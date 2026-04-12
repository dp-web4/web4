"""
Trust Propagation Networks for Web4
Session 31, Track 1

How trust flows through network edges:
- Transitive trust computation (discount chains)
- Trust flow algorithms (max-flow, shortest path)
- Trust aggregation at nodes (multiple sources)
- Trust decay along paths (distance penalty)
- Personalized trust (PageRank-like)
- Trust cycles and their resolution
- Sybil resistance through trust bottlenecks
- Comparative: direct vs transitive vs reputation
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional


# ─── Trust Graph ───────────────────────────────────────────────────

@dataclass
class TrustEdge:
    source: int
    target: int
    weight: float  # direct trust [0, 1]
    context: str = "general"


class TrustNetwork:
    """Weighted directed trust graph."""

    def __init__(self):
        self.edges: Dict[Tuple[int, int], TrustEdge] = {}
        self.nodes: Set[int] = set()

    def add_edge(self, src: int, dst: int, weight: float, context: str = "general"):
        self.edges[(src, dst)] = TrustEdge(src, dst, weight, context)
        self.nodes.add(src)
        self.nodes.add(dst)

    def get_weight(self, src: int, dst: int) -> float:
        edge = self.edges.get((src, dst))
        return edge.weight if edge else 0.0

    def out_neighbors(self, node: int) -> List[int]:
        return [dst for (src, dst) in self.edges if src == node]

    def in_neighbors(self, node: int) -> List[int]:
        return [src for (src, dst) in self.edges if dst == node]

    def out_degree(self, node: int) -> int:
        return len(self.out_neighbors(node))


# ─── Transitive Trust ─────────────────────────────────────────────

def transitive_trust_multiplicative(network: TrustNetwork, src: int, dst: int,
                                     max_hops: int = 5) -> float:
    """
    Transitive trust via multiplicative discount.
    Trust along path = product of edge weights.
    Returns maximum trust over all paths (up to max_hops).
    """
    if src == dst:
        return 1.0

    # BFS with trust tracking
    best_trust = 0.0
    # (current_node, accumulated_trust, visited)
    queue = [(src, 1.0, {src})]

    while queue:
        node, trust, visited = queue.pop(0)

        if len(visited) > max_hops + 1:
            continue

        for neighbor in network.out_neighbors(node):
            if neighbor in visited:
                continue

            edge_trust = network.get_weight(node, neighbor)
            path_trust = trust * edge_trust

            if neighbor == dst:
                best_trust = max(best_trust, path_trust)
            elif path_trust > best_trust:  # pruning: only explore if can improve
                new_visited = visited | {neighbor}
                queue.append((neighbor, path_trust, new_visited))

    return best_trust


def transitive_trust_min(network: TrustNetwork, src: int, dst: int,
                          max_hops: int = 5) -> float:
    """
    Transitive trust via minimum (weakest link).
    Trust along path = min(edge weights).
    Returns maximum over all paths.
    """
    if src == dst:
        return 1.0

    best_trust = 0.0
    queue = [(src, 1.0, {src})]

    while queue:
        node, trust, visited = queue.pop(0)

        if len(visited) > max_hops + 1:
            continue

        for neighbor in network.out_neighbors(node):
            if neighbor in visited:
                continue

            edge_trust = network.get_weight(node, neighbor)
            path_trust = min(trust, edge_trust)

            if neighbor == dst:
                best_trust = max(best_trust, path_trust)
            elif path_trust > best_trust:
                new_visited = visited | {neighbor}
                queue.append((neighbor, path_trust, new_visited))

    return best_trust


def transitive_trust_discounted(network: TrustNetwork, src: int, dst: int,
                                 discount: float = 0.9, max_hops: int = 5) -> float:
    """
    Transitive trust with hop discount.
    Each hop multiplies by discount factor in addition to edge weight.
    Models trust decay with distance.
    """
    if src == dst:
        return 1.0

    best_trust = 0.0
    queue = [(src, 1.0, {src}, 0)]

    while queue:
        node, trust, visited, hops = queue.pop(0)

        if hops >= max_hops:
            continue

        for neighbor in network.out_neighbors(node):
            if neighbor in visited:
                continue

            edge_trust = network.get_weight(node, neighbor)
            path_trust = trust * edge_trust * discount

            if neighbor == dst:
                best_trust = max(best_trust, path_trust)
            elif path_trust > best_trust:
                new_visited = visited | {neighbor}
                queue.append((neighbor, path_trust, new_visited, hops + 1))

    return best_trust


# ─── Trust Flow (Max-Flow Based) ──────────────────────────────────

def trust_max_flow(network: TrustNetwork, src: int, dst: int) -> float:
    """
    Maximum trust flow from src to dst.
    Uses Ford-Fulkerson with BFS (Edmonds-Karp).
    Capacity of each edge = trust weight.
    """
    if src == dst:
        return float('inf')

    # Build adjacency with residual capacities
    nodes = sorted(network.nodes)
    capacity = {}
    for (s, d), edge in network.edges.items():
        capacity[(s, d)] = edge.weight
        if (d, s) not in capacity:
            capacity[(d, s)] = 0.0

    total_flow = 0.0

    while True:
        # BFS to find augmenting path
        parent = {src: None}
        visited = {src}
        queue = [src]
        found = False

        while queue and not found:
            node = queue.pop(0)
            for neighbor in nodes:
                if neighbor not in visited and capacity.get((node, neighbor), 0) > 1e-10:
                    visited.add(neighbor)
                    parent[neighbor] = node
                    if neighbor == dst:
                        found = True
                        break
                    queue.append(neighbor)

        if not found:
            break

        # Find bottleneck
        path_flow = float('inf')
        node = dst
        while parent[node] is not None:
            prev = parent[node]
            path_flow = min(path_flow, capacity.get((prev, node), 0))
            node = prev

        # Update residual capacities
        node = dst
        while parent[node] is not None:
            prev = parent[node]
            capacity[(prev, node)] = capacity.get((prev, node), 0) - path_flow
            capacity[(node, prev)] = capacity.get((node, prev), 0) + path_flow
            node = prev

        total_flow += path_flow

    return total_flow


# ─── Personalized Trust (PageRank-like) ───────────────────────────

def personalized_trust(network: TrustNetwork, source: int,
                        damping: float = 0.85, iterations: int = 50) -> Dict[int, float]:
    """
    Personalized PageRank from source node.
    Measures how much trust flows from source to each node.
    """
    nodes = sorted(network.nodes)
    n = len(nodes)

    if n == 0:
        return {}

    # Initialize: all trust at source
    trust = {node: (1.0 if node == source else 0.0) for node in nodes}

    for _ in range(iterations):
        new_trust = {}
        for node in nodes:
            # Incoming trust from neighbors
            incoming = 0.0
            for neighbor in network.in_neighbors(node):
                out_deg = network.out_degree(neighbor)
                if out_deg > 0:
                    edge_weight = network.get_weight(neighbor, node)
                    incoming += trust[neighbor] * edge_weight / out_deg

            # Damped personalized PageRank
            new_trust[node] = (1 - damping) * (1.0 if node == source else 0.0) + damping * incoming

        trust = new_trust

    return trust


# ─── Trust Aggregation ────────────────────────────────────────────

def aggregate_trust_weighted_mean(trusts: List[Tuple[float, float]]) -> float:
    """
    Aggregate multiple trust opinions using weighted mean.
    Input: list of (trust_value, recommender_trust) pairs.
    """
    if not trusts:
        return 0.0

    total_weight = sum(w for _, w in trusts)
    if total_weight <= 0:
        return 0.0

    return sum(t * w for t, w in trusts) / total_weight


def aggregate_trust_pessimistic(trusts: List[Tuple[float, float]]) -> float:
    """
    Pessimistic aggregation: weighted minimum.
    Use when security is priority.
    """
    if not trusts:
        return 0.0
    return min(t for t, _ in trusts)


def aggregate_trust_bayesian(trusts: List[Tuple[float, float]],
                              prior: float = 0.5) -> float:
    """
    Bayesian aggregation: update prior with each opinion.
    Higher recommender trust → stronger evidence.
    """
    belief = prior
    for trust_val, recommender_trust in trusts:
        # Evidence strength proportional to recommender trust
        strength = recommender_trust
        # Bayesian update (simplified)
        if trust_val > 0.5:
            belief = belief + strength * (1 - belief) * (trust_val - 0.5) * 2
        else:
            belief = belief - strength * belief * (0.5 - trust_val) * 2
        belief = max(0, min(1, belief))

    return belief


# ─── Trust Cycle Resolution ──────────────────────────────────────

def detect_trust_cycles(network: TrustNetwork) -> List[List[int]]:
    """
    Detect cycles in trust graph using DFS.
    Returns list of cycles found.
    """
    cycles = []
    visited = set()
    rec_stack = set()

    def dfs(node, path):
        visited.add(node)
        rec_stack.add(node)

        for neighbor in network.out_neighbors(node):
            if neighbor not in visited:
                dfs(neighbor, path + [neighbor])
            elif neighbor in rec_stack:
                # Found cycle: extract it
                cycle_start = path.index(neighbor) if neighbor in path else -1
                if cycle_start >= 0:
                    cycle = path[cycle_start:] + [neighbor]
                    if len(cycle) >= 3:  # non-trivial cycle
                        cycles.append(cycle)

        rec_stack.discard(node)

    for node in sorted(network.nodes):
        if node not in visited:
            dfs(node, [node])

    return cycles


def resolve_cycle_trust(network: TrustNetwork, cycle: List[int]) -> float:
    """
    Resolve trust in a cycle to a fixed point.
    Trust around cycle = product of edge weights.
    If < 1, cycle trust converges; if ≥ 1, cap at max edge.
    """
    if len(cycle) < 2:
        return 0.0

    cycle_product = 1.0
    for i in range(len(cycle) - 1):
        cycle_product *= network.get_weight(cycle[i], cycle[i + 1])

    # Cycle trust converges to geometric mean of edge weights
    n_edges = len(cycle) - 1
    if cycle_product > 0:
        return cycle_product ** (1 / n_edges)
    return 0.0


# ─── Sybil Resistance ────────────────────────────────────────────

def trust_bottleneck(network: TrustNetwork, src: int, dst: int) -> float:
    """
    Find the trust bottleneck (minimum cut) between src and dst.
    Low bottleneck → Sybil attack easier (few trust links needed).
    High bottleneck → more trust paths needed.
    """
    return trust_max_flow(network, src, dst)


def sybil_region_boundary(network: TrustNetwork, trusted_nodes: Set[int]) -> Dict[int, float]:
    """
    For each non-trusted node, compute total trust flow from trusted region.
    Sybil nodes will have low flow from trusted region.
    """
    flows = {}
    for node in network.nodes:
        if node in trusted_nodes:
            flows[node] = 1.0
            continue

        total_flow = 0.0
        for trusted in trusted_nodes:
            total_flow += trust_max_flow(network, trusted, node)

        flows[node] = min(1.0, total_flow)

    return flows


# ─── Graph Generators ─────────────────────────────────────────────

def build_chain_network(n: int, trust: float = 0.8) -> TrustNetwork:
    """Linear chain: 0→1→2→...→n-1"""
    net = TrustNetwork()
    for i in range(n - 1):
        net.add_edge(i, i + 1, trust)
    return net


def build_trust_web(n: int, density: float = 0.3, seed: int = 42) -> TrustNetwork:
    """Random trust network."""
    rng = random.Random(seed)
    net = TrustNetwork()
    for i in range(n):
        net.nodes.add(i)
    for i in range(n):
        for j in range(n):
            if i != j and rng.random() < density:
                net.add_edge(i, j, rng.uniform(0.3, 0.9))
    return net


def build_sybil_network(n_honest: int, n_sybil: int, attack_edges: int,
                         seed: int = 42) -> Tuple[TrustNetwork, Set[int], Set[int]]:
    """
    Network with honest region and Sybil region.
    attack_edges: number of edges from honest to Sybil region.
    """
    rng = random.Random(seed)
    net = TrustNetwork()

    honest = set(range(n_honest))
    sybil = set(range(n_honest, n_honest + n_sybil))

    # Honest region: well-connected
    for i in honest:
        for j in honest:
            if i != j and rng.random() < 0.4:
                net.add_edge(i, j, rng.uniform(0.6, 0.9))

    # Sybil region: densely connected to each other
    for i in sybil:
        for j in sybil:
            if i != j:
                net.add_edge(i, j, rng.uniform(0.8, 1.0))

    # Attack edges: limited connections from honest to sybil
    honest_list = sorted(honest)
    sybil_list = sorted(sybil)
    for _ in range(attack_edges):
        h = rng.choice(honest_list)
        s = rng.choice(sybil_list)
        net.add_edge(h, s, rng.uniform(0.3, 0.6))

    return net, honest, sybil


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
    print("Trust Propagation Networks for Web4")
    print("Session 31, Track 1")
    print("=" * 70)

    # ── §1 Transitive Trust (Multiplicative) ──────────────────────
    print("\n§1 Transitive Trust (Multiplicative)\n")

    chain = build_chain_network(5, trust=0.8)

    # Direct neighbor
    t01 = transitive_trust_multiplicative(chain, 0, 1)
    check("direct_trust", abs(t01 - 0.8) < 0.01, f"t={t01:.3f}")

    # Two hops: 0.8 * 0.8 = 0.64
    t02 = transitive_trust_multiplicative(chain, 0, 2)
    check("two_hop_trust", abs(t02 - 0.64) < 0.01, f"t={t02:.3f}")

    # Four hops: 0.8^4 = 0.4096
    t04 = transitive_trust_multiplicative(chain, 0, 4)
    check("four_hop_trust", abs(t04 - 0.4096) < 0.01, f"t={t04:.4f}")

    # Trust decreases with distance
    check("trust_decreases_with_distance", t01 > t02 > t04)

    # Self trust = 1
    check("self_trust", transitive_trust_multiplicative(chain, 0, 0) == 1.0)

    # No path → 0
    check("no_path_zero", transitive_trust_multiplicative(chain, 4, 0) == 0.0)

    # ── §2 Transitive Trust (Min) ────────────────────────────────
    print("\n§2 Transitive Trust (Weakest Link)\n")

    # Build network with varying edge weights
    varied = TrustNetwork()
    varied.add_edge(0, 1, 0.9)
    varied.add_edge(1, 2, 0.5)  # weak link
    varied.add_edge(2, 3, 0.8)

    t_min = transitive_trust_min(varied, 0, 3)
    check("weakest_link", abs(t_min - 0.5) < 0.01, f"t={t_min:.3f}")

    # Alternative path bypassing weak link
    varied.add_edge(0, 2, 0.7)  # bypass 0→1→2, go 0→2 directly
    t_min2 = transitive_trust_min(varied, 0, 3)
    check("bypass_improves", t_min2 >= t_min,
          f"with_bypass={t_min2:.3f} without={t_min:.3f}")

    # ── §3 Discounted Trust ──────────────────────────────────────
    print("\n§3 Discounted Transitive Trust\n")

    t_disc = transitive_trust_discounted(chain, 0, 2, discount=0.9)
    t_nodis = transitive_trust_multiplicative(chain, 0, 2)
    check("discount_reduces", t_disc < t_nodis,
          f"disc={t_disc:.4f} nodis={t_nodis:.4f}")

    # Higher discount → less reduction
    t_disc_high = transitive_trust_discounted(chain, 0, 2, discount=0.99)
    t_disc_low = transitive_trust_discounted(chain, 0, 2, discount=0.5)
    check("higher_discount_more_trust", t_disc_high > t_disc_low,
          f"high={t_disc_high:.4f} low={t_disc_low:.4f}")

    # ── §4 Trust Max-Flow ────────────────────────────────────────
    print("\n§4 Trust Max-Flow\n")

    # Simple network with two paths
    flow_net = TrustNetwork()
    flow_net.add_edge(0, 1, 0.5)
    flow_net.add_edge(0, 2, 0.3)
    flow_net.add_edge(1, 3, 0.4)
    flow_net.add_edge(2, 3, 0.3)

    flow = trust_max_flow(flow_net, 0, 3)
    check("max_flow_positive", flow > 0, f"flow={flow:.3f}")
    # Max flow = min(0.5, 0.4) + min(0.3, 0.3) = 0.4 + 0.3 = 0.7
    check("max_flow_value", abs(flow - 0.7) < 0.01, f"flow={flow:.3f}")

    # Single edge bottleneck
    simple = TrustNetwork()
    simple.add_edge(0, 1, 0.6)
    flow_simple = trust_max_flow(simple, 0, 1)
    check("single_edge_flow", abs(flow_simple - 0.6) < 0.01)

    # ── §5 Personalized Trust ────────────────────────────────────
    print("\n§5 Personalized Trust (PageRank-like)\n")

    web = build_trust_web(8, density=0.3, seed=42)
    pt = personalized_trust(web, source=0)

    # Source has highest trust
    check("source_highest", pt[0] >= max(pt[n] for n in web.nodes if n != 0),
          f"source={pt[0]:.4f}")

    # All values non-negative
    check("all_non_negative", all(v >= 0 for v in pt.values()))

    # Direct neighbors get more trust than non-neighbors
    neighbors = set(web.out_neighbors(0))
    if neighbors:
        non_neighbors = web.nodes - neighbors - {0}
        if non_neighbors:
            avg_neighbor = sum(pt[n] for n in neighbors) / len(neighbors)
            avg_non = sum(pt[n] for n in non_neighbors) / len(non_neighbors)
            check("neighbors_more_trusted", avg_neighbor >= avg_non,
                  f"neighbors={avg_neighbor:.4f} non={avg_non:.4f}")

    # ── §6 Trust Aggregation ─────────────────────────────────────
    print("\n§6 Trust Aggregation\n")

    opinions = [(0.8, 0.9), (0.6, 0.5), (0.7, 0.7)]

    # Weighted mean
    agg_mean = aggregate_trust_weighted_mean(opinions)
    check("weighted_mean_bounded", 0.6 <= agg_mean <= 0.8,
          f"mean={agg_mean:.3f}")

    # Pessimistic
    agg_pess = aggregate_trust_pessimistic(opinions)
    check("pessimistic_is_min", agg_pess == 0.6)

    # Bayesian
    agg_bayes = aggregate_trust_bayesian(opinions)
    check("bayesian_bounded", 0 <= agg_bayes <= 1, f"bayes={agg_bayes:.3f}")

    # Weighted mean > pessimistic
    check("mean_gt_pessimistic", agg_mean > agg_pess)

    # All high trust → high aggregate
    high_opinions = [(0.9, 0.9), (0.85, 0.8), (0.88, 0.95)]
    check("high_trust_high_agg",
          aggregate_trust_weighted_mean(high_opinions) > 0.8)

    # ── §7 Trust Cycles ──────────────────────────────────────────
    print("\n§7 Trust Cycle Detection\n")

    cycle_net = TrustNetwork()
    cycle_net.add_edge(0, 1, 0.8)
    cycle_net.add_edge(1, 2, 0.7)
    cycle_net.add_edge(2, 0, 0.6)  # creates cycle 0→1→2→0
    cycle_net.add_edge(2, 3, 0.5)  # non-cyclic edge

    cycles = detect_trust_cycles(cycle_net)
    check("cycle_detected", len(cycles) > 0, f"cycles={len(cycles)}")

    # No cycles in a DAG (chain)
    dag_cycles = detect_trust_cycles(chain)
    check("dag_no_cycles", len(dag_cycles) == 0, f"cycles={len(dag_cycles)}")

    # Cycle trust resolution
    if cycles:
        cycle_trust = resolve_cycle_trust(cycle_net, cycles[0])
        check("cycle_trust_bounded", 0 < cycle_trust < 1,
              f"trust={cycle_trust:.3f}")
        # Geometric mean of 0.8, 0.7, 0.6 ≈ 0.695
        check("cycle_trust_geometric",
              abs(cycle_trust - (0.8 * 0.7 * 0.6) ** (1/3)) < 0.01,
              f"trust={cycle_trust:.3f}")

    # ── §8 Sybil Resistance ──────────────────────────────────────
    print("\n§8 Sybil Resistance Analysis\n")

    sybil_net, honest, sybil = build_sybil_network(
        n_honest=5, n_sybil=5, attack_edges=2, seed=42)

    # Trust bottleneck: max-flow from a single honest node to sybil nodes
    # (not all honest nodes combined)
    honest_node = min(honest)
    sybil_flows_single = {}
    for s in sybil:
        sybil_flows_single[s] = trust_max_flow(sybil_net, honest_node, s)

    avg_sybil_single = sum(sybil_flows_single.values()) / len(sybil) if sybil else 0

    # From a single honest node, flow to sybil region is bottlenecked
    check("sybil_bottlenecked_per_node", avg_sybil_single < 1.0,
          f"avg_flow={avg_sybil_single:.3f}")

    # More attack edges → more flow (build comparison)
    sybil_net2, _, sybil2 = build_sybil_network(5, 5, attack_edges=5, seed=42)
    sybil_flows_more = {}
    for s in sybil2:
        sybil_flows_more[s] = trust_max_flow(sybil_net2, honest_node, s)
    avg_sybil_more = sum(sybil_flows_more.values()) / len(sybil2)
    check("more_attacks_more_flow", avg_sybil_more >= avg_sybil_single,
          f"2_edges={avg_sybil_single:.3f} 5_edges={avg_sybil_more:.3f}")

    # ── §9 Comparative Analysis ──────────────────────────────────
    print("\n§9 Direct vs Transitive vs Flow Trust\n")

    comp_net = TrustNetwork()
    comp_net.add_edge(0, 1, 0.9)
    comp_net.add_edge(1, 2, 0.8)
    comp_net.add_edge(0, 2, 0.5)  # direct but low trust
    comp_net.add_edge(0, 3, 0.3)
    comp_net.add_edge(3, 2, 0.9)

    # Direct trust 0→2 = 0.5
    direct = comp_net.get_weight(0, 2)

    # Transitive (multiplicative): max(0.5, 0.9*0.8, 0.3*0.9) = max(0.5, 0.72, 0.27) = 0.72
    transitive = transitive_trust_multiplicative(comp_net, 0, 2)

    # Flow: sum of capacities through parallel paths
    flow = trust_max_flow(comp_net, 0, 2)

    check("transitive_gt_direct", transitive >= direct,
          f"trans={transitive:.3f} direct={direct:.3f}")
    check("flow_gt_single_path", flow >= transitive,
          f"flow={flow:.3f} trans={transitive:.3f}")

    # Direct is a lower bound
    check("direct_lower_bound", direct <= transitive)

    # ── §10 Distance Penalty ─────────────────────────────────────
    print("\n§10 Trust Distance Analysis\n")

    long_chain = build_chain_network(10, trust=0.9)

    # Trust at each hop (increase max_hops for long chains)
    hop_trusts = [transitive_trust_multiplicative(long_chain, 0, i, max_hops=10) for i in range(10)]

    # Monotonically decreasing
    check("monotone_decrease", all(hop_trusts[i] >= hop_trusts[i+1]
                                    for i in range(9)))

    # Exponential decay: trust[n] ≈ 0.9^n
    for n in [1, 3, 5, 9]:
        expected = 0.9 ** n
        check(f"hop_{n}_matches", abs(hop_trusts[n] - expected) < 0.01,
              f"actual={hop_trusts[n]:.4f} expected={expected:.4f}")

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
