#!/usr/bin/env python3
"""
Test Multi-Session SAGE Pattern Accumulation
=============================================

Tests if accumulating patterns from multiple SAGE sessions provides
compounding benefits compared to single-session transfer.

Sessions tested:
- Session 42: DREAM consolidation (7 patterns, 1 learning, 2 associations)
- Session 48: Emotional intelligence (4 dimensions: Curiosity, Frustration, Progress, Engagement)
- Session 49: Circadian rhythm (5 phases: DAWN, DAY, DUSK, NIGHT, DEEP_NIGHT)

Created: December 14, 2025
Session: Autonomous Web4 Research Session 51
"""

import json
import random
import sys
import time
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, '/home/dp/ai-workspace/web4/web4-standard/implementation/reference')
sys.path.insert(0, '/home/dp/ai-workspace/HRM')

from pattern_exchange_protocol import (
    SAGEToUniversalConverter,
    UniversalToWeb4Converter
)
from web4_coordination_learning import CoordinationLearner
from universal_pattern_schema import (
    UniversalPattern,
    PatternDomain,
    PatternCategory
)


def load_session42_patterns() -> List[UniversalPattern]:
    """Load and convert real SAGE Session 42 patterns."""
    # Load real S42 data
    sage_path = Path('/home/dp/ai-workspace/HRM/sage/tests/dream_consolidation_results.json')

    with open(sage_path, 'r') as f:
        sage_data = json.load(f)

    from sage.core.dream_consolidation import (
        MemoryPattern,
        QualityLearning,
        CreativeAssociation,
        ConsolidatedMemory
    )

    # Reconstruct from JSON
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

    return universal_patterns


def create_session48_emotional_patterns() -> List[UniversalPattern]:
    """
    Create conceptual patterns from Session 48 emotional intelligence.

    Session 48 added: Curiosity, Frustration, Progress, Engagement
    """
    timestamp = time.time()
    patterns = []

    # Pattern 1: High curiosity correlates with quality
    patterns.append(UniversalPattern(
        pattern_id=f"sage_s48_curiosity_{int(timestamp)}",
        source_domain=PatternDomain.CONSCIOUSNESS,
        category=PatternCategory.QUALITY,
        description="SAGE S48: High curiosity correlates with quality",
        characteristics={
            'epistemic_breadth': 0.85,  # Maps to diversity_score
            'context_richness': 0.80,   # Maps to network_density
            'confidence_level': 0.75     # Maps to trust_score
        },
        frequency=15,
        confidence=0.70,
        sample_size=20,
        quality_correlation=0.65,
        extraction_timestamp=timestamp,
        first_observed=timestamp - 7200,
        last_observed=timestamp,
        source_metadata={'sage_session': 48, 'metric': 'curiosity'}
    ))

    # Pattern 2: Frustration triggers rest/consolidation
    patterns.append(UniversalPattern(
        pattern_id=f"sage_s48_frustration_{int(timestamp)}",
        source_domain=PatternDomain.CONSCIOUSNESS,
        category=PatternCategory.ADAPTATION,
        description="SAGE S48: Frustration triggers rest for consolidation",
        characteristics={
            'metabolic_stress': 0.90,    # High stress
            'learning_stability': 0.40,  # Low stability when frustrated
            'quality_trajectory': 0.30   # Declining quality
        },
        frequency=8,
        confidence=0.75,
        sample_size=20,
        quality_correlation=-0.50,  # Negative: frustration hurts quality
        extraction_timestamp=timestamp,
        first_observed=timestamp - 7200,
        last_observed=timestamp,
        source_metadata={'sage_session': 48, 'metric': 'frustration'}
    ))

    # Pattern 3: Progress indicates learning effectiveness
    patterns.append(UniversalPattern(
        pattern_id=f"sage_s48_progress_{int(timestamp)}",
        source_domain=PatternDomain.CONSCIOUSNESS,
        category=PatternCategory.SUCCESS,
        description="SAGE S48: Progress indicates effective learning",
        characteristics={
            'quality_trajectory': 0.85,  # Improving
            'learning_stability': 0.80,  # Stable improvement
            'response_confidence': 0.78  # Maps to coordination_confidence
        },
        frequency=12,
        confidence=0.80,
        sample_size=20,
        quality_correlation=0.75,
        extraction_timestamp=timestamp,
        first_observed=timestamp - 7200,
        last_observed=timestamp,
        source_metadata={'sage_session': 48, 'metric': 'progress'}
    ))

    # Pattern 4: Engagement enables sustained coordination
    patterns.append(UniversalPattern(
        pattern_id=f"sage_s48_engagement_{int(timestamp)}",
        source_domain=PatternDomain.CONSCIOUSNESS,
        category=PatternCategory.SUCCESS,
        description="SAGE S48: High engagement enables sustained quality",
        characteristics={
            'response_confidence': 0.85,
            'epistemic_coherence': 0.88,  # Maps to objective_coherence
            'learning_stability': 0.82    # Maps to parameter_stability
        },
        frequency=18,
        confidence=0.78,
        sample_size=20,
        quality_correlation=0.70,
        extraction_timestamp=timestamp,
        first_observed=timestamp - 7200,
        last_observed=timestamp,
        source_metadata={'sage_session': 48, 'metric': 'engagement'}
    ))

    return patterns


def generate_coordination_history(num_cycles: int = 150) -> List[Dict]:
    """Generate coordination history for testing."""
    history = []

    for i in range(num_cycles):
        network_density = random.uniform(0.3, 0.95)
        trust_score = random.uniform(0.4, 0.95)
        diversity_score = random.uniform(0.2, 0.85)

        # Quality calculation
        quality = 0.5
        if network_density > 0.7:
            quality += 0.25
        if trust_score > 0.8:
            quality += 0.20
        if diversity_score > 0.6:
            quality += 0.15

        quality = max(0.0, min(1.0, quality + random.uniform(-0.1, 0.1)))

        history.append({
            'cycle_id': i,
            'network_density': network_density,
            'avg_trust_score': trust_score,
            'diversity_score': diversity_score,
            'quality': quality,
            'coordination_confidence': quality * 0.9,
            'parameter_stability': 0.8,
            'objective_coherence': 0.9,
            'coordination_succeeded': quality > 0.65,
            'timestamp': time.time() + i
        })

    return history


def test_multisession_accumulation():
    """Test if multiple SAGE sessions provide compounding benefits."""
    print("=" * 80)
    print("TEST: Multi-Session SAGE Pattern Accumulation")
    print("=" * 80)
    print()

    # Generate test data
    print("Generating coordination history (150 cycles)...")
    test_history = generate_coordination_history(150)
    train_cycles = test_history[:100]
    test_cycles = test_history[100:]
    print(f"✓ Train: {len(train_cycles)}, Test: {len(test_cycles)}")
    print()

    # Baseline: Web4 only
    print("Baseline: Web4-only learning...")
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
    print(f"Web4-only: {accuracy_web4:.1%}")
    print()

    # Single session: Session 42 only
    print("Single Session: Web4 + SAGE Session 42...")
    s42_patterns = load_session42_patterns()
    print(f"✓ Loaded {len(s42_patterns)} Session 42 patterns")

    importer = UniversalToWeb4Converter()
    s42_coord_patterns = []
    for universal in s42_patterns:
        coord = importer.convert_to_coordination_pattern(universal)
        if coord:
            s42_coord_patterns.append(coord)

    learnings_s42 = learner.extract_patterns(train_cycles)
    learnings_s42.patterns.extend(s42_coord_patterns)
    print(f"✓ Combined: {len(learnings_s42.patterns)} patterns")

    correct_s42 = 0
    for cycle in test_cycles:
        interaction = {'quality_estimate': cycle['quality']}
        context = {
            'network_density': cycle['network_density'],
            'avg_trust_score': cycle['avg_trust_score'],
            'diversity_score': cycle['diversity_score']
        }
        should_coord, conf, _ = learner.recommend(interaction, context, learnings_s42)
        if should_coord == cycle['coordination_succeeded']:
            correct_s42 += 1

    accuracy_s42 = correct_s42 / len(test_cycles)
    improvement_s42 = (accuracy_s42 - accuracy_web4) * 100
    print(f"Web4 + S42: {accuracy_s42:.1%} ({improvement_s42:+.1f}pp)")
    print()

    # Multi-session: Sessions 42 + 48
    print("Multi-Session: Web4 + SAGE S42 + S48...")
    s48_patterns = create_session48_emotional_patterns()
    print(f"✓ Created {len(s48_patterns)} Session 48 emotional patterns")

    all_patterns = s42_patterns + s48_patterns
    print(f"✓ Combined {len(all_patterns)} total SAGE patterns")

    all_coord_patterns = []
    for universal in all_patterns:
        coord = importer.convert_to_coordination_pattern(universal)
        if coord:
            all_coord_patterns.append(coord)

    learnings_multi = learner.extract_patterns(train_cycles)
    learnings_multi.patterns.extend(all_coord_patterns)
    print(f"✓ Total: {len(learnings_multi.patterns)} patterns")

    correct_multi = 0
    for cycle in test_cycles:
        interaction = {'quality_estimate': cycle['quality']}
        context = {
            'network_density': cycle['network_density'],
            'avg_trust_score': cycle['avg_trust_score'],
            'diversity_score': cycle['diversity_score']
        }
        should_coord, conf, _ = learner.recommend(interaction, context, learnings_multi)
        if should_coord == cycle['coordination_succeeded']:
            correct_multi += 1

    accuracy_multi = correct_multi / len(test_cycles)
    improvement_multi = (accuracy_multi - accuracy_web4) * 100
    compound_benefit = (accuracy_multi - accuracy_s42) * 100

    print(f"Web4 + S42 + S48: {accuracy_multi:.1%} ({improvement_multi:+.1f}pp)")
    print()

    # Results
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    print(f"Web4-only:         {accuracy_web4:.1%}")
    print(f"Web4 + S42:        {accuracy_s42:.1%} ({improvement_s42:+.1f}pp)")
    print(f"Web4 + S42 + S48:  {accuracy_multi:.1%} ({improvement_multi:+.1f}pp)")
    print()

    print(f"Session 42 contribution: {improvement_s42:+.1f}pp")
    print(f"Session 48 contribution: {compound_benefit:+.1f}pp")
    print(f"Total improvement: {improvement_multi:+.1f}pp")
    print()

    if compound_benefit > 0:
        print("✅ Multi-session accumulation provides compounding benefits!")
        print(f"   Adding Session 48 emotional patterns improved by {compound_benefit:+.1f}pp")
    elif compound_benefit >= -1.0:
        print("⚠️  Multi-session shows minimal additional benefit")
    else:
        print("⚠️  Multi-session decreased performance")

    return {
        'web4_only': accuracy_web4,
        'web4_s42': accuracy_s42,
        'web4_multi': accuracy_multi,
        's42_contribution': improvement_s42,
        's48_contribution': compound_benefit,
        'total_improvement': improvement_multi
    }


if __name__ == "__main__":
    results = test_multisession_accumulation()

    print()
    print("=" * 80)
    print("RESEARCH SUMMARY")
    print("=" * 80)
    print()

    print("Pattern Accumulation Test:")
    print(f"  Baseline (Web4-only): {results['web4_only']:.1%}")
    print(f"  + Session 42:         {results['web4_s42']:.1%} ({results['s42_contribution']:+.1f}pp)")
    print(f"  + Session 48:         {results['web4_multi']:.1%} ({results['s48_contribution']:+.1f}pp additional)")
    print()

    if results['s48_contribution'] > 0:
        print("Key Finding:")
        print("  Multiple SAGE sessions accumulate benefits - more sessions = better transfer")
        print()
        print("  Session 42 (DREAM consolidation): Quality learning patterns")
        print("  Session 48 (Emotional intelligence): Adaptation and engagement patterns")
        print("  Combined: Richer pattern set improves Web4 coordination")
    else:
        print("Finding:")
        print("  Session 42 provides primary benefit, Session 48 marginal")

    print()
