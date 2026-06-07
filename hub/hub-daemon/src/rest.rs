// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! V2 REST surface for external clients (Hestia, peer hubs).
//!
//! Per architecture commitment #8: every consequential request arrives
//! as a [`SignedEnvelope`] (from hub_lib::envelope) with a server-issued
//! nonce. The hub verifies signature + nonce, then routes the payload to
//! a handler. Private keys never reach the hub.
//!
//! Spec reference: see `shared-context/forum/cbp-to-legion-hub-api-spec-for-h2-h3-2026-06-07.md`
//!
//! ## V2-7 Step 2 scope (this module)
//!
//! - `POST /v1/auth/challenge`  — mint a single-use nonce
//! - `POST /v1/chapters/{chapter_id}/events` — accept a SignedEnvelope and
//!   route its payload (limited action set) to the ledger
//! - `GET  /v1/chapters/{chapter_id}/state` — public state (no auth in
//!   this slice; need-to-know filtering arrives with V2-8 law interpreter)
//!
//! Limitations honest about today:
//! - PublicKeyResolver only knows the Sovereign LCT. Members can't sign
//!   envelopes yet — their public keys aren't registered with the hub
//!   until V2-12 (member self-add) closes that gap.
//! - The `Sovereign-sign-callback` (hub → Hestia direction) is V2-7
//!   Step 3, not here.
//! - Authority/need-to-know on reads is V2-8.

use anyhow::Result;
use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::{IntoResponse, Json},
    routing::{get, post},
    Router,
};
use chrono::Utc;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::Mutex;
use uuid::Uuid;
use web4_core::crypto::KeyPair;

use hub_lib::chapter::ChapterPaths;
use hub_lib::envelope::{verify_envelope, Challenge, MapResolver, NonceStore, SignedEnvelope, VerifyError};
use hub_lib::events::ChapterEvent;
use hub_lib::identity::IdentityFile;
use hub_lib::init::load_society;
use hub_lib::ledger::ChapterLedger;
use hub_lib::state::ChapterState;

#[derive(Clone)]
pub struct RestState {
    pub paths: ChapterPaths,
    pub chapter_lct_id: Uuid,
    pub sovereign_lct_id: Uuid,
    /// Sovereign keypair is held for V2-7 Step 2 only — used to co-sign
    /// the ledger entry AFTER a SignedEnvelope-authenticated action.
    /// V2-7 Step 3 inverts this (Hestia signs; hub never sees the key)
    /// and this field goes away. Acknowledged-debt scaffolding.
    pub sovereign_keypair: Arc<KeyPair>,
    pub ledger: Arc<Mutex<ChapterLedger>>,
    pub nonces: Arc<NonceStore>,
    pub resolver: Arc<MapResolver>,
}

impl RestState {
    pub fn open(chapter_dir: PathBuf) -> Result<Self> {
        let paths = ChapterPaths::new(chapter_dir.clone());
        let config = hub_lib::chapter::ChapterConfig::load(paths.config())?;
        let sovereign = IdentityFile::load(&config.sovereign.lct_path)?;
        let kp = sovereign.keypair()?;
        let store = hub_lib::store::open_chapter_store(&chapter_dir)?;
        let ledger = ChapterLedger::open(store)?;
        let society = load_society(&chapter_dir)?;

        // V2-7 Step 2 resolver: just the Sovereign LCT. Members can't
        // sign envelopes yet (their pubkeys arrive with V2-12 join).
        let mut resolver = MapResolver::new();
        resolver.insert(sovereign.lct.clone());

        Ok(Self {
            paths,
            chapter_lct_id: society.lct_id,
            sovereign_lct_id: sovereign.lct.id,
            sovereign_keypair: Arc::new(kp),
            ledger: Arc::new(Mutex::new(ledger)),
            nonces: Arc::new(NonceStore::new()),
            resolver: Arc::new(resolver),
        })
    }
}

pub fn router(state: RestState) -> Router {
    Router::new()
        .route("/v1/auth/challenge", post(issue_challenge))
        .route("/v1/chapters/:chapter_id/events", post(submit_event))
        .route("/v1/chapters/:chapter_id/state", get(read_state))
        .with_state(state)
}

// ---------- error wrapper ----------

struct ApiError {
    status: StatusCode,
    message: String,
}

impl ApiError {
    fn bad_request(msg: impl Into<String>) -> Self {
        Self { status: StatusCode::BAD_REQUEST, message: msg.into() }
    }
    fn unauthorized(msg: impl Into<String>) -> Self {
        Self { status: StatusCode::UNAUTHORIZED, message: msg.into() }
    }
    fn not_found(msg: impl Into<String>) -> Self {
        Self { status: StatusCode::NOT_FOUND, message: msg.into() }
    }
    fn internal(e: anyhow::Error) -> Self {
        Self { status: StatusCode::INTERNAL_SERVER_ERROR, message: format!("{:#}", e) }
    }
}

impl IntoResponse for ApiError {
    fn into_response(self) -> axum::response::Response {
        let body = serde_json::json!({"error": self.message});
        (self.status, Json(body)).into_response()
    }
}

impl From<VerifyError> for ApiError {
    fn from(e: VerifyError) -> Self {
        // Map verifier outcomes to HTTP status codes
        match e {
            VerifyError::UnknownSigner(_) => ApiError::unauthorized(e.to_string()),
            VerifyError::UnknownNonce(_) => ApiError::unauthorized(e.to_string()),
            VerifyError::ExpiredNonce(_) => ApiError::unauthorized(e.to_string()),
            VerifyError::NonceLctMismatch(_) => ApiError::unauthorized(e.to_string()),
            VerifyError::BadSignature(_) => ApiError::unauthorized(e.to_string()),
            VerifyError::UnsupportedProof => ApiError::bad_request(e.to_string()),
            VerifyError::Internal(err) => ApiError::internal(err),
        }
    }
}

// ---------- POST /v1/auth/challenge ----------

#[derive(Deserialize)]
struct ChallengeRequest {
    for_lct_id: Uuid,
}

async fn issue_challenge(
    State(s): State<RestState>,
    Json(req): Json<ChallengeRequest>,
) -> Result<Json<Challenge>, ApiError> {
    // Cheap maintenance: drop expired before issuing a new one.
    s.nonces.prune_expired(Utc::now());
    let challenge = s.nonces.issue(req.for_lct_id, Utc::now());
    Ok(Json(challenge))
}

// ---------- POST /v1/chapters/{chapter_id}/events ----------

/// The action types V2-7 Step 2 routes from a verified envelope.
/// Mirrors a subset of ChapterEvent; extends as more flows land.
#[derive(Deserialize)]
#[serde(tag = "action", rename_all = "snake_case")]
enum EnvelopeAction {
    AddMember {
        member_lct_id: Uuid,
        #[serde(default)]
        name: Option<String>,
    },
    DeclareSkill {
        member_lct_id: Uuid,
        skill: String,
    },
}

#[derive(Serialize)]
struct EventAccepted {
    entry_index: u64,
    entry_hash: String,
    event_kind: String,
    signer_lct_id: Uuid,
}

async fn submit_event(
    State(s): State<RestState>,
    Path(chapter_id): Path<Uuid>,
    Json(envelope): Json<SignedEnvelope>,
) -> Result<Json<EventAccepted>, ApiError> {
    // 1. Confirm caller addressed the right chapter (defense in depth —
    // a SignedEnvelope verified against THIS hub couldn't be valid for
    // another anyway, but explicit check catches misrouted requests).
    if chapter_id != s.chapter_lct_id {
        return Err(ApiError::not_found(format!(
            "chapter id {} does not match this hub's chapter {}",
            chapter_id, s.chapter_lct_id
        )));
    }

    // 2. Authority check: envelope verifies (signer known, nonce valid,
    // payload not tampered).
    let _redeemed = verify_envelope(&envelope, &s.nonces, s.resolver.as_ref(), Utc::now())?;

    // 3. V2-7 Step 2 authorization: only Sovereign can submit signed
    // envelopes. Member-signing arrives with V2-12. PolicyEntity gating
    // arrives with V2-8.
    if envelope.signer_lct_id != s.sovereign_lct_id {
        return Err(ApiError::unauthorized(format!(
            "V2-7 Step 2: only Sovereign LCT may submit signed envelopes; got {}",
            envelope.signer_lct_id
        )));
    }

    // 4. Parse the action.
    let action: EnvelopeAction = serde_json::from_value(envelope.payload.clone())
        .map_err(|e| ApiError::bad_request(format!("payload not a known action: {}", e)))?;

    // 5. Translate to ChapterEvent + apply.
    // The ledger entry is signed by the Sovereign keypair, same as the
    // MCP path. V2-7 Step 3 inverts this so the envelope's signature IS
    // the actor signature on the ledger entry — eliminating the hub's
    // need to hold the keypair.
    let event = match action {
        EnvelopeAction::AddMember { member_lct_id, name } => ChapterEvent::MemberAdded {
            member_lct_id,
            added_by: envelope.signer_lct_id,
            member_name: name,
        },
        EnvelopeAction::DeclareSkill { member_lct_id, skill } => ChapterEvent::MemberSkillDeclared {
            member_lct_id,
            skill,
            declared_by: envelope.signer_lct_id,
        },
    };

    let mut ledger = s.ledger.lock().await;
    let entry = ledger.append(s.sovereign_lct_id, &s.sovereign_keypair, event)
        .map_err(ApiError::internal)?;

    Ok(Json(EventAccepted {
        entry_index: entry.index,
        entry_hash: entry.entry_hash.clone(),
        event_kind: entry.event.kind().to_string(),
        signer_lct_id: envelope.signer_lct_id,
    }))
}

// ---------- GET /v1/chapters/{chapter_id}/state ----------

#[derive(Serialize)]
struct PublicState {
    chapter_id: Uuid,
    chapter_name: String,
    member_count: usize,
    ledger_entries: u64,
    head_hash: String,
    /// V2-7 Step 2: public roles list (which roles are filled).
    /// Filler identities are public-by-design within the chapter.
    /// V2-8 will gate this on need-to-know per chapter law.
    filled_roles: Vec<RoleSnapshot>,
}

#[derive(Serialize)]
struct RoleSnapshot {
    role: String,
    role_lct_id: Uuid,
    filled_by_lct_id: Uuid,
}

async fn read_state(
    State(s): State<RestState>,
    Path(chapter_id): Path<Uuid>,
) -> Result<Json<PublicState>, ApiError> {
    if chapter_id != s.chapter_lct_id {
        return Err(ApiError::not_found(format!(
            "chapter id {} does not match this hub's chapter {}",
            chapter_id, s.chapter_lct_id
        )));
    }
    let ledger = s.ledger.lock().await;
    let state = ChapterState::project(&ledger);
    let society = load_society(s.paths.root.clone())
        .map_err(ApiError::internal)?;
    let filled_roles: Vec<RoleSnapshot> = society.roles.iter()
        .map(|(name, ra)| RoleSnapshot {
            role: name.clone(),
            role_lct_id: ra.role_lct_id,
            filled_by_lct_id: ra.filling_entity_lct_id,
        })
        .collect();
    let member_count = state.member_count();
    let ledger_entries = ledger.len() as u64;
    let head_hash = ledger.head_hash().to_string();
    Ok(Json(PublicState {
        chapter_id: s.chapter_lct_id,
        chapter_name: state.chapter_name,
        member_count,
        ledger_entries,
        head_hash,
        filled_roles,
    }))
}
