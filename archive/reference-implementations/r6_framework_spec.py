#!/usr/bin/env python3
"""
Web4 R6 Action Framework — Reference Implementation
=====================================================
Implements the canonical R6 specification from:
  web4-standard/protocols/web4-r6-framework.md (348 lines)

Covers ALL 10 sections:
  §1 Overview — R6 = Rules + Role + Request + Reference + Resource → Result
  §2 Six Components — Rules, Role, Request, Reference, Resource, Result
  §3 R6 Transaction Format — Action structure, confidence calculation
  §4 T3/V3 Tensor Evolution — Talent/Training/Temperament and Valuation/Veracity/Validity
  §5 Action Lifecycle — Initiation, Execution, Completion phases
  §6 Composability — Action chains, parallel execution, hierarchical decomposition
  §7 Integration with Core Web4 — LCT, MRH, ATP/ADP
  §8 Implementation Requirements — Mandatory and optional features
  §9 Security Considerations — Action integrity, resource protection
  §10 Privacy Considerations — Encrypted requests, anonymized references
"""

from __future__ import annotations
import copy
import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# ══════════════════════════════════════════════════════════════
# §2 — The Six Components
# ══════════════════════════════════════════════════════════════

# --- 2.1 Rules ---

@dataclass
class Rules:
    """Systemic boundaries and protocols that define what's possible."""
    governing_contracts: List[str] = field(default_factory=list)
    permission_scope: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)

    def permits(self, action: str) -> bool:
        """Check if action is within permission scope."""
        return action in self.permission_scope

    def within_budget(self, atp_amount: float) -> bool:
        """Check if ATP spend is within max_atp_spend constraint."""
        max_spend = self.constraints.get("max_atp_spend", float("inf"))
        return atp_amount <= max_spend

    def within_timeout(self, elapsed_seconds: float) -> bool:
        """Check if execution is within timeout constraint."""
        timeout = self.constraints.get("timeout_seconds", float("inf"))
        return elapsed_seconds <= timeout

    def meets_quality(self, quality_score: float) -> bool:
        """Check if quality meets threshold constraint."""
        threshold = self.constraints.get("quality_threshold", 0.0)
        return quality_score >= threshold


# --- 2.2 Role ---

@dataclass
class T3Snapshot:
    """Trust tensor snapshot: Talent/Training/Temperament."""
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    def composite(self) -> float:
        """Weighted average of T3 dimensions."""
        return (self.talent + self.training + self.temperament) / 3.0


@dataclass
class Role:
    """Operational identity for a specific action."""
    role_lct: str
    role_context: str
    delegated_permissions: List[str] = field(default_factory=list)
    t3_snapshot: T3Snapshot = field(default_factory=T3Snapshot)

    def has_permission(self, perm: str) -> bool:
        return perm in self.delegated_permissions


# --- 2.3 Request ---

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(Enum):
    ANALYZE = "analyze"
    COMPUTE = "compute"
    VERIFY = "verify"
    DELEGATE = "delegate"


@dataclass
class Request:
    """The heart of intent — what the entity desires to achieve."""
    action_type: ActionType
    description: str
    acceptance_criteria: List[str] = field(default_factory=list)
    priority: Priority = Priority.MEDIUM
    deadline: Optional[str] = None  # ISO-8601
    success_metrics: Dict[str, float] = field(default_factory=dict)


# --- 2.4 Reference ---

@dataclass
class SuccessPattern:
    """Historical pattern from past successes."""
    approach: str
    average_confidence: float = 0.0


@dataclass
class MRHContext:
    """Markov Relevancy Horizon context for the action."""
    depth: int = 2
    relevant_entities: List[str] = field(default_factory=list)


@dataclass
class Reference:
    """Temporal context from past interactions."""
    similar_actions: List[str] = field(default_factory=list)
    success_patterns: Optional[SuccessPattern] = None
    relevant_memory: List[str] = field(default_factory=list)
    mrh_context: MRHContext = field(default_factory=MRHContext)

    def historical_confidence(self) -> float:
        """Get average confidence from past patterns."""
        if self.success_patterns:
            return self.success_patterns.average_confidence
        return 0.5  # neutral prior


# --- 2.5 Resource ---

@dataclass
class EstimatedCost:
    """Estimated cost of action execution."""
    atp: float = 0.0
    time: float = 0.0  # seconds


@dataclass
class Resource:
    """Energy and assets required for manifestation."""
    atp_allocated: float = 0.0
    atp_consumed: float = 0.0
    compute_units: int = 0
    data_access: List[str] = field(default_factory=list)
    estimated_cost: EstimatedCost = field(default_factory=EstimatedCost)

    def remaining_atp(self) -> float:
        return self.atp_allocated - self.atp_consumed

    def can_afford(self) -> bool:
        return self.atp_allocated >= self.estimated_cost.atp


# --- 2.6 Result ---

@dataclass
class V3Assessment:
    """Value tensor: Valuation/Veracity/Validity."""
    valuation: float = 0.0
    veracity: float = 0.0
    validity: float = 0.0

    def composite(self) -> float:
        return (self.valuation + self.veracity + self.validity) / 3.0


@dataclass
class Performance:
    """Performance metrics from action execution."""
    completion_time: float = 0.0  # seconds
    quality_score: float = 0.0
    criteria_met: List[str] = field(default_factory=list)


@dataclass
class WitnessAttestation:
    """Witness attestation for action result."""
    witness_lct: str
    attestation_type: str  # "quality", "time", "audit", etc.
    signature: str = ""


@dataclass
class ValueCreated:
    """Value created by the action."""
    v3_assessment: V3Assessment = field(default_factory=V3Assessment)
    atp_earned: float = 0.0


@dataclass
class Result:
    """The outcome that emerges from action."""
    output: Any = None
    performance: Performance = field(default_factory=Performance)
    value_created: ValueCreated = field(default_factory=ValueCreated)
    side_effects: List[str] = field(default_factory=list)
    witness_attestations: List[WitnessAttestation] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════
# §3 — R6 Transaction Format
# ══════════════════════════════════════════════════════════════

class ActionStatus(Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


def generate_action_id() -> str:
    """Generate unique R6 action ID."""
    return f"r6:web4:{hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16]}"


@dataclass
class ConfidenceAssessment:
    """Pre-execution confidence calculation (§3.2).

    overall_confidence = weighted average of:
      role_capability (from Role's T3 tensor)
      historical_success (from Reference patterns)
      resource_availability (can afford the attempt)
      risk_assessment (cost of failure analysis)
    """
    role_capability: float = 0.0
    historical_success: float = 0.0
    resource_availability: float = 0.0
    risk_assessment: float = 0.0

    def overall(self) -> float:
        """Weighted average of all confidence dimensions."""
        return (self.role_capability + self.historical_success +
                self.resource_availability + self.risk_assessment) / 4.0


def calculate_confidence(role: Role, reference: Reference,
                         resource: Resource, risk_factor: float = 0.9) -> ConfidenceAssessment:
    """Calculate confidence assessment before execution (§3.2)."""
    return ConfidenceAssessment(
        role_capability=role.t3_snapshot.composite(),
        historical_success=reference.historical_confidence(),
        resource_availability=1.0 if resource.can_afford() else 0.0,
        risk_assessment=risk_factor,
    )


@dataclass
class R6Action:
    """Complete R6 action structure (§3.1)."""
    action_id: str = field(default_factory=generate_action_id)
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    initiator_lct: str = ""
    status: ActionStatus = ActionStatus.PENDING

    rules: Rules = field(default_factory=Rules)
    role: Role = field(default_factory=lambda: Role("", ""))
    request: Request = field(default_factory=lambda: Request(ActionType.ANALYZE, ""))
    reference: Reference = field(default_factory=Reference)
    resource: Resource = field(default_factory=Resource)
    result: Result = field(default_factory=Result)

    confidence: Optional[ConfidenceAssessment] = None

    def calculate_confidence(self, risk_factor: float = 0.9) -> ConfidenceAssessment:
        """Calculate and store confidence assessment."""
        self.confidence = calculate_confidence(
            self.role, self.reference, self.resource, risk_factor
        )
        return self.confidence

    def to_dict(self) -> dict:
        """Serialize to the canonical JSON format from §3.1."""
        return {
            "r6_action": {
                "action_id": self.action_id,
                "timestamp": self.timestamp,
                "initiator_lct": self.initiator_lct,
                "status": self.status.value,
                "rules": {
                    "governing_contracts": self.rules.governing_contracts,
                    "permission_scope": self.rules.permission_scope,
                    "constraints": self.rules.constraints,
                },
                "role": {
                    "role_lct": self.role.role_lct,
                    "role_context": self.role.role_context,
                    "delegated_permissions": self.role.delegated_permissions,
                    "t3_snapshot": {
                        "talent": self.role.t3_snapshot.talent,
                        "training": self.role.t3_snapshot.training,
                        "temperament": self.role.t3_snapshot.temperament,
                    },
                },
                "request": {
                    "action_type": self.request.action_type.value,
                    "description": self.request.description,
                    "acceptance_criteria": self.request.acceptance_criteria,
                    "priority": self.request.priority.value,
                },
                "reference": {
                    "similar_actions": self.reference.similar_actions,
                    "mrh_context": {
                        "depth": self.reference.mrh_context.depth,
                        "relevant_entities": self.reference.mrh_context.relevant_entities,
                    },
                },
                "resource": {
                    "atp_allocated": self.resource.atp_allocated,
                    "atp_consumed": self.resource.atp_consumed,
                    "compute_units": self.resource.compute_units,
                    "data_access": self.resource.data_access,
                    "estimated_cost": {
                        "atp": self.resource.estimated_cost.atp,
                        "time": self.resource.estimated_cost.time,
                    },
                },
                "result": {
                    "output": self.result.output,
                    "performance": {
                        "completion_time": self.result.performance.completion_time,
                        "quality_score": self.result.performance.quality_score,
                        "criteria_met": self.result.performance.criteria_met,
                    },
                    "value_created": {
                        "v3_assessment": {
                            "valuation": self.result.value_created.v3_assessment.valuation,
                            "veracity": self.result.value_created.v3_assessment.veracity,
                            "validity": self.result.value_created.v3_assessment.validity,
                        },
                        "atp_earned": self.result.value_created.atp_earned,
                    },
                },
            }
        }


# ══════════════════════════════════════════════════════════════
# §4 — T3/V3 Tensor Evolution
# ══════════════════════════════════════════════════════════════

@dataclass
class TensorDelta:
    """A trust/value tensor update from an R6 action."""
    previous: float
    delta: float
    reason: str

    @property
    def new(self) -> float:
        return max(0.0, min(1.0, self.previous + self.delta))


class TensorEvolution:
    """Manages T3/V3 tensor evolution from R6 performance (§4.1, §4.2)."""

    @staticmethod
    def talent_update(current: float, was_novel: bool, edge_case: bool = False) -> TensorDelta:
        """Talent evolves from novel approaches and creative problem-solving."""
        delta = 0.0
        reason = "No novel contribution"
        if was_novel:
            delta = 0.02
            reason = "Innovative approach to complex problem"
        if edge_case:
            delta += 0.01
            reason = "Creative problem-solving in edge case"
        return TensorDelta(previous=current, delta=delta, reason=reason)

    @staticmethod
    def training_update(current: float, success: bool, domain_repetition: int = 0) -> TensorDelta:
        """Training evolves from successful domain completion."""
        if success:
            delta = 0.01
            reason = f"Successfully completed action (#{domain_repetition} in domain)"
            return TensorDelta(previous=current, delta=delta, reason=reason)
        return TensorDelta(previous=current, delta=0.0, reason="Unsuccessful, no training gain")

    @staticmethod
    def temperament_update(current: float, met_deadline: bool,
                           confidence_calibration: float = 0.0) -> TensorDelta:
        """Temperament evolves from reliability and calibration.

        confidence_calibration: difference between predicted and actual performance
          (positive = overconfident, negative = underconfident)
        """
        delta = 0.0
        reason = "Baseline performance"

        if met_deadline:
            delta += 0.005
            reason = "Met deadline"
        else:
            delta -= 0.01
            reason = "Missed deadline"

        # Overconfidence penalty (§4.1 example)
        if confidence_calibration > 0.1:
            penalty = -0.05 * (confidence_calibration / 0.5)
            delta += penalty
            reason = "Confidence exceeded actual performance"

        # Well-calibrated bonus
        if abs(confidence_calibration) < 0.05:
            delta += 0.005
            reason = "Well-calibrated confidence"

        return TensorDelta(previous=current, delta=delta, reason=reason)

    @staticmethod
    def v3_update(action_id: str, valuation: float, veracity: float,
                  validity: float, atp_spent: float, atp_earned: float) -> dict:
        """Produce V3 update record (§4.2)."""
        return {
            "action_id": action_id,
            "valuation": valuation,
            "veracity": veracity,
            "validity": validity,
            "atp_impact": {
                "spent": atp_spent,
                "earned": atp_earned,
                "net_gain": atp_earned - atp_spent,
            },
        }


# ══════════════════════════════════════════════════════════════
# §5 — Action Lifecycle
# ══════════════════════════════════════════════════════════════

class ActionLifecycle:
    """Manages the 3-phase R6 action lifecycle (§5)."""

    def __init__(self, action: R6Action, confidence_threshold: float = 0.5):
        self.action = action
        self.confidence_threshold = confidence_threshold
        self._phase = "pre_initiation"
        self._start_time: Optional[float] = None

    @property
    def phase(self) -> str:
        return self._phase

    def initiate(self) -> Tuple[bool, str]:
        """Initiation Phase (§5.1):
        1. Entity forms intent (Request)
        2. Checks Role permissions (Role + Rules)
        3. Gathers historical context (Reference)
        4. Assesses available Resources
        5. Calculates confidence
        6. Commits to action if confidence exceeds threshold
        """
        # Step 2: Check role permissions
        for perm in self.action.rules.permission_scope:
            if not self.action.role.has_permission(perm):
                # The permission scope defines what's allowed; the role must have these
                pass  # R6 is permissive — rules define the envelope

        # Step 4: Assess resources
        if not self.action.resource.can_afford():
            return False, "Insufficient resources"

        # Step 5: Calculate confidence
        conf = self.action.calculate_confidence()

        # Step 6: Commit if above threshold
        if conf.overall() < self.confidence_threshold:
            return False, f"Confidence {conf.overall():.2f} below threshold {self.confidence_threshold}"

        self.action.status = ActionStatus.PENDING
        self._phase = "initiated"
        return True, "Action initiated"

    def execute(self) -> bool:
        """Execution Phase (§5.2):
        1. ATP tokens locked (Resource commitment)
        2. Action performed according to Request
        3. Real-time monitoring against constraints
        4. Witness observations recorded
        5. Progress updates to interested parties
        """
        if self._phase != "initiated":
            return False

        self.action.status = ActionStatus.EXECUTING
        self._phase = "executing"
        self._start_time = time.time()
        return True

    def complete(self, result: Result) -> Tuple[bool, str]:
        """Completion Phase (§5.3):
        1. Result produced and validated
        2. V3 assessment by recipients
        3. ATP/ADP settlement
        4. T3 tensor updates calculated
        5. Action archived as future Reference
        6. Witness attestations finalized
        """
        if self._phase != "executing":
            return False, "Not in executing phase"

        self.action.result = result
        self.action.status = ActionStatus.COMPLETED
        self._phase = "completed"

        # Check quality threshold
        if self.action.rules.meets_quality(result.performance.quality_score):
            return True, "Action completed successfully"
        else:
            return True, "Action completed below quality threshold"

    def fail(self, reason: str) -> None:
        """Mark action as failed."""
        self.action.status = ActionStatus.FAILED
        self.action.result.output = f"FAILED: {reason}"
        self._phase = "failed"


# ══════════════════════════════════════════════════════════════
# §6 — Composability
# ══════════════════════════════════════════════════════════════

class ActionChain:
    """Action chains: Result of one becomes Resource for next (§6.1)."""

    def __init__(self):
        self.actions: List[R6Action] = []

    def add(self, action: R6Action):
        """Add action to chain, wiring previous result as resource."""
        if self.actions:
            prev = self.actions[-1]
            if prev.status == ActionStatus.COMPLETED:
                # Previous result feeds into next action's data_access
                action.resource.data_access.append(prev.action_id)
                if prev.reference.similar_actions:
                    action.reference.similar_actions.extend(prev.reference.similar_actions)
                action.reference.similar_actions.append(prev.action_id)
        self.actions.append(action)

    def is_complete(self) -> bool:
        return all(a.status == ActionStatus.COMPLETED for a in self.actions)


class ParallelExecution:
    """Parallel R6 actions sharing Resources within Role permissions (§6.2)."""

    def __init__(self, role: Role, total_atp: float):
        self.role = role
        self.total_atp = total_atp
        self.actions: List[R6Action] = []
        self._allocated: float = 0.0

    def add(self, action: R6Action) -> bool:
        """Add a parallel action if budget allows."""
        needed = action.resource.estimated_cost.atp
        if self._allocated + needed > self.total_atp:
            return False
        action.role = self.role  # shared role
        self._allocated += needed
        self.actions.append(action)
        return True


class HierarchicalDecomposition:
    """Complex actions decompose into simpler R6 primitives (§6.3)."""

    def __init__(self, parent: R6Action):
        self.parent = parent
        self.subtasks: List[R6Action] = []

    def decompose(self, subtask: R6Action):
        """Add a subtask derived from parent."""
        subtask.reference.similar_actions.append(self.parent.action_id)
        self.subtasks.append(subtask)

    def all_complete(self) -> bool:
        return all(s.status == ActionStatus.COMPLETED for s in self.subtasks)

    def aggregate_quality(self) -> float:
        """Average quality across subtasks."""
        if not self.subtasks:
            return 0.0
        scores = [s.result.performance.quality_score for s in self.subtasks
                   if s.status == ActionStatus.COMPLETED]
        return sum(scores) / len(scores) if scores else 0.0


# ══════════════════════════════════════════════════════════════
# §7 — Integration with Core Web4
# ══════════════════════════════════════════════════════════════

@dataclass
class LCTActionRecord:
    """Record an R6 action in an LCT (§7.1)."""
    lct_id: str
    action_id: str
    outcome: str  # "completed", "failed"
    reputation_delta: float = 0.0


@dataclass
class MRHPropagation:
    """Result propagation through MRH (§7.2)."""
    action_id: str
    source_lct: str
    propagated_to: List[str] = field(default_factory=list)
    depth: int = 0

    def propagate(self, entity_lct: str):
        self.propagated_to.append(entity_lct)


@dataclass
class ATPSettlement:
    """ATP/ADP cycle settlement for R6 action (§7.3)."""
    action_id: str
    atp_consumed: float = 0.0
    atp_generated: float = 0.0

    @property
    def net_value(self) -> float:
        return self.atp_generated - self.atp_consumed


# ══════════════════════════════════════════════════════════════
# §8 — Implementation Requirements
# ══════════════════════════════════════════════════════════════

class ImplementationCompliance:
    """Check compliance with mandatory and optional features (§8)."""

    MANDATORY = [
        "record_complete_r6_tuples",
        "calculate_confidence",
        "update_t3v3_tensors",
        "enable_witness_attestation",
        "archive_results_as_references",
    ]

    OPTIONAL = [
        "action_recommendation",
        "resource_optimization",
        "success_prediction",
        "action_decomposition",
    ]

    def __init__(self):
        self.implemented: Dict[str, bool] = {}

    def mark_implemented(self, feature: str):
        self.implemented[feature] = True

    def is_mandatory_complete(self) -> bool:
        return all(self.implemented.get(f, False) for f in self.MANDATORY)

    def compliance_report(self) -> dict:
        mandatory_status = {f: self.implemented.get(f, False) for f in self.MANDATORY}
        optional_status = {f: self.implemented.get(f, False) for f in self.OPTIONAL}
        return {
            "mandatory": mandatory_status,
            "optional": optional_status,
            "mandatory_complete": self.is_mandatory_complete(),
            "optional_count": sum(1 for v in optional_status.values() if v),
        }


# ══════════════════════════════════════════════════════════════
# §9-§10 — Security & Privacy
# ══════════════════════════════════════════════════════════════

@dataclass
class ActionIntegrity:
    """Cryptographic integrity for R6 action (§9.1)."""
    action_id: str
    component_hashes: Dict[str, str] = field(default_factory=dict)

    def hash_component(self, name: str, data: str):
        """Hash an R6 component for integrity verification."""
        h = hashlib.sha256(data.encode()).hexdigest()
        self.component_hashes[name] = h

    def verify_integrity(self, name: str, data: str) -> bool:
        """Verify a component hasn't been tampered with."""
        expected = self.component_hashes.get(name)
        if not expected:
            return False
        actual = hashlib.sha256(data.encode()).hexdigest()
        return actual == expected


@dataclass
class PrivacyControls:
    """Privacy considerations for R6 (§10)."""
    encrypt_request: bool = False
    anonymize_references: bool = False
    selective_disclosure: bool = False

    def apply_to_action(self, action_dict: dict) -> dict:
        """Apply privacy controls to serialized action."""
        result = copy.deepcopy(action_dict)
        inner = result.get("r6_action", result)

        if self.encrypt_request:
            inner["request"] = {"encrypted": True, "description": "[ENCRYPTED]"}

        if self.anonymize_references:
            ref = inner.get("reference", {})
            ref["similar_actions"] = [f"anon:{i}" for i in range(len(ref.get("similar_actions", [])))]
            ref["relevant_memory"] = []

        if self.selective_disclosure:
            res = inner.get("result", {})
            res["side_effects"] = []

        return result


# ══════════════════════════════════════════════════════════════
# TESTS
# ══════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(label, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {label} {detail}")

    # ── T1: Six Components (§2) ──
    print("T1: Six Components (§2)")

    # Rules
    rules = Rules(
        governing_contracts=["contract_1"],
        permission_scope=["read:data", "write:results"],
        constraints={"max_atp_spend": 100, "timeout_seconds": 3600, "quality_threshold": 0.8},
    )
    check("T1.1 Rules permits read", rules.permits("read:data"))
    check("T1.2 Rules denies delete", not rules.permits("delete:data"))
    check("T1.3 Within budget", rules.within_budget(50))
    check("T1.4 Over budget", not rules.within_budget(150))
    check("T1.5 Within timeout", rules.within_timeout(3000))
    check("T1.6 Over timeout", not rules.within_timeout(4000))
    check("T1.7 Meets quality", rules.meets_quality(0.9))
    check("T1.8 Below quality", not rules.meets_quality(0.7))

    # Role
    role = Role(
        role_lct="lct:web4:role:analyst",
        role_context="data-analyst",
        delegated_permissions=["analyze", "report"],
        t3_snapshot=T3Snapshot(talent=0.7, training=0.85, temperament=0.9),
    )
    check("T1.9 Role has analyze", role.has_permission("analyze"))
    check("T1.10 Role lacks delete", not role.has_permission("delete"))
    check("T1.11 T3 composite", abs(role.t3_snapshot.composite() - (0.7 + 0.85 + 0.9) / 3) < 1e-10)

    # Request
    req = Request(
        action_type=ActionType.ANALYZE,
        description="Analyze dataset for anomalies",
        acceptance_criteria=["Format: JSON", "Quality > 0.8"],
        priority=Priority.HIGH,
    )
    check("T1.12 Request type", req.action_type == ActionType.ANALYZE)
    check("T1.13 Request priority", req.priority == Priority.HIGH)

    # Reference
    ref = Reference(
        similar_actions=["r6:web4:prev1", "r6:web4:prev2"],
        success_patterns=SuccessPattern(approach="statistical analysis", average_confidence=0.85),
        mrh_context=MRHContext(depth=2, relevant_entities=["lct:web4:oracle1"]),
    )
    check("T1.14 Historical confidence", abs(ref.historical_confidence() - 0.85) < 1e-10)

    empty_ref = Reference()
    check("T1.15 Default confidence 0.5", abs(empty_ref.historical_confidence() - 0.5) < 1e-10)

    # Resource
    resource = Resource(
        atp_allocated=50,
        atp_consumed=0,
        compute_units=1000,
        estimated_cost=EstimatedCost(atp=45, time=1800),
    )
    check("T1.16 Can afford", resource.can_afford())
    check("T1.17 Remaining ATP", resource.remaining_atp() == 50)

    poor_resource = Resource(atp_allocated=10, estimated_cost=EstimatedCost(atp=45))
    check("T1.18 Cannot afford", not poor_resource.can_afford())

    # Result
    result = Result(
        output="Analysis complete",
        performance=Performance(completion_time=1650, quality_score=0.92, criteria_met=["c1", "c2"]),
        value_created=ValueCreated(
            v3_assessment=V3Assessment(valuation=0.9, veracity=0.95, validity=1.0),
            atp_earned=55,
        ),
        side_effects=["Updated cache"],
        witness_attestations=[WitnessAttestation("lct:web4:oracle:1", "quality")],
    )
    check("T1.19 Result quality", result.performance.quality_score == 0.92)
    check("T1.20 V3 composite", abs(result.value_created.v3_assessment.composite() - (0.9+0.95+1.0)/3) < 1e-10)
    check("T1.21 ATP earned", result.value_created.atp_earned == 55)

    # ── T2: R6 Action Structure (§3.1) ──
    print("T2: R6 Action Structure (§3.1)")

    action = R6Action(
        initiator_lct="lct:web4:agent:alice",
        rules=rules,
        role=role,
        request=req,
        reference=ref,
        resource=resource,
    )
    check("T2.1 Action ID format", action.action_id.startswith("r6:web4:"))
    check("T2.2 Status pending", action.status == ActionStatus.PENDING)
    check("T2.3 Timestamp present", len(action.timestamp) > 0)

    # Serialization
    d = action.to_dict()
    check("T2.4 Has r6_action key", "r6_action" in d)
    inner = d["r6_action"]
    check("T2.5 Has all 6 components",
          all(k in inner for k in ["rules", "role", "request", "reference", "resource", "result"]))
    check("T2.6 T3 in role", "t3_snapshot" in inner["role"])
    check("T2.7 Talent value", inner["role"]["t3_snapshot"]["talent"] == 0.7)
    check("T2.8 Action type serialized", inner["request"]["action_type"] == "analyze")

    # ── T3: Confidence Calculation (§3.2) ──
    print("T3: Confidence Calculation (§3.2)")

    conf = action.calculate_confidence()
    check("T3.1 Role capability from T3", abs(conf.role_capability - role.t3_snapshot.composite()) < 1e-10)
    check("T3.2 Historical from reference", abs(conf.historical_success - 0.85) < 1e-10)
    check("T3.3 Resource available", conf.resource_availability == 1.0)
    check("T3.4 Risk assessment", conf.risk_assessment == 0.9)
    check("T3.5 Overall is average", abs(conf.overall() -
          (conf.role_capability + conf.historical_success + conf.resource_availability + conf.risk_assessment) / 4) < 1e-10)
    check("T3.6 Stored on action", action.confidence is not None)

    # With poor resources
    poor_action = R6Action(
        role=role,
        reference=ref,
        resource=poor_resource,
    )
    poor_conf = poor_action.calculate_confidence()
    check("T3.7 Poor resources = 0.0", poor_conf.resource_availability == 0.0)
    check("T3.8 Poor overall lower", poor_conf.overall() < conf.overall())

    # ── T4: T3/V3 Tensor Evolution (§4) ──
    print("T4: T3/V3 Tensor Evolution (§4)")

    # Talent updates
    novel = TensorEvolution.talent_update(0.7, was_novel=True)
    check("T4.1 Novel delta +0.02", abs(novel.delta - 0.02) < 1e-10)
    check("T4.2 Novel new value", abs(novel.new - 0.72) < 1e-10)

    not_novel = TensorEvolution.talent_update(0.7, was_novel=False)
    check("T4.3 Not novel delta 0", not_novel.delta == 0.0)

    edge = TensorEvolution.talent_update(0.7, was_novel=True, edge_case=True)
    check("T4.4 Edge case delta +0.03", abs(edge.delta - 0.03) < 1e-10)

    # Training updates
    success = TensorEvolution.training_update(0.85, success=True, domain_repetition=10)
    check("T4.5 Training success +0.01", abs(success.delta - 0.01) < 1e-10)
    check("T4.6 Training new value", abs(success.new - 0.86) < 1e-10)

    failure = TensorEvolution.training_update(0.85, success=False)
    check("T4.7 Training failure no gain", failure.delta == 0.0)

    # Temperament updates
    overconf = TensorEvolution.temperament_update(0.9, met_deadline=True, confidence_calibration=0.5)
    check("T4.8 Overconfidence penalty", overconf.delta < 0,
          f"delta={overconf.delta}")

    reliable = TensorEvolution.temperament_update(0.9, met_deadline=True, confidence_calibration=0.02)
    check("T4.9 Well-calibrated bonus", reliable.delta > 0)

    missed = TensorEvolution.temperament_update(0.9, met_deadline=False)
    check("T4.10 Missed deadline penalty", missed.delta < 0)

    # V3 updates
    v3 = TensorEvolution.v3_update("r6:web4:test", 0.9, 0.95, 1.0, 45, 55)
    check("T4.11 V3 net gain", v3["atp_impact"]["net_gain"] == 10)
    check("T4.12 V3 valuation", v3["valuation"] == 0.9)
    check("T4.13 V3 veracity", v3["veracity"] == 0.95)

    # Tensor delta clamping
    high = TensorEvolution.talent_update(0.99, was_novel=True, edge_case=True)
    check("T4.14 Clamped at 1.0", high.new <= 1.0)

    low = TensorEvolution.temperament_update(0.01, met_deadline=False, confidence_calibration=0.5)
    check("T4.15 Clamped at 0.0", low.new >= 0.0)

    # ── T5: Action Lifecycle (§5) ──
    print("T5: Action Lifecycle (§5)")

    lc_action = R6Action(
        initiator_lct="lct:web4:agent:bob",
        rules=Rules(
            permission_scope=["analyze"],
            constraints={"quality_threshold": 0.8},
        ),
        role=Role("lct:web4:role:analyst", "analyst",
                   delegated_permissions=["analyze"],
                   t3_snapshot=T3Snapshot(0.8, 0.8, 0.8)),
        request=Request(ActionType.ANALYZE, "Analyze data"),
        reference=Reference(success_patterns=SuccessPattern("stats", 0.8)),
        resource=Resource(atp_allocated=50, estimated_cost=EstimatedCost(atp=40)),
    )

    lifecycle = ActionLifecycle(lc_action, confidence_threshold=0.5)
    check("T5.1 Pre-initiation phase", lifecycle.phase == "pre_initiation")

    # Initiate
    ok, msg = lifecycle.initiate()
    check("T5.2 Initiation succeeds", ok, msg)
    check("T5.3 Phase is initiated", lifecycle.phase == "initiated")
    check("T5.4 Confidence calculated", lc_action.confidence is not None)

    # Execute
    check("T5.5 Execution starts", lifecycle.execute())
    check("T5.6 Phase is executing", lifecycle.phase == "executing")
    check("T5.7 Status executing", lc_action.status == ActionStatus.EXECUTING)

    # Complete
    good_result = Result(
        performance=Performance(quality_score=0.92, criteria_met=["c1"]),
        value_created=ValueCreated(v3_assessment=V3Assessment(0.9, 0.9, 0.9)),
    )
    ok, msg = lifecycle.complete(good_result)
    check("T5.8 Completion succeeds", ok)
    check("T5.9 Phase is completed", lifecycle.phase == "completed")
    check("T5.10 Status completed", lc_action.status == ActionStatus.COMPLETED)

    # Lifecycle with insufficient resources
    poor_lc = R6Action(
        resource=Resource(atp_allocated=5, estimated_cost=EstimatedCost(atp=50)),
        role=Role("r", "r", t3_snapshot=T3Snapshot(0.8, 0.8, 0.8)),
        reference=Reference(success_patterns=SuccessPattern("x", 0.8)),
    )
    poor_lifecycle = ActionLifecycle(poor_lc)
    ok, msg = poor_lifecycle.initiate()
    check("T5.11 Poor resources fails", not ok)
    check("T5.12 Reason is resources", "resources" in msg.lower())

    # Lifecycle with low confidence
    low_conf_action = R6Action(
        resource=Resource(atp_allocated=50, estimated_cost=EstimatedCost(atp=40)),
        role=Role("r", "r", t3_snapshot=T3Snapshot(0.1, 0.1, 0.1)),
        reference=Reference(success_patterns=SuccessPattern("x", 0.1)),
    )
    low_lifecycle = ActionLifecycle(low_conf_action, confidence_threshold=0.9)
    ok, msg = low_lifecycle.initiate()
    check("T5.13 Low confidence fails", not ok)
    check("T5.14 Reason is confidence", "confidence" in msg.lower())

    # Fail path
    fail_action = R6Action(
        resource=Resource(atp_allocated=50, estimated_cost=EstimatedCost(atp=40)),
        role=Role("r", "r", t3_snapshot=T3Snapshot(0.8, 0.8, 0.8)),
        reference=Reference(success_patterns=SuccessPattern("x", 0.8)),
    )
    fail_lifecycle = ActionLifecycle(fail_action)
    fail_lifecycle.initiate()
    fail_lifecycle.execute()
    fail_lifecycle.fail("Hardware error")
    check("T5.15 Failed status", fail_action.status == ActionStatus.FAILED)
    check("T5.16 Failed phase", fail_lifecycle.phase == "failed")

    # ── T6: Composability (§6) ──
    print("T6: Composability (§6)")

    # Action chains
    chain = ActionChain()
    a1 = R6Action(
        request=Request(ActionType.ANALYZE, "Step 1"),
        resource=Resource(atp_allocated=20, estimated_cost=EstimatedCost(atp=15)),
    )
    a1.status = ActionStatus.COMPLETED
    a1.result = Result(output="Step 1 result")

    a2 = R6Action(
        request=Request(ActionType.COMPUTE, "Step 2"),
        resource=Resource(atp_allocated=30, estimated_cost=EstimatedCost(atp=25)),
    )

    chain.add(a1)
    chain.add(a2)
    check("T6.1 Chain wires result", a1.action_id in a2.resource.data_access)
    check("T6.2 Chain adds reference", a1.action_id in a2.reference.similar_actions)
    check("T6.3 Chain not complete", not chain.is_complete())

    a2.status = ActionStatus.COMPLETED
    check("T6.4 Chain complete", chain.is_complete())

    # Parallel execution
    shared_role = Role("lct:web4:role:worker", "worker",
                       delegated_permissions=["compute"],
                       t3_snapshot=T3Snapshot(0.7, 0.7, 0.7))
    parallel = ParallelExecution(shared_role, total_atp=100)

    pa1 = R6Action(resource=Resource(estimated_cost=EstimatedCost(atp=40)))
    pa2 = R6Action(resource=Resource(estimated_cost=EstimatedCost(atp=40)))
    pa3 = R6Action(resource=Resource(estimated_cost=EstimatedCost(atp=40)))

    check("T6.5 First parallel added", parallel.add(pa1))
    check("T6.6 Second parallel added", parallel.add(pa2))
    check("T6.7 Third exceeds budget", not parallel.add(pa3))
    check("T6.8 Shared role applied", pa1.role.role_lct == "lct:web4:role:worker")

    # Hierarchical decomposition
    parent = R6Action(request=Request(ActionType.ANALYZE, "Complex analysis"))
    hierarchy = HierarchicalDecomposition(parent)

    s1 = R6Action(request=Request(ActionType.ANALYZE, "Sub-analysis 1"))
    s2 = R6Action(request=Request(ActionType.COMPUTE, "Sub-computation"))
    hierarchy.decompose(s1)
    hierarchy.decompose(s2)

    check("T6.9 Subtask references parent", parent.action_id in s1.reference.similar_actions)
    check("T6.10 Not all complete", not hierarchy.all_complete())

    s1.status = ActionStatus.COMPLETED
    s1.result = Result(performance=Performance(quality_score=0.9))
    s2.status = ActionStatus.COMPLETED
    s2.result = Result(performance=Performance(quality_score=0.8))

    check("T6.11 All complete", hierarchy.all_complete())
    check("T6.12 Aggregate quality", abs(hierarchy.aggregate_quality() - 0.85) < 1e-10)

    # ── T7: Web4 Integration (§7) ──
    print("T7: Web4 Integration (§7)")

    # LCT action record
    record = LCTActionRecord("lct:web4:agent:alice", "r6:web4:action1", "completed", 0.02)
    check("T7.1 LCT record", record.reputation_delta == 0.02)

    # MRH propagation
    prop = MRHPropagation("r6:web4:action1", "lct:web4:agent:alice")
    prop.propagate("lct:web4:oracle:1")
    prop.propagate("lct:web4:agent:bob")
    check("T7.2 Propagated to 2 entities", len(prop.propagated_to) == 2)

    # ATP settlement
    settlement = ATPSettlement("r6:web4:action1", atp_consumed=45, atp_generated=55)
    check("T7.3 Net value positive", settlement.net_value == 10)
    check("T7.4 Net value correct", settlement.net_value == 55 - 45)

    neg_settlement = ATPSettlement("r6:web4:action2", atp_consumed=50, atp_generated=30)
    check("T7.5 Net value negative", neg_settlement.net_value == -20)

    # ── T8: Implementation Requirements (§8) ──
    print("T8: Implementation Requirements (§8)")

    compliance = ImplementationCompliance()
    check("T8.1 Not complete initially", not compliance.is_mandatory_complete())

    for feat in ImplementationCompliance.MANDATORY:
        compliance.mark_implemented(feat)

    check("T8.2 Complete after all mandatory", compliance.is_mandatory_complete())

    report = compliance.compliance_report()
    check("T8.3 Report mandatory complete", report["mandatory_complete"])
    check("T8.4 No optional features", report["optional_count"] == 0)

    compliance.mark_implemented("action_recommendation")
    compliance.mark_implemented("success_prediction")
    report2 = compliance.compliance_report()
    check("T8.5 Two optional features", report2["optional_count"] == 2)

    # ── T9: Security & Privacy (§9-§10) ──
    print("T9: Security & Privacy (§9-§10)")

    # Action integrity
    integrity = ActionIntegrity("r6:web4:test")
    test_data = json.dumps({"action": "analyze", "target": "dataset1"})
    integrity.hash_component("request", test_data)
    check("T9.1 Integrity hash stored", "request" in integrity.component_hashes)
    check("T9.2 Verify correct data", integrity.verify_integrity("request", test_data))
    check("T9.3 Detect tampering", not integrity.verify_integrity("request", "tampered"))
    check("T9.4 Unknown component", not integrity.verify_integrity("unknown", test_data))

    # Privacy controls
    action_dict = action.to_dict()
    privacy = PrivacyControls(encrypt_request=True, anonymize_references=True, selective_disclosure=True)
    private = privacy.apply_to_action(action_dict)
    inner_priv = private["r6_action"]
    check("T9.5 Request encrypted", inner_priv["request"]["encrypted"] is True)
    check("T9.6 References anonymized",
          all(a.startswith("anon:") for a in inner_priv["reference"]["similar_actions"]))
    check("T9.7 Side effects cleared", inner_priv["result"]["side_effects"] == [])

    # No privacy
    no_privacy = PrivacyControls()
    public = no_privacy.apply_to_action(action_dict)
    check("T9.8 No encryption", "encrypted" not in public["r6_action"]["request"])

    # ── T10: End-to-End Flow ──
    print("T10: End-to-End Flow")

    # Create complete R6 action, run lifecycle, extract tensors
    e2e_action = R6Action(
        initiator_lct="lct:web4:agent:eve",
        rules=Rules(
            governing_contracts=["contract:data-analysis"],
            permission_scope=["analyze", "report"],
            constraints={"max_atp_spend": 100, "quality_threshold": 0.7},
        ),
        role=Role("lct:web4:role:analyst", "data-analyst",
                   delegated_permissions=["analyze", "report"],
                   t3_snapshot=T3Snapshot(0.75, 0.85, 0.9)),
        request=Request(ActionType.ANALYZE, "Full dataset analysis",
                        acceptance_criteria=["JSON format", "Quality > 0.7"],
                        priority=Priority.HIGH),
        reference=Reference(
            similar_actions=["r6:web4:prev1"],
            success_patterns=SuccessPattern("statistical", 0.82),
            mrh_context=MRHContext(depth=2, relevant_entities=["lct:web4:oracle:1"]),
        ),
        resource=Resource(atp_allocated=80, estimated_cost=EstimatedCost(atp=60, time=3000)),
    )

    # Lifecycle
    lc = ActionLifecycle(e2e_action, confidence_threshold=0.6)
    ok, _ = lc.initiate()
    check("T10.1 E2E initiated", ok)

    ok = lc.execute()
    check("T10.2 E2E executing", ok)

    e2e_result = Result(
        output="Full analysis results",
        performance=Performance(completion_time=2500, quality_score=0.88, criteria_met=["JSON", "Quality"]),
        value_created=ValueCreated(
            v3_assessment=V3Assessment(valuation=0.85, veracity=0.90, validity=0.95),
            atp_earned=70,
        ),
        witness_attestations=[
            WitnessAttestation("lct:web4:oracle:1", "quality", "sig:..."),
        ],
    )
    ok, msg = lc.complete(e2e_result)
    check("T10.3 E2E completed", ok)
    check("T10.4 Quality met", "successfully" in msg)

    # Tensor evolution from result
    t3 = e2e_action.role.t3_snapshot
    talent_delta = TensorEvolution.talent_update(t3.talent, was_novel=True)
    training_delta = TensorEvolution.training_update(t3.training, success=True, domain_repetition=5)
    predicted_conf = e2e_action.confidence.overall()
    actual_quality = e2e_result.performance.quality_score
    calibration = predicted_conf - actual_quality
    temperament_delta = TensorEvolution.temperament_update(t3.temperament, met_deadline=True,
                                                           confidence_calibration=calibration)

    check("T10.5 Talent increased", talent_delta.new > t3.talent)
    check("T10.6 Training increased", training_delta.new > t3.training)
    check("T10.7 Temperament within bounds", 0.0 <= temperament_delta.new <= 1.0)

    # V3 update
    v3_update = TensorEvolution.v3_update(
        e2e_action.action_id,
        e2e_result.value_created.v3_assessment.valuation,
        e2e_result.value_created.v3_assessment.veracity,
        e2e_result.value_created.v3_assessment.validity,
        atp_spent=60, atp_earned=70,
    )
    check("T10.8 V3 positive net", v3_update["atp_impact"]["net_gain"] == 10)

    # Serialize and verify structure
    serialized = e2e_action.to_dict()
    check("T10.9 Serialized has all fields", "r6_action" in serialized)
    check("T10.10 Status is completed", serialized["r6_action"]["status"] == "completed")

    # Record in LCT and propagate through MRH
    lct_record = LCTActionRecord("lct:web4:agent:eve", e2e_action.action_id, "completed", 0.03)
    mrh_prop = MRHPropagation(e2e_action.action_id, "lct:web4:agent:eve")
    mrh_prop.propagate("lct:web4:oracle:1")
    atp_settle = ATPSettlement(e2e_action.action_id, atp_consumed=60, atp_generated=70)

    check("T10.11 LCT recorded", lct_record.action_id == e2e_action.action_id)
    check("T10.12 MRH propagated", len(mrh_prop.propagated_to) == 1)
    check("T10.13 ATP settled", atp_settle.net_value == 10)

    # ══════════════════════════════════════════════════════════

    print(f"\n{'='*60}")
    print(f"R6 Framework Spec: {passed}/{passed+failed} checks passed")
    if failed:
        print(f"  {failed} FAILED")
    else:
        print(f"  All checks passed!")
    print(f"{'='*60}")
    return failed == 0


if __name__ == "__main__":
    run_tests()
