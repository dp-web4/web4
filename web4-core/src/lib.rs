// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: MIT
//
// This software is covered by US Patents 11,477,027 and 12,278,913,
// and pending application 19/178,619. See PATENTS.md for details.

//! # Web4 Core Library
//!
//! Trust-native distributed intelligence infrastructure implemented in Rust.
//!
//! This crate provides the foundational primitives for Web4:
//!
//! - **LCT (Linked Context Token)**: Non-transferable identity tokens
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

pub mod coherence;
pub mod crypto;
pub mod error;
pub mod lct;
pub mod t3;
pub mod v3;

// Re-export primary types for convenience
pub use coherence::{
    check_coherence, coherence_threshold_for_entity, Coherence, CoherenceCalculator,
    CoherenceEvent, CoherenceParams,
};
pub use crypto::{sha256, sha256_hex, KeyPair, PublicKey, SignatureBytes};
pub use error::{Result, Web4Error};
pub use lct::{EntityType, HardwareBinding, Lct, LctBuilder, LctStatus};
pub use t3::{TrustDimension, TrustObservation, TrustRelation, T3, T3_DIMENSIONS};
pub use v3::{TrustValueScore, ValueDimension, ValueObservation, V3, V3_DIMENSIONS};

/// Library version
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

/// Prelude module for convenient imports
pub mod prelude {
    pub use crate::coherence::{Coherence, CoherenceCalculator, CoherenceParams};
    pub use crate::crypto::{KeyPair, PublicKey, SignatureBytes};
    pub use crate::error::{Result, Web4Error};
    pub use crate::lct::{EntityType, Lct, LctBuilder, LctStatus};
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
