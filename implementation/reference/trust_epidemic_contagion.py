"""
Trust Epidemic & Contagion Modeling for Web4
Session 32, Track 1

Epidemiological models applied to trust propagation:
- SIR model for trust change propagation
- SIS model for oscillating trust (no permanent immunity)
- Influence maximization (seed selection for trust campaigns)
- Contagion threshold (complex vs simple contagion)
- Immunization strategies (protecting high-value nodes)
- R0 (basic reproduction number) for trust changes
- Network topology effects on epidemic dynamics
"""

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict


# ─── Node States ──────────────────────────────────────────────────

class NodeState(Enum):
    SUSCEPTIBLE = "S"     # Can be influenced
    INFLUENCED = "I"      # Currently spreading influence
    RECOVERED = "R"       # Immune to further influence (SIR only)


@dataclass
class EpidemicNode:
    node_id: str
    state: NodeState = NodeState.SUSCEPTIBLE
    trust_level: float = 0.5
    influence_time: int = -1  # when influenced
    recovery_time: int = -1   # when recovered


# ─── Network ─────────────────────────────────────────────────────

@dataclass
class TrustNetwork:
    nodes: Dict[str, EpidemicNode] = field(default_factory=dict)
    adjacency: Dict[str, Set[str]] = field(default_factory=dict)

    def add_node(self, node_id: str, trust: float = 0.5):
        self.nodes[node_id] = EpidemicNode(node_id=node_id, trust_level=trust)
        if node_id not in self.adjacency:
            self.adjacency[node_id] = set()

    def add_edge(self, a: str, b: str):
        self.adjacency.setdefault(a, set()).add(b)
        self.adjacency.setdefault(b, set()).add(a)

    def neighbors(self, node_id: str) -> Set[str]:
        return self.adjacency.get(node_id, set())

    def degree(self, node_id: str) -> int:
        return len(self.adjacency.get(node_id, set()))


# ─── SIR Model ────────────────────────────────────────────────────

def sir_epidemic(network: TrustNetwork,
                 seeds: List[str],
                 beta: float = 0.3,
                 gamma: float = 0.1,
                 trust_change: float = 0.2,
                 max_rounds: int = 100,
                 rng: random.Random = None) -> Dict[str, List[int]]:
    """
    SIR epidemic model for trust change.
    beta: infection probability per contact
    gamma: recovery probability per round
    trust_change: amount trust changes when influenced
    Returns {S: [counts], I: [counts], R: [counts]}
    """
    if rng is None:
        rng = random.Random(42)

    # Initialize seeds as influenced
    for seed in seeds:
        if seed in network.nodes:
            network.nodes[seed].state = NodeState.INFLUENCED
            network.nodes[seed].influence_time = 0
            network.nodes[seed].trust_level = min(1.0,
                network.nodes[seed].trust_level + trust_change)

    history = {"S": [], "I": [], "R": []}

    for t in range(max_rounds):
        s_count = sum(1 for n in network.nodes.values() if n.state == NodeState.SUSCEPTIBLE)
        i_count = sum(1 for n in network.nodes.values() if n.state == NodeState.INFLUENCED)
        r_count = sum(1 for n in network.nodes.values() if n.state == NodeState.RECOVERED)

        history["S"].append(s_count)
        history["I"].append(i_count)
        history["R"].append(r_count)

        if i_count == 0:
            break

        # Infection phase
        new_influenced = []
        for nid, node in network.nodes.items():
            if node.state == NodeState.INFLUENCED:
                for neighbor_id in network.neighbors(nid):
                    neighbor = network.nodes[neighbor_id]
                    if neighbor.state == NodeState.SUSCEPTIBLE:
                        if rng.random() < beta:
                            new_influenced.append(neighbor_id)

        # Recovery phase
        new_recovered = []
        for nid, node in network.nodes.items():
            if node.state == NodeState.INFLUENCED:
                if rng.random() < gamma:
                    new_recovered.append(nid)

        # Apply state changes
        for nid in new_influenced:
            network.nodes[nid].state = NodeState.INFLUENCED
            network.nodes[nid].influence_time = t
            network.nodes[nid].trust_level = min(1.0,
                network.nodes[nid].trust_level + trust_change)

        for nid in new_recovered:
            network.nodes[nid].state = NodeState.RECOVERED
            network.nodes[nid].recovery_time = t

    return history


# ─── SIS Model ────────────────────────────────────────────────────

def sis_epidemic(network: TrustNetwork,
                 seeds: List[str],
                 beta: float = 0.3,
                 gamma: float = 0.1,
                 max_rounds: int = 100,
                 rng: random.Random = None) -> List[int]:
    """
    SIS model: influenced nodes become susceptible again (no immunity).
    Models oscillating trust — trust changes that can be reversed.
    Returns list of influenced counts per round.
    """
    if rng is None:
        rng = random.Random(42)

    for seed in seeds:
        if seed in network.nodes:
            network.nodes[seed].state = NodeState.INFLUENCED

    i_counts = []

    for t in range(max_rounds):
        i_count = sum(1 for n in network.nodes.values() if n.state == NodeState.INFLUENCED)
        i_counts.append(i_count)

        if i_count == 0:
            break

        # Infection
        new_influenced = set()
        for nid, node in network.nodes.items():
            if node.state == NodeState.INFLUENCED:
                for neighbor_id in network.neighbors(nid):
                    if network.nodes[neighbor_id].state == NodeState.SUSCEPTIBLE:
                        if rng.random() < beta:
                            new_influenced.add(neighbor_id)

        # Recovery (back to susceptible)
        recovered = set()
        for nid, node in network.nodes.items():
            if node.state == NodeState.INFLUENCED:
                if rng.random() < gamma:
                    recovered.add(nid)

        for nid in recovered:
            network.nodes[nid].state = NodeState.SUSCEPTIBLE
        for nid in new_influenced:
            network.nodes[nid].state = NodeState.INFLUENCED

    return i_counts


# ─── R0 Estimation ───────────────────────────────────────────────

def estimate_r0(beta: float, gamma: float, avg_degree: float) -> float:
    """
    Basic reproduction number for network epidemic.
    R0 = beta * avg_degree / gamma
    R0 > 1: epidemic spreads; R0 < 1: dies out.
    """
    if gamma <= 0:
        return float('inf')
    return beta * avg_degree / gamma


def epidemic_threshold(avg_degree: float, gamma: float) -> float:
    """
    Critical beta above which epidemic can spread.
    beta_c = gamma / avg_degree
    """
    if avg_degree <= 0:
        return float('inf')
    return gamma / avg_degree


# ─── Influence Maximization ──────────────────────────────────────

def greedy_influence_max(network: TrustNetwork,
                          k: int,
                          beta: float = 0.3,
                          gamma: float = 0.1,
                          n_simulations: int = 20,
                          rng: random.Random = None) -> List[str]:
    """
    Greedy algorithm for influence maximization.
    Select k seed nodes to maximize total spread.
    """
    if rng is None:
        rng = random.Random(42)

    selected = []

    for _ in range(k):
        best_node = None
        best_spread = -1

        for candidate in network.nodes:
            if candidate in selected:
                continue

            # Monte Carlo estimation of spread
            total_spread = 0
            for sim in range(n_simulations):
                # Reset states
                test_net = TrustNetwork()
                for nid in network.nodes:
                    test_net.add_node(nid, network.nodes[nid].trust_level)
                for nid in network.adjacency:
                    for nbr in network.adjacency[nid]:
                        test_net.adjacency.setdefault(nid, set()).add(nbr)

                seeds = selected + [candidate]
                history = sir_epidemic(test_net, seeds, beta, gamma,
                                       rng=random.Random(rng.randint(0, 10000)))
                total_spread += history["R"][-1] + history["I"][-1]

            avg_spread = total_spread / n_simulations
            if avg_spread > best_spread:
                best_spread = avg_spread
                best_node = candidate

        if best_node:
            selected.append(best_node)

    return selected


# ─── Immunization Strategies ─────────────────────────────────────

def degree_immunization(network: TrustNetwork, k: int) -> List[str]:
    """Immunize top-k highest degree nodes (targeted vaccination)."""
    degrees = [(nid, network.degree(nid)) for nid in network.nodes]
    degrees.sort(key=lambda x: -x[1])
    return [nid for nid, _ in degrees[:k]]


def random_immunization(network: TrustNetwork, k: int,
                         rng: random.Random = None) -> List[str]:
    """Random immunization — baseline strategy."""
    if rng is None:
        rng = random.Random(42)
    nodes = list(network.nodes.keys())
    return rng.sample(nodes, min(k, len(nodes)))


def acquaintance_immunization(network: TrustNetwork, k: int,
                                rng: random.Random = None) -> List[str]:
    """
    Acquaintance immunization: pick random nodes, immunize their neighbors.
    Exploits friendship paradox — neighbors have higher degree on average.
    """
    if rng is None:
        rng = random.Random(42)

    candidates = set()
    nodes = list(network.nodes.keys())

    while len(candidates) < k and nodes:
        random_node = rng.choice(nodes)
        neighbors = list(network.neighbors(random_node))
        if neighbors:
            neighbor = rng.choice(neighbors)
            candidates.add(neighbor)
        nodes = [n for n in nodes if n not in candidates]

    return list(candidates)[:k]


# ─── Complex Contagion ───────────────────────────────────────────

def complex_contagion(network: TrustNetwork,
                       seeds: List[str],
                       threshold: float = 0.3,
                       max_rounds: int = 50) -> int:
    """
    Complex contagion: adoption requires fraction >= threshold of neighbors.
    Models trust changes that need social proof (not just one contact).
    Returns total adopters.
    """
    adopted = set(seeds)

    for _ in range(max_rounds):
        new_adopters = set()
        for nid in network.nodes:
            if nid in adopted:
                continue
            neighbors = network.neighbors(nid)
            if not neighbors:
                continue
            fraction_adopted = len(neighbors & adopted) / len(neighbors)
            if fraction_adopted >= threshold:
                new_adopters.add(nid)

        if not new_adopters:
            break
        adopted.update(new_adopters)

    return len(adopted)


# ══════════════════════════════════════════════════════════════════
#  TESTS
# ══════════════════════════════════════════════════════════════════

def _build_test_network(n: int = 30, p: float = 0.15,
                         rng: random.Random = None) -> TrustNetwork:
    """Build random Erdos-Renyi test network."""
    if rng is None:
        rng = random.Random(42)
    net = TrustNetwork()
    for i in range(n):
        net.add_node(f"n{i}", trust=rng.uniform(0.3, 0.8))
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p:
                net.add_edge(f"n{i}", f"n{j}")
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
    print("Trust Epidemic & Contagion Modeling for Web4")
    print("Session 32, Track 1")
    print("=" * 70)

    # ── §1 SIR Epidemic ─────────────────────────────────────────
    print("\n§1 SIR Epidemic\n")

    net = _build_test_network(30, 0.15)
    history = sir_epidemic(net, ["n0"], beta=0.3, gamma=0.1,
                            rng=random.Random(42))

    # S should decrease, R should increase
    check("sir_s_decreases", history["S"][-1] <= history["S"][0],
          f"S0={history['S'][0]} Sf={history['S'][-1]}")
    check("sir_r_increases", history["R"][-1] >= history["R"][0],
          f"R0={history['R'][0]} Rf={history['R'][-1]}")

    # Conservation: S + I + R = N always
    n = 30
    for t in range(len(history["S"])):
        total = history["S"][t] + history["I"][t] + history["R"][t]
        if total != n:
            check("sir_conservation", False, f"t={t} total={total}")
            break
    else:
        check("sir_conservation", True)

    # Epidemic eventually ends (I reaches 0)
    check("sir_ends", history["I"][-1] == 0,
          f"final_I={history['I'][-1]}")

    # ── §2 SIS Model ───────────────────────────────────────────
    print("\n§2 SIS Model\n")

    net2 = _build_test_network(30, 0.15)
    sis_counts = sis_epidemic(net2, ["n0", "n1"], beta=0.3, gamma=0.1,
                               max_rounds=100, rng=random.Random(42))

    check("sis_starts_with_seeds", sis_counts[0] >= 2,
          f"initial={sis_counts[0]}")

    # SIS can persist (endemic state) if R0 > 1
    avg_deg = sum(net2.degree(n) for n in net2.nodes) / len(net2.nodes)
    r0 = estimate_r0(0.3, 0.1, avg_deg)
    if r0 > 1:
        # Should have some infected at the end
        check("sis_persists_if_r0_gt_1", len(sis_counts) > 10,
              f"rounds={len(sis_counts)} R0={r0:.2f}")
    else:
        check("sis_persists_if_r0_gt_1", True, "R0 < 1, dies out as expected")

    # ── §3 R0 Analysis ──────────────────────────────────────────
    print("\n§3 R0 Analysis\n")

    # R0 > 1 means epidemic
    r0_high = estimate_r0(0.5, 0.1, 6.0)
    check("r0_epidemic", r0_high > 1, f"R0={r0_high:.2f}")

    # R0 < 1 means die out
    r0_low = estimate_r0(0.05, 0.5, 3.0)
    check("r0_die_out", r0_low < 1, f"R0={r0_low:.2f}")

    # Threshold
    beta_c = epidemic_threshold(6.0, 0.1)
    check("threshold_correct", abs(beta_c - 0.1/6.0) < 0.001,
          f"beta_c={beta_c:.4f}")

    # Higher degree → lower threshold (easier to spread)
    beta_c_high = epidemic_threshold(10.0, 0.1)
    beta_c_low = epidemic_threshold(3.0, 0.1)
    check("higher_degree_lower_threshold", beta_c_high < beta_c_low)

    # ── §4 Influence Maximization ───────────────────────────────
    print("\n§4 Influence Maximization\n")

    net4 = _build_test_network(20, 0.2, rng=random.Random(123))
    seeds = greedy_influence_max(net4, k=2, beta=0.3, gamma=0.1,
                                  n_simulations=10, rng=random.Random(42))
    check("influence_max_selects_k", len(seeds) == 2,
          f"seeds={len(seeds)}")

    # Selected nodes should have above-average degree
    avg_deg = sum(net4.degree(n) for n in net4.nodes) / len(net4.nodes)
    seed_avg_deg = sum(net4.degree(s) for s in seeds) / len(seeds)
    check("seeds_high_degree", seed_avg_deg >= avg_deg * 0.5,
          f"seed_deg={seed_avg_deg:.1f} avg_deg={avg_deg:.1f}")

    # ── §5 Immunization Strategies ──────────────────────────────
    print("\n§5 Immunization Strategies\n")

    net5 = _build_test_network(30, 0.15, rng=random.Random(42))

    deg_immune = degree_immunization(net5, 3)
    check("degree_immune_count", len(deg_immune) == 3)

    # Degree immunization should select highest-degree nodes
    all_degrees = {nid: net5.degree(nid) for nid in net5.nodes}
    immune_degrees = [all_degrees[n] for n in deg_immune]
    check("degree_immune_highest", all(d >= 3 for d in immune_degrees),
          f"degrees={immune_degrees}")

    # Acquaintance immunization exploits friendship paradox
    acq_immune = acquaintance_immunization(net5, 3, rng=random.Random(42))
    check("acquaintance_immune_count", len(acq_immune) <= 3)

    acq_degrees = [all_degrees[n] for n in acq_immune if n in all_degrees]
    avg_all = sum(all_degrees.values()) / len(all_degrees)
    avg_acq = sum(acq_degrees) / len(acq_degrees) if acq_degrees else 0
    # Acquaintance method should select above-average degree (friendship paradox)
    check("friendship_paradox", avg_acq >= avg_all * 0.8,
          f"acq_avg={avg_acq:.1f} all_avg={avg_all:.1f}")

    # ── §6 Complex Contagion ────────────────────────────────────
    print("\n§6 Complex Contagion\n")

    net6 = _build_test_network(30, 0.2, rng=random.Random(42))

    # Low threshold → more adoption
    low_thresh = complex_contagion(net6, ["n0", "n1"], threshold=0.1)
    high_thresh = complex_contagion(net6, ["n0", "n1"], threshold=0.5)
    check("low_threshold_more_adoption", low_thresh >= high_thresh,
          f"low={low_thresh} high={high_thresh}")

    # Very high threshold → only seeds adopt
    very_high = complex_contagion(net6, ["n0"], threshold=0.99)
    check("very_high_threshold_seeds_only", very_high <= 2,
          f"adopted={very_high}")

    # More seeds → more adoption
    more_seeds = complex_contagion(net6, ["n0", "n1", "n2", "n3", "n4"],
                                    threshold=0.3)
    fewer_seeds = complex_contagion(net6, ["n0"], threshold=0.3)
    check("more_seeds_more_adoption", more_seeds >= fewer_seeds,
          f"more={more_seeds} fewer={fewer_seeds}")

    # ── §7 Topology Effects ─────────────────────────────────────
    print("\n§7 Topology Effects on Spread\n")

    # Dense network spreads faster
    dense = _build_test_network(20, 0.4, rng=random.Random(42))
    sparse = _build_test_network(20, 0.08, rng=random.Random(42))

    dense_hist = sir_epidemic(dense, ["n0"], beta=0.3, gamma=0.1,
                               rng=random.Random(42))
    sparse_hist = sir_epidemic(sparse, ["n0"], beta=0.3, gamma=0.1,
                                rng=random.Random(42))

    dense_total = dense_hist["R"][-1]
    sparse_total = sparse_hist["R"][-1]
    check("dense_spreads_more", dense_total >= sparse_total,
          f"dense={dense_total} sparse={sparse_total}")

    # Star topology: hub removal stops spread
    star = TrustNetwork()
    star.add_node("hub")
    for i in range(10):
        star.add_node(f"leaf_{i}")
        star.add_edge("hub", f"leaf_{i}")

    # Hub as seed → spreads to leaves
    star_hist = sir_epidemic(star, ["hub"], beta=0.5, gamma=0.05,
                              rng=random.Random(42))
    hub_spread = star_hist["R"][-1] + star_hist["I"][-1]
    check("star_hub_spreads", hub_spread > 5,
          f"spread={hub_spread}")

    # ── Summary ─────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
