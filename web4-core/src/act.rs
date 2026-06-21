// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later

//! # Acts: the unifying primitive for memory, forum posts, and handoffs
//!
//! CBP's insight (forum 2026-06-20, "Fleet as a Web4 society"): a memory write,
//! a forum post, and a session handoff are **the same primitive** — an entity
//! externalizing a *witnessed act* into a ledger, addressed across the MRH:
//!
//! - a **memory write** is an act to your *future self* — the **temporal** MRH;
//! - a **handoff** is an act to a *peer* — the **lateral** MRH;
//! - a **forum post** is an act to the *society* — the **broad** MRH.
//!
//! ## Thin governance record, fat substance
//!
//! Web4 *governs* the work; it does not *become* the work. So an [`Act`] is a
//! **thin** record — who/whom, MRH direction, consequence class, witness marks —
//! that **points at** the fat substance (the actual forum prose, git commit, or
//! memory file) via a [`SubstanceRef`]. The substance stays where it already
//! lives (forum, git, disk); the ledger just holds the accountable pointer.
//!
//! This keeps Phase 1 purely additive: mint an Act *alongside* the existing
//! free-text artifact, change no behavior, and gain a witnessed, trust-bearing
//! governance trail.
//!
//! Witnessing here is the **flat** [`WitnessAttestation`] (a single entity
//! attesting it observed the act). The recursive witness-tree is intentionally
//! *not* modeled in this open crate.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::r6::WitnessAttestation;
use crate::v3::TrustValueScore;
use crate::{TrustDimension, ValueDimension};

/// What kind of substance an act points at (advisory; the `uri` is canonical).
#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum SubstanceMedium {
    /// A forum thread/post.
    Forum,
    /// A git commit / blob / PR.
    Git,
    /// A persisted memory file.
    Memory,
    /// A document / spec.
    Doc,
    /// A direct message.
    Message,
    Other,
}

/// A pointer to the *fat substance* an [`Act`] governs. The act is the thin
/// record; this binds it to a specific version of the real content.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct SubstanceRef {
    /// Locator of the substance (git commit hash, forum path, URL, file path).
    pub uri: String,
    /// Content hash binding the act to a specific *version* of the substance,
    /// so the governance record can't silently drift from what it attests.
    pub content_hash: String,
    /// What medium the substance lives in.
    pub medium: SubstanceMedium,
}

impl SubstanceRef {
    pub fn new(uri: impl Into<String>, content_hash: impl Into<String>, medium: SubstanceMedium) -> Self {
        Self { uri: uri.into(), content_hash: content_hash.into(), medium }
    }
}

/// The MRH direction an act is addressed across — *who the future reader is*.
#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum MrhDirection {
    /// To your future self — a memory write (temporal MRH).
    Temporal,
    /// To a peer — a handoff (lateral MRH).
    Lateral,
    /// To the society at large — a forum post (broad MRH).
    Broad,
}

/// How reversible an act's effect is — gates ATP staking and witnessing.
#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq, Default)]
#[serde(rename_all = "snake_case")]
pub enum ConsequenceClass {
    /// Freely undoable (a memory note, a draft).
    #[default]
    Reversible,
    /// Undoable at a cost (a forum post others may have read).
    Costly,
    /// Cannot be undone (a merge to main, a published release).
    Irreversible,
}

impl ConsequenceClass {
    fn scale(self) -> f64 {
        match self {
            ConsequenceClass::Reversible => 0.5,
            ConsequenceClass::Costly => 1.0,
            ConsequenceClass::Irreversible => 2.0,
        }
    }
}

/// A thin, witnessed governance record of an entity externalizing work — the
/// unifying primitive behind memory writes, handoffs, and forum posts.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct Act {
    pub act_id: Uuid,
    /// The acting entity (the LCT that externalized the act).
    pub actor_lct: Uuid,
    /// The addressee, when the act is directed at a specific peer (a handoff).
    /// `None` for temporal-self (memory) and broad (forum) acts.
    #[serde(default)]
    pub audience: Option<Uuid>,
    /// Which way across the MRH this act reaches.
    pub direction: MrhDirection,
    /// How reversible the act's effect is.
    pub consequence: ConsequenceClass,
    /// Pointer to the fat substance this act governs.
    pub substance: SubstanceRef,
    /// Flat witness marks — entities attesting they observed the act.
    #[serde(default)]
    pub witnesses: Vec<WitnessAttestation>,
    pub at: DateTime<Utc>,
}

impl Act {
    /// A **memory write** — an act to your future self (temporal MRH).
    pub fn memory(actor_lct: Uuid, substance: SubstanceRef, at: DateTime<Utc>) -> Self {
        Self::new(actor_lct, None, MrhDirection::Temporal, substance, at)
    }

    /// A **handoff** — an act to a peer (lateral MRH).
    pub fn handoff(actor_lct: Uuid, peer_lct: Uuid, substance: SubstanceRef, at: DateTime<Utc>) -> Self {
        Self::new(actor_lct, Some(peer_lct), MrhDirection::Lateral, substance, at)
    }

    /// A **forum post** — an act to the society (broad MRH).
    pub fn forum(actor_lct: Uuid, substance: SubstanceRef, at: DateTime<Utc>) -> Self {
        Self::new(actor_lct, None, MrhDirection::Broad, substance, at)
    }

    fn new(
        actor_lct: Uuid,
        audience: Option<Uuid>,
        direction: MrhDirection,
        substance: SubstanceRef,
        at: DateTime<Utc>,
    ) -> Self {
        Self {
            act_id: Uuid::new_v4(),
            actor_lct,
            audience,
            direction,
            consequence: ConsequenceClass::default(),
            substance,
            witnesses: Vec::new(),
            at,
        }
    }

    pub fn with_consequence(mut self, c: ConsequenceClass) -> Self {
        self.consequence = c;
        self
    }

    pub fn witnessed_by(mut self, attestation: WitnessAttestation) -> Self {
        self.witnesses.push(attestation);
        self
    }

    /// Whether this act must carry an ATP stake before it's admissible. The
    /// gate is on irreversibility: you stake energy on acts you can't take back.
    pub fn requires_atp_stake(&self) -> bool {
        matches!(self.consequence, ConsequenceClass::Costly | ConsequenceClass::Irreversible)
    }

    /// Whether this act must be witnessed to be admissible (irreversibles must).
    pub fn requires_witness(&self) -> bool {
        matches!(self.consequence, ConsequenceClass::Irreversible)
    }

    /// Fold this act's realized [`ActOutcome`] into the actor's
    /// [`EntityTrust`] — "EntityTrust fed by act-outcomes". A fulfilled act
    /// builds Validity/Veracity; a failed one debits them; the consequence
    /// class scales the magnitude (more is staked on irreversibles, so the
    /// trust swing is larger). Returns the realized (validity, veracity) deltas.
    pub fn record_outcome(&self, trust: &mut TrustValueScore, outcome: ActOutcome) -> (f64, f64) {
        let s = self.consequence.scale();
        let (validity, veracity) = match outcome {
            ActOutcome::Fulfilled => (0.03 * s, 0.02 * s),
            ActOutcome::Failed => (-0.05 * s, -0.03 * s),
            ActOutcome::Disputed => (0.0, -0.04 * s),
        };
        // A fulfilled act is also a small Temperament signal (consistency).
        if matches!(outcome, ActOutcome::Fulfilled) {
            trust.trust.apply_delta(TrustDimension::Temperament, 0.01 * s);
        }
        let dv = trust.value.apply_delta(ValueDimension::Validity, validity);
        let dver = trust.value.apply_delta(ValueDimension::Veracity, veracity);
        (dv, dver)
    }
}

/// The realized outcome of an act, once witnessed/evaluated. Feeds EntityTrust.
#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ActOutcome {
    /// The act achieved its stated effect (the substance landed as claimed).
    Fulfilled,
    /// The act's effect failed or was reverted.
    Failed,
    /// A witness disputes the act's claim.
    Disputed,
}

#[cfg(test)]
mod tests {
    use super::*;

    fn now() -> DateTime<Utc> {
        DateTime::parse_from_rfc3339("2026-06-20T12:00:00Z").unwrap().with_timezone(&Utc)
    }

    fn sref() -> SubstanceRef {
        SubstanceRef::new("git:abc123", "deadbeef", SubstanceMedium::Git)
    }

    #[test]
    fn three_framings_share_one_primitive() {
        let me = Uuid::new_v4();
        let peer = Uuid::new_v4();
        assert_eq!(Act::memory(me, sref(), now()).direction, MrhDirection::Temporal);
        assert_eq!(Act::handoff(me, peer, sref(), now()).direction, MrhDirection::Lateral);
        assert_eq!(Act::forum(me, sref(), now()).direction, MrhDirection::Broad);
        // The handoff is the only one addressed to a specific peer.
        assert_eq!(Act::handoff(me, peer, sref(), now()).audience, Some(peer));
        assert_eq!(Act::memory(me, sref(), now()).audience, None);
    }

    #[test]
    fn irreversible_acts_gate_on_atp_and_witness() {
        let a = Act::forum(Uuid::new_v4(), sref(), now())
            .with_consequence(ConsequenceClass::Irreversible);
        assert!(a.requires_atp_stake());
        assert!(a.requires_witness());

        let m = Act::memory(Uuid::new_v4(), sref(), now()); // default Reversible
        assert!(!m.requires_atp_stake());
        assert!(!m.requires_witness());
    }

    #[test]
    fn fulfilled_act_builds_entity_trust() {
        let actor = Uuid::new_v4();
        let mut trust = TrustValueScore::new(actor);
        let before = trust.value.score(ValueDimension::Validity);
        let act = Act::handoff(actor, Uuid::new_v4(), sref(), now())
            .with_consequence(ConsequenceClass::Costly);
        let (dv, _) = act.record_outcome(&mut trust, ActOutcome::Fulfilled);
        assert!(dv > 0.0);
        assert!(trust.value.score(ValueDimension::Validity) > before);
    }

    #[test]
    fn failed_irreversible_costs_more_than_reversible() {
        let actor = Uuid::new_v4();
        let mut t_irrev = TrustValueScore::new(actor);
        let mut t_rev = TrustValueScore::new(actor);
        let irrev = Act::forum(actor, sref(), now()).with_consequence(ConsequenceClass::Irreversible);
        let rev = Act::forum(actor, sref(), now()).with_consequence(ConsequenceClass::Reversible);
        let (di, _) = irrev.record_outcome(&mut t_irrev, ActOutcome::Failed);
        let (dr, _) = rev.record_outcome(&mut t_rev, ActOutcome::Failed);
        assert!(di < dr, "an irreversible failure debits Validity more steeply");
    }

    #[test]
    fn witness_marks_attach() {
        let w = WitnessAttestation {
            lct: "witness-lct".into(),
            attestation: "verified".into(),
            signature: "sig".into(),
            timestamp: now(),
        };
        let a = Act::forum(Uuid::new_v4(), sref(), now()).witnessed_by(w);
        assert_eq!(a.witnesses.len(), 1);
    }

    #[test]
    fn substance_ref_round_trips() {
        let a = Act::memory(Uuid::new_v4(), sref(), now());
        let json = serde_json::to_string(&a).unwrap();
        let back: Act = serde_json::from_str(&json).unwrap();
        assert_eq!(a, back);
    }
}
