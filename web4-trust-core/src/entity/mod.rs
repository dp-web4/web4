//! Entity trust types
//!
//! Entities are the fundamental units in Web4 that accumulate trust.
//! Each entity has:
//! - A unique identifier (type:name format)
//! - T3 Trust Tensor
//! - V3 Value Tensor
//! - Witnessing relationships

mod trust;
mod types;

pub use trust::EntityTrust;
pub use types::EntityType;
