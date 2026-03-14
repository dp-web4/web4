"""
Web4 R6 Action Framework

Canonical implementation per web4-standard/protocols/web4-r6-framework.md.

R6 = Rules + Role + Request + Reference + Resource → Result

Every entity interaction in Web4 can be expressed as an R6 action — a
structured lifecycle that transforms intent into accountable output with
full T3/V3 tensor evolution and ATP energy accounting.

Key lifecycle: pending → executing → completed | failed
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from .trust import T3, V3, _clamp
from .lct import LCT
from .atp import ATPAccount


# ── Action Status ────────────────────────────────────────────────

class ActionStatus(str, Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class ActionType(str, Enum):
    ANALYZE = "analyze"
    COMPUTE = "compute"
    VERIFY = "verify"
    DELEGATE = "delegate"
    TRANSFER = "transfer"
    ATTEST = "attest"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ── R6 Component Data Types ─────────────────────────────────────

@dataclass
class Rules:
    """Governing constraints for an action (§2.1)."""
    permission_scope: List[str] = field(default_factory=list)
    max_atp_spend: float = 0.0
    timeout_seconds: int = 3600
    quality_threshold: float = 0.0
    governing_contracts: List[str] = field(default_factory=list)

    def permits(self, permission: str) -> bool:
        """Check if a permission is in scope."""
        return permission in self.permission_scope


@dataclass
class Role:
    """Operational identity for the action (§2.2)."""
    role_lct_id: str
    role_context: str
    delegated_permissions: List[str] = field(default_factory=list)
    t3_snapshot: Optional[T3] = None

    def has_permission(self, permission: str) -> bool:
        return permission in self.delegated_permissions


@dataclass
class Request:
    """The intent — what the entity wants to achieve (§2.3)."""
    action_type: ActionType
    description: str
    acceptance_criteria: List[str] = field(default_factory=list)
    priority: Priority = Priority.MEDIUM
    deadline: Optional[str] = None


@dataclass
class Reference:
    """Historical context from past interactions (§2.4)."""
    similar_actions: List[str] = field(default_factory=list)
    average_confidence: float = 0.0
    relevant_memory: List[str] = field(default_factory=list)
    mrh_depth: int = 0


@dataclass
class Resource:
    """Energy and assets for the action (§2.5)."""
    atp_allocated: float = 0.0
    atp_consumed: float = 0.0
    compute_units: int = 0
    data_access: List[str] = field(default_factory=list)
    estimated_atp: float = 0.0


@dataclass
class WitnessAttestation:
    """An external witness's attestation of the result (§2.6)."""
    witness_lct_id: str
    attestation_type: str  # "quality", "completion", "accuracy"
    score: float = 1.0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class Result:
    """The outcome of an R6 action (§2.6)."""
    output: str = ""
    quality_score: float = 0.0
    criteria_met: List[str] = field(default_factory=list)
    v3_assessment: Optional[V3] = None
    atp_earned: float = 0.0
    side_effects: List[str] = field(default_factory=list)
    witness_attestations: List[WitnessAttestation] = field(default_factory=list)


# ── Confidence Calculation ───────────────────────────────────────

# Per spec §3.2: weighted average of four factors
CONFIDENCE_WEIGHTS = {
    "role_capability": 0.3,
    "historical_success": 0.25,
    "resource_availability": 0.25,
    "risk_assessment": 0.2,
}


@dataclass
class ConfidenceAssessment:
    """Pre-execution confidence calculation (§3.2)."""
    role_capability: float = 0.5
    historical_success: float = 0.5
    resource_availability: float = 1.0
    risk_assessment: float = 0.5

    @property
    def overall(self) -> float:
        """Weighted average confidence."""
        return (
            self.role_capability * CONFIDENCE_WEIGHTS["role_capability"]
            + self.historical_success * CONFIDENCE_WEIGHTS["historical_success"]
            + self.resource_availability * CONFIDENCE_WEIGHTS["resource_availability"]
            + self.risk_assessment * CONFIDENCE_WEIGHTS["risk_assessment"]
        )


def assess_confidence(
    role: Role,
    reference: Reference,
    resource: Resource,
    rules: Rules,
) -> ConfidenceAssessment:
    """
    Calculate confidence from R6 components (§3.2).

    - role_capability: from T3 composite (or 0.5 default)
    - historical_success: from reference average confidence
    - resource_availability: 1.0 if allocated >= estimated, else ratio
    - risk_assessment: from quality threshold (lower threshold = less risk)
    """
    # Role capability from T3 snapshot
    role_cap = role.t3_snapshot.composite if role.t3_snapshot else 0.5

    # Historical success from reference
    hist = reference.average_confidence if reference.average_confidence > 0 else 0.5

    # Resource availability
    if resource.estimated_atp > 0:
        res_avail = min(1.0, resource.atp_allocated / resource.estimated_atp)
    else:
        res_avail = 1.0

    # Risk: inverse of quality threshold (high threshold = more risk of failure)
    risk = 1.0 - rules.quality_threshold * 0.5

    return ConfidenceAssessment(
        role_capability=role_cap,
        historical_success=hist,
        resource_availability=res_avail,
        risk_assessment=risk,
    )


# ── T3/V3 Evolution from Results ────────────────────────────────

def evolve_t3(t3: T3, result: Result, success: bool) -> T3:
    """
    Update T3 tensor from action result (§4.1).

    Uses the existing T3.update() method with the result's quality score.
    """
    return t3.update(quality=result.quality_score, success=success)


def evolve_v3(result: Result) -> V3:
    """
    Extract V3 assessment from result (§4.2).

    If result has explicit v3_assessment, use it.
    Otherwise derive from quality_score and attestations.
    """
    if result.v3_assessment:
        return result.v3_assessment

    q = result.quality_score
    # Derive: valuation from quality, veracity from attestation count,
    # validity from whether any attestation exists
    attest_count = len(result.witness_attestations)
    veracity = min(1.0, 0.5 + attest_count * 0.15) if attest_count else q * 0.8
    validity = 1.0 if attest_count > 0 else (0.8 if q >= 0.5 else 0.3)

    return V3(valuation=q, veracity=veracity, validity=validity)


# ── R6 Action ────────────────────────────────────────────────────

@dataclass
class R6Action:
    """
    A complete R6 action with lifecycle management.

    Usage:
        action = R6Action.create(
            initiator_lct_id="lct:web4:agent:alice",
            rules=Rules(permission_scope=["read:data"], max_atp_spend=50),
            role=Role("lct:web4:role:analyst", "data-analyst", ["analyze"]),
            request=Request(ActionType.ANALYZE, "Analyze dataset"),
        )
        action.begin(account)       # locks ATP, status → executing
        action.complete(result)     # settles ATP, evolves tensors
    """
    action_id: str
    initiator_lct_id: str
    status: ActionStatus
    timestamp: str
    rules: Rules
    role: Role
    request: Request
    reference: Reference
    resource: Resource
    result: Optional[Result] = None
    confidence: Optional[ConfidenceAssessment] = None

    @classmethod
    def create(
        cls,
        initiator_lct_id: str,
        rules: Rules,
        role: Role,
        request: Request,
        reference: Optional[Reference] = None,
        resource: Optional[Resource] = None,
    ) -> R6Action:
        """Create a new pending R6 action."""
        ts = datetime.now(timezone.utc).isoformat()
        # Deterministic action ID from components
        id_source = f"{initiator_lct_id}:{role.role_context}:{request.description}:{ts}"
        action_id = "r6:web4:" + hashlib.sha256(id_source.encode()).hexdigest()[:16]

        ref = reference or Reference()
        res = resource or Resource(atp_allocated=rules.max_atp_spend,
                                    estimated_atp=rules.max_atp_spend)

        action = cls(
            action_id=action_id,
            initiator_lct_id=initiator_lct_id,
            status=ActionStatus.PENDING,
            timestamp=ts,
            rules=rules,
            role=role,
            request=request,
            reference=ref,
            resource=res,
        )
        # Calculate pre-execution confidence
        action.confidence = assess_confidence(role, ref, res, rules)
        return action

    def begin(self, account: Optional[ATPAccount] = None) -> bool:
        """
        Begin execution (§5.1-5.2).

        Locks ATP if account provided. Transitions pending → executing.
        Returns False if ATP lock fails or if not in pending state.
        """
        if self.status != ActionStatus.PENDING:
            return False

        if account and self.resource.atp_allocated > 0:
            if not account.lock(self.resource.atp_allocated):
                return False

        self.status = ActionStatus.EXECUTING
        return True

    def complete(
        self,
        result: Result,
        account: Optional[ATPAccount] = None,
    ) -> bool:
        """
        Complete the action with a result (§5.3).

        Commits ATP, records result. Transitions executing → completed.
        Returns False if not in executing state.
        """
        if self.status != ActionStatus.EXECUTING:
            return False

        self.result = result
        self.status = ActionStatus.COMPLETED

        # ATP settlement: commit consumed, rollback remainder
        if account:
            consumed = min(self.resource.atp_allocated, self.resource.atp_allocated)
            # Use quality-based consumption: low quality = less consumed
            actual_consumed = consumed * max(0.1, result.quality_score)
            self.resource.atp_consumed = actual_consumed
            account.commit(actual_consumed)
            # Rollback unused
            remainder = self.resource.atp_allocated - actual_consumed
            if remainder > 0:
                account.rollback(remainder)

        return True

    def fail(
        self,
        reason: str,
        account: Optional[ATPAccount] = None,
    ) -> bool:
        """
        Fail the action (§5.3 failure path).

        Rolls back all locked ATP. Transitions executing → failed.
        """
        if self.status != ActionStatus.EXECUTING:
            return False

        self.result = Result(output=reason, quality_score=0.0)
        self.status = ActionStatus.FAILED

        # Rollback all locked ATP on failure
        if account and self.resource.atp_allocated > 0:
            account.rollback(self.resource.atp_allocated)

        return True

    def evolve_tensors(self) -> tuple[Optional[T3], Optional[V3]]:
        """
        Calculate T3/V3 evolution from this action's result (§4).

        Returns (new_t3, new_v3) or (None, None) if not completed.
        """
        if self.status != ActionStatus.COMPLETED or self.result is None:
            return None, None

        t3_base = self.role.t3_snapshot or T3()
        new_t3 = evolve_t3(t3_base, self.result, success=True)
        new_v3 = evolve_v3(self.result)
        return new_t3, new_v3

    def check_permission(self, permission: str) -> bool:
        """Check if action has a specific permission via both rules and role."""
        return self.rules.permits(permission) and self.role.has_permission(permission)

    def meets_quality_threshold(self) -> bool:
        """Check if result meets the quality threshold from rules."""
        if self.result is None:
            return False
        return self.result.quality_score >= self.rules.quality_threshold

    def to_reference(self) -> Reference:
        """Convert completed action to a Reference for future actions (§2.6)."""
        conf = self.confidence.overall if self.confidence else 0.0
        return Reference(
            similar_actions=[self.action_id],
            average_confidence=conf,
        )

    def as_dict(self) -> dict:
        """Serialize to spec-compatible dict (§3.1)."""
        d = {
            "r6_action": {
                "action_id": self.action_id,
                "timestamp": self.timestamp,
                "initiator_lct": self.initiator_lct_id,
                "status": self.status.value,
                "rules": {
                    "governing_contracts": self.rules.governing_contracts,
                    "permission_scope": self.rules.permission_scope,
                    "constraints": {
                        "max_atp_spend": self.rules.max_atp_spend,
                        "timeout_seconds": self.rules.timeout_seconds,
                        "quality_threshold": self.rules.quality_threshold,
                    },
                },
                "role": {
                    "role_lct": self.role.role_lct_id,
                    "role_context": self.role.role_context,
                    "delegated_permissions": self.role.delegated_permissions,
                },
                "request": {
                    "action_type": self.request.action_type.value,
                    "description": self.request.description,
                    "priority": self.request.priority.value,
                },
                "resource": {
                    "atp_allocated": self.resource.atp_allocated,
                    "atp_consumed": self.resource.atp_consumed,
                },
            }
        }
        if self.role.t3_snapshot:
            d["r6_action"]["role"]["t3_snapshot"] = self.role.t3_snapshot.as_dict()
        if self.result:
            d["r6_action"]["result"] = {
                "output": self.result.output,
                "quality_score": self.result.quality_score,
                "criteria_met": self.result.criteria_met,
                "atp_earned": self.result.atp_earned,
            }
            if self.result.v3_assessment:
                d["r6_action"]["result"]["v3_assessment"] = self.result.v3_assessment.as_dict()
        if self.confidence:
            d["r6_action"]["confidence"] = {
                "role_capability": self.confidence.role_capability,
                "historical_success": self.confidence.historical_success,
                "resource_availability": self.confidence.resource_availability,
                "risk_assessment": self.confidence.risk_assessment,
                "overall": self.confidence.overall,
            }
        return d
