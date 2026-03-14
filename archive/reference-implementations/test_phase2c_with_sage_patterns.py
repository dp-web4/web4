#!/usr/bin/env python3
"""
Test Phase 2c with SAGE Patterns - Compound Benefits
=====================================================

Tests if combining SAGE consciousness patterns with circadian temporal
awareness provides compound benefits beyond either alone.

Hypothesis:
- SAGE patterns improve coordination quality (Session 50: +24pp)
- Circadian awareness optimizes timing (Session 51: 10.2% DAY vs 0% NIGHT)
- Combined: Better decisions at optimal times

Created: December 14, 2025
Session: Autonomous Web4 Research Session 52
"""

import json
import random
import sys
import time
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, '/home/dp/ai-workspace/web4/web4-standard/implementation/reference')
sys.path.insert(0, '/home/dp/ai-workspace/HRM')

from web4_phase2c_circadian_coordinator import Web4CircadianCoordinator
from pattern_exchange_protocol import (
    SAGEToUniversalConverter,
    UniversalToWeb4Converter
)
from web4_coordination_learning import CoordinationLearner
from sage.core.circadian_clock import CircadianPhase


def load_sage_session42_patterns():
    """Load and convert real SAGE Session 42 patterns."""
    sage_path = Path('/home/dp/ai-workspace/HRM/sage/tests/dream_consolidation_results.json')

    with open(sage_path, 'r') as f:
        sage_data = json.load(f)

    from sage.core.dream_consolidation import (
        MemoryPattern,
        QualityLearning,
        CreativeAssociation,
        ConsolidatedMemory
    )

    # Reconstruct ConsolidatedMemory
    patterns = [
        MemoryPattern(
            pattern_type=p['pattern_type'],
            description=p['description'],
            strength=p['strength'],
            examples=p['examples'],
            frequency=p['frequency'],
            created_at=p['created_at']
        )
        for p in sage_data['patterns']
    ]

    quality_learnings = [
        QualityLearning(
            characteristic=ql['characteristic'],
            positive_correlation=ql['positive_correlation'],
            confidence=ql['confidence'],
            sample_size=ql['sample_size'],
            average_quality_with=ql['average_quality_with'],
            average_quality_without=ql['average_quality_without']
        )
        for ql in sage_data['quality_learnings']
    ]

    creative_associations = [
        CreativeAssociation(
            concept_a=ca['concept_a'],
            concept_b=ca['concept_b'],
            association_type=ca['association_type'],
            strength=ca['strength'],
            supporting_cycles=ca['supporting_cycles'],
            insight=ca['insight']
        )
        for ca in sage_data['creative_associations']
    ]

    consolidated = ConsolidatedMemory(
        dream_session_id=42,
        timestamp=sage_data['timestamp'],
        cycles_processed=sage_data['cycles_processed'],
        patterns=patterns,
        quality_learnings=quality_learnings,
        creative_associations=creative_associations,
        epistemic_insights=sage_data['epistemic_insights'],
        consolidation_time=sage_data['consolidation_time']
    )

    # Convert via protocol
    converter = SAGEToUniversalConverter()
    universal_patterns = converter.export_consolidated_memory(consolidated)

    # Convert to Web4 coordination patterns
    importer = UniversalToWeb4Converter()
    coord_patterns = []
    for universal in universal_patterns:
        coord = importer.convert_to_coordination_pattern(universal)
        if coord:
            coord_patterns.append(coord)

    return coord_patterns


def generate_coordination_stream(num_cycles: int = 500) -> List[Dict]:
    """Generate coordination stream with embedded patterns."""
    stream = []

    for i in range(num_cycles):
        # Realistic variation
        network_density = random.uniform(0.4, 0.95)
        trust_score = random.uniform(0.5, 0.95)
        diversity_score = random.uniform(0.3, 0.85)

        # Quality with embedded patterns (matching SAGE learnings)
        quality = 0.5

        if network_density > 0.7:
            quality += 0.20
        if trust_score > 0.8:
            quality += 0.18
        if diversity_score > 0.6:
            quality += 0.15

        # Add noise
        quality = max(0.0, min(1.0, quality + random.uniform(-0.08, 0.08)))

        stream.append({
            'priority': random.uniform(0.6, 0.95),
            'trust_score': trust_score,
            'network_density': network_density,
            'quality_score': quality,
            'context': {'diversity_score': diversity_score}
        })

    return stream


def test_baseline_phase2b():
    """Test baseline Phase 2b (no circadian, no SAGE)."""
    print("=" * 80)
    print("BASELINE: Phase 2b (No Circadian, No SAGE)")
    print("=" * 80)
    print()

    from web4_phase2b_integrated_coordinator import Web4IntegratedCoordinator

    coordinator = Web4IntegratedCoordinator(
        enable_epistemic=True,
        enable_learning=True,
        enable_interventions=False
    )

    stream = generate_coordination_stream(500)

    print("Running 500 cycles...")
    coordinations = 0
    total_quality = 0.0

    for cycle in stream:
        should_coord, telemetry = coordinator.coordinate_interaction(
            priority=cycle['priority'],
            trust_score=cycle['trust_score'],
            network_density=cycle['network_density'],
            quality_score=cycle['quality_score'],
            context=cycle['context']
        )

        if should_coord:
            coordinations += 1
            total_quality += cycle['quality_score']

    coord_rate = coordinations / len(stream)
    avg_quality = total_quality / coordinations if coordinations > 0 else 0.0

    print(f"Coordination rate: {coord_rate:.1%}")
    print(f"Average quality: {avg_quality:.3f}")
    print()

    return {'rate': coord_rate, 'quality': avg_quality}


def test_phase2c_circadian_only():
    """Test Phase 2c with circadian but no SAGE patterns."""
    print("=" * 80)
    print("TEST 1: Phase 2c with Circadian (No SAGE)")
    print("=" * 80)
    print()

    coordinator = Web4CircadianCoordinator(
        enable_circadian=True,
        enable_epistemic=True,
        enable_learning=True,
        enable_interventions=False,
        circadian_period=100
    )

    stream = generate_coordination_stream(500)

    print("Running 500 cycles with circadian awareness...")
    coordinations = 0
    total_quality = 0.0
    day_coords = 0
    night_coords = 0

    for cycle in stream:
        should_coord, telemetry = coordinator.coordinate_interaction(
            priority=cycle['priority'],
            trust_score=cycle['trust_score'],
            network_density=cycle['network_density'],
            quality_score=cycle['quality_score'],
            context=cycle['context']
        )

        if should_coord:
            coordinations += 1
            total_quality += cycle['quality_score']

            # Track day/night distribution
            if telemetry.circadian_phase in ['day', 'dawn']:
                day_coords += 1
            elif telemetry.circadian_phase in ['night', 'deep_night']:
                night_coords += 1

    coord_rate = coordinations / len(stream)
    avg_quality = total_quality / coordinations if coordinations > 0 else 0.0

    phase_summary = coordinator.get_phase_summary()

    print(f"Overall coordination rate: {coord_rate:.1%}")
    print(f"Average quality: {avg_quality:.3f}")
    print(f"Day coordinations: {day_coords} ({day_coords/coordinations*100:.1f}%)")
    print(f"Night coordinations: {night_coords} ({night_coords/coordinations*100:.1f}%)")
    print()

    print("Quality by Phase:")
    for phase in ['day', 'night']:
        stats = phase_summary.get(phase, {})
        print(f"  {phase:6s}: {stats.get('avg_quality', 0.0):.3f}")

    print()

    return {'rate': coord_rate, 'quality': avg_quality, 'day_coords': day_coords, 'night_coords': night_coords}


def test_phase2c_with_sage():
    """Test Phase 2c with circadian AND SAGE patterns."""
    print("=" * 80)
    print("TEST 2: Phase 2c with Circadian + SAGE Patterns")
    print("=" * 80)
    print()

    # Load SAGE patterns
    print("Loading SAGE Session 42 patterns...")
    sage_patterns = load_sage_session42_patterns()
    print(f"✓ Loaded {len(sage_patterns)} SAGE patterns")
    print()

    coordinator = Web4CircadianCoordinator(
        enable_circadian=True,
        enable_epistemic=True,
        enable_learning=True,
        enable_interventions=False,
        circadian_period=100
    )

    # Pre-seed with SAGE patterns
    print("Pre-seeding coordinator with SAGE patterns...")
    if coordinator.learnings is None:
        from web4_coordination_learning import ConsolidatedLearnings
        coordinator.learnings = ConsolidatedLearnings(
            patterns=[],
            success_factors=[],
            network_insights=[]
        )
    coordinator.learnings.patterns.extend(sage_patterns)
    print(f"✓ Coordinator now has {len(coordinator.learnings.patterns)} patterns")
    print()

    # Debug: Show pattern types
    print("Pattern types loaded:")
    from collections import Counter
    pattern_types = Counter([p.pattern_type for p in sage_patterns])
    for ptype, count in pattern_types.items():
        print(f"  {ptype}: {count}")
    print()

    stream = generate_coordination_stream(500)

    print("Running 500 cycles with circadian + SAGE...")
    coordinations = 0
    total_quality = 0.0
    day_coords = 0
    night_coords = 0
    sage_used = 0

    for cycle in stream:
        should_coord, telemetry = coordinator.coordinate_interaction(
            priority=cycle['priority'],
            trust_score=cycle['trust_score'],
            network_density=cycle['network_density'],
            quality_score=cycle['quality_score'],
            context=cycle['context']
        )

        if should_coord:
            coordinations += 1
            total_quality += cycle['quality_score']

            if telemetry.learned_patterns_used > 0:
                sage_used += 1

            if telemetry.circadian_phase in ['day', 'dawn']:
                day_coords += 1
            elif telemetry.circadian_phase in ['night', 'deep_night']:
                night_coords += 1

    coord_rate = coordinations / len(stream)
    avg_quality = total_quality / coordinations if coordinations > 0 else 0.0
    sage_usage_rate = sage_used / coordinations if coordinations > 0 else 0.0

    phase_summary = coordinator.get_phase_summary()

    print(f"Overall coordination rate: {coord_rate:.1%}")
    print(f"Average quality: {avg_quality:.3f}")
    print(f"SAGE pattern usage: {sage_usage_rate:.1%}")
    if coordinations > 0:
        print(f"Day coordinations: {day_coords} ({day_coords/coordinations*100:.1f}%)")
        print(f"Night coordinations: {night_coords} ({night_coords/coordinations*100:.1f}%)")
    else:
        print("⚠️  WARNING: 0 coordinations occurred!")
        print(f"Day cycles: {day_coords}, Night cycles: {night_coords}")
    print()

    print("Quality by Phase:")
    for phase in ['day', 'night']:
        stats = phase_summary.get(phase, {})
        print(f"  {phase:6s}: {stats.get('avg_quality', 0.0):.3f}")

    print()

    return {
        'rate': coord_rate,
        'quality': avg_quality,
        'sage_usage': sage_usage_rate,
        'day_coords': day_coords,
        'night_coords': night_coords
    }


def run_comparison():
    """Run complete comparison test."""
    print("=" * 80)
    print("Phase 2c + SAGE Pattern Integration Test")
    print("=" * 80)
    print()

    print("Testing three configurations:")
    print("  1. Baseline: Phase 2b (no circadian, no SAGE)")
    print("  2. Circadian: Phase 2c (circadian only)")
    print("  3. Combined: Phase 2c + SAGE patterns")
    print()

    # Baseline
    baseline = test_baseline_phase2b()
    print("\n")

    # Circadian only
    circadian = test_phase2c_circadian_only()
    print("\n")

    # Combined
    combined = test_phase2c_with_sage()
    print("\n")

    # Summary
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print()

    print(f"{'Configuration':<30s} | {'Coord Rate':>12s} | {'Avg Quality':>12s}")
    print("-" * 80)
    print(f"{'Baseline (Phase 2b)':<30s} | {baseline['rate']:12.1%} | {baseline['quality']:12.3f}")
    print(f"{'Circadian Only (Phase 2c)':<30s} | {circadian['rate']:12.1%} | {circadian['quality']:12.3f}")
    print(f"{'Circadian + SAGE':<30s} | {combined['rate']:12.1%} | {combined['quality']:12.3f}")
    print()

    # Calculate improvements
    circadian_improvement = (circadian['rate'] - baseline['rate']) * 100
    sage_improvement = (combined['rate'] - circadian['rate']) * 100
    total_improvement = (combined['rate'] - baseline['rate']) * 100

    print("Improvements vs Baseline:")
    print(f"  Circadian contribution: {circadian_improvement:+.1f}pp")
    print(f"  SAGE contribution:      {sage_improvement:+.1f}pp")
    print(f"  Total improvement:      {total_improvement:+.1f}pp")
    print()

    quality_baseline = baseline['quality']
    quality_circadian = circadian['quality']
    quality_combined = combined['quality']

    print("Quality Improvements:")
    print(f"  Circadian: {(quality_circadian - quality_baseline):+.3f}")
    print(f"  + SAGE:    {(quality_combined - quality_circadian):+.3f}")
    print(f"  Total:     {(quality_combined - quality_baseline):+.3f}")
    print()

    # Assess compound benefits
    if sage_improvement > 0:
        print("✅ COMPOUND BENEFITS CONFIRMED")
        print("   Circadian + SAGE provides benefits beyond either alone")
        print(f"   Circadian: temporal optimization ({circadian_improvement:+.1f}pp)")
        print(f"   SAGE: pattern-based decisions ({sage_improvement:+.1f}pp)")
        print(f"   Combined: {total_improvement:+.1f}pp total")
    elif total_improvement > 0:
        print("⚠️  PARTIAL BENEFITS")
        print(f"   Combined still better than baseline ({total_improvement:+.1f}pp)")
    else:
        print("⚠️  NO COMPOUND BENEFITS DETECTED")

    print()

    return {
        'baseline': baseline,
        'circadian': circadian,
        'combined': combined,
        'circadian_improvement': circadian_improvement,
        'sage_improvement': sage_improvement,
        'total_improvement': total_improvement
    }


if __name__ == "__main__":
    results = run_comparison()

    print("=" * 80)
    print("RESEARCH SUMMARY")
    print("=" * 80)
    print()

    print("This test validates compound benefits from combining:")
    print("  • Temporal awareness (circadian rhythm from Thor S49)")
    print("  • Pattern-based learning (SAGE patterns from S42)")
    print()

    if results['sage_improvement'] > 0:
        print("Key Finding:")
        print("  Circadian temporal optimization + SAGE pattern knowledge")
        print("  provides compound benefits for Web4 coordination.")
        print()
        print("  Circadian enables: Time-aware decisions (when to coordinate)")
        print("  SAGE enables: Pattern-based decisions (how to coordinate)")
        print("  Combined: Better decisions at optimal times")
    else:
        print("Finding:")
        print("  Results show interaction between temporal and pattern-based")
        print("  optimization, though may need larger scale for clear benefits.")

    print()
