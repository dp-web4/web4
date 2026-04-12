"""
Trust Network Robustness Certification for Web4
Session 30, Track 5

Formal robustness analysis and certification:
- k-connectivity: minimum vertex/edge cuts
- Robustness certificates: provable attack tolerance
- Percolation thresholds: random failure tolerance
- Targeted attack resilience (hub removal)
- Trust-weighted robustness (not all edges equal)
- Redundancy analysis (alternative trust paths)
- Recovery time estimation after node failure
- Certification levels based on robustness metrics
"""

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Set, Tuple, Optional


# ─── Graph Structures ──────────────────────────────────────────────

@dataclass
class TrustGraph:
    """Weighted directed trust graph."""
    n_nodes: int
    edges: Dict[Tuple[int, int], float] = field(default_factory=dict)  # (src, dst) → weight
    node_trust: Dict[int, float] = field(default_factory=dict)  # node → trust

    def add_edge(self, src: int, dst: int, weight: float = 1.0):
        self.edges[(src, dst)] = weight

    def neighbors(self, node: int) -> List[int]:
        return [dst for (src, dst) in self.edges if src == node]

    def in_neighbors(self, node: int) -> List[int]:
        return [src for (src, dst) in self.edges if dst == node]

    def degree(self, node: int) -> int:
        return len(self.neighbors(node))

    def nodes(self) -> Set[int]:
        nodes = set()
        for src, dst in self.edges:
            nodes.add(src)
            nodes.add(dst)
        for n in self.node_trust:
            nodes.add(n)
        return nodes

    def remove_node(self, node: int) -> 'TrustGraph':
        """Return copy with node removed."""
        new_graph = TrustGraph(self.n_nodes - 1)
        for (src, dst), w in self.edges.items():
            if src != node and dst != node:
                new_graph.add_edge(src, dst, w)
        for n, t in self.node_trust.items():
            if n != node:
                new_graph.node_trust[n] = t
        return new_graph


# ─── Connectivity Analysis ─────────────────────────────────────────

def bfs_reachable(graph: TrustGraph, start: int, excluded: Set[int] = None) -> Set[int]:
    """BFS from start, excluding specified nodes."""
    if excluded is None:
        excluded = set()

    visited = {start}
    queue = [start]

    while queue:
        node = queue.pop(0)
        for neighbor in graph.neighbors(node):
            if neighbor not in visited and neighbor not in excluded:
                visited.add(neighbor)
                queue.append(neighbor)

    return visited


def is_connected(graph: TrustGraph) -> bool:
    """Check if graph is strongly connected (treat as undirected)."""
    nodes = graph.nodes()
    if len(nodes) <= 1:
        return True

    # Build undirected adjacency
    adj = {n: set() for n in nodes}
    for (src, dst) in graph.edges:
        adj[src].add(dst)
        adj[dst].add(src)

    start = next(iter(nodes))
    visited = {start}
    queue = [start]
    while queue:
        node = queue.pop(0)
        for n in adj.get(node, set()):
            if n not in visited:
                visited.add(n)
                queue.append(n)

    return len(visited) == len(nodes)


def vertex_connectivity(graph: TrustGraph) -> int:
    """
    Approximate vertex connectivity (min vertex cut).
    Uses brute-force for small graphs.
    """
    nodes = sorted(graph.nodes())
    n = len(nodes)

    if n <= 1:
        return 0
    if not is_connected(graph):
        return 0

    # Try removing k nodes and check connectivity
    for k in range(1, n):
        # Try all combinations of k nodes (limited for performance)
        from itertools import combinations
        found_cut = False

        combos = list(combinations(nodes, k))
        # Limit to 100 combinations for large graphs
        if len(combos) > 100:
            random.seed(42)
            combos = random.sample(combos, 100)

        for to_remove in combos:
            remaining = [n for n in nodes if n not in to_remove]
            if len(remaining) <= 1:
                continue

            # Check if remaining graph is connected
            adj = {n: set() for n in remaining}
            for (src, dst) in graph.edges:
                if src not in to_remove and dst not in to_remove:
                    if src in adj:
                        adj[src].add(dst)
                    if dst in adj:
                        adj[dst].add(src)

            start = remaining[0]
            visited = {start}
            queue = [start]
            while queue:
                node = queue.pop(0)
                for nb in adj.get(node, set()):
                    if nb not in visited:
                        visited.add(nb)
                        queue.append(nb)

            if len(visited) < len(remaining):
                found_cut = True
                break

        if found_cut:
            return k

    return n - 1  # complete graph


def edge_connectivity(graph: TrustGraph) -> int:
    """
    Approximate edge connectivity (min edge cut).
    Lower bound: minimum degree.
    """
    nodes = graph.nodes()
    if len(nodes) <= 1:
        return 0
    if not is_connected(graph):
        return 0

    # Build undirected degree
    degree = {n: 0 for n in nodes}
    counted = set()
    for (src, dst) in graph.edges:
        edge_key = (min(src, dst), max(src, dst))
        if edge_key not in counted:
            counted.add(edge_key)
            degree[src] = degree.get(src, 0) + 1
            degree[dst] = degree.get(dst, 0) + 1

    if not degree:
        return 0

    # Min degree is upper bound on edge connectivity
    return min(degree.values())


# ─── Percolation Analysis ─────────────────────────────────────────

def random_failure_tolerance(graph: TrustGraph, trials: int = 50,
                              seed: int = 42) -> Dict:
    """
    Test random node removal until disconnected.
    Returns fraction of nodes that can be removed.
    """
    rng = random.Random(seed)
    nodes = sorted(graph.nodes())
    n = len(nodes)

    if n <= 2:
        return {"threshold": 0.0, "mean_removals": 0}

    total_removals = 0

    for _ in range(trials):
        order = list(nodes)
        rng.shuffle(order)
        removed = set()

        disconnected_at = n - 1  # default: could remove all but 1
        for node in order:
            removed.add(node)
            remaining = [nd for nd in nodes if nd not in removed]
            if len(remaining) <= 1:
                disconnected_at = len(removed) - 1
                break

            # Check connectivity
            adj = {nd: set() for nd in remaining}
            for (src, dst) in graph.edges:
                if src not in removed and dst not in removed:
                    if src in adj:
                        adj[src].add(dst)
                    if dst in adj:
                        adj[dst].add(src)

            start = remaining[0]
            visited = {start}
            queue = [start]
            while queue:
                nd = queue.pop(0)
                for nb in adj.get(nd, set()):
                    if nb not in visited:
                        visited.add(nb)
                        queue.append(nb)

            if len(visited) < len(remaining):
                disconnected_at = len(removed) - 1  # last one broke it
                break

        total_removals += disconnected_at

    mean_removals = total_removals / trials
    threshold = mean_removals / n

    return {
        "threshold": threshold,
        "mean_removals": mean_removals,
        "n_nodes": n,
    }


def targeted_attack_resilience(graph: TrustGraph) -> Dict:
    """
    Test targeted attack: remove highest-degree nodes first.
    Returns number of removals until disconnected.
    """
    nodes = sorted(graph.nodes())
    n = len(nodes)

    if n <= 2:
        return {"removals_to_disconnect": 0, "fraction": 0.0}

    # Sort by degree (highest first)
    degrees = {nd: graph.degree(nd) for nd in nodes}
    attack_order = sorted(nodes, key=lambda nd: degrees.get(nd, 0), reverse=True)

    removed = set()
    for i, node in enumerate(attack_order):
        removed.add(node)
        remaining = [nd for nd in nodes if nd not in removed]
        if len(remaining) <= 1:
            return {"removals_to_disconnect": i + 1, "fraction": (i + 1) / n}

        # Check connectivity
        adj = {nd: set() for nd in remaining}
        for (src, dst) in graph.edges:
            if src not in removed and dst not in removed:
                if src in adj:
                    adj[src].add(dst)
                if dst in adj:
                    adj[dst].add(src)

        start = remaining[0]
        visited = {start}
        queue = [start]
        while queue:
            nd = queue.pop(0)
            for nb in adj.get(nd, set()):
                if nb not in visited:
                    visited.add(nb)
                    queue.append(nb)

        if len(visited) < len(remaining):
            return {"removals_to_disconnect": i + 1, "fraction": (i + 1) / n}

    return {"removals_to_disconnect": n, "fraction": 1.0}


# ─── Trust Path Redundancy ────────────────────────────────────────

def count_disjoint_paths(graph: TrustGraph, src: int, dst: int,
                          max_paths: int = 10) -> int:
    """
    Count node-disjoint paths from src to dst (approximation).
    Uses iterative BFS with node removal.
    """
    if src == dst:
        return 0

    count = 0
    used_nodes = {src, dst}  # these are always used

    for _ in range(max_paths):
        # BFS avoiding used intermediate nodes
        visited = {src}
        parent = {src: None}
        queue = [src]
        found = False

        while queue and not found:
            node = queue.pop(0)
            for neighbor in graph.neighbors(node):
                if neighbor == dst:
                    found = True
                    parent[dst] = node
                    break
                if neighbor not in visited and (neighbor not in used_nodes or neighbor == dst):
                    visited.add(neighbor)
                    parent[neighbor] = node
                    queue.append(neighbor)

        if not found:
            break

        # Trace path and mark intermediate nodes as used
        count += 1
        node = dst
        while parent.get(node) is not None:
            node = parent[node]
            if node != src:
                used_nodes.add(node)

    return count


def trust_weighted_redundancy(graph: TrustGraph, src: int, dst: int) -> float:
    """
    Trust-weighted path redundancy score.
    Higher = more reliable paths between nodes.
    """
    n_paths = count_disjoint_paths(graph, src, dst)
    if n_paths == 0:
        return 0.0

    # Weight by source and destination trust
    src_trust = graph.node_trust.get(src, 0.5)
    dst_trust = graph.node_trust.get(dst, 0.5)

    # Redundancy: log(1 + n_paths) scaled by trust
    redundancy = math.log(1 + n_paths) * (src_trust + dst_trust) / 2
    return min(1.0, redundancy)


# ─── Recovery Time Estimation ─────────────────────────────────────

def estimate_recovery_time(graph: TrustGraph, failed_node: int,
                            attestation_rate: float = 0.1) -> float:
    """
    Estimate recovery time after node failure.

    Time depends on:
    - Number of affected edges (trust relationships to rebuild)
    - Attestation rate (how fast new trust is established)
    - Redundancy (alternative paths reduce impact)
    """
    affected_edges = len([1 for (src, dst) in graph.edges
                          if src == failed_node or dst == failed_node])

    if affected_edges == 0:
        return 0.0

    # Each affected edge needs ~1/attestation_rate time to rebuild
    base_time = affected_edges / attestation_rate

    # Redundancy reduces effective recovery time
    nodes = graph.nodes()
    avg_redundancy = 0.0
    count = 0
    for n in nodes:
        if n != failed_node:
            r = count_disjoint_paths(graph, n, failed_node)
            avg_redundancy += r
            count += 1

    if count > 0:
        avg_redundancy /= count

    # More redundancy → faster recovery
    redundancy_factor = 1.0 / (1.0 + avg_redundancy)

    return base_time * redundancy_factor


# ─── Robustness Certification ─────────────────────────────────────

class CertificationLevel(Enum):
    PLATINUM = "platinum"    # highest robustness
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"
    UNCERTIFIED = "uncertified"


@dataclass
class RobustnessCertificate:
    level: CertificationLevel
    vertex_connectivity: int
    edge_connectivity: int
    random_failure_threshold: float
    targeted_attack_fraction: float
    avg_path_redundancy: float
    details: Dict[str, float] = field(default_factory=dict)


def certify_robustness(graph: TrustGraph) -> RobustnessCertificate:
    """
    Generate robustness certificate for trust network.

    Platinum: k-connected (k≥3), random threshold > 0.5, targeted > 0.3
    Gold: k-connected (k≥2), random threshold > 0.3, targeted > 0.2
    Silver: connected, random threshold > 0.2
    Bronze: connected
    Uncertified: disconnected
    """
    if not is_connected(graph):
        return RobustnessCertificate(
            CertificationLevel.UNCERTIFIED, 0, 0, 0.0, 0.0, 0.0)

    v_conn = vertex_connectivity(graph)
    e_conn = edge_connectivity(graph)
    rf = random_failure_tolerance(graph, trials=20)
    ta = targeted_attack_resilience(graph)

    # Average path redundancy (sample pairs)
    nodes = sorted(graph.nodes())
    total_redundancy = 0.0
    pairs = 0
    for i in range(min(len(nodes), 5)):
        for j in range(i + 1, min(len(nodes), 5)):
            total_redundancy += count_disjoint_paths(graph, nodes[i], nodes[j])
            pairs += 1
    avg_redundancy = total_redundancy / pairs if pairs > 0 else 0.0

    # Determine level
    rf_threshold = rf["threshold"]
    ta_fraction = ta["fraction"]

    if v_conn >= 3 and rf_threshold > 0.5 and ta_fraction > 0.3:
        level = CertificationLevel.PLATINUM
    elif v_conn >= 2 and rf_threshold > 0.3 and ta_fraction > 0.2:
        level = CertificationLevel.GOLD
    elif rf_threshold > 0.2:
        level = CertificationLevel.SILVER
    elif is_connected(graph):
        level = CertificationLevel.BRONZE
    else:
        level = CertificationLevel.UNCERTIFIED

    return RobustnessCertificate(
        level=level,
        vertex_connectivity=v_conn,
        edge_connectivity=e_conn,
        random_failure_threshold=rf_threshold,
        targeted_attack_fraction=ta_fraction,
        avg_path_redundancy=avg_redundancy,
        details={
            "n_nodes": len(nodes),
            "n_edges": len(graph.edges),
            "mean_removals": rf["mean_removals"],
        }
    )


# ─── Graph Generators ─────────────────────────────────────────────

def build_complete_graph(n: int, trust: float = 0.7) -> TrustGraph:
    """Complete graph with uniform trust."""
    g = TrustGraph(n)
    for i in range(n):
        g.node_trust[i] = trust
        for j in range(n):
            if i != j:
                g.add_edge(i, j, trust)
    return g


def build_ring_graph(n: int, trust: float = 0.7) -> TrustGraph:
    """Ring graph — minimally connected."""
    g = TrustGraph(n)
    for i in range(n):
        g.node_trust[i] = trust
        g.add_edge(i, (i + 1) % n, trust)
        g.add_edge((i + 1) % n, i, trust)
    return g


def build_random_graph(n: int, p: float = 0.3, seed: int = 42) -> TrustGraph:
    """Erdos-Renyi random graph."""
    rng = random.Random(seed)
    g = TrustGraph(n)
    for i in range(n):
        g.node_trust[i] = rng.uniform(0.3, 0.9)
        for j in range(i + 1, n):
            if rng.random() < p:
                w = rng.uniform(0.3, 0.9)
                g.add_edge(i, j, w)
                g.add_edge(j, i, w)
    return g


def build_star_graph(n: int, trust: float = 0.7) -> TrustGraph:
    """Star graph — hub and spokes."""
    g = TrustGraph(n)
    g.node_trust[0] = 0.9  # hub is high trust
    for i in range(1, n):
        g.node_trust[i] = trust
        g.add_edge(0, i, trust)
        g.add_edge(i, 0, trust)
    return g


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
    print("Trust Network Robustness Certification for Web4")
    print("Session 30, Track 5")
    print("=" * 70)

    # ── §1 Graph Construction ─────────────────────────────────────
    print("\n§1 Graph Construction\n")

    complete6 = build_complete_graph(6)
    check("complete_6_edges", len(complete6.edges) == 30,
          f"edges={len(complete6.edges)}")
    check("complete_6_connected", is_connected(complete6))

    ring8 = build_ring_graph(8)
    check("ring_8_connected", is_connected(ring8))
    check("ring_8_edges", len(ring8.edges) == 16,
          f"edges={len(ring8.edges)}")

    star6 = build_star_graph(6)
    check("star_6_connected", is_connected(star6))

    # ── §2 Vertex Connectivity ────────────────────────────────────
    print("\n§2 Vertex Connectivity\n")

    # Complete graph K6: vertex connectivity = 5
    vc_complete = vertex_connectivity(complete6)
    check("complete_v_conn", vc_complete == 5, f"vc={vc_complete}")

    # Ring: vertex connectivity = 1 (remove any node disconnects... actually 2 for undirected ring)
    # Wait — ring connectivity should be 2 (need to remove 2 nodes to disconnect)
    # Actually for a cycle graph, κ = 2
    vc_ring = vertex_connectivity(ring8)
    check("ring_v_conn", vc_ring == 2, f"vc={vc_ring}")

    # Star: vertex connectivity = 1 (remove hub)
    vc_star = vertex_connectivity(star6)
    check("star_v_conn", vc_star == 1, f"vc={vc_star}")

    # ── §3 Edge Connectivity ──────────────────────────────────────
    print("\n§3 Edge Connectivity\n")

    ec_complete = edge_connectivity(complete6)
    check("complete_e_conn", ec_complete == 5, f"ec={ec_complete}")

    ec_star = edge_connectivity(star6)
    check("star_e_conn", ec_star == 1, f"ec={ec_star}")

    # ── §4 Random Failure Tolerance ───────────────────────────────
    print("\n§4 Random Failure Tolerance\n")

    rf_complete = random_failure_tolerance(complete6)
    rf_star = random_failure_tolerance(star6)

    # Complete graph should tolerate more random failures
    check("complete_more_robust_random",
          rf_complete["threshold"] > rf_star["threshold"],
          f"complete={rf_complete['threshold']:.3f} star={rf_star['threshold']:.3f}")

    check("random_threshold_bounded", 0 <= rf_complete["threshold"] <= 1)

    # ── §5 Targeted Attack Resilience ─────────────────────────────
    print("\n§5 Targeted Attack Resilience\n")

    ta_complete = targeted_attack_resilience(complete6)
    ta_star = targeted_attack_resilience(star6)

    # Star is very vulnerable to targeted attack (remove hub)
    check("star_vulnerable_targeted", ta_star["removals_to_disconnect"] == 1,
          f"removals={ta_star['removals_to_disconnect']}")

    # Complete graph needs more targeted removals
    check("complete_resilient_targeted",
          ta_complete["removals_to_disconnect"] > ta_star["removals_to_disconnect"],
          f"complete={ta_complete['removals_to_disconnect']} star={ta_star['removals_to_disconnect']}")

    # ── §6 Path Redundancy ────────────────────────────────────────
    print("\n§6 Trust Path Redundancy\n")

    # Complete graph: many disjoint paths
    paths_complete = count_disjoint_paths(complete6, 0, 5)
    check("complete_many_paths", paths_complete >= 3,
          f"paths={paths_complete}")

    # Ring: 2 disjoint paths between any pair
    paths_ring = count_disjoint_paths(ring8, 0, 4)
    check("ring_two_paths", paths_ring == 2,
          f"paths={paths_ring}")

    # Star: 1 path (through hub)
    paths_star = count_disjoint_paths(star6, 1, 3)
    check("star_one_path", paths_star == 1,
          f"paths={paths_star}")

    # Trust-weighted redundancy
    twr = trust_weighted_redundancy(complete6, 0, 5)
    check("twr_positive", twr > 0, f"twr={twr:.3f}")
    check("twr_bounded", 0 <= twr <= 1, f"twr={twr:.3f}")

    # ── §7 Recovery Time ──────────────────────────────────────────
    print("\n§7 Recovery Time Estimation\n")

    # Star hub failure → long recovery
    rt_star_hub = estimate_recovery_time(star6, failed_node=0)
    # Leaf failure → shorter recovery
    rt_star_leaf = estimate_recovery_time(star6, failed_node=1)

    check("hub_recovery_longer", rt_star_hub > rt_star_leaf,
          f"hub={rt_star_hub:.1f} leaf={rt_star_leaf:.1f}")

    # Isolated node → 0 recovery
    isolated = TrustGraph(1)
    isolated.node_trust[0] = 0.5
    rt_isolated = estimate_recovery_time(isolated, 0)
    check("isolated_zero_recovery", rt_isolated == 0.0)

    # ── §8 Robustness Certification ───────────────────────────────
    print("\n§8 Robustness Certification\n")

    cert_complete = certify_robustness(complete6)
    check("complete_high_cert",
          cert_complete.level in (CertificationLevel.PLATINUM, CertificationLevel.GOLD),
          f"level={cert_complete.level.value}")

    cert_star = certify_robustness(star6)
    check("star_low_cert",
          cert_star.level in (CertificationLevel.BRONZE, CertificationLevel.SILVER,
                               CertificationLevel.UNCERTIFIED),
          f"level={cert_star.level.value}")

    # Disconnected → uncertified
    disconnected = TrustGraph(4)
    disconnected.add_edge(0, 1, 0.5)
    disconnected.add_edge(1, 0, 0.5)
    disconnected.node_trust = {0: 0.5, 1: 0.5, 2: 0.5, 3: 0.5}
    cert_disc = certify_robustness(disconnected)
    check("disconnected_uncertified",
          cert_disc.level == CertificationLevel.UNCERTIFIED,
          f"level={cert_disc.level.value}")

    # ── §9 Random Graph Certification ─────────────────────────────
    print("\n§9 Random Graph Analysis\n")

    rg = build_random_graph(10, p=0.4, seed=42)
    cert_random = certify_robustness(rg)
    check("random_graph_certified",
          cert_random.level != CertificationLevel.UNCERTIFIED,
          f"level={cert_random.level.value}")
    check("random_cert_has_details", len(cert_random.details) > 0)

    # Sparse random graph
    rg_sparse = build_random_graph(10, p=0.15, seed=42)
    cert_sparse = certify_robustness(rg_sparse)

    # Dense should be more robust than sparse
    level_order = {
        CertificationLevel.UNCERTIFIED: 0,
        CertificationLevel.BRONZE: 1,
        CertificationLevel.SILVER: 2,
        CertificationLevel.GOLD: 3,
        CertificationLevel.PLATINUM: 4,
    }
    check("dense_more_robust",
          level_order[cert_random.level] >= level_order[cert_sparse.level],
          f"dense={cert_random.level.value} sparse={cert_sparse.level.value}")

    # ── §10 Comparative Robustness ────────────────────────────────
    print("\n§10 Topology Comparison\n")

    # Compare topologies at same size
    n = 8
    topologies = {
        "complete": build_complete_graph(n),
        "ring": build_ring_graph(n),
        "star": build_star_graph(n),
        "random": build_random_graph(n, p=0.4, seed=99),
    }

    certs = {name: certify_robustness(g) for name, g in topologies.items()}

    # Complete should be most robust
    check("complete_most_robust",
          level_order[certs["complete"].level] >= max(
              level_order[certs[t].level] for t in ["ring", "star", "random"]),
          f"levels={[(t, c.level.value) for t, c in certs.items()]}")

    # Star should be least robust (or tied with ring)
    check("star_least_robust",
          level_order[certs["star"].level] <= level_order[certs["ring"].level],
          f"star={certs['star'].level.value} ring={certs['ring'].level.value}")

    # Vertex connectivity ordering: complete > random > ring > star (approximately)
    check("v_conn_ordering",
          certs["complete"].vertex_connectivity >= certs["star"].vertex_connectivity,
          f"complete={certs['complete'].vertex_connectivity} star={certs['star'].vertex_connectivity}")

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
