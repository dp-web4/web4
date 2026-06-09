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
    extract::{Query, State},
    http::StatusCode,
    response::{IntoResponse, Json},
    routing::{get, post},
    Router,
};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::Mutex;
use uuid::Uuid;
use web4_core::role::SocietyRole;

use hub_lib::hub::{HubPaths, SovereignMode};
use hub_lib::events::HubEvent;
use hub_lib::identity::IdentityFile;
use hub_lib::init::load_society;
use hub_lib::law::{Decision, Law, R6Request};
use hub_lib::ledger::HubLedger;
use hub_lib::signer::{HestiaCallbackSigner, LocalKeypairSigner, RemoteSigner, SignIntent};
use hub_lib::state::HubState;

#[derive(Clone)]
pub struct McpState {
    pub paths: HubPaths,
    pub hub_id: Uuid,
    pub hub_name: String,
    pub sovereign_lct_id: Uuid,
    /// Signer abstraction — LocalKeypairSigner for MVP-compat chapters,
    /// HestiaCallbackSigner for Hestia-mode. MCP handlers route ledger
    /// signing through this trait, same shape as REST.
    pub signer: Arc<dyn RemoteSigner>,
    pub ledger: Arc<Mutex<HubLedger>>,
    /// Chapter law snapshot (loaded at open). PolicyEntity gate runs
    /// before each act-recording tool commits to the ledger.
    ///
    /// RwLock for hot-reload via the REST `/v1/admin/reload-law` endpoint;
    /// any subsequent MCP tool-call picks up the swapped-in law on its
    /// next .read() lock.
    pub law: Arc<tokio::sync::RwLock<Option<Law>>>,
}

impl McpState {
    /// Open with a caller-supplied shared law slot AND a shared in-memory
    /// ledger handle. `hub serve` uses this to give MCP, REST, and the admin
    /// dashboard a *single* `Arc<Mutex<HubLedger>>`, so an act recorded
    /// through any one surface is immediately visible to the others. Without
    /// this, each surface held its own ledger loaded at startup and only
    /// reconverged on daemon restart — live writes (e.g. a member declaring a
    /// skill via MCP) were invisible to the admin dashboard until then.
    pub async fn open_with_law_and_ledger(
        hub_dir: PathBuf,
        law: Arc<tokio::sync::RwLock<Option<Law>>>,
        ledger: Arc<Mutex<HubLedger>>,
    ) -> Result<Self> {
        let paths = HubPaths::new(hub_dir.clone());
        let config = hub_lib::hub::HubConfig::load(paths.config())?;
        let society = load_society(&hub_dir).await?;
        let (sovereign_lct_id, signer): (Uuid, Arc<dyn RemoteSigner>) = match config.sovereign.mode()? {
            SovereignMode::Local { lct_path } => {
                let sovereign = IdentityFile::load(&lct_path)?;
                let kp = sovereign.keypair()?;
                let signer = Arc::new(LocalKeypairSigner::new(sovereign.lct.id, kp));
                (sovereign.lct.id, signer)
            }
            SovereignMode::Hestia { callback_url, lct_id, .. } => {
                let signer = Arc::new(HestiaCallbackSigner::new(lct_id, callback_url)?);
                (lct_id, signer)
            }
        };
        Ok(Self {
            paths,
            hub_id: society.lct_id,
            hub_name: society.name,
            sovereign_lct_id,
            signer,
            ledger,
            law,
        })
    }
}

pub fn router(state: McpState) -> Router {
    Router::new()
        .route("/tools", get(list_tools))
        .route("/tools/query_hub", get(query_hub))
        // Back-compat alias for pre-rename clients (was query_chapter).
        .route("/tools/query_chapter", get(query_hub))
        .route("/tools/list_members", get(list_members))
        .route("/tools/find_skill", get(find_skill))
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
        ToolDescriptor { name: "add_member",     method: "POST", description: "Add a new member" },
        ToolDescriptor { name: "assign_role",    method: "POST", description: "Assign a role to a member" },
        ToolDescriptor { name: "record_event",   method: "POST", description: "Record a hub event (demo night, workshop, etc.)" },
        ToolDescriptor { name: "declare_skill",  method: "POST", description: "Declare a skill for a member" },
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
    let society = load_society(s.paths.root.clone()).await?;
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
    Json(req): Json<AddMemberRequest>,
) -> Result<Json<EventRecordedResponse>, ApiError> {
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
    Json(req): Json<AssignRoleRequest>,
) -> Result<Json<EventRecordedResponse>, ApiError> {
    // Update the persisted society role-fill (web4-core enforces authority and
    // owns the role LCT), then witness the act in the ledger with that LCT.
    // Without the society update the assignment never showed as filled.
    let mut store = hub_lib::store::open_hub_store(&s.paths.root)
        .map_err(ApiError::internal)?;
    let mut society = store.read_society().await
        .map_err(ApiError::internal)?
        .ok_or_else(|| ApiError::internal(anyhow::anyhow!("society state missing")))?;
    let role_lct_id = society
        .assign_role(req.role.clone(), req.member_lct_id, s.sovereign_lct_id)
        .map_err(|e| ApiError::forbidden(format!("role assignment rejected: {e}")))?;
    store.write_society(&society).await.map_err(ApiError::internal)?;

    let event = HubEvent::RoleAssigned {
        role: req.role,
        role_lct_id,
        assigned_to: req.member_lct_id,
        assigned_by: s.sovereign_lct_id,
    };
    append_with_sovereign(&s, event).await
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
    Json(req): Json<RecordEventRequest>,
) -> Result<Json<EventRecordedResponse>, ApiError> {
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
    Json(req): Json<DeclareSkillRequest>,
) -> Result<Json<EventRecordedResponse>, ApiError> {
    let event = HubEvent::MemberSkillDeclared {
        member_lct_id: req.member_lct_id,
        skill: req.skill,
        declared_by: s.sovereign_lct_id,
    };
    append_with_sovereign(&s, event).await
}

// ---------- helper ----------

async fn append_with_sovereign(
    s: &McpState,
    event: HubEvent,
) -> Result<Json<EventRecordedResponse>, ApiError> {
    use chrono::Utc;
    use uuid::Uuid;

    // PolicyEntity gate (V2-8 §4): if a chapter law is loaded, evaluate
    // before signing. MCP returns the same allow/deny/escalate decisions
    // as REST. For MCP we encode deny + escalate as ApiError (which becomes
    // a 500 with the error body for now — V2-16 admin UI is where escalation
    // queueing actually lands).
    let law_guard = s.law.read().await;
    if let Some(law) = law_guard.as_ref() {
        let req = R6Request {
            role: "sovereign".to_string(),
            action: event.kind().to_string(),
            payload: serde_yaml::to_value(&event)
                .map_err(|e| ApiError::internal(anyhow::anyhow!("serializing event for R6: {}", e)))?,
            resource: Default::default(),
        };
        let outcome = law.evaluate_outcome(&req);
        match outcome.decision {
            Decision::Allow => { /* proceed */ }
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
