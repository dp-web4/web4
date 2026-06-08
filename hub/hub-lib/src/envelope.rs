// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Signed envelopes — the V2 authority primitive for hub HTTP API.
//!
//! ## Why this exists
//!
//! V2 ships a REST API surface for external clients (Hestia, peers).
//! Every consequential request must prove **who** is asking and **that**
//! the request hasn't been replayed. Per architecture commitment #8,
//! the hub validates this without ever seeing the caller's private key.
//!
//! The shape: client gets a server-issued nonce (the **challenge**),
//! includes it in a JSON **payload**, signs (payload + nonce) with the
//! caller's keypair, and ships the bundle as a [`SignedEnvelope`]. The
//! hub looks up the caller's public key from a [`PublicKeyResolver`],
//! verifies the signature, marks the nonce redeemed, then routes the
//! payload to whichever handler does the work.
//!
//! ## Why a nonce, not just a signature
//!
//! A bare signature can be replayed: capture the bytes, resubmit them
//! tomorrow, the signature still verifies. Tying the signature to a
//! server-issued nonce (with a TTL + one-time redemption) prevents
//! replay without requiring the hub to remember every payload it has
//! ever seen.
//!
//! ## Why this is ZKP-friendly
//!
//! [`Proof`] is a non-exhaustive enum. Today the only variant is
//! [`Proof::EdDsa`] — a standard Ed25519 signature. Tomorrow,
//! [`Proof::Zkp`] (or similar) slots into the same envelope shape;
//! verifiers learn to accept additional proof kinds without rewriting
//! every handler.

use anyhow::{Context, Result};
use chrono::{DateTime, Duration, Utc};
use rand::RngCore;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Mutex;
use uuid::Uuid;
use web4_core::crypto::SignatureBytes;
use web4_core::lct::Lct;

/// Default challenge TTL: 60 seconds. Long enough for slow networks
/// + interactive Hestia prompts, short enough that captured envelopes
/// can't be replayed indefinitely.
pub const DEFAULT_CHALLENGE_TTL_SECONDS: i64 = 60;

/// A server-issued nonce + its expiration. Single-use: redeemed when
/// a SignedEnvelope referencing it verifies.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Challenge {
    /// 32 bytes of entropy, hex-encoded.
    pub nonce: String,
    /// Which LCT this challenge was minted for. The signer must match.
    pub for_lct_id: Uuid,
    pub issued_at: DateTime<Utc>,
    pub expires_at: DateTime<Utc>,
}

impl Challenge {
    pub fn is_expired(&self, now: DateTime<Utc>) -> bool {
        now > self.expires_at
    }
}

/// A signed request from an external client. Verified by the hub
/// before its payload is routed to a handler.
///
/// ## Wire shape (V2-7 — interop with Hestia H2/H3)
///
/// ```json
/// {
///   "challenge_nonce": "...",
///   "payload": { ... },
///   "signature": "hex-encoded-64-byte-ed25519-sig",
///   "signer_lct_id": "uuid"
/// }
/// ```
///
/// Per agreement with Legion's Hestia H2/H3 (`hestia@253c611` core/src/hub.rs):
/// flat `signature` field, Ed25519 only for now. ZKP-friendly extension
/// path: add an optional `proof_kind: String` field (default "ed25519")
/// when ZKP variants need to flow over the same wire shape.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SignedEnvelope {
    pub challenge_nonce: String,
    pub payload: serde_json::Value,
    /// Hex-encoded Ed25519 signature (64 bytes = 128 hex chars) over
    /// `signing_bytes()`.
    pub signature: String,
    pub signer_lct_id: Uuid,
}

impl SignedEnvelope {
    /// Bytes signed: `challenge_nonce ++ canonical(payload)`.
    ///
    /// Matches Hestia's signing algorithm exactly (`nonce.as_bytes() ++
    /// payload.to_string().as_bytes()`). With serde_json's default
    /// features (no `preserve_order`), `Value::to_string()` produces
    /// alphabetically-keyed output, so this is canonical-by-default
    /// without an explicit canonicalization pass. We still use an
    /// explicit canonicalizer here so the hub doesn't depend on
    /// upstream feature flags staying off.
    pub fn signing_bytes(&self) -> Result<Vec<u8>> {
        canonical_signing_bytes(&self.challenge_nonce, &self.payload)
    }
}

fn canonical_signing_bytes(
    challenge_nonce: &str,
    payload: &serde_json::Value,
) -> Result<Vec<u8>> {
    let canonical = serialize_canonical(payload)?;
    let mut buf = Vec::with_capacity(challenge_nonce.len() + canonical.len());
    buf.extend_from_slice(challenge_nonce.as_bytes());
    buf.extend_from_slice(canonical.as_bytes());
    Ok(buf)
}

/// Serialize a serde_json::Value with sorted object keys.
fn serialize_canonical(v: &serde_json::Value) -> Result<String> {
    fn write(v: &serde_json::Value, out: &mut String) -> Result<()> {
        match v {
            serde_json::Value::Null => out.push_str("null"),
            serde_json::Value::Bool(b) => out.push_str(if *b { "true" } else { "false" }),
            serde_json::Value::Number(n) => out.push_str(&n.to_string()),
            serde_json::Value::String(s) => {
                let escaped = serde_json::to_string(s)
                    .context("serializing string in canonical form")?;
                out.push_str(&escaped);
            }
            serde_json::Value::Array(items) => {
                out.push('[');
                for (i, item) in items.iter().enumerate() {
                    if i > 0 { out.push(','); }
                    write(item, out)?;
                }
                out.push(']');
            }
            serde_json::Value::Object(map) => {
                let mut keys: Vec<&String> = map.keys().collect();
                keys.sort();
                out.push('{');
                for (i, k) in keys.iter().enumerate() {
                    if i > 0 { out.push(','); }
                    let escaped_key = serde_json::to_string(k)
                        .context("serializing key in canonical form")?;
                    out.push_str(&escaped_key);
                    out.push(':');
                    write(&map[*k], out)?;
                }
                out.push('}');
            }
        }
        Ok(())
    }
    let mut s = String::new();
    write(v, &mut s)?;
    Ok(s)
}

/// Resolves an LCT id to its full Lct (needed to verify signatures).
///
/// Implementations: a society's known-members + role-fillers; a peer
/// hub's published LCT for federation; a delegation-store lookup for
/// AI agents acting under DelegatedAuthority.
pub trait PublicKeyResolver: Send + Sync {
    fn lookup(&self, lct_id: Uuid) -> Option<Lct>;
}

/// Resolver backed by a HashMap. Useful for tests + small chapters.
pub struct MapResolver(pub HashMap<Uuid, Lct>);

impl MapResolver {
    pub fn new() -> Self {
        Self(HashMap::new())
    }
    pub fn insert(&mut self, lct: Lct) {
        self.0.insert(lct.id, lct);
    }
}

impl Default for MapResolver {
    fn default() -> Self {
        Self::new()
    }
}

impl PublicKeyResolver for MapResolver {
    fn lookup(&self, lct_id: Uuid) -> Option<Lct> {
        self.0.get(&lct_id).cloned()
    }
}

/// Why a verification call failed. Specific enough that an HTTP layer
/// can map each variant to the right status code (4xx vs 5xx) and
/// shape the response envelope.
#[derive(Debug, thiserror::Error)]
pub enum VerifyError {
    #[error("unknown signer LCT {0}")]
    UnknownSigner(Uuid),

    #[error("challenge nonce '{0}' not found (expired, redeemed, or fabricated)")]
    UnknownNonce(String),

    #[error("challenge nonce '{0}' has expired")]
    ExpiredNonce(String),

    #[error("challenge nonce '{0}' was issued for a different LCT")]
    NonceLctMismatch(String),

    #[error("signature verification failed: {0}")]
    BadSignature(String),

    #[error("internal error: {0}")]
    Internal(#[from] anyhow::Error),
}

/// Issues + redeems single-use challenge nonces. In-memory for V2-7;
/// V2 sprints that add multi-replica deployments will likely want a
/// shared-state version (Redis or similar) — keep the trait shape in
/// mind for that.
pub struct NonceStore {
    inner: Mutex<HashMap<String, Challenge>>,
    ttl_seconds: i64,
}

impl NonceStore {
    pub fn new() -> Self {
        Self {
            inner: Mutex::new(HashMap::new()),
            ttl_seconds: DEFAULT_CHALLENGE_TTL_SECONDS,
        }
    }

    pub fn with_ttl(ttl_seconds: i64) -> Self {
        Self {
            inner: Mutex::new(HashMap::new()),
            ttl_seconds,
        }
    }

    /// Issue a fresh challenge for the given LCT. Caller delivers it
    /// to the requester (typically in an HTTP 200 response).
    pub fn issue(&self, for_lct_id: Uuid, now: DateTime<Utc>) -> Challenge {
        let mut rng_bytes = [0u8; 32];
        rand::thread_rng().fill_bytes(&mut rng_bytes);
        let nonce = hex::encode(rng_bytes);
        let challenge = Challenge {
            nonce: nonce.clone(),
            for_lct_id,
            issued_at: now,
            expires_at: now + Duration::seconds(self.ttl_seconds),
        };
        self.inner.lock().expect("nonce store poisoned").insert(nonce, challenge.clone());
        challenge
    }

    /// Atomically check-and-redeem a nonce. Returns the Challenge if
    /// it existed (and was not already redeemed); the caller is
    /// responsible for additional validation (LCT match, expiry).
    pub fn redeem(&self, nonce: &str) -> Option<Challenge> {
        self.inner.lock().expect("nonce store poisoned").remove(nonce)
    }

    /// Walk the store and drop expired entries. Call periodically (or
    /// on a per-request basis if the store is small).
    pub fn prune_expired(&self, now: DateTime<Utc>) -> usize {
        let mut store = self.inner.lock().expect("nonce store poisoned");
        let before = store.len();
        store.retain(|_, ch| !ch.is_expired(now));
        before - store.len()
    }

    pub fn len(&self) -> usize {
        self.inner.lock().expect("nonce store poisoned").len()
    }

    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }
}

impl Default for NonceStore {
    fn default() -> Self {
        Self::new()
    }
}

/// Verify a SignedEnvelope end-to-end:
/// 1. Resolve signer LCT via [`PublicKeyResolver`]
/// 2. Redeem nonce (one-shot) — fails if unknown / already redeemed
/// 3. Check nonce LCT match + expiry
/// 4. Verify proof against canonical signing bytes
///
/// On success: returns the redeemed Challenge (mostly for audit) +
/// caller knows the envelope's payload is authentic + unique.
pub fn verify_envelope(
    envelope: &SignedEnvelope,
    nonces: &NonceStore,
    resolver: &dyn PublicKeyResolver,
    now: DateTime<Utc>,
) -> std::result::Result<Challenge, VerifyError> {
    // 1. Resolve signer.
    let signer_lct = resolver.lookup(envelope.signer_lct_id)
        .ok_or(VerifyError::UnknownSigner(envelope.signer_lct_id))?;

    // 2-3. Redeem nonce + validate.
    let challenge = nonces.redeem(&envelope.challenge_nonce)
        .ok_or_else(|| VerifyError::UnknownNonce(envelope.challenge_nonce.clone()))?;
    if challenge.for_lct_id != envelope.signer_lct_id {
        return Err(VerifyError::NonceLctMismatch(envelope.challenge_nonce.clone()));
    }
    if challenge.is_expired(now) {
        return Err(VerifyError::ExpiredNonce(envelope.challenge_nonce.clone()));
    }

    // 4. Verify signature.
    let signing_bytes = envelope.signing_bytes()
        .map_err(VerifyError::Internal)?;
    let sig_bytes = hex::decode(&envelope.signature)
        .map_err(|e| VerifyError::BadSignature(format!("hex decode: {}", e)))?;
    let sig_arr: [u8; 64] = sig_bytes.as_slice().try_into()
        .map_err(|_| VerifyError::BadSignature("signature must be 64 bytes".into()))?;
    let sig = SignatureBytes::from_bytes(sig_arr);
    signer_lct.verify_signature(&signing_bytes, &sig)
        .map_err(|e| VerifyError::BadSignature(e.to_string()))?;

    Ok(challenge)
}

/// Convenience for clients/tests: build a SignedEnvelope around a
/// payload using a given keypair + a previously-issued challenge.
pub fn build_envelope(
    signer_lct_id: Uuid,
    keypair: &web4_core::crypto::KeyPair,
    challenge: &Challenge,
    payload: serde_json::Value,
) -> Result<SignedEnvelope> {
    let signing_bytes = canonical_signing_bytes(&challenge.nonce, &payload)?;
    let sig = keypair.sign(&signing_bytes);
    Ok(SignedEnvelope {
        challenge_nonce: challenge.nonce.clone(),
        payload,
        signature: hex::encode(sig.bytes),
        signer_lct_id,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::identity::IdentityFile;
    use serde_json::json;
    use web4_core::lct::EntityType;

    fn fresh_identity() -> IdentityFile {
        IdentityFile::generate(EntityType::Human)
    }

    fn now_fixed() -> DateTime<Utc> {
        // Use Utc::now() — chrono::Utc::now is allowed in tests; only
        // the workflow scripts forbid Date.now/Math.random.
        Utc::now()
    }

    #[tokio::test]
    async fn happy_path_signed_envelope_verifies() {
        let signer = fresh_identity();
        let kp = signer.keypair().unwrap();
        let mut resolver = MapResolver::new();
        resolver.insert(signer.lct.clone());

        let nonces = NonceStore::new();
        let now = now_fixed();
        let challenge = nonces.issue(signer.lct.id, now);

        let payload = json!({"action": "add_member", "name": "Alice"});
        let env = build_envelope(signer.lct.id, &kp, &challenge, payload.clone()).unwrap();

        let redeemed = verify_envelope(&env, &nonces, &resolver, now).unwrap();
        assert_eq!(redeemed.nonce, challenge.nonce);
        // Nonce is single-use: the second attempt fails
        assert!(matches!(
            verify_envelope(&env, &nonces, &resolver, now),
            Err(VerifyError::UnknownNonce(_))
        ));
    }

    #[tokio::test]
    async fn wrong_keypair_fails() {
        let signer = fresh_identity();
        let attacker = fresh_identity();
        let bad_kp = attacker.keypair().unwrap();

        let mut resolver = MapResolver::new();
        resolver.insert(signer.lct.clone()); // resolver only knows the real signer

        let nonces = NonceStore::new();
        let now = now_fixed();
        let challenge = nonces.issue(signer.lct.id, now);

        // Attacker signs the envelope but claims to be signer
        let env = build_envelope(signer.lct.id, &bad_kp, &challenge, json!({})).unwrap();
        let result = verify_envelope(&env, &nonces, &resolver, now);
        assert!(matches!(result, Err(VerifyError::BadSignature(_))),
            "wrong-key signature must fail, got: {:?}", result);
    }

    #[tokio::test]
    async fn unknown_signer_fails() {
        let signer = fresh_identity();
        let kp = signer.keypair().unwrap();
        // resolver has no entries
        let resolver = MapResolver::new();
        let nonces = NonceStore::new();
        let now = now_fixed();
        // Manually mint a challenge for this LCT even though resolver doesn't know it
        let challenge = nonces.issue(signer.lct.id, now);
        let env = build_envelope(signer.lct.id, &kp, &challenge, json!({})).unwrap();
        let result = verify_envelope(&env, &nonces, &resolver, now);
        assert!(matches!(result, Err(VerifyError::UnknownSigner(_))));
    }

    #[tokio::test]
    async fn unknown_nonce_fails() {
        let signer = fresh_identity();
        let kp = signer.keypair().unwrap();
        let mut resolver = MapResolver::new();
        resolver.insert(signer.lct.clone());
        let nonces = NonceStore::new();
        let now = now_fixed();

        // Construct a challenge that was NEVER issued
        let fake = Challenge {
            nonce: "deadbeef".repeat(8),
            for_lct_id: signer.lct.id,
            issued_at: now,
            expires_at: now + Duration::seconds(60),
        };
        let env = build_envelope(signer.lct.id, &kp, &fake, json!({})).unwrap();
        let result = verify_envelope(&env, &nonces, &resolver, now);
        assert!(matches!(result, Err(VerifyError::UnknownNonce(_))));
    }

    #[tokio::test]
    async fn nonce_for_different_lct_fails() {
        let signer = fresh_identity();
        let other = fresh_identity();
        let kp = signer.keypair().unwrap();
        let mut resolver = MapResolver::new();
        resolver.insert(signer.lct.clone());
        resolver.insert(other.lct.clone());

        let nonces = NonceStore::new();
        let now = now_fixed();
        // Challenge issued for `other`, but signer tries to use it
        let challenge = nonces.issue(other.lct.id, now);
        let env = build_envelope(signer.lct.id, &kp, &challenge, json!({})).unwrap();
        let result = verify_envelope(&env, &nonces, &resolver, now);
        assert!(matches!(result, Err(VerifyError::NonceLctMismatch(_))));
    }

    #[tokio::test]
    async fn expired_nonce_fails() {
        let signer = fresh_identity();
        let kp = signer.keypair().unwrap();
        let mut resolver = MapResolver::new();
        resolver.insert(signer.lct.clone());

        let nonces = NonceStore::with_ttl(1); // 1 second TTL
        let now = now_fixed();
        let challenge = nonces.issue(signer.lct.id, now);
        let env = build_envelope(signer.lct.id, &kp, &challenge, json!({})).unwrap();

        let later = now + Duration::seconds(5); // way past TTL
        let result = verify_envelope(&env, &nonces, &resolver, later);
        assert!(matches!(result, Err(VerifyError::ExpiredNonce(_))));
    }

    #[tokio::test]
    async fn replay_attack_fails() {
        // The nonce is single-use: redeeming once consumes it.
        let signer = fresh_identity();
        let kp = signer.keypair().unwrap();
        let mut resolver = MapResolver::new();
        resolver.insert(signer.lct.clone());
        let nonces = NonceStore::new();
        let now = now_fixed();
        let challenge = nonces.issue(signer.lct.id, now);
        let env = build_envelope(signer.lct.id, &kp, &challenge, json!({"x": 1})).unwrap();

        // First verification: passes
        verify_envelope(&env, &nonces, &resolver, now).unwrap();
        // Replay: same envelope, but nonce already redeemed
        let replay = verify_envelope(&env, &nonces, &resolver, now);
        assert!(matches!(replay, Err(VerifyError::UnknownNonce(_))));
    }

    #[tokio::test]
    async fn tampered_payload_fails() {
        let signer = fresh_identity();
        let kp = signer.keypair().unwrap();
        let mut resolver = MapResolver::new();
        resolver.insert(signer.lct.clone());
        let nonces = NonceStore::new();
        let now = now_fixed();
        let challenge = nonces.issue(signer.lct.id, now);

        // Build envelope around original payload
        let mut env = build_envelope(signer.lct.id, &kp, &challenge, json!({"amount": 10})).unwrap();
        // Tamper: change payload to look more favorable
        env.payload = json!({"amount": 10000});

        let result = verify_envelope(&env, &nonces, &resolver, now);
        assert!(matches!(result, Err(VerifyError::BadSignature(_))));
    }

    #[tokio::test]
    async fn canonical_signing_is_key_order_independent() {
        // Two payloads with the same keys in different orders must
        // produce identical signing bytes.
        let p1 = json!({"a": 1, "b": 2, "c": 3});
        let p2 = json!({"c": 3, "a": 1, "b": 2});
        let bytes1 = canonical_signing_bytes("nonce", &p1).unwrap();
        let bytes2 = canonical_signing_bytes("nonce", &p2).unwrap();
        assert_eq!(bytes1, bytes2);
    }

    #[tokio::test]
    async fn interop_with_hestia_signing_algorithm() {
        // Lock-in test: our signing bytes MUST equal Hestia's algorithm
        // `nonce.as_bytes() ++ payload.to_string().as_bytes()`.
        // This test must keep passing or interop with Hestia breaks.
        let payload = json!({"a": 1, "b": "hello"});
        let nonce = "abc123";

        let ours = canonical_signing_bytes(nonce, &payload).unwrap();

        let mut hestia_style = Vec::new();
        hestia_style.extend_from_slice(nonce.as_bytes());
        hestia_style.extend_from_slice(payload.to_string().as_bytes());

        assert_eq!(ours, hestia_style,
            "hub signing bytes must match hestia's algorithm exactly");
    }

    #[tokio::test]
    async fn deserialize_hestia_wire_envelope() {
        // Lock-in test: a JSON envelope produced by Hestia (per their
        // SignedEnvelope shape in hestia@253c611 core/src/hub.rs) MUST
        // deserialize into ours.
        let hestia_json = json!({
            "challenge_nonce": "abc123",
            "payload": {"action": "add_member"},
            "signature": "00".repeat(64),
            "signer_lct_id": Uuid::new_v4().to_string(),
        });
        let env: SignedEnvelope = serde_json::from_value(hestia_json).unwrap();
        assert_eq!(env.challenge_nonce, "abc123");
        assert_eq!(env.signature.len(), 128);
    }

    #[tokio::test]
    async fn prune_expired_drops_old_entries() {
        let nonces = NonceStore::with_ttl(1);
        let now = now_fixed();
        let lct = Uuid::new_v4();
        nonces.issue(lct, now);
        nonces.issue(lct, now);
        assert_eq!(nonces.len(), 2);
        let dropped = nonces.prune_expired(now + Duration::seconds(5));
        assert_eq!(dropped, 2);
        assert_eq!(nonces.len(), 0);
    }
}
