"""
Trust Information Geometry for Web4
Session 32, Track 2

Trust distributions live on statistical manifolds. Information geometry
provides the natural metric for comparing trust states.

- KL divergence between trust distributions
- Fisher information matrix for trust parameters
- Rényi divergence (generalized)
- Jensen-Shannon divergence (symmetric, bounded)
- Hellinger distance
- Wasserstein distance (earth mover's)
- Natural gradient for trust optimization
- Information-theoretic trust capacity
"""

import math
import random
from typing import List, Tuple, Dict


# ─── Divergence Measures ──────────────────────────────────────────

def kl_divergence(p: List[float], q: List[float], eps: float = 1e-15) -> float:
    """
    KL(P || Q): information lost when Q approximates P.
    Asymmetric. Not a true metric.
    """
    total = 0.0
    for pi, qi in zip(p, q):
        pi = max(eps, pi)
        qi = max(eps, qi)
        total += pi * math.log(pi / qi)
    return total


def js_divergence(p: List[float], q: List[float]) -> float:
    """
    Jensen-Shannon divergence: symmetric, bounded, sqrt is a metric.
    JSD(P, Q) = 0.5 * KL(P || M) + 0.5 * KL(Q || M), M = (P+Q)/2.
    Range [0, ln(2)].
    """
    m = [(pi + qi) / 2 for pi, qi in zip(p, q)]
    return 0.5 * kl_divergence(p, m) + 0.5 * kl_divergence(q, m)


def renyi_divergence(p: List[float], q: List[float],
                     alpha: float = 2.0, eps: float = 1e-15) -> float:
    """
    Rényi divergence of order α.
    α → 1: KL divergence. α = 2: chi-squared-like. α → ∞: max divergence.
    """
    if abs(alpha - 1.0) < 1e-10:
        return kl_divergence(p, q, eps)

    total = 0.0
    for pi, qi in zip(p, q):
        pi = max(eps, pi)
        qi = max(eps, qi)
        total += pi ** alpha * qi ** (1 - alpha)

    if total <= 0:
        return float('inf')

    return math.log(total) / (alpha - 1)


def hellinger_distance(p: List[float], q: List[float]) -> float:
    """
    Hellinger distance: symmetric, bounded [0, 1], true metric.
    Related to Bhattacharyya coefficient.
    """
    total = sum((math.sqrt(max(0, pi)) - math.sqrt(max(0, qi))) ** 2
                for pi, qi in zip(p, q))
    return math.sqrt(total / 2)


def wasserstein_1d(p: List[float], q: List[float]) -> float:
    """
    1D Wasserstein (earth mover's) distance for discrete distributions.
    Minimum cost to transform P into Q.
    """
    # Cumulative distributions
    cp = []
    cq = []
    running_p, running_q = 0.0, 0.0
    for pi, qi in zip(p, q):
        running_p += pi
        running_q += qi
        cp.append(running_p)
        cq.append(running_q)

    # L1 distance between CDFs
    return sum(abs(cpi - cqi) for cpi, cqi in zip(cp, cq)) / len(p)


# ─── Fisher Information ──────────────────────────────────────────

def fisher_information_bernoulli(theta: float, eps: float = 1e-10) -> float:
    """
    Fisher information for Bernoulli(θ) = 1 / (θ(1-θ)).
    Measures how much trust score uncertainty changes with small perturbation.
    High near 0 and 1 (extreme trust scores are sensitive).
    """
    theta = max(eps, min(1 - eps, theta))
    return 1.0 / (theta * (1 - theta))


def fisher_information_beta(alpha: float, beta_param: float) -> float:
    """
    Fisher information for Beta(α, β) distribution.
    Used for trust estimation from attestations (Beta-Bernoulli model).
    Returns scalar (diagonal element for α).
    """
    from math import lgamma

    def trigamma(x: float) -> float:
        """Approximate trigamma function ψ'(x)."""
        result = 0.0
        # Shift to large x
        while x < 10:
            result += 1.0 / (x * x)
            x += 1
        # Asymptotic expansion
        result += 1.0 / x + 1.0 / (2 * x * x) + 1.0 / (6 * x ** 3)
        return result

    return trigamma(alpha) - trigamma(alpha + beta_param)


def trust_sensitivity(trust_scores: List[float]) -> List[float]:
    """
    Compute Fisher information for each trust score.
    Indicates which scores are most sensitive to perturbation.
    """
    return [fisher_information_bernoulli(t) for t in trust_scores]


# ─── Natural Gradient ─────────────────────────────────────────────

def natural_gradient_step(theta: float, grad: float,
                          lr: float = 0.01) -> float:
    """
    Natural gradient: multiply gradient by inverse Fisher information.
    Gives equal-speed movement in probability space regardless of parameterization.
    """
    fisher = fisher_information_bernoulli(theta)
    if fisher > 0:
        natural_grad = grad / fisher
    else:
        natural_grad = grad

    new_theta = theta - lr * natural_grad
    return max(0.001, min(0.999, new_theta))


# ─── Trust Distribution Comparison ────────────────────────────────

def trust_distribution_from_scores(scores: List[float],
                                    n_bins: int = 10) -> List[float]:
    """Convert trust scores to probability distribution over bins."""
    dist = [0.0] * n_bins
    for s in scores:
        bin_idx = min(int(s * n_bins), n_bins - 1)
        dist[bin_idx] += 1

    total = sum(dist)
    if total > 0:
        dist = [d / total for d in dist]
    else:
        dist = [1.0 / n_bins] * n_bins

    return dist


def mutual_information(joint: List[List[float]],
                       eps: float = 1e-15) -> float:
    """
    Mutual information I(X;Y) from joint distribution.
    Measures how much knowing X tells you about Y (and vice versa).
    """
    rows = len(joint)
    cols = len(joint[0]) if joint else 0

    # Marginals
    px = [sum(joint[i]) for i in range(rows)]
    py = [sum(joint[i][j] for i in range(rows)) for j in range(cols)]

    mi = 0.0
    for i in range(rows):
        for j in range(cols):
            pij = max(eps, joint[i][j])
            pxi = max(eps, px[i])
            pyj = max(eps, py[j])
            if pij > eps:
                mi += pij * math.log(pij / (pxi * pyj))

    return max(0.0, mi)


def channel_capacity_binary(error_rate: float) -> float:
    """
    Binary symmetric channel capacity.
    C = 1 - H(error_rate).
    For trust: how much info each attestation conveys.
    """
    if error_rate <= 0 or error_rate >= 1:
        return 0.0 if error_rate == 0.5 else 1.0

    h = -error_rate * math.log2(error_rate) - (1 - error_rate) * math.log2(1 - error_rate)
    return max(0.0, 1.0 - h)


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
    print("Trust Information Geometry for Web4")
    print("Session 32, Track 2")
    print("=" * 70)

    random.seed(42)

    # ── §1 KL Divergence ────────────────────────────────────────
    print("\n§1 KL Divergence\n")

    # Same distribution: KL = 0
    p = [0.2, 0.3, 0.5]
    check("kl_same_zero", abs(kl_divergence(p, p)) < 1e-10)

    # KL is non-negative (Gibbs' inequality)
    q = [0.1, 0.4, 0.5]
    check("kl_nonnegative", kl_divergence(p, q) >= 0)

    # KL is asymmetric
    kl_pq = kl_divergence(p, q)
    kl_qp = kl_divergence(q, p)
    check("kl_asymmetric", abs(kl_pq - kl_qp) > 0.001,
          f"KL(p||q)={kl_pq:.4f} KL(q||p)={kl_qp:.4f}")

    # ── §2 Jensen-Shannon Divergence ────────────────────────────
    print("\n§2 Jensen-Shannon Divergence\n")

    jsd = js_divergence(p, q)
    check("jsd_nonneg", jsd >= 0)
    check("jsd_bounded", jsd <= math.log(2) + 1e-10,
          f"jsd={jsd:.4f} bound={math.log(2):.4f}")

    # JSD is symmetric
    jsd_qp = js_divergence(q, p)
    check("jsd_symmetric", abs(jsd - jsd_qp) < 1e-10)

    # JSD = 0 for identical distributions
    check("jsd_same_zero", abs(js_divergence(p, p)) < 1e-10)

    # ── §3 Hellinger & Wasserstein ──────────────────────────────
    print("\n§3 Hellinger & Wasserstein Distances\n")

    hd = hellinger_distance(p, q)
    check("hellinger_bounded", 0 <= hd <= 1,
          f"hd={hd:.4f}")
    check("hellinger_same_zero", hellinger_distance(p, p) < 1e-10)

    # Hellinger is symmetric
    check("hellinger_symmetric",
          abs(hellinger_distance(p, q) - hellinger_distance(q, p)) < 1e-10)

    # Wasserstein
    wd = wasserstein_1d(p, q)
    check("wasserstein_nonneg", wd >= 0)
    check("wasserstein_same_zero", wasserstein_1d(p, p) < 1e-10)

    # ── §4 Rényi Divergence ─────────────────────────────────────
    print("\n§4 Rényi Divergence\n")

    # α → 1 should approximate KL
    renyi_near1 = renyi_divergence(p, q, alpha=1.001)
    kl_val = kl_divergence(p, q)
    check("renyi_near1_approx_kl", abs(renyi_near1 - kl_val) < 0.01,
          f"renyi={renyi_near1:.4f} kl={kl_val:.4f}")

    # α = 2 gives different value
    renyi_2 = renyi_divergence(p, q, alpha=2.0)
    check("renyi_2_positive", renyi_2 > 0,
          f"renyi_2={renyi_2:.4f}")

    # ── §5 Fisher Information ───────────────────────────────────
    print("\n§5 Fisher Information\n")

    # Fisher highest near boundaries (0 and 1)
    fi_05 = fisher_information_bernoulli(0.5)
    fi_01 = fisher_information_bernoulli(0.1)
    fi_09 = fisher_information_bernoulli(0.9)
    check("fisher_boundary_higher", fi_01 > fi_05 and fi_09 > fi_05,
          f"fi(0.1)={fi_01:.2f} fi(0.5)={fi_05:.2f} fi(0.9)={fi_09:.2f}")

    # Fisher at 0.5 is minimal: I(0.5) = 4
    check("fisher_min_at_half", abs(fi_05 - 4.0) < 0.01)

    # Sensitivity analysis
    scores = [0.1, 0.3, 0.5, 0.7, 0.9]
    sens = trust_sensitivity(scores)
    # Extreme scores more sensitive
    check("extreme_more_sensitive", sens[0] > sens[2] and sens[4] > sens[2])

    # ── §6 Natural Gradient ─────────────────────────────────────
    print("\n§6 Natural Gradient\n")

    # Natural gradient moves faster near 0.5 (low Fisher)
    # and slower near boundaries (high Fisher)
    grad = 0.1
    step_05 = abs(natural_gradient_step(0.5, grad) - 0.5)
    step_01 = abs(natural_gradient_step(0.1, grad) - 0.1)

    check("natural_grad_equalization", step_05 > step_01,
          f"step@0.5={step_05:.6f} step@0.1={step_01:.6f}")

    # ── §7 Trust Distribution Comparison ────────────────────────
    print("\n§7 Trust Distribution Comparison\n")

    # Two federations with different trust profiles
    fed_a_scores = [random.betavariate(5, 2) for _ in range(100)]  # High trust
    fed_b_scores = [random.betavariate(2, 5) for _ in range(100)]  # Low trust
    fed_c_scores = [random.betavariate(5, 2) for _ in range(100)]  # Similar to A

    dist_a = trust_distribution_from_scores(fed_a_scores)
    dist_b = trust_distribution_from_scores(fed_b_scores)
    dist_c = trust_distribution_from_scores(fed_c_scores)

    # A vs B should be more different than A vs C
    jsd_ab = js_divergence(dist_a, dist_b)
    jsd_ac = js_divergence(dist_a, dist_c)
    check("similar_feds_closer", jsd_ac < jsd_ab,
          f"jsd(A,B)={jsd_ab:.4f} jsd(A,C)={jsd_ac:.4f}")

    # ── §8 Mutual Information ───────────────────────────────────
    print("\n§8 Mutual Information & Channel Capacity\n")

    # Independent: MI = 0
    independent = [
        [0.25, 0.25],
        [0.25, 0.25],
    ]
    mi_indep = mutual_information(independent)
    check("mi_independent_zero", mi_indep < 0.01,
          f"mi={mi_indep:.6f}")

    # Perfectly correlated: MI = H(X)
    correlated = [
        [0.5, 0.0],
        [0.0, 0.5],
    ]
    mi_corr = mutual_information(correlated)
    check("mi_correlated_positive", mi_corr > 0.5,
          f"mi={mi_corr:.4f}")

    # Channel capacity
    cap_perfect = channel_capacity_binary(0.0)
    cap_useless = channel_capacity_binary(0.5)
    cap_good = channel_capacity_binary(0.1)
    check("capacity_perfect", abs(cap_perfect - 1.0) < 0.01)
    check("capacity_useless", abs(cap_useless) < 0.01)
    check("capacity_good_intermediate", 0 < cap_good < 1,
          f"cap={cap_good:.4f}")

    # Trust attestation capacity at 0.3 error rate
    cap_trust = channel_capacity_binary(0.3)
    check("trust_attestation_capacity", cap_trust > 0,
          f"cap={cap_trust:.4f} bits/attestation")

    # ── Summary ─────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
