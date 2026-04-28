// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// This software is covered by US Patents 11,477,027 and 12,278,913,
// and pending application 19/178,619. See PATENTS.md for details.

//! # Ledger
//!
//! LCTs are inherently blockchain tokens (NFTs). They must be **anchored** to a
//! ledger to be meaningful — a standalone LCT is a category mistake.
//!
//! This module defines the [`Ledger`] trait that any backend implements, plus
//! two built-in backends:
//!
//! - [`InMemoryLedger`] — for tests, prototyping, ephemeral runs.
//! - [`LocalLedger`] — file-based JSON-lines hash chain. Persistent, tamper-
//!   evident, suitable for solo dev / team-scoped accountability / regulated
//!   environments. Mirrors the Hardbound `src/ledger/` design pattern in Rust.
//!
//! Future backends (separate crates):
//!
//! - `web4-act-client::ActLedger` — HTTP/REST client to ACT's Cosmos SDK
//!   gateway, for federation-wide consensus.
//!
//! ## Quick start
//!
//! ```rust
//! use web4_core::{Lct, EntityType, InMemoryLedger, Ledger};
//!
//! let (lct, _keypair) = Lct::new(EntityType::Human, None);
//! let mut ledger = InMemoryLedger::new();
//! let receipt = lct.mint(&mut ledger).unwrap();
//!
//! assert_eq!(receipt.lct_id, lct.id);
//! let looked_up = ledger.lookup(lct.id).unwrap().unwrap();
//! assert_eq!(looked_up.id, lct.id);
//! ```

pub mod in_memory;
pub mod local;

pub use in_memory::InMemoryLedger;
pub use local::LocalLedger;

use crate::crypto::sha256_hex;
use crate::error::{Result, Web4Error};
use crate::lct::{Lct, LctStatus};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Receipt returned when an LCT is minted into a ledger.
///
/// Contains the entry hash and position for later verification. Persist this
/// alongside the LCT to prove it was anchored at a specific point in the
/// ledger's history.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct MintReceipt {
    /// The minted LCT's ID.
    pub lct_id: Uuid,
    /// Index of the mint entry in the ledger (0 = genesis).
    pub entry_index: u64,
    /// Hex-encoded SHA-256 hash of this entry's canonical form.
    pub entry_hash: String,
    /// Hex-encoded hash of the previous entry (or 64 zeros for genesis).
    pub prev_hash: String,
    /// Backend identifier (e.g. "in-memory", "local-file", "act-cosmos").
    pub backend: String,
    /// Timestamp the mint was recorded.
    pub minted_at: DateTime<Utc>,
}

/// A single entry in a ledger's append-only log.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct LedgerEntry {
    /// Position in the chain (0 = genesis).
    pub index: u64,
    /// When this entry was recorded.
    pub timestamp: DateTime<Utc>,
    /// Hash of the previous entry (or 64 zeros for genesis).
    pub prev_hash: String,
    /// Canonical hash of this entry (computed over all other fields).
    pub entry_hash: String,
    /// What this entry records.
    pub event: LedgerEvent,
}

/// What kind of event a ledger entry represents.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum LedgerEvent {
    /// Genesis entry — establishes the ledger.
    Genesis {
        /// Backend kind (e.g. "in-memory", "local-file").
        backend: String,
        /// When the ledger was created.
        created_at: DateTime<Utc>,
    },
    /// An LCT was minted (anchored to this ledger).
    Mint {
        /// The minted LCT.
        lct: Lct,
    },
    /// An LCT's status changed.
    StatusChange {
        /// Affected LCT.
        lct_id: Uuid,
        /// Previous status.
        from: LctStatus,
        /// New status.
        to: LctStatus,
    },
}

/// Cryptographic proof that an LCT exists in a ledger at a specific position.
///
/// A proof can be verified later (online or offline, depending on backend) to
/// confirm the LCT was anchored before tampering. For local ledgers, verifying
/// the proof requires access to the ledger's current state. For chain-based
/// backends, proofs may be Merkle paths verifiable from the chain head.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct LedgerProof {
    /// LCT being proved.
    pub lct_id: Uuid,
    /// Index of the mint entry.
    pub entry_index: u64,
    /// Hash of the mint entry.
    pub entry_hash: String,
    /// Current head hash of the ledger when the proof was generated.
    pub head_hash: String,
    /// Backend that produced this proof.
    pub backend: String,
    /// When the proof was generated.
    pub generated_at: DateTime<Utc>,
}

/// Anchors LCTs to a ledger and supports lookup, status updates, and proofs.
///
/// Implementations must:
/// - Append entries in order with prev_hash linking
/// - Reject duplicate mints (same LCT ID)
/// - Maintain consistency between the entry log and the LCT lookup table
pub trait Ledger {
    /// Mint a new LCT, anchoring it to the ledger.
    ///
    /// Returns a [`MintReceipt`] with the entry hash and position. Errors if an
    /// LCT with the same ID has already been minted.
    fn mint(&mut self, lct: &Lct) -> Result<MintReceipt>;

    /// Look up an LCT by ID.
    ///
    /// Returns `Ok(None)` if the LCT was never minted to this ledger.
    fn lookup(&self, id: Uuid) -> Result<Option<Lct>>;

    /// Update an LCT's status (Active → Dormant → Void → Slashed).
    ///
    /// Records the transition as a new ledger entry and updates the
    /// in-memory state. Errors if the LCT was never minted.
    fn update_status(&mut self, id: Uuid, status: LctStatus) -> Result<LedgerEntry>;

    /// Generate proof that an LCT exists in the ledger.
    fn anchor(&self, id: Uuid) -> Result<LedgerProof>;

    /// Verify a proof against the current ledger state.
    ///
    /// Returns `Ok(true)` if the proof is valid (the LCT was anchored at the
    /// stated position with the stated hash). Returns `Ok(false)` if the proof
    /// doesn't match (e.g., LCT not present or hash differs). Errors only on
    /// internal failures (e.g., I/O errors for file-backed ledgers).
    fn verify_proof(&self, proof: &LedgerProof) -> Result<bool>;

    /// Backend identifier (used in receipts and proofs).
    fn backend_kind(&self) -> &'static str;

    /// Total number of entries in the ledger (including genesis).
    fn len(&self) -> u64;

    /// Whether the ledger has any entries beyond genesis.
    fn is_empty(&self) -> bool {
        self.len() <= 1
    }
}

// ---------------------------------------------------------------------------
// Internals shared by backend implementations
// ---------------------------------------------------------------------------

/// Genesis prev-hash sentinel (64 hex zeros).
pub(crate) fn genesis_prev_hash() -> String {
    "0".repeat(64)
}

/// Compute the canonical hash of a ledger entry (excluding `entry_hash` itself).
///
/// Hash = SHA-256 over the JSON serialization of the entry with the
/// `entry_hash` field cleared. This makes the hash deterministic and
/// reproducible across implementations.
pub(crate) fn compute_entry_hash(entry: &LedgerEntry) -> Result<String> {
    let mut canonical = entry.clone();
    canonical.entry_hash = String::new();
    let json = serde_json::to_string(&canonical)?;
    Ok(sha256_hex(json.as_bytes()))
}

/// Build a genesis entry for a freshly-created ledger.
pub(crate) fn build_genesis_entry(backend: &str) -> Result<LedgerEntry> {
    let now = Utc::now();
    let mut entry = LedgerEntry {
        index: 0,
        timestamp: now,
        prev_hash: genesis_prev_hash(),
        entry_hash: String::new(),
        event: LedgerEvent::Genesis {
            backend: backend.to_string(),
            created_at: now,
        },
    };
    entry.entry_hash = compute_entry_hash(&entry)?;
    Ok(entry)
}

/// Build a mint entry chained to the current head.
pub(crate) fn build_mint_entry(index: u64, prev_hash: &str, lct: &Lct) -> Result<LedgerEntry> {
    let mut entry = LedgerEntry {
        index,
        timestamp: Utc::now(),
        prev_hash: prev_hash.to_string(),
        entry_hash: String::new(),
        event: LedgerEvent::Mint { lct: lct.clone() },
    };
    entry.entry_hash = compute_entry_hash(&entry)?;
    Ok(entry)
}

/// Build a status-change entry chained to the current head.
pub(crate) fn build_status_entry(
    index: u64,
    prev_hash: &str,
    lct_id: Uuid,
    from: LctStatus,
    to: LctStatus,
) -> Result<LedgerEntry> {
    let mut entry = LedgerEntry {
        index,
        timestamp: Utc::now(),
        prev_hash: prev_hash.to_string(),
        entry_hash: String::new(),
        event: LedgerEvent::StatusChange { lct_id, from, to },
    };
    entry.entry_hash = compute_entry_hash(&entry)?;
    Ok(entry)
}

/// Verify the entry's stored hash matches its canonical hash.
pub(crate) fn verify_entry_hash(entry: &LedgerEntry) -> Result<bool> {
    let expected = compute_entry_hash(entry)?;
    Ok(expected == entry.entry_hash)
}

/// Helper for backends to convert a "not found" condition into a domain error.
pub(crate) fn not_found(id: Uuid) -> Web4Error {
    Web4Error::NotFound(format!("LCT {} not in ledger", id))
}

/// Helper for backends to convert a "duplicate mint" condition into a domain error.
pub(crate) fn duplicate(id: Uuid) -> Web4Error {
    Web4Error::Ledger(format!("LCT {} already minted", id))
}
