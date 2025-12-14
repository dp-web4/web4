#!/usr/bin/env python3
"""
Test Real SAGE Pattern Import V2 - Improved Characteristic Mapping
===================================================================

Fixes the characteristic mapping issue from V1 by properly using the
universal schema's defined mappings between consciousness and coordination.

V1 Issue: Created arbitrary characteristics that don't map to Web4 context
V2 Fix: Use proper schema mappings (epistemic_breadth → diversity_score, etc.)

Created: December 14, 2025
Session: Autonomous Web4 Research Session 49
"""

import json
import time
import random
import sys
from pathlib import Path
from typing import List, Dict

# Add paths
sys.path.insert(0, '/home/dp/ai-workspace/web4/web4-standard/implementation/reference')
sys.path.insert(0, '/home/dp/ai-workspace/HRM')

from web4_coordination_learning import (
    CoordinationLearner,
    PatternType,
    ConsolidatedLearnings
)
from pattern_exchange_protocol import (
    UniversalToWeb4Converter
)
from universal_pattern_schema import (
    UniversalPattern,
    PatternDomain,
    PatternCategory,
    STANDARD_MAPPINGS
)


def load_sage_session42_patterns() -> Dict:
    """Load real SAGE Session 42 consolidated memory."""
    sage_path = Path('/home/dp/ai-workspace/HRM/sage/tests/dream_consolidation_results.json')

    with open(sage_path, 'r') as f:
        consolidated = json.load(f)

    return consolidated


def convert_sage_to_universal_v2(sage_consolidated: Dict) -> List[UniversalPattern]:
    """
    Convert SAGE ConsolidatedMemory to UniversalPattern format V2.

    Improvements over V1:
    - Uses proper schema mappings from STANDARD_MAPPINGS
    - Maps SAGE characteristics to Web4-compatible names
    - Better quality correlation calculation
    """
    universal_patterns = []
    timestamp = sage_consolidated['timestamp']

    # Get SAGE → Coordination mappings
    mappings = {m.source_characteristic: m for m in STANDARD_MAPPINGS[('consciousness', 'coordination')]}

    # Convert memory patterns
    for i, pattern in enumerate(sage_consolidated['patterns']):
        pattern_type = pattern['pattern_type']

        # Map SAGE pattern types to categories
        category_map = {
            'epistemic_pattern': PatternCategory.EPISTEMIC,
            'metabolic_transition': PatternCategory.EFFICIENCY,
            'quality_characteristic': PatternCategory.QUALITY,
            'quality_trajectory': PatternCategory.SUCCESS
        }

        category = category_map.get(pattern_type, PatternCategory.SUCCESS)

        # Build characteristics using proper Web4 names via mappings
        characteristics = {}

        # Base characteristics
        characteristics['pattern_strength'] = pattern['strength']
        characteristics['pattern_frequency'] = pattern['frequency'] / sage_consolidated['cycles_processed']

        # Pattern-specific characteristics (using schema mappings)
        if 'epistemic' in pattern['description'].lower():
            if 'stable' in pattern['description'].lower():
                # Stable epistemic state
                # Map to: confidence_level → trust_score
                characteristics['confidence_level'] = 0.70
                characteristics['epistemic_breadth'] = 0.60  # Stable = moderate breadth
                characteristics['epistemic_coherence'] = 0.85  # Stable = high coherence

            elif 'confident' in pattern['description'].lower():
                # Confident epistemic state
                characteristics['confidence_level'] = 0.90
                characteristics['epistemic_breadth'] = 0.75  # Confident allows more breadth
                characteristics['epistemic_coherence'] = 0.80

        if 'wake' in pattern['description'].lower() or 'focus' in pattern['description'].lower():
            # Metabolic transitions
            characteristics['metabolic_stress'] = 0.50  # Moderate effort
            characteristics['learning_stability'] = 0.75  # Stable transitions

        if 'quality' in pattern['description'].lower():
            # Quality characteristics
            if 'numbers' in pattern['description'].lower():
                characteristics['context_richness'] = 0.85  # Numbers = rich context
                characteristics['epistemic_breadth'] = 0.80

            if 'unique' in pattern['description'].lower():
                characteristics['epistemic_breadth'] = 0.90  # Uniqueness = high diversity

            if 'hedging' in pattern['description'].lower():
                characteristics['confidence_level'] = 0.85  # Avoiding hedging = confident

        # Calculate quality correlation
        quality_correlation = 0.0
        if category == PatternCategory.QUALITY:
            quality_correlation = pattern['strength'] * 0.8
        elif category == PatternCategory.EPISTEMIC:
            quality_correlation = pattern['strength'] * 0.5
        elif category == PatternCategory.EFFICIENCY:
            quality_correlation = pattern['strength'] * 0.3

        universal = UniversalPattern(
            pattern_id=f"sage_s42_v2_pattern_{i}_{int(timestamp)}",
            source_domain=PatternDomain.CONSCIOUSNESS,
            category=category,
            description=f"SAGE S42: {pattern['description']}",
            characteristics=characteristics,
            frequency=pattern['frequency'],
            confidence=pattern['strength'],
            sample_size=sage_consolidated['cycles_processed'],
            quality_correlation=quality_correlation,
            extraction_timestamp=timestamp,
            first_observed=timestamp - 3600,
            last_observed=timestamp,
            source_metadata={
                'sage_session': 42,
                'pattern_type': pattern_type,
                'examples': pattern['examples']
            }
        )

        universal_patterns.append(universal)

    # Convert quality learnings (the most important!)
    for i, learning in enumerate(sage_consolidated['quality_learnings']):
        characteristics = {}

        # Quality delta from learning
        quality_delta = learning['average_quality_with'] - learning['average_quality_without']

        # Map 'has_numbers' characteristic
        if learning['characteristic'] == 'has_numbers':
            # Numbers improve quality by +31.2% in SAGE data
            # This maps to: context_richness → network_density
            characteristics['context_richness'] = 0.85  # High context when numbers present
            characteristics['epistemic_breadth'] = 0.80  # Numbers imply diverse thinking
            characteristics['confidence_level'] = 0.85   # Numbers imply confidence

        # Strong positive correlation for quality improvement
        quality_correlation = 0.0
        if learning['positive_correlation']:
            # Scale by actual quality delta
            quality_correlation = min(0.95, quality_delta * 2.0)
        else:
            quality_correlation = max(-0.95, quality_delta * 2.0)

        universal = UniversalPattern(
            pattern_id=f"sage_s42_v2_learning_{i}_{int(timestamp)}",
            source_domain=PatternDomain.CONSCIOUSNESS,
            category=PatternCategory.QUALITY,
            description=f"SAGE S42 Learning: {learning['characteristic']} {'improves' if learning['positive_correlation'] else 'degrades'} quality (Δ={quality_delta:+.3f})",
            characteristics=characteristics,
            frequency=learning['sample_size'],
            confidence=learning['confidence'],
            sample_size=learning['sample_size'],
            quality_correlation=quality_correlation,
            extraction_timestamp=timestamp,
            first_observed=timestamp - 3600,
            last_observed=timestamp,
            source_metadata={
                'sage_session': 42,
                'learning_type': 'quality_learning',
                'characteristic': learning['characteristic'],
                'quality_delta': quality_delta
            }
        )

        universal_patterns.append(universal)

    # Convert creative associations
    for i, assoc in enumerate(sage_consolidated['creative_associations']):
        characteristics = {}

        # Map association concepts
        if 'focus_state' in assoc['concept_a'] or 'focus_state' in assoc['concept_b']:
            characteristics['metabolic_stress'] = 0.60
            characteristics['learning_stability'] = 0.70

        if 'confident_epistemic' in assoc['concept_a'] or 'confident_epistemic' in assoc['concept_b']:
            characteristics['confidence_level'] = 0.90
            characteristics['epistemic_coherence'] = 0.85
            characteristics['epistemic_breadth'] = 0.75

        # Quality correlation from association type
        quality_correlation = 0.0
        if assoc['association_type'] == 'correlation':
            quality_correlation = assoc['strength'] * 0.7
        elif assoc['association_type'] == 'negative_correlation':
            quality_correlation = -assoc['strength'] * 0.7

        category = PatternCategory.EPISTEMIC if 'epistemic' in assoc['insight'].lower() else PatternCategory.EFFICIENCY

        universal = UniversalPattern(
            pattern_id=f"sage_s42_v2_assoc_{i}_{int(timestamp)}",
            source_domain=PatternDomain.CONSCIOUSNESS,
            category=category,
            description=f"SAGE S42 Association: {assoc['insight']}",
            characteristics=characteristics,
            frequency=len(assoc['supporting_cycles']),
            confidence=assoc['strength'],
            sample_size=sage_consolidated['cycles_processed'],
            quality_correlation=quality_correlation,
            extraction_timestamp=timestamp,
            first_observed=timestamp - 3600,
            last_observed=timestamp,
            source_metadata={
                'sage_session': 42,
                'association_type': assoc['association_type'],
                'concept_a': assoc['concept_a'],
                'concept_b': assoc['concept_b']
            }
        )

        universal_patterns.append(universal)

    return universal_patterns


def generate_test_coordination_history(num_cycles: int = 150) -> List[Dict]:
    """Generate coordination history matching Web4 context structure."""
    history = []

    for i in range(num_cycles):
        network_density = random.uniform(0.3, 0.95)
        trust_score = random.uniform(0.4, 0.95)
        diversity_score = random.uniform(0.2, 0.85)

        # Base quality
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


def test_v2_import():
    """Test V2 SAGE import with proper characteristic mapping."""
    print("=" * 80)
    print("TEST: Real SAGE Import V2 - Fixed Characteristic Mapping")
    print("=" * 80)
    print()

    # Load SAGE data
    print("Loading SAGE Session 42...")
    sage_consolidated = load_sage_session42_patterns()
    print(f"✓ {len(sage_consolidated['patterns'])} patterns, {len(sage_consolidated['quality_learnings'])} learnings")
    print()

    # Convert with V2 (proper mappings)
    print("Converting with V2 characteristic mapping...")
    universal_patterns = convert_sage_to_universal_v2(sage_consolidated)
    print(f"✓ {len(universal_patterns)} universal patterns")
    print()

    # Show key patterns
    print("Key Universal Patterns (V2):")
    for pattern in universal_patterns:
        if 'Learning' in pattern.description:
            print(f"  • {pattern.description}")
            print(f"    Characteristics: {list(pattern.characteristics.keys())}")
            print(f"    Quality correlation: {pattern.quality_correlation:+.3f}")
            print()

    # Export
    export_data = {
        'export_timestamp': time.time(),
        'source_domain': 'consciousness',
        'source_session': 'SAGE Session 42',
        'version': 2,
        'num_patterns': len(universal_patterns),
        'patterns': [p.to_dict() for p in universal_patterns]
    }

    export_path = Path('sage_s42_real_patterns_v2.json')
    with open(export_path, 'w') as f:
        json.dump(export_data, f, indent=2)

    print(f"✓ Exported to {export_path}")
    print()

    # Import to Web4
    print("Importing to Web4...")
    importer = UniversalToWeb4Converter()
    coord_patterns = importer.import_patterns(export_path)
    print(f"✓ {len(coord_patterns)} Web4 patterns")
    print()

    return coord_patterns


def test_v2_effectiveness():
    """Test effectiveness of V2 mapping."""
    print("=" * 80)
    print("TEST: V2 Effectiveness vs V1 vs Web4-only")
    print("=" * 80)
    print()

    # Generate test data
    print("Generating test coordination data...")
    test_history = generate_test_coordination_history(150)
    train_cycles = test_history[:100]
    test_cycles = test_history[100:]
    print(f"✓ Train: {len(train_cycles)}, Test: {len(test_cycles)}")
    print()

    # Baseline: Web4-only
    print("Baseline: Web4-only...")
    learner = CoordinationLearner()
    learnings_web4 = learner.extract_patterns(train_cycles)
    print(f"✓ {len(learnings_web4.patterns)} Web4 patterns")

    correct_web4 = 0
    for cycle in test_cycles:
        interaction = {'quality_estimate': cycle['quality']}
        context = {
            'network_density': cycle['network_density'],
            'avg_trust_score': cycle['avg_trust_score'],
            'diversity_score': cycle['diversity_score']
        }
        should_coord, conf, _ = learner.recommend(interaction, context, learnings_web4)
        if should_coord == cycle['coordination_succeeded']:
            correct_web4 += 1

    accuracy_web4 = correct_web4 / len(test_cycles)
    print(f"Web4-only: {correct_web4}/{len(test_cycles)} ({accuracy_web4:.1%})")
    print()

    # Enhanced: Web4 + SAGE V2
    print("Enhanced: Web4 + SAGE V2...")
    sage_consolidated = load_sage_session42_patterns()
    universal_patterns = convert_sage_to_universal_v2(sage_consolidated)

    importer = UniversalToWeb4Converter()
    sage_patterns = []
    for universal in universal_patterns:
        coord = importer.convert_to_coordination_pattern(universal)
        if coord:
            sage_patterns.append(coord)

    print(f"✓ {len(sage_patterns)} SAGE patterns")

    learnings_combined = learner.extract_patterns(train_cycles)
    learnings_combined.patterns.extend(sage_patterns)
    print(f"✓ {len(learnings_combined.patterns)} total patterns")
    print()

    correct_combined = 0
    for cycle in test_cycles:
        interaction = {'quality_estimate': cycle['quality']}
        context = {
            'network_density': cycle['network_density'],
            'avg_trust_score': cycle['avg_trust_score'],
            'diversity_score': cycle['diversity_score']
        }
        should_coord, conf, _ = learner.recommend(interaction, context, learnings_combined)
        if should_coord == cycle['coordination_succeeded']:
            correct_combined += 1

    accuracy_combined = correct_combined / len(test_cycles)
    print(f"Web4 + SAGE V2: {correct_combined}/{len(test_cycles)} ({accuracy_combined:.1%})")
    print()

    # Results
    improvement = (accuracy_combined - accuracy_web4) * 100
    print(f"Improvement: {improvement:+.1f}pp")
    print()

    if improvement > 0:
        print("✅ V2 mapping improved predictions!")
    elif improvement == 0:
        print("⚠️  No change from baseline")
    else:
        print("⚠️  Still seeing decrease")

    return {
        'web4_only': accuracy_web4,
        'web4_sage_v2': accuracy_combined,
        'improvement': improvement
    }


def run_v2_tests():
    """Run V2 test suite."""
    print("=" * 80)
    print("Real SAGE Import V2 - Fixed Characteristic Mapping")
    print("=" * 80)
    print()

    start = time.time()

    patterns = test_v2_import()
    print("\n\n")

    results = test_v2_effectiveness()
    print("\n\n")

    print("=" * 80)
    print("V2 SUMMARY")
    print("=" * 80)
    print()

    print(f"Patterns imported: {len(patterns)}")
    print(f"Web4-only accuracy: {results['web4_only']:.1%}")
    print(f"Web4 + SAGE V2 accuracy: {results['web4_sage_v2']:.1%}")
    print(f"Improvement: {results['improvement']:+.1f}pp")
    print()

    if results['improvement'] > 0:
        print("✅ Fixed characteristic mapping works!")
    else:
        print("⚠️  Further investigation needed")

    print()
    print(f"Completed in {time.time() - start:.1f}s")
    print()


if __name__ == "__main__":
    run_v2_tests()
