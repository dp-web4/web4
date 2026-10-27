// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! LCT identity convergence Slice E (hub/docs/PRD_LCT_IDENTITY_CONVERGENCE.md): lost-key lineage.
//!
//! When a presence's key is lost (a being rebuilt on a new disk), D4 cannot link the new presence to the old
//! one: there is no old key to sign with. E lets the Sovereign ATTEST the link instead, and the successor
//! countersign it. The result is a *labelled* edge, `attested_predecessor` / `attested_successor`, kept apart
//! from D-b1's verified `predecessors` / `successor` everywhere, so it can never read as `verified`.
//!
//! What it proves: this hub's Sovereign key made the statement, and the successor's key consented to it. It
//! does NOT prove the two presences are one entity. That is the Sovereign's claim, and law weighs it (FR5).
//!
//! The statement (E1) is `web4-lct-attest-predecessor-v1\n<hub>\n<old>\n<new>\n<issued_at>\n<reason>\n`.
//! `reason` is ONE line, so the signed bytes parse one way only, and it is PUBLIC (witnessed, and carried by
//! lineage and evidence). The successor countersigns first and the Sovereign signs last, so `issued_at` may
//! be up to 24 h old when the envelope arrives (E-6, a two-machine ceremony).
//!
//! "Live" (one predicate, used everywhere in E): an attested edge is live until a later
//! `LctPredecessorAttestationWithdrawn` names it; a verified D4 edge is always live. Every "has a
//! successor" / "has a predecessor" check in E, and the D-b1 cycle guard (E3a), call `HubState`'s
//! `lct_has_live_successor` / `lct_has_live_predecessor`, so there is one notion, not three.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use web4_core::crypto::{PublicKey, SignatureBytes};
use web4_core::lct::LctStatus;

use crate::ids::CanonicalLctId;
use crate::routing::{CLOCK_SKEW_SECS, CONSENT_MAX_AGE_SECS};
use crate::state::HubState;

pub const ATTEST_DOMAIN: &str = "web4-lct-attest-predecessor-v1";
pub const WITHDRAW_DOMAIN: &str = "web4-lct-attest-withdraw-v1";
/// E1 (Pub): `reason` is capped, in UTF-8 bytes.
pub const REASON_MAX_BYTES: usize = 280;
/// E-6 (Pub): how old `issued_at` may be when the Sovereign's envelope arrives. The successor countersigns on
/// its own machine first; the Sovereign signs last, on the hub's.
pub const ATTEST_MAX_AGE_SECS: i64 = 24 * 3600;

/// The exact bytes both keys sign. `issued_at` and `reason` are signed verbatim, as sent.
pub fn attestation_bytes(hub: Uuid, old: &CanonicalLctId, new: &CanonicalLctId, issued_at: &str, reason: &str)
    -> Vec<u8> {
    format!("{ATTEST_DOMAIN}\n{hub}\n{old}\n{new}\n{issued_at}\n{reason}\n").into_bytes()
}

/// The exact bytes the Sovereign signs to withdraw the attestation witnessed at `attestation_index`.
pub fn withdrawal_bytes(hub: Uuid, old: &CanonicalLctId, new: &CanonicalLctId, attestation_index: u64,
    issued_at: &str, reason: &str) -> Vec<u8> {
    format!("{WITHDRAW_DOMAIN}\n{hub}\n{old}\n{new}\n{attestation_index}\n{issued_at}\n{reason}\n").into_bytes()
}

fn signature(hex_str: &str) -> Option<SignatureBytes> {
    let raw: [u8; 64] = hex::decode(hex_str).ok()?.try_into().ok()?;
    Some(SignatureBytes::from_bytes(raw))
}

/// E1 (Pub): one line, no control characters, at most `REASON_MAX_BYTES`. A `\n` inside `reason` would let
/// the signed bytes be parsed differently from what either party read.
pub fn check_reason(reason: &str) -> Result<(), String> {
    if reason.len() > REASON_MAX_BYTES {
        return Err(format!("reason is {} bytes; the limit is {REASON_MAX_BYTES} (it is public: keep it short)",
            reason.len()));
    }
    if reason.chars().any(char::is_control) {
        return Err("reason must be one line with no control characters (\\n, \\r, ...): the signed bytes \
            must parse one way only".into());
    }
    Ok(())
}

/// E1 (CBP): the attester is this hub's Sovereign key, and only while it is CURRENT. A Sovereign presence that
/// D4 says has rotated away no longer speaks for the hub. The key comes from the hub's identity, never from
/// the statement, so a Sovereign of another hub (a demo hub on the being's machine) never qualifies.
fn check_attester(state: &HubState, sovereign: &PublicKey) -> Result<(), String> {
    let canonical = CanonicalLctId::derive(sovereign);
    if state.lct_successors.get(&canonical).is_some_and(|v| !v.is_empty()) {
        return Err(format!("the Sovereign key ({canonical}) has been rotated away (D4); only the Sovereign's \
            current verified key may attest"));
    }
    Ok(())
}

fn parse_issued_at(issued_at: &str, now: DateTime<Utc>, max_age: i64) -> Result<DateTime<Utc>, String> {
    let at = DateTime::parse_from_rfc3339(issued_at)
        .map_err(|_| format!("issued_at '{issued_at}' is not RFC 3339"))?;
    if at.offset().local_minus_utc() != 0 {
        return Err("issued_at must be UTC".into());
    }
    let at = at.with_timezone(&Utc);
    let age = (now - at).num_seconds();
    if !(-CLOCK_SKEW_SECS..=max_age).contains(&age) {
        return Err(format!("issued_at is outside the window ({age} s old; allowed {}..={max_age})",
            -CLOCK_SKEW_SECS));
    }
    Ok(at)
}

/// An attestation as submitted (E1/E2).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct AttestationStatement {
    pub old: CanonicalLctId,
    pub new: CanonicalLctId,
    /// RFC 3339, UTC. Signed as sent.
    pub issued_at: String,
    /// One line, public. Signed as sent.
    pub reason: String,
    /// This hub's Sovereign key over `attestation_bytes`.
    pub attester_signature_hex: String,
    /// `new`'s binding key over the same bytes: the successor's consent.
    pub new_signature_hex: String,
}

impl AttestationStatement {
    /// Verify against `state` at `now` (the envelope's time), with `sovereign` read from the hub's identity.
    /// Fail-closed. A pair that is already live is NOT an error here: the caller folds it into the first
    /// entry (E4) before calling this, so the join rule below never refuses a replay of its own pair.
    pub fn verify(&self, state: &HubState, hub: Uuid, sovereign: &PublicKey, now: DateTime<Utc>)
        -> Result<DateTime<Utc>, String> {
        if self.old == self.new {
            return Err("old and new are the same LCT; an attestation links two presences".into());
        }
        check_reason(&self.reason)?;
        state.registry.get(&self.old).ok_or_else(|| format!("{} (old) is not published here", self.old))?;
        let new_doc = state.registry.get(&self.new)
            .ok_or_else(|| format!("{} (new) is not published here", self.new))?;
        // E3: a terminal or dormant successor cannot inherit. `old` may be in any status: a lost-key
        // predecessor is often stale, and its status stays its own evidence.
        if new_doc.document.status != LctStatus::Active {
            return Err(format!("{} (new) is not active (its current document says {:?}); only an active \
                presence can continue another", self.new, new_doc.document.status));
        }
        check_attester(state, sovereign)?;
        // E3: no cycles. `new` must be a tip, by either kind of live edge.
        if state.lct_has_live_successor(&self.new) {
            return Err(format!("{} (new) already has a live successor (verified or attested); it cannot \
                continue another presence", self.new));
        }
        // E3 / E-9 (Legion): no joins. A rebuilt being mints a fresh key with no history; a `new` that already
        // continues something would merge two lineages into one presence.
        if state.lct_has_live_predecessor(&self.new) {
            return Err(format!("{} (new) already has a live predecessor (verified or attested); a second \
                lineage cannot join it", self.new));
        }
        // E3 / E-3: a judgment is refused against a standing key fact. Disputing it is compromise recovery.
        if state.lct_successors.get(&self.old).is_some_and(|v| !v.is_empty()) {
            return Err(format!("{} (old) has a verified successor (D4); an attestation cannot contradict a \
                key-signed rotation", self.old));
        }
        let at = parse_issued_at(&self.issued_at, now, ATTEST_MAX_AGE_SECS)?;
        let bytes = attestation_bytes(hub, &self.old, &self.new, &self.issued_at, &self.reason);
        let attester_sig = signature(&self.attester_signature_hex)
            .ok_or("attester_signature_hex is not a 64-byte hex signature")?;
        let new_sig = signature(&self.new_signature_hex).ok_or("new_signature_hex is not a 64-byte hex signature")?;
        sovereign.verify(&bytes, &attester_sig)
            .map_err(|_| "the attester signature does not verify under this hub's Sovereign key".to_string())?;
        new_doc.document.public_key.verify(&bytes, &new_sig)
            .map_err(|_| format!("the new signature does not verify under {}'s binding key (the successor \
                must countersign)", self.new))?;
        Ok(at)
    }
}

/// A withdrawal as submitted (E5). Sovereign-signed only: withdrawing a claim needs no consent from its subject.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct WithdrawalStatement {
    pub old: CanonicalLctId,
    pub new: CanonicalLctId,
    /// The ledger index of the live `LctPredecessorAttested` being withdrawn.
    pub attestation_index: u64,
    pub issued_at: String,
    pub reason: String,
    pub attester_signature_hex: String,
}

impl WithdrawalStatement {
    /// One signer who submits at once, so H2's window applies.
    pub fn verify(&self, state: &HubState, hub: Uuid, sovereign: &PublicKey, now: DateTime<Utc>)
        -> Result<DateTime<Utc>, String> {
        check_reason(&self.reason)?;
        match state.attestation_index(&self.old, &self.new) {
            Some(i) if i == self.attestation_index => {}
            Some(i) => return Err(format!("the live attestation {} ⇢ {} is entry {i}, not {}", self.old,
                self.new, self.attestation_index)),
            None => return Err(format!("there is no live attestation {} ⇢ {}", self.old, self.new)),
        }
        check_attester(state, sovereign)?;
        let at = parse_issued_at(&self.issued_at, now, CONSENT_MAX_AGE_SECS)?;
        let bytes = withdrawal_bytes(hub, &self.old, &self.new, self.attestation_index, &self.issued_at,
            &self.reason);
        let sig = signature(&self.attester_signature_hex)
            .ok_or("attester_signature_hex is not a 64-byte hex signature")?;
        sovereign.verify(&bytes, &sig)
            .map_err(|_| "the attester signature does not verify under this hub's Sovereign key".to_string())?;
        Ok(at)
    }
}

/// One live attested edge, from the other end's point of view.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct AttestedRef {
    pub canonical: CanonicalLctId,
    /// The ledger index of the `LctPredecessorAttested` that witnessed it.
    pub index: u64,
    /// The channel the attestation arrived through (E2, CBP): witnessed, so a daemon-minted one is anomalous.
    pub attested_by: String,
}

/// An attested edge that a later withdrawal took out of lineage (E5). The ledger keeps both entries.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct WithdrawnRef {
    pub canonical: CanonicalLctId,
    pub index: u64,
    pub withdrawn_at: u64,
}
