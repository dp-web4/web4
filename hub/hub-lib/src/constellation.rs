// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Hub-side constellation attestation verification — the verifier half of the
//! challenge-response MFA contract whose member half ships in hestia
//! (`core/src/constellation.rs`).
//!
//! Wire contract: `shared-context/forum/legion-constellation-attestation-wire-shape-2026-06-11.md`
//! (greenlit in `hub-to-legion-constellation-pr-greenlight-2026-06-11.md`).
//! The structs here mirror hestia's serde shape and the signing payload is
//! byte-for-byte identical — `test_vector_payload_hash` pins THIS repo's
//! construction to a fixed constant.
//!
//! **That constant is not a cross-repo gate, and this comment used to claim it
//! was** (measured 2026-07-30): hestia contains no counterpart test — neither the
//! vector nor the string `test-vector-nonce` appears anywhere in that repo — so
//! drift in hestia's half fails nothing here. The two constructions *are*
//! identical today, verified by re-deriving the constant from the wire memo
//! independently of either implementation. What is missing is the gate, not the
//! agreement. hestia owes the mirror-image vector; tracked in
//! `hub-to-legion-the-constellation-attestation-signs-a-string-it-does-not-transmit-2026-07-30.md`.
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

use chrono::{DateTime, Duration, SecondsFormat, Utc};
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

impl AssuranceLevel {
    /// The tier's **wire tag** — the same snake_case string serde emits, pinned
    /// here as an explicit contract. Signed payloads use this, never
    /// `format!("{:?}")`: a `Debug` impl is a Rust convenience, and a portable
    /// receipt a non-Rust verifier must reproduce cannot be anchored to one.
    pub fn wire_tag(&self) -> &'static str {
        match self {
            Self::SingleDevice => "single_device",
            Self::MultiDevice => "multi_device",
            Self::HardwareBacked => "hardware_backed",
        }
    }
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

/// Whether an enrolled device's key is currently authorized to contribute
/// assurance. A `Revoked`/`Suspended` device counts for NOTHING even if its key
/// can still produce a valid signature. `#[serde(default)]` sites migrate to Active.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Default, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DeviceStatus {
    #[default]
    Active,
    Suspended,
    Revoked,
}

/// The AUTHORITATIVE per-device record — the owner committed it (signed) BEFORE
/// the challenge, and the hub resolves the verifier's device facts from here, not
/// from the presented attestation (GPT constellation-assurance report, 2026-07-21).
/// The presenter identifies a device and proves possession; it is never
/// authoritative for that device's key or class.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct EnrolledDevice {
    pub owner_lct_id: Uuid,
    pub device_lct_id: Uuid,
    /// The device's enrolled Ed25519 public key (hex) — signatures verify against
    /// THIS, never against a key carried in the attestation.
    pub pubkey_hex: String,
    /// Owner-committed class. `Hardware` here means "the owner committed this as a
    /// hardware device pre-challenge" — strictly stronger than a presenter label,
    /// and a future `hardware_evidence` layer (TPM/Secure-Enclave) upgrades it to
    /// *verified* hardware.
    pub device_class: DeviceType,
    #[serde(default)]
    pub status: DeviceStatus,
    pub enrolled_at: DateTime<Utc>,
    #[serde(default)]
    pub enrollment_version: u64,
}

/// The set of enrolled devices the verifier resolves against, keyed by
/// `(owner_lct, device_lct)`. In the hub this is projected from the ledger's
/// `DeviceEnrolled`/`DeviceRevoked` events (Phase 2); tests build it directly.
#[derive(Clone, Debug, Default)]
pub struct EnrolledDeviceSet {
    devices: HashMap<(Uuid, Uuid), EnrolledDevice>,
}

impl EnrolledDeviceSet {
    pub fn new() -> Self {
        Self { devices: HashMap::new() }
    }

    pub fn insert(&mut self, d: EnrolledDevice) {
        self.devices.insert((d.owner_lct_id, d.device_lct_id), d);
    }

    pub fn get(&self, owner: Uuid, device: Uuid) -> Option<&EnrolledDevice> {
        self.devices.get(&(owner, device))
    }

    pub fn len(&self) -> usize {
        self.devices.len()
    }

    pub fn is_empty(&self) -> bool {
        self.devices.is_empty()
    }
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
    /// Canonical on the wire (fixed-width nanoseconds, `Z`) so the transmitted
    /// spelling is the one [`signing_payload_v2`] signs. The shim's deserializer
    /// accepts any valid RFC3339, so v1 members — which emit chrono's `AutoSi`
    /// default — parse unchanged.
    #[serde(with = "canonical_ts")]
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
    #[error("attestation is future-dated beyond allowed skew")]
    FutureDated,
    #[error("owner_pubkey_hex does not match this member's pinned key")]
    ForeignOwnerKey,
    #[error("owner signature does not verify")]
    OwnerSignatureInvalid,
    #[error("hub signature on the assurance receipt does not verify")]
    ReceiptSignatureInvalid,
    #[error("the supplied hub key is not the key this receipt was signed by")]
    SignerKeyMismatch,
    #[error("malformed attestation: {0}")]
    Malformed(String),
}

/// Deterministic signing payload, **v1** — byte-for-byte the hestia construction:
/// SHA-256 over `"web4:constellation-attest:v1:"` ‖ owner uuid (16 bytes) ‖
/// nonce (utf8) ‖ issued_at (`to_rfc3339()`, utf8) ‖ each member uuid (16 bytes).
///
/// **Signs a string it does not transmit.** `to_rfc3339()` spells the instant
/// `…+00:00`; the JSON that crosses the wire carries chrono's serde default,
/// `…Z`. Those are different bytes and therefore a different SHA-256 — measured
/// on the shipped test vector, the same inputs hash to `a30b8d41…` under the
/// signed spelling and `7f051de2…` under the transmitted one. It works today only
/// because both peers reconstruct the payload from the *parsed* `DateTime<Utc>`
/// rather than from the string they received, so the divergence is invisible
/// until someone verifies from the wire alone — exactly the defect
/// `signing_bytes` v3 fixed for [`AssuranceReceipt`] (see [`canonical_timestamp`]).
/// `AutoSi` also varies the fractional width with the value, so any hop that
/// re-serializes at lower precision (a millisecond-resolution JS relying party, a
/// microsecond DB column) silently changes the bytes the signature covers.
///
/// Retained because members still emit it, and accepted by
/// [`ConstellationAttestation::verify_enrolled`] for exactly that reason.
/// Prefer [`signing_payload_v2`]; this is scheduled for retirement once hestia
/// emits v2 (receiver first, senders last — the #595 pattern).
pub fn signing_payload(
    owner: Uuid,
    members: &[Uuid],
    nonce: &str,
    issued_at: &DateTime<Utc>,
) -> Vec<u8> {
    signing_payload_parts(
        b"web4:constellation-attest:v1:",
        owner,
        members,
        nonce,
        &issued_at.to_rfc3339(),
    )
}

/// Deterministic signing payload, **v2** — identical field order to
/// [`signing_payload`], with the two changes that make an attestation verifiable
/// from its own JSON: the domain tag is bumped to `v2`, and `issued_at` is spelled
/// by [`canonical_timestamp`] — the same function the serde shim writes to the
/// wire. A relying party holding nothing but the attestation's JSON can rebuild
/// these bytes using the transmitted strings verbatim.
///
/// The tag bump is what keeps that safe: v1 and v2 bytes can never collide, so
/// accepting both is a strict superset of today's behaviour and not a
/// cross-protocol confusion (a forger still needs a signature from the pinned
/// owner key under one spelling or the other).
pub fn signing_payload_v2(
    owner: Uuid,
    members: &[Uuid],
    nonce: &str,
    issued_at: &DateTime<Utc>,
) -> Vec<u8> {
    signing_payload_parts(
        b"web4:constellation-attest:v2:",
        owner,
        members,
        nonce,
        &canonical_timestamp(issued_at),
    )
}

/// The one construction both versions share — they differ only in the domain tag
/// and how `issued_at` was spelled, so the field order cannot drift between them.
/// Taking the timestamp as an already-formatted `&str` is deliberate: it is what
/// lets a verifier feed in the string it received rather than one it re-derived.
fn signing_payload_parts(
    tag: &[u8],
    owner: Uuid,
    members: &[Uuid],
    nonce: &str,
    issued_at: &str,
) -> Vec<u8> {
    let mut buf = Vec::with_capacity(128);
    buf.extend_from_slice(tag);
    buf.extend_from_slice(owner.as_bytes());
    buf.extend_from_slice(nonce.as_bytes());
    buf.extend_from_slice(issued_at.as_bytes());
    for m in members {
        buf.extend_from_slice(m.as_bytes());
    }
    sha256(&buf).to_vec()
}

impl ConstellationAttestation {
    /// The original presented-key verifier (device sigs checked against the
    /// attestation's OWN `pubkey_hex`, class from its OWN `device_type`).
    ///
    /// **RETIRED from the API (2026-07-21): `#[cfg(test)]`-only.** It was the
    /// network self-authentication hole — an owner-key holder could mint fresh
    /// keys, label them `Hardware`, and forge a tier (GPT report). Every path now
    /// uses [`Self::verify_enrolled`], which resolves device facts from the
    /// authoritative enrollment registry. This is kept only so the historical
    /// presented-key behavior tests still document what changed; a production
    /// caller can't name it.
    #[cfg(test)]
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

    /// **The authoritative verifier** (GPT constellation-assurance fix, 2026-07-21).
    /// Resolves every device fact — public key, class, status — from `enrolled`
    /// (owner-committed BEFORE the challenge), NOT from the presented attestation.
    /// The presented `pubkey_hex`/`device_type` are ignored entirely. Closes the
    /// network self-authentication hole: an owner-key holder can no longer mint
    /// fresh keys, label them `Hardware`, and inflate the tier.
    ///
    /// Differences from [`Self::verify`] (retained until Phase 3):
    /// - each device signature is checked against the ENROLLED pubkey;
    /// - device class (`Hardware`) comes from the ENROLLED record;
    /// - only `Active` enrolled devices count; unenrolled/revoked add nothing;
    /// - `issued_at` must be fresh AND not future-dated beyond `future_skew`
    ///   (GPT #5 — a future timestamp yields a negative age that slips `> max_age`).
    pub fn verify_enrolled(
        &self,
        pinned_owner_pubkey_hex: &str,
        enrolled: &EnrolledDeviceSet,
        max_age: Duration,
        future_skew: Duration,
        now: DateTime<Utc>,
    ) -> Result<AssuranceLevel, VerifyError> {
        let age = now - self.issued_at;
        if age > max_age {
            return Err(VerifyError::Stale);
        }
        if age < -future_skew {
            return Err(VerifyError::FutureDated);
        }
        if !self.owner_pubkey_hex.eq_ignore_ascii_case(pinned_owner_pubkey_hex) {
            return Err(VerifyError::ForeignOwnerKey);
        }

        // Owner: verify against the PINNED (trusted) key.
        let owner_pk = pubkey_from_hex(&self.owner_pubkey_hex)
            .map_err(|e| VerifyError::Malformed(format!("owner pubkey: {e}")))?;
        let owner_sig = sig_from_hex(&self.owner_signature)
            .map_err(|e| VerifyError::Malformed(format!("owner signature: {e}")))?;

        // Receiver first, senders last (#595): accept v2, still accept v1 while
        // members emit it. The version the OWNER signed fixes the payload for the
        // device signatures too — owner and devices sign the same bytes, so
        // resolving each independently would let a v1 device co-sign ride on a v2
        // owner signature and vice versa.
        let payload = [
            signing_payload_v2(
                self.owner_lct_id,
                &self.member_lcts,
                &self.challenge_nonce,
                &self.issued_at,
            ),
            signing_payload(
                self.owner_lct_id,
                &self.member_lcts,
                &self.challenge_nonce,
                &self.issued_at,
            ),
        ]
        .into_iter()
        .find(|p| owner_pk.verify(p, &owner_sig).is_ok())
        .ok_or(VerifyError::OwnerSignatureInvalid)?;

        // Devices: resolve every fact from the enrollment registry. Collapse
        // duplicate lct_ids so one device signed twice is still one. A signature
        // whose device is unenrolled, revoked, or signed with a key other than its
        // ENROLLED key contributes nothing (silent drop — rule 4 stays).
        let mut counted: std::collections::HashSet<Uuid> = std::collections::HashSet::new();
        let mut classes: Vec<DeviceType> = Vec::new();
        for ds in &self.device_signatures {
            if !counted.insert(ds.lct_id) {
                continue;
            }
            let Some(rec) = enrolled.get(self.owner_lct_id, ds.lct_id) else {
                continue; // not an enrolled device of this owner — presenter can't invent one
            };
            if rec.status != DeviceStatus::Active {
                continue; // revoked/suspended keys never count
            }
            let ok = pubkey_from_hex(&rec.pubkey_hex) // the ENROLLED key, not ds.pubkey_hex
                .ok()
                .zip(sig_from_hex(&ds.signature).ok())
                .map(|(pk, sig)| pk.verify(&payload, &sig).is_ok())
                .unwrap_or(false);
            if ok {
                classes.push(rec.device_class.clone()); // the ENROLLED class, not ds.device_type
            }
        }

        Ok(if classes.iter().any(|c| *c == DeviceType::Hardware) {
            AssuranceLevel::HardwareBacked
        } else if classes.len() >= 2 {
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

/// The **one** spelling of a receipt timestamp: RFC3339, always exactly nine
/// fractional digits, always `Z`.
///
/// This exists so the string the hub TRANSMITS and the string the hub SIGNS come
/// out of the same function. Under `signing_bytes` v2 they did not: the signed
/// form was `DateTime::to_rfc3339()` (`…+00:00`) while the wire form was chrono's
/// serde default (`…Z`), so a relying party could not reconstruct the canonical
/// bytes from the JSON it was handed without knowing a chrono-specific quirk —
/// measured 2026-07-30 and worked around with a `Z` → `+00:00` shim in
/// `tools/verify_assurance_receipt.py`.
///
/// [`SecondsFormat::Nanos`] rather than `AutoSi` because `AutoSi` varies the
/// fractional digit count with the *value* (0, 3, or 9), so the field's width
/// depended on whether the clock happened to land on a whole second — the fixture
/// timestamp `2099-01-01T00:00:00Z` and a live `…13.302191724Z` were the same
/// field in two shapes. `Nanos` is fixed-width AND lossless at
/// `DateTime<Utc>`'s own resolution, so canonicalizing costs no precision and
/// needs no truncation: `parse_from_rfc3339(canonical_timestamp(t)) == t`.
pub fn canonical_timestamp(t: &DateTime<Utc>) -> String {
    t.to_rfc3339_opts(SecondsFormat::Nanos, true)
}

/// Serde shim binding the wire form to [`canonical_timestamp`]. Applied to every
/// timestamp `signing_bytes` covers, so "sign what you send" is enforced by
/// construction instead of by two definitions agreeing by luck.
mod canonical_ts {
    use super::{canonical_timestamp, DateTime, Utc};
    use serde::{Deserialize, Deserializer, Serializer};

    pub fn serialize<S: Serializer>(t: &DateTime<Utc>, s: S) -> Result<S::Ok, S::Error> {
        s.serialize_str(&canonical_timestamp(t))
    }

    /// Accepts any valid RFC3339 instant, not just our own output: a verifier
    /// must be able to hand back a receipt it received, and being strict here
    /// would reject well-formed input for no integrity gain — the signature,
    /// not the parser, is what detects tampering.
    pub fn deserialize<'de, D: Deserializer<'de>>(d: D) -> Result<DateTime<Utc>, D::Error> {
        let s = String::deserialize(d)?;
        DateTime::parse_from_rfc3339(&s)
            .map(|t| t.with_timezone(&Utc))
            .map_err(serde::de::Error::custom)
    }
}

/// A **portable, hub-signed assurance receipt** (A2 evidence, 2026-07-29). The hub
/// issues this after a verified `present_constellation`: it binds the derived tier
/// to the exact owner + roster + challenge, and the hub SIGNS it. A relying party
/// verifies the signature with the hub's public key and checks freshness —
/// **without running Hestia or trusting the presenter** (PRD_ASSURANCE A2: "verify
/// a signed decision before acting"). Trust in the hub identity itself is the
/// relying party's to establish — inspectable evidence, not prescribed trust.
///
/// **The receipt never carries a usable verification key.** It names its signer
/// two ways the holder cannot forge into authority: `hub_signer_lct_id` (resolve
/// it to a published LCT) and `hub_signer_key_id` (a truncated fingerprint —
/// enough to *select* among keys you already trust, useless for verifying). The
/// key itself must arrive out of band. Carrying the full pubkey would let a
/// relying party do the natural-looking thing —
/// `receipt.verify(&pubkey_from_hex(&receipt.<key>)?, now)` — and accept a wholly
/// fabricated receipt signed by an attacker's keypair with `tier:
/// HardwareBacked`. That is JWT `jwk`-header confusion, and it is the same
/// self-authentication hole `verify_enrolled` guards with `ForeignOwnerKey`
/// (see the `verify()` docs at rules 3/4 above). A fingerprint cannot be
/// inflated into a key, so the trap does not exist to be walked into.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct AssuranceReceipt {
    pub owner_lct_id: Uuid,
    pub tier: AssuranceLevel,
    pub pair_id: Uuid,
    pub challenge_nonce: String,
    /// The attestation's `issued_at` (binds the receipt to that specific challenge).
    #[serde(with = "canonical_ts")]
    pub issued_at: DateTime<Utc>,
    #[serde(with = "canonical_ts")]
    pub bound_at: DateTime<Utc>,
    #[serde(with = "canonical_ts")]
    pub valid_until: DateTime<Utc>,
    /// The hub **society** LCT — the hub record, NOT the signing identity.
    pub hub_lct_id: Uuid,
    /// The LCT whose key actually produced `signature`. On a live hub this differs
    /// from `hub_lct_id` (society id `edf4d5ba-…` vs the sovereign LCT), so a
    /// relying party resolving "the hub's published LCT" from `hub_lct_id` alone
    /// resolves the wrong record and can never name the key holder.
    pub hub_signer_lct_id: Uuid,
    /// **Key selector, not a key**: the first 8 bytes of `sha256(pubkey)`, hex.
    /// Lets a relying party pick the right key out of the set it already trusts,
    /// and yields a precise [`VerifyError::SignerKeyMismatch`] when it picks
    /// wrong. It is NOT sufficient to verify with — deliberately.
    pub hub_signer_key_id: String,
    /// `sha256` over the device roster in **sorted** order — binds the tier to the
    /// EXACT device set, so a receipt can't be replayed for a different
    /// constellation, and a relying party holding that set can recompute it
    /// without knowing the order the presenter happened to use.
    pub roster_hash: String,
    /// The hub's Ed25519 signature over [`Self::signing_bytes`], hex. Empty until signed.
    pub signature: String,
}

impl AssuranceReceipt {
    /// The `hub_signer_key_id` for a key — first 8 bytes of `sha256(pubkey)`, hex.
    /// A selector, deliberately too short and too one-way to serve as a key.
    pub fn key_id(pubkey: &PublicKey) -> String {
        hex::encode(&sha256(&pubkey.to_bytes())[..8])
    }

    /// SHA-256 over the roster in **sorted** order — deterministic and
    /// cross-implementation, so any verifier holding the same device set computes
    /// the same hash regardless of presentation order. (Roster order carries no
    /// meaning here: the tier is derived from the enrolled set, not a sequence.)
    pub fn roster_hash(roster: &[Uuid]) -> String {
        let mut sorted: Vec<&Uuid> = roster.iter().collect();
        sorted.sort_unstable();
        let mut buf = Vec::with_capacity(16 * roster.len());
        for r in sorted {
            buf.extend_from_slice(r.as_bytes());
        }
        hex::encode(sha256(&buf))
    }

    /// Canonical bytes the hub signs — **every field except `signature`**, with
    /// no exceptions: the signer's identity and key id are inside the tag, so a
    /// holder cannot re-point a valid receipt at a different signer. A version
    /// tag domains it; field order is fixed. Any drift breaks the sig.
    ///
    /// `v2` (2026-07-29): `v1` omitted the signer's key id, carried no signer
    /// identity at all, and spelled the tier with Rust's `Debug` impl. The byte
    /// layout changed, so the tag had to; no `v1` receipt was ever issued (the
    /// primitive had not yet reached a running daemon), so nothing is stranded.
    ///
    /// `v3` (2026-07-30): **the hub now signs the string it transmits.** `v2` fed
    /// `to_rfc3339()` (`…+00:00`) into these bytes while serialising `…Z` onto the
    /// wire, so the canonical bytes were not reconstructable from a received
    /// receipt — a standalone verifier had to guess a chrono spelling. Both sides
    /// now go through [`canonical_timestamp`], and
    /// `signed_bytes_are_reconstructable_from_the_wire_alone` asserts exactly that
    /// by rebuilding these bytes from parsed JSON. The layout changed, so the tag
    /// had to. **No `v2` receipt was ever issued either, and that is measured, not
    /// assumed:** the receipt primitive landed 2026-07-29 16:06 PT (`d5bd10b`)
    /// while the live daemon has been running since 2026-07-27 20:22 PT, and the
    /// running image contains zero occurrences of the `assurance-receipt` domain
    /// string (checked against `/proc/<pid>/exe`, with `query_hub` as the
    /// positive control). Nothing is stranded because nothing was ever emitted.
    pub fn signing_bytes(&self) -> Vec<u8> {
        let mut b = Vec::with_capacity(256);
        b.extend_from_slice(b"web4:assurance-receipt:v3:");
        b.extend_from_slice(self.owner_lct_id.as_bytes());
        b.extend_from_slice(self.tier.wire_tag().as_bytes());
        b.extend_from_slice(self.pair_id.as_bytes());
        b.extend_from_slice(self.challenge_nonce.as_bytes());
        b.extend_from_slice(canonical_timestamp(&self.issued_at).as_bytes());
        b.extend_from_slice(canonical_timestamp(&self.bound_at).as_bytes());
        b.extend_from_slice(canonical_timestamp(&self.valid_until).as_bytes());
        b.extend_from_slice(self.hub_lct_id.as_bytes());
        b.extend_from_slice(self.hub_signer_lct_id.as_bytes());
        b.extend_from_slice(self.hub_signer_key_id.as_bytes());
        b.extend_from_slice(self.roster_hash.as_bytes());
        b
    }

    /// **The relying party's check — no Hestia required.** Verify the hub's
    /// signature over the canonical bytes and confirm the receipt is unexpired.
    ///
    /// `hub_pubkey` MUST come from outside the receipt — pinned, or resolved from
    /// the LCT named by `hub_signer_lct_id`. The receipt cannot supply it (see the
    /// struct docs); `hub_signer_key_id` only confirms the caller brought the key
    /// this receipt was actually signed by, turning "wrong hub" from an opaque
    /// signature failure into [`VerifyError::SignerKeyMismatch`].
    pub fn verify(&self, hub_pubkey: &PublicKey, now: DateTime<Utc>) -> Result<(), VerifyError> {
        if now > self.valid_until {
            return Err(VerifyError::Stale);
        }
        // Order matters: reject a key that isn't this receipt's signer BEFORE
        // spending a signature verification on it, and never fall through to
        // "well, the bytes verified" for a key the receipt doesn't claim.
        if self.hub_signer_key_id.is_empty() {
            return Err(VerifyError::Malformed(
                "receipt carries no hub_signer_key_id — unattributable, refusing to verify".into(),
            ));
        }
        if Self::key_id(hub_pubkey) != self.hub_signer_key_id {
            return Err(VerifyError::SignerKeyMismatch);
        }
        let sig = sig_from_hex(&self.signature)
            .map_err(|e| VerifyError::Malformed(format!("receipt signature: {e}")))?;
        hub_pubkey
            .verify(&self.signing_bytes(), &sig)
            .map_err(|_| VerifyError::ReceiptSignatureInvalid)
    }
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

    /// Clock skew tolerated on `issued_at` before an attestation is rejected as
    /// future-dated (GPT #5). Small — enough for honest cross-host drift.
    pub const FUTURE_SKEW_SECS: i64 = 120;

    /// Rule 1 then rules 2–5 then rule 6. The outstanding challenge is burned
    /// on ANY presentation attempt — a failed verify forces a re-challenge
    /// rather than leaving the nonce open to further tries.
    ///
    /// Verifies against the AUTHORITATIVE enrollment registry (`enrolled`), not
    /// the presented device facts — the GPT self-authentication fix. `enrolled`
    /// is the hub's projected `enrolled_devices` (owner-committed pre-challenge).
    pub fn present(
        &self,
        pair_id: Uuid,
        att: &ConstellationAttestation,
        pinned_owner_pubkey_hex: &str,
        enrolled: &EnrolledDeviceSet,
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
        let assurance = att.verify_enrolled(
            pinned_owner_pubkey_hex,
            enrolled,
            self.max_age,
            Duration::seconds(Self::FUTURE_SKEW_SECS),
            now,
        )?;
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
        make_att_with(signing_payload, owner_kp, owner_lct, roster, cosigners, nonce, issued_at)
    }

    /// Same, but the caller picks the payload version — so the migration tests can
    /// mint a genuine v1 sender and a genuine v2 sender rather than asserting on
    /// bytes they built by hand.
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn make_att_with(
        payload_fn: fn(Uuid, &[Uuid], &str, &DateTime<Utc>) -> Vec<u8>,
        owner_kp: &KeyPair,
        owner_lct: Uuid,
        roster: &[Uuid],
        cosigners: &[(Uuid, DeviceType, &KeyPair)],
        nonce: &str,
        issued_at: DateTime<Utc>,
    ) -> ConstellationAttestation {
        let payload = payload_fn(owner_lct, roster, nonce, &issued_at);
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

    /// The v2 half of the cross-repo anchor. Both constants were re-derived from
    /// the wire memo's field order by a third implementation (Python, no chrono,
    /// no `web4-core`) before being pinned here, so agreeing with them is evidence
    /// about the *contract* and not about a shared dependency — hub-lib and hestia
    /// both resolve `web4-core` from the same path, which means a shared-crate bug
    /// would otherwise agree with itself.
    #[test]
    fn test_vector_payload_hash_v2() {
        let owner = Uuid::parse_str("00000000-0000-4000-8000-000000000001").unwrap();
        let members = [
            Uuid::parse_str("00000000-0000-4000-8000-0000000000aa").unwrap(),
            Uuid::parse_str("00000000-0000-4000-8000-0000000000bb").unwrap(),
        ];
        let issued_at = ts("2026-06-11T00:00:00+00:00");
        // The same instant, spelled the way the wire spells it.
        assert_eq!(canonical_timestamp(&issued_at), "2026-06-11T00:00:00.000000000Z");
        let payload = signing_payload_v2(owner, &members, "test-vector-nonce", &issued_at);
        assert_eq!(
            hex::encode(&payload),
            "003a19c58b76323f8438168950ad32c19a36f3dc32c126cf89a91e5fece1cf3b",
        );
        // The whole point of the bump, stated as an assertion: same inputs, same
        // instant, different bytes. This is why v1 could not simply be respelled.
        assert_ne!(
            payload,
            signing_payload(owner, &members, "test-vector-nonce", &issued_at)
        );
    }

    /// THE v2 property, mirroring `signed_bytes_are_reconstructable_from_the_wire_alone`
    /// for the attestation. A relying party holding only the JSON must be able to
    /// rebuild the signed bytes from the transmitted strings verbatim.
    #[test]
    fn attestation_v2_bytes_are_reconstructable_from_the_wire_alone() {
        let owner_kp = KeyPair::from_secret_bytes(&[9u8; 32]);
        let owner = Uuid::new_v4();
        let roster = vec![Uuid::new_v4(), Uuid::new_v4()];
        // A live-clock-shaped instant: under AutoSi this is 9 fractional digits,
        // whereas the v1 vector's whole second is zero — the width spread that
        // makes the defect intermittent rather than total.
        let issued = ts("2026-07-30T04:03:13.302191724Z");
        let att = make_att_with(
            signing_payload_v2, &owner_kp, owner, &roster, &[], "wire-nonce", issued,
        );

        let json = serde_json::to_string(&att).unwrap();
        let wire: serde_json::Value = serde_json::from_str(&json).unwrap();
        let s = |k: &str| wire[k].as_str().unwrap_or_default().to_string();

        // A standalone verifier's arithmetic: the strings as received, nothing
        // re-formatted, no chrono.
        let mut rebuilt = Vec::new();
        rebuilt.extend_from_slice(b"web4:constellation-attest:v2:");
        rebuilt.extend_from_slice(Uuid::parse_str(&s("owner_lct_id")).unwrap().as_bytes());
        rebuilt.extend_from_slice(s("challenge_nonce").as_bytes());
        rebuilt.extend_from_slice(s("issued_at").as_bytes());
        for m in wire["member_lcts"].as_array().unwrap() {
            rebuilt.extend_from_slice(Uuid::parse_str(m.as_str().unwrap()).unwrap().as_bytes());
        }
        let rebuilt = sha256(&rebuilt).to_vec();

        assert_eq!(
            rebuilt,
            signing_payload_v2(owner, &roster, "wire-nonce", &issued),
            "the transmitted strings no longer rebuild the signed payload"
        );
        // Internal equality alone could be two identical mistakes; this is the
        // property a relying party actually depends on.
        let sig = sig_from_hex(&att.owner_signature).unwrap();
        assert!(
            owner_kp.verifying_key().verify(&rebuilt, &sig).is_ok(),
            "bytes rebuilt from the wire do not verify against the owner signature"
        );
        assert!(!json.contains("+00:00"), "wire regressed to an offset suffix: {json}");

        // And the v1 construction must still NOT have this property — if it ever
        // gains it, chrono changed underneath us and the rationale needs re-checking.
        assert_ne!(canonical_timestamp(&issued), issued.to_rfc3339());
    }

    /// An owner's ACTIVE enrolled devices, built from the same `enroll` helper the
    /// rest of the enrolled-verifier tests use.
    fn enrolled_set(owner: Uuid, devices: &[(Uuid, &KeyPair, DeviceType)]) -> EnrolledDeviceSet {
        let mut set = EnrolledDeviceSet::new();
        for (id, kp, class) in devices {
            set.insert(enroll(owner, *id, class.clone(), DeviceStatus::Active, kp, Utc::now()));
        }
        set
    }

    /// The migration guarantee: accepting v2 must not stop accepting v1, because
    /// every member in the field still signs v1 (receiver first, senders last).
    #[test]
    fn verify_enrolled_accepts_both_payload_versions() {
        let owner_kp = KeyPair::generate();
        let owner = Uuid::new_v4();
        let (d1, d2) = (Uuid::new_v4(), Uuid::new_v4());
        let (k1, k2) = (KeyPair::generate(), KeyPair::generate());
        let now = Utc::now();
        let pinned = owner_kp.verifying_key().to_hex();
        let enrolled = enrolled_set(
            owner,
            &[(d1, &k1, DeviceType::Desktop), (d2, &k2, DeviceType::Hardware)],
        );
        let cosigners: &[(Uuid, DeviceType, &KeyPair)] =
            &[(d1, DeviceType::Desktop, &k1), (d2, DeviceType::Hardware, &k2)];

        for (label, payload_fn) in [
            ("v1", signing_payload as fn(Uuid, &[Uuid], &str, &DateTime<Utc>) -> Vec<u8>),
            ("v2", signing_payload_v2),
        ] {
            let att = make_att_with(
                payload_fn, &owner_kp, owner, &[d1, d2], cosigners, "n", now,
            );
            assert_eq!(
                att.verify_enrolled(&pinned, &enrolled, Duration::minutes(5), Duration::minutes(2), now),
                Ok(AssuranceLevel::HardwareBacked),
                "{label} attestation must verify and derive its tier from enrolled devices",
            );
        }
    }

    /// A device co-sign under one version must not ride on an owner signature made
    /// under the other: owner and devices sign the SAME bytes, and the owner's
    /// version is what fixes them. The mismatched device contributes nothing, so
    /// the tier degrades rather than the presentation being rejected — rule 4's
    /// silent drop, unchanged.
    #[test]
    fn a_device_cosign_cannot_cross_payload_versions() {
        let owner_kp = KeyPair::generate();
        let owner = Uuid::new_v4();
        let (d1, d2) = (Uuid::new_v4(), Uuid::new_v4());
        let (k1, k2) = (KeyPair::generate(), KeyPair::generate());
        let now = Utc::now();
        let pinned = owner_kp.verifying_key().to_hex();
        let enrolled = enrolled_set(
            owner,
            &[(d1, &k1, DeviceType::Desktop), (d2, &k2, DeviceType::Hardware)],
        );

        // Owner signs v2; the hardware device signs v1 and is spliced in.
        let mut att = make_att_with(
            signing_payload_v2, &owner_kp, owner, &[d1, d2],
            &[(d1, DeviceType::Desktop, &k1)], "n", now,
        );
        let v1 = signing_payload(owner, &[d1, d2], "n", &now);
        att.device_signatures.push(DeviceSignature {
            lct_id: d2,
            device_type: DeviceType::Hardware,
            pubkey_hex: k2.verifying_key().to_hex(),
            signature: k2.sign(&v1).to_hex(),
        });

        assert_eq!(
            att.verify_enrolled(&pinned, &enrolled, Duration::minutes(5), Duration::minutes(2), now),
            Ok(AssuranceLevel::SingleDevice),
            "a v1 hardware co-sign must not inflate a v2 attestation to hardware_backed",
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
        assert_eq!(gate.present(pair, &att, &pinned, &EnrolledDeviceSet::new(), now), Err(VerifyError::NoChallenge));

        // Mint → present → bound.
        let nonce = gate.mint_challenge(pair);
        let att = make_att(&owner_kp, owner, &[], &[], &nonce, now);
        let binding = gate.present(pair, &att, &pinned, &EnrolledDeviceSet::new(), now).unwrap();
        assert_eq!(binding.assurance, AssuranceLevel::SingleDevice);
        assert_eq!(binding.valid_until, now + Duration::hours(1));

        // Replay of the same attestation → nonce already burned.
        assert_eq!(gate.present(pair, &att, &pinned, &EnrolledDeviceSet::new(), now), Err(VerifyError::NoChallenge));

        // Wrong nonce burns the outstanding challenge too: present with a
        // stale nonce fails AND a follow-up with the right one now finds
        // nothing pending.
        let fresh = gate.mint_challenge(pair);
        let stale_att = make_att(&owner_kp, owner, &[], &[], "not-the-nonce", now);
        assert_eq!(gate.present(pair, &stale_att, &pinned, &EnrolledDeviceSet::new(), now), Err(VerifyError::NonceMismatch));
        let right_att = make_att(&owner_kp, owner, &[], &[], &fresh, now);
        assert_eq!(gate.present(pair, &right_att, &pinned, &EnrolledDeviceSet::new(), now), Err(VerifyError::NoChallenge));
    }

    // ---- verify_enrolled: the network self-authentication hole, closed ----

    const SKEW: Duration = Duration::minutes(2);
    fn enroll(owner: Uuid, device: Uuid, class: DeviceType, status: DeviceStatus, kp: &KeyPair, at: DateTime<Utc>) -> EnrolledDevice {
        EnrolledDevice {
            owner_lct_id: owner, device_lct_id: device,
            pubkey_hex: kp.verifying_key().to_hex(),
            device_class: class, status, enrolled_at: at, enrollment_version: 1,
        }
    }

    /// Baseline: two ACTIVE enrolled devices, both co-sign → MultiDevice from the
    /// REGISTRY, not from anything presented.
    #[test]
    fn enrolled_verifier_accepts_two_active_devices() {
        let owner_kp = KeyPair::generate();
        let owner = Uuid::new_v4();
        let (d1, d2) = (Uuid::new_v4(), Uuid::new_v4());
        let (k1, k2) = (KeyPair::generate(), KeyPair::generate());
        let now = Utc::now();
        let mut reg = EnrolledDeviceSet::new();
        reg.insert(enroll(owner, d1, DeviceType::Desktop, DeviceStatus::Active, &k1, now));
        reg.insert(enroll(owner, d2, DeviceType::Mobile, DeviceStatus::Active, &k2, now));
        let att = make_att(&owner_kp, owner, &[d1, d2],
            &[(d1, DeviceType::Desktop, &k1), (d2, DeviceType::Mobile, &k2)], "n", now);
        assert_eq!(
            att.verify_enrolled(&owner_kp.verifying_key().to_hex(), &reg, Duration::minutes(5), SKEW, now).unwrap(),
            AssuranceLevel::MultiDevice);
    }

    /// GPT #1: forged hardware. The enrolled device is Desktop; the attacker
    /// appends a phantom "Hardware" co-sign with a fresh key + made-up device id.
    /// It's unenrolled → ignored; the tier comes from the enrolled Desktop.
    #[test]
    fn enrolled_verifier_rejects_forged_hardware() {
        let owner_kp = KeyPair::generate();
        let owner = Uuid::new_v4();
        let d1 = Uuid::new_v4();
        let k1 = KeyPair::generate();
        let now = Utc::now();
        let mut reg = EnrolledDeviceSet::new();
        reg.insert(enroll(owner, d1, DeviceType::Desktop, DeviceStatus::Active, &k1, now));
        // Attacker appends a phantom Hardware device signed by a brand-new key.
        let phantom = Uuid::new_v4();
        let pk = KeyPair::generate();
        let att = make_att(&owner_kp, owner, &[d1, phantom],
            &[(d1, DeviceType::Desktop, &k1), (phantom, DeviceType::Hardware, &pk)], "n", now);
        assert_eq!(
            att.verify_enrolled(&owner_kp.verifying_key().to_hex(), &reg, Duration::minutes(5), SKEW, now).unwrap(),
            AssuranceLevel::SingleDevice, "phantom Hardware is unenrolled → must not count");
    }

    /// Class comes from the ENROLLED record: a device enrolled as Desktop but
    /// PRESENTED as Hardware does not yield HardwareBacked.
    #[test]
    fn enrolled_verifier_takes_class_from_registry_not_attestation() {
        let owner_kp = KeyPair::generate();
        let owner = Uuid::new_v4();
        let d1 = Uuid::new_v4();
        let k1 = KeyPair::generate();
        let now = Utc::now();
        let mut reg = EnrolledDeviceSet::new();
        reg.insert(enroll(owner, d1, DeviceType::Desktop, DeviceStatus::Active, &k1, now));
        // Present the real device but LIE that it's Hardware.
        let att = make_att(&owner_kp, owner, &[d1],
            &[(d1, DeviceType::Hardware, &k1)], "n", now);
        assert_eq!(
            att.verify_enrolled(&owner_kp.verifying_key().to_hex(), &reg, Duration::minutes(5), SKEW, now).unwrap(),
            AssuranceLevel::SingleDevice, "enrolled class (Desktop) wins over presented (Hardware)");
    }

    /// A revoked device contributes nothing even though its key still signs.
    #[test]
    fn enrolled_verifier_excludes_revoked() {
        let owner_kp = KeyPair::generate();
        let owner = Uuid::new_v4();
        let (d1, d2) = (Uuid::new_v4(), Uuid::new_v4());
        let (k1, k2) = (KeyPair::generate(), KeyPair::generate());
        let now = Utc::now();
        let mut reg = EnrolledDeviceSet::new();
        reg.insert(enroll(owner, d1, DeviceType::Desktop, DeviceStatus::Active, &k1, now));
        reg.insert(enroll(owner, d2, DeviceType::Mobile, DeviceStatus::Revoked, &k2, now)); // revoked
        let att = make_att(&owner_kp, owner, &[d1, d2],
            &[(d1, DeviceType::Desktop, &k1), (d2, DeviceType::Mobile, &k2)], "n", now);
        assert_eq!(
            att.verify_enrolled(&owner_kp.verifying_key().to_hex(), &reg, Duration::minutes(5), SKEW, now).unwrap(),
            AssuranceLevel::SingleDevice, "a revoked device must not count");
    }

    /// A device signing with a key OTHER than its enrolled key is not counted.
    #[test]
    fn enrolled_verifier_rejects_foreign_device_key() {
        let owner_kp = KeyPair::generate();
        let owner = Uuid::new_v4();
        let d1 = Uuid::new_v4();
        let enrolled_key = KeyPair::generate();
        let foreign = KeyPair::generate();
        let now = Utc::now();
        let mut reg = EnrolledDeviceSet::new();
        reg.insert(enroll(owner, d1, DeviceType::Desktop, DeviceStatus::Active, &enrolled_key, now));
        // The attestation co-signs d1 with a FOREIGN key (not the enrolled one).
        let att = make_att(&owner_kp, owner, &[d1], &[(d1, DeviceType::Desktop, &foreign)], "n", now);
        assert_eq!(
            att.verify_enrolled(&owner_kp.verifying_key().to_hex(), &reg, Duration::minutes(5), SKEW, now).unwrap(),
            AssuranceLevel::SingleDevice, "foreign key fails against the enrolled key");
    }

    /// GPT #3: duplicate signature entries never inflate the count.
    #[test]
    fn enrolled_verifier_collapses_duplicates() {
        let owner_kp = KeyPair::generate();
        let owner = Uuid::new_v4();
        let d1 = Uuid::new_v4();
        let k1 = KeyPair::generate();
        let now = Utc::now();
        let mut reg = EnrolledDeviceSet::new();
        reg.insert(enroll(owner, d1, DeviceType::Desktop, DeviceStatus::Active, &k1, now));
        let att = make_att(&owner_kp, owner, &[d1],
            &[(d1, DeviceType::Desktop, &k1), (d1, DeviceType::Desktop, &k1)], "n", now);
        assert_eq!(
            att.verify_enrolled(&owner_kp.verifying_key().to_hex(), &reg, Duration::minutes(5), SKEW, now).unwrap(),
            AssuranceLevel::SingleDevice, "one device, duplicated, is still one");
    }

    /// GPT #4 + #5: wrong owner key rejected; future-dated rejected.
    #[test]
    fn enrolled_verifier_rejects_wrong_owner_and_future_dated() {
        let owner_kp = KeyPair::generate();
        let owner = Uuid::new_v4();
        let now = Utc::now();
        let reg = EnrolledDeviceSet::new();

        let att = make_att(&owner_kp, owner, &[], &[], "n", now);
        let foreign = KeyPair::generate().verifying_key().to_hex();
        assert_eq!(
            att.verify_enrolled(&foreign, &reg, Duration::minutes(5), SKEW, now),
            Err(VerifyError::ForeignOwnerKey));

        // issued_at an hour in the future → FutureDated (negative age slips > max_age).
        let att = make_att(&owner_kp, owner, &[], &[], "n", now + Duration::hours(1));
        assert_eq!(
            att.verify_enrolled(&owner_kp.verifying_key().to_hex(), &reg, Duration::minutes(5), SKEW, now),
            Err(VerifyError::FutureDated));
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
        gate.present(pair, &att, &pinned, &EnrolledDeviceSet::new(), now).unwrap();

        assert!(gate.assurance(pair, now + Duration::minutes(59)).is_some());
        // Past valid_until → gone, never silently extended.
        assert!(gate.assurance(pair, now + Duration::minutes(61)).is_none());
        // And it stays gone until a new challenge/present cycle.
        assert!(gate.assurance(pair, now + Duration::minutes(59)).is_none());
    }

    #[test]
    fn assurance_receipt_is_portably_verifiable_without_hestia() {
        // A2: the hub signs a receipt; a relying party verifies it with the hub's
        // PUBLIC key and a clock — nothing else. No hub, no hestia, no presenter.
        let hub_kp = KeyPair::generate();
        let now = Utc::now();
        let roster = vec![Uuid::new_v4(), Uuid::new_v4()];
        let signer_lct = Uuid::new_v4();
        let mut r = AssuranceReceipt {
            owner_lct_id: Uuid::new_v4(),
            tier: AssuranceLevel::HardwareBacked,
            pair_id: Uuid::new_v4(),
            challenge_nonce: "hub-nonce".into(),
            issued_at: now,
            bound_at: now,
            valid_until: now + Duration::hours(1),
            hub_lct_id: Uuid::new_v4(),
            hub_signer_lct_id: signer_lct,
            hub_signer_key_id: AssuranceReceipt::key_id(&hub_kp.verifying_key()),
            roster_hash: AssuranceReceipt::roster_hash(&roster),
            signature: String::new(),
        };
        r.signature = hub_kp.sign(&r.signing_bytes()).to_hex();

        // Relying party: verify with the hub key + now. PASS.
        assert!(r.verify(&hub_kp.verifying_key(), now).is_ok());
        // Tamper the tier → the signature no longer covers it.
        let mut forged = r.clone();
        forged.tier = AssuranceLevel::SingleDevice;
        assert_eq!(forged.verify(&hub_kp.verifying_key(), now), Err(VerifyError::ReceiptSignatureInvalid));
        // Tamper the roster_hash (replay to another constellation) → fails.
        let mut replayed = r.clone();
        replayed.roster_hash = AssuranceReceipt::roster_hash(&[Uuid::new_v4()]);
        assert!(replayed.verify(&hub_kp.verifying_key(), now).is_err());
        // Expired → Stale.
        assert_eq!(r.verify(&hub_kp.verifying_key(), now + Duration::hours(2)), Err(VerifyError::Stale));
        // A different hub key → named as such, not an opaque sig failure.
        assert_eq!(
            r.verify(&KeyPair::generate().verifying_key(), now),
            Err(VerifyError::SignerKeyMismatch)
        );
        // Re-pointing a valid receipt at another signer identity breaks the sig:
        // hub_signer_lct_id is inside the signed bytes.
        let mut repointed = r.clone();
        repointed.hub_signer_lct_id = Uuid::new_v4();
        assert_eq!(
            repointed.verify(&hub_kp.verifying_key(), now),
            Err(VerifyError::ReceiptSignatureInvalid)
        );
    }

    #[test]
    fn canonical_timestamp_is_fixed_width_z_suffixed_and_lossless() {
        // Fixed width is half the point: `AutoSi` (chrono's serde default, and what
        // v2 shipped) varies the fraction with the VALUE, so a whole-second instant
        // and a live-clock instant occupied the same field in different shapes.
        for iso in [
            "2099-01-01T00:00:00Z",             // whole second — AutoSi emits no fraction
            "2026-07-30T04:03:13.000000001Z",   // one nanosecond
            "2026-07-30T04:03:13.302000000Z",   // exactly milliseconds — AutoSi emits 3
            "2026-07-30T04:03:13.302191724Z",   // live-clock shaped
            "1970-01-01T00:00:00Z",
        ] {
            let t = DateTime::parse_from_rfc3339(iso).unwrap().with_timezone(&Utc);
            let c = canonical_timestamp(&t);
            assert!(c.ends_with('Z'), "{c}: must be Z-suffixed, never an offset");
            assert!(!c.contains('+'), "{c}: must carry no numeric offset");
            let frac = c.split('.').nth(1).expect("must always carry a fraction");
            assert_eq!(
                frac.trim_end_matches('Z').len(),
                9,
                "{c}: fractional digits must be fixed-width 9"
            );
            // Lossless at DateTime<Utc>'s own resolution — so canonicalizing costs
            // no precision and the stored instant equals the transmitted one. (This
            // is why Nanos, not Millis: Millis would be fixed-width too, but would
            // silently round the value the signature covers.)
            assert_eq!(
                DateTime::parse_from_rfc3339(&c).unwrap().with_timezone(&Utc),
                t,
                "{c}: canonical form must round-trip exactly"
            );
        }
    }

    #[test]
    fn signed_bytes_are_reconstructable_from_the_wire_alone() {
        // THE v3 property, and the whole reason for the tag bump: a relying party
        // holding nothing but the receipt's JSON must be able to rebuild the exact
        // bytes the hub signed, using the transmitted strings VERBATIM. Under v2
        // this test fails — the wire said `…Z` while the signature covered
        // `…+00:00`, so `tools/verify_assurance_receipt.py` needed a shim that
        // guessed a chrono spelling.
        let hub_kp = KeyPair::generate();
        let ts = |s: &str| DateTime::parse_from_rfc3339(s).unwrap().with_timezone(&Utc);
        // Deliberately mixed widths under AutoSi: 9 digits, 1 nanosecond, and a
        // whole second. If width leaked into the signature, this spread catches it.
        let issued = ts("2026-07-30T04:03:13.302191724Z");
        let bound = ts("2026-07-30T04:03:13.000000001Z");
        let until = ts("2099-01-01T00:00:00Z");
        let roster = vec![Uuid::new_v4(), Uuid::new_v4()];
        let mut r = AssuranceReceipt {
            owner_lct_id: Uuid::new_v4(),
            tier: AssuranceLevel::HardwareBacked,
            pair_id: Uuid::new_v4(),
            challenge_nonce: "hub-nonce-wire".into(),
            issued_at: issued,
            bound_at: bound,
            valid_until: until,
            hub_lct_id: Uuid::new_v4(),
            hub_signer_lct_id: Uuid::new_v4(),
            hub_signer_key_id: AssuranceReceipt::key_id(&hub_kp.verifying_key()),
            roster_hash: AssuranceReceipt::roster_hash(&roster),
            signature: String::new(),
        };
        r.signature = hub_kp.sign(&r.signing_bytes()).to_hex();

        let json = serde_json::to_string(&r).unwrap();
        let wire: serde_json::Value = serde_json::from_str(&json).unwrap();
        let s = |k: &str| wire[k].as_str().unwrap_or_default().to_string();
        let uuid = |k: &str| Uuid::parse_str(&s(k)).unwrap();

        // A standalone verifier's arithmetic: no chrono, no re-formatting, nothing
        // but the strings as received, in the documented field order.
        let mut rebuilt = Vec::new();
        rebuilt.extend_from_slice(b"web4:assurance-receipt:v3:");
        rebuilt.extend_from_slice(uuid("owner_lct_id").as_bytes());
        rebuilt.extend_from_slice(s("tier").as_bytes());
        rebuilt.extend_from_slice(uuid("pair_id").as_bytes());
        rebuilt.extend_from_slice(s("challenge_nonce").as_bytes());
        rebuilt.extend_from_slice(s("issued_at").as_bytes());
        rebuilt.extend_from_slice(s("bound_at").as_bytes());
        rebuilt.extend_from_slice(s("valid_until").as_bytes());
        rebuilt.extend_from_slice(uuid("hub_lct_id").as_bytes());
        rebuilt.extend_from_slice(uuid("hub_signer_lct_id").as_bytes());
        rebuilt.extend_from_slice(s("hub_signer_key_id").as_bytes());
        rebuilt.extend_from_slice(s("roster_hash").as_bytes());
        assert_eq!(
            rebuilt,
            r.signing_bytes(),
            "the transmitted strings no longer rebuild the signed bytes — signing_bytes \
             and the serde form have drifted apart, which is the v2 defect returning"
        );

        // And the rebuilt bytes must actually satisfy the signature. Internal
        // equality alone could be two identical mistakes; this is the property a
        // relying party depends on.
        let sig = sig_from_hex(&r.signature).unwrap();
        assert!(
            hub_kp.verifying_key().verify(&rebuilt, &sig).is_ok(),
            "bytes rebuilt from the wire do not verify against the receipt's signature"
        );

        // The v2 spelling must appear nowhere on the wire.
        assert!(!json.contains("+00:00"), "wire regressed to an offset suffix: {json}");
        // …and the divergence this bump fixes must still be real upstream. If chrono
        // ever makes `to_rfc3339()` emit `Z`, the premise recorded in the v3 note
        // changed and the note should be re-checked rather than trusted.
        assert_ne!(
            canonical_timestamp(&issued),
            issued.to_rfc3339(),
            "chrono's to_rfc3339() now agrees with the canonical form — re-check the v3 rationale"
        );

        // A receipt that has been through JSON is the same value and still verifies:
        // losslessness is what makes that true.
        let back: AssuranceReceipt = serde_json::from_str(&json).unwrap();
        assert_eq!(back, r, "round-trip changed the receipt");
        assert!(back.verify(&hub_kp.verifying_key(), issued).is_ok());
    }

    #[test]
    fn a_fabricated_receipt_cannot_self_authenticate_its_signer() {
        // THE trap this shape exists to prevent (JWT `jwk`-header confusion). An
        // attacker mints their own keypair, writes the highest tier and any owner
        // they like, and signs it themselves. The receipt is internally perfect:
        // its key id matches its signature, every field is covered.
        let attacker = KeyPair::generate();
        let now = Utc::now();
        let mut forged = AssuranceReceipt {
            owner_lct_id: Uuid::new_v4(),
            tier: AssuranceLevel::HardwareBacked,
            pair_id: Uuid::new_v4(),
            challenge_nonce: "attacker-chosen".into(),
            issued_at: now,
            bound_at: now,
            valid_until: now + Duration::hours(1),
            hub_lct_id: Uuid::new_v4(),
            hub_signer_lct_id: Uuid::new_v4(),
            hub_signer_key_id: AssuranceReceipt::key_id(&attacker.verifying_key()),
            roster_hash: AssuranceReceipt::roster_hash(&[Uuid::new_v4()]),
            signature: String::new(),
        };
        forged.signature = attacker.sign(&forged.signing_bytes()).to_hex();

        // Self-consistent, so it verifies against the attacker's OWN key — that is
        // expected and harmless. The receipt is only evidence about a key.
        assert!(forged.verify(&attacker.verifying_key(), now).is_ok());

        // What must NOT be possible: the relying party deriving the verification
        // key from the receipt. `hub_signer_key_id` is a one-way 8-byte selector,
        // so there is no `pubkey_from_hex(receipt.<field>)` to write — the struct
        // exposes no key material at all. The only key a relying party can bring
        // is one it already trusts, and against the real hub's key the forgery is
        // rejected by attribution before a signature is even checked.
        let real_hub = KeyPair::generate();
        assert_eq!(
            forged.verify(&real_hub.verifying_key(), now),
            Err(VerifyError::SignerKeyMismatch)
        );
    }

    #[test]
    fn roster_hash_is_order_independent_but_set_sensitive() {
        // A relying party holding the device set recomputes the hash without
        // knowing the order the presenter used...
        let a = Uuid::new_v4();
        let b = Uuid::new_v4();
        let c = Uuid::new_v4();
        assert_eq!(
            AssuranceReceipt::roster_hash(&[a, b, c]),
            AssuranceReceipt::roster_hash(&[c, a, b])
        );
        // ...but a different SET is still a different constellation.
        assert_ne!(
            AssuranceReceipt::roster_hash(&[a, b, c]),
            AssuranceReceipt::roster_hash(&[a, b])
        );
    }

    #[test]
    fn tier_wire_tag_matches_the_serde_wire_value() {
        // The signed bytes spell the tier with `wire_tag()`; the JSON spells it
        // with serde. If those two ever disagree, a non-Rust verifier reading the
        // JSON reconstructs bytes the hub never signed.
        for tier in [
            AssuranceLevel::SingleDevice,
            AssuranceLevel::MultiDevice,
            AssuranceLevel::HardwareBacked,
        ] {
            let json = serde_json::to_string(&tier).expect("tier serializes");
            assert_eq!(json, format!("\"{}\"", tier.wire_tag()));
        }
    }
}
