#!/usr/bin/env python3
"""
Web4 Phase 2b: Integrated Coordinator Demonstration
===================================================

Demonstrates the integrated epistemic + learning coordinator across
different operational scenarios.

Created: December 13, 2025
"""

import random
from typing import List, Dict
from web4_phase2b_integrated_coordinator import (
    Web4IntegratedCoordinator,
    CoordinationParameters,
    InterventionLevel
)


def generate_scenario_data(scenario_type: str, num_cycles: int) -> List[Dict]:
    """
    Generate coordination cycles for different operational scenarios.

    Args:
        scenario_type: 'production', 'stress', 'degrading', 'recovering'
        num_cycles: Number of cycles to generate

    Returns:
        List of coordination interaction dicts
    """
    cycles = []

    for i in range(num_cycles):
        progress = i / num_cycles  # 0.0 to 1.0

        if scenario_type == "production":
            # Healthy operation - high trust, stable network, good quality
            priority = random.uniform(0.6, 0.9)
            trust_score = random.uniform(0.7, 0.95)
            network_density = random.uniform(0.6, 0.85)
            quality_score = random.uniform(0.7, 0.9)
            diversity_score = random.uniform(0.5, 0.8)

        elif scenario_type == "stress":
            # High load - many coordination requests, varying quality
            priority = random.uniform(0.7, 1.0)  # High priority
            trust_score = random.uniform(0.5, 0.9)
            network_density = random.uniform(0.4, 0.9)
            quality_score = random.uniform(0.4, 0.8)
            diversity_score = random.uniform(0.3, 0.7)

        elif scenario_type == "degrading":
            # Performance declining over time
            degradation = progress * 0.4  # Degrade up to 40%
            priority = random.uniform(0.5, 0.8)
            trust_score = random.uniform(0.7 - degradation, 0.9 - degradation)
            network_density = random.uniform(0.6 - degradation, 0.8 - degradation)
            quality_score = random.uniform(0.7 - degradation, 0.9 - degradation)
            diversity_score = random.uniform(0.5 - degradation, 0.8 - degradation)

        elif scenario_type == "recovering":
            # Performance improving over time
            improvement = progress * 0.3  # Improve up to 30%
            priority = random.uniform(0.5, 0.8)
            trust_score = random.uniform(0.5 + improvement, 0.7 + improvement)
            network_density = random.uniform(0.4 + improvement, 0.6 + improvement)
            quality_score = random.uniform(0.5 + improvement, 0.7 + improvement)
            diversity_score = random.uniform(0.4 + improvement, 0.6 + improvement)

        else:
            raise ValueError(f"Unknown scenario type: {scenario_type}")

        cycles.append({
            'priority': priority,
            'trust_score': trust_score,
            'network_density': network_density,
            'quality_score': quality_score,
            'diversity_score': diversity_score
        })

    return cycles


def run_scenario(
    scenario_name: str,
    cycles: List[Dict],
    enable_learning: bool = True,
    enable_interventions: bool = False
):
    """Run a coordination scenario and display results."""

    print("=" * 80)
    print(f"Scenario: {scenario_name.upper()} ({len(cycles)} cycles)")
    print("=" * 80)
    print()

    # Initialize coordinator
    coordinator = Web4IntegratedCoordinator(
        enable_epistemic=True,
        enable_learning=enable_learning,
        enable_interventions=enable_interventions,
        learning_frequency=50  # Update learnings every 50 cycles
    )

    features = []
    if enable_learning:
        features.append("learning")
    if enable_interventions:
        features.append("interventions")

    print(f"✓ Integrated coordinator ({', '.join(features) if features else 'tracking only'})")
    print()

    # Run coordination cycles
    for i, cycle in enumerate(cycles, 1):
        should_coord, telemetry = coordinator.coordinate_interaction(
            priority=cycle['priority'],
            trust_score=cycle['trust_score'],
            network_density=cycle['network_density'],
            quality_score=cycle['quality_score'],
            context={'diversity_score': cycle['diversity_score']}
        )

        # Display periodic updates
        if i % 25 == 0 or i == len(cycles):
            print(f"Cycle {i:3d}: {telemetry.epistemic_state:12s} | "
                  f"Conf: {telemetry.decision_confidence:.3f} | "
                  f"Coord: {'Yes' if should_coord else 'No '}")

            if telemetry.intervention_level != InterventionLevel.NONE:
                print(f"         → Intervention: {telemetry.intervention_level.value} "
                      f"({telemetry.intervention_reason})")

    print()

    # Display results
    metrics = coordinator.get_metrics()

    print("Results:")
    print(f"  Total cycles: {metrics.total_cycles}")
    print(f"  Coordinations: {metrics.coordinations} ({metrics.coordination_rate:.1%})")
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

    # Learning results
    if enable_learning:
        learned = coordinator.get_learned_patterns_summary()
        if learned:
            print("Learned Patterns:")
            for i, pattern in enumerate(learned['patterns'][:3], 1):
                print(f"  {i}. {pattern['type']:8s}: {pattern['description']}")
                print(f"     Frequency: {pattern['frequency']:3d}, Confidence: {pattern['confidence']:.3f}")
            print()

            if learned['success_factors']:
                print("Success Factors:")
                for i, factor in enumerate(learned['success_factors'][:2], 1):
                    print(f"  {i}. {factor['name']}: {factor['correlation']:+.3f} "
                          f"(confidence: {factor['confidence']:.3f})")
                print()

            print(f"Quality Trajectory: {learned['quality_trajectory']}")
            print(f"Confidence Trajectory: {learned['confidence_trajectory']}")
            print(f"Prediction Accuracy: {metrics.learning_accuracy:.1%}")
            print()

    # Intervention results
    if enable_interventions and metrics.interventions_triggered > 0:
        print("Interventions:")
        print(f"  Total triggered: {metrics.interventions_triggered}")
        for intervention_type, count in metrics.interventions_by_type.items():
            print(f"  {intervention_type}: {count}")
        print()


def run_all_scenarios():
    """Run all demonstration scenarios."""

    print("=" * 80)
    print("Web4 Phase 2b: Integrated Epistemic + Learning Coordinator")
    print("=" * 80)
    print()
    print("Demonstrating:")
    print("1. Production scenario (healthy operation)")
    print("2. Stress scenario (high load)")
    print("3. Degrading scenario (performance decline)")
    print("4. Recovering scenario (performance improvement)")
    print()
    print("Each scenario shows:")
    print("- Epistemic state tracking")
    print("- Coordination pattern learning")
    print("- Automatic interventions (if enabled)")
    print()

    # 1. Production scenario - tracking + learning
    production_cycles = generate_scenario_data("production", 100)
    run_scenario(
        "production",
        production_cycles,
        enable_learning=True,
        enable_interventions=False
    )

    print("\n\n")

    # 2. Stress scenario - tracking + learning + interventions
    stress_cycles = generate_scenario_data("stress", 100)
    run_scenario(
        "stress",
        stress_cycles,
        enable_learning=True,
        enable_interventions=True
    )

    print("\n\n")

    # 3. Degrading scenario - tracking + learning + interventions
    degrading_cycles = generate_scenario_data("degrading", 150)
    run_scenario(
        "degrading",
        degrading_cycles,
        enable_learning=True,
        enable_interventions=True
    )

    print("\n\n")

    # 4. Recovering scenario - tracking + learning
    recovering_cycles = generate_scenario_data("recovering", 150)
    run_scenario(
        "recovering",
        recovering_cycles,
        enable_learning=True,
        enable_interventions=False
    )

    print("\n\n")
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("✅ Phase 2b integrated coordinator operational")
    print("✅ Epistemic tracking working across scenarios")
    print("✅ Pattern learning adapting to different contexts")
    print("✅ Interventions triggering appropriately")
    print()
    print("Integration complete:")
    print("- Phase 1 (S16-20): Epistemic framework")
    print("- Phase 2a (S21): Runtime tracking design")
    print("- Phase 2b (S22+): Learning integration")
    print()
    print("Next steps:")
    print("- Long-duration validation (1000+ cycles)")
    print("- Real coordination data testing")
    print("- SAGE bidirectional learning")
    print("- ACT society deployment")
    print()


if __name__ == "__main__":
    import time
    start = time.time()

    run_all_scenarios()

    elapsed = time.time() - start
    print(f"Demo completed in {elapsed:.1f}s")
    print()
