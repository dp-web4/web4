// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// This software is covered by US Patents 11,477,027 and 12,278,913,
// and pending application 19/178,619. See PATENTS.md for details.

//! Witness attestations and birth certificates (canon §2.3, §4, §11.2).
//!
//! The upgrade path out of a `self_issued` §3.2 bootstrap: a society witnesses
//! an entity's existence with a **quorum of ≥3 signed attestations** and confers
//! a **birth certificate**, which carries citizenship (high inherited trust,
//! permanent citizen pairing). This module is the SCHEMA + the fail-closed
//! validator; the *conferral flow* (who gathers the quorum, when the society
//! signs) is the hub-as-society's lane.
//!
//! **Verification is fail-closed and comes in two strengths, exactly as §11.2
//! frames it:** a structural check ([`BirthCertificate::quorum_structurally_ok`])
//! is the minimum (present + ≥3 distinct witnesses + a present attestation per
//! witness); a COSE-verified check ([`Lct::verify_birth_certificate`]) is
//! RECOMMENDED and additionally verifies every witness signature against that
//! witness's bound public key. Absence is always the closed pole: no birth
//! certificate ⇒ a Regular LCT (self-issued, low trust), never a silent pass.

use crate::crypto::{KeyPair, PublicKey, SignatureBytes};
use chrono::{DateTime, SecondsFormat, Utc};
use serde::{Deserialize, Serialize};

/// A witness's role when attesting (canon §5.2.3). Birth certificates require
/// `Existence` attestations; the other roles carry over the same signature
/// machinery for action/state/quality witnessing.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AttestationType {
    Time,
    Audit,
    Oracle,
    Existence,
    Action,
    State,
    Quality,
}

/// One signed witness attestation over a subject LCT (canon §2.3 `attestations`).
/// The signature covers [`Attestation::message`] — the subject's canonical id +
/// the attestation type + the timestamp, domain-separated — so any verifier
/// reconstructs exactly what was signed from the document alone.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Attestation {
    /// The witnessing entity's canonical LCT id (`lct:web4:…`).
    pub witness: String,
    /// What is being attested (birth uses `Existence`).
    #[serde(rename = "type")]
    pub attestation_type: AttestationType,
    /// When the witness observed the subject.
    pub ts: DateTime<Utc>,
    /// COSE-style signature by the witness's binding key over [`message`].
    pub sig: SignatureBytes,
}

impl Attestation {
    /// The canonical message a witness signs, reconstructible from the document:
    /// `"web4:lct:attestation:v1\n" + subject_lct_id + "\n" + type + "\n" + ts`.
    /// The timestamp is rendered `AutoSi` + `Z` (byte-identical to the serde wire
    /// form), matching the binding-proof discipline — a non-chrono verifier gets
    /// the exact bytes. Changing this rendering after any attestation is signed
    /// requires a `v1`→`v2` bump.
    pub fn message(subject_lct_id: &str, attestation_type: AttestationType, ts: DateTime<Utc>) -> Vec<u8> {
        let ty = serde_json::to_string(&attestation_type)
            .unwrap_or_default()
            .trim_matches('"')
            .to_string();
        format!(
            "web4:lct:attestation:v1\n{}\n{}\n{}",
            subject_lct_id,
            ty,
            ts.to_rfc3339_opts(SecondsFormat::AutoSi, true)
        )
        .into_bytes()
    }

    /// Sign an existence-style attestation of `subject_lct_id` with the witness's
    /// keypair. `witness` is recorded as the witness's own canonical id.
    pub fn sign(
        subject_lct_id: &str,
        witness: impl Into<String>,
        attestation_type: AttestationType,
        ts: DateTime<Utc>,
        witness_keypair: &KeyPair,
    ) -> Self {
        let sig = witness_keypair.sign(&Self::message(subject_lct_id, attestation_type, ts));
        Attestation { witness: witness.into(), attestation_type, ts, sig }
    }

    /// Verify this attestation's signature over `subject_lct_id` against the
    /// witness's bound public key. **Fail-closed**: `false` on any signature
    /// failure. (Whether `witness_pubkey` truly belongs to `self.witness` is the
    /// caller's resolver contract — see [`Lct::verify_birth_certificate`].)
    pub fn verify(&self, subject_lct_id: &str, witness_pubkey: &PublicKey) -> bool {
        witness_pubkey
            .verify(&Self::message(subject_lct_id, self.attestation_type, self.ts), &self.sig)
            .is_ok()
    }
}

/// The birth-certificate section of an LCT (canon §2.3 / §4.2). Its presence is
/// what distinguishes a citizen (society-conferred, high trust) from a Regular
/// self-issued LCT.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct BirthCertificate {
    /// LCT id of the issuing society.
    pub issuing_society: String,
    /// LCT id of the citizen role this entity inhabits.
    pub citizen_role: String,
    /// The witnesses whose quorum attests this birth (≥3, canon-required).
    /// Canonical LCT ids; each MUST have a matching entry in the LCT's
    /// `attestations` (checked by the validator).
    pub birth_witnesses: Vec<String>,
    pub birth_timestamp: DateTime<Utc>,
    /// Society-type classification (RECOMMENDED). `None` = unstated.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub birth_context: Option<BirthContext>,
    /// Blockchain anchor for temporal proof (RECOMMENDED; `None` when no anchor).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub genesis_block_hash: Option<String>,
}

/// Society-type classification (canon §4.2 `birth_context`).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum BirthContext {
    Nation,
    Platform,
    Network,
    Organization,
    Ecosystem,
}

/// The canon-required minimum witness quorum for a birth certificate (§4.2).
pub const BIRTH_WITNESS_QUORUM: usize = 3;

impl BirthCertificate {
    /// Structural quorum check (§11.2, present-only minimum — no signatures):
    /// ≥3 **distinct** birth witnesses. Distinctness matters — three entries that
    /// are one witness are not a quorum. Does NOT verify attestations or pairing
    /// (that is the whole-LCT validator's job, since those live on the LCT).
    pub fn quorum_structurally_ok(&self) -> bool {
        let mut seen = std::collections::BTreeSet::new();
        let distinct = self.birth_witnesses.iter().filter(|w| seen.insert(*w)).count();
        distinct >= BIRTH_WITNESS_QUORUM
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::lct::{EntityType, Lct};

    #[test]
    fn attestation_signs_and_verifies_fail_closed() {
        let (subject, _sk) = Lct::new(EntityType::AiSoftware, None);
        let witness_kp = KeyPair::generate();
        let att = Attestation::sign(
            &subject.lct_id(),
            "lct:web4:witness:1",
            AttestationType::Existence,
            subject.created_at,
            &witness_kp,
        );
        assert!(att.verify(&subject.lct_id(), &witness_kp.verifying_key()));
        // wrong witness key → rejected
        assert!(!att.verify(&subject.lct_id(), &KeyPair::generate().verifying_key()));
        // wrong subject → rejected (the id is in the signed message)
        assert!(!att.verify("lct:web4:mb32:bother", &witness_kp.verifying_key()));
    }

    #[test]
    fn quorum_needs_three_distinct_witnesses() {
        let base = BirthCertificate {
            issuing_society: "lct:web4:society:hub".into(),
            citizen_role: "lct:web4:role:citizen".into(),
            birth_witnesses: vec!["w1".into(), "w2".into(), "w3".into()],
            birth_timestamp: chrono::DateTime::UNIX_EPOCH.into(),
            birth_context: Some(BirthContext::Ecosystem),
            genesis_block_hash: None,
        };
        assert!(base.quorum_structurally_ok());
        // three ENTRIES but one witness = not a quorum
        let padded = BirthCertificate {
            birth_witnesses: vec!["w1".into(), "w1".into(), "w1".into()],
            ..base.clone()
        };
        assert!(!padded.quorum_structurally_ok());
        // two witnesses = below quorum
        let two = BirthCertificate { birth_witnesses: vec!["w1".into(), "w2".into()], ..base };
        assert!(!two.quorum_structurally_ok());
    }
}
