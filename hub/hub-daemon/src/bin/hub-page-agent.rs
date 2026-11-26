// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! `hub-page-agent`: the runner for the chapter's own assistant (hub/docs/PRD_CHAPTER_PAGE_AGENT.md).
//!
//! The hub decides; this wakes the model. Each pass:
//! 1. asks `GET /admin/api/chapter/agent/jobs` on the hub's loopback plane for the next open ask
//!    (the hub leases it and hands back a job token for that one ask);
//! 2. reads the job, `GET .../jobs/:token`: the system prompt, the prompt and the answer schema,
//!    all composed by the hub;
//! 3. runs the Claude Code CLI in print mode with **no tools** (`--tools ""`), no MCP servers, no
//!    settings, hooks or session saved, in an empty directory, under the login of the user this
//!    runs as (or a `claude setup-token` token from `oauth_token_file`);
//! 4. hands the structured answer back, `POST .../jobs/:token`. If the hub refuses the draft
//!    (422), it retries once with the reason; if that fails too, it reports the refusal.
//!
//! This process holds the subscription login and the model choice, and nothing else: it reaches
//! only the job routes, and the hub validates and governs whatever comes back. The model can't
//! reach anything at all: its only output is text.
//!
//! Usage: `hub-page-agent --config page-agent.json [--dry-run] [--every SECS]`. With no `--every`
//! it runs one pass and exits.

use std::collections::VecDeque;
use std::path::PathBuf;
use std::process::Stdio;
use std::time::{Duration, Instant};

use anyhow::{bail, Context, Result};
use clap::Parser;
use serde::Deserialize;
use tokio::io::AsyncWriteExt;

#[derive(Parser)]
#[command(name = "hub-page-agent", about = "Wake the chapter's own assistant for each open ask and hand its answer to the hub")]
struct Args {
    /// The runner's JSON config (see `Config`).
    #[arg(long)]
    config: PathBuf,
    /// Print the job the hub composed; run no model, answer nothing. The job stays leased.
    #[arg(long)]
    dry_run: bool,
    /// Run a pass every SECS seconds instead of once.
    #[arg(long)]
    every: Option<u64>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct Config {
    /// The hub's operator plane, e.g. `http://127.0.0.1:8780`. Loopback only.
    hub_admin_url: String,
    /// The Claude Code CLI. Default `claude` on PATH.
    #[serde(default = "default_claude")]
    claude: String,
    /// A model alias or name for `--model`. Default: the CLI's own default.
    #[serde(default)]
    model: Option<String>,
    /// How long one model run may take.
    #[serde(default = "default_timeout")]
    timeout_secs: u64,
    /// At most this many model runs in any hour, whatever the hub asks.
    #[serde(default = "default_runs")]
    max_runs_per_hour: usize,
    /// Named in the runner line the hub records ("pub · claude 2.1.331 · claude-opus-5-5").
    #[serde(default = "default_host")]
    host_label: String,
    /// A 0600 file holding a `claude setup-token` token, passed as `CLAUDE_CODE_OAUTH_TOKEN`.
    /// Without it, the CLI uses the login of the user this runs as.
    #[serde(default)]
    oauth_token_file: Option<PathBuf>,
    /// The hub's `operator.token`, for a hub run with `HUB_OPERATOR_AUTH=token`. Sent as
    /// `X-Operator-Token`. Omit it on a loopback-only hub.
    #[serde(default)]
    operator_token_file: Option<PathBuf>,
}

fn default_claude() -> String {
    "claude".into()
}
fn default_timeout() -> u64 {
    240
}
fn default_runs() -> usize {
    30
}
fn default_host() -> String {
    "runner".into()
}

struct Runner {
    cfg: Config,
    http: reqwest::Client,
    runs: VecDeque<Instant>,
    cli_version: String,
    operator_token: Option<String>,
    /// An empty directory the CLI runs in, so it finds no project files or settings.
    workdir: PathBuf,
}

/// What the model answered, as the schema shapes it.
#[derive(Debug, Default)]
struct ModelAnswer {
    reply: String,
    page: Option<serde_json::Value>,
    brief: Option<String>,
    model: Option<String>,
}

impl Runner {
    fn url(&self, rest: &str) -> String {
        format!("{}/admin/api/chapter/agent/{rest}", self.cfg.hub_admin_url.trim_end_matches('/'))
    }

    fn at_cap(&mut self) -> bool {
        let hour_ago = Instant::now() - Duration::from_secs(3600);
        while self.runs.front().is_some_and(|t| *t < hour_ago) {
            self.runs.pop_front();
        }
        self.runs.len() >= self.cfg.max_runs_per_hour
    }

    /// Run the model once: no tools, no MCP, no settings, no saved session, in an empty
    /// directory. The prompt goes on stdin.
    async fn run_model(&mut self, system: &str, prompt: &str, schema: &serde_json::Value) -> Result<ModelAnswer> {
        self.runs.push_back(Instant::now());
        let mut cmd = tokio::process::Command::new(&self.cfg.claude);
        cmd.current_dir(&self.workdir)
            .args(["-p", "--tools", "", "--strict-mcp-config", "--setting-sources", "", "--no-session-persistence",
                   "--output-format", "json"])
            .arg("--json-schema").arg(schema.to_string())
            .arg("--system-prompt").arg(system)
            .stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::piped())
            .kill_on_drop(true);
        if let Some(m) = &self.cfg.model {
            cmd.arg("--model").arg(m);
        }
        if let Some(f) = &self.cfg.oauth_token_file {
            let tok = std::fs::read_to_string(f).with_context(|| format!("reading {}", f.display()))?;
            cmd.env("CLAUDE_CODE_OAUTH_TOKEN", tok.trim());
        }
        let mut child = cmd.spawn().with_context(|| format!("starting {}", self.cfg.claude))?;
        let mut stdin = child.stdin.take().context("stdin")?;
        stdin.write_all(prompt.as_bytes()).await?;
        drop(stdin);
        let out = tokio::time::timeout(Duration::from_secs(self.cfg.timeout_secs), child.wait_with_output()).await
            .context("the model run timed out")??;
        if !out.status.success() {
            bail!("the CLI exited {}: {}", out.status, String::from_utf8_lossy(&out.stderr).chars().take(400).collect::<String>());
        }
        parse_cli_output(&out.stdout)
    }

    fn req(&self, method: reqwest::Method, rest: &str) -> reqwest::RequestBuilder {
        let r = self.http.request(method, self.url(rest));
        match &self.operator_token {
            Some(t) => r.header("X-Operator-Token", t),
            None => r,
        }
    }

    async fn post_answer(&self, token: &str, body: &serde_json::Value) -> Result<reqwest::Response> {
        Ok(self.req(reqwest::Method::POST, &format!("jobs/{token}")).json(body).send().await?)
    }

    fn runner_line(&self, model: Option<&str>) -> String {
        format!("{} · claude {} · {}", self.cfg.host_label, self.cli_version, model.unwrap_or("default model"))
    }

    /// One pass: take the next job, if any, and see it through.
    async fn pass(&mut self, dry_run: bool) -> Result<bool> {
        if self.at_cap() {
            eprintln!("hub-page-agent: at {} runs this hour; not taking jobs", self.cfg.max_runs_per_hour);
            return Ok(false);
        }
        let jobs: serde_json::Value = self.req(reqwest::Method::GET, "jobs").send().await?.error_for_status()?.json().await?;
        let Some(job) = jobs["jobs"].as_array().and_then(|a| a.first()).cloned() else { return Ok(false) };
        let token = job["token"].as_str().context("job token")?.to_string();
        let request_id = job["request_id"].as_str().unwrap_or("?").to_string();
        let packet: serde_json::Value = self.req(reqwest::Method::GET, &format!("jobs/{token}")).send().await?
            .error_for_status()?.json().await?;
        let (system, prompt, schema) = (packet["system"].as_str().context("system")?.to_string(),
            packet["prompt"].as_str().context("prompt")?.to_string(), packet["schema"].clone());
        if dry_run {
            println!("=== job {request_id}\n--- system\n{system}\n--- prompt\n{prompt}");
            return Ok(true);
        }
        let started = Instant::now();
        let mut answer = self.run_model(&system, &prompt, &schema).await
            .with_context(|| format!("ask {request_id}"))?;
        let mut body = answer_body(&answer, self.runner_line(answer.model.as_deref()));
        let resp = self.post_answer(&token, &body).await?;
        if resp.status() == reqwest::StatusCode::UNPROCESSABLE_ENTITY {
            // The hub refused the draft. Once more, with the reason; then report the refusal.
            let why = error_text(resp).await;
            eprintln!("hub-page-agent: ask {request_id}: draft refused ({why}); retrying once");
            let retry = format!("{prompt}\n\n## Your last answer was refused\n\nThe hub refused the page you wrote: {why}\nWrite it again so it passes, or set page to null and say what you need.\n");
            answer = self.run_model(&system, &retry, &schema).await.with_context(|| format!("ask {request_id}, retry"))?;
            body = answer_body(&answer, self.runner_line(answer.model.as_deref()));
            let resp = self.post_answer(&token, &body).await?;
            if resp.status() == reqwest::StatusCode::UNPROCESSABLE_ENTITY {
                let why = error_text(resp).await;
                let refused = serde_json::json!({ "reply": answer.reply, "refused": why,
                    "runner": self.runner_line(answer.model.as_deref()) });
                self.post_answer(&token, &refused).await?.error_for_status()?;
                eprintln!("hub-page-agent: ask {request_id}: refused twice; reported");
                return Ok(true);
            }
            resp.error_for_status()?;
        } else {
            resp.error_for_status()?;
        }
        eprintln!("hub-page-agent: ask {request_id} answered in {:.0}s", started.elapsed().as_secs_f64());
        Ok(true)
    }
}

/// The CLI's `--output-format json` result: the schema-shaped answer is `structured_output`.
fn parse_cli_output(stdout: &[u8]) -> Result<ModelAnswer> {
    let v: serde_json::Value = serde_json::from_slice(stdout).context("the CLI's output isn't JSON")?;
    if v["is_error"].as_bool() == Some(true) {
        bail!("the CLI reported an error: {}", v["result"].as_str().unwrap_or("").chars().take(400).collect::<String>());
    }
    let s = if v["structured_output"].is_object() {
        v["structured_output"].clone()
    } else {
        // Older CLIs: the answer is the JSON text in `result`.
        serde_json::from_str(v["result"].as_str().unwrap_or("")).context("no structured answer in the CLI's output")?
    };
    let reply = s["reply"].as_str().unwrap_or("").trim().to_string();
    if reply.is_empty() {
        bail!("the model gave no reply");
    }
    let model = v["modelUsage"].as_object().and_then(|m| m.keys().next().cloned());
    Ok(ModelAnswer {
        reply,
        page: Some(s["page"].clone()).filter(|p| p.is_object()),
        brief: s["brief"].as_str().map(str::to_string).filter(|b| !b.trim().is_empty()),
        model,
    })
}

fn answer_body(a: &ModelAnswer, runner: String) -> serde_json::Value {
    let mut body = serde_json::json!({ "reply": a.reply, "runner": runner });
    if let Some(p) = &a.page {
        body["page"] = p.clone();
    }
    if let Some(b) = &a.brief {
        body["brief"] = serde_json::Value::String(b.clone());
    }
    body
}

async fn error_text(resp: reqwest::Response) -> String {
    let v: serde_json::Value = resp.json().await.unwrap_or_default();
    v["error"].as_str().or_else(|| v["message"].as_str()).unwrap_or("no reason given").chars().take(300).collect()
}

fn loopback_only(url: &str) -> Result<()> {
    let rest = url.strip_prefix("http://").context("hub_admin_url must be http:// on loopback")?;
    let host = rest.split(['/', ':']).next().unwrap_or("");
    if !matches!(host, "127.0.0.1" | "localhost") && !rest.starts_with("[::1]") {
        bail!("hub_admin_url must be on loopback (127.0.0.1, localhost or [::1]), not {host}");
    }
    Ok(())
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();
    let cfg: Config = serde_json::from_slice(&std::fs::read(&args.config)
        .with_context(|| format!("reading {}", args.config.display()))?)
        .with_context(|| format!("parsing {}", args.config.display()))?;
    loopback_only(&cfg.hub_admin_url)?;
    let cli_version = std::process::Command::new(&cfg.claude).arg("--version").output().ok()
        .map(|o| String::from_utf8_lossy(&o.stdout).split_whitespace().next().unwrap_or("?").to_string())
        .unwrap_or_else(|| "?".into());
    let operator_token = match &cfg.operator_token_file {
        Some(f) => Some(std::fs::read_to_string(f).with_context(|| format!("reading {}", f.display()))?.trim().to_string()),
        None => None,
    };
    let mut r = Runner {
        operator_token,
        http: reqwest::Client::builder().timeout(Duration::from_secs(30)).build()?,
        runs: VecDeque::new(),
        cli_version,
        workdir: {
            let d = std::env::temp_dir().join(format!("hub-page-agent-{}", std::process::id()));
            std::fs::create_dir_all(&d).with_context(|| format!("creating {}", d.display()))?;
            d
        },
        cfg,
    };
    loop {
        match r.pass(args.dry_run).await {
            // Took a job: look again at once, in case more are waiting.
            Ok(true) if args.every.is_some() && !args.dry_run => continue,
            Ok(_) => {}
            Err(e) => eprintln!("hub-page-agent: {e:#}"),
        }
        match args.every {
            Some(secs) => tokio::time::sleep(Duration::from_secs(secs)).await,
            None => return Ok(()),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_structured_answer_is_read_from_the_clis_output() {
        let out = br#"{"is_error":false,"result":"{}","modelUsage":{"claude-opus-5-5":{}},
            "structured_output":{"reply":"Done.","page":{"headline":"Hi"},"brief":null}}"#;
        let a = parse_cli_output(out).unwrap();
        assert_eq!(a.reply, "Done.");
        assert_eq!(a.page.unwrap()["headline"], "Hi");
        assert!(a.brief.is_none());
        assert_eq!(a.model.as_deref(), Some("claude-opus-5-5"));
    }

    #[test]
    fn a_null_page_is_no_page_and_an_error_is_an_error() {
        let a = parse_cli_output(br#"{"is_error":false,"structured_output":{"reply":"What time?","page":null,"brief":null}}"#).unwrap();
        assert!(a.page.is_none());
        assert!(parse_cli_output(br#"{"is_error":true,"result":"rate limited"}"#).is_err());
        assert!(parse_cli_output(br#"{"is_error":false,"structured_output":{"reply":"  ","page":null}}"#).is_err());
    }

    #[test]
    fn the_hub_must_be_on_loopback() {
        assert!(loopback_only("http://127.0.0.1:8780").is_ok());
        assert!(loopback_only("http://localhost:8780/").is_ok());
        assert!(loopback_only("http://[::1]:8780").is_ok());
        assert!(loopback_only("http://chapter.example.org").is_err());
        assert!(loopback_only("https://127.0.0.1:8780").is_err());
    }
}
