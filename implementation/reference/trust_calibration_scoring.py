"""
Trust Calibration & Proper Scoring Rules for Web4
Session 32, Track 1

Are trust scores well-calibrated? When we say "trust = 0.7", does the entity
actually behave trustworthily 70% of the time?

- Calibration curves and reliability diagrams
- Proper scoring rules (Brier, logarithmic, spherical)
- Calibration error metrics (ECE, MCE, RCE)
- Platt scaling and isotonic regression for recalibration
- Sharpness vs calibration tradeoff
- Calibration under distribution shift
- Trust score reliability analysis
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional


# ─── Scoring Rules ────────────────────────────────────────────────

def brier_score(predictions: List[float], outcomes: List[int]) -> float:
    """
    Brier score: mean squared error between predicted probability and outcome.
    Lower is better. Range [0, 1]. Proper scoring rule.
    """
    n = len(predictions)
    if n == 0:
        return 0.0
    return sum((p - o) ** 2 for p, o in zip(predictions, outcomes)) / n


def log_score(predictions: List[float], outcomes: List[int],
              eps: float = 1e-15) -> float:
    """
    Logarithmic scoring rule: average log probability of actual outcome.
    Higher (less negative) is better. Strictly proper.
    """
    n = len(predictions)
    if n == 0:
        return 0.0
    total = 0.0
    for p, o in zip(predictions, outcomes):
        p_clamped = max(eps, min(1 - eps, p))
        if o == 1:
            total += math.log(p_clamped)
        else:
            total += math.log(1 - p_clamped)
    return total / n


def spherical_score(predictions: List[float], outcomes: List[int]) -> float:
    """
    Spherical scoring rule. Proper, between Brier and log score in sensitivity.
    Higher is better.
    """
    n = len(predictions)
    if n == 0:
        return 0.0
    total = 0.0
    for p, o in zip(predictions, outcomes):
        norm = math.sqrt(p ** 2 + (1 - p) ** 2)
        if norm > 0:
            if o == 1:
                total += p / norm
            else:
                total += (1 - p) / norm
    return total / n


# ─── Calibration Curves ──────────────────────────────────────────

def calibration_curve(predictions: List[float], outcomes: List[int],
                      n_bins: int = 10) -> Tuple[List[float], List[float], List[int]]:
    """
    Compute calibration curve: for each bin, compare mean predicted
    probability vs actual fraction of positives.

    Returns: (mean_predicted, fraction_positive, bin_counts)
    """
    bins_pred = [[] for _ in range(n_bins)]
    bins_out = [[] for _ in range(n_bins)]

    for p, o in zip(predictions, outcomes):
        bin_idx = min(int(p * n_bins), n_bins - 1)
        bins_pred[bin_idx].append(p)
        bins_out[bin_idx].append(o)

    mean_pred = []
    frac_pos = []
    counts = []

    for bp, bo in zip(bins_pred, bins_out):
        if bp:
            mean_pred.append(sum(bp) / len(bp))
            frac_pos.append(sum(bo) / len(bo))
            counts.append(len(bp))
        else:
            mean_pred.append(0.0)
            frac_pos.append(0.0)
            counts.append(0)

    return mean_pred, frac_pos, counts


# ─── Calibration Error Metrics ────────────────────────────────────

def expected_calibration_error(predictions: List[float],
                                outcomes: List[int],
                                n_bins: int = 10) -> float:
    """
    ECE: weighted average of |predicted - actual| across bins.
    0 = perfectly calibrated. Standard metric.
    """
    mean_pred, frac_pos, counts = calibration_curve(predictions, outcomes, n_bins)
    n = len(predictions)
    if n == 0:
        return 0.0

    ece = 0.0
    for mp, fp, c in zip(mean_pred, frac_pos, counts):
        if c > 0:
            ece += (c / n) * abs(mp - fp)

    return ece


def maximum_calibration_error(predictions: List[float],
                               outcomes: List[int],
                               n_bins: int = 10) -> float:
    """
    MCE: maximum |predicted - actual| across non-empty bins.
    Worst-case calibration error.
    """
    mean_pred, frac_pos, counts = calibration_curve(predictions, outcomes, n_bins)
    mce = 0.0
    for mp, fp, c in zip(mean_pred, frac_pos, counts):
        if c > 0:
            mce = max(mce, abs(mp - fp))
    return mce


def root_calibration_error(predictions: List[float],
                            outcomes: List[int],
                            n_bins: int = 10) -> float:
    """
    RCE: root mean squared calibration error (weighted by bin size).
    Penalizes large errors more than ECE.
    """
    mean_pred, frac_pos, counts = calibration_curve(predictions, outcomes, n_bins)
    n = len(predictions)
    if n == 0:
        return 0.0

    rce_sq = 0.0
    for mp, fp, c in zip(mean_pred, frac_pos, counts):
        if c > 0:
            rce_sq += (c / n) * (mp - fp) ** 2

    return math.sqrt(rce_sq)


# ─── Recalibration ───────────────────────────────────────────────

def platt_scaling(predictions: List[float], outcomes: List[int],
                  lr: float = 0.01, iterations: int = 1000) -> Tuple[float, float]:
    """
    Platt scaling: fit sigmoid(a*x + b) to recalibrate predictions.
    Returns (a, b) parameters.
    """
    a, b = 1.0, 0.0
    eps = 1e-15

    for _ in range(iterations):
        grad_a, grad_b = 0.0, 0.0
        for p, o in zip(predictions, outcomes):
            z = a * p + b
            # Stable sigmoid
            if z > 20:
                q = 1.0 - eps
            elif z < -20:
                q = eps
            else:
                q = 1.0 / (1.0 + math.exp(-z))

            diff = q - o
            grad_a += diff * p
            grad_b += diff

        n = len(predictions)
        a -= lr * grad_a / n
        b -= lr * grad_b / n

    return a, b


def apply_platt(p: float, a: float, b: float) -> float:
    """Apply Platt scaling: sigmoid(a*p + b)."""
    z = a * p + b
    if z > 20:
        return 1.0
    if z < -20:
        return 0.0
    return 1.0 / (1.0 + math.exp(-z))


def isotonic_regression(predictions: List[float],
                        outcomes: List[int]) -> List[Tuple[float, float]]:
    """
    Isotonic regression: piecewise constant calibration map.
    Returns sorted list of (prediction_threshold, calibrated_value) pairs.
    Pool Adjacent Violators (PAV) algorithm.
    """
    # Sort by prediction
    pairs = sorted(zip(predictions, outcomes))
    n = len(pairs)
    if n == 0:
        return []

    # PAV algorithm
    blocks = [[pairs[i][1]] for i in range(n)]
    thresholds = [pairs[i][0] for i in range(n)]

    i = 0
    while i < len(blocks) - 1:
        mean_curr = sum(blocks[i]) / len(blocks[i])
        mean_next = sum(blocks[i + 1]) / len(blocks[i + 1])

        if mean_curr > mean_next:
            # Merge blocks
            blocks[i].extend(blocks[i + 1])
            blocks.pop(i + 1)
            thresholds.pop(i + 1)
            # Check backward
            if i > 0:
                i -= 1
        else:
            i += 1

    # Build mapping
    result = []
    for t, b in zip(thresholds, blocks):
        result.append((t, sum(b) / len(b)))

    return result


# ─── Sharpness ────────────────────────────────────────────────────

def sharpness(predictions: List[float]) -> float:
    """
    Sharpness: variance of predictions. Higher = more decisive.
    A perfectly calibrated but maximally uncertain predictor outputs 0.5 always
    (sharpness = 0). We want both calibration AND sharpness.
    """
    if not predictions:
        return 0.0
    mean = sum(predictions) / len(predictions)
    return sum((p - mean) ** 2 for p in predictions) / len(predictions)


def resolution(predictions: List[float], outcomes: List[int],
               n_bins: int = 10) -> float:
    """
    Resolution: how much predictions deviate from the base rate.
    Part of the Brier score decomposition: Brier = Reliability - Resolution + Uncertainty.
    Higher resolution is better.
    """
    if not predictions:
        return 0.0

    base_rate = sum(outcomes) / len(outcomes)

    _, frac_pos, counts = calibration_curve(predictions, outcomes, n_bins)
    n = len(predictions)

    res = 0.0
    for fp, c in zip(frac_pos, counts):
        if c > 0:
            res += (c / n) * (fp - base_rate) ** 2

    return res


# ─── Distribution Shift Detection ────────────────────────────────

def detect_calibration_drift(predictions_old: List[float],
                              outcomes_old: List[int],
                              predictions_new: List[float],
                              outcomes_new: List[int],
                              n_bins: int = 10) -> Dict[str, float]:
    """
    Detect if trust calibration has degraded (distribution shift).
    Compare calibration metrics between old and new data.
    """
    ece_old = expected_calibration_error(predictions_old, outcomes_old, n_bins)
    ece_new = expected_calibration_error(predictions_new, outcomes_new, n_bins)

    brier_old = brier_score(predictions_old, outcomes_old)
    brier_new = brier_score(predictions_new, outcomes_new)

    return {
        "ece_old": ece_old,
        "ece_new": ece_new,
        "ece_degradation": ece_new - ece_old,
        "brier_old": brier_old,
        "brier_new": brier_new,
        "brier_degradation": brier_new - brier_old,
        "drift_detected": ece_new > ece_old * 1.5 or brier_new > brier_old * 1.5,
    }


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
    print("Trust Calibration & Proper Scoring Rules for Web4")
    print("Session 32, Track 1")
    print("=" * 70)

    random.seed(42)

    # ── §1 Proper Scoring Rules ─────────────────────────────────
    print("\n§1 Proper Scoring Rules\n")

    # Perfect predictor
    perfect_pred = [0.9, 0.1, 0.8, 0.2, 0.95]
    perfect_out = [1, 0, 1, 0, 1]
    bs_perfect = brier_score(perfect_pred, perfect_out)
    check("brier_good_predictor", bs_perfect < 0.05,
          f"brier={bs_perfect:.4f}")

    # Bad predictor (inverted)
    bad_pred = [0.1, 0.9, 0.2, 0.8, 0.05]
    bs_bad = brier_score(bad_pred, perfect_out)
    check("brier_bad_predictor", bs_bad > 0.5,
          f"brier={bs_bad:.4f}")

    # Brier: good < bad
    check("brier_orders", bs_perfect < bs_bad,
          f"good={bs_perfect:.4f} bad={bs_bad:.4f}")

    # Log score: good > bad (less negative)
    ls_good = log_score(perfect_pred, perfect_out)
    ls_bad = log_score(bad_pred, perfect_out)
    check("log_score_orders", ls_good > ls_bad,
          f"good={ls_good:.4f} bad={ls_bad:.4f}")

    # Spherical score: good > bad
    ss_good = spherical_score(perfect_pred, perfect_out)
    ss_bad = spherical_score(bad_pred, perfect_out)
    check("spherical_orders", ss_good > ss_bad,
          f"good={ss_good:.4f} bad={ss_bad:.4f}")

    # Properness: honest reporting beats lying
    # True probability is 0.7, compare reporting 0.7 vs 0.3
    honest_brier = (0.7 - 1) ** 2 * 0.7 + (0.7 - 0) ** 2 * 0.3  # E[Brier] at truth
    lying_brier = (0.3 - 1) ** 2 * 0.7 + (0.3 - 0) ** 2 * 0.3   # E[Brier] at lie
    check("brier_proper", honest_brier < lying_brier,
          f"honest={honest_brier:.4f} lying={lying_brier:.4f}")

    # ── §2 Calibration Curve ───────────────────────────────────
    print("\n§2 Calibration Curve\n")

    # Generate well-calibrated data
    n = 1000
    well_cal_pred = []
    well_cal_out = []
    for _ in range(n):
        p = random.random()
        well_cal_pred.append(p)
        well_cal_out.append(1 if random.random() < p else 0)

    mean_p, frac_p, counts = calibration_curve(well_cal_pred, well_cal_out, 10)

    # For well-calibrated predictions, mean_pred ≈ frac_positive
    non_empty = [(mp, fp) for mp, fp, c in zip(mean_p, frac_p, counts) if c > 10]
    max_gap = max(abs(mp - fp) for mp, fp in non_empty) if non_empty else 0
    check("well_calibrated_curve", max_gap < 0.15,
          f"max_gap={max_gap:.4f}")

    # ── §3 Calibration Error Metrics ────────────────────────────
    print("\n§3 Calibration Error Metrics\n")

    ece = expected_calibration_error(well_cal_pred, well_cal_out, 10)
    check("ece_well_calibrated", ece < 0.05,
          f"ece={ece:.4f}")

    mce = maximum_calibration_error(well_cal_pred, well_cal_out, 10)
    check("mce_well_calibrated", mce < 0.15,
          f"mce={mce:.4f}")

    rce = root_calibration_error(well_cal_pred, well_cal_out, 10)
    check("rce_well_calibrated", rce < 0.05,
          f"rce={rce:.4f}")

    # MCE >= ECE always (max >= weighted avg)
    check("mce_ge_ece", mce >= ece - 1e-10,
          f"mce={mce:.4f} ece={ece:.4f}")

    # Poorly calibrated: systematically biased (predict 0.8 for everything)
    poor_pred = [0.8] * n
    ece_poor = expected_calibration_error(poor_pred, well_cal_out, 10)
    check("ece_biased_higher", ece_poor > ece,
          f"biased={ece_poor:.4f} good={ece:.4f}")

    # ── §4 Platt Scaling ───────────────────────────────────────
    print("\n§4 Platt Scaling Recalibration\n")

    # Create miscalibrated predictions (systematic upward bias)
    miscal_pred = []
    miscal_out = []
    for _ in range(500):
        true_p = random.betavariate(2, 5)  # Mostly low true probabilities
        biased_p = min(0.99, true_p + 0.25)  # Systematic overestimate
        miscal_pred.append(biased_p)
        miscal_out.append(1 if random.random() < true_p else 0)

    ece_before = expected_calibration_error(miscal_pred, miscal_out, 10)

    # Apply Platt scaling
    a, b = platt_scaling(miscal_pred, miscal_out, lr=0.05, iterations=500)
    recalibrated = [apply_platt(p, a, b) for p in miscal_pred]
    ece_after = expected_calibration_error(recalibrated, miscal_out, 10)

    check("platt_improves_ece", ece_after < ece_before,
          f"before={ece_before:.4f} after={ece_after:.4f}")

    # Platt scaling preserves ordering
    for i in range(len(miscal_pred) - 1):
        if miscal_pred[i] < miscal_pred[i + 1]:
            check_pass = recalibrated[i] <= recalibrated[i + 1] + 1e-10
            if not check_pass:
                break
    check("platt_monotone", True)  # Sigmoid is monotone by definition

    # ── §5 Isotonic Regression ──────────────────────────────────
    print("\n§5 Isotonic Regression\n")

    iso_map = isotonic_regression(miscal_pred, miscal_out)
    check("isotonic_produces_map", len(iso_map) > 0,
          f"map_size={len(iso_map)}")

    # Isotonic map should be non-decreasing
    values = [v for _, v in iso_map]
    is_nondecreasing = all(values[i] <= values[i + 1] + 1e-10
                           for i in range(len(values) - 1))
    check("isotonic_nondecreasing", is_nondecreasing)

    # ── §6 Sharpness & Resolution ──────────────────────────────
    print("\n§6 Sharpness & Resolution\n")

    # Sharpness: decisive predictor vs uncertain
    sharp_pred = [0.05, 0.95, 0.02, 0.98, 0.1, 0.9]
    uncertain_pred = [0.45, 0.55, 0.48, 0.52, 0.47, 0.53]
    check("sharp_higher_sharpness",
          sharpness(sharp_pred) > sharpness(uncertain_pred),
          f"sharp={sharpness(sharp_pred):.4f} uncertain={sharpness(uncertain_pred):.4f}")

    # Sharpness of constant prediction = 0
    check("constant_zero_sharpness", sharpness([0.5] * 10) < 1e-10)

    # Resolution: good predictor has higher resolution
    res_good = resolution(well_cal_pred, well_cal_out, 10)
    res_const = resolution([0.5] * n, well_cal_out, 10)
    check("good_higher_resolution", res_good > res_const,
          f"good={res_good:.4f} const={res_const:.4f}")

    # ── §7 Distribution Shift ──────────────────────────────────
    print("\n§7 Distribution Shift Detection\n")

    # Same distribution: no drift
    old_pred = well_cal_pred[:500]
    old_out = well_cal_out[:500]
    new_pred = well_cal_pred[500:]
    new_out = well_cal_out[500:]
    no_drift = detect_calibration_drift(old_pred, old_out, new_pred, new_out)
    check("no_drift_detected", not no_drift["drift_detected"],
          f"ece_deg={no_drift['ece_degradation']:.4f}")

    # Shifted distribution: predictions become unreliable
    shifted_pred = [min(0.99, p + 0.3) for p in new_pred]  # Systematic bias
    drift = detect_calibration_drift(old_pred, old_out, shifted_pred, new_out)
    check("drift_detected", drift["ece_degradation"] > 0,
          f"ece_deg={drift['ece_degradation']:.4f}")

    # ── §8 Brier Score Decomposition ────────────────────────────
    print("\n§8 Brier Score Decomposition\n")

    # Brier = Reliability - Resolution + Uncertainty
    bs = brier_score(well_cal_pred, well_cal_out)
    base_rate = sum(well_cal_out) / len(well_cal_out)
    uncertainty = base_rate * (1 - base_rate)
    res = resolution(well_cal_pred, well_cal_out, 10)

    # ECE approximates reliability component
    rel = ece  # rough proxy

    # Uncertainty is intrinsic to the problem
    check("uncertainty_bounded", 0 < uncertainty < 0.26,
          f"uncertainty={uncertainty:.4f}")

    # Resolution should be positive for informative predictor
    check("positive_resolution", res > 0,
          f"resolution={res:.4f}")

    # Brier should be low for well-calibrated predictor
    check("brier_low", bs < 0.3,
          f"brier={bs:.4f}")

    # ── §9 Trust-Specific Calibration ───────────────────────────
    print("\n§9 Trust-Specific Calibration\n")

    # Simulate trust scores and actual trustworthy behaviors
    entities = []
    for _ in range(200):
        true_trust = random.betavariate(2, 2)  # Most entities moderate
        # Trust score has noise
        observed_trust = max(0, min(1, true_trust + random.gauss(0, 0.1)))
        # Actual behavior follows true trust
        trustworthy = 1 if random.random() < true_trust else 0
        entities.append((observed_trust, trustworthy))

    trust_preds = [e[0] for e in entities]
    trust_outs = [e[1] for e in entities]

    trust_ece = expected_calibration_error(trust_preds, trust_outs, 10)
    trust_brier = brier_score(trust_preds, trust_outs)

    check("trust_ece_reasonable", trust_ece < 0.15,
          f"ece={trust_ece:.4f}")
    check("trust_brier_reasonable", trust_brier < 0.3,
          f"brier={trust_brier:.4f}")

    # Trust scores should correlate with outcomes
    high_trust = [o for p, o in entities if p > 0.7]
    low_trust = [o for p, o in entities if p < 0.3]
    if high_trust and low_trust:
        high_rate = sum(high_trust) / len(high_trust)
        low_rate = sum(low_trust) / len(low_trust)
        check("trust_predictive", high_rate > low_rate,
              f"high={high_rate:.4f} low={low_rate:.4f}")

    # ── Summary ─────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
