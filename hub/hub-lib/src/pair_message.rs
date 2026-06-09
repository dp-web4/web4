// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! PAIRED-CHANNELS Sprint D: pair message sidecar.
//!
//! Per-pair message log lives outside the ledger to keep the chain
//! compact for high-traffic pairs. Each message has a corresponding
//! `HubEvent::PairMessagePosted` ledger entry recording metadata +
//! `payload_hash`; the bytes themselves live in
//! `HubStore::append_pair_message`. Auditor verifies a sidecar entry
//! by recomputing sha256(payload) and matching against the ledger
//! event's `payload_hash` — sidecar tamper is detectable.
//!
//! At Sprint D the payload is a plaintext string (proving the pipe).
//! At Sprint E it becomes opaque ciphertext (ChaCha20-Poly1305
//! over an HKDF-derived session key); the structure here is
//! unchanged — only the payload contents shift from text to
//! base64-encoded ciphertext bytes. Sprint F adds an `ephemeral_pub`
//! field for the per-session forward-secrecy ratchet.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// A single message in a pair's sidecar log.
///
/// Fields are stable across Sprint D → E → F (we only ever add
/// optional fields via serde default + skip_serializing_if).
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PairMessage {
    pub pair_id: Uuid,
    /// Monotonic per pair, assigned by the hub at append time.
    /// Caller doesn't choose; the store/ledger pair determines it.
    pub seq: u64,
    /// Envelope signer of the post. Must be one of the pair's two
    /// LCT participants — REST layer enforces this.
    pub from: Uuid,
    pub posted_at: DateTime<Utc>,
    /// Sprint D: plaintext payload. Sprint E swaps for opaque
    /// ciphertext (base64-encoded for JSON wire compat). The store
    /// treats it as bytes either way.
    pub payload: String,
    /// Sprint F (placeholder, currently unused): the sender's
    /// ephemeral X25519 public key for this session's ratchet
    /// position. Sprint D leaves this None.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub ephemeral_pub_hex: Option<String>,
}

impl PairMessage {
    /// Compute the canonical payload hash for the ledger event. Hub
    /// computes this at append time and stores it in the
    /// `PairMessagePosted` event so auditors can detect sidecar
    /// tampering by recomputation.
    pub fn payload_hash(payload: &str) -> String {
        web4_core::crypto::sha256_hex(payload.as_bytes())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn payload_hash_is_deterministic_sha256() {
        let h1 = PairMessage::payload_hash("hello");
        let h2 = PairMessage::payload_hash("hello");
        assert_eq!(h1, h2);
        assert_ne!(h1, PairMessage::payload_hash("world"));
        // Spot-check: known SHA-256 of "hello"
        assert_eq!(h1, "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824");
    }

    #[test]
    fn serde_round_trip_sprint_d_shape() {
        let msg = PairMessage {
            pair_id: Uuid::new_v4(),
            seq: 7,
            from: Uuid::new_v4(),
            posted_at: Utc::now(),
            payload: "hello there".into(),
            ephemeral_pub_hex: None,
        };
        let json = serde_json::to_string(&msg).unwrap();
        assert!(!json.contains("ephemeral_pub_hex"),
            "None must be skipped so Sprint D wire shape stays clean");
        let back: PairMessage = serde_json::from_str(&json).unwrap();
        assert_eq!(back.seq, 7);
        assert_eq!(back.payload, "hello there");
    }
}
