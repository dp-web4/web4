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

from dataclasses import dataclass, field
from typing import Dict, Optional

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

    def as_dict(self) -> Dict[str, float]:
        return {"talent": self.talent, "training": self.training, "temperament": self.temperament}


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

    def as_dict(self) -> Dict[str, float]:
        return {"valuation": self.valuation, "veracity": self.veracity, "validity": self.validity}


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
