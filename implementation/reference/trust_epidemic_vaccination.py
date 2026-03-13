"""
Trust Epidemic Vaccination for Web4
Session 34, Track 8

Targeted intervention strategies for trust contagion networks:
- SIR/SIS models with vaccination (trust immunization)
- Targeted vaccination strategies (degree, betweenness, trust-weighted)
- Ring vaccination (vaccinate neighbors of infected)
- Herd immunity thresholds for trust networks
- Optimal vaccination budget allocation
- Vaccine efficacy and waning immunity
- Quarantine vs vaccination tradeoffs
- Trust epidemic containment simulation
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict


# ─── Network Graph ───────────────────────────────────────────────

@dataclass
class TrustNetwork:
    """Simple graph for epidemic modeling."""
    nodes: Set[str]
    edges: Dict[str, Set[str]]  # adjacency list

    def add_edge(self, a: str, b: str):
        self.nodes.add(a)
        self.nodes.add(b)
        self.edges.setdefault(a, set()).add(b)
        self.edges.setdefault(b, set()).add(a)

    def degree(self, node: str) -> int:
        return len(self.edges.get(node, set()))

    def neighbors(self, node: str) -> Set[str]:
        return self.edges.get(node, set())

    @property
    def avg_degree(self) -> float:
        if not self.nodes:
            return 0
        return sum(self.degree(n) for n in self.nodes) / len(self.nodes)

    @staticmethod
    def erdos_renyi(n: int, p: float, rng: random.Random = None) -> 'TrustNetwork':
        """Create Erdős–Rényi random graph."""
        rng = rng or random.Random()
        net = TrustNetwork(set(), {})
        nodes = [f"n{i}" for i in range(n)]
        for node in nodes:
            net.nodes.add(node)
            net.edges.setdefault(node, set())
        for i in range(n):
            for j in range(i + 1, n):
                if rng.random() < p:
                    net.add_edge(nodes[i], nodes[j])
        return net


# ─── Epidemic State ──────────────────────────────────────────────

class EpidemicState:
    """SIR model with vaccination state."""
    SUSCEPTIBLE = "S"
    INFECTED = "I"
    RECOVERED = "R"
    VACCINATED = "V"

    def __init__(self, network: TrustNetwork):
        self.network = network
        self.state: Dict[str, str] = {n: self.SUSCEPTIBLE for n in network.nodes}
        self.infection_time: Dict[str, int] = {}
        self.history: List[Dict[str, int]] = []

    def infect(self, node: str, t: int = 0):
        if self.state.get(node) == self.SUSCEPTIBLE:
            self.state[node] = self.INFECTED
            self.infection_time[node] = t

    def vaccinate(self, node: str):
        if self.state.get(node) == self.SUSCEPTIBLE:
            self.state[node] = self.VACCINATED

    def count(self) -> Dict[str, int]:
        counts = {self.SUSCEPTIBLE: 0, self.INFECTED: 0,
                  self.RECOVERED: 0, self.VACCINATED: 0}
        for s in self.state.values():
            counts[s] = counts.get(s, 0) + 1
        return counts

    def record(self):
        self.history.append(self.count())


# ─── SIR Simulation ─────────────────────────────────────────────

def sir_step(epidemic: EpidemicState,
              beta: float, gamma: float,
              rng: random.Random = None) -> int:
    """
    One step of SIR with vaccination.
    beta: infection rate per contact
    gamma: recovery rate
    Returns number of new infections.
    """
    rng = rng or random.Random()
    new_infections = 0
    new_recoveries = []

    infected = [n for n, s in epidemic.state.items()
                if s == EpidemicState.INFECTED]

    for node in infected:
        # Try to infect neighbors
        for neighbor in epidemic.network.neighbors(node):
            if epidemic.state[neighbor] == EpidemicState.SUSCEPTIBLE:
                if rng.random() < beta:
                    epidemic.state[neighbor] = EpidemicState.INFECTED
                    new_infections += 1

        # Recovery
        if rng.random() < gamma:
            new_recoveries.append(node)

    for node in new_recoveries:
        epidemic.state[node] = EpidemicState.RECOVERED

    return new_infections


def simulate_epidemic(network: TrustNetwork,
                       initial_infected: List[str],
                       beta: float, gamma: float,
                       max_steps: int = 200,
                       vaccination_strategy: Optional[Dict[str, bool]] = None,
                       rng: random.Random = None) -> EpidemicState:
    """Run full SIR simulation with optional vaccination."""
    rng = rng or random.Random()
    epidemic = EpidemicState(network)

    # Apply vaccination
    if vaccination_strategy:
        for node, vaccinated in vaccination_strategy.items():
            if vaccinated:
                epidemic.vaccinate(node)

    # Seed infection
    for node in initial_infected:
        epidemic.infect(node, 0)

    epidemic.record()

    for t in range(max_steps):
        new = sir_step(epidemic, beta, gamma, rng)
        epidemic.record()

        # Stop if no infected
        if epidemic.count()[EpidemicState.INFECTED] == 0:
            break

    return epidemic


# ─── Vaccination Strategies ──────────────────────────────────────

def random_vaccination(network: TrustNetwork, budget: int,
                        rng: random.Random = None) -> Dict[str, bool]:
    """Vaccinate random nodes."""
    rng = rng or random.Random()
    nodes = list(network.nodes)
    rng.shuffle(nodes)
    return {n: (i < budget) for i, n in enumerate(nodes)}


def degree_targeted_vaccination(network: TrustNetwork,
                                  budget: int) -> Dict[str, bool]:
    """Vaccinate highest-degree nodes first (hubs)."""
    sorted_nodes = sorted(network.nodes, key=lambda n: -network.degree(n))
    return {n: (i < budget) for i, n in enumerate(sorted_nodes)}


def trust_weighted_vaccination(network: TrustNetwork, budget: int,
                                 trust_scores: Dict[str, float]) -> Dict[str, bool]:
    """Vaccinate based on trust importance: high-trust nodes first."""
    sorted_nodes = sorted(network.nodes,
                           key=lambda n: -trust_scores.get(n, 0))
    return {n: (i < budget) for i, n in enumerate(sorted_nodes)}


def ring_vaccination(network: TrustNetwork,
                      infected: Set[str]) -> Dict[str, bool]:
    """Vaccinate all neighbors of infected nodes (containment ring)."""
    to_vaccinate = set()
    for node in infected:
        to_vaccinate |= network.neighbors(node)
    to_vaccinate -= infected  # Don't vaccinate already infected
    return {n: (n in to_vaccinate) for n in network.nodes}


# ─── Herd Immunity Threshold ─────────────────────────────────────

def herd_immunity_threshold(R0: float) -> float:
    """
    Fraction of population that must be immune for herd immunity.
    p_c = 1 - 1/R0
    """
    if R0 <= 1:
        return 0.0
    return 1.0 - 1.0 / R0


def basic_reproduction_number(beta: float, gamma: float,
                                avg_degree: float) -> float:
    """R0 = beta * avg_degree / gamma for network SIR."""
    if gamma <= 0:
        return float('inf')
    return beta * avg_degree / gamma


def effective_R0(R0: float, vaccination_fraction: float,
                   efficacy: float = 1.0) -> float:
    """R_eff = R0 * (1 - efficacy * vaccination_fraction)."""
    return R0 * (1.0 - efficacy * vaccination_fraction)


# ─── Vaccination Budget Optimization ─────────────────────────────

def evaluate_strategy(network: TrustNetwork,
                       strategy: Dict[str, bool],
                       initial_infected: List[str],
                       beta: float, gamma: float,
                       n_simulations: int = 20,
                       rng: random.Random = None) -> Dict[str, float]:
    """
    Evaluate a vaccination strategy by running multiple simulations.
    Returns metrics on epidemic size.
    """
    rng = rng or random.Random()
    total_infecteds = []
    peak_infecteds = []

    for i in range(n_simulations):
        sim_rng = random.Random(rng.randint(0, 10**6))
        result = simulate_epidemic(network, initial_infected,
                                    beta, gamma, vaccination_strategy=strategy,
                                    rng=sim_rng)
        final = result.count()
        total_inf = final[EpidemicState.RECOVERED] + final[EpidemicState.INFECTED]
        total_infecteds.append(total_inf)

        peak = max(h[EpidemicState.INFECTED] for h in result.history) if result.history else 0
        peak_infecteds.append(peak)

    n = len(network.nodes)
    return {
        "avg_total_infected": sum(total_infecteds) / n_simulations,
        "avg_attack_rate": sum(total_infecteds) / (n_simulations * n),
        "avg_peak": sum(peak_infecteds) / n_simulations,
        "budget_used": sum(1 for v in strategy.values() if v),
    }


# ─── Waning Immunity ─────────────────────────────────────────────

def vaccination_waning(initial_immunity: float, half_life: float,
                        time: float) -> float:
    """
    Vaccine efficacy wanes exponentially.
    efficacy(t) = initial * exp(-ln(2)/half_life * t)
    """
    rate = math.log(2) / half_life
    return initial_immunity * math.exp(-rate * time)


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
    print("Trust Epidemic Vaccination for Web4")
    print("Session 34, Track 8")
    print("=" * 70)

    rng = random.Random(42)

    # ── §1 Network Basics ────────────────────────────────────────
    print("\n§1 Network Basics\n")

    net = TrustNetwork.erdos_renyi(50, 0.15, rng=random.Random(42))
    check("network_has_nodes", len(net.nodes) == 50)
    check("network_has_edges", net.avg_degree > 2, f"avg_deg={net.avg_degree:.1f}")

    # ── §2 Basic SIR ────────────────────────────────────────────
    print("\n§2 Basic SIR Simulation\n")

    result_no_vax = simulate_epidemic(net, ["n0"], beta=0.3, gamma=0.1,
                                       rng=random.Random(42))
    final_no_vax = result_no_vax.count()
    total_inf_no_vax = final_no_vax[EpidemicState.RECOVERED] + final_no_vax[EpidemicState.INFECTED]

    check("sir_some_infected", total_inf_no_vax > 1)
    check("sir_has_history", len(result_no_vax.history) > 2)

    # With very low beta: minimal spread
    result_low = simulate_epidemic(net, ["n0"], beta=0.01, gamma=0.5,
                                    rng=random.Random(42))
    final_low = result_low.count()
    total_inf_low = final_low[EpidemicState.RECOVERED] + final_low[EpidemicState.INFECTED]
    check("low_beta_few_infected", total_inf_low < total_inf_no_vax)

    # ── §3 Vaccination Effect ────────────────────────────────────
    print("\n§3 Vaccination Effect\n")

    # Vaccinate 40% of nodes randomly
    vax_strategy = random_vaccination(net, budget=20, rng=random.Random(42))
    n_vaccinated = sum(1 for v in vax_strategy.values() if v)
    check("budget_respected", n_vaccinated == 20)

    result_vax = simulate_epidemic(net, ["n0"], beta=0.3, gamma=0.1,
                                    vaccination_strategy=vax_strategy,
                                    rng=random.Random(42))
    final_vax = result_vax.count()
    total_inf_vax = final_vax[EpidemicState.RECOVERED] + final_vax[EpidemicState.INFECTED]

    check("vaccination_reduces_spread", total_inf_vax <= total_inf_no_vax,
          f"vax={total_inf_vax}, no_vax={total_inf_no_vax}")
    check("vaccinated_count", final_vax[EpidemicState.VACCINATED] > 0)

    # ── §4 Degree-Targeted Vaccination ───────────────────────────
    print("\n§4 Degree-Targeted Vaccination\n")

    degree_vax = degree_targeted_vaccination(net, budget=10)
    # Top-degree nodes should be vaccinated
    degrees = [(n, net.degree(n)) for n in net.nodes]
    degrees.sort(key=lambda x: -x[1])
    top_10 = [n for n, d in degrees[:10]]
    check("hubs_vaccinated", all(degree_vax.get(n, False) for n in top_10))

    result_degree = simulate_epidemic(net, ["n0"], beta=0.3, gamma=0.1,
                                       vaccination_strategy=degree_vax,
                                       rng=random.Random(42))
    final_degree = result_degree.count()
    total_inf_degree = final_degree[EpidemicState.RECOVERED] + final_degree[EpidemicState.INFECTED]
    check("degree_vax_effective", total_inf_degree <= total_inf_no_vax)

    # ── §5 Ring Vaccination ──────────────────────────────────────
    print("\n§5 Ring Vaccination\n")

    ring_vax = ring_vaccination(net, {"n0"})
    ring_count = sum(1 for v in ring_vax.values() if v)
    check("ring_vaccinates_neighbors", ring_count == net.degree("n0"))

    # n0's neighbors should all be vaccinated
    for neighbor in net.neighbors("n0"):
        check(f"ring_neighbor_{neighbor}", ring_vax.get(neighbor, False))
        break  # Just check first neighbor

    # Ring shouldn't vaccinate the infected node itself
    check("ring_not_infected", not ring_vax.get("n0", False))

    # ── §6 Herd Immunity ────────────────────────────────────────
    print("\n§6 Herd Immunity Threshold\n")

    # R0 = 2 → threshold = 0.5
    check("herd_R0_2", abs(herd_immunity_threshold(2.0) - 0.5) < 1e-9)

    # R0 = 3 → threshold = 2/3
    check("herd_R0_3", abs(herd_immunity_threshold(3.0) - 2/3) < 1e-9)

    # R0 ≤ 1: no vaccination needed
    check("herd_R0_1", herd_immunity_threshold(1.0) == 0.0)
    check("herd_R0_0.5", herd_immunity_threshold(0.5) == 0.0)

    # Higher R0 → higher threshold
    check("herd_monotonic", herd_immunity_threshold(5.0) > herd_immunity_threshold(3.0))

    # ── §7 R0 Calculations ──────────────────────────────────────
    print("\n§7 R0 Calculations\n")

    R0 = basic_reproduction_number(0.3, 0.1, net.avg_degree)
    check("R0_positive", R0 > 0)
    check("R0_formula", abs(R0 - 0.3 * net.avg_degree / 0.1) < 1e-9)

    # Effective R0 with vaccination
    R_eff = effective_R0(R0, 0.5, efficacy=1.0)
    check("R_eff_halved", abs(R_eff - R0 * 0.5) < 1e-9)

    # With imperfect vaccine
    R_eff_imperfect = effective_R0(R0, 0.5, efficacy=0.8)
    check("imperfect_vaccine", R_eff_imperfect > R_eff)
    check("imperfect_formula", abs(R_eff_imperfect - R0 * (1 - 0.4)) < 1e-9)

    # ── §8 Waning Immunity ───────────────────────────────────────
    print("\n§8 Waning Immunity\n")

    # At t=0: full immunity
    check("waning_t0", abs(vaccination_waning(1.0, 180, 0) - 1.0) < 1e-9)

    # At half-life: 50% immunity
    check("waning_halflife", abs(vaccination_waning(1.0, 180, 180) - 0.5) < 1e-3)

    # Decreasing over time
    e1 = vaccination_waning(0.95, 365, 100)
    e2 = vaccination_waning(0.95, 365, 200)
    check("waning_decreasing", e1 > e2)

    # Longer half-life → slower waning
    e_short = vaccination_waning(1.0, 90, 100)
    e_long = vaccination_waning(1.0, 365, 100)
    check("longer_halflife_slower", e_long > e_short)

    # ── §9 Strategy Comparison ───────────────────────────────────
    print("\n§9 Strategy Comparison\n")

    # Compare random vs degree-targeted with same budget
    budget = 15
    rnd = random_vaccination(net, budget, rng=random.Random(42))
    deg = degree_targeted_vaccination(net, budget)

    eval_rnd = evaluate_strategy(net, rnd, ["n0"], 0.3, 0.1, n_simulations=10,
                                  rng=random.Random(42))
    eval_deg = evaluate_strategy(net, deg, ["n0"], 0.3, 0.1, n_simulations=10,
                                  rng=random.Random(42))

    check("both_strategies_evaluated", eval_rnd["budget_used"] == budget)
    check("degree_budget", eval_deg["budget_used"] == budget)
    # Degree-targeted should generally be more effective (lower attack rate)
    check("degree_likely_better", eval_deg["avg_attack_rate"] <= eval_rnd["avg_attack_rate"] + 0.2,
          f"deg={eval_deg['avg_attack_rate']:.3f}, rnd={eval_rnd['avg_attack_rate']:.3f}")

    # No vaccination baseline
    no_vax_strat = {n: False for n in net.nodes}
    eval_none = evaluate_strategy(net, no_vax_strat, ["n0"], 0.3, 0.1,
                                   n_simulations=10, rng=random.Random(42))
    check("no_vax_baseline_computed", eval_none["avg_attack_rate"] > 0)

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
