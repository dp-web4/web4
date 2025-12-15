#!/usr/bin/env python3
"""
Test Phase 2c + SAGE with Tuned Threshold - Full Comparison
============================================================

Compares three configurations at optimal satisfaction threshold (0.60):
1. Baseline: Phase 2b with 0.60 threshold (no circadian, no SAGE)
2. Circadian: Phase 2c with 0.60 threshold (circadian only)
3. Combined: Phase 2c with 0.60 threshold + SAGE patterns

Tests if compound benefits emerge when satisfaction threshold is appropriately calibrated.

Created: December 15, 2025
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

from web4_phase2b_integrated_coordinator import Web4IntegratedCoordinator
from web4_phase2c_circadian_coordinator import Web4CircadianCoordinator
from pattern_exchange_protocol import (
    SAGEToUniversalConverter,
    UniversalToWeb4Converter
)
from web4_production_coordinator import CoordinationParameters
from sage.core.circadian_clock import CircadianPhase


# Use threshold that enabled coordination in sweep test
TUNED_THRESHOLD = 0.60


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

    converter = SAGEToUniversalConverter()
    universal_patterns = converter.export_consolidated_memory(consolidated)

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
        network_density = random.uniform(0.4, 0.95)
        trust_score = random.uniform(0.5, 0.95)
        diversity_score = random.uniform(0.3, 0.85)

        quality = 0.5
        if network_density > 0.7:
            quality += 0.20
        if trust_score > 0.8:
            quality += 0.18
        if diversity_score > 0.6:
            quality += 0.15

        quality = max(0.0, min(1.0, quality + random.uniform(-0.08, 0.08)))

        stream.append({
            'priority': random.uniform(0.6, 0.95),
            'trust_score': trust_score,
            'network_density': network_density,
            'quality_score': quality,
            'context': {'diversity_score': diversity_score}
        })

    return stream


def test_baseline_tuned():
    """Test baseline Phase 2b with tuned threshold."""
    print("=" * 80)
    print(f"BASELINE: Phase 2b (threshold={TUNED_THRESHOLD})")
    print("=" * 80)
    print()

    params = CoordinationParameters(satisfaction_threshold=TUNED_THRESHOLD)

    coordinator = Web4IntegratedCoordinator(
        params=params,
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


def test_circadian_tuned():
    """Test Phase 2c with circadian, tuned threshold."""
    print("=" * 80)
    print(f"CIRCADIAN: Phase 2c (threshold={TUNED_THRESHOLD})")
    print("=" * 80)
    print()

    params = CoordinationParameters(satisfaction_threshold=TUNED_THRESHOLD)

    coordinator = Web4CircadianCoordinator(
        params=params,
        enable_circadian=True,
        enable_epistemic=True,
        enable_learning=True,
        enable_interventions=False,
        circadian_period=100
    )

    stream = generate_coordination_stream(500)

    print("Running 500 cycles with circadian...")
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

            if telemetry.circadian_phase in ['day', 'dawn']:
                day_coords += 1
            elif telemetry.circadian_phase in ['night', 'deep_night']:
                night_coords += 1

    coord_rate = coordinations / len(stream)
    avg_quality = total_quality / coordinations if coordinations > 0 else 0.0

    phase_summary = coordinator.get_phase_summary()

    print(f"Coordination rate: {coord_rate:.1%}")
    print(f"Average quality: {avg_quality:.3f}")
    if coordinations > 0:
        print(f"Day coordinations: {day_coords} ({day_coords/coordinations*100:.1f}%)")
        print(f"Night coordinations: {night_coords} ({night_coords/coordinations*100:.1f}%)")

    print()
    print("Quality by Phase:")
    for phase in ['day', 'night']:
        stats = phase_summary.get(phase, {})
        print(f"  {phase:6s}: {stats.get('avg_quality', 0.0):.3f}")

    print()

    return {
        'rate': coord_rate,
        'quality': avg_quality,
        'day_coords': day_coords,
        'night_coords': night_coords
    }


def test_combined_tuned():
    """Test Phase 2c + SAGE with tuned threshold."""
    print("=" * 80)
    print(f"COMBINED: Phase 2c + SAGE (threshold={TUNED_THRESHOLD})")
    print("=" * 80)
    print()

    # Load SAGE patterns
    print("Loading SAGE Session 42 patterns...")
    sage_patterns = load_sage_session42_patterns()
    print(f"✓ Loaded {len(sage_patterns)} patterns")
    print()

    params = CoordinationParameters(satisfaction_threshold=TUNED_THRESHOLD)

    coordinator = Web4CircadianCoordinator(
        params=params,
        enable_circadian=True,
        enable_epistemic=True,
        enable_learning=True,
        enable_interventions=False,
        circadian_period=100
    )

    # Pre-seed with SAGE patterns
    if coordinator.learnings is None:
        from web4_coordination_learning import ConsolidatedLearnings
        coordinator.learnings = ConsolidatedLearnings(
            patterns=[],
            success_factors=[],
            network_insights=[]
        )
    coordinator.learnings.patterns.extend(sage_patterns)
    print(f"✓ Pre-seeded with {len(coordinator.learnings.patterns)} patterns")
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
    sage_usage = sage_used / coordinations if coordinations > 0 else 0.0

    phase_summary = coordinator.get_phase_summary()

    print(f"Coordination rate: {coord_rate:.1%}")
    print(f"Average quality: {avg_quality:.3f}")
    print(f"SAGE pattern usage: {sage_usage:.1%}")
    if coordinations > 0:
        print(f"Day coordinations: {day_coords} ({day_coords/coordinations*100:.1f}%)")
        print(f"Night coordinations: {night_coords} ({night_coords/coordinations*100:.1f}%)")

    print()
    print("Quality by Phase:")
    for phase in ['day', 'night']:
        stats = phase_summary.get(phase, {})
        print(f"  {phase:6s}: {stats.get('avg_quality', 0.0):.3f}")

    print()

    return {
        'rate': coord_rate,
        'quality': avg_quality,
        'sage_usage': sage_usage,
        'day_coords': day_coords,
        'night_coords': night_coords
    }


def run_tuned_comparison():
    """Run complete comparison with tuned threshold."""
    print("=" * 80)
    print(f"Phase 2c + SAGE Comparison (Tuned Threshold = {TUNED_THRESHOLD})")
    print("=" * 80)
    print()

    print("Testing three configurations at optimal threshold:")
    print(f"  1. Baseline: Phase 2b (threshold={TUNED_THRESHOLD})")
    print(f"  2. Circadian: Phase 2c (threshold={TUNED_THRESHOLD})")
    print(f"  3. Combined: Phase 2c + SAGE (threshold={TUNED_THRESHOLD})")
    print()

    # Run tests
    baseline = test_baseline_tuned()
    print("\\n")

    circadian = test_circadian_tuned()
    print("\\n")

    combined = test_combined_tuned()
    print("\\n")

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
    circadian_delta = (circadian['rate'] - baseline['rate']) * 100
    sage_delta = (combined['rate'] - circadian['rate']) * 100
    total_delta = (combined['rate'] - baseline['rate']) * 100

    print("Coordination Rate Changes:")
    print(f"  Circadian contribution: {circadian_delta:+.1f}pp")
    print(f"  SAGE contribution:      {sage_delta:+.1f}pp")
    print(f"  Total change:           {total_delta:+.1f}pp")
    print()

    quality_circadian = circadian['quality'] - baseline['quality']
    quality_sage = combined['quality'] - circadian['quality']
    quality_total = combined['quality'] - baseline['quality']

    print("Quality Changes:")
    print(f"  Circadian: {quality_circadian:+.3f}")
    print(f"  + SAGE:    {quality_sage:+.3f}")
    print(f"  Total:     {quality_total:+.3f}")
    print()

    # Assess compound benefits
    if sage_delta > 1.0:
        print("✅ SAGE PATTERNS CONTRIBUTE POSITIVELY")
        print(f"   Adding SAGE patterns improved coordination by {sage_delta:+.1f}pp")
        print(f"   With tuned threshold ({TUNED_THRESHOLD}), compound benefits emerge")
    elif sage_delta > -1.0:
        print("⚪ SAGE PATTERNS NEUTRAL")
        print(f"   SAGE contribution minimal ({sage_delta:+.1f}pp)")
    else:
        print("⚠️  SAGE PATTERNS STILL SUPPRESS COORDINATION")
        print(f"   SAGE reduced coordination by {sage_delta:.1f}pp")

    print()

    if total_delta > 0:
        print(f"Overall: Combined system better than baseline ({total_delta:+.1f}pp)")
    else:
        print(f"Overall: Combined system worse than baseline ({total_delta:+.1f}pp)")

    print()

    return {
        'baseline': baseline,
        'circadian': circadian,
        'combined': combined,
        'circadian_delta': circadian_delta,
        'sage_delta': sage_delta,
        'total_delta': total_delta
    }


if __name__ == "__main__":
    results = run_tuned_comparison()

    print("=" * 80)
    print("RESEARCH SUMMARY")
    print("=" * 80)
    print()

    print(f"Satisfaction Threshold: {TUNED_THRESHOLD}")
    print()

    if results['sage_delta'] > 0:
        print("Key Finding:")
        print("  With appropriate threshold calibration, circadian + SAGE can combine effectively")
        print()
        print(f"  Circadian: temporal optimization ({results['circadian_delta']:+.1f}pp)")
        print(f"  SAGE: pattern-based improvement ({results['sage_delta']:+.1f}pp)")
        print(f"  Combined: {results['total_delta']:+.1f}pp total")
        print()
        print("✅ COMPOUND BENEFITS CONFIRMED (with tuned parameters)")
    else:
        print("Finding:")
        print(f"  Even with tuned threshold ({TUNED_THRESHOLD}), SAGE patterns don't improve coordination")
        print("  May need pattern filtering or characteristic validation")

    print()
