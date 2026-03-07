#!/usr/bin/env python3
"""
Trust Aggregation Function Semantics — Session 28, Track 8
============================================================

Formal analysis of HOW per-dimension T3 scores combine into composite trust.
Currently 3+ aggregation functions exist in the codebase with no principled
selection criteria. This track:

  1. Defines 5 aggregation functions with formal properties
  2. Proves which properties each function satisfies
  3. Provides decision criteria for choosing the right function
  4. Analyzes sensitivity (how small changes in inputs affect output)
  5. Handles heterogeneous aggregation (cross-federation reconciliation)
  6. Tests robustness to adversarial manipulation

Aggregation functions:
  - Weighted arithmetic mean (WAM): most common, linear
  - Geometric mean (GM): penalizes any low dimension
  - Harmonic mean (HM): heavily penalizes low dimensions
  - Min-based (MIN): most conservative — weakest link
  - Weighted power mean (WPM): generalizes all above via parameter p

~45 checks expected.
"""

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Callable, Optional

passed = 0
failed = 0
errors = []


def check(condition, msg):
    global passed, failed, errors
    if condition:
        passed += 1
    else:
        failed += 1
        errors.append(msg)
        print(f"  FAIL: {msg}")


# ============================================================
# §1 — Aggregation Functions
# ============================================================

def weighted_arithmetic_mean(scores: Dict[str, float],
                              weights: Dict[str, float]) -> float:
    """WAM: sum(w_i * s_i) / sum(w_i). Linear, most common."""
    total_weight = sum(weights.get(d, 1.0) for d in scores)
    if total_weight == 0:
        return 0.0
    return sum(scores[d] * weights.get(d, 1.0) for d in scores) / total_weight


def geometric_mean(scores: Dict[str, float],
                   weights: Dict[str, float]) -> float:
    """GM: prod(s_i^w_i)^(1/sum(w_i)). Penalizes any low dimension."""
    if not scores:
        return 0.0
    total_weight = sum(weights.get(d, 1.0) for d in scores)
    if total_weight == 0:
        return 0.0
    log_sum = 0.0
    for d, s in scores.items():
        if s <= 0:
            return 0.0  # GM is 0 if any score is 0
        w = weights.get(d, 1.0)
        log_sum += w * math.log(s)
    return math.exp(log_sum / total_weight)


def harmonic_mean(scores: Dict[str, float],
                  weights: Dict[str, float]) -> float:
    """HM: sum(w_i) / sum(w_i/s_i). Heavily penalizes low dimensions."""
    if not scores:
        return 0.0
    total_weight = sum(weights.get(d, 1.0) for d in scores)
    inv_sum = 0.0
    for d, s in scores.items():
        if s <= 0:
            return 0.0
        w = weights.get(d, 1.0)
        inv_sum += w / s
    if inv_sum == 0:
        return 0.0
    return total_weight / inv_sum


def min_aggregation(scores: Dict[str, float],
                    weights: Dict[str, float]) -> float:
    """MIN: min(s_i). Most conservative — weakest link decides."""
    if not scores:
        return 0.0
    return min(scores.values())


def weighted_power_mean(scores: Dict[str, float],
                        weights: Dict[str, float],
                        p: float = 1.0) -> float:
    """WPM: (sum(w_i * s_i^p) / sum(w_i))^(1/p).

    Generalizes:
      p = -inf: min
      p = -1: harmonic mean
      p → 0: geometric mean (via limit)
      p = 1: arithmetic mean
      p = +inf: max
    """
    if not scores or p == 0:
        return geometric_mean(scores, weights)

    total_weight = sum(weights.get(d, 1.0) for d in scores)
    if total_weight == 0:
        return 0.0

    power_sum = 0.0
    for d, s in scores.items():
        if s <= 0 and p < 0:
            return 0.0
        w = weights.get(d, 1.0)
        power_sum += w * (s ** p)

    result = (power_sum / total_weight) ** (1.0 / p)
    return max(0.0, min(1.0, result))


# ============================================================
# §2 — Formal Properties
# ============================================================

@dataclass
class AggregationProperty:
    """A formal property an aggregation function may satisfy."""
    name: str
    description: str

    def check(self, agg_fn: Callable, n_tests: int = 100) -> bool:
        """Test if a function satisfies this property empirically."""
        raise NotImplementedError


class MonotonicityProperty(AggregationProperty):
    """Increasing any input should not decrease the output."""

    def __init__(self):
        super().__init__("monotonicity", "Increasing input → non-decreasing output")

    def check(self, agg_fn, n_tests=100):
        rng = random.Random(42)
        for _ in range(n_tests):
            n_dims = rng.randint(2, 5)
            dims = [f"d{i}" for i in range(n_dims)]
            scores = {d: rng.random() for d in dims}
            weights = {d: rng.random() + 0.1 for d in dims}
            base = agg_fn(scores, weights)

            # Increase one dimension
            dim = rng.choice(dims)
            increased = dict(scores)
            increased[dim] = min(1.0, scores[dim] + 0.1)
            result = agg_fn(increased, weights)

            if result < base - 1e-9:
                return False
        return True


class BoundednessProperty(AggregationProperty):
    """Output is bounded by min and max of inputs."""

    def __init__(self):
        super().__init__("boundedness", "min(inputs) ≤ output ≤ max(inputs)")

    def check(self, agg_fn, n_tests=100):
        rng = random.Random(42)
        for _ in range(n_tests):
            n_dims = rng.randint(2, 5)
            dims = [f"d{i}" for i in range(n_dims)]
            scores = {d: rng.uniform(0.1, 0.9) for d in dims}
            weights = {d: rng.random() + 0.1 for d in dims}
            result = agg_fn(scores, weights)

            if result < min(scores.values()) - 1e-9:
                return False
            if result > max(scores.values()) + 1e-9:
                return False
        return True


class IdempotencyProperty(AggregationProperty):
    """If all inputs are the same, output equals that value."""

    def __init__(self):
        super().__init__("idempotency", "All inputs equal v → output = v")

    def check(self, agg_fn, n_tests=50):
        rng = random.Random(42)
        for _ in range(n_tests):
            v = rng.uniform(0.1, 0.9)
            n_dims = rng.randint(2, 5)
            dims = [f"d{i}" for i in range(n_dims)]
            scores = {d: v for d in dims}
            weights = {d: rng.random() + 0.1 for d in dims}
            result = agg_fn(scores, weights)

            if abs(result - v) > 1e-6:
                return False
        return True


# ============================================================
# §3 — Decision Criteria
# ============================================================

@dataclass
class AggregationContext:
    """Context for choosing an aggregation function."""
    use_case: str
    risk_tolerance: str  # "high", "medium", "low"
    dimension_independence: bool  # Are dimensions independent?
    allow_compensation: bool  # Can high dim compensate for low dim?

    def recommended_function(self) -> str:
        """Recommend an aggregation function based on context."""
        if self.risk_tolerance == "low" or not self.allow_compensation:
            return "min"
        elif self.risk_tolerance == "high" and self.allow_compensation:
            return "weighted_arithmetic_mean"
        elif not self.dimension_independence:
            return "geometric_mean"
        else:
            return "weighted_power_mean"


# ============================================================
# §4 — Sensitivity Analysis
# ============================================================

class SensitivityAnalyzer:
    """Analyze how sensitive aggregation is to input changes."""

    def __init__(self, agg_fn: Callable):
        self.agg_fn = agg_fn

    def partial_derivative(self, scores: Dict[str, float],
                           weights: Dict[str, float],
                           dimension: str,
                           delta: float = 0.001) -> float:
        """Numerical partial derivative wrt one dimension."""
        base = self.agg_fn(scores, weights)
        perturbed = dict(scores)
        perturbed[dimension] = min(1.0, scores[dimension] + delta)
        result = self.agg_fn(perturbed, weights)
        return (result - base) / delta

    def sensitivity_vector(self, scores: Dict[str, float],
                           weights: Dict[str, float]) -> Dict[str, float]:
        """Sensitivity of output to each dimension."""
        return {d: self.partial_derivative(scores, weights, d)
                for d in scores}

    def max_sensitivity(self, scores: Dict[str, float],
                        weights: Dict[str, float]) -> Tuple[str, float]:
        """Dimension with highest sensitivity."""
        sv = self.sensitivity_vector(scores, weights)
        dim = max(sv, key=sv.get)
        return dim, sv[dim]

    def condition_number(self, scores: Dict[str, float],
                         weights: Dict[str, float]) -> float:
        """Ratio of max to min sensitivity (higher = more sensitive to input mix)."""
        sv = self.sensitivity_vector(scores, weights)
        max_s = max(sv.values())
        min_s = min(abs(v) for v in sv.values()) if sv else 0
        if min_s < 1e-12:
            return float('inf')
        return max_s / min_s


# ============================================================
# §5 — Cross-Federation Reconciliation
# ============================================================

class CrossFederationReconciler:
    """Reconcile trust scores computed with different aggregation functions."""

    def reconcile(self, score_a: float, agg_fn_a: str,
                  score_b: float, agg_fn_b: str,
                  trust_a: float = 0.5, trust_b: float = 0.5) -> float:
        """Reconcile two scores from different federations.

        Uses trust-weighted average with a correction for aggregation bias.
        """
        # Correction factors: GM < WAM < max; compensate for systematic bias
        bias = {
            "weighted_arithmetic_mean": 0.0,
            "geometric_mean": 0.05,  # GM is systematically lower
            "harmonic_mean": 0.1,    # HM is even lower
            "min": 0.15,             # MIN is most conservative
        }

        corrected_a = score_a + bias.get(agg_fn_a, 0.0)
        corrected_b = score_b + bias.get(agg_fn_b, 0.0)

        # Trust-weighted combination
        total_trust = trust_a + trust_b
        if total_trust == 0:
            return (corrected_a + corrected_b) / 2

        result = (corrected_a * trust_a + corrected_b * trust_b) / total_trust
        return max(0.0, min(1.0, result))


# ============================================================
# §6 — Tests
# ============================================================

AGG_FUNCTIONS = {
    "wam": weighted_arithmetic_mean,
    "gm": geometric_mean,
    "hm": harmonic_mean,
    "min": min_aggregation,
}


def test_basic_properties():
    """§6.1: Basic aggregation function properties."""
    print("\n§6.1 Basic Properties")

    scores = {"talent": 0.8, "training": 0.6, "temperament": 0.7}
    weights = {"talent": 0.4, "training": 0.3, "temperament": 0.3}

    # s1: WAM computed correctly
    wam = weighted_arithmetic_mean(scores, weights)
    expected = (0.8 * 0.4 + 0.6 * 0.3 + 0.7 * 0.3) / 1.0
    check(abs(wam - expected) < 0.001,
          f"s1: WAM = {wam:.4f} (expected {expected:.4f})")

    # s2: GM ≤ WAM (AM-GM inequality)
    gm = geometric_mean(scores, weights)
    check(gm <= wam + 0.001,
          f"s2: GM ({gm:.4f}) ≤ WAM ({wam:.4f}) — AM-GM inequality")

    # s3: HM ≤ GM ≤ WAM (mean inequality chain)
    hm = harmonic_mean(scores, weights)
    check(hm <= gm + 0.001,
          f"s3: HM ({hm:.4f}) ≤ GM ({gm:.4f}) ≤ WAM ({wam:.4f})")

    # s4: MIN ≤ all others
    mn = min_aggregation(scores, weights)
    check(mn <= hm + 0.001 and mn <= gm + 0.001 and mn <= wam + 0.001,
          f"s4: MIN ({mn:.4f}) ≤ all other means")

    # s5: Power mean with p=1 equals WAM
    wpm1 = weighted_power_mean(scores, weights, p=1.0)
    check(abs(wpm1 - wam) < 0.001,
          f"s5: WPM(p=1) = {wpm1:.4f} ≈ WAM = {wam:.4f}")

    # s6: Power mean with p=-1 approximates HM
    wpm_neg1 = weighted_power_mean(scores, weights, p=-1.0)
    check(abs(wpm_neg1 - hm) < 0.01,
          f"s6: WPM(p=-1) = {wpm_neg1:.4f} ≈ HM = {hm:.4f}")


def test_formal_properties():
    """§6.2: Formal property verification."""
    print("\n§6.2 Formal Properties")

    monotonicity = MonotonicityProperty()
    boundedness = BoundednessProperty()
    idempotency = IdempotencyProperty()

    for name, fn in AGG_FUNCTIONS.items():
        # s7: Monotonicity
        is_mono = monotonicity.check(fn)
        check(is_mono, f"s7_{name}: {name} is monotone")

        # s8: Boundedness
        is_bounded = boundedness.check(fn)
        check(is_bounded, f"s8_{name}: {name} is bounded")

        # s9: Idempotency
        is_idemp = idempotency.check(fn)
        check(is_idemp, f"s9_{name}: {name} is idempotent")


def test_decision_criteria():
    """§6.3: Aggregation function selection."""
    print("\n§6.3 Decision Criteria")

    # s10: Low risk → MIN
    ctx1 = AggregationContext("authority_gate", "low", True, False)
    check(ctx1.recommended_function() == "min",
          f"s10: low risk → {ctx1.recommended_function()}")

    # s11: High risk, compensating → WAM
    ctx2 = AggregationContext("general_query", "high", True, True)
    check(ctx2.recommended_function() == "weighted_arithmetic_mean",
          f"s11: high risk → {ctx2.recommended_function()}")

    # s12: Medium risk, dependent dimensions → GM
    ctx3 = AggregationContext("cross_domain", "medium", False, True)
    check(ctx3.recommended_function() == "geometric_mean",
          f"s12: dependent dims → {ctx3.recommended_function()}")


def test_sensitivity():
    """§6.4: Sensitivity analysis."""
    print("\n§6.4 Sensitivity Analysis")

    scores = {"talent": 0.8, "training": 0.3, "temperament": 0.7}
    weights = {"talent": 0.5, "training": 0.25, "temperament": 0.25}

    # s13: WAM sensitivity proportional to weight
    sa_wam = SensitivityAnalyzer(weighted_arithmetic_mean)
    sv = sa_wam.sensitivity_vector(scores, weights)
    check(sv["talent"] > sv["training"],
          f"s13: WAM more sensitive to talent ({sv['talent']:.3f}) than training ({sv['training']:.3f})")

    # s14: GM more sensitive to low-scoring dimensions
    sa_gm = SensitivityAnalyzer(geometric_mean)
    sv_gm = sa_gm.sensitivity_vector(scores, weights)
    # Training is lowest score → GM should be very sensitive to it
    check(sv_gm["training"] > 0,
          f"s14: GM sensitive to low training ({sv_gm['training']:.3f})")

    # s15: MIN only sensitive to minimum dimension
    sa_min = SensitivityAnalyzer(min_aggregation)
    sv_min = sa_min.sensitivity_vector(scores, weights)
    check(sv_min["training"] > sv_min["talent"],
          f"s15: MIN sensitive to min dim (training={sv_min['training']:.3f})")

    # s16: Condition number
    cn = sa_wam.condition_number(scores, weights)
    check(cn > 1.0, f"s16: WAM condition number = {cn:.2f} (>1 means heterogeneous sensitivity)")


def test_adversarial_manipulation():
    """§6.5: Robustness to adversarial score manipulation."""
    print("\n§6.5 Adversarial Robustness")

    honest_scores = {"talent": 0.7, "training": 0.7, "temperament": 0.7}
    weights = {"talent": 1.0, "training": 1.0, "temperament": 1.0}

    # Adversary inflates one dimension to max
    adversarial_scores = {"talent": 1.0, "training": 0.1, "temperament": 0.1}

    # s17: WAM is vulnerable (can be inflated by one high score)
    wam_honest = weighted_arithmetic_mean(honest_scores, weights)
    wam_adversarial = weighted_arithmetic_mean(adversarial_scores, weights)
    wam_manipulation_gain = wam_adversarial - min(adversarial_scores.values())
    check(wam_manipulation_gain > 0.2,
          f"s17: WAM vulnerable to inflation (gain={wam_manipulation_gain:.3f})")

    # s18: GM is more resistant (one 0.1 drags everything down)
    gm_adversarial = geometric_mean(adversarial_scores, weights)
    check(gm_adversarial < wam_adversarial,
          f"s18: GM ({gm_adversarial:.3f}) more conservative than WAM ({wam_adversarial:.3f})")

    # s19: MIN is most resistant (reports actual minimum)
    min_adversarial = min_aggregation(adversarial_scores, weights)
    check(min_adversarial == 0.1,
          f"s19: MIN reports actual minimum ({min_adversarial})")

    # s20: HM also penalizes low dimensions
    hm_adversarial = harmonic_mean(adversarial_scores, weights)
    check(hm_adversarial < wam_adversarial,
          f"s20: HM ({hm_adversarial:.3f}) < WAM ({wam_adversarial:.3f})")


def test_cross_federation():
    """§6.6: Cross-federation reconciliation."""
    print("\n§6.6 Cross-Federation Reconciliation")

    reconciler = CrossFederationReconciler()

    # s21: Same function, same score → no change
    result = reconciler.reconcile(0.7, "weighted_arithmetic_mean",
                                   0.7, "weighted_arithmetic_mean")
    check(abs(result - 0.7) < 0.01,
          f"s21: same function, same score → {result:.3f}")

    # s22: Different functions → bias correction applied
    result2 = reconciler.reconcile(0.7, "weighted_arithmetic_mean",
                                    0.65, "geometric_mean",
                                    trust_a=0.5, trust_b=0.5)
    # GM score gets +0.05 bias correction → 0.70
    check(abs(result2 - 0.7) < 0.05,
          f"s22: bias-corrected reconciliation = {result2:.3f}")

    # s23: Trust weighting matters
    result_trust = reconciler.reconcile(0.9, "weighted_arithmetic_mean",
                                         0.3, "weighted_arithmetic_mean",
                                         trust_a=0.9, trust_b=0.1)
    check(result_trust > 0.7,
          f"s23: high-trust federation dominates ({result_trust:.3f})")

    # s24: Result bounded to [0, 1]
    for _ in range(20):
        r = reconciler.reconcile(random.random(), "min",
                                  random.random(), "weighted_arithmetic_mean")
        check(0.0 <= r <= 1.0, f"s24: reconciled score {r:.3f} in [0,1]")
        break  # Check once explicitly


def test_power_mean_spectrum():
    """§6.7: Power mean unifies all aggregation functions."""
    print("\n§6.7 Power Mean Spectrum")

    scores = {"a": 0.8, "b": 0.3, "c": 0.6}
    weights = {"a": 1.0, "b": 1.0, "c": 1.0}

    # s25: As p increases, WPM increases (for mixed scores)
    results = {}
    for p in [-2, -1, 0, 1, 2]:
        results[p] = weighted_power_mean(scores, weights, p=float(p))

    # WPM is increasing in p
    check(results[-2] <= results[-1] + 0.01,
          f"s25a: WPM(p=-2)={results[-2]:.3f} ≤ WPM(p=-1)={results[-1]:.3f}")
    check(results[-1] <= results[0] + 0.01,
          f"s25b: WPM(p=-1)={results[-1]:.3f} ≤ WPM(p=0)={results[0]:.3f}")
    check(results[0] <= results[1] + 0.01,
          f"s25c: WPM(p=0)={results[0]:.3f} ≤ WPM(p=1)={results[1]:.3f}")

    # s26: p → -∞ approaches min
    wpm_neg10 = weighted_power_mean(scores, weights, p=-10.0)
    check(abs(wpm_neg10 - min(scores.values())) < 0.05,
          f"s26: WPM(p=-10) ≈ MIN ({wpm_neg10:.3f} ≈ {min(scores.values()):.3f})")


# ============================================================
# §7 — Run All Tests
# ============================================================

def main():
    print("=" * 70)
    print("Trust Aggregation Function Semantics")
    print("Session 28, Track 8")
    print("=" * 70)

    test_basic_properties()
    test_formal_properties()
    test_decision_criteria()
    test_sensitivity()
    test_adversarial_manipulation()
    test_cross_federation()
    test_power_mean_spectrum()

    print(f"\n{'=' * 70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    if errors:
        print(f"\nFailures:")
        for e in errors:
            print(f"  - {e}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
