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

/// Where an act is addressed — the recipient **and** its MRH relevance horizon
/// in one typed field: "the MRH scope *is* the addressing" (HUB). This mirrors
/// the hub-track `HubEvent::ReferencedAct { to: ActAddress, .. }` so the core
/// act and the hub envelope agree on the recipient model. A hub→citizen
/// notification is just this act reversed (`from = hub, to = Citizen`).
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case", tag = "to")]
pub enum ActAddress {
    /// Another instance of the plural self (next wake / post-compaction) — a
    /// memory write. MRH = temporal.
    FutureSelf { entity: Uuid },
    /// A peer cell (machine/track LCT) — a handoff. MRH = lateral.
    Peer { lct_id: Uuid },
    /// A specific citizen of this society — the notification case
    /// (hub→citizen). MRH = lateral.
    Citizen { lct_id: Uuid },
    /// A role; fans out to its current holders. MRH = broad.
    Role { role: String },
    /// The society at large — a forum post. (Contributed back: HUB's draft has
    /// no all-citizens variant; forum-to-everyone isn't `Role` fan-out.)
    Society { lct_id: Uuid },
}

impl ActAddress {
    /// The coarse MRH axis this address reaches across.
    pub fn mrh_direction(&self) -> MrhDirection {
        match self {
            ActAddress::FutureSelf { .. } => MrhDirection::Temporal,
            ActAddress::Peer { .. } | ActAddress::Citizen { .. } => MrhDirection::Lateral,
            ActAddress::Role { .. } | ActAddress::Society { .. } => MrhDirection::Broad,
        }
    }
}

/// The coarse MRH axis an act reaches across (derived from [`ActAddress`]).
#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum MrhDirection {
    /// To your future self — a memory write (temporal MRH).
    Temporal,
    /// To a peer or a citizen — a handoff / notification (lateral MRH).
    Lateral,
    /// To a role or the society at large — a forum post (broad MRH).
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

    /// The **default** mapping from consequence class to "needs a council
    /// `proposal_ref` (M-of-N authorization)". Reversibility is the intrinsic,
    /// actor-assessable property (canonical, in the type); whether a class
    /// actually gates on council is **per-society charter policy** that the hub
    /// owns (via its existing council-threshold config) — a society may gate a
    /// Costly-but-reversible large spend, or auto-approve a sensitive reversible
    /// act. This helper is the sensible default (`Irreversible ⇒ council`), not
    /// type law; the hub may override per charter (HUB, 2026-06-20).
    pub fn requires_council(self) -> bool {
        matches!(self, ConsequenceClass::Irreversible)
    }
}

/// A thin, witnessed governance record of an entity externalizing work — the
/// unifying primitive behind memory writes, handoffs, and forum posts.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct Act {
    pub act_id: Uuid,
    /// The acting entity — the **from**. Rides in the payload; the ledger
    /// envelope's signer may differ (HUB's identity bridge: the machine/track
    /// LCT signs the envelope, an arc-LCT is `actor_lct` here).
    pub actor_lct: Uuid,
    /// Recipient + MRH relevance horizon, in one field.
    pub address: ActAddress,
    /// Act kind — lets a recipient route/filter **without opening the
    /// substance**. Convention (HUB, hub↔core converged): a bare `<verb>`
    /// for fleet/peer acts (`handoff`, `memo`, `sweep`, `forum`); the
    /// `notify:<event>` namespace for hub→citizen notifications (the
    /// act-reversed case, e.g. `notify:intro_accepted`). The `notify:*`
    /// sub-vocabulary is hub-minted; the canonical registry lives in the
    /// society/ledger spec. Open set — extend freely.
    #[serde(default)]
    pub kind: String,
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
    /// Default kind `"memo"`.
    pub fn memory(actor_lct: Uuid, substance: SubstanceRef, at: DateTime<Utc>) -> Self {
        Self::addressed(actor_lct, ActAddress::FutureSelf { entity: actor_lct }, "memo", substance, at)
    }

    /// A **handoff** — an act to a peer (lateral MRH). Default kind `"handoff"`.
    pub fn handoff(actor_lct: Uuid, peer_lct: Uuid, substance: SubstanceRef, at: DateTime<Utc>) -> Self {
        Self::addressed(actor_lct, ActAddress::Peer { lct_id: peer_lct }, "handoff", substance, at)
    }

    /// A **forum post** — an act to the society at large (broad MRH). Default
    /// kind `"forum"`.
    pub fn forum(actor_lct: Uuid, society_lct: Uuid, substance: SubstanceRef, at: DateTime<Utc>) -> Self {
        Self::addressed(actor_lct, ActAddress::Society { lct_id: society_lct }, "forum", substance, at)
    }

    /// The general constructor — any [`ActAddress`] + [`kind`](Act::kind)
    /// (incl. the hub→`Citizen` `notify:<event>` case and `Role` fan-out).
    pub fn addressed(
        actor_lct: Uuid,
        address: ActAddress,
        kind: impl Into<String>,
        substance: SubstanceRef,
        at: DateTime<Utc>,
    ) -> Self {
        Self {
            act_id: Uuid::new_v4(),
            actor_lct,
            address,
            kind: kind.into(),
            consequence: ConsequenceClass::default(),
            substance,
            witnesses: Vec::new(),
            at,
        }
    }

    /// Override the act [`kind`](Act::kind) — e.g. a more specific verb than a
    /// constructor's default, or a `notify:<event>` on a `Citizen`-addressed act.
    pub fn with_kind(mut self, kind: impl Into<String>) -> Self {
        self.kind = kind.into();
        self
    }

    pub fn with_consequence(mut self, c: ConsequenceClass) -> Self {
        self.consequence = c;
        self
    }

    pub fn witnessed_by(mut self, attestation: WitnessAttestation) -> Self {
        self.witnesses.push(attestation);
        self
    }

    /// The coarse MRH axis this act reaches across (derived from its address).
    pub fn mrh_direction(&self) -> MrhDirection {
        self.address.mrh_direction()
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
        let soc = Uuid::new_v4();
        // One primitive, differing only in MRH-as-addressing.
        assert_eq!(Act::memory(me, sref(), now()).mrh_direction(), MrhDirection::Temporal);
        assert_eq!(Act::handoff(me, peer, sref(), now()).mrh_direction(), MrhDirection::Lateral);
        assert_eq!(Act::forum(me, soc, sref(), now()).mrh_direction(), MrhDirection::Broad);
        // The handoff is the only one addressed to a specific peer.
        assert_eq!(Act::handoff(me, peer, sref(), now()).address, ActAddress::Peer { lct_id: peer });
        assert_eq!(Act::memory(me, sref(), now()).address, ActAddress::FutureSelf { entity: me });
        // Default kinds per HUB's vocabulary.
        assert_eq!(Act::memory(me, sref(), now()).kind, "memo");
        assert_eq!(Act::handoff(me, peer, sref(), now()).kind, "handoff");
        assert_eq!(Act::forum(me, soc, sref(), now()).kind, "forum");
        assert_eq!(Act::memory(me, sref(), now()).with_kind("runbook").kind, "runbook");
    }

    #[test]
    fn citizen_notification_is_the_act_reversed() {
        // HUB's insight: a hub→citizen notification is the same primitive,
        // addressed to a Citizen (lateral MRH).
        let hub = Uuid::new_v4();
        let citizen = Uuid::new_v4();
        let n = Act::addressed(
            hub,
            ActAddress::Citizen { lct_id: citizen },
            "notify:intro_accepted",
            sref(),
            now(),
        );
        assert_eq!(n.mrh_direction(), MrhDirection::Lateral);
        assert_eq!(n.actor_lct, hub);
        assert!(n.kind.starts_with("notify:"));
    }

    #[test]
    fn irreversible_acts_gate_on_atp_witness_and_council() {
        let a = Act::forum(Uuid::new_v4(), Uuid::new_v4(), sref(), now())
            .with_consequence(ConsequenceClass::Irreversible);
        assert!(a.requires_atp_stake());
        assert!(a.requires_witness());
        // Bridge to HUB's gate: Irreversible == High == needs a council proposal_ref.
        assert!(a.consequence.requires_council());

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
        let soc = Uuid::new_v4();
        let irrev = Act::forum(actor, soc, sref(), now()).with_consequence(ConsequenceClass::Irreversible);
        let rev = Act::forum(actor, soc, sref(), now()).with_consequence(ConsequenceClass::Reversible);
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
        let a = Act::forum(Uuid::new_v4(), Uuid::new_v4(), sref(), now()).witnessed_by(w);
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
