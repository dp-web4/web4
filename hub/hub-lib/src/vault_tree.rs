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
//! This is the public, generic base. Presence/liveness-gated tiers (constellation-MFA, the
//! novel mechanism) are a separate, private extension and are intentionally not here.
//!
//! Crypto is reused from [`web4_core::vault::crypto`] (Argon2id `derive_key` +
//! ChaCha20-Poly1305 `seal`/`open`) — no new ciphers.

use anyhow::{bail, Context, Result};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::path::{Path, PathBuf};
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
    path: PathBuf,
    master: DerivedKey,
    salt: [u8; 16],
    data: VaultData,
}

impl OpenVault {
    /// Create a fresh empty vault at `path`, keyed by `master_passphrase`. Not yet persisted.
    pub fn create(path: impl AsRef<Path>, master_passphrase: &str, vault_id: impl Into<String>) -> Result<Self> {
        let salt = crypto::generate_salt();
        let master = crypto::derive_key(master_passphrase, &salt).map_err(|e| anyhow::anyhow!("derive master: {e}"))?;
        Ok(Self {
            path: path.as_ref().to_path_buf(),
            master,
            salt,
            data: VaultData { meta: Meta { schema: 1, vault_id: vault_id.into() }, ..Default::default() },
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
        Ok(Self { path, master, salt, data })
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
        let plain = serde_json::to_vec(&self.data).context("serializing vault data")?;
        let sealed = crypto::seal(&self.master, &plain).map_err(|e| anyhow::anyhow!("seal vault: {e}"))?;
        let mut out = Vec::with_capacity(21 + sealed.len());
        out.extend_from_slice(MAGIC);
        out.push(VERSION);
        out.extend_from_slice(&self.salt);
        out.extend_from_slice(&sealed);
        let tmp = self.path.with_extension("hvlt-tmp");
        std::fs::write(&tmp, &out).with_context(|| format!("writing {}", tmp.display()))?;
        std::fs::rename(&tmp, &self.path).with_context(|| format!("installing {}", self.path.display()))?;
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

    /// Open an item, returning its plaintext in a **zeroizing** buffer. `Sealed` items
    /// require the correct `cred`; a wrong/missing credential fails closed.
    pub fn open_item(&self, name: &str, cred: Option<&str>) -> Result<Zeroizing<Vec<u8>>> {
        let item = self.data.items.get(name).ok_or_else(|| anyhow::anyhow!("no such item: {name}"))?;
        match item.protection {
            Protection::Master => Ok(Zeroizing::new(item.payload.clone())),
            Protection::Sealed => {
                let cred = cred.ok_or_else(|| anyhow::anyhow!("item is sealed — a credential is required"))?;
                let salt = item.inner_salt.as_ref().ok_or_else(|| anyhow::anyhow!("sealed item missing salt (corrupt)"))?;
                let key = crypto::derive_key(cred, salt).map_err(|e| anyhow::anyhow!("derive sealed key: {e}"))?;
                let plain = crypto::open(&key, &item.payload)
                    .map_err(|_| anyhow::anyhow!("sealed item did not open (wrong credential)"))?;
                Ok(Zeroizing::new(plain))
            }
        }
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
        assert_eq!(&v.open_item("g", None).unwrap()[..], b"SECRET_MARKER_XYZ");
    }

    #[test]
    fn wrong_master_fails_closed() {
        let (_d, p) = tmp();
        OpenVault::create(&p, "right", "v").unwrap().save().unwrap();
        assert!(OpenVault::open(&p, "wrong").is_err());
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
        assert!(v.open_item("k", None).is_err());            // master alone: no
        assert!(v.open_item("k", Some("nope")).is_err());     // wrong cred: no
        assert_eq!(&v.open_item("k", Some("second-factor")).unwrap()[..], b"top-secret");
    }
}
