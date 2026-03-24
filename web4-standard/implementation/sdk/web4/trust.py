"""
Web4 Trust Tensors (T3/V3)

Canonical implementation of the T3 (Trust) and V3 (Value) tensor systems
per web4-standard/core-spec/t3-v3-tensors.md.

T3 dimensions: Talent, Training, Temperament
V3 dimensions: Valuation, Veracity, Validity

Key design principle: tensors are ROLE-CONTEXTUAL. An entity's trust
as a surgeon has no bearing on trust as a mechanic. All operations
accept an optional role parameter for proper context binding.

Validated against: web4-standard/test-vectors/t3v3/tensor-operations.json
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# ── Canonical weights (from test vectors) ────────────────────────

T3_WEIGHTS = {"talent": 0.4, "training": 0.3, "temperament": 0.3}
V3_WEIGHTS = {"valuation": 0.3, "veracity": 0.35, "validity": 0.35}

# Update factors per dimension (test vector t3v3-003)
T3_UPDATE_FACTORS = {"talent": 1.0, "training": 0.8, "temperament": 0.6}

# Update rate
T3_UPDATE_RATE = 0.02

# Trust bridge weights (test vector t3v3-008)
BRIDGE_PRIMARY_WEIGHT = 0.6
BRIDGE_SECONDARY_WEIGHT_EACH = 1 / 3  # of remaining 0.4

# MRH decay (test vector t3v3-009)
MRH_MAX_HOPS = 4  # 5+ hops = BEYOND = zero trust

# Operational health weights (test vector t3v3-010)
# NOTE: The whitepaper uses "coherence" for identity coherence (C×S×Phi×R),
# a distinct concept measuring pattern stability and self-reference.
# This SDK metric measures operational health (trust + value + energy).
HEALTH_WEIGHTS = {"t3": 0.4, "v3": 0.3, "energy": 0.3}
HEALTH_THRESHOLD = 0.7

# Diminishing returns (test vector t3v3-007)
DIMINISHING_BASE = 0.8
DIMINISHING_FLOOR = 0.1

# ── JSON-LD Context URIs ─────────────────────────────────────

T3_JSONLD_CONTEXT = "https://web4.io/contexts/t3.jsonld"
V3_JSONLD_CONTEXT = "https://web4.io/contexts/v3.jsonld"
WEB4_ONTOLOGY_NS = "https://web4.io/ontology#"  # Kept for OWL/RDF tooling reference

# ── Outcome-based evolution (spec §2.3) ──────────────────────────


class ActionOutcome(Enum):
    """Categorized action outcomes per spec §2.3 evolution table."""
    NOVEL_SUCCESS = "novel_success"
    STANDARD_SUCCESS = "standard_success"
    EXPECTED_FAILURE = "expected_failure"
    UNEXPECTED_FAILURE = "unexpected_failure"
    ETHICS_VIOLATION = "ethics_violation"


# Per-dimension delta ranges: (talent, training, temperament)
# Using midpoints of spec ranges for deterministic cross-language compatibility.
OUTCOME_DELTAS: Dict[ActionOutcome, Dict[str, float]] = {
    ActionOutcome.NOVEL_SUCCESS: {"talent": 0.035, "training": 0.015, "temperament": 0.01},
    ActionOutcome.STANDARD_SUCCESS: {"talent": 0.0, "training": 0.0075, "temperament": 0.005},
    ActionOutcome.EXPECTED_FAILURE: {"talent": -0.01, "training": 0.0, "temperament": 0.0},
    ActionOutcome.UNEXPECTED_FAILURE: {"talent": -0.02, "training": -0.01, "temperament": -0.02},
    ActionOutcome.ETHICS_VIOLATION: {"talent": -0.05, "training": 0.0, "temperament": -0.10},
}

# ── Decay/refresh rates (spec §2.3) ─────────────────────────────

TRAINING_DECAY_PER_MONTH = 0.001
TEMPERAMENT_RECOVERY_PER_MONTH = 0.01


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


# ── T3 Tensor ────────────────────────────────────────────────────

@dataclass
class T3:
    """Trust tensor: Talent / Training / Temperament."""

    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    def __post_init__(self):
        self.talent = _clamp(self.talent)
        self.training = _clamp(self.training)
        self.temperament = _clamp(self.temperament)

    @property
    def composite(self) -> float:
        """Weighted composite score (canonical weights)."""
        return (
            self.talent * T3_WEIGHTS["talent"]
            + self.training * T3_WEIGHTS["training"]
            + self.temperament * T3_WEIGHTS["temperament"]
        )

    def update(self, quality: float, success: bool = True) -> T3:
        """
        Update from an action outcome.

        Per spec: base_delta = T3_UPDATE_RATE * (quality - 0.5)
        Each dimension gets base_delta * its factor.
        Returns a NEW T3 (immutable pattern).
        """
        base_delta = T3_UPDATE_RATE * (quality - 0.5)
        return T3(
            talent=_clamp(self.talent + base_delta * T3_UPDATE_FACTORS["talent"]),
            training=_clamp(self.training + base_delta * T3_UPDATE_FACTORS["training"]),
            temperament=_clamp(self.temperament + base_delta * T3_UPDATE_FACTORS["temperament"]),
        )

    def evolve(self, outcome: ActionOutcome) -> T3:
        """Apply outcome-based deltas per spec §2.3 table. Returns a NEW T3."""
        deltas = OUTCOME_DELTAS[outcome]
        return T3(
            talent=_clamp(self.talent + deltas["talent"]),
            training=_clamp(self.training + deltas["training"]),
            temperament=_clamp(self.temperament + deltas["temperament"]),
        )

    def decay(self, months: float) -> T3:
        """Apply time-based decay/refresh per spec §2.3.

        - Training decays at TRAINING_DECAY_PER_MONTH without practice
        - Temperament recovers at TEMPERAMENT_RECOVERY_PER_MONTH with good behavior
        - Talent is stable (no decay)
        """
        return T3(
            talent=self.talent,
            training=_clamp(self.training - TRAINING_DECAY_PER_MONTH * months),
            temperament=_clamp(self.temperament + TEMPERAMENT_RECOVERY_PER_MONTH * months),
        )

    def as_dict(self) -> Dict[str, float]:
        return {"talent": self.talent, "training": self.training, "temperament": self.temperament}

    def to_jsonld(self, entity: Optional[str] = None, role: Optional[str] = None) -> Dict[str, Any]:
        """Serialize to JSON-LD per t3v3-ontology.ttl.

        Produces both shorthand properties (web4:talent etc.) and
        structured dimension_scores array (web4:hasDimensionScore form).
        The shorthand carries aggregate scores; the array enables
        sub-dimension extensions by other ontologies.

        Args:
            entity: Optional LCT entity ID (web4:entity binding)
            role: Optional role context (web4:role binding)
        """
        doc: Dict[str, Any] = {
            "@context": [T3_JSONLD_CONTEXT],
            "@type": "T3Tensor",
            # Shorthand aggregate scores (ontology §backward-compatible)
            "talent": self.talent,
            "training": self.training,
            "temperament": self.temperament,
            "composite_score": self.composite,
            # Structured dimension scores (ontology §DimensionScore)
            "dimension_scores": [
                {"dimension": "web4:Talent", "score": self.talent},
                {"dimension": "web4:Training", "score": self.training},
                {"dimension": "web4:Temperament", "score": self.temperament},
            ],
        }
        if entity is not None:
            doc["entity"] = entity
        if role is not None:
            doc["role"] = role
        return doc

    def to_jsonld_string(self, indent: int = 2, **kwargs: Any) -> str:
        """Serialize to JSON-LD string."""
        return json.dumps(self.to_jsonld(**kwargs), indent=indent)

    @classmethod
    def from_jsonld(cls, doc: Dict[str, Any]) -> T3:
        """Deserialize from JSON-LD document.

        Accepts both JSON-LD format (with @context/@type) and plain dict
        format (from as_dict). composite_score is recomputed, not stored.
        """
        talent = doc.get("talent", 0.5)
        training = doc.get("training", 0.5)
        temperament = doc.get("temperament", 0.5)
        return cls(talent=talent, training=training, temperament=temperament)

    @classmethod
    def from_jsonld_string(cls, s: str) -> T3:
        """Deserialize from JSON-LD string."""
        return cls.from_jsonld(json.loads(s))


# ── V3 Tensor ────────────────────────────────────────────────────

@dataclass
class V3:
    """Value tensor: Valuation / Veracity / Validity."""

    valuation: float = 0.5
    veracity: float = 0.5
    validity: float = 0.5

    def __post_init__(self):
        self.valuation = _clamp(self.valuation)
        self.veracity = _clamp(self.veracity)
        self.validity = _clamp(self.validity)

    @property
    def composite(self) -> float:
        """Weighted composite score (canonical weights)."""
        return (
            self.valuation * V3_WEIGHTS["valuation"]
            + self.veracity * V3_WEIGHTS["veracity"]
            + self.validity * V3_WEIGHTS["validity"]
        )

    @classmethod
    def calculate(
        cls,
        atp_earned: float,
        atp_expected: float,
        recipient_satisfaction: float,
        verified_claims: int,
        total_claims: int,
        witness_confidence: float,
        value_transferred: bool,
    ) -> V3:
        """Compute V3 from R6 action components per spec §3.3.

        Args:
            atp_earned: ATP actually earned from the action
            atp_expected: ATP expected for this action type
            recipient_satisfaction: 0-1 satisfaction score from recipient
            verified_claims: number of claims independently verified
            total_claims: total claims made
            witness_confidence: 0-1 aggregate witness confidence
            value_transferred: whether value was actually delivered
        """
        valuation = (atp_earned / atp_expected * recipient_satisfaction) if atp_expected > 0 else 0.0
        veracity = (verified_claims / total_claims * witness_confidence) if total_claims > 0 else 0.0
        validity = 1.0 if value_transferred else 0.0
        return cls(
            valuation=_clamp(valuation),
            veracity=_clamp(veracity),
            validity=validity,
        )

    def as_dict(self) -> Dict[str, float]:
        return {"valuation": self.valuation, "veracity": self.veracity, "validity": self.validity}

    def to_jsonld(self, entity: Optional[str] = None, role: Optional[str] = None) -> Dict[str, Any]:
        """Serialize to JSON-LD per t3v3-ontology.ttl.

        Produces both shorthand properties (web4:valuation etc.) and
        structured dimension_scores array (web4:hasDimensionScore form).

        Args:
            entity: Optional LCT entity ID (web4:entity binding)
            role: Optional role context (web4:role binding)
        """
        doc: Dict[str, Any] = {
            "@context": [V3_JSONLD_CONTEXT],
            "@type": "V3Tensor",
            # Shorthand aggregate scores (ontology §backward-compatible)
            "valuation": self.valuation,
            "veracity": self.veracity,
            "validity": self.validity,
            "composite_score": self.composite,
            # Structured dimension scores (ontology §DimensionScore)
            "dimension_scores": [
                {"dimension": "web4:Valuation", "score": self.valuation},
                {"dimension": "web4:Veracity", "score": self.veracity},
                {"dimension": "web4:Validity", "score": self.validity},
            ],
        }
        if entity is not None:
            doc["entity"] = entity
        if role is not None:
            doc["role"] = role
        return doc

    def to_jsonld_string(self, indent: int = 2, **kwargs: Any) -> str:
        """Serialize to JSON-LD string."""
        return json.dumps(self.to_jsonld(**kwargs), indent=indent)

    @classmethod
    def from_jsonld(cls, doc: Dict[str, Any]) -> V3:
        """Deserialize from JSON-LD document.

        Accepts both JSON-LD format (with @context/@type) and plain dict
        format (from as_dict). composite_score is recomputed, not stored.
        """
        valuation = doc.get("valuation", 0.5)
        veracity = doc.get("veracity", 0.5)
        validity = doc.get("validity", 0.5)
        return cls(valuation=valuation, veracity=veracity, validity=validity)

    @classmethod
    def from_jsonld_string(cls, s: str) -> V3:
        """Deserialize from JSON-LD string."""
        return cls.from_jsonld(json.loads(s))


# ── Role-Contextual Tensor Store ─────────────────────────────────

@dataclass
class RoleTensors:
    """T3/V3 pair for a specific role context."""

    role: str
    t3: T3 = field(default_factory=T3)
    v3: V3 = field(default_factory=V3)


class TrustProfile:
    """
    An entity's complete trust profile — T3/V3 tensors per role.

    Usage:
        profile = TrustProfile("lct:alice")
        profile.set_role("web4:DataAnalyst", T3(0.85, 0.90, 0.95))
        score = profile.get_t3("web4:DataAnalyst").composite
    """

    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        self._roles: Dict[str, RoleTensors] = {}

    def set_role(self, role: str, t3: Optional[T3] = None, v3: Optional[V3] = None):
        """Set tensors for a role."""
        rt = self._roles.get(role, RoleTensors(role=role))
        if t3 is not None:
            rt.t3 = t3
        if v3 is not None:
            rt.v3 = v3
        self._roles[role] = rt

    def get_t3(self, role: str) -> T3:
        """Get T3 for role. Returns default (0.5, 0.5, 0.5) if role not found."""
        rt = self._roles.get(role)
        return rt.t3 if rt else T3()

    def get_v3(self, role: str) -> V3:
        """Get V3 for role. Returns default (0.5, 0.5, 0.5) if role not found."""
        rt = self._roles.get(role)
        return rt.v3 if rt else V3()

    @property
    def roles(self) -> list[str]:
        return list(self._roles.keys())


# ── Role Requirements (spec §5.1) ────────────────────────────────

@dataclass
class RoleRequirement:
    """Minimum T3 thresholds for a role per spec §5.1."""
    role: str
    min_talent: float = 0.0
    min_training: float = 0.0
    min_temperament: float = 0.0

    def is_qualified(self, t3: T3) -> bool:
        """Check if a T3 tensor meets all minimum thresholds."""
        return (
            t3.talent >= self.min_talent
            and t3.training >= self.min_training
            and t3.temperament >= self.min_temperament
        )

    def evaluate(self, t3: T3) -> Dict[str, object]:
        """Evaluate a candidate against this role's requirements."""
        qualified = self.is_qualified(t3)
        return {
            "role": self.role,
            "qualified": qualified,
            "trust_score": t3.composite if qualified else 0.0,
            "gaps": {
                "talent": max(0.0, self.min_talent - t3.talent),
                "training": max(0.0, self.min_training - t3.training),
                "temperament": max(0.0, self.min_temperament - t3.temperament),
            },
        }


# ── Team Tensor Composition (spec §8.2) ──────────────────────────

def compute_team_t3(
    profiles: List[TrustProfile],
    role: str,
    weights: Optional[Dict[str, float]] = None,
) -> Optional[T3]:
    """Compute team T3 for a role as weighted average of qualified members.

    Per spec §8.2: only members with the role contribute. Cannot average
    trust across different roles. Returns None if no members have the role.

    Args:
        profiles: list of TrustProfile objects (team members)
        role: the role to compute team trust for
        weights: optional per-entity_id weights (defaults to equal weight)
    """
    qualified = [(p, p.get_t3(role)) for p in profiles if role in p.roles]
    if not qualified:
        return None

    if weights:
        total_w = sum(weights.get(p.entity_id, 1.0) for p, _ in qualified)
        if total_w == 0:
            return None
        talent = sum(t.talent * weights.get(p.entity_id, 1.0) for p, t in qualified) / total_w
        training = sum(t.training * weights.get(p.entity_id, 1.0) for p, t in qualified) / total_w
        temperament = sum(t.temperament * weights.get(p.entity_id, 1.0) for p, t in qualified) / total_w
    else:
        n = len(qualified)
        talent = sum(t.talent for _, t in qualified) / n
        training = sum(t.training for _, t in qualified) / n
        temperament = sum(t.temperament for _, t in qualified) / n

    return T3(talent=talent, training=training, temperament=temperament)


# ── Trust Operations ─────────────────────────────────────────────

def trust_bridge(
    competence: float,
    reliability: float,
    consistency: float,
    alignment: float,
    witnesses: float,
    lineage: float,
) -> T3:
    """
    Map 6-dimensional trust to T3 (test vector t3v3-008).

    Primary mapping:
      competence → talent, reliability → training, consistency → temperament
    Secondary dimensions (alignment, witnesses, lineage) contribute
    BRIDGE_SECONDARY_WEIGHT_EACH to each.
    """
    secondary_sum = alignment + witnesses + lineage
    sw = (1.0 - BRIDGE_PRIMARY_WEIGHT) / 3  # 0.4/3 ≈ 0.1333

    return T3(
        talent=_clamp(BRIDGE_PRIMARY_WEIGHT * competence + sw * secondary_sum),
        training=_clamp(BRIDGE_PRIMARY_WEIGHT * reliability + sw * secondary_sum),
        temperament=_clamp(BRIDGE_PRIMARY_WEIGHT * consistency + sw * secondary_sum),
    )


def mrh_trust_decay(base_trust: float, hops: int, decay_factor: float = 0.7) -> float:
    """
    Trust decay per MRH hop (test vector t3v3-009).

    5+ hops = BEYOND zone = zero trust.
    """
    if hops > MRH_MAX_HOPS:
        return 0.0
    return base_trust * (decay_factor ** hops)


def mrh_zone(hops: int) -> str:
    """MRH zone classification per hop count."""
    if hops == 0:
        return "SELF"
    elif hops == 1:
        return "DIRECT"
    elif hops == 2:
        return "INDIRECT"
    elif hops <= MRH_MAX_HOPS:
        return "PERIPHERAL"
    else:
        return "BEYOND"


def operational_health(t3_composite: float, v3_composite: float, energy_ratio: float) -> float:
    """
    Operational health score (test vector t3v3-010).

    Returns weighted combination of T3 composite, V3 composite, and ATP energy ratio.
    This measures an entity's operational readiness — distinct from the whitepaper's
    "identity coherence" (C×S×Phi×R) which measures pattern stability, self-reference,
    integration, and role consistency.
    """
    return (
        t3_composite * HEALTH_WEIGHTS["t3"]
        + v3_composite * HEALTH_WEIGHTS["v3"]
        + energy_ratio * HEALTH_WEIGHTS["energy"]
    )


def is_healthy(t3_composite: float, v3_composite: float, energy_ratio: float) -> bool:
    """Check if entity meets operational health threshold."""
    return operational_health(t3_composite, v3_composite, energy_ratio) >= HEALTH_THRESHOLD


def diminishing_returns(repeat_count: int, base_factor: float = DIMINISHING_BASE) -> float:
    """
    Diminishing returns factor for repeated actions (test vector t3v3-007).

    factor = max(base_factor^(n-1), floor)
    n is 1-indexed.
    """
    if repeat_count <= 0:
        return 1.0
    raw = base_factor ** (repeat_count - 1)
    return max(raw, DIMINISHING_FLOOR)
