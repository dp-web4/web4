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
//! - GET  /tools/query_hub       → hub identity + role-fill snapshot + recent events
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
//!
//! P0 (public-release): /tools/list_members and /tools/find_skill are NOT
//! exposed on the public fleet plane. They live on the operator plane only,
//! behind operator auth, because a public hub bound to 0.0.0.0 must not let
//! anonymous internet clients enumerate members or search skills. Members can
//! still query these via the sealed REST channel or the operator plane.

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
        hub_lib::store::open_hub_store_with_key_async(&self.paths.root, key).await
    }
}

/// Public, read-only MCP tools — safe on the public fleet listener.
/// P0 (public-release): member/skill enumeration is NOT here; see
/// [`operator_read_router`] for those.
pub fn read_router(state: McpState) -> Router {
    Router::new()
        .route("/tools", get(list_tools))
        .route("/tools/query_hub", get(query_hub))
        // Back-compat alias for pre-rename clients (was query_chapter).
        .route("/tools/query_chapter", get(query_hub))
        .with_state(state)
}

/// Operator-plane read tools. These expose member rosters and skill graphs and
/// therefore live ONLY on the loopback operator listener, behind operator auth.
pub fn operator_read_router(state: McpState) -> Router {
    Router::new()
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
#[derive(Debug)]
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
    fn bad_request(msg: impl Into<String>) -> Self {
        Self { status: StatusCode::BAD_REQUEST, message: msg.into() }
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
        // Member/skill enumeration is operator-plane only (public-release P0).
        // They are not advertised on the public listener.
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
    members: Vec<hub_lib::state::MemberView>,
}

async fn list_members(State(s): State<McpState>) -> Result<Json<ListMembersResponse>, ApiError> {
    let ledger = s.ledger.lock().await;
    let state = HubState::project(&ledger);
    // Operator-plane callers see all fields (the operator listener is bound to
    // loopback and authenticated as the chapter operator).
    let members = state.members.values()
        .map(|m| m.to_view(None, true, true))
        .collect();
    Ok(Json(ListMembersResponse { members }))
}

// ---------- GET /tools/find_skill ----------

#[derive(Deserialize)]
struct FindSkillQuery { q: String }

#[derive(Serialize)]
struct FindSkillResponse {
    query: String,
    matches: Vec<hub_lib::state::MemberView>,
}

async fn find_skill(
    State(s): State<McpState>,
    Query(q): Query<FindSkillQuery>,
) -> Result<Json<FindSkillResponse>, ApiError> {
    const MAX_QUERY_LEN: usize = 256;
    if q.q.len() > MAX_QUERY_LEN {
        // 400, not 403: an over-long query is malformed input, not a
        // permissions failure (matches the rest.rs channel-side check).
        return Err(ApiError::bad_request(format!(
            "skill query too long (max {} chars)",
            MAX_QUERY_LEN
        )));
    }
    let ledger = s.ledger.lock().await;
    let state = HubState::project(&ledger);
    let matches = state.find_skill(&q.q)
        .into_iter()
        .map(|m| m.to_view(None, true, true))
        .collect();
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
    use crate::rest::channel_e2e_tests::{fresh_rest_state, witness_for_test};
    use crate::rest::RestState;

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

    // ---------- harness ----------

    /// An `McpState` over the SAME hub a `RestState` is serving — the sharing
    /// `hub serve` actually builds (one signer, one ledger, one law slot, one
    /// store key). Tests seed through REST's `witness_for_test` and then drive
    /// the MCP handlers, so what they observe is one hub, not two.
    async fn mcp_over(s: &RestState) -> McpState {
        McpState::open_with_law_and_ledger(
            s.paths.root.clone(),
            s.law.clone(),
            s.ledger.clone(),
            s.signer.clone(),
            s.sovereign_lct_id,
            s.store_key.clone(),
            s.hub_id,
            s.hub_name.clone(),
        )
        .await
        .expect("an McpState over an ignited local-mode hub")
    }

    fn loopback() -> ConnectInfo<SocketAddr> {
        ConnectInfo("127.0.0.1:52000".parse().unwrap())
    }

    /// The witnessed head — `(last index, head hash)`. The pair is the ledger's
    /// identity: an appended entry moves both, and a denied act must move neither.
    async fn head(s: &McpState) -> (u64, String) {
        let ledger = s.ledger.lock().await;
        (
            HubState::project(&ledger).last_index,
            ledger.head_hash().to_string(),
        )
    }

    /// Order-independent JSON rendering. `Society.roles` is a hash map, so two
    /// serializations of the SAME society differ in key order — comparing raw
    /// `to_string` output reports a difference that isn't one (and, worse,
    /// reports a difference where a real one is required).
    fn canonical(v: &serde_json::Value) -> String {
        match v {
            serde_json::Value::Object(m) => {
                let sorted: std::collections::BTreeMap<_, _> =
                    m.iter().map(|(k, v)| (k.as_str(), canonical(v))).collect();
                let body: Vec<String> =
                    sorted.iter().map(|(k, v)| format!("{k:?}:{v}")).collect();
                format!("{{{}}}", body.join(","))
            }
            serde_json::Value::Array(a) => {
                let body: Vec<String> = a.iter().map(canonical).collect();
                format!("[{}]", body.join(","))
            }
            other => other.to_string(),
        }
    }

    /// The persisted society, canonically rendered. `assign_role` mutates a
    /// local copy before the gate runs, so "was anything written" is the
    /// question that matters, and only the stored bytes answer it.
    async fn stored_society(s: &McpState) -> String {
        let store = s.open_store().await.expect("store opens");
        let society = store
            .read_society()
            .await
            .expect("society reads")
            .expect("an initialized hub has a society");
        canonical(&serde_json::to_value(&society).expect("society serializes"))
    }

    fn add_member_req() -> AddMemberRequest {
        AddMemberRequest { member_lct_id: Uuid::new_v4(), name: Some("Probe".into()) }
    }

    /// A law that pins one `decision` onto one event kind. `check_governance`
    /// builds its `R6Request` with `action = event.kind()`, so this is the
    /// narrowest possible selector for a single tool.
    fn law_for(action: &str, decision: &str) -> String {
        format!(
            "version: \"1.0.0\"\nnorms:\n  - id: MCP-TEST-NORM\n    \
             selector: r6.request.action\n    operator: \"==\"\n    \
             value: {action}\n    decision: {decision}\n    priority: 100\n"
        )
    }

    // ---------- append_signed_event: what the caller is told ----------

    /// The response is the receipt for the append, so its three fields must
    /// describe the entry that actually landed — not the entry we intended.
    /// Nothing checked that `entry_hash` is the new head, which is the one
    /// field a caller can independently verify the chain against.
    #[tokio::test]
    async fn a_write_tools_receipt_names_the_entry_that_actually_landed() {
        let (_tmp, rest) = fresh_rest_state(None).await;
        let s = mcp_over(&rest).await;
        let (before_index, before_hash) = head(&s).await;

        let req = add_member_req();
        let member = req.member_lct_id;
        let resp = add_member(State(s.clone()), loopback(), Json(req))
            .await
            .expect("an unlawed hub admits a member add")
            .0;

        assert_eq!(resp.entry_index, before_index + 1, "the receipt must name the appended index");
        assert_eq!(resp.event_kind, "member_added", "the receipt must name the event kind");
        let (after_index, after_hash) = head(&s).await;
        assert_eq!(after_index, resp.entry_index, "the ledger advanced to the receipted index");
        assert_ne!(after_hash, before_hash, "an append moves the head");
        assert_eq!(
            resp.entry_hash, after_hash,
            "entry_hash must be the new chain head — it is the caller's only handle on the chain"
        );

        // And the act is real: the projection sees the member.
        let ledger = s.ledger.lock().await;
        assert!(
            HubState::project(&ledger).members.contains_key(&member),
            "the appended MemberAdded must project into the member registry"
        );
    }

    // ---------- check_governance: the council gate ----------

    /// Seed an active council: one holder plus the Sovereign is N=2, then set
    /// M. Returns after both events are witnessed.
    async fn set_council(rest: &RestState, new_m: u32) {
        witness_for_test(rest, HubEvent::CouncilMemberAdded {
            member_lct_id: Uuid::new_v4(),
            member_pubkey_hex: "00".repeat(32),
            added_by: rest.sovereign_lct_id,
            member_name: Some("Co-Sovereign".into()),
        })
        .await;
        witness_for_test(rest, HubEvent::CouncilThresholdChanged {
            new_m,
            initiated_by: rest.sovereign_lct_id,
        })
        .await;
    }

    /// H-002: under an active 2-of-N council, a single-signer Sovereign commit
    /// is not permitted — and the MCP write tools sign as the Sovereign with no
    /// council aggregation at all. If this gate regresses, the MCP surface
    /// becomes the way to commit governed acts *around* council mode.
    #[tokio::test]
    async fn council_mode_refuses_the_mcp_write_tools_and_appends_nothing() {
        let (_tmp, rest) = fresh_rest_state(None).await;
        let s = mcp_over(&rest).await;
        set_council(&rest, 2).await;
        let before = head(&s).await;

        let err = add_member(State(s.clone()), loopback(), Json(add_member_req()))
            .await
            .err()
            .expect("council mode must refuse a single-signer Sovereign commit");
        assert_eq!(err.status, StatusCode::CONFLICT, "council refusal is a 409");
        assert!(
            err.message.contains("council/propose") || err.message.contains("council mode active"),
            "the refusal must point at the council path, got: {}",
            err.message
        );
        assert_eq!(before, head(&s).await, "a council-refused act must append nothing");
    }

    /// The boundary the gate is written on (`m >= 2`). A 1-of-N council is a
    /// council with no aggregation requirement, so the Sovereign acting alone
    /// IS the threshold — refusing here would brick single-holder hubs.
    #[tokio::test]
    async fn a_one_of_n_threshold_is_not_council_mode() {
        let (_tmp, rest) = fresh_rest_state(None).await;
        let s = mcp_over(&rest).await;
        set_council(&rest, 1).await;
        let (before_index, _) = head(&s).await;

        let resp = add_member(State(s.clone()), loopback(), Json(add_member_req()))
            .await
            .expect("M=1 is not council mode — the write must proceed")
            .0;
        assert_eq!(resp.entry_index, before_index + 1, "the act committed");
    }

    // ---------- check_governance: the PolicyEntity gate ----------

    /// Three law decisions, three distinct HTTP outcomes. `deny` and `escalate`
    /// are both refusals but they are NOT interchangeable — 202 means "queued
    /// for the Sovereign", 403 means "no". A regression that collapsed escalate
    /// into deny would silently turn a review queue into a wall, and both
    /// return an `Err`, so only the status distinguishes them.
    #[tokio::test]
    async fn law_deny_and_escalate_refuse_with_distinct_statuses_and_append_nothing() {
        for (decision, expected) in
            [("deny", StatusCode::FORBIDDEN), ("escalate", StatusCode::ACCEPTED)]
        {
            let (_tmp, rest) = fresh_rest_state(Some(&law_for("member_added", decision))).await;
            let s = mcp_over(&rest).await;
            let before = head(&s).await;

            let err = add_member(State(s.clone()), loopback(), Json(add_member_req()))
                .await
                .err()
                .unwrap_or_else(|| panic!("law decision `{decision}` must refuse the act"));
            assert_eq!(err.status, expected, "law decision `{decision}` mapped to the wrong status");
            assert_eq!(
                before,
                head(&s).await,
                "a `{decision}` act must leave the ledger bit-identical"
            );
        }
    }

    /// `warn` is the third decision and the one that is easy to get wrong in the
    /// other direction: it logs and **proceeds**. Pinning it stops a
    /// fail-closed sweep from quietly reclassifying warn as deny.
    #[tokio::test]
    async fn law_warn_proceeds_to_the_ledger() {
        let (_tmp, rest) = fresh_rest_state(Some(&law_for("member_added", "warn"))).await;
        let s = mcp_over(&rest).await;
        let (before_index, _) = head(&s).await;

        let resp = add_member(State(s.clone()), loopback(), Json(add_member_req()))
            .await
            .expect("`warn` flags the act, it does not block it")
            .0;
        assert_eq!(resp.entry_index, before_index + 1, "a warned act still commits");
    }

    /// The law is selected on `event.kind()`, so a norm aimed at one tool must
    /// not catch another. Without this, a law test passes just as well against a
    /// gate that denies everything.
    #[tokio::test]
    async fn a_norm_aimed_at_one_tool_does_not_catch_another() {
        let (_tmp, rest) = fresh_rest_state(Some(&law_for("role_assigned", "deny"))).await;
        let s = mcp_over(&rest).await;
        let (before_index, _) = head(&s).await;

        add_member(State(s.clone()), loopback(), Json(add_member_req()))
            .await
            .expect("a role_assigned norm must not deny member_added");
        assert_eq!(head(&s).await.0, before_index + 1, "the unrelated act committed");
    }

    // ---------- check_governance: the law-integrity gate (HUB-001 parity) ----------

    /// `check_governance` opens with `law_integrity_write_gate` and the module
    /// claims REST parity for it. Nothing verified that at this surface. A
    /// mismatch is the rollback/tamper signal: the served law is not the law the
    /// ledger witnessed, so the gate we are about to evaluate cannot be trusted.
    #[tokio::test]
    async fn a_law_that_diverges_from_the_witnessed_head_refuses_mcp_writes() {
        let served = law_for("member_added", "allow");
        let (_tmp, rest) = fresh_rest_state(Some(&served)).await;
        let s = mcp_over(&rest).await;

        // Serve one law, witness a different one's hash: a positive mismatch.
        // (LawAmended is exempt from the integrity check — it is the recovery path.)
        {
            let mut store = rest.open_store().await.expect("store opens");
            store.write_law(&served).await.expect("law persists");
        }
        witness_for_test(&rest, HubEvent::LawAmended {
            new_law_sha256: hub_lib::law::Law::sha256_hex_of(&law_for("member_added", "deny")),
            amended_by: rest.sovereign_lct_id,
            version: "1.0.0".into(),
            diff_summary: Some("a head the store does not match".into()),
        })
        .await;
        let before = head(&s).await;

        let err = add_member(State(s.clone()), loopback(), Json(add_member_req()))
            .await
            .err()
            .expect("a law-integrity mismatch must refuse governed writes");
        assert_eq!(err.status, StatusCode::CONFLICT, "a law-integrity refusal is a 409");
        assert!(
            err.message.contains("law integrity mismatch"),
            "the refusal must name the mismatch, got: {}",
            err.message
        );
        assert_eq!(before, head(&s).await, "a mismatch-refused act must append nothing");
    }

    // ---------- ordering: the gate must dominate the side effect ----------

    /// RWOA's **O** clause for the one MCP handler that has a pre-append side
    /// effect. `assign_role` mutates an in-memory society, then gates, then
    /// persists — and the ordering of those last two lines is the whole
    /// guarantee. Swap them and society state runs ahead of the witnessed
    /// ledger: the role reads as filled while no entry attests it, and nothing
    /// in the test suite noticed. A denied act must leave the store
    /// bit-identical.
    #[tokio::test]
    async fn a_denied_role_assignment_leaves_the_persisted_society_bit_identical() {
        let (_tmp, rest) = fresh_rest_state(Some(&law_for("role_assigned", "deny"))).await;
        let s = mcp_over(&rest).await;
        let before_society = stored_society(&s).await;
        let before_head = head(&s).await;

        let err = assign_role(
            State(s.clone()),
            loopback(),
            Json(AssignRoleRequest {
                role: SocietyRole::Archivist,
                role_lct_id: None,
                member_lct_id: Uuid::new_v4(),
            }),
        )
        .await
        .err()
        .expect("the law denies role_assigned");
        assert_eq!(err.status, StatusCode::FORBIDDEN, "a law denial is a 403");

        assert_eq!(
            before_society,
            stored_society(&s).await,
            "the denied assignment was persisted — the governance gate ran AFTER write_society"
        );
        assert_eq!(before_head, head(&s).await, "a denied assignment must append nothing");
    }

    /// The other half of the ordering claim: on the allow path the society
    /// write and the ledger append BOTH happen, and the role LCT in the event is
    /// the one the society recorded. Without this, "leaves state bit-identical"
    /// is satisfiable by a handler that never persists anything.
    #[tokio::test]
    async fn an_allowed_role_assignment_persists_the_society_and_witnesses_the_same_role_lct() {
        let (_tmp, rest) = fresh_rest_state(None).await;
        let s = mcp_over(&rest).await;
        let before_society = stored_society(&s).await;
        let member = Uuid::new_v4();

        let resp = assign_role(
            State(s.clone()),
            loopback(),
            Json(AssignRoleRequest {
                role: SocietyRole::Archivist,
                role_lct_id: None,
                member_lct_id: member,
            }),
        )
        .await
        .expect("an unlawed hub allows the Sovereign to assign a role")
        .0;
        assert_eq!(resp.event_kind, "role_assigned");
        assert_ne!(
            before_society,
            stored_society(&s).await,
            "an allowed assignment must be persisted"
        );

        // The witnessed event's role_lct_id is the society's, not a fresh one.
        let ledger = s.ledger.lock().await;
        let entry = ledger
            .entries()
            .iter()
            .rev()
            .find(|e| matches!(e.event, HubEvent::RoleAssigned { .. }))
            .expect("a RoleAssigned entry was appended");
        let HubEvent::RoleAssigned { role_lct_id, assigned_to, .. } = &entry.event else {
            unreachable!()
        };
        assert_eq!(*assigned_to, member, "the event names the assignee");
        let store = s.open_store().await.unwrap();
        let society = store.read_society().await.unwrap().unwrap();
        assert!(
            society.roles.values().any(|r| r.role_lct_id == *role_lct_id
                && r.filling_entity_lct_id == member),
            "the witnessed role LCT must be the one the society persisted, not a fresh UUID"
        );
    }

    // ---------- find_skill input bound ----------

    /// An over-long skill query is malformed input (400), not a permissions
    /// failure (403) — the distinction `find_skill` documents against the
    /// channel-side check in rest.rs. Boundary: exactly MAX is accepted.
    #[tokio::test]
    async fn an_over_long_skill_query_is_a_400_and_the_bound_itself_is_allowed() {
        let (_tmp, rest) = fresh_rest_state(None).await;
        let s = mcp_over(&rest).await;

        let at_bound = "r".repeat(256);
        assert!(
            find_skill(State(s.clone()), Query(FindSkillQuery { q: at_bound })).await.is_ok(),
            "a query at exactly the bound is accepted"
        );
        let over = find_skill(State(s.clone()), Query(FindSkillQuery { q: "r".repeat(257) }))
            .await
            .err()
            .expect("one char over the bound is rejected");
        assert_eq!(
            over.status,
            StatusCode::BAD_REQUEST,
            "an over-long query is malformed input, not a permissions failure"
        );
    }
}
