// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Tier-2 unlock, decided by the built-in quorum verifier (`hub_lib::unlock_quorum`, #860).
//!
//! This replaces the external `HUB_UNLOCK_VERIFIER` subprocess, which received opaque
//! attestations and returned a verdict the hub took on its word. Now every check runs here, in
//! the verifier's order:
//!
//! 1. `/unlock/challenge` (loopback, ignited) opens a **release intent** binding the tier (the
//!    secret), the operation (`release`), the hub as requester, the destination (this hub's
//!    memory), the council policy in force, an expiry and a nonce. Approvals sign its digest, so
//!    approvals gathered for one intent authorize nothing else.
//! 2. `/unlock/approver-challenge` issues one approver a **single-use challenge** for it —
//!    idempotent while outstanding, and not a secret (the signature is what counts).
//! 3. `/unlock/attest` takes a signed approval or decline. It is VERIFIED against the approver's
//!    council key from the ledger projection — never a key the submission carries — and only a
//!    verified one is witnessed: anyone can submit bytes, and bytes are not a record. A verified
//!    decline VETOES the intent, terminally. When the threshold is met the verifier records the
//!    intent CONSUMED, the resolution is witnessed, and only then is the protected tier opened —
//!    at most once: a failure after consumption leaves it consumed and unreleased, and recovery
//!    needs a fresh intent.
//!
//! The release goes where the intent's signed `destination` says — this hub's memory
//! ([`Tier2::released`]) — and NOWHERE else. `/unlock/attest` is network-reachable by design (a
//! remote council member must be able to reach it) and does not authenticate its submitter: the
//! verified approval signature is its only authority, and whoever relays an approval is not
//! thereby a recipient. So the response reports status and witness metadata only, never payload
//! bytes; a test pins the response schema.
//!
//! The policy (roster, threshold, epoch) is the council as the signed ledger projects it; the
//! epoch is the index of the newest council-changing entry, so a council change makes every
//! intent opened under the old council stale — terminally, by the verifier's own rule.
//!
//! Consumed/vetoed live in the verifier's memory; on first use after a restart they are
//! re-derived from the ledger's `VaultUnlockResolved` entries, so an approver who attests to an
//! old challenge hears "consumed" or "vetoed", not "unknown". (An old intent cannot be re-opened
//! regardless: only `/unlock/challenge` opens intents, each with a fresh nonce.)
//!
//! OFF unless the operator enables it: `HUB_TIER2_UNLOCK=quorum`. A hub that still carries the
//! retired `HUB_UNLOCK_VERIFIER` gets tier-2 OFF and a startup warning, not a silent switch of
//! verifier.
//!
//! What this is not: the advisory, host-software embodiment. A compromised host can skip it; see
//! the `unlock_quorum` module doc for the hardware design this does not provide.
use super::*;
use hub_lib::unlock_quorum::{
    Approval, Bytes32, Decline, IntentState, OperationParams, QuorumVerifier, Refusal, ReleaseIntent,
    Roster,
};

/// How long a release intent authorizes anything.
pub(super) const INTENT_TTL_SECS: u64 = 300;
/// How long one approver's challenge is valid (capped by the intent's own expiry in practice).
pub(super) const CHALLENGE_TTL_SECS: u64 = 300;

/// The environment switch. Anything else — including absent — is off.
pub(super) fn tier2_enabled_from_env() -> bool {
    let on = std::env::var("HUB_TIER2_UNLOCK").ok().as_deref() == Some("quorum");
    if !on && std::env::var("HUB_UNLOCK_VERIFIER").ok().is_some_and(|v| !v.is_empty()) {
        tracing::warn!(
            "HUB_UNLOCK_VERIFIER is set, but the external unlock verifier is RETIRED: tier-2 \
             unlock is now decided by the built-in quorum verifier and is OFF until \
             HUB_TIER2_UNLOCK=quorum is set. Nothing was switched silently."
        );
    }
    on
}

struct OpenRelease {
    intent: ReleaseIntent,
    digest: Bytes32,
    required: usize,
}

/// The daemon's tier-2 state: the verifier, which intent each challenge id names, and the
/// terminal outcomes re-derived from the ledger.
#[derive(Default)]
pub struct Tier2 {
    verifier: Option<QuorumVerifier>,
    releases: std::collections::HashMap<Uuid, OpenRelease>,
    terminal: std::collections::HashMap<Uuid, IntentState>,
    rederived: bool,
    released: Option<ReleasedTier>,
}

/// A protected tier a quorum released into hub memory — the intent's signed destination.
pub(crate) struct ReleasedTier {
    pub challenge_id: Uuid,
    pub tier: String,
    pub payload: String,
    /// The `VaultUnlockResolved` entry that authorized it.
    pub resolution_index: u64,
}

impl Tier2 {
    /// The tier the last granted quorum released into hub memory, if any. In-process only: no
    /// route returns it.
    pub(crate) fn released(&self) -> Option<&ReleasedTier> {
        self.released.as_ref()
    }
}

fn now_secs() -> u64 {
    Utc::now().timestamp().max(0) as u64
}

fn random32() -> Bytes32 {
    let mut n = [0u8; 32];
    n[..16].copy_from_slice(Uuid::new_v4().as_bytes());
    n[16..].copy_from_slice(Uuid::new_v4().as_bytes());
    n
}

fn refused(status: StatusCode, r: impl std::fmt::Display) -> ApiError {
    ApiError { status, message: r.to_string() }
}

fn refusal_status(r: &Refusal) -> StatusCode {
    match r {
        Refusal::NotOnRoster | Refusal::BadSignature => StatusCode::FORBIDDEN,
        Refusal::UnknownIntent => StatusCode::NOT_FOUND,
        _ => StatusCode::CONFLICT,
    }
}

fn digest_hex(d: &Bytes32) -> String {
    hex::encode(d)
}

/// The council as the signed ledger projects it: roster (keys from the ledger's pins, never
/// from a submission), threshold, the epoch (index of the newest council-changing entry), and
/// the roster ids in order.
fn council_policy(ledger: &hub_lib::ledger::HubLedger) -> Result<(Roster, usize, u64, Vec<Uuid>), ApiError> {
    let st = HubState::project(ledger);
    let mut roster = Roster::new();
    let mut ids = Vec::new();
    for (lct, pk_hex) in &st.council_pubkeys {
        let key = hex::decode(pk_hex)
            .ok()
            .and_then(|b| <[u8; 32]>::try_from(b.as_slice()).ok())
            .and_then(|a| web4_core::crypto::PublicKey::from_bytes(&a).ok())
            .ok_or_else(|| refused(StatusCode::CONFLICT, format!(
                "council member {lct} has an unusable pinned key; a roster with a broken pin cannot \
                 decide a release (fail-closed) — re-pin or remove the member")))?;
        roster = roster.with(*lct, key);
        ids.push(*lct);
    }
    let threshold = st
        .council_threshold
        .map(|(m, _)| m as usize)
        .unwrap_or_else(|| unlock_default_threshold(ids.len()) as usize);
    let epoch = ledger
        .entries()
        .iter()
        .rev()
        .find(|e| matches!(e.event,
            HubEvent::CouncilMemberAdded { .. } | HubEvent::CouncilMemberRemoved { .. }
            | HubEvent::CouncilThresholdChanged { .. } | HubEvent::CouncilMirrored { .. }))
        .map(|e| e.index)
        .unwrap_or(0);
    Ok((roster, threshold, epoch, ids))
}

impl Tier2 {
    /// Admit the council policy in force (creating the verifier on first use), and re-derive the
    /// terminal outcomes from the ledger once per process.
    fn sync(&mut self, ledger: &hub_lib::ledger::HubLedger) -> Result<(usize, Vec<Uuid>), ApiError> {
        if !self.rederived {
            for e in ledger.entries() {
                if let HubEvent::VaultUnlockResolved { challenge_id, granted, .. } = &e.event {
                    self.terminal.insert(*challenge_id,
                        if *granted { IntentState::Consumed } else { IntentState::Vetoed });
                }
            }
            self.rederived = true;
        }
        let (roster, threshold, epoch, ids) = council_policy(ledger)?;
        if ids.is_empty() {
            return Err(refused(StatusCode::CONFLICT,
                "no Sovereign Council enrolled — there is no roster to authorize a tier-2 release"));
        }
        match &mut self.verifier {
            None => self.verifier = Some(QuorumVerifier::new(roster, threshold, epoch)
                .map_err(|r| refused(StatusCode::CONFLICT, r))?),
            Some(v) => v.admit_policy(roster, threshold, epoch).map_err(|r| refused(StatusCode::CONFLICT, r))?,
        }
        Ok((threshold, ids))
    }

    fn terminal_refusal(&self, challenge_id: &Uuid) -> Option<ApiError> {
        self.terminal.get(challenge_id).map(|s| refused(StatusCode::CONFLICT, match s {
            IntentState::Consumed => "this release was already granted and consumed — a release intent authorizes at most once",
            IntentState::Vetoed => "this release was vetoed by a council member — a veto is terminal",
            IntentState::Open => "this release is open",
        }))
    }
}

fn require_enabled(s: &RestState) -> Result<(), ApiError> {
    if s.tier2_enabled {
        return Ok(());
    }
    Err(refused(StatusCode::NOT_IMPLEMENTED,
        "tier-2 M-of-N unlock is not enabled on this hub (set HUB_TIER2_UNLOCK=quorum to enable the \
         built-in quorum verifier)"))
}

#[derive(Deserialize)]
pub struct ChallengeReq {
    /// The protected tier to release (witnessed). Defaults to "protected".
    #[serde(default = "default_unlock_tier")]
    pub(super) tier: String,
}
fn default_unlock_tier() -> String {
    "protected".to_string()
}

/// What an approver is asked to approve, in full: every field the digest binds, readable.
#[derive(Serialize, Deserialize, Clone, Debug, PartialEq)]
pub struct IntentView {
    pub secret_id: String,
    pub operation: String,
    pub requester: Uuid,
    pub destination: String,
    pub policy_version_hex: String,
    pub expires_at: u64,
    pub nonce_hex: String,
    pub digest_hex: String,
}

impl IntentView {
    fn of(i: &ReleaseIntent) -> Self {
        Self {
            secret_id: i.secret_id.clone(),
            operation: i.operation.clone(),
            requester: i.requester,
            destination: i.destination.clone(),
            policy_version_hex: hex::encode(i.policy_version),
            expires_at: i.expires_at,
            nonce_hex: hex::encode(i.nonce),
            digest_hex: digest_hex(&i.digest()),
        }
    }
}

#[derive(Serialize)]
pub struct ChallengeResp {
    pub(super) challenge_id: Uuid,
    pub(super) tier: String,
    pub(super) hub_lct: Uuid,
    pub(super) issued_at: u64,
    /// Distinct verified approvals required (the council M).
    pub(super) required: u32,
    /// The council members who may approve or decline.
    pub(super) roster: Vec<Uuid>,
    /// The release intent, every bound field shown.
    pub(super) intent: IntentView,
}

/// `POST /v1/hubs/:id/unlock/challenge` — open a release intent for the tier. Loopback-only (the
/// hub/operator triggers it), ignited, enabled, council enrolled. Witnessed
/// (`VaultUnlockRequested`) BEFORE the intent is open, so an unrecorded request opens nothing.
pub(super) async fn unlock_challenge(
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    State(s): State<RestState>,
    Path(_hub_id): Path<Uuid>,
    Json(req): Json<ChallengeReq>,
) -> Result<Json<ChallengeResp>, ApiError> {
    if !peer.ip().is_loopback() {
        return Err(refused(StatusCode::FORBIDDEN,
            "opening a tier-2 release intent is local-only (the hub/operator triggers it)"));
    }
    if s.is_locked() {
        return Err(refused(StatusCode::SERVICE_UNAVAILABLE,
            "ignite tier-1 first (passphrase / hardware) before a tier-2 M-of-N unlock"));
    }
    require_enabled(&s)?;
    let now = now_secs();
    let mut t2 = s.tier2.lock().await;
    let (required, roster, intent) = {
        let ledger = s.ledger.lock().await;
        let (required, roster) = t2.sync(&ledger)?;
        let v = t2.verifier.as_ref().expect("synced");
        let intent = ReleaseIntent {
            secret_id: req.tier.clone(),
            operation: "release".into(),
            requester: s.sovereign_lct_id,
            destination: format!("hub-memory:{}", s.hub_id),
            policy_version: v.policy_in_force(),
            expires_at: now + INTENT_TTL_SECS,
            nonce: random32(),
        };
        (required, roster, intent)
    };
    let challenge_id = Uuid::new_v4();
    witness_event(&s, HubEvent::VaultUnlockRequested {
        challenge_id,
        tier: req.tier.clone(),
        required: required as u32,
        requested_at: Utc::now(),
    })
    .await?;
    let digest = t2
        .verifier
        .as_mut()
        .expect("synced")
        .open_intent(intent.clone(), now)
        .map_err(|r| refused(refusal_status(&r), r))?;
    t2.releases.insert(challenge_id, OpenRelease { intent: intent.clone(), digest, required });
    Ok(Json(ChallengeResp {
        challenge_id,
        tier: req.tier,
        hub_lct: s.sovereign_lct_id,
        issued_at: now,
        required: required as u32,
        roster,
        intent: IntentView::of(&intent),
    }))
}

#[derive(Deserialize)]
pub struct ApproverChallengeReq {
    pub challenge_id: Uuid,
    pub approver: Uuid,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct ApproverChallengeResp {
    pub challenge_id: Uuid,
    pub approver: Uuid,
    pub intent: IntentView,
    /// Sign `web4:release-approve:v1:` || digest || this, with the approver's council key.
    pub challenge_hex: String,
}

/// `POST /v1/hubs/:id/unlock/approver-challenge` — issue one council member their single-use
/// challenge for an open intent, with the intent in full so they see what they would approve.
/// Idempotent while outstanding. Not witnessed: a challenge authorizes nothing and is not secret.
pub(super) async fn unlock_approver_challenge(
    State(s): State<RestState>,
    Path(_hub_id): Path<Uuid>,
    Json(req): Json<ApproverChallengeReq>,
) -> Result<Json<ApproverChallengeResp>, ApiError> {
    require_enabled(&s)?;
    let mut t2 = s.tier2.lock().await;
    {
        let ledger = s.ledger.lock().await;
        t2.sync(&ledger)?;
    }
    if let Some(e) = t2.terminal_refusal(&req.challenge_id) {
        return Err(e);
    }
    let (intent, digest) = match t2.releases.get(&req.challenge_id) {
        Some(r) => (r.intent.clone(), r.digest),
        None => return Err(ApiError::not_found("no such release intent (expired, or the hub restarted)")),
    };
    let bytes = t2
        .verifier
        .as_mut()
        .expect("synced")
        .issue_challenge(&digest, req.approver, now_secs(), CHALLENGE_TTL_SECS)
        .map_err(|r| refused(refusal_status(&r), r))?;
    Ok(Json(ApproverChallengeResp {
        challenge_id: req.challenge_id,
        approver: req.approver,
        intent: IntentView::of(&intent),
        challenge_hex: hex::encode(bytes),
    }))
}

#[derive(Deserialize)]
pub struct AttestReq {
    pub challenge_id: Uuid,
    #[serde(default)]
    pub approval: Option<Approval>,
    #[serde(default)]
    pub decline: Option<Decline>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct AttestResp {
    pub granted: bool,
    pub vetoed: bool,
    pub approvals: Vec<Uuid>,
    pub declines: Vec<Uuid>,
    pub required: usize,
    pub reason: String,
    /// On the grant: whether the protected tier was opened into hub memory (its destination).
    /// Never the payload — see the module doc.
    pub opened: bool,
    /// On the grant: the ledger index of the witnessed `VaultUnlockResolved`.
    pub resolution_index: Option<u64>,
}

/// `POST /v1/hubs/:id/unlock/attest` — a council member's signed approval or decline. Verified
/// against their council key; a refused one is NOT witnessed and changes nothing.
pub(super) async fn unlock_attest(
    State(s): State<RestState>,
    Path(_hub_id): Path<Uuid>,
    Json(req): Json<AttestReq>,
) -> Result<Json<AttestResp>, ApiError> {
    require_enabled(&s)?;
    let now = now_secs();
    let mut t2 = s.tier2.lock().await;
    {
        let ledger = s.ledger.lock().await;
        t2.sync(&ledger)?;
    }
    if let Some(e) = t2.terminal_refusal(&req.challenge_id) {
        return Err(e);
    }
    let (intent, digest, required) = match t2.releases.get(&req.challenge_id) {
        Some(r) => (r.intent.clone(), r.digest, r.required),
        None => return Err(ApiError::not_found("no such release intent (expired, or the hub restarted)")),
    };

    match (req.approval, req.decline) {
        (Some(a), None) => {
            if a.intent_digest != digest {
                return Err(refused(StatusCode::CONFLICT, "the approval signs a different intent than this challenge names"));
            }
            let v = t2.verifier.as_mut().expect("synced");
            v.submit_approval(&a, now).map_err(|r| refused(refusal_status(&r), r))?;
            witness_event(&s, HubEvent::VaultUnlockAttested {
                challenge_id: req.challenge_id,
                admin_lct_id: a.approver,
                decision: "approve".into(),
                attested_at: Utc::now(),
            })
            .await?;
            let params = OperationParams {
                secret_id: intent.secret_id.clone(),
                operation: intent.operation.clone(),
                destination: intent.destination.clone(),
            };
            let v = t2.verifier.as_mut().expect("synced");
            match v.authorize(&digest, &params, now) {
                Ok(auth) => {
                    // CONSUMED in the verifier before anything below: at most once.
                    t2.terminal.insert(req.challenge_id, IntentState::Consumed);
                    t2.releases.remove(&req.challenge_id);
                    let resolution_index = witness_event(&s, HubEvent::VaultUnlockResolved {
                        challenge_id: req.challenge_id,
                        tier: intent.secret_id.clone(),
                        granted: true,
                        approvals: auth.approvers.clone(),
                        declines: Vec::new(),
                        resolved_at: Utc::now(),
                    })
                    .await
                    .map_err(|e| refused(e.status, format!(
                        "the quorum was met and the intent is CONSUMED, but the resolution could not \
                         be recorded ({}); nothing was released. Open a fresh intent.", e.message)))?;
                    // Released to the destination the intent signed: hub memory, not the caller.
                    let opened = match open_protected_tier(&s).await {
                        Some(payload) => {
                            t2.released = Some(ReleasedTier {
                                challenge_id: req.challenge_id,
                                tier: intent.secret_id.clone(),
                                payload,
                                resolution_index,
                            });
                            true
                        }
                        None => false,
                    };
                    tracing::warn!(
                        challenge = %req.challenge_id, tier = %intent.secret_id, opened, resolution_index,
                        "TIER-2 RELEASE GRANTED by a verified M-of-N quorum (witnessed); opened into hub memory"
                    );
                    Ok(Json(AttestResp {
                        granted: true, vetoed: false, approvals: auth.approvers, declines: Vec::new(),
                        required, reason: "a threshold of distinct verified council approvals".into(),
                        opened, resolution_index: Some(resolution_index),
                    }))
                }
                Err(Refusal::BelowThreshold { have, need }) => Ok(Json(AttestResp {
                    granted: false, vetoed: false, approvals: Vec::new(), declines: Vec::new(), required,
                    reason: format!("{have} of {need} verified approvals"), opened: false, resolution_index: None,
                })),
                Err(r) => Err(refused(refusal_status(&r), r)),
            }
        }
        (None, Some(d)) => {
            if d.intent_digest != digest {
                return Err(refused(StatusCode::CONFLICT, "the decline signs a different intent than this challenge names"));
            }
            let v = t2.verifier.as_mut().expect("synced");
            v.submit_decline(&d, now).map_err(|r| refused(refusal_status(&r), r))?;
            t2.terminal.insert(req.challenge_id, IntentState::Vetoed);
            t2.releases.remove(&req.challenge_id);
            witness_event(&s, HubEvent::VaultUnlockAttested {
                challenge_id: req.challenge_id,
                admin_lct_id: d.approver,
                decision: "decline".into(),
                attested_at: Utc::now(),
            })
            .await?;
            witness_event(&s, HubEvent::VaultUnlockResolved {
                challenge_id: req.challenge_id,
                tier: intent.secret_id.clone(),
                granted: false,
                approvals: Vec::new(),
                declines: vec![d.approver],
                resolved_at: Utc::now(),
            })
            .await?;
            Ok(Json(AttestResp {
                granted: false, vetoed: true, approvals: Vec::new(), declines: vec![d.approver], required,
                reason: "vetoed by a verified council decline — terminal".into(), opened: false, resolution_index: None,
            }))
        }
        _ => Err(refused(StatusCode::BAD_REQUEST, "send exactly one of `approval` or `decline`")),
    }
}
