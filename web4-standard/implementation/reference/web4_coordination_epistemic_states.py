#!/usr/bin/env python3
"""
Web4 Coordination Epistemic States

Inspired by Thor S32 federated epistemic coordination, this module defines
epistemic state tracking for Web4 coordinators - enabling distributed
meta-coordination awareness.

Just as SAGE consciousnesses share epistemic state (confident, frustrated,
learning), Web4 coordinators can share coordination epistemic state (optimal,
struggling, adapting) to enable epistemic-aware task delegation.

Research Provenance:
- Thor S30: Epistemic state tracking for consciousness
- Thor S32: Federated epistemic coordination
- Web4 S15: Research arc complete (Track 54)
- Cross-domain synthesis: Universal patterns across Thor/Web4/Synchronism

Key Insight:
Meta-cognitive awareness (Thor) and meta-coordination awareness (Web4) are
manifestations of the same pattern - systems tracking their own quality and
limitations to enable better distributed coordination.

Usage:

    from web4_coordination_epistemic_states import (
        estimate_coordination_epistemic_state,
        CoordinationEpistemicState
    )

    # Get metrics from coordinator
    metrics = coordinator.get_metrics()

    # Estimate epistemic state
    epistemic = estimate_coordination_epistemic_state(metrics)

    print(f"State: {epistemic.primary_state().value}")
    print(f"Confidence: {epistemic.coordination_confidence:.2f}")
    print(f"Stability: {epistemic.parameter_stability:.2f}")
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import statistics


class CoordinationEpistemicState(Enum):
    """
    Coordination epistemic states - meta-awareness of coordination quality.

    Analogous to Thor S30 epistemic states (confident, uncertain, frustrated,
    confused, learning, stable) but applied to coordination rather than
    consciousness.
    """
    OPTIMAL = "optimal"          # High performance, stable satisfaction
    ADAPTING = "adapting"        # Active parameter adjustment
    STRUGGLING = "struggling"    # Repeated adaptation without improvement
    CONFLICTING = "conflicting"  # Multi-objective trade-offs challenging
    CONVERGING = "converging"    # Approaching satisfaction threshold
    STABLE = "stable"            # Satisfaction threshold maintained


@dataclass
class CoordinationEpistemicMetrics:
    """
    Quantified meta-coordination awareness metrics.

    Based on Thor S30 EpistemicMetrics pattern, adapted for coordination context.

    Attributes:
        coordination_confidence: How well coordination is working (0-1)
        parameter_stability: How stable coordination parameters are (0-1)
        objective_coherence: How aligned multi-objectives are (0-1)
        improvement_rate: Rate of performance improvement (can be negative)
        adaptation_frustration: Repeated adaptation without gain (0-1)
    """
    coordination_confidence: float  # 0-1
    parameter_stability: float      # 0-1
    objective_coherence: float      # 0-1
    improvement_rate: float         # Can be negative
    adaptation_frustration: float   # 0-1

    def primary_state(self) -> CoordinationEpistemicState:
        """
        Determine primary coordination epistemic state from metrics.

        Following Thor S30 pattern for state determination from metrics.
        Improved in Session 19 based on production metric analysis.

        Returns:
            Primary coordination epistemic state
        """
        # High frustration dominates (struggling)
        if self.adaptation_frustration > 0.7:
            return CoordinationEpistemicState.STRUGGLING

        # Low coherence → conflicting objectives
        if self.objective_coherence < 0.4:
            return CoordinationEpistemicState.CONFLICTING

        # High confidence + high stability → optimal
        # Session 19: Lowered from 0.9 to 0.85 based on production mean (0.843)
        if self.coordination_confidence > 0.85 and self.parameter_stability > 0.85:
            return CoordinationEpistemicState.OPTIMAL

        # High stability but moderate confidence → stable
        # Session 19: Moved before converging to fix cascade order
        if self.parameter_stability > 0.85 and self.coordination_confidence > 0.7:
            return CoordinationEpistemicState.STABLE

        # Moderate confidence with changing parameters → converging
        # Session 19: Added stability requirement (was missing)
        if 0.7 < self.coordination_confidence < 0.85 and self.parameter_stability < 0.85:
            return CoordinationEpistemicState.CONVERGING

        # Low stability (parameters changing) → adapting
        if self.parameter_stability < 0.5:
            return CoordinationEpistemicState.ADAPTING

        # Default: stable
        return CoordinationEpistemicState.STABLE

    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for logging/telemetry"""
        return {
            'coordination_confidence': self.coordination_confidence,
            'parameter_stability': self.parameter_stability,
            'objective_coherence': self.objective_coherence,
            'improvement_rate': self.improvement_rate,
            'adaptation_frustration': self.adaptation_frustration,
            'primary_state': self.primary_state().value
        }


def estimate_coordination_epistemic_state(
    metrics: Dict,
    history: Optional[List[Dict]] = None
) -> CoordinationEpistemicMetrics:
    """
    Estimate coordination epistemic state from Web4 coordinator metrics.

    Analogous to Thor S30's estimate_epistemic_metrics() for consciousness,
    but applied to coordination quality rather than understanding quality.

    This function bridges Web4 Track 52 (Production Coordinator) metrics
    to Thor S32 (Federated Epistemic) style epistemic awareness.

    Args:
        metrics: Current metrics from Web4ProductionCoordinator.get_metrics()
        history: Optional history of previous metrics for trend analysis

    Returns:
        CoordinationEpistemicMetrics with estimated epistemic state

    Example:
        >>> coordinator = Web4ProductionCoordinator()
        >>> # ... run coordination ...
        >>> metrics = coordinator.get_metrics()
        >>> epistemic = estimate_coordination_epistemic_state(metrics)
        >>> print(f"State: {epistemic.primary_state().value}")
        >>> print(f"Confidence: {epistemic.coordination_confidence:.2f}")
    """
    # 1. Coordination Confidence: Weighted multi-objective fitness
    #    How well is the coordinator performing overall?
    coverage = metrics.get('coverage', 0.0)
    quality = metrics.get('quality', 0.0)
    efficiency = metrics.get('efficiency', 0.0)

    # Use Track 52 default weights (coverage-priority: 50/30/20)
    coordination_confidence = (
        0.50 * coverage +
        0.30 * quality +
        0.20 * efficiency
    )

    # 2. Parameter Stability: How stable are coordination parameters?
    #    Low drift = high stability
    parameter_drift = metrics.get('parameter_drift_rate', 0.0)
    parameter_stability = max(0.0, min(1.0, 1.0 - parameter_drift))

    # Alternative: Use satisfaction stable windows as stability indicator
    stable_windows = metrics.get('satisfaction_stable_windows', 0)
    if stable_windows >= 3:
        # 3+ windows of stability → very stable
        parameter_stability = max(parameter_stability, 0.9)
    elif stable_windows == 2:
        parameter_stability = max(parameter_stability, 0.7)
    elif stable_windows == 1:
        parameter_stability = max(parameter_stability, 0.5)

    # 3. Objective Coherence: How aligned are multi-objectives?
    #    When quality and efficiency are both high → coherent
    #    When quality high but efficiency low → conflicting
    #    Use minimum as coherence measure (bottleneck)
    objective_coherence = min(quality, efficiency)

    # Alternative: Check if objectives are anti-correlated
    # (From Track 54 prediction M1: quality-efficiency correlation should be negative)
    # If both are high despite negative correlation → coherent resolution
    if quality > 0.8 and efficiency > 0.8:
        objective_coherence = max(objective_coherence, 0.8)

    # 4. Improvement Rate: Is performance getting better or worse?
    improvement_rate = 0.0

    # Use satisfaction history if available
    satisfaction_history = metrics.get('satisfaction_history', [])
    if len(satisfaction_history) >= 5:
        recent = satisfaction_history[-5:]
        # Linear trend: (last - first) / window_size
        improvement_rate = (recent[-1] - recent[0]) / 5.0
    elif history and len(history) >= 2:
        # Use historical coverage as proxy
        current_coverage = metrics.get('coverage', 0.0)
        prev_coverage = history[-1].get('coverage', current_coverage)
        improvement_rate = current_coverage - prev_coverage

    # 5. Adaptation Frustration: Repeated adaptation without satisfaction gain
    #    High adaptation count but low satisfaction improvement → frustrated
    adaptation_count = metrics.get('adaptation_count', 0)
    total_cycles = metrics.get('total_cycles', 1)

    if adaptation_count > 5 and total_cycles > 100:
        # Calculate adaptation frequency
        adaptation_frequency = adaptation_count / total_cycles

        # If adapting frequently (>5%) but not improving → frustrated
        if adaptation_frequency > 0.05:
            if improvement_rate < 0.01:  # Not improving
                adaptation_frustration = min(1.0, adaptation_frequency * 10)
            else:
                # Adapting and improving → not frustrated
                adaptation_frustration = 0.0
        else:
            # Low adaptation frequency → not frustrated
            adaptation_frustration = 0.0
    else:
        # Not enough data yet
        adaptation_frustration = 0.0

    return CoordinationEpistemicMetrics(
        coordination_confidence=coordination_confidence,
        parameter_stability=parameter_stability,
        objective_coherence=objective_coherence,
        improvement_rate=improvement_rate,
        adaptation_frustration=adaptation_frustration
    )


class CoordinationEpistemicTracker:
    """
    Tracks coordination epistemic states over time.

    Analogous to Thor S30 EpistemicStateTracker, adapted for coordination.
    """

    def __init__(self, history_size: int = 100):
        """
        Initialize coordination epistemic tracker.

        Args:
            history_size: Number of cycles to keep in history
        """
        self.history_size = history_size
        self.history: List[CoordinationEpistemicMetrics] = []
        self.cycle_count = 0

    def track(self, metrics: CoordinationEpistemicMetrics):
        """
        Track coordination epistemic metrics for a cycle.

        Args:
            metrics: Coordination epistemic metrics to track
        """
        self.history.append(metrics)
        if len(self.history) > self.history_size:
            self.history.pop(0)
        self.cycle_count += 1

    def current_state(self) -> Optional[CoordinationEpistemicMetrics]:
        """Get most recent coordination epistemic metrics"""
        return self.history[-1] if self.history else None

    def get_trend(self, metric: str, window: int = 10) -> Optional[str]:
        """
        Analyze trend in a specific metric.

        Args:
            metric: Metric name (coordination_confidence, parameter_stability, etc.)
            window: Number of recent cycles to analyze

        Returns:
            'improving', 'declining', 'stable', or None if insufficient data
        """
        if len(self.history) < window:
            return None

        recent = self.history[-window:]
        values = [getattr(m, metric) for m in recent]

        # Linear regression trend
        n = len(values)
        x = list(range(n))
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)

        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean)**2 for i in range(n))

        if denominator == 0:
            return 'stable'

        slope = numerator / denominator

        # Classify trend
        if slope > 0.01:
            return 'improving'
        elif slope < -0.01:
            return 'declining'
        else:
            return 'stable'

    def get_state_distribution(self) -> Dict[str, float]:
        """
        Get distribution of epistemic states over history.

        Returns:
            Dictionary mapping state names to frequencies (0-1)
        """
        if not self.history:
            return {}

        state_counts = {}
        for metrics in self.history:
            state = metrics.primary_state().value
            state_counts[state] = state_counts.get(state, 0) + 1

        total = len(self.history)
        return {state: count / total for state, count in state_counts.items()}

    def detect_struggling_pattern(self, window: int = 20) -> bool:
        """
        Detect sustained struggling pattern (high adaptation frustration).

        Args:
            window: Number of recent cycles to check

        Returns:
            True if sustained struggling detected
        """
        if len(self.history) < window:
            return False

        recent = self.history[-window:]
        struggling_count = sum(
            1 for m in recent
            if m.primary_state() == CoordinationEpistemicState.STRUGGLING
        )

        # If >50% of recent cycles are struggling → sustained pattern
        return struggling_count > (window / 2)

    def detect_improvement_trajectory(self, window: int = 10) -> bool:
        """
        Detect sustained improvement trajectory.

        Args:
            window: Number of recent cycles to check

        Returns:
            True if sustained improvement detected
        """
        trend = self.get_trend('coordination_confidence', window)
        return trend == 'improving'


if __name__ == "__main__":
    print("="*80)
    print("Web4 Coordination Epistemic States")
    print("="*80)
    print()
    print("Inspired by Thor S32 federated epistemic coordination")
    print("Enables distributed meta-coordination awareness for Web4")
    print()

    # Demo: Simulate different coordination scenarios
    scenarios = [
        {
            'name': 'Optimal Performance',
            'coverage': 0.95,
            'quality': 0.92,
            'efficiency': 0.88,
            'satisfaction_stable_windows': 5,
            'adaptation_count': 2,
            'total_cycles': 1000
        },
        {
            'name': 'Struggling to Converge',
            'coverage': 0.70,
            'quality': 0.65,
            'efficiency': 0.30,
            'satisfaction_stable_windows': 0,
            'adaptation_count': 50,
            'total_cycles': 500
        },
        {
            'name': 'Conflicting Objectives',
            'coverage': 0.85,
            'quality': 0.90,
            'efficiency': 0.25,  # Low efficiency despite good quality
            'satisfaction_stable_windows': 1,
            'adaptation_count': 10,
            'total_cycles': 800
        },
        {
            'name': 'Actively Adapting',
            'coverage': 0.75,
            'quality': 0.70,
            'efficiency': 0.65,
            'satisfaction_stable_windows': 1,
            'adaptation_count': 15,
            'total_cycles': 300,
            'satisfaction_history': [0.70, 0.72, 0.74, 0.76, 0.78]  # Improving
        },
        {
            'name': 'Stable Operation',
            'coverage': 0.93,
            'quality': 0.88,
            'efficiency': 0.82,
            'satisfaction_stable_windows': 3,
            'adaptation_count': 3,
            'total_cycles': 1500
        }
    ]

    for scenario in scenarios:
        name = scenario.pop('name')
        print(f"Scenario: {name}")
        print("-"*80)

        epistemic = estimate_coordination_epistemic_state(scenario)

        print(f"State: {epistemic.primary_state().value}")
        print(f"  Coordination Confidence: {epistemic.coordination_confidence:.2f}")
        print(f"  Parameter Stability: {epistemic.parameter_stability:.2f}")
        print(f"  Objective Coherence: {epistemic.objective_coherence:.2f}")
        print(f"  Improvement Rate: {epistemic.improvement_rate:+.3f}")
        print(f"  Adaptation Frustration: {epistemic.adaptation_frustration:.2f}")
        print()

    # Demo: Tracker
    print("="*80)
    print("Epistemic State Tracking Demo")
    print("="*80)
    print()

    tracker = CoordinationEpistemicTracker(history_size=50)

    # Simulate progression: struggling → adapting → converging → optimal
    import random
    for i in range(40):
        if i < 10:
            # Struggling phase
            metrics_dict = {
                'coverage': 0.60 + random.uniform(-0.1, 0.1),
                'quality': 0.55 + random.uniform(-0.1, 0.1),
                'efficiency': 0.25 + random.uniform(-0.05, 0.05),
                'satisfaction_stable_windows': 0,
                'adaptation_count': 5 + i,
                'total_cycles': 100 + i*10
            }
        elif i < 20:
            # Adapting phase
            progress = (i - 10) / 10
            metrics_dict = {
                'coverage': 0.70 + progress * 0.15,
                'quality': 0.65 + progress * 0.20,
                'efficiency': 0.30 + progress * 0.30,
                'satisfaction_stable_windows': 0 if i < 15 else 1,
                'adaptation_count': 15 + (i - 10),
                'total_cycles': 200 + i*10
            }
        elif i < 30:
            # Converging phase
            progress = (i - 20) / 10
            metrics_dict = {
                'coverage': 0.85 + progress * 0.08,
                'quality': 0.85 + progress * 0.05,
                'efficiency': 0.60 + progress * 0.25,
                'satisfaction_stable_windows': 1 if i < 25 else 2,
                'adaptation_count': 25 + (i - 20) // 2,
                'total_cycles': 300 + i*10
            }
        else:
            # Optimal phase
            metrics_dict = {
                'coverage': 0.93 + random.uniform(-0.02, 0.02),
                'quality': 0.90 + random.uniform(-0.02, 0.02),
                'efficiency': 0.85 + random.uniform(-0.03, 0.03),
                'satisfaction_stable_windows': 3 + (i - 30),
                'adaptation_count': 30,
                'total_cycles': 400 + i*10
            }

        epistemic = estimate_coordination_epistemic_state(metrics_dict)
        tracker.track(epistemic)

    # Print final state
    current = tracker.current_state()
    print(f"Current State: {current.primary_state().value}")
    print(f"  Confidence: {current.coordination_confidence:.2f}")
    print(f"  Stability: {current.parameter_stability:.2f}")
    print()

    # Print state distribution
    distribution = tracker.get_state_distribution()
    print("State Distribution:")
    for state, freq in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
        print(f"  {state}: {freq:.1%}")
    print()

    # Print trends
    print("Trends (last 10 cycles):")
    for metric in ['coordination_confidence', 'parameter_stability', 'objective_coherence']:
        trend = tracker.get_trend(metric, window=10)
        print(f"  {metric}: {trend}")
    print()

    # Check patterns
    if tracker.detect_improvement_trajectory():
        print("✓ Improvement trajectory detected")
    if tracker.detect_struggling_pattern():
        print("⚠ Struggling pattern detected")
    else:
        print("✓ No sustained struggling pattern")

    print()
    print("="*80)
    print("✓ Coordination epistemic states implementation complete!")
    print("✓ Ready for integration with Track 52 Production Coordinator")
    print("✓ Enables distributed meta-coordination awareness (Thor S32 pattern)")
    print("="*80)
    print()
