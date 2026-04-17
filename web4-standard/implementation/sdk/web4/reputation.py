"""
Web4 Reputation Computation

Implements web4-standard/core-spec/reputation-computation.md:
- ReputationRule: rule-triggered reputation changes with modifiers
- ReputationEngine: matches rules against action outcomes, computes deltas
- ReputationStore: time-weighted aggregation and inactivity decay

This module builds on web4.r6 (ReputationDelta, ContributingFactor, TensorDelta)
and web4.trust (T3, V3). It does NOT replace R7Action.compute_reputation() —
that method is the simple quality-based path. This module adds the full
rule-engine path described in the spec.

Cross-module integration:
- web4.r6: ReputationDelta, ContributingFactor, TensorDelta, R7Action, ActionStatus
- web4.trust: T3, V3, _clamp
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .atp import ATPAccount
from .r6 import (
    ActionStatus,
    ContributingFactor,
    R7Action,
    ReputationDelta,
    TensorDelta,
)
from .trust import T3, V3, TrustProfile, _clamp

__all__ = [
    # Classes
    "ReputationRule", "DimensionImpact", "Modifier",
    "ReputationEngine", "ReputationStore",
    "ActionOutcomeResult",
    # Functions
    "analyze_factors",
    "process_action_outcome",
]


# ── Reputation Rule ──────────────────────────────────────────────

@dataclass
class Modifier:
    """A conditional multiplier for a reputation dimension delta."""
    condition: str       # factor name that must be present (e.g. "deadline_met")
    multiplier: float    # multiplied into base_delta when condition active


@dataclass
class DimensionImpact:
    """Impact definition for a single T3 or V3 dimension."""
    base_delta: float = 0.0
    modifiers: List[Modifier] = field(default_factory=list)


@dataclass
class ReputationRule:
    """
    A rule that maps action outcomes to reputation changes.

    Rules are defined by Law Oracles and specify:
    - trigger_conditions: when the rule fires (action_type, result_status, thresholds)
    - t3_impacts / v3_impacts: per-dimension base deltas with conditional modifiers
    - witnesses_required: how many witnesses must attest the change
    - law_oracle: which oracle owns this rule

    Per spec section 4: "Reputation changes are rule-triggered, not arbitrary."
    """
    rule_id: str
    trigger_conditions: Dict[str, Any] = field(default_factory=dict)
    t3_impacts: Dict[str, DimensionImpact] = field(default_factory=dict)
    v3_impacts: Dict[str, DimensionImpact] = field(default_factory=dict)
    witnesses_required: int = 0
    law_oracle: str = ""

    def matches(self, action: R7Action) -> bool:
        """Check if this rule's trigger conditions match the given action."""
        tc = self.trigger_conditions

        # action_type must match if specified
        if "action_type" in tc and action.request.action != tc["action_type"]:
            return False

        # result_status must match if specified
        if "result_status" in tc:
            expected = tc["result_status"]
            if action.result.status.value != expected:
                return False

        # quality_threshold: action output must have quality >= threshold
        if "quality_threshold" in tc:
            quality = action.result.output.get("quality", 0.0)
            if quality < tc["quality_threshold"]:
                return False

        # min_atp_stake: action must have staked at least this much
        if "min_atp_stake" in tc:
            if action.request.atp_stake < tc["min_atp_stake"]:
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize rule to dict with trigger conditions and T3/V3 impact definitions."""
        return {
            "rule_id": self.rule_id,
            "trigger_conditions": self.trigger_conditions,
            "t3_impacts": {
                k: {"base_delta": v.base_delta, "modifiers": [
                    {"condition": m.condition, "multiplier": m.multiplier}
                    for m in v.modifiers
                ]}
                for k, v in self.t3_impacts.items()
            },
            "v3_impacts": {
                k: {"base_delta": v.base_delta, "modifiers": [
                    {"condition": m.condition, "multiplier": m.multiplier}
                    for m in v.modifiers
                ]}
                for k, v in self.v3_impacts.items()
            },
            "witnesses_required": self.witnesses_required,
            "law_oracle": self.law_oracle,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ReputationRule":
        """Deserialize from dict produced by to_dict()."""
        def _parse_impacts(raw: Dict[str, Any]) -> Dict[str, DimensionImpact]:
            result: Dict[str, DimensionImpact] = {}
            for dim, impact_d in raw.items():
                modifiers = [
                    Modifier(condition=m["condition"], multiplier=m["multiplier"])
                    for m in impact_d.get("modifiers", [])
                ]
                result[dim] = DimensionImpact(
                    base_delta=impact_d.get("base_delta", 0.0),
                    modifiers=modifiers,
                )
            return result

        return cls(
            rule_id=d["rule_id"],
            trigger_conditions=d.get("trigger_conditions", {}),
            t3_impacts=_parse_impacts(d.get("t3_impacts", {})),
            v3_impacts=_parse_impacts(d.get("v3_impacts", {})),
            witnesses_required=d.get("witnesses_required", 0),
            law_oracle=d.get("law_oracle", ""),
        )


# ── Factor Analysis ──────────────────────────────────────────────

def analyze_factors(action: R7Action) -> List[ContributingFactor]:
    """
    Analyze an action's outcome to identify contributing factors.

    Per spec section 5: factors are extracted from quality, timing,
    and resource efficiency signals in the action result.
    """
    factors: List[ContributingFactor] = []
    output = action.result.output

    # Quality-based factor
    quality = output.get("quality", output.get("accuracy", None))
    if quality is not None and quality > 0.5:
        factors.append(ContributingFactor(factor="high_accuracy", weight=0.4))

    # Deadline factor
    if action.request.constraints.get("deadline_met"):
        factors.append(ContributingFactor(factor="deadline_met", weight=0.3))

    # Early completion factor
    if action.request.constraints.get("early_completion"):
        factors.append(ContributingFactor(factor="early_completion", weight=0.2))

    # Resource efficiency: consumed < required
    consumed = action.result.atp_consumed
    required = action.resource.required_atp
    if required > 0 and consumed < required:
        efficiency = 1.0 - (consumed / required)
        factors.append(ContributingFactor(
            factor="resource_efficiency",
            weight=round(efficiency * 0.2, 4),
        ))

    return factors


# ── Reputation Engine ────────────────────────────────────────────

class ReputationEngine:
    """
    Rule-based reputation computation engine.

    Evaluates an R7Action against a set of ReputationRules to produce
    a ReputationDelta. This is the full rule-engine path from spec
    section 5 — more expressive than R7Action.compute_reputation().

    Usage:
        engine = ReputationEngine()
        engine.add_rule(rule)
        delta = engine.evaluate(action)
    """

    def __init__(self) -> None:
        self._rules: List[ReputationRule] = []

    def add_rule(self, rule: ReputationRule) -> None:
        """Register a reputation rule for evaluation."""
        self._rules.append(rule)

    @property
    def rules(self) -> List[ReputationRule]:
        """Copy of all registered reputation rules."""
        return list(self._rules)

    def evaluate(
        self,
        action: R7Action,
        factors: Optional[List[ContributingFactor]] = None,
    ) -> Optional[ReputationDelta]:
        """
        Evaluate action against all rules and compute reputation delta.

        Returns None if no rules match. Per spec: "No rules triggered = no
        reputation change."
        """
        triggered = [r for r in self._rules if r.matches(action)]
        if not triggered:
            return None

        if factors is None:
            factors = analyze_factors(action)

        factor_names = {f.factor for f in factors}

        # Compute T3 deltas across all triggered rules
        t3_delta: Dict[str, TensorDelta] = {}
        for dim in ("talent", "training", "temperament"):
            total = 0.0
            for rule in triggered:
                impact = rule.t3_impacts.get(dim)
                if not impact:
                    continue
                multiplier = 1.0
                for mod in impact.modifiers:
                    if mod.condition in factor_names:
                        multiplier *= mod.multiplier
                total += impact.base_delta * multiplier

            total = max(-1.0, min(1.0, total))
            if total != 0:
                current_t3 = action.role.t3_in_role or T3()
                old = getattr(current_t3, dim)
                new = _clamp(old + total)
                change = round(new - old, 10)
                if change != 0:
                    t3_delta[dim] = TensorDelta(
                        change=change, from_value=old, to_value=new,
                    )

        # Compute V3 deltas across all triggered rules
        v3_delta: Dict[str, TensorDelta] = {}
        for dim in ("veracity", "validity", "valuation"):
            total = 0.0
            for rule in triggered:
                impact = rule.v3_impacts.get(dim)
                if not impact:
                    continue
                multiplier = 1.0
                for mod in impact.modifiers:
                    if mod.condition in factor_names:
                        multiplier *= mod.multiplier
                total += impact.base_delta * multiplier

            total = max(-1.0, min(1.0, total))
            if total != 0:
                current_v3 = action.role.v3_in_role or V3()
                old = getattr(current_v3, dim)
                new = _clamp(old + total)
                change = round(new - old, 10)
                if change != 0:
                    v3_delta[dim] = TensorDelta(
                        change=change, from_value=old, to_value=new,
                    )

        ts = datetime.now(timezone.utc).isoformat()
        rule_ids = ", ".join(r.rule_id for r in triggered)

        delta = ReputationDelta(
            subject_lct=action.role.actor,
            role_lct=action.role.role_lct,
            action_type=action.request.action,
            action_target=action.request.target,
            action_id=action.action_id,
            rule_triggered=rule_ids,
            reason=f"Triggered by rule(s): {rule_ids}",
            t3_delta=t3_delta,
            v3_delta=v3_delta,
            contributing_factors=factors,
            timestamp=ts,
        )
        action.reputation = delta
        return delta


# ── Reputation Store (Aggregation + Decay) ───────────────────────

@dataclass
class _StoredDelta:
    """Internal: a delta with its timestamp for time-weighted aggregation."""
    dimension: str
    change: float
    timestamp: datetime


class ReputationStore:
    """
    Time-weighted reputation aggregation with inactivity decay.

    Per spec sections 7-8: reputation is computed by time-weighted
    aggregation of deltas over a configurable horizon, with natural
    decay when entities are inactive.

    Reputation is ROLE-CONTEXTUALIZED — stored per (entity_lct, role_lct) pair.

    Usage:
        store = ReputationStore()
        store.record(delta)  # record a ReputationDelta
        score = store.current("lct:alice", "lct:role:analyst", "training")
    """

    # Decay params per spec section 7
    DEFAULT_HALF_LIFE_DAYS = 30.0
    DEFAULT_HORIZON_DAYS = 90
    INACTIVITY_GRACE_DAYS = 30
    INACTIVITY_RATE_PER_MONTH = 0.01
    INACTIVITY_ACCELERATE_MONTHS = 6
    INACTIVITY_ACCELERATE_FACTOR = 1.5
    MAX_INACTIVITY_DECAY = 0.5

    def __init__(self) -> None:
        # Key: (entity_lct, role_lct) → list of stored deltas
        self._deltas: Dict[tuple[str, str], List[_StoredDelta]] = {}
        # Key: (entity_lct, role_lct) → last action datetime
        self._last_action: Dict[tuple[str, str], datetime] = {}

    def record(self, delta: ReputationDelta, now: Optional[datetime] = None) -> None:
        """Record a ReputationDelta into the store."""
        key = (delta.subject_lct, delta.role_lct)
        ts = now or datetime.now(timezone.utc)

        if delta.timestamp:
            try:
                ts = datetime.fromisoformat(delta.timestamp)
            except (ValueError, TypeError):
                pass

        self._last_action[key] = ts

        if key not in self._deltas:
            self._deltas[key] = []

        # Store T3 deltas
        for dim, td in delta.t3_delta.items():
            self._deltas[key].append(_StoredDelta(
                dimension=dim, change=td.change, timestamp=ts,
            ))

        # Store V3 deltas
        for dim, td in delta.v3_delta.items():
            self._deltas[key].append(_StoredDelta(
                dimension=dim, change=td.change, timestamp=ts,
            ))

    def current(
        self,
        entity_lct: str,
        role_lct: str,
        dimension: str,
        *,
        horizon_days: int = DEFAULT_HORIZON_DAYS,
        half_life_days: float = DEFAULT_HALF_LIFE_DAYS,
        now: Optional[datetime] = None,
    ) -> float:
        """
        Compute current reputation for a specific entity+role+dimension.

        Per spec section 7: time-weighted aggregation with exponential
        recency weighting. Returns 0.5 (neutral) for unknown pairings.
        Result is clamped to [0.0, 1.0].
        """
        now_dt = now or datetime.now(timezone.utc)
        key = (entity_lct, role_lct)
        stored = self._deltas.get(key, [])

        # Filter by dimension and horizon
        cutoff = now_dt - timedelta(days=horizon_days)
        relevant = [
            d for d in stored
            if d.dimension == dimension and d.timestamp >= cutoff
        ]

        if not relevant:
            return 0.5  # Neutral starting point per spec

        weighted_sum = 0.0
        weight_sum = 0.0

        for d in relevant:
            age_days = max(0.0, (now_dt - d.timestamp).total_seconds() / 86400.0)
            recency_weight = math.exp(-age_days / half_life_days)
            weighted_sum += d.change * recency_weight
            weight_sum += recency_weight

        if weight_sum == 0:
            return 0.5

        # The spec computes: weighted_sum / weight_sum as current value.
        # But deltas are CHANGES, not absolute values. We apply them to
        # the neutral baseline of 0.5.
        aggregated = weighted_sum / weight_sum
        return _clamp(0.5 + aggregated)

    def inactivity_decay(
        self,
        entity_lct: str,
        role_lct: str,
        *,
        now: Optional[datetime] = None,
    ) -> float:
        """
        Compute inactivity decay penalty.

        Per spec section 7: no decay within 30 days, -0.01/month after that,
        accelerates 1.5x after 6 months, capped at -0.5.
        """
        now_dt = now or datetime.now(timezone.utc)
        key = (entity_lct, role_lct)
        last = self._last_action.get(key)

        if last is None:
            return 0.0

        days_inactive = max(0.0, (now_dt - last).total_seconds() / 86400.0)

        if days_inactive < self.INACTIVITY_GRACE_DAYS:
            return 0.0

        months_inactive = days_inactive / 30.0
        decay = -self.INACTIVITY_RATE_PER_MONTH * months_inactive

        if months_inactive > self.INACTIVITY_ACCELERATE_MONTHS:
            decay *= self.INACTIVITY_ACCELERATE_FACTOR

        return max(-self.MAX_INACTIVITY_DECAY, decay)

    def effective_reputation(
        self,
        entity_lct: str,
        role_lct: str,
        dimension: str,
        *,
        horizon_days: int = DEFAULT_HORIZON_DAYS,
        half_life_days: float = DEFAULT_HALF_LIFE_DAYS,
        now: Optional[datetime] = None,
    ) -> float:
        """Current reputation with inactivity decay applied."""
        now_dt = now or datetime.now(timezone.utc)
        base = self.current(
            entity_lct, role_lct, dimension,
            horizon_days=horizon_days,
            half_life_days=half_life_days,
            now=now_dt,
        )
        decay = self.inactivity_decay(entity_lct, role_lct, now=now_dt)
        return _clamp(base + decay)

    def has_history(self, entity_lct: str, role_lct: str) -> bool:
        """Check if store has any deltas for this entity+role pair."""
        return (entity_lct, role_lct) in self._deltas


# ── Action Outcome Processing ──────────────────────────────────


@dataclass
class ActionOutcomeResult:
    """Result of processing a completed R7Action through the reputation pipeline.

    Contains the reputation delta (if rules matched), the updated T3/V3
    tensors for the actor's role, and ATP settlement details.
    """
    delta: Optional[ReputationDelta]
    updated_t3: T3
    updated_v3: V3
    atp_committed: float
    atp_rolled_back: float


def process_action_outcome(
    action: R7Action,
    engine: ReputationEngine,
    profile: TrustProfile,
    account: ATPAccount,
    *,
    store: Optional[ReputationStore] = None,
) -> ActionOutcomeResult:
    """Process a completed R7Action through the reputation and trust pipeline.

    This is the core "action → consequence" composition function. It takes
    a completed action (status SUCCESS or FAILURE) and:

    1. Evaluates reputation rules via the engine → ReputationDelta
    2. Applies T3/V3 deltas to the actor's TrustProfile
    3. Settles ATP: commits locked stake on success, rolls back on failure
    4. Optionally records the delta in a ReputationStore

    Does NOT evaluate policy (that's PolicyGate). Operates on the OUTCOME
    of an already-completed action.

    Args:
        action: A completed R7Action (status must be SUCCESS or FAILURE).
        engine: ReputationEngine with rules to evaluate.
        profile: Actor's TrustProfile (mutated in place with updated tensors).
        account: Actor's ATPAccount (mutated in place with ATP settlement).
        store: Optional ReputationStore to record the delta for aggregation.

    Returns:
        ActionOutcomeResult with delta, updated tensors, and ATP settlement.

    Raises:
        ValueError: If action status is not SUCCESS or FAILURE.
    """
    status = action.result.status
    if status not in (ActionStatus.SUCCESS, ActionStatus.FAILURE):
        raise ValueError(
            f"Cannot process action with status '{status.value}'; "
            f"expected 'success' or 'failure'"
        )

    # Step 1: Evaluate reputation rules
    delta = engine.evaluate(action)

    # Step 2: Apply T3/V3 deltas to the actor's trust profile
    role = action.role.role_lct
    current_t3 = profile.get_t3(role)
    current_v3 = profile.get_v3(role)

    if delta is not None:
        # Apply T3 deltas
        t3_kwargs = {
            "talent": current_t3.talent,
            "training": current_t3.training,
            "temperament": current_t3.temperament,
        }
        for dim, td in delta.t3_delta.items():
            t3_kwargs[dim] = td.to_value

        # Apply V3 deltas
        v3_kwargs = {
            "veracity": current_v3.veracity,
            "validity": current_v3.validity,
            "valuation": current_v3.valuation,
        }
        for dim, td in delta.v3_delta.items():
            v3_kwargs[dim] = td.to_value

        updated_t3 = T3(**t3_kwargs)
        updated_v3 = V3(**v3_kwargs)
        profile.set_role(role, t3=updated_t3, v3=updated_v3)
    else:
        updated_t3 = current_t3
        updated_v3 = current_v3

    # Step 3: Settle ATP — commit on success, rollback on failure
    atp_stake = action.request.atp_stake
    atp_committed = 0.0
    atp_rolled_back = 0.0

    if atp_stake > 0:
        if status == ActionStatus.SUCCESS:
            atp_committed = account.commit(atp_stake)
        else:
            atp_rolled_back = account.rollback(atp_stake)

    # Step 4: Optionally record in store for time-weighted aggregation
    if delta is not None and store is not None:
        store.record(delta)

    return ActionOutcomeResult(
        delta=delta,
        updated_t3=updated_t3,
        updated_v3=updated_v3,
        atp_committed=atp_committed,
        atp_rolled_back=atp_rolled_back,
    )
