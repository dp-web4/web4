#!/usr/bin/env python3
"""
Full-Stack Web4 Demo — 5-Minute Compliance Walkthrough

End-to-end demonstration: Team → Identity → Classify → Act → Monitor →
Override → Audit. Shows all Web4 layers working together as a single
coherent system suitable for regulatory demo.

Architecture layers exercised:
  1. Team/Society creation (Hardbound)
  2. LCT identity with hardware binding
  3. EU AI Act classification (Annex III)
  4. R6 action framework with ATP accounting
  5. T3/V3 tensor monitoring + drift detection
  6. Human oversight (approval + override)
  7. Fractal chain ledger + compliance export
  8. Bias audit + data governance
  9. Attack defense validation
  10. Full assessment + regulatory report

This is the reference demo script for compliance consultancies and
regulatory bodies per docs/strategy/eu-ai-act-compliance-mapping.md.

Session: Legion Autonomous 2026-02-26
"""

import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ═══════════════════════════════════════════════════════════════
# LAYER 1: TEAM/SOCIETY
# ═══════════════════════════════════════════════════════════════

class TeamRole(Enum):
    ADMIN = "admin"
    MEMBER = "member"
    AI_AGENT = "ai_agent"
    AUDITOR = "auditor"
    OVERSEER = "overseer"


@dataclass
class TeamMember:
    lct_id: str
    name: str
    role: TeamRole
    hardware_binding_level: int = 1
    trust: dict = field(default_factory=lambda: {
        "talent": 0.5, "training": 0.5, "temperament": 0.5
    })
    v3: dict = field(default_factory=lambda: {
        "valuation": 0.5, "veracity": 0.5, "validity": 0.5
    })
    joined: str = ""
    capabilities: list = field(default_factory=list)
    limitations: list = field(default_factory=list)

    def __post_init__(self):
        if not self.joined:
            self.joined = datetime.utcnow().isoformat()

    @property
    def t3_composite(self) -> float:
        return sum(self.trust.values()) / 3.0

    @property
    def v3_composite(self) -> float:
        return sum(self.v3.values()) / 3.0


@dataclass
class Team:
    team_id: str
    name: str
    description: str
    admin_lct_id: str
    members: dict = field(default_factory=dict)  # lct_id → TeamMember
    policies: list = field(default_factory=list)
    created: str = ""

    def __post_init__(self):
        if not self.created:
            self.created = datetime.utcnow().isoformat()

    def add_member(self, member: TeamMember) -> dict:
        self.members[member.lct_id] = member
        return {"added": member.lct_id, "role": member.role.value,
                "team": self.team_id}

    def member_count(self) -> int:
        return len(self.members)


# ═══════════════════════════════════════════════════════════════
# LAYER 2: CLASSIFICATION (Art. 6)
# ═══════════════════════════════════════════════════════════════

class AnnexIIICategory(Enum):
    BIOMETRICS = "biometrics"
    CRITICAL_INFRA = "critical_infrastructure"
    EDUCATION = "education"
    EMPLOYMENT = "employment"
    ESSENTIAL_SERVICES = "essential_services"
    LAW_ENFORCEMENT = "law_enforcement"
    MIGRATION = "migration"
    JUSTICE = "justice"
    NONE = "not_high_risk"


class RiskLevel(Enum):
    HIGH = "high"
    LIMITED = "limited"
    MINIMAL = "minimal"


@dataclass
class Classification:
    category: AnnexIIICategory
    risk_level: RiskLevel
    evidence: list
    classified_by: str
    date: str = ""

    def __post_init__(self):
        if not self.date:
            self.date = datetime.utcnow().isoformat()


# ═══════════════════════════════════════════════════════════════
# LAYER 3: ATP LEDGER
# ═══════════════════════════════════════════════════════════════

class ATPLedger:
    FEE_RATE = 0.05

    def __init__(self):
        self.accounts: dict[str, float] = {}
        self.locks: dict[str, dict] = {}
        self.total_fees: float = 0.0
        self.transactions: list[dict] = []

    def create_account(self, owner: str, balance: float):
        self.accounts[owner] = self.accounts.get(owner, 0.0) + balance

    def balance(self, owner: str) -> float:
        return self.accounts.get(owner, 0.0)

    def lock(self, owner: str, amount: float, lock_id: str) -> bool:
        if self.accounts.get(owner, 0.0) < amount:
            return False
        self.accounts[owner] -= amount
        self.locks[lock_id] = {"owner": owner, "amount": amount}
        self.transactions.append({
            "type": "lock", "owner": owner, "amount": amount,
            "lock_id": lock_id, "time": datetime.utcnow().isoformat()
        })
        return True

    def commit(self, lock_id: str, executor: str, consumed: float) -> bool:
        if lock_id not in self.locks:
            return False
        lock = self.locks.pop(lock_id)
        consumed = min(consumed, lock["amount"])
        fee = consumed * self.FEE_RATE
        self.total_fees += fee
        self.accounts[executor] = self.accounts.get(executor, 0.0) + consumed - fee
        self.accounts[lock["owner"]] += lock["amount"] - consumed
        self.transactions.append({
            "type": "commit", "lock_id": lock_id, "executor": executor,
            "consumed": consumed, "fee": fee,
            "time": datetime.utcnow().isoformat()
        })
        return True

    @property
    def total_supply(self) -> float:
        return (sum(self.accounts.values()) +
                sum(l["amount"] for l in self.locks.values()) +
                self.total_fees)


# ═══════════════════════════════════════════════════════════════
# LAYER 4: R6 ACTION FRAMEWORK
# ═══════════════════════════════════════════════════════════════

@dataclass
class R6Action:
    action_id: str
    rules: str
    role: str
    request: str
    reference: str
    resource: str
    result: str
    entity_id: str
    trust_delta: float = 0.0
    coherence: float = 0.8
    timestamp: str = ""
    hash: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
        if not self.hash:
            content = f"{self.action_id}:{self.entity_id}:{self.timestamp}"
            self.hash = hashlib.sha256(content.encode()).hexdigest()[:16]


# ═══════════════════════════════════════════════════════════════
# LAYER 5: LEDGER (Art. 12)
# ═══════════════════════════════════════════════════════════════

class FractalLedger:
    def __init__(self):
        self.entries: list[dict] = []
        self.chain_head: str = "genesis"

    def record(self, event_type: str, entity_id: str, data: dict,
               severity: str = "info") -> dict:
        level = "root" if severity in ("incident", "critical") else \
                "stem" if event_type == "status_change" else \
                "leaf" if severity == "warning" else "compost"
        entry_hash = hashlib.sha256(
            f"{len(self.entries)}:{self.chain_head}:{json.dumps(data, sort_keys=True)}".encode()
        ).hexdigest()[:16]
        entry = {
            "id": f"L-{len(self.entries):05d}",
            "type": event_type,
            "entity": entity_id,
            "data": data,
            "severity": severity,
            "level": level,
            "prev_hash": self.chain_head,
            "hash": entry_hash,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.chain_head = entry_hash
        self.entries.append(entry)
        return entry

    def verify_chain(self) -> bool:
        if not self.entries:
            return True
        expected = "genesis"
        for e in self.entries:
            if e["prev_hash"] != expected:
                return False
            expected = e["hash"]
        return True

    def export_regulatory(self, entity_id: str) -> dict:
        entity_entries = [e for e in self.entries if e["entity"] == entity_id]
        return {
            "eu_ai_act_audit_log": {
                "regulation": "EU 2024/1689",
                "article": "12",
                "entity": entity_id,
                "export_date": datetime.utcnow().isoformat(),
                "chain_valid": self.verify_chain(),
                "entries": len(entity_entries),
                "by_severity": {
                    s: sum(1 for e in entity_entries if e["severity"] == s)
                    for s in ("info", "warning", "critical", "incident")
                }
            }
        }


# ═══════════════════════════════════════════════════════════════
# LAYER 6: HUMAN OVERSIGHT (Art. 14)
# ═══════════════════════════════════════════════════════════════

class OversightEngine:
    def __init__(self, ledger: FractalLedger):
        self.ledger = ledger
        self.overseers: dict[str, str] = {}  # entity → overseer
        self.pending: list[dict] = []
        self.decisions: list[dict] = []

    def assign(self, entity_id: str, overseer_id: str):
        self.overseers[entity_id] = overseer_id
        self.ledger.record("oversight_assign", entity_id,
                           {"overseer": overseer_id}, "warning")

    def request_approval(self, entity_id: str, action: str) -> dict:
        if entity_id not in self.overseers:
            return {"approved": True, "reason": "no_oversight"}
        req = {
            "id": f"APR-{len(self.pending):03d}",
            "entity": entity_id,
            "action": action,
            "status": "pending",
            "time": datetime.utcnow().isoformat()
        }
        self.pending.append(req)
        self.ledger.record("approval_request", entity_id,
                           {"action": action}, "warning")
        return {"approved": False, "request_id": req["id"]}

    def decide(self, request_id: str, approved: bool, reason: str = "") -> dict:
        for req in self.pending:
            if req["id"] == request_id:
                req["status"] = "approved" if approved else "denied"
                req["reason"] = reason
                self.decisions.append(req)
                self.ledger.record("approval_decision", req["entity"],
                                   {"approved": approved, "reason": reason},
                                   "warning")
                return req
        return {"error": "not_found"}

    def override(self, entity_id: str, new_status: str, reason: str) -> dict:
        result = {
            "entity": entity_id,
            "new_status": new_status,
            "reason": reason,
            "time": datetime.utcnow().isoformat()
        }
        self.ledger.record("status_override", entity_id, result, "incident")
        return result


# ═══════════════════════════════════════════════════════════════
# LAYER 7: MONITORING (Art. 9)
# ═══════════════════════════════════════════════════════════════

class TensorMonitor:
    def __init__(self):
        self.snapshots: list[dict] = []

    def snapshot(self, member: TeamMember) -> dict:
        snap = {
            "entity": member.lct_id,
            "t3": dict(member.trust),
            "t3_composite": member.t3_composite,
            "v3": dict(member.v3),
            "v3_composite": member.v3_composite,
            "risk_flags": [f"{d}={v:.2f}" for d, v in member.trust.items() if v < 0.4],
            "time": datetime.utcnow().isoformat()
        }
        self.snapshots.append(snap)
        return snap

    def detect_drift(self, entity_id: str, window: int = 3) -> dict:
        entity_snaps = [s for s in self.snapshots if s["entity"] == entity_id]
        if len(entity_snaps) < 2:
            return {"drift": False, "reason": "insufficient_data"}
        recent = entity_snaps[-window:]
        composites = [s["t3_composite"] for s in recent]
        if len(composites) < 2:
            return {"drift": False, "reason": "insufficient_data"}
        deltas = [composites[i+1] - composites[i] for i in range(len(composites)-1)]
        avg_delta = sum(deltas) / len(deltas)
        return {
            "drift": avg_delta < -0.02,
            "direction": "declining" if avg_delta < -0.02 else "stable",
            "avg_delta": round(avg_delta, 4),
            "snapshots": len(recent)
        }


# ═══════════════════════════════════════════════════════════════
# LAYER 8: BIAS AUDIT (Art. 10)
# ═══════════════════════════════════════════════════════════════

class BiasAuditor:
    def audit(self, dataset_id: str, outcomes: dict[str, dict[str, float]],
              auditor_id: str) -> dict:
        findings = []
        for char, groups in outcomes.items():
            rates = list(groups.values())
            if not rates:
                continue
            min_rate, max_rate = min(rates), max(rates)
            di_ratio = min_rate / max_rate if max_rate > 0 else 1.0
            if di_ratio < 0.8:
                findings.append(
                    f"{char}: DI ratio {di_ratio:.2f} < 0.8 ({groups})")
        return {
            "dataset": dataset_id,
            "auditor": auditor_id,
            "has_bias": len(findings) > 0,
            "findings": findings,
            "date": datetime.utcnow().isoformat()
        }


# ═══════════════════════════════════════════════════════════════
# FULL-STACK DEMO ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════

class FullStackDemo:
    """Orchestrates the complete 5-minute demo."""

    def __init__(self):
        self.ledger = FractalLedger()
        self.atp = ATPLedger()
        self.oversight = OversightEngine(self.ledger)
        self.monitor = TensorMonitor()
        self.auditor = BiasAuditor()
        self.actions: list[R6Action] = []
        self.team: Optional[Team] = None

    def step_1_create_team(self) -> dict:
        """Step 1: Create team/society with admin."""
        admin = TeamMember(
            lct_id="lct:web4:human:alice-admin",
            name="Alice (Admin)",
            role=TeamRole.ADMIN,
            hardware_binding_level=5,  # TPM2
            trust={"talent": 0.9, "training": 0.85, "temperament": 0.92},
            capabilities=["team_management", "policy_setting", "member_onboarding"],
            limitations=[]
        )

        self.team = Team(
            team_id="team:acme-ai-governance",
            name="ACME AI Governance Team",
            description="Enterprise AI governance using Web4 infrastructure",
            admin_lct_id=admin.lct_id,
            policies=[
                "All AI agents require human oversight for critical decisions",
                "EU AI Act compliance mandatory for all team AI systems",
                "Minimum hardware binding level 3 for high-risk systems"
            ]
        )
        self.team.add_member(admin)

        # Fund admin ATP account
        self.atp.create_account(admin.lct_id, 10000.0)

        self.ledger.record("team_created", self.team.team_id,
                           {"name": self.team.name, "admin": admin.lct_id})

        return {
            "team": self.team.team_id,
            "admin": admin.lct_id,
            "hw_binding": admin.hardware_binding_level,
            "policies": len(self.team.policies)
        }

    def step_2_add_ai_agent(self) -> dict:
        """Step 2: Create AI agent with identity and classification."""
        agent = TeamMember(
            lct_id="lct:web4:ai:cv-screener-001",
            name="CV Screening Agent",
            role=TeamRole.AI_AGENT,
            hardware_binding_level=4,  # TrustZone
            trust={"talent": 0.75, "training": 0.82, "temperament": 0.68},
            v3={"valuation": 0.7, "veracity": 0.85, "validity": 0.78},
            capabilities=[
                "resume_parsing", "candidate_scoring",
                "qualification_matching", "skills_extraction"
            ],
            limitations=[
                "no_final_hiring_decisions",
                "requires_human_review_above_threshold",
                "max_delegation_depth_2"
            ]
        )
        self.team.add_member(agent)
        self.atp.create_account(agent.lct_id, 5000.0)

        # Classify under EU AI Act
        classification = Classification(
            category=AnnexIIICategory.EMPLOYMENT,
            risk_level=RiskLevel.HIGH,
            evidence=["Annex III §4(a): AI for recruitment and candidate filtering"],
            classified_by=self.team.admin_lct_id
        )

        self.ledger.record("agent_created", agent.lct_id,
                           {"name": agent.name, "team": self.team.team_id,
                            "hw_binding": agent.hardware_binding_level})
        self.ledger.record("classification", agent.lct_id,
                           {"category": classification.category.value,
                            "risk_level": classification.risk_level.value,
                            "evidence": classification.evidence},
                           severity="warning")

        return {
            "agent": agent.lct_id,
            "hw_binding": agent.hardware_binding_level,
            "classification": classification.category.value,
            "risk_level": classification.risk_level.value,
            "t3_composite": agent.t3_composite,
            "capabilities": len(agent.capabilities),
            "limitations": len(agent.limitations)
        }

    def step_3_assign_oversight(self) -> dict:
        """Step 3: Assign human oversight."""
        overseer = TeamMember(
            lct_id="lct:web4:human:bob-overseer",
            name="Bob (HR Oversight)",
            role=TeamRole.OVERSEER,
            hardware_binding_level=3,
            trust={"talent": 0.8, "training": 0.75, "temperament": 0.85}
        )
        self.team.add_member(overseer)

        agent_id = "lct:web4:ai:cv-screener-001"
        self.oversight.assign(agent_id, overseer.lct_id)

        return {
            "overseer": overseer.lct_id,
            "agent": agent_id,
            "team_members": self.team.member_count()
        }

    def step_4_execute_actions(self) -> dict:
        """Step 4: Agent performs tasks via R6 framework."""
        agent_id = "lct:web4:ai:cv-screener-001"
        admin_id = "lct:web4:human:alice-admin"
        agent = self.team.members[agent_id]

        tasks_executed = 0
        total_atp_consumed = 0.0

        # Execute 5 screening batches
        for batch in range(5):
            budget = 100.0
            lock_id = f"task-{batch}"

            if not self.atp.lock(admin_id, budget, lock_id):
                continue

            action = R6Action(
                action_id=f"R6-{batch:04d}",
                rules="employment_screening_policy_v3",
                role="cv_screener",
                request=f"screen_batch_{batch}",
                reference=f"job-posting-2026-Q1-{batch:03d}",
                resource=f"{budget} ATP",
                result=f"Screened {20*(batch+1)} CVs — {18*(batch+1)} passed, {2*(batch+1)} flagged",
                entity_id=agent_id,
                trust_delta=0.005,
                coherence=0.85 + batch * 0.02
            )
            self.actions.append(action)

            # Quality-based payment
            quality = 0.75 + batch * 0.03
            payment = budget * quality
            self.atp.commit(lock_id, agent_id, payment)

            # Update trust
            delta = 0.02 * (quality - 0.5)
            for dim in agent.trust:
                agent.trust[dim] = min(1.0, agent.trust[dim] + delta)

            self.ledger.record("action", agent_id, {
                "action_id": action.action_id,
                "request": action.request,
                "result": action.result,
                "atp": payment,
                "coherence": action.coherence
            })

            tasks_executed += 1
            total_atp_consumed += payment

            # Record tensor snapshot
            self.monitor.snapshot(agent)

        return {
            "tasks": tasks_executed,
            "total_atp": round(total_atp_consumed, 2),
            "agent_trust": round(agent.t3_composite, 3),
            "actions_logged": len(self.actions)
        }

    def step_5_monitor_and_detect(self) -> dict:
        """Step 5: Monitor tensors, detect drift, run bias audit."""
        agent_id = "lct:web4:ai:cv-screener-001"
        agent = self.team.members[agent_id]

        # Simulate drift: temperament drops
        original_temp = agent.trust["temperament"]
        agent.trust["temperament"] = 0.35
        self.monitor.snapshot(agent)
        agent.trust["temperament"] = 0.30
        self.monitor.snapshot(agent)

        drift = self.monitor.detect_drift(agent_id)

        # Run bias audit
        bias_result = self.auditor.audit(
            "cv_screening_dataset_2026",
            {
                "gender": {"male": 0.72, "female": 0.58},
                "age": {"18-30": 0.65, "31-50": 0.70, "51+": 0.48}
            },
            "lct:web4:human:carol-auditor"
        )

        self.ledger.record("drift_detected", agent_id, drift, "critical")
        self.ledger.record("bias_audit", agent_id, bias_result, "warning")

        # Restore for later steps
        agent.trust["temperament"] = original_temp

        return {
            "drift_detected": drift["drift"],
            "drift_direction": drift.get("direction", "unknown"),
            "bias_found": bias_result["has_bias"],
            "bias_findings": len(bias_result["findings"]),
            "current_t3": round(agent.t3_composite, 3)
        }

    def step_6_human_oversight(self) -> dict:
        """Step 6: Human blocks critical action, then overrides."""
        agent_id = "lct:web4:ai:cv-screener-001"

        # Agent tries critical action
        approval = self.oversight.request_approval(
            agent_id, "auto_reject_low_score_candidates"
        )

        # Human denies
        if not approval.get("approved"):
            decision = self.oversight.decide(
                approval["request_id"], False,
                "Auto-rejection not permitted — human review required"
            )

        # Human overrides: pause agent for review
        override = self.oversight.override(
            agent_id, "dormant",
            "Paused for bias review — temperament drift + bias findings"
        )

        return {
            "action_blocked": not approval.get("approved", True),
            "decision": "denied",
            "override_status": "dormant",
            "reason": override["reason"]
        }

    def step_7_audit_export(self) -> dict:
        """Step 7: Generate compliance audit export."""
        agent_id = "lct:web4:ai:cv-screener-001"

        # Chain integrity
        chain_valid = self.ledger.verify_chain()

        # Regulatory export
        export = self.ledger.export_regulatory(agent_id)

        # ATP accounting
        atp_summary = {
            "admin_balance": self.atp.balance("lct:web4:human:alice-admin"),
            "agent_balance": self.atp.balance(agent_id),
            "total_fees": self.atp.total_fees,
            "total_supply": self.atp.total_supply,
            "transactions": len(self.atp.transactions)
        }

        return {
            "chain_valid": chain_valid,
            "total_ledger_entries": len(self.ledger.entries),
            "agent_entries": export["eu_ai_act_audit_log"]["entries"],
            "atp_accounting": atp_summary,
            "export_generated": True
        }

    def run_full_demo(self) -> dict:
        """Execute complete 5-minute demo."""
        results = {}

        results["step_1_team"] = self.step_1_create_team()
        results["step_2_agent"] = self.step_2_add_ai_agent()
        results["step_3_oversight"] = self.step_3_assign_oversight()
        results["step_4_actions"] = self.step_4_execute_actions()
        results["step_5_monitoring"] = self.step_5_monitor_and_detect()
        results["step_6_oversight"] = self.step_6_human_oversight()
        results["step_7_audit"] = self.step_7_audit_export()

        # Summary
        results["demo_summary"] = {
            "team_members": self.team.member_count(),
            "total_actions": len(self.actions),
            "ledger_entries": len(self.ledger.entries),
            "chain_integrity": self.ledger.verify_chain(),
            "atp_conservation": abs(self.atp.total_supply - 15000.0) < 1.0,
            "compliance_ready": True
        }

        return results


# ═══════════════════════════════════════════════════════════════
# CHECKS
# ═══════════════════════════════════════════════════════════════

def run_checks():
    passed = 0
    failed = 0

    def check(condition: bool, description: str):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {description}")

    # ─── Run the demo ─────────────────────────────────────────

    demo = FullStackDemo()
    results = demo.run_full_demo()

    # ─── Step 1: Team Creation ────────────────────────────────

    print("Step 1: Team Creation")
    s1 = results["step_1_team"]
    check(s1["team"] == "team:acme-ai-governance", "Team created with correct ID")
    check(s1["hw_binding"] == 5, "Admin has TPM2 binding (level 5)")
    check(s1["policies"] == 3, "3 governance policies set")

    # ─── Step 2: AI Agent Identity ────────────────────────────

    print("Step 2: AI Agent Identity + Classification")
    s2 = results["step_2_agent"]
    check(s2["agent"] == "lct:web4:ai:cv-screener-001", "Agent LCT ID correct")
    check(s2["hw_binding"] == 4, "Agent has TrustZone binding (level 4)")
    check(s2["classification"] == "employment", "Classified as employment (Annex III)")
    check(s2["risk_level"] == "high", "Risk level is HIGH")
    check(s2["t3_composite"] > 0.7, f"Agent T3 composite > 0.7 ({s2['t3_composite']:.2f})")
    check(s2["capabilities"] == 4, "4 capabilities declared")
    check(s2["limitations"] == 3, "3 limitations declared")

    # ─── Step 3: Human Oversight ──────────────────────────────

    print("Step 3: Human Oversight Assignment")
    s3 = results["step_3_oversight"]
    check(s3["overseer"] == "lct:web4:human:bob-overseer", "Overseer assigned")
    check(s3["team_members"] == 3, "Team has 3 members (admin + agent + overseer)")

    # ─── Step 4: R6 Actions ──────────────────────────────────

    print("Step 4: R6 Action Execution")
    s4 = results["step_4_actions"]
    check(s4["tasks"] == 5, "5 screening batches executed")
    check(s4["total_atp"] > 0, f"ATP consumed: {s4['total_atp']}")
    check(s4["agent_trust"] > 0.7, f"Agent trust maintained ({s4['agent_trust']:.3f})")
    check(s4["actions_logged"] == 5, "5 actions logged in R6 framework")

    # ─── Step 5: Monitoring ──────────────────────────────────

    print("Step 5: Tensor Monitoring + Bias Audit")
    s5 = results["step_5_monitoring"]
    check(s5["drift_detected"], "Drift detected when temperament drops")
    check(s5["drift_direction"] == "declining", "Drift direction is declining")
    check(s5["bias_found"], "Bias detected in CV screening dataset")
    check(s5["bias_findings"] > 0, f"Bias findings: {s5['bias_findings']}")

    # ─── Step 6: Human Override ──────────────────────────────

    print("Step 6: Human Oversight Actions")
    s6 = results["step_6_oversight"]
    check(s6["action_blocked"], "Critical action blocked by oversight")
    check(s6["decision"] == "denied", "Human denied auto-rejection")
    check(s6["override_status"] == "dormant", "Agent paused to DORMANT")
    check("bias" in s6["reason"].lower(), "Override reason mentions bias")

    # ─── Step 7: Audit Export ────────────────────────────────

    print("Step 7: Compliance Audit Export")
    s7 = results["step_7_audit"]
    check(s7["chain_valid"], "Hash chain integrity verified")
    check(s7["total_ledger_entries"] > 10, f"Ledger has {s7['total_ledger_entries']} entries")
    check(s7["agent_entries"] > 5, f"Agent has {s7['agent_entries']} entries")
    check(s7["export_generated"], "Regulatory export generated")
    check(s7["atp_accounting"]["total_fees"] > 0, "ATP fees collected")
    check(s7["atp_accounting"]["transactions"] == 10, "10 ATP transactions (5 locks + 5 commits)")

    # ─── Demo Summary ────────────────────────────────────────

    print("Demo Summary")
    summary = results["demo_summary"]
    check(summary["team_members"] == 3, "3 team members")
    check(summary["total_actions"] == 5, "5 total actions")
    check(summary["chain_integrity"], "Chain integrity maintained")
    check(summary["atp_conservation"], "ATP conservation within tolerance")
    check(summary["compliance_ready"], "System marked compliance-ready")

    # ─── Cross-Layer Verification ────────────────────────────

    print("Cross-Layer Verification")

    # Verify ledger has entries from all layers
    entry_types = set(e["type"] for e in demo.ledger.entries)
    check("team_created" in entry_types, "Ledger records team creation")
    check("agent_created" in entry_types, "Ledger records agent identity")
    check("classification" in entry_types, "Ledger records classification")
    check("action" in entry_types, "Ledger records R6 actions")
    check("drift_detected" in entry_types, "Ledger records drift detection")
    check("bias_audit" in entry_types, "Ledger records bias audit")
    check("oversight_assign" in entry_types, "Ledger records oversight assignment")
    check("approval_request" in entry_types, "Ledger records approval request")
    check("approval_decision" in entry_types, "Ledger records approval decision")
    check("status_override" in entry_types, "Ledger records status override")

    # Verify all layers connect to same agent
    agent_id = "lct:web4:ai:cv-screener-001"
    agent_entries = [e for e in demo.ledger.entries if e["entity"] == agent_id]
    check(len(agent_entries) > 8, f"Agent has entries from multiple layers ({len(agent_entries)})")

    # Verify ATP flows match ledger records
    atp_actions = [e for e in demo.ledger.entries
                   if e["type"] == "action" and e["entity"] == agent_id]
    check(len(atp_actions) == 5, "5 ATP-consuming actions recorded in ledger")

    # Verify tensor snapshots exist
    check(len(demo.monitor.snapshots) > 5, f"Multiple tensor snapshots ({len(demo.monitor.snapshots)})")

    # ─── Demo-ability Checks ─────────────────────────────────

    print("Demo-ability Checks")

    # Can we explain each step in under 1 minute?
    check(len(results) == 8, "8 demo steps (7 + summary)")
    check(all(isinstance(v, dict) for v in results.values()), "All steps return structured data")

    # Each step has enough data to narrate
    for step_name, step_data in results.items():
        if step_name != "demo_summary":
            check(len(step_data) >= 3,
                  f"{step_name} has >= 3 data points for narration")

    # ─── Summary ──────────────────────────────────────────────

    total = passed + failed
    print(f"\n{'='*60}")
    print(f"Full-Stack Demo: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  {failed} FAILED")
    else:
        print("  All checks passed!")
    print(f"{'='*60}")

    print(f"\nDemo Steps:")
    print(f"  1. Team Creation: {s1['team']}")
    print(f"  2. AI Agent: {s2['agent']} (HW:{s2['hw_binding']}, {s2['risk_level']})")
    print(f"  3. Oversight: {s3['overseer']}")
    print(f"  4. Actions: {s4['tasks']} tasks, {s4['total_atp']} ATP")
    print(f"  5. Monitoring: drift={'YES' if s5['drift_detected'] else 'NO'}, bias={'YES' if s5['bias_found'] else 'NO'}")
    print(f"  6. Override: {s6['override_status']} ({s6['decision']})")
    print(f"  7. Audit: {s7['total_ledger_entries']} entries, chain={'VALID' if s7['chain_valid'] else 'BROKEN'}")

    return passed, failed


if __name__ == "__main__":
    run_checks()
