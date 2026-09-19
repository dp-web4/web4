// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! `vault_tree` — a **recursive-item enclosure** (the generic base of the shared
//! recursive-vault doctrine; see `web4/docs/best-practices/storage-and-key-management.md`).
//!
//! A vault is a tree whose outer unlock (master key) reveals only `config` + the **index**
//! (what exists + how it's protected) — not every item's plaintext. Per-item
//! [`Protection`]: `Master` (outer key) or `Sealed` (an independent credential). An item may
//! itself be a `SubVault` (the recursion). Decryption is **memory-only** — [`open_item`] returns
//! a zeroizing buffer; nothing decrypted touches disk; persistence always re-encrypts.
//!
//! Four tiers, following the recursive-vault embodiment of the filed application
//! (US 19/803,885): `Master` (outer key), `Sealed` (an independent
//! credential), `Liveness` (a **fresh presence proof obtained at open time**), and
//! `SealedLiveness` (both).
//!
//! The presence proof is not re-invented here: a `Liveness` item is opened by presenting a
//! constellation attestation to the public [`crate::constellation`] verifier, which mints a
//! single-use challenge, resolves every device key and class from the **enrollment record**
//! rather than from the presented attestation, and derives the assurance tier from the
//! signatures that actually verified. The vault binds that challenge to the item being
//! opened, so a challenge minted for one item cannot open another.
//!
//! **This is the host-software embodiment.** The enforcement here is this process's own
//! code: a host that is itself compromised can call `open_item` directly. The specification's
//! stronger reading puts the decision inside a hardware module that holds the key material;
//! that embodiment needs hardware this crate does not have, and nothing here should be read
//! as providing it.
//!
//! Crypto is reused from [`web4_core::vault::crypto`] (Argon2id `derive_key` +
//! ChaCha20-Poly1305 `seal`/`open`) — no new ciphers.

use crate::constellation::{
    AssuranceLevel, ConstellationAttestation, ConstellationGate, EnrolledDeviceSet,
};
use anyhow::{bail, Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, HashMap};
use std::path::{Path, PathBuf};
use std::sync::Mutex;
use uuid::Uuid;
use web4_core::vault::crypto::{self, DerivedKey};
use zeroize::Zeroizing;

const MAGIC: &[u8; 4] = b"HVLT";
const VERSION: u8 = 1;

/// How an item is protected.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub enum Protection {
    /// Opened by the outer master key. The basics.
    Master,
    /// Encrypted under an INDEPENDENT credential; master unlock reveals it exists, not its
    /// plaintext.
    Sealed,
    /// Released only against a presence proof obtained **at open time**. The
    /// payload is master-encrypted like `Master`; what the tier adds is the check, and the
    /// check is only as strong as the process running it (see the module doc).
    Liveness { req: PresenceRequirement },
    /// Both: the independent credential AND a presence proof at open time.
    SealedLiveness { req: PresenceRequirement },
}

/// What a liveness-protected item requires of the presence evidence presented when it is
/// opened. The tier is the one the verifier **derived** from signatures that verified against
/// enrolled keys, never the tier the presenter claimed.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct PresenceRequirement {
    pub min_assurance: AssuranceLevel,
}

impl PresenceRequirement {
    /// Require at least `min_assurance`.
    pub fn at_least(min_assurance: AssuranceLevel) -> Self {
        Self { min_assurance }
    }
}

/// Presence evidence a caller presents to open a liveness-protected item.
///
/// Everything authoritative is borrowed from outside the attestation: the gate holds the
/// challenge it minted, `enrolled` is the owner-committed enrollment record, and
/// `pinned_owner_pubkey_hex` is the owner key the hub already trusts for this pair. The
/// attestation identifies devices and proves possession; it is never the source of a key.
pub struct PresenceEvidence<'a> {
    pub gate: &'a ConstellationGate,
    pub pair_id: Uuid,
    pub attestation: &'a ConstellationAttestation,
    pub pinned_owner_pubkey_hex: &'a str,
    pub enrolled: &'a EnrolledDeviceSet,
    pub now: DateTime<Utc>,
}

/// The extra factors an open may carry. `Default` is "master only", which opens `Master`
/// items and fails closed on every other tier.
#[derive(Default)]
pub struct Factors<'a> {
    /// The independent credential for `Sealed` / `SealedLiveness`.
    pub cred: Option<&'a str>,
    /// Presence evidence for `Liveness` / `SealedLiveness`.
    pub presence: Option<PresenceEvidence<'a>>,
}

impl<'a> Factors<'a> {
    /// Just the independent credential.
    pub fn sealed(cred: &'a str) -> Self {
        Self { cred: Some(cred), presence: None }
    }

    /// Just presence evidence.
    pub fn presence(ev: PresenceEvidence<'a>) -> Self {
        Self { cred: None, presence: Some(ev) }
    }

    /// Both factors, for a `SealedLiveness` item.
    pub fn sealed_with_presence(cred: &'a str, ev: PresenceEvidence<'a>) -> Self {
        Self { cred: Some(cred), presence: Some(ev) }
    }
}

/// What an item is, for the index (no plaintext exposed).
#[derive(Clone, Copy, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ItemKind {
    Credential,
    Document,
    /// The item's plaintext is itself a serialized vault — the recursion.
    SubVault,
}

#[derive(Clone, Serialize, Deserialize)]
struct StoredItem {
    kind: ItemKind,
    protection: Protection,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    inner_salt: Option<Vec<u8>>,
    /// `Master`: plaintext (within the outer encryption). `Sealed`: inner AEAD blob.
    payload: Vec<u8>,
}

#[derive(Clone, Default, Serialize, Deserialize)]
struct Meta {
    schema: u32,
    vault_id: String,
}

#[derive(Clone, Default, Serialize, Deserialize)]
struct VaultData {
    meta: Meta,
    config: serde_json::Value,
    items: BTreeMap<String, StoredItem>,
}

/// A plaintext-free listing of a vault's contents (from the index).
#[derive(Clone, Debug, PartialEq)]
pub struct ItemRef {
    pub name: String,
    pub kind: ItemKind,
    pub protection: Protection,
}

/// An opened vault held **in memory**. Item plaintext is produced on demand by
/// [`open_item`](Self::open_item) into a zeroizing buffer; never written to disk.
pub struct OpenVault {
    /// The file this vault persists to, or `None` for a **sub-vault handle**: one opened
    /// out of a parent item, which has no file of its own. `save()` refuses on such a
    /// handle — writing it to `self.path` would put the child's tree where the parent's
    /// file is, under the same master and salt, producing a vault that opens cleanly and
    /// has silently lost the parent. Write a modified child back with
    /// [`put_subvault`](Self::put_subvault) on its parent, then save the parent.
    path: Option<PathBuf>,
    master: DerivedKey,
    salt: [u8; 16],
    data: VaultData,
    /// Which item each outstanding presence challenge was minted for, by pair. In memory
    /// only — never serialized, so a restart invalidates every outstanding challenge. This
    /// is what binds a challenge to the item being opened: the gate's nonce alone is bound
    /// to a pair, not to a secret.
    pending_presence: Mutex<HashMap<Uuid, String>>,
}

impl OpenVault {
    /// Create a fresh empty vault at `path`, keyed by `master_passphrase`. Not yet persisted.
    pub fn create(path: impl AsRef<Path>, master_passphrase: &str, vault_id: impl Into<String>) -> Result<Self> {
        let salt = crypto::generate_salt();
        let master = crypto::derive_key(master_passphrase, &salt).map_err(|e| anyhow::anyhow!("derive master: {e}"))?;
        Ok(Self {
            path: Some(path.as_ref().to_path_buf()),
            master,
            salt,
            data: VaultData { meta: Meta { schema: 1, vault_id: vault_id.into() }, ..Default::default() },
            pending_presence: Mutex::new(HashMap::new()),
        })
    }

    /// Open an existing vault file. Fails closed on a wrong key (AEAD) — no plaintext fallback.
    pub fn open(path: impl AsRef<Path>, master_passphrase: &str) -> Result<Self> {
        let path = path.as_ref().to_path_buf();
        let raw = std::fs::read(&path).with_context(|| format!("reading vault {}", path.display()))?;
        if raw.len() < 21 || &raw[..4] != MAGIC {
            bail!("{} is not a vault_tree file", path.display());
        }
        if raw[4] != VERSION {
            bail!("vault_tree {} version {} unsupported", path.display(), raw[4]);
        }
        let mut salt = [0u8; 16];
        salt.copy_from_slice(&raw[5..21]);
        let master = crypto::derive_key(master_passphrase, &salt).map_err(|e| anyhow::anyhow!("derive master: {e}"))?;
        let plain = crypto::open(&master, &raw[21..])
            .map_err(|_| anyhow::anyhow!("vault {} did not open (wrong passphrase or corrupt)", path.display()))?;
        let data: VaultData = serde_json::from_slice(&plain).context("parsing vault data")?;
        Ok(Self { path: Some(path), master, salt, data, pending_presence: Mutex::new(HashMap::new()) })
    }

    /// Open if present, else create. Convenience for daemon startup.
    pub fn open_or_create(path: impl AsRef<Path>, master_passphrase: &str, vault_id: impl Into<String>) -> Result<Self> {
        if path.as_ref().exists() {
            Self::open(path, master_passphrase)
        } else {
            let v = Self::create(path, master_passphrase, vault_id)?;
            v.save()?;
            Ok(v)
        }
    }

    /// Re-encrypt the whole tree and write it atomically (the only persistence path).
    pub fn save(&self) -> Result<()> {
        let path = self.path.as_ref().ok_or_else(|| {
            anyhow::anyhow!(
                "this is a sub-vault handle and has no file of its own — write it back with                  put_subvault(name, &child) on the parent it came from, then save the parent"
            )
        })?;
        let plain = serde_json::to_vec(&self.data).context("serializing vault data")?;
        let sealed = crypto::seal(&self.master, &plain).map_err(|e| anyhow::anyhow!("seal vault: {e}"))?;
        let mut out = Vec::with_capacity(21 + sealed.len());
        out.extend_from_slice(MAGIC);
        out.push(VERSION);
        out.extend_from_slice(&self.salt);
        out.extend_from_slice(&sealed);
        // Was hand-rolled here as tmp+rename with a FIXED temp name and no
        // fsync — i.e. it carried both defects the helper exists to remove.
        // Two savers shared `<name>.hvlt-tmp`, so one could rename the other's
        // half-written temp into place, or find it already renamed away and
        // fail with ENOENT (measured — see the test below). And the rename
        // could become visible before the bytes, leaving a sealed vault that
        // decrypts to nothing. This file is the identity store; a torn write
        // here does not heal on the next save.
        //
        // 0600, and for the same reason the identity file is: the seal's
        // confidentiality is conditional on the passphrase, and an empty one is
        // explicitly permitted as a deliberate operator choice (see
        // `IdentityFile::save_encrypted` — "encrypted format with a publicly
        // derivable key"). A hub provisioned that way has a `protected.hvlt`
        // whose master key anyone can derive, holding the tier-2 sealing
        // credential; at 0644 that is readable by every local account. The mode
        // cannot be applied from outside — this rename installs a fresh inode
        // every save — so it belongs on the `open(2)` here.
        crate::atomic_file::write_atomic_mode(path, &out, 0o600)
            .with_context(|| format!("installing {}", path.display()))?;
        Ok(())
    }

    /// The index: what exists and how it's protected — no plaintext.
    pub fn list(&self) -> Vec<ItemRef> {
        self.data.items.iter().map(|(name, it)| ItemRef {
            name: name.clone(),
            kind: it.kind,
            protection: it.protection.clone(),
        }).collect()
    }

    pub fn contains(&self, name: &str) -> bool {
        self.data.items.contains_key(name)
    }

    /// Add a `Master`-tier item (readable after the outer unlock).
    pub fn put_master(&mut self, name: impl Into<String>, kind: ItemKind, bytes: &[u8]) {
        self.data.items.insert(name.into(), StoredItem {
            kind, protection: Protection::Master, inner_salt: None, payload: bytes.to_vec(),
        });
    }

    /// Add a `Sealed` item, encrypted under an independent credential (not the master key).
    pub fn put_sealed(&mut self, name: impl Into<String>, kind: ItemKind, bytes: &[u8], cred: &str) -> Result<()> {
        let salt = crypto::generate_salt();
        let key = crypto::derive_key(cred, &salt).map_err(|e| anyhow::anyhow!("derive sealed key: {e}"))?;
        let blob = crypto::seal(&key, bytes).map_err(|e| anyhow::anyhow!("seal item: {e}"))?;
        self.data.items.insert(name.into(), StoredItem {
            kind, protection: Protection::Sealed, inner_salt: Some(salt.to_vec()), payload: blob,
        });
        Ok(())
    }

    /// Add a `Liveness` item: master-encrypted, released only against a presence proof
    /// obtained at open time. Nothing about the proof is stored with the item — there is no
    /// nonce on disk to replay, because the challenge is minted per open.
    pub fn put_liveness(&mut self, name: impl Into<String>, kind: ItemKind, bytes: &[u8], req: PresenceRequirement) {
        self.data.items.insert(name.into(), StoredItem {
            kind, protection: Protection::Liveness { req }, inner_salt: None, payload: bytes.to_vec(),
        });
    }

    /// Add a `SealedLiveness` item: sealed under an independent credential AND gated on a
    /// presence proof at open time.
    pub fn put_sealed_liveness(
        &mut self,
        name: impl Into<String>,
        kind: ItemKind,
        bytes: &[u8],
        cred: &str,
        req: PresenceRequirement,
    ) -> Result<()> {
        let salt = crypto::generate_salt();
        let key = crypto::derive_key(cred, &salt).map_err(|e| anyhow::anyhow!("derive sealed key: {e}"))?;
        let blob = crypto::seal(&key, bytes).map_err(|e| anyhow::anyhow!("seal item: {e}"))?;
        self.data.items.insert(name.into(), StoredItem {
            kind, protection: Protection::SealedLiveness { req }, inner_salt: Some(salt.to_vec()), payload: blob,
        });
        Ok(())
    }

    /// Store `child` as a `Master`-tier sub-vault item of this vault — the write half of
    /// [`open_subvault`](Self::open_subvault). Persist by saving *this* vault.
    pub fn put_subvault(&mut self, name: impl Into<String>, child: &OpenVault) -> Result<()> {
        let bytes = serde_json::to_vec(&child.data).context("serializing sub-vault data")?;
        self.put_master(name, ItemKind::SubVault, &bytes);
        Ok(())
    }

    /// Store `child` as a `Sealed` sub-vault item, encrypted under an independent credential.
    /// The credential is the one a later [`open_subvault`](Self::open_subvault) will need.
    pub fn put_sealed_subvault(&mut self, name: impl Into<String>, child: &OpenVault, cred: &str) -> Result<()> {
        let bytes = serde_json::to_vec(&child.data).context("serializing sub-vault data")?;
        self.put_sealed(name, ItemKind::SubVault, &bytes, cred)
    }

    /// Mint a presence challenge for opening `name` over the constellation pair `pair_id`,
    /// and remember which item it was minted for. The returned nonce is the one the member's
    /// attestation must carry.
    ///
    /// The challenge is single-use twice over: the gate burns its nonce on any presentation
    /// attempt, and this binding is removed on any open attempt. A failed presentation
    /// therefore costs a fresh challenge rather than leaving one open to further tries.
    ///
    /// The binding is **per pair, latest mint wins**: minting for a second item over the same
    /// `pair_id` replaces the first item's outstanding challenge, and an open of that first
    /// item then fails with "no presence challenge outstanding". Two items being opened
    /// concurrently need two pairs.
    pub fn presence_challenge(&self, name: &str, pair_id: Uuid, gate: &ConstellationGate) -> Result<String> {
        let item = self.data.items.get(name).ok_or_else(|| anyhow::anyhow!("no such item: {name}"))?;
        match item.protection {
            Protection::Liveness { .. } | Protection::SealedLiveness { .. } => {}
            _ => bail!("{name} is not a liveness-protected item — it takes no presence proof"),
        }
        let nonce = gate.mint_challenge(pair_id);
        self.pending_presence.lock().unwrap().insert(pair_id, name.to_string());
        Ok(nonce)
    }

    /// Open an item, returning its plaintext in a **zeroizing** buffer. Every tier above
    /// `Master` fails closed on a missing, wrong, or stale factor.
    pub fn open_item(&self, name: &str, factors: &Factors) -> Result<Zeroizing<Vec<u8>>> {
        let item = self.data.items.get(name).ok_or_else(|| anyhow::anyhow!("no such item: {name}"))?;
        match &item.protection {
            Protection::Master => Ok(Zeroizing::new(item.payload.clone())),
            Protection::Sealed => Ok(Zeroizing::new(self.unseal(item, factors)?)),
            Protection::Liveness { req } => {
                self.check_presence(name, req, factors)?;
                Ok(Zeroizing::new(item.payload.clone()))
            }
            Protection::SealedLiveness { req } => {
                // Presence first: a wrong credential should not be distinguishable from a
                // right one to a caller who cannot prove presence.
                self.check_presence(name, req, factors)?;
                Ok(Zeroizing::new(self.unseal(item, factors)?))
            }
        }
    }

    /// Open a `SubVault` item and return the nested vault, in memory. Nesting is transparent:
    /// the sub-vault is keyed by the same master, so one authorized open gates a hierarchy.
    /// The nested vault's own items keep their own tiers — opening the parent's sub-vault
    /// item does not open what is protected inside it.
    pub fn open_subvault(&self, name: &str, factors: &Factors) -> Result<OpenVault> {
        let item = self.data.items.get(name).ok_or_else(|| anyhow::anyhow!("no such item: {name}"))?;
        if item.kind != ItemKind::SubVault {
            bail!("{name} is not a sub-vault");
        }
        let plain = self.open_item(name, factors)?;
        let data: VaultData = serde_json::from_slice(&plain).context("parsing sub-vault data")?;
        // DerivedKey is not Clone; rebuild it from bytes (nesting shares the master key).
        let master = DerivedKey::from_bytes(*self.master.as_bytes());
        Ok(OpenVault {
            // No path: a sub-vault is persisted through its parent, never over the parent's
            // own file. See the field's doc.
            path: None,
            master,
            salt: self.salt,
            data,
            pending_presence: Mutex::new(HashMap::new()),
        })
    }

    fn unseal(&self, item: &StoredItem, factors: &Factors) -> Result<Vec<u8>> {
        let cred = factors.cred.ok_or_else(|| anyhow::anyhow!("item is sealed — a credential is required"))?;
        let salt = item.inner_salt.as_ref().ok_or_else(|| anyhow::anyhow!("sealed item missing salt (corrupt)"))?;
        let key = crypto::derive_key(cred, salt).map_err(|e| anyhow::anyhow!("derive sealed key: {e}"))?;
        crypto::open(&key, &item.payload)
            .map_err(|_| anyhow::anyhow!("sealed item did not open (wrong credential)"))
    }

    /// Verify presence **at this open**, against the challenge minted for this item.
    ///
    /// The evidence is verified by [`ConstellationGate::present`], which resolves every
    /// device key and class from the enrollment record rather than from the attestation,
    /// counts only signatures that verify, and derives the assurance tier itself. The
    /// requirement is then checked against the derived tier, never a claimed one.
    fn check_presence(&self, name: &str, req: &PresenceRequirement, factors: &Factors) -> Result<()> {
        let ev = factors
            .presence
            .as_ref()
            .ok_or_else(|| anyhow::anyhow!("{name} requires a presence proof obtained at open time"))?;
        let minted_for = self
            .pending_presence
            .lock()
            .unwrap()
            .remove(&ev.pair_id)
            .ok_or_else(|| anyhow::anyhow!("no presence challenge outstanding for this pair — call presence_challenge({name}) first"))?;
        if minted_for != name {
            bail!("the outstanding presence challenge was minted for {minted_for}, not {name}");
        }
        let binding = ev
            .gate
            .present(ev.pair_id, ev.attestation, ev.pinned_owner_pubkey_hex, ev.enrolled, ev.now)
            .map_err(|e| anyhow::anyhow!("presence proof refused: {e}"))?;
        if binding.assurance < req.min_assurance {
            bail!(
                "presence proof derived {:?}, below the item's required {:?}",
                binding.assurance,
                req.min_assurance
            );
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tmp() -> (tempfile::TempDir, PathBuf) {
        let d = tempfile::tempdir().unwrap();
        let p = d.path().join("t.hvlt");
        (d, p)
    }

    /// The vault file is the identity store, and its seal is only as
    /// confidential as the passphrase — which is permitted to be empty. So the
    /// file's mode is load-bearing, and it has to be set at the write: `save`
    /// renames a fresh inode over the target, so an operator's `chmod` is
    /// discarded by the next save. Both arms below; the second is the one that
    /// catches a regression back to the un-moded helper on an existing vault.
    #[cfg(unix)]
    #[test]
    fn save_lands_at_0600_and_does_not_revert_a_hardened_file() {
        use std::os::unix::fs::PermissionsExt;
        let (_d, p) = tmp();
        let mut v = OpenVault::create(&p, "m", "v1").unwrap();
        v.put_master("g", ItemKind::Document, b"SECRET_MARKER_XYZ");
        v.save().unwrap();
        let mode = std::fs::metadata(&p).unwrap().permissions().mode() & 0o777;
        assert_eq!(mode, 0o600, "fresh vault landed at {mode:o}, want 600");

        std::fs::set_permissions(&p, std::fs::Permissions::from_mode(0o600)).unwrap();
        v.save().unwrap();
        let mode = std::fs::metadata(&p).unwrap().permissions().mode() & 0o777;
        assert_eq!(mode, 0o600, "re-save reverted 0600 to {mode:o}");
    }

    #[test]
    fn master_round_trips_no_plaintext_on_disk() {
        let (_d, p) = tmp();
        {
            let mut v = OpenVault::create(&p, "m", "v1").unwrap();
            v.put_master("g", ItemKind::Document, b"SECRET_MARKER_XYZ");
            v.save().unwrap();
        }
        let raw = std::fs::read(&p).unwrap();
        assert_eq!(&raw[..4], b"HVLT");
        assert!(!raw.windows(17).any(|w| w == b"SECRET_MARKER_XYZ"));
        let v = OpenVault::open(&p, "m").unwrap();
        assert_eq!(&v.open_item("g", &Factors::default()).unwrap()[..], b"SECRET_MARKER_XYZ");
    }

    /// `save` used to hand-roll tmp+rename with a FIXED temp name
    /// (`<name>.hvlt-tmp`), so concurrent savers shared one temp file. Run
    /// against that version this test FAILS, in the way it actually breaks on
    /// Linux: not a byte-level splice (a single `write(2)` holds the inode
    /// lock, so the writes do not interleave) but
    ///
    ///     installing /tmp/.../t.hvlt: No such file or directory (os error 2)
    ///
    /// — one saver renamed the shared temp into place, and the next found
    /// nothing to rename. The neighbouring failure, which the same window
    /// permits, is worse and silent: rename the temp while another saver is
    /// still filling it, and the installed vault is a truncated one.
    ///
    /// So the assertions are "it still decrypts" and "every save succeeded",
    /// not "the bytes were not spliced". The payload is large and the race is
    /// repeated because the window is short; key derivation happens before the
    /// threads start so Argon2 does not stagger them out of contention.
    #[test]
    fn concurrent_saves_land_whole_and_leave_no_temp() {
        let (d, p) = tmp();
        let filler = vec![b'x'; 512 * 1024];

        let vaults: Vec<OpenVault> = (0..4)
            .map(|i| {
                let mut v = OpenVault::create(&p, "m", "v1").unwrap();
                v.put_master("filler", ItemKind::Document, &filler);
                v.put_master("who", ItemKind::Document, format!("body-{i}").as_bytes());
                v
            })
            .collect();

        // No per-round decrypt probe: `open` runs Argon2id and would put this
        // test in the minutes. Every save is checked instead — the shared-temp
        // window surfaces there — and the file is decrypted once at the end.
        for _ in 0..40 {
            std::thread::scope(|s| {
                for v in &vaults {
                    s.spawn(move || {
                        v.save().expect("a concurrent save failed to install");
                    });
                }
            });
        }

        // Whichever writer won, the file on disk is a complete vault: it
        // decrypts, and the marker is one writer's, not a mixture.
        let v = OpenVault::open(&p, "m").unwrap();
        let body = v.open_item("who", &Factors::default()).unwrap();
        assert!(
            body.starts_with(b"body-") && body.len() == 6,
            "vault decrypted to a splice: {body:?}"
        );

        let strays: Vec<_> = std::fs::read_dir(d.path())
            .unwrap()
            .map(|e| e.unwrap().file_name().to_string_lossy().into_owned())
            .filter(|n| n != "t.hvlt")
            .collect();
        assert!(strays.is_empty(), "left behind: {strays:?}");
    }

    #[test]
    fn wrong_master_fails_closed() {
        let (_d, p) = tmp();
        OpenVault::create(&p, "right", "v").unwrap().save().unwrap();
        assert!(OpenVault::open(&p, "wrong").is_err());
    }

    // ─────────── liveness tier: presence obtained at open time ───────────

    use crate::constellation::tests::make_att;
    use crate::constellation::{DeviceStatus, DeviceType, EnrolledDevice};
    use web4_core::crypto::KeyPair;

    const NOW: &str = "2026-09-17T12:00:00+00:00";

    fn now() -> DateTime<Utc> {
        DateTime::parse_from_rfc3339(NOW).unwrap().with_timezone(&Utc)
    }

    /// An owner with one enrolled device of `class`, and the enrollment record the verifier
    /// resolves against. The record is the authority for both the key and the class; the
    /// attestation only names the device.
    struct Constellation {
        owner_kp: KeyPair,
        owner_pubkey_hex: String,
        owner_lct: Uuid,
        device_lct: Uuid,
        device_kp: KeyPair,
        enrolled: EnrolledDeviceSet,
    }

    fn constellation(class: DeviceType) -> Constellation {
        let owner_kp = KeyPair::generate();
        let device_kp = KeyPair::generate();
        let owner_lct = Uuid::new_v4();
        let device_lct = Uuid::new_v4();
        let mut enrolled = EnrolledDeviceSet::new();
        enrolled.insert(EnrolledDevice {
            owner_lct_id: owner_lct,
            device_lct_id: device_lct,
            pubkey_hex: device_kp.verifying_key().to_hex(),
            device_class: class,
            status: DeviceStatus::Active,
            enrolled_at: now(),
            enrollment_version: 1,
        });
        let owner_pubkey_hex = owner_kp.verifying_key().to_hex();
        Constellation { owner_kp, owner_pubkey_hex, owner_lct, device_lct, device_kp, enrolled }
    }

    impl Constellation {
        fn attest(&self, nonce: &str) -> ConstellationAttestation {
            make_att(
                &self.owner_kp,
                self.owner_lct,
                &[self.device_lct],
                &[(self.device_lct, DeviceType::Hardware, &self.device_kp)],
                nonce,
                now(),
            )
        }

        fn evidence<'a>(
            &'a self,
            gate: &'a ConstellationGate,
            pair: Uuid,
            att: &'a ConstellationAttestation,
        ) -> PresenceEvidence<'a> {
            PresenceEvidence {
                gate,
                pair_id: pair,
                attestation: att,
                pinned_owner_pubkey_hex: &self.owner_pubkey_hex,
                enrolled: &self.enrolled,
                now: now(),
            }
        }
    }

    /// The tier's whole point: master alone does not open it, and a proof obtained at open
    /// time does. The challenge is minted per open — there is no nonce stored with the item
    /// for a caller to replay.
    #[test]
    fn liveness_item_needs_a_proof_obtained_at_open_time() {
        let (_d, p) = tmp();
        {
            let mut v = OpenVault::create(&p, "m", "v").unwrap();
            v.put_liveness(
                "ignition-key",
                ItemKind::Credential,
                b"LIVENESS_MARKER",
                PresenceRequirement::at_least(AssuranceLevel::HardwareBacked),
            );
            v.save().unwrap();
        }
        let v = OpenVault::open(&p, "m").unwrap();
        let raw = std::fs::read(&p).unwrap();
        assert!(!raw.windows(15).any(|w| w == b"LIVENESS_MARKER"));

        // Master unlock alone: refused.
        assert!(v.open_item("ignition-key", &Factors::default()).is_err());

        let c = constellation(DeviceType::Hardware);
        let gate = ConstellationGate::new();
        let pair = Uuid::new_v4();
        let nonce = v.presence_challenge("ignition-key", pair, &gate).unwrap();
        let att = c.attest(&nonce);
        let out = v
            .open_item("ignition-key", &Factors::presence(c.evidence(&gate, pair, &att)))
            .unwrap();
        assert_eq!(&out[..], b"LIVENESS_MARKER");
    }

    /// Fresh AT OPEN, not once per session: the same attestation replayed against a second
    /// open finds no outstanding challenge. This is the assertion that fails if the tier
    /// ever goes back to a nonce stored with the item.
    #[test]
    fn a_presence_proof_does_not_open_the_item_twice() {
        let (_d, p) = tmp();
        let mut v = OpenVault::create(&p, "m", "v").unwrap();
        v.put_liveness("k", ItemKind::Credential, b"x", PresenceRequirement::at_least(AssuranceLevel::SingleDevice));

        let c = constellation(DeviceType::Desktop);
        let gate = ConstellationGate::new();
        let pair = Uuid::new_v4();
        let nonce = v.presence_challenge("k", pair, &gate).unwrap();
        let att = c.attest(&nonce);
        assert!(v.open_item("k", &Factors::presence(c.evidence(&gate, pair, &att))).is_ok());

        let err = v
            .open_item("k", &Factors::presence(c.evidence(&gate, pair, &att)))
            .unwrap_err()
            .to_string();
        assert!(err.contains("no presence challenge outstanding"), "second open said: {err}");
    }

    /// A challenge minted for one item does not open another: the gate's nonce is bound to a
    /// pair, so the binding to the secret has to come from the vault.
    #[test]
    fn a_challenge_minted_for_one_item_does_not_open_another() {
        let (_d, p) = tmp();
        let mut v = OpenVault::create(&p, "m", "v").unwrap();
        let req = PresenceRequirement::at_least(AssuranceLevel::SingleDevice);
        v.put_liveness("cheap", ItemKind::Document, b"cheap", req.clone());
        v.put_liveness("treasury", ItemKind::Credential, b"treasury", req);

        let c = constellation(DeviceType::Desktop);
        let gate = ConstellationGate::new();
        let pair = Uuid::new_v4();
        let nonce = v.presence_challenge("cheap", pair, &gate).unwrap();
        let att = c.attest(&nonce);
        let err = v
            .open_item("treasury", &Factors::presence(c.evidence(&gate, pair, &att)))
            .unwrap_err()
            .to_string();
        assert!(err.contains("minted for cheap"), "cross-item open said: {err}");
    }

    /// The requirement is checked against the tier the verifier DERIVED from enrolled keys,
    /// not the one the attestation claims.
    ///
    /// The attestation here **claims** `HardwareBacked` while its one device is enrolled as
    /// `Desktop`. The claim is not covered by the signature — owner and devices sign the
    /// owner, roster, nonce and timestamp — so a presenter can set it freely, and a check
    /// that reads it opens the item. Asserting only that a low-tier device is refused would
    /// pass either way: this arm is what separates the two.
    #[test]
    fn a_claimed_tier_does_not_satisfy_a_hardware_requirement() {
        let (_d, p) = tmp();
        let mut v = OpenVault::create(&p, "m", "v").unwrap();
        v.put_liveness("k", ItemKind::Credential, b"x", PresenceRequirement::at_least(AssuranceLevel::HardwareBacked));

        let c = constellation(DeviceType::Desktop);
        let gate = ConstellationGate::new();
        let pair = Uuid::new_v4();
        let nonce = v.presence_challenge("k", pair, &gate).unwrap();
        let mut att = c.attest(&nonce);
        att.claimed_assurance = AssuranceLevel::HardwareBacked; // unsigned, and freely settable
        let err = v
            .open_item("k", &Factors::presence(c.evidence(&gate, pair, &att)))
            .unwrap_err()
            .to_string();
        assert!(err.contains("below the item's required"), "a claimed tier opened a hardware item: {err}");
    }

    /// Both factors, and neither alone.
    #[test]
    fn sealed_liveness_needs_the_credential_and_the_proof() {
        let (_d, p) = tmp();
        let mut v = OpenVault::create(&p, "m", "v").unwrap();
        v.put_sealed_liveness(
            "k",
            ItemKind::Credential,
            b"both-factors",
            "second-factor",
            PresenceRequirement::at_least(AssuranceLevel::HardwareBacked),
        )
        .unwrap();

        let c = constellation(DeviceType::Hardware);
        let gate = ConstellationGate::new();

        // Credential alone: refused, and the refusal names presence — the credential is not
        // even attempted.
        let err = v.open_item("k", &Factors::sealed("second-factor")).unwrap_err().to_string();
        assert!(err.contains("requires a presence proof"), "cred-only said: {err}");

        // Presence alone: refused.
        let pair = Uuid::new_v4();
        let nonce = v.presence_challenge("k", pair, &gate).unwrap();
        let att = c.attest(&nonce);
        assert!(v.open_item("k", &Factors::presence(c.evidence(&gate, pair, &att))).is_err());

        // Both: opens. (A fresh challenge — the last attempt burned the previous one.)
        let pair = Uuid::new_v4();
        let nonce = v.presence_challenge("k", pair, &gate).unwrap();
        let att = c.attest(&nonce);
        let out = v
            .open_item("k", &Factors::sealed_with_presence("second-factor", c.evidence(&gate, pair, &att)))
            .unwrap();
        assert_eq!(&out[..], b"both-factors");
    }

    /// The recursion: one authorized open yields a nested vault of the same form, and the
    /// nested vault's own tiers still hold. The sub-vault here is `Sealed`; the quorum that
    /// releases its credential in the hub's tier-2 path is a separate gate and is not what
    /// this test exercises.
    #[test]
    fn a_sub_vault_nests_and_keeps_its_own_tiers() {
        let (_d, p) = tmp();

        let mut inner = OpenVault::create(&p, "m", "inner").unwrap();
        inner.put_master("note", ItemKind::Document, b"inner-master");
        inner.put_sealed("deeper", ItemKind::Credential, b"inner-sealed", "inner-cred").unwrap();

        let mut v = OpenVault::create(&p, "m", "outer").unwrap();
        v.put_sealed_subvault("child", &inner, "child-cred").unwrap();
        v.save().unwrap();

        let v = OpenVault::open(&p, "m").unwrap();
        assert!(v.open_subvault("child", &Factors::default()).is_err()); // sealed: not without the credential
        let child = v.open_subvault("child", &Factors::sealed("child-cred")).unwrap();
        assert_eq!(&child.open_item("note", &Factors::default()).unwrap()[..], b"inner-master");
        // Opening the parent's item did not open what is protected inside the child.
        assert!(child.open_item("deeper", &Factors::default()).is_err());
        assert_eq!(&child.open_item("deeper", &Factors::sealed("inner-cred")).unwrap()[..], b"inner-sealed");
    }

    /// A sub-vault handle has no file of its own. Saving one used to write the CHILD's tree
    /// over the PARENT's file — re-sealed under the same master and salt, so the result
    /// opened cleanly and the parent was simply gone. Found by review, reproduced from
    /// outside the crate, and asserted here from both ends: the save is refused, and the
    /// parent file still holds what it held.
    #[test]
    fn a_sub_vault_cannot_overwrite_its_parent() {
        let (_d, p) = tmp();

        let mut child = OpenVault::create(&p, "m", "inner").unwrap();
        child.put_master("subitem", ItemKind::Document, b"child-body");

        let mut parent = OpenVault::create(&p, "m", "outer").unwrap();
        parent.put_master("PARENT_SECRET", ItemKind::Document, b"parent-body");
        parent.put_subvault("child", &child).unwrap();
        parent.save().unwrap();

        let parent = OpenVault::open(&p, "m").unwrap();
        let mut child = parent.open_subvault("child", &Factors::default()).unwrap();
        child.put_master("added-to-child", ItemKind::Document, b"new");

        let err = child.save().unwrap_err().to_string();
        assert!(err.contains("sub-vault handle"), "child.save() said: {err}");

        // The parent file is untouched: both its items are still there, and the child's
        // mutation did not land anywhere.
        let reopened = OpenVault::open(&p, "m").unwrap();
        let names: Vec<String> = reopened.list().into_iter().map(|i| i.name).collect();
        assert_eq!(names, vec!["PARENT_SECRET".to_string(), "child".to_string()]);
        assert_eq!(&reopened.open_item("PARENT_SECRET", &Factors::default()).unwrap()[..], b"parent-body");
    }

    /// The supported write path for a modified child: hand it back to the parent and save
    /// the parent. Siblings survive, and the child's change is inside the child item.
    #[test]
    fn a_modified_sub_vault_is_written_back_through_its_parent() {
        let (_d, p) = tmp();

        let mut child = OpenVault::create(&p, "m", "inner").unwrap();
        child.put_master("subitem", ItemKind::Document, b"child-body");
        let mut parent = OpenVault::create(&p, "m", "outer").unwrap();
        parent.put_master("sibling", ItemKind::Document, b"sibling-body");
        parent.put_sealed_subvault("child", &child, "child-cred").unwrap();
        parent.save().unwrap();

        let mut parent = OpenVault::open(&p, "m").unwrap();
        let mut child = parent.open_subvault("child", &Factors::sealed("child-cred")).unwrap();
        child.put_master("added-to-child", ItemKind::Document, b"new");
        parent.put_sealed_subvault("child", &child, "child-cred").unwrap();
        parent.save().unwrap();

        let parent = OpenVault::open(&p, "m").unwrap();
        assert_eq!(&parent.open_item("sibling", &Factors::default()).unwrap()[..], b"sibling-body");
        let child = parent.open_subvault("child", &Factors::sealed("child-cred")).unwrap();
        assert_eq!(&child.open_item("added-to-child", &Factors::default()).unwrap()[..], b"new");
        assert_eq!(&child.open_item("subitem", &Factors::default()).unwrap()[..], b"child-body");
    }

    #[test]
    fn sealed_needs_the_credential() {
        let (_d, p) = tmp();
        {
            let mut v = OpenVault::create(&p, "m", "v").unwrap();
            v.put_sealed("k", ItemKind::Credential, b"top-secret", "second-factor").unwrap();
            v.save().unwrap();
        }
        let v = OpenVault::open(&p, "m").unwrap();
        assert_eq!(v.list()[0].protection, Protection::Sealed);
        assert!(v.open_item("k", &Factors::default()).is_err());            // master alone: no
        assert!(v.open_item("k", &Factors::sealed("nope")).is_err());     // wrong cred: no
        assert_eq!(&v.open_item("k", &Factors::sealed("second-factor")).unwrap()[..], b"top-secret");
    }
}
