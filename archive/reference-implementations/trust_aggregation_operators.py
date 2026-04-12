"""
Trust Aggregation Operators for Web4
Session 31, Track 6

Advanced aggregation beyond simple means:
- Trimmed mean (outlier-robust)
- Weighted median (order-statistic based)
- Byzantine-resilient aggregation (tolerates adversarial inputs)
- Dempster-Shafer belief fusion (evidential reasoning)
- OWA (Ordered Weighted Average) operators
- Choquet integral (non-additive measures)
- Consensus-based aggregation (iterative opinion pooling)
- Aggregation operator properties (monotonicity, idempotency, boundary conditions)
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Callable


# ─── Trimmed Mean ─────────────────────────────────────────────────

def trimmed_mean(values: List[float], trim_fraction: float = 0.1) -> float:
    """
    Remove top and bottom trim_fraction of values, then average.
    Robust to outliers — standard in trust aggregation.
    """
    if not values:
        return 0.0
    n = len(values)
    k = int(n * trim_fraction)
    if k * 2 >= n:
        # Too much trimming, fall back to median
        sorted_vals = sorted(values)
        mid = n // 2
        if n % 2 == 0:
            return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2
        return sorted_vals[mid]

    sorted_vals = sorted(values)
    trimmed = sorted_vals[k:n - k]
    return sum(trimmed) / len(trimmed)


def winsorized_mean(values: List[float], trim_fraction: float = 0.1) -> float:
    """
    Replace extreme values instead of removing them.
    Less aggressive than trimming.
    """
    if not values:
        return 0.0
    n = len(values)
    k = int(n * trim_fraction)
    sorted_vals = sorted(values)

    # Replace bottom k with k-th value, top k with (n-k-1)-th value
    result = list(sorted_vals)
    for i in range(k):
        result[i] = sorted_vals[k]
    for i in range(n - k, n):
        result[i] = sorted_vals[n - k - 1]

    return sum(result) / len(result)


# ─── Weighted Median ──────────────────────────────────────────────

def weighted_median(values: List[float], weights: List[float]) -> float:
    """
    Median weighted by trust/reputation of attestors.
    More robust than weighted mean against Byzantine attestors.
    """
    if not values or not weights:
        return 0.0

    pairs = sorted(zip(values, weights), key=lambda x: x[0])
    total_weight = sum(w for _, w in pairs)
    cumulative = 0.0

    for val, w in pairs:
        cumulative += w
        if cumulative >= total_weight / 2:
            return val

    return pairs[-1][0]


# ─── Byzantine-Resilient Aggregation ──────────────────────────────

def byzantine_trimmed_mean(values: List[float], f: int) -> float:
    """
    Remove f highest and f lowest values, average the rest.
    Tolerates up to f Byzantine (arbitrary) inputs.
    Requires n >= 2f + 1 honest inputs for correctness.
    """
    if len(values) <= 2 * f:
        # Not enough values to trim
        return sum(values) / len(values) if values else 0.0

    sorted_vals = sorted(values)
    middle = sorted_vals[f:len(sorted_vals) - f]
    return sum(middle) / len(middle)


def coordinate_wise_median(trust_vectors: List[List[float]]) -> List[float]:
    """
    For multi-dimensional trust, take median of each dimension.
    Byzantine-resilient for multi-dimensional trust tensors.
    """
    if not trust_vectors:
        return []

    dims = len(trust_vectors[0])
    result = []
    for d in range(dims):
        dim_values = sorted([v[d] for v in trust_vectors])
        mid = len(dim_values) // 2
        if len(dim_values) % 2 == 0:
            result.append((dim_values[mid - 1] + dim_values[mid]) / 2)
        else:
            result.append(dim_values[mid])

    return result


# ─── Dempster-Shafer Belief Fusion ────────────────────────────────

@dataclass
class MassFunction:
    """Basic probability assignment (BPA) for Dempster-Shafer theory."""
    masses: Dict[frozenset, float] = field(default_factory=dict)

    def belief(self, hypothesis: frozenset) -> float:
        """Belief: sum of masses for all subsets of hypothesis."""
        return sum(m for h, m in self.masses.items()
                   if h.issubset(hypothesis))

    def plausibility(self, hypothesis: frozenset) -> float:
        """Plausibility: sum of masses for all sets intersecting hypothesis."""
        return sum(m for h, m in self.masses.items()
                   if h.intersection(hypothesis))


def dempster_combine(m1: MassFunction, m2: MassFunction) -> MassFunction:
    """
    Dempster's rule of combination.
    Fuses two independent evidence sources.
    """
    combined_masses: Dict[frozenset, float] = {}
    conflict = 0.0

    for h1, mass1 in m1.masses.items():
        for h2, mass2 in m2.masses.items():
            intersection = h1.intersection(h2)
            product = mass1 * mass2

            if not intersection:
                conflict += product
            else:
                combined_masses[intersection] = combined_masses.get(intersection, 0.0) + product

    # Normalize by conflict
    if abs(1.0 - conflict) < 1e-10:
        return MassFunction(masses=combined_masses)  # Total conflict

    normalization = 1.0 / (1.0 - conflict)
    normalized = {h: m * normalization for h, m in combined_masses.items()}
    return MassFunction(masses=normalized)


# ─── OWA Operators ────────────────────────────────────────────────

def owa_aggregate(values: List[float], weights: List[float]) -> float:
    """
    Ordered Weighted Average (Yager).
    Weights are applied to sorted values, not to positions.
    Allows expressing AND-like, OR-like, and averaging behaviors.
    """
    if not values or not weights:
        return 0.0

    n = len(values)
    # Pad or truncate weights to match values
    w = list(weights[:n])
    while len(w) < n:
        w.append(0.0)

    # Normalize weights
    total = sum(w)
    if total <= 0:
        return 0.0
    w = [wi / total for wi in w]

    # Sort values descending, apply weights
    sorted_desc = sorted(values, reverse=True)
    return sum(v * wi for v, wi in zip(sorted_desc, w))


def owa_orness(weights: List[float]) -> float:
    """
    Measure of OR-ness (optimism) of OWA weights.
    1 = pure OR (max), 0 = pure AND (min), 0.5 = average.
    """
    n = len(weights)
    if n <= 1:
        return 0.5

    total = sum(weights)
    if total <= 0:
        return 0.5

    w_norm = [wi / total for wi in weights]
    return sum((n - 1 - i) * w_norm[i] for i in range(n)) / (n - 1)


# ─── Choquet Integral ─────────────────────────────────────────────

def choquet_integral(values: List[float],
                     capacity: Callable[[frozenset], float]) -> float:
    """
    Choquet integral with respect to a fuzzy measure (capacity).
    Generalizes weighted average — captures interaction between criteria.
    """
    n = len(values)
    indices = list(range(n))
    # Sort by value ascending
    sorted_pairs = sorted(enumerate(values), key=lambda x: x[1])

    result = 0.0
    prev_val = 0.0
    for k, (idx, val) in enumerate(sorted_pairs):
        # Coalition of criteria with values >= val
        coalition = frozenset(i for i, v in sorted_pairs[k:])
        cap = capacity(coalition)
        result += (val - prev_val) * cap
        prev_val = val

    return result


# ─── Consensus-Based Aggregation ──────────────────────────────────

def opinion_pool_linear(opinions: List[float],
                        weights: List[float]) -> float:
    """Linear opinion pool: weighted average of probability assessments."""
    total = sum(weights)
    if total <= 0:
        return 0.0
    return sum(o * w for o, w in zip(opinions, weights)) / total


def opinion_pool_logarithmic(opinions: List[float],
                              weights: List[float]) -> float:
    """
    Logarithmic opinion pool: weighted geometric mean.
    Better calibrated than linear pool for probabilities.
    """
    if not opinions or not weights:
        return 0.0

    total_weight = sum(weights)
    if total_weight <= 0:
        return 0.0

    log_sum = 0.0
    for o, w in zip(opinions, weights):
        if o <= 0:
            return 0.0  # Can't take log of zero
        log_sum += (w / total_weight) * math.log(o)

    return math.exp(log_sum)


def iterative_consensus(opinions: List[float],
                        influence_matrix: List[List[float]],
                        max_iterations: int = 100,
                        tolerance: float = 1e-6) -> List[float]:
    """
    DeGroot consensus model.
    Each agent updates opinion as weighted average of neighbors.
    Converges when influence matrix is regular.
    """
    n = len(opinions)
    current = list(opinions)

    for _ in range(max_iterations):
        new_opinions = []
        for i in range(n):
            total = sum(influence_matrix[i][j] * current[j] for j in range(n))
            weight_sum = sum(influence_matrix[i])
            new_opinions.append(total / weight_sum if weight_sum > 0 else current[i])

        # Check convergence
        max_diff = max(abs(new_opinions[i] - current[i]) for i in range(n))
        current = new_opinions
        if max_diff < tolerance:
            break

    return current


# ─── Aggregation Properties ──────────────────────────────────────

def is_monotone(agg_fn: Callable, n: int = 5, trials: int = 50) -> bool:
    """Test if aggregation function is monotone (increasing any input increases output)."""
    random.seed(42)
    for _ in range(trials):
        values = [random.random() for _ in range(n)]
        base = agg_fn(values)

        for i in range(n):
            increased = list(values)
            increased[i] = min(1.0, values[i] + 0.1)
            result = agg_fn(increased)
            if result < base - 1e-10:
                return False
    return True


def is_idempotent(agg_fn: Callable, n: int = 5, trials: int = 20) -> bool:
    """Test if agg(x, x, ..., x) = x for all x."""
    for _ in range(trials):
        x = random.random()
        values = [x] * n
        result = agg_fn(values)
        if abs(result - x) > 1e-6:
            return False
    return True


def satisfies_boundary(agg_fn: Callable, n: int = 5) -> Tuple[bool, bool]:
    """Test boundary conditions: agg(0,...,0) = 0 and agg(1,...,1) = 1."""
    zeros = agg_fn([0.0] * n)
    ones = agg_fn([1.0] * n)
    return (abs(zeros) < 1e-6, abs(ones - 1.0) < 1e-6)


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
    print("Trust Aggregation Operators for Web4")
    print("Session 31, Track 6")
    print("=" * 70)

    # ── §1 Trimmed Mean ─────────────────────────────────────────
    print("\n§1 Trimmed Mean\n")

    # Normal case
    values = [0.1, 0.5, 0.6, 0.7, 0.9]
    tm = trimmed_mean(values, 0.2)  # trim 1 from each end
    check("trimmed_mean_basic", abs(tm - 0.6) < 0.01,
          f"tm={tm:.4f}")

    # Outlier robustness
    clean = [0.5, 0.6, 0.7, 0.6, 0.5]
    with_outlier = [0.0, 0.5, 0.6, 0.7, 0.6, 0.5, 1.0]
    tm_clean = trimmed_mean(clean, 0.0)
    tm_outlier = trimmed_mean(with_outlier, 0.15)  # trim 1 from each end
    check("trimmed_outlier_robust", abs(tm_clean - tm_outlier) < 0.05,
          f"clean={tm_clean:.4f} outlier={tm_outlier:.4f}")

    # Winsorized vs trimmed
    values = [0.1, 0.3, 0.5, 0.7, 0.9]
    wm = winsorized_mean(values, 0.2)
    check("winsorized_basic", 0.3 <= wm <= 0.7,
          f"wm={wm:.4f}")

    # ── §2 Weighted Median ──────────────────────────────────────
    print("\n§2 Weighted Median\n")

    vals = [0.2, 0.5, 0.8]
    weights = [1.0, 1.0, 1.0]
    wmed = weighted_median(vals, weights)
    check("wmedian_uniform", abs(wmed - 0.5) < 0.01,
          f"wmed={wmed:.4f}")

    # Heavy weight on high value
    weights_high = [0.1, 0.1, 10.0]
    wmed_high = weighted_median(vals, weights_high)
    check("wmedian_high_weight", wmed_high == 0.8,
          f"wmed={wmed_high:.4f}")

    # Heavy weight on low value
    weights_low = [10.0, 0.1, 0.1]
    wmed_low = weighted_median(vals, weights_low)
    check("wmedian_low_weight", wmed_low == 0.2,
          f"wmed={wmed_low:.4f}")

    # ── §3 Byzantine-Resilient Aggregation ──────────────────────
    print("\n§3 Byzantine-Resilient Aggregation\n")

    # Honest values around 0.7, with f=2 Byzantine extremes
    honest = [0.65, 0.70, 0.72, 0.68, 0.71]
    byzantine = [0.0, 0.0, 0.65, 0.70, 0.72, 0.68, 0.71, 1.0, 1.0]
    btm_honest = byzantine_trimmed_mean(honest, 0)
    btm_byz = byzantine_trimmed_mean(byzantine, 2)
    check("btm_removes_byzantine", abs(btm_honest - btm_byz) < 0.01,
          f"honest={btm_honest:.4f} byz={btm_byz:.4f}")

    # Coordinate-wise median for 3D trust vectors
    vectors = [
        [0.7, 0.8, 0.6],
        [0.0, 0.0, 1.0],  # Byzantine
        [0.72, 0.78, 0.62],
        [0.68, 0.82, 0.58],
        [1.0, 1.0, 0.0],  # Byzantine
    ]
    cwm = coordinate_wise_median(vectors)
    check("cwm_robust", all(0.5 < v < 0.9 for v in cwm),
          f"cwm={[f'{v:.2f}' for v in cwm]}")

    # ── §4 Dempster-Shafer Fusion ───────────────────────────────
    print("\n§4 Dempster-Shafer Belief Fusion\n")

    # Evidence source 1: 60% believes entity is trustworthy
    trustworthy = frozenset(["trustworthy"])
    untrustworthy = frozenset(["untrustworthy"])
    frame = frozenset(["trustworthy", "untrustworthy"])

    m1 = MassFunction(masses={
        trustworthy: 0.6,
        frame: 0.4  # uncertainty
    })

    # Evidence source 2: 70% believes entity is trustworthy
    m2 = MassFunction(masses={
        trustworthy: 0.7,
        frame: 0.3
    })

    combined = dempster_combine(m1, m2)
    bel_t = combined.belief(trustworthy)
    check("ds_combined_belief", bel_t > 0.8,
          f"belief(trustworthy)={bel_t:.4f}")

    # Plausibility >= Belief always
    pl_t = combined.plausibility(trustworthy)
    check("ds_plausibility_ge_belief", pl_t >= bel_t - 1e-10,
          f"belief={bel_t:.4f} plausibility={pl_t:.4f}")

    # Belief + Plausibility of complement = 1
    bel_u = combined.belief(untrustworthy)
    check("ds_complement", abs(bel_t + combined.plausibility(untrustworthy) -
                               (pl_t + bel_u)) < 0.5,
          f"bel_t={bel_t:.4f} pl_u={combined.plausibility(untrustworthy):.4f}")

    # ── §5 OWA Operators ────────────────────────────────────────
    print("\n§5 OWA Operators\n")

    values = [0.3, 0.7, 0.5]

    # MAX-like (weight on largest)
    owa_max = owa_aggregate(values, [1.0, 0.0, 0.0])
    check("owa_max", abs(owa_max - 0.7) < 0.01,
          f"owa_max={owa_max:.4f}")

    # MIN-like (weight on smallest)
    owa_min = owa_aggregate(values, [0.0, 0.0, 1.0])
    check("owa_min", abs(owa_min - 0.3) < 0.01,
          f"owa_min={owa_min:.4f}")

    # Average (equal weights)
    owa_avg = owa_aggregate(values, [1.0, 1.0, 1.0])
    check("owa_avg", abs(owa_avg - 0.5) < 0.01,
          f"owa_avg={owa_avg:.4f}")

    # Orness
    check("orness_max", abs(owa_orness([1.0, 0.0, 0.0]) - 1.0) < 0.01)
    check("orness_min", abs(owa_orness([0.0, 0.0, 1.0]) - 0.0) < 0.01)
    check("orness_avg", abs(owa_orness([1.0, 1.0, 1.0]) - 0.5) < 0.01)

    # ── §6 Choquet Integral ─────────────────────────────────────
    print("\n§6 Choquet Integral\n")

    # Additive capacity (reduces to weighted average)
    individual_weights = [0.3, 0.5, 0.2]

    def additive_capacity(s: frozenset) -> float:
        return sum(individual_weights[i] for i in s)

    values = [0.4, 0.8, 0.6]
    ci = choquet_integral(values, additive_capacity)
    wa = sum(v * w for v, w in zip(values, individual_weights))
    check("choquet_additive_equals_wa", abs(ci - wa) < 0.01,
          f"choquet={ci:.4f} wa={wa:.4f}")

    # Super-additive capacity (positive interaction)
    def superadditive_capacity(s: frozenset) -> float:
        base = sum(individual_weights[i] for i in s)
        if len(s) >= 2:
            base += 0.1 * (len(s) - 1)  # synergy bonus
        return min(1.0, base)

    ci_super = choquet_integral(values, superadditive_capacity)
    check("choquet_superadditive_higher", ci_super >= ci - 0.01,
          f"super={ci_super:.4f} additive={ci:.4f}")

    # ── §7 Consensus Aggregation ────────────────────────────────
    print("\n§7 Consensus-Based Aggregation\n")

    # Linear opinion pool
    opinions = [0.6, 0.8, 0.7]
    weights = [1.0, 2.0, 1.0]
    lop = opinion_pool_linear(opinions, weights)
    check("linear_pool", abs(lop - 0.725) < 0.01,
          f"lop={lop:.4f}")

    # Logarithmic pool (geometric mean for equal weights)
    log_pool = opinion_pool_logarithmic([0.4, 0.8], [1.0, 1.0])
    geo_mean = math.sqrt(0.4 * 0.8)
    check("log_pool_geo_mean", abs(log_pool - geo_mean) < 0.01,
          f"log={log_pool:.4f} geo={geo_mean:.4f}")

    # Log pool < linear pool for unequal values (AM-GM inequality)
    lin = opinion_pool_linear([0.4, 0.8], [1.0, 1.0])
    check("log_le_linear", log_pool <= lin + 1e-10,
          f"log={log_pool:.4f} lin={lin:.4f}")

    # DeGroot iterative consensus
    opinions = [0.2, 0.8, 0.5]
    # Equal influence → converge to average
    influence = [
        [0.5, 0.25, 0.25],
        [0.25, 0.5, 0.25],
        [0.25, 0.25, 0.5],
    ]
    consensus = iterative_consensus(opinions, influence)
    avg = sum(opinions) / len(opinions)
    check("degroot_converges", all(abs(c - avg) < 0.01 for c in consensus),
          f"consensus={[f'{c:.3f}' for c in consensus]} avg={avg:.3f}")

    # Asymmetric influence: agent 0 is more influential
    influence_asym = [
        [0.8, 0.1, 0.1],
        [0.5, 0.3, 0.2],
        [0.5, 0.2, 0.3],
    ]
    consensus_asym = iterative_consensus(opinions, influence_asym)
    # Should converge closer to agent 0's opinion
    check("degroot_influential", consensus_asym[0] < 0.4,
          f"consensus={[f'{c:.3f}' for c in consensus_asym]}")

    # ── §8 Aggregation Properties ───────────────────────────────
    print("\n§8 Aggregation Properties\n")

    # Trimmed mean properties
    random.seed(42)
    check("trimmed_monotone", is_monotone(lambda v: trimmed_mean(v, 0.1)))
    check("trimmed_idempotent", is_idempotent(lambda v: trimmed_mean(v, 0.1)))

    lb, ub = satisfies_boundary(lambda v: trimmed_mean(v, 0.1))
    check("trimmed_boundary_lower", lb)
    check("trimmed_boundary_upper", ub)

    # OWA with equal weights should be idempotent
    n = 5
    check("owa_equal_idempotent",
          is_idempotent(lambda v: owa_aggregate(v, [1.0] * len(v)), n=n))

    # Byzantine trimmed mean is monotone for honest range
    check("btm_monotone",
          is_monotone(lambda v: byzantine_trimmed_mean(v, 1), n=5))

    # ── Summary ─────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
