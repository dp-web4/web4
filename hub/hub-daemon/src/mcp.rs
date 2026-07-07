// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! MCP-shaped HTTP service exposing the chapter's I/O membrane.
//!
//! Sprint 3 scope: pragmatic HTTP+JSON endpoints per tool. Full MCP wire
//! protocol compliance (JSON-RPC framing, capability negotiation) is V2 —
//! the *tool surface* and the *signing discipline* are what matter for
//! getting a chapter usable now.
//!
//! Tools:
//! - GET  /tools                 → list available tools + descriptions
//! - GET  /tools/query_hub      → hub identity + role-fill snapshot + recent events
//! - GET  /tools/list_members    → all current members (projected from ledger)
//! - GET  /tools/find_skill      → ?q=...  case-insensitive skill search
//! - POST /tools/add_member      → {member_lct_id, name?} — records MemberAdded
//! - POST /tools/assign_role     → {role, role_lct_id, member_lct_id} — records RoleAssigned
//! - POST /tools/record_event    → {event_kind, title, attended_by, held_at?}
//! - POST /tools/declare_skill   → {member_lct_id, skill} — records MemberSkillDeclared
//!
//! Authentication: MVP runs locally on a port the chapter operator
//! controls. Act-recording endpoints sign ledger entries with the Sovereign
//! keypair loaded from config.toml. Per-client signed envelopes are V2.

use anyhow::Result;
use axum::{
    extract::{ConnectInfo, Query, State},
    http::StatusCode,
    response::{IntoResponse, Json},
    routing::{get, post},
    Router,
};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::net::SocketAddr;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::Mutex;
use uuid::Uuid;
use web4_core::role::SocietyRole;

use hub_lib::hub::HubPaths;
use hub_lib::events::HubEvent;
use hub_lib::law::{Decision, Law, R6Request};
use hub_lib::ledger::HubLedger;
use hub_lib::signer::{RemoteSigner, SignIntent, SwappableSigner};
use hub_lib::state::HubState;

#[derive(Clone)]
pub struct McpState {
    pub paths: HubPaths,
    pub hub_id: Uuid,
    pub hub_name: String,
    pub sovereign_lct_id: Uuid,
    /// Shared swappable signer (the SAME `Arc<SwappableSigner>` RestState holds).
    /// MCP handlers route ledger signing through it; runtime ignition swaps the
    /// LockedSigner → real one once, visible to both surfaces. Also lets McpState
    /// construct in a locked shell (no `load_auto` of an encrypted identity).
    pub signer: Arc<SwappableSigner>,
    pub ledger: Arc<Mutex<HubLedger>>,
    /// Hub law snapshot (loaded at open). PolicyEntity gate runs
    /// before each act-recording tool commits to the ledger.
    ///
    /// RwLock for hot-reload via the REST `/v1/admin/reload-law` endpoint;
    /// any subsequent MCP tool-call picks up the swapped-in law on its
    /// next .read() lock.
    pub law: Arc<tokio::sync::RwLock<Option<Law>>>,
    /// Shared derived store key (same Arc as RestState) — de-env'd runtime opens.
    pub store_key: Arc<tokio::sync::RwLock<Option<zeroize::Zeroizing<[u8; 32]>>>>,
}

impl McpState {
    /// Open with a caller-supplied shared law slot AND a shared in-memory
    /// ledger handle. `hub serve` uses this to give MCP, REST, and the admin
    /// dashboard a *single* `Arc<Mutex<HubLedger>>`, so an act recorded
    /// through any one surface is immediately visible to the others. Without
    /// this, each surface held its own ledger loaded at startup and only
    /// reconverged on daemon restart — live writes (e.g. a member declaring a
    /// skill via MCP) were invisible to the admin dashboard until then.
    /// `hub serve` builds RestState first, then constructs McpState sharing
    /// RestState's `signer`, `sovereign_lct_id`, and `store_key`. McpState no
    /// longer loads the identity itself — so it constructs cleanly in a locked
    /// shell, and a single runtime ignition (the signer swap) lights up both
    /// surfaces.
    pub async fn open_with_law_and_ledger(
        hub_dir: PathBuf,
        law: Arc<tokio::sync::RwLock<Option<Law>>>,
        ledger: Arc<Mutex<HubLedger>>,
        signer: Arc<SwappableSigner>,
        sovereign_lct_id: Uuid,
        store_key: Arc<tokio::sync::RwLock<Option<zeroize::Zeroizing<[u8; 32]>>>>,
        hub_id: Uuid,
        hub_name: String,
    ) -> Result<Self> {
        // No load_society here — it reads the (encrypted) store and would fail in a locked
        // shell. hub_id/hub_name come from RestState (from the ledger when ignited, or from
        // the clear public-identity.json when locked).
        Ok(Self {
            paths: HubPaths::new(hub_dir),
            hub_id,
            hub_name,
            sovereign_lct_id,
            signer,
            ledger,
            law,
            store_key,
        })
    }

    /// De-env'd runtime store open (mirrors `RestState::open_store`).
    pub async fn open_store(&self) -> Result<Box<dyn hub_lib::store::HubStore>> {
        let key = self.store_key.read().await.as_ref().map(|z| **z);
        hub_lib::store::open_hub_store_with_key(&self.paths.root, key)
    }
}

/// Read-only MCP tools — safe on the public listener.
pub fn read_router(state: McpState) -> Router {
    Router::new()
        .route("/tools", get(list_tools))
        .route("/tools/query_hub", get(query_hub))
        // Back-compat alias for pre-rename clients (was query_chapter).
        .route("/tools/query_chapter", get(query_hub))
        .route("/tools/list_members", get(list_members))
        .route("/tools/find_skill", get(find_skill))
        .with_state(state)
}

/// Sovereign-signing MCP **write** tools. P0 (residual review): these must live
/// ONLY on the loopback operator listener. A same-host reverse proxy / tunnel
/// forwarding public traffic to `127.0.0.1:<hub-port>` makes `ConnectInfo(peer)`
/// read as loopback, so the `require_loopback` guard alone is defeated behind a
/// proxy — exactly the public-deploy topology. Mounting them on the never-proxied
/// operator plane (`:8772`, 127.0.0.1-only) closes that hole; the loopback guard
/// stays as defense-in-depth.
pub fn write_router(state: McpState) -> Router {
    Router::new()
        .route("/tools/add_member", post(add_member))
        .route("/tools/assign_role", post(assign_role))
        .route("/tools/record_event", post(record_event))
        .route("/tools/declare_skill", post(declare_skill))
        .with_state(state)
}

// ---------- error wrapper ----------

/// Status-aware MCP error. Constructors set the right HTTP code so
/// PolicyEntity gating (deny → 403, escalate → 202) mirrors REST.
struct ApiError {
    status: StatusCode,
    message: String,
}

impl ApiError {
    fn internal(e: anyhow::Error) -> Self {
        Self { status: StatusCode::INTERNAL_SERVER_ERROR, message: format!("{:#}", e) }
    }
    fn forbidden(msg: impl Into<String>) -> Self {
        Self { status: StatusCode::FORBIDDEN, message: msg.into() }
    }
    fn accepted_escalation(msg: impl Into<String>) -> Self {
        Self { status: StatusCode::ACCEPTED, message: msg.into() }
    }
}

impl IntoResponse for ApiError {
    fn into_response(self) -> axum::response::Response {
        let body = serde_json::json!({"error": self.message});
        (self.status, Json(body)).into_response()
    }
}

impl<E: Into<anyhow::Error>> From<E> for ApiError {
    fn from(e: E) -> Self { ApiError::internal(e.into()) }
}

// ---------- GET /tools ----------

#[derive(Serialize)]
struct ToolDescriptor {
    name: &'static str,
    method: &'static str,
    description: &'static str,
}

async fn list_tools() -> Json<Vec<ToolDescriptor>> {
    Json(vec![
        ToolDescriptor { name: "query_hub",       method: "GET",  description: "Hub identity + role-fill + recent events" },
        ToolDescriptor { name: "list_members",   method: "GET",  description: "Current hub members" },
        ToolDescriptor { name: "find_skill",     method: "GET",  description: "Find members by skill (substring, case-insensitive). ?q=..." },
        // Write tools (add_member/assign_role/record_event/declare_skill) sign as
        // the Sovereign and are served ONLY on the loopback operator plane — not
        // advertised here (they 404 on the public listener by design).
    ])
}

// ---------- GET /tools/query_hub (alias: /tools/query_chapter) ----------

#[derive(Serialize)]
struct QueryHubResponse {
    hub_name: String,
    founding_sovereign_lct_id: Option<Uuid>,
    charter_hash: Option<String>,
    member_count: usize,
    role_fill: HashMap<String, Uuid>,
    last_ledger_index: u64,
    head_hash: String,
}

async fn query_hub(State(s): State<McpState>) -> Result<Json<QueryHubResponse>, ApiError> {
    let ledger = s.ledger.lock().await;
    let state = HubState::project(&ledger);
    // Read the society via the shared store handle so the in-memory `store_key`
    // (populated at runtime ignition, then the passphrase is dropped) decrypts
    // an at-rest vault. The free `load_society(root)` opens the store WITHOUT a
    // key and so fails post-ignition on an encrypted store — see the locked-shell
    // note on `open_with_law_and_ledger`. `assign_role` already uses this path.
    let store = s.open_store().await.map_err(ApiError::internal)?;
    let society = store.read_society().await
        .map_err(ApiError::internal)?
        .ok_or_else(|| ApiError::internal(anyhow::anyhow!("no society found in hub store")))?;
    let role_fill: HashMap<String, Uuid> = society.roles.iter()
        .map(|(k, v)| (k.clone(), v.filling_entity_lct_id))
        .collect();
    let member_count = state.member_count();
    Ok(Json(QueryHubResponse {
        hub_name: state.hub_name,
        founding_sovereign_lct_id: state.founding_sovereign_lct_id,
        charter_hash: state.charter_hash,
        member_count,
        role_fill,
        last_ledger_index: state.last_index,
        head_hash: ledger.head_hash().to_string(),
    }))
}

// ---------- GET /tools/list_members ----------

#[derive(Serialize)]
struct ListMembersResponse {
    members: Vec<hub_lib::state::Member>,
}

async fn list_members(State(s): State<McpState>) -> Result<Json<ListMembersResponse>, ApiError> {
    let ledger = s.ledger.lock().await;
    let state = HubState::project(&ledger);
    Ok(Json(ListMembersResponse {
        members: state.members.values().cloned().collect(),
    }))
}

// ---------- GET /tools/find_skill ----------

#[derive(Deserialize)]
struct FindSkillQuery { q: String }

#[derive(Serialize)]
struct FindSkillResponse {
    query: String,
    matches: Vec<hub_lib::state::Member>,
}

async fn find_skill(
    State(s): State<McpState>,
    Query(q): Query<FindSkillQuery>,
) -> Result<Json<FindSkillResponse>, ApiError> {
    let ledger = s.ledger.lock().await;
    let state = HubState::project(&ledger);
    let matches = state.find_skill(&q.q).into_iter().cloned().collect();
    Ok(Json(FindSkillResponse { query: q.q, matches }))
}

// ---------- POST /tools/add_member ----------

#[derive(Deserialize)]
struct AddMemberRequest {
    member_lct_id: Uuid,
    #[serde(default)]
    name: Option<String>,
}

#[derive(Serialize)]
struct EventRecordedResponse {
    entry_index: u64,
    entry_hash: String,
    event_kind: String,
}

async fn add_member(
    State(s): State<McpState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Json(req): Json<AddMemberRequest>,
) -> Result<Json<EventRecordedResponse>, ApiError> {
    require_loopback(&peer)?;
    let event = HubEvent::MemberAdded {
        member_lct_id: req.member_lct_id,
        added_by: s.sovereign_lct_id,
        member_name: req.name,
        member_pubkey_hex: None,
    };
    append_with_sovereign(&s, event).await
}

// ---------- POST /tools/assign_role ----------

#[derive(Deserialize)]
struct AssignRoleRequest {
    role: SocietyRole,
    /// Ignored if supplied — the role LCT is society-managed. Accepted for
    /// back-compat with pre-fix clients that sent it.
    #[serde(default)]
    #[allow(dead_code)]
    role_lct_id: Option<Uuid>,
    member_lct_id: Uuid,
}

async fn assign_role(
    State(s): State<McpState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Json(req): Json<AssignRoleRequest>,
) -> Result<Json<EventRecordedResponse>, ApiError> {
    require_loopback(&peer)?;
    // Mutate the IN-MEMORY society to learn the role LCT and build the event.
    // Nothing is persisted yet — `society` is a local copy; web4-core enforces
    // authority and owns the role LCT.
    let mut store = s.open_store().await
        .map_err(ApiError::internal)?;
    let mut society = store.read_society().await
        .map_err(ApiError::internal)?
        .ok_or_else(|| ApiError::internal(anyhow::anyhow!("society state missing")))?;
    let role_lct_id = society
        .assign_role(req.role.clone(), req.member_lct_id, s.sovereign_lct_id)
        .map_err(|e| ApiError::forbidden(format!("role assignment rejected: {e}")))?;
    let event = HubEvent::RoleAssigned {
        role: req.role,
        role_lct_id,
        assigned_to: req.member_lct_id,
        assigned_by: s.sovereign_lct_id,
    };
    // P0 (residual review): gate BEFORE persisting. A council/law rejection here
    // drops the in-memory `society` (never written), so society state can't run
    // ahead of the witnessed ledger. Persist + append only after the gate passes.
    check_governance(&s, &event).await?;
    store.write_society(&society).await.map_err(ApiError::internal)?;
    append_signed_event(&s, event).await
}

// ---------- POST /tools/record_event ----------

#[derive(Deserialize)]
struct RecordEventRequest {
    event_kind: String,
    title: String,
    #[serde(default)]
    attended_by: Vec<Uuid>,
    #[serde(default)]
    held_at: Option<DateTime<Utc>>,
}

async fn record_event(
    State(s): State<McpState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Json(req): Json<RecordEventRequest>,
) -> Result<Json<EventRecordedResponse>, ApiError> {
    require_loopback(&peer)?;
    let event = HubEvent::EventRecorded {
        event_kind: req.event_kind,
        title: req.title,
        attended_by: req.attended_by,
        recorded_by: s.sovereign_lct_id,
        held_at: req.held_at.unwrap_or_else(Utc::now),
    };
    append_with_sovereign(&s, event).await
}

// ---------- POST /tools/declare_skill ----------

#[derive(Deserialize)]
struct DeclareSkillRequest {
    member_lct_id: Uuid,
    skill: String,
}

async fn declare_skill(
    State(s): State<McpState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Json(req): Json<DeclareSkillRequest>,
) -> Result<Json<EventRecordedResponse>, ApiError> {
    require_loopback(&peer)?;
    let event = HubEvent::MemberSkillDeclared {
        member_lct_id: req.member_lct_id,
        skill: req.skill,
        declared_by: s.sovereign_lct_id,
    };
    append_with_sovereign(&s, event).await
}

// ---------- helper ----------

/// Operator-plane guard for the MCP *write* tools. They sign as the Sovereign,
/// so — unlike the read tools — they must never be reachable from the network
/// (H-001): the MCP router is merged into the public listener, so each write
/// tool rejects any non-loopback caller. Local reachability is still not full
/// authorization (an operator token is the tracked follow-up), but this closes
/// the remote Sovereign-signing bypass.
fn require_loopback(peer: &SocketAddr) -> Result<(), ApiError> {
    if peer.ip().is_loopback() {
        Ok(())
    } else {
        Err(ApiError::forbidden(
            "MCP write tools sign as the Sovereign and are local-only — reach them from the hub host",
        ))
    }
}

/// The council + law governance gate, **read-only** (no signing, no append).
///
/// P0 (residual review): a handler that performs pre-append side effects — e.g.
/// `assign_role` persisting society state — MUST call this *before* it persists,
/// then call [`append_signed_event`]. Otherwise a council/law rejection can leave
/// state ahead of the witnessed ledger. Handlers with no side effects can use the
/// combined [`append_with_sovereign`].
async fn check_governance(s: &McpState, event: &HubEvent) -> Result<(), ApiError> {
    // HUB-001 (parity with REST): refuse governed writes while the served law
    // diverges from the witnessed LawAmended head — the law we'd evaluate below
    // may be rolled-back/tampered. Override: HUB_ALLOW_LAW_MISMATCH=1.
    crate::rest::law_integrity_write_gate(&s.ledger, s.open_store().await.ok())
        .await
        .map_err(|message| ApiError { status: StatusCode::CONFLICT, message })?;

    // Council gate (parity with REST /events, V2-9 Phase 2): if a council
    // threshold of 2+ is active, a single-signer Sovereign commit is not
    // permitted — governed acts must flow through council propose/sign (H-002).
    let council_threshold_active = {
        let ledger = s.ledger.lock().await;
        matches!(
            hub_lib::state::HubState::project(&*ledger).council_threshold,
            Some((m, _)) if m >= 2
        )
    };
    if council_threshold_active {
        return Err(ApiError {
            status: StatusCode::CONFLICT,
            message: "council mode active (threshold >= 2-of-N): submit governed acts via \
                      POST /v1/hubs/{hub_id}/council/propose + /sign, not the MCP write tools"
                .to_string(),
        });
    }

    // PolicyEntity gate (V2-8 §4): if a hub law is loaded, evaluate before signing.
    let law_guard = s.law.read().await;
    if let Some(law) = law_guard.as_ref() {
        let req = R6Request {
            role: "sovereign".to_string(),
            action: event.kind().to_string(),
            payload: serde_yaml::to_value(event)
                .map_err(|e| ApiError::internal(anyhow::anyhow!("serializing event for R6: {}", e)))?,
            resource: Default::default(),
        };
        let outcome = law.evaluate_outcome(&req);
        match outcome.decision {
            Decision::Allow => { /* proceed */ }
            Decision::Warn => {
                tracing::warn!(
                    "act flagged by hub law (norm: {})",
                    outcome.winning_norm.as_deref().unwrap_or("?")
                );
            }
            Decision::Deny => {
                return Err(ApiError::forbidden(format!(
                    "act denied by hub law (norm: {})",
                    outcome.winning_norm.as_deref().unwrap_or("?")
                )));
            }
            Decision::Escalate => {
                return Err(ApiError::accepted_escalation(format!(
                    "act requires escalation to {} ({}); admin review queue is V2-16",
                    outcome.escalate_to.as_deref().unwrap_or("sovereign"),
                    outcome.winning_norm.as_deref().unwrap_or("escalation trigger"),
                )));
            }
        }
    }
    Ok(())
}

/// Sign `event` as the Sovereign and append it to the ledger. Assumes
/// [`check_governance`] has already passed (use [`append_with_sovereign`] unless
/// you've already preflighted around a side effect).
async fn append_signed_event(
    s: &McpState,
    event: HubEvent,
) -> Result<Json<EventRecordedResponse>, ApiError> {
    use chrono::Utc;
    use uuid::Uuid;

    // Build the unsigned entry under the lock, release for the (possibly
    // remote) sign, then re-acquire to commit. Same shape as REST.
    // HubLedger::append_signed detects stale state if a parallel
    // append landed in between (Step 3a stale-detection contract).
    let event_kind_str = event.kind().to_string();
    let event_value = serde_json::to_value(&event)
        .map_err(|e| ApiError::internal(anyhow::anyhow!("serializing event: {}", e)))?;
    let (unsigned, intent) = {
        let ledger = s.ledger.lock().await;
        let unsigned = ledger.build_entry(s.sovereign_lct_id, event, Utc::now())?;
        let intent = SignIntent {
            request_id: Uuid::new_v4(),
            hub_id: s.hub_id,
            hub_name: s.hub_name.clone(),
            actor_lct_id: s.sovereign_lct_id,
            ledger_index: unsigned.entry.index,
            event_kind: event_kind_str.clone(),
            event: event_value,
        };
        (unsigned, intent)
    };

    let signing_bytes = unsigned.signing_bytes.clone();
    let signature = s.signer
        .sign(s.sovereign_lct_id, &signing_bytes, &intent)
        .await
        .map_err(|e| ApiError::internal(anyhow::anyhow!("Sovereign signer: {}", e)))?;

    let mut ledger = s.ledger.lock().await;
    let entry = ledger.append_signed(unsigned, signature).await?;
    Ok(Json(EventRecordedResponse {
        entry_index: entry.index,
        entry_hash: entry.entry_hash.clone(),
        event_kind: entry.event.kind().to_string(),
    }))
}

/// Gate ([`check_governance`]) then append — for handlers with NO pre-append side
/// effects (add_member, record_event, declare_skill).
async fn append_with_sovereign(
    s: &McpState,
    event: HubEvent,
) -> Result<Json<EventRecordedResponse>, ApiError> {
    check_governance(s, &event).await?;
    append_signed_event(s, event).await
}

#[cfg(test)]
mod tests {
    use super::*;

    /// H-001 gate: the Sovereign-signing MCP write tools are merged into the
    /// public listener, so they must refuse any non-loopback caller. (Read tools
    /// stay open; only the write path carries Sovereign authority.)
    #[test]
    fn write_tools_require_loopback() {
        let remote: SocketAddr = "203.0.113.7:52000".parse().unwrap();
        let local4: SocketAddr = "127.0.0.1:52000".parse().unwrap();
        let local6: SocketAddr = "[::1]:52000".parse().unwrap();
        assert_eq!(
            require_loopback(&remote).unwrap_err().status,
            StatusCode::FORBIDDEN,
            "a remote caller of a Sovereign-signing write tool must be forbidden"
        );
        assert!(require_loopback(&local4).is_ok(), "loopback v4 is allowed");
        assert!(require_loopback(&local6).is_ok(), "loopback v6 is allowed");
    }
}
