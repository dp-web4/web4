"""
Web4 Agentic Context Protocol (ACP)

Canonical implementation per web4-standard/core-spec/acp-framework.md.

ACP adds agentic capability to Web4, enabling entities to initiate
actions autonomously while maintaining safety, auditability, and
human oversight. ACP builds on MCP and integrates with AGY (Agency
Delegation) and SAL (Society-Authority-Law).

Key concepts:
- AgentPlan: multi-step workflow definition with triggers and guards
- Intent: proposed action with proof of agency
- Decision: human or automated approval/denial
- ExecutionRecord: immutable record of action execution
- State machine: Idle→Planning→IntentCreated→Approved→Executing→Recording→Complete

This module provides DATA STRUCTURES, state machine, and validation.
Actual MCP transport and ledger writes are out of scope.

Validated against: web4-standard/test-vectors/acp/plan-operations.json
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ── ACP Errors ──────────────────────────────────────────────────

class ACPError(Exception):
    """Base class for ACP errors."""
    error_code: str = "W4_ERR_ACP"


class NoValidGrant(ACPError):
    """No valid agency grant found."""
    error_code = "W4_ERR_ACP_NO_GRANT"


class ScopeViolation(ACPError):
    """Action outside grant scope."""
    error_code = "W4_ERR_ACP_SCOPE_VIOLATION"


class ApprovalRequired(ACPError):
    """Human approval needed but not provided."""
    error_code = "W4_ERR_ACP_APPROVAL_REQUIRED"


class WitnessDeficit(ACPError):
    """Insufficient witnesses for action."""
    error_code = "W4_ERR_ACP_WITNESS_DEFICIT"


class PlanExpired(ACPError):
    """Plan has expired."""
    error_code = "W4_ERR_ACP_PLAN_EXPIRED"


class LedgerWriteFailure(ACPError):
    """Failed to write to immutable ledger."""
    error_code = "W4_ERR_ACP_LEDGER_WRITE"


class InvalidTransition(ACPError):
    """Invalid state machine transition."""
    error_code = "W4_ERR_ACP_INVALID_TRANSITION"


class ResourceCapExceeded(ACPError):
    """Action exceeds resource caps."""
    error_code = "W4_ERR_ACP_RESOURCE_CAP_EXCEEDED"


# ── Enums ───────────────────────────────────────────────────────

class ACPState(str, Enum):
    """ACP lifecycle states (§3.2)."""
    IDLE = "idle"
    PLANNING = "planning"
    INTENT_CREATED = "intent_created"
    APPROVAL_GATE = "approval_gate"
    EXECUTING = "executing"
    RECORDING = "recording"
    COMPLETE = "complete"
    FAILED = "failed"


class TriggerKind(str, Enum):
    """Trigger types for agent plans (§2.1)."""
    CRON = "cron"
    EVENT = "event"
    MANUAL = "manual"


class DecisionType(str, Enum):
    """Decision outcomes (§2.3)."""
    APPROVE = "approve"
    DENY = "deny"
    MODIFY = "modify"


class ApprovalMode(str, Enum):
    """Approval gate modes."""
    AUTO = "auto"           # Always auto-approve
    MANUAL = "manual"       # Always require human
    CONDITIONAL = "conditional"  # Auto if within limits, manual otherwise


# ── Valid transitions ───────────────────────────────────────────

VALID_TRANSITIONS: Dict[ACPState, List[ACPState]] = {
    ACPState.IDLE: [ACPState.PLANNING],
    ACPState.PLANNING: [ACPState.INTENT_CREATED, ACPState.FAILED],
    ACPState.INTENT_CREATED: [ACPState.APPROVAL_GATE, ACPState.FAILED],
    ACPState.APPROVAL_GATE: [ACPState.EXECUTING, ACPState.FAILED],
    ACPState.EXECUTING: [ACPState.RECORDING, ACPState.FAILED],
    ACPState.RECORDING: [ACPState.COMPLETE, ACPState.FAILED],
    ACPState.COMPLETE: [ACPState.IDLE],  # Can restart
    ACPState.FAILED: [ACPState.IDLE],    # Can retry
}


# ── Trigger ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class Trigger:
    """
    A plan trigger (§2.1).

    Triggers define when a plan should be evaluated: on schedule (cron),
    on event, or on manual invocation.
    """
    kind: TriggerKind
    expr: str = ""           # cron expression or event topic
    authorized: List[str] = field(default_factory=list)  # for manual triggers


# ── Guards ──────────────────────────────────────────────────────

@dataclass
class ResourceCaps:
    """Resource caps for a plan (§2.1 guards)."""
    max_atp: float = 0.0
    max_executions: int = 0
    rate_limit: str = ""      # e.g. "10/hour"

    def check_atp(self, atp_amount: float) -> bool:
        """Check if ATP amount is within cap."""
        if self.max_atp <= 0:
            return True  # No cap
        return atp_amount <= self.max_atp

    def check_executions(self, count: int) -> bool:
        """Check if execution count is within cap."""
        if self.max_executions <= 0:
            return True  # No cap
        return count <= self.max_executions


@dataclass
class HumanApproval:
    """Human approval gate configuration (§2.1)."""
    mode: ApprovalMode = ApprovalMode.CONDITIONAL
    auto_threshold: float = 0.0   # Auto-approve if value <= threshold
    timeout: int = 3600           # Seconds to wait for human
    fallback: str = "deny"        # What to do on timeout: "deny" or "abort"

    def needs_human(self, value: float) -> bool:
        """Determine if human approval is needed based on value."""
        if self.mode == ApprovalMode.AUTO:
            return False
        if self.mode == ApprovalMode.MANUAL:
            return True
        # Conditional: auto if within threshold
        return value > self.auto_threshold


@dataclass
class Guards:
    """
    Plan guards — safety constraints (§2.1).

    Guards enforce resource caps, witness levels, law compliance,
    and human approval requirements.
    """
    law_hash: str = ""
    resource_caps: ResourceCaps = field(default_factory=ResourceCaps)
    witness_level: int = 0
    human_approval: HumanApproval = field(default_factory=HumanApproval)
    expires_at: str = ""

    def is_expired(self, now: Optional[str] = None) -> bool:
        """Check if the guards have expired."""
        if not self.expires_at:
            return False
        now_str = now or datetime.now(timezone.utc).isoformat()
        return now_str > self.expires_at

    def validate_witnesses(self, witness_count: int) -> bool:
        """Check if sufficient witnesses are available."""
        return witness_count >= self.witness_level


# ── Plan Step ───────────────────────────────────────────────────

@dataclass
class PlanStep:
    """
    A single step in an agent plan (§2.1).

    Steps reference MCP tools and declare dependencies for ordering.
    """
    step_id: str
    mcp_tool: str                       # e.g. "invoice.search"
    args: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    requires_approval: str = ""         # Condition string, e.g. "if_amount > 10"

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "id": self.step_id,
            "mcp": self.mcp_tool,
            "args": self.args,
        }
        if self.depends_on:
            d["dependsOn"] = self.depends_on
        if self.requires_approval:
            d["requiresApproval"] = self.requires_approval
        return d


# ── Agent Plan ──────────────────────────────────────────────────

@dataclass
class AgentPlan:
    """
    Declarative specification of agent workflow (§2.1).

    An AgentPlan defines triggers, steps, guards, and the principal-agent
    relationship. It is content-addressed via canonical hash.
    """
    plan_id: str
    principal: str                # LCT ID of the entity authorizing the plan
    agent: str                    # LCT ID of the entity executing the plan
    grant_id: str                 # AGY grant authorizing this plan
    triggers: List[Trigger] = field(default_factory=list)
    steps: List[PlanStep] = field(default_factory=list)
    guards: Guards = field(default_factory=Guards)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    @property
    def step_order(self) -> List[str]:
        """Topological order of steps based on dependencies."""
        ordered: List[str] = []
        visited: set = set()

        step_map = {s.step_id: s for s in self.steps}

        def visit(step_id: str):
            if step_id in visited:
                return
            visited.add(step_id)
            step = step_map.get(step_id)
            if step:
                for dep in step.depends_on:
                    visit(dep)
            ordered.append(step_id)

        for s in self.steps:
            visit(s.step_id)
        return ordered

    def get_step(self, step_id: str) -> Optional[PlanStep]:
        """Look up a step by ID."""
        return next((s for s in self.steps if s.step_id == step_id), None)

    def canonical_hash(self) -> str:
        """Content-addressed hash of the plan."""
        canonical = json.dumps({
            "planId": self.plan_id,
            "principal": self.principal,
            "agent": self.agent,
            "grantId": self.grant_id,
            "steps": [s.to_dict() for s in self.steps],
            "guards": {
                "lawHash": self.guards.law_hash,
                "witnessLevel": self.guards.witness_level,
                "resourceCaps": {
                    "maxAtp": self.guards.resource_caps.max_atp,
                    "maxExecutions": self.guards.resource_caps.max_executions,
                },
            },
        }, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "ACP.AgentPlan",
            "planId": self.plan_id,
            "principal": self.principal,
            "agent": self.agent,
            "grantId": self.grant_id,
            "triggers": [
                {"kind": t.kind.value, "expr": t.expr}
                for t in self.triggers
            ],
            "steps": [s.to_dict() for s in self.steps],
            "guards": {
                "lawHash": self.guards.law_hash,
                "witnessLevel": self.guards.witness_level,
                "resourceCaps": {
                    "maxAtp": self.guards.resource_caps.max_atp,
                    "maxExecutions": self.guards.resource_caps.max_executions,
                    "rateLimit": self.guards.resource_caps.rate_limit,
                },
                "humanApproval": {
                    "mode": self.guards.human_approval.mode.value,
                    "autoThreshold": self.guards.human_approval.auto_threshold,
                    "timeout": self.guards.human_approval.timeout,
                    "fallback": self.guards.human_approval.fallback,
                },
                "expiresAt": self.guards.expires_at,
            },
            "createdAt": self.created_at,
        }


# ── Proof of Agency ─────────────────────────────────────────────

@dataclass(frozen=True)
class ProofOfAgency:
    """
    Proof that an agent has authority to act (§4.2).

    Links intent to grant, plan, and provides cryptographic proof.
    """
    grant_id: str
    plan_id: str
    intent_id: str
    nonce: str = ""
    audience: List[str] = field(default_factory=list)
    expires_at: str = ""

    def __post_init__(self):
        if not self.nonce:
            object.__setattr__(self, "nonce", uuid.uuid4().hex[:16])


# ── Intent ──────────────────────────────────────────────────────

@dataclass
class Intent:
    """
    An actionable proposal generated from plan evaluation (§2.2).

    Intents are the bridge between planning and execution.
    They carry proof of agency and explain reasoning.
    """
    intent_id: str
    plan_id: str
    step_id: str
    proposed_action: Dict[str, Any]     # {"mcp": "tool.name", "args": {...}}
    proof: ProofOfAgency
    explanation: str = ""
    confidence: float = 0.0
    risk_assessment: str = "low"
    needs_approval: bool = False
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "ACP.Intent",
            "intentId": self.intent_id,
            "planId": self.plan_id,
            "stepId": self.step_id,
            "proposedAction": self.proposed_action,
            "proofOfAgency": {
                "grantId": self.proof.grant_id,
                "planId": self.proof.plan_id,
                "intentId": self.proof.intent_id,
                "nonce": self.proof.nonce,
            },
            "explain": {
                "why": self.explanation,
                "confidence": self.confidence,
                "riskAssessment": self.risk_assessment,
            },
            "needsApproval": self.needs_approval,
            "createdAt": self.created_at,
        }


# ── Decision ────────────────────────────────────────────────────

@dataclass
class Decision:
    """
    Human or automated decision on an intent (§2.3).
    """
    intent_id: str
    decision: DecisionType
    decided_by: str               # LCT ID of decision maker
    rationale: str = ""
    modifications: Optional[Dict[str, Any]] = None
    witnesses: List[str] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    @property
    def approved(self) -> bool:
        return self.decision == DecisionType.APPROVE

    @property
    def denied(self) -> bool:
        return self.decision == DecisionType.DENY

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "type": "ACP.Decision",
            "intentId": self.intent_id,
            "decision": self.decision.value,
            "by": self.decided_by,
            "rationale": self.rationale,
            "witnesses": self.witnesses,
            "timestamp": self.timestamp,
        }
        if self.modifications:
            d["modifications"] = self.modifications
        return d


# ── Execution Record ────────────────────────────────────────────

@dataclass
class ExecutionRecord:
    """
    Immutable record of action execution (§2.4).

    Captures what was done, by whom, the result, and trust deltas.
    """
    record_id: str
    intent_id: str
    grant_id: str
    law_hash: str
    mcp_call: Dict[str, Any]           # {"resource": "...", "args": {...}}
    result_status: str = "success"     # "success" or "failure"
    result_output: Dict[str, Any] = field(default_factory=dict)
    resources_consumed: Dict[str, float] = field(default_factory=dict)
    t3v3_delta: Dict[str, Any] = field(default_factory=dict)
    witnesses: List[str] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    @property
    def success(self) -> bool:
        return self.result_status == "success"

    def canonical_hash(self) -> str:
        """Content-addressed hash for ledger inclusion."""
        canonical = json.dumps({
            "recordId": self.record_id,
            "intentId": self.intent_id,
            "grantId": self.grant_id,
            "lawHash": self.law_hash,
            "mcpCall": self.mcp_call,
            "resultStatus": self.result_status,
            "timestamp": self.timestamp,
        }, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "ACP.ExecutionRecord",
            "recordId": self.record_id,
            "intentId": self.intent_id,
            "grantId": self.grant_id,
            "lawHash": self.law_hash,
            "mcpCall": self.mcp_call,
            "result": {
                "status": self.result_status,
                "output": self.result_output,
                "resourcesConsumed": self.resources_consumed,
            },
            "t3v3Delta": self.t3v3_delta,
            "witnesses": self.witnesses,
            "timestamp": self.timestamp,
        }


# ── ACP State Machine ──────────────────────────────────────────

class ACPStateMachine:
    """
    ACP lifecycle state machine (§3).

    Tracks state transitions for a single plan execution cycle.
    Validates transitions against the allowed state graph.
    Maintains an audit trail of all transitions.
    """

    def __init__(self, plan: AgentPlan):
        self.plan = plan
        self.state = ACPState.IDLE
        self.intent: Optional[Intent] = None
        self.decision: Optional[Decision] = None
        self.record: Optional[ExecutionRecord] = None
        self.error: Optional[str] = None
        self._history: List[Dict[str, Any]] = []
        self._log_transition(ACPState.IDLE, "initialized")

    def _log_transition(self, to_state: ACPState, reason: str):
        self._history.append({
            "from": self.state.value if self._history else None,
            "to": to_state.value,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def _transition(self, to_state: ACPState, reason: str = ""):
        """Validate and execute a state transition."""
        if to_state not in VALID_TRANSITIONS.get(self.state, []):
            raise InvalidTransition(
                f"Cannot transition from {self.state.value} to {to_state.value}"
            )
        self._log_transition(to_state, reason)
        self.state = to_state

    @property
    def history(self) -> List[Dict[str, Any]]:
        return list(self._history)

    def start_planning(self):
        """Trigger fires → begin planning."""
        if self.plan.guards.is_expired():
            self._transition(ACPState.PLANNING, "trigger fired")
            self.fail("Plan expired")
            raise PlanExpired(f"Plan {self.plan.plan_id} has expired")
        self._transition(ACPState.PLANNING, "trigger fired")

    def create_intent(self, intent: Intent):
        """Plan evaluated → intent created."""
        # Validate resource caps
        atp_requested = intent.proposed_action.get("args", {}).get("atp", 0)
        if not self.plan.guards.resource_caps.check_atp(atp_requested):
            self.fail(f"ATP cap exceeded: {atp_requested}")
            raise ResourceCapExceeded(
                f"ATP {atp_requested} exceeds cap {self.plan.guards.resource_caps.max_atp}"
            )

        self.intent = intent
        self._transition(ACPState.INTENT_CREATED, f"intent {intent.intent_id}")

    def enter_approval_gate(self):
        """Law check passes → approval gate."""
        if self.intent is None:
            self.fail("No intent to approve")
            raise InvalidTransition("No intent created")
        self._transition(ACPState.APPROVAL_GATE, "law check passed")

    def approve(self, decision: Decision):
        """Decision made at approval gate."""
        self.decision = decision
        if decision.denied:
            self.fail(f"Denied: {decision.rationale}")
            return
        if decision.decision == DecisionType.MODIFY and decision.modifications:
            # Apply modifications to intent
            if self.intent:
                self.intent.proposed_action.update(decision.modifications)
        self._transition(ACPState.EXECUTING, f"approved by {decision.decided_by}")

    def record_execution(self, record: ExecutionRecord):
        """Execution complete → record result."""
        self.record = record
        self._transition(ACPState.RECORDING, f"record {record.record_id}")

    def complete(self):
        """Recording done → complete."""
        self._transition(ACPState.COMPLETE, "execution recorded and witnessed")

    def fail(self, reason: str):
        """Transition to failed state from any active state."""
        self.error = reason
        if ACPState.FAILED in VALID_TRANSITIONS.get(self.state, []):
            self._log_transition(ACPState.FAILED, reason)
            self.state = ACPState.FAILED

    def reset(self):
        """Reset to idle for re-execution."""
        if self.state in (ACPState.COMPLETE, ACPState.FAILED):
            self._transition(ACPState.IDLE, "reset")
            self.intent = None
            self.decision = None
            self.record = None
            self.error = None


# ── Plan Validation ─────────────────────────────────────────────

def validate_plan(plan: AgentPlan) -> List[str]:
    """
    Validate an agent plan structure.

    Returns a list of validation errors (empty = valid).
    """
    errors: List[str] = []

    if not plan.plan_id:
        errors.append("Plan must have a plan_id")
    if not plan.principal:
        errors.append("Plan must have a principal")
    if not plan.agent:
        errors.append("Plan must have an agent")
    if not plan.grant_id:
        errors.append("Plan must have a grant_id")
    if not plan.steps:
        errors.append("Plan must have at least one step")

    # Validate step dependencies
    step_ids = {s.step_id for s in plan.steps}
    for step in plan.steps:
        for dep in step.depends_on:
            if dep not in step_ids:
                errors.append(f"Step {step.step_id} depends on unknown step {dep}")

    # Check for dependency cycles
    if plan.steps and _has_cycle(plan.steps):
        errors.append("Plan steps contain a dependency cycle")

    return errors


def _has_cycle(steps: List[PlanStep]) -> bool:
    """Detect cycles in step dependencies via DFS."""
    step_map = {s.step_id: s for s in steps}
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {s.step_id: WHITE for s in steps}

    def dfs(sid: str) -> bool:
        color[sid] = GRAY
        step = step_map.get(sid)
        if step:
            for dep in step.depends_on:
                if dep in color:
                    if color[dep] == GRAY:
                        return True
                    if color[dep] == WHITE and dfs(dep):
                        return True
        color[sid] = BLACK
        return False

    for s in steps:
        if color[s.step_id] == WHITE:
            if dfs(s.step_id):
                return True
    return False


# ── Intent Builder ──────────────────────────────────────────────

def build_intent(
    plan: AgentPlan,
    step_id: str,
    args: Optional[Dict[str, Any]] = None,
    explanation: str = "",
    confidence: float = 0.5,
) -> Intent:
    """
    Convenience function to build an Intent from a plan step.

    Creates the proof of agency automatically from the plan.
    """
    step = plan.get_step(step_id)
    if step is None:
        raise ValueError(f"Step {step_id} not found in plan {plan.plan_id}")

    intent_id = f"acp:intent:{uuid.uuid4().hex[:12]}"

    merged_args = dict(step.args)
    if args:
        merged_args.update(args)

    proof = ProofOfAgency(
        grant_id=plan.grant_id,
        plan_id=plan.plan_id,
        intent_id=intent_id,
    )

    # Determine if human approval is needed
    needs_approval = bool(step.requires_approval)
    if not needs_approval:
        # Check guards
        atp_amount = merged_args.get("atp", 0)
        if isinstance(atp_amount, (int, float)):
            needs_approval = plan.guards.human_approval.needs_human(atp_amount)

    return Intent(
        intent_id=intent_id,
        plan_id=plan.plan_id,
        step_id=step_id,
        proposed_action={"mcp": step.mcp_tool, "args": merged_args},
        proof=proof,
        explanation=explanation,
        confidence=confidence,
        needs_approval=needs_approval,
    )
