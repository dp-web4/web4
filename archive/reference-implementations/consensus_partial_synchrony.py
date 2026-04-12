#!/usr/bin/env python3
"""
Consensus Under Partial Synchrony — Session 20, Track 3

How Web4 federation consensus works in real-world network conditions:
- Vector clock causality tracking
- Partial network partition detection and classification
- Leader election under Byzantine failures
- Stale read detection and freshness guarantees
- Membership churn (join/leave during consensus)
- Adaptive timeout calibration
- Message reordering and deduplication
- Split-brain detection and resolution
- Consensus progress tracking and liveness monitoring
- Partition-tolerant state reconciliation
- Performance under adversarial conditions

Reference: federation consensus, gossip protocol, BFT implementations
"""

from __future__ import annotations
import hashlib
import math
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, FrozenSet, List, Optional, Set, Tuple


# ─── Constants ────────────────────────────────────────────────────────────────

class ConsensusPhase(Enum):
    IDLE = "idle"
    PRE_PREPARE = "pre_prepare"
    PREPARE = "prepare"
    COMMIT = "commit"
    FINALIZED = "finalized"
    FAILED = "failed"


class PartitionType(Enum):
    NONE = "none"
    ASYMMETRIC = "asymmetric"    # A→B works, B→A doesn't
    SYMMETRIC = "symmetric"      # A↮B
    PARTIAL = "partial"          # Some paths work, others don't
    TOTAL = "total"              # Complete network split


class NodeState(Enum):
    ACTIVE = "active"
    JOINING = "joining"
    LEAVING = "leaving"
    SUSPECTED = "suspected"
    FAILED = "failed"


# ─── Data Structures ─────────────────────────────────────────────────────────

@dataclass
class VectorClock:
    """Vector clock for causal ordering."""
    clocks: Dict[str, int] = field(default_factory=dict)

    def tick(self, node_id: str) -> "VectorClock":
        """Increment this node's clock."""
        new = VectorClock(dict(self.clocks))
        new.clocks[node_id] = new.clocks.get(node_id, 0) + 1
        return new

    def merge(self, other: "VectorClock") -> "VectorClock":
        """Merge two vector clocks (component-wise max)."""
        all_nodes = set(self.clocks.keys()) | set(other.clocks.keys())
        merged = {}
        for node in all_nodes:
            merged[node] = max(self.clocks.get(node, 0), other.clocks.get(node, 0))
        return VectorClock(merged)

    def happens_before(self, other: "VectorClock") -> bool:
        """Check if self happens-before other (causally precedes)."""
        if not self.clocks:
            return bool(other.clocks)
        at_least_one_less = False
        for node in set(self.clocks.keys()) | set(other.clocks.keys()):
            s = self.clocks.get(node, 0)
            o = other.clocks.get(node, 0)
            if s > o:
                return False
            if s < o:
                at_least_one_less = True
        return at_least_one_less

    def concurrent_with(self, other: "VectorClock") -> bool:
        """Check if events are concurrent (incomparable)."""
        return not self.happens_before(other) and not other.happens_before(self) and self.clocks != other.clocks


@dataclass
class ConsensusMessage:
    """A message in the consensus protocol."""
    sender: str
    sequence: int
    phase: ConsensusPhase
    value: str
    vector_clock: VectorClock
    timestamp: float
    view_number: int = 0
    msg_hash: str = ""

    def __post_init__(self):
        if not self.msg_hash:
            data = f"{self.sender}:{self.sequence}:{self.phase.value}:{self.value}:{self.view_number}"
            self.msg_hash = hashlib.sha256(data.encode()).hexdigest()[:16]


@dataclass
class ConsensusRound:
    """State of a single consensus round."""
    sequence: int
    proposed_value: Optional[str] = None
    phase: ConsensusPhase = ConsensusPhase.IDLE
    prepares: Dict[str, ConsensusMessage] = field(default_factory=dict)
    commits: Dict[str, ConsensusMessage] = field(default_factory=dict)
    finalized_value: Optional[str] = None
    start_time: float = 0.0
    view_number: int = 0


# ─── S1: Vector Clock Causality ──────────────────────────────────────────────

def detect_causality_violation(
    messages: List[ConsensusMessage],
) -> List[Tuple[ConsensusMessage, ConsensusMessage]]:
    """
    Detect messages that violate causal ordering.
    Returns pairs of (earlier_received, later_sent) that are causally inverted.
    """
    violations = []
    for i, msg_a in enumerate(messages):
        for msg_b in messages[i + 1:]:
            # If b happened before a in vector clock but arrived after → violation
            if msg_b.vector_clock.happens_before(msg_a.vector_clock):
                if msg_b.timestamp > msg_a.timestamp:
                    violations.append((msg_a, msg_b))
    return violations


# ─── S2: Partition Detection ────────────────────────────────────────────────

class PartitionDetector:
    """Detect and classify network partitions."""

    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.heartbeats: Dict[str, Dict[str, float]] = {}  # sender → {receiver → last_time}
        self.nodes: Set[str] = set()

    def add_node(self, node_id: str):
        self.nodes.add(node_id)
        if node_id not in self.heartbeats:
            self.heartbeats[node_id] = {}

    def record_heartbeat(self, sender: str, receiver: str, timestamp: float):
        if sender not in self.heartbeats:
            self.heartbeats[sender] = {}
        self.heartbeats[sender][receiver] = timestamp

    def reachability_matrix(self, now: float) -> Dict[str, Set[str]]:
        """Build reachability matrix — who can reach whom."""
        reach = {}
        for node in self.nodes:
            reach[node] = set()
            for peer in self.nodes:
                if peer == node:
                    reach[node].add(peer)
                    continue
                last = self.heartbeats.get(node, {}).get(peer, 0)
                if now - last < self.timeout:
                    reach[node].add(peer)
        return reach

    def classify_partition(self, now: float) -> PartitionType:
        """Classify the current partition state."""
        reach = self.reachability_matrix(now)

        # Check for any missing links
        has_missing = False
        has_asymmetric = False

        for a in self.nodes:
            for b in self.nodes:
                if a == b:
                    continue
                a_to_b = b in reach.get(a, set())
                b_to_a = a in reach.get(b, set())

                if not a_to_b and not b_to_a:
                    has_missing = True
                elif a_to_b != b_to_a:
                    has_asymmetric = True

        if not has_missing and not has_asymmetric:
            return PartitionType.NONE

        # Check if network is totally split into components
        components = self._find_components(reach)
        if len(components) > 1:
            # All nodes in different components can't reach each other
            all_isolated = True
            for comp_a in components:
                for comp_b in components:
                    if comp_a == comp_b:
                        continue
                    for node_a in comp_a:
                        for node_b in comp_b:
                            if node_b in reach.get(node_a, set()):
                                all_isolated = False
            if all_isolated:
                return PartitionType.TOTAL

        if has_asymmetric:
            return PartitionType.ASYMMETRIC

        return PartitionType.PARTIAL

    def _find_components(self, reach: Dict[str, Set[str]]) -> List[Set[str]]:
        """Find connected components (treating links as undirected)."""
        visited = set()
        components = []

        for node in self.nodes:
            if node in visited:
                continue
            component = set()
            queue = [node]
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                component.add(current)
                # Both directions
                for peer in self.nodes:
                    if peer not in visited:
                        if peer in reach.get(current, set()) or current in reach.get(peer, set()):
                            queue.append(peer)
            components.append(component)

        return components

    def isolated_nodes(self, now: float) -> Set[str]:
        """Find nodes that can't reach anyone."""
        reach = self.reachability_matrix(now)
        isolated = set()
        for node in self.nodes:
            peers = reach.get(node, set()) - {node}
            if not peers:
                isolated.add(node)
        return isolated


# ─── S3: Leader Election Under Byzantine Failures ───────────────────────────

class LeaderElection:
    """View-change based leader election resilient to Byzantine failures."""

    def __init__(self, nodes: List[str], max_faults: int):
        self.nodes = sorted(nodes)
        self.n = len(nodes)
        self.f = max_faults
        self.current_view = 0
        self.view_change_votes: Dict[int, Set[str]] = {}  # view → voters
        self.complaints: Dict[str, int] = {}  # node_id → complaint count

    def current_leader(self) -> str:
        """Leader is determined by view number mod n."""
        return self.nodes[self.current_view % self.n]

    def complain(self, node_id: str, target_view: int) -> bool:
        """
        Node complains about current leader, requesting view change.
        Returns True if view change triggered.
        """
        if target_view not in self.view_change_votes:
            self.view_change_votes[target_view] = set()
        self.view_change_votes[target_view].add(node_id)

        # Need f+1 complaints to trigger view change
        if len(self.view_change_votes[target_view]) >= self.f + 1:
            self.current_view = target_view
            return True
        return False

    def view_change_quorum(self, view: int) -> bool:
        """Check if enough votes exist for view change."""
        votes = self.view_change_votes.get(view, set())
        return len(votes) >= self.f + 1

    def skip_byzantine_leader(self) -> str:
        """Skip suspected Byzantine leader and move to next view."""
        self.current_view += 1
        return self.current_leader()


# ─── S4: Stale Read Detection ───────────────────────────────────────────────

@dataclass
class FinalityRecord:
    """Tracks finality state at each node."""
    sequence: int
    value_hash: str
    finality_time: float
    witnesses: Set[str] = field(default_factory=set)


class FreshnessGuarantee:
    """Detect and prevent stale reads."""

    def __init__(self, staleness_threshold: float = 10.0):
        self.threshold = staleness_threshold
        self.node_finality: Dict[str, FinalityRecord] = {}  # node → latest finality

    def update_finality(self, node_id: str, record: FinalityRecord):
        current = self.node_finality.get(node_id)
        if current is None or record.sequence > current.sequence:
            self.node_finality[node_id] = record

    def is_stale(self, node_id: str, now: float) -> bool:
        """Check if a node's state is stale."""
        record = self.node_finality.get(node_id)
        if record is None:
            return True
        return now - record.finality_time > self.threshold

    def freshest_node(self, now: float) -> Optional[str]:
        """Find the node with the most recent finality."""
        best = None
        best_seq = -1
        for node_id, record in self.node_finality.items():
            if not self.is_stale(node_id, now) and record.sequence > best_seq:
                best = node_id
                best_seq = record.sequence
        return best

    def finality_lag(self, node_a: str, node_b: str) -> int:
        """Sequence gap between two nodes (positive = a is behind b)."""
        rec_a = self.node_finality.get(node_a)
        rec_b = self.node_finality.get(node_b)
        if rec_a is None or rec_b is None:
            return -1
        return rec_b.sequence - rec_a.sequence


# ─── S5: Membership Churn ───────────────────────────────────────────────────

@dataclass
class MembershipEvent:
    """Node join/leave event."""
    node_id: str
    event_type: str  # "join" or "leave"
    timestamp: float
    epoch: int  # Membership epoch number


class ChurnManager:
    """Handle membership changes during consensus."""

    def __init__(self, initial_members: List[str]):
        self.members: Dict[str, NodeState] = {m: NodeState.ACTIVE for m in initial_members}
        self.epoch = 0
        self.events: List[MembershipEvent] = []
        self.pending_joins: Set[str] = set()
        self.pending_leaves: Set[str] = set()

    def request_join(self, node_id: str, timestamp: float) -> bool:
        """Request to join — takes effect at next epoch."""
        if node_id in self.members:
            return False
        self.pending_joins.add(node_id)
        self.members[node_id] = NodeState.JOINING
        self.events.append(MembershipEvent(node_id, "join", timestamp, self.epoch))
        return True

    def request_leave(self, node_id: str, timestamp: float) -> bool:
        """Request to leave — takes effect at next epoch."""
        if node_id not in self.members or self.members[node_id] == NodeState.FAILED:
            return False
        self.pending_leaves.add(node_id)
        self.members[node_id] = NodeState.LEAVING
        self.events.append(MembershipEvent(node_id, "leave", timestamp, self.epoch))
        return True

    def advance_epoch(self) -> int:
        """Apply pending joins/leaves atomically."""
        self.epoch += 1
        for node in self.pending_joins:
            self.members[node] = NodeState.ACTIVE
        for node in self.pending_leaves:
            del self.members[node]
        self.pending_joins.clear()
        self.pending_leaves.clear()
        return self.epoch

    def active_members(self) -> List[str]:
        return [n for n, s in self.members.items() if s == NodeState.ACTIVE]

    def quorum_size(self) -> int:
        """BFT quorum for current active membership."""
        n = len(self.active_members())
        f = (n - 1) // 3
        return 2 * f + 1

    def can_reach_consensus(self) -> bool:
        """Check if we have enough active members for BFT."""
        active = len(self.active_members())
        return active >= 4  # Need at least 3f+1 = 4 (f=1)


# ─── S6: Adaptive Timeout Calibration ───────────────────────────────────────

class AdaptiveTimeout:
    """Calibrate consensus timeouts based on observed latencies."""

    def __init__(self, initial_timeout: float = 5.0, alpha: float = 0.125):
        self.timeout = initial_timeout
        self.alpha = alpha  # EWMA smoothing factor
        self.estimated_rtt: float = initial_timeout / 3
        self.rtt_variance: float = initial_timeout / 6
        self.samples: List[float] = []
        self.min_timeout: float = 1.0
        self.max_timeout: float = 60.0

    def record_rtt(self, rtt: float):
        """Record an observed round-trip time."""
        self.samples.append(rtt)
        # TCP-style RTT estimation (Jacobson/Karels)
        error = rtt - self.estimated_rtt
        self.estimated_rtt += self.alpha * error
        self.rtt_variance += self.alpha * (abs(error) - self.rtt_variance)
        self.timeout = max(
            self.min_timeout,
            min(self.max_timeout, self.estimated_rtt + 4 * self.rtt_variance),
        )

    def current_timeout(self) -> float:
        return self.timeout

    def backoff(self, factor: float = 2.0):
        """Exponential backoff after timeout."""
        self.timeout = min(self.max_timeout, self.timeout * factor)

    def reset(self):
        """Reset after successful communication."""
        if self.samples:
            self.timeout = max(
                self.min_timeout,
                self.estimated_rtt + 4 * self.rtt_variance,
            )


# ─── S7: Message Deduplication ──────────────────────────────────────────────

class MessageDeduplicator:
    """Detect and filter duplicate/reordered messages."""

    def __init__(self, window_size: int = 1000):
        self.seen: Dict[str, float] = {}  # msg_hash → timestamp
        self.window_size = window_size
        self.sequence_per_sender: Dict[str, int] = {}  # sender → max_sequence

    def is_duplicate(self, msg: ConsensusMessage) -> bool:
        """Check if message is a duplicate."""
        return msg.msg_hash in self.seen

    def is_reordered(self, msg: ConsensusMessage) -> bool:
        """Check if message arrived out of sequence."""
        max_seq = self.sequence_per_sender.get(msg.sender, -1)
        return msg.sequence < max_seq

    def accept(self, msg: ConsensusMessage) -> bool:
        """
        Accept a message if not duplicate.
        Returns True if accepted (new message).
        """
        if msg.msg_hash in self.seen:
            return False

        self.seen[msg.msg_hash] = msg.timestamp
        current_max = self.sequence_per_sender.get(msg.sender, -1)
        if msg.sequence > current_max:
            self.sequence_per_sender[msg.sender] = msg.sequence

        # Evict old entries
        if len(self.seen) > self.window_size:
            oldest = min(self.seen, key=self.seen.get)
            del self.seen[oldest]

        return True


# ─── S8: Split-Brain Detection ──────────────────────────────────────────────

@dataclass
class BrainState:
    """State of a partition component."""
    nodes: FrozenSet[str]
    latest_sequence: int
    latest_value_hash: str
    leader: Optional[str]


def detect_split_brain(
    components: List[Set[str]],
    finality: FreshnessGuarantee,
) -> List[Tuple[BrainState, BrainState]]:
    """
    Detect split-brain: two partition components both making progress.
    Returns pairs of conflicting brain states.
    """
    brain_states = []
    for comp in components:
        if not comp:
            continue
        max_seq = -1
        best_hash = ""
        leader = None
        for node in comp:
            rec = finality.node_finality.get(node)
            if rec and rec.sequence > max_seq:
                max_seq = rec.sequence
                best_hash = rec.value_hash
                leader = node
        brain_states.append(BrainState(
            nodes=frozenset(comp),
            latest_sequence=max_seq,
            latest_value_hash=best_hash,
            leader=leader,
        ))

    # Find conflicts: different values at similar sequences
    conflicts = []
    for i, a in enumerate(brain_states):
        for b in brain_states[i + 1:]:
            if a.latest_sequence >= 0 and b.latest_sequence >= 0:
                seq_gap = abs(a.latest_sequence - b.latest_sequence)
                if seq_gap < 5 and a.latest_value_hash != b.latest_value_hash:
                    conflicts.append((a, b))

    return conflicts


# ─── S9: Consensus Progress Tracking ────────────────────────────────────────

@dataclass
class ProgressMetrics:
    """Metrics for consensus progress monitoring."""
    rounds_attempted: int = 0
    rounds_finalized: int = 0
    rounds_failed: int = 0
    avg_latency: float = 0.0
    current_streak: int = 0  # Consecutive successes
    view_changes: int = 0
    messages_sent: int = 0
    messages_deduplicated: int = 0

    @property
    def success_rate(self) -> float:
        if self.rounds_attempted == 0:
            return 0.0
        return self.rounds_finalized / self.rounds_attempted

    @property
    def liveness(self) -> bool:
        """Are we making progress? In partial synchrony, 30%+ finalization counts."""
        return self.rounds_finalized > 0 and self.success_rate > 0.3


class ProgressTracker:
    """Track consensus progress and detect stalls."""

    def __init__(self, stall_threshold: int = 5):
        self.metrics = ProgressMetrics()
        self.stall_threshold = stall_threshold
        self.consecutive_failures = 0
        self.round_latencies: List[float] = []

    def record_round(self, finalized: bool, latency: float):
        self.metrics.rounds_attempted += 1
        if finalized:
            self.metrics.rounds_finalized += 1
            self.metrics.current_streak += 1
            self.consecutive_failures = 0
            self.round_latencies.append(latency)
            if self.round_latencies:
                self.metrics.avg_latency = sum(self.round_latencies) / len(self.round_latencies)
        else:
            self.metrics.rounds_failed += 1
            self.metrics.current_streak = 0
            self.consecutive_failures += 1

    def is_stalled(self) -> bool:
        return self.consecutive_failures >= self.stall_threshold

    def record_view_change(self):
        self.metrics.view_changes += 1

    def record_message(self, deduplicated: bool = False):
        self.metrics.messages_sent += 1
        if deduplicated:
            self.metrics.messages_deduplicated += 1


# ─── S10: Partition-Tolerant State Reconciliation ───────────────────────────

@dataclass
class StateEntry:
    """A key-value state entry with version."""
    key: str
    value: str
    version: int
    origin: str  # Node that created this version
    timestamp: float


class StateReconciler:
    """Reconcile divergent state after partition heals."""

    def __init__(self):
        self.states: Dict[str, Dict[str, StateEntry]] = {}  # node → {key → entry}

    def set_state(self, node_id: str, entry: StateEntry):
        if node_id not in self.states:
            self.states[node_id] = {}
        self.states[node_id][entry.key] = entry

    def reconcile(
        self,
        nodes: List[str],
        strategy: str = "latest_version",
    ) -> Dict[str, StateEntry]:
        """
        Reconcile state across nodes.
        Strategies: "latest_version", "latest_timestamp", "majority_wins"
        """
        all_keys: Set[str] = set()
        for node in nodes:
            all_keys.update(self.states.get(node, {}).keys())

        reconciled = {}
        for key in all_keys:
            entries = []
            for node in nodes:
                entry = self.states.get(node, {}).get(key)
                if entry:
                    entries.append(entry)

            if not entries:
                continue

            if strategy == "latest_version":
                reconciled[key] = max(entries, key=lambda e: e.version)
            elif strategy == "latest_timestamp":
                reconciled[key] = max(entries, key=lambda e: e.timestamp)
            elif strategy == "majority_wins":
                # Most common value wins
                value_counts: Dict[str, int] = {}
                value_entries: Dict[str, StateEntry] = {}
                for e in entries:
                    value_counts[e.value] = value_counts.get(e.value, 0) + 1
                    value_entries[e.value] = e
                winner = max(value_counts, key=value_counts.get)
                reconciled[key] = value_entries[winner]
            else:
                reconciled[key] = max(entries, key=lambda e: e.version)

        return reconciled

    def find_conflicts(self, nodes: List[str]) -> Dict[str, List[StateEntry]]:
        """Find keys where nodes disagree on value."""
        conflicts = {}
        all_keys: Set[str] = set()
        for node in nodes:
            all_keys.update(self.states.get(node, {}).keys())

        for key in all_keys:
            entries = []
            for node in nodes:
                entry = self.states.get(node, {}).get(key)
                if entry:
                    entries.append(entry)
            if len(entries) > 1:
                values = set(e.value for e in entries)
                if len(values) > 1:
                    conflicts[key] = entries

        return conflicts


# ─── S11: Performance ───────────────────────────────────────────────────────

# Included in checks


# ══════════════════════════════════════════════════════════════════════════════
#  CHECKS
# ══════════════════════════════════════════════════════════════════════════════

def run_checks():
    checks = []
    import random
    rng = random.Random(42)

    # ── S1: Vector Clock Causality ───────────────────────────────────────

    # S1.1: Tick increments correctly
    vc = VectorClock()
    vc1 = vc.tick("A")
    checks.append(("s1_tick", vc1.clocks.get("A") == 1))

    # S1.2: Happens-before relation
    vc_a = VectorClock({"A": 1, "B": 0})
    vc_b = VectorClock({"A": 1, "B": 1})
    checks.append(("s1_happens_before", vc_a.happens_before(vc_b)))
    checks.append(("s1_not_happens_after", not vc_b.happens_before(vc_a)))

    # S1.3: Concurrent events
    vc_x = VectorClock({"A": 2, "B": 1})
    vc_y = VectorClock({"A": 1, "B": 2})
    checks.append(("s1_concurrent", vc_x.concurrent_with(vc_y)))

    # S1.4: Merge takes component-wise max
    merged = vc_x.merge(vc_y)
    checks.append(("s1_merge", merged.clocks.get("A") == 2 and merged.clocks.get("B") == 2))

    # S1.5: Empty clock happens-before non-empty
    checks.append(("s1_empty_before", VectorClock().happens_before(vc_a)))

    # S1.6: Causality violation detection
    msg1 = ConsensusMessage("A", 1, ConsensusPhase.PREPARE, "v1",
                           VectorClock({"A": 2}), timestamp=100)
    msg2 = ConsensusMessage("B", 2, ConsensusPhase.PREPARE, "v1",
                           VectorClock({"A": 1}), timestamp=101)
    violations = detect_causality_violation([msg1, msg2])
    checks.append(("s1_causality_violation", len(violations) > 0))

    # S1.7: No violation when ordered
    msg3 = ConsensusMessage("A", 1, ConsensusPhase.PREPARE, "v1",
                           VectorClock({"A": 1}), timestamp=100)
    msg4 = ConsensusMessage("B", 2, ConsensusPhase.PREPARE, "v1",
                           VectorClock({"A": 2}), timestamp=101)
    violations = detect_causality_violation([msg3, msg4])
    checks.append(("s1_no_violation", len(violations) == 0))

    # ── S2: Partition Detection ──────────────────────────────────────────

    detector = PartitionDetector(timeout=5.0)
    for n in ["A", "B", "C", "D"]:
        detector.add_node(n)

    now = 100.0

    # S2.1: Full connectivity → no partition
    for a in ["A", "B", "C", "D"]:
        for b in ["A", "B", "C", "D"]:
            if a != b:
                detector.record_heartbeat(a, b, now)
    checks.append(("s2_no_partition", detector.classify_partition(now) == PartitionType.NONE))

    # S2.2: Asymmetric partition (A→B works, B→A doesn't)
    det2 = PartitionDetector(timeout=5.0)
    for n in ["A", "B"]:
        det2.add_node(n)
    det2.record_heartbeat("A", "B", now)
    # B→A has no heartbeat
    checks.append(("s2_asymmetric", det2.classify_partition(now) == PartitionType.ASYMMETRIC))

    # S2.3: Total partition
    det3 = PartitionDetector(timeout=5.0)
    for n in ["A", "B", "C", "D"]:
        det3.add_node(n)
    # Group 1: A↔B, Group 2: C↔D, no cross-group
    det3.record_heartbeat("A", "B", now)
    det3.record_heartbeat("B", "A", now)
    det3.record_heartbeat("C", "D", now)
    det3.record_heartbeat("D", "C", now)
    checks.append(("s2_total_partition", det3.classify_partition(now) == PartitionType.TOTAL))

    # S2.4: Stale heartbeats → partition
    checks.append(("s2_stale_partition", detector.classify_partition(now + 100) != PartitionType.NONE))

    # S2.5: Isolated node detection
    det4 = PartitionDetector(timeout=5.0)
    for n in ["A", "B", "C"]:
        det4.add_node(n)
    det4.record_heartbeat("A", "B", now)
    det4.record_heartbeat("B", "A", now)
    # C is isolated
    isolated = det4.isolated_nodes(now)
    checks.append(("s2_isolated_node", "C" in isolated))

    # S2.6: Reachability matrix
    reach = detector.reachability_matrix(now)
    checks.append(("s2_reachability", len(reach["A"]) == 4))  # A can reach all (incl self)

    # ── S3: Leader Election ──────────────────────────────────────────────

    election = LeaderElection(["N0", "N1", "N2", "N3"], max_faults=1)

    # S3.1: Initial leader is N0 (view 0, 0 % 4 = 0)
    checks.append(("s3_initial_leader", election.current_leader() == "N0"))

    # S3.2: View change requires f+1 complaints
    changed = election.complain("N1", 1)
    checks.append(("s3_one_complaint_no_change", not changed))

    # S3.3: Two complaints (f+1=2) triggers view change
    changed = election.complain("N2", 1)
    checks.append(("s3_two_complaints_change", changed))

    # S3.4: New leader after view change
    checks.append(("s3_new_leader", election.current_leader() == "N1"))

    # S3.5: Skip Byzantine leader
    new = election.skip_byzantine_leader()
    checks.append(("s3_skip_byzantine", new == "N2"))

    # S3.6: Quorum check
    checks.append(("s3_view_change_quorum", election.view_change_quorum(1)))
    checks.append(("s3_no_quorum", not election.view_change_quorum(999)))

    # ── S4: Stale Read Detection ─────────────────────────────────────────

    freshness = FreshnessGuarantee(staleness_threshold=10.0)
    now = 1000.0

    # S4.1: No finality → stale
    checks.append(("s4_no_finality_stale", freshness.is_stale("node1", now)))

    # S4.2: Recent finality → fresh
    freshness.update_finality("node1", FinalityRecord(10, "hash1", now - 2))
    checks.append(("s4_recent_fresh", not freshness.is_stale("node1", now)))

    # S4.3: Old finality → stale
    checks.append(("s4_old_stale", freshness.is_stale("node1", now + 20)))

    # S4.4: Freshest node
    freshness.update_finality("node2", FinalityRecord(12, "hash2", now - 1))
    best = freshness.freshest_node(now)
    checks.append(("s4_freshest", best == "node2"))  # Higher sequence, more recent

    # S4.5: Finality lag
    lag = freshness.finality_lag("node1", "node2")
    checks.append(("s4_lag", lag == 2))

    # S4.6: Update to higher sequence
    freshness.update_finality("node1", FinalityRecord(15, "hash3", now))
    checks.append(("s4_update_higher", freshness.node_finality["node1"].sequence == 15))

    # S4.7: Lower sequence ignored
    freshness.update_finality("node1", FinalityRecord(5, "old", now))
    checks.append(("s4_lower_ignored", freshness.node_finality["node1"].sequence == 15))

    # ── S5: Membership Churn ─────────────────────────────────────────────

    churn = ChurnManager(["A", "B", "C", "D"])

    # S5.1: Initial members
    checks.append(("s5_initial_4", len(churn.active_members()) == 4))

    # S5.2: Join request goes to JOINING
    churn.request_join("E", now)
    checks.append(("s5_join_request", churn.members["E"] == NodeState.JOINING))

    # S5.3: Joining not in active members
    checks.append(("s5_joining_not_active", "E" not in churn.active_members()))

    # S5.4: Advance epoch activates
    churn.advance_epoch()
    checks.append(("s5_epoch_activates", churn.members["E"] == NodeState.ACTIVE))

    # S5.5: Leave request
    churn.request_leave("A", now)
    checks.append(("s5_leave_request", churn.members["A"] == NodeState.LEAVING))

    # S5.6: Advance epoch removes
    churn.advance_epoch()
    checks.append(("s5_epoch_removes", "A" not in churn.members))

    # S5.7: Quorum size
    active = len(churn.active_members())  # 4 (B,C,D,E)
    q = churn.quorum_size()
    f = (active - 1) // 3  # 1
    checks.append(("s5_quorum", q == 2 * f + 1))

    # S5.8: Can reach consensus
    checks.append(("s5_can_consensus", churn.can_reach_consensus()))

    # S5.9: Duplicate join rejected
    checks.append(("s5_dup_join", not churn.request_join("B", now)))

    # ── S6: Adaptive Timeout ─────────────────────────────────────────────

    timeout = AdaptiveTimeout(initial_timeout=5.0)

    # S6.1: Initial timeout
    checks.append(("s6_initial", timeout.current_timeout() == 5.0))

    # S6.2: Low RTTs reduce timeout
    for _ in range(10):
        timeout.record_rtt(0.5)
    checks.append(("s6_low_rtt", timeout.current_timeout() < 5.0))

    # S6.3: Backoff increases timeout
    pre_backoff = timeout.current_timeout()
    timeout.backoff()
    checks.append(("s6_backoff", timeout.current_timeout() > pre_backoff))

    # S6.4: Timeout bounded
    for _ in range(20):
        timeout.backoff()
    checks.append(("s6_max_bound", timeout.current_timeout() <= 60.0))

    # S6.5: Reset after success
    timeout.reset()
    checks.append(("s6_reset", timeout.current_timeout() < 60.0))

    # S6.6: Min bound
    fast_timeout = AdaptiveTimeout(initial_timeout=5.0)
    for _ in range(100):
        fast_timeout.record_rtt(0.001)
    checks.append(("s6_min_bound", fast_timeout.current_timeout() >= 1.0))

    # ── S7: Message Deduplication ────────────────────────────────────────

    dedup = MessageDeduplicator()

    msg = ConsensusMessage("A", 1, ConsensusPhase.PREPARE, "v1",
                          VectorClock({"A": 1}), 100)

    # S7.1: First message accepted
    checks.append(("s7_first_accepted", dedup.accept(msg)))

    # S7.2: Duplicate rejected
    checks.append(("s7_duplicate_rejected", not dedup.accept(msg)))

    # S7.3: Different message accepted
    msg2 = ConsensusMessage("B", 1, ConsensusPhase.PREPARE, "v1",
                           VectorClock({"B": 1}), 101)
    checks.append(("s7_different_accepted", dedup.accept(msg2)))

    # S7.4: Reorder detection
    msg3 = ConsensusMessage("A", 5, ConsensusPhase.PREPARE, "v1",
                           VectorClock({"A": 5}), 102)
    dedup.accept(msg3)
    msg_old = ConsensusMessage("A", 2, ConsensusPhase.PREPARE, "v1",
                              VectorClock({"A": 2}), 103)
    checks.append(("s7_reorder_detected", dedup.is_reordered(msg_old)))

    # S7.5: Eviction at window size
    small_dedup = MessageDeduplicator(window_size=5)
    for i in range(10):
        m = ConsensusMessage(f"N{i}", i, ConsensusPhase.PREPARE, f"v{i}",
                            VectorClock(), 100 + i)
        small_dedup.accept(m)
    checks.append(("s7_eviction", len(small_dedup.seen) <= 5))

    # ── S8: Split-Brain Detection ────────────────────────────────────────

    fresh = FreshnessGuarantee()

    # S8.1: No split-brain with consistent state
    fresh.update_finality("A", FinalityRecord(10, "same_hash", now))
    fresh.update_finality("B", FinalityRecord(10, "same_hash", now))
    components = [{"A", "B"}]
    conflicts = detect_split_brain(components, fresh)
    checks.append(("s8_no_split_brain", len(conflicts) == 0))

    # S8.2: Split-brain with divergent state
    fresh.update_finality("C", FinalityRecord(10, "hash_c", now))
    fresh.update_finality("D", FinalityRecord(11, "hash_d", now))
    components = [{"A", "B"}, {"C", "D"}]
    conflicts = detect_split_brain(components, fresh)
    checks.append(("s8_split_brain_detected", len(conflicts) > 0))

    # S8.3: Large sequence gap → not split brain (just lagging)
    fresh2 = FreshnessGuarantee()
    fresh2.update_finality("X", FinalityRecord(1, "old", now))
    fresh2.update_finality("Y", FinalityRecord(100, "new", now))
    conflicts = detect_split_brain([{"X"}, {"Y"}], fresh2)
    checks.append(("s8_lag_not_split", len(conflicts) == 0))

    # ── S9: Progress Tracking ────────────────────────────────────────────

    tracker = ProgressTracker(stall_threshold=3)

    # S9.1: Initial state
    checks.append(("s9_initial", tracker.metrics.success_rate == 0.0))

    # S9.2: Successful rounds
    tracker.record_round(True, 0.5)
    tracker.record_round(True, 0.6)
    checks.append(("s9_success_rate", tracker.metrics.success_rate == 1.0))

    # S9.3: Failed round
    tracker.record_round(False, 5.0)
    checks.append(("s9_streak_broken", tracker.metrics.current_streak == 0))

    # S9.4: Not stalled yet
    checks.append(("s9_not_stalled", not tracker.is_stalled()))

    # S9.5: Stall detection
    tracker.record_round(False, 5.0)
    tracker.record_round(False, 5.0)
    checks.append(("s9_stalled", tracker.is_stalled()))

    # S9.6: Liveness check
    checks.append(("s9_liveness", tracker.metrics.liveness))

    # S9.7: Average latency
    checks.append(("s9_avg_latency", abs(tracker.metrics.avg_latency - 0.55) < 0.01))

    # S9.8: View change tracking
    tracker.record_view_change()
    checks.append(("s9_view_change", tracker.metrics.view_changes == 1))

    # ── S10: State Reconciliation ────────────────────────────────────────

    recon = StateReconciler()

    # S10.1: No conflicts when states agree
    recon.set_state("A", StateEntry("key1", "value1", 1, "A", now))
    recon.set_state("B", StateEntry("key1", "value1", 1, "A", now))
    conflicts = recon.find_conflicts(["A", "B"])
    checks.append(("s10_no_conflicts", len(conflicts) == 0))

    # S10.2: Conflict detected when states diverge
    recon.set_state("B", StateEntry("key1", "value2", 2, "B", now + 1))
    conflicts = recon.find_conflicts(["A", "B"])
    checks.append(("s10_conflict_detected", "key1" in conflicts))

    # S10.3: Reconcile by latest version
    result = recon.reconcile(["A", "B"], strategy="latest_version")
    checks.append(("s10_latest_version", result["key1"].value == "value2"))

    # S10.4: Reconcile by latest timestamp
    recon.set_state("A", StateEntry("key2", "old", 1, "A", now))
    recon.set_state("B", StateEntry("key2", "new", 1, "B", now + 5))
    result = recon.reconcile(["A", "B"], strategy="latest_timestamp")
    checks.append(("s10_latest_timestamp", result["key2"].value == "new"))

    # S10.5: Majority wins
    recon.set_state("C", StateEntry("key3", "consensus", 1, "C", now))
    recon.set_state("A", StateEntry("key3", "consensus", 1, "A", now))
    recon.set_state("B", StateEntry("key3", "outlier", 1, "B", now))
    result = recon.reconcile(["A", "B", "C"], strategy="majority_wins")
    checks.append(("s10_majority_wins", result["key3"].value == "consensus"))

    # S10.6: Reconcile preserves all keys
    recon.set_state("A", StateEntry("unique_a", "val_a", 1, "A", now))
    recon.set_state("B", StateEntry("unique_b", "val_b", 1, "B", now))
    result = recon.reconcile(["A", "B"])
    checks.append(("s10_all_keys", "unique_a" in result and "unique_b" in result))

    # ── S11: Performance ─────────────────────────────────────────────────

    # S11.1: Vector clock merge at scale
    t0 = time.time()
    vc_big = VectorClock({f"n{i}": rng.randint(1, 1000) for i in range(100)})
    vc_other = VectorClock({f"n{i}": rng.randint(1, 1000) for i in range(100)})
    for _ in range(1000):
        vc_big.merge(vc_other)
    elapsed = time.time() - t0
    checks.append(("s11_vc_merge_1000", elapsed < 1.0))

    # S11.2: Partition detection with 50 nodes
    t0 = time.time()
    big_det = PartitionDetector(timeout=5.0)
    for i in range(50):
        big_det.add_node(f"node_{i}")
    for i in range(50):
        for j in range(50):
            if i != j and rng.random() > 0.2:
                big_det.record_heartbeat(f"node_{i}", f"node_{j}", now)
    ptype = big_det.classify_partition(now)
    elapsed = time.time() - t0
    checks.append(("s11_partition_50", elapsed < 2.0))

    # S11.3: Message dedup at scale
    t0 = time.time()
    big_dedup = MessageDeduplicator(window_size=5000)
    for i in range(5000):
        m = ConsensusMessage(f"n{i % 50}", i, ConsensusPhase.PREPARE,
                            f"v{i}", VectorClock(), now + i)
        big_dedup.accept(m)
    elapsed = time.time() - t0
    checks.append(("s11_dedup_5000", elapsed < 2.0))

    # S11.4: State reconciliation at scale
    t0 = time.time()
    big_recon = StateReconciler()
    for node in range(20):
        for key in range(100):
            big_recon.set_state(f"n{node}", StateEntry(
                f"key_{key}", f"val_{rng.randint(0, 3)}",
                rng.randint(1, 10), f"n{node}", now + rng.random(),
            ))
    result = big_recon.reconcile([f"n{i}" for i in range(20)])
    elapsed = time.time() - t0
    checks.append(("s11_reconcile_20x100", len(result) == 100 and elapsed < 2.0))

    # S11.5: Churn manager 100 joins/leaves
    t0 = time.time()
    big_churn = ChurnManager([f"init_{i}" for i in range(10)])
    for i in range(100):
        if i % 2 == 0:
            big_churn.request_join(f"new_{i}", now + i)
        else:
            members = big_churn.active_members()
            if members:
                big_churn.request_leave(members[0], now + i)
        if i % 10 == 9:
            big_churn.advance_epoch()
    elapsed = time.time() - t0
    checks.append(("s11_churn_100", elapsed < 1.0))

    # ── Print Results ────────────────────────────────────────────────────
    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    print(f"\n{'='*60}")
    print(f"  Consensus Under Partial Synchrony — {passed}/{total} checks passed")
    print(f"{'='*60}")

    for name, ok in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")

    if passed < total:
        print(f"\n  FAILURES:")
        for name, ok in checks:
            if not ok:
                print(f"    ✗ {name}")

    print()
    return passed, total


if __name__ == "__main__":
    run_checks()
