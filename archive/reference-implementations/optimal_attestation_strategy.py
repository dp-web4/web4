"""
Optimal Attestation Strategy for Web4 Trust Systems
Session 30, Track 2

Analyzes optimal strategies for trust attestation:
- When to attest (timing optimization)
- How many attestors needed (information-theoretic bounds)
- Attestor selection (diversity vs redundancy tradeoff)
- Sequential vs batch attestation
- Bayesian updating with attestation evidence
- Multi-armed bandit for attestor selection
- Cost-benefit analysis of attestation overhead
"""

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional


# ─── Data Structures ───────────────────────────────────────────────

class AttestorQuality(Enum):
    HIGH = "high"       # trust >= 0.8
    MEDIUM = "medium"   # trust 0.4-0.8
    LOW = "low"         # trust < 0.4


@dataclass
class Attestor:
    id: str
    trust: float           # attestor's own trust score [0,1]
    accuracy: float        # P(correct attestation) [0.5, 1]
    cost: float            # cost per attestation in ATP
    response_time: float   # expected response time in ticks

    @property
    def quality(self) -> AttestorQuality:
        if self.trust >= 0.8:
            return AttestorQuality.HIGH
        elif self.trust >= 0.4:
            return AttestorQuality.MEDIUM
        return AttestorQuality.LOW


@dataclass
class AttestationResult:
    attestor_id: str
    attested_trust: float
    confidence: float
    timestamp: int


@dataclass
class BayesianEstimator:
    """Bayesian trust estimator using beta distribution prior."""
    alpha: float = 1.0   # prior successes
    beta_param: float = 1.0    # prior failures

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta_param)

    @property
    def variance(self) -> float:
        a, b = self.alpha, self.beta_param
        return (a * b) / ((a + b) ** 2 * (a + b + 1))

    @property
    def confidence_width(self) -> float:
        """95% credible interval width (beta approximation)."""
        std = math.sqrt(self.variance)
        return min(4 * std, 1.0)  # ±2σ, capped at 1

    def update(self, observation: float, weight: float = 1.0):
        """Update with weighted observation."""
        self.alpha += observation * weight
        self.beta_param += (1 - observation) * weight

    def entropy(self) -> float:
        """Entropy of beta distribution (approximate)."""
        a, b = self.alpha, self.beta_param
        if a <= 0 or b <= 0:
            return 0.0
        # Beta distribution entropy
        try:
            log_beta = (math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b))
            return log_beta - (a - 1) * (math.digamma(a) - math.digamma(a + b)) \
                   - (b - 1) * (math.digamma(b) - math.digamma(a + b))
        except (ValueError, OverflowError):
            return 0.0


# Need digamma - add to math if not available
if not hasattr(math, 'digamma'):
    def _digamma(x):
        """Digamma function approximation."""
        if x <= 0:
            return float('-inf')
        result = 0.0
        while x < 6:
            result -= 1.0 / x
            x += 1
        result += math.log(x) - 1.0 / (2 * x)
        x2 = 1.0 / (x * x)
        result -= x2 * (1.0/12 - x2 * (1.0/120 - x2 / 252))
        return result
    math.digamma = _digamma


# ─── Information Value of Attestation ──────────────────────────────

def attestation_information_value(attestor_trust: float, prior_uncertainty: float) -> float:
    """
    Expected information gain from one attestation.

    Higher attestor trust → more informative attestation.
    Higher prior uncertainty → more room for information gain.
    """
    # Channel capacity ≈ trust * log2(levels) for trust-weighted channel
    capacity = attestor_trust * math.log2(max(2, 1.0 / max(0.01, 1 - attestor_trust)))
    # Information gain bounded by min(capacity, prior_uncertainty)
    return min(capacity, prior_uncertainty)


def optimal_attestor_count(target_precision: float, attestor_trust: float,
                           trust_levels: int = 10) -> int:
    """
    Minimum attestors needed for target precision.

    Based on information-theoretic bounds:
    - Each attestor provides C bits of information
    - Need enough bits to achieve target precision
    - Precision ≈ 1/sqrt(n * C) for n attestors
    """
    if attestor_trust <= 0:
        return trust_levels  # max attestors needed

    # Channel capacity per attestor
    sigma = max(0.01, (1 - attestor_trust) * (trust_levels / 3))
    capacity = 0.0
    for i in range(trust_levels):
        p_correct = attestor_trust + (1 - attestor_trust) * math.exp(0)
        # Simplified: capacity ≈ trust * log2(trust_levels)
        capacity = attestor_trust * math.log2(trust_levels)

    if capacity <= 0:
        return trust_levels

    # n attestors with independent capacity: total = n * C
    # Precision ≈ 1 / (2^(n*C/2))  →  need n*C/2 ≥ log2(1/precision)
    bits_needed = math.log2(1.0 / max(0.001, target_precision))
    n = math.ceil(2 * bits_needed / capacity)
    return max(1, min(n, 100))


# ─── Attestor Selection Strategy ───────────────────────────────────

def greedy_attestor_selection(attestors: List[Attestor], budget: float,
                              target_precision: float) -> List[Attestor]:
    """
    Select attestors greedily by information-per-cost ratio.
    """
    selected = []
    remaining_budget = budget
    prior_uncertainty = 1.0  # start with maximum uncertainty

    # Sort by info value / cost ratio
    candidates = sorted(attestors,
                        key=lambda a: attestation_information_value(a.trust, 1.0) / max(0.01, a.cost),
                        reverse=True)

    for attestor in candidates:
        if attestor.cost > remaining_budget:
            continue
        info_gain = attestation_information_value(attestor.trust, prior_uncertainty)
        if info_gain < 0.001:
            break  # diminishing returns
        selected.append(attestor)
        remaining_budget -= attestor.cost
        prior_uncertainty *= (1 - attestor.trust)  # reduce uncertainty
        if prior_uncertainty < target_precision:
            break

    return selected


def diverse_attestor_selection(attestors: List[Attestor], k: int) -> List[Attestor]:
    """
    Select k attestors maximizing diversity (different quality tiers).
    """
    by_quality = {q: [] for q in AttestorQuality}
    for a in attestors:
        by_quality[a.quality].append(a)

    # Sort within each quality tier by trust (descending)
    for q in by_quality:
        by_quality[q].sort(key=lambda a: a.trust, reverse=True)

    selected = []
    # Round-robin from each quality tier
    tier_order = [AttestorQuality.HIGH, AttestorQuality.MEDIUM, AttestorQuality.LOW]
    tier_idx = {q: 0 for q in tier_order}

    while len(selected) < k:
        added = False
        for q in tier_order:
            if len(selected) >= k:
                break
            idx = tier_idx[q]
            if idx < len(by_quality[q]):
                selected.append(by_quality[q][idx])
                tier_idx[q] = idx + 1
                added = True
        if not added:
            break

    return selected


# ─── Sequential vs Batch Attestation ──────────────────────────────

def sequential_attestation_value(attestors: List[Attestor],
                                  true_trust: float,
                                  seed: int = 42) -> Dict:
    """
    Simulate sequential attestation with early stopping.
    Stop when confidence width < threshold or budget exhausted.
    """
    rng = random.Random(seed)
    estimator = BayesianEstimator()
    results = []
    total_cost = 0.0
    threshold = 0.15  # stop when CI width < this

    for attestor in attestors:
        # Generate noisy observation
        noise = rng.gauss(0, (1 - attestor.trust) * 0.3)
        observation = max(0, min(1, true_trust + noise))

        # Weight by attestor trust
        estimator.update(observation, weight=attestor.trust)
        total_cost += attestor.cost

        results.append({
            "attestor": attestor.id,
            "estimate": estimator.mean,
            "ci_width": estimator.confidence_width,
            "cost": total_cost,
        })

        if estimator.confidence_width < threshold:
            break

    return {
        "estimates": results,
        "final_estimate": estimator.mean,
        "final_ci_width": estimator.confidence_width,
        "total_cost": total_cost,
        "attestations_used": len(results),
        "early_stopped": len(results) < len(attestors),
    }


def batch_attestation_value(attestors: List[Attestor],
                             true_trust: float,
                             seed: int = 42) -> Dict:
    """
    Simulate batch attestation (all at once, no early stopping).
    """
    rng = random.Random(seed)
    estimator = BayesianEstimator()
    total_cost = 0.0

    for attestor in attestors:
        noise = rng.gauss(0, (1 - attestor.trust) * 0.3)
        observation = max(0, min(1, true_trust + noise))
        estimator.update(observation, weight=attestor.trust)
        total_cost += attestor.cost

    return {
        "final_estimate": estimator.mean,
        "final_ci_width": estimator.confidence_width,
        "total_cost": total_cost,
        "attestations_used": len(attestors),
    }


# ─── Multi-Armed Bandit Attestor Selection ─────────────────────────

class UCB1AttestorSelector:
    """
    UCB1 algorithm for learning which attestors to use.
    Balances exploration (trying unknown attestors) vs exploitation
    (using known-good attestors).
    """

    def __init__(self, attestors: List[Attestor]):
        self.attestors = attestors
        self.counts = {a.id: 0 for a in attestors}
        self.rewards = {a.id: 0.0 for a in attestors}
        self.total_rounds = 0

    def select(self) -> Attestor:
        """Select attestor using UCB1 formula."""
        # First: try each attestor at least once
        for a in self.attestors:
            if self.counts[a.id] == 0:
                return a

        # UCB1: mean_reward + sqrt(2 * ln(t) / n_i)
        best_score = -1
        best_attestor = self.attestors[0]

        for a in self.attestors:
            n = self.counts[a.id]
            mean = self.rewards[a.id] / n
            exploration = math.sqrt(2 * math.log(self.total_rounds) / n)
            score = mean + exploration
            if score > best_score:
                best_score = score
                best_attestor = a

        return best_attestor

    def update(self, attestor_id: str, reward: float):
        """Update with observed reward."""
        self.counts[attestor_id] += 1
        self.rewards[attestor_id] += reward
        self.total_rounds += 1

    def best_attestor(self) -> Attestor:
        """Return attestor with highest mean reward."""
        best_mean = -1
        best = self.attestors[0]
        for a in self.attestors:
            if self.counts[a.id] > 0:
                mean = self.rewards[a.id] / self.counts[a.id]
                if mean > best_mean:
                    best_mean = mean
                    best = a
        return best


# ─── Cost-Benefit Analysis ─────────────────────────────────────────

def attestation_roi(trust_improvement: float, attestation_cost: float,
                    trust_value_per_unit: float = 10.0) -> float:
    """
    Return on investment for attestation.
    ROI = (value_gained - cost) / cost
    """
    value = trust_improvement * trust_value_per_unit
    if attestation_cost <= 0:
        return float('inf') if value > 0 else 0.0
    return (value - attestation_cost) / attestation_cost


def optimal_attestation_budget(entity_value: float, current_trust: float,
                               attestor_cost: float) -> float:
    """
    Optimal budget allocation: diminishing returns on attestation.
    Budget should be proportional to entity value and inversely
    proportional to current trust (less trusted entities benefit more).
    """
    uncertainty = 1 - current_trust
    # Budget = entity_value * uncertainty * diminishing_factor
    # Cap at reasonable fraction of entity value
    budget = entity_value * uncertainty * 0.3
    return max(attestor_cost, min(budget, entity_value * 0.5))


# ─── Timing Optimization ──────────────────────────────────────────

def optimal_reattestion_interval(decay_rate: float, trust_threshold: float,
                                  current_trust: float) -> int:
    """
    When should an entity seek re-attestation?

    Trust decays: T(t) = T(0) * e^(-decay * t)
    Re-attest when T(t) approaches threshold.
    """
    if current_trust <= trust_threshold or decay_rate <= 0:
        return 1  # immediate

    # Time until trust reaches threshold
    ratio = trust_threshold / current_trust
    if ratio <= 0:
        return 1000  # effectively never
    time_to_threshold = -math.log(ratio) / decay_rate

    # Re-attest at 80% of time-to-threshold (safety margin)
    return max(1, int(time_to_threshold * 0.8))


def attestation_freshness_weight(age: int, half_life: int = 50) -> float:
    """
    Weight for attestation based on age.
    Exponential decay with configurable half-life.
    """
    return math.exp(-0.693 * age / half_life)


# ─── Trust Aggregation with Attestation Weights ───────────────────

def weighted_attestation_aggregate(results: List[AttestationResult],
                                    current_time: int,
                                    half_life: int = 50) -> Tuple[float, float]:
    """
    Aggregate attestation results with freshness and confidence weighting.
    Returns (aggregated_trust, total_weight).
    """
    if not results:
        return 0.5, 0.0  # uninformative prior

    total_weight = 0.0
    weighted_sum = 0.0

    for r in results:
        age = current_time - r.timestamp
        freshness = attestation_freshness_weight(age, half_life)
        weight = r.confidence * freshness
        weighted_sum += r.attested_trust * weight
        total_weight += weight

    if total_weight <= 0:
        return 0.5, 0.0

    return weighted_sum / total_weight, total_weight


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
    print("Optimal Attestation Strategy for Web4 Trust")
    print("Session 30, Track 2")
    print("=" * 70)

    # ── §1 Information Value ──────────────────────────────────────
    print("\n§1 Information Value of Attestation\n")

    # Higher trust attestor → more information
    iv_high = attestation_information_value(0.9, 1.0)
    iv_low = attestation_information_value(0.3, 1.0)
    check("high_trust_more_info", iv_high > iv_low,
          f"high={iv_high:.3f} low={iv_low:.3f}")

    # Zero uncertainty → no information gain
    iv_zero = attestation_information_value(0.9, 0.0)
    check("zero_uncertainty_no_gain", iv_zero == 0.0,
          f"iv={iv_zero}")

    # Perfect attestor
    iv_perfect = attestation_information_value(1.0, 1.0)
    check("perfect_attestor_max_info", iv_perfect > 0,
          f"iv={iv_perfect:.3f}")

    # ── §2 Optimal Attestor Count ─────────────────────────────────
    print("\n§2 Optimal Attestor Count\n")

    # Higher precision → more attestors needed
    n_coarse = optimal_attestor_count(0.2, 0.7)
    n_fine = optimal_attestor_count(0.05, 0.7)
    check("finer_precision_more_attestors", n_fine >= n_coarse,
          f"coarse={n_coarse} fine={n_fine}")

    # Higher trust attestor → fewer needed
    n_high = optimal_attestor_count(0.1, 0.9)
    n_low = optimal_attestor_count(0.1, 0.3)
    check("high_trust_fewer_attestors", n_high <= n_low,
          f"high={n_high} low={n_low}")

    # At least 1 attestor always needed
    n_min = optimal_attestor_count(0.5, 0.99)
    check("min_one_attestor", n_min >= 1, f"n={n_min}")

    # ── §3 Greedy Attestor Selection ──────────────────────────────
    print("\n§3 Greedy Attestor Selection\n")

    attestors = [
        Attestor("A1", 0.9, 0.95, 1.0, 1),
        Attestor("A2", 0.7, 0.85, 0.5, 2),
        Attestor("A3", 0.5, 0.75, 0.3, 3),
        Attestor("A4", 0.3, 0.65, 0.2, 5),
        Attestor("A5", 0.1, 0.55, 0.1, 10),
    ]

    selected = greedy_attestor_selection(attestors, budget=2.0, target_precision=0.1)
    check("greedy_selects_some", len(selected) > 0,
          f"selected={len(selected)}")
    check("greedy_within_budget", sum(a.cost for a in selected) <= 2.0,
          f"cost={sum(a.cost for a in selected):.1f}")

    # Best info/cost ratio should be selected first
    if selected:
        check("greedy_best_first", selected[0].trust >= 0.5,
              f"first={selected[0].id} trust={selected[0].trust}")

    # ── §4 Diverse Attestor Selection ─────────────────────────────
    print("\n§4 Diverse Attestor Selection\n")

    diverse = diverse_attestor_selection(attestors, k=3)
    check("diverse_selects_k", len(diverse) == 3,
          f"selected={len(diverse)}")

    # Should include multiple quality tiers
    qualities = {a.quality for a in diverse}
    check("diverse_multiple_tiers", len(qualities) >= 2,
          f"tiers={[q.value for q in qualities]}")

    # ── §5 Bayesian Estimator ─────────────────────────────────────
    print("\n§5 Bayesian Trust Estimator\n")

    est = BayesianEstimator()
    check("prior_mean_0.5", abs(est.mean - 0.5) < 0.01,
          f"mean={est.mean:.3f}")

    # Update with high observations → mean increases
    for _ in range(10):
        est.update(0.8, weight=1.0)
    check("updated_mean_high", est.mean > 0.6,
          f"mean={est.mean:.3f}")

    # Confidence increases (CI narrows)
    ci_before = BayesianEstimator(alpha=1, beta_param=1).confidence_width
    ci_after = est.confidence_width
    check("ci_narrows_with_evidence", ci_after < ci_before,
          f"before={ci_before:.3f} after={ci_after:.3f}")

    # Entropy decreases with evidence
    ent_prior = BayesianEstimator().entropy()
    ent_posterior = est.entropy()
    check("entropy_decreases", ent_posterior < ent_prior,
          f"prior={ent_prior:.3f} posterior={ent_posterior:.3f}")

    # ── §6 Sequential Attestation ─────────────────────────────────
    print("\n§6 Sequential vs Batch Attestation\n")

    seq = sequential_attestation_value(attestors, true_trust=0.7, seed=42)
    batch = batch_attestation_value(attestors, true_trust=0.7, seed=42)

    # Sequential should use fewer attestations (early stopping)
    check("sequential_early_stop", seq["attestations_used"] <= batch["attestations_used"],
          f"seq={seq['attestations_used']} batch={batch['attestations_used']}")

    # Sequential should cost less (or equal)
    check("sequential_cheaper", seq["total_cost"] <= batch["total_cost"],
          f"seq={seq['total_cost']:.1f} batch={batch['total_cost']:.1f}")

    # Both should estimate reasonably close to true trust
    check("seq_reasonable_estimate", abs(seq["final_estimate"] - 0.7) < 0.3,
          f"est={seq['final_estimate']:.3f}")
    check("batch_reasonable_estimate", abs(batch["final_estimate"] - 0.7) < 0.3,
          f"est={batch['final_estimate']:.3f}")

    # ── §7 UCB1 Attestor Selection ────────────────────────────────
    print("\n§7 UCB1 Multi-Armed Bandit\n")

    rng = random.Random(42)
    selector = UCB1AttestorSelector(attestors)

    # Run 200 rounds
    for _ in range(200):
        a = selector.select()
        # Reward: accuracy adjusted by trust
        reward = a.accuracy * a.trust + rng.gauss(0, 0.1)
        reward = max(0, min(1, reward))
        selector.update(a.id, reward)

    # Best attestor should be the highest trust one (A1)
    best = selector.best_attestor()
    check("ucb1_finds_best", best.trust >= 0.7,
          f"best={best.id} trust={best.trust}")

    # All attestors explored at least once
    all_explored = all(selector.counts[a.id] > 0 for a in attestors)
    check("ucb1_explores_all", all_explored,
          f"counts={dict(selector.counts)}")

    # Best attestor explored most
    best_count = selector.counts[best.id]
    check("ucb1_exploits_best", best_count > 200 / len(attestors),
          f"best_count={best_count} avg={200/len(attestors):.0f}")

    # ── §8 Cost-Benefit Analysis ──────────────────────────────────
    print("\n§8 Cost-Benefit Analysis\n")

    roi_good = attestation_roi(0.3, 1.0)  # 30% trust improvement, 1 ATP cost
    roi_bad = attestation_roi(0.01, 5.0)  # 1% improvement, 5 ATP cost
    check("good_roi_positive", roi_good > 0, f"roi={roi_good:.2f}")
    check("bad_roi_negative", roi_bad < 0, f"roi={roi_bad:.2f}")

    # Higher entity value → higher optimal budget
    budget_high = optimal_attestation_budget(1000, 0.5, 1.0)
    budget_low = optimal_attestation_budget(100, 0.5, 1.0)
    check("higher_value_higher_budget", budget_high > budget_low,
          f"high={budget_high:.1f} low={budget_low:.1f}")

    # Higher current trust → lower budget (less need for attestation)
    budget_trusted = optimal_attestation_budget(1000, 0.9, 1.0)
    budget_untrusted = optimal_attestation_budget(1000, 0.2, 1.0)
    check("untrusted_higher_budget", budget_untrusted > budget_trusted,
          f"trusted={budget_trusted:.1f} untrusted={budget_untrusted:.1f}")

    # ── §9 Timing Optimization ────────────────────────────────────
    print("\n§9 Attestation Timing\n")

    # Higher decay rate → more frequent re-attestation
    interval_fast = optimal_reattestion_interval(0.1, 0.5, 0.9)
    interval_slow = optimal_reattestion_interval(0.01, 0.5, 0.9)
    check("fast_decay_shorter_interval", interval_fast < interval_slow,
          f"fast={interval_fast} slow={interval_slow}")

    # Already below threshold → immediate
    interval_urgent = optimal_reattestion_interval(0.05, 0.5, 0.4)
    check("below_threshold_immediate", interval_urgent == 1,
          f"interval={interval_urgent}")

    # Freshness weight decays
    w_fresh = attestation_freshness_weight(0)
    w_old = attestation_freshness_weight(100)
    check("fresh_heavier_than_old", w_fresh > w_old,
          f"fresh={w_fresh:.3f} old={w_old:.3f}")

    # At half-life, weight should be ~0.5
    w_half = attestation_freshness_weight(50, half_life=50)
    check("half_life_weight", abs(w_half - 0.5) < 0.05,
          f"w={w_half:.3f}")

    # ── §10 Weighted Aggregation ──────────────────────────────────
    print("\n§10 Weighted Attestation Aggregation\n")

    results = [
        AttestationResult("A1", 0.8, 0.9, timestamp=90),
        AttestationResult("A2", 0.7, 0.7, timestamp=50),
        AttestationResult("A3", 0.6, 0.5, timestamp=10),
    ]

    agg_trust, total_weight = weighted_attestation_aggregate(results, current_time=100)

    # Aggregated trust should be between min and max
    check("aggregate_in_range", 0.6 <= agg_trust <= 0.8,
          f"agg={agg_trust:.3f}")

    # Should be closer to A1 (most recent + highest confidence)
    check("aggregate_favors_recent", agg_trust > 0.7,
          f"agg={agg_trust:.3f}")

    # Total weight positive
    check("total_weight_positive", total_weight > 0,
          f"weight={total_weight:.3f}")

    # Empty results → uninformative prior
    empty_trust, empty_weight = weighted_attestation_aggregate([], current_time=100)
    check("empty_uninformative", abs(empty_trust - 0.5) < 0.01,
          f"trust={empty_trust}")

    # ── §11 End-to-End Strategy Comparison ────────────────────────
    print("\n§11 Strategy Comparison\n")

    # Compare: greedy vs diverse vs random selection
    random.seed(42)
    true_trust = 0.75

    # Greedy
    greedy_sel = greedy_attestor_selection(attestors, budget=5.0, target_precision=0.1)
    greedy_result = batch_attestation_value(greedy_sel, true_trust, seed=100)

    # Diverse
    diverse_sel = diverse_attestor_selection(attestors, k=len(greedy_sel) if greedy_sel else 3)
    diverse_result = batch_attestation_value(diverse_sel, true_trust, seed=100)

    # Random
    random_sel = random.sample(attestors, min(3, len(attestors)))
    random_result = batch_attestation_value(random_sel, true_trust, seed=100)

    # All should produce estimates
    check("greedy_produces_estimate", greedy_result["final_estimate"] > 0)
    check("diverse_produces_estimate", diverse_result["final_estimate"] > 0)
    check("random_produces_estimate", random_result["final_estimate"] > 0)

    # ── §12 Diminishing Returns ───────────────────────────────────
    print("\n§12 Diminishing Returns Analysis\n")

    # Adding more attestors gives diminishing CI reduction
    ci_widths = []
    est = BayesianEstimator()
    rng = random.Random(42)
    for i in range(20):
        obs = max(0, min(1, 0.7 + rng.gauss(0, 0.1)))
        est.update(obs, weight=0.8)
        ci_widths.append(est.confidence_width)

    # CI should decrease monotonically (or stay flat)
    check("ci_monotone_decrease", all(ci_widths[i] >= ci_widths[i+1] - 0.01
                                       for i in range(len(ci_widths)-1)),
          f"widths={[f'{w:.3f}' for w in ci_widths[:5]]}")

    # Early attestations reduce CI more than later ones
    if len(ci_widths) > 10:
        early_reduction = ci_widths[0] - ci_widths[4]   # reduction from attestation 1→5
        late_reduction = ci_widths[10] - ci_widths[14]   # reduction from attestation 11→15
        check("diminishing_returns", early_reduction > late_reduction,
              f"early={early_reduction:.4f} late={late_reduction:.4f}")

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
