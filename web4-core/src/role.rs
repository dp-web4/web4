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
        if !self.additional_holders.contains(&entity_lct_id)
            && entity_lct_id != self.filling_entity_lct_id
        {
            self.additional_holders.push(entity_lct_id);
            self.multi_holder = true;
        }
    }

    /// Check if an entity is authorized to act in this role.
    pub fn is_authorized(&self, entity_lct_id: Uuid) -> bool {
        self.filling_entity_lct_id == entity_lct_id
            || self.additional_holders.contains(&entity_lct_id)
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
}
