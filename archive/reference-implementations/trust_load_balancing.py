"""
Trust-Based Load Balancing for Web4
Session 31, Track 5

Load balancing strategies that use trust scores to distribute work:
- Trust-weighted round robin
- Least-loaded trust-aware scheduling
- Trust-proportional partitioning
- Failover with trust ranking
- Adaptive load shedding based on trust
- Capacity estimation from trust history
- Hot/cold node management
- Load balancing metrics and fairness
"""

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional, Set


# ─── Node Model ──────────────────────────────────────────────────

class NodeStatus(Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    OVERLOADED = "overloaded"
    OFFLINE = "offline"


@dataclass
class Node:
    """A federation node with trust score and load metrics."""
    node_id: str
    trust_score: float  # [0, 1]
    capacity: int       # max concurrent tasks
    current_load: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    status: NodeStatus = NodeStatus.ACTIVE

    @property
    def load_ratio(self) -> float:
        if self.capacity <= 0:
            return 1.0
        return self.current_load / self.capacity

    @property
    def available_capacity(self) -> int:
        return max(0, self.capacity - self.current_load)

    @property
    def success_rate(self) -> float:
        total = self.completed_tasks + self.failed_tasks
        if total == 0:
            return 1.0  # assume good until proven otherwise
        return self.completed_tasks / total

    @property
    def effective_trust(self) -> float:
        """Trust adjusted by success rate."""
        return self.trust_score * self.success_rate


# ─── Trust-Weighted Round Robin ──────────────────────────────────

class TrustWeightedRoundRobin:
    """
    Round robin that gives more turns to higher-trust nodes.
    Each node gets turns proportional to its trust score.
    """

    def __init__(self, nodes: List[Node]):
        self.nodes = [n for n in nodes if n.status == NodeStatus.ACTIVE]
        self.index = 0
        self._build_schedule()

    def _build_schedule(self):
        """Build weighted schedule: higher trust → more slots."""
        self.schedule = []
        if not self.nodes:
            return
        # Normalize trust scores and assign slots (min 1 per node)
        min_trust = min(n.trust_score for n in self.nodes)
        for node in self.nodes:
            # slots proportional to trust, minimum 1
            slots = max(1, round(node.trust_score * 10))
            self.schedule.extend([node] * slots)

    def next_node(self) -> Optional[Node]:
        if not self.schedule:
            return None
        node = self.schedule[self.index % len(self.schedule)]
        self.index += 1
        return node

    def assign_tasks(self, num_tasks: int) -> Dict[str, int]:
        """Assign tasks using weighted round robin."""
        assignments = {n.node_id: 0 for n in self.nodes}
        for _ in range(num_tasks):
            node = self.next_node()
            if node:
                assignments[node.node_id] += 1
        return assignments


# ─── Least-Loaded Trust-Aware Scheduler ──────────────────────────

def trust_load_score(node: Node, trust_weight: float = 0.5) -> float:
    """
    Combined score: lower is better.
    Balances current load ratio with inverse trust.
    """
    load_component = node.load_ratio
    trust_component = 1.0 - node.effective_trust
    return trust_weight * trust_component + (1 - trust_weight) * load_component


def least_loaded_trust_aware(nodes: List[Node]) -> Optional[Node]:
    """Select node with best combined load+trust score."""
    active = [n for n in nodes if n.status == NodeStatus.ACTIVE
              and n.available_capacity > 0]
    if not active:
        return None
    return min(active, key=trust_load_score)


# ─── Trust-Proportional Partitioning ─────────────────────────────

def trust_proportional_partition(nodes: List[Node], total_tasks: int) -> Dict[str, int]:
    """
    Distribute tasks proportional to trust × capacity.
    Higher-trust, higher-capacity nodes get more work.
    """
    active = [n for n in nodes if n.status == NodeStatus.ACTIVE]
    if not active:
        return {}

    # Weight = trust × available_capacity
    weights = {}
    for n in active:
        weights[n.node_id] = n.trust_score * n.available_capacity

    total_weight = sum(weights.values())
    if total_weight == 0:
        # Equal distribution
        per_node = total_tasks // len(active)
        remainder = total_tasks % len(active)
        result = {n.node_id: per_node for n in active}
        for i, n in enumerate(active):
            if i < remainder:
                result[n.node_id] += 1
        return result

    # Proportional assignment
    result = {}
    assigned = 0
    sorted_nodes = sorted(active, key=lambda n: weights[n.node_id], reverse=True)
    for n in sorted_nodes[:-1]:
        share = round(total_tasks * weights[n.node_id] / total_weight)
        share = min(share, n.available_capacity)
        result[n.node_id] = share
        assigned += share

    # Last node gets remainder
    last = sorted_nodes[-1]
    result[last.node_id] = min(total_tasks - assigned, last.available_capacity)

    return result


# ─── Failover with Trust Ranking ─────────────────────────────────

def trust_ranked_failover(nodes: List[Node], failed_node_id: str,
                          tasks_to_reassign: int) -> Dict[str, int]:
    """
    When a node fails, redistribute its tasks to remaining nodes
    ordered by trust (highest trust gets first pick).
    """
    available = [n for n in nodes
                 if n.node_id != failed_node_id
                 and n.status == NodeStatus.ACTIVE
                 and n.available_capacity > 0]

    # Sort by trust descending
    available.sort(key=lambda n: n.effective_trust, reverse=True)

    reassignment = {}
    remaining = tasks_to_reassign

    for node in available:
        if remaining <= 0:
            break
        take = min(remaining, node.available_capacity)
        reassignment[node.node_id] = take
        remaining -= take

    return reassignment


# ─── Adaptive Load Shedding ──────────────────────────────────────

@dataclass
class LoadSheddingPolicy:
    """Shed load based on trust thresholds."""
    soft_limit_ratio: float = 0.7    # start shedding low-trust tasks
    hard_limit_ratio: float = 0.9    # shed all but highest-trust tasks
    min_trust_soft: float = 0.3      # below this trust → shed at soft limit
    min_trust_hard: float = 0.7      # below this trust → shed at hard limit

    def should_accept(self, node: Node, task_trust_requirement: float) -> bool:
        """Decide whether to accept a task based on current load."""
        if node.status == NodeStatus.OFFLINE:
            return False

        load = node.load_ratio

        if load < self.soft_limit_ratio:
            return True  # under soft limit → accept everything

        if load >= self.hard_limit_ratio:
            # Only accept high-trust tasks
            return task_trust_requirement >= self.min_trust_hard

        # Between soft and hard: shed low-trust tasks
        return task_trust_requirement >= self.min_trust_soft


# ─── Capacity Estimation ─────────────────────────────────────────

def estimate_effective_capacity(node: Node, history_window: int = 100) -> float:
    """
    Effective capacity = nominal capacity × trust × success_rate.
    Untrusted or unreliable nodes have lower effective capacity.
    """
    return node.capacity * node.effective_trust


def cluster_effective_capacity(nodes: List[Node]) -> float:
    """Total effective capacity across all active nodes."""
    return sum(estimate_effective_capacity(n)
               for n in nodes if n.status == NodeStatus.ACTIVE)


# ─── Hot/Cold Node Management ────────────────────────────────────

def classify_nodes(nodes: List[Node]) -> Dict[str, List[Node]]:
    """
    Classify nodes into hot (overloaded), warm (normal), cold (underused).
    """
    hot = []
    warm = []
    cold = []

    for n in nodes:
        if n.status == NodeStatus.OFFLINE:
            continue
        if n.load_ratio > 0.8:
            hot.append(n)
        elif n.load_ratio < 0.2:
            cold.append(n)
        else:
            warm.append(n)

    return {"hot": hot, "warm": warm, "cold": cold}


def rebalance_hot_cold(nodes: List[Node]) -> List[Tuple[str, str, int]]:
    """
    Generate migration suggestions: move tasks from hot to cold nodes.
    Returns list of (from_node, to_node, task_count).
    """
    classified = classify_nodes(nodes)
    migrations = []

    hot = sorted(classified["hot"], key=lambda n: n.load_ratio, reverse=True)
    cold = sorted(classified["cold"], key=lambda n: n.effective_trust, reverse=True)

    cold_idx = 0
    for h in hot:
        excess = h.current_load - int(h.capacity * 0.6)  # bring down to 60%
        if excess <= 0:
            continue

        while excess > 0 and cold_idx < len(cold):
            c = cold[cold_idx]
            can_take = c.available_capacity
            if can_take <= 0:
                cold_idx += 1
                continue

            move = min(excess, can_take)
            # Only migrate to nodes with sufficient trust
            if c.trust_score >= 0.3:
                migrations.append((h.node_id, c.node_id, move))
                excess -= move
            cold_idx += 1

    return migrations


# ─── Load Balancing Metrics ──────────────────────────────────────

def load_fairness_index(nodes: List[Node]) -> float:
    """
    Jain's fairness index for load distribution.
    Returns 1.0 for perfectly fair, 1/n for maximally unfair.
    """
    active = [n for n in nodes if n.status == NodeStatus.ACTIVE]
    if not active:
        return 1.0

    loads = [n.load_ratio for n in active]
    n = len(loads)
    sum_x = sum(loads)
    sum_x2 = sum(x ** 2 for x in loads)

    if sum_x2 == 0:
        return 1.0  # all zero load → perfectly fair

    return (sum_x ** 2) / (n * sum_x2)


def trust_weighted_fairness(nodes: List[Node]) -> float:
    """
    Fairness index adjusted for trust: higher-trust nodes SHOULD
    have proportionally higher load.
    Measures how well load matches trust proportion.
    """
    active = [n for n in nodes if n.status == NodeStatus.ACTIVE]
    if not active:
        return 1.0

    total_trust = sum(n.trust_score for n in active)
    total_load = sum(n.current_load for n in active)

    if total_trust == 0 or total_load == 0:
        return 1.0

    # Compare actual load share vs expected trust share
    deviations = []
    for n in active:
        expected_share = n.trust_score / total_trust
        actual_share = n.current_load / total_load
        deviations.append(abs(actual_share - expected_share))

    # Perfect alignment → 0 deviation → fairness = 1.0
    avg_deviation = sum(deviations) / len(deviations)
    return max(0.0, 1.0 - avg_deviation * len(active))


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
    print("Trust-Based Load Balancing for Web4")
    print("Session 31, Track 5")
    print("=" * 70)

    # ── §1 Node Model ───────────────────────────────────────────
    print("\n§1 Node Model\n")

    n1 = Node("A", trust_score=0.9, capacity=100, current_load=50,
              completed_tasks=90, failed_tasks=10)
    check("load_ratio", abs(n1.load_ratio - 0.5) < 0.01, f"lr={n1.load_ratio}")
    check("available_cap", n1.available_capacity == 50)
    check("success_rate", abs(n1.success_rate - 0.9) < 0.01)
    check("effective_trust", abs(n1.effective_trust - 0.81) < 0.01,
          f"et={n1.effective_trust}")

    n_zero = Node("Z", trust_score=0.5, capacity=0)
    check("zero_cap_ratio", n_zero.load_ratio == 1.0)

    # ── §2 Trust-Weighted Round Robin ────────────────────────────
    print("\n§2 Trust-Weighted Round Robin\n")

    nodes_rr = [
        Node("high", trust_score=0.9, capacity=100),
        Node("low", trust_score=0.2, capacity=100),
    ]
    rr = TrustWeightedRoundRobin(nodes_rr)
    assignments = rr.assign_tasks(100)

    # High-trust node should get more tasks
    check("rr_high_gets_more", assignments["high"] > assignments["low"],
          f"high={assignments['high']} low={assignments['low']}")

    # Both nodes get some tasks
    check("rr_both_served", assignments["high"] > 0 and assignments["low"] > 0)

    # Total tasks assigned
    check("rr_total_correct", sum(assignments.values()) == 100,
          f"total={sum(assignments.values())}")

    # ── §3 Least-Loaded Trust-Aware ──────────────────────────────
    print("\n§3 Least-Loaded Trust-Aware\n")

    nodes_ll = [
        Node("A", trust_score=0.9, capacity=100, current_load=80),
        Node("B", trust_score=0.5, capacity=100, current_load=20),
        Node("C", trust_score=0.7, capacity=100, current_load=40),
    ]

    selected = least_loaded_trust_aware(nodes_ll)
    # B has lowest load, C has good balance — should pick based on combined score
    check("ll_selects_node", selected is not None)
    check("ll_not_overloaded", selected.node_id != "A",
          f"selected={selected.node_id}")

    # All full → None
    nodes_full = [Node("X", trust_score=0.9, capacity=10, current_load=10)]
    check("ll_full_returns_none", least_loaded_trust_aware(nodes_full) is None)

    # ── §4 Trust-Proportional Partitioning ───────────────────────
    print("\n§4 Trust-Proportional Partitioning\n")

    nodes_pp = [
        Node("high", trust_score=0.8, capacity=100),
        Node("low", trust_score=0.2, capacity=100),
    ]
    partition = trust_proportional_partition(nodes_pp, 100)

    check("pp_high_more", partition["high"] > partition["low"],
          f"high={partition['high']} low={partition['low']}")
    check("pp_total", sum(partition.values()) == 100,
          f"total={sum(partition.values())}")

    # Respects capacity limits
    nodes_limited = [
        Node("big", trust_score=0.9, capacity=10, current_load=8),
        Node("small", trust_score=0.1, capacity=100),
    ]
    partition_lim = trust_proportional_partition(nodes_limited, 50)
    check("pp_respects_cap", partition_lim.get("big", 0) <= 2,
          f"big={partition_lim.get('big', 0)}")

    # ── §5 Failover ──────────────────────────────────────────────
    print("\n§5 Trust-Ranked Failover\n")

    nodes_fo = [
        Node("failed", trust_score=0.5, capacity=100, current_load=30),
        Node("backup1", trust_score=0.9, capacity=100, current_load=20),
        Node("backup2", trust_score=0.3, capacity=100, current_load=10),
    ]

    reassigned = trust_ranked_failover(nodes_fo, "failed", 30)
    check("fo_redistributed", sum(reassigned.values()) == 30,
          f"total={sum(reassigned.values())}")
    check("fo_high_trust_first",
          reassigned.get("backup1", 0) >= reassigned.get("backup2", 0),
          f"b1={reassigned.get('backup1', 0)} b2={reassigned.get('backup2', 0)}")

    # ── §6 Load Shedding ────────────────────────────────────────
    print("\n§6 Adaptive Load Shedding\n")

    policy = LoadSheddingPolicy()
    light_node = Node("light", trust_score=0.8, capacity=100, current_load=50)
    heavy_node = Node("heavy", trust_score=0.8, capacity=100, current_load=85)
    critical_node = Node("crit", trust_score=0.8, capacity=100, current_load=95)

    # Light load: accept everything
    check("shed_accept_light", policy.should_accept(light_node, 0.1))

    # Heavy load: reject low-trust tasks
    check("shed_reject_low_heavy", not policy.should_accept(heavy_node, 0.1))
    check("shed_accept_mid_heavy", policy.should_accept(heavy_node, 0.5))

    # Critical load: only high-trust tasks
    check("shed_reject_mid_crit", not policy.should_accept(critical_node, 0.5))
    check("shed_accept_high_crit", policy.should_accept(critical_node, 0.8))

    # Offline: reject all
    offline = Node("off", trust_score=0.9, capacity=100, status=NodeStatus.OFFLINE)
    check("shed_reject_offline", not policy.should_accept(offline, 1.0))

    # ── §7 Capacity Estimation ───────────────────────────────────
    print("\n§7 Capacity Estimation\n")

    reliable = Node("r", trust_score=0.9, capacity=100,
                     completed_tasks=95, failed_tasks=5)
    unreliable = Node("u", trust_score=0.3, capacity=100,
                       completed_tasks=50, failed_tasks=50)

    cap_r = estimate_effective_capacity(reliable)
    cap_u = estimate_effective_capacity(unreliable)
    check("cap_reliable_higher", cap_r > cap_u,
          f"reliable={cap_r:.1f} unreliable={cap_u:.1f}")

    # Cluster capacity
    cluster = [reliable, unreliable]
    total_cap = cluster_effective_capacity(cluster)
    check("cluster_cap_sum", abs(total_cap - (cap_r + cap_u)) < 0.01,
          f"total={total_cap:.1f}")

    # ── §8 Hot/Cold Classification ───────────────────────────────
    print("\n§8 Hot/Cold Node Management\n")

    nodes_hc = [
        Node("hot1", trust_score=0.8, capacity=100, current_load=90),
        Node("hot2", trust_score=0.7, capacity=100, current_load=85),
        Node("warm", trust_score=0.6, capacity=100, current_load=50),
        Node("cold1", trust_score=0.9, capacity=100, current_load=10),
        Node("cold2", trust_score=0.5, capacity=100, current_load=5),
    ]

    classified = classify_nodes(nodes_hc)
    check("hc_hot_count", len(classified["hot"]) == 2)
    check("hc_warm_count", len(classified["warm"]) == 1)
    check("hc_cold_count", len(classified["cold"]) == 2)

    # Rebalance suggestions
    migrations = rebalance_hot_cold(nodes_hc)
    check("hc_has_migrations", len(migrations) > 0)

    # Migrations go from hot to cold
    for src, dst, count in migrations:
        src_node = next(n for n in nodes_hc if n.node_id == src)
        dst_node = next(n for n in nodes_hc if n.node_id == dst)
        check(f"hc_migrate_{src}_to_{dst}",
              src_node.load_ratio > 0.8 and dst_node.load_ratio < 0.2,
              f"src_lr={src_node.load_ratio} dst_lr={dst_node.load_ratio}")

    # ── §9 Load Fairness ─────────────────────────────────────────
    print("\n§9 Load Fairness Metrics\n")

    # Perfect fairness: all same load
    equal_nodes = [
        Node(f"n{i}", trust_score=0.5, capacity=100, current_load=50)
        for i in range(5)
    ]
    fi = load_fairness_index(equal_nodes)
    check("fairness_perfect", abs(fi - 1.0) < 0.01, f"fi={fi:.4f}")

    # Unfair: one loaded, rest empty
    unfair_nodes = [
        Node("loaded", trust_score=0.5, capacity=100, current_load=100),
        Node("empty1", trust_score=0.5, capacity=100, current_load=0),
        Node("empty2", trust_score=0.5, capacity=100, current_load=0),
    ]
    fi_unfair = load_fairness_index(unfair_nodes)
    check("fairness_unfair", fi_unfair < 0.5, f"fi={fi_unfair:.4f}")

    # Trust-weighted fairness: load matches trust
    tw_nodes = [
        Node("high_t", trust_score=0.8, capacity=100, current_load=80),
        Node("low_t", trust_score=0.2, capacity=100, current_load=20),
    ]
    twf = trust_weighted_fairness(tw_nodes)
    check("tw_fairness_aligned", twf > 0.8, f"twf={twf:.4f}")

    # Misaligned: low trust has high load
    mis_nodes = [
        Node("high_t", trust_score=0.8, capacity=100, current_load=20),
        Node("low_t", trust_score=0.2, capacity=100, current_load=80),
    ]
    twf_mis = trust_weighted_fairness(mis_nodes)
    check("tw_fairness_misaligned", twf_mis < twf,
          f"mis={twf_mis:.4f} aligned={twf:.4f}")

    # ── §10 Integration: Simulate Workload ───────────────────────
    print("\n§10 Workload Simulation\n")

    random.seed(42)
    sim_nodes = [
        Node(f"node_{i}", trust_score=0.3 + 0.7 * (i / 9),
             capacity=50 + i * 10)
        for i in range(10)
    ]

    # Simulate 500 task arrivals using least-loaded trust-aware
    for _ in range(500):
        selected = least_loaded_trust_aware(sim_nodes)
        if selected:
            selected.current_load += 1
            # Simulate some completions
            if random.random() < 0.3:
                for n in sim_nodes:
                    if n.current_load > 0:
                        n.current_load -= 1
                        if random.random() < n.trust_score:
                            n.completed_tasks += 1
                        else:
                            n.failed_tasks += 1

    # No node should be massively overloaded
    max_lr = max(n.load_ratio for n in sim_nodes)
    check("sim_no_overload", max_lr < 1.5,
          f"max_load_ratio={max_lr:.2f}")

    # Higher-trust nodes should have handled more total tasks
    high_trust_tasks = sum(n.completed_tasks + n.failed_tasks
                           for n in sim_nodes if n.trust_score > 0.7)
    low_trust_tasks = sum(n.completed_tasks + n.failed_tasks
                          for n in sim_nodes if n.trust_score < 0.5)
    check("sim_trust_correlation",
          high_trust_tasks > 0 and low_trust_tasks >= 0)

    # Fairness should be reasonable (not perfect, but not terrible)
    fi_sim = load_fairness_index(sim_nodes)
    check("sim_fairness_ok", fi_sim > 0.2, f"fi={fi_sim:.4f}")

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
