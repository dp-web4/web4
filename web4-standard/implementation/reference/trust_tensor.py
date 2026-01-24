#!/usr/bin/env python3
"""
T3 Trust Tensor and V3 Value Tensor Implementation

Implements the canonical 6-dimension trust and value tensors as defined in
WEB4_CANONICAL_TERMINOLOGY.md. These tensors provide multi-dimensional
assessment of entity trustworthiness and value creation.

NOTE: The current t3-v3-tensors.md spec uses 3 dimensions (Talent/Training/Temperament).
This implementation follows the canonical 6 dimensions. A reconciliation is needed
in the spec documentation.

T3 Trust Tensor (6 dimensions):
1. competence  - Technical capability to perform role
2. reliability - Consistent delivery on commitments
3. consistency - Predictable behavior patterns
4. witnesses   - Corroboration from trusted third parties
5. lineage     - Historical track record
6. alignment   - Goal/value alignment with relying party

V3 Value Tensor (6 dimensions):
1. energy      - Resources invested/mobilized
2. contribution - Tangible output delivered
3. stewardship - Responsible resource management
4. network     - Relationship capital created
5. reputation  - External recognition earned
6. temporal    - Value persistence over time

Key Concepts:
- Tensors are ROLE-CONTEXTUAL (trust as surgeon ≠ trust as mechanic)
- Updates occur through R6 action outcomes
- Coherence Index (CI) modulates trust application
- Economic incentives (ATP costs) derive from tensor values
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
    6-dimension Trust Tensor

    All values are [0.0, 1.0] representing trust level.
    """
    # Core capability dimensions
    competence: float = 0.5    # Technical capability to perform role
    reliability: float = 0.5   # Consistent delivery on commitments
    consistency: float = 0.5   # Predictable behavior patterns

    # Social/verification dimensions
    witnesses: float = 0.5     # Corroboration from trusted third parties
    lineage: float = 0.5       # Historical track record
    alignment: float = 0.5     # Goal/value alignment with relying party

    def __post_init__(self):
        """Validate all dimensions in [0, 1]"""
        for dim in self.dimensions():
            value = getattr(self, dim)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{dim} must be in [0.0, 1.0], got {value}")

    @staticmethod
    def dimensions() -> List[str]:
        """Get list of dimension names"""
        return ['competence', 'reliability', 'consistency',
                'witnesses', 'lineage', 'alignment']

    def as_vector(self) -> List[float]:
        """Convert to 6D vector"""
        return [getattr(self, dim) for dim in self.dimensions()]

    @classmethod
    def from_vector(cls, vec: List[float]) -> 'T3Tensor':
        """Create from 6D vector"""
        if len(vec) != 6:
            raise ValueError(f"Expected 6 dimensions, got {len(vec)}")
        return cls(**dict(zip(cls.dimensions(), vec)))

    def magnitude(self) -> float:
        """Euclidean magnitude (overall trust level)"""
        return math.sqrt(sum(v**2 for v in self.as_vector())) / math.sqrt(6)

    def weighted_score(self, weights: Optional[Dict[str, float]] = None) -> float:
        """
        Compute weighted trust score

        Default weights emphasize core capability (competence, reliability)
        with secondary emphasis on verification (witnesses, lineage).
        """
        if weights is None:
            weights = {
                'competence': 0.25,
                'reliability': 0.20,
                'consistency': 0.15,
                'witnesses': 0.15,
                'lineage': 0.15,
                'alignment': 0.10
            }

        total = sum(getattr(self, dim) * weights.get(dim, 0)
                   for dim in self.dimensions())
        return total

    def distance(self, other: 'T3Tensor') -> float:
        """Euclidean distance to another tensor"""
        v1 = self.as_vector()
        v2 = other.as_vector()
        return math.sqrt(sum((a - b)**2 for a, b in zip(v1, v2)))

    def meets_threshold(self, threshold: 'T3Tensor') -> Tuple[bool, List[str]]:
        """
        Check if this tensor meets minimum threshold requirements

        Returns:
            (meets_all, list_of_failing_dimensions)
        """
        failing = []
        for dim in self.dimensions():
            if getattr(self, dim) < getattr(threshold, dim):
                failing.append(dim)
        return (len(failing) == 0, failing)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'T3Tensor':
        return cls(**{k: v for k, v in data.items() if k in cls.dimensions()})


# ============================================================================
# V3 Value Tensor
# ============================================================================

@dataclass
class V3Tensor:
    """
    6-dimension Value Tensor

    Values are typically [0.0, 1.0] but some may exceed 1.0 for
    exceptional value creation.
    """
    # Resource dimensions
    energy: float = 0.5        # Resources invested/mobilized
    contribution: float = 0.5  # Tangible output delivered
    stewardship: float = 0.5   # Responsible resource management

    # Social dimensions
    network: float = 0.5       # Relationship capital created
    reputation: float = 0.5    # External recognition earned
    temporal: float = 0.5      # Value persistence over time

    @staticmethod
    def dimensions() -> List[str]:
        return ['energy', 'contribution', 'stewardship',
                'network', 'reputation', 'temporal']

    def as_vector(self) -> List[float]:
        return [getattr(self, dim) for dim in self.dimensions()]

    @classmethod
    def from_vector(cls, vec: List[float]) -> 'V3Tensor':
        if len(vec) != 6:
            raise ValueError(f"Expected 6 dimensions, got {len(vec)}")
        return cls(**dict(zip(cls.dimensions(), vec)))

    def total_value(self) -> float:
        """Sum of all value dimensions"""
        return sum(self.as_vector())

    def weighted_value(self, weights: Optional[Dict[str, float]] = None) -> float:
        """Compute weighted value score"""
        if weights is None:
            weights = {
                'contribution': 0.30,
                'stewardship': 0.20,
                'energy': 0.15,
                'network': 0.15,
                'reputation': 0.10,
                'temporal': 0.10
            }
        return sum(getattr(self, dim) * weights.get(dim, 0)
                  for dim in self.dimensions())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'V3Tensor':
        return cls(**{k: v for k, v in data.items() if k in cls.dimensions()})


# ============================================================================
# Tensor Updates from R6 Actions
# ============================================================================

class ActionOutcome(Enum):
    """Outcome categories for R6 actions"""
    NOVEL_SUCCESS = "novel_success"        # Innovative solution worked
    STANDARD_SUCCESS = "standard_success"  # Expected outcome achieved
    EXPECTED_FAILURE = "expected_failure"  # Reasonable attempt failed
    UNEXPECTED_FAILURE = "unexpected_failure"  # Should have worked, didn't
    ETHICS_VIOLATION = "ethics_violation"  # Violated behavioral norms


@dataclass
class T3UpdateDelta:
    """Delta values for T3 updates based on action outcomes"""
    competence: float = 0.0
    reliability: float = 0.0
    consistency: float = 0.0
    witnesses: float = 0.0
    lineage: float = 0.0
    alignment: float = 0.0


# Standard update deltas per outcome type
T3_UPDATE_TABLE: Dict[ActionOutcome, T3UpdateDelta] = {
    ActionOutcome.NOVEL_SUCCESS: T3UpdateDelta(
        competence=0.03,
        reliability=0.02,
        consistency=0.01,
        witnesses=0.0,
        lineage=0.02,
        alignment=0.01
    ),
    ActionOutcome.STANDARD_SUCCESS: T3UpdateDelta(
        competence=0.005,
        reliability=0.01,
        consistency=0.01,
        witnesses=0.0,
        lineage=0.005,
        alignment=0.005
    ),
    ActionOutcome.EXPECTED_FAILURE: T3UpdateDelta(
        competence=-0.01,
        reliability=0.0,
        consistency=0.0,
        witnesses=0.0,
        lineage=-0.005,
        alignment=0.0
    ),
    ActionOutcome.UNEXPECTED_FAILURE: T3UpdateDelta(
        competence=-0.02,
        reliability=-0.02,
        consistency=-0.01,
        witnesses=0.0,
        lineage=-0.01,
        alignment=-0.01
    ),
    ActionOutcome.ETHICS_VIOLATION: T3UpdateDelta(
        competence=-0.05,
        reliability=-0.05,
        consistency=-0.10,
        witnesses=0.0,
        lineage=-0.05,
        alignment=-0.10
    )
}


def update_t3(
    current: T3Tensor,
    outcome: ActionOutcome,
    witness_attestations: int = 0,
    ci_multiplier: float = 1.0
) -> T3Tensor:
    """
    Update T3 tensor based on action outcome

    Args:
        current: Current T3 tensor
        outcome: Action outcome category
        witness_attestations: Number of witness attestations received
        ci_multiplier: Coherence Index to modulate update magnitude

    Returns:
        Updated T3 tensor
    """
    delta = T3_UPDATE_TABLE[outcome]

    # Apply CI multiplier (low coherence reduces positive updates, amplifies negative)
    def apply_ci(base: float) -> float:
        if base >= 0:
            return base * ci_multiplier
        else:
            return base * (2.0 - ci_multiplier)  # Negative amplified when CI < 1

    # Witness bonus
    witness_bonus = min(witness_attestations * 0.01, 0.05)

    new_values = {}
    for dim in T3Tensor.dimensions():
        current_val = getattr(current, dim)
        delta_val = getattr(delta, dim)
        adjusted_delta = apply_ci(delta_val)

        # Add witness bonus to witnesses dimension
        if dim == 'witnesses':
            adjusted_delta += witness_bonus

        # Clamp to [0, 1]
        new_val = max(0.0, min(1.0, current_val + adjusted_delta))
        new_values[dim] = round(new_val, 4)

    return T3Tensor(**new_values)


def update_v3(
    current: V3Tensor,
    atp_spent: float,
    atp_earned: float,
    contribution_quality: float,
    witness_count: int = 0
) -> V3Tensor:
    """
    Update V3 tensor based on value creation

    Args:
        current: Current V3 tensor
        atp_spent: ATP resources consumed
        atp_earned: ATP value generated
        contribution_quality: Quality score [0, 1] from recipients
        witness_count: Number of witnesses to the value transfer
    """
    # Energy: based on resources mobilized
    energy_delta = min(atp_spent / 100, 0.05)

    # Contribution: based on value generated and quality
    if atp_spent > 0:
        value_ratio = atp_earned / atp_spent
        contribution_delta = (value_ratio - 1.0) * 0.02 * contribution_quality
    else:
        contribution_delta = 0.0

    # Stewardship: efficiency of resource use
    if atp_spent > 0:
        efficiency = min(atp_earned / atp_spent, 2.0) / 2.0
        stewardship_delta = (efficiency - 0.5) * 0.02
    else:
        stewardship_delta = 0.0

    # Network: witnesses create relationships
    network_delta = min(witness_count * 0.005, 0.02)

    # Reputation: quality drives reputation
    reputation_delta = (contribution_quality - 0.5) * 0.02

    # Temporal: positive outcomes increase persistence
    if atp_earned > atp_spent:
        temporal_delta = 0.01
    else:
        temporal_delta = -0.005

    new_values = {
        'energy': max(0, min(1.5, current.energy + energy_delta)),
        'contribution': max(0, min(1.5, current.contribution + contribution_delta)),
        'stewardship': max(0, min(1, current.stewardship + stewardship_delta)),
        'network': max(0, min(1.5, current.network + network_delta)),
        'reputation': max(0, min(1.5, current.reputation + reputation_delta)),
        'temporal': max(0, min(1, current.temporal + temporal_delta))
    }

    return V3Tensor(**{k: round(v, 4) for k, v in new_values.items()})


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
    Manages role-contextual T3/V3 tensors for an entity

    Key principle: Trust is NEVER global. Each role has separate tensors.
    """

    def __init__(self, entity_lct: str):
        self.entity_lct = entity_lct
        self.role_tensors: Dict[str, RoleTensorPair] = {}
        self.history: List[dict] = []

    def get_or_create(self, role: str) -> RoleTensorPair:
        """Get tensors for role, creating if needed"""
        if role not in self.role_tensors:
            # New roles start with minimal trust
            self.role_tensors[role] = RoleTensorPair(
                role=role,
                t3=T3Tensor(
                    competence=0.3,
                    reliability=0.3,
                    consistency=0.5,
                    witnesses=0.1,
                    lineage=0.1,
                    alignment=0.5
                ),
                v3=V3Tensor(
                    energy=0.3,
                    contribution=0.3,
                    stewardship=0.5,
                    network=0.1,
                    reputation=0.1,
                    temporal=0.5
                )
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
        """
        Update tensors for a role based on R6 action outcome
        """
        pair = self.get_or_create(role)

        # Update T3
        new_t3 = update_t3(pair.t3, outcome, witness_count, ci_multiplier)

        # Update V3
        new_v3 = update_v3(pair.v3, atp_spent, atp_earned,
                          contribution_quality, witness_count)

        # Record history
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'role': role,
            'outcome': outcome.value,
            't3_before': pair.t3.to_dict(),
            't3_after': new_t3.to_dict(),
            'v3_before': pair.v3.to_dict(),
            'v3_after': new_v3.to_dict()
        })

        # Update pair
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
        Compute ATP cost for an action based on trust tensors

        Lower trust = higher cost (risk premium)
        Lower CI = higher cost (coherence penalty)
        """
        pair = self.get_or_create(role)

        # Trust discount: high trust reduces cost
        trust_score = pair.t3.weighted_score()
        trust_multiplier = 2.0 - trust_score  # 1.0 at trust=1.0, 2.0 at trust=0.0

        # CI penalty: low coherence increases cost
        ci_multiplier = 1.0 / (ci ** 2)  # 1x at CI=1.0, 4x at CI=0.5
        ci_multiplier = min(ci_multiplier, 10.0)  # Cap at 10x

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
    Apply time-based decay to tensors

    - competence: Stable (represents inherent capability)
    - reliability/consistency: Slow decay without reinforcement
    - witnesses: Moderate decay (testimony fades)
    - lineage: Very slow decay (history persists)
    - alignment: Context-dependent, moderate decay
    """
    decay_rates = {
        'competence': 0.0,      # No decay
        'reliability': 0.005,   # 0.5% per month
        'consistency': 0.005,
        'witnesses': 0.01,      # 1% per month
        'lineage': 0.002,       # 0.2% per month
        'alignment': 0.005
    }

    for role, pair in tensor_store.role_tensors.items():
        new_values = {}
        for dim in T3Tensor.dimensions():
            current = getattr(pair.t3, dim)
            decay = decay_rates[dim] * (days_elapsed / 30)
            new_val = max(0.1, current - decay)  # Floor at 0.1
            new_values[dim] = round(new_val, 4)

        pair.t3 = T3Tensor(**new_values)


# ============================================================================
# Demo
# ============================================================================

def demo_trust_tensors():
    """Demonstrate trust tensor functionality"""

    print("=" * 60)
    print("T3/V3 TRUST TENSOR DEMO")
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
    threshold = T3Tensor(
        competence=0.4,
        reliability=0.4,
        consistency=0.4,
        witnesses=0.2,
        lineage=0.2,
        alignment=0.4
    )
    meets, failing = pair.t3.meets_threshold(threshold)
    print(f"  Threshold: {threshold.to_dict()}")
    print(f"  Meets threshold: {meets}")
    if failing:
        print(f"  Failing dimensions: {failing}")

    print("\n" + "=" * 60)
    print("Trust Tensor Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo_trust_tensors()
