// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// This software is covered by US Patents 11,477,027 and 12,278,913,
// and pending application 19/178,619. See PATENTS.md for details.

//! Society — a self-sovereign Web4 entity with roles, citizens, and ATP.
//!
//! A society is the organizational unit of Web4. Key properties:
//! - Self-sovereign: no external authority governs it
//! - Fractal: societies can contain sub-societies and federate into higher-order societies
//! - Anti-hierarchical: trust emerges from peer witnessing, not top-down imposition
//!
//! Genesis protocols:
//! - **Self-bootstrapped**: A single entity founds a society (solo founder wears many hats)
//! - **Federation-based**: Two+ existing societies form a higher-order society
//!
//! Minimum viable society requires:
//! 1. Internal differentiation (roles with meaningfully different authority)
//! 2. Witnessing capacity (at least one role can independently attest)
//! 3. Reified resource grounded externally (ATP represents something real)
//!
//! Reference: `web4-standard/core-spec/inter-society-protocol.md`,
//!            `web4-standard/core-spec/society-roles.md`

use crate::crypto::KeyPair;
use crate::error::{Result, Web4Error};
use crate::lct::{EntityType, Lct};
use crate::role::{RoleAssignment, SocietyRole};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

/// Metabolic state of a society (lifecycle phase).
/// Reference: `SOCIETY_METABOLIC_STATES.md`
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MetabolicState {
    /// Society is being created, charter drafted
    Genesis,
    /// Roles being assigned, initial ATP minted
    Bootstrap,
    /// Fully operational
    Operational,
    /// Low activity, roles may be unfilled
    Dormant,
    /// Winding down, ATP being settled
    Sunset,
}

/// A Web4 Society — self-sovereign organizational unit.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Society {
    /// Society's own LCT
    pub lct_id: Uuid,

    /// Human-readable name
    pub name: String,

    /// Charter hash — immutable once published, amendable by Sovereign
    pub charter_hash: String,

    /// Current metabolic state
    pub state: MetabolicState,

    /// Founder's entity LCT
    pub founder_lct_id: Uuid,

    /// When the society was created
    pub created_at: DateTime<Utc>,

    /// Role assignments — role → assignment
    pub roles: HashMap<String, RoleAssignment>,

    /// Citizen LCT IDs
    pub citizens: Vec<Uuid>,

    /// Parent society (if this is a constituent of a federation)
    pub federation_parent: Option<Uuid>,

    /// Child societies (if this is a higher-order federation)
    pub federation_children: Vec<Uuid>,
}

impl Society {
    /// Self-bootstrap a new society. The founder fills all mandatory roles initially.
    ///
    /// This implements the "solo founder wears many hats" genesis protocol.
    /// Roles can be delegated to other entities later via `assign_role()`.
    pub fn bootstrap(
        name: String,
        charter_hash: String,
        founder_lct_id: Uuid,
    ) -> (Self, Vec<(SocietyRole, Uuid)>) {
        let society_lct_id = Uuid::new_v4();
        let mut roles = HashMap::new();
        let mut role_lcts = Vec::new();

        // Create role assignments for all 7 base-mandatory roles
        for role in SocietyRole::base_mandatory() {
            let role_lct_id = Uuid::new_v4();
            let key = role_key(&role);
            roles.insert(
                key,
                RoleAssignment::new(
                    role.clone(),
                    role_lct_id,
                    founder_lct_id,
                    founder_lct_id, // self-assigned at genesis
                ),
            );
            role_lcts.push((role, role_lct_id));
        }

        let society = Self {
            lct_id: society_lct_id,
            name,
            charter_hash,
            state: MetabolicState::Genesis,
            founder_lct_id: founder_lct_id,
            created_at: Utc::now(),
            roles,
            citizens: vec![founder_lct_id],
            federation_parent: None,
            federation_children: Vec::new(),
        };

        (society, role_lcts)
    }

    /// Transition to Bootstrap state (roles assigned, ATP being minted).
    pub fn begin_bootstrap(&mut self) -> Result<()> {
        if self.state != MetabolicState::Genesis {
            return Err(Web4Error::InvalidState(
                "Can only begin bootstrap from Genesis state".into(),
            ));
        }
        self.state = MetabolicState::Bootstrap;
        Ok(())
    }

    /// Transition to Operational state (all mandatory roles filled, ATP minted).
    pub fn go_operational(&mut self) -> Result<()> {
        if self.state != MetabolicState::Bootstrap {
            return Err(Web4Error::InvalidState(
                "Can only go operational from Bootstrap state".into(),
            ));
        }
        // Verify all base-mandatory roles are assigned
        for role in SocietyRole::base_mandatory() {
            let key = role_key(&role);
            if !self.roles.contains_key(&key) {
                return Err(Web4Error::InvalidState(format!(
                    "Base-mandatory role {:?} not assigned",
                    role
                )));
            }
        }
        self.state = MetabolicState::Operational;
        Ok(())
    }

    /// Add a citizen to the society.
    pub fn add_citizen(&mut self, entity_lct_id: Uuid) {
        if !self.citizens.contains(&entity_lct_id) {
            self.citizens.push(entity_lct_id);
        }
    }

    /// Assign a role to an entity. Only Sovereign or Administrator can do this.
    pub fn assign_role(
        &mut self,
        role: SocietyRole,
        entity_lct_id: Uuid,
        assigned_by: Uuid,
    ) -> Result<Uuid> {
        // Verify assigner has Sovereign or Administrator role
        if !self.has_role_authority(assigned_by, &SocietyRole::Sovereign)
            && !self.has_role_authority(assigned_by, &SocietyRole::Administrator)
        {
            return Err(Web4Error::Unauthorized(
                "Only Sovereign or Administrator can assign roles".into(),
            ));
        }

        let key = role_key(&role);

        if let Some(existing) = self.roles.get_mut(&key) {
            // Role exists — rotate the filling entity
            existing.rotate(entity_lct_id, assigned_by);
            Ok(existing.role_lct_id)
        } else {
            // New role assignment
            let role_lct_id = Uuid::new_v4();
            self.roles.insert(
                key,
                RoleAssignment::new(role, role_lct_id, entity_lct_id, assigned_by),
            );
            Ok(role_lct_id)
        }
    }

    /// Check if an entity holds a specific role.
    pub fn has_role_authority(&self, entity_lct_id: Uuid, role: &SocietyRole) -> bool {
        let key = role_key(role);
        self.roles
            .get(&key)
            .map(|a| a.is_authorized(entity_lct_id))
            .unwrap_or(false)
    }

    /// Get the role assignment for a specific role.
    pub fn get_role(&self, role: &SocietyRole) -> Option<&RoleAssignment> {
        self.roles.get(&role_key(role))
    }

    /// Get all roles held by an entity.
    pub fn roles_for_entity(&self, entity_lct_id: Uuid) -> Vec<&RoleAssignment> {
        self.roles
            .values()
            .filter(|a| a.is_authorized(entity_lct_id))
            .collect()
    }

    /// Validate minimum viable society requirements.
    pub fn validate_minimum_viable(&self) -> std::result::Result<(), Vec<String>> {
        let mut errors = Vec::new();

        // 1. Internal differentiation — at least 2 roles filled by different entities
        let unique_fillers: std::collections::HashSet<Uuid> = self
            .roles
            .values()
            .map(|a| a.filling_entity_lct_id)
            .collect();
        if unique_fillers.len() < 2 && self.state == MetabolicState::Operational {
            errors.push(
                "Minimum viable society requires at least 2 distinct role-filling entities".into(),
            );
        }

        // 2. Witnessing capacity — Witness or Auditor role must exist
        let has_witness = self.roles.contains_key(&role_key(&SocietyRole::Witness))
            || self.roles.contains_key(&role_key(&SocietyRole::Auditor));
        if !has_witness && self.state == MetabolicState::Operational {
            errors.push(
                "Minimum viable society requires witnessing capacity (Witness or Auditor role)"
                    .into(),
            );
        }

        // 3. All base-mandatory roles filled
        for role in SocietyRole::base_mandatory() {
            if !self.roles.contains_key(&role_key(&role)) {
                errors.push(format!("Base-mandatory role {:?} not assigned", role));
            }
        }

        if errors.is_empty() {
            Ok(())
        } else {
            Err(errors)
        }
    }

    /// Join a federation (become a constituent of a higher-order society).
    pub fn join_federation(&mut self, parent_society_lct_id: Uuid) {
        self.federation_parent = Some(parent_society_lct_id);
    }

    /// Secede from a federation.
    pub fn secede(&mut self) -> Option<Uuid> {
        self.federation_parent.take()
    }

    /// Add a child society (this society becomes a federation).
    pub fn add_constituent(&mut self, child_society_lct_id: Uuid) {
        if !self.federation_children.contains(&child_society_lct_id) {
            self.federation_children.push(child_society_lct_id);
        }
    }

    /// Check if this society is a federation (has child societies).
    pub fn is_federation(&self) -> bool {
        !self.federation_children.is_empty()
    }

    /// Check if this society is a constituent of another society.
    pub fn is_constituent(&self) -> bool {
        self.federation_parent.is_some()
    }
}

/// Serialize role to stable key string.
fn role_key(role: &SocietyRole) -> String {
    match role {
        SocietyRole::Sovereign => "sovereign".into(),
        SocietyRole::LawOracle => "law_oracle".into(),
        SocietyRole::PolicyEntity => "policy_entity".into(),
        SocietyRole::Treasurer => "treasurer".into(),
        SocietyRole::Administrator => "administrator".into(),
        SocietyRole::Archivist => "archivist".into(),
        SocietyRole::Citizen => "citizen".into(),
        SocietyRole::Witness => "witness".into(),
        SocietyRole::Auditor => "auditor".into(),
        SocietyRole::Custom(name) => format!("custom:{name}"),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bootstrap_society() {
        let founder = Uuid::new_v4();
        let (society, role_lcts) = Society::bootstrap(
            "Acme Corp".into(),
            "sha256:charter_hash_here".into(),
            founder,
        );

        assert_eq!(society.state, MetabolicState::Genesis);
        assert_eq!(society.citizens.len(), 1);
        assert_eq!(role_lcts.len(), 7);

        // Founder holds all 7 roles initially
        for role in SocietyRole::base_mandatory() {
            assert!(society.has_role_authority(founder, &role));
        }
    }

    #[test]
    fn test_lifecycle_transitions() {
        let founder = Uuid::new_v4();
        let (mut society, _) = Society::bootstrap(
            "Test Society".into(),
            "sha256:test".into(),
            founder,
        );

        assert!(society.begin_bootstrap().is_ok());
        assert_eq!(society.state, MetabolicState::Bootstrap);

        assert!(society.go_operational().is_ok());
        assert_eq!(society.state, MetabolicState::Operational);

        // Can't go operational twice
        assert!(society.go_operational().is_err());
    }

    #[test]
    fn test_role_delegation() {
        let founder = Uuid::new_v4();
        let alice = Uuid::new_v4();
        let (mut society, _) = Society::bootstrap(
            "Test Society".into(),
            "sha256:test".into(),
            founder,
        );

        // Founder (as Sovereign) assigns PolicyEntity to Alice
        let role_lct = society
            .assign_role(SocietyRole::PolicyEntity, alice, founder)
            .unwrap();

        assert!(society.has_role_authority(alice, &SocietyRole::PolicyEntity));
        assert!(!society.has_role_authority(founder, &SocietyRole::PolicyEntity));

        // Role-LCT is preserved after rotation
        let same_role_lct = society
            .get_role(&SocietyRole::PolicyEntity)
            .unwrap()
            .role_lct_id;
        assert_eq!(role_lct, same_role_lct);
    }

    #[test]
    fn test_federation() {
        let founder_a = Uuid::new_v4();
        let founder_b = Uuid::new_v4();

        let (mut society_a, _) = Society::bootstrap("Alpha".into(), "sha256:a".into(), founder_a);
        let (mut society_b, _) = Society::bootstrap("Beta".into(), "sha256:b".into(), founder_b);

        // Create federation
        let federation_founder = Uuid::new_v4();
        let (mut federation, _) = Society::bootstrap(
            "Alpha-Beta Federation".into(),
            "sha256:fed".into(),
            federation_founder,
        );

        federation.add_constituent(society_a.lct_id);
        federation.add_constituent(society_b.lct_id);
        society_a.join_federation(federation.lct_id);
        society_b.join_federation(federation.lct_id);

        assert!(federation.is_federation());
        assert!(society_a.is_constituent());
        assert!(society_b.is_constituent());

        // Society A secedes
        let parent = society_a.secede();
        assert_eq!(parent, Some(federation.lct_id));
        assert!(!society_a.is_constituent());
    }
}
