// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later

//! In-memory ledger backend.
//!
//! For tests, prototyping, and ephemeral runs. State is lost when the process
//! exits. Not suitable for any deployment that needs persistence.

use super::{
    build_genesis_entry, build_mint_entry, build_status_entry, duplicate, not_found,
    verify_entry_hash, Ledger, LedgerEntry, LedgerEvent, LedgerProof, MintReceipt,
};
use crate::error::Result;
use crate::lct::{Lct, LctStatus};
use chrono::Utc;
use std::collections::HashMap;
use uuid::Uuid;

/// In-memory ledger.
///
/// Maintains an append-only log of [`LedgerEntry`] values plus a `HashMap`
/// for fast LCT lookup. Hash-chained via `prev_hash` for tamper detection
/// (though "tamper" is a low concern when state is in-memory).
#[derive(Debug)]
pub struct InMemoryLedger {
    entries: Vec<LedgerEntry>,
    lcts: HashMap<Uuid, Lct>,
    head_hash: String,
}

impl InMemoryLedger {
    /// Create a new in-memory ledger with a genesis entry.
    pub fn new() -> Self {
        let genesis = build_genesis_entry(Self::BACKEND_KIND)
            .expect("genesis entry construction is infallible");
        let head_hash = genesis.entry_hash.clone();
        Self {
            entries: vec![genesis],
            lcts: HashMap::new(),
            head_hash,
        }
    }

    /// Backend identifier.
    pub const BACKEND_KIND: &'static str = "in-memory";

    /// Iterate over all entries (genesis + mints + status changes).
    pub fn entries(&self) -> &[LedgerEntry] {
        &self.entries
    }
}

impl Default for InMemoryLedger {
    fn default() -> Self {
        Self::new()
    }
}

impl Ledger for InMemoryLedger {
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
        self.head_hash = entry.entry_hash.clone();
        self.lcts.insert(lct.id, lct.clone());
        self.entries.push(entry);
        Ok(receipt)
    }

    fn lookup(&self, id: Uuid) -> Result<Option<Lct>> {
        Ok(self.lcts.get(&id).cloned())
    }

    fn update_status(&mut self, id: Uuid, status: LctStatus) -> Result<LedgerEntry> {
        let lct = self.lcts.get(&id).ok_or_else(|| not_found(id))?;
        let from = lct.status.clone();
        if from == status {
            return Err(crate::error::Web4Error::InvalidInput(format!(
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
        self.head_hash = entry.entry_hash.clone();
        if let Some(stored) = self.lcts.get_mut(&id) {
            stored.status = status;
        }
        self.entries.push(entry.clone());
        Ok(entry)
    }

    fn anchor(&self, id: Uuid) -> Result<LedgerProof> {
        // Find the most recent mint entry for this LCT
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
        // Sanity-check that the entry actually mints the claimed LCT
        let mints_match = matches!(
            &entry.event,
            LedgerEvent::Mint { lct } if lct.id == proof.lct_id
        );
        if !mints_match {
            return Ok(false);
        }
        // Sanity-check that the entry's hash matches its content (tamper detection)
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::lct::EntityType;

    #[test]
    fn genesis_entry_present() {
        let ledger = InMemoryLedger::new();
        assert_eq!(ledger.len(), 1);
        assert!(ledger.is_empty());
        assert!(matches!(
            ledger.entries()[0].event,
            LedgerEvent::Genesis { .. }
        ));
    }

    #[test]
    fn mint_and_lookup() {
        let mut ledger = InMemoryLedger::new();
        let (lct, _) = Lct::new(EntityType::Human, None);
        let receipt = ledger.mint(&lct).unwrap();
        assert_eq!(receipt.lct_id, lct.id);
        assert_eq!(receipt.entry_index, 1);
        assert_eq!(receipt.backend, "in-memory");

        let looked_up = ledger.lookup(lct.id).unwrap();
        assert_eq!(looked_up.as_ref().map(|l| l.id), Some(lct.id));
        assert!(!ledger.is_empty());
    }

    #[test]
    fn duplicate_mint_rejected() {
        let mut ledger = InMemoryLedger::new();
        let (lct, _) = Lct::new(EntityType::Human, None);
        ledger.mint(&lct).unwrap();
        let second = ledger.mint(&lct);
        assert!(second.is_err());
    }

    #[test]
    fn anchor_and_verify() {
        let mut ledger = InMemoryLedger::new();
        let (lct, _) = Lct::new(EntityType::AiSoftware, None);
        ledger.mint(&lct).unwrap();
        let proof = ledger.anchor(lct.id).unwrap();
        assert!(ledger.verify_proof(&proof).unwrap());
    }

    #[test]
    fn verify_rejects_wrong_backend() {
        let mut ledger = InMemoryLedger::new();
        let (lct, _) = Lct::new(EntityType::AiSoftware, None);
        ledger.mint(&lct).unwrap();
        let mut proof = ledger.anchor(lct.id).unwrap();
        proof.backend = "act-cosmos".into();
        assert!(!ledger.verify_proof(&proof).unwrap());
    }

    #[test]
    fn status_change_tracked() {
        let mut ledger = InMemoryLedger::new();
        let (lct, _) = Lct::new(EntityType::Human, None);
        ledger.mint(&lct).unwrap();

        let entry = ledger.update_status(lct.id, LctStatus::Dormant).unwrap();
        assert!(matches!(
            entry.event,
            LedgerEvent::StatusChange {
                from: LctStatus::Active,
                to: LctStatus::Dormant,
                ..
            }
        ));

        let updated = ledger.lookup(lct.id).unwrap().unwrap();
        assert_eq!(updated.status, LctStatus::Dormant);
    }

    #[test]
    fn status_change_unknown_lct() {
        let mut ledger = InMemoryLedger::new();
        let result = ledger.update_status(Uuid::new_v4(), LctStatus::Void);
        assert!(result.is_err());
    }

    #[test]
    fn chain_integrity_via_prev_hash() {
        let mut ledger = InMemoryLedger::new();
        let (lct1, _) = Lct::new(EntityType::Human, None);
        let (lct2, _) = Lct::new(EntityType::AiSoftware, None);
        ledger.mint(&lct1).unwrap();
        ledger.mint(&lct2).unwrap();

        let entries = ledger.entries();
        assert_eq!(entries.len(), 3);
        // Each entry's prev_hash should equal the previous entry's entry_hash
        for window in entries.windows(2) {
            assert_eq!(window[0].entry_hash, window[1].prev_hash);
        }
    }
}
