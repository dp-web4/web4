//! # Web4 Trust Core
//!
//! Core trust primitives for the Web4 ecosystem.
//!
//! This crate provides:
//! - T3 Trust Tensor (3 root dimensions: Talent/Training/Temperament)
//! - V3 Value Tensor (3 root dimensions: Valuation/Veracity/Validity)
//! - Entity trust with witnessing relationships
//! - Temporal decay functions
//! - Storage backends for persistence
//!
//! Each tensor dimension is a root node in an open-ended RDF sub-graph,
//! extensible via `web4:subDimensionOf`. See `web4-standard/ontology/t3v3-ontology.ttl`.
//!
//! ## Example
//!
//! ```rust
//! use web4_trust_core::{EntityTrust, EntityType, TrustStore};
//! use web4_trust_core::storage::InMemoryStore;
//!
//! // Create a trust store
//! let store = InMemoryStore::new();
//!
//! // Get or create entity trust
//! let mut trust = store.get_or_create("mcp:filesystem").unwrap();
//!
//! // Update from outcome
//! trust.update_from_outcome(true, 0.1);
//!
//! // Check trust level
//! println!("T3 average: {}", trust.t3_average());
//! println!("Trust level: {:?}", trust.trust_level());
//! ```

pub mod tensor;
pub mod entity;
pub mod witnessing;
pub mod decay;
pub mod storage;

#[cfg(any(feature = "python", feature = "wasm"))]
pub mod bindings;

// Re-exports for convenience
pub use tensor::{T3Tensor, V3Tensor, TrustLevel};
pub use entity::{EntityTrust, EntityType};
pub use witnessing::{WitnessEvent, WitnessingChain};
pub use storage::TrustStore;

/// Crate-level error type
#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("Entity not found: {0}")]
    NotFound(String),

    #[error("Storage error: {0}")]
    Storage(String),

    #[error("Serialization error: {0}")]
    Serialization(String),

    #[error("Invalid entity ID format: {0}")]
    InvalidEntityId(String),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}

pub type Result<T> = std::result::Result<T, Error>;

/// Version information
pub const VERSION: &str = env!("CARGO_PKG_VERSION");
