#!/usr/bin/env python3
"""
Test Phase-Tagged Pattern Extraction
====================================

Validates that phase-tagged learner can extract explicit patterns
that match the implicit learning observed in Session 52.

Session 52 Finding:
"Implicit learning works (all 4 phase-specific patterns detected),
but 0 explicit patterns extracted."

This test validates that phase-tagged extraction produces explicit
patterns matching the implicit behavioral patterns.

Created: December 15, 2025
Session: Autonomous Web4 Research Session 53
"""

import random
import sys
from pathlib import Path

sys.path.insert(0, '/home/dp/ai-workspace/web4/web4-standard/implementation/reference')
sys.path.insert(0, '/home/dp/ai-workspace/HRM')

from web4_phase_tagged_learning import PhaseTaggedLearner, PhaseTaggedLearnings
from sage.core.circadian_clock import CircadianPhase


def generate_phase_dependent_history(num_cycles: int = 1000):
    """
    Generate history with embedded phase-specific patterns.

    Same pattern as Session 52 test_phase_specific_learning.py:
    - DAY: High density (0.7-0.95), high diversity (0.7-0.95)
    - NIGHT: Low density (0.3-0.5), high trust (0.85-0.95)
    """
    history = []

    circadian_period = 100

    for i in range(num_cycles):
        # Determine phase
        cycle_in_period = i % circadian_period
        phase_progress = cycle_in_period / circadian_period

        if phase_progress < 0.10:
            phase = 'dawn'
        elif phase_progress < 0.50:
            phase = 'day'
        elif phase_progress < 0.60:
            phase = 'dusk'
        elif phase_progress < 0.90:
            phase = 'night'
        else:
            phase = 'deep_night'

        # Generate with phase-specific success patterns
        if phase in ['day', 'dawn', 'dusk']:
            # DAY pattern: High density, high diversity → SUCCESS
            if random.random() < 0.5:
                network_density = random.uniform(0.7, 0.95)
                trust_score = random.uniform(0.6, 0.85)
                diversity_score = random.uniform(0.7, 0.95)
                quality = 0.85 + random.uniform(-0.05, 0.10)
            else:
                network_density = random.uniform(0.3, 0.95)
                trust_score = random.uniform(0.4, 0.95)
                diversity_score = random.uniform(0.3, 0.95)
                quality = 0.55 + random.uniform(-0.15, 0.25)

        else:  # night, deep_night
            # NIGHT pattern: Low density, high trust → SUCCESS
            if random.random() < 0.5:
                network_density = random.uniform(0.3, 0.5)
                trust_score = random.uniform(0.85, 0.95)
                diversity_score = random.uniform(0.3, 0.5)
                quality = 0.80 + random.uniform(-0.05, 0.10)
            else:
                network_density = random.uniform(0.3, 0.95)
                trust_score = random.uniform(0.4, 0.95)
                diversity_score = random.uniform(0.3, 0.95)
                quality = 0.55 + random.uniform(-0.15, 0.25)

        quality = max(0.0, min(1.0, quality))

        history.append({
            'cycle_id': i,
            'circadian_phase': phase,
            'network_density': network_density,
            'trust_score': trust_score,
            'avg_trust_score': trust_score,
            'diversity_score': diversity_score,
            'quality': quality,
            'priority': random.uniform(0.6, 0.9),
            'coordination_succeeded': quality > 0.7
        })

    return history


def test_phase_tagged_extraction():
    """Test phase-tagged pattern extraction"""
    print("=" * 80)
    print("TEST: Phase-Tagged Pattern Extraction")
    print("=" * 80)
    print()

    print("Generating 1000-cycle history with phase-specific patterns...")
    history = generate_phase_dependent_history(1000)
    print(f"✓ Generated {len(history)} cycles")
    print()

    # Count cycles by phase
    from collections import Counter
    phase_counts = Counter(c['circadian_phase'] for c in history)
    print("Phase distribution:")
    for phase, count in sorted(phase_counts.items()):
        print(f"  {phase:10s}: {count:3d} cycles ({count/len(history)*100:.1f}%)")
    print()

    # Initialize phase-tagged learner
    print("Initializing PhaseTaggedLearner...")
    learner = PhaseTaggedLearner(
        min_pattern_frequency=5,  # At least 5 occurrences
        min_confidence=0.5,        # 50% confidence minimum
        min_phase_samples=10       # At least 10 samples per phase
    )
    print("✓ Learner initialized")
    print()

    # Extract patterns
    print("Extracting phase-tagged patterns...")
    learnings = learner.extract_phase_patterns(history)
    print("✓ Pattern extraction complete")
    print()

    # Analyze results
    print("=" * 80)
    print("PATTERN EXTRACTION RESULTS")
    print("=" * 80)
    print()

    print(f"Base patterns extracted: {len(learnings.patterns)}")
    print(f"Phase-tagged patterns extracted: {len(learnings.phase_patterns)}")
    print()

    if learnings.phase_patterns:
        print("Phase-Tagged Patterns:")
        print()

        for i, pattern in enumerate(learnings.phase_patterns, 1):
            print(f"{i}. {pattern.description}")
            print(f"   Type: {pattern.pattern_type}")
            print(f"   Applicable phases: {', '.join(pattern.applicable_phases)}")
            print(f"   Overall confidence: {pattern.confidence:.3f}")
            print(f"   Overall quality: {pattern.average_quality:.3f}")
            print(f"   Frequency: {pattern.frequency}")
            print()

            if pattern.characteristics:
                print("   Characteristics:")
                for char, value in pattern.characteristics.items():
                    if isinstance(value, float):
                        print(f"     {char}: {value:.3f}")
                    else:
                        print(f"     {char}: {value}")
                print()

            if pattern.phase_quality:
                print("   Phase-Specific Quality:")
                for phase, quality in pattern.phase_quality.items():
                    conf = pattern.phase_confidence.get(phase, 0.0)
                    freq = pattern.phase_frequency.get(phase, 0)
                    print(f"     {phase:10s}: quality={quality:.3f}, "
                          f"confidence={conf:.3f}, freq={freq}")
                print()

    else:
        print("⚠️  No phase-tagged patterns extracted")
        print()

    # Test phase-specific retrieval
    print("=" * 80)
    print("PHASE-SPECIFIC PATTERN RETRIEVAL")
    print("=" * 80)
    print()

    for phase in ['day', 'night']:
        patterns = learnings.get_patterns_for_phase(phase, min_confidence=0.4)
        print(f"{phase.upper()} patterns (min_confidence=0.4): {len(patterns)}")

        if patterns:
            for pattern in patterns:
                quality = pattern.get_phase_quality(phase)
                print(f"  • {pattern.description}: quality={quality:.3f}")
        else:
            print("  (none)")

        print()

    # Validate against Session 52 implicit learning
    print("=" * 80)
    print("VALIDATION AGAINST SESSION 52 IMPLICIT LEARNING")
    print("=" * 80)
    print()

    print("Session 52 Implicit Learning Results:")
    print("  DAY: density=0.751, diversity=0.760 (high complexity)")
    print("  NIGHT: density=0.448, trust=0.860 (high trust, simple)")
    print()

    # Check if extracted patterns match implicit learning
    day_patterns = learnings.get_patterns_for_phase('day', min_confidence=0.3)
    night_patterns = learnings.get_patterns_for_phase('night', min_confidence=0.3)

    validation_results = {
        'day_high_density': False,
        'day_high_diversity': False,
        'night_low_density': False,
        'night_high_trust': False
    }

    # Check DAY patterns
    for pattern in day_patterns:
        chars = pattern.characteristics
        if chars.get('avg_network_density', 0) > 0.7:
            validation_results['day_high_density'] = True
        if chars.get('avg_diversity', 0) > 0.7:
            validation_results['day_high_diversity'] = True

    # Check NIGHT patterns
    for pattern in night_patterns:
        chars = pattern.characteristics
        if chars.get('avg_network_density', 1.0) < 0.5:
            validation_results['night_low_density'] = True
        if chars.get('avg_trust', 0) > 0.85:
            validation_results['night_high_trust'] = True

    print("Explicit Pattern Validation:")
    if validation_results['day_high_density']:
        print("✅ DAY: High network density pattern extracted")
    else:
        print("⚠️  DAY: High density pattern not found")

    if validation_results['day_high_diversity']:
        print("✅ DAY: High diversity pattern extracted")
    else:
        print("⚠️  DAY: High diversity pattern not found")

    if validation_results['night_high_trust']:
        print("✅ NIGHT: High trust pattern extracted")
    else:
        print("⚠️  NIGHT: High trust pattern not found")

    if validation_results['night_low_density']:
        print("✅ NIGHT: Low density pattern extracted")
    else:
        print("⚠️  NIGHT: Low density pattern not found")

    print()

    patterns_found = sum(validation_results.values())

    if patterns_found == 4:
        print("✅ ALL 4 IMPLICIT PATTERNS MATCHED BY EXPLICIT EXTRACTION")
        print("   Session 52 implicit learning now captured as explicit patterns!")
    elif patterns_found >= 2:
        print(f"⚠️  PARTIAL MATCH: {patterns_found}/4 patterns extracted")
        print("   Some implicit patterns captured explicitly")
    else:
        print("⚠️  FEW PATTERNS EXTRACTED")
        print("   Explicit extraction not matching implicit learning")

    print()

    return {
        'patterns_extracted': len(learnings.phase_patterns),
        'validation_score': patterns_found,
        'learnings': learnings
    }


if __name__ == "__main__":
    results = test_phase_tagged_extraction()

    print("=" * 80)
    print("RESEARCH SUMMARY")
    print("=" * 80)
    print()

    print("Research Question: Can explicit phase-tagged extraction match")
    print("                   implicit learning from Session 52?")
    print()

    print(f"Phase-tagged patterns extracted: {results['patterns_extracted']}")
    print(f"Implicit patterns matched: {results['validation_score']}/4")
    print()

    if results['validation_score'] >= 3:
        print("✅ SUCCESS: Explicit extraction captures implicit learning")
        print()
        print("Impact:")
        print("  • Implicit learning (behavioral) now formalized as explicit patterns")
        print("  • Patterns are portable (can export via pattern exchange protocol)")
        print("  • Patterns are inspectable (can debug why coordination happens)")
        print("  • Patterns are phase-aware (know when to apply each pattern)")
        print()
        print("Next: Test pattern export/import for cross-domain transfer")

    else:
        print("⚠️  Partial success - some tuning needed")
        print()
        print("Possible improvements:")
        print("  • Adjust min_confidence threshold")
        print("  • Adjust min_frequency threshold")
        print("  • Increase min_phase_samples")
        print("  • Generate more test data")

    print()
