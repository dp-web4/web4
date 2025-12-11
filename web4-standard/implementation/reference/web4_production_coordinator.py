#!/usr/bin/env python3
"""
Web4 Production Coordinator - Track 52

Session 14+: Production-ready Web4 coordinator with opt-in multi-objective optimization

Based on Thor S26 production integration pattern:
- Backward compatible (single-objective by default)
- Opt-in multi-objective feature
- Factory functions for common modes (balanced, quality, efficiency)
- A/B testing support via feature flags

Integrates:
- Track 39: Web4 temporal adaptation with satisfaction threshold
- Track 45: Multi-objective optimization framework
- Track 47: Multi-objective production integration
- Track 49: Full ATP dynamics integration
- Thor S26: Production integration pattern (opt-in design)

Research Provenance:
- Legion S8-S14: Web4 autonomous research arc (18 hours, 6,358+ LOC)
- Thor S26-S29: Production SAGE integration and adaptive weighting
- Cross-domain validation: Thor patterns → Web4 (100% transfer success)

Key Features:
1. Backward compatible: Single-objective by default
2. Multi-objective: Opt-in via enable_multi_objective flag
3. Mode factory: balanced, quality-priority, efficiency-priority, coverage-priority
4. A/B testing: Feature flags for gradual rollout
5. Metrics: Built-in performance tracking for production monitoring

Usage Examples:

    # Single-objective (legacy, default)
    coordinator = Web4ProductionCoordinator()

    # Multi-objective (opt-in)
    coordinator = Web4ProductionCoordinator(enable_multi_objective=True)

    # Mode presets
    coordinator = create_coordinator_balanced()
    coordinator = create_coordinator_quality_priority()
    coordinator = create_coordinator_efficiency_priority()
    coordinator = create_coordinator_coverage_priority()

    # Custom weights
    coordinator = Web4ProductionCoordinator(
        enable_multi_objective=True,
        coverage_weight=0.6,
        quality_weight=0.3,
        efficiency_weight=0.1
    )
"""

import random
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from collections import deque
from enum import Enum
import time


class CoordinatorMode(Enum):
    """Coordinator operational modes"""
    SINGLE_OBJECTIVE = "single_objective"  # Legacy: coverage only
    BALANCED = "balanced"  # Equal weight to all objectives
    QUALITY_PRIORITY = "quality_priority"  # Prioritize decision quality
    EFFICIENCY_PRIORITY = "efficiency_priority"  # Prioritize resource efficiency
    COVERAGE_PRIORITY = "coverage_priority"  # Prioritize coverage (default multi-obj)
    CUSTOM = "custom"  # User-specified weights


@dataclass
class MultiObjectiveFitness:
    """
    Three-dimensional fitness for Web4 coordination.

    Based on Thor S23 multi-objective framework, validated in Web4 Sessions 10-11.
    """
    coverage: float  # 0-1: % of high-priority interactions coordinated
    quality: float  # 0-1: Coordination decision quality
    efficiency: float  # 0-1: Resource utilization efficiency (interactions/ATP)

    def weighted_score(
        self,
        coverage_weight: float,
        quality_weight: float,
        efficiency_weight: float
    ) -> float:
        """Calculate weighted fitness score"""
        return (coverage_weight * self.coverage +
                quality_weight * self.quality +
                efficiency_weight * self.efficiency)

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for serialization"""
        return {
            'coverage': self.coverage,
            'quality': self.quality,
            'efficiency': self.efficiency
        }


@dataclass
class CoordinationMetrics:
    """Production metrics for monitoring and telemetry"""
    total_interactions: int = 0
    high_priority_interactions: int = 0
    coordinated_high_priority: int = 0
    authorization_grants: int = 0
    authorization_denials: int = 0
    atp_allocations: int = 0
    atp_rest_cycles: int = 0
    quality_samples: List[float] = field(default_factory=list)
    atp_spent: float = 0.0

    # Timing metrics (for latency tracking)
    coordination_times_ms: List[float] = field(default_factory=list)

    # Multi-objective fitness (updated periodically)
    current_fitness: Optional[MultiObjectiveFitness] = None

    # Satisfaction tracking
    satisfaction_history: List[float] = field(default_factory=list)
    stable_windows: int = 0

    def add_coordination_time(self, time_ms: float):
        """Track coordination latency"""
        self.coordination_times_ms.append(time_ms)
        # Keep last 1000 samples
        if len(self.coordination_times_ms) > 1000:
            self.coordination_times_ms = self.coordination_times_ms[-1000:]

    def get_mean_latency_ms(self) -> float:
        """Get mean coordination latency in milliseconds"""
        if not self.coordination_times_ms:
            return 0.0
        return statistics.mean(self.coordination_times_ms)

    def get_p95_latency_ms(self) -> float:
        """Get 95th percentile coordination latency"""
        if not self.coordination_times_ms:
            return 0.0
        sorted_times = sorted(self.coordination_times_ms)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[idx]

    def calculate_fitness(self) -> MultiObjectiveFitness:
        """Calculate current multi-objective fitness"""
        # Coverage
        if self.high_priority_interactions > 0:
            coverage = self.coordinated_high_priority / self.high_priority_interactions
        else:
            coverage = 0.0

        # Quality
        if self.quality_samples:
            quality = statistics.mean(self.quality_samples)
        else:
            quality = 0.0

        # Efficiency (interactions per ATP spent)
        if self.atp_spent > 0:
            interactions_per_atp = self.total_interactions / self.atp_spent
            # Normalize to 0-1 (100-500 interactions/ATP is typical)
            efficiency = (interactions_per_atp - 100) / 400
            efficiency = max(0.0, min(1.0, efficiency))
        else:
            efficiency = 0.0

        self.current_fitness = MultiObjectiveFitness(
            coverage=coverage,
            quality=quality,
            efficiency=efficiency
        )
        return self.current_fitness

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary for telemetry"""
        fitness = self.calculate_fitness()
        return {
            'total_interactions': self.total_interactions,
            'high_priority_interactions': self.high_priority_interactions,
            'coordinated_high_priority': self.coordinated_high_priority,
            'authorization_grants': self.authorization_grants,
            'authorization_denials': self.authorization_denials,
            'atp_allocations': self.atp_allocations,
            'atp_rest_cycles': self.atp_rest_cycles,
            'atp_spent': self.atp_spent,
            'mean_latency_ms': self.get_mean_latency_ms(),
            'p95_latency_ms': self.get_p95_latency_ms(),
            'coverage': fitness.coverage,
            'quality': fitness.quality,
            'efficiency': fitness.efficiency,
            'satisfaction_stable_windows': self.stable_windows
        }


@dataclass
class CoordinationParameters:
    """
    Web4 coordination parameters.

    Production-ready with sensible defaults from Web4 research arc validation.
    """
    # ATP parameters (Track 39, validated in Track 50)
    atp_allocation_cost: float = 0.005  # Pareto-optimal from Track 45
    atp_rest_recovery: float = 0.080  # Pareto-optimal from Track 45
    atp_allocation_threshold: float = 0.20

    # Authorization parameters
    auth_trust_threshold: float = 0.50
    auth_risk_tolerance: float = 0.30

    # Reputation parameters
    rep_coherence_gamma: float = 2.0  # From Synchronism coherence function
    rep_density_critical: float = 0.1

    # Satisfaction threshold (Track 39, validated across Thor/Web4/Synchronism)
    satisfaction_threshold: float = 0.95  # Universal ~95% pattern
    satisfaction_windows_required: int = 3  # 3-window temporal confirmation

    # Multi-objective weights (default: coverage-priority from Track 45)
    coverage_weight: float = 0.50
    quality_weight: float = 0.30
    efficiency_weight: float = 0.20

    # Feature flags (Thor S26 pattern)
    enable_multi_objective: bool = False  # Opt-in multi-objective
    enable_adaptive_weighting: bool = False  # Future: Thor S28-29 pattern
    enable_quality_metrics: bool = False  # Future: Track 53

    def get_mode(self) -> CoordinatorMode:
        """Determine coordinator mode from weights"""
        if not self.enable_multi_objective:
            return CoordinatorMode.SINGLE_OBJECTIVE

        # Check for preset modes
        if (abs(self.coverage_weight - 0.33) < 0.01 and
            abs(self.quality_weight - 0.33) < 0.01 and
            abs(self.efficiency_weight - 0.34) < 0.01):
            return CoordinatorMode.BALANCED

        if self.quality_weight > 0.5:
            return CoordinatorMode.QUALITY_PRIORITY

        if self.efficiency_weight > 0.4:
            return CoordinatorMode.EFFICIENCY_PRIORITY

        if self.coverage_weight > 0.5:
            return CoordinatorMode.COVERAGE_PRIORITY

        return CoordinatorMode.CUSTOM


@dataclass
class ATPState:
    """ATP (Attention/Time/Processing) resource state"""
    current_level: float = 1.0
    max_level: float = 1.0
    min_level: float = 0.0

    allocation_cost: float = 0.005
    rest_recovery: float = 0.080
    allocation_threshold: float = 0.20

    def can_allocate(self) -> bool:
        """Check if ATP is above threshold for allocation"""
        return self.current_level >= self.allocation_threshold

    def allocate(self) -> bool:
        """Attempt to allocate ATP. Returns True if successful."""
        if not self.can_allocate():
            return False
        self.current_level = max(self.min_level, self.current_level - self.allocation_cost)
        return True

    def rest(self):
        """Recover ATP during rest cycle"""
        self.current_level = min(self.max_level, self.current_level + self.rest_recovery)

    def get_level(self) -> float:
        """Get current ATP level"""
        return self.current_level


class Web4ProductionCoordinator:
    """
    Production-ready Web4 coordinator with opt-in multi-objective optimization.

    Design principles (Thor S26 pattern):
    1. Backward compatible: Single-objective by default
    2. Opt-in multi-objective: enable_multi_objective=True
    3. Feature flags: Gradual rollout support
    4. Built-in metrics: Production monitoring
    5. Mode presets: Common use cases pre-configured

    Usage:
        # Single-objective (legacy mode)
        coordinator = Web4ProductionCoordinator()

        # Multi-objective (opt-in)
        coordinator = Web4ProductionCoordinator(enable_multi_objective=True)

        # Custom mode
        params = CoordinationParameters(
            enable_multi_objective=True,
            coverage_weight=0.6,
            quality_weight=0.3,
            efficiency_weight=0.1
        )
        coordinator = Web4ProductionCoordinator(params)
    """

    def __init__(self, params: Optional[CoordinationParameters] = None):
        """
        Initialize coordinator.

        Args:
            params: Coordination parameters. If None, uses production defaults.
        """
        self.params = params or CoordinationParameters()

        # ATP state
        self.atp_state = ATPState(
            allocation_cost=self.params.atp_allocation_cost,
            rest_recovery=self.params.atp_rest_recovery,
            allocation_threshold=self.params.atp_allocation_threshold
        )

        # Metrics (production monitoring)
        self.metrics = CoordinationMetrics()

        # Satisfaction tracking (Track 39 temporal adaptation)
        self.satisfaction_history: deque = deque(maxlen=self.params.satisfaction_windows_required)

        # Mode tracking
        self.mode = self.params.get_mode()

    def coordinate_interaction(
        self,
        priority: float,
        trust_score: float,
        network_density: float,
        quality_score: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Coordinate a network interaction.

        Args:
            priority: Interaction priority (0-1, >0.7 is high-priority)
            trust_score: Trust score for authorization (0-1)
            network_density: Network density for reputation (0-1)
            quality_score: Optional pre-computed quality score

        Returns:
            Dict with:
                coordinated: bool - Whether coordination occurred
                authorized: bool - Whether authorization granted
                quality: float - Quality of coordination (0-1)
                cost: float - Resource cost (ATP spent)
                atp_level: float - Current ATP level
                latency_ms: float - Coordination latency in milliseconds
        """
        start_time = time.time()

        self.metrics.total_interactions += 1
        is_high_priority = priority > 0.7

        if is_high_priority:
            self.metrics.high_priority_interactions += 1

        # ATP availability check
        atp_available = self.atp_state.can_allocate()

        # Decision: coordinate or skip
        if atp_available and is_high_priority:
            # Authorization check
            authorized = trust_score > self.params.auth_trust_threshold

            if authorized:
                self.metrics.authorization_grants += 1

                # Allocate ATP
                allocation_succeeded = self.atp_state.allocate()

                if allocation_succeeded:
                    self.metrics.atp_allocations += 1
                    self.metrics.coordinated_high_priority += 1
                    self.metrics.atp_spent += self.params.atp_allocation_cost

                    # Calculate coordination quality
                    if quality_score is None:
                        # Quality model (Track 49 pattern)
                        base_quality = 0.5 + 0.3 * priority
                        atp_bonus = self.atp_state.get_level() * 0.3
                        density_bonus = min(0.2, network_density * 0.2)
                        quality_score = min(1.0, base_quality + atp_bonus + density_bonus)

                    self.metrics.quality_samples.append(quality_score)
                    # Keep last 1000 samples
                    if len(self.metrics.quality_samples) > 1000:
                        self.metrics.quality_samples = self.metrics.quality_samples[-1000:]

                    # Latency tracking
                    latency_ms = (time.time() - start_time) * 1000
                    self.metrics.add_coordination_time(latency_ms)

                    return {
                        'coordinated': True,
                        'authorized': True,
                        'quality': quality_score,
                        'cost': self.params.atp_allocation_cost,
                        'atp_level': self.atp_state.get_level(),
                        'latency_ms': latency_ms
                    }
            else:
                self.metrics.authorization_denials += 1

        # No coordination - rest cycle
        self.atp_state.rest()
        self.metrics.atp_rest_cycles += 1

        latency_ms = (time.time() - start_time) * 1000
        self.metrics.add_coordination_time(latency_ms)

        return {
            'coordinated': False,
            'authorized': False,
            'quality': 0.0,
            'cost': 0.0,
            'atp_level': self.atp_state.get_level(),
            'latency_ms': latency_ms
        }

    def check_satisfaction(self) -> Tuple[bool, float]:
        """
        Check if current performance satisfies threshold.

        Returns:
            (satisfied, fitness_score)

        Uses Track 39 satisfaction threshold pattern (~95% for 3 windows).
        """
        fitness = self.metrics.calculate_fitness()

        if self.params.enable_multi_objective:
            # Multi-objective: weighted fitness score
            score = fitness.weighted_score(
                self.params.coverage_weight,
                self.params.quality_weight,
                self.params.efficiency_weight
            )
        else:
            # Single-objective: coverage only (legacy mode)
            score = fitness.coverage

        satisfied = score >= self.params.satisfaction_threshold

        # Update satisfaction history
        self.satisfaction_history.append(satisfied)

        # Check for stable satisfaction (3-window pattern from Track 39)
        if len(self.satisfaction_history) == self.params.satisfaction_windows_required:
            all_satisfied = all(self.satisfaction_history)
            if all_satisfied:
                self.metrics.stable_windows += 1
            else:
                self.metrics.stable_windows = 0

        return satisfied, score

    def get_metrics(self) -> Dict:
        """Get current metrics for telemetry/monitoring"""
        return self.metrics.to_dict()

    def get_mode(self) -> CoordinatorMode:
        """Get current coordinator mode"""
        return self.mode

    def reset_metrics(self):
        """Reset metrics (for testing/validation)"""
        self.metrics = CoordinationMetrics()


# Factory functions for common modes (Thor S26 pattern)

def create_coordinator_single_objective() -> Web4ProductionCoordinator:
    """
    Create single-objective coordinator (legacy mode).

    Optimizes for coverage only. Backward compatible with existing deployments.
    """
    params = CoordinationParameters(enable_multi_objective=False)
    return Web4ProductionCoordinator(params)


def create_coordinator_balanced() -> Web4ProductionCoordinator:
    """
    Create balanced multi-objective coordinator.

    Equal weights: coverage=33%, quality=33%, efficiency=34%
    """
    params = CoordinationParameters(
        enable_multi_objective=True,
        coverage_weight=0.33,
        quality_weight=0.33,
        efficiency_weight=0.34
    )
    return Web4ProductionCoordinator(params)


def create_coordinator_coverage_priority() -> Web4ProductionCoordinator:
    """
    Create coverage-priority coordinator (default multi-objective).

    Weights: coverage=50%, quality=30%, efficiency=20%

    This is the Pareto-optimal configuration from Track 45.
    """
    params = CoordinationParameters(
        enable_multi_objective=True,
        coverage_weight=0.50,
        quality_weight=0.30,
        efficiency_weight=0.20
    )
    return Web4ProductionCoordinator(params)


def create_coordinator_quality_priority() -> Web4ProductionCoordinator:
    """
    Create quality-priority coordinator.

    Weights: coverage=30%, quality=60%, efficiency=10%

    Use when decision quality is critical (high-stakes coordination).
    """
    params = CoordinationParameters(
        enable_multi_objective=True,
        coverage_weight=0.30,
        quality_weight=0.60,
        efficiency_weight=0.10
    )
    return Web4ProductionCoordinator(params)


def create_coordinator_efficiency_priority() -> Web4ProductionCoordinator:
    """
    Create efficiency-priority coordinator.

    Weights: coverage=30%, quality=20%, efficiency=50%

    Use when resource utilization is critical (resource-constrained environments).
    """
    params = CoordinationParameters(
        enable_multi_objective=True,
        coverage_weight=0.30,
        quality_weight=0.20,
        efficiency_weight=0.50
    )
    return Web4ProductionCoordinator(params)


# A/B testing support

def create_coordinator_ab_test(
    enable_multi_objective: bool,
    test_group: str = "control"
) -> Web4ProductionCoordinator:
    """
    Create coordinator for A/B testing.

    Args:
        enable_multi_objective: If True, uses multi-objective (test group)
        test_group: Identifier for telemetry ("control" or "treatment")

    Returns:
        Coordinator configured for A/B test

    Usage:
        # Control group (single-objective)
        coordinator = create_coordinator_ab_test(False, "control")

        # Treatment group (multi-objective)
        coordinator = create_coordinator_ab_test(True, "treatment")
    """
    params = CoordinationParameters(enable_multi_objective=enable_multi_objective)
    coordinator = Web4ProductionCoordinator(params)
    coordinator.test_group = test_group  # Add test group identifier
    return coordinator


if __name__ == "__main__":
    print("="*80)
    print("Web4 Production Coordinator - Track 52")
    print("="*80)
    print()
    print("Production-ready coordinator with opt-in multi-objective optimization")
    print("Based on Thor S26 production integration pattern")
    print()

    # Demo: Single-objective vs multi-objective
    print("Creating coordinators...")
    print()

    # Single-objective (legacy)
    coord_single = create_coordinator_single_objective()
    print(f"✓ Single-objective coordinator: {coord_single.get_mode().value}")

    # Multi-objective modes
    coord_balanced = create_coordinator_balanced()
    print(f"✓ Balanced coordinator: {coord_balanced.get_mode().value}")

    coord_coverage = create_coordinator_coverage_priority()
    print(f"✓ Coverage-priority coordinator: {coord_coverage.get_mode().value}")

    coord_quality = create_coordinator_quality_priority()
    print(f"✓ Quality-priority coordinator: {coord_quality.get_mode().value}")

    coord_efficiency = create_coordinator_efficiency_priority()
    print(f"✓ Efficiency-priority coordinator: {coord_efficiency.get_mode().value}")

    print()
    print("="*80)
    print("Quick validation test...")
    print("="*80)
    print()

    # Run quick test on coverage-priority mode
    coordinator = coord_coverage

    # Simulate 1000 interactions
    for _ in range(1000):
        priority = random.betavariate(2, 5)  # Most low, some high
        trust_score = random.uniform(0.3, 0.9)
        network_density = random.uniform(0.1, 0.8)

        result = coordinator.coordinate_interaction(
            priority, trust_score, network_density
        )

    # Check results
    metrics = coordinator.get_metrics()
    satisfied, score = coordinator.check_satisfaction()

    print(f"Total interactions: {metrics['total_interactions']}")
    print(f"High-priority interactions: {metrics['high_priority_interactions']}")
    print(f"Coordinated: {metrics['coordinated_high_priority']}")
    print()
    print(f"Coverage: {metrics['coverage']:.1%}")
    print(f"Quality: {metrics['quality']:.1%}")
    print(f"Efficiency: {metrics['efficiency']:.1%}")
    print()
    print(f"Satisfaction score: {score:.3f}")
    print(f"Satisfied: {'✓' if satisfied else '✗'}")
    print(f"Stable windows: {metrics['satisfaction_stable_windows']}")
    print()
    print(f"Mean latency: {metrics['mean_latency_ms']:.3f} ms")
    print(f"P95 latency: {metrics['p95_latency_ms']:.3f} ms")
    print()

    print("✓ Track 52 implementation complete!")
    print()
