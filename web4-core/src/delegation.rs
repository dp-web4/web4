// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// This software is covered by US Patents 11,477,027 and 12,278,913,
// and pending application 19/178,619. See PATENTS.md for details.

//! Delegated Authority — binding a delegator to an agent with scoped permissions.
//!
//! A `DelegatedAuthority` allows one entity (the delegator) to grant another
//! entity (the agent) permission to act within a bounded scope. The delegation
//! is cryptographically signed by the delegator and verifiable by any party.
//!
//! Key properties:
//! - **Scoped**: restricted to specific roles and/or actions
//! - **Temporal**: optional expiration
//! - **Revocable**: delegator can revoke at any time
//! - **Signed**: Ed25519 signature over canonical serialization
//! - **Verifiable**: any party with the delegator's public key can verify
//!
//! Use cases:
//! - Human delegates to AI agent (Hestia H4)
//! - Sovereign delegates administrative authority
//! - Role-filler delegates to sub-agent for specific tasks
//!
//! Reference: `web4/hub/docs/V2-V3-ARCHITECTURE.md` §Track U, sub-item U2

use crate::crypto::{sha256, KeyPair, PublicKey, SignatureBytes};
use crate::error::{Result, Web4Error};
use crate::role::SocietyRole;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Scope of a delegation — which roles and actions the agent may perform.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DelegationScope {
    /// Roles the agent may act under. Empty = no role-specific grants.
    pub roles: Vec<SocietyRole>,

    /// Specific actions permitted. Empty = all actions within the granted roles.
    pub actions: Vec<String>,

    /// Restrict delegation to a specific society. None = any society.
    pub society_lct_id: Option<Uuid>,
}

impl DelegationScope {
    /// Unrestricted scope — all roles, all actions, any society.
    pub fn unrestricted() -> Self {
        Self {
            roles: Vec::new(),
            actions: Vec::new(),
            society_lct_id: None,
        }
    }

    /// Scope limited to specific roles.
    pub fn for_roles(roles: Vec<SocietyRole>) -> Self {
        Self {
            roles,
            actions: Vec::new(),
            society_lct_id: None,
        }
    }

    /// Check whether this scope covers a given role and action.
    pub fn covers(&self, role: &SocietyRole, action: &str) -> bool {
        let role_ok = self.roles.is_empty() || self.roles.contains(role);
        let action_ok = self.actions.is_empty() || self.actions.iter().any(|a| a == action);
        role_ok && action_ok
    }

    /// Check whether this scope is restricted to a specific society.
    pub fn covers_society(&self, society_id: Uuid) -> bool {
        self.society_lct_id.is_none() || self.society_lct_id == Some(society_id)
    }

    /// Canonical bytes for signing — deterministic serialization.
    fn canonical_bytes(&self) -> Vec<u8> {
        serde_json::to_vec(self).expect("DelegationScope is always serializable")
    }
}

/// A cryptographically signed delegation of authority from one entity to another.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DelegatedAuthority {
    /// Unique identifier for this delegation.
    pub id: Uuid,

    /// LCT of the entity granting authority.
    pub delegator_lct_id: Uuid,

    /// LCT of the entity receiving authority.
    pub agent_lct_id: Uuid,

    /// What the agent is permitted to do.
    pub scope: DelegationScope,

    /// When the delegation was created.
    pub created_at: DateTime<Utc>,

    /// When the delegation expires. None = no expiration.
    pub expires_at: Option<DateTime<Utc>>,

    /// Whether this delegation has been revoked.
    pub revoked: bool,

    /// When the delegation was revoked (if applicable).
    pub revoked_at: Option<DateTime<Utc>>,

    /// Delegator's Ed25519 signature over the canonical delegation content.
    pub signature: SignatureBytes,
}

impl DelegatedAuthority {
    /// Create and sign a new delegation.
    pub fn create(
        delegator_lct_id: Uuid,
        agent_lct_id: Uuid,
        scope: DelegationScope,
        expires_at: Option<DateTime<Utc>>,
        delegator_keypair: &KeyPair,
    ) -> Self {
        let id = Uuid::new_v4();
        let created_at = Utc::now();

        let signing_payload = Self::signing_payload(
            id,
            delegator_lct_id,
            agent_lct_id,
            &scope,
            created_at,
            expires_at,
        );
        let signature = delegator_keypair.sign(&signing_payload);

        Self {
            id,
            delegator_lct_id,
            agent_lct_id,
            scope,
            created_at,
            expires_at,
            revoked: false,
            revoked_at: None,
            signature,
        }
    }

    /// Verify the delegation's signature against the delegator's public key.
    pub fn verify(&self, delegator_public_key: &PublicKey) -> Result<()> {
        if self.revoked {
            return Err(Web4Error::Unauthorized(
                "Delegation has been revoked".into(),
            ));
        }

        if let Some(exp) = self.expires_at {
            if Utc::now() > exp {
                return Err(Web4Error::Unauthorized("Delegation has expired".into()));
            }
        }

        let payload = Self::signing_payload(
            self.id,
            self.delegator_lct_id,
            self.agent_lct_id,
            &self.scope,
            self.created_at,
            self.expires_at,
        );
        delegator_public_key.verify(&payload, &self.signature)
            .map_err(|_| Web4Error::SignatureInvalid(
                "Delegation signature does not match delegator's public key".into(),
            ))
    }

    /// Check whether this delegation authorizes a specific action.
    pub fn authorizes(&self, role: &SocietyRole, action: &str, agent_id: Uuid) -> Result<()> {
        if agent_id != self.agent_lct_id {
            return Err(Web4Error::Unauthorized(
                "Agent does not match delegation".into(),
            ));
        }

        if self.revoked {
            return Err(Web4Error::Unauthorized(
                "Delegation has been revoked".into(),
            ));
        }

        if let Some(exp) = self.expires_at {
            if Utc::now() > exp {
                return Err(Web4Error::Unauthorized("Delegation has expired".into()));
            }
        }

        if !self.scope.covers(role, action) {
            return Err(Web4Error::Unauthorized(format!(
                "Delegation does not cover role {:?} action {:?}",
                role, action
            )));
        }

        Ok(())
    }

    /// Revoke this delegation. Irreversible.
    pub fn revoke(&mut self) {
        self.revoked = true;
        self.revoked_at = Some(Utc::now());
    }

    /// Whether this delegation is currently valid (not revoked, not expired).
    pub fn is_active(&self) -> bool {
        if self.revoked {
            return false;
        }
        if let Some(exp) = self.expires_at {
            return Utc::now() <= exp;
        }
        true
    }

    /// Canonical signing payload — deterministic byte sequence for signature.
    fn signing_payload(
        id: Uuid,
        delegator: Uuid,
        agent: Uuid,
        scope: &DelegationScope,
        created_at: DateTime<Utc>,
        expires_at: Option<DateTime<Utc>>,
    ) -> Vec<u8> {
        let mut buf = Vec::with_capacity(256);
        buf.extend_from_slice(b"web4:delegation:v1:");
        buf.extend_from_slice(id.as_bytes());
        buf.extend_from_slice(delegator.as_bytes());
        buf.extend_from_slice(agent.as_bytes());
        buf.extend_from_slice(&scope.canonical_bytes());
        buf.extend_from_slice(created_at.to_rfc3339().as_bytes());
        if let Some(exp) = expires_at {
            buf.extend_from_slice(exp.to_rfc3339().as_bytes());
        }
        sha256(&buf).to_vec()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_create_and_verify() {
        let delegator_kp = KeyPair::generate();
        let delegator_pk = delegator_kp.verifying_key();
        let delegator_id = Uuid::new_v4();
        let agent_id = Uuid::new_v4();

        let deleg = DelegatedAuthority::create(
            delegator_id,
            agent_id,
            DelegationScope::for_roles(vec![SocietyRole::Administrator]),
            None,
            &delegator_kp,
        );

        assert!(deleg.is_active());
        assert!(deleg.verify(&delegator_pk).is_ok());
    }

    #[test]
    fn test_wrong_key_fails_verification() {
        let delegator_kp = KeyPair::generate();
        let imposter_kp = KeyPair::generate();
        let imposter_pk = imposter_kp.verifying_key();

        let deleg = DelegatedAuthority::create(
            Uuid::new_v4(),
            Uuid::new_v4(),
            DelegationScope::unrestricted(),
            None,
            &delegator_kp,
        );

        assert!(deleg.verify(&imposter_pk).is_err());
    }

    #[test]
    fn test_revocation() {
        let kp = KeyPair::generate();
        let mut deleg = DelegatedAuthority::create(
            Uuid::new_v4(),
            Uuid::new_v4(),
            DelegationScope::unrestricted(),
            None,
            &kp,
        );

        assert!(deleg.is_active());

        deleg.revoke();

        assert!(!deleg.is_active());
        assert!(deleg.revoked);
        assert!(deleg.revoked_at.is_some());
        assert!(deleg.verify(&kp.verifying_key()).is_err());
    }

    #[test]
    fn test_scope_coverage() {
        let scope = DelegationScope::for_roles(vec![
            SocietyRole::Administrator,
            SocietyRole::Archivist,
        ]);

        assert!(scope.covers(&SocietyRole::Administrator, "any_action"));
        assert!(scope.covers(&SocietyRole::Archivist, "query"));
        assert!(!scope.covers(&SocietyRole::Sovereign, "amend_charter"));
    }

    #[test]
    fn test_scope_with_actions() {
        let scope = DelegationScope {
            roles: vec![SocietyRole::Treasurer],
            actions: vec!["mint_atp".into(), "transfer_atp".into()],
            society_lct_id: None,
        };

        assert!(scope.covers(&SocietyRole::Treasurer, "mint_atp"));
        assert!(scope.covers(&SocietyRole::Treasurer, "transfer_atp"));
        assert!(!scope.covers(&SocietyRole::Treasurer, "burn_atp"));
        assert!(!scope.covers(&SocietyRole::Sovereign, "mint_atp"));
    }

    #[test]
    fn test_authorizes_checks_agent() {
        let kp = KeyPair::generate();
        let agent_id = Uuid::new_v4();
        let wrong_agent = Uuid::new_v4();

        let deleg = DelegatedAuthority::create(
            Uuid::new_v4(),
            agent_id,
            DelegationScope::for_roles(vec![SocietyRole::Administrator]),
            None,
            &kp,
        );

        assert!(deleg
            .authorizes(&SocietyRole::Administrator, "manage", agent_id)
            .is_ok());
        assert!(deleg
            .authorizes(&SocietyRole::Administrator, "manage", wrong_agent)
            .is_err());
    }

    #[test]
    fn test_society_scoping() {
        let society_a = Uuid::new_v4();
        let society_b = Uuid::new_v4();

        let scoped = DelegationScope {
            roles: Vec::new(),
            actions: Vec::new(),
            society_lct_id: Some(society_a),
        };

        assert!(scoped.covers_society(society_a));
        assert!(!scoped.covers_society(society_b));

        let unscoped = DelegationScope::unrestricted();
        assert!(unscoped.covers_society(society_a));
        assert!(unscoped.covers_society(society_b));
    }

    #[test]
    fn test_serialization_roundtrip() {
        let kp = KeyPair::generate();
        let deleg = DelegatedAuthority::create(
            Uuid::new_v4(),
            Uuid::new_v4(),
            DelegationScope::for_roles(vec![SocietyRole::PolicyEntity]),
            None,
            &kp,
        );

        let json = serde_json::to_string(&deleg).unwrap();
        let recovered: DelegatedAuthority = serde_json::from_str(&json).unwrap();

        assert_eq!(recovered.id, deleg.id);
        assert_eq!(recovered.delegator_lct_id, deleg.delegator_lct_id);
        assert_eq!(recovered.agent_lct_id, deleg.agent_lct_id);
        assert_eq!(recovered.signature, deleg.signature);
        assert!(recovered.verify(&kp.verifying_key()).is_ok());
    }
}
