#!/usr/bin/env python3
"""
ACP (Agentic Context Protocol) — Reference Implementation
============================================================

Implements the ACP spec: Trigger → Plan → Intent → Law Check →
Approval Gate → Execute → Record & Witness → Post-Audit

ACP is the agentic layer above R7 and Hardbound. It enables entities to:
- Define multi-step plans with triggers and dependencies
- Generate intents (proposed actions) from plans
- Route through approval gates (auto or human)
- Execute via R7 actions through Hardbound governance
- Record full execution traces with witnesses

The key ACP innovation: agents don't just execute — they PLAN, PROPOSE,
and EXPLAIN. Every action carries proof of agency, law compliance, and
an explanation of why this action was chosen.

Integration stack:
    ACP (this file) → R7 (action semantics) → Hardbound (governance) → Ledger

Date: 2026-02-21
Spec: web4-standard/core-spec/acp-framework.md
"""

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
# ACP Error Hierarchy (from spec §10)
# ═══════════════════════════════════════════════════════════════

class ACPError(Exception):
    """Base class for ACP errors."""
    pass

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
    """Failed to write execution record."""
    error_code = "W4_ERR_ACP_LEDGER_WRITE"

class GuardViolation(ACPError):
    """Plan guard check failed."""
    error_code = "W4_ERR_ACP_GUARD_VIOLATION"

class StepDependencyFailed(ACPError):
    """Required dependency step failed."""
    error_code = "W4_ERR_ACP_STEP_DEP_FAILED"


# ═══════════════════════════════════════════════════════════════
# ACP State Machine (from spec §3)
# ═══════════════════════════════════════════════════════════════

class ACPState(Enum):
    """ACP lifecycle states."""
    IDLE = "idle"
    PLANNING = "planning"
    INTENT_CREATED = "intent_created"
    LAW_CHECK = "law_check"
    APPROVAL_GATE = "approval_gate"
    EXECUTING = "executing"
    RECORDING = "recording"
    COMPLETE = "complete"
    FAILED = "failed"
    REJECTED = "rejected"
    ABORTED = "aborted"


class TriggerKind(Enum):
    """Types of plan triggers."""
    MANUAL = "manual"
    EVENT = "event"
    CRON = "cron"
    CONDITION = "condition"


class ApprovalMode(Enum):
    """How approval is determined."""
    AUTO = "auto"              # Always auto-approve within limits
    MANUAL = "manual"          # Always require human approval
    CONDITIONAL = "conditional"  # Auto if condition met, else manual
    DELEGATED = "delegated"    # Delegate to another entity


class DecisionType(Enum):
    """Types of approval decisions."""
    APPROVE = "approve"
    DENY = "deny"
    MODIFY = "modify"


# ═══════════════════════════════════════════════════════════════
# ACP Data Structures (from spec §2)
# ═══════════════════════════════════════════════════════════════

@dataclass
class Trigger:
    """What activates a plan."""
    kind: TriggerKind
    config: Dict[str, Any] = field(default_factory=dict)
    authorized: List[str] = field(default_factory=list)

    def matches(self, event: Dict[str, Any]) -> bool:
        """Check if this trigger matches an event."""
        if self.kind == TriggerKind.MANUAL:
            return event.get("kind") == "manual" and (
                not self.authorized or event.get("by") in self.authorized
            )
        elif self.kind == TriggerKind.EVENT:
            return event.get("topic") == self.config.get("topic")
        elif self.kind == TriggerKind.CONDITION:
            # Conditions evaluated externally
            return event.get("condition_met", False)
        return False


@dataclass
class PlanStep:
    """A single step in an agent plan."""
    id: str
    action: str               # MCP tool name or action identifier
    args: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    requires_approval: Optional[str] = None  # Condition for requiring approval
    atp_cost: float = 10.0    # Estimated ATP cost
    timeout: float = 300.0    # Max execution time (seconds)
    on_failure: str = "abort"  # abort | skip | retry


@dataclass
class ResourceCaps:
    """Resource limits for a plan."""
    max_atp: float = 100.0
    max_executions: int = 100
    rate_limit: str = "10/hour"
    max_concurrent: int = 1

    def check(self, consumed_atp: float, execution_count: int) -> bool:
        """Check if resource caps would be exceeded."""
        return consumed_atp < self.max_atp and execution_count < self.max_executions


@dataclass
class Guards:
    """Safety guards for a plan."""
    law_hash: Optional[str] = None
    resource_caps: ResourceCaps = field(default_factory=ResourceCaps)
    witness_level: int = 1
    approval_mode: ApprovalMode = ApprovalMode.AUTO
    approval_threshold: Optional[float] = None  # Auto if value below this
    approval_timeout: float = 3600.0
    approval_fallback: str = "deny"

    def requires_manual_approval(self, step: PlanStep, context: Dict) -> bool:
        """Determine if a step needs manual approval."""
        if self.approval_mode == ApprovalMode.MANUAL:
            return True
        if self.approval_mode == ApprovalMode.AUTO:
            return False
        if self.approval_mode == ApprovalMode.CONDITIONAL:
            if step.requires_approval and self.approval_threshold is not None:
                value = context.get("value", 0)
                return value > self.approval_threshold
        return False


@dataclass
class AgencyGrant:
    """Proof of delegated agency (from AGY spec)."""
    grant_id: str
    principal_lct: str         # Who delegates
    agent_lct: str             # Who receives
    scope: List[str]           # Allowed actions
    resource_caps: ResourceCaps = field(default_factory=ResourceCaps)
    witness_level: int = 1
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    revoked: bool = False

    def is_valid(self) -> bool:
        if self.revoked:
            return False
        now = datetime.now(timezone.utc).isoformat()
        if self.valid_until and now > self.valid_until:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        return True

    def allows_action(self, action: str) -> bool:
        """Check if action is within grant scope."""
        if "*" in self.scope:
            return True
        for s in self.scope:
            if s.endswith("*") and action.startswith(s[:-1]):
                return True
            if action == s:
                return True
        return False


@dataclass
class AgentPlan:
    """A declarative specification of what an agent intends to accomplish."""
    plan_id: str
    name: str
    principal_lct: str         # Who the plan serves
    agent_lct: str             # Who executes
    grant_id: str              # Agency grant backing this plan
    triggers: List[Trigger] = field(default_factory=list)
    steps: List[PlanStep] = field(default_factory=list)
    guards: Guards = field(default_factory=Guards)
    expires_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc).isoformat() > self.expires_at

    def get_step(self, step_id: str) -> Optional[PlanStep]:
        for s in self.steps:
            if s.id == step_id:
                return s
        return None

    def get_ready_steps(self, completed: set) -> List[PlanStep]:
        """Get steps whose dependencies are all satisfied."""
        ready = []
        for s in self.steps:
            if s.id in completed:
                continue
            if all(d in completed for d in s.depends_on):
                ready.append(s)
        return ready


@dataclass
class Explanation:
    """Human-readable explanation of why an action was proposed."""
    why: str
    confidence: float = 0.0
    alternatives: List[str] = field(default_factory=list)
    risk_assessment: str = "low"


@dataclass
class Intent:
    """An actionable proposal generated from plan evaluation."""
    intent_id: str
    plan_id: str
    step_id: str
    proposed_action: str
    proposed_args: Dict[str, Any] = field(default_factory=dict)
    proof_of_agency: Dict[str, Any] = field(default_factory=dict)
    explanation: Explanation = field(default_factory=lambda: Explanation(why=""))
    needs_approval: bool = False
    atp_cost: float = 10.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    state: ACPState = ACPState.INTENT_CREATED


@dataclass
class Decision:
    """Human or automated decision on an intent."""
    intent_id: str
    decision: DecisionType
    by: str                     # LCT of decision-maker
    rationale: str = ""
    modifications: Optional[Dict[str, Any]] = None
    witnesses: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ExecutionRecord:
    """Immutable record of an executed action."""
    record_id: str
    intent_id: str
    plan_id: str
    step_id: str
    agent_lct: str
    action: str
    args: Dict[str, Any]
    result_status: str        # success | failure | error
    result_output: Any = None
    atp_consumed: float = 0.0
    t3v3_delta: Dict[str, Any] = field(default_factory=dict)
    witnesses: List[str] = field(default_factory=list)
    governance_trace: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    hash: str = ""

    def compute_hash(self, prev_hash: str = "") -> str:
        data = json.dumps({
            "record_id": self.record_id,
            "intent_id": self.intent_id,
            "plan_id": self.plan_id,
            "action": self.action,
            "result_status": self.result_status,
            "atp_consumed": self.atp_consumed,
            "prev_hash": prev_hash,
        }, sort_keys=True)
        self.hash = hashlib.sha256(data.encode()).hexdigest()
        return self.hash


# ═══════════════════════════════════════════════════════════════
# ACP Executor — The Engine
# ═══════════════════════════════════════════════════════════════

class ACPExecutor:
    """
    Executes agent plans through the ACP lifecycle.

    Lifecycle: Trigger → Plan → Intent → Law Check → Approval →
               Execute → Record → Post-Audit

    The executor manages:
    - Plan registration and validation
    - Grant verification (AGY integration)
    - Law compliance checks (SAL integration)
    - Approval routing (auto or manual)
    - Action execution (delegates to action_handler)
    - Execution recording (hash-chained)
    - Witness collection
    """

    def __init__(
        self,
        action_handler: Callable[[str, Dict], Tuple[str, Any]],
        law_checker: Optional[Callable[[AgentPlan, Intent], bool]] = None,
        witness_provider: Optional[Callable[[str], List[str]]] = None,
    ):
        """
        Args:
            action_handler: fn(action_name, args) -> (status, output)
            law_checker: fn(plan, intent) -> bool (raises on violation)
            witness_provider: fn(intent_id) -> list of witness LCTs
        """
        self.action_handler = action_handler
        self.law_checker = law_checker or self._default_law_check
        self.witness_provider = witness_provider or self._default_witnesses

        # Registries
        self.plans: Dict[str, AgentPlan] = {}
        self.grants: Dict[str, AgencyGrant] = {}
        self.intents: Dict[str, Intent] = {}
        self.decisions: Dict[str, Decision] = {}
        self.records: List[ExecutionRecord] = []

        # State tracking per plan
        self.plan_executions: Dict[str, int] = {}      # plan_id -> execution count
        self.plan_atp_consumed: Dict[str, float] = {}  # plan_id -> total ATP used

        # Auto-approver registry
        self.auto_approvers: Dict[str, Callable[[Intent], DecisionType]] = {}

    def register_grant(self, grant: AgencyGrant):
        """Register an agency grant."""
        self.grants[grant.grant_id] = grant

    def register_plan(self, plan: AgentPlan) -> str:
        """Register and validate a plan."""
        # Validate grant exists
        if plan.grant_id not in self.grants:
            raise NoValidGrant(f"Grant {plan.grant_id} not registered")

        grant = self.grants[plan.grant_id]
        if not grant.is_valid():
            raise NoValidGrant(f"Grant {plan.grant_id} is expired/revoked")

        # Validate all steps are within grant scope
        for step in plan.steps:
            if not grant.allows_action(step.action):
                raise ScopeViolation(
                    f"Step '{step.id}' action '{step.action}' not in grant scope"
                )

        self.plans[plan.plan_id] = plan
        self.plan_executions[plan.plan_id] = 0
        self.plan_atp_consumed[plan.plan_id] = 0.0
        return plan.plan_id

    def register_auto_approver(
        self,
        name: str,
        approver: Callable[[Intent], DecisionType],
    ):
        """Register an auto-approval function."""
        self.auto_approvers[name] = approver

    # ── Trigger Phase ──

    def trigger_plan(
        self,
        plan_id: str,
        event: Dict[str, Any],
    ) -> List[ExecutionRecord]:
        """
        Trigger a plan and execute all ready steps.

        Returns list of execution records for all steps executed.
        """
        if plan_id not in self.plans:
            raise ACPError(f"Plan {plan_id} not registered")

        plan = self.plans[plan_id]

        # Check expiry
        if plan.is_expired():
            raise PlanExpired(f"Plan {plan.name} has expired")

        # Check resource caps
        if not plan.guards.resource_caps.check(
            self.plan_atp_consumed.get(plan_id, 0),
            self.plan_executions.get(plan_id, 0),
        ):
            raise GuardViolation("Plan resource caps exceeded")

        # Verify trigger matches
        trigger_matched = any(t.matches(event) for t in plan.triggers)
        if not trigger_matched:
            raise ACPError("No trigger matches event")

        # Execute plan steps in dependency order
        completed = set()
        failed = set()
        all_records = []

        while True:
            ready = plan.get_ready_steps(completed | failed)
            if not ready:
                break

            for step in ready:
                # Check if dependencies all succeeded (not just completed)
                dep_failed = any(d in failed for d in step.depends_on)
                if dep_failed:
                    if step.on_failure == "skip":
                        completed.add(step.id)
                        continue
                    elif step.on_failure == "abort":
                        failed.add(step.id)
                        continue
                    # retry handled externally

                try:
                    record = self._execute_step(plan, step, event)
                    all_records.append(record)

                    if record.result_status == "success":
                        completed.add(step.id)
                    else:
                        if step.on_failure == "abort":
                            failed.add(step.id)
                        else:
                            completed.add(step.id)  # skip treats failure as done

                except ApprovalRequired:
                    # Step needs manual approval — mark as needing intervention
                    failed.add(step.id)
                    # Create a pending intent for manual resolution
                    intent = self._create_intent(plan, step, event)
                    intent.needs_approval = True
                    self.intents[intent.intent_id] = intent

                except ACPError as e:
                    failed.add(step.id)
                    # Record the failure
                    record = ExecutionRecord(
                        record_id=f"rec:{uuid.uuid4().hex[:12]}",
                        intent_id="",
                        plan_id=plan.plan_id,
                        step_id=step.id,
                        agent_lct=plan.agent_lct,
                        action=step.action,
                        args=step.args,
                        result_status="error",
                        result_output=str(e),
                        governance_trace=[f"error: {type(e).__name__}: {e}"],
                    )
                    self._chain_record(record)
                    all_records.append(record)

        return all_records

    # ── Intent Phase ──

    def _create_intent(
        self,
        plan: AgentPlan,
        step: PlanStep,
        context: Dict[str, Any],
    ) -> Intent:
        """Create an intent from a plan step."""
        grant = self.grants[plan.grant_id]

        intent = Intent(
            intent_id=f"intent:{uuid.uuid4().hex[:12]}",
            plan_id=plan.plan_id,
            step_id=step.id,
            proposed_action=step.action,
            proposed_args=step.args,
            proof_of_agency={
                "grant_id": grant.grant_id,
                "principal": grant.principal_lct,
                "agent": grant.agent_lct,
                "scope": grant.scope,
            },
            explanation=Explanation(
                why=f"Plan '{plan.name}' step '{step.id}' triggered",
                confidence=0.9,
                risk_assessment="low" if step.atp_cost < 20 else "medium",
            ),
            needs_approval=plan.guards.requires_manual_approval(step, context),
            atp_cost=step.atp_cost,
        )

        self.intents[intent.intent_id] = intent
        return intent

    # ── Law Check Phase ──

    def _check_law_compliance(self, plan: AgentPlan, intent: Intent):
        """Verify intent complies with society laws."""
        return self.law_checker(plan, intent)

    @staticmethod
    def _default_law_check(plan: AgentPlan, intent: Intent) -> bool:
        """Default law check: verify guards are respected."""
        # Check witness level from guards
        if plan.guards.witness_level < 0:
            raise GuardViolation("Invalid witness level")
        return True

    # ── Approval Phase ──

    def _resolve_approval(
        self,
        plan: AgentPlan,
        intent: Intent,
    ) -> Decision:
        """Route intent through approval gate."""
        if not intent.needs_approval:
            # Auto-approve
            return Decision(
                intent_id=intent.intent_id,
                decision=DecisionType.APPROVE,
                by="acp:auto-approver",
                rationale="Within auto-approval limits",
            )

        # Check registered auto-approvers
        for name, approver in self.auto_approvers.items():
            try:
                result = approver(intent)
                if result == DecisionType.APPROVE:
                    return Decision(
                        intent_id=intent.intent_id,
                        decision=DecisionType.APPROVE,
                        by=f"acp:auto-approver:{name}",
                        rationale=f"Auto-approved by {name}",
                    )
            except Exception:
                continue

        # No auto-approver handled it — needs manual approval
        raise ApprovalRequired(
            f"Intent {intent.intent_id} requires manual approval"
        )

    def submit_decision(
        self,
        intent_id: str,
        decision: DecisionType,
        by: str,
        rationale: str = "",
        modifications: Optional[Dict] = None,
    ) -> Optional[ExecutionRecord]:
        """Submit a manual decision on a pending intent."""
        if intent_id not in self.intents:
            raise ACPError(f"Intent {intent_id} not found")

        intent = self.intents[intent_id]
        dec = Decision(
            intent_id=intent_id,
            decision=decision,
            by=by,
            rationale=rationale,
            modifications=modifications,
        )
        self.decisions[intent_id] = dec

        if decision == DecisionType.DENY:
            intent.state = ACPState.REJECTED
            return None

        if decision == DecisionType.MODIFY and modifications:
            intent.proposed_args.update(modifications)

        # Execute the approved intent
        plan = self.plans[intent.plan_id]
        step = plan.get_step(intent.step_id)
        if not step:
            raise ACPError(f"Step {intent.step_id} not found in plan")

        # Execute action
        try:
            status, output = self.action_handler(
                intent.proposed_action, intent.proposed_args
            )
        except Exception as e:
            status, output = "error", str(e)

        # Collect witnesses
        witnesses = self.witness_provider(intent.intent_id)

        # Create execution record
        record = ExecutionRecord(
            record_id=f"rec:{uuid.uuid4().hex[:12]}",
            intent_id=intent.intent_id,
            plan_id=intent.plan_id,
            step_id=intent.step_id,
            agent_lct=plan.agent_lct,
            action=intent.proposed_action,
            args=intent.proposed_args,
            result_status=status,
            result_output=output,
            atp_consumed=intent.atp_cost if status == "success" else 0,
            witnesses=witnesses,
            governance_trace=[
                f"manual_decision: {decision.value} by {by}",
                f"rationale: {rationale}",
            ],
        )
        self._chain_record(record)
        self._update_plan_counters(plan.plan_id, record)

        intent.state = ACPState.COMPLETE if status == "success" else ACPState.FAILED
        return record

    # ── Execute Phase ──

    def _execute_step(
        self,
        plan: AgentPlan,
        step: PlanStep,
        context: Dict[str, Any],
    ) -> ExecutionRecord:
        """Execute a single plan step through full ACP lifecycle."""
        trace = []

        # Phase 1: Create Intent
        intent = self._create_intent(plan, step, context)
        trace.append(f"intent_created: {intent.intent_id}")

        # Phase 2: Law Check
        try:
            self._check_law_compliance(plan, intent)
            trace.append("law_check: pass")
        except (GuardViolation, ACPError) as e:
            intent.state = ACPState.REJECTED
            trace.append(f"law_check: FAIL ({e})")
            raise

        # Phase 3: Approval
        try:
            decision = self._resolve_approval(plan, intent)
            trace.append(f"approval: {decision.decision.value} by {decision.by}")
        except ApprovalRequired:
            intent.state = ACPState.APPROVAL_GATE
            trace.append("approval: PENDING (manual required)")
            raise

        self.decisions[intent.intent_id] = decision

        # Phase 4: Execute
        intent.state = ACPState.EXECUTING
        try:
            status, output = self.action_handler(step.action, step.args)
            trace.append(f"execute: {status}")
        except Exception as e:
            status, output = "error", str(e)
            trace.append(f"execute: error ({e})")

        # Phase 5: Collect witnesses
        witnesses = self.witness_provider(intent.intent_id)
        if len(witnesses) < plan.guards.witness_level:
            trace.append(f"witness: deficit ({len(witnesses)}/{plan.guards.witness_level})")
        else:
            trace.append(f"witness: ok ({len(witnesses)} witnesses)")

        # Phase 6: Record
        record = ExecutionRecord(
            record_id=f"rec:{uuid.uuid4().hex[:12]}",
            intent_id=intent.intent_id,
            plan_id=plan.plan_id,
            step_id=step.id,
            agent_lct=plan.agent_lct,
            action=step.action,
            args=step.args,
            result_status=status,
            result_output=output,
            atp_consumed=step.atp_cost if status == "success" else 0,
            witnesses=witnesses,
            governance_trace=trace,
        )
        self._chain_record(record)
        self._update_plan_counters(plan.plan_id, record)

        intent.state = ACPState.COMPLETE if status == "success" else ACPState.FAILED
        self.intents[intent.intent_id] = intent

        return record

    # ── Ledger & Bookkeeping ──

    def _chain_record(self, record: ExecutionRecord):
        """Add record to hash chain."""
        prev_hash = self.records[-1].hash if self.records else "genesis"
        record.compute_hash(prev_hash)
        self.records.append(record)

    def _update_plan_counters(self, plan_id: str, record: ExecutionRecord):
        """Update plan execution counters."""
        self.plan_executions[plan_id] = self.plan_executions.get(plan_id, 0) + 1
        self.plan_atp_consumed[plan_id] = (
            self.plan_atp_consumed.get(plan_id, 0) + record.atp_consumed
        )

    @staticmethod
    def _default_witnesses(intent_id: str) -> List[str]:
        """Default witness provider: system witness."""
        return [f"lct:web4:witness:system:{intent_id[:8]}"]

    # ── Query API ──

    def get_plan_status(self, plan_id: str) -> Dict:
        """Get execution status of a plan."""
        plan = self.plans.get(plan_id)
        if not plan:
            return {"error": f"Plan {plan_id} not found"}

        plan_records = [r for r in self.records if r.plan_id == plan_id]
        successes = sum(1 for r in plan_records if r.result_status == "success")
        failures = sum(1 for r in plan_records if r.result_status in ("failure", "error"))

        return {
            "plan_id": plan_id,
            "name": plan.name,
            "total_executions": self.plan_executions.get(plan_id, 0),
            "atp_consumed": self.plan_atp_consumed.get(plan_id, 0),
            "successes": successes,
            "failures": failures,
            "success_rate": successes / max(1, successes + failures),
            "steps": len(plan.steps),
            "pending_intents": sum(
                1 for i in self.intents.values()
                if i.plan_id == plan_id and i.state == ACPState.APPROVAL_GATE
            ),
        }

    def get_pending_approvals(self) -> List[Intent]:
        """Get all intents waiting for manual approval."""
        return [
            i for i in self.intents.values()
            if i.needs_approval and i.state == ACPState.APPROVAL_GATE
        ]

    def verify_chain_integrity(self) -> bool:
        """Verify the execution record hash chain."""
        for i, record in enumerate(self.records):
            prev_hash = self.records[i - 1].hash if i > 0 else "genesis"
            stored_hash = record.hash
            # Recompute what the hash SHOULD be
            data = json.dumps({
                "record_id": record.record_id,
                "intent_id": record.intent_id,
                "plan_id": record.plan_id,
                "action": record.action,
                "result_status": record.result_status,
                "atp_consumed": record.atp_consumed,
                "prev_hash": prev_hash,
            }, sort_keys=True)
            expected = hashlib.sha256(data.encode()).hexdigest()
            if stored_hash != expected:
                return False
        return True


# ═══════════════════════════════════════════════════════════════
# Demo: ACP in action
# ═══════════════════════════════════════════════════════════════

def run_demo():
    """Demonstrate ACP lifecycle with realistic scenarios."""
    print("=" * 70)
    print("  ACP (Agentic Context Protocol) — Reference Implementation")
    print("  Trigger → Plan → Intent → Law Check → Approve → Execute → Record")
    print("=" * 70)

    checks_passed = 0
    checks_failed = 0

    def check(name, condition, detail=""):
        nonlocal checks_passed, checks_failed
        if condition:
            print(f"  ✓ {name}")
            checks_passed += 1
        else:
            msg = f": {detail}" if detail else ""
            print(f"  ✗ {name}{msg}")
            checks_failed += 1

    # ── Setup: Action Handler ──
    # Simulates MCP tool execution
    action_results = {}

    def action_handler(action: str, args: Dict) -> Tuple[str, Any]:
        """Simulated action execution."""
        if action == "invoice.search":
            result = [
                {"id": "INV-001", "amount": 5.0, "status": "ready"},
                {"id": "INV-002", "amount": 15.0, "status": "ready"},
                {"id": "INV-003", "amount": 500.0, "status": "ready"},
            ]
            action_results["invoices"] = result
            return "success", result
        elif action == "invoice.validate":
            return "success", {"valid": True, "count": 3}
        elif action == "invoice.approve":
            amount = args.get("amount", 0)
            return "success", {"approved": True, "amount": amount}
        elif action == "invoice.reject":
            return "success", {"rejected": True}
        elif action == "security.scan":
            return "success", {"threats": 0, "warnings": 2}
        elif action == "security.isolate":
            return "failure", {"error": "no threat to isolate"}
        elif action == "unauthorized.action":
            return "success", "should never reach here"
        else:
            return "success", {"action": action, "args": args}

    executor = ACPExecutor(action_handler=action_handler)

    # ── Test 1: Grant Registration + Plan Registration ──
    print("\n── Test 1: Grant + Plan Registration ──")

    grant = AgencyGrant(
        grant_id="agy:grant:invoice-auth",
        principal_lct="lct:web4:entity:cfo",
        agent_lct="lct:web4:entity:invoice-bot",
        scope=["invoice.*"],
        resource_caps=ResourceCaps(max_atp=200, max_executions=50),
        witness_level=1,
    )
    executor.register_grant(grant)

    plan = AgentPlan(
        plan_id="acp:plan:invoice-processor",
        name="Invoice Processor",
        principal_lct="lct:web4:entity:cfo",
        agent_lct="lct:web4:entity:invoice-bot",
        grant_id="agy:grant:invoice-auth",
        triggers=[
            Trigger(kind=TriggerKind.MANUAL, authorized=["lct:web4:entity:cfo"]),
            Trigger(kind=TriggerKind.EVENT, config={"topic": "invoice.ready"}),
        ],
        steps=[
            PlanStep(id="fetch", action="invoice.search", args={"status": "ready"}, atp_cost=5),
            PlanStep(id="validate", action="invoice.validate", depends_on=["fetch"], atp_cost=5),
            PlanStep(
                id="approve-small",
                action="invoice.approve",
                args={"amount": 5.0},
                depends_on=["validate"],
                atp_cost=10,
            ),
        ],
        guards=Guards(
            resource_caps=ResourceCaps(max_atp=200, max_executions=50),
            witness_level=1,
            approval_mode=ApprovalMode.AUTO,
        ),
    )

    plan_id = executor.register_plan(plan)
    check("T1: Plan registered successfully", plan_id == plan.plan_id)
    check("T1: Grant registered", "agy:grant:invoice-auth" in executor.grants)

    # ── Test 2: Trigger Plan Execution ──
    print("\n── Test 2: Trigger Plan Execution (3-step pipeline) ──")

    records = executor.trigger_plan(
        plan_id,
        {"kind": "manual", "by": "lct:web4:entity:cfo"},
    )

    check("T2: All 3 steps executed", len(records) == 3)
    check("T2: Step 1 (fetch) succeeded", records[0].result_status == "success")
    check("T2: Step 2 (validate) succeeded", records[1].result_status == "success")
    check("T2: Step 3 (approve) succeeded", records[2].result_status == "success")
    check("T2: Governance trace includes intent",
          any("intent_created" in t for t in records[0].governance_trace))
    check("T2: Governance trace includes law check",
          any("law_check: pass" in t for t in records[0].governance_trace))
    check("T2: Governance trace includes approval",
          any("approval: approve" in t for t in records[0].governance_trace))

    # ── Test 3: Resource Caps Enforcement ──
    print("\n── Test 3: Resource Caps Enforcement ──")

    status = executor.get_plan_status(plan_id)
    check("T3: ATP consumed tracked", status["atp_consumed"] == 20.0,
          f"got {status['atp_consumed']}")  # 5 + 5 + 10
    check("T3: Execution count tracked", status["total_executions"] == 3)
    check("T3: Success rate = 100%", status["success_rate"] == 1.0)

    # ── Test 4: Scope Violation Detection ──
    print("\n── Test 4: Scope Violation Detection ──")

    try:
        bad_plan = AgentPlan(
            plan_id="acp:plan:bad",
            name="Unauthorized",
            principal_lct="lct:web4:entity:cfo",
            agent_lct="lct:web4:entity:invoice-bot",
            grant_id="agy:grant:invoice-auth",
            steps=[PlanStep(id="hack", action="unauthorized.action")],
        )
        executor.register_plan(bad_plan)
        check("T4: Scope violation detected", False, "should have raised")
    except ScopeViolation as e:
        check("T4: Scope violation detected", "unauthorized.action" in str(e))

    # ── Test 5: Expired Grant Rejection ──
    print("\n── Test 5: Expired Grant Rejection ──")

    expired_grant = AgencyGrant(
        grant_id="agy:grant:expired",
        principal_lct="lct:web4:entity:cfo",
        agent_lct="lct:web4:entity:old-bot",
        scope=["*"],
        valid_until="2020-01-01T00:00:00+00:00",
    )
    executor.register_grant(expired_grant)

    try:
        old_plan = AgentPlan(
            plan_id="acp:plan:expired",
            name="Expired Grant Plan",
            principal_lct="lct:web4:entity:cfo",
            agent_lct="lct:web4:entity:old-bot",
            grant_id="agy:grant:expired",
            steps=[PlanStep(id="do", action="anything")],
        )
        executor.register_plan(old_plan)
        check("T5: Expired grant rejected", False, "should have raised")
    except NoValidGrant:
        check("T5: Expired grant rejected", True)

    # ── Test 6: Manual Approval Flow ──
    print("\n── Test 6: Manual Approval Flow ──")

    manual_plan = AgentPlan(
        plan_id="acp:plan:high-value",
        name="High Value Invoice",
        principal_lct="lct:web4:entity:cfo",
        agent_lct="lct:web4:entity:invoice-bot",
        grant_id="agy:grant:invoice-auth",
        triggers=[Trigger(kind=TriggerKind.MANUAL, authorized=["lct:web4:entity:cfo"])],
        steps=[
            PlanStep(
                id="approve-big",
                action="invoice.approve",
                args={"amount": 500.0},
                atp_cost=25,
                requires_approval="amount > 100",
            ),
        ],
        guards=Guards(
            approval_mode=ApprovalMode.CONDITIONAL,
            approval_threshold=100.0,
            witness_level=2,
        ),
    )
    executor.register_plan(manual_plan)

    # Trigger — should raise ApprovalRequired because amount > threshold
    try:
        records = executor.trigger_plan(
            "acp:plan:high-value",
            {"kind": "manual", "by": "lct:web4:entity:cfo", "value": 500.0},
        )
        # The step failed due to approval required, but may return empty records
        pending = executor.get_pending_approvals()
        check("T6: Intent pending approval", len(pending) >= 1)
    except ACPError:
        pending = executor.get_pending_approvals()
        check("T6: Intent pending approval", len(pending) >= 1)

    # Submit manual approval
    if pending:
        intent = pending[0]
        record = executor.submit_decision(
            intent.intent_id,
            DecisionType.APPROVE,
            by="lct:web4:entity:cfo",
            rationale="Reviewed and approved the high-value invoice",
        )
        check("T6: Manual approval executed", record is not None)
        check("T6: Manual decision recorded",
              record.result_status == "success" if record else False)
        check("T6: Governance trace shows manual",
              any("manual_decision" in t for t in record.governance_trace) if record else False)

    # ── Test 7: Dependency Chain with Failure ──
    print("\n── Test 7: Dependency Chain with Failure Handling ──")

    sec_grant = AgencyGrant(
        grant_id="agy:grant:security",
        principal_lct="lct:web4:entity:admin",
        agent_lct="lct:web4:entity:sec-bot",
        scope=["security.*"],
    )
    executor.register_grant(sec_grant)

    sec_plan = AgentPlan(
        plan_id="acp:plan:security-monitor",
        name="Security Monitor",
        principal_lct="lct:web4:entity:admin",
        agent_lct="lct:web4:entity:sec-bot",
        grant_id="agy:grant:security",
        triggers=[Trigger(kind=TriggerKind.EVENT, config={"topic": "alert"})],
        steps=[
            PlanStep(id="scan", action="security.scan", atp_cost=5),
            PlanStep(
                id="isolate",
                action="security.isolate",
                depends_on=["scan"],
                atp_cost=20,
                on_failure="skip",  # Don't abort if isolation fails
            ),
        ],
        guards=Guards(approval_mode=ApprovalMode.AUTO),
    )
    executor.register_plan(sec_plan)

    records = executor.trigger_plan(
        "acp:plan:security-monitor",
        {"topic": "alert"},
    )

    check("T7: Both steps executed", len(records) == 2)
    check("T7: Scan succeeded", records[0].result_status == "success")
    check("T7: Isolate failed gracefully", records[1].result_status == "failure")

    # ── Test 8: Event Trigger ──
    print("\n── Test 8: Event Trigger ──")

    records = executor.trigger_plan(
        plan_id,  # Invoice plan also has event trigger
        {"topic": "invoice.ready"},
    )
    check("T8: Event trigger executed plan", len(records) == 3)

    # ── Test 9: Hash Chain Integrity ──
    print("\n── Test 9: Hash Chain Integrity ──")

    check("T9: Hash chain intact", executor.verify_chain_integrity())
    total_records = len(executor.records)
    check("T9: Records accumulated", total_records >= 8,
          f"got {total_records}")

    # Tamper detection
    if executor.records:
        original = executor.records[0].hash
        executor.records[0].hash = "tampered"
        check("T9: Tamper detected", not executor.verify_chain_integrity())
        executor.records[0].hash = original  # Restore

    # ── Test 10: Trigger Mismatch ──
    print("\n── Test 10: Trigger Mismatch Rejection ──")

    try:
        executor.trigger_plan(plan_id, {"topic": "wrong.topic"})
        check("T10: Wrong trigger rejected", False)
    except ACPError as e:
        check("T10: Wrong trigger rejected", "No trigger matches" in str(e))

    # ── Test 11: Plan Status Dashboard ──
    print("\n── Test 11: Plan Status Dashboard ──")

    status = executor.get_plan_status(plan_id)
    check("T11: Dashboard shows correct name", status["name"] == "Invoice Processor")
    check("T11: Dashboard shows executions", status["total_executions"] >= 6)
    check("T11: Dashboard shows ATP consumed", status["atp_consumed"] >= 40)

    # ── Test 12: Auto-Approver Registration ──
    print("\n── Test 12: Custom Auto-Approver ──")

    # Register an auto-approver that approves invoices under $1000
    def invoice_auto_approver(intent: Intent) -> DecisionType:
        amount = intent.proposed_args.get("amount", 0)
        if amount <= 1000:
            return DecisionType.APPROVE
        raise Exception("Amount too high")

    executor.register_auto_approver("invoice_threshold", invoice_auto_approver)

    # Create a plan that requires conditional approval
    auto_plan = AgentPlan(
        plan_id="acp:plan:auto-invoice",
        name="Auto-Approved Invoice",
        principal_lct="lct:web4:entity:cfo",
        agent_lct="lct:web4:entity:invoice-bot",
        grant_id="agy:grant:invoice-auth",
        triggers=[Trigger(kind=TriggerKind.MANUAL, authorized=["lct:web4:entity:cfo"])],
        steps=[
            PlanStep(
                id="approve-medium",
                action="invoice.approve",
                args={"amount": 750.0},
                atp_cost=15,
                requires_approval="amount > 0",
            ),
        ],
        guards=Guards(
            approval_mode=ApprovalMode.CONDITIONAL,
            approval_threshold=0,  # All amounts need approval check
        ),
    )
    executor.register_plan(auto_plan)

    records = executor.trigger_plan(
        "acp:plan:auto-invoice",
        {"kind": "manual", "by": "lct:web4:entity:cfo", "value": 750},
    )
    check("T12: Auto-approver handled intent", len(records) == 1)
    check("T12: Auto-approved successfully", records[0].result_status == "success")
    check("T12: Trace shows auto-approver",
          any("invoice_threshold" in t for t in records[0].governance_trace))

    # ── Test 13: Decision Modification ──
    print("\n── Test 13: Decision with Modification ──")

    mod_plan = AgentPlan(
        plan_id="acp:plan:modifiable",
        name="Modifiable Invoice",
        principal_lct="lct:web4:entity:cfo",
        agent_lct="lct:web4:entity:invoice-bot",
        grant_id="agy:grant:invoice-auth",
        triggers=[Trigger(kind=TriggerKind.MANUAL, authorized=["lct:web4:entity:cfo"])],
        steps=[
            PlanStep(
                id="approve-mod",
                action="invoice.approve",
                args={"amount": 2000.0},
                atp_cost=30,
            ),
        ],
        guards=Guards(approval_mode=ApprovalMode.MANUAL),
    )
    executor.register_plan(mod_plan)

    # Trigger — will create pending intent since MANUAL approval
    executor.trigger_plan(
        "acp:plan:modifiable",
        {"kind": "manual", "by": "lct:web4:entity:cfo"},
    )

    pending = executor.get_pending_approvals()
    mod_intents = [p for p in pending if p.plan_id == "acp:plan:modifiable"]
    check("T13: Modifiable intent pending", len(mod_intents) >= 1)

    if mod_intents:
        record = executor.submit_decision(
            mod_intents[0].intent_id,
            DecisionType.MODIFY,
            by="lct:web4:entity:cfo",
            rationale="Reduced amount to budget limit",
            modifications={"amount": 1500.0},
        )
        check("T13: Modified decision executed", record is not None)
        check("T13: Args reflect modification",
              record.args.get("amount") == 1500.0 if record else False)

    # ── Test 14: Denial Flow ──
    print("\n── Test 14: Denial Flow ──")

    deny_plan = AgentPlan(
        plan_id="acp:plan:deniable",
        name="Deniable Request",
        principal_lct="lct:web4:entity:cfo",
        agent_lct="lct:web4:entity:invoice-bot",
        grant_id="agy:grant:invoice-auth",
        triggers=[Trigger(kind=TriggerKind.MANUAL, authorized=["lct:web4:entity:cfo"])],
        steps=[
            PlanStep(id="approve-deny", action="invoice.approve", args={"amount": 9999}),
        ],
        guards=Guards(approval_mode=ApprovalMode.MANUAL),
    )
    executor.register_plan(deny_plan)

    executor.trigger_plan(
        "acp:plan:deniable",
        {"kind": "manual", "by": "lct:web4:entity:cfo"},
    )

    pending = executor.get_pending_approvals()
    deny_intents = [p for p in pending if p.plan_id == "acp:plan:deniable"]

    if deny_intents:
        record = executor.submit_decision(
            deny_intents[0].intent_id,
            DecisionType.DENY,
            by="lct:web4:entity:cfo",
            rationale="Amount exceeds quarterly budget",
        )
        check("T14: Denial returns no record", record is None)

        # Verify the intent is now in REJECTED state
        denied_intent = executor.intents[deny_intents[0].intent_id]
        check("T14: Intent state is REJECTED",
              denied_intent.state == ACPState.REJECTED)

    # ── Summary ──
    print("\n" + "=" * 70)
    total = checks_passed + checks_failed
    print(f"  ACP Reference Implementation: {checks_passed}/{total} checks passed")
    if checks_failed == 0:
        print("  ALL CHECKS PASSED!")

    print(f"\n  CAPABILITIES DEMONSTRATED:")
    print(f"    1. Plan registration with grant validation + scope enforcement")
    print(f"    2. Multi-step pipeline with dependency ordering")
    print(f"    3. Trigger matching (manual + event)")
    print(f"    4. Law compliance checking")
    print(f"    5. Auto-approval + manual approval + custom auto-approvers")
    print(f"    6. Decision modification (approve/deny/modify)")
    print(f"    7. Dependency failure handling (abort vs skip)")
    print(f"    8. Hash-chained execution records")
    print(f"    9. Resource cap enforcement (ATP + execution count)")
    print(f"   10. Governance trace for full auditability")
    print(f"   11. Plan status dashboard")

    print(f"\n  ACP STATE MACHINE COVERAGE:")
    states_seen = set()
    for intent in executor.intents.values():
        states_seen.add(intent.state.value)
    print(f"    States exercised: {sorted(states_seen)}")

    print(f"\n  INTEGRATION POINTS:")
    print(f"    - R7: ACP creates intents → R7 executes actions")
    print(f"    - Hardbound: Governance trace maps to 10-layer stack")
    print(f"    - AGY: Grants provide proof of agency")
    print(f"    - SAL: Law checker verifies society compliance")
    print(f"    - ATP: Resource caps + per-step cost tracking")

    print("=" * 70)

    return checks_failed == 0


if __name__ == "__main__":
    success = run_demo()
    import sys
    sys.exit(0 if success else 1)
