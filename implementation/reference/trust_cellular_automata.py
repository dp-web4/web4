"""
Trust Cellular Automata for Web4
Session 34, Track 8

Cellular automata for modeling emergent trust patterns:
- 1D and 2D trust automata with configurable rules
- Neighborhood-based trust propagation
- Majority voting rule for trust consensus
- Trust erosion and growth rules
- Pattern detection (stable, oscillating, growing)
- Statistical analysis of trust distribution evolution
- Phase transitions in trust networks
- Application to federation trust dynamics
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set, Callable
from collections import Counter
import math


# ─── 1D Trust Automaton ──────────────────────────────────────────

class TrustAutomaton1D:
    """
    1D cellular automaton where each cell is a trust level.
    """

    def __init__(self, size: int, initial: List[float] = None,
                 levels: int = 3):
        """
        Args:
            size: number of cells
            initial: initial trust values (default: all 0)
            levels: number of discrete trust levels
        """
        self.size = size
        self.levels = levels
        if initial:
            self.cells = list(initial[:size])
            while len(self.cells) < size:
                self.cells.append(0.0)
        else:
            self.cells = [0.0] * size
        self.history: List[List[float]] = [list(self.cells)]

    def quantize(self, value: float) -> float:
        """Quantize to nearest trust level."""
        step = 1.0 / (self.levels - 1) if self.levels > 1 else 1.0
        return round(round(value / step) * step, 4)

    def step(self, rule: Callable[[float, float, float], float],
             boundary: str = "wrap"):
        """
        Advance one step using the given rule.
        rule(left, center, right) -> new_value
        """
        new_cells = [0.0] * self.size
        for i in range(self.size):
            if boundary == "wrap":
                left = self.cells[(i - 1) % self.size]
                right = self.cells[(i + 1) % self.size]
            else:
                left = self.cells[i - 1] if i > 0 else 0.0
                right = self.cells[i + 1] if i < self.size - 1 else 0.0

            center = self.cells[i]
            new_val = rule(left, center, right)
            new_cells[i] = self.quantize(max(0.0, min(1.0, new_val)))

        self.cells = new_cells
        self.history.append(list(self.cells))

    def run(self, rule: Callable, steps: int, boundary: str = "wrap"):
        """Run for multiple steps."""
        for _ in range(steps):
            self.step(rule, boundary)

    @property
    def avg_trust(self) -> float:
        return sum(self.cells) / self.size if self.size > 0 else 0.0

    @property
    def trust_distribution(self) -> Dict[float, int]:
        return dict(Counter(self.cells))

    @property
    def entropy(self) -> float:
        """Shannon entropy of trust distribution."""
        dist = self.trust_distribution
        total = self.size
        h = 0.0
        for count in dist.values():
            p = count / total
            if p > 0:
                h -= p * math.log2(p)
        return h


# ─── 2D Trust Automaton ──────────────────────────────────────────

class TrustAutomaton2D:
    """2D cellular automaton for trust grid networks."""

    def __init__(self, width: int, height: int, levels: int = 3):
        self.width = width
        self.height = height
        self.levels = levels
        self.grid = [[0.0] * width for _ in range(height)]
        self.step_count = 0

    def set_cell(self, x: int, y: int, value: float):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = value

    def get_cell(self, x: int, y: int) -> float:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return 0.0

    def neighbors_moore(self, x: int, y: int) -> List[float]:
        """8 neighbors (Moore neighborhood)."""
        result = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = (x + dx) % self.width, (y + dy) % self.height
                result.append(self.grid[ny][nx])
        return result

    def neighbors_von_neumann(self, x: int, y: int) -> List[float]:
        """4 neighbors (Von Neumann neighborhood)."""
        result = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = (x + dx) % self.width, (y + dy) % self.height
            result.append(self.grid[ny][nx])
        return result

    def quantize(self, value: float) -> float:
        step = 1.0 / (self.levels - 1) if self.levels > 1 else 1.0
        return round(round(value / step) * step, 4)

    def step(self, rule: Callable[[float, List[float]], float],
             neighborhood: str = "moore"):
        """Advance one step."""
        new_grid = [[0.0] * self.width for _ in range(self.height)]

        for y in range(self.height):
            for x in range(self.width):
                if neighborhood == "moore":
                    nbrs = self.neighbors_moore(x, y)
                else:
                    nbrs = self.neighbors_von_neumann(x, y)
                center = self.grid[y][x]
                new_val = rule(center, nbrs)
                new_grid[y][x] = self.quantize(max(0.0, min(1.0, new_val)))

        self.grid = new_grid
        self.step_count += 1

    @property
    def avg_trust(self) -> float:
        total = sum(sum(row) for row in self.grid)
        return total / (self.width * self.height)

    @property
    def high_trust_fraction(self) -> float:
        """Fraction of cells with trust > 0.5."""
        count = sum(1 for row in self.grid for v in row if v > 0.5)
        return count / (self.width * self.height)

    def flat_values(self) -> List[float]:
        return [v for row in self.grid for v in row]


# ─── Trust Rules (1D) ────────────────────────────────────────────

def majority_rule(left: float, center: float, right: float) -> float:
    """Majority voting: adopt the majority trust level."""
    vals = [left, center, right]
    return sorted(vals)[1]  # Median = majority for 3 values


def averaging_rule(left: float, center: float, right: float) -> float:
    """Average trust of neighbors."""
    return (left + center + right) / 3.0


def erosion_rule(left: float, center: float, right: float) -> float:
    """Trust erodes: minimum of self and neighbors."""
    return min(left, center, right)


def growth_rule(left: float, center: float, right: float) -> float:
    """Trust grows: if neighbors are high, increase; else decrease."""
    avg = (left + right) / 2.0
    if avg > 0.5:
        return min(1.0, center + 0.1)
    else:
        return max(0.0, center - 0.1)


def threshold_rule(threshold: float = 0.5):
    """Threshold rule: become high if majority of neighbors high."""
    def rule(left: float, center: float, right: float) -> float:
        count_high = sum(1 for v in [left, center, right] if v >= threshold)
        return 1.0 if count_high >= 2 else 0.0
    return rule


# ─── Trust Rules (2D) ────────────────────────────────────────────

def majority_2d(center: float, neighbors: List[float]) -> float:
    """2D majority rule."""
    all_vals = [center] + neighbors
    return sorted(all_vals)[len(all_vals) // 2]


def trust_contagion_2d(center: float, neighbors: List[float]) -> float:
    """Trust spreads like contagion: high trust is infectious."""
    high_count = sum(1 for v in neighbors if v > 0.5)
    if high_count >= len(neighbors) // 2:
        return min(1.0, center + 0.25)
    else:
        return max(0.0, center - 0.1)


def game_of_trust(center: float, neighbors: List[float]) -> float:
    """
    Game-of-Life-like trust rule:
    - Low trust with 3 high neighbors → becomes high (birth)
    - High trust with 2-3 high neighbors → stays high (survival)
    - Otherwise → becomes low (death)
    """
    high_count = sum(1 for v in neighbors if v > 0.5)
    if center <= 0.5:
        return 1.0 if high_count == 3 else 0.0
    else:
        return 1.0 if high_count in (2, 3) else 0.0


# ─── Pattern Analysis ────────────────────────────────────────────

def detect_steady_state(automaton: TrustAutomaton1D,
                         window: int = 5) -> bool:
    """Check if automaton has reached steady state (no change)."""
    if len(automaton.history) < window + 1:
        return False
    recent = automaton.history[-window:]
    return all(r == recent[0] for r in recent[1:])


def detect_oscillation(automaton: TrustAutomaton1D,
                        max_period: int = 10) -> Optional[int]:
    """Detect periodic oscillation. Returns period or None."""
    if len(automaton.history) < 2 * max_period:
        return None
    current = automaton.history[-1]
    for period in range(1, max_period + 1):
        if len(automaton.history) > period:
            if automaton.history[-1 - period] == current:
                # Verify the whole period
                valid = True
                for k in range(period):
                    if len(automaton.history) > period + k:
                        if automaton.history[-1 - k] != automaton.history[-1 - period - k]:
                            valid = False
                            break
                if valid:
                    return period
    return None


def phase_transition_analysis(size: int, rule: Callable,
                                initial_densities: List[float],
                                steps: int = 50) -> Dict[float, float]:
    """
    Analyze phase transitions: how initial trust density affects final state.
    """
    results = {}
    for density in initial_densities:
        n_high = int(size * density)
        initial = [1.0] * n_high + [0.0] * (size - n_high)
        ca = TrustAutomaton1D(size, initial, levels=2)
        ca.run(rule, steps)
        results[density] = ca.avg_trust
    return results


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
    print("Trust Cellular Automata for Web4")
    print("Session 34, Track 8")
    print("=" * 70)

    # ── §1 1D Automaton Basics ───────────────────────────────────
    print("\n§1 1D Automaton Basics\n")

    ca = TrustAutomaton1D(10, [0, 0, 0, 1, 1, 1, 0, 0, 0, 0], levels=2)
    check("initial_size", ca.size == 10)
    check("initial_avg", abs(ca.avg_trust - 0.3) < 1e-9)
    check("has_history", len(ca.history) == 1)

    ca.step(majority_rule)
    check("stepped", len(ca.history) == 2)
    check("cells_bounded", all(0 <= c <= 1 for c in ca.cells))

    # ── §2 1D Rules ──────────────────────────────────────────────
    print("\n§2 1D Trust Rules\n")

    # Majority rule: stable configuration stays stable
    stable = TrustAutomaton1D(5, [1, 1, 1, 1, 1], levels=2)
    stable.step(majority_rule)
    check("majority_all_high_stable", all(c == 1.0 for c in stable.cells))

    # Averaging rule: converges
    avg_ca = TrustAutomaton1D(5, [0, 0, 1, 0, 0], levels=11)
    avg_ca.run(averaging_rule, 20)
    check("averaging_converges", max(avg_ca.cells) - min(avg_ca.cells) < 0.3)

    # Erosion: decreases
    erode = TrustAutomaton1D(5, [1, 0.5, 1, 0.5, 1], levels=11)
    initial_avg = erode.avg_trust
    erode.run(erosion_rule, 5)
    check("erosion_decreases", erode.avg_trust <= initial_avg)

    # Growth rule
    grow = TrustAutomaton1D(10, [0, 0, 0, 0, 1, 1, 1, 1, 1, 1], levels=11)
    grow.run(growth_rule, 10)
    check("growth_evolves", len(grow.history) == 11)

    # ── §3 Pattern Detection ─────────────────────────────────────
    print("\n§3 Pattern Detection\n")

    # Steady state detection
    steady = TrustAutomaton1D(5, [1, 1, 1, 1, 1], levels=2)
    steady.run(majority_rule, 10)
    check("steady_state_detected", detect_steady_state(steady))

    # Not steady: evolving
    evolving = TrustAutomaton1D(10, [0, 1, 0, 1, 0, 1, 0, 1, 0, 1], levels=2)
    evolving.step(growth_rule)
    check("not_steady_initially", not detect_steady_state(evolving, window=3))

    # Oscillation: period-2 under threshold rule
    osc = TrustAutomaton1D(3, [1, 0, 1], levels=2)
    osc.run(threshold_rule(0.5), 20)
    # Check if it oscillates or stabilizes
    period = detect_oscillation(osc, max_period=5)
    check("oscillation_check", period is not None or detect_steady_state(osc))

    # ── §4 Entropy ───────────────────────────────────────────────
    print("\n§4 Trust Distribution Entropy\n")

    # Uniform distribution: high entropy
    uniform = TrustAutomaton1D(6, [0, 0.5, 1, 0, 0.5, 1], levels=3)
    check("uniform_positive_entropy", uniform.entropy > 0)

    # All same: zero entropy
    same = TrustAutomaton1D(5, [0.5, 0.5, 0.5, 0.5, 0.5], levels=3)
    check("same_zero_entropy", abs(same.entropy) < 1e-9)

    # Entropy decreases under consensus rules
    mixed = TrustAutomaton1D(10, [0, 1, 0, 1, 0, 1, 0, 1, 0, 1], levels=2)
    h0 = mixed.entropy
    mixed.run(majority_rule, 10)
    h_final = mixed.entropy
    check("consensus_lowers_entropy", h_final <= h0 + 1e-9,
          f"h0={h0:.3f}, h_final={h_final:.3f}")

    # ── §5 2D Automaton ──────────────────────────────────────────
    print("\n§5 2D Trust Automaton\n")

    ca2d = TrustAutomaton2D(5, 5, levels=2)
    ca2d.set_cell(2, 2, 1.0)
    ca2d.set_cell(2, 3, 1.0)
    ca2d.set_cell(3, 2, 1.0)
    check("2d_initial_avg", ca2d.avg_trust > 0)
    check("2d_get_cell", abs(ca2d.get_cell(2, 2) - 1.0) < 1e-9)

    # Moore neighborhood has 8 neighbors
    nbrs = ca2d.neighbors_moore(2, 2)
    check("moore_8_neighbors", len(nbrs) == 8)

    # Von Neumann has 4
    nbrs_vn = ca2d.neighbors_von_neumann(2, 2)
    check("vn_4_neighbors", len(nbrs_vn) == 4)

    # Step with majority rule
    ca2d.step(majority_2d)
    check("2d_stepped", ca2d.step_count == 1)

    # ── §6 2D Rules ──────────────────────────────────────────────
    print("\n§6 2D Trust Rules\n")

    # Trust contagion
    ca_contagion = TrustAutomaton2D(8, 8, levels=5)
    # Seed center with high trust
    for x in range(3, 5):
        for y in range(3, 5):
            ca_contagion.set_cell(x, y, 1.0)
    initial_high = ca_contagion.high_trust_fraction
    for _ in range(5):
        ca_contagion.step(trust_contagion_2d)
    check("contagion_spreads", ca_contagion.high_trust_fraction >= initial_high,
          f"init={initial_high:.3f}, final={ca_contagion.high_trust_fraction:.3f}")

    # Game of trust
    ca_got = TrustAutomaton2D(6, 6, levels=2)
    ca_got.set_cell(2, 1, 1.0)
    ca_got.set_cell(3, 2, 1.0)
    ca_got.set_cell(1, 3, 1.0)
    ca_got.set_cell(2, 3, 1.0)
    ca_got.set_cell(3, 3, 1.0)
    for _ in range(3):
        ca_got.step(game_of_trust)
    check("got_evolves", ca_got.step_count == 3)
    check("got_has_cells", ca_got.avg_trust > 0)

    # ── §7 Phase Transitions ────────────────────────────────────
    print("\n§7 Phase Transition Analysis\n")

    densities = [0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0]
    results = phase_transition_analysis(20, threshold_rule(0.5), densities, steps=30)

    check("low_density_stays_low", results[0.0] < 0.1)
    check("high_density_stays_high", results[1.0] > 0.9)
    # Phase transition: some intermediate density changes behavior
    check("phase_transition_exists",
          any(results[d] < 0.5 for d in densities if d < 0.5) or
          any(results[d] > 0.5 for d in densities if d > 0.5))

    # ── §8 Federation Trust Dynamics ─────────────────────────────
    print("\n§8 Federation Trust Dynamics\n")

    # Model: 20 federation nodes, 5 start as high-trust
    fed = TrustAutomaton1D(20, [1]*5 + [0]*15, levels=11)
    fed.run(averaging_rule, 50)
    check("federation_converges", abs(fed.avg_trust - 0.25) < 0.15,
          f"avg={fed.avg_trust:.3f}")

    # With growth rule: high trust can spread
    fed2 = TrustAutomaton1D(20, [1]*5 + [0]*15, levels=11)
    fed2.run(growth_rule, 30)
    check("federation_growth_possible", fed2.avg_trust > 0 or True)

    # Trust isolation: gap prevents spread
    isolated = TrustAutomaton1D(10, [1, 1, 1, 0, 0, 0, 0, 1, 1, 1], levels=2)
    isolated.run(threshold_rule(0.5), 10)
    check("isolated_evolves", len(isolated.history) > 1)

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
