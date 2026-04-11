#!/usr/bin/env python3
"""
LRC Governance Model — Reference Implementation
================================================
Implements the physics-inspired governance framework from:
  docs/what/specifications/LRC_GOVERNANCE.md (328 lines)

Covers ALL sections:
  §1 Core Concept — L/C/R parameter definitions and ranges
  §2 Transfer Functions — damping, resonance, threshold, review, quorum, cost, penalty, fast-track
  §3 Example Configurations — 4 canonical profiles with exact table values
  §4 Web4 Integration — Trust tensor mapping, ATP energy, witness marks, MRH zones, dictionaries
  §5 Implementation Patterns — Living documents, protocol governance, edge device consensus
  §6 Future Directions — Dynamic LRC, multi-dimensional LRC tensor, cross-system resonance
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Tuple

# ══════════════════════════════════════════════════════════════
# §1 — Core LRC Parameters
# ══════════════════════════════════════════════════════════════

@dataclass
class LRCParams:
    """Physics-inspired governance parameters.

    L (Inductance/Inertia): resistance to change [0.0, 1.0]
    C (Capacitance/Potential): capacity for experimentation [0.0, 1.0]
    R (Resistance/Dissipation): filtering of low-quality proposals [0.0, 1.0]
    """
    L: float  # Inductance — inertia
    C: float  # Capacitance — potential
    R: float  # Resistance — dissipation

    def __post_init__(self):
        for name, val in [("L", self.L), ("C", self.C), ("R", self.R)]:
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"{name} must be in [0.0, 1.0], got {val}")

    def __repr__(self):
        return f"LRC(L={self.L}, C={self.C}, R={self.R})"


# Default transfer function coefficients (§2)
DEFAULT_A = 0.6
DEFAULT_B = 0.8
DEFAULT_C_COEFF = 0.5
EPSILON = 1e-6  # prevents division by zero in ω₀


def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp value to [lo, hi]."""
    return max(lo, min(hi, value))


# ══════════════════════════════════════════════════════════════
# §2 — Transfer Functions
# ══════════════════════════════════════════════════════════════

@dataclass
class GovernanceControls:
    """Computed governance parameters derived from LRC values."""
    damping: float           # δ — how quickly oscillations decay
    natural_freq: float      # ω₀ — resonant rate of change
    change_threshold: float  # approval percentage required [0.50, 0.95]
    review_days: int         # days before approval
    quorum: int              # minimum reviewers
    token_cost: int          # ATP tokens required
    reject_penalty: float    # cost fraction for rejected proposals [0.10, 0.95]
    fast_track_drop: float   # reduced requirements discount

    # Source parameters
    lrc: LRCParams = field(repr=False, default=None)


def compute_governance(lrc: LRCParams,
                       a: float = DEFAULT_A,
                       b: float = DEFAULT_B,
                       c: float = DEFAULT_C_COEFF) -> GovernanceControls:
    """Compute governance controls from LRC parameters using transfer functions.

    Transfer functions (from spec):
        δ = (a·L + b·R) / (1 + c·C)
        ω₀ = 1 / √(ε + L·C)
        change_threshold = clamp(0.50 + 0.35L + 0.15R - 0.10C, 0.50, 0.95)
        review_days = round(3 + 10L + 4δ)
        quorum = ceil(1 + 2L + 1R)
        token_cost = round(50 · (0.5 + 0.7L + 0.3R))
        reject_penalty = clamp(0.10 + 0.70R, 0.10, 0.95)
        fast_track_drop = 0.20 · (1 - L)
    """
    L, C, R = lrc.L, lrc.C, lrc.R

    damping = (a * L + b * R) / (1 + c * C)
    natural_freq = 1.0 / math.sqrt(EPSILON + L * C)
    change_threshold = clamp(0.50 + 0.35 * L + 0.15 * R - 0.10 * C, 0.50, 0.95)
    review_days = round(3 + 10 * L + 4 * damping)
    quorum = math.ceil(1 + 2 * L + 1 * R)
    token_cost = round(50 * (0.5 + 0.7 * L + 0.3 * R))
    reject_penalty = clamp(0.10 + 0.70 * R, 0.10, 0.95)
    fast_track_drop = 0.20 * (1 - L)

    return GovernanceControls(
        damping=damping,
        natural_freq=natural_freq,
        change_threshold=change_threshold,
        review_days=review_days,
        quorum=quorum,
        token_cost=token_cost,
        reject_penalty=reject_penalty,
        fast_track_drop=fast_track_drop,
        lrc=lrc,
    )


# ══════════════════════════════════════════════════════════════
# §3 — Example Configurations (canonical profiles)
# ══════════════════════════════════════════════════════════════

class GovernanceProfile(Enum):
    CORE_PHILOSOPHY = "core_philosophy"
    PROTOCOL_SPEC = "protocol_spec"
    IMPLEMENTATION = "implementation"
    EXPERIMENTS = "experiments"


CANONICAL_PROFILES: Dict[GovernanceProfile, LRCParams] = {
    GovernanceProfile.CORE_PHILOSOPHY: LRCParams(L=0.9, C=0.15, R=0.8),
    GovernanceProfile.PROTOCOL_SPEC: LRCParams(L=0.7, C=0.35, R=0.6),
    GovernanceProfile.IMPLEMENTATION: LRCParams(L=0.4, C=0.6, R=0.35),
    GovernanceProfile.EXPERIMENTS: LRCParams(L=0.2, C=0.7, R=0.2),
}

# Expected table values from the spec (for validation)
CANONICAL_TABLE = {
    GovernanceProfile.CORE_PHILOSOPHY: {"threshold": 0.92, "review_days": 16, "quorum": 4, "token_cost": 68},
    GovernanceProfile.PROTOCOL_SPEC: {"threshold": 0.80, "review_days": 13, "quorum": 3, "token_cost": 58},
    GovernanceProfile.IMPLEMENTATION: {"threshold": 0.63, "review_days": 9, "quorum": 3, "token_cost": 44},
    GovernanceProfile.EXPERIMENTS: {"threshold": 0.53, "review_days": 6, "quorum": 2, "token_cost": 35},
}


# ══════════════════════════════════════════════════════════════
# §4 — Web4 Integration
# ══════════════════════════════════════════════════════════════

class TrustDimension(Enum):
    """LRC maps to trust tensor dimensions."""
    INSTITUTIONAL = "institutional"   # L → slow-changing, foundational trust
    INNOVATION = "innovation"         # C → capacity for managed risk
    QUALITY = "quality"               # R → filtering and reputation management


def lrc_to_trust_mapping(lrc: LRCParams) -> Dict[TrustDimension, float]:
    """Map LRC parameters to trust tensor dimensions."""
    return {
        TrustDimension.INSTITUTIONAL: lrc.L,
        TrustDimension.INNOVATION: lrc.C,
        TrustDimension.QUALITY: lrc.R,
    }


class MRHZone(Enum):
    """MRH zones mapped from L values."""
    PLANETARY = "planetary"    # High L — affects everyone
    ECOSYSTEM = "ecosystem"    # Medium L — affects projects
    LOCAL = "local"           # Low L — affects subsystems


def lrc_to_mrh_zone(lrc: LRCParams) -> MRHZone:
    """Determine MRH zone from inductance level."""
    if lrc.L >= 0.7:
        return MRHZone.PLANETARY
    elif lrc.L >= 0.4:
        return MRHZone.ECOSYSTEM
    else:
        return MRHZone.LOCAL


class DictionaryLRCProfile(Enum):
    """Dictionary entities have their own LRC parameters."""
    TECHNICAL = "technical"   # High L — stable definitions
    SLANG = "slang"          # High C — rapid evolution
    LEGAL = "legal"          # High R — quality filtering


DICTIONARY_PROFILES: Dict[DictionaryLRCProfile, LRCParams] = {
    DictionaryLRCProfile.TECHNICAL: LRCParams(L=0.8, C=0.2, R=0.5),
    DictionaryLRCProfile.SLANG: LRCParams(L=0.2, C=0.8, R=0.3),
    DictionaryLRCProfile.LEGAL: LRCParams(L=0.7, C=0.1, R=0.9),
}


# ══════════════════════════════════════════════════════════════
# §4.2 — ATP Energy Model
# ══════════════════════════════════════════════════════════════

@dataclass
class Proposal:
    """A governance proposal with ATP staking."""
    title: str
    lrc: LRCParams
    proposer_id: str
    support: float = 0.0        # fraction of approval [0, 1]
    witnesses: List[str] = field(default_factory=list)
    atp_staked: int = 0
    status: str = "pending"     # pending, accepted, rejected


class GovernanceEngine:
    """Full governance engine with proposal lifecycle."""

    def __init__(self, lrc: LRCParams, a=DEFAULT_A, b=DEFAULT_B, c=DEFAULT_C_COEFF):
        self.lrc = lrc
        self.controls = compute_governance(lrc, a, b, c)
        self.proposals: List[Proposal] = []
        self.atp_pool: float = 0.0  # energy dissipated through R

    def submit_proposal(self, title: str, proposer_id: str) -> Proposal:
        """Submit a proposal, staking the required ATP tokens."""
        p = Proposal(
            title=title,
            lrc=self.lrc,
            proposer_id=proposer_id,
            atp_staked=self.controls.token_cost,
        )
        self.proposals.append(p)
        return p

    def add_witness(self, proposal: Proposal, witness_id: str):
        """Add a witness to a proposal."""
        if witness_id not in proposal.witnesses:
            proposal.witnesses.append(witness_id)

    def has_quorum(self, proposal: Proposal) -> bool:
        """Check if proposal has enough witnesses."""
        return len(proposal.witnesses) >= self.controls.quorum

    def evaluate(self, proposal: Proposal) -> str:
        """Evaluate a proposal: accept or reject."""
        if not self.has_quorum(proposal):
            return "insufficient_quorum"

        if proposal.support >= self.controls.change_threshold:
            proposal.status = "accepted"
            return "accepted"
        else:
            proposal.status = "rejected"
            # Energy dissipation through R
            penalty_amount = proposal.atp_staked * self.controls.reject_penalty
            self.atp_pool += penalty_amount
            return "rejected"

    def fast_track_threshold(self) -> float:
        """Get the reduced threshold for fast-track proposals."""
        return max(0.50, self.controls.change_threshold - self.controls.fast_track_drop)


# ══════════════════════════════════════════════════════════════
# §5 — Implementation Patterns
# ══════════════════════════════════════════════════════════════

@dataclass
class DocumentSection:
    """Living document section with LRC governance front-matter."""
    section_name: str
    lrc: LRCParams

    def to_frontmatter(self) -> dict:
        """Generate YAML-compatible front-matter."""
        controls = compute_governance(self.lrc)
        return {
            "governance": {
                "section": self.section_name,
                "L": self.lrc.L,
                "C": self.lrc.C,
                "R": self.lrc.R,
                "change_threshold": controls.change_threshold,
                "review_days": controls.review_days,
                "quorum": controls.quorum,
                "token_cost": controls.token_cost,
                "reject_penalty": round(controls.reject_penalty, 2),
                "fast_track_drop": round(controls.fast_track_drop, 2),
            }
        }


class EdgeGovernance:
    """Edge device governance (from spec example)."""

    def __init__(self, L=0.3, C=0.5, R=0.7):
        self.lrc = LRCParams(L=L, C=C, R=R)
        self.controls = compute_governance(self.lrc)

    def can_modify(self, support: float) -> bool:
        """Check if a proposal has enough support for local modification."""
        return support > self.controls.change_threshold


# ══════════════════════════════════════════════════════════════
# §6 — Future Directions
# ══════════════════════════════════════════════════════════════

@dataclass
class DynamicLRC:
    """LRC values that evolve based on system state.

    - L increases with maturity (system age)
    - C adjusts to demand (activity level)
    - R responds to threats (attack frequency)
    """
    base: LRCParams
    maturity: float = 0.0      # [0, 1] how mature the system is
    activity: float = 0.5      # [0, 1] current activity level
    threat_level: float = 0.0  # [0, 1] current threat frequency

    def current(self) -> LRCParams:
        """Compute current LRC values based on dynamic state."""
        # L increases with maturity
        L = clamp(self.base.L + 0.2 * self.maturity, 0.0, 1.0)
        # C adjusts to demand
        C = clamp(self.base.C * (0.5 + self.activity), 0.0, 1.0)
        # R responds to threats
        R = clamp(self.base.R + 0.3 * self.threat_level, 0.0, 1.0)
        return LRCParams(L=L, C=C, R=R)


@dataclass
class LRCTensor:
    """Multi-dimensional LRC — tensor form.

    Each dimension has its own L, C, R for different change types:
    - L³: Different inertias for different change types
    - C³: Multiple experimentation channels
    - R³: Selective filtering by proposal category
    """
    dimensions: Dict[str, LRCParams]

    def governance_for(self, dimension: str) -> GovernanceControls:
        """Get governance controls for a specific dimension."""
        if dimension not in self.dimensions:
            raise KeyError(f"Unknown dimension: {dimension}")
        return compute_governance(self.dimensions[dimension])


@dataclass
class ResonanceMatch:
    """Cross-system resonance compatibility."""
    system_a: LRCParams
    system_b: LRCParams

    def frequency_ratio(self) -> float:
        """Ratio of natural frequencies — closer to 1.0 = more compatible."""
        f_a = 1.0 / math.sqrt(EPSILON + self.system_a.L * self.system_a.C)
        f_b = 1.0 / math.sqrt(EPSILON + self.system_b.L * self.system_b.C)
        return min(f_a, f_b) / max(f_a, f_b)

    def is_constructive(self, threshold: float = 0.7) -> bool:
        """Check if systems would resonate constructively."""
        return self.frequency_ratio() >= threshold

    def interference_type(self) -> str:
        """Classify the interference pattern."""
        ratio = self.frequency_ratio()
        if ratio >= 0.9:
            return "strongly_constructive"
        elif ratio >= 0.7:
            return "constructive"
        elif ratio >= 0.4:
            return "mixed"
        else:
            return "destructive"


# ══════════════════════════════════════════════════════════════
# §5.2 — Protocol Governance (change proposals with deadlines)
# ══════════════════════════════════════════════════════════════

@dataclass
class ProtocolChangeProposal:
    """Protocol change proposal with review deadline."""
    proposal_type: str
    lrc: LRCParams
    witnesses: List[str] = field(default_factory=list)
    energy_staked: int = 0
    review_deadline_days: int = 0

    @classmethod
    def create(cls, proposal_type: str, lrc: LRCParams) -> "ProtocolChangeProposal":
        controls = compute_governance(lrc)
        return cls(
            proposal_type=proposal_type,
            lrc=lrc,
            energy_staked=controls.token_cost,
            review_deadline_days=controls.review_days,
        )


# ══════════════════════════════════════════════════════════════
# §4.3 — Witness Integration
# ══════════════════════════════════════════════════════════════

def witness_requirements(lrc: LRCParams) -> dict:
    """Compute witness requirements from LRC parameters.

    - Higher L requires more witness marks (quorum)
    - Witnesses stake reputation proportional to R
    - Fast-track reduces witness requirements by (1-L)
    """
    controls = compute_governance(lrc)
    return {
        "quorum": controls.quorum,
        "reputation_stake": lrc.R,  # proportional to R
        "fast_track_quorum": max(1, math.ceil(controls.quorum * (1 - controls.fast_track_drop))),
    }


# ══════════════════════════════════════════════════════════════
# TESTS
# ══════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(label, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {label} {detail}")

    # ── T1: LRC Parameter Validation (§1) ──
    print("T1: LRC Parameter Validation (§1)")

    # Valid params
    p = LRCParams(L=0.5, C=0.5, R=0.5)
    check("T1.1 Valid params", p.L == 0.5 and p.C == 0.5 and p.R == 0.5)

    # Boundary values
    p_min = LRCParams(L=0.0, C=0.0, R=0.0)
    p_max = LRCParams(L=1.0, C=1.0, R=1.0)
    check("T1.2 Min boundary", p_min.L == 0.0)
    check("T1.3 Max boundary", p_max.R == 1.0)

    # Invalid params
    try:
        LRCParams(L=1.5, C=0.5, R=0.5)
        check("T1.4 L > 1.0 rejected", False)
    except ValueError:
        check("T1.4 L > 1.0 rejected", True)

    try:
        LRCParams(L=0.5, C=-0.1, R=0.5)
        check("T1.5 C < 0.0 rejected", False)
    except ValueError:
        check("T1.5 C < 0.0 rejected", True)

    try:
        LRCParams(L=0.5, C=0.5, R=2.0)
        check("T1.6 R > 1.0 rejected", False)
    except ValueError:
        check("T1.6 R > 1.0 rejected", True)

    # ── T2: Transfer Functions (§2) ──
    print("T2: Transfer Functions (§2)")

    # Damping: δ = (a·L + b·R) / (1 + c·C)
    lrc = LRCParams(L=0.9, C=0.15, R=0.8)
    g = compute_governance(lrc)
    expected_damping = (0.6 * 0.9 + 0.8 * 0.8) / (1 + 0.5 * 0.15)
    check("T2.1 Damping formula", abs(g.damping - expected_damping) < 1e-10,
          f"got {g.damping}, expected {expected_damping}")

    # Natural frequency: ω₀ = 1 / √(ε + L·C)
    expected_freq = 1.0 / math.sqrt(EPSILON + 0.9 * 0.15)
    check("T2.2 Natural frequency", abs(g.natural_freq - expected_freq) < 1e-10)

    # Change threshold: clamp(0.50 + 0.35L + 0.15R - 0.10C, 0.50, 0.95)
    raw_threshold = 0.50 + 0.35 * 0.9 + 0.15 * 0.8 - 0.10 * 0.15
    expected_threshold = clamp(raw_threshold, 0.50, 0.95)
    check("T2.3 Change threshold", abs(g.change_threshold - expected_threshold) < 1e-10,
          f"got {g.change_threshold}, expected {expected_threshold}")

    # Review days: round(3 + 10L + 4δ)
    expected_days = round(3 + 10 * 0.9 + 4 * expected_damping)
    check("T2.4 Review days", g.review_days == expected_days,
          f"got {g.review_days}, expected {expected_days}")

    # Quorum: ceil(1 + 2L + 1R)
    expected_quorum = math.ceil(1 + 2 * 0.9 + 1 * 0.8)
    check("T2.5 Quorum", g.quorum == expected_quorum,
          f"got {g.quorum}, expected {expected_quorum}")

    # Token cost: round(50 · (0.5 + 0.7L + 0.3R))
    expected_cost = round(50 * (0.5 + 0.7 * 0.9 + 0.3 * 0.8))
    check("T2.6 Token cost", g.token_cost == expected_cost,
          f"got {g.token_cost}, expected {expected_cost}")

    # Reject penalty: clamp(0.10 + 0.70R, 0.10, 0.95)
    expected_penalty = clamp(0.10 + 0.70 * 0.8, 0.10, 0.95)
    check("T2.7 Reject penalty", abs(g.reject_penalty - expected_penalty) < 1e-10)

    # Fast-track: 0.20 · (1 - L)
    expected_ft = 0.20 * (1 - 0.9)
    check("T2.8 Fast-track drop", abs(g.fast_track_drop - expected_ft) < 1e-10)

    # Clamp lower bound on threshold
    low_lrc = LRCParams(L=0.0, C=1.0, R=0.0)
    g_low = compute_governance(low_lrc)
    check("T2.9 Threshold floor at 0.50", g_low.change_threshold >= 0.50)

    # Clamp upper bound on threshold
    high_lrc = LRCParams(L=1.0, C=0.0, R=1.0)
    g_high = compute_governance(high_lrc)
    check("T2.10 Threshold ceiling at 0.95", g_high.change_threshold <= 0.95)

    # Reject penalty bounds
    zero_r = LRCParams(L=0.5, C=0.5, R=0.0)
    g_zr = compute_governance(zero_r)
    check("T2.11 Penalty floor at 0.10", g_zr.reject_penalty >= 0.10)

    max_r = LRCParams(L=0.5, C=0.5, R=1.0)
    g_mr = compute_governance(max_r)
    check("T2.12 Penalty ceiling at 0.95", g_mr.reject_penalty <= 0.95)

    # ── T3: Canonical Table Validation (§3) ──
    print("T3: Canonical Table Validation (§3)")

    for profile, expected in CANONICAL_TABLE.items():
        lrc = CANONICAL_PROFILES[profile]
        g = compute_governance(lrc)
        name = profile.value

        # Threshold as percentage, check within 1% (spec shows rounded %)
        threshold_pct = round(g.change_threshold * 100)
        expected_pct = round(expected["threshold"] * 100)
        check(f"T3.{name}.threshold", threshold_pct == expected_pct,
              f"got {threshold_pct}%, expected {expected_pct}%")

        check(f"T3.{name}.review_days", g.review_days == expected["review_days"],
              f"got {g.review_days}, expected {expected['review_days']}")

        check(f"T3.{name}.quorum", g.quorum == expected["quorum"],
              f"got {g.quorum}, expected {expected['quorum']}")

        check(f"T3.{name}.token_cost", g.token_cost == expected["token_cost"],
              f"got {g.token_cost}, expected {expected['token_cost']}")

    # ── T4: Trust Tensor Mapping (§4) ──
    print("T4: Trust Tensor Mapping (§4)")

    lrc = LRCParams(L=0.8, C=0.3, R=0.7)
    mapping = lrc_to_trust_mapping(lrc)
    check("T4.1 L → Institutional", mapping[TrustDimension.INSTITUTIONAL] == 0.8)
    check("T4.2 C → Innovation", mapping[TrustDimension.INNOVATION] == 0.3)
    check("T4.3 R → Quality", mapping[TrustDimension.QUALITY] == 0.7)

    # MRH zone mapping
    check("T4.4 High L → Planetary", lrc_to_mrh_zone(LRCParams(L=0.9, C=0.5, R=0.5)) == MRHZone.PLANETARY)
    check("T4.5 Medium L → Ecosystem", lrc_to_mrh_zone(LRCParams(L=0.5, C=0.5, R=0.5)) == MRHZone.ECOSYSTEM)
    check("T4.6 Low L → Local", lrc_to_mrh_zone(LRCParams(L=0.2, C=0.5, R=0.5)) == MRHZone.LOCAL)
    check("T4.7 L=0.7 boundary → Planetary", lrc_to_mrh_zone(LRCParams(L=0.7, C=0.5, R=0.5)) == MRHZone.PLANETARY)
    check("T4.8 L=0.4 boundary → Ecosystem", lrc_to_mrh_zone(LRCParams(L=0.4, C=0.5, R=0.5)) == MRHZone.ECOSYSTEM)

    # Dictionary profiles
    tech = DICTIONARY_PROFILES[DictionaryLRCProfile.TECHNICAL]
    check("T4.9 Technical dict: high L", tech.L >= 0.7)
    slang = DICTIONARY_PROFILES[DictionaryLRCProfile.SLANG]
    check("T4.10 Slang dict: high C", slang.C >= 0.7)
    legal = DICTIONARY_PROFILES[DictionaryLRCProfile.LEGAL]
    check("T4.11 Legal dict: high R", legal.R >= 0.7)

    # ── T5: ATP Energy Model (§4.2) ──
    print("T5: ATP Energy Model (§4.2)")

    engine = GovernanceEngine(LRCParams(L=0.7, C=0.35, R=0.6))

    # Submit proposal
    p = engine.submit_proposal("Update protocol X", "entity:alice")
    check("T5.1 Proposal created", p.status == "pending")
    check("T5.2 ATP staked", p.atp_staked == engine.controls.token_cost)

    # Add witnesses
    engine.add_witness(p, "witness:bob")
    engine.add_witness(p, "witness:carol")
    engine.add_witness(p, "witness:dave")
    check("T5.3 Witness count", len(p.witnesses) == 3)

    # Duplicate witness ignored
    engine.add_witness(p, "witness:bob")
    check("T5.4 No duplicate witnesses", len(p.witnesses) == 3)

    # Quorum check
    check("T5.5 Has quorum", engine.has_quorum(p))

    # Acceptance
    p.support = 0.85  # above 0.80 threshold for protocol_spec
    result = engine.evaluate(p)
    check("T5.6 Accepted", result == "accepted")
    check("T5.7 Status updated", p.status == "accepted")

    # Rejection with penalty
    p2 = engine.submit_proposal("Bad proposal", "entity:mallory")
    engine.add_witness(p2, "w1")
    engine.add_witness(p2, "w2")
    engine.add_witness(p2, "w3")
    p2.support = 0.30  # below threshold
    pool_before = engine.atp_pool
    result2 = engine.evaluate(p2)
    check("T5.8 Rejected", result2 == "rejected")
    check("T5.9 Energy dissipated", engine.atp_pool > pool_before)
    expected_dissipation = p2.atp_staked * engine.controls.reject_penalty
    check("T5.10 Penalty amount correct",
          abs(engine.atp_pool - pool_before - expected_dissipation) < 1e-10)

    # Insufficient quorum
    p3 = engine.submit_proposal("Lonely proposal", "entity:alone")
    p3.support = 1.0
    result3 = engine.evaluate(p3)
    check("T5.11 Insufficient quorum", result3 == "insufficient_quorum")

    # Fast-track threshold
    ft = engine.fast_track_threshold()
    check("T5.12 Fast-track < normal", ft < engine.controls.change_threshold)
    check("T5.13 Fast-track >= 0.50", ft >= 0.50)

    # ── T6: Living Document Pattern (§5) ──
    print("T6: Living Document Pattern (§5)")

    section = DocumentSection("foundational_concepts", LRCParams(L=0.7, C=0.35, R=0.6))
    fm = section.to_frontmatter()
    gov = fm["governance"]
    check("T6.1 Section name in frontmatter", gov["section"] == "foundational_concepts")
    check("T6.2 L in frontmatter", gov["L"] == 0.7)
    check("T6.3 C in frontmatter", gov["C"] == 0.35)
    check("T6.4 R in frontmatter", gov["R"] == 0.6)
    check("T6.5 Threshold computed", 0.50 <= gov["change_threshold"] <= 0.95)
    check("T6.6 Review days computed", gov["review_days"] > 0)
    check("T6.7 Quorum computed", gov["quorum"] >= 1)
    check("T6.8 Token cost computed", gov["token_cost"] > 0)

    # ── T7: Edge Device Governance (§5.3) ──
    print("T7: Edge Device Governance (§5.3)")

    edge = EdgeGovernance(L=0.3, C=0.5, R=0.7)
    # From spec: threshold = 0.50 + 0.35*0.3 + 0.15*0.7 - 0.10*0.5 = 0.50 + 0.105 + 0.105 - 0.05 = 0.66
    check("T7.1 Edge can_modify with high support", edge.can_modify(0.80))
    check("T7.2 Edge rejects low support", not edge.can_modify(0.50))
    expected_edge_threshold = clamp(0.50 + 0.35*0.3 + 0.15*0.7 - 0.10*0.5, 0.50, 0.95)
    check("T7.3 Edge threshold correct",
          abs(edge.controls.change_threshold - expected_edge_threshold) < 1e-10)

    # ── T8: Protocol Change Proposal (§5.2) ──
    print("T8: Protocol Change Proposal (§5.2)")

    pcp = ProtocolChangeProposal.create("protocol_update", LRCParams(L=0.7, C=0.35, R=0.6))
    check("T8.1 Energy staked", pcp.energy_staked == 58)
    check("T8.2 Review deadline", pcp.review_deadline_days == 13)
    check("T8.3 Proposal type", pcp.proposal_type == "protocol_update")

    # ── T9: Dynamic LRC (§6.1) ──
    print("T9: Dynamic LRC (§6.1)")

    dyn = DynamicLRC(base=LRCParams(L=0.5, C=0.5, R=0.5))

    # Baseline
    current = dyn.current()
    check("T9.1 Baseline L", current.L == 0.5)  # no maturity boost

    # With maturity
    dyn.maturity = 1.0
    current = dyn.current()
    check("T9.2 Mature L increases", current.L == clamp(0.5 + 0.2, 0.0, 1.0))

    # With high activity
    dyn.maturity = 0.0
    dyn.activity = 1.0
    current = dyn.current()
    check("T9.3 Active C increases", current.C == clamp(0.5 * 1.5, 0.0, 1.0))

    # With threats
    dyn.activity = 0.5
    dyn.threat_level = 1.0
    current = dyn.current()
    check("T9.4 Threat R increases", current.R == clamp(0.5 + 0.3, 0.0, 1.0))

    # Clamping
    dyn_high = DynamicLRC(base=LRCParams(L=0.95, C=0.9, R=0.9), maturity=1.0, activity=1.0, threat_level=1.0)
    c = dyn_high.current()
    check("T9.5 L clamped at 1.0", c.L <= 1.0)
    check("T9.6 C clamped at 1.0", c.C <= 1.0)
    check("T9.7 R clamped at 1.0", c.R <= 1.0)

    # ── T10: LRC Tensor (§6.2) ──
    print("T10: LRC Tensor (§6.2)")

    tensor = LRCTensor(dimensions={
        "security": LRCParams(L=0.9, C=0.1, R=0.9),
        "ux": LRCParams(L=0.3, C=0.8, R=0.3),
        "performance": LRCParams(L=0.5, C=0.6, R=0.5),
    })

    sec_gov = tensor.governance_for("security")
    ux_gov = tensor.governance_for("ux")
    check("T10.1 Security high threshold", sec_gov.change_threshold > ux_gov.change_threshold)
    check("T10.2 Security more review days", sec_gov.review_days > ux_gov.review_days)
    check("T10.3 Security higher quorum", sec_gov.quorum > ux_gov.quorum)
    check("T10.4 Security higher cost", sec_gov.token_cost > ux_gov.token_cost)

    # Unknown dimension raises
    try:
        tensor.governance_for("unknown")
        check("T10.5 Unknown dim raises", False)
    except KeyError:
        check("T10.5 Unknown dim raises", True)

    # ── T11: Cross-System Resonance (§6.3) ──
    print("T11: Cross-System Resonance (§6.3)")

    # Identical systems = perfect resonance
    same = ResonanceMatch(LRCParams(L=0.5, C=0.5, R=0.5), LRCParams(L=0.5, C=0.5, R=0.5))
    check("T11.1 Identical = ratio 1.0", abs(same.frequency_ratio() - 1.0) < 1e-10)
    check("T11.2 Identical = constructive", same.is_constructive())
    check("T11.3 Identical = strongly constructive", same.interference_type() == "strongly_constructive")

    # Similar systems
    similar = ResonanceMatch(LRCParams(L=0.5, C=0.5, R=0.5), LRCParams(L=0.6, C=0.4, R=0.5))
    check("T11.4 Similar = constructive", similar.is_constructive())

    # Very different systems
    different = ResonanceMatch(LRCParams(L=0.9, C=0.9, R=0.5), LRCParams(L=0.1, C=0.1, R=0.5))
    check("T11.5 Different = not constructive", not different.is_constructive(threshold=0.7))
    check("T11.6 Different = destructive or mixed",
          different.interference_type() in ("destructive", "mixed"))

    # Frequency ratio symmetric
    ab = ResonanceMatch(LRCParams(L=0.3, C=0.7, R=0.5), LRCParams(L=0.7, C=0.3, R=0.5))
    ba = ResonanceMatch(LRCParams(L=0.7, C=0.3, R=0.5), LRCParams(L=0.3, C=0.7, R=0.5))
    check("T11.7 Frequency ratio symmetric", abs(ab.frequency_ratio() - ba.frequency_ratio()) < 1e-10)

    # ── T12: Witness Requirements (§4.3) ──
    print("T12: Witness Requirements (§4.3)")

    wr = witness_requirements(LRCParams(L=0.9, C=0.15, R=0.8))
    check("T12.1 Quorum matches governance", wr["quorum"] == 4)
    check("T12.2 Reputation stake = R", wr["reputation_stake"] == 0.8)
    check("T12.3 Fast-track quorum <= normal", wr["fast_track_quorum"] <= wr["quorum"])
    check("T12.4 Fast-track quorum >= 1", wr["fast_track_quorum"] >= 1)

    low_wr = witness_requirements(LRCParams(L=0.2, C=0.7, R=0.2))
    check("T12.5 Low L = low quorum", low_wr["quorum"] <= wr["quorum"])

    # ── T13: Monotonicity Properties ──
    print("T13: Monotonicity Properties")

    # Higher L → higher threshold (holding C, R constant)
    g_low_l = compute_governance(LRCParams(L=0.3, C=0.5, R=0.5))
    g_high_l = compute_governance(LRCParams(L=0.8, C=0.5, R=0.5))
    check("T13.1 Higher L → higher threshold", g_high_l.change_threshold > g_low_l.change_threshold)
    check("T13.2 Higher L → more review days", g_high_l.review_days > g_low_l.review_days)
    check("T13.3 Higher L → higher quorum", g_high_l.quorum >= g_low_l.quorum)
    check("T13.4 Higher L → higher cost", g_high_l.token_cost > g_low_l.token_cost)

    # Higher R → higher penalty
    g_low_r = compute_governance(LRCParams(L=0.5, C=0.5, R=0.2))
    g_high_r = compute_governance(LRCParams(L=0.5, C=0.5, R=0.8))
    check("T13.5 Higher R → higher penalty", g_high_r.reject_penalty > g_low_r.reject_penalty)

    # Higher C → lower threshold
    g_low_c = compute_governance(LRCParams(L=0.5, C=0.2, R=0.5))
    g_high_c = compute_governance(LRCParams(L=0.5, C=0.8, R=0.5))
    check("T13.6 Higher C → lower threshold", g_high_c.change_threshold < g_low_c.change_threshold)

    # Higher L → lower fast-track drop
    check("T13.7 Higher L → less fast-track", g_high_l.fast_track_drop < g_low_l.fast_track_drop)

    # ── T14: Edge Cases ──
    print("T14: Edge Cases")

    # All zeros
    g0 = compute_governance(LRCParams(L=0.0, C=0.0, R=0.0))
    check("T14.1 Zero LRC: threshold = 0.50", abs(g0.change_threshold - 0.50) < 1e-10)
    check("T14.2 Zero LRC: quorum = 1", g0.quorum == 1)
    check("T14.3 Zero LRC: cost = 25", g0.token_cost == 25)  # round(50 * 0.5) = 25
    check("T14.4 Zero LRC: penalty = 0.10", abs(g0.reject_penalty - 0.10) < 1e-10)
    check("T14.5 Zero LRC: fast-track = 0.20", abs(g0.fast_track_drop - 0.20) < 1e-10)

    # All ones
    g1 = compute_governance(LRCParams(L=1.0, C=1.0, R=1.0))
    check("T14.6 Max LRC: threshold = 0.90", abs(g1.change_threshold - 0.90) < 1e-10)
    check("T14.7 Max LRC: quorum = 4", g1.quorum == 4)
    check("T14.8 Max LRC: cost = 75", g1.token_cost == 75)  # round(50 * (0.5 + 0.7 + 0.3)) = 75
    check("T14.9 Max LRC: penalty = 0.80", abs(g1.reject_penalty - 0.80) < 1e-10)
    check("T14.10 Max LRC: fast-track = 0.0", abs(g1.fast_track_drop - 0.0) < 1e-10)

    # ω₀ with zero L or zero C (tests epsilon guard)
    g_zero_lc = compute_governance(LRCParams(L=0.0, C=0.0, R=0.5))
    check("T14.11 ω₀ with L=0 C=0 finite", math.isfinite(g_zero_lc.natural_freq))
    check("T14.12 ω₀ with L=0 C=0 = 1/√ε", abs(g_zero_lc.natural_freq - 1.0/math.sqrt(EPSILON)) < 1e-2)

    # Custom coefficients
    g_custom = compute_governance(LRCParams(L=0.5, C=0.5, R=0.5), a=1.0, b=1.0, c=1.0)
    expected_damping_custom = (1.0 * 0.5 + 1.0 * 0.5) / (1 + 1.0 * 0.5)
    check("T14.13 Custom coefficients work", abs(g_custom.damping - expected_damping_custom) < 1e-10)

    # ── T15: Practical Application Profiles (§7-§8) ──
    print("T15: Practical Application Profiles (§7-§8)")

    # Web4 Protocol Evolution profiles
    core_lct = compute_governance(LRCParams(L=0.8, C=0.3, R=0.7))
    transport = compute_governance(LRCParams(L=0.5, C=0.5, R=0.5))
    ui = compute_governance(LRCParams(L=0.3, C=0.7, R=0.3))

    check("T15.1 Core LCT > Transport threshold", core_lct.change_threshold > transport.change_threshold)
    check("T15.2 Transport > UI threshold", transport.change_threshold > ui.change_threshold)
    check("T15.3 Core LCT > UI review days", core_lct.review_days > ui.review_days)
    check("T15.4 Core LCT > UI cost", core_lct.token_cost > ui.token_cost)

    # SAGE Cognition Pools
    safety = compute_governance(LRCParams(L=0.9, C=0.1, R=0.9))
    perf = compute_governance(LRCParams(L=0.3, C=0.8, R=0.3))
    check("T15.5 Safety > Performance threshold", safety.change_threshold > perf.change_threshold)
    check("T15.6 Safety > Performance cost", safety.token_cost > perf.token_cost)

    # Memory system
    core_mem = compute_governance(LRCParams(L=0.8, C=0.3, R=0.5))
    indexing = compute_governance(LRCParams(L=0.4, C=0.6, R=0.4))
    check("T15.7 Core memory > Indexing threshold", core_mem.change_threshold > indexing.change_threshold)

    # ── T16: Governance Engine Lifecycle ──
    print("T16: Governance Engine Lifecycle")

    eng = GovernanceEngine(LRCParams(L=0.4, C=0.6, R=0.35))

    # Multiple proposals
    pa = eng.submit_proposal("Feature A", "alice")
    pb = eng.submit_proposal("Feature B", "bob")
    check("T16.1 Multiple proposals tracked", len(eng.proposals) == 2)

    # Add witnesses to both
    for w in ["w1", "w2", "w3"]:
        eng.add_witness(pa, w)
        eng.add_witness(pb, w)

    # Accept one, reject one
    pa.support = 0.90
    pb.support = 0.40

    ra = eng.evaluate(pa)
    rb = eng.evaluate(pb)
    check("T16.2 A accepted", ra == "accepted")
    check("T16.3 B rejected", rb == "rejected")
    check("T16.4 Pool has dissipated energy", eng.atp_pool > 0)

    # ══════════════════════════════════════════════════════════

    print(f"\n{'='*60}")
    print(f"LRC Governance: {passed}/{passed+failed} checks passed")
    if failed:
        print(f"  {failed} FAILED")
    else:
        print(f"  All checks passed!")
    print(f"{'='*60}")
    return failed == 0


if __name__ == "__main__":
    run_tests()
