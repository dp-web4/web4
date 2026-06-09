// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later

//! PAIRED-CHANNELS Sprint E: end-to-end encryption for LCT pair messages.
//!
//! Composes the Sprint A ECDH primitive (`KeyPair::ecdh_with_peer`)
//! with HKDF-SHA256 (session-key derivation) + ChaCha20-Poly1305 AEAD
//! (payload encryption + authentication). This is the moment "the hub
//! cannot read content" stops being aspirational — the seal/open
//! happens entirely at endpoints; the hub stores opaque ciphertext.
//!
//! ## Key derivation
//!
//! ```text
//! shared_secret = ECDH(my_x25519_secret, peer_x25519_public)
//! session_key   = HKDF-SHA256(
//!                     salt = pair_id_bytes,            // pair-distinguishing salt
//!                     ikm  = shared_secret,
//!                     info = "web4-paired-channel-v1",
//!                     L    = 32 bytes,
//!                 )
//! ```
//!
//! The salt being `pair_id` addresses the open question in the PRD
//! (§8.1): two LCTs can have multiple distinct pairs without session-key
//! reuse — the same shared secret produces a different session key per
//! pair. Both endpoints know `pair_id` from the hub (it's metadata),
//! so they derive identical session keys without coordination.
//!
//! ## Wire format
//!
//! ```text
//! sealed = nonce_12_bytes || ciphertext_n_bytes
//! ```
//!
//! ChaCha20-Poly1305 uses a 12-byte nonce. The ciphertext includes
//! the 16-byte Poly1305 authentication tag at the end (AEAD-attached,
//! per the standard). At the wire layer (over JSON to the hub), the
//! sealed bytes are base64-encoded — that part's the caller's
//! responsibility (`Sealed::to_base64` / `Sealed::from_base64` are
//! provided as convenience).
//!
//! ## Nonce strategy (Sprint E MVP)
//!
//! Random 12-byte nonce per message. With 2^96 possible nonces and
//! ChaCha20-Poly1305's birthday-bound at 2^48 messages per key,
//! collision probability is negligible at any practical message
//! volume. Sprint F adds proper per-session counter nonces + ephemeral
//! ratchet keys for forward secrecy; Sprint E is the static-key
//! baseline.
//!
//! ## What this gives you
//!
//! - **Confidentiality:** hub stores opaque ciphertext; only the two
//!   pair participants can decrypt.
//! - **Integrity / authenticity-of-payload:** AEAD detects tampering
//!   (the Poly1305 tag fails if a byte flips). Authenticity-of-sender
//!   still rides the *envelope* signature at the REST layer — the
//!   AEAD only proves "whoever knew the session key wrote this," which
//!   the envelope signature pins to a specific LCT.
//!
//! ## What this does NOT give you (deferred)
//!
//! - **Forward secrecy** — Sprint F. If an LCT's static key is later
//!   compromised, an attacker who captured past ciphertexts can derive
//!   the session key and decrypt them. Sprint F's ephemeral-key
//!   ratchet closes this.
//! - **Future secrecy / post-compromise security** — full Signal
//!   double-ratchet, deferred per the PRD §6 out-of-scope list.
//! - **Group channels** — 2-party only.

use crate::crypto::{KeyPair, PublicKey, SharedSecret};
use crate::error::{Result, Web4Error};
use chacha20poly1305::{
    aead::{Aead, KeyInit},
    ChaCha20Poly1305, Key, Nonce,
};
use hkdf::Hkdf;
use rand::RngCore;
use sha2::Sha256;
use uuid::Uuid;

/// Info-string for HKDF. Bump the version suffix if the derivation
/// inputs / output usage ever changes — it's a clean way to enforce
/// that old session keys can't be accidentally repurposed.
const HKDF_INFO: &[u8] = b"web4-paired-channel-v1";

/// ChaCha20-Poly1305 nonce length per the AEAD construction. The
/// `chacha20poly1305` crate's type system also enforces this.
const NONCE_LEN: usize = 12;

/// A 32-byte session key derived from an ECDH shared secret +
/// pair_id salt. Carries a redacted Debug like SharedSecret.
#[derive(Clone)]
pub struct SessionKey([u8; 32]);

impl SessionKey {
    pub fn as_bytes(&self) -> &[u8; 32] { &self.0 }
}

impl std::fmt::Debug for SessionKey {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("SessionKey(<redacted 32 bytes>)")
    }
}

/// A sealed pair message: 12-byte nonce prefix + ciphertext (with
/// trailing 16-byte Poly1305 tag). Caller transports the raw bytes
/// (typically base64 over JSON to the hub).
#[derive(Clone, Debug)]
pub struct Sealed(Vec<u8>);

impl Sealed {
    /// Raw on-wire bytes: nonce ‖ ciphertext.
    pub fn as_bytes(&self) -> &[u8] { &self.0 }

    /// Move out the raw bytes.
    pub fn into_bytes(self) -> Vec<u8> { self.0 }

    /// Convenience: base64-encode for JSON transport.
    pub fn to_base64(&self) -> String {
        use base64::Engine;
        base64::engine::general_purpose::STANDARD.encode(&self.0)
    }

    /// Convenience: parse from base64.
    pub fn from_base64(s: &str) -> Result<Self> {
        use base64::Engine;
        let bytes = base64::engine::general_purpose::STANDARD
            .decode(s)
            .map_err(|e| Web4Error::Crypto(format!("base64 decode: {}", e)))?;
        if bytes.len() < NONCE_LEN + 16 {
            return Err(Web4Error::Crypto(
                format!("sealed blob too short: {} bytes < nonce+tag = {}",
                    bytes.len(), NONCE_LEN + 16)
            ));
        }
        Ok(Self(bytes))
    }

    /// Construct from raw bytes (skip base64). Validates min length.
    pub fn from_bytes(bytes: Vec<u8>) -> Result<Self> {
        if bytes.len() < NONCE_LEN + 16 {
            return Err(Web4Error::Crypto(
                format!("sealed blob too short: {} bytes < nonce+tag = {}",
                    bytes.len(), NONCE_LEN + 16)
            ));
        }
        Ok(Self(bytes))
    }
}

/// Derive the per-pair session key from an ECDH shared secret + the
/// pair's identifier. Both endpoints can do this independently from
/// public information (peer's LCT pubkey, pair_id from the hub) +
/// their own private key.
pub fn derive_session_key(shared: &SharedSecret, pair_id: Uuid) -> SessionKey {
    let hk = Hkdf::<Sha256>::new(Some(pair_id.as_bytes()), shared.as_bytes());
    let mut okm = [0u8; 32];
    // HKDF-Expand can only fail for L > 255*HashLen, which we're nowhere near.
    hk.expand(HKDF_INFO, &mut okm)
        .expect("HKDF expand for 32 bytes never fails");
    SessionKey(okm)
}

/// Encrypt `plaintext` under `session_key` with a fresh random nonce.
/// Output is `nonce || ciphertext_with_tag` wrapped in `Sealed`.
pub fn encrypt(session_key: &SessionKey, plaintext: &[u8]) -> Result<Sealed> {
    let cipher = ChaCha20Poly1305::new(Key::from_slice(session_key.as_bytes()));
    let mut nonce_bytes = [0u8; NONCE_LEN];
    rand::thread_rng().fill_bytes(&mut nonce_bytes);
    let nonce = Nonce::from_slice(&nonce_bytes);
    let ciphertext = cipher.encrypt(nonce, plaintext)
        .map_err(|e| Web4Error::Crypto(format!("ChaCha20-Poly1305 encrypt: {}", e)))?;
    let mut out = Vec::with_capacity(NONCE_LEN + ciphertext.len());
    out.extend_from_slice(&nonce_bytes);
    out.extend_from_slice(&ciphertext);
    Ok(Sealed(out))
}

/// Decrypt a `Sealed` blob under `session_key`. Returns plaintext on
/// success; errors (AEAD authentication failed) if the ciphertext was
/// tampered or the wrong session key was used.
pub fn decrypt(session_key: &SessionKey, sealed: &Sealed) -> Result<Vec<u8>> {
    let bytes = sealed.as_bytes();
    if bytes.len() < NONCE_LEN + 16 {
        return Err(Web4Error::Crypto("sealed blob too short".into()));
    }
    let (nonce_bytes, ciphertext) = bytes.split_at(NONCE_LEN);
    let cipher = ChaCha20Poly1305::new(Key::from_slice(session_key.as_bytes()));
    let nonce = Nonce::from_slice(nonce_bytes);
    cipher.decrypt(nonce, ciphertext)
        .map_err(|e| Web4Error::Crypto(format!("ChaCha20-Poly1305 decrypt: {}", e)))
}

/// End-to-end convenience: given my LCT keypair, the peer's LCT
/// public key, the pair_id, and a plaintext — produce a sealed blob
/// the recipient can [`open`] using the symmetric inverse path.
pub fn seal(my: &KeyPair, peer: &PublicKey, pair_id: Uuid, plaintext: &[u8]) -> Result<Sealed> {
    let shared = my.ecdh_with_peer(peer)?;
    let key = derive_session_key(&shared, pair_id);
    encrypt(&key, plaintext)
}

/// End-to-end convenience: given my LCT keypair, the peer's LCT
/// public key, the pair_id, and a sealed blob — recover the plaintext.
pub fn open(my: &KeyPair, peer: &PublicKey, pair_id: Uuid, sealed: &Sealed) -> Result<Vec<u8>> {
    let shared = my.ecdh_with_peer(peer)?;
    let key = derive_session_key(&shared, pair_id);
    decrypt(&key, sealed)
}

// ============================================================================
// PAIRED-CHANNELS Sprint F — Forward secrecy via ephemeral session keys
// ============================================================================
//
// Sprint E used a static-key ECDH only:
//
//     shared = ECDH(my_lct_secret, peer_lct_public)
//     key    = HKDF(salt=pair_id, ikm=shared, info=...)
//
// Compromise of the LCT static key (after the fact) + captured
// ciphertexts → attacker derives `shared` and decrypts everything.
// No forward secrecy.
//
// Sprint F mixes in an **ephemeral X25519 keypair per pair-session**
// (generated when the pair is confirmed; destroyed when the session
// ends). Each party publishes their ephemeral public to the ledger
// (in PairingRequested / PairingConfirmed); both parties keep their
// own ephemeral SECRET locally. The session key derivation becomes:
//
//     static_shared    = ECDH(my_lct_secret, peer_lct_public)
//     ephemeral_shared = ECDH(my_eph_secret, peer_eph_public)
//     ikm              = static_shared || ephemeral_shared
//     key              = HKDF(salt=pair_id, ikm, info="web4-paired-channel-v2")
//
// Both shareds are needed to derive the key. An attacker who later
// compromises the LCT static keys but never had access to the
// ephemeral secrets cannot derive the key — past sessions remain
// confidential. (Future secrecy / post-compromise security would
// require Signal-style per-message ratcheting, deferred per the
// PRD §6 out-of-scope list.)
//
// **What "session" means here:** the lifetime of the pair. One
// ephemeral key per pair, kept alive for the pair's duration. When
// the pair is revoked or expires, both parties wipe their ephemeral
// secrets. Sprint F-confirmed pairs that haven't been revoked yet
// retain forward secrecy as long as the endpoints actually wipe.
// (Endpoint discipline; hub can't enforce.)
//
// Wire format unchanged: still `nonce ‖ ciphertext_with_tag`. The
// derivation is different but the AEAD output looks identical, so
// the hub-side relay code (rest.rs) needs no changes.

/// Info-string for the Sprint F derivation. Distinct from v1 so an
/// attacker can't try to mix-and-match a v1 session key onto a v2
/// ciphertext (domain separation).
const HKDF_INFO_V2: &[u8] = b"web4-paired-channel-v2";

/// An ephemeral X25519 keypair for one pair-session. Caller must
/// persist the secret locally (we never put it on the wire) and
/// publish the public via PairingRequested / PairingConfirmed.
///
/// When the pair ends, drop this struct (and any local copies of
/// `secret_hex`) to honor forward secrecy.
pub struct EphemeralKeyPair {
    secret: x25519_dalek::StaticSecret,
    public: x25519_dalek::PublicKey,
}

impl EphemeralKeyPair {
    /// Generate a fresh ephemeral keypair from the OS RNG. One per
    /// pair-session; do NOT reuse across pairs (no advantage, and
    /// any reuse weakens the forward-secrecy claim).
    pub fn generate() -> Self {
        let secret = x25519_dalek::StaticSecret::random_from_rng(&mut rand::thread_rng());
        let public = x25519_dalek::PublicKey::from(&secret);
        Self { secret, public }
    }

    pub fn public_bytes(&self) -> [u8; 32] {
        *self.public.as_bytes()
    }

    /// 32-byte secret as hex for local persistence. Endpoint
    /// implementations save this alongside their PairState; wipe
    /// the file when the pair is revoked.
    pub fn secret_hex(&self) -> String {
        hex_encode(&self.secret.to_bytes())
    }

    pub fn public_hex(&self) -> String {
        hex_encode(self.public.as_bytes())
    }

    /// Reconstruct from a secret hex string (matched output of
    /// `secret_hex`). Errors on bad hex or wrong length.
    pub fn from_secret_hex(s: &str) -> Result<Self> {
        let bytes = hex_decode(s)?;
        let arr: [u8; 32] = bytes.as_slice().try_into()
            .map_err(|_| Web4Error::Crypto(
                format!("ephemeral secret must be 32 bytes, got {}", bytes.len())
            ))?;
        let secret = x25519_dalek::StaticSecret::from(arr);
        let public = x25519_dalek::PublicKey::from(&secret);
        Ok(Self { secret, public })
    }
}

impl std::fmt::Debug for EphemeralKeyPair {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("EphemeralKeyPair(<secret redacted>)")
    }
}

/// Decode a 32-byte X25519 public from hex. Used when reading the
/// peer's ephemeral pub from a PairingRequested / PairingConfirmed
/// event in the ledger.
pub fn ephemeral_public_from_hex(s: &str) -> Result<x25519_dalek::PublicKey> {
    let bytes = hex_decode(s)?;
    let arr: [u8; 32] = bytes.as_slice().try_into()
        .map_err(|_| Web4Error::Crypto(
            format!("ephemeral pubkey must be 32 bytes, got {}", bytes.len())
        ))?;
    Ok(x25519_dalek::PublicKey::from(arr))
}

/// V2 session-key derivation. Mixes the LCT-static ECDH and the
/// per-session ephemeral ECDH. Both endpoints derive the same key
/// from their own secret + the peer's two publics + pair_id.
pub fn derive_session_key_v2(
    static_shared: &SharedSecret,
    ephemeral_shared: &SharedSecret,
    pair_id: Uuid,
) -> SessionKey {
    let mut ikm = Vec::with_capacity(64);
    ikm.extend_from_slice(static_shared.as_bytes());
    ikm.extend_from_slice(ephemeral_shared.as_bytes());
    let hk = Hkdf::<Sha256>::new(Some(pair_id.as_bytes()), &ikm);
    let mut okm = [0u8; 32];
    hk.expand(HKDF_INFO_V2, &mut okm)
        .expect("HKDF expand for 32 bytes never fails");
    SessionKey(okm)
}

/// End-to-end seal with forward secrecy. Caller supplies their own
/// LCT keypair + ephemeral keypair + peer's LCT public + peer's
/// ephemeral public + pair_id + plaintext.
pub fn seal_fs(
    my_lct: &KeyPair,
    my_eph: &EphemeralKeyPair,
    peer_lct: &PublicKey,
    peer_eph_pub: &x25519_dalek::PublicKey,
    pair_id: Uuid,
    plaintext: &[u8],
) -> Result<Sealed> {
    let static_shared = my_lct.ecdh_with_peer(peer_lct)?;
    let eph_shared = SharedSecret::from_bytes(*my_eph.secret.diffie_hellman(peer_eph_pub).as_bytes());
    let key = derive_session_key_v2(&static_shared, &eph_shared, pair_id);
    encrypt(&key, plaintext)
}

/// Symmetric inverse of `seal_fs`.
pub fn open_fs(
    my_lct: &KeyPair,
    my_eph: &EphemeralKeyPair,
    peer_lct: &PublicKey,
    peer_eph_pub: &x25519_dalek::PublicKey,
    pair_id: Uuid,
    sealed: &Sealed,
) -> Result<Vec<u8>> {
    let static_shared = my_lct.ecdh_with_peer(peer_lct)?;
    let eph_shared = SharedSecret::from_bytes(*my_eph.secret.diffie_hellman(peer_eph_pub).as_bytes());
    let key = derive_session_key_v2(&static_shared, &eph_shared, pair_id);
    decrypt(&key, sealed)
}

// ---------- internal hex helpers (no external dep) ----------

fn hex_encode(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{:02x}", b)).collect()
}

fn hex_decode(s: &str) -> Result<Vec<u8>> {
    if s.len() % 2 != 0 {
        return Err(Web4Error::Crypto("hex string must have even length".into()));
    }
    (0..s.len()).step_by(2).map(|i| {
        u8::from_str_radix(&s[i..i + 2], 16)
            .map_err(|e| Web4Error::Crypto(format!("invalid hex: {}", e)))
    }).collect()
}

// SharedSecret needs to expose a private constructor for the ephemeral
// path above. We do that by making it a sibling helper — keeps the
// (LCT-derived only) public construction path through `ecdh_with_peer`.

// Note: `SharedSecret` struct field is private at the module level,
// so this only works because `seal_fs` / `open_fs` live in the same
// file. External callers still get a SharedSecret only via
// `KeyPair::ecdh_with_peer`. Internal-only construction is fine.


#[cfg(test)]
mod tests {
    use super::*;

    /// Foundation property: Alice seals to Bob, Bob opens with his own
    /// keypair + Alice's pubkey, recovers the original plaintext.
    #[test]
    fn seal_open_round_trip() {
        let alice = KeyPair::generate();
        let bob = KeyPair::generate();
        let pair_id = Uuid::new_v4();
        let plaintext = b"hello bob - this should be e2e";

        let sealed = seal(&alice, &bob.verifying_key(), pair_id, plaintext).unwrap();
        let recovered = open(&bob, &alice.verifying_key(), pair_id, &sealed).unwrap();
        assert_eq!(recovered, plaintext);
    }

    /// Symmetric direction: Bob seals to Alice, Alice opens. Same key.
    #[test]
    fn seal_open_is_direction_symmetric() {
        let alice = KeyPair::generate();
        let bob = KeyPair::generate();
        let pair_id = Uuid::new_v4();

        let from_alice = seal(&alice, &bob.verifying_key(), pair_id, b"to bob").unwrap();
        let from_bob = seal(&bob, &alice.verifying_key(), pair_id, b"to alice").unwrap();

        assert_eq!(open(&bob, &alice.verifying_key(), pair_id, &from_alice).unwrap(), b"to bob");
        assert_eq!(open(&alice, &bob.verifying_key(), pair_id, &from_bob).unwrap(), b"to alice");
    }

    /// AEAD integrity: flipping a single ciphertext byte must cause
    /// open() to error. This is what "the hub cannot tamper without
    /// detection" buys us at the wire layer.
    #[test]
    fn tampered_ciphertext_fails_open() {
        let alice = KeyPair::generate();
        let bob = KeyPair::generate();
        let pair_id = Uuid::new_v4();

        let sealed = seal(&alice, &bob.verifying_key(), pair_id, b"important").unwrap();
        let mut bytes = sealed.into_bytes();
        // Flip a byte in the ciphertext region (past the 12-byte nonce).
        let target = bytes.len() / 2;
        bytes[target] ^= 0xff;
        let tampered = Sealed::from_bytes(bytes).unwrap();
        assert!(open(&bob, &alice.verifying_key(), pair_id, &tampered).is_err(),
            "tampered ciphertext must fail AEAD authentication");
    }

    /// Different pair_ids must produce different session keys — so
    /// the same shared secret can serve many pairs without key reuse.
    /// Addresses PRD §8.1 open question.
    #[test]
    fn different_pair_ids_use_distinct_session_keys() {
        let alice = KeyPair::generate();
        let bob = KeyPair::generate();
        let p1 = Uuid::new_v4();
        let p2 = Uuid::new_v4();

        let sealed_p1 = seal(&alice, &bob.verifying_key(), p1, b"x").unwrap();
        // Opening sealed_p1 with the WRONG pair_id must fail — proves
        // the pair_id is mixed into the session key, not just metadata.
        assert!(open(&bob, &alice.verifying_key(), p2, &sealed_p1).is_err(),
            "seal under p1 must not open under p2");
    }

    /// Wrong peer pubkey must fail — confirms the ECDH derivation
    /// actually binds to the peer's identity.
    #[test]
    fn wrong_peer_pubkey_fails_open() {
        let alice = KeyPair::generate();
        let bob = KeyPair::generate();
        let carol = KeyPair::generate();
        let pair_id = Uuid::new_v4();

        let sealed = seal(&alice, &bob.verifying_key(), pair_id, b"for bob").unwrap();
        assert!(open(&bob, &carol.verifying_key(), pair_id, &sealed).is_err(),
            "bob using carol's pubkey instead of alice's must fail");
    }

    /// Base64 round-trip for the wire format.
    #[test]
    fn sealed_base64_round_trip() {
        let alice = KeyPair::generate();
        let bob = KeyPair::generate();
        let pair_id = Uuid::new_v4();

        let sealed = seal(&alice, &bob.verifying_key(), pair_id, b"hello").unwrap();
        let b64 = sealed.to_base64();
        let back = Sealed::from_base64(&b64).unwrap();
        assert_eq!(sealed.as_bytes(), back.as_bytes());
        // And the round-tripped Sealed still decrypts:
        let plain = open(&bob, &alice.verifying_key(), pair_id, &back).unwrap();
        assert_eq!(plain, b"hello");
    }

    /// SessionKey's Debug must redact.
    #[test]
    fn session_key_debug_is_redacted() {
        let alice = KeyPair::generate();
        let bob = KeyPair::generate();
        let pair_id = Uuid::new_v4();
        let shared = alice.ecdh_with_peer(&bob.verifying_key()).unwrap();
        let key = derive_session_key(&shared, pair_id);
        let s = format!("{:?}", key);
        assert!(s.contains("redacted"));
        // Spot-check the raw bytes don't appear in hex form
        let hex: String = key.as_bytes().iter()
            .map(|b| format!("{:02x}", b)).collect();
        assert!(!s.contains(&hex[..16]));
    }

    /// Nonces are random per encryption — encrypting the SAME plaintext
    /// twice produces DIFFERENT ciphertexts.
    #[test]
    fn nonces_are_unique_per_encryption() {
        let alice = KeyPair::generate();
        let bob = KeyPair::generate();
        let pair_id = Uuid::new_v4();

        let s1 = seal(&alice, &bob.verifying_key(), pair_id, b"same plaintext").unwrap();
        let s2 = seal(&alice, &bob.verifying_key(), pair_id, b"same plaintext").unwrap();
        assert_ne!(s1.as_bytes(), s2.as_bytes(),
            "identical plaintexts must produce distinct ciphertexts (random nonces)");
    }

    /// Too-short sealed blob errors cleanly (defense against
    /// malformed wire input).
    #[test]
    fn short_sealed_blob_errors() {
        // Length < 12 (nonce) + 16 (tag) = 28
        let result = Sealed::from_bytes(vec![0u8; 20]);
        assert!(result.is_err());
    }

    // ---------- Sprint F: forward secrecy ----------

    /// FS happy path: Alice and Bob each generate ephemeral keys,
    /// publish the publics, derive the same v2 session key, seal/open
    /// successfully.
    #[test]
    fn fs_seal_open_round_trip() {
        let alice = KeyPair::generate();
        let bob = KeyPair::generate();
        let alice_eph = EphemeralKeyPair::generate();
        let bob_eph = EphemeralKeyPair::generate();
        let pair_id = Uuid::new_v4();
        let plaintext = b"forward secrecy demo";

        let sealed = seal_fs(
            &alice, &alice_eph,
            &bob.verifying_key(), &bob_eph.public,
            pair_id, plaintext,
        ).unwrap();
        let recovered = open_fs(
            &bob, &bob_eph,
            &alice.verifying_key(), &alice_eph.public,
            pair_id, &sealed,
        ).unwrap();
        assert_eq!(recovered, plaintext);
    }

    /// **The forward secrecy property itself, demonstrated as a test:**
    /// Alice seals with FS (v2). An attacker later obtains BOTH
    /// parties' static LCT keys but NOT the ephemeral secrets
    /// (because they were wiped). The v1 open() call (static-only
    /// derivation) MUST fail — proving the captured ciphertext is
    /// unreachable without the ephemerals.
    #[test]
    fn fs_v2_ciphertext_cannot_be_opened_with_static_keys_alone() {
        let alice = KeyPair::generate();
        let bob = KeyPair::generate();
        let alice_eph = EphemeralKeyPair::generate();
        let bob_eph = EphemeralKeyPair::generate();
        let pair_id = Uuid::new_v4();
        let plaintext = b"top secret with forward secrecy";

        // Alice seals using FS path
        let sealed = seal_fs(
            &alice, &alice_eph,
            &bob.verifying_key(), &bob_eph.public,
            pair_id, plaintext,
        ).unwrap();

        // Attacker later has BOTH static private keys (worst case),
        // and the captured ciphertext. They try the v1 open path
        // (static-only). Should fail — the v1 derivation produces a
        // different key, AEAD authentication fails.
        let result = open(&alice, &bob.verifying_key(), pair_id, &sealed);
        assert!(result.is_err(),
            "FS-sealed ciphertext must not open via the static-only v1 path");

        // And just to be exhaustive: attacker can't even fabricate
        // their own ephemeral and try; without one of the real
        // ephemeral *secrets*, ECDH produces the wrong shared.
        let fake_eph = EphemeralKeyPair::generate();
        let result_with_fake = open_fs(
            &alice, &fake_eph,
            &bob.verifying_key(), &bob_eph.public,
            pair_id, &sealed,
        );
        assert!(result_with_fake.is_err(),
            "FS-sealed ciphertext must not open with a fabricated ephemeral");
    }

    /// Symmetric verification: Bob with HIS ephemeral secret and
    /// alice's ephemeral public derives the same v2 key as Alice did
    /// for the seal — recover succeeds.
    #[test]
    fn fs_direction_symmetric() {
        let alice = KeyPair::generate();
        let bob = KeyPair::generate();
        let alice_eph = EphemeralKeyPair::generate();
        let bob_eph = EphemeralKeyPair::generate();
        let pair_id = Uuid::new_v4();

        let from_alice = seal_fs(
            &alice, &alice_eph,
            &bob.verifying_key(), &bob_eph.public,
            pair_id, b"to bob",
        ).unwrap();
        let from_bob = seal_fs(
            &bob, &bob_eph,
            &alice.verifying_key(), &alice_eph.public,
            pair_id, b"to alice",
        ).unwrap();

        assert_eq!(
            open_fs(&bob, &bob_eph, &alice.verifying_key(), &alice_eph.public,
                pair_id, &from_alice).unwrap(),
            b"to bob"
        );
        assert_eq!(
            open_fs(&alice, &alice_eph, &bob.verifying_key(), &bob_eph.public,
                pair_id, &from_bob).unwrap(),
            b"to alice"
        );
    }

    /// Ephemeral secret round-trips through hex (for local persistence).
    /// Reconstructed keypair produces the same public.
    #[test]
    fn fs_ephemeral_secret_hex_round_trip() {
        let eph = EphemeralKeyPair::generate();
        let secret_hex = eph.secret_hex();
        let recovered = EphemeralKeyPair::from_secret_hex(&secret_hex).unwrap();
        assert_eq!(eph.public_bytes(), recovered.public_bytes(),
            "recovered keypair must produce the same public key");
    }

    /// Ephemeral keypair Debug must redact.
    #[test]
    fn fs_ephemeral_debug_is_redacted() {
        let eph = EphemeralKeyPair::generate();
        let s = format!("{:?}", eph);
        assert!(s.contains("redacted"));
        // The secret hex must not appear anywhere in Debug output
        let secret = eph.secret_hex();
        assert!(!s.contains(&secret[..16]));
    }

    /// Distinct pair_ids still produce distinct v2 session keys
    /// (the salt mixing carries over from v1).
    #[test]
    fn fs_pair_id_still_binds_session_key() {
        let alice = KeyPair::generate();
        let bob = KeyPair::generate();
        let alice_eph = EphemeralKeyPair::generate();
        let bob_eph = EphemeralKeyPair::generate();
        let p1 = Uuid::new_v4();
        let p2 = Uuid::new_v4();

        let sealed = seal_fs(
            &alice, &alice_eph, &bob.verifying_key(), &bob_eph.public,
            p1, b"hello",
        ).unwrap();
        let wrong_pair = open_fs(
            &bob, &bob_eph, &alice.verifying_key(), &alice_eph.public,
            p2, &sealed,
        );
        assert!(wrong_pair.is_err(),
            "v2 ciphertext under p1 must not open under p2");
    }

    /// `ephemeral_public_from_hex` parses the same bytes back as the
    /// keypair produced — closing the wire-format loop.
    #[test]
    fn fs_ephemeral_public_hex_parse_round_trip() {
        let eph = EphemeralKeyPair::generate();
        let pub_hex = eph.public_hex();
        let parsed = ephemeral_public_from_hex(&pub_hex).unwrap();
        assert_eq!(parsed.as_bytes(), &eph.public_bytes());
    }
}
