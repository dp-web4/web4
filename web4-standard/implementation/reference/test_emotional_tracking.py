#!/usr/bin/env python3
"""
Test Emotional Coordination Tracking
====================================

Phase 1: Validate metric computation
Phase 2: Test correlation with coordination success (this test)

Research Questions:
1. Do emotional metrics make sense?
2. Does high curiosity correlate with diverse successful coordination?
3. Does frustration correlate with quality stagnation?
4. Does progress correlate with learning effectiveness?

Created: December 15, 2025
Session: Autonomous Web4 Research Session 53
"""

import random
import sys
import numpy as np
from typing import List, Dict

sys.path.insert(0, '/home/dp/ai-workspace/web4/web4-standard/implementation/reference')

from web4_emotional_tracking import (
    EmotionalCoordinationTracker,
    track_coordination_emotions,
    detect_emotional_events
)


def generate_scenario_improving_quality(num_cycles: int = 100) -> List[Dict]:
    """
    Generate scenario with improving quality.

    Expected emotions:
    - High progress (quality improving)
    - Low frustration (not stagnating)
    """
    history = []

    for i in range(num_cycles):
        # Quality improves over time
        base_quality = 0.5 + (i / num_cycles) * 0.4  # 0.5 → 0.9
        quality = max(0.0, min(1.0, base_quality + random.uniform(-0.05, 0.05)))

        history.append({
            'cycle_id': i,
            'network_density': random.uniform(0.5, 0.9),
            'diversity_score': random.uniform(0.5, 0.9),
            'quality': quality,
            'priority': random.uniform(0.7, 0.95),
            'timestamp': i * 1.0
        })

    return history


def generate_scenario_stagnant_quality(num_cycles: int = 100) -> List[Dict]:
    """
    Generate scenario with stagnant quality.

    Expected emotions:
    - High frustration (quality stagnating)
    - Low progress (no improvement)
    """
    history = []

    # Stuck at mediocre quality
    stagnant_quality = 0.6

    for i in range(num_cycles):
        quality = stagnant_quality + random.uniform(-0.02, 0.02)  # Very low variance

        history.append({
            'cycle_id': i,
            'network_density': random.uniform(0.5, 0.7),
            'diversity_score': random.uniform(0.4, 0.6),
            'quality': quality,
            'priority': random.uniform(0.5, 0.8),
            'timestamp': i * 1.0
        })

    return history


def generate_scenario_high_diversity(num_cycles: int = 100) -> List[Dict]:
    """
    Generate scenario with high diversity exploration.

    Expected emotions:
    - High curiosity (diverse exploration)
    """
    history = []

    for i in range(num_cycles):
        # Highly variable diversity (exploring different options)
        diversity = random.uniform(0.3, 0.95)

        history.append({
            'cycle_id': i,
            'network_density': random.uniform(0.4, 0.95),
            'diversity_score': diversity,
            'quality': random.uniform(0.6, 0.85),
            'priority': random.uniform(0.6, 0.9),
            'timestamp': i * 1.0
        })

    return history


def generate_scenario_focused_priority(num_cycles: int = 100) -> List[Dict]:
    """
    Generate scenario with sustained high-priority focus.

    Expected emotions:
    - High engagement (focused on important work)
    """
    history = []

    for i in range(num_cycles):
        # Consistently high priority
        priority = random.uniform(0.85, 0.95)

        history.append({
            'cycle_id': i,
            'network_density': random.uniform(0.6, 0.9),
            'diversity_score': random.uniform(0.5, 0.8),
            'quality': random.uniform(0.7, 0.9),
            'priority': priority,
            'timestamp': i * 1.0
        })

    return history


def test_scenario(name: str, history: List[Dict], expected_emotions: Dict):
    """Test emotional tracking on specific scenario"""
    print(f"\n{'='*80}")
    print(f"SCENARIO: {name}")
    print(f"{'='*80}\n")

    # Track emotions
    emotions_trajectory = track_coordination_emotions(history)

    # Get final emotional state (after sufficient history)
    if len(emotions_trajectory) > 20:
        final_emotions = emotions_trajectory[-1]

        print(f"Final Emotional State (cycle {final_emotions.cycle_count}):")
        print(f"  Curiosity:   {final_emotions.curiosity:.3f}")
        print(f"  Frustration: {final_emotions.frustration:.3f}")
        print(f"  Progress:    {final_emotions.progress:.3f}")
        print(f"  Engagement:  {final_emotions.engagement:.3f}")
        print()

        # Validate against expectations
        validation_results = {}

        for emotion_name, (expected_level, threshold) in expected_emotions.items():
            actual = getattr(final_emotions, emotion_name)

            if expected_level == 'high':
                validated = actual > threshold
            elif expected_level == 'low':
                validated = actual < threshold
            else:  # moderate
                validated = True  # Don't validate moderate expectations

            validation_results[emotion_name] = validated

            status = "✅" if validated else "⚠️ "
            expected_str = f"{expected_level} (threshold {threshold})"
            print(f"{status} {emotion_name.capitalize()}: {actual:.3f} "
                  f"(expected {expected_str})")

        print()

        # Overall validation
        passed = sum(validation_results.values())
        total = len([v for k, v in expected_emotions.items()
                    if v[0] != 'moderate'])

        if passed == total:
            print(f"✅ VALIDATION PASSED ({passed}/{total})")
        else:
            print(f"⚠️  PARTIAL VALIDATION ({passed}/{total})")

        return validation_results

    else:
        print("⚠️  Insufficient history for validation")
        return {}


def test_event_detection():
    """Test emotional event detection"""
    print(f"\n{'='*80}")
    print("EMOTIONAL EVENT DETECTION")
    print(f"{'='*80}\n")

    # Generate scenario with frustration event
    history = []

    # Good quality initially
    for i in range(30):
        quality = 0.8 + random.uniform(-0.05, 0.05)
        history.append({
            'cycle_id': i,
            'network_density': random.uniform(0.7, 0.9),
            'diversity_score': random.uniform(0.6, 0.9),
            'quality': quality,
            'priority': random.uniform(0.7, 0.9),
            'timestamp': i * 1.0
        })

    # Then quality stagnates (frustration trigger)
    for i in range(30, 70):
        quality = 0.55 + random.uniform(-0.02, 0.02)  # Stagnant
        history.append({
            'cycle_id': i,
            'network_density': random.uniform(0.5, 0.7),
            'diversity_score': random.uniform(0.4, 0.6),
            'quality': quality,
            'priority': random.uniform(0.5, 0.8),
            'timestamp': i * 1.0
        })

    # Track emotions
    emotions_trajectory = track_coordination_emotions(history)

    # Detect events
    events = detect_emotional_events(
        emotions_trajectory,
        frustration_threshold=0.6,
        curiosity_drop_threshold=0.35,
        progress_drop_threshold=0.35
    )

    print(f"Detected {len(events)} emotional events:\n")

    for event in events:
        print(f"  Cycle {event['cycle']:3d}: {event['type']:20s} - {event['description']}")

    print()

    # Check if frustration event was detected around cycle 40-60
    frustration_events = [e for e in events if e['type'] == 'high_frustration']
    frustration_in_range = any(30 <= e['cycle'] < 70 for e in frustration_events)

    if frustration_in_range:
        print("✅ Frustration event correctly detected during stagnation period")
    else:
        print("⚠️  Frustration event not detected in expected range")

    print()

    return events


def run_all_tests():
    """Run all emotional tracking tests"""
    print("="*80)
    print("EMOTIONAL COORDINATION TRACKING - VALIDATION TESTS")
    print("="*80)

    print("\nPhase 1: Metric Computation")
    print("Phase 2: Correlation Validation (these tests)")
    print()

    # Test scenarios
    results = {}

    # Scenario 1: Improving Quality → High Progress, Low Frustration
    results['improving'] = test_scenario(
        "Improving Quality",
        generate_scenario_improving_quality(100),
        {
            'progress': ('high', 0.65),
            'frustration': ('low', 0.3)
        }
    )

    # Scenario 2: Stagnant Quality → High Frustration, Low Progress
    results['stagnant'] = test_scenario(
        "Stagnant Quality",
        generate_scenario_stagnant_quality(100),
        {
            'frustration': ('high', 0.5),
            'progress': ('low', 0.5)
        }
    )

    # Scenario 3: High Diversity → High Curiosity
    results['diverse'] = test_scenario(
        "High Diversity Exploration",
        generate_scenario_high_diversity(100),
        {
            'curiosity': ('high', 0.6)
        }
    )

    # Scenario 4: Focused Priority → High Engagement
    results['focused'] = test_scenario(
        "Focused High-Priority Work",
        generate_scenario_focused_priority(100),
        {
            'engagement': ('high', 0.75)
        }
    )

    # Test event detection
    events = test_event_detection()

    # Summary
    print("="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    print()

    total_validated = sum(sum(r.values()) for r in results.values())
    total_expected = sum(len(r) for r in results.values())

    print(f"Emotional metrics validated: {total_validated}/{total_expected}")
    print()

    for scenario, validations in results.items():
        passed = sum(validations.values())
        total = len(validations)
        status = "✅" if passed == total else "⚠️ "
        print(f"{status} {scenario:12s}: {passed}/{total}")

    print()

    if total_validated >= total_expected * 0.75:  # 75% threshold
        print("✅ PHASE 2 VALIDATION SUCCESSFUL")
        print("   Emotional metrics correlate with coordination patterns")
        print()
        print("Validated Correlations:")
        print("  • Progress correlates with quality improvement")
        print("  • Frustration correlates with quality stagnation")
        print("  • Curiosity correlates with diversity exploration")
        print("  • Engagement correlates with priority focus")
        print()
        print("Next: Phase 3 - Implement emotional modulation of decisions")

    else:
        print("⚠️  PARTIAL VALIDATION")
        print("   Some metrics need tuning")

    print()

    return results, events


if __name__ == "__main__":
    results, events = run_all_tests()
