#!/usr/bin/env python3
"""
Web4 Reputation Computation — Reference Implementation
========================================================

Implements: web4-standard/core-spec/reputation-computation.md (759 lines)

Full R7 reputation computation system:
  §1  Reputation Delta Structure — multi-dimensional T3/V3 deltas
  §2  Trust Tensor (T3) — Talent / Training / Temperament
  §3  Value Tensor (V3) — Veracity / Validity / Value
  §4  Reputation Rules — rule-triggered changes with modifiers
  §5  Multi-Factor Computation — weighted contributing factors
  §6  Witnessing — independent validation of reputation changes
  §7  Aggregation — time-weighted accumulation and decay
  §8  Implementation — complete R7 reputation engine
  §9  Security — Sybil resistance, gaming prevention

Run: python reputation_computation.py
"""

from __future__ import annotations
import hashlib
import json
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional


# ============================================================
# §1  REPUTATION DELTA STRUCTURE
# ============================================================

@dataclass
class DimensionDelta:
    """Change in a single T3 or V3 dimension."""
    change: float = 0.0
    from_value: float = 0.0
    to_value: float = 0.0

    def to_dict(self) -> dict:
        return {"change": self.change, "from": self.from_value, "to": self.to_value}


@dataclass
class RolePairingInMRH:
    """MRH role pairing context — reputation is role-contextualized."""
    entity: str = ""      # entity LCT
    role: str = ""        # role LCT
    paired_at: str = ""   # ISO8601 timestamp
    mrh_link: str = ""    # link:mrh:entity→role:...


@dataclass
class ContributingFactor:
    """A factor that influenced the reputation delta."""
    factor: str = ""
    weight: float = 0.0
    normalized_weight: float = 0.0
    value: Any = None


@dataclass
class WitnessAttestation:
    """Independent witness attestation of a reputation change."""
    lct: str = ""
    witness_type: str = ""  # law_oracle, role_validator, mrh_witness
    signature: str = ""
    timestamp: str = ""
    attestation: dict = field(default_factory=dict)

    def sign(self, reputation_hash: str, action_id: str) -> WitnessAttestation:
        """Sign the reputation delta."""
        self.timestamp = datetime.utcnow().isoformat()
        self.attestation = {
            "action_id": action_id,
            "reputation_hash": reputation_hash,
            "verified": True,
            "confidence": 0.95,
        }
        payload = json.dumps(self.attestation, sort_keys=True).encode()
        self.signature = hashlib.sha256(payload + self.lct.encode()).hexdigest()
        return self


@dataclass
class ReputationDelta:
    """Complete reputation delta from an R7 transaction."""
    subject_lct: str = ""
    role_lct: str = ""
    role_pairing_in_mrh: Optional[RolePairingInMRH] = None
    action_type: str = ""
    action_target: str = ""
    action_id: str = ""
    rule_triggered: str = ""
    reason: str = ""
    t3_delta: dict[str, DimensionDelta] = field(default_factory=dict)
    v3_delta: dict[str, DimensionDelta] = field(default_factory=dict)
    contributing_factors: list[ContributingFactor] = field(default_factory=list)
    witnesses: list[WitnessAttestation] = field(default_factory=list)
    net_trust_change: float = 0.0
    net_value_change: float = 0.0
    timestamp: str = ""

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of the reputation delta."""
        payload = json.dumps({
            "subject_lct": self.subject_lct,
            "role_lct": self.role_lct,
            "action_id": self.action_id,
            "rule_triggered": self.rule_triggered,
            "net_trust_change": self.net_trust_change,
            "net_value_change": self.net_value_change,
            "timestamp": self.timestamp,
        }, sort_keys=True).encode()
        return f"sha256:{hashlib.sha256(payload).hexdigest()}"

    def to_dict(self) -> dict:
        return {
            "reputation": {
                "subject_lct": self.subject_lct,
                "role_lct": self.role_lct,
                "role_pairing_in_mrh": {
                    "entity": self.role_pairing_in_mrh.entity,
                    "role": self.role_pairing_in_mrh.role,
                    "paired_at": self.role_pairing_in_mrh.paired_at,
                    "mrh_link": self.role_pairing_in_mrh.mrh_link,
                } if self.role_pairing_in_mrh else None,
                "action_type": self.action_type,
                "action_target": self.action_target,
                "action_id": self.action_id,
                "rule_triggered": self.rule_triggered,
                "reason": self.reason,
                "t3_delta": {k: v.to_dict() for k, v in self.t3_delta.items()},
                "v3_delta": {k: v.to_dict() for k, v in self.v3_delta.items()},
                "contributing_factors": [
                    {"factor": f.factor, "weight": f.weight} for f in self.contributing_factors
                ],
                "witnesses": [
                    {"lct": w.lct, "signature": w.signature, "timestamp": w.timestamp}
                    for w in self.witnesses
                ],
                "net_trust_change": self.net_trust_change,
                "net_value_change": self.net_value_change,
                "timestamp": self.timestamp,
            }
        }


# ============================================================
# §2  TRUST TENSOR (T3) — Talent / Training / Temperament
# ============================================================

T3_DIMENSIONS = ["talent", "training", "temperament"]

@dataclass
class T3Tensor:
    """Trust Tensor: Talent / Training / Temperament."""
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    def get(self, dim: str) -> float:
        return getattr(self, dim, 0.0)

    def set(self, dim: str, value: float):
        setattr(self, dim, max(0.0, min(1.0, value)))

    def average(self) -> float:
        return (self.talent + self.training + self.temperament) / 3.0

    def apply_delta(self, deltas: dict[str, float]) -> dict[str, DimensionDelta]:
        """Apply deltas, return dimension changes."""
        changes = {}
        for dim in T3_DIMENSIONS:
            if dim in deltas and deltas[dim] != 0:
                old = self.get(dim)
                new_val = max(0.0, min(1.0, old + deltas[dim]))
                self.set(dim, new_val)
                changes[dim] = DimensionDelta(change=new_val - old, from_value=old, to_value=new_val)
        return changes

    def interpret(self) -> str:
        """Interpret T3 level per spec §2."""
        avg = self.average()
        if avg >= 0.8:
            return "maximum_trust"
        elif avg >= 0.5:
            return "potential_needs_development"
        else:
            return "high_risk"


# ============================================================
# §3  VALUE TENSOR (V3) — Veracity / Validity / Value
# ============================================================

V3_DIMENSIONS = ["veracity", "validity", "value"]

@dataclass
class V3Tensor:
    """Value Tensor: Veracity / Validity / Value."""
    veracity: float = 0.5
    validity: float = 0.5
    value: float = 0.5

    def get(self, dim: str) -> float:
        return getattr(self, dim, 0.0)

    def set(self, dim: str, val: float):
        setattr(self, dim, max(0.0, min(1.0, val)))

    def average(self) -> float:
        return (self.veracity + self.validity + self.value) / 3.0

    def apply_delta(self, deltas: dict[str, float]) -> dict[str, DimensionDelta]:
        changes = {}
        for dim in V3_DIMENSIONS:
            if dim in deltas and deltas[dim] != 0:
                old = self.get(dim)
                new_val = max(0.0, min(1.0, old + deltas[dim]))
                self.set(dim, new_val)
                changes[dim] = DimensionDelta(change=new_val - old, from_value=old, to_value=new_val)
        return changes

    def interpret(self) -> str:
        """Interpret V3 level per spec §3."""
        avg = self.average()
        if avg >= 0.8:
            return "high_quality_trustworthy"
        elif avg >= 0.5:
            return "valuable_but_needs_rigor"
        else:
            return "low_quality_untrustworthy"


# ============================================================
# §4  REPUTATION RULES
# ============================================================

class RuleCategory(Enum):
    """Rule categories from spec §4."""
    SUCCESS = "success"
    FAILURE = "failure"
    EXCEPTIONAL = "exceptional"
    ETHICAL_VIOLATION = "ethical_violation"


@dataclass
class RuleModifier:
    """Modifier that adjusts base delta based on a condition."""
    condition: str = ""
    multiplier: float = 1.0


@dataclass
class DimensionImpact:
    """Impact on a single dimension: base delta + modifiers."""
    base_delta: float = 0.0
    modifiers: list[RuleModifier] = field(default_factory=list)


@dataclass
class ReputationRule:
    """A reputation rule defined by a Law Oracle."""
    rule_id: str = ""
    category: RuleCategory = RuleCategory.SUCCESS
    trigger_conditions: dict = field(default_factory=dict)
    t3_impacts: dict[str, DimensionImpact] = field(default_factory=dict)
    v3_impacts: dict[str, DimensionImpact] = field(default_factory=dict)
    witnesses_required: int = 0
    law_oracle: str = ""

    @property
    def reputation_impact(self) -> dict:
        """Combined T3 + V3 impacts for dimension lookup."""
        combined = {}
        combined.update(self.t3_impacts)
        combined.update(self.v3_impacts)
        return combined


# ============================================================
# §5  MULTI-FACTOR COMPUTATION
# ============================================================

@dataclass
class ActionContext:
    """Context of an action for reputation computation."""
    action_type: str = ""
    target: str = ""
    constraints: dict = field(default_factory=dict)  # e.g., deadline
    resource_required: float = 0.0


@dataclass
class ActionResult:
    """Result of an action."""
    status: str = ""   # success, failure, error
    quality: float = 0.0
    accuracy: float = 0.0
    resource_consumed: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    output: dict = field(default_factory=dict)
    txn_hash: str = ""


def matches_trigger_conditions(rule: ReputationRule, action: ActionContext,
                               result: ActionResult) -> bool:
    """Check if rule trigger conditions are met."""
    conditions = rule.trigger_conditions

    if "action_type" in conditions:
        if action.action_type != conditions["action_type"]:
            return False

    if "result_status" in conditions:
        if result.status != conditions["result_status"]:
            return False

    if "quality_threshold" in conditions:
        if result.quality < conditions["quality_threshold"]:
            return False

    return True


def analyze_factors(action: ActionContext, result: ActionResult,
                    rule: ReputationRule) -> list[ContributingFactor]:
    """Analyze contributing factors per spec §5."""
    factors = []

    # Quality-based factors
    if "quality_threshold" in rule.trigger_conditions:
        threshold = rule.trigger_conditions["quality_threshold"]
        if result.quality > threshold:
            exceed_ratio = (result.quality - threshold) / max(threshold, 0.01)
            factors.append(ContributingFactor(
                factor="exceed_quality", weight=exceed_ratio, value=result.quality
            ))

    # Time-based factors
    if "deadline" in action.constraints:
        deadline = action.constraints["deadline"]
        if isinstance(deadline, datetime) and result.timestamp <= deadline:
            factors.append(ContributingFactor(
                factor="deadline_met", weight=0.3, value=True
            ))
            time_saved = (deadline - result.timestamp).total_seconds()
            if time_saved > 3600:  # > 1 hour
                factors.append(ContributingFactor(
                    factor="early_completion", weight=0.2, value=time_saved
                ))

    # Resource efficiency
    if action.resource_required > 0 and result.resource_consumed < action.resource_required:
        efficiency = 1.0 - (result.resource_consumed / action.resource_required)
        factors.append(ContributingFactor(
            factor="resource_efficiency", weight=efficiency * 0.2, value=efficiency
        ))

    # Accuracy factors
    if result.accuracy > 0.95:
        factors.append(ContributingFactor(
            factor="high_accuracy", weight=0.4, value=result.accuracy
        ))

    return factors


def factor_applies(condition: str, factors: list[ContributingFactor]) -> bool:
    """Check if a modifier condition is satisfied by the contributing factors."""
    return any(f.factor == condition for f in factors)


def compute_dimension_delta(dimension: str, rules: list[ReputationRule],
                            factors: list[ContributingFactor],
                            action: ActionContext, result: ActionResult) -> float:
    """Compute delta for a single T3 or V3 dimension (spec §5)."""
    total_delta = 0.0

    for rule in rules:
        impact_map = rule.reputation_impact
        if dimension not in impact_map:
            continue

        impact = impact_map[dimension]
        base_delta = impact.base_delta

        # Apply modifiers based on contributing factors
        multiplier = 1.0
        for modifier in impact.modifiers:
            if factor_applies(modifier.condition, factors):
                multiplier *= modifier.multiplier

        total_delta += base_delta * multiplier

    # Clamp to [-1.0, +1.0]
    return max(-1.0, min(1.0, total_delta))


def normalize_factors(factors: list[ContributingFactor]) -> list[ContributingFactor]:
    """Normalize factor weights to sum to 1.0."""
    total = sum(f.weight for f in factors)
    if total > 0:
        for f in factors:
            f.normalized_weight = f.weight / total
    return factors


def compute_reputation_delta(
    subject_lct: str,
    role_lct: str,
    action: ActionContext,
    result: ActionResult,
    rules: list[ReputationRule],
    t3: T3Tensor,
    v3: V3Tensor,
    role_pairing: Optional[RolePairingInMRH] = None,
) -> ReputationDelta:
    """
    Core reputation computation algorithm from spec §5.

    Returns empty delta if no rules are triggered.
    """
    # 1. Identify triggered rules
    triggered = [r for r in rules if matches_trigger_conditions(r, action, result)]
    if not triggered:
        return ReputationDelta(
            subject_lct=subject_lct, role_lct=role_lct,
            action_type=action.action_type, action_target=action.target,
            timestamp=datetime.utcnow().isoformat(),
        )

    # 2. Compute contributing factors
    all_factors = []
    for rule in triggered:
        rule_factors = analyze_factors(action, result, rule)
        all_factors.extend(rule_factors)

    # 3. Normalize factor weights
    all_factors = normalize_factors(all_factors)

    # 4. Compute T3 deltas
    t3_raw = {}
    for dim in T3_DIMENSIONS:
        delta = compute_dimension_delta(dim, triggered, all_factors, action, result)
        if delta != 0:
            t3_raw[dim] = delta

    t3_changes = t3.apply_delta(t3_raw)

    # 5. Compute V3 deltas
    v3_raw = {}
    for dim in V3_DIMENSIONS:
        delta = compute_dimension_delta(dim, triggered, all_factors, action, result)
        if delta != 0:
            v3_raw[dim] = delta

    v3_changes = v3.apply_delta(v3_raw)

    # 6. Assemble reputation delta
    net_trust = sum(d.change for d in t3_changes.values())
    net_value = sum(d.change for d in v3_changes.values())

    reason_parts = [r.rule_id for r in triggered]
    factor_parts = [f.factor for f in all_factors if f.weight > 0]

    delta = ReputationDelta(
        subject_lct=subject_lct,
        role_lct=role_lct,
        role_pairing_in_mrh=role_pairing,
        action_type=action.action_type,
        action_target=action.target,
        action_id=result.txn_hash or f"txn:{uuid.uuid4().hex[:16]}",
        rule_triggered=triggered[0].rule_id,
        reason=f"Rules: {', '.join(reason_parts)}; Factors: {', '.join(factor_parts)}",
        t3_delta=t3_changes,
        v3_delta=v3_changes,
        contributing_factors=all_factors,
        net_trust_change=net_trust,
        net_value_change=net_value,
        timestamp=datetime.utcnow().isoformat(),
    )

    return delta


# ============================================================
# §6  WITNESSING REPUTATION CHANGES
# ============================================================

@dataclass
class WitnessCandidate:
    """Candidate witness for reputation change."""
    lct: str = ""
    witness_type: str = ""
    priority: int = 3


def select_reputation_witnesses(
    rule: ReputationRule,
    role_validators: list[str] | None = None,
    mrh_witnesses: list[str] | None = None,
) -> list[WitnessCandidate]:
    """Select witnesses per spec §6."""
    required = rule.witnesses_required
    candidates = []

    # 1. Law Oracle witness (priority 1)
    if rule.law_oracle:
        candidates.append(WitnessCandidate(
            lct=rule.law_oracle, witness_type="law_oracle", priority=1
        ))

    # 2. Role-specific validators (priority 2)
    for v in (role_validators or []):
        candidates.append(WitnessCandidate(
            lct=v, witness_type="role_validator", priority=2
        ))

    # 3. MRH-proximate entities (priority 3)
    for w in (mrh_witnesses or []):
        candidates.append(WitnessCandidate(
            lct=w, witness_type="mrh_witness", priority=3
        ))

    # Select by priority
    selected = []
    for priority in [1, 2, 3]:
        for c in candidates:
            if c.priority == priority and len(selected) < required:
                selected.append(c)

    return selected


def create_witness_attestations(
    witnesses: list[WitnessCandidate],
    reputation_delta: ReputationDelta,
) -> list[WitnessAttestation]:
    """Create witness attestations for a reputation delta."""
    rep_hash = reputation_delta.compute_hash()
    attestations = []
    for w in witnesses:
        att = WitnessAttestation(
            lct=w.lct,
            witness_type=w.witness_type,
        ).sign(rep_hash, reputation_delta.action_id)
        attestations.append(att)
    return attestations


# ============================================================
# §7  REPUTATION AGGREGATION OVER TIME
# ============================================================

@dataclass
class StoredDelta:
    """A stored reputation delta for time-weighted aggregation."""
    dimension: str = ""
    change: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    role_lct: str = ""


class ReputationStore:
    """Stores and aggregates reputation deltas over time."""

    def __init__(self):
        self.deltas: list[StoredDelta] = []
        self.last_action: dict[tuple[str, str], datetime] = {}  # (entity, role) → timestamp

    def store_delta(self, entity_lct: str, role_lct: str,
                    rep_delta: ReputationDelta):
        """Store a reputation delta for later aggregation."""
        now = datetime.utcnow()
        self.last_action[(entity_lct, role_lct)] = now

        for dim, dd in rep_delta.t3_delta.items():
            self.deltas.append(StoredDelta(
                dimension=dim, change=dd.change,
                timestamp=now, role_lct=role_lct,
            ))
        for dim, dd in rep_delta.v3_delta.items():
            self.deltas.append(StoredDelta(
                dimension=dim, change=dd.change,
                timestamp=now, role_lct=role_lct,
            ))

    def compute_current_reputation(
        self, entity_lct: str, role_lct: str, dimension: str,
        time_horizon_days: int = 90, reference_time: datetime | None = None,
    ) -> float:
        """
        Time-weighted aggregation per spec §7.

        Returns: Current reputation value [0.0, 1.0] for entity in role.
        """
        now = reference_time or datetime.utcnow()
        cutoff = now - timedelta(days=time_horizon_days)

        matching = [
            d for d in self.deltas
            if d.role_lct == role_lct and d.dimension == dimension and d.timestamp >= cutoff
        ]

        if not matching:
            return 0.5  # Neutral for new role pairings

        weighted_sum = 0.0
        weight_sum = 0.0

        for d in matching:
            age_days = max(0.0, (now - d.timestamp).total_seconds() / 86400.0)
            recency_weight = math.exp(-age_days / 30.0)  # 30-day half-life
            weighted_sum += d.change * recency_weight
            weight_sum += recency_weight

        current = weighted_sum / weight_sum if weight_sum > 0 else 0.5
        return max(0.0, min(1.0, current))

    def apply_reputation_decay(
        self, entity_lct: str, role_lct: str, dimension: str,
        reference_time: datetime | None = None,
    ) -> float:
        """
        Apply natural decay for inactivity per spec §7.

        Returns decay amount (negative).
        """
        now = reference_time or datetime.utcnow()
        last = self.last_action.get((entity_lct, role_lct))

        if not last:
            return 0.0

        days_inactive = (now - last).total_seconds() / 86400.0

        if days_inactive < 30:
            return 0.0

        months_inactive = days_inactive / 30.0
        decay = -0.01 * months_inactive

        # Accelerate after 6 months
        if months_inactive > 6:
            decay *= 1.5

        return max(-0.5, decay)


# ============================================================
# §9  SECURITY — Gaming Prevention
# ============================================================

class GamingPrevention:
    """Anti-gaming measures per spec §9."""

    def __init__(self):
        self.action_history: dict[tuple[str, str], list[datetime]] = {}  # (entity, action) → timestamps
        self.diminishing_factor: float = 0.8  # Per spec: 0.8^(n-1)
        self.diminishing_floor: float = 0.1   # Per MEMORY.md

    def compute_diminishing_multiplier(self, entity_lct: str, action_type: str,
                                       window_days: int = 30) -> float:
        """
        Diminishing returns for repeated identical actions.
        Per memory: 0.8^(n-1) with floor at 0.1
        """
        key = (entity_lct, action_type)
        history = self.action_history.get(key, [])
        cutoff = datetime.utcnow() - timedelta(days=window_days)
        recent = [t for t in history if t >= cutoff]
        n = len(recent) + 1  # Current action is n-th
        multiplier = self.diminishing_factor ** (n - 1)
        return max(self.diminishing_floor, multiplier)

    def record_action(self, entity_lct: str, action_type: str):
        key = (entity_lct, action_type)
        self.action_history.setdefault(key, []).append(datetime.utcnow())

    def check_self_attestation(self, subject_lct: str,
                               witness_lcts: list[str]) -> bool:
        """No self-attestation: witnesses must be independent."""
        return subject_lct not in witness_lcts

    def check_quality_threshold(self, quality: float, threshold: float) -> bool:
        """Minimum standards must be met."""
        return quality >= threshold

    @staticmethod
    def sybil_cost(num_identities: int, hardware_cost: float = 250.0,
                   atp_cost: float = 50.0) -> float:
        """Economic cost of Sybil attack per spec §9."""
        return num_identities * (hardware_cost + atp_cost)

    @staticmethod
    def atp_farming_fee(amount: float, fee_rate: float = 0.05) -> float:
        """5% fee per transfer makes circular flows unprofitable."""
        return amount * fee_rate


# ============================================================
# §8  COMPLETE R7 REPUTATION ENGINE
# ============================================================

class ReputationEngine:
    """Complete R7 reputation engine integrating all components."""

    def __init__(self):
        self.rules: list[ReputationRule] = []
        self.store = ReputationStore()
        self.gaming = GamingPrevention()
        self.entity_t3: dict[str, dict[str, T3Tensor]] = {}  # entity → {role → T3}
        self.entity_v3: dict[str, dict[str, V3Tensor]] = {}  # entity → {role → V3}

    def register_rule(self, rule: ReputationRule):
        self.rules.append(rule)

    def get_or_create_t3(self, entity_lct: str, role_lct: str) -> T3Tensor:
        entity_roles = self.entity_t3.setdefault(entity_lct, {})
        if role_lct not in entity_roles:
            entity_roles[role_lct] = T3Tensor()
        return entity_roles[role_lct]

    def get_or_create_v3(self, entity_lct: str, role_lct: str) -> V3Tensor:
        entity_roles = self.entity_v3.setdefault(entity_lct, {})
        if role_lct not in entity_roles:
            entity_roles[role_lct] = V3Tensor()
        return entity_roles[role_lct]

    def process_action(
        self,
        entity_lct: str,
        role_lct: str,
        action: ActionContext,
        result: ActionResult,
        role_pairing: Optional[RolePairingInMRH] = None,
        role_validators: list[str] | None = None,
        mrh_witnesses: list[str] | None = None,
    ) -> ReputationDelta:
        """Process an action and compute reputation delta."""
        t3 = self.get_or_create_t3(entity_lct, role_lct)
        v3 = self.get_or_create_v3(entity_lct, role_lct)

        # Apply diminishing returns
        diminishing = self.gaming.compute_diminishing_multiplier(
            entity_lct, action.action_type
        )

        # Compute base delta
        delta = compute_reputation_delta(
            subject_lct=entity_lct,
            role_lct=role_lct,
            action=action,
            result=result,
            rules=self.rules,
            t3=T3Tensor(t3.talent, t3.training, t3.temperament),  # copy
            v3=V3Tensor(v3.veracity, v3.validity, v3.value),      # copy
            role_pairing=role_pairing,
        )

        # Apply diminishing returns to actual T3/V3
        if diminishing < 1.0:
            t3_raw = {dim: dd.change * diminishing for dim, dd in delta.t3_delta.items()}
            v3_raw = {dim: dd.change * diminishing for dim, dd in delta.v3_delta.items()}
        else:
            t3_raw = {dim: dd.change for dim, dd in delta.t3_delta.items()}
            v3_raw = {dim: dd.change for dim, dd in delta.v3_delta.items()}

        # Apply to actual tensors
        actual_t3_changes = t3.apply_delta(t3_raw)
        actual_v3_changes = v3.apply_delta(v3_raw)

        # Update delta with actual changes (post-diminishing)
        delta.t3_delta = actual_t3_changes
        delta.v3_delta = actual_v3_changes
        delta.net_trust_change = sum(d.change for d in actual_t3_changes.values())
        delta.net_value_change = sum(d.change for d in actual_v3_changes.values())

        # Select witnesses and create attestations
        if self.rules:
            triggered = [r for r in self.rules
                         if matches_trigger_conditions(r, action, result)]
            if triggered:
                witnesses = select_reputation_witnesses(
                    triggered[0], role_validators, mrh_witnesses
                )
                attestations = create_witness_attestations(witnesses, delta)
                delta.witnesses = attestations

        # Store delta
        self.store.store_delta(entity_lct, role_lct, delta)

        # Record action for gaming prevention
        self.gaming.record_action(entity_lct, action.action_type)

        return delta

    def query_reputation(self, entity_lct: str, role_lct: str,
                         dimension: str, time_horizon_days: int = 90) -> float:
        """Query current reputation for entity in role."""
        return self.store.compute_current_reputation(
            entity_lct, role_lct, dimension, time_horizon_days
        )


# ============================================================
# TESTS
# ============================================================

def run_tests():
    passed = 0
    failed = 0
    total = 0

    def check(name: str, condition: bool):
        nonlocal passed, failed, total
        total += 1
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name}")

    # ── T1: T3 Tensor Basics ──
    print("T1: T3 Tensor Basics")

    t3 = T3Tensor(0.8, 0.8, 0.9)
    check("T1.1 Talent", t3.talent == 0.8)
    check("T1.2 Training", t3.training == 0.8)
    check("T1.3 Temperament", t3.temperament == 0.9)
    check("T1.4 Average", abs(t3.average() - 0.8333) < 0.01)
    check("T1.5 Interpret high", t3.interpret() == "maximum_trust")

    t3_mid = T3Tensor(0.5, 0.6, 0.7)
    check("T1.6 Interpret mid", t3_mid.interpret() == "potential_needs_development")

    t3_low = T3Tensor(0.2, 0.3, 0.4)
    check("T1.7 Interpret low", t3_low.interpret() == "high_risk")

    changes = t3.apply_delta({"talent": 0.1, "training": -0.2})
    check("T1.8 Talent updated", abs(t3.talent - 0.9) < 0.001)
    check("T1.9 Training updated", abs(t3.training - 0.6) < 0.001)
    check("T1.10 Temperament unchanged", t3.temperament == 0.9)
    check("T1.11 Changes dict", "talent" in changes)
    check("T1.12 Change from value", abs(changes["talent"].from_value - 0.8) < 0.001)
    check("T1.13 Change to value", abs(changes["talent"].to_value - 0.9) < 0.001)

    # Clamping
    t3c = T3Tensor(0.95, 0.05, 0.5)
    t3c.apply_delta({"talent": 0.2, "training": -0.1})
    check("T1.14 Clamped to 1.0", t3c.talent == 1.0)
    check("T1.15 Clamped to 0.0", t3c.training == 0.0)

    # ── T2: V3 Tensor Basics ──
    print("T2: V3 Tensor Basics")

    v3 = V3Tensor(0.8, 0.9, 0.85)
    check("T2.1 Veracity", v3.veracity == 0.8)
    check("T2.2 Validity", v3.validity == 0.9)
    check("T2.3 Value", v3.value == 0.85)
    check("T2.4 Average", abs(v3.average() - 0.85) < 0.001)
    check("T2.5 Interpret high", v3.interpret() == "high_quality_trustworthy")

    v3_mid = V3Tensor(0.6, 0.5, 0.7)
    check("T2.6 Interpret mid", v3_mid.interpret() == "valuable_but_needs_rigor")

    v3_low = V3Tensor(0.3, 0.2, 0.1)
    check("T2.7 Interpret low", v3_low.interpret() == "low_quality_untrustworthy")

    changes = v3.apply_delta({"veracity": 0.05, "value": -0.1})
    check("T2.8 Veracity updated", abs(v3.veracity - 0.85) < 0.001)
    check("T2.9 Value updated", abs(v3.value - 0.75) < 0.001)
    check("T2.10 Validity unchanged", v3.validity == 0.9)

    # ── T3: Reputation Rule Structure ──
    print("T3: Reputation Rule Structure")

    success_rule = ReputationRule(
        rule_id="successful_analysis",
        category=RuleCategory.SUCCESS,
        trigger_conditions={
            "action_type": "analyze_dataset",
            "result_status": "success",
            "quality_threshold": 0.95,
        },
        t3_impacts={
            "training": DimensionImpact(base_delta=0.01, modifiers=[
                RuleModifier(condition="deadline_met", multiplier=1.5),
                RuleModifier(condition="exceed_quality", multiplier=1.2),
            ]),
            "temperament": DimensionImpact(base_delta=0.005, modifiers=[
                RuleModifier(condition="early_completion", multiplier=1.3),
            ]),
        },
        v3_impacts={
            "veracity": DimensionImpact(base_delta=0.02, modifiers=[
                RuleModifier(condition="high_accuracy", multiplier=1.1),
            ]),
        },
        witnesses_required=2,
        law_oracle="lct:web4:oracle:data_science",
    )
    check("T3.1 Rule ID", success_rule.rule_id == "successful_analysis")
    check("T3.2 Category success", success_rule.category == RuleCategory.SUCCESS)
    check("T3.3 T3 impacts count", len(success_rule.t3_impacts) == 2)
    check("T3.4 V3 impacts count", len(success_rule.v3_impacts) == 1)
    check("T3.5 Witnesses required", success_rule.witnesses_required == 2)
    check("T3.6 Law oracle", success_rule.law_oracle == "lct:web4:oracle:data_science")
    check("T3.7 Combined impacts", len(success_rule.reputation_impact) == 3)

    # Modifiers
    training_impact = success_rule.t3_impacts["training"]
    check("T3.8 Training base delta", training_impact.base_delta == 0.01)
    check("T3.9 Training modifiers count", len(training_impact.modifiers) == 2)
    check("T3.10 First modifier condition", training_impact.modifiers[0].condition == "deadline_met")
    check("T3.11 First modifier multiplier", training_impact.modifiers[0].multiplier == 1.5)

    # ── T4: Failure and Ethical Violation Rules ──
    print("T4: Failure and Ethical Violation Rules")

    failure_rule = ReputationRule(
        rule_id="model_training_failure",
        category=RuleCategory.FAILURE,
        trigger_conditions={"action_type": "train_model", "result_status": "failure"},
        t3_impacts={
            "training": DimensionImpact(base_delta=-0.005),
            "temperament": DimensionImpact(base_delta=-0.01),
        },
        v3_impacts={
            "validity": DimensionImpact(base_delta=-0.01),
        },
    )
    check("T4.1 Failure category", failure_rule.category == RuleCategory.FAILURE)
    check("T4.2 Negative training delta", failure_rule.t3_impacts["training"].base_delta == -0.005)
    check("T4.3 Negative temperament delta", failure_rule.t3_impacts["temperament"].base_delta == -0.01)

    ethical_rule = ReputationRule(
        rule_id="data_manipulation",
        category=RuleCategory.ETHICAL_VIOLATION,
        trigger_conditions={"action_type": "submit_report", "result_status": "violation"},
        t3_impacts={
            "temperament": DimensionImpact(base_delta=-0.10),
        },
        v3_impacts={
            "veracity": DimensionImpact(base_delta=-0.20),
            "validity": DimensionImpact(base_delta=-0.15),
        },
    )
    check("T4.4 Ethical violation category", ethical_rule.category == RuleCategory.ETHICAL_VIOLATION)
    check("T4.5 Severe temperament penalty", ethical_rule.t3_impacts["temperament"].base_delta == -0.10)
    check("T4.6 Severe veracity penalty", ethical_rule.v3_impacts["veracity"].base_delta == -0.20)
    check("T4.7 Severe validity penalty", ethical_rule.v3_impacts["validity"].base_delta == -0.15)

    # ── T5: Trigger Condition Matching ──
    print("T5: Trigger Condition Matching")

    action = ActionContext(action_type="analyze_dataset", target="dataset.csv", resource_required=100)
    result_good = ActionResult(status="success", quality=0.97, accuracy=0.98, resource_consumed=90)
    result_bad = ActionResult(status="failure", quality=0.5)

    check("T5.1 Success matches success rule", matches_trigger_conditions(success_rule, action, result_good))
    check("T5.2 Failure doesn't match success rule", not matches_trigger_conditions(success_rule, action, result_bad))

    # Wrong action type
    wrong_action = ActionContext(action_type="wrong_type")
    check("T5.3 Wrong action type", not matches_trigger_conditions(success_rule, wrong_action, result_good))

    # Below quality threshold
    result_low_q = ActionResult(status="success", quality=0.90)
    check("T5.4 Below quality threshold", not matches_trigger_conditions(success_rule, action, result_low_q))

    # Exact threshold
    result_exact = ActionResult(status="success", quality=0.95)
    check("T5.5 At quality threshold", matches_trigger_conditions(success_rule, action, result_exact))

    # ── T6: Contributing Factors Analysis ──
    print("T6: Contributing Factors Analysis")

    now = datetime.utcnow()
    action_with_deadline = ActionContext(
        action_type="analyze_dataset", target="data.csv",
        constraints={"deadline": now + timedelta(hours=2)},
        resource_required=100,
    )
    result_efficient = ActionResult(
        status="success", quality=0.98, accuracy=0.97,
        resource_consumed=80, timestamp=now,
    )

    factors = analyze_factors(action_with_deadline, result_efficient, success_rule)
    factor_names = [f.factor for f in factors]
    check("T6.1 Has exceed_quality", "exceed_quality" in factor_names)
    check("T6.2 Has deadline_met", "deadline_met" in factor_names)
    check("T6.3 Has early_completion", "early_completion" in factor_names)
    check("T6.4 Has resource_efficiency", "resource_efficiency" in factor_names)
    check("T6.5 Has high_accuracy", "high_accuracy" in factor_names)
    check("T6.6 At least 5 factors", len(factors) >= 5)

    # Normalize
    normalized = normalize_factors(factors)
    total_weight = sum(f.normalized_weight for f in normalized)
    check("T6.7 Weights sum to 1.0", abs(total_weight - 1.0) < 0.001)

    # No factors case
    action_simple = ActionContext(action_type="simple")
    result_simple = ActionResult(status="success", quality=0.5, resource_consumed=100)
    simple_rule = ReputationRule(
        rule_id="simple", trigger_conditions={"action_type": "simple", "result_status": "success"},
    )
    simple_factors = analyze_factors(action_simple, result_simple, simple_rule)
    check("T6.8 No factors for simple", len(simple_factors) == 0)

    # ── T7: Dimension Delta Computation ──
    print("T7: Dimension Delta Computation")

    # With modifiers
    delta_training = compute_dimension_delta(
        "training", [success_rule], factors, action_with_deadline, result_efficient
    )
    check("T7.1 Training delta positive", delta_training > 0)
    check("T7.2 Training delta has modifiers",
          delta_training > success_rule.t3_impacts["training"].base_delta)

    delta_veracity = compute_dimension_delta(
        "veracity", [success_rule], factors, action_with_deadline, result_efficient
    )
    check("T7.3 Veracity delta positive", delta_veracity > 0)

    # No impact dimension
    delta_talent = compute_dimension_delta(
        "talent", [success_rule], factors, action_with_deadline, result_efficient
    )
    check("T7.4 Talent delta zero (no impact)", delta_talent == 0)

    # Clamping
    extreme_rule = ReputationRule(
        rule_id="extreme",
        trigger_conditions={"action_type": "extreme", "result_status": "success"},
        t3_impacts={"talent": DimensionImpact(base_delta=2.0)},
    )
    extreme_action = ActionContext(action_type="extreme")
    extreme_result = ActionResult(status="success")
    extreme_delta = compute_dimension_delta(
        "talent", [extreme_rule], [], extreme_action, extreme_result
    )
    check("T7.5 Clamped to 1.0", extreme_delta == 1.0)

    neg_rule = ReputationRule(
        rule_id="neg_extreme",
        trigger_conditions={"action_type": "extreme", "result_status": "success"},
        t3_impacts={"talent": DimensionImpact(base_delta=-2.0)},
    )
    neg_delta = compute_dimension_delta(
        "talent", [neg_rule], [], extreme_action, extreme_result
    )
    check("T7.6 Clamped to -1.0", neg_delta == -1.0)

    # ── T8: Full Reputation Delta Computation ──
    print("T8: Full Reputation Delta Computation")

    t3_alice = T3Tensor(0.85, 0.90, 0.88)
    v3_alice = V3Tensor(0.80, 1.0, 0.75)
    pairing = RolePairingInMRH(
        entity="lct:web4:entity:alice",
        role="lct:web4:role:analyst",
        paired_at="2025-01-01T00:00:00",
        mrh_link="link:mrh:alice→analyst:001",
    )

    delta = compute_reputation_delta(
        subject_lct="lct:web4:entity:alice",
        role_lct="lct:web4:role:analyst",
        action=action_with_deadline,
        result=result_efficient,
        rules=[success_rule],
        t3=t3_alice,
        v3=v3_alice,
        role_pairing=pairing,
    )

    check("T8.1 Subject LCT", delta.subject_lct == "lct:web4:entity:alice")
    check("T8.2 Role LCT", delta.role_lct == "lct:web4:role:analyst")
    check("T8.3 Action type", delta.action_type == "analyze_dataset")
    check("T8.4 Rule triggered", delta.rule_triggered == "successful_analysis")
    check("T8.5 Has T3 delta", len(delta.t3_delta) > 0)
    check("T8.6 Has V3 delta", len(delta.v3_delta) > 0)
    check("T8.7 Has factors", len(delta.contributing_factors) > 0)
    check("T8.8 Net trust positive", delta.net_trust_change > 0)
    check("T8.9 Net value positive", delta.net_value_change > 0)
    check("T8.10 Has timestamp", len(delta.timestamp) > 0)
    check("T8.11 Has reason", len(delta.reason) > 0)
    check("T8.12 Role pairing preserved", delta.role_pairing_in_mrh is not None)

    # ── T9: No Rules Triggered ──
    print("T9: No Rules Triggered")

    empty_delta = compute_reputation_delta(
        subject_lct="lct:web4:entity:bob",
        role_lct="lct:web4:role:chef",
        action=ActionContext(action_type="cook"),
        result=ActionResult(status="success"),
        rules=[success_rule],  # Doesn't match "cook"
        t3=T3Tensor(), v3=V3Tensor(),
    )
    check("T9.1 No T3 delta", len(empty_delta.t3_delta) == 0)
    check("T9.2 No V3 delta", len(empty_delta.v3_delta) == 0)
    check("T9.3 Net trust zero", empty_delta.net_trust_change == 0)
    check("T9.4 Net value zero", empty_delta.net_value_change == 0)

    # ── T10: Reputation Delta Serialization ──
    print("T10: Reputation Delta Serialization")

    delta_dict = delta.to_dict()
    rep = delta_dict["reputation"]
    check("T10.1 Has subject_lct", "subject_lct" in rep)
    check("T10.2 Has role_lct", "role_lct" in rep)
    check("T10.3 Has t3_delta", "t3_delta" in rep)
    check("T10.4 Has v3_delta", "v3_delta" in rep)
    check("T10.5 Has contributing_factors", "contributing_factors" in rep)
    check("T10.6 Has witnesses", "witnesses" in rep)
    check("T10.7 Has net_trust_change", "net_trust_change" in rep)
    check("T10.8 Has net_value_change", "net_value_change" in rep)
    check("T10.9 Role pairing present", rep["role_pairing_in_mrh"] is not None)

    # T3 delta structure
    if delta.t3_delta:
        first_dim = list(rep["t3_delta"].keys())[0]
        dim_data = rep["t3_delta"][first_dim]
        check("T10.10 T3 dim has change", "change" in dim_data)
        check("T10.11 T3 dim has from", "from" in dim_data)
        check("T10.12 T3 dim has to", "to" in dim_data)

    # Hash
    rep_hash = delta.compute_hash()
    check("T10.13 Hash starts with sha256:", rep_hash.startswith("sha256:"))
    check("T10.14 Hash deterministic", delta.compute_hash() == rep_hash)

    # ── T11: Witness Selection ──
    print("T11: Witness Selection")

    witnesses = select_reputation_witnesses(
        success_rule,
        role_validators=["lct:web4:validator:v1", "lct:web4:validator:v2"],
        mrh_witnesses=["lct:web4:witness:w1"],
    )
    check("T11.1 2 witnesses selected (required=2)", len(witnesses) == 2)
    check("T11.2 Law oracle first", witnesses[0].witness_type == "law_oracle")
    check("T11.3 Role validator second", witnesses[1].witness_type == "role_validator")

    # More witnesses required than available
    greedy_rule = ReputationRule(
        rule_id="greedy", witnesses_required=10,
        law_oracle="lct:web4:oracle:test",
    )
    greedy_witnesses = select_reputation_witnesses(
        greedy_rule,
        role_validators=["lct:web4:validator:v1"],
        mrh_witnesses=["lct:web4:witness:w1", "lct:web4:witness:w2"],
    )
    check("T11.4 Capped at available (4)", len(greedy_witnesses) == 4)

    # Zero required
    no_witness_rule = ReputationRule(rule_id="no_witness", witnesses_required=0)
    no_witnesses = select_reputation_witnesses(no_witness_rule)
    check("T11.5 Zero witnesses", len(no_witnesses) == 0)

    # ── T12: Witness Attestation ──
    print("T12: Witness Attestation")

    attestations = create_witness_attestations(witnesses, delta)
    check("T12.1 Attestation count matches", len(attestations) == len(witnesses))
    check("T12.2 First has signature", len(attestations[0].signature) > 0)
    check("T12.3 First has timestamp", len(attestations[0].timestamp) > 0)
    check("T12.4 First attestation verified", attestations[0].attestation["verified"])
    check("T12.5 Attestation has action_id", "action_id" in attestations[0].attestation)
    check("T12.6 Attestation has reputation_hash", "reputation_hash" in attestations[0].attestation)
    check("T12.7 Confidence 0.95", attestations[0].attestation["confidence"] == 0.95)

    # ── T13: Reputation Store — Time-Weighted Aggregation ──
    print("T13: Reputation Store — Time-Weighted Aggregation")

    store = ReputationStore()
    entity = "lct:web4:entity:charlie"
    role = "lct:web4:role:engineer"

    # Neutral for new entity
    neutral = store.compute_current_reputation(entity, role, "training")
    check("T13.1 Neutral for new entity", neutral == 0.5)

    # Store some deltas
    now = datetime.utcnow()

    # Recent positive delta
    recent_delta = ReputationDelta(
        t3_delta={"training": DimensionDelta(change=0.05, from_value=0.5, to_value=0.55)},
        v3_delta={},
    )
    store.store_delta(entity, role, recent_delta)

    rep = store.compute_current_reputation(entity, role, "training", reference_time=now)
    check("T13.2 Positive after recent delta", rep > 0.0)

    # Store older delta (simulate by modifying timestamp)
    old_delta = StoredDelta(
        dimension="training", change=0.03, role_lct=role,
        timestamp=now - timedelta(days=60),
    )
    store.deltas.append(old_delta)

    rep_with_old = store.compute_current_reputation(entity, role, "training", reference_time=now)
    check("T13.3 Older deltas have less weight", rep_with_old != rep)  # Different due to weighting

    # Beyond horizon
    very_old = StoredDelta(
        dimension="training", change=0.1, role_lct=role,
        timestamp=now - timedelta(days=200),
    )
    store.deltas.append(very_old)
    rep_horizon = store.compute_current_reputation(entity, role, "training",
                                                    time_horizon_days=90, reference_time=now)
    # Very old delta should be excluded
    check("T13.4 Beyond-horizon delta excluded",
          rep_horizon == rep_with_old)  # Same as before since 200-day is outside 90-day horizon

    # ── T14: Reputation Decay ──
    print("T14: Reputation Decay")

    decay_store = ReputationStore()
    decay_entity = "lct:web4:entity:dave"
    decay_role = "lct:web4:role:pilot"
    decay_now = datetime.utcnow()

    # No last action = no decay
    no_decay = decay_store.apply_reputation_decay(decay_entity, decay_role, "training", decay_now)
    check("T14.1 No last action = no decay", no_decay == 0.0)

    # Recent activity = no decay (within 30 days)
    decay_store.last_action[(decay_entity, decay_role)] = decay_now - timedelta(days=15)
    recent_decay = decay_store.apply_reputation_decay(decay_entity, decay_role, "training", decay_now)
    check("T14.2 Recent activity = no decay", recent_decay == 0.0)

    # 60 days inactive (2 months × -0.01)
    decay_store.last_action[(decay_entity, decay_role)] = decay_now - timedelta(days=60)
    two_month_decay = decay_store.apply_reputation_decay(decay_entity, decay_role, "training", decay_now)
    check("T14.3 60-day decay negative", two_month_decay < 0)
    expected_decay = -0.01 * (60 / 30.0)
    check("T14.4 60-day decay value", abs(two_month_decay - expected_decay) < 0.001)

    # 8 months inactive (accelerated after 6)
    decay_store.last_action[(decay_entity, decay_role)] = decay_now - timedelta(days=240)
    long_decay = decay_store.apply_reputation_decay(decay_entity, decay_role, "training", decay_now)
    check("T14.5 Long decay accelerated", long_decay < two_month_decay)
    check("T14.6 Decay >= -0.5 cap", long_decay >= -0.5)

    # Extreme inactivity (5 years)
    decay_store.last_action[(decay_entity, decay_role)] = decay_now - timedelta(days=1825)
    extreme_decay = decay_store.apply_reputation_decay(decay_entity, decay_role, "training", decay_now)
    check("T14.7 Extreme decay capped at -0.5", extreme_decay == -0.5)

    # ── T15: Gaming Prevention — Diminishing Returns ──
    print("T15: Gaming Prevention — Diminishing Returns")

    gaming = GamingPrevention()

    # First action: full credit
    m1 = gaming.compute_diminishing_multiplier("entity_a", "analyze")
    check("T15.1 First action full credit", m1 == 1.0)

    # Record actions and check diminishing
    gaming.record_action("entity_a", "analyze")
    m2 = gaming.compute_diminishing_multiplier("entity_a", "analyze")
    check("T15.2 Second action 0.8", abs(m2 - 0.8) < 0.001)

    gaming.record_action("entity_a", "analyze")
    m3 = gaming.compute_diminishing_multiplier("entity_a", "analyze")
    check("T15.3 Third action 0.64", abs(m3 - 0.64) < 0.001)

    gaming.record_action("entity_a", "analyze")
    m4 = gaming.compute_diminishing_multiplier("entity_a", "analyze")
    check("T15.4 Fourth action 0.512", abs(m4 - 0.512) < 0.001)

    # Different action type = independent
    m_diff = gaming.compute_diminishing_multiplier("entity_a", "deploy")
    check("T15.5 Different action full credit", m_diff == 1.0)

    # Different entity = independent
    m_other = gaming.compute_diminishing_multiplier("entity_b", "analyze")
    check("T15.6 Different entity full credit", m_other == 1.0)

    # Floor at 0.1 (after many repeated actions)
    for _ in range(50):
        gaming.record_action("entity_a", "analyze")
    m_floor = gaming.compute_diminishing_multiplier("entity_a", "analyze")
    check("T15.7 Floor at 0.1", abs(m_floor - 0.1) < 0.001)

    # ── T16: Gaming Prevention — Self-Attestation ──
    print("T16: Gaming Prevention — Self-Attestation")

    check("T16.1 Independent witnesses ok",
          gaming.check_self_attestation("alice", ["bob", "charlie"]))
    check("T16.2 Self-attestation blocked",
          not gaming.check_self_attestation("alice", ["bob", "alice"]))

    # Quality threshold
    check("T16.3 Quality above threshold", gaming.check_quality_threshold(0.96, 0.95))
    check("T16.4 Quality below threshold", not gaming.check_quality_threshold(0.94, 0.95))
    check("T16.5 Quality at threshold", gaming.check_quality_threshold(0.95, 0.95))

    # ── T17: Sybil Attack Economics ──
    print("T17: Sybil Attack Economics")

    cost_1 = GamingPrevention.sybil_cost(1)
    check("T17.1 Single identity cost", cost_1 == 300.0)

    cost_10 = GamingPrevention.sybil_cost(10)
    check("T17.2 10 identities cost", cost_10 == 3000.0)

    cost_100 = GamingPrevention.sybil_cost(100)
    check("T17.3 100 identities cost", cost_100 == 30000.0)

    # ATP farming fee
    fee = GamingPrevention.atp_farming_fee(1000.0)
    check("T17.4 5% farming fee", fee == 50.0)

    # Circular flow: 1000 ATP → 950 → 902.5 → ... unprofitable
    remaining = 1000.0
    for _ in range(10):
        remaining -= GamingPrevention.atp_farming_fee(remaining)
    check("T17.5 Circular flow shrinks", remaining < 600)

    # ── T18: Role-Contextualized Reputation ──
    print("T18: Role-Contextualized Reputation")

    engine = ReputationEngine()

    # Register success rule
    engine.register_rule(success_rule)

    # Alice as analyst
    alice = "lct:web4:entity:alice"
    role_analyst = "lct:web4:role:analyst"
    role_surgeon = "lct:web4:role:surgeon"

    # Process action as analyst
    analyst_delta = engine.process_action(
        entity_lct=alice,
        role_lct=role_analyst,
        action=action_with_deadline,
        result=result_efficient,
        role_validators=["lct:web4:validator:v1"],
    )
    check("T18.1 Analyst delta has trust change", analyst_delta.net_trust_change != 0)

    # Query reputation in different roles
    analyst_training = engine.query_reputation(alice, role_analyst, "training")
    surgeon_training = engine.query_reputation(alice, role_surgeon, "training")
    check("T18.2 Analyst has reputation", analyst_training != 0.5)
    check("T18.3 Surgeon neutral (no actions)", surgeon_training == 0.5)
    check("T18.4 Different roles different rep", analyst_training != surgeon_training)

    # T3/V3 are role-specific
    t3_analyst = engine.get_or_create_t3(alice, role_analyst)
    t3_surgeon = engine.get_or_create_t3(alice, role_surgeon)
    check("T18.5 Analyst T3 modified", t3_analyst.training != 0.5)
    check("T18.6 Surgeon T3 default", t3_surgeon.training == 0.5)

    # ── T19: Multi-Rule Processing ──
    print("T19: Multi-Rule Processing")

    multi_engine = ReputationEngine()

    # Two rules that both trigger on same action
    rule_a = ReputationRule(
        rule_id="quality_bonus",
        trigger_conditions={"action_type": "analyze", "result_status": "success"},
        t3_impacts={"talent": DimensionImpact(base_delta=0.02)},
    )
    rule_b = ReputationRule(
        rule_id="efficiency_bonus",
        trigger_conditions={"action_type": "analyze", "result_status": "success"},
        v3_impacts={"value": DimensionImpact(base_delta=0.01)},
    )
    multi_engine.register_rule(rule_a)
    multi_engine.register_rule(rule_b)

    multi_action = ActionContext(action_type="analyze", resource_required=50)
    multi_result = ActionResult(status="success", quality=0.9, resource_consumed=40)

    multi_delta = multi_engine.process_action(
        entity_lct="lct:web4:entity:eve",
        role_lct="lct:web4:role:data_analyst",
        action=multi_action, result=multi_result,
    )
    check("T19.1 Both rules triggered", multi_delta.net_trust_change > 0)
    check("T19.2 V3 also changed", multi_delta.net_value_change > 0)
    check("T19.3 Talent increased",
          "talent" in multi_delta.t3_delta)
    check("T19.4 Value increased",
          "value" in multi_delta.v3_delta)

    # ── T20: Diminishing Returns in Engine ──
    print("T20: Diminishing Returns in Engine")

    dim_engine = ReputationEngine()
    dim_engine.register_rule(ReputationRule(
        rule_id="repeat_action",
        trigger_conditions={"action_type": "submit", "result_status": "success"},
        t3_impacts={"training": DimensionImpact(base_delta=0.05)},
    ))

    entity_f = "lct:web4:entity:frank"
    role_f = "lct:web4:role:submitter"

    # First action: full credit
    d1 = dim_engine.process_action(
        entity_lct=entity_f, role_lct=role_f,
        action=ActionContext(action_type="submit"),
        result=ActionResult(status="success"),
    )
    first_change = d1.net_trust_change

    # Second action: diminished
    d2 = dim_engine.process_action(
        entity_lct=entity_f, role_lct=role_f,
        action=ActionContext(action_type="submit"),
        result=ActionResult(status="success"),
    )
    second_change = d2.net_trust_change

    check("T20.1 First action change", first_change > 0)
    check("T20.2 Second action diminished", second_change < first_change)
    check("T20.3 Ratio ~0.8", abs(second_change / first_change - 0.8) < 0.05)

    # ── T21: Spec Example Verification ──
    print("T21: Spec Example Verification")

    # From spec §5 example:
    # Rule: successful_model_training
    # training: base +0.01, modifiers (quality 1.2, early 1.3) = +0.0156
    # temperament: base +0.005, modifier (deadline 1.5) = +0.0075

    spec_rule = ReputationRule(
        rule_id="successful_model_training",
        category=RuleCategory.SUCCESS,
        trigger_conditions={
            "action_type": "train_ml_model",
            "result_status": "success",
            "quality_threshold": 0.95,
        },
        t3_impacts={
            "training": DimensionImpact(base_delta=0.01, modifiers=[
                RuleModifier(condition="exceed_quality", multiplier=1.2),
                RuleModifier(condition="early_completion", multiplier=1.3),
            ]),
            "temperament": DimensionImpact(base_delta=0.005, modifiers=[
                RuleModifier(condition="deadline_met", multiplier=1.5),
            ]),
        },
        v3_impacts={
            "veracity": DimensionImpact(base_delta=0.02),
            "validity": DimensionImpact(base_delta=0.01, modifiers=[
                RuleModifier(condition="high_accuracy", multiplier=1.1),
            ]),
        },
        witnesses_required=2,
        law_oracle="lct:web4:oracle:ml_society",
    )

    spec_now = datetime.utcnow()
    spec_action = ActionContext(
        action_type="train_ml_model",
        target="customer_model",
        constraints={"deadline": spec_now + timedelta(hours=4)},
        resource_required=100,
    )
    spec_result = ActionResult(
        status="success", quality=0.97, accuracy=0.97,
        resource_consumed=90, timestamp=spec_now,
    )

    spec_factors = analyze_factors(spec_action, spec_result, spec_rule)
    factor_names = [f.factor for f in spec_factors]

    # Compute dimension deltas
    training_d = compute_dimension_delta("training", [spec_rule], spec_factors, spec_action, spec_result)
    temperament_d = compute_dimension_delta("temperament", [spec_rule], spec_factors, spec_action, spec_result)
    veracity_d = compute_dimension_delta("veracity", [spec_rule], spec_factors, spec_action, spec_result)
    validity_d = compute_dimension_delta("validity", [spec_rule], spec_factors, spec_action, spec_result)

    # Spec: training = 0.01 * 1.2 * 1.3 = 0.0156
    check("T21.1 Training delta matches spec", abs(training_d - 0.0156) < 0.001)
    # Spec: temperament = 0.005 * 1.5 = 0.0075
    check("T21.2 Temperament delta matches spec", abs(temperament_d - 0.0075) < 0.001)
    # Spec: veracity = 0.02 (no modifiers for veracity explicitly)
    check("T21.3 Veracity delta matches spec", abs(veracity_d - 0.02) < 0.001)
    # Spec: validity = 0.01 * 1.1 = 0.011
    check("T21.4 Validity delta matches spec", abs(validity_d - 0.011) < 0.001)

    # Net changes from spec
    net_trust = training_d + temperament_d
    net_value = veracity_d + validity_d
    check("T21.5 Net trust ~0.0231", abs(net_trust - 0.0231) < 0.001)
    check("T21.6 Net value ~0.031", abs(net_value - 0.031) < 0.001)

    # ── T22: Role Pairing In MRH ──
    print("T22: Role Pairing In MRH")

    rp = RolePairingInMRH(
        entity="lct:web4:entity:grace",
        role="lct:web4:role:architect",
        paired_at="2025-06-15T10:00:00",
        mrh_link="link:mrh:grace→architect:001",
    )
    check("T22.1 Entity set", rp.entity == "lct:web4:entity:grace")
    check("T22.2 Role set", rp.role == "lct:web4:role:architect")
    check("T22.3 Paired at set", rp.paired_at == "2025-06-15T10:00:00")
    check("T22.4 MRH link set", rp.mrh_link == "link:mrh:grace→architect:001")

    # ── T23: Contributing Factor Structure ──
    print("T23: Contributing Factor Structure")

    cf = ContributingFactor(factor="exceed_quality", weight=0.5, value=0.98)
    check("T23.1 Factor name", cf.factor == "exceed_quality")
    check("T23.2 Weight", cf.weight == 0.5)
    check("T23.3 Value", cf.value == 0.98)
    check("T23.4 Initial normalized weight", cf.normalized_weight == 0.0)

    # Normalization
    factors = [
        ContributingFactor(factor="a", weight=0.3),
        ContributingFactor(factor="b", weight=0.7),
    ]
    normalize_factors(factors)
    check("T23.5 Normalized sum = 1.0",
          abs(factors[0].normalized_weight + factors[1].normalized_weight - 1.0) < 0.001)
    check("T23.6 Factor a normalized", abs(factors[0].normalized_weight - 0.3) < 0.001)
    check("T23.7 Factor b normalized", abs(factors[1].normalized_weight - 0.7) < 0.001)

    # Empty factors normalization
    empty = normalize_factors([])
    check("T23.8 Empty factors ok", len(empty) == 0)

    # ── T24: Engine Witness Integration ──
    print("T24: Engine Witness Integration")

    witness_engine = ReputationEngine()
    witness_engine.register_rule(ReputationRule(
        rule_id="witnessed_action",
        trigger_conditions={"action_type": "certify", "result_status": "success"},
        t3_impacts={"talent": DimensionImpact(base_delta=0.01)},
        witnesses_required=3,
        law_oracle="lct:web4:oracle:cert_authority",
    ))

    wd = witness_engine.process_action(
        entity_lct="lct:web4:entity:henry",
        role_lct="lct:web4:role:certifier",
        action=ActionContext(action_type="certify"),
        result=ActionResult(status="success"),
        role_validators=["lct:web4:validator:v1", "lct:web4:validator:v2"],
        mrh_witnesses=["lct:web4:witness:w1"],
    )
    check("T24.1 Has witnesses", len(wd.witnesses) > 0)
    check("T24.2 3 witnesses", len(wd.witnesses) == 3)
    check("T24.3 First witness is oracle", wd.witnesses[0].witness_type == "law_oracle")

    # ── T25: Ethical Violation Processing ──
    print("T25: Ethical Violation Processing")

    ethics_engine = ReputationEngine()
    ethics_engine.register_rule(ethical_rule)

    ev_delta = ethics_engine.process_action(
        entity_lct="lct:web4:entity:villain",
        role_lct="lct:web4:role:reporter",
        action=ActionContext(action_type="submit_report"),
        result=ActionResult(status="violation"),
    )
    check("T25.1 Severe trust penalty", ev_delta.net_trust_change < 0)
    check("T25.2 Severe value penalty", ev_delta.net_value_change < 0)
    check("T25.3 Temperament hit", "temperament" in ev_delta.t3_delta)
    check("T25.4 Veracity hit", "veracity" in ev_delta.v3_delta)

    # Check T3/V3 are actually reduced
    villain_t3 = ethics_engine.get_or_create_t3("lct:web4:entity:villain", "lct:web4:role:reporter")
    villain_v3 = ethics_engine.get_or_create_v3("lct:web4:entity:villain", "lct:web4:role:reporter")
    check("T25.5 Temperament below 0.5", villain_t3.temperament < 0.5)
    check("T25.6 Veracity below 0.5", villain_v3.veracity < 0.5)
    check("T25.7 Validity below 0.5", villain_v3.validity < 0.5)

    # ── T26: Exceptional Performance Rule ──
    print("T26: Exceptional Performance Rule")

    exceptional_rule = ReputationRule(
        rule_id="exceptional_performance",
        category=RuleCategory.EXCEPTIONAL,
        trigger_conditions={"action_type": "solve", "result_status": "success", "quality_threshold": 0.99},
        t3_impacts={
            "talent": DimensionImpact(base_delta=0.02),
            "training": DimensionImpact(base_delta=0.015),
        },
        v3_impacts={
            "value": DimensionImpact(base_delta=0.03),
        },
    )

    exc_engine = ReputationEngine()
    exc_engine.register_rule(exceptional_rule)

    exc_delta = exc_engine.process_action(
        entity_lct="lct:web4:entity:genius",
        role_lct="lct:web4:role:researcher",
        action=ActionContext(action_type="solve"),
        result=ActionResult(status="success", quality=0.995),
    )
    check("T26.1 Talent increased", "talent" in exc_delta.t3_delta)
    check("T26.2 Training increased", "training" in exc_delta.t3_delta)
    check("T26.3 Value increased", "value" in exc_delta.v3_delta)
    check("T26.4 High net trust", exc_delta.net_trust_change > 0.03)

    # Below exceptional threshold — no trigger
    no_exc = exc_engine.process_action(
        entity_lct="lct:web4:entity:average",
        role_lct="lct:web4:role:researcher",
        action=ActionContext(action_type="solve"),
        result=ActionResult(status="success", quality=0.85),
    )
    check("T26.5 Below threshold no change", no_exc.net_trust_change == 0)

    # ── T27: DimensionDelta and Aggregated T3/V3 ──
    print("T27: Dimension Delta and Aggregated Values")

    dd = DimensionDelta(change=0.05, from_value=0.70, to_value=0.75)
    d = dd.to_dict()
    check("T27.1 Dict has change", d["change"] == 0.05)
    check("T27.2 Dict has from", d["from"] == 0.70)
    check("T27.3 Dict has to", d["to"] == 0.75)

    # T3 zero delta doesn't create entry
    t3_zero = T3Tensor(0.5, 0.5, 0.5)
    zero_changes = t3_zero.apply_delta({"talent": 0.0})
    check("T27.4 Zero delta no entry", len(zero_changes) == 0)

    # V3 zero delta
    v3_zero = V3Tensor(0.5, 0.5, 0.5)
    zero_v3 = v3_zero.apply_delta({"veracity": 0.0})
    check("T27.5 V3 zero delta no entry", len(zero_v3) == 0)

    # Multiple dimensions
    multi_changes = t3_zero.apply_delta({"talent": 0.1, "training": 0.2, "temperament": -0.1})
    check("T27.6 Three dimensions changed", len(multi_changes) == 3)

    # ── T28: Factor Condition Matching ──
    print("T28: Factor Condition Matching")

    test_factors = [
        ContributingFactor(factor="deadline_met", weight=0.3),
        ContributingFactor(factor="resource_efficiency", weight=0.2),
    ]
    check("T28.1 deadline_met applies", factor_applies("deadline_met", test_factors))
    check("T28.2 resource_efficiency applies", factor_applies("resource_efficiency", test_factors))
    check("T28.3 high_accuracy not present", not factor_applies("high_accuracy", test_factors))
    check("T28.4 Empty factors", not factor_applies("anything", []))

    # ── Summary ──
    print(f"\n{'='*60}")
    print(f"Reputation Computation: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  {failed} FAILED")
    else:
        print("  All checks passed!")
    print(f"{'='*60}")

    return passed, total


if __name__ == "__main__":
    run_tests()
