#!/usr/bin/env python3
"""
T3 Trust Tensor and V3 Value Tensor Implementation

Implements the canonical T3/V3 tensors as defined in the Web4 ontology
(web4-standard/ontology/t3v3-ontology.ttl) and CANONICAL_TERMS_v1.md.

T3 Trust Tensor — 3 root dimensions, fractally extensible:
  1. talent      — Natural aptitude / capability for a specific role
  2. training    — Learned skills, certifications, experience
  3. temperament — Behavioral consistency, reliability, ethical disposition

V3 Value Tensor — 3 root dimensions, fractally extensible:
  1. valuation   — Subjective worth as perceived by recipients
  2. veracity    — Truthfulness, accuracy of claims
  3. validity    — Soundness of reasoning, confirmed value delivery

Each root dimension is a node in an open-ended RDF sub-graph. Domain-specific
sub-dimensions refine roots via web4:subDimensionOf. The root score is the
aggregate of its sub-graph. See t3v3-ontology.ttl for the formal ontology.

Key Concepts:
- Tensors are ROLE-CONTEXTUAL (trust as surgeon ≠ trust as mechanic)
- Updates occur through R6 action outcomes
- Coherence Index (CI) modulates trust application
- Economic incentives (ATP costs) derive from tensor values
- Sub-dimensions allow domain-specific refinement without modifying core
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import hashlib


# ============================================================================
# T3 Trust Tensor
# ============================================================================

@dataclass
class T3Tensor:
    """
    Trust Tensor with 3 canonical root dimensions.

    Each root is an aggregate of an open-ended sub-dimension graph.
    All root values are [0.0, 1.0] representing trust level.
    """
    talent: float = 0.5       # Natural capability for role
    training: float = 0.5     # Learned skills and experience
    temperament: float = 0.5  # Behavioral consistency and reliability

    # Open-ended sub-dimensions grouped by root
    # e.g. {"talent": {"statistical_modeling": 0.9, "data_viz": 0.7}}
    sub_dimensions: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def __post_init__(self):
        """Validate root dimensions in [0, 1]"""
        for dim in self.root_dimensions():
            value = getattr(self, dim)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{dim} must be in [0.0, 1.0], got {value}")

    @staticmethod
    def root_dimensions() -> List[str]:
        """Get list of root dimension names"""
        return ['talent', 'training', 'temperament']

    def as_vector(self) -> List[float]:
        """Convert root dimensions to 3D vector"""
        return [getattr(self, dim) for dim in self.root_dimensions()]

    @classmethod
    def from_vector(cls, vec: List[float]) -> 'T3Tensor':
        """Create from 3D vector"""
        if len(vec) != 3:
            raise ValueError(f"Expected 3 dimensions, got {len(vec)}")
        return cls(**dict(zip(cls.root_dimensions(), vec)))

    def magnitude(self) -> float:
        """Euclidean magnitude (overall trust level)"""
        return math.sqrt(sum(v**2 for v in self.as_vector())) / math.sqrt(3)

    def weighted_score(self, weights: Optional[Dict[str, float]] = None) -> float:
        """
        Compute weighted trust score from root dimensions.

        Default weights from t3-v3-tensors.md spec.
        """
        if weights is None:
            weights = {
                'talent': 0.40,
                'training': 0.30,
                'temperament': 0.30,
            }

        total = sum(getattr(self, dim) * weights.get(dim, 0)
                   for dim in self.root_dimensions())
        return total

    def distance(self, other: 'T3Tensor') -> float:
        """Euclidean distance to another tensor (root dimensions only)"""
        v1 = self.as_vector()
        v2 = other.as_vector()
        return math.sqrt(sum((a - b)**2 for a, b in zip(v1, v2)))

    def meets_threshold(self, threshold: 'T3Tensor') -> Tuple[bool, List[str]]:
        """
        Check if this tensor meets minimum threshold requirements.

        Returns: (meets_all, list_of_failing_dimensions)
        """
        failing = []
        for dim in self.root_dimensions():
            if getattr(self, dim) < getattr(threshold, dim):
                failing.append(dim)
        return (len(failing) == 0, failing)

    def aggregate_from_sub_dimensions(self, root_dim: str) -> Optional[float]:
        """Recompute root score as mean of its sub-dimension scores."""
        subs = self.sub_dimensions.get(root_dim, {})
        if not subs:
            return None
        return sum(subs.values()) / len(subs)

    def recompute_roots(self):
        """Recompute all root scores from sub-dimensions (where available)."""
        for dim in self.root_dimensions():
            agg = self.aggregate_from_sub_dimensions(dim)
            if agg is not None:
                setattr(self, dim, max(0.0, min(1.0, agg)))

    def to_dict(self) -> dict:
        d = {dim: getattr(self, dim) for dim in self.root_dimensions()}
        if self.sub_dimensions:
            d['sub_dimensions'] = self.sub_dimensions
        return d

    @classmethod
    def from_dict(cls, data: dict) -> 'T3Tensor':
        roots = {k: v for k, v in data.items() if k in cls.root_dimensions()}
        sub = data.get('sub_dimensions', {})
        return cls(**roots, sub_dimensions=sub)

    # Backward compatibility: map old 6D names to canonical structure
    @classmethod
    def from_legacy_6d(cls, competence=0.5, reliability=0.5, consistency=0.5,
                       witnesses=0.5, lineage=0.5, alignment=0.5) -> 'T3Tensor':
        """
        Create from legacy 6D dimension names.

        Mapping:
          talent     ← competence (capability)
          training   ← average(lineage) (track record → experience proxy)
          temperament ← average(reliability, consistency, alignment)

        witnesses is metadata, not a trust dimension — ignored in root scores.
        """
        return cls(
            talent=competence,
            training=lineage,
            temperament=(reliability + consistency + alignment) / 3.0,
            sub_dimensions={
                'temperament': {
                    'reliability': reliability,
                    'consistency': consistency,
                    'alignment': alignment,
                }
            }
        )


# ============================================================================
# V3 Value Tensor
# ============================================================================

@dataclass
class V3Tensor:
    """
    Value Tensor with 3 canonical root dimensions.

    Valuation may exceed 1.0 for exceptional value creation.
    Veracity and validity are [0.0, 1.0].
    """
    valuation: float = 0.5    # Subjective worth as perceived by recipients
    veracity: float = 0.5     # Truthfulness and accuracy of claims
    validity: float = 0.5     # Soundness of reasoning, confirmed delivery

    # Open-ended sub-dimensions
    sub_dimensions: Dict[str, Dict[str, float]] = field(default_factory=dict)

    @staticmethod
    def root_dimensions() -> List[str]:
        return ['valuation', 'veracity', 'validity']

    def as_vector(self) -> List[float]:
        return [getattr(self, dim) for dim in self.root_dimensions()]

    @classmethod
    def from_vector(cls, vec: List[float]) -> 'V3Tensor':
        if len(vec) != 3:
            raise ValueError(f"Expected 3 dimensions, got {len(vec)}")
        return cls(**dict(zip(cls.root_dimensions(), vec)))

    def total_value(self) -> float:
        """Sum of root value dimensions"""
        return sum(self.as_vector())

    def weighted_value(self, weights: Optional[Dict[str, float]] = None) -> float:
        """Compute weighted value score"""
        if weights is None:
            weights = {
                'valuation': 0.40,
                'veracity': 0.35,
                'validity': 0.25,
            }
        return sum(getattr(self, dim) * weights.get(dim, 0)
                  for dim in self.root_dimensions())

    def to_dict(self) -> dict:
        d = {dim: getattr(self, dim) for dim in self.root_dimensions()}
        if self.sub_dimensions:
            d['sub_dimensions'] = self.sub_dimensions
        return d

    @classmethod
    def from_dict(cls, data: dict) -> 'V3Tensor':
        roots = {k: v for k, v in data.items() if k in cls.root_dimensions()}
        sub = data.get('sub_dimensions', {})
        return cls(**roots, sub_dimensions=sub)

    @classmethod
    def from_legacy_6d(cls, energy=0.5, contribution=0.5, stewardship=0.5,
                       network=0.5, reputation=0.5, temporal=0.5) -> 'V3Tensor':
        """
        Create from legacy 6D dimension names.

        Mapping:
          valuation ← contribution (tangible output = perceived value)
          veracity  ← reputation (external recognition → validation proxy)
          validity  ← stewardship (responsible delivery → confirmed value)

        energy is ATP metadata; network and temporal become sub-dimensions.
        """
        return cls(
            valuation=contribution,
            veracity=reputation,
            validity=stewardship,
            sub_dimensions={
                'valuation': {
                    'network_effects': network,
                    'energy_invested': energy,
                },
                'validity': {
                    'temporal_persistence': temporal,
                }
            }
        )


# ============================================================================
# Tensor Updates from R6 Actions
# ============================================================================

class ActionOutcome(Enum):
    """Outcome categories for R6 actions"""
    NOVEL_SUCCESS = "novel_success"
    STANDARD_SUCCESS = "standard_success"
    EXPECTED_FAILURE = "expected_failure"
    UNEXPECTED_FAILURE = "unexpected_failure"
    ETHICS_VIOLATION = "ethics_violation"


@dataclass
class T3UpdateDelta:
    """Delta values for T3 updates based on action outcomes"""
    talent: float = 0.0
    training: float = 0.0
    temperament: float = 0.0


# Standard update deltas per outcome type
# Aligned with t3-v3-tensors.md Section 2.3
T3_UPDATE_TABLE: Dict[ActionOutcome, T3UpdateDelta] = {
    ActionOutcome.NOVEL_SUCCESS: T3UpdateDelta(
        talent=0.03,       # Novel solutions demonstrate aptitude
        training=0.02,     # Experience gained
        temperament=0.01,  # Consistent positive behavior
    ),
    ActionOutcome.STANDARD_SUCCESS: T3UpdateDelta(
        talent=0.0,        # Expected performance, no talent signal
        training=0.01,     # Practice builds skill
        temperament=0.005, # Reliable execution
    ),
    ActionOutcome.EXPECTED_FAILURE: T3UpdateDelta(
        talent=-0.01,      # Slight capability concern
        training=0.0,      # Reasonable attempt, no skill loss
        temperament=0.0,   # Expected failures don't affect temperament
    ),
    ActionOutcome.UNEXPECTED_FAILURE: T3UpdateDelta(
        talent=-0.02,      # Capability shortfall
        training=-0.01,    # Knowledge gap revealed
        temperament=-0.02, # Reliability concern
    ),
    ActionOutcome.ETHICS_VIOLATION: T3UpdateDelta(
        talent=-0.05,      # Misapplied capability
        training=0.0,      # Knowledge intact
        temperament=-0.10, # Severe behavioral concern
    )
}


def update_t3(
    current: T3Tensor,
    outcome: ActionOutcome,
    witness_attestations: int = 0,
    ci_multiplier: float = 1.0
) -> T3Tensor:
    """
    Update T3 tensor based on action outcome.

    Args:
        current: Current T3 tensor
        outcome: Action outcome category
        witness_attestations: Number of witness attestations received
        ci_multiplier: Coherence Index to modulate update magnitude

    Returns:
        Updated T3 tensor (sub_dimensions preserved unchanged)
    """
    delta = T3_UPDATE_TABLE[outcome]

    # Apply CI multiplier (low coherence reduces positive updates, amplifies negative)
    def apply_ci(base: float) -> float:
        if base >= 0:
            return base * ci_multiplier
        else:
            return base * (2.0 - ci_multiplier)

    # Witness attestations boost temperament (reliable entities get witnessed more)
    witness_bonus = min(witness_attestations * 0.01, 0.05)

    new_values = {}
    for dim in T3Tensor.root_dimensions():
        current_val = getattr(current, dim)
        delta_val = getattr(delta, dim)
        adjusted_delta = apply_ci(delta_val)

        if dim == 'temperament':
            adjusted_delta += witness_bonus

        new_val = max(0.0, min(1.0, current_val + adjusted_delta))
        new_values[dim] = round(new_val, 4)

    return T3Tensor(sub_dimensions=current.sub_dimensions, **new_values)


def update_v3(
    current: V3Tensor,
    atp_spent: float,
    atp_earned: float,
    contribution_quality: float,
    witness_count: int = 0
) -> V3Tensor:
    """
    Update V3 tensor based on value creation.

    Args:
        current: Current V3 tensor
        atp_spent: ATP resources consumed
        atp_earned: ATP value generated
        contribution_quality: Quality score [0, 1] from recipients
        witness_count: Number of witnesses to the value transfer
    """
    # Valuation: based on perceived value generated
    if atp_spent > 0:
        value_ratio = atp_earned / atp_spent
        valuation_delta = (value_ratio - 1.0) * 0.02 * contribution_quality
    else:
        valuation_delta = 0.0

    # Veracity: quality and witness attestation drive accuracy perception
    veracity_delta = (contribution_quality - 0.5) * 0.02
    veracity_delta += min(witness_count * 0.005, 0.02)

    # Validity: efficiency of actual value delivery
    if atp_spent > 0:
        efficiency = min(atp_earned / atp_spent, 2.0) / 2.0
        validity_delta = (efficiency - 0.5) * 0.02
    else:
        validity_delta = 0.0

    new_values = {
        'valuation': max(0, min(1.5, current.valuation + valuation_delta)),
        'veracity': max(0, min(1.0, current.veracity + veracity_delta)),
        'validity': max(0, min(1.0, current.validity + validity_delta)),
    }

    return V3Tensor(
        sub_dimensions=current.sub_dimensions,
        **{k: round(v, 4) for k, v in new_values.items()}
    )


# ============================================================================
# Role-Contextual Tensor Storage
# ============================================================================

@dataclass
class RoleTensorPair:
    """T3/V3 tensors bound to a specific role"""
    role: str
    t3: T3Tensor
    v3: V3Tensor
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    action_count: int = 0


class EntityTensorStore:
    """
    Manages role-contextual T3/V3 tensors for an entity.

    Key principle: Trust is NEVER global. Each role has separate tensors.
    """

    def __init__(self, entity_lct: str):
        self.entity_lct = entity_lct
        self.role_tensors: Dict[str, RoleTensorPair] = {}
        self.history: List[dict] = []

    def get_or_create(self, role: str) -> RoleTensorPair:
        """Get tensors for role, creating if needed"""
        if role not in self.role_tensors:
            self.role_tensors[role] = RoleTensorPair(
                role=role,
                t3=T3Tensor(talent=0.3, training=0.3, temperament=0.5),
                v3=V3Tensor(valuation=0.3, veracity=0.3, validity=0.5),
            )
        return self.role_tensors[role]

    def update_from_action(
        self,
        role: str,
        outcome: ActionOutcome,
        atp_spent: float,
        atp_earned: float,
        contribution_quality: float,
        witness_count: int = 0,
        ci_multiplier: float = 1.0
    ) -> RoleTensorPair:
        """Update tensors for a role based on R6 action outcome"""
        pair = self.get_or_create(role)

        new_t3 = update_t3(pair.t3, outcome, witness_count, ci_multiplier)
        new_v3 = update_v3(pair.v3, atp_spent, atp_earned,
                          contribution_quality, witness_count)

        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'role': role,
            'outcome': outcome.value,
            't3_before': pair.t3.to_dict(),
            't3_after': new_t3.to_dict(),
            'v3_before': pair.v3.to_dict(),
            'v3_after': new_v3.to_dict()
        })

        pair.t3 = new_t3
        pair.v3 = new_v3
        pair.last_updated = datetime.now().isoformat()
        pair.action_count += 1

        return pair

    def compute_atp_cost(
        self,
        role: str,
        base_cost: float,
        ci: float = 1.0
    ) -> float:
        """
        Compute ATP cost for an action based on trust tensors.

        Lower trust = higher cost (risk premium).
        Lower CI = higher cost (coherence penalty).
        """
        pair = self.get_or_create(role)

        trust_score = pair.t3.weighted_score()
        trust_multiplier = 2.0 - trust_score

        ci_multiplier = 1.0 / (ci ** 2)
        ci_multiplier = min(ci_multiplier, 10.0)

        return base_cost * trust_multiplier * ci_multiplier

    def to_dict(self) -> dict:
        return {
            'entity_lct': self.entity_lct,
            'roles': {
                role: {
                    't3': pair.t3.to_dict(),
                    'v3': pair.v3.to_dict(),
                    'created_at': pair.created_at,
                    'last_updated': pair.last_updated,
                    'action_count': pair.action_count
                }
                for role, pair in self.role_tensors.items()
            }
        }


# ============================================================================
# Tensor Decay
# ============================================================================

def apply_decay(tensor_store: EntityTensorStore, days_elapsed: int = 30) -> None:
    """
    Apply time-based decay to T3 tensors.

    Per t3-v3-tensors.md Section 2.3:
    - talent: No decay (represents inherent capability)
    - training: -0.001 per month without practice
    - temperament: +0.01 per month recovery toward baseline
    """
    decay_rates = {
        'talent': 0.0,        # Stable
        'training': 0.001,    # Slow skill decay
        'temperament': -0.01, # Negative = recovery toward baseline
    }

    for role, pair in tensor_store.role_tensors.items():
        new_values = {}
        for dim in T3Tensor.root_dimensions():
            current = getattr(pair.t3, dim)
            rate = decay_rates[dim] * (days_elapsed / 30)
            new_val = max(0.1, min(1.0, current - rate))
            new_values[dim] = round(new_val, 4)

        pair.t3 = T3Tensor(sub_dimensions=pair.t3.sub_dimensions, **new_values)


# ============================================================================
# Demo
# ============================================================================

def demo_trust_tensors():
    """Demonstrate trust tensor functionality"""

    print("=" * 60)
    print("T3/V3 TRUST TENSOR DEMO (Canonical 3D + Sub-Dimensions)")
    print("=" * 60)

    # Create entity tensor store
    store = EntityTensorStore("lct:demo-entity")

    print("\n1. Initial State (New Entity)")
    print("-" * 40)
    pair = store.get_or_create("web4:DataAnalyst")
    print(f"  Role: web4:DataAnalyst")
    print(f"  T3: {pair.t3.to_dict()}")
    print(f"  T3 weighted score: {pair.t3.weighted_score():.3f}")
    print(f"  V3: {pair.v3.to_dict()}")

    print("\n2. After Novel Success")
    print("-" * 40)
    pair = store.update_from_action(
        role="web4:DataAnalyst",
        outcome=ActionOutcome.NOVEL_SUCCESS,
        atp_spent=10,
        atp_earned=15,
        contribution_quality=0.9,
        witness_count=2,
        ci_multiplier=0.95
    )
    print(f"  T3: {pair.t3.to_dict()}")
    print(f"  T3 weighted score: {pair.t3.weighted_score():.3f}")
    print(f"  V3: {pair.v3.to_dict()}")

    print("\n3. After Multiple Standard Successes")
    print("-" * 40)
    for i in range(5):
        pair = store.update_from_action(
            role="web4:DataAnalyst",
            outcome=ActionOutcome.STANDARD_SUCCESS,
            atp_spent=5,
            atp_earned=6,
            contribution_quality=0.8,
            witness_count=1
        )
    print(f"  T3: {pair.t3.to_dict()}")
    print(f"  T3 weighted score: {pair.t3.weighted_score():.3f}")
    print(f"  Action count: {pair.action_count}")

    print("\n4. ATP Cost Calculation")
    print("-" * 40)
    base_cost = 10
    costs = [
        (1.0, store.compute_atp_cost("web4:DataAnalyst", base_cost, ci=1.0)),
        (0.8, store.compute_atp_cost("web4:DataAnalyst", base_cost, ci=0.8)),
        (0.5, store.compute_atp_cost("web4:DataAnalyst", base_cost, ci=0.5)),
    ]
    for ci, cost in costs:
        print(f"  CI={ci}: {cost:.2f} ATP (base: {base_cost})")

    print("\n5. Role Isolation")
    print("-" * 40)
    mechanic_pair = store.get_or_create("web4:Mechanic")
    print(f"  DataAnalyst T3 score: {pair.t3.weighted_score():.3f}")
    print(f"  Mechanic T3 score: {mechanic_pair.t3.weighted_score():.3f}")
    print("  (New role starts with minimal trust)")

    print("\n6. Threshold Checking")
    print("-" * 40)
    threshold = T3Tensor(talent=0.4, training=0.4, temperament=0.4)
    meets, failing = pair.t3.meets_threshold(threshold)
    print(f"  Threshold: {threshold.to_dict()}")
    print(f"  Meets threshold: {meets}")
    if failing:
        print(f"  Failing dimensions: {failing}")

    print("\n7. Sub-Dimensions")
    print("-" * 40)
    t3_with_subs = T3Tensor(
        talent=0.85,
        training=0.90,
        temperament=0.78,
        sub_dimensions={
            'talent': {
                'statistical_modeling': 0.92,
                'data_visualization': 0.78,
            },
            'training': {
                'python_proficiency': 0.95,
                'sql_expertise': 0.85,
            }
        }
    )
    print(f"  T3 with sub-dims: {t3_with_subs.to_dict()}")
    print(f"  Talent aggregate from subs: {t3_with_subs.aggregate_from_sub_dimensions('talent'):.3f}")
    print(f"  Training aggregate from subs: {t3_with_subs.aggregate_from_sub_dimensions('training'):.3f}")

    print("\n8. Legacy 6D Migration")
    print("-" * 40)
    legacy = T3Tensor.from_legacy_6d(
        competence=0.8, reliability=0.7, consistency=0.9,
        witnesses=0.6, lineage=0.5, alignment=0.85
    )
    print(f"  Legacy 6D → Canonical: {legacy.to_dict()}")
    print(f"  (witnesses=0.6 absorbed as metadata, not a dimension)")

    print("\n" + "=" * 60)
    print("Trust Tensor Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo_trust_tensors()
