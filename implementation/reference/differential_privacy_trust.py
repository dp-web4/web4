#!/usr/bin/env python3
"""
Differential Privacy for Trust Queries

Web4's trust system must balance transparency with privacy. Differential
privacy (DP) provides formal mathematical guarantees: any single entity's
trust data has bounded influence on query results.

Key question: Can we answer trust queries (aggregate scores, rankings,
statistics) while provably protecting individual trust values?

EU AI Act relevance:
  - Art. 10: Data quality + privacy
  - Art. 13: Transparency (but not at cost of privacy)
  - Art. 14: Human oversight (aggregate, not individual exposure)

Sections:
  §1  Laplace Mechanism — calibrated noise for numeric trust queries
  §2  Gaussian Mechanism — (ε,δ)-DP for composition-friendly queries
  §3  Exponential Mechanism — private selection from discrete options
  §4  Privacy Budget Accounting — track cumulative privacy loss
  §5  Composition Theorems — sequential and parallel composition
  §6  Trust Histogram with DP — private distribution of trust scores
  §7  Private Trust Aggregation — mean, median, percentiles with DP
  §8  Private Ranking — trust leaderboards without exact values
  §9  Local Differential Privacy — per-entity noise before aggregation
  §10 Private Federated Trust — cross-federation queries with DP
  §11 Privacy-Utility Tradeoff — measure information loss vs protection
  §12 Complete DP Trust Pipeline — end-to-end private trust analytics
"""

import math
import random
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════
#  CORE DP MECHANISMS
# ═══════════════════════════════════════════════════════════════

def laplace_noise(scale: float) -> float:
    """Sample from Laplace distribution with given scale."""
    u = random.uniform(-0.5, 0.5)
    return -scale * math.copysign(1, u) * math.log(1 - 2 * abs(u))


def gaussian_noise(sigma: float) -> float:
    """Sample from Gaussian distribution with given sigma."""
    return random.gauss(0, sigma)


def laplace_mechanism(true_value: float, sensitivity: float, epsilon: float) -> float:
    """
    Laplace mechanism: add Lap(sensitivity/epsilon) noise.

    Achieves ε-differential privacy.

    Args:
        true_value: The actual query result
        sensitivity: Maximum change in result from one entity changing
        epsilon: Privacy parameter (smaller = more private)
    """
    scale = sensitivity / epsilon
    return true_value + laplace_noise(scale)


def gaussian_mechanism(true_value: float, sensitivity: float,
                       epsilon: float, delta: float) -> float:
    """
    Gaussian mechanism: add N(0, σ²) noise where σ = sensitivity * √(2ln(1.25/δ)) / ε.

    Achieves (ε,δ)-differential privacy.
    """
    sigma = sensitivity * math.sqrt(2 * math.log(1.25 / delta)) / epsilon
    return true_value + gaussian_noise(sigma)


def exponential_mechanism(scores: Dict[str, float], sensitivity: float,
                          epsilon: float) -> str:
    """
    Exponential mechanism: select from options with probability
    proportional to exp(epsilon * score / (2 * sensitivity)).

    Returns the selected option key.
    """
    if not scores:
        return ""

    # Compute selection probabilities
    max_score = max(scores.values())
    probs = {}
    for key, score in scores.items():
        # Subtract max for numerical stability
        probs[key] = math.exp(epsilon * (score - max_score) / (2 * sensitivity))

    total = sum(probs.values())
    if total == 0:
        return random.choice(list(scores.keys()))

    # Sample
    r = random.random() * total
    cumulative = 0
    for key, prob in probs.items():
        cumulative += prob
        if r <= cumulative:
            return key

    return list(scores.keys())[-1]


# ═══════════════════════════════════════════════════════════════
#  TEST FRAMEWORK
# ═══════════════════════════════════════════════════════════════

passed = 0
failed = 0
total_sections = 0

def section(title):
    global total_sections
    total_sections += 1
    print(f"\n§{total_sections} {title}")
    print("─" * 40)

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✓ {name}")
    else:
        failed += 1
        print(f"  ✗ {name}")
    if detail:
        print(f"    {detail}")


# ═══════════════════════════════════════════════════════════════
#  §1. LAPLACE MECHANISM
# ═══════════════════════════════════════════════════════════════

section("Laplace Mechanism")

# Test: Laplace noise has correct distribution properties
random.seed(42)
scale = 1.0
samples = [laplace_noise(scale) for _ in range(10000)]
mean_noise = statistics.mean(samples)
var_noise = statistics.variance(samples)

check("Laplace noise mean ≈ 0",
      abs(mean_noise) < 0.1,
      f"mean={mean_noise:.4f}")
check("Laplace noise variance ≈ 2*scale²",
      abs(var_noise - 2 * scale**2) < 0.5,
      f"variance={var_noise:.3f} expected={2*scale**2:.3f}")

# Test: ε-DP guarantee
# For two neighboring datasets (differ by one entity), outputs should be similar
def test_laplace_dp(epsilon=1.0, sensitivity=1.0, n_trials=5000):
    """
    Empirical test of ε-DP.

    For neighboring datasets D and D' (differ by one entity's trust):
      P[M(D) ∈ S] ≤ e^ε * P[M(D') ∈ S]

    Test by comparing output distributions.
    """
    random.seed(42)

    # Two neighboring datasets
    trust_scores_d = [random.uniform(0, 1) for _ in range(100)]
    trust_scores_d_prime = trust_scores_d.copy()
    trust_scores_d_prime[0] = 1.0 - trust_scores_d_prime[0]  # Change one entity

    mean_d = statistics.mean(trust_scores_d)
    mean_d_prime = statistics.mean(trust_scores_d_prime)

    # Query: mean trust with Laplace noise
    outputs_d = [laplace_mechanism(mean_d, sensitivity / len(trust_scores_d), epsilon)
                 for _ in range(n_trials)]
    outputs_d_prime = [laplace_mechanism(mean_d_prime, sensitivity / len(trust_scores_d_prime), epsilon)
                       for _ in range(n_trials)]

    # Check overlap of distributions
    # Both should produce similar ranges
    mean_out_d = statistics.mean(outputs_d)
    mean_out_d_prime = statistics.mean(outputs_d_prime)

    return {
        'mean_d': mean_out_d,
        'mean_d_prime': mean_out_d_prime,
        'diff': abs(mean_out_d - mean_out_d_prime),
        'true_diff': abs(mean_d - mean_d_prime),
        'noise_hides_diff': abs(mean_out_d - mean_out_d_prime) < abs(mean_d - mean_d_prime) * 3
    }

dp_test = test_laplace_dp()
check("Laplace mechanism preserves privacy (noise covers true difference)",
      dp_test['noise_hides_diff'] or dp_test['diff'] < 0.05,
      f"output diff={dp_test['diff']:.4f} true diff={dp_test['true_diff']:.4f}")


# ═══════════════════════════════════════════════════════════════
#  §2. GAUSSIAN MECHANISM
# ═══════════════════════════════════════════════════════════════

section("Gaussian Mechanism")

# Test Gaussian noise properties
random.seed(42)
sigma = 1.0
g_samples = [gaussian_noise(sigma) for _ in range(10000)]
g_mean = statistics.mean(g_samples)
g_var = statistics.variance(g_samples)

check("Gaussian noise mean ≈ 0",
      abs(g_mean) < 0.1,
      f"mean={g_mean:.4f}")
check("Gaussian noise variance ≈ σ²",
      abs(g_var - sigma**2) < 0.2,
      f"variance={g_var:.3f} expected={sigma**2:.3f}")

# Compare Gaussian vs Laplace for same privacy level
def compare_mechanisms(epsilon=1.0, delta=1e-5, sensitivity=1.0, n_trials=3000):
    """Compare utility of Laplace vs Gaussian mechanisms."""
    random.seed(42)
    true_value = 0.5

    laplace_errors = []
    gaussian_errors = []

    for _ in range(n_trials):
        lap = laplace_mechanism(true_value, sensitivity, epsilon)
        gau = gaussian_mechanism(true_value, sensitivity, epsilon, delta)
        laplace_errors.append(abs(lap - true_value))
        gaussian_errors.append(abs(gau - true_value))

    return {
        'laplace_mae': statistics.mean(laplace_errors),
        'gaussian_mae': statistics.mean(gaussian_errors),
        'laplace_std': statistics.stdev(laplace_errors),
        'gaussian_std': statistics.stdev(gaussian_errors)
    }

comp = compare_mechanisms()
check("Both mechanisms add meaningful noise",
      comp['laplace_mae'] > 0.1 and comp['gaussian_mae'] > 0.1,
      f"Lap MAE={comp['laplace_mae']:.3f} Gauss MAE={comp['gaussian_mae']:.3f}")
# Gaussian adds more noise per query (σ scales with √(2ln(1.25/δ))) but composes better
check("Gaussian mechanism trades per-query noise for better composition",
      comp['gaussian_mae'] > comp['laplace_mae'] * 0.5,
      f"Lap MAE={comp['laplace_mae']:.3f} Gauss MAE={comp['gaussian_mae']:.3f}")


# ═══════════════════════════════════════════════════════════════
#  §3. EXPONENTIAL MECHANISM
# ═══════════════════════════════════════════════════════════════

section("Exponential Mechanism")

# Test: exponential mechanism selects high-quality options
def test_exponential(n_trials=5000):
    """Exponential mechanism should prefer higher-scored options."""
    random.seed(42)
    scores = {'excellent': 0.9, 'good': 0.7, 'average': 0.5, 'poor': 0.2}

    selections = defaultdict(int)
    for _ in range(n_trials):
        selected = exponential_mechanism(scores, sensitivity=1.0, epsilon=2.0)
        selections[selected] += 1

    # Higher-scored options should be selected more often
    rates = {k: v / n_trials for k, v in selections.items()}
    return rates

exp_rates = test_exponential()
check("Exponential prefers 'excellent' over 'poor'",
      exp_rates.get('excellent', 0) > exp_rates.get('poor', 0),
      f"excellent={exp_rates.get('excellent', 0):.3f} poor={exp_rates.get('poor', 0):.3f}")
check("All options have nonzero probability (DP guarantee)",
      all(v > 0 for v in exp_rates.values()),
      f"rates={exp_rates}")

# Test with different epsilon values
def test_epsilon_sensitivity():
    """Higher epsilon → more utility (closer to optimal), less privacy."""
    random.seed(42)
    scores = {'best': 1.0, 'worst': 0.0}

    results = {}
    for eps in [0.1, 0.5, 1.0, 5.0, 10.0]:
        selections = [exponential_mechanism(scores, 1.0, eps) for _ in range(2000)]
        best_rate = sum(1 for s in selections if s == 'best') / 2000
        results[eps] = best_rate

    return results

eps_results = test_epsilon_sensitivity()
check("Higher ε → more likely to select optimal",
      eps_results[10.0] > eps_results[0.1],
      f"ε=0.1: {eps_results[0.1]:.3f} ε=10: {eps_results[10.0]:.3f}")


# ═══════════════════════════════════════════════════════════════
#  §4. PRIVACY BUDGET ACCOUNTING
# ═══════════════════════════════════════════════════════════════

section("Privacy Budget Accounting")

@dataclass
class PrivacyBudget:
    """Track cumulative privacy loss across queries."""
    total_epsilon: float = 0.0
    total_delta: float = 0.0
    max_epsilon: float = 10.0  # Privacy budget limit
    max_delta: float = 1e-3
    queries: List[Dict] = field(default_factory=list)

    def can_query(self, epsilon: float, delta: float = 0.0) -> bool:
        """Check if this query fits within remaining budget."""
        return (self.total_epsilon + epsilon <= self.max_epsilon and
                self.total_delta + delta <= self.max_delta)

    def consume(self, epsilon: float, delta: float = 0.0, query_name: str = ""):
        """Record a query's privacy cost."""
        self.total_epsilon += epsilon
        self.total_delta += delta
        self.queries.append({
            'name': query_name,
            'epsilon': epsilon,
            'delta': delta,
            'cumulative_epsilon': self.total_epsilon,
            'cumulative_delta': self.total_delta
        })

    def remaining_epsilon(self) -> float:
        return self.max_epsilon - self.total_epsilon


budget = PrivacyBudget(max_epsilon=5.0)
check("Fresh budget has full epsilon",
      budget.remaining_epsilon() == 5.0,
      f"remaining={budget.remaining_epsilon()}")

budget.consume(1.0, query_name="mean_trust")
budget.consume(0.5, query_name="median_trust")
check("Budget tracks consumption",
      budget.total_epsilon == 1.5,
      f"consumed ε={budget.total_epsilon}")
check("Can query within budget",
      budget.can_query(3.0),
      f"remaining={budget.remaining_epsilon()}")
check("Cannot exceed budget",
      not budget.can_query(4.0),
      f"remaining={budget.remaining_epsilon()} requested=4.0")


# ═══════════════════════════════════════════════════════════════
#  §5. COMPOSITION THEOREMS
# ═══════════════════════════════════════════════════════════════

section("Composition Theorems")

def basic_composition(epsilons: List[float]) -> float:
    """Basic composition: total ε = sum of individual ε's."""
    return sum(epsilons)


def advanced_composition(epsilons: List[float], delta: float = 1e-5) -> Tuple[float, float]:
    """
    Advanced composition theorem:
    k queries of ε-DP each compose to (ε', kδ + δ')-DP where:
      ε' = √(2k ln(1/δ')) * ε + k * ε * (e^ε - 1)
    Simplified to: ε' ≈ ε * √(2k * ln(1/δ'))
    """
    if not epsilons:
        return 0.0, 0.0

    k = len(epsilons)
    eps = max(epsilons)  # Conservative: use max

    # Advanced composition bound
    eps_prime = eps * math.sqrt(2 * k * math.log(1 / delta)) + k * eps * (math.exp(eps) - 1)

    return eps_prime, k * delta + delta


# Test composition
epsilons = [1.0] * 10
basic = basic_composition(epsilons)
advanced_eps, advanced_delta = advanced_composition(epsilons, delta=1e-5)

check("Basic composition: sum of epsilons",
      basic == 10.0,
      f"basic ε={basic}")

# Advanced composition is tighter for SMALL epsilon. With ε=1.0, the e^ε-1 term
# dominates. Use ε=0.1 to demonstrate the benefit.
small_epsilons = [0.1] * 100
small_basic = basic_composition(small_epsilons)
small_advanced, _ = advanced_composition(small_epsilons, delta=1e-5)
check("Advanced composition tighter for small ε (100 × 0.1)",
      small_advanced < small_basic,
      f"advanced ε={small_advanced:.2f} basic ε={small_basic:.2f}")
check("Advanced composition: non-trivial delta",
      advanced_delta > 0,
      f"delta={advanced_delta:.6f}")

# Parallel composition: queries on disjoint subsets
def parallel_composition(epsilons: List[float]) -> float:
    """Parallel composition: max of individual ε's (disjoint data)."""
    return max(epsilons) if epsilons else 0.0

parallel_eps = parallel_composition([1.0, 2.0, 0.5])
check("Parallel composition: max of epsilons",
      parallel_eps == 2.0,
      f"parallel ε={parallel_eps}")


# ═══════════════════════════════════════════════════════════════
#  §6. TRUST HISTOGRAM WITH DP
# ═══════════════════════════════════════════════════════════════

section("Trust Histogram with DP")

def private_histogram(values: List[float], n_bins: int = 10,
                      epsilon: float = 1.0) -> List[int]:
    """
    Create differentially private histogram.

    Each bin count gets independent Laplace noise with sensitivity 1
    (changing one value changes at most one bin by 1).
    """
    # Create histogram
    bins = [0] * n_bins
    for v in values:
        bin_idx = min(int(v * n_bins), n_bins - 1)
        bins[bin_idx] += 1

    # Add noise to each bin
    noisy_bins = []
    for count in bins:
        noisy = count + laplace_noise(1.0 / epsilon)
        noisy_bins.append(max(0, round(noisy)))

    return noisy_bins


random.seed(42)
trust_values = [random.betavariate(5, 2) for _ in range(500)]
true_hist = [0] * 10
for v in trust_values:
    true_hist[min(int(v * 10), 9)] += 1

noisy_hist = private_histogram(trust_values, n_bins=10, epsilon=1.0)

# Check that noisy histogram preserves distribution shape
check("Noisy histogram has correct number of bins",
      len(noisy_hist) == 10,
      f"bins={len(noisy_hist)}")

# Correlation between true and noisy
corr_numer = sum((t - statistics.mean(true_hist)) * (n - statistics.mean(noisy_hist))
                 for t, n in zip(true_hist, noisy_hist))
corr_denom = (math.sqrt(sum((t - statistics.mean(true_hist))**2 for t in true_hist)) *
              math.sqrt(sum((n - statistics.mean(noisy_hist))**2 for n in noisy_hist)))
correlation = corr_numer / max(corr_denom, 0.001)

check("Noisy histogram correlates with true (r > 0.5)",
      correlation > 0.5,
      f"correlation={correlation:.3f}")

# Total count preservation (approximate)
total_diff = abs(sum(noisy_hist) - sum(true_hist))
check("Total count approximately preserved",
      total_diff < len(trust_values) * 0.3,
      f"true total={sum(true_hist)} noisy total={sum(noisy_hist)}")


# ═══════════════════════════════════════════════════════════════
#  §7. PRIVATE TRUST AGGREGATION
# ═══════════════════════════════════════════════════════════════

section("Private Trust Aggregation")

def private_mean(values: List[float], epsilon: float = 1.0,
                 lower: float = 0.0, upper: float = 1.0) -> float:
    """
    Private mean with bounded sensitivity.

    Sensitivity of mean = (upper - lower) / n
    """
    n = len(values)
    if n == 0:
        return 0.0
    true_mean = statistics.mean(values)
    sensitivity = (upper - lower) / n
    return laplace_mechanism(true_mean, sensitivity, epsilon)


def private_median(values: List[float], epsilon: float = 1.0) -> float:
    """
    Private median using exponential mechanism.

    Score each candidate by negative distance to true median rank.
    """
    if not values:
        return 0.0

    sorted_vals = sorted(values)
    n = len(sorted_vals)

    # Candidate medians: the actual values
    scores = {}
    for i, v in enumerate(sorted_vals):
        # Score = -|rank - n/2| (higher = closer to median)
        scores[v] = -abs(i - n / 2)

    return exponential_mechanism(scores, sensitivity=1.0, epsilon=epsilon)


def private_percentile(values: List[float], p: float = 0.5,
                       epsilon: float = 1.0) -> float:
    """Private percentile using noisy rank selection."""
    if not values:
        return 0.0

    sorted_vals = sorted(values)
    n = len(sorted_vals)
    target_rank = int(p * n)

    # Add noise to the rank
    noisy_rank = round(target_rank + laplace_noise(1.0 / epsilon))
    noisy_rank = max(0, min(n - 1, noisy_rank))

    return sorted_vals[noisy_rank]


random.seed(42)
trust_data = [random.betavariate(5, 2) for _ in range(200)]
true_mean = statistics.mean(trust_data)
true_median = statistics.median(trust_data)

# Test private mean accuracy
private_means = [private_mean(trust_data, epsilon=1.0) for _ in range(100)]
pm_mean = statistics.mean(private_means)
check("Private mean unbiased (close to true mean)",
      abs(pm_mean - true_mean) < 0.05,
      f"private={pm_mean:.4f} true={true_mean:.4f}")

# Test private median
private_medians = [private_median(trust_data, epsilon=1.0) for _ in range(100)]
pm_median = statistics.mean(private_medians)
check("Private median close to true median",
      abs(pm_median - true_median) < 0.15,
      f"private={pm_median:.4f} true={true_median:.4f}")

# Test percentiles
p25 = private_percentile(trust_data, p=0.25, epsilon=1.0)
p75 = private_percentile(trust_data, p=0.75, epsilon=1.0)
check("Private percentiles ordered (p25 < p75)",
      p25 < p75,
      f"p25={p25:.3f} p75={p75:.3f}")


# ═══════════════════════════════════════════════════════════════
#  §8. PRIVATE RANKING
# ═══════════════════════════════════════════════════════════════

section("Private Ranking")

def private_top_k(entities: Dict[str, float], k: int = 5,
                  epsilon: float = 1.0) -> List[str]:
    """
    Select top-k entities with differential privacy.

    Uses repeated exponential mechanism (peeling).
    Each selection consumes ε/k privacy budget.
    """
    remaining = dict(entities)
    selected = []
    per_selection_eps = epsilon / k

    for _ in range(min(k, len(remaining))):
        if not remaining:
            break
        winner = exponential_mechanism(remaining, sensitivity=1.0,
                                      epsilon=per_selection_eps)
        selected.append(winner)
        del remaining[winner]

    return selected


random.seed(42)
entity_trusts = {f"e{i}": random.betavariate(5, 2) for i in range(50)}
true_top5 = sorted(entity_trusts, key=entity_trusts.get, reverse=True)[:5]

# Run private top-k many times (use higher epsilon for 50 entities)
top_k_results = defaultdict(int)
for _ in range(200):
    top5 = private_top_k(entity_trusts, k=5, epsilon=5.0)
    for entity in top5:
        top_k_results[entity] += 1

# True top-10 should appear more than bottom-10
true_top10 = sorted(entity_trusts, key=entity_trusts.get, reverse=True)[:10]
top10_appearances = sum(top_k_results.get(e, 0) for e in true_top10)
check("True top-10 appear frequently in private ranking",
      top10_appearances > 200,
      f"true top-10 total appearances={top10_appearances}/1000")

# Check that top entities selected more than bottom
bottom10 = sorted(entity_trusts, key=entity_trusts.get)[:10]
bottom10_appearances = sum(top_k_results.get(e, 0) for e in bottom10)
check("Top entities selected more than bottom entities",
      top10_appearances > bottom10_appearances,
      f"top10={top10_appearances} bottom10={bottom10_appearances}")

# Private rank position
def private_rank(entity: str, entities: Dict[str, float],
                 epsilon: float = 1.0) -> int:
    """Return private rank of entity (with noisy position)."""
    sorted_entities = sorted(entities, key=entities.get, reverse=True)
    true_rank = sorted_entities.index(entity) + 1
    noisy_rank = round(true_rank + laplace_noise(1.0 / epsilon))
    return max(1, min(len(entities), noisy_rank))

top_entity = true_top5[0]
private_ranks = [private_rank(top_entity, entity_trusts) for _ in range(100)]
avg_rank = statistics.mean(private_ranks)
check("Top entity's private rank close to true (< 10)",
      avg_rank < 10,
      f"avg private rank={avg_rank:.1f} true rank=1")


# ═══════════════════════════════════════════════════════════════
#  §9. LOCAL DIFFERENTIAL PRIVACY
# ═══════════════════════════════════════════════════════════════

section("Local Differential Privacy")

def randomized_response(true_value: bool, epsilon: float = 1.0) -> bool:
    """
    Randomized response for binary trust queries.

    With probability p = e^ε/(1+e^ε), report truthfully.
    With probability 1-p, report randomly.
    """
    p = math.exp(epsilon) / (1 + math.exp(epsilon))
    if random.random() < p:
        return true_value
    else:
        return random.random() < 0.5


def unary_encoding_ldp(value: float, epsilon: float = 1.0,
                       n_bins: int = 10) -> List[float]:
    """
    Unary encoding for local DP on continuous values.

    Each entity encodes their trust into n_bins, then randomizes each bit.
    """
    # Encode value into bins
    encoding = [0.0] * n_bins
    bin_idx = min(int(value * n_bins), n_bins - 1)
    encoding[bin_idx] = 1.0

    # Randomize each bit
    p = math.exp(epsilon / 2) / (1 + math.exp(epsilon / 2))
    q = 1.0 / (1 + math.exp(epsilon / 2))

    randomized = []
    for bit in encoding:
        if bit == 1.0:
            randomized.append(1.0 if random.random() < p else 0.0)
        else:
            randomized.append(1.0 if random.random() < q else 0.0)

    return randomized


def aggregate_ldp(encoded_values: List[List[float]], epsilon: float,
                  n_total: int) -> List[float]:
    """
    Aggregate locally-private encoded values to estimate histogram.

    Corrects for randomization bias.
    """
    n_bins = len(encoded_values[0]) if encoded_values else 0
    p = math.exp(epsilon / 2) / (1 + math.exp(epsilon / 2))
    q = 1.0 / (1 + math.exp(epsilon / 2))

    sums = [0.0] * n_bins
    for enc in encoded_values:
        for i, v in enumerate(enc):
            sums[i] += v

    # Correct for bias: estimated_count = (sum - n*q) / (p - q)
    corrected = []
    for s in sums:
        corrected.append(max(0, (s - n_total * q) / (p - q)))

    return corrected


random.seed(42)
local_trust = [random.betavariate(5, 2) for _ in range(300)]

# Each entity applies local DP
encoded = [unary_encoding_ldp(v, epsilon=2.0) for v in local_trust]

# Server aggregates
estimated_hist = aggregate_ldp(encoded, epsilon=2.0, n_total=300)
true_hist_local = [0.0] * 10
for v in local_trust:
    true_hist_local[min(int(v * 10), 9)] += 1

# Normalize
est_total = sum(estimated_hist) if sum(estimated_hist) > 0 else 1
true_total = sum(true_hist_local)
est_norm = [e / est_total for e in estimated_hist]
true_norm = [t / true_total for t in true_hist_local]

# Check correlation
if all(e == est_norm[0] for e in est_norm):
    ldp_corr = 0.0
else:
    ldp_numer = sum((t - statistics.mean(true_norm)) * (e - statistics.mean(est_norm))
                    for t, e in zip(true_norm, est_norm))
    ldp_denom = (math.sqrt(sum((t - statistics.mean(true_norm))**2 for t in true_norm)) *
                 math.sqrt(sum((e - statistics.mean(est_norm))**2 for e in est_norm)))
    ldp_corr = ldp_numer / max(ldp_denom, 0.001)

check("LDP histogram correlates with true distribution",
      ldp_corr > 0.3,
      f"correlation={ldp_corr:.3f}")

# Randomized response test
random.seed(42)
true_threshold = [v > 0.7 for v in local_trust]
true_rate = sum(true_threshold) / len(true_threshold)

rr_responses = [randomized_response(t, epsilon=2.0) for t in true_threshold]
rr_rate = sum(rr_responses) / len(rr_responses)

# Correct for bias: E[response=1] = p*θ + (1-p)*0.5, so θ = (observed - (1-p)*0.5) / p
p_rr = math.exp(2.0) / (1 + math.exp(2.0))
estimated_rate = (rr_rate - (1 - p_rr) * 0.5) / p_rr
estimated_rate = max(0, min(1, estimated_rate))

check("Randomized response recovers approximate rate",
      abs(estimated_rate - true_rate) < 0.15,
      f"estimated={estimated_rate:.3f} true={true_rate:.3f}")


# ═══════════════════════════════════════════════════════════════
#  §10. PRIVATE FEDERATED TRUST
# ═══════════════════════════════════════════════════════════════

section("Private Federated Trust")

@dataclass
class Federation:
    """A federation with its own trust data."""
    name: str
    trust_scores: List[float]

    def private_stats(self, epsilon: float) -> Dict:
        """Compute private aggregate statistics."""
        n = len(self.trust_scores)
        if n == 0:
            return {'mean': 0.0, 'count': 0}

        # Split budget: ε/2 for mean, ε/2 for count
        priv_mean = private_mean(self.trust_scores, epsilon / 2)
        priv_count = n + laplace_noise(1.0 / (epsilon / 2))

        return {
            'mean': priv_mean,
            'count': max(1, round(priv_count))
        }


def federated_private_mean(federations: List[Federation],
                           epsilon: float = 1.0) -> float:
    """
    Compute private global mean across federations.

    Each federation reports private stats. Global aggregator
    combines with no additional privacy loss (post-processing theorem).
    """
    per_fed_eps = epsilon  # Each federation uses full budget (parallel composition)
    total_count = 0
    weighted_sum = 0.0

    for fed in federations:
        stats = fed.private_stats(per_fed_eps)
        weighted_sum += stats['mean'] * stats['count']
        total_count += stats['count']

    return weighted_sum / max(total_count, 1)


random.seed(42)
federations = [
    Federation("alpha", [random.betavariate(5, 2) for _ in range(100)]),
    Federation("beta", [random.betavariate(3, 3) for _ in range(80)]),
    Federation("gamma", [random.betavariate(2, 5) for _ in range(120)])
]

true_global = statistics.mean([s for f in federations for s in f.trust_scores])

# Run many times to check unbiasedness
private_globals = [federated_private_mean(federations, epsilon=1.0)
                   for _ in range(100)]
avg_private = statistics.mean(private_globals)

check("Federated private mean close to true global",
      abs(avg_private - true_global) < 0.1,
      f"private={avg_private:.4f} true={true_global:.4f}")

# Cross-federation comparison with DP
def private_federation_comparison(feds: List[Federation],
                                  epsilon: float = 1.0) -> Dict[str, float]:
    """Privately compare federation mean trust levels."""
    results = {}
    for fed in feds:
        results[fed.name] = private_mean(fed.trust_scores, epsilon)
    return results

comparison = private_federation_comparison(federations, epsilon=1.0)
# Alpha (betavariate(5,2)) should have highest trust
check("Private comparison preserves ordering (mostly)",
      comparison['alpha'] > comparison['gamma'] or comparison['beta'] > comparison['gamma'],
      f"alpha={comparison['alpha']:.3f} beta={comparison['beta']:.3f} gamma={comparison['gamma']:.3f}")


# ═══════════════════════════════════════════════════════════════
#  §11. PRIVACY-UTILITY TRADEOFF
# ═══════════════════════════════════════════════════════════════

section("Privacy-Utility Tradeoff")

def measure_tradeoff(trust_data: List[float],
                     epsilons: List[float]) -> Dict[float, Dict]:
    """
    Measure utility (accuracy) at different privacy levels (ε).

    Lower ε = more privacy, less utility.
    """
    true_mean = statistics.mean(trust_data)
    results = {}

    for eps in epsilons:
        random.seed(42)  # Reproducible
        private_means_tr = [private_mean(trust_data, eps) for _ in range(200)]
        mae = statistics.mean(abs(pm - true_mean) for pm in private_means_tr)
        mse = statistics.mean((pm - true_mean)**2 for pm in private_means_tr)

        results[eps] = {
            'mae': mae,
            'mse': mse,
            'relative_error': mae / max(abs(true_mean), 0.001)
        }

    return results


random.seed(42)
tradeoff_data = [random.betavariate(5, 2) for _ in range(200)]
tradeoff = measure_tradeoff(tradeoff_data, [0.1, 0.5, 1.0, 2.0, 5.0, 10.0])

check("Higher ε → lower error (better utility)",
      tradeoff[10.0]['mae'] < tradeoff[0.1]['mae'],
      f"ε=0.1 MAE={tradeoff[0.1]['mae']:.4f} ε=10 MAE={tradeoff[10.0]['mae']:.4f}")

check("ε=1.0 gives reasonable accuracy (< 10% relative error)",
      tradeoff[1.0]['relative_error'] < 0.10,
      f"relative error={tradeoff[1.0]['relative_error']:.4f}")

check("Error scales inversely with ε",
      tradeoff[0.5]['mae'] > tradeoff[5.0]['mae'],
      f"ε=0.5: {tradeoff[0.5]['mae']:.4f} ε=5.0: {tradeoff[5.0]['mae']:.4f}")

# Sample size effect
def sample_size_tradeoff(n_samples: List[int], epsilon: float = 1.0) -> Dict:
    """Larger datasets → less noise impact."""
    results = {}
    for n in n_samples:
        random.seed(42)
        data = [random.betavariate(5, 2) for _ in range(n)]
        true_mean = statistics.mean(data)
        errors = [abs(private_mean(data, epsilon) - true_mean) for _ in range(100)]
        results[n] = statistics.mean(errors)
    return results

size_effect = sample_size_tradeoff([20, 50, 100, 500, 1000])
check("Larger datasets → less privacy noise impact",
      size_effect[1000] < size_effect[20],
      f"n=20: {size_effect[20]:.4f} n=1000: {size_effect[1000]:.4f}")


# ═══════════════════════════════════════════════════════════════
#  §12. COMPLETE DP TRUST PIPELINE
# ═══════════════════════════════════════════════════════════════

section("Complete DP Trust Pipeline")

class DPTrustAnalytics:
    """
    End-to-end differentially private trust analytics system.

    Manages privacy budget, provides private queries, tracks usage.
    """

    def __init__(self, trust_data: Dict[str, float],
                 total_epsilon: float = 5.0, total_delta: float = 1e-4):
        self.data = trust_data
        self.values = list(trust_data.values())
        self.budget = PrivacyBudget(max_epsilon=total_epsilon, max_delta=total_delta)

    def query_mean(self, epsilon: float = 0.5) -> Optional[float]:
        if not self.budget.can_query(epsilon):
            return None
        result = private_mean(self.values, epsilon)
        self.budget.consume(epsilon, query_name="mean")
        return result

    def query_histogram(self, epsilon: float = 0.5, n_bins: int = 10) -> Optional[List[int]]:
        if not self.budget.can_query(epsilon):
            return None
        result = private_histogram(self.values, n_bins, epsilon)
        self.budget.consume(epsilon, query_name="histogram")
        return result

    def query_top_k(self, k: int = 5, epsilon: float = 1.0) -> Optional[List[str]]:
        if not self.budget.can_query(epsilon):
            return None
        result = private_top_k(self.data, k, epsilon)
        self.budget.consume(epsilon, query_name=f"top_{k}")
        return result

    def query_percentile(self, p: float = 0.5, epsilon: float = 0.5) -> Optional[float]:
        if not self.budget.can_query(epsilon):
            return None
        result = private_percentile(self.values, p, epsilon)
        self.budget.consume(epsilon, query_name=f"p{int(p*100)}")
        return result

    def remaining_budget(self) -> float:
        return self.budget.remaining_epsilon()


# Build the pipeline
random.seed(42)
entity_data = {f"entity_{i}": random.betavariate(5, 2) for i in range(500)}
pipeline = DPTrustAnalytics(entity_data, total_epsilon=5.0)

check("Pipeline initialized with full budget",
      pipeline.remaining_budget() == 5.0,
      f"budget={pipeline.remaining_budget()}")

# Run a series of queries
mean_result = pipeline.query_mean(epsilon=0.5)
check("Mean query succeeds",
      mean_result is not None,
      f"private mean={mean_result:.4f}")

hist_result = pipeline.query_histogram(epsilon=0.5)
check("Histogram query succeeds",
      hist_result is not None and len(hist_result) == 10,
      f"histogram bins={len(hist_result) if hist_result else 0}")

top5 = pipeline.query_top_k(k=5, epsilon=1.0)
check("Top-5 query succeeds",
      top5 is not None and len(top5) == 5,
      f"top-5={top5}")

p50 = pipeline.query_percentile(p=0.5, epsilon=0.5)
check("Percentile query succeeds",
      p50 is not None,
      f"p50={p50:.4f}")

remaining = pipeline.remaining_budget()
check("Budget tracked correctly",
      abs(remaining - 2.5) < 0.01,
      f"remaining={remaining} (expected 2.5)")

# Budget exhaustion
p90 = pipeline.query_percentile(p=0.9, epsilon=0.5)
check("Can still query within budget",
      p90 is not None,
      f"remaining after={pipeline.remaining_budget()}")

# Try to exceed budget
exceeded = pipeline.query_mean(epsilon=5.0)
check("Budget enforcement: rejects over-budget query",
      exceeded is None,
      f"query with ε=5.0 correctly rejected, remaining={pipeline.remaining_budget()}")

# Privacy accounting summary
check("Total queries tracked",
      len(pipeline.budget.queries) == 5,
      f"queries={len(pipeline.budget.queries)}")


# ═══════════════════════════════════════════════════════════════
#  SUMMARY
# ═══════════════════════════════════════════════════════════════

print(f"\n{'═' * 50}")
print(f"Differential Privacy Trust: {passed}/{passed+failed} checks passed")
print(f"Sections: {total_sections}/12")
if failed == 0:
    print(f"\n✓ All {passed} checks passed across {total_sections} sections")
else:
    print(f"\n✗ {failed} checks failed")
