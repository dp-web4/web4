// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-only
//
// This software is covered by US Patents 11,477,027 and 12,278,913,
// and pending application 19/178,619. A royalty-free license is granted
// under AGPL-3.0 terms for non-commercial and research use.
// For commercial licensing: dp@metalinxx.io
// See PATENTS.md for details.

//! Cryptographic primitives for Web4
//!
//! Provides Ed25519 key generation, signing, and verification.
//! All keys are designed to be hardware-bindable (TPM/SE) in production.

use crate::error::{Result, Web4Error};
use ed25519_dalek::{Signature, Signer, SigningKey, Verifier, VerifyingKey};
use rand::rngs::OsRng;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

/// A keypair for signing and verification
#[derive(Clone)]
pub struct KeyPair {
    signing_key: SigningKey,
}

impl KeyPair {
    /// Generate a new random keypair
    ///
    /// NOTE: In production, this should be hardware-bound (TPM/SE).
    /// Current implementation stores keys in memory only.
    pub fn generate() -> Self {
        let mut csprng = OsRng;
        let signing_key = SigningKey::generate(&mut csprng);
        Self { signing_key }
    }

    /// Create keypair from existing secret key bytes (32 bytes)
    pub fn from_secret_bytes(bytes: &[u8; 32]) -> Self {
        let signing_key = SigningKey::from_bytes(bytes);
        Self { signing_key }
    }

    /// Get the public key bytes
    pub fn public_key_bytes(&self) -> [u8; 32] {
        self.signing_key.verifying_key().to_bytes()
    }

    /// Get the secret key bytes
    ///
    /// WARNING: Handle with care. In production, this should never leave
    /// the hardware security module.
    pub fn secret_key_bytes(&self) -> [u8; 32] {
        self.signing_key.to_bytes()
    }

    /// Get the verifying (public) key
    pub fn verifying_key(&self) -> PublicKey {
        PublicKey {
            key: self.signing_key.verifying_key(),
        }
    }

    /// Sign a message
    pub fn sign(&self, message: &[u8]) -> SignatureBytes {
        let signature = self.signing_key.sign(message);
        SignatureBytes {
            bytes: signature.to_bytes(),
        }
    }
}

/// A public key for verification
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct PublicKey {
    #[serde(with = "public_key_serde")]
    key: VerifyingKey,
}

impl PublicKey {
    /// Create from bytes
    pub fn from_bytes(bytes: &[u8; 32]) -> Result<Self> {
        let key = VerifyingKey::from_bytes(bytes)
            .map_err(|e| Web4Error::Crypto(format!("Invalid public key: {}", e)))?;
        Ok(Self { key })
    }

    /// Get the raw bytes
    pub fn to_bytes(&self) -> [u8; 32] {
        self.key.to_bytes()
    }

    /// Verify a signature
    pub fn verify(&self, message: &[u8], signature: &SignatureBytes) -> Result<()> {
        let sig = Signature::from_bytes(&signature.bytes);
        self.key
            .verify(message, &sig)
            .map_err(|e| Web4Error::SignatureInvalid(format!("{}", e)))
    }

    /// Get hex-encoded public key (for display)
    pub fn to_hex(&self) -> String {
        hex::encode(&self.to_bytes())
    }
}

/// Signature bytes wrapper
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct SignatureBytes {
    #[serde(with = "hex_bytes")]
    pub bytes: [u8; 64],
}

impl SignatureBytes {
    /// Create from raw bytes
    pub fn from_bytes(bytes: [u8; 64]) -> Self {
        Self { bytes }
    }

    /// Get hex-encoded signature
    pub fn to_hex(&self) -> String {
        hex::encode(&self.bytes)
    }
}

/// Compute SHA-256 hash
pub fn sha256(data: &[u8]) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(data);
    hasher.finalize().into()
}

/// Compute SHA-256 hash and return as hex string
pub fn sha256_hex(data: &[u8]) -> String {
    hex::encode(&sha256(data))
}

// Serde helpers for VerifyingKey
mod public_key_serde {
    use super::hex;
    use ed25519_dalek::VerifyingKey;
    use serde::{Deserialize, Deserializer, Serializer};

    pub fn serialize<S>(key: &VerifyingKey, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let hex_str = hex::encode(&key.to_bytes());
        serializer.serialize_str(&hex_str)
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<VerifyingKey, D::Error>
    where
        D: Deserializer<'de>,
    {
        let hex_str = String::deserialize(deserializer)?;
        let bytes = hex::decode(&hex_str).map_err(serde::de::Error::custom)?;
        let arr: [u8; 32] = bytes
            .try_into()
            .map_err(|_| serde::de::Error::custom("Invalid public key length"))?;
        VerifyingKey::from_bytes(&arr).map_err(serde::de::Error::custom)
    }
}

// Serde helper for signature bytes
mod hex_bytes {
    use super::hex;
    use serde::{Deserialize, Deserializer, Serializer};

    pub fn serialize<S>(bytes: &[u8; 64], serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let hex_str = hex::encode(bytes);
        serializer.serialize_str(&hex_str)
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<[u8; 64], D::Error>
    where
        D: Deserializer<'de>,
    {
        let hex_str = String::deserialize(deserializer)?;
        let bytes = hex::decode(&hex_str).map_err(serde::de::Error::custom)?;
        bytes
            .try_into()
            .map_err(|_| serde::de::Error::custom("Invalid signature length"))
    }
}

// We need hex for encoding
mod hex {
    pub fn encode(bytes: &[u8]) -> String {
        bytes.iter().map(|b| format!("{:02x}", b)).collect()
    }

    pub fn decode(s: &str) -> Result<Vec<u8>, String> {
        if s.len() % 2 != 0 {
            return Err("Hex string must have even length".into());
        }
        (0..s.len())
            .step_by(2)
            .map(|i| {
                u8::from_str_radix(&s[i..i + 2], 16)
                    .map_err(|e| format!("Invalid hex: {}", e))
            })
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_keypair_generation() {
        let kp = KeyPair::generate();
        let public = kp.verifying_key();
        assert_eq!(public.to_bytes().len(), 32);
    }

    #[test]
    fn test_sign_verify() {
        let kp = KeyPair::generate();
        let message = b"Hello, Web4!";

        let signature = kp.sign(message);
        let public = kp.verifying_key();

        assert!(public.verify(message, &signature).is_ok());
    }

    #[test]
    fn test_verify_wrong_message() {
        let kp = KeyPair::generate();
        let signature = kp.sign(b"Original message");
        let public = kp.verifying_key();

        assert!(public.verify(b"Different message", &signature).is_err());
    }

    #[test]
    fn test_sha256() {
        let hash = sha256(b"test");
        assert_eq!(hash.len(), 32);

        // Known hash for "test"
        let hex = sha256_hex(b"test");
        assert_eq!(
            hex,
            "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
        );
    }

    #[test]
    fn test_public_key_serialization() {
        let kp = KeyPair::generate();
        let public = kp.verifying_key();

        let json = serde_json::to_string(&public).unwrap();
        let recovered: PublicKey = serde_json::from_str(&json).unwrap();

        assert_eq!(public, recovered);
    }
}
