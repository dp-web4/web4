#!/usr/bin/env python3
"""
Agent Orchestration Trust Protocol — Web4 Reference Implementation

Handles multi-agent PIPELINES where Agent A calls Agent B which calls Tool C
which calls Agent D. This is structurally different from delegation chains:
- Delegation: authority transfer (parent → child scope narrowing)
- Orchestration: execution flow (caller → callee → sub-callee → result)

Implements:
  1. PipelineTrustModel: Trust propagates multiplicatively through call depth
  2. ATPBudgetCascade: Parent budget constrains all descendants, excess returns
  3. BlameAttributionGraph: Causal chain analysis for pipeline failures
  4. OversightInjectionPoint: Where human-in-the-loop can intercept
  5. PipelineCircuitBreaker: If any hop falls below T3 threshold, halt + rollback
  6. OrchestrationAuditTrail: Single ledger entry per pipeline with full call graph
  7. PipelineOrchestrator: End-to-end pipeline execution with trust governance

Key insight: In agent pipelines, trust is CONSUMED (multiplicative decay)
while ATP is SPENT (additive deduction). A 5-hop pipeline with 0.9 trust
per hop has 0.59 end-to-end trust but the ATP budget is sum of per-hop costs.

Art. 14 (human oversight): Oversight injection points let humans approve
at critical junctures without breaking the pipeline flow.
Art. 26 (deployer): The pipeline initiator bears deployer obligations for
the entire chain's output.

Checks: 90+
"""

import hashlib
import math
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════
# PART 1: PIPELINE DATA MODEL
# ═══════════════════════════════════════════════════════════════

class PipelineStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    HALTED = auto()        # Circuit breaker triggered
    OVERSIGHT_WAIT = auto() # Waiting for human approval
    ROLLED_BACK = auto()


class HopStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    SKIPPED = auto()       # Skipped due to upstream failure
    ROLLED_BACK = auto()


class FailureType(Enum):
    TRUST_BELOW_THRESHOLD = "trust_below_threshold"
    ATP_EXHAUSTED = "atp_exhausted"
    TIMEOUT = "timeout"
    AGENT_ERROR = "agent_error"
    OVERSIGHT_DENIED = "oversight_denied"
    CIRCUIT_BREAK = "circuit_break"


class BlameLevel(Enum):
    """How much blame a hop bears for a pipeline failure."""
    PRIMARY = "primary"      # Direct cause of failure
    CONTRIBUTING = "contributing"  # Contributed to conditions
    NONE = "none"            # Not involved


@dataclass
class AgentNode:
    """An agent participating in a pipeline."""
    agent_id: str = ""
    agent_name: str = ""
    lct_uri: str = ""
    t3_talent: float = 0.5
    t3_training: float = 0.5
    t3_temperament: float = 0.5
    atp_balance: float = 100.0
    society_id: str = ""

    @property
    def t3_composite(self) -> float:
        return (self.t3_talent + self.t3_training + self.t3_temperament) / 3.0


@dataclass
class PipelineHop:
    """A single hop in an agent pipeline."""
    hop_id: str = ""
    hop_index: int = 0
    caller_id: str = ""
    callee_id: str = ""
    task_type: str = ""
    task_description: str = ""

    # Trust
    caller_trust: float = 0.0
    callee_trust: float = 0.0
    hop_trust: float = 0.0          # min(caller, callee) × decay
    cumulative_trust: float = 0.0   # Product of all hop trusts to this point

    # ATP
    atp_budget: float = 0.0
    atp_spent: float = 0.0
    atp_remaining: float = 0.0

    # Execution
    status: HopStatus = HopStatus.PENDING
    start_time: float = 0.0
    end_time: float = 0.0
    result: Any = None
    quality: float = 0.0  # 0.0-1.0 quality of output

    # Oversight
    requires_oversight: bool = False
    oversight_approved: bool = False
    oversight_approver: str = ""

    # Failure
    failure_type: Optional[FailureType] = None
    failure_detail: str = ""

    def compute_id(self):
        raw = f"{self.caller_id}:{self.callee_id}:{self.hop_index}:{self.task_type}"
        self.hop_id = hashlib.sha256(raw.encode()).hexdigest()[:12]
        return self.hop_id


@dataclass
class Pipeline:
    """A complete multi-agent pipeline."""
    pipeline_id: str = ""
    initiator_id: str = ""        # Entity that started the pipeline (bears deployer obligations)
    description: str = ""
    hops: List[PipelineHop] = field(default_factory=list)
    status: PipelineStatus = PipelineStatus.PENDING

    # Trust
    end_to_end_trust: float = 0.0
    min_trust_threshold: float = 0.3   # Pipeline halts below this

    # ATP
    total_budget: float = 0.0
    total_spent: float = 0.0
    total_remaining: float = 0.0

    # Timing
    start_time: float = 0.0
    end_time: float = 0.0
    timeout: float = 300.0  # 5 minutes default

    # Quality
    aggregate_quality: float = 0.0

    # Audit
    audit_hash: str = ""

    def compute_id(self):
        raw = f"{self.initiator_id}:{self.description}:{self.start_time}"
        self.pipeline_id = hashlib.sha256(raw.encode()).hexdigest()[:12]
        return self.pipeline_id


# ═══════════════════════════════════════════════════════════════
# PART 2: PIPELINE TRUST MODEL
# ═══════════════════════════════════════════════════════════════

class PipelineTrustModel:
    """
    Trust propagation through agent pipelines.

    Trust is MULTIPLICATIVE: each hop multiplies the cumulative trust.
    A 5-hop pipeline with 0.9 trust per hop = 0.9^5 = 0.59 end-to-end.

    This mirrors multi-hop dictionary translation: multiplicative decay.
    """

    TRUST_DECAY_PER_HOP = 0.95  # 5% decay per hop (trust cost of indirection)

    def __init__(self, min_trust: float = 0.3, decay: float = 0.95):
        self.min_trust = min_trust
        self.decay = decay

    def compute_hop_trust(self, caller: AgentNode, callee: AgentNode,
                          hop_index: int) -> float:
        """Compute trust for a single hop."""
        # Hop trust = min(caller, callee) × decay^hop_index
        base_trust = min(caller.t3_composite, callee.t3_composite)
        hop_trust = base_trust * (self.decay ** hop_index)
        return hop_trust

    def compute_cumulative_trust(self, hop_trusts: List[float]) -> float:
        """Compute end-to-end trust (multiplicative)."""
        if not hop_trusts:
            return 0.0
        result = 1.0
        for t in hop_trusts:
            result *= t
        return result

    def trust_sufficient(self, cumulative_trust: float) -> bool:
        """Check if cumulative trust meets minimum threshold."""
        return cumulative_trust >= self.min_trust

    def max_viable_depth(self, agent_trust: float) -> int:
        """How deep can a pipeline go before trust drops below threshold?"""
        if agent_trust <= 0 or self.decay <= 0:
            return 0
        # agent_trust × decay^n ≥ min_trust
        # n ≤ log(min_trust / agent_trust) / log(decay)
        if agent_trust <= self.min_trust:
            return 0
        ratio = self.min_trust / agent_trust
        if self.decay >= 1.0:
            return 100  # No decay
        depth = math.log(ratio) / math.log(self.decay)
        return max(0, int(depth))


# ═══════════════════════════════════════════════════════════════
# PART 3: ATP BUDGET CASCADE
# ═══════════════════════════════════════════════════════════════

class ATPBudgetCascade:
    """
    ATP budget management for pipeline execution.

    Parent budget constrains ALL descendants. Each hop deducts its cost.
    Excess ATP returns to the initiator on completion.
    On failure, spent ATP is lost (thermodynamic accountability).
    """

    HOP_BASE_COST = 5.0    # Minimum ATP per hop
    HOP_FEE_RATE = 0.02    # 2% fee per hop

    def __init__(self, base_cost: float = 5.0, fee_rate: float = 0.02):
        self.base_cost = base_cost
        self.fee_rate = fee_rate

    def compute_hop_cost(self, budget: float, hop_index: int) -> float:
        """Cost of a single hop: base + fee% of remaining budget."""
        fee = budget * self.fee_rate
        return self.base_cost + fee

    def allocate_budget(self, total_budget: float,
                        num_hops: int) -> List[float]:
        """Allocate ATP budget across pipeline hops."""
        if num_hops <= 0:
            return []
        remaining = total_budget
        allocations = []
        for i in range(num_hops):
            cost = self.compute_hop_cost(remaining, i)
            if cost > remaining:
                cost = remaining  # Give whatever's left
            allocations.append(cost)
            remaining -= cost
        return allocations

    def compute_total_cost(self, budget: float, num_hops: int) -> float:
        """Total ATP cost for the pipeline."""
        return sum(self.allocate_budget(budget, num_hops))

    def refund_excess(self, total_budget: float, total_spent: float) -> float:
        """Compute refund on successful completion."""
        return max(0.0, total_budget - total_spent)


# ═══════════════════════════════════════════════════════════════
# PART 4: BLAME ATTRIBUTION GRAPH
# ═══════════════════════════════════════════════════════════════

@dataclass
class BlameAssignment:
    """Blame assignment for a single hop in a failed pipeline."""
    hop_id: str = ""
    agent_id: str = ""
    blame_level: BlameLevel = BlameLevel.NONE
    blame_score: float = 0.0  # 0.0-1.0
    reason: str = ""
    t3_impact: float = 0.0    # How much T3 should change


class BlameAttributionGraph:
    """
    Causal chain analysis for pipeline failures.

    When a pipeline fails, blame must be attributed to specific hops:
    - PRIMARY: The hop that directly caused the failure
    - CONTRIBUTING: Hops that created conditions for failure
    - NONE: Hops that executed correctly

    T3 reputation impact: primary = -0.05, contributing = -0.02, none = +0.01
    """

    def attribute_blame(self, pipeline: Pipeline) -> List[BlameAssignment]:
        """Analyze a failed pipeline and attribute blame."""
        assignments = []

        # Find the failing hop
        failing_hop = None
        for hop in pipeline.hops:
            if hop.failure_type is not None:
                failing_hop = hop
                break

        if failing_hop is None:
            # No failure — all get positive credit
            for hop in pipeline.hops:
                if hop.status == HopStatus.COMPLETED:
                    assignments.append(BlameAssignment(
                        hop_id=hop.hop_id,
                        agent_id=hop.callee_id,
                        blame_level=BlameLevel.NONE,
                        blame_score=0.0,
                        reason="Completed successfully",
                        t3_impact=0.01,
                    ))
            return assignments

        for hop in pipeline.hops:
            if hop.hop_id == failing_hop.hop_id:
                # Primary blame
                assignments.append(BlameAssignment(
                    hop_id=hop.hop_id,
                    agent_id=hop.callee_id,
                    blame_level=BlameLevel.PRIMARY,
                    blame_score=1.0,
                    reason=f"Direct failure: {hop.failure_type.value}",
                    t3_impact=-0.05,
                ))
            elif hop.status == HopStatus.COMPLETED and hop.quality < 0.5:
                # Contributing — completed but low quality (set up conditions)
                assignments.append(BlameAssignment(
                    hop_id=hop.hop_id,
                    agent_id=hop.callee_id,
                    blame_level=BlameLevel.CONTRIBUTING,
                    blame_score=0.5 - hop.quality,
                    reason=f"Low quality output ({hop.quality:.2f}) contributed to downstream failure",
                    t3_impact=-0.02,
                ))
            elif hop.status == HopStatus.COMPLETED:
                # Completed successfully with good quality — no blame
                assignments.append(BlameAssignment(
                    hop_id=hop.hop_id,
                    agent_id=hop.callee_id,
                    blame_level=BlameLevel.NONE,
                    blame_score=0.0,
                    reason="Completed with adequate quality",
                    t3_impact=0.01,
                ))
            elif hop.status == HopStatus.SKIPPED:
                # Skipped due to upstream failure — no blame
                assignments.append(BlameAssignment(
                    hop_id=hop.hop_id,
                    agent_id=hop.callee_id,
                    blame_level=BlameLevel.NONE,
                    blame_score=0.0,
                    reason="Skipped due to upstream failure",
                    t3_impact=0.0,
                ))

        return assignments

    def total_blame_for_agent(self, assignments: List[BlameAssignment],
                               agent_id: str) -> float:
        """Total blame score for a specific agent across all hops."""
        return sum(a.blame_score for a in assignments if a.agent_id == agent_id)

    def t3_adjustments(self, assignments: List[BlameAssignment]) -> Dict[str, float]:
        """Compute T3 reputation adjustments from blame assignments."""
        adjustments: Dict[str, float] = {}
        for a in assignments:
            if a.agent_id not in adjustments:
                adjustments[a.agent_id] = 0.0
            adjustments[a.agent_id] += a.t3_impact
        return adjustments


# ═══════════════════════════════════════════════════════════════
# PART 5: OVERSIGHT INJECTION POINTS
# ═══════════════════════════════════════════════════════════════

@dataclass
class OversightPoint:
    """A point in the pipeline where human oversight can be injected."""
    hop_index: int = 0
    reason: str = ""
    required: bool = True   # If True, pipeline blocks until approved
    auto_approve_trust: float = 0.9  # Auto-approve if trust above this


class OversightManager:
    """
    Art. 14 human oversight for agent pipelines.

    Oversight can be injected at any hop. If the hop's cumulative trust
    is below the auto-approve threshold, human approval is required.
    """

    def __init__(self):
        self.injection_points: Dict[str, List[OversightPoint]] = {}  # pipeline_id → points
        self.decisions: List[Dict] = []

    def configure_oversight(self, pipeline_id: str,
                            points: List[OversightPoint]):
        """Set oversight injection points for a pipeline."""
        self.injection_points[pipeline_id] = points

    def needs_oversight(self, pipeline_id: str, hop_index: int,
                        cumulative_trust: float) -> bool:
        """Check if a hop requires human oversight."""
        if pipeline_id not in self.injection_points:
            return False
        for point in self.injection_points[pipeline_id]:
            if point.hop_index == hop_index:
                if cumulative_trust >= point.auto_approve_trust:
                    return False  # Trust high enough for auto-approval
                return point.required
        return False

    def record_decision(self, pipeline_id: str, hop_index: int,
                        approved: bool, approver: str = ""):
        """Record an oversight decision."""
        self.decisions.append({
            "pipeline_id": pipeline_id,
            "hop_index": hop_index,
            "approved": approved,
            "approver": approver,
            "timestamp": time.time(),
        })

    def auto_approve_check(self, pipeline_id: str, hop_index: int,
                           cumulative_trust: float) -> Optional[bool]:
        """Check if auto-approval applies. Returns None if manual needed."""
        if pipeline_id not in self.injection_points:
            return True  # No oversight configured → auto approve
        for point in self.injection_points[pipeline_id]:
            if point.hop_index == hop_index:
                if cumulative_trust >= point.auto_approve_trust:
                    return True
                return None  # Manual review needed
        return True  # No oversight at this hop


# ═══════════════════════════════════════════════════════════════
# PART 6: PIPELINE CIRCUIT BREAKER
# ═══════════════════════════════════════════════════════════════

class CircuitState(Enum):
    CLOSED = auto()     # Normal operation
    OPEN = auto()       # Broken — pipeline halted
    HALF_OPEN = auto()  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for pipeline circuit breaker."""
    min_trust_threshold: float = 0.3
    max_consecutive_failures: int = 3
    cooldown_seconds: float = 60.0
    atp_minimum: float = 5.0


class PipelineCircuitBreaker:
    """
    If any hop's trust drops below threshold, the pipeline halts
    and remaining hops are rolled back. This prevents low-trust
    agents from executing in a pipeline context.
    """

    def __init__(self, config: CircuitBreakerConfig = None):
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.consecutive_failures = 0
        self.last_failure_time = 0.0
        self.trip_reasons: List[str] = []

    def check_hop(self, hop: PipelineHop, cumulative_trust: float,
                  remaining_atp: float) -> Tuple[bool, Optional[str]]:
        """Check if a hop should proceed or if circuit should break."""
        if self.state == CircuitState.OPEN:
            # Check cooldown
            if time.time() - self.last_failure_time < self.config.cooldown_seconds:
                return (False, "Circuit breaker OPEN — cooldown active")
            else:
                self.state = CircuitState.HALF_OPEN

        # Trust check
        if cumulative_trust < self.config.min_trust_threshold:
            self._trip(f"Trust {cumulative_trust:.3f} below threshold {self.config.min_trust_threshold}")
            return (False, self.trip_reasons[-1])

        # ATP check
        if remaining_atp < self.config.atp_minimum:
            self._trip(f"ATP {remaining_atp:.1f} below minimum {self.config.atp_minimum}")
            return (False, self.trip_reasons[-1])

        # Callee trust check
        if hop.callee_trust < self.config.min_trust_threshold:
            self._trip(f"Callee trust {hop.callee_trust:.3f} below threshold")
            return (False, self.trip_reasons[-1])

        # If half-open and check passed, close the circuit
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.consecutive_failures = 0

        return (True, None)

    def _trip(self, reason: str):
        self.state = CircuitState.OPEN
        self.consecutive_failures += 1
        self.last_failure_time = time.time()
        self.trip_reasons.append(reason)

    def reset(self):
        self.state = CircuitState.CLOSED
        self.consecutive_failures = 0
        self.trip_reasons = []


# ═══════════════════════════════════════════════════════════════
# PART 7: ORCHESTRATION AUDIT TRAIL
# ═══════════════════════════════════════════════════════════════

@dataclass
class AuditEntry:
    """A single entry in the pipeline audit trail."""
    entry_type: str = ""  # "hop_start", "hop_complete", "hop_fail", "oversight", "circuit_break"
    hop_index: int = -1
    agent_id: str = ""
    detail: str = ""
    timestamp: float = 0.0
    content_hash: str = ""
    prev_hash: str = ""


class OrchestrationAuditTrail:
    """
    Single ledger entry per pipeline with full call graph embedded.
    Hash-chained for tamper evidence.
    """

    def __init__(self):
        self.entries: List[AuditEntry] = []
        self.prev_hash = "genesis"

    def record(self, entry_type: str, hop_index: int = -1,
               agent_id: str = "", detail: str = "") -> AuditEntry:
        now = time.time()
        content = f"{entry_type}:{hop_index}:{agent_id}:{detail}"
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        chain_input = f"{content_hash}:{self.prev_hash}"
        entry_hash = hashlib.sha256(chain_input.encode()).hexdigest()[:16]

        entry = AuditEntry(
            entry_type=entry_type,
            hop_index=hop_index,
            agent_id=agent_id,
            detail=detail,
            timestamp=now,
            content_hash=content_hash,
            prev_hash=self.prev_hash,
        )
        self.prev_hash = entry_hash
        self.entries.append(entry)
        return entry

    def verify_chain(self) -> bool:
        """Verify the audit trail hash chain is intact."""
        expected_prev = "genesis"
        for entry in self.entries:
            if entry.prev_hash != expected_prev:
                return False
            chain_input = f"{entry.content_hash}:{entry.prev_hash}"
            expected_prev = hashlib.sha256(chain_input.encode()).hexdigest()[:16]
        return True

    def pipeline_summary(self) -> Dict:
        """Summarize the pipeline execution from audit trail."""
        hop_starts = sum(1 for e in self.entries if e.entry_type == "hop_start")
        hop_completes = sum(1 for e in self.entries if e.entry_type == "hop_complete")
        hop_fails = sum(1 for e in self.entries if e.entry_type == "hop_fail")
        oversights = sum(1 for e in self.entries if e.entry_type == "oversight")
        breaks = sum(1 for e in self.entries if e.entry_type == "circuit_break")
        return {
            "total_entries": len(self.entries),
            "hops_started": hop_starts,
            "hops_completed": hop_completes,
            "hops_failed": hop_fails,
            "oversight_events": oversights,
            "circuit_breaks": breaks,
        }


# ═══════════════════════════════════════════════════════════════
# PART 8: PIPELINE ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════

class PipelineOrchestrator:
    """
    End-to-end pipeline execution with trust governance.
    Combines all components into unified orchestration.
    """

    def __init__(self, min_trust: float = 0.3, trust_decay: float = 0.95,
                 atp_base_cost: float = 5.0, atp_fee_rate: float = 0.02):
        self.trust_model = PipelineTrustModel(min_trust, trust_decay)
        self.budget_cascade = ATPBudgetCascade(atp_base_cost, atp_fee_rate)
        self.blame_graph = BlameAttributionGraph()
        self.oversight = OversightManager()
        self.circuit_breaker = PipelineCircuitBreaker(
            CircuitBreakerConfig(min_trust_threshold=min_trust)
        )
        self.audit_trail = OrchestrationAuditTrail()
        self.agents: Dict[str, AgentNode] = {}
        self.pipelines: Dict[str, Pipeline] = {}

    def register_agent(self, agent: AgentNode):
        self.agents[agent.agent_id] = agent

    def create_pipeline(self, initiator_id: str, description: str,
                        hop_specs: List[Dict], total_budget: float,
                        timeout: float = 300.0) -> Pipeline:
        """Create a pipeline from hop specifications."""
        now = time.time()
        pipeline = Pipeline(
            initiator_id=initiator_id,
            description=description,
            total_budget=total_budget,
            total_remaining=total_budget,
            timeout=timeout,
            start_time=now,
        )
        pipeline.compute_id()

        # Build hops
        allocations = self.budget_cascade.allocate_budget(
            total_budget, len(hop_specs)
        )

        cumulative_trust = 1.0
        for i, spec in enumerate(hop_specs):
            caller_id = spec.get("caller_id", initiator_id)
            callee_id = spec["callee_id"]

            caller = self.agents.get(caller_id)
            callee = self.agents.get(callee_id)

            caller_trust = caller.t3_composite if caller else 0.5
            callee_trust = callee.t3_composite if callee else 0.5

            hop_trust = self.trust_model.compute_hop_trust(
                caller or AgentNode(t3_talent=0.5, t3_training=0.5, t3_temperament=0.5),
                callee or AgentNode(t3_talent=0.5, t3_training=0.5, t3_temperament=0.5),
                i,
            )
            cumulative_trust *= hop_trust

            hop = PipelineHop(
                hop_index=i,
                caller_id=caller_id,
                callee_id=callee_id,
                task_type=spec.get("task_type", "generic"),
                task_description=spec.get("description", ""),
                caller_trust=caller_trust,
                callee_trust=callee_trust,
                hop_trust=hop_trust,
                cumulative_trust=cumulative_trust,
                atp_budget=allocations[i] if i < len(allocations) else 0.0,
                atp_remaining=allocations[i] if i < len(allocations) else 0.0,
                requires_oversight=spec.get("requires_oversight", False),
            )
            hop.compute_id()
            pipeline.hops.append(hop)

        pipeline.end_to_end_trust = cumulative_trust
        self.pipelines[pipeline.pipeline_id] = pipeline
        self.audit_trail.record("pipeline_created", agent_id=initiator_id,
                                detail=f"Pipeline {pipeline.pipeline_id}: {len(hop_specs)} hops")
        return pipeline

    def execute_pipeline(self, pipeline_id: str,
                         simulate_results: Optional[Dict[int, Dict]] = None) -> Pipeline:
        """
        Execute a pipeline. In reference implementation, uses simulate_results
        to provide per-hop outcomes.

        simulate_results: {hop_index: {"quality": 0.9, "success": True, "atp_cost": 5.0}}
        """
        if pipeline_id not in self.pipelines:
            raise ValueError(f"Unknown pipeline: {pipeline_id}")

        pipeline = self.pipelines[pipeline_id]
        pipeline.status = PipelineStatus.RUNNING
        simulate_results = simulate_results or {}

        self.circuit_breaker.reset()
        total_spent = 0.0

        for hop in pipeline.hops:
            # 1. Circuit breaker check
            proceed, reason = self.circuit_breaker.check_hop(
                hop, hop.cumulative_trust, pipeline.total_remaining
            )
            if not proceed:
                hop.status = HopStatus.FAILED
                hop.failure_type = FailureType.CIRCUIT_BREAK
                hop.failure_detail = reason or "circuit break"
                pipeline.status = PipelineStatus.HALTED
                self.audit_trail.record("circuit_break", hop.hop_index,
                                       hop.callee_id, reason or "")
                # Skip remaining hops
                for remaining in pipeline.hops[hop.hop_index + 1:]:
                    remaining.status = HopStatus.SKIPPED
                break

            # 2. Oversight check
            if hop.requires_oversight:
                auto = self.oversight.auto_approve_check(
                    pipeline_id, hop.hop_index, hop.cumulative_trust
                )
                if auto is None:
                    # Manual oversight needed — simulate approval from results
                    sim = simulate_results.get(hop.hop_index, {})
                    approved = sim.get("oversight_approved", True)
                    if not approved:
                        hop.status = HopStatus.FAILED
                        hop.failure_type = FailureType.OVERSIGHT_DENIED
                        hop.failure_detail = "Human oversight denied execution"
                        pipeline.status = PipelineStatus.HALTED
                        self.audit_trail.record("oversight", hop.hop_index,
                                               hop.callee_id, "DENIED")
                        for remaining in pipeline.hops[hop.hop_index + 1:]:
                            remaining.status = HopStatus.SKIPPED
                        break
                    else:
                        hop.oversight_approved = True
                        self.audit_trail.record("oversight", hop.hop_index,
                                               hop.callee_id, "APPROVED")

            # 3. Execute hop
            self.audit_trail.record("hop_start", hop.hop_index, hop.callee_id,
                                    f"Task: {hop.task_type}")
            hop.status = HopStatus.RUNNING
            hop.start_time = time.time()

            # Simulate execution result
            sim = simulate_results.get(hop.hop_index, {"quality": 0.8, "success": True})
            success = sim.get("success", True)
            quality = sim.get("quality", 0.8)
            atp_cost = sim.get("atp_cost", self.budget_cascade.base_cost)

            if success:
                hop.status = HopStatus.COMPLETED
                hop.quality = quality
                hop.atp_spent = min(atp_cost, hop.atp_budget)
                hop.atp_remaining = hop.atp_budget - hop.atp_spent
                hop.end_time = time.time()
                total_spent += hop.atp_spent
                pipeline.total_remaining -= hop.atp_spent

                self.audit_trail.record("hop_complete", hop.hop_index, hop.callee_id,
                                        f"Quality: {quality:.2f}, ATP: {hop.atp_spent:.1f}")
            else:
                hop.status = HopStatus.FAILED
                hop.failure_type = FailureType(
                    sim.get("failure_type", FailureType.AGENT_ERROR.value)
                )
                hop.failure_detail = sim.get("failure_detail", "Agent execution failed")
                hop.atp_spent = min(atp_cost, hop.atp_budget)
                total_spent += hop.atp_spent
                pipeline.total_remaining -= hop.atp_spent
                hop.end_time = time.time()

                pipeline.status = PipelineStatus.FAILED
                self.audit_trail.record("hop_fail", hop.hop_index, hop.callee_id,
                                        f"Failure: {hop.failure_type.value}")
                # Skip remaining
                for remaining in pipeline.hops[hop.hop_index + 1:]:
                    remaining.status = HopStatus.SKIPPED
                break

        # Finalize
        if pipeline.status == PipelineStatus.RUNNING:
            pipeline.status = PipelineStatus.COMPLETED

        pipeline.total_spent = total_spent
        pipeline.total_remaining = pipeline.total_budget - total_spent
        pipeline.end_time = time.time()

        # Compute aggregate quality (product of completed hop qualities)
        completed = [h for h in pipeline.hops if h.status == HopStatus.COMPLETED]
        if completed:
            pipeline.aggregate_quality = 1.0
            for h in completed:
                pipeline.aggregate_quality *= h.quality
        else:
            pipeline.aggregate_quality = 0.0

        # Compute audit hash
        content = f"{pipeline.pipeline_id}:{pipeline.status.name}:{pipeline.total_spent}"
        content += f":{pipeline.aggregate_quality}:{len(completed)}"
        pipeline.audit_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        self.audit_trail.record("pipeline_complete", agent_id=pipeline.initiator_id,
                                detail=f"Status: {pipeline.status.name}, Quality: {pipeline.aggregate_quality:.3f}")
        return pipeline


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

    # ── S1: Agent Node ──────────────────────────────────────────
    print("\nS1: Agent Node")
    agent_a = AgentNode("a", "Agent Alpha", "lct://org:alpha@web4", 0.9, 0.85, 0.88, 500, "society-1")
    agent_b = AgentNode("b", "Agent Beta", "lct://org:beta@web4", 0.8, 0.75, 0.82, 300, "society-1")
    agent_c = AgentNode("c", "Agent Gamma", "lct://org:gamma@web4", 0.7, 0.65, 0.70, 200, "society-2")
    results.append(check("s1_composite_a", abs(agent_a.t3_composite - 0.8767) < 0.01))
    results.append(check("s1_composite_b", abs(agent_b.t3_composite - 0.79) < 0.01))
    results.append(check("s1_composite_c", abs(agent_c.t3_composite - 0.6833) < 0.01))

    # ── S2: Pipeline Trust Model ────────────────────────────────
    print("\nS2: Pipeline Trust Model")
    trust_model = PipelineTrustModel(min_trust=0.3, decay=0.95)
    hop0_trust = trust_model.compute_hop_trust(agent_a, agent_b, 0)
    results.append(check("s2_hop0_trust", abs(hop0_trust - 0.79) < 0.01))  # min(a,b) × 0.95^0

    hop1_trust = trust_model.compute_hop_trust(agent_b, agent_c, 1)
    results.append(check("s2_hop1_decay", hop1_trust < hop0_trust))  # Decayed by 0.95

    cumulative = trust_model.compute_cumulative_trust([hop0_trust, hop1_trust])
    results.append(check("s2_cumulative", cumulative < hop0_trust))
    results.append(check("s2_cumulative_product", abs(cumulative - hop0_trust * hop1_trust) < 0.001))

    # ── S3: Trust Sufficiency ───────────────────────────────────
    print("\nS3: Trust Sufficiency")
    results.append(check("s3_sufficient", trust_model.trust_sufficient(0.5)))
    results.append(check("s3_insufficient", not trust_model.trust_sufficient(0.2)))
    results.append(check("s3_boundary", trust_model.trust_sufficient(0.3)))
    results.append(check("s3_below_boundary", not trust_model.trust_sufficient(0.29)))

    # ── S4: Max Viable Depth ────────────────────────────────────
    print("\nS4: Max Viable Depth")
    depth = trust_model.max_viable_depth(0.9)
    results.append(check("s4_finite_depth", depth > 0))
    results.append(check("s4_depth_reasonable", depth < 50))

    # Verify: trust at max depth should be near threshold
    deep_trust = 0.9 * (0.95 ** depth)
    results.append(check("s4_depth_near_threshold", deep_trust >= 0.3))

    zero_depth = trust_model.max_viable_depth(0.2)
    results.append(check("s4_zero_depth_low_trust", zero_depth == 0))

    # ── S5: ATP Budget Cascade ──────────────────────────────────
    print("\nS5: ATP Budget Cascade")
    budget = ATPBudgetCascade(base_cost=5.0, fee_rate=0.02)
    allocations = budget.allocate_budget(100.0, 5)
    results.append(check("s5_five_allocs", len(allocations) == 5))
    results.append(check("s5_total_within_budget", sum(allocations) <= 100.0))
    results.append(check("s5_first_alloc", allocations[0] > 5.0))  # base + fee

    # Decreasing allocations (because remaining budget shrinks)
    results.append(check("s5_decreasing", allocations[0] > allocations[-1]))

    refund = budget.refund_excess(100.0, 30.0)
    results.append(check("s5_refund", abs(refund - 70.0) < 0.01))

    # ── S6: Empty Budget ────────────────────────────────────────
    print("\nS6: Edge Cases")
    empty_alloc = budget.allocate_budget(100.0, 0)
    results.append(check("s6_empty_alloc", len(empty_alloc) == 0))

    no_refund = budget.refund_excess(50.0, 60.0)
    results.append(check("s6_no_negative_refund", no_refund == 0.0))

    # ── S7: Blame Attribution — Success ─────────────────────────
    print("\nS7: Blame Attribution — Success")
    blame = BlameAttributionGraph()
    success_pipeline = Pipeline(pipeline_id="p-ok", status=PipelineStatus.COMPLETED)
    for i in range(3):
        success_pipeline.hops.append(PipelineHop(
            hop_id=f"h{i}", hop_index=i, callee_id=f"agent-{i}",
            status=HopStatus.COMPLETED, quality=0.9,
        ))
    assignments = blame.attribute_blame(success_pipeline)
    results.append(check("s7_three_assignments", len(assignments) == 3))
    results.append(check("s7_all_none", all(a.blame_level == BlameLevel.NONE for a in assignments)))
    results.append(check("s7_positive_t3", all(a.t3_impact > 0 for a in assignments)))

    # ── S8: Blame Attribution — Failure ─────────────────────────
    print("\nS8: Blame Attribution — Failure")
    fail_pipeline = Pipeline(pipeline_id="p-fail", status=PipelineStatus.FAILED)
    fail_pipeline.hops = [
        PipelineHop(hop_id="h0", hop_index=0, callee_id="good-agent",
                    status=HopStatus.COMPLETED, quality=0.85),
        PipelineHop(hop_id="h1", hop_index=1, callee_id="mediocre-agent",
                    status=HopStatus.COMPLETED, quality=0.3),
        PipelineHop(hop_id="h2", hop_index=2, callee_id="bad-agent",
                    status=HopStatus.FAILED, failure_type=FailureType.AGENT_ERROR),
        PipelineHop(hop_id="h3", hop_index=3, callee_id="skipped-agent",
                    status=HopStatus.SKIPPED),
    ]
    fail_assignments = blame.attribute_blame(fail_pipeline)
    results.append(check("s8_four_assignments", len(fail_assignments) == 4))

    primary = [a for a in fail_assignments if a.blame_level == BlameLevel.PRIMARY]
    results.append(check("s8_one_primary", len(primary) == 1))
    results.append(check("s8_primary_is_bad", primary[0].agent_id == "bad-agent"))
    results.append(check("s8_primary_negative_t3", primary[0].t3_impact < 0))

    contributing = [a for a in fail_assignments if a.blame_level == BlameLevel.CONTRIBUTING]
    results.append(check("s8_one_contributing", len(contributing) == 1))
    results.append(check("s8_contributing_mediocre", contributing[0].agent_id == "mediocre-agent"))

    # ── S9: T3 Adjustments ──────────────────────────────────────
    print("\nS9: T3 Adjustments")
    adjustments = blame.t3_adjustments(fail_assignments)
    results.append(check("s9_good_positive", adjustments.get("good-agent", 0) > 0))
    results.append(check("s9_bad_negative", adjustments.get("bad-agent", 0) < 0))
    results.append(check("s9_mediocre_negative", adjustments.get("mediocre-agent", 0) < 0))
    results.append(check("s9_skipped_zero", adjustments.get("skipped-agent", 0) == 0))

    # ── S10: Oversight Manager ──────────────────────────────────
    print("\nS10: Oversight Manager")
    oversight = OversightManager()
    oversight.configure_oversight("p1", [
        OversightPoint(hop_index=0, reason="First hop", auto_approve_trust=0.9),
        OversightPoint(hop_index=2, reason="Critical hop", auto_approve_trust=0.95),
    ])

    results.append(check("s10_needs_low_trust",
        oversight.needs_oversight("p1", 0, 0.5)))
    results.append(check("s10_no_need_high_trust",
        not oversight.needs_oversight("p1", 0, 0.95)))
    results.append(check("s10_no_oversight_hop1",
        not oversight.needs_oversight("p1", 1, 0.5)))

    # ── S11: Auto-Approve ───────────────────────────────────────
    print("\nS11: Auto-Approve Logic")
    auto_high = oversight.auto_approve_check("p1", 0, 0.95)
    results.append(check("s11_auto_high", auto_high is True))

    auto_low = oversight.auto_approve_check("p1", 0, 0.5)
    results.append(check("s11_manual_low", auto_low is None))

    auto_no_config = oversight.auto_approve_check("p1", 1, 0.5)
    results.append(check("s11_no_config_approve", auto_no_config is True))

    auto_unknown = oversight.auto_approve_check("unknown", 0, 0.1)
    results.append(check("s11_unknown_pipeline", auto_unknown is True))

    # ── S12: Circuit Breaker ────────────────────────────────────
    print("\nS12: Circuit Breaker")
    cb = PipelineCircuitBreaker(CircuitBreakerConfig(min_trust_threshold=0.3))
    good_hop = PipelineHop(callee_trust=0.8, cumulative_trust=0.6)
    ok, reason = cb.check_hop(good_hop, 0.6, 50.0)
    results.append(check("s12_good_passes", ok))
    results.append(check("s12_no_reason", reason is None))

    low_trust_hop = PipelineHop(callee_trust=0.8)
    ok2, reason2 = cb.check_hop(low_trust_hop, 0.1, 50.0)
    results.append(check("s12_low_trust_fails", not ok2))
    results.append(check("s12_trust_reason", "Trust" in (reason2 or "")))
    results.append(check("s12_state_open", cb.state == CircuitState.OPEN))

    # ── S13: Circuit Breaker — ATP ──────────────────────────────
    print("\nS13: Circuit Breaker — ATP")
    cb2 = PipelineCircuitBreaker(CircuitBreakerConfig(atp_minimum=10.0))
    low_atp_hop = PipelineHop(callee_trust=0.8)
    ok3, reason3 = cb2.check_hop(low_atp_hop, 0.8, 3.0)
    results.append(check("s13_low_atp_fails", not ok3))
    results.append(check("s13_atp_reason", "ATP" in (reason3 or "")))

    # ── S14: Audit Trail ────────────────────────────────────────
    print("\nS14: Audit Trail")
    audit = OrchestrationAuditTrail()
    audit.record("hop_start", 0, "agent-a", "Starting task")
    audit.record("hop_complete", 0, "agent-a", "Done")
    audit.record("hop_start", 1, "agent-b", "Next task")
    audit.record("hop_fail", 1, "agent-b", "Error")

    results.append(check("s14_four_entries", len(audit.entries) == 4))
    results.append(check("s14_first_genesis", audit.entries[0].prev_hash == "genesis"))
    results.append(check("s14_chain_valid", audit.verify_chain()))

    summary = audit.pipeline_summary()
    results.append(check("s14_starts_2", summary["hops_started"] == 2))
    results.append(check("s14_completes_1", summary["hops_completed"] == 1))
    results.append(check("s14_fails_1", summary["hops_failed"] == 1))

    # ── S15: Full Orchestrator — Happy Path ─────────────────────
    print("\nS15: Full Orchestrator — Happy Path")
    orch = PipelineOrchestrator(min_trust=0.3, trust_decay=0.95)
    orch.register_agent(agent_a)
    orch.register_agent(agent_b)
    orch.register_agent(agent_c)

    pipeline = orch.create_pipeline(
        initiator_id="a",
        description="Data processing pipeline",
        hop_specs=[
            {"callee_id": "b", "task_type": "extract", "description": "Extract data"},
            {"caller_id": "b", "callee_id": "c", "task_type": "transform", "description": "Transform"},
        ],
        total_budget=100.0,
    )
    results.append(check("s15_pipeline_id", len(pipeline.pipeline_id) > 0))
    results.append(check("s15_two_hops", len(pipeline.hops) == 2))
    results.append(check("s15_trust_positive", pipeline.end_to_end_trust > 0))

    executed = orch.execute_pipeline(pipeline.pipeline_id, {
        0: {"quality": 0.9, "success": True, "atp_cost": 5.0},
        1: {"quality": 0.85, "success": True, "atp_cost": 5.0},
    })
    results.append(check("s15_completed", executed.status == PipelineStatus.COMPLETED))
    results.append(check("s15_quality", executed.aggregate_quality > 0.5))
    results.append(check("s15_atp_spent", executed.total_spent > 0))
    results.append(check("s15_audit_hash", len(executed.audit_hash) == 16))

    # ── S16: Orchestrator — Failure Mid-Pipeline ────────────────
    print("\nS16: Failure Mid-Pipeline")
    orch2 = PipelineOrchestrator(min_trust=0.3)
    orch2.register_agent(agent_a)
    orch2.register_agent(agent_b)
    orch2.register_agent(agent_c)

    p2 = orch2.create_pipeline("a", "Failing pipeline", [
        {"callee_id": "b", "task_type": "step1"},
        {"caller_id": "b", "callee_id": "c", "task_type": "step2"},
        {"caller_id": "c", "callee_id": "a", "task_type": "step3"},
    ], 100.0)
    ex2 = orch2.execute_pipeline(p2.pipeline_id, {
        0: {"quality": 0.9, "success": True},
        1: {"quality": 0.0, "success": False, "failure_type": "agent_error",
            "failure_detail": "Model crashed"},
    })
    results.append(check("s16_failed", ex2.status == PipelineStatus.FAILED))
    results.append(check("s16_hop1_failed", ex2.hops[1].status == HopStatus.FAILED))
    results.append(check("s16_hop2_skipped", ex2.hops[2].status == HopStatus.SKIPPED))
    results.append(check("s16_partial_spend", ex2.total_spent > 0))

    # Blame attribution
    blame2 = BlameAttributionGraph()
    assignments2 = blame2.attribute_blame(ex2)
    primary2 = [a for a in assignments2 if a.blame_level == BlameLevel.PRIMARY]
    results.append(check("s16_blame_primary", len(primary2) == 1))
    results.append(check("s16_blame_agent_c", primary2[0].agent_id == "c"))

    # ── S17: Orchestrator — Low Trust Circuit Break ─────────────
    print("\nS17: Low Trust Circuit Break")
    low_trust_agent = AgentNode("d", "Agent Delta", "lct://low", 0.1, 0.1, 0.1, 100, "s1")
    orch3 = PipelineOrchestrator(min_trust=0.3)
    orch3.register_agent(agent_a)
    orch3.register_agent(low_trust_agent)

    p3 = orch3.create_pipeline("a", "Low trust pipeline", [
        {"callee_id": "d", "task_type": "risky"},
    ], 50.0)
    ex3 = orch3.execute_pipeline(p3.pipeline_id)
    results.append(check("s17_halted", ex3.status == PipelineStatus.HALTED))
    results.append(check("s17_circuit_break",
        ex3.hops[0].failure_type == FailureType.CIRCUIT_BREAK))

    # ── S18: Oversight Denial ───────────────────────────────────
    print("\nS18: Oversight Denial")
    orch4 = PipelineOrchestrator(min_trust=0.3)
    orch4.register_agent(agent_a)
    orch4.register_agent(agent_b)

    p4 = orch4.create_pipeline("a", "Oversight pipeline", [
        {"callee_id": "b", "task_type": "critical", "requires_oversight": True},
    ], 50.0)
    # Configure oversight with high trust threshold so manual approval needed
    orch4.oversight.configure_oversight(p4.pipeline_id, [
        OversightPoint(hop_index=0, reason="Critical task", auto_approve_trust=0.99),
    ])
    ex4 = orch4.execute_pipeline(p4.pipeline_id, {
        0: {"oversight_approved": False},
    })
    results.append(check("s18_halted", ex4.status == PipelineStatus.HALTED))
    results.append(check("s18_oversight_denied",
        ex4.hops[0].failure_type == FailureType.OVERSIGHT_DENIED))

    # ── S19: Oversight Approved ─────────────────────────────────
    print("\nS19: Oversight Approved")
    orch5 = PipelineOrchestrator(min_trust=0.3)
    orch5.register_agent(agent_a)
    orch5.register_agent(agent_b)

    p5 = orch5.create_pipeline("a", "Approved pipeline", [
        {"callee_id": "b", "task_type": "critical", "requires_oversight": True},
    ], 50.0)
    orch5.oversight.configure_oversight(p5.pipeline_id, [
        OversightPoint(hop_index=0, reason="Critical", auto_approve_trust=0.99),
    ])
    ex5 = orch5.execute_pipeline(p5.pipeline_id, {
        0: {"quality": 0.95, "success": True, "oversight_approved": True},
    })
    results.append(check("s19_completed", ex5.status == PipelineStatus.COMPLETED))
    results.append(check("s19_hop_approved", ex5.hops[0].oversight_approved))

    # ── S20: Multi-Hop Trust Decay ──────────────────────────────
    print("\nS20: Multi-Hop Trust Decay")
    trust5 = PipelineTrustModel(min_trust=0.1, decay=0.9)
    # 5 hops of identical trust
    hop_trusts = [trust5.compute_hop_trust(agent_a, agent_a, i) for i in range(5)]
    cumulative5 = trust5.compute_cumulative_trust(hop_trusts)
    # Should be (0.877 * 0.9^i) product
    results.append(check("s20_5hop_decayed", cumulative5 < 0.5))
    results.append(check("s20_monotonic_decay",
        all(hop_trusts[i] > hop_trusts[i+1] for i in range(4))))

    # ── S21: Budget Cascade — Large Pipeline ────────────────────
    print("\nS21: Budget Cascade — Large Pipeline")
    big_budget = ATPBudgetCascade(base_cost=10.0, fee_rate=0.05)
    allocs = big_budget.allocate_budget(1000.0, 10)
    results.append(check("s21_ten_allocs", len(allocs) == 10))
    results.append(check("s21_within_budget", sum(allocs) <= 1000.0))
    # First allocation should be largest
    results.append(check("s21_first_largest", allocs[0] == max(allocs)))
    # Each subsequent should be smaller (fee is % of decreasing remainder)
    results.append(check("s21_monotonic_decrease",
        all(allocs[i] >= allocs[i+1] for i in range(9))))

    # ── S22: Audit Trail Integrity ──────────────────────────────
    print("\nS22: Audit Trail Integrity")
    results.append(check("s22_chain_intact", orch.audit_trail.verify_chain()))
    summary22 = orch.audit_trail.pipeline_summary()
    results.append(check("s22_has_starts", summary22["hops_started"] > 0))
    results.append(check("s22_has_completes", summary22["hops_completed"] > 0))

    # ── S23: Blame — All Success ────────────────────────────────
    print("\nS23: Blame — All Success")
    success_assignments = blame.attribute_blame(executed)
    results.append(check("s23_all_none_blame",
        all(a.blame_level == BlameLevel.NONE for a in success_assignments)))
    adj23 = blame.t3_adjustments(success_assignments)
    results.append(check("s23_all_positive", all(v > 0 for v in adj23.values())))

    # ── S24: Pipeline Quality — Multiplicative ──────────────────
    print("\nS24: Pipeline Quality — Multiplicative")
    # Quality = product of per-hop qualities
    expected_quality = 0.9 * 0.85  # From S15
    results.append(check("s24_quality_product",
        abs(executed.aggregate_quality - expected_quality) < 0.01))

    # ── S25: Deployer Obligations ───────────────────────────────
    print("\nS25: Deployer Obligations (Art. 26)")
    # The initiator bears deployer obligations
    results.append(check("s25_initiator_set", executed.initiator_id == "a"))
    results.append(check("s25_initiator_tracked",
        any(e.agent_id == "a" for e in orch.audit_trail.entries)))

    # ── S26: Trust Model — Zero Trust ───────────────────────────
    print("\nS26: Edge — Zero Trust")
    zero_agent = AgentNode("z", "Zero", "", 0.0, 0.0, 0.0)
    zero_trust = trust_model.compute_hop_trust(agent_a, zero_agent, 0)
    results.append(check("s26_zero_trust", zero_trust == 0.0))
    results.append(check("s26_not_sufficient", not trust_model.trust_sufficient(0.0)))

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
