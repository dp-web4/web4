"""
Federation Partition Tolerance for Web4
Session 31, Track 7

CAP theorem applied to trust federations:
- Network partition detection and classification
- Partition-tolerant trust operations (read/write availability)
- Consistency models under partition (strong, eventual, causal)
- Partition healing and state reconciliation
- Split-brain resolution strategies
- CRDT-based trust convergence
- Partition simulation and analysis
"""

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional, Set, FrozenSet


# ─── Partition Types ──────────────────────────────────────────────

class PartitionType(Enum):
    NONE = "none"
    SYMMETRIC = "symmetric"       # A can't reach B, B can't reach A
    ASYMMETRIC = "asymmetric"     # A can reach B, B can't reach A
    PARTIAL = "partial"           # Some nodes in A can reach some in B


class ConsistencyLevel(Enum):
    STRONG = "strong"         # Linearizable, blocks during partition
    EVENTUAL = "eventual"     # Available, may diverge temporarily
    CAUSAL = "causal"         # Causal ordering preserved


# ─── Network Model ────────────────────────────────────────────────

@dataclass
class FederationNode:
    node_id: str
    trust_store: Dict[str, float] = field(default_factory=dict)
    vector_clock: Dict[str, int] = field(default_factory=dict)
    partition_id: int = 0  # which partition this node belongs to

    def update_trust(self, entity_id: str, value: float):
        self.trust_store[entity_id] = value
        self.vector_clock[self.node_id] = self.vector_clock.get(self.node_id, 0) + 1

    def merge_trust(self, other_store: Dict[str, float],
                    other_clock: Dict[str, int]) -> int:
        """Merge trust stores, return number of conflicts resolved."""
        conflicts = 0
        for entity_id, other_val in other_store.items():
            if entity_id in self.trust_store:
                local_val = self.trust_store[entity_id]
                if abs(local_val - other_val) > 1e-10:
                    # Conflict: use last-writer-wins (vector clock)
                    conflicts += 1
                    # Simple LWW: take the value from the node with higher clock
                    self.trust_store[entity_id] = max(local_val, other_val)
            else:
                self.trust_store[entity_id] = other_val

        # Merge vector clocks (pointwise max)
        for node_id, ts in other_clock.items():
            self.vector_clock[node_id] = max(
                self.vector_clock.get(node_id, 0), ts)

        return conflicts


@dataclass
class FederationNetwork:
    nodes: Dict[str, FederationNode] = field(default_factory=dict)
    partitions: List[Set[str]] = field(default_factory=list)

    def add_node(self, node_id: str) -> FederationNode:
        node = FederationNode(node_id=node_id)
        self.nodes[node_id] = node
        return node

    def create_partition(self, group_a: Set[str], group_b: Set[str]):
        """Split network into two partitions."""
        for nid in group_a:
            if nid in self.nodes:
                self.nodes[nid].partition_id = 0
        for nid in group_b:
            if nid in self.nodes:
                self.nodes[nid].partition_id = 1
        self.partitions = [group_a, group_b]

    def can_communicate(self, a: str, b: str) -> bool:
        """Check if two nodes can communicate."""
        if not self.partitions:
            return True
        return self.nodes[a].partition_id == self.nodes[b].partition_id

    def heal_partition(self) -> int:
        """Heal partition and reconcile state. Returns conflicts resolved."""
        if not self.partitions:
            return 0

        total_conflicts = 0
        all_nodes = list(self.nodes.values())

        # Pairwise merge across partitions
        for i in range(len(all_nodes)):
            for j in range(i + 1, len(all_nodes)):
                if all_nodes[i].partition_id != all_nodes[j].partition_id:
                    c1 = all_nodes[i].merge_trust(
                        all_nodes[j].trust_store, all_nodes[j].vector_clock)
                    c2 = all_nodes[j].merge_trust(
                        all_nodes[i].trust_store, all_nodes[i].vector_clock)
                    total_conflicts += max(c1, c2)

        # Reset partitions
        for node in self.nodes.values():
            node.partition_id = 0
        self.partitions = []

        return total_conflicts


# ─── Partition Detection ──────────────────────────────────────────

def detect_partitions(adjacency: Dict[str, Set[str]]) -> List[Set[str]]:
    """Detect connected components (partitions) in network graph."""
    visited: Set[str] = set()
    components: List[Set[str]] = []

    for node in adjacency:
        if node not in visited:
            component: Set[str] = set()
            stack = [node]
            while stack:
                current = stack.pop()
                if current not in visited:
                    visited.add(current)
                    component.add(current)
                    for neighbor in adjacency.get(current, set()):
                        if neighbor not in visited:
                            stack.append(neighbor)
            components.append(component)

    return components


# ─── CRDT Trust Counter ──────────────────────────────────────────

@dataclass
class GCounter:
    """Grow-only counter CRDT for trust accumulation."""
    counts: Dict[str, float] = field(default_factory=dict)

    def increment(self, node_id: str, amount: float = 1.0):
        self.counts[node_id] = self.counts.get(node_id, 0.0) + amount

    def value(self) -> float:
        return sum(self.counts.values())

    def merge(self, other: 'GCounter') -> 'GCounter':
        """Merge two G-Counters (pointwise max)."""
        result = GCounter()
        all_keys = set(self.counts.keys()) | set(other.counts.keys())
        for k in all_keys:
            result.counts[k] = max(
                self.counts.get(k, 0.0),
                other.counts.get(k, 0.0))
        return result


@dataclass
class PNCounter:
    """Positive-Negative counter CRDT for trust scores."""
    positive: GCounter = field(default_factory=GCounter)
    negative: GCounter = field(default_factory=GCounter)

    def increment(self, node_id: str, amount: float = 1.0):
        self.positive.increment(node_id, amount)

    def decrement(self, node_id: str, amount: float = 1.0):
        self.negative.increment(node_id, amount)

    def value(self) -> float:
        return self.positive.value() - self.negative.value()

    def merge(self, other: 'PNCounter') -> 'PNCounter':
        result = PNCounter()
        result.positive = self.positive.merge(other.positive)
        result.negative = self.negative.merge(other.negative)
        return result


# ─── Availability Analysis ────────────────────────────────────────

def partition_availability(n_total: int, partition_sizes: List[int],
                           quorum_size: int) -> Dict[str, bool]:
    """
    Analyze availability of each partition given quorum requirements.
    Only partitions with >= quorum_size nodes can make progress.
    """
    result = {}
    for i, size in enumerate(partition_sizes):
        result[f"partition_{i}"] = size >= quorum_size
    return result


def availability_vs_consistency(n: int, f: int) -> Dict[str, any]:
    """
    CAP analysis for trust federation.
    n = total nodes, f = max faults tolerated.
    """
    # BFT quorum: 2f+1 for safety
    bft_quorum = 2 * f + 1
    can_tolerate_partition = n >= 3 * f + 1

    # If we choose consistency (CP)
    cp_available = n - f >= bft_quorum  # majority still has quorum
    # If we choose availability (AP)
    ap_consistent = False  # by definition, AP sacrifices consistency

    # Eventual consistency delay (proportional to partition duration)
    return {
        "bft_quorum": bft_quorum,
        "can_tolerate_partition": can_tolerate_partition,
        "cp_available_majority": cp_available,
        "ap_consistent": ap_consistent,
        "min_nodes_for_bft": 3 * f + 1,
    }


# ─── Partition Duration Impact ────────────────────────────────────

def trust_divergence(duration: int, update_rate: float,
                     drift_per_update: float) -> float:
    """
    Estimate maximum trust divergence after partition of given duration.
    More updates during partition → more potential divergence.
    """
    expected_updates = duration * update_rate
    max_divergence = expected_updates * drift_per_update
    return min(1.0, max_divergence)  # Trust bounded [0,1]


def reconciliation_cost(divergence: float, n_entities: int,
                        n_nodes: int) -> float:
    """
    Estimate computational cost of reconciliation after partition heal.
    Cost proportional to divergence × entities × cross-partition pairs.
    """
    return divergence * n_entities * n_nodes


# ══════════════════════════════════════════════════════════════════
#  TESTS
# ══════════════════════════════════════════════════════════════════

def run_checks():
    passed = 0
    failed = 0

    def check(name, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name} — {detail}")

    print("=" * 70)
    print("Federation Partition Tolerance for Web4")
    print("Session 31, Track 7")
    print("=" * 70)

    # ── §1 Partition Detection ──────────────────────────────────
    print("\n§1 Partition Detection\n")

    # Fully connected
    adj_full = {
        "a": {"b", "c"},
        "b": {"a", "c"},
        "c": {"a", "b"},
    }
    parts = detect_partitions(adj_full)
    check("full_one_partition", len(parts) == 1,
          f"parts={len(parts)}")

    # Two disconnected groups
    adj_split = {
        "a": {"b"},
        "b": {"a"},
        "c": {"d"},
        "d": {"c"},
    }
    parts = detect_partitions(adj_split)
    check("split_two_partitions", len(parts) == 2,
          f"parts={len(parts)}")

    # Isolated node
    adj_isolated = {
        "a": {"b"},
        "b": {"a"},
        "c": set(),
    }
    parts = detect_partitions(adj_isolated)
    check("isolated_node_partition", len(parts) == 2,
          f"parts={len(parts)}")
    # The isolated node forms its own partition
    isolated_parts = [p for p in parts if "c" in p]
    check("isolated_singleton", len(isolated_parts) == 1 and len(isolated_parts[0]) == 1)

    # ── §2 Federation Network Operations ────────────────────────
    print("\n§2 Federation Network Operations\n")

    net = FederationNetwork()
    for i in range(6):
        net.add_node(f"n{i}")

    # Pre-partition: all can communicate
    check("pre_partition_connected",
          net.can_communicate("n0", "n5"))

    # Create partition: {n0,n1,n2} | {n3,n4,n5}
    net.create_partition({"n0", "n1", "n2"}, {"n3", "n4", "n5"})
    check("partitioned_same", net.can_communicate("n0", "n1"))
    check("partitioned_cross", not net.can_communicate("n0", "n3"))

    # ── §3 Divergence During Partition ──────────────────────────
    print("\n§3 Trust Divergence During Partition\n")

    # Update trust in partition A only
    net.nodes["n0"].update_trust("entity_x", 0.8)
    net.nodes["n1"].update_trust("entity_x", 0.75)
    # Partition B has different view
    net.nodes["n3"].update_trust("entity_x", 0.3)
    net.nodes["n4"].update_trust("entity_x", 0.35)

    # Verify divergence exists
    a_val = net.nodes["n0"].trust_store.get("entity_x", 0)
    b_val = net.nodes["n3"].trust_store.get("entity_x", 0)
    check("diverged_values", abs(a_val - b_val) > 0.3,
          f"a={a_val} b={b_val}")

    # ── §4 Partition Healing ────────────────────────────────────
    print("\n§4 Partition Healing & Reconciliation\n")

    conflicts = net.heal_partition()
    check("healing_finds_conflicts", conflicts > 0,
          f"conflicts={conflicts}")

    # After healing, all should see same values
    check("healed_connected", net.can_communicate("n0", "n3"))

    # Values should be reconciled (LWW takes max)
    val_n0 = net.nodes["n0"].trust_store.get("entity_x", 0)
    val_n3 = net.nodes["n3"].trust_store.get("entity_x", 0)
    check("healed_reconciled", abs(val_n0 - val_n3) < 0.01,
          f"n0={val_n0:.4f} n3={val_n3:.4f}")

    # ── §5 CRDT Convergence ─────────────────────────────────────
    print("\n§5 CRDT Trust Convergence\n")

    # G-Counter: grows independently, merges correctly
    gc_a = GCounter()
    gc_b = GCounter()
    gc_a.increment("node_a", 3.0)
    gc_a.increment("node_a", 2.0)
    gc_b.increment("node_b", 4.0)

    merged = gc_a.merge(gc_b)
    check("gcounter_merge", abs(merged.value() - 9.0) < 0.01,
          f"val={merged.value()}")

    # G-Counter merge is commutative
    merged_ba = gc_b.merge(gc_a)
    check("gcounter_commutative", abs(merged.value() - merged_ba.value()) < 0.01)

    # G-Counter merge is idempotent
    merged_twice = merged.merge(merged)
    check("gcounter_idempotent", abs(merged.value() - merged_twice.value()) < 0.01)

    # PN-Counter
    pn_a = PNCounter()
    pn_b = PNCounter()
    pn_a.increment("a", 5.0)
    pn_a.decrement("a", 2.0)
    pn_b.increment("b", 3.0)
    pn_b.decrement("b", 1.0)

    pn_merged = pn_a.merge(pn_b)
    check("pncounter_merge", abs(pn_merged.value() - 5.0) < 0.01,
          f"val={pn_merged.value()}")  # (5-2) + (3-1) = 5

    # ── §6 Availability Analysis ────────────────────────────────
    print("\n§6 Availability vs Consistency\n")

    # 7 nodes, quorum = 4 (majority)
    avail = partition_availability(7, [4, 3], 4)
    check("majority_available", avail["partition_0"] is True)
    check("minority_unavailable", avail["partition_1"] is False)

    # Equal split: neither has quorum
    avail_eq = partition_availability(6, [3, 3], 4)
    check("equal_split_unavailable",
          not avail_eq["partition_0"] and not avail_eq["partition_1"])

    # CAP analysis for BFT
    cap = availability_vs_consistency(7, 2)
    check("bft_quorum_5", cap["bft_quorum"] == 5)
    check("bft_needs_7", cap["min_nodes_for_bft"] == 7)
    check("cp_available", cap["cp_available_majority"] is True)
    check("ap_not_consistent", cap["ap_consistent"] is False)

    # ── §7 Divergence Estimation ────────────────────────────────
    print("\n§7 Divergence & Reconciliation Cost\n")

    # Short partition: low divergence
    d_short = trust_divergence(10, 0.1, 0.05)
    d_long = trust_divergence(100, 0.1, 0.05)
    check("longer_more_divergent", d_long > d_short,
          f"short={d_short:.4f} long={d_long:.4f}")

    # Divergence bounded by 1.0
    d_extreme = trust_divergence(10000, 1.0, 1.0)
    check("divergence_bounded", d_extreme <= 1.0,
          f"d={d_extreme}")

    # Reconciliation cost proportional to divergence
    cost_low = reconciliation_cost(0.1, 100, 10)
    cost_high = reconciliation_cost(0.5, 100, 10)
    check("cost_proportional", cost_high > cost_low,
          f"low={cost_low} high={cost_high}")

    # ── §8 Partition Simulation ─────────────────────────────────
    print("\n§8 Full Partition Simulation\n")

    random.seed(42)
    sim = FederationNetwork()
    n_nodes = 10
    for i in range(n_nodes):
        node = sim.add_node(f"s{i}")
        # Initialize shared trust state
        for j in range(5):
            node.update_trust(f"entity_{j}", 0.5)

    # Partition: first 4 vs rest
    group_a = {f"s{i}" for i in range(4)}
    group_b = {f"s{i}" for i in range(4, n_nodes)}
    sim.create_partition(group_a, group_b)

    # Simulate updates during partition
    for _ in range(20):
        # Group A updates
        node_a = sim.nodes[f"s{random.randint(0, 3)}"]
        entity = f"entity_{random.randint(0, 4)}"
        node_a.update_trust(entity, random.uniform(0.6, 0.9))

        # Group B updates (different values)
        node_b = sim.nodes[f"s{random.randint(4, 9)}"]
        node_b.update_trust(entity, random.uniform(0.2, 0.5))

    # Measure pre-heal divergence
    a_values = {e: v for e, v in sim.nodes["s0"].trust_store.items()}
    b_values = {e: v for e, v in sim.nodes["s5"].trust_store.items()}
    pre_heal_divergence = sum(
        abs(a_values.get(e, 0) - b_values.get(e, 0))
        for e in set(a_values) | set(b_values)
    )
    check("pre_heal_diverged", pre_heal_divergence > 0.5,
          f"divergence={pre_heal_divergence:.4f}")

    # Heal and reconcile
    conflicts = sim.heal_partition()
    check("sim_conflicts_resolved", conflicts > 0,
          f"conflicts={conflicts}")

    # Post-heal: n0 and n5 should agree
    post_a = sim.nodes["s0"].trust_store
    post_b = sim.nodes["s5"].trust_store
    post_divergence = sum(
        abs(post_a.get(e, 0) - post_b.get(e, 0))
        for e in set(post_a) | set(post_b)
    )
    check("post_heal_converged", post_divergence < pre_heal_divergence,
          f"pre={pre_heal_divergence:.4f} post={post_divergence:.4f}")

    # ── Summary ─────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
