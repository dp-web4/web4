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
    /// The hub's `operator.token`, for a hub run with `HUB_OPERATOR_AUTH=token`. Sent as
    /// `X-Operator-Token` on every operator-plane call. Omit it on a loopback-only hub. Without
    /// it a token-mode hub answers 403, and the pass fails (exit 1) and names this field.
    #[serde(default)]
    operator_token_file: Option<PathBuf>,
}

/// Read the operator token file, if one is configured. A configured file that is missing or
/// empty is an error at start, not a 403 on every pass.
fn read_operator_token(file: Option<&Path>) -> Result<Option<String>> {
    let Some(f) = file else { return Ok(None) };
    let t = std::fs::read_to_string(f).with_context(|| format!("reading operator_token_file {}", f.display()))?;
    let t = t.trim();
    if t.is_empty() {
        bail!("operator_token_file {} is empty", f.display());
    }
    Ok(Some(t.to_string()))
}

/// What a 401/403 from the operator plane means, said so the operator can act on it.
fn refused_by_operator_plane(what: &str, status: reqwest::StatusCode, sent_token: bool) -> String {
    if sent_token {
        format!("{what} answered {status}: the hub refused the operator token. Check that \
                 operator_token_file holds the hub's current operator.token")
    } else {
        format!("{what} answered {status}: the hub wants an operator token (HUB_OPERATOR_AUTH=token). \
                 Set operator_token_file to the hub's operator.token")
    }
}

fn default_curl() -> PathBuf {
    PathBuf::from("curl")
}

fn default_alert_hours() -> u32 {
    6
}

/// What a dry run prints for one row. The link is the recipient's whole credential, and a dry
/// run's output lands in the journal, so it never carries one (Legion, #957).
fn dry_run_line(address: &str, n: &Nudge) -> String {
    let body = match &n.link {
        Some(link) => n.body.replace(link.as_str(), "<link withheld>"),
        None => n.body.clone(),
    };
    format!("would send to {address}: {} | {body}", n.subject)
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
    /// The movement link in `body` (K4), if the hub minted one. A dry run withholds it.
    #[serde(default)]
    link: Option<String>,
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
    /// 401/403: the operator plane refused the carrier: no token, or the wrong one. A fault in
    /// this carrier's config, not a hub that is down, so it fails the pass instead of waiting
    /// out the locked-hub window.
    Refused(String),
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
    /// The chapter notices due. `Ok(None)` when the hub has no chapter routes (404) or is
    /// locked (503): nothing to do.
    async fn notices(&self) -> Result<Option<Vec<Notice>>>;
    /// Report one notice. An error means the hub has not recorded it.
    async fn notice_sent(&self, notice_id: &str, ok: bool) -> Result<()>;
}

#[async_trait::async_trait]
trait Mailer {
    async fn send(&self, to: &str, subject: &str, body: &str) -> Result<()>;
}

struct HttpHub {
    base: String,
    http: reqwest::Client,
    /// Sent as `X-Operator-Token` on every call, when the hub runs with `HUB_OPERATOR_AUTH=token`.
    operator_token: Option<String>,
}

impl HttpHub {
    fn url(&self, path: &str) -> String {
        format!("{}{path}", self.base.trim_end_matches('/'))
    }

    fn req(&self, method: reqwest::Method, url: &str) -> reqwest::RequestBuilder {
        let r = self.http.request(method, url);
        match &self.operator_token {
            Some(t) => r.header("X-Operator-Token", t),
            None => r,
        }
    }

    fn is_refusal(status: reqwest::StatusCode) -> bool {
        status == reqwest::StatusCode::UNAUTHORIZED || status == reqwest::StatusCode::FORBIDDEN
    }

    fn refused(&self, what: &str, status: reqwest::StatusCode) -> String {
        refused_by_operator_plane(what, status, self.operator_token.is_some())
    }
}

#[async_trait::async_trait]
impl Hub for HttpHub {
    async fn nudges(&self) -> HubAnswer {
        let url = self.url("/admin/api/commitments/nudges");
        let resp = match self.req(reqwest::Method::GET, &url).send().await {
            Ok(r) => r,
            Err(e) => return HubAnswer::Down(e.to_string()),
        };
        if Self::is_refusal(resp.status()) {
            return HubAnswer::Refused(self.refused(&url, resp.status()));
        }
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
        let url = self.url("/admin/api/commitments/nudges/delivered");
        let resp = self.req(reqwest::Method::POST, &url).json(&serde_json::json!({
            "commitment_id": a.commitment_id,
            "about_index": a.about_index,
            "party_id": a.party_id,
            "channel": "email",
            "ok": a.ok,
        })).send().await.with_context(|| format!("POST {url}"))?;
        let status = resp.status();
        if Self::is_refusal(status) {
            // Not the hub judging the report: it never read it. Keep it, like a transport error.
            bail!("{}", self.refused(&format!("POST {url}"), status));
        }
        if status.is_success() {
            Ok(Report::Recorded)
        } else if status.is_client_error() {
            Ok(Report::Refused(format!("{status}: {}", resp.text().await.unwrap_or_default())))
        } else {
            bail!("POST {url} answered {status}")
        }
    }

    async fn notices(&self) -> Result<Option<Vec<Notice>>> {
        let url = self.url("/admin/api/chapter/notices");
        let resp = self.req(reqwest::Method::GET, &url).send().await.context("listing notices")?;
        let status = resp.status();
        if Self::is_refusal(status) {
            bail!("{}", self.refused(&url, status));
        }
        if status == reqwest::StatusCode::NOT_FOUND || status == reqwest::StatusCode::SERVICE_UNAVAILABLE {
            return Ok(None);
        }
        if !status.is_success() {
            bail!("{url} answered {status}");
        }
        #[derive(Deserialize)]
        struct Listing {
            notices: Vec<Notice>,
        }
        Ok(Some(resp.json::<Listing>().await.context("reading notices")?.notices))
    }

    async fn notice_sent(&self, notice_id: &str, ok: bool) -> Result<()> {
        let url = self.url("/admin/api/chapter/notices/sent");
        let resp = self.req(reqwest::Method::POST, &url)
            .json(&serde_json::json!({ "notice_id": notice_id, "ok": ok }))
            .send().await.with_context(|| format!("POST {url}"))?;
        let status = resp.status();
        if Self::is_refusal(status) {
            bail!("{}", self.refused(&format!("POST {url}"), status));
        }
        if !status.is_success() {
            bail!("POST {url} answered {status}");
        }
        Ok(())
    }
}

/// The bare address for the SMTP envelope. `from` may be a display form (`Chapter <chapter@x.org>`,
/// as the chapter example shows): that belongs in the `From:` header, but `MAIL FROM` takes the
/// address alone, and servers answer the display form with 501.
fn envelope_address(from: &str) -> &str {
    match (from.rfind('<'), from.rfind('>')) {
        (Some(open), Some(close)) if open < close => from[open + 1..close].trim(),
        _ => from.trim(),
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
                  "--mail-from", envelope_address(&self.cfg.from), "--mail-rcpt", to, "--upload-file", "-"]);
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

/// What the carrier remembers between passes: how long the hub has been unreachable, and the
/// reports it still owes the hub.
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
    /// Chapter notices sent (or failed) whose report did not reach the hub. The hub lists a
    /// notice until it hears it was sent, so without this a lost report re-sends the same
    /// welcome every pass. Re-reported before any notice is sent.
    #[serde(default)]
    unreported_notices: Vec<NoticeReport>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
struct NoticeReport {
    notice_id: String,
    ok: bool,
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
                    println!("{}", dry_run_line(address, &n));
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
        HubAnswer::Refused(m) => bail!("{m}"),
    };
    // Said in the journal on every pass, not only in the operator's alert hours from now.
    tracing::warn!("the hub {why}");
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

/// One row of `GET /admin/api/chapter/notices`: the chapter layer's own mail (a welcome, "you're
/// on this event", a recap). Off the ledger: each is reported back as sent or failed by id.
#[derive(Clone, Debug, Deserialize)]
struct Notice {
    notice_id: String,
    address: String,
    subject: String,
    body: String,
}

/// Send the chapter notices the hub lists. A hub with no chapter routes answers 404, and that is
/// nothing to do, not an error. A dry run prints subjects and recipients, never bodies: each body
/// carries the person's chapter page link.
///
/// The hub lists a notice until it hears it was sent, so a *sent* report that does not get through
/// is kept in `state` and the pass stops; the next one re-reports it before sending anything. The
/// same rule as nudge attempts: a lost report must not become the same email every five minutes.
///
/// A *failed-send* report is never kept or replayed. The hub counts every `ok: false` it receives
/// and stops listing a notice after its `NOTICE_MAX_ATTEMPTS` (3) of them, so replaying one whose answer
/// was lost (but which the hub may have recorded) could count a single failed send several times
/// and drop the welcome. Left alone, the worst case is one uncounted failure: the hub lists the
/// notice again and the next pass makes a real second attempt.
async fn notice_pass(hub: &dyn Hub, mail: &dyn Mailer, state: &mut CarrierState, dry_run: bool) -> Result<u32> {
    if !dry_run {
        let pending = std::mem::take(&mut state.unreported_notices);
        let mut first_err = None;
        for r in pending {
            if !r.ok {
                // Never replay a failed-send report (see above). Only a state file from before this
                // rule could hold one.
                tracing::warn!("dropping a kept failed-send report for {}: replaying it could count one failure twice", r.notice_id);
                continue;
            }
            if let Err(e) = hub.notice_sent(&r.notice_id, r.ok).await {
                if first_err.is_none() {
                    first_err = Some(e);
                }
                state.unreported_notices.push(r);
            }
        }
        if let Some(e) = first_err {
            return Err(e.context(format!("{} notice report(s) still not recorded by the hub; sending no notice \
                until they are", state.unreported_notices.len())));
        }
    }
    let Some(notices) = hub.notices().await? else { return Ok(0) };
    let mut sent = 0;
    for n in notices {
        if dry_run {
            println!("would send notice {} to {}: {}", n.notice_id, n.address, n.subject);
            continue;
        }
        let ok = match mail.send(&n.address, &n.subject, &n.body).await {
            Ok(()) => { sent += 1; true }
            Err(e) => { tracing::warn!("notice {} failed: {e:#}", n.notice_id); false }
        };
        if let Err(e) = hub.notice_sent(&n.notice_id, ok).await {
            if !ok {
                return Err(e.context(format!("notice {} failed to send and its failure report may not have reached \
                    the hub; not replayed, because the hub counts each failure report as another failed send. If \
                    the hub didn't record it, it lists the notice again and the next pass retries the send",
                    n.notice_id)));
            }
            state.unreported_notices.push(NoticeReport { notice_id: n.notice_id.clone(), ok });
            return Err(e.context(format!("notice {} was sent but the hub has not recorded it; kept, and \
                re-reported before the next notice is sent", n.notice_id)));
        }
    }
    Ok(sent)
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
        operator_token: read_operator_token(cfg.operator_token_file.as_deref())?,
    };
    let mail = CurlMailer { cfg: cfg.clone() };
    let alert_after = chrono::Duration::hours(i64::from(cfg.locked_alert_hours));
    loop {
        let mut state = CarrierState::load(&cfg.state_file)?;
        let mut failed = 0;
        match pass(&hub, &mail, &cfg.operator_address, alert_after, &mut state, Utc::now(), args.dry_run).await {
            Ok(r) => tracing::info!(?r, "nudge pass"),
            Err(e) => { failed += 1; tracing::warn!("nudge pass failed: {e:#}") }
        }
        match notice_pass(&hub, &mail, &mut state, args.dry_run).await {
            Ok(0) => {}
            Ok(n) => tracing::info!(sent = n, "chapter notices"),
            Err(e) => { failed += 1; tracing::warn!("notice pass failed: {e:#}") }
        }
        if !args.dry_run {
            state.save(&cfg.state_file)?;
        }
        match args.every {
            Some(secs) => tokio::time::sleep(std::time::Duration::from_secs(secs)).await,
            // A one-shot run under a timer: a failed pass is a failed unit, not SUCCESS with
            // `sent: 0` in the journal.
            None if failed > 0 => bail!("{failed} of 2 passes failed; the warnings above say why"),
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
        /// The notices the hub lists: like the real hub, a notice stays listed until it is
        /// reported sent.
        notices: Mutex<Vec<Notice>>,
        notice_reports: Mutex<Vec<(String, bool)>>,
        /// Failure reports per notice, counted like `admin_notice_sent`: one per request.
        notice_failures: Mutex<std::collections::HashMap<String, u32>>,
        /// Commit the next N notice reports, then answer with an error as if the reply was lost.
        lose_acks: std::sync::atomic::AtomicU32,
    }

    impl FakeHub {
        fn new(answer: HubAnswer) -> Self {
            Self { answer: Mutex::new(Some(answer)), reports: Mutex::new(Vec::new()), refuse: false,
                broken: std::sync::atomic::AtomicBool::new(false), notices: Mutex::new(Vec::new()),
                notice_reports: Mutex::new(Vec::new()), notice_failures: Mutex::new(Default::default()),
                lose_acks: std::sync::atomic::AtomicU32::new(0) }
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
        async fn notices(&self) -> Result<Option<Vec<Notice>>> {
            let failures = self.notice_failures.lock().unwrap();
            Ok(Some(self.notices.lock().unwrap().iter()
                .filter(|n| failures.get(&n.notice_id).copied().unwrap_or(0) < NOTICE_MAX_ATTEMPTS_AT_HUB)
                .cloned().collect()))
        }
        async fn notice_sent(&self, notice_id: &str, ok: bool) -> Result<()> {
            if self.broken.load(std::sync::atomic::Ordering::SeqCst) {
                bail!("POST answered 502 Bad Gateway");
            }
            self.notice_reports.lock().unwrap().push((notice_id.into(), ok));
            if ok {
                self.notices.lock().unwrap().retain(|n| n.notice_id != notice_id);
            } else {
                *self.notice_failures.lock().unwrap().entry(notice_id.into()).or_insert(0) += 1;
            }
            let lose = self.lose_acks.load(std::sync::atomic::Ordering::SeqCst);
            if lose > 0 {
                self.lose_acks.store(lose - 1, std::sync::atomic::Ordering::SeqCst);
                bail!("connection reset after the hub committed the report");
            }
            Ok(())
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
            subject: "Venue AV: you're the backup".into(), body: "Alex owns Venue AV.".into(), link: None,
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

    #[test]
    fn a_dry_run_line_withholds_the_link() {
        let mut n = nudge("sam", Some("sam@example.org"), None);
        n.body = "Alex owns Venue AV.\n\nSay where it stands: https://hub.example.org/c/c.p.1.abcd".into();
        n.link = Some("https://hub.example.org/c/c.p.1.abcd".into());
        let line = dry_run_line("sam@example.org", &n);
        assert!(!line.contains("/c/") && line.contains("<link withheld>"), "{line}");
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
            from: "Hub <hub@example.org>".into(),
            operator_address: "op@example.org".into(),
            netrc_file: Some(dir.path().join("netrc")),
            curl: fake,
            locked_alert_hours: 6,
            state_file: dir.path().join("state.json"),
            operator_token_file: None,
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
        assert!(sent.starts_with("From: Hub <hub@example.org>\r\nTo: sam@example.org\r\n"), "{sent}");
        assert!(sent.ends_with("\r\n\r\nAlex owns Venue AV.\r\n"), "{sent}");
    }

    /// A display-form `from` keeps its name in the header; the envelope gets the address alone.
    #[test]
    fn the_envelope_sender_is_the_bare_address() {
        assert_eq!(envelope_address("AI Collective Portland <chapter@example.org>"), "chapter@example.org");
        assert_eq!(envelope_address("hub@example.org"), "hub@example.org");
        assert_eq!(envelope_address(" <hub@example.org> "), "hub@example.org");
        let message = render_message("Chapter <chapter@example.org>", "sam@example.org", "s", "b", Utc::now());
        assert!(message.starts_with("From: Chapter <chapter@example.org>\r\n"), "{message}");
    }

    #[test]
    fn a_missing_state_file_is_a_fresh_start_and_a_bad_one_is_an_error() {
        let dir = tempfile::tempdir().unwrap();
        let p = dir.path().join("state.json");
        assert_eq!(CarrierState::load(&p).unwrap(), CarrierState::default());
        let s = CarrierState { unreachable_since: Some(at(1)), last_alert_at: None, unreported: vec![Attempt {
            commitment_id: "c".into(), about_index: 7, party_id: "sam".into(), ok: true }],
            unreported_notices: vec![NoticeReport { notice_id: "welcome.p1".into(), ok: true }] };
        s.save(&p).unwrap();
        assert_eq!(CarrierState::load(&p).unwrap(), s);
        std::fs::write(&p, b"nope").unwrap();
        assert!(CarrierState::load(&p).is_err());
    }

    fn notice(id: &str, address: &str) -> Notice {
        Notice { notice_id: id.into(), address: address.into(), subject: "Welcome to the chapter".into(),
            body: "Your page: https://hub.example.org/p/x".into() }
    }

    /// A refused carrier is its own config fault: the pass fails at once, and the operator is not
    /// told, hours later, that the hub "is not answering".
    #[tokio::test]
    async fn a_refused_carrier_fails_the_pass_and_does_not_start_the_locked_clock() {
        let mail = FakeMail::default();
        let mut state = CarrierState::default();
        for h in [0, 7] {
            let hub = FakeHub::new(HubAnswer::Refused("403 Forbidden: set operator_token_file".into()));
            let e = pass(&hub, &mail, "op@example.org", chrono::Duration::hours(6), &mut state, at(h), false)
                .await.unwrap_err();
            assert!(e.to_string().contains("operator_token_file"), "{e:#}");
        }
        assert_eq!(state, CarrierState::default());
        assert!(mail.sent.lock().unwrap().is_empty(), "no locked-hub alert for a refusal");
    }

    /// The hub lists a notice until it hears it was sent. A report that is lost must not turn one
    /// welcome into a welcome every pass.
    #[tokio::test]
    async fn a_notice_whose_report_is_lost_is_not_sent_again() {
        let hub = FakeHub::new(HubAnswer::Nudges(Vec::new()));
        *hub.notices.lock().unwrap() = vec![notice("welcome.natalie", "n@example.org"), notice("welcome.yemaya", "y@example.org")];
        hub.broken.store(true, std::sync::atomic::Ordering::SeqCst);
        let mail = FakeMail::default();
        let mut state = CarrierState::default();
        let e = notice_pass(&hub, &mail, &mut state, false).await.unwrap_err();
        assert!(format!("{e:#}").contains("welcome.natalie"), "{e:#}");
        assert_eq!(mail.sent.lock().unwrap().len(), 1, "stopped after the first unrecorded send");
        assert_eq!(state.unreported_notices, vec![NoticeReport { notice_id: "welcome.natalie".into(), ok: true }]);
        // Still broken: nothing new goes out.
        notice_pass(&hub, &mail, &mut state, false).await.unwrap_err();
        assert_eq!(mail.sent.lock().unwrap().len(), 1);
        // Back: the old report lands first, and only the notice nobody has had goes out.
        hub.broken.store(false, std::sync::atomic::Ordering::SeqCst);
        assert_eq!(notice_pass(&hub, &mail, &mut state, false).await.unwrap(), 1);
        let to: Vec<String> = mail.sent.lock().unwrap().iter().map(|(t, _)| t.clone()).collect();
        assert_eq!(to, vec!["n@example.org", "y@example.org"]);
        assert!(state.unreported_notices.is_empty());
        assert_eq!(hub.notice_reports.lock().unwrap().clone(),
            vec![("welcome.natalie".to_string(), true), ("welcome.yemaya".to_string(), true)]);
    }

    /// The hub's limit (`NOTICE_MAX_ATTEMPTS` in rest/commitments/chapter.rs): after this many
    /// failure reports a notice is no longer listed.
    const NOTICE_MAX_ATTEMPTS_AT_HUB: u32 = 3;

    /// Fails the first send, then delivers.
    #[derive(Default)]
    struct FlakyMail {
        attempts: Mutex<Vec<(String, bool)>>,
    }

    #[async_trait::async_trait]
    impl Mailer for FlakyMail {
        async fn send(&self, to: &str, _subject: &str, _body: &str) -> Result<()> {
            let mut a = self.attempts.lock().unwrap();
            let first = a.is_empty();
            a.push((to.into(), !first));
            if first { bail!("421 try again later") } else { Ok(()) }
        }
    }

    #[tokio::test]
    async fn a_failed_send_report_whose_answer_is_lost_is_never_replayed_so_one_failure_counts_once() {
        let hub = FakeHub::new(HubAnswer::Nudges(Vec::new()));
        *hub.notices.lock().unwrap() = vec![notice("welcome.natalie", "n@example.org")];
        let mail = FlakyMail::default();
        let mut state = CarrierState::default();
        // Pass 1: SMTP fails; the hub commits the failure report, but its answer is lost.
        hub.lose_acks.store(1, std::sync::atomic::Ordering::SeqCst);
        let e = notice_pass(&hub, &mail, &mut state, false).await.unwrap_err();
        assert!(format!("{e:#}").contains("not replayed"), "{e:#}");
        assert!(state.unreported_notices.is_empty(), "a failed-send report is never kept for replay");
        // Passes 2 and 3 replay nothing, so the hub still counts one failure and still lists the
        // welcome; pass 2 makes a real second attempt, which delivers.
        assert_eq!(notice_pass(&hub, &mail, &mut state, false).await.unwrap(), 1);
        assert_eq!(notice_pass(&hub, &mail, &mut state, false).await.unwrap(), 0, "delivered and recorded: not sent again");
        assert_eq!(hub.notice_failures.lock().unwrap().get("welcome.natalie").copied(), Some(1),
            "one real failure, counted once");
        assert_eq!(*mail.attempts.lock().unwrap(),
            vec![("n@example.org".to_string(), false), ("n@example.org".to_string(), true)]);
        assert_eq!(hub.notice_reports.lock().unwrap().clone(),
            vec![("welcome.natalie".to_string(), false), ("welcome.natalie".to_string(), true)]);
    }

    #[tokio::test]
    async fn a_kept_failed_send_report_from_an_older_state_file_is_dropped_not_replayed() {
        let hub = FakeHub::new(HubAnswer::Nudges(Vec::new()));
        let mail = FakeMail::default();
        let mut state = CarrierState { unreported_notices: vec![
            NoticeReport { notice_id: "welcome.yemaya".into(), ok: false },
            NoticeReport { notice_id: "welcome.natalie".into(), ok: true },
        ], ..Default::default() };
        assert_eq!(notice_pass(&hub, &mail, &mut state, false).await.unwrap(), 0);
        assert!(state.unreported_notices.is_empty());
        assert_eq!(hub.notice_reports.lock().unwrap().clone(), vec![("welcome.natalie".to_string(), true)]);
        assert!(hub.notice_failures.lock().unwrap().is_empty());
    }

    #[test]
    fn the_operator_token_file_is_trimmed_and_an_empty_one_is_an_error() {
        let dir = tempfile::tempdir().unwrap();
        let p = dir.path().join("operator.token");
        assert_eq!(read_operator_token(None).unwrap(), None);
        std::fs::write(&p, "s3cret\n").unwrap();
        assert_eq!(read_operator_token(Some(&p)).unwrap().as_deref(), Some("s3cret"));
        std::fs::write(&p, " \n").unwrap();
        assert!(read_operator_token(Some(&p)).is_err());
        assert!(read_operator_token(Some(&dir.path().join("missing"))).is_err());
    }

    /// A stand-in for a hub run with `HUB_OPERATOR_AUTH=token`: every operator route answers 403
    /// unless `X-Operator-Token` matches. Records each notice report it accepts.
    async fn token_hub(token: &'static str) -> (String, std::sync::Arc<Mutex<Vec<serde_json::Value>>>) {
        use axum::{http::{HeaderMap, StatusCode}, response::IntoResponse, routing::{get, post}, Json, Router};
        let seen = std::sync::Arc::new(Mutex::new(Vec::<serde_json::Value>::new()));
        let s = seen.clone();
        let authed = move |h: &HeaderMap| h.get("x-operator-token").and_then(|v| v.to_str().ok()) == Some(token);
        let app = Router::new()
            .route("/admin/api/commitments/nudges", get(move |h: HeaderMap| async move {
                if !authed(&h) { return StatusCode::FORBIDDEN.into_response(); }
                Json(serde_json::json!({ "nudges": [] })).into_response()
            }))
            .route("/admin/api/chapter/notices", get(move |h: HeaderMap| async move {
                if !authed(&h) { return StatusCode::FORBIDDEN.into_response(); }
                Json(serde_json::json!({ "notices": [
                    { "notice_id": "welcome.natalie", "address": "n@example.org", "subject": "Welcome", "body": "b" }
                ] })).into_response()
            }))
            .route("/admin/api/chapter/notices/sent", post(move |h: HeaderMap, Json(body): Json<serde_json::Value>| {
                let s = s.clone();
                async move {
                    if !authed(&h) { return StatusCode::FORBIDDEN.into_response(); }
                    s.lock().unwrap().push(body);
                    Json(serde_json::json!({ "recorded": true })).into_response()
                }
            }));
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let addr = listener.local_addr().unwrap();
        tokio::spawn(async move { axum::serve(listener, app).await.unwrap() });
        (format!("http://{addr}"), seen)
    }

    fn http_hub(base: &str, token: Option<&str>) -> HttpHub {
        HttpHub { base: base.into(), http: reqwest::Client::new(), operator_token: token.map(Into::into) }
    }

    /// The 2026-11-26 chapter hub: token mode, a carrier with no token. Every pass answered 403
    /// and the unit still read SUCCESS with `sent: 0`. Now each pass fails and names the field.
    #[tokio::test]
    async fn a_token_mode_hub_refuses_a_carrier_without_the_token_loudly() {
        let (base, seen) = token_hub("s3cret").await;
        let mail = FakeMail::default();
        let mut state = CarrierState::default();
        let hub = http_hub(&base, None);
        match hub.nudges().await {
            HubAnswer::Refused(m) => assert!(m.contains("403") && m.contains("operator_token_file"), "{m}"),
            other => panic!("expected a refusal, got {other:?}"),
        }
        let e = notice_pass(&hub, &mail, &mut state, false).await.unwrap_err();
        assert!(format!("{e:#}").contains("operator_token_file"), "{e:#}");
        // The wrong token is named as the wrong token, not a missing one.
        match http_hub(&base, Some("stale")).nudges().await {
            HubAnswer::Refused(m) => assert!(m.contains("refused the operator token"), "{m}"),
            other => panic!("expected a refusal, got {other:?}"),
        }
        assert!(mail.sent.lock().unwrap().is_empty() && seen.lock().unwrap().is_empty());
    }

    #[tokio::test]
    async fn with_the_token_the_carrier_lists_sends_and_reports() {
        let (base, seen) = token_hub("s3cret").await;
        let mail = FakeMail::default();
        let mut state = CarrierState::default();
        let hub = http_hub(&base, Some("s3cret"));
        assert!(matches!(hub.nudges().await, HubAnswer::Nudges(ref v) if v.is_empty()));
        assert_eq!(notice_pass(&hub, &mail, &mut state, false).await.unwrap(), 1);
        assert_eq!(mail.sent.lock().unwrap()[0].0, "n@example.org");
        assert_eq!(seen.lock().unwrap().clone(), vec![serde_json::json!({ "notice_id": "welcome.natalie", "ok": true })]);
    }
}
