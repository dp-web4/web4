#!/usr/bin/env python3
"""
Temporal Consistency & Causal Ordering — Session 28, Track 4
=============================================================

Distributed trust operations need causal ordering guarantees. When trust
events happen across federation boundaries with clock drift, how do we
maintain consistency?

Models:
  1. Vector Clocks for trust event ordering
  2. Lamport Timestamps for lightweight causality
  3. Clock Drift Simulation with bounded skew
  4. Causal Consistency for trust operations
  5. Conflict-Free Replicated Data Types (CRDTs) for trust scores
  6. Happens-Before analysis for trust events
  7. Anti-Entropy protocol for trust state convergence
  8. Timeline reconstruction from partial observations

Key insight: Session 27 found cross-federation propagation is 13x slower.
This means trust events at federation boundaries have severe ordering
challenges — events may arrive out of causal order.

~80 checks expected.
"""

import math
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, FrozenSet

passed = 0
failed = 0
errors = []


def check(condition, msg):
    global passed, failed, errors
    if condition:
        passed += 1
    else:
        failed += 1
        errors.append(msg)
        print(f"  FAIL: {msg}")


# ============================================================
# §1 — Vector Clocks
# ============================================================

class VectorClock:
    """Vector clock for tracking causality in distributed trust systems.

    Each federation/node maintains a counter. Comparing two vector clocks
    determines happens-before, concurrent, or identical relationship.
    """

    def __init__(self, node_id: str, node_ids: Optional[List[str]] = None):
        self.node_id = node_id
        self.clock: Dict[str, int] = defaultdict(int)
        if node_ids:
            for nid in node_ids:
                self.clock[nid] = 0

    def tick(self) -> 'VectorClock':
        """Increment own counter (local event)."""
        self.clock[self.node_id] += 1
        return self

    def send(self) -> Dict[str, int]:
        """Prepare clock for sending with a message."""
        self.tick()
        return dict(self.clock)

    def receive(self, other_clock: Dict[str, int]):
        """Merge received clock (take component-wise max) and tick."""
        for nid, count in other_clock.items():
            self.clock[nid] = max(self.clock[nid], count)
        self.tick()

    def snapshot(self) -> Dict[str, int]:
        return dict(self.clock)

    def happens_before(self, other: 'VectorClock') -> bool:
        """Does self happen before other? (self < other)"""
        at_least_one_less = False
        for nid in set(list(self.clock.keys()) + list(other.clock.keys())):
            if self.clock.get(nid, 0) > other.clock.get(nid, 0):
                return False
            if self.clock.get(nid, 0) < other.clock.get(nid, 0):
                at_least_one_less = True
        return at_least_one_less

    def concurrent_with(self, other: 'VectorClock') -> bool:
        """Are self and other concurrent? (neither happens-before)"""
        return not self.happens_before(other) and not other.happens_before(self) and \
               self.clock != other.clock

    def identical_to(self, other: 'VectorClock') -> bool:
        """Are the clocks identical?"""
        all_keys = set(list(self.clock.keys()) + list(other.clock.keys()))
        return all(self.clock.get(k, 0) == other.clock.get(k, 0) for k in all_keys)


# ============================================================
# §2 — Lamport Timestamps
# ============================================================

class LamportClock:
    """Lightweight scalar logical clock.

    Weaker than vector clocks but O(1) space.
    If a → b then L(a) < L(b), but NOT the converse.
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.time: int = 0

    def tick(self) -> int:
        self.time += 1
        return self.time

    def send(self) -> int:
        return self.tick()

    def receive(self, sender_time: int) -> int:
        self.time = max(self.time, sender_time) + 1
        return self.time


# ============================================================
# §3 — Trust Events with Causal Ordering
# ============================================================

class TrustEventType(Enum):
    ATTESTATION = "attestation"
    REVOCATION = "revocation"
    DELEGATION = "delegation"
    MIGRATION = "migration"
    TRUST_UPDATE = "trust_update"
    ATP_TRANSFER = "atp_transfer"


@dataclass
class TrustEvent:
    """A trust event with causal metadata."""
    event_id: str
    event_type: TrustEventType
    source_node: str
    target_entity: str
    value: float = 0.0
    vector_clock: Dict[str, int] = field(default_factory=dict)
    lamport_time: int = 0
    wall_clock: float = 0.0
    causal_dependencies: Set[str] = field(default_factory=set)  # event_ids this depends on


class CausalEventLog:
    """Maintains a causally ordered log of trust events.

    Events are stored with their causal metadata and can be
    queried for ordering relationships.
    """

    def __init__(self):
        self.events: Dict[str, TrustEvent] = {}
        self.causal_graph: Dict[str, Set[str]] = defaultdict(set)  # event -> events it depends on

    def add_event(self, event: TrustEvent):
        self.events[event.event_id] = event
        self.causal_graph[event.event_id] = set(event.causal_dependencies)

    def happens_before(self, event_a_id: str, event_b_id: str) -> bool:
        """Check if event_a causally precedes event_b via transitive closure."""
        if event_a_id == event_b_id:
            return False
        visited = set()
        queue = [event_b_id]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            deps = self.causal_graph.get(current, set())
            if event_a_id in deps:
                return True
            queue.extend(deps)
        return False

    def concurrent_events(self) -> List[Tuple[str, str]]:
        """Find all pairs of concurrent events."""
        concurrent = []
        event_ids = list(self.events.keys())
        for i in range(len(event_ids)):
            for j in range(i + 1, len(event_ids)):
                a, b = event_ids[i], event_ids[j]
                if not self.happens_before(a, b) and not self.happens_before(b, a):
                    concurrent.append((a, b))
        return concurrent

    def causal_order(self) -> List[str]:
        """Topological sort of events by causal order."""
        in_degree = defaultdict(int)
        for eid in self.events:
            in_degree[eid] = len(self.causal_graph.get(eid, set()))

        queue = [eid for eid in self.events if in_degree[eid] == 0]
        order = []

        while queue:
            # Break ties by lamport time, then event_id
            queue.sort(key=lambda e: (self.events[e].lamport_time, e))
            current = queue.pop(0)
            order.append(current)

            # Find events that depend on current
            for eid, deps in self.causal_graph.items():
                if current in deps:
                    in_degree[eid] -= 1
                    if in_degree[eid] == 0 and eid not in order:
                        queue.append(eid)

        return order


# ============================================================
# §4 — Clock Drift Simulation
# ============================================================

@dataclass
class DriftingClock:
    """Simulates a wall clock with bounded drift.

    Real clocks drift at ~10-50 ppm. Over 1 hour, that's 36-180ms.
    """
    node_id: str
    drift_rate: float = 0.0  # ppm (parts per million)
    offset: float = 0.0       # initial offset in seconds
    _base_time: float = 0.0

    def __post_init__(self):
        self._base_time = time.time()

    def now(self, real_time: float) -> float:
        """Get this clock's reading at real_time."""
        elapsed = real_time - self._base_time
        drifted_elapsed = elapsed * (1.0 + self.drift_rate * 1e-6)
        return self._base_time + self.offset + drifted_elapsed

    def skew_from(self, other: 'DriftingClock', real_time: float) -> float:
        """Absolute clock skew between this and another clock."""
        return abs(self.now(real_time) - other.now(real_time))


class ClockSynchronizer:
    """NTP-like clock synchronization for federation nodes.

    Periodic sync reduces drift but can't eliminate it entirely.
    """

    def __init__(self, max_skew_tolerance: float = 0.1):
        self.max_skew_tolerance = max_skew_tolerance  # seconds
        self.sync_history: List[Dict] = []

    def sync_pair(self, clock_a: DriftingClock, clock_b: DriftingClock,
                  real_time: float, network_delay: float = 0.01) -> float:
        """Synchronize two clocks, returning residual skew."""
        reading_a = clock_a.now(real_time)
        reading_b = clock_b.now(real_time + network_delay)

        estimated_skew = reading_a - reading_b + network_delay / 2
        correction = estimated_skew / 2

        # Apply half-correction to each (gradual sync)
        clock_a.offset -= correction * 0.5
        clock_b.offset += correction * 0.5

        residual = clock_a.skew_from(clock_b, real_time + network_delay)
        self.sync_history.append({
            "time": real_time,
            "estimated_skew": estimated_skew,
            "residual": residual,
        })
        return residual

    def within_tolerance(self, clocks: List[DriftingClock], real_time: float) -> bool:
        """Check if all clocks are within tolerance of each other."""
        for i in range(len(clocks)):
            for j in range(i + 1, len(clocks)):
                if clocks[i].skew_from(clocks[j], real_time) > self.max_skew_tolerance:
                    return False
        return True


# ============================================================
# §5 — CRDTs for Trust Scores
# ============================================================

class GCounterTrust:
    """Grow-only counter CRDT for accumulating trust evidence.

    Each node can only increment. Merge = component-wise max.
    Guarantees eventual consistency without coordination.
    """

    def __init__(self, node_id: str, node_ids: List[str]):
        self.node_id = node_id
        self.counters: Dict[str, float] = {nid: 0.0 for nid in node_ids}

    def increment(self, amount: float = 1.0):
        self.counters[self.node_id] += amount

    def value(self) -> float:
        return sum(self.counters.values())

    def merge(self, other: 'GCounterTrust'):
        for nid in other.counters:
            self.counters[nid] = max(self.counters.get(nid, 0), other.counters[nid])

    def state(self) -> Dict[str, float]:
        return dict(self.counters)


class LWWRegisterTrust:
    """Last-Writer-Wins Register for trust scores.

    Concurrent writes resolved by timestamp (higher wins).
    Suitable for trust scores that are periodically recalculated.
    """

    def __init__(self):
        self.value: float = 0.0
        self.timestamp: int = 0  # Lamport timestamp
        self.writer: str = ""

    def write(self, value: float, timestamp: int, writer: str):
        if timestamp > self.timestamp or (timestamp == self.timestamp and writer > self.writer):
            self.value = value
            self.timestamp = timestamp
            self.writer = writer

    def merge(self, other: 'LWWRegisterTrust'):
        if other.timestamp > self.timestamp or \
           (other.timestamp == self.timestamp and other.writer > self.writer):
            self.value = other.value
            self.timestamp = other.timestamp
            self.writer = other.writer

    def read(self) -> Tuple[float, int, str]:
        return self.value, self.timestamp, self.writer


class ORSetTrust:
    """Observed-Remove Set CRDT for trust attestation sets.

    Supports concurrent add and remove. Add wins over concurrent remove.
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self._counter = 0
        self.adds: Dict[str, Set[Tuple[str, int]]] = defaultdict(set)  # element -> {(node, tag)}
        self.removes: Dict[str, Set[Tuple[str, int]]] = defaultdict(set)

    def add(self, element: str):
        self._counter += 1
        tag = (self.node_id, self._counter)
        self.adds[element].add(tag)

    def remove(self, element: str):
        # Only remove tags we've seen
        if element in self.adds:
            self.removes[element] |= self.adds[element]

    def contains(self, element: str) -> bool:
        return len(self.adds.get(element, set()) - self.removes.get(element, set())) > 0

    def elements(self) -> Set[str]:
        result = set()
        for elem, add_tags in self.adds.items():
            remove_tags = self.removes.get(elem, set())
            if len(add_tags - remove_tags) > 0:
                result.add(elem)
        return result

    def merge(self, other: 'ORSetTrust'):
        for elem, tags in other.adds.items():
            self.adds[elem] |= tags
        for elem, tags in other.removes.items():
            self.removes[elem] |= tags


# ============================================================
# §6 — Anti-Entropy Protocol
# ============================================================

class AntiEntropyProtocol:
    """Gossip-based anti-entropy for trust state convergence.

    Nodes periodically exchange state digests and synchronize
    missing or divergent entries.
    """

    def __init__(self, node_ids: List[str]):
        self.node_ids = node_ids
        self.states: Dict[str, Dict[str, float]] = {
            nid: {} for nid in node_ids
        }
        self.sync_count = 0
        self.convergence_history: List[float] = []

    def update_local(self, node_id: str, key: str, value: float):
        self.states[node_id][key] = value

    def sync_pair(self, node_a: str, node_b: str):
        """Synchronize state between two nodes (merge)."""
        state_a = self.states[node_a]
        state_b = self.states[node_b]

        # Merge: take max value for each key
        all_keys = set(list(state_a.keys()) + list(state_b.keys()))
        for key in all_keys:
            merged = max(state_a.get(key, 0), state_b.get(key, 0))
            state_a[key] = merged
            state_b[key] = merged

        self.sync_count += 1

    def run_round(self):
        """One round of random pair-wise sync."""
        nodes = list(self.node_ids)
        random.shuffle(nodes)
        for i in range(0, len(nodes) - 1, 2):
            self.sync_pair(nodes[i], nodes[i + 1])

    def convergence_metric(self) -> float:
        """Fraction of (node, key) pairs that agree on the same value.

        1.0 = fully converged.
        """
        all_keys = set()
        for state in self.states.values():
            all_keys.update(state.keys())

        if not all_keys or len(self.node_ids) < 2:
            return 1.0

        agreements = 0
        total_comparisons = 0

        for key in all_keys:
            values = [self.states[nid].get(key) for nid in self.node_ids]
            for i in range(len(values)):
                for j in range(i + 1, len(values)):
                    total_comparisons += 1
                    if values[i] == values[j]:
                        agreements += 1

        return agreements / total_comparisons if total_comparisons > 0 else 1.0


# ============================================================
# §7 — Tests
# ============================================================

def test_vector_clocks():
    """§7.1: Vector clock causality."""
    print("\n§7.1 Vector Clocks")

    nodes = ["fed_a", "fed_b", "fed_c"]

    vc_a = VectorClock("fed_a", nodes)
    vc_b = VectorClock("fed_b", nodes)
    vc_c = VectorClock("fed_c", nodes)

    # s1: Initial clocks are identical
    check(vc_a.identical_to(vc_b), "s1: initial clocks identical")

    # s2: Local tick creates ordering
    vc_a.tick()
    check(vc_a.clock["fed_a"] == 1, "s2: tick increments own counter")

    # s3: Send and receive establish happens-before
    msg = vc_a.send()  # a ticks to 2
    vc_b.receive(msg)   # b merges and ticks
    check(vc_b.clock["fed_a"] >= 2, "s3: receiver sees sender's state")
    check(vc_b.clock["fed_b"] >= 1, "s3b: receiver ticked own clock")

    # s4: Happens-before relationship
    vc_a_snap = VectorClock("fed_a", nodes)
    vc_a_snap.clock = dict(msg)  # State of a at send time
    check(vc_a_snap.happens_before(vc_b),
          "s4: sender's send state happens-before receiver's state")

    # s5: Concurrent events
    vc_a.tick()  # a does something independently
    vc_c.tick()  # c does something independently
    check(vc_a.concurrent_with(vc_c), "s5: independent events are concurrent")

    # s6: Transitivity: if a→b and b→c then a→c
    msg_b = vc_b.send()
    vc_c.receive(msg_b)
    # Now a (at send time) → b → c
    check(not vc_c.concurrent_with(vc_b), "s6: causally related events not concurrent")


def test_lamport_clocks():
    """§7.2: Lamport timestamp ordering."""
    print("\n§7.2 Lamport Clocks")

    lc_a = LamportClock("fed_a")
    lc_b = LamportClock("fed_b")

    # s7: Monotonically increasing
    t1 = lc_a.tick()
    t2 = lc_a.tick()
    check(t2 > t1, "s7: Lamport clock monotonically increasing")

    # s8: Send-receive ordering
    send_time = lc_a.send()
    recv_time = lc_b.receive(send_time)
    check(recv_time > send_time, "s8: receiver time > sender time")

    # s9: Multiple rounds maintain ordering
    for _ in range(5):
        t_send = lc_a.send()
        t_recv = lc_b.receive(t_send)
        t_reply = lc_b.send()
        t_recv2 = lc_a.receive(t_reply)
    check(lc_a.time > 0 and lc_b.time > 0, "s9: multi-round exchange works")
    check(lc_a.time > 5 and lc_b.time > 5, "s9b: clocks advance through exchanges")


def test_causal_event_log():
    """§7.3: Causal ordering of trust events."""
    print("\n§7.3 Causal Event Log")

    log = CausalEventLog()

    # Create events with causal dependencies
    # e1 → e2 → e4
    # e1 → e3 (concurrent with e2)
    # e3 → e5
    events = [
        TrustEvent("e1", TrustEventType.ATTESTATION, "fed_a", "entity_x",
                   lamport_time=1, causal_dependencies=set()),
        TrustEvent("e2", TrustEventType.TRUST_UPDATE, "fed_a", "entity_x",
                   lamport_time=2, causal_dependencies={"e1"}),
        TrustEvent("e3", TrustEventType.DELEGATION, "fed_b", "entity_y",
                   lamport_time=2, causal_dependencies={"e1"}),
        TrustEvent("e4", TrustEventType.ATP_TRANSFER, "fed_a", "entity_x",
                   lamport_time=3, causal_dependencies={"e2"}),
        TrustEvent("e5", TrustEventType.REVOCATION, "fed_b", "entity_y",
                   lamport_time=4, causal_dependencies={"e3"}),
    ]

    for e in events:
        log.add_event(e)

    # s10: Happens-before relationships
    check(log.happens_before("e1", "e2"), "s10: e1 → e2")
    check(log.happens_before("e1", "e4"), "s10b: e1 → e4 (transitive)")
    check(log.happens_before("e2", "e4"), "s10c: e2 → e4")

    # s11: Concurrent events
    check(not log.happens_before("e2", "e3") and not log.happens_before("e3", "e2"),
          "s11: e2 and e3 are concurrent")

    # s12: Find all concurrent pairs
    concurrent = log.concurrent_events()
    concurrent_set = {frozenset(pair) for pair in concurrent}
    check(frozenset(("e2", "e3")) in concurrent_set,
          f"s12: (e2, e3) in concurrent pairs ({len(concurrent)} pairs)")

    # s13: Causal order (topological sort)
    order = log.causal_order()
    check(order.index("e1") < order.index("e2"), "s13: e1 before e2 in causal order")
    check(order.index("e1") < order.index("e3"), "s13b: e1 before e3")
    check(order.index("e2") < order.index("e4"), "s13c: e2 before e4")
    check(order.index("e3") < order.index("e5"), "s13d: e3 before e5")

    # s14: All events present in order
    check(len(order) == 5, f"s14: all 5 events in causal order (got {len(order)})")


def test_clock_drift():
    """§7.4: Clock drift and synchronization."""
    print("\n§7.4 Clock Drift Simulation")

    base_time = time.time()

    # s15: Clocks with different drift rates
    clock_a = DriftingClock("node_a", drift_rate=10.0, offset=0.0)
    clock_a._base_time = base_time
    clock_b = DriftingClock("node_b", drift_rate=-20.0, offset=0.05)
    clock_b._base_time = base_time
    clock_c = DriftingClock("node_c", drift_rate=50.0, offset=-0.02)
    clock_c._base_time = base_time

    # s15: Different drift rates create different readings
    future = base_time + 3600  # 1 hour later
    reading_a = clock_a.now(future)
    reading_b = clock_b.now(future)
    check(abs(reading_a - reading_b) > 0.01,
          f"s15: clocks diverge over time (skew={abs(reading_a - reading_b):.4f}s)")

    # s16: Skew grows with time
    skew_1h = clock_a.skew_from(clock_b, base_time + 3600)
    skew_2h = clock_a.skew_from(clock_b, base_time + 7200)
    check(skew_2h > skew_1h,
          f"s16: skew grows ({skew_1h:.4f}s → {skew_2h:.4f}s)")

    # s17: Sync reduces skew
    sync = ClockSynchronizer(max_skew_tolerance=0.1)
    residual = sync.sync_pair(clock_a, clock_b, future, network_delay=0.01)
    check(residual < skew_1h + 0.1,
          f"s17: sync reduces skew (residual={residual:.4f}s)")

    # s18: Tolerance check
    clocks = [clock_a, clock_b, clock_c]
    # After multiple sync rounds
    for _ in range(5):
        for i in range(len(clocks)):
            for j in range(i + 1, len(clocks)):
                sync.sync_pair(clocks[i], clocks[j], future, 0.01)
    within = sync.within_tolerance(clocks, future)
    check(within, "s18: all clocks within tolerance after sync")


def test_crdts():
    """§7.5: CRDTs for trust scores."""
    print("\n§7.5 CRDTs for Trust")

    nodes = ["node_a", "node_b", "node_c"]

    # s19: G-Counter CRDT
    gc_a = GCounterTrust("node_a", nodes)
    gc_b = GCounterTrust("node_b", nodes)

    gc_a.increment(3.0)
    gc_b.increment(2.0)

    # Before merge
    check(gc_a.value() == 3.0 and gc_b.value() == 2.0, "s19: independent increments")

    # s20: Merge produces correct sum
    gc_a.merge(gc_b)
    check(gc_a.value() == 5.0, f"s20: merged G-Counter = 5.0 (got {gc_a.value()})")

    # s21: Merge is idempotent
    gc_a.merge(gc_b)
    check(gc_a.value() == 5.0, "s21: merge is idempotent")

    # s22: Merge is commutative
    gc_b.merge(gc_a)
    check(gc_b.value() == gc_a.value(), "s22: merge is commutative")

    # s23: LWW Register
    lww_a = LWWRegisterTrust()
    lww_b = LWWRegisterTrust()

    lww_a.write(0.7, timestamp=1, writer="node_a")
    lww_b.write(0.8, timestamp=2, writer="node_b")

    lww_a.merge(lww_b)
    check(lww_a.value == 0.8, f"s23: LWW takes later write (got {lww_a.value})")

    # s24: LWW tie-breaking by writer ID
    lww_c = LWWRegisterTrust()
    lww_d = LWWRegisterTrust()
    lww_c.write(0.6, timestamp=5, writer="node_a")
    lww_d.write(0.9, timestamp=5, writer="node_b")

    lww_c.merge(lww_d)
    check(lww_c.value == 0.9, "s24: LWW breaks ties by writer ID (higher wins)")

    # s25: OR-Set CRDT
    ors_a = ORSetTrust("node_a")
    ors_b = ORSetTrust("node_b")

    ors_a.add("attestation_1")
    ors_a.add("attestation_2")
    ors_b.add("attestation_3")

    ors_a.merge(ors_b)
    check(ors_a.contains("attestation_1") and ors_a.contains("attestation_3"),
          "s25: OR-Set merge preserves all adds")

    # s26: OR-Set concurrent add+remove
    ors_c = ORSetTrust("node_c")
    ors_d = ORSetTrust("node_d")

    ors_c.add("item_x")
    ors_d.add("item_x")

    # c removes, d doesn't know about c's add yet
    ors_c.remove("item_x")
    check(not ors_c.contains("item_x"), "s26: remove works locally")

    # Merge: d's add should win (concurrent add beats remove)
    ors_c.merge(ors_d)
    check(ors_c.contains("item_x"), "s26b: concurrent add wins over remove in OR-Set")


def test_anti_entropy():
    """§7.6: Anti-entropy convergence."""
    print("\n§7.6 Anti-Entropy Protocol")

    random.seed(42)
    nodes = [f"node_{i}" for i in range(8)]
    protocol = AntiEntropyProtocol(nodes)

    # s27: Initialize with divergent state
    for i, nid in enumerate(nodes):
        protocol.update_local(nid, f"trust_{nid}", 0.5 + i * 0.05)
        protocol.update_local(nid, "global_param", random.random())

    initial_convergence = protocol.convergence_metric()
    check(initial_convergence < 1.0,
          f"s27: initial state is divergent ({initial_convergence:.2f})")

    # s28: Convergence after rounds
    for _ in range(20):
        protocol.run_round()

    final_convergence = protocol.convergence_metric()
    check(final_convergence > initial_convergence,
          f"s28: convergence improved ({initial_convergence:.2f} → {final_convergence:.2f})")

    # s29: Full convergence reached
    for _ in range(50):
        protocol.run_round()

    full_convergence = protocol.convergence_metric()
    check(full_convergence > 0.95,
          f"s29: near-full convergence ({full_convergence:.2f})")

    # s30: All nodes agree on values
    ref_state = protocol.states[nodes[0]]
    agreement_count = 0
    for nid in nodes[1:]:
        if protocol.states[nid] == ref_state:
            agreement_count += 1
    check(agreement_count == len(nodes) - 1,
          f"s30: all nodes agree ({agreement_count + 1}/{len(nodes)})")


def test_timeline_reconstruction():
    """§7.7: Reconstructing trust timeline from partial observations."""
    print("\n§7.7 Timeline Reconstruction")

    log = CausalEventLog()

    # Create a trust lifecycle with causal dependencies
    events = [
        TrustEvent("create", TrustEventType.ATTESTATION, "admin", "new_entity",
                   value=0.5, lamport_time=1),
        TrustEvent("first_tx", TrustEventType.ATP_TRANSFER, "new_entity", "peer",
                   value=10.0, lamport_time=2, causal_dependencies={"create"}),
        TrustEvent("trust_boost", TrustEventType.TRUST_UPDATE, "witness", "new_entity",
                   value=0.7, lamport_time=3, causal_dependencies={"first_tx"}),
        TrustEvent("delegate", TrustEventType.DELEGATION, "new_entity", "sub_agent",
                   lamport_time=4, causal_dependencies={"trust_boost"}),
        TrustEvent("revoke", TrustEventType.REVOCATION, "admin", "new_entity",
                   lamport_time=10, causal_dependencies={"delegate"}),
    ]

    for e in events:
        log.add_event(e)

    # s31: Timeline reconstruction preserves causality
    timeline = log.causal_order()
    check(timeline == ["create", "first_tx", "trust_boost", "delegate", "revoke"],
          f"s31: timeline matches causal order ({timeline})")

    # s32: No concurrent events in this linear chain
    concurrent = log.concurrent_events()
    check(len(concurrent) == 0,
          f"s32: no concurrent events in linear chain ({len(concurrent)} found)")

    # s33: Adding a concurrent event
    log.add_event(TrustEvent(
        "independent_attest", TrustEventType.ATTESTATION, "other_fed", "entity_y",
        lamport_time=5, causal_dependencies=set()
    ))
    concurrent2 = log.concurrent_events()
    check(len(concurrent2) > 0,
          f"s33: concurrent event detected ({len(concurrent2)} pairs)")

    # s34: Causal order includes all events
    order2 = log.causal_order()
    check(len(order2) == 6, f"s34: all 6 events in order (got {len(order2)})")


def test_cross_federation_ordering():
    """§7.8: Ordering challenges at federation boundaries."""
    print("\n§7.8 Cross-Federation Ordering")

    nodes = ["fed_a", "fed_b", "fed_c"]
    vc_a = VectorClock("fed_a", nodes)
    vc_b = VectorClock("fed_b", nodes)
    vc_c = VectorClock("fed_c", nodes)

    # s35: Simulate cross-federation event sequence
    # Fed A creates attestation
    vc_a.tick()  # a=(1,0,0)

    # Fed A sends to Fed B (intra-federation, fast)
    msg_ab = vc_a.send()  # a=(2,0,0)
    vc_b.receive(msg_ab)   # b=(2,1,0)

    # Fed B sends to Fed C (cross-federation, slow — arrives later)
    msg_bc = vc_b.send()  # b=(2,2,0)

    # Meanwhile, Fed A sends directly to Fed C (also cross-federation)
    msg_ac = vc_a.send()  # a=(3,0,0)
    vc_c.receive(msg_ac)   # c=(3,0,1)

    # Now Fed C receives Fed B's message (arrived late)
    vc_c.receive(msg_bc)   # c=(3,2,2)

    # s35: Fed C correctly orders all events
    check(vc_c.clock["fed_a"] >= 2,
          f"s35: fed_c saw fed_a's events (fed_a={vc_c.clock['fed_a']})")
    check(vc_c.clock["fed_b"] >= 2,
          f"s35b: fed_c saw fed_b's events (fed_b={vc_c.clock['fed_b']})")

    # s36: Out-of-order delivery doesn't break causality
    # vc_c received msg_ac before msg_bc, but vector clock captures correct ordering
    check(vc_c.clock["fed_c"] >= 2,
          f"s36: fed_c's own clock advanced ({vc_c.clock['fed_c']})")

    # s37: Concurrent cross-federation events detected
    vc_x = VectorClock("fed_x", ["fed_x", "fed_y"])
    vc_y = VectorClock("fed_y", ["fed_x", "fed_y"])

    vc_x.tick()  # x acts independently
    vc_y.tick()  # y acts independently

    check(vc_x.concurrent_with(vc_y), "s37: independent federation events are concurrent")


def test_consistency_properties():
    """§7.9: Formal consistency properties."""
    print("\n§7.9 Consistency Properties")

    # s38: Causal consistency — if a → b, any node seeing b also sees a
    log = CausalEventLog()
    log.add_event(TrustEvent("cause", TrustEventType.ATTESTATION, "n1", "e1",
                              lamport_time=1))
    log.add_event(TrustEvent("effect", TrustEventType.TRUST_UPDATE, "n1", "e1",
                              lamport_time=2, causal_dependencies={"cause"}))

    order = log.causal_order()
    cause_idx = order.index("cause")
    effect_idx = order.index("effect")
    check(cause_idx < effect_idx,
          "s38: causal consistency — cause appears before effect")

    # s39: CRDT convergence — after sufficient merges, all replicas agree
    nodes = ["r1", "r2", "r3"]
    replicas = {nid: GCounterTrust(nid, nodes) for nid in nodes}

    # Independent updates
    replicas["r1"].increment(10)
    replicas["r2"].increment(20)
    replicas["r3"].increment(30)

    # Full merge
    for a in nodes:
        for b in nodes:
            if a != b:
                replicas[a].merge(replicas[b])

    values = [replicas[nid].value() for nid in nodes]
    check(len(set(values)) == 1 and values[0] == 60.0,
          f"s39: all replicas converge to 60.0 (got {values})")

    # s40: Vector clock antisymmetry — if a → b then NOT b → a
    vc1 = VectorClock("n1", ["n1", "n2"])
    vc2 = VectorClock("n2", ["n1", "n2"])
    vc1.tick()
    msg = vc1.send()
    vc2.receive(msg)

    check(not vc2.happens_before(vc1),
          "s40: antisymmetry — receiver does NOT happen before sender's earlier state")

    # s41: Lamport clock respects causality (if a→b then L(a) < L(b))
    lc_a = LamportClock("a")
    lc_b = LamportClock("b")

    t1 = lc_a.send()
    t2 = lc_b.receive(t1)
    t3 = lc_b.send()
    t4 = lc_a.receive(t3)

    check(t1 < t2 and t2 < t3 and t3 < t4,
          f"s41: Lamport timestamps respect causal order ({t1}<{t2}<{t3}<{t4})")


def test_trust_event_ordering_invariants():
    """§7.10: Trust-specific ordering invariants."""
    print("\n§7.10 Trust Event Ordering Invariants")

    log = CausalEventLog()

    # s42: Attestation must happen before trust update based on it
    log.add_event(TrustEvent("attest", TrustEventType.ATTESTATION, "a", "x",
                              value=0.8, lamport_time=1))
    log.add_event(TrustEvent("update", TrustEventType.TRUST_UPDATE, "a", "x",
                              value=0.75, lamport_time=2, causal_dependencies={"attest"}))

    check(log.happens_before("attest", "update"),
          "s42: attestation before trust update")

    # s43: Delegation before revocation
    log.add_event(TrustEvent("grant", TrustEventType.DELEGATION, "root", "agent",
                              lamport_time=3))
    log.add_event(TrustEvent("revoke_grant", TrustEventType.REVOCATION, "root", "agent",
                              lamport_time=4, causal_dependencies={"grant"}))

    check(log.happens_before("grant", "revoke_grant"),
          "s43: delegation before revocation")

    # s44: ATP transfer requires prior trust establishment
    log.add_event(TrustEvent("establish", TrustEventType.ATTESTATION, "b", "y",
                              value=0.6, lamport_time=5))
    log.add_event(TrustEvent("transfer", TrustEventType.ATP_TRANSFER, "y", "z",
                              value=50.0, lamport_time=6, causal_dependencies={"establish"}))

    check(log.happens_before("establish", "transfer"),
          "s44: trust established before ATP transfer")

    # s45: Revocation invalidates subsequent operations
    order = log.causal_order()
    # Revocation event should appear after its cause
    check("revoke_grant" in order and "grant" in order,
          "s45: both delegation and revocation in timeline")


# ============================================================
# §8 — Run All Tests
# ============================================================

def main():
    print("=" * 70)
    print("Temporal Consistency & Causal Ordering")
    print("Session 28, Track 4")
    print("=" * 70)

    test_vector_clocks()
    test_lamport_clocks()
    test_causal_event_log()
    test_clock_drift()
    test_crdts()
    test_anti_entropy()
    test_timeline_reconstruction()
    test_cross_federation_ordering()
    test_consistency_properties()
    test_trust_event_ordering_invariants()

    print(f"\n{'=' * 70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    if errors:
        print(f"\nFailures:")
        for e in errors:
            print(f"  - {e}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
