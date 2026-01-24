//! Temporal decay functions
//!
//! Trust decays over time when entities are inactive.
//! This ensures trust reflects recency and prevents stale trust.

mod temporal;

pub use temporal::{DecayConfig, calculate_decay_factor};
