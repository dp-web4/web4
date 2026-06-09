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
    /// Public-key resolver for envelope signature verification.
    /// Wrapped in RwLock so the V2-12 join endpoint can extend it
    /// at runtime as new members are admitted.
    pub resolver: Arc<tokio::sync::RwLock<MapResolver>>,
    /// Chapter law, loaded at open() time. None = no law set (all
    /// envelope-authenticated acts allowed). When present, the PolicyEntity
    /// gate runs before each act is committed to the ledger.
    ///
    /// Wrapped in RwLock so set-law (or `POST /v1/hubs/{id}/law`)
    /// can hot-reload without restarting hub serve.
    pub law: Arc<tokio::sync::RwLock<Option<Law>>>,
}

impl RestState {
    /// As `hub serve` needs it: a caller-supplied shared in-memory ledger
    /// handle. `hub serve` passes the *same* `Arc<Mutex<HubLedger>>` here and
    /// to `McpState`, so MCP, REST, and the admin dashboard all read/write one
    /// ledger — an act recorded through any surface is immediately visible to
    /// the others (previously each held its own startup snapshot and only
    /// reconverged on restart).
    pub async fn open_with_law_and_ledger(
        hub_dir: PathBuf,
        law: Arc<tokio::sync::RwLock<Option<Law>>>,
        ledger: Arc<Mutex<HubLedger>>,
    ) -> Result<Self> {
        let paths = HubPaths::new(hub_dir.clone());
        let config = hub_lib::hub::HubConfig::load(paths.config())?;
        let society = load_society(&hub_dir).await?;

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

        // Resolver seeded with the Sovereign LCT + every member's pubkey
        // from prior MemberAdded events (V2-12). HubState::project walks
        // the ledger and accumulates member_pubkeys; we reconstruct an Lct
        // per member so future envelopes from them verify against the
        // public key recorded at admission time.
        let mut resolver = MapResolver::new();
        resolver.insert(sovereign_lct.clone());
        let projected = {
            let l = ledger.lock().await;
            HubState::project(&*l)
        };
        for (member_lct_id, pubkey_hex) in &projected.member_pubkeys {
            match hub_lib::hub::hestia_sovereign_lct(*member_lct_id, pubkey_hex) {
                Ok(lct) => resolver.insert(lct),
                Err(e) => tracing::warn!(
                    "skipping member {} pubkey reconstruction: {}",
                    member_lct_id, e
                ),
            }
        }
        // V2-9 Phase 1: seed the resolver with every Sovereign Council
        // holder's pubkey so any holder can sign chapter acts as a
        // co-Sovereign. Holders are also auto-added to member_pubkeys
        // when they're admitted (CouncilMemberAdded handler in state.rs
        // inserts them into the member registry); this loop is the
        // explicit council-holder pass for clarity + to surface
        // reconstruction errors with the council label.
        for (holder_lct_id, pubkey_hex) in &projected.council_pubkeys {
            match hub_lib::hub::hestia_sovereign_lct(*holder_lct_id, pubkey_hex) {
                Ok(lct) => resolver.insert(lct),
                Err(e) => tracing::warn!(
                    "skipping council holder {} pubkey reconstruction: {}",
                    holder_lct_id, e
                ),
            }
        }

        Ok(Self {
            paths,
            hub_id: society.lct_id,
            hub_name: society.name.clone(),
            sovereign_lct_id: sovereign_lct.id,
            signer,
            ledger,
            nonces: Arc::new(NonceStore::new()),
            resolver: Arc::new(tokio::sync::RwLock::new(resolver)),
            law,
        })
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
        let new_law: Option<Law> = match store.read_law().await? {
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
        // Discovery endpoint that Hestia's `hestia hub connect` calls.
        // Matches the HubInfo shape declared in `hestia/core/src/hub.rs`
        // (hub_lct_id, api_versions, endpoints, hubs). Unauthenticated
        // by design — discovery is a public read.
        .route("/.well-known/web4-hub.json", get(well_known_hub_info))
        .route("/v1/auth/challenge", post(issue_challenge))
        // Hub-named routes (canonical; chapter→hub rename mirrored on
        // Hestia side at hestia@c3932a8 — back-compat /v1/chapters/*
        // aliases dropped 2026-06-08).
        .route("/v1/hubs/:hub_id/events", post(submit_event))
        .route("/v1/hubs/:hub_id/state", get(read_state))
        .route("/v1/hubs/:hub_id/members/join", post(submit_join))
        // V2-9 Phase 2: Sovereign Council proposal + aggregation flow.
        .route("/v1/hubs/:hub_id/council/propose", post(submit_proposal))
        .route("/v1/hubs/:hub_id/council/sign", post(sign_proposal))
        .route("/v1/hubs/:hub_id/council/proposals", get(list_proposals))
        .route("/v1/hubs/:hub_id/council/proposals/:proposal_id", get(get_proposal))
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

// ---------- GET /.well-known/web4-hub.json (discovery) ----------

/// Shape matches `hestia::hub::HubInfo` exactly so `hestia hub connect`
/// can deserialize without translation. Public read; no auth.
#[derive(Serialize)]
struct WellKnownHubInfo {
    /// The hub's society LCT id (what `hestia hub connect` keys on).
    hub_lct_id: Uuid,
    /// API versions this hub serves. v1 today; future versions get
    /// added when the wire shape evolves under semver discipline.
    api_versions: Vec<&'static str>,
    /// Endpoint hints for clients. `rest` is the v1 base; `mcp` is the
    /// tool-call base. Both are relative to the hub's reachable URL
    /// (the client already knows it — they fetched this from there).
    endpoints: WellKnownEndpoints,
    /// Hubs this server hosts. Single-hub deployments return one entry;
    /// future multi-hub hosting returns multiple.
    hubs: Vec<WellKnownHubSummary>,
}

#[derive(Serialize)]
struct WellKnownEndpoints {
    rest: &'static str,
    mcp: &'static str,
}

#[derive(Serialize)]
struct WellKnownHubSummary {
    id: Uuid,
    name: String,
    public: bool,
}

async fn well_known_hub_info(
    State(s): State<RestState>,
) -> Json<WellKnownHubInfo> {
    Json(WellKnownHubInfo {
        hub_lct_id: s.hub_id,
        api_versions: vec!["v1"],
        endpoints: WellKnownEndpoints {
            rest: "/v1",
            mcp: "/tools",
        },
        hubs: vec![WellKnownHubSummary {
            id: s.hub_id,
            name: s.hub_name.clone(),
            // For now every hub the daemon serves is publicly
            // discoverable — if you reached the well-known you reach
            // the hub. Private hub semantics (ACLs at the discovery
            // layer) land if/when the operational model requires.
            public: true,
        }],
    })
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
    let resolver_guard = s.resolver.read().await;
    let _redeemed = verify_envelope(&envelope, &s.nonces, &*resolver_guard, Utc::now())?;
    drop(resolver_guard);

    // 2. V2-7 §2 broadening (Sprint 3): the founding Sovereign OR any
    // current member may sign envelopes. Per-action authorization
    // (below at action match) constrains *which* acts each may perform
    // — Sovereign-only acts (add_member) reject member envelopes;
    // self-acts (declare_skill) require envelope.signer == act subject.
    //
    // Pre-Sprint-3 behavior was Sovereign-only at this layer. The
    // restriction moved into per-action checks because V2-12 admitted
    // members already authenticate via the resolver — gating their
    // envelopes here was just delaying the inevitable.
    let (signer_is_sovereign, signer_is_member) = {
        let ledger = s.ledger.lock().await;
        let projected = hub_lib::state::HubState::project(&*ledger);
        let is_sov = envelope.signer_lct_id == s.sovereign_lct_id;
        let is_member = projected.members.contains_key(&envelope.signer_lct_id);
        (is_sov, is_member)
    };
    if !signer_is_sovereign && !signer_is_member {
        return Err(ApiError::unauthorized(format!(
            "signer {} is neither the founding Sovereign nor a current member",
            envelope.signer_lct_id
        )));
    }

    // 2.5 V2-9 Phase 2 council gate: if a council threshold of 2+ is
    // recorded in state, no single-signer commit is permitted — all
    // acts must flow through the council propose/sign endpoints so
    // M-of-N is actually enforced. The founding Sovereign is still a
    // valid voter; they just participate as one of M like any holder.
    let council_threshold_active = {
        let ledger = s.ledger.lock().await;
        let projected = hub_lib::state::HubState::project(&*ledger);
        matches!(projected.council_threshold, Some((m, _)) if m >= 2)
    };
    if council_threshold_active {
        return Err(ApiError {
            status: StatusCode::CONFLICT,
            message: "council mode active (threshold >= 2-of-N): submit acts via \
                      POST /v1/hubs/{hub_id}/council/propose + /sign".into(),
        });
    }

    // 3. Parse the action.
    let action: EnvelopeAction = serde_json::from_value(envelope.payload.clone())
        .map_err(|e| ApiError::bad_request(format!("payload not a known action: {}", e)))?;

    // Per-action authorization. Sprint 3 carves the action space into
    // "Sovereign-only" (membership control, role assignment, charter,
    // law) and "member-self" (declare your own skill, etc.). The
    // founding Sovereign can do anything; members are restricted to
    // acts about themselves.
    let event = match action {
        EnvelopeAction::AddMember { member_lct_id, name } => {
            if !signer_is_sovereign {
                return Err(ApiError::unauthorized(String::from(
                    "add_member is a Sovereign-only act; members cannot admit other members \
                     (members self-add via POST /v1/hubs/{id}/members/join — V2-12)"
                )));
            }
            HubEvent::MemberAdded {
                member_lct_id,
                added_by: envelope.signer_lct_id,
                member_name: name,
                member_pubkey_hex: None,
            }
        }
        EnvelopeAction::DeclareSkill { member_lct_id, skill } => {
            // Sovereign can declare skills for any member (operator
            // convenience). Members can declare only their OWN skills —
            // signer must match the subject, no impersonation.
            if !signer_is_sovereign && envelope.signer_lct_id != member_lct_id {
                return Err(ApiError::unauthorized(format!(
                    "members may only declare their own skills (signer {} != subject {})",
                    envelope.signer_lct_id, member_lct_id,
                )));
            }
            HubEvent::MemberSkillDeclared {
                member_lct_id,
                skill,
                declared_by: envelope.signer_lct_id,
            }
        }
    };

    // 3.5 PolicyEntity gate (V2-8 §4): if a chapter law is loaded,
    // evaluate the act against it. Deny → 403; Escalate → 202 with the
    // escalate_to role; Allow → proceed.
    let law_guard = s.law.read().await;
    if let Some(law) = law_guard.as_ref() {
        let req = build_r6_request(&envelope, &event, s.sovereign_lct_id)
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
    let entry = ledger.append_signed(unsigned, signature).await
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
    let society = load_society(s.paths.root.clone()).await
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

// ---------- POST /v1/hubs/{hub_id}/members/join (V2-12) ----------

/// Payload shape inside the SignedEnvelope for a join request. The
/// member signs this with their own keypair; the hub bootstraps
/// signature verification from the supplied `member_pubkey_hex`
/// (since the resolver doesn't yet know this LCT).
#[derive(Clone, Debug, Serialize, Deserialize)]
struct JoinPayload {
    /// MUST be "member_join_request" so a misrouted envelope can't
    /// accidentally trigger a join.
    action: String,
    /// The applicant's LCT id. MUST equal envelope.signer_lct_id.
    member_lct_id: Uuid,
    /// Applicant's public key (hex-encoded 32 bytes) — pinned by this
    /// MemberAdded event for future signature verification.
    member_pubkey_hex: String,
    #[serde(default)]
    name: Option<String>,
}

#[derive(Serialize)]
struct JoinAccepted {
    member_lct_id: Uuid,
    entry_index: u64,
    entry_hash: String,
    welcome: String,
}

async fn submit_join(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
    Json(envelope): Json<SignedEnvelope>,
) -> Result<Json<JoinAccepted>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }

    // 1. Parse the join payload from the envelope.
    let payload: JoinPayload = serde_json::from_value(envelope.payload.clone())
        .map_err(|e| ApiError::bad_request(format!("join payload not parseable: {}", e)))?;
    if payload.action != "member_join_request" {
        return Err(ApiError::bad_request(format!(
            "join endpoint requires action='member_join_request', got '{}'",
            payload.action
        )));
    }
    if payload.member_lct_id != envelope.signer_lct_id {
        return Err(ApiError::bad_request(format!(
            "envelope.signer_lct_id ({}) must match payload.member_lct_id ({})",
            envelope.signer_lct_id, payload.member_lct_id,
        )));
    }

    // 2. Bootstrap signature verification against the payload-supplied
    // pubkey. Adhoc one-shot resolver containing just the applicant —
    // we can't go through s.resolver because the applicant isn't there
    // yet (that's the whole point of join). The pubkey is self-vouched
    // for this single act; downstream verification trusts the same key
    // because admission pinned it into the ledger.
    let applicant_lct = hub_lib::hub::hestia_sovereign_lct(
        payload.member_lct_id, &payload.member_pubkey_hex,
    ).map_err(|e| ApiError::bad_request(format!("invalid member_pubkey_hex: {}", e)))?;
    let mut adhoc = MapResolver::new();
    adhoc.insert(applicant_lct.clone());
    let _redeemed = verify_envelope(&envelope, &s.nonces, &adhoc, Utc::now())?;

    // 3. PolicyEntity gate — admission policy from chapter law.
    // R6Request shape: role="applicant" (not yet a member), action is
    // the join itself, payload carries the request fields.
    let event = HubEvent::MemberAdded {
        member_lct_id: payload.member_lct_id,
        added_by: s.sovereign_lct_id,
        member_name: payload.name.clone(),
        member_pubkey_hex: Some(payload.member_pubkey_hex.clone()),
    };
    let event_kind_str = event.kind().to_string();
    let event_value_yaml = serde_yaml::to_value(&event)
        .map_err(|e| ApiError::internal(anyhow::anyhow!("serializing event for R6: {}", e)))?;

    let law_guard = s.law.read().await;
    if let Some(law) = law_guard.as_ref() {
        let req = R6Request {
            role: "applicant".to_string(),
            action: "member_join_request".to_string(),
            payload: event_value_yaml.clone(),
            resource: Default::default(),
        };
        let outcome = law.evaluate_outcome(&req);
        match outcome.decision {
            Decision::Allow => { /* proceed */ }
            Decision::Deny => {
                return Err(ApiError {
                    status: StatusCode::FORBIDDEN,
                    message: format!(
                        "membership denied by chapter law (norm: {})",
                        outcome.winning_norm.as_deref().unwrap_or("?")
                    ),
                });
            }
            Decision::Escalate => {
                return Err(ApiError {
                    status: StatusCode::ACCEPTED,
                    message: format!(
                        "membership requires escalation to {} ({}); admin review queue is V2-16",
                        outcome.escalate_to.as_deref().unwrap_or("sovereign"),
                        outcome.winning_norm.as_deref().unwrap_or("escalation trigger"),
                    ),
                });
            }
        }
    }
    drop(law_guard);

    // 4. Build unsigned MemberAdded entry, ask Sovereign signer to sign it,
    // commit. Same shape as submit_event's signing path.
    let (unsigned, intent) = {
        let ledger = s.ledger.lock().await;
        let unsigned = ledger.build_entry(s.sovereign_lct_id, event, Utc::now())
            .map_err(ApiError::internal)?;
        let intent = SignIntent {
            request_id: Uuid::new_v4(),
            hub_id: s.hub_id,
            hub_name: s.hub_name.clone(),
            actor_lct_id: s.sovereign_lct_id,
            ledger_index: unsigned.entry.index,
            event_kind: event_kind_str.clone(),
            event: serde_json::to_value(&unsigned.entry.event)
                .map_err(|e| ApiError::internal(anyhow::anyhow!("serializing event for intent: {}", e)))?,
        };
        (unsigned, intent)
    };

    let signing_bytes = unsigned.signing_bytes.clone();
    let signature = s.signer
        .sign(s.sovereign_lct_id, &signing_bytes, &intent)
        .await
        .map_err(|e| ApiError::internal(anyhow::anyhow!("Sovereign signer denied/failed: {}", e)))?;

    let entry_index;
    let entry_hash;
    {
        let mut ledger = s.ledger.lock().await;
        let entry = ledger.append_signed(unsigned, signature).await
            .map_err(ApiError::internal)?;
        entry_index = entry.index;
        entry_hash = entry.entry_hash.clone();
    }

    // 5. Add the new member's pubkey to the live resolver so future
    // member-signed envelopes from them verify without a serve restart.
    s.resolver.write().await.insert(applicant_lct);

    Ok(Json(JoinAccepted {
        member_lct_id: payload.member_lct_id,
        entry_index,
        entry_hash,
        welcome: format!("welcome to {}", s.hub_name),
    }))
}

// ---------- PolicyEntity gate helper (V2-8 §4) ----------

/// Build an R6Request from a SignedEnvelope + the resolved HubEvent.
///
/// Sprint 3 (V2-7 §2 broadening): the role is now derived from the
/// signer. Sovereign envelopes get role="sovereign"; member envelopes
/// get role="citizen" (the base membership role per Web4 spec). Chapter
/// law can therefore write different norms for each — e.g., allow
/// citizens to declare_skill but deny them from add_member (which
/// is already enforced upstream in submit_event's per-action check;
/// the law can add policy on top of code-level authorization).
fn build_r6_request(
    envelope: &SignedEnvelope,
    event: &HubEvent,
    sovereign_lct_id: Uuid,
) -> anyhow::Result<R6Request> {
    let payload = serde_yaml::to_value(event)
        .map_err(|e| anyhow::anyhow!("serializing event for R6: {}", e))?;
    let role = if envelope.signer_lct_id == sovereign_lct_id {
        "sovereign"
    } else {
        "citizen"
    };
    Ok(R6Request {
        role: role.to_string(),
        action: event.kind().to_string(),
        payload,
        resource: Default::default(),
    })
}

// ============================================================================
// V2-9 Phase 2 — Sovereign Council propose / sign / list / get
// ============================================================================

use hub_lib::proposal::{CouncilProposal, ProposalStatus};

#[derive(Deserialize)]
#[serde(tag = "action", rename_all = "snake_case")]
enum CouncilAction {
    CouncilPropose { proposed_event: HubEvent },
    CouncilSign { proposal_id: Uuid },
}

#[derive(Serialize)]
struct ProposalSummary {
    id: Uuid,
    event_kind: String,
    proposed_by: Uuid,
    proposed_at: chrono::DateTime<Utc>,
    expires_at: chrono::DateTime<Utc>,
    signatures: usize,
    threshold_m: u32,
    threshold_n: u32,
    status: ProposalStatusTag,
    /// Set when status == "committed".
    #[serde(skip_serializing_if = "Option::is_none")]
    entry_index: Option<u64>,
}

#[derive(Serialize)]
#[serde(rename_all = "snake_case")]
enum ProposalStatusTag {
    Open,
    Committed,
    Rejected,
    Expired,
}

impl From<&ProposalStatus> for ProposalStatusTag {
    fn from(s: &ProposalStatus) -> Self {
        match s {
            ProposalStatus::Open => Self::Open,
            ProposalStatus::Committed { .. } => Self::Committed,
            ProposalStatus::Rejected { .. } => Self::Rejected,
            ProposalStatus::Expired => Self::Expired,
        }
    }
}

fn summarize(p: &CouncilProposal, threshold: (u32, u32)) -> ProposalSummary {
    let entry_index = match &p.status {
        ProposalStatus::Committed { entry_index, .. } => Some(*entry_index),
        _ => None,
    };
    ProposalSummary {
        id: p.id,
        event_kind: p.proposed_event.kind().to_string(),
        proposed_by: p.proposed_by,
        proposed_at: p.proposed_at,
        expires_at: p.expires_at,
        signatures: p.unique_signers().len(),
        threshold_m: threshold.0,
        threshold_n: threshold.1,
        status: (&p.status).into(),
        entry_index,
    }
}

/// Project the current set of valid council holders (founding Sovereign
/// included) + the threshold from the ledger. Used by both propose
/// and sign to know who counts as a vote.
fn project_council(
    s: &RestState,
    ledger: &hub_lib::ledger::HubLedger,
) -> (std::collections::BTreeSet<Uuid>, (u32, u32)) {
    let projected = hub_lib::state::HubState::project(ledger);
    let mut holders = projected.council_holders.clone();
    holders.insert(s.sovereign_lct_id);
    // Default threshold when none set: 1-of-1 (current behavior). The
    // propose flow still works without an explicit threshold — it just
    // commits on first signature, which mirrors single-Sovereign mode
    // but produces a council audit trail.
    let threshold = projected.council_threshold
        .unwrap_or((1, holders.len() as u32));
    (holders, threshold)
}

async fn submit_proposal(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
    Json(envelope): Json<SignedEnvelope>,
) -> Result<Json<ProposalSummary>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }

    // 1. Envelope verifies (signature + nonce + signer known).
    let resolver_guard = s.resolver.read().await;
    let _redeemed = verify_envelope(&envelope, &s.nonces, &*resolver_guard, Utc::now())?;
    drop(resolver_guard);

    // 2. Parse + validate action shape.
    let action: CouncilAction = serde_json::from_value(envelope.payload.clone())
        .map_err(|e| ApiError::bad_request(format!("payload not a council action: {}", e)))?;
    let proposed_event = match action {
        CouncilAction::CouncilPropose { proposed_event } => proposed_event,
        CouncilAction::CouncilSign { .. } => {
            return Err(ApiError::bad_request(
                String::from("this endpoint expects action=council_propose; use /council/sign for council_sign")
            ));
        }
    };

    // 3. Authorization: signer must be a current council holder (or
    // founding Sovereign). Members can't propose chapter acts.
    let (holders, threshold) = {
        let ledger = s.ledger.lock().await;
        project_council(&s, &*ledger)
    };
    if !holders.contains(&envelope.signer_lct_id) {
        return Err(ApiError::unauthorized(format!(
            "signer {} is not a Sovereign Council holder", envelope.signer_lct_id
        )));
    }

    // 4. Create proposal + record proposer's vote. Cleanup any expired
    // proposals while we're touching the store, so they don't pile up.
    let now = Utc::now();
    let mut proposal = CouncilProposal::new(proposed_event, envelope.signer_lct_id, now);
    proposal.add_vote(envelope, now);

    // If proposer alone meets threshold (1-of-1 case or 1-of-N with
    // M=1), commit immediately so this works as a strict superset of
    // the existing /events flow.
    if proposal.meets_threshold(threshold.0, &holders) {
        let entry_index = commit_proposed_event(&s, &proposal.proposed_event, Some(proposal.id)).await?;
        proposal.status = ProposalStatus::Committed { entry_index, committed_at: now };
    }

    persist_proposal(&s, &proposal).await?;
    cleanup_expired_proposals(&s, now).await;

    Ok(Json(summarize(&proposal, threshold)))
}

async fn sign_proposal(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
    Json(envelope): Json<SignedEnvelope>,
) -> Result<Json<ProposalSummary>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }

    let resolver_guard = s.resolver.read().await;
    let _redeemed = verify_envelope(&envelope, &s.nonces, &*resolver_guard, Utc::now())?;
    drop(resolver_guard);

    let action: CouncilAction = serde_json::from_value(envelope.payload.clone())
        .map_err(|e| ApiError::bad_request(format!("payload not a council action: {}", e)))?;
    let proposal_id = match action {
        CouncilAction::CouncilSign { proposal_id } => proposal_id,
        CouncilAction::CouncilPropose { .. } => {
            return Err(ApiError::bad_request(
                String::from("this endpoint expects action=council_sign; use /council/propose for council_propose")
            ));
        }
    };

    let (holders, threshold) = {
        let ledger = s.ledger.lock().await;
        project_council(&s, &*ledger)
    };
    if !holders.contains(&envelope.signer_lct_id) {
        return Err(ApiError::unauthorized(format!(
            "signer {} is not a Sovereign Council holder", envelope.signer_lct_id
        )));
    }

    let mut proposal = read_proposal(&s, proposal_id).await?
        .ok_or_else(|| ApiError::not_found(format!("proposal {} not found", proposal_id)))?;

    if !proposal.is_open() {
        return Err(ApiError {
            status: StatusCode::CONFLICT,
            message: format!("proposal {} is not open (status: {:?})", proposal_id, proposal.status),
        });
    }
    let now = Utc::now();
    if proposal.is_expired_at(now) {
        proposal.status = ProposalStatus::Expired;
        persist_proposal(&s, &proposal).await?;
        return Err(ApiError {
            status: StatusCode::CONFLICT,
            message: format!("proposal {} expired at {}", proposal_id, proposal.expires_at),
        });
    }

    proposal.add_vote(envelope, now);

    if proposal.meets_threshold(threshold.0, &holders) {
        let entry_index = commit_proposed_event(&s, &proposal.proposed_event, Some(proposal.id)).await?;
        proposal.status = ProposalStatus::Committed { entry_index, committed_at: now };
    }

    persist_proposal(&s, &proposal).await?;
    Ok(Json(summarize(&proposal, threshold)))
}

async fn list_proposals(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
) -> Result<Json<Vec<ProposalSummary>>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }
    let (_holders, threshold) = {
        let ledger = s.ledger.lock().await;
        project_council(&s, &*ledger)
    };
    let proposals = read_all_proposals(&s).await?;
    Ok(Json(proposals.iter().map(|p| summarize(p, threshold)).collect()))
}

async fn get_proposal(
    State(s): State<RestState>,
    Path((hub_id, proposal_id)): Path<(Uuid, Uuid)>,
) -> Result<Json<CouncilProposal>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }
    let proposal = read_proposal(&s, proposal_id).await?
        .ok_or_else(|| ApiError::not_found(format!("proposal {} not found", proposal_id)))?;
    Ok(Json(proposal))
}

// ---------- council helpers ----------
//
// Direct async calls now that HubStore is async-trait. No spawn_blocking
// needed — file/sqlite store methods complete synchronously inside their
// async fn bodies; future network backends (DynamoDB, Postgres) do real
// awaits here.

async fn persist_proposal(s: &RestState, proposal: &CouncilProposal) -> Result<(), ApiError> {
    let mut store = hub_lib::store::open_chapter_store(&s.paths.root)
        .map_err(ApiError::internal)?;
    store.write_proposal(proposal).await
        .map_err(ApiError::internal)
}

async fn read_proposal(s: &RestState, id: Uuid) -> Result<Option<CouncilProposal>, ApiError> {
    let store = hub_lib::store::open_chapter_store(&s.paths.root)
        .map_err(ApiError::internal)?;
    store.read_proposal(id).await
        .map_err(ApiError::internal)
}

async fn read_all_proposals(s: &RestState) -> Result<Vec<CouncilProposal>, ApiError> {
    let store = hub_lib::store::open_chapter_store(&s.paths.root)
        .map_err(ApiError::internal)?;
    store.list_proposals().await
        .map_err(ApiError::internal)
}

async fn cleanup_expired_proposals(s: &RestState, now: chrono::DateTime<Utc>) {
    // Best-effort: mark expired proposals so listings reflect reality.
    // We don't delete — keeping them as audit trail of attempted-but-
    // never-committed acts. Deletion is a separate operator action.
    let Ok(all) = read_all_proposals(s).await else { return };
    for mut p in all {
        if p.is_open() && p.is_expired_at(now) {
            p.status = ProposalStatus::Expired;
            let _ = persist_proposal(s, &p).await;
        }
    }
}

/// Commit a proposed event to the ledger via the hub's signer (founding
/// Sovereign). The ledger entry's `actor_lct_id` is the founding
/// Sovereign — they're the executor of the council's decision. The
/// authorization audit trail (M holder signatures) lives in the
/// proposal record, linked bidirectionally:
/// - proposal → ledger: `ProposalStatus::Committed { entry_index }`
/// - ledger → proposal: `LedgerEntry.proposal_ref = Some(proposal_id)`
/// The ledger-side reference is part of `signing_payload`, so an
/// attacker can't forge a `proposal_ref` onto an existing entry
/// without invalidating the founding Sovereign's signature.
async fn commit_proposed_event(
    s: &RestState,
    event: &HubEvent,
    proposal_ref: Option<Uuid>,
) -> Result<u64, ApiError> {
    let event_kind_str = event.kind().to_string();
    let event_value = serde_json::to_value(event)
        .map_err(|e| ApiError::internal(anyhow::anyhow!("serializing event: {}", e)))?;
    let (unsigned, intent) = {
        let ledger = s.ledger.lock().await;
        let unsigned = ledger.build_entry_with_proposal_ref(
            s.sovereign_lct_id, event.clone(), Utc::now(), proposal_ref,
        ).map_err(ApiError::internal)?;
        let intent = SignIntent {
            request_id: Uuid::new_v4(),
            hub_id: s.hub_id,
            hub_name: s.hub_name.clone(),
            actor_lct_id: s.sovereign_lct_id,
            ledger_index: unsigned.entry.index,
            event_kind: event_kind_str,
            event: event_value,
        };
        (unsigned, intent)
    };
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
    let mut ledger = s.ledger.lock().await;
    let (entry_index, needs_resolver_refresh) = {
        let entry = ledger.append_signed(unsigned, signature).await
            .map_err(ApiError::internal)?;
        let needs = matches!(
            &entry.event,
            HubEvent::CouncilMemberAdded { .. } | HubEvent::MemberAdded { .. }
        );
        (entry.index, needs)
    };
    // If the committed act was a council membership / member-add,
    // refresh the resolver so the new pubkey can verify envelopes
    // immediately (same pattern as submit_join's live insert).
    if needs_resolver_refresh {
        let projected = hub_lib::state::HubState::project(&*ledger);
        let mut resolver = s.resolver.write().await;
        for (lct_id, pk) in projected.member_pubkeys.iter()
            .chain(projected.council_pubkeys.iter())
        {
            if let Ok(lct) = hub_lib::hub::hestia_sovereign_lct(*lct_id, pk) {
                resolver.insert(lct);
            }
        }
    }
    Ok(entry_index)
}
