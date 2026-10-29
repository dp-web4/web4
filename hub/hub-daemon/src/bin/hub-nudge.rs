// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! `hub-nudge`: the commitments carrier, slice K3b (hub/docs/PRD_COMMITMENTS.md §6).
//!
//! The hub records; this delivers (C4). Each pass:
//! 1. reads `GET /admin/api/commitments/nudges` on the hub's operator plane;
//! 2. sends every row the hub marked sendable (`held: null`) by email, through `curl`'s SMTP
//!    client and the operator's own mail server;
//! 3. reports each attempt, sent or failed, with `POST .../nudges/delivered`, so no failure is silent.
//!
//! The hub decides what is owed, the per-party cap and the wording. This process holds the mail
//! server settings, which the hub never sees.
//!
//! **A locked hub is loud.** The sweep runs only while the hub is unlocked, so a hub that restarts
//! and waits for its passphrase stops escalating with no sign to anyone (PRD §9.1). When the hub
//! has answered 503 (locked), or not at all, for `locked_alert_hours`, this emails the operator,
//! and only the operator, once a day until it is back.
//!
//! Usage: `hub-nudge --config nudge.json [--dry-run] [--every SECS]`. With no `--every` it runs
//! one pass and exits (for a systemd timer or cron).

use std::path::{Path, PathBuf};
use std::process::Stdio;

use anyhow::{bail, Context, Result};
use chrono::{DateTime, Utc};
use clap::Parser;
use serde::{Deserialize, Serialize};
use tokio::io::AsyncWriteExt;

#[derive(Parser)]
#[command(name = "hub-nudge", about = "Deliver the hub's commitment nudges by email and report each attempt")]
struct Args {
    /// The carrier's JSON config (see `Config`).
    #[arg(long)]
    config: PathBuf,
    /// Print what would be sent; send nothing, report nothing.
    #[arg(long)]
    dry_run: bool,
    /// Run a pass every SECS seconds instead of once.
    #[arg(long)]
    every: Option<u64>,
}

/// The carrier's own settings. The hub never sees them.
#[derive(Clone, Debug, Deserialize)]
struct Config {
    /// The hub's operator plane, e.g. `http://127.0.0.1:8772`. Loopback only: the routes refuse
    /// anything else.
    hub_admin_url: String,
    /// e.g. `smtps://smtp.example.org:465`.
    smtp_url: String,
    /// The envelope and header sender.
    from: String,
    /// Who hears when the hub is locked or down.
    operator_address: String,
    /// A 0600 netrc file with the mail server login, passed to curl as `--netrc-file`, so it
    /// never appears on a command line. Omit it for a server that needs no login.
    #[serde(default)]
    netrc_file: Option<PathBuf>,
    #[serde(default = "default_curl")]
    curl: PathBuf,
    #[serde(default = "default_alert_hours")]
    locked_alert_hours: u32,
    /// Where the carrier remembers how long the hub has been locked.
    state_file: PathBuf,
}

fn default_curl() -> PathBuf {
    PathBuf::from("curl")
}

fn default_alert_hours() -> u32 {
    6
}

/// One row of `GET /admin/api/commitments/nudges`.
#[derive(Clone, Debug, Deserialize)]
struct Nudge {
    commitment_id: String,
    about_index: u64,
    party: Party,
    address: Option<String>,
    held: Option<String>,
    subject: String,
    body: String,
}

#[derive(Clone, Debug, Deserialize)]
struct Party {
    party_id: String,
}

#[derive(Debug)]
enum HubAnswer {
    Nudges(Vec<Nudge>),
    /// 503: the vault is locked and the sweep is not running.
    Locked,
    /// 404: the hub answers but has no nudges route, i.e. it runs a build from before K3a.
    NoRoute,
    /// No answer, or an answer that is not a listing.
    Down(String),
}

/// One send attempt as the hub records it. Kept in [`CarrierState`] when its report could not be
/// delivered, so the hub's ledger, which the per-party cap is counted from, still learns of it.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
struct Attempt {
    commitment_id: String,
    about_index: u64,
    party_id: String,
    ok: bool,
}

impl Attempt {
    fn of(n: &Nudge, ok: bool) -> Self {
        Self { commitment_id: n.commitment_id.clone(), about_index: n.about_index, party_id: n.party.party_id.clone(), ok }
    }
}

#[derive(Debug, PartialEq, Eq)]
enum Report {
    Recorded,
    /// The hub refused the report (4xx). The send happened; log it and move on, never retry: a
    /// lead unseated between the send and the report is refused for a send that was real.
    Refused(String),
}

#[async_trait::async_trait]
trait Hub {
    async fn nudges(&self) -> HubAnswer;
    async fn report(&self, a: &Attempt) -> Result<Report>;
}

#[async_trait::async_trait]
trait Mailer {
    async fn send(&self, to: &str, subject: &str, body: &str) -> Result<()>;
}

struct HttpHub {
    base: String,
    http: reqwest::Client,
}

#[async_trait::async_trait]
impl Hub for HttpHub {
    async fn nudges(&self) -> HubAnswer {
        let url = format!("{}/admin/api/commitments/nudges", self.base.trim_end_matches('/'));
        let resp = match self.http.get(&url).send().await {
            Ok(r) => r,
            Err(e) => return HubAnswer::Down(e.to_string()),
        };
        if resp.status() == reqwest::StatusCode::SERVICE_UNAVAILABLE {
            return HubAnswer::Locked;
        }
        if resp.status() == reqwest::StatusCode::NOT_FOUND {
            return HubAnswer::NoRoute;
        }
        if !resp.status().is_success() {
            return HubAnswer::Down(format!("{url} answered {}", resp.status()));
        }
        #[derive(Deserialize)]
        struct Listing {
            nudges: Vec<Nudge>,
        }
        match resp.json::<Listing>().await {
            Ok(l) => HubAnswer::Nudges(l.nudges),
            Err(e) => HubAnswer::Down(format!("{url}: unreadable listing: {e}")),
        }
    }

    async fn report(&self, a: &Attempt) -> Result<Report> {
        let url = format!("{}/admin/api/commitments/nudges/delivered", self.base.trim_end_matches('/'));
        let resp = self.http.post(&url).json(&serde_json::json!({
            "commitment_id": a.commitment_id,
            "about_index": a.about_index,
            "party_id": a.party_id,
            "channel": "email",
            "ok": a.ok,
        })).send().await.with_context(|| format!("POST {url}"))?;
        let status = resp.status();
        if status.is_success() {
            Ok(Report::Recorded)
        } else if status.is_client_error() {
            Ok(Report::Refused(format!("{status}: {}", resp.text().await.unwrap_or_default())))
        } else {
            bail!("POST {url} answered {status}")
        }
    }
}

/// Sends through `curl`'s SMTP client: no mail library in the hub's tree, and the login stays in
/// a netrc file rather than on argv.
struct CurlMailer {
    cfg: Config,
}

#[async_trait::async_trait]
impl Mailer for CurlMailer {
    async fn send(&self, to: &str, subject: &str, body: &str) -> Result<()> {
        let message = render_message(&self.cfg.from, to, subject, body, Utc::now());
        let mut cmd = tokio::process::Command::new(&self.cfg.curl);
        cmd.args(["--silent", "--show-error", "--ssl-reqd", "--url", &self.cfg.smtp_url,
                  "--mail-from", &self.cfg.from, "--mail-rcpt", to, "--upload-file", "-"]);
        if let Some(netrc) = &self.cfg.netrc_file {
            cmd.arg("--netrc-file").arg(netrc);
        }
        let mut child = cmd.stdin(Stdio::piped()).stdout(Stdio::null()).stderr(Stdio::piped())
            .spawn().with_context(|| format!("starting {}", self.cfg.curl.display()))?;
        child.stdin.take().expect("piped").write_all(message.as_bytes()).await?;
        let out = child.wait_with_output().await?;
        if !out.status.success() {
            bail!("curl exited {}: {}", out.status, String::from_utf8_lossy(&out.stderr).trim());
        }
        Ok(())
    }
}

/// A header value can never carry a line break: the hub already refuses control characters in a
/// title, and this drops any that reach here anyway, so no field can add a header.
fn header_safe(v: &str) -> String {
    v.chars().filter(|c| !c.is_control()).collect()
}

/// RFC 2047 for a subject that is not plain ASCII.
fn encode_subject(subject: &str) -> String {
    let s = header_safe(subject);
    if s.is_ascii() {
        s
    } else {
        format!("=?UTF-8?B?{}?=", base64(s.as_bytes()))
    }
}

fn base64(bytes: &[u8]) -> String {
    const T: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut out = String::with_capacity((bytes.len() + 2) / 3 * 4);
    for chunk in bytes.chunks(3) {
        let n = match chunk.len() {
            3 => (u32::from(chunk[0]) << 16) | (u32::from(chunk[1]) << 8) | u32::from(chunk[2]),
            2 => (u32::from(chunk[0]) << 16) | (u32::from(chunk[1]) << 8),
            _ => u32::from(chunk[0]) << 16,
        };
        for i in 0..4 {
            if i <= chunk.len() {
                out.push(T[((n >> (18 - 6 * i)) & 63) as usize] as char);
            } else {
                out.push('=');
            }
        }
    }
    out
}

fn render_message(from: &str, to: &str, subject: &str, body: &str, now: DateTime<Utc>) -> String {
    format!(
        "From: {}\r\nTo: {}\r\nSubject: {}\r\nDate: {}\r\nMIME-Version: 1.0\r\n\
         Content-Type: text/plain; charset=utf-8\r\nContent-Transfer-Encoding: 8bit\r\n\r\n{}\r\n",
        header_safe(from), header_safe(to), encode_subject(subject), now.to_rfc2822(),
        body.replace("\r\n", "\n").replace('\n', "\r\n"),
    )
}

/// What the carrier remembers between passes: only how long the hub has been unreachable.
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
struct CarrierState {
    #[serde(default)]
    unreachable_since: Option<DateTime<Utc>>,
    #[serde(default)]
    last_alert_at: Option<DateTime<Utc>>,
    /// Attempts whose report did not reach the hub. Re-reported before anything new is sent: an
    /// unrecorded send is invisible to the cap, so sending on past one could repeat it each pass.
    #[serde(default)]
    unreported: Vec<Attempt>,
}

impl CarrierState {
    fn load(path: &Path) -> Result<Self> {
        match std::fs::read(path) {
            Ok(b) => serde_json::from_slice(&b).with_context(|| format!("parsing {}", path.display())),
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(Self::default()),
            Err(e) => Err(e).with_context(|| format!("reading {}", path.display())),
        }
    }

    fn save(&self, path: &Path) -> Result<()> {
        let tmp = path.with_extension("tmp");
        std::fs::write(&tmp, serde_json::to_vec_pretty(self)?)?;
        std::fs::rename(&tmp, path).with_context(|| format!("writing {}", path.display()))
    }
}

/// What one pass did.
#[derive(Debug, Default, PartialEq, Eq)]
struct PassReport {
    sent: u32,
    failed: u32,
    held: u32,
    report_refused: u32,
    /// Attempts left in the state file because their report could not be delivered.
    unreported: u32,
    alerted: bool,
}

/// Report one attempt. `Ok(true)` when the hub has answered (recorded or refused); `Ok(false)`
/// when the report did not get through and must be kept.
async fn deliver_report(hub: &dyn Hub, a: &Attempt, r: &mut PassReport) -> bool {
    match hub.report(a).await {
        Ok(Report::Recorded) => true,
        Ok(Report::Refused(m)) => {
            tracing::warn!("hub refused the report for {} entry {}: {m}", a.commitment_id, a.about_index);
            r.report_refused += 1;
            true
        }
        Err(e) => {
            tracing::warn!("report for {} entry {} did not reach the hub: {e:#}", a.commitment_id, a.about_index);
            false
        }
    }
}

/// One pass. `state` is updated in place; the caller saves it.
async fn pass(
    hub: &dyn Hub, mail: &dyn Mailer, operator: &str, alert_after: chrono::Duration,
    state: &mut CarrierState, now: DateTime<Utc>, dry_run: bool,
) -> Result<PassReport> {
    let mut r = PassReport::default();
    let why = match hub.nudges().await {
        HubAnswer::Nudges(rows) => {
            state.unreachable_since = None;
            state.last_alert_at = None;
            // Old reports first. If any still cannot get through, send nothing new.
            let pending = std::mem::take(&mut state.unreported);
            for a in pending {
                if dry_run || !deliver_report(hub, &a, &mut r).await {
                    state.unreported.push(a);
                }
            }
            if !state.unreported.is_empty() {
                r.unreported = state.unreported.len() as u32;
                return Ok(r);
            }
            for n in rows {
                let (None, Some(address)) = (&n.held, &n.address) else {
                    r.held += 1;
                    continue;
                };
                if dry_run {
                    println!("would send to {address}: {} | {}", n.subject, n.body);
                    continue;
                }
                let ok = match mail.send(address, &n.subject, &n.body).await {
                    Ok(()) => { r.sent += 1; true }
                    Err(e) => {
                        tracing::warn!("send for {} entry {} failed: {e:#}", n.commitment_id, n.about_index);
                        r.failed += 1;
                        false
                    }
                };
                let a = Attempt::of(&n, ok);
                if !deliver_report(hub, &a, &mut r).await {
                    // Stop here: the next pass re-reports this before it sends anything else.
                    state.unreported.push(a);
                    r.unreported = 1;
                    return Ok(r);
                }
            }
            return Ok(r);
        }
        HubAnswer::Locked => "is locked: it answers 503, so silence is not escalating and nobody is being nudged".to_string(),
        HubAnswer::NoRoute => "answers, but has no commitments nudge route (it may be running a build from before \
            K3a), so nobody is being nudged".to_string(),
        HubAnswer::Down(e) => format!("is not answering ({e}), so nobody is being nudged"),
    };
    let since = *state.unreachable_since.get_or_insert(now);
    let due = now - since >= alert_after
        && state.last_alert_at.map_or(true, |t| now - t >= chrono::Duration::hours(24));
    if due {
        let subject = "Your hub needs you: commitments are not moving";
        let body = format!(
            "Your hub {why}. That has been so since {}.\n\nOnce it is unlocked, the next sweep \
             catches up on every step it missed, in order.",
            since.to_rfc2822());
        if dry_run {
            println!("would alert {operator}: {body}");
        } else {
            mail.send(operator, subject, &body).await.context("alerting the operator")?;
            state.last_alert_at = Some(now);
            r.alerted = true;
        }
    }
    Ok(r)
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt().with_env_filter(
        tracing_subscriber::EnvFilter::try_from_default_env().unwrap_or_else(|_| "info".into())).init();
    let args = Args::parse();
    let cfg: Config = serde_json::from_slice(&std::fs::read(&args.config)
        .with_context(|| format!("reading {}", args.config.display()))?)
        .with_context(|| format!("parsing {}", args.config.display()))?;
    let hub = HttpHub {
        base: cfg.hub_admin_url.clone(),
        http: reqwest::Client::builder().timeout(std::time::Duration::from_secs(30)).build()?,
    };
    let mail = CurlMailer { cfg: cfg.clone() };
    let alert_after = chrono::Duration::hours(i64::from(cfg.locked_alert_hours));
    loop {
        let mut state = CarrierState::load(&cfg.state_file)?;
        match pass(&hub, &mail, &cfg.operator_address, alert_after, &mut state, Utc::now(), args.dry_run).await {
            Ok(r) => tracing::info!(?r, "nudge pass"),
            Err(e) => tracing::warn!("nudge pass failed: {e:#}"),
        }
        if !args.dry_run {
            state.save(&cfg.state_file)?;
        }
        match args.every {
            Some(secs) => tokio::time::sleep(std::time::Duration::from_secs(secs)).await,
            None => return Ok(()),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Mutex;

    struct FakeHub {
        answer: Mutex<Option<HubAnswer>>,
        reports: Mutex<Vec<(String, bool)>>,
        refuse: bool,
        broken: std::sync::atomic::AtomicBool,
    }

    impl FakeHub {
        fn new(answer: HubAnswer) -> Self {
            Self { answer: Mutex::new(Some(answer)), reports: Mutex::new(Vec::new()), refuse: false,
                broken: std::sync::atomic::AtomicBool::new(false) }
        }
    }

    #[async_trait::async_trait]
    impl Hub for FakeHub {
        async fn nudges(&self) -> HubAnswer {
            self.answer.lock().unwrap().take().unwrap_or(HubAnswer::Nudges(Vec::new()))
        }
        async fn report(&self, a: &Attempt) -> Result<Report> {
            if self.broken.load(std::sync::atomic::Ordering::SeqCst) {
                bail!("POST answered 502 Bad Gateway");
            }
            self.reports.lock().unwrap().push((a.party_id.clone(), a.ok));
            Ok(if self.refuse { Report::Refused("400".into()) } else { Report::Recorded })
        }
    }

    #[derive(Default)]
    struct FakeMail {
        sent: Mutex<Vec<(String, String)>>,
        fail_to: Option<String>,
    }

    #[async_trait::async_trait]
    impl Mailer for FakeMail {
        async fn send(&self, to: &str, subject: &str, _body: &str) -> Result<()> {
            if self.fail_to.as_deref() == Some(to) {
                bail!("550 no such mailbox");
            }
            self.sent.lock().unwrap().push((to.into(), subject.into()));
            Ok(())
        }
    }

    fn nudge(party: &str, address: Option<&str>, held: Option<&str>) -> Nudge {
        Nudge {
            commitment_id: "c".into(), about_index: 7, party: Party { party_id: party.into() },
            address: address.map(Into::into), held: held.map(Into::into),
            subject: "Venue AV: you're the backup".into(), body: "Alex owns Venue AV.".into(),
        }
    }

    fn at(h: i64) -> DateTime<Utc> {
        DateTime::UNIX_EPOCH + chrono::Duration::hours(h)
    }

    async fn run(hub: &FakeHub, mail: &FakeMail, state: &mut CarrierState, h: i64) -> PassReport {
        pass(hub, mail, "op@example.org", chrono::Duration::hours(6), state, at(h), false).await.unwrap()
    }

    #[tokio::test]
    async fn sends_only_what_the_hub_marked_sendable_and_reports_every_attempt() {
        let hub = FakeHub::new(HubAnswer::Nudges(vec![
            nudge("sam", Some("sam@example.org"), None),
            nudge("kim", Some("kim@example.org"), None),
            nudge("lee", None, Some("no_address")),
            nudge("alex", Some("alex@example.org"), Some("capped")),
        ]));
        let mail = FakeMail { fail_to: Some("kim@example.org".into()), ..Default::default() };
        let mut state = CarrierState::default();
        let r = run(&hub, &mail, &mut state, 0).await;
        assert_eq!(r, PassReport { sent: 1, failed: 1, held: 2, report_refused: 0, unreported: 0, alerted: false });
        assert_eq!(*mail.sent.lock().unwrap(), vec![("sam@example.org".to_string(), "Venue AV: you're the backup".to_string())]);
        assert_eq!(*hub.reports.lock().unwrap(), vec![("sam".to_string(), true), ("kim".to_string(), false)],
            "a failed send is reported too, never silent");
    }

    #[tokio::test]
    async fn a_refused_report_is_logged_not_retried() {
        let mut hub = FakeHub::new(HubAnswer::Nudges(vec![nudge("sam", Some("sam@example.org"), None)]));
        hub.refuse = true;
        let mail = FakeMail::default();
        let r = run(&hub, &mail, &mut CarrierState::default(), 0).await;
        assert_eq!((r.sent, r.report_refused), (1, 1));
        assert_eq!(hub.reports.lock().unwrap().len(), 1);
    }

    #[tokio::test]
    async fn a_locked_hub_alerts_the_operator_only_after_the_window_and_then_daily() {
        let mail = FakeMail::default();
        let mut state = CarrierState::default();
        assert!(!run(&FakeHub::new(HubAnswer::Locked), &mail, &mut state, 0).await.alerted);
        assert!(!run(&FakeHub::new(HubAnswer::Locked), &mail, &mut state, 5).await.alerted, "inside the window");
        assert!(run(&FakeHub::new(HubAnswer::Locked), &mail, &mut state, 6).await.alerted);
        assert!(!run(&FakeHub::new(HubAnswer::Down("refused".into())), &mail, &mut state, 7).await.alerted,
            "once a day, not once a pass");
        assert!(run(&FakeHub::new(HubAnswer::Locked), &mail, &mut state, 30).await.alerted);
        let sent = mail.sent.lock().unwrap().clone();
        assert_eq!(sent.len(), 2);
        assert!(sent.iter().all(|(to, _)| to == "op@example.org"), "only the operator hears about a lock");

        // Back up: the clock resets, so the next lock waits out a fresh window.
        run(&FakeHub::new(HubAnswer::Nudges(Vec::new())), &mail, &mut state, 31).await;
        assert_eq!(state, CarrierState::default());
        assert!(!run(&FakeHub::new(HubAnswer::Locked), &mail, &mut state, 32).await.alerted);
    }

    /// Maintainer note 1 on #955: a send whose report is lost is invisible to the cap. The
    /// carrier keeps it, stops, and sends nothing new until the hub has it.
    #[tokio::test]
    async fn a_report_that_cannot_reach_the_hub_is_kept_and_nothing_more_is_sent_until_it_does() {
        let mail = FakeMail::default();
        let mut state = CarrierState::default();
        let hub = FakeHub::new(HubAnswer::Nudges(vec![
            nudge("sam", Some("sam@example.org"), None),
            nudge("kim", Some("kim@example.org"), None),
        ]));
        hub.broken.store(true, std::sync::atomic::Ordering::SeqCst);
        let r = run(&hub, &mail, &mut state, 0).await;
        assert_eq!((r.sent, r.unreported), (1, 1), "stopped after the first unrecorded send: {r:?}");
        assert_eq!(state.unreported.len(), 1);

        // Still broken: the hub lists sam again (it never heard), and nothing is re-sent.
        let hub = FakeHub::new(HubAnswer::Nudges(vec![nudge("sam", Some("sam@example.org"), None)]));
        hub.broken.store(true, std::sync::atomic::Ordering::SeqCst);
        let r = run(&hub, &mail, &mut state, 1).await;
        assert_eq!((r.sent, r.unreported), (0, 1));
        assert_eq!(mail.sent.lock().unwrap().len(), 1, "no repeat send while the report path is down");

        // Mended: the old report goes first, then new work.
        let hub = FakeHub::new(HubAnswer::Nudges(vec![nudge("kim", Some("kim@example.org"), None)]));
        let r = run(&hub, &mail, &mut state, 2).await;
        assert_eq!((r.sent, r.unreported), (1, 0));
        assert!(state.unreported.is_empty());
        assert_eq!(*hub.reports.lock().unwrap(), vec![("sam".to_string(), true), ("kim".to_string(), true)]);
    }

    /// Maintainer note 2 on #955: a hub from before K3a answers 404, and "not answering" would
    /// send the operator after the wrong fault.
    #[tokio::test]
    async fn a_hub_without_the_route_is_named_as_such_to_the_operator() {
        #[derive(Default)]
        struct Bodies(Mutex<Vec<String>>);
        #[async_trait::async_trait]
        impl Mailer for Bodies {
            async fn send(&self, _to: &str, _subject: &str, body: &str) -> Result<()> {
                self.0.lock().unwrap().push(body.into());
                Ok(())
            }
        }
        let mail = Bodies::default();
        let mut state = CarrierState::default();
        for h in [0, 6] {
            pass(&FakeHub::new(HubAnswer::NoRoute), &mail, "op@example.org", chrono::Duration::hours(6),
                &mut state, at(h), false).await.unwrap();
        }
        let bodies = mail.0.lock().unwrap();
        assert_eq!(bodies.len(), 1);
        assert!(bodies[0].contains("before K3a") && !bodies[0].contains("not answering"), "{}", bodies[0]);
    }

    #[tokio::test]
    async fn a_dry_run_sends_and_reports_nothing() {
        let hub = FakeHub::new(HubAnswer::Nudges(vec![nudge("sam", Some("sam@example.org"), None)]));
        let mail = FakeMail::default();
        pass(&hub, &mail, "op@example.org", chrono::Duration::hours(6), &mut CarrierState::default(), at(0), true)
            .await.unwrap();
        assert!(mail.sent.lock().unwrap().is_empty() && hub.reports.lock().unwrap().is_empty());
    }

    #[test]
    fn no_field_can_add_a_header_and_a_non_ascii_subject_is_encoded() {
        let m = render_message("hub@example.org", "sam@example.org\r\nBcc: x@evil.example",
            "Café AV\r\nBcc: y@evil.example", "line one\nline two", at(0));
        let headers = m.split("\r\n\r\n").next().unwrap();
        assert!(!headers.contains("\r\nBcc:"), "{headers}");
        assert!(headers.contains("Subject: =?UTF-8?B?"), "{headers}");
        assert!(m.ends_with("line one\r\nline two\r\n"));
        assert_eq!(base64(b"Man"), "TWFu");
        assert_eq!(base64(b"Ma"), "TWE=");
        assert_eq!(base64(b"M"), "TQ==");
        assert_eq!(encode_subject("Venue AV"), "Venue AV");
    }

    /// The real mailer, against a stand-in `curl` that records its argv and stdin.
    #[tokio::test]
    async fn the_curl_mailer_passes_the_login_by_file_and_the_message_on_stdin() {
        use std::os::unix::fs::PermissionsExt;
        let dir = tempfile::tempdir().unwrap();
        let fake = dir.path().join("curl");
        let log = dir.path().join("argv");
        let msg = dir.path().join("stdin");
        std::fs::write(&fake, format!(
            "#!/bin/sh\nprintf '%s\\n' \"$@\" > '{}'\ncat > '{}'\n", log.display(), msg.display())).unwrap();
        std::fs::set_permissions(&fake, std::fs::Permissions::from_mode(0o755)).unwrap();
        let cfg = Config {
            hub_admin_url: "http://127.0.0.1:8772".into(),
            smtp_url: "smtps://smtp.example.org:465".into(),
            from: "hub@example.org".into(),
            operator_address: "op@example.org".into(),
            netrc_file: Some(dir.path().join("netrc")),
            curl: fake,
            locked_alert_hours: 6,
            state_file: dir.path().join("state.json"),
        };
        CurlMailer { cfg }.send("sam@example.org", "Venue AV: you're the backup", "Alex owns Venue AV.")
            .await.unwrap();
        let argv: Vec<String> = std::fs::read_to_string(&log).unwrap().lines().map(String::from).collect();
        let after = |flag: &str| argv.iter().position(|a| a == flag).map(|i| argv[i + 1].clone());
        assert_eq!(after("--mail-rcpt").as_deref(), Some("sam@example.org"));
        assert_eq!(after("--mail-from").as_deref(), Some("hub@example.org"));
        assert_eq!(after("--url").as_deref(), Some("smtps://smtp.example.org:465"));
        assert!(after("--netrc-file").unwrap().ends_with("netrc"));
        assert!(argv.iter().any(|a| a == "--ssl-reqd"), "never send in the clear: {argv:?}");
        assert!(!argv.iter().any(|a| a == "--user" || a == "-u"), "the login stays in the file: {argv:?}");
        let sent = std::fs::read_to_string(&msg).unwrap();
        assert!(sent.starts_with("From: hub@example.org\r\nTo: sam@example.org\r\n"), "{sent}");
        assert!(sent.ends_with("\r\n\r\nAlex owns Venue AV.\r\n"), "{sent}");
    }

    #[test]
    fn a_missing_state_file_is_a_fresh_start_and_a_bad_one_is_an_error() {
        let dir = tempfile::tempdir().unwrap();
        let p = dir.path().join("state.json");
        assert_eq!(CarrierState::load(&p).unwrap(), CarrierState::default());
        let s = CarrierState { unreachable_since: Some(at(1)), last_alert_at: None, unreported: vec![Attempt {
            commitment_id: "c".into(), about_index: 7, party_id: "sam".into(), ok: true }] };
        s.save(&p).unwrap();
        assert_eq!(CarrierState::load(&p).unwrap(), s);
        std::fs::write(&p, b"nope").unwrap();
        assert!(CarrierState::load(&p).is_err());
    }
}
