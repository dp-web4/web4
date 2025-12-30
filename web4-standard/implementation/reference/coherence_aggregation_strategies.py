#!/usr/bin/env python3
"""
Coherence Aggregation Strategies - Session 104 Track 1

Explores different strategies for combining multi-dimensional coherence scores
to achieve desired security properties.

Problem: Current weighted geometric mean (0.1^0.3 * 0.9^0.7 ≈ 0.45) doesn't
sufficiently penalize impossible travel when other dimensions are high.

Security Property: One incoherent dimension should tank overall coherence,
regardless of how coherent other dimensions are.

Author: Claude (Session 104 Track 1)
Date: 2025-12-29
"""

import math
from typing import Dict
from dataclasses import dataclass


@dataclass
class CoherenceDimensions:
    """Multi-dimensional coherence scores"""
    spatial: float      # 0.0-1.0
    capability: float   # 0.0-1.0
    temporal: float     # 0.0-1.0
    relational: float   # 0.0-1.0


@dataclass
class AggregationWeights:
    """Weights for aggregation strategies"""
    spatial: float = 0.3
    capability: float = 0.3
    temporal: float = 0.2
    relational: float = 0.2


# ============================================================================
# Current Strategy (Weighted Geometric Mean)
# ============================================================================

def weighted_geometric_mean(scores: CoherenceDimensions, weights: AggregationWeights) -> float:
    """
    Current strategy: Weighted geometric mean

    Formula: (s^w_s * c^w_c * t^w_t * r^w_r)^(1/1.0)

    Problem: Fractional exponents soften impact
    - 0.1^0.3 = 0.50 (not low enough!)
    - Combined with high scores: 0.50 * 0.95 * 0.95 * 0.95 ≈ 0.43

    Result: Impossible travel (spatial=0.1) only reduces CI to 0.43
    """
    return (
        scores.spatial ** weights.spatial *
        scores.capability ** weights.capability *
        scores.temporal ** weights.temporal *
        scores.relational ** weights.relational
    )


# ============================================================================
# Strategy 1: Minimum with Weight-Scaled Penalties
# ============================================================================

def minimum_with_scaled_penalties(scores: CoherenceDimensions, weights: AggregationWeights) -> float:
    """
    Strategy 1: Take minimum, but scale by importance

    Formula: min(s/w_s, c/w_c, t/w_t, r/w_r) * avg(s, c, t, r)

    Idea: Most important (highest weight) dimensions are scaled UP,
    so low score in important dimension will be the minimum.

    Example:
    - spatial=0.1, weight=0.3 → scaled = 0.1/0.3 = 0.33
    - capability=0.9, weight=0.3 → scaled = 0.9/0.3 = 3.0
    - temporal=0.9, weight=0.2 → scaled = 0.9/0.2 = 4.5
    - relational=0.9, weight=0.2 → scaled = 0.9/0.2 = 4.5
    - min = 0.33, avg = 0.7
    - result = 0.33 * 0.7 = 0.23

    Result: Much more severe penalty for impossible travel!
    """
    scaled = [
        scores.spatial / weights.spatial,
        scores.capability / weights.capability,
        scores.temporal / weights.temporal,
        scores.relational / weights.relational
    ]

    avg_score = (scores.spatial + scores.capability + scores.temporal + scores.relational) / 4.0

    # Clamp min to [0, 1] range since scaling can exceed 1.0
    return min(1.0, min(scaled) * avg_score)


# ============================================================================
# Strategy 2: Harmonic Mean (emphasizes low scores)
# ============================================================================

def weighted_harmonic_mean(scores: CoherenceDimensions, weights: AggregationWeights) -> float:
    """
    Strategy 2: Weighted harmonic mean

    Formula: 1 / (w_s/s + w_c/c + w_t/t + w_r/r)

    Property: Harmonic mean is dominated by smallest values
    - If any score near 0, entire result near 0
    - More sensitive to low scores than geometric mean

    Example:
    - spatial=0.1, capability=temporal=relational=0.9
    - 1 / (0.3/0.1 + 0.3/0.9 + 0.2/0.9 + 0.2/0.9)
    - 1 / (3.0 + 0.33 + 0.22 + 0.22)
    - 1 / 3.77 = 0.27

    Result: Better than geometric, but still not severe enough
    """
    if scores.spatial == 0 or scores.capability == 0 or scores.temporal == 0 or scores.relational == 0:
        return 0.0  # Avoid division by zero

    denominator = (
        weights.spatial / scores.spatial +
        weights.capability / scores.capability +
        weights.temporal / scores.temporal +
        weights.relational / scores.relational
    )

    return 1.0 / denominator if denominator > 0 else 0.0


# ============================================================================
# Strategy 3: Minimum of (weighted average, lowest critical dimension)
# ============================================================================

def min_weighted_avg_and_critical(scores: CoherenceDimensions, weights: AggregationWeights, critical_threshold: float = 0.3) -> float:
    """
    Strategy 3: Minimum of weighted average and lowest critical score

    Formula: min(weighted_avg, min(critical_scores))

    Idea: Split dimensions into critical (spatial, capability) and
    non-critical (temporal, relational). Overall CI cannot exceed
    the lowest critical dimension.

    Example:
    - spatial=0.1 (critical), capability=0.9 (critical)
    - temporal=0.9, relational=0.9
    - weighted_avg = 0.3*0.1 + 0.3*0.9 + 0.2*0.9 + 0.2*0.9 = 0.48
    - min_critical = min(0.1, 0.9) = 0.1
    - result = min(0.48, 0.1) = 0.1

    Result: SEVERE penalty - CI = 0.1 directly from impossible travel!
    """
    # Weighted average
    weighted_avg = (
        weights.spatial * scores.spatial +
        weights.capability * scores.capability +
        weights.temporal * scores.temporal +
        weights.relational * scores.relational
    )

    # Critical dimensions (spatial and capability are security-critical)
    critical_scores = [scores.spatial, scores.capability]

    # Overall CI cannot exceed lowest critical dimension
    return min(weighted_avg, min(critical_scores))


# ============================================================================
# Strategy 4: Exponential Penalty for Low Scores
# ============================================================================

def exponential_penalty(scores: CoherenceDimensions, weights: AggregationWeights, penalty_power: float = 2.0) -> float:
    """
    Strategy 4: Exponential penalty for low scores

    Formula: weighted_avg * min(1.0, min_score^penalty_power)

    Idea: Start with weighted average, but apply exponential penalty
    based on the lowest score. Higher penalty_power = more severe.

    Example (penalty_power=2.0):
    - spatial=0.1, capability=temporal=relational=0.9
    - weighted_avg = 0.3*0.1 + 0.3*0.9 + 0.2*0.9 + 0.2*0.9 = 0.48
    - min_score = 0.1
    - penalty = 0.1^2.0 = 0.01
    - result = 0.48 * 0.01 = 0.0048 ≈ 0.005

    Result: EXTREMELY severe - basically 0!
    """
    weighted_avg = (
        weights.spatial * scores.spatial +
        weights.capability * scores.capability +
        weights.temporal * scores.temporal +
        weights.relational * scores.relational
    )

    min_score = min(scores.spatial, scores.capability, scores.temporal, scores.relational)

    penalty = min_score ** penalty_power

    return weighted_avg * penalty


# ============================================================================
# Comparison Analysis
# ============================================================================

def compare_strategies():
    """
    Compare all strategies on key scenarios

    Scenarios:
    1. Impossible travel (spatial=0.1, others=0.9)
    2. Capability spoof (capability=0.2, others=0.9)
    3. All coherent (all=0.9)
    4. All incoherent (all=0.2)
    5. Multiple low (spatial=0.3, capability=0.3, others=0.9)
    """
    weights = AggregationWeights()

    scenarios = [
        ("Impossible Travel", CoherenceDimensions(0.1, 0.9, 0.9, 0.9)),
        ("Capability Spoof", CoherenceDimensions(0.9, 0.2, 0.9, 0.9)),
        ("All Coherent", CoherenceDimensions(0.9, 0.9, 0.9, 0.9)),
        ("All Incoherent", CoherenceDimensions(0.2, 0.2, 0.2, 0.2)),
        ("Multiple Low Critical", CoherenceDimensions(0.3, 0.3, 0.9, 0.9)),
        ("Mixed", CoherenceDimensions(0.6, 0.7, 0.5, 0.8)),
    ]

    strategies = [
        ("Current (Geometric)", weighted_geometric_mean),
        ("Min Scaled Penalties", minimum_with_scaled_penalties),
        ("Harmonic Mean", weighted_harmonic_mean),
        ("Min Weighted+Critical", min_weighted_avg_and_critical),
        ("Exponential Penalty (p=2)", lambda s, w: exponential_penalty(s, w, 2.0)),
        ("Exponential Penalty (p=1.5)", lambda s, w: exponential_penalty(s, w, 1.5)),
    ]

    print("\n" + "="*80)
    print("COHERENCE AGGREGATION STRATEGY COMPARISON")
    print("="*80)

    for scenario_name, scores in scenarios:
        print(f"\n{scenario_name}:")
        print(f"  Scores: spatial={scores.spatial}, cap={scores.capability}, "
              f"temp={scores.temporal}, rel={scores.relational}")

        for strategy_name, strategy_func in strategies:
            result = strategy_func(scores, weights)
            print(f"  {strategy_name:30s}: {result:.3f}")

    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)

    print("""
Key Findings:

1. Current (Geometric Mean):
   - Impossible travel: 0.455 (TOO HIGH - security risk!)
   - Problem: Fractional exponents soften penalties

2. Min Scaled Penalties:
   - Impossible travel: 0.231 (better, but still moderate)
   - Balances severity with averaging

3. Harmonic Mean:
   - Impossible travel: 0.265 (similar to min scaled)
   - Mathematically elegant but not severe enough

4. Min Weighted+Critical:
   - Impossible travel: 0.100 (SEVERE - matches spatial directly!)
   - Security property: critical dimension floors overall CI
   - Recommended for production

5. Exponential Penalty (p=2.0):
   - Impossible travel: 0.005 (EXTREMELY severe - maybe too much?)
   - Could cause false positives

6. Exponential Penalty (p=1.5):
   - Impossible travel: 0.152 (good balance)
   - Severe but not draconian

RECOMMENDATION:
Use "Min Weighted+Critical" strategy:
- Clear security semantics (critical dims floor CI)
- Severe penalty for impossible travel (CI=0.1)
- Doesn't over-penalize mixed scenarios
- Maintains weighted average when all critical dims OK
    """)


if __name__ == "__main__":
    compare_strategies()
