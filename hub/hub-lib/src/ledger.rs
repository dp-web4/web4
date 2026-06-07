// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Chapter ledger — append-only signed event log with hash-chained integrity.
//!
//! ## Why a hub-specific ledger
//!
//! `web4_core::LocalLedger` exists, but its events are fixed to LCT
//! anchoring (Mint, StatusChange). Chapter operations record *domain*
//! events (member added, role assigned, charter amended, event held),
//! which is a different shape.
//!
//! This module reuses the *pattern* (append-only JSONL + sha256 prev-hash
//! chain) and the *crypto primitives* (`web4_core::crypto::sha256_hex`,
//! `KeyPair::sign`, `Lct::verify_signature`) from web4-core. It does
//! **not** reimplement primitives — it composes hub-specific event
//! semantics on top of the canonical crypto.
//!
//! ## Entry shape
//!
//! Each entry holds:
//! - `index` — 0-based position in the chain (Genesis is 0)
//! - `timestamp`
//! - `prev_hash` — sha256 of the previous entry's `entry_hash`; 64 zeros for Genesis
//! - `actor_lct_id` — who signed this entry
//! - `event` — typed ChapterEvent
//! - `signature` — actor's Ed25519 signature over `signing_payload(entry)`
//! - `entry_hash` — sha256 over the full canonical entry (including signature)
//!
//! Verification: signature must validate against the actor's LCT public key;
//! `entry_hash` must match recomputation; `prev_hash` must match the previous
//! entry's `entry_hash`.

use anyhow::{anyhow, Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs::OpenOptions;
use std::io::Write;
use std::path::{Path, PathBuf};
use uuid::Uuid;
use web4_core::crypto::{sha256_hex, KeyPair, SignatureBytes};
use web4_core::lct::Lct;

use crate::events::ChapterEvent;

/// Sentinel prev-hash for the Genesis entry: 64 hex zeros.
pub const GENESIS_PREV_HASH: &str = "0000000000000000000000000000000000000000000000000000000000000000";

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct LedgerEntry {
    pub index: u64,
    pub timestamp: DateTime<Utc>,
    pub prev_hash: String,
    pub actor_lct_id: Uuid,
    pub event: ChapterEvent,
    /// Hex-encoded Ed25519 signature over `signing_payload`.
    pub signature: String,
    /// sha256 hex of the canonical entry (computed with `entry_hash` field cleared).
    pub entry_hash: String,
}

/// The bytes that get signed: the entry's content with `signature` and
/// `entry_hash` both cleared. Deterministic across builds because the
/// serde struct field order is fixed.
fn signing_payload(entry: &LedgerEntry) -> Result<Vec<u8>> {
    let mut tmp = entry.clone();
    tmp.signature = String::new();
    tmp.entry_hash = String::new();
    let json = serde_json::to_string(&tmp).context("serializing entry for signing")?;
    Ok(json.into_bytes())
}

/// sha256 hash of the canonical entry (signature included, entry_hash cleared).
fn compute_entry_hash(entry: &LedgerEntry) -> Result<String> {
    let mut tmp = entry.clone();
    tmp.entry_hash = String::new();
    let json = serde_json::to_string(&tmp).context("serializing entry for hashing")?;
    Ok(sha256_hex(json.as_bytes()))
}

/// Append-only chapter event ledger backed by a JSONL file.
#[derive(Debug)]
pub struct ChapterLedger {
    path: PathBuf,
    entries: Vec<LedgerEntry>,
    head_hash: String,
}

impl ChapterLedger {
    /// Open an existing ledger or create a new (empty) one.
    /// Does NOT write a Genesis entry — that's the caller's responsibility
    /// via [`Self::write_genesis`].
    pub fn open(path: impl AsRef<Path>) -> Result<Self> {
        let path = path.as_ref().to_path_buf();

        if let Some(parent) = path.parent() {
            if !parent.as_os_str().is_empty() {
                std::fs::create_dir_all(parent)
                    .with_context(|| format!("creating parent dir {}", parent.display()))?;
            }
        }

        let mut entries = Vec::new();
        let mut head_hash = GENESIS_PREV_HASH.to_string();

        if path.exists() {
            let content = std::fs::read_to_string(&path)
                .with_context(|| format!("reading {}", path.display()))?;
            for (line_num, line) in content.lines().enumerate() {
                let trimmed = line.trim();
                if trimmed.is_empty() {
                    continue;
                }
                let entry: LedgerEntry = serde_json::from_str(trimmed)
                    .with_context(|| format!("parsing line {} of {}", line_num + 1, path.display()))?;
                head_hash = entry.entry_hash.clone();
                entries.push(entry);
            }
        } else {
            // Create empty file.
            OpenOptions::new().create_new(true).write(true).open(&path)
                .with_context(|| format!("creating {}", path.display()))?;
        }

        Ok(Self { path, entries, head_hash })
    }

    pub fn path(&self) -> &Path { &self.path }
    pub fn entries(&self) -> &[LedgerEntry] { &self.entries }
    pub fn len(&self) -> usize { self.entries.len() }
    pub fn is_empty(&self) -> bool { self.entries.is_empty() }
    pub fn head_hash(&self) -> &str { &self.head_hash }

    /// Write the Genesis entry. Errors if the ledger is not empty.
    pub fn write_genesis(
        &mut self,
        sovereign_lct_id: Uuid,
        sovereign_keypair: &KeyPair,
        chapter_name: String,
        charter_hash: String,
    ) -> Result<&LedgerEntry> {
        if !self.entries.is_empty() {
            return Err(anyhow!("ledger already has entries; Genesis would be illegal"));
        }
        let now = Utc::now();
        let event = ChapterEvent::Genesis {
            chapter_name,
            charter_hash,
            founding_sovereign_lct_id: sovereign_lct_id,
            created_at: now,
        };
        self.append_inner(sovereign_lct_id, sovereign_keypair, event, now)
    }

    /// Append a signed entry to the ledger. Returns the appended entry.
    pub fn append(
        &mut self,
        actor_lct_id: Uuid,
        actor_keypair: &KeyPair,
        event: ChapterEvent,
    ) -> Result<&LedgerEntry> {
        if self.entries.is_empty() {
            return Err(anyhow!("ledger has no Genesis entry; call write_genesis first"));
        }
        self.append_inner(actor_lct_id, actor_keypair, event, Utc::now())
    }

    fn append_inner(
        &mut self,
        actor_lct_id: Uuid,
        actor_keypair: &KeyPair,
        event: ChapterEvent,
        timestamp: DateTime<Utc>,
    ) -> Result<&LedgerEntry> {
        let index = self.entries.len() as u64;
        let prev_hash = self.head_hash.clone();

        // Build entry with empty signature + entry_hash for signing
        let mut entry = LedgerEntry {
            index,
            timestamp,
            prev_hash,
            actor_lct_id,
            event,
            signature: String::new(),
            entry_hash: String::new(),
        };

        let payload = signing_payload(&entry)?;
        let sig = actor_keypair.sign(&payload);
        entry.signature = hex::encode(sig.bytes);

        // Now hash with signature filled in
        entry.entry_hash = compute_entry_hash(&entry)?;

        // Append to file
        let line = serde_json::to_string(&entry).context("serializing entry")?;
        let mut f = OpenOptions::new().append(true).create(true).open(&self.path)
            .with_context(|| format!("opening {} for append", self.path.display()))?;
        writeln!(f, "{}", line)
            .with_context(|| format!("writing to {}", self.path.display()))?;

        self.head_hash = entry.entry_hash.clone();
        self.entries.push(entry);
        Ok(self.entries.last().unwrap())
    }

    /// Verify the entire chain.
    /// `lct_lookup` maps an actor LCT id to its Lct (for signature verification).
    /// Returns Ok(()) if every entry's signature, hash, and prev-hash check out.
    pub fn verify_chain(&self, lct_lookup: impl Fn(Uuid) -> Option<Lct>) -> Result<()> {
        let mut expected_prev = GENESIS_PREV_HASH.to_string();
        for (i, entry) in self.entries.iter().enumerate() {
            // Index check
            if entry.index != i as u64 {
                return Err(anyhow!(
                    "entry {} has index field {}; expected {}",
                    i, entry.index, i
                ));
            }
            // Prev-hash check
            if entry.prev_hash != expected_prev {
                return Err(anyhow!(
                    "entry {} prev_hash mismatch: stored {}, expected {}",
                    i, entry.prev_hash, expected_prev
                ));
            }
            // Entry-hash check
            let recomputed = compute_entry_hash(entry)?;
            if entry.entry_hash != recomputed {
                return Err(anyhow!(
                    "entry {} entry_hash mismatch: stored {}, recomputed {}",
                    i, entry.entry_hash, recomputed
                ));
            }
            // Signature check
            let actor = lct_lookup(entry.actor_lct_id).ok_or_else(|| {
                anyhow!("entry {} actor LCT {} not found by lookup", i, entry.actor_lct_id)
            })?;
            let payload = signing_payload(entry)?;
            let sig_bytes = hex::decode(&entry.signature)
                .with_context(|| format!("decoding entry {} signature", i))?;
            let sig_arr: [u8; 64] = sig_bytes.as_slice().try_into()
                .map_err(|_| anyhow!("entry {} signature must be 64 bytes", i))?;
            let signature = SignatureBytes::from_bytes(sig_arr);
            actor.verify_signature(&payload, &signature)
                .map_err(|e| anyhow!("entry {} signature verification failed: {}", i, e))?;

            expected_prev = entry.entry_hash.clone();
        }
        Ok(())
    }
}

/// Convenience: build a single-entry lookup table for a known set of LCTs.
/// Useful for tests + sprint 2 where the only known LCTs are the Sovereign
/// and (later) members.
pub fn build_lookup(lcts: impl IntoIterator<Item = Lct>) -> HashMap<Uuid, Lct> {
    lcts.into_iter().map(|l| (l.id, l)).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::identity::IdentityFile;
    use tempfile::tempdir;
    use web4_core::lct::EntityType;

    fn fresh_sovereign() -> IdentityFile {
        IdentityFile::generate(EntityType::Human)
    }

    #[test]
    fn open_creates_empty_file() {
        let tmp = tempdir().unwrap();
        let path = tmp.path().join("ledger.jsonl");
        let ledger = ChapterLedger::open(&path).unwrap();
        assert!(path.exists());
        assert!(ledger.is_empty());
        assert_eq!(ledger.head_hash(), GENESIS_PREV_HASH);
    }

    #[test]
    fn genesis_then_one_event_signs_and_verifies() {
        let tmp = tempdir().unwrap();
        let path = tmp.path().join("ledger.jsonl");
        let sovereign = fresh_sovereign();
        let keypair = sovereign.keypair().unwrap();

        let mut ledger = ChapterLedger::open(&path).unwrap();
        ledger.write_genesis(
            sovereign.lct.id,
            &keypair,
            "Test Chapter".into(),
            "sha256:cafebabe".into(),
        ).unwrap();

        let member_id = Uuid::new_v4();
        ledger.append(
            sovereign.lct.id,
            &keypair,
            ChapterEvent::MemberAdded {
                member_lct_id: member_id,
                added_by: sovereign.lct.id,
                member_name: Some("Alice".into()),
            },
        ).unwrap();

        assert_eq!(ledger.len(), 2);

        let lookup_map = build_lookup([sovereign.lct.clone()]);
        ledger.verify_chain(|id| lookup_map.get(&id).cloned()).unwrap();
    }

    #[test]
    fn reopen_replays_chain_integrity() {
        let tmp = tempdir().unwrap();
        let path = tmp.path().join("ledger.jsonl");
        let sovereign = fresh_sovereign();
        let keypair = sovereign.keypair().unwrap();

        {
            let mut ledger = ChapterLedger::open(&path).unwrap();
            ledger.write_genesis(
                sovereign.lct.id, &keypair,
                "X".into(), "sha256:0".into(),
            ).unwrap();
            for _ in 0..3 {
                ledger.append(
                    sovereign.lct.id, &keypair,
                    ChapterEvent::MemberAdded {
                        member_lct_id: Uuid::new_v4(),
                        added_by: sovereign.lct.id,
                        member_name: None,
                    },
                ).unwrap();
            }
        }

        // Re-open and verify
        let reopened = ChapterLedger::open(&path).unwrap();
        assert_eq!(reopened.len(), 4);
        let lookup_map = build_lookup([sovereign.lct.clone()]);
        reopened.verify_chain(|id| lookup_map.get(&id).cloned()).unwrap();
    }

    #[test]
    fn tampered_event_fails_verification() {
        let tmp = tempdir().unwrap();
        let path = tmp.path().join("ledger.jsonl");
        let sovereign = fresh_sovereign();
        let keypair = sovereign.keypair().unwrap();

        let mut ledger = ChapterLedger::open(&path).unwrap();
        ledger.write_genesis(
            sovereign.lct.id, &keypair,
            "X".into(), "sha256:0".into(),
        ).unwrap();
        ledger.append(
            sovereign.lct.id, &keypair,
            ChapterEvent::MemberAdded {
                member_lct_id: Uuid::new_v4(),
                added_by: sovereign.lct.id,
                member_name: Some("Original".into()),
            },
        ).unwrap();

        // Tamper: overwrite the file with a modified version of entry 1
        let content = std::fs::read_to_string(&path).unwrap();
        let lines: Vec<&str> = content.lines().collect();
        let tampered_line = lines[1].replace("Original", "Tampered");
        let new_content = format!("{}\n{}\n", lines[0], tampered_line);
        std::fs::write(&path, new_content).unwrap();

        // Re-open: hash recompute should now mismatch
        let reopened = ChapterLedger::open(&path).unwrap();
        let lookup_map = build_lookup([sovereign.lct.clone()]);
        let result = reopened.verify_chain(|id| lookup_map.get(&id).cloned());
        assert!(result.is_err(), "tampered entry must fail verification");
        let err = format!("{:?}", result.unwrap_err());
        assert!(err.contains("entry_hash mismatch") || err.contains("signature verification failed"),
            "expected hash/signature failure, got: {}", err);
    }

    #[test]
    fn genesis_after_existing_entries_errors() {
        let tmp = tempdir().unwrap();
        let path = tmp.path().join("ledger.jsonl");
        let sovereign = fresh_sovereign();
        let keypair = sovereign.keypair().unwrap();

        let mut ledger = ChapterLedger::open(&path).unwrap();
        ledger.write_genesis(
            sovereign.lct.id, &keypair,
            "X".into(), "sha256:0".into(),
        ).unwrap();

        let result = ledger.write_genesis(
            sovereign.lct.id, &keypair,
            "Y".into(), "sha256:1".into(),
        );
        assert!(result.is_err());
    }

    #[test]
    fn append_before_genesis_errors() {
        let tmp = tempdir().unwrap();
        let path = tmp.path().join("ledger.jsonl");
        let sovereign = fresh_sovereign();
        let keypair = sovereign.keypair().unwrap();

        let mut ledger = ChapterLedger::open(&path).unwrap();
        let result = ledger.append(
            sovereign.lct.id, &keypair,
            ChapterEvent::MemberAdded {
                member_lct_id: Uuid::new_v4(),
                added_by: sovereign.lct.id,
                member_name: None,
            },
        );
        assert!(result.is_err());
    }
}
