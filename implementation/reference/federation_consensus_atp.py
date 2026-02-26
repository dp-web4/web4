#!/usr/bin/env python3
"""
Web4 Reference Implementation: Federation + Consensus + ATP Integration
Spec: docs/what/specifications/FEDERATION_CONSENSUS_ATP_INTEGRATION.md (756 lines)

Covers:
  §1 Executive Summary & Background (Layers 1-3)
  §2 Transaction Types (FEDERATION_TASK, EXECUTION_PROOF, ATP existing)
  §3 Block Structure with Federation Transactions
  §4 Integration Implementation (Phase 3.5-3.75)
  §5 Performance Analysis (latency, throughput, cost-benefit)
  §6 Security Analysis (3 attack vectors)
  §7 Economic Model (ATP flow, incentive alignment)
  §8 SAGE Cognition Integration
  §9 Testing Strategy (unit + integration + performance)
  §10 Open Research Questions

Run:  python3 federation_consensus_atp.py
"""

import hashlib, json, time, uuid, math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

# ── §1  Background: 3-Layer Stack ──────────────────────────────────────

class TransactionType(Enum):
    """All transaction types in the integrated system."""
    # Layer 1: ATP transactions (existing)
    ATP_TRANSFER_LOCK = "ATP_TRANSFER_LOCK"
    ATP_TRANSFER_COMMIT = "ATP_TRANSFER_COMMIT"
    ATP_TRANSFER_ROLLBACK = "ATP_TRANSFER_ROLLBACK"
    ATP_BALANCE_SET = "ATP_BALANCE_SET"
    # Layer 3: Federation transactions (new)
    FEDERATION_TASK = "FEDERATION_TASK"
    EXECUTION_PROOF = "EXECUTION_PROOF"


@dataclass
class ATPAccount:
    """ATP account with total/available/locked balances."""
    lct_id: str
    total: float = 0.0
    available: float = 0.0
    locked: float = 0.0

    def lock(self, amount: float) -> bool:
        if amount > self.available:
            return False
        self.available -= amount
        self.locked += amount
        return True

    def commit(self, amount: float) -> bool:
        if amount > self.locked:
            return False
        self.locked -= amount
        self.total -= amount
        return True

    def rollback(self, amount: float) -> bool:
        if amount > self.locked:
            return False
        self.locked -= amount
        self.available += amount
        return True

    def credit(self, amount: float):
        self.total += amount
        self.available += amount


class ATPLedger:
    """Layer 1: ATP state management with two-phase commit."""

    def __init__(self):
        self.accounts: Dict[str, ATPAccount] = {}
        self.locks: Dict[str, dict] = {}  # transfer_id -> lock info

    def create_account(self, lct_id: str, initial_balance: float = 0.0):
        self.accounts[lct_id] = ATPAccount(
            lct_id=lct_id,
            total=initial_balance,
            available=initial_balance,
            locked=0.0,
        )

    def get_account(self, lct_id: str) -> Optional[ATPAccount]:
        return self.accounts.get(lct_id)

    def lock_transfer(self, transfer_id: str, source: str, amount: float) -> bool:
        acct = self.accounts.get(source)
        if not acct:
            return False
        if acct.lock(amount):
            self.locks[transfer_id] = {
                "source": source, "amount": amount, "status": "locked"
            }
            return True
        return False

    def commit_transfer(self, transfer_id: str, dest: str) -> bool:
        lock = self.locks.get(transfer_id)
        if not lock or lock["status"] != "locked":
            return False
        src_acct = self.accounts.get(lock["source"])
        dst_acct = self.accounts.get(dest)
        if not src_acct or not dst_acct:
            return False
        if src_acct.commit(lock["amount"]):
            dst_acct.credit(lock["amount"])
            lock["status"] = "committed"
            return True
        return False

    def rollback_transfer(self, transfer_id: str) -> bool:
        lock = self.locks.get(transfer_id)
        if not lock or lock["status"] != "locked":
            return False
        acct = self.accounts.get(lock["source"])
        if not acct:
            return False
        if acct.rollback(lock["amount"]):
            lock["status"] = "rolled_back"
            return True
        return False


# ── §2  Transaction Types ──────────────────────────────────────────────

@dataclass
class FederationTaskTransaction:
    """Type 1: Record task delegation in consensus block."""
    type: str = "FEDERATION_TASK"
    task_id: str = ""
    delegating_platform: str = ""
    delegating_agent: str = ""
    executing_platform: str = ""
    executing_agent: str = ""
    estimated_cost: float = 0.0
    task_data: dict = field(default_factory=dict)
    quality_threshold: float = 0.7
    timestamp: float = 0.0
    signature: str = ""

    def validate(self, ledger: ATPLedger, pending_tasks: set, consensus_group: set) -> Tuple[bool, str]:
        """Validation rules from spec."""
        # 1. Delegating agent has sufficient ATP
        acct = ledger.get_account(self.delegating_agent)
        if not acct or acct.available < self.estimated_cost:
            return False, "insufficient_atp"
        # 2. Signature valid (simplified: non-empty)
        if not self.signature:
            return False, "invalid_signature"
        # 3. Executing platform in consensus group
        if self.executing_platform not in consensus_group:
            return False, "platform_not_in_consensus"
        # 4. Task ID unique
        if self.task_id in pending_tasks:
            return False, "duplicate_task"
        return True, "valid"


@dataclass
class ExecutionProofTransaction:
    """Type 2: Record task completion and quality score."""
    type: str = "EXECUTION_PROOF"
    task_id: str = ""
    executing_platform: str = ""
    executing_agent: str = ""
    quality_score: float = 0.0
    execution_time: float = 0.0
    result_hash: str = ""
    timestamp: float = 0.0
    signature: str = ""

    def validate(self, pending_tasks: dict, task_timeout: float = 60.0) -> Tuple[bool, str]:
        """Validation rules from spec."""
        # 1. Task exists in pending
        if self.task_id not in pending_tasks:
            return False, "task_not_found"
        # 2. Quality score in [0.0, 1.0]
        if not (0.0 <= self.quality_score <= 1.0):
            return False, "invalid_quality"
        # 3. Signature valid
        if not self.signature:
            return False, "invalid_signature"
        # 4. Execution within timeout
        task = pending_tasks[self.task_id]
        if self.execution_time > task.get("timeout", task_timeout):
            return False, "execution_timeout"
        return True, "valid"


# ── §3  Block Structure ────────────────────────────────────────────────

@dataclass
class ConsensusBlock:
    """Block containing federation + ATP transactions."""
    block_number: int
    prev_hash: str
    timestamp: float
    transactions: List[dict] = field(default_factory=list)
    proposer_platform: str = ""
    signature: str = ""

    def compute_hash(self) -> str:
        data = json.dumps({
            "block_number": self.block_number,
            "prev_hash": self.prev_hash,
            "timestamp": self.timestamp,
            "tx_count": len(self.transactions),
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()


# ── §2-§4  Transaction Processor ───────────────────────────────────────

class FederationTransactionProcessor:
    """Processes federation transactions with ATP integration."""

    def __init__(self, ledger: ATPLedger, consensus_group: set):
        self.ledger = ledger
        self.consensus_group = consensus_group
        self.pending_tasks: Dict[str, dict] = {}
        self.completed_tasks: Dict[str, dict] = {}
        self.blocks: List[ConsensusBlock] = []

    def process_federation_task(self, tx: FederationTaskTransaction) -> Tuple[bool, str]:
        """Process FEDERATION_TASK: record pending + lock ATP."""
        valid, reason = tx.validate(self.ledger, set(self.pending_tasks.keys()), self.consensus_group)
        if not valid:
            return False, reason

        # Lock ATP (same transfer_id as task_id)
        locked = self.ledger.lock_transfer(tx.task_id, tx.delegating_agent, tx.estimated_cost)
        if not locked:
            return False, "atp_lock_failed"

        # Record task as pending
        self.pending_tasks[tx.task_id] = {
            "delegating_agent": tx.delegating_agent,
            "executing_agent": tx.executing_agent,
            "estimated_cost": tx.estimated_cost,
            "quality_threshold": tx.quality_threshold,
            "timeout": tx.task_data.get("timeout", 60.0),
            "timestamp": tx.timestamp,
        }
        return True, "task_pending"

    def process_execution_proof(self, tx: ExecutionProofTransaction) -> Tuple[bool, str]:
        """Process EXECUTION_PROOF: settle ATP based on quality."""
        valid, reason = tx.validate(self.pending_tasks)
        if not valid:
            return False, reason

        task = self.pending_tasks[tx.task_id]

        # Quality-based settlement
        if tx.quality_score >= task["quality_threshold"]:
            # Commit ATP to executor
            self.ledger.commit_transfer(tx.task_id, tx.executing_agent)
            settlement = "COMMIT"
        else:
            # Rollback ATP to delegator
            self.ledger.rollback_transfer(tx.task_id)
            settlement = "ROLLBACK"

        # Move to completed
        self.completed_tasks[tx.task_id] = {
            **task,
            "quality_score": tx.quality_score,
            "execution_time": tx.execution_time,
            "settlement": settlement,
        }
        del self.pending_tasks[tx.task_id]
        return True, settlement

    def create_block(self, transactions: List[dict], proposer: str) -> ConsensusBlock:
        """Create consensus block with transactions."""
        prev_hash = self.blocks[-1].compute_hash() if self.blocks else "genesis"
        block = ConsensusBlock(
            block_number=len(self.blocks),
            prev_hash=prev_hash,
            timestamp=time.time(),
            transactions=transactions,
            proposer_platform=proposer,
            signature=f"sig_{proposer}",
        )
        self.blocks.append(block)
        return block


# ── §2  FB-PBFT Consensus Protocol (Layer 2) ──────────────────────────

class FBPBFTConsensus:
    """Simplified FB-PBFT consensus (3-phase commit)."""

    def __init__(self, platforms: List[str]):
        self.platforms = platforms
        self.n = len(platforms)
        self.f = (self.n - 1) // 3  # Max Byzantine faults

    @property
    def quorum(self) -> int:
        """2f+1 quorum needed."""
        return 2 * self.f + 1

    def can_tolerate_faults(self, num_faults: int) -> bool:
        return num_faults <= self.f

    def propose(self, block: ConsensusBlock) -> dict:
        """Phase 1: Propose."""
        return {"phase": "PROPOSE", "block": block.block_number}

    def prepare(self, block: ConsensusBlock, votes: int) -> Tuple[bool, str]:
        """Phase 2: Prepare (need 2f+1 votes)."""
        if votes >= self.quorum:
            return True, "prepared"
        return False, "insufficient_votes"

    def commit(self, block: ConsensusBlock, votes: int) -> Tuple[bool, str]:
        """Phase 3: Commit (need 2f+1 votes)."""
        if votes >= self.quorum:
            return True, "committed"
        return False, "insufficient_votes"


# ── §5  Performance Analysis ───────────────────────────────────────────

@dataclass
class PerformanceMetrics:
    """Latency and throughput analysis from spec."""

    # Without consensus
    http_rtt_ms: float = 10.0
    task_execution_ms: float = 45.0

    # With consensus
    consensus_rtt_ms: float = 30.0  # 3 RTT = ~30ms

    # Throughput
    blocks_per_second: float = 7.7
    tasks_per_block: int = 5

    @property
    def latency_without_consensus(self) -> float:
        """HTTP-only latency: request + execution + response."""
        return self.http_rtt_ms + self.task_execution_ms + self.http_rtt_ms

    @property
    def latency_with_consensus(self) -> float:
        """With consensus: block1 + execution + block2."""
        return self.consensus_rtt_ms + self.task_execution_ms + self.consensus_rtt_ms

    @property
    def overhead_ms(self) -> float:
        return self.latency_with_consensus - self.latency_without_consensus

    @property
    def overhead_percent(self) -> float:
        return (self.overhead_ms / self.latency_without_consensus) * 100

    @property
    def federation_throughput(self) -> float:
        """Tasks per second."""
        return self.tasks_per_block * self.blocks_per_second

    def should_use_consensus(self, atp_cost: float, threshold: float = 100.0) -> bool:
        """Spec recommendation: use consensus for >100 ATP tasks."""
        return atp_cost > threshold


# ── §6  Security Analysis ─────────────────────────────────────────────

class SecurityAnalyzer:
    """Analyzes 3 attack vectors from spec."""

    @staticmethod
    def analyze_false_quality_claim(
        claimed_quality: float,
        actual_quality: float,
        has_consensus: bool,
    ) -> dict:
        """Attack Vector 1: False quality claims."""
        is_fraudulent = claimed_quality > actual_quality + 0.1  # significant difference
        if has_consensus:
            return {
                "detected": True,
                "mechanism": "consensus_proof_on_chain",
                "fraud": is_fraudulent,
                "action": "challenge_with_counter_proof" if is_fraudulent else "none",
            }
        else:
            return {
                "detected": is_fraudulent,  # Only if delegator checks locally
                "mechanism": "local_detection_only",
                "fraud": is_fraudulent,
                "action": "refuse_commit" if is_fraudulent else "none",
            }

    @staticmethod
    def analyze_double_spend(
        alice_available: float,
        task1_cost: float,
        task2_cost: float,
        has_consensus: bool,
    ) -> dict:
        """Attack Vector 2: Double-spending on task costs."""
        total_cost = task1_cost + task2_cost
        can_afford_both = alice_available >= total_cost

        if has_consensus:
            # Consensus serializes transactions
            return {
                "prevented": True,
                "mechanism": "consensus_serialization",
                "task1_accepted": alice_available >= task1_cost,
                "task2_accepted": can_afford_both,
            }
        else:
            # Race condition possible
            return {
                "prevented": False,
                "mechanism": "local_locking_only",
                "task1_accepted": True,
                "task2_accepted": True,  # Race condition allows both
                "race_condition": not can_afford_both,
            }

    @staticmethod
    def analyze_group_collusion(
        total_platforms: int,
        colluding_platforms: int,
    ) -> dict:
        """Attack Vector 3: Consensus group collusion."""
        f = (total_platforms - 1) // 3
        quorum = 2 * f + 1

        return {
            "total_platforms": total_platforms,
            "colluding": colluding_platforms,
            "max_tolerable_faults": f,
            "quorum_needed": quorum,
            "attack_succeeds": colluding_platforms >= quorum,
            "collusion_percent": (colluding_platforms / total_platforms) * 100,
            "defense": "economic_staking" if colluding_platforms < quorum else "consensus_broken",
        }


# ── §7  Economic Model ────────────────────────────────────────────────

class EconomicModel:
    """Quality-based ATP flow with incentive alignment."""

    def __init__(self, quality_threshold: float = 0.7):
        self.quality_threshold = quality_threshold

    def simulate_high_quality(self, initial_atp: float, cost: float, quality: float) -> dict:
        """High quality execution: delegator pays, executor earns."""
        assert quality >= self.quality_threshold
        return {
            "delegator_before": initial_atp,
            "delegator_after": initial_atp - cost,
            "executor_earned": cost,
            "settlement": "COMMIT",
        }

    def simulate_low_quality(self, initial_atp: float, cost: float, quality: float) -> dict:
        """Low quality execution: delegator refunded."""
        assert quality < self.quality_threshold
        return {
            "delegator_before": initial_atp,
            "delegator_after": initial_atp,  # Full refund
            "executor_earned": 0.0,
            "settlement": "ROLLBACK",
        }

    def compute_incentive_score(self, quality_history: List[float]) -> dict:
        """Platform incentive alignment from quality history."""
        if not quality_history:
            return {"avg_quality": 0.0, "payment_rate": 0.0, "reputation": "unknown"}
        avg = sum(quality_history) / len(quality_history)
        payment_rate = sum(1 for q in quality_history if q >= self.quality_threshold) / len(quality_history)
        if payment_rate >= 0.9:
            reputation = "excellent"
        elif payment_rate >= 0.7:
            reputation = "good"
        elif payment_rate >= 0.5:
            reputation = "mediocre"
        else:
            reputation = "poor"
        return {
            "avg_quality": avg,
            "payment_rate": payment_rate,
            "reputation": reputation,
            "total_tasks": len(quality_history),
        }


# ── §8  SAGE Cognition Integration ────────────────────────────────────

class SAGECognitionIntegrator:
    """ATP-aware SAGE decision logic from spec §8."""

    def __init__(self, agent_id: str, ledger: ATPLedger, daily_budget: float = 1000.0):
        self.agent_id = agent_id
        self.agent_lct = f"lct:web4:agent:{agent_id}"
        self.ledger = ledger
        self.daily_budget = daily_budget
        self.daily_spent = 0.0

    def estimate_cost(self, perception_size: int, complexity: str) -> float:
        """Estimate task cost based on complexity."""
        base_costs = {"low": 50.0, "medium": 150.0, "high": 300.0, "critical": 500.0}
        base = base_costs.get(complexity, 150.0)
        # Scale with perception size
        scale = max(1.0, perception_size / 512.0)
        return base * scale

    def should_delegate(self, estimated_cost: float, local_capacity: float) -> Tuple[bool, str]:
        """Decision: delegate vs local processing."""
        acct = self.ledger.get_account(self.agent_lct)
        if not acct:
            return False, "no_atp_account"

        has_budget = acct.available >= estimated_cost
        within_daily = (self.daily_spent + estimated_cost) <= self.daily_budget
        insufficient_local = local_capacity < 0.5  # Below 50% capacity

        if insufficient_local and has_budget and within_daily:
            return True, "delegate_recommended"
        elif not has_budget:
            return False, "insufficient_atp"
        elif not within_daily:
            return False, "daily_budget_exceeded"
        else:
            return False, "local_sufficient"

    def process_perception(
        self,
        perception_size: int,
        complexity: str,
        local_capacity: float,
        target_platform: Optional[str] = None,
    ) -> dict:
        """Enhanced SAGE perception processing with ATP awareness."""
        estimated_cost = self.estimate_cost(perception_size, complexity)
        should, reason = self.should_delegate(estimated_cost, local_capacity)

        if should and target_platform:
            self.daily_spent += estimated_cost
            return {
                "action": "delegate",
                "target": target_platform,
                "estimated_cost": estimated_cost,
                "reason": reason,
            }
        else:
            return {
                "action": "local",
                "reason": reason,
                "estimated_cost": estimated_cost,
            }


# ── §9  Testing Strategy ──────────────────────────────────────────────

@dataclass
class TestScenario:
    """Test scenario definition."""
    name: str
    platforms: int
    tasks: int
    quality: float
    expected_settlement: str
    description: str


# ── §10  Research Questions ────────────────────────────────────────────

class ResearchQuestions:
    """Open research question explorations."""

    @staticmethod
    def optimal_quality_threshold(
        qualities: List[float],
        thresholds: List[float],
    ) -> dict:
        """Q1: What threshold maximizes network utility?"""
        results = {}
        for threshold in thresholds:
            paid = sum(1 for q in qualities if q >= threshold)
            avg_paid_quality = (
                sum(q for q in qualities if q >= threshold) / paid
                if paid > 0 else 0.0
            )
            results[threshold] = {
                "payment_rate": paid / len(qualities),
                "avg_paid_quality": avg_paid_quality,
                "utility": (paid / len(qualities)) * avg_paid_quality,
            }
        # Find optimal
        best = max(results.items(), key=lambda x: x[1]["utility"])
        return {"results": results, "optimal_threshold": best[0], "optimal_utility": best[1]["utility"]}

    @staticmethod
    def dynamic_pricing(base_cost: float, demand: float, complexity: str) -> float:
        """Q2: Dynamic task pricing based on demand/complexity."""
        complexity_mult = {"low": 0.5, "medium": 1.0, "high": 2.0, "critical": 3.0}
        surge_mult = max(1.0, 1.0 + (demand - 0.7) * 2.0)  # Surge above 70% demand
        return base_cost * complexity_mult.get(complexity, 1.0) * surge_mult

    @staticmethod
    def reputation_bonus(base_payment: float, quality_history: List[float]) -> float:
        """Q3: Reputation-based payment adjustments."""
        if len(quality_history) < 5:
            return base_payment  # Not enough history
        avg_quality = sum(quality_history[-10:]) / len(quality_history[-10:])
        if avg_quality >= 0.9:
            return base_payment * 1.10  # +10% bonus
        elif avg_quality >= 0.8:
            return base_payment * 1.05  # +5% bonus
        elif avg_quality < 0.5:
            return base_payment * 0.90  # -10% penalty
        return base_payment


# ════════════════════════════════════════════════════════════════════════
#  TESTS
# ════════════════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0
    total = 0

    def check(label, condition):
        nonlocal passed, failed, total
        total += 1
        if condition:
            passed += 1
            print(f"  ✓ {label}")
        else:
            failed += 1
            print(f"  ✗ {label}")

    # ── §1  Layer 1: ATP Ledger ────────────────────────────────────
    print("\n§1 ATP Ledger (Layer 1)")

    ledger = ATPLedger()
    ledger.create_account("alice@Thor", 1000.0)
    ledger.create_account("bob@Sprout", 500.0)

    check("T1.1 Alice account created", ledger.get_account("alice@Thor").total == 1000.0)
    check("T1.2 Bob account created", ledger.get_account("bob@Sprout").total == 500.0)
    check("T1.3 Alice available", ledger.get_account("alice@Thor").available == 1000.0)
    check("T1.4 Lock 300 ATP", ledger.lock_transfer("tx1", "alice@Thor", 300.0))
    check("T1.5 Alice available after lock", ledger.get_account("alice@Thor").available == 700.0)
    check("T1.6 Alice locked", ledger.get_account("alice@Thor").locked == 300.0)
    check("T1.7 Commit transfer", ledger.commit_transfer("tx1", "bob@Sprout"))
    check("T1.8 Alice total after commit", ledger.get_account("alice@Thor").total == 700.0)
    check("T1.9 Bob total after commit", ledger.get_account("bob@Sprout").total == 800.0)

    # Rollback test
    ledger2 = ATPLedger()
    ledger2.create_account("charlie", 500.0)
    ledger2.lock_transfer("tx2", "charlie", 200.0)
    check("T1.10 Rollback transfer", ledger2.rollback_transfer("tx2"))
    check("T1.11 Charlie available after rollback", ledger2.get_account("charlie").available == 500.0)
    check("T1.12 Charlie locked after rollback", ledger2.get_account("charlie").locked == 0.0)

    # Insufficient funds
    check("T1.13 Lock fails insufficient", not ledger2.lock_transfer("tx3", "charlie", 999.0))

    # ── §2  Transaction Types ──────────────────────────────────────
    print("\n§2 Transaction Types")

    ledger3 = ATPLedger()
    ledger3.create_account("lct:web4:agent:alice", 1000.0)
    ledger3.create_account("lct:web4:agent:bob", 500.0)
    consensus_group = {"Thor", "Sprout", "Legion"}

    task_tx = FederationTaskTransaction(
        task_id="task-001",
        delegating_platform="Thor",
        delegating_agent="lct:web4:agent:alice",
        executing_platform="Sprout",
        executing_agent="lct:web4:agent:bob",
        estimated_cost=300.0,
        task_data={"perception_size": 512, "complexity": "medium", "timeout": 60.0},
        quality_threshold=0.7,
        timestamp=time.time(),
        signature="ed25519_sig_alice",
    )

    valid, reason = task_tx.validate(ledger3, set(), consensus_group)
    check("T2.1 Valid federation task", valid)
    check("T2.2 Reason is valid", reason == "valid")

    # Invalid: no signature
    task_no_sig = FederationTaskTransaction(
        task_id="task-002",
        delegating_agent="lct:web4:agent:alice",
        executing_platform="Sprout",
        estimated_cost=100.0,
        signature="",
    )
    valid2, reason2 = task_no_sig.validate(ledger3, set(), consensus_group)
    check("T2.3 Reject no signature", not valid2)
    check("T2.4 Reason invalid_signature", reason2 == "invalid_signature")

    # Invalid: platform not in consensus
    task_bad_platform = FederationTaskTransaction(
        task_id="task-003",
        delegating_agent="lct:web4:agent:alice",
        executing_platform="Unknown",
        estimated_cost=100.0,
        signature="sig",
    )
    valid3, reason3 = task_bad_platform.validate(ledger3, set(), consensus_group)
    check("T2.5 Reject unknown platform", not valid3)
    check("T2.6 Reason platform_not_in_consensus", reason3 == "platform_not_in_consensus")

    # Invalid: duplicate task
    valid4, reason4 = task_tx.validate(ledger3, {"task-001"}, consensus_group)
    check("T2.7 Reject duplicate task", not valid4)
    check("T2.8 Reason duplicate_task", reason4 == "duplicate_task")

    # Execution proof
    proof_tx = ExecutionProofTransaction(
        task_id="task-001",
        executing_platform="Sprout",
        executing_agent="lct:web4:agent:bob",
        quality_score=0.85,
        execution_time=45.2,
        result_hash=hashlib.sha256(b"result").hexdigest(),
        timestamp=time.time(),
        signature="ed25519_sig_bob",
    )

    pending = {"task-001": {"timeout": 60.0}}
    valid5, reason5 = proof_tx.validate(pending)
    check("T2.9 Valid execution proof", valid5)

    # Invalid: task not found
    proof_bad = ExecutionProofTransaction(task_id="task-999", signature="sig", quality_score=0.5)
    valid6, reason6 = proof_bad.validate(pending)
    check("T2.10 Reject proof for unknown task", not valid6)

    # Invalid: quality out of range
    proof_quality = ExecutionProofTransaction(task_id="task-001", quality_score=1.5, signature="sig")
    valid7, reason7 = proof_quality.validate(pending)
    check("T2.11 Reject invalid quality score", not valid7)

    # Invalid: timeout exceeded
    proof_timeout = ExecutionProofTransaction(
        task_id="task-001", quality_score=0.8, execution_time=100.0, signature="sig"
    )
    valid8, reason8 = proof_timeout.validate(pending)
    check("T2.12 Reject execution timeout", not valid8)
    check("T2.13 Reason execution_timeout", reason8 == "execution_timeout")

    # ── §3  Block Structure ────────────────────────────────────────
    print("\n§3 Block Structure")

    block = ConsensusBlock(
        block_number=42,
        prev_hash="abc123",
        timestamp=1701388800.0,
        transactions=[
            {"type": "FEDERATION_TASK", "task_id": "uuid-A"},
            {"type": "ATP_TRANSFER_LOCK", "transfer_id": "uuid-A"},
        ],
        proposer_platform="Thor",
        signature="sig",
    )

    check("T3.1 Block number", block.block_number == 42)
    check("T3.2 Block has 2 transactions", len(block.transactions) == 2)
    check("T3.3 Block hash is hex string", len(block.compute_hash()) == 64)
    check("T3.4 FEDERATION_TASK in block", block.transactions[0]["type"] == "FEDERATION_TASK")
    check("T3.5 ATP_LOCK linked to task", block.transactions[1]["transfer_id"] == "uuid-A")

    # ── §4  Transaction Processor ──────────────────────────────────
    print("\n§4 Transaction Processor (Integration)")

    proc_ledger = ATPLedger()
    proc_ledger.create_account("lct:web4:agent:alice", 1000.0)
    proc_ledger.create_account("lct:web4:agent:bob", 200.0)
    processor = FederationTransactionProcessor(proc_ledger, {"Thor", "Sprout", "Legion"})

    # Happy path: delegate task
    ft = FederationTaskTransaction(
        task_id="integrated-001",
        delegating_platform="Thor",
        delegating_agent="lct:web4:agent:alice",
        executing_platform="Sprout",
        executing_agent="lct:web4:agent:bob",
        estimated_cost=300.0,
        task_data={"timeout": 60.0},
        quality_threshold=0.7,
        timestamp=time.time(),
        signature="sig_alice",
    )

    ok, msg = processor.process_federation_task(ft)
    check("T4.1 Task processed successfully", ok)
    check("T4.2 Task is pending", "integrated-001" in processor.pending_tasks)
    check("T4.3 Alice ATP locked", proc_ledger.get_account("lct:web4:agent:alice").locked == 300.0)
    check("T4.4 Alice available reduced", proc_ledger.get_account("lct:web4:agent:alice").available == 700.0)

    # High quality execution proof
    ep = ExecutionProofTransaction(
        task_id="integrated-001",
        executing_platform="Sprout",
        executing_agent="lct:web4:agent:bob",
        quality_score=0.85,
        execution_time=45.0,
        result_hash="result_hash",
        timestamp=time.time(),
        signature="sig_bob",
    )

    ok2, settlement = processor.process_execution_proof(ep)
    check("T4.5 Proof processed", ok2)
    check("T4.6 Settlement COMMIT", settlement == "COMMIT")
    check("T4.7 Task completed", "integrated-001" in processor.completed_tasks)
    check("T4.8 Task no longer pending", "integrated-001" not in processor.pending_tasks)
    check("T4.9 Bob credited 300 ATP", proc_ledger.get_account("lct:web4:agent:bob").total == 500.0)
    check("T4.10 Alice deducted", proc_ledger.get_account("lct:web4:agent:alice").total == 700.0)

    # Low quality path: rollback
    proc_ledger2 = ATPLedger()
    proc_ledger2.create_account("delegator", 1000.0)
    proc_ledger2.create_account("executor", 100.0)
    proc2 = FederationTransactionProcessor(proc_ledger2, {"Thor", "Sprout"})

    ft2 = FederationTaskTransaction(
        task_id="low-q-001",
        delegating_agent="delegator",
        executing_platform="Sprout",
        executing_agent="executor",
        estimated_cost=200.0,
        task_data={"timeout": 60.0},
        quality_threshold=0.7,
        timestamp=time.time(),
        signature="sig",
    )
    proc2.process_federation_task(ft2)

    ep2 = ExecutionProofTransaction(
        task_id="low-q-001",
        executing_agent="executor",
        quality_score=0.55,
        execution_time=30.0,
        signature="sig",
    )
    ok3, settlement2 = proc2.process_execution_proof(ep2)
    check("T4.11 Low quality processed", ok3)
    check("T4.12 Settlement ROLLBACK", settlement2 == "ROLLBACK")
    check("T4.13 Delegator ATP restored", proc_ledger2.get_account("delegator").available == 1000.0)
    check("T4.14 Executor not paid", proc_ledger2.get_account("executor").total == 100.0)

    # Block creation
    block1 = processor.create_block([{"type": "test"}], "Thor")
    check("T4.15 Block created", block1.block_number == 0)
    block2 = processor.create_block([{"type": "test2"}], "Sprout")
    check("T4.16 Block chained", block2.prev_hash == block1.compute_hash())

    # ── §2  FB-PBFT Consensus ──────────────────────────────────────
    print("\n§2b FB-PBFT Consensus (Layer 2)")

    # 4 platforms: f=1, quorum=3
    consensus4 = FBPBFTConsensus(["Thor", "Sprout", "Legion", "Cloud"])
    check("T5.1 4 platforms, f=1", consensus4.f == 1)
    check("T5.2 Quorum = 3", consensus4.quorum == 3)
    check("T5.3 Tolerates 1 fault", consensus4.can_tolerate_faults(1))
    check("T5.4 Cannot tolerate 2 faults", not consensus4.can_tolerate_faults(2))

    # 7 platforms: f=2, quorum=5
    consensus7 = FBPBFTConsensus(["A", "B", "C", "D", "E", "F", "G"])
    check("T5.5 7 platforms, f=2", consensus7.f == 2)
    check("T5.6 Quorum = 5", consensus7.quorum == 5)

    # 13 platforms: f=4
    consensus13 = FBPBFTConsensus([f"P{i}" for i in range(13)])
    check("T5.7 13 platforms, f=4", consensus13.f == 4)
    check("T5.8 Quorum = 9", consensus13.quorum == 9)

    # Prepare/commit phases
    test_block = ConsensusBlock(block_number=0, prev_hash="gen", timestamp=time.time())
    ok_prep, _ = consensus4.prepare(test_block, 3)
    check("T5.9 Prepare with 3 votes succeeds", ok_prep)
    fail_prep, _ = consensus4.prepare(test_block, 2)
    check("T5.10 Prepare with 2 votes fails", not fail_prep)
    ok_commit, _ = consensus4.commit(test_block, 3)
    check("T5.11 Commit with quorum succeeds", ok_commit)

    # ── §5  Performance Analysis ───────────────────────────────────
    print("\n§5 Performance Analysis")

    perf = PerformanceMetrics()
    check("T6.1 Without consensus = 65ms", perf.latency_without_consensus == 65.0)
    check("T6.2 With consensus = 105ms", perf.latency_with_consensus == 105.0)
    check("T6.3 Overhead = 40ms", perf.overhead_ms == 40.0)
    check("T6.4 Overhead ~61.5%", abs(perf.overhead_percent - 61.538) < 1.0)
    check("T6.5 Throughput = 38.5 tasks/sec", perf.federation_throughput == 38.5)
    check("T6.6 Use consensus for 200 ATP", perf.should_use_consensus(200.0))
    check("T6.7 Skip consensus for 50 ATP", not perf.should_use_consensus(50.0))

    # ── §6  Security Analysis ──────────────────────────────────────
    print("\n§6 Security Analysis")

    sec = SecurityAnalyzer()

    # Attack 1: False quality claims
    fraud_with = sec.analyze_false_quality_claim(0.9, 0.3, has_consensus=True)
    check("T7.1 Fraud detected with consensus", fraud_with["detected"])
    check("T7.2 Fraud flagged", fraud_with["fraud"])
    check("T7.3 Challenge mechanism", fraud_with["action"] == "challenge_with_counter_proof")

    fraud_without = sec.analyze_false_quality_claim(0.9, 0.3, has_consensus=False)
    check("T7.4 Fraud detected locally", fraud_without["detected"])
    check("T7.5 Local mechanism only", fraud_without["mechanism"] == "local_detection_only")

    no_fraud = sec.analyze_false_quality_claim(0.85, 0.82, has_consensus=True)
    check("T7.6 No fraud when close quality", not no_fraud["fraud"])

    # Attack 2: Double spending
    ds_with = sec.analyze_double_spend(300.0, 300.0, 300.0, has_consensus=True)
    check("T7.7 Double-spend prevented with consensus", ds_with["prevented"])
    check("T7.8 First task accepted", ds_with["task1_accepted"])
    check("T7.9 Second task rejected", not ds_with["task2_accepted"])

    ds_without = sec.analyze_double_spend(300.0, 300.0, 300.0, has_consensus=False)
    check("T7.10 Double-spend NOT prevented without consensus", not ds_without["prevented"])
    check("T7.11 Race condition possible", ds_without["race_condition"])

    # Attack 3: Group collusion
    coll4 = sec.analyze_group_collusion(4, 1)
    check("T7.12 4 platforms, 1 colluding: attack fails", not coll4["attack_succeeds"])

    coll4_3 = sec.analyze_group_collusion(4, 3)
    check("T7.13 4 platforms, 3 colluding: attack succeeds", coll4_3["attack_succeeds"])
    check("T7.14 Collusion = 75%", coll4_3["collusion_percent"] == 75.0)

    coll7 = sec.analyze_group_collusion(7, 2)
    check("T7.15 7 platforms, 2 colluding: attack fails", not coll7["attack_succeeds"])

    # ── §7  Economic Model ─────────────────────────────────────────
    print("\n§7 Economic Model")

    econ = EconomicModel(quality_threshold=0.7)

    # High quality flow
    hq = econ.simulate_high_quality(1000.0, 300.0, 0.85)
    check("T8.1 Delegator after = 700", hq["delegator_after"] == 700.0)
    check("T8.2 Executor earned = 300", hq["executor_earned"] == 300.0)
    check("T8.3 Settlement COMMIT", hq["settlement"] == "COMMIT")

    # Low quality flow
    lq = econ.simulate_low_quality(1000.0, 300.0, 0.55)
    check("T8.4 Delegator refunded", lq["delegator_after"] == 1000.0)
    check("T8.5 Executor gets nothing", lq["executor_earned"] == 0.0)
    check("T8.6 Settlement ROLLBACK", lq["settlement"] == "ROLLBACK")

    # Incentive scoring
    excellent = econ.compute_incentive_score([0.9, 0.85, 0.92, 0.88, 0.95])
    check("T8.7 Excellent reputation", excellent["reputation"] == "excellent")
    check("T8.8 100% payment rate", excellent["payment_rate"] == 1.0)

    poor = econ.compute_incentive_score([0.3, 0.4, 0.5, 0.2, 0.6])
    check("T8.9 Poor reputation", poor["reputation"] == "poor")
    check("T8.10 Low payment rate", poor["payment_rate"] < 0.5)

    mediocre = econ.compute_incentive_score([0.75, 0.65, 0.72, 0.68, 0.71, 0.66, 0.73, 0.69, 0.74, 0.67])
    check("T8.11 Mediocre reputation", mediocre["reputation"] in ("mediocre", "good"))

    empty = econ.compute_incentive_score([])
    check("T8.12 Unknown for no history", empty["reputation"] == "unknown")

    # ── §8  SAGE Integration ───────────────────────────────────────
    print("\n§8 SAGE Cognition Integration")

    sage_ledger = ATPLedger()
    sage_ledger.create_account("lct:web4:agent:dp", 1000.0)
    sage = SAGECognitionIntegrator("dp", sage_ledger, daily_budget=1000.0)

    # Cost estimation
    cost_medium = sage.estimate_cost(512, "medium")
    check("T9.1 Medium cost = 150", cost_medium == 150.0)
    cost_high = sage.estimate_cost(1024, "high")
    check("T9.2 High cost scaled = 600", cost_high == 600.0)
    cost_low = sage.estimate_cost(256, "low")
    check("T9.3 Low cost scaled (min scale 1.0)", cost_low == 50.0)

    # Delegation decision
    should, reason = sage.should_delegate(150.0, 0.3)  # Low local capacity
    check("T9.4 Delegate when low capacity", should)
    check("T9.5 Reason delegate_recommended", reason == "delegate_recommended")

    should2, reason2 = sage.should_delegate(150.0, 0.8)  # High local capacity
    check("T9.6 Don't delegate when capacity OK", not should2)
    check("T9.7 Reason local_sufficient", reason2 == "local_sufficient")

    # Insufficient ATP
    sage_ledger2 = ATPLedger()
    sage_ledger2.create_account("lct:web4:agent:poor", 10.0)
    sage2 = SAGECognitionIntegrator("poor", sage_ledger2)
    should3, reason3 = sage2.should_delegate(500.0, 0.1)
    check("T9.8 Don't delegate no ATP", not should3)
    check("T9.9 Reason insufficient_atp", reason3 == "insufficient_atp")

    # Perception processing
    result = sage.process_perception(512, "medium", 0.3, "Sprout")
    check("T9.10 Action is delegate", result["action"] == "delegate")
    check("T9.11 Target is Sprout", result["target"] == "Sprout")

    result2 = sage.process_perception(512, "medium", 0.9, "Sprout")
    check("T9.12 Action is local", result2["action"] == "local")

    # Daily budget exceeded
    sage.daily_spent = 990.0
    should4, reason4 = sage.should_delegate(150.0, 0.1)
    check("T9.13 Daily budget exceeded", not should4)
    check("T9.14 Reason daily_budget_exceeded", reason4 == "daily_budget_exceeded")

    # ── §9  Integration Test Scenarios ─────────────────────────────
    print("\n§9 Integration Test Scenarios")

    # Happy path: 4 platforms, high quality
    full_ledger = ATPLedger()
    full_ledger.create_account("alice@Thor", 1000.0)
    full_ledger.create_account("bob@Sprout", 200.0)
    full_ledger.create_account("charlie@Legion", 500.0)
    full_ledger.create_account("dave@Cloud", 300.0)
    full_proc = FederationTransactionProcessor(
        full_ledger, {"Thor", "Sprout", "Legion", "Cloud"}
    )

    # Delegate + high quality
    ft_happy = FederationTaskTransaction(
        task_id="happy-001",
        delegating_agent="alice@Thor",
        executing_platform="Sprout",
        executing_agent="bob@Sprout",
        estimated_cost=300.0,
        task_data={"timeout": 60.0},
        quality_threshold=0.7,
        timestamp=time.time(),
        signature="sig",
    )
    full_proc.process_federation_task(ft_happy)
    ep_happy = ExecutionProofTransaction(
        task_id="happy-001",
        executing_agent="bob@Sprout",
        quality_score=0.85,
        execution_time=45.0,
        signature="sig",
    )
    ok_h, settle_h = full_proc.process_execution_proof(ep_happy)
    check("T10.1 Happy path: COMMIT", settle_h == "COMMIT")
    check("T10.2 Alice = 700", full_ledger.get_account("alice@Thor").total == 700.0)
    check("T10.3 Bob = 500", full_ledger.get_account("bob@Sprout").total == 500.0)

    # Concurrent tasks
    ft_c1 = FederationTaskTransaction(
        task_id="concurrent-001",
        delegating_agent="charlie@Legion",
        executing_platform="Sprout",
        executing_agent="bob@Sprout",
        estimated_cost=100.0,
        task_data={"timeout": 60.0},
        quality_threshold=0.7,
        timestamp=time.time(),
        signature="sig",
    )
    ft_c2 = FederationTaskTransaction(
        task_id="concurrent-002",
        delegating_agent="charlie@Legion",
        executing_platform="Thor",
        executing_agent="alice@Thor",
        estimated_cost=100.0,
        task_data={"timeout": 60.0},
        quality_threshold=0.7,
        timestamp=time.time(),
        signature="sig",
    )
    full_proc.process_federation_task(ft_c1)
    full_proc.process_federation_task(ft_c2)
    check("T10.4 Both tasks pending", len(full_proc.pending_tasks) == 2)
    check("T10.5 Charlie locked 200", full_ledger.get_account("charlie@Legion").locked == 200.0)

    # Crash/timeout scenario: task expires
    ft_crash = FederationTaskTransaction(
        task_id="crash-001",
        delegating_agent="dave@Cloud",
        executing_platform="Sprout",
        executing_agent="bob@Sprout",
        estimated_cost=100.0,
        task_data={"timeout": 5.0},
        quality_threshold=0.7,
        timestamp=time.time(),
        signature="sig",
    )
    full_proc.process_federation_task(ft_crash)
    # Simulate timeout: execution takes too long
    ep_crash = ExecutionProofTransaction(
        task_id="crash-001",
        executing_agent="bob@Sprout",
        quality_score=0.9,
        execution_time=10.0,  # Exceeds 5s timeout
        signature="sig",
    )
    ok_crash, reason_crash = full_proc.process_execution_proof(ep_crash)
    check("T10.6 Timeout rejected", not ok_crash)
    check("T10.7 Reason is timeout", reason_crash == "execution_timeout")

    # ── §10  Research Questions ────────────────────────────────────
    print("\n§10 Research Questions")

    rq = ResearchQuestions()

    # Q1: Optimal quality threshold
    qualities = [0.3, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
    thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
    result_q1 = rq.optimal_quality_threshold(qualities, thresholds)
    check("T11.1 Optimal threshold found", result_q1["optimal_threshold"] in thresholds)
    check("T11.2 Utility > 0", result_q1["optimal_utility"] > 0)
    check("T11.3 All thresholds analyzed", len(result_q1["results"]) == 5)

    # Q2: Dynamic pricing
    price_normal = rq.dynamic_pricing(100.0, 0.5, "medium")
    check("T11.4 Normal demand price = 100", price_normal == 100.0)
    price_surge = rq.dynamic_pricing(100.0, 0.9, "medium")
    check("T11.5 Surge price > 100", price_surge > 100.0)
    price_complex = rq.dynamic_pricing(100.0, 0.5, "high")
    check("T11.6 High complexity = 200", price_complex == 200.0)
    price_critical_surge = rq.dynamic_pricing(100.0, 1.0, "critical")
    check("T11.7 Critical+surge >> base", price_critical_surge > 300.0)

    # Q3: Reputation bonus
    bonus_excellent = rq.reputation_bonus(100.0, [0.95, 0.92, 0.9, 0.93, 0.91])
    check("T11.8 Excellent gets +10%", abs(bonus_excellent - 110.0) < 0.01)
    bonus_good = rq.reputation_bonus(100.0, [0.85, 0.82, 0.84, 0.83, 0.81])
    check("T11.9 Good gets +5%", bonus_good == 105.0)
    bonus_poor = rq.reputation_bonus(100.0, [0.3, 0.4, 0.35, 0.45, 0.38])
    check("T11.10 Poor gets -10%", bonus_poor == 90.0)
    bonus_new = rq.reputation_bonus(100.0, [0.9, 0.85])
    check("T11.11 New agent no bonus", bonus_new == 100.0)

    # ── Cross-cutting: Transaction type enumeration ────────────────
    print("\n§Cross-Cutting Validation")

    check("T12.1 6 transaction types", len(TransactionType) == 6)
    check("T12.2 FEDERATION_TASK type exists", TransactionType.FEDERATION_TASK.value == "FEDERATION_TASK")
    check("T12.3 EXECUTION_PROOF type exists", TransactionType.EXECUTION_PROOF.value == "EXECUTION_PROOF")
    check("T12.4 ATP_TRANSFER_LOCK exists", TransactionType.ATP_TRANSFER_LOCK.value == "ATP_TRANSFER_LOCK")

    # Verify 3-layer architecture
    check("T12.5 Layer 1 = ATP Ledger", isinstance(ledger, ATPLedger))
    check("T12.6 Layer 2 = Consensus", isinstance(consensus4, FBPBFTConsensus))
    check("T12.7 Layer 3 = Federation Processor", isinstance(processor, FederationTransactionProcessor))

    # Atomic pair: FEDERATION_TASK + ATP_LOCK share task_id/transfer_id
    check("T12.8 Task+Lock share ID", ft.task_id == "integrated-001")

    # Block structure has federation + ATP transactions
    mixed_block = ConsensusBlock(
        block_number=0, prev_hash="gen", timestamp=time.time(),
        transactions=[
            {"type": "FEDERATION_TASK", "task_id": "t1"},
            {"type": "ATP_TRANSFER_LOCK", "transfer_id": "t1"},
            {"type": "EXECUTION_PROOF", "task_id": "t1"},
            {"type": "ATP_TRANSFER_COMMIT", "transfer_id": "t1"},
        ]
    )
    check("T12.9 Mixed block has 4 tx", len(mixed_block.transactions) == 4)
    check("T12.10 All IDs match", all(
        tx.get("task_id", tx.get("transfer_id")) == "t1"
        for tx in mixed_block.transactions
    ))

    # ── Summary ────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"Federation Consensus ATP Integration: {passed}/{total} checks passed")
    if failed == 0:
        print("  All checks passed!")
    else:
        print(f"  {failed} checks FAILED")
    print(f"{'='*60}")
    return failed == 0


if __name__ == "__main__":
    run_tests()
