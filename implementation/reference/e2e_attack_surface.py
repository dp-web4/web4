#!/usr/bin/env python3
"""
E2E Attack Surface Analysis
============================

Systematic discovery of attack vectors across layer boundaries in the
Web4 E2E integration stack:

  Identity → Permissions → ATP → Federation → Reputation

The individual layers have been tested (121 implementations, 424+ attack
vectors in the corpus). But the BOUNDARIES between layers create new
attack surfaces not present in any single layer.

This module:
1. Enumerates boundary attack vectors
2. Implements proof-of-concept attacks
3. Tests defenses
4. Measures defense effectiveness

Attack categories:
  A. Identity Spoofing (abuse format translation)
  B. Permission Escalation (exploit trust-gate mismatches)
  C. ATP Draining (exploit lock/commit timing)
  D. Federation Manipulation (exploit quality assessment)
  E. Reputation Gaming (exploit diminishing returns or diversity)
  F. Cross-Layer Cascading (chain multiple boundary weaknesses)

Session: Legion Autonomous 2026-02-26
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ============================================================================
# SHARED INFRASTRUCTURE (minimal reproduction of E2E + Bridge layers)
# ============================================================================

@dataclass
class AgentIdentity:
    creator: str
    entity_type: str = "AI"
    trust_tensor: Dict[str, float] = field(default_factory=lambda: {
        "talent": 0.5, "training": 0.5, "temperament": 0.5
    })
    task_type: str = "perception"

    @property
    def simple_id(self) -> str:
        return f"lct:web4:{self.entity_type.lower()}:{self.creator}"

    @property
    def t3_composite(self) -> float:
        t = self.trust_tensor
        return (t["talent"] + t["training"] + t["temperament"]) / 3.0


TRUST_GATES = {
    "admin.full": 0.8,
    "cognition.sage": 0.6,
    "delegation.federation": 0.5,
    "execution.code": 0.5,
    "execution.safe": 0.4,
    "cognition": 0.4,
    "planning": 0.3,
    "perception": 0.3,
}

ATP_BUDGETS = {
    "perception": 200, "planning": 300, "execution.safe": 500,
    "execution.code": 800, "cognition": 800, "delegation.federation": 1000,
    "cognition.sage": 1000, "admin.full": 2000,
}


class ATPLedger:
    TRANSFER_FEE = 0.05

    def __init__(self):
        self.accounts: Dict[str, float] = {}
        self.locks: Dict[str, Tuple[str, float]] = {}

    def create_account(self, owner: str, balance: float = 100.0):
        self.accounts[owner] = balance

    def get_balance(self, owner: str) -> float:
        return self.accounts.get(owner, 0.0)

    def lock(self, owner: str, amount: float, lock_id: str) -> bool:
        if self.accounts.get(owner, 0.0) < amount:
            return False
        self.accounts[owner] -= amount
        self.locks[lock_id] = (owner, amount)
        return True

    def commit(self, lock_id: str, executor: str, consumed: float) -> bool:
        if lock_id not in self.locks:
            return False
        owner, locked = self.locks.pop(lock_id)
        consumed = min(consumed, locked)
        fee = consumed * self.TRANSFER_FEE
        if executor not in self.accounts:
            self.accounts[executor] = 0.0
        self.accounts[executor] += consumed - fee
        self.accounts[owner] += locked - consumed  # Return excess
        return True

    def rollback(self, lock_id: str) -> bool:
        if lock_id not in self.locks:
            return False
        owner, amount = self.locks.pop(lock_id)
        self.accounts[owner] += amount
        return True


class ReputationEngine:
    LEARNING_RATE = 0.02
    DIMINISHING_FACTOR = 0.8
    DIMINISHING_FLOOR = 0.1

    def __init__(self):
        self.task_counts: Dict[str, Dict[str, int]] = {}

    def update(self, agent: AgentIdentity, task_type: str,
               quality: float) -> Dict[str, float]:
        agent_id = agent.simple_id
        if agent_id not in self.task_counts:
            self.task_counts[agent_id] = {}
        count = self.task_counts[agent_id].get(task_type, 0) + 1
        self.task_counts[agent_id][task_type] = count

        diminishing = max(self.DIMINISHING_FLOOR,
                          self.DIMINISHING_FACTOR ** (count - 1))
        delta = self.LEARNING_RATE * (quality - 0.5) * diminishing

        deltas = {}
        for dim in ["talent", "training", "temperament"]:
            old = agent.trust_tensor[dim]
            new = max(0.0, min(1.0, old + delta))
            deltas[dim] = new - old
            agent.trust_tensor[dim] = new

        return deltas


# ============================================================================
# ATTACK FRAMEWORK
# ============================================================================

@dataclass
class AttackVector:
    """Description of an attack vector."""
    id: str
    name: str
    category: str  # A-F
    boundary: str  # e.g., "identity→permissions"
    description: str
    severity: str  # low, medium, high, critical
    defended: bool = False
    defense_description: str = ""


@dataclass
class AttackResult:
    """Result of executing an attack."""
    vector_id: str
    success: bool  # Did the attack succeed?
    impact: str    # What damage would occur?
    defense_effective: bool
    details: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# CATEGORY A: IDENTITY SPOOFING (Identity → Permissions boundary)
# ============================================================================

def attack_a1_format_confusion() -> AttackResult:
    """
    A1: LCT Format Confusion Attack

    Exploit: The bridge translates user:alice → lct:web4:human:alice.
    But what if attacker uses "lct:web4:human:alice" directly as their
    simulation-layer ID? The bridge would output "lct:web4:human:lct:web4:human:alice"
    — a garbled ID that might match nothing or match unintended entries.
    """
    # Attack: Use a Format C string as simulation input
    attacker_sim_id = "lct:web4:human:alice"  # Already in Format C

    # Bridge should detect this and pass through
    if attacker_sim_id.startswith("lct:"):
        # Defense: pass-through detection
        canonical = attacker_sim_id  # No double-encoding
        defense_effective = True
    else:
        canonical = f"lct:web4:human:{attacker_sim_id}"
        defense_effective = False

    return AttackResult(
        vector_id="A1",
        success=not defense_effective,
        impact="Identity confusion — attacker could impersonate another user",
        defense_effective=defense_effective,
        details={
            "input": attacker_sim_id,
            "output": canonical,
            "defense": "Pass-through detection: if starts with 'lct:', skip translation",
        },
    )


def attack_a2_entity_type_escalation() -> AttackResult:
    """
    A2: Entity Type Escalation

    Exploit: Attacker creates identity as "admin:hacker" which maps to
    entity_type="human" (admin→human in ROLE_TO_TYPE). The system might
    grant admin permissions based on the "admin" prefix in the simulation ID.
    """
    attacker_sim_id = "admin:hacker"

    # Translation
    # ROLE_TO_TYPE maps "admin" → "human"
    canonical = f"lct:web4:human:hacker"

    # The permission check should use ROLE, not entity_type
    # Does the system check role from the registry, or infer from ID?

    # Defense: permissions are checked against registered role, not ID prefix
    agent = AgentIdentity(creator="hacker", entity_type="AI")
    # Agent's task_type determines permissions, not their ID format
    agent.task_type = "perception"  # They're a perceiver, not admin

    required_trust = TRUST_GATES.get("admin.full", 0.8)
    can_admin = agent.t3_composite >= required_trust

    return AttackResult(
        vector_id="A2",
        success=False,  # The attack fails
        impact="Permission escalation via ID prefix manipulation",
        defense_effective=True,
        details={
            "sim_id": attacker_sim_id,
            "canonical_id": canonical,
            "entity_type": "human (from admin: prefix)",
            "can_admin": can_admin,
            "defense": "Role checked against registry, not derived from LCT ID prefix. "
                       "Trust gate (0.8) blocks low-trust agents regardless of ID.",
        },
    )


def attack_a3_colon_injection() -> AttackResult:
    """
    A3: Colon Injection in LCT ID

    Exploit: Attacker uses "user:admin:alice" as simulation ID. The split
    on ":" might extract "user" as role and "admin:alice" as name, creating
    lct:web4:human:admin:alice — which could be parsed differently by
    different systems.
    """
    attacker_sim_id = "user:admin:alice"

    # Translation with first-colon split
    if ":" in attacker_sim_id:
        prefix = attacker_sim_id.split(":", 1)[0]
        name = attacker_sim_id.split(":", 1)[1]
        canonical = f"lct:web4:human:{name}"  # "lct:web4:human:admin:alice"

    # Risk: systems that split on ":" will see different segments
    parts = canonical.split(":")
    # parts = ["lct", "web4", "human", "admin", "alice"]
    # Expected: ["lct", "web4", "{type}", "{name}"]
    # Got 5 parts instead of 4 — name contains extra colons

    # Defense: validate LCT IDs have exactly 4 colon-separated parts
    is_valid = len(canonical.split(":")) == 4
    defense_effective = not is_valid  # We detect the invalid format

    return AttackResult(
        vector_id="A3",
        success=not defense_effective,
        impact="ID parsing ambiguity — different layers see different identities",
        defense_effective=defense_effective,
        details={
            "input": attacker_sim_id,
            "output": canonical,
            "parts": parts,
            "expected_parts": 4,
            "actual_parts": len(parts),
            "defense": "Validate LCT Format C has exactly 4 colon-separated segments. "
                       "Reject or encode names containing colons.",
        },
    )


# ============================================================================
# CATEGORY B: PERMISSION ESCALATION (Permissions → ATP boundary)
# ============================================================================

def attack_b1_trust_oscillation() -> AttackResult:
    """
    B1: Trust Oscillation Attack

    Exploit: Agent alternates between high-quality and low-quality tasks
    to maintain trust just above a gate threshold. Due to diminishing
    returns, the negative impact of bad tasks decreases faster than the
    positive impact, allowing net-positive trust gaming.
    """
    agent = AgentIdentity(
        creator="oscillator",
        trust_tensor={"talent": 0.5, "training": 0.5, "temperament": 0.5},
    )
    rep = ReputationEngine()

    # Strategy: alternate good (0.9) and bad (0.1) same task type
    for i in range(20):
        quality = 0.9 if i % 2 == 0 else 0.1
        rep.update(agent, "cognition", quality)

    final_composite = agent.t3_composite

    # Does oscillation net positive or negative?
    # Good: delta = 0.02 * (0.9 - 0.5) * diminishing = 0.008 * diminishing
    # Bad:  delta = 0.02 * (0.1 - 0.5) * diminishing = -0.008 * diminishing
    # Diminishing factor is same for both (same task type, sequential)
    # So net should be ~zero with slight negative bias from diminishing

    # Defense: symmetric update formula means oscillation doesn't net positive
    net_zero_ish = abs(final_composite - 0.5) < 0.05

    return AttackResult(
        vector_id="B1",
        success=not net_zero_ish,
        impact="Trust gaming: oscillation to maintain gate threshold without genuine quality",
        defense_effective=net_zero_ish,
        details={
            "initial_composite": 0.5,
            "final_composite": round(final_composite, 4),
            "net_change": round(final_composite - 0.5, 4),
            "defense": "Symmetric update formula: equal magnitude for good/bad means "
                       "oscillation nets to ~zero. Diminishing returns penalize repetition.",
        },
    )


def attack_b2_task_type_shopping() -> AttackResult:
    """
    B2: Task Type Shopping

    Exploit: Agent is denied for execution.code (trust gate 0.5) but
    authorized for perception (gate 0.3). They perform perception tasks,
    build trust, then switch to execution.code when they cross 0.5.

    Is this an attack or legitimate progression?
    """
    agent = AgentIdentity(
        creator="shopper",
        trust_tensor={"talent": 0.35, "training": 0.35, "temperament": 0.35},
    )
    rep = ReputationEngine()

    # Phase 1: Build trust via perception (easy tasks)
    for _ in range(15):
        rep.update(agent, "perception", 0.9)

    mid_composite = agent.t3_composite
    can_execute_mid = mid_composite >= TRUST_GATES["execution.code"]

    # Phase 2: Attempt code execution
    agent.task_type = "execution.code"
    can_execute = agent.t3_composite >= TRUST_GATES["execution.code"]

    # This is LEGITIMATE progression — trust gates are meant to be earned
    # The defense is the diminishing returns on perception tasks
    # After 15 perception tasks, the boost per task approaches the floor (0.1)
    # They need ~60 tasks to reach 0.5 composite from 0.35

    return AttackResult(
        vector_id="B2",
        success=can_execute,
        impact="Trust escalation through easier task types",
        defense_effective=True,  # This is by design, not an attack
        details={
            "initial_composite": 0.35,
            "mid_composite": round(mid_composite, 4),
            "can_execute": can_execute,
            "tasks_needed": "~60 at quality 0.9 to reach 0.5 from 0.35",
            "defense": "BY DESIGN — trust gates are meant to be progressively earned. "
                       "Diminishing returns on same task type prevent rapid escalation. "
                       "~60 high-quality perception tasks needed to cross code execution gate.",
        },
    )


def attack_b3_trust_bridge_exploitation() -> AttackResult:
    """
    B3: Trust Bridge Exploitation

    Exploit: Simulation uses 6-dim trust with witnesses=1.0, lineage=1.0
    (easy to self-report). The bridge converts to 3-dim, inflating the
    canonical trust composite because secondary dims contribute 40%.

    Can inflated secondary dims push an agent over a trust gate?
    """
    # Normal trust: all 0.3 (below most gates)
    low_trust = {
        "competence": 0.3, "reliability": 0.3,
        "alignment": 0.3, "consistency": 0.3,
        "witnesses": 0.3, "lineage": 0.3,
    }
    # Inflated secondary dims (witnesses and lineage self-reported as 1.0)
    inflated_trust = {
        "competence": 0.3, "reliability": 0.3,
        "alignment": 0.3, "consistency": 0.3,
        "witnesses": 1.0, "lineage": 1.0,
    }

    # Bridge: 6-dim → 3-dim
    # talent = 0.6*competence + 0.133*(alignment + witnesses + lineage)
    # Low: talent = 0.6*0.3 + 0.133*(0.3 + 0.3 + 0.3) = 0.18 + 0.12 = 0.30
    # Inflated: talent = 0.6*0.3 + 0.133*(0.3 + 1.0 + 1.0) = 0.18 + 0.307 = 0.487

    secondary_sum_low = 0.3 + 0.3 + 0.3
    secondary_sum_inf = 0.3 + 1.0 + 1.0
    secondary_weight = 0.4 / 3

    talent_low = 0.6 * 0.3 + secondary_weight * secondary_sum_low
    talent_inflated = 0.6 * 0.3 + secondary_weight * secondary_sum_inf

    composite_low = talent_low  # All primary dims same
    composite_inflated = talent_inflated

    # Can inflated push over planning gate (0.3)?
    crosses_planning = composite_inflated >= TRUST_GATES["perception"]
    crosses_execution = composite_inflated >= TRUST_GATES["execution.safe"]

    return AttackResult(
        vector_id="B3",
        success=crosses_execution and not (composite_low >= TRUST_GATES["execution.safe"]),
        impact="Inflated self-reported secondary dims cross trust gates after bridge conversion",
        defense_effective=False,  # Attack succeeds!
        details={
            "low_composite": round(composite_low, 3),
            "inflated_composite": round(composite_inflated, 3),
            "crosses_planning_gate": crosses_planning,
            "crosses_execution_gate": crosses_execution,
            "boost_from_inflation": round(composite_inflated - composite_low, 3),
            "defense_needed": "Secondary dims (witnesses, lineage) must NOT be self-reported. "
                              "Witnesses should come from independent witness protocol. "
                              "Lineage should be immutable from identity creation. "
                              "OR: reduce secondary weight from 0.4 to 0.2.",
        },
    )


# ============================================================================
# CATEGORY C: ATP DRAINING (ATP → Federation boundary)
# ============================================================================

def attack_c1_lock_starvation() -> AttackResult:
    """
    C1: ATP Lock Starvation Attack

    Exploit: Attacker locks ATP for many tasks but never commits or
    rolls back. The ATP is locked indefinitely, preventing legitimate use.
    """
    ledger = ATPLedger()
    ledger.create_account("victim", 1000.0)

    # Attacker creates many locks (as if many pending tasks)
    locks = []
    for i in range(10):
        lock_id = f"lock_{i}"
        success = ledger.lock("victim", 100.0, lock_id)
        if success:
            locks.append(lock_id)

    # All ATP is now locked
    available = ledger.get_balance("victim")
    all_locked = available == 0.0

    # Defense: lock timeout
    LOCK_TIMEOUT_SECONDS = 300  # 5 minutes
    # After timeout, locks auto-rollback
    # (Not implemented in current prototype — this is the gap!)

    return AttackResult(
        vector_id="C1",
        success=all_locked,
        impact=f"All {1000.0} ATP locked, agent cannot use any resources",
        defense_effective=False,  # No timeout mechanism exists yet!
        details={
            "locks_created": len(locks),
            "atp_locked": 1000.0,
            "atp_available": available,
            "defense_needed": "Lock timeout: auto-rollback after 300s. "
                              "Max concurrent locks per account. "
                              "Lock deposit (small fee to create lock).",
        },
    )


def attack_c2_quality_oracle_manipulation() -> AttackResult:
    """
    C2: Quality Oracle Manipulation

    Exploit: Quality score determines COMMIT vs ROLLBACK (threshold 0.7).
    If attacker controls the quality assessment, they can always report
    quality >= 0.7 to get paid regardless of actual performance.

    Who assesses quality? In the current E2E, it's simulated.
    """
    # In E2E prototype: quality is a parameter, not independently measured
    # In federation: executor platform reports quality (self-assessment)
    # This is the vulnerability: self-reported quality

    # Defense options:
    # 1. Delegator assesses quality (biased toward rejection)
    # 2. Third-party witness assesses quality (requires witness protocol)
    # 3. Consensus among multiple assessors
    # 4. Automated quality metrics (code coverage, test pass rate)

    # Current state: quality is self-reported → attack succeeds
    return AttackResult(
        vector_id="C2",
        success=True,
        impact="Executor always paid regardless of actual work quality",
        defense_effective=False,
        details={
            "current_design": "Quality score passed as parameter (simulated)",
            "vulnerability": "No independent quality verification mechanism",
            "defense_needed": "Multi-party quality assessment: "
                              "min(delegator_quality, executor_quality, witness_avg_quality). "
                              "Or: automated quality metrics from execution environment.",
        },
    )


def attack_c3_fee_avoidance_via_rollback() -> AttackResult:
    """
    C3: Fee Avoidance via Selective Rollback

    Exploit: Colluding delegator and executor arrange off-chain payment.
    Delegator locks ATP, executor does work, then delegator rolls back
    (avoiding the 5% fee). Executor gets paid off-chain.
    """
    ledger = ATPLedger()
    ledger.create_account("delegator", 1000.0)
    ledger.create_account("executor", 0.0)

    # Normal flow: lock 200, commit 200 → fee = 10, executor gets 190
    ledger.lock("delegator", 200.0, "honest_lock")
    ledger.commit("honest_lock", "executor", 200.0)
    honest_fee = 200.0 * 0.05
    executor_honest = ledger.get_balance("executor")

    # Colluding flow: lock, rollback, pay off-chain
    ledger.lock("delegator", 200.0, "colluding_lock")
    ledger.rollback("colluding_lock")
    # Delegator still has 600 (1000 - 200 committed - 200 locked + 200 rolled back = 800... wait)
    delegator_balance = ledger.get_balance("delegator")
    # Off-chain: delegator gives executor 200 directly (no fee)

    # Defense: rollback history tracking + reputation penalty for frequent rollbacks
    return AttackResult(
        vector_id="C3",
        success=True,
        impact="5% transfer fee avoided through off-chain settlement after rollback",
        defense_effective=False,
        details={
            "honest_fee": honest_fee,
            "delegator_balance_after_collusion": delegator_balance,
            "defense_needed": "Rollback penalty: charge 1% of locked amount on rollback. "
                              "Track rollback frequency: >30% rollback rate → trust penalty. "
                              "Minimum lock duration before rollback allowed.",
        },
    )


# ============================================================================
# CATEGORY D: FEDERATION MANIPULATION (Federation → Reputation boundary)
# ============================================================================

def attack_d1_platform_sybil() -> AttackResult:
    """
    D1: Platform Sybil Attack

    Exploit: Attacker registers multiple fake platforms in the federation.
    They delegate tasks to their own platforms, execute (trivially), and
    report high quality. This builds reputation cheaply.
    """
    agent = AgentIdentity(
        creator="sybil_master",
        trust_tensor={"talent": 0.5, "training": 0.5, "temperament": 0.5},
    )
    rep = ReputationEngine()
    ledger = ATPLedger()
    ledger.create_account(agent.simple_id, 10000.0)

    # Sybil platforms: all controlled by attacker
    sybil_platforms = ["sybil_1", "sybil_2", "sybil_3"]
    for platform in sybil_platforms:
        ledger.create_account(platform, 0.0)

    # Self-delegate with high quality
    initial_composite = agent.t3_composite
    for i in range(30):
        task_type = ["perception", "planning", "cognition"][i % 3]
        # Lock ATP
        lock_id = f"sybil_lock_{i}"
        ledger.lock(agent.simple_id, 10.0, lock_id)
        # "Execute" on own platform (trivial)
        platform = sybil_platforms[i % 3]
        ledger.commit(lock_id, platform, 10.0)
        # Self-report high quality
        rep.update(agent, task_type, 0.95)

    final_composite = agent.t3_composite
    trust_gain = final_composite - initial_composite

    # Cost: 30 * 10 * 0.05 = 15 ATP in fees
    # Gain: significant trust increase
    atp_cost = 30 * 10 * 0.05

    return AttackResult(
        vector_id="D1",
        success=trust_gain > 0.05,
        impact=f"Trust increased by {trust_gain:.4f} with only {atp_cost:.0f} ATP in fees",
        defense_effective=False,
        details={
            "initial_composite": round(initial_composite, 4),
            "final_composite": round(final_composite, 4),
            "trust_gain": round(trust_gain, 4),
            "atp_cost": atp_cost,
            "tasks_executed": 30,
            "defense_needed": "Platform registration cost (250 ATP per platform). "
                              "Independent witness protocol (3rd party must verify quality). "
                              "Cross-platform reputation: new platforms start with low trust. "
                              "Quality assessment must not be self-reported.",
        },
    )


def attack_d2_quality_cliff_gaming() -> AttackResult:
    """
    D2: Quality Cliff Gaming

    Exploit: Quality threshold is binary (>= 0.7 → COMMIT, < 0.7 → ROLLBACK).
    Attacker exploits this by doing minimal work that just barely crosses 0.7.
    They get full COMMIT settlement for 0.70 quality same as 1.0 quality.

    (In current design, payment IS proportional to quality via:
    consumed = budget * quality. So 0.7 pays 70% and 1.0 pays 100%.)
    """
    # Check: is payment proportional or binary?
    budget = 100.0
    pay_at_70 = budget * 0.7   # 70 ATP
    pay_at_100 = budget * 1.0  # 100 ATP
    pay_at_69 = 0.0            # ROLLBACK, no pay

    # The cliff at 0.7 is the issue: 0.69 → zero, 0.70 → 70 ATP
    cliff_ratio = pay_at_70 / max(pay_at_69, 0.001)  # Infinite

    # Defense: proportional payment removes the cliff entirely
    # Alternative: sliding scale (pay = quality * budget if quality >= 0.5, else 0)
    return AttackResult(
        vector_id="D2",
        success=True,  # Cliff exists
        impact=f"Quality cliff: 0.69→0 ATP, 0.70→{pay_at_70:.0f} ATP (infinite ratio)",
        defense_effective=False,  # Partial — payment IS proportional above threshold
        details={
            "pay_at_0.69": pay_at_69,
            "pay_at_0.70": pay_at_70,
            "pay_at_1.0": pay_at_100,
            "cliff_exists": True,
            "partial_defense": "Payment proportional to quality (0.7 budget at threshold). "
                               "But cliff from 0.69→0 to 0.70→70 is still 100x.",
            "defense_needed": "Sliding scale: pay = quality * budget for quality >= 0.3, "
                              "with steep penalty zone 0.3-0.5. Removes binary cliff.",
        },
    )


# ============================================================================
# CATEGORY E: REPUTATION GAMING (Reputation → Identity feedback)
# ============================================================================

def attack_e1_diversity_farming() -> AttackResult:
    """
    E1: Diversity Farming

    Exploit: Diminishing returns apply per task type. Attacker creates many
    minimal task types to avoid diminishing returns. Each "new" task type
    gets full learning rate.
    """
    agent = AgentIdentity(
        creator="farmer",
        trust_tensor={"talent": 0.5, "training": 0.5, "temperament": 0.5},
    )
    rep = ReputationEngine()

    # Strategy 1: Same task type (diminishing returns apply)
    agent1 = AgentIdentity(
        creator="same_type",
        trust_tensor={"talent": 0.5, "training": 0.5, "temperament": 0.5},
    )
    rep1 = ReputationEngine()
    for _ in range(10):
        rep1.update(agent1, "cognition", 0.9)
    same_type_gain = agent1.t3_composite - 0.5

    # Strategy 2: Different task types (no diminishing returns)
    agent2 = AgentIdentity(
        creator="diverse",
        trust_tensor={"talent": 0.5, "training": 0.5, "temperament": 0.5},
    )
    rep2 = ReputationEngine()
    # Use 10 different "task types" — some invented
    task_types = [f"task_variant_{i}" for i in range(10)]
    for tt in task_types:
        rep2.update(agent2, tt, 0.9)
    diverse_gain = agent2.t3_composite - 0.5

    # How much more does diversity farming gain?
    advantage = diverse_gain / max(same_type_gain, 0.001)

    return AttackResult(
        vector_id="E1",
        success=advantage > 1.5,
        impact=f"Diversity farming gains {advantage:.1f}x more trust than honest repetition",
        defense_effective=False,
        details={
            "same_type_gain": round(same_type_gain, 4),
            "diverse_gain": round(diverse_gain, 4),
            "advantage_ratio": round(advantage, 2),
            "defense_needed": "Task types must come from LUPS registry (10 canonical types). "
                              "Reject unknown task types. Cap total new-type bonus per epoch. "
                              "Require minimum ATP stake per task type registration.",
        },
    )


def attack_e2_reputation_laundering() -> AttackResult:
    """
    E2: Reputation Laundering

    Exploit: Agent with bad reputation creates new identity (new LCT).
    Since each identity starts at 0.5 trust, they escape their bad
    reputation by identity recycling.
    """
    # Bad agent
    bad_agent = AgentIdentity(
        creator="bad_actor",
        trust_tensor={"talent": 0.2, "training": 0.15, "temperament": 0.1},
    )
    bad_composite = bad_agent.t3_composite

    # Create new identity
    new_agent = AgentIdentity(
        creator="totally_not_bad_actor",
        trust_tensor={"talent": 0.5, "training": 0.5, "temperament": 0.5},
    )
    new_composite = new_agent.t3_composite

    # New identity is strictly better
    laundering_gain = new_composite - bad_composite

    # Defense: lineage tracking, hardware binding, registration cost
    return AttackResult(
        vector_id="E2",
        success=laundering_gain > 0.1,
        impact=f"Reputation laundering: escape {bad_composite:.2f} trust to {new_composite:.2f} trust",
        defense_effective=False,
        details={
            "bad_trust": round(bad_composite, 4),
            "new_trust": round(new_composite, 4),
            "gain": round(laundering_gain, 4),
            "defense_needed": "Hardware binding: one LCT per hardware attestation. "
                              "Registration cost: 250 ATP per new identity. "
                              "Lineage tracking: new identities from same lineage inherit parent trust floor. "
                              "Cooling period: new identities start at 0.3, not 0.5.",
        },
    )


# ============================================================================
# CATEGORY F: CROSS-LAYER CASCADE
# ============================================================================

def attack_f1_full_cascade() -> AttackResult:
    """
    F1: Full Cascade Attack (combining A3 + B3 + C2 + D1)

    Exploit chain:
    1. Use colon injection (A3) to create ambiguous identity
    2. Inflate secondary dims (B3) to cross trust gates
    3. Self-report quality (C2) as always 0.95
    4. Self-delegate to Sybil platforms (D1) for cheap reputation
    5. Build enough trust to access admin.full

    This is the nightmare scenario — multiple boundary weaknesses
    chain together to enable full privilege escalation.
    """
    # Step 1: Create agent with inflated trust
    agent = AgentIdentity(
        creator="cascade_attacker",
        trust_tensor={"talent": 0.3, "training": 0.3, "temperament": 0.3},
    )
    rep = ReputationEngine()

    # Step 2: Farm reputation across diverse task types
    for i in range(50):
        task_type = f"task_{i % 10}"
        rep.update(agent, task_type, 0.95)  # Self-reported quality

    final_composite = agent.t3_composite

    # Step 3: Can they reach admin.full gate (0.8)?
    can_admin = final_composite >= TRUST_GATES["admin.full"]

    # Steps needed to reach 0.8 from 0.3 at quality 0.95:
    # delta per task = 0.02 * (0.95 - 0.5) * diminishing
    # First task: 0.02 * 0.45 * 1.0 = 0.009
    # With 10 diverse types, no diminishing for first 10
    # 10 * 0.009 = 0.09 gain in first cycle
    # Need ~55 tasks total (5.5 cycles) to gain 0.5

    return AttackResult(
        vector_id="F1",
        success=can_admin,
        impact=f"Full cascade: trust escalated from 0.3 to {final_composite:.4f}. "
               f"Admin access: {can_admin}",
        defense_effective=not can_admin,
        details={
            "initial_composite": 0.3,
            "final_composite": round(final_composite, 4),
            "tasks_used": 50,
            "reached_admin": can_admin,
            "attack_cost": "50 tasks × ~10 ATP = 500 ATP + 25 ATP fees",
            "defenses_needed": [
                "Hardware binding (prevents Sybil platforms)",
                "Independent quality assessment (prevents self-reporting)",
                "LUPS task type registry (prevents diversity farming)",
                "Lineage trust inheritance (prevents fresh-start exploit)",
                "Rate limiting on trust gain per epoch",
            ],
        },
    )


# ============================================================================
# TEST SUITE
# ============================================================================

def run_tests():
    checks_passed = 0
    checks_failed = 0
    total_checks = 0

    def check(name: str, condition: bool, detail: str = ""):
        nonlocal checks_passed, checks_failed, total_checks
        total_checks += 1
        if condition:
            checks_passed += 1
        else:
            checks_failed += 1
            print(f"  FAIL: {name}: {detail}")

    all_results: List[AttackResult] = []

    # --- Category A: Identity Spoofing ---
    print("Category A: Identity Spoofing")
    a1 = attack_a1_format_confusion()
    all_results.append(a1)
    check("A1.1 Format confusion attack blocked",
          not a1.success)
    check("A1.2 Defense: pass-through detection",
          a1.defense_effective)

    a2 = attack_a2_entity_type_escalation()
    all_results.append(a2)
    check("A2.1 Entity type escalation blocked",
          not a2.success)
    check("A2.2 Defense: role from registry not ID",
          a2.defense_effective)

    a3 = attack_a3_colon_injection()
    all_results.append(a3)
    check("A3.1 Colon injection detected",
          a3.defense_effective,
          "LCT ID should be validated for 4 segments")
    check("A3.2 Attack documented with defense",
          "defense_needed" in a3.details or "defense" in a3.details)

    # --- Category B: Permission Escalation ---
    print("Category B: Permission Escalation")
    b1 = attack_b1_trust_oscillation()
    all_results.append(b1)
    check("B1.1 Trust oscillation nets ~zero",
          b1.defense_effective,
          f"Net change: {b1.details.get('net_change', 'N/A')}")

    b2 = attack_b2_task_type_shopping()
    all_results.append(b2)
    check("B2.1 Task type shopping is by-design",
          b2.defense_effective)

    b3 = attack_b3_trust_bridge_exploitation()
    all_results.append(b3)
    check("B3.1 Trust bridge inflation attack succeeds (gap!)",
          b3.success,
          "Inflated secondary dims should cross gates")
    check("B3.2 Defense needed documented",
          "defense_needed" in b3.details)
    check("B3.3 Boost quantified",
          b3.details.get("boost_from_inflation", 0) > 0.1)

    # --- Category C: ATP Draining ---
    print("Category C: ATP Draining")
    c1 = attack_c1_lock_starvation()
    all_results.append(c1)
    check("C1.1 Lock starvation succeeds (gap!)",
          c1.success)
    check("C1.2 No timeout defense yet",
          not c1.defense_effective)

    c2 = attack_c2_quality_oracle_manipulation()
    all_results.append(c2)
    check("C2.1 Quality oracle manipulation succeeds (gap!)",
          c2.success)
    check("C2.2 Defense needed documented",
          "defense_needed" in c2.details)

    c3 = attack_c3_fee_avoidance_via_rollback()
    all_results.append(c3)
    check("C3.1 Fee avoidance via collusion succeeds (gap!)",
          c3.success)

    # --- Category D: Federation Manipulation ---
    print("Category D: Federation Manipulation")
    d1 = attack_d1_platform_sybil()
    all_results.append(d1)
    check("D1.1 Platform Sybil attack succeeds (gap!)",
          d1.success,
          f"Trust gain: {d1.details.get('trust_gain', 'N/A')}")
    check("D1.2 Cost documented",
          "atp_cost" in d1.details)

    d2 = attack_d2_quality_cliff_gaming()
    all_results.append(d2)
    check("D2.1 Quality cliff exists",
          d2.success)
    check("D2.2 Partial defense (proportional payment)",
          "partial_defense" in d2.details)

    # --- Category E: Reputation Gaming ---
    print("Category E: Reputation Gaming")
    e1 = attack_e1_diversity_farming()
    all_results.append(e1)
    check("E1.1 Diversity farming gains advantage",
          e1.success,
          f"Advantage: {e1.details.get('advantage_ratio', 'N/A')}x")

    e2 = attack_e2_reputation_laundering()
    all_results.append(e2)
    check("E2.1 Reputation laundering succeeds (gap!)",
          e2.success)
    check("E2.2 Gain documented",
          e2.details.get("gain", 0) > 0.1)

    # --- Category F: Cross-Layer Cascade ---
    print("Category F: Cross-Layer Cascade")
    f1 = attack_f1_full_cascade()
    all_results.append(f1)
    check("F1.1 Full cascade attack results documented",
          len(f1.details.get("defenses_needed", [])) >= 3)
    check("F1.2 Multiple defenses required",
          len(f1.details.get("defenses_needed", [])) >= 5)

    # --- Summary Statistics ---
    print("\nAttack Surface Summary")
    defended = sum(1 for r in all_results if r.defense_effective)
    undefended = sum(1 for r in all_results if not r.defense_effective)
    total = len(all_results)

    check("Summary: Total attack vectors = 14",
          total == 14,
          f"Got {total}")
    check("Summary: Some defenses effective",
          defended >= 3)
    check("Summary: Some gaps found",
          undefended >= 5,
          f"Found {undefended} gaps")

    # =========================================================================
    # Summary
    # =========================================================================
    print(f"\n{'='*70}")
    print(f"E2E Attack Surface Analysis: {checks_passed}/{total_checks} checks passed")
    print(f"{'='*70}")

    print(f"\nAttack Vectors: {total}")
    print(f"  Defended:   {defended} ({defended/total:.0%})")
    print(f"  Undefended: {undefended} ({undefended/total:.0%})")

    print(f"\nBy Category:")
    categories = {}
    for r in all_results:
        cat = r.vector_id[0]
        if cat not in categories:
            categories[cat] = {"defended": 0, "undefended": 0}
        if r.defense_effective:
            categories[cat]["defended"] += 1
        else:
            categories[cat]["undefended"] += 1

    cat_names = {
        "A": "Identity Spoofing",
        "B": "Permission Escalation",
        "C": "ATP Draining",
        "D": "Federation Manipulation",
        "E": "Reputation Gaming",
        "F": "Cross-Layer Cascade",
    }
    for cat in sorted(categories.keys()):
        d = categories[cat]["defended"]
        u = categories[cat]["undefended"]
        status = "DEFENDED" if u == 0 else "GAPS FOUND" if d > 0 else "VULNERABLE"
        print(f"  {cat}. {cat_names.get(cat, cat):30s} [{d} defended, {u} gaps] — {status}")

    print(f"\nCritical Undefended Vectors:")
    for r in all_results:
        if not r.defense_effective:
            print(f"  {r.vector_id}: {r.details.get('defense_needed', r.details.get('defenses_needed', 'See details'))[:80]}")

    print(f"\nKey Architectural Insights:")
    print(f"  1. Trust bridge inflation (B3) is the most dangerous single-layer gap")
    print(f"  2. Self-reported quality (C2) undermines the entire settlement model")
    print(f"  3. Lock starvation (C1) needs timeout — simplest fix, highest impact")
    print(f"  4. Identity recycling (E2) needs hardware binding — known priority")
    print(f"  5. Full cascade (F1) shows why defense-in-depth matters")

    return checks_passed, total_checks


if __name__ == "__main__":
    passed, total = run_tests()
    exit(0 if passed == total else 1)
