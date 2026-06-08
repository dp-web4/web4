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
use hub_lib::init::load_society;
use hub_lib::state::HubState;

use crate::rest::RestState;

const STYLE: &str = r#"
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         max-width: 1100px; margin: 1.5rem auto; padding: 0 1rem; color: #222; }
  h1 { font-size: 1.4rem; border-bottom: 2px solid #444; padding-bottom: 0.3rem; }
  h2 { font-size: 1.1rem; margin-top: 1.5rem; color: #444; }
  nav { background: #f0f0f0; padding: 0.6rem 0.9rem; border-radius: 4px;
        margin-bottom: 1.2rem; }
  nav a { margin-right: 1rem; text-decoration: none; color: #0066cc; }
  nav a:hover { text-decoration: underline; }
  table { border-collapse: collapse; width: 100%; margin: 0.5rem 0 1rem; }
  th, td { text-align: left; padding: 0.35rem 0.6rem; border-bottom: 1px solid #ddd;
           font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 0.85rem; }
  th { background: #fafafa; font-weight: 600; }
  .muted { color: #888; font-style: italic; }
  .pill { display: inline-block; padding: 0.1rem 0.5rem; border-radius: 10px;
          font-size: 0.75rem; background: #e7eef7; color: #1a3a6b; }
  .pill-warn { background: #fbe6c2; color: #6b3a1a; }
  pre { background: #f7f7f7; padding: 0.8rem; border-radius: 4px;
        overflow-x: auto; font-size: 0.8rem; }
  .grid { display: grid; grid-template-columns: max-content 1fr; gap: 0.3rem 1rem; }
  .grid dt { font-weight: 600; color: #555; }
  .grid dd { margin: 0; font-family: ui-monospace, monospace; font-size: 0.9rem; }
  footer { margin-top: 2rem; padding-top: 0.6rem; border-top: 1px solid #ddd;
           color: #888; font-size: 0.8rem; }
</style>
"#;

fn layout(hub_name: &str, title: &str, body: &str) -> Html<String> {
    let nav = r#"<nav>
      <a href="/admin">Overview</a>
      <a href="/admin/members">Members</a>
      <a href="/admin/roles">Roles</a>
      <a href="/admin/ledger">Ledger</a>
      <a href="/admin/law">Law</a>
      <a href="/admin/council">Council</a>
    </nav>"#;
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

fn html_escape(s: &str) -> String {
    s.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
}

pub fn router(state: RestState) -> Router {
    Router::new()
        .route("/admin", get(overview))
        .route("/admin/members", get(members))
        .route("/admin/roles", get(roles))
        .route("/admin/ledger", get(ledger_list))
        .route("/admin/ledger/:index", get(ledger_detail))
        .route("/admin/law", get(law))
        .route("/admin/council", get(council))
        .with_state(state)
}

// ---------- error ----------

struct AdminError(StatusCode, String);

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

async fn overview(State(s): State<RestState>) -> Result<Html<String>, AdminError> {
    let ledger = s.ledger.lock().await;
    let projected = HubState::project(&*ledger);
    let entries = ledger.entries();
    let head_hash = ledger.head_hash().to_string();
    let backend = ledger.backend_kind().as_str();
    let ledger_len = entries.len();
    let last_20: Vec<_> = entries.iter().rev().take(20).cloned().collect();
    drop(ledger);

    let society = load_society(&s.paths.root).await?;
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

    Ok(layout(&s.hub_name, "Overview", &body))
}

async fn members(State(s): State<RestState>) -> Result<Html<String>, AdminError> {
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

    Ok(layout(&s.hub_name, "Members", &body))
}

async fn roles(State(s): State<RestState>) -> Result<Html<String>, AdminError> {
    let society = load_society(&s.paths.root).await?;
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

    Ok(layout(&s.hub_name, "Roles", &body))
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
    Ok(layout(&s.hub_name, "Ledger", &body))
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
    Ok(layout(&s.hub_name, &format!("Entry #{}", index), &body))
}

async fn council(State(s): State<RestState>) -> Result<Html<String>, AdminError> {
    use hub_lib::proposal::ProposalStatus;
    let ledger = s.ledger.lock().await;
    let projected = HubState::project(&*ledger);
    drop(ledger);
    let proposals = {
        let store = hub_lib::store::open_chapter_store(&s.paths.root)
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

    Ok(layout(&s.hub_name, "Council", &body))
}

async fn law(State(s): State<RestState>) -> Result<Html<String>, AdminError> {
    use hub_lib::store::open_chapter_store;
    let store = open_chapter_store(&s.paths.root)?;
    let yaml = store.read_law().await?;

    let mut body = String::from("<h2>Chapter law</h2>");
    match yaml {
        None => {
            body.push_str(
                "<p class=\"muted\">No law set. Open-admission applies by default.</p>\
                 <p>Set one via <code>hub set-law &lt;hub-dir&gt; law.yaml</code>, \
                 then <code>POST /v1/admin/reload-law</code>.</p>",
            );
        }
        Some(yaml) => {
            let law_guard = s.law.read().await;
            if let Some(l) = &*law_guard {
                body.push_str(&format!(
                    "<dl class=\"grid\"><dt>Version</dt><dd>{}</dd>\
                     <dt>Norms</dt><dd>{}</dd><dt>Procedures</dt><dd>{}</dd>\
                     <dt>Escalation triggers</dt><dd>{}</dd></dl>",
                    html_escape(&l.version),
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
    Ok(layout(&s.hub_name, "Law", &body))
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
    }
}

fn short(id: &uuid::Uuid) -> String {
    let s = id.to_string();
    format!("{}…", &s[..8])
}

