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

    /// The chapter law was amended (V2-8). The new law's YAML bytes are
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
    /// `purpose` is free-text; chapter law can pattern-match against
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
    /// voluntarily revoke; chapter law may force-revoke; key rotation
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
}
