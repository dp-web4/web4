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
//! **Two provable things, both fail-closed:**
//! - [`RatchetRequirement`] — the committed society law. Monotone: an amendment
//!   is legal only if it [`RatchetRequirement::is_legal_advance`] of the prior
//!   (the ratchet cannot reverse). Its `level()` is a derived ordinal summary.
//! - [`RatchetRequirement::satisfied_by`] — whether the society's CURRENT
//!   structure ([`SovereignStructureProof`], recomputed from constellation
//!   co-signatures + sovereign-role occupancy, never claimed) meets the
//!   requirement. A society cannot prove authority stronger than its structure
//!   supports.
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

/// A society's COMMITTED requirement for exercising sovereign authority — the
/// ratchet. Lives in the `role:sovereign` extension (witnessed society law).
/// MONOTONE: every field only tightens; see [`is_legal_advance`].
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

    /// **Fail-closed** satisfaction: does the society's current structure prove
    /// enough to exercise sovereign authority under this committed requirement?
    /// This is the act gate — sovereign authority is exercisable only when `true`.
    /// Every check reads recomputed-from-structure evidence, never a claim.
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
