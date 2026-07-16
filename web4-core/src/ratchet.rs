// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// This software is covered by US Patents 11,477,027 and 12,278,913,
// and pending application 19/178,619. See PATENTS.md for details.

//! The society ratchet — a monotone, provable measure of how far a society's
//! **sovereign authority** has climbed away from reachability-as-authority.
//!
//! Design: `specs/hestia-role-orchestration/society-ratchet-model-2026-07-15.md`.
//!
//! The Sovereign is a *role* (SAL §2.1), not a special entity. A society's
//! requirement for exercising sovereign authority (amend law, confer birth
//! certificates, admit/bar members) is a monotone function of society law: it
//! only ever tightens — more devices, more factors, more distinct occupants,
//! eventually the genesis operator **barred** from singularly filling the role.
//! The genesis rung (L0) is the honest weak pole: one device, one operator, so
//! *access is the authority proof* (the RWOA `R` clause; the genesis bootstrap
//! window "cannot be re-entered once witnessed authority exists" — the ratchet
//! makes that continuous and provable).
//!
//! **Whose bar? — web4 makes the evidence inspectable; it does NOT state the
//! threshold.** The structure earns *some* level of trust, but *how much* is the
//! **relying party's** contextual call, scaled to the stakes of the specific act.
//! Web4 states neither who nor when should be trusted; it provides the tools to
//! make the evidence unforgeable and inspectable. So there is no universal gate
//! here and no exclusion: an entity presenting one-device-reachability-as-proof
//! is **not barred** — it is rightly weighed as **higher risk** than a full
//! constellation with rich witnessed reputation, and the evaluator decides what
//! that risk buys for *this* act. A [`RatchetRequirement`] is therefore a *bar an
//! evaluator holds*, used two ways with the same type:
//! - a society checking its OWN structure against its OWN committed law
//!   (self-governance — the monotone ratchet of its own sovereign acts), and
//! - a relying party checking a *presented* society against the relying party's
//!   OWN risk policy for a given act (federation trust).
//!
//! A society's own committed requirement is itself inspectable evidence ("this
//! society holds its sovereign to a 2-device + biometric bar" is a trust signal).
//!
//! **Two provable things, both fail-closed:**
//! - [`RatchetRequirement`] — a bar; when it is a society's own committed law it
//!   is monotone: an amendment is legal only if it
//!   [`RatchetRequirement::is_legal_advance`] of the prior (a society's ratchet
//!   over its own acts cannot reverse). `level()` is a derived ordinal summary.
//! - [`RatchetRequirement::satisfied_by`] — whether a presented
//!   [`SovereignStructureProof`] (recomputed from constellation co-signatures +
//!   sovereign-role occupancy, never claimed) clears the evaluator's bar. An
//!   entity cannot *prove* authority stronger than its structure supports; a
//!   `false` is "below this evaluator's bar for these stakes" (higher risk), not
//!   a protocol verdict of exclusion.
//!
//! T3/V3 weighting of occupant assurance is deliberately DEFERRED (a separate
//! calibrated step, so the ratchet does not silently move the trust surface).

use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

/// One independent class of sovereign-authority evidence. Each is provable from
/// queryable structure — none is a self-asserted claim. `DevicePossession` and
/// `HardwareToken` map onto the existing constellation `AssuranceLevel`; the
/// others extend it.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum FactorClass {
    /// Access to a bound device proven by a challenge co-signature.
    DevicePossession,
    /// A hardware-backed device co-signature (TPM/SE) — strongest device proof.
    HardwareToken,
    /// A biometric factor attestation.
    Biometric,
    /// A distinct entity co-filling the sovereign role (beyond the operator).
    DistinctOccupant,
}

/// A **bar** an evaluator holds against sovereign-authority evidence — read the
/// module docs on *whose* bar. When it is a society's OWN committed law (in the
/// `role:sovereign` extension, witnessed) it is MONOTONE — every field only
/// tightens; see [`is_legal_advance`]. When it is a relying party's risk policy
/// for a given act, monotonicity does not apply (the relying party sets whatever
/// bar the stakes warrant). The struct is the same; the two uses differ only in
/// who authors it and whether the ratchet (self-law) constrains its evolution.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct RatchetRequirement {
    /// Distinct devices whose possession must be proven (≥1).
    pub min_devices: u8,
    /// A hardware-backed device co-signature is required.
    pub require_hardware_backed: bool,
    /// Independent factor classes required beyond the device count.
    #[serde(default)]
    pub required_factors: BTreeSet<FactorClass>,
    /// Distinct entities that must jointly fill the sovereign role (≥1). `1` =
    /// autocratic (single occupant); `≥2` = a Governance-Council (SAL §2.1).
    pub min_sovereign_occupants: u8,
    /// Once `true`, the genesis operator may NOT singularly fill the sovereign
    /// role — a one-way flip (the ratchet's terminal social property).
    pub operator_sole_fill_barred: bool,
}

impl RatchetRequirement {
    /// L0 — the genesis rung. One device, one operator, no extra factors, operator
    /// may fill sovereign alone. Access is the authority proof because nothing
    /// stronger exists yet (honest weak-`R`; the bootstrap window).
    pub fn genesis() -> Self {
        RatchetRequirement {
            min_devices: 1,
            require_hardware_backed: false,
            required_factors: BTreeSet::new(),
            min_sovereign_occupants: 1,
            operator_sole_fill_barred: false,
        }
    }

    /// The RATCHET GATE: `next` is a legal amendment iff it tightens (or holds)
    /// EVERY axis. Any relaxation — fewer devices, a dropped factor, fewer
    /// occupants, un-barring the operator — returns `false`. This is the one-way
    /// property; the same monotone discipline as the role-law strictest-wins fold.
    pub fn is_legal_advance(&self, next: &RatchetRequirement) -> bool {
        next.min_devices >= self.min_devices
            && (!self.require_hardware_backed || next.require_hardware_backed)
            && self.required_factors.is_subset(&next.required_factors)
            && next.min_sovereign_occupants >= self.min_sovereign_occupants
            && (!self.operator_sole_fill_barred || next.operator_sole_fill_barred)
    }

    /// A derived ordinal summary of the committed requirement (0 = genesis). Each
    /// authority-strengthening property counts once; MONOTONE in the requirement
    /// (if `a.is_legal_advance(b)` then `a.level() <= b.level()`). The requirement
    /// vector is authoritative — this is a comparable digest, not the ground truth.
    pub fn level(&self) -> u8 {
        (self.min_devices >= 2) as u8
            + self.require_hardware_backed as u8
            + (!self.required_factors.is_empty()) as u8
            + (self.min_sovereign_occupants >= 2) as u8
            + self.operator_sole_fill_barred as u8
    }

    /// **Fail-closed** predicate: does the presented structure clear the bar in
    /// `self`? The bar belongs to whoever is EVALUATING — a society against its
    /// own committed law (self-governance), or a relying party against its own
    /// risk policy for a specific act's stakes. Web4 ships the inspectable
    /// evidence and this predicate; it never states a universal threshold.
    ///
    /// `false` means "below THIS evaluator's bar for these stakes" — **higher
    /// risk, not exclusion**. A low-assurance entity is not barred from asking;
    /// it is rightly weighed as riskier, and the evaluator scales its bar to the
    /// act (RWOA: trust is a contextual preponderance of evidence scaled to
    /// stakes, not a boolean — low-stakes reversible acts may clear a low bar).
    /// The one hard invariant web4 does enforce: an entity cannot *prove*
    /// authority its structure does not support (every axis is recomputed from
    /// structure, never a claim).
    pub fn satisfied_by(&self, s: &SovereignStructureProof) -> bool {
        s.verified_devices >= self.min_devices
            && (!self.require_hardware_backed || s.hardware_backed)
            && self.required_factors.is_subset(&s.present_factors)
            && s.distinct_sovereign_occupants >= self.min_sovereign_occupants
        // Note: `operator_sole_fill_barred` constrains WHO may occupy (checked at
        // admission), not a count here — a society that bars sole-fill also sets
        // min_sovereign_occupants >= 2, which IS checked above.
    }
}

/// What a society's structure currently PROVES about sovereign authority —
/// recomputed from queryable evidence (constellation co-signatures + the
/// sovereign role's `mrh.paired` occupants + factor attestations), never trusted
/// from a claimed field. The verifier's ground truth for [`satisfied_by`].
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct SovereignStructureProof {
    /// Distinct devices with a verified challenge co-signature (the constellation
    /// `AssuranceLevel` device count, recomputed).
    pub verified_devices: u8,
    /// At least one verified co-signature came from a hardware-backed device.
    pub hardware_backed: bool,
    /// Factor classes actually attested by structure.
    #[serde(default)]
    pub present_factors: BTreeSet<FactorClass>,
    /// Distinct entities occupying the sovereign role (`mrh.paired` `sovereign`
    /// edges, deduplicated).
    pub distinct_sovereign_occupants: u8,
}

#[cfg(test)]
mod tests {
    use super::*;

    fn factors(fs: &[FactorClass]) -> BTreeSet<FactorClass> {
        fs.iter().copied().collect()
    }

    #[test]
    fn genesis_is_the_weakest_rung() {
        let g = RatchetRequirement::genesis();
        assert_eq!(g.level(), 0);
        // Genesis is satisfied by a single device — access is authority.
        assert!(g.satisfied_by(&SovereignStructureProof {
            verified_devices: 1,
            hardware_backed: false,
            present_factors: BTreeSet::new(),
            distinct_sovereign_occupants: 1,
        }));
    }

    #[test]
    fn the_ratchet_is_one_way() {
        let g = RatchetRequirement::genesis();
        let tightened = RatchetRequirement {
            min_devices: 2,
            required_factors: factors(&[FactorClass::Biometric]),
            min_sovereign_occupants: 2,
            operator_sole_fill_barred: true,
            ..g.clone()
        };
        assert!(g.is_legal_advance(&tightened), "tightening every axis is legal");
        assert!(!tightened.is_legal_advance(&g), "relaxing back is NOT legal");
        // level is monotone under a legal advance
        assert!(g.level() < tightened.level());
        // a single-axis relaxation is illegal (drop the biometric factor)
        let dropped = RatchetRequirement { required_factors: BTreeSet::new(), ..tightened.clone() };
        assert!(!tightened.is_legal_advance(&dropped));
        // un-barring the operator is illegal
        let unbarred = RatchetRequirement { operator_sole_fill_barred: false, ..tightened.clone() };
        assert!(!tightened.is_legal_advance(&unbarred));
    }

    #[test]
    fn satisfaction_is_fail_closed_cannot_prove_beyond_structure() {
        // A society commits to a 3-device + hardware + council-of-2 requirement…
        let req = RatchetRequirement {
            min_devices: 3,
            require_hardware_backed: true,
            required_factors: factors(&[FactorClass::Biometric]),
            min_sovereign_occupants: 2,
            operator_sole_fill_barred: true,
        };
        // …but its structure proves only 1 software device, 1 occupant, no factor.
        let weak = SovereignStructureProof {
            verified_devices: 1,
            hardware_backed: false,
            present_factors: BTreeSet::new(),
            distinct_sovereign_occupants: 1,
        };
        assert!(!req.satisfied_by(&weak), "cannot prove authority beyond structure");
        // Structure that meets every axis satisfies it.
        let strong = SovereignStructureProof {
            verified_devices: 3,
            hardware_backed: true,
            present_factors: factors(&[FactorClass::Biometric]),
            distinct_sovereign_occupants: 2,
        };
        assert!(req.satisfied_by(&strong));
        // Each single missing axis independently fails closed.
        for weaken in [
            SovereignStructureProof { verified_devices: 2, ..strong.clone() },
            SovereignStructureProof { hardware_backed: false, ..strong.clone() },
            SovereignStructureProof { present_factors: BTreeSet::new(), ..strong.clone() },
            SovereignStructureProof { distinct_sovereign_occupants: 1, ..strong.clone() },
        ] {
            assert!(!req.satisfied_by(&weaken), "one missing axis must fail closed");
        }
    }

    #[test]
    fn low_assurance_is_evidence_not_exclusion_relying_party_decides() {
        // The SAME weak structure (one-device, access-as-proof) clears a lenient
        // evaluator's bar and misses a strict one. Web4 states no universal
        // threshold — the bar is the relying party's, scaled to the act's stakes.
        let weak = SovereignStructureProof {
            verified_devices: 1,
            hardware_backed: false,
            present_factors: BTreeSet::new(),
            distinct_sovereign_occupants: 1,
        };
        // A relying party admitting a LOW-stakes reversible act accepts genesis.
        let lenient = RatchetRequirement::genesis();
        assert!(lenient.satisfied_by(&weak), "weak structure clears a low bar");
        // A relying party gating a HIGH-stakes irreversible act sets a high bar;
        // the same entity is not EXCLUDED — it is simply below THIS bar (riskier).
        let strict = RatchetRequirement {
            min_devices: 2,
            require_hardware_backed: true,
            required_factors: factors(&[FactorClass::Biometric]),
            min_sovereign_occupants: 2,
            operator_sole_fill_barred: true,
        };
        assert!(!strict.satisfied_by(&weak), "same structure, higher bar → below bar (not barred)");
        // The distinction is the EVALUATOR's, not the entity's: one structure,
        // two verdicts, because trust is contextual and scaled to stakes.
    }

    #[test]
    fn level_summary_is_monotone_across_a_climb() {
        // A plausible ratchet climb, each step a legal advance, level non-decreasing.
        let steps = [
            RatchetRequirement::genesis(),
            RatchetRequirement { min_devices: 2, ..RatchetRequirement::genesis() },
            RatchetRequirement { min_devices: 2, required_factors: factors(&[FactorClass::Biometric]), ..RatchetRequirement::genesis() },
            RatchetRequirement { min_devices: 2, require_hardware_backed: true, required_factors: factors(&[FactorClass::Biometric]), ..RatchetRequirement::genesis() },
            RatchetRequirement { min_devices: 2, require_hardware_backed: true, required_factors: factors(&[FactorClass::Biometric]), min_sovereign_occupants: 2, operator_sole_fill_barred: true },
        ];
        for w in steps.windows(2) {
            assert!(w[0].is_legal_advance(&w[1]), "each step is a legal advance");
            assert!(w[0].level() <= w[1].level(), "level never decreases");
        }
        assert_eq!(steps[0].level(), 0);
        assert_eq!(steps[4].level(), 5);
    }
}
