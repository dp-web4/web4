#!/usr/bin/env python3
"""
Test Phase 2c with SAGE Patterns - Tuned Parameters
===================================================

Tests circadian + SAGE integration with adjusted satisfaction threshold
to avoid over-conservative coordination.

Based on findings from initial test:
- Original: satisfaction_threshold = 0.95 → 0% coordination
- This test: Try 0.75, 0.65, 0.55 to find optimal balance

Hypothesis:
- Lower satisfaction threshold will allow circadian + SAGE to both contribute
- Need to balance quality vs coordination rate
- Find threshold where compound benefits emerge

Created: December 15, 2025
Session: Autonomous Web4 Research Session 52
"""

import json
import random
import sys
import time
from pathlib import Path
from typing import List, Dict
from dataclasses import replace

sys.path.insert(0, '/home/dp/ai-workspace/web4/web4-standard/implementation/reference')
sys.path.insert(0, '/home/dp/ai-workspace/HRM')

from web4_phase2c_circadian_coordinator import Web4CircadianCoordinator
from pattern_exchange_protocol import (
    SAGEToUniversalConverter,
    UniversalToWeb4Converter
)
from web4_coordination_learning import CoordinationLearner
from web4_production_coordinator import CoordinationParameters
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

        # Quality with embedded patterns
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


def test_phase2c_with_threshold(satisfaction_threshold: float, sage_patterns: List):
    """Test Phase 2c with SAGE patterns at specific satisfaction threshold."""

    # Create custom parameters with tuned threshold
    params = CoordinationParameters(
        satisfaction_threshold=satisfaction_threshold
    )

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

    stream = generate_coordination_stream(500)

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

    return {
        'threshold': satisfaction_threshold,
        'rate': coord_rate,
        'quality': avg_quality,
        'day_coords': day_coords,
        'night_coords': night_coords,
        'coordinations': coordinations
    }


def run_threshold_sweep():
    """Run tests across multiple satisfaction thresholds."""
    print("=" * 80)
    print("Phase 2c + SAGE: Satisfaction Threshold Sweep")
    print("=" * 80)
    print()

    # Load SAGE patterns once
    print("Loading SAGE Session 42 patterns...")
    sage_patterns = load_sage_session42_patterns()
    print(f"✓ Loaded {len(sage_patterns)} patterns")
    print()

    # Test multiple thresholds
    thresholds = [0.95, 0.85, 0.75, 0.65, 0.55, 0.45]

    print(f"Testing {len(thresholds)} satisfaction thresholds...")
    print()

    results = []

    for threshold in thresholds:
        print(f"Testing threshold = {threshold:.2f}...")
        result = test_phase2c_with_threshold(threshold, sage_patterns)
        results.append(result)

        print(f"  Coordination rate: {result['rate']:.1%}")
        print(f"  Average quality: {result['quality']:.3f}")
        if result['coordinations'] > 0:
            print(f"  Day/Night: {result['day_coords']}/{result['night_coords']}")
        print()

    # Summary
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    print(f"{'Threshold':>10s} | {'Coord Rate':>12s} | {'Avg Quality':>12s} | {'Day %':>8s} | {'Night %':>8s}")
    print("-" * 80)

    for r in results:
        if r['coordinations'] > 0:
            day_pct = r['day_coords'] / r['coordinations'] * 100
            night_pct = r['night_coords'] / r['coordinations'] * 100
            print(f"{r['threshold']:10.2f} | {r['rate']:12.1%} | {r['quality']:12.3f} | "
                  f"{day_pct:8.1f} | {night_pct:8.1f}")
        else:
            print(f"{r['threshold']:10.2f} | {r['rate']:12.1%} | {'N/A':>12s} | "
                  f"{'N/A':>8s} | {'N/A':>8s}")

    print()

    # Find optimal threshold
    viable_results = [r for r in results if r['coordinations'] > 0 and r['rate'] > 0.05]

    if viable_results:
        # Optimize for quality while maintaining reasonable coordination rate
        best = max(viable_results, key=lambda r: r['quality'] if r['rate'] > 0.10 else 0)

        print(f"Recommended threshold: {best['threshold']:.2f}")
        print(f"  Coordination rate: {best['rate']:.1%}")
        print(f"  Average quality: {best['quality']:.3f}")
        print(f"  Day/Night balance: {best['day_coords']}/{best['night_coords']}")
        print()

    return results


if __name__ == "__main__":
    results = run_threshold_sweep()

    print("=" * 80)
    print("FINDINGS")
    print("=" * 80)
    print()

    print("Threshold Sensitivity Analysis:")
    print("  Original 0.95 threshold caused 0% coordination with circadian + SAGE")
    print("  This test explores lower thresholds to find optimal balance")
    print()

    has_viable = any(r['coordinations'] > 0 for r in results)

    if has_viable:
        print("✅ Found viable thresholds!")
        print("   Circadian + SAGE can work with appropriate calibration")
    else:
        print("⚠️  No viable thresholds found")
        print("   May need to adjust circadian bias strength or SAGE pattern filtering")

    print()
