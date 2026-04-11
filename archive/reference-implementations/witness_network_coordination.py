"""
Witness Network Coordination & Quorum Management
=================================================

Builds on witness_protocol_unified.py and witnessing_spec.py to add:
1. WitnessPool — Federation-wide pool with reputation tracking
2. QuorumSelector — Reputation-weighted random selection with diversity requirements
3. WitnessSLA — Availability/response-time tracking with penalty enforcement
4. WitnessSlasher — Consequences for false/biased attestations
5. LoadBalancer — Distribute duties across federation to prevent exhaustion
6. WitnessIncentives — ATP-based reward/penalty economics
7. QuorumComposer — Multi-society diversity and geographic requirements
8. WitnessNetworkOrchestrator — Ties everything together

Gap closed: Individual witness types documented but distributed coordination not.
"""

from __future__ import annotations
import hashlib
import math
import random
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict


# ─── Enums ────────────────────────────────────────────────────────────────────

class WitnessClass(str, Enum):
    TIME = "time"
    AUDIT = "audit"
    ORACLE = "oracle"
    EXISTENCE = "existence"
    ACTION = "action"
    STATE = "state"
    QUALITY = "quality"


class WitnessStatus(Enum):
    ACTIVE = auto()
    IDLE = auto()
    OVERLOADED = auto()
    SUSPENDED = auto()
    SLASHED = auto()
    RETIRED = auto()


class SLAViolation(Enum):
    RESPONSE_TIMEOUT = auto()
    AVAILABILITY_BELOW_SLA = auto()
    FALSE_ATTESTATION = auto()
    BIAS_DETECTED = auto()
    COLLUSION_DETECTED = auto()


class SelectionStrategy(Enum):
    REPUTATION_WEIGHTED = auto()
    ROUND_ROBIN = auto()
    LEAST_LOADED = auto()
    DIVERSITY_FIRST = auto()


# ─── Data Structures ─────────────────────────────────────────────────────────

@dataclass
class WitnessNode:
    """A witness in the federation pool."""
    witness_id: str
    society_id: str
    region: str  # Geographic region
    classes: Set[WitnessClass]  # Which witness types it can serve
    stake: float = 100.0  # ATP staked
    reputation: float = 0.5  # [0, 1]
    status: WitnessStatus = WitnessStatus.ACTIVE
    total_attestations: int = 0
    successful_attestations: int = 0
    false_attestations: int = 0
    total_response_time_ms: float = 0.0
    current_load: int = 0
    max_load: int = 20
    availability_checks: int = 0
    availability_hits: int = 0
    last_active: float = field(default_factory=time.time)
    penalties: List[Dict] = field(default_factory=list)
    rewards: List[Dict] = field(default_factory=list)

    @property
    def accuracy_rate(self) -> float:
        if self.total_attestations == 0:
            return 1.0  # Benefit of doubt for new witnesses
        return self.successful_attestations / self.total_attestations

    @property
    def avg_response_ms(self) -> float:
        if self.total_attestations == 0:
            return 0.0
        return self.total_response_time_ms / self.total_attestations

    @property
    def availability_rate(self) -> float:
        if self.availability_checks == 0:
            return 1.0
        return self.availability_hits / self.availability_checks

    @property
    def utilization(self) -> float:
        return self.current_load / self.max_load if self.max_load > 0 else 1.0


@dataclass
class QuorumRequirement:
    """Requirements for forming a witness quorum."""
    min_witnesses: int = 3
    min_reputation: float = 0.3
    required_classes: Set[WitnessClass] = field(default_factory=lambda: {WitnessClass.TIME})
    min_societies: int = 1  # Minimum distinct societies represented
    min_regions: int = 1  # Minimum distinct geographic regions
    max_from_single_society: int = 0  # 0 = no limit
    response_timeout_ms: float = 5000.0
    min_availability: float = 0.8


@dataclass
class WitnessQuorum:
    """A selected witness quorum."""
    quorum_id: str
    witnesses: List[WitnessNode]
    requirement: QuorumRequirement
    formed_at: float = field(default_factory=time.time)
    societies: Set[str] = field(default_factory=set)
    regions: Set[str] = field(default_factory=set)
    avg_reputation: float = 0.0
    strategy_used: SelectionStrategy = SelectionStrategy.REPUTATION_WEIGHTED

    def __post_init__(self):
        self.societies = {w.society_id for w in self.witnesses}
        self.regions = {w.region for w in self.witnesses}
        if self.witnesses:
            self.avg_reputation = sum(w.reputation for w in self.witnesses) / len(self.witnesses)
        if not self.quorum_id:
            content = ":".join(w.witness_id for w in self.witnesses) + f":{self.formed_at}"
            self.quorum_id = hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class SLARecord:
    """SLA compliance record for a witness."""
    witness_id: str
    period_start: float
    period_end: float
    expected_availability: float
    actual_availability: float
    expected_response_ms: float
    actual_avg_response_ms: float
    attestation_count: int
    violations: List[SLAViolation] = field(default_factory=list)
    compliant: bool = True


@dataclass
class IncentiveRecord:
    """ATP incentive record."""
    witness_id: str
    amount: float  # Positive = reward, negative = penalty
    reason: str
    timestamp: float = field(default_factory=time.time)


# ─── Witness Pool ─────────────────────────────────────────────────────────────

class WitnessPool:
    """Federation-wide pool of witnesses with reputation tracking."""

    def __init__(self, federation_id: str):
        self.federation_id = federation_id
        self.witnesses: Dict[str, WitnessNode] = {}
        self.by_society: Dict[str, Set[str]] = defaultdict(set)
        self.by_region: Dict[str, Set[str]] = defaultdict(set)
        self.by_class: Dict[WitnessClass, Set[str]] = defaultdict(set)

    def register(self, witness: WitnessNode) -> bool:
        """Register a witness in the pool."""
        if witness.witness_id in self.witnesses:
            return False

        self.witnesses[witness.witness_id] = witness
        self.by_society[witness.society_id].add(witness.witness_id)
        self.by_region[witness.region].add(witness.witness_id)
        for wc in witness.classes:
            self.by_class[wc].add(witness.witness_id)
        return True

    def deregister(self, witness_id: str) -> bool:
        """Remove a witness from the pool."""
        w = self.witnesses.get(witness_id)
        if not w:
            return False

        self.by_society[w.society_id].discard(witness_id)
        self.by_region[w.region].discard(witness_id)
        for wc in w.classes:
            self.by_class[wc].discard(witness_id)
        del self.witnesses[witness_id]
        return True

    def get_eligible(self, requirement: QuorumRequirement) -> List[WitnessNode]:
        """Get all witnesses eligible for a quorum requirement."""
        eligible = []
        for w in self.witnesses.values():
            if w.status not in (WitnessStatus.ACTIVE, WitnessStatus.IDLE):
                continue
            if w.reputation < requirement.min_reputation:
                continue
            if w.availability_rate < requirement.min_availability:
                continue
            if w.utilization >= 1.0:
                continue
            eligible.append(w)
        return eligible

    def record_attestation(self, witness_id: str, success: bool,
                           response_ms: float):
        """Record an attestation result."""
        w = self.witnesses.get(witness_id)
        if not w:
            return

        w.total_attestations += 1
        w.total_response_time_ms += response_ms
        if success:
            w.successful_attestations += 1
        else:
            w.false_attestations += 1

        # Update reputation
        self._update_reputation(w, success)
        w.last_active = time.time()

    def record_availability(self, witness_id: str, available: bool):
        """Record an availability check."""
        w = self.witnesses.get(witness_id)
        if not w:
            return

        w.availability_checks += 1
        if available:
            w.availability_hits += 1

    def _update_reputation(self, w: WitnessNode, success: bool):
        """Update reputation with bounded exponential moving average."""
        delta = 0.02 if success else -0.05
        w.reputation = max(0.0, min(1.0, w.reputation + delta))

    def get_stats(self) -> Dict:
        """Get pool statistics."""
        active = [w for w in self.witnesses.values()
                  if w.status == WitnessStatus.ACTIVE]
        return {
            "total_witnesses": len(self.witnesses),
            "active_witnesses": len(active),
            "societies": len(self.by_society),
            "regions": len(self.by_region),
            "classes_covered": len(self.by_class),
            "avg_reputation": (sum(w.reputation for w in active) / len(active)
                               if active else 0.0),
            "avg_availability": (sum(w.availability_rate for w in active) / len(active)
                                 if active else 0.0),
        }


# ─── Quorum Selector ─────────────────────────────────────────────────────────

class QuorumSelector:
    """Selects witness quorums with configurable strategies."""

    def __init__(self, pool: WitnessPool, seed: int = None):
        self.pool = pool
        self.rng = random.Random(seed)

    def select(self, requirement: QuorumRequirement,
               strategy: SelectionStrategy = SelectionStrategy.REPUTATION_WEIGHTED,
               exclude: Set[str] = None) -> Optional[WitnessQuorum]:
        """Select a quorum meeting the requirement."""
        eligible = self.pool.get_eligible(requirement)
        if exclude:
            eligible = [w for w in eligible if w.witness_id not in exclude]

        if len(eligible) < requirement.min_witnesses:
            return None

        # Filter by required classes
        if requirement.required_classes:
            class_eligible = [
                w for w in eligible
                if requirement.required_classes & w.classes
            ]
            if not class_eligible:
                return None

        if strategy == SelectionStrategy.REPUTATION_WEIGHTED:
            selected = self._reputation_weighted(eligible, requirement)
        elif strategy == SelectionStrategy.ROUND_ROBIN:
            selected = self._round_robin(eligible, requirement)
        elif strategy == SelectionStrategy.LEAST_LOADED:
            selected = self._least_loaded(eligible, requirement)
        elif strategy == SelectionStrategy.DIVERSITY_FIRST:
            selected = self._diversity_first(eligible, requirement)
        else:
            selected = self._reputation_weighted(eligible, requirement)

        if not selected or len(selected) < requirement.min_witnesses:
            return None

        # Verify diversity requirements
        societies = {w.society_id for w in selected}
        regions = {w.region for w in selected}

        if len(societies) < requirement.min_societies:
            return None
        if len(regions) < requirement.min_regions:
            return None

        # Check single-society concentration
        if requirement.max_from_single_society > 0:
            society_counts = defaultdict(int)
            for w in selected:
                society_counts[w.society_id] += 1
            if any(c > requirement.max_from_single_society
                   for c in society_counts.values()):
                return None

        # Update load
        for w in selected:
            w.current_load += 1

        quorum = WitnessQuorum(
            quorum_id="",
            witnesses=selected,
            requirement=requirement,
            strategy_used=strategy,
        )
        return quorum

    def _reputation_weighted(self, eligible: List[WitnessNode],
                             req: QuorumRequirement) -> List[WitnessNode]:
        """Select witnesses weighted by reputation."""
        if not eligible:
            return []

        weights = [max(w.reputation, 0.01) for w in eligible]
        total = sum(weights)
        probs = [wt / total for wt in weights]

        # Weighted sampling without replacement
        selected = []
        remaining = list(range(len(eligible)))
        remaining_probs = list(probs)

        for _ in range(min(req.min_witnesses, len(eligible))):
            if not remaining:
                break

            r = self.rng.random()
            cumsum = 0.0
            chosen_idx = remaining[-1]
            for i, idx in enumerate(remaining):
                cumsum += remaining_probs[i]
                if cumsum >= r:
                    chosen_idx = i
                    break

            selected.append(eligible[remaining[chosen_idx]])
            remaining.pop(chosen_idx)
            remaining_probs.pop(chosen_idx)
            # Renormalize
            total = sum(remaining_probs)
            if total > 0:
                remaining_probs = [p / total for p in remaining_probs]

        return selected

    def _round_robin(self, eligible: List[WitnessNode],
                     req: QuorumRequirement) -> List[WitnessNode]:
        """Select by round-robin (least-recently-active first)."""
        sorted_by_active = sorted(eligible, key=lambda w: w.last_active)
        return sorted_by_active[:req.min_witnesses]

    def _least_loaded(self, eligible: List[WitnessNode],
                      req: QuorumRequirement) -> List[WitnessNode]:
        """Select least-loaded witnesses."""
        sorted_by_load = sorted(eligible, key=lambda w: w.utilization)
        return sorted_by_load[:req.min_witnesses]

    def _diversity_first(self, eligible: List[WitnessNode],
                         req: QuorumRequirement) -> List[WitnessNode]:
        """Select for maximum diversity (societies, regions, classes)."""
        selected = []
        used_societies = set()
        used_regions = set()
        used_classes = set()

        # Sort by reputation descending for quality within diversity
        candidates = sorted(eligible, key=lambda w: w.reputation, reverse=True)

        while len(selected) < req.min_witnesses and candidates:
            best_score = -1
            best_idx = 0

            for i, w in enumerate(candidates):
                score = 0
                if w.society_id not in used_societies:
                    score += 3
                if w.region not in used_regions:
                    score += 2
                new_classes = w.classes - used_classes
                score += len(new_classes)
                score += w.reputation  # Tiebreak by reputation

                if score > best_score:
                    best_score = score
                    best_idx = i

            chosen = candidates.pop(best_idx)
            selected.append(chosen)
            used_societies.add(chosen.society_id)
            used_regions.add(chosen.region)
            used_classes.update(chosen.classes)

        return selected


# ─── Witness SLA ──────────────────────────────────────────────────────────────

class WitnessSLA:
    """SLA tracking and enforcement for witnesses."""

    def __init__(self, target_availability: float = 0.95,
                 target_response_ms: float = 5000.0,
                 min_accuracy: float = 0.9,
                 evaluation_period: float = 86400.0):  # 24 hours
        self.target_availability = target_availability
        self.target_response_ms = target_response_ms
        self.min_accuracy = min_accuracy
        self.evaluation_period = evaluation_period
        self.records: Dict[str, List[SLARecord]] = defaultdict(list)

    def evaluate(self, witness: WitnessNode) -> SLARecord:
        """Evaluate SLA compliance for a witness."""
        now = time.time()
        violations = []

        # Check availability
        if witness.availability_rate < self.target_availability:
            violations.append(SLAViolation.AVAILABILITY_BELOW_SLA)

        # Check response time
        if witness.avg_response_ms > self.target_response_ms and witness.total_attestations > 0:
            violations.append(SLAViolation.RESPONSE_TIMEOUT)

        # Check accuracy
        if witness.accuracy_rate < self.min_accuracy and witness.total_attestations >= 10:
            violations.append(SLAViolation.FALSE_ATTESTATION)

        record = SLARecord(
            witness_id=witness.witness_id,
            period_start=now - self.evaluation_period,
            period_end=now,
            expected_availability=self.target_availability,
            actual_availability=witness.availability_rate,
            expected_response_ms=self.target_response_ms,
            actual_avg_response_ms=witness.avg_response_ms,
            attestation_count=witness.total_attestations,
            violations=violations,
            compliant=len(violations) == 0,
        )

        self.records[witness.witness_id].append(record)
        return record

    def get_violation_count(self, witness_id: str) -> int:
        """Get total violations across all evaluation periods."""
        return sum(
            len(r.violations) for r in self.records.get(witness_id, [])
        )


# ─── Witness Slasher ─────────────────────────────────────────────────────────

class WitnessSlasher:
    """Penalty enforcement for witness misconduct."""

    def __init__(self, pool: WitnessPool,
                 false_attestation_penalty: float = 50.0,
                 sla_violation_penalty: float = 10.0,
                 collusion_penalty: float = 200.0,
                 slash_threshold: int = 3,
                 suspension_threshold: int = 5):
        self.pool = pool
        self.false_attestation_penalty = false_attestation_penalty
        self.sla_violation_penalty = sla_violation_penalty
        self.collusion_penalty = collusion_penalty
        self.slash_threshold = slash_threshold
        self.suspension_threshold = suspension_threshold
        self.incentive_records: List[IncentiveRecord] = []

    def slash_false_attestation(self, witness_id: str,
                                evidence: str = "") -> Optional[IncentiveRecord]:
        """Slash a witness for false attestation."""
        w = self.pool.witnesses.get(witness_id)
        if not w:
            return None

        penalty = min(self.false_attestation_penalty, w.stake)
        w.stake -= penalty
        w.reputation = max(0.0, w.reputation - 0.1)
        w.false_attestations += 1

        record = IncentiveRecord(
            witness_id=witness_id,
            amount=-penalty,
            reason=f"false_attestation:{evidence}",
        )
        self.incentive_records.append(record)
        w.penalties.append({"amount": penalty, "reason": "false_attestation"})

        # Check if should be suspended
        if w.false_attestations >= self.suspension_threshold:
            w.status = WitnessStatus.SLASHED

        return record

    def slash_sla_violation(self, witness_id: str,
                            violation: SLAViolation) -> Optional[IncentiveRecord]:
        """Slash for SLA violation."""
        w = self.pool.witnesses.get(witness_id)
        if not w:
            return None

        penalty = min(self.sla_violation_penalty, w.stake)
        w.stake -= penalty

        record = IncentiveRecord(
            witness_id=witness_id,
            amount=-penalty,
            reason=f"sla_violation:{violation.name}",
        )
        self.incentive_records.append(record)
        w.penalties.append({"amount": penalty, "reason": violation.name})

        # Accumulate → suspend
        total_penalties = sum(p["amount"] for p in w.penalties)
        if total_penalties >= self.slash_threshold * self.sla_violation_penalty:
            w.status = WitnessStatus.SUSPENDED

        return record

    def slash_collusion(self, witness_ids: List[str],
                        evidence: str = "") -> List[IncentiveRecord]:
        """Slash multiple witnesses for detected collusion."""
        records = []
        for wid in witness_ids:
            w = self.pool.witnesses.get(wid)
            if not w:
                continue

            penalty = min(self.collusion_penalty, w.stake)
            w.stake -= penalty
            w.reputation = max(0.0, w.reputation - 0.2)
            w.status = WitnessStatus.SLASHED

            record = IncentiveRecord(
                witness_id=wid,
                amount=-penalty,
                reason=f"collusion:{evidence}",
            )
            self.incentive_records.append(record)
            records.append(record)
            w.penalties.append({"amount": penalty, "reason": "collusion"})

        return records

    def reward(self, witness_id: str, amount: float,
               reason: str = "valid_attestation") -> Optional[IncentiveRecord]:
        """Reward a witness for valid attestation."""
        w = self.pool.witnesses.get(witness_id)
        if not w:
            return None

        w.stake += amount
        record = IncentiveRecord(witness_id=witness_id, amount=amount, reason=reason)
        self.incentive_records.append(record)
        w.rewards.append({"amount": amount, "reason": reason})
        return record


# ─── Load Balancer ────────────────────────────────────────────────────────────

class WitnessLoadBalancer:
    """Distributes witness duties across the federation."""

    def __init__(self, pool: WitnessPool,
                 overload_threshold: float = 0.8,
                 idle_threshold: float = 0.1):
        self.pool = pool
        self.overload_threshold = overload_threshold
        self.idle_threshold = idle_threshold

    def rebalance(self) -> Dict:
        """Rebalance load across witnesses."""
        overloaded = []
        idle = []
        balanced = []

        for w in self.pool.witnesses.values():
            if w.status != WitnessStatus.ACTIVE:
                continue

            util = w.utilization
            if util > self.overload_threshold:
                w.status = WitnessStatus.OVERLOADED
                overloaded.append(w.witness_id)
            elif util < self.idle_threshold:
                w.status = WitnessStatus.IDLE
                idle.append(w.witness_id)
            else:
                balanced.append(w.witness_id)

        return {
            "overloaded": overloaded,
            "idle": idle,
            "balanced": balanced,
            "total_active": len(overloaded) + len(idle) + len(balanced),
        }

    def get_load_distribution(self) -> Dict:
        """Get current load distribution statistics."""
        loads = [w.utilization for w in self.pool.witnesses.values()
                 if w.status in (WitnessStatus.ACTIVE, WitnessStatus.IDLE,
                                 WitnessStatus.OVERLOADED)]
        if not loads:
            return {"min": 0, "max": 0, "avg": 0, "std": 0}

        avg = sum(loads) / len(loads)
        variance = sum((l - avg) ** 2 for l in loads) / len(loads)

        return {
            "min": min(loads),
            "max": max(loads),
            "avg": avg,
            "std": math.sqrt(variance),
            "count": len(loads),
        }

    def release_load(self, witness_id: str, amount: int = 1):
        """Release load from a witness (attestation completed)."""
        w = self.pool.witnesses.get(witness_id)
        if w:
            w.current_load = max(0, w.current_load - amount)
            if w.status == WitnessStatus.OVERLOADED and w.utilization <= self.overload_threshold:
                w.status = WitnessStatus.ACTIVE


# ─── Quorum Composer ─────────────────────────────────────────────────────────

class QuorumComposer:
    """Composes quorums with multi-society and geographic diversity."""

    def __init__(self, pool: WitnessPool, selector: QuorumSelector):
        self.pool = pool
        self.selector = selector

    def compose_byzantine_tolerant(self, f: int = 1,
                                   required_classes: Set[WitnessClass] = None
                                   ) -> Optional[WitnessQuorum]:
        """Compose a BFT-tolerant quorum (N >= 3f + 1)."""
        n = 3 * f + 1
        req = QuorumRequirement(
            min_witnesses=n,
            min_reputation=0.4,
            required_classes=required_classes or {WitnessClass.TIME},
            min_societies=min(2, len(self.pool.by_society)),
            min_regions=min(2, len(self.pool.by_region)),
        )
        return self.selector.select(req, SelectionStrategy.DIVERSITY_FIRST)

    def compose_for_class(self, witness_class: WitnessClass,
                          min_witnesses: int = 3) -> Optional[WitnessQuorum]:
        """Compose a quorum for a specific witness class."""
        req = QuorumRequirement(
            min_witnesses=min_witnesses,
            required_classes={witness_class},
            min_reputation=0.3,
        )
        return self.selector.select(req, SelectionStrategy.REPUTATION_WEIGHTED)

    def compose_cross_society(self, society_ids: List[str],
                              per_society: int = 1) -> Optional[WitnessQuorum]:
        """Compose a quorum with witnesses from specific societies."""
        total_needed = len(society_ids) * per_society
        req = QuorumRequirement(
            min_witnesses=total_needed,
            min_societies=len(society_ids),
            max_from_single_society=per_society,
            min_reputation=0.3,
        )
        return self.selector.select(req, SelectionStrategy.DIVERSITY_FIRST)


# ─── Network Orchestrator ─────────────────────────────────────────────────────

class WitnessNetworkOrchestrator:
    """Orchestrates the complete witness network lifecycle."""

    def __init__(self, federation_id: str, seed: int = None):
        self.pool = WitnessPool(federation_id)
        self.selector = QuorumSelector(self.pool, seed=seed)
        self.sla = WitnessSLA()
        self.slasher = WitnessSlasher(self.pool)
        self.balancer = WitnessLoadBalancer(self.pool)
        self.composer = QuorumComposer(self.pool, self.selector)
        self.active_quorums: Dict[str, WitnessQuorum] = {}
        self.completed_quorums: List[str] = []

    def register_witness(self, witness: WitnessNode) -> bool:
        return self.pool.register(witness)

    def request_quorum(self, requirement: QuorumRequirement,
                       strategy: SelectionStrategy = SelectionStrategy.REPUTATION_WEIGHTED
                       ) -> Optional[WitnessQuorum]:
        """Request a new witness quorum."""
        quorum = self.selector.select(requirement, strategy)
        if quorum:
            self.active_quorums[quorum.quorum_id] = quorum
        return quorum

    def complete_attestation(self, quorum_id: str,
                             results: Dict[str, Tuple[bool, float]]):
        """Complete attestation and update witness records.

        results: witness_id → (success, response_ms)
        """
        quorum = self.active_quorums.get(quorum_id)
        if not quorum:
            return

        for w in quorum.witnesses:
            if w.witness_id in results:
                success, response_ms = results[w.witness_id]
                self.pool.record_attestation(w.witness_id, success, response_ms)
                self.balancer.release_load(w.witness_id)

                # Reward or penalize
                if success:
                    self.slasher.reward(w.witness_id, 5.0, "valid_attestation")
                else:
                    self.slasher.slash_false_attestation(w.witness_id)

        self.completed_quorums.append(quorum_id)
        del self.active_quorums[quorum_id]

    def run_sla_evaluation(self) -> List[SLARecord]:
        """Run SLA evaluation for all active witnesses."""
        records = []
        for w in self.pool.witnesses.values():
            if w.status in (WitnessStatus.ACTIVE, WitnessStatus.OVERLOADED):
                record = self.sla.evaluate(w)
                records.append(record)

                # Slash for violations
                for violation in record.violations:
                    self.slasher.slash_sla_violation(w.witness_id, violation)

        return records

    def get_network_health(self) -> Dict:
        """Get overall network health metrics."""
        stats = self.pool.get_stats()
        load = self.balancer.get_load_distribution()

        return {
            **stats,
            "load_distribution": load,
            "active_quorums": len(self.active_quorums),
            "completed_quorums": len(self.completed_quorums),
            "total_incentive_records": len(self.slasher.incentive_records),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def _make_witness(wid: str, society: str = "soc_A", region: str = "us-east",
                  classes: Set[WitnessClass] = None,
                  reputation: float = 0.7, stake: float = 100.0,
                  load: int = 0) -> WitnessNode:
    """Create a test witness node."""
    return WitnessNode(
        witness_id=wid,
        society_id=society,
        region=region,
        classes=classes or {WitnessClass.TIME, WitnessClass.AUDIT},
        reputation=reputation,
        stake=stake,
        current_load=load,
    )


def run_tests():
    results = []

    def check(name, condition, detail=""):
        results.append((name, condition, detail))

    # ─── S1: Witness Pool basics ──────────────────────────────────────

    pool = WitnessPool("fed_test")

    w1 = _make_witness("w1", "soc_A", "us-east")
    w2 = _make_witness("w2", "soc_B", "eu-west")
    w3 = _make_witness("w3", "soc_A", "ap-south")
    w4 = _make_witness("w4", "soc_C", "us-west")
    w5 = _make_witness("w5", "soc_B", "eu-east")

    check("s1_register", pool.register(w1))
    check("s1_register_dup", not pool.register(w1))  # Duplicate
    pool.register(w2)
    pool.register(w3)
    pool.register(w4)
    pool.register(w5)
    check("s1_total", len(pool.witnesses) == 5)
    check("s1_societies", len(pool.by_society) == 3)
    check("s1_regions", len(pool.by_region) == 5)

    # Deregister
    check("s1_deregister", pool.deregister("w5"))
    check("s1_deregister_gone", "w5" not in pool.witnesses)
    check("s1_deregister_not_found", not pool.deregister("w_nonexistent"))
    pool.register(w5)  # Re-register for later tests

    # Stats
    stats = pool.get_stats()
    check("s1_stats_total", stats["total_witnesses"] == 5)
    check("s1_stats_societies", stats["societies"] == 3)

    # Record attestation
    pool.record_attestation("w1", True, 100.0)
    pool.record_attestation("w1", True, 200.0)
    pool.record_attestation("w1", False, 500.0)
    check("s1_attestation_count", w1.total_attestations == 3)
    check("s1_accuracy", abs(w1.accuracy_rate - 2/3) < 0.01,
          f"accuracy={w1.accuracy_rate:.3f}")
    check("s1_avg_response", abs(w1.avg_response_ms - 800/3) < 0.1,
          f"avg_ms={w1.avg_response_ms:.1f}")

    # Availability
    pool.record_availability("w2", True)
    pool.record_availability("w2", True)
    pool.record_availability("w2", False)
    check("s1_availability", abs(w2.availability_rate - 2/3) < 0.01,
          f"avail={w2.availability_rate:.3f}")

    # ─── S2: Quorum selection — reputation weighted ───────────────────

    pool2 = WitnessPool("fed_select")
    for i in range(10):
        soc = f"soc_{chr(65 + i % 3)}"
        reg = ["us-east", "eu-west", "ap-south", "us-west"][i % 4]
        rep = 0.3 + (i * 0.07)
        w = _make_witness(f"sel_{i}", soc, reg, reputation=rep)
        pool2.register(w)

    selector = QuorumSelector(pool2, seed=42)
    req = QuorumRequirement(min_witnesses=3, min_reputation=0.3)
    quorum = selector.select(req, SelectionStrategy.REPUTATION_WEIGHTED)
    check("s2_quorum_formed", quorum is not None)
    check("s2_quorum_size", len(quorum.witnesses) == 3)
    check("s2_quorum_id", len(quorum.quorum_id) == 16)
    check("s2_all_above_min_rep",
          all(w.reputation >= 0.3 for w in quorum.witnesses))

    # ─── S3: Quorum selection — least loaded ──────────────────────────

    pool3 = WitnessPool("fed_load")
    for i in range(6):
        w = _make_witness(f"load_{i}", reputation=0.7, load=i * 3)
        pool3.register(w)

    selector3 = QuorumSelector(pool3, seed=42)
    req3 = QuorumRequirement(min_witnesses=3)
    quorum3 = selector3.select(req3, SelectionStrategy.LEAST_LOADED)
    check("s3_least_loaded", quorum3 is not None)
    # Should pick the 3 least loaded
    loads = [w.current_load - 1 for w in quorum3.witnesses]  # -1 because selection adds 1
    check("s3_low_loads", max(loads) <= 6,
          f"loads={loads}")

    # ─── S4: Quorum selection — diversity first ───────────────────────

    pool4 = WitnessPool("fed_diverse")
    societies = ["soc_A", "soc_B", "soc_C", "soc_D"]
    regions = ["us-east", "eu-west", "ap-south", "us-west"]
    for i in range(8):
        w = _make_witness(f"div_{i}", societies[i % 4], regions[i % 4],
                         reputation=0.5 + (i * 0.05))
        pool4.register(w)

    selector4 = QuorumSelector(pool4, seed=42)
    req4 = QuorumRequirement(min_witnesses=4, min_societies=3, min_regions=3)
    quorum4 = selector4.select(req4, SelectionStrategy.DIVERSITY_FIRST)
    check("s4_diverse_formed", quorum4 is not None)
    check("s4_min_societies", len(quorum4.societies) >= 3,
          f"societies={quorum4.societies}")
    check("s4_min_regions", len(quorum4.regions) >= 3,
          f"regions={quorum4.regions}")

    # ─── S5: Quorum selection — insufficient resources ────────────────

    small_pool = WitnessPool("fed_small")
    small_pool.register(_make_witness("small_1", reputation=0.2))
    small_pool.register(_make_witness("small_2", reputation=0.2))

    sel_small = QuorumSelector(small_pool, seed=42)
    req_big = QuorumRequirement(min_witnesses=5, min_reputation=0.3)
    check("s5_insufficient", sel_small.select(req_big) is None)

    # Low reputation filter
    req_high_rep = QuorumRequirement(min_witnesses=2, min_reputation=0.5)
    check("s5_low_rep", sel_small.select(req_high_rep) is None)

    # Overloaded witnesses excluded
    overload_pool = WitnessPool("fed_over")
    for i in range(3):
        w = _make_witness(f"over_{i}", load=20)  # max_load=20
        overload_pool.register(w)
    sel_over = QuorumSelector(overload_pool, seed=42)
    req_over = QuorumRequirement(min_witnesses=2)
    check("s5_overloaded", sel_over.select(req_over) is None)

    # ─── S6: Society concentration limit ──────────────────────────────

    conc_pool = WitnessPool("fed_conc")
    for i in range(5):
        soc = "soc_A" if i < 4 else "soc_B"
        conc_pool.register(_make_witness(f"conc_{i}", soc, reputation=0.7))

    sel_conc = QuorumSelector(conc_pool, seed=42)
    # Max 2 from any single society, need 3 total
    req_conc = QuorumRequirement(min_witnesses=3, max_from_single_society=2,
                                 min_societies=2)
    quorum_conc = sel_conc.select(req_conc, SelectionStrategy.DIVERSITY_FIRST)
    check("s6_concentration_limit", quorum_conc is not None)
    if quorum_conc:
        soc_counts = defaultdict(int)
        for w in quorum_conc.witnesses:
            soc_counts[w.society_id] += 1
        check("s6_max_per_society", max(soc_counts.values()) <= 2,
              f"counts={dict(soc_counts)}")

    # ─── S7: Witness SLA evaluation ───────────────────────────────────

    sla = WitnessSLA(target_availability=0.95, target_response_ms=1000.0)

    # Good witness
    good_w = _make_witness("good_w", reputation=0.9)
    for _ in range(20):
        good_w.total_attestations += 1
        good_w.successful_attestations += 1
        good_w.total_response_time_ms += 500.0
    for _ in range(20):
        good_w.availability_checks += 1
        good_w.availability_hits += 1

    good_record = sla.evaluate(good_w)
    check("s7_good_compliant", good_record.compliant)
    check("s7_good_no_violations", len(good_record.violations) == 0)

    # Bad witness — low availability
    bad_avail_w = _make_witness("bad_avail", reputation=0.5)
    for _ in range(100):
        bad_avail_w.availability_checks += 1
    for _ in range(80):
        bad_avail_w.availability_hits += 1  # 80% < 95%

    bad_avail_record = sla.evaluate(bad_avail_w)
    check("s7_bad_avail", not bad_avail_record.compliant)
    check("s7_avail_violation",
          SLAViolation.AVAILABILITY_BELOW_SLA in bad_avail_record.violations)

    # Bad witness — slow response
    slow_w = _make_witness("slow_w", reputation=0.5)
    for _ in range(20):
        slow_w.total_attestations += 1
        slow_w.successful_attestations += 1
        slow_w.total_response_time_ms += 2000.0  # 2s avg > 1s target

    slow_record = sla.evaluate(slow_w)
    check("s7_slow_violation",
          SLAViolation.RESPONSE_TIMEOUT in slow_record.violations)

    # Bad witness — low accuracy
    inaccurate_w = _make_witness("inaccurate_w", reputation=0.5)
    for _ in range(10):
        inaccurate_w.total_attestations += 1
    for _ in range(7):
        inaccurate_w.successful_attestations += 1  # 70% < 90%

    inacc_record = sla.evaluate(inaccurate_w)
    check("s7_accuracy_violation",
          SLAViolation.FALSE_ATTESTATION in inacc_record.violations)

    # ─── S8: Witness Slasher ──────────────────────────────────────────

    slash_pool = WitnessPool("fed_slash")
    slash_w = _make_witness("slash_target", stake=200.0, reputation=0.8)
    slash_pool.register(slash_w)
    slasher = WitnessSlasher(slash_pool)

    # False attestation penalty
    record = slasher.slash_false_attestation("slash_target", "test_evidence")
    check("s8_slash_amount", record.amount == -50.0,
          f"amount={record.amount}")
    check("s8_stake_reduced", slash_w.stake == 150.0,
          f"stake={slash_w.stake}")
    check("s8_rep_reduced", abs(slash_w.reputation - 0.7) < 0.001,
          f"rep={slash_w.reputation}")

    # SLA violation penalty
    sla_record = slasher.slash_sla_violation("slash_target",
                                             SLAViolation.RESPONSE_TIMEOUT)
    check("s8_sla_penalty", sla_record.amount == -10.0)
    check("s8_stake_after_sla", slash_w.stake == 140.0)

    # Reward
    reward_record = slasher.reward("slash_target", 20.0, "good_work")
    check("s8_reward", reward_record.amount == 20.0)
    check("s8_stake_after_reward", slash_w.stake == 160.0)

    # Collusion detection
    coll_pool = WitnessPool("fed_collusion")
    for i in range(3):
        coll_pool.register(_make_witness(f"coll_{i}", stake=100.0, reputation=0.6))
    coll_slasher = WitnessSlasher(coll_pool)
    coll_records = coll_slasher.slash_collusion(
        ["coll_0", "coll_1", "coll_2"], "coordinated_false_attestation")
    check("s8_collusion_count", len(coll_records) == 3)
    check("s8_collusion_all_slashed",
          all(coll_pool.witnesses[f"coll_{i}"].status == WitnessStatus.SLASHED
              for i in range(3)))

    # Suspension threshold
    susp_pool = WitnessPool("fed_susp")
    susp_w = _make_witness("susp_target", stake=500.0)
    susp_pool.register(susp_w)
    susp_slasher = WitnessSlasher(susp_pool, suspension_threshold=3)
    for i in range(3):
        susp_slasher.slash_false_attestation("susp_target", f"offense_{i}")
    check("s8_auto_suspend",
          susp_w.status == WitnessStatus.SLASHED)

    # Slash non-existent witness
    check("s8_slash_nonexistent",
          slasher.slash_false_attestation("nobody") is None)

    # ─── S9: Load Balancer ────────────────────────────────────────────

    lb_pool = WitnessPool("fed_lb")
    for i in range(6):
        w = _make_witness(f"lb_{i}", load=i * 4)
        lb_pool.register(w)

    balancer = WitnessLoadBalancer(lb_pool)
    rebalance = balancer.rebalance()
    check("s9_has_overloaded", len(rebalance["overloaded"]) > 0)
    check("s9_has_idle", len(rebalance["idle"]) > 0)
    check("s9_total", rebalance["total_active"] == 6)

    # Load distribution
    dist = balancer.get_load_distribution()
    check("s9_load_min", dist["min"] == 0.0)
    check("s9_load_max", dist["max"] == 1.0)
    check("s9_load_count", dist["count"] == 6)

    # Release load
    balancer.release_load("lb_5", 20)
    check("s9_release", lb_pool.witnesses["lb_5"].current_load == 0)

    # ─── S10: Quorum Composer — BFT ──────────────────────────────────

    orch = WitnessNetworkOrchestrator("fed_orch", seed=42)
    societies = ["soc_A", "soc_B", "soc_C"]
    regions = ["us-east", "eu-west", "ap-south"]

    for i in range(12):
        w = _make_witness(f"orch_{i}", societies[i % 3], regions[i % 3],
                         reputation=0.5 + (i * 0.03))
        orch.register_witness(w)

    # BFT quorum (f=1 → N=4)
    bft_quorum = orch.composer.compose_byzantine_tolerant(f=1)
    check("s10_bft_formed", bft_quorum is not None)
    if bft_quorum:
        check("s10_bft_size", len(bft_quorum.witnesses) >= 4,
              f"size={len(bft_quorum.witnesses)}")
        check("s10_bft_multi_society", len(bft_quorum.societies) >= 2,
              f"societies={bft_quorum.societies}")

    # Class-specific quorum
    time_quorum = orch.composer.compose_for_class(WitnessClass.TIME, 3)
    check("s10_time_quorum", time_quorum is not None)

    # Cross-society quorum
    cross_quorum = orch.composer.compose_cross_society(
        ["soc_A", "soc_B", "soc_C"], per_society=1)
    check("s10_cross_society", cross_quorum is not None)
    if cross_quorum:
        check("s10_cross_diversity", len(cross_quorum.societies) >= 3,
              f"soc={cross_quorum.societies}")

    # ─── S11: Orchestrator E2E ────────────────────────────────────────

    orch2 = WitnessNetworkOrchestrator("fed_e2e", seed=123)
    for i in range(10):
        soc = f"soc_{chr(65 + i % 3)}"
        reg = ["us", "eu", "ap"][i % 3]
        w = _make_witness(f"e2e_{i}", soc, reg, reputation=0.6 + (i * 0.03))
        orch2.register_witness(w)

    # Request quorum
    req = QuorumRequirement(min_witnesses=3, min_reputation=0.4)
    quorum = orch2.request_quorum(req)
    check("s11_quorum_requested", quorum is not None)
    check("s11_active_quorum", len(orch2.active_quorums) == 1)

    # Complete attestation
    if quorum:
        attestation_results = {}
        for w in quorum.witnesses:
            attestation_results[w.witness_id] = (True, 200.0)

        orch2.complete_attestation(quorum.quorum_id, attestation_results)
        check("s11_completed", len(orch2.completed_quorums) == 1)
        check("s11_active_cleared", len(orch2.active_quorums) == 0)

        # Witnesses got rewarded
        for w in quorum.witnesses:
            wnode = orch2.pool.witnesses[w.witness_id]
            check(f"s11_rewarded_{w.witness_id}",
                  len(wnode.rewards) > 0,
                  f"rewards={len(wnode.rewards)}")

    # SLA evaluation
    sla_records = orch2.run_sla_evaluation()
    check("s11_sla_records", len(sla_records) > 0,
          f"records={len(sla_records)}")

    # Network health
    health = orch2.get_network_health()
    check("s11_health_total", health["total_witnesses"] == 10)
    check("s11_health_active", health["active_witnesses"] > 0)

    # ─── S12: Multiple quorum cycles ──────────────────────────────────

    orch3 = WitnessNetworkOrchestrator("fed_cycles", seed=99)
    for i in range(15):
        w = _make_witness(f"cyc_{i}", f"soc_{i%4}", f"reg_{i%3}",
                         reputation=0.5 + (i * 0.02))
        orch3.register_witness(w)

    req_cycle = QuorumRequirement(min_witnesses=3, min_reputation=0.3)
    total_quorums = 0
    total_attestations = 0

    for cycle in range(5):
        q = orch3.request_quorum(req_cycle)
        if q:
            total_quorums += 1
            cycle_results = {w.witness_id: (True, 150.0 + cycle * 10)
                            for w in q.witnesses}
            orch3.complete_attestation(q.quorum_id, cycle_results)
            total_attestations += len(cycle_results)

    check("s12_all_quorums", total_quorums == 5)
    check("s12_all_completed", len(orch3.completed_quorums) == 5)
    check("s12_attestations", total_attestations == 15,
          f"attestations={total_attestations}")

    # Reputation should have improved for active witnesses
    active_reps = [w.reputation for w in orch3.pool.witnesses.values()
                   if w.total_attestations > 0]
    check("s12_rep_improved", all(r > 0.5 for r in active_reps),
          f"reps={[f'{r:.2f}' for r in active_reps]}")

    # ─── S13: Mixed success attestations ──────────────────────────────

    orch4 = WitnessNetworkOrchestrator("fed_mixed", seed=77)
    for i in range(6):
        w = _make_witness(f"mix_{i}", reputation=0.6, stake=200.0)
        orch4.register_witness(w)

    req_mix = QuorumRequirement(min_witnesses=3, min_reputation=0.3)
    q_mix = orch4.request_quorum(req_mix)
    check("s13_quorum", q_mix is not None)

    if q_mix:
        wids = [w.witness_id for w in q_mix.witnesses]
        # First witness fails, others succeed
        mix_results = {
            wids[0]: (False, 1000.0),  # Failed
            wids[1]: (True, 200.0),
            wids[2]: (True, 150.0),
        }
        orch4.complete_attestation(q_mix.quorum_id, mix_results)

        # Failed witness got slashed
        failed_w = orch4.pool.witnesses[wids[0]]
        check("s13_failed_penalized", failed_w.stake < 200.0,
              f"stake={failed_w.stake}")
        check("s13_failed_rep_drop", failed_w.reputation < 0.6,
              f"rep={failed_w.reputation}")

        # Successful witnesses got rewarded
        success_w = orch4.pool.witnesses[wids[1]]
        check("s13_success_rewarded", success_w.stake > 200.0,
              f"stake={success_w.stake}")

    # ─── S14: Reputation dynamics ─────────────────────────────────────

    rep_pool = WitnessPool("fed_rep")
    rep_w = _make_witness("rep_target", reputation=0.5)
    rep_pool.register(rep_w)

    # 10 successes: +0.02 each = +0.20
    for _ in range(10):
        rep_pool.record_attestation("rep_target", True, 100.0)
    check("s14_rep_after_success", abs(rep_w.reputation - 0.7) < 0.01,
          f"rep={rep_w.reputation:.3f}")

    # 5 failures: -0.05 each = -0.25
    for _ in range(5):
        rep_pool.record_attestation("rep_target", False, 500.0)
    check("s14_rep_after_failure", abs(rep_w.reputation - 0.45) < 0.01,
          f"rep={rep_w.reputation:.3f}")

    # Reputation bounded at 0
    low_w = _make_witness("low_w", reputation=0.1)
    rep_pool.register(low_w)
    for _ in range(5):
        rep_pool.record_attestation("low_w", False, 100.0)
    check("s14_rep_floor", low_w.reputation == 0.0,
          f"rep={low_w.reputation}")

    # Reputation bounded at 1
    high_w = _make_witness("high_w", reputation=0.95)
    rep_pool.register(high_w)
    for _ in range(10):
        rep_pool.record_attestation("high_w", True, 100.0)
    check("s14_rep_ceiling", high_w.reputation == 1.0,
          f"rep={high_w.reputation}")

    # ─── S15: Exclusion from quorum ───────────────────────────────────

    excl_pool = WitnessPool("fed_excl")
    for i in range(6):
        excl_pool.register(_make_witness(f"excl_{i}", reputation=0.7))

    sel_excl = QuorumSelector(excl_pool, seed=42)
    req_excl = QuorumRequirement(min_witnesses=3)

    # Exclude some witnesses
    excl_quorum = sel_excl.select(req_excl, exclude={"excl_0", "excl_1", "excl_2"})
    check("s15_exclude_works", excl_quorum is not None)
    if excl_quorum:
        excluded_ids = {w.witness_id for w in excl_quorum.witnesses}
        check("s15_none_excluded",
              not excluded_ids.intersection({"excl_0", "excl_1", "excl_2"}))

    # Exclude too many → fails
    excl_fail = sel_excl.select(req_excl,
                                exclude={"excl_0", "excl_1", "excl_2", "excl_3", "excl_4"})
    # Only 1 eligible, need 3
    check("s15_over_exclude", excl_fail is None)

    # ─── S16: Round-robin selection ───────────────────────────────────

    rr_pool = WitnessPool("fed_rr")
    for i in range(5):
        w = _make_witness(f"rr_{i}", reputation=0.6)
        w.last_active = time.time() - (i * 100)  # Older = selected first
        rr_pool.register(w)

    sel_rr = QuorumSelector(rr_pool, seed=42)
    req_rr = QuorumRequirement(min_witnesses=3)
    quorum_rr = sel_rr.select(req_rr, SelectionStrategy.ROUND_ROBIN)
    check("s16_round_robin", quorum_rr is not None)
    if quorum_rr:
        # Should pick the 3 with oldest last_active
        ids = {w.witness_id for w in quorum_rr.witnesses}
        check("s16_oldest_selected", "rr_4" in ids,
              f"selected={ids}")

    # ─── S17: Stake depletion ─────────────────────────────────────────

    depl_pool = WitnessPool("fed_depl")
    depl_w = _make_witness("depl_w", stake=30.0)
    depl_pool.register(depl_w)
    depl_slasher = WitnessSlasher(depl_pool, false_attestation_penalty=50.0)

    # Penalty capped at stake
    rec = depl_slasher.slash_false_attestation("depl_w")
    check("s17_capped_penalty", rec.amount == -30.0,
          f"amount={rec.amount}")
    check("s17_zero_stake", depl_w.stake == 0.0,
          f"stake={depl_w.stake}")

    # ─── S18: Witness class filtering ─────────────────────────────────

    class_pool = WitnessPool("fed_class")
    # Some witnesses only do TIME, some only AUDIT, some both
    class_pool.register(_make_witness("time_only",
                                     classes={WitnessClass.TIME}))
    class_pool.register(_make_witness("audit_only",
                                     classes={WitnessClass.AUDIT}))
    class_pool.register(_make_witness("both",
                                     classes={WitnessClass.TIME, WitnessClass.AUDIT}))
    class_pool.register(_make_witness("oracle_only",
                                     classes={WitnessClass.ORACLE}))

    # Class index
    check("s18_time_index", len(class_pool.by_class[WitnessClass.TIME]) == 2)
    check("s18_audit_index", len(class_pool.by_class[WitnessClass.AUDIT]) == 2)
    check("s18_oracle_index", len(class_pool.by_class[WitnessClass.ORACLE]) == 1)

    # ─── Print Results ────────────────────────────────────────────────

    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)

    print(f"\n{'='*70}")
    print(f"Witness Network Coordination & Quorum Management")
    print(f"{'='*70}")

    for name, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        det = f" [{detail}]" if detail else ""
        if not ok:
            print(f"  {status}: {name}{det}")

    print(f"\n  Total: {passed + failed} | Passed: {passed} | Failed: {failed}")
    print(f"{'='*70}")

    if failed > 0:
        print("\nFAILED TESTS:")
        for name, ok, detail in results:
            if not ok:
                print(f"  FAIL: {name} [{detail}]")

    return passed, failed


if __name__ == "__main__":
    run_tests()
