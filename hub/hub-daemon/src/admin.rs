// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! V2-16: read-only operator dashboard at `/admin`.
//!
//! Purpose: give a hub operator a single-page view of what the hub is
//! holding without grepping JSON. Renders the same data the REST + MCP
//! surfaces expose — chapter identity, members, role-fill snapshot,
//! recent ledger acts, current law — in a hand-rolled HTML page.
//!
//! Read-only by design. Operators still mutate via CLI (`hub set-law`,
//! `hub assign-role`, etc.) or REST (`POST /v1/hubs/{id}/events`).
//! Adding write paths here would force decisions about authentication
//! that V2-7's signed-envelope model already answered for non-browser
//! clients — those decisions can wait until there's evidence we need
//! browser-driven writes.
//!
//! No templating engine. Plain `format!()` + a tiny embedded stylesheet.
//! If this grows past a handful of pages, switch to askama then.

use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::{Html, IntoResponse},
    routing::get,
    Router,
};
use hub_lib::events::HubEvent;
use hub_lib::law::HubLawExt;
use hub_lib::signer::RemoteSigner; // signer_kind() — signer is now a concrete SwappableSigner
use hub_lib::state::HubState;

use crate::rest::RestState;

// Style family: Metalinxx Web4 Tools palette (charcoal + sage), per
// 4-gov/source/brand/BRAND.md. Deliberately NO product or company logo —
// the hub is the standard's reference implementation ("standard, not
// product"); the society name is the masthead.
const STYLE: &str = r#"
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         max-width: 1100px; margin: 1.5rem auto; padding: 0 1rem;
         background: #2d2d2d; color: #e8e8e8; }
  h1 { font-size: 1.4rem; border-bottom: 2px solid #509982; padding-bottom: 0.3rem; }
  h2 { font-size: 1.1rem; margin-top: 1.5rem; color: #a8aeac; }
  nav { background: #383838; padding: 0.6rem 0.9rem; border-radius: 4px;
        margin-bottom: 1.2rem; }
  nav a { margin-right: 1rem; text-decoration: none; color: #5fb89a; }
  nav a:hover { text-decoration: underline; }
  table { border-collapse: collapse; width: 100%; margin: 0.5rem 0 1rem; }
  th, td { text-align: left; padding: 0.35rem 0.6rem; border-bottom: 1px solid #565656;
           font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 0.85rem; }
  th { background: #383838; font-weight: 600; }
  .muted { color: #7b817f; font-style: italic; }
  .pill { display: inline-block; padding: 0.1rem 0.5rem; border-radius: 10px;
          font-size: 0.75rem; background: #4d6664; color: #d7deda; }
  .pill-warn { background: #6b5a3a; color: #f5deb8; }
  pre { background: #383838; padding: 0.8rem; border-radius: 4px;
        overflow-x: auto; font-size: 0.8rem; }
  .grid { display: grid; grid-template-columns: max-content 1fr; gap: 0.3rem 1rem; }
  .grid dt { font-weight: 600; color: #a8aeac; }
  .grid dd { margin: 0; font-family: ui-monospace, monospace; font-size: 0.9rem; }
  footer { margin-top: 2rem; padding-top: 0.6rem; border-top: 1px solid #565656;
           color: #7b817f; font-size: 0.8rem; }
</style>
"#;

fn layout(s: &RestState, title: &str, body: &str) -> Html<String> {
    let hub_name = &s.hub_name;
    // The Members page lists full rosters + skills, and the Joins/Manage write
    // pages exist ONLY on the loopback operator plane. Show their nav links
    // there; omit them on the read-only fleet plane so we don't advertise links
    // that would 404 or expose member data to anonymous public visitors.
    let operator_nav = if s.operator_plane {
        r#"
      <a href="/admin">Overview</a>
      <a href="/admin/ledger">Ledger</a>
      <a href="/admin/pairs">Pairs</a>
      <a href="/admin/members">Members</a>
      <a href="/admin/joins">Joins ⚙</a>
      <a href="/admin/manage">Manage ⚙</a>"#
    } else {
        ""
    };
    let nav = format!(
        r#"<nav>
      <a href="/">Home</a>
      <a href="/admin/roles">Roles</a>
      <a href="/admin/law">Law</a>
      <a href="/admin/council">Council</a>{operator_nav}
    </nav>"#
    );
    Html(format!(
        "<!doctype html><html><head><meta charset=\"utf-8\">\
         <title>{title} — {hub_name}</title>{STYLE}</head>\
         <body><h1>{hub_name} — {title}</h1>{nav}{body}\
         <footer>Web4 hub admin · read-only · operator dashboard</footer>\
         </body></html>",
        title = html_escape(title),
        hub_name = html_escape(hub_name),
    ))
}

/// Simple public layout for the fleet-plane landing page (no admin nav).
fn public_layout(hub_name: &str, hub_id: &str, body: &str) -> Html<String> {
    Html(format!(
        "<!doctype html><html><head><meta charset=\"utf-8\">\
         <title>{hub_name}</title>{STYLE}<style>.button {{ display:inline-block; padding:0.4rem 0.9rem; \
         background:#509982; color:#fff; border-radius:4px; text-decoration:none; margin:0.3rem 0; }}\
         code {{ background:#383838; padding:0.15rem 0.4rem; border-radius:3px; }}</style></head>\
         <body><h1>{hub_name}</h1>{body}\
         <footer>Web4 hub · <a href=\"/.well-known/web4-hub.json\">descriptor</a> · <a href=\"/v1/hubs/{hub_id}/law\">law</a></footer>\
         </body></html>",
        hub_name = html_escape(hub_name),
        hub_id = html_escape(hub_id),
    ))
}

fn html_escape(s: &str) -> String {
    s.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
}

/// PUBLIC admin surfaces: deliberate transparency only — the landing page,
/// the society's law, the council roster, and role fill (same info as public
/// `/v1/state`). The ledger browser does NOT belong here: `ledger_detail`
/// renders full event payloads, and `MemberAdded`/`MemberProfileUpdated`/
/// `MemberSkillDeclared` events carry names, pubkeys, skills, and profile
/// values (including self-tier fields) — a public ledger page lets an
/// anonymous visitor reconstruct the entire roster, bypassing the MCP
/// read-tool gating AND the profile visibility tiers (review 2026-07-23).
pub fn router(state: RestState) -> Router {
    Router::new()
        .route("/", get(landing_page))
        .route("/admin/roles", get(roles))
        .route("/admin/law", get(law))
        .route("/admin/council", get(council))
        .with_state(state)
}

/// Operator-plane admin pages. These expose member rosters, skills, and
/// admission/management actions, so they live ONLY on the loopback operator
/// listener behind operator auth.

// ---------- error ----------

#[derive(Debug)]
pub(crate) struct AdminError(StatusCode, String);

impl IntoResponse for AdminError {
    fn into_response(self) -> axum::response::Response {
        let body = format!(
            "<!doctype html><html><body>{STYLE}<h1>Error {}</h1><pre>{}</pre></body></html>",
            self.0.as_u16(),
            html_escape(&self.1),
        );
        (self.0, Html(body)).into_response()
    }
}

impl From<anyhow::Error> for AdminError {
    fn from(e: anyhow::Error) -> Self {
        AdminError(StatusCode::INTERNAL_SERVER_ERROR, format!("{:#}", e))
    }
}

// ---------- handlers ----------

/// Public landing page for the hub. This is the first thing an external visitor
/// sees; it explains what the hub is, how to install Hestia, and how to request
/// membership, without exposing member rosters or skills.
async fn landing_page(State(s): State<RestState>) -> Result<Html<String>, AdminError> {
    let locked = s.is_locked();
    let law_guard = s.law.read().await;
    let law_version = law_guard
        .as_ref()
        .map(|l| l.version.clone())
        .unwrap_or_else(|| "(none set)".to_string());
    // Truthful by construction: evaluate the SAME synthetic R6 the join path
    // runs (rest.rs submit_join), instead of the advisory `admission.open`
    // display knob — the knob is consumed by no gate, and rendering it let
    // the page claim "closed admission" while the law auto-admitted
    // (review 2026-07-23).
    let admission_decision = law_guard
        .as_ref()
        .map(|law| {
            law.evaluate_outcome(&hub_lib::law::R6Request {
                role: "applicant".to_string(),
                action: "member_join_request".to_string(),
                payload: serde_yaml::Value::Null,
                resource: Default::default(),
            })
            .decision
        })
        // No law loaded → the join path allows (open-by-default): say so.
        .unwrap_or(hub_lib::law::Decision::Allow);
    drop(law_guard);

    let status = if locked {
        r#"<span class="pill pill-warn">🔒 locked</span> — the hub vault is locked. Only the operator can unlock it."#
    } else {
        r#"<span class="pill">unlocked</span> — the hub is active and accepting sealed requests."#
    };

    let admission_note = match admission_decision {
        hub_lib::law::Decision::Allow | hub_lib::law::Decision::Warn => {
            "This chapter currently allows open admission: anyone with a Web4 LCT can request citizenship."
        }
        hub_lib::law::Decision::Escalate => {
            "This chapter uses closed admission: membership requests queue for operator review."
        }
        hub_lib::law::Decision::Deny => {
            "This chapter is not accepting membership requests right now."
        }
    };

    let body = format!(
        r#"<div style="max-width:700px">
<h2>Welcome to {hub_name}</h2>
<p>This is a <strong>Web4 community hub</strong> — a self-sovereign society server. Members join with a Web4 LCT, communicate through end-to-end encrypted channels, declare skills, and build reputation.</p>

<h3>Status</h3>
<p>{status}</p>

<h3>Membership</h3>
<p>{admission_note}</p>

<h3>Get started</h3>
<ol>
  <li><strong>Install Hestia</strong> — the local app that holds your identity and talks to this hub.<br>
      <a class="button" href="https://github.com/dp-web4/hestia/releases">Download Hestia</a></li>
  <li><strong>Request citizenship</strong> — from Hestia, run:<br>
      <code>hestia connect-hub https://&lt;this-host&gt;</code></li>
  <li><strong>Wait for review</strong> — the operator will admit or decline your request.</li>
</ol>

<h3>Transparency</h3>
<ul>
  <li><a href="/.well-known/web4-hub.json">Machine-readable hub descriptor</a></li>
  <li><a href="/v1/hubs/{hub_id}/law">Current hub law</a> (version {law_version})</li>
</ul>

<p class="muted">Operators: the dashboard lives on the loopback operator plane (<code>/admin</code> on the operator port).</p>
</div>"#,
        hub_name = html_escape(&s.hub_name),
        hub_id = s.hub_id,
        law_version = html_escape(&law_version),
    );

    Ok(public_layout(&s.hub_name, &s.hub_id.to_string(), &body))
}

async fn overview(State(s): State<RestState>) -> Result<Html<String>, AdminError> {
    let ledger = s.ledger.lock().await;
    let projected = HubState::project(&*ledger);
    let entries = ledger.entries();
    let head_hash = ledger.head_hash().to_string();
    let backend = ledger.backend_kind().as_str();
    let ledger_len = entries.len();
    let last_20: Vec<_> = entries.iter().rev().take(20).cloned().collect();
    drop(ledger);

    let society = s.society().await?;
    let law_guard = s.law.read().await;
    let (law_version, norms, procedures) = match &*law_guard {
        Some(l) => (l.version.clone(), l.norms.len(), l.procedures.len()),
        None => ("(none set)".into(), 0, 0),
    };
    drop(law_guard);

    let mut body = String::new();
    body.push_str("<h2>Hub identity</h2><dl class=\"grid\">");
    body.push_str(&format!("<dt>Society LCT</dt><dd>{}</dd>", s.hub_id));
    body.push_str(&format!("<dt>Sovereign LCT</dt><dd>{}</dd>", s.sovereign_lct_id));
    body.push_str(&format!(
        "<dt>Sovereign mode</dt><dd>{:?}</dd>",
        s.signer.signer_kind()
    ));
    body.push_str(&format!("<dt>Charter hash</dt><dd>{}</dd>", html_escape(&society.charter_hash)));
    body.push_str(&format!("<dt>Metabolic state</dt><dd>{:?}</dd>", society.state));
    body.push_str(&format!("<dt>Ledger backend</dt><dd>{}</dd>", backend));
    body.push_str(&format!("<dt>Ledger length</dt><dd>{}</dd>", ledger_len));
    body.push_str(&format!("<dt>Head hash</dt><dd>{}</dd>", html_escape(&head_hash)));
    body.push_str("</dl>");

    body.push_str("<h2>Membership</h2><dl class=\"grid\">");
    body.push_str(&format!("<dt>Members</dt><dd>{}</dd>", projected.member_count()));
    body.push_str(&format!("<dt>Member pubkeys pinned</dt><dd>{}</dd>", projected.member_pubkeys.len()));
    body.push_str(&format!("<dt>Skills declared</dt><dd>{}</dd>", projected.skill_index.len()));
    body.push_str("</dl>");

    body.push_str("<h2>Law</h2><dl class=\"grid\">");
    body.push_str(&format!("<dt>Version</dt><dd>{}</dd>", html_escape(&law_version)));
    body.push_str(&format!("<dt>Norms</dt><dd>{}</dd>", norms));
    body.push_str(&format!("<dt>Procedures</dt><dd>{}</dd>", procedures));
    body.push_str("</dl>");

    body.push_str("<h2>Recent acts (last 20)</h2>");
    body.push_str(&render_ledger_table(&last_20));

    Ok(layout(&s, "Overview", &body))
}

pub(crate) async fn members(State(s): State<RestState>) -> Result<Html<String>, AdminError> {
    let ledger = s.ledger.lock().await;
    let projected = HubState::project(&*ledger);
    drop(ledger);

    let mut body = String::from("<h2>Members</h2>");
    if projected.members.is_empty() {
        body.push_str("<p class=\"muted\">No members.</p>");
    } else {
        body.push_str("<table><thead><tr><th>LCT</th><th>Name</th><th>Skills</th><th>Has pubkey</th></tr></thead><tbody>");
        for m in projected.members.values() {
            let name = m.name.as_deref().unwrap_or("(unnamed)");
            let skills = if m.skills.is_empty() {
                "<span class=\"muted\">none</span>".to_string()
            } else {
                m.skills.iter().cloned().collect::<Vec<_>>().join(", ")
            };
            let pk_pill = if projected.member_pubkeys.contains_key(&m.lct_id) {
                "<span class=\"pill\">yes</span>"
            } else {
                "<span class=\"pill pill-warn\">no (pre-V2-12)</span>"
            };
            body.push_str(&format!(
                "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>",
                m.lct_id,
                html_escape(name),
                skills,
                pk_pill,
            ));
        }
        body.push_str("</tbody></table>");
    }

    Ok(layout(&s, "Members", &body))
}

async fn roles(State(s): State<RestState>) -> Result<Html<String>, AdminError> {
    let society = s.society().await?;
    let ledger = s.ledger.lock().await;
    let projected = HubState::project(&*ledger);
    drop(ledger);

    let mut body = String::from("<h2>Role assignments</h2>");
    if society.roles.is_empty() {
        body.push_str("<p class=\"muted\">No roles assigned.</p>");
    } else {
        body.push_str("<table><thead><tr><th>Role</th><th>Role LCT</th><th>Filled by</th></tr></thead><tbody>");
        let mut entries: Vec<_> = society.roles.iter().collect();
        entries.sort_by(|a, b| a.0.cmp(b.0));
        for (role_key, assignment) in entries {
            body.push_str(&format!(
                "<tr><td>{}</td><td>{}</td><td>{}</td></tr>",
                html_escape(role_key),
                assignment.role_lct_id,
                assignment.filling_entity_lct_id,
            ));
        }
        body.push_str("</tbody></table>");
    }

    body.push_str("<h2 style=\"margin-top:2rem\">Sovereign Council</h2>");
    body.push_str("<dl class=\"grid\">");
    body.push_str(&format!("<dt>Founding Sovereign</dt><dd>{}</dd>", society.founder_lct_id));
    body.push_str(&format!("<dt>Active sovereign</dt><dd>{}</dd>", s.sovereign_lct_id));
    if society.founder_lct_id != s.sovereign_lct_id {
        body.push_str("<dt>Note</dt><dd><span class=\"pill pill-warn\">sovereignty has rotated since founding</span></dd>");
    }
    body.push_str(&format!("<dt>Council holders</dt><dd>{}</dd>", projected.council_holders.len()));
    match projected.council_threshold {
        Some((m, n)) => {
            body.push_str(&format!(
                "<dt>Threshold</dt><dd>{}-of-{} \
                 <span class=\"pill pill-warn\">recorded only; Phase 2 will enforce on submit_event</span></dd>",
                m, n,
            ));
        }
        None => {
            body.push_str("<dt>Threshold</dt><dd>single-signer (none set)</dd>");
        }
    }
    body.push_str("</dl>");

    if !projected.council_holders.is_empty() {
        body.push_str("<table style=\"margin-top:0.6rem\"><thead><tr><th>Holder LCT</th><th>Name</th><th>Pubkey pinned</th></tr></thead><tbody>");
        for holder in &projected.council_holders {
            let name = projected.members.get(holder)
                .and_then(|m| m.name.clone())
                .unwrap_or_else(|| "(unnamed)".into());
            let pk_pill = if projected.council_pubkeys.contains_key(holder) {
                "<span class=\"pill\">yes</span>"
            } else {
                "<span class=\"pill pill-warn\">no</span>"
            };
            body.push_str(&format!(
                "<tr><td>{}</td><td>{}</td><td>{}</td></tr>",
                holder, html_escape(&name), pk_pill,
            ));
        }
        body.push_str("</tbody></table>");
    }

    Ok(layout(&s, "Roles", &body))
}

async fn ledger_list(State(s): State<RestState>) -> Result<Html<String>, AdminError> {
    let ledger = s.ledger.lock().await;
    let entries: Vec<_> = ledger.entries().iter().rev().take(200).cloned().collect();
    drop(ledger);

    let body = format!(
        "<h2>Ledger ({} entries shown, newest first)</h2>{}",
        entries.len(),
        render_ledger_table(&entries),
    );
    Ok(layout(&s, "Ledger", &body))
}

async fn ledger_detail(
    State(s): State<RestState>,
    Path(index): Path<u64>,
) -> Result<Html<String>, AdminError> {
    let ledger = s.ledger.lock().await;
    let entry = ledger.entries().iter().find(|e| e.index == index).cloned();
    drop(ledger);

    let entry = entry.ok_or_else(|| {
        AdminError(StatusCode::NOT_FOUND, format!("no ledger entry at index {}", index))
    })?;

    let event_json = serde_json::to_string_pretty(&entry.event)
        .map_err(|e| AdminError(StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;

    let proposal_ref_html = match entry.proposal_ref {
        Some(id) => format!(
            "<dt>Proposal</dt><dd><a href=\"/admin/council\">{}</a> \
             <span class=\"pill\">council-authorized</span></dd>",
            id,
        ),
        None => String::new(),
    };
    let body = format!(
        "<h2>Entry #{}</h2><dl class=\"grid\">\
         <dt>Index</dt><dd>{}</dd>\
         <dt>Timestamp</dt><dd>{}</dd>\
         <dt>Actor LCT</dt><dd>{}</dd>\
         <dt>Event kind</dt><dd>{}</dd>\
         {}\
         <dt>Prev hash</dt><dd>{}</dd>\
         <dt>Entry hash</dt><dd>{}</dd>\
         <dt>Signature</dt><dd>{}</dd>\
         </dl>\
         <h2>Event payload</h2><pre>{}</pre>",
        index,
        entry.index,
        entry.timestamp,
        entry.actor_lct_id,
        entry.event.kind(),
        proposal_ref_html,
        html_escape(&entry.prev_hash),
        html_escape(&entry.entry_hash),
        html_escape(&entry.signature),
        html_escape(&event_json),
    );
    Ok(layout(&s, &format!("Entry #{}", index), &body))
}

async fn council(State(s): State<RestState>) -> Result<Html<String>, AdminError> {
    use hub_lib::proposal::ProposalStatus;
    let ledger = s.ledger.lock().await;
    let projected = HubState::project(&*ledger);
    drop(ledger);
    let proposals = {
        let store = s.open_store().await
            .map_err(|e| AdminError(StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
        store.list_proposals().await
            .map_err(|e| AdminError(StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?
    };

    let mut body = String::from("<h2>Sovereign Council proposals</h2><dl class=\"grid\">");
    let (m, n) = projected.council_threshold.unwrap_or((1, (projected.council_holders.len() + 1) as u32));
    body.push_str(&format!("<dt>Threshold</dt><dd>{}-of-{}", m, n));
    if m < 2 {
        body.push_str(" <span class=\"pill\">single-signer mode — propose flow optional</span>");
    } else {
        body.push_str(" <span class=\"pill\">council enforcement active — /v1/hubs/.../events rejects single-signer</span>");
    }
    body.push_str("</dd>");
    body.push_str(&format!("<dt>Holders eligible to vote</dt><dd>{}</dd>", projected.council_holders.len() + 1));
    body.push_str(&format!("<dt>Proposals on record</dt><dd>{}</dd>", proposals.len()));
    body.push_str("</dl>");

    if proposals.is_empty() {
        body.push_str("<p class=\"muted\">No proposals yet. POST a council_propose envelope to /v1/hubs/{id}/council/propose to create one.</p>");
    } else {
        body.push_str("<table><thead><tr><th>Proposal</th><th>Act</th><th>Proposer</th><th>Votes</th><th>Status</th><th>Proposed</th><th>Expires</th></tr></thead><tbody>");
        for p in &proposals {
            let votes = p.unique_signers().len();
            let status_html = match &p.status {
                ProposalStatus::Open => format!(
                    "<span class=\"pill\">open ({}/{})</span>",
                    votes.min(m as usize), m,
                ),
                ProposalStatus::Committed { entry_index, .. } => format!(
                    "<span class=\"pill\">committed → <a href=\"/admin/ledger/{}\">#{}</a></span>",
                    entry_index, entry_index,
                ),
                ProposalStatus::Rejected { reason } => format!(
                    "<span class=\"pill pill-warn\">rejected: {}</span>",
                    html_escape(reason),
                ),
                ProposalStatus::Expired => "<span class=\"pill pill-warn\">expired</span>".into(),
            };
            body.push_str(&format!(
                "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>",
                short(&p.id),
                p.proposed_event.kind(),
                short(&p.proposed_by),
                votes,
                status_html,
                p.proposed_at.format("%Y-%m-%d %H:%M:%S UTC"),
                p.expires_at.format("%Y-%m-%d %H:%M:%S UTC"),
            ));
        }
        body.push_str("</tbody></table>");
    }

    Ok(layout(&s, "Council", &body))
}

async fn pairs(State(s): State<RestState>) -> Result<Html<String>, AdminError> {
    use hub_lib::state::PairStatus;
    let ledger = s.ledger.lock().await;
    let projected = HubState::project(&*ledger);
    drop(ledger);

    let now = chrono::Utc::now();
    let mut body = String::from("<h2>LCT paired channels</h2>");
    body.push_str(&format!(
        "<dl class=\"grid\"><dt>Total pairs on ledger</dt><dd>{}</dd>\
         <dt>Active right now</dt><dd>{}</dd>\
         <dt>Pending</dt><dd>{}</dd>\
         <dt>Revoked or expired</dt><dd>{}</dd></dl>",
        projected.pairs.len(),
        projected.pairs.values().filter(|p| p.effective_status(now) == "active").count(),
        projected.pairs.values().filter(|p| p.effective_status(now) == "pending").count(),
        projected.pairs.values()
            .filter(|p| matches!(p.effective_status(now), "revoked" | "expired"))
            .count(),
    ));

    if projected.pairs.is_empty() {
        body.push_str("<p class=\"muted\">No pairs on record. \
            POST a pair_request envelope to /v1/hubs/{id}/pairs/request.</p>");
    } else {
        body.push_str(
            "<table><thead><tr>\
             <th>Pair</th><th>Initiator → Counterparty</th><th>Purpose</th>\
             <th>Status</th><th>Proposed</th><th>Confirmed</th><th>Msgs</th>\
             </tr></thead><tbody>"
        );
        // Newest-first
        let mut pairs: Vec<_> = projected.pairs.values().collect();
        pairs.sort_by(|a, b| b.proposed_at.cmp(&a.proposed_at));
        for p in pairs {
            let eff = p.effective_status(now);
            let pill_class = match eff {
                "active" => "pill",
                "pending" => "pill",
                _ => "pill pill-warn",
            };
            let revoke_detail = match &p.revocation_kind {
                Some(k) => format!(" ({:?})", k),
                None => String::new(),
            };
            body.push_str(&format!(
                "<tr><td>{}</td><td>{} → {}</td><td>{}</td>\
                 <td><span class=\"{}\">{}{}</span></td>\
                 <td>{}</td><td>{}</td><td>{}</td></tr>",
                short(&p.id),
                short(&p.initiator),
                short(&p.counterparty),
                html_escape(&p.purpose),
                pill_class,
                eff,
                html_escape(&revoke_detail),
                p.proposed_at.format("%Y-%m-%d %H:%M:%S UTC"),
                p.confirmed_at.map(|t| t.format("%H:%M:%S UTC").to_string())
                    .unwrap_or_else(|| "—".into()),
                p.message_count,
            ));
        }
        body.push_str("</tbody></table>");
        body.push_str(
            "<p class=\"muted\" style=\"margin-top:1rem\">\
             Sprint D will increment the Msgs column as relayed messages flow. \
             Today the column tracks 0 for all pairs.</p>"
        );
    }

    Ok(layout(&s, "Pairs", &body))
}

async fn law(State(s): State<RestState>) -> Result<Html<String>, AdminError> {
        let store = s.open_store().await?;
    let yaml = store.read_law().await?;

    let mut body = String::from("<h2>Hub law</h2>");
    match yaml {
        None => {
            body.push_str(
                "<p class=\"muted\">No law set. Open-admission applies by default.</p>\
                 <p>Set one via <code>hub set-law &lt;hub-dir&gt; law.yaml</code>, \
                 then <code>POST /v1/admin/reload-law</code>.</p>",
            );
        }
        Some(yaml) => {
            // Provenance of the most recent amendment, surfaced from the witnessed
            // LawAmended entry so it's inspectable here (no ledger-digging).
            let last_amend = {
                let ledger = s.ledger.lock().await;
                ledger.entries().iter().rev().find_map(|e| match &e.event {
                    HubEvent::LawAmended { amended_by, .. } => Some((e.timestamp, *amended_by)),
                    _ => None,
                })
            };
            let amended = match last_amend {
                Some((ts, by)) => format!(
                    "<dt>Last amended</dt><dd>{} <span class=\"muted\">by {}</span></dd>",
                    ts.format("%Y-%m-%d %H:%M UTC"), short(&by),
                ),
                None => "<dt>Last amended</dt><dd class=\"muted\">never (genesis law)</dd>".to_string(),
            };
            let law_guard = s.law.read().await;
            if let Some(l) = &*law_guard {
                body.push_str(&format!(
                    "<dl class=\"grid\"><dt>Version</dt><dd>{}</dd>{}\
                     <dt>Norms</dt><dd>{}</dd><dt>Procedures</dt><dd>{}</dd>\
                     <dt>Escalation triggers</dt><dd>{}</dd></dl>",
                    html_escape(&l.version),
                    amended,
                    l.norms.len(),
                    l.procedures.len(),
                    l.escalation.len(),
                ));
            }
            drop(law_guard);
            body.push_str("<h2>Raw YAML</h2><pre>");
            body.push_str(&html_escape(&yaml));
            body.push_str("</pre>");
        }
    }
    Ok(layout(&s, "Law", &body))
}

// ---------- shared bits ----------

fn render_ledger_table(entries: &[hub_lib::ledger::LedgerEntry]) -> String {
    if entries.is_empty() {
        return "<p class=\"muted\">No entries.</p>".into();
    }
    let mut out = String::from(
        "<table><thead><tr><th>#</th><th>Kind</th><th>Actor</th><th>When</th><th>Summary</th></tr></thead><tbody>",
    );
    for e in entries {
        let council_pill = if e.proposal_ref.is_some() {
            " <span class=\"pill\">council</span>"
        } else {
            ""
        };
        out.push_str(&format!(
            "<tr><td><a href=\"/admin/ledger/{idx}\">#{idx}</a>{pill}</td>\
             <td>{kind}</td><td>{actor}</td><td>{ts}</td><td>{summary}</td></tr>",
            idx = e.index,
            pill = council_pill,
            kind = e.event.kind(),
            actor = e.actor_lct_id,
            ts = e.timestamp.format("%Y-%m-%d %H:%M:%S UTC"),
            summary = event_summary(&e.event),
        ));
    }
    out.push_str("</tbody></table>");
    out
}

fn event_summary(event: &HubEvent) -> String {
    match event {
        HubEvent::Genesis { hub_name, .. } => format!("Founded \"{}\"", html_escape(hub_name)),
        HubEvent::MemberAdded { member_lct_id, member_name, member_pubkey_hex, .. } => {
            let name = member_name.as_deref().unwrap_or("(unnamed)");
            let pk = if member_pubkey_hex.is_some() { " · self-signed" } else { "" };
            format!("Member {} added{}", html_escape(name), pk)
                + &format!(" <span class=\"muted\">[{}]</span>", short(member_lct_id))
        }
        HubEvent::MemberRemoved { member_lct_id, reason, .. } => format!(
            "Member {} removed{}",
            short(member_lct_id),
            reason
                .as_deref()
                .map(|r| format!(" ({})", html_escape(r)))
                .unwrap_or_default(),
        ),
        HubEvent::RoleAssigned { role, assigned_to, .. } => {
            format!("Role {:?} → {}", role, short(assigned_to))
        }
        HubEvent::EventRecorded { event_kind, title, attended_by, .. } => format!(
            "{}: \"{}\" · {} attendee(s)",
            html_escape(event_kind),
            html_escape(title),
            attended_by.len(),
        ),
        HubEvent::CharterAmended { diff_summary, .. } => format!(
            "Charter amended{}",
            diff_summary
                .as_deref()
                .map(|s| format!(": {}", html_escape(s)))
                .unwrap_or_default(),
        ),
        HubEvent::MemberSkillDeclared { member_lct_id, skill, .. } => {
            format!("Skill \"{}\" by {}", html_escape(skill), short(member_lct_id))
        }
        HubEvent::MemberKeyPinned { member_lct_id, .. } => {
            format!("Channel key pinned for {}", short(member_lct_id))
        }
        HubEvent::DeviceEnrolled { owner_lct_id, device_lct_id, device_class, .. } => format!(
            "Device {} ({:?}) enrolled by {}",
            short(device_lct_id), device_class, short(owner_lct_id)
        ),
        HubEvent::DeviceRevoked { owner_lct_id, device_lct_id } => format!(
            "Device {} revoked by {}", short(device_lct_id), short(owner_lct_id)
        ),
        HubEvent::IntroRequested { from_lct, to_lct, .. } => {
            format!("Intro requested {} → {}", short(from_lct), short(to_lct))
        }
        HubEvent::IntroResponded { intro_id, accepted, .. } => {
            format!("Intro {} {}", short(intro_id), if *accepted { "accepted" } else { "declined" })
        }
        HubEvent::MemberProfileUpdated { member_lct_id, fields, .. } => {
            let keys: Vec<&str> = fields.keys().map(|k| k.as_str()).collect();
            format!("Profile update ({}) by {}", html_escape(&keys.join(", ")), short(member_lct_id))
        }
        HubEvent::LawAmended { version, diff_summary, .. } => format!(
            "Law → v{}{}",
            html_escape(version),
            diff_summary
                .as_deref()
                .map(|s| format!(" · {}", html_escape(s)))
                .unwrap_or_default(),
        ),
        HubEvent::CouncilMemberAdded { member_lct_id, member_name, .. } => {
            let name = member_name.as_deref().unwrap_or("(unnamed)");
            format!(
                "Council holder {} admitted <span class=\"muted\">[{}]</span>",
                html_escape(name),
                short(member_lct_id),
            )
        }
        HubEvent::CouncilMemberRemoved { member_lct_id, removal_kind, .. } => {
            format!("Council holder {} removed ({:?})", short(member_lct_id), removal_kind)
        }
        HubEvent::CouncilThresholdChanged { new_m, .. } => {
            format!("Council threshold M={} requested", new_m)
        }
        HubEvent::PairingRequested { pair_id, initiator_lct_id, counterparty_lct_id, purpose, .. } => {
            format!(
                "Pair requested {} ↔ {} <span class=\"muted\">[{}, \"{}\"]</span>",
                short(initiator_lct_id),
                short(counterparty_lct_id),
                short(pair_id),
                html_escape(purpose),
            )
        }
        HubEvent::PairingConfirmed { pair_id, confirmed_by, counterparty_ephemeral_pub_hex } => {
            let fs_pill = if counterparty_ephemeral_pub_hex.is_some() {
                " <span class=\"pill\">FS</span>"
            } else { "" };
            format!(
                "Pair confirmed by {} <span class=\"muted\">[{}]</span>{}",
                short(confirmed_by),
                short(pair_id),
                fs_pill,
            )
        }
        HubEvent::PairingRevoked { pair_id, revoked_by, revocation_kind, .. } => {
            format!(
                "Pair revoked by {} ({:?}) <span class=\"muted\">[{}]</span>",
                short(revoked_by),
                revocation_kind,
                short(pair_id),
            )
        }
        HubEvent::PairMessagePosted { pair_id, seq, from, .. } => {
            format!(
                "Pair msg seq={} from {} <span class=\"muted\">[{}]</span>",
                seq,
                short(from),
                short(pair_id),
            )
        }
        HubEvent::VaultUnlockRequested { challenge_id, tier, required, .. } => {
            format!(
                "🔒 Tier-2 unlock requested for \"{}\" (need {}) <span class=\"muted\">[{}]</span>",
                html_escape(tier),
                required,
                short(challenge_id),
            )
        }
        HubEvent::VaultUnlockAttested { challenge_id, admin_lct_id, decision, .. } => {
            format!(
                "🔑 Admin {} {} unlock <span class=\"muted\">[{}]</span>",
                short(admin_lct_id),
                html_escape(decision),
                short(challenge_id),
            )
        }
        HubEvent::VaultUnlockResolved { challenge_id, tier, granted, approvals, declines, .. } => {
            format!(
                "{} Tier-2 unlock of \"{}\" — {}/{}↑ {}↓ <span class=\"muted\">[{}]</span>",
                if *granted { "🔓" } else { "⛔" },
                html_escape(tier),
                approvals.len(),
                approvals.len(),
                declines.len(),
                short(challenge_id),
            )
        }
        HubEvent::ReferencedAct { act } => {
            use web4_core::act::ActAddress;
            let dst = match &act.address {
                ActAddress::FutureSelf { entity } => format!("future-self {}", short(entity)),
                ActAddress::Peer { lct_id } => format!("peer {}", short(lct_id)),
                ActAddress::Citizen { lct_id } => format!("citizen {}", short(lct_id)),
                ActAddress::Role { role } => format!("role {}", html_escape(role)),
                ActAddress::Society { lct_id } => format!("society {}", short(lct_id)),
            };
            format!(
                "✉️ act <code>{}</code> <span class=\"muted\">from</span> {} → {} <span class=\"muted\">[{}]</span>",
                html_escape(&act.kind),
                short(&act.actor_lct),
                dst,
                html_escape(&act.substance.uri),
            )
        }
        HubEvent::ReputationRecorded { delta } => format!(
            "📊 reputation Δ for {} <span class=\"muted\">in role</span> {} \
             <span class=\"muted\">(ΔT3 {:+.3}, ΔV3 {:+.3}) — {}</span>",
            html_escape(&delta.subject_lct),
            html_escape(&delta.role_lct),
            delta.net_trust_change(),
            delta.net_value_change(),
            html_escape(&delta.reason),
        ),
        HubEvent::ObligationOpened { request_id, subject_lct, role_lct, due_at, criticality, .. } => format!(
            "⏳ obligation <code>{}</code> opened by {} <span class=\"muted\">in role</span> {} \
             <span class=\"muted\">(due {}, {:?})</span>",
            html_escape(request_id),
            html_escape(subject_lct),
            html_escape(role_lct),
            due_at.format("%Y-%m-%d %H:%M UTC"),
            criticality,
        ),
        HubEvent::ObligationResolved { request_id, outcome, .. } => format!(
            "✅ obligation <code>{}</code> resolved <span class=\"muted\">({})</span>",
            html_escape(request_id),
            html_escape(outcome),
        ),
        HubEvent::LctPublished { lct_id, document, published_by, provenance, .. } => format!(
            "🪪 LCT published: {:?} <code>{}</code> by {} <span class=\"muted\">({:?})</span>",
            document.entity_type,
            html_escape(lct_id),
            short(published_by),
            provenance,
        ),
        HubEvent::MemberJoinRequested { member_lct_id, name, .. } => format!(
            "🚪 join requested by {} {} <span class=\"muted\">[escalated → review]</span>",
            short(member_lct_id),
            name.as_deref().map(html_escape).unwrap_or_default(),
        ),
        HubEvent::MemberJoinResolved { request_id, approved, resolved_by, reason, .. } => format!(
            "🚪 join {} (req {}) by {}{}",
            if *approved { "APPROVED" } else { "DENIED" },
            short(request_id),
            short(resolved_by),
            reason.as_deref().map(|r| format!(" — {}", html_escape(r))).unwrap_or_default(),
        ),
        HubEvent::MemberJoinReviewRequested { member_lct_id, .. } => format!(
            "🛠 denial-review requested by {} <span class=\"muted\">[repair path]</span>",
            short(member_lct_id),
        ),
        HubEvent::MemberJoinReviewResolved { review_id, granted, resolved_by, reason, .. } => format!(
            "🛠 review {} (rev {}) by {}{}",
            if *granted { "GRANTED" } else { "REFUSED" },
            short(review_id),
            short(resolved_by),
            reason.as_deref().map(|r| format!(" — {}", html_escape(r))).unwrap_or_default(),
        ),
        HubEvent::MemberAdmissionReset { member_lct_id, reset_by, .. } => format!(
            "🧹 admission reset for {} by {}",
            short(member_lct_id), short(reset_by),
        ),
    }
}

fn short(id: &uuid::Uuid) -> String {
    let s = id.to_string();
    format!("{}…", &s[..8])
}

// ============================================================================
// Operator plane GUI — write pages, mounted ONLY on the 127.0.0.1 operator
// listener (the buttons POST to the loopback-only /admin/api/* surface).
// ============================================================================

const OPERATOR_BANNER: &str = r#"<div style="background:#4d3a3a;color:#f5d5d5;padding:0.5rem 0.9rem;border-radius:4px;margin-bottom:1rem;">
  ⚙ <b>Operator plane</b> — local-only (127.0.0.1). Actions sign as the Sovereign and are witnessed to the ledger.
  &nbsp;|&nbsp; <a href="/admin/joins" style="color:#ffd9a8">Admission queue</a>
  &nbsp; <a href="/admin/manage" style="color:#ffd9a8">Manage members</a>
  &nbsp; <a href="/admin" style="color:#ffd9a8">Dashboard</a>
</div>
<style>
  button { background:#509982; color:#fff; border:0; border-radius:4px; padding:0.3rem 0.7rem;
           font-size:0.8rem; cursor:pointer; margin-right:0.3rem; }
  button:hover { background:#5fb89a; }
  button.danger { background:#a85a5a; } button.danger:hover { background:#c06b6b; }
</style>"#;

const OPERATOR_JS: &str = r#"<script>
async function hubAct(url, body) {
  const r = await fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body||{})});
  const t = await r.text();
  if (!r.ok) { alert('Failed ('+r.status+'): '+t); return; }
  location.reload();
}
function admit(id){ if(confirm('Admit this applicant as a member? Their key is pinned live.')) hubAct('/admin/api/joins/'+id+'/admit'); }
function deny(id){ const reason=prompt('Deny — reason (optional):'); if(reason!==null) hubAct('/admin/api/joins/'+id+'/deny',{reason:reason||null}); }
function rekey(id){ const k=prompt('New 64-hex Ed25519 public key for member '+id+':'); if(k) hubAct('/admin/api/members/'+id+'/key',{pubkey_hex:k.trim()}); }
function removeMember(id){ const reason=prompt('Remove member '+id+' — reason (optional):'); if(reason!==null) hubAct('/admin/api/members/'+id+'/remove',{reason:reason||null}); }
function addMember(){
  const lct=document.getElementById('add-lct').value.trim();
  const pubkey_hex=document.getElementById('add-key').value.trim();
  const name=document.getElementById('add-name').value.trim();
  if(!lct||!pubkey_hex){ alert('LCT id and pubkey (64 hex) are required.'); return; }
  hubAct('/admin/api/members/add',{lct_id:lct,pubkey_hex:pubkey_hex,name:name||null});
}
function grantReview(id){ if(confirm('Grant this review? Clears the applicant’s auto-block so they can apply again.')) hubAct('/admin/api/reviews/'+id+'/grant'); }
function refuseReview(id){ const reason=prompt('Refuse review — reason (optional):'); if(reason!==null) hubAct('/admin/api/reviews/'+id+'/refuse',{reason:reason||null}); }
function admissionReset(){ const lct=prompt('Admission-reset which LCT id? (clears denial + review standing)'); if(!lct) return; const reason=prompt('Reason (optional):'); if(reason!==null) hubAct('/admin/api/members/'+lct.trim()+'/admission-reset',{reason:reason||null}); }
function setLimits(){
  const rt=document.getElementById('lim-repeat').value.trim();
  const rv=document.getElementById('lim-review').value.trim();
  const body={};
  if(rt!=='') body.repeat_limit=parseInt(rt,10);
  if(rv!=='') body.review_limit=parseInt(rv,10);
  if(Object.keys(body).length===0){ alert('Enter at least one limit to set.'); return; }
  if(confirm('Write these admission limits to hub law? (witnessed amendment)')) hubAct('/admin/api/admission-limits',body);
}
</script>"#;

pub(crate) async fn joins_page(State(s): State<RestState>) -> Result<Html<String>, AdminError> {
    use hub_lib::state::JoinStatus;
    let ledger = s.ledger.lock().await;
    let projected = HubState::project(&*ledger);
    drop(ledger);

    let mut joins: Vec<hub_lib::state::JoinRequest> = projected.pending_joins.into_values().collect();
    joins.sort_by(|a, b| {
        let ak = (a.status != JoinStatus::Pending, std::cmp::Reverse(a.requested_at));
        let bk = (b.status != JoinStatus::Pending, std::cmp::Reverse(b.requested_at));
        ak.cmp(&bk)
    });
    let pending = joins.iter().filter(|j| j.status == JoinStatus::Pending).count();

    // Admission policy (the repair-path limits) — effective values from hub law,
    // or code defaults if unset. Setting them writes hub law (witnessed).
    let (repeat_limit, review_limit, src) = match s.law.read().await.as_ref() {
        Some(l) => {
            let in_law = l.ext.admission.as_ref()
                .map(|a| a.repeat_limit.is_some() || a.review_limit.is_some())
                .unwrap_or(false);
            (l.admission_repeat_limit(), l.admission_review_limit(),
             if in_law { "from hub law" } else { "default (not yet in law)" })
        }
        None => (
            hub_lib::law::DEFAULT_ADMISSION_REPEAT_LIMIT,
            hub_lib::law::DEFAULT_ADMISSION_REVIEW_LIMIT,
            "default (no law set)",
        ),
    };

    let mut body = String::from(OPERATOR_BANNER);
    body.push_str("<h2>Admission policy</h2>");
    body.push_str(&format!(
        "<p class=\"muted\">Retries before auto-block: <b>{repeat_limit}</b> · denial-reviews (appeals) \
         before terminal: <b>{review_limit}</b> &nbsp;<span class=\"pill\">{src}</span>. \
         Setting these <b>amends hub law</b> (witnessed, inspectable) — the single source of truth.</p>"
    ));
    body.push_str(&format!(
        "<div style=\"display:grid;grid-template-columns:max-content 1fr;gap:0.4rem 0.6rem;max-width:520px;align-items:center;\">\
         <label>Retries (repeat_limit)</label><input id=\"lim-repeat\" type=\"number\" min=\"1\" placeholder=\"{repeat_limit}\" style=\"padding:0.3rem;width:6rem;\">\
         <label>Appeals (review_limit)</label><input id=\"lim-review\" type=\"number\" min=\"0\" placeholder=\"{review_limit}\" style=\"padding:0.3rem;width:6rem;\">\
         <span></span><span><button onclick=\"setLimits()\">Write to hub law</button></span>\
         </div>"
    ));

    body.push_str("<h2 style=\"margin-top:1.5rem\">Admission queue</h2>");
    body.push_str(&format!(
        "<p class=\"muted\">{} pending · {} total. Law-<code>Allow</code> joins are auto-admitted and never queue; \
         only law-<code>Escalate</code> requests land here.</p>",
        pending, joins.len(),
    ));
    if joins.is_empty() {
        body.push_str("<p class=\"muted\">No join requests waiting.</p>");
    } else {
        body.push_str("<table><thead><tr><th>Status</th><th>Requested</th><th>LCT</th><th>Name</th>\
                       <th>Message</th><th>Pubkey</th><th>Actions</th></tr></thead><tbody>");
        for j in &joins {
            let status = match j.status {
                JoinStatus::Pending => "<span class=\"pill pill-warn\">pending</span>",
                JoinStatus::Approved => "<span class=\"pill\">approved</span>",
                JoinStatus::Denied => "<span class=\"pill\">denied</span>",
            };
            let actions = if j.status == JoinStatus::Pending {
                format!(
                    "<button onclick=\"admit('{id}')\">Admit</button>\
                     <button class=\"danger\" onclick=\"deny('{id}')\">Deny</button>",
                    id = j.request_id
                )
            } else {
                let by = j.resolved_by.map(|u| short(&u)).unwrap_or_default();
                let reason = j.reason.as_deref().map(|r| format!(" — {}", html_escape(r))).unwrap_or_default();
                format!("<span class=\"muted\">by {}{}</span>", by, reason)
            };
            let pk = &j.member_pubkey_hex[..j.member_pubkey_hex.len().min(12)];
            body.push_str(&format!(
                "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td><code>{}…</code></td><td>{}</td></tr>",
                status,
                j.requested_at.format("%Y-%m-%d %H:%M"),
                short(&j.member_lct_id),
                j.name.as_deref().map(html_escape).unwrap_or_default(),
                j.message.as_deref().map(html_escape).unwrap_or_default(),
                pk,
                actions,
            ));
        }
        body.push_str("</tbody></table>");
    }

    // ── Denial-review queue (the repair path) ──
    use hub_lib::state::ReviewStatus;
    let mut reviews: Vec<hub_lib::state::JoinReview> = projected.join_reviews.into_values().collect();
    reviews.sort_by(|a, b| {
        let ak = (a.status != ReviewStatus::Pending, std::cmp::Reverse(a.requested_at));
        let bk = (b.status != ReviewStatus::Pending, std::cmp::Reverse(b.requested_at));
        ak.cmp(&bk)
    });
    let rpending = reviews.iter().filter(|r| r.status == ReviewStatus::Pending).count();
    body.push_str("<h2 style=\"margin-top:1.5rem\">Denial reviews</h2>");
    body.push_str(&format!(
        "<p class=\"muted\">{} pending. A blocked applicant (≥ repeat_limit denials) pleads here; \
         granting clears their auto-block. &nbsp; \
         <button onclick=\"admissionReset()\">Admission-reset an LCT…</button></p>",
        rpending,
    ));
    if reviews.is_empty() {
        body.push_str("<p class=\"muted\">No reviews.</p>");
    } else {
        body.push_str("<table><thead><tr><th>Status</th><th>Requested</th><th>LCT</th>\
                       <th>Plea</th><th>Actions</th></tr></thead><tbody>");
        for r in &reviews {
            let status = match r.status {
                ReviewStatus::Pending => "<span class=\"pill pill-warn\">pending</span>",
                ReviewStatus::Granted => "<span class=\"pill\">granted</span>",
                ReviewStatus::Refused => "<span class=\"pill\">refused</span>",
            };
            let actions = if r.status == ReviewStatus::Pending {
                format!(
                    "<button onclick=\"grantReview('{id}')\">Grant</button>\
                     <button class=\"danger\" onclick=\"refuseReview('{id}')\">Refuse</button>",
                    id = r.review_id
                )
            } else {
                let by = r.resolved_by.map(|u| short(&u)).unwrap_or_default();
                let reason = r.reason.as_deref().map(|x| format!(" — {}", html_escape(x))).unwrap_or_default();
                format!("<span class=\"muted\">by {}{}</span>", by, reason)
            };
            body.push_str(&format!(
                "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>",
                status,
                r.requested_at.format("%Y-%m-%d %H:%M"),
                short(&r.member_lct_id),
                r.plea.as_deref().map(html_escape).unwrap_or_default(),
                actions,
            ));
        }
        body.push_str("</tbody></table>");
    }

    body.push_str(OPERATOR_JS);
    Ok(layout(&s, "Admission queue", &body))
}

pub(crate) async fn manage_page(State(s): State<RestState>) -> Result<Html<String>, AdminError> {
    let ledger = s.ledger.lock().await;
    let projected = HubState::project(&*ledger);
    drop(ledger);

    let mut body = String::from(OPERATOR_BANNER);

    // Proactive admission: the Sovereign adds a known member directly (e.g. a
    // fleet machine whose pubkey is already committed in fleet-identity), without
    // waiting for them to submit a join request. Live — no restart.
    body.push_str("<h2>Add a member</h2>");
    body.push_str(
        "<p class=\"muted\">Add a known member directly (Sovereign act). Takes effect live — no restart.</p>\
         <div style=\"display:grid;grid-template-columns:max-content 1fr;gap:0.4rem 0.6rem;max-width:760px;align-items:center;\">\
         <label>LCT id</label><input id=\"add-lct\" placeholder=\"uuid\" style=\"font-family:monospace;padding:0.3rem;\">\
         <label>Pubkey (64 hex)</label><input id=\"add-key\" placeholder=\"Ed25519 public key, hex\" style=\"font-family:monospace;padding:0.3rem;\">\
         <label>Name</label><input id=\"add-name\" placeholder=\"(optional)\" style=\"padding:0.3rem;\">\
         <span></span><span><button onclick=\"addMember()\">Add member</button></span>\
         </div>",
    );

    body.push_str("<h2 style=\"margin-top:1.5rem\">Members</h2>");
    body.push_str("<p class=\"muted\">Re-key (rotate a member's channel pubkey) and remove take effect live — no serve restart.</p>");
    if projected.members.is_empty() {
        body.push_str("<p class=\"muted\">No members.</p>");
    } else {
        body.push_str("<table><thead><tr><th>LCT</th><th>Name</th><th>Pubkey</th><th>Actions</th></tr></thead><tbody>");
        for m in projected.members.values() {
            let name = m.name.as_deref().unwrap_or("(unnamed)");
            let pk_pill = if projected.member_pubkeys.contains_key(&m.lct_id) {
                "<span class=\"pill\">pinned</span>"
            } else {
                "<span class=\"pill pill-warn\">none</span>"
            };
            body.push_str(&format!(
                "<tr><td><code>{}</code></td><td>{}</td><td>{}</td>\
                 <td><button onclick=\"rekey('{id}')\">Re-key</button>\
                 <button class=\"danger\" onclick=\"removeMember('{id}')\">Remove</button></td></tr>",
                m.lct_id,
                html_escape(name),
                pk_pill,
                id = m.lct_id,
            ));
        }
        body.push_str("</tbody></table>");
    }
    body.push_str(OPERATOR_JS);
    Ok(layout(&s, "Manage members", &body))
}

/// Operator-plane GUI pages (member roster, admit/deny + member management).
/// Mounted ONLY on the loopback operator listener, alongside the read-only
/// dashboard router.
pub fn operator_router(state: RestState) -> Router {
    Router::new()
        .route("/admin", get(overview))
        .route("/admin/members", get(members))
        .route("/admin/joins", get(joins_page))
        .route("/admin/manage", get(manage_page))
        // Moved off the public plane (review 2026-07-23): these render act
        // payloads / relationship data — roster, skills, profile values (all
        // tiers), pair metadata. Public transparency = law + roles + council;
        // history browsing is an operator affordance.
        .route("/admin/ledger", get(ledger_list))
        .route("/admin/ledger/:index", get(ledger_detail))
        .route("/admin/pairs", get(pairs))
        .with_state(state)
}

