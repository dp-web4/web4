// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// This software is covered by US Patents 11,477,027 and 12,278,913,
// and pending application 19/178,619. See PATENTS.md for details.

//! Society Roles — the 7 base-mandatory roles per `society-roles.md`.
//!
//! Every Web4 society MUST fill these seven roles. A role:
//! - Has its own LCT (authority binds to role, not filling entity)
//! - Can be filled by a single entity, a sub-society, or a federation
//! - Carries its own T3/V3 trust metrics (performance of the role)
//! - Can be rotated without breaking accountability chains
//!
//! The role taxonomy is:
//! - **Base-mandatory** (7): Must exist in every society
//! - **Context-mandatory**: Required when certain conditions hold
//!   (e.g., Witness is mandatory when outward roles exist)
//! - **Optional**: Societies may define additional roles
//!
//! Reference: `web4-standard/core-spec/society-roles.md`

use crate::lct::{EntityType, Lct};
use crate::crypto::KeyPair;
use crate::t3::T3;
use crate::v3::V3;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// The 7 base-mandatory roles that every Web4 society must fill.
/// Plus context-mandatory and optional roles.
#[derive(Clone, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SocietyRole {
    // ── Base-mandatory (7) ────────────────────────────────────────

    /// Final authority for charter amendment, identity recovery,
    /// and extraordinary inter-society decisions.
    Sovereign,

    /// Publishes machine-readable laws, signs interpretations,
    /// answers compliance queries, maps laws to R6/R7 action grammar.
    /// NOT a decision-maker — an oracle that the PolicyEntity consults.
    LawOracle,

    /// Takes R6/R7 action requests, evaluates against Law Oracle's laws,
    /// returns approve/deny/escalate with reasoning. The enforcement arm.
    PolicyEntity,

    /// Operates Treasury: mints ATP, allocates per law, accounts for
    /// ATP/ADP movements. Conservation invariant: sum(ATP) + sum(ADP) = const.
    Treasurer,

    /// Operational execution: citizen lifecycle management, R6/R7 dispatch
    /// routing, infrastructure liveness, day-to-day society operations.
    Administrator,

    /// Maintains ledger writes, cryptographic chain integrity, retention
    /// policy enforcement, historical queries. The society's memory.
    Archivist,

    /// Base membership role. Every entity holds Citizen first; additional
    /// roles layer on top. Citizen is the genesis role — immutable once granted.
    Citizen,

    // ── Context-mandatory ─────────────────────────────────────────

    /// Independent attestation of other roles' actions. Mandatory when
    /// outward-facing roles exist (inter-society interactions).
    Witness,

    /// T3/V3 validation and trust auditing. Mandatory when the society
    /// issues trust attestations consumed by other societies.
    Auditor,

    // ── Optional / custom ─────────────────────────────────────────

    /// Society-defined role with custom authority scope.
    Custom(String),
}

impl SocietyRole {
    /// Returns true if this is one of the 7 base-mandatory roles.
    pub fn is_base_mandatory(&self) -> bool {
        matches!(
            self,
            SocietyRole::Sovereign
                | SocietyRole::LawOracle
                | SocietyRole::PolicyEntity
                | SocietyRole::Treasurer
                | SocietyRole::Administrator
                | SocietyRole::Archivist
                | SocietyRole::Citizen
        )
    }

    /// All 7 base-mandatory roles.
    pub fn base_mandatory() -> Vec<SocietyRole> {
        vec![
            SocietyRole::Sovereign,
            SocietyRole::LawOracle,
            SocietyRole::PolicyEntity,
            SocietyRole::Treasurer,
            SocietyRole::Administrator,
            SocietyRole::Archivist,
            SocietyRole::Citizen,
        ]
    }

    /// Human-readable description of the role's responsibility.
    pub fn description(&self) -> &str {
        match self {
            SocietyRole::Sovereign => "Final authority for charter amendment and identity recovery",
            SocietyRole::LawOracle => "Publishes and interprets machine-readable laws",
            SocietyRole::PolicyEntity => "Evaluates action requests against law, returns signed decisions",
            SocietyRole::Treasurer => "Operates treasury, mints ATP, enforces conservation",
            SocietyRole::Administrator => "Citizen lifecycle, dispatch routing, operations",
            SocietyRole::Archivist => "Ledger integrity, chain maintenance, historical queries",
            SocietyRole::Citizen => "Base membership role — genesis role, immutable once granted",
            SocietyRole::Witness => "Independent attestation of other roles' actions",
            SocietyRole::Auditor => "T3/V3 validation and trust auditing",
            SocietyRole::Custom(name) => Box::leak(format!("Custom role: {name}").into_boxed_str()),
        }
    }
}

/// A role assignment — binds a role to its own LCT and tracks the entity filling it.
///
/// Key principle: authority binds to `role_lct`, not `filling_entity_lct`.
/// When the filling entity rotates, accountability chains remain intact
/// because the role's LCT (and its signature history) doesn't change.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RoleAssignment {
    /// The role being assigned
    pub role: SocietyRole,

    /// The role's own LCT — authority binds here
    pub role_lct_id: Uuid,

    /// The entity currently filling this role
    pub filling_entity_lct_id: Uuid,

    /// When this assignment was made
    pub assigned_at: DateTime<Utc>,

    /// Who assigned (typically Sovereign or Administrator)
    pub assigned_by: Uuid,

    /// Trust metrics for this role's performance
    pub role_trust: T3,

    /// Value metrics for this role's contributions
    pub role_value: V3,

    /// Whether the role can be filled by multiple entities simultaneously
    /// (e.g., a committee of Witnesses)
    pub multi_holder: bool,

    /// Additional entities filling this role (for committee/federation patterns)
    pub additional_holders: Vec<Uuid>,

    /// M-of-N threshold for consequential actions. None = single-signer (M=1).
    /// When set, at least `threshold.0` of the current `threshold.1` holders
    /// must sign for a consequential action to be valid.
    pub threshold: Option<(u32, u32)>,

    /// Lifecycle events on this role assignment (filler-added, removed, elected, etc.)
    #[serde(default)]
    pub events: Vec<RoleEvent>,
}

/// Lifecycle event on a role assignment — tracks filler additions, removals,
/// elections, and ejections for audit trail.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RoleEvent {
    pub timestamp: DateTime<Utc>,
    pub kind: RoleEventKind,
    pub entity_lct_id: Uuid,
    pub initiated_by: Uuid,
}

/// Kind of role lifecycle event.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum RoleEventKind {
    FillerAdded,
    FillerRemoved,
    FillerResigned,
    FillerEjected,
    FillerElected,
    ThresholdChanged,
}

impl RoleAssignment {
    /// Create a new role assignment with a fresh role-LCT.
    pub fn new(
        role: SocietyRole,
        role_lct_id: Uuid,
        filling_entity_lct_id: Uuid,
        assigned_by: Uuid,
    ) -> Self {
        Self {
            role,
            role_lct_id,
            filling_entity_lct_id,
            assigned_at: Utc::now(),
            assigned_by,
            role_trust: T3::new(),
            role_value: V3::new(),
            multi_holder: false,
            additional_holders: Vec::new(),
            threshold: None,
            events: Vec::new(),
        }
    }

    /// Rotate the entity filling this role. The role-LCT stays the same.
    pub fn rotate(&mut self, new_entity_lct_id: Uuid, rotated_by: Uuid) {
        self.filling_entity_lct_id = new_entity_lct_id;
        self.assigned_at = Utc::now();
        self.assigned_by = rotated_by;
    }

    /// Add an additional holder (committee/federation pattern).
    pub fn add_holder(&mut self, entity_lct_id: Uuid) {
        self.add_holder_by(entity_lct_id, Uuid::nil());
    }

    /// Add an additional holder with initiator tracking.
    pub fn add_holder_by(&mut self, entity_lct_id: Uuid, initiated_by: Uuid) {
        if !self.additional_holders.contains(&entity_lct_id)
            && entity_lct_id != self.filling_entity_lct_id
        {
            self.additional_holders.push(entity_lct_id);
            self.multi_holder = true;
            self.events.push(RoleEvent {
                timestamp: Utc::now(),
                kind: RoleEventKind::FillerAdded,
                entity_lct_id,
                initiated_by,
            });
        }
    }

    /// Remove a holder. Cannot remove the primary filler — use `rotate()` for that.
    pub fn remove_holder(&mut self, entity_lct_id: Uuid, initiated_by: Uuid, kind: RoleEventKind) {
        if let Some(pos) = self.additional_holders.iter().position(|id| *id == entity_lct_id) {
            self.additional_holders.remove(pos);
            if self.additional_holders.is_empty() {
                self.multi_holder = false;
            }
            self.events.push(RoleEvent {
                timestamp: Utc::now(),
                kind,
                entity_lct_id,
                initiated_by,
            });
        }
    }

    /// Set M-of-N threshold for consequential actions.
    /// `m` must be >= 1 and <= total holder count.
    pub fn set_threshold(&mut self, m: u32, initiated_by: Uuid) {
        let n = self.holder_count() as u32;
        let m = m.min(n).max(1);
        self.threshold = Some((m, n));
        self.events.push(RoleEvent {
            timestamp: Utc::now(),
            kind: RoleEventKind::ThresholdChanged,
            entity_lct_id: Uuid::nil(),
            initiated_by,
        });
    }

    /// Total number of entities filling this role (primary + additional).
    pub fn holder_count(&self) -> usize {
        1 + self.additional_holders.len()
    }

    /// All holder IDs (primary first, then additional).
    pub fn all_holders(&self) -> Vec<Uuid> {
        let mut holders = vec![self.filling_entity_lct_id];
        holders.extend_from_slice(&self.additional_holders);
        holders
    }

    /// Check if an entity is authorized to act in this role.
    pub fn is_authorized(&self, entity_lct_id: Uuid) -> bool {
        self.filling_entity_lct_id == entity_lct_id
            || self.additional_holders.contains(&entity_lct_id)
    }

    /// Check whether a set of signers meets the M-of-N threshold.
    /// Returns true if no threshold is set (single-signer mode) and the
    /// signer is a holder, or if enough valid holders signed.
    pub fn meets_threshold(&self, signers: &[Uuid]) -> bool {
        match self.threshold {
            None => signers.iter().any(|s| self.is_authorized(*s)),
            Some((m, _)) => {
                let valid = signers.iter().filter(|s| self.is_authorized(**s)).count();
                valid >= m as usize
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_base_mandatory_roles() {
        let roles = SocietyRole::base_mandatory();
        assert_eq!(roles.len(), 7);
        for role in &roles {
            assert!(role.is_base_mandatory());
        }
        assert!(!SocietyRole::Witness.is_base_mandatory());
        assert!(!SocietyRole::Custom("foo".into()).is_base_mandatory());
    }

    #[test]
    fn test_role_assignment_rotation() {
        let sovereign_id = Uuid::new_v4();
        let role_lct = Uuid::new_v4();
        let entity_a = Uuid::new_v4();
        let entity_b = Uuid::new_v4();

        let mut assignment = RoleAssignment::new(
            SocietyRole::PolicyEntity,
            role_lct,
            entity_a,
            sovereign_id,
        );

        assert!(assignment.is_authorized(entity_a));
        assert!(!assignment.is_authorized(entity_b));

        // Rotate to entity_b — role-LCT stays the same
        assignment.rotate(entity_b, sovereign_id);
        assert!(!assignment.is_authorized(entity_a));
        assert!(assignment.is_authorized(entity_b));
        assert_eq!(assignment.role_lct_id, role_lct); // unchanged
    }

    #[test]
    fn test_multi_holder_committee() {
        let sovereign_id = Uuid::new_v4();
        let role_lct = Uuid::new_v4();
        let witness_a = Uuid::new_v4();
        let witness_b = Uuid::new_v4();
        let witness_c = Uuid::new_v4();

        let mut assignment = RoleAssignment::new(
            SocietyRole::Witness,
            role_lct,
            witness_a,
            sovereign_id,
        );

        assignment.add_holder(witness_b);
        assignment.add_holder(witness_c);

        assert!(assignment.multi_holder);
        assert!(assignment.is_authorized(witness_a));
        assert!(assignment.is_authorized(witness_b));
        assert!(assignment.is_authorized(witness_c));
        assert_eq!(assignment.additional_holders.len(), 2);
    }

    #[test]
    fn test_threshold_2_of_3() {
        let sovereign_id = Uuid::new_v4();
        let role_lct = Uuid::new_v4();
        let member_a = Uuid::new_v4();
        let member_b = Uuid::new_v4();
        let member_c = Uuid::new_v4();
        let outsider = Uuid::new_v4();

        let mut council = RoleAssignment::new(
            SocietyRole::Sovereign,
            role_lct,
            member_a,
            sovereign_id,
        );
        council.add_holder_by(member_b, sovereign_id);
        council.add_holder_by(member_c, sovereign_id);
        council.set_threshold(2, sovereign_id);

        assert_eq!(council.holder_count(), 3);
        assert_eq!(council.threshold, Some((2, 3)));

        // Single signer insufficient
        assert!(!council.meets_threshold(&[member_a]));
        // Two valid signers sufficient
        assert!(council.meets_threshold(&[member_a, member_b]));
        assert!(council.meets_threshold(&[member_b, member_c]));
        // Three is fine too
        assert!(council.meets_threshold(&[member_a, member_b, member_c]));
        // One valid + one outsider insufficient
        assert!(!council.meets_threshold(&[member_a, outsider]));
    }

    #[test]
    fn test_single_sovereign_is_threshold_1_of_1() {
        let sovereign_id = Uuid::new_v4();
        let role_lct = Uuid::new_v4();
        let entity = Uuid::new_v4();
        let outsider = Uuid::new_v4();

        let assignment = RoleAssignment::new(
            SocietyRole::Sovereign,
            role_lct,
            entity,
            sovereign_id,
        );

        // No threshold set — single-signer mode
        assert!(assignment.meets_threshold(&[entity]));
        assert!(!assignment.meets_threshold(&[outsider]));
        assert!(!assignment.meets_threshold(&[]));
    }

    #[test]
    fn test_remove_holder() {
        let sovereign_id = Uuid::new_v4();
        let role_lct = Uuid::new_v4();
        let a = Uuid::new_v4();
        let b = Uuid::new_v4();
        let c = Uuid::new_v4();

        let mut assignment = RoleAssignment::new(
            SocietyRole::Witness,
            role_lct,
            a,
            sovereign_id,
        );
        assignment.add_holder_by(b, sovereign_id);
        assignment.add_holder_by(c, sovereign_id);
        assert_eq!(assignment.holder_count(), 3);

        assignment.remove_holder(b, sovereign_id, RoleEventKind::FillerEjected);
        assert_eq!(assignment.holder_count(), 2);
        assert!(!assignment.is_authorized(b));
        assert!(assignment.is_authorized(a));
        assert!(assignment.is_authorized(c));
    }

    #[test]
    fn test_lifecycle_events_tracked() {
        let sovereign_id = Uuid::new_v4();
        let role_lct = Uuid::new_v4();
        let a = Uuid::new_v4();
        let b = Uuid::new_v4();

        let mut assignment = RoleAssignment::new(
            SocietyRole::Administrator,
            role_lct,
            a,
            sovereign_id,
        );

        assignment.add_holder_by(b, sovereign_id);
        assignment.set_threshold(2, sovereign_id);
        assignment.remove_holder(b, sovereign_id, RoleEventKind::FillerResigned);

        assert_eq!(assignment.events.len(), 3);
        assert_eq!(assignment.events[0].kind, RoleEventKind::FillerAdded);
        assert_eq!(assignment.events[1].kind, RoleEventKind::ThresholdChanged);
        assert_eq!(assignment.events[2].kind, RoleEventKind::FillerResigned);
    }

    #[test]
    fn test_all_holders() {
        let sovereign_id = Uuid::new_v4();
        let a = Uuid::new_v4();
        let b = Uuid::new_v4();

        let mut assignment = RoleAssignment::new(
            SocietyRole::Witness,
            Uuid::new_v4(),
            a,
            sovereign_id,
        );
        assignment.add_holder(b);

        let holders = assignment.all_holders();
        assert_eq!(holders.len(), 2);
        assert_eq!(holders[0], a);
        assert_eq!(holders[1], b);
    }
}
