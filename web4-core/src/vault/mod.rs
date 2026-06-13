// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later

//! # Recursive in-memory vault
//!
//! The shared storage substrate for hub / hestia / hardbound. Doctrine (see
//! `dev-hub/design/recursive-vault.md`):
//!
//! 1. **Total enclosure** — config, identity, metadata, and state live inside an
//!    encrypted vault, never in plaintext files. Each item is a [`Document`].
//! 2. **Recursive locking** — the outer unlock yields the basics + an index;
//!    individual items can be [`Protection::Sealed`] under an independent
//!    credential, and a sealed item's plaintext can itself be a whole vault (a
//!    sub-vault).
//! 3. **Memory-only unlock** — decryption produces a zeroizing in-memory buffer
//!    ([`open_document`](Vault::open_document)); nothing decrypted touches disk.
//!    Persistence always re-encrypts.
//!
//! The on-disk file is `magic "W4VT" | version | salt(16) | nonce(12) |
//! ChaCha20-Poly1305(serialized contents)`. The whole-file key is Argon2id over
//! the master passphrase.
//!
//! This crate provides the generic container; applications store whatever they
//! need as documents (an app's typed config/credential structs serialize to
//! document bytes). Apps that want richer per-credential metadata layer it on
//! top.

pub mod crypto;
pub mod document;

pub use document::{Document, ItemRef, Protection};

use std::fs::{self, File};
use std::io::Write;
use std::path::{Path, PathBuf};

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use zeroize::Zeroizing;

use crate::error::{Result, Web4Error};

const MAGIC: &[u8; 4] = b"W4VT";
const VERSION: u8 = 1;
const HEADER_LEN: usize = 4 + 1 + 16 + 12; // 33

/// The cleartext contents of a vault — serialized to JSON, then encrypted at
/// rest. Generic: everything an application encloses is a [`Document`].
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VaultContents {
    pub version: u32,
    pub created_at: DateTime<Utc>,
    #[serde(default)]
    pub documents: Vec<Document>,
}

impl Default for VaultContents {
    fn default() -> Self {
        Self {
            version: 1,
            created_at: Utc::now(),
            documents: Vec::new(),
        }
    }
}

/// An open vault. Holds the decrypted contents in memory and the master
/// passphrase needed to re-encrypt on save. Drop does not persist.
pub struct Vault {
    path: PathBuf,
    passphrase: String,
    contents: VaultContents,
}

impl Vault {
    /// Open an existing vault file with the master passphrase. Decrypts the
    /// contents INTO MEMORY.
    pub fn open(path: impl Into<PathBuf>, passphrase: impl Into<String>) -> Result<Self> {
        let path = path.into();
        let passphrase = passphrase.into();
        let contents = load(&path, &passphrase)?;
        Ok(Self { path, passphrase, contents })
    }

    /// Create a new empty vault. Errors if a file already exists at `path`.
    pub fn init(path: impl Into<PathBuf>, passphrase: impl Into<String>) -> Result<Self> {
        let path = path.into();
        if path.exists() {
            return Err(Web4Error::Vault(format!("vault already exists: {}", path.display())));
        }
        Self::init_force(path, passphrase)
    }

    /// Create a new empty vault, overwriting any existing file.
    pub fn init_force(path: impl Into<PathBuf>, passphrase: impl Into<String>) -> Result<Self> {
        let path = path.into();
        let passphrase = passphrase.into();
        let contents = VaultContents::default();
        save(&path, &passphrase, &contents)?;
        Ok(Self { path, passphrase, contents })
    }

    pub fn path(&self) -> &Path {
        &self.path
    }

    fn doc_pos(&self, namespace: &str, name: &str) -> Option<usize> {
        self.contents
            .documents
            .iter()
            .position(|d| d.namespace == namespace && d.name == name)
    }

    /// The content index: namespace + name + protection for every item, without
    /// exposing sealed plaintext.
    pub fn index(&self) -> Vec<ItemRef> {
        self.contents.documents.iter().map(ItemRef::from).collect()
    }

    /// Store a master-tier document (config / metadata / state). Upserts by
    /// (namespace, name) and persists.
    pub fn put_document(&mut self, namespace: &str, name: &str, bytes: Vec<u8>) -> Result<()> {
        self.upsert(Document::master(namespace, name, bytes))
    }

    /// Read a master-tier document's bytes. `None` if absent or sealed.
    pub fn get_document(&self, namespace: &str, name: &str) -> Option<&[u8]> {
        self.doc_pos(namespace, name)
            .and_then(|i| self.contents.documents[i].master_bytes())
    }

    /// Store a document sealed under an INDEPENDENT `credential`. Upserts.
    pub fn seal_document(
        &mut self,
        namespace: &str,
        name: &str,
        bytes: &[u8],
        credential: &str,
    ) -> Result<()> {
        self.upsert(Document::sealed(namespace, name, bytes, credential)?)
    }

    /// Open a document INTO MEMORY. For a sealed document, `credential` is its
    /// independent secret. Returns a zeroizing buffer; nothing touches disk.
    pub fn open_document(
        &self,
        namespace: &str,
        name: &str,
        credential: &str,
    ) -> Result<Zeroizing<Vec<u8>>> {
        let i = self
            .doc_pos(namespace, name)
            .ok_or_else(|| Web4Error::NotFound(format!("{namespace}/{name}")))?;
        self.contents.documents[i].open(credential)
    }

    pub fn remove_document(&mut self, namespace: &str, name: &str) -> Result<()> {
        let i = self
            .doc_pos(namespace, name)
            .ok_or_else(|| Web4Error::NotFound(format!("{namespace}/{name}")))?;
        self.contents.documents.remove(i);
        self.save()
    }

    /// Store a nested vault, sealed under its own `credential` (recursion).
    pub fn put_subvault(
        &mut self,
        namespace: &str,
        name: &str,
        sub: &VaultContents,
        credential: &str,
    ) -> Result<()> {
        let bytes = serde_json::to_vec(sub)?;
        self.seal_document(namespace, name, &bytes, credential)
    }

    /// Open a nested vault into memory with its `credential`.
    pub fn open_subvault(
        &self,
        namespace: &str,
        name: &str,
        credential: &str,
    ) -> Result<VaultContents> {
        let bytes = self.open_document(namespace, name, credential)?;
        Ok(serde_json::from_slice(&bytes)?)
    }

    fn upsert(&mut self, doc: Document) -> Result<()> {
        match self.doc_pos(&doc.namespace, &doc.name) {
            Some(i) => self.contents.documents[i] = doc,
            None => self.contents.documents.push(doc),
        }
        self.save()
    }

    fn save(&self) -> Result<()> {
        save(&self.path, &self.passphrase, &self.contents)
    }
}

/// Read + decrypt a vault file into its contents.
pub fn load(path: &Path, passphrase: &str) -> Result<VaultContents> {
    if !path.exists() {
        return Err(Web4Error::Vault(format!("vault not found: {}", path.display())));
    }
    let raw = fs::read(path).map_err(|e| Web4Error::Vault(format!("read {}: {e}", path.display())))?;
    if raw.len() < HEADER_LEN {
        return Err(Web4Error::Vault("file too short for header".into()));
    }
    if &raw[..4] != MAGIC {
        return Err(Web4Error::Vault("wrong magic bytes".into()));
    }
    if raw[4] != VERSION {
        return Err(Web4Error::Vault(format!("unsupported version: {}", raw[4])));
    }
    let mut salt = [0u8; 16];
    salt.copy_from_slice(&raw[5..21]);
    let mut nonce = [0u8; 12];
    nonce.copy_from_slice(&raw[21..33]);
    let key = crypto::derive_key(passphrase, &salt)?;
    let plaintext = crypto::decrypt(&key, &nonce, &raw[HEADER_LEN..])?;
    Ok(serde_json::from_slice(&plaintext)?)
}

/// Encrypt + atomically write vault contents. Fresh salt + nonce every write.
pub fn save(path: &Path, passphrase: &str, contents: &VaultContents) -> Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .map_err(|e| Web4Error::Vault(format!("mkdir {}: {e}", parent.display())))?;
    }
    let salt = crypto::generate_salt();
    let nonce = crypto::generate_nonce();
    let key = crypto::derive_key(passphrase, &salt)?;
    let plaintext = serde_json::to_vec(contents)?;
    let ciphertext = crypto::encrypt(&key, &nonce, &plaintext)?;

    let mut buffer = Vec::with_capacity(HEADER_LEN + ciphertext.len());
    buffer.extend_from_slice(MAGIC);
    buffer.push(VERSION);
    buffer.extend_from_slice(&salt);
    buffer.extend_from_slice(&nonce);
    buffer.extend_from_slice(&ciphertext);

    let tmp = path.with_extension("w4vt.tmp");
    {
        let mut f = File::create(&tmp).map_err(|e| Web4Error::Vault(format!("create tmp: {e}")))?;
        f.write_all(&buffer).map_err(|e| Web4Error::Vault(format!("write tmp: {e}")))?;
        f.sync_all().map_err(|e| Web4Error::Vault(format!("sync tmp: {e}")))?;
    }
    fs::rename(&tmp, path).map_err(|e| Web4Error::Vault(format!("rename: {e}")))?;

    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let mut perms = fs::metadata(path)
            .map_err(|e| Web4Error::Vault(format!("stat: {e}")))?
            .permissions();
        perms.set_mode(0o600);
        fs::set_permissions(path, perms).map_err(|e| Web4Error::Vault(format!("chmod: {e}")))?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn temp() -> (tempfile_path::TempLike, PathBuf) {
        let dir = tempfile_path::TempLike::new();
        let path = dir.path().join("v.w4vt");
        (dir, path)
    }

    #[test]
    fn master_doc_round_trips() {
        let (_d, path) = temp();
        let mut v = Vault::init(&path, "master").unwrap();
        v.put_document("config", "daemon", b"bind=127.0.0.1".to_vec()).unwrap();
        let v2 = Vault::open(&path, "master").unwrap();
        assert_eq!(v2.get_document("config", "daemon").unwrap(), b"bind=127.0.0.1");
        assert_eq!(v2.index()[0].protection, Protection::Master);
    }

    #[test]
    fn sealed_needs_its_own_credential() {
        let (_d, path) = temp();
        let mut v = Vault::init(&path, "master").unwrap();
        v.seal_document("identity", "sovereign_key", b"ed25519-secret", "second").unwrap();
        let v2 = Vault::open(&path, "master").unwrap();
        // Index shows it exists + sealed; master path can't read it.
        assert!(matches!(v2.index()[0].protection, Protection::Sealed { .. }));
        assert!(v2.get_document("identity", "sovereign_key").is_none());
        assert!(v2.open_document("identity", "sovereign_key", "master").is_err());
        let opened = v2.open_document("identity", "sovereign_key", "second").unwrap();
        assert_eq!(&*opened, b"ed25519-secret");
    }

    #[test]
    fn no_plaintext_on_disk() {
        const M: &[u8] = b"MASTER_MARK_web4_zzz";
        const S: &[u8] = b"SEALED_MARK_web4_qqq";
        let (_d, path) = temp();
        let mut v = Vault::init(&path, "master").unwrap();
        v.put_document("c", "m", M.to_vec()).unwrap();
        v.seal_document("c", "s", S, "cred").unwrap();
        let raw = fs::read(&path).unwrap();
        assert!(!raw.windows(M.len()).any(|w| w == M));
        assert!(!raw.windows(S.len()).any(|w| w == S));
    }

    #[test]
    fn subvault_recurses_and_locks_independently() {
        let (_d, path) = temp();
        let mut v = Vault::init(&path, "master").unwrap();
        let mut sub = VaultContents::default();
        sub.documents.push(Document::master("inner", "k", b"v".to_vec()));
        v.put_subvault("nested", "child", &sub, "sub-cred").unwrap();
        let v2 = Vault::open(&path, "master").unwrap();
        assert!(v2.open_subvault("nested", "child", "master").is_err());
        let opened = v2.open_subvault("nested", "child", "sub-cred").unwrap();
        assert_eq!(opened.documents[0].master_bytes().unwrap(), b"v");
    }

    /// Minimal temp-dir helper (web4-core has no tempfile dev-dep).
    mod tempfile_path {
        use std::path::{Path, PathBuf};
        pub struct TempLike(PathBuf);
        impl TempLike {
            pub fn new() -> Self {
                // Unique per-process+counter dir under the system temp dir.
                use std::sync::atomic::{AtomicU64, Ordering};
                static N: AtomicU64 = AtomicU64::new(0);
                let pid = std::process::id();
                let n = N.fetch_add(1, Ordering::Relaxed);
                let p = std::env::temp_dir().join(format!("w4vt-test-{pid}-{n}"));
                std::fs::create_dir_all(&p).unwrap();
                Self(p)
            }
            pub fn path(&self) -> &Path {
                &self.0
            }
        }
        impl Drop for TempLike {
            fn drop(&mut self) {
                let _ = std::fs::remove_dir_all(&self.0);
            }
        }
    }
}
