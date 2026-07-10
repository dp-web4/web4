// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// This software is covered by US Patents 11,477,027 and 12,278,913,
// and pending application 19/178,619. See PATENTS.md for details.

//! # Web4 Core Library
//!
//! Trust-native distributed intelligence infrastructure implemented in Rust.
//!
//! This crate provides the foundational primitives for Web4:
//!
//! - **LCT (Linked Context Token)**: Non-transferable presence tokens
//! - **T3 (Trust Tensor)**: 3 root dimensions (Talent/Training/Temperament),
//!   fractally extensible via RDF sub-dimensions
//! - **V3 (Value Tensor)**: 3 root dimensions (Valuation/Veracity/Validity),
//!   same fractal RDF pattern as T3
//! - **Coherence**: Identity coherence scoring (C * S * Phi * R)
//! - **Crypto**: Ed25519 cryptographic operations
//!
//! ## Quick Start
//!
//! ```rust
//! use web4_core::{Lct, EntityType, T3, TrustDimension};
//!
//! // Create an LCT for a human user
//! let (lct, keypair) = Lct::new(EntityType::Human, None);
//!
//! // Sign a message
//! let message = b"Hello, Web4!";
//! let signature = keypair.sign(message);
//!
//! // Verify the signature
//! assert!(lct.verify_signature(message, &signature).is_ok());
//!
//! // Create a trust tensor and record observations
//! let mut trust = T3::new();
//! trust.observe(TrustDimension::Talent, 0.9).unwrap();
//! trust.observe(TrustDimension::Training, 0.85).unwrap();
//!
//! // Get aggregate trust score
//! let score = trust.aggregate();
//! ```
//!
//! ## Design Philosophy
//!
//! Web4 implements trust as a first-class primitive, not an afterthought.
//! Every identity is cryptographically bound, every interaction is witnessed,
//! and trust accumulates through demonstrated behavior over time.
//!
//! Key principles:
//! - **Non-transferable identity**: LCTs cannot be sold, stolen, or faked
//! - **Fractal trust**: 3 root dimensions extensible via `web4:subDimensionOf`
//! - **Coherence requirements**: Entities must maintain identity coherence
//! - **Hardware binding**: Production deployments bind keys to secure hardware

pub mod act;
pub mod atp;
pub mod coherence;
pub mod crypto;
pub mod delegation;
pub mod did;
pub mod error;
pub mod event;
pub mod lct;
pub mod ledger;
pub mod pair_channel;
pub mod r6;
pub mod role;
pub mod role_extension;
pub mod oid4vc;
pub mod sd_jwt_vc;
pub mod society;
pub mod t3;
pub mod time;
pub mod v3;
pub mod vault;

// Re-export primary types for convenience
pub use act::{
    Act, ActAddress, ActOutcome, ConsequenceClass, MrhDirection, SubstanceMedium, SubstanceRef,
};
pub use atp::{ATPAccount, TransferResult};
pub use coherence::{
    check_coherence, coherence_threshold_for_entity, Coherence, CoherenceCalculator,
    CoherenceEvent, CoherenceParams,
};
pub use crypto::{sha256, sha256_hex, KeyPair, PublicKey, SignatureBytes};
pub use error::{Result, Web4Error};
pub use lct::{derive_lct_id, EntityType, HardwareBinding, Lct, LctBuilder, LctStatus, Mrh, MrhEdge};
pub use ledger::{
    InMemoryLedger, Ledger, LedgerEntry, LedgerEvent, LedgerProof, LocalLedger, MintReceipt,
};
pub use r6::{
    ActionResult, ActionRole, ActionStatus, R7Action, ReputationDelta, Request, ResourceRequirements,
    Rules,
};
pub use delegation::{DelegatedAuthority, DelegationScope};
pub use did::{DidDocument, DidDocumentMetadata, ServiceEndpoints, did_web4, parse_did_web4};
pub use role::{RoleAssignment, RoleEvent, RoleEventKind, SocietyRole};
pub use role_extension::{Affordance, AtpBudget, DriftMark, ExtensionVerdict, LintVerdict, Responsibility, RoleEntity, RoleExtension, RoleRegistry, Scope};
pub use sd_jwt_vc::{SdJwtVc, UnsignedSdJwtVc, VerifiedCredential, verify_issuer, verify_presentation, present, web4_presence_credential};
pub use society::{MetabolicState, Society};
pub use vault::{Vault, VaultContents, Document, ItemRef, Protection};
pub use t3::{TrustDimension, TrustObservation, TrustRelation, T3, T3_DIMENSIONS};
pub use time::{Criticality, Deadline, DeadlineOutcome, TemporalImpact, Timing, WitnessAvailability};
pub use v3::{TrustValueScore, ValueDimension, ValueObservation, V3, V3_DIMENSIONS};

/// Library version
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

/// Prelude module for convenient imports
pub mod prelude {
    pub use crate::coherence::{Coherence, CoherenceCalculator, CoherenceParams};
    pub use crate::crypto::{KeyPair, PublicKey, SignatureBytes};
    pub use crate::error::{Result, Web4Error};
    pub use crate::lct::{EntityType, Lct, LctBuilder, LctStatus};
    pub use crate::atp::ATPAccount;
    pub use crate::r6::{R7Action, ReputationDelta, Rules};
    pub use crate::delegation::{DelegatedAuthority, DelegationScope};
    pub use crate::role::{RoleAssignment, SocietyRole};
    pub use crate::society::{MetabolicState, Society};
    pub use crate::t3::{TrustDimension, T3};
    pub use crate::v3::{ValueDimension, V3};
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_full_workflow() {
        // 1. Create an organization LCT
        let (org_lct, _org_keypair) = Lct::new(EntityType::Organization, None);
        assert!(org_lct.is_active());

        // 2. Organization creates an AI agent
        let (ai_lct, ai_keypair) = org_lct.create_child(EntityType::AiSoftware);
        assert_eq!(ai_lct.parent_id, Some(org_lct.id));
        assert_eq!(ai_lct.lineage_depth, 1);

        // 3. AI agent signs a message
        let message = b"Task completed successfully";
        let signature = ai_keypair.sign(message);
        assert!(ai_lct.verify_signature(message, &signature).is_ok());

        // 4. Build trust over time
        let mut trust = T3::new();
        for _ in 0..10 {
            trust.observe(TrustDimension::Talent, 0.9).unwrap();
            trust.observe(TrustDimension::Training, 0.85).unwrap();
        }
        assert!(trust.aggregate() > 0.7);

        // 5. Calculate coherence
        let coherence = Coherence::with_values(0.92, 0.92, 0.92, 0.92).unwrap();
        assert!(coherence.meets_threshold(ai_lct.coherence_threshold()));
    }

    #[test]
    fn test_trust_value_integration() {
        // Create a trust-value score for an entity
        let mut tv = TrustValueScore::new(uuid::Uuid::new_v4());

        // Build trust through observations
        tv.trust.observe(TrustDimension::Talent, 0.9).unwrap();
        tv.trust.observe(TrustDimension::Training, 0.9).unwrap();

        // Build value through contributions
        tv.value.observe(ValueDimension::Valuation, 0.8).unwrap();
        tv.value.observe(ValueDimension::Validity, 0.85).unwrap();

        // Combined score should reflect both
        let combined = tv.combined();
        assert!(combined > 0.5);
    }

    #[test]
    fn test_voided_lct_cannot_sign() {
        let (mut lct, keypair) = Lct::new(EntityType::Human, None);
        let message = b"Test message";
        let signature = keypair.sign(message);

        // Void the LCT
        lct.void();

        // Verification should fail
        assert!(lct.verify_signature(message, &signature).is_err());
    }

    #[test]
    fn test_coherence_requirements() {
        let (human_lct, _) = Lct::new(EntityType::Human, None);
        let (ai_lct, _) = Lct::new(EntityType::AiSoftware, None);

        // AI has higher coherence requirements due to copyability
        assert!(ai_lct.coherence_threshold() > human_lct.coherence_threshold());
    }
}
