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
//! - GET  /tools/query_chapter   → chapter identity + role-fill snapshot + recent events
//! - GET  /tools/list_members    → all current members (projected from ledger)
//! - GET  /tools/find_skill      → ?q=...  case-insensitive skill search
//! - POST /tools/add_member      → {member_lct_id, name?} — records MemberAdded
//! - POST /tools/assign_role     → {role, role_lct_id, member_lct_id} — records RoleAssigned
//! - POST /tools/record_event    → {event_kind, title, attended_by, held_at?}
//! - POST /tools/declare_skill   → {member_lct_id, skill} — records MemberSkillDeclared
//!
//! Authentication: MVP runs locally on a port the chapter operator
//! controls. Mutating endpoints sign ledger entries with the Sovereign
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
use web4_core::crypto::KeyPair;
use web4_core::role::SocietyRole;

use hub_lib::chapter::ChapterPaths;
use hub_lib::events::ChapterEvent;
use hub_lib::identity::IdentityFile;
use hub_lib::init::load_society;
use hub_lib::ledger::ChapterLedger;
use hub_lib::state::ChapterState;

#[derive(Clone)]
pub struct McpState {
    pub paths: ChapterPaths,
    pub sovereign_lct_id: Uuid,
    pub sovereign_keypair: Arc<KeyPair>,
    pub ledger: Arc<Mutex<ChapterLedger>>,
}

impl McpState {
    pub fn open(chapter_dir: PathBuf) -> Result<Self> {
        let paths = ChapterPaths::new(chapter_dir);
        let config = hub_lib::chapter::ChapterConfig::load(paths.config())?;
        let sovereign = IdentityFile::load(&config.sovereign.lct_path)?;
        let kp = sovereign.keypair()?;
        let ledger = ChapterLedger::open(paths.ledger())?;
        Ok(Self {
            paths,
            sovereign_lct_id: sovereign.lct.id,
            sovereign_keypair: Arc::new(kp),
            ledger: Arc::new(Mutex::new(ledger)),
        })
    }
}

pub fn router(state: McpState) -> Router {
    Router::new()
        .route("/tools", get(list_tools))
        .route("/tools/query_chapter", get(query_chapter))
        .route("/tools/list_members", get(list_members))
        .route("/tools/find_skill", get(find_skill))
        .route("/tools/add_member", post(add_member))
        .route("/tools/assign_role", post(assign_role))
        .route("/tools/record_event", post(record_event))
        .route("/tools/declare_skill", post(declare_skill))
        .with_state(state)
}

// ---------- error wrapper ----------

struct ApiError(anyhow::Error);

impl IntoResponse for ApiError {
    fn into_response(self) -> axum::response::Response {
        let body = serde_json::json!({"error": format!("{:#}", self.0)});
        (StatusCode::INTERNAL_SERVER_ERROR, Json(body)).into_response()
    }
}

impl<E: Into<anyhow::Error>> From<E> for ApiError {
    fn from(e: E) -> Self { ApiError(e.into()) }
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
        ToolDescriptor { name: "query_chapter",  method: "GET",  description: "Chapter identity + role-fill + recent events" },
        ToolDescriptor { name: "list_members",   method: "GET",  description: "Current chapter members" },
        ToolDescriptor { name: "find_skill",     method: "GET",  description: "Find members by skill (substring, case-insensitive). ?q=..." },
        ToolDescriptor { name: "add_member",     method: "POST", description: "Add a new member" },
        ToolDescriptor { name: "assign_role",    method: "POST", description: "Assign a role to a member" },
        ToolDescriptor { name: "record_event",   method: "POST", description: "Record a chapter event (demo night, workshop, etc.)" },
        ToolDescriptor { name: "declare_skill",  method: "POST", description: "Declare a skill for a member" },
    ])
}

// ---------- GET /tools/query_chapter ----------

#[derive(Serialize)]
struct QueryChapterResponse {
    chapter_name: String,
    founding_sovereign_lct_id: Option<Uuid>,
    charter_hash: Option<String>,
    member_count: usize,
    role_fill: HashMap<String, Uuid>,
    last_ledger_index: u64,
    head_hash: String,
}

async fn query_chapter(State(s): State<McpState>) -> Result<Json<QueryChapterResponse>, ApiError> {
    let ledger = s.ledger.lock().await;
    let state = ChapterState::project(&ledger);
    let society = load_society(s.paths.root.clone())?;
    let role_fill: HashMap<String, Uuid> = society.roles.iter()
        .map(|(k, v)| (k.clone(), v.filling_entity_lct_id))
        .collect();
    let member_count = state.member_count();
    Ok(Json(QueryChapterResponse {
        chapter_name: state.chapter_name,
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
    let state = ChapterState::project(&ledger);
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
    let state = ChapterState::project(&ledger);
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
    let event = ChapterEvent::MemberAdded {
        member_lct_id: req.member_lct_id,
        added_by: s.sovereign_lct_id,
        member_name: req.name,
    };
    append_with_sovereign(&s, event).await
}

// ---------- POST /tools/assign_role ----------

#[derive(Deserialize)]
struct AssignRoleRequest {
    role: SocietyRole,
    role_lct_id: Uuid,
    member_lct_id: Uuid,
}

async fn assign_role(
    State(s): State<McpState>,
    Json(req): Json<AssignRoleRequest>,
) -> Result<Json<EventRecordedResponse>, ApiError> {
    let event = ChapterEvent::RoleAssigned {
        role: req.role,
        role_lct_id: req.role_lct_id,
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
    let event = ChapterEvent::EventRecorded {
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
    let event = ChapterEvent::MemberSkillDeclared {
        member_lct_id: req.member_lct_id,
        skill: req.skill,
        declared_by: s.sovereign_lct_id,
    };
    append_with_sovereign(&s, event).await
}

// ---------- helper ----------

async fn append_with_sovereign(
    s: &McpState,
    event: ChapterEvent,
) -> Result<Json<EventRecordedResponse>, ApiError> {
    let mut ledger = s.ledger.lock().await;
    let entry = ledger.append(s.sovereign_lct_id, &s.sovereign_keypair, event)?;
    Ok(Json(EventRecordedResponse {
        entry_index: entry.index,
        entry_hash: entry.entry_hash.clone(),
        event_kind: entry.event.kind().to_string(),
    }))
}
