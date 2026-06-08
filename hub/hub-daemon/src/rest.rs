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
//! - `POST /v1/hubs/{hub_id}/events` — accept a SignedEnvelope and
//!   route its payload (limited action set) to the ledger
//! - `GET  /v1/hubs/{hub_id}/state` — public state (no auth in
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

use hub_lib::hub::{HubPaths, SovereignMode};
use hub_lib::envelope::{verify_envelope, Challenge, MapResolver, NonceStore, SignedEnvelope, VerifyError};
use hub_lib::events::HubEvent;
use hub_lib::identity::IdentityFile;
use hub_lib::init::load_society;
use hub_lib::law::{Decision, Law, R6Request};
use hub_lib::ledger::HubLedger;
use hub_lib::signer::{HestiaCallbackSigner, LocalKeypairSigner, RemoteSigner, SignIntent};
use hub_lib::state::HubState;

#[derive(Clone)]
pub struct RestState {
    pub paths: HubPaths,
    pub hub_id: Uuid,
    pub hub_name: String,
    pub sovereign_lct_id: Uuid,
    /// The signer abstraction. LocalKeypairSigner for MVP-compat chapters
    /// (keypair in process); HestiaCallbackSigner for Hestia-mode
    /// chapters (hub holds NO keys; signs via Hestia HTTP callback).
    pub signer: Arc<dyn RemoteSigner>,
    pub ledger: Arc<Mutex<HubLedger>>,
    pub nonces: Arc<NonceStore>,
    pub resolver: Arc<MapResolver>,
    /// Chapter law, loaded at open() time. None = no law set (all
    /// envelope-authenticated acts allowed). When present, the PolicyEntity
    /// gate runs before each act is committed to the ledger.
    ///
    /// Wrapped in RwLock so set-law (or `POST /v1/hubs/{id}/law`)
    /// can hot-reload without restarting hub serve.
    pub law: Arc<tokio::sync::RwLock<Option<Law>>>,
}

impl RestState {
    /// Open with the caller-supplied shared law slot. Used by `hub serve`
    /// so REST + MCP evaluate against the same snapshot + share reload.
    pub fn open_with_law(
        hub_dir: PathBuf,
        law: Arc<tokio::sync::RwLock<Option<Law>>>,
    ) -> Result<Self> {
        let paths = HubPaths::new(hub_dir.clone());
        let config = hub_lib::hub::HubConfig::load(paths.config())?;
        let store = hub_lib::store::open_chapter_store(&hub_dir)?;
        let ledger = HubLedger::open(store)?;
        let society = load_society(&hub_dir)?;

        // Build the right Sovereign LCT + signer for the chapter's mode.
        let (sovereign_lct, signer): (_, Arc<dyn RemoteSigner>) = match config.sovereign.mode()? {
            SovereignMode::Local { lct_path } => {
                let sovereign = IdentityFile::load(&lct_path)?;
                let kp = sovereign.keypair()?;
                let signer = Arc::new(LocalKeypairSigner::new(sovereign.lct.id, kp));
                (sovereign.lct, signer as Arc<dyn RemoteSigner>)
            }
            SovereignMode::Hestia { callback_url, lct_id, pubkey_hex } => {
                let lct = hub_lib::hub::hestia_sovereign_lct(lct_id, &pubkey_hex)?;
                let signer = Arc::new(HestiaCallbackSigner::new(lct_id, callback_url)?);
                (lct, signer as Arc<dyn RemoteSigner>)
            }
        };

        // V2-7 Step 2 resolver: just the Sovereign LCT. Members can't
        // sign envelopes yet (their pubkeys arrive with V2-12 join).
        let mut resolver = MapResolver::new();
        resolver.insert(sovereign_lct.clone());

        Ok(Self {
            paths,
            hub_id: society.lct_id,
            hub_name: society.name.clone(),
            sovereign_lct_id: sovereign_lct.id,
            signer,
            ledger: Arc::new(Mutex::new(ledger)),
            nonces: Arc::new(NonceStore::new()),
            resolver: Arc::new(resolver),
            law,
        })
    }

    /// Backward-compat: load the chapter's law from storage into a
    /// fresh slot. Standalone callers that don't need REST/MCP shared
    /// reload can use this.
    pub fn open(hub_dir: PathBuf) -> Result<Self> {
        let store = hub_lib::store::open_chapter_store(&hub_dir)?;
        let law: Option<Law> = match store.read_law()? {
            Some(yaml) => Some(Law::parse_and_validate(&yaml)
                .map_err(|e| anyhow::anyhow!("loading chapter law: {}", e))?),
            None => None,
        };
        Self::open_with_law(hub_dir, Arc::new(tokio::sync::RwLock::new(law)))
    }

    /// Re-read the chapter law from storage and swap it into the
    /// in-memory snapshot. Returns Ok with the version (or "none" if
    /// no law set). Used by the `/v1/admin/reload-law` endpoint so
    /// operators can `hub set-law` then `curl reload-law` without
    /// restarting hub serve.
    pub async fn reload_law(&self) -> anyhow::Result<String> {
        use anyhow::Context;
        let store = hub_lib::store::open_chapter_store(&self.paths.root)
            .context("opening store for law reload")?;
        let new_law: Option<Law> = match store.read_law()? {
            Some(ref yaml) => Some(Law::parse_and_validate(yaml)
                .map_err(|e| anyhow::anyhow!("law on disk failed to parse/validate: {}", e))?),
            None => None,
        };
        let version = new_law.as_ref()
            .map(|l| l.version.clone())
            .unwrap_or_else(|| "none".to_string());
        *self.law.write().await = new_law;
        Ok(version)
    }
}

pub fn router(state: RestState) -> Router {
    Router::new()
        .route("/v1/auth/challenge", post(issue_challenge))
        // Canonical hub-named routes.
        .route("/v1/hubs/:hub_id/events", post(submit_event))
        .route("/v1/hubs/:hub_id/state", get(read_state))
        // Back-compat: Legion's Hestia H2/H3 client (hestia@253c611)
        // targets /v1/chapters/{id}/* — register the same handlers
        // under that path until Hestia rolls forward to /v1/hubs/.
        .route("/v1/chapters/:hub_id/events", post(submit_event))
        .route("/v1/chapters/:hub_id/state", get(read_state))
        .route("/v1/admin/reload-law", post(reload_law))
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

// ---------- POST /v1/hubs/{hub_id}/events ----------

/// The action types V2-7 Step 2 routes from a verified envelope.
/// Mirrors a subset of HubEvent; extends as more flows land.
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
    Path(hub_id): Path<Uuid>,
    Json(envelope): Json<SignedEnvelope>,
) -> Result<Json<EventAccepted>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "chapter id {} does not match this hub's chapter {}",
            hub_id, s.hub_id
        )));
    }

    // 1. Authority check: envelope verifies (signer known, nonce valid,
    // payload not tampered).
    let _redeemed = verify_envelope(&envelope, &s.nonces, s.resolver.as_ref(), Utc::now())?;

    // 2. V2-7 Step 2 authorization: only Sovereign can submit signed
    // envelopes. Member-signing arrives with V2-12. PolicyEntity gating
    // arrives with V2-8.
    if envelope.signer_lct_id != s.sovereign_lct_id {
        return Err(ApiError::unauthorized(format!(
            "V2-7 Step 2: only Sovereign LCT may submit signed envelopes; got {}",
            envelope.signer_lct_id
        )));
    }

    // 3. Parse the action.
    let action: EnvelopeAction = serde_json::from_value(envelope.payload.clone())
        .map_err(|e| ApiError::bad_request(format!("payload not a known action: {}", e)))?;

    let event = match action {
        EnvelopeAction::AddMember { member_lct_id, name } => HubEvent::MemberAdded {
            member_lct_id,
            added_by: envelope.signer_lct_id,
            member_name: name,
        },
        EnvelopeAction::DeclareSkill { member_lct_id, skill } => HubEvent::MemberSkillDeclared {
            member_lct_id,
            skill,
            declared_by: envelope.signer_lct_id,
        },
    };

    // 3.5 PolicyEntity gate (V2-8 §4): if a chapter law is loaded,
    // evaluate the act against it. Deny → 403; Escalate → 202 with the
    // escalate_to role; Allow → proceed.
    let law_guard = s.law.read().await;
    if let Some(law) = law_guard.as_ref() {
        let req = build_r6_request(&envelope, &event)
            .map_err(ApiError::internal)?;
        let outcome = law.evaluate_outcome(&req);
        match outcome.decision {
            Decision::Allow => { /* proceed */ }
            Decision::Deny => {
                return Err(ApiError {
                    status: StatusCode::FORBIDDEN,
                    message: format!(
                        "act denied by chapter law (norm: {})",
                        outcome.winning_norm.as_deref().unwrap_or("?")
                    ),
                });
            }
            Decision::Escalate => {
                return Err(ApiError {
                    status: StatusCode::ACCEPTED,
                    message: format!(
                        "act requires escalation to {} ({}); admin review queue is V2-16",
                        outcome.escalate_to.as_deref().unwrap_or("sovereign"),
                        outcome.winning_norm.as_deref().unwrap_or("escalation trigger"),
                    ),
                });
            }
        }
    }
    drop(law_guard);

    // 4. Build the unsigned entry. We need the ledger lock briefly to
    // assign index + prev_hash, then we release it during the (possibly
    // remote) signing roundtrip, then re-acquire to commit. The
    // append_signed call detects if a parallel append landed in between
    // and errors loudly rather than corrupting the chain (per Step 3a's
    // stale-detection contract).
    let event_kind_str = event.kind().to_string();
    let event_value = serde_json::to_value(&event)
        .map_err(|e| ApiError::internal(anyhow::anyhow!("serializing event: {}", e)))?;
    let (unsigned, intent) = {
        let ledger = s.ledger.lock().await;
        let unsigned = ledger.build_entry(s.sovereign_lct_id, event.clone(), Utc::now())
            .map_err(ApiError::internal)?;
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

    // 5. Sign — via LocalKeypairSigner (MVP) or HestiaCallbackSigner
    // (V2-7+). The signer trait abstracts whether the key lives in
    // process or in a remote vault. Per architecture commitment #8,
    // the hub never holds keys in Hestia-mode chapters.
    let signing_bytes = unsigned.signing_bytes.clone();
    let signature = s.signer
        .sign(s.sovereign_lct_id, &signing_bytes, &intent)
        .await
        .map_err(|e| match e {
            hub_lib::signer::SignError::Denied(reason) => ApiError::unauthorized(
                format!("Sovereign signer denied: {}", reason)
            ),
            hub_lib::signer::SignError::Transport(msg) => ApiError {
                status: StatusCode::SERVICE_UNAVAILABLE,
                message: format!("Sovereign signer unreachable: {}", msg),
            },
            hub_lib::signer::SignError::Malformed(msg) => ApiError::internal(
                anyhow::anyhow!("malformed signer response: {}", msg)
            ),
            hub_lib::signer::SignError::Internal(err) => ApiError::internal(err),
        })?;

    // 6. Commit the signed entry.
    let mut ledger = s.ledger.lock().await;
    let entry = ledger.append_signed(unsigned, signature)
        .map_err(ApiError::internal)?;

    Ok(Json(EventAccepted {
        entry_index: entry.index,
        entry_hash: entry.entry_hash.clone(),
        event_kind: entry.event.kind().to_string(),
        signer_lct_id: envelope.signer_lct_id,
    }))
}

// ---------- GET /v1/hubs/{hub_id}/state ----------

#[derive(Serialize)]
struct PublicState {
    hub_id: Uuid,
    hub_name: String,
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
    Path(hub_id): Path<Uuid>,
) -> Result<Json<PublicState>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "chapter id {} does not match this hub's chapter {}",
            hub_id, s.hub_id
        )));
    }
    let ledger = s.ledger.lock().await;
    let state = HubState::project(&ledger);
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
        hub_id: s.hub_id,
        hub_name: state.hub_name,
        member_count,
        ledger_entries,
        head_hash,
        filled_roles,
    }))
}

// ---------- POST /v1/admin/reload-law ----------

#[derive(Serialize)]
struct ReloadLawResponse {
    reloaded: bool,
    version: String,
}

async fn reload_law(
    State(s): State<RestState>,
) -> Result<Json<ReloadLawResponse>, ApiError> {
    let version = s.reload_law().await.map_err(ApiError::internal)?;
    Ok(Json(ReloadLawResponse { reloaded: true, version }))
}

// ---------- PolicyEntity gate helper (V2-8 §4) ----------

/// Build an R6Request from a SignedEnvelope + the resolved HubEvent.
/// V2-8 §4 first cut: role is hardcoded to "sovereign" since
/// envelope-authenticated submissions today require the Sovereign
/// signer (V2-7 §2 restriction; member-signing arrives with V2-12).
/// `resource` is empty for V2-8 — future sprints add ATP tracking,
/// witness counts, etc. via additional context.
fn build_r6_request(_envelope: &SignedEnvelope, event: &HubEvent) -> anyhow::Result<R6Request> {
    let payload = serde_yaml::to_value(event)
        .map_err(|e| anyhow::anyhow!("serializing event for R6: {}", e))?;
    Ok(R6Request {
        role: "sovereign".to_string(),
        action: event.kind().to_string(),
        payload,
        resource: Default::default(),
    })
}
