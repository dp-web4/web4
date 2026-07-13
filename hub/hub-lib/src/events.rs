// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Hub event types.
//!
//! These are the *domain* events a chapter records — distinct from
//! `web4_core::ledger::LedgerEvent` which is about LCT anchoring (mint /
//! status-change). The hub's HubLedger records the hub's social
//! and governance actions on top of (and alongside) any LCT anchoring
//! that web4-core handles.
//!
//! Each event variant captures who/what/when for one consequential
//! chapter action. The Sovereign signs Genesis. Subsequent events are
//! signed by the actor whose LCT id is named in the enclosing
//! `LedgerEntry::actor_lct_id`.
//!
//! Reusing `web4_core::role::SocietyRole` for the RoleAssigned variant —
//! no hub-side redefinition.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use web4_core::act::Act;
use web4_core::lct::Lct;
use web4_core::role::SocietyRole;

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum HubEvent {
    /// First entry in any hub ledger. Established at chapter init.
    Genesis {
        hub_name: String,
        charter_hash: String,
        founding_sovereign_lct_id: Uuid,
        created_at: DateTime<Utc>,
    },

    /// A member's LCT was registered as a hub Citizen.
    MemberAdded {
        member_lct_id: Uuid,
        added_by: Uuid,
        member_name: Option<String>,
        /// Member's public key, hex-encoded 32 bytes (V2-12 addition).
        /// Allows the hub to verify future envelopes signed by this
        /// member without an external registry. Optional for back-compat
        /// with chapters that added members via Sovereign-only CLI flow
        /// before V2-12 — those members can't sign envelopes until
        /// re-added with a pubkey.
        #[serde(default, skip_serializing_if = "Option::is_none")]
        member_pubkey_hex: Option<String>,
    },

    /// A member's Citizen status was revoked.
    MemberRemoved {
        member_lct_id: Uuid,
        removed_by: Uuid,
        reason: Option<String>,
    },

    /// A prospective member submitted a join request that hub law **escalated**
    /// to operator review (V2-16 admission queue). The applicant self-vouches
    /// `member_pubkey_hex` (the hub bootstraps signature verification from it);
    /// nothing is admitted until a matching `MemberJoinResolved{approved:true}`
    /// — and the actual `MemberAdded` — is recorded by the Sovereign. Law-`Allow`
    /// joins are auto-admitted and skip the queue; law-`Deny` joins are rejected
    /// and never recorded. `request_id` ties the request to its resolution.
    MemberJoinRequested {
        request_id: Uuid,
        member_lct_id: Uuid,
        member_pubkey_hex: String,
        #[serde(default, skip_serializing_if = "Option::is_none")]
        name: Option<String>,
        /// Optional free-text note from the applicant (shown to the operator).
        #[serde(default, skip_serializing_if = "Option::is_none")]
        message: Option<String>,
        requested_at: DateTime<Utc>,
    },

    /// An operator (Sovereign) resolved a pending join request — approved or
    /// denied. On approval a `MemberAdded` is recorded alongside (the actual
    /// admission); this event closes the queue entry, recording who decided and
    /// why. The membrane is fully auditable: request → resolution, both witnessed.
    MemberJoinResolved {
        request_id: Uuid,
        approved: bool,
        resolved_by: Uuid,
        #[serde(default, skip_serializing_if = "Option::is_none")]
        reason: Option<String>,
        resolved_at: DateTime<Utc>,
    },

    /// A blocked applicant (≥ admission `repeat_limit` denials) requested a
    /// denial-review — the only self-service way to clear the auto-block. Goes to
    /// the operator review queue; capped at the law's `review_limit`, after which
    /// it's terminal until an operator `MemberAdmissionReset`.
    MemberJoinReviewRequested {
        review_id: Uuid,
        member_lct_id: Uuid,
        #[serde(default, skip_serializing_if = "Option::is_none")]
        plea: Option<String>,
        requested_at: DateTime<Utc>,
    },

    /// An operator resolved a denial-review. `granted: true` clears the
    /// applicant's auto-block (denial count resets → they may apply afresh);
    /// `false` refuses it (counts toward the review limit). Witnessed for audit.
    MemberJoinReviewResolved {
        review_id: Uuid,
        granted: bool,
        resolved_by: Uuid,
        #[serde(default, skip_serializing_if = "Option::is_none")]
        reason: Option<String>,
        resolved_at: DateTime<Utc>,
    },

    /// Operator hard-reset of an applicant's admission standing — the terminal
    /// backstop. Clears both denial and review counts so the LCT may apply afresh
    /// even after the review path is exhausted.
    MemberAdmissionReset {
        member_lct_id: Uuid,
        reset_by: Uuid,
        #[serde(default, skip_serializing_if = "Option::is_none")]
        reason: Option<String>,
        reset_at: DateTime<Utc>,
    },

    /// A role assignment was changed.
    RoleAssigned {
        role: SocietyRole,
        role_lct_id: Uuid,
        assigned_to: Uuid,
        assigned_by: Uuid,
    },

    /// A chapter event was held + recorded (demo night, workshop, etc.).
    EventRecorded {
        event_kind: String,
        title: String,
        attended_by: Vec<Uuid>,
        recorded_by: Uuid,
        held_at: DateTime<Utc>,
    },

    /// The hub charter was amended. `new_charter_hash` is the post-amendment
    /// hash. Must be signed by the Sovereign.
    CharterAmended {
        new_charter_hash: String,
        amended_by: Uuid,
        diff_summary: Option<String>,
    },

    /// A member declared a skill or interest. Self-attested in MVP; future
    /// versions add witness/attestor chains and T3 accrual per task-role.
    MemberSkillDeclared {
        member_lct_id: Uuid,
        skill: String,
        declared_by: Uuid,
    },

    /// A member asked the hub to introduce them to another member (the
    /// consent half of member discovery: find_members returns LCTs, an intro
    /// connects them only if BOTH agree). Travels only over the sealed
    /// channel. `purpose` is optional free text — note it is ledger-witnessed.
    IntroRequested {
        intro_id: Uuid,
        from_lct: Uuid,
        to_lct: Uuid,
        #[serde(default, skip_serializing_if = "Option::is_none")]
        purpose: Option<String>,
    },

    /// The target of an intro accepted or declined it. On acceptance each
    /// party may retrieve the other's pinned channel pubkey (list_intros) —
    /// which is everything a member↔member pair_channel needs.
    IntroResponded {
        intro_id: Uuid,
        responded_by: Uuid,
        accepted: bool,
    },

    /// Pin (or rotate) a member's channel public key after admission. Fills the
    /// enrollment gap for members admitted without `member_pubkey_hex` (the
    /// pre-V2-12 / CLI-bootstrap path): without a pinned key the member cannot
    /// open the sealed channel at all. Sovereign-authorized; the member
    /// generates the keypair locally and the public half is pinned here.
    MemberKeyPinned {
        member_lct_id: Uuid,
        /// Hex-encoded 32-byte Ed25519 public key.
        member_pubkey_hex: String,
        pinned_by: Uuid,
    },

    /// A member updated their profile — free-text fields (e.g. `skills`,
    /// `interests`, and arbitrary expandable keys) used for semantic member
    /// discovery (`find_members`). Self-attested, same authorization as
    /// MemberSkillDeclared (signer == subject). `fields` are merged into the
    /// member's profile; an empty value clears that field. Plain-language by
    /// design — not schematized.
    MemberProfileUpdated {
        member_lct_id: Uuid,
        fields: std::collections::BTreeMap<String, String>,
        updated_by: Uuid,
    },

    /// The hub law was amended (V2-8). The new law's YAML bytes are
    /// stored separately via [`crate::store::HubStore::write_law`];
    /// this event records the amendment in the ledger for audit. The
    /// `new_law_sha256` is the canonical hash of the YAML content,
    /// enabling cross-verification: any party can walk the ledger,
    /// follow the LawAmended events, and reconstruct which law was
    /// in force at any historical point.
    ///
    /// Per architecture commitment #1: law is always signed and
    /// auditable, never hardcoded. This event is the auditable trace.
    LawAmended {
        new_law_sha256: String,
        amended_by: Uuid,
        version: String,
        diff_summary: Option<String>,
    },

    /// A new Sovereign Council holder was admitted (V2-9 Phase 1). The
    /// added holder co-signs chapter acts as a co-Sovereign. Their
    /// public key is pinned at admission time so future envelopes
    /// verify without an external registry.
    ///
    /// Per architecture commitment #5: multi-Sovereign Council from the
    /// start — no single-founder pattern in production. Phase 1 ships
    /// the data model + per-holder envelope signing. Phase 2 lands the
    /// proposal/aggregation flow that enforces M-of-N on council-gated
    /// acts.
    CouncilMemberAdded {
        member_lct_id: Uuid,
        member_pubkey_hex: String,
        added_by: Uuid,
        member_name: Option<String>,
    },

    /// A Sovereign Council holder was removed. `removal_kind` captures
    /// whether the holder left voluntarily, was ejected, or was replaced
    /// by election — for audit trail consumers that care about the
    /// distinction (web4_core::role::RoleEventKind).
    CouncilMemberRemoved {
        member_lct_id: Uuid,
        removed_by: Uuid,
        removal_kind: web4_core::role::RoleEventKind,
        reason: Option<String>,
    },

    /// The Sovereign Council's M-of-N threshold changed. N is derived
    /// from current holder count at apply time. Until V2-9 Phase 2
    /// ships the proposal/aggregation flow, this value is recorded
    /// but NOT enforced on `submit_event` — any single council
    /// holder's signature still commits.
    CouncilThresholdChanged {
        new_m: u32,
        initiated_by: Uuid,
    },

    /// PAIRED-CHANNELS Sprint B: an LCT-holder requested a pair with
    /// another LCT-holder. The pair is `Pending` until the counterparty
    /// signs a `PairingConfirmed`. Initiator's envelope at submit time
    /// is the request signature; counterparty has not yet agreed.
    ///
    /// `purpose` is free-text; hub law can pattern-match against
    /// it (e.g., allow `delegation_*` purposes only for council holders).
    /// `expires_at` is optional — None means "no auto-expiry, must be
    /// revoked explicitly."
    ///
    /// Per architecture commitment #2: signed envelope at the REST
    /// boundary. Per commitment #8: the underlying ECDH-derived shared
    /// secret is computed at endpoints, never crosses the hub.
    PairingRequested {
        pair_id: Uuid,
        initiator_lct_id: Uuid,
        counterparty_lct_id: Uuid,
        purpose: String,
        proposed_at: DateTime<Utc>,
        #[serde(default, skip_serializing_if = "Option::is_none")]
        expires_at: Option<DateTime<Utc>>,
        /// PAIRED-CHANNELS Sprint F: initiator's per-session X25519
        /// ephemeral public key (hex), for forward-secrecy session-key
        /// derivation. Optional for back-compat: pairs created before
        /// Sprint F (or by clients that don't opt in) leave this None
        /// and fall back to the Sprint E static-key-only derivation.
        #[serde(default, skip_serializing_if = "Option::is_none")]
        initiator_ephemeral_pub_hex: Option<String>,
    },

    /// PAIRED-CHANNELS Sprint B: counterparty confirmed the pair.
    /// Transitions `Pending` → `Active`. Subsequent message posts
    /// to the pair are valid until `PairingRevoked` or `expires_at`.
    ///
    /// `confirmed_by` MUST be the counterparty named in the
    /// corresponding `PairingRequested` — the REST handler enforces
    /// this. Hub-side projection rejects mismatched confirmations
    /// (apply() silently no-ops; verify-ledger surfaces nothing
    /// because all entries are syntactically valid).
    PairingConfirmed {
        pair_id: Uuid,
        confirmed_by: Uuid,
        /// PAIRED-CHANNELS Sprint F: counterparty's per-session
        /// X25519 ephemeral public key (hex). Pairs with both
        /// ephemerals get forward secrecy; pairs missing either
        /// fall back to v1 static-only derivation.
        #[serde(default, skip_serializing_if = "Option::is_none")]
        counterparty_ephemeral_pub_hex: Option<String>,
    },

    /// PAIRED-CHANNELS Sprint B: pair revoked. Either party may
    /// voluntarily revoke; hub law may force-revoke; key rotation
    /// invalidates the derived shared secret and requires re-pairing.
    /// `revocation_kind` is the audit-relevant signal (voluntary
    /// vs. forced says something different to V3 trust accrual).
    PairingRevoked {
        pair_id: Uuid,
        revoked_by: Uuid,
        revocation_kind: PairRevocationKind,
        #[serde(default, skip_serializing_if = "Option::is_none")]
        reason: Option<String>,
    },

    /// PAIRED-CHANNELS Sprint D: a message was relayed on a pair.
    /// The actual payload bytes live in a per-pair sidecar log
    /// (`HubStore::append_pair_message`); this ledger event records
    /// the metadata + a payload hash so auditors can verify the
    /// sidecar hasn't been tampered with. Payload-by-reference, not
    /// payload-by-value: keeps the ledger compact for high-traffic
    /// pairs while preserving the witness property.
    ///
    /// `seq` is monotonic per pair, assigned by the hub at append
    /// time; `from` is the message author (envelope signer, must be
    /// a current pair participant). At Sprint D the sidecar payload
    /// is plaintext string; at Sprint E it becomes opaque ciphertext.
    /// `payload_hash` is sha256(payload bytes) — works for both.
    PairMessagePosted {
        pair_id: Uuid,
        seq: u64,
        from: Uuid,
        posted_at: DateTime<Utc>,
        payload_hash: String,
    },

    /// Tier-2 vault unlock — the ignited hub asked its M-of-N admins (the
    /// Sovereign Council) to authorize unlocking a protected tier. Issued with
    /// a fresh challenge; the start of a witnessed quorum decision. "A 3am
    /// auto-unlock is a visible, declinable record, not a silent file read."
    VaultUnlockRequested {
        challenge_id: Uuid,
        tier: String,
        /// How many distinct admin approvals this tier requires (the council M).
        required: u32,
        requested_at: DateTime<Utc>,
    },

    /// An admin submitted a signed decision for an outstanding unlock challenge.
    /// The attestation is verified by the (private) quorum engine; this records
    /// that a decision was received + from whom, for audit. `decision` is the
    /// admin's own word ("approve" / "decline"); a decline is a witnessed veto.
    VaultUnlockAttested {
        challenge_id: Uuid,
        admin_lct_id: Uuid,
        decision: String,
        attested_at: DateTime<Utc>,
    },

    /// The quorum resolved: granted iff distinct, fresh, roster-verified
    /// approvals reached the threshold (declines veto). The audited outcome.
    VaultUnlockResolved {
        challenge_id: Uuid,
        tier: String,
        granted: bool,
        approvals: Vec<Uuid>,
        declines: Vec<Uuid>,
        resolved_at: DateTime<Utc>,
    },

    /// A **referenced act** — a thin, witnessed governance record of an entity
    /// externalizing work: the one primitive behind fleet handoffs
    /// (`to = Peer`), hub→citizen notifications (`to = Citizen` — a notification
    /// is just this act *reversed*), forum posts (`to = Society`), and memory
    /// writes (`to = FutureSelf`). The payload is a [`web4_core::act::Act`]
    /// **verbatim**, so the originating cell and every witness serialize
    /// byte-identical records (convergence:
    /// `forum/legion-to-hub-referenced-act-shape-converged-2026-06-20`).
    ///
    /// The act binds to a *specific version* of its substance via
    /// `act.substance.content_hash` (a witnessed pointer that can't silently
    /// drift from the fat thing it attests), and its reversibility
    /// (`act.consequence`) drives the council gate —
    /// `ConsequenceClass::Irreversible ⇒ proposal_ref`, via
    /// [`web4_core::act::ConsequenceClass::requires_council`].
    ///
    /// Authorship is `act.actor_lct` (the *from*): the hub signs every ledger
    /// entry as the Sovereign (it is the witness), so the actor rides in the
    /// payload, exactly as `IntroRequested.from_lct`. The act's routing label
    /// `act.kind` is bare `<verb>` for fleet/peer acts (`handoff`/`memo`/`sweep`/
    /// `forum`) or `notify:<event>` for the hub→citizen act-reversed case (Legion
    /// hosts the registry; HUB owns the `notify:*` sub-vocabulary). Any
    /// recipient-sealed body is a *delivery* concern carried on the mailbox
    /// envelope (the daemon's `SealedNotice`), never duplicated onto this
    /// witnessed record — its integrity is bound instead by `content_hash`.
    ReferencedAct { act: Act },

    /// R7 reputation back-propagation: a role-contextualized trust/value delta
    /// recorded on the ledger — the *witnessed* half of reputation. The delta is
    /// computed elsewhere (`web4_core::r6::compute_reputation` from factors ×
    /// society-law weights); the hub records + applies it, never invents the math.
    /// Reputation is NEVER global — the delta's `(subject_lct, role_lct)` scopes
    /// it to an MRH role-pairing link (RFC #403).
    ReputationRecorded { delta: web4_core::r6::ReputationDelta },

    /// §5.1 R7 carrier: an accountability *obligation* opened by a coordination
    /// act that carried an `r7` block with a deadline. The subject committed to
    /// `request_id` due by `due_at`; resolution (met/late via `ObligationResolved`,
    /// or missed via the timeout sweep) folds a temporal `ReputationRecorded`.
    ObligationOpened {
        request_id: String,
        subject_lct: String,
        role_lct: String,
        due_at: DateTime<Utc>,
        criticality: web4_core::time::Criticality,
        opened_at: DateTime<Utc>,
    },

    /// §5.1 R7 carrier: an obligation reached a terminal state. `outcome` is
    /// "met" | "late" | "missed" (audit trail; the trust debit/credit rides a
    /// separate `ReputationRecorded`). Clears the obligation from the projection.
    ObligationResolved {
        request_id: String,
        outcome: String,
        /// Who resolved it. For P1 this is always the obligation's subject (the
        /// satisfy path is subject-only); recorded so audit — and future
        /// law-gated delegated resolution — has the resolver on the ledger.
        #[serde(default, skip_serializing_if = "Option::is_none")]
        resolved_by: Option<Uuid>,
        resolved_at: DateTime<Utc>,
    },

    /// A society published one of its LCTs upward so the hub registry can serve
    /// its presence. Publication is itself a witnessed act (the ledger entry IS
    /// the witness — canon genesis step 7); the registry is a projection over
    /// these events, replayed like members/pairs/law. Ingest is fail-closed: the
    /// publish is rejected unless binding + id-derivation (+ legacy alias, if
    /// any) all verify — never stored-as-unverified. Serves presence, mints no
    /// trust: provenance is carried, never laundered.
    ///
    /// Contract: `shared-context/forum/hub-to-legion-lct-published-event-spec-registry-projection-2026-07-10.md` §1.
    LctPublished {
        /// Canonical reachable id — the mb32 string, re-derived from the
        /// document's public key and checked on ingest. Never trusted as a label.
        lct_id: String,
        /// The LCT document, `web4_core::Lct` VERBATIM — same convergence
        /// discipline as `ReferencedAct`: producer and every witness serialize
        /// byte-identical.
        document: Lct,
        /// The pinned hub member relaying the publish (the society's hub
        /// identity), bound to the envelope signer at ingest. Authorship of the
        /// LCT itself lives in `document` (self-issued → `created_by` None).
        published_by: Uuid,
        /// Presence-only provenance. Never a trust grant.
        provenance: LctProvenance,
        published_at: DateTime<Utc>,
    },
}

/// How a published LCT came to exist. Carried on the registry entry so a
/// consumer can tell a bootstrap from a conferred identity — never summed into
/// trust.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum LctProvenance {
    /// §3.2 bootstrap: the entity signed its own binding. The Phase-1 path.
    SelfIssued,
    /// Birth-certificate-class: a society conferred the LCT. Requires the ≥3
    /// Witness-daemon quorum, which does not exist yet — so ingest rejects this
    /// until Phase 2, closing the path that would launder a bootstrap into a
    /// birth certificate before the quorum machinery can check it.
    SocietyConferred,
}

/// Why a pair ended. Captures audit-relevant intent so V3 trust
/// accrual can distinguish "we finished our work cleanly" from
/// "the chapter intervened" from "the key got rotated."
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PairRevocationKind {
    /// Either party chose to end the pair under normal circumstances.
    /// Trust-neutral or trust-positive (purpose-complete).
    Voluntary,
    /// The pair's `expires_at` was reached. Auto-cleanup; trust-neutral.
    Expired,
    /// Hub law force-revoked (norm fired with `decision: deny` for
    /// continued pair existence, or escalation outcome). Trust signal:
    /// pair was deemed inappropriate by the society.
    #[serde(alias = "chapter_law")]
    HubLaw,
    /// One party's LCT key rotated; derived shared secrets are no
    /// longer valid. Trust-neutral; re-pair to continue.
    KeyRotation,
}

impl HubEvent {
    /// Short human-readable kind name — matches the serde tag.
    pub fn kind(&self) -> &'static str {
        match self {
            Self::Genesis { .. } => "genesis",
            Self::MemberAdded { .. } => "member_added",
            Self::MemberRemoved { .. } => "member_removed",
            Self::MemberJoinRequested { .. } => "member_join_requested",
            Self::MemberJoinResolved { .. } => "member_join_resolved",
            Self::MemberJoinReviewRequested { .. } => "member_join_review_requested",
            Self::MemberJoinReviewResolved { .. } => "member_join_review_resolved",
            Self::MemberAdmissionReset { .. } => "member_admission_reset",
            Self::RoleAssigned { .. } => "role_assigned",
            Self::EventRecorded { .. } => "event_recorded",
            Self::CharterAmended { .. } => "charter_amended",
            Self::MemberSkillDeclared { .. } => "member_skill_declared",
            Self::MemberKeyPinned { .. } => "member_key_pinned",
            Self::IntroRequested { .. } => "intro_requested",
            Self::IntroResponded { .. } => "intro_responded",
            Self::MemberProfileUpdated { .. } => "member_profile_updated",
            Self::LawAmended { .. } => "law_amended",
            Self::CouncilMemberAdded { .. } => "council_member_added",
            Self::CouncilMemberRemoved { .. } => "council_member_removed",
            Self::CouncilThresholdChanged { .. } => "council_threshold_changed",
            Self::PairingRequested { .. } => "pairing_requested",
            Self::PairingConfirmed { .. } => "pairing_confirmed",
            Self::PairingRevoked { .. } => "pairing_revoked",
            Self::PairMessagePosted { .. } => "pair_message_posted",
            Self::VaultUnlockRequested { .. } => "vault_unlock_requested",
            Self::VaultUnlockAttested { .. } => "vault_unlock_attested",
            Self::VaultUnlockResolved { .. } => "vault_unlock_resolved",
            Self::ReferencedAct { .. } => "referenced_act",
            Self::ReputationRecorded { .. } => "reputation_recorded",
            Self::ObligationOpened { .. } => "obligation_opened",
            Self::ObligationResolved { .. } => "obligation_resolved",
            Self::LctPublished { .. } => "lct_published",
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn kind_strings_match_serde_tags() {
        let g = HubEvent::Genesis {
            hub_name: "X".into(),
            charter_hash: "sha256:0".into(),
            founding_sovereign_lct_id: Uuid::nil(),
            created_at: Utc::now(),
        };
        assert_eq!(g.kind(), "genesis");

        let json = serde_json::to_string(&g).unwrap();
        assert!(json.contains("\"kind\":\"genesis\""));
    }

    #[tokio::test]
    async fn role_assigned_uses_upstream_role_enum() {
        let e = HubEvent::RoleAssigned {
            role: SocietyRole::Treasurer,
            role_lct_id: Uuid::new_v4(),
            assigned_to: Uuid::new_v4(),
            assigned_by: Uuid::new_v4(),
        };
        let json = serde_json::to_string(&e).unwrap();
        assert!(json.contains("\"role\":\"treasurer\""));
    }

    /// The convergence guarantee: a `ReferencedAct`'s payload is a `web4_core::act::Act`
    /// *verbatim*, so the fleet's first real Act
    /// (`shared-context/acts/legion-2026-06-24-session-handoff.act.json`) replays onto the
    /// hub ledger with zero reshaping, and the inner act bytes are identical to what the
    /// originating cell witnessed ("both sides witness the same bytes").
    #[tokio::test]
    async fn legions_first_real_act_round_trips_as_a_referenced_act_payload() {
        // The artifact, verbatim (kept in-crate so the test is hermetic).
        let act_json = r#"{
  "act_id": "7dea2b7a-e0b2-43b5-adb3-6d1c9ed353e3",
  "actor_lct": "881f13b0-6ca4-445b-b36a-655018174ba5",
  "address": { "to": "future_self", "entity": "881f13b0-6ca4-445b-b36a-655018174ba5" },
  "kind": "handoff",
  "consequence": "reversible",
  "substance": {
    "uri": "shared-context/acts/legion-2026-06-24-session-handoff.md",
    "content_hash": "c903bf541d68a6dd461e56ae2056c761e399b628ce0ef2f1f054b015cd8d282a",
    "medium": "doc"
  },
  "witnesses": [{
    "lct": "881f13b0-6ca4-445b-b36a-655018174ba5",
    "attestation": "authored",
    "signature": "906aa168fe8431391d5a34317a1c16fb83be3e53cc6a077b33d6a4610873a3e3c960ed4416af041593df6a9c586a0e561d5a22eb4e03f3357321e0fcc415ef0a",
    "timestamp": "2026-06-24T23:11:44.811783264Z"
  }],
  "at": "2026-06-24T23:11:44.811510269Z"
}"#;
        // It deserializes into the core Act with no hub-side reshaping...
        let act: Act = serde_json::from_str(act_json).expect("Legion's act parses as a core Act");
        assert_eq!(act.kind, "handoff");
        assert!(matches!(act.address, web4_core::act::ActAddress::FutureSelf { .. }));

        // ...and the inner act bytes survive the wrap/unwrap unchanged (verbatim payload).
        let value_before: serde_json::Value = serde_json::from_str(act_json).unwrap();
        let event = HubEvent::ReferencedAct { act };
        assert_eq!(event.kind(), "referenced_act");
        let HubEvent::ReferencedAct { act: unwrapped } = &event else { unreachable!() };
        assert_eq!(serde_json::to_value(unwrapped).unwrap(), value_before);
    }
}
