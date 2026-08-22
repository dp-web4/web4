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
//! - `event` — typed HubEvent
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

use crate::events::HubEvent;
use crate::store::HubStore;

/// Sentinel prev-hash for the Genesis entry: 64 hex zeros.
pub const GENESIS_PREV_HASH: &str = "0000000000000000000000000000000000000000000000000000000000000000";

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct LedgerEntry {
    pub index: u64,
    pub timestamp: DateTime<Utc>,
    pub prev_hash: String,
    pub actor_lct_id: Uuid,
    pub event: HubEvent,
    /// Hex-encoded Ed25519 signature over `signing_payload`.
    pub signature: String,
    /// sha256 hex of the canonical entry (computed with `entry_hash` field cleared).
    pub entry_hash: String,
    /// V2-9 Phase 2: when this entry was committed via the Sovereign
    /// Council propose/sign flow, this references the proposal whose
    /// M-of-N signatures authorized the act. Single-pane audit:
    /// auditors walk the ledger, find entries with `proposal_ref =
    /// Some(id)`, fetch the proposal from the store, and verify the
    /// M holder envelopes against the council's pubkeys.
    ///
    /// `None` for entries committed via the direct /events path (no
    /// council authorization), and for all pre-V2-9-P2 entries
    /// (back-compat via serde default + skip_serializing_if).
    /// Because the field is part of `signing_payload`, an attacker
    /// cannot forge a fake `proposal_ref` onto an existing entry —
    /// the signature wouldn't verify.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub proposal_ref: Option<Uuid>,
}

/// The bytes that get signed: the entry's content with `signature` and
/// `entry_hash` both cleared.
///
/// ## What the determinism actually rests on
///
/// Two things, not one. The struct's serde field order is fixed — that
/// part is local and obvious. The other is **chrono's serde spelling of
/// `timestamp`**: this function writes whatever `DateTime<Utc>`'s
/// `Serialize` impl produces, which is `to_rfc3339_opts(AutoSi, true)` —
/// a `Z` suffix and a *variable-width* fractional part (0, 3, 6, or 9
/// digits, chosen by the value). Nothing in this module states that, and
/// it is load-bearing. Pinned by `ledger_timestamp_wire_spelling_is_pinned`
/// so a chrono bump that changes it fails at upgrade time rather than in
/// `verify-ledger`, where the symptom would read as "the ledger has been
/// tampered with".
///
/// ## Consequence for auditors
///
/// The signed bytes are re-derived from the *parsed* entry, never read
/// from the stored text. Within this implementation that is a safety
/// property, and a deliberate one: re-spelling a persisted timestamp
/// cannot invalidate a chain that is otherwise intact (pinned by
/// `verification_re_derives_so_it_is_spelling_independent`). Across
/// implementations it is a cost — an auditor recomputing these bytes in
/// another language cannot hash the JSON it read; it must first normalise
/// `timestamp` to chrono's `AutoSi`/`Z` form. [`crate::constellation::canonical_timestamp`]
/// is the fixed-width spelling this repo adopted for exactly that reason
/// (attestations, receipts). The ledger has **not** adopted it: doing so
/// changes every entry's signing bytes and every `entry_hash`, i.e. a
/// migration of the live chain, not a code change. Open question, not an
/// oversight.
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
/// and passes the resulting signature to [`HubLedger::append_signed`].
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

/// Append-only hub event ledger.
///
/// Owns hash-chain integrity + signing logic. Delegates byte persistence
/// to a [`HubStore`] — so the ledger works identically against file,
/// SQLite, or future backends.
pub struct HubLedger {
    store: Box<dyn HubStore>,
    entries: Vec<LedgerEntry>,
    head_hash: String,
}

impl std::fmt::Debug for HubLedger {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("HubLedger")
            .field("backend_kind", &self.store.backend_kind())
            .field("entries", &self.entries.len())
            .field("head_hash", &self.head_hash)
            .finish()
    }
}

/// The sealed chain-tail watermark (dp's design, 2026-08-08).
///
/// `verify_chain`'s own caveat names the one thing hash-linking cannot prove:
/// *"removing entries from the tail leaves a chain that verifies."* This is the
/// independently-recorded value it says to compare against — written into the
/// **store** (SQLCipher-encrypted on the sqlite backend) at every append, so the
/// chain and its witness live in different trust boundaries. A tail-trimmed
/// `ledger.jsonl` no longer matches the watermark the vault still holds.
///
/// Semantics are a **monotonic floor**, not an equality:
/// - chain longer than the watermark → fine (the crash window between
///   ledger-append and watermark-stamp lags by design; the next append heals it);
/// - chain shorter, or a different entry at the watermark index → **refused at
///   open** (truncation or rewritten history).
///
/// What it does NOT close, stated so nobody recalls it as closed: a coordinated
/// rollback of chain **and** store together (a whole-filesystem restore). Inside
/// one machine that is undetectable by construction; it is what cross-hub
/// anchoring exists for. This is the local tier of that design, not a substitute.
#[derive(Clone, Debug, serde::Serialize, serde::Deserialize)]
pub struct ChainWatermark {
    /// Number of entries witnessed (chain length at stamp time).
    pub chain_len: u64,
    /// `entry_hash` of the entry at `chain_len - 1`.
    pub head_hash: String,
    /// `entry_hash` of up to two entries before the head — diagnostic depth so a
    /// dispute about the head itself can be localised, per the design ask
    /// ("hash of last couple items").
    #[serde(default)]
    pub prev_hashes: Vec<String>,
    pub stamped_at: DateTime<Utc>,
}

impl HubLedger {
    /// Open a ledger backed by the given store. Loads any existing entries
    /// into memory + restores head_hash. Does NOT write a Genesis entry —
    /// that's the caller's responsibility via [`Self::write_genesis`].
    pub async fn open(store: Box<dyn HubStore>) -> Result<Self> {
        let entries = store.ledger_load_all().await
            .context("loading ledger entries from store")?;

        // Chain-tail check against the sealed watermark. Everything that reads
        // this ledger loads through here, so this is the one choke point where a
        // truncated tail can be caught before anything trusts the chain.
        //
        // The two failure directions are different claims and get different
        // exits: a chain SHORTER than the floor, or a DIFFERENT entry at the
        // floor index, is refuted — refuse. A watermark that cannot be read is
        // undecidable, not refuted — also refuse, but say which fired. Both are
        // overridable with HUB_ALLOW_CHAIN_ROLLBACK=1 (mirroring
        // HUB_ALLOW_LAW_MISMATCH), which exists for operator forensics, not for
        // production.
        let override_on = std::env::var("HUB_ALLOW_CHAIN_ROLLBACK").ok().as_deref() == Some("1");
        match store.read_chain_watermark().await {
            Ok(None) => {} // no claim yet (pre-watermark hub); first append stamps it
            Ok(Some(wm)) => {
                let n = wm.chain_len as usize;
                let verdict: Option<String> = if entries.len() < n {
                    Some(format!(
                        "chain has {} entries but the sealed watermark witnessed {} \
                         (head {}) — the tail has been truncated or the chain rolled back",
                        entries.len(), n, &wm.head_hash[..16.min(wm.head_hash.len())],
                    ))
                } else if n > 0 && entries[n - 1].entry_hash != wm.head_hash {
                    Some(format!(
                        "the entry at watermark index {} is not the entry the sealed \
                         watermark witnessed ({} != {}) — divergent history",
                        n - 1,
                        &entries[n - 1].entry_hash[..16],
                        &wm.head_hash[..16.min(wm.head_hash.len())],
                    ))
                } else {
                    None
                };
                if let Some(msg) = verdict {
                    if override_on {
                        tracing::warn!("CHAIN WATERMARK OVERRIDE (HUB_ALLOW_CHAIN_ROLLBACK=1): {msg}");
                    } else {
                        return Err(anyhow!("chain watermark check REFUTED: {msg}"));
                    }
                }
            }
            Err(e) => {
                let msg = format!("chain watermark UNDECIDABLE (store read failed): {e:#}");
                if override_on {
                    tracing::warn!("{msg} — proceeding under HUB_ALLOW_CHAIN_ROLLBACK=1");
                } else {
                    return Err(anyhow!(msg));
                }
            }
        }

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
    pub fn store(&self) -> &dyn HubStore { self.store.as_ref() }
    pub fn store_mut(&mut self) -> &mut dyn HubStore { self.store.as_mut() }

    /// Write the Genesis entry. Errors if the ledger is not empty.
    /// Convenience wrapper for callers holding a local keypair.
    pub async fn write_genesis(
        &mut self,
        sovereign_lct_id: Uuid,
        sovereign_keypair: &KeyPair,
        hub_name: String,
        charter_hash: String,
    ) -> Result<&LedgerEntry> {
        let (unsigned, _) = self.build_genesis(sovereign_lct_id, hub_name, charter_hash)?;
        let sig = sovereign_keypair.sign(&unsigned.signing_bytes);
        self.append_signed(unsigned, SignatureBytes::from_bytes(sig.bytes)).await
    }

    /// Build the unsigned Genesis entry. Errors if the ledger is not empty.
    /// Returns the unsigned entry + the canonical timestamp it uses (so a
    /// Hestia-mode init can include the timestamp in the sign-request).
    pub fn build_genesis(
        &self,
        sovereign_lct_id: Uuid,
        hub_name: String,
        charter_hash: String,
    ) -> Result<(UnsignedEntry, DateTime<Utc>)> {
        if !self.entries.is_empty() {
            return Err(anyhow!("ledger already has entries; Genesis would be illegal"));
        }
        let now = Utc::now();
        let event = HubEvent::Genesis {
            hub_name,
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
    pub async fn append(
        &mut self,
        actor_lct_id: Uuid,
        actor_keypair: &KeyPair,
        event: HubEvent,
    ) -> Result<&LedgerEntry> {
        if self.entries.is_empty() {
            return Err(anyhow!("ledger has no Genesis entry; call write_genesis first"));
        }
        let unsigned = self.build_entry(actor_lct_id, event, Utc::now())?;
        let sig = actor_keypair.sign(&unsigned.signing_bytes);
        self.append_signed(unsigned, SignatureBytes::from_bytes(sig.bytes)).await
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
        event: HubEvent,
        timestamp: DateTime<Utc>,
    ) -> Result<UnsignedEntry> {
        self.build_entry_with_proposal_ref(actor_lct_id, event, timestamp, None)
    }

    /// V2-9 Phase 2: variant of [`Self::build_entry`] that pins a
    /// council proposal reference into the entry. Used by the
    /// council propose/sign commit path so single-pane auditors can
    /// link the ledger entry to the proposal record holding the
    /// M-of-N holder signatures. `proposal_ref` is part of
    /// `signing_payload` so it can't be forged after the fact.
    pub fn build_entry_with_proposal_ref(
        &self,
        actor_lct_id: Uuid,
        event: HubEvent,
        timestamp: DateTime<Utc>,
        proposal_ref: Option<Uuid>,
    ) -> Result<UnsignedEntry> {
        let entry = LedgerEntry {
            index: self.entries.len() as u64,
            timestamp,
            prev_hash: self.head_hash.clone(),
            actor_lct_id,
            event,
            signature: String::new(),
            entry_hash: String::new(),
            proposal_ref,
        };
        let signing_bytes = signing_payload(&entry)?;
        Ok(UnsignedEntry { entry, signing_bytes })
    }

    /// Commit a signed entry: fills in the signature + computes
    /// entry_hash + persists to the store + advances head_hash.
    /// Caller is responsible for producing a valid signature over
    /// `unsigned.signing_bytes`.
    pub async fn append_signed(
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

        self.store.ledger_append(&unsigned.entry).await
            .context("persisting ledger entry via store")?;

        self.head_hash = unsigned.entry.entry_hash.clone();
        self.entries.push(unsigned.entry);

        // Stamp the sealed watermark AFTER the entry is durably committed —
        // this order makes the crash window lag in the benign direction (floor
        // behind chain), which open() tolerates. A stamp failure is warned, not
        // returned: the entry IS witnessed, and erroring here would tell the
        // caller their act failed when the ledger says otherwise.
        let wm = ChainWatermark {
            chain_len: self.entries.len() as u64,
            head_hash: self.head_hash.clone(),
            prev_hashes: self.entries.iter().rev().skip(1).take(2)
                .map(|e| e.entry_hash.clone()).collect(),
            stamped_at: Utc::now(),
        };
        if let Err(e) = self.store.write_chain_watermark(&wm).await {
            tracing::warn!(
                "entry {} committed but the chain watermark stamp FAILED: {e:#} — \
                 the sealed floor now lags the chain until the next successful append",
                self.entries.len() - 1,
            );
        }
        Ok(self.entries.last().unwrap())
    }


    /// Verify the entire chain.
    /// `lct_lookup` maps an actor LCT id to its Lct (for signature verification).
    /// Returns Ok(()) if every entry's signature, hash, and prev-hash check out.
    /// Verify every entry: index, prev_hash linkage, entry_hash, signature.
    ///
    /// ## What `Ok(())` proves — and the one thing it does not
    ///
    /// It proves the entries **present** are internally consistent and each was
    /// signed by the LCT `lct_lookup` resolves for it. It does **not** prove
    /// they are *all* the entries. The chain is anchored at its origin and open
    /// at its head: entry 0's `prev_hash` is pinned to [`GENESIS_PREV_HASH`], so
    /// removing entries from the front, from the middle, or reordering them all
    /// fail here — but lopping entries off the **tail** leaves every surviving
    /// index, link, hash and signature correct, and this function returns
    /// `Ok(())` over a history that has had acts removed.
    ///
    /// That is a property of forward hash chains, not a defect in this
    /// implementation, and closing it needs an anchor *outside* the store. The
    /// material for one is already published unauthenticated: `query_hub` and
    /// `GET /v1/hubs/{id}/state` both carry `head_hash` and the entry count, so
    /// a peer that records them can detect a head that moved backwards. An
    /// auditor relying on this function alone cannot.
    ///
    /// ## One guard per check
    ///
    /// The four checks below used to share two tamper tests between them, both
    /// of which broke a hash *and* a signature at once. Neutering the
    /// `entry_hash` comparison left the suite green; so did neutering
    /// `verify_signature` outright. Each check now has a test that fails when
    /// that check — and only that check — is removed, verified by mutation:
    ///
    /// | check | the tamper only it catches |
    /// |---|---|
    /// | `index` | a deleted middle entry, a swap, a dropped Genesis |
    /// | `prev_hash` | a forked entry grafted at its own index |
    /// | `entry_hash` | a rewritten head hash (signature still valid) |
    /// | `signature` | a forged signature with the hash recomputed to match |
    ///
    /// Plus `a_truncated_tail_still_verifies_because_the_chain_only_proves_consistency`,
    /// which asserts `Ok` deliberately so the limit above is pinned rather than
    /// rediscovered during an incident.
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
    use crate::hub::HubPaths;
    use crate::identity::IdentityFile;
    use crate::store::FileBackend;
    use tempfile::tempdir;
    use web4_core::lct::EntityType;

    fn fresh_sovereign() -> IdentityFile {
        IdentityFile::generate(EntityType::Human)
    }

    fn fresh_store(tmp: &tempfile::TempDir) -> (Box<dyn HubStore>, std::path::PathBuf) {
        let hub_dir = tmp.path().join("chap");
        std::fs::create_dir_all(&hub_dir).unwrap();
        let paths = HubPaths::new(hub_dir.clone());
        let ledger_path = paths.ledger();
        (Box::new(FileBackend::new(paths)), ledger_path)
    }

    fn reopen_file_backend(tmp: &tempfile::TempDir) -> Box<dyn HubStore> {
        let hub_dir = tmp.path().join("chap");
        Box::new(FileBackend::new(HubPaths::new(hub_dir)))
    }

    #[tokio::test]
    async fn open_creates_empty_file() {
        let tmp = tempdir().unwrap();
        let (store, _) = fresh_store(&tmp);
        let ledger = HubLedger::open(store).await.unwrap();
        assert!(ledger.is_empty());
        assert_eq!(ledger.head_hash(), GENESIS_PREV_HASH);
    }

    #[tokio::test]
    async fn genesis_then_one_event_signs_and_verifies() {
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();
        let keypair = sovereign.keypair().unwrap();

        let (store, _) = fresh_store(&tmp);
        let mut ledger = HubLedger::open(store).await.unwrap();
        ledger.write_genesis(
            sovereign.lct.id,
            &keypair,
            "Test Chapter".into(),
            "sha256:cafebabe".into(),
        ).await.unwrap();

        let member_id = Uuid::new_v4();
        ledger.append(
            sovereign.lct.id,
            &keypair,
            HubEvent::MemberAdded {
                member_lct_id: member_id,
                added_by: sovereign.lct.id,
                member_name: Some("Alice".into()),
                member_pubkey_hex: None,
                anchor_level: None,
                trust_ceiling: None,
            },
        ).await.unwrap();

        assert_eq!(ledger.len(), 2);

        let lookup_map = build_lookup([sovereign.lct.clone()]);
        ledger.verify_chain(|id| lookup_map.get(&id).cloned()).unwrap();
    }

    #[tokio::test]
    async fn reopen_replays_chain_integrity() {
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();
        let keypair = sovereign.keypair().unwrap();

        {
            let (store, _) = fresh_store(&tmp);
            let mut ledger = HubLedger::open(store).await.unwrap();
            ledger.write_genesis(
                sovereign.lct.id, &keypair,
                "X".into(), "sha256:0".into(),
            ).await.unwrap();
            for _ in 0..3 {
                ledger.append(
                    sovereign.lct.id, &keypair,
                    HubEvent::MemberAdded {
                        member_lct_id: Uuid::new_v4(),
                        added_by: sovereign.lct.id,
                        member_name: None,
                        member_pubkey_hex: None,
                        anchor_level: None,
                        trust_ceiling: None,
                    },
                ).await.unwrap();
            }
        }

        // Re-open a fresh store pointing at the same dir and verify.
        let reopened = HubLedger::open(reopen_file_backend(&tmp)).await.unwrap();
        assert_eq!(reopened.len(), 4);
        let lookup_map = build_lookup([sovereign.lct.clone()]);
        reopened.verify_chain(|id| lookup_map.get(&id).cloned()).unwrap();
    }

    #[tokio::test]
    async fn tampered_event_fails_verification() {
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();
        let keypair = sovereign.keypair().unwrap();

        let (store, ledger_path) = fresh_store(&tmp);
        let mut ledger = HubLedger::open(store).await.unwrap();
        ledger.write_genesis(
            sovereign.lct.id, &keypair,
            "X".into(), "sha256:0".into(),
        ).await.unwrap();
        ledger.append(
            sovereign.lct.id, &keypair,
            HubEvent::MemberAdded {
                member_lct_id: Uuid::new_v4(),
                added_by: sovereign.lct.id,
                member_name: Some("Original".into()),
                member_pubkey_hex: None,
                anchor_level: None,
                trust_ceiling: None,
            },
        ).await.unwrap();
        drop(ledger);

        // Tamper directly at the file-backed layer: this test is
        // file-backend-specific (it knows where bytes live). SqliteBackend
        // gets its own tamper tests below.
        let content = std::fs::read_to_string(&ledger_path).unwrap();
        let lines: Vec<&str> = content.lines().collect();
        let tampered_line = lines[1].replace("Original", "Tampered");
        let new_content = format!("{}\n{}\n", lines[0], tampered_line);
        std::fs::write(&ledger_path, new_content).unwrap();

        // Re-open: hash recompute should now mismatch
        let reopened = HubLedger::open(reopen_file_backend(&tmp)).await.unwrap();
        let lookup_map = build_lookup([sovereign.lct.clone()]);
        let result = reopened.verify_chain(|id| lookup_map.get(&id).cloned());
        assert!(result.is_err(), "tampered entry must fail verification");
        let err = format!("{:?}", result.unwrap_err());
        // Asserted as the entry_hash check exactly, not `entry_hash ||
        // signature`. The disjunction this replaces was vacuous for the hash
        // check: neutering `entry.entry_hash != recomputed` left the whole
        // ledger suite green, because a payload tamper also breaks the
        // signature and the `||` accepted whichever check survived. Measured
        // by mutation, 2026-07-30.
        assert!(err.contains("entry_hash mismatch"),
            "expected the entry_hash check, got: {}", err);
    }

    /// **The one attack `entry_hash` alone catches.**
    ///
    /// Rewriting an entry's *payload* breaks the hash and the signature both,
    /// so it cannot show that the hash check works. Rewriting the stored
    /// `entry_hash` field of the **last** entry can: the signature covers the
    /// entry with `entry_hash` cleared, so it still verifies; the index is
    /// untouched; and being last, no successor's `prev_hash` points at it.
    /// Only the recomputation catches it.
    ///
    /// It matters because `entry_hash` is what the hub publishes as its head
    /// (`query_hub`, `GET /v1/hubs/{id}/state`). An unchecked head field is a
    /// forgeable anchor — and the anchor is the only detector for the one
    /// tamper class the chain itself cannot see (see the truncation test).
    #[tokio::test]
    async fn a_rewritten_head_entry_hash_is_caught_only_by_the_hash_check() {
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();
        let (path, lines) = chain_of(&tmp, &sovereign, 2).await;

        let last = lines.last().unwrap();
        let entry: LedgerEntry = serde_json::from_str(last).unwrap();
        let forged = format!("{:0>64}", "beef");
        assert_ne!(entry.entry_hash, forged);
        let tampered = last.replace(&entry.entry_hash, &forged);
        assert_ne!(&tampered, last, "the tamper must actually land");

        let mut rewritten = lines.clone();
        *rewritten.last_mut().unwrap() = tampered;
        let err = verify_after_rewrite(&tmp, &sovereign, &path, &rewritten).await
            .expect_err("a forged head hash must not verify");
        let err = format!("{err:?}");
        assert!(err.contains("entry_hash mismatch"),
            "the hash recomputation must be what catches it, got: {err}");
    }

    /// **The one attack the signature check alone catches — and the check that
    /// had no negative test at all until this one.**
    ///
    /// Measured 2026-07-30: replacing `actor.verify_signature(..)` with a
    /// no-op left every test in this module green. Every tamper the suite
    /// induced broke a hash first, so the check that makes the ledger
    /// *unforgeable* rather than merely *self-consistent* was never exercised.
    ///
    /// `entry_hash` covers the signature field, so a forged signature normally
    /// trips the hash check on the way past. A forger who recomputes the hash
    /// afterwards — which costs nothing, it is a plain sha256 over public
    /// bytes — produces an entry that is consistent in every respect except
    /// the one that requires a key. That is the entry this builds.
    #[tokio::test]
    async fn a_forged_signature_with_a_recomputed_hash_is_caught_only_by_the_signature_check() {
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();
        let (path, lines) = chain_of(&tmp, &sovereign, 2).await;

        let mut entry: LedgerEntry = serde_json::from_str(lines.last().unwrap()).unwrap();
        // Flip one hex digit of the signature, keeping it decodable and 64 bytes
        // so the failure is verification and not a parse error.
        let first = entry.signature.chars().next().unwrap();
        let flipped = if first == '0' { '1' } else { '0' };
        entry.signature = format!("{flipped}{}", &entry.signature[1..]);
        // ...then repair the hash the way a forger would.
        entry.entry_hash = compute_entry_hash(&entry).unwrap();

        let mut rewritten = lines.clone();
        *rewritten.last_mut().unwrap() = serde_json::to_string(&entry).unwrap();
        assert_ne!(rewritten.last(), lines.last(), "the forgery must actually land");

        let err = verify_after_rewrite(&tmp, &sovereign, &path, &rewritten).await
            .expect_err("a forged signature must not verify");
        let err = format!("{err:?}");
        assert!(err.contains("signature verification failed"),
            "the signature check must be what catches it, got: {err}");
    }

    /// Build Genesis + `n` MemberAdded entries on the file backend and hand
    /// back the on-disk lines. The tamper tests below each rewrite this file
    /// a different way — one structural attack per test, so a passing test
    /// names exactly which check caught it.
    async fn chain_of(
        tmp: &tempfile::TempDir,
        sovereign: &IdentityFile,
        n: usize,
    ) -> (std::path::PathBuf, Vec<String>) {
        let keypair = sovereign.keypair().unwrap();
        let (store, ledger_path) = fresh_store(tmp);
        let mut ledger = HubLedger::open(store).await.unwrap();
        ledger.write_genesis(
            sovereign.lct.id, &keypair,
            "X".into(), "sha256:0".into(),
        ).await.unwrap();
        for i in 0..n {
            ledger.append(
                sovereign.lct.id, &keypair,
                HubEvent::MemberAdded {
                    member_lct_id: Uuid::new_v4(),
                    added_by: sovereign.lct.id,
                    member_name: Some(format!("m{i}")),
                    member_pubkey_hex: None,
                    anchor_level: None,
                    trust_ceiling: None,
                },
            ).await.unwrap();
        }
        drop(ledger);
        let lines = std::fs::read_to_string(&ledger_path).unwrap()
            .lines().map(str::to_string).collect();
        (ledger_path, lines)
    }

    async fn verify_after_rewrite(
        tmp: &tempfile::TempDir,
        sovereign: &IdentityFile,
        path: &std::path::Path,
        lines: &[String],
    ) -> Result<()> {
        let mut body = lines.join("\n");
        if !body.is_empty() { body.push('\n'); }
        std::fs::write(path, body).unwrap();
        // Stand the chain-tail watermark down: this helper exists to exercise
        // `verify_chain`'s per-entry checks in isolation, and the watermark now
        // front-runs it at open() for any rewrite that moves the head. Deleting
        // the plaintext sibling file is also exactly what the File-tier attacker
        // these rewrites simulate would do; the watermark's own coverage is
        // asserted by the dedicated tests above, not here. `let _` because some
        // callers have already deleted it to make the same point explicitly.
        let _ = std::fs::remove_file(tmp.path().join("chap/chain-watermark.json"));
        let reopened = HubLedger::open(reopen_file_backend(tmp)).await.unwrap();
        let lookup = build_lookup([sovereign.lct.clone()]);
        reopened.verify_chain(|id| lookup.get(&id).cloned())
    }

    /// **The chain's limit, pinned as behaviour rather than left to be
    /// discovered during an incident.**
    ///
    /// A forward hash chain proves that the entries present are internally
    /// consistent. It cannot prove they are *all* the entries: lopping entries
    /// off the tail leaves every remaining prev_hash, entry_hash, index and
    /// signature correct, so `verify_chain` returns `Ok` and `hub verify-ledger`
    /// prints "Ledger verified." over a chain that has had history removed.
    /// Detecting that requires an anchor outside the file — the head hash
    /// recorded independently. `query_hub` and `GET /v1/hubs/{id}/state`
    /// publish `head_hash` + `last_ledger_index` unauthenticated precisely so
    /// a peer can hold one.
    ///
    /// This test asserts `Ok` deliberately. If someone later teaches the
    /// verifier to detect truncation, this test fails and points at the doc
    /// comment that has to change with it.
    #[tokio::test]
    async fn a_truncated_tail_still_verifies_because_the_chain_only_proves_consistency() {
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();
        let (path, lines) = chain_of(&tmp, &sovereign, 3).await;
        assert_eq!(lines.len(), 4, "genesis + 3");
        let head_before = HubLedger::open(reopen_file_backend(&tmp)).await.unwrap()
            .head_hash().to_string();

        // Drop the last two entries. Nothing else is touched.
        //
        // NEW (chain-tail watermark): open() now refuses this, because the
        // sealed floor still witnesses 4 entries. Assert the refusal FIRST —
        // this is the hole this test used to document, closing.
        {
            let mut body = lines[..2].join("\n"); body.push('\n');
            std::fs::write(&path, body).unwrap();
            let err = HubLedger::open(reopen_file_backend(&tmp)).await
                .err().expect("a truncated tail must now be refused at open");
            assert!(format!("{err:#}").contains("watermark"));
        }

        // The ORIGINAL lesson still holds one layer down, and stays pinned: the
        // chain ALONE cannot see truncation. On the File backend the watermark
        // is a plaintext sibling file, so an attacker who knows about it deletes
        // it — read_chain_watermark then returns None ("no claim") and the
        // guard stands down. That is the documented File-tier limit; on the
        // SQLCipher backend the same deletion needs the store key.
        std::fs::remove_file(tmp.path().join("chap/chain-watermark.json")).unwrap();
        let result = verify_after_rewrite(&tmp, &sovereign, &path, &lines[..2]).await;
        assert!(result.is_ok(),
            "with the watermark gone, the chain alone is still blind; got {:?}", result.err());

        // The head the hub publishes moves with the truncation — which is what
        // makes an externally-recorded head a sufficient detector for the case
        // the chain cannot see on its own.
        let reopened = HubLedger::open(reopen_file_backend(&tmp)).await.unwrap();
        assert_eq!(reopened.len(), 2);
        assert_ne!(reopened.head_hash(), head_before,
            "the published head must change, or an external anchor would not detect this either");
    }

    /// Removing an entry from the *middle* is caught — by the index check,
    /// not the hash chain. Worth its own test because it is the one structural
    /// attack whose detector is the cheapest check in the function, and a
    /// refactor that dropped the index check would still pass every other
    /// tamper test in this module.
    #[tokio::test]
    async fn a_deleted_middle_entry_fails_the_index_check() {
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();
        let (path, lines) = chain_of(&tmp, &sovereign, 3).await;

        let kept: Vec<String> = [&lines[0], &lines[1], &lines[3]]
            .into_iter().cloned().collect();
        let err = verify_after_rewrite(&tmp, &sovereign, &path, &kept).await
            .expect_err("a hole in the middle must not verify");
        let err = format!("{err:?}");
        assert!(err.contains("index field"), "expected the index check, got: {err}");
    }

    /// Reordering two entries in place. Both are genuine signed entries, so
    /// only the position-dependent checks can catch it — and the one that
    /// actually fires is the index check, asserted exactly rather than as a
    /// disjunction with prev_hash. A disjunction here would pass whichever
    /// check survived a refactor, which is the same vacuity `expect_err`
    /// avoids one level up.
    #[tokio::test]
    async fn two_entries_swapped_in_place_fail_the_index_check() {
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();
        let (path, lines) = chain_of(&tmp, &sovereign, 3).await;

        let swapped: Vec<String> = [&lines[0], &lines[2], &lines[1], &lines[3]]
            .into_iter().cloned().collect();
        let err = verify_after_rewrite(&tmp, &sovereign, &path, &swapped).await
            .expect_err("a reordered chain must not verify");
        let err = format!("{err:?}");
        assert!(err.contains("has index field 2; expected 1"),
            "expected the index check at position 1, got: {err}");
    }

    /// Truncating from the *front* — dropping Genesis — is caught, unlike
    /// truncating from the back. Measured: what catches it is the **index**
    /// check (the survivors' `index` fields start at 1), not the Genesis
    /// anchor. Recorded that way because the anchor's real job is different:
    /// `prev_hash == GENESIS_PREV_HASH` at position 0 is what stops an
    /// attacker *grafting a new origin* on, not what notices the old one is
    /// gone. The graft is covered separately below.
    #[tokio::test]
    async fn dropping_genesis_fails_the_index_check_not_the_genesis_anchor() {
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();
        let (path, lines) = chain_of(&tmp, &sovereign, 3).await;

        let err = verify_after_rewrite(&tmp, &sovereign, &path, &lines[1..]).await
            .expect_err("a chain with no Genesis must not verify");
        let err = format!("{err:?}");
        assert!(err.contains("entry 0 has index field 1"),
            "expected the index check at position 0, got: {err}");
    }

    /// **The one attack `prev_hash` alone catches.**
    ///
    /// Every other structural tamper in this module is caught by the index
    /// check, so nothing here exercised the linkage on its own — a refactor
    /// that deleted the prev_hash comparison would have kept the whole suite
    /// green. This induces the case it exists for: two chains from the same
    /// Genesis, same signer, and an entry from the second grafted onto the
    /// first *at its correct index*. Index matches, `entry_hash` recomputes,
    /// the signature is genuine — the graft is only visible as a broken link.
    ///
    /// This is not hypothetical for a hub whose sovereign signer can be driven
    /// twice: it is what a rollback-and-replay of the store produces.
    #[tokio::test]
    async fn a_forked_entry_grafted_at_its_own_index_fails_only_on_prev_hash() {
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();

        // Chain A: G, a1, a2.
        let (path, chain_a) = chain_of(&tmp, &sovereign, 2).await;
        assert_eq!(chain_a.len(), 3);

        // Chain B: rewind to Genesis, then append a *different* b1, b2 with the
        // same key. b2.index == 2 and b2.prev_hash == hash(b1).
        let chain_b = {
            let mut body = chain_a[0].clone();
            body.push('\n');
            std::fs::write(&path, body).unwrap();
            // This test rewinds the FILE to Genesis to forge a fork — exactly
            // the rollback the watermark now refuses at open(). Stand it down so
            // the test can still exercise the prev_hash graft check it predates;
            // the rollback itself is covered by the watermark tests.
            let _ = std::fs::remove_file(tmp.path().join("chap/chain-watermark.json"));
            let keypair = sovereign.keypair().unwrap();
            let mut ledger = HubLedger::open(reopen_file_backend(&tmp)).await.unwrap();
            for i in 0..2 {
                ledger.append(
                    sovereign.lct.id, &keypair,
                    HubEvent::MemberAdded {
                        member_lct_id: Uuid::new_v4(),
                        added_by: sovereign.lct.id,
                        member_name: Some(format!("fork{i}")),
                        member_pubkey_hex: None,
                        anchor_level: None,
                        trust_ceiling: None,
                    },
                ).await.unwrap();
            }
            drop(ledger);
            std::fs::read_to_string(&path).unwrap()
                .lines().map(str::to_string).collect::<Vec<_>>()
        };
        assert_ne!(chain_a[2], chain_b[2], "the two forks must actually differ");

        let grafted: Vec<String> = vec![
            chain_a[0].clone(), chain_a[1].clone(), chain_b[2].clone(),
        ];
        let err = verify_after_rewrite(&tmp, &sovereign, &path, &grafted).await
            .expect_err("a grafted fork must not verify");
        let err = format!("{err:?}");
        assert!(err.contains("prev_hash mismatch"),
            "prev_hash must be what catches a graft, got: {err}");
    }

    /// The file-backend tamper test above states its own gap: "SqliteBackend
    /// would need its own tamper test." SQLite is what the live fleet chapter
    /// actually runs on, and its ledger is one table — `DELETE FROM
    /// ledger_entries WHERE idx >= ?` is a shorter attack than rewriting a
    /// JSONL file. Both classes are induced here against the real backend.
    #[tokio::test]
    async fn the_sqlite_backend_catches_a_tampered_entry_and_now_a_truncated_tail_too() {
        use crate::store::SqliteBackend;
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();
        let keypair = sovereign.keypair().unwrap();
        let db_path = tmp.path().join("hub.db");

        {
            let store = Box::new(SqliteBackend::open(&db_path, None).unwrap());
            let mut ledger = HubLedger::open(store).await.unwrap();
            ledger.write_genesis(
                sovereign.lct.id, &keypair, "X".into(), "sha256:0".into(),
            ).await.unwrap();
            for i in 0..3 {
                ledger.append(
                    sovereign.lct.id, &keypair,
                    HubEvent::MemberAdded {
                        member_lct_id: Uuid::new_v4(),
                        added_by: sovereign.lct.id,
                        member_name: Some(format!("m{i}")),
                        member_pubkey_hex: None,
                        anchor_level: None,
                        trust_ceiling: None,
                    },
                ).await.unwrap();
            }
        }
        let lookup = build_lookup([sovereign.lct.clone()]);
        let reopen = |p: &std::path::Path| {
            Box::new(SqliteBackend::open(p, None).unwrap()) as Box<dyn HubStore>
        };

        // Baseline: untampered, verifies. Without this the two assertions
        // below could both be explained by a broken fixture.
        HubLedger::open(reopen(&db_path)).await.unwrap()
            .verify_chain(|id| lookup.get(&id).cloned())
            .expect("the untampered sqlite chain verifies");

        // (a) Edit an entry's payload in place — caught by the entry hash.
        {
            let conn = rusqlite::Connection::open(&db_path).unwrap();
            let n = conn.execute(
                "UPDATE ledger_entries SET entry_json = replace(entry_json, 'm1', 'HACKED') \
                 WHERE idx = 2", [],
            ).unwrap();
            assert_eq!(n, 1, "the tamper must actually land or the assertion is vacuous");
        }
        let err = format!("{:?}", HubLedger::open(reopen(&db_path)).await.unwrap()
            .verify_chain(|id| lookup.get(&id).cloned())
            .expect_err("a tampered sqlite entry must not verify"));
        assert!(err.contains("entry_hash mismatch"),
            "expected the entry_hash check, got: {err}");

        // (b) Truncate the tail — one DELETE. NEW: the sealed watermark row in
        // `metadata` survives the DELETE, so open() now refuses. On a keyed
        // (SQLCipher) store this is the trust boundary doing its work: erasing
        // the watermark too requires the store key, and holding the key is
        // Sovereign-equivalent compromise.
        {
            let conn = rusqlite::Connection::open(&db_path).unwrap();
            let n = conn.execute("DELETE FROM ledger_entries WHERE idx >= 2", []).unwrap();
            assert_eq!(n, 2, "the truncation must actually land");
        }
        let err = HubLedger::open(reopen(&db_path)).await
            .err().expect("sqlite truncation must now be refused at open");
        assert!(format!("{err:#}").contains("watermark"));

        // And the ORIGINAL lesson, preserved: erase the watermark row as well
        // (attacker WITH the key, or this test's keyless fixture) and the chain
        // alone is still blind — which is what external anchoring is for.
        {
            let conn = rusqlite::Connection::open(&db_path).unwrap();
            conn.execute("DELETE FROM metadata WHERE key = 'chain_watermark'", []).unwrap();
        }
        let ledger = HubLedger::open(reopen(&db_path)).await.unwrap();
        assert_eq!(ledger.len(), 2);
        ledger.verify_chain(|id| lookup.get(&id).cloned())
            .expect("a truncated sqlite tail re-verifies — the chain cannot see removal");
    }

    #[tokio::test]
    async fn genesis_after_existing_entries_errors() {
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();
        let keypair = sovereign.keypair().unwrap();

        let (store, _) = fresh_store(&tmp);
        let mut ledger = HubLedger::open(store).await.unwrap();
        ledger.write_genesis(
            sovereign.lct.id, &keypair,
            "X".into(), "sha256:0".into(),
        ).await.unwrap();

        let result = ledger.write_genesis(
            sovereign.lct.id, &keypair,
            "Y".into(), "sha256:1".into(),
        ).await;
        assert!(result.is_err());
    }

    #[tokio::test]
    async fn split_api_simulates_remote_signing() {
        // The split build_entry / append_signed API enables Hestia-mode
        // where the actor's keypair lives in a remote vault. Simulate it
        // here: we hold the keypair locally, but pretend we're a "remote
        // signer" that only sees the signing bytes the ledger hands us.
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();
        let kp = sovereign.keypair().unwrap();

        let (store, _) = fresh_store(&tmp);
        let mut ledger = HubLedger::open(store).await.unwrap();

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
        ledger.append_signed(unsigned_genesis, sig).await.unwrap();

        // Member added via the split path
        let unsigned_member = ledger.build_entry(
            sovereign.lct.id,
            HubEvent::MemberAdded {
                member_lct_id: Uuid::new_v4(),
                added_by: sovereign.lct.id,
                member_name: Some("Alice".into()),
                member_pubkey_hex: None,
                anchor_level: None,
                trust_ceiling: None,
            },
            Utc::now(),
        ).unwrap();
        let bytes_to_sign = unsigned_member.signing_bytes.clone();
        let sig = SignatureBytes::from_bytes(kp.sign(&bytes_to_sign).bytes);
        ledger.append_signed(unsigned_member, sig).await.unwrap();

        assert_eq!(ledger.len(), 2);

        // Chain verifies
        let lookup_map = build_lookup([sovereign.lct.clone()]);
        ledger.verify_chain(|id| lookup_map.get(&id).cloned()).unwrap();
    }

    #[tokio::test]
    async fn append_signed_rejects_stale_unsigned_entry() {
        // If a parallel append landed between build_entry and append_signed,
        // the commit must fail rather than corrupt the chain.
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();
        let kp = sovereign.keypair().unwrap();

        let (store, _) = fresh_store(&tmp);
        let mut ledger = HubLedger::open(store).await.unwrap();
        ledger.write_genesis(
            sovereign.lct.id, &kp,
            "X".into(), "0".repeat(64),
        ).await.unwrap();

        // Build entry A (gets index=1, prev_hash=genesis_hash)
        let unsigned_a = ledger.build_entry(
            sovereign.lct.id,
            HubEvent::MemberAdded { member_lct_id: Uuid::new_v4(), added_by: sovereign.lct.id, member_name: None, member_pubkey_hex: None,
            anchor_level: None,
            trust_ceiling: None,
        },
            Utc::now(),
        ).unwrap();

        // In parallel, entry B lands first (also index=1 at build time,
        // but commits before A and becomes the actual index=1)
        ledger.append(
            sovereign.lct.id, &kp,
            HubEvent::MemberAdded { member_lct_id: Uuid::new_v4(), added_by: sovereign.lct.id, member_name: Some("B".into()), member_pubkey_hex: None,
            anchor_level: None,
            trust_ceiling: None,
        },
        ).await.unwrap();

        // Now A tries to commit; should fail because the ledger advanced
        let sig = SignatureBytes::from_bytes(kp.sign(&unsigned_a.signing_bytes).bytes);
        let result = ledger.append_signed(unsigned_a, sig).await;
        assert!(result.is_err(), "stale unsigned must be rejected, not silently overwrite");
        let err = format!("{:?}", result.unwrap_err());
        assert!(err.contains("ledger advanced") || err.contains("head changed"),
            "expected stale-detection error, got: {}", err);
    }

    #[tokio::test]
    async fn append_before_genesis_errors() {
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();
        let keypair = sovereign.keypair().unwrap();

        let (store, _) = fresh_store(&tmp);
        let mut ledger = HubLedger::open(store).await.unwrap();
        let result = ledger.append(
            sovereign.lct.id, &keypair,
            HubEvent::MemberAdded {
                member_lct_id: Uuid::new_v4(),
                added_by: sovereign.lct.id,
                member_name: None,
                member_pubkey_hex: None,
                anchor_level: None,
                trust_ceiling: None,
            },
        ).await;
        assert!(result.is_err());
    }

    /// V2-9 Phase 2 back-compat: a ledger entry serialized BEFORE the
    /// `proposal_ref` field existed must still parse + verify cleanly.
    /// We simulate this by:
    /// 1. Build + commit an entry with proposal_ref=None (the normal
    ///    path; output JSON has no `proposal_ref` key thanks to
    ///    skip_serializing_if).
    /// 2. Round-trip it through serde and confirm proposal_ref is
    ///    still None (deserialized via serde default).
    /// 3. Construct a hand-written JSON string with NO proposal_ref
    ///    key, deserialize, confirm it parses + has None.
    /// 4. Verify the chain (signature still validates).
    #[tokio::test]
    async fn proposal_ref_is_back_compat_via_serde_default() {
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();
        let keypair = sovereign.keypair().unwrap();
        let (store, _) = fresh_store(&tmp);
        let mut ledger = HubLedger::open(store).await.unwrap();
        ledger.write_genesis(
            sovereign.lct.id, &keypair,
            "Test".into(), "sha256:0".into(),
        ).await.unwrap();
        // Append a normal entry (proposal_ref = None by default).
        let entry = ledger.append(
            sovereign.lct.id, &keypair,
            HubEvent::MemberAdded {
                member_lct_id: Uuid::new_v4(),
                added_by: sovereign.lct.id,
                member_name: Some("Alice".into()),
                member_pubkey_hex: None,
                anchor_level: None,
                trust_ceiling: None,
            },
        ).await.unwrap().clone();

        // 1. Serialized form should NOT contain `proposal_ref` (skip_if None)
        let json = serde_json::to_string(&entry).unwrap();
        assert!(!json.contains("proposal_ref"),
            "default None proposal_ref must be skipped in serialization (saw: {})", json);

        // 2. Round-trip — still None.
        let back: LedgerEntry = serde_json::from_str(&json).unwrap();
        assert!(back.proposal_ref.is_none());
        assert_eq!(back.entry_hash, entry.entry_hash);

        // 3. Build a JSON string that LITERALLY omits the field
        // (mimicking a pre-V2-9-P2 ledger entry on disk) — must parse.
        let no_field_json = json.clone();
        assert!(!no_field_json.contains("proposal_ref"));
        let parsed: LedgerEntry = serde_json::from_str(&no_field_json).unwrap();
        assert!(parsed.proposal_ref.is_none());

        // 4. Chain verifies — signature still valid against the same bytes.
        let lookup = build_lookup([sovereign.lct.clone()]);
        ledger.verify_chain(|id| lookup.get(&id).cloned()).unwrap();
    }

    /// V2-9 Phase 2: an entry committed WITH a proposal_ref serializes
    /// + verifies correctly. The field is part of signing_payload so
    /// the signature covers it (forgery resistance).
    #[tokio::test]
    async fn proposal_ref_when_set_is_signed_and_verifies() {
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();
        let keypair = sovereign.keypair().unwrap();
        let (store, _) = fresh_store(&tmp);
        let mut ledger = HubLedger::open(store).await.unwrap();
        ledger.write_genesis(
            sovereign.lct.id, &keypair,
            "Test".into(), "sha256:0".into(),
        ).await.unwrap();
        let proposal_id = Uuid::new_v4();
        let event = HubEvent::MemberAdded {
            member_lct_id: Uuid::new_v4(),
            added_by: sovereign.lct.id,
            member_name: Some("Carol".into()),
            member_pubkey_hex: None,
            anchor_level: None,
            trust_ceiling: None,
        };
        // Build with proposal_ref + sign + commit.
        let unsigned = ledger.build_entry_with_proposal_ref(
            sovereign.lct.id, event, Utc::now(), Some(proposal_id),
        ).unwrap();
        let sig = keypair.sign(&unsigned.signing_bytes);
        let entry = ledger.append_signed(unsigned, SignatureBytes::from_bytes(sig.bytes)).await
            .unwrap()
            .clone();
        assert_eq!(entry.proposal_ref, Some(proposal_id));

        // Serialized form DOES contain `proposal_ref` now.
        let json = serde_json::to_string(&entry).unwrap();
        assert!(json.contains("proposal_ref"));

        // Chain verifies — signature covers the proposal_ref field.
        let lookup = build_lookup([sovereign.lct.clone()]);
        ledger.verify_chain(|id| lookup.get(&id).cloned()).unwrap();

        // Tamper test: flipping proposal_ref invalidates the signature.
        let mut tampered = entry.clone();
        tampered.proposal_ref = Some(Uuid::new_v4());
        let payload = signing_payload(&tampered).unwrap();
        let sig_bytes = hex::decode(&tampered.signature).unwrap();
        let sig_arr: [u8; 64] = sig_bytes.as_slice().try_into().unwrap();
        let result = sovereign.lct.verify_signature(
            &payload,
            &SignatureBytes::from_bytes(sig_arr),
        );
        assert!(result.is_err(),
            "tampering with proposal_ref must invalidate signature");
    }

    /// `signing_payload` embeds `timestamp` in whatever spelling chrono's
    /// serde impl chooses — `to_rfc3339_opts(AutoSi, true)`, whose
    /// fractional width varies with the value. Every signature and every
    /// `entry_hash` in the live chain was computed over that spelling, so
    /// it is part of the ledger's on-disk format even though no type
    /// declares it. Pin the exact output: a chrono upgrade that changes
    /// the format fails here, at upgrade time, instead of surfacing as a
    /// whole-chain verification failure during an audit.
    #[test]
    fn ledger_timestamp_wire_spelling_is_pinned() {
        let cases = [
            // (instant, exact bytes chrono writes into signing_payload)
            ("2026-06-11T00:00:00Z",           "\"2026-06-11T00:00:00Z\""),
            ("2026-06-11T00:00:00.100Z",       "\"2026-06-11T00:00:00.100Z\""),
            ("2026-06-11T00:00:00.123456Z",    "\"2026-06-11T00:00:00.123456Z\""),
            ("2026-06-11T00:00:00.123456789Z", "\"2026-06-11T00:00:00.123456789Z\""),
        ];
        for (input, expected) in cases {
            let t = DateTime::parse_from_rfc3339(input).unwrap().with_timezone(&Utc);
            assert_eq!(
                serde_json::to_string(&t).unwrap(), expected,
                "chrono's serde spelling changed for {input} — every existing \
                 ledger signature and entry_hash was computed over the old one"
            );
        }
        // The variable-width part, stated as the rule an auditor needs:
        // equivalent RFC3339 spellings collapse to one canonical output.
        for equivalent in [
            "2026-06-11T00:00:00.000Z",
            "2026-06-11T00:00:00+00:00",
            "2026-06-10T17:00:00-07:00",
        ] {
            let t = DateTime::parse_from_rfc3339(equivalent).unwrap().with_timezone(&Utc);
            assert_eq!(serde_json::to_string(&t).unwrap(), "\"2026-06-11T00:00:00Z\"");
        }
    }

    /// The bytes verified are re-derived from the parsed entry, not read
    /// from the stored text. Rewriting a persisted timestamp into a
    /// different — but equivalent — RFC3339 spelling therefore leaves an
    /// intact chain intact: the ledger is robust to re-spelling by a
    /// migration, a backend, or an operator's editor.
    ///
    /// The second half is what keeps this from passing vacuously: changing
    /// the *instant* rather than its spelling must still break the chain.
    #[tokio::test]
    async fn verification_re_derives_so_it_is_spelling_independent() {
        let tmp = tempdir().unwrap();
        let sovereign = fresh_sovereign();
        let keypair = sovereign.keypair().unwrap();
        let (store, ledger_path) = fresh_store(&tmp);
        let mut ledger = HubLedger::open(store).await.unwrap();
        ledger.write_genesis(
            sovereign.lct.id, &keypair,
            "Test".into(), "sha256:0".into(),
        ).await.unwrap();

        // A zero-nanosecond instant, so the stored spelling is the bare
        // `Z` form and the rewrite below is a pure spelling change.
        let pinned = DateTime::parse_from_rfc3339("2026-06-11T00:00:00Z")
            .unwrap().with_timezone(&Utc);
        let unsigned = ledger.build_entry(
            sovereign.lct.id,
            HubEvent::MemberAdded {
                member_lct_id: Uuid::new_v4(),
                added_by: sovereign.lct.id,
                member_name: Some("Dana".into()),
                member_pubkey_hex: None,
                anchor_level: None,
                trust_ceiling: None,
            },
            pinned,
        ).unwrap();
        let sig = keypair.sign(&unsigned.signing_bytes);
        ledger.append_signed(unsigned, SignatureBytes::from_bytes(sig.bytes)).await.unwrap();

        let lookup = build_lookup([sovereign.lct.clone()]);
        let on_disk = std::fs::read_to_string(&ledger_path).unwrap();
        assert!(on_disk.contains("\"timestamp\":\"2026-06-11T00:00:00Z\""),
            "expected the bare-Z spelling on disk, saw: {on_disk}");

        // Same instant, different bytes.
        let respelled = on_disk.replace(
            "\"timestamp\":\"2026-06-11T00:00:00Z\"",
            "\"timestamp\":\"2026-06-10T17:00:00-07:00\"",
        );
        assert_ne!(respelled, on_disk, "the rewrite must actually change the text");
        std::fs::write(&ledger_path, &respelled).unwrap();

        let reopened = HubLedger::open(reopen_file_backend(&tmp)).await.unwrap();
        reopened.verify_chain(|id| lookup.get(&id).cloned()).expect(
            "re-spelling a timestamp must not invalidate an intact chain — \
             verification re-derives the signed bytes from the parsed entry"
        );

        // Not vacuous: a different instant is a different entry.
        let moved = respelled.replace(
            "\"timestamp\":\"2026-06-10T17:00:00-07:00\"",
            "\"timestamp\":\"2026-06-11T00:00:01Z\"",
        );
        assert_ne!(moved, respelled);
        std::fs::write(&ledger_path, &moved).unwrap();
        let tampered = HubLedger::open(reopen_file_backend(&tmp)).await.unwrap();
        assert!(
            tampered.verify_chain(|id| lookup.get(&id).cloned()).is_err(),
            "moving the instant must break the chain"
        );
    }

    // ---- chain-tail watermark (dp's design, 2026-08-08): the sealed floor ----

    /// Build a 3-entry chain on the File backend and return (tmp, ledger_path).
    async fn three_entry_chain() -> (tempfile::TempDir, std::path::PathBuf, IdentityFile) {
        let tmp = tempdir().unwrap();
        let (store, ledger_path) = fresh_store(&tmp);
        let sov = fresh_sovereign();
        let kp = sov.keypair().unwrap();
        let mut ledger = HubLedger::open(store).await.unwrap();
        ledger.write_genesis(sov.lct.id, &kp, "WM".into(), "sha256:0".into()).await.unwrap();
        for skill in ["a", "b"] {
            ledger.append(sov.lct.id, &kp, HubEvent::MemberSkillDeclared {
                member_lct_id: sov.lct.id,
                skill: skill.into(),
                declared_by: sov.lct.id,
            }).await.unwrap();
        }
        (tmp, ledger_path, sov)
    }

    #[tokio::test]
    async fn every_append_stamps_the_sealed_watermark() {
        let (tmp, _lp, _sov) = three_entry_chain().await;
        let store = reopen_file_backend(&tmp);
        let wm = store.read_chain_watermark().await.unwrap()
            .expect("appends must leave a watermark");
        assert_eq!(wm.chain_len, 3);
        // The watermark's head is the chain's real head.
        let entries = store.ledger_load_all().await.unwrap();
        assert_eq!(wm.head_hash, entries.last().unwrap().entry_hash);
        // And it remembers the couple before it, per the design.
        assert_eq!(wm.prev_hashes.len(), 2);
        assert_eq!(wm.prev_hashes[0], entries[entries.len()-2].entry_hash);
    }

    /// The attack verify-ledger warns about: drop the tail, chain still verifies.
    /// With the watermark, open() refuses.
    #[tokio::test]
    async fn a_truncated_tail_is_refused_at_open() {
        let (tmp, ledger_path, _sov) = three_entry_chain().await;

        // Truncate: remove the last line of ledger.jsonl. Assert the mutation
        // landed — a truncation that silently failed reads exactly like a
        // working guard.
        let txt = std::fs::read_to_string(&ledger_path).unwrap();
        let lines: Vec<&str> = txt.lines().collect();
        assert_eq!(lines.len(), 3, "fixture did not build 3 entries");
        std::fs::write(&ledger_path, format!("{}\n{}\n", lines[0], lines[1])).unwrap();
        assert_eq!(std::fs::read_to_string(&ledger_path).unwrap().lines().count(), 2);

        let err = HubLedger::open(reopen_file_backend(&tmp)).await
            .err()
            .expect("a chain shorter than its sealed watermark must be refused");
        let msg = format!("{err:#}");
        assert!(msg.contains("watermark"), "the refusal must name the mechanism: {msg}");
    }

    /// A crash between ledger-append and watermark-stamp leaves the watermark
    /// one behind. That is the benign direction and must not brick the hub.
    #[tokio::test]
    async fn a_lagging_watermark_is_tolerated() {
        let (tmp, _lp, _sov) = three_entry_chain().await;
        {
            let store = reopen_file_backend(&tmp);
            let entries = store.ledger_load_all().await.unwrap();
            let mut store = store;
            store.write_chain_watermark(&ChainWatermark {
                chain_len: 2,
                head_hash: entries[1].entry_hash.clone(),
                prev_hashes: vec![entries[0].entry_hash.clone()],
                stamped_at: Utc::now(),
            }).await.unwrap();
        }
        let ledger = HubLedger::open(reopen_file_backend(&tmp)).await
            .expect("a watermark BEHIND the chain is the crash window, not an attack");
        assert_eq!(ledger.len(), 3);
    }

    /// Same length, different entry at the watermark index: a rewritten history
    /// that kept the count. Refused.
    #[tokio::test]
    async fn a_divergent_entry_at_the_watermark_is_refused() {
        let (tmp, _lp, _sov) = three_entry_chain().await;
        {
            let mut store = reopen_file_backend(&tmp);
            store.write_chain_watermark(&ChainWatermark {
                chain_len: 3,
                head_hash: "0".repeat(64),
                prev_hashes: vec![],
                stamped_at: Utc::now(),
            }).await.unwrap();
        }
        let err = HubLedger::open(reopen_file_backend(&tmp)).await
            .err()
            .expect("an entry that is not the one the watermark witnessed must be refused");
        assert!(format!("{err:#}").contains("watermark"));
    }
}
