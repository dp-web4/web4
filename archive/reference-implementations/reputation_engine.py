"""
Web4 Reputation Engine
=====================

Computes T3/V3 reputation deltas from authorization outcomes and R7 action results.

Key Features:
- Multi-dimensional trust assessment (Talent, Training, Temperament)
- Multi-dimensional value assessment (Veracity, Validity, Value)
- Gaming resistance through decay, witnesses, and multi-factor scoring
- Role-contextual reputation (surgeon trust ≠ mechanic trust)
- Time-based decay and recovery
- Authorization history integration

Design Philosophy:
- Reputation is earned through consistent performance
- Trust degrades slowly, builds slowly (asymmetric)
- Gaming is expensive and detectable
- Witness validation prevents self-promotion
- Multiple dimensions prevent narrow optimization
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import time
import hashlib
import json
import math


class OutcomeType(Enum):
    """Types of action outcomes"""
    NOVEL_SUCCESS = "novel_success"  # Creative, exceptional result
    STANDARD_SUCCESS = "standard_success"  # Expected good result
    EXPECTED_FAILURE = "expected_failure"  # Attempted but failed (reasonable)
    UNEXPECTED_FAILURE = "unexpected_failure"  # Should have succeeded but didn't
    ETHICS_VIOLATION = "ethics_violation"  # Violated trust or rules
    EXCEPTIONAL_QUALITY = "exceptional_quality"  # Above expectations
    DEADLINE_MET = "deadline_met"  # Timely completion
    DEADLINE_MISSED = "deadline_missed"  # Late completion
    RESOURCE_EFFICIENT = "resource_efficient"  # Under budget
    RESOURCE_WASTEFUL = "resource_wasteful"  # Over budget


@dataclass
class T3Tensor:
    """Trust tensor (capability and character)"""
    talent: float = 0.5  # Natural aptitude
    training: float = 0.5  # Learned skills
    temperament: float = 0.5  # Reliability
    last_updated: float = field(default_factory=time.time)
    decay_enabled: bool = True

    def __post_init__(self):
        """Validate tensor values"""
        self.talent = max(0.0, min(1.0, self.talent))
        self.training = max(0.0, min(1.0, self.training))
        self.temperament = max(0.0, min(1.0, self.temperament))

    def apply_decay(self, months_elapsed: float):
        """Apply time-based decay"""
        if not self.decay_enabled:
            return

        # Training decays without practice
        self.training = max(0.0, self.training - (0.001 * months_elapsed))

        # Temperament can recover slowly
        if self.temperament < 0.8:
            self.temperament = min(1.0, self.temperament + (0.01 * months_elapsed))

        # Talent doesn't decay (innate capability)

        self.last_updated = time.time()

    def update(self, delta_talent: float, delta_training: float, delta_temperament: float):
        """Update tensor values"""
        self.talent = max(0.0, min(1.0, self.talent + delta_talent))
        self.training = max(0.0, min(1.0, self.training + delta_training))
        self.temperament = max(0.0, min(1.0, self.temperament + delta_temperament))
        self.last_updated = time.time()

    def average(self) -> float:
        """Get average trust score"""
        return (self.talent + self.training + self.temperament) / 3.0

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "talent": self.talent,
            "training": self.training,
            "temperament": self.temperament,
            "average": self.average(),
            "last_updated": self.last_updated
        }


@dataclass
class V3Tensor:
    """Value tensor (output quality)"""
    veracity: float = 0.5  # Truthfulness
    validity: float = 0.5  # Logical soundness
    value: float = 0.5  # Actual utility
    last_updated: float = field(default_factory=time.time)

    def __post_init__(self):
        """Validate tensor values"""
        self.veracity = max(0.0, min(1.0, self.veracity))
        self.validity = max(0.0, min(1.0, self.validity))
        self.value = max(0.0, self.value)  # Value can exceed 1.0

    def update(self, delta_veracity: float, delta_validity: float, delta_value: float):
        """Update tensor values"""
        self.veracity = max(0.0, min(1.0, self.veracity + delta_veracity))
        self.validity = max(0.0, min(1.0, self.validity + delta_validity))
        self.value = max(0.0, self.value + delta_value)
        self.last_updated = time.time()

    def average(self) -> float:
        """Get average value score (cap at 1.0 for averaging)"""
        return (self.veracity + self.validity + min(1.0, self.value)) / 3.0

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "veracity": self.veracity,
            "validity": self.validity,
            "value": self.value,
            "average": self.average(),
            "last_updated": self.last_updated
        }


@dataclass
class ReputationDelta:
    """Reputation change from a single action"""
    entity_lct: str
    role_lct: str
    action_type: str
    action_target: str
    action_id: str
    outcome_type: OutcomeType
    timestamp: float = field(default_factory=time.time)

    # T3 changes
    delta_talent: float = 0.0
    delta_training: float = 0.0
    delta_temperament: float = 0.0

    # V3 changes
    delta_veracity: float = 0.0
    delta_validity: float = 0.0
    delta_value: float = 0.0

    # Supporting evidence
    contributing_factors: List[Dict] = field(default_factory=list)
    witnesses: List[str] = field(default_factory=list)
    reason: str = ""

    def net_trust_change(self) -> float:
        """Total T3 change"""
        return self.delta_talent + self.delta_training + self.delta_temperament

    def net_value_change(self) -> float:
        """Total V3 change"""
        return self.delta_veracity + self.delta_validity + self.delta_value

    def to_dict(self) -> Dict:
        """Convert to dictionary for logging"""
        return {
            "entity_lct": self.entity_lct,
            "role_lct": self.role_lct,
            "action_type": self.action_type,
            "action_target": self.action_target,
            "action_id": self.action_id,
            "outcome_type": self.outcome_type.value,
            "timestamp": self.timestamp,
            "t3_delta": {
                "talent": self.delta_talent,
                "training": self.delta_training,
                "temperament": self.delta_temperament
            },
            "v3_delta": {
                "veracity": self.delta_veracity,
                "validity": self.delta_validity,
                "value": self.delta_value
            },
            "net_trust_change": self.net_trust_change(),
            "net_value_change": self.net_value_change(),
            "contributing_factors": self.contributing_factors,
            "witnesses": self.witnesses,
            "reason": self.reason
        }


@dataclass
class EntityReputation:
    """Complete reputation profile for an entity in a role"""
    entity_lct: str
    role_lct: str
    t3: T3Tensor = field(default_factory=T3Tensor)
    v3: V3Tensor = field(default_factory=V3Tensor)
    creation_time: float = field(default_factory=time.time)
    total_actions: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    history: List[ReputationDelta] = field(default_factory=list)

    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_actions == 0:
            return 0.0
        return self.successful_actions / self.total_actions

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "entity_lct": self.entity_lct,
            "role_lct": self.role_lct,
            "t3": self.t3.to_dict(),
            "v3": self.v3.to_dict(),
            "creation_time": self.creation_time,
            "total_actions": self.total_actions,
            "successful_actions": self.successful_actions,
            "failed_actions": self.failed_actions,
            "success_rate": self.success_rate(),
            "reputation_age_days": (time.time() - self.creation_time) / 86400
        }


class ReputationEngine:
    """
    Web4 Reputation Computation Engine

    Computes T3/V3 reputation deltas from action outcomes, prevents gaming,
    and maintains role-contextual reputation profiles.
    """

    def __init__(self):
        # Role-contextual reputation storage: (entity_lct, role_lct) -> EntityReputation
        self.reputations: Dict[Tuple[str, str], EntityReputation] = {}

        # Outcome impact tables (base values)
        self.t3_impacts = self._init_t3_impacts()
        self.v3_impacts = self._init_v3_impacts()

        # Gaming resistance parameters
        self.witness_boost = 1.2  # 20% boost for witnessed actions
        self.consistency_bonus = 1.1  # 10% bonus for consistent performance
        self.novelty_multiplier = 1.5  # 50% boost for novel achievements

        # Decay parameters
        self.decay_check_interval = 86400 * 30  # Check monthly
        self.last_decay_check = time.time()

    def _init_t3_impacts(self) -> Dict[OutcomeType, Tuple[float, float, float]]:
        """Initialize T3 impact table: (talent, training, temperament)"""
        return {
            OutcomeType.NOVEL_SUCCESS: (+0.03, +0.02, +0.01),
            OutcomeType.STANDARD_SUCCESS: (0.0, +0.01, +0.005),
            OutcomeType.EXPECTED_FAILURE: (-0.01, 0.0, 0.0),
            OutcomeType.UNEXPECTED_FAILURE: (-0.02, -0.01, -0.02),
            OutcomeType.ETHICS_VIOLATION: (-0.05, 0.0, -0.10),
            OutcomeType.EXCEPTIONAL_QUALITY: (+0.02, +0.01, +0.01),
            OutcomeType.DEADLINE_MET: (0.0, 0.0, +0.01),
            OutcomeType.DEADLINE_MISSED: (0.0, 0.0, -0.02),
            OutcomeType.RESOURCE_EFFICIENT: (+0.01, +0.005, +0.005),
            OutcomeType.RESOURCE_WASTEFUL: (-0.01, 0.0, -0.01)
        }

    def _init_v3_impacts(self) -> Dict[OutcomeType, Tuple[float, float, float]]:
        """Initialize V3 impact table: (veracity, validity, value)"""
        return {
            OutcomeType.NOVEL_SUCCESS: (+0.01, +0.01, +0.02),
            OutcomeType.STANDARD_SUCCESS: (+0.005, +0.005, +0.01),
            OutcomeType.EXPECTED_FAILURE: (0.0, 0.0, 0.0),
            OutcomeType.UNEXPECTED_FAILURE: (-0.01, -0.01, -0.01),
            OutcomeType.ETHICS_VIOLATION: (-0.10, -0.05, -0.05),
            OutcomeType.EXCEPTIONAL_QUALITY: (+0.02, +0.01, +0.03),
            OutcomeType.DEADLINE_MET: (0.0, 0.0, +0.01),
            OutcomeType.DEADLINE_MISSED: (0.0, 0.0, -0.01),
            OutcomeType.RESOURCE_EFFICIENT: (0.0, +0.01, +0.02),
            OutcomeType.RESOURCE_WASTEFUL: (0.0, -0.01, -0.02)
        }

    def get_or_create_reputation(self, entity_lct: str, role_lct: str) -> EntityReputation:
        """Get existing reputation or create new one"""
        key = (entity_lct, role_lct)
        if key not in self.reputations:
            self.reputations[key] = EntityReputation(
                entity_lct=entity_lct,
                role_lct=role_lct
            )
        return self.reputations[key]

    def compute_delta(
        self,
        entity_lct: str,
        role_lct: str,
        action_type: str,
        action_target: str,
        outcome_type: OutcomeType,
        contributing_factors: Optional[List[Dict]] = None,
        witnesses: Optional[List[str]] = None,
        action_id: Optional[str] = None
    ) -> ReputationDelta:
        """
        Compute reputation delta from action outcome

        Applies:
        - Base impact from outcome type
        - Witness boost (if witnesses provided)
        - Consistency bonus (if entity has good history)
        - Novelty multiplier (for creative achievements)
        - Gaming resistance (diminishing returns)
        """

        # Get base impacts
        t3_base = self.t3_impacts.get(outcome_type, (0.0, 0.0, 0.0))
        v3_base = self.v3_impacts.get(outcome_type, (0.0, 0.0, 0.0))

        # Get entity reputation for context
        reputation = self.get_or_create_reputation(entity_lct, role_lct)

        # Apply modifiers
        multiplier = 1.0

        # Witness boost (resistance to self-promotion)
        if witnesses and len(witnesses) > 0:
            multiplier *= self.witness_boost

        # Consistency bonus (reward reliable performers)
        if reputation.total_actions >= 10 and reputation.success_rate() > 0.8:
            multiplier *= self.consistency_bonus

        # Novelty multiplier (encourage innovation)
        if outcome_type == OutcomeType.NOVEL_SUCCESS:
            multiplier *= self.novelty_multiplier

        # Diminishing returns (prevent gaming through volume)
        # As reputation increases, gains become smaller
        t3_avg = reputation.t3.average()
        if t3_avg > 0.8:
            diminishing_factor = 0.5  # 50% reduction for high reputation
        elif t3_avg > 0.6:
            diminishing_factor = 0.75  # 25% reduction for medium-high
        else:
            diminishing_factor = 1.0  # Full gains for low reputation

        multiplier *= diminishing_factor

        # Apply multipliers to base impacts
        delta = ReputationDelta(
            entity_lct=entity_lct,
            role_lct=role_lct,
            action_type=action_type,
            action_target=action_target,
            action_id=action_id or f"action:{int(time.time())}",
            outcome_type=outcome_type,
            delta_talent=t3_base[0] * multiplier,
            delta_training=t3_base[1] * multiplier,
            delta_temperament=t3_base[2] * multiplier,
            delta_veracity=v3_base[0] * multiplier,
            delta_validity=v3_base[1] * multiplier,
            delta_value=v3_base[2] * multiplier,
            contributing_factors=contributing_factors or [],
            witnesses=witnesses or [],
            reason=self._generate_reason(outcome_type, multiplier)
        )

        return delta

    def apply_delta(self, delta: ReputationDelta):
        """Apply reputation delta to entity's reputation"""
        reputation = self.get_or_create_reputation(delta.entity_lct, delta.role_lct)

        # Update T3
        reputation.t3.update(
            delta.delta_talent,
            delta.delta_training,
            delta.delta_temperament
        )

        # Update V3
        reputation.v3.update(
            delta.delta_veracity,
            delta.delta_validity,
            delta.delta_value
        )

        # Update statistics
        reputation.total_actions += 1
        if delta.outcome_type in [OutcomeType.NOVEL_SUCCESS, OutcomeType.STANDARD_SUCCESS,
                                  OutcomeType.EXCEPTIONAL_QUALITY, OutcomeType.DEADLINE_MET,
                                  OutcomeType.RESOURCE_EFFICIENT]:
            reputation.successful_actions += 1
        else:
            reputation.failed_actions += 1

        # Add to history
        reputation.history.append(delta)

        # Trim history if too long (keep last 100)
        if len(reputation.history) > 100:
            reputation.history = reputation.history[-100:]

    def check_decay(self):
        """Apply time-based decay to all reputations"""
        now = time.time()
        if now - self.last_decay_check < self.decay_check_interval:
            return  # Not time yet

        months_elapsed = (now - self.last_decay_check) / (86400 * 30)

        for reputation in self.reputations.values():
            reputation.t3.apply_decay(months_elapsed)

        self.last_decay_check = now

    def _generate_reason(self, outcome_type: OutcomeType, multiplier: float) -> str:
        """Generate human-readable reason for reputation change"""
        reasons = {
            OutcomeType.NOVEL_SUCCESS: "Demonstrated exceptional creativity and problem-solving",
            OutcomeType.STANDARD_SUCCESS: "Completed task successfully as expected",
            OutcomeType.EXPECTED_FAILURE: "Attempted challenging task but didn't succeed",
            OutcomeType.UNEXPECTED_FAILURE: "Failed task that should have been achievable",
            OutcomeType.ETHICS_VIOLATION: "Violated ethical standards or trust",
            OutcomeType.EXCEPTIONAL_QUALITY: "Exceeded quality expectations significantly",
            OutcomeType.DEADLINE_MET: "Completed work on time",
            OutcomeType.DEADLINE_MISSED: "Failed to meet deadline",
            OutcomeType.RESOURCE_EFFICIENT: "Completed task efficiently under budget",
            OutcomeType.RESOURCE_WASTEFUL: "Used excessive resources for task"
        }

        base_reason = reasons.get(outcome_type, "Action completed")

        if multiplier > 1.5:
            return f"{base_reason} (with witnesses and proven consistency)"
        elif multiplier > 1.2:
            return f"{base_reason} (witnessed by community)"
        elif multiplier < 0.6:
            return f"{base_reason} (reputation approaching ceiling)"
        else:
            return base_reason

    def get_reputation(self, entity_lct: str, role_lct: str) -> Optional[EntityReputation]:
        """Get entity's reputation in role"""
        key = (entity_lct, role_lct)
        return self.reputations.get(key)

    def get_trust_score(self, entity_lct: str, role_lct: str) -> float:
        """Get average T3 trust score"""
        reputation = self.get_reputation(entity_lct, role_lct)
        return reputation.t3.average() if reputation else 0.5

    def get_value_score(self, entity_lct: str, role_lct: str) -> float:
        """Get average V3 value score"""
        reputation = self.get_reputation(entity_lct, role_lct)
        return reputation.v3.average() if reputation else 0.5

    def detect_gaming_attempt(self, entity_lct: str, role_lct: str) -> Tuple[bool, Optional[str]]:
        """Detect potential reputation gaming"""
        reputation = self.get_reputation(entity_lct, role_lct)
        if not reputation or reputation.total_actions < 10:
            return False, None

        # Check for suspicious patterns

        # 1. Too many successes without witnesses (self-promotion)
        recent = reputation.history[-20:] if len(reputation.history) >= 20 else reputation.history
        witnessed = sum(1 for delta in recent if len(delta.witnesses) > 0)
        if reputation.success_rate() > 0.95 and witnessed / len(recent) < 0.2:
            return True, "Suspiciously high success rate without witnesses"

        # 2. Rapid reputation growth (buying reputation)
        if len(reputation.history) >= 10:
            recent_growth = sum(delta.net_trust_change() for delta in reputation.history[-10:])
            if recent_growth > 0.5:  # More than 0.5 total growth in 10 actions
                return True, "Unusually rapid reputation growth"

        # 3. Inconsistent performance (manipulation)
        if reputation.total_actions >= 20:
            success_variance = abs(reputation.success_rate() - 0.5)
            if success_variance < 0.1:  # Too perfectly balanced
                return True, "Suspiciously consistent 50/50 success pattern"

        return False, None


# Example usage
if __name__ == "__main__":
    engine = ReputationEngine()

    # Create test entity
    entity = "lct:ai:researcher"
    role = "role:data_analyst"

    print("=" * 70)
    print("Web4 Reputation Engine - Demonstration")
    print("=" * 70)

    # Simulate action sequence
    outcomes = [
        (OutcomeType.STANDARD_SUCCESS, ["witness:1"], "First successful analysis"),
        (OutcomeType.STANDARD_SUCCESS, [], "Second analysis (no witness)"),
        (OutcomeType.NOVEL_SUCCESS, ["witness:1", "witness:2"], "Creative solution"),
        (OutcomeType.EXCEPTIONAL_QUALITY, ["witness:1"], "Exceeded expectations"),
        (OutcomeType.EXPECTED_FAILURE, [], "Attempted difficult task"),
        (OutcomeType.STANDARD_SUCCESS, ["witness:2"], "Consistent performance"),
    ]

    for i, (outcome, witnesses, desc) in enumerate(outcomes, 1):
        delta = engine.compute_delta(
            entity_lct=entity,
            role_lct=role,
            action_type="analyze",
            action_target=f"dataset:{i}",
            outcome_type=outcome,
            witnesses=witnesses
        )

        engine.apply_delta(delta)

        print(f"\n Action {i}: {desc}")
        print(f"   Outcome: {outcome.value}")
        print(f"   T3 Delta: +{delta.net_trust_change():.4f}")
        print(f"   V3 Delta: +{delta.net_value_change():.4f}")
        print(f"   Witnesses: {len(witnesses)}")

    # Show final reputation
    reputation = engine.get_reputation(entity, role)
    print("\n" + "=" * 70)
    print("Final Reputation Profile")
    print("=" * 70)
    print(json.dumps(reputation.to_dict(), indent=2))

    # Check for gaming
    is_gaming, reason = engine.detect_gaming_attempt(entity, role)
    print(f"\nGaming Detection: {'⚠️  SUSPICIOUS' if is_gaming else '✅ Clean'}")
    if is_gaming:
        print(f"Reason: {reason}")
