"""
Trust Decay Models for Web4
Session 30, Track 6

Comprehensive analysis of trust decay mechanisms:
- Exponential decay (standard, memoryless)
- Polynomial decay (slower, heavy-tailed)
- Stepwise decay (threshold-based transitions)
- Activity-dependent decay (interaction maintains trust)
- Context-dependent decay (different rates for different roles)
- Decay with floor (minimum trust level)
- Comparative analysis of decay functions
- Optimal decay parameter selection
"""

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Callable


# ─── Decay Functions ───────────────────────────────────────────────

def exponential_decay(t0: float, rate: float, time: int) -> float:
    """T(t) = t0 * e^(-rate * time)"""
    return t0 * math.exp(-rate * time)


def polynomial_decay(t0: float, alpha: float, time: int) -> float:
    """T(t) = t0 / (1 + alpha * time)"""
    return t0 / (1 + alpha * time)


def stepwise_decay(t0: float, step_size: float, step_interval: int, time: int) -> float:
    """T(t) = t0 - step_size * floor(time / step_interval)"""
    steps = time // step_interval
    return max(0, t0 - step_size * steps)


def logarithmic_decay(t0: float, rate: float, time: int) -> float:
    """T(t) = t0 / (1 + rate * ln(1 + time))"""
    return t0 / (1 + rate * math.log(1 + time))


def decay_with_floor(decay_fn: Callable, floor: float, *args, **kwargs) -> float:
    """Apply any decay function but cap at a minimum floor."""
    return max(floor, decay_fn(*args, **kwargs))


# ─── Activity-Dependent Decay ─────────────────────────────────────

@dataclass
class ActivityTracker:
    """Tracks entity activity and adjusts decay rate."""
    base_decay_rate: float = 0.01
    activity_boost: float = 0.005  # trust boost per interaction
    max_trust: float = 1.0
    min_trust: float = 0.0

    def compute_trust(self, initial_trust: float, time_steps: int,
                      activity_times: List[int]) -> List[float]:
        """
        Simulate trust over time with activity-dependent decay.
        Active entities decay slower; inactive entities decay faster.
        """
        trust_history = [initial_trust]
        trust = initial_trust
        activity_set = set(activity_times)

        for t in range(1, time_steps + 1):
            if t in activity_set:
                # Activity: boost trust
                trust = min(self.max_trust, trust + self.activity_boost)
            else:
                # No activity: decay
                trust *= (1 - self.base_decay_rate)

            trust = max(self.min_trust, trust)
            trust_history.append(trust)

        return trust_history


# ─── Context-Dependent Decay ──────────────────────────────────────

class TrustContext(Enum):
    FINANCIAL = "financial"       # fastest decay (high-stakes)
    IDENTITY = "identity"         # medium decay
    SOCIAL = "social"             # slow decay
    CONTENT = "content"           # slowest decay


CONTEXT_DECAY_RATES = {
    TrustContext.FINANCIAL: 0.05,
    TrustContext.IDENTITY: 0.02,
    TrustContext.SOCIAL: 0.01,
    TrustContext.CONTENT: 0.005,
}


def context_dependent_decay(t0: float, context: TrustContext, time: int) -> float:
    """Decay rate depends on trust context."""
    rate = CONTEXT_DECAY_RATES[context]
    return exponential_decay(t0, rate, time)


# ─── Decay Parameter Optimization ─────────────────────────────────

def optimal_decay_rate(target_half_life: int) -> float:
    """
    Compute exponential decay rate for desired half-life.
    T(t) = T0 * e^(-rate * t)
    At t = half_life: T = T0/2
    rate = ln(2) / half_life
    """
    if target_half_life <= 0:
        return float('inf')
    return math.log(2) / target_half_life


def half_life(rate: float) -> float:
    """Compute half-life from exponential decay rate."""
    if rate <= 0:
        return float('inf')
    return math.log(2) / rate


def time_to_threshold(t0: float, rate: float, threshold: float) -> float:
    """Time until trust drops below threshold (exponential)."""
    if t0 <= threshold:
        return 0.0
    if rate <= 0:
        return float('inf')
    return -math.log(threshold / t0) / rate


# ─── Comparative Analysis ─────────────────────────────────────────

def compare_decay_models(t0: float, time_steps: int,
                          exp_rate: float = 0.02,
                          poly_alpha: float = 0.05,
                          log_rate: float = 0.5) -> Dict[str, List[float]]:
    """Compare different decay models over time."""
    results = {
        "exponential": [],
        "polynomial": [],
        "logarithmic": [],
        "stepwise": [],
    }

    for t in range(time_steps + 1):
        results["exponential"].append(exponential_decay(t0, exp_rate, t))
        results["polynomial"].append(polynomial_decay(t0, poly_alpha, t))
        results["logarithmic"].append(logarithmic_decay(t0, log_rate, t))
        results["stepwise"].append(stepwise_decay(t0, 0.1, 10, t))

    return results


def decay_area_under_curve(values: List[float]) -> float:
    """Total trust maintained over time (trapezoidal integration)."""
    if len(values) < 2:
        return 0.0
    total = 0.0
    for i in range(len(values) - 1):
        total += (values[i] + values[i + 1]) / 2
    return total


# ─── Trust Renewal ─────────────────────────────────────────────────

def trust_with_renewal(t0: float, decay_rate: float, time_steps: int,
                        renewal_times: List[int], renewal_boost: float = 0.2) -> List[float]:
    """
    Trust decay with periodic renewal (re-attestation).
    """
    trust_history = [t0]
    trust = t0

    renewal_set = set(renewal_times)
    for t in range(1, time_steps + 1):
        trust *= (1 - decay_rate)
        if t in renewal_set:
            trust = min(1.0, trust + renewal_boost)
        trust_history.append(trust)

    return trust_history


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
    print("Trust Decay Models for Web4")
    print("Session 30, Track 6")
    print("=" * 70)

    # ── §1 Exponential Decay ──────────────────────────────────────
    print("\n§1 Exponential Decay\n")

    t = exponential_decay(1.0, 0.1, 0)
    check("exp_initial", abs(t - 1.0) < 0.001, f"t={t}")

    t10 = exponential_decay(1.0, 0.1, 10)
    check("exp_decays", t10 < 1.0, f"t10={t10:.4f}")

    # At half-life, should be ~0.5
    hl = half_life(0.1)
    t_hl = exponential_decay(1.0, 0.1, int(hl))
    check("exp_half_life", abs(t_hl - 0.5) < 0.05,
          f"t_hl={t_hl:.4f} hl={hl:.1f}")

    # Monotone decreasing
    values = [exponential_decay(1.0, 0.05, t) for t in range(100)]
    check("exp_monotone", all(values[i] >= values[i+1] for i in range(99)))

    # ── §2 Polynomial Decay ──────────────────────────────────────
    print("\n§2 Polynomial Decay\n")

    p0 = polynomial_decay(1.0, 0.1, 0)
    check("poly_initial", abs(p0 - 1.0) < 0.001)

    p50 = polynomial_decay(1.0, 0.1, 50)
    check("poly_slower_than_exp", p50 > exponential_decay(1.0, 0.1, 50),
          f"poly={p50:.4f} exp={exponential_decay(1.0, 0.1, 50):.4f}")

    # Polynomial has heavy tail (slower asymptotic decay)
    p200 = polynomial_decay(1.0, 0.1, 200)
    e200 = exponential_decay(1.0, 0.1, 200)
    check("poly_heavy_tail", p200 > e200,
          f"poly={p200:.6f} exp={e200:.6f}")

    # ── §3 Stepwise Decay ─────────────────────────────────────────
    print("\n§3 Stepwise Decay\n")

    s0 = stepwise_decay(1.0, 0.2, 10, 0)
    check("step_initial", abs(s0 - 1.0) < 0.001)

    s5 = stepwise_decay(1.0, 0.2, 10, 5)
    check("step_no_change_mid", abs(s5 - 1.0) < 0.001, f"s5={s5}")

    s10 = stepwise_decay(1.0, 0.2, 10, 10)
    check("step_drops_at_interval", abs(s10 - 0.8) < 0.001, f"s10={s10}")

    s50 = stepwise_decay(1.0, 0.2, 10, 50)
    check("step_five_drops", abs(s50 - 0.0) < 0.001, f"s50={s50}")

    # Floor at 0
    s100 = stepwise_decay(1.0, 0.2, 10, 100)
    check("step_floor_zero", s100 == 0.0)

    # ── §4 Logarithmic Decay ─────────────────────────────────────
    print("\n§4 Logarithmic Decay\n")

    l0 = logarithmic_decay(1.0, 0.5, 0)
    check("log_initial", abs(l0 - 1.0) < 0.001)

    # Log decay is slowest of all
    l100 = logarithmic_decay(1.0, 0.5, 100)
    p100 = polynomial_decay(1.0, 0.1, 100)
    check("log_slowest", l100 > p100,
          f"log={l100:.4f} poly={p100:.4f}")

    # ── §5 Decay with Floor ───────────────────────────────────────
    print("\n§5 Decay with Floor\n")

    floor_val = decay_with_floor(exponential_decay, 0.1, 1.0, 0.1, 100)
    check("floor_applied", floor_val >= 0.1,
          f"val={floor_val:.4f}")

    floor_early = decay_with_floor(exponential_decay, 0.1, 1.0, 0.1, 0)
    check("floor_not_early", floor_early == 1.0)

    # ── §6 Activity-Dependent Decay ───────────────────────────────
    print("\n§6 Activity-Dependent Decay\n")

    tracker = ActivityTracker(base_decay_rate=0.02, activity_boost=0.01)

    # Active entity
    active_history = tracker.compute_trust(
        0.7, 100,
        activity_times=list(range(0, 100, 5))  # active every 5 steps
    )

    # Inactive entity
    inactive_history = tracker.compute_trust(0.7, 100, activity_times=[])

    # Active entity maintains higher trust
    check("active_higher_trust", active_history[-1] > inactive_history[-1],
          f"active={active_history[-1]:.4f} inactive={inactive_history[-1]:.4f}")

    # Inactive entity eventually drops low
    check("inactive_decays", inactive_history[-1] < 0.5,
          f"val={inactive_history[-1]:.4f}")

    # Active entity doesn't hit zero
    check("active_above_zero", active_history[-1] > 0.1,
          f"val={active_history[-1]:.4f}")

    # ── §7 Context-Dependent Decay ────────────────────────────────
    print("\n§7 Context-Dependent Decay\n")

    t_fin = context_dependent_decay(0.8, TrustContext.FINANCIAL, 50)
    t_soc = context_dependent_decay(0.8, TrustContext.SOCIAL, 50)
    t_con = context_dependent_decay(0.8, TrustContext.CONTENT, 50)

    # Financial decays fastest
    check("financial_fastest", t_fin < t_soc,
          f"fin={t_fin:.4f} soc={t_soc:.4f}")

    # Content decays slowest
    check("content_slowest", t_con > t_soc,
          f"con={t_con:.4f} soc={t_soc:.4f}")

    # All positive
    check("all_positive", t_fin > 0 and t_soc > 0 and t_con > 0)

    # ── §8 Parameter Optimization ─────────────────────────────────
    print("\n§8 Decay Parameter Optimization\n")

    rate = optimal_decay_rate(50)
    hl_computed = half_life(rate)
    check("optimal_rate_correct", abs(hl_computed - 50) < 0.1,
          f"hl={hl_computed:.2f}")

    rate_fast = optimal_decay_rate(10)
    rate_slow = optimal_decay_rate(100)
    check("fast_higher_rate", rate_fast > rate_slow,
          f"fast={rate_fast:.4f} slow={rate_slow:.4f}")

    # Time to threshold
    ttt = time_to_threshold(1.0, 0.1, 0.5)
    check("time_to_threshold", abs(ttt - half_life(0.1)) < 0.1,
          f"ttt={ttt:.2f} hl={half_life(0.1):.2f}")

    # Already below threshold → 0
    ttt_zero = time_to_threshold(0.3, 0.1, 0.5)
    check("already_below", ttt_zero == 0.0)

    # ── §9 Comparative Analysis ───────────────────────────────────
    print("\n§9 Comparative Decay Models\n")

    comparison = compare_decay_models(1.0, 100)

    # All start at 1.0
    for name, values in comparison.items():
        check(f"{name}_starts_at_1", abs(values[0] - 1.0) < 0.01,
              f"val={values[0]}")

    # Area under curve: all models positive
    auc_exp = decay_area_under_curve(comparison["exponential"])
    auc_poly = decay_area_under_curve(comparison["polynomial"])
    auc_log = decay_area_under_curve(comparison["logarithmic"])
    check("auc_all_positive", auc_exp > 0 and auc_poly > 0 and auc_log > 0,
          f"exp={auc_exp:.1f} poly={auc_poly:.1f} log={auc_log:.1f}")
    # Logarithmic and polynomial have similar AUC (both heavy-tailed)
    check("auc_log_poly_similar", abs(auc_log - auc_poly) / max(auc_log, auc_poly) < 0.5,
          f"log={auc_log:.1f} poly={auc_poly:.1f}")

    # ── §10 Trust Renewal ─────────────────────────────────────────
    print("\n§10 Trust with Renewal\n")

    # No renewal → just decay
    no_renewal = trust_with_renewal(0.8, 0.02, 100, [])
    check("no_renewal_decays", no_renewal[-1] < no_renewal[0],
          f"start={no_renewal[0]:.3f} end={no_renewal[-1]:.3f}")

    # Periodic renewal maintains trust
    with_renewal = trust_with_renewal(0.8, 0.02, 100,
                                       renewal_times=list(range(20, 100, 20)),
                                       renewal_boost=0.15)
    check("renewal_maintains", with_renewal[-1] > no_renewal[-1],
          f"with={with_renewal[-1]:.3f} without={no_renewal[-1]:.3f}")

    # Renewal creates sawtooth pattern
    has_increase = any(with_renewal[i+1] > with_renewal[i]
                       for i in range(len(with_renewal) - 1))
    check("renewal_sawtooth", has_increase)

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
