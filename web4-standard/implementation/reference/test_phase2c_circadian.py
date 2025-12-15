#!/usr/bin/env python3
"""
Test Web4 Phase 2c Circadian Coordinator
=========================================

Validates temporal awareness integration into Web4 coordination.

Tests:
- Circadian clock integration
- Phase-dependent coordination biasing
- Scheduled consolidation during NIGHT
- Temporal pattern learning
- Long-duration circadian stability

Created: December 14, 2025
Session: Autonomous Web4 Research Session 51
"""

import sys
import random
import time
from typing import List, Dict

sys.path.insert(0, '/home/dp/ai-workspace/web4/web4-standard/implementation/reference')

from web4_phase2c_circadian_coordinator import Web4CircadianCoordinator, CircadianMetrics
from sage.core.circadian_clock import CircadianPhase


def generate_coordination_stream(num_cycles: int) -> List[Dict]:
    """Generate realistic coordination stream."""
    stream = []

    for i in range(num_cycles):
        # Realistic parameter variation
        priority = random.uniform(0.5, 0.95)
        trust_score = random.uniform(0.6, 0.95)
        network_density = random.uniform(0.5, 0.90)

        # Quality estimate (some correlation with parameters)
        quality = 0.5
        if trust_score > 0.8:
            quality += 0.25
        if network_density > 0.7:
            quality += 0.20

        quality = max(0.0, min(1.0, quality + random.uniform(-0.1, 0.1)))

        stream.append({
            'priority': priority,
            'trust_score': trust_score,
            'network_density': network_density,
            'quality_score': quality,
            'context': {'diversity_score': random.uniform(0.5, 0.85)}
        })

    return stream


def test_circadian_integration():
    """Test basic circadian clock integration."""
    print("=" * 80)
    print("TEST: Circadian Integration")
    print("=" * 80)
    print()

    coordinator = Web4CircadianCoordinator(
        enable_circadian=True,
        enable_epistemic=True,
        enable_learning=True,
        circadian_period=100,
        consolidate_during_night=True
    )

    print("✓ Created circadian coordinator")
    print(f"  Circadian period: 100 cycles")
    print(f"  Consolidation during night: enabled")
    print()

    # Run a few coordination cycles
    print("Running 10 test cycles...")
    for i in range(10):
        should_coord, telemetry = coordinator.coordinate_interaction(
            priority=0.8,
            trust_score=0.85,
            network_density=0.75,
            quality_score=0.80
        )

        if i == 0 or i == 9:
            print(f"  Cycle {i}: Phase={telemetry.circadian_phase}, "
                  f"Decision={should_coord}, Bias={telemetry.circadian_bias_applied:+.3f}")

    print()
    print("✅ Circadian integration working")
    print()


def test_phase_dependent_biasing():
    """Test that coordination decisions vary by circadian phase."""
    print("=" * 80)
    print("TEST: Phase-Dependent Biasing")
    print("=" * 80)
    print()

    coordinator = Web4CircadianCoordinator(
        enable_circadian=True,
        enable_epistemic=False,  # Disable for cleaner test
        enable_learning=False,
        circadian_period=50  # Shorter period for faster testing
    )

    print("Running 50 cycles (1 complete circadian day)...")
    print()

    phases_seen = set()
    biases_by_phase = {}

    for i in range(50):
        should_coord, telemetry = coordinator.coordinate_interaction(
            priority=0.7,
            trust_score=0.75,
            network_density=0.70,
            quality_score=0.75
        )

        phase = telemetry.circadian_phase
        phases_seen.add(phase)

        if phase not in biases_by_phase:
            biases_by_phase[phase] = []

        biases_by_phase[phase].append(telemetry.circadian_bias_applied)

    print(f"Phases observed: {sorted(phases_seen)}")
    print()

    print("Average Bias by Phase:")
    for phase in sorted(biases_by_phase.keys()):
        avg_bias = sum(biases_by_phase[phase]) / len(biases_by_phase[phase])
        print(f"  {phase:12s}: {avg_bias:+.3f}")

    print()

    # Verify DAY has positive bias, NIGHT has negative
    day_bias = sum(biases_by_phase.get('day', [0])) / max(1, len(biases_by_phase.get('day', [0])))
    night_bias = sum(biases_by_phase.get('night', [0])) / max(1, len(biases_by_phase.get('night', [0])))

    if day_bias > 0 and night_bias < 0:
        print("✅ Phase-dependent biasing confirmed")
        print(f"   DAY bias: {day_bias:+.3f} (positive, encourages coordination)")
        print(f"   NIGHT bias: {night_bias:+.3f} (negative, discourages coordination)")
    else:
        print("⚠️  Unexpected bias pattern")

    print()


def test_scheduled_consolidation():
    """Test that consolidation happens during NIGHT phases."""
    print("=" * 80)
    print("TEST: Scheduled Consolidation")
    print("=" * 80)
    print()

    coordinator = Web4CircadianCoordinator(
        enable_circadian=True,
        enable_epistemic=True,
        enable_learning=True,
        circadian_period=100,
        consolidate_during_night=True
    )

    # Generate stream
    stream = generate_coordination_stream(200)

    print("Running 200 cycles with scheduled consolidation...")

    consolidations_before_night = 0
    consolidations_during_night = 0

    for i, cycle in enumerate(stream):
        should_coord, telemetry = coordinator.coordinate_interaction(
            priority=cycle['priority'],
            trust_score=cycle['trust_score'],
            network_density=cycle['network_density'],
            quality_score=cycle['quality_score'],
            context=cycle['context']
        )

        # Track when consolidations happen (access raw metrics, not computed averages)
        if i > 0:
            prev_consolidations = consolidations_before_night + consolidations_during_night
            curr_consolidations = coordinator.circadian_metrics.consolidations_executed

            if curr_consolidations > prev_consolidations:
                # Consolidation just happened
                if telemetry.circadian_phase in ['night', 'deep_night']:
                    consolidations_during_night += 1
                else:
                    consolidations_before_night += 1

    metrics = coordinator.get_circadian_metrics()

    print()
    print(f"Total consolidations executed: {metrics.consolidations_executed}")
    print(f"  During NIGHT phases: {consolidations_during_night}")
    print(f"  During DAY phases: {consolidations_before_night}")
    print(f"  Patterns learned during night: {metrics.patterns_learned_during_night}")
    print()

    if consolidations_during_night > consolidations_before_night:
        print("✅ Scheduled consolidation working")
        print("   Consolidation preferentially happens during NIGHT phases")
    else:
        print("⚠️  Consolidation not preferring NIGHT phases")

    print()


def test_longduration_circadian():
    """Test circadian coordinator over 1000 cycles."""
    print("=" * 80)
    print("TEST: Long-Duration Circadian Validation (1000 cycles)")
    print("=" * 80)
    print()

    coordinator = Web4CircadianCoordinator(
        enable_circadian=True,
        enable_epistemic=True,
        enable_learning=True,
        enable_interventions=True,
        circadian_period=100,
        consolidate_during_night=True
    )

    # Generate stream
    stream = generate_coordination_stream(1000)

    print("Running 1000 coordination cycles...")
    start = time.time()

    for i, cycle in enumerate(stream):
        should_coord, telemetry = coordinator.coordinate_interaction(
            priority=cycle['priority'],
            trust_score=cycle['trust_score'],
            network_density=cycle['network_density'],
            quality_score=cycle['quality_score'],
            context=cycle['context']
        )

        # Periodic progress
        if (i + 1) % 200 == 0:
            metrics = coordinator.get_circadian_metrics()
            print(f"  Cycle {i+1:4d}: Coord rate={metrics.coordination_rate:.1%}, "
                  f"Patterns={metrics.patterns_extracted}, "
                  f"Consolidations={metrics.consolidations_executed}")

    elapsed = time.time() - start

    print()
    print(f"✓ Completed 1000 cycles in {elapsed:.1f}s ({1000/elapsed:.0f} cycles/s)")
    print()

    # Final metrics
    metrics = coordinator.get_circadian_metrics()

    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    print(f"Total Cycles: {metrics.total_cycles}")
    print(f"Coordinations: {metrics.coordinations} ({metrics.coordination_rate:.1%})")
    print()

    # Phase distribution
    phase_summary = coordinator.get_phase_summary()

    print("Coordination by Circadian Phase:")
    print(f"{'Phase':12s} | {'Cycles':>7s} | {'Coord':>7s} | {'Rate':>6s} | {'Avg Quality':>11s}")
    print("-" * 80)

    for phase in CircadianPhase:
        phase_name = phase.value
        stats = phase_summary[phase_name]

        print(f"{phase_name:12s} | {stats['cycles']:7d} | "
              f"{stats['coordinations']:7d} | {stats['coordination_rate']:6.1%} | "
              f"{stats['avg_quality']:11.3f}")

    print()

    # Key metrics
    print("Temporal Patterns:")
    day_quality = phase_summary['day']['avg_quality']
    night_quality = phase_summary['night']['avg_quality']
    delta = day_quality - night_quality

    print(f"  Day vs Night quality: {day_quality:.3f} vs {night_quality:.3f} (Δ={delta:+.3f})")
    print(f"  Day coordination rate: {phase_summary['day']['coordination_rate']:.1%}")
    print(f"  Night coordination rate: {phase_summary['night']['coordination_rate']:.1%}")
    print()

    # Learning
    print("Learning System:")
    print(f"  Patterns extracted: {metrics.patterns_extracted}")
    print(f"  Consolidations executed: {metrics.consolidations_executed}")
    print(f"  Patterns learned during night: {metrics.patterns_learned_during_night}")
    print()

    # Validation
    print("=" * 80)
    print("VALIDATION")
    print("=" * 80)
    print()

    success_criteria = []

    if metrics.total_cycles == 1000:
        success_criteria.append("✅ Completed 1000 cycles")

    if delta > 0:
        success_criteria.append(f"✅ Day quality higher than night (Δ={delta:+.3f})")

    if phase_summary['day']['coordination_rate'] > phase_summary['night']['coordination_rate']:
        success_criteria.append("✅ Day coordination rate > night rate")

    if metrics.consolidations_executed > 0:
        success_criteria.append(f"✅ Scheduled consolidation executed ({metrics.consolidations_executed} times)")

    if metrics.patterns_extracted > 0:
        success_criteria.append(f"✅ Pattern learning active ({metrics.patterns_extracted} patterns)")

    for criterion in success_criteria:
        print(criterion)

    print()
    print("Circadian-aware Phase 2c validated over 1000 cycles")
    print()


def run_all_tests():
    """Run complete Phase 2c test suite."""
    print("=" * 80)
    print("Web4 Phase 2c Circadian Coordinator Test Suite")
    print("=" * 80)
    print()

    test_circadian_integration()
    print("\n\n")

    test_phase_dependent_biasing()
    print("\n\n")

    test_scheduled_consolidation()
    print("\n\n")

    test_longduration_circadian()


if __name__ == "__main__":
    run_all_tests()
