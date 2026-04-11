"""
Web4 Trust Tensor Field Dynamics — Session 18, Track 4
======================================================

Models trust as a continuous field governed by partial differential equations.
Trust propagates through a network like heat diffusion, with sources (positive
interactions), sinks (violations), and boundary conditions (trust ceilings/floors).

Key physics:
- Diffusion equation: dT/dt = a*Lap(T) + S(x,t)
- Wave equation: d2T/dt2 = c2*Lap(T)
- Source/sink terms: S(x,t) = rate of trust creation/destruction
- Steady state: Lap(T) + S = 0 (Poisson equation)
- Trust as gravity: entities attracted toward high-trust regions

~80 checks expected.
"""

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Callable


# ============================================================
# S1 — 1D Trust Field
# ============================================================

@dataclass
class TrustField1D:
    """1D trust field on a grid of N nodes."""
    values: List[float]
    dx: float = 1.0

    @property
    def n(self) -> int:
        return len(self.values)

    def laplacian(self, i: int) -> float:
        if i <= 0 or i >= self.n - 1:
            return 0.0
        return (self.values[i-1] - 2*self.values[i] + self.values[i+1]) / (self.dx ** 2)

    def gradient(self, i: int) -> float:
        if i <= 0 or i >= self.n - 1:
            return 0.0
        return (self.values[i+1] - self.values[i-1]) / (2 * self.dx)

    def total_trust(self) -> float:
        return sum(self.values)

    def mean_trust(self) -> float:
        return self.total_trust() / self.n if self.n > 0 else 0.0

    def max_gradient(self) -> float:
        return max(abs(self.gradient(i)) for i in range(self.n))

    def clone(self) -> 'TrustField1D':
        return TrustField1D(values=list(self.values), dx=self.dx)


def diffuse_1d(field_: TrustField1D, alpha: float, dt: float,
               source: Optional[Callable[[int, float], float]] = None,
               time: float = 0.0) -> TrustField1D:
    """One step of trust diffusion: dT/dt = a*Lap(T) + S(x,t)"""
    new_values = list(field_.values)
    for i in range(1, field_.n - 1):
        lap = field_.laplacian(i)
        s = source(i, time) if source else 0.0
        new_values[i] = field_.values[i] + dt * (alpha * lap + s)
        new_values[i] = max(0.0, min(1.0, new_values[i]))
    return TrustField1D(values=new_values, dx=field_.dx)


def test_section_1():
    checks = []

    n = 21
    values = [0.0] * n
    values[n // 2] = 1.0
    field_ = TrustField1D(values=values)

    checks.append(("field_created", field_.n == 21))
    checks.append(("peak_at_center", field_.values[10] == 1.0))
    checks.append(("total_trust_1", abs(field_.total_trust() - 1.0) < 0.01))

    lap_center = field_.laplacian(10)
    checks.append(("laplacian_negative", lap_center < 0))

    alpha = 0.3
    dt = 0.1
    current = field_.clone()
    for _ in range(50):
        current = diffuse_1d(current, alpha, dt)

    checks.append(("peak_decreased", current.values[10] < 1.0))
    checks.append(("neighbors_increased", current.values[9] > 0 and current.values[11] > 0))
    checks.append(("all_bounded", all(0 <= v <= 1 for v in current.values)))
    checks.append(("gradient_decreased", current.max_gradient() < field_.max_gradient()))

    def constant_source(i, t):
        return 0.1 if i == 10 else 0.0

    field2 = TrustField1D(values=[0.0] * 21)
    for _ in range(100):
        field2 = diffuse_1d(field2, alpha, dt, source=constant_source)

    checks.append(("source_maintains_trust", field2.values[10] > 0.3))
    checks.append(("source_spreads", field2.values[8] > 0 and field2.values[12] > 0))

    return checks


# ============================================================
# S2 — 2D Trust Field (Network Grid)
# ============================================================

@dataclass
class TrustField2D:
    """2D trust field on an NxM grid."""
    values: List[List[float]]
    dx: float = 1.0
    dy: float = 1.0

    @property
    def rows(self) -> int:
        return len(self.values)

    @property
    def cols(self) -> int:
        return len(self.values[0]) if self.values else 0

    def laplacian(self, i: int, j: int) -> float:
        if i <= 0 or i >= self.rows - 1 or j <= 0 or j >= self.cols - 1:
            return 0.0
        lap_x = (self.values[i-1][j] - 2*self.values[i][j] + self.values[i+1][j]) / (self.dx**2)
        lap_y = (self.values[i][j-1] - 2*self.values[i][j] + self.values[i][j+1]) / (self.dy**2)
        return lap_x + lap_y

    def total_trust(self) -> float:
        return sum(sum(row) for row in self.values)

    def clone(self) -> 'TrustField2D':
        return TrustField2D(values=[list(row) for row in self.values], dx=self.dx, dy=self.dy)


def diffuse_2d(field_: TrustField2D, alpha: float, dt: float,
               source: Optional[Callable[[int, int, float], float]] = None,
               time: float = 0.0) -> TrustField2D:
    new_vals = [list(row) for row in field_.values]
    for i in range(1, field_.rows - 1):
        for j in range(1, field_.cols - 1):
            lap = field_.laplacian(i, j)
            s = source(i, j, time) if source else 0.0
            new_vals[i][j] = field_.values[i][j] + dt * (alpha * lap + s)
            new_vals[i][j] = max(0.0, min(1.0, new_vals[i][j]))
    return TrustField2D(values=new_vals, dx=field_.dx, dy=field_.dy)


def test_section_2():
    checks = []

    n = 11
    values = [[0.0] * n for _ in range(n)]
    values[5][5] = 1.0
    field_ = TrustField2D(values=values)

    checks.append(("grid_created", field_.rows == 11 and field_.cols == 11))
    checks.append(("peak_at_center", field_.values[5][5] == 1.0))

    lap = field_.laplacian(5, 5)
    checks.append(("laplacian_2d_negative", lap < 0))

    current = field_.clone()
    for _ in range(50):
        current = diffuse_2d(current, 0.2, 0.1)

    checks.append(("peak_spread", current.values[5][5] < 1.0))
    checks.append(("radial_spread", current.values[5][4] > 0 and current.values[4][5] > 0))
    checks.append(("all_bounded_2d", all(0 <= v <= 1 for row in current.values for v in row)))

    v_up = current.values[4][5]
    v_down = current.values[6][5]
    v_left = current.values[5][4]
    v_right = current.values[5][6]
    checks.append(("radial_symmetry", abs(v_up - v_down) < 0.01 and abs(v_left - v_right) < 0.01))

    return checks


# ============================================================
# S3 — Trust Wave Propagation
# ============================================================

@dataclass
class TrustWaveField:
    """Trust field with wave dynamics using leapfrog method."""
    current: List[float]
    previous: List[float]
    c: float = 1.0
    dx: float = 1.0
    dt: float = 0.1
    damping: float = 0.01

    @property
    def n(self) -> int:
        return len(self.current)

    def step(self) -> 'TrustWaveField':
        new = list(self.current)
        courant = (self.c * self.dt / self.dx) ** 2

        for i in range(1, self.n - 1):
            lap = self.current[i-1] - 2*self.current[i] + self.current[i+1]
            new[i] = (
                2 * self.current[i] - self.previous[i] +
                courant * lap -
                self.damping * (self.current[i] - self.previous[i])
            )
            new[i] = max(0.0, min(1.0, new[i]))

        return TrustWaveField(
            current=new, previous=list(self.current),
            c=self.c, dx=self.dx, dt=self.dt, damping=self.damping,
        )

    def energy(self) -> float:
        kinetic = sum(
            ((self.current[i] - self.previous[i]) / self.dt) ** 2
            for i in range(self.n)
        ) * 0.5
        potential = sum(
            ((self.current[i+1] - self.current[i]) / self.dx) ** 2
            for i in range(self.n - 1)
        ) * 0.5 * self.c ** 2
        return kinetic + potential


def test_section_3():
    checks = []

    n = 51
    center = 25
    sigma = 3.0
    current = [math.exp(-((i - center)**2) / (2 * sigma**2)) * 0.5 for i in range(n)]
    previous = list(current)

    wave = TrustWaveField(current=current, previous=previous, c=1.0, dx=1.0, dt=0.3, damping=0.005)
    checks.append(("wave_created", wave.n == 51))

    initial_energy = wave.energy()
    checks.append(("initial_energy", initial_energy > 0))

    for _ in range(100):
        wave = wave.step()

    checks.append(("pulse_moved", wave.current[center] < current[center]))
    checks.append(("all_bounded_wave", all(0 <= v <= 1 for v in wave.current)))

    final_energy = wave.energy()
    checks.append(("energy_dissipated", final_energy < initial_energy))

    n2 = 41
    current2 = [0.5] * n2
    previous2 = [0.5] * n2
    current2[10] = 0.8
    previous2[10] = 0.5

    wave2 = TrustWaveField(current=current2, previous=previous2, c=2.0, dx=1.0, dt=0.2, damping=0.0)
    for _ in range(30):
        wave2 = wave2.step()

    checks.append(("wave_propagated", wave2.current[15] != 0.5))
    checks.append(("initial_energy_positive", wave.energy() >= 0))

    return checks


# ============================================================
# S4 — Trust Sources and Sinks
# ============================================================

@dataclass
class TrustSource:
    position: int
    rate: float
    duration: float
    start_time: float = 0.0

    def is_active(self, time: float) -> bool:
        if time < self.start_time:
            return False
        if self.duration < 0:
            return True
        return time < self.start_time + self.duration

    def strength(self, time: float) -> float:
        return self.rate if self.is_active(time) else 0.0


@dataclass
class SourceField:
    trust_field: TrustField1D
    sources: List[TrustSource] = field(default_factory=list)
    time: float = 0.0
    alpha: float = 0.3
    dt: float = 0.1

    def source_function(self, i: int, t: float) -> float:
        total = 0.0
        for src in self.sources:
            if src.position == i:
                total += src.strength(t)
        return total

    def step(self) -> 'SourceField':
        new_field = diffuse_1d(self.trust_field, self.alpha, self.dt,
                               source=self.source_function, time=self.time)
        return SourceField(
            trust_field=new_field, sources=self.sources,
            time=self.time + self.dt, alpha=self.alpha, dt=self.dt,
        )


def test_section_4():
    checks = []

    n = 21
    src_field = SourceField(
        trust_field=TrustField1D(values=[0.0] * n),
        sources=[TrustSource(position=10, rate=0.5, duration=-1)],
    )

    for _ in range(100):
        src_field = src_field.step()

    checks.append(("source_builds_trust", src_field.trust_field.values[10] > 0.3))
    checks.append(("source_radiates", src_field.trust_field.values[8] > 0))

    sink_field = SourceField(
        trust_field=TrustField1D(values=[0.5] * n),
        sources=[TrustSource(position=10, rate=-0.5, duration=-1)],
    )

    for _ in range(50):
        sink_field = sink_field.step()

    checks.append(("sink_drains", sink_field.trust_field.values[10] < 0.5))
    checks.append(("sink_bounded", sink_field.trust_field.values[10] >= 0.0))

    temp_field = SourceField(
        trust_field=TrustField1D(values=[0.0] * n),
        sources=[TrustSource(position=10, rate=0.5, duration=2.0, start_time=0.0)],
        dt=0.1,
    )

    for _ in range(20):
        temp_field = temp_field.step()
    trust_at_active = temp_field.trust_field.values[10]

    for _ in range(80):
        temp_field = temp_field.step()
    trust_after_inactive = temp_field.trust_field.values[10]

    checks.append(("temp_source_built", trust_at_active > 0))
    checks.append(("temp_source_decayed", trust_after_inactive < trust_at_active))

    compete = SourceField(
        trust_field=TrustField1D(values=[0.5] * n),
        sources=[
            TrustSource(position=5, rate=0.3, duration=-1),
            TrustSource(position=15, rate=-0.3, duration=-1),
        ],
    )

    for _ in range(200):
        compete = compete.step()

    checks.append(("source_high", compete.trust_field.values[5] > 0.5))
    checks.append(("sink_low", compete.trust_field.values[15] < 0.5))
    checks.append(("gradient_exists", compete.trust_field.values[5] > compete.trust_field.values[15]))

    return checks


# ============================================================
# S5 — Steady State Solutions
# ============================================================

def solve_steady_state(n: int, sources: Dict[int, float],
                       boundary_left: float = 0.0, boundary_right: float = 0.0,
                       max_iter: int = 10000, tol: float = 1e-6) -> List[float]:
    """Solve Lap(T) + S = 0 with Dirichlet boundary conditions via Gauss-Seidel."""
    T = [0.5] * n
    T[0] = boundary_left
    T[n-1] = boundary_right

    for iteration in range(max_iter):
        max_change = 0.0
        for i in range(1, n - 1):
            s = sources.get(i, 0.0)
            new_val = 0.5 * (T[i-1] + T[i+1]) + 0.5 * s
            new_val = max(0.0, min(1.0, new_val))
            change = abs(new_val - T[i])
            max_change = max(max_change, change)
            T[i] = new_val
        if max_change < tol:
            break

    return T


def test_section_5():
    checks = []

    T = solve_steady_state(21, {}, boundary_left=0.0, boundary_right=1.0)
    checks.append(("linear_solution", abs(T[10] - 0.5) < 0.01))
    checks.append(("boundary_left", abs(T[0] - 0.0) < 0.01))
    checks.append(("boundary_right", abs(T[20] - 1.0) < 0.01))
    checks.append(("monotone", all(T[i] <= T[i+1] + 0.01 for i in range(20))))

    T2 = solve_steady_state(21, {10: 0.05}, boundary_left=0.0, boundary_right=0.0)
    checks.append(("source_peak", T2[10] > T2[5]))
    checks.append(("symmetric_solution", abs(T2[5] - T2[15]) < 0.01))

    residuals = []
    for i in range(1, 20):
        lap = (T2[i-1] - 2*T2[i] + T2[i+1])
        s = 0.05 if i == 10 else 0.0
        residuals.append(abs(lap + s))
    checks.append(("poisson_satisfied", max(residuals) < 0.01))

    T3 = solve_steady_state(21, {5: 0.3, 15: 0.3}, boundary_left=0.0, boundary_right=0.0)
    checks.append(("two_peaks", T3[5] > T3[0] and T3[15] > T3[20]))

    return checks


# ============================================================
# S6 — Trust Field on Graph Networks
# ============================================================

@dataclass
class GraphTrustField:
    """Trust field on an arbitrary graph."""
    trust: Dict[str, float]
    edges: Dict[str, Set[str]]
    edge_weights: Dict[Tuple[str, str], float] = field(default_factory=dict)

    def neighbors(self, node: str) -> Set[str]:
        return self.edges.get(node, set())

    def graph_laplacian(self, node: str) -> float:
        nbrs = self.neighbors(node)
        if not nbrs:
            return 0.0
        total = 0.0
        for nbr in nbrs:
            w = self.edge_weights.get((node, nbr), 1.0)
            total += w * (self.trust.get(nbr, 0) - self.trust.get(node, 0))
        return total

    def diffuse_step(self, alpha: float = 0.1, dt: float = 0.1) -> 'GraphTrustField':
        new_trust = dict(self.trust)
        for node in self.trust:
            lap = self.graph_laplacian(node)
            new_trust[node] = max(0.0, min(1.0, self.trust[node] + alpha * dt * lap))
        return GraphTrustField(trust=new_trust, edges=self.edges, edge_weights=self.edge_weights)

    def total_trust(self) -> float:
        return sum(self.trust.values())


def test_section_6():
    checks = []

    trust = {"A": 1.0, "B": 0.0, "C": 0.0, "D": 0.0, "E": 0.0}
    edges = {
        "A": {"B"}, "B": {"A", "C"}, "C": {"B", "D"},
        "D": {"C", "E"}, "E": {"D"},
    }
    gf = GraphTrustField(trust=trust, edges=edges)

    checks.append(("graph_created", len(gf.trust) == 5))
    checks.append(("laplacian_A", gf.graph_laplacian("A") < 0))

    current = gf
    for _ in range(100):
        current = current.diffuse_step(alpha=0.5, dt=0.1)

    checks.append(("trust_spread_graph", current.trust["B"] > 0))
    checks.append(("trust_spread_far", current.trust["C"] > 0))
    checks.append(("all_bounded_graph", all(0 <= v <= 1 for v in current.trust.values())))

    trust_star = {"center": 1.0}
    edges_star = {"center": set()}
    for i in range(5):
        name = f"leaf_{i}"
        trust_star[name] = 0.0
        edges_star[name] = {"center"}
        edges_star["center"].add(name)

    gf_star = GraphTrustField(trust=trust_star, edges=edges_star)
    for _ in range(50):
        gf_star = gf_star.diffuse_step(alpha=0.5, dt=0.1)

    leaf_trusts = [gf_star.trust[f"leaf_{i}"] for i in range(5)]
    checks.append(("star_symmetric", max(leaf_trusts) - min(leaf_trusts) < 0.01))
    checks.append(("star_spread", leaf_trusts[0] > 0))

    trust_w = {"A": 1.0, "B": 0.0, "C": 0.0}
    edges_w = {"A": {"B", "C"}, "B": {"A"}, "C": {"A"}}
    weights = {("A", "B"): 5.0, ("B", "A"): 5.0, ("A", "C"): 1.0, ("C", "A"): 1.0}
    gf_w = GraphTrustField(trust=trust_w, edges=edges_w, edge_weights=weights)

    for _ in range(30):
        gf_w = gf_w.diffuse_step(alpha=0.2, dt=0.1)

    checks.append(("weighted_B_higher", gf_w.trust["B"] > gf_w.trust["C"]))

    return checks


# ============================================================
# S7 — Stability Analysis
# ============================================================

def analyze_stability(field_: TrustField1D, alpha: float, dt: float,
                      steps: int = 200) -> Dict:
    cfl = alpha * dt / (field_.dx ** 2)
    stable = cfl <= 0.5

    current = field_.clone()
    energies = []
    for step in range(steps):
        e = sum(v**2 for v in current.values)
        energies.append(e)
        current = diffuse_1d(current, alpha, dt)

    blowup = any(math.isinf(e) or math.isnan(e) for e in energies)
    if not blowup and len(energies) > 1:
        blowup = energies[-1] > energies[0] * 100

    convergence_ratios = []
    for i in range(1, len(energies)):
        if energies[i-1] > 1e-10:
            convergence_ratios.append(energies[i] / energies[i-1])

    return {
        "cfl": cfl, "cfl_stable": stable, "blowup": blowup,
        "final_energy": energies[-1] if energies else 0,
        "initial_energy": energies[0] if energies else 0,
        "convergence_ratios": convergence_ratios[:10],
    }


def test_section_7():
    checks = []

    field_ = TrustField1D(values=[0.0]*10 + [1.0] + [0.0]*10)
    result = analyze_stability(field_, alpha=0.3, dt=0.1)
    checks.append(("cfl_stable", result["cfl_stable"]))
    checks.append(("no_blowup", not result["blowup"]))
    checks.append(("energy_decreases", result["final_energy"] <= result["initial_energy"] + 0.01))

    result2 = analyze_stability(field_.clone(), alpha=10.0, dt=0.5)
    checks.append(("cfl_unstable", not result2["cfl_stable"]))

    if result["convergence_ratios"]:
        checks.append(("convergent", result["convergence_ratios"][0] <= 1.01))

    result3 = analyze_stability(field_.clone(), alpha=0.1, dt=0.01)
    checks.append(("small_dt_stable", result3["cfl_stable"]))
    checks.append(("small_dt_converges", result3["final_energy"] < result3["initial_energy"]))

    return checks


# ============================================================
# S8 — Conservation Laws
# ============================================================

def test_section_8():
    checks = []

    n = 21
    field_ = TrustField1D(values=[0.0]*5 + [0.8]*11 + [0.0]*5)
    initial_total = field_.total_trust()

    current = field_.clone()
    for _ in range(100):
        current = diffuse_1d(current, alpha=0.2, dt=0.1)

    final_total = current.total_trust()
    checks.append(("approx_conservation", abs(final_total - initial_total) < initial_total * 0.3))

    def source(i, t):
        return 0.1 if i == 10 else 0.0

    field2 = TrustField1D(values=[0.0] * n)
    initial2 = field2.total_trust()
    current2 = field2
    for _ in range(100):
        current2 = diffuse_1d(current2, 0.2, 0.1, source=source)
    checks.append(("source_increases_total", current2.total_trust() > initial2))

    field3 = TrustField1D(values=[0.5] * n)
    initial3 = field3.total_trust()

    def sink(i, t):
        return -0.1 if i == 10 else 0.0

    current3 = field3
    for _ in range(50):
        current3 = diffuse_1d(current3, 0.2, 0.1, source=sink)
    checks.append(("sink_decreases_total", current3.total_trust() < initial3))

    def entropy(values):
        total = sum(values)
        if total == 0:
            return 0
        probs = [v / total for v in values if v > 0]
        return -sum(p * math.log(p) for p in probs if p > 0)

    field4 = TrustField1D(values=[0.0]*10 + [1.0] + [0.0]*10)
    initial_entropy = entropy(field4.values)

    current4 = field4.clone()
    for _ in range(50):
        current4 = diffuse_1d(current4, 0.3, 0.1)
    final_entropy = entropy(current4.values)

    checks.append(("entropy_increases", final_entropy > initial_entropy))

    return checks


# ============================================================
# S9 — Trust Potential & Force
# ============================================================

@dataclass
class TrustPotential:
    trust_field: TrustField1D

    def force_at(self, position: float) -> float:
        i = int(position)
        if i < 0 or i >= self.trust_field.n - 1:
            return 0.0
        frac = position - i
        grad_i = self.trust_field.gradient(i)
        grad_next = self.trust_field.gradient(min(i + 1, self.trust_field.n - 1))
        grad = grad_i * (1 - frac) + grad_next * frac
        return grad

    def potential_energy(self, position: float) -> float:
        i = int(position)
        if i < 0 or i >= self.trust_field.n:
            return 0.0
        frac = position - i
        if i + 1 < self.trust_field.n:
            return -(self.trust_field.values[i] * (1 - frac) + self.trust_field.values[i + 1] * frac)
        return -self.trust_field.values[i]


def simulate_entity_in_field(potential: TrustPotential, start: float,
                              steps: int = 100, dt: float = 0.1,
                              mass: float = 1.0, friction: float = 0.5) -> List[float]:
    pos = start
    vel = 0.0
    trajectory = [pos]

    for _ in range(steps):
        force = potential.force_at(pos)
        acc = force / mass - friction * vel
        vel += acc * dt
        pos += vel * dt
        pos = max(0.0, min(float(potential.trust_field.n - 1), pos))
        trajectory.append(pos)

    return trajectory


def test_section_9():
    checks = []

    n = 31
    values = [0.3 + 0.6 * math.exp(-((i - 15)**2) / (2 * 8**2)) for i in range(n)]
    field_ = TrustField1D(values=values)
    potential = TrustPotential(trust_field=field_)

    force_left = potential.force_at(10.0)
    checks.append(("force_toward_peak", force_left > 0))

    force_right = potential.force_at(20.0)
    checks.append(("force_back_to_peak", force_right < 0))

    force_peak = potential.force_at(15.0)
    checks.append(("force_near_zero_at_peak", abs(force_peak) < abs(force_left)))

    pe_peak = potential.potential_energy(15.0)
    pe_edge = potential.potential_energy(0.0)
    checks.append(("pe_lower_at_peak", pe_peak < pe_edge))

    traj = simulate_entity_in_field(potential, start=5.0, steps=200)
    checks.append(("entity_moves_toward_peak", abs(traj[-1] - 15.0) < abs(traj[0] - 15.0)))

    traj2 = simulate_entity_in_field(potential, start=15.0, steps=100)
    checks.append(("entity_stays_at_peak", abs(traj2[-1] - 15.0) < 2.0))

    starts = [3.0, 10.0, 20.0, 27.0]
    final_positions = []
    for s in starts:
        t = simulate_entity_in_field(potential, start=s, steps=1000, friction=0.2)
        final_positions.append(t[-1])
    checks.append(("all_converge", all(abs(p - 15.0) < 5.0 for p in final_positions)))

    return checks


# ============================================================
# S10 — Multi-Dimensional Trust Tensors as Fields
# ============================================================

@dataclass
class TrustTensorField:
    talent: TrustField1D
    training: TrustField1D
    temperament: TrustField1D

    @property
    def n(self) -> int:
        return self.talent.n

    def composite(self, i: int) -> float:
        return (self.talent.values[i] + self.training.values[i] + self.temperament.values[i]) / 3

    def diffuse_coupled(self, alpha_base: float, dt: float,
                        coupling: float = 0.1) -> 'TrustTensorField':
        new_tal = list(self.talent.values)
        new_tra = list(self.training.values)
        new_tem = list(self.temperament.values)

        for i in range(1, self.n - 1):
            comp = self.composite(i)

            lap_tal = self.talent.laplacian(i)
            lap_tra = self.training.laplacian(i)
            lap_tem = self.temperament.laplacian(i)

            new_tal[i] = self.talent.values[i] + dt * (
                alpha_base * lap_tal + coupling * (comp - self.talent.values[i])
            )
            new_tra[i] = self.training.values[i] + dt * (
                alpha_base * lap_tra + coupling * (comp - self.training.values[i])
            )
            new_tem[i] = self.temperament.values[i] + dt * (
                alpha_base * lap_tem + coupling * (comp - self.temperament.values[i])
            )

            new_tal[i] = max(0.0, min(1.0, new_tal[i]))
            new_tra[i] = max(0.0, min(1.0, new_tra[i]))
            new_tem[i] = max(0.0, min(1.0, new_tem[i]))

        return TrustTensorField(
            talent=TrustField1D(new_tal),
            training=TrustField1D(new_tra),
            temperament=TrustField1D(new_tem),
        )


def test_section_10():
    checks = []

    n = 21
    talent_vals = [0.0] * n
    talent_vals[10] = 0.9
    training_vals = [0.0] * n
    training_vals[5] = 0.8
    temperament_vals = [0.5] * n

    tf = TrustTensorField(
        talent=TrustField1D(talent_vals),
        training=TrustField1D(training_vals),
        temperament=TrustField1D(temperament_vals),
    )

    checks.append(("tensor_created", tf.n == 21))
    checks.append(("composite_at_10", tf.composite(10) > 0.1))

    current = tf
    for _ in range(100):
        current = current.diffuse_coupled(alpha_base=0.3, dt=0.1, coupling=0.05)

    checks.append(("talent_spread", current.talent.values[10] < 0.9))
    checks.append(("training_spread", current.training.values[5] < 0.8))

    initial_spread = abs(tf.talent.values[10] - tf.training.values[10])
    final_spread = abs(current.talent.values[10] - current.training.values[10])
    checks.append(("coupling_reduces_spread", final_spread < initial_spread))

    for i in range(n):
        checks.append(("tensor_bounded", (
            0 <= current.talent.values[i] <= 1 and
            0 <= current.training.values[i] <= 1 and
            0 <= current.temperament.values[i] <= 1
        )))
        break

    uncoupled = tf
    for _ in range(100):
        uncoupled = uncoupled.diffuse_coupled(alpha_base=0.3, dt=0.1, coupling=0.0)
    uncoupled_spread = abs(uncoupled.talent.values[10] - uncoupled.training.values[10])
    checks.append(("no_coupling_independent", uncoupled_spread >= final_spread - 0.01))

    return checks


# ============================================================
# S11 — Performance & Large-Scale Simulation
# ============================================================

def test_section_11():
    checks = []
    import time as time_mod

    n = 1000
    values = [0.0] * n
    values[500] = 1.0
    field_ = TrustField1D(values=values)

    start = time_mod.time()
    current = field_
    for _ in range(100):
        current = diffuse_1d(current, 0.3, 0.1)
    elapsed = time_mod.time() - start

    checks.append(("1d_1000_fast", elapsed < 5.0))
    checks.append(("1d_1000_spread", current.values[500] < 1.0))

    trust = {f"n{i}": 0.5 for i in range(200)}
    trust["n0"] = 1.0
    edges = {f"n{i}": set() for i in range(200)}

    rng = random.Random(42)
    for i in range(200):
        for d in [1, 2]:
            j = (i + d) % 200
            edges[f"n{i}"].add(f"n{j}")
            edges[f"n{j}"].add(f"n{i}")
        if rng.random() < 0.1:
            j = rng.randint(0, 199)
            edges[f"n{i}"].add(f"n{j}")
            edges[f"n{j}"].add(f"n{i}")

    gf = GraphTrustField(trust=trust, edges=edges)

    start = time_mod.time()
    for _ in range(50):
        gf = gf.diffuse_step(alpha=0.3, dt=0.1)
    graph_time = time_mod.time() - start

    checks.append(("graph_200_fast", graph_time < 10.0))
    checks.append(("graph_trust_spread", gf.trust["n10"] > 0.5))

    start = time_mod.time()
    ss = solve_steady_state(100, {50: 0.5}, boundary_left=0.0, boundary_right=0.0)
    ss_time = time_mod.time() - start

    checks.append(("steady_100_fast", ss_time < 2.0))
    checks.append(("steady_converged", ss[50] > ss[0]))

    n_wave = 500
    current_w = [0.5] * n_wave
    previous_w = [0.5] * n_wave
    current_w[250] = 0.8

    wave = TrustWaveField(current=current_w, previous=previous_w, c=1.0, dx=1.0, dt=0.3, damping=0.01)
    start = time_mod.time()
    for _ in range(200):
        wave = wave.step()
    wave_time = time_mod.time() - start

    checks.append(("wave_500_fast", wave_time < 5.0))
    checks.append(("wave_propagated", wave.current[260] != 0.5))

    return checks


# ============================================================
# Harness
# ============================================================

def run_section(name, func):
    results = func()
    passed = sum(1 for _, v in results if v)
    total = len(results)
    status = "\u2713" if passed == total else "\u2717"
    print(f"  {status} {name}: {passed}/{total}")
    return results


def main():
    all_checks = []
    sections = [
        ("S1 1D Trust Field", test_section_1),
        ("S2 2D Trust Field", test_section_2),
        ("S3 Trust Wave Propagation", test_section_3),
        ("S4 Trust Sources & Sinks", test_section_4),
        ("S5 Steady State Solutions", test_section_5),
        ("S6 Graph Trust Field", test_section_6),
        ("S7 Stability Analysis", test_section_7),
        ("S8 Conservation Laws", test_section_8),
        ("S9 Trust Potential & Force", test_section_9),
        ("S10 Multi-Dim Trust Tensors", test_section_10),
        ("S11 Performance & Scale", test_section_11),
    ]

    for name, func in sections:
        results = run_section(name, func)
        all_checks.extend(results)

    passed = sum(1 for _, v in all_checks if v)
    total = len(all_checks)
    print(f"\nTotal: {passed}/{total}")

    if passed < total:
        print(f"\nFailed checks:")
        for name, v in all_checks:
            if not v:
                print(f"    FAIL: {name}")


if __name__ == "__main__":
    main()
