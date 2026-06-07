// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! On-disk LCT + KeyPair persistence.
//!
//! Sprint 1 stores both the public LCT and the private signing key in a
//! single JSON file for simplicity. Sprint 6 polish may split into
//! public/private file pair with restricted permissions on the secret file.
//!
//! The file format intentionally mirrors web4-core's serde-derived
//! representation so a future move of this format into web4-core proper is
//! trivial — we're not inventing a new format, we're persisting the
//! existing one.

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::path::Path;
use web4_core::crypto::KeyPair;
use web4_core::lct::{EntityType, Lct};

/// On-disk representation of an LCT plus its signing keypair.
///
/// Contains private key material — protect the file (mode 0600 on Unix
/// recommended; not enforced in MVP).
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct IdentityFile {
    /// Public LCT — serializes via web4-core's existing Serialize impl.
    pub lct: Lct,

    /// Secret signing key, hex-encoded (32 bytes → 64 hex chars).
    pub secret_key_hex: String,
}

impl IdentityFile {
    /// Create a fresh LCT + keypair for the given entity type.
    pub fn generate(entity_type: EntityType) -> Self {
        let (lct, keypair) = Lct::new(entity_type, None);
        Self::from_parts(lct, keypair)
    }

    /// Wrap an existing LCT + keypair.
    pub fn from_parts(lct: Lct, keypair: KeyPair) -> Self {
        Self {
            lct,
            secret_key_hex: hex::encode(keypair.secret_key_bytes()),
        }
    }

    /// Save to a JSON file. Caller is responsible for filesystem permissions.
    pub fn save(&self, path: impl AsRef<Path>) -> Result<()> {
        let path = path.as_ref();
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)
                .with_context(|| format!("creating parent dir {}", parent.display()))?;
        }
        let json = serde_json::to_string_pretty(self)
            .context("serializing identity file")?;
        std::fs::write(path, json)
            .with_context(|| format!("writing identity file {}", path.display()))?;
        Ok(())
    }

    /// Load from a JSON file.
    pub fn load(path: impl AsRef<Path>) -> Result<Self> {
        let path = path.as_ref();
        let json = std::fs::read_to_string(path)
            .with_context(|| format!("reading identity file {}", path.display()))?;
        let identity: Self = serde_json::from_str(&json)
            .with_context(|| format!("parsing identity file {}", path.display()))?;
        Ok(identity)
    }

    /// Reconstruct the in-memory KeyPair from the stored hex.
    pub fn keypair(&self) -> Result<KeyPair> {
        let bytes = hex::decode(&self.secret_key_hex)
            .context("decoding secret_key_hex")?;
        let arr: [u8; 32] = bytes.as_slice().try_into()
            .map_err(|_| anyhow::anyhow!("secret key must be exactly 32 bytes"))?;
        Ok(KeyPair::from_secret_bytes(&arr))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn round_trip_save_load_sign_verify() {
        let dir = tempdir().unwrap();
        let path = dir.path().join("sovereign.json");

        // Generate, save
        let identity = IdentityFile::generate(EntityType::Human);
        identity.save(&path).unwrap();

        // Load, reconstruct keypair, sign + verify against the loaded LCT
        let loaded = IdentityFile::load(&path).unwrap();
        let keypair = loaded.keypair().unwrap();
        let message = b"hub sprint 1 round-trip";
        let sig = keypair.sign(message);

        loaded.lct.verify_signature(message, &sig)
            .expect("signature must verify against the loaded LCT");

        // Original LCT also verifies (same key material)
        identity.lct.verify_signature(message, &sig)
            .expect("signature must verify against the original LCT");
    }

    #[test]
    fn generates_with_correct_entity_type() {
        let identity = IdentityFile::generate(EntityType::Human);
        assert_eq!(identity.lct.entity_type, EntityType::Human);

        let ai_identity = IdentityFile::generate(EntityType::AiSoftware);
        assert_eq!(ai_identity.lct.entity_type, EntityType::AiSoftware);
    }
}
