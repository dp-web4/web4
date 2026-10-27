// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! LCT identity convergence Slice D-b1 (hub/docs/PRD_LCT_IDENTITY_CONVERGENCE.md, D4): verified rotation.
//!
//! A rotation is ONE statement, `web4-lct-rotate-v1\n<hub>\n<old>\n<new>\n<issued_at>\n` (the H2
//! consent shape), signed by the OLD document's binding key AND countersigned by the NEW one over the
//! same bytes. The old signature proves the predecessor's holder chose this successor; the new one is
//! the successor's consent, without which a holder of A could graft its history (or its slashing) onto
//! any published X. Both documents must already be published, so each key is read from the registry,
//! never from the statement.
//!
//! Forks are evidence, never resolved: one old key naming two distinct successors yields two
//! `LctRotated` entries and a `successor_conflict`, with no single verified successor. A replay, or the
//! same `old→new` pair re-signed later, is folded into the first entry (Legion, #930).
//!
//! What this proves: possession of both binding keys at signing time. It covers PLANNED rotation; a
//! thief holding the old key can produce the same statement, so compromise recovery is out of D.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use web4_core::crypto::SignatureBytes;
use web4_core::lct::LctStatus;

use crate::ids::CanonicalLctId;
use crate::routing::{CLOCK_SKEW_SECS, CONSENT_MAX_AGE_SECS};
use crate::state::HubState;

pub const ROTATE_DOMAIN: &str = "web4-lct-rotate-v1";

/// The exact bytes both binding keys sign. `issued_at` is signed verbatim, as sent.
pub fn rotation_bytes(hub: Uuid, old: &CanonicalLctId, new: &CanonicalLctId, issued_at: &str) -> Vec<u8> {
    format!("{ROTATE_DOMAIN}\n{hub}\n{old}\n{new}\n{issued_at}\n").into_bytes()
}

/// A rotation as submitted: both canonicals, the signed `issued_at`, and the two signatures (hex).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct RotationStatement {
    pub old: CanonicalLctId,
    pub new: CanonicalLctId,
    /// RFC 3339, UTC. Signed as sent.
    pub issued_at: String,
    pub old_signature_hex: String,
    pub new_signature_hex: String,
}

fn signature(hex_str: &str) -> Option<SignatureBytes> {
    let raw: [u8; 64] = hex::decode(hex_str).ok()?.try_into().ok()?;
    Some(SignatureBytes::from_bytes(raw))
}

impl RotationStatement {
    /// Verify against `state` (the registry both keys are read from) at `now`. Returns the parsed
    /// `issued_at`. Fail-closed: every check must hold.
    pub fn verify(&self, state: &HubState, hub: Uuid, now: DateTime<Utc>) -> Result<DateTime<Utc>, String> {
        if self.old == self.new {
            return Err("old and new are the same LCT; a republish is not a rotation".into());
        }
        let old_doc = state.registry.get(&self.old)
            .ok_or_else(|| format!("{} (old) is not published here", self.old))?;
        let new_doc = state.registry.get(&self.new)
            .ok_or_else(|| format!("{} (new) is not published here", self.new))?;
        // CBP #934: a rotation is a planned hand-over between two LIVE identities. An old LCT whose current
        // document says it is no longer active (void, slashed, dormant) has withdrawn its key's authority,
        // so a leaked binding key cannot hand its history to an attacker's LCT after the revocation. A
        // non-active successor is refused likewise. The status is the document's own (self-asserted), and
        // honouring a self-declared non-active status here is the against-interest direction (D-a).
        for (which, id, doc) in [("old", &self.old, old_doc), ("new", &self.new, new_doc)] {
            if doc.document.status != LctStatus::Active {
                return Err(format!("{id} ({which}) is not active (its current document says {:?}); \
                    a rotation needs both LCTs active", doc.document.status));
            }
        }
        // Legion #934: no cycles. A `new` that already has a witnessed successor is itself rotated away, so
        // naming it would close a loop (A→B, B→A) in which neither key reads as current. Because every
        // canonical in a chain except its tip has a successor, refusing this one hop rules out any cycle.
        // Slice E3a (Legion #938): that argument holds per edge KIND, so the guard reads live successors of
        // both kinds. Otherwise an attested A ⇢ B followed by a rotation B → A closes a ring neither guard sees.
        if state.lct_has_live_successor(&self.new) {
            return Err(format!("{} (new) has already been rotated away (it has a live successor, verified or \
                attested); a rotation cannot name a superseded LCT as its successor", self.new));
        }
        let at = DateTime::parse_from_rfc3339(&self.issued_at)
            .map_err(|_| format!("issued_at '{}' is not RFC 3339", self.issued_at))?;
        if at.offset().local_minus_utc() != 0 {
            return Err("issued_at must be UTC".into());
        }
        let at = at.with_timezone(&Utc);
        let age = (now - at).num_seconds();
        if !(-CLOCK_SKEW_SECS..=CONSENT_MAX_AGE_SECS).contains(&age) {
            return Err(format!("issued_at is outside the window ({age} s old; allowed {}..={})",
                -CLOCK_SKEW_SECS, CONSENT_MAX_AGE_SECS));
        }
        let bytes = rotation_bytes(hub, &self.old, &self.new, &self.issued_at);
        let old_sig = signature(&self.old_signature_hex).ok_or("old_signature_hex is not a 64-byte hex signature")?;
        let new_sig = signature(&self.new_signature_hex).ok_or("new_signature_hex is not a 64-byte hex signature")?;
        old_doc.document.public_key.verify(&bytes, &old_sig)
            .map_err(|_| format!("the old signature does not verify under {}'s binding key", self.old))?;
        new_doc.document.public_key.verify(&bytes, &new_sig)
            .map_err(|_| format!("the new signature does not verify under {}'s binding key (the successor \
                must countersign)", self.new))?;
        Ok(at)
    }
}

/// One witnessed rotation edge, from the other end's point of view.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct RotationRef {
    pub canonical: CanonicalLctId,
    /// The ledger index of the `LctRotated` that witnessed it.
    pub index: u64,
}

/// What the hub can say about a canonical's rotation lineage. Evidence, never a verdict (FR5).
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize)]
pub struct LctLineage {
    /// The single verified successor: set only when exactly one distinct successor was witnessed.
    pub successor: Option<RotationRef>,
    /// Two or more distinct witnessed successors (a fork): every one, in ledger order, and no
    /// `successor`. Law decides; the hub picks no winner.
    pub successor_conflict: Vec<RotationRef>,
    /// Verified predecessors (each countersigned by this canonical), in ledger order.
    pub predecessors: Vec<RotationRef>,
    /// `rotated_from` MRH edges in this canonical's own document that no `LctRotated` backs: a
    /// self-claim, signed only by this key.
    pub claimed_predecessors: Vec<String>,
    /// Slice E: the single LIVE attested successor (a Sovereign claim the successor countersigned), set only
    /// when exactly one distinct one is live. A LABEL, never a verified rotation.
    pub attested_successor: Option<crate::lct_attest::AttestedRef>,
    /// Two or more live attested successors (E4): every one, and no `attested_successor`.
    pub attested_successor_conflict: Vec<crate::lct_attest::AttestedRef>,
    /// Live attested predecessors, in ledger order.
    pub attested_predecessors: Vec<crate::lct_attest::AttestedRef>,
    /// E5: attested edges at either end that a withdrawal took out of lineage, citing it.
    pub withdrawn_attestations: Vec<crate::lct_attest::WithdrawnRef>,
    /// E-8 (Legion): this canonical has live successors of BOTH kinds (the old key signed a rotation after its
    /// loss was attested, or the reverse). `successor` / `successor_conflict` still report the verified fact
    /// and `attested_*` the claim, but neither is THE successor: law sees both (FR5).
    pub successor_kind_conflict: bool,
}

pub fn lineage(state: &HubState, canonical: &CanonicalLctId) -> LctLineage {
    let refs = |m: &std::collections::BTreeMap<CanonicalLctId, Vec<(CanonicalLctId, u64)>>| -> Vec<RotationRef> {
        m.get(canonical).map(|v| v.iter().map(|(c, i)| RotationRef { canonical: c.clone(), index: *i }).collect())
            .unwrap_or_default()
    };
    let successors = refs(&state.lct_successors);
    let predecessors = refs(&state.lct_predecessors);
    let (successor, successor_conflict) = match successors.as_slice() {
        [one] => (Some(one.clone()), Vec::new()),
        _ => (None, if successors.len() > 1 { successors } else { Vec::new() }),
    };
    let claimed_predecessors = state.registry.get(canonical).map(|e| e.document.mrh.bound.iter()
        .filter(|edge| edge.edge_type == "rotated_from")
        .filter(|edge| !predecessors.iter().any(|p| p.canonical.as_str() == edge.lct_id))
        .map(|edge| edge.lct_id.clone()).collect()).unwrap_or_default();
    let attested = |m: &std::collections::BTreeMap<CanonicalLctId, Vec<(CanonicalLctId, u64, String)>>| {
        m.get(canonical).map(|v| v.iter().map(|(c, i, by)| crate::lct_attest::AttestedRef {
            canonical: c.clone(), index: *i, attested_by: by.clone() }).collect::<Vec<_>>()).unwrap_or_default()
    };
    let attested_successors = attested(&state.lct_attested_successors);
    let attested_predecessors = attested(&state.lct_attested_predecessors);
    let successor_kind_conflict = !attested_successors.is_empty()
        && state.lct_successors.get(canonical).is_some_and(|v| !v.is_empty());
    let (attested_successor, attested_successor_conflict) = match attested_successors.as_slice() {
        [one] => (Some(one.clone()), Vec::new()),
        _ => (None, if attested_successors.len() > 1 { attested_successors } else { Vec::new() }),
    };
    let withdrawn_attestations = state.lct_attestations_withdrawn.iter().filter_map(|(old, new, i, w)| {
        let other = if old == canonical { new } else if new == canonical { old } else { return None };
        Some(crate::lct_attest::WithdrawnRef { canonical: other.clone(), index: *i, withdrawn_at: *w })
    }).collect();
    LctLineage { successor, successor_conflict, predecessors, claimed_predecessors, attested_successor,
        attested_successor_conflict, attested_predecessors, withdrawn_attestations, successor_kind_conflict }
}
