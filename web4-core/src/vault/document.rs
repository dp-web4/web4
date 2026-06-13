// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later

//! Vault documents + the per-item protection model that makes the vault
//! recursive. A `Document` is a non-credential item (config / metadata / state /
//! identity) enclosed in the vault instead of a plaintext sidecar file.
//!
//! - `Master`  — readable with the outer unlock (the basics).
//! - `Sealed`  — encrypted under an INDEPENDENT credential; the outer unlock
//!   reveals only that the item exists. `open()` decrypts INTO MEMORY (a
//!   zeroizing buffer) and returns it; nothing decrypted touches disk.
//!
//! A sealed document whose plaintext is itself a serialized vault is a
//! sub-vault — the recursion.

use serde::{Deserialize, Serialize};
use zeroize::Zeroizing;

use super::crypto::{decrypt, derive_key, encrypt, generate_nonce, generate_salt};
use crate::error::Result;

/// How a vault item is protected *beyond* the outer master encryption.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum Protection {
    /// Readable with the outer master unlock. Bytes are protected only by the
    /// whole-vault encryption.
    Master,
    /// Encrypted under an INDEPENDENT credential. The outer unlock reveals the
    /// item's existence + metadata but NOT its plaintext. Carries its own KDF
    /// salt + AEAD nonce.
    Sealed { salt: [u8; 16], nonce: [u8; 12] },
    // Liveness { .. } — SITL-gated; opening will require a satisfying
    // PresenceProof (constellation-MFA verifier kept private). Not yet impl'd.
}

/// A non-credential vault item. `namespace` groups items (e.g. "config",
/// "identity"); `name` is unique within a namespace.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Document {
    pub namespace: String,
    pub name: String,
    pub protection: Protection,
    /// `Master`: plaintext (inside the outer-encrypted vault). `Sealed`: inner
    /// ciphertext (AEAD tag included) — never cleartext.
    payload: Vec<u8>,
}

impl Document {
    /// A master-tier document — plaintext held inside the outer-encrypted vault.
    pub fn master(namespace: impl Into<String>, name: impl Into<String>, bytes: Vec<u8>) -> Self {
        Self {
            namespace: namespace.into(),
            name: name.into(),
            protection: Protection::Master,
            payload: bytes,
        }
    }

    /// Seal `bytes` under an INDEPENDENT `credential`. Plaintext is encrypted now
    /// and never stored in the clear; opening requires the same credential.
    pub fn sealed(
        namespace: impl Into<String>,
        name: impl Into<String>,
        bytes: &[u8],
        credential: &str,
    ) -> Result<Self> {
        let salt = generate_salt();
        let nonce = generate_nonce();
        let key = derive_key(credential, &salt)?;
        let payload = encrypt(&key, &nonce, bytes)?;
        Ok(Self {
            namespace: namespace.into(),
            name: name.into(),
            protection: Protection::Sealed { salt, nonce },
            payload,
        })
    }

    pub fn is_sealed(&self) -> bool {
        matches!(self.protection, Protection::Sealed { .. })
    }

    /// Master-tier plaintext, if this is a `Master` document. `None` for sealed.
    pub fn master_bytes(&self) -> Option<&[u8]> {
        match self.protection {
            Protection::Master => Some(self.payload.as_slice()),
            _ => None,
        }
    }

    /// Decrypt INTO MEMORY. `Master`: a copy of the plaintext. `Sealed`: derive
    /// the key from `credential` and decrypt. Returns a zeroizing buffer that
    /// never touches disk.
    pub fn open(&self, credential: &str) -> Result<Zeroizing<Vec<u8>>> {
        match &self.protection {
            Protection::Master => Ok(Zeroizing::new(self.payload.clone())),
            Protection::Sealed { salt, nonce } => {
                let key = derive_key(credential, salt)?;
                Ok(Zeroizing::new(decrypt(&key, nonce, &self.payload)?))
            }
        }
    }
}

/// One row of the vault's content *index*: enough to enumerate and reason about
/// an item after the outer unlock, without exposing sealed plaintext.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ItemRef {
    pub namespace: String,
    pub name: String,
    pub protection: Protection,
}

impl From<&Document> for ItemRef {
    fn from(d: &Document) -> Self {
        Self {
            namespace: d.namespace.clone(),
            name: d.name.clone(),
            protection: d.protection.clone(),
        }
    }
}
