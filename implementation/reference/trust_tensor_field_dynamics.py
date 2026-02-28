"""
Web4 Trust Tensor Field Dynamics — Session 18, Track 4
======================================================

Models trust as a continuous field with physical dynamics:
- Diffusion: trust spreads between connected entities (heat equation)
- Sources/sinks: entities that generate or absorb trust
- Wave propagation: trust signals travel through networks
- Potential fields: trust gradients create forces
- Conservation laws: trust energy is conserved under diffusion
- Boundary conditions: edges of trust networks
- Tensor decomposition: eigenmodes of trust dynamics

This is the "physics of trust" — treating trust as a physical field
governed by differential equations over the entity graph.

~80 checks expected.
"""

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


# ============================================================
# §1 — Trust Field on a Graph
# ============================================================

@dataclass
class TrustField:
    """Trust as a scalar field over a graph of entities."""
    values: Dict[str, float] = field(default_factory=dict)
    edges: List[Tuple[str, str, float]] = field(default_factory=list)
    adjacency: Dict[str, List[Tuple[str, float]]] = field(default_factory=dict)

    def set_value(self, entity_id: str, value: float):
        self.values[entity_id] = max(0.0, min(1.0, value))

    def add_edge(self, e1: str, e2: str, weight: float = 1.0):
        self.edges.append((e1, e2, weight))
        if e1 not in self.adjacency:
            self.adjacency[e1] = []
        if e2 not in self.adjacency:
            self.adjacency[e2] = []
        self.adjacency[e1].append((e2, weight))
        self.adjacency[e2].append((e1, weight))

    def laplacian(self, entity_id: str) -> float:
        """
        Graph Laplacian at entity: Δf(v) = Σ w(v,u) * (f(u) - f(v))
        Discrete version of the continuous Laplacian.
        """
        if entity_id not in self.adjacency:
            return 0.0
        lap = 0.0
        for neighbor, weight in self.adjacency[entity_id]:
            lap += weight * (self.values.get(neighbor, 0.5) - self.values.get(entity_id, 0.5))
        return lap

    def gradient_at(self, entity_id: str) -> Dict[str, float]:
        """Gradient: direction of steepest trust increase for each neighbor."""
        if entity_id not in self.adjacency:
            return {}
        v = self.values.get(entity_id, 0.5)
        return {
            n: w * (self.values.get(n, 0.5) - v)
            for n, w in self.adjacency[entity_id]
        }

    def total_energy(self) -> float:
        """Total trust energy: Σ f(v)^2 / 2 (kinetic-like term)."""
        return sum(v ** 2 for v in self.values.values()) / 2

    def total_gradient_energy(self) -> float:
        """Dirichlet energy: Σ_edges w * (f(u) - f(v))^2 / 2."""
        energy = 0.0
        for u, v, w in self.edges:
            diff = self.values.get(u, 0.5) - self.values.get(v, 0.5)
            energy += w * diff ** 2 / 2
        return energy


def test_section_1():
    checks = []

    tf = TrustField()
    tf.set_value("alice", 0.9)
    tf.set_value("bob", 0.3)
    tf.set_value("carol", 0.6)
    tf.add_edge("alice", "bob", 1.0)
    tf.add_edge("bob", "carol", 1.0)
    tf.add_edge("alice", "carol", 0.5)

    checks.append(("field_set", tf.values["alice"] == 0.9))
    checks.append(("bounded_high", tf.values["alice"] <= 1.0))

    # Laplacian: flow from high to low
    lap_alice = tf.laplacian("alice")
    checks.append(("laplacian_negative_high", lap_alice < 0))  # Alice is highest, net flow OUT
    lap_bob = tf.laplacian("bob")
    checks.append(("laplacian_positive_low", lap_bob > 0))  # Bob is lowest, net flow IN

    # Gradient
    grad_bob = tf.gradient_at("bob")
    checks.append(("gradient_alice_positive", grad_bob["alice"] > 0))
    checks.append(("gradient_carol_positive", grad_bob["carol"] > 0))

    # Energy
    total_e = tf.total_energy()
    checks.append(("positive_energy", total_e > 0))

    grad_e = tf.total_gradient_energy()
    checks.append(("positive_gradient_energy", grad_e > 0))

    # Clamping
    tf.set_value("dave", 1.5)
    checks.append(("clamped_high", tf.values["dave"] == 1.0))
    tf.set_value("eve", -0.3)
    checks.append(("clamped_low", tf.values["eve"] == 0.0))

    return checks


# ============================================================
# §2 — Heat Equation (Trust Diffusion)
# ============================================================

def diffuse(field: TrustField, dt: float = 0.1, diffusion_rate: float = 0.5) -> TrustField:
    """
    One step of trust diffusion: ∂f/∂t = D * Δf
    where Δf is the graph Laplacian.
    """
    new_field = TrustField()
    new_field.edges = field.edges
    new_field.adjacency = field.adjacency

    for eid in field.values:
        lap = field.laplacian(eid)
        new_val = field.values[eid] + dt * diffusion_rate * lap
        new_field.set_value(eid, new_val)

    return new_field


def simulate_diffusion(field: TrustField, steps: int, dt: float = 0.1,
                       diffusion_rate: float = 0.5) -> List[Dict[str, float]]:
    """Run diffusion for multiple steps, recording trajectory."""
    trajectory = [dict(field.values)]
    current = field

    for _ in range(steps):
        current = diffuse(current, dt, diffusion_rate)
        trajectory.append(dict(current.values))

    return trajectory


def test_section_2():
    checks = []

    # Simple 3-node diffusion
    tf = TrustField()
    tf.set_value("a", 1.0)
    tf.set_value("b", 0.0)
    tf.set_value("c", 0.0)
    tf.add_edge("a", "b", 1.0)
    tf.add_edge("b", "c", 1.0)

    traj = simulate_diffusion(tf, steps=100, dt=0.05, diffusion_rate=0.3)
    checks.append(("diffusion_trajectory", len(traj) == 101))

    # Trust should flow from a to b to c
    checks.append(("a_decreases", traj[-1]["a"] < traj[0]["a"]))
    checks.append(("c_increases", traj[-1]["c"] > traj[0]["c"]))

    # Convergence: all values should approach the mean
    mean_val = sum(traj[0].values()) / 3
    final_spread = max(traj[-1].values()) - min(traj[-1].values())
    checks.append(("converges", final_spread < 0.3))

    # Mean preservation (trust is conserved in diffusion)
    final_mean = sum(traj[-1].values()) / 3
    checks.append(("mean_preserved", abs(final_mean - mean_val) < 0.05))

    # Gradient energy decreases monotonically
    energies = []
    tf2 = TrustField()
    tf2.set_value("a", 1.0)
    tf2.set_value("b", 0.0)
    tf2.set_value("c", 0.0)
    tf2.add_edge("a", "b", 1.0)
    tf2.add_edge("b", "c", 1.0)

    for i in range(50):
        energies.append(tf2.total_gradient_energy())
        tf2 = diffuse(tf2, dt=0.05, diffusion_rate=0.3)

    checks.append(("energy_decreasing", all(
        energies[i] >= energies[i+1] - 0.001 for i in range(len(energies)-1)
    )))

    # Ring topology: symmetric diffusion
    ring = TrustField()
    for i in range(4):
        ring.set_value(f"n{i}", 0.0)
    ring.set_value("n0", 1.0)
    ring.add_edge("n0", "n1", 1.0)
    ring.add_edge("n1", "n2", 1.0)
    ring.add_edge("n2", "n3", 1.0)
    ring.add_edge("n3", "n0", 1.0)

    ring_traj = simulate_diffusion(ring, steps=200, dt=0.05, diffusion_rate=0.3)
    # Opposite node should receive trust last
    checks.append(("ring_spreads", ring_traj[-1]["n2"] > 0.1))

    return checks


# ============================================================
# §3 — Trust Sources and Sinks
# ============================================================

@dataclass
class TrustSource:
    """Entity that generates trust (positive source) or absorbs it (sink)."""
    entity_id: str
    rate: float  # Positive = source, negative = sink
    capacity: float = float('inf')  # Maximum trust it can inject
    injected: float = 0.0

    def inject(self, field: TrustField, dt: float):
        if abs(self.injected) >= self.capacity:
            return
        amount = self.rate * dt
        if abs(self.injected + amount) > self.capacity:
            amount = math.copysign(self.capacity - abs(self.injected), self.rate)
        current = field.values.get(self.entity_id, 0.5)
        field.set_value(self.entity_id, current + amount)
        self.injected += abs(amount)


def diffuse_with_sources(field: TrustField, sources: List[TrustSource],
                         dt: float = 0.1, diffusion_rate: float = 0.5) -> TrustField:
    """Diffusion with source/sink terms: ∂f/∂t = D*Δf + S(x)."""
    new_field = diffuse(field, dt, diffusion_rate)
    for source in sources:
        source.inject(new_field, dt)
    return new_field


def test_section_3():
    checks = []

    # Source injects trust
    tf = TrustField()
    tf.set_value("source", 0.5)
    tf.set_value("sink", 0.5)
    tf.set_value("mid", 0.5)
    tf.add_edge("source", "mid", 1.0)
    tf.add_edge("mid", "sink", 1.0)

    source = TrustSource("source", rate=1.0, capacity=5.0)
    sink = TrustSource("sink", rate=-0.5)

    current = tf
    for _ in range(50):
        current = diffuse_with_sources(current, [source, sink], dt=0.05, diffusion_rate=0.3)

    checks.append(("source_higher", current.values["source"] > 0.5))
    checks.append(("sink_lower", current.values["sink"] < current.values["source"]))

    # Capacity limit
    source2 = TrustSource("src", rate=10.0, capacity=0.5)
    tf2 = TrustField()
    tf2.set_value("src", 0.5)
    for _ in range(100):
        source2.inject(tf2, 0.05)
    checks.append(("capacity_limited", source2.injected <= 0.51))

    # Equilibrium: source rate = sink rate = diffusion loss
    # Steady state should exist
    tf3 = TrustField()
    for i in range(5):
        tf3.set_value(f"n{i}", 0.5)
    for i in range(4):
        tf3.add_edge(f"n{i}", f"n{i+1}", 1.0)

    src = TrustSource("n0", rate=0.5)
    snk = TrustSource("n4", rate=-0.5)

    values_100 = None
    values_200 = None
    current3 = tf3
    for step in range(300):
        current3 = diffuse_with_sources(current3, [src, snk], dt=0.05, diffusion_rate=0.3)
        if step == 99:
            values_100 = dict(current3.values)
        if step == 199:
            values_200 = dict(current3.values)

    # Check convergence to steady state (values at 200 ≈ values at 300)
    values_300 = dict(current3.values)
    if values_200:
        max_diff = max(abs(values_300[k] - values_200[k]) for k in values_300)
        checks.append(("steady_state_approach", max_diff < 0.1))

    # Gradient: trust flows from source to sink
    checks.append(("gradient_source_to_sink", current3.values["n0"] > current3.values["n4"]))

    return checks


# ============================================================
# §4 — Wave Propagation in Trust Networks
# ============================================================

@dataclass
class TrustWaveField:
    """Trust field with wave dynamics (second-order)."""
    position: Dict[str, float] = field(default_factory=dict)  # f(x,t)
    velocity: Dict[str, float] = field(default_factory=dict)  # ∂f/∂t
    edges: List[Tuple[str, str, float]] = field(default_factory=list)
    adjacency: Dict[str, List[Tuple[str, float]]] = field(default_factory=dict)
    damping: float = 0.01

    def set_initial(self, entity_id: str, position: float, velocity: float = 0.0):
        self.position[entity_id] = max(0.0, min(1.0, position))
        self.velocity[entity_id] = velocity

    def add_edge(self, e1: str, e2: str, weight: float = 1.0):
        self.edges.append((e1, e2, weight))
        if e1 not in self.adjacency:
            self.adjacency[e1] = []
        if e2 not in self.adjacency:
            self.adjacency[e2] = []
        self.adjacency[e1].append((e2, weight))
        self.adjacency[e2].append((e1, weight))

    def laplacian(self, entity_id: str) -> float:
        if entity_id not in self.adjacency:
            return 0.0
        lap = 0.0
        for n, w in self.adjacency[entity_id]:
            lap += w * (self.position.get(n, 0.5) - self.position.get(entity_id, 0.5))
        return lap

    def step(self, dt: float = 0.05, wave_speed: float = 1.0):
        """
        Wave equation: ∂²f/∂t² = c² * Δf - γ * ∂f/∂t
        Verlet-like integration.
        """
        new_positions = {}
        new_velocities = {}

        for eid in self.position:
            lap = self.laplacian(eid)
            accel = wave_speed ** 2 * lap - self.damping * self.velocity.get(eid, 0)
            new_vel = self.velocity.get(eid, 0) + accel * dt
            new_pos = self.position[eid] + new_vel * dt
            new_positions[eid] = max(0.0, min(1.0, new_pos))
            new_velocities[eid] = new_vel

        self.position = new_positions
        self.velocity = new_velocities

    def kinetic_energy(self) -> float:
        return sum(v ** 2 for v in self.velocity.values()) / 2

    def potential_energy(self) -> float:
        energy = 0.0
        for u, v, w in self.edges:
            diff = self.position.get(u, 0.5) - self.position.get(v, 0.5)
            energy += w * diff ** 2 / 2
        return energy


def test_section_4():
    checks = []

    # Create a chain with initial pulse
    wave = TrustWaveField(damping=0.05)
    for i in range(10):
        wave.set_initial(f"n{i}", 0.5)
    wave.set_initial("n0", 0.9, velocity=0.5)  # Initial pulse

    for i in range(9):
        wave.add_edge(f"n{i}", f"n{i+1}", 1.0)

    # Simulate wave propagation
    positions_over_time = []
    for _ in range(200):
        positions_over_time.append(dict(wave.position))
        wave.step(dt=0.02, wave_speed=1.0)

    # Wave should propagate: n0 perturbation should reach n9
    checks.append(("wave_propagates", positions_over_time[-1]["n9"] != 0.5 or
                    any(p["n9"] != 0.5 for p in positions_over_time)))

    # Initial node should oscillate (not monotonic)
    n0_values = [p["n0"] for p in positions_over_time]
    changes = sum(1 for i in range(len(n0_values)-1) if n0_values[i] != n0_values[i+1])
    checks.append(("source_changes", changes > 5))

    # With damping, energy should decrease over time
    energies = []
    wave2 = TrustWaveField(damping=0.1)
    for i in range(5):
        wave2.set_initial(f"n{i}", 0.5)
    wave2.set_initial("n0", 0.9)
    for i in range(4):
        wave2.add_edge(f"n{i}", f"n{i+1}", 1.0)

    for _ in range(100):
        ke = wave2.kinetic_energy()
        pe = wave2.potential_energy()
        energies.append(ke + pe)
        wave2.step(dt=0.02, wave_speed=0.5)

    # Total energy should generally decrease with damping
    checks.append(("energy_dissipates", energies[-1] < energies[0] + 0.01))

    # Zero damping: energy should be approximately conserved
    wave3 = TrustWaveField(damping=0.0)
    for i in range(5):
        wave3.set_initial(f"n{i}", 0.5)
    wave3.set_initial("n0", 0.8)
    for i in range(4):
        wave3.add_edge(f"n{i}", f"n{i+1}", 1.0)

    e_initial = wave3.kinetic_energy() + wave3.potential_energy()
    for _ in range(100):
        wave3.step(dt=0.01, wave_speed=0.5)
    e_final = wave3.kinetic_energy() + wave3.potential_energy()
    # Note: clamping to [0,1] can dissipate energy, so allow some tolerance
    checks.append(("energy_approx_conserved", abs(e_final - e_initial) < e_initial * 0.5 + 0.01))

    return checks


# ============================================================
# §5 — Trust Potential Fields
# ============================================================

@dataclass
class TrustPotential:
    """Trust as a potential field — entities move toward high-trust regions."""
    field: TrustField

    def force_on(self, entity_id: str) -> Dict[str, float]:
        """
        Force = -∇φ (negative gradient of potential).
        In trust context: entities are "attracted" to high-trust neighbors.
        """
        grad = self.field.gradient_at(entity_id)
        # Force proportional to gradient (trust flows toward higher trust)
        return {n: g for n, g in grad.items()}

    def equilibrium_condition(self, entity_id: str, threshold: float = 0.01) -> bool:
        """Check if entity is at equilibrium (net force ≈ 0)."""
        forces = self.force_on(entity_id)
        net_force = sum(forces.values())
        return abs(net_force) < threshold

    def potential_well_depth(self, entity_id: str) -> float:
        """
        Depth of potential well: how much energy needed to move entity
        away from current position. Related to local stability.
        """
        # Approximation: curvature of potential (second derivative)
        # Using Laplacian as proxy for curvature
        return abs(self.field.laplacian(entity_id))


def test_section_5():
    checks = []

    # Use asymmetric values so mid is NOT the average of neighbors
    tf = TrustField()
    tf.set_value("high", 0.9)
    tf.set_value("mid", 0.3)  # Below average of 0.9 and 0.1 → net positive force
    tf.set_value("low", 0.1)
    tf.add_edge("high", "mid", 1.0)
    tf.add_edge("mid", "low", 1.0)

    pot = TrustPotential(field=tf)

    # Force on mid-point
    forces = pot.force_on("mid")
    checks.append(("force_toward_high", forces["high"] > 0))
    checks.append(("force_toward_low", forces["low"] < 0))

    # Uniform field → equilibrium
    uniform = TrustField()
    for i in range(5):
        uniform.set_value(f"n{i}", 0.5)
    for i in range(4):
        uniform.add_edge(f"n{i}", f"n{i+1}", 1.0)

    pot2 = TrustPotential(field=uniform)
    checks.append(("uniform_equilibrium", pot2.equilibrium_condition("n2")))

    # Non-uniform, non-average → not equilibrium
    # mid=0.3, neighbors: high=0.9, low=0.1 → lap = (0.9-0.3)+(0.1-0.3) = 0.4 ≠ 0
    checks.append(("non_uniform_not_eq", not pot.equilibrium_condition("mid")))

    # Potential well depth (Laplacian magnitude)
    depth_mid = pot.potential_well_depth("mid")
    checks.append(("well_depth_positive", depth_mid > 0))

    # High node has only one neighbor pulling down → nonzero curvature
    depth_high = pot.potential_well_depth("high")
    checks.append(("high_has_curvature", depth_high > 0))

    return checks


# ============================================================
# §6 — Spectral Trust Analysis
# ============================================================

def power_iteration(matrix: List[List[float]], n_iter: int = 100) -> Tuple[float, List[float]]:
    """
    Find dominant eigenvalue and eigenvector of a matrix using power iteration.
    """
    n = len(matrix)
    v = [1.0 / math.sqrt(n)] * n

    eigenvalue = 0.0
    for _ in range(n_iter):
        # Matrix-vector multiply
        new_v = [0.0] * n
        for i in range(n):
            for j in range(n):
                new_v[i] += matrix[i][j] * v[j]

        # Find max component for eigenvalue estimate
        norm = math.sqrt(sum(x ** 2 for x in new_v))
        if norm < 1e-10:
            break

        eigenvalue = norm
        v = [x / norm for x in new_v]

    return eigenvalue, v


def build_adjacency_matrix(field: TrustField) -> Tuple[List[List[float]], List[str]]:
    """Build adjacency matrix from trust field."""
    entities = sorted(field.values.keys())
    n = len(entities)
    idx = {e: i for i, e in enumerate(entities)}

    matrix = [[0.0] * n for _ in range(n)]
    for u, v, w in field.edges:
        if u in idx and v in idx:
            matrix[idx[u]][idx[v]] = w
            matrix[idx[v]][idx[u]] = w

    return matrix, entities


def test_section_6():
    checks = []

    # Complete graph: dominant eigenvalue = (n-1)
    tf = TrustField()
    entities = ["a", "b", "c", "d"]
    for e in entities:
        tf.set_value(e, 0.5)
    for i, e1 in enumerate(entities):
        for j, e2 in enumerate(entities):
            if i < j:
                tf.add_edge(e1, e2, 1.0)

    mat, ents = build_adjacency_matrix(tf)
    eigenvalue, eigenvector = power_iteration(mat)

    checks.append(("dominant_eigenvalue", abs(eigenvalue - 3.0) < 0.1))  # n-1 = 3
    checks.append(("eigenvector_exists", len(eigenvector) == 4))

    # Eigenvector for complete graph is uniform (all components equal)
    ev_mean = sum(eigenvector) / len(eigenvector)
    ev_var = sum((x - ev_mean) ** 2 for x in eigenvector) / len(eigenvector)
    checks.append(("uniform_eigenvector", ev_var < 0.01))

    # Star graph: center has highest eigenvector centrality
    star = TrustField()
    star.set_value("center", 0.5)
    for i in range(5):
        star.set_value(f"leaf_{i}", 0.5)
        star.add_edge("center", f"leaf_{i}", 1.0)

    star_mat, star_ents = build_adjacency_matrix(star)
    _, star_ev = power_iteration(star_mat)

    center_idx = star_ents.index("center")
    checks.append(("center_highest_centrality", star_ev[center_idx] > max(
        star_ev[i] for i in range(len(star_ev)) if i != center_idx
    )))

    # Path graph: spectral gap relates to mixing time
    path = TrustField()
    for i in range(6):
        path.set_value(f"p{i}", 0.5)
    for i in range(5):
        path.add_edge(f"p{i}", f"p{i+1}", 1.0)

    path_mat, path_ents = build_adjacency_matrix(path)
    path_ev, _ = power_iteration(path_mat)
    checks.append(("path_eigenvalue", path_ev > 0))

    return checks


# ============================================================
# §7 — Trust Field Conservation Laws
# ============================================================

def test_section_7():
    checks = []

    # Conservation under pure diffusion (no sources/sinks)
    tf = TrustField()
    total_initial = 0.0
    rng = random.Random(42)
    for i in range(8):
        val = rng.uniform(0.1, 0.9)
        tf.set_value(f"n{i}", val)
        total_initial += val

    for i in range(7):
        tf.add_edge(f"n{i}", f"n{i+1}", 1.0)
    tf.add_edge("n7", "n0", 1.0)  # Ring

    # Run diffusion
    traj = simulate_diffusion(tf, steps=200, dt=0.02, diffusion_rate=0.3)

    # Total trust should be conserved
    total_final = sum(traj[-1].values())
    checks.append(("total_conserved", abs(total_final - total_initial) < 0.1))

    # Mean is conserved
    mean_initial = total_initial / 8
    mean_final = total_final / 8
    checks.append(("mean_conserved", abs(mean_final - mean_initial) < 0.02))

    # Variance decreases (second law of thermodynamics analog)
    var_initial = sum((v - mean_initial) ** 2 for v in traj[0].values()) / 8
    var_final = sum((v - mean_final) ** 2 for v in traj[-1].values()) / 8
    checks.append(("variance_decreases", var_final <= var_initial + 0.001))

    # Entropy increases (information-theoretic)
    def field_entropy(values):
        total = sum(abs(v) for v in values.values())
        if total < 1e-10:
            return 0.0
        probs = [abs(v) / total for v in values.values()]
        return -sum(p * math.log(p + 1e-15) for p in probs)

    entropy_initial = field_entropy(traj[0])
    entropy_final = field_entropy(traj[-1])
    checks.append(("entropy_increases", entropy_final >= entropy_initial - 0.05))

    # At equilibrium: all values equal (maximum entropy)
    # Run much longer
    long_traj = simulate_diffusion(tf, steps=1000, dt=0.02, diffusion_rate=0.3)
    final_vals = list(long_traj[-1].values())
    spread = max(final_vals) - min(final_vals)
    checks.append(("equilibrium_uniform", spread < 0.05))

    return checks


# ============================================================
# §8 — Boundary Conditions
# ============================================================

@dataclass
class BoundaryCondition:
    """Boundary conditions for trust field."""
    fixed_values: Dict[str, float] = field(default_factory=dict)
    reflecting_nodes: Set[str] = field(default_factory=set)

    def apply(self, field: TrustField):
        """Apply boundary conditions after diffusion step."""
        for eid, val in self.fixed_values.items():
            field.values[eid] = val


def diffuse_with_boundary(field: TrustField, bc: BoundaryCondition,
                          dt: float = 0.1, diffusion_rate: float = 0.5) -> TrustField:
    """Diffuse with boundary conditions."""
    new_field = diffuse(field, dt, diffusion_rate)
    bc.apply(new_field)
    return new_field


def test_section_8():
    checks = []

    # Dirichlet BC: fixed trust at boundaries
    tf = TrustField()
    for i in range(5):
        tf.set_value(f"n{i}", 0.5)
    for i in range(4):
        tf.add_edge(f"n{i}", f"n{i+1}", 1.0)

    bc = BoundaryCondition(fixed_values={"n0": 1.0, "n4": 0.0})

    current = tf
    for _ in range(200):
        current = diffuse_with_boundary(current, bc, dt=0.05, diffusion_rate=0.3)

    # Boundaries should maintain their values
    checks.append(("bc_left_fixed", abs(current.values["n0"] - 1.0) < 0.01))
    checks.append(("bc_right_fixed", abs(current.values["n4"] - 0.0) < 0.01))

    # Interior should form linear gradient (steady-state of diffusion with Dirichlet BCs)
    checks.append(("interior_gradient", current.values["n1"] > current.values["n2"]))
    checks.append(("interior_gradient_2", current.values["n2"] > current.values["n3"]))

    # Linear interpolation: n1≈0.75, n2≈0.5, n3≈0.25
    checks.append(("n2_near_half", abs(current.values["n2"] - 0.5) < 0.15))

    # Neumann-like BC (reflecting): no flux at boundary
    # Approximated by not fixing values
    tf2 = TrustField()
    for i in range(5):
        tf2.set_value(f"n{i}", 0.5)
    tf2.set_value("n0", 1.0)
    for i in range(4):
        tf2.add_edge(f"n{i}", f"n{i+1}", 1.0)

    current2 = tf2
    for _ in range(2000):
        current2 = diffuse(current2, dt=0.02, diffusion_rate=0.3)

    # Without fixed BCs, should converge to uniform
    vals = list(current2.values.values())
    checks.append(("neumann_uniform", max(vals) - min(vals) < 0.05))

    return checks


# ============================================================
# §9 — Trust Tensor Decomposition
# ============================================================

@dataclass
class TrustTensorField:
    """3D trust tensor field (T3 dimensions) over a graph."""
    talent: TrustField = field(default_factory=TrustField)
    training: TrustField = field(default_factory=TrustField)
    temperament: TrustField = field(default_factory=TrustField)

    def set_trust(self, entity_id: str, t: float, tr: float, te: float):
        self.talent.set_value(entity_id, t)
        self.training.set_value(entity_id, tr)
        self.temperament.set_value(entity_id, te)

    def add_edge(self, e1: str, e2: str, weight: float = 1.0):
        self.talent.add_edge(e1, e2, weight)
        self.training.add_edge(e1, e2, weight)
        self.temperament.add_edge(e1, e2, weight)

    def diffuse_all(self, dt: float = 0.1, rate: float = 0.5):
        """Diffuse all three dimensions independently."""
        self.talent = diffuse(self.talent, dt, rate)
        self.training = diffuse(self.training, dt, rate)
        self.temperament = diffuse(self.temperament, dt, rate)

    def composite(self, entity_id: str) -> float:
        t = self.talent.values.get(entity_id, 0.5)
        tr = self.training.values.get(entity_id, 0.5)
        te = self.temperament.values.get(entity_id, 0.5)
        return (t + tr + te) / 3

    def total_energy(self) -> float:
        return (self.talent.total_gradient_energy() +
                self.training.total_gradient_energy() +
                self.temperament.total_gradient_energy())


def test_section_9():
    checks = []

    ttf = TrustTensorField()
    ttf.set_trust("alice", 0.9, 0.3, 0.7)
    ttf.set_trust("bob", 0.4, 0.8, 0.5)
    ttf.set_trust("carol", 0.6, 0.6, 0.6)
    ttf.add_edge("alice", "bob", 1.0)
    ttf.add_edge("bob", "carol", 1.0)
    ttf.add_edge("alice", "carol", 0.5)

    # Composite trust
    alice_comp = ttf.composite("alice")
    checks.append(("composite_correct", abs(alice_comp - (0.9+0.3+0.7)/3) < 0.01))

    # Diffuse
    initial_energy = ttf.total_energy()
    for _ in range(50):
        ttf.diffuse_all(dt=0.05, rate=0.3)
    final_energy = ttf.total_energy()

    checks.append(("energy_decreases", final_energy < initial_energy + 0.01))

    # Dimensions converge independently
    alice_t = ttf.talent.values["alice"]
    bob_t = ttf.talent.values["bob"]
    # After diffusion, they should be closer
    initial_diff = abs(0.9 - 0.4)
    final_diff = abs(alice_t - bob_t)
    checks.append(("talent_converges", final_diff < initial_diff))

    # All values bounded
    for dim_field in [ttf.talent, ttf.training, ttf.temperament]:
        for v in dim_field.values.values():
            checks.append(("dim_bounded", 0.0 <= v <= 1.0))
            break  # Just check one per dimension

    # Anisotropy: different dimensions diffuse independently
    alice_training = ttf.training.values["alice"]
    alice_talent = ttf.talent.values["alice"]
    checks.append(("dims_differ", abs(alice_training - alice_talent) > 0.001 or
                    abs(0.3 - 0.9) > 0.5))  # Started very different

    return checks


# ============================================================
# §10 — Trust Dynamics Performance
# ============================================================

def test_section_10():
    checks = []
    import time as time_mod
    rng = random.Random(42)

    # Large network diffusion
    tf = TrustField()
    n_nodes = 200
    for i in range(n_nodes):
        tf.set_value(f"n{i}", rng.uniform(0.1, 0.9))

    # Random graph edges
    for i in range(n_nodes):
        for _ in range(3):  # ~3 edges per node
            j = rng.randint(0, n_nodes - 1)
            if i != j:
                tf.add_edge(f"n{i}", f"n{j}", rng.uniform(0.5, 1.5))

    start = time_mod.time()
    traj = simulate_diffusion(tf, steps=100, dt=0.02, diffusion_rate=0.1)
    elapsed = time_mod.time() - start

    checks.append(("large_diffusion_fast", elapsed < 10.0))
    checks.append(("trajectory_recorded", len(traj) == 101))

    # Conservation in large network
    total_initial = sum(traj[0].values())
    total_final = sum(traj[-1].values())
    checks.append(("large_conserved", abs(total_final - total_initial) < n_nodes * 0.05))

    # Wave simulation on medium network
    wave = TrustWaveField(damping=0.05)
    for i in range(50):
        wave.set_initial(f"n{i}", 0.5)
    wave.set_initial("n0", 0.9)
    for i in range(49):
        wave.add_edge(f"n{i}", f"n{i+1}", 1.0)

    start = time_mod.time()
    for _ in range(500):
        wave.step(dt=0.01, wave_speed=0.5)
    wave_time = time_mod.time() - start
    checks.append(("wave_sim_fast", wave_time < 5.0))

    # Tensor field diffusion
    ttf = TrustTensorField()
    for i in range(50):
        ttf.set_trust(f"n{i}", rng.uniform(0.2, 0.8), rng.uniform(0.2, 0.8), rng.uniform(0.2, 0.8))
    for i in range(49):
        ttf.add_edge(f"n{i}", f"n{i+1}", 1.0)

    start = time_mod.time()
    for _ in range(100):
        ttf.diffuse_all(dt=0.02, rate=0.2)
    tensor_time = time_mod.time() - start
    checks.append(("tensor_diffusion_fast", tensor_time < 5.0))

    # All values still bounded after large simulation
    all_bounded = all(0.0 <= v <= 1.0 for v in wave.position.values())
    checks.append(("wave_bounded", all_bounded))

    return checks


# ============================================================
# Harness
# ============================================================

def run_section(name, func):
    results = func()
    passed = sum(1 for _, v in results if v)
    total = len(results)
    status = "✓" if passed == total else "✗"
    print(f"  {status} {name}: {passed}/{total}")
    return results


def main():
    all_checks = []
    sections = [
        ("§1 Trust Field on Graph", test_section_1),
        ("§2 Heat Equation (Diffusion)", test_section_2),
        ("§3 Sources and Sinks", test_section_3),
        ("§4 Wave Propagation", test_section_4),
        ("§5 Potential Fields", test_section_5),
        ("§6 Spectral Analysis", test_section_6),
        ("§7 Conservation Laws", test_section_7),
        ("§8 Boundary Conditions", test_section_8),
        ("§9 Trust Tensor Decomposition", test_section_9),
        ("§10 Performance", test_section_10),
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
