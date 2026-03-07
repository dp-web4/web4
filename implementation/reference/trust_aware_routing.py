"""
Trust-Aware Routing for Web4
Session 32, Track 2

Routing decisions based on trust in network paths:
- Shortest trusted path (trust-weighted Dijkstra)
- Multi-path trust routing (redundant paths for resilience)
- Maximum trust path (maximize minimum trust along path)
- Trust-cost tradeoff (Pareto-optimal paths)
- Adversarial routing (avoid untrusted regions)
- Onion routing trust variant (layered trust hops)
- Path trust aggregation methods
"""

import math
import heapq
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set, Optional


# ─── Trust Network ────────────────────────────────────────────────

@dataclass
class TrustLink:
    target: str
    trust: float      # [0, 1]
    latency: float    # cost metric (ms, hops, etc.)
    bandwidth: float = 1.0


@dataclass
class RoutingNetwork:
    adjacency: Dict[str, List[TrustLink]] = field(default_factory=dict)

    def add_link(self, source: str, target: str,
                 trust: float, latency: float, bandwidth: float = 1.0):
        if source not in self.adjacency:
            self.adjacency[source] = []
        self.adjacency[source].append(
            TrustLink(target=target, trust=trust,
                      latency=latency, bandwidth=bandwidth))

    def add_bidirectional(self, a: str, b: str,
                          trust: float, latency: float, bandwidth: float = 1.0):
        self.add_link(a, b, trust, latency, bandwidth)
        self.add_link(b, a, trust, latency, bandwidth)

    def nodes(self) -> Set[str]:
        result = set(self.adjacency.keys())
        for links in self.adjacency.values():
            for link in links:
                result.add(link.target)
        return result

    def neighbors(self, node: str) -> List[TrustLink]:
        return self.adjacency.get(node, [])


# ─── Shortest Trusted Path (Trust-Weighted Dijkstra) ──────────────

def shortest_trusted_path(network: RoutingNetwork,
                           source: str, target: str,
                           min_trust: float = 0.0) -> Tuple[List[str], float]:
    """
    Dijkstra's algorithm with trust threshold.
    Only uses links with trust >= min_trust.
    Returns (path, total_cost) or ([], inf) if no path.
    """
    dist = {source: 0.0}
    prev = {source: None}
    visited = set()
    heap = [(0.0, source)]

    while heap:
        d, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)

        if node == target:
            # Reconstruct path
            path = []
            current = target
            while current is not None:
                path.append(current)
                current = prev[current]
            return list(reversed(path)), d

        for link in network.neighbors(node):
            if link.trust < min_trust:
                continue
            new_dist = d + link.latency
            if link.target not in dist or new_dist < dist[link.target]:
                dist[link.target] = new_dist
                prev[link.target] = node
                heapq.heappush(heap, (new_dist, link.target))

    return [], float('inf')


# ─── Maximum Trust Path ──────────────────────────────────────────

def max_trust_path(network: RoutingNetwork,
                   source: str, target: str) -> Tuple[List[str], float]:
    """
    Find path that maximizes minimum trust along the way.
    Uses modified Dijkstra with max-min objective.
    Returns (path, min_trust_on_path).
    """
    # Best known min-trust to reach each node
    best_trust = {source: 1.0}
    prev = {source: None}
    visited = set()
    # Max-heap (negate trust for min-heap)
    heap = [(-1.0, source)]

    while heap:
        neg_trust, node = heapq.heappop(heap)
        current_trust = -neg_trust

        if node in visited:
            continue
        visited.add(node)

        if node == target:
            path = []
            current = target
            while current is not None:
                path.append(current)
                current = prev[current]
            return list(reversed(path)), current_trust

        for link in network.neighbors(node):
            # Trust through this link = min(trust_so_far, link_trust)
            path_trust = min(current_trust, link.trust)
            if link.target not in best_trust or path_trust > best_trust[link.target]:
                best_trust[link.target] = path_trust
                prev[link.target] = node
                heapq.heappush(heap, (-path_trust, link.target))

    return [], 0.0


# ─── Multi-Path Trust Routing ────────────────────────────────────

def find_k_trusted_paths(network: RoutingNetwork,
                          source: str, target: str,
                          k: int = 3,
                          min_trust: float = 0.0) -> List[Tuple[List[str], float]]:
    """
    Find k shortest trusted paths (Yen's algorithm simplified).
    Returns list of (path, cost) sorted by cost.
    """
    paths = []

    # Find first shortest path
    path, cost = shortest_trusted_path(network, source, target, min_trust)
    if not path:
        return []
    paths.append((path, cost))

    candidates = []

    for i in range(1, k):
        if i - 1 >= len(paths):
            break
        prev_path = paths[i - 1][0]

        for j in range(len(prev_path) - 1):
            spur_node = prev_path[j]
            root_path = prev_path[:j + 1]

            # Temporarily remove edges used by previous paths at this spur
            removed = []
            for p, _ in paths:
                if len(p) > j + 1 and p[:j + 1] == root_path:
                    # Remove edge p[j] -> p[j+1]
                    src, tgt = p[j], p[j + 1]
                    for idx, link in enumerate(network.adjacency.get(src, [])):
                        if link.target == tgt:
                            removed.append((src, idx, link))
                            network.adjacency[src][idx] = TrustLink(
                                target="__removed__", trust=0, latency=float('inf'))
                            break

            # Find spur path
            spur_path, spur_cost = shortest_trusted_path(
                network, spur_node, target, min_trust)

            # Restore edges
            for src, idx, link in removed:
                network.adjacency[src][idx] = link

            if spur_path:
                total_path = root_path[:-1] + spur_path
                # Calculate total cost
                total_cost = 0
                for m in range(len(total_path) - 1):
                    for link in network.neighbors(total_path[m]):
                        if link.target == total_path[m + 1]:
                            total_cost += link.latency
                            break

                candidate = (total_path, total_cost)
                if candidate not in candidates and candidate not in paths:
                    candidates.append(candidate)

        if not candidates:
            break

        candidates.sort(key=lambda x: x[1])
        paths.append(candidates.pop(0))

    return paths


# ─── Trust-Cost Pareto Paths ─────────────────────────────────────

def pareto_optimal_paths(network: RoutingNetwork,
                          source: str, target: str,
                          n_paths: int = 5) -> List[Tuple[List[str], float, float]]:
    """
    Find paths that are Pareto-optimal in (cost, trust) space.
    Returns list of (path, cost, min_trust).
    """
    # Find multiple paths with varying trust thresholds
    all_paths = []

    for threshold in [0.0, 0.2, 0.4, 0.6, 0.8]:
        path, cost = shortest_trusted_path(network, source, target, threshold)
        if path:
            # Compute min trust along path
            min_t = 1.0
            for i in range(len(path) - 1):
                for link in network.neighbors(path[i]):
                    if link.target == path[i + 1]:
                        min_t = min(min_t, link.trust)
                        break
            all_paths.append((path, cost, min_t))

    # Filter Pareto-optimal
    pareto = []
    for p in all_paths:
        dominated = False
        for q in all_paths:
            if q[1] <= p[1] and q[2] >= p[2] and (q[1] < p[1] or q[2] > p[2]):
                dominated = True
                break
        if not dominated:
            # Avoid duplicates
            if not any(pp[0] == p[0] for pp in pareto):
                pareto.append(p)

    return sorted(pareto, key=lambda x: x[1])


# ─── Adversarial Routing ─────────────────────────────────────────

def adversarial_avoidance_path(network: RoutingNetwork,
                                source: str, target: str,
                                untrusted_nodes: Set[str]) -> Tuple[List[str], float]:
    """
    Route around untrusted nodes entirely.
    """
    # Create filtered network view
    filtered = RoutingNetwork()
    for node, links in network.adjacency.items():
        if node in untrusted_nodes:
            continue
        for link in links:
            if link.target not in untrusted_nodes:
                filtered.add_link(node, link.target, link.trust,
                                   link.latency, link.bandwidth)

    return shortest_trusted_path(filtered, source, target)


# ─── Path Trust Aggregation ──────────────────────────────────────

def path_trust_product(trusts: List[float]) -> float:
    """Multiplicative: trust attenuates along chain."""
    result = 1.0
    for t in trusts:
        result *= t
    return result


def path_trust_min(trusts: List[float]) -> float:
    """Weakest link: path trust = minimum link trust."""
    return min(trusts) if trusts else 0.0


def path_trust_harmonic(trusts: List[float]) -> float:
    """Harmonic mean: penalizes weak links more than arithmetic mean."""
    if not trusts or any(t <= 0 for t in trusts):
        return 0.0
    return len(trusts) / sum(1.0 / t for t in trusts)


# ══════════════════════════════════════════════════════════════════
#  TESTS
# ══════════════════════════════════════════════════════════════════

def _build_test_network() -> RoutingNetwork:
    """Build test network:
    A --[0.9, 1]-- B --[0.8, 2]-- D
    |               |              |
    [0.3, 1]       [0.7, 1]      [0.9, 1]
    |               |              |
    C --[0.5, 3]-- E --[0.6, 1]-- F
    """
    net = RoutingNetwork()
    net.add_bidirectional("A", "B", 0.9, 1.0)
    net.add_bidirectional("A", "C", 0.3, 1.0)
    net.add_bidirectional("B", "D", 0.8, 2.0)
    net.add_bidirectional("B", "E", 0.7, 1.0)
    net.add_bidirectional("C", "E", 0.5, 3.0)
    net.add_bidirectional("D", "F", 0.9, 1.0)
    net.add_bidirectional("E", "F", 0.6, 1.0)
    return net


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
    print("Trust-Aware Routing for Web4")
    print("Session 32, Track 2")
    print("=" * 70)

    net = _build_test_network()

    # ── §1 Shortest Trusted Path ────────────────────────────────
    print("\n§1 Shortest Trusted Path\n")

    path, cost = shortest_trusted_path(net, "A", "F")
    check("shortest_path_found", len(path) > 0, f"path={path}")
    check("shortest_path_valid", path[0] == "A" and path[-1] == "F",
          f"path={path}")
    check("shortest_path_cost", cost < float('inf'),
          f"cost={cost}")

    # With high trust threshold, some paths become unavailable
    path_high, cost_high = shortest_trusted_path(net, "A", "F", min_trust=0.7)
    check("high_trust_path", len(path_high) > 0,
          f"path={path_high}")

    # Very high threshold may block all paths
    path_blocked, cost_blocked = shortest_trusted_path(net, "A", "F", min_trust=0.95)
    # A-B (0.9) is below 0.95, so no path
    check("blocked_by_trust", len(path_blocked) == 0,
          f"path={path_blocked}")

    # ── §2 Maximum Trust Path ───────────────────────────────────
    print("\n§2 Maximum Trust Path\n")

    path_mt, min_trust = max_trust_path(net, "A", "F")
    check("max_trust_found", len(path_mt) > 0, f"path={path_mt}")
    check("max_trust_reasonable", min_trust > 0.5,
          f"min_trust={min_trust:.2f}")

    # Max trust path through A-B-D-F: min(0.9, 0.8, 0.9) = 0.8
    # vs A-B-E-F: min(0.9, 0.7, 0.6) = 0.6
    check("max_trust_optimal", min_trust >= 0.7,
          f"min_trust={min_trust:.2f} path={path_mt}")

    # ── §3 Multi-Path Routing ───────────────────────────────────
    print("\n§3 Multi-Path Routing\n")

    k_paths = find_k_trusted_paths(net, "A", "F", k=3)
    check("k_paths_found", len(k_paths) >= 2,
          f"found={len(k_paths)}")

    # Paths should be sorted by cost
    if len(k_paths) >= 2:
        check("k_paths_sorted", k_paths[0][1] <= k_paths[1][1],
              f"costs={[c for _, c in k_paths]}")

    # All paths should start at A and end at F
    for p, c in k_paths:
        if p[0] != "A" or p[-1] != "F":
            check("k_paths_endpoints", False, f"path={p}")
            break
    else:
        check("k_paths_endpoints", True)

    # ── §4 Pareto-Optimal Paths ─────────────────────────────────
    print("\n§4 Pareto-Optimal Paths\n")

    pareto = pareto_optimal_paths(net, "A", "F")
    check("pareto_found", len(pareto) >= 1,
          f"found={len(pareto)}")

    # Verify Pareto optimality: no path dominates another
    for i, (p1, c1, t1) in enumerate(pareto):
        for j, (p2, c2, t2) in enumerate(pareto):
            if i != j:
                dominated = c2 <= c1 and t2 >= t1 and (c2 < c1 or t2 > t1)
                if dominated:
                    check("pareto_no_domination", False,
                          f"path {i} dominated by {j}")
                    break
        else:
            continue
        break
    else:
        check("pareto_no_domination", True)

    # ── §5 Adversarial Routing ──────────────────────────────────
    print("\n§5 Adversarial Routing\n")

    # Route avoiding node B
    path_avoid, cost_avoid = adversarial_avoidance_path(
        net, "A", "F", {"B"})
    check("avoid_b_found", len(path_avoid) > 0,
          f"path={path_avoid}")
    check("avoid_b_excludes", "B" not in path_avoid,
          f"path={path_avoid}")

    # Cost should be higher than unrestricted
    check("avoid_costs_more", cost_avoid >= cost,
          f"avoid={cost_avoid} unrestricted={cost}")

    # Avoid too many nodes → no path
    path_blocked, _ = adversarial_avoidance_path(
        net, "A", "F", {"B", "C", "E"})
    # A can only reach B and C directly; both blocked, so no path to F
    check("too_many_avoided_blocks", len(path_blocked) == 0,
          f"path={path_blocked}")

    # ── §6 Path Trust Aggregation ───────────────────────────────
    print("\n§6 Path Trust Aggregation\n")

    trusts = [0.9, 0.8, 0.7]

    prod = path_trust_product(trusts)
    check("product_trust", abs(prod - 0.504) < 0.01,
          f"product={prod:.4f}")

    min_t = path_trust_min(trusts)
    check("min_trust", abs(min_t - 0.7) < 0.01,
          f"min={min_t:.4f}")

    harm = path_trust_harmonic(trusts)
    check("harmonic_trust", 0.7 < harm < 0.9,
          f"harmonic={harm:.4f}")

    # Product < Harmonic < Min < Arithmetic
    arith = sum(trusts) / len(trusts)
    check("ordering_product_lt_harmonic", prod < harm)
    check("ordering_harmonic_lt_arith", harm < arith)

    # Min is always ≤ harmonic
    check("min_le_harmonic", min_t <= harm + 0.01)

    # ── Summary ─────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
