// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Hub-side constellation attestation verification — the verifier half of the
//! challenge-response MFA contract whose member half ships in hestia
//! (`core/src/constellation.rs`).
//!
//! Wire contract: `shared-context/forum/legion-constellation-attestation-wire-shape-2026-06-11.md`
//! (greenlit in `hub-to-legion-constellation-pr-greenlight-2026-06-11.md`).
//! The structs here mirror hestia's serde shape and the signing payload is
//! byte-for-byte identical — `test_vector_payload_hash` is the mechanical
//! anchor that keeps the two repos honest.
//!
//! The verification rules (numbering from the wire-shape memo):
//! 1. `challenge_nonce` matches the nonce minted for this `pair_id`;
//!    single-use, burned on any presentation attempt.
//! 2. `issued_at` within max age (default 5 min) on the hub's clock.
//! 3. Owner signature verifies against `owner_pubkey_hex`, which MUST equal
//!    the member's **pinned** resolver pubkey — a foreign owner key riding in
//!    on a valid channel is rejected, never warned.
//! 4. Device sigs verify against the *included* pubkey; non-verifying,
//!    non-roster, and malformed sigs are dropped silently.
//! 5. The assurance tier is **derived** from verified co-signs;
//!    `claimed_assurance` is never trusted.
//! 6. The derived tier is bound to the `pair_id` with a validity window
//!    (default 1 h); expiry re-challenges, never silently extends.

use chrono::{DateTime, Duration, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Mutex;
use uuid::Uuid;
use web4_core::crypto::{sha256, PublicKey, SignatureBytes};

/// Assurance tier, lowest to highest. Wire values are snake_case
/// (`single_device` / `multi_device` / `hardware_backed`).
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AssuranceLevel {
    SingleDevice,
    MultiDevice,
    HardwareBacked,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DeviceType {
    Desktop,
    Mobile,
    Server,
    Agent,
    Hardware,
}

/// A device co-signature over the same signing payload the owner signed —
/// co-signing binds the device to the exact roster + nonce it vouched for.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DeviceSignature {
    pub lct_id: Uuid,
    pub device_type: DeviceType,
    pub pubkey_hex: String,
    /// Ed25519 signature over `signing_payload(...)`, hex.
    pub signature: String,
}

/// The challenge-bound attestation a member presents over the sealed channel.
/// Mirrors hestia's `ConstellationAttestation` JSON shape exactly.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ConstellationAttestation {
    pub owner_lct_id: Uuid,
    pub owner_pubkey_hex: String,
    pub member_lcts: Vec<Uuid>,
    pub challenge_nonce: String,
    pub issued_at: DateTime<Utc>,
    pub claimed_assurance: AssuranceLevel,
    /// Owner's Ed25519 signature over `signing_payload(...)`, hex.
    pub owner_signature: String,
    pub device_signatures: Vec<DeviceSignature>,
}

/// Why a presentation was refused. `ForeignOwnerKey` is surfaced as 403 by
/// the daemon (an authenticated channel presenting someone else's owner key
/// is an authorization failure, not a malformed request).
#[derive(Debug, PartialEq, Eq, thiserror::Error)]
pub enum VerifyError {
    #[error("no outstanding challenge for this pair — call constellation_challenge first")]
    NoChallenge,
    #[error("challenge nonce mismatch — challenge burned, re-challenge to retry")]
    NonceMismatch,
    #[error("attestation expired — issued_at exceeds the max age window")]
    Stale,
    #[error("owner_pubkey_hex does not match this member's pinned key")]
    ForeignOwnerKey,
    #[error("owner signature does not verify")]
    OwnerSignatureInvalid,
    #[error("malformed attestation: {0}")]
    Malformed(String),
}

/// Deterministic signing payload — byte-for-byte the hestia construction:
/// SHA-256 over `"web4:constellation-attest:v1:"` ‖ owner uuid (16 bytes) ‖
/// nonce (utf8) ‖ issued_at (`to_rfc3339()`, utf8) ‖ each member uuid (16 bytes).
pub fn signing_payload(
    owner: Uuid,
    members: &[Uuid],
    nonce: &str,
    issued_at: &DateTime<Utc>,
) -> Vec<u8> {
    let mut buf = Vec::with_capacity(128);
    buf.extend_from_slice(b"web4:constellation-attest:v1:");
    buf.extend_from_slice(owner.as_bytes());
    buf.extend_from_slice(nonce.as_bytes());
    buf.extend_from_slice(issued_at.to_rfc3339().as_bytes());
    for m in members {
        buf.extend_from_slice(m.as_bytes());
    }
    sha256(&buf).to_vec()
}

impl ConstellationAttestation {
    /// Rules 2–5: max-age, pinned-owner-key match, owner signature, device
    /// co-signs (silent drop), derived tier. Rule 1 (nonce) and rule 6
    /// (binding) live in [`ConstellationGate`], which owns the per-pair state.
    pub fn verify(
        &self,
        pinned_owner_pubkey_hex: &str,
        max_age: Duration,
        now: DateTime<Utc>,
    ) -> Result<AssuranceLevel, VerifyError> {
        if now - self.issued_at > max_age {
            return Err(VerifyError::Stale);
        }
        if !self.owner_pubkey_hex.eq_ignore_ascii_case(pinned_owner_pubkey_hex) {
            return Err(VerifyError::ForeignOwnerKey);
        }

        let payload = signing_payload(
            self.owner_lct_id,
            &self.member_lcts,
            &self.challenge_nonce,
            &self.issued_at,
        );

        let owner_pk = pubkey_from_hex(&self.owner_pubkey_hex)
            .map_err(|e| VerifyError::Malformed(format!("owner pubkey: {e}")))?;
        let owner_sig = sig_from_hex(&self.owner_signature)
            .map_err(|e| VerifyError::Malformed(format!("owner signature: {e}")))?;
        owner_pk
            .verify(&payload, &owner_sig)
            .map_err(|_| VerifyError::OwnerSignatureInvalid)?;

        // Rule 4: silent drop of non-roster / malformed / non-verifying sigs.
        // Deduped by lct_id — one device key presented twice is still ONE
        // verified device, so duplicate sigs can't inflate the tier.
        let mut verified: HashMap<Uuid, &DeviceSignature> = HashMap::new();
        for ds in &self.device_signatures {
            if !self.member_lcts.contains(&ds.lct_id) {
                continue;
            }
            let ok = pubkey_from_hex(&ds.pubkey_hex)
                .ok()
                .zip(sig_from_hex(&ds.signature).ok())
                .map(|(pk, sig)| pk.verify(&payload, &sig).is_ok())
                .unwrap_or(false);
            if ok {
                verified.entry(ds.lct_id).or_insert(ds);
            }
        }

        // Rule 5: derive, never trust claimed_assurance.
        let has_hardware = verified.values().any(|s| s.device_type == DeviceType::Hardware);
        Ok(if has_hardware {
            AssuranceLevel::HardwareBacked
        } else if verified.len() >= 2 {
            AssuranceLevel::MultiDevice
        } else {
            AssuranceLevel::SingleDevice
        })
    }
}

fn pubkey_from_hex(hex_str: &str) -> anyhow::Result<PublicKey> {
    let bytes = hex::decode(hex_str)?;
    let arr: [u8; 32] = bytes
        .as_slice()
        .try_into()
        .map_err(|_| anyhow::anyhow!("pubkey must be 32 bytes"))?;
    Ok(PublicKey::from_bytes(&arr)?)
}

fn sig_from_hex(hex_str: &str) -> anyhow::Result<SignatureBytes> {
    let bytes = hex::decode(hex_str)?;
    let arr: [u8; 64] = bytes
        .as_slice()
        .try_into()
        .map_err(|_| anyhow::anyhow!("signature must be 64 bytes"))?;
    Ok(SignatureBytes::from_bytes(arr))
}

/// An assurance tier bound to a `pair_id` after a verified presentation.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct TierBinding {
    pub assurance: AssuranceLevel,
    pub bound_at: DateTime<Utc>,
    pub valid_until: DateTime<Utc>,
}

#[derive(Default)]
struct GateInner {
    /// Outstanding challenge nonce per pair — single-use, burned on present.
    pending: HashMap<Uuid, String>,
    /// Verified tier bindings per pair.
    bound: HashMap<Uuid, TierBinding>,
}

/// Per-`pair_id` challenge + tier-binding state (rules 1 and 6). One gate per
/// hub process, shared across handlers; the lock is never held across await.
pub struct ConstellationGate {
    max_age: Duration,
    validity: Duration,
    inner: Mutex<GateInner>,
}

impl Default for ConstellationGate {
    fn default() -> Self {
        Self::new()
    }
}

impl ConstellationGate {
    /// Memo-suggested windows: 5-min attestation max age, 1-h tier validity.
    pub const DEFAULT_MAX_AGE_SECS: i64 = 300;
    pub const DEFAULT_VALIDITY_SECS: i64 = 3600;

    pub fn new() -> Self {
        Self::with_windows(
            Duration::seconds(Self::DEFAULT_MAX_AGE_SECS),
            Duration::seconds(Self::DEFAULT_VALIDITY_SECS),
        )
    }

    pub fn with_windows(max_age: Duration, validity: Duration) -> Self {
        Self { max_age, validity, inner: Mutex::new(GateInner::default()) }
    }

    /// Mint a fresh challenge nonce for this pair. Re-challenging replaces
    /// any outstanding nonce (there is at most one live challenge per pair).
    pub fn mint_challenge(&self, pair_id: Uuid) -> String {
        let nonce = hex::encode(rand::random::<[u8; 32]>());
        self.inner.lock().unwrap().pending.insert(pair_id, nonce.clone());
        nonce
    }

    /// Rule 1 then rules 2–5 then rule 6. The outstanding challenge is burned
    /// on ANY presentation attempt — a failed verify forces a re-challenge
    /// rather than leaving the nonce open to further tries.
    pub fn present(
        &self,
        pair_id: Uuid,
        att: &ConstellationAttestation,
        pinned_owner_pubkey_hex: &str,
        now: DateTime<Utc>,
    ) -> Result<TierBinding, VerifyError> {
        let expected = self
            .inner
            .lock()
            .unwrap()
            .pending
            .remove(&pair_id)
            .ok_or(VerifyError::NoChallenge)?;
        if att.challenge_nonce != expected {
            return Err(VerifyError::NonceMismatch);
        }
        let assurance = att.verify(pinned_owner_pubkey_hex, self.max_age, now)?;
        let binding = TierBinding {
            assurance,
            bound_at: now,
            valid_until: now + self.validity,
        };
        self.inner.lock().unwrap().bound.insert(pair_id, binding.clone());
        Ok(binding)
    }

    /// The current unexpired binding for a pair — the hook the trust / read-
    /// scoping layers will consume. Expired bindings are dropped and return
    /// None (rule 6: re-challenge on expiry, never silently extend).
    pub fn assurance(&self, pair_id: Uuid, now: DateTime<Utc>) -> Option<TierBinding> {
        let mut g = self.inner.lock().unwrap();
        match g.bound.get(&pair_id) {
            Some(b) if b.valid_until > now => Some(b.clone()),
            Some(_) => {
                g.bound.remove(&pair_id);
                None
            }
            None => None,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use web4_core::crypto::KeyPair;

    /// Build + sign an attestation the way hestia's `create` does, so the
    /// daemon e2e tests and these unit tests exercise the real contract.
    pub(crate) fn make_att(
        owner_kp: &KeyPair,
        owner_lct: Uuid,
        roster: &[Uuid],
        cosigners: &[(Uuid, DeviceType, &KeyPair)],
        nonce: &str,
        issued_at: DateTime<Utc>,
    ) -> ConstellationAttestation {
        let payload = signing_payload(owner_lct, roster, nonce, &issued_at);
        ConstellationAttestation {
            owner_lct_id: owner_lct,
            owner_pubkey_hex: owner_kp.verifying_key().to_hex(),
            member_lcts: roster.to_vec(),
            challenge_nonce: nonce.to_string(),
            issued_at,
            claimed_assurance: AssuranceLevel::SingleDevice,
            owner_signature: owner_kp.sign(&payload).to_hex(),
            device_signatures: cosigners
                .iter()
                .map(|(lct, dt, kp)| DeviceSignature {
                    lct_id: *lct,
                    device_type: dt.clone(),
                    pubkey_hex: kp.verifying_key().to_hex(),
                    signature: kp.sign(&payload).to_hex(),
                })
                .collect(),
        }
    }

    fn ts(s: &str) -> DateTime<Utc> {
        DateTime::parse_from_rfc3339(s).unwrap().with_timezone(&Utc)
    }

    /// The cross-repo contract anchor (review criterion 4): a fixed input
    /// must produce exactly this payload hash. hestia's `signing_payload`
    /// over the same input yields the same 32 bytes — any domain-tag or
    /// length-framing drift on either side breaks this constant.
    #[test]
    fn test_vector_payload_hash() {
        let owner = Uuid::parse_str("00000000-0000-4000-8000-000000000001").unwrap();
        let members = [
            Uuid::parse_str("00000000-0000-4000-8000-0000000000aa").unwrap(),
            Uuid::parse_str("00000000-0000-4000-8000-0000000000bb").unwrap(),
        ];
        let issued_at = ts("2026-06-11T00:00:00+00:00");
        let payload = signing_payload(owner, &members, "test-vector-nonce", &issued_at);
        assert_eq!(
            hex::encode(&payload),
            "a30b8d41895709aae3bc2956922bcb434897383beb597af0bbe7ad28242fb31b",
        );
    }

    /// Companion to the payload vector: a known attestation resolves to a
    /// known tier (deterministic keys → mechanically checkable end to end).
    #[test]
    fn test_vector_known_att_resolves_hardware_backed() {
        let owner_kp = KeyPair::from_secret_bytes(&[7u8; 32]);
        let desk_kp = KeyPair::from_secret_bytes(&[1u8; 32]);
        let hw_kp = KeyPair::from_secret_bytes(&[2u8; 32]);
        let owner = Uuid::parse_str("00000000-0000-4000-8000-000000000001").unwrap();
        let desk = Uuid::parse_str("00000000-0000-4000-8000-0000000000aa").unwrap();
        let hw = Uuid::parse_str("00000000-0000-4000-8000-0000000000bb").unwrap();
        let issued_at = ts("2026-06-11T00:00:00+00:00");
        let att = make_att(
            &owner_kp,
            owner,
            &[desk, hw],
            &[(desk, DeviceType::Desktop, &desk_kp), (hw, DeviceType::Hardware, &hw_kp)],
            "test-vector-nonce",
            issued_at,
        );
        let tier = att
            .verify(&owner_kp.verifying_key().to_hex(), Duration::minutes(5), issued_at)
            .unwrap();
        assert_eq!(tier, AssuranceLevel::HardwareBacked);
    }

    #[test]
    fn tiers_derived_from_verified_cosigns_not_claims() {
        let owner_kp = KeyPair::generate();
        let owner = Uuid::new_v4();
        let (d1, d2) = (Uuid::new_v4(), Uuid::new_v4());
        let (k1, k2) = (KeyPair::generate(), KeyPair::generate());
        let now = Utc::now();
        let pinned = owner_kp.verifying_key().to_hex();

        // 0 co-signs → single_device.
        let att = make_att(&owner_kp, owner, &[d1, d2], &[], "n", now);
        assert_eq!(att.verify(&pinned, Duration::minutes(5), now).unwrap(),
            AssuranceLevel::SingleDevice);

        // 2 co-signs → multi_device.
        let att = make_att(&owner_kp, owner, &[d1, d2],
            &[(d1, DeviceType::Desktop, &k1), (d2, DeviceType::Mobile, &k2)], "n", now);
        assert_eq!(att.verify(&pinned, Duration::minutes(5), now).unwrap(),
            AssuranceLevel::MultiDevice);

        // Inflated claim, 1 real co-sign → still single_device.
        let mut att = make_att(&owner_kp, owner, &[d1, d2],
            &[(d1, DeviceType::Desktop, &k1)], "n", now);
        att.claimed_assurance = AssuranceLevel::HardwareBacked;
        assert_eq!(att.verify(&pinned, Duration::minutes(5), now).unwrap(),
            AssuranceLevel::SingleDevice);
    }

    #[test]
    fn duplicate_device_sig_cannot_inflate_tier() {
        let owner_kp = KeyPair::generate();
        let owner = Uuid::new_v4();
        let d1 = Uuid::new_v4();
        let k1 = KeyPair::generate();
        let now = Utc::now();
        // Same device co-signing twice is still ONE verified device.
        let att = make_att(&owner_kp, owner, &[d1],
            &[(d1, DeviceType::Desktop, &k1), (d1, DeviceType::Desktop, &k1)], "n", now);
        assert_eq!(
            att.verify(&owner_kp.verifying_key().to_hex(), Duration::minutes(5), now).unwrap(),
            AssuranceLevel::SingleDevice
        );
    }

    #[test]
    fn non_roster_and_garbage_sigs_dropped_silently() {
        let owner_kp = KeyPair::generate();
        let owner = Uuid::new_v4();
        let d1 = Uuid::new_v4();
        let k1 = KeyPair::generate();
        let now = Utc::now();
        let mut att = make_att(&owner_kp, owner, &[d1],
            &[(d1, DeviceType::Hardware, &k1)], "n", now);
        // A non-roster co-sign and a garbage sig must not error the
        // attestation — they just add nothing.
        att.device_signatures.push(DeviceSignature {
            lct_id: Uuid::new_v4(), // not in roster
            device_type: DeviceType::Hardware,
            pubkey_hex: k1.verifying_key().to_hex(),
            signature: att.device_signatures[0].signature.clone(),
        });
        att.device_signatures.push(DeviceSignature {
            lct_id: d1,
            device_type: DeviceType::Desktop,
            pubkey_hex: "zz".into(), // malformed
            signature: "zz".into(),
        });
        assert_eq!(
            att.verify(&owner_kp.verifying_key().to_hex(), Duration::minutes(5), now).unwrap(),
            AssuranceLevel::HardwareBacked
        );
    }

    #[test]
    fn stale_and_foreign_owner_key_rejected() {
        let owner_kp = KeyPair::generate();
        let owner = Uuid::new_v4();
        let now = Utc::now();
        let pinned = owner_kp.verifying_key().to_hex();

        let att = make_att(&owner_kp, owner, &[], &[], "n", now - Duration::minutes(6));
        assert_eq!(att.verify(&pinned, Duration::minutes(5), now), Err(VerifyError::Stale));

        let att = make_att(&owner_kp, owner, &[], &[], "n", now);
        let foreign_pinned = KeyPair::generate().verifying_key().to_hex();
        assert_eq!(
            att.verify(&foreign_pinned, Duration::minutes(5), now),
            Err(VerifyError::ForeignOwnerKey)
        );
    }

    #[test]
    fn tampered_roster_breaks_owner_signature() {
        let owner_kp = KeyPair::generate();
        let owner = Uuid::new_v4();
        let now = Utc::now();
        let mut att = make_att(&owner_kp, owner, &[Uuid::new_v4()], &[], "n", now);
        att.member_lcts.push(Uuid::new_v4()); // phantom device
        assert_eq!(
            att.verify(&owner_kp.verifying_key().to_hex(), Duration::minutes(5), now),
            Err(VerifyError::OwnerSignatureInvalid)
        );
    }

    #[test]
    fn gate_nonce_is_single_use_and_burned() {
        let gate = ConstellationGate::new();
        let pair = Uuid::new_v4();
        let owner_kp = KeyPair::generate();
        let owner = Uuid::new_v4();
        let pinned = owner_kp.verifying_key().to_hex();
        let now = Utc::now();

        // No challenge yet → refused.
        let att = make_att(&owner_kp, owner, &[], &[], "whatever", now);
        assert_eq!(gate.present(pair, &att, &pinned, now), Err(VerifyError::NoChallenge));

        // Mint → present → bound.
        let nonce = gate.mint_challenge(pair);
        let att = make_att(&owner_kp, owner, &[], &[], &nonce, now);
        let binding = gate.present(pair, &att, &pinned, now).unwrap();
        assert_eq!(binding.assurance, AssuranceLevel::SingleDevice);
        assert_eq!(binding.valid_until, now + Duration::hours(1));

        // Replay of the same attestation → nonce already burned.
        assert_eq!(gate.present(pair, &att, &pinned, now), Err(VerifyError::NoChallenge));

        // Wrong nonce burns the outstanding challenge too: present with a
        // stale nonce fails AND a follow-up with the right one now finds
        // nothing pending.
        let fresh = gate.mint_challenge(pair);
        let stale_att = make_att(&owner_kp, owner, &[], &[], "not-the-nonce", now);
        assert_eq!(gate.present(pair, &stale_att, &pinned, now), Err(VerifyError::NonceMismatch));
        let right_att = make_att(&owner_kp, owner, &[], &[], &fresh, now);
        assert_eq!(gate.present(pair, &right_att, &pinned, now), Err(VerifyError::NoChallenge));
    }

    #[test]
    fn binding_expires_and_requires_rechallenge() {
        let gate = ConstellationGate::new();
        let pair = Uuid::new_v4();
        let owner_kp = KeyPair::generate();
        let owner = Uuid::new_v4();
        let pinned = owner_kp.verifying_key().to_hex();
        let now = Utc::now();

        let nonce = gate.mint_challenge(pair);
        let att = make_att(&owner_kp, owner, &[], &[], &nonce, now);
        gate.present(pair, &att, &pinned, now).unwrap();

        assert!(gate.assurance(pair, now + Duration::minutes(59)).is_some());
        // Past valid_until → gone, never silently extended.
        assert!(gate.assurance(pair, now + Duration::minutes(61)).is_none());
        // And it stays gone until a new challenge/present cycle.
        assert!(gate.assurance(pair, now + Duration::minutes(59)).is_none());
    }
}
