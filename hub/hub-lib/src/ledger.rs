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
use uuid::Uuid;
use web4_core::crypto::{sha256_hex, KeyPair, SignatureBytes};
use web4_core::lct::Lct;

use crate::events::ChapterEvent;
use crate::store::ChapterStore;

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

/// A ledger entry that has been assigned its index + prev_hash but not
/// yet signed. The caller (or a remote signer) signs `signing_bytes`
/// and passes the resulting signature to [`ChapterLedger::append_signed`].
///
/// Holding this struct outside the ledger does NOT append an act to
/// the ledger; it's a draft. If a parallel append lands between
/// build_entry and append_signed, the commit will error rather than
/// corrupt the chain.
#[derive(Debug)]
pub struct UnsignedEntry {
    pub entry: LedgerEntry,
    /// The exact bytes the actor must sign. Don't reconstruct these
    /// yourself — use what build_entry returned.
    pub signing_bytes: Vec<u8>,
}

/// Append-only chapter event ledger.
///
/// Owns hash-chain integrity + signing logic. Delegates byte persistence
/// to a [`ChapterStore`] — so the ledger works identically against file,
/// SQLite, or future backends.
pub struct ChapterLedger {
    store: Box<dyn ChapterStore>,
    entries: Vec<LedgerEntry>,
    head_hash: String,
}

impl std::fmt::Debug for ChapterLedger {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("ChapterLedger")
            .field("backend_kind", &self.store.backend_kind())
            .field("entries", &self.entries.len())
            .field("head_hash", &self.head_hash)
            .finish()
    }
}

impl ChapterLedger {
    /// Open a ledger backed by the given store. Loads any existing entries
    /// into memory + restores head_hash. Does NOT write a Genesis entry —
    /// that's the caller's responsibility via [`Self::write_genesis`].
    pub fn open(store: Box<dyn ChapterStore>) -> Result<Self> {
        let entries = store.ledger_load_all()
            .context("loading ledger entries from store")?;
        let head_hash = entries
            .last()
            .map(|e| e.entry_hash.clone())
            .unwrap_or_else(|| GENESIS_PREV_HASH.to_string());
        Ok(Self { store, entries, head_hash })
    }

    pub fn entries(&self) -> &[LedgerEntry] { &self.entries }
    pub fn len(&self) -> usize { self.entries.len() }
    pub fn is_empty(&self) -> bool { self.entries.is_empty() }
    pub fn head_hash(&self) -> &str { &self.head_hash }
    pub fn backend_kind(&self) -> crate::store::BackendKind { self.store.backend_kind() }

    /// Borrow the underlying store. Useful for callers that need to
    /// read/write related artifacts (charter, society) through the same
    /// backend.
    pub fn store(&self) -> &dyn ChapterStore { self.store.as_ref() }
    pub fn store_mut(&mut self) -> &mut dyn ChapterStore { self.store.as_mut() }

    /// Write the Genesis entry. Errors if the ledger is not empty.
    /// Convenience wrapper for callers holding a local keypair.
    pub fn write_genesis(
        &mut self,
        sovereign_lct_id: Uuid,
        sovereign_keypair: &KeyPair,
        chapter_name: String,
        charter_hash: String,
    ) -> Result<&LedgerEntry> {
        let (unsigned, _) = self.build_genesis(sovereign_lct_id, chapter_name, charter_hash)?;
        let sig = sovereign_keypair.sign(&unsigned.signing_bytes);
        self.append_signed(unsigned, SignatureBytes::from_bytes(sig.bytes))
    }

    /// Build the unsigned Genesis entry. Errors if the ledger is not empty.
    /// Returns the unsigned entry + the canonical timestamp it uses (so a
    /// Hestia-mode init can include the timestamp in the sign-request).
    pub fn build_genesis(
        &self,
        sovereign_lct_id: Uuid,
        chapter_name: String,
        charter_hash: String,
    ) -> Result<(UnsignedEntry, DateTime<Utc>)> {
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
        let unsigned = self.build_entry(sovereign_lct_id, event, now)?;
        Ok((unsigned, now))
    }

    /// Append a signed entry to the ledger using a local keypair.
    /// Convenience wrapper over [`Self::build_entry`] + [`Self::append_signed`]
    /// for callers that hold the actor's keypair in-process (MVP path).
    /// For Hestia-mode (the actor's keypair is in a remote vault), use the
    /// split API directly.
    pub fn append(
        &mut self,
        actor_lct_id: Uuid,
        actor_keypair: &KeyPair,
        event: ChapterEvent,
    ) -> Result<&LedgerEntry> {
        if self.entries.is_empty() {
            return Err(anyhow!("ledger has no Genesis entry; call write_genesis first"));
        }
        let unsigned = self.build_entry(actor_lct_id, event, Utc::now())?;
        let sig = actor_keypair.sign(&unsigned.signing_bytes);
        self.append_signed(unsigned, SignatureBytes::from_bytes(sig.bytes))
    }

    /// Build an unsigned entry: assigns index + prev_hash + actor + event,
    /// returns the exact signing bytes the actor must sign. Does NOT
    /// append the act to the ledger — caller commits via [`Self::append_signed`].
    ///
    /// Enables async signing: caller hands `signing_bytes` to a remote
    /// signer (vault, HSM, Hestia), awaits the signature, then commits.
    pub fn build_entry(
        &self,
        actor_lct_id: Uuid,
        event: ChapterEvent,
        timestamp: DateTime<Utc>,
    ) -> Result<UnsignedEntry> {
        // Genesis is its own path (write_genesis). All other entries
        // require a Genesis to exist.
        let entry = LedgerEntry {
            index: self.entries.len() as u64,
            timestamp,
            prev_hash: self.head_hash.clone(),
            actor_lct_id,
            event,
            signature: String::new(),
            entry_hash: String::new(),
        };
        let signing_bytes = signing_payload(&entry)?;
        Ok(UnsignedEntry { entry, signing_bytes })
    }

    /// Commit a signed entry: fills in the signature + computes
    /// entry_hash + persists to the store + advances head_hash.
    /// Caller is responsible for producing a valid signature over
    /// `unsigned.signing_bytes`.
    pub fn append_signed(
        &mut self,
        mut unsigned: UnsignedEntry,
        signature: SignatureBytes,
    ) -> Result<&LedgerEntry> {
        // Sanity: the unsigned entry's index must match our current tail.
        // (Could happen if a parallel append landed between build and commit.)
        let expected_index = self.entries.len() as u64;
        if unsigned.entry.index != expected_index {
            return Err(anyhow!(
                "ledger advanced between build_entry and append_signed: \
                 unsigned.index={}, current expected={}",
                unsigned.entry.index, expected_index
            ));
        }
        if unsigned.entry.prev_hash != self.head_hash {
            return Err(anyhow!(
                "ledger head changed between build_entry and append_signed: \
                 unsigned.prev_hash={}, current head_hash={}",
                unsigned.entry.prev_hash, self.head_hash
            ));
        }

        unsigned.entry.signature = hex::encode(signature.bytes);
        unsigned.entry.entry_hash = compute_entry_hash(&unsigned.entry)?;

        self.store.ledger_append(&unsigned.entry)
            .context("persisting ledger entry via store")?;

        self.head_hash = unsigned.entry.entry_hash.clone();
        self.entries.push(unsigned.entry);
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
    use crate::chapter::ChapterPaths;
    use crate::identity::IdentityFile;
    use crate::store::FileBackend;
    use tempfile::tempdir;
    use web4_core::lct::EntityType;

    fn fresh_sovereign() -> IdentityFile {
        IdentityFile::generate(EntityType::Human)
    }

    fn fresh_store(tmp: &tempfile::TempDir) -> (Box<dyn ChapterStore>, std::path::PathBuf) {
        let chapter_dir = tmp.path().join("chap");
        std::fs::create_dir_all(&chapter_dir).unwrap();
        let paths = ChapterPaths::new(chapter_dir.clone());
        let ledger_path = paths.ledger();
        (Box::new(FileBackend::new(paths)), ledger_path)
    }

    fn reopen_file_backend(tmp: &tempfile::TempDir) -> Box<dyn ChapterStore> {
        let chapter_dir = tmp.path().join("chap");
        Box::new(FileBackend::new(ChapterPaths::new(chapter_dir)))
    }

    #[test]
    fn open_creates_empty_file() {
        let tmp = tempdir().unwrap();
        let (store, _) = fresh_store(&tmp);
        let ledger = ChapterLedger::open(store).unwrap();
        assert!(ledger.is_empty());
        assert_eq!(ledger.head_hash(), GENESIS_PREV_HASH);
    }

    #[test]
    fn genesis_then_one_event_signs_and_verifies() {
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();
        let keypair = sovereign.keypair().unwrap();

        let (store, _) = fresh_store(&tmp);
        let mut ledger = ChapterLedger::open(store).unwrap();
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
        let sovereign = fresh_sovereign();
        let keypair = sovereign.keypair().unwrap();

        {
            let (store, _) = fresh_store(&tmp);
            let mut ledger = ChapterLedger::open(store).unwrap();
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

        // Re-open a fresh store pointing at the same dir and verify.
        let reopened = ChapterLedger::open(reopen_file_backend(&tmp)).unwrap();
        assert_eq!(reopened.len(), 4);
        let lookup_map = build_lookup([sovereign.lct.clone()]);
        reopened.verify_chain(|id| lookup_map.get(&id).cloned()).unwrap();
    }

    #[test]
    fn tampered_event_fails_verification() {
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();
        let keypair = sovereign.keypair().unwrap();

        let (store, ledger_path) = fresh_store(&tmp);
        let mut ledger = ChapterLedger::open(store).unwrap();
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
        drop(ledger);

        // Tamper directly at the file-backed layer: this test is
        // file-backend-specific (it knows where bytes live). SqliteBackend
        // would need its own tamper test.
        let content = std::fs::read_to_string(&ledger_path).unwrap();
        let lines: Vec<&str> = content.lines().collect();
        let tampered_line = lines[1].replace("Original", "Tampered");
        let new_content = format!("{}\n{}\n", lines[0], tampered_line);
        std::fs::write(&ledger_path, new_content).unwrap();

        // Re-open: hash recompute should now mismatch
        let reopened = ChapterLedger::open(reopen_file_backend(&tmp)).unwrap();
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
        let sovereign = fresh_sovereign();
        let keypair = sovereign.keypair().unwrap();

        let (store, _) = fresh_store(&tmp);
        let mut ledger = ChapterLedger::open(store).unwrap();
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
    fn split_api_simulates_remote_signing() {
        // The split build_entry / append_signed API enables Hestia-mode
        // where the actor's keypair lives in a remote vault. Simulate it
        // here: we hold the keypair locally, but pretend we're a "remote
        // signer" that only sees the signing bytes the ledger hands us.
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();
        let kp = sovereign.keypair().unwrap();

        let (store, _) = fresh_store(&tmp);
        let mut ledger = ChapterLedger::open(store).unwrap();

        // Genesis via the split path
        let (unsigned_genesis, _ts) = ledger.build_genesis(
            sovereign.lct.id,
            "Split Test".into(),
            "0".repeat(64),
        ).unwrap();
        // "Remote signer" sees only signing_bytes
        let bytes_to_sign = unsigned_genesis.signing_bytes.clone();
        let sig_obj = kp.sign(&bytes_to_sign);
        let sig = SignatureBytes::from_bytes(sig_obj.bytes);
        ledger.append_signed(unsigned_genesis, sig).unwrap();

        // Member added via the split path
        let unsigned_member = ledger.build_entry(
            sovereign.lct.id,
            ChapterEvent::MemberAdded {
                member_lct_id: Uuid::new_v4(),
                added_by: sovereign.lct.id,
                member_name: Some("Alice".into()),
            },
            Utc::now(),
        ).unwrap();
        let bytes_to_sign = unsigned_member.signing_bytes.clone();
        let sig = SignatureBytes::from_bytes(kp.sign(&bytes_to_sign).bytes);
        ledger.append_signed(unsigned_member, sig).unwrap();

        assert_eq!(ledger.len(), 2);

        // Chain verifies
        let lookup_map = build_lookup([sovereign.lct.clone()]);
        ledger.verify_chain(|id| lookup_map.get(&id).cloned()).unwrap();
    }

    #[test]
    fn append_signed_rejects_stale_unsigned_entry() {
        // If a parallel append landed between build_entry and append_signed,
        // the commit must fail rather than corrupt the chain.
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();
        let kp = sovereign.keypair().unwrap();

        let (store, _) = fresh_store(&tmp);
        let mut ledger = ChapterLedger::open(store).unwrap();
        ledger.write_genesis(
            sovereign.lct.id, &kp,
            "X".into(), "0".repeat(64),
        ).unwrap();

        // Build entry A (gets index=1, prev_hash=genesis_hash)
        let unsigned_a = ledger.build_entry(
            sovereign.lct.id,
            ChapterEvent::MemberAdded { member_lct_id: Uuid::new_v4(), added_by: sovereign.lct.id, member_name: None },
            Utc::now(),
        ).unwrap();

        // In parallel, entry B lands first (also index=1 at build time,
        // but commits before A and becomes the actual index=1)
        ledger.append(
            sovereign.lct.id, &kp,
            ChapterEvent::MemberAdded { member_lct_id: Uuid::new_v4(), added_by: sovereign.lct.id, member_name: Some("B".into()) },
        ).unwrap();

        // Now A tries to commit; should fail because the ledger advanced
        let sig = SignatureBytes::from_bytes(kp.sign(&unsigned_a.signing_bytes).bytes);
        let result = ledger.append_signed(unsigned_a, sig);
        assert!(result.is_err(), "stale unsigned must be rejected, not silently overwrite");
        let err = format!("{:?}", result.unwrap_err());
        assert!(err.contains("ledger advanced") || err.contains("head changed"),
            "expected stale-detection error, got: {}", err);
    }

    #[test]
    fn append_before_genesis_errors() {
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();
        let keypair = sovereign.keypair().unwrap();

        let (store, _) = fresh_store(&tmp);
        let mut ledger = ChapterLedger::open(store).unwrap();
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
