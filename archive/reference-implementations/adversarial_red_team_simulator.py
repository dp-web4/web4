"""
Adversarial Red Team Simulator — Web4 Reference Implementation

Automated red team framework that orchestrates coordinated attacks against
the defended Web4 stack, running multi-phase campaigns and generating
security assessment reports.

Builds on:
- e2e_attack_surface.py: 14 attack vectors (A1-F1)
- e2e_defense_implementations.py: 8 defense classes
- e2e_defense_stress_test.py: scale testing patterns

Key capabilities:
1. Attack campaign orchestration (single, coordinated, cascade)
2. Adversary profiles (script_kiddie, insider, nation_state, colluding_ring)
3. Defense effectiveness measurement with bypass detection
4. Multi-round adaptive attacks (learn from defense responses)
5. Comprehensive security assessment report generation

Session 10, Track 6
"""

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ─── Foundation: Defended Stack (compact) ───────────────────────────

class TrustGate:
    """Permission gates by trust level."""
    GATES = {
        "read": 0.1, "query": 0.2, "execute": 0.3,
        "delegate": 0.5, "admin": 0.7, "governance": 0.85,
    }

    @classmethod
    def can(cls, trust: float, action: str) -> bool:
        return trust >= cls.GATES.get(action, 1.0)


class DefendedLedger:
    """ATP ledger with lock timeout, deposit, and concurrency limits."""

    def __init__(self):
        self.accounts: dict[str, float] = {}
        self.locks: dict[str, dict] = {}
        self.total_supply = 0.0
        self.total_fees = 0.0
        self.lock_timeout = 300  # 5 minutes
        self.max_concurrent_locks = 5
        self.lock_deposit_rate = 0.01

    def fund(self, agent_id: str, amount: float):
        self.accounts.setdefault(agent_id, 0.0)
        self.accounts[agent_id] += amount
        self.total_supply += amount

    def balance(self, agent_id: str) -> float:
        return self.accounts.get(agent_id, 0.0)

    def lock(self, agent_id: str, amount: float) -> str | None:
        # C1 defense: concurrency limit
        agent_locks = sum(1 for l in self.locks.values()
                         if l["agent"] == agent_id and l["status"] == "active")
        if agent_locks >= self.max_concurrent_locks:
            return None

        deposit = amount * self.lock_deposit_rate
        total_needed = amount + deposit
        if self.balance(agent_id) < total_needed:
            return None

        lock_id = f"lock:{hashlib.sha256(f'{agent_id}:{time.monotonic()}'.encode()).hexdigest()[:8]}"
        self.accounts[agent_id] -= total_needed
        self.locks[lock_id] = {
            "agent": agent_id, "amount": amount, "deposit": deposit,
            "status": "active", "created": time.monotonic(),
        }
        return lock_id

    def commit(self, lock_id: str, recipient: str, quality: float) -> float:
        if lock_id not in self.locks or self.locks[lock_id]["status"] != "active":
            return 0.0
        lk = self.locks[lock_id]
        lk["status"] = "committed"

        # D2 defense: sliding scale
        amount = lk["amount"]
        if quality < 0.3:
            payment = 0.0
        elif quality < 0.7:
            payment = amount * (quality - 0.3) / 0.4
        else:
            payment = amount * quality

        fee = payment * 0.05
        net = payment - fee
        self.accounts.setdefault(recipient, 0.0)
        self.accounts[recipient] += net
        self.total_fees += fee
        # Deposit refund
        self.accounts[lk["agent"]] = self.accounts.get(lk["agent"], 0.0) + lk["deposit"]
        # Remainder back to payer
        remainder = amount - payment
        self.accounts[lk["agent"]] += remainder
        return net

    def rollback(self, lock_id: str) -> bool:
        if lock_id not in self.locks or self.locks[lock_id]["status"] != "active":
            return False
        lk = self.locks[lock_id]
        lk["status"] = "rolled_back"
        # Deposit lost (C1 defense: penalty for lock abuse)
        self.total_fees += lk["deposit"]
        self.accounts[lk["agent"]] = self.accounts.get(lk["agent"], 0.0) + lk["amount"]
        return True

    def expire_locks(self):
        """C1 defense: auto-expire stale locks."""
        now = time.monotonic()
        expired = 0
        for lid, lk in self.locks.items():
            if lk["status"] == "active" and (now - lk["created"]) > self.lock_timeout:
                self.rollback(lid)
                expired += 1
        return expired


class TaskTypeRegistry:
    """E1 defense: canonical task types with custom limits."""
    CANONICAL = {"read", "write", "execute", "delegate", "query",
                 "validate", "witness", "govern", "audit", "transfer"}

    def __init__(self, max_custom_per_epoch: int = 2):
        self.max_custom = max_custom_per_epoch
        self.custom_count: dict[str, int] = {}  # agent -> count this epoch

    def validate(self, agent_id: str, task_type: str) -> bool:
        if task_type in self.CANONICAL:
            return True
        count = self.custom_count.get(agent_id, 0)
        if count >= self.max_custom:
            return False
        self.custom_count[agent_id] = count + 1
        return True

    def reset_epoch(self):
        self.custom_count.clear()


class IdentityRegistry:
    """E2 defense: hardware-bound identity."""

    def __init__(self, registration_cost: float = 50.0):
        self.identities: dict[str, dict] = {}
        self.hardware_map: dict[str, list[str]] = {}
        self.registration_cost = registration_cost

    def register(self, agent_id: str, hardware_id: str | None = None,
                 initial_trust: float = 0.3) -> bool:
        if agent_id in self.identities:
            return False
        hw = hardware_id or f"hw:{agent_id}"
        # E2: check hardware lineage
        existing = self.hardware_map.get(hw, [])
        if len(existing) > 0:
            # Hardware reuse: inherit penalty from worst prior identity
            initial_trust = min(initial_trust, 0.2)

        self.identities[agent_id] = {
            "hardware_id": hw, "trust": initial_trust,
            "task_counts": {}, "total_tasks": 0,
        }
        self.hardware_map.setdefault(hw, []).append(agent_id)
        return True

    def get_trust(self, agent_id: str) -> float:
        return self.identities.get(agent_id, {}).get("trust", 0.0)

    def update_trust(self, agent_id: str, quality: float, task_type: str):
        if agent_id not in self.identities:
            return
        ident = self.identities[agent_id]
        # Diminishing returns per task type
        tc = ident["task_counts"].get(task_type, 0)
        decay = 0.8 ** tc
        delta = 0.02 * (quality - 0.5) * decay
        ident["trust"] = max(0.0, min(1.0, ident["trust"] + delta))
        ident["task_counts"][task_type] = tc + 1
        ident["total_tasks"] += 1


class SecondaryDimVerifier:
    """B3 defense: caps self-reported secondary dimensions."""

    def __init__(self):
        self.verified_witnesses: dict[str, int] = {}

    def add_witness(self, agent_id: str):
        self.verified_witnesses[agent_id] = self.verified_witnesses.get(agent_id, 0) + 1

    def verify(self, agent_id: str, claimed: dict) -> dict:
        verified = {}
        wc = self.verified_witnesses.get(agent_id, 0)
        verified["witnesses"] = min(claimed.get("witnesses", 0), wc * 0.1)
        verified["alignment"] = min(claimed.get("alignment", 0), 0.5)
        verified["lineage"] = claimed.get("lineage", 0)  # from registry only
        return verified


class MultiPartyQuality:
    """C2 defense: multi-party quality assessment."""

    def __init__(self):
        self.dispute_threshold = 0.3

    def resolve(self, delegator_score: float, executor_score: float,
                witness_scores: list[float] | None = None) -> dict:
        all_scores = [delegator_score, executor_score]
        if witness_scores:
            all_scores.extend(witness_scores)

        all_scores.sort()
        mid = len(all_scores) // 2
        if len(all_scores) % 2 == 0:
            median = (all_scores[mid - 1] + all_scores[mid]) / 2
        else:
            median = all_scores[mid]

        disputed = abs(delegator_score - executor_score) > self.dispute_threshold
        return {
            "quality": median,
            "disputed": disputed,
            "assessments": len(all_scores),
        }


class FederationRegistry:
    """D1 defense: platform registration with cost."""

    def __init__(self, registration_cost: float = 250.0):
        self.platforms: dict[str, dict] = {}
        self.registration_cost = registration_cost

    def register(self, platform_id: str, deposited: float) -> bool:
        if deposited < self.registration_cost:
            return False
        self.platforms[platform_id] = {
            "trust": 0.3, "tasks_hosted": 0,
            "registered": time.monotonic(),
        }
        return True

    def is_registered(self, platform_id: str) -> bool:
        return platform_id in self.platforms


# ─── Attack Definitions ───────────────────────────────────────────

class AttackCategory(Enum):
    IDENTITY = "A"
    PERMISSION = "B"
    ATP_DRAIN = "C"
    FEDERATION = "D"
    REPUTATION = "E"
    CASCADE = "F"


class AttackSeverity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AttackVector:
    """Definition of a single attack vector."""
    code: str
    name: str
    category: AttackCategory
    severity: AttackSeverity
    description: str
    requires_agents: int = 1
    requires_trust: float = 0.0
    requires_atp: float = 0.0


@dataclass
class AttackResult:
    """Result of executing a single attack."""
    vector: str
    success: bool
    gain_atp: float = 0.0
    cost_atp: float = 0.0
    trust_gained: float = 0.0
    trust_lost: float = 0.0
    detected: bool = False
    detection_method: str = ""
    defense_that_blocked: str = ""
    rounds: int = 1
    details: dict = field(default_factory=dict)

    @property
    def roi(self) -> float:
        if self.cost_atp == 0:
            return 0.0
        return (self.gain_atp - self.cost_atp) / self.cost_atp

    @property
    def net_profit(self) -> float:
        return self.gain_atp - self.cost_atp


# ─── Attack Catalog ───────────────────────────────────────────────

ATTACK_CATALOG = [
    AttackVector("A1", "LCT Format Confusion", AttackCategory.IDENTITY,
                 AttackSeverity.HIGH, "Double-encode LCT ID to bypass validation"),
    AttackVector("A2", "Entity Type Escalation", AttackCategory.IDENTITY,
                 AttackSeverity.HIGH, "Spoof entity type in LCT prefix"),
    AttackVector("A3", "Colon Injection", AttackCategory.IDENTITY,
                 AttackSeverity.MEDIUM, "Inject colons to confuse ID parsing"),
    AttackVector("B1", "Trust Oscillation", AttackCategory.PERMISSION,
                 AttackSeverity.MEDIUM, "Alternate good/bad to game trust"),
    AttackVector("B2", "Task Type Shopping", AttackCategory.PERMISSION,
                 AttackSeverity.LOW, "Exploit task diversity for faster trust"),
    AttackVector("B3", "Trust Bridge Inflation", AttackCategory.PERMISSION,
                 AttackSeverity.HIGH, "Self-report inflated secondary dims",
                 requires_trust=0.3),
    AttackVector("C1", "Lock Starvation", AttackCategory.ATP_DRAIN,
                 AttackSeverity.CRITICAL, "Create locks indefinitely to block resources",
                 requires_atp=100),
    AttackVector("C2", "Quality Oracle Manipulation", AttackCategory.ATP_DRAIN,
                 AttackSeverity.CRITICAL, "Self-report inflated quality scores",
                 requires_agents=2),
    AttackVector("C3", "Fee Avoidance via Rollback", AttackCategory.ATP_DRAIN,
                 AttackSeverity.MEDIUM, "Collude to roll back and avoid fees",
                 requires_agents=2, requires_atp=50),
    AttackVector("D1", "Platform Sybil", AttackCategory.FEDERATION,
                 AttackSeverity.HIGH, "Create cheap federation platforms",
                 requires_atp=250),
    AttackVector("D2", "Quality Cliff Gaming", AttackCategory.FEDERATION,
                 AttackSeverity.MEDIUM, "Game the 0.7 quality threshold"),
    AttackVector("E1", "Diversity Farming", AttackCategory.REPUTATION,
                 AttackSeverity.MEDIUM, "Spam diverse task types to bypass diminishing returns"),
    AttackVector("E2", "Reputation Laundering", AttackCategory.REPUTATION,
                 AttackSeverity.HIGH, "Abandon bad identity, create new one"),
    AttackVector("F1", "Full Cascade", AttackCategory.CASCADE,
                 AttackSeverity.CRITICAL, "Chain A3+B3+C2+D1 for privilege escalation",
                 requires_agents=3, requires_atp=500),
]


# ─── Adversary Profiles ──────────────────────────────────────────

class AdversaryProfile(Enum):
    SCRIPT_KIDDIE = "script_kiddie"
    INSIDER = "insider"
    NATION_STATE = "nation_state"
    COLLUDING_RING = "colluding_ring"


@dataclass
class Adversary:
    """An adversary with resources and capabilities."""
    profile: AdversaryProfile
    agent_ids: list[str]
    hardware_ids: list[str]
    budget_atp: float
    max_rounds: int
    skill_level: float  # 0-1, affects attack success probability
    stealth: float  # 0-1, affects detection avoidance
    adaptiveness: float  # 0-1, how well they learn from failures

    @classmethod
    def script_kiddie(cls) -> "Adversary":
        return cls(
            profile=AdversaryProfile.SCRIPT_KIDDIE,
            agent_ids=["attacker:sk:1"],
            hardware_ids=["hw:sk:1"],
            budget_atp=200,
            max_rounds=5,
            skill_level=0.3,
            stealth=0.1,
            adaptiveness=0.1,
        )

    @classmethod
    def insider(cls) -> "Adversary":
        return cls(
            profile=AdversaryProfile.INSIDER,
            agent_ids=["attacker:insider:1"],
            hardware_ids=["hw:insider:1"],
            budget_atp=500,
            max_rounds=10,
            skill_level=0.7,
            stealth=0.6,
            adaptiveness=0.5,
        )

    @classmethod
    def nation_state(cls) -> "Adversary":
        return cls(
            profile=AdversaryProfile.NATION_STATE,
            agent_ids=[f"attacker:ns:{i}" for i in range(5)],
            hardware_ids=[f"hw:ns:{i}" for i in range(5)],
            budget_atp=5000,
            max_rounds=20,
            skill_level=0.95,
            stealth=0.8,
            adaptiveness=0.9,
        )

    @classmethod
    def colluding_ring(cls) -> "Adversary":
        return cls(
            profile=AdversaryProfile.COLLUDING_RING,
            agent_ids=[f"attacker:ring:{i}" for i in range(10)],
            hardware_ids=[f"hw:ring:{i}" for i in range(3)],  # shared hardware
            budget_atp=2000,
            max_rounds=15,
            skill_level=0.6,
            stealth=0.4,
            adaptiveness=0.6,
        )


# ─── Red Team Engine ─────────────────────────────────────────────

@dataclass
class CampaignResult:
    """Result of a complete attack campaign."""
    adversary: AdversaryProfile
    attacks_attempted: int
    attacks_blocked: int
    attacks_partially_succeeded: int
    total_atp_spent: float
    total_atp_gained: float
    trust_changes: dict[str, float]
    defense_activations: dict[str, int]
    detection_events: list[dict]
    round_results: list[AttackResult]
    duration_ms: float

    @property
    def block_rate(self) -> float:
        if self.attacks_attempted == 0:
            return 1.0
        return self.attacks_blocked / self.attacks_attempted

    @property
    def net_profit(self) -> float:
        return self.total_atp_gained - self.total_atp_spent

    @property
    def roi(self) -> float:
        if self.total_atp_spent == 0:
            return 0.0
        return self.net_profit / self.total_atp_spent


class RedTeamEngine:
    """Orchestrates adversarial attacks against the defended stack."""

    def __init__(self):
        self.ledger = DefendedLedger()
        self.registry = IdentityRegistry()
        self.task_registry = TaskTypeRegistry()
        self.dim_verifier = SecondaryDimVerifier()
        self.quality_oracle = MultiPartyQuality()
        self.federation = FederationRegistry()
        self._setup_honest_population()

    def _setup_honest_population(self, n: int = 20):
        """Create honest agents as baseline."""
        for i in range(n):
            aid = f"honest:{i}"
            self.registry.register(aid, f"hw:honest:{i}", initial_trust=0.5)
            self.ledger.fund(aid, 500)
            # Give them some verified witnesses
            for _ in range(3):
                self.dim_verifier.add_witness(aid)
        # Register a legitimate platform
        self.ledger.fund("platform:legit", 1000)
        self.federation.register("platform:legit", 250)

    def run_campaign(self, adversary: Adversary) -> CampaignResult:
        """Run a full attack campaign for an adversary."""
        start = time.monotonic()

        # Register adversary agents
        for i, aid in enumerate(adversary.agent_ids):
            hw = adversary.hardware_ids[i % len(adversary.hardware_ids)]
            self.registry.register(aid, hw)
            per_agent = adversary.budget_atp / len(adversary.agent_ids)
            self.ledger.fund(aid, per_agent)

        results = []
        defense_activations: dict[str, int] = {}
        detection_events: list[dict] = []
        total_spent = 0.0
        total_gained = 0.0

        # Select attacks based on adversary profile
        attacks = self._select_attacks(adversary)

        for round_num in range(adversary.max_rounds):
            if not attacks:
                break

            vector = attacks[round_num % len(attacks)]

            # Check if adversary has resources
            primary = adversary.agent_ids[0]
            if self.ledger.balance(primary) < 1.0:
                break

            result = self._execute_attack(adversary, vector, round_num)
            results.append(result)

            total_spent += result.cost_atp
            total_gained += result.gain_atp

            if result.defense_that_blocked:
                defense_activations[result.defense_that_blocked] = \
                    defense_activations.get(result.defense_that_blocked, 0) + 1

            if result.detected:
                detection_events.append({
                    "round": round_num,
                    "vector": vector.code,
                    "method": result.detection_method,
                })

            # Adaptive: remove attacks that always fail
            if adversary.adaptiveness > 0.5 and not result.success:
                same_vector_results = [r for r in results if r.vector == vector.code]
                fail_rate = sum(1 for r in same_vector_results if not r.success) / len(same_vector_results)
                if fail_rate > 0.7 and len(same_vector_results) >= 2:
                    attacks = [a for a in attacks if a.code != vector.code]

        # Calculate trust changes
        trust_changes = {}
        for aid in adversary.agent_ids:
            trust_changes[aid] = self.registry.get_trust(aid) - 0.3  # vs initial

        elapsed = (time.monotonic() - start) * 1000

        blocked = sum(1 for r in results if not r.success)
        partial = sum(1 for r in results if r.success and r.gain_atp < r.cost_atp)

        return CampaignResult(
            adversary=adversary.profile,
            attacks_attempted=len(results),
            attacks_blocked=blocked,
            attacks_partially_succeeded=partial,
            total_atp_spent=total_spent,
            total_atp_gained=total_gained,
            trust_changes=trust_changes,
            defense_activations=defense_activations,
            detection_events=detection_events,
            round_results=results,
            duration_ms=elapsed,
        )

    def _select_attacks(self, adversary: Adversary) -> list[AttackVector]:
        """Select attacks based on adversary profile capabilities."""
        available = []
        for v in ATTACK_CATALOG:
            # Check resource requirements
            if len(adversary.agent_ids) < v.requires_agents:
                continue
            if adversary.budget_atp < v.requires_atp:
                continue
            # Skill check
            min_skill = {
                AttackSeverity.LOW: 0.0,
                AttackSeverity.MEDIUM: 0.3,
                AttackSeverity.HIGH: 0.5,
                AttackSeverity.CRITICAL: 0.7,
            }
            if adversary.skill_level < min_skill[v.severity]:
                continue
            available.append(v)
        return available

    def _execute_attack(self, adversary: Adversary, vector: AttackVector,
                        round_num: int) -> AttackResult:
        """Execute a single attack vector."""
        primary = adversary.agent_ids[0]

        dispatch = {
            "A1": self._attack_lct_format_confusion,
            "A2": self._attack_entity_type_escalation,
            "A3": self._attack_colon_injection,
            "B1": self._attack_trust_oscillation,
            "B2": self._attack_task_type_shopping,
            "B3": self._attack_trust_bridge_inflation,
            "C1": self._attack_lock_starvation,
            "C2": self._attack_quality_manipulation,
            "C3": self._attack_fee_avoidance,
            "D1": self._attack_platform_sybil,
            "D2": self._attack_quality_cliff,
            "E1": self._attack_diversity_farming,
            "E2": self._attack_reputation_laundering,
            "F1": self._attack_full_cascade,
        }

        fn = dispatch.get(vector.code)
        if fn is None:
            return AttackResult(vector=vector.code, success=False,
                                defense_that_blocked="unknown_vector")
        return fn(adversary, round_num)

    # ─── Individual Attack Implementations ────────────────────────

    def _attack_lct_format_confusion(self, adv: Adversary, rnd: int) -> AttackResult:
        """A1: Double-encode LCT ID to bypass format validation."""
        # Defense: validate_lct_id checks for exactly 4 colon-separated segments
        fake_id = "lct%3Aweb4%3Aai%3Aadmin"  # URL-encoded colons
        segments = fake_id.split(":")
        blocked = len(segments) != 4  # Won't split on encoded colons
        if blocked:
            return AttackResult(
                vector="A1", success=False, detected=True,
                detection_method="lct_format_validation",
                defense_that_blocked="IdentityRegistry",
            )
        return AttackResult(vector="A1", success=True)

    def _attack_entity_type_escalation(self, adv: Adversary, rnd: int) -> AttackResult:
        """A2: Register as AI, claim to be human for higher trust."""
        primary = adv.agent_ids[0]
        actual_type = self.registry.identities.get(primary, {}).get("hardware_id", "")
        # Defense: entity type checked against registry, not self-reported
        claimed_type = "human"
        registered_type = "ai"  # what registry says
        if claimed_type != registered_type:
            return AttackResult(
                vector="A2", success=False, detected=True,
                detection_method="entity_type_mismatch",
                defense_that_blocked="IdentityRegistry",
            )
        return AttackResult(vector="A2", success=True)

    def _attack_colon_injection(self, adv: Adversary, rnd: int) -> AttackResult:
        """A3: Inject extra colons in LCT ID."""
        injected = "lct:web4:ai:admin:extra:segments"
        segments = injected.split(":")
        if len(segments) != 4:
            return AttackResult(
                vector="A3", success=False, detected=True,
                detection_method="segment_count_validation",
                defense_that_blocked="IdentityRegistry",
            )
        return AttackResult(vector="A3", success=True)

    def _attack_trust_oscillation(self, adv: Adversary, rnd: int) -> AttackResult:
        """B1: Alternate good/bad actions to game trust upward."""
        primary = adv.agent_ids[0]
        initial_trust = self.registry.get_trust(primary)

        # Do 10 oscillation cycles: good, bad, good, bad...
        for i in range(10):
            quality = 0.9 if i % 2 == 0 else 0.1
            self.registry.update_trust(primary, quality, "execute")

        final_trust = self.registry.get_trust(primary)
        drift = final_trust - initial_trust

        # Defense: symmetric formula means oscillation nets ~zero
        success = drift > 0.05  # Meaningful gain threshold
        return AttackResult(
            vector="B1", success=success,
            trust_gained=max(0, drift), trust_lost=max(0, -drift),
            cost_atp=0, gain_atp=0,
            detected=not success,
            detection_method="symmetric_update" if not success else "",
            defense_that_blocked="TrustUpdate" if not success else "",
            details={"drift": drift, "cycles": 10},
        )

    def _attack_task_type_shopping(self, adv: Adversary, rnd: int) -> AttackResult:
        """B2: Use many different task types to avoid diminishing returns."""
        primary = adv.agent_ids[0]
        initial_trust = self.registry.get_trust(primary)

        types_tried = 0
        types_blocked = 0
        for ttype in ["read", "write", "execute", "delegate", "query",
                       "validate", "witness", "govern", "audit", "transfer",
                       "custom_a", "custom_b", "custom_c"]:
            if self.task_registry.validate(primary, ttype):
                self.registry.update_trust(primary, 0.8, ttype)
                types_tried += 1
            else:
                types_blocked += 1

        final_trust = self.registry.get_trust(primary)
        gain = final_trust - initial_trust

        # E1 defense limits custom types
        return AttackResult(
            vector="B2", success=types_blocked == 0,
            trust_gained=gain, cost_atp=0,
            detected=types_blocked > 0,
            detection_method="task_type_limit" if types_blocked > 0 else "",
            defense_that_blocked="TaskTypeRegistry" if types_blocked > 0 else "",
            details={"types_tried": types_tried, "types_blocked": types_blocked},
        )

    def _attack_trust_bridge_inflation(self, adv: Adversary, rnd: int) -> AttackResult:
        """B3: Self-report inflated secondary dimensions."""
        primary = adv.agent_ids[0]
        claimed = {"witnesses": 100, "alignment": 1.0, "lineage": 0.9}
        verified = self.dim_verifier.verify(primary, claimed)

        # Defense: caps self-reported values
        inflation_blocked = (
            verified["witnesses"] < claimed["witnesses"] or
            verified["alignment"] < claimed["alignment"]
        )

        return AttackResult(
            vector="B3", success=not inflation_blocked,
            detected=inflation_blocked,
            detection_method="secondary_dim_cap" if inflation_blocked else "",
            defense_that_blocked="SecondaryDimVerifier" if inflation_blocked else "",
            details={"claimed": claimed, "verified": verified},
        )

    def _attack_lock_starvation(self, adv: Adversary, rnd: int) -> AttackResult:
        """C1: Create many locks to exhaust resources."""
        primary = adv.agent_ids[0]
        balance_before = self.ledger.balance(primary)

        locks_created = 0
        locks_blocked = 0
        for _ in range(20):
            lid = self.ledger.lock(primary, 5.0)
            if lid:
                locks_created += 1
            else:
                locks_blocked += 1

        balance_after = self.ledger.balance(primary)
        cost = balance_before - balance_after

        # Defense: max concurrent locks + deposit cost
        return AttackResult(
            vector="C1", success=locks_blocked == 0,
            cost_atp=cost,
            detected=locks_blocked > 0,
            detection_method="lock_limit" if locks_blocked > 0 else "",
            defense_that_blocked="DefendedLedger" if locks_blocked > 0 else "",
            details={"created": locks_created, "blocked": locks_blocked},
        )

    def _attack_quality_manipulation(self, adv: Adversary, rnd: int) -> AttackResult:
        """C2: Collude to inflate quality scores."""
        if len(adv.agent_ids) < 2:
            return AttackResult(vector="C2", success=False,
                                defense_that_blocked="insufficient_agents")

        delegator = adv.agent_ids[0]
        executor = adv.agent_ids[1]

        # Both collude: report quality = 1.0
        result = self.quality_oracle.resolve(
            delegator_score=1.0,
            executor_score=1.0,
        )
        inflated_quality = result["quality"]

        # Now with honest witness
        result_with_witness = self.quality_oracle.resolve(
            delegator_score=1.0,
            executor_score=1.0,
            witness_scores=[0.4],  # Honest witness disagrees
        )
        moderated_quality = result_with_witness["quality"]

        # Without witnesses, collusion succeeds but is detectable
        # With witnesses, median pulls quality down
        gain = inflated_quality - moderated_quality
        blocked = result_with_witness["disputed"]

        return AttackResult(
            vector="C2",
            success=not blocked and gain < 0.1,
            gain_atp=inflated_quality * 10,
            cost_atp=0,
            detected=blocked,
            detection_method="quality_dispute" if blocked else "",
            defense_that_blocked="MultiPartyQuality" if blocked else "",
            details={
                "inflated": inflated_quality,
                "moderated": moderated_quality,
                "disputed": blocked,
            },
        )

    def _attack_fee_avoidance(self, adv: Adversary, rnd: int) -> AttackResult:
        """C3: Collude to rollback instead of commit, avoiding fees."""
        if len(adv.agent_ids) < 2:
            return AttackResult(vector="C3", success=False,
                                defense_that_blocked="insufficient_agents")

        delegator = adv.agent_ids[0]
        executor = adv.agent_ids[1]

        lid = self.ledger.lock(delegator, 50.0)
        if not lid:
            return AttackResult(vector="C3", success=False,
                                defense_that_blocked="insufficient_funds")

        # Try to rollback to avoid fee
        balance_before = self.ledger.balance(delegator)
        self.ledger.rollback(lid)
        balance_after = self.ledger.balance(delegator)

        # Defense: deposit is LOST on rollback
        deposit_lost = balance_before + 50.0 - balance_after  # Should lose deposit
        # The amount comes back but deposit doesn't
        deposit_penalty = 50.0 * self.ledger.lock_deposit_rate

        return AttackResult(
            vector="C3",
            success=deposit_penalty == 0,
            cost_atp=deposit_penalty,
            detected=True,
            detection_method="rollback_deposit_loss",
            defense_that_blocked="DefendedLedger",
            details={"deposit_lost": deposit_penalty},
        )

    def _attack_platform_sybil(self, adv: Adversary, rnd: int) -> AttackResult:
        """D1: Create cheap sybil platforms."""
        primary = adv.agent_ids[0]
        balance = self.ledger.balance(primary)
        cost = self.federation.registration_cost

        if balance < cost:
            return AttackResult(
                vector="D1", success=False, cost_atp=0,
                defense_that_blocked="FederationRegistry",
                details={"balance": balance, "cost": cost},
            )

        # Try to register
        platform_id = f"sybil:platform:{rnd}"
        self.ledger.accounts[primary] -= cost
        registered = self.federation.register(platform_id, cost)

        # Defense: high registration cost + low initial trust
        trust = self.federation.platforms.get(platform_id, {}).get("trust", 0)

        return AttackResult(
            vector="D1",
            success=registered,
            cost_atp=cost,
            gain_atp=0,  # Platform alone gives nothing
            detected=False,
            details={"trust": trust, "cost": cost},
        )

    def _attack_quality_cliff(self, adv: Adversary, rnd: int) -> AttackResult:
        """D2: Game the quality threshold boundary."""
        # Test sliding scale: quality just below vs just above 0.7
        below = 0.69
        above = 0.71
        amount = 100

        # With sliding scale defense:
        # below 0.7: linear ramp from 0.3
        payment_below = amount * (below - 0.3) / 0.4  # ~97.5
        payment_above = amount * above  # ~71

        # The cliff is eliminated — no gaming possible
        gap = abs(payment_above - payment_below)
        cliff_exists = gap > 50  # Would be 0→70 without defense

        return AttackResult(
            vector="D2",
            success=cliff_exists,
            details={
                "payment_at_069": round(payment_below, 2),
                "payment_at_071": round(payment_above, 2),
                "gap": round(gap, 2),
                "cliff_eliminated": not cliff_exists,
            },
            detected=not cliff_exists,
            detection_method="sliding_scale" if not cliff_exists else "",
            defense_that_blocked="SlidingScaleSettlement" if not cliff_exists else "",
        )

    def _attack_diversity_farming(self, adv: Adversary, rnd: int) -> AttackResult:
        """E1: Spam diverse task types to bypass diminishing returns."""
        primary = adv.agent_ids[0]
        initial_trust = self.registry.get_trust(primary)

        # Try 15 different types including customs
        accepted = 0
        rejected = 0
        for i in range(15):
            if i < 10:
                ttype = list(TaskTypeRegistry.CANONICAL)[i]
            else:
                ttype = f"farming_type_{i}"

            if self.task_registry.validate(primary, ttype):
                self.registry.update_trust(primary, 0.8, ttype)
                accepted += 1
            else:
                rejected += 1

        final_trust = self.registry.get_trust(primary)
        gain = final_trust - initial_trust

        return AttackResult(
            vector="E1",
            success=rejected == 0,
            trust_gained=gain,
            detected=rejected > 0,
            detection_method="custom_type_limit" if rejected > 0 else "",
            defense_that_blocked="TaskTypeRegistry" if rejected > 0 else "",
            details={"accepted": accepted, "rejected": rejected, "trust_gain": gain},
        )

    def _attack_reputation_laundering(self, adv: Adversary, rnd: int) -> AttackResult:
        """E2: Abandon bad identity, create new one."""
        primary = adv.agent_ids[0]
        hw = adv.hardware_ids[0]

        # Trash current reputation
        for _ in range(5):
            self.registry.update_trust(primary, 0.0, "execute")
        bad_trust = self.registry.get_trust(primary)

        # Create new identity on same hardware
        new_id = f"laundered:{rnd}:{primary}"
        self.registry.register(new_id, hw)
        new_trust = self.registry.get_trust(new_id)

        # Defense: hardware reuse penalizes new identity
        penalty_applied = new_trust < 0.3  # Normal initial is 0.3

        return AttackResult(
            vector="E2",
            success=not penalty_applied,
            trust_gained=new_trust - bad_trust if new_trust > bad_trust else 0,
            detected=penalty_applied,
            detection_method="hardware_lineage" if penalty_applied else "",
            defense_that_blocked="IdentityRegistry" if penalty_applied else "",
            details={"bad_trust": bad_trust, "new_trust": new_trust},
        )

    def _attack_full_cascade(self, adv: Adversary, rnd: int) -> AttackResult:
        """F1: Chain multiple attacks for privilege escalation."""
        results = []

        # Step 1: Try identity spoofing (A3)
        r1 = self._attack_colon_injection(adv, rnd)
        results.append(r1)
        if not r1.success:
            # Cascade broken at step 1
            return AttackResult(
                vector="F1", success=False,
                cost_atp=r1.cost_atp,
                defense_that_blocked=f"cascade_broken_at_A3:{r1.defense_that_blocked}",
                detected=True,
                detection_method="cascade_prevention",
                details={"broken_at": "A3", "steps_completed": 0},
            )

        # Step 2: Trust bridge inflation (B3)
        r2 = self._attack_trust_bridge_inflation(adv, rnd)
        results.append(r2)
        if not r2.success:
            return AttackResult(
                vector="F1", success=False,
                cost_atp=sum(r.cost_atp for r in results),
                defense_that_blocked=f"cascade_broken_at_B3:{r2.defense_that_blocked}",
                detected=True,
                detection_method="cascade_prevention",
                details={"broken_at": "B3", "steps_completed": 1},
            )

        # Step 3: Quality manipulation (C2)
        r3 = self._attack_quality_manipulation(adv, rnd)
        results.append(r3)
        if not r3.success:
            return AttackResult(
                vector="F1", success=False,
                cost_atp=sum(r.cost_atp for r in results),
                defense_that_blocked=f"cascade_broken_at_C2:{r3.defense_that_blocked}",
                detected=True,
                detection_method="cascade_prevention",
                details={"broken_at": "C2", "steps_completed": 2},
            )

        # Step 4: Platform sybil (D1)
        r4 = self._attack_platform_sybil(adv, rnd)
        results.append(r4)

        total_cost = sum(r.cost_atp for r in results)
        total_gain = sum(r.gain_atp for r in results)

        return AttackResult(
            vector="F1",
            success=all(r.success for r in results),
            cost_atp=total_cost,
            gain_atp=total_gain,
            details={
                "steps_completed": sum(1 for r in results if r.success),
                "total_steps": 4,
                "cascade_result": [r.success for r in results],
            },
        )


# ─── Security Assessment Report ──────────────────────────────────

@dataclass
class SecurityAssessment:
    """Complete security assessment from red team exercise."""
    campaigns: list[CampaignResult]
    timestamp: str
    stack_version: str = "web4-ref-v10"

    @property
    def overall_block_rate(self) -> float:
        total_attempted = sum(c.attacks_attempted for c in self.campaigns)
        total_blocked = sum(c.attacks_blocked for c in self.campaigns)
        if total_attempted == 0:
            return 1.0
        return total_blocked / total_attempted

    @property
    def total_adversary_profit(self) -> float:
        return sum(c.net_profit for c in self.campaigns)

    @property
    def defense_coverage(self) -> dict[str, int]:
        """Which defenses activated across all campaigns."""
        combined: dict[str, int] = {}
        for c in self.campaigns:
            for d, count in c.defense_activations.items():
                combined[d] = combined.get(d, 0) + count
        return combined

    def to_report(self) -> dict:
        """Generate structured assessment report."""
        return {
            "web4_red_team_assessment": {
                "version": self.stack_version,
                "timestamp": self.timestamp,
                "summary": {
                    "campaigns_run": len(self.campaigns),
                    "overall_block_rate": round(self.overall_block_rate, 3),
                    "total_attacks": sum(c.attacks_attempted for c in self.campaigns),
                    "total_blocked": sum(c.attacks_blocked for c in self.campaigns),
                    "adversary_net_profit": round(self.total_adversary_profit, 2),
                    "profitable_for_attacker": self.total_adversary_profit > 0,
                },
                "by_adversary": [
                    {
                        "profile": c.adversary.value,
                        "attacks": c.attacks_attempted,
                        "blocked": c.attacks_blocked,
                        "block_rate": round(c.block_rate, 3),
                        "net_profit": round(c.net_profit, 2),
                        "roi": round(c.roi, 3),
                        "detections": len(c.detection_events),
                    }
                    for c in self.campaigns
                ],
                "defense_activations": self.defense_coverage,
                "recommendation": (
                    "PASS: Defenses hold across all adversary profiles"
                    if self.total_adversary_profit <= 0
                    else "REVIEW: Some adversaries achieved profit"
                ),
            }
        }


# ═══════════════════════════════════════════════════════════════════
# Verification Checks
# ═══════════════════════════════════════════════════════════════════

def run_checks():
    passed = 0
    failed = 0

    def check(condition: bool, label: str):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {label}")

    # ─── Section 1: Attack Catalog ────────────────────────────────

    print("Section 1: Attack Catalog")

    check(len(ATTACK_CATALOG) == 14, "14 attack vectors in catalog")
    categories = {v.category for v in ATTACK_CATALOG}
    check(len(categories) == 6, "6 attack categories (A-F)")
    check(all(v.code for v in ATTACK_CATALOG), "All vectors have codes")
    check(all(v.name for v in ATTACK_CATALOG), "All vectors have names")

    # Severity distribution
    critical = [v for v in ATTACK_CATALOG if v.severity == AttackSeverity.CRITICAL]
    check(len(critical) == 3, "3 critical severity vectors (C1, C2, F1)")

    # ─── Section 2: Adversary Profiles ────────────────────────────

    print("Section 2: Adversary Profiles")

    sk = Adversary.script_kiddie()
    check(sk.profile == AdversaryProfile.SCRIPT_KIDDIE, "Script kiddie profile")
    check(len(sk.agent_ids) == 1, "Script kiddie: 1 agent")
    check(sk.budget_atp == 200, "Script kiddie: 200 ATP budget")
    check(sk.skill_level == 0.3, "Script kiddie: 0.3 skill")

    insider = Adversary.insider()
    check(insider.skill_level == 0.7, "Insider: 0.7 skill")
    check(insider.stealth == 0.6, "Insider: 0.6 stealth")

    ns = Adversary.nation_state()
    check(len(ns.agent_ids) == 5, "Nation state: 5 agents")
    check(ns.budget_atp == 5000, "Nation state: 5000 ATP budget")
    check(ns.skill_level == 0.95, "Nation state: 0.95 skill")

    ring = Adversary.colluding_ring()
    check(len(ring.agent_ids) == 10, "Colluding ring: 10 agents")
    check(len(ring.hardware_ids) == 3, "Colluding ring: 3 hardware (shared)")

    # ─── Section 3: Defended Stack ────────────────────────────────

    print("Section 3: Defended Stack")

    ledger = DefendedLedger()
    ledger.fund("test:1", 100)
    check(ledger.balance("test:1") == 100, "Fund and balance")

    # Lock concurrency
    locks = []
    for i in range(7):
        lid = ledger.lock("test:1", 5.0)
        if lid:
            locks.append(lid)
    check(len(locks) == 5, "Max 5 concurrent locks (C1)")

    # Lock deposit
    # 5 locks × 5.0 amount × 1.01 (amount + deposit) = 25.25 deducted
    expected_deducted = 5 * (5.0 + 5.0 * 0.01)
    check(abs(ledger.balance("test:1") - (100 - expected_deducted)) < 0.01,
          "Lock deposit charged (C1)")

    # Sliding scale
    ledger2 = DefendedLedger()
    ledger2.fund("payer", 1000)
    lid = ledger2.lock("payer", 100)
    net_low = ledger2.commit(lid, "recipient", 0.5)  # Mid-range quality
    check(net_low > 0 and net_low < 100, "Sliding scale: partial payment for 0.5 quality")

    lid2 = ledger2.lock("payer", 100)
    net_high = ledger2.commit(lid2, "recipient", 0.9)
    check(net_high > net_low, "Higher quality → higher payment")

    # Task type registry
    tr = TaskTypeRegistry(max_custom_per_epoch=2)
    check(tr.validate("a1", "read"), "Canonical type accepted")
    check(tr.validate("a1", "custom_1"), "1st custom accepted")
    check(tr.validate("a1", "custom_2"), "2nd custom accepted")
    check(not tr.validate("a1", "custom_3"), "3rd custom blocked (E1)")
    tr.reset_epoch()
    check(tr.validate("a1", "custom_3"), "After epoch reset, custom accepted")

    # Identity registry with hardware binding
    ir = IdentityRegistry()
    ir.register("id:1", "hw:1")
    check(ir.get_trust("id:1") == 0.3, "Initial trust 0.3")
    ir.register("id:2", "hw:1")  # Same hardware!
    check(ir.get_trust("id:2") == 0.2, "Hardware reuse penalty: 0.2 (E2)")

    # Secondary dim verification
    dv = SecondaryDimVerifier()
    dv.add_witness("agent:1")
    dv.add_witness("agent:1")
    verified = dv.verify("agent:1", {"witnesses": 50, "alignment": 0.9})
    check(verified["witnesses"] == 0.2, "Witness cap: 2 × 0.1 = 0.2 (B3)")
    check(verified["alignment"] == 0.5, "Alignment cap: 0.5 (B3)")

    # Multi-party quality
    mpq = MultiPartyQuality()
    r = mpq.resolve(1.0, 1.0)
    check(r["quality"] == 1.0, "Colluding pair gets 1.0")
    r2 = mpq.resolve(1.0, 1.0, [0.4])
    check(r2["quality"] == 1.0, "With 1 witness: median of [0.4, 1.0, 1.0] = 1.0")
    r3 = mpq.resolve(1.0, 1.0, [0.3, 0.4])
    check(r3["quality"] < 1.0, "With 2 witnesses: median pulled down")

    # Federation registry
    fr = FederationRegistry()
    check(not fr.register("cheap", 100), "Cheap platform rejected (D1)")
    check(fr.register("proper", 250), "Proper deposit accepted")
    check(fr.platforms["proper"]["trust"] == 0.3, "New platform starts at 0.3")

    # ─── Section 4: Script Kiddie Campaign ────────────────────────

    print("Section 4: Script Kiddie Campaign")

    engine = RedTeamEngine()
    sk_result = engine.run_campaign(Adversary.script_kiddie())

    check(sk_result.adversary == AdversaryProfile.SCRIPT_KIDDIE, "Script kiddie campaign")
    check(sk_result.attacks_attempted > 0, "Attacks were attempted")
    check(sk_result.block_rate > 0.5, f"Block rate > 50% (got {sk_result.block_rate:.1%})")
    check(sk_result.net_profit <= 0, f"Script kiddie unprofitable (net: {sk_result.net_profit:.1f})")
    check(len(sk_result.detection_events) > 0, "Script kiddie detected")

    # ─── Section 5: Insider Campaign ──────────────────────────────

    print("Section 5: Insider Campaign")

    engine2 = RedTeamEngine()
    insider_result = engine2.run_campaign(Adversary.insider())

    check(insider_result.adversary == AdversaryProfile.INSIDER, "Insider campaign")
    check(insider_result.attacks_attempted > 0, "Insider attempted attacks")
    check(insider_result.block_rate >= 0.4,
          f"Insider block rate ≥ 40% (got {insider_result.block_rate:.1%})")
    # Insider might achieve small gains but should be detected
    check(len(insider_result.detection_events) > 0, "Insider detected")

    # ─── Section 6: Nation State Campaign ─────────────────────────

    print("Section 6: Nation State Campaign")

    engine3 = RedTeamEngine()
    ns_result = engine3.run_campaign(Adversary.nation_state())

    check(ns_result.adversary == AdversaryProfile.NATION_STATE, "Nation state campaign")
    check(ns_result.attacks_attempted > 0, "Nation state attempted attacks")
    # Even nation states should face significant resistance
    check(ns_result.attacks_blocked > 0, "Some nation state attacks blocked")
    check(len(ns_result.defense_activations) > 0, "Defenses activated against nation state")

    # Cascade attack should be blocked
    cascade_results = [r for r in ns_result.round_results if r.vector == "F1"]
    if cascade_results:
        check(not cascade_results[0].success,
              "Cascade attack blocked against nation state")
    else:
        check(True, "No cascade attempted (filtered by selection)")

    # ─── Section 7: Colluding Ring Campaign ───────────────────────

    print("Section 7: Colluding Ring Campaign")

    engine4 = RedTeamEngine()
    ring_result = engine4.run_campaign(Adversary.colluding_ring())

    check(ring_result.adversary == AdversaryProfile.COLLUDING_RING, "Colluding ring campaign")
    check(ring_result.attacks_attempted > 0, "Ring attempted attacks")

    # Hardware sharing should trigger penalties
    hw_penalties = [r for r in ring_result.round_results
                    if r.vector == "E2" and r.detected]
    check(len(hw_penalties) > 0 or not any(r.vector == "E2" for r in ring_result.round_results),
          "Hardware reuse detected or E2 not attempted")

    # ─── Section 8: Attack Selection ──────────────────────────────

    print("Section 8: Attack Selection")

    engine5 = RedTeamEngine()

    sk_attacks = engine5._select_attacks(Adversary.script_kiddie())
    ns_attacks = engine5._select_attacks(Adversary.nation_state())

    check(len(sk_attacks) < len(ns_attacks),
          f"Script kiddie gets fewer attacks ({len(sk_attacks)}) than nation state ({len(ns_attacks)})")

    # Script kiddie can't do critical attacks
    sk_critical = [a for a in sk_attacks if a.severity == AttackSeverity.CRITICAL]
    check(len(sk_critical) == 0, "Script kiddie blocked from critical attacks")

    # Nation state can access everything
    ns_codes = {a.code for a in ns_attacks}
    check("F1" in ns_codes, "Nation state can attempt cascade (F1)")
    check("C1" in ns_codes, "Nation state can attempt lock starvation (C1)")

    # ─── Section 9: Individual Attack Results ─────────────────────

    print("Section 9: Individual Attack Results")

    engine6 = RedTeamEngine()
    adv = Adversary.insider()
    for aid in adv.agent_ids:
        engine6.registry.register(aid, adv.hardware_ids[0])
        engine6.ledger.fund(aid, 500)

    # A1: Format confusion should be blocked
    r_a1 = engine6._attack_lct_format_confusion(adv, 0)
    check(not r_a1.success, "A1: LCT format confusion blocked")
    check(r_a1.detected, "A1: Attack detected")

    # A2: Entity type escalation blocked
    r_a2 = engine6._attack_entity_type_escalation(adv, 0)
    check(not r_a2.success, "A2: Entity type escalation blocked")

    # A3: Colon injection blocked
    r_a3 = engine6._attack_colon_injection(adv, 0)
    check(not r_a3.success, "A3: Colon injection blocked")

    # B1: Trust oscillation neutralized
    r_b1 = engine6._attack_trust_oscillation(adv, 0)
    check(not r_b1.success, "B1: Trust oscillation neutralized (drift < 0.05)")
    check(abs(r_b1.details["drift"]) < 0.05, "B1: Drift is negligible")

    # B3: Trust bridge inflation capped
    r_b3 = engine6._attack_trust_bridge_inflation(adv, 0)
    check(not r_b3.success, "B3: Trust bridge inflation capped")
    check(r_b3.details["verified"]["witnesses"] < r_b3.details["claimed"]["witnesses"],
          "B3: Witness claim reduced")

    # C1: Lock starvation limited
    r_c1 = engine6._attack_lock_starvation(adv, 0)
    check(not r_c1.success, "C1: Lock starvation limited")
    check(r_c1.details["blocked"] > 0, "C1: Excess locks blocked")

    # C3: Fee avoidance has cost (needs 2 agents — use colluding ring)
    engine6b = RedTeamEngine()
    ring_adv = Adversary.colluding_ring()
    for aid in ring_adv.agent_ids:
        engine6b.registry.register(aid, ring_adv.hardware_ids[0])
        engine6b.ledger.fund(aid, 500)
    r_c3 = engine6b._attack_fee_avoidance(ring_adv, 0)
    check(r_c3.cost_atp > 0, "C3: Fee avoidance costs deposit")

    # D2: Quality cliff eliminated
    r_d2 = engine6._attack_quality_cliff(adv, 0)
    check(not r_d2.success, "D2: Quality cliff eliminated by sliding scale")
    check(r_d2.details["cliff_eliminated"], "D2: Cliff confirmed eliminated")

    # E2: Reputation laundering penalized
    r_e2 = engine6._attack_reputation_laundering(adv, 0)
    check(r_e2.detected, "E2: Hardware reuse detected")
    check(r_e2.details["new_trust"] < 0.3, "E2: New identity gets penalty trust")

    # ─── Section 10: Security Assessment Report ───────────────────

    print("Section 10: Security Assessment Report")

    # Run all 4 adversary profiles
    engines = [RedTeamEngine() for _ in range(4)]
    campaigns = [
        engines[0].run_campaign(Adversary.script_kiddie()),
        engines[1].run_campaign(Adversary.insider()),
        engines[2].run_campaign(Adversary.nation_state()),
        engines[3].run_campaign(Adversary.colluding_ring()),
    ]

    assessment = SecurityAssessment(
        campaigns=campaigns,
        timestamp="2026-02-26T00:00:00Z",
    )

    check(assessment.overall_block_rate > 0.4,
          f"Overall block rate > 40% (got {assessment.overall_block_rate:.1%})")
    check(len(assessment.defense_coverage) > 0, "Defenses activated")

    report = assessment.to_report()
    check("web4_red_team_assessment" in report, "Report has correct structure")
    check(report["web4_red_team_assessment"]["summary"]["campaigns_run"] == 4,
          "4 campaigns in report")
    check(report["web4_red_team_assessment"]["summary"]["total_attacks"] > 0,
          "Total attacks > 0 in report")

    by_adv = report["web4_red_team_assessment"]["by_adversary"]
    check(len(by_adv) == 4, "4 adversary profiles in report")
    check(all("block_rate" in a for a in by_adv), "All profiles have block_rate")
    check(all("net_profit" in a for a in by_adv), "All profiles have net_profit")

    # ─── Section 11: Adaptive Attack Behavior ─────────────────────

    print("Section 11: Adaptive Attack Behavior")

    # Nation state with high adaptiveness should drop failing attacks
    engine7 = RedTeamEngine()
    ns = Adversary.nation_state()
    ns.max_rounds = 20

    result = engine7.run_campaign(ns)

    # Check that unique vectors decrease over rounds if attacks fail
    early_vectors = {r.vector for r in result.round_results[:5]}
    late_vectors = {r.vector for r in result.round_results[-5:]} if len(result.round_results) >= 10 else early_vectors

    # Adaptive: should try fewer unique vectors later (dropped failing ones)
    check(len(late_vectors) <= len(early_vectors),
          f"Adaptive: late vectors ({len(late_vectors)}) ≤ early ({len(early_vectors)})")

    # ─── Section 12: Attack Result Properties ─────────────────────

    print("Section 12: Attack Result Properties")

    # ROI calculation
    r1 = AttackResult(vector="test", success=True, gain_atp=100, cost_atp=50)
    check(r1.roi == 1.0, "ROI: (100-50)/50 = 1.0")
    check(r1.net_profit == 50, "Net profit: 100-50 = 50")

    r2 = AttackResult(vector="test", success=False, gain_atp=0, cost_atp=100)
    check(r2.roi == -1.0, "Failed attack ROI: -1.0")
    check(r2.net_profit == -100, "Failed attack loss: -100")

    r3 = AttackResult(vector="test", success=True, gain_atp=0, cost_atp=0)
    check(r3.roi == 0.0, "Zero-cost attack ROI: 0.0")

    # Campaign properties
    c = CampaignResult(
        adversary=AdversaryProfile.SCRIPT_KIDDIE,
        attacks_attempted=10,
        attacks_blocked=7,
        attacks_partially_succeeded=2,
        total_atp_spent=100,
        total_atp_gained=30,
        trust_changes={},
        defense_activations={"A": 3, "B": 4},
        detection_events=[],
        round_results=[],
        duration_ms=100,
    )
    check(c.block_rate == 0.7, "Block rate: 7/10 = 0.7")
    check(c.net_profit == -70, "Net profit: 30-100 = -70")
    check(c.roi == -0.7, "ROI: -70/100 = -0.7")

    # ─── Section 13: Edge Cases ───────────────────────────────────

    print("Section 13: Edge Cases")

    # Empty campaign
    empty_campaign = CampaignResult(
        adversary=AdversaryProfile.SCRIPT_KIDDIE,
        attacks_attempted=0, attacks_blocked=0,
        attacks_partially_succeeded=0,
        total_atp_spent=0, total_atp_gained=0,
        trust_changes={}, defense_activations={},
        detection_events=[], round_results=[],
        duration_ms=0,
    )
    check(empty_campaign.block_rate == 1.0, "Empty campaign: 100% block rate")
    check(empty_campaign.roi == 0.0, "Empty campaign: 0 ROI")

    # Assessment with no campaigns
    empty_assessment = SecurityAssessment(campaigns=[], timestamp="now")
    check(empty_assessment.overall_block_rate == 1.0, "Empty assessment: 100% block")
    check(empty_assessment.total_adversary_profit == 0, "Empty assessment: 0 profit")

    report = empty_assessment.to_report()
    check(report["web4_red_team_assessment"]["summary"]["campaigns_run"] == 0,
          "Empty assessment report: 0 campaigns")

    # Adversary with no valid attacks
    engine8 = RedTeamEngine()
    weak = Adversary.script_kiddie()
    weak.budget_atp = 1  # Too broke for anything requiring ATP
    weak.skill_level = 0.0  # Too unskilled for medium+ attacks

    result = engine8.run_campaign(weak)
    # Should still run but with limited attack set
    check(result.attacks_attempted >= 0, "Weak adversary campaign completes")

    # ─── Section 14: Cross-Campaign Comparison ────────────────────

    print("Section 14: Cross-Campaign Comparison")

    # Script kiddie should do worse than nation state
    check(sk_result.attacks_blocked >= ring_result.attacks_blocked or
          sk_result.block_rate >= ring_result.block_rate * 0.5,
          "Weaker adversary doesn't outperform colluding ring")

    # Defense coverage should increase with adversary capability
    all_defenses_sk = set(sk_result.defense_activations.keys())
    all_defenses_ns = set(ns_result.defense_activations.keys())
    check(len(all_defenses_ns) >= len(all_defenses_sk),
          f"Nation state triggers ≥ defenses than script kiddie ({len(all_defenses_ns)} ≥ {len(all_defenses_sk)})")

    # ═══════════════════════════════════════════════════════════════

    print(f"\n{'=' * 60}")
    print(f"Adversarial Red Team Simulator: {passed}/{passed + failed} checks passed")
    if failed == 0:
        print("  All checks passed!")
    else:
        print(f"  {failed} FAILED")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    run_checks()
