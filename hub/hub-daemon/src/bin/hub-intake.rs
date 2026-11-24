// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! `hub-intake`: the chapter's inbound carrier (`hub/docs/PRD_CHAPTER_PRODUCT.md`).
//!
//! The chapter keeps its address and its mail program. A copy of what arrives there (a forward,
//! or a mailbox the chapter shares) lands in a mailbox this carrier reads. Each pass:
//! 1. asks the IMAP server, through `curl`, for messages newer than the last one handed over;
//! 2. reads each one: sender, subject, Message-ID, date and the plain text;
//! 3. hands it to `POST /admin/api/chapter/intake` on the hub's operator plane, which opens a job
//!    for the committee that answers the chapter's address.
//!
//! The hub never sees the mailbox login. The hub dedups by Message-ID, so a pass that dies
//! half-way and runs again opens nothing twice. Auto-replies and messages from the hub's own
//! sending address are skipped, so a nudge bounced back can't become a job.
//!
//! Usage: `hub-intake --config intake.json [--dry-run] [--every SECS]`.

use std::path::{Path, PathBuf};
use std::process::Stdio;

use anyhow::{bail, Context, Result};
use chrono::{DateTime, Utc};
use clap::Parser;
use serde::{Deserialize, Serialize};

#[derive(Parser)]
#[command(name = "hub-intake", about = "Hand new mail in the chapter's inbox to the hub as requests")]
struct Args {
    #[arg(long)]
    config: PathBuf,
    /// Print what would be handed over; change nothing.
    #[arg(long)]
    dry_run: bool,
    /// Run a pass every SECS seconds instead of once.
    #[arg(long)]
    every: Option<u64>,
}

#[derive(Clone, Debug, Deserialize)]
struct Config {
    /// The hub's operator plane, e.g. `http://127.0.0.1:8782`.
    hub_admin_url: String,
    /// The mailbox, e.g. `imaps://imap.gmail.com:993/INBOX`.
    imap_url: String,
    /// A 0600 netrc file with the mailbox login, passed to curl so it is never on a command line.
    netrc_file: PathBuf,
    #[serde(default = "default_curl")]
    curl: PathBuf,
    /// Where the carrier remembers the last message it handed over.
    state_file: PathBuf,
    /// Addresses whose mail is never a request: the hub's own sender, at least.
    #[serde(default)]
    ignore_from: Vec<String>,
    /// On the very first pass, how many days back to pick up. Later passes take only new mail.
    #[serde(default = "default_backfill")]
    backfill_days: i64,
}

fn default_curl() -> PathBuf {
    PathBuf::from("curl")
}

fn default_backfill() -> i64 {
    1
}

#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
struct CarrierState {
    last_uid: Option<u64>,
}

impl CarrierState {
    fn load(path: &Path) -> Result<Self> {
        match std::fs::read(path) {
            Ok(b) => serde_json::from_slice(&b).context("reading the intake state file"),
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(Self::default()),
            Err(e) => Err(e.into()),
        }
    }

    fn save(&self, path: &Path) -> Result<()> {
        let tmp = path.with_extension("tmp");
        std::fs::write(&tmp, serde_json::to_vec_pretty(self)?)?;
        std::fs::rename(&tmp, path)?;
        Ok(())
    }
}

// ---------------------------------------------------------------------------------------------
// Reading one message (RFC 5322 + the MIME needed for ordinary mail)
// ---------------------------------------------------------------------------------------------

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
struct Parsed {
    message_id: String,
    from_name: String,
    from_address: String,
    subject: String,
    text: String,
    received_at: Option<DateTime<Utc>>,
    auto: bool,
}

fn split_head(raw: &str) -> (&str, &str) {
    for sep in ["\r\n\r\n", "\n\n"] {
        if let Some(i) = raw.find(sep) {
            return (&raw[..i], &raw[i + sep.len()..]);
        }
    }
    (raw, "")
}

/// Headers, unfolded, names lowercased, in order.
fn headers(head: &str) -> Vec<(String, String)> {
    let mut out: Vec<(String, String)> = Vec::new();
    for line in head.lines() {
        let line = line.trim_end_matches('\r');
        if line.starts_with(' ') || line.starts_with('\t') {
            if let Some(last) = out.last_mut() {
                last.1.push(' ');
                last.1.push_str(line.trim());
            }
        } else if let Some((k, v)) = line.split_once(':') {
            out.push((k.trim().to_ascii_lowercase(), v.trim().to_string()));
        }
    }
    out
}

fn header<'a>(h: &'a [(String, String)], name: &str) -> Option<&'a str> {
    h.iter().find(|(k, _)| k == name).map(|(_, v)| v.as_str())
}

fn b64_decode(s: &str) -> Vec<u8> {
    let val = |c: u8| -> Option<u32> {
        match c {
            b'A'..=b'Z' => Some(u32::from(c - b'A')),
            b'a'..=b'z' => Some(u32::from(c - b'a') + 26),
            b'0'..=b'9' => Some(u32::from(c - b'0') + 52),
            b'+' | b'-' => Some(62),
            b'/' | b'_' => Some(63),
            _ => None,
        }
    };
    let mut out = Vec::new();
    let (mut acc, mut bits) = (0u32, 0u32);
    for c in s.bytes() {
        if c == b'=' {
            break;
        }
        let Some(v) = val(c) else { continue };
        acc = (acc << 6) | v;
        bits += 6;
        if bits >= 8 {
            bits -= 8;
            out.push((acc >> bits) as u8);
            acc &= (1 << bits) - 1;
        }
    }
    out
}

fn qp_decode(s: &str, underscore_is_space: bool) -> Vec<u8> {
    let b = s.as_bytes();
    let mut out = Vec::with_capacity(b.len());
    let mut i = 0;
    while i < b.len() {
        match b[i] {
            b'=' => {
                let hex = |c: u8| (c as char).to_digit(16);
                if i + 1 < b.len() && (b[i + 1] == b'\n' || b[i + 1] == b'\r') {
                    // Soft line break.
                    i += 1;
                    if b[i] == b'\r' && i + 1 < b.len() && b[i + 1] == b'\n' {
                        i += 1;
                    }
                    i += 1;
                    continue;
                }
                match (b.get(i + 1).and_then(|c| hex(*c)), b.get(i + 2).and_then(|c| hex(*c))) {
                    (Some(h), Some(l)) => {
                        out.push((h * 16 + l) as u8);
                        i += 3;
                    }
                    _ => {
                        out.push(b'=');
                        i += 1;
                    }
                }
            }
            b'_' if underscore_is_space => {
                out.push(b' ');
                i += 1;
            }
            c => {
                out.push(c);
                i += 1;
            }
        }
    }
    out
}

/// Bytes to text in the named charset: UTF-8, or Latin-1 / Windows-1252 byte for byte.
fn to_text(bytes: &[u8], charset: &str) -> String {
    let cs = charset.to_ascii_lowercase();
    if cs.contains("8859-1") || cs.contains("1252") || cs.contains("latin") {
        bytes.iter().map(|b| *b as char).collect()
    } else {
        String::from_utf8_lossy(bytes).into_owned()
    }
}

/// Decode RFC 2047 encoded words (`=?utf-8?B?...?=`), as subjects and names carry them.
fn decode_words(s: &str) -> String {
    let mut out = String::new();
    let mut rest = s;
    let mut last_was_word = false;
    while let Some(start) = rest.find("=?") {
        let before = &rest[..start];
        if !(last_was_word && before.trim().is_empty()) {
            out.push_str(before);
        }
        let after = &rest[start + 2..];
        let parts: Vec<&str> = after.splitn(3, '?').collect();
        if parts.len() == 3 {
            if let Some(end) = parts[2].find("?=") {
                let (charset, enc, text) = (parts[0], parts[1], &parts[2][..end]);
                let bytes = if enc.eq_ignore_ascii_case("b") { b64_decode(text) } else { qp_decode(text, true) };
                out.push_str(&to_text(&bytes, charset));
                let consumed = start + 2 + parts[0].len() + 1 + parts[1].len() + 1 + end + 2;
                rest = &rest[consumed..];
                last_was_word = true;
                continue;
            }
        }
        out.push_str("=?");
        rest = after;
        last_was_word = false;
    }
    out.push_str(rest);
    out
}

/// `Name <addr>` or a bare address.
fn parse_from(v: &str) -> (String, String) {
    let v = decode_words(v);
    if let (Some(a), Some(b)) = (v.rfind('<'), v.rfind('>')) {
        if a < b {
            let name = v[..a].trim().trim_matches('"').trim().to_string();
            return (name, v[a + 1..b].trim().to_string());
        }
    }
    (String::new(), v.trim().to_string())
}

fn param(value: &str, name: &str) -> Option<String> {
    value.split(';').skip(1).find_map(|p| {
        let (k, v) = p.split_once('=')?;
        (k.trim().eq_ignore_ascii_case(name)).then(|| v.trim().trim_matches('"').to_string())
    })
}

fn strip_html(s: &str) -> String {
    let mut out = String::new();
    let mut in_tag = false;
    for c in s.chars() {
        match c {
            '<' => in_tag = true,
            '>' => {
                in_tag = false;
                out.push(' ');
            }
            _ if !in_tag => out.push(c),
            _ => {}
        }
    }
    let out = out.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">");
    out.split_whitespace().collect::<Vec<_>>().join(" ")
}

/// The readable text of a part: text/plain preferred, text/html stripped as a fallback.
fn body_text(h: &[(String, String)], body: &str, depth: u8) -> Option<(bool, String)> {
    let ctype = header(h, "content-type").unwrap_or("text/plain");
    let lower = ctype.to_ascii_lowercase();
    if lower.starts_with("multipart/") && depth < 4 {
        let boundary = param(ctype, "boundary")?;
        let marker = format!("--{boundary}");
        let mut html: Option<String> = None;
        for part in body.split(&marker).skip(1) {
            if part.starts_with("--") {
                break;
            }
            let part = part.trim_start_matches(['\r', '\n']);
            let (ph, pb) = split_head(part);
            let ph = headers(ph);
            if let Some((is_plain, t)) = body_text(&ph, pb, depth + 1) {
                if is_plain {
                    return Some((true, t));
                }
                html.get_or_insert(t);
            }
        }
        return html.map(|t| (false, t));
    }
    if !(lower.starts_with("text/plain") || lower.starts_with("text/html")) {
        return None;
    }
    let charset = param(ctype, "charset").unwrap_or_else(|| "utf-8".into());
    let cte = header(h, "content-transfer-encoding").unwrap_or("7bit").to_ascii_lowercase();
    let bytes = match cte.as_str() {
        "base64" => b64_decode(body),
        "quoted-printable" => qp_decode(body, false),
        _ => body.as_bytes().to_vec(),
    };
    let text = to_text(&bytes, &charset);
    if lower.starts_with("text/html") {
        Some((false, strip_html(&text)))
    } else {
        Some((true, text.replace("\r\n", "\n")))
    }
}

fn parse_message(raw: &str) -> Option<Parsed> {
    let (head, body) = split_head(raw);
    let h = headers(head);
    let (from_name, from_address) = parse_from(header(&h, "from")?);
    let message_id = header(&h, "message-id").map(str::to_string)
        .unwrap_or_else(|| {
            use std::hash::{Hash, Hasher};
            let mut s = std::collections::hash_map::DefaultHasher::new();
            raw.hash(&mut s);
            format!("<no-id-{:x}@hub-intake>", s.finish())
        });
    let auto = header(&h, "auto-submitted").is_some_and(|v| !v.eq_ignore_ascii_case("no"))
        || header(&h, "x-autoreply").is_some()
        || header(&h, "precedence").is_some_and(|v| v.eq_ignore_ascii_case("auto_reply"));
    Some(Parsed {
        message_id,
        from_name,
        from_address,
        subject: decode_words(header(&h, "subject").unwrap_or("")),
        text: body_text(&h, body, 0).map(|(_, t)| t).unwrap_or_default().trim().to_string(),
        received_at: header(&h, "date").and_then(|d| DateTime::parse_from_rfc2822(d).ok()).map(|d| d.with_timezone(&Utc)),
        auto,
    })
}

/// UIDs from an IMAP `* SEARCH 4 7 9` line.
fn parse_search(out: &str) -> Vec<u64> {
    out.lines().filter_map(|l| l.trim().strip_prefix("* SEARCH"))
        .flat_map(|rest| rest.split_whitespace().filter_map(|n| n.parse().ok()).collect::<Vec<u64>>())
        .collect()
}

// ---------------------------------------------------------------------------------------------
// The pass
// ---------------------------------------------------------------------------------------------

async fn curl(cfg: &Config, url: &str, request: Option<&str>) -> Result<String> {
    let mut cmd = tokio::process::Command::new(&cfg.curl);
    cmd.arg("--silent").arg("--show-error").arg("--fail").arg("--max-time").arg("60")
        .arg("--netrc-file").arg(&cfg.netrc_file).arg("--url").arg(url);
    if let Some(r) = request {
        cmd.arg("--request").arg(r);
    }
    let out = cmd.stdin(Stdio::null()).output().await.context("running curl")?;
    if !out.status.success() {
        bail!("curl failed: {}", String::from_utf8_lossy(&out.stderr).trim());
    }
    Ok(String::from_utf8_lossy(&out.stdout).into_owned())
}

fn imap_date(t: DateTime<Utc>) -> String {
    t.format("%d-%b-%Y").to_string()
}

async fn hand_over(cfg: &Config, p: &Parsed) -> Result<serde_json::Value> {
    let url = format!("{}/admin/api/chapter/intake", cfg.hub_admin_url.trim_end_matches('/'));
    let resp = reqwest::Client::new().post(&url).json(&serde_json::json!({
        "message_id": p.message_id, "from_name": p.from_name, "from_address": p.from_address,
        "subject": p.subject, "text": p.text, "received_at": p.received_at,
    })).send().await.context("reaching the hub")?;
    let status = resp.status();
    let body: serde_json::Value = resp.json().await.unwrap_or(serde_json::Value::Null);
    if !status.is_success() {
        bail!("the hub refused it ({status}): {}", body["error"].as_str().or(body["message"].as_str()).unwrap_or(""));
    }
    Ok(body)
}

async fn pass(cfg: &Config, state: &mut CarrierState, dry_run: bool) -> Result<usize> {
    let search = match state.last_uid {
        Some(last) => format!("UID SEARCH UID {}:*", last + 1),
        None => format!("UID SEARCH SINCE {}", imap_date(Utc::now() - chrono::Duration::days(cfg.backfill_days))),
    };
    let mut uids: Vec<u64> = parse_search(&curl(cfg, &cfg.imap_url, Some(&search)).await?);
    // `n:*` always returns the highest UID, even when it is not newer.
    uids.retain(|u| state.last_uid.map_or(true, |last| *u > last));
    uids.sort_unstable();
    let mut handed = 0;
    for uid in uids {
        let raw = curl(cfg, &format!("{};UID={uid}", cfg.imap_url.trim_end_matches('/')), None).await?;
        match parse_message(&raw) {
            None => tracing::warn!(uid, "unreadable message skipped"),
            Some(p) if p.auto => tracing::info!(uid, "auto-reply skipped"),
            Some(p) if cfg.ignore_from.iter().any(|a| a.eq_ignore_ascii_case(&p.from_address)) => {
                tracing::info!(uid, "message from an ignored sender skipped")
            }
            Some(p) if dry_run => println!("would hand over uid {uid}: \"{}\" from {}", p.subject, p.from_address),
            Some(p) => {
                // A refusal stops the pass here, so this message is retried next time.
                let v = hand_over(cfg, &p).await.with_context(|| format!("message uid {uid}"))?;
                tracing::info!(uid, duplicate = v["duplicate"].as_bool().unwrap_or(false), "handed over");
                handed += 1;
            }
        }
        if !dry_run {
            state.last_uid = Some(uid);
        }
    }
    Ok(handed)
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt().with_target(false).init();
    let args = Args::parse();
    let cfg: Config = serde_json::from_slice(&std::fs::read(&args.config).context("reading the config")?)
        .context("parsing the config")?;
    loop {
        let mut state = CarrierState::load(&cfg.state_file)?;
        let before = state.clone();
        let r = pass(&cfg, &mut state, args.dry_run).await;
        if state != before {
            state.save(&cfg.state_file)?;
        }
        match (&r, args.every) {
            (Ok(n), _) => tracing::info!(handed = n, "pass done"),
            (Err(e), Some(_)) => tracing::warn!("pass failed: {e:#}"),
            (Err(_), None) => {}
        }
        let Some(secs) = args.every else { return r.map(|_| ()) };
        tokio::time::sleep(std::time::Duration::from_secs(secs)).await;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn reads_a_plain_message() {
        let raw = "From: \"Venue Person\" <venue@example.org>\r\nSubject: Hosting your\r\n January event?\r\n\
                   Message-ID: <abc@example.org>\r\nDate: Mon, 23 Nov 2026 10:00:00 -0800\r\n\r\nWe'd love to host.\r\n";
        let p = parse_message(raw).unwrap();
        assert_eq!(p.from_name, "Venue Person");
        assert_eq!(p.from_address, "venue@example.org");
        assert_eq!(p.subject, "Hosting your January event?");
        assert_eq!(p.message_id, "<abc@example.org>");
        assert_eq!(p.text, "We'd love to host.");
        assert_eq!(p.received_at.unwrap().to_rfc3339(), "2026-11-23T18:00:00+00:00");
        assert!(!p.auto);
    }

    #[test]
    fn reads_encoded_words_and_multipart_alternative() {
        let raw = "From: =?utf-8?B?SsO8cmdlbg==?= <j@example.org>\nSubject: =?utf-8?Q?Caf=C3=A9_night?=\n\
                   Content-Type: multipart/alternative; boundary=\"xyz\"\n\n--xyz\nContent-Type: text/plain; charset=utf-8\n\
                   Content-Transfer-Encoding: quoted-printable\n\nSee you at the caf=C3=A9 =\nsoon.\n--xyz\n\
                   Content-Type: text/html\n\n<p>See you</p>\n--xyz--\n";
        let p = parse_message(raw).unwrap();
        assert_eq!(p.from_name, "Jürgen");
        assert_eq!(p.subject, "Café night");
        assert_eq!(p.text, "See you at the café soon.");
    }

    #[test]
    fn html_only_mail_is_stripped_and_base64_decoded() {
        let raw = "From: a@example.org\nSubject: hi\nContent-Type: text/html; charset=utf-8\n\
                   Content-Transfer-Encoding: base64\n\nPHA+SGVsbG8gPGI+dGhlcmU8L2I+PC9wPg==\n";
        let p = parse_message(raw).unwrap();
        assert_eq!(p.text, "Hello there");
        assert_eq!(p.from_address, "a@example.org");
    }

    #[test]
    fn auto_replies_are_marked() {
        let raw = "From: a@example.org\nSubject: Out of office\nAuto-Submitted: auto-replied\n\nAway.\n";
        assert!(parse_message(raw).unwrap().auto);
    }

    #[test]
    fn search_lines_parse() {
        assert_eq!(parse_search("* SEARCH 4 7 9\r\n"), vec![4, 7, 9]);
        assert!(parse_search("* SEARCH\r\n").is_empty());
    }
}
