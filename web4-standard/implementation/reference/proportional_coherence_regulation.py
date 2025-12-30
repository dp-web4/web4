#!/usr/bin/env python3
"""
Proportional Coherence Regulation - Session 105 Track 1

Implements proportional (gradient-based) regulation to avoid threshold attractors
discovered in Thor Session 138.

Problem (Binary Threshold Regulation):
- Below threshold: Little/no regulation
- Above threshold: Strong regulation
- Creates attractor at threshold (equilibrium lock)
- Same issue Thor discovered in emotional regulation!

Solution (Proportional Regulation):
- Regulation strength ∝ distance from ideal
- Continuous gradient, not on/off
- No hard thresholds, no attractors
- Mimics biological prefrontal cortex modulation

Inspired by: Thor Session 138 "Threshold Attractor Discovery"
Author: Claude (Session 105 Track 1)
Date: 2025-12-29
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
import math

# Import existing components
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from coherence_regulation import CoherenceRegulationConfig


@dataclass
class ProportionalRegulationConfig:
    """
    Configuration for proportional regulation

    Key difference from binary threshold:
    - target_ci: Ideal coherence target (not threshold)
    - regulation_strength: How strongly to pull toward target
    - gradient_smoothness: How smooth the transition (sigmoid parameter)
    """
    # Target coherence (ideal state, not hard threshold)
    target_ci: float = 0.7  # Aim for high but achievable coherence

    # Regulation strength
    max_boost: float = 0.3  # Maximum CI boost when very low
    max_penalty: float = 0.1  # Maximum CI reduction when anomalously high

    # Gradient smoothness (higher = smoother transitions)
    gradient_smoothness: float = 5.0  # Sigmoid steepness

    # Soft bounds (safety floor/ceiling, not attractors)
    absolute_min_ci: float = 0.1  # Safety floor (emergencies only)
    absolute_max_ci: float = 0.95  # Safety ceiling

    # Time-based recovery
    enable_temporal_recovery: bool = True
    recovery_rate_per_hour: float = 0.05  # Gradual drift toward target

    # Cascade prevention (proportional intervention, not binary)
    cascade_prevention_enabled: bool = True
    cascade_severity_threshold: float = 0.3  # Below this = severe
    max_cascade_boost: float = 0.4  # Emergency boost for cascades


def calculate_proportional_boost(
    current_ci: float,
    target_ci: float,
    max_boost: float,
    gradient_smoothness: float
) -> float:
    """
    Calculate proportional CI boost based on distance from target

    Uses sigmoid-based gradient:
    - Far below target → Strong boost
    - Near target → Minimal boost
    - At/above target → No boost

    Formula: boost = max_boost * sigmoid(distance_from_target)

    Args:
        current_ci: Current coherence index
        target_ci: Target coherence
        max_boost: Maximum boost amount
        gradient_smoothness: Sigmoid steepness (higher = smoother)

    Returns:
        Boost amount [0.0, max_boost]
    """
    # Distance from target (negative = below target)
    distance = current_ci - target_ci

    # If at/above target, no boost needed
    if distance >= 0:
        return 0.0

    # Sigmoid: S(x) = 1 / (1 + e^(-k*x))
    # For x < 0 (below target), this gives value in (0, 1)
    # k controls steepness
    k = gradient_smoothness
    sigmoid_value = 1 / (1 + math.exp(-k * distance))

    # Invert so below target = high value
    boost_factor = 1 - sigmoid_value

    return max_boost * boost_factor


def calculate_proportional_penalty(
    current_ci: float,
    target_ci: float,
    max_penalty: float,
    gradient_smoothness: float
) -> float:
    """
    Calculate proportional CI penalty for anomalously high CI

    Prevents CI inflation (e.g., from manipulated data).
    Uses gentle penalty above target.

    Args:
        current_ci: Current coherence index
        target_ci: Target coherence
        max_penalty: Maximum penalty amount
        gradient_smoothness: Sigmoid steepness

    Returns:
        Penalty amount [0.0, max_penalty]
    """
    # Distance from target (positive = above target)
    distance = current_ci - target_ci

    # If at/below target, no penalty
    if distance <= 0:
        return 0.0

    # Gentle sigmoid for above-target
    k = gradient_smoothness / 2  # Gentler than boost
    sigmoid_value = 1 / (1 + math.exp(-k * distance))

    return max_penalty * sigmoid_value


def apply_temporal_recovery(
    current_ci: float,
    target_ci: float,
    time_elapsed: timedelta,
    recovery_rate_per_hour: float
) -> float:
    """
    Apply gradual drift toward target CI over time

    Simulates natural recovery when no new issues occur.
    Rate is proportional to distance from target.

    Args:
        current_ci: Current coherence index
        target_ci: Target coherence
        time_elapsed: Time since last grounding
        recovery_rate_per_hour: Recovery rate per hour

    Returns:
        CI recovery amount (positive = boost, negative = reduction)
    """
    hours = time_elapsed.total_seconds() / 3600

    # Distance from target
    distance = target_ci - current_ci

    # Recovery proportional to distance
    # Far from target → faster recovery
    # Near target → slower recovery
    recovery_amount = distance * recovery_rate_per_hour * hours

    return recovery_amount


def detect_cascade_severity(ci_history: List[float]) -> float:
    """
    Calculate cascade severity as continuous gradient

    Instead of binary cascade/no-cascade, returns severity [0.0, 1.0]:
    - 0.0: No cascade
    - 0.5: Moderate downward trend
    - 1.0: Severe cascade

    Args:
        ci_history: Recent CI values (e.g., last 10)

    Returns:
        Cascade severity [0.0, 1.0]
    """
    if len(ci_history) < 3:
        return 0.0

    # Calculate trend (are we going down?)
    recent = ci_history[-5:]  # Last 5 CIs
    trend = (recent[-1] - recent[0]) / max(len(recent) - 1, 1)

    # Negative trend = potential cascade (must be significant)
    if trend >= -0.02:  # Ignore tiny fluctuations
        return 0.0  # No significant downward trend

    # Severity factors:
    # 1. How steep is the decline?
    steepness = min(abs(trend) / 0.2, 1.0)  # Normalize by -0.2 per step

    # 2. How low are we?
    current_low = max(0, 1 - recent[-1])  # Lower CI = higher severity

    # 3. How consistent is the decline?
    declines = sum(1 for i in range(1, len(recent)) if recent[i] < recent[i-1])
    consistency = declines / max(len(recent) - 1, 1)

    # Combine factors (require both steepness AND consistency)
    # Don't penalize minor fluctuations
    severity = (0.5 * steepness + 0.2 * current_low + 0.3 * consistency)

    return min(severity, 1.0)


def apply_proportional_cascade_prevention(
    current_ci: float,
    cascade_severity: float,
    max_cascade_boost: float
) -> float:
    """
    Apply proportional cascade prevention boost

    Boost proportional to cascade severity:
    - Low severity → Small boost
    - High severity → Large boost

    Args:
        current_ci: Current CI
        cascade_severity: Severity [0.0, 1.0]
        max_cascade_boost: Maximum boost for severe cascades

    Returns:
        Cascade prevention boost amount
    """
    # Boost proportional to severity
    boost = cascade_severity * max_cascade_boost

    return boost


class ProportionalCoherenceRegulator:
    """
    Proportional coherence regulator (no threshold attractors)

    Replaces binary threshold regulation with continuous gradient-based
    regulation inspired by biological prefrontal cortex modulation.

    Key differences from binary regulation:
    1. No hard thresholds → No attractors
    2. Regulation strength ∝ distance from target
    3. Smooth gradients → Natural variation preserved
    4. Cascade severity is continuous, not binary
    """

    def __init__(self, config: Optional[ProportionalRegulationConfig] = None):
        """Initialize proportional regulator"""
        self.config = config or ProportionalRegulationConfig()

    def regulate(
        self,
        current_ci: float,
        time_since_last_grounding: Optional[timedelta] = None,
        ci_history: Optional[List[float]] = None
    ) -> Tuple[float, Dict]:
        """
        Apply proportional regulation to CI

        Args:
            current_ci: Raw CI from coherence_index()
            time_since_last_grounding: Time elapsed (for temporal recovery)
            ci_history: Recent CI values (for cascade detection)

        Returns:
            (regulated_ci, metadata)
        """
        metadata = {
            'raw_ci': current_ci,
            'regulations_applied': [],
            'regulation_amounts': {}
        }

        regulated_ci = current_ci

        # 1. Proportional boost/penalty based on distance from target
        boost = calculate_proportional_boost(
            current_ci,
            self.config.target_ci,
            self.config.max_boost,
            self.config.gradient_smoothness
        )

        if boost > 0:
            regulated_ci += boost
            metadata['regulations_applied'].append('proportional_boost')
            metadata['regulation_amounts']['boost'] = boost

        penalty = calculate_proportional_penalty(
            current_ci,
            self.config.target_ci,
            self.config.max_penalty,
            self.config.gradient_smoothness
        )

        if penalty > 0:
            regulated_ci -= penalty
            metadata['regulations_applied'].append('proportional_penalty')
            metadata['regulation_amounts']['penalty'] = penalty

        # 2. Temporal recovery (gradual drift to target)
        if time_since_last_grounding and self.config.enable_temporal_recovery:
            recovery = apply_temporal_recovery(
                regulated_ci,
                self.config.target_ci,
                time_since_last_grounding,
                self.config.recovery_rate_per_hour
            )

            if abs(recovery) > 0.001:  # Non-trivial recovery
                regulated_ci += recovery
                metadata['regulations_applied'].append('temporal_recovery')
                metadata['regulation_amounts']['recovery'] = recovery

        # 3. Cascade prevention (proportional, not binary)
        if ci_history and self.config.cascade_prevention_enabled:
            cascade_severity = detect_cascade_severity(ci_history)
            metadata['cascade_severity'] = cascade_severity

            if cascade_severity > 0.2:  # Non-trivial cascade
                cascade_boost = apply_proportional_cascade_prevention(
                    regulated_ci,
                    cascade_severity,
                    self.config.max_cascade_boost
                )

                regulated_ci += cascade_boost
                metadata['regulations_applied'].append('cascade_prevention')
                metadata['regulation_amounts']['cascade_boost'] = cascade_boost

        # 4. Safety bounds (absolute floor/ceiling, rarely triggered)
        original_ci = regulated_ci

        if regulated_ci < self.config.absolute_min_ci:
            regulated_ci = self.config.absolute_min_ci
            metadata['regulations_applied'].append('safety_floor')
            metadata['regulation_amounts']['safety_clamp'] = regulated_ci - original_ci
        elif regulated_ci > self.config.absolute_max_ci:
            regulated_ci = self.config.absolute_max_ci
            metadata['regulations_applied'].append('safety_ceiling')
            metadata['regulation_amounts']['safety_clamp'] = regulated_ci - original_ci

        # Final metadata
        metadata['final_ci'] = regulated_ci
        metadata['total_adjustment'] = regulated_ci - current_ci
        metadata['target_ci'] = self.config.target_ci
        metadata['distance_from_target'] = abs(regulated_ci - self.config.target_ci)

        return (regulated_ci, metadata)


# ============================================================================
# Comparison Helper
# ============================================================================

def compare_binary_vs_proportional(
    ci_values: List[float],
    binary_threshold: float = 0.4,
    proportional_target: float = 0.7
) -> Dict:
    """
    Compare binary threshold regulation vs proportional regulation

    Args:
        ci_values: List of raw CI values to regulate
        binary_threshold: Threshold for binary regulation
        proportional_target: Target for proportional regulation

    Returns:
        Comparison statistics
    """
    from coherence_regulation import CoherenceRegulationManager, CoherenceRegulationConfig

    # Binary regulator
    binary_config = CoherenceRegulationConfig(cascade_ci_threshold=binary_threshold)
    binary_reg = CoherenceRegulationManager(binary_config)

    # Proportional regulator
    prop_config = ProportionalRegulationConfig(target_ci=proportional_target)
    prop_reg = ProportionalCoherenceRegulator(prop_config)

    binary_results = []
    proportional_results = []

    for i, ci in enumerate(ci_values):
        # Binary regulation (uses regulate_coherence method)
        binary_ci, _ = binary_reg.regulate_coherence("test", ci, ci_history=[(c, "") for c in ci_values[:i+1]])
        binary_results.append(binary_ci)

        # Proportional regulation
        prop_ci, _ = prop_reg.regulate(ci, ci_history=ci_values[:i+1])
        proportional_results.append(prop_ci)

    return {
        'raw': ci_values,
        'binary_regulated': binary_results,
        'proportional_regulated': proportional_results,
        'binary_variance': variance(binary_results),
        'proportional_variance': variance(proportional_results),
        'binary_mean': sum(binary_results) / len(binary_results),
        'proportional_mean': sum(proportional_results) / len(proportional_results)
    }


def variance(values: List[float]) -> float:
    """Calculate variance"""
    mean = sum(values) / len(values)
    return sum((x - mean) ** 2 for x in values) / len(values)


if __name__ == "__main__":
    print("Proportional Coherence Regulation - Session 105 Track 1")
    print("=" * 70)
    print("\nInspired by Thor Session 138: Threshold Attractor Discovery")
    print("\nKey Insight:")
    print("  Binary thresholds create attractors (equilibrium lock)")
    print("  Proportional regulation creates gradients (natural variation)")
    print("\nRegulator initialized with default proportional config")
    print(f"  Target CI: {ProportionalRegulationConfig().target_ci}")
    print(f"  Max boost: {ProportionalRegulationConfig().max_boost}")
    print(f"  Gradient smoothness: {ProportionalRegulationConfig().gradient_smoothness}")
