#!/usr/bin/env python3
"""
PolicyGate IRP Plugin — SOIA-SAGE Convergence Implementation
=============================================================

PolicyGate wraps PolicyEntity.evaluate() as an IRP (Iterative Refinement
Protocol) energy function, making policy evaluation a first-class participant
in the consciousness loop.

Key insight: PolicyEntity is itself a specialized SAGE stack — a "plugin of
plugins." The IRP contract is self-similar at three nested scales:
  1. Outer: SAGE consciousness loop (PolicyGate is one plugin among many)
  2. Middle: PolicyGate evaluation (rule_matching → energy_scoring → filtering)
  3. Inner: Ambiguous case handling (advisory for WARN-level decisions)

CRISIS mode changes the ACCOUNTABILITY EQUATION, not policy strictness.
Policy rules stay identical. What changes is how the decision is RECORDED —
with duress context acknowledging conditions were beyond the agent's control.

Implements:
- IRP contract: init_state / step / energy / project / halt
- AccountabilityFrame: NORMAL / DEGRADED / DURESS
- PolicyEvaluation with accountability_frame + duress_context
- Energy function: compliance score (0=compliant, >0=violation magnitude)
- Integration with TeamPolicy, TeamHeartbeat metabolic states, and R7 actions
- Hash-chained evaluation ledger for audit trail

Design decision: docs/history/design_decisions/POLICY-ENTITY-REPOSITIONING.md
SOIA mapping: SOIA's IRP maps to SAGE's consciousness loop
Date: 2026-02-21
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from web4_entity import T3Tensor, V3Tensor, ATPBudget


# ═══════════════════════════════════════════════════════════════
# Accountability Frame — Metabolic context for policy decisions
# ═══════════════════════════════════════════════════════════════

class AccountabilityFrame(Enum):
    """
    Accountability context for policy evaluation.

    NORMAL:   Standard accountability — agent chose outcome.
              Active during WAKE and FOCUS metabolic states.
    DEGRADED: Reduced capabilities acknowledged.
              Active during REST and DREAM metabolic states.
    DURESS:   Fight-or-flight — consequences beyond control.
              Active during CRISIS metabolic state.

    CRITICAL: DURESS does NOT change policy rules — only how the
    decision is RECORDED. Both "freeze" and "fight" are valid under duress.
    """
    NORMAL = "normal"
    DEGRADED = "degraded"
    DURESS = "duress"


# Map metabolic states to accountability frames
METABOLIC_TO_ACCOUNTABILITY = {
    "wake": AccountabilityFrame.NORMAL,
    "focus": AccountabilityFrame.NORMAL,
    "rest": AccountabilityFrame.DEGRADED,
    "dream": AccountabilityFrame.DEGRADED,
    "crisis": AccountabilityFrame.DURESS,
}


# ═══════════════════════════════════════════════════════════════
# Policy Decision and Evaluation
# ═══════════════════════════════════════════════════════════════

class PolicyDecision(Enum):
    """Policy evaluation outcome."""
    ALLOW = "allow"
    DENY = "deny"
    WARN = "warn"     # Allowed but flagged for review
    DEFER = "defer"   # Needs multi-sig or higher authority


@dataclass
class PolicyConstraint:
    """A single policy constraint with violation weight."""
    rule_id: str
    rule_name: str
    weight: float = 1.0           # Contribution to energy function
    category: str = "general"     # rbac, cost, threshold, custom


@dataclass
class PolicyEvaluation:
    """
    Full policy evaluation result with SAGE integration fields.

    Backward compatible: accountability_frame defaults to "normal",
    duress_context defaults to None.
    """
    decision: PolicyDecision
    rule_id: Optional[str] = None
    rule_name: Optional[str] = None
    reason: str = ""
    enforced: bool = True
    constraints_applied: List[PolicyConstraint] = field(default_factory=list)
    constraints_violated: List[PolicyConstraint] = field(default_factory=list)

    # Enterprise governance
    requires_approval: bool = False
    atp_cost: float = 0.0

    # SAGE PolicyGate integration
    accountability_frame: str = "normal"
    duress_context: Optional[Dict[str, Any]] = None

    # Energy score (for IRP convergence)
    energy_score: float = 0.0     # 0=compliant, >0=violations

    # Audit trail
    timestamp: str = ""
    evaluation_hash: str = ""

    def to_dict(self) -> dict:
        return {
            "decision": self.decision.value,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "reason": self.reason,
            "enforced": self.enforced,
            "constraints_applied": len(self.constraints_applied),
            "constraints_violated": len(self.constraints_violated),
            "requires_approval": self.requires_approval,
            "atp_cost": self.atp_cost,
            "accountability_frame": self.accountability_frame,
            "duress_context": self.duress_context,
            "energy_score": self.energy_score,
            "timestamp": self.timestamp,
            "evaluation_hash": self.evaluation_hash,
        }


# ═══════════════════════════════════════════════════════════════
# Policy Rules — Configurable constraint definitions
# ═══════════════════════════════════════════════════════════════

@dataclass
class PolicyRule:
    """A policy rule with evaluation logic."""
    rule_id: str
    rule_name: str
    category: str = "general"
    weight: float = 1.0
    # Callable: (action_type, actor_role, params, context) -> (pass, reason)
    evaluator: Optional[Callable] = None

    def evaluate(self, action_type: str, actor_role: str,
                 params: Dict, context: Dict) -> Tuple[bool, str]:
        """Evaluate this rule. Returns (passed, reason)."""
        if self.evaluator:
            return self.evaluator(action_type, actor_role, params, context)
        return True, "no evaluator configured"


# ═══════════════════════════════════════════════════════════════
# PolicyGate IRP Plugin
# ═══════════════════════════════════════════════════════════════

class PolicyGateIRP:
    """
    IRP plugin wrapping policy evaluation as energy function.

    Implements the 5-method IRP contract:
      init_state → step → energy → project → halt

    The energy function returns compliance score:
      0 = fully compliant (converged)
      >0 = violation magnitude (needs refinement)

    PolicyGate is itself a specialized SAGE stack — fractal self-similarity:
      Outer:  SAGE consciousness loop (PolicyGate is one plugin)
      Middle: PolicyGate evaluation (rule matching → energy scoring)
      Inner:  Advisory for ambiguous cases (WARN-level decisions)
    """

    def __init__(self, rules: List[PolicyRule] = None,
                 trust_threshold: float = 0.3,
                 atp_threshold: float = 5.0):
        self.rules = rules or self._default_rules()
        self.trust_threshold = trust_threshold
        self.atp_threshold = atp_threshold

        # Evaluation ledger (hash-chained)
        self.evaluations: List[PolicyEvaluation] = []
        self._chain_head: str = "genesis"

        # IRP iteration tracking
        self._iterations = 0
        self._max_iterations = 10
        self._convergence_threshold = 0.01

    # ─── IRP Contract: 5 lifecycle methods ───

    def init_state(self, context: Dict) -> Dict:
        """
        Initialize policy evaluation context.

        Context should contain:
          - action_type: str
          - actor_role: str
          - actor_lct: str
          - t3: T3Tensor (or dict with talent/training/temperament)
          - atp: ATPBudget (or dict with balance/cap)
          - metabolic_state: str (wake/focus/rest/dream/crisis)
          - policy_version: int
          - team_policy: dict (admin_only, operator_min, action_costs, multi_sig)
          - parameters: dict (action-specific params)
        """
        metabolic = context.get("metabolic_state", "wake")
        frame = METABOLIC_TO_ACCOUNTABILITY.get(metabolic, AccountabilityFrame.NORMAL)

        state = {
            "action_type": context.get("action_type", "unknown"),
            "actor_role": context.get("actor_role", "agent"),
            "actor_lct": context.get("actor_lct", ""),
            "metabolic_state": metabolic,
            "accountability_frame": frame.value,
            "t3_composite": self._extract_t3_composite(context),
            "atp_balance": self._extract_atp_balance(context),
            "policy_version": context.get("policy_version", 1),
            "team_policy": context.get("team_policy", {}),
            "parameters": context.get("parameters", {}),
            "constraints_applied": [],
            "constraints_violated": [],
            "energy": float("inf"),
            "iteration": 0,
            "converged": False,
            "decision": None,
            "duress_context": None,
        }

        # Build duress context if in CRISIS
        if frame == AccountabilityFrame.DURESS:
            state["duress_context"] = {
                "metabolic_state": metabolic,
                "accountability_frame": frame.value,
                "constraint": context.get("crisis_reason", "metabolic crisis"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        self._iterations = 0
        return state

    def step(self, state: Dict) -> Dict:
        """
        Single evaluation step: apply rules, compute compliance.

        Each step refines the evaluation by:
        1. Checking trust threshold (T3 composite)
        2. Checking ATP affordability
        3. Evaluating RBAC constraints
        4. Evaluating custom rules
        5. Computing aggregate energy score
        """
        self._iterations += 1
        state["iteration"] = self._iterations

        applied = []
        violated = []
        action_type = state["action_type"]
        actor_role = state["actor_role"]
        params = state["parameters"]
        team_policy = state["team_policy"]

        # ── Built-in constraints ──

        # 1. Trust threshold
        t3_comp = state["t3_composite"]
        trust_constraint = PolicyConstraint(
            rule_id="trust_threshold",
            rule_name="Minimum T3 composite",
            weight=3.0,
            category="threshold",
        )
        applied.append(trust_constraint)
        if t3_comp < self.trust_threshold:
            violated.append(trust_constraint)

        # 2. ATP affordability
        atp_balance = state["atp_balance"]
        action_costs = team_policy.get("action_costs", {})
        cost = action_costs.get(action_type, 10.0)
        atp_constraint = PolicyConstraint(
            rule_id="atp_affordability",
            rule_name="ATP balance sufficient",
            weight=3.0,   # Hard constraint: can't spend what you don't have
            category="cost",
        )
        applied.append(atp_constraint)
        if atp_balance < cost:
            violated.append(atp_constraint)
        state["atp_cost"] = cost

        # 3. RBAC — admin-only / operator-min checks
        admin_only = set(team_policy.get("admin_only", []))
        operator_min = set(team_policy.get("operator_min", []))

        rbac_constraint = PolicyConstraint(
            rule_id="rbac_authorization",
            rule_name="Role authorization",
            weight=5.0,  # Highest weight — unauthorized access is critical
            category="rbac",
        )
        applied.append(rbac_constraint)
        if action_type in admin_only and actor_role != "admin":
            violated.append(rbac_constraint)
        elif action_type in operator_min and actor_role not in ("admin", "operator"):
            violated.append(rbac_constraint)

        # 4. Multi-sig check
        multi_sig = team_policy.get("multi_sig", {})
        ms_req = multi_sig.get(action_type)
        if ms_req:
            state["requires_approval"] = True

        # 5. Evaluate custom rules
        context = {
            "t3_composite": t3_comp,
            "atp_balance": atp_balance,
            "metabolic_state": state["metabolic_state"],
            "accountability_frame": state["accountability_frame"],
            "policy_version": state["policy_version"],
        }

        for rule in self.rules:
            constraint = PolicyConstraint(
                rule_id=rule.rule_id,
                rule_name=rule.rule_name,
                weight=rule.weight,
                category=rule.category,
            )
            applied.append(constraint)
            passed, reason = rule.evaluate(action_type, actor_role, params, context)
            if not passed:
                violated.append(constraint)

        # ── Compute decision ──
        state["constraints_applied"] = applied
        state["constraints_violated"] = violated

        if len(violated) == 0:
            state["decision"] = PolicyDecision.ALLOW.value
        elif any(c.category == "rbac" for c in violated):
            state["decision"] = PolicyDecision.DENY.value
        elif any(c.weight >= 3.0 for c in violated):
            state["decision"] = PolicyDecision.DENY.value
        else:
            state["decision"] = PolicyDecision.WARN.value

        # Compute energy
        state["energy"] = self.energy(state)
        state["converged"] = state["energy"] <= self._convergence_threshold

        return state

    def energy(self, state: Dict) -> float:
        """
        Return compliance score as energy value for consciousness loop.

        Energy = sum of (violation_weight × category_multiplier)

        Score = 0 means fully compliant (converged).
        Score > 0 means violations exist (needs refinement or denial).

        Category multipliers:
          rbac: ×10 (unauthorized access — catastrophic)
          threshold: ×5 (trust/capability failure)
          cost: ×3 (resource constraint)
          custom: ×2 (policy-specific rules)
          general: ×1
        """
        violated = state.get("constraints_violated", [])
        if not violated:
            return 0.0

        CATEGORY_MULTIPLIER = {
            "rbac": 10.0,
            "threshold": 5.0,
            "cost": 3.0,
            "custom": 2.0,
            "general": 1.0,
        }

        total_energy = 0.0
        for constraint in violated:
            multiplier = CATEGORY_MULTIPLIER.get(constraint.category, 1.0)
            total_energy += constraint.weight * multiplier

        return round(total_energy, 4)

    def project(self, state: Dict) -> Dict:
        """
        Projection for next cycle: what constraints remain active?

        In a full SAGE loop, this would project which constraints
        the agent might resolve (e.g., by acquiring more ATP, or
        requesting role elevation). For reference implementation,
        we return the current constraint state.
        """
        projected = dict(state)
        projected["projected_constraints"] = [
            c.rule_id for c in state.get("constraints_violated", [])
        ]
        return projected

    def halt(self, state: Dict) -> bool:
        """
        Halt condition: policy evaluation complete?

        Halts when:
        1. Energy = 0 (fully compliant, converged)
        2. Decision is DENY (no amount of refinement will fix RBAC)
        3. Max iterations reached
        4. Energy converged (change < threshold)
        """
        if state.get("converged", False):
            return True
        if state.get("decision") == PolicyDecision.DENY.value:
            return True
        if self._iterations >= self._max_iterations:
            return True
        return False

    # ─── High-level evaluate method ───

    def evaluate(self, context: Dict) -> PolicyEvaluation:
        """
        Run the full IRP evaluation loop.

        This is the main entry point: takes an action context,
        runs init_state → step → energy → halt loop, returns
        a PolicyEvaluation with accountability frame.
        """
        state = self.init_state(context)

        # IRP convergence loop
        while not self.halt(state):
            state = self.step(state)
            if self.halt(state):
                break
            state = self.project(state)

        # If we never stepped (already converged/denied), step once
        if state["iteration"] == 0:
            state = self.step(state)

        # Build evaluation result
        evaluation = PolicyEvaluation(
            decision=PolicyDecision(state.get("decision", "deny")),
            rule_id=self._primary_violation_id(state),
            rule_name=self._primary_violation_name(state),
            reason=self._build_reason(state),
            enforced=True,
            constraints_applied=[
                PolicyConstraint(
                    rule_id=c.rule_id, rule_name=c.rule_name,
                    weight=c.weight, category=c.category,
                ) for c in state.get("constraints_applied", [])
            ],
            constraints_violated=[
                PolicyConstraint(
                    rule_id=c.rule_id, rule_name=c.rule_name,
                    weight=c.weight, category=c.category,
                ) for c in state.get("constraints_violated", [])
            ],
            requires_approval=state.get("requires_approval", False),
            atp_cost=state.get("atp_cost", 0.0),
            accountability_frame=state["accountability_frame"],
            duress_context=state.get("duress_context"),
            energy_score=state.get("energy", 0.0),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Compute evaluation hash and chain it
        eval_data = json.dumps(evaluation.to_dict(), sort_keys=True)
        evaluation.evaluation_hash = hashlib.sha256(
            f"{self._chain_head}:{eval_data}".encode()
        ).hexdigest()[:16]
        self._chain_head = evaluation.evaluation_hash

        # Record in evaluation ledger
        self.evaluations.append(evaluation)

        return evaluation

    # ─── Helpers ───

    def _extract_t3_composite(self, context: Dict) -> float:
        """Extract T3 composite from various context formats."""
        t3 = context.get("t3")
        if t3 is None:
            return 0.5  # Default
        if isinstance(t3, T3Tensor):
            return t3.composite()
        if isinstance(t3, dict):
            talent = t3.get("talent", 0.5)
            training = t3.get("training", 0.5)
            temperament = t3.get("temperament", 0.5)
            return 0.4 * talent + 0.3 * training + 0.3 * temperament
        return float(t3)

    def _extract_atp_balance(self, context: Dict) -> float:
        """Extract ATP balance from various context formats."""
        atp = context.get("atp")
        if atp is None:
            return 100.0
        if isinstance(atp, ATPBudget):
            return atp.balance
        if isinstance(atp, dict):
            return atp.get("balance", 100.0)
        return float(atp)

    def _primary_violation_id(self, state: Dict) -> Optional[str]:
        violated = state.get("constraints_violated", [])
        if violated:
            return max(violated, key=lambda c: c.weight).rule_id
        return None

    def _primary_violation_name(self, state: Dict) -> Optional[str]:
        violated = state.get("constraints_violated", [])
        if violated:
            return max(violated, key=lambda c: c.weight).rule_name
        return None

    def _build_reason(self, state: Dict) -> str:
        violated = state.get("constraints_violated", [])
        decision = state.get("decision", "deny")
        frame = state.get("accountability_frame", "normal")

        if not violated:
            return f"All {len(state.get('constraints_applied', []))} constraints satisfied"

        violation_names = [c.rule_name for c in violated]
        prefix = f"[{frame.upper()}] " if frame != "normal" else ""
        return f"{prefix}{len(violated)} violation(s): {', '.join(violation_names)}"

    def _default_rules(self) -> List[PolicyRule]:
        """Default policy rules based on Web4 governance patterns."""

        def high_risk_requires_witnesses(action_type, actor_role, params, context):
            """High-risk actions need witnesses (3+ for admin, 2+ for operator)."""
            witnesses = params.get("witnesses", 0)
            if action_type in ("emergency_shutdown", "rotate_credentials",
                               "approve_deployment"):
                if witnesses < 3:
                    return False, f"High-risk action requires 3+ witnesses, got {witnesses}"
            return True, ""

        def degraded_blocks_admin(action_type, actor_role, params, context):
            """Admin actions blocked in degraded accountability (REST/DREAM)."""
            frame = context.get("accountability_frame", "normal")
            if frame == "degraded" and action_type in (
                "add_member", "remove_member", "update_policy",
                "grant_role", "revoke_role"
            ):
                return False, f"Admin action '{action_type}' blocked in {frame} frame"
            return True, ""

        return [
            PolicyRule(
                rule_id="witness_requirement",
                rule_name="Witness requirement for high-risk actions",
                category="custom",
                weight=2.0,
                evaluator=high_risk_requires_witnesses,
            ),
            PolicyRule(
                rule_id="degraded_admin_block",
                rule_name="Admin actions blocked in degraded state",
                category="custom",
                weight=1.5,
                evaluator=degraded_blocks_admin,
            ),
        ]

    # ─── Analytics ───

    def evaluation_summary(self) -> Dict:
        """Summary statistics over all evaluations."""
        if not self.evaluations:
            return {"total": 0}

        total = len(self.evaluations)
        by_decision = {}
        by_frame = {}
        total_energy = 0.0

        for e in self.evaluations:
            by_decision[e.decision.value] = by_decision.get(e.decision.value, 0) + 1
            by_frame[e.accountability_frame] = by_frame.get(e.accountability_frame, 0) + 1
            total_energy += e.energy_score

        return {
            "total": total,
            "by_decision": by_decision,
            "by_frame": by_frame,
            "avg_energy": round(total_energy / total, 4),
            "chain_head": self._chain_head,
        }


# ═══════════════════════════════════════════════════════════════
# PolicyEntity — 15th entity type in Web4 taxonomy
# ═══════════════════════════════════════════════════════════════

class PolicyEntity:
    """
    PolicyEntity: the 15th primary entity type.

    Mode: Responsive/Delegative
    Energy pattern: Active
    LCT format: policy:<name>:<version>:<hash>

    Immutable once registered — updates create new entities.
    Trust built through: evaluation consistency, convergence quality,
    low false-positive/false-negative rates, witness attestations.
    """

    def __init__(self, name: str, version: int = 1,
                 gate: PolicyGateIRP = None,
                 team_policy: Dict = None):
        self.name = name
        self.version = version
        self.gate = gate or PolicyGateIRP()
        self.team_policy = team_policy or {}

        # Entity identity
        self._content_hash = self._compute_hash()
        self.lct = f"policy:{name}:{version}:{self._content_hash[:8]}"

        # Trust metrics (T3 for policy entity)
        self.t3 = T3Tensor()  # Starts at default (0.5, 0.5, 0.5)
        self.evaluations_count = 0
        self.consistency_score = 1.0  # Starts perfect, degrades on inconsistency

    def _compute_hash(self) -> str:
        data = json.dumps({
            "name": self.name,
            "version": self.version,
            "team_policy": self.team_policy,
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def evaluate_action(self, context: Dict) -> PolicyEvaluation:
        """Evaluate an action through this policy entity's gate."""
        # Inject team_policy into context
        ctx = dict(context)
        ctx["team_policy"] = self.team_policy
        ctx["policy_version"] = self.version

        evaluation = self.gate.evaluate(ctx)
        self.evaluations_count += 1

        # Update consistency: if decision changed for same inputs, degrade
        # (simplified — real version would compare with historical evaluations)

        return evaluation

    def upgrade(self, new_team_policy: Dict) -> "PolicyEntity":
        """Create a new version with updated policy (immutability preserved)."""
        return PolicyEntity(
            name=self.name,
            version=self.version + 1,
            gate=self.gate,
            team_policy=new_team_policy,
        )

    def to_dict(self) -> dict:
        return {
            "lct": self.lct,
            "name": self.name,
            "version": self.version,
            "content_hash": self._content_hash,
            "evaluations_count": self.evaluations_count,
            "consistency_score": self.consistency_score,
            "t3": {"talent": self.t3.talent, "training": self.t3.training,
                    "temperament": self.t3.temperament},
        }


# ═══════════════════════════════════════════════════════════════
# Demo + Verification
# ═══════════════════════════════════════════════════════════════

def run_demo():
    """Demonstrate PolicyGate IRP with multiple scenarios."""
    print("=" * 70)
    print("  POLICYGATE IRP PLUGIN — SOIA-SAGE CONVERGENCE")
    print("  Accountability Frames + Energy Function + IRP Contract")
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

    # ── Setup ──
    # Create a team policy based on Hardbound defaults
    team_policy = {
        "admin_only": ["add_member", "remove_member", "update_policy",
                       "grant_role", "revoke_role", "set_atp_limit",
                       "approve_deployment", "emergency_shutdown",
                       "rotate_credentials", "set_resource_limit"],
        "operator_min": ["deploy_staging", "run_migration", "scale_service",
                         "update_config", "restart_service"],
        "action_costs": {
            "emergency_shutdown": 50.0,
            "approve_deployment": 25.0,
            "run_analysis": 5.0,
            "review_pr": 5.0,
            "deploy_staging": 20.0,
        },
        "multi_sig": {
            "emergency_shutdown": {"required": 2, "eligible_roles": ["admin", "operator"]},
            "rotate_credentials": {"required": 2, "eligible_roles": ["admin"]},
        },
    }

    policy_entity = PolicyEntity(
        name="team-alpha-governance",
        version=1,
        team_policy=team_policy,
    )

    # ── Test 1: Normal agent action (should ALLOW) ──
    print("\n── Test 1: Normal Agent Action (WAKE state) ──")
    eval1 = policy_entity.evaluate_action({
        "action_type": "run_analysis",
        "actor_role": "agent",
        "actor_lct": "lct:agent:alice",
        "t3": {"talent": 0.6, "training": 0.7, "temperament": 0.5},
        "atp": {"balance": 100.0},
        "metabolic_state": "wake",
    })
    print(f"  Decision: {eval1.decision.value}, Energy: {eval1.energy_score}")
    print(f"  Frame: {eval1.accountability_frame}, Cost: {eval1.atp_cost}")
    check("T1: Agent allowed to run_analysis", eval1.decision == PolicyDecision.ALLOW)
    check("T1: Normal accountability frame", eval1.accountability_frame == "normal")
    check("T1: Zero energy (compliant)", eval1.energy_score == 0.0)
    check("T1: ATP cost = 5.0", eval1.atp_cost == 5.0)

    # ── Test 2: RBAC denial (agent tries admin action) ──
    print("\n── Test 2: RBAC Denial (agent → admin action) ──")
    eval2 = policy_entity.evaluate_action({
        "action_type": "emergency_shutdown",
        "actor_role": "agent",
        "actor_lct": "lct:agent:alice",
        "t3": {"talent": 0.9, "training": 0.9, "temperament": 0.9},
        "atp": {"balance": 500.0},
        "metabolic_state": "wake",
    })
    print(f"  Decision: {eval2.decision.value}, Energy: {eval2.energy_score}")
    print(f"  Reason: {eval2.reason}")
    check("T2: Agent denied admin action", eval2.decision == PolicyDecision.DENY)
    check("T2: High energy (RBAC violation)", eval2.energy_score >= 50.0)
    check("T2: Primary violation is RBAC",
          eval2.rule_id == "rbac_authorization")

    # ── Test 3: CRISIS mode (admin action in duress) ──
    print("\n── Test 3: CRISIS Mode (duress accountability) ──")
    eval3 = policy_entity.evaluate_action({
        "action_type": "emergency_shutdown",
        "actor_role": "admin",
        "actor_lct": "lct:admin:bob",
        "t3": {"talent": 0.8, "training": 0.8, "temperament": 0.7},
        "atp": {"balance": 200.0},
        "metabolic_state": "crisis",
        "crisis_reason": "ATP pool critically low, system under attack",
        "parameters": {"witnesses": 3},
    })
    print(f"  Decision: {eval3.decision.value}, Energy: {eval3.energy_score}")
    print(f"  Frame: {eval3.accountability_frame}")
    print(f"  Duress: {eval3.duress_context is not None}")
    print(f"  Requires approval: {eval3.requires_approval}")
    check("T3: Admin allowed emergency_shutdown",
          eval3.decision == PolicyDecision.ALLOW)
    check("T3: Duress accountability frame",
          eval3.accountability_frame == "duress")
    check("T3: Duress context populated",
          eval3.duress_context is not None)
    check("T3: Duress records crisis reason",
          eval3.duress_context and "attack" in eval3.duress_context.get("constraint", ""))
    check("T3: Multi-sig required",
          eval3.requires_approval)

    # ── Test 4: Degraded state blocks admin changes ──
    print("\n── Test 4: Degraded State (REST blocks admin changes) ──")
    eval4 = policy_entity.evaluate_action({
        "action_type": "add_member",
        "actor_role": "admin",
        "actor_lct": "lct:admin:bob",
        "t3": {"talent": 0.8, "training": 0.8, "temperament": 0.7},
        "atp": {"balance": 200.0},
        "metabolic_state": "rest",
    })
    print(f"  Decision: {eval4.decision.value}, Energy: {eval4.energy_score}")
    print(f"  Frame: {eval4.accountability_frame}")
    print(f"  Reason: {eval4.reason}")
    # Note: custom rule "degraded_admin_block" only has weight 1.5 (< 3.0), so WARN not DENY
    check("T4: Degraded accountability frame",
          eval4.accountability_frame == "degraded")
    check("T4: Action flagged (WARN or DENY)",
          eval4.decision in (PolicyDecision.WARN, PolicyDecision.DENY))
    check("T4: Non-zero energy", eval4.energy_score > 0)

    # ── Test 5: Insufficient trust ──
    print("\n── Test 5: Insufficient Trust (T3 below threshold) ──")
    eval5 = policy_entity.evaluate_action({
        "action_type": "run_analysis",
        "actor_role": "agent",
        "actor_lct": "lct:agent:charlie",
        "t3": {"talent": 0.1, "training": 0.1, "temperament": 0.1},
        "atp": {"balance": 100.0},
        "metabolic_state": "wake",
    })
    print(f"  Decision: {eval5.decision.value}, Energy: {eval5.energy_score}")
    check("T5: Low trust denied", eval5.decision == PolicyDecision.DENY)
    check("T5: Trust threshold violation detected",
          any(c.rule_id == "trust_threshold"
              for c in eval5.constraints_violated))

    # ── Test 6: Insufficient ATP ──
    print("\n── Test 6: Insufficient ATP ──")
    eval6 = policy_entity.evaluate_action({
        "action_type": "deploy_staging",
        "actor_role": "operator",
        "actor_lct": "lct:operator:dave",
        "t3": {"talent": 0.7, "training": 0.7, "temperament": 0.7},
        "atp": {"balance": 5.0},  # Need 20 for deploy_staging
        "metabolic_state": "wake",
    })
    print(f"  Decision: {eval6.decision.value}, Energy: {eval6.energy_score}")
    check("T6: Insufficient ATP denied", eval6.decision == PolicyDecision.DENY)
    check("T6: ATP violation detected",
          any(c.rule_id == "atp_affordability"
              for c in eval6.constraints_violated))

    # ── Test 7: High-risk without witnesses ──
    print("\n── Test 7: High-Risk Without Witnesses ──")
    eval7 = policy_entity.evaluate_action({
        "action_type": "approve_deployment",
        "actor_role": "admin",
        "actor_lct": "lct:admin:bob",
        "t3": {"talent": 0.8, "training": 0.8, "temperament": 0.7},
        "atp": {"balance": 200.0},
        "metabolic_state": "focus",
        "parameters": {"witnesses": 1},  # Need 3+
    })
    print(f"  Decision: {eval7.decision.value}, Energy: {eval7.energy_score}")
    check("T7: Missing witnesses flagged",
          eval7.decision in (PolicyDecision.WARN, PolicyDecision.DENY))
    check("T7: Witness rule violated",
          any(c.rule_id == "witness_requirement"
              for c in eval7.constraints_violated))

    # ── Test 8: Policy entity upgrade (immutability) ──
    print("\n── Test 8: Policy Entity Immutability + Upgrade ──")
    v1_hash = policy_entity._content_hash
    v1_lct = policy_entity.lct

    new_policy = dict(team_policy)
    new_policy["action_costs"]["run_analysis"] = 8.0  # Increased cost
    v2 = policy_entity.upgrade(new_policy)

    check("T8: Upgrade creates new version", v2.version == 2)
    check("T8: Different content hash", v2._content_hash != v1_hash)
    check("T8: Different LCT", v2.lct != v1_lct)
    check("T8: Original unchanged", policy_entity.version == 1)
    check("T8: LCT format correct",
          v2.lct.startswith("policy:team-alpha-governance:2:"))

    # ── Test 9: Energy function properties ──
    print("\n── Test 9: Energy Function Properties ──")
    # Energy should be monotonic with violation severity
    gate = PolicyGateIRP()

    # No violations
    state_clean = gate.init_state({
        "action_type": "run_analysis",
        "actor_role": "agent",
        "t3": {"talent": 0.7, "training": 0.7, "temperament": 0.7},
        "atp": {"balance": 100.0},
        "metabolic_state": "wake",
        "team_policy": team_policy,
    })
    state_clean = gate.step(state_clean)
    energy_clean = state_clean["energy"]

    # Trust violation
    state_trust = gate.init_state({
        "action_type": "run_analysis",
        "actor_role": "agent",
        "t3": {"talent": 0.1, "training": 0.1, "temperament": 0.1},
        "atp": {"balance": 100.0},
        "metabolic_state": "wake",
        "team_policy": team_policy,
    })
    state_trust = gate.step(state_trust)
    energy_trust = state_trust["energy"]

    # RBAC violation
    state_rbac = gate.init_state({
        "action_type": "emergency_shutdown",
        "actor_role": "agent",
        "t3": {"talent": 0.9, "training": 0.9, "temperament": 0.9},
        "atp": {"balance": 500.0},
        "metabolic_state": "wake",
        "team_policy": team_policy,
    })
    state_rbac = gate.step(state_rbac)
    energy_rbac = state_rbac["energy"]

    print(f"  Clean energy: {energy_clean}")
    print(f"  Trust violation energy: {energy_trust}")
    print(f"  RBAC violation energy: {energy_rbac}")
    check("T9: Clean state has zero energy", energy_clean == 0.0)
    check("T9: Trust violation > 0", energy_trust > 0)
    check("T9: RBAC violation > trust violation", energy_rbac > energy_trust)
    check("T9: Energy ordering (0 < trust < rbac)",
          0 == energy_clean < energy_trust < energy_rbac)

    # ── Test 10: Evaluation ledger (hash chain) ──
    print("\n── Test 10: Evaluation Ledger Chain Integrity ──")
    summary = policy_entity.gate.evaluation_summary()
    print(f"  Total evaluations: {summary['total']}")
    print(f"  By decision: {summary['by_decision']}")
    print(f"  By frame: {summary['by_frame']}")
    print(f"  Chain head: {summary['chain_head']}")

    # Verify chain
    all_evals = policy_entity.gate.evaluations
    check("T10: Multiple evaluations recorded", len(all_evals) >= 7)

    # Verify each has unique hash
    hashes = [e.evaluation_hash for e in all_evals]
    check("T10: All evaluation hashes unique", len(set(hashes)) == len(hashes))

    # Verify accountability frames represented
    frames = set(e.accountability_frame for e in all_evals)
    check("T10: Multiple accountability frames seen",
          len(frames) >= 2)

    # ── Test 11: IRP convergence properties ──
    print("\n── Test 11: IRP Convergence Properties ──")
    gate2 = PolicyGateIRP()
    state = gate2.init_state({
        "action_type": "run_analysis",
        "actor_role": "agent",
        "t3": {"talent": 0.6, "training": 0.6, "temperament": 0.6},
        "atp": {"balance": 50.0},
        "metabolic_state": "wake",
        "team_policy": team_policy,
    })

    # Manually drive the IRP loop
    energies = []
    for i in range(5):
        state = gate2.step(state)
        energies.append(state["energy"])
        if gate2.halt(state):
            break

    check("T11: IRP halts within 5 iterations", gate2.halt(state))
    check("T11: Energy converges (non-increasing)",
          all(energies[i] >= energies[i+1] - 0.01
              for i in range(len(energies)-1)))
    check("T11: Final energy is stable", len(set(energies)) <= 2)

    # ── Test 12: Fractal self-similarity check ──
    print("\n── Test 12: Fractal Self-Similarity ──")
    # PolicyEntity is itself a stack: it has its own T3, own evaluations, own LCT
    check("T12: PolicyEntity has LCT",
          policy_entity.lct.startswith("policy:"))
    check("T12: PolicyEntity has T3 tensor",
          hasattr(policy_entity, 't3'))
    check("T12: PolicyEntity tracks evaluation count",
          policy_entity.evaluations_count >= 7)
    check("T12: PolicyGateIRP implements IRP contract",
          all(hasattr(gate, m) for m in
              ["init_state", "step", "energy", "project", "halt"]))

    # ── Summary ──
    print("\n" + "=" * 70)
    total = checks_passed + checks_failed
    print(f"  PolicyGate IRP: {checks_passed}/{total} checks passed")
    if checks_failed == 0:
        print("  ALL CHECKS PASSED!")

    print(f"\n  KEY INSIGHTS:")
    print(f"    1. IRP contract (5 methods) works as policy evaluation loop")
    print(f"    2. Energy function orders violations: 0 < trust < RBAC")
    print(f"    3. Accountability frames map from metabolic states")
    print(f"    4. CRISIS = duress recording, NOT stricter policy")
    print(f"    5. Degraded blocks admin changes (safety by default)")
    print(f"    6. PolicyEntity is immutable — upgrades create new entities")
    print(f"    7. Fractal self-similarity: entity has own T3, LCT, evaluations")
    print(f"    8. Evaluation ledger is hash-chained for audit trail")
    print(f"    9. Multi-sig surfaces through requires_approval flag")
    print(f"   10. Witness requirement enforced as custom policy rule")

    print(f"\n  SOIA-SAGE CONVERGENCE:")
    print(f"    - PolicyGate.energy() = IRP energy function ✓")
    print(f"    - AccountabilityFrame maps from metabolic state ✓")
    print(f"    - Duress context records crisis conditions ✓")
    print(f"    - PolicyEntity is 15th entity type with own LCT ✓")
    print(f"    - Immutable versioning = fractal identity ✓")
    print("=" * 70)

    return checks_failed == 0


if __name__ == "__main__":
    success = run_demo()
    import sys
    sys.exit(0 if success else 1)
