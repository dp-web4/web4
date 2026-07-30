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
    ///
    /// ## What the canonicalizer does and does not buy
    ///
    /// It removes the *hub's* dependence on its own feature flags. It
    /// cannot remove the protocol's dependence on the **sender's**,
    /// because the hub never sees the sender's bytes — only the parsed
    /// [`serde_json::Value`]. So this is a requirement on senders, and
    /// it is not stated anywhere else:
    ///
    /// > **The sender must serialize `payload` with object keys in
    /// > ascending byte order.** A sender that emits any other key order
    /// > signs different bytes than the hub verifies, and gets
    /// > [`VerifyError::BadSignature`] — an error that names neither key
    /// > order nor the payload.
    ///
    /// Hestia satisfies this by construction, not by intent:
    /// `serde_json::Map` is a `BTreeMap` under default features, so
    /// `to_string()` is sorted. A client in a language whose maps keep
    /// insertion order (the `plugin-sdk/python` and `plugin-sdk/typescript`
    /// trees are where one would appear) has to sort deliberately.
    /// Pinned by `sender_key_order_is_a_requirement_the_hub_cannot_see`
    /// and `canonical_form_equals_hestias_to_string`.
    ///
    /// Key order is not the only such requirement, and it is the one that
    /// gets written down because it is the one a Rust author thinks of.
    /// **The sender must also spell numbers the way `serde_json` does**,
    /// for the same reason and with the same symptom — a bare
    /// [`VerifyError::BadSignature`]. Two divergences are measured, not
    /// inferred (2026-07-30, `serde_json` 1.0.150, CPython 3.12, V8):
    ///
    /// - **Small floats, Python only.** Rust switches to exponential form
    ///   below `1e-5` and never pads the exponent; Python's `json.dumps`
    ///   switches below `1e-4` and pads to two digits. So `3.5e-5` signs as
    ///   `0.000035` here and `3.5e-05` there, and `3.5e-6` signs as `3.5e-6`
    ///   here and `3.5e-06` there. The divergent band is contiguous:
    ///   **every non-zero float with magnitude in `[1e-9, 1e-4)`**. Below
    ///   `1e-9` the exponent reaches two digits and the two agree again.
    ///   That band is ordinary territory for a fraction — a T3/V3 weight or
    ///   a per-unit rate lands in it without anyone choosing an odd value.
    /// - **Integers above `u64::MAX`, every language.** `serde_json` (no
    ///   `arbitrary_precision`) falls back to `f64`, so `18446744073709551616`
    ///   signs as `1.8446744073709552e+19`. Python keeps it exact; JS spells
    ///   the rounded double as `18446744073709552000`. All three differ.
    ///   Note this one loses information *before* the signature check, so
    ///   distinct large integers become the same value to the hub.
    ///
    /// TypeScript is otherwise safe: V8 and `serde_json` agree across the
    /// whole float range tested, including the integral-valued floats
    /// (`1e5` → `100000`) where they look like they should differ — the
    /// sender's own spelling is what reaches the parser, so the two only
    /// have to agree on the round trip, not on the literal.
    ///
    /// Pinned by `sender_number_spelling_is_a_requirement_the_hub_cannot_see`.
    ///
    /// The mirror image of that requirement is that the payload's **wire
    /// spelling is not authenticated**: because the hub re-derives the
    /// signing bytes from the parsed value, an intermediary can re-order
    /// the keys, or re-spell a float (`1e2` → `100.0`), and the signature
    /// still verifies. That is malleability, not forgery — the two
    /// spellings parse to the same [`serde_json::Value`], and every
    /// consumer downstream of [`verify_envelope`] reads that value, never
    /// the received text. The property that keeps it safe is therefore
    /// "nothing acts on the raw bytes," the same property that makes
    /// `ledger::signing_payload` safe (see its docs). If a consumer ever
    /// needs the exact bytes a signer saw, it must carry them explicitly;
    /// it cannot recover them from a verified envelope.
    /// Pinned by `wire_spelling_is_malleable_and_that_is_the_safe_case`.
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
        //
        // It is necessary but NOT sufficient, and on its own it is a
        // vacuous canary: this payload's insertion order is already its
        // sorted order, so it keeps passing under `preserve_order` — the
        // one condition that breaks the interop it guards (measured
        // 2026-07-30). `canonical_form_equals_hestias_to_string` is the
        // battery that actually fails there; keep both.
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

    /// The interop anchor. Hestia signs `payload.to_string()`
    /// (`hestia core/src/hub.rs`, `SignedEnvelope::create`); the hub signs
    /// `serialize_canonical(payload)`. Nothing forces those to agree — they
    /// are two independently written serializers in two repositories — so
    /// pin the equality over the shapes an envelope payload actually takes.
    ///
    /// If this ever fails, the hub has stopped accepting hestia's envelopes.
    /// The most likely cause is `serde_json`'s `preserve_order` feature being
    /// unified on in *this* workspace's graph, which turns `Map` into an
    /// `IndexMap` and makes `to_string()` insertion-ordered.
    #[test]
    fn canonical_form_equals_hestias_to_string() {
        let cases = vec![
            json!({}),
            json!(null),
            json!(true),
            json!("plain"),
            // Escapes: both sides delegate to serde_json's escaper, but only
            // one of them does so via a public API.
            json!("quote\" backslash\\ newline\n tab\t control\u{1}"),
            json!("unicode: é 日本語 \u{1F600}"),
            // Numbers: Display-for-Number vs the serializer's f64/i64 paths.
            json!({"u": u64::MAX, "i": i64::MIN, "z": 0, "neg_zero": -0.0}),
            json!({"f": 0.1, "big": 1e300, "small": 1e-300, "exact": 2.0}),
            // Key order: the hub sorts explicitly, hestia relies on BTreeMap.
            json!({"b": 1, "a": 2, "C": 3, "_": 4, "": 5, "é": 6, "a1": 7, "a": 8}),
            // Nesting, and empty containers inside it.
            json!({"outer": {"inner": [1, {"deep": []}, {}], "sib": [[], [[]]]}}),
            // The realistic one.
            json!({"action": "add_member", "name": "Alice", "roles": ["citizen"]}),
        ];
        for v in cases {
            assert_eq!(
                serialize_canonical(&v).unwrap(),
                v.to_string(),
                "hub canonical form diverged from serde_json's Value::to_string() \
                 (hestia's signing algorithm) for {v}"
            );
        }
    }

    /// The second requirement the hub imposes on senders and cannot observe:
    /// **number spelling**. Companion to the key-order test below; see
    /// `signing_bytes`' docs for the measurement this pins.
    ///
    /// Two halves, because they fail for different reasons:
    ///
    /// 1. A spelling table, locking in `serde_json`'s float `Display` at the
    ///    two decade boundaries that matter. A `serde_json` bump that moves
    ///    where exponential form starts, or that starts padding exponents,
    ///    silently re-spells the bytes every sender must reproduce — and no
    ///    other test in this file would notice, because both sides of
    ///    `canonical_form_equals_hestias_to_string` would move together.
    /// 2. An end-to-end sign-and-reject, so the table is anchored to the
    ///    symptom rather than to a string comparison: a sender that spells
    ///    `3.5e-6` the way CPython does gets `BadSignature`, from a payload
    ///    the hub agrees is the same *value*.
    #[tokio::test]
    async fn sender_number_spelling_is_a_requirement_the_hub_cannot_see() {
        // 1. The table. `given` is a valid JSON literal; `canonical` is the
        // spelling every sender must reproduce to be verifiable here.
        // Measured 2026-07-30 against serde_json 1.0.150.
        let table = [
            // Above the exponential threshold: plain decimal, both agree.
            ("1e-4", "0.0001"),
            ("3.5e-4", "0.00035"),
            // The form-divergence decade: Rust decimal, Python `3.5e-05`.
            ("1e-5", "0.00001"),
            ("3.5e-5", "0.000035"),
            // The padding-divergence decades: Rust `3.5e-6`, Python `3.5e-06`.
            ("1e-6", "1e-6"),
            ("3.5e-6", "3.5e-6"),
            ("1e-9", "1e-9"),
            // Two-digit exponent: the two agree again.
            ("1e-10", "1e-10"),
            ("1e-100", "1e-100"),
            // Integers: exact through u64::MAX, f64 above it.
            ("18446744073709551615", "18446744073709551615"),
            ("18446744073709551616", "1.8446744073709552e+19"),
        ];
        for (given, expected) in table {
            let v: serde_json::Value = serde_json::from_str(given).unwrap();
            let canonical = serialize_canonical(&v).unwrap();
            assert_eq!(
                canonical, expected,
                "canonical spelling of {given} moved — every sender's signing \
                 bytes just changed, and only this test says so"
            );
            // The canonical form is a fixed point: re-parsing and
            // re-canonicalizing must not move it again. Without this, a
            // spelling could satisfy the table and still not be reproducible
            // by a sender that round-trips its own output.
            let reparsed: serde_json::Value = serde_json::from_str(&canonical).unwrap();
            assert_eq!(
                serialize_canonical(&reparsed).unwrap(),
                canonical,
                "canonical form of {given} is not a fixed point"
            );
        }

        // 2. The symptom. Sign the CPython spelling, send the same value.
        let signer = fresh_identity();
        let kp = signer.keypair().unwrap();
        let mut resolver = MapResolver::new();
        resolver.insert(signer.lct.clone());
        let now = now_fixed();
        let nonces = NonceStore::new();
        let challenge = nonces.issue(signer.lct.id, now);

        // What `json.dumps({"rate": 3.5e-6}, sort_keys=True, separators=(",", ":"))`
        // emits, transcribed. The hub's canonical form of the same value is
        // `{"rate":3.5e-6}` — one character apart.
        let python_spelling = r#"{"rate":3.5e-06}"#;
        let payload: serde_json::Value = serde_json::from_str(python_spelling).unwrap();
        assert_ne!(
            serialize_canonical(&payload).unwrap(),
            python_spelling,
            "if these ever agree the divergence is gone and this test should be \
             retired, not weakened"
        );

        let mut foreign_bytes = challenge.nonce.as_bytes().to_vec();
        foreign_bytes.extend_from_slice(python_spelling.as_bytes());
        let sig = kp.sign(&foreign_bytes);
        let envelope = SignedEnvelope {
            challenge_nonce: challenge.nonce.clone(),
            payload: payload.clone(),
            signature: hex::encode(sig.bytes),
            signer_lct_id: signer.lct.id,
        };
        assert!(
            matches!(
                verify_envelope(&envelope, &nonces, &resolver, now),
                Err(VerifyError::BadSignature(_))
            ),
            "a correctly-signed, correctly-keyed, correctly-valued payload is \
             rejected purely on number spelling — that is the requirement"
        );

        // The control: the identical value spelled the hub's way verifies, so
        // the rejection above is about spelling and nothing else.
        let challenge2 = nonces.issue(signer.lct.id, now);
        let ok = build_envelope(signer.lct.id, &kp, &challenge2, payload).unwrap();
        verify_envelope(&ok, &nonces, &resolver, now)
            .expect("same value, hub's spelling — must verify");
    }

    /// The requirement the hub imposes on senders and cannot itself observe.
    ///
    /// The hub verifies against *sorted* keys. A sender that serializes in
    /// any other order signs different bytes — and because the hub only ever
    /// sees the parsed `Value`, the resulting error is a bare
    /// `BadSignature` that names neither key order nor the payload. This
    /// test exists so the requirement is written down somewhere executable.
    #[tokio::test]
    async fn sender_key_order_is_a_requirement_the_hub_cannot_see() {
        let signer = fresh_identity();
        let kp = signer.keypair().unwrap();
        let mut resolver = MapResolver::new();
        resolver.insert(signer.lct.clone());
        let now = now_fixed();

        // One payload, two serializations. Both are valid JSON for the same
        // value; only the second is what the hub will re-derive.
        let unsorted = r#"{"b":1,"a":2}"#;
        let sorted = r#"{"a":2,"b":1}"#;
        let payload: serde_json::Value = serde_json::from_str(unsorted).unwrap();
        assert_eq!(
            serialize_canonical(&payload).unwrap(),
            sorted,
            "precondition: the hub's canonical form is the sorted spelling"
        );

        // A sender whose map keeps insertion order signs `unsorted`.
        let nonces = NonceStore::new();
        let challenge = nonces.issue(signer.lct.id, now);
        let mut signed_bytes = challenge.nonce.clone().into_bytes();
        signed_bytes.extend_from_slice(unsorted.as_bytes());
        let env = SignedEnvelope {
            challenge_nonce: challenge.nonce.clone(),
            payload: payload.clone(),
            signature: hex::encode(kp.sign(&signed_bytes).bytes),
            signer_lct_id: signer.lct.id,
        };

        match verify_envelope(&env, &nonces, &resolver, now) {
            Err(VerifyError::BadSignature(msg)) => {
                // The diagnostic gap is the point: nothing in the error
                // points at key order. Assert that, so a future error
                // message that *does* explain it fails here and gets read.
                assert!(
                    !msg.to_lowercase().contains("order")
                        && !msg.to_lowercase().contains("payload"),
                    "error text unexpectedly explains the cause: {msg}"
                );
            }
            other => panic!("expected BadSignature from unsorted-key signing, got {other:?}"),
        }

        // Same key, same nonce-issuing store, same payload — sorted signing
        // bytes verify. So order alone is the difference, not the setup.
        let challenge2 = nonces.issue(signer.lct.id, now);
        let mut ok_bytes = challenge2.nonce.clone().into_bytes();
        ok_bytes.extend_from_slice(sorted.as_bytes());
        let good = SignedEnvelope {
            challenge_nonce: challenge2.nonce.clone(),
            payload,
            signature: hex::encode(kp.sign(&ok_bytes).bytes),
            signer_lct_id: signer.lct.id,
        };
        assert!(verify_envelope(&good, &nonces, &resolver, now).is_ok());
    }

    /// The other side of re-deriving from the parsed value: the wire
    /// spelling of `payload` is **not** covered by the signature.
    ///
    /// An intermediary may re-order keys or re-spell a float and the
    /// envelope still verifies. That is safe only because every consumer
    /// downstream of `verify_envelope` reads the parsed `Value`, never the
    /// received text — the same safety property `ledger::signing_payload`
    /// relies on. This test is what would fail if someone "fixed" the
    /// canonicalizer into a received-bytes signer, and it is the reason a
    /// consumer that needs the signer's exact bytes must carry them.
    #[tokio::test]
    async fn wire_spelling_is_malleable_and_that_is_the_safe_case() {
        let signer = fresh_identity();
        let kp = signer.keypair().unwrap();
        let mut resolver = MapResolver::new();
        resolver.insert(signer.lct.clone());
        let now = now_fixed();
        let nonces = NonceStore::new();
        let challenge = nonces.issue(signer.lct.id, now);

        // The signer's spelling.
        let as_sent = r#"{"amount":1e2,"to":"treasury"}"#;
        let value: serde_json::Value = serde_json::from_str(as_sent).unwrap();
        let env = build_envelope(signer.lct.id, &kp, &challenge, value.clone()).unwrap();

        // What an intermediary rewrites it to: keys swapped, float re-spelled.
        let tampered = r#"{"to":"treasury","amount":100.0}"#;
        assert_ne!(as_sent, tampered);
        let tampered_value: serde_json::Value = serde_json::from_str(tampered).unwrap();
        assert_eq!(
            value, tampered_value,
            "the two spellings must denote the same value — that is what makes \
             this malleability rather than forgery"
        );

        let rewritten = SignedEnvelope { payload: tampered_value, ..env };
        let redeemed = verify_envelope(&rewritten, &nonces, &resolver, now)
            .expect("re-spelled payload still verifies — the signature covers the value");
        assert_eq!(redeemed.nonce, challenge.nonce);

        // Changing the *value* is still caught. Without this the assertion
        // above would pass for a verifier that checks nothing.
        let challenge2 = nonces.issue(signer.lct.id, now);
        let mut forged = build_envelope(
            signer.lct.id,
            &kp,
            &challenge2,
            serde_json::from_str::<serde_json::Value>(as_sent).unwrap(),
        )
        .unwrap();
        forged.payload = serde_json::from_str(r#"{"amount":101,"to":"treasury"}"#).unwrap();
        assert!(matches!(
            verify_envelope(&forged, &nonces, &resolver, now),
            Err(VerifyError::BadSignature(_))
        ));
    }
}
