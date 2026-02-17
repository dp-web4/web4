// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: MIT
//
// This software is covered by US Patents 11,477,027 and 12,278,913,
// and pending application 19/178,619. See PATENTS.md for details.

//! Error types for web4-core
//!
//! Provides structured error handling across the library.

use thiserror::Error;

/// Primary error type for web4-core operations
#[derive(Error, Debug)]
pub enum Web4Error {
    /// Cryptographic operation failed
    #[error("Cryptographic error: {0}")]
    Crypto(String),

    /// Signature verification failed
    #[error("Signature verification failed: {0}")]
    SignatureInvalid(String),

    /// LCT-related error
    #[error("LCT error: {0}")]
    Lct(String),

    /// Identity coherence below threshold
    #[error("Coherence threshold not met: {score:.3} < {threshold:.3}")]
    CoherenceBelowThreshold { score: f64, threshold: f64 },

    /// Serialization/deserialization error
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),

    /// Invalid input provided
    #[error("Invalid input: {0}")]
    InvalidInput(String),

    /// Entity not found
    #[error("Entity not found: {0}")]
    NotFound(String),

    /// Operation not authorized
    #[error("Not authorized: {0}")]
    Unauthorized(String),

    /// LCT has been voided or slashed
    #[error("LCT voided: {0}")]
    LctVoided(String),
}

/// Result type alias for web4-core operations
pub type Result<T> = std::result::Result<T, Web4Error>;
