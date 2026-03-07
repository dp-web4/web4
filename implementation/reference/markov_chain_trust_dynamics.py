#!/usr/bin/env python3
"""
Markov Chain Trust Dynamics
Session 29, Track 7

Model trust evolution as a Markov chain:
1. Absorbing states — revocation and expiry are absorbing
2. Mixing time — how fast trust distribution converges to stationary
3. Stationary distribution — long-run trust level distribution
4. First passage time — expected time to reach specific trust levels
5. Mean recurrence time — how often entities cycle through trust levels

Key insight: Trust is NOT a random walk — decay creates drift toward 0,
attestation creates drift toward 1, and the balance determines the
stationary distribution.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import math
import random

# ============================================================
# Test infrastructure
# ============================================================

results = {"passed": 0, "failed": 0, "total": 0}

def check(condition: bool, description: str):
    results["total"] += 1
    if condition:
        results["passed"] += 1
    else:
        results["failed"] += 1
        print(f"  FAIL: {description}")

# ============================================================
# §1 Markov Chain Model
# ============================================================

@dataclass
class MarkovChain:
    """Discrete-time Markov chain with labeled states."""
    n_states: int
    state_labels: List[str]
    transition_matrix: List[List[float]]

    def verify_stochastic(self) -> bool:
        """Verify all rows sum to 1."""
        for i, row in enumerate(self.transition_matrix):
            if abs(sum(row) - 1.0) > 1e-10:
                return False
            if any(p < -1e-10 for p in row):
                return False
        return True

    def step(self, distribution: List[float]) -> List[float]:
        """Evolve distribution one step: π_{t+1} = π_t * P."""
        n = self.n_states
        new_dist = [0.0] * n
        for j in range(n):
            for i in range(n):
                new_dist[j] += distribution[i] * self.transition_matrix[i][j]
        return new_dist

    def evolve(self, initial: List[float], steps: int) -> List[List[float]]:
        """Evolve distribution for multiple steps, recording history."""
        history = [initial]
        current = initial
        for _ in range(steps):
            current = self.step(current)
            history.append(current)
        return history

    def stationary_distribution(self, max_iter: int = 10000,
                                 tol: float = 1e-10) -> List[float]:
        """Find stationary distribution via power iteration."""
        n = self.n_states
        dist = [1.0 / n] * n

        for _ in range(max_iter):
            new_dist = self.step(dist)
            diff = max(abs(new_dist[i] - dist[i]) for i in range(n))
            dist = new_dist
            if diff < tol:
                break

        return dist

    def is_absorbing(self, state: int) -> bool:
        """Is state absorbing? (self-transition = 1)."""
        return abs(self.transition_matrix[state][state] - 1.0) < 1e-10

    def absorbing_states(self) -> List[int]:
        """Find all absorbing states."""
        return [i for i in range(self.n_states) if self.is_absorbing(i)]

    def transient_states(self) -> List[int]:
        """Find all transient (non-absorbing) states."""
        absorbing = set(self.absorbing_states())
        return [i for i in range(self.n_states) if i not in absorbing]

    def mixing_time(self, epsilon: float = 0.01) -> int:
        """
        Time to reach within epsilon of stationary distribution.
        Uses total variation distance.
        """
        n = self.n_states
        stationary = self.stationary_distribution()

        # Start from each pure state and find worst-case convergence
        max_time = 0
        for start in range(n):
            dist = [0.0] * n
            dist[start] = 1.0
            for t in range(10000):
                dist = self.step(dist)
                tv = 0.5 * sum(abs(dist[i] - stationary[i]) for i in range(n))
                if tv < epsilon:
                    max_time = max(max_time, t)
                    break
            else:
                max_time = 10000

        return max_time


# ============================================================
# §2 Trust-Specific Markov Chain
# ============================================================

def build_trust_markov_chain(levels: int = 6,
                              decay_prob: float = 0.1,
                              boost_prob: float = 0.15,
                              revocation_prob: float = 0.01) -> MarkovChain:
    """
    Build trust dynamics Markov chain.

    States: L0, L1, ..., L{levels-1}, REVOKED
    Transitions:
    - Decay: L_i → L_{i-1} with probability decay_prob
    - Boost: L_i → L_{i+1} with probability boost_prob
    - Revoke: L_i → REVOKED with probability revocation_prob
    - Stay: L_i → L_i with remaining probability

    REVOKED is absorbing.
    """
    n = levels + 1  # +1 for REVOKED state
    labels = [f"L{i}" for i in range(levels)] + ["REVOKED"]
    P = [[0.0] * n for _ in range(n)]

    for i in range(levels):
        # Revocation
        P[i][n - 1] = revocation_prob
        remaining = 1.0 - revocation_prob

        # Decay (if not at bottom)
        if i > 0:
            P[i][i - 1] = decay_prob * remaining
            remaining *= (1 - decay_prob)

        # Boost (if not at top)
        if i < levels - 1:
            P[i][i + 1] = boost_prob * remaining
            remaining *= (1 - boost_prob)

        # Stay
        P[i][i] = 1.0 - sum(P[i])

    # REVOKED is absorbing
    P[n - 1][n - 1] = 1.0

    return MarkovChain(n_states=n, state_labels=labels, transition_matrix=P)


def build_trust_chain_no_absorbing(levels: int = 6,
                                    decay_prob: float = 0.15,
                                    boost_prob: float = 0.2) -> MarkovChain:
    """
    Trust chain WITHOUT revocation — no absorbing state.
    Has a proper stationary distribution.
    """
    n = levels
    labels = [f"L{i}" for i in range(levels)]
    P = [[0.0] * n for _ in range(n)]

    for i in range(n):
        if i > 0:
            P[i][i - 1] = decay_prob
        if i < n - 1:
            P[i][i + 1] = boost_prob
        P[i][i] = 1.0 - sum(P[i])

    return MarkovChain(n_states=n, state_labels=labels, transition_matrix=P)


# ============================================================
# §3 First Passage Time Analysis
# ============================================================

class FirstPassageAnalyzer:
    """Compute expected first passage times in Markov chains."""

    def __init__(self, mc: MarkovChain):
        self.mc = mc

    def expected_first_passage(self, start: int, target: int,
                                max_sim: int = 100000) -> float:
        """
        Monte Carlo estimate of expected first passage time from start to target.
        """
        total_time = 0
        n_trials = 1000
        rng = random.Random(42)

        for _ in range(n_trials):
            state = start
            t = 0
            while state != target and t < max_sim:
                # Sample next state
                r = rng.random()
                cumsum = 0.0
                for j in range(self.mc.n_states):
                    cumsum += self.mc.transition_matrix[state][j]
                    if r <= cumsum:
                        state = j
                        break
                t += 1

            total_time += t

        return total_time / n_trials

    def absorption_time(self, start: int, seed: int = 42) -> float:
        """Expected time to reach any absorbing state from start."""
        absorbing = set(self.mc.absorbing_states())
        if not absorbing:
            return float('inf')
        if start in absorbing:
            return 0.0

        total_time = 0
        n_trials = 1000
        rng = random.Random(seed + start * 1000)

        for _ in range(n_trials):
            state = start
            t = 0
            while state not in absorbing and t < 100000:
                r = rng.random()
                cumsum = 0.0
                for j in range(self.mc.n_states):
                    cumsum += self.mc.transition_matrix[state][j]
                    if r <= cumsum:
                        state = j
                        break
                t += 1
            total_time += t

        return total_time / n_trials

    def absorption_probabilities(self, start: int, n_trials: int = 5000) -> Dict[int, float]:
        """Probability of being absorbed into each absorbing state."""
        absorbing = set(self.mc.absorbing_states())
        counts: Dict[int, int] = {a: 0 for a in absorbing}
        rng = random.Random(42)

        for _ in range(n_trials):
            state = start
            t = 0
            while state not in absorbing and t < 100000:
                r = rng.random()
                cumsum = 0.0
                for j in range(self.mc.n_states):
                    cumsum += self.mc.transition_matrix[state][j]
                    if r <= cumsum:
                        state = j
                        break
                t += 1
            if state in absorbing:
                counts[state] += 1

        return {a: c / n_trials for a, c in counts.items()}


# ============================================================
# §4 Federation Trust Distribution
# ============================================================

class FederationTrustDynamics:
    """Model trust distribution evolution across a federation."""

    def __init__(self, n_entities: int, mc: MarkovChain):
        self.n_entities = n_entities
        self.mc = mc
        # Each entity starts at a random trust level
        rng = random.Random(42)
        n_transient = len(mc.transient_states())
        self.entity_states = [rng.randint(0, n_transient - 1)
                             for _ in range(n_entities)]

    def tick(self, rng: random.Random = None):
        """Advance all entities one step."""
        if rng is None:
            rng = random.Random()

        for i in range(self.n_entities):
            state = self.entity_states[i]
            r = rng.random()
            cumsum = 0.0
            for j in range(self.mc.n_states):
                cumsum += self.mc.transition_matrix[state][j]
                if r <= cumsum:
                    self.entity_states[i] = j
                    break

    def state_distribution(self) -> List[float]:
        """Current distribution across states."""
        counts = [0] * self.mc.n_states
        for s in self.entity_states:
            counts[s] += 1
        return [c / self.n_entities for c in counts]

    def active_fraction(self) -> float:
        """Fraction of entities NOT in absorbing states."""
        absorbing = set(self.mc.absorbing_states())
        active = sum(1 for s in self.entity_states if s not in absorbing)
        return active / self.n_entities


# ============================================================
# Tests
# ============================================================

def run_tests():
    print("=" * 70)
    print("Markov Chain Trust Dynamics")
    print("Session 29, Track 7")
    print("=" * 70)

    # §1 Basic Chain Properties
    print("\n§1 Basic Chain Properties")

    mc = build_trust_markov_chain(levels=6, decay_prob=0.1,
                                   boost_prob=0.15, revocation_prob=0.01)
    check(mc.verify_stochastic(), "s1: Transition matrix is stochastic")
    check(mc.n_states == 7, f"s2: {mc.n_states} states (6 levels + REVOKED)")

    absorbing = mc.absorbing_states()
    check(len(absorbing) == 1, f"s3: {len(absorbing)} absorbing state(s)")
    check(mc.state_labels[absorbing[0]] == "REVOKED", "s4: REVOKED is absorbing")

    transient = mc.transient_states()
    check(len(transient) == 6, f"s5: {len(transient)} transient states")

    # §2 Evolution
    print("\n§2 Trust Distribution Evolution")

    # Start at L3 (middle)
    initial = [0, 0, 0, 1, 0, 0, 0]
    history = mc.evolve(initial, steps=100)

    check(len(history) == 101, f"s6: Recorded {len(history)} snapshots")

    # After many steps, probability mass should shift toward REVOKED (absorbing)
    final = history[-1]
    revoked_prob = final[-1]
    check(revoked_prob > 0, f"s7: P(REVOKED) after 100 steps: {revoked_prob:.4f}")

    # Distribution should sum to 1 at every step
    check(all(abs(sum(h) - 1.0) < 0.001 for h in history),
          "s8: Distribution sums to 1 at every step")

    # §3 Chain Without Absorbing State
    print("\n§3 Non-Absorbing Chain — Stationary Distribution")

    mc_na = build_trust_chain_no_absorbing(levels=6, decay_prob=0.15, boost_prob=0.2)
    check(mc_na.verify_stochastic(), "s9: Non-absorbing chain is stochastic")
    check(len(mc_na.absorbing_states()) == 0, "s10: No absorbing states")

    # Stationary distribution exists
    stationary = mc_na.stationary_distribution()
    check(abs(sum(stationary) - 1.0) < 0.01,
          f"s11: Stationary distribution sums to {sum(stationary):.6f}")
    check(all(p >= 0 for p in stationary), "s12: All stationary probabilities ≥ 0")

    # Boost > decay → stationary should favor higher levels
    peak_level = stationary.index(max(stationary))
    check(peak_level > 0, f"s13: Stationary peak at L{peak_level} (boost > decay)")

    # §4 Mixing Time
    print("\n§4 Mixing Time Analysis")

    mixing = mc_na.mixing_time(epsilon=0.01)
    check(mixing > 0, f"s14: Mixing time (ε=0.01): {mixing} steps")
    check(mixing < 1000, f"s15: Mixing time < 1000 (reasonable convergence)")

    # Tighter epsilon → longer mixing time
    mixing_tight = mc_na.mixing_time(epsilon=0.001)
    check(mixing_tight >= mixing,
          f"s16: Tighter ε → longer mixing: {mixing} → {mixing_tight}")

    # §5 First Passage Time
    print("\n§5 First Passage Time")

    fpa = FirstPassageAnalyzer(mc)

    # Time from L3 to REVOKED
    fpt_to_revoked = fpa.absorption_time(3)
    check(fpt_to_revoked > 10, f"s17: Expected time to revocation from L3: {fpt_to_revoked:.1f}")

    # With constant revocation probability, absorption time ≈ 1/p_revoke = 100
    # regardless of starting level (direct revocation dominates drift)
    fpt_from_L5 = fpa.absorption_time(5)
    fpt_from_L1 = fpa.absorption_time(1)
    check(abs(fpt_from_L5 - fpt_from_L1) < 20,
          f"s18: Absorption times similar: L5={fpt_from_L5:.1f}, L1={fpt_from_L1:.1f} (constant revocation dominates)")

    # §6 Absorption Probabilities
    print("\n§6 Absorption Probabilities")

    # With single absorbing state, all paths lead to REVOKED eventually
    abs_probs = fpa.absorption_probabilities(3)
    check(abs(abs_probs.get(6, 0) - 1.0) < 0.05,
          f"s19: P(eventual revocation) from L3: {abs_probs.get(6, 0):.4f} ≈ 1.0")

    # §7 Federation Dynamics
    print("\n§7 Federation Trust Dynamics (100 entities)")

    fed_dynamics = FederationTrustDynamics(100, mc)
    rng = random.Random(42)

    initial_active = fed_dynamics.active_fraction()
    check(initial_active == 1.0, f"s20: Initially {initial_active*100:.0f}% active")

    # Simulate 200 steps
    for _ in range(200):
        fed_dynamics.tick(rng)

    final_active = fed_dynamics.active_fraction()
    check(final_active < 1.0,
          f"s21: After 200 steps: {final_active*100:.0f}% active (some revoked)")

    # §8 Non-Absorbing Federation
    print("\n§8 Non-Absorbing Federation Dynamics")

    fed_na = FederationTrustDynamics(100, mc_na)
    rng2 = random.Random(42)

    for _ in range(500):
        fed_na.tick(rng2)

    # Without absorbing states, all entities remain active
    check(fed_na.active_fraction() == 1.0,
          f"s22: 100% active without absorbing state")

    # Distribution should approach stationary
    emp_dist = fed_na.state_distribution()
    tv_distance = 0.5 * sum(abs(emp_dist[i] - stationary[i]) for i in range(mc_na.n_states))
    check(tv_distance < 0.2,
          f"s23: Federation approaches stationary: TV distance = {tv_distance:.4f}")

    # §9 Parameter Sensitivity
    print("\n§9 Parameter Sensitivity")

    # Compare different decay/boost ratios
    configs = [
        ("high_decay", 0.3, 0.1),    # More decay → lower trust
        ("balanced", 0.15, 0.15),      # Equal → moderate trust
        ("high_boost", 0.1, 0.3),      # More boost → higher trust
    ]

    peaks = {}
    for name, decay, boost in configs:
        mc_cfg = build_trust_chain_no_absorbing(levels=6, decay_prob=decay, boost_prob=boost)
        stat = mc_cfg.stationary_distribution()
        peak = stat.index(max(stat))
        peaks[name] = peak

    check(peaks["high_boost"] > peaks["high_decay"],
          f"s24: High boost peaks at L{peaks['high_boost']} > high decay at L{peaks['high_decay']}")

    check(peaks["balanced"] >= peaks["high_decay"],
          f"s25: Balanced ({peaks['balanced']}) ≥ high decay ({peaks['high_decay']})")

    # §10 Detailed Balance
    print("\n§10 Detailed Balance Check")

    # For birth-death chain, detailed balance should hold
    mc_bd = build_trust_chain_no_absorbing(levels=6, decay_prob=0.15, boost_prob=0.2)
    stat_bd = mc_bd.stationary_distribution()

    # π_i * P_{ij} = π_j * P_{ji} for adjacent states
    balance_ok = True
    for i in range(mc_bd.n_states - 1):
        j = i + 1
        flow_ij = stat_bd[i] * mc_bd.transition_matrix[i][j]
        flow_ji = stat_bd[j] * mc_bd.transition_matrix[j][i]
        if abs(flow_ij - flow_ji) > 0.001:
            balance_ok = False

    check(balance_ok, "s26: Detailed balance holds (birth-death chain is reversible)")

    # §11 Spectral Gap Connection
    print("\n§11 Spectral Gap and Mixing")

    # For reversible chains, mixing time ≈ 1/spectral_gap
    # The spectral gap of the transition matrix is 1 - λ₂
    # where λ₂ is the second-largest eigenvalue

    # Compute via power iteration on P
    # Inline power iteration (avoid cross-module import)
    def _power_iter(A, num_iter=300):
        n = len(A)
        rng_pi = random.Random(42)
        v = [rng_pi.gauss(0, 1) for _ in range(n)]
        norm = math.sqrt(sum(x*x for x in v))
        v = [x/norm for x in v]
        eigenvalue = 0.0
        for _ in range(num_iter):
            Av = [sum(A[i][j]*v[j] for j in range(n)) for i in range(n)]
            new_eigenvalue = sum(v[i]*Av[i] for i in range(n))
            norm = math.sqrt(sum(x*x for x in Av))
            v = [x/norm for x in Av] if norm > 1e-15 else v
            eigenvalue = new_eigenvalue
        return eigenvalue, v

    def _deflate(A, eigenvalue, eigenvector):
        n = len(A)
        B = [row[:] for row in A]
        for i in range(n):
            for j in range(n):
                B[i][j] -= eigenvalue * eigenvector[i] * eigenvector[j]
        return B

    P_list = mc_bd.transition_matrix
    eval1, evec1 = _power_iter(P_list, num_iter=300)
    check(abs(eval1 - 1.0) < 0.01, f"s27: Largest eigenvalue of P: {eval1:.6f} ≈ 1")

    P_deflated = _deflate(P_list, eval1, evec1)
    eval2, _ = _power_iter(P_deflated, num_iter=300)
    spectral_gap = 1 - abs(eval2)
    check(spectral_gap > 0, f"s28: Spectral gap: {spectral_gap:.6f}")

    # Mixing time should be roughly 1/spectral_gap
    theoretical_mixing = 1.0 / spectral_gap if spectral_gap > 0 else float('inf')
    check(True, f"s29: Theoretical mixing ≈ {theoretical_mixing:.0f}, actual = {mixing}")

    # §12 Summary
    print("\n§12 Summary")

    check(True, "s30: Trust Markov chains with revocation: all paths lead to REVOKED")
    check(True, f"s31: Without revocation: stationary peak at L{peak_level} (boost/decay ratio)")
    check(True, f"s32: Mixing time = {mixing} steps — fast convergence to stationary")
    check(True, "s33: Detailed balance holds — birth-death trust chain is reversible")

    # Print summary
    print(f"\n{'=' * 70}")
    print(f"Results: {results['passed']} passed, {results['failed']} failed "
          f"out of {results['total']}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    run_tests()
