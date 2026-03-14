#!/usr/bin/env python3
"""
Web4 Epistemic Measurement Demonstration - Session 17
======================================================

Demonstrates real measurement of epistemic predictions (M1-M6) following
SAGE S34 pattern: Real measurements with simulated coordination data.

This bridges Session 16 (epistemic states implementation) with Session 17
(observational framework) by showing how to measure epistemic predictions.

Research Provenance:
- Web4 S16: Epistemic coordination states (Phase 1)
- Web4 S17: Observational framework extension
- SAGE S33: Observational validation pattern
- SAGE S34: Real measurement integration

Created: December 12, 2025
"""

import random
import statistics
import numpy as np
from typing import Dict, List

from web4_coordination_epistemic_states import (
    CoordinationEpistemicState,
    CoordinationEpistemicMetrics,
    estimate_coordination_epistemic_state
)

from web4_epistemic_observational_extension import (
    Web4EpistemicObservationalFramework
)


def generate_simulated_coordination_history(num_cycles: int = 100,
                                             quality_mean: float = 0.85,
                                             quality_std: float = 0.10) -> List[Dict]:
    """
    Generate simulated coordination history for measurement demonstration.

    Generates realistic coordination cycles with:
    - Epistemic metrics (coordination confidence, parameter stability, etc.)
    - Actual quality scores
    - Ground truth labels for validation

    Args:
        num_cycles: Number of coordination cycles to simulate
        quality_mean: Mean coordination quality
        quality_std: Standard deviation of quality

    Returns:
        List of coordination cycles with epistemic and quality data
    """
    history = []

    # Start in adapting state, converge to optimal
    for i in range(num_cycles):
        # Generate metrics that evolve over time
        progress = i / num_cycles

        # Simulate convergence: starts lower, improves over time
        coverage = 0.70 + 0.25 * progress + random.gauss(0, 0.03)
        quality = max(0, min(1.0, quality_mean + random.gauss(0, quality_std) + 0.1 * progress))
        efficiency = 0.65 + 0.20 * progress + random.gauss(0, 0.05)

        # Calculate parameter drift (high early, low later)
        parameter_drift = max(0.001, 0.1 * (1 - progress) + random.gauss(0, 0.02))

        # Adaptation frequency (higher early)
        adaptation_rate = max(0.01, 0.15 * (1 - progress))

        # Satisfaction history (improves over time)
        satisfaction_history = [
            max(0, min(1.0, 0.85 + 0.1 * progress + random.gauss(0, 0.05)))
            for _ in range(10)
        ]

        # Estimate epistemic metrics
        metrics_dict = {
            'coverage': coverage,
            'quality': quality,
            'efficiency': efficiency,
            'parameter_drift': parameter_drift,
            'adaptation_rate': adaptation_rate,
            'satisfaction_history': satisfaction_history
        }

        epistemic_metrics = estimate_coordination_epistemic_state(metrics_dict, history)

        # Ground truth struggling: when quality < 0.75 and improvement_rate < 0
        ground_truth_struggling = (quality < 0.75 and epistemic_metrics.improvement_rate < 0)

        cycle = {
            'cycle_id': i,
            'epistemic_metrics': epistemic_metrics,
            'quality': quality,  # Actual coordination quality
            'coverage': coverage,
            'efficiency': efficiency,
            'ground_truth_struggling': ground_truth_struggling
        }

        history.append(cycle)

    return history


def demonstrate_epistemic_measurements():
    """
    Demonstrate measurement of all 6 epistemic predictions.

    Following SAGE S34 pattern: Real measurement functions with simulated data.
    """
    print("=" * 80)
    print("Web4 Epistemic Measurement Demonstration")
    print("=" * 80)
    print()
    print("Simulating 100 coordination cycles with epistemic tracking...")
    print()

    # Generate simulated coordination history
    coordination_history = generate_simulated_coordination_history(
        num_cycles=100,
        quality_mean=0.85,
        quality_std=0.08
    )

    print(f"✓ Generated {len(coordination_history)} coordination cycles")
    print()

    # Initialize framework
    framework = Web4EpistemicObservationalFramework()

    print("=" * 80)
    print("Measuring Epistemic Predictions (M1-M6)")
    print("=" * 80)
    print()

    # Prepare data for measurements
    data = {'coordination_history': coordination_history}

    # Measure M1: Confidence-Quality Correlation
    print("M1: Coordination Confidence-Quality Correlation")
    print("-" * 80)
    try:
        m1_pred = framework.predictions_dict['M1']
        observed, error = m1_pred.measure(data)
        validated, significance = m1_pred.validate(observed, error)

        print(f"  Predicted: r > 0.50")
        print(f"  Observed:  r = {observed:.3f} ± {error:.3f}")
        print(f"  Validated: {'✅ YES' if validated else '❌ NO'}")
        print(f"  Significance: {significance:.2f}σ")
        print()
    except Exception as e:
        print(f"  ⚠️  Measurement failed: {e}")
        print()

    # Measure M2: State Distribution Balance
    print("M2: Epistemic State Distribution Balance")
    print("-" * 80)
    try:
        m2_pred = framework.predictions_dict['M2']
        observed, error = m2_pred.measure(data)
        validated, significance = m2_pred.validate(observed, error)

        print(f"  Predicted: Max state proportion < 50%")
        print(f"  Observed:  Max proportion = {observed:.3f} ± {error:.3f}")
        print(f"  Validated: {'✅ YES' if validated else '❌ NO'}")
        print(f"  Significance: {significance:.2f}σ")

        # Show state distribution
        state_counts = {}
        for cycle in coordination_history:
            state = cycle['epistemic_metrics'].primary_state()
            state_counts[state] = state_counts.get(state, 0) + 1

        print("  State distribution:")
        for state, count in sorted(state_counts.items(), key=lambda x: -x[1]):
            proportion = count / len(coordination_history)
            print(f"    {state.value:12s}: {proportion:5.1%} ({count} cycles)")
        print()
    except Exception as e:
        print(f"  ⚠️  Measurement failed: {e}")
        print()

    # Measure M3: Struggling Detection Accuracy
    print("M3: Struggling Detection Accuracy")
    print("-" * 80)
    try:
        m3_pred = framework.predictions_dict['M3']
        observed, error = m3_pred.measure(data)
        validated, significance = m3_pred.validate(observed, error)

        print(f"  Predicted: Accuracy ≥ 70%")
        print(f"  Observed:  Accuracy = {observed:.3f} ± {error:.3f}")
        print(f"  Validated: {'✅ YES' if validated else '❌ NO'}")
        print(f"  Significance: {significance:.2f}σ")
        print()
    except Exception as e:
        print(f"  ⚠️  Measurement failed: {e}")
        print()

    # Measure M4: Optimal/Stable Prevalence
    print("M4: Optimal/Stable State Prevalence")
    print("-" * 80)
    try:
        m4_pred = framework.predictions_dict['M4']
        observed, error = m4_pred.measure(data)
        validated, significance = m4_pred.validate(observed, error)

        print(f"  Predicted: ≥60% in optimal/stable states")
        print(f"  Observed:  {observed:.3f} ± {error:.3f} ({observed*100:.1f}%)")
        print(f"  Validated: {'✅ YES' if validated else '❌ NO'}")
        print(f"  Significance: {significance:.2f}σ")
        print()
    except Exception as e:
        print(f"  ⚠️  Measurement failed: {e}")
        print()

    # Measure M5: Parameter Stability in Optimal
    print("M5: Parameter Stability in Optimal State")
    print("-" * 80)
    try:
        m5_pred = framework.predictions_dict['M5']
        observed, error = m5_pred.measure(data)
        validated, significance = m5_pred.validate(observed, error)

        print(f"  Predicted: Stability > 0.90 when optimal")
        print(f"  Observed:  Stability = {observed:.3f} ± {error:.3f}")
        print(f"  Validated: {'✅ YES' if validated else '❌ NO'}")
        print(f"  Significance: {significance:.2f}σ")
        print()
    except Exception as e:
        print(f"  ⚠️  Measurement failed: {e}")
        print()

    # Measure M6: Adaptation Frustration
    print("M6: Adaptation Frustration in Stable Conditions")
    print("-" * 80)
    try:
        m6_pred = framework.predictions_dict['M6']
        observed, error = m6_pred.measure(data)
        validated, significance = m6_pred.validate(observed, error)

        print(f"  Predicted: Frustration < 0.30")
        print(f"  Observed:  Frustration = {observed:.3f} ± {error:.3f}")
        print(f"  Validated: {'✅ YES' if validated else '❌ NO'}")
        print(f"  Significance: {significance:.2f}σ")
        print()
    except Exception as e:
        print(f"  ⚠️  Measurement failed: {e}")
        print()

    # Calculate combined significance for epistemic predictions
    print("=" * 80)
    print("Combined Significance (Epistemic Predictions)")
    print("=" * 80)
    print()

    epistemic_preds = [p for p in framework.predictions if p.id in ["M1", "M2", "M3", "M4", "M5", "M6"]]
    measured_count = sum(1 for p in epistemic_preds if p.observed_value is not None)
    validated_count = sum(1 for p in epistemic_preds if p.validated)

    if measured_count > 0:
        # Calculate combined significance for measured epistemic predictions
        chi_squared = sum(p.significance ** 2 for p in epistemic_preds if p.significance is not None)
        combined_sigma = np.sqrt(chi_squared)

        print(f"Measured predictions: {measured_count}/6")
        print(f"Validated predictions: {validated_count}/{measured_count}")
        print(f"Validation rate: {validated_count/measured_count:.1%}")
        print()
        print(f"Combined significance: {combined_sigma:.2f}σ")
        print()

        if combined_sigma >= 5.0:
            print("✅ Discovery threshold (5σ) exceeded!")
        elif combined_sigma >= 3.0:
            print("✅ Strong evidence (3σ)")
        elif combined_sigma >= 2.0:
            print("✅ Suggestive evidence (2σ)")
        else:
            print("⚠️  Evidence below significance threshold")

        print()
        print("Comparison to SAGE S33:")
        print(f"  SAGE: 18/18 predictions validated, 13.50σ combined")
        print(f"  Web4 Epistemic: {validated_count}/6 predictions validated, {combined_sigma:.2f}σ combined")
        print()

    # Show framework summary
    print("=" * 80)
    print("Full Framework Summary (17 base + 6 epistemic = 23 predictions)")
    print("=" * 80)
    print()
    summary = framework.get_extended_summary()
    print(f"Total predictions: {summary['total_predictions']}")
    print(f"Measured: {summary['measured_predictions']}")
    print(f"Validated: {summary['validated_predictions']}")
    if summary['measured_predictions'] > 0:
        print(f"Validation rate: {summary['validation_rate']:.1%}")
    print()
    print("Epistemic predictions (Session 16):")
    ep_stats = summary.get('epistemic_predictions', {})
    print(f"  Measured: {ep_stats.get('measured', 0)}/6")
    print(f"  Validated: {ep_stats.get('validated', 0)}/6")
    print(f"  Mean significance: {ep_stats.get('mean_significance', 0.0):.2f}σ")
    print()

    print("=" * 80)
    print("Demonstration Complete")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Integrate with long_duration_web4_validation.py for real data")
    print("2. Measure all 23 predictions (17 base + 6 epistemic)")
    print("3. Compare combined significance to SAGE S33 (target: ≥10σ)")
    print("4. Proceed to Phase 2: CoordinationProof extension (Session 16)")
    print()


if __name__ == "__main__":
    demonstrate_epistemic_measurements()
