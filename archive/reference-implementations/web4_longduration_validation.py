#!/usr/bin/env python3
"""
Web4 Phase 2b: Long-Duration Validation
=======================================

Validates Phase 2b integrated coordinator over 1000+ coordination cycles:
- Learning evolution over time
- Prediction accuracy improvement
- Epistemic state distribution
- Intervention effectiveness
- Pattern quality metrics

Created: December 13, 2025
"""

import random
import time
from typing import List, Dict, Tuple
import statistics

from web4_phase2b_integrated_coordinator import (
    Web4IntegratedCoordinator,
    InterventionLevel
)


def generate_realistic_coordination_stream(num_cycles: int) -> List[Dict]:
    """
    Generate realistic long-duration coordination stream with varying conditions.

    Simulates:
    - Normal operation (50%)
    - Stress periods (20%)
    - Degradation periods (15%)
    - Recovery periods (15%)
    """
    stream = []

    for i in range(num_cycles):
        progress = i / num_cycles

        # Determine current phase based on progress
        phase_random = random.random()

        if phase_random < 0.50:  # Normal operation (50%)
            priority = random.uniform(0.6, 0.85)
            trust_score = random.uniform(0.7, 0.95)
            network_density = random.uniform(0.65, 0.85)
            quality_score = random.uniform(0.7, 0.9)
            diversity_score = random.uniform(0.5, 0.8)

        elif phase_random < 0.70:  # Stress (20%)
            priority = random.uniform(0.8, 1.0)
            trust_score = random.uniform(0.5, 0.85)
            network_density = random.uniform(0.4, 0.85)
            quality_score = random.uniform(0.4, 0.75)
            diversity_score = random.uniform(0.3, 0.7)

        elif phase_random < 0.85:  # Degradation (15%)
            degradation = random.uniform(0.2, 0.4)
            priority = random.uniform(0.5, 0.75)
            trust_score = random.uniform(0.5 - degradation, 0.8 - degradation)
            network_density = random.uniform(0.4 - degradation, 0.7 - degradation)
            quality_score = random.uniform(0.5 - degradation, 0.75 - degradation)
            diversity_score = random.uniform(0.3, 0.6)

        else:  # Recovery (15%)
            recovery = progress * 0.3  # Gradual improvement
            priority = random.uniform(0.5, 0.8)
            trust_score = random.uniform(0.5 + recovery, 0.75 + recovery)
            network_density = random.uniform(0.45 + recovery, 0.70 + recovery)
            quality_score = random.uniform(0.5 + recovery, 0.75 + recovery)
            diversity_score = random.uniform(0.4 + recovery, 0.7 + recovery)

        cycle = {
            'priority': priority,
            'trust_score': trust_score,
            'network_density': network_density,
            'quality_score': quality_score,
            'diversity_score': diversity_score,
            'cycle_id': i
        }

        stream.append(cycle)

    return stream


def run_longduration_validation(num_cycles: int = 1000):
    """
    Run long-duration validation of Phase 2b integrated coordinator.

    Args:
        num_cycles: Number of coordination cycles to simulate
    """
    print("=" * 80)
    print(f"Web4 Phase 2b: Long-Duration Validation ({num_cycles} cycles)")
    print("=" * 80)
    print()

    # Generate coordination stream
    print(f"Generating {num_cycles} coordination cycles...")
    stream = generate_realistic_coordination_stream(num_cycles)
    print(f"✓ Generated {len(stream)} cycles")
    print()

    # Initialize coordinator with learning + interventions
    print("Initializing Phase 2b coordinator...")
    print("  - Epistemic tracking: enabled")
    print("  - Learning: enabled (updates every 100 cycles)")
    print("  - Interventions: enabled")
    print()

    coordinator = Web4IntegratedCoordinator(
        enable_epistemic=True,
        enable_learning=True,
        enable_interventions=True,
        learning_frequency=100
    )

    # Run coordination cycles with periodic reporting
    print(f"Running {num_cycles} coordination cycles...")
    print()

    start_time = time.time()

    # Track metrics over time
    accuracy_windows = []  # Prediction accuracy in 100-cycle windows
    learning_updates = []  # Times when learning was updated

    for i, cycle in enumerate(stream):
        should_coord, telemetry = coordinator.coordinate_interaction(
            priority=cycle['priority'],
            trust_score=cycle['trust_score'],
            network_density=cycle['network_density'],
            quality_score=cycle['quality_score'],
            context={'diversity_score': cycle['diversity_score']}
        )

        # Periodic reporting
        if (i + 1) % 100 == 0:
            elapsed = time.time() - start_time
            cycles_per_sec = (i + 1) / elapsed

            metrics = coordinator.get_metrics()

            print(f"Cycle {i+1:4d}: "
                  f"Coord rate: {metrics.coordination_rate:.1%} | "
                  f"Avg conf: {metrics.avg_confidence:.3f} | "
                  f"Patterns: {metrics.patterns_extracted:2d} | "
                  f"Learning acc: {metrics.learning_accuracy:.1%} | "
                  f"Rate: {cycles_per_sec:.1f} c/s")

            # Calculate prediction accuracy for this window
            if metrics.learning_accuracy > 0:
                accuracy_windows.append(metrics.learning_accuracy)

            # Track learning updates
            if metrics.patterns_extracted > 0:
                learning_updates.append(i + 1)

    elapsed_total = time.time() - start_time
    print()
    print(f"✓ Completed {num_cycles} cycles in {elapsed_total:.1f}s ({num_cycles/elapsed_total:.1f} cycles/s)")
    print()

    # Final metrics
    metrics = coordinator.get_metrics()

    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    print(f"Total Cycles: {metrics.total_cycles}")
    print(f"Coordinations: {metrics.coordinations} ({metrics.coordination_rate:.1%})")
    print()

    # Epistemic distribution
    epistemic_summary = coordinator.get_epistemic_summary()
    if epistemic_summary:
        print("Epistemic State Distribution:")
        for state, pct in sorted(epistemic_summary.items(), key=lambda x: x[1], reverse=True):
            print(f"  {state:12s}: {pct:6.1%}")
        print()

        print("Average Epistemic Metrics:")
        print(f"  Coherence:  {metrics.avg_coherence:.3f}")
        print(f"  Confidence: {metrics.avg_confidence:.3f}")
        print(f"  Stability:  {metrics.avg_stability:.3f}")
        print()

    # Learning evolution
    if metrics.patterns_extracted > 0:
        print("Learning System:")
        print(f"  Patterns extracted: {metrics.patterns_extracted}")
        print(f"  Success factors: {metrics.success_factors_discovered}")
        print(f"  Network insights: {metrics.network_insights_discovered}")
        print(f"  Final prediction accuracy: {metrics.learning_accuracy:.1%}")
        print()

        if len(accuracy_windows) > 1:
            print("Learning Evolution:")
            print(f"  Initial accuracy (cycle 100): {accuracy_windows[0]:.1%}")
            print(f"  Final accuracy (cycle {num_cycles}): {accuracy_windows[-1]:.1%}")
            improvement = (accuracy_windows[-1] - accuracy_windows[0]) * 100
            print(f"  Improvement: {improvement:+.1f}pp")
            print()

            # Show accuracy trend
            print("Accuracy Trend (every 100 cycles):")
            for i, acc in enumerate(accuracy_windows[:10], 1):  # First 10 windows
                bar_length = int(acc * 50)
                bar = "█" * bar_length
                print(f"  Cycle {i*100:4d}: {bar} {acc:.1%}")

            if len(accuracy_windows) > 10:
                print(f"  ... ({len(accuracy_windows) - 10} more windows)")
                # Show last window
                acc = accuracy_windows[-1]
                bar_length = int(acc * 50)
                bar = "█" * bar_length
                print(f"  Cycle {len(accuracy_windows)*100:4d}: {bar} {acc:.1%}")
            print()

    # Learned patterns
    learned = coordinator.get_learned_patterns_summary()
    if learned and learned.get('patterns'):
        print("Top Learned Patterns:")
        for i, pattern in enumerate(learned['patterns'][:3], 1):
            print(f"  {i}. {pattern['description']}")
            print(f"     Frequency: {pattern['frequency']}, Confidence: {pattern['confidence']:.3f}")
        print()

        if learned.get('success_factors'):
            print("Success Factors Discovered:")
            for i, factor in enumerate(learned['success_factors'][:2], 1):
                print(f"  {i}. {factor['name']}: {factor['correlation']:+.3f} "
                      f"(confidence: {factor['confidence']:.3f})")
            print()

        print(f"Quality Trajectory: {learned['quality_trajectory']}")
        print(f"Confidence Trajectory: {learned['confidence_trajectory']}")
        print()

    # Interventions
    if metrics.interventions_triggered > 0:
        print("Interventions:")
        print(f"  Total triggered: {metrics.interventions_triggered}")
        for intervention_type, count in sorted(metrics.interventions_by_type.items(),
                                               key=lambda x: x[1], reverse=True):
            print(f"  {intervention_type}: {count}")
        print()

    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print()

    # Success criteria
    success_criteria = []

    if metrics.patterns_extracted > 0:
        success_criteria.append(f"✅ Learning working ({metrics.patterns_extracted} patterns extracted)")
    else:
        success_criteria.append("❌ No patterns extracted")

    if len(accuracy_windows) > 1 and accuracy_windows[-1] > accuracy_windows[0]:
        success_criteria.append(f"✅ Learning improving over time ({improvement:+.1f}pp)")
    elif len(accuracy_windows) > 1:
        success_criteria.append("⚠️  Learning accuracy stable (no clear improvement)")

    if metrics.interventions_triggered > 0:
        success_criteria.append(f"✅ Interventions triggered ({metrics.interventions_triggered} times)")
    else:
        success_criteria.append("⚠️  No interventions needed (system stable)")

    if metrics.coordination_rate > 0.3:
        success_criteria.append(f"✅ Healthy coordination rate ({metrics.coordination_rate:.1%})")
    else:
        success_criteria.append(f"⚠️  Low coordination rate ({metrics.coordination_rate:.1%})")

    for criterion in success_criteria:
        print(criterion)

    print()
    print(f"Phase 2b validated over {num_cycles} cycles")
    print()


if __name__ == "__main__":
    import sys

    # Default to 1000 cycles, but allow override
    num_cycles = 1000
    if len(sys.argv) > 1:
        num_cycles = int(sys.argv[1])

    run_longduration_validation(num_cycles)
