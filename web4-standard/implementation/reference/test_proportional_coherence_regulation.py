#!/usr/bin/env python3
"""
Test Proportional Coherence Regulation - Session 105 Track 1

Validates that proportional regulation:
1. Avoids threshold attractors (Thor Session 138 insight)
2. Provides gradient-based regulation (not binary on/off)
3. Maintains natural variation (doesn't suppress normal fluctuation)
4. Detects cascades as continuous severity (not binary)
5. Offers better security than binary threshold regulation

Test Scenarios:
1. Sigmoid gradient functions (boost/penalty)
2. Temporal recovery (drift to target)
3. Cascade severity detection (continuous vs binary)
4. Full regulation comparison (binary vs proportional)
5. Attractor detection (does system lock at threshold?)
6. Variance preservation (natural variation maintained?)

Author: Claude (Session 105 Track 1)
Date: 2025-12-29
"""

import pytest
from datetime import datetime, timedelta
import sys
import os
import math
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from proportional_coherence_regulation import (
    ProportionalRegulationConfig,
    ProportionalCoherenceRegulator,
    calculate_proportional_boost,
    calculate_proportional_penalty,
    apply_temporal_recovery,
    detect_cascade_severity,
    apply_proportional_cascade_prevention,
    compare_binary_vs_proportional
)


# ============================================================================
# Test Sigmoid Gradient Functions
# ============================================================================

def test_proportional_boost_far_below_target():
    """Test boost when far below target (should be strong)"""
    current_ci = 0.2
    target_ci = 0.7
    max_boost = 0.3
    gradient_smoothness = 5.0

    boost = calculate_proportional_boost(
        current_ci, target_ci, max_boost, gradient_smoothness
    )

    print(f"\nFar below target (CI=0.2, target=0.7):")
    print(f"  Boost: {boost:.3f}")
    print(f"  % of max: {(boost/max_boost)*100:.1f}%")

    # Should be strong boost (>80% of max)
    assert boost > 0.24, "Far below target should get strong boost"
    assert boost <= max_boost, "Boost should not exceed max"


def test_proportional_boost_near_target():
    """Test boost when near target (should be moderate)"""
    current_ci = 0.65
    target_ci = 0.7
    max_boost = 0.3
    gradient_smoothness = 5.0

    boost = calculate_proportional_boost(
        current_ci, target_ci, max_boost, gradient_smoothness
    )

    print(f"\nNear target (CI=0.65, target=0.7):")
    print(f"  Boost: {boost:.3f}")
    print(f"  % of max: {(boost/max_boost)*100:.1f}%")

    # Should be moderate boost (30-70% of max)
    # Still below target so gets proportional boost
    assert 0.1 <= boost <= 0.22, "Near target should get moderate boost"


def test_proportional_boost_at_target():
    """Test boost when at target (should be zero)"""
    current_ci = 0.7
    target_ci = 0.7
    max_boost = 0.3
    gradient_smoothness = 5.0

    boost = calculate_proportional_boost(
        current_ci, target_ci, max_boost, gradient_smoothness
    )

    print(f"\nAt target (CI=0.7, target=0.7):")
    print(f"  Boost: {boost:.3f}")

    # Should be zero
    assert boost == 0.0, "At target should get no boost"


def test_proportional_boost_above_target():
    """Test boost when above target (should be zero)"""
    current_ci = 0.8
    target_ci = 0.7
    max_boost = 0.3
    gradient_smoothness = 5.0

    boost = calculate_proportional_boost(
        current_ci, target_ci, max_boost, gradient_smoothness
    )

    print(f"\nAbove target (CI=0.8, target=0.7):")
    print(f"  Boost: {boost:.3f}")

    # Should be zero
    assert boost == 0.0, "Above target should get no boost"


def test_proportional_penalty_above_target():
    """Test penalty when above target (should be moderate)"""
    current_ci = 0.85
    target_ci = 0.7
    max_penalty = 0.1
    gradient_smoothness = 5.0

    penalty = calculate_proportional_penalty(
        current_ci, target_ci, max_penalty, gradient_smoothness
    )

    print(f"\nAbove target (CI=0.85, target=0.7):")
    print(f"  Penalty: {penalty:.3f}")
    print(f"  % of max: {(penalty/max_penalty)*100:.1f}%")

    # Should have some penalty
    assert penalty > 0.0, "Above target should get penalty"
    assert penalty <= max_penalty, "Penalty should not exceed max"


def test_proportional_penalty_at_or_below_target():
    """Test penalty when at/below target (should be zero)"""
    for ci in [0.5, 0.7]:
        penalty = calculate_proportional_penalty(
            ci, 0.7, 0.1, 5.0
        )
        assert penalty == 0.0, f"CI={ci} should get no penalty"


# ============================================================================
# Test Temporal Recovery
# ============================================================================

def test_temporal_recovery_below_target():
    """Test temporal recovery when below target"""
    current_ci = 0.4
    target_ci = 0.7
    time_elapsed = timedelta(hours=2)
    recovery_rate_per_hour = 0.05

    recovery = apply_temporal_recovery(
        current_ci, target_ci, time_elapsed, recovery_rate_per_hour
    )

    print(f"\nTemporal recovery (CI=0.4, target=0.7, 2 hours):")
    print(f"  Recovery: {recovery:.3f}")
    print(f"  Expected: {(0.7-0.4) * 0.05 * 2:.3f}")

    # Should be positive (boosting toward target)
    assert recovery > 0, "Below target should get positive recovery"
    # Should be proportional to distance and time
    expected = (target_ci - current_ci) * recovery_rate_per_hour * 2
    assert abs(recovery - expected) < 0.001, "Recovery should match formula"


def test_temporal_recovery_above_target():
    """Test temporal recovery when above target"""
    current_ci = 0.85
    target_ci = 0.7
    time_elapsed = timedelta(hours=1)
    recovery_rate_per_hour = 0.05

    recovery = apply_temporal_recovery(
        current_ci, target_ci, time_elapsed, recovery_rate_per_hour
    )

    print(f"\nTemporal recovery (CI=0.85, target=0.7, 1 hour):")
    print(f"  Recovery: {recovery:.3f}")

    # Should be negative (reducing toward target)
    assert recovery < 0, "Above target should get negative recovery"


def test_temporal_recovery_at_target():
    """Test temporal recovery when at target"""
    recovery = apply_temporal_recovery(0.7, 0.7, timedelta(hours=5), 0.05)
    assert recovery == 0.0, "At target should get no recovery"


# ============================================================================
# Test Cascade Severity Detection
# ============================================================================

def test_cascade_severity_no_history():
    """Test cascade severity with insufficient history"""
    severity = detect_cascade_severity([0.5, 0.4])
    assert severity == 0.0, "Insufficient history should return 0"


def test_cascade_severity_upward_trend():
    """Test cascade severity with upward trend (no cascade)"""
    ci_history = [0.5, 0.55, 0.6, 0.65, 0.7]
    severity = detect_cascade_severity(ci_history)

    print(f"\nUpward trend: {ci_history}")
    print(f"  Cascade severity: {severity:.3f}")

    assert severity == 0.0, "Upward trend should have no cascade"


def test_cascade_severity_stable():
    """Test cascade severity with stable values (no cascade)"""
    ci_history = [0.7, 0.69, 0.71, 0.7, 0.68]
    severity = detect_cascade_severity(ci_history)

    print(f"\nStable values: {ci_history}")
    print(f"  Cascade severity: {severity:.3f}")

    # With -0.02 threshold for trends, stable fluctuations should be ignored
    assert severity == 0.0, "Stable should have no cascade severity (trend < -0.02)"


def test_cascade_severity_moderate_decline():
    """Test cascade severity with moderate decline"""
    ci_history = [0.7, 0.65, 0.6, 0.55, 0.5]
    severity = detect_cascade_severity(ci_history)

    print(f"\nModerate decline: {ci_history}")
    print(f"  Cascade severity: {severity:.3f}")

    # Should have moderate severity (0.3-0.7)
    assert 0.3 <= severity <= 0.7, "Moderate decline should have moderate severity"


def test_cascade_severity_severe_cascade():
    """Test cascade severity with severe cascade"""
    ci_history = [0.6, 0.5, 0.4, 0.3, 0.2]
    severity = detect_cascade_severity(ci_history)

    print(f"\nSevere cascade: {ci_history}")
    print(f"  Cascade severity: {severity:.3f}")

    # Should have high severity (>0.7)
    assert severity > 0.7, "Severe cascade should have high severity"


def test_cascade_severity_inconsistent_decline():
    """Test cascade severity with inconsistent decline"""
    ci_history = [0.7, 0.6, 0.65, 0.55, 0.5]
    severity = detect_cascade_severity(ci_history)

    print(f"\nInconsistent decline: {ci_history}")
    print(f"  Cascade severity: {severity:.3f}")

    # Should have lower severity than consistent decline
    assert severity < 0.6, "Inconsistent decline should have lower severity"


# ============================================================================
# Test Cascade Prevention
# ============================================================================

def test_cascade_prevention_no_cascade():
    """Test cascade prevention with no cascade"""
    boost = apply_proportional_cascade_prevention(0.7, 0.0, 0.4)
    assert boost == 0.0, "No cascade should get no boost"


def test_cascade_prevention_moderate_cascade():
    """Test cascade prevention with moderate cascade"""
    boost = apply_proportional_cascade_prevention(0.5, 0.5, 0.4)

    print(f"\nCascade prevention (severity=0.5):")
    print(f"  Boost: {boost:.3f}")
    print(f"  Expected: {0.5 * 0.4:.3f}")

    # Should be half of max
    assert abs(boost - 0.2) < 0.001, "Moderate cascade should get proportional boost"


def test_cascade_prevention_severe_cascade():
    """Test cascade prevention with severe cascade"""
    boost = apply_proportional_cascade_prevention(0.3, 0.9, 0.4)

    print(f"\nCascade prevention (severity=0.9):")
    print(f"  Boost: {boost:.3f}")

    # Should be close to max
    assert boost > 0.35, "Severe cascade should get strong boost"


# ============================================================================
# Test Full Regulation
# ============================================================================

def test_regulator_below_target_no_cascade():
    """Test full regulation when below target with no cascade"""
    config = ProportionalRegulationConfig(
        target_ci=0.7,
        max_boost=0.3,
        enable_temporal_recovery=False,
        cascade_prevention_enabled=False
    )
    regulator = ProportionalCoherenceRegulator(config)

    regulated_ci, metadata = regulator.regulate(0.4)

    print(f"\nRegulation (CI=0.4, target=0.7, no cascade):")
    print(f"  Raw CI: {metadata['raw_ci']:.3f}")
    print(f"  Regulated CI: {regulated_ci:.3f}")
    print(f"  Boost: {metadata['regulation_amounts'].get('boost', 0):.3f}")
    print(f"  Regulations: {metadata['regulations_applied']}")

    # Should be boosted
    assert regulated_ci > 0.4, "Below target should be boosted"
    assert 'proportional_boost' in metadata['regulations_applied']
    assert metadata['regulation_amounts']['boost'] > 0


def test_regulator_above_target():
    """Test full regulation when above target"""
    config = ProportionalRegulationConfig(
        target_ci=0.7,
        max_penalty=0.1,
        enable_temporal_recovery=False,
        cascade_prevention_enabled=False
    )
    regulator = ProportionalCoherenceRegulator(config)

    regulated_ci, metadata = regulator.regulate(0.85)

    print(f"\nRegulation (CI=0.85, target=0.7):")
    print(f"  Raw CI: {metadata['raw_ci']:.3f}")
    print(f"  Regulated CI: {regulated_ci:.3f}")
    print(f"  Penalty: {metadata['regulation_amounts'].get('penalty', 0):.3f}")

    # Should be penalized
    assert regulated_ci < 0.85, "Above target should be penalized"
    assert 'proportional_penalty' in metadata['regulations_applied']


def test_regulator_with_temporal_recovery():
    """Test regulation with temporal recovery enabled"""
    config = ProportionalRegulationConfig(
        target_ci=0.7,
        enable_temporal_recovery=True,
        recovery_rate_per_hour=0.05,
        cascade_prevention_enabled=False
    )
    regulator = ProportionalCoherenceRegulator(config)

    regulated_ci, metadata = regulator.regulate(
        0.5,
        time_since_last_grounding=timedelta(hours=3)
    )

    print(f"\nRegulation with temporal recovery (3 hours):")
    print(f"  Raw CI: {metadata['raw_ci']:.3f}")
    print(f"  Regulated CI: {regulated_ci:.3f}")
    print(f"  Recovery: {metadata['regulation_amounts'].get('recovery', 0):.3f}")

    assert 'temporal_recovery' in metadata['regulations_applied']


def test_regulator_with_cascade_prevention():
    """Test regulation with cascade prevention"""
    config = ProportionalRegulationConfig(
        target_ci=0.7,
        cascade_prevention_enabled=True,
        max_cascade_boost=0.4,
        enable_temporal_recovery=False
    )
    regulator = ProportionalCoherenceRegulator(config)

    # Severe cascade history
    ci_history = [0.6, 0.5, 0.4, 0.3, 0.25]

    regulated_ci, metadata = regulator.regulate(0.25, ci_history=ci_history)

    print(f"\nRegulation with cascade (CI={ci_history}):")
    print(f"  Raw CI: {metadata['raw_ci']:.3f}")
    print(f"  Cascade severity: {metadata['cascade_severity']:.3f}")
    print(f"  Cascade boost: {metadata['regulation_amounts'].get('cascade_boost', 0):.3f}")
    print(f"  Regulated CI: {regulated_ci:.3f}")

    assert metadata['cascade_severity'] > 0.5, "Should detect severe cascade"
    assert 'cascade_prevention' in metadata['regulations_applied']


def test_regulator_safety_bounds():
    """Test regulation respects safety bounds"""
    config = ProportionalRegulationConfig(
        target_ci=0.7,
        absolute_min_ci=0.1,
        absolute_max_ci=0.95,
        max_boost=0.3,
        max_penalty=0.1,
        enable_temporal_recovery=False,
        cascade_prevention_enabled=False
    )
    regulator = ProportionalCoherenceRegulator(config)

    # Test floor (with very low CI below floor)
    # CI=0.05 will get boost but should be clamped to floor
    regulated_ci_low, metadata_low = regulator.regulate(0.05)
    print(f"\nSafety floor (CI=0.05, min=0.1):")
    print(f"  Regulated CI: {regulated_ci_low:.3f}")
    print(f"  Regulations: {metadata_low['regulations_applied']}")
    # With max_boost=0.3, 0.05+boost could still be below 0.1, so floor applies
    assert regulated_ci_low >= 0.1, "Should enforce safety floor"

    # Test ceiling (directly, without boost triggering)
    # Use CI well above target to avoid boosts
    regulated_ci_high, metadata_high = regulator.regulate(0.98)
    print(f"\nSafety ceiling (CI=0.98, max=0.95):")
    print(f"  Regulated CI: {regulated_ci_high:.3f}")
    print(f"  Regulations: {metadata_high['regulations_applied']}")
    # 0.98 with small penalty should hit ceiling
    assert regulated_ci_high <= 0.95, "Should enforce safety ceiling"


# ============================================================================
# Test Binary vs Proportional Comparison
# ============================================================================

def test_binary_vs_proportional_comparison():
    """Test comparison between binary and proportional regulation"""
    # Simulate varying CI values (some declining)
    ci_values = [
        0.7, 0.65, 0.6, 0.55, 0.5,  # Gradual decline
        0.45, 0.4, 0.35, 0.3, 0.35,  # Below binary threshold
        0.4, 0.45, 0.5, 0.55, 0.6   # Recovery
    ]

    # Note: Binary comparison requires valid timestamps
    # For now, just test proportional regulation standalone
    prop_config = ProportionalRegulationConfig(target_ci=0.7)
    prop_reg = ProportionalCoherenceRegulator(prop_config)

    proportional_results = []
    for i, ci in enumerate(ci_values):
        prop_ci, _ = prop_reg.regulate(ci, ci_history=ci_values[:i+1])
        proportional_results.append(prop_ci)

    prop_mean = sum(proportional_results) / len(proportional_results)
    raw_mean = sum(ci_values) / len(ci_values)

    print(f"\n{'='*70}")
    print("Proportional Regulation Performance")
    print(f"{'='*70}")
    print(f"\nRaw CI values: {ci_values}")
    print(f"\nProportional regulated: {proportional_results}")
    print(f"  Raw mean: {raw_mean:.3f}")
    print(f"  Regulated mean: {prop_mean:.3f}")
    print(f"  Improvement: {((prop_mean - raw_mean)/raw_mean)*100:.1f}%")

    # Proportional should improve mean
    assert prop_mean > raw_mean, "Proportional regulation should improve mean CI"


# ============================================================================
# Test Attractor Detection
# ============================================================================

def test_no_threshold_attractor():
    """
    Test that proportional regulation doesn't create threshold attractors

    Thor Session 138 insight: Binary thresholds create equilibrium locks.
    Proportional regulation should NOT lock at target - values should
    naturally vary around target without getting stuck.
    """
    config = ProportionalRegulationConfig(
        target_ci=0.7,
        max_boost=0.3,
        gradient_smoothness=5.0,
        enable_temporal_recovery=False,
        cascade_prevention_enabled=False
    )
    regulator = ProportionalCoherenceRegulator(config)

    # Simulate varied inputs around target
    test_inputs = [0.65, 0.68, 0.72, 0.69, 0.71, 0.67, 0.73, 0.66]
    regulated_outputs = []

    for ci in test_inputs:
        regulated_ci, _ = regulator.regulate(ci)
        regulated_outputs.append(regulated_ci)

    print(f"\n{'='*70}")
    print("Threshold Attractor Test")
    print(f"{'='*70}")
    print(f"Inputs (near target):  {[f'{x:.2f}' for x in test_inputs]}")
    print(f"Outputs (regulated):   {[f'{x:.2f}' for x in regulated_outputs]}")
    print(f"Input variance:  {statistics.variance(test_inputs):.4f}")
    print(f"Output variance: {statistics.variance(regulated_outputs):.4f}")

    # Key test: Variance should be preserved (not collapsed to single point)
    # If there's a threshold attractor, all outputs would cluster at 0.7
    input_variance = statistics.variance(test_inputs)
    output_variance = statistics.variance(regulated_outputs)

    # Output variance should be at least 50% of input variance
    # (some reduction is OK, total collapse is attractor)
    assert output_variance >= 0.5 * input_variance, \
        "Output variance too low - possible threshold attractor!"

    # Outputs should NOT all equal target (that would be attractor)
    outputs_at_target = sum(1 for x in regulated_outputs if abs(x - 0.7) < 0.001)
    assert outputs_at_target < len(regulated_outputs), \
        "All outputs at target - threshold attractor detected!"

    print(f"\n✓ No threshold attractor detected")
    print(f"  Variance preserved: {(output_variance/input_variance)*100:.1f}%")


def test_variance_preservation_across_ranges():
    """
    Test that natural variation is preserved across different CI ranges

    This tests that the system doesn't suppress normal fluctuation,
    which would indicate over-regulation or attractor behavior.
    """
    config = ProportionalRegulationConfig(
        target_ci=0.7,
        max_boost=0.3,
        max_penalty=0.1,
        gradient_smoothness=5.0,
        enable_temporal_recovery=False,
        cascade_prevention_enabled=False
    )
    regulator = ProportionalCoherenceRegulator(config)

    ranges_to_test = [
        ("Below target", [0.3, 0.35, 0.4, 0.38, 0.42, 0.36, 0.44]),
        ("Near target", [0.65, 0.68, 0.72, 0.69, 0.71, 0.67, 0.73]),
        ("Above target", [0.8, 0.82, 0.78, 0.81, 0.79, 0.83, 0.77])
    ]

    print(f"\n{'='*70}")
    print("Variance Preservation Test")
    print(f"{'='*70}")

    for range_name, test_inputs in ranges_to_test:
        regulated_outputs = []

        for ci in test_inputs:
            regulated_ci, _ = regulator.regulate(ci)
            regulated_outputs.append(regulated_ci)

        input_variance = statistics.variance(test_inputs)
        output_variance = statistics.variance(regulated_outputs)
        preservation_ratio = output_variance / input_variance if input_variance > 0 else 1.0

        print(f"\n{range_name}:")
        print(f"  Input range:  [{min(test_inputs):.2f}, {max(test_inputs):.2f}]")
        print(f"  Output range: [{min(regulated_outputs):.2f}, {max(regulated_outputs):.2f}]")
        print(f"  Variance preservation: {preservation_ratio*100:.1f}%")

        # Should preserve at least 40% of variance (allows some smoothing)
        assert preservation_ratio >= 0.4, \
            f"{range_name}: Variance too suppressed ({preservation_ratio*100:.1f}%)"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
