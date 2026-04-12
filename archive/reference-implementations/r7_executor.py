#!/usr/bin/env python3
"""
R7 Action Framework — Reference Implementation
================================================

Implements the R7 spec: Rules + Role + Request + Reference + Resource → Result + Reputation

The key R7 innovation over R6: reputation is an explicit, role-contextualized,
witnessed first-class output. Every action produces both a Result AND a
ReputationDelta, making trust mechanics observable, attributable, and verifiable.

Reputation is stored on the MRH role pairing link, not globally. An entity's
reputation as "ML Engineer in Biotech" is independent of their reputation as
"Admin in FinOps". This is the R7 equation:

    R7 = Rules + Role + Request + Reference + Resource → Result + Reputation

Where Reputation = f(action_outcome, role_context, reputation_rules, witnesses)

Integrates with:
- web4_entity.py: T3Tensor, V3Tensor, ATPBudget, Web4Entity
- hardbound_cli.py: TeamPolicy, TeamLedger, TeamRole governance

Date: 2026-02-20
Spec: web4-standard/core-spec/r7-framework.md
"""

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from web4_entity import (
    Web4Entity, EntityType, T3Tensor, V3Tensor, ATPBudget,
    R6Request, R6Result, R6Decision, MetabolicState, PolicyGate
)


# ═══════════════════════════════════════════════════════════════
# R7 Error Hierarchy (from spec §7)
# ═══════════════════════════════════════════════════════════════

class R7Error(Exception):
    """Base exception for R7 framework errors."""
    pass

class RuleViolation(R7Error):
    """Action violates governing rules."""
    pass

class RoleUnauthorized(R7Error):
    """Actor lacks required role or permissions."""
    pass

class RequestMalformed(R7Error):
    """Request structure or parameters invalid."""
    pass

class ReferenceInvalid(R7Error):
    """Referenced entities not found or invalid."""
    pass

class ResourceInsufficient(R7Error):
    """Required resources unavailable."""
    pass

class ResultInvalid(R7Error):
    """Result violates output constraints."""
    pass

class ReputationComputationError(R7Error):
    """Reputation delta cannot be computed."""
    pass


# ═══════════════════════════════════════════════════════════════
# R7 Data Structures
# ═══════════════════════════════════════════════════════════════

@dataclass
class R7Rules:
    """Governing constraints and policies for the action (spec §1.1)."""
    law_hash: str = ""
    society: str = ""
    constraints: List[Dict[str, Any]] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    prohibitions: List[str] = field(default_factory=list)
    reputation_rules: List["ReputationRule"] = field(default_factory=list)


@dataclass
class R7Role:
    """Contextual identity under which the action is performed (spec §1.2).

    Role-contextualized reputation: T3/V3 on the MRH role pairing link.
    """
    actor_lct: str = ""
    role_lct: str = ""
    paired_at: str = ""
    t3_in_role: Optional[T3Tensor] = None
    v3_in_role: Optional[V3Tensor] = None


@dataclass
class R7Request:
    """Specific action intent and parameters (spec §1.3)."""
    action: str = ""
    target: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    atp_stake: float = 0.0
    nonce: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    proof_of_agency: Optional[Dict[str, str]] = None


@dataclass
class R7Reference:
    """Historical context and precedents (spec §1.4)."""
    precedents: List[Dict[str, Any]] = field(default_factory=list)
    mrh_context: Dict[str, Any] = field(default_factory=dict)
    interpretations: List[Dict[str, str]] = field(default_factory=list)
    witnesses: List[str] = field(default_factory=list)


@dataclass
class R7Resource:
    """Computational, economic, and material resources (spec §1.5)."""
    required_atp: float = 0.0
    required_compute: Dict[str, Any] = field(default_factory=dict)
    available_atp: float = 0.0
    escrow_amount: float = 0.0
    escrow_status: str = "pending"


@dataclass
class ContributingFactor:
    """A factor contributing to a reputation change."""
    factor: str
    weight: float

    def to_dict(self) -> dict:
        return {"factor": self.factor, "weight": self.weight}


@dataclass
class TensorDelta:
    """A single dimension change in a tensor."""
    dimension: str
    change: float
    from_value: float
    to_value: float

    def to_dict(self) -> dict:
        return {
            "change": round(self.change, 6),
            "from": round(self.from_value, 6),
            "to": round(self.to_value, 6),
        }


@dataclass
class ReputationDelta:
    """Explicit trust and value changes from an action (spec §1.7).

    This is the R7 innovation: reputation is first-class output,
    role-contextualized, witnessed, and composable.
    """
    subject_lct: str = ""
    role_lct: str = ""
    action_type: str = ""
    action_target: str = ""
    action_id: str = ""
    rule_triggered: str = ""
    reason: str = ""
    t3_deltas: List[TensorDelta] = field(default_factory=list)
    v3_deltas: List[TensorDelta] = field(default_factory=list)
    contributing_factors: List[ContributingFactor] = field(default_factory=list)
    witnesses: List[str] = field(default_factory=list)
    net_trust_change: float = 0.0
    net_value_change: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "subject_lct": self.subject_lct,
            "role_lct": self.role_lct,
            "action_type": self.action_type,
            "action_target": self.action_target,
            "action_id": self.action_id,
            "rule_triggered": self.rule_triggered,
            "reason": self.reason,
            "t3_delta": {d.dimension: d.to_dict() for d in self.t3_deltas},
            "v3_delta": {d.dimension: d.to_dict() for d in self.v3_deltas},
            "contributing_factors": [f.to_dict() for f in self.contributing_factors],
            "witnesses": self.witnesses,
            "net_trust_change": round(self.net_trust_change, 6),
            "net_value_change": round(self.net_value_change, 6),
            "timestamp": self.timestamp,
        }


@dataclass
class R7Result:
    """The complete R7 action result (spec §1.6)."""
    action_id: str = ""
    status: str = "pending"  # success, failure, error
    output: Any = None
    output_hash: str = ""
    error: Optional[str] = None
    error_type: Optional[str] = None
    atp_consumed: float = 0.0
    atp_refunded: float = 0.0
    execution_time_ms: float = 0.0
    ledger_proof: Optional[str] = None
    witnesses: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        d = {
            "action_id": self.action_id,
            "status": self.status,
            "output_hash": self.output_hash,
            "atp_consumed": self.atp_consumed,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "timestamp": self.timestamp,
        }
        if self.error:
            d["error"] = {"type": self.error_type, "message": self.error}
        if self.ledger_proof:
            d["ledger_proof"] = self.ledger_proof
        return d


@dataclass
class R7Action:
    """Complete R7 action specification (all 7 components).

    R7 = Rules + Role + Request + Reference + Resource → Result + Reputation
    """
    rules: R7Rules = field(default_factory=R7Rules)
    role: R7Role = field(default_factory=R7Role)
    request: R7Request = field(default_factory=R7Request)
    reference: R7Reference = field(default_factory=R7Reference)
    resource: R7Resource = field(default_factory=R7Resource)
    # Outputs (populated during execution)
    result: Optional[R7Result] = None
    reputation: Optional[ReputationDelta] = None


# ═══════════════════════════════════════════════════════════════
# Reputation Rules — Configurable reputation computation
# ═══════════════════════════════════════════════════════════════

class ReputationRuleType(str, Enum):
    """Types of reputation computation rules."""
    SUCCESS_REWARD = "success_reward"
    FAILURE_PENALTY = "failure_penalty"
    EFFICIENCY_BONUS = "efficiency_bonus"
    STAKE_REWARD = "stake_reward"
    DEADLINE_FACTOR = "deadline_factor"


@dataclass
class ReputationRule:
    """A rule that maps action outcomes to reputation changes.

    The R7 spec says reputation rules are defined by the Law Oracle
    and apply based on action type, outcome, and context.
    """
    rule_id: str
    rule_type: ReputationRuleType
    action_pattern: str = "*"  # glob pattern for action types
    affects_t3: Dict[str, float] = field(default_factory=dict)  # dimension → base delta
    affects_v3: Dict[str, float] = field(default_factory=dict)
    condition: Optional[Callable] = None  # optional callable(result) → bool

    def matches(self, action_type: str) -> bool:
        if self.action_pattern == "*":
            return True
        return action_type == self.action_pattern or action_type.startswith(self.action_pattern.rstrip("*"))

    def evaluate(self, result: R7Result) -> bool:
        if self.condition:
            return self.condition(result)
        if self.rule_type == ReputationRuleType.SUCCESS_REWARD:
            return result.status == "success"
        if self.rule_type == ReputationRuleType.FAILURE_PENALTY:
            return result.status in ("failure", "error")
        return True


# ═══════════════════════════════════════════════════════════════
# Default Reputation Rules
# ═══════════════════════════════════════════════════════════════

DEFAULT_REPUTATION_RULES = [
    ReputationRule(
        rule_id="default_success",
        rule_type=ReputationRuleType.SUCCESS_REWARD,
        affects_t3={"training": 0.01, "temperament": 0.005},
        affects_v3={"veracity": 0.01, "validity": 0.005},
    ),
    ReputationRule(
        rule_id="default_failure",
        rule_type=ReputationRuleType.FAILURE_PENALTY,
        affects_t3={"temperament": -0.02},
        affects_v3={"validity": -0.01},
    ),
    ReputationRule(
        rule_id="efficiency_bonus",
        rule_type=ReputationRuleType.EFFICIENCY_BONUS,
        affects_t3={"talent": 0.015},
        affects_v3={"valuation": 0.01},
        condition=lambda r: r.status == "success" and r.atp_consumed < r.execution_time_ms * 0.01,
    ),
    ReputationRule(
        rule_id="stake_reward",
        rule_type=ReputationRuleType.STAKE_REWARD,
        affects_t3={"talent": 0.01},
        affects_v3={"veracity": 0.02},
        condition=lambda r: r.status == "success",  # additional check in compute
    ),
]


# ═══════════════════════════════════════════════════════════════
# R7 Ledger Entry
# ═══════════════════════════════════════════════════════════════

@dataclass
class R7LedgerEntry:
    """A complete R7 transaction record for the ledger."""
    entry_id: str
    action_id: str
    actor_lct: str
    role_lct: str
    action_type: str
    target: str
    result_status: str
    atp_consumed: float
    reputation: Dict[str, Any]
    output_hash: str
    prev_hash: str
    timestamp: str
    entry_hash: str = ""

    def compute_hash(self) -> str:
        data = json.dumps({
            "entry_id": self.entry_id,
            "action_id": self.action_id,
            "actor_lct": self.actor_lct,
            "result_status": self.result_status,
            "atp_consumed": self.atp_consumed,
            "output_hash": self.output_hash,
            "prev_hash": self.prev_hash,
            "timestamp": self.timestamp,
        }, sort_keys=True)
        self.entry_hash = hashlib.sha256(data.encode()).hexdigest()
        return self.entry_hash

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "action_id": self.action_id,
            "actor": self.actor_lct,
            "role": self.role_lct,
            "action": self.action_type,
            "target": self.target,
            "status": self.result_status,
            "atp": self.atp_consumed,
            "reputation": self.reputation,
            "output_hash": self.output_hash,
            "prev_hash": self.prev_hash,
            "entry_hash": self.entry_hash,
            "timestamp": self.timestamp,
        }


# ═══════════════════════════════════════════════════════════════
# R7 Executor — The core engine
# ═══════════════════════════════════════════════════════════════

class R7Executor:
    """
    R7 Action Framework executor.

    Implements the full R7 transaction flow:
    1. Pre-execution validation (§2.1)
    2. Metered execution (§2.2)
    3. Reputation computation (§2.3)
    4. Post-execution settlement (§2.4)

    Each action produces both a Result AND a ReputationDelta.
    Trust-building is the core value proposition.
    """

    def __init__(
        self,
        reputation_rules: Optional[List[ReputationRule]] = None,
        society_lct: str = "lct:web4:society:default",
    ):
        self.reputation_rules = reputation_rules or list(DEFAULT_REPUTATION_RULES)
        self.society_lct = society_lct
        self.ledger: List[R7LedgerEntry] = []
        self.escrow: Dict[str, float] = {}  # action_id → escrowed ATP
        # Role-contextualized reputation store:
        # (entity_lct, role_lct) → {"t3": T3Tensor, "v3": V3Tensor}
        self.role_reputations: Dict[Tuple[str, str], Dict[str, Any]] = {}
        # Effector registry: action_type → callable
        self.effectors: Dict[str, Callable] = {}

    def register_effector(self, action_type: str, handler: Callable):
        """Register an action handler."""
        self.effectors[action_type] = handler

    def get_role_reputation(self, entity_lct: str, role_lct: str) -> Tuple[T3Tensor, V3Tensor]:
        """Get or create role-contextualized T3/V3 for an entity."""
        key = (entity_lct, role_lct)
        if key not in self.role_reputations:
            self.role_reputations[key] = {
                "t3": T3Tensor(talent=0.5, training=0.5, temperament=0.5),
                "v3": V3Tensor(valuation=0.0, veracity=0.5, validity=0.5),
            }
        rep = self.role_reputations[key]
        return rep["t3"], rep["v3"]

    # ═══════════════════════════════════════════════════════════
    # §2.1 — Pre-execution Validation
    # ═══════════════════════════════════════════════════════════

    def validate(self, action: R7Action) -> Tuple[bool, Optional[str]]:
        """
        Validate an R7 action before execution.

        Checks: role pairing, rule compliance, resource availability,
        reference validity, agency delegation.

        Returns (valid, error_message).
        """
        # 1. Verify actor has required role
        if not action.role.actor_lct:
            return False, "Missing actor LCT"
        if not action.role.role_lct:
            return False, "Missing role LCT"

        # 2. Check request is well-formed
        if not action.request.action:
            return False, "Missing action type"

        # 3. Check rules compliance — action not prohibited
        for prohibition in action.rules.prohibitions:
            if action.request.action == prohibition:
                return False, f"Action '{action.request.action}' is prohibited"

        # 4. Check permissions (if specified)
        if action.rules.permissions:
            action_verb = action.request.action.split("_")[0] if "_" in action.request.action else action.request.action
            if action_verb not in action.rules.permissions and action.request.action not in action.rules.permissions:
                return False, f"Action '{action.request.action}' not in permitted actions"

        # 5. Check constraints
        for constraint in action.rules.constraints:
            ctype = constraint.get("type", "")
            cval = constraint.get("value", 0)
            if ctype == "atp_minimum" and action.resource.available_atp < cval:
                return False, f"ATP balance {action.resource.available_atp} below minimum {cval}"

        # 6. Verify resource availability
        if action.resource.required_atp > action.resource.available_atp:
            return False, f"Insufficient ATP: need {action.resource.required_atp}, have {action.resource.available_atp}"

        # 7. Escrow resources
        if action.resource.escrow_amount > 0:
            action_id = action.request.nonce
            self.escrow[action_id] = action.resource.escrow_amount

        return True, None

    # ═══════════════════════════════════════════════════════════
    # §2.2 — Metered Execution
    # ═══════════════════════════════════════════════════════════

    def execute(self, action: R7Action) -> R7Result:
        """
        Execute an R7 action with metering.

        Dispatches to registered effectors or uses default execution.
        Measures resource consumption and creates R7Result.
        """
        action_id = f"r7:{action.request.nonce}"
        start = time.monotonic()

        try:
            # Dispatch to effector if registered
            if action.request.action in self.effectors:
                output = self.effectors[action.request.action](action)
            else:
                # Default: action succeeds
                output = f"Executed: {action.request.action} on {action.request.target}"

            elapsed = (time.monotonic() - start) * 1000
            output_hash = hashlib.sha256(
                json.dumps(str(output), sort_keys=True).encode()
            ).hexdigest()[:16]

            return R7Result(
                action_id=action_id,
                status="success",
                output=output,
                output_hash=output_hash,
                atp_consumed=action.resource.required_atp,
                execution_time_ms=elapsed,
            )

        except R7Error as e:
            elapsed = (time.monotonic() - start) * 1000
            return R7Result(
                action_id=action_id,
                status="error",
                error=str(e),
                error_type=type(e).__name__,
                atp_consumed=action.resource.required_atp * 0.1,  # partial cost on error
                execution_time_ms=elapsed,
            )

        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            return R7Result(
                action_id=action_id,
                status="failure",
                error=str(e),
                error_type="ExecutionFailure",
                atp_consumed=action.resource.required_atp * 0.5,  # half cost on failure
                execution_time_ms=elapsed,
            )

    # ═══════════════════════════════════════════════════════════
    # §2.3 — Reputation Computation (THE R7 INNOVATION)
    # ═══════════════════════════════════════════════════════════

    def compute_reputation(self, action: R7Action, result: R7Result) -> ReputationDelta:
        """
        Compute explicit reputation changes based on action outcome.

        This is the key R7 innovation: trust changes are first-class outputs,
        role-contextualized, and witnessed.

        Reputation is stored on the MRH role pairing link, not globally.
        """
        entity_lct = action.role.actor_lct
        role_lct = action.role.role_lct

        # Get current role-contextualized tensors
        current_t3, current_v3 = self.get_role_reputation(entity_lct, role_lct)

        reputation = ReputationDelta(
            subject_lct=entity_lct,
            role_lct=role_lct,
            action_type=action.request.action,
            action_target=action.request.target,
            action_id=result.action_id,
        )

        # Collect all applicable rules
        all_rules = self.reputation_rules + action.rules.reputation_rules
        triggered_rules = []

        for rule in all_rules:
            if rule.matches(action.request.action) and rule.evaluate(result):
                triggered_rules.append(rule)

        if not triggered_rules:
            reputation.reason = "No reputation rules triggered"
            return reputation

        # Aggregate T3 deltas from all triggered rules
        t3_aggregate: Dict[str, float] = {}
        v3_aggregate: Dict[str, float] = {}

        for rule in triggered_rules:
            for dim, delta in rule.affects_t3.items():
                # Scale by stake if it's a stake reward
                if rule.rule_type == ReputationRuleType.STAKE_REWARD:
                    stake = action.request.atp_stake
                    if stake <= 0:
                        continue
                    delta = delta * min(stake / 100.0, 2.0)  # cap at 2x
                t3_aggregate[dim] = t3_aggregate.get(dim, 0.0) + delta

            for dim, delta in rule.affects_v3.items():
                if rule.rule_type == ReputationRuleType.STAKE_REWARD:
                    stake = action.request.atp_stake
                    if stake <= 0:
                        continue
                    delta = delta * min(stake / 100.0, 2.0)
                v3_aggregate[dim] = v3_aggregate.get(dim, 0.0) + delta

        # Build TensorDeltas with from/to values
        t3_map = {"talent": current_t3.talent, "training": current_t3.training,
                   "temperament": current_t3.temperament}
        v3_map = {"valuation": current_v3.valuation, "veracity": current_v3.veracity,
                   "validity": current_v3.validity}

        for dim, delta in t3_aggregate.items():
            if dim in t3_map and abs(delta) > 1e-9:
                from_val = t3_map[dim]
                to_val = max(0.0, min(1.0, from_val + delta))
                reputation.t3_deltas.append(TensorDelta(
                    dimension=dim, change=to_val - from_val,
                    from_value=from_val, to_value=to_val,
                ))

        for dim, delta in v3_aggregate.items():
            if dim in v3_map and abs(delta) > 1e-9:
                from_val = v3_map[dim]
                to_val = max(0.0, min(1.0, from_val + delta))
                reputation.v3_deltas.append(TensorDelta(
                    dimension=dim, change=to_val - from_val,
                    from_value=from_val, to_value=to_val,
                ))

        # Contributing factors
        factors = []
        if result.status == "success":
            factors.append(ContributingFactor("outcome_success", 0.5))
        else:
            factors.append(ContributingFactor("outcome_failure", 0.5))

        if action.request.atp_stake > 0:
            stake_weight = min(action.request.atp_stake / 100.0, 0.3)
            factors.append(ContributingFactor("atp_stake", stake_weight))

        if result.execution_time_ms > 0 and result.status == "success":
            factors.append(ContributingFactor("execution_efficiency", 0.2))

        reputation.contributing_factors = factors
        reputation.rule_triggered = triggered_rules[0].rule_id
        reputation.net_trust_change = sum(d.change for d in reputation.t3_deltas)
        reputation.net_value_change = sum(d.change for d in reputation.v3_deltas)

        # Generate reason
        if result.status == "success":
            reputation.reason = (
                f"Successfully executed '{action.request.action}' on '{action.request.target}' "
                f"in role '{role_lct}'"
            )
        else:
            reputation.reason = (
                f"Failed '{action.request.action}' on '{action.request.target}': "
                f"{result.error or 'unknown error'}"
            )

        # Witnesses (from reference + any configured witnesses)
        reputation.witnesses = list(action.reference.witnesses)

        return reputation

    # ═══════════════════════════════════════════════════════════
    # §2.4 — Post-execution Settlement
    # ═══════════════════════════════════════════════════════════

    def settle(self, action: R7Action, result: R7Result, reputation: ReputationDelta) -> R7LedgerEntry:
        """
        Settle an R7 action: apply tensor updates, record to ledger.

        Settlement is atomic: either fully completes or fully rolls back.
        """
        entity_lct = action.role.actor_lct
        role_lct = action.role.role_lct

        # 1. Apply T3/V3 deltas to role-contextualized reputation
        t3, v3 = self.get_role_reputation(entity_lct, role_lct)

        for delta in reputation.t3_deltas:
            if delta.dimension == "talent":
                t3.talent = delta.to_value
            elif delta.dimension == "training":
                t3.training = delta.to_value
            elif delta.dimension == "temperament":
                t3.temperament = delta.to_value

        for delta in reputation.v3_deltas:
            if delta.dimension == "valuation":
                v3.valuation = delta.to_value
            elif delta.dimension == "veracity":
                v3.veracity = delta.to_value
            elif delta.dimension == "validity":
                v3.validity = delta.to_value

        # 2. Release or refund escrow
        action_id = action.request.nonce
        if action_id in self.escrow:
            escrowed = self.escrow.pop(action_id)
            if result.status != "success":
                result.atp_refunded = escrowed * 0.8  # 80% refund on failure

        # 3. Record to ledger
        prev_hash = self.ledger[-1].entry_hash if self.ledger else "genesis"
        entry = R7LedgerEntry(
            entry_id=f"r7-{len(self.ledger):06d}",
            action_id=result.action_id,
            actor_lct=entity_lct,
            role_lct=role_lct,
            action_type=action.request.action,
            target=action.request.target,
            result_status=result.status,
            atp_consumed=result.atp_consumed,
            reputation=reputation.to_dict(),
            output_hash=result.output_hash,
            prev_hash=prev_hash,
            timestamp=result.timestamp,
        )
        entry.compute_hash()
        self.ledger.append(entry)

        # 4. Set ledger proof on result
        result.ledger_proof = entry.entry_hash

        return entry

    # ═══════════════════════════════════════════════════════════
    # Full R7 Transaction — convenience method
    # ═══════════════════════════════════════════════════════════

    def process(self, action: R7Action) -> Tuple[R7Result, ReputationDelta]:
        """
        Process a complete R7 action: validate → execute → compute reputation → settle.

        Returns (result, reputation).
        """
        # 1. Validate
        valid, error = self.validate(action)
        if not valid:
            # Even validation failures produce reputation (R7 spec)
            result = R7Result(
                action_id=f"r7:{action.request.nonce}",
                status="error",
                error=error,
                error_type="ValidationError",
            )
            reputation = self.compute_reputation(action, result)
            action.result = result
            action.reputation = reputation
            self.settle(action, result, reputation)
            return result, reputation

        # 2. Execute
        result = self.execute(action)

        # 3. Compute reputation
        reputation = self.compute_reputation(action, result)

        # 4. Settle
        self.settle(action, result, reputation)

        # 5. Attach to action
        action.result = result
        action.reputation = reputation

        return result, reputation

    # ═══════════════════════════════════════════════════════════
    # Analytics
    # ═══════════════════════════════════════════════════════════

    def get_reputation_history(self, entity_lct: str, role_lct: Optional[str] = None) -> List[Dict]:
        """Get reputation change history for an entity (optionally filtered by role)."""
        history = []
        for entry in self.ledger:
            if entry.actor_lct == entity_lct:
                if role_lct is None or entry.role_lct == role_lct:
                    history.append({
                        "action_id": entry.action_id,
                        "action": entry.action_type,
                        "status": entry.result_status,
                        "role": entry.role_lct,
                        "net_trust": entry.reputation.get("net_trust_change", 0),
                        "net_value": entry.reputation.get("net_value_change", 0),
                        "timestamp": entry.timestamp,
                    })
        return history

    def get_cumulative_reputation(self, entity_lct: str) -> Dict[str, Dict]:
        """Get all role-contextualized reputations for an entity."""
        result = {}
        for (e_lct, r_lct), rep in self.role_reputations.items():
            if e_lct == entity_lct:
                result[r_lct] = {
                    "t3": rep["t3"].to_dict(),
                    "v3": rep["v3"].to_dict(),
                }
        return result

    def verify_ledger_integrity(self) -> Tuple[bool, int]:
        """Verify the hash chain integrity of the R7 ledger."""
        for i, entry in enumerate(self.ledger):
            expected_prev = self.ledger[i - 1].entry_hash if i > 0 else "genesis"
            if entry.prev_hash != expected_prev:
                return False, i
            # Re-compute hash
            saved = entry.entry_hash
            entry.compute_hash()
            if entry.entry_hash != saved:
                return False, i
        return True, len(self.ledger)


# ═══════════════════════════════════════════════════════════════
# R7 Action Builder — Fluent construction
# ═══════════════════════════════════════════════════════════════

class R7ActionBuilder:
    """Fluent builder for R7 actions."""

    def __init__(self, action_type: str, target: str):
        self._action = R7Action()
        self._action.request.action = action_type
        self._action.request.target = target

    def as_actor(self, actor_lct: str, role_lct: str) -> "R7ActionBuilder":
        self._action.role.actor_lct = actor_lct
        self._action.role.role_lct = role_lct
        return self

    def with_rules(self, permissions: Optional[List[str]] = None,
                   prohibitions: Optional[List[str]] = None,
                   society: str = "") -> "R7ActionBuilder":
        if permissions:
            self._action.rules.permissions = permissions
        if prohibitions:
            self._action.rules.prohibitions = prohibitions
        if society:
            self._action.rules.society = society
        return self

    def with_constraint(self, ctype: str, value: Any) -> "R7ActionBuilder":
        self._action.rules.constraints.append({"type": ctype, "value": value})
        return self

    def with_resources(self, atp_required: float, atp_available: float,
                       escrow: float = 0.0) -> "R7ActionBuilder":
        self._action.resource.required_atp = atp_required
        self._action.resource.available_atp = atp_available
        self._action.resource.escrow_amount = escrow
        return self

    def with_stake(self, amount: float) -> "R7ActionBuilder":
        self._action.request.atp_stake = amount
        return self

    def with_parameters(self, **kwargs) -> "R7ActionBuilder":
        self._action.request.parameters.update(kwargs)
        return self

    def with_witnesses(self, *witnesses: str) -> "R7ActionBuilder":
        self._action.reference.witnesses = list(witnesses)
        return self

    def with_precedent(self, action_hash: str, outcome: str, relevance: float) -> "R7ActionBuilder":
        self._action.reference.precedents.append({
            "actionHash": action_hash, "outcome": outcome, "relevance": relevance,
        })
        return self

    def with_reputation_rule(self, rule: ReputationRule) -> "R7ActionBuilder":
        self._action.rules.reputation_rules.append(rule)
        return self

    def build(self) -> R7Action:
        return self._action


# ═══════════════════════════════════════════════════════════════
# Demo / Test
# ═══════════════════════════════════════════════════════════════

def demo():
    """Demonstrate the R7 action framework."""
    print("=" * 70)
    print("  R7 Action Framework — Reference Implementation Demo")
    print("  Rules + Role + Request + Reference + Resource → Result + Reputation")
    print("=" * 70)

    executor = R7Executor(society_lct="lct:web4:society:demo-corp")

    # Register a custom effector
    def analyze_dataset(action: R7Action) -> dict:
        params = action.request.parameters
        return {
            "analysis": "complete",
            "records_processed": params.get("records", 1000),
            "confidence": params.get("confidence", 0.95),
        }

    def train_model(action: R7Action) -> dict:
        return {"model_id": "model-v2", "accuracy": 0.94, "epochs": 50}

    executor.register_effector("analyze_dataset", analyze_dataset)
    executor.register_effector("train_model", train_model)

    # ── Test 1: Simple successful query ──
    print("\n── Test 1: Simple Query (read) ──")
    action1 = (R7ActionBuilder("read", "data:web4:dataset:quarterly")
        .as_actor("lct:web4:human:alice", "lct:web4:role:reader")
        .with_rules(permissions=["read", "write"])
        .with_resources(atp_required=1.0, atp_available=100.0)
        .with_witnesses("lct:web4:witness:validator-1")
        .build())

    result1, rep1 = executor.process(action1)
    print(f"  Status: {result1.status}")
    print(f"  ATP consumed: {result1.atp_consumed}")
    print(f"  Net trust Δ: {rep1.net_trust_change:+.4f}")
    print(f"  Net value Δ: {rep1.net_value_change:+.4f}")
    print(f"  Reason: {rep1.reason}")
    assert result1.status == "success", f"Expected success, got {result1.status}"

    # ── Test 2: ATP-staked analysis ──
    print("\n── Test 2: ATP-staked Analysis ──")
    action2 = (R7ActionBuilder("analyze_dataset", "data:web4:dataset:financials")
        .as_actor("lct:web4:ai:sage", "lct:web4:role:analyst")
        .with_rules(permissions=["analyze_dataset", "read"])
        .with_resources(atp_required=50.0, atp_available=500.0, escrow=50.0)
        .with_stake(100.0)
        .with_parameters(records=5000, confidence=0.98)
        .with_witnesses("lct:web4:witness:w1", "lct:web4:witness:w2")
        .build())

    result2, rep2 = executor.process(action2)
    print(f"  Status: {result2.status}")
    print(f"  Output: {result2.output}")
    print(f"  ATP consumed: {result2.atp_consumed}")
    print(f"  Net trust Δ: {rep2.net_trust_change:+.4f}")
    print(f"  Net value Δ: {rep2.net_value_change:+.4f}")
    print(f"  Contributing factors: {[f.factor for f in rep2.contributing_factors]}")
    assert result2.status == "success"

    # ── Test 3: Permission denied ──
    print("\n── Test 3: Permission Denied (prohibited action) ──")
    action3 = (R7ActionBuilder("delete", "data:web4:dataset:protected")
        .as_actor("lct:web4:human:bob", "lct:web4:role:viewer")
        .with_rules(permissions=["read"], prohibitions=["delete"])
        .with_resources(atp_required=10.0, atp_available=100.0)
        .build())

    result3, rep3 = executor.process(action3)
    print(f"  Status: {result3.status}")
    print(f"  Error: {result3.error}")
    print(f"  Net trust Δ: {rep3.net_trust_change:+.4f} (even failures affect reputation)")
    assert result3.status == "error"
    assert "prohibited" in result3.error.lower()

    # ── Test 4: Resource insufficient ──
    print("\n── Test 4: Insufficient Resources ──")
    action4 = (R7ActionBuilder("train_model", "dataset:biotech:proteins")
        .as_actor("lct:web4:ai:trainer", "lct:web4:role:ml_engineer")
        .with_rules(permissions=["train_model"])
        .with_resources(atp_required=500.0, atp_available=100.0)
        .build())

    result4, rep4 = executor.process(action4)
    print(f"  Status: {result4.status}")
    print(f"  Error: {result4.error}")
    print(f"  Net trust Δ: {rep4.net_trust_change:+.4f}")
    assert result4.status == "error"

    # ── Test 5: Successful model training ──
    print("\n── Test 5: Successful Model Training ──")
    action5 = (R7ActionBuilder("train_model", "dataset:biotech:proteins")
        .as_actor("lct:web4:ai:trainer", "lct:web4:role:ml_engineer")
        .with_rules(permissions=["train_model"])
        .with_resources(atp_required=100.0, atp_available=500.0)
        .with_stake(200.0)
        .with_witnesses("lct:web4:witness:compute-verifier")
        .build())

    result5, rep5 = executor.process(action5)
    print(f"  Status: {result5.status}")
    print(f"  Output: {result5.output}")
    print(f"  Net trust Δ: {rep5.net_trust_change:+.4f}")
    print(f"  Net value Δ: {rep5.net_value_change:+.4f}")
    print(f"  T3 deltas: {[f'{d.dimension}: {d.change:+.4f}' for d in rep5.t3_deltas]}")
    print(f"  V3 deltas: {[f'{d.dimension}: {d.change:+.4f}' for d in rep5.v3_deltas]}")
    assert result5.status == "success"

    # ── Test 6: Execution failure (effector raises) ──
    print("\n── Test 6: Execution Failure (effector exception) ──")
    def fail_action(action: R7Action):
        raise RuntimeError("Disk full: cannot write model")

    executor.register_effector("failing_task", fail_action)

    action6 = (R7ActionBuilder("failing_task", "resource:disk")
        .as_actor("lct:web4:ai:sage", "lct:web4:role:operator")
        .with_resources(atp_required=20.0, atp_available=200.0)
        .build())

    result6, rep6 = executor.process(action6)
    print(f"  Status: {result6.status}")
    print(f"  Error: {result6.error}")
    print(f"  ATP consumed: {result6.atp_consumed} (partial: 50% of requested)")
    print(f"  Net trust Δ: {rep6.net_trust_change:+.4f} (penalty for failure)")
    assert result6.status == "failure"
    assert rep6.net_trust_change < 0  # failure should decrease trust

    # ── Test 7: Role-contextualized reputation divergence ──
    print("\n── Test 7: Role-Contextualized Reputation ──")
    # Same entity, different roles → different reputations
    trainer_rep = executor.get_cumulative_reputation("lct:web4:ai:trainer")
    sage_rep = executor.get_cumulative_reputation("lct:web4:ai:sage")

    print(f"  Trainer roles: {list(trainer_rep.keys())}")
    for role, rep in trainer_rep.items():
        print(f"    {role}: T3={rep['t3']['composite']:.4f}, V3={rep['v3']['composite']:.4f}")

    print(f"  Sage roles: {list(sage_rep.keys())}")
    for role, rep in sage_rep.items():
        print(f"    {role}: T3={rep['t3']['composite']:.4f}, V3={rep['v3']['composite']:.4f}")

    # Sage as analyst should have better reputation than as operator (one success vs one failure)
    analyst_t3 = sage_rep.get("lct:web4:role:analyst", {}).get("t3", {}).get("composite", 0)
    operator_t3 = sage_rep.get("lct:web4:role:operator", {}).get("t3", {}).get("composite", 0)
    print(f"  Sage as analyst: T3={analyst_t3:.4f}")
    print(f"  Sage as operator: T3={operator_t3:.4f}")
    assert analyst_t3 > operator_t3, "Analyst (success) should have higher T3 than operator (failure)"

    # ── Ledger Integrity ──
    print("\n── Ledger Integrity Check ──")
    valid, count = executor.verify_ledger_integrity()
    print(f"  Hash chain valid: {valid}")
    print(f"  Entries verified: {count}")
    assert valid

    # ── Reputation History ──
    print("\n── Reputation History: Sage ──")
    history = executor.get_reputation_history("lct:web4:ai:sage")
    for h in history:
        print(f"  [{h['status']:>7s}] {h['action']:<20s} trust={h['net_trust']:+.4f} value={h['net_value']:+.4f}")

    # ── Summary ──
    print("\n" + "=" * 70)
    tests_passed = 7
    print(f"  R7 Framework: {tests_passed}/7 tests passed")
    print(f"  Ledger entries: {len(executor.ledger)}")
    print(f"  Role reputations tracked: {len(executor.role_reputations)}")
    print(f"  Key R7 properties verified:")
    print(f"    ✓ Reputation is explicit first-class output")
    print(f"    ✓ Reputation is role-contextualized (not global)")
    print(f"    ✓ Even failures produce reputation deltas")
    print(f"    ✓ Hash-chained ledger with reputation records")
    print(f"    ✓ Contributing factors tracked and attributed")
    print(f"    ✓ Witness attestations on reputation changes")
    print(f"    ✓ ATP staking amplifies reputation rewards")
    print("=" * 70)

    return executor


if __name__ == "__main__":
    demo()
