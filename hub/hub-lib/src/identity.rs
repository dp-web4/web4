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

    /// Plaintext JSON save. **Bootstrap/tests only** — production goes through
    /// [`save_encrypted`] (the daemon never writes a plaintext private key; see
    /// the vault doctrine). Caller owns filesystem permissions.
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

    /// Save the identity into an **encrypted** vault file (W4VT). The Ed25519
    /// private key never lands on disk in the clear. Keyed by `passphrase` — an
    /// empty passphrase is permitted (a deliberate operator choice: encrypted
    /// format with a publicly-derivable key, re-keyable later) but is never a
    /// silent default. The vault doctrine: production writes only this.
    pub fn save_encrypted(&self, path: impl AsRef<Path>, passphrase: &str) -> Result<()> {
        let path = path.as_ref();
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)
                .with_context(|| format!("creating parent dir {}", parent.display()))?;
        }
        let json = serde_json::to_vec(self).context("serializing identity")?;
        let mut vault = web4_core::vault::Vault::init_force(path.to_path_buf(), passphrase)
            .map_err(|e| anyhow::anyhow!("creating identity vault {}: {e}", path.display()))?;
        vault
            .put_document("identity", "sovereign", json)
            .map_err(|e| anyhow::anyhow!("writing identity into vault: {e}"))?;
        Ok(())
    }

    /// Load an identity from an encrypted vault file.
    pub fn load_encrypted(path: impl AsRef<Path>, passphrase: &str) -> Result<Self> {
        let path = path.as_ref();
        let vault = web4_core::vault::Vault::open(path.to_path_buf(), passphrase)
            .map_err(|e| anyhow::anyhow!("opening identity vault {}: {e}", path.display()))?;
        let bytes = vault
            .get_document("identity", "sovereign")
            .ok_or_else(|| anyhow::anyhow!("identity vault {} has no identity document", path.display()))?;
        serde_json::from_slice(bytes).context("parsing identity from vault")
    }

    /// Smart loader: encrypted vault files start with the `W4VT` magic; legacy
    /// plaintext identities are JSON. Sniffs and dispatches — encrypted files
    /// unlock with `HUB_PASSPHRASE` (an explicit empty value is a valid key).
    /// This is what production call sites use, so a pre-vault plaintext hub keeps
    /// loading (then migrate it once) and the doctrine path both work behind one
    /// path. Reading plaintext is allowed (back-compat / migration source); only
    /// *writing* plaintext is refused.
    pub fn load_auto(path: impl AsRef<Path>) -> Result<Self> {
        let path = path.as_ref();
        let raw = std::fs::read(path)
            .with_context(|| format!("reading identity file {}", path.display()))?;
        if raw.starts_with(b"W4VT") {
            let pass = env_passphrase().ok_or_else(|| anyhow::anyhow!(
                "identity at {} is an encrypted vault — set HUB_PASSPHRASE to unlock it \
                 (an empty value is allowed: HUB_PASSPHRASE=)",
                path.display()
            ))?;
            Self::load_encrypted(path, &pass)
        } else {
            serde_json::from_slice(&raw)
                .with_context(|| format!("parsing plaintext identity file {}", path.display()))
        }
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

/// Read-side passphrase from the environment. `Some(p)` if `HUB_PASSPHRASE` is
/// set — **including an empty string**, which is a deliberate no-passphrase
/// choice (encrypt-with-empty-key), NOT the same as unset. `None` only when the
/// variable is absent. The distinction is the whole point of the vault
/// doctrine: the system never silently falls back to plaintext; "no passphrase"
/// must be chosen explicitly. (Mirrors hestia's `HESTIA_PASSPHRASE`.)
pub fn env_passphrase() -> Option<String> {
    std::env::var("HUB_PASSPHRASE").ok()
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[tokio::test]
    async fn round_trip_save_load_sign_verify() {
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

    #[tokio::test]
    async fn generates_with_correct_entity_type() {
        let identity = IdentityFile::generate(EntityType::Human);
        assert_eq!(identity.lct.entity_type, EntityType::Human);

        let ai_identity = IdentityFile::generate(EntityType::AiSoftware);
        assert_eq!(ai_identity.lct.entity_type, EntityType::AiSoftware);
    }

    #[test]
    fn encrypted_round_trips_and_keeps_the_private_key_off_disk() {
        let dir = tempdir().unwrap();
        let path = dir.path().join("sovereign.vault");
        let id = IdentityFile::generate(EntityType::Human);

        id.save_encrypted(&path, "strong-pass").unwrap();
        // On disk: W4VT magic, and the secret key hex appears NOWHERE.
        let raw = std::fs::read(&path).unwrap();
        assert!(raw.starts_with(b"W4VT"), "must be an encrypted vault file");
        assert!(!String::from_utf8_lossy(&raw).contains(&id.secret_key_hex),
            "private key must never be plaintext on disk");

        let loaded = IdentityFile::load_encrypted(&path, "strong-pass").unwrap();
        assert_eq!(loaded.secret_key_hex, id.secret_key_hex);
        assert!(IdentityFile::load_encrypted(&path, "wrong").is_err(), "wrong passphrase → fail");
    }

    #[test]
    fn empty_passphrase_is_a_valid_deliberate_choice_still_encrypted() {
        // NULL passphrase (operator pressed return) — still produces an
        // encrypted vault file, never plaintext. The key is publicly derivable,
        // but the format is uniform and re-keyable; the point is no plaintext.
        let dir = tempdir().unwrap();
        let path = dir.path().join("id.vault");
        let id = IdentityFile::generate(EntityType::Human);
        id.save_encrypted(&path, "").unwrap();
        let raw = std::fs::read(&path).unwrap();
        assert!(raw.starts_with(b"W4VT"), "empty passphrase still encrypts (no plaintext)");
        let loaded = IdentityFile::load_encrypted(&path, "").unwrap();
        assert_eq!(loaded.secret_key_hex, id.secret_key_hex);
    }

    #[test]
    fn load_auto_sniffs_plaintext_vs_encrypted_and_empty_is_not_unset() {
        let dir = tempdir().unwrap();
        let id = IdentityFile::generate(EntityType::Human);

        // Plaintext (legacy / pre-migration) loads with no passphrase.
        let plain = dir.path().join("plain.json");
        id.save(&plain).unwrap();
        assert_eq!(IdentityFile::load_auto(&plain).unwrap().secret_key_hex, id.secret_key_hex);

        // Encrypted (empty passphrase) needs HUB_PASSPHRASE set — and an
        // explicit empty value unlocks it, while *unset* does not.
        let enc = dir.path().join("enc.vault");
        id.save_encrypted(&enc, "").unwrap();
        std::env::remove_var("HUB_PASSPHRASE");
        assert!(IdentityFile::load_auto(&enc).is_err(), "unset env must NOT silently open an encrypted vault");
        std::env::set_var("HUB_PASSPHRASE", ""); // explicit empty = a valid choice
        assert_eq!(IdentityFile::load_auto(&enc).unwrap().secret_key_hex, id.secret_key_hex);
        std::env::remove_var("HUB_PASSPHRASE");
    }
}
