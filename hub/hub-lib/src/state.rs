// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Event-sourced chapter state projection.
//!
//! The ledger is the source of truth. This module folds the ledger's events
//! into current state (member list, skill index, role-fill snapshot, etc.)
//! for query-time access by MCP tools and the admin CLI.
//!
//! Rebuilt from scratch on each query in MVP; future sprints may cache and
//! incrementally update.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};
use uuid::Uuid;

use crate::events::{HubEvent, PairRevocationKind, ProfileVisibility};
use crate::ledger::HubLedger;

/// One profile field with its disclosure tier. Stored inside
/// [`Member::profile`] so each field carries its own visibility.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProfileField {
    pub value: String,
    #[serde(default)]
    pub visibility: ProfileVisibility,
}

impl ProfileField {
    pub fn new(value: impl Into<String>, visibility: ProfileVisibility) -> Self {
        Self { value: value.into(), visibility }
    }
}

/// Backward-compatible deserialization for `Member::profile`. Older ledgers
/// stored the profile as `{"key": "value"}`; we load those as
/// `ProfileVisibility::Members` (the pre-visibility behavior).
fn deserialize_profile_legacy<'de, D>(deserializer: D) -> Result<BTreeMap<String, ProfileField>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    use serde::de::Error;
    let raw: serde_json::Value = Deserialize::deserialize(deserializer)?;
    let mut out = BTreeMap::new();
    let obj = raw.as_object().ok_or_else(|| D::Error::custom("profile must be an object"))?;
    for (k, v) in obj {
        let field = match v {
            serde_json::Value::Object(m) => {
                serde_json::from_value(serde_json::Value::Object(m.clone()))
                    .map_err(D::Error::custom)?
            }
            serde_json::Value::String(s) => ProfileField {
                value: s.clone(),
                visibility: ProfileVisibility::default(),
            },
            _ => return Err(D::Error::custom("profile value must be a string or object")),
        };
        out.insert(k.clone(), field);
    }
    Ok(out)
}

/// Projected current state of a chapter, derived from ledger events.
#[derive(Clone, Debug, Default, Serialize)]
pub struct HubState {
    pub hub_name: String,
    pub founding_sovereign_lct_id: Option<Uuid>,
    pub charter_hash: Option<String>,

    /// LCT id → Member record. Members removed via MemberRemoved are dropped.
    pub members: BTreeMap<Uuid, Member>,

    /// Skill index: skill (lowercase) → set of member LCT ids who declared it.
    pub skill_index: BTreeMap<String, BTreeSet<Uuid>>,

    /// Member LCT id → hex-encoded public key (V2-12). Populated from
    /// MemberAdded events that carry a pubkey. Used to seed the envelope
    /// resolver at hub serve startup so member-signed envelopes verify
    /// without an external registry. Members added pre-V2-12 (no pubkey
    /// in their MemberAdded event) are absent here and can't sign
    /// envelopes until re-added with a pubkey.
    pub member_pubkeys: BTreeMap<Uuid, String>,

    /// Authoritative constellation enrollment: `owner_lct → device_lct →`
    /// [`EnrolledDevice`]. The record (pubkey, class, status) the constellation
    /// verifier resolves against — established by owner-signed `DeviceEnrolled`
    /// before any challenge, so a presented attestation can't self-authenticate
    /// its device facts (GPT enrollment-registry fix, 2026-07-21). Nested (not a
    /// `(Uuid,Uuid)` tuple key) so it serializes as a JSON object.
    pub enrolled_devices: BTreeMap<Uuid, BTreeMap<Uuid, crate::constellation::EnrolledDevice>>,

    /// Member↔member introductions (the consent half of discovery).
    /// Projected from IntroRequested/IntroResponded.
    pub intros: BTreeMap<Uuid, Intro>,

    /// V2-9 Phase 1: Sovereign Council holders beyond the founding
    /// Sovereign. Empty for single-Sovereign chapters. Each holder
    /// can sign chapter acts as a co-Sovereign; their pubkey is in
    /// `council_pubkeys`.
    pub council_holders: BTreeSet<Uuid>,

    /// V2-9 Phase 1: pubkeys of council holders. Resolver bootstrap
    /// merges these with `member_pubkeys` at hub serve startup so any
    /// council holder's envelope verifies.
    pub council_pubkeys: BTreeMap<Uuid, String>,

    /// V2-9 Phase 1: current M-of-N threshold for council-gated acts.
    /// `None` means single-signer mode. The N component is recomputed
    /// from `council_holders.len() + 1` (the founding Sovereign counts)
    /// at apply time. **Not yet enforced** — informational until
    /// V2-9 Phase 2 ships the proposal/aggregation flow.
    pub council_threshold: Option<(u32, u32)>,

    /// PAIRED-CHANNELS Sprint B: pair_id → PairState. Tracks the
    /// lifecycle of every LCT-to-LCT pair the chapter has hosted.
    /// Cleared on hub recovery via projection from the ledger.
    pub pairs: BTreeMap<Uuid, PairState>,

    /// V2-16 admission queue: `request_id` → join request (pending or resolved).
    /// Built from `MemberJoinRequested`/`MemberJoinResolved`. The operator GUI
    /// lists `Pending` entries and approves/denies them; law-`Allow` joins are
    /// auto-admitted and never appear here.
    pub pending_joins: BTreeMap<Uuid, JoinRequest>,

    /// Repair path: `review_id` → denial-review request (the only self-service
    /// way to clear an auto-block). Built from `MemberJoinReviewRequested`/
    /// `MemberJoinReviewResolved`.
    pub join_reviews: BTreeMap<Uuid, JoinReview>,

    /// Admission standing per applicant LCT — the abuse-resistance counters.
    /// `denials` resets on a granted review or an operator reset; `reviews`
    /// resets only on an operator reset. Thresholds live in hub law
    /// (`admission_repeat_limit`/`admission_review_limit`), not here.
    pub admission: BTreeMap<Uuid, AdmissionStanding>,

    /// Role-contextualized reputation, keyed by `(subject_lct, role_lct)` — the
    /// projected side of R7 back-propagation. Reputation is NEVER global; it lives
    /// on the MRH role-pairing link (RFC #403). Folded from `ReputationRecorded`.
    ///
    /// Serialized as a JSON **array** of entries, not a map: JSON object keys
    /// must be strings, and a tuple key would make `serde_json::to_string(&state)`
    /// fail at runtime. The array form (`{subject_lct, role_lct, …}`) keeps the
    /// whole `HubState` safely serializable.
    #[serde(serialize_with = "serialize_reputation")]
    pub reputation: BTreeMap<(String, String), RoleReputation>,

    /// §5.1 R7 carrier: open accountability obligations, keyed by `request_id`.
    /// An `ObligationOpened` inserts; `ObligationResolved` removes. String-keyed,
    /// so serialization-safe. The timeout sweep (P2) reads this to debit misses.
    pub obligations: BTreeMap<String, Obligation>,

    /// The LCT registry: published presence, keyed by canonical (pubkey-derived)
    /// `lct_id`. Folded from `LctPublished`, which ingest has already verified —
    /// an entry here means binding + id-derivation checked out at the door, so
    /// the projection stores rather than re-verifies. Serves presence, mints no
    /// trust. Absence is the closed pole: an unknown id resolves 404, never a
    /// fabricated stub.
    pub registry: BTreeMap<String, RegistryEntry>,

    /// Last seen index from the ledger (for cache invalidation in future).
    pub last_index: u64,
}

/// One published LCT as the registry serves it. `version` counts republishes of
/// the *same* key (updated MRH edges, status change) — the latest document is
/// served, and full history stays reachable by ledger replay. A key rotation is
/// NOT a version bump: the id is pubkey-derived, so it moves, and the new entry
/// carries an MRH `rotated_from` edge to its predecessor. Identity is never
/// mutated in place.
#[derive(Clone, Debug, Serialize)]
pub struct RegistryEntry {
    pub document: web4_core::lct::Lct,
    pub provenance: crate::events::LctProvenance,
    pub published_by: Uuid,
    pub published_at: DateTime<Utc>,
    pub version: u32,
}

/// An open R7 obligation: the subject committed to `request_id` due by `due_at`,
/// in the `role_lct` context. Folded from `ObligationOpened`; removed on
/// `ObligationResolved`. Retains `criticality` + `opened_at` so a met/late/missed
/// evaluation can reconstruct the `Deadline` + `Timing`.
#[derive(Clone, Debug, Serialize)]
pub struct Obligation {
    pub subject_lct: String,
    pub role_lct: String,
    pub due_at: DateTime<Utc>,
    pub criticality: web4_core::time::Criticality,
    pub opened_at: DateTime<Utc>,
}

/// Accumulated role-contextualized reputation for one `(subject, role)` pairing.
/// Folded from `ReputationRecorded` deltas via `T3/V3::apply_delta` — the hub
/// applies the math but never invents it (weights are a society-law hook).
#[derive(Clone, Debug, Serialize)]
pub struct RoleReputation {
    pub t3: web4_core::t3::T3,
    pub v3: web4_core::v3::V3,
    pub observations: u32,
    pub last_updated: DateTime<Utc>,
    /// Attestation strength of this folded `(subject, role)` bucket — the
    /// **weakest** sovereign strength of any delta that fed it (HUB Concern 1,
    /// thread `identity-p1-cospec`). `placeholder` ⇒ member-attested, not
    /// hub-verified: the subject's `instance_lct` derives from a placeholder
    /// sovereign and cannot be cryptographically bound. Only a bucket fed
    /// **exclusively** by hardware-sovereign deltas reports `hardware`.
    pub sovereign_strength: web4_core::r6::SovereignStrength,
}

impl RoleReputation {
    fn new(ts: DateTime<Utc>) -> Self {
        Self {
            t3: web4_core::t3::T3::default(),
            v3: web4_core::v3::V3::default(),
            observations: 0,
            last_updated: ts,
            // Neutral bucket, no deltas folded yet → strongest possible; the
            // first (and every) delta can only weaken it via `min` below.
            sovereign_strength: web4_core::r6::SovereignStrength::Hardware,
        }
    }
}

/// Serialize the tuple-keyed reputation map as a JSON array of flattened
/// entries. JSON object keys must be strings, so a `(String, String)`-keyed map
/// can't serialize as an object — emitting a sequence keeps the whole
/// [`HubState`] serializable (and is friendlier to consumers than a joined
/// string key).
fn serialize_reputation<S>(
    map: &BTreeMap<(String, String), RoleReputation>,
    serializer: S,
) -> Result<S::Ok, S::Error>
where
    S: serde::Serializer,
{
    use serde::ser::SerializeSeq;
    #[derive(Serialize)]
    struct Entry<'a> {
        subject_lct: &'a str,
        role_lct: &'a str,
        #[serde(flatten)]
        reputation: &'a RoleReputation,
    }
    let mut seq = serializer.serialize_seq(Some(map.len()))?;
    for ((subject_lct, role_lct), reputation) in map {
        seq.serialize_element(&Entry {
            subject_lct,
            role_lct,
            reputation,
        })?;
    }
    seq.end()
}

/// Map a `ReputationDelta` dimension name to the typed T3 dimension.
fn trust_dim(s: &str) -> Option<web4_core::t3::TrustDimension> {
    use web4_core::t3::TrustDimension::*;
    match s {
        "talent" => Some(Talent),
        "training" => Some(Training),
        "temperament" => Some(Temperament),
        _ => None,
    }
}
/// Map a `ReputationDelta` dimension name to the typed V3 dimension.
fn value_dim(s: &str) -> Option<web4_core::v3::ValueDimension> {
    use web4_core::v3::ValueDimension::*;
    match s {
        "valuation" => Some(Valuation),
        "veracity" => Some(Veracity),
        "validity" => Some(Validity),
        _ => None,
    }
}

/// Abuse-resistance counters for one applicant LCT (see [`HubState::admission`]).
#[derive(Clone, Copy, Debug, Default, Serialize, Deserialize)]
pub struct AdmissionStanding {
    /// Denials since the last clear (granted review or operator reset).
    pub denials: u32,
    /// Denial-review requests since the last operator reset.
    pub reviews: u32,
}

/// Repair path: one denial-review request, projected from
/// `MemberJoinReviewRequested` / `MemberJoinReviewResolved`.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct JoinReview {
    pub review_id: Uuid,
    pub member_lct_id: Uuid,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub plea: Option<String>,
    pub requested_at: DateTime<Utc>,
    pub status: ReviewStatus,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub resolved_by: Option<Uuid>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub reason: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub resolved_at: Option<DateTime<Utc>>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ReviewStatus {
    /// Awaiting operator Grant/Refuse.
    Pending,
    /// Operator granted — the applicant's auto-block is cleared.
    Granted,
    /// Operator refused — counts toward the review limit.
    Refused,
}

/// V2-16: one entry in the admission queue, projected from
/// `MemberJoinRequested` (creates it `Pending`) and `MemberJoinResolved`
/// (transitions to `Approved`/`Denied`). The applicant's self-vouched
/// `member_pubkey_hex` is what the Sovereign pins on approval.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct JoinRequest {
    pub request_id: Uuid,
    pub member_lct_id: Uuid,
    pub member_pubkey_hex: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub message: Option<String>,
    pub requested_at: DateTime<Utc>,
    pub status: JoinStatus,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub resolved_by: Option<Uuid>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub reason: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub resolved_at: Option<DateTime<Utc>>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum JoinStatus {
    /// Awaiting operator Admit/Deny (law escalated it).
    Pending,
    /// Operator approved; a `MemberAdded` was recorded.
    Approved,
    /// Operator denied; no admission recorded.
    Denied,
}

/// PAIRED-CHANNELS Sprint B: projected state of a single pair.
/// Built from PairingRequested / PairingConfirmed / PairingRevoked
/// events. Status transitions are strictly monotonic:
/// `Pending` → `Active` → `Revoked`; or `Pending` → `Revoked`
/// (request cancelled before confirm).
///
/// Note: `Expired` is a derived state computed against current time
/// (see [`PairState::effective_status`]); the stored `status` only
/// transitions on explicit events. This keeps projection deterministic
/// (no time-dependent rebuilds) while still surfacing expiry to
/// queries.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PairState {
    pub id: Uuid,
    pub initiator: Uuid,
    pub counterparty: Uuid,
    pub purpose: String,
    pub status: PairStatus,
    pub proposed_at: DateTime<Utc>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub expires_at: Option<DateTime<Utc>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub confirmed_at: Option<DateTime<Utc>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub revoked_at: Option<DateTime<Utc>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub revocation_kind: Option<PairRevocationKind>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub revocation_reason: Option<String>,
    /// PAIRED-CHANNELS Sprint D will increment this per relayed message.
    /// Used as a trust-accrual signal in Sprint G. Sprint B leaves it at 0.
    #[serde(default)]
    pub message_count: u64,
    /// PAIRED-CHANNELS Sprint F: initiator's per-session ephemeral
    /// X25519 public key (hex), surfaced from PairingRequested. The
    /// counterparty reads this from the pair detail + uses it (with
    /// their own ephemeral secret) to derive the v2 session key.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub initiator_ephemeral_pub_hex: Option<String>,
    /// PAIRED-CHANNELS Sprint F: counterparty's per-session ephemeral
    /// X25519 public key (hex), surfaced from PairingConfirmed.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub counterparty_ephemeral_pub_hex: Option<String>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PairStatus {
    /// Initiator requested; counterparty hasn't confirmed yet.
    Pending,
    /// Both parties have signed; the pair is live.
    Active,
    /// Explicitly revoked (any `PairRevocationKind`).
    Revoked,
}

impl PairState {
    /// True iff either initiator or counterparty matches `lct_id`.
    /// Used by queries like "show me my pairs".
    pub fn includes(&self, lct_id: Uuid) -> bool {
        self.initiator == lct_id || self.counterparty == lct_id
    }

    /// Status taking expiry into account. If `status == Active` and
    /// we're past `expires_at`, returns Expired. Otherwise returns
    /// the stored status as a corresponding effective string.
    ///
    /// String-typed so callers don't need to handle the synthetic
    /// `Expired` value vs. the projected `Revoked` value — both
    /// mean "no longer usable."
    pub fn effective_status(&self, now: DateTime<Utc>) -> &'static str {
        match self.status {
            PairStatus::Active => {
                if let Some(exp) = self.expires_at {
                    if now >= exp { return "expired"; }
                }
                "active"
            }
            PairStatus::Pending => "pending",
            PairStatus::Revoked => "revoked",
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Member {
    pub lct_id: Uuid,
    pub name: Option<String>,
    pub skills: BTreeSet<String>,
    /// Free-text profile fields (skills, interests, + expandable keys) for
    /// semantic member discovery. Populated by MemberProfileUpdated events.
    /// Each field carries a visibility tier; old ledgers without tiers load
    /// as the default `Members` visibility.
    #[serde(default, deserialize_with = "deserialize_profile_legacy")]
    pub profile: BTreeMap<String, ProfileField>,
}

impl Member {
    /// Profile fields visible to a given viewer category.
    /// - `viewer == member.lct_id` → self, members, public fields.
    /// - `viewer_is_operator == true` → all fields.
    /// - `viewer_is_member == true` → members + public fields.
    /// - otherwise → public fields only.
    pub fn visible_profile(
        &self,
        viewer: Option<Uuid>,
        viewer_is_member: bool,
        viewer_is_operator: bool,
    ) -> BTreeMap<String, String> {
        self.profile
            .iter()
            .filter(|(_, f)| match f.visibility {
                ProfileVisibility::Public => true,
                ProfileVisibility::Members => viewer_is_member || viewer_is_operator,
                ProfileVisibility::SelfOnly => {
                    viewer.map(|v| v == self.lct_id).unwrap_or(false) || viewer_is_operator
                }
            })
            .map(|(k, f)| (k.clone(), f.value.clone()))
            .collect()
    }

    /// A serializable view of this member with the profile filtered to what the
    /// viewer is allowed to see. Used by REST/MCP read paths so we never leak
    /// `ProfileField` internals (visibility tiers or self-only values) to callers.
    pub fn to_view(
        &self,
        viewer: Option<Uuid>,
        viewer_is_member: bool,
        viewer_is_operator: bool,
    ) -> MemberView {
        MemberView {
            lct_id: self.lct_id,
            name: self.name.clone(),
            skills: self.skills.clone(),
            profile: self.visible_profile(viewer, viewer_is_member, viewer_is_operator),
        }
    }
}

/// A filtered, serialization-ready view of a [`Member`]. The `profile` here is
/// the already-resolved `key → value` map the viewer is allowed to see; the
/// underlying visibility tier is not exposed.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct MemberView {
    pub lct_id: Uuid,
    pub name: Option<String>,
    pub skills: BTreeSet<String>,
    pub profile: BTreeMap<String, String>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum IntroStatus {
    Pending,
    Accepted,
    Declined,
}

/// A member↔member introduction. Created by `request_intro` over the sealed
/// channel; resolved by the target via `respond_intro`. On acceptance, each
/// party can retrieve the other's pinned pubkey — all a direct member↔member
/// pair_channel needs.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Intro {
    pub id: Uuid,
    pub from_lct: Uuid,
    pub to_lct: Uuid,
    pub purpose: Option<String>,
    pub status: IntroStatus,
}

impl HubState {
    /// Build the projection from a ledger.
    pub fn project(ledger: &HubLedger) -> Self {
        let mut state = HubState::default();
        state.advance(ledger, 0);
        state
    }

    /// Fold ledger entries at position `from..` into this state and return the
    /// next unfolded position. The ledger is append-only (entries are never
    /// rewritten and `index == position`), so folding only the tail is exact —
    /// this is the primitive behind an incremental projection cache: keep a
    /// state plus its high-water position and re-fold only what's new, turning
    /// per-query projection from O(ledger) into O(appended).
    pub fn advance(&mut self, ledger: &HubLedger, from: usize) -> usize {
        let entries = ledger.entries();
        let start = from.min(entries.len());
        for entry in &entries[start..] {
            self.apply(&entry.event, entry.timestamp);
            self.last_index = entry.index;
        }
        entries.len()
    }

    fn apply(&mut self, event: &HubEvent, ts: DateTime<Utc>) {
        match event {
            HubEvent::Genesis { hub_name, charter_hash, founding_sovereign_lct_id, .. } => {
                self.hub_name = hub_name.clone();
                self.charter_hash = Some(charter_hash.clone());
                self.founding_sovereign_lct_id = Some(*founding_sovereign_lct_id);
                // Sovereign is implicitly a member.
                self.members.entry(*founding_sovereign_lct_id)
                    .or_insert_with(|| Member {
                        lct_id: *founding_sovereign_lct_id,
                        name: Some("Sovereign".into()),
                        skills: BTreeSet::new(),
                        profile: std::collections::BTreeMap::new(),
                    });
            }
            HubEvent::MemberAdded { member_lct_id, member_name, member_pubkey_hex, .. } => {
                self.members.entry(*member_lct_id).or_insert_with(|| Member {
                    lct_id: *member_lct_id,
                    name: member_name.clone(),
                    skills: BTreeSet::new(),
                    profile: std::collections::BTreeMap::new(),
                });
                if let Some(pk) = member_pubkey_hex {
                    self.member_pubkeys.insert(*member_lct_id, pk.clone());
                }
            }
            HubEvent::MemberRemoved { member_lct_id, .. } => {
                if let Some(removed) = self.members.remove(member_lct_id) {
                    // Also drop from skill index.
                    for skill in &removed.skills {
                        if let Some(set) = self.skill_index.get_mut(skill) {
                            set.remove(member_lct_id);
                            if set.is_empty() {
                                self.skill_index.remove(skill);
                            }
                        }
                    }
                }
                // Drop the pinned channel key too — otherwise a removed member's
                // key lingers in the projection and gets re-seeded into the
                // resolver on the next serve restart (they'd still verify).
                self.member_pubkeys.remove(member_lct_id);
            }
            HubEvent::MemberJoinRequested {
                request_id, member_lct_id, member_pubkey_hex, name, message, requested_at,
            } => {
                self.pending_joins.insert(*request_id, JoinRequest {
                    request_id: *request_id,
                    member_lct_id: *member_lct_id,
                    member_pubkey_hex: member_pubkey_hex.clone(),
                    name: name.clone(),
                    message: message.clone(),
                    requested_at: *requested_at,
                    status: JoinStatus::Pending,
                    resolved_by: None,
                    reason: None,
                    resolved_at: None,
                });
            }
            HubEvent::MemberJoinResolved {
                request_id, approved, resolved_by, reason, resolved_at,
            } => {
                let member_lct = self.pending_joins.get(request_id).map(|jr| jr.member_lct_id);
                if let Some(jr) = self.pending_joins.get_mut(request_id) {
                    jr.status = if *approved { JoinStatus::Approved } else { JoinStatus::Denied };
                    jr.resolved_by = Some(*resolved_by);
                    jr.reason = reason.clone();
                    jr.resolved_at = Some(*resolved_at);
                }
                // Admission standing: a denial increments the repeat counter; an
                // approval (now a member) clears it.
                if let Some(lct) = member_lct {
                    if *approved {
                        self.admission.remove(&lct);
                    } else {
                        self.admission.entry(lct).or_default().denials += 1;
                    }
                }
            }
            HubEvent::MemberJoinReviewRequested {
                review_id, member_lct_id, plea, requested_at,
            } => {
                self.join_reviews.insert(*review_id, JoinReview {
                    review_id: *review_id,
                    member_lct_id: *member_lct_id,
                    plea: plea.clone(),
                    requested_at: *requested_at,
                    status: ReviewStatus::Pending,
                    resolved_by: None,
                    reason: None,
                    resolved_at: None,
                });
                self.admission.entry(*member_lct_id).or_default().reviews += 1;
            }
            HubEvent::MemberJoinReviewResolved {
                review_id, granted, resolved_by, reason, resolved_at,
            } => {
                let member_lct = self.join_reviews.get(review_id).map(|rv| rv.member_lct_id);
                if let Some(rv) = self.join_reviews.get_mut(review_id) {
                    rv.status = if *granted { ReviewStatus::Granted } else { ReviewStatus::Refused };
                    rv.resolved_by = Some(*resolved_by);
                    rv.reason = reason.clone();
                    rv.resolved_at = Some(*resolved_at);
                }
                // A granted review clears the auto-block: reset denials. The review
                // count keeps accumulating toward the cap until an operator reset.
                if *granted {
                    if let Some(lct) = member_lct {
                        if let Some(st) = self.admission.get_mut(&lct) { st.denials = 0; }
                    }
                }
            }
            HubEvent::MemberAdmissionReset { member_lct_id, .. } => {
                // Terminal backstop: full clear (denials + reviews).
                self.admission.remove(member_lct_id);
            }
            HubEvent::MemberSkillDeclared { member_lct_id, skill, .. } => {
                let key = skill.to_lowercase();
                if let Some(member) = self.members.get_mut(member_lct_id) {
                    member.skills.insert(key.clone());
                    self.skill_index.entry(key).or_default().insert(*member_lct_id);
                }
                // If member doesn't exist, silently ignore — event predates
                // their MemberAdded. (Real impl would error or queue.)
            }
            HubEvent::MemberKeyPinned { member_lct_id, member_pubkey_hex, .. } => {
                // Pin (or rotate — last write wins) the member's channel key.
                // Only for existing members: a pin for an unknown LCT is
                // ignored, same stance as the skill arm above.
                if self.members.contains_key(member_lct_id) {
                    self.member_pubkeys.insert(*member_lct_id, member_pubkey_hex.clone());
                }
            }
            HubEvent::DeviceEnrolled {
                owner_lct_id, device_lct_id, device_pubkey_hex, device_class,
                enrolled_at, enrollment_version,
            } => {
                // Only an admitted member may enroll devices into a constellation.
                // Insert or rotate — last write wins; a re-enroll reactivates.
                if self.members.contains_key(owner_lct_id) {
                    self.enrolled_devices
                        .entry(*owner_lct_id)
                        .or_default()
                        .insert(*device_lct_id, crate::constellation::EnrolledDevice {
                            owner_lct_id: *owner_lct_id,
                            device_lct_id: *device_lct_id,
                            pubkey_hex: device_pubkey_hex.clone(),
                            device_class: device_class.clone(),
                            status: crate::constellation::DeviceStatus::Active,
                            enrolled_at: *enrolled_at,
                            enrollment_version: *enrollment_version,
                        });
                }
            }
            HubEvent::DeviceRevoked { owner_lct_id, device_lct_id } => {
                if let Some(devs) = self.enrolled_devices.get_mut(owner_lct_id) {
                    if let Some(d) = devs.get_mut(device_lct_id) {
                        d.status = crate::constellation::DeviceStatus::Revoked;
                    }
                }
            }
            HubEvent::IntroRequested { intro_id, from_lct, to_lct, purpose } => {
                self.intros.entry(*intro_id).or_insert(Intro {
                    id: *intro_id,
                    from_lct: *from_lct,
                    to_lct: *to_lct,
                    purpose: purpose.clone(),
                    status: IntroStatus::Pending,
                });
            }
            HubEvent::IntroResponded { intro_id, responded_by, accepted } => {
                // Only the target may resolve, and only once (first response
                // wins; dispatch enforces this too — projection is defensive).
                if let Some(intro) = self.intros.get_mut(intro_id) {
                    if intro.status == IntroStatus::Pending && *responded_by == intro.to_lct {
                        intro.status = if *accepted { IntroStatus::Accepted } else { IntroStatus::Declined };
                    }
                }
            }
            HubEvent::MemberProfileUpdated { member_lct_id, fields, visibilities, .. } => {
                if let Some(member) = self.members.get_mut(member_lct_id) {
                    for (k, v) in fields {
                        if v.is_empty() {
                            member.profile.remove(k);
                        } else {
                            // A value-only update PRESERVES the field's existing
                            // tier (the documented contract) — defaulting an
                            // omitted tier to Members silently disclosed a
                            // SelfOnly field to all members (review 2026-07-23).
                            // Only a brand-new field defaults to Members.
                            let visibility = visibilities.get(k).copied().unwrap_or_else(|| {
                                member
                                    .profile
                                    .get(k)
                                    .map(|f| f.visibility)
                                    .unwrap_or_default()
                            });
                            member.profile.insert(k.clone(), ProfileField {
                                value: v.clone(),
                                visibility,
                            });
                        }
                    }
                }
            }
            HubEvent::RoleAssigned { .. }
            | HubEvent::EventRecorded { .. }
            | HubEvent::CharterAmended { .. }
            | HubEvent::LawAmended { .. }
            // Vault-unlock events are audit-only: the witnessed record of a
            // tier-2 M-of-N decision. They don't change member/role/pair state.
            | HubEvent::VaultUnlockRequested { .. }
            | HubEvent::VaultUnlockAttested { .. }
            | HubEvent::VaultUnlockResolved { .. }
            // Referenced acts are thin witnessed records; the substance lives at
            // pointer_uri, not in HubState.
            | HubEvent::ReferencedAct { .. } => {
                // Not projected into HubState yet — these affect society.json /
                // charter.json / hub-law.yaml instead. Future sprints surface
                // them here too.
            }
            // R7 reputation: fold the delta into the (subject, role) tensors. The
            // hub applies the delta (via T3/V3::apply_delta); the *weights* that
            // produced it are a society-law hook, computed by the recorder.
            HubEvent::ReputationRecorded { delta } => {
                let rep = self
                    .reputation
                    .entry((delta.subject_lct.clone(), delta.role_lct.clone()))
                    .or_insert_with(|| RoleReputation::new(ts));
                for (dim, td) in &delta.t3_delta {
                    if let Some(d) = trust_dim(dim) {
                        rep.t3.apply_delta(d, td.change);
                    }
                }
                for (dim, td) in &delta.v3_delta {
                    if let Some(d) = value_dim(dim) {
                        rep.v3.apply_delta(d, td.change);
                    }
                }
                // Fail-closed provenance: the bucket is only as strong as the
                // weakest delta that fed it. A placeholder-attested delta pins the
                // bucket to `placeholder` and no later hardware delta can upgrade
                // the placeholder-era observations back to `hardware`.
                rep.sovereign_strength = rep.sovereign_strength.min(delta.sovereign_strength);
                rep.observations += 1;
                rep.last_updated = ts;
            }
            HubEvent::ObligationOpened {
                request_id,
                subject_lct,
                role_lct,
                due_at,
                criticality,
                opened_at,
            } => {
                // Keep-first: a duplicate ObligationOpened for a live request_id
                // must NOT overwrite (that would let a subject reset its own
                // deadline clock). The channel handler already rejects re-opens
                // deny+warn; this is the projection-level backstop so any that
                // slip through (e.g. a concurrent-witness race) can't reset the
                // clock — the original opened_at/due_at stand.
                self.obligations.entry(request_id.clone()).or_insert_with(|| Obligation {
                    subject_lct: subject_lct.clone(),
                    role_lct: role_lct.clone(),
                    due_at: *due_at,
                    criticality: *criticality,
                    opened_at: *opened_at,
                });
            }
            HubEvent::ObligationResolved { request_id, .. } => {
                self.obligations.remove(request_id);
            }
            HubEvent::LctPublished { lct_id, document, published_by, provenance, published_at } => {
                // Republish of the same key overwrites in place and bumps
                // version; the id is pubkey-derived, so "same id" IS "same key".
                let version = self.registry.get(lct_id).map_or(1, |e| e.version + 1);
                self.registry.insert(lct_id.clone(), RegistryEntry {
                    document: document.clone(),
                    provenance: *provenance,
                    published_by: *published_by,
                    published_at: *published_at,
                    version,
                });
            }
            HubEvent::CouncilMemberAdded { member_lct_id, member_pubkey_hex, member_name, .. } => {
                self.council_holders.insert(*member_lct_id);
                self.council_pubkeys.insert(*member_lct_id, member_pubkey_hex.clone());
                // Council holders are also members (co-Sovereigns participate
                // in chapter life). Auto-add them to the member registry if
                // not already present, so /admin/members shows them.
                self.members.entry(*member_lct_id).or_insert_with(|| Member {
                    lct_id: *member_lct_id,
                    name: member_name.clone(),
                    skills: BTreeSet::new(),
                    profile: std::collections::BTreeMap::new(),
                });
                // Rebalance N component of threshold if set.
                if let Some((m, _)) = self.council_threshold {
                    let n = (self.council_holders.len() + 1) as u32;
                    self.council_threshold = Some((m, n));
                }
            }
            HubEvent::CouncilMemberRemoved { member_lct_id, .. } => {
                self.council_holders.remove(member_lct_id);
                self.council_pubkeys.remove(member_lct_id);
                if let Some((m, _)) = self.council_threshold {
                    let n = (self.council_holders.len() + 1) as u32;
                    // If removing a holder drops N below M, clamp M to N.
                    let m_clamped = m.min(n.max(1));
                    self.council_threshold = Some((m_clamped, n));
                }
            }
            HubEvent::CouncilThresholdChanged { new_m, .. } => {
                let n = (self.council_holders.len() + 1) as u32;
                let m = (*new_m).clamp(1, n.max(1));
                self.council_threshold = Some((m, n));
            }
            HubEvent::PairingRequested {
                pair_id, initiator_lct_id, counterparty_lct_id,
                purpose, proposed_at, expires_at,
                initiator_ephemeral_pub_hex,
            } => {
                // Idempotent: if a pair with this id already exists
                // (replay scenario), keep the original — the ledger's
                // chain integrity says the first occurrence wins.
                self.pairs.entry(*pair_id).or_insert_with(|| PairState {
                    id: *pair_id,
                    initiator: *initiator_lct_id,
                    counterparty: *counterparty_lct_id,
                    purpose: purpose.clone(),
                    status: PairStatus::Pending,
                    proposed_at: *proposed_at,
                    expires_at: *expires_at,
                    confirmed_at: None,
                    revoked_at: None,
                    revocation_kind: None,
                    revocation_reason: None,
                    message_count: 0,
                    initiator_ephemeral_pub_hex: initiator_ephemeral_pub_hex.clone(),
                    counterparty_ephemeral_pub_hex: None,
                });
            }
            HubEvent::PairingConfirmed { pair_id, confirmed_by, counterparty_ephemeral_pub_hex } => {
                // Confirmation is only valid from the counterparty
                // (REST layer enforces this; here we defensively
                // re-check so a hand-crafted ledger entry can't
                // sneak through projection).
                if let Some(p) = self.pairs.get_mut(pair_id) {
                    if p.status == PairStatus::Pending
                        && *confirmed_by == p.counterparty
                    {
                        p.status = PairStatus::Active;
                        p.confirmed_at = Some(ts);
                        // Sprint F: record counterparty's ephemeral if supplied.
                        if counterparty_ephemeral_pub_hex.is_some() {
                            p.counterparty_ephemeral_pub_hex =
                                counterparty_ephemeral_pub_hex.clone();
                        }
                    }
                    // Else: confirmation from non-counterparty, or
                    // already-active/revoked — silent no-op. The
                    // REST layer should have prevented this; not
                    // worth crashing projection if it slips through.
                }
            }
            HubEvent::PairingRevoked {
                pair_id, revoked_by: _, revocation_kind, reason,
            } => {
                if let Some(p) = self.pairs.get_mut(pair_id) {
                    // Revocation is allowed from either party; chapter
                    // law / V2-9 council enforcement is the only way to
                    // restrict who can revoke. Once revoked, stays
                    // revoked (subsequent revoke events are no-ops).
                    if p.status != PairStatus::Revoked {
                        p.status = PairStatus::Revoked;
                        p.revoked_at = Some(ts);
                        p.revocation_kind = Some(revocation_kind.clone());
                        p.revocation_reason = reason.clone();
                    }
                }
            }
            HubEvent::PairMessagePosted { pair_id, .. } => {
                // Sprint D: bump per-pair message_count. The actual
                // payload lives in the sidecar (HubStore::append_pair_message);
                // projection just counts that a message happened. This
                // is what feeds V3 trust accrual in Sprint G.
                if let Some(p) = self.pairs.get_mut(pair_id) {
                    p.message_count = p.message_count.saturating_add(1);
                }
            }
        }
    }

    /// Members who declared a skill matching the query (case-insensitive substring).
    pub fn find_skill(&self, query: &str) -> Vec<&Member> {
        let q = query.to_lowercase();
        let mut out = Vec::new();
        let mut seen: BTreeSet<Uuid> = BTreeSet::new();
        for (skill, lct_ids) in &self.skill_index {
            if skill.contains(&q) {
                for id in lct_ids {
                    if seen.insert(*id) {
                        if let Some(m) = self.members.get(id) {
                            out.push(m);
                        }
                    }
                }
            }
        }
        out
    }

    pub fn member_count(&self) -> usize { self.members.len() }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::hub::HubPaths;
    use crate::identity::IdentityFile;
    use crate::ledger::HubLedger;
    use crate::store::FileBackend;
    use chrono::Utc;
    use tempfile::tempdir;
    use web4_core::lct::EntityType;

    async fn make_ledger_with(events: Vec<(Uuid, &web4_core::crypto::KeyPair, HubEvent)>)
        -> (tempfile::TempDir, HubLedger)
    {
        let tmp = tempdir().unwrap();
        let chap = tmp.path().join("chap");
        std::fs::create_dir_all(&chap).unwrap();
        let store: Box<dyn crate::store::HubStore> =
            Box::new(FileBackend::new(HubPaths::new(chap)));
        let mut ledger = HubLedger::open(store).await.unwrap();
        for (actor, kp, event) in events {
            // First event must be Genesis; for tests we treat all as plain entries
            // but use write_genesis for the first.
            if ledger.is_empty() {
                if let HubEvent::Genesis { hub_name, charter_hash, founding_sovereign_lct_id, .. } = &event {
                    ledger.write_genesis(
                        *founding_sovereign_lct_id, kp,
                        hub_name.clone(),
                        charter_hash.clone(),
                    ).await.unwrap();
                    continue;
                } else {
                    panic!("first event in test fixture must be Genesis");
                }
            }
            ledger.append(actor, kp, event).await.unwrap();
        }
        (tmp, ledger)
    }

    #[tokio::test]
    async fn project_genesis_seeds_sovereign_as_member() {
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "Test".into(),
                charter_hash: "sha256:0".into(),
                founding_sovereign_lct_id: sov.lct.id,
                created_at: Utc::now(),
            }),
        ]).await;
        let state = HubState::project(&ledger);
        assert_eq!(state.member_count(), 1);
        assert!(state.members.contains_key(&sov.lct.id));
    }

    #[tokio::test]
    async fn device_enrollment_projects_and_revoke_flips_status() {
        use crate::constellation::{DeviceStatus, DeviceType};
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let owner = sov.lct.id;
        let dev = Uuid::new_v4();
        let pk_hex = "aa".repeat(32); // 32-byte hex; projection stores verbatim
        let genesis = HubEvent::Genesis {
            hub_name: "Test".into(), charter_hash: "sha256:0".into(),
            founding_sovereign_lct_id: owner, created_at: Utc::now(),
        };
        let enroll = HubEvent::DeviceEnrolled {
            owner_lct_id: owner, device_lct_id: dev, device_pubkey_hex: pk_hex.clone(),
            device_class: DeviceType::Hardware, enrolled_at: Utc::now(), enrollment_version: 1,
        };

        // Enrolled → Active, class from the record.
        let (_t, ledger) = make_ledger_with(vec![
            (owner, &kp, genesis.clone()), (owner, &kp, enroll.clone()),
        ]).await;
        let state = HubState::project(&ledger);
        let rec = state.enrolled_devices.get(&owner).and_then(|d| d.get(&dev)).unwrap();
        assert_eq!(rec.device_class, DeviceType::Hardware);
        assert_eq!(rec.status, DeviceStatus::Active);
        assert_eq!(rec.pubkey_hex, pk_hex);

        // Revoke flips status; the record stays (auditable), just doesn't count.
        let (_t2, ledger2) = make_ledger_with(vec![
            (owner, &kp, genesis), (owner, &kp, enroll),
            (owner, &kp, HubEvent::DeviceRevoked { owner_lct_id: owner, device_lct_id: dev }),
        ]).await;
        let state2 = HubState::project(&ledger2);
        assert_eq!(
            state2.enrolled_devices[&owner][&dev].status, DeviceStatus::Revoked);
    }

    #[tokio::test]
    async fn reputation_recorded_folds_into_role_pairing() {
        use std::collections::HashMap;
        use web4_core::t3::{T3, TrustDimension};
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let subject = Uuid::new_v4().to_string();
        let mut t3_delta = HashMap::new();
        t3_delta.insert("temperament".to_string(),
            web4_core::r6::TensorDelta { change: 0.2, from_value: 0.0, to_value: 0.2 });
        let delta = web4_core::r6::ReputationDelta {
            subject_lct: subject.clone(),
            role_lct: "citizen".to_string(),
            sovereign_strength: web4_core::r6::SovereignStrength::Hardware,
            action_type: "handoff".into(),
            action_target: "hub".into(),
            action_id: "act-1".into(),
            rule_triggered: "on_time".into(),
            reason: "delivered on time".into(),
            t3_delta,
            v3_delta: HashMap::new(),
            contributing_factors: vec![],
            witnesses: vec![],
            timestamp: Utc::now(),
        };
        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "Test".into(), charter_hash: "sha256:0".into(),
                founding_sovereign_lct_id: sov.lct.id, created_at: Utc::now(),
            }),
            (sov.lct.id, &kp, HubEvent::ReputationRecorded { delta }),
        ]).await;
        let state = HubState::project(&ledger);
        let rep = state.reputation.get(&(subject.clone(), "citizen".to_string()))
            .expect("reputation projected for the (subject, citizen) role-pairing");
        assert_eq!(rep.observations, 1);
        let before = T3::default().score(TrustDimension::Temperament);
        assert!(rep.t3.score(TrustDimension::Temperament) >= before, "temperament folded up");
        // Role-contextualized: a different role for the SAME subject is a distinct
        // pairing (no global reputation) — nothing there.
        assert!(state.reputation.get(&(subject, "treasurer".to_string())).is_none());
        // Single hardware-attested delta → the bucket reports `hardware`.
        assert_eq!(rep.sovereign_strength, web4_core::r6::SovereignStrength::Hardware);
    }

    #[tokio::test]
    async fn fold_pins_bucket_to_weakest_sovereign_strength() {
        // HUB Concern 2 (identity-p1-cospec): a placeholder-attested delta pins the
        // (subject, role) bucket to `placeholder`, and a later hardware delta must
        // NOT upgrade the placeholder-era observations back to `hardware`.
        use std::collections::HashMap;
        use web4_core::r6::{ReputationDelta, SovereignStrength, TensorDelta};
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let subject = Uuid::new_v4().to_string();
        let mk = |strength: SovereignStrength, id: &str| {
            let mut t3 = HashMap::new();
            t3.insert("temperament".to_string(),
                TensorDelta { change: 0.1, from_value: 0.0, to_value: 0.1 });
            ReputationDelta {
                subject_lct: subject.clone(),
                role_lct: "role:constellation:mesh-worker".to_string(),
                sovereign_strength: strength,
                action_type: "act".into(), action_target: "hub".into(), action_id: id.into(),
                rule_triggered: "r".into(), reason: "x".into(),
                t3_delta: t3, v3_delta: HashMap::new(),
                contributing_factors: vec![], witnesses: vec![], timestamp: Utc::now(),
            }
        };
        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "Test".into(), charter_hash: "sha256:0".into(),
                founding_sovereign_lct_id: sov.lct.id, created_at: Utc::now(),
            }),
            // hardware first, then a placeholder delta, then hardware again.
            (sov.lct.id, &kp, HubEvent::ReputationRecorded { delta: mk(SovereignStrength::Hardware, "a1") }),
            (sov.lct.id, &kp, HubEvent::ReputationRecorded { delta: mk(SovereignStrength::Placeholder, "a2") }),
            (sov.lct.id, &kp, HubEvent::ReputationRecorded { delta: mk(SovereignStrength::Hardware, "a3") }),
        ]).await;
        let state = HubState::project(&ledger);
        let rep = state.reputation
            .get(&(subject, "role:constellation:mesh-worker".to_string()))
            .expect("bucket projected");
        assert_eq!(rep.observations, 3);
        assert_eq!(rep.sovereign_strength, SovereignStrength::Placeholder,
            "one placeholder delta must pin the whole bucket to placeholder (fail-closed)");
    }

    #[tokio::test]
    async fn hub_state_with_reputation_serializes_as_array() {
        // Guards the tuple-key landmine: a `(String, String)`-keyed map can't be a
        // JSON object, so without the custom serializer `to_string(&state)` would
        // fail at runtime. It must succeed and emit reputation as an array.
        use std::collections::HashMap;
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let subject = Uuid::new_v4().to_string();
        let mut t3_delta = HashMap::new();
        t3_delta.insert("talent".to_string(),
            web4_core::r6::TensorDelta { change: 0.1, from_value: 0.0, to_value: 0.1 });
        let delta = web4_core::r6::ReputationDelta {
            subject_lct: subject.clone(),
            role_lct: "citizen".to_string(),
            sovereign_strength: Default::default(),
            action_type: "handoff".into(), action_target: "hub".into(), action_id: "a".into(),
            rule_triggered: "r".into(), reason: "x".into(),
            t3_delta, v3_delta: HashMap::new(),
            contributing_factors: vec![], witnesses: vec![], timestamp: Utc::now(),
        };
        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "Test".into(), charter_hash: "sha256:0".into(),
                founding_sovereign_lct_id: sov.lct.id, created_at: Utc::now(),
            }),
            (sov.lct.id, &kp, HubEvent::ReputationRecorded { delta }),
        ]).await;
        let state = HubState::project(&ledger);
        let json = serde_json::to_value(&state).expect("HubState must serialize");
        let arr = json["reputation"].as_array().expect("reputation is a JSON array");
        assert_eq!(arr.len(), 1);
        assert_eq!(arr[0]["subject_lct"], serde_json::json!(subject));
        assert_eq!(arr[0]["role_lct"], serde_json::json!("citizen"));
        assert_eq!(arr[0]["observations"], serde_json::json!(1));
    }

    #[tokio::test]
    async fn member_added_and_removed_round_trip() {
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let alice = Uuid::new_v4();
        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "Test".into(),
                charter_hash: "sha256:0".into(),
                founding_sovereign_lct_id: sov.lct.id,
                created_at: Utc::now(),
            }),
            (sov.lct.id, &kp, HubEvent::MemberAdded {
                member_lct_id: alice,
                added_by: sov.lct.id,
                member_name: Some("Alice".into()),
                member_pubkey_hex: None,
            }),
            (sov.lct.id, &kp, HubEvent::MemberSkillDeclared {
                member_lct_id: alice,
                skill: "Rust".into(),
                declared_by: sov.lct.id,
            }),
            (sov.lct.id, &kp, HubEvent::MemberRemoved {
                member_lct_id: alice,
                removed_by: sov.lct.id,
                reason: Some("left chapter".into()),
            }),
        ]).await;
        let state = HubState::project(&ledger);
        assert_eq!(state.member_count(), 1); // just Sovereign
        assert!(!state.members.contains_key(&alice));
        // Skill index should also drop the orphaned skill entry.
        assert!(state.find_skill("rust").is_empty());
    }

    #[tokio::test]
    async fn advance_folds_only_the_tail_and_matches_full_projection() {
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let alice = Uuid::new_v4();
        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "Test".into(), charter_hash: "sha256:0".into(),
                founding_sovereign_lct_id: sov.lct.id, created_at: Utc::now(),
            }),
            (sov.lct.id, &kp, HubEvent::MemberAdded {
                member_lct_id: alice, added_by: sov.lct.id,
                member_name: Some("Alice".into()), member_pubkey_hex: None,
            }),
        ]).await;
        let full = HubState::project(&ledger);

        // Folding from 0 reproduces the full projection and reports the tail.
        let mut inc = HubState::default();
        let next = inc.advance(&ledger, 0);
        assert_eq!(next, ledger.entries().len());
        assert_eq!(inc.member_count(), full.member_count());
        assert_eq!(inc.last_index, full.last_index);
        assert!(inc.members.contains_key(&alice));

        // Advancing again from the high-water mark folds nothing (idempotent).
        let members_before = inc.member_count();
        let next2 = inc.advance(&ledger, next);
        assert_eq!(next2, next);
        assert_eq!(inc.member_count(), members_before);
    }

    #[tokio::test]
    async fn find_skill_is_case_insensitive_substring() {
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let alice = Uuid::new_v4();
        let bob = Uuid::new_v4();
        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "Test".into(),
                charter_hash: "sha256:0".into(),
                founding_sovereign_lct_id: sov.lct.id,
                created_at: Utc::now(),
            }),
            (sov.lct.id, &kp, HubEvent::MemberAdded { member_lct_id: alice, added_by: sov.lct.id, member_name: Some("Alice".into()), member_pubkey_hex: None }),
            (sov.lct.id, &kp, HubEvent::MemberAdded { member_lct_id: bob, added_by: sov.lct.id, member_name: Some("Bob".into()), member_pubkey_hex: None }),
            (sov.lct.id, &kp, HubEvent::MemberSkillDeclared { member_lct_id: alice, skill: "Medical Imaging RAG".into(), declared_by: sov.lct.id }),
            (sov.lct.id, &kp, HubEvent::MemberSkillDeclared { member_lct_id: bob, skill: "Distributed Systems".into(), declared_by: sov.lct.id }),
        ]).await;
        let state = HubState::project(&ledger);
        let matches = state.find_skill("RAG");
        assert_eq!(matches.len(), 1);
        assert_eq!(matches[0].lct_id, alice);

        let matches = state.find_skill("imaging");
        assert_eq!(matches.len(), 1);

        let matches = state.find_skill("nothing");
        assert_eq!(matches.len(), 0);
    }

    // ---------- PAIRED-CHANNELS Sprint B ----------

    /// Happy path: request → confirm → projection shows Active pair
    /// with correct initiator/counterparty/purpose; the entry's
    /// timestamp from the ledger is the `confirmed_at`.
    #[tokio::test]
    async fn pair_request_then_confirm_projects_active() {
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let alice = Uuid::new_v4();
        let bob = Uuid::new_v4();
        let pair_id = Uuid::new_v4();
        let t0 = Utc::now();

        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "Pairs Test".into(),
                charter_hash: "sha256:0".into(),
                founding_sovereign_lct_id: sov.lct.id,
                created_at: t0,
            }),
            (alice, &kp, HubEvent::PairingRequested {
                pair_id,
                initiator_lct_id: alice,
                counterparty_lct_id: bob,
                purpose: "code review collab".into(),
                proposed_at: t0,
                expires_at: None,
            initiator_ephemeral_pub_hex: None,
            }),
            (bob, &kp, HubEvent::PairingConfirmed {
                pair_id,
                confirmed_by: bob,
            counterparty_ephemeral_pub_hex: None,
            }),
        ]).await;

        let state = HubState::project(&ledger);
        let pair = state.pairs.get(&pair_id).expect("pair projected");
        assert_eq!(pair.id, pair_id);
        assert_eq!(pair.initiator, alice);
        assert_eq!(pair.counterparty, bob);
        assert_eq!(pair.purpose, "code review collab");
        assert_eq!(pair.status, PairStatus::Active);
        assert!(pair.confirmed_at.is_some());
        assert!(pair.includes(alice));
        assert!(pair.includes(bob));
        assert!(!pair.includes(Uuid::new_v4()));
    }

    /// Confirmation from someone OTHER than the named counterparty
    /// must be a no-op at projection level (REST layer should have
    /// rejected; this is defense in depth).
    #[tokio::test]
    async fn pair_confirmation_from_wrong_signer_is_ignored() {
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let alice = Uuid::new_v4();
        let bob = Uuid::new_v4();
        let mallory = Uuid::new_v4();
        let pair_id = Uuid::new_v4();
        let t0 = Utc::now();

        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "Pairs Test".into(),
                charter_hash: "sha256:0".into(),
                founding_sovereign_lct_id: sov.lct.id,
                created_at: t0,
            }),
            (alice, &kp, HubEvent::PairingRequested {
                pair_id,
                initiator_lct_id: alice,
                counterparty_lct_id: bob,
                purpose: "p".into(),
                proposed_at: t0,
                expires_at: None,
            initiator_ephemeral_pub_hex: None,
            }),
            // Mallory (not the counterparty) confirms — must be rejected.
            (mallory, &kp, HubEvent::PairingConfirmed {
                pair_id,
                confirmed_by: mallory,
            counterparty_ephemeral_pub_hex: None,
            }),
        ]).await;

        let state = HubState::project(&ledger);
        let pair = state.pairs.get(&pair_id).expect("pair exists");
        assert_eq!(pair.status, PairStatus::Pending,
            "confirmation from non-counterparty must not activate the pair");
        assert!(pair.confirmed_at.is_none());
    }

    /// Revoke-before-confirm cancels the pending pair. Status moves
    /// straight to Revoked without ever becoming Active.
    #[tokio::test]
    async fn pair_revoke_before_confirm_cancels() {
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let alice = Uuid::new_v4();
        let bob = Uuid::new_v4();
        let pair_id = Uuid::new_v4();
        let t0 = Utc::now();

        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "Pairs Test".into(),
                charter_hash: "sha256:0".into(),
                founding_sovereign_lct_id: sov.lct.id,
                created_at: t0,
            }),
            (alice, &kp, HubEvent::PairingRequested {
                pair_id,
                initiator_lct_id: alice,
                counterparty_lct_id: bob,
                purpose: "p".into(),
                proposed_at: t0,
                expires_at: None,
            initiator_ephemeral_pub_hex: None,
            }),
            (alice, &kp, HubEvent::PairingRevoked {
                pair_id,
                revoked_by: alice,
                revocation_kind: PairRevocationKind::Voluntary,
                reason: Some("changed my mind".into()),
            }),
        ]).await;

        let state = HubState::project(&ledger);
        let pair = state.pairs.get(&pair_id).unwrap();
        assert_eq!(pair.status, PairStatus::Revoked);
        assert!(pair.confirmed_at.is_none(), "never reached Active");
        assert!(pair.revoked_at.is_some());
        assert_eq!(pair.revocation_kind, Some(PairRevocationKind::Voluntary));
        assert_eq!(pair.revocation_reason.as_deref(), Some("changed my mind"));
    }

    /// Once revoked, subsequent revoke events don't bump the revocation
    /// timestamp / kind. First revocation is canonical.
    #[tokio::test]
    async fn pair_revoke_is_idempotent() {
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let alice = Uuid::new_v4();
        let bob = Uuid::new_v4();
        let pair_id = Uuid::new_v4();
        let t0 = Utc::now();

        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "Pairs Test".into(),
                charter_hash: "sha256:0".into(),
                founding_sovereign_lct_id: sov.lct.id,
                created_at: t0,
            }),
            (alice, &kp, HubEvent::PairingRequested {
                pair_id, initiator_lct_id: alice, counterparty_lct_id: bob,
                purpose: "p".into(), proposed_at: t0, expires_at: None,
            initiator_ephemeral_pub_hex: None,
            }),
            (alice, &kp, HubEvent::PairingRevoked {
                pair_id, revoked_by: alice,
                revocation_kind: PairRevocationKind::Voluntary,
                reason: Some("first".into()),
            }),
            (alice, &kp, HubEvent::PairingRevoked {
                pair_id, revoked_by: alice,
                revocation_kind: PairRevocationKind::HubLaw,
                reason: Some("second — should be ignored".into()),
            }),
        ]).await;

        let state = HubState::project(&ledger);
        let pair = state.pairs.get(&pair_id).unwrap();
        assert_eq!(pair.revocation_kind, Some(PairRevocationKind::Voluntary),
            "first revocation wins; second is no-op");
        assert_eq!(pair.revocation_reason.as_deref(), Some("first"));
    }

    /// Multiple distinct pairs coexist without interference.
    #[tokio::test]
    async fn multiple_pairs_project_independently() {
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let alice = Uuid::new_v4();
        let bob = Uuid::new_v4();
        let carol = Uuid::new_v4();
        let p1 = Uuid::new_v4();
        let p2 = Uuid::new_v4();
        let t0 = Utc::now();

        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "T".into(), charter_hash: "0".into(),
                founding_sovereign_lct_id: sov.lct.id, created_at: t0,
            }),
            // alice-bob: confirmed
            (alice, &kp, HubEvent::PairingRequested {
                pair_id: p1, initiator_lct_id: alice, counterparty_lct_id: bob,
                purpose: "p1".into(), proposed_at: t0, expires_at: None,
            initiator_ephemeral_pub_hex: None,
            }),
            (bob, &kp, HubEvent::PairingConfirmed { pair_id: p1, confirmed_by: bob, counterparty_ephemeral_pub_hex: None }),
            // alice-carol: still pending
            (alice, &kp, HubEvent::PairingRequested {
                pair_id: p2, initiator_lct_id: alice, counterparty_lct_id: carol,
                purpose: "p2".into(), proposed_at: t0, expires_at: None,
            initiator_ephemeral_pub_hex: None,
            }),
        ]).await;

        let state = HubState::project(&ledger);
        assert_eq!(state.pairs.len(), 2);
        assert_eq!(state.pairs[&p1].status, PairStatus::Active);
        assert_eq!(state.pairs[&p2].status, PairStatus::Pending);
        // Alice is in both; bob in only p1; carol in only p2.
        let alices_pairs: Vec<_> = state.pairs.values()
            .filter(|p| p.includes(alice)).collect();
        assert_eq!(alices_pairs.len(), 2);
    }

    /// `effective_status` returns "expired" when past `expires_at`
    /// even though the stored status is still Active.
    #[tokio::test]
    async fn pair_effective_status_handles_expiry() {
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let alice = Uuid::new_v4();
        let bob = Uuid::new_v4();
        let pair_id = Uuid::new_v4();
        let t0 = Utc::now();
        let expires = t0 + chrono::Duration::seconds(60);

        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "T".into(), charter_hash: "0".into(),
                founding_sovereign_lct_id: sov.lct.id, created_at: t0,
            }),
            (alice, &kp, HubEvent::PairingRequested {
                pair_id, initiator_lct_id: alice, counterparty_lct_id: bob,
                purpose: "p".into(), proposed_at: t0,
                expires_at: Some(expires),
            initiator_ephemeral_pub_hex: None,
            }),
            (bob, &kp, HubEvent::PairingConfirmed { pair_id, confirmed_by: bob, counterparty_ephemeral_pub_hex: None }),
        ]).await;

        let state = HubState::project(&ledger);
        let pair = state.pairs.get(&pair_id).unwrap();
        assert_eq!(pair.effective_status(t0 + chrono::Duration::seconds(30)), "active");
        assert_eq!(pair.effective_status(t0 + chrono::Duration::seconds(120)), "expired");
    }

    /// Serde round-trip for the new event types via the existing
    /// HubEvent kind-tag machinery. Catches schema-level breakage.
    #[tokio::test]
    async fn pair_events_serde_round_trip() {
        let pair_id = Uuid::new_v4();
        let alice = Uuid::new_v4();
        let bob = Uuid::new_v4();
        let t0 = Utc::now();

        let req = HubEvent::PairingRequested {
            pair_id, initiator_lct_id: alice, counterparty_lct_id: bob,
            purpose: "x".into(), proposed_at: t0, expires_at: None,
        initiator_ephemeral_pub_hex: None,
        };
        let req_json = serde_json::to_string(&req).unwrap();
        assert!(req_json.contains("\"kind\":\"pairing_requested\""));
        let back: HubEvent = serde_json::from_str(&req_json).unwrap();
        assert_eq!(back.kind(), "pairing_requested");

        let conf = HubEvent::PairingConfirmed { pair_id, confirmed_by: bob, counterparty_ephemeral_pub_hex: None };
        let conf_json = serde_json::to_string(&conf).unwrap();
        assert!(conf_json.contains("\"kind\":\"pairing_confirmed\""));

        let rev = HubEvent::PairingRevoked {
            pair_id, revoked_by: alice,
            revocation_kind: PairRevocationKind::HubLaw,
            reason: None,
        };
        let rev_json = serde_json::to_string(&rev).unwrap();
        assert!(rev_json.contains("\"kind\":\"pairing_revoked\""));
        // Canonical form after the chapter→hub rename.
        assert!(rev_json.contains("\"revocation_kind\":\"hub_law\""));
        // No reason -> field skipped
        assert!(!rev_json.contains("\"reason\""));

        // Back-compat: pre-rename ledgers serialized this as "chapter_law";
        // the serde alias must still deserialize them.
        let legacy = rev_json.replace("\"hub_law\"", "\"chapter_law\"");
        let back: HubEvent = serde_json::from_str(&legacy).unwrap();
        match back {
            HubEvent::PairingRevoked { revocation_kind, .. } => {
                assert_eq!(revocation_kind, PairRevocationKind::HubLaw);
            }
            _ => panic!("expected PairingRevoked"),
        }
    }

    #[tokio::test]
    async fn value_only_profile_update_preserves_visibility_tier() {
        // Review 2026-07-23: a value update that omits the tier used to reset
        // a SelfOnly field to Members — silent re-disclosure. The contract:
        // omitted tier on an EXISTING field preserves it; a NEW field
        // defaults to Members.
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let owner = sov.lct.id;
        let genesis = HubEvent::Genesis {
            hub_name: "Test".into(), charter_hash: "sha256:0".into(),
            founding_sovereign_lct_id: owner, created_at: Utc::now(),
        };
        let mut set_secret = BTreeMap::new();
        set_secret.insert("phone".to_string(), "555-0100".to_string());
        let mut set_secret_vis = BTreeMap::new();
        set_secret_vis.insert("phone".to_string(), ProfileVisibility::SelfOnly);
        let create = HubEvent::MemberProfileUpdated {
            member_lct_id: owner,
            fields: set_secret,
            visibilities: set_secret_vis,
            updated_by: owner,
        };
        // Value-only update: NO visibilities map (what a client that doesn't
        // resend tiers produces).
        let mut new_value = BTreeMap::new();
        new_value.insert("phone".to_string(), "555-0199".to_string());
        let mut brand_new = new_value.clone();
        brand_new.insert("website".to_string(), "example.org".to_string());
        let update = HubEvent::MemberProfileUpdated {
            member_lct_id: owner,
            fields: brand_new,
            visibilities: BTreeMap::new(),
            updated_by: owner,
        };
        let (_t, ledger) = make_ledger_with(vec![
            (owner, &kp, genesis), (owner, &kp, create), (owner, &kp, update),
        ]).await;
        let state = HubState::project(&ledger);
        let member = state.members.get(&owner).unwrap();
        let phone = member.profile.get("phone").unwrap();
        assert_eq!(phone.value, "555-0199", "value updated");
        assert_eq!(
            phone.visibility,
            ProfileVisibility::SelfOnly,
            "omitted tier PRESERVES the existing SelfOnly — no silent re-disclosure"
        );
        assert_eq!(
            member.profile.get("website").unwrap().visibility,
            ProfileVisibility::Members,
            "brand-new field defaults to Members"
        );
    }

    #[test]
    fn visible_profile_respects_tiers() {
        let alice = Uuid::new_v4();
        let bob = Uuid::new_v4();
        let mut profile = BTreeMap::new();
        profile.insert("public".into(), ProfileField::new("pub", ProfileVisibility::Public));
        profile.insert("members".into(), ProfileField::new("mem", ProfileVisibility::Members));
        profile.insert("self".into(), ProfileField::new("secret", ProfileVisibility::SelfOnly));
        let member = Member {
            lct_id: alice,
            name: Some("Alice".into()),
            skills: BTreeSet::new(),
            profile,
        };

        // Self sees all three.
        let self_view = member.visible_profile(Some(alice), true, false);
        assert_eq!(self_view.len(), 3);
        assert_eq!(self_view.get("self"), Some(&"secret".to_string()));

        // Another member sees public + members, not self.
        let member_view = member.visible_profile(Some(bob), true, false);
        assert_eq!(member_view.len(), 2);
        assert!(member_view.contains_key("public"));
        assert!(member_view.contains_key("members"));
        assert!(!member_view.contains_key("self"));

        // Operator sees everything.
        let op_view = member.visible_profile(None, true, true);
        assert_eq!(op_view.len(), 3);

        // Anonymous/external sees only public.
        let anon_view = member.visible_profile(None, false, false);
        assert_eq!(anon_view.len(), 1);
        assert_eq!(anon_view.get("public"), Some(&"pub".to_string()));
    }

    #[test]
    fn to_view_serializes_filtered_profile_only() {
        let alice = Uuid::new_v4();
        let mut profile = BTreeMap::new();
        profile.insert("bio".into(), ProfileField::new("hi", ProfileVisibility::Public));
        profile.insert("phone".into(), ProfileField::new("555", ProfileVisibility::SelfOnly));
        let member = Member {
            lct_id: alice,
            name: Some("Alice".into()),
            skills: BTreeSet::from(["rust".into()]),
            profile,
        };
        let view = member.to_view(Some(alice), true, false);
        assert_eq!(view.lct_id, alice);
        assert_eq!(view.profile.len(), 2);
        assert!(!serde_json::to_string(&view).unwrap().contains("\"visibility\""),
            "MemberView must not expose the visibility tier metadata");
    }
}
