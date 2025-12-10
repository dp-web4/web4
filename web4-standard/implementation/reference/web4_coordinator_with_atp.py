#!/usr/bin/env python3
"""
Web4 Multi-Objective Coordinator with Full ATP Integration

Session 11 - Track 49: Fix ATP integration gap from Track 48

Integrates Track 47's multi-objective coordinator with Track 39's full ATP dynamics.

Root cause from Track 48:
  Track 47's coordinate_interaction() used placeholder: atp_available = True
  This prevented actual coordination (0% coverage/quality/efficiency)

Solution:
  Add proper ATP simulation with:
  - ATP level tracking (0-1)
  - Attention cost depletion
  - Rest recovery over time
  - Allocation threshold enforcement

Cross-validates:
- Track 39: Web4 temporal adaptation with ATP dynamics
- Track 47: Multi-objective production integration
- Thor S25: Multi-objective workload testing (3x efficiency gain)

Research Provenance:
- Legion S10 Track 39: Web4 temporal adaptation (1,070 LOC)
- Legion S10 Track 47: Multi-objective production (577 LOC)
- Legion S10 Track 48: Long-duration validation with discovered issue (474 LOC)
- Legion S11 Track 49: ATP integration fix (this module)
- Thor S25: Multi-objective workload testing (471 LOC)
"""

import random
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
from collections import deque

from web4_multi_objective_production import (
    NetworkWindow,
    Web4CoordinationParameters,
    AdaptationTrigger,
    create_multi_objective_coordinator
)


@dataclass
class ATPState:
    """ATP (Attention/Time/Processing) resource state"""
    current_level: float = 1.0  # 0-1
    max_level: float = 1.0
    min_level: float = 0.0

    # Dynamics parameters (from coordinator params)
    allocation_cost: float = 0.005
    rest_recovery: float = 0.080
    allocation_threshold: float = 0.20

    def can_allocate(self) -> bool:
        """Check if ATP is above threshold for allocation"""
        return self.current_level >= self.allocation_threshold

    def allocate(self) -> bool:
        """
        Attempt to allocate ATP for coordination.
        Returns True if allocation succeeded, False otherwise.
        """
        if not self.can_allocate():
            return False

        self.current_level = max(self.min_level, self.current_level - self.allocation_cost)
        return True

    def rest(self):
        """Recover ATP during rest"""
        self.current_level = min(self.max_level, self.current_level + self.rest_recovery)

    def get_level(self) -> float:
        """Get current ATP level"""
        return self.current_level


class Web4CoordinatorWithATP:
    """
    Production Web4 coordinator with full ATP dynamics integration.

    Fixes Track 48's integration issue by replacing placeholder ATP logic
    with proper ATP simulation from Track 39.
    """

    def __init__(self, params: Optional[Web4CoordinationParameters] = None):
        self.params = params or Web4CoordinationParameters()

        # Network metrics window
        self.current_window = NetworkWindow(window_size=1000)
        self.previous_window = NetworkWindow(window_size=1000)

        # ATP state (NEW: Track 49)
        self.atp_state = ATPState(
            allocation_cost=self.params.atp_allocation_cost,
            rest_recovery=self.params.atp_rest_recovery,
            allocation_threshold=self.params.atp_allocation_threshold
        )

        # Satisfaction tracking
        self.satisfaction_stable_windows = 0

        # Adaptation state
        self.cycles_since_adaptation = 0
        self.total_adaptations = 0
        self.total_coordinations = 0
        self.total_rest_cycles = 0

    def coordinate_interaction(
        self,
        priority: float,
        trust_score: float,
        network_density: float,
        quality_score: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Coordinate a network interaction with full ATP dynamics.

        This replaces Track 47's placeholder logic with actual ATP simulation.

        Args:
            priority: Interaction priority (0-1)
            trust_score: Trust score for authorization (0-1)
            network_density: Network density for reputation (0-1)
            quality_score: Optional quality score for multi-objective tracking

        Returns:
            coordinated: Whether coordination occurred
            authorized: Whether authorization granted
            quality: Quality of coordination
            cost: Resource cost
            atp_level: Current ATP level after interaction
        """
        is_high_priority = priority > 0.7

        # ATP availability check (FIXED: Track 49)
        atp_available = self.atp_state.can_allocate()

        # Decision: coordinate or skip
        if atp_available and is_high_priority:
            # Authorization check
            authorized = trust_score > self.params.auth_trust_threshold

            if authorized:
                # Allocate ATP (FIXED: Track 49)
                allocation_succeeded = self.atp_state.allocate()

                if allocation_succeeded:
                    self.total_coordinations += 1

                    # Calculate coordination quality
                    if quality_score is None and self.params.enable_multi_objective:
                        # Simulate quality based on ATP level, network density, and priority
                        base_quality = 0.5 + 0.3 * priority
                        atp_bonus = self.atp_state.get_level() * 0.3  # Higher ATP → better quality
                        density_bonus = min(0.2, network_density * 0.2)
                        quality_score = min(1.0, base_quality + atp_bonus + density_bonus)

                    # Track interaction
                    self.current_window.add_interaction(
                        coordination_succeeded=True,
                        authorization_correct=True,
                        quality_score=quality_score,
                        coordination_cost=self.params.atp_allocation_cost
                    )

                    return {
                        'coordinated': True,
                        'authorized': True,
                        'quality': quality_score or 0.0,
                        'cost': self.params.atp_allocation_cost,
                        'atp_level': self.atp_state.get_level()
                    }

        # No coordination - rest cycle (FIXED: Track 49)
        self.atp_state.rest()
        self.total_rest_cycles += 1

        self.current_window.add_interaction(
            coordination_succeeded=False,
            authorization_correct=False,
            quality_score=None,
            coordination_cost=0.0
        )

        return {
            'coordinated': False,
            'authorized': False,
            'quality': 0.0,
            'cost': 0.0,
            'atp_level': self.atp_state.get_level()
        }

    def check_adaptation_needed(self) -> Tuple[AdaptationTrigger, str]:
        """
        Check if parameter adaptation is needed.

        Uses satisfaction threshold from Track 39 + multi-objective from Track 47.
        """
        metrics = self.current_window.get_metrics(
            coverage_weight=self.params.coverage_weight,
            quality_weight=self.params.quality_weight,
            efficiency_weight=self.params.efficiency_weight
        )

        # Multi-objective satisfaction check (Track 47)
        if self.params.enable_multi_objective:
            # Check weighted fitness
            if metrics['weighted_fitness'] >= self.params.satisfaction_threshold:
                self.satisfaction_stable_windows += 1
                if self.satisfaction_stable_windows >= self.params.satisfaction_windows_required:
                    return (AdaptationTrigger.NONE,
                           f"multi_objective satisfied (fitness {metrics['weighted_fitness']:.3f})")
            else:
                self.satisfaction_stable_windows = 0

                # Identify which objective is failing
                if metrics['coverage'] < 0.90:
                    return (AdaptationTrigger.COVERAGE_DROP,
                           f"coverage {metrics['coverage']:.1%}")
                elif metrics['quality'] < 0.80:
                    return (AdaptationTrigger.QUALITY_DROP,
                           f"quality {metrics['quality']:.1%}")
                elif metrics['efficiency'] < 0.50:
                    return (AdaptationTrigger.EFFICIENCY_DROP,
                           f"efficiency {metrics['efficiency']:.1%}")
                else:
                    return (AdaptationTrigger.MULTI_OBJECTIVE_DROP,
                           f"weighted fitness {metrics['weighted_fitness']:.3f}")

        else:
            # Single-objective satisfaction check (backward compatible)
            if metrics['coverage'] >= self.params.satisfaction_threshold:
                self.satisfaction_stable_windows += 1
                if self.satisfaction_stable_windows >= self.params.satisfaction_windows_required:
                    return (AdaptationTrigger.NONE,
                           f"coverage satisfied ({metrics['coverage']:.1%})")
            else:
                self.satisfaction_stable_windows = 0
                return (AdaptationTrigger.COVERAGE_DROP,
                       f"coverage {metrics['coverage']:.1%}")

        return (AdaptationTrigger.NONE, "monitoring")

    def get_current_metrics(self) -> Dict[str, float]:
        """Get current performance metrics"""
        metrics = self.current_window.get_metrics(
            coverage_weight=self.params.coverage_weight,
            quality_weight=self.params.quality_weight,
            efficiency_weight=self.params.efficiency_weight
        )

        # Add ATP state
        metrics['atp_level'] = self.atp_state.get_level()

        return metrics

    def get_statistics(self) -> Dict[str, any]:
        """Get operational statistics"""
        total_cycles = self.total_coordinations + self.total_rest_cycles

        return {
            'total_cycles': total_cycles,
            'total_coordinations': self.total_coordinations,
            'total_rest_cycles': self.total_rest_cycles,
            'coordination_rate': self.total_coordinations / total_cycles if total_cycles > 0 else 0.0,
            'total_adaptations': self.total_adaptations,
            'satisfaction_stable_windows': self.satisfaction_stable_windows
        }


# Factory function (updated for Track 49)

def create_multi_objective_coordinator_with_atp(**kwargs) -> Web4CoordinatorWithATP:
    """
    Create multi-objective Web4 coordinator with full ATP dynamics.

    Based on:
    - Track 45 Pareto-optimal config (cost=0.005, recovery=0.080)
    - Track 47 multi-objective framework
    - Track 49 ATP integration fix
    - Thor S25 validation (3x efficiency gain)
    """
    defaults = {
        'atp_allocation_cost': 0.005,     # Pareto-optimal
        'atp_rest_recovery': 0.080,       # Pareto-optimal
        'atp_allocation_threshold': 0.20,
        'enable_multi_objective': True,
        'coverage_weight': 0.5,
        'quality_weight': 0.3,
        'efficiency_weight': 0.2
    }
    defaults.update(kwargs)
    params = Web4CoordinationParameters(**defaults)
    return Web4CoordinatorWithATP(params)


# Validation demonstration

def validate_atp_integration():
    """Validate that ATP integration works correctly (fixes Track 48 issue)"""
    print("="*80)
    print("ATP INTEGRATION VALIDATION")
    print("="*80)
    print()
    print("Fixes Track 48 issue where placeholder ATP prevented coordination")
    print()

    coordinator = create_multi_objective_coordinator_with_atp()

    print("Configuration:")
    print(f"  Cost: {coordinator.params.atp_allocation_cost:.3f}")
    print(f"  Recovery: {coordinator.params.atp_rest_recovery:.3f}")
    print(f"  Threshold: {coordinator.params.atp_allocation_threshold:.3f}")
    print(f"  Multi-objective: {coordinator.params.enable_multi_objective}")
    print()

    print("Running 1000 interactions with ATP dynamics...")
    print()

    # Track ATP levels over time
    atp_history = []

    for i in range(1000):
        # Varying priority
        priority = 0.5 + 0.5 * (i % 100) / 100

        result = coordinator.coordinate_interaction(
            priority=priority,
            trust_score=0.7,
            network_density=0.5,
            quality_score=None  # Let coordinator simulate
        )

        atp_history.append(result['atp_level'])

        # Show first few cycles
        if i < 5:
            print(f"  Cycle {i}: Coordinated={result['coordinated']}, "
                  f"ATP={result['atp_level']:.3f}, Quality={result['quality']:.3f}")

    print()
    print("✓ Completed 1000 interactions")
    print()

    # Get final metrics
    metrics = coordinator.get_current_metrics()
    stats = coordinator.get_statistics()

    print("Performance Metrics:")
    print(f"  Coverage: {metrics['coverage']:.1%}")
    print(f"  Quality: {metrics['quality']:.1%}")
    print(f"  Efficiency: {metrics['efficiency']:.1%}")
    print(f"  Weighted Fitness: {metrics['weighted_fitness']:.3f}")
    print(f"  ATP Level: {metrics['atp_level']:.3f}")
    print()

    print("Operational Statistics:")
    print(f"  Total cycles: {stats['total_cycles']}")
    print(f"  Coordinations: {stats['total_coordinations']}")
    print(f"  Rest cycles: {stats['total_rest_cycles']}")
    print(f"  Coordination rate: {stats['coordination_rate']:.1%}")
    print()

    # Validate results
    print("Validation Results:")

    if metrics['coverage'] > 0:
        print(f"  ✅ Coverage > 0% ({metrics['coverage']:.1%}) - ATP integration working")
    else:
        print(f"  ❌ Coverage = 0% - ATP integration FAILED")

    if metrics['quality'] > 0:
        print(f"  ✅ Quality > 0% ({metrics['quality']:.1%}) - Quality tracking working")
    else:
        print(f"  ❌ Quality = 0% - Quality tracking FAILED")

    if metrics['efficiency'] > 0:
        print(f"  ✅ Efficiency > 0% ({metrics['efficiency']:.1%}) - Efficiency tracking working")
    else:
        print(f"  ❌ Efficiency = 0% - Efficiency tracking FAILED")

    if stats['total_coordinations'] > 0:
        print(f"  ✅ Coordinations occurred ({stats['total_coordinations']}) - ATP dynamics working")
    else:
        print(f"  ❌ No coordinations - ATP dynamics FAILED")

    print()

    # Compare to Track 48 results (all zeros)
    print("Comparison to Track 48 (broken):")
    print(f"  Track 48 Coverage: 0.0%  →  Track 49: {metrics['coverage']:.1%}")
    print(f"  Track 48 Quality: 0.0%   →  Track 49: {metrics['quality']:.1%}")
    print(f"  Track 48 Efficiency: 0.0% →  Track 49: {metrics['efficiency']:.1%}")
    print()

    if metrics['coverage'] > 0 and metrics['quality'] > 0 and metrics['efficiency'] > 0:
        print("="*80)
        print("✅ ATP INTEGRATION VALIDATED - Track 48 issue FIXED")
        print("="*80)
        return True
    else:
        print("="*80)
        print("❌ ATP INTEGRATION FAILED - Track 48 issue persists")
        print("="*80)
        return False


if __name__ == "__main__":
    success = validate_atp_integration()

    if success:
        print()
        print("Next steps:")
        print("  1. Re-run Track 48 long-duration validation with this coordinator")
        print("  2. Validate predictions S2, M1, M3 with working ATP dynamics")
        print("  3. Compare with Thor S25 multi-objective workload results")
        print()
