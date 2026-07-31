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
        crate::atomic_file::write_atomic_mode(&self.path, &out, 0o600)
            .with_context(|| format!("installing {}", self.path.display()))?;
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
        assert_eq!(&v.open_item("g", None).unwrap()[..], b"SECRET_MARKER_XYZ");
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
        let body = v.open_item("who", None).unwrap();
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
