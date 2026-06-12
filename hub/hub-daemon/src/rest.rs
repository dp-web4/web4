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
use hub_lib::envelope::{verify_envelope, Challenge, MapResolver, NonceStore, PublicKeyResolver, SignedEnvelope, VerifyError};
use hub_lib::events::HubEvent;
use hub_lib::identity::IdentityFile;
use hub_lib::init::load_society;
use hub_lib::law::{Decision, DecisionOutcome, Law, R6Request};
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
    /// Per-pair constellation MFA state: outstanding challenge nonces +
    /// verified assurance-tier bindings (`constellation_challenge` /
    /// `present_constellation` channel tools).
    pub constellations: Arc<hub_lib::constellation::ConstellationGate>,
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
            constellations: Arc::new(hub_lib::constellation::ConstellationGate::new()),
        })
    }

    /// Re-read the chapter law from storage and swap it into the
    /// in-memory snapshot. Returns Ok with the version (or "none" if
    /// no law set). Used by the `/v1/admin/reload-law` endpoint so
    /// operators can `hub set-law` then `curl reload-law` without
    /// restarting hub serve.
    pub async fn reload_law(&self) -> anyhow::Result<String> {
        use anyhow::Context;
        let store = hub_lib::store::open_hub_store(&self.paths.root)
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
        // Member↔hub E2E channel: citizen-tier reads/acts travel sealed,
        // never in the clear. The sealed request authenticates the caller
        // (AEAD open) AND decrypts in one step; the response is sealed back.
        .route("/v1/hubs/:hub_id/channel", post(channel_request))
        .route("/v1/hubs/:hub_id/members/join", post(submit_join))
        // V2-9 Phase 2: Sovereign Council proposal + aggregation flow.
        .route("/v1/hubs/:hub_id/council/propose", post(submit_proposal))
        .route("/v1/hubs/:hub_id/council/sign", post(sign_proposal))
        .route("/v1/hubs/:hub_id/council/proposals", get(list_proposals))
        .route("/v1/hubs/:hub_id/council/proposals/:proposal_id", get(get_proposal))
        // PAIRED-CHANNELS Sprint C: LCT pair lifecycle endpoints.
        // Request / confirm / revoke are signed-envelope acts; list /
        // detail are public reads (chapter law gates later).
        .route("/v1/hubs/:hub_id/pairs/request", post(submit_pair_request))
        .route("/v1/hubs/:hub_id/pairs/:pair_id/confirm", post(submit_pair_confirm))
        .route("/v1/hubs/:hub_id/pairs/:pair_id/revoke", post(submit_pair_revoke))
        .route("/v1/hubs/:hub_id/pairs", get(list_pairs))
        .route("/v1/hubs/:hub_id/pairs/:pair_id", get(get_pair))
        // PAIRED-CHANNELS Sprint D: message relay on a confirmed pair.
        .route("/v1/hubs/:hub_id/pairs/:pair_id/messages",
               post(post_pair_message).get(get_pair_messages))
        .route("/v1/admin/reload-law", post(reload_law))
        .with_state(state)
}

// ---------- error wrapper ----------

#[derive(Debug)]
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
    /// The hub's LCT public key (hex) — the ECDH peer a member uses to open
    /// an E2E member↔hub channel. `None` if the signer can't expose it
    /// (e.g. Hestia mode). Public, integrity-protecting only (not a secret).
    #[serde(skip_serializing_if = "Option::is_none")]
    hub_pubkey_hex: Option<String>,
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
        hub_pubkey_hex: s.signer.public_key().map(|pk| pk.to_hex()),
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
    UpdateProfile {
        member_lct_id: Uuid,
        fields: std::collections::BTreeMap<String, String>,
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
        EnvelopeAction::UpdateProfile { member_lct_id, fields } => {
            // Same self-only rule as DeclareSkill: members update only their
            // own profile (signer == subject); Sovereign may update any
            // member's (operator convenience / seeding).
            if !signer_is_sovereign && envelope.signer_lct_id != member_lct_id {
                return Err(ApiError::unauthorized(format!(
                    "members may only update their own profile (signer {} != subject {})",
                    envelope.signer_lct_id, member_lct_id,
                )));
            }
            HubEvent::MemberProfileUpdated {
                member_lct_id,
                fields,
                updated_by: envelope.signer_lct_id,
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
                        "act denied by hub law (norm: {})",
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

// ---------- POST /v1/hubs/{id}/channel (E2E member↔hub channel) ----------
//
// Citizen-tier reads/acts never travel in the clear. The member seals a
// request to the hub's LCT (X25519 ECDH from identity keys → ChaCha20-Poly1305,
// `web4_core::pair_channel`); the hub opens it (a successful AEAD open both
// AUTHENTICATES the caller — only the holder of their private key could have
// sealed it — and decrypts), runs the authz pipeline, and seals the response
// back. v1 serves citizen-tier reads; PolicyEntity-on-reads + MRH/trust/
// constellation scoping layer onto `dispatch_channel`.

#[derive(Deserialize)]
struct ChannelRequest {
    caller_lct_id: Uuid,
    pair_id: Uuid,
    /// base64(nonce ‖ ciphertext) sealed to the hub's LCT pubkey.
    sealed: String,
    /// For an **external** caller (not yet a member, so no pinned pubkey): the
    /// self-vouched pubkey to ECDH against. The hub uses it to open the
    /// channel (a successful open proves key possession) but only honors the
    /// `request_citizenship` action — the external→citizen bootstrap, encrypted.
    /// Members ignore this (their pinned pubkey is authoritative).
    #[serde(default)]
    caller_pubkey_hex: Option<String>,
}

#[derive(Serialize)]
struct ChannelResponse {
    sealed: String,
}

/// The decrypted inner request: a tool name + free-form args, mirroring the
/// MCP read surface.
#[derive(Deserialize)]
struct ChannelInner {
    tool: String,
    #[serde(default)]
    args: serde_json::Value,
}

async fn channel_request(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
    Json(req): Json<ChannelRequest>,
) -> Result<Json<ChannelResponse>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!("unknown hub {hub_id}")));
    }

    // Resolve the caller's pubkey: a member's is pinned (authoritative); an
    // external caller (not yet a member) self-vouches one in caller_pubkey_hex,
    // which only unlocks the request_citizenship action below. A successful
    // channel_open authenticates either way (only the key holder could seal).
    let caller_pubkey = {
        let resolver = s.resolver.read().await;
        match resolver.lookup(req.caller_lct_id).map(|lct| lct.public_key) {
            Some(pinned) => pinned,
            None => match req.caller_pubkey_hex.as_deref() {
                Some(hex) => hub_lib::hub::hestia_sovereign_lct(req.caller_lct_id, hex)
                    .map_err(|e| ApiError::bad_request(format!("invalid caller_pubkey_hex: {e}")))?
                    .public_key,
                None => return Err(ApiError::unauthorized(
                    "caller LCT not known to this hub — include caller_pubkey_hex to request citizenship".to_string(),
                )),
            },
        }
    };

    // Open = authenticate (AEAD proves key possession) + decrypt, in one step.
    let plaintext = s.signer
        .channel_open(&caller_pubkey, req.pair_id, &req.sealed)
        .map_err(|_| ApiError::unauthorized(
            "channel authentication/decryption failed".to_string(),
        ))?;
    let inner: ChannelInner = serde_json::from_slice(&plaintext)
        .map_err(|e| ApiError::bad_request(format!("malformed channel request: {e}")))?;

    // Authz + dispatch on the decrypted request.
    let response = dispatch_channel(&s, req.caller_lct_id, req.pair_id, req.caller_pubkey_hex.clone(), inner).await?;

    // Seal the response back over the same channel.
    let body = serde_json::to_vec(&response)
        .map_err(|e| ApiError::internal(anyhow::anyhow!("serializing response: {e}")))?;
    let sealed = s.signer
        .channel_seal(&caller_pubkey, req.pair_id, &body)
        .map_err(|e| ApiError::internal(anyhow::anyhow!("sealing response: {e}")))?;

    Ok(Json(ChannelResponse { sealed }))
}

/// Per-tier default cap on how many member records one read may return. The
/// MRH bound at the result layer: a citizen can't bulk-enumerate the whole
/// membership; the Sovereign is unbounded. v1 default — chapter law / config
/// will own this value, and a higher trust score or a verified constellation
/// (MFA) will raise it once those subsystems land.
const CITIZEN_READ_LIMIT: usize = 50;

/// Read scope: who is asking + how much they may see. v1 enforces result
/// bounding by tier. `assurance` (single LCT vs verified constellation) and a
/// trust floor are the hooks the constellation / T3-V3 layers attach to — not
/// yet enforced (those subsystems don't exist yet), but threaded here so they
/// slot in without re-touching the read handlers.
struct ReadScope {
    #[allow(dead_code)] // surfaced for the future trust/constellation layers
    role: &'static str,
    /// None = unbounded (Sovereign); Some(n) = at most n records.
    max_results: Option<usize>,
}

impl ReadScope {
    fn for_role(role: &'static str) -> Self {
        let max_results = match role {
            "sovereign" => None,
            _ => Some(CITIZEN_READ_LIMIT),
        };
        ReadScope { role, max_results }
    }

    /// Effective record count: honor the caller's requested `limit` but never
    /// exceed the tier cap.
    fn effective_limit(&self, requested: Option<usize>) -> Option<usize> {
        match (self.max_results, requested) {
            (None, r) => r,
            (Some(cap), Some(r)) => Some(r.min(cap)),
            (Some(cap), None) => Some(cap),
        }
    }
}

/// Tier resolution + dispatch for a decrypted channel request.
/// Tiers: Sovereign / citizen (member) → reads; **external** (authenticated
/// LCT, not yet a member) → only `request_citizenship`. Finer role/trust/
/// constellation gating layers on here.
async fn dispatch_channel(
    s: &RestState,
    caller_lct_id: Uuid,
    pair_id: Uuid,
    caller_pubkey_hex: Option<String>,
    inner: ChannelInner,
) -> Result<serde_json::Value, ApiError> {
    let state = {
        let ledger = s.ledger.lock().await;
        HubState::project(&ledger)
    };

    // Tier resolution.
    let role = if caller_lct_id == s.sovereign_lct_id {
        "sovereign"
    } else if state.members.contains_key(&caller_lct_id) {
        "citizen"
    } else {
        // External tier: an authenticated LCT that isn't a member. The only
        // thing it may do is request citizenship (the encrypted external→citizen
        // bootstrap). Everything else is refused.
        if inner.tool == "request_citizenship" {
            return request_citizenship(s, caller_lct_id, caller_pubkey_hex, &inner.args).await;
        }
        return Err(ApiError {
            status: StatusCode::FORBIDDEN,
            message: "external LCTs may only request citizenship".to_string(),
        });
    };

    // PolicyEntity-on-reads: chapter law decides whether this tier may run
    // this read (default-open when no law / no matching norm).
    gate_read(s, role, inner.tool.as_str()).await?;

    // Scoping: bound how much this tier may see (MRH at the result layer).
    let scope = ReadScope::for_role(role);
    let requested = inner.args.get("limit").and_then(|v| v.as_u64()).map(|n| n as usize);
    let limit = scope.effective_limit(requested);

    match inner.tool.as_str() {
        "query_hub" => Ok(serde_json::json!({
            "hub_name": state.hub_name,
            "member_count": state.member_count(),
            "last_ledger_index": state.last_index,
        })),
        "list_members" => {
            let all: Vec<&hub_lib::state::Member> = state.members.values().collect();
            let total = all.len();
            let shown: Vec<&hub_lib::state::Member> = match limit {
                Some(n) => all.into_iter().take(n).collect(),
                None => all,
            };
            Ok(serde_json::json!({
                "members": shown,
                "total": total,
                "truncated": total > limit.unwrap_or(total),
            }))
        }
        "find_skill" => {
            let q = inner.args.get("q").and_then(|v| v.as_str()).unwrap_or("").to_lowercase();
            let matches: Vec<&hub_lib::state::Member> = state.members.values()
                .filter(|m| m.skills.iter().any(|sk| sk.contains(&q)))
                .collect();
            let total = matches.len();
            let shown: Vec<&hub_lib::state::Member> = match limit {
                Some(n) => matches.into_iter().take(n).collect(),
                None => matches,
            };
            Ok(serde_json::json!({
                "members": shown,
                "total": total,
                "truncated": total > limit.unwrap_or(total),
            }))
        }
        "find_members" => {
            // Semantic member discovery. The hub is the front door (gating +
            // tier scoping happen here); membot is the engine (the sidecar does
            // the embedding + 3-signal search). top_k is bounded by the tier cap.
            let query = inner.args.get("query").and_then(|v| v.as_str()).unwrap_or("");
            if query.trim().is_empty() {
                return Err(ApiError::bad_request("find_members requires a 'query'".to_string()));
            }
            let requested = inner.args.get("top_k").and_then(|v| v.as_u64()).map(|n| n as usize);
            let effective = scope.effective_limit(requested.or(Some(12))).unwrap_or(12);
            let temperature = inner.args.get("temperature").and_then(|v| v.as_f64()).unwrap_or(0.0);
            let hits = membox_find_members(query, effective, temperature).await?;
            Ok(serde_json::json!({
                "results": hits,
                "total": hits.len(),
                "temperature": temperature,
            }))
        }
        // Reserved registration slot for membot's Walk-as-MCP (ships ~2026-06-12):
        // when it lands it's a register-and-gate, not a reimplement. Same role
        // gating + tier scoping as find_members applies (gate_read already ran).
        "walk_members" => Err(ApiError {
            status: StatusCode::NOT_IMPLEMENTED,
            message: "walk_members is reserved for membot's Walk-as-MCP (not yet shipped)".to_string(),
        }),
        // ---- introductions (the consent half of discovery) ----
        // Both halves ride the sealed channel, so by construction both parties
        // hold pinned channel keys by the time an intro is accepted — which is
        // exactly what makes the mutual-approval payoff (each side getting the
        // other's pubkey for a direct member↔member pair_channel) possible.
        "request_intro" => {
            let to: Uuid = inner.args.get("to").and_then(|v| v.as_str())
                .and_then(|s| s.parse().ok())
                .ok_or_else(|| ApiError::bad_request("request_intro requires 'to' (member LCT uuid)".to_string()))?;
            // purpose is optional free text — and ledger-witnessed; keep it brief.
            let purpose = inner.args.get("purpose").and_then(|v| v.as_str()).map(String::from);
            if to == caller_lct_id {
                return Err(ApiError::bad_request("cannot request an intro to yourself".to_string()));
            }
            if !state.members.contains_key(&to) {
                return Err(ApiError::bad_request(format!("{to} is not a member of this hub")));
            }
            let dup = state.intros.values().any(|i| {
                i.status == hub_lib::state::IntroStatus::Pending
                    && i.from_lct == caller_lct_id
                    && i.to_lct == to
            });
            if dup {
                return Err(ApiError::bad_request("an intro to that member is already pending".to_string()));
            }
            let intro_id = Uuid::new_v4();
            let event = HubEvent::IntroRequested {
                intro_id,
                from_lct: caller_lct_id,
                to_lct: to,
                purpose,
            };
            let (index, _hash) = commit_pair_event(s, event).await?;
            Ok(serde_json::json!({ "intro_id": intro_id, "status": "pending", "entry_index": index }))
        }
        "list_intros" => {
            // Only intros the caller is a party to — never the full table.
            let mine: Vec<serde_json::Value> = state.intros.values()
                .filter(|i| i.from_lct == caller_lct_id || i.to_lct == caller_lct_id)
                .map(|i| {
                    let mut v = serde_json::json!({
                        "intro_id": i.id,
                        "from_lct": i.from_lct,
                        "to_lct": i.to_lct,
                        "purpose": i.purpose,
                        "status": i.status,
                    });
                    // The mutual-approval payoff: once accepted, each party
                    // gets the OTHER party's pinned pubkey — everything a
                    // direct member↔member pair_channel needs.
                    if i.status == hub_lib::state::IntroStatus::Accepted {
                        let peer = if i.from_lct == caller_lct_id { i.to_lct } else { i.from_lct };
                        v["peer_lct"] = serde_json::json!(peer);
                        v["peer_pubkey_hex"] = serde_json::json!(state.member_pubkeys.get(&peer));
                    }
                    v
                })
                .collect();
            Ok(serde_json::json!({ "intros": mine, "total": mine.len() }))
        }
        "respond_intro" => {
            let intro_id: Uuid = inner.args.get("intro_id").and_then(|v| v.as_str())
                .and_then(|s| s.parse().ok())
                .ok_or_else(|| ApiError::bad_request("respond_intro requires 'intro_id'".to_string()))?;
            let accept = inner.args.get("accept").and_then(|v| v.as_bool())
                .ok_or_else(|| ApiError::bad_request("respond_intro requires 'accept' (bool)".to_string()))?;
            let intro = state.intros.get(&intro_id)
                .ok_or_else(|| ApiError::bad_request(format!("unknown intro {intro_id}")))?;
            if intro.to_lct != caller_lct_id {
                return Err(ApiError {
                    status: StatusCode::FORBIDDEN,
                    message: "only the intro's target may respond".to_string(),
                });
            }
            if intro.status != hub_lib::state::IntroStatus::Pending {
                return Err(ApiError::bad_request("intro is already resolved".to_string()));
            }
            let from = intro.from_lct;
            let event = HubEvent::IntroResponded { intro_id, responded_by: caller_lct_id, accepted: accept };
            let (index, _hash) = commit_pair_event(s, event).await?;
            let mut out = serde_json::json!({
                "intro_id": intro_id,
                "status": if accept { "accepted" } else { "declined" },
                "entry_index": index,
            });
            if accept {
                out["peer_lct"] = serde_json::json!(from);
                out["peer_pubkey_hex"] = serde_json::json!(state.member_pubkeys.get(&from));
            }
            Ok(out)
        }
        // ---- constellation attestation (challenge-response MFA, assurance tiers) ----
        // Wire contract: forum/legion-constellation-attestation-wire-shape-2026-06-11.md.
        // Member side ships in hestia (core/src/constellation.rs); this is the
        // verifier half. The derived tier binds to THIS pair_id — it's the
        // `assurance` hook ReadScope already reserves.
        "constellation_challenge" => {
            let nonce = s.constellations.mint_challenge(pair_id);
            Ok(serde_json::json!({ "nonce": nonce }))
        }
        "present_constellation" => {
            let att: hub_lib::constellation::ConstellationAttestation =
                serde_json::from_value(inner.args.clone())
                    .map_err(|e| ApiError::bad_request(format!("malformed attestation: {e}")))?;
            // The attestation must be bound to the channel identity: its owner
            // key is checked against the caller's PINNED resolver pubkey. No
            // pinned key (never enrolled via set-member-key/admission) = reject,
            // never fall back to a self-carried key.
            let pinned = {
                let resolver = s.resolver.read().await;
                resolver.lookup(caller_lct_id).map(|lct| lct.public_key.to_hex())
            };
            let Some(pinned) = pinned else {
                return Err(ApiError {
                    status: StatusCode::FORBIDDEN,
                    message: "no pinned key for this member — enroll a key before presenting a constellation".to_string(),
                });
            };
            use hub_lib::constellation::VerifyError;
            let binding = s.constellations
                .present(pair_id, &att, &pinned, chrono::Utc::now())
                .map_err(|e| match e {
                    // A foreign owner key on an authenticated channel is an
                    // authorization failure (memo rule 3: reject, not warn).
                    VerifyError::ForeignOwnerKey => ApiError {
                        status: StatusCode::FORBIDDEN,
                        message: e.to_string(),
                    },
                    other => ApiError::bad_request(other.to_string()),
                })?;
            Ok(serde_json::json!({
                "assurance": binding.assurance,
                "valid_until": binding.valid_until,
            }))
        }
        other => Err(ApiError::bad_request(format!("unknown or non-channel tool: {other}"))),
    }
}

/// Call the local membox sidecar (the discovery engine) for semantic member
/// search. The hub composes membot as a localhost dependency; this never faces
/// the network. A sidecar that's down → 503 with a clear message (discovery
/// degraded, the rest of the hub is fine).
async fn membox_find_members(
    query: &str,
    top_k: usize,
    temperature: f64,
) -> Result<Vec<serde_json::Value>, ApiError> {
    let base = std::env::var("WEB4_MEMBOX_URL")
        .unwrap_or_else(|_| "http://127.0.0.1:8771".to_string());
    let client = reqwest::Client::new();
    let resp = client
        .post(format!("{}/find_members", base.trim_end_matches('/')))
        .json(&serde_json::json!({ "query": query, "top_k": top_k, "temperature": temperature }))
        .send()
        .await
        .map_err(|e| ApiError {
            status: StatusCode::SERVICE_UNAVAILABLE,
            message: format!("member-discovery engine unreachable: {e}"),
        })?;
    if !resp.status().is_success() {
        let code = resp.status();
        let body = resp.text().await.unwrap_or_default();
        return Err(ApiError {
            status: StatusCode::BAD_GATEWAY,
            message: format!("discovery engine returned {code}: {body}"),
        });
    }
    let body: serde_json::Value = resp
        .json()
        .await
        .map_err(|e| ApiError::internal(anyhow::anyhow!("parsing discovery response: {e}")))?;
    Ok(body
        .get("results")
        .and_then(|r| r.as_array())
        .cloned()
        .unwrap_or_default())
}

/// External→citizen bootstrap over the channel. An authenticated external LCT
/// (proven by the successful channel_open) asks to become a member. Mirrors the
/// plaintext `/members/join` admission, but encrypted: PolicyEntity gates as
/// `role="applicant"`; on accept the Sovereign signs a MemberAdded pinning the
/// applicant's pubkey, and we add them to the resolver so their *next* channel
/// is as a citizen (no caller_pubkey_hex needed).
async fn request_citizenship(
    s: &RestState,
    caller_lct_id: Uuid,
    caller_pubkey_hex: Option<String>,
    args: &serde_json::Value,
) -> Result<serde_json::Value, ApiError> {
    let pubkey_hex = caller_pubkey_hex.ok_or_else(|| ApiError::bad_request(
        "request_citizenship requires the channel to carry caller_pubkey_hex".to_string(),
    ))?;
    // Reject if already a member (idempotency / no double-admit).
    {
        let ledger = s.ledger.lock().await;
        if HubState::project(&ledger).members.contains_key(&caller_lct_id) {
            return Ok(serde_json::json!({ "admitted": true, "already_member": true }));
        }
    }
    let name = args.get("name").and_then(|v| v.as_str()).map(String::from);
    let event = HubEvent::MemberAdded {
        member_lct_id: caller_lct_id,
        added_by: s.sovereign_lct_id,
        member_name: name,
        member_pubkey_hex: Some(pubkey_hex.clone()),
    };

    // PolicyEntity gate — admission policy from chapter law, role="applicant".
    {
        let law_guard = s.law.read().await;
        if let Some(law) = law_guard.as_ref() {
            let payload = serde_yaml::to_value(&event)
                .map_err(|e| ApiError::internal(anyhow::anyhow!("serializing event for R6: {e}")))?;
            let req = R6Request {
                role: "applicant".to_string(),
                action: "member_join_request".to_string(),
                payload,
                resource: Default::default(),
            };
            match law.evaluate_outcome(&req).decision {
                Decision::Allow => {}
                Decision::Deny => return Err(ApiError {
                    status: StatusCode::FORBIDDEN,
                    message: "citizenship denied by hub law".to_string(),
                }),
                Decision::Escalate => return Err(ApiError {
                    status: StatusCode::ACCEPTED,
                    message: "citizenship requires escalation (admin review)".to_string(),
                }),
            }
        }
    }

    // Sovereign-signs + commits the admission, then pins the new member's
    // pubkey so future channels authenticate them as a citizen.
    let (index, _hash) = commit_pair_event(s, event).await?;
    if let Ok(lct) = hub_lib::hub::hestia_sovereign_lct(caller_lct_id, &pubkey_hex) {
        s.resolver.write().await.insert(lct);
    }

    Ok(serde_json::json!({
        "admitted": true,
        "member_lct_id": caller_lct_id,
        "entry_index": index,
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
                        "membership denied by hub law (norm: {})",
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
/// PolicyEntity-on-reads (the read half of the §8 "PolicyEntity gates queries
/// the same way it gates writes" commitment). Evaluate a read of `tool` by a
/// caller in `role` against chapter law. No law → Allow (open-by-default, the
/// pre-gate behavior). Reads are namespaced `read:<tool>` in the action so
/// read norms don't collide with act (event-kind) norms. Pure + testable;
/// `gate_read` wires it to the live law slot + HTTP status codes.
fn read_decision(law: Option<&Law>, role: &str, tool: &str) -> DecisionOutcome {
    let Some(law) = law else {
        return DecisionOutcome {
            decision: Decision::Allow,
            winning_norm: None,
            escalation_index: None,
            escalate_to: None,
        };
    };
    let req = R6Request {
        role: role.to_string(),
        action: format!("read:{tool}"),
        payload: Default::default(),
        resource: Default::default(),
    };
    law.evaluate_outcome(&req)
}

/// Gate a channel read against chapter law. Allow → proceed; Deny → 403;
/// Escalate → 202 (the read is held pending the escalation target's review).
async fn gate_read(s: &RestState, role: &str, tool: &str) -> Result<(), ApiError> {
    let law_guard = s.law.read().await;
    let outcome = read_decision(law_guard.as_ref(), role, tool);
    match outcome.decision {
        Decision::Allow => Ok(()),
        Decision::Deny => Err(ApiError {
            status: StatusCode::FORBIDDEN,
            message: format!(
                "read '{tool}' denied by hub law (norm: {})",
                outcome.winning_norm.as_deref().unwrap_or("?")
            ),
        }),
        Decision::Escalate => Err(ApiError {
            status: StatusCode::ACCEPTED,
            message: format!(
                "read '{tool}' escalated to {} by hub law",
                outcome.escalate_to.as_deref().unwrap_or("sovereign")
            ),
        }),
    }
}

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
    let mut store = hub_lib::store::open_hub_store(&s.paths.root)
        .map_err(ApiError::internal)?;
    store.write_proposal(proposal).await
        .map_err(ApiError::internal)
}

async fn read_proposal(s: &RestState, id: Uuid) -> Result<Option<CouncilProposal>, ApiError> {
    let store = hub_lib::store::open_hub_store(&s.paths.root)
        .map_err(ApiError::internal)?;
    store.read_proposal(id).await
        .map_err(ApiError::internal)
}

async fn read_all_proposals(s: &RestState) -> Result<Vec<CouncilProposal>, ApiError> {
    let store = hub_lib::store::open_hub_store(&s.paths.root)
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

// ============================================================================
// PAIRED-CHANNELS Sprint C — pair lifecycle endpoints
// ============================================================================
//
// Three POST endpoints (request / confirm / revoke) and two GETs
// (list / detail). Reads are public-by-default; chapter law gates
// later. Writes are signed envelopes — same machinery as /v1/hubs/.../events.
//
// The hub never sees the ECDH shared secret — that's derived at the
// endpoints from their LCT keys (Sprint A). The hub only witnesses
// the lifecycle and (eventually, Sprint D) relays opaque ciphertext.

use hub_lib::state::{PairState, PairStatus};
use hub_lib::events::PairRevocationKind;

#[derive(Deserialize)]
struct PairRequestPayload {
    /// Discriminator inside the envelope payload (same shape as
    /// other action types). Required to be "pair_request".
    action: String,
    counterparty_lct_id: Uuid,
    purpose: String,
    #[serde(default)]
    expires_at: Option<chrono::DateTime<Utc>>,
    /// PAIRED-CHANNELS Sprint F: initiator's per-session X25519
    /// ephemeral public key (hex). If supplied AND the counterparty
    /// supplies theirs in pair_confirm, this pair's messages get
    /// forward secrecy.
    #[serde(default)]
    initiator_ephemeral_pub_hex: Option<String>,
}

#[derive(Deserialize)]
struct PairConfirmPayload {
    action: String, // "pair_confirm"
    pair_id: Uuid,
    /// PAIRED-CHANNELS Sprint F: counterparty's per-session X25519
    /// ephemeral public key (hex). Optional for back-compat.
    #[serde(default)]
    counterparty_ephemeral_pub_hex: Option<String>,
}

#[derive(Deserialize)]
struct PairRevokePayload {
    action: String, // "pair_revoke"
    pair_id: Uuid,
    #[serde(default = "default_revocation_kind")]
    revocation_kind: PairRevocationKind,
    #[serde(default)]
    reason: Option<String>,
}

fn default_revocation_kind() -> PairRevocationKind {
    PairRevocationKind::Voluntary
}

#[derive(Serialize)]
struct PairAccepted {
    pair_id: Uuid,
    entry_index: u64,
    entry_hash: String,
    status: PairStatus,
}

#[derive(Serialize)]
struct PairSummary {
    id: Uuid,
    initiator: Uuid,
    counterparty: Uuid,
    purpose: String,
    status: PairStatus,
    effective_status: &'static str,
    proposed_at: chrono::DateTime<Utc>,
    #[serde(skip_serializing_if = "Option::is_none")]
    confirmed_at: Option<chrono::DateTime<Utc>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    revoked_at: Option<chrono::DateTime<Utc>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    expires_at: Option<chrono::DateTime<Utc>>,
    message_count: u64,
    /// PAIRED-CHANNELS Sprint F: ephemeral public keys. Recipient
    /// reads counterparty_ephemeral_pub_hex from initiator's side
    /// and vice versa; both are needed to derive the v2 session key.
    #[serde(skip_serializing_if = "Option::is_none")]
    initiator_ephemeral_pub_hex: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    counterparty_ephemeral_pub_hex: Option<String>,
}

impl PairSummary {
    fn from_pair(p: &PairState, now: chrono::DateTime<Utc>) -> Self {
        Self {
            id: p.id,
            initiator: p.initiator,
            counterparty: p.counterparty,
            purpose: p.purpose.clone(),
            status: p.status,
            effective_status: p.effective_status(now),
            proposed_at: p.proposed_at,
            confirmed_at: p.confirmed_at,
            revoked_at: p.revoked_at,
            expires_at: p.expires_at,
            message_count: p.message_count,
            initiator_ephemeral_pub_hex: p.initiator_ephemeral_pub_hex.clone(),
            counterparty_ephemeral_pub_hex: p.counterparty_ephemeral_pub_hex.clone(),
        }
    }
}

/// Shared preamble for the three POST handlers: verify envelope,
/// reject if signer isn't a current member or the founding Sovereign,
/// reject if council mode active (consistency with /events behavior).
/// Returns the projected HubState (caller often needs it next).
async fn pair_endpoint_preamble(
    s: &RestState,
    envelope: &SignedEnvelope,
) -> Result<hub_lib::state::HubState, ApiError> {
    let resolver_guard = s.resolver.read().await;
    let _redeemed = verify_envelope(envelope, &s.nonces, &*resolver_guard, Utc::now())?;
    drop(resolver_guard);

    let projected = {
        let ledger = s.ledger.lock().await;
        hub_lib::state::HubState::project(&*ledger)
    };

    let is_sov = envelope.signer_lct_id == s.sovereign_lct_id;
    let is_member = projected.members.contains_key(&envelope.signer_lct_id);
    if !is_sov && !is_member {
        return Err(ApiError::unauthorized(format!(
            "signer {} is neither the founding Sovereign nor a current member",
            envelope.signer_lct_id
        )));
    }

    // Same council gate as /events for consistency. In council mode,
    // pair acts go through the propose/sign flow like everything else.
    if matches!(projected.council_threshold, Some((m, _)) if m >= 2) {
        return Err(ApiError {
            status: StatusCode::CONFLICT,
            message: "council mode active (threshold >= 2-of-N): submit pair acts via \
                      POST /v1/hubs/{hub_id}/council/propose + /sign".into(),
        });
    }

    Ok(projected)
}

async fn submit_pair_request(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
    Json(envelope): Json<SignedEnvelope>,
) -> Result<Json<PairAccepted>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }
    let projected = pair_endpoint_preamble(&s, &envelope).await?;

    let payload: PairRequestPayload = serde_json::from_value(envelope.payload.clone())
        .map_err(|e| ApiError::bad_request(format!("payload not a pair_request: {}", e)))?;
    if payload.action != "pair_request" {
        return Err(ApiError::bad_request(format!(
            "expected action=pair_request, got {}", payload.action
        )));
    }

    // Counterparty must be a current member (or the Sovereign) — we
    // can't pair with someone we don't know how to deliver to.
    let cp_known = payload.counterparty_lct_id == s.sovereign_lct_id
        || projected.members.contains_key(&payload.counterparty_lct_id);
    if !cp_known {
        return Err(ApiError::bad_request(format!(
            "counterparty {} is not a current member; only known LCTs can be paired with",
            payload.counterparty_lct_id
        )));
    }
    // Self-pairs are pointless.
    if payload.counterparty_lct_id == envelope.signer_lct_id {
        return Err(ApiError::bad_request(
            String::from("self-pair (initiator == counterparty) is not allowed")
        ));
    }

    let pair_id = Uuid::new_v4();
    let event = HubEvent::PairingRequested {
        pair_id,
        initiator_lct_id: envelope.signer_lct_id,
        counterparty_lct_id: payload.counterparty_lct_id,
        purpose: payload.purpose,
        proposed_at: Utc::now(),
        expires_at: payload.expires_at,
        initiator_ephemeral_pub_hex: payload.initiator_ephemeral_pub_hex,
    };

    // PolicyEntity gate (V2-8 §4): chapter law can pattern-match
    // `r6.request.action == "pairing_requested"` and gate by purpose,
    // counterparty role, initiator role, etc.
    let law_guard = s.law.read().await;
    if let Some(law) = law_guard.as_ref() {
        let req = build_r6_request(&envelope, &event, s.sovereign_lct_id)
            .map_err(ApiError::internal)?;
        match law.evaluate_outcome(&req).decision {
            Decision::Allow => {}
            Decision::Deny => {
                return Err(ApiError {
                    status: StatusCode::FORBIDDEN,
                    message: "pair_request denied by hub law".into(),
                });
            }
            Decision::Escalate => {
                return Err(ApiError {
                    status: StatusCode::ACCEPTED,
                    message: "pair_request escalated to council; use propose/sign".into(),
                });
            }
        }
    }
    drop(law_guard);

    let (entry_index, entry_hash) = commit_pair_event(&s, event).await?;
    Ok(Json(PairAccepted {
        pair_id,
        entry_index,
        entry_hash,
        status: PairStatus::Pending,
    }))
}

async fn submit_pair_confirm(
    State(s): State<RestState>,
    Path((hub_id, pair_id)): Path<(Uuid, Uuid)>,
    Json(envelope): Json<SignedEnvelope>,
) -> Result<Json<PairAccepted>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }
    let projected = pair_endpoint_preamble(&s, &envelope).await?;

    let payload: PairConfirmPayload = serde_json::from_value(envelope.payload.clone())
        .map_err(|e| ApiError::bad_request(format!("payload not a pair_confirm: {}", e)))?;
    if payload.action != "pair_confirm" || payload.pair_id != pair_id {
        return Err(ApiError::bad_request(
            String::from("pair_id in path must match payload + action must be pair_confirm")
        ));
    }

    let pair = projected.pairs.get(&pair_id)
        .ok_or_else(|| ApiError::not_found(format!("pair {} not found", pair_id)))?;
    if pair.status != PairStatus::Pending {
        return Err(ApiError {
            status: StatusCode::CONFLICT,
            message: format!("pair {} is {:?}, not Pending; cannot confirm", pair_id, pair.status),
        });
    }
    // Only the counterparty can confirm.
    if envelope.signer_lct_id != pair.counterparty {
        return Err(ApiError::unauthorized(format!(
            "only the counterparty ({}) may confirm pair {}; got {}",
            pair.counterparty, pair_id, envelope.signer_lct_id
        )));
    }

    let event = HubEvent::PairingConfirmed {
        pair_id,
        confirmed_by: envelope.signer_lct_id,
        counterparty_ephemeral_pub_hex: payload.counterparty_ephemeral_pub_hex,
    };
    let (entry_index, entry_hash) = commit_pair_event(&s, event).await?;
    Ok(Json(PairAccepted {
        pair_id,
        entry_index,
        entry_hash,
        status: PairStatus::Active,
    }))
}

async fn submit_pair_revoke(
    State(s): State<RestState>,
    Path((hub_id, pair_id)): Path<(Uuid, Uuid)>,
    Json(envelope): Json<SignedEnvelope>,
) -> Result<Json<PairAccepted>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }
    let projected = pair_endpoint_preamble(&s, &envelope).await?;

    let payload: PairRevokePayload = serde_json::from_value(envelope.payload.clone())
        .map_err(|e| ApiError::bad_request(format!("payload not a pair_revoke: {}", e)))?;
    if payload.action != "pair_revoke" || payload.pair_id != pair_id {
        return Err(ApiError::bad_request(
            String::from("pair_id in path must match payload + action must be pair_revoke")
        ));
    }

    let pair = projected.pairs.get(&pair_id)
        .ok_or_else(|| ApiError::not_found(format!("pair {} not found", pair_id)))?;
    if pair.status == PairStatus::Revoked {
        return Err(ApiError {
            status: StatusCode::CONFLICT,
            message: format!("pair {} already revoked", pair_id),
        });
    }
    // Either party (or the founding Sovereign, as operator override)
    // can revoke. Chapter law could further restrict; today no law
    // norms target pairing_revoked yet.
    let is_party = envelope.signer_lct_id == pair.initiator
        || envelope.signer_lct_id == pair.counterparty;
    let is_sov = envelope.signer_lct_id == s.sovereign_lct_id;
    if !is_party && !is_sov {
        return Err(ApiError::unauthorized(format!(
            "signer {} is neither a party to pair {} nor the founding Sovereign",
            envelope.signer_lct_id, pair_id
        )));
    }

    let event = HubEvent::PairingRevoked {
        pair_id,
        revoked_by: envelope.signer_lct_id,
        revocation_kind: payload.revocation_kind,
        reason: payload.reason,
    };
    let (entry_index, entry_hash) = commit_pair_event(&s, event).await?;
    Ok(Json(PairAccepted {
        pair_id,
        entry_index,
        entry_hash,
        status: PairStatus::Revoked,
    }))
}

async fn list_pairs(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
    axum::extract::Query(q): axum::extract::Query<ListPairsQuery>,
) -> Result<Json<Vec<PairSummary>>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }
    let projected = {
        let ledger = s.ledger.lock().await;
        hub_lib::state::HubState::project(&*ledger)
    };
    let now = Utc::now();
    let mut pairs: Vec<_> = projected.pairs.values()
        .filter(|p| match q.r#for {
            Some(lct) => p.includes(lct),
            None => true,
        })
        .map(|p| PairSummary::from_pair(p, now))
        .collect();
    // Newest-first by proposed_at for stable, useful ordering.
    pairs.sort_by(|a, b| b.proposed_at.cmp(&a.proposed_at));
    Ok(Json(pairs))
}

#[derive(Deserialize)]
struct ListPairsQuery {
    #[serde(default)]
    r#for: Option<Uuid>,
}

async fn get_pair(
    State(s): State<RestState>,
    Path((hub_id, pair_id)): Path<(Uuid, Uuid)>,
) -> Result<Json<PairSummary>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }
    let projected = {
        let ledger = s.ledger.lock().await;
        hub_lib::state::HubState::project(&*ledger)
    };
    let pair = projected.pairs.get(&pair_id)
        .ok_or_else(|| ApiError::not_found(format!("pair {} not found", pair_id)))?;
    Ok(Json(PairSummary::from_pair(pair, Utc::now())))
}

// ---------- PAIRED-CHANNELS Sprint D: message relay ----------

use hub_lib::pair_message::PairMessage;

#[derive(Deserialize)]
struct PairMessagePayload {
    action: String, // "pair_message"
    pair_id: Uuid,
    /// Sprint D: plaintext. Sprint E: base64-encoded ciphertext.
    /// Wire shape unchanged.
    body: String,
}

#[derive(Serialize)]
struct PairMessageAccepted {
    pair_id: Uuid,
    seq: u64,
    entry_index: u64,
    entry_hash: String,
    payload_hash: String,
}

async fn post_pair_message(
    State(s): State<RestState>,
    Path((hub_id, pair_id)): Path<(Uuid, Uuid)>,
    Json(envelope): Json<SignedEnvelope>,
) -> Result<Json<PairMessageAccepted>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }
    // Envelope verify + member check + council gate via the same preamble
    // pair_request / confirm / revoke use.
    let projected = pair_endpoint_preamble(&s, &envelope).await?;

    let payload: PairMessagePayload = serde_json::from_value(envelope.payload.clone())
        .map_err(|e| ApiError::bad_request(format!("payload not a pair_message: {}", e)))?;
    if payload.action != "pair_message" || payload.pair_id != pair_id {
        return Err(ApiError::bad_request(
            String::from("pair_id in path must match payload + action must be pair_message")
        ));
    }

    let pair = projected.pairs.get(&pair_id)
        .ok_or_else(|| ApiError::not_found(format!("pair {} not found", pair_id)))?;
    // Must be Active to relay (use effective_status so expired pairs
    // are rejected even though stored status is Active).
    let eff = pair.effective_status(Utc::now());
    if eff != "active" {
        return Err(ApiError {
            status: StatusCode::CONFLICT,
            message: format!("pair {} is {}; messages can only be relayed on active pairs",
                pair_id, eff),
        });
    }
    // Signer must be one of the two parties — no third-party injection.
    let is_party = envelope.signer_lct_id == pair.initiator
        || envelope.signer_lct_id == pair.counterparty;
    if !is_party {
        return Err(ApiError::unauthorized(format!(
            "signer {} is not a party to pair {}", envelope.signer_lct_id, pair_id
        )));
    }

    // Compute seq: the pair's current message_count IS the next seq
    // (0-indexed). Hub holds the ledger lock during the
    // build_entry → commit window, so concurrent posts to the same
    // pair serialize naturally — the append_signed stale-detection
    // would catch any race anyway.
    let seq = pair.message_count;
    let now = Utc::now();
    let payload_hash = PairMessage::payload_hash(&payload.body);

    // 1. Append the message to the sidecar BEFORE the ledger event.
    //    If sidecar write fails, no ledger event → no message_count
    //    bump → consistent. If ledger commit fails after sidecar
    //    write, we have an orphan sidecar entry (recoverable: next
    //    post with the same seq will fail the conditional/append
    //    detection). Acceptable for MVP; Sprint E will add atomicity
    //    if needed via a HubStore::tx_pair_message helper.
    let msg = PairMessage {
        pair_id,
        seq,
        from: envelope.signer_lct_id,
        posted_at: now,
        payload: payload.body,
        ephemeral_pub_hex: None,
    };
    {
        let mut store = hub_lib::store::open_hub_store(&s.paths.root)
            .map_err(ApiError::internal)?;
        store.append_pair_message(&msg).await
            .map_err(ApiError::internal)?;
    }

    // 2. Commit the ledger event so the projection bumps
    //    message_count + the witness chain records the metadata.
    let event = HubEvent::PairMessagePosted {
        pair_id,
        seq,
        from: envelope.signer_lct_id,
        posted_at: now,
        payload_hash: payload_hash.clone(),
    };
    let (entry_index, entry_hash) = commit_pair_event(&s, event).await?;

    Ok(Json(PairMessageAccepted {
        pair_id,
        seq,
        entry_index,
        entry_hash,
        payload_hash,
    }))
}

#[derive(Deserialize)]
struct PairMessagesQuery {
    /// Return only messages with seq strictly greater than this.
    /// Polling clients pass the last seq they saw.
    #[serde(default)]
    since: Option<u64>,
}

#[derive(Serialize)]
struct PairMessagesResponse {
    pair_id: Uuid,
    count: usize,
    messages: Vec<PairMessage>,
}

async fn get_pair_messages(
    State(s): State<RestState>,
    Path((hub_id, pair_id)): Path<(Uuid, Uuid)>,
    axum::extract::Query(q): axum::extract::Query<PairMessagesQuery>,
) -> Result<Json<PairMessagesResponse>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }
    // Pair must exist (don't leak which pair_ids exist via empty 200).
    {
        let ledger = s.ledger.lock().await;
        let projected = hub_lib::state::HubState::project(&*ledger);
        if !projected.pairs.contains_key(&pair_id) {
            return Err(ApiError::not_found(format!("pair {} not found", pair_id)));
        }
    }
    let store = hub_lib::store::open_hub_store(&s.paths.root)
        .map_err(ApiError::internal)?;
    let messages = store.list_pair_messages(pair_id, q.since).await
        .map_err(ApiError::internal)?;
    Ok(Json(PairMessagesResponse {
        pair_id,
        count: messages.len(),
        messages,
    }))
}

/// Commit a pair lifecycle event via the hub's signer (founding
/// Sovereign as executor). Same shape as `commit_proposed_event` —
/// hub signs the ledger entry; the pair's authorization is in the
/// envelope (verified above) + the event's fields (initiator_lct_id,
/// confirmed_by, revoked_by). Auditors correlate.
async fn commit_pair_event(s: &RestState, event: HubEvent) -> Result<(u64, String), ApiError> {
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
            event_kind: event_kind_str,
            event: event_value,
        };
        (unsigned, intent)
    };
    let signing_bytes = unsigned.signing_bytes.clone();
    let signature = s.signer
        .sign(s.sovereign_lct_id, &signing_bytes, &intent)
        .await
        .map_err(|e| ApiError::internal(anyhow::anyhow!("Sovereign signer denied/failed: {}", e)))?;
    let mut ledger = s.ledger.lock().await;
    let entry = ledger.append_signed(unsigned, signature).await
        .map_err(ApiError::internal)?;
    Ok((entry.index, entry.entry_hash.clone()))
}

#[cfg(test)]
mod read_gate_tests {
    use super::*;
    use hub_lib::law::Law;

    #[test]
    fn read_defaults_open_without_law() {
        // No chapter law → reads are open (pre-gate behavior preserved).
        assert_eq!(read_decision(None, "citizen", "list_members").decision, Decision::Allow);
        assert_eq!(read_decision(None, "sovereign", "find_skill").decision, Decision::Allow);
    }

    #[test]
    fn read_honors_a_deny_norm_and_leaves_others_open() {
        let yaml = r#"
version: "1.0.0"
norms:
  - id: NO-MEMBER-DUMP
    selector: r6.request.action
    operator: "=="
    value: "read:list_members"
    decision: deny
    priority: 10
    description: "Members are not bulk-listable over the channel"
"#;
        let law = Law::parse_and_validate(yaml).expect("valid law");
        // The denied read is denied for a citizen...
        let denied = read_decision(Some(&law), "citizen", "list_members");
        assert_eq!(denied.decision, Decision::Deny);
        assert_eq!(denied.winning_norm.as_deref(), Some("NO-MEMBER-DUMP"));
        // ...while an unlisted read stays open (default-allow).
        assert_eq!(read_decision(Some(&law), "citizen", "find_skill").decision, Decision::Allow);
    }

    #[test]
    fn read_can_escalate() {
        let yaml = r#"
version: "1.0.0"
norms:
  - id: SENSITIVE-QUERY
    selector: r6.request.action
    operator: "=="
    value: "read:query_hub"
    decision: escalate
    priority: 5
    description: "Hub-identity queries need Sovereign sign-off"
"#;
        let law = Law::parse_and_validate(yaml).expect("valid law");
        assert_eq!(read_decision(Some(&law), "citizen", "query_hub").decision, Decision::Escalate);
    }

    #[test]
    fn scope_bounds_citizens_and_not_the_sovereign() {
        let citizen = ReadScope::for_role("citizen");
        let sovereign = ReadScope::for_role("sovereign");
        // Citizen is capped; Sovereign is unbounded.
        assert_eq!(citizen.effective_limit(None), Some(CITIZEN_READ_LIMIT));
        assert_eq!(sovereign.effective_limit(None), None);
        // A citizen's requested limit is honored only up to the cap.
        assert_eq!(citizen.effective_limit(Some(5)), Some(5));
        assert_eq!(citizen.effective_limit(Some(10_000)), Some(CITIZEN_READ_LIMIT));
        // The Sovereign's requested limit is honored as-is.
        assert_eq!(sovereign.effective_limit(Some(5)), Some(5));
    }
}

/// End-to-end channel harness: a real RestState over a throwaway chapter, with
/// requests sealed by an external applicant via the same pair_channel primitive
/// the member side (hestia) uses. Exercises the full path — channel_open (authn)
/// → tier resolution → PolicyEntity → dispatch → seal response — that the unit
/// tests can't reach. The first RestState integration harness in this crate.
#[cfg(test)]
mod channel_e2e_tests {
    use super::*;
    use axum::extract::{Json, Path, State};
    use hub_lib::identity::IdentityFile;
    use hub_lib::init::{init_hub, InitArgs};
    use hub_lib::ledger::HubLedger;
    use hub_lib::store::open_hub_store;
    use tokio::sync::RwLock;
    use web4_core::crypto::{KeyPair, PublicKey};
    use web4_core::lct::EntityType;
    use web4_core::pair_channel::{self, Sealed};

    /// A throwaway Local-mode chapter + a RestState over it, optional law loaded.
    async fn fresh_rest_state(law_yaml: Option<&str>) -> (tempfile::TempDir, RestState) {
        let tmp = tempfile::tempdir().unwrap();
        let sov = tmp.path().join("sovereign.json");
        IdentityFile::generate(EntityType::Human).save(&sov).unwrap();
        let hub_dir = tmp.path().join("chapter");
        init_hub(InitArgs {
            hub_name: "E2E Test Hub".into(),
            hub_dir: hub_dir.clone(),
            sovereign_lct_path: sov,
            storage: None,
        })
        .await
        .unwrap();
        let law = Arc::new(RwLock::new(
            law_yaml.map(|y| Law::parse_and_validate(y).unwrap()),
        ));
        let store = open_hub_store(&hub_dir).unwrap();
        let ledger = Arc::new(Mutex::new(HubLedger::open(store).await.unwrap()));
        let state = RestState::open_with_law_and_ledger(hub_dir, law, ledger)
            .await
            .unwrap();
        (tmp, state)
    }

    fn seal_req(
        applicant: &KeyPair,
        hub_pub: &PublicKey,
        pair_id: Uuid,
        tool: &str,
        args: serde_json::Value,
    ) -> String {
        let inner = serde_json::json!({ "tool": tool, "args": args });
        let pt = serde_json::to_vec(&inner).unwrap();
        pair_channel::seal(applicant, hub_pub, pair_id, &pt)
            .unwrap()
            .to_base64()
    }

    fn open_resp(
        applicant: &KeyPair,
        hub_pub: &PublicKey,
        pair_id: Uuid,
        sealed_b64: &str,
    ) -> serde_json::Value {
        let sealed = Sealed::from_base64(sealed_b64).unwrap();
        let pt = pair_channel::open(applicant, hub_pub, pair_id, &sealed).unwrap();
        serde_json::from_slice(&pt).unwrap()
    }

    #[tokio::test]
    async fn external_bootstrap_then_citizen_read_over_channel() {
        let (_tmp, state) = fresh_rest_state(None).await; // open admission
        let hub_pub = state.signer.public_key().expect("local signer exposes a pubkey");
        let applicant = KeyPair::generate();
        let applicant_lct = Uuid::new_v4();
        let applicant_hex = applicant.verifying_key().to_hex();

        // 1. External tier → request_citizenship over a sealed channel, carrying
        //    a self-vouched pubkey. AEAD open authenticates; admission pins it.
        let pid = Uuid::new_v4();
        let sealed = seal_req(&applicant, &hub_pub, pid, "request_citizenship",
            serde_json::json!({ "name": "E2E Applicant" }));
        let req = ChannelRequest {
            caller_lct_id: applicant_lct,
            pair_id: pid,
            sealed,
            caller_pubkey_hex: Some(applicant_hex),
        };
        let resp = channel_request(State(state.clone()), Path(state.hub_id), Json(req))
            .await
            .expect("admission should succeed");
        let out = open_resp(&applicant, &hub_pub, pid, &resp.0.sealed);
        assert_eq!(out["admitted"], serde_json::json!(true));

        // 2. Now a citizen: a sealed list_members read returns the membership,
        //    and the channel needs NO caller_pubkey_hex (the pubkey is pinned).
        let pid2 = Uuid::new_v4();
        let sealed2 = seal_req(&applicant, &hub_pub, pid2, "list_members", serde_json::json!({}));
        let req2 = ChannelRequest {
            caller_lct_id: applicant_lct,
            pair_id: pid2,
            sealed: sealed2,
            caller_pubkey_hex: None,
        };
        let resp2 = channel_request(State(state.clone()), Path(state.hub_id), Json(req2))
            .await
            .expect("citizen read should succeed");
        let out2 = open_resp(&applicant, &hub_pub, pid2, &resp2.0.sealed);
        let members = out2["members"].as_array().expect("members array");
        assert!(
            members.iter().any(|m| m["lct_id"] == serde_json::json!(applicant_lct)),
            "the admitted applicant should appear in list_members"
        );
    }

    #[tokio::test]
    async fn admission_law_escalates_external_join() {
        // The live admission law: joins escalate to the Sovereign, not auto-admit.
        const LAW: &str = r#"
version: "1.0.0"
norms:
  - id: ADMISSION-REQUIRES-SOVEREIGN
    selector: r6.request.action
    operator: "=="
    value: member_join_request
    decision: escalate
    priority: 100
"#;
        let (_tmp, state) = fresh_rest_state(Some(LAW)).await;
        let hub_pub = state.signer.public_key().unwrap();
        let applicant = KeyPair::generate();
        let pid = Uuid::new_v4();
        let sealed = seal_req(&applicant, &hub_pub, pid, "request_citizenship",
            serde_json::json!({ "name": "Should Escalate" }));
        let req = ChannelRequest {
            caller_lct_id: Uuid::new_v4(),
            pair_id: pid,
            sealed,
            caller_pubkey_hex: Some(applicant.verifying_key().to_hex()),
        };
        let err = channel_request(State(state.clone()), Path(state.hub_id), Json(req))
            .await
            .err()
            .expect("join should be escalated, not admitted");
        assert_eq!(err.status, StatusCode::ACCEPTED, "escalate → 202");
    }

    #[tokio::test]
    async fn find_members_over_channel_then_degrades_when_engine_down() {
        use axum::{routing::post, Router};

        // Stand up a mock discovery engine (the membox sidecar's contract).
        let app = Router::new().route(
            "/find_members",
            post(|| async {
                axum::Json(serde_json::json!({
                    "results": [{ "member_lct": "657b6bc9", "name": "Ada", "score": 0.87 }],
                    "total": 1
                }))
            }),
        );
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let addr = listener.local_addr().unwrap();
        tokio::spawn(async move { axum::serve(listener, app).await.unwrap(); });
        std::env::set_var("WEB4_MEMBOX_URL", format!("http://{addr}"));

        let (_tmp, state) = fresh_rest_state(None).await; // open admission
        let hub_pub = state.signer.public_key().unwrap();
        let applicant = KeyPair::generate();
        let applicant_lct = Uuid::new_v4();

        // Admit so the caller is a citizen (find_members is citizen-gated).
        let pid = Uuid::new_v4();
        let sealed = seal_req(&applicant, &hub_pub, pid, "request_citizenship",
            serde_json::json!({ "name": "Caller" }));
        channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: applicant_lct, pair_id: pid, sealed,
            caller_pubkey_hex: Some(applicant.verifying_key().to_hex()),
        })).await.expect("admitted");

        // find_members over the channel → hub gates+scopes, calls the engine,
        // seals the ranked LCTs back.
        let pid2 = Uuid::new_v4();
        let sealed2 = seal_req(&applicant, &hub_pub, pid2, "find_members",
            serde_json::json!({ "query": "diffusion eval harness" }));
        let resp = channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: applicant_lct, pair_id: pid2, sealed: sealed2, caller_pubkey_hex: None,
        })).await.expect("find_members ok");
        let out = open_resp(&applicant, &hub_pub, pid2, &resp.0.sealed);
        assert_eq!(out["results"][0]["member_lct"], serde_json::json!("657b6bc9"));
        assert_eq!(out["total"], serde_json::json!(1));

        // Engine down → graceful 503, hub itself unaffected.
        std::env::set_var("WEB4_MEMBOX_URL", "http://127.0.0.1:1");
        let pid3 = Uuid::new_v4();
        let sealed3 = seal_req(&applicant, &hub_pub, pid3, "find_members",
            serde_json::json!({ "query": "anything" }));
        let err = channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: applicant_lct, pair_id: pid3, sealed: sealed3, caller_pubkey_hex: None,
        })).await.err().expect("engine-down should error");
        assert_eq!(err.status, StatusCode::SERVICE_UNAVAILABLE);

        std::env::remove_var("WEB4_MEMBOX_URL");
    }

    /// Seal+send one channel call for an admitted member; open the response.
    async fn member_call(
        state: &RestState,
        me: &KeyPair,
        my_lct: Uuid,
        tool: &str,
        args: serde_json::Value,
    ) -> Result<serde_json::Value, ApiError> {
        let hub_pub = state.signer.public_key().unwrap();
        let pid = Uuid::new_v4();
        let sealed = seal_req(me, &hub_pub, pid, tool, args);
        let resp = channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: my_lct, pair_id: pid, sealed, caller_pubkey_hex: None,
        })).await?;
        Ok(open_resp(me, &hub_pub, pid, &resp.0.sealed))
    }

    #[tokio::test]
    async fn intro_full_loop_mutual_approval_exchanges_pubkeys() {
        let (_tmp, state) = fresh_rest_state(None).await; // open admission
        let hub_pub = state.signer.public_key().unwrap();

        // Admit Alice and Bob over the channel (pins their pubkeys).
        let (alice, alice_lct) = (KeyPair::generate(), Uuid::new_v4());
        let (bob, bob_lct) = (KeyPair::generate(), Uuid::new_v4());
        for (kp, lct, name) in [(&alice, alice_lct, "Alice"), (&bob, bob_lct, "Bob")] {
            let pid = Uuid::new_v4();
            let sealed = seal_req(kp, &hub_pub, pid, "request_citizenship",
                serde_json::json!({ "name": name }));
            channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
                caller_lct_id: lct, pair_id: pid, sealed,
                caller_pubkey_hex: Some(kp.verifying_key().to_hex()),
            })).await.expect("admitted");
        }

        // Alice requests an intro to Bob.
        let out = member_call(&state, &alice, alice_lct, "request_intro",
            serde_json::json!({ "to": bob_lct, "purpose": "collab on evals" })).await.unwrap();
        assert_eq!(out["status"], serde_json::json!("pending"));
        let intro_id = out["intro_id"].as_str().unwrap().to_string();

        // Duplicate pending request is rejected.
        let dup = member_call(&state, &alice, alice_lct, "request_intro",
            serde_json::json!({ "to": bob_lct })).await;
        assert!(dup.is_err(), "duplicate pending intro must be rejected");

        // Bob sees it pending; Alice can't respond to her own request.
        let bob_list = member_call(&state, &bob, bob_lct, "list_intros", serde_json::json!({})).await.unwrap();
        assert_eq!(bob_list["total"], serde_json::json!(1));
        assert_eq!(bob_list["intros"][0]["status"], serde_json::json!("pending"));
        let not_target = member_call(&state, &alice, alice_lct, "respond_intro",
            serde_json::json!({ "intro_id": intro_id, "accept": true })).await;
        assert!(not_target.is_err(), "only the target may respond");

        // Bob accepts → gets Alice's pinned pubkey in the response.
        let acc = member_call(&state, &bob, bob_lct, "respond_intro",
            serde_json::json!({ "intro_id": intro_id, "accept": true })).await.unwrap();
        assert_eq!(acc["status"], serde_json::json!("accepted"));
        assert_eq!(acc["peer_pubkey_hex"], serde_json::json!(alice.verifying_key().to_hex()));

        // Alice's list now shows accepted + Bob's pinned pubkey — everything a
        // direct member↔member pair_channel needs.
        let alice_list = member_call(&state, &alice, alice_lct, "list_intros", serde_json::json!({})).await.unwrap();
        assert_eq!(alice_list["intros"][0]["status"], serde_json::json!("accepted"));
        assert_eq!(alice_list["intros"][0]["peer_pubkey_hex"], serde_json::json!(bob.verifying_key().to_hex()));

        // Already-resolved: a second response is rejected.
        let again = member_call(&state, &bob, bob_lct, "respond_intro",
            serde_json::json!({ "intro_id": intro_id, "accept": false })).await;
        assert!(again.is_err(), "resolved intro can't be re-responded");
    }

    use hub_lib::constellation::{
        signing_payload, AssuranceLevel, ConstellationAttestation, DeviceSignature, DeviceType,
    };

    /// Build + sign an attestation the way hestia's member side does.
    fn make_att(
        owner_kp: &KeyPair,
        owner_lct: Uuid,
        cosigners: &[(DeviceType, &KeyPair)],
        nonce: &str,
        issued_at: chrono::DateTime<chrono::Utc>,
    ) -> ConstellationAttestation {
        let roster: Vec<Uuid> = cosigners.iter().map(|_| Uuid::new_v4()).collect();
        let payload = signing_payload(owner_lct, &roster, nonce, &issued_at);
        ConstellationAttestation {
            owner_lct_id: owner_lct,
            owner_pubkey_hex: owner_kp.verifying_key().to_hex(),
            member_lcts: roster.clone(),
            challenge_nonce: nonce.to_string(),
            issued_at,
            claimed_assurance: AssuranceLevel::SingleDevice,
            owner_signature: owner_kp.sign(&payload).to_hex(),
            device_signatures: roster
                .iter()
                .zip(cosigners)
                .map(|(lct, (dt, kp))| DeviceSignature {
                    lct_id: *lct,
                    device_type: dt.clone(),
                    pubkey_hex: kp.verifying_key().to_hex(),
                    signature: kp.sign(&payload).to_hex(),
                })
                .collect(),
        }
    }

    /// One challenge → present round trip on a fixed pair_id. Both calls ride
    /// the same sealed channel the other tools use.
    async fn challenge_and_present(
        state: &RestState,
        me: &KeyPair,
        my_lct: Uuid,
        pid: Uuid,
        att_for_nonce: impl FnOnce(String) -> ConstellationAttestation,
    ) -> Result<serde_json::Value, ApiError> {
        let hub_pub = state.signer.public_key().unwrap();
        let sealed = seal_req(me, &hub_pub, pid, "constellation_challenge", serde_json::json!({}));
        let resp = channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: my_lct, pair_id: pid, sealed, caller_pubkey_hex: None,
        })).await?;
        let nonce = open_resp(me, &hub_pub, pid, &resp.0.sealed)["nonce"]
            .as_str().expect("challenge returns a nonce").to_string();

        let att = att_for_nonce(nonce);
        let sealed = seal_req(me, &hub_pub, pid, "present_constellation",
            serde_json::to_value(&att).unwrap());
        let resp = channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: my_lct, pair_id: pid, sealed, caller_pubkey_hex: None,
        })).await?;
        Ok(open_resp(me, &hub_pub, pid, &resp.0.sealed))
    }

    /// Review criterion 5: all three tiers derived over the live channel —
    /// the tier comes from verified co-signs (memo rule 5), and each present
    /// burns its challenge so each tier needs a fresh challenge.
    #[tokio::test]
    async fn constellation_three_tiers_over_channel() {
        let (_tmp, state) = fresh_rest_state(None).await; // open admission
        let hub_pub = state.signer.public_key().unwrap();
        let (me, my_lct) = (KeyPair::generate(), Uuid::new_v4());
        let pid0 = Uuid::new_v4();
        let sealed = seal_req(&me, &hub_pub, pid0, "request_citizenship",
            serde_json::json!({ "name": "Constellation Owner" }));
        channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: my_lct, pair_id: pid0, sealed,
            caller_pubkey_hex: Some(me.verifying_key().to_hex()),
        })).await.expect("admitted");

        let (k1, k2, khw) = (KeyPair::generate(), KeyPair::generate(), KeyPair::generate());

        // No co-signs → single_device.
        let out = challenge_and_present(&state, &me, my_lct, Uuid::new_v4(), |n|
            make_att(&me, my_lct, &[], &n, chrono::Utc::now())).await.unwrap();
        assert_eq!(out["assurance"], serde_json::json!("single_device"));
        assert!(out["valid_until"].is_string(), "binding carries its validity window");

        // Two device co-signs → multi_device.
        let out = challenge_and_present(&state, &me, my_lct, Uuid::new_v4(), |n|
            make_att(&me, my_lct,
                &[(DeviceType::Desktop, &k1), (DeviceType::Mobile, &k2)], &n, chrono::Utc::now())).await.unwrap();
        assert_eq!(out["assurance"], serde_json::json!("multi_device"));

        // A hardware co-sign → hardware_backed.
        let out = challenge_and_present(&state, &me, my_lct, Uuid::new_v4(), |n|
            make_att(&me, my_lct, &[(DeviceType::Hardware, &khw)], &n, chrono::Utc::now())).await.unwrap();
        assert_eq!(out["assurance"], serde_json::json!("hardware_backed"));
    }

    /// Review criteria 1–3: replay (burned nonce), bad nonce, stale issued_at,
    /// and a foreign owner key (valid channel, someone else's owner key → 403).
    #[tokio::test]
    async fn constellation_reject_paths_over_channel() {
        let (_tmp, state) = fresh_rest_state(None).await;
        let hub_pub = state.signer.public_key().unwrap();
        let (me, my_lct) = (KeyPair::generate(), Uuid::new_v4());
        let pid0 = Uuid::new_v4();
        let sealed = seal_req(&me, &hub_pub, pid0, "request_citizenship",
            serde_json::json!({ "name": "Rejectee" }));
        channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: my_lct, pair_id: pid0, sealed,
            caller_pubkey_hex: Some(me.verifying_key().to_hex()),
        })).await.expect("admitted");

        let present = |pid: Uuid, att: ConstellationAttestation| {
            let sealed = seal_req(&me, &hub_pub, pid, "present_constellation",
                serde_json::to_value(&att).unwrap());
            channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
                caller_lct_id: my_lct, pair_id: pid, sealed, caller_pubkey_hex: None,
            }))
        };
        let challenge = |pid: Uuid| {
            let sealed = seal_req(&me, &hub_pub, pid, "constellation_challenge", serde_json::json!({}));
            channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
                caller_lct_id: my_lct, pair_id: pid, sealed, caller_pubkey_hex: None,
            }))
        };
        let nonce_of = |pid: Uuid, resp: &ChannelResponse| -> String {
            open_resp(&me, &hub_pub, pid, &resp.sealed)["nonce"].as_str().unwrap().to_string()
        };

        // Present with no outstanding challenge → 400.
        let pid = Uuid::new_v4();
        let att = make_att(&me, my_lct, &[], "never-minted", chrono::Utc::now());
        let err = present(pid, att).await.err().expect("no challenge → reject");
        assert_eq!(err.status, StatusCode::BAD_REQUEST);

        // Replay: a valid present succeeds once, the same attestation again
        // finds its nonce burned → 400.
        let pid = Uuid::new_v4();
        let resp = challenge(pid).await.unwrap();
        let att = make_att(&me, my_lct, &[], &nonce_of(pid, &resp.0), chrono::Utc::now());
        present(pid, att.clone()).await.expect("first present succeeds");
        let err = present(pid, att).await.err().expect("replay → reject");
        assert_eq!(err.status, StatusCode::BAD_REQUEST);

        // Wrong nonce → 400 (and the real nonce is burned by the attempt).
        let pid = Uuid::new_v4();
        challenge(pid).await.unwrap();
        let att = make_att(&me, my_lct, &[], "not-the-nonce", chrono::Utc::now());
        let err = present(pid, att).await.err().expect("bad nonce → reject");
        assert_eq!(err.status, StatusCode::BAD_REQUEST);

        // Stale issued_at (outside the 5-min window) → 400.
        let pid = Uuid::new_v4();
        let resp = challenge(pid).await.unwrap();
        let att = make_att(&me, my_lct, &[], &nonce_of(pid, &resp.0),
            chrono::Utc::now() - chrono::Duration::minutes(6));
        let err = present(pid, att).await.err().expect("stale → reject");
        assert_eq!(err.status, StatusCode::BAD_REQUEST);

        // Foreign owner key: correctly signed attestation, but by a key that
        // is NOT this member's pinned key → 403, not a warn-and-accept.
        let pid = Uuid::new_v4();
        let resp = challenge(pid).await.unwrap();
        let foreign = KeyPair::generate();
        let att = make_att(&foreign, my_lct, &[], &nonce_of(pid, &resp.0), chrono::Utc::now());
        let err = present(pid, att).await.err().expect("foreign owner key → reject");
        assert_eq!(err.status, StatusCode::FORBIDDEN);
    }
}
