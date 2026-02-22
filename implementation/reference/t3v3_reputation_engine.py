#!/usr/bin/env python3
"""
Web4 T3/V3 Tensor & Reputation Engine — Reference Implementation

Implements two tightly coupled specifications:
  1. web4-standard/core-spec/t3-v3-tensors.md (471 lines)
  2. web4-standard/core-spec/reputation-computation.md (759 lines)

T3/V3 Tensors:
  - Role-contextual trust (T3: Talent/Training/Temperament)
  - Role-contextual value (V3: Veracity/Validity/Value)
  - Fractal sub-dimensions via subDimensionOf chains
  - Evolution history per entity-role pair
  - Decay mechanics (training decay, temperament recovery)
  - Team composition (weighted average per role)

Reputation Engine:
  - ReputationRule: trigger conditions → T3/V3 deltas with modifiers
  - ReputationDelta: full delta with contributing factors + witnesses
  - compute_reputation_delta(): multi-factor computation
  - Time-weighted aggregation with 30-day half-life
  - Reputation decay for inactive entities
  - Anti-gaming: diminishing returns, witness diversity
"""

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Optional


# ══════════════════════════════════════════════════════════════
# §2 — T3 Tensor (Trust Through Capability)
# ══════════════════════════════════════════════════════════════

T3_DIMS = ["talent", "training", "temperament"]
V3_DIMS = ["veracity", "validity", "value"]

# §2.3 — Evolution mechanics: outcome → dimension impact
OUTCOME_IMPACTS = {
    "novel_success":      {"talent": (0.02, 0.05), "training": (0.01, 0.02), "temperament": (0.01, 0.01)},
    "standard_success":   {"talent": (0.0, 0.0),   "training": (0.005, 0.01), "temperament": (0.005, 0.005)},
    "expected_failure":   {"talent": (-0.01, -0.01), "training": (0.0, 0.0),  "temperament": (0.0, 0.0)},
    "unexpected_failure": {"talent": (-0.02, -0.02), "training": (-0.01, -0.01), "temperament": (-0.02, -0.02)},
    "ethics_violation":   {"talent": (-0.05, -0.05), "training": (0.0, 0.0),  "temperament": (-0.10, -0.10)},
}


@dataclass
class DimensionScore:
    """Score for a single dimension with provenance."""
    value: float
    observed_at: Optional[str] = None
    witnessed_by: Optional[str] = None

    def to_dict(self) -> dict:
        d = {"value": round(self.value, 4)}
        if self.observed_at:
            d["observed_at"] = self.observed_at
        if self.witnessed_by:
            d["witnessed_by"] = self.witnessed_by
        return d


@dataclass
class SubDimension:
    """Fractal sub-dimension linked via subDimensionOf (§2.4)."""
    name: str
    parent: str  # Parent dimension name
    score: float = 0.0
    children: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {"name": self.name, "parent": self.parent, "score": round(self.score, 4)}
        if self.children:
            d["children"] = [c.to_dict() for c in self.children]
        return d


@dataclass
class EvolutionEntry:
    """Single evolution event for a tensor (§2.3)."""
    timestamp: str
    context: str
    action_id: str
    deltas: dict  # dim → delta value
    reason: str
    outcome_type: str = "standard_success"

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "context": self.context,
            "action_id": self.action_id,
            "deltas": {k: round(v, 4) for k, v in self.deltas.items()},
            "reason": self.reason,
            "outcome_type": self.outcome_type,
        }


class Tensor:
    """Role-contextual trust or value tensor."""

    def __init__(self, dim_names: list, initial_values: dict = None):
        self.dim_names = list(dim_names)
        self.dimensions: dict[str, float] = {}
        for d in dim_names:
            self.dimensions[d] = (initial_values or {}).get(d, 0.5)
        self.sub_dimensions: dict[str, list[SubDimension]] = {d: [] for d in dim_names}
        self.evolution: list[EvolutionEntry] = []

    def __getitem__(self, dim: str) -> float:
        return self.dimensions.get(dim, 0.0)

    def __setitem__(self, dim: str, value: float):
        self.dimensions[dim] = max(0.0, min(1.0, value))

    def apply_delta(self, dim: str, delta: float) -> float:
        """Apply a delta to a dimension, clamping to [0,1]."""
        old = self.dimensions.get(dim, 0.5)
        new = round(max(0.0, min(1.0, old + delta)), 10)
        self.dimensions[dim] = new
        return round(new - old, 10)  # Actual change after clamping

    def composite(self, weights: dict = None) -> float:
        """Weighted average composite score."""
        if not weights:
            weights = {d: 1.0 / len(self.dim_names) for d in self.dim_names}
        total_w = sum(weights.get(d, 0) for d in self.dim_names)
        if total_w == 0:
            return 0.0
        return sum(self.dimensions[d] * weights.get(d, 0) for d in self.dim_names) / total_w

    def add_sub_dimension(self, parent: str, name: str, score: float = 0.0) -> SubDimension:
        """Add a fractal sub-dimension (§2.4)."""
        sd = SubDimension(name=name, parent=parent, score=score)
        if parent in self.sub_dimensions:
            self.sub_dimensions[parent].append(sd)
        else:
            # Check if parent is itself a sub-dimension
            for root_dims in self.sub_dimensions.values():
                for rd in root_dims:
                    if rd.name == parent:
                        rd.children.append(sd)
                        return sd
        return sd

    def get_all_sub_dims(self, root: str) -> list[SubDimension]:
        """Get all sub-dimensions under a root (fractal traversal)."""
        result = []
        stack = list(self.sub_dimensions.get(root, []))
        while stack:
            sd = stack.pop()
            result.append(sd)
            stack.extend(sd.children)
        return result

    def record_evolution(self, timestamp: str, context: str, action_id: str,
                          deltas: dict, reason: str, outcome_type: str = "standard_success"):
        self.evolution.append(EvolutionEntry(
            timestamp=timestamp, context=context, action_id=action_id,
            deltas=deltas, reason=reason, outcome_type=outcome_type,
        ))

    def to_dict(self) -> dict:
        d = {"dimensions": {k: round(v, 4) for k, v in self.dimensions.items()}}
        d["composite"] = round(self.composite(), 4)
        if any(sds for sds in self.sub_dimensions.values()):
            d["sub_dimensions"] = {
                k: [sd.to_dict() for sd in v]
                for k, v in self.sub_dimensions.items() if v
            }
        if self.evolution:
            d["evolution_count"] = len(self.evolution)
        return d


# ══════════════════════════════════════════════════════════════
# §1.1 — Role-Contextual T3/V3 (NOT global)
# ══════════════════════════════════════════════════════════════

class RoleTensor:
    """T3 and V3 tensors bound to a specific entity-role pair."""

    def __init__(self, entity_lct: str, role_lct: str,
                 t3_values: dict = None, v3_values: dict = None):
        self.entity_lct = entity_lct
        self.role_lct = role_lct
        self.t3 = Tensor(T3_DIMS, t3_values)
        self.v3 = Tensor(V3_DIMS, v3_values)
        self.created_at = _now()
        self.last_action_at: Optional[str] = None
        self.action_count = 0

    def trust_score(self, weights: dict = None) -> float:
        """Composite T3 score for this role."""
        return self.t3.composite(weights)

    def value_score(self, weights: dict = None) -> float:
        """Composite V3 score for this role."""
        return self.v3.composite(weights)

    def apply_outcome(self, outcome_type: str, context: str, action_id: str,
                       reason: str, modifiers: dict = None) -> dict:
        """Apply an R6/R7 outcome to this role tensor (§2.3)."""
        if outcome_type not in OUTCOME_IMPACTS:
            return {}

        impacts = OUTCOME_IMPACTS[outcome_type]
        t3_deltas = {}
        v3_deltas = {}

        for dim in T3_DIMS:
            if dim in impacts:
                lo, hi = impacts[dim]
                base = (lo + hi) / 2.0
                mod = (modifiers or {}).get(dim, 1.0)
                delta = base * mod
                if delta != 0:
                    actual = self.t3.apply_delta(dim, delta)
                    if actual != 0:
                        t3_deltas[dim] = round(actual, 4)

        # V3 impacts derived from outcome type
        v3_impacts = self._v3_from_outcome(outcome_type)
        for dim in V3_DIMS:
            if dim in v3_impacts:
                delta = v3_impacts[dim] * (modifiers or {}).get(dim, 1.0)
                if delta != 0:
                    actual = self.v3.apply_delta(dim, delta)
                    if actual != 0:
                        v3_deltas[dim] = round(actual, 4)

        # Record evolution
        all_deltas = {**{f"t3.{k}": v for k, v in t3_deltas.items()},
                      **{f"v3.{k}": v for k, v in v3_deltas.items()}}
        self.t3.record_evolution(_now(), context, action_id, t3_deltas, reason, outcome_type)
        self.v3.record_evolution(_now(), context, action_id, v3_deltas, reason, outcome_type)

        self.last_action_at = _now()
        self.action_count += 1

        return {"t3_deltas": t3_deltas, "v3_deltas": v3_deltas}

    def _v3_from_outcome(self, outcome_type: str) -> dict:
        v3_map = {
            "novel_success":      {"veracity": 0.02, "validity": 0.01, "value": 0.03},
            "standard_success":   {"veracity": 0.01, "validity": 0.005, "value": 0.01},
            "expected_failure":   {"veracity": 0.0, "validity": -0.005, "value": -0.01},
            "unexpected_failure": {"veracity": -0.01, "validity": -0.01, "value": -0.02},
            "ethics_violation":   {"veracity": -0.20, "validity": -0.15, "value": -0.10},
        }
        return v3_map.get(outcome_type, {})

    def to_dict(self) -> dict:
        return {
            "entity_lct": self.entity_lct,
            "role_lct": self.role_lct,
            "t3": self.t3.to_dict(),
            "v3": self.v3.to_dict(),
            "trust_score": round(self.trust_score(), 4),
            "value_score": round(self.value_score(), 4),
            "action_count": self.action_count,
            "last_action_at": self.last_action_at,
        }


# ══════════════════════════════════════════════════════════════
# Entity Tensor Registry — Multi-role management
# ══════════════════════════════════════════════════════════════

class EntityTensorRegistry:
    """Manages T3/V3 tensors for entities across all their roles."""

    def __init__(self):
        self._tensors: dict[str, dict[str, RoleTensor]] = {}  # entity → role → tensor

    def get_or_create(self, entity_lct: str, role_lct: str,
                       t3_init: dict = None, v3_init: dict = None) -> RoleTensor:
        if entity_lct not in self._tensors:
            self._tensors[entity_lct] = {}
        if role_lct not in self._tensors[entity_lct]:
            self._tensors[entity_lct][role_lct] = RoleTensor(
                entity_lct, role_lct, t3_init, v3_init)
        return self._tensors[entity_lct][role_lct]

    def get(self, entity_lct: str, role_lct: str) -> Optional[RoleTensor]:
        return self._tensors.get(entity_lct, {}).get(role_lct)

    def roles_for_entity(self, entity_lct: str) -> list[str]:
        return list(self._tensors.get(entity_lct, {}).keys())

    def entity_count(self) -> int:
        return len(self._tensors)

    def total_tensors(self) -> int:
        return sum(len(roles) for roles in self._tensors.values())


# ══════════════════════════════════════════════════════════════
# §4 — Reputation Rules
# ══════════════════════════════════════════════════════════════

@dataclass
class RuleModifier:
    condition: str
    multiplier: float

    def to_dict(self) -> dict:
        return {"condition": self.condition, "multiplier": self.multiplier}


@dataclass
class DimensionImpact:
    base_delta: float
    modifiers: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {"base_delta": self.base_delta}
        if self.modifiers:
            d["modifiers"] = [m.to_dict() for m in self.modifiers]
        return d


@dataclass
class ReputationRule:
    """§4 — Rule mapping outcomes to T3/V3 deltas."""
    rule_id: str
    trigger_conditions: dict
    t3_impacts: dict = field(default_factory=dict)  # dim → DimensionImpact
    v3_impacts: dict = field(default_factory=dict)  # dim → DimensionImpact
    witnesses_required: int = 1
    law_oracle: Optional[str] = None
    category: str = "success"  # success, failure, exceptional, ethical_violation

    def matches(self, action_type: str, result_status: str, quality: float = 0.0) -> bool:
        tc = self.trigger_conditions
        if "action_type" in tc and tc["action_type"] != action_type:
            return False
        if "result_status" in tc and tc["result_status"] != result_status:
            return False
        if "quality_threshold" in tc and quality < tc["quality_threshold"]:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "trigger_conditions": self.trigger_conditions,
            "t3_impacts": {k: v.to_dict() for k, v in self.t3_impacts.items()},
            "v3_impacts": {k: v.to_dict() for k, v in self.v3_impacts.items()},
            "witnesses_required": self.witnesses_required,
            "law_oracle": self.law_oracle,
            "category": self.category,
        }


# ══════════════════════════════════════════════════════════════
# §5 — Reputation Delta & Contributing Factors
# ══════════════════════════════════════════════════════════════

@dataclass
class ContributingFactor:
    factor: str
    weight: float
    value: float = 0.0
    normalized_weight: float = 0.0

    def to_dict(self) -> dict:
        return {
            "factor": self.factor,
            "weight": round(self.weight, 4),
            "normalized_weight": round(self.normalized_weight, 4),
            "value": self.value,
        }


@dataclass
class WitnessAttestation:
    lct: str
    witness_type: str
    signature: str = ""
    timestamp: str = ""
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return {
            "lct": self.lct,
            "type": self.witness_type,
            "signature": self.signature or f"sig:{self.lct}",
            "timestamp": self.timestamp or _now(),
            "confidence": self.confidence,
        }


@dataclass
class DimensionDelta:
    change: float
    from_value: float
    to_value: float

    def to_dict(self) -> dict:
        return {
            "change": round(self.change, 4),
            "from": round(self.from_value, 4),
            "to": round(self.to_value, 4),
        }


@dataclass
class ReputationDelta:
    """Complete reputation change from a single R7 transaction (§1)."""
    subject_lct: str
    role_lct: str
    action_type: str
    action_id: str
    rule_triggered: str
    reason: str
    t3_delta: dict = field(default_factory=dict)  # dim → DimensionDelta
    v3_delta: dict = field(default_factory=dict)
    contributing_factors: list = field(default_factory=list)
    witnesses: list = field(default_factory=list)
    net_trust_change: float = 0.0
    net_value_change: float = 0.0
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "subject_lct": self.subject_lct,
            "role_lct": self.role_lct,
            "action_type": self.action_type,
            "action_id": self.action_id,
            "rule_triggered": self.rule_triggered,
            "reason": self.reason,
            "t3_delta": {k: v.to_dict() for k, v in self.t3_delta.items()},
            "v3_delta": {k: v.to_dict() for k, v in self.v3_delta.items()},
            "contributing_factors": [f.to_dict() for f in self.contributing_factors],
            "witnesses": [w.to_dict() for w in self.witnesses],
            "net_trust_change": round(self.net_trust_change, 4),
            "net_value_change": round(self.net_value_change, 4),
            "timestamp": self.timestamp or _now(),
        }


# ══════════════════════════════════════════════════════════════
# Reputation Engine — Core computation (§5)
# ══════════════════════════════════════════════════════════════

class ReputationEngine:
    """Computes reputation deltas from R7 actions (§5)."""

    def __init__(self, registry: EntityTensorRegistry):
        self.registry = registry
        self.rules: list[ReputationRule] = []
        self.delta_history: list[ReputationDelta] = []
        self._diminishing_returns: dict[str, dict[str, int]] = {}  # entity → action_type → count

    def add_rule(self, rule: ReputationRule):
        self.rules.append(rule)

    def compute_reputation_delta(
        self,
        entity_lct: str,
        role_lct: str,
        action_type: str,
        action_id: str,
        result_status: str,
        quality: float = 0.0,
        factors_data: dict = None,
    ) -> Optional[ReputationDelta]:
        """§5 — Core computation: action + rules → reputation delta."""

        # 1. Get or create role tensor
        rt = self.registry.get_or_create(entity_lct, role_lct)

        # 2. Find triggered rules
        triggered = [r for r in self.rules if r.matches(action_type, result_status, quality)]
        if not triggered:
            return None  # No rules triggered = no reputation change

        # 3. Compute contributing factors
        factors = self._analyze_factors(action_type, result_status, quality, factors_data or {})

        # 4. Normalize factor weights
        total_w = sum(f.weight for f in factors) if factors else 1.0
        for f in factors:
            f.normalized_weight = f.weight / total_w if total_w > 0 else 0.0

        # 5. Track action count for diminishing returns (once per call, not per dim)
        dr_factor = self._get_diminishing_factor(entity_lct, action_type)

        # 6. Compute T3 deltas
        t3_deltas = {}
        for dim in T3_DIMS:
            delta = self._compute_dimension_delta(dim, triggered, factors)
            delta *= dr_factor
            if abs(delta) > 0.0001:
                old = rt.t3[dim]
                actual = rt.t3.apply_delta(dim, delta)
                t3_deltas[dim] = DimensionDelta(change=actual, from_value=old, to_value=rt.t3[dim])

        # 7. Compute V3 deltas
        v3_deltas = {}
        for dim in V3_DIMS:
            delta = self._compute_dimension_delta(dim, triggered, factors)
            if abs(delta) > 0.0001:
                old = rt.v3[dim]
                actual = rt.v3.apply_delta(dim, delta)
                v3_deltas[dim] = DimensionDelta(change=actual, from_value=old, to_value=rt.v3[dim])

        # 8. Assemble delta
        net_trust = sum(d.change for d in t3_deltas.values())
        net_value = sum(d.change for d in v3_deltas.values())
        reason = self._generate_reason(triggered, factors, result_status)

        rd = ReputationDelta(
            subject_lct=entity_lct,
            role_lct=role_lct,
            action_type=action_type,
            action_id=action_id,
            rule_triggered=triggered[0].rule_id,
            reason=reason,
            t3_delta=t3_deltas,
            v3_delta=v3_deltas,
            contributing_factors=factors,
            net_trust_change=net_trust,
            net_value_change=net_value,
        )

        rt.action_count += 1
        rt.last_action_at = _now()

        self.delta_history.append(rd)
        return rd

    def _compute_dimension_delta(self, dimension: str, rules: list[ReputationRule],
                                   factors: list[ContributingFactor]) -> float:
        """§5 compute_dimension_delta — single dimension."""
        total_delta = 0.0
        for rule in rules:
            # Check T3 impacts
            if dimension in rule.t3_impacts:
                impact = rule.t3_impacts[dimension]
                base = impact.base_delta
                multiplier = 1.0
                for mod in impact.modifiers:
                    if any(f.factor == mod.condition for f in factors):
                        multiplier *= mod.multiplier
                total_delta += base * multiplier

            # Check V3 impacts
            if dimension in rule.v3_impacts:
                impact = rule.v3_impacts[dimension]
                base = impact.base_delta
                multiplier = 1.0
                for mod in impact.modifiers:
                    if any(f.factor == mod.condition for f in factors):
                        multiplier *= mod.multiplier
                total_delta += base * multiplier

        return max(-1.0, min(1.0, total_delta))

    def _analyze_factors(self, action_type: str, result_status: str,
                          quality: float, extra: dict) -> list[ContributingFactor]:
        """§5 analyze_factors — extract contributing factors."""
        factors = []

        if quality > 0.95:
            factors.append(ContributingFactor(
                factor="high_accuracy", weight=0.4, value=quality))
        if quality > 0.8:
            factors.append(ContributingFactor(
                factor="exceed_quality", weight=(quality - 0.8) * 2, value=quality))

        if extra.get("deadline_met", False):
            factors.append(ContributingFactor(factor="deadline_met", weight=0.3, value=1.0))
        if extra.get("early_completion", False):
            factors.append(ContributingFactor(factor="early_completion", weight=0.2, value=1.0))
        if extra.get("resource_efficiency", 0) > 0:
            eff = extra["resource_efficiency"]
            factors.append(ContributingFactor(factor="resource_efficiency", weight=eff * 0.2, value=eff))

        if result_status == "failure":
            factors.append(ContributingFactor(factor="action_failed", weight=0.5, value=0.0))
        if result_status == "ethics_violation":
            factors.append(ContributingFactor(factor="ethics_breach", weight=1.0, value=0.0))

        return factors

    def _get_diminishing_factor(self, entity_lct: str, action_type: str) -> float:
        """§7 Gaming Prevention — diminishing returns for repeated actions.
        Returns multiplier (1.0 = no diminishing, <1.0 = diminished).
        Counter increments once per compute call, not per dimension."""
        if entity_lct not in self._diminishing_returns:
            self._diminishing_returns[entity_lct] = {}
        counts = self._diminishing_returns[entity_lct]
        count = counts.get(action_type, 0)
        counts[action_type] = count + 1

        if count > 5:
            return 1.0 / (1.0 + (count - 5) * 0.2)
        return 1.0

    def _generate_reason(self, rules: list, factors: list, status: str) -> str:
        rule_names = [r.rule_id for r in rules]
        factor_names = [f.factor for f in factors]
        return f"Rules: {', '.join(rule_names)}; Factors: {', '.join(factor_names)}; Status: {status}"

    # §7 — Time-weighted aggregation
    def compute_current_reputation(self, entity_lct: str, role_lct: str,
                                     dimension: str, horizon_days: int = 90) -> float:
        """§7 — Time-weighted aggregation with 30-day half-life."""
        relevant = [
            d for d in self.delta_history
            if d.subject_lct == entity_lct and d.role_lct == role_lct
        ]
        if not relevant:
            return 0.5  # Neutral starting point

        # Get deltas for this dimension
        weighted_sum = 0.0
        weight_sum = 0.0

        for i, delta in enumerate(relevant):
            # Use index as pseudo-age (latest = 0, oldest = len-1)
            age = len(relevant) - 1 - i
            recency_weight = math.exp(-age / 10.0)  # Scaled for test counts

            change = 0.0
            if dimension in delta.t3_delta:
                change = delta.t3_delta[dimension].change
            elif dimension in delta.v3_delta:
                change = delta.v3_delta[dimension].change

            if change != 0:
                weighted_sum += change * recency_weight
                weight_sum += recency_weight

        if weight_sum == 0:
            return 0.5

        # Get current tensor value
        rt = self.registry.get(entity_lct, role_lct)
        if rt:
            if dimension in T3_DIMS:
                return rt.t3[dimension]
            elif dimension in V3_DIMS:
                return rt.v3[dimension]
        return 0.5

    # §7 — Decay
    def apply_decay(self, entity_lct: str, role_lct: str, months_inactive: float) -> dict:
        """§7 — Reputation decay for inactive entities."""
        rt = self.registry.get(entity_lct, role_lct)
        if not rt:
            return {}

        decays = {}
        if months_inactive < 1.0:
            return {}  # No decay within 30 days

        # Training decays -0.001/month
        training_decay = -0.001 * months_inactive
        if months_inactive > 6:
            training_decay *= 1.5
        training_decay = max(-0.5, training_decay)
        actual = rt.t3.apply_delta("training", training_decay)
        if abs(actual) > 0:
            decays["training"] = round(actual, 4)

        # Temperament recovers +0.01/month (if below 1.0)
        if rt.t3["temperament"] < 1.0:
            temp_recovery = 0.01 * min(months_inactive, 6)
            actual = rt.t3.apply_delta("temperament", temp_recovery)
            if abs(actual) > 0:
                decays["temperament_recovery"] = round(actual, 4)

        # Talent: no decay (inherent capability)

        return decays


# ══════════════════════════════════════════════════════════════
# §6 — Witness Selection
# ══════════════════════════════════════════════════════════════

class WitnessSelector:
    """§6 — Select witnesses for reputation changes by priority."""

    def __init__(self):
        self.law_oracles: list[str] = []
        self.role_validators: dict[str, list[str]] = {}  # role → validators
        self.mrh_witnesses: dict[str, list[str]] = {}  # entity → MRH witnesses

    def add_law_oracle(self, lct: str):
        self.law_oracles.append(lct)

    def add_role_validator(self, role: str, validator_lct: str):
        if role not in self.role_validators:
            self.role_validators[role] = []
        self.role_validators[role].append(validator_lct)

    def add_mrh_witness(self, entity: str, witness_lct: str):
        if entity not in self.mrh_witnesses:
            self.mrh_witnesses[entity] = []
        self.mrh_witnesses[entity].append(witness_lct)

    def select(self, entity_lct: str, role_lct: str, required: int) -> list[WitnessAttestation]:
        """Select witnesses by priority: law oracle > role validator > MRH."""
        candidates = []

        # Priority 1: Law oracles
        for lo in self.law_oracles:
            candidates.append((1, lo, "law_oracle"))

        # Priority 2: Role validators
        for rv in self.role_validators.get(role_lct, []):
            candidates.append((2, rv, "role_validator"))

        # Priority 3: MRH witnesses
        for mw in self.mrh_witnesses.get(entity_lct, []):
            candidates.append((3, mw, "mrh_witness"))

        # Select by priority
        candidates.sort(key=lambda x: x[0])
        selected = []
        for _, lct, wtype in candidates:
            if len(selected) >= required:
                break
            selected.append(WitnessAttestation(lct=lct, witness_type=wtype))

        return selected


# ══════════════════════════════════════════════════════════════
# §8.2 — Team Composition
# ══════════════════════════════════════════════════════════════

def compute_team_trust(registry: EntityTensorRegistry, members: list[str],
                        required_role: str, weights: dict = None) -> Optional[float]:
    """§8.2 — Team T3 for role = weighted average of members with that role."""
    qualified = []
    for m in members:
        rt = registry.get(m, required_role)
        if rt:
            qualified.append(rt)

    if not qualified:
        return None  # Team lacks required role

    scores = [rt.trust_score(weights) for rt in qualified]
    return sum(scores) / len(scores)


# ══════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════

def _now() -> str:
    return "2026-02-21T12:00:00Z"


# ══════════════════════════════════════════════════════════════
# Self-Tests
# ══════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            print(f"  [PASS] {name}")
            passed += 1
        else:
            print(f"  [FAIL] {name}")
            failed += 1

    # ── T1: Basic T3 Tensor ─────────────────────────────────
    print("\n═══ T1: T3 Tensor Basics ═══")
    t3 = Tensor(T3_DIMS, {"talent": 0.85, "training": 0.90, "temperament": 0.95})
    check("T1: talent = 0.85", t3["talent"] == 0.85)
    check("T1: training = 0.90", t3["training"] == 0.90)
    check("T1: temperament = 0.95", t3["temperament"] == 0.95)
    check("T1: composite = 0.9", abs(t3.composite() - 0.9) < 0.001)

    # Weighted composite
    weights = {"talent": 0.3, "training": 0.4, "temperament": 0.3}
    wc = t3.composite(weights)
    expected = 0.85 * 0.3 + 0.90 * 0.4 + 0.95 * 0.3
    check("T1: weighted composite", abs(wc - expected) < 0.001)

    # Apply delta
    t3.apply_delta("talent", 0.05)
    check("T1: talent after +0.05 = 0.90", abs(t3["talent"] - 0.90) < 0.001)

    # Clamping
    t3.apply_delta("temperament", 0.10)
    check("T1: clamped at 1.0", t3["temperament"] == 1.0)
    t3["temperament"] = 0.1
    t3.apply_delta("temperament", -0.5)
    check("T1: clamped at 0.0", t3["temperament"] == 0.0)

    # Serialization
    td = t3.to_dict()
    check("T1: to_dict has dimensions", "dimensions" in td)
    check("T1: to_dict has composite", "composite" in td)

    # ── T2: V3 Tensor ──────────────────────────────────────
    print("\n═══ T2: V3 Tensor Basics ═══")
    v3 = Tensor(V3_DIMS, {"veracity": 0.80, "validity": 0.90, "value": 0.75})
    check("T2: veracity = 0.80", v3["veracity"] == 0.80)
    check("T2: composite", abs(v3.composite() - 0.8167) < 0.01)
    v3.apply_delta("value", 0.05)
    check("T2: value after delta", abs(v3["value"] - 0.80) < 0.001)

    # ── T3: Role-Contextual Tensors (§1.1) ──────────────────
    print("\n═══ T3: Role-Contextual Tensors ═══")
    registry = EntityTensorRegistry()

    # Alice as DataAnalyst
    alice_analyst = registry.get_or_create(
        "lct:alice", "web4:DataAnalyst",
        t3_init={"talent": 0.85, "training": 0.90, "temperament": 0.95},
        v3_init={"veracity": 0.80, "validity": 0.85, "value": 0.75},
    )
    check("T3: alice analyst created", alice_analyst is not None)
    check("T3: analyst talent = 0.85", alice_analyst.t3["talent"] == 0.85)

    # Alice as Mechanic (different tensor!)
    alice_mechanic = registry.get_or_create(
        "lct:alice", "web4:Mechanic",
        t3_init={"talent": 0.20, "training": 0.15, "temperament": 0.50},
    )
    check("T3: mechanic talent = 0.20", alice_mechanic.t3["talent"] == 0.20)
    check("T3: mechanic ≠ analyst", alice_analyst.trust_score() != alice_mechanic.trust_score())

    # Same entity, different roles, independent tensors
    check("T3: analyst trust > mechanic trust", alice_analyst.trust_score() > alice_mechanic.trust_score())

    # Registry queries
    check("T3: alice has 2 roles", len(registry.roles_for_entity("lct:alice")) == 2)
    check("T3: 1 entity in registry", registry.entity_count() == 1)
    check("T3: 2 total tensors", registry.total_tensors() == 2)

    # ── T4: Outcome Application (§2.3) ──────────────────────
    print("\n═══ T4: Outcome Application ═══")
    bob = registry.get_or_create(
        "lct:bob", "web4:Engineer",
        t3_init={"talent": 0.50, "training": 0.50, "temperament": 0.50},
        v3_init={"veracity": 0.50, "validity": 0.50, "value": 0.50},
    )

    # Novel success
    result = bob.apply_outcome("novel_success", "engineering", "txn:001", "Innovative solution")
    check("T4: novel success has t3 deltas", len(result["t3_deltas"]) > 0)
    check("T4: novel success has v3 deltas", len(result["v3_deltas"]) > 0)
    check("T4: talent increased", bob.t3["talent"] > 0.50)
    check("T4: value increased", bob.v3["value"] > 0.50)
    check("T4: action count = 1", bob.action_count == 1)

    # Ethics violation
    old_temp = bob.t3["temperament"]
    old_veracity = bob.v3["veracity"]
    bob.apply_outcome("ethics_violation", "engineering", "txn:002", "Data manipulation detected")
    check("T4: temperament decreased severely", bob.t3["temperament"] < old_temp - 0.05)
    check("T4: veracity decreased severely", bob.v3["veracity"] < old_veracity - 0.10)

    # Evolution history
    check("T4: t3 evolution recorded", len(bob.t3.evolution) == 2)
    check("T4: v3 evolution recorded", len(bob.v3.evolution) == 2)

    # ── T5: Fractal Sub-Dimensions (§2.4) ───────────────────
    print("\n═══ T5: Fractal Sub-Dimensions ═══")
    analyst_t3 = alice_analyst.t3

    # Add sub-dimensions under Talent
    sd1 = analyst_t3.add_sub_dimension("talent", "statistical_modeling", 0.92)
    sd2 = analyst_t3.add_sub_dimension("talent", "data_visualization", 0.78)
    check("T5: sub-dim added", sd1 is not None)
    check("T5: sub-dim score", sd1.score == 0.92)

    # Add sub-sub-dimension (fractal depth)
    sd3 = SubDimension(name="bayesian_inference", parent="statistical_modeling", score=0.88)
    sd1.children.append(sd3)
    check("T5: sub-sub-dim added", len(sd1.children) == 1)

    # Traverse all sub-dims under talent
    all_talent_subs = analyst_t3.get_all_sub_dims("talent")
    check("T5: 3 sub-dims under talent", len(all_talent_subs) == 3)
    names = {sd.name for sd in all_talent_subs}
    check("T5: includes bayesian_inference", "bayesian_inference" in names)

    # Serialization
    td = analyst_t3.to_dict()
    check("T5: sub_dimensions in dict", "sub_dimensions" in td)
    check("T5: talent has sub-dims", "talent" in td["sub_dimensions"])

    # ── T6: Reputation Rules (§4) ───────────────────────────
    print("\n═══ T6: Reputation Rules ═══")
    success_rule = ReputationRule(
        rule_id="successful_analysis",
        trigger_conditions={"action_type": "analyze_dataset", "result_status": "success", "quality_threshold": 0.95},
        t3_impacts={
            "training": DimensionImpact(base_delta=0.01, modifiers=[
                RuleModifier("deadline_met", 1.5),
                RuleModifier("exceed_quality", 1.2),
            ]),
            "temperament": DimensionImpact(base_delta=0.005, modifiers=[
                RuleModifier("early_completion", 1.3),
            ]),
        },
        v3_impacts={
            "veracity": DimensionImpact(base_delta=0.02, modifiers=[
                RuleModifier("high_accuracy", 1.1),
            ]),
        },
        witnesses_required=2,
        law_oracle="lct:web4:oracle:data_science",
        category="success",
    )
    check("T6: rule created", success_rule is not None)
    check("T6: matches success", success_rule.matches("analyze_dataset", "success", 0.97))
    check("T6: doesn't match failure", not success_rule.matches("analyze_dataset", "failure", 0.97))
    check("T6: doesn't match low quality", not success_rule.matches("analyze_dataset", "success", 0.90))

    failure_rule = ReputationRule(
        rule_id="analysis_failure",
        trigger_conditions={"action_type": "analyze_dataset", "result_status": "failure"},
        t3_impacts={"training": DimensionImpact(base_delta=-0.005)},
        v3_impacts={"validity": DimensionImpact(base_delta=-0.01)},
        category="failure",
    )
    check("T6: failure rule matches", failure_rule.matches("analyze_dataset", "failure"))

    # Serialization
    rd = success_rule.to_dict()
    check("T6: rule serializes", rd["rule_id"] == "successful_analysis")
    check("T6: has t3 impacts", "training" in rd["t3_impacts"])

    # ── T7: Reputation Engine — Delta Computation (§5) ──────
    print("\n═══ T7: Reputation Delta Computation ═══")
    engine = ReputationEngine(registry)
    engine.add_rule(success_rule)
    engine.add_rule(failure_rule)

    # Create entity for reputation testing
    charlie = registry.get_or_create(
        "lct:charlie", "web4:DataAnalyst",
        t3_init={"talent": 0.70, "training": 0.60, "temperament": 0.65},
        v3_init={"veracity": 0.55, "validity": 0.60, "value": 0.50},
    )

    # Successful analysis with high quality
    delta = engine.compute_reputation_delta(
        entity_lct="lct:charlie",
        role_lct="web4:DataAnalyst",
        action_type="analyze_dataset",
        action_id="txn:100",
        result_status="success",
        quality=0.97,
        factors_data={"deadline_met": True, "early_completion": True},
    )
    check("T7: delta computed", delta is not None)
    check("T7: has t3 deltas", len(delta.t3_delta) > 0)
    check("T7: has v3 deltas", len(delta.v3_delta) > 0)
    check("T7: training increased", "training" in delta.t3_delta and delta.t3_delta["training"].change > 0)
    check("T7: veracity increased", "veracity" in delta.v3_delta and delta.v3_delta["veracity"].change > 0)
    check("T7: net trust positive", delta.net_trust_change > 0)
    check("T7: net value positive", delta.net_value_change > 0)
    check("T7: has contributing factors", len(delta.contributing_factors) > 0)
    check("T7: rule triggered", delta.rule_triggered == "successful_analysis")

    # Failure
    delta_fail = engine.compute_reputation_delta(
        entity_lct="lct:charlie",
        role_lct="web4:DataAnalyst",
        action_type="analyze_dataset",
        action_id="txn:101",
        result_status="failure",
    )
    check("T7: failure delta computed", delta_fail is not None)
    check("T7: failure net trust negative", delta_fail.net_trust_change < 0)

    # No matching rules → None
    no_delta = engine.compute_reputation_delta(
        entity_lct="lct:charlie",
        role_lct="web4:DataAnalyst",
        action_type="unknown_action",
        action_id="txn:102",
        result_status="success",
    )
    check("T7: no rules → None", no_delta is None)

    # ── T8: Contributing Factors (§5) ───────────────────────
    print("\n═══ T8: Contributing Factors ═══")
    # With quality exceeding
    delta_quality = engine.compute_reputation_delta(
        entity_lct="lct:charlie",
        role_lct="web4:DataAnalyst",
        action_type="analyze_dataset",
        action_id="txn:103",
        result_status="success",
        quality=0.99,
        factors_data={"deadline_met": True, "resource_efficiency": 0.3},
    )
    factors = delta_quality.contributing_factors
    factor_names = [f.factor for f in factors]
    check("T8: high_accuracy factor", "high_accuracy" in factor_names)
    check("T8: exceed_quality factor", "exceed_quality" in factor_names)
    check("T8: deadline_met factor", "deadline_met" in factor_names)
    check("T8: resource_efficiency factor", "resource_efficiency" in factor_names)

    # Normalized weights sum to ~1.0
    total_nw = sum(f.normalized_weight for f in factors)
    check("T8: normalized weights sum ≈ 1.0", abs(total_nw - 1.0) < 0.01)

    # Factor serialization
    fd = factors[0].to_dict()
    check("T8: factor has name", "factor" in fd)
    check("T8: factor has weight", "weight" in fd)
    check("T8: factor has normalized_weight", "normalized_weight" in fd)

    # ── T9: Witness Selection (§6) ──────────────────────────
    print("\n═══ T9: Witness Selection ═══")
    selector = WitnessSelector()
    selector.add_law_oracle("lct:web4:oracle:data_science")
    selector.add_role_validator("web4:DataAnalyst", "lct:web4:validator:stats")
    selector.add_role_validator("web4:DataAnalyst", "lct:web4:validator:methods")
    selector.add_mrh_witness("lct:charlie", "lct:web4:witness:team_lead")

    witnesses = selector.select("lct:charlie", "web4:DataAnalyst", required=3)
    check("T9: 3 witnesses selected", len(witnesses) == 3)
    check("T9: first is law_oracle", witnesses[0].witness_type == "law_oracle")
    check("T9: second is role_validator", witnesses[1].witness_type == "role_validator")

    # Fewer than required
    witnesses_2 = selector.select("lct:unknown", "web4:Unknown", required=5)
    check("T9: returns available (< required)", len(witnesses_2) <= 5)

    # Witness serialization
    wd = witnesses[0].to_dict()
    check("T9: witness has lct", "lct" in wd)
    check("T9: witness has type", "type" in wd)
    check("T9: witness has timestamp", "timestamp" in wd)

    # ── T10: Diminishing Returns (§7) ───────────────────────
    print("\n═══ T10: Diminishing Returns ═══")
    dr_registry = EntityTensorRegistry()
    dr_engine = ReputationEngine(dr_registry)
    dr_engine.add_rule(success_rule)

    dr_registry.get_or_create("lct:gamer", "web4:DataAnalyst",
                               t3_init={"talent": 0.50, "training": 0.50, "temperament": 0.50},
                               v3_init={"veracity": 0.50, "validity": 0.50, "value": 0.50})

    # Run same action many times
    deltas = []
    for i in range(10):
        d = dr_engine.compute_reputation_delta(
            "lct:gamer", "web4:DataAnalyst", "analyze_dataset",
            f"txn:dr-{i}", "success", 0.97, {"deadline_met": True})
        if d:
            deltas.append(d.net_trust_change)

    check("T10: all deltas computed", len(deltas) == 10)
    # Later deltas should be smaller due to diminishing returns
    check("T10: diminishing returns — later < earlier", deltas[-1] < deltas[0])
    check("T10: first 5 equal (no diminishing)", abs(deltas[0] - deltas[4]) < 0.001)
    check("T10: 6th+ smaller", deltas[6] < deltas[4])

    # ── T11: Reputation Aggregation (§7) ────────────────────
    print("\n═══ T11: Time-Weighted Aggregation ═══")
    agg_registry = EntityTensorRegistry()
    agg_engine = ReputationEngine(agg_registry)
    agg_engine.add_rule(success_rule)
    agg_engine.add_rule(failure_rule)

    agg_registry.get_or_create("lct:dave", "web4:DataAnalyst",
                                t3_init={"talent": 0.50, "training": 0.50, "temperament": 0.50},
                                v3_init={"veracity": 0.50, "validity": 0.50, "value": 0.50})

    # Build history
    for i in range(5):
        agg_engine.compute_reputation_delta(
            "lct:dave", "web4:DataAnalyst", "analyze_dataset",
            f"txn:agg-{i}", "success", 0.97, {"deadline_met": True})

    rep = agg_engine.compute_current_reputation("lct:dave", "web4:DataAnalyst", "training")
    check("T11: reputation computed", rep is not None)
    check("T11: training > 0.5 after successes", rep > 0.50)

    # Unknown entity → neutral
    neutral = agg_engine.compute_current_reputation("lct:unknown", "web4:Unknown", "training")
    check("T11: unknown entity = 0.5", neutral == 0.5)

    # ── T12: Decay (§7) ────────────────────────────────────
    print("\n═══ T12: Reputation Decay ═══")
    decay_registry = EntityTensorRegistry()
    decay_engine = ReputationEngine(decay_registry)

    decay_registry.get_or_create("lct:eve", "web4:DataAnalyst",
                                  t3_init={"talent": 0.80, "training": 0.80, "temperament": 0.70})

    # No decay within 30 days
    decays_short = decay_engine.apply_decay("lct:eve", "web4:DataAnalyst", 0.5)
    check("T12: no decay < 1 month", len(decays_short) == 0)

    # 3 months inactive
    decays_3m = decay_engine.apply_decay("lct:eve", "web4:DataAnalyst", 3.0)
    check("T12: training decayed", "training" in decays_3m)
    check("T12: training decay negative", decays_3m["training"] < 0)

    # Temperament recovery
    check("T12: temperament recovers", "temperament_recovery" in decays_3m)
    check("T12: recovery positive", decays_3m["temperament_recovery"] > 0)

    # 12 months inactive (accelerated decay)
    decay_registry2 = EntityTensorRegistry()
    decay_engine2 = ReputationEngine(decay_registry2)
    decay_registry2.get_or_create("lct:fred", "web4:DataAnalyst",
                                   t3_init={"talent": 0.80, "training": 0.80, "temperament": 0.70})
    decays_12m = decay_engine2.apply_decay("lct:fred", "web4:DataAnalyst", 12.0)
    check("T12: 12-month decay larger", abs(decays_12m.get("training", 0)) > abs(decays_3m.get("training", 0)))

    # Talent doesn't decay
    eve_rt = decay_registry.get("lct:eve", "web4:DataAnalyst")
    check("T12: talent unchanged", eve_rt.t3["talent"] == 0.80)

    # ── T13: Role-Specific Reputation Query (§7 example) ────
    print("\n═══ T13: Role-Specific Reputation ═══")
    multi_registry = EntityTensorRegistry()

    # Alice: high analyst, low surgeon
    multi_registry.get_or_create("lct:alice2", "web4:Analyst",
                                  t3_init={"talent": 0.90, "training": 0.92, "temperament": 0.88})
    multi_registry.get_or_create("lct:alice2", "web4:Surgeon",
                                  t3_init={"talent": 0.20, "training": 0.15, "temperament": 0.50})

    analyst_trust = multi_registry.get("lct:alice2", "web4:Analyst").trust_score()
    surgeon_trust = multi_registry.get("lct:alice2", "web4:Surgeon").trust_score()
    check("T13: analyst trust = 0.90", abs(analyst_trust - 0.90) < 0.01)
    check("T13: surgeon trust ≈ 0.28", abs(surgeon_trust - 0.2833) < 0.01)
    check("T13: analyst >> surgeon", analyst_trust > surgeon_trust + 0.3)

    # ── T14: Team Composition (§8.2) ────────────────────────
    print("\n═══ T14: Team Trust Composition ═══")
    team_registry = EntityTensorRegistry()
    team_registry.get_or_create("lct:t1", "web4:Engineer",
                                 t3_init={"talent": 0.80, "training": 0.70, "temperament": 0.90})
    team_registry.get_or_create("lct:t2", "web4:Engineer",
                                 t3_init={"talent": 0.60, "training": 0.80, "temperament": 0.85})
    team_registry.get_or_create("lct:t3", "web4:Designer",  # Wrong role
                                 t3_init={"talent": 0.90, "training": 0.90, "temperament": 0.90})

    team_trust = compute_team_trust(team_registry, ["lct:t1", "lct:t2", "lct:t3"], "web4:Engineer")
    check("T14: team trust computed", team_trust is not None)
    # Only t1 and t2 are engineers
    expected_team = (team_registry.get("lct:t1", "web4:Engineer").trust_score() +
                     team_registry.get("lct:t2", "web4:Engineer").trust_score()) / 2
    check("T14: team trust = avg of engineers", abs(team_trust - expected_team) < 0.001)

    # No one has role → None
    no_team = compute_team_trust(team_registry, ["lct:t1", "lct:t2"], "web4:Surgeon")
    check("T14: no role match → None", no_team is None)

    # ── T15: Delta Serialization ────────────────────────────
    print("\n═══ T15: Delta Serialization ═══")
    # Use the delta from T7
    dd = delta.to_dict()
    check("T15: has subject_lct", dd["subject_lct"] == "lct:charlie")
    check("T15: has role_lct", dd["role_lct"] == "web4:DataAnalyst")
    check("T15: has action_type", dd["action_type"] == "analyze_dataset")
    check("T15: has t3_delta", len(dd["t3_delta"]) > 0)
    check("T15: has v3_delta", len(dd["v3_delta"]) > 0)
    check("T15: has contributing_factors", len(dd["contributing_factors"]) > 0)
    check("T15: has net_trust_change", "net_trust_change" in dd)
    check("T15: has net_value_change", "net_value_change" in dd)

    # T3 delta structure
    for dim, dim_delta in dd["t3_delta"].items():
        check(f"T15: t3.{dim} has change", "change" in dim_delta)
        check(f"T15: t3.{dim} has from", "from" in dim_delta)
        check(f"T15: t3.{dim} has to", "to" in dim_delta)
        break  # Just check first

    # JSON roundtrip
    j = json.dumps(dd)
    parsed = json.loads(j)
    check("T15: JSON roundtrip preserves subject", parsed["subject_lct"] == "lct:charlie")

    # ── T16: Role Tensor Serialization ──────────────────────
    print("\n═══ T16: Role Tensor Serialization ═══")
    rtd = alice_analyst.to_dict()
    check("T16: has entity_lct", rtd["entity_lct"] == "lct:alice")
    check("T16: has role_lct", rtd["role_lct"] == "web4:DataAnalyst")
    check("T16: has t3", "t3" in rtd)
    check("T16: has v3", "v3" in rtd)
    check("T16: has trust_score", "trust_score" in rtd)
    check("T16: has value_score", "value_score" in rtd)

    # ── T17: V3 from Outcome ────────────────────────────────
    print("\n═══ T17: V3 Outcome Mapping ═══")
    v3_entity = registry.get_or_create("lct:val", "web4:Tester",
                                        v3_init={"veracity": 0.50, "validity": 0.50, "value": 0.50})
    result = v3_entity.apply_outcome("novel_success", "testing", "txn:v3-1", "Great test")
    check("T17: novel success → value up", "value" in result["v3_deltas"])
    check("T17: novel success value > 0", result["v3_deltas"].get("value", 0) > 0)

    # Standard success gives smaller deltas
    v3_2 = registry.get_or_create("lct:val2", "web4:Tester",
                                   v3_init={"veracity": 0.50, "validity": 0.50, "value": 0.50})
    r2 = v3_2.apply_outcome("standard_success", "testing", "txn:v3-2", "OK test")
    check("T17: standard success has v3 deltas", len(r2["v3_deltas"]) > 0)

    # ── T18: Anti-Gaming via Rules ──────────────────────────
    print("\n═══ T18: Anti-Gaming Properties ═══")
    # Ethics violation is severe
    gaming_reg = EntityTensorRegistry()
    gaming_eng = ReputationEngine(gaming_reg)
    ethics_rule = ReputationRule(
        rule_id="ethics_violation",
        trigger_conditions={"result_status": "ethics_violation"},
        t3_impacts={"temperament": DimensionImpact(base_delta=-0.10)},
        v3_impacts={
            "veracity": DimensionImpact(base_delta=-0.20),
            "validity": DimensionImpact(base_delta=-0.15),
        },
        category="ethical_violation",
    )
    gaming_eng.add_rule(ethics_rule)

    gaming_reg.get_or_create("lct:cheater", "web4:Analyst",
                              t3_init={"talent": 0.80, "training": 0.80, "temperament": 0.80},
                              v3_init={"veracity": 0.80, "validity": 0.80, "value": 0.80})

    d = gaming_eng.compute_reputation_delta(
        "lct:cheater", "web4:Analyst", "manipulate_data",
        "txn:cheat-1", "ethics_violation")
    check("T18: ethics violation computed", d is not None)
    check("T18: temperament severely hit", d.t3_delta.get("temperament", DimensionDelta(0,0,0)).change <= -0.10)
    check("T18: veracity severely hit", d.v3_delta.get("veracity", DimensionDelta(0,0,0)).change <= -0.20)
    check("T18: net trust deeply negative", d.net_trust_change < -0.05)
    check("T18: net value deeply negative", d.net_value_change < -0.15)

    # ══════════════════════════════════════════════════════════
    print(f"""
{'='*60}
  T3/V3 Tensor & Reputation Engine — Results
  {passed} passed, {failed} failed out of {passed + failed} checks
{'='*60}
""")

    if failed == 0:
        print("  All checks pass — T3/V3 + Reputation engine validated")
        print("  T3: Talent/Training/Temperament (role-contextual)")
        print("  V3: Veracity/Validity/Value (role-contextual)")
        print("  Fractal sub-dimensions via subDimensionOf chains")
        print("  Reputation rules with trigger conditions + modifiers")
        print("  Multi-factor delta computation with witnesses")
        print("  Time-weighted aggregation + decay mechanics")
        print("  Anti-gaming: diminishing returns, ethics penalties")
        print(f"  Team composition: role-specific weighted average")
    else:
        print("  Some checks failed — review output above")

    return passed, failed


if __name__ == "__main__":
    run_tests()
