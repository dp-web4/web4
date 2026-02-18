// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: MIT
//
// This software is covered by US Patents 11,477,027 and 12,278,913,
// and pending application 19/178,619. See PATENTS.md for details.

//! Linked Context Token (LCT) Implementation
//!
//! LCTs are non-transferable presence tokens that serve as the cryptographic
//! root presence anchor for entities in Web4. Each LCT is permanently bound to a
//! single entity and cannot be stolen, sold, or faked.
//!
//! # P0 BLOCKER: Hardware Binding
//!
//! Currently, LCT keys are stored in software. For production use, keys MUST
//! be hardware-bound (TPM 2.0, Secure Enclave, TrustZone). Without hardware
//! binding, LCTs can be copied and identity can be impersonated.

use crate::crypto::{sha256_hex, KeyPair, PublicKey, SignatureBytes};
use crate::error::{Result, Web4Error};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Entity type that an LCT can represent
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EntityType {
    /// Human user
    Human,
    /// AI agent (software-bound)
    AiSoftware,
    /// AI agent (hardware-bound, e.g., on Jetson)
    AiEmbodied,
    /// Organization
    Organization,
    /// Role (first-class entity)
    Role,
    /// Task
    Task,
    /// Resource
    Resource,
    /// Hybrid entity
    Hybrid,
}

/// LCT status
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum LctStatus {
    /// Active and valid
    Active,
    /// Temporarily dormant
    Dormant,
    /// Voided (entity ceased to exist)
    Void,
    /// Slashed (compromised or malicious)
    Slashed,
}

/// Hardware binding level for the LCT
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct HardwareBinding {
    /// Binding level (0-5)
    /// 0-3: None/Weak (testing only)
    /// 4: Software (encrypted keys)
    /// 5: Hardware (TPM/SE)
    pub level: u8,

    /// Description of the binding
    pub description: String,

    /// Trust ceiling based on binding level
    pub trust_ceiling: f64,
}

impl Default for HardwareBinding {
    fn default() -> Self {
        // Default to software binding (level 4)
        Self {
            level: 4,
            description: "Software-bound keys (development)".into(),
            trust_ceiling: 0.85,
        }
    }
}

/// Linked Context Token - the fundamental identity primitive
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Lct {
    /// Unique identifier
    pub id: Uuid,

    /// Entity type
    pub entity_type: EntityType,

    /// Current status
    pub status: LctStatus,

    /// Public key for this LCT
    pub public_key: PublicKey,

    /// Creation timestamp
    pub created_at: DateTime<Utc>,

    /// Creator's LCT ID (None for root entities)
    pub created_by: Option<Uuid>,

    /// Hardware binding information
    pub hardware_binding: HardwareBinding,

    /// Parent LCT ID for hierarchical relationships
    pub parent_id: Option<Uuid>,

    /// Lineage depth (distance from root)
    pub lineage_depth: u32,
}

impl Lct {
    /// Create a new LCT
    ///
    /// Returns both the LCT and the keypair (which should be securely stored)
    pub fn new(entity_type: EntityType, created_by: Option<Uuid>) -> (Self, KeyPair) {
        let keypair = KeyPair::generate();
        let public_key = keypair.verifying_key();

        let lct = Self {
            id: Uuid::new_v4(),
            entity_type,
            status: LctStatus::Active,
            public_key,
            created_at: Utc::now(),
            created_by,
            hardware_binding: HardwareBinding::default(),
            parent_id: None,
            lineage_depth: 0,
        };

        (lct, keypair)
    }

    /// Create a child LCT under this parent
    pub fn create_child(&self, entity_type: EntityType) -> (Self, KeyPair) {
        let keypair = KeyPair::generate();
        let public_key = keypair.verifying_key();

        let lct = Self {
            id: Uuid::new_v4(),
            entity_type,
            status: LctStatus::Active,
            public_key,
            created_at: Utc::now(),
            created_by: Some(self.id),
            hardware_binding: HardwareBinding::default(),
            parent_id: Some(self.id),
            lineage_depth: self.lineage_depth + 1,
        };

        (lct, keypair)
    }

    /// Check if LCT is active
    pub fn is_active(&self) -> bool {
        self.status == LctStatus::Active
    }

    /// Void this LCT (entity ceased to exist)
    pub fn void(&mut self) {
        self.status = LctStatus::Void;
    }

    /// Slash this LCT (compromised or malicious)
    pub fn slash(&mut self) {
        self.status = LctStatus::Slashed;
    }

    /// Get trust ceiling based on hardware binding
    pub fn trust_ceiling(&self) -> f64 {
        self.hardware_binding.trust_ceiling
    }

    /// Verify a signature from this LCT
    pub fn verify_signature(&self, message: &[u8], signature: &SignatureBytes) -> Result<()> {
        if !self.is_active() {
            return Err(Web4Error::LctVoided(format!(
                "LCT {} is {:?}",
                self.id, self.status
            )));
        }
        self.public_key.verify(message, signature)
    }

    /// Get the LCT fingerprint (short identifier for display)
    pub fn fingerprint(&self) -> String {
        let full = sha256_hex(&self.public_key.to_bytes());
        format!("{}...{}", &full[..8], &full[56..])
    }

    /// Check coherence requirements based on entity type
    ///
    /// Returns the minimum coherence threshold for trust accumulation
    pub fn coherence_threshold(&self) -> f64 {
        match self.entity_type {
            EntityType::Human => 0.5,        // Body-bound identity
            EntityType::AiEmbodied => 0.6,   // Hardware binding helps
            EntityType::AiSoftware => 0.7,   // Higher bar due to copyability
            EntityType::Organization => 0.5,
            EntityType::Role => 0.5,
            EntityType::Task => 0.3,
            EntityType::Resource => 0.3,
            EntityType::Hybrid => 0.6,
        }
    }
}

/// Builder for creating LCTs with custom configuration
pub struct LctBuilder {
    entity_type: EntityType,
    created_by: Option<Uuid>,
    parent_id: Option<Uuid>,
    hardware_binding: Option<HardwareBinding>,
}

impl LctBuilder {
    pub fn new(entity_type: EntityType) -> Self {
        Self {
            entity_type,
            created_by: None,
            parent_id: None,
            hardware_binding: None,
        }
    }

    pub fn created_by(mut self, creator: Uuid) -> Self {
        self.created_by = Some(creator);
        self
    }

    pub fn parent(mut self, parent: Uuid) -> Self {
        self.parent_id = Some(parent);
        self
    }

    pub fn hardware_binding(mut self, binding: HardwareBinding) -> Self {
        self.hardware_binding = Some(binding);
        self
    }

    pub fn build(self) -> (Lct, KeyPair) {
        let keypair = KeyPair::generate();
        let public_key = keypair.verifying_key();

        let lct = Lct {
            id: Uuid::new_v4(),
            entity_type: self.entity_type,
            status: LctStatus::Active,
            public_key,
            created_at: Utc::now(),
            created_by: self.created_by,
            hardware_binding: self.hardware_binding.unwrap_or_default(),
            parent_id: self.parent_id,
            lineage_depth: if self.parent_id.is_some() { 1 } else { 0 },
        };

        (lct, keypair)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lct_creation() {
        let (lct, _keypair) = Lct::new(EntityType::Human, None);

        assert!(lct.is_active());
        assert_eq!(lct.entity_type, EntityType::Human);
        assert_eq!(lct.lineage_depth, 0);
        assert!(lct.created_by.is_none());
    }

    #[test]
    fn test_child_lct() {
        let (parent, _) = Lct::new(EntityType::Organization, None);
        let (child, _) = parent.create_child(EntityType::Role);

        assert_eq!(child.parent_id, Some(parent.id));
        assert_eq!(child.created_by, Some(parent.id));
        assert_eq!(child.lineage_depth, 1);
    }

    #[test]
    fn test_signature_verification() {
        let (lct, keypair) = Lct::new(EntityType::AiSoftware, None);
        let message = b"Test message";

        let signature = keypair.sign(message);
        assert!(lct.verify_signature(message, &signature).is_ok());
    }

    #[test]
    fn test_voided_lct_rejects_signature() {
        let (mut lct, keypair) = Lct::new(EntityType::AiSoftware, None);
        let signature = keypair.sign(b"Test");

        lct.void();

        assert!(lct.verify_signature(b"Test", &signature).is_err());
    }

    #[test]
    fn test_coherence_thresholds() {
        let (human, _) = Lct::new(EntityType::Human, None);
        let (ai_sw, _) = Lct::new(EntityType::AiSoftware, None);
        let (ai_hw, _) = Lct::new(EntityType::AiEmbodied, None);

        assert_eq!(human.coherence_threshold(), 0.5);
        assert_eq!(ai_sw.coherence_threshold(), 0.7);
        assert_eq!(ai_hw.coherence_threshold(), 0.6);
    }

    #[test]
    fn test_lct_builder() {
        let parent_id = Uuid::new_v4();
        let creator_id = Uuid::new_v4();

        let (lct, _) = LctBuilder::new(EntityType::Task)
            .created_by(creator_id)
            .parent(parent_id)
            .build();

        assert_eq!(lct.entity_type, EntityType::Task);
        assert_eq!(lct.created_by, Some(creator_id));
        assert_eq!(lct.parent_id, Some(parent_id));
    }

    #[test]
    fn test_fingerprint() {
        let (lct, _) = Lct::new(EntityType::Human, None);
        let fp = lct.fingerprint();

        // Format: 8 chars + "..." + 8 chars
        assert_eq!(fp.len(), 19);
        assert!(fp.contains("..."));
    }
}
