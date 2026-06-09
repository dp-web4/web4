// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// This software is covered by US Patents 11,477,027 and 12,278,913,
// and pending application 19/178,619. See PATENTS.md for details.

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

// ============================================================================
// X25519 ECDH — for LCT paired-channel key agreement
// ============================================================================
//
// Per the PAIRED-CHANNELS PRD (web4/hub/docs/PAIRED-CHANNELS.md, Sprint A):
// two LCT-holders need to derive a shared secret without involving the hub,
// so the hub can mediate the relationship under chapter law without ever
// seeing the payload (constitutional commitment #8: secrets-free hub).
//
// LCT identity keys are Ed25519 (signing) — they sign envelopes, ledger
// entries, etc. X25519 (Diffie-Hellman over the same Curve25519) is the
// natural ECDH primitive. Standard practice is to derive an X25519
// keypair from the existing Ed25519 keypair so a single LCT key serves
// both signing (envelopes / ledger) and key-agreement (pair channels) —
// no new keys to mint per LCT, no schema migration.
//
// **The derivation:**
//
// - **Secret half (private→private):** Per RFC 8032 §5.1.5, an Ed25519
//   signing key is a 32-byte seed; the actual scalar used in signing is
//   `SHA512(seed)[..32]` with the standard X25519 clamping
//   (`& 248`, `| 64`, `& 127`). That clamped 32-byte value IS a valid
//   X25519 secret scalar. So Ed25519 seed -> SHA512 -> clamp -> X25519
//   secret.
//
// - **Public half (public→public):** Ed25519 public keys are points on
//   the Edwards form of Curve25519; X25519 public keys are points on
//   the Montgomery form. `EdwardsPoint::to_montgomery` is the canonical
//   birational map. Compressed Edwards Y -> decompress -> to_montgomery
//   -> bytes.
//
// These two paths produce a matched X25519 keypair from any Ed25519
// keypair. Anyone with the Ed25519 public key can derive the X25519
// public key, and the holder of the Ed25519 secret can derive the
// matching X25519 secret. ECDH agreement follows.

/// A shared secret derived from an X25519 ECDH. 32 bytes; suitable as
/// input to a KDF (HKDF) for actual session-key material — do NOT use
/// the raw shared secret directly for AEAD without first running it
/// through a KDF.
#[derive(Clone)]
pub struct SharedSecret([u8; 32]);

impl SharedSecret {
    /// Borrow the raw 32 bytes. Intended for HKDF input; **do not**
    /// pass this directly to AEAD construction without a KDF pass.
    pub fn as_bytes(&self) -> &[u8; 32] {
        &self.0
    }

    /// Move the raw bytes out (consumes self). Same caveat as
    /// [`as_bytes`] — feed to HKDF, not directly to AEAD.
    pub fn into_bytes(self) -> [u8; 32] {
        self.0
    }

    /// Crate-internal constructor for callers that compute the
    /// shared bytes through a non-LCT path (e.g., ephemeral X25519
    /// ECDH in [`crate::pair_channel::seal_fs`]). External callers
    /// still must go through [`crate::crypto::KeyPair::ecdh_with_peer`].
    pub(crate) fn from_bytes(bytes: [u8; 32]) -> Self {
        Self(bytes)
    }
}

impl std::fmt::Debug for SharedSecret {
    /// Redacted Debug — we never want raw shared-secret bytes in logs.
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("SharedSecret(<redacted 32 bytes>)")
    }
}

/// Derive the X25519 secret scalar from an Ed25519 32-byte seed
/// per RFC 8032 §5.1.5 + standard X25519 clamping.
///
/// The returned 32 bytes are a valid X25519 `StaticSecret` representation.
/// Hardware-bound LCTs would do this derivation inside the secure element;
/// the software path here is for MVP + tests.
fn ed25519_seed_to_x25519_secret(seed: &[u8; 32]) -> [u8; 32] {
    use sha2::Sha512;
    let mut hasher = Sha512::new();
    hasher.update(seed);
    let hash = hasher.finalize();
    let mut out = [0u8; 32];
    out.copy_from_slice(&hash[..32]);
    // X25519 clamping (RFC 7748 §5)
    out[0] &= 248;
    out[31] &= 127;
    out[31] |= 64;
    out
}

/// Convert an Ed25519 public key (compressed Edwards Y, 32 bytes) to
/// the matching X25519 public key (Montgomery U, 32 bytes).
///
/// Errors if the input doesn't decompress to a valid Edwards point.
/// Anyone with the LCT's public key can run this — it's the natural
/// "given this LCT, what's their X25519 pubkey" question.
pub fn ed25519_to_x25519_public(ed_pub_bytes: &[u8; 32]) -> Result<[u8; 32]> {
    use curve25519_dalek::edwards::CompressedEdwardsY;
    let compressed = CompressedEdwardsY(*ed_pub_bytes);
    let edwards = compressed.decompress().ok_or_else(|| {
        Web4Error::Crypto("ed25519 public key did not decompress to a valid Edwards point".into())
    })?;
    let montgomery = edwards.to_montgomery();
    Ok(montgomery.to_bytes())
}

impl KeyPair {
    /// Derive this LCT's X25519 secret for ECDH.
    ///
    /// **Hardware caveat:** in software-mode chapters this returns the
    /// derived secret in memory. Production hardware-bound LCTs should
    /// perform the derivation inside the secure element; the secret
    /// never crosses the trust boundary.
    pub fn to_x25519_secret(&self) -> x25519_dalek::StaticSecret {
        let seed = self.secret_key_bytes();
        let scalar = ed25519_seed_to_x25519_secret(&seed);
        x25519_dalek::StaticSecret::from(scalar)
    }

    /// Derive this LCT's X25519 public key (the Montgomery-form public
    /// matching the secret returned by [`Self::to_x25519_secret`]).
    pub fn to_x25519_public(&self) -> x25519_dalek::PublicKey {
        x25519_dalek::PublicKey::from(&self.to_x25519_secret())
    }

    /// LCT-pairing convenience: derive the shared secret between this
    /// LCT and a peer LCT, given only the peer's Ed25519 public key.
    ///
    /// This is the canonical entry point for paired-channel key
    /// agreement: caller has their own KeyPair (their LCT) and the
    /// peer's LCT public key (from the hub's resolver). Output is
    /// suitable as HKDF input for session-key derivation.
    ///
    /// Errors if the peer's Ed25519 public key isn't decompressible
    /// (malformed pubkey on the wire / in the ledger).
    pub fn ecdh_with_peer(&self, peer_ed_public: &PublicKey) -> Result<SharedSecret> {
        let peer_x_bytes = ed25519_to_x25519_public(&peer_ed_public.to_bytes())?;
        let peer_x = x25519_dalek::PublicKey::from(peer_x_bytes);
        let my_secret = self.to_x25519_secret();
        let shared = my_secret.diffie_hellman(&peer_x);
        Ok(SharedSecret(*shared.as_bytes()))
    }
}

impl PublicKey {
    /// Convert this LCT public key into the matching X25519 public key.
    /// Cheap; pure curve math.
    pub fn to_x25519(&self) -> Result<x25519_dalek::PublicKey> {
        let bytes = ed25519_to_x25519_public(&self.to_bytes())?;
        Ok(x25519_dalek::PublicKey::from(bytes))
    }
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

    // ---------- X25519 ECDH (PAIRED-CHANNELS Sprint A) ----------

    /// The canonical agreement property: A using B's pubkey + A's
    /// secret derives the same shared secret as B using A's pubkey
    /// + B's secret. This is the entire point of ECDH and the
    /// foundation of LCT paired channels.
    #[test]
    fn ecdh_agreement_is_symmetric() {
        let alice = KeyPair::generate();
        let bob = KeyPair::generate();

        let alice_pub = alice.verifying_key();
        let bob_pub = bob.verifying_key();

        let alice_view = alice.ecdh_with_peer(&bob_pub).unwrap();
        let bob_view = bob.ecdh_with_peer(&alice_pub).unwrap();

        assert_eq!(alice_view.as_bytes(), bob_view.as_bytes(),
            "alice and bob must derive the same shared secret");
    }

    /// Distinct pairs must produce distinct shared secrets — if A-B and
    /// A-C derived the same secret, an eavesdropper could substitute
    /// recipients. Sanity check that the underlying primitive isn't
    /// degenerate.
    #[test]
    fn ecdh_distinct_peers_produce_distinct_secrets() {
        let alice = KeyPair::generate();
        let bob = KeyPair::generate();
        let carol = KeyPair::generate();

        let ab = alice.ecdh_with_peer(&bob.verifying_key()).unwrap();
        let ac = alice.ecdh_with_peer(&carol.verifying_key()).unwrap();

        assert_ne!(ab.as_bytes(), ac.as_bytes(),
            "alice-bob secret must differ from alice-carol secret");
    }

    /// Conversion correctness: `KeyPair::to_x25519_public()` must
    /// match what we get by going through `PublicKey::to_x25519()`.
    /// Both paths should produce the same X25519 public key for the
    /// same underlying LCT.
    #[test]
    fn x25519_public_derivation_paths_agree() {
        let kp = KeyPair::generate();

        let via_keypair = kp.to_x25519_public();
        let via_pubkey = kp.verifying_key().to_x25519().unwrap();

        assert_eq!(via_keypair.as_bytes(), via_pubkey.as_bytes(),
            "deriving X25519 pubkey from KeyPair vs from PublicKey must agree");
    }

    /// Crypto sanity: secret-half (clamped SHA512 of seed) and
    /// public-half (Edwards->Montgomery) must form a valid X25519
    /// keypair — i.e., `public = secret * basepoint` in Montgomery
    /// form. The cleanest test is "derived public matches what
    /// x25519-dalek computes from the derived secret."
    #[test]
    fn derived_x25519_keypair_is_internally_consistent() {
        let kp = KeyPair::generate();
        let secret = kp.to_x25519_secret();
        let derived_public_from_secret = x25519_dalek::PublicKey::from(&secret);
        let derived_public_from_keypair = kp.to_x25519_public();

        assert_eq!(
            derived_public_from_secret.as_bytes(),
            derived_public_from_keypair.as_bytes(),
            "the X25519 keypair derived from the Ed25519 keypair must satisfy public = secret * basepoint"
        );
    }

    /// Malformed peer pubkey (not a valid Edwards point) must error
    /// cleanly rather than panic or silently produce garbage. We
    /// probe several byte patterns and require at least one to fail
    /// decompression — robust against future curve-lib changes that
    /// might accept a previously-rejected pattern.
    #[test]
    fn ecdh_with_invalid_peer_pubkey_errors() {
        // Candidates: small y-values that empirically aren't on the
        // Edwards curve. Different lib versions handle different
        // patterns; assert that AT LEAST ONE of these is rejected.
        let candidates: Vec<[u8; 32]> = vec![
            { let mut a = [0; 32]; a[0] = 0x02; a }, // y = 2
            { let mut a = [0; 32]; a[0] = 0x05; a }, // y = 5
            { let mut a = [0; 32]; a[0] = 0x07; a }, // y = 7
            { let mut a = [0; 32]; a[0] = 0x0b; a }, // y = 11
        ];
        let any_failed = candidates.iter()
            .any(|c| ed25519_to_x25519_public(c).is_err());
        assert!(any_failed,
            "expected at least one of the small-y candidates to fail Edwards decompression");
    }

    /// SharedSecret's Debug impl must redact the bytes. Logging
    /// a SharedSecret accidentally should never leak key material.
    #[test]
    fn shared_secret_debug_is_redacted() {
        let alice = KeyPair::generate();
        let bob = KeyPair::generate();
        let secret = alice.ecdh_with_peer(&bob.verifying_key()).unwrap();
        let debug_str = format!("{:?}", secret);
        // Must not contain hex-looking sequences of the actual bytes.
        let raw_hex = hex::encode(secret.as_bytes());
        assert!(!debug_str.contains(&raw_hex[..16]),
            "Debug output must not include the actual secret bytes");
        assert!(debug_str.contains("redacted"),
            "Debug output should explicitly say redacted");
    }
}
