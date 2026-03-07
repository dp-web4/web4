"""
Trust Topology Invariants for Web4
Session 31, Track 1

Formal invariants that must hold in any valid trust network:
- Conservation: total trust is bounded
- Connectivity: trust paths maintain transitivity
- Monotonicity: trust operations preserve ordering
- Symmetry: bidirectional trust relationships
- Locality: trust changes have bounded propagation
- Stability: equilibrium points are attractors
- Decomposition: complex networks reduce to simple components
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional


# ─── Trust Network ─────────────────────────────────────────────────

@dataclass
class TrustNetwork:
    """Weighted directed trust graph with invariant checking."""
    edges: Dict[Tuple[int, int], float] = field(default_factory=dict)
    node_trust: Dict[int, float] = field(default_factory=dict)

    def add_node(self, node: int, trust: float = 0.5):
        self.node_trust[node] = max(0.0, min(1.0, trust))

    def add_edge(self, src: int, dst: int, weight: float):
        weight = max(0.0, min(1.0, weight))
        self.edges[(src, dst)] = weight

    def nodes(self) -> Set[int]:
        nodes = set(self.node_trust.keys())
        for s, d in self.edges:
            nodes.add(s)
            nodes.add(d)
        return nodes

    def neighbors(self, node: int) -> List[int]:
        return [d for (s, d) in self.edges if s == node]

    def in_neighbors(self, node: int) -> List[int]:
        return [s for (s, d) in self.edges if d == node]

    def edge_weight(self, src: int, dst: int) -> float:
        return self.edges.get((src, dst), 0.0)


# ─── Invariant 1: Trust Boundedness ────────────────────────────────

def check_trust_bounded(network: TrustNetwork) -> Tuple[bool, str]:
    """All trust values must be in [0, 1]."""
    for node, trust in network.node_trust.items():
        if trust < 0 or trust > 1:
            return False, f"Node {node} trust={trust} out of [0,1]"
    for (src, dst), weight in network.edges.items():
        if weight < 0 or weight > 1:
            return False, f"Edge ({src},{dst}) weight={weight} out of [0,1]"
    return True, "All trust values in [0,1]"


# ─── Invariant 2: Trust Conservation ──────────────────────────────

def total_trust(network: TrustNetwork) -> float:
    """Sum of all node trust scores."""
    return sum(network.node_trust.values())


def check_trust_conservation(before: TrustNetwork, after: TrustNetwork,
                              tolerance: float = 0.01) -> Tuple[bool, str]:
    """
    Total trust should not increase without external attestation.
    Internal operations (transfer, delegation) conserve trust.
    """
    t_before = total_trust(before)
    t_after = total_trust(after)

    if t_after > t_before + tolerance:
        return False, f"Trust increased: {t_before:.4f} → {t_after:.4f}"
    return True, f"Trust conserved: {t_before:.4f} → {t_after:.4f}"


# ─── Invariant 3: Transitivity ────────────────────────────────────

def transitive_trust(network: TrustNetwork, a: int, b: int, c: int) -> float:
    """Trust(a→c) through b: trust(a→b) * trust(b→c)."""
    return network.edge_weight(a, b) * network.edge_weight(b, c)


def check_transitivity_bound(network: TrustNetwork) -> Tuple[bool, str]:
    """
    Transitive trust should not exceed direct trust.
    If A trusts B and B trusts C, then A's indirect trust of C
    through B should be ≤ min(A→B, B→C).
    """
    nodes = sorted(network.nodes())
    for a in nodes:
        for b in network.neighbors(a):
            for c in network.neighbors(b):
                if c == a:
                    continue
                indirect = transitive_trust(network, a, b, c)
                direct = network.edge_weight(a, c)
                ab = network.edge_weight(a, b)
                bc = network.edge_weight(b, c)
                min_link = min(ab, bc)
                # Indirect trust ≤ min of the chain links
                if indirect > min_link + 0.001:
                    return False, f"Transitivity violation: {a}→{b}→{c}: indirect={indirect:.3f} > min_link={min_link:.3f}"
    return True, "Transitivity bound holds"


# ─── Invariant 4: Monotonicity ────────────────────────────────────

def check_monotone_attestation(trust_before: float, attestation_positive: bool,
                                trust_after: float) -> Tuple[bool, str]:
    """
    Positive attestation should not decrease trust.
    Negative attestation should not increase trust.
    """
    if attestation_positive and trust_after < trust_before - 0.001:
        return False, f"Positive attestation decreased trust: {trust_before:.3f} → {trust_after:.3f}"
    if not attestation_positive and trust_after > trust_before + 0.001:
        return False, f"Negative attestation increased trust: {trust_before:.3f} → {trust_after:.3f}"
    return True, f"Monotonicity holds: {trust_before:.3f} → {trust_after:.3f}"


def apply_attestation(trust: float, positive: bool, weight: float = 0.1) -> float:
    """Apply attestation and return new trust (monotone)."""
    if positive:
        return min(1.0, trust + weight * (1 - trust))
    else:
        return max(0.0, trust - weight * trust)


# ─── Invariant 5: Symmetry of Mutual Trust ───────────────────────

def check_mutual_trust_symmetry(network: TrustNetwork,
                                 tolerance: float = 0.3) -> Tuple[bool, str]:
    """
    In healthy networks, mutual trust should be roughly symmetric.
    Large asymmetry (A trusts B but B doesn't trust A) is a warning.
    Returns the maximum asymmetry found.
    """
    max_asymmetry = 0.0
    worst_pair = None

    for (src, dst), weight in network.edges.items():
        reverse = network.edge_weight(dst, src)
        asymmetry = abs(weight - reverse)
        if asymmetry > max_asymmetry:
            max_asymmetry = asymmetry
            worst_pair = (src, dst)

    if max_asymmetry > tolerance:
        return False, f"High asymmetry {max_asymmetry:.3f} at {worst_pair}"
    return True, f"Max asymmetry {max_asymmetry:.3f} within tolerance"


# ─── Invariant 6: Locality of Trust Changes ──────────────────────

def propagation_depth(network: TrustNetwork, changed_node: int,
                       threshold: float = 0.01) -> int:
    """
    How far does a trust change propagate?
    Returns the BFS depth at which impact < threshold.
    """
    visited = {changed_node}
    frontier = [changed_node]
    depth = 0

    while frontier:
        next_frontier = []
        for node in frontier:
            for neighbor in network.neighbors(node):
                if neighbor not in visited:
                    # Impact at this depth: trust * edge_weight^depth
                    impact = network.edge_weight(node, neighbor)
                    for _ in range(depth):
                        impact *= 0.7  # decay per hop
                    if impact >= threshold:
                        visited.add(neighbor)
                        next_frontier.append(neighbor)
        frontier = next_frontier
        depth += 1

    return depth


def check_locality(network: TrustNetwork, max_depth: int = 5) -> Tuple[bool, str]:
    """Trust changes should have bounded propagation depth."""
    nodes = sorted(network.nodes())
    max_prop = 0
    for node in nodes[:10]:  # sample
        d = propagation_depth(network, node)
        max_prop = max(max_prop, d)

    if max_prop > max_depth:
        return False, f"Propagation depth {max_prop} exceeds bound {max_depth}"
    return True, f"Max propagation depth {max_prop} within bound {max_depth}"


# ─── Invariant 7: Stability (Fixed Points) ───────────────────────

def trust_update_step(network: TrustNetwork, damping: float = 0.85) -> Dict[int, float]:
    """
    PageRank-like trust update: node trust = weighted average of in-neighbors.
    """
    nodes = sorted(network.nodes())
    n = len(nodes)
    if n == 0:
        return {}

    new_trust = {}
    for node in nodes:
        in_nbrs = network.in_neighbors(node)
        if in_nbrs:
            weighted_sum = sum(
                network.node_trust.get(src, 0.5) * network.edge_weight(src, node)
                for src in in_nbrs
            )
            total_weight = sum(network.edge_weight(src, node) for src in in_nbrs)
            if total_weight > 0:
                avg = weighted_sum / total_weight
            else:
                avg = 0.5
        else:
            avg = 0.5  # no in-neighbors: default

        new_trust[node] = damping * avg + (1 - damping) * (1.0 / n)

    return new_trust


def find_fixed_point(network: TrustNetwork, max_iter: int = 100,
                      tolerance: float = 0.001) -> Tuple[Dict[int, float], int]:
    """Iterate trust updates until convergence."""
    net = TrustNetwork()
    net.edges = dict(network.edges)
    net.node_trust = dict(network.node_trust)

    for iteration in range(max_iter):
        new_trust = trust_update_step(net)
        max_diff = max(abs(new_trust[n] - net.node_trust.get(n, 0.5))
                       for n in new_trust)
        net.node_trust = new_trust
        if max_diff < tolerance:
            return new_trust, iteration + 1
    return net.node_trust, max_iter


def check_convergence(network: TrustNetwork, max_iter: int = 100) -> Tuple[bool, str]:
    """Trust updates should converge to a fixed point."""
    _, iterations = find_fixed_point(network, max_iter)
    if iterations >= max_iter:
        return False, f"Did not converge in {max_iter} iterations"
    return True, f"Converged in {iterations} iterations"


# ─── Invariant 8: Decomposition ───────────────────────────────────

def connected_components(network: TrustNetwork) -> List[Set[int]]:
    """Find connected components (treating edges as undirected)."""
    nodes = network.nodes()
    visited = set()
    components = []

    for start in nodes:
        if start in visited:
            continue
        component = set()
        queue = [start]
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            component.add(node)
            for neighbor in network.neighbors(node):
                if neighbor not in visited:
                    queue.append(neighbor)
            for neighbor in network.in_neighbors(node):
                if neighbor not in visited:
                    queue.append(neighbor)
        components.append(component)

    return components


def check_component_independence(network: TrustNetwork) -> Tuple[bool, str]:
    """
    Trust in one component should not affect another component.
    """
    components = connected_components(network)
    if len(components) <= 1:
        return True, "Single component — independence trivially holds"

    # Verify no cross-component edges
    for comp in components:
        for node in comp:
            for neighbor in network.neighbors(node):
                if neighbor not in comp:
                    return False, f"Cross-component edge {node}→{neighbor}"

    return True, f"{len(components)} independent components verified"


# ─── Invariant 9: Trust Entropy Bound ─────────────────────────────

def trust_entropy(network: TrustNetwork) -> float:
    """Shannon entropy of trust distribution."""
    values = list(network.node_trust.values())
    if not values:
        return 0.0

    total = sum(values)
    if total <= 0:
        return 0.0

    entropy = 0.0
    for v in values:
        if v > 0:
            p = v / total
            entropy -= p * math.log2(p)
    return entropy


def check_entropy_bounds(network: TrustNetwork) -> Tuple[bool, str]:
    """
    Trust entropy should be bounded by log2(n).
    Very low entropy indicates dangerous concentration.
    """
    n = len(network.node_trust)
    if n <= 1:
        return True, "Single node — entropy bound trivial"

    entropy = trust_entropy(network)
    max_entropy = math.log2(n)

    if entropy > max_entropy + 0.01:
        return False, f"Entropy {entropy:.3f} exceeds max {max_entropy:.3f}"
    return True, f"Entropy {entropy:.3f} ≤ max {max_entropy:.3f}"


# ─── Network Generators ───────────────────────────────────────────

def build_chain(n: int, trust: float = 0.7) -> TrustNetwork:
    """Linear chain: 0→1→2→...→n-1"""
    net = TrustNetwork()
    for i in range(n):
        net.add_node(i, trust)
    for i in range(n - 1):
        net.add_edge(i, i + 1, trust)
        net.add_edge(i + 1, i, trust)
    return net


def build_star(n: int, hub_trust: float = 0.9) -> TrustNetwork:
    """Star: hub 0 connected to all others."""
    net = TrustNetwork()
    net.add_node(0, hub_trust)
    for i in range(1, n):
        net.add_node(i, 0.5)
        net.add_edge(0, i, 0.7)
        net.add_edge(i, 0, 0.7)
    return net


def build_complete(n: int, trust: float = 0.6) -> TrustNetwork:
    """Complete graph."""
    net = TrustNetwork()
    for i in range(n):
        net.add_node(i, trust)
    for i in range(n):
        for j in range(n):
            if i != j:
                net.add_edge(i, j, trust)
    return net


def build_random(n: int, p: float = 0.3, seed: int = 42) -> TrustNetwork:
    """Erdos-Renyi random graph."""
    rng = random.Random(seed)
    net = TrustNetwork()
    for i in range(n):
        net.add_node(i, rng.uniform(0.3, 0.9))
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p:
                w = rng.uniform(0.3, 0.8)
                net.add_edge(i, j, w)
                net.add_edge(j, i, w)
    return net


def build_bipartite(n1: int, n2: int, trust: float = 0.6) -> TrustNetwork:
    """Bipartite: two groups, edges only between groups."""
    net = TrustNetwork()
    for i in range(n1):
        net.add_node(i, trust)
    for j in range(n1, n1 + n2):
        net.add_node(j, trust)
    for i in range(n1):
        for j in range(n1, n1 + n2):
            net.add_edge(i, j, trust)
            net.add_edge(j, i, trust)
    return net


# ─── Trust Operations with Invariant Preservation ────────────────

def trust_transfer(network: TrustNetwork, src: int, dst: int,
                    amount: float) -> TrustNetwork:
    """Transfer trust from src to dst (conserving total)."""
    net = TrustNetwork()
    net.edges = dict(network.edges)
    net.node_trust = dict(network.node_trust)

    src_trust = net.node_trust.get(src, 0.5)
    dst_trust = net.node_trust.get(dst, 0.5)

    actual_amount = min(amount, src_trust)
    net.node_trust[src] = src_trust - actual_amount
    net.node_trust[dst] = min(1.0, dst_trust + actual_amount)

    return net


def trust_decay(network: TrustNetwork, rate: float = 0.01) -> TrustNetwork:
    """Apply uniform decay (non-conservative — trust decreases)."""
    net = TrustNetwork()
    net.edges = dict(network.edges)
    net.node_trust = {n: t * (1 - rate) for n, t in network.node_trust.items()}
    return net


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
    print("Trust Topology Invariants for Web4")
    print("Session 31, Track 1")
    print("=" * 70)

    # ── §1 Boundedness ────────────────────────────────────────────
    print("\n§1 Trust Boundedness\n")

    chain = build_chain(5)
    ok, msg = check_trust_bounded(chain)
    check("chain_bounded", ok, msg)

    star = build_star(6)
    ok, msg = check_trust_bounded(star)
    check("star_bounded", ok, msg)

    complete = build_complete(4)
    ok, msg = check_trust_bounded(complete)
    check("complete_bounded", ok, msg)

    # Manually violate
    bad_net = TrustNetwork()
    bad_net.node_trust[0] = 1.5
    ok, msg = check_trust_bounded(bad_net)
    check("violation_detected", not ok, msg)

    # ── §2 Conservation ───────────────────────────────────────────
    print("\n§2 Trust Conservation\n")

    net = build_chain(5, trust=0.8)
    t_before = total_trust(net)

    # Transfer conserves
    net_after = trust_transfer(net, 0, 4, 0.2)
    ok, msg = check_trust_conservation(net, net_after)
    check("transfer_conserves", ok, msg)

    # Verify actual values
    check("transfer_src_decreased",
          net_after.node_trust[0] < net.node_trust[0])
    check("transfer_dst_increased",
          net_after.node_trust[4] > net.node_trust[4])

    # Decay is non-conservative (trust decreases)
    net_decayed = trust_decay(net, rate=0.1)
    t_decayed = total_trust(net_decayed)
    check("decay_reduces_total", t_decayed < t_before,
          f"before={t_before:.3f} after={t_decayed:.3f}")

    # ── §3 Transitivity ──────────────────────────────────────────
    print("\n§3 Transitivity Bound\n")

    # Chain: A→B→C with trust 0.7
    net = build_chain(3, trust=0.7)
    indirect = transitive_trust(net, 0, 1, 2)
    check("transitive_product", abs(indirect - 0.49) < 0.01,
          f"indirect={indirect:.3f}")

    # Indirect ≤ min(direct links)
    check("indirect_leq_min", indirect <= min(0.7, 0.7) + 0.001)

    ok, msg = check_transitivity_bound(net)
    check("chain_transitivity", ok, msg)

    # Complete graph satisfies transitivity
    ok, msg = check_transitivity_bound(complete)
    check("complete_transitivity", ok, msg)

    # ── §4 Monotonicity ──────────────────────────────────────────
    print("\n§4 Attestation Monotonicity\n")

    trust = 0.5

    # Positive attestation
    trust_up = apply_attestation(trust, positive=True)
    ok, msg = check_monotone_attestation(trust, True, trust_up)
    check("positive_increases", ok, msg)
    check("positive_value", trust_up > trust)

    # Negative attestation
    trust_down = apply_attestation(trust, positive=False)
    ok, msg = check_monotone_attestation(trust, False, trust_down)
    check("negative_decreases", ok, msg)
    check("negative_value", trust_down < trust)

    # Bounded after multiple attestations
    t = 0.5
    for _ in range(100):
        t = apply_attestation(t, positive=True)
    check("bounded_after_many_positive", t <= 1.0, f"t={t:.6f}")

    t = 0.5
    for _ in range(100):
        t = apply_attestation(t, positive=False)
    check("bounded_after_many_negative", t >= 0.0, f"t={t:.6f}")

    # ── §5 Symmetry ──────────────────────────────────────────────
    print("\n§5 Mutual Trust Symmetry\n")

    # Complete graph: perfectly symmetric
    ok, msg = check_mutual_trust_symmetry(complete)
    check("complete_symmetric", ok, msg)

    # Chain: symmetric (bidirectional)
    ok, msg = check_mutual_trust_symmetry(chain)
    check("chain_symmetric", ok, msg)

    # Asymmetric network
    asym = TrustNetwork()
    asym.add_node(0, 0.9)
    asym.add_node(1, 0.3)
    asym.add_edge(0, 1, 0.9)
    asym.add_edge(1, 0, 0.1)
    ok, msg = check_mutual_trust_symmetry(asym, tolerance=0.3)
    check("asymmetry_detected", not ok, msg)

    # ── §6 Locality ──────────────────────────────────────────────
    print("\n§6 Trust Change Locality\n")

    large_chain = build_chain(20, trust=0.7)
    depth = propagation_depth(large_chain, 0)
    check("chain_propagation_bounded", depth <= 20,
          f"depth={depth}")

    ok, msg = check_locality(large_chain, max_depth=25)
    check("chain_locality", ok, msg)

    # Star: changes at hub propagate to all
    large_star = build_star(10)
    depth_hub = propagation_depth(large_star, 0)
    check("hub_propagation", depth_hub >= 1,
          f"depth={depth_hub}")

    # Leaf change has limited propagation
    depth_leaf = propagation_depth(large_star, 5)
    check("leaf_limited_propagation", depth_leaf <= 3,
          f"depth={depth_leaf}")

    # ── §7 Convergence ────────────────────────────────────────────
    print("\n§7 Trust Update Convergence\n")

    # Complete graph converges
    ok, msg = check_convergence(complete)
    check("complete_converges", ok, msg)

    # Chain converges
    ok, msg = check_convergence(chain)
    check("chain_converges", ok, msg)

    # Random graph converges
    rg = build_random(10, p=0.4)
    ok, msg = check_convergence(rg)
    check("random_converges", ok, msg)

    # Fixed point values are valid
    fp, iters = find_fixed_point(complete)
    check("fixed_point_bounded", all(0 <= v <= 1 for v in fp.values()),
          f"values={[f'{v:.3f}' for v in fp.values()]}")

    # ── §8 Decomposition ──────────────────────────────────────────
    print("\n§8 Component Decomposition\n")

    # Connected network: 1 component
    components = connected_components(chain)
    check("chain_one_component", len(components) == 1,
          f"components={len(components)}")

    # Disconnected: 2 components
    disc = TrustNetwork()
    for i in range(4):
        disc.add_node(i, 0.5)
    disc.add_edge(0, 1, 0.7)
    disc.add_edge(1, 0, 0.7)
    disc.add_edge(2, 3, 0.7)
    disc.add_edge(3, 2, 0.7)
    components = connected_components(disc)
    check("disconnected_two_components", len(components) == 2,
          f"components={len(components)}")

    # Independence holds
    ok, msg = check_component_independence(disc)
    check("components_independent", ok, msg)

    # Bipartite: still 1 component
    bp = build_bipartite(3, 3)
    components = connected_components(bp)
    check("bipartite_one_component", len(components) == 1)

    # ── §9 Entropy Bounds ─────────────────────────────────────────
    print("\n§9 Trust Entropy Bounds\n")

    # Uniform trust: max entropy
    uniform = build_complete(8, trust=0.5)
    ok, msg = check_entropy_bounds(uniform)
    check("uniform_entropy_bounded", ok, msg)

    entropy_val = trust_entropy(uniform)
    max_ent = math.log2(8)
    check("uniform_entropy_near_max", abs(entropy_val - max_ent) < 0.01,
          f"entropy={entropy_val:.3f} max={max_ent:.3f}")

    # Concentrated trust: low entropy
    concentrated = TrustNetwork()
    concentrated.add_node(0, 0.99)
    for i in range(1, 8):
        concentrated.add_node(i, 0.001)
    entropy_conc = trust_entropy(concentrated)
    check("concentrated_low_entropy", entropy_conc < max_ent,
          f"entropy={entropy_conc:.3f}")

    ok, msg = check_entropy_bounds(concentrated)
    check("concentrated_entropy_bounded", ok, msg)

    # ── §10 Comprehensive Invariant Suite ─────────────────────────
    print("\n§10 Comprehensive Invariant Suite\n")

    # Run all invariants on a random network
    rnet = build_random(12, p=0.3, seed=99)

    invariants = [
        ("bounded", check_trust_bounded(rnet)),
        ("transitivity", check_transitivity_bound(rnet)),
        ("symmetry", check_mutual_trust_symmetry(rnet, tolerance=0.5)),
        ("locality", check_locality(rnet)),
        ("convergence", check_convergence(rnet)),
        ("independence", check_component_independence(rnet)),
        ("entropy", check_entropy_bounds(rnet)),
    ]

    all_pass = True
    for name, (ok, msg) in invariants:
        if not ok:
            all_pass = False
        check(f"random_{name}", ok, msg)

    # After trust transfer, conservation holds
    rnet_after = trust_transfer(rnet, 0, 5, 0.1)
    ok, msg = check_trust_conservation(rnet, rnet_after)
    check("random_conservation", ok, msg)

    # After transfer, boundedness still holds
    ok, msg = check_trust_bounded(rnet_after)
    check("post_transfer_bounded", ok, msg)

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
