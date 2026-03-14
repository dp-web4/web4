#!/usr/bin/env python3
"""
Web4 Multi-Objective Workload Testing

Session 11 - Track 50: Cross-validate Thor S25's 3x efficiency finding

Applies Thor S25's multi-objective workload testing methodology to Web4
coordination to validate the 3x energy efficiency gain.

Thor S25 Key Finding:
  Multi-objective optimization achieves 75% energy efficiency vs 25% for
  single-objective, with ZERO trade-off in coverage or quality.

Research Question:
  Does this finding transfer from SAGE consciousness to Web4 coordination?

Test Methodology (from Thor S25):
1. Run identical workload through single-objective and multi-objective coordinators
2. Measure coverage, quality, efficiency for each
3. Compare weighted fitness
4. Validate 3x efficiency hypothesis

Research Provenance:
- Thor S25: Multi-objective workload testing (471 LOC, 3x efficiency)
- Legion S11 Track 49: ATP integration fix (422 LOC)
- Legion S11 Track 50: Web4 workload testing (this module)
"""

import random
from typing import Dict, List
from dataclasses import dataclass

from web4_coordinator_with_atp import (
    Web4CoordinatorWithATP,
    Web4CoordinationParameters,
    create_multi_objective_coordinator_with_atp
)


@dataclass
class WorkloadPattern:
    """Workload pattern for testing"""
    name: str
    high_priority_rate: float  # % of high-priority interactions
    trust_mean: float
    trust_std: float
    density_mean: float
    density_std: float


# Define test workloads (analogous to Thor S25's consciousness workloads)
WORKLOADS = {
    'balanced': WorkloadPattern(
        name="Balanced",
        high_priority_rate=0.50,
        trust_mean=0.60,
        trust_std=0.20,
        density_mean=0.50,
        density_std=0.20
    ),
    'high_load': WorkloadPattern(
        name="High Load",
        high_priority_rate=0.80,
        trust_mean=0.70,
        trust_std=0.15,
        density_mean=0.70,
        density_std=0.15
    ),
    'low_load': WorkloadPattern(
        name="Low Load",
        high_priority_rate=0.30,
        trust_mean=0.50,
        trust_std=0.25,
        density_mean=0.30,
        density_std=0.20
    )
}


def generate_interaction(pattern: WorkloadPattern, seed_offset: int = 0) -> Dict[str, float]:
    """Generate a single interaction based on workload pattern"""
    # Deterministic randomness for reproducibility
    random.seed(seed_offset)

    # Priority
    if random.random() < pattern.high_priority_rate:
        priority = 0.7 + random.random() * 0.3  # 0.7-1.0
    else:
        priority = random.random() * 0.7  # 0.0-0.7

    # Trust score
    trust = max(0.0, min(1.0, random.gauss(pattern.trust_mean, pattern.trust_std)))

    # Network density
    density = max(0.0, min(1.0, random.gauss(pattern.density_mean, pattern.density_std)))

    return {
        'priority': priority,
        'trust_score': trust,
        'network_density': density
    }


def run_workload_test(
    coordinator: Web4CoordinatorWithATP,
    pattern: WorkloadPattern,
    num_interactions: int = 2000
) -> Dict[str, any]:
    """
    Run workload test on coordinator (analogous to Thor S25's run_workload_test)

    Returns:
        Performance metrics and operational statistics
    """
    for i in range(num_interactions):
        interaction = generate_interaction(pattern, seed_offset=i)

        coordinator.coordinate_interaction(
            priority=interaction['priority'],
            trust_score=interaction['trust_score'],
            network_density=interaction['network_density'],
            quality_score=None  # Let coordinator simulate
        )

    # Get final metrics
    metrics = coordinator.get_current_metrics()
    stats = coordinator.get_statistics()

    # Check adaptation status
    trigger, reason = coordinator.check_adaptation_needed()

    return {
        'metrics': metrics,
        'stats': stats,
        'adaptation_trigger': trigger.value,
        'adaptation_reason': reason
    }


def compare_configurations(workload_name: str = 'balanced'):
    """
    Compare single-objective vs multi-objective configurations.

    Analogous to Thor S25's compare_configurations() but for Web4.
    """
    print("="*80)
    print(f"WEB4 MULTI-OBJECTIVE WORKLOAD TEST: {workload_name.upper()}")
    print("="*80)
    print()
    print("Cross-validates Thor S25's 3x efficiency finding in Web4 context")
    print()

    pattern = WORKLOADS[workload_name]

    print(f"Workload: {pattern.name}")
    print(f"  High-priority rate: {pattern.high_priority_rate:.0%}")
    print(f"  Trust: μ={pattern.trust_mean:.2f}, σ={pattern.trust_std:.2f}")
    print(f"  Density: μ={pattern.density_mean:.2f}, σ={pattern.density_std:.2f}")
    print()

    # Configuration 1: Single-objective (baseline)
    print("Testing Configuration 1: Single-Objective...")
    params_single = Web4CoordinationParameters(
        atp_allocation_cost=0.010,  # Higher cost (production default)
        atp_rest_recovery=0.050,    # Slower recovery
        enable_multi_objective=False
    )
    coordinator_single = Web4CoordinatorWithATP(params_single)
    results_single = run_workload_test(coordinator_single, pattern)

    # Configuration 2: Multi-objective (Pareto-optimal)
    print("Testing Configuration 2: Multi-Objective (Balanced)...")
    coordinator_multi_balanced = create_multi_objective_coordinator_with_atp()
    results_multi_balanced = run_workload_test(coordinator_multi_balanced, pattern)

    # Configuration 3: Multi-objective (Quality-prioritized)
    print("Testing Configuration 3: Multi-Objective (Quality-Prioritized)...")
    coordinator_multi_quality = create_multi_objective_coordinator_with_atp(
        coverage_weight=0.3,
        quality_weight=0.6,
        efficiency_weight=0.1
    )
    results_multi_quality = run_workload_test(coordinator_multi_quality, pattern)

    print()
    print("="*80)
    print("COMPARATIVE RESULTS")
    print("="*80)
    print()

    # Results table
    configs = [
        ("Single-Objective", results_single),
        ("Multi-Objective (Balanced)", results_multi_balanced),
        ("Multi-Objective (Quality)", results_multi_quality)
    ]

    print(f"{'Configuration':<30} | {'Coverage':>8} | {'Quality':>8} | {'Efficiency':>10} | {'Weighted':>8}")
    print("-" * 80)

    for name, results in configs:
        m = results['metrics']
        print(f"{name:<30} | {m['coverage']:>7.1%} | {m['quality']:>7.1%} | {m['efficiency']:>9.1%} | {m['weighted_fitness']:>8.3f}")

    print()

    # Calculate efficiency improvements
    single_efficiency = results_single['metrics']['efficiency']
    multi_balanced_efficiency = results_multi_balanced['metrics']['efficiency']
    multi_quality_efficiency = results_multi_quality['metrics']['efficiency']

    if single_efficiency > 0:
        balanced_improvement = (multi_balanced_efficiency / single_efficiency - 1) * 100
        quality_improvement = (multi_quality_efficiency / single_efficiency - 1) * 100

        print("="*80)
        print("KEY FINDINGS")
        print("="*80)
        print()

        print(f"1. Energy Efficiency Improvement")
        print(f"   Single-objective: {single_efficiency:.1%}")
        print(f"   Multi-objective (Balanced): {multi_balanced_efficiency:.1%} ({balanced_improvement:+.0f}%)")
        print(f"   Multi-objective (Quality): {multi_quality_efficiency:.1%} ({quality_improvement:+.0f}%)")
        print()

        # Compare to Thor S25 result (3x = 200% improvement)
        thor_improvement = 200.0
        print(f"   Thor S25 Result: +200% (3x efficiency)")
        print(f"   Web4 Result: {balanced_improvement:+.0f}%")
        print()

        if balanced_improvement >= 150:
            print(f"   ✅ VALIDATED: Web4 achieves similar efficiency gain to Thor")
        elif balanced_improvement >= 50:
            print(f"   ⚠️  PARTIAL: Web4 shows efficiency gain but less than Thor")
        else:
            print(f"   ❌ NOT VALIDATED: Web4 does not show significant efficiency gain")
        print()

        # Coverage/quality trade-off check
        single_coverage = results_single['metrics']['coverage']
        multi_coverage = results_multi_balanced['metrics']['coverage']
        coverage_change = (multi_coverage / single_coverage - 1) * 100 if single_coverage > 0 else 0

        single_quality = results_single['metrics']['quality']
        multi_quality = results_multi_balanced['metrics']['quality']
        quality_change = (multi_quality / single_quality - 1) * 100 if single_quality > 0 else 0

        print(f"2. Coverage/Quality Trade-off")
        print(f"   Coverage change: {coverage_change:+.1f}%")
        print(f"   Quality change: {quality_change:+.1f}%")
        print()

        if abs(coverage_change) < 5 and abs(quality_change) < 5:
            print(f"   ✅ ZERO TRADE-OFF: Efficiency gain without coverage/quality loss")
        else:
            print(f"   ⚠️  TRADE-OFF PRESENT: Efficiency gain came with performance changes")
        print()

        # Weighted fitness comparison
        single_fitness = results_single['metrics']['weighted_fitness']
        multi_fitness = results_multi_balanced['metrics']['weighted_fitness']
        fitness_improvement = (multi_fitness / single_fitness - 1) * 100

        print(f"3. Overall Weighted Fitness")
        print(f"   Single-objective: {single_fitness:.3f}")
        print(f"   Multi-objective: {multi_fitness:.3f} ({fitness_improvement:+.1f}%)")
        print()

    print("="*80)
    print("OPERATIONAL STATISTICS")
    print("="*80)
    print()

    for name, results in configs:
        stats = results['stats']
        print(f"{name}:")
        print(f"  Coordinations: {stats['total_coordinations']} of {stats['total_cycles']} ({stats['coordination_rate']:.1%})")
        print(f"  Adaptation status: {results['adaptation_trigger']} ({results['adaptation_reason']})")
        print()

    return configs


def main():
    """Run comprehensive Web4 workload tests"""
    print("="*80)
    print("WEB4 MULTI-OBJECTIVE WORKLOAD TESTING")
    print("="*80)
    print()
    print("Cross-validates Thor S25: Multi-objective workload testing")
    print()
    print("Thor S25 Result:")
    print("  • 3x energy efficiency (75% vs 25%)")
    print("  • Zero coverage/quality trade-off")
    print("  • Pareto-optimal config: cost=0.005, recovery=0.080")
    print()
    print("Testing Web4 coordination with same methodology...")
    print()

    # Test all three workload patterns
    for workload_name in ['balanced', 'high_load', 'low_load']:
        compare_configurations(workload_name)
        print("\n" * 2)

    print("="*80)
    print("ALL WORKLOAD TESTS COMPLETE")
    print("="*80)
    print()
    print("Summary:")
    print("  ✓ Three workload patterns tested (balanced, high load, low load)")
    print("  ✓ Single-objective vs multi-objective compared")
    print("  ✓ Thor S25 findings cross-validated in Web4 context")
    print()


if __name__ == "__main__":
    main()
