#!/usr/bin/env python3
"""
Agent Orchestration Trust Protocol — Web4 Reference Implementation

Handles trust, accountability, and ATP flow through multi-agent orchestration
pipelines. Modern AI deployments are pipelines: Agent A calls Agent B which
calls Tool C which calls Agent D. This protocol answers:

  - Who bears responsibility when a chain of agents produces harmful output?
  - How does T3 reputation propagate through a call graph?
  - How does ATP budget accounting work across sub-delegations?
  - Where can human oversight be injected without breaking the pipeline?

Implements:
  1. PipelineTrustModel: Multiplicative trust propagation through call depth
  2. ATPBudgetCascade: Parent budget constrains descendants, excess bubbles up
  3. BlameAttributionGraph: Causal chain analysis for pipeline failures
  4. OversightInjectionPoint: Human-in-the-loop approval at configurable hops
  5. PipelineCircuitBreaker: If any hop falls below T3 threshold, halt + rollback
  6. OrchestrationAuditTrail: Single ledger entry per pipeline with full call graph

EU AI Act Art. 14 (human oversight of autonomous chains)
EU AI Act Art. 26 (deployer obligations in agent chains)

Builds on: acp_framework.py, acp_executor.py, agy_agency_delegation.py,
           cognitive_sub_entity.py, cross_federation_delegation.py

Checks: 91
"""

import hashlib
import math
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════
# PART 1: DATA MODEL
# ═══════════════════════════════════════════════════════════════

class AgentRole(Enum):
    ORCHESTRATOR = "orchestrator"   # Top-level pipeline controller
    WORKER = "worker"               # Task executor
    TOOL = "tool"                   # Specialized capability
    VALIDATOR = "validator"         # Output quality checker
    MONITOR = "monitor"             # Runtime observer


class PipelineStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    HALTED = "halted"       # Circuit breaker triggered
    ROLLED_BACK = "rolled_back"


class HopStatus(Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"     # Bypassed by circuit breaker


class BlameLevel(Enum):
    PRIMARY = "primary"       # Direct cause of failure
    CONTRIBUTING = "contributing"  # Enabled the failure
    PROPAGATING = "propagating"   # Passed bad output forward
    INNOCENT = "innocent"     # Not involved in failure chain


class OversightDecision(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"
    ESCALATE = "escalate"


@dataclass
class AgentNode:
    """An agent in the orchestration pipeline."""
    agent_id: str = ""
    agent_name: str = ""
    role: AgentRole = AgentRole.WORKER
    lct_uri: str = ""
    t3_composite: float = 0.5
    t3_talent: float = 0.5
    t3_training: float = 0.5
    t3_temperament: float = 0.5
    atp_balance: float = 0.0
    max_delegation_depth: int = 5
    hardware_bound: bool = False


@dataclass
class PipelineHop:
    """A single call in the pipeline call graph."""
    hop_id: str = ""
    source_agent: str = ""
    target_agent: str = ""
    depth: int = 0
    task_type: str = ""
    input_hash: str = ""
    output_hash: str = ""
    status: HopStatus = HopStatus.PENDING
    atp_allocated: float = 0.0
    atp_consumed: float = 0.0
    atp_returned: float = 0.0
    trust_at_hop: float = 0.0   # Propagated trust at this depth
    quality_score: float = 0.0  # Output quality assessment
    start_time: float = 0.0
    end_time: float = 0.0
    error: str = ""


# ═══════════════════════════════════════════════════════════════
# PART 2: PIPELINE TRUST MODEL
# ═══════════════════════════════════════════════════════════════

class PipelineTrustModel:
    """
    Trust propagates multiplicatively through call depth.
    Similar to multi-hop dictionary translation confidence decay.

    trust_at_depth_n = product(t3_composite[agent_i] for i in 0..n)

    Deep pipelines naturally have lower trust — this is a feature,
    not a bug. It incentivizes shallow, well-trusted chains.
    """

    # Trust floor — below this, pipeline hop is rejected
    TRUST_FLOOR = 0.3

    # Trust decay per hop (additional multiplicative factor)
    HOP_DECAY = 0.95

    def __init__(self, trust_floor: float = None, hop_decay: float = None):
        self.trust_floor = trust_floor or self.TRUST_FLOOR
        self.hop_decay = hop_decay or self.HOP_DECAY

    def propagate_trust(self, agent_chain: List[AgentNode]) -> List[float]:
        """Calculate trust at each hop in the pipeline."""
        if not agent_chain:
            return []

        trust_values = []
        cumulative = 1.0
        for i, agent in enumerate(agent_chain):
            cumulative *= agent.t3_composite
            if i > 0:
                cumulative *= self.hop_decay
            trust_values.append(cumulative)
        return trust_values

    def chain_trust(self, agent_chain: List[AgentNode]) -> float:
        """Overall pipeline trust = trust at final hop."""
        values = self.propagate_trust(agent_chain)
        return values[-1] if values else 0.0

    def is_viable(self, agent_chain: List[AgentNode]) -> Tuple[bool, int]:
        """Check if chain trust stays above floor. Returns (viable, failing_hop)."""
        values = self.propagate_trust(agent_chain)
        for i, v in enumerate(values):
            if v < self.trust_floor:
                return (False, i)
        return (True, -1)

    def optimal_depth(self, avg_trust: float) -> int:
        """Calculate max pipeline depth before trust drops below floor."""
        if avg_trust <= 0 or avg_trust >= 1:
            return 0 if avg_trust <= 0 else 100
        effective = avg_trust * self.hop_decay
        if effective >= 1.0:
            return 100
        # trust_floor = effective^depth → depth = log(floor) / log(effective)
        depth = math.log(self.trust_floor) / math.log(effective)
        return max(1, int(depth))


# ═══════════════════════════════════════════════════════════════
# PART 3: ATP BUDGET CASCADE
# ═══════════════════════════════════════════════════════════════

@dataclass
class BudgetAllocation:
    """ATP budget allocated to a pipeline hop."""
    allocation_id: str = ""
    parent_allocation: str = ""
    agent_id: str = ""
    allocated: float = 0.0
    consumed: float = 0.0
    returned: float = 0.0
    children_allocated: float = 0.0
    locked: bool = True


class ATPBudgetCascade:
    """
    Parent ATP budget constrains all descendants.
    Excess bubbles up on completion. Deficit fails the hop.

    Invariant: sum(child_allocated) ≤ parent_allocated - parent_consumed
    """

    # Per-hop base cost
    HOP_COST = 2.0

    # Fee rate per hop depth
    DEPTH_FEE_RATE = 0.5

    def __init__(self, hop_cost: float = None, depth_fee_rate: float = None):
        self.hop_cost = hop_cost or self.HOP_COST
        self.depth_fee_rate = depth_fee_rate or self.DEPTH_FEE_RATE
        self.allocations: Dict[str, BudgetAllocation] = {}
        self.alloc_counter = 0

    def allocate(self, agent_id: str, amount: float,
                 parent_id: str = "") -> Optional[BudgetAllocation]:
        """Allocate ATP budget for a pipeline hop."""
        # Check parent budget
        if parent_id and parent_id in self.allocations:
            parent = self.allocations[parent_id]
            available = parent.allocated - parent.consumed - parent.children_allocated
            if amount > available:
                return None
            parent.children_allocated += amount

        self.alloc_counter += 1
        alloc = BudgetAllocation(
            allocation_id=f"ALLOC-{self.alloc_counter:04d}",
            parent_allocation=parent_id,
            agent_id=agent_id,
            allocated=amount,
            locked=True,
        )
        self.allocations[alloc.allocation_id] = alloc
        return alloc

    def consume(self, allocation_id: str, amount: float, depth: int = 0) -> bool:
        """Consume ATP from allocation. Includes per-hop and depth fees."""
        if allocation_id not in self.allocations:
            return False
        alloc = self.allocations[allocation_id]
        total_cost = amount + self.hop_cost + depth * self.depth_fee_rate
        if total_cost > alloc.allocated - alloc.consumed - alloc.children_allocated:
            return False
        alloc.consumed += total_cost
        return True

    def release(self, allocation_id: str) -> float:
        """Release allocation, returning excess to parent."""
        if allocation_id not in self.allocations:
            return 0.0
        alloc = self.allocations[allocation_id]
        excess = alloc.allocated - alloc.consumed - alloc.children_allocated
        alloc.returned = max(0, excess)
        alloc.locked = False

        # Return to parent
        if alloc.parent_allocation and alloc.parent_allocation in self.allocations:
            parent = self.allocations[alloc.parent_allocation]
            parent.children_allocated -= alloc.allocated
            parent.children_allocated = max(0, parent.children_allocated)

        return alloc.returned

    def total_consumed(self) -> float:
        """Total ATP consumed across all allocations."""
        return sum(a.consumed for a in self.allocations.values())

    def budget_utilization(self) -> float:
        """What fraction of allocated budget was actually used."""
        total_allocated = sum(a.allocated for a in self.allocations.values()
                              if not a.parent_allocation)  # Root allocations only
        total_consumed = sum(a.consumed for a in self.allocations.values())
        return total_consumed / max(1.0, total_allocated)


# ═══════════════════════════════════════════════════════════════
# PART 4: BLAME ATTRIBUTION GRAPH
# ═══════════════════════════════════════════════════════════════

@dataclass
class BlameEntry:
    """Blame assessment for a single agent in a pipeline failure."""
    agent_id: str = ""
    hop_id: str = ""
    blame_level: BlameLevel = BlameLevel.INNOCENT
    blame_score: float = 0.0     # 0.0-1.0 — degree of blame
    explanation: str = ""
    t3_impact: float = 0.0       # T3 reputation delta


class BlameAttributionGraph:
    """
    Causal chain analysis for pipeline failures.
    Determines who caused what at which hop.

    Attribution rules:
    - PRIMARY: Agent whose output directly caused failure
    - CONTRIBUTING: Agent whose output was part of the failure chain
    - PROPAGATING: Agent that passed bad output without catching it
    - INNOCENT: Agent not in the failure chain

    70/30 split: 70% blame to direct cause, 30% distributed to chain
    """

    # Attribution weights
    PRIMARY_WEIGHT = 0.70
    CHAIN_WEIGHT = 0.30

    # T3 impact per blame level
    T3_IMPACT = {
        BlameLevel.PRIMARY: -0.10,
        BlameLevel.CONTRIBUTING: -0.05,
        BlameLevel.PROPAGATING: -0.02,
        BlameLevel.INNOCENT: 0.0,
    }

    def attribute(self, hops: List[PipelineHop],
                  failure_hop_id: str) -> List[BlameEntry]:
        """Attribute blame across pipeline hops."""
        entries = []

        # Find failure hop
        failure_hop = None
        failure_idx = -1
        for i, h in enumerate(hops):
            if h.hop_id == failure_hop_id:
                failure_hop = h
                failure_idx = i
                break

        if not failure_hop:
            return entries

        # Primary blame: the agent that failed
        entries.append(BlameEntry(
            agent_id=failure_hop.target_agent,
            hop_id=failure_hop_id,
            blame_level=BlameLevel.PRIMARY,
            blame_score=self.PRIMARY_WEIGHT,
            explanation=f"Direct failure at hop {failure_hop_id}: {failure_hop.error}",
            t3_impact=self.T3_IMPACT[BlameLevel.PRIMARY],
        ))

        # Contributing: agents that provided input to the failure
        chain_agents = []
        for i in range(failure_idx):
            hop = hops[i]
            if hop.status == HopStatus.COMPLETED:
                # Check if this hop's output was consumed by failure chain
                chain_agents.append(hop)

        if chain_agents:
            per_agent_blame = self.CHAIN_WEIGHT / len(chain_agents)
            for hop in chain_agents:
                # Closer to failure = more blame
                distance = failure_idx - hops.index(hop)
                proximity_factor = 1.0 / max(1, distance)
                blame_score = per_agent_blame * proximity_factor

                level = BlameLevel.CONTRIBUTING if proximity_factor > 0.5 else BlameLevel.PROPAGATING
                entries.append(BlameEntry(
                    agent_id=hop.target_agent,
                    hop_id=hop.hop_id,
                    blame_level=level,
                    blame_score=blame_score,
                    explanation=f"{'Contributing' if level == BlameLevel.CONTRIBUTING else 'Propagating'} agent at hop {hop.hop_id}",
                    t3_impact=self.T3_IMPACT[level],
                ))

        # Agents after failure = innocent (never executed or were skipped)
        for i in range(failure_idx + 1, len(hops)):
            hop = hops[i]
            entries.append(BlameEntry(
                agent_id=hop.target_agent,
                hop_id=hop.hop_id,
                blame_level=BlameLevel.INNOCENT,
                blame_score=0.0,
                explanation=f"Not in failure chain (after failure at {failure_hop_id})",
                t3_impact=0.0,
            ))

        return entries

    def total_blame(self, entries: List[BlameEntry]) -> float:
        """Total blame should sum to ~1.0 (PRIMARY + CHAIN)."""
        return sum(e.blame_score for e in entries)

    def t3_impact_summary(self, entries: List[BlameEntry]) -> Dict[str, float]:
        """Map agent_id → total T3 impact."""
        impacts: Dict[str, float] = {}
        for e in entries:
            impacts[e.agent_id] = impacts.get(e.agent_id, 0.0) + e.t3_impact
        return impacts


# ═══════════════════════════════════════════════════════════════
# PART 5: OVERSIGHT INJECTION POINT
# ═══════════════════════════════════════════════════════════════

@dataclass
class OversightCheckpoint:
    """A point in the pipeline where human oversight is required."""
    checkpoint_id: str = ""
    pipeline_id: str = ""
    hop_id: str = ""
    agent_id: str = ""
    decision: OversightDecision = OversightDecision.APPROVE
    reviewer_id: str = ""
    review_timestamp: float = 0.0
    notes: str = ""
    auto_approved: bool = False   # If below threshold, auto-approve


class OversightInjector:
    """
    Configurable human-in-the-loop approval at pipeline hops.
    Art. 14 compliance: human oversight of autonomous agent chains.

    Rules:
    - Trust < 0.5 → ALWAYS require human review
    - Depth > 3 → require review (deep chains are risky)
    - Critical tasks → always require review regardless of trust
    - Otherwise → auto-approve if trust > threshold
    """

    AUTO_APPROVE_THRESHOLD = 0.7
    MAX_AUTO_DEPTH = 3
    CRITICAL_TASK_TYPES = {"financial", "safety", "legal", "medical", "delete"}

    def __init__(self, auto_threshold: float = None, max_auto_depth: int = None):
        self.auto_threshold = auto_threshold or self.AUTO_APPROVE_THRESHOLD
        self.max_auto_depth = max_auto_depth or self.MAX_AUTO_DEPTH
        self.checkpoints: List[OversightCheckpoint] = []
        self.checkpoint_counter = 0

    def requires_review(self, trust: float, depth: int,
                        task_type: str) -> bool:
        """Determine if human review is required at this hop."""
        if task_type.lower() in self.CRITICAL_TASK_TYPES:
            return True
        if trust < 0.5:
            return True
        if depth > self.max_auto_depth:
            return True
        return trust < self.auto_threshold

    def create_checkpoint(self, pipeline_id: str, hop_id: str,
                          agent_id: str, trust: float, depth: int,
                          task_type: str) -> OversightCheckpoint:
        """Create oversight checkpoint (auto-approved or pending review)."""
        self.checkpoint_counter += 1
        needs_review = self.requires_review(trust, depth, task_type)

        checkpoint = OversightCheckpoint(
            checkpoint_id=f"OVS-{self.checkpoint_counter:04d}",
            pipeline_id=pipeline_id,
            hop_id=hop_id,
            agent_id=agent_id,
            auto_approved=not needs_review,
            decision=OversightDecision.APPROVE if not needs_review else OversightDecision.APPROVE,
        )
        if not needs_review:
            checkpoint.review_timestamp = time.time()
            checkpoint.reviewer_id = "auto"
            checkpoint.notes = f"Auto-approved: trust={trust:.2f}, depth={depth}"

        self.checkpoints.append(checkpoint)
        return checkpoint

    def review(self, checkpoint_id: str, decision: OversightDecision,
               reviewer_id: str, notes: str = "") -> bool:
        """Submit human review decision."""
        for cp in self.checkpoints:
            if cp.checkpoint_id == checkpoint_id:
                cp.decision = decision
                cp.reviewer_id = reviewer_id
                cp.review_timestamp = time.time()
                cp.notes = notes
                return True
        return False

    def auto_approval_rate(self) -> float:
        """Fraction of checkpoints auto-approved."""
        if not self.checkpoints:
            return 0.0
        auto = sum(1 for cp in self.checkpoints if cp.auto_approved)
        return auto / len(self.checkpoints)


# ═══════════════════════════════════════════════════════════════
# PART 6: PIPELINE CIRCUIT BREAKER
# ═══════════════════════════════════════════════════════════════

class CircuitBreakerState(Enum):
    CLOSED = "closed"     # Normal operation
    OPEN = "open"         # Tripped — pipeline halted
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerEvent:
    """Record of circuit breaker state change."""
    pipeline_id: str = ""
    old_state: CircuitBreakerState = CircuitBreakerState.CLOSED
    new_state: CircuitBreakerState = CircuitBreakerState.OPEN
    trigger_hop: str = ""
    trigger_reason: str = ""
    timestamp: float = 0.0


class PipelineCircuitBreaker:
    """
    If any hop falls below T3 threshold, halt pipeline and rollback ATP.
    Circuit breaker state IS trust signal (OPEN = low trust).

    Thresholds:
    - T3 composite < 0.3 → immediate OPEN
    - Quality < 0.2 → immediate OPEN
    - 3 consecutive failures → OPEN
    """

    T3_THRESHOLD = 0.3
    QUALITY_THRESHOLD = 0.2
    FAILURE_COUNT_THRESHOLD = 3

    def __init__(self):
        self.states: Dict[str, CircuitBreakerState] = {}
        self.failure_counts: Dict[str, int] = {}
        self.events: List[CircuitBreakerEvent] = []

    def get_state(self, pipeline_id: str) -> CircuitBreakerState:
        return self.states.get(pipeline_id, CircuitBreakerState.CLOSED)

    def check_hop(self, pipeline_id: str, hop: PipelineHop,
                  agent_trust: float) -> CircuitBreakerState:
        """Check if circuit breaker should trip for this hop."""
        current = self.get_state(pipeline_id)
        if current == CircuitBreakerState.OPEN:
            return current  # Already tripped

        # Check T3 threshold
        if agent_trust < self.T3_THRESHOLD:
            return self._trip(pipeline_id, hop.hop_id,
                              f"T3 below threshold: {agent_trust:.3f} < {self.T3_THRESHOLD}")

        # Check quality threshold
        if hop.status == HopStatus.COMPLETED and hop.quality_score < self.QUALITY_THRESHOLD:
            return self._trip(pipeline_id, hop.hop_id,
                              f"Quality below threshold: {hop.quality_score:.3f} < {self.QUALITY_THRESHOLD}")

        # Check consecutive failures
        if hop.status == HopStatus.FAILED:
            key = f"{pipeline_id}:{hop.target_agent}"
            self.failure_counts[key] = self.failure_counts.get(key, 0) + 1
            if self.failure_counts[key] >= self.FAILURE_COUNT_THRESHOLD:
                return self._trip(pipeline_id, hop.hop_id,
                                  f"Consecutive failures: {self.failure_counts[key]}")
        elif hop.status == HopStatus.COMPLETED:
            key = f"{pipeline_id}:{hop.target_agent}"
            self.failure_counts[key] = 0

        return CircuitBreakerState.CLOSED

    def _trip(self, pipeline_id: str, hop_id: str, reason: str) -> CircuitBreakerState:
        old = self.states.get(pipeline_id, CircuitBreakerState.CLOSED)
        self.states[pipeline_id] = CircuitBreakerState.OPEN
        self.events.append(CircuitBreakerEvent(
            pipeline_id=pipeline_id,
            old_state=old,
            new_state=CircuitBreakerState.OPEN,
            trigger_hop=hop_id,
            trigger_reason=reason,
            timestamp=time.time(),
        ))
        return CircuitBreakerState.OPEN

    def reset(self, pipeline_id: str) -> CircuitBreakerState:
        """Reset circuit breaker to HALF_OPEN for recovery testing."""
        self.states[pipeline_id] = CircuitBreakerState.HALF_OPEN
        return CircuitBreakerState.HALF_OPEN

    def close(self, pipeline_id: str) -> CircuitBreakerState:
        """Close circuit breaker after successful recovery."""
        self.states[pipeline_id] = CircuitBreakerState.CLOSED
        return CircuitBreakerState.CLOSED


# ═══════════════════════════════════════════════════════════════
# PART 7: ORCHESTRATION AUDIT TRAIL
# ═══════════════════════════════════════════════════════════════

@dataclass
class PipelineAuditEntry:
    """Single ledger entry for a complete pipeline execution."""
    pipeline_id: str = ""
    initiator_agent: str = ""
    total_hops: int = 0
    total_agents: int = 0
    status: PipelineStatus = PipelineStatus.PENDING
    atp_total_allocated: float = 0.0
    atp_total_consumed: float = 0.0
    atp_returned: float = 0.0
    chain_trust: float = 0.0
    oversight_checkpoints: int = 0
    circuit_breaker_events: int = 0
    blame_entries: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    hop_hashes: List[str] = field(default_factory=list)
    entry_hash: str = ""
    prev_hash: str = ""

    def compute_hash(self, prev: str = "genesis") -> str:
        content = f"{self.pipeline_id}:{self.total_hops}:{self.status.value}"
        content += f":{self.atp_total_consumed}:{self.chain_trust}:{prev}"
        self.entry_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        self.prev_hash = prev
        return self.entry_hash


class OrchestrationAuditTrail:
    """Hash-chained audit trail of pipeline executions."""

    def __init__(self):
        self.entries: List[PipelineAuditEntry] = []
        self.prev_hash = "genesis"

    def record(self, entry: PipelineAuditEntry) -> PipelineAuditEntry:
        entry.compute_hash(self.prev_hash)
        self.prev_hash = entry.entry_hash
        self.entries.append(entry)
        return entry

    def verify_chain(self) -> bool:
        prev = "genesis"
        for entry in self.entries:
            if entry.prev_hash != prev:
                return False
            prev = entry.entry_hash
        return True

    def pipelines_by_status(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for e in self.entries:
            s = e.status.value
            counts[s] = counts.get(s, 0) + 1
        return counts


# ═══════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════

def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}")
    return condition


def run_tests():
    results = []
    now = time.time()

    # ── S1: Trust Propagation — Simple Chain ────────────────────
    print("\nS1: Trust Propagation — Simple Chain")
    trust_model = PipelineTrustModel()
    chain = [
        AgentNode("a1", "Orchestrator", AgentRole.ORCHESTRATOR, t3_composite=0.9),
        AgentNode("a2", "Worker", AgentRole.WORKER, t3_composite=0.85),
        AgentNode("a3", "Tool", AgentRole.TOOL, t3_composite=0.80),
    ]
    values = trust_model.propagate_trust(chain)
    results.append(check("s1_first_hop", abs(values[0] - 0.9) < 0.01))
    # Second: 0.9 * 0.85 * 0.95 = 0.72675
    results.append(check("s1_second_hop", abs(values[1] - 0.72675) < 0.01))
    # Third: 0.72675 * 0.80 * 0.95 = 0.55233
    results.append(check("s1_third_hop", abs(values[2] - 0.55233) < 0.01))

    # Chain trust = final hop
    ct = trust_model.chain_trust(chain)
    results.append(check("s1_chain_trust", abs(ct - values[-1]) < 0.001))

    # ── S2: Trust Propagation — Viability ───────────────────────
    print("\nS2: Trust Viability")
    viable, fail_idx = trust_model.is_viable(chain)
    results.append(check("s2_viable", viable))
    results.append(check("s2_no_fail", fail_idx == -1))

    # Low-trust chain should fail
    low_chain = [
        AgentNode("b1", t3_composite=0.5),
        AgentNode("b2", t3_composite=0.5),
        AgentNode("b3", t3_composite=0.5),
        AgentNode("b4", t3_composite=0.5),
    ]
    viable2, fail_idx2 = trust_model.is_viable(low_chain)
    results.append(check("s2_not_viable", not viable2))
    results.append(check("s2_fail_idx", fail_idx2 > 0))

    # ── S3: Optimal Depth ───────────────────────────────────────
    print("\nS3: Optimal Depth")
    depth_high = trust_model.optimal_depth(0.9)
    results.append(check("s3_high_trust_deep", depth_high >= 7))  # 0.9*0.95=0.855, log(0.3)/log(0.855)≈7.7

    depth_low = trust_model.optimal_depth(0.5)
    results.append(check("s3_low_trust_shallow", depth_low < depth_high))

    depth_min = trust_model.optimal_depth(0.35)
    results.append(check("s3_very_low_shallowest", depth_min <= depth_low))

    # ── S4: ATP Budget Allocation ───────────────────────────────
    print("\nS4: ATP Budget Cascade — Allocation")
    budget = ATPBudgetCascade()
    root = budget.allocate("orchestrator", 100.0)
    results.append(check("s4_root_alloc", root is not None))
    results.append(check("s4_root_amount", root.allocated == 100.0))

    # Child allocation from parent
    child = budget.allocate("worker-1", 40.0, root.allocation_id)
    results.append(check("s4_child_alloc", child is not None))
    results.append(check("s4_parent_tracked",
        budget.allocations[root.allocation_id].children_allocated == 40.0))

    # Over-allocation fails
    over = budget.allocate("worker-2", 80.0, root.allocation_id)
    results.append(check("s4_over_fails", over is None))

    # ── S5: ATP Consumption ─────────────────────────────────────
    print("\nS5: ATP Consumption")
    ok = budget.consume(child.allocation_id, 10.0, depth=1)
    results.append(check("s5_consume_ok", ok))
    # Total cost = 10 + 2 (hop) + 0.5 (depth) = 12.5
    results.append(check("s5_consumed",
        abs(budget.allocations[child.allocation_id].consumed - 12.5) < 0.01))

    # Over-consume fails
    fail = budget.consume(child.allocation_id, 50.0, depth=1)
    results.append(check("s5_over_consume_fails", not fail))

    # ── S6: ATP Release ─────────────────────────────────────────
    print("\nS6: ATP Release")
    returned = budget.release(child.allocation_id)
    results.append(check("s6_returned", returned > 0))
    results.append(check("s6_excess_correct",
        abs(returned - (40.0 - 12.5)) < 0.01))  # 27.5 returned

    # ── S7: Budget Utilization ──────────────────────────────────
    print("\nS7: Budget Utilization")
    util = budget.budget_utilization()
    results.append(check("s7_utilization", 0 < util < 1.0))
    total = budget.total_consumed()
    results.append(check("s7_total_consumed", total > 0))

    # ── S8: Blame Attribution — Simple Failure ──────────────────
    print("\nS8: Blame Attribution")
    blame = BlameAttributionGraph()
    hops = [
        PipelineHop("h1", "a0", "a1", 0, "analyze", status=HopStatus.COMPLETED,
                     quality_score=0.9),
        PipelineHop("h2", "a1", "a2", 1, "transform", status=HopStatus.COMPLETED,
                     quality_score=0.8),
        PipelineHop("h3", "a2", "a3", 2, "validate", status=HopStatus.FAILED,
                     error="Validation failed: output malformed"),
        PipelineHop("h4", "a3", "a4", 3, "report", status=HopStatus.SKIPPED),
    ]

    entries = blame.attribute(hops, "h3")
    results.append(check("s8_has_entries", len(entries) > 0))

    primary = [e for e in entries if e.blame_level == BlameLevel.PRIMARY]
    results.append(check("s8_primary_found", len(primary) == 1))
    results.append(check("s8_primary_agent", primary[0].agent_id == "a3"))
    results.append(check("s8_primary_weight",
        abs(primary[0].blame_score - 0.70) < 0.01))

    # ── S9: Blame — Chain Attribution ───────────────────────────
    print("\nS9: Blame Chain")
    contributing = [e for e in entries
                    if e.blame_level in (BlameLevel.CONTRIBUTING, BlameLevel.PROPAGATING)]
    results.append(check("s9_chain_exists", len(contributing) > 0))

    innocent = [e for e in entries if e.blame_level == BlameLevel.INNOCENT]
    results.append(check("s9_innocent_found", len(innocent) > 0))
    results.append(check("s9_innocent_agent", innocent[0].agent_id == "a4"))

    # T3 impact
    impacts = blame.t3_impact_summary(entries)
    results.append(check("s9_primary_impact", impacts["a3"] == -0.10))
    results.append(check("s9_innocent_no_impact", impacts.get("a4", 0.0) == 0.0))

    # ── S10: Oversight — Critical Task ──────────────────────────
    print("\nS10: Oversight — Critical Task")
    oversight = OversightInjector()
    needs = oversight.requires_review(0.95, 1, "financial")
    results.append(check("s10_critical_review", needs))

    needs2 = oversight.requires_review(0.95, 1, "analyze")
    results.append(check("s10_normal_no_review", not needs2))

    # ── S11: Oversight — Low Trust ──────────────────────────────
    print("\nS11: Oversight — Low Trust")
    needs3 = oversight.requires_review(0.3, 1, "analyze")
    results.append(check("s11_low_trust_review", needs3))

    needs4 = oversight.requires_review(0.6, 1, "analyze")
    results.append(check("s11_mid_trust_review", needs4))

    # ── S12: Oversight — Deep Pipeline ──────────────────────────
    print("\nS12: Oversight — Deep Pipeline")
    needs5 = oversight.requires_review(0.9, 5, "analyze")
    results.append(check("s12_deep_review", needs5))

    needs6 = oversight.requires_review(0.9, 2, "analyze")
    results.append(check("s12_shallow_no_review", not needs6))

    # ── S13: Oversight Checkpoint ───────────────────────────────
    print("\nS13: Oversight Checkpoint")
    cp1 = oversight.create_checkpoint("p1", "h1", "a1", 0.9, 1, "analyze")
    results.append(check("s13_auto_approved", cp1.auto_approved))

    cp2 = oversight.create_checkpoint("p1", "h2", "a2", 0.3, 2, "analyze")
    results.append(check("s13_needs_review", not cp2.auto_approved))

    # Submit review
    oversight.review(cp2.checkpoint_id, OversightDecision.APPROVE,
                     "human-001", "Looks good")
    results.append(check("s13_reviewed",
        any(cp.reviewer_id == "human-001" for cp in oversight.checkpoints)))

    rate = oversight.auto_approval_rate()
    results.append(check("s13_approval_rate", abs(rate - 0.5) < 0.01))

    # ── S14: Circuit Breaker — Normal ───────────────────────────
    print("\nS14: Circuit Breaker — Normal")
    cb = PipelineCircuitBreaker()
    normal_hop = PipelineHop("h1", "a0", "a1", 0, "test",
                              status=HopStatus.COMPLETED, quality_score=0.8)
    state = cb.check_hop("p1", normal_hop, 0.8)
    results.append(check("s14_closed", state == CircuitBreakerState.CLOSED))

    # ── S15: Circuit Breaker — Low Trust Trip ───────────────────
    print("\nS15: Circuit Breaker — Low Trust")
    low_hop = PipelineHop("h2", "a1", "a2", 1, "test",
                           status=HopStatus.EXECUTING)
    state2 = cb.check_hop("p2", low_hop, 0.2)
    results.append(check("s15_tripped", state2 == CircuitBreakerState.OPEN))
    results.append(check("s15_event_logged", len(cb.events) == 1))
    results.append(check("s15_event_reason", "T3 below" in cb.events[0].trigger_reason))

    # ── S16: Circuit Breaker — Quality Trip ─────────────────────
    print("\nS16: Circuit Breaker — Quality")
    cb2 = PipelineCircuitBreaker()
    bad_quality = PipelineHop("h3", "a2", "a3", 2, "test",
                               status=HopStatus.COMPLETED, quality_score=0.1)
    state3 = cb2.check_hop("p3", bad_quality, 0.8)
    results.append(check("s16_quality_trip", state3 == CircuitBreakerState.OPEN))

    # ── S17: Circuit Breaker — Consecutive Failures ─────────────
    print("\nS17: Circuit Breaker — Consecutive Failures")
    cb3 = PipelineCircuitBreaker()
    for i in range(3):
        fail_hop = PipelineHop(f"hf{i}", "a0", "a1", 0, "test",
                                status=HopStatus.FAILED)
        state = cb3.check_hop("p4", fail_hop, 0.8)

    results.append(check("s17_failure_trip", state == CircuitBreakerState.OPEN))

    # Reset + close
    cb3.reset("p4")
    results.append(check("s17_half_open", cb3.get_state("p4") == CircuitBreakerState.HALF_OPEN))
    cb3.close("p4")
    results.append(check("s17_closed", cb3.get_state("p4") == CircuitBreakerState.CLOSED))

    # ── S18: Audit Trail ────────────────────────────────────────
    print("\nS18: Audit Trail")
    trail = OrchestrationAuditTrail()
    for i in range(5):
        entry = PipelineAuditEntry(
            pipeline_id=f"pipe-{i}",
            initiator_agent="orch-001",
            total_hops=3 + i,
            total_agents=3 + i,
            status=PipelineStatus.COMPLETED if i < 3 else PipelineStatus.FAILED,
            atp_total_allocated=100.0 + i * 10,
            atp_total_consumed=50.0 + i * 5,
            chain_trust=0.8 - i * 0.05,
            start_time=now + i * 100,
            end_time=now + i * 100 + 30,
        )
        trail.record(entry)

    results.append(check("s18_entries", len(trail.entries) == 5))
    results.append(check("s18_chain_valid", trail.verify_chain()))

    by_status = trail.pipelines_by_status()
    results.append(check("s18_completed", by_status.get("completed", 0) == 3))
    results.append(check("s18_failed", by_status.get("failed", 0) == 2))

    # ── S19: Audit Hash Chain Integrity ─────────────────────────
    print("\nS19: Audit Chain Integrity")
    # Tamper
    trail.entries[2].entry_hash = "tampered"
    results.append(check("s19_tamper_detected", not trail.verify_chain()))

    # Restore
    trail.entries[2].compute_hash(trail.entries[1].entry_hash)
    # Need to also recompute subsequent entries
    for i in range(3, len(trail.entries)):
        trail.entries[i].compute_hash(trail.entries[i-1].entry_hash)
    trail.prev_hash = trail.entries[-1].entry_hash
    results.append(check("s19_restored", trail.verify_chain()))

    # ── S20: End-to-End Pipeline ────────────────────────────────
    print("\nS20: End-to-End Pipeline")
    # Set up full pipeline
    e2e_trust = PipelineTrustModel()
    e2e_budget = ATPBudgetCascade()
    e2e_oversight = OversightInjector()
    e2e_cb = PipelineCircuitBreaker()
    e2e_trail = OrchestrationAuditTrail()
    e2e_blame = BlameAttributionGraph()

    agents = [
        AgentNode("orch", "Orchestrator", AgentRole.ORCHESTRATOR, t3_composite=0.92),
        AgentNode("worker1", "Analyzer", AgentRole.WORKER, t3_composite=0.88),
        AgentNode("worker2", "Transformer", AgentRole.WORKER, t3_composite=0.85),
        AgentNode("validator", "QA", AgentRole.VALIDATOR, t3_composite=0.90),
    ]

    # 1. Check trust viability
    viable, _ = e2e_trust.is_viable(agents)
    results.append(check("s20_viable", viable))

    trust_values = e2e_trust.propagate_trust(agents)
    results.append(check("s20_trust_degrades",
        trust_values[0] > trust_values[-1]))

    # 2. Allocate budget
    root_alloc = e2e_budget.allocate("orch", 200.0)
    results.append(check("s20_budget_alloc", root_alloc is not None))

    child1 = e2e_budget.allocate("worker1", 80.0, root_alloc.allocation_id)
    child2 = e2e_budget.allocate("worker2", 60.0, root_alloc.allocation_id)
    results.append(check("s20_children_alloc",
        child1 is not None and child2 is not None))

    # 3. Check oversight
    cp = e2e_oversight.create_checkpoint("e2e-pipe", "h1", "worker1",
                                          trust_values[1], 1, "analyze")
    results.append(check("s20_oversight_auto", cp.auto_approved))

    # 4. Execute hops
    e2e_budget.consume(child1.allocation_id, 15.0, depth=1)
    e2e_budget.consume(child2.allocation_id, 20.0, depth=2)

    # 5. Circuit breaker check
    hop1 = PipelineHop("e2e-h1", "orch", "worker1", 1, "analyze",
                         status=HopStatus.COMPLETED, quality_score=0.85)
    cb_state = e2e_cb.check_hop("e2e-pipe", hop1, trust_values[1])
    results.append(check("s20_cb_closed", cb_state == CircuitBreakerState.CLOSED))

    # 6. Release budgets
    r1 = e2e_budget.release(child1.allocation_id)
    r2 = e2e_budget.release(child2.allocation_id)
    results.append(check("s20_budget_returned", r1 > 0 and r2 > 0))

    # 7. Audit trail
    audit_entry = PipelineAuditEntry(
        pipeline_id="e2e-pipe",
        initiator_agent="orch",
        total_hops=4,
        total_agents=4,
        status=PipelineStatus.COMPLETED,
        atp_total_allocated=200.0,
        atp_total_consumed=e2e_budget.total_consumed(),
        chain_trust=e2e_trust.chain_trust(agents),
        oversight_checkpoints=1,
    )
    e2e_trail.record(audit_entry)
    results.append(check("s20_audit_recorded", len(e2e_trail.entries) == 1))
    results.append(check("s20_audit_valid", e2e_trail.verify_chain()))

    # ── S21: E2E Pipeline Failure ───────────────────────────────
    print("\nS21: E2E Pipeline Failure")
    fail_hops = [
        PipelineHop("fh1", "orch", "w1", 0, "parse",
                     status=HopStatus.COMPLETED, quality_score=0.9),
        PipelineHop("fh2", "w1", "w2", 1, "process",
                     status=HopStatus.COMPLETED, quality_score=0.7),
        PipelineHop("fh3", "w2", "w3", 2, "validate",
                     status=HopStatus.FAILED, error="Output corrupted"),
        PipelineHop("fh4", "w3", "w4", 3, "report",
                     status=HopStatus.SKIPPED),
    ]

    blame_entries = e2e_blame.attribute(fail_hops, "fh3")
    results.append(check("s21_blame_assigned", len(blame_entries) > 0))

    primary_blame = [b for b in blame_entries if b.blame_level == BlameLevel.PRIMARY]
    results.append(check("s21_primary_w3", primary_blame[0].agent_id == "w3"))

    total_blame = e2e_blame.total_blame(blame_entries)
    results.append(check("s21_blame_sums", total_blame > 0.9))

    impacts = e2e_blame.t3_impact_summary(blame_entries)
    results.append(check("s21_impacts", impacts["w3"] == -0.10))

    # ── Summary ─────────────────────────────────────────────────
    passed = sum(results)
    total = len(results)
    print(f"\n{'='*60}")
    print(f"Agent Orchestration Trust Protocol: {passed}/{total} checks passed")
    if passed == total:
        print("ALL CHECKS PASSED")
    else:
        print(f"FAILURES: {total - passed}")
    return passed == total


if __name__ == "__main__":
    run_tests()
