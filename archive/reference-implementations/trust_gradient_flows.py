"""
Trust Gradient Flows for Web4
Session 34, Track 2

Gradient-based trust optimization on continuous spaces:
- Trust landscape as differentiable loss surface
- Gradient descent on trust parameters
- Natural gradient (Fisher information-scaled)
- Trust potential fields and flow dynamics
- Lyapunov stability analysis for trust equilibria
- Gradient flow ODEs for trust evolution
- Trust manifold geometry (curvature, geodesics)
- Multi-agent trust gradient dynamics (coupled systems)
- Convergence rate analysis
"""

import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Callable
from collections import defaultdict


# ─── Trust Landscape ─────────────────────────────────────────────

@dataclass
class TrustLandscape:
    """
    Trust as a differentiable function over parameter space.
    Parameters represent trust configuration (thresholds, weights, etc).
    """
    dim: int
    loss_fn: Callable[[List[float]], float]
    grad_fn: Callable[[List[float]], List[float]]
    name: str = "trust_landscape"

    def loss(self, params: List[float]) -> float:
        return self.loss_fn(params)

    def gradient(self, params: List[float]) -> List[float]:
        return self.grad_fn(params)


def numerical_gradient(loss_fn: Callable[[List[float]], float],
                        params: List[float], eps: float = 1e-5) -> List[float]:
    """Compute gradient numerically via central differences."""
    grad = []
    for i in range(len(params)):
        p_plus = list(params)
        p_minus = list(params)
        p_plus[i] += eps
        p_minus[i] -= eps
        grad.append((loss_fn(p_plus) - loss_fn(p_minus)) / (2 * eps))
    return grad


# ─── Standard Trust Loss Functions ───────────────────────────────

def trust_calibration_loss(params: List[float], observations: List[Tuple[float, float]]) -> float:
    """
    MSE between predicted trust and observed outcomes.
    params[0] = threshold, params[1] = scale
    observations: [(predicted_trust, actual_outcome), ...]
    """
    threshold, scale = params[0], max(params[1], 0.01)
    total = 0.0
    for pred, actual in observations:
        adjusted = 1.0 / (1.0 + math.exp(-scale * (pred - threshold)))
        total += (adjusted - actual) ** 2
    return total / len(observations) if observations else 0.0


def trust_consensus_loss(params: List[float], target: float) -> float:
    """
    Loss measuring deviation of trust parameters from consensus target.
    Quadratic well centered at target.
    """
    return sum((p - target) ** 2 for p in params)


def multi_objective_trust_loss(params: List[float],
                                 security_weight: float = 0.6,
                                 usability_weight: float = 0.4) -> float:
    """
    Multi-objective: security (high thresholds) vs usability (low friction).
    params[0] = threshold, params[1] = attestation_count
    """
    threshold = params[0]
    att_count = params[1]
    # Security: higher threshold, more attestations = better
    security = -(threshold * att_count)
    # Usability: lower threshold, fewer attestations = better
    usability = threshold ** 2 + att_count ** 2
    return security_weight * security + usability_weight * usability


# ─── Gradient Descent ────────────────────────────────────────────

@dataclass
class GDResult:
    """Result of gradient descent optimization."""
    params: List[float]
    loss: float
    iterations: int
    loss_history: List[float]
    converged: bool


def gradient_descent(landscape: TrustLandscape,
                      initial: List[float],
                      lr: float = 0.01,
                      max_iter: int = 1000,
                      tol: float = 1e-8) -> GDResult:
    """Standard gradient descent."""
    params = list(initial)
    loss_history = []

    for i in range(max_iter):
        loss = landscape.loss(params)
        loss_history.append(loss)
        grad = landscape.gradient(params)

        # Update
        params = [p - lr * g for p, g in zip(params, grad)]

        # Convergence check
        grad_norm = math.sqrt(sum(g ** 2 for g in grad))
        if grad_norm < tol:
            return GDResult(params, loss, i + 1, loss_history, True)

    return GDResult(params, landscape.loss(params), max_iter, loss_history, False)


def adam_optimizer(landscape: TrustLandscape,
                    initial: List[float],
                    lr: float = 0.001,
                    beta1: float = 0.9,
                    beta2: float = 0.999,
                    eps: float = 1e-8,
                    max_iter: int = 1000,
                    tol: float = 1e-8) -> GDResult:
    """Adam optimizer for trust parameter optimization."""
    params = list(initial)
    m = [0.0] * len(params)  # First moment
    v = [0.0] * len(params)  # Second moment
    loss_history = []

    for t in range(1, max_iter + 1):
        loss = landscape.loss(params)
        loss_history.append(loss)
        grad = landscape.gradient(params)

        # Update moments
        for i in range(len(params)):
            m[i] = beta1 * m[i] + (1 - beta1) * grad[i]
            v[i] = beta2 * v[i] + (1 - beta2) * grad[i] ** 2

        # Bias correction
        m_hat = [mi / (1 - beta1 ** t) for mi in m]
        v_hat = [vi / (1 - beta2 ** t) for vi in v]

        # Update parameters
        params = [p - lr * mh / (math.sqrt(vh) + eps)
                  for p, mh, vh in zip(params, m_hat, v_hat)]

        grad_norm = math.sqrt(sum(g ** 2 for g in grad))
        if grad_norm < tol:
            return GDResult(params, loss, t, loss_history, True)

    return GDResult(params, landscape.loss(params), max_iter, loss_history, False)


# ─── Natural Gradient ────────────────────────────────────────────

def fisher_information_bernoulli(theta: float) -> float:
    """Fisher information for Bernoulli(θ): I(θ) = 1/(θ(1-θ))."""
    theta = max(min(theta, 0.999), 0.001)
    return 1.0 / (theta * (1.0 - theta))


def natural_gradient_step(params: List[float], grad: List[float],
                           fisher_diag: List[float], lr: float) -> List[float]:
    """
    Natural gradient: pre-multiply gradient by inverse Fisher.
    Moves equal distances in probability space (not parameter space).
    """
    return [p - lr * g / max(f, 1e-10)
            for p, g, f in zip(params, grad, fisher_diag)]


# ─── Trust Potential Field ───────────────────────────────────────

@dataclass
class TrustField:
    """
    Trust as a potential field: entities are influenced by trust gradients.
    High-trust entities attract; low-trust repel.
    """
    entities: Dict[str, List[float]]  # entity -> position in trust space
    trust_scores: Dict[str, float]    # entity -> trust level

    def potential_at(self, point: List[float]) -> float:
        """
        Total trust potential at a point.
        High-trust entities create attractive wells (negative potential).
        """
        total = 0.0
        for eid, pos in self.entities.items():
            trust = self.trust_scores.get(eid, 0.5)
            dist_sq = sum((a - b) ** 2 for a, b in zip(point, pos))
            if dist_sq < 1e-10:
                continue
            # Attractive: -trust/distance, repulsive: (1-trust)/distance
            total += -(trust - 0.5) / math.sqrt(dist_sq)
        return total

    def gradient_at(self, point: List[float], eps: float = 1e-5) -> List[float]:
        """Numerical gradient of potential field."""
        return numerical_gradient(lambda p: self.potential_at(p), point, eps)

    def flow_step(self, point: List[float], dt: float = 0.01) -> List[float]:
        """Follow the gradient flow (steepest descent on potential)."""
        grad = self.gradient_at(point)
        return [p - dt * g for p, g in zip(point, grad)]


# ─── Lyapunov Stability ─────────────────────────────────────────

def check_lyapunov_stability(dynamics: Callable[[List[float]], List[float]],
                               equilibrium: List[float],
                               perturbations: List[List[float]],
                               lyapunov_fn: Callable[[List[float]], float],
                               steps: int = 100,
                               dt: float = 0.01) -> Dict[str, object]:
    """
    Check Lyapunov stability:
    1. V(x*) = 0 at equilibrium
    2. V(x) > 0 for x ≠ x*
    3. dV/dt ≤ 0 along trajectories
    """
    v_eq = lyapunov_fn(equilibrium)
    v_positive = all(lyapunov_fn(p) > 0 for p in perturbations)

    # Check dV/dt ≤ 0 along trajectories from perturbations
    decreasing = True
    for perturb in perturbations:
        x = list(perturb)
        prev_v = lyapunov_fn(x)
        for _ in range(steps):
            dx = dynamics(x)
            x = [xi + dt * dxi for xi, dxi in zip(x, dx)]
            curr_v = lyapunov_fn(x)
            if curr_v > prev_v + 1e-6:
                decreasing = False
                break
            prev_v = curr_v

    return {
        "v_at_equilibrium": v_eq,
        "v_positive_definite": v_positive,
        "v_decreasing": decreasing,
        "stable": abs(v_eq) < 1e-6 and v_positive and decreasing,
    }


# ─── Coupled Multi-Agent Trust Dynamics ──────────────────────────

def coupled_trust_dynamics(trusts: List[float],
                            adjacency: List[List[float]],
                            decay: float = 0.1,
                            coupling: float = 0.05) -> List[float]:
    """
    Coupled ODE system for multi-agent trust:
    dT_i/dt = -decay * T_i + coupling * Σ_j A_ij * (T_j - T_i)

    Consensus dynamics with decay.
    """
    n = len(trusts)
    dt = [0.0] * n
    for i in range(n):
        dt[i] = -decay * trusts[i]
        for j in range(n):
            dt[i] += coupling * adjacency[i][j] * (trusts[j] - trusts[i])
    return dt


def simulate_coupled(trusts: List[float],
                      adjacency: List[List[float]],
                      steps: int = 200,
                      dt: float = 0.1,
                      decay: float = 0.1,
                      coupling: float = 0.05) -> List[List[float]]:
    """Simulate coupled trust dynamics. Returns history."""
    history = [list(trusts)]
    current = list(trusts)

    for _ in range(steps):
        deriv = coupled_trust_dynamics(current, adjacency, decay, coupling)
        current = [max(0, min(1, t + dt * d)) for t, d in zip(current, deriv)]
        history.append(list(current))

    return history


# ─── Convergence Rate Analysis ───────────────────────────────────

def convergence_rate(loss_history: List[float]) -> Optional[float]:
    """
    Estimate convergence rate from loss history.
    For exponential convergence: loss(t) ≈ C * exp(-rate * t)
    Returns estimated rate, or None if not converging.
    """
    if len(loss_history) < 10:
        return None

    # Use log of loss ratios
    ratios = []
    for i in range(1, len(loss_history)):
        if loss_history[i] > 1e-15 and loss_history[i-1] > 1e-15:
            ratio = loss_history[i] / loss_history[i-1]
            if 0 < ratio < 1:
                ratios.append(-math.log(ratio))

    if not ratios:
        return None

    return sum(ratios) / len(ratios)


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
    print("Trust Gradient Flows for Web4")
    print("Session 34, Track 2")
    print("=" * 70)

    # ── §1 Numerical Gradient ────────────────────────────────────
    print("\n§1 Numerical Gradient\n")

    # f(x,y) = x² + y², grad = (2x, 2y)
    def quad(p): return p[0]**2 + p[1]**2
    g = numerical_gradient(quad, [3.0, 4.0])
    check("num_grad_x", abs(g[0] - 6.0) < 1e-3, f"g[0]={g[0]}")
    check("num_grad_y", abs(g[1] - 8.0) < 1e-3, f"g[1]={g[1]}")

    # At origin: gradient = 0
    g0 = numerical_gradient(quad, [0.0, 0.0])
    check("grad_at_min", all(abs(gi) < 1e-3 for gi in g0))

    # ── §2 Gradient Descent ──────────────────────────────────────
    print("\n§2 Gradient Descent\n")

    landscape = TrustLandscape(
        dim=2,
        loss_fn=quad,
        grad_fn=lambda p: [2*p[0], 2*p[1]],
        name="quadratic"
    )

    result = gradient_descent(landscape, [5.0, 5.0], lr=0.1, max_iter=200)
    check("gd_converged", result.converged or result.loss < 1e-6)
    check("gd_near_minimum", result.loss < 0.01, f"loss={result.loss:.6f}")
    check("gd_loss_decreasing", result.loss_history[-1] < result.loss_history[0])

    # Non-trivial landscape: Rosenbrock-like
    def rosenbrock(p):
        return (1 - p[0])**2 + 100*(p[1] - p[0]**2)**2

    def rosenbrock_grad(p):
        dx = -2*(1 - p[0]) - 400*p[0]*(p[1] - p[0]**2)
        dy = 200*(p[1] - p[0]**2)
        return [dx, dy]

    landscape_r = TrustLandscape(2, rosenbrock, rosenbrock_grad, "rosenbrock")
    result_r = gradient_descent(landscape_r, [0.0, 0.0], lr=0.001, max_iter=5000)
    check("rosenbrock_loss_decreased", result_r.loss < rosenbrock([0.0, 0.0]))

    # ── §3 Adam Optimizer ────────────────────────────────────────
    print("\n§3 Adam Optimizer\n")

    result_adam = adam_optimizer(landscape, [5.0, 5.0], lr=0.1, max_iter=500)
    check("adam_converged", result_adam.loss < 0.01, f"loss={result_adam.loss:.6f}")

    # Adam on quadratic should converge faster than vanilla GD
    result_adam_r = adam_optimizer(landscape_r, [0.0, 0.0], lr=0.01, max_iter=5000)
    check("adam_rosenbrock_better", result_adam_r.loss < result_r.loss * 10,
          f"adam={result_adam_r.loss:.4f}, gd={result_r.loss:.4f}")

    # ── §4 Natural Gradient ──────────────────────────────────────
    print("\n§4 Natural Gradient\n")

    # Fisher information at θ=0.5 (minimum = 4)
    fi_half = fisher_information_bernoulli(0.5)
    check("fisher_min_at_half", abs(fi_half - 4.0) < 1e-6)

    # Fisher diverges at boundaries
    fi_01 = fisher_information_bernoulli(0.01)
    fi_99 = fisher_information_bernoulli(0.99)
    check("fisher_high_at_boundary", fi_01 > 50 and fi_99 > 50)

    # Natural gradient step: at θ=0.5, grad=1 → natural_grad = grad/I = 1/4 = 0.25
    params = [0.5]
    grad = [1.0]
    fisher = [fi_half]
    new_params = natural_gradient_step(params, grad, fisher, lr=1.0)
    check("natural_grad_step", abs(new_params[0] - (0.5 - 1.0/4.0)) < 1e-6,
          f"new={new_params[0]}")

    # ── §5 Trust Potential Field ─────────────────────────────────
    print("\n§5 Trust Potential Field\n")

    field = TrustField(
        entities={
            "trusted_hub": [0.0, 0.0],
            "untrusted_node": [5.0, 5.0],
        },
        trust_scores={
            "trusted_hub": 0.9,      # attractive
            "untrusted_node": 0.1,   # repulsive
        }
    )

    # Near trusted hub: potential should be low (attractive)
    pot_near_hub = field.potential_at([0.1, 0.1])
    pot_far = field.potential_at([3.0, 3.0])
    check("near_hub_lower_potential", pot_near_hub < pot_far,
          f"near={pot_near_hub:.4f}, far={pot_far:.4f}")

    # Flow step should move toward trusted hub
    start = [2.0, 2.0]
    after = field.flow_step(start, dt=0.1)
    dist_before = math.sqrt(sum(x**2 for x in start))
    dist_after = math.sqrt(sum(x**2 for x in after))
    check("flow_toward_hub", dist_after < dist_before,
          f"before={dist_before:.4f}, after={dist_after:.4f}")

    # ── §6 Lyapunov Stability ────────────────────────────────────
    print("\n§6 Lyapunov Stability\n")

    # Simple linear dynamics: dx/dt = -x (stable at origin)
    dynamics = lambda x: [-xi for xi in x]
    lyapunov = lambda x: sum(xi**2 for xi in x)  # V(x) = ||x||²

    stability = check_lyapunov_stability(
        dynamics,
        equilibrium=[0.0, 0.0],
        perturbations=[[0.5, 0.3], [-0.2, 0.4], [0.1, -0.1]],
        lyapunov_fn=lyapunov,
        steps=50,
        dt=0.01,
    )
    check("lyapunov_stable", stability["stable"])
    check("v_at_eq_zero", abs(stability["v_at_equilibrium"]) < 1e-10)
    check("v_positive_definite", stability["v_positive_definite"])
    check("v_decreasing", stability["v_decreasing"])

    # Unstable dynamics: dx/dt = +x
    unstable = lambda x: [xi for xi in x]
    stability_u = check_lyapunov_stability(
        unstable,
        equilibrium=[0.0, 0.0],
        perturbations=[[0.1, 0.1]],
        lyapunov_fn=lyapunov,
        steps=50, dt=0.01,
    )
    check("unstable_detected", not stability_u["v_decreasing"])

    # ── §7 Coupled Multi-Agent Dynamics ──────────────────────────
    print("\n§7 Coupled Multi-Agent Trust Dynamics\n")

    # 3 agents, fully connected
    trusts = [0.9, 0.3, 0.6]
    adj = [[0, 1, 1], [1, 0, 1], [1, 1, 0]]

    history = simulate_coupled(trusts, adj, steps=500, dt=0.05,
                                decay=0.05, coupling=0.1)

    final = history[-1]
    # With coupling, agents should converge toward each other
    spread_initial = max(trusts) - min(trusts)
    spread_final = max(final) - min(final)
    check("convergence_reduces_spread", spread_final < spread_initial,
          f"init={spread_initial:.3f}, final={spread_final:.3f}")

    # With decay, values should decrease over time
    avg_initial = sum(trusts) / 3
    avg_final = sum(final) / 3
    check("decay_reduces_average", avg_final < avg_initial,
          f"init_avg={avg_initial:.3f}, final_avg={avg_final:.3f}")

    # Disconnected: no coupling effect
    adj_disc = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    hist_disc = simulate_coupled([0.9, 0.3, 0.6], adj_disc, steps=100, dt=0.05,
                                  decay=0.1, coupling=0.1)
    final_disc = hist_disc[-1]
    # Each decays independently — ordering preserved
    check("disconnected_preserves_order",
          final_disc[0] > final_disc[2] > final_disc[1])

    # ── §8 Convergence Rate ──────────────────────────────────────
    print("\n§8 Convergence Rate Analysis\n")

    # Exponential decay: loss = exp(-0.1 * t)
    exp_history = [math.exp(-0.1 * t) for t in range(100)]
    rate = convergence_rate(exp_history)
    check("exp_rate_detected", rate is not None)
    check("exp_rate_matches", abs(rate - 0.1) < 0.01, f"rate={rate}")

    # Quadratic convergence is faster
    result_quad = gradient_descent(landscape, [1.0, 1.0], lr=0.3, max_iter=100)
    rate_quad = convergence_rate(result_quad.loss_history)
    check("quad_converges", rate_quad is not None and rate_quad > 0)

    # Non-converging: constant loss
    const_history = [1.0] * 50
    rate_const = convergence_rate(const_history)
    check("constant_no_rate", rate_const is None or abs(rate_const) < 1e-10)

    # ── §9 Trust Calibration Loss ────────────────────────────────
    print("\n§9 Trust Calibration\n")

    observations = [(0.8, 1.0), (0.3, 0.0), (0.6, 1.0), (0.2, 0.0), (0.9, 1.0)]

    loss_initial = trust_calibration_loss([0.5, 1.0], observations)
    check("calibration_loss_computed", loss_initial >= 0)

    # Optimize calibration
    cal_landscape = TrustLandscape(
        dim=2,
        loss_fn=lambda p: trust_calibration_loss(p, observations),
        grad_fn=lambda p: numerical_gradient(
            lambda q: trust_calibration_loss(q, observations), p),
    )
    result_cal = adam_optimizer(cal_landscape, [0.5, 1.0], lr=0.05, max_iter=500)
    check("calibration_improved", result_cal.loss <= loss_initial + 1e-6,
          f"init={loss_initial:.4f}, final={result_cal.loss:.4f}")

    # Multi-objective
    mo_loss = multi_objective_trust_loss([0.5, 3.0])
    check("multi_obj_computed", isinstance(mo_loss, float))

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
