// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later

//! Vault crypto primitives — Argon2id KDF + ChaCha20-Poly1305 AEAD.
//!
//! Shared substrate for the recursive in-memory vault used by hub / hestia /
//! hardbound (see `dev-hub/design/recursive-vault.md`). Argon2id (m=64MB, t=3,
//! p=4) derives a 32-byte key from a passphrase + salt; ChaCha20-Poly1305 seals
//! the payload. The `DerivedKey` zeroizes on drop.

use argon2::{Algorithm, Argon2, Params, Version};
use chacha20poly1305::{
    aead::{Aead, KeyInit},
    ChaCha20Poly1305, Key, Nonce,
};
use rand::RngCore;
use zeroize::Zeroize;

use crate::error::{Result, Web4Error};

const ARGON_M_COST_KIB: u32 = 64 * 1024; // 64 MB
const ARGON_T_COST: u32 = 3;
const ARGON_P_COST: u32 = 4;

/// A 32-byte ChaCha20 key derived from a passphrase via Argon2id. Zeroized on
/// drop so derived key material doesn't linger in memory.
pub struct DerivedKey([u8; 32]);

impl DerivedKey {
    pub fn as_bytes(&self) -> &[u8; 32] {
        &self.0
    }

    /// Wrap a raw 32-byte key (e.g. derived once and cached, or unsealed from
    /// hardware) so it can be used with [`encrypt`]/[`decrypt`]/[`seal`].
    pub fn from_bytes(bytes: [u8; 32]) -> Self {
        DerivedKey(bytes)
    }
}

impl Drop for DerivedKey {
    fn drop(&mut self) {
        self.0.zeroize();
    }
}

/// Derive a 32-byte symmetric key from a passphrase + salt (Argon2id).
pub fn derive_key(passphrase: &str, salt: &[u8]) -> Result<DerivedKey> {
    let params = Params::new(ARGON_M_COST_KIB, ARGON_T_COST, ARGON_P_COST, Some(32))
        .map_err(|e| Web4Error::Crypto(format!("argon2 params: {e}")))?;
    let argon = Argon2::new(Algorithm::Argon2id, Version::V0x13, params);
    let mut key = [0u8; 32];
    argon
        .hash_password_into(passphrase.as_bytes(), salt, &mut key)
        .map_err(|e| Web4Error::Crypto(format!("argon2 derive: {e}")))?;
    Ok(DerivedKey(key))
}

/// Generate a 16-byte random salt.
pub fn generate_salt() -> [u8; 16] {
    let mut salt = [0u8; 16];
    rand::rngs::OsRng.fill_bytes(&mut salt);
    salt
}

/// Generate a 12-byte random nonce.
pub fn generate_nonce() -> [u8; 12] {
    let mut nonce = [0u8; 12];
    rand::rngs::OsRng.fill_bytes(&mut nonce);
    nonce
}

/// Encrypt `plaintext` with `key` + `nonce`. Output includes the auth tag.
pub fn encrypt(key: &DerivedKey, nonce: &[u8; 12], plaintext: &[u8]) -> Result<Vec<u8>> {
    ChaCha20Poly1305::new(Key::from_slice(key.as_bytes()))
        .encrypt(Nonce::from_slice(nonce), plaintext)
        .map_err(|e| Web4Error::Crypto(format!("encrypt: {e}")))
}

/// Decrypt `ciphertext` with `key` + `nonce`. Fails on wrong key/tamper.
pub fn decrypt(key: &DerivedKey, nonce: &[u8; 12], ciphertext: &[u8]) -> Result<Vec<u8>> {
    ChaCha20Poly1305::new(Key::from_slice(key.as_bytes()))
        .decrypt(Nonce::from_slice(nonce), ciphertext)
        .map_err(|_| Web4Error::DecryptionFailed)
}

/// Self-framing seal: encrypt `plaintext` under `key` with a fresh random nonce,
/// returning `nonce(12) || ciphertext`. The companion [`open`] reverses it. For
/// callers that want to encrypt individual blobs (a file, a ledger line) with a
/// key they already hold, without managing nonces themselves.
pub fn seal(key: &DerivedKey, plaintext: &[u8]) -> Result<Vec<u8>> {
    let nonce = generate_nonce();
    let ct = encrypt(key, &nonce, plaintext)?;
    let mut out = Vec::with_capacity(12 + ct.len());
    out.extend_from_slice(&nonce);
    out.extend_from_slice(&ct);
    Ok(out)
}

/// Reverse [`seal`]: split `nonce(12) || ciphertext` and decrypt.
pub fn open(key: &DerivedKey, blob: &[u8]) -> Result<Vec<u8>> {
    if blob.len() < 12 {
        return Err(Web4Error::Vault("sealed blob too short".into()));
    }
    let nonce: [u8; 12] = blob[..12].try_into().expect("checked len");
    decrypt(key, &nonce, &blob[12..])
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn derive_is_deterministic_and_salt_sensitive() {
        let s1 = generate_salt();
        let s2 = generate_salt();
        assert_ne!(s1, s2);
        assert_eq!(
            derive_key("pw", &s1).unwrap().as_bytes(),
            derive_key("pw", &s1).unwrap().as_bytes()
        );
        assert_ne!(
            derive_key("pw", &s1).unwrap().as_bytes(),
            derive_key("pw", &s2).unwrap().as_bytes()
        );
    }

    #[test]
    fn seal_open_round_trip_with_raw_key() {
        let key = DerivedKey::from_bytes([9u8; 32]);
        let blob = seal(&key, b"ledger entry").unwrap();
        // nonce(12) framing + ciphertext+tag; not the plaintext.
        assert!(blob.len() > 12);
        assert_ne!(&blob[12..], b"ledger entry");
        assert_eq!(open(&key, &blob).unwrap(), b"ledger entry");
        // Wrong key fails.
        assert!(matches!(
            open(&DerivedKey::from_bytes([1u8; 32]), &blob),
            Err(Web4Error::DecryptionFailed)
        ));
    }

    #[test]
    fn encrypt_decrypt_round_trip_and_tamper_rejected() {
        let salt = generate_salt();
        let nonce = generate_nonce();
        let key = derive_key("pw", &salt).unwrap();
        let mut ct = encrypt(&key, &nonce, b"secret").unwrap();
        assert_eq!(decrypt(&key, &nonce, &ct).unwrap(), b"secret");
        ct[0] ^= 0xff;
        assert!(matches!(decrypt(&key, &nonce, &ct), Err(Web4Error::DecryptionFailed)));
    }
}
