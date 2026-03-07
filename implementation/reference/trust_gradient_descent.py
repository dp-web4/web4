"""
Trust Gradient Descent for Web4
Session 31, Track 4

Optimization of trust parameters using gradient methods:
- Trust score optimization (find optimal trust allocation)
- Policy threshold optimization (minimize false positives/negatives)
- Learning rate schedules for trust updates
- Momentum-based trust convergence
- Adam optimizer for multi-dimensional trust
- Constraint satisfaction (bounded optimization)
- Convergence analysis and stopping criteria
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Callable, Optional


# ─── Objective Functions ───────────────────────────────────────────

def trust_loss_function(trust_scores: List[float],
                         target_scores: List[float]) -> float:
    """MSE loss between current and target trust scores."""
    if len(trust_scores) != len(target_scores):
        return float('inf')
    n = len(trust_scores)
    if n == 0:
        return 0.0
    return sum((a - b) ** 2 for a, b in zip(trust_scores, target_scores)) / n


def policy_loss_function(threshold: float, trust_scores: List[float],
                          labels: List[bool]) -> float:
    """
    Classification loss: how well does threshold separate trusted from untrusted?
    labels[i] = True means entity i should be trusted.
    """
    if not trust_scores:
        return 0.0

    errors = 0
    for trust, label in zip(trust_scores, labels):
        predicted = trust >= threshold
        if predicted != label:
            errors += 1

    return errors / len(trust_scores)


def regularized_trust_loss(trust_scores: List[float],
                            target_scores: List[float],
                            lambda_reg: float = 0.01) -> float:
    """MSE + L2 regularization (penalize extreme trust values)."""
    mse = trust_loss_function(trust_scores, target_scores)
    # Regularize away from boundaries (0 and 1)
    reg = sum((t - 0.5) ** 2 for t in trust_scores) * lambda_reg
    return mse + reg


# ─── Gradient Computation ─────────────────────────────────────────

def numerical_gradient(f: Callable, params: List[float],
                        epsilon: float = 0.001) -> List[float]:
    """Compute gradient numerically (finite differences)."""
    grad = []
    for i in range(len(params)):
        params_plus = list(params)
        params_minus = list(params)
        params_plus[i] += epsilon
        params_minus[i] -= epsilon
        grad.append((f(params_plus) - f(params_minus)) / (2 * epsilon))
    return grad


def trust_mse_gradient(trust_scores: List[float],
                        target_scores: List[float]) -> List[float]:
    """Analytical gradient of MSE loss."""
    n = len(trust_scores)
    if n == 0:
        return []
    return [2 * (t - tgt) / n for t, tgt in zip(trust_scores, target_scores)]


# ─── Gradient Descent ──────────────────────────────────────────────

@dataclass
class GDResult:
    params: List[float]
    loss: float
    iterations: int
    loss_history: List[float]
    converged: bool


def gradient_descent(f: Callable, initial: List[float],
                      grad_f: Callable = None,
                      lr: float = 0.1, max_iter: int = 200,
                      tolerance: float = 1e-6,
                      bounds: Tuple[float, float] = (0.0, 1.0)) -> GDResult:
    """
    Gradient descent with projection to [0, 1] bounds.
    """
    params = list(initial)
    loss_history = []

    for iteration in range(max_iter):
        loss = f(params)
        loss_history.append(loss)

        if loss < tolerance:
            return GDResult(params, loss, iteration + 1, loss_history, True)

        # Compute gradient
        if grad_f:
            grad = grad_f(params)
        else:
            grad = numerical_gradient(f, params)

        # Update with projection
        for i in range(len(params)):
            params[i] -= lr * grad[i]
            params[i] = max(bounds[0], min(bounds[1], params[i]))

        # Check convergence
        if len(loss_history) > 1 and abs(loss_history[-1] - loss_history[-2]) < tolerance:
            return GDResult(params, f(params), iteration + 1, loss_history, True)

    return GDResult(params, f(params), max_iter, loss_history, False)


# ─── Learning Rate Schedules ──────────────────────────────────────

def constant_lr(base_lr: float, iteration: int) -> float:
    return base_lr


def step_decay_lr(base_lr: float, iteration: int,
                   drop_factor: float = 0.5, drop_every: int = 50) -> float:
    """Step decay: halve LR every drop_every iterations."""
    return base_lr * (drop_factor ** (iteration // drop_every))


def exponential_decay_lr(base_lr: float, iteration: int,
                          decay_rate: float = 0.01) -> float:
    """Exponential decay: lr = base * e^(-rate * iter)."""
    return base_lr * math.exp(-decay_rate * iteration)


def cosine_annealing_lr(base_lr: float, iteration: int,
                         max_iter: int = 200) -> float:
    """Cosine annealing: smooth decrease to 0."""
    return base_lr * (1 + math.cos(math.pi * iteration / max_iter)) / 2


# ─── Momentum ─────────────────────────────────────────────────────

def gradient_descent_momentum(f: Callable, initial: List[float],
                                lr: float = 0.1, momentum: float = 0.9,
                                max_iter: int = 200,
                                tolerance: float = 1e-6) -> GDResult:
    """GD with momentum for faster convergence."""
    params = list(initial)
    velocity = [0.0] * len(params)
    loss_history = []

    for iteration in range(max_iter):
        loss = f(params)
        loss_history.append(loss)

        if loss < tolerance:
            return GDResult(params, loss, iteration + 1, loss_history, True)

        grad = numerical_gradient(f, params)

        for i in range(len(params)):
            velocity[i] = momentum * velocity[i] - lr * grad[i]
            params[i] += velocity[i]
            params[i] = max(0.0, min(1.0, params[i]))

        if len(loss_history) > 1 and abs(loss_history[-1] - loss_history[-2]) < tolerance:
            return GDResult(params, f(params), iteration + 1, loss_history, True)

    return GDResult(params, f(params), max_iter, loss_history, False)


# ─── Adam Optimizer ────────────────────────────────────────────────

def adam_optimizer(f: Callable, initial: List[float],
                    lr: float = 0.01, beta1: float = 0.9,
                    beta2: float = 0.999, epsilon: float = 1e-8,
                    max_iter: int = 200,
                    tolerance: float = 1e-6) -> GDResult:
    """
    Adam optimizer: adaptive learning rates per parameter.
    Good for multi-dimensional trust optimization.
    """
    params = list(initial)
    m = [0.0] * len(params)  # first moment
    v = [0.0] * len(params)  # second moment
    loss_history = []

    for t in range(1, max_iter + 1):
        loss = f(params)
        loss_history.append(loss)

        if loss < tolerance:
            return GDResult(params, loss, t, loss_history, True)

        grad = numerical_gradient(f, params)

        for i in range(len(params)):
            m[i] = beta1 * m[i] + (1 - beta1) * grad[i]
            v[i] = beta2 * v[i] + (1 - beta2) * grad[i] ** 2

            # Bias correction
            m_hat = m[i] / (1 - beta1 ** t)
            v_hat = v[i] / (1 - beta2 ** t)

            params[i] -= lr * m_hat / (math.sqrt(v_hat) + epsilon)
            params[i] = max(0.0, min(1.0, params[i]))

        if len(loss_history) > 1 and abs(loss_history[-1] - loss_history[-2]) < tolerance:
            return GDResult(params, f(params), t, loss_history, True)

    return GDResult(params, f(params), max_iter, loss_history, False)


# ─── Multi-Objective Trust Optimization ───────────────────────────

def pareto_dominates(obj_a: List[float], obj_b: List[float]) -> bool:
    """Does solution A Pareto-dominate solution B?"""
    at_least_one_better = False
    for a, b in zip(obj_a, obj_b):
        if a > b:  # worse (minimization)
            return False
        if a < b:
            at_least_one_better = True
    return at_least_one_better


def find_pareto_front(solutions: List[Tuple[List[float], List[float]]]) -> List[int]:
    """
    Find Pareto-optimal solutions from (params, objectives) pairs.
    Returns indices of non-dominated solutions.
    """
    n = len(solutions)
    dominated = [False] * n

    for i in range(n):
        if dominated[i]:
            continue
        for j in range(n):
            if i == j or dominated[j]:
                continue
            if pareto_dominates(solutions[j][1], solutions[i][1]):
                dominated[i] = True
                break

    return [i for i in range(n) if not dominated[i]]


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
    print("Trust Gradient Descent for Web4")
    print("Session 31, Track 4")
    print("=" * 70)

    # ── §1 Loss Functions ─────────────────────────────────────────
    print("\n§1 Loss Functions\n")

    # Perfect match → zero loss
    loss_zero = trust_loss_function([0.5, 0.7, 0.3], [0.5, 0.7, 0.3])
    check("perfect_zero_loss", abs(loss_zero) < 0.001)

    # Some error
    loss_some = trust_loss_function([0.5, 0.7, 0.3], [0.6, 0.8, 0.4])
    check("error_positive_loss", loss_some > 0)

    # Policy loss
    scores = [0.2, 0.4, 0.6, 0.8]
    labels = [False, False, True, True]
    loss_good = policy_loss_function(0.5, scores, labels)
    check("good_threshold_low_loss", loss_good == 0.0,
          f"loss={loss_good}")

    loss_bad = policy_loss_function(0.1, scores, labels)
    check("bad_threshold_high_loss", loss_bad > 0)

    # ── §2 Gradient Computation ───────────────────────────────────
    print("\n§2 Gradient Computation\n")

    target = [0.7, 0.5, 0.8]
    current = [0.3, 0.3, 0.3]

    # Analytical gradient
    grad_analytical = trust_mse_gradient(current, target)
    check("gradient_negative_toward_target",
          all(g < 0 for g in grad_analytical),  # all should point toward target (higher)
          f"grad={[f'{g:.3f}' for g in grad_analytical]}")

    # Numerical gradient should match analytical
    f = lambda x: trust_loss_function(x, target)
    grad_numerical = numerical_gradient(f, current)
    check("numerical_matches_analytical",
          all(abs(a - n) < 0.01 for a, n in zip(grad_analytical, grad_numerical)),
          f"analytical={[f'{g:.3f}' for g in grad_analytical]} numerical={[f'{g:.3f}' for g in grad_numerical]}")

    # ── §3 Basic Gradient Descent ─────────────────────────────────
    print("\n§3 Gradient Descent Optimization\n")

    target = [0.7, 0.5, 0.8]
    f = lambda x: trust_loss_function(x, target)
    grad_f = lambda x: trust_mse_gradient(x, target)

    result = gradient_descent(f, [0.3, 0.3, 0.3], grad_f=grad_f,
                               lr=0.5, max_iter=200)
    check("gd_converges", result.converged, f"iters={result.iterations}")
    check("gd_low_loss", result.loss < 0.01,
          f"loss={result.loss:.6f}")
    check("gd_near_target",
          all(abs(p - t) < 0.05 for p, t in zip(result.params, target)),
          f"params={[f'{p:.3f}' for p in result.params]}")

    # Loss decreases monotonically (mostly)
    decreasing = sum(1 for i in range(len(result.loss_history) - 1)
                     if result.loss_history[i] >= result.loss_history[i + 1] - 0.001)
    check("loss_mostly_decreasing",
          decreasing > len(result.loss_history) * 0.8)

    # ── §4 Learning Rate Schedules ────────────────────────────────
    print("\n§4 Learning Rate Schedules\n")

    lr_const = [constant_lr(0.1, i) for i in range(100)]
    check("constant_lr", all(lr == 0.1 for lr in lr_const))

    lr_step = [step_decay_lr(0.1, i, drop_every=25) for i in range(100)]
    check("step_decay_decreasing", lr_step[0] > lr_step[50],
          f"t0={lr_step[0]} t50={lr_step[50]}")

    lr_exp = [exponential_decay_lr(0.1, i) for i in range(100)]
    check("exp_decay_monotone",
          all(lr_exp[i] >= lr_exp[i + 1] for i in range(99)))

    lr_cos = [cosine_annealing_lr(0.1, i, 100) for i in range(100)]
    check("cosine_starts_high", abs(lr_cos[0] - 0.1) < 0.01)
    check("cosine_ends_low", lr_cos[-1] < 0.01)

    # ── §5 Momentum ──────────────────────────────────────────────
    print("\n§5 Gradient Descent with Momentum\n")

    target = [0.6, 0.4, 0.7, 0.5]
    f = lambda x: trust_loss_function(x, target)

    result_no_mom = gradient_descent(f, [0.1, 0.1, 0.1, 0.1],
                                      lr=0.3, max_iter=200)
    result_mom = gradient_descent_momentum(f, [0.1, 0.1, 0.1, 0.1],
                                            lr=0.3, momentum=0.9, max_iter=200)

    check("momentum_converges", result_mom.converged)
    check("momentum_low_loss", result_mom.loss < 0.01,
          f"loss={result_mom.loss:.6f}")

    # Both converge to similar quality (momentum may take more iterations
    # on simple convex problems due to overshooting)
    check("momentum_similar_quality",
          abs(result_mom.loss - result_no_mom.loss) < 0.01,
          f"mom_loss={result_mom.loss:.6f} no_mom_loss={result_no_mom.loss:.6f}")

    # ── §6 Adam Optimizer ─────────────────────────────────────────
    print("\n§6 Adam Optimizer\n")

    target = [0.8, 0.3, 0.6, 0.9, 0.5]
    f = lambda x: trust_loss_function(x, target)

    result_adam = adam_optimizer(f, [0.5] * 5, lr=0.05, max_iter=500)
    check("adam_converges", result_adam.converged,
          f"iters={result_adam.iterations}")
    check("adam_low_loss", result_adam.loss < 0.01,
          f"loss={result_adam.loss:.6f}")
    check("adam_near_target",
          all(abs(p - t) < 0.1 for p, t in zip(result_adam.params, target)),
          f"params={[f'{p:.2f}' for p in result_adam.params]}")

    # ── §7 Bounded Optimization ───────────────────────────────────
    print("\n§7 Constraint Satisfaction\n")

    # Target outside bounds should clamp
    target_extreme = [1.5, -0.5, 0.5]
    f = lambda x: trust_loss_function(x, target_extreme)
    result_bounded = gradient_descent(f, [0.5, 0.5, 0.5], lr=0.3,
                                       max_iter=200, bounds=(0.0, 1.0))

    check("bounded_params", all(0 <= p <= 1 for p in result_bounded.params),
          f"params={result_bounded.params}")

    # Should reach bounds (1.0 and 0.0) for extreme targets
    check("reaches_upper_bound", result_bounded.params[0] > 0.9,
          f"p0={result_bounded.params[0]:.3f}")
    check("reaches_lower_bound", result_bounded.params[1] < 0.1,
          f"p1={result_bounded.params[1]:.3f}")

    # ── §8 Policy Threshold Optimization ──────────────────────────
    print("\n§8 Policy Threshold Optimization\n")

    # Synthetic data: entities with known trustworthiness
    rng = random.Random(42)
    trust_scores = [rng.uniform(0, 1) for _ in range(50)]
    labels = [t > 0.5 for t in trust_scores]  # true threshold is 0.5

    # Use smooth surrogate loss (logistic) instead of discrete 0/1
    def smooth_policy_loss(x):
        threshold = x[0]
        loss = 0.0
        for t, label in zip(trust_scores, labels):
            diff = (t - threshold) * (1 if label else -1)
            # Logistic loss: log(1 + exp(-diff * scale))
            scaled = diff * 20  # steepness
            loss += math.log(1 + math.exp(-scaled)) if scaled > -20 else -scaled
        return loss / len(trust_scores)

    result_policy = gradient_descent(smooth_policy_loss, [0.3], lr=0.01, max_iter=500)

    check("policy_converges", result_policy.converged,
          f"iters={result_policy.iterations}")
    check("policy_near_true_threshold",
          abs(result_policy.params[0] - 0.5) < 0.15,
          f"threshold={result_policy.params[0]:.3f}")

    # ── §9 Pareto Front ──────────────────────────────────────────
    print("\n§9 Multi-Objective Pareto Front\n")

    # Params → (security_loss, usability_loss)
    solutions = [
        ([0.9], [0.1, 0.8]),   # high security, low usability
        ([0.5], [0.4, 0.4]),   # balanced
        ([0.1], [0.8, 0.1]),   # low security, high usability
        ([0.7], [0.2, 0.5]),   # good security, moderate usability
        ([0.3], [0.6, 0.3]),   # moderate security, good usability
        ([0.6], [0.5, 0.5]),   # dominated by [0.5] solution
    ]

    pareto_indices = find_pareto_front(solutions)
    check("pareto_found", len(pareto_indices) > 0)

    # Pareto front should include extremes
    check("pareto_includes_extremes",
          0 in pareto_indices and 2 in pareto_indices,
          f"indices={pareto_indices}")

    # Dominated solution excluded
    check("dominated_excluded", 5 not in pareto_indices,
          f"indices={pareto_indices}")

    # ── §10 Convergence Analysis ──────────────────────────────────
    print("\n§10 Convergence Analysis\n")

    # Different optimizers on same problem
    target = [0.7, 0.3, 0.8]
    f = lambda x: trust_loss_function(x, target)

    r_gd = gradient_descent(f, [0.5, 0.5, 0.5], lr=0.3, max_iter=300)
    r_mom = gradient_descent_momentum(f, [0.5, 0.5, 0.5], lr=0.3, momentum=0.9, max_iter=300)
    r_adam = adam_optimizer(f, [0.5, 0.5, 0.5], lr=0.05, max_iter=300)

    # All should converge
    check("all_converge",
          r_gd.converged and r_mom.converged and r_adam.converged,
          f"gd={r_gd.converged} mom={r_mom.converged} adam={r_adam.converged}")

    # All should achieve low loss
    check("all_low_loss",
          r_gd.loss < 0.01 and r_mom.loss < 0.01 and r_adam.loss < 0.01,
          f"gd={r_gd.loss:.6f} mom={r_mom.loss:.6f} adam={r_adam.loss:.6f}")

    # Final params should be similar
    for i in range(3):
        check(f"param_{i}_agreement",
              max(r_gd.params[i], r_mom.params[i], r_adam.params[i]) -
              min(r_gd.params[i], r_mom.params[i], r_adam.params[i]) < 0.1,
              f"gd={r_gd.params[i]:.3f} mom={r_mom.params[i]:.3f} adam={r_adam.params[i]:.3f}")

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
