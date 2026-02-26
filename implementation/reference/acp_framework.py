#!/usr/bin/env python3
"""
Web4 Agentic Context Protocol (ACP) Framework — Reference Implementation
==========================================================================

Implements: web4-standard/core-spec/acp-framework.md (647 lines)

Complete ACP framework covering all 13 spec sections:
  §1  Core Concept — reactive to agentic evolution
  §2  ACP Components — Plan, Intent, Decision, ExecutionRecord
  §3  State Machine — 7-state lifecycle
  §4  ACP-AGY Integration — agency validation, proof of agency
  §5  ACP-SAL Integration — law compliance, witness requirements
  §6  Human Console Interface — approval requests, monitoring
  §7  Security Model — defense in depth, threat mitigation
  §8  ACP-MRH Integration — RDF relationships
  §9  Implementation Requirements — MUST/SHOULD/MAY
  §10 Error Handling — 6 error types, recovery strategies
  §11 Use Cases — invoice, security, content moderation

Run: python acp_framework.py
"""

from __future__ import annotations
import hashlib
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Optional


# ============================================================
# §10  ERROR HANDLING (defined first for use throughout)
# ============================================================

class ACPError(Exception):
    """Base class for ACP errors."""
    error_code = "W4_ERR_ACP_GENERIC"

class NoValidGrant(ACPError):
    error_code = "W4_ERR_ACP_NO_GRANT"

class ScopeViolation(ACPError):
    error_code = "W4_ERR_ACP_SCOPE_VIOLATION"

class ApprovalRequired(ACPError):
    error_code = "W4_ERR_ACP_APPROVAL_REQUIRED"

class WitnessDeficit(ACPError):
    error_code = "W4_ERR_ACP_WITNESS_DEFICIT"

class PlanExpired(ACPError):
    error_code = "W4_ERR_ACP_PLAN_EXPIRED"

class LedgerWriteFailure(ACPError):
    error_code = "W4_ERR_ACP_LEDGER_WRITE"

class ResourceCapExceeded(ACPError):
    error_code = "W4_ERR_ACP_RESOURCE_CAP"

class IllegalTrigger(ACPError):
    error_code = "W4_ERR_ACP_ILLEGAL_TRIGGER"


# ============================================================
# §2  ACP COMPONENTS
# ============================================================

class TriggerKind(Enum):
    CRON = "cron"
    EVENT = "event"
    MANUAL = "manual"


@dataclass
class Trigger:
    kind: TriggerKind = TriggerKind.MANUAL
    expr: str = ""
    topic: str = ""
    authorized: list[str] = field(default_factory=list)


@dataclass
class PlanStep:
    """A step in an agent plan."""
    step_id: str = ""
    mcp: str = ""          # MCP resource/tool to call
    args: dict = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    requires_approval: str = ""  # condition or empty


@dataclass
class ResourceCaps:
    max_atp: float = 0.0
    max_executions: int = 0
    rate_limit: str = ""  # e.g., "10/hour"


@dataclass
class HumanApprovalConfig:
    mode: str = "prompt"  # "auto-if<=N else prompt"
    timeout: int = 3600
    fallback: str = "deny"  # deny, abort


@dataclass
class PlanGuards:
    law_hash: str = ""
    resource_caps: ResourceCaps = field(default_factory=ResourceCaps)
    witness_level: int = 0
    human_approval: HumanApprovalConfig = field(default_factory=HumanApprovalConfig)


@dataclass
class AgentPlan:
    """§2.1 Agent Plan — declarative specification of agent intent."""
    plan_id: str = ""
    principal: str = ""     # lct of the principal (client)
    agent: str = ""         # lct of the agent
    grant_id: str = ""      # agy grant
    triggers: list[Trigger] = field(default_factory=list)
    steps: list[PlanStep] = field(default_factory=list)
    guards: PlanGuards = field(default_factory=PlanGuards)
    expires_at: str = ""
    signatures: list[str] = field(default_factory=list)

    def is_expired(self, now: datetime | None = None) -> bool:
        if not self.expires_at:
            return False
        now = now or datetime.utcnow()
        try:
            expiry = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            return now >= expiry.replace(tzinfo=None)
        except ValueError:
            return False


@dataclass
class ProofOfAgency:
    """§4.2 Proof of Agency."""
    grant_id: str = ""
    plan_id: str = ""
    intent_id: str = ""
    ledger_proof: dict = field(default_factory=dict)
    nonce: str = ""
    audience: list[str] = field(default_factory=list)
    expires_at: str = ""


@dataclass
class Intent:
    """§2.2 Intent — actionable proposal from plan evaluation."""
    intent_id: str = ""
    plan_id: str = ""
    proposed_action: dict = field(default_factory=dict)  # mcp + args
    proof_of_agency: Optional[ProofOfAgency] = None
    explain: dict = field(default_factory=dict)  # why, confidence, alternatives, risk
    needs_approval: bool = False
    created_at: str = ""


@dataclass
class Decision:
    """§2.3 Decision — human or automated decision on intent."""
    intent_id: str = ""
    decision: str = ""  # approve, deny, modify
    modifications: Optional[dict] = None
    by: str = ""
    rationale: str = ""
    witnesses: list[str] = field(default_factory=list)
    timestamp: str = ""


@dataclass
class T3V3Delta:
    """Trust/value tensor changes."""
    agent_t3: dict = field(default_factory=dict)
    client_v3: dict = field(default_factory=dict)


@dataclass
class ExecutionRecord:
    """§2.4 Execution Record — immutable record of action."""
    record_id: str = ""
    intent_id: str = ""
    grant_id: str = ""
    law_hash: str = ""
    mcp_call: dict = field(default_factory=dict)
    result: dict = field(default_factory=dict)
    t3v3_delta: T3V3Delta = field(default_factory=T3V3Delta)
    witnesses: list[str] = field(default_factory=list)
    ledger_inclusion: dict = field(default_factory=dict)


# ============================================================
# §3  ACP STATE MACHINE
# ============================================================

class ACPState(Enum):
    """§3.1 Lifecycle states."""
    IDLE = "idle"
    PLANNING = "planning"
    INTENT_CREATED = "intent_created"
    LAW_CHECK = "law_check"
    APPROVAL_GATE = "approval_gate"
    EXECUTING = "executing"
    RECORDING = "recording"
    COMPLETE = "complete"
    FAILED = "failed"


# §3.2 State transitions
ACP_TRANSITIONS = {
    ACPState.IDLE: {ACPState.PLANNING, ACPState.FAILED},
    ACPState.PLANNING: {ACPState.INTENT_CREATED, ACPState.FAILED},
    ACPState.INTENT_CREATED: {ACPState.LAW_CHECK, ACPState.FAILED},
    ACPState.LAW_CHECK: {ACPState.APPROVAL_GATE, ACPState.FAILED},
    ACPState.APPROVAL_GATE: {ACPState.EXECUTING, ACPState.FAILED},
    ACPState.EXECUTING: {ACPState.RECORDING, ACPState.FAILED},
    ACPState.RECORDING: {ACPState.COMPLETE, ACPState.FAILED},
    ACPState.COMPLETE: set(),
    ACPState.FAILED: set(),
}


class ACPStateMachine:
    """State machine for ACP lifecycle."""

    def __init__(self):
        self.state = ACPState.IDLE
        self.history: list[tuple[ACPState, str, str]] = [
            (ACPState.IDLE, datetime.utcnow().isoformat(), "init")
        ]

    def can_transition(self, target: ACPState) -> bool:
        return target in ACP_TRANSITIONS.get(self.state, set())

    def transition(self, target: ACPState, reason: str = "") -> bool:
        if not self.can_transition(target):
            return False
        self.state = target
        self.history.append((target, datetime.utcnow().isoformat(), reason))
        return True

    @property
    def is_terminal(self) -> bool:
        return self.state in (ACPState.COMPLETE, ACPState.FAILED)


# ============================================================
# §4  ACP-AGY INTEGRATION
# ============================================================

@dataclass
class AgencyGrant:
    """Agency grant for ACP validation."""
    grant_id: str = ""
    principal: str = ""
    agent: str = ""
    scope: list[str] = field(default_factory=list)  # e.g., ["invoice.*"]
    resource_caps: ResourceCaps = field(default_factory=ResourceCaps)
    witness_level: int = 0
    expires_at: str = ""
    revoked: bool = False

    def is_expired(self, now: datetime | None = None) -> bool:
        if not self.expires_at:
            return False
        now = now or datetime.utcnow()
        try:
            expiry = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            return now >= expiry.replace(tzinfo=None)
        except ValueError:
            return False


def within_scope(action: dict, scope: list[str]) -> bool:
    """Check if proposed action is within grant scope."""
    mcp = action.get("mcp", "")
    for s in scope:
        if s.endswith("*"):
            if mcp.startswith(s[:-1]):
                return True
        elif mcp == s:
            return True
    return False


def exceeds_caps(intent: Intent, caps: ResourceCaps, executions_today: int = 0) -> bool:
    """Check if intent would exceed resource caps."""
    proposed_atp = intent.proposed_action.get("args", {}).get("atp", 0)
    if caps.max_atp > 0 and proposed_atp > caps.max_atp:
        return True
    if caps.max_executions > 0 and executions_today >= caps.max_executions:
        return True
    return False


def validate_acp_agency(plan: AgentPlan, intent: Intent,
                        grants: dict[str, AgencyGrant],
                        executions_today: int = 0) -> bool:
    """§4.1 Validate agency for ACP action."""
    grant = grants.get(plan.grant_id)
    if not grant or grant.revoked:
        raise NoValidGrant(f"No valid grant: {plan.grant_id}")
    if grant.is_expired():
        raise NoValidGrant(f"Grant expired: {plan.grant_id}")
    if not within_scope(intent.proposed_action, grant.scope):
        raise ScopeViolation(f"Action outside scope: {intent.proposed_action.get('mcp')}")
    if exceeds_caps(intent, grant.resource_caps, executions_today):
        raise ResourceCapExceeded("Resource caps exceeded")
    return True


# ============================================================
# §5  ACP-SAL INTEGRATION
# ============================================================

@dataclass
class LawConfig:
    """Simplified law oracle config for compliance checks."""
    law_hash: str = ""
    allowed_triggers: list[str] = field(default_factory=list)  # trigger kinds
    max_atp_per_plan: float = 1000.0
    min_witness_level: int = 1
    prohibited_actions: list[str] = field(default_factory=list)


@dataclass
class WitnessRequirement:
    """§5.2 Witness requirements."""
    level: int = 0
    types: list[str] = field(default_factory=list)
    quorum_model: str = "byzantine"
    quorum_threshold: float = 0.67
    timeout: int = 300
    fallback: str = "abort"


def check_law_compliance(plan: AgentPlan, law: LawConfig) -> bool:
    """§5.1 Check plan compliance with society laws."""
    for trigger in plan.triggers:
        if law.allowed_triggers and trigger.kind.value not in law.allowed_triggers:
            raise IllegalTrigger(f"Trigger {trigger.kind.value} not allowed")

    if plan.guards.resource_caps.max_atp > law.max_atp_per_plan:
        raise ResourceCapExceeded(
            f"Plan ATP cap {plan.guards.resource_caps.max_atp} > law max {law.max_atp_per_plan}"
        )

    if plan.guards.witness_level < law.min_witness_level:
        raise WitnessDeficit(
            f"Plan witness level {plan.guards.witness_level} < law min {law.min_witness_level}"
        )

    return True


# ============================================================
# §6  HUMAN CONSOLE INTERFACE
# ============================================================

@dataclass
class RiskProfile:
    level: str = "low"  # low, medium, high, critical
    factors: list[str] = field(default_factory=list)


@dataclass
class ApprovalRequest:
    """§6.1 Approval request for human console."""
    intent: Intent = field(default_factory=Intent)
    plan: AgentPlan = field(default_factory=AgentPlan)
    risk_assessment: RiskProfile = field(default_factory=RiskProfile)
    explanation: dict = field(default_factory=dict)
    urgency: str = "low"  # low, medium, high, critical
    deadline: str = ""


@dataclass
class DashboardState:
    """§6.2 Monitoring dashboard."""
    active_plans: int = 0
    pending_intents: int = 0
    executions_today: int = 0
    success_rate: float = 0.0
    atp_consumed: float = 0.0
    trust_trend: dict = field(default_factory=dict)
    alerts: list[dict] = field(default_factory=list)


# ============================================================
# §7  SECURITY MODEL
# ============================================================

class SecurityLayer(Enum):
    """§7.1 Defense in depth layers."""
    AGENCY = "agency"       # Layer 1: Valid grants
    LAW = "law"             # Layer 2: Compliance
    APPROVAL = "approval"   # Layer 3: Human oversight
    WITNESS = "witness"     # Layer 4: Multi-party attestation
    AUDIT = "audit"         # Layer 5: Post-execution review


@dataclass
class ThreatMitigation:
    """§7.2 Threat and mitigation mapping."""
    threat: str = ""
    mitigation: str = ""
    layer: SecurityLayer = SecurityLayer.AGENCY


THREAT_MAP = [
    ThreatMitigation("runaway_automation", "Resource caps, rate limits", SecurityLayer.AGENCY),
    ThreatMitigation("unauthorized_actions", "Agency grants, scope enforcement", SecurityLayer.AGENCY),
    ThreatMitigation("malicious_plans", "Law compliance, witness requirements", SecurityLayer.LAW),
    ThreatMitigation("replay_attacks", "Nonces, temporal bounds", SecurityLayer.WITNESS),
    ThreatMitigation("trust_gaming", "Audit adjustments, reputation stakes", SecurityLayer.AUDIT),
]


# ============================================================
# §8  ACP-MRH INTEGRATION (RDF relationships)
# ============================================================

@dataclass
class ACPTriple:
    """RDF triple for ACP MRH relationships."""
    subject: str = ""
    predicate: str = ""
    obj: str = ""

    def to_turtle(self) -> str:
        return f"{self.subject} {self.predicate} {self.obj} ."


ACP_PREDICATES = [
    "acp:hasAgent",
    "acp:hasPrincipal",
    "acp:underGrant",
    "acp:derivedFrom",
    "acp:hasDecision",
    "acp:hasExecutionRecord",
    "acp:executedBy",
    "acp:witnessedBy",
    "acp:recordedIn",
]


def generate_plan_triples(plan: AgentPlan) -> list[ACPTriple]:
    """Generate RDF triples for a plan."""
    triples = [
        ACPTriple(f"lct:plan:{plan.plan_id}", "acp:hasAgent", f"lct:entity:{plan.agent}"),
        ACPTriple(f"lct:plan:{plan.plan_id}", "acp:hasPrincipal", f"lct:entity:{plan.principal}"),
    ]
    if plan.grant_id:
        triples.append(
            ACPTriple(f"lct:plan:{plan.plan_id}", "acp:underGrant", f"lct:grant:{plan.grant_id}")
        )
    return triples


def generate_execution_triples(record: ExecutionRecord, agent_lct: str) -> list[ACPTriple]:
    """Generate RDF triples for an execution record."""
    triples = [
        ACPTriple(f"lct:record:{record.record_id}", "acp:executedBy", f"lct:entity:{agent_lct}"),
    ]
    for w in record.witnesses:
        triples.append(
            ACPTriple(f"lct:record:{record.record_id}", "acp:witnessedBy", f"lct:witness:{w}")
        )
    return triples


# ============================================================
# §8+  COMPLETE ACP ENGINE
# ============================================================

class ACPEngine:
    """Complete ACP execution engine."""

    def __init__(self):
        self.plans: dict[str, AgentPlan] = {}
        self.grants: dict[str, AgencyGrant] = {}
        self.intents: dict[str, Intent] = {}
        self.decisions: dict[str, Decision] = {}
        self.records: dict[str, ExecutionRecord] = {}
        self.state_machines: dict[str, ACPStateMachine] = {}
        self.execution_counts: dict[str, int] = {}  # plan_id → count
        self.dashboard = DashboardState()

    def register_grant(self, grant: AgencyGrant):
        self.grants[grant.grant_id] = grant

    def register_plan(self, plan: AgentPlan) -> ACPStateMachine:
        self.plans[plan.plan_id] = plan
        sm = ACPStateMachine()
        self.state_machines[plan.plan_id] = sm
        self.dashboard.active_plans += 1
        return sm

    def trigger_plan(self, plan_id: str, trigger: Trigger) -> Optional[Intent]:
        """§3: Trigger → Planning → Intent Created."""
        plan = self.plans.get(plan_id)
        if not plan:
            return None

        sm = self.state_machines.get(plan_id)
        if not sm:
            return None

        # Check expiry
        if plan.is_expired():
            sm.transition(ACPState.FAILED, "Plan expired")
            raise PlanExpired(f"Plan {plan_id} expired")

        # Idle → Planning
        if sm.state != ACPState.IDLE:
            return None
        sm.transition(ACPState.PLANNING, f"Triggered by {trigger.kind.value}")

        # Evaluate plan steps
        if not plan.steps:
            sm.transition(ACPState.FAILED, "No steps in plan")
            return None

        # Generate intent from first executable step
        step = plan.steps[0]
        intent = Intent(
            intent_id=f"acp:intent:{uuid.uuid4().hex[:12]}",
            plan_id=plan_id,
            proposed_action={"mcp": step.mcp, "args": step.args},
            proof_of_agency=ProofOfAgency(
                grant_id=plan.grant_id,
                plan_id=plan_id,
                nonce=uuid.uuid4().hex[:16],
            ),
            explain={
                "why": f"Step '{step.step_id}' from plan {plan_id}",
                "confidence": 0.95,
                "alternatives": [],
                "riskAssessment": "low",
            },
            needs_approval=bool(step.requires_approval),
            created_at=datetime.utcnow().isoformat(),
        )
        self.intents[intent.intent_id] = intent
        sm.transition(ACPState.INTENT_CREATED, f"Intent {intent.intent_id}")
        self.dashboard.pending_intents += 1
        return intent

    def law_check(self, intent_id: str, law: LawConfig) -> bool:
        """§5: Law compliance check."""
        intent = self.intents.get(intent_id)
        if not intent:
            return False

        plan = self.plans.get(intent.plan_id)
        if not plan:
            return False

        sm = self.state_machines.get(intent.plan_id)
        if not sm or sm.state != ACPState.INTENT_CREATED:
            return False

        try:
            check_law_compliance(plan, law)
            sm.transition(ACPState.LAW_CHECK, "Law check passed")

            # Also validate agency
            count = self.execution_counts.get(plan.plan_id, 0)
            validate_acp_agency(plan, intent, self.grants, count)

            sm.transition(ACPState.APPROVAL_GATE, "Agency validated")
            return True
        except ACPError as e:
            sm.transition(ACPState.FAILED, str(e))
            return False

    def decide(self, intent_id: str, decision: str, by: str,
               rationale: str = "", witnesses: list[str] | None = None) -> Optional[Decision]:
        """§2.3 + §3: Approval gate."""
        intent = self.intents.get(intent_id)
        if not intent:
            return None

        sm = self.state_machines.get(intent.plan_id)
        if not sm or sm.state != ACPState.APPROVAL_GATE:
            return None

        d = Decision(
            intent_id=intent_id,
            decision=decision,
            by=by,
            rationale=rationale,
            witnesses=witnesses or [],
            timestamp=datetime.utcnow().isoformat(),
        )
        self.decisions[intent_id] = d
        self.dashboard.pending_intents = max(0, self.dashboard.pending_intents - 1)

        if decision == "approve":
            sm.transition(ACPState.EXECUTING, f"Approved by {by}")
            return d
        else:
            sm.transition(ACPState.FAILED, f"Denied by {by}: {rationale}")
            return d

    def execute(self, intent_id: str) -> Optional[ExecutionRecord]:
        """§2.4 + §3: Execute action and create record."""
        intent = self.intents.get(intent_id)
        if not intent:
            return None

        plan = self.plans.get(intent.plan_id)
        if not plan:
            return None

        sm = self.state_machines.get(intent.plan_id)
        if not sm or sm.state != ACPState.EXECUTING:
            return None

        # Simulate execution
        record = ExecutionRecord(
            record_id=f"acp:record:{uuid.uuid4().hex[:12]}",
            intent_id=intent_id,
            grant_id=plan.grant_id,
            law_hash=plan.guards.law_hash,
            mcp_call={
                "resource": intent.proposed_action.get("mcp"),
                "args": intent.proposed_action.get("args"),
                "timestamp": datetime.utcnow().isoformat(),
            },
            result={
                "status": "success",
                "output": {"processed": True},
                "resourcesConsumed": {"atp": 2},
            },
            t3v3_delta=T3V3Delta(
                agent_t3={"temperament": 0.01},
                client_v3={"value": 0.02},
            ),
            witnesses=self.decisions.get(intent_id, Decision()).witnesses,
            ledger_inclusion={
                "hash": hashlib.sha256(intent_id.encode()).hexdigest()[:16],
                "block": 12346,
            },
        )
        self.records[record.record_id] = record
        self.execution_counts[plan.plan_id] = self.execution_counts.get(plan.plan_id, 0) + 1
        self.dashboard.executions_today += 1

        sm.transition(ACPState.RECORDING, "Execution complete")
        sm.transition(ACPState.COMPLETE, "Recorded and witnessed")

        return record

    def get_dashboard(self) -> DashboardState:
        total = self.dashboard.executions_today
        if total > 0:
            completed = sum(
                1 for sm in self.state_machines.values()
                if sm.state == ACPState.COMPLETE
            )
            self.dashboard.success_rate = completed / total
        return self.dashboard

    def handle_error(self, plan_id: str, error: ACPError) -> str:
        """§10.2 Error recovery."""
        sm = self.state_machines.get(plan_id)
        if sm and not sm.is_terminal:
            sm.transition(ACPState.FAILED, f"Error: {error.error_code}")

        if isinstance(error, ApprovalRequired):
            return "escalate_to_human"
        elif isinstance(error, WitnessDeficit):
            return "wait_for_witnesses"
        elif isinstance(error, ScopeViolation):
            return "request_grant_expansion"
        elif isinstance(error, LedgerWriteFailure):
            return "retry_with_backoff"
        else:
            return "abort_plan"


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

    # ── T1: Error Types ──
    print("T1: Error Types (§10)")

    check("T1.1 NoValidGrant code", NoValidGrant.error_code == "W4_ERR_ACP_NO_GRANT")
    check("T1.2 ScopeViolation code", ScopeViolation.error_code == "W4_ERR_ACP_SCOPE_VIOLATION")
    check("T1.3 ApprovalRequired code", ApprovalRequired.error_code == "W4_ERR_ACP_APPROVAL_REQUIRED")
    check("T1.4 WitnessDeficit code", WitnessDeficit.error_code == "W4_ERR_ACP_WITNESS_DEFICIT")
    check("T1.5 PlanExpired code", PlanExpired.error_code == "W4_ERR_ACP_PLAN_EXPIRED")
    check("T1.6 LedgerWriteFailure code", LedgerWriteFailure.error_code == "W4_ERR_ACP_LEDGER_WRITE")
    check("T1.7 All inherit ACPError",
          all(issubclass(c, ACPError) for c in
              [NoValidGrant, ScopeViolation, ApprovalRequired, WitnessDeficit, PlanExpired, LedgerWriteFailure]))

    # ── T2: Trigger Types ──
    print("T2: Trigger Types (§2.1)")

    check("T2.1 Cron trigger", TriggerKind.CRON.value == "cron")
    check("T2.2 Event trigger", TriggerKind.EVENT.value == "event")
    check("T2.3 Manual trigger", TriggerKind.MANUAL.value == "manual")

    t_cron = Trigger(kind=TriggerKind.CRON, expr="0 */6 * * *")
    check("T2.4 Cron expr", t_cron.expr == "0 */6 * * *")

    t_event = Trigger(kind=TriggerKind.EVENT, topic="invoice.ready")
    check("T2.5 Event topic", t_event.topic == "invoice.ready")

    t_manual = Trigger(kind=TriggerKind.MANUAL, authorized=["lct:web4:human:CFO"])
    check("T2.6 Manual authorized", len(t_manual.authorized) == 1)

    # ── T3: Agent Plan ──
    print("T3: Agent Plan (§2.1)")

    plan = AgentPlan(
        plan_id="acp:plan:invoice-processor",
        principal="lct:web4:entity:CLIENT",
        agent="lct:web4:entity:AGENT",
        grant_id="agy:grant:invoice-authority",
        triggers=[t_cron, t_event, t_manual],
        steps=[
            PlanStep(step_id="fetch", mcp="invoice.search", args={"status": "ready", "limit": 100}),
            PlanStep(step_id="validate", mcp="invoice.validate", args={"rules": "standard"}, depends_on=["fetch"]),
            PlanStep(step_id="approve", mcp="invoice.approve", args={"threshold": 25},
                     depends_on=["validate"], requires_approval="if_amount > 10"),
        ],
        guards=PlanGuards(
            law_hash="sha256:abc",
            resource_caps=ResourceCaps(max_atp=25, max_executions=100, rate_limit="10/hour"),
            witness_level=2,
            human_approval=HumanApprovalConfig(mode="auto-if<=10 else prompt", timeout=3600, fallback="deny"),
        ),
        expires_at="2027-01-01T00:00:00Z",
    )

    check("T3.1 Plan ID", plan.plan_id == "acp:plan:invoice-processor")
    check("T3.2 Principal", plan.principal == "lct:web4:entity:CLIENT")
    check("T3.3 Agent", plan.agent == "lct:web4:entity:AGENT")
    check("T3.4 3 triggers", len(plan.triggers) == 3)
    check("T3.5 3 steps", len(plan.steps) == 3)
    check("T3.6 Grant ID", plan.grant_id == "agy:grant:invoice-authority")
    check("T3.7 Not expired", not plan.is_expired())
    check("T3.8 Resource caps ATP", plan.guards.resource_caps.max_atp == 25)
    check("T3.9 Witness level", plan.guards.witness_level == 2)
    check("T3.10 Human approval mode", "auto" in plan.guards.human_approval.mode)

    # Step dependencies
    check("T3.11 Step fetch no deps", len(plan.steps[0].depends_on) == 0)
    check("T3.12 Step validate depends on fetch", plan.steps[1].depends_on == ["fetch"])
    check("T3.13 Step approve requires approval", plan.steps[2].requires_approval != "")

    # Expired plan
    expired_plan = AgentPlan(expires_at="2020-01-01T00:00:00Z")
    check("T3.14 Expired plan detected", expired_plan.is_expired())

    # ── T4: ACP State Machine ──
    print("T4: ACP State Machine (§3)")

    sm = ACPStateMachine()
    check("T4.1 Starts idle", sm.state == ACPState.IDLE)
    check("T4.2 Not terminal", not sm.is_terminal)

    # Happy path: idle → planning → intent_created → law_check → approval → executing → recording → complete
    check("T4.3 Can go to planning", sm.can_transition(ACPState.PLANNING))
    sm.transition(ACPState.PLANNING, "cron trigger")
    check("T4.4 In planning", sm.state == ACPState.PLANNING)

    sm.transition(ACPState.INTENT_CREATED, "intent generated")
    check("T4.5 Intent created", sm.state == ACPState.INTENT_CREATED)

    sm.transition(ACPState.LAW_CHECK, "law passed")
    check("T4.6 Law check", sm.state == ACPState.LAW_CHECK)

    sm.transition(ACPState.APPROVAL_GATE, "agency valid")
    check("T4.7 Approval gate", sm.state == ACPState.APPROVAL_GATE)

    sm.transition(ACPState.EXECUTING, "approved")
    check("T4.8 Executing", sm.state == ACPState.EXECUTING)

    sm.transition(ACPState.RECORDING, "execution done")
    check("T4.9 Recording", sm.state == ACPState.RECORDING)

    sm.transition(ACPState.COMPLETE, "recorded")
    check("T4.10 Complete", sm.state == ACPState.COMPLETE)
    check("T4.11 Terminal", sm.is_terminal)
    check("T4.12 History length", len(sm.history) == 8)

    # Failure from any state
    sm2 = ACPStateMachine()
    sm2.transition(ACPState.PLANNING)
    sm2.transition(ACPState.FAILED, "error")
    check("T4.13 Failed terminal", sm2.is_terminal)

    # Cannot skip states
    sm3 = ACPStateMachine()
    check("T4.14 Cannot skip to executing", not sm3.can_transition(ACPState.EXECUTING))

    # ── T5: Agency Grant ──
    print("T5: Agency Grant (§4)")

    grant = AgencyGrant(
        grant_id="agy:grant:invoice-authority",
        principal="lct:web4:entity:CLIENT",
        agent="lct:web4:entity:AGENT",
        scope=["invoice.*"],
        resource_caps=ResourceCaps(max_atp=25, max_executions=100),
        witness_level=2,
        expires_at="2027-01-01T00:00:00Z",
    )
    check("T5.1 Grant ID", grant.grant_id == "agy:grant:invoice-authority")
    check("T5.2 Not expired", not grant.is_expired())
    check("T5.3 Not revoked", not grant.revoked)
    check("T5.4 Scope wildcard", "invoice.*" in grant.scope)

    # Expired grant
    expired_grant = AgencyGrant(expires_at="2020-01-01T00:00:00Z")
    check("T5.5 Expired grant", expired_grant.is_expired())

    # ── T6: Scope Validation ──
    print("T6: Scope Validation (§4)")

    check("T6.1 Wildcard match", within_scope({"mcp": "invoice.search"}, ["invoice.*"]))
    check("T6.2 Wildcard match 2", within_scope({"mcp": "invoice.approve"}, ["invoice.*"]))
    check("T6.3 Exact match", within_scope({"mcp": "invoice.search"}, ["invoice.search"]))
    check("T6.4 No match", not within_scope({"mcp": "payment.process"}, ["invoice.*"]))
    check("T6.5 Empty scope", not within_scope({"mcp": "anything"}, []))
    check("T6.6 Multiple scopes", within_scope({"mcp": "payment.send"}, ["invoice.*", "payment.*"]))

    # ── T7: Resource Caps ──
    print("T7: Resource Caps (§4)")

    intent = Intent(proposed_action={"mcp": "test", "args": {"atp": 30}})
    caps = ResourceCaps(max_atp=25, max_executions=10)
    check("T7.1 ATP exceeded", exceeds_caps(intent, caps))

    intent2 = Intent(proposed_action={"mcp": "test", "args": {"atp": 20}})
    check("T7.2 ATP within", not exceeds_caps(intent2, caps))

    check("T7.3 Execution count exceeded", exceeds_caps(intent2, caps, executions_today=10))
    check("T7.4 Execution count within", not exceeds_caps(intent2, caps, executions_today=9))

    # ── T8: Agency Validation ──
    print("T8: Agency Validation (§4)")

    grants = {"agy:grant:invoice-authority": grant}

    valid_intent = Intent(
        proposed_action={"mcp": "invoice.search", "args": {"atp": 10}},
    )
    check("T8.1 Valid agency", validate_acp_agency(plan, valid_intent, grants))

    # Invalid: no grant
    bad_plan = AgentPlan(grant_id="agy:nonexistent")
    try:
        validate_acp_agency(bad_plan, valid_intent, grants)
        check("T8.2 No grant raises", False)
    except NoValidGrant:
        check("T8.2 No grant raises", True)

    # Invalid: scope violation
    bad_intent = Intent(proposed_action={"mcp": "payment.process"})
    try:
        validate_acp_agency(plan, bad_intent, grants)
        check("T8.3 Scope violation raises", False)
    except ScopeViolation:
        check("T8.3 Scope violation raises", True)

    # Invalid: revoked
    revoked_grant = AgencyGrant(grant_id="revoked", revoked=True, scope=["*"])
    try:
        validate_acp_agency(
            AgentPlan(grant_id="revoked"), valid_intent, {"revoked": revoked_grant}
        )
        check("T8.4 Revoked grant raises", False)
    except NoValidGrant:
        check("T8.4 Revoked grant raises", True)

    # ── T9: Law Compliance ──
    print("T9: Law Compliance (§5)")

    law = LawConfig(
        law_hash="sha256:law001",
        allowed_triggers=["cron", "event", "manual"],
        max_atp_per_plan=100,
        min_witness_level=1,
    )
    check("T9.1 Law compliance passes", check_law_compliance(plan, law))

    # Trigger not allowed
    restricted_law = LawConfig(allowed_triggers=["cron"])
    plan_with_event = AgentPlan(
        triggers=[Trigger(kind=TriggerKind.EVENT, topic="test")],
        guards=PlanGuards(resource_caps=ResourceCaps(max_atp=10), witness_level=1),
    )
    try:
        check_law_compliance(plan_with_event, restricted_law)
        check("T9.2 Illegal trigger raises", False)
    except IllegalTrigger:
        check("T9.2 Illegal trigger raises", True)

    # ATP cap exceeds law
    atp_plan = AgentPlan(
        triggers=[Trigger(kind=TriggerKind.CRON)],
        guards=PlanGuards(resource_caps=ResourceCaps(max_atp=200), witness_level=1),
    )
    try:
        check_law_compliance(atp_plan, LawConfig(max_atp_per_plan=100, min_witness_level=1))
        check("T9.3 ATP cap exceeded raises", False)
    except ResourceCapExceeded:
        check("T9.3 ATP cap exceeded raises", True)

    # Witness deficit
    low_witness_plan = AgentPlan(
        triggers=[Trigger(kind=TriggerKind.CRON)],
        guards=PlanGuards(resource_caps=ResourceCaps(max_atp=10), witness_level=0),
    )
    try:
        check_law_compliance(low_witness_plan, LawConfig(min_witness_level=2))
        check("T9.4 Witness deficit raises", False)
    except WitnessDeficit:
        check("T9.4 Witness deficit raises", True)

    # ── T10: Witness Requirements ──
    print("T10: Witness Requirements (§5.2)")

    wr = WitnessRequirement(
        level=2, types=["time", "audit"],
        quorum_model="byzantine", quorum_threshold=0.67,
        timeout=300, fallback="abort",
    )
    check("T10.1 Level 2", wr.level == 2)
    check("T10.2 Types", wr.types == ["time", "audit"])
    check("T10.3 Byzantine model", wr.quorum_model == "byzantine")
    check("T10.4 Threshold 0.67", wr.quorum_threshold == 0.67)
    check("T10.5 Timeout 300s", wr.timeout == 300)
    check("T10.6 Fallback abort", wr.fallback == "abort")

    # ── T11: Human Console ──
    print("T11: Human Console (§6)")

    approval_req = ApprovalRequest(
        intent=valid_intent,
        plan=plan,
        risk_assessment=RiskProfile(level="low", factors=["within_threshold"]),
        explanation={"summary": "Auto-approve within limits"},
        urgency="low",
        deadline="2026-01-01T00:00:00Z",
    )
    check("T11.1 Approval request created", approval_req.intent is not None)
    check("T11.2 Risk low", approval_req.risk_assessment.level == "low")
    check("T11.3 Urgency low", approval_req.urgency == "low")

    dash = DashboardState(
        active_plans=12, pending_intents=3, executions_today=147,
        success_rate=0.98, atp_consumed=523,
        trust_trend={"agent": {"t3": 0.05, "period": "7d"}},
        alerts=[{"level": "warning", "message": "Approaching ATP cap"}],
    )
    check("T11.4 Dashboard active plans", dash.active_plans == 12)
    check("T11.5 Dashboard success rate", dash.success_rate == 0.98)
    check("T11.6 Dashboard has alerts", len(dash.alerts) == 1)

    # ── T12: Security Layers ──
    print("T12: Security Model (§7)")

    check("T12.1 5 security layers", len(SecurityLayer) == 5)
    check("T12.2 Agency layer", SecurityLayer.AGENCY.value == "agency")
    check("T12.3 Law layer", SecurityLayer.LAW.value == "law")
    check("T12.4 Approval layer", SecurityLayer.APPROVAL.value == "approval")
    check("T12.5 Witness layer", SecurityLayer.WITNESS.value == "witness")
    check("T12.6 Audit layer", SecurityLayer.AUDIT.value == "audit")

    check("T12.7 5 threat mitigations", len(THREAT_MAP) == 5)
    threat_names = [t.threat for t in THREAT_MAP]
    check("T12.8 Runaway automation", "runaway_automation" in threat_names)
    check("T12.9 Replay attacks", "replay_attacks" in threat_names)
    check("T12.10 Trust gaming", "trust_gaming" in threat_names)

    # ── T13: MRH Integration ──
    print("T13: MRH Integration (§8)")

    check("T13.1 9 ACP predicates", len(ACP_PREDICATES) == 9)
    check("T13.2 hasAgent predicate", "acp:hasAgent" in ACP_PREDICATES)
    check("T13.3 witnessedBy predicate", "acp:witnessedBy" in ACP_PREDICATES)

    triples = generate_plan_triples(plan)
    check("T13.4 Plan generates 3 triples", len(triples) == 3)
    check("T13.5 First triple has agent", "acp:hasAgent" in triples[0].predicate)
    check("T13.6 Turtle format", triples[0].to_turtle().endswith(" ."))

    record = ExecutionRecord(
        record_id="acp:record:test01",
        witnesses=["witness_a", "witness_b"],
    )
    exec_triples = generate_execution_triples(record, "agent01")
    check("T13.7 Execution generates 3 triples", len(exec_triples) == 3)
    check("T13.8 executedBy triple", "acp:executedBy" in exec_triples[0].predicate)

    # ── T14: Full ACP Engine Lifecycle ──
    print("T14: Full ACP Engine Lifecycle")

    engine = ACPEngine()

    # Register grant
    engine.register_grant(grant)

    # Register plan
    sm = engine.register_plan(plan)
    check("T14.1 Plan registered", plan.plan_id in engine.plans)
    check("T14.2 SM created", sm.state == ACPState.IDLE)
    check("T14.3 Dashboard updated", engine.dashboard.active_plans == 1)

    # Trigger plan
    intent = engine.trigger_plan(plan.plan_id, t_cron)
    check("T14.4 Intent created", intent is not None)
    check("T14.5 Intent has ID", intent.intent_id.startswith("acp:intent:"))
    check("T14.6 Intent has PoA", intent.proof_of_agency is not None)
    check("T14.7 SM at intent_created", sm.state == ACPState.INTENT_CREATED)
    check("T14.8 Pending intents 1", engine.dashboard.pending_intents == 1)

    # Law check + agency validation
    ok = engine.law_check(intent.intent_id, law)
    check("T14.9 Law check passed", ok)
    check("T14.10 SM at approval gate", sm.state == ACPState.APPROVAL_GATE)

    # Approve
    decision = engine.decide(
        intent.intent_id, "approve", "lct:web4:human:CFO",
        rationale="Within limits", witnesses=["witness_a", "witness_b"],
    )
    check("T14.11 Decision created", decision is not None)
    check("T14.12 Decision approved", decision.decision == "approve")
    check("T14.13 SM at executing", sm.state == ACPState.EXECUTING)

    # Execute
    record = engine.execute(intent.intent_id)
    check("T14.14 Record created", record is not None)
    check("T14.15 Record has ID", record.record_id.startswith("acp:record:"))
    check("T14.16 Result success", record.result["status"] == "success")
    check("T14.17 T3V3 delta", record.t3v3_delta.agent_t3["temperament"] == 0.01)
    check("T14.18 Witnesses", len(record.witnesses) == 2)
    check("T14.19 Ledger inclusion", "hash" in record.ledger_inclusion)
    check("T14.20 SM complete", sm.state == ACPState.COMPLETE)
    check("T14.21 Execution count", engine.execution_counts[plan.plan_id] == 1)

    # Dashboard
    dash = engine.get_dashboard()
    check("T14.22 Dashboard executions", dash.executions_today == 1)
    check("T14.23 Dashboard success rate", dash.success_rate == 1.0)

    # ── T15: Denial Path ──
    print("T15: Denial Path")

    engine2 = ACPEngine()
    engine2.register_grant(grant)

    deny_plan = AgentPlan(
        plan_id="acp:plan:deny-test",
        principal="lct:web4:entity:CLIENT",
        agent="lct:web4:entity:AGENT",
        grant_id="agy:grant:invoice-authority",
        triggers=[t_manual],
        steps=[PlanStep(step_id="action", mcp="invoice.delete", args={})],
        guards=PlanGuards(resource_caps=ResourceCaps(max_atp=10), witness_level=1),
    )
    sm2 = engine2.register_plan(deny_plan)
    intent2 = engine2.trigger_plan(deny_plan.plan_id, t_manual)
    engine2.law_check(intent2.intent_id, law)

    decision2 = engine2.decide(
        intent2.intent_id, "deny", "lct:web4:human:CFO",
        rationale="Too dangerous",
    )
    check("T15.1 Decision deny", decision2.decision == "deny")
    check("T15.2 SM failed", sm2.state == ACPState.FAILED)
    check("T15.3 Terminal", sm2.is_terminal)

    # Cannot execute after denial
    record2 = engine2.execute(intent2.intent_id)
    check("T15.4 Cannot execute after deny", record2 is None)

    # ── T16: Expired Plan ──
    print("T16: Expired Plan")

    engine3 = ACPEngine()
    engine3.register_grant(grant)

    expired_p = AgentPlan(
        plan_id="acp:plan:expired",
        agent="lct:web4:entity:AGENT",
        grant_id="agy:grant:invoice-authority",
        triggers=[t_cron],
        steps=[PlanStep(step_id="action", mcp="invoice.search")],
        expires_at="2020-01-01T00:00:00Z",
    )
    sm3 = engine3.register_plan(expired_p)

    try:
        engine3.trigger_plan(expired_p.plan_id, t_cron)
        check("T16.1 Expired plan raises", False)
    except PlanExpired:
        check("T16.1 Expired plan raises", True)
    check("T16.2 SM failed", sm3.state == ACPState.FAILED)

    # ── T17: Error Recovery ──
    print("T17: Error Recovery (§10.2)")

    test_engine = ACPEngine()
    check("T17.1 Approval escalation",
          test_engine.handle_error("test", ApprovalRequired()) == "escalate_to_human")
    check("T17.2 Witness wait",
          test_engine.handle_error("test", WitnessDeficit()) == "wait_for_witnesses")
    check("T17.3 Scope expansion",
          test_engine.handle_error("test", ScopeViolation()) == "request_grant_expansion")
    check("T17.4 Ledger retry",
          test_engine.handle_error("test", LedgerWriteFailure()) == "retry_with_backoff")
    check("T17.5 Generic abort",
          test_engine.handle_error("test", ACPError()) == "abort_plan")

    # ── T18: Intent Structure ──
    print("T18: Intent Structure (§2.2)")

    intent_full = Intent(
        intent_id="acp:intent:test123",
        plan_id="acp:plan:test",
        proposed_action={"mcp": "invoice.approve", "args": {"id": "INV-123", "amount": 9.5}},
        proof_of_agency=ProofOfAgency(
            grant_id="agy:grant:test",
            plan_id="acp:plan:test",
            nonce="unique-nonce-123",
            audience=["mcp:invoice/*"],
            expires_at="2027-01-01T00:00:00Z",
        ),
        explain={
            "why": "Invoice matches auto-approval criteria",
            "confidence": 0.95,
            "alternatives": ["route_to_manual", "request_clarification"],
            "riskAssessment": "low",
        },
        needs_approval=False,
        created_at="2025-09-15T15:30:00Z",
    )
    check("T18.1 Intent ID", intent_full.intent_id == "acp:intent:test123")
    check("T18.2 MCP call", intent_full.proposed_action["mcp"] == "invoice.approve")
    check("T18.3 PoA nonce", intent_full.proof_of_agency.nonce == "unique-nonce-123")
    check("T18.4 Confidence", intent_full.explain["confidence"] == 0.95)
    check("T18.5 2 alternatives", len(intent_full.explain["alternatives"]) == 2)
    check("T18.6 No approval needed", not intent_full.needs_approval)

    # ── T19: Decision Structure ──
    print("T19: Decision Structure (§2.3)")

    decision_full = Decision(
        intent_id="acp:intent:test123",
        decision="approve",
        by="lct:web4:entity:AUTO-APPROVER",
        rationale="Within auto-approval limits",
        witnesses=["lct:web4:witness:A", "lct:web4:witness:B"],
        timestamp="2025-09-15T15:30:05Z",
    )
    check("T19.1 Decision approve", decision_full.decision == "approve")
    check("T19.2 Auto-approver", "AUTO-APPROVER" in decision_full.by)
    check("T19.3 2 witnesses", len(decision_full.witnesses) == 2)

    # Modify decision
    modify_decision = Decision(
        intent_id="test", decision="modify",
        modifications={"args": {"amount": 5.0}},
        by="lct:web4:human:CFO",
    )
    check("T19.4 Modify decision", modify_decision.decision == "modify")
    check("T19.5 Has modifications", modify_decision.modifications is not None)

    # ── T20: Execution Record ──
    print("T20: Execution Record (§2.4)")

    exec_record = ExecutionRecord(
        record_id="acp:record:exec001",
        intent_id="acp:intent:test123",
        grant_id="agy:grant:test",
        law_hash="sha256:law001",
        mcp_call={"resource": "invoice.approve", "args": {"id": "INV-123"}},
        result={"status": "success", "output": {"tx": "bank#789"}},
        t3v3_delta=T3V3Delta(
            agent_t3={"temperament": 0.01},
            client_v3={"value": 0.02},
        ),
        witnesses=["lct:web4:witness:A"],
        ledger_inclusion={"hash": "0xabc", "block": 12346},
    )
    check("T20.1 Record ID", exec_record.record_id == "acp:record:exec001")
    check("T20.2 Result success", exec_record.result["status"] == "success")
    check("T20.3 Agent T3 delta", exec_record.t3v3_delta.agent_t3["temperament"] == 0.01)
    check("T20.4 Client V3 delta", exec_record.t3v3_delta.client_v3["value"] == 0.02)
    check("T20.5 Ledger block", exec_record.ledger_inclusion["block"] == 12346)

    # ── T21: Implementation Requirements ──
    print("T21: Implementation Requirements (§9)")

    # Verify engine satisfies MUST requirements
    # 1. Valid agency grant required
    engine_must = ACPEngine()
    no_grant_plan = AgentPlan(
        plan_id="must-test", grant_id="nonexistent",
        triggers=[t_cron], steps=[PlanStep(step_id="s1", mcp="test")],
        guards=PlanGuards(resource_caps=ResourceCaps(max_atp=10), witness_level=1),
    )
    sm_must = engine_must.register_plan(no_grant_plan)
    intent_must = engine_must.trigger_plan(no_grant_plan.plan_id, t_cron)
    ok = engine_must.law_check(intent_must.intent_id, law)
    check("T21.1 MUST: Agency validation", not ok)
    check("T21.2 SM failed on no grant", sm_must.state == ACPState.FAILED)

    # 2. Ledger recording (execution records have ledger_inclusion)
    check("T21.3 MUST: Ledger inclusion present", "hash" in record.ledger_inclusion)

    # 3. Proof of agency included
    check("T21.4 MUST: PoA in intent", intent_full.proof_of_agency is not None)

    # 4. Witness attestation
    check("T21.5 MUST: Witnesses in record", len(record.witnesses) > 0)

    # ── T22: Empty Plan ──
    print("T22: Edge Cases")

    empty_engine = ACPEngine()
    empty_engine.register_grant(grant)

    empty_plan = AgentPlan(
        plan_id="empty", grant_id="agy:grant:invoice-authority",
        triggers=[t_cron], steps=[],
        guards=PlanGuards(resource_caps=ResourceCaps(max_atp=10), witness_level=1),
    )
    sm_empty = empty_engine.register_plan(empty_plan)
    result = empty_engine.trigger_plan(empty_plan.plan_id, t_cron)
    check("T22.1 Empty plan returns None", result is None)
    check("T22.2 SM failed", sm_empty.state == ACPState.FAILED)

    # Trigger non-existent plan
    result2 = empty_engine.trigger_plan("nonexistent", t_cron)
    check("T22.3 Nonexistent plan returns None", result2 is None)

    # Double trigger
    plan2 = AgentPlan(
        plan_id="double", grant_id="agy:grant:invoice-authority",
        triggers=[t_cron], steps=[PlanStep(step_id="s1", mcp="invoice.search")],
        guards=PlanGuards(resource_caps=ResourceCaps(max_atp=10), witness_level=1),
    )
    sm_double = empty_engine.register_plan(plan2)
    empty_engine.trigger_plan(plan2.plan_id, t_cron)
    result3 = empty_engine.trigger_plan(plan2.plan_id, t_cron)
    check("T22.4 Double trigger returns None (not idle)", result3 is None)

    # ── Summary ──
    print(f"\n{'='*60}")
    print(f"ACP Framework: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  {failed} FAILED")
    else:
        print("  All checks passed!")
    print(f"{'='*60}")

    return passed, total


if __name__ == "__main__":
    run_tests()
