#!/usr/bin/env python3
"""
R6→R7 Evolution Reference Implementation
RFC: RFC-R7-FRAMEWORK-001
Spec: r7-framework.md + reputation-computation.md

Implements the evolution from R6 (implicit reputation) to R7 (explicit reputation output).
R7 = Rules + Role + Request + Reference + Resource → Result + Reputation

Key innovations:
- ReputationDelta as first-class output (not buried in Result)
- Role-contextualized T3/V3 deltas (not global)
- Multi-factor reputation computation with weighted contributing factors
- Reputation rules engine (trigger conditions, modifiers, impact)
- Witness selection and attestation for reputation changes
- Time-weighted aggregation and natural decay
- R6→R7 migration path (wrapper, parallel operation)
- R7 error hierarchy with reputation-aware error handling
"""

import hashlib
import json
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# ============================================================
# Section 1: Core Data Structures
# ============================================================

class R7Error(Exception):
    """Base R7 error"""
    pass

class RuleViolation(R7Error):
    """Action violates governing rules"""
    pass

class RoleUnauthorized(R7Error):
    """Actor lacks required role or permissions"""
    pass

class RequestMalformed(R7Error):
    """Request structure or parameters invalid"""
    pass

class ReferenceInvalid(R7Error):
    """Referenced entities not found or invalid"""
    pass

class ResourceInsufficient(R7Error):
    """Required resources unavailable"""
    pass

class ResultInvalid(R7Error):
    """Result violates output constraints"""
    pass

class ReputationComputationError(R7Error):
    """Reputation delta cannot be computed"""
    pass


class ActionStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"


@dataclass
class RuleSet:
    """R7 Rules: governing constraints and policies"""
    law_hash: str = ""
    society: str = ""
    constraints: List[Dict[str, Any]] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    prohibitions: List[str] = field(default_factory=list)


@dataclass
class RolePairing:
    """R7 Role: contextual identity for action execution"""
    actor: str = ""            # Entity LCT
    role_lct: str = ""         # Role LCT
    paired_at: str = ""
    t3_in_role: Dict[str, float] = field(default_factory=lambda: {
        "talent": 0.5, "training": 0.5, "temperament": 0.5
    })
    v3_in_role: Dict[str, float] = field(default_factory=lambda: {
        "veracity": 0.5, "validity": 0.5, "value": 0.5
    })
    mrh_link: str = ""


@dataclass
class Request:
    """R7 Request: action intent and parameters"""
    action: str = ""
    target: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    atp_stake: float = 0.0
    nonce: str = field(default_factory=lambda: str(uuid.uuid4()))
    proof_of_agency: Optional[Dict[str, Any]] = None


@dataclass
class ReferenceContext:
    """R7 Reference: historical context and precedents"""
    precedents: List[Dict[str, Any]] = field(default_factory=list)
    mrh_context: Dict[str, Any] = field(default_factory=dict)
    interpretations: List[Dict[str, Any]] = field(default_factory=list)
    witnesses: List[Dict[str, Any]] = field(default_factory=list)

    def get_action_history(self, entity_lct: str, action_type: str) -> List[Dict]:
        return [p for p in self.precedents
                if p.get("actor") == entity_lct and p.get("action") == action_type]

    def get_current_witnesses(self) -> List[Dict]:
        return self.witnesses


@dataclass
class Resource:
    """R7 Resource: computational, economic, material resources"""
    required: Dict[str, Any] = field(default_factory=lambda: {"atp": 0})
    available: Dict[str, Any] = field(default_factory=lambda: {"atp_balance": 1000})
    pricing: Dict[str, float] = field(default_factory=dict)
    escrow: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Result:
    """R7 Result: deterministic outcome"""
    status: ActionStatus = ActionStatus.SUCCESS
    output: Dict[str, Any] = field(default_factory=dict)
    resource_consumed: Dict[str, Any] = field(default_factory=dict)
    attestations: List[Dict[str, Any]] = field(default_factory=list)
    ledger_proof: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    atp_cost: float = 0.0
    value_created: float = 0.0

    @classmethod
    def failed(cls, reason: str) -> "Result":
        return cls(status=ActionStatus.FAILURE, error=reason)


@dataclass
class ContributingFactor:
    """A factor that contributed to a reputation change"""
    factor: str
    weight: float
    value: Any = None
    normalized_weight: float = 0.0


@dataclass
class WitnessAttestation:
    """Witness attestation of a reputation change"""
    lct: str
    witness_type: str = "role_validator"
    signature: str = ""
    timestamp: str = ""
    confidence: float = 1.0
    verified: bool = True


@dataclass
class TensorChange:
    """Change to a single tensor dimension"""
    change: float
    from_value: float
    to_value: float


@dataclass
class ReputationDelta:
    """R7 Reputation: explicit trust/value changes from an action"""
    subject_lct: str = ""
    role_lct: str = ""
    role_pairing_in_mrh: Dict[str, Any] = field(default_factory=dict)
    action_type: str = ""
    action_target: str = ""
    action_id: str = ""
    rule_triggered: Optional[str] = None
    reason: str = ""
    t3_delta: Dict[str, TensorChange] = field(default_factory=dict)
    v3_delta: Dict[str, TensorChange] = field(default_factory=dict)
    contributing_factors: List[ContributingFactor] = field(default_factory=list)
    witnesses: List[WitnessAttestation] = field(default_factory=list)
    net_trust_change: float = 0.0
    net_value_change: float = 0.0
    timestamp: str = ""

    @classmethod
    def negative(cls, subject_lct: str, reason: str) -> "ReputationDelta":
        return cls(
            subject_lct=subject_lct,
            reason=reason,
            t3_delta={"temperament": TensorChange(-0.005, 0.5, 0.495)},
            net_trust_change=-0.005
        )

    @classmethod
    def empty(cls, subject_lct: str) -> "ReputationDelta":
        return cls(subject_lct=subject_lct, reason="No reputation rules triggered")

    def to_dict(self) -> Dict[str, Any]:
        t3 = {}
        for dim, tc in self.t3_delta.items():
            t3[dim] = {"change": tc.change, "from": tc.from_value, "to": tc.to_value}
        v3 = {}
        for dim, tc in self.v3_delta.items():
            v3[dim] = {"change": tc.change, "from": tc.from_value, "to": tc.to_value}
        return {
            "subject_lct": self.subject_lct,
            "role_lct": self.role_lct,
            "action_type": self.action_type,
            "action_id": self.action_id,
            "rule_triggered": self.rule_triggered,
            "reason": self.reason,
            "t3_delta": t3,
            "v3_delta": v3,
            "contributing_factors": [
                {"factor": f.factor, "weight": f.weight} for f in self.contributing_factors
            ],
            "witnesses": [{"lct": w.lct, "type": w.witness_type} for w in self.witnesses],
            "net_trust_change": self.net_trust_change,
            "net_value_change": self.net_value_change,
            "timestamp": self.timestamp,
        }


@dataclass
class R7Action:
    """Complete R7 action with all 7 components"""
    rules: RuleSet = field(default_factory=RuleSet)
    role: RolePairing = field(default_factory=RolePairing)
    request: Request = field(default_factory=Request)
    reference: ReferenceContext = field(default_factory=ReferenceContext)
    resource: Resource = field(default_factory=Resource)
    result: Optional[Result] = None
    reputation: Optional[ReputationDelta] = None


# ============================================================
# Section 2: Reputation Rules Engine
# ============================================================

@dataclass
class ReputationModifier:
    """Modifier applied to reputation change based on conditions"""
    condition: str
    multiplier: float


@dataclass
class DimensionImpact:
    """Impact on a single T3/V3 dimension"""
    base_delta: float
    modifiers: List[ReputationModifier] = field(default_factory=list)


@dataclass
class ReputationRule:
    """A rule that maps outcomes to reputation changes"""
    rule_id: str
    trigger_conditions: Dict[str, Any] = field(default_factory=dict)
    t3_impact: Dict[str, DimensionImpact] = field(default_factory=dict)
    v3_impact: Dict[str, DimensionImpact] = field(default_factory=dict)
    witnesses_required: int = 1
    law_oracle: str = ""
    category: str = "success"  # success, failure, exceptional, violation
    affects_trust: bool = True
    affects_value: bool = True


def _matches_trigger(rule: ReputationRule, action: R7Action, result: Result) -> bool:
    """Check if a rule's trigger conditions are met."""
    conds = rule.trigger_conditions
    if "action_type" in conds and action.request.action != conds["action_type"]:
        if conds["action_type"] != "*":
            return False
    if "result_status" in conds:
        expected = conds["result_status"]
        if expected == "success" and result.status != ActionStatus.SUCCESS:
            return False
        if expected == "failure" and result.status != ActionStatus.FAILURE:
            return False
        if expected == "error" and result.status != ActionStatus.ERROR:
            return False
    if "quality_threshold" in conds:
        quality = result.output.get("quality", result.output.get("accuracy", 0.0))
        if quality < conds["quality_threshold"]:
            return False
    if "category" in conds and rule.category != conds["category"]:
        return False
    return True


# ============================================================
# Section 3: Multi-Factor Analysis
# ============================================================

def _analyze_factors(action: R7Action, result: Result, rule: ReputationRule) -> List[ContributingFactor]:
    """Analyze contributing factors for a reputation change."""
    factors = []

    # Quality-based
    quality = result.output.get("quality", result.output.get("accuracy", None))
    threshold = rule.trigger_conditions.get("quality_threshold", None)
    if quality is not None and threshold is not None and quality > threshold:
        exceed_ratio = (quality - threshold) / max(threshold, 0.01)
        factors.append(ContributingFactor("exceed_quality", min(exceed_ratio, 1.0), quality))

    # Deadline-based
    deadline_str = action.request.constraints.get("deadline")
    if deadline_str and result.status == ActionStatus.SUCCESS:
        factors.append(ContributingFactor("deadline_met", 0.3, True))
        completion_time = result.output.get("completion_time_hours", None)
        if completion_time is not None and completion_time < 0.8:
            factors.append(ContributingFactor("early_completion", 0.2, completion_time))

    # Resource efficiency
    required_atp = action.resource.required.get("atp", 0)
    consumed_atp = result.resource_consumed.get("atp", result.atp_cost)
    if required_atp > 0 and consumed_atp < required_atp:
        efficiency = 1.0 - (consumed_atp / required_atp)
        factors.append(ContributingFactor("resource_efficiency", efficiency * 0.2, efficiency))

    # Accuracy
    accuracy = result.output.get("accuracy")
    if accuracy is not None and accuracy > 0.95:
        factors.append(ContributingFactor("high_accuracy", 0.4, accuracy))

    # Witness count
    witness_count = len(action.reference.get_current_witnesses())
    if witness_count >= 3:
        factors.append(ContributingFactor("well_witnessed", 0.15, witness_count))

    # Rule compliance
    if result.status == ActionStatus.SUCCESS:
        factors.append(ContributingFactor("successful_execution", 0.3, True))
    elif result.status == ActionStatus.FAILURE:
        factors.append(ContributingFactor("failed_execution", 0.4, False))

    # Normalize weights
    total_weight = sum(f.weight for f in factors)
    if total_weight > 0:
        for f in factors:
            f.normalized_weight = f.weight / total_weight

    return factors


def _factor_applies(condition: str, factors: List[ContributingFactor]) -> bool:
    """Check if a modifier condition is satisfied by the contributing factors."""
    for f in factors:
        if f.factor == condition:
            return True
    return False


# ============================================================
# Section 4: Reputation Computation
# ============================================================

def _compute_dimension_delta(
    dimension: str,
    rules: List[ReputationRule],
    factors: List[ContributingFactor],
    is_trust: bool = True
) -> float:
    """Compute delta for a single T3 or V3 dimension."""
    total_delta = 0.0
    for rule in rules:
        impacts = rule.t3_impact if is_trust else rule.v3_impact
        if dimension not in impacts:
            continue
        impact = impacts[dimension]
        base_delta = impact.base_delta
        multiplier = 1.0
        for mod in impact.modifiers:
            if _factor_applies(mod.condition, factors):
                multiplier *= mod.multiplier
        total_delta += base_delta * multiplier
    return max(-1.0, min(1.0, total_delta))


def compute_reputation_delta(
    action: R7Action,
    result: Result,
    rules: List[ReputationRule]
) -> ReputationDelta:
    """
    Compute explicit reputation changes based on action outcome.
    Core R7 innovation: reputation is a first-class output.
    """
    ts = datetime.now(timezone.utc).isoformat()
    action_id = hashlib.sha256(
        f"{action.request.nonce}:{ts}".encode()
    ).hexdigest()[:16]

    reputation = ReputationDelta(
        subject_lct=action.role.actor,
        role_lct=action.role.role_lct,
        role_pairing_in_mrh={
            "entity": action.role.actor,
            "role": action.role.role_lct,
            "paired_at": action.role.paired_at,
            "mrh_link": action.role.mrh_link,
        },
        action_type=action.request.action,
        action_target=action.request.target,
        action_id=f"txn:{action_id}",
        timestamp=ts,
    )

    # Find triggered rules
    triggered = [r for r in rules if _matches_trigger(r, action, result)]
    if not triggered:
        reputation.reason = "No reputation rules triggered"
        return reputation

    # Analyze contributing factors
    all_factors = []
    for rule in triggered:
        rule_factors = _analyze_factors(action, result, rule)
        all_factors.extend(rule_factors)

    # Deduplicate factors by name (keep highest weight)
    seen = {}
    for f in all_factors:
        if f.factor not in seen or f.weight > seen[f.factor].weight:
            seen[f.factor] = f
    all_factors = list(seen.values())

    # Re-normalize
    total_weight = sum(f.weight for f in all_factors)
    if total_weight > 0:
        for f in all_factors:
            f.normalized_weight = f.weight / total_weight

    # Compute T3 deltas
    t3_changes = {}
    for dim in ["talent", "training", "temperament"]:
        delta = _compute_dimension_delta(dim, triggered, all_factors, is_trust=True)
        if delta != 0:
            current = action.role.t3_in_role.get(dim, 0.5)
            new_val = max(0.0, min(1.0, current + delta))
            t3_changes[dim] = TensorChange(delta, current, new_val)

    # Compute V3 deltas
    v3_changes = {}
    for dim in ["veracity", "validity", "value"]:
        delta = _compute_dimension_delta(dim, triggered, all_factors, is_trust=False)
        if delta != 0:
            current = action.role.v3_in_role.get(dim, 0.5)
            new_val = max(0.0, min(1.0, current + delta))
            v3_changes[dim] = TensorChange(delta, current, new_val)

    # Assemble reputation
    reputation.t3_delta = t3_changes
    reputation.v3_delta = v3_changes
    reputation.contributing_factors = all_factors
    reputation.rule_triggered = triggered[0].rule_id
    reputation.net_trust_change = sum(tc.change for tc in t3_changes.values())
    reputation.net_value_change = sum(tc.change for tc in v3_changes.values())

    # Generate reason
    parts = []
    if result.status == ActionStatus.SUCCESS:
        parts.append(f"Successful {action.request.action}")
    elif result.status == ActionStatus.FAILURE:
        parts.append(f"Failed {action.request.action}")
    else:
        parts.append(f"Error in {action.request.action}")
    factor_names = [f.factor for f in all_factors[:3]]
    if factor_names:
        parts.append(f"factors: {', '.join(factor_names)}")
    reputation.reason = "; ".join(parts)

    return reputation


# ============================================================
# Section 5: R7 Execution Pipeline
# ============================================================

class R7Executor:
    """Full R7 execution pipeline: validate → execute → compute reputation → settle."""

    def __init__(self, reputation_rules: List[ReputationRule] = None):
        self.rules = reputation_rules or []
        self.ledger: List[Dict[str, Any]] = []
        self.reputation_history: List[ReputationDelta] = []
        self.role_t3: Dict[str, Dict[str, float]] = {}  # (entity,role) → t3
        self.role_v3: Dict[str, Dict[str, float]] = {}
        self.action_count = 0

    def _role_key(self, entity: str, role: str) -> str:
        return f"{entity}|{role}"

    def validate(self, action: R7Action) -> Tuple[bool, str]:
        """Pre-execution validation."""
        # Check role exists
        if not action.role.actor:
            return False, "Actor LCT required"
        if not action.role.role_lct:
            return False, "Role LCT required"

        # Check request
        if not action.request.action:
            return False, "Action type required"

        # Check permissions
        if action.request.action in action.rules.prohibitions:
            return False, f"Action '{action.request.action}' is prohibited"

        if action.rules.permissions and action.request.action not in action.rules.permissions:
            # Check for wildcard
            has_wildcard = any(p == "*" or p.endswith(":*") for p in action.rules.permissions)
            if not has_wildcard:
                return False, f"Action '{action.request.action}' not in permissions"

        # Check resource availability
        required_atp = action.resource.required.get("atp", 0)
        available_atp = action.resource.available.get("atp_balance", 0)
        if required_atp > available_atp:
            return False, f"Insufficient ATP: need {required_atp}, have {available_atp}"

        # Check constraints
        for constraint in action.rules.constraints:
            ctype = constraint.get("type")
            cvalue = constraint.get("value")
            if ctype == "atp_minimum" and action.request.atp_stake < cvalue:
                return False, f"ATP stake {action.request.atp_stake} below minimum {cvalue}"

        return True, "Validation passed"

    def execute(self, action: R7Action) -> Tuple[Result, ReputationDelta]:
        """Execute R7 action with explicit reputation output."""
        # 1. Validate
        valid, reason = self.validate(action)
        if not valid:
            result = Result.failed(reason)
            rep = ReputationDelta.negative(action.role.actor, f"validation_failed: {reason}")
            rep.role_lct = action.role.role_lct
            rep.action_type = action.request.action
            rep.timestamp = datetime.now(timezone.utc).isoformat()
            action.result = result
            action.reputation = rep
            self.reputation_history.append(rep)
            return result, rep

        # 2. Simulate action execution
        result = self._perform_action(action)

        # 3. Compute reputation (THE R7 INNOVATION)
        reputation = compute_reputation_delta(action, result, self.rules)

        # 4. Apply tensor updates to role pairing
        self._apply_tensor_updates(action.role, reputation)

        # 5. Record to ledger
        self._record_to_ledger(action, result, reputation)

        # 6. Store
        action.result = result
        action.reputation = reputation
        self.reputation_history.append(reputation)
        self.action_count += 1

        return result, reputation

    def _perform_action(self, action: R7Action) -> Result:
        """Simulate action execution. In production, this dispatches to actual handlers."""
        # Simulated action based on type
        action_type = action.request.action
        atp_cost = action.resource.required.get("atp", 0)
        quality = action.request.parameters.get("quality", 0.8)
        accuracy = action.request.parameters.get("accuracy", None)

        output = {
            "action": action_type,
            "quality": quality,
            "processed": True,
        }
        if accuracy is not None:
            output["accuracy"] = accuracy

        if action.request.constraints.get("deadline"):
            output["completion_time_hours"] = action.request.parameters.get(
                "completion_time_hours", 0.5
            )

        return Result(
            status=ActionStatus.SUCCESS,
            output=output,
            resource_consumed={"atp": atp_cost * 0.9},
            atp_cost=atp_cost * 0.9,
            value_created=quality * atp_cost,
            ledger_proof={"txHash": f"0x{uuid.uuid4().hex[:16]}"},
        )

    def _apply_tensor_updates(self, role: RolePairing, reputation: ReputationDelta):
        """Apply T3/V3 deltas to the specific MRH role pairing."""
        key = self._role_key(role.actor, role.role_lct)

        # Initialize if needed
        if key not in self.role_t3:
            self.role_t3[key] = dict(role.t3_in_role)
            self.role_v3[key] = dict(role.v3_in_role)

        # Apply T3 deltas
        for dim, tc in reputation.t3_delta.items():
            self.role_t3[key][dim] = tc.to_value
            role.t3_in_role[dim] = tc.to_value

        # Apply V3 deltas
        for dim, tc in reputation.v3_delta.items():
            self.role_v3[key][dim] = tc.to_value
            role.v3_in_role[dim] = tc.to_value

    def _record_to_ledger(self, action: R7Action, result: Result, reputation: ReputationDelta):
        """Record R7 transaction to ledger."""
        entry = {
            "action_type": action.request.action,
            "actor": action.role.actor,
            "role": action.role.role_lct,
            "status": result.status.value,
            "reputation": reputation.to_dict(),
            "timestamp": reputation.timestamp,
        }
        self.ledger.append(entry)

    def get_reputation_history(
        self, entity_lct: str, role_lct: str = None
    ) -> List[ReputationDelta]:
        """Get reputation history for an entity, optionally filtered by role."""
        history = [r for r in self.reputation_history if r.subject_lct == entity_lct]
        if role_lct:
            history = [r for r in history if r.role_lct == role_lct]
        return history


# ============================================================
# Section 6: R6→R7 Migration
# ============================================================

class R6Executor:
    """Legacy R6 executor: Rules + Role + Request + Reference + Resource → Result"""

    def __init__(self, r7_executor: R7Executor):
        self._r7 = r7_executor
        self._reputation_log: List[ReputationDelta] = []

    def execute_r6_action(
        self,
        rules: RuleSet,
        role: RolePairing,
        request: Request,
        reference: ReferenceContext,
        resource: Resource
    ) -> Result:
        """
        Legacy R6 interface. Internally calls R7 and logs reputation silently.
        Backward compatible: returns only Result.
        """
        action = R7Action(
            rules=rules,
            role=role,
            request=request,
            reference=reference,
            resource=resource,
        )
        result, reputation = self._r7.execute(action)

        # Log reputation silently for backward compatibility
        if reputation.net_trust_change != 0 or reputation.net_value_change != 0:
            self._reputation_log.append(reputation)

        return result

    def get_silent_reputation_log(self) -> List[ReputationDelta]:
        """Access reputation changes that were logged silently via R6 interface."""
        return self._reputation_log


class R6ToR7Migrator:
    """Automated R6 → R7 migration utilities."""

    @staticmethod
    def wrap_r6_result(result: Result, action: R7Action, rules: List[ReputationRule]) -> Tuple[Result, ReputationDelta]:
        """Convert an R6-style result to R7 (result + reputation)."""
        reputation = compute_reputation_delta(action, result, rules)
        return result, reputation

    @staticmethod
    def extract_reputation_from_result(result: Result) -> Dict[str, float]:
        """Extract implicit reputation signals from an R6 result."""
        signals = {}
        if result.status == ActionStatus.SUCCESS:
            signals["temperament"] = +0.005
            signals["training"] = +0.01
        elif result.status == ActionStatus.FAILURE:
            signals["temperament"] = -0.01
            signals["training"] = -0.005
        if result.value_created > 0:
            signals["value"] = min(result.value_created / 100.0, 0.02)
        return signals


# ============================================================
# Section 7: Witness Selection
# ============================================================

class WitnessSelector:
    """Select witnesses for reputation changes."""

    def __init__(self):
        self.validators: Dict[str, List[str]] = {}  # role → [validator_lcts]
        self.law_oracles: List[str] = []

    def register_validator(self, role: str, validator_lct: str):
        if role not in self.validators:
            self.validators[role] = []
        self.validators[role].append(validator_lct)

    def register_law_oracle(self, oracle_lct: str):
        self.law_oracles.append(oracle_lct)

    def select_witnesses(
        self,
        action: R7Action,
        reputation: ReputationDelta,
        required_count: int = 2
    ) -> List[WitnessAttestation]:
        """Select witnesses for a reputation change."""
        candidates = []

        # Priority 1: Law oracles
        for oracle in self.law_oracles:
            candidates.append(WitnessAttestation(
                lct=oracle,
                witness_type="law_oracle",
                timestamp=datetime.now(timezone.utc).isoformat(),
                confidence=0.99,
            ))

        # Priority 2: Role validators
        role_type = action.role.role_lct.split(":")[-1] if action.role.role_lct else ""
        for role_key, validators in self.validators.items():
            if role_key in role_type or role_key == "*":
                for v in validators:
                    candidates.append(WitnessAttestation(
                        lct=v,
                        witness_type="role_validator",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        confidence=0.95,
                    ))

        # Priority 3: MRH witnesses from reference
        for w in action.reference.get_current_witnesses():
            candidates.append(WitnessAttestation(
                lct=w.get("lct", w.get("id", f"witness:{uuid.uuid4().hex[:8]}")),
                witness_type="mrh_witness",
                timestamp=datetime.now(timezone.utc).isoformat(),
                confidence=0.90,
            ))

        # Select required count, deduplicated
        selected = []
        seen_lcts = set()
        for c in candidates:
            if c.lct not in seen_lcts and len(selected) < required_count:
                # Generate signature
                sig_input = f"{reputation.action_id}:{c.lct}:{reputation.timestamp}"
                c.signature = hashlib.sha256(sig_input.encode()).hexdigest()[:32]
                selected.append(c)
                seen_lcts.add(c.lct)

        return selected


# ============================================================
# Section 8: Time-Weighted Aggregation & Decay
# ============================================================

class ReputationAggregator:
    """Aggregate reputation deltas over time with decay."""

    def __init__(self, half_life_days: float = 30.0, decay_start_days: int = 30):
        self.half_life_days = half_life_days
        self.decay_start_days = decay_start_days

    def compute_current_reputation(
        self,
        deltas: List[ReputationDelta],
        dimension: str,
        is_trust: bool = True,
        base_value: float = 0.5,
        now: datetime = None,
    ) -> float:
        """
        Compute current reputation by time-weighted aggregation.
        Role-contextualized: caller must pre-filter by entity+role.
        """
        if now is None:
            now = datetime.now(timezone.utc)

        relevant_deltas = []
        for d in deltas:
            changes = d.t3_delta if is_trust else d.v3_delta
            if dimension in changes:
                try:
                    ts = datetime.fromisoformat(d.timestamp.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    ts = now
                relevant_deltas.append((ts, changes[dimension].change))

        if not relevant_deltas:
            return base_value

        weighted_sum = 0.0
        weight_sum = 0.0
        for ts, change in relevant_deltas:
            age_days = max(0, (now - ts).total_seconds() / 86400.0)
            recency_weight = math.exp(-age_days / self.half_life_days)
            weighted_sum += change * recency_weight
            weight_sum += recency_weight

        if weight_sum == 0:
            return base_value

        current = base_value + weighted_sum
        return max(0.0, min(1.0, current))

    def apply_decay(
        self,
        current_value: float,
        last_action_timestamp: datetime,
        now: datetime = None
    ) -> float:
        """Apply natural reputation decay from inactivity."""
        if now is None:
            now = datetime.now(timezone.utc)

        days_inactive = (now - last_action_timestamp).total_seconds() / 86400.0

        if days_inactive < self.decay_start_days:
            return 0.0

        months_inactive = days_inactive / 30.0
        decay = -0.01 * months_inactive

        if months_inactive > 6:
            decay *= 1.5

        return max(-0.5, decay)

    def get_reputation_summary(
        self,
        deltas: List[ReputationDelta],
        now: datetime = None,
    ) -> Dict[str, Any]:
        """Aggregate summary of reputation changes."""
        if not deltas:
            return {
                "total_actions": 0,
                "net_trust_change": 0.0,
                "net_value_change": 0.0,
                "violations": 0,
                "witnesses": 0,
            }

        total_trust = sum(d.net_trust_change for d in deltas)
        total_value = sum(d.net_value_change for d in deltas)
        violations = sum(1 for d in deltas if d.net_trust_change < -0.05)
        all_witnesses = set()
        for d in deltas:
            for w in d.witnesses:
                all_witnesses.add(w.lct)

        return {
            "total_actions": len(deltas),
            "net_trust_change": total_trust,
            "net_value_change": total_value,
            "violations": violations,
            "witnesses": len(all_witnesses),
        }


# ============================================================
# Section 9: Diminishing Returns & Gaming Prevention
# ============================================================

class GamingPrevention:
    """Prevent reputation gaming through diminishing returns and anomaly detection."""

    def __init__(self, window_hours: int = 24):
        self.window_hours = window_hours
        self.action_log: List[Tuple[str, str, datetime]] = []  # (entity, action_type, time)

    def record_action(self, entity: str, action_type: str, when: datetime = None):
        if when is None:
            when = datetime.now(timezone.utc)
        self.action_log.append((entity, action_type, when))

    def get_diminishing_factor(self, entity: str, action_type: str, now: datetime = None) -> float:
        """
        Compute diminishing returns factor for repeated identical actions.
        Returns multiplier [0.1, 1.0] — decreases with repetition.
        """
        if now is None:
            now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=self.window_hours)
        recent_count = sum(
            1 for e, a, t in self.action_log
            if e == entity and a == action_type and t > cutoff
        )
        if recent_count <= 1:
            return 1.0
        # Exponential decay: 0.8^(n-1), floor at 0.1
        return max(0.1, 0.8 ** (recent_count - 1))

    def detect_anomaly(self, entity: str, now: datetime = None) -> Tuple[bool, str]:
        """Detect anomalous patterns suggesting gaming."""
        if now is None:
            now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=self.window_hours)
        recent = [(e, a, t) for e, a, t in self.action_log if e == entity and t > cutoff]

        # Check rate
        if len(recent) > 100:
            return True, f"Rate limit exceeded: {len(recent)} actions in {self.window_hours}h"

        # Check diversity
        action_types = set(a for _, a, _ in recent)
        if len(recent) > 10 and len(action_types) == 1:
            return True, f"Low diversity: {len(recent)} actions all same type"

        return False, "No anomaly detected"


# ============================================================
# Section 10: Federation Reputation Oracle
# ============================================================

class FederationReputationOracle:
    """Federation-wide reputation tracking across societies."""

    def __init__(self):
        self.society_reputations: Dict[str, List[ReputationDelta]] = {}

    def record(self, society_id: str, reputation: ReputationDelta):
        if society_id not in self.society_reputations:
            self.society_reputations[society_id] = []
        self.society_reputations[society_id].append(reputation)

    def get_society_summary(self, society_id: str) -> Dict[str, Any]:
        """Get reputation summary for a society."""
        deltas = self.society_reputations.get(society_id, [])
        aggregator = ReputationAggregator()
        return aggregator.get_reputation_summary(deltas)

    def get_cross_society_reputation(self, entity_lct: str) -> Dict[str, Dict[str, Any]]:
        """Get entity's reputation across all societies."""
        result = {}
        aggregator = ReputationAggregator()
        for society_id, deltas in self.society_reputations.items():
            entity_deltas = [d for d in deltas if d.subject_lct == entity_lct]
            if entity_deltas:
                result[society_id] = aggregator.get_reputation_summary(entity_deltas)
        return result


# ============================================================
# Section 11: Standard Reputation Rules Library
# ============================================================

def create_standard_rules() -> List[ReputationRule]:
    """Create standard reputation rules covering common action types."""
    rules = []

    # Rule 1: Successful action
    rules.append(ReputationRule(
        rule_id="successful_action",
        trigger_conditions={"action_type": "*", "result_status": "success"},
        t3_impact={
            "training": DimensionImpact(0.01, [
                ReputationModifier("deadline_met", 1.5),
                ReputationModifier("exceed_quality", 1.2),
            ]),
            "temperament": DimensionImpact(0.005, [
                ReputationModifier("early_completion", 1.3),
            ]),
        },
        v3_impact={
            "veracity": DimensionImpact(0.005, [
                ReputationModifier("high_accuracy", 1.5),
            ]),
        },
        category="success",
    ))

    # Rule 2: Failed action
    rules.append(ReputationRule(
        rule_id="failed_action",
        trigger_conditions={"action_type": "*", "result_status": "failure"},
        t3_impact={
            "training": DimensionImpact(-0.005),
            "temperament": DimensionImpact(-0.01),
        },
        v3_impact={
            "validity": DimensionImpact(-0.01),
        },
        category="failure",
    ))

    # Rule 3: Exceptional performance (quality > 0.95)
    rules.append(ReputationRule(
        rule_id="exceptional_performance",
        trigger_conditions={"action_type": "*", "result_status": "success", "quality_threshold": 0.95},
        t3_impact={
            "talent": DimensionImpact(0.02, [
                ReputationModifier("exceed_quality", 1.3),
            ]),
            "training": DimensionImpact(0.015),
        },
        v3_impact={
            "value": DimensionImpact(0.03, [
                ReputationModifier("resource_efficiency", 1.2),
            ]),
        },
        category="exceptional",
    ))

    # Rule 4: Ethical violation
    rules.append(ReputationRule(
        rule_id="ethical_violation",
        trigger_conditions={"action_type": "violate", "result_status": "failure"},
        t3_impact={
            "temperament": DimensionImpact(-0.10),
        },
        v3_impact={
            "veracity": DimensionImpact(-0.20),
            "validity": DimensionImpact(-0.15),
        },
        category="violation",
    ))

    # Rule 5: Witness attestation
    rules.append(ReputationRule(
        rule_id="witness_contribution",
        trigger_conditions={"action_type": "witness", "result_status": "success"},
        t3_impact={
            "temperament": DimensionImpact(0.008),
        },
        v3_impact={
            "veracity": DimensionImpact(0.01),
        },
        category="success",
    ))

    # Rule 6: Resource-efficient completion
    rules.append(ReputationRule(
        rule_id="efficient_completion",
        trigger_conditions={"action_type": "*", "result_status": "success"},
        v3_impact={
            "value": DimensionImpact(0.005, [
                ReputationModifier("resource_efficiency", 2.0),
            ]),
        },
        category="success",
    ))

    return rules


# ============================================================
# Section 12: RDF Serialization
# ============================================================

class ReputationRDFSerializer:
    """Serialize reputation deltas as RDF triples."""

    NS = "https://web4.io/ontology#"

    def serialize(self, reputation: ReputationDelta) -> List[str]:
        """Serialize a reputation delta to Turtle triples."""
        triples = []
        subj = f"<{self.NS}reputation/{reputation.action_id}>"

        triples.append(f'{subj} a <{self.NS}ReputationDelta> .')
        triples.append(f'{subj} <{self.NS}subject> "{reputation.subject_lct}" .')
        triples.append(f'{subj} <{self.NS}roleLCT> "{reputation.role_lct}" .')
        triples.append(f'{subj} <{self.NS}actionType> "{reputation.action_type}" .')
        triples.append(f'{subj} <{self.NS}netTrustChange> "{reputation.net_trust_change}"^^<http://www.w3.org/2001/XMLSchema#decimal> .')
        triples.append(f'{subj} <{self.NS}netValueChange> "{reputation.net_value_change}"^^<http://www.w3.org/2001/XMLSchema#decimal> .')

        if reputation.rule_triggered:
            triples.append(f'{subj} <{self.NS}ruleTriggered> "{reputation.rule_triggered}" .')

        for dim, tc in reputation.t3_delta.items():
            triples.append(f'{subj} <{self.NS}t3Delta/{dim}> "{tc.change}"^^<http://www.w3.org/2001/XMLSchema#decimal> .')

        for dim, tc in reputation.v3_delta.items():
            triples.append(f'{subj} <{self.NS}v3Delta/{dim}> "{tc.change}"^^<http://www.w3.org/2001/XMLSchema#decimal> .')

        for w in reputation.witnesses:
            triples.append(f'{subj} <{self.NS}witnessedBy> "{w.lct}" .')

        return triples


# ============================================================
# TESTS
# ============================================================

def _check(label: str, condition: bool, detail: str = ""):
    status = "PASS" if condition else "FAIL"
    msg = f"  [{status}] {label}"
    if detail and not condition:
        msg += f" — {detail}"
    print(msg)
    return condition


def run_tests():
    passed = 0
    failed = 0
    total = 0

    def check(label, condition, detail=""):
        nonlocal passed, failed, total
        total += 1
        if _check(label, condition, detail):
            passed += 1
        else:
            failed += 1

    # ── T1: Core Data Structures ──
    print("\n── T1: Core Data Structures ──")

    r = RuleSet(law_hash="abc", permissions=["read", "write"])
    check("T1.1 RuleSet creation", r.law_hash == "abc")
    check("T1.2 RuleSet permissions", "write" in r.permissions)

    role = RolePairing(
        actor="lct:web4:entity:alice",
        role_lct="lct:web4:role:analyst:abc",
        t3_in_role={"talent": 0.85, "training": 0.90, "temperament": 0.88},
        v3_in_role={"veracity": 0.92, "validity": 0.88, "value": 0.85},
    )
    check("T1.3 RolePairing actor", role.actor == "lct:web4:entity:alice")
    check("T1.4 RolePairing T3", role.t3_in_role["talent"] == 0.85)

    req = Request(action="analyze_dataset", target="resource:data:q4")
    check("T1.5 Request action", req.action == "analyze_dataset")
    check("T1.6 Request nonce generated", len(req.nonce) > 0)

    ref = ReferenceContext(precedents=[{"actor": "alice", "action": "analyze"}])
    check("T1.7 Reference history", len(ref.get_action_history("alice", "analyze")) == 1)

    res = Resource(required={"atp": 100}, available={"atp_balance": 500})
    check("T1.8 Resource ATP required", res.required["atp"] == 100)

    result = Result(status=ActionStatus.SUCCESS, output={"data": "result"})
    check("T1.9 Result status", result.status == ActionStatus.SUCCESS)

    result_fail = Result.failed("test error")
    check("T1.10 Result.failed", result_fail.status == ActionStatus.FAILURE)
    check("T1.11 Result.failed error", result_fail.error == "test error")

    # ── T2: ReputationDelta ──
    print("\n── T2: ReputationDelta ──")

    rep = ReputationDelta(
        subject_lct="lct:web4:entity:alice",
        role_lct="lct:web4:role:analyst:abc",
        action_type="analyze",
        t3_delta={"training": TensorChange(0.01, 0.90, 0.91)},
        v3_delta={"veracity": TensorChange(0.02, 0.85, 0.87)},
        net_trust_change=0.01,
        net_value_change=0.02,
    )
    check("T2.1 ReputationDelta subject", rep.subject_lct == "lct:web4:entity:alice")
    check("T2.2 ReputationDelta role-contextualized", rep.role_lct == "lct:web4:role:analyst:abc")
    check("T2.3 T3 delta training", rep.t3_delta["training"].change == 0.01)
    check("T2.4 V3 delta veracity", rep.v3_delta["veracity"].change == 0.02)
    check("T2.5 Net trust change", rep.net_trust_change == 0.01)

    d = rep.to_dict()
    check("T2.6 to_dict has t3_delta", "training" in d["t3_delta"])
    check("T2.7 to_dict t3 change", d["t3_delta"]["training"]["change"] == 0.01)

    neg = ReputationDelta.negative("alice", "bad")
    check("T2.8 negative delta", neg.net_trust_change < 0)

    empty = ReputationDelta.empty("alice")
    check("T2.9 empty delta", empty.net_trust_change == 0.0)

    # ── T3: R7 Error Hierarchy ──
    print("\n── T3: R7 Error Hierarchy ──")

    check("T3.1 RuleViolation is R7Error", issubclass(RuleViolation, R7Error))
    check("T3.2 RoleUnauthorized is R7Error", issubclass(RoleUnauthorized, R7Error))
    check("T3.3 RequestMalformed is R7Error", issubclass(RequestMalformed, R7Error))
    check("T3.4 ReferenceInvalid is R7Error", issubclass(ReferenceInvalid, R7Error))
    check("T3.5 ResourceInsufficient is R7Error", issubclass(ResourceInsufficient, R7Error))
    check("T3.6 ResultInvalid is R7Error", issubclass(ResultInvalid, R7Error))
    check("T3.7 ReputationComputationError", issubclass(ReputationComputationError, R7Error))

    errors = [RuleViolation, RoleUnauthorized, RequestMalformed,
              ReferenceInvalid, ResourceInsufficient, ResultInvalid,
              ReputationComputationError]
    check("T3.8 All 7 error types", len(errors) == 7)

    # ── T4: Reputation Rules Engine ──
    print("\n── T4: Reputation Rules Engine ──")

    rules = create_standard_rules()
    check("T4.1 Standard rules created", len(rules) >= 6)
    check("T4.2 Success rule exists", any(r.rule_id == "successful_action" for r in rules))
    check("T4.3 Failure rule exists", any(r.rule_id == "failed_action" for r in rules))
    check("T4.4 Exceptional rule exists", any(r.rule_id == "exceptional_performance" for r in rules))
    check("T4.5 Violation rule exists", any(r.rule_id == "ethical_violation" for r in rules))
    check("T4.6 Witness rule exists", any(r.rule_id == "witness_contribution" for r in rules))

    # Test trigger matching
    action = R7Action(
        role=RolePairing(actor="alice", role_lct="role:analyst"),
        request=Request(action="analyze_dataset"),
    )
    success_result = Result(status=ActionStatus.SUCCESS, output={"quality": 0.8})
    success_rule = rules[0]  # successful_action
    check("T4.7 Trigger matches success", _matches_trigger(success_rule, action, success_result))

    failure_result = Result(status=ActionStatus.FAILURE)
    check("T4.8 Success rule no match failure", not _matches_trigger(success_rule, action, failure_result))

    fail_rule = rules[1]  # failed_action
    check("T4.9 Failure rule matches failure", _matches_trigger(fail_rule, action, failure_result))

    # Quality threshold
    exceptional_rule = rules[2]  # exceptional_performance
    high_q = Result(status=ActionStatus.SUCCESS, output={"quality": 0.98})
    low_q = Result(status=ActionStatus.SUCCESS, output={"quality": 0.7})
    check("T4.10 Exceptional matches high quality", _matches_trigger(exceptional_rule, action, high_q))
    check("T4.11 Exceptional no match low quality", not _matches_trigger(exceptional_rule, action, low_q))

    # ── T5: Multi-Factor Analysis ──
    print("\n── T5: Multi-Factor Analysis ──")

    action5 = R7Action(
        role=RolePairing(actor="alice", role_lct="role:analyst"),
        request=Request(
            action="analyze",
            constraints={"deadline": "2026-01-01T00:00:00Z"},
            parameters={"completion_time_hours": 0.5},
        ),
        resource=Resource(required={"atp": 100}),
        reference=ReferenceContext(witnesses=[{"lct": "w1"}, {"lct": "w2"}, {"lct": "w3"}]),
    )
    result5 = Result(
        status=ActionStatus.SUCCESS,
        output={"quality": 0.97, "accuracy": 0.96, "completion_time_hours": 0.5},
        resource_consumed={"atp": 80},
        atp_cost=80,
    )
    factors = _analyze_factors(action5, result5, exceptional_rule)
    check("T5.1 Factors generated", len(factors) > 0)

    factor_names = [f.factor for f in factors]
    check("T5.2 Has exceed_quality", "exceed_quality" in factor_names)
    check("T5.3 Has deadline_met", "deadline_met" in factor_names)
    check("T5.4 Has early_completion", "early_completion" in factor_names)
    check("T5.5 Has high_accuracy", "high_accuracy" in factor_names)
    check("T5.6 Has well_witnessed", "well_witnessed" in factor_names)
    check("T5.7 Has successful_execution", "successful_execution" in factor_names)

    # Normalized weights sum to ~1
    total_w = sum(f.normalized_weight for f in factors)
    check("T5.8 Normalized weights sum ~1", abs(total_w - 1.0) < 0.01, f"got {total_w}")

    check("T5.9 Factor applies check", _factor_applies("deadline_met", factors))
    check("T5.10 Factor not applies", not _factor_applies("nonexistent_factor", factors))

    # ── T6: Reputation Computation ──
    print("\n── T6: Reputation Computation ──")

    action6 = R7Action(
        role=RolePairing(
            actor="lct:web4:entity:alice",
            role_lct="lct:web4:role:analyst:abc",
            t3_in_role={"talent": 0.85, "training": 0.90, "temperament": 0.88},
            v3_in_role={"veracity": 0.92, "validity": 0.88, "value": 0.85},
        ),
        request=Request(action="analyze_dataset"),
        resource=Resource(required={"atp": 100}),
    )
    result6 = Result(
        status=ActionStatus.SUCCESS,
        output={"quality": 0.8},
        resource_consumed={"atp": 90},
        atp_cost=90,
    )
    rep6 = compute_reputation_delta(action6, result6, rules)
    check("T6.1 Subject LCT set", rep6.subject_lct == "lct:web4:entity:alice")
    check("T6.2 Role LCT set", rep6.role_lct == "lct:web4:role:analyst:abc")
    check("T6.3 Has action_type", rep6.action_type == "analyze_dataset")
    check("T6.4 Has action_id", rep6.action_id.startswith("txn:"))
    check("T6.5 Has timestamp", len(rep6.timestamp) > 0)
    check("T6.6 Rule triggered", rep6.rule_triggered is not None)
    check("T6.7 Has reason", len(rep6.reason) > 0)
    check("T6.8 Net trust positive (success)", rep6.net_trust_change > 0)
    check("T6.9 Has contributing factors", len(rep6.contributing_factors) > 0)

    # Failure case
    result6f = Result(status=ActionStatus.FAILURE, error="oops")
    rep6f = compute_reputation_delta(action6, result6f, rules)
    check("T6.10 Failure: net trust negative", rep6f.net_trust_change < 0)
    check("T6.11 Failure: rule triggered", rep6f.rule_triggered == "failed_action")

    # Exceptional performance
    result6e = Result(
        status=ActionStatus.SUCCESS,
        output={"quality": 0.98},
        resource_consumed={"atp": 50},
        atp_cost=50,
    )
    rep6e = compute_reputation_delta(action6, result6e, rules)
    check("T6.12 Exceptional: higher trust change", rep6e.net_trust_change > rep6.net_trust_change)
    check("T6.13 Exceptional: has talent delta", "talent" in rep6e.t3_delta)
    check("T6.14 Exceptional: has value delta", "value" in rep6e.v3_delta)

    # No rules triggered
    empty_rules = []
    rep6n = compute_reputation_delta(action6, result6, empty_rules)
    check("T6.15 No rules: zero change", rep6n.net_trust_change == 0.0)

    # ── T7: R7 Executor Pipeline ──
    print("\n── T7: R7 Executor Pipeline ──")

    executor = R7Executor(reputation_rules=rules)

    action7 = R7Action(
        rules=RuleSet(permissions=["analyze_dataset"]),
        role=RolePairing(
            actor="lct:web4:entity:bob",
            role_lct="lct:web4:role:ml_engineer:def",
            t3_in_role={"talent": 0.85, "training": 0.88, "temperament": 0.90},
            v3_in_role={"veracity": 0.90, "validity": 0.92, "value": 0.88},
        ),
        request=Request(action="analyze_dataset", parameters={"quality": 0.85}),
        resource=Resource(required={"atp": 50}, available={"atp_balance": 500}),
    )
    result7, rep7 = executor.execute(action7)
    check("T7.1 Execute returns result", result7 is not None)
    check("T7.2 Execute returns reputation", rep7 is not None)
    check("T7.3 Result is success", result7.status == ActionStatus.SUCCESS)
    check("T7.4 Reputation has subject", rep7.subject_lct == "lct:web4:entity:bob")
    check("T7.5 Reputation role-contextualized", rep7.role_lct == "lct:web4:role:ml_engineer:def")
    check("T7.6 Ledger entry recorded", len(executor.ledger) == 1)
    check("T7.7 Reputation history recorded", len(executor.reputation_history) == 1)
    check("T7.8 Action count incremented", executor.action_count == 1)

    # Validation failure
    action7f = R7Action(
        rules=RuleSet(permissions=["read"]),
        role=RolePairing(actor="bob", role_lct="role:reader"),
        request=Request(action="delete"),  # Not in permissions
        resource=Resource(),
    )
    result7f, rep7f = executor.execute(action7f)
    check("T7.9 Validation failure: failed result", result7f.status == ActionStatus.FAILURE)
    check("T7.10 Validation failure: negative reputation", rep7f.net_trust_change < 0)

    # Insufficient resources
    action7r = R7Action(
        rules=RuleSet(permissions=["compute"]),
        role=RolePairing(actor="bob", role_lct="role:compute"),
        request=Request(action="compute"),
        resource=Resource(required={"atp": 9999}, available={"atp_balance": 100}),
    )
    result7r, rep7r = executor.execute(action7r)
    check("T7.11 Resource failure", result7r.status == ActionStatus.FAILURE)
    check("T7.12 Resource failure reason", "Insufficient ATP" in result7r.error)

    # ── T8: R7 Tensor Updates ──
    print("\n── T8: R7 Tensor Updates ──")

    executor8 = R7Executor(reputation_rules=rules)
    role8 = RolePairing(
        actor="lct:web4:entity:charlie",
        role_lct="lct:web4:role:dev:xyz",
        t3_in_role={"talent": 0.50, "training": 0.50, "temperament": 0.50},
        v3_in_role={"veracity": 0.50, "validity": 0.50, "value": 0.50},
    )
    action8 = R7Action(
        rules=RuleSet(permissions=["code"]),
        role=role8,
        request=Request(action="code", parameters={"quality": 0.8}),
        resource=Resource(required={"atp": 10}, available={"atp_balance": 100}),
    )
    _, rep8 = executor8.execute(action8)

    key8 = executor8._role_key("lct:web4:entity:charlie", "lct:web4:role:dev:xyz")
    check("T8.1 Tensor stored for role", key8 in executor8.role_t3)
    check("T8.2 T3 updated from default", any(
        executor8.role_t3[key8][d] != 0.50 for d in ["talent", "training", "temperament"]
        if d in rep8.t3_delta
    ))

    # Multiple actions accumulate
    action8b = R7Action(
        rules=RuleSet(permissions=["code"]),
        role=role8,
        request=Request(action="code", parameters={"quality": 0.85}),
        resource=Resource(required={"atp": 10}, available={"atp_balance": 100}),
    )
    _, rep8b = executor8.execute(action8b)
    check("T8.3 Second action recorded", executor8.action_count == 2)
    check("T8.4 Reputation history grows", len(executor8.reputation_history) == 2)

    # Reputation history query
    history = executor8.get_reputation_history("lct:web4:entity:charlie")
    check("T8.5 History query by entity", len(history) == 2)
    history_role = executor8.get_reputation_history("lct:web4:entity:charlie", "lct:web4:role:dev:xyz")
    check("T8.6 History query by role", len(history_role) == 2)
    history_other = executor8.get_reputation_history("lct:web4:entity:charlie", "other_role")
    check("T8.7 History query other role empty", len(history_other) == 0)

    # ── T9: R6→R7 Migration ──
    print("\n── T9: R6→R7 Migration ──")

    r7_exec = R7Executor(reputation_rules=rules)
    r6_exec = R6Executor(r7_exec)

    r6_result = r6_exec.execute_r6_action(
        rules=RuleSet(permissions=["query"]),
        role=RolePairing(actor="alice", role_lct="role:reader"),
        request=Request(action="query", parameters={"quality": 0.8}),
        reference=ReferenceContext(),
        resource=Resource(required={"atp": 5}, available={"atp_balance": 100}),
    )
    check("T9.1 R6 returns only Result", isinstance(r6_result, Result))
    check("T9.2 R6 result is success", r6_result.status == ActionStatus.SUCCESS)
    check("T9.3 R6 reputation logged silently", len(r6_exec.get_silent_reputation_log()) >= 1)
    check("T9.4 R7 executor also recorded", len(r7_exec.reputation_history) >= 1)

    # Migration wrapper
    migrator = R6ToR7Migrator()
    simple_result = Result(status=ActionStatus.SUCCESS, value_created=50.0)
    signals = migrator.extract_reputation_from_result(simple_result)
    check("T9.5 Extract signals success", signals.get("temperament", 0) > 0)
    check("T9.6 Extract signals value", signals.get("value", 0) > 0)

    fail_signals = migrator.extract_reputation_from_result(Result.failed("err"))
    check("T9.7 Extract signals failure negative", fail_signals.get("temperament", 0) < 0)

    # wrap_r6_result
    action9 = R7Action(
        role=RolePairing(actor="alice", role_lct="role:analyst"),
        request=Request(action="analyze"),
    )
    wrapped_result, wrapped_rep = migrator.wrap_r6_result(simple_result, action9, rules)
    check("T9.8 Wrap returns result", wrapped_result is not None)
    check("T9.9 Wrap returns reputation", wrapped_rep is not None)

    # ── T10: Witness Selection ──
    print("\n── T10: Witness Selection ──")

    ws = WitnessSelector()
    ws.register_law_oracle("lct:web4:oracle:data_science")
    ws.register_validator("analyst", "lct:web4:validator:fin_audit")
    ws.register_validator("*", "lct:web4:validator:general")

    action10 = R7Action(
        role=RolePairing(actor="alice", role_lct="lct:web4:role:analyst:abc"),
        request=Request(action="analyze"),
        reference=ReferenceContext(witnesses=[
            {"lct": "lct:web4:witness:peer1"},
            {"lct": "lct:web4:witness:peer2"},
        ]),
    )
    rep10 = ReputationDelta(action_id="txn:test123", timestamp="2026-02-22T00:00:00Z")

    witnesses = ws.select_witnesses(action10, rep10, required_count=3)
    check("T10.1 Witnesses selected", len(witnesses) == 3)
    check("T10.2 Law oracle first", witnesses[0].witness_type == "law_oracle")
    check("T10.3 Signatures generated", all(len(w.signature) > 0 for w in witnesses))
    check("T10.4 Timestamps set", all(len(w.timestamp) > 0 for w in witnesses))

    # Deduplicate witnesses
    ws2 = WitnessSelector()
    ws2.register_law_oracle("oracle1")
    ws2.register_law_oracle("oracle1")  # Duplicate
    witnesses2 = ws2.select_witnesses(action10, rep10, required_count=5)
    lcts = [w.lct for w in witnesses2]
    check("T10.5 No duplicate witnesses", len(lcts) == len(set(lcts)))

    # ── T11: Time-Weighted Aggregation ──
    print("\n── T11: Time-Weighted Aggregation ──")

    agg = ReputationAggregator(half_life_days=30.0)
    now = datetime.now(timezone.utc)

    deltas = [
        ReputationDelta(
            t3_delta={"training": TensorChange(0.02, 0.5, 0.52)},
            timestamp=(now - timedelta(days=1)).isoformat(),
        ),
        ReputationDelta(
            t3_delta={"training": TensorChange(0.01, 0.52, 0.53)},
            timestamp=(now - timedelta(days=10)).isoformat(),
        ),
        ReputationDelta(
            t3_delta={"training": TensorChange(-0.005, 0.53, 0.525)},
            timestamp=(now - timedelta(days=60)).isoformat(),
        ),
    ]

    current = agg.compute_current_reputation(deltas, "training", is_trust=True, base_value=0.5, now=now)
    check("T11.1 Aggregation positive overall", current > 0.5)
    check("T11.2 Recent deltas weighted more", current > 0.51)

    # Decay
    decay = agg.apply_decay(0.8, now - timedelta(days=60), now=now)
    check("T11.3 Decay after 60 days", decay < 0)
    check("T11.4 Decay magnitude", decay < -0.01)

    no_decay = agg.apply_decay(0.8, now - timedelta(days=15), now=now)
    check("T11.5 No decay within 30 days", no_decay == 0.0)

    long_decay = agg.apply_decay(0.8, now - timedelta(days=270), now=now)
    check("T11.6 Accelerated decay after 6 months", abs(long_decay) > abs(decay))

    # Summary
    summary_deltas = [
        ReputationDelta(
            net_trust_change=0.05,
            net_value_change=0.02,
            witnesses=[WitnessAttestation(lct="w1"), WitnessAttestation(lct="w2")],
        ),
        ReputationDelta(
            net_trust_change=-0.08,
            net_value_change=0.01,
            witnesses=[WitnessAttestation(lct="w1"), WitnessAttestation(lct="w3")],
        ),
    ]
    summary = agg.get_reputation_summary(summary_deltas)
    check("T11.7 Summary total actions", summary["total_actions"] == 2)
    check("T11.8 Summary net trust", abs(summary["net_trust_change"] - (-0.03)) < 0.001)
    check("T11.9 Summary unique witnesses", summary["witnesses"] == 3)
    check("T11.10 Summary violations", summary["violations"] == 1)

    empty_summary = agg.get_reputation_summary([])
    check("T11.11 Empty summary", empty_summary["total_actions"] == 0)

    # ── T12: Diminishing Returns & Gaming Prevention ──
    print("\n── T12: Diminishing Returns & Gaming Prevention ──")

    gp = GamingPrevention(window_hours=24)
    now12 = datetime.now(timezone.utc)

    # First action: full factor
    f1 = gp.get_diminishing_factor("alice", "query", now=now12)
    check("T12.1 First action full factor", f1 == 1.0)

    # Record repeated actions
    for i in range(5):
        gp.record_action("alice", "query", now12 - timedelta(minutes=i))

    f5 = gp.get_diminishing_factor("alice", "query", now=now12)
    check("T12.2 After 5 repeats: diminished", f5 < 0.5)
    check("T12.3 Diminishing floor", f5 >= 0.1)

    # Different action type: no diminishing
    f_other = gp.get_diminishing_factor("alice", "compute", now=now12)
    check("T12.4 Different action type full", f_other == 1.0)

    # Anomaly detection: rate
    gp2 = GamingPrevention(window_hours=24)
    for i in range(101):
        gp2.record_action("spammer", "query", now12 - timedelta(minutes=i))
    anomaly, reason = gp2.detect_anomaly("spammer", now=now12)
    check("T12.5 Rate anomaly detected", anomaly)
    check("T12.6 Rate anomaly reason", "Rate limit" in reason)

    # Anomaly detection: low diversity
    gp3 = GamingPrevention(window_hours=24)
    for i in range(15):
        gp3.record_action("gamer", "same_action", now12 - timedelta(minutes=i))
    anomaly3, reason3 = gp3.detect_anomaly("gamer", now=now12)
    check("T12.7 Low diversity anomaly", anomaly3)
    check("T12.8 Diversity reason", "Low diversity" in reason3)

    # No anomaly
    gp4 = GamingPrevention(window_hours=24)
    for i in range(5):
        gp4.record_action("legit", f"action_{i}", now12)
    anomaly4, reason4 = gp4.detect_anomaly("legit", now=now12)
    check("T12.9 No anomaly for legit", not anomaly4)

    # ── T13: R7Action Complete Structure ──
    print("\n── T13: R7Action Complete Structure ──")

    full_action = R7Action(
        rules=RuleSet(law_hash="sha256:abc", permissions=["analyze"]),
        role=RolePairing(
            actor="lct:web4:entity:alice",
            role_lct="lct:web4:role:analyst:abc",
            paired_at="2025-09-15T12:00:00Z",
            mrh_link="link:mrh:alice→analyst:xyz",
        ),
        request=Request(action="analyze", target="resource:data:q4", atp_stake=100),
        reference=ReferenceContext(precedents=[{"actionHash": "abc", "relevance": 0.9}]),
        resource=Resource(required={"atp": 100}, available={"atp_balance": 500}),
    )
    check("T13.1 Full R7Action rules", full_action.rules.law_hash == "sha256:abc")
    check("T13.2 Full R7Action role", full_action.role.mrh_link == "link:mrh:alice→analyst:xyz")
    check("T13.3 Full R7Action request", full_action.request.atp_stake == 100)
    check("T13.4 Full R7Action reference", len(full_action.reference.precedents) == 1)
    check("T13.5 Full R7Action resource", full_action.resource.required["atp"] == 100)
    check("T13.6 Initially no result", full_action.result is None)
    check("T13.7 Initially no reputation", full_action.reputation is None)

    # Execute full action
    exec13 = R7Executor(reputation_rules=rules)
    r13, rep13 = exec13.execute(full_action)
    check("T13.8 Full action result stored", full_action.result is not None)
    check("T13.9 Full action reputation stored", full_action.reputation is not None)
    check("T13.10 All 7 components present",
          all([full_action.rules, full_action.role, full_action.request,
               full_action.reference, full_action.resource,
               full_action.result, full_action.reputation]))

    # ── T14: Reputation Rule Modifiers ──
    print("\n── T14: Reputation Rule Modifiers ──")

    # Test that modifiers amplify deltas
    mod_rule = ReputationRule(
        rule_id="mod_test",
        trigger_conditions={"action_type": "*", "result_status": "success"},
        t3_impact={
            "training": DimensionImpact(0.01, [
                ReputationModifier("deadline_met", 2.0),
                ReputationModifier("high_accuracy", 1.5),
            ]),
        },
    )

    # Without modifiers
    factors_none = [ContributingFactor("something_else", 1.0)]
    delta_none = _compute_dimension_delta("training", [mod_rule], factors_none, is_trust=True)
    check("T14.1 Base delta without modifiers", abs(delta_none - 0.01) < 0.001)

    # With one modifier
    factors_one = [ContributingFactor("deadline_met", 1.0)]
    delta_one = _compute_dimension_delta("training", [mod_rule], factors_one, is_trust=True)
    check("T14.2 Delta with one modifier", abs(delta_one - 0.02) < 0.001)

    # With both modifiers
    factors_both = [ContributingFactor("deadline_met", 1.0), ContributingFactor("high_accuracy", 1.0)]
    delta_both = _compute_dimension_delta("training", [mod_rule], factors_both, is_trust=True)
    check("T14.3 Delta with both modifiers", abs(delta_both - 0.03) < 0.001)

    # Clamping
    extreme_rule = ReputationRule(
        rule_id="extreme",
        trigger_conditions={"action_type": "*", "result_status": "success"},
        t3_impact={"talent": DimensionImpact(5.0)},
    )
    delta_clamped = _compute_dimension_delta("talent", [extreme_rule], [], is_trust=True)
    check("T14.4 Delta clamped to 1.0", delta_clamped == 1.0)

    extreme_neg = ReputationRule(
        rule_id="extreme_neg",
        trigger_conditions={"action_type": "*", "result_status": "failure"},
        t3_impact={"talent": DimensionImpact(-5.0)},
    )
    delta_neg_clamped = _compute_dimension_delta("talent", [extreme_neg], [], is_trust=True)
    check("T14.5 Negative delta clamped to -1.0", delta_neg_clamped == -1.0)

    # ── T15: Reputation Role Isolation ──
    print("\n── T15: Reputation Role Isolation ──")

    exec15 = R7Executor(reputation_rules=rules)

    # Same entity, different roles
    role_analyst = RolePairing(
        actor="lct:web4:entity:alice",
        role_lct="lct:web4:role:analyst",
        t3_in_role={"talent": 0.9, "training": 0.9, "temperament": 0.9},
        v3_in_role={"veracity": 0.9, "validity": 0.9, "value": 0.9},
    )
    role_surgeon = RolePairing(
        actor="lct:web4:entity:alice",
        role_lct="lct:web4:role:surgeon",
        t3_in_role={"talent": 0.2, "training": 0.1, "temperament": 0.3},
        v3_in_role={"veracity": 0.2, "validity": 0.1, "value": 0.2},
    )

    _, rep_analyst = exec15.execute(R7Action(
        rules=RuleSet(permissions=["analyze"]),
        role=role_analyst,
        request=Request(action="analyze", parameters={"quality": 0.8}),
        resource=Resource(required={"atp": 10}, available={"atp_balance": 100}),
    ))
    _, rep_surgeon = exec15.execute(R7Action(
        rules=RuleSet(permissions=["operate"]),
        role=role_surgeon,
        request=Request(action="operate", parameters={"quality": 0.8}),
        resource=Resource(required={"atp": 10}, available={"atp_balance": 100}),
    ))

    check("T15.1 Analyst reputation on analyst role", rep_analyst.role_lct == "lct:web4:role:analyst")
    check("T15.2 Surgeon reputation on surgeon role", rep_surgeon.role_lct == "lct:web4:role:surgeon")
    check("T15.3 Different role contexts", rep_analyst.role_lct != rep_surgeon.role_lct)

    key_analyst = exec15._role_key("lct:web4:entity:alice", "lct:web4:role:analyst")
    key_surgeon = exec15._role_key("lct:web4:entity:alice", "lct:web4:role:surgeon")
    check("T15.4 Separate T3 storage per role", key_analyst in exec15.role_t3 and key_surgeon in exec15.role_t3)
    check("T15.5 Role-specific T3 different",
          exec15.role_t3[key_analyst] != exec15.role_t3[key_surgeon])

    # No global reputation
    history_all = exec15.get_reputation_history("lct:web4:entity:alice")
    history_analyst = exec15.get_reputation_history("lct:web4:entity:alice", "lct:web4:role:analyst")
    history_surgeon = exec15.get_reputation_history("lct:web4:entity:alice", "lct:web4:role:surgeon")
    check("T15.6 Total history = 2", len(history_all) == 2)
    check("T15.7 Analyst history = 1", len(history_analyst) == 1)
    check("T15.8 Surgeon history = 1", len(history_surgeon) == 1)

    # ── T16: Federation Reputation Oracle ──
    print("\n── T16: Federation Reputation Oracle ──")

    oracle = FederationReputationOracle()
    oracle.record("society_alpha", ReputationDelta(
        subject_lct="alice", net_trust_change=0.05, net_value_change=0.02,
        witnesses=[WitnessAttestation(lct="w1")],
    ))
    oracle.record("society_alpha", ReputationDelta(
        subject_lct="bob", net_trust_change=0.03, net_value_change=0.01,
        witnesses=[WitnessAttestation(lct="w2")],
    ))
    oracle.record("society_beta", ReputationDelta(
        subject_lct="alice", net_trust_change=0.02, net_value_change=0.01,
        witnesses=[WitnessAttestation(lct="w3")],
    ))

    summary_alpha = oracle.get_society_summary("society_alpha")
    check("T16.1 Society summary actions", summary_alpha["total_actions"] == 2)
    check("T16.2 Society net trust", abs(summary_alpha["net_trust_change"] - 0.08) < 0.001)
    check("T16.3 Society witnesses", summary_alpha["witnesses"] == 2)

    cross = oracle.get_cross_society_reputation("alice")
    check("T16.4 Cross-society has alpha", "society_alpha" in cross)
    check("T16.5 Cross-society has beta", "society_beta" in cross)
    check("T16.6 Cross-society alice in alpha", cross["society_alpha"]["total_actions"] == 1)

    empty_cross = oracle.get_cross_society_reputation("nobody")
    check("T16.7 Unknown entity empty", len(empty_cross) == 0)

    # ── T17: RDF Serialization ──
    print("\n── T17: RDF Serialization ──")

    serializer = ReputationRDFSerializer()
    rep17 = ReputationDelta(
        subject_lct="lct:web4:entity:alice",
        role_lct="lct:web4:role:analyst:abc",
        action_type="analyze",
        action_id="txn:abc123",
        rule_triggered="successful_action",
        t3_delta={"training": TensorChange(0.01, 0.9, 0.91)},
        v3_delta={"veracity": TensorChange(0.02, 0.85, 0.87)},
        witnesses=[WitnessAttestation(lct="w1")],
        net_trust_change=0.01,
        net_value_change=0.02,
    )
    triples = serializer.serialize(rep17)
    check("T17.1 Triples generated", len(triples) > 0)
    check("T17.2 Has type triple", any("ReputationDelta" in t for t in triples))
    check("T17.3 Has subject triple", any("subject" in t and "alice" in t for t in triples))
    check("T17.4 Has roleLCT triple", any("roleLCT" in t for t in triples))
    check("T17.5 Has T3 delta triple", any("t3Delta/training" in t for t in triples))
    check("T17.6 Has V3 delta triple", any("v3Delta/veracity" in t for t in triples))
    check("T17.7 Has witness triple", any("witnessedBy" in t for t in triples))
    check("T17.8 Has net trust triple", any("netTrustChange" in t for t in triples))
    check("T17.9 Has rule triggered", any("ruleTriggered" in t for t in triples))

    # ── T18: Constraint Validation ──
    print("\n── T18: Constraint Validation ──")

    exec18 = R7Executor(reputation_rules=rules)

    # ATP minimum constraint
    action18 = R7Action(
        rules=RuleSet(
            permissions=["query"],
            constraints=[{"type": "atp_minimum", "value": 50}],
        ),
        role=RolePairing(actor="alice", role_lct="role:querier"),
        request=Request(action="query", atp_stake=10),  # Below minimum
        resource=Resource(required={"atp": 5}, available={"atp_balance": 100}),
    )
    r18, rep18 = exec18.execute(action18)
    check("T18.1 ATP minimum rejected", r18.status == ActionStatus.FAILURE)
    check("T18.2 Rejection reason mentions stake", "below minimum" in r18.error)

    # Prohibition constraint
    action18b = R7Action(
        rules=RuleSet(prohibitions=["delete"]),
        role=RolePairing(actor="alice", role_lct="role:user"),
        request=Request(action="delete"),
        resource=Resource(),
    )
    r18b, _ = exec18.execute(action18b)
    check("T18.3 Prohibition enforced", r18b.status == ActionStatus.FAILURE)
    check("T18.4 Prohibition reason", "prohibited" in r18b.error)

    # Missing actor
    action18c = R7Action(
        role=RolePairing(role_lct="role:user"),  # No actor
        request=Request(action="test"),
    )
    r18c, _ = exec18.execute(action18c)
    check("T18.5 Missing actor rejected", r18c.status == ActionStatus.FAILURE)

    # Missing role
    action18d = R7Action(
        role=RolePairing(actor="alice"),  # No role_lct
        request=Request(action="test"),
    )
    r18d, _ = exec18.execute(action18d)
    check("T18.6 Missing role rejected", r18d.status == ActionStatus.FAILURE)

    # Missing action
    action18e = R7Action(
        role=RolePairing(actor="alice", role_lct="role:user"),
        request=Request(),  # No action
    )
    r18e, _ = exec18.execute(action18e)
    check("T18.7 Missing action rejected", r18e.status == ActionStatus.FAILURE)

    # ── T19: SAL Integration Patterns ──
    print("\n── T19: SAL Integration Patterns ──")

    # Society-specific rules
    sal_rules = [
        ReputationRule(
            rule_id="sal_law_compliance",
            trigger_conditions={"action_type": "*", "result_status": "success"},
            t3_impact={"temperament": DimensionImpact(0.008)},
            v3_impact={"validity": DimensionImpact(0.005)},
            law_oracle="lct:web4:oracle:society_alpha",
        ),
        ReputationRule(
            rule_id="sal_violation",
            trigger_conditions={"action_type": "violate", "result_status": "failure"},
            t3_impact={"temperament": DimensionImpact(-0.05)},
            v3_impact={"veracity": DimensionImpact(-0.10)},
            law_oracle="lct:web4:oracle:society_alpha",
        ),
    ]

    exec19 = R7Executor(reputation_rules=sal_rules)
    action19 = R7Action(
        rules=RuleSet(law_hash="sha256:law1", society="society_alpha", permissions=["trade"]),
        role=RolePairing(
            actor="lct:web4:entity:trader",
            role_lct="lct:web4:role:trader:abc",
            t3_in_role={"talent": 0.7, "training": 0.7, "temperament": 0.7},
            v3_in_role={"veracity": 0.7, "validity": 0.7, "value": 0.7},
        ),
        request=Request(action="trade", parameters={"quality": 0.8}),
        resource=Resource(required={"atp": 20}, available={"atp_balance": 200}),
    )
    r19, rep19 = exec19.execute(action19)
    check("T19.1 SAL action success", r19.status == ActionStatus.SUCCESS)
    check("T19.2 SAL rule triggered", rep19.rule_triggered == "sal_law_compliance")
    check("T19.3 SAL temperament increase", rep19.net_trust_change > 0)

    # ── T20: Reputation History Integrity ──
    print("\n── T20: Reputation History Integrity ──")

    exec20 = R7Executor(reputation_rules=rules)
    actions_20 = []
    for i in range(10):
        a = R7Action(
            rules=RuleSet(permissions=["compute"]),
            role=RolePairing(
                actor="lct:web4:entity:worker",
                role_lct="lct:web4:role:compute:main",
                t3_in_role={"talent": 0.5, "training": 0.5, "temperament": 0.5},
                v3_in_role={"veracity": 0.5, "validity": 0.5, "value": 0.5},
            ),
            request=Request(action="compute", parameters={"quality": 0.8}),
            resource=Resource(required={"atp": 5}, available={"atp_balance": 1000}),
        )
        exec20.execute(a)
        actions_20.append(a)

    check("T20.1 10 actions recorded", exec20.action_count == 10)
    check("T20.2 10 ledger entries", len(exec20.ledger) == 10)
    check("T20.3 10 reputation entries", len(exec20.reputation_history) == 10)

    # All have unique action IDs
    action_ids = [r.action_id for r in exec20.reputation_history]
    check("T20.4 Unique action IDs", len(set(action_ids)) == 10)

    # All have timestamps
    check("T20.5 All have timestamps", all(r.timestamp for r in exec20.reputation_history))

    # Ledger entries match reputation
    for entry in exec20.ledger:
        check(f"T20.6 Ledger has reputation data", "reputation" in entry)

    # ── T21: R7 vs R6 Comparison ──
    print("\n── T21: R7 vs R6 Comparison ──")

    # R7 gives both result and reputation
    exec21 = R7Executor(reputation_rules=rules)
    action21 = R7Action(
        rules=RuleSet(permissions=["query"]),
        role=RolePairing(actor="alice", role_lct="role:user"),
        request=Request(action="query", parameters={"quality": 0.8}),
        resource=Resource(required={"atp": 5}, available={"atp_balance": 100}),
    )
    r21, rep21 = exec21.execute(action21)

    # R6 same action, only result
    r6_exec21 = R6Executor(R7Executor(reputation_rules=rules))
    r6_result21 = r6_exec21.execute_r6_action(
        rules=action21.rules,
        role=RolePairing(actor="alice", role_lct="role:user"),
        request=action21.request,
        reference=action21.reference,
        resource=action21.resource,
    )

    check("T21.1 R7 returns tuple", isinstance(r21, Result) and isinstance(rep21, ReputationDelta))
    check("T21.2 R6 returns only result", isinstance(r6_result21, Result))
    check("T21.3 Both succeed", r21.status == r6_result21.status == ActionStatus.SUCCESS)
    check("T21.4 R7 has explicit reputation", rep21.net_trust_change != 0 or rep21.reason != "")
    check("T21.5 R6 reputation logged silently", len(r6_exec21.get_silent_reputation_log()) > 0)

    # The key difference: R7 makes trust visible
    check("T21.6 R7 trust is observable", rep21.t3_delta is not None)
    check("T21.7 R7 trust is attributable", rep21.action_id.startswith("txn:"))
    check("T21.8 R7 trust is role-contextualized", rep21.role_lct == "role:user")

    # ── T22: Edge Cases ──
    print("\n── T22: Edge Cases ──")

    # Zero-delta reputation (no rules match)
    exec22 = R7Executor(reputation_rules=[])
    action22 = R7Action(
        rules=RuleSet(permissions=["*"]),
        role=RolePairing(actor="alice", role_lct="role:user"),
        request=Request(action="noop"),
        resource=Resource(required={"atp": 0}, available={"atp_balance": 100}),
    )
    r22, rep22 = exec22.execute(action22)
    check("T22.1 Zero rules: success", r22.status == ActionStatus.SUCCESS)
    check("T22.2 Zero rules: zero reputation", rep22.net_trust_change == 0.0)
    check("T22.3 Zero rules: zero value", rep22.net_value_change == 0.0)

    # Boundary tensor values (near 0 and 1)
    exec22b = R7Executor(reputation_rules=rules)
    role_max = RolePairing(
        actor="alice", role_lct="role:max",
        t3_in_role={"talent": 0.99, "training": 0.99, "temperament": 0.99},
        v3_in_role={"veracity": 0.99, "validity": 0.99, "value": 0.99},
    )
    action22b = R7Action(
        rules=RuleSet(permissions=["*"]),
        role=role_max,
        request=Request(action="test", parameters={"quality": 0.99}),
        resource=Resource(required={"atp": 10}, available={"atp_balance": 100}),
    )
    _, rep22b = exec22b.execute(action22b)
    # All tensor values should be clamped to [0, 1]
    for dim, tc in rep22b.t3_delta.items():
        check(f"T22.4 T3 {dim} clamped ≤ 1.0", tc.to_value <= 1.0)
    for dim, tc in rep22b.v3_delta.items():
        check(f"T22.5 V3 {dim} clamped ≤ 1.0", tc.to_value <= 1.0)

    # Wildcard permissions
    action22c = R7Action(
        rules=RuleSet(permissions=["admin:*"]),
        role=RolePairing(actor="admin", role_lct="role:admin"),
        request=Request(action="anything"),
        resource=Resource(required={"atp": 0}, available={"atp_balance": 100}),
    )
    v22c, _ = exec22.validate(action22c)
    check("T22.6 Wildcard permissions pass", v22c)

    # ── T23: Aggregation Edge Cases ──
    print("\n── T23: Aggregation Edge Cases ──")

    agg23 = ReputationAggregator()

    # No deltas
    current23 = agg23.compute_current_reputation([], "training", base_value=0.5)
    check("T23.1 No deltas returns base", current23 == 0.5)

    # Single delta
    single = [ReputationDelta(
        t3_delta={"training": TensorChange(0.1, 0.5, 0.6)},
        timestamp=datetime.now(timezone.utc).isoformat(),
    )]
    current23b = agg23.compute_current_reputation(single, "training", base_value=0.5)
    check("T23.2 Single positive delta", current23b > 0.5)

    # Large negative
    large_neg = [ReputationDelta(
        t3_delta={"training": TensorChange(-10.0, 0.5, -9.5)},
        timestamp=datetime.now(timezone.utc).isoformat(),
    )]
    current23c = agg23.compute_current_reputation(large_neg, "training", base_value=0.5)
    check("T23.3 Large negative clamped to 0", current23c == 0.0)

    # ── Summary ──
    print(f"\n{'='*60}")
    print(f"R6→R7 Evolution: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  {failed} FAILED")
    print(f"{'='*60}")
    return passed, total


if __name__ == "__main__":
    run_tests()
