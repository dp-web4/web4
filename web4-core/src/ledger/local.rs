// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later

//! File-based local ledger backend.
//!
//! Persistent, hash-chained, tamper-evident. Each entry is one JSON line in
//! an append-only file. On open, the file is replayed to reconstruct LCT
//! state and verify the chain integrity (every `prev_hash` must match the
//! previous entry's `entry_hash`).
//!
//! Suitable for solo dev, team-scoped accountability, regulated/air-gapped
//! environments. Mirrors the design pattern used by Hardbound's
//! `src/ledger/` (TypeScript) but in Rust.
//!
//! ## Format
//!
//! One JSON object per line, no trailing comma, append-only:
//!
//! ```jsonl
//! {"index":0,"timestamp":"...","prev_hash":"00...00","entry_hash":"...","event":{"kind":"genesis",...}}
//! {"index":1,"timestamp":"...","prev_hash":"...","entry_hash":"...","event":{"kind":"mint","lct":{...}}}
//! ```
//!
//! ## Example
//!
//! ```no_run
//! use web4_core::{Lct, EntityType, LocalLedger, Ledger};
//!
//! let mut ledger = LocalLedger::open("./team.jsonl").unwrap();
//! let (lct, _kp) = Lct::new(EntityType::Human, None);
//! ledger.mint(&lct).unwrap();
//!
//! // Reopen — state is reconstructed from the file
//! let ledger2 = LocalLedger::open("./team.jsonl").unwrap();
//! assert_eq!(ledger2.lookup(lct.id).unwrap().map(|l| l.id), Some(lct.id));
//! ```

use super::{
    build_genesis_entry, build_mint_entry, build_status_entry, duplicate, genesis_prev_hash,
    not_found, verify_entry_hash, Ledger, LedgerEntry, LedgerEvent, LedgerProof, MintReceipt,
};
use crate::error::{Result, Web4Error};
use crate::lct::{Lct, LctStatus};
use chrono::Utc;
use std::collections::HashMap;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use uuid::Uuid;

/// File-based ledger backed by an append-only JSON-lines file.
#[derive(Debug)]
pub struct LocalLedger {
    path: PathBuf,
    entries: Vec<LedgerEntry>,
    lcts: HashMap<Uuid, Lct>,
    head_hash: String,
}

impl LocalLedger {
    /// Backend identifier.
    pub const BACKEND_KIND: &'static str = "local-file";

    /// Open an existing ledger file or create a new one.
    ///
    /// On open: replays the file, verifies the hash chain, and reconstructs
    /// LCT state. Errors if the chain is broken (tamper detected) or if any
    /// entry's stored hash doesn't match its canonical hash.
    ///
    /// On create: writes a genesis entry to the file.
    pub fn open<P: AsRef<Path>>(path: P) -> Result<Self> {
        let path = path.as_ref().to_path_buf();

        if path.exists() {
            Self::load_existing(path)
        } else {
            Self::create_new(path)
        }
    }

    fn create_new(path: PathBuf) -> Result<Self> {
        if let Some(parent) = path.parent() {
            if !parent.as_os_str().is_empty() {
                fs::create_dir_all(parent).map_err(io_to_w4)?;
            }
        }
        let genesis = build_genesis_entry(Self::BACKEND_KIND)?;
        let head_hash = genesis.entry_hash.clone();

        let line = serde_json::to_string(&genesis)?;
        let mut file = OpenOptions::new()
            .create_new(true)
            .write(true)
            .open(&path)
            .map_err(io_to_w4)?;
        writeln!(file, "{}", line).map_err(io_to_w4)?;

        Ok(Self {
            path,
            entries: vec![genesis],
            lcts: HashMap::new(),
            head_hash,
        })
    }

    fn load_existing(path: PathBuf) -> Result<Self> {
        let content = fs::read_to_string(&path).map_err(io_to_w4)?;
        let mut entries: Vec<LedgerEntry> = Vec::new();
        for (line_num, line) in content.lines().enumerate() {
            let trimmed = line.trim();
            if trimmed.is_empty() {
                continue;
            }
            let entry: LedgerEntry = serde_json::from_str(trimmed).map_err(|e| {
                Web4Error::Ledger(format!(
                    "parse error at line {} of {}: {}",
                    line_num + 1,
                    path.display(),
                    e
                ))
            })?;
            entries.push(entry);
        }

        if entries.is_empty() {
            return Err(Web4Error::Ledger(format!(
                "ledger file {} is empty (no genesis entry)",
                path.display()
            )));
        }

        // Verify chain integrity and replay state
        let mut lcts: HashMap<Uuid, Lct> = HashMap::new();
        let mut expected_prev = genesis_prev_hash();
        for entry in &entries {
            if entry.prev_hash != expected_prev {
                return Err(Web4Error::Ledger(format!(
                    "tamper detected at index {}: prev_hash mismatch",
                    entry.index
                )));
            }
            if !verify_entry_hash(entry)? {
                return Err(Web4Error::Ledger(format!(
                    "tamper detected at index {}: entry_hash mismatch",
                    entry.index
                )));
            }
            match &entry.event {
                LedgerEvent::Genesis { .. } => {
                    // Verify it's actually at index 0
                    if entry.index != 0 {
                        return Err(Web4Error::Ledger(format!(
                            "genesis entry at non-zero index {}",
                            entry.index
                        )));
                    }
                }
                LedgerEvent::Mint { lct } => {
                    if lcts.contains_key(&lct.id) {
                        return Err(Web4Error::Ledger(format!(
                            "duplicate mint for LCT {} at index {}",
                            lct.id, entry.index
                        )));
                    }
                    lcts.insert(lct.id, lct.clone());
                }
                LedgerEvent::StatusChange { lct_id, to, .. } => {
                    let stored = lcts.get_mut(lct_id).ok_or_else(|| {
                        Web4Error::Ledger(format!(
                            "status change at index {} references unknown LCT {}",
                            entry.index, lct_id
                        ))
                    })?;
                    stored.status = to.clone();
                }
                LedgerEvent::Act { .. } => {
                    // A witnessed act is a governance record over off-ledger
                    // substance; it doesn't mutate LCT state during replay.
                }
            }
            expected_prev = entry.entry_hash.clone();
        }

        let head_hash = entries.last().expect("non-empty above").entry_hash.clone();
        Ok(Self {
            path,
            entries,
            lcts,
            head_hash,
        })
    }

    fn append_entry(&mut self, entry: LedgerEntry) -> Result<()> {
        let line = serde_json::to_string(&entry)?;
        let mut file = OpenOptions::new()
            .append(true)
            .open(&self.path)
            .map_err(io_to_w4)?;
        writeln!(file, "{}", line).map_err(io_to_w4)?;
        self.head_hash = entry.entry_hash.clone();
        self.entries.push(entry);
        Ok(())
    }

    /// Path of the ledger file.
    pub fn path(&self) -> &Path {
        &self.path
    }

    /// Iterate over all entries (replayed from file).
    pub fn entries(&self) -> &[LedgerEntry] {
        &self.entries
    }
}

impl Ledger for LocalLedger {
    fn mint(&mut self, lct: &Lct) -> Result<MintReceipt> {
        if self.lcts.contains_key(&lct.id) {
            return Err(duplicate(lct.id));
        }
        let entry = build_mint_entry(self.entries.len() as u64, &self.head_hash, lct)?;
        let receipt = MintReceipt {
            lct_id: lct.id,
            entry_index: entry.index,
            entry_hash: entry.entry_hash.clone(),
            prev_hash: entry.prev_hash.clone(),
            backend: Self::BACKEND_KIND.to_string(),
            minted_at: entry.timestamp,
        };
        self.lcts.insert(lct.id, lct.clone());
        self.append_entry(entry)?;
        Ok(receipt)
    }

    fn lookup(&self, id: Uuid) -> Result<Option<Lct>> {
        Ok(self.lcts.get(&id).cloned())
    }

    fn update_status(&mut self, id: Uuid, status: LctStatus) -> Result<LedgerEntry> {
        let lct = self.lcts.get(&id).ok_or_else(|| not_found(id))?;
        let from = lct.status.clone();
        if from == status {
            return Err(Web4Error::InvalidInput(format!(
                "LCT {} is already in status {:?}",
                id, status
            )));
        }
        let entry = build_status_entry(
            self.entries.len() as u64,
            &self.head_hash,
            id,
            from,
            status.clone(),
        )?;
        if let Some(stored) = self.lcts.get_mut(&id) {
            stored.status = status;
        }
        self.append_entry(entry.clone())?;
        Ok(entry)
    }

    fn anchor(&self, id: Uuid) -> Result<LedgerProof> {
        let entry = self
            .entries
            .iter()
            .find(|e| matches!(&e.event, LedgerEvent::Mint { lct } if lct.id == id))
            .ok_or_else(|| not_found(id))?;
        Ok(LedgerProof {
            lct_id: id,
            entry_index: entry.index,
            entry_hash: entry.entry_hash.clone(),
            head_hash: self.head_hash.clone(),
            backend: Self::BACKEND_KIND.to_string(),
            generated_at: Utc::now(),
        })
    }

    fn verify_proof(&self, proof: &LedgerProof) -> Result<bool> {
        if proof.backend != Self::BACKEND_KIND {
            return Ok(false);
        }
        let Some(entry) = self.entries.get(proof.entry_index as usize) else {
            return Ok(false);
        };
        if entry.entry_hash != proof.entry_hash {
            return Ok(false);
        }
        let mints_match = matches!(
            &entry.event,
            LedgerEvent::Mint { lct } if lct.id == proof.lct_id
        );
        if !mints_match {
            return Ok(false);
        }
        if !verify_entry_hash(entry)? {
            return Ok(false);
        }
        Ok(true)
    }

    fn backend_kind(&self) -> &'static str {
        Self::BACKEND_KIND
    }

    fn len(&self) -> u64 {
        self.entries.len() as u64
    }
}

fn io_to_w4(e: std::io::Error) -> Web4Error {
    Web4Error::Ledger(format!("I/O error: {}", e))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::lct::EntityType;
    use std::fs::File;
    use std::io::Write as _;

    fn tmp_path(suffix: &str) -> PathBuf {
        let mut p = std::env::temp_dir();
        p.push(format!(
            "web4-core-ledger-test-{}-{}.jsonl",
            uuid::Uuid::new_v4(),
            suffix
        ));
        p
    }

    #[test]
    fn create_new_ledger_writes_genesis() {
        let path = tmp_path("genesis");
        let _ = fs::remove_file(&path);
        let ledger = LocalLedger::open(&path).unwrap();
        assert_eq!(ledger.len(), 1);
        assert!(matches!(
            ledger.entries()[0].event,
            LedgerEvent::Genesis { .. }
        ));
        let _ = fs::remove_file(&path);
    }

    #[test]
    fn mint_persists_across_reopen() {
        let path = tmp_path("persist");
        let _ = fs::remove_file(&path);
        let lct_id;
        {
            let mut ledger = LocalLedger::open(&path).unwrap();
            let (lct, _) = Lct::new(EntityType::Human, None);
            lct_id = lct.id;
            ledger.mint(&lct).unwrap();
        }
        let ledger = LocalLedger::open(&path).unwrap();
        assert_eq!(ledger.len(), 2);
        assert_eq!(ledger.lookup(lct_id).unwrap().map(|l| l.id), Some(lct_id));
        let _ = fs::remove_file(&path);
    }

    #[test]
    fn status_change_persists() {
        let path = tmp_path("status");
        let _ = fs::remove_file(&path);
        let lct_id;
        {
            let mut ledger = LocalLedger::open(&path).unwrap();
            let (lct, _) = Lct::new(EntityType::AiSoftware, None);
            lct_id = lct.id;
            ledger.mint(&lct).unwrap();
            ledger.update_status(lct_id, LctStatus::Slashed).unwrap();
        }
        let ledger = LocalLedger::open(&path).unwrap();
        let restored = ledger.lookup(lct_id).unwrap().unwrap();
        assert_eq!(restored.status, LctStatus::Slashed);
        let _ = fs::remove_file(&path);
    }

    #[test]
    fn tamper_detection_on_reopen() {
        let path = tmp_path("tamper");
        let _ = fs::remove_file(&path);
        {
            let mut ledger = LocalLedger::open(&path).unwrap();
            let (lct, _) = Lct::new(EntityType::Human, None);
            ledger.mint(&lct).unwrap();
        }
        // Append a forged entry with a bad prev_hash
        let mut file = OpenOptions::new().append(true).open(&path).unwrap();
        let bogus = r#"{"index":2,"timestamp":"2099-01-01T00:00:00Z","prev_hash":"deadbeef","entry_hash":"deadbeef","event":{"kind":"mint","lct":{}}}"#;
        writeln!(file, "{}", bogus).unwrap();
        drop(file);

        let result = LocalLedger::open(&path);
        assert!(result.is_err());
        let _ = fs::remove_file(&path);
    }

    #[test]
    fn anchor_and_verify_round_trip() {
        let path = tmp_path("anchor");
        let _ = fs::remove_file(&path);
        let mut ledger = LocalLedger::open(&path).unwrap();
        let (lct, _) = Lct::new(EntityType::Organization, None);
        ledger.mint(&lct).unwrap();
        let proof = ledger.anchor(lct.id).unwrap();
        assert!(ledger.verify_proof(&proof).unwrap());
        // Mutate the proof's entry_hash — verification should fail
        let mut bad = proof.clone();
        bad.entry_hash = "0".repeat(64);
        assert!(!ledger.verify_proof(&bad).unwrap());
        let _ = fs::remove_file(&path);
    }

    #[test]
    fn empty_file_is_error() {
        let path = tmp_path("empty");
        let _ = fs::remove_file(&path);
        File::create(&path).unwrap();
        let result = LocalLedger::open(&path);
        assert!(result.is_err());
        let _ = fs::remove_file(&path);
    }
}
