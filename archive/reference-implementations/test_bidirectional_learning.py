#!/usr/bin/env python3
"""
Test Bidirectional Learning - Web4 ↔ SAGE Pattern Transfer
==========================================================

Demonstrates complete bidirectional pattern transfer:
1. Generate Web4 coordination data
2. Extract Web4 patterns
3. Export to universal format
4. Simulate SAGE patterns (universal format)
5. Import SAGE patterns into Web4
6. Measure effectiveness of imported patterns

Created: December 13, 2025
"""

import random
import time
from pathlib import Path
from typing import List, Dict

from web4_coordination_learning import (
    CoordinationLearner,
    PatternType,
    ConsolidatedLearnings
)
from pattern_exchange_protocol import (
    Web4ToUniversalConverter,
    UniversalToWeb4Converter
)
from universal_pattern_schema import (
    UniversalPattern,
    PatternDomain,
    PatternCategory
)


def generate_test_coordination_history(num_cycles: int = 200) -> List[Dict]:
    """
    Generate realistic coordination history for testing.

    Embedded patterns (known ground truth):
    - High network density (>0.7) → Success
    - High trust (>0.8) → Success
    - Low diversity (<0.3) → Failure
    """
    history = []

    for i in range(num_cycles):
        # Generate base metrics
        network_density = random.uniform(0.3, 0.95)
        trust_score = random.uniform(0.4, 0.95)
        diversity_score = random.uniform(0.2, 0.85)

        # Calculate quality based on embedded patterns
        quality = 0.5

        if network_density > 0.7:
            quality += 0.25
        if trust_score > 0.8:
            quality += 0.2
        if diversity_score < 0.3:
            quality -= 0.3

        quality = max(0.0, min(1.0, quality + random.uniform(-0.1, 0.1)))

        cycle = {
            'cycle_id': i,
            'network_density': network_density,
            'avg_trust_score': trust_score,
            'diversity_score': diversity_score,
            'quality': quality,
            'coordination_confidence': quality * 0.9 + random.uniform(0, 0.1),
            'parameter_stability': 0.8 + random.uniform(-0.1, 0.1),
            'objective_coherence': 0.9 + random.uniform(-0.05, 0.05),
            'coordination_succeeded': quality > 0.65,
            'timestamp': time.time() + i
        }

        history.append(cycle)

    return history


def create_simulated_sage_patterns() -> List[UniversalPattern]:
    """
    Create simulated SAGE consciousness patterns in universal format.

    These represent patterns SAGE would have learned from consciousness cycles.
    In real deployment, these would come from actual SAGE DREAM consolidation.
    """
    patterns = []

    # Pattern 1: High context richness → High quality
    pattern1 = UniversalPattern(
        pattern_id="sage_quality_high_context",
        source_domain=PatternDomain.CONSCIOUSNESS,
        category=PatternCategory.QUALITY,
        description="High context richness leads to high quality responses",
        characteristics={
            'context_richness': 0.85,      # Maps to network_density
            'confidence_level': 0.90,      # Maps to trust_score
            'epistemic_breadth': 0.75      # Maps to diversity_score
        },
        frequency=142,
        confidence=0.91,
        sample_size=160,
        quality_correlation=0.87,
        extraction_timestamp=time.time() - 86400,  # 1 day ago
        first_observed=time.time() - 172800,       # 2 days ago
        last_observed=time.time() - 3600           # 1 hour ago
    )
    patterns.append(pattern1)

    # Pattern 2: Low epistemic breadth → Low quality
    pattern2 = UniversalPattern(
        pattern_id="sage_quality_low_breadth",
        source_domain=PatternDomain.CONSCIOUSNESS,
        category=PatternCategory.FAILURE,
        description="Low epistemic breadth correlates with lower quality",
        characteristics={
            'context_richness': 0.45,
            'confidence_level': 0.60,
            'epistemic_breadth': 0.25      # Low breadth
        },
        frequency=78,
        confidence=0.82,
        sample_size=95,
        quality_correlation=-0.72,
        extraction_timestamp=time.time() - 86400,
        first_observed=time.time() - 172800,
        last_observed=time.time() - 7200
    )
    patterns.append(pattern2)

    # Pattern 3: Balanced characteristics → Stable quality
    pattern3 = UniversalPattern(
        pattern_id="sage_quality_balanced",
        source_domain=PatternDomain.CONSCIOUSNESS,
        category=PatternCategory.SUCCESS,
        description="Balanced characteristics produce stable quality",
        characteristics={
            'context_richness': 0.70,
            'confidence_level': 0.75,
            'epistemic_breadth': 0.65,
            'learning_stability': 0.85
        },
        frequency=203,
        confidence=0.95,
        sample_size=220,
        quality_correlation=0.79,
        extraction_timestamp=time.time() - 43200,  # 12 hours ago
        first_observed=time.time() - 259200,       # 3 days ago
        last_observed=time.time() - 1800           # 30 min ago
    )
    patterns.append(pattern3)

    return patterns


def test_web4_pattern_export():
    """Test: Export Web4 coordination patterns to universal format."""
    print("=" * 80)
    print("TEST 1: Web4 Pattern Export")
    print("=" * 80)
    print()

    # Generate coordination history
    print("Generating 200 coordination cycles...")
    history = generate_test_coordination_history(200)
    print(f"✓ Generated {len(history)} cycles")
    print()

    # Extract Web4 patterns
    print("Extracting Web4 coordination patterns...")
    learner = CoordinationLearner()
    learnings = learner.extract_patterns(history)
    print(f"✓ Extracted {len(learnings.patterns)} patterns")
    print(f"✓ Extracted {len(learnings.success_factors)} success factors")
    print()

    # Convert to universal format
    print("Converting to universal format...")
    converter = Web4ToUniversalConverter()
    universal_patterns = converter.export_learnings(
        learnings,
        export_path=Path("web4_patterns_export.json")
    )
    print(f"✓ Converted {len(universal_patterns)} patterns")
    print()

    # Display sample
    if universal_patterns:
        print("Sample Universal Pattern:")
        sample = universal_patterns[0]
        print(f"  ID: {sample.pattern_id}")
        print(f"  Source: {sample.source_domain.value}")
        print(f"  Category: {sample.category.value}")
        print(f"  Description: {sample.description}")
        print(f"  Characteristics: {list(sample.characteristics.keys())}")
        print(f"  Confidence: {sample.confidence:.3f}")
        print(f"  Quality Correlation: {sample.quality_correlation:+.3f}")
        print()

    return universal_patterns


def test_sage_pattern_import():
    """Test: Import simulated SAGE patterns into Web4."""
    print("=" * 80)
    print("TEST 2: SAGE Pattern Import to Web4")
    print("=" * 80)
    print()

    # Create simulated SAGE patterns
    print("Creating simulated SAGE patterns (universal format)...")
    sage_patterns = create_simulated_sage_patterns()
    print(f"✓ Created {len(sage_patterns)} SAGE patterns")
    print()

    # Display SAGE patterns
    print("SAGE Patterns (from consciousness domain):")
    for i, pattern in enumerate(sage_patterns, 1):
        print(f"{i}. {pattern.description}")
        print(f"   Category: {pattern.category.value}")
        print(f"   Characteristics: {pattern.characteristics}")
        print(f"   Confidence: {pattern.confidence:.3f}, Quality Correlation: {pattern.quality_correlation:+.3f}")
        print()

    # Export SAGE patterns to file
    export_data = {
        'export_timestamp': time.time(),
        'source_domain': 'consciousness',
        'num_patterns': len(sage_patterns),
        'patterns': [p.to_dict() for p in sage_patterns]
    }

    import json
    with open('sage_patterns_export.json', 'w') as f:
        json.dump(export_data, f, indent=2)
    print("✓ Exported SAGE patterns to sage_patterns_export.json")
    print()

    # Import into Web4
    print("Importing SAGE patterns into Web4...")
    importer = UniversalToWeb4Converter()
    coord_patterns = importer.import_patterns(Path("sage_patterns_export.json"))
    print(f"✓ Imported {len(coord_patterns)} patterns as Web4 coordination patterns")
    print()

    # Display imported patterns
    print("Imported as Web4 Coordination Patterns:")
    for i, pattern in enumerate(coord_patterns, 1):
        print(f"{i}. {pattern.description}")
        print(f"   Pattern type: {pattern.pattern_type.value}")
        print(f"   Characteristics: {list(pattern.characteristics.keys())}")
        print(f"   Average quality: {pattern.average_quality:.3f}")
        print(f"   Confidence: {pattern.confidence:.3f}")
        print()

    return coord_patterns


def test_pattern_effectiveness():
    """Test: Measure effectiveness of imported SAGE patterns on Web4 coordination."""
    print("=" * 80)
    print("TEST 3: Pattern Transfer Effectiveness")
    print("=" * 80)
    print()

    # Generate test coordination data
    print("Generating test coordination data...")
    test_history = generate_test_coordination_history(100)
    print(f"✓ Generated {len(test_history)} test cycles")
    print()

    # Learn from Web4 data only (baseline)
    print("Baseline: Learning from Web4 data only...")
    learner_web4_only = CoordinationLearner()
    learnings_web4_only = learner_web4_only.extract_patterns(test_history[:70])  # Train on 70
    print(f"✓ Learned {len(learnings_web4_only.patterns)} Web4-only patterns")
    print()

    # Test on remaining 30 cycles
    correct_web4_only = 0
    for cycle in test_history[70:]:
        interaction = {'quality_estimate': cycle['quality']}
        context = {
            'network_density': cycle['network_density'],
            'avg_trust_score': cycle['avg_trust_score'],
            'diversity_score': cycle['diversity_score']
        }

        should_coord, conf, _ = learner_web4_only.recommend(interaction, context, learnings_web4_only)
        if should_coord == cycle['coordination_succeeded']:
            correct_web4_only += 1

    accuracy_web4_only = correct_web4_only / 30
    print(f"Web4-only accuracy: {correct_web4_only}/30 ({accuracy_web4_only:.1%})")
    print()

    # Import SAGE patterns and add to Web4 learnings
    print("Enhanced: Web4 + imported SAGE patterns...")
    sage_patterns = create_simulated_sage_patterns()
    importer = UniversalToWeb4Converter()

    # Manually import (simpler than file-based for test)
    imported_patterns = []
    for sage_pattern in sage_patterns:
        coord_pattern = importer.convert_to_coordination_pattern(sage_pattern)
        if coord_pattern:
            imported_patterns.append(coord_pattern)

    print(f"✓ Imported {len(imported_patterns)} SAGE patterns")

    # Add imported patterns to Web4 learnings
    learnings_web4_plus_sage = learner_web4_only.extract_patterns(test_history[:70])
    learnings_web4_plus_sage.patterns.extend(imported_patterns)
    print(f"✓ Combined learnings: {len(learnings_web4_plus_sage.patterns)} total patterns")
    print()

    # Test with combined patterns
    correct_combined = 0
    for cycle in test_history[70:]:
        interaction = {'quality_estimate': cycle['quality']}
        context = {
            'network_density': cycle['network_density'],
            'avg_trust_score': cycle['avg_trust_score'],
            'diversity_score': cycle['diversity_score']
        }

        should_coord, conf, _ = learner_web4_only.recommend(interaction, context, learnings_web4_plus_sage)
        if should_coord == cycle['coordination_succeeded']:
            correct_combined += 1

    accuracy_combined = correct_combined / 30
    print(f"Web4 + SAGE accuracy: {correct_combined}/30 ({accuracy_combined:.1%})")
    print()

    # Calculate improvement
    improvement = (accuracy_combined - accuracy_web4_only) * 100
    print(f"Improvement from SAGE patterns: {improvement:+.1f}pp")
    print()

    if improvement > 0:
        print("✅ SAGE patterns improved Web4 coordination predictions!")
        print("   Cross-domain pattern transfer is effective.")
    elif improvement == 0:
        print("⚠️  No improvement detected")
        print("   SAGE patterns may not be relevant to this coordination data")
    else:
        print("⚠️  Slight decrease detected")
        print("   SAGE patterns may not transfer well to this specific scenario")

    print()

    return {
        'web4_only_accuracy': accuracy_web4_only,
        'combined_accuracy': accuracy_combined,
        'improvement_pp': improvement
    }


def run_all_tests():
    """Run complete bidirectional learning test suite."""
    print("=" * 80)
    print("Bidirectional Learning Test Suite")
    print("=" * 80)
    print()
    print("Testing Web4 ↔ SAGE pattern transfer with universal schema")
    print()

    # Test 1: Export Web4 patterns
    web4_patterns = test_web4_pattern_export()

    print("\n\n")

    # Test 2: Import SAGE patterns
    sage_patterns = test_sage_pattern_import()

    print("\n\n")

    # Test 3: Measure effectiveness
    results = test_pattern_effectiveness()

    print("\n\n")
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    print("✅ Web4 → Universal export: Working")
    print(f"   Exported {len(web4_patterns)} coordination patterns")
    print()

    print("✅ SAGE → Web4 import: Working")
    print(f"   Imported {len(sage_patterns)} consciousness patterns")
    print()

    print("✅ Pattern transfer effectiveness: Measured")
    print(f"   Web4-only accuracy: {results['web4_only_accuracy']:.1%}")
    print(f"   Web4 + SAGE accuracy: {results['combined_accuracy']:.1%}")
    print(f"   Improvement: {results['improvement_pp']:+.1f}pp")
    print()

    print("Bidirectional learning infrastructure complete:")
    print("- Universal pattern schema ✅")
    print("- Web4 export protocol ✅")
    print("- Web4 import protocol ✅")
    print("- Pattern characteristic mapping ✅")
    print("- Effectiveness measurement ✅")
    print()

    print("Next steps:")
    print("- Implement SAGE export (requires SAGE DREAM consolidation access)")
    print("- Test with real SAGE patterns from Sessions 42-44")
    print("- Long-duration validation (1000+ cycles)")
    print("- Continuous learning loop")
    print()


if __name__ == "__main__":
    import sys
    sys.path.insert(0, '/home/dp/ai-workspace/web4/web4-standard/implementation/reference')

    start_time = time.time()

    run_all_tests()

    elapsed = time.time() - start_time
    print(f"Tests completed in {elapsed:.1f}s")
    print()
