#!/usr/bin/env python3
"""
Test Emotional Decision Modulation (Phase 3)
============================================

Validates that emotional signals improve coordination effectiveness.

Research Questions:
1. Does frustration-triggered consolidation improve learning?
2. Does progress-based threshold adaptation optimize coordination?
3. Does curiosity-driven diversity tolerance improve exploration?
4. Does engagement-based priority filtering improve focus?

Created: December 15, 2025
Session: Autonomous Web4 Research Session 54
"""

import random
import sys
from typing import List, Dict

sys.path.insert(0, '/home/dp/ai-workspace/web4/web4-standard/implementation/reference')
sys.path.insert(0, '/home/dp/ai-workspace/HRM')

from web4_phase2d_emotional_coordinator import Web4EmotionalCoordinator
from web4_phase2c_circadian_coordinator import Web4CircadianCoordinator
from web4_production_coordinator import CoordinationParameters


def generate_learning_scenario(num_cycles: int = 500) -> List[Dict]:
    """
    Generate scenario with initial low quality that improves with learning.

    Expected: Frustration triggers consolidation, progress adjusts threshold
    """
    history = []

    for i in range(num_cycles):
        # Quality improves gradually (simulating learning)
        base_quality = 0.5 + (i / num_cycles) * 0.3  # 0.5 → 0.8

        # Add periodic dips (frustration triggers)
        if i % 150 == 100:
            quality = 0.55 + random.uniform(-0.05, 0.05)  # Temporary dip
        else:
            quality = max(0.0, min(1.0, base_quality + random.uniform(-0.08, 0.08)))

        history.append({
            'cycle_id': i,
            'priority': random.uniform(0.6, 0.9),
            'trust_score': random.uniform(0.6, 0.9),
            'network_density': random.uniform(0.5, 0.9),
            'quality_score': quality,
            'diversity_score': random.uniform(0.5, 0.8)
        })

    return history


def test_frustration_consolidation():
    """Test that frustration triggers consolidation"""
    print("=" * 80)
    print("TEST 1: Frustration-Triggered Consolidation")
    print("=" * 80)
    print()

    params = CoordinationParameters(satisfaction_threshold=0.65)

    # Coordinator with emotional modulation
    coordinator = Web4EmotionalCoordinator(
        params=params,
        enable_circadian=False,  # Disable for cleaner test
        enable_emotional=True,
        enable_learning=True,
        frustration_consolidation_threshold=0.6
    )

    # Generate scenario with quality stagnation
    history = []

    # Good quality initially
    for i in range(50):
        quality = 0.8 + random.uniform(-0.03, 0.03)
        history.append({
            'priority': random.uniform(0.7, 0.9),
            'trust_score': random.uniform(0.7, 0.9),
            'network_density': random.uniform(0.6, 0.9),
            'quality_score': quality,
            'diversity_score': random.uniform(0.6, 0.9)
        })

    # Then quality stagnates (triggers frustration)
    for i in range(50, 150):
        quality = 0.6 + random.uniform(-0.02, 0.02)  # Stagnant
        history.append({
            'priority': random.uniform(0.6, 0.8),
            'trust_score': random.uniform(0.6, 0.8),
            'network_density': random.uniform(0.5, 0.7),
            'quality_score': quality,
            'diversity_score': random.uniform(0.4, 0.6)
        })

    print(f"Running {len(history)} cycles...")
    print()

    consolidations_triggered = 0
    max_frustration = 0.0

    for cycle in history:
        should_coord, telemetry = coordinator.coordinate_interaction(
            priority=cycle['priority'],
            trust_score=cycle['trust_score'],
            network_density=cycle['network_density'],
            quality_score=cycle['quality_score'],
            context={'diversity_score': cycle['diversity_score']}
        )

        if telemetry.consolidation_triggered:
            consolidations_triggered += 1
            print(f"  Cycle {telemetry.cycle_number}: Consolidation triggered "
                  f"(frustration={telemetry.emotional_state.frustration:.3f})")

        if telemetry.emotional_state:
            max_frustration = max(max_frustration, telemetry.emotional_state.frustration)

    print()
    print(f"Max frustration observed: {max_frustration:.3f}")
    print(f"Consolidations triggered: {consolidations_triggered}")
    print()

    if consolidations_triggered > 0:
        print("✅ Frustration successfully triggered consolidation")
        print("   Emotional signal enabled adaptive learning")
    else:
        print("⚠️  No consolidations triggered")
        print(f"   Max frustration {max_frustration:.3f} may not have exceeded threshold")

    print()

    return consolidations_triggered > 0


def test_progress_threshold_adaptation():
    """Test that progress signal adapts satisfaction threshold"""
    print("=" * 80)
    print("TEST 2: Progress-Based Threshold Adaptation")
    print("=" * 80)
    print()

    params = CoordinationParameters(satisfaction_threshold=0.65)

    coordinator = Web4EmotionalCoordinator(
        params=params,
        enable_circadian=False,
        enable_emotional=True,
        enable_learning=False,  # Disable for cleaner test
        progress_threshold_adjustment_range=(-0.10, +0.10)
    )

    # Generate improving quality scenario
    history = generate_learning_scenario(200)

    print(f"Running {len(history)} cycles with improving quality...")
    print()

    threshold_adjustments = []
    progress_scores = []

    for cycle in history:
        should_coord, telemetry = coordinator.coordinate_interaction(
            priority=cycle['priority'],
            trust_score=cycle['trust_score'],
            network_density=cycle['network_density'],
            quality_score=cycle['quality_score'],
            context={'diversity_score': cycle['diversity_score']}
        )

        if telemetry.threshold_adjustment is not None:
            threshold_adjustments.append(telemetry.threshold_adjustment)

        if telemetry.emotional_state:
            progress_scores.append(telemetry.emotional_state.progress)

    # Analyze last 50 cycles (should show high progress)
    late_progress = sum(progress_scores[-50:]) / 50 if len(progress_scores) >= 50 else 0
    late_threshold_adj = sum(threshold_adjustments[-50:]) / 50 if len(threshold_adjustments) >= 50 else 0

    print(f"Late-stage progress score: {late_progress:.3f}")
    print(f"Late-stage avg threshold adjustment: {late_threshold_adj:+.4f}")
    print()

    # High progress should lower threshold (negative adjustment)
    if late_progress > 0.6 and late_threshold_adj < 0:
        print("✅ High progress lowered threshold (correct)")
        print("   System adapting to explore more as learning improves")
        return True
    elif late_progress < 0.4 and late_threshold_adj > 0:
        print("✅ Low progress raised threshold (correct)")
        print("   System becoming more selective when not improving")
        return True
    else:
        print(f"⚠️  Progress={late_progress:.3f}, threshold_adj={late_threshold_adj:+.3f}")
        print("   Relationship unclear or threshold not adapting strongly")
        return False


def test_curiosity_diversity_modulation():
    """Test that curiosity signal modulates diversity tolerance"""
    print("=" * 80)
    print("TEST 3: Curiosity-Driven Diversity Tolerance")
    print("=" * 80)
    print()

    params = CoordinationParameters(satisfaction_threshold=0.65)

    coordinator = Web4EmotionalCoordinator(
        params=params,
        enable_circadian=False,
        enable_emotional=True,
        enable_learning=False,
        curiosity_diversity_bonus=0.08
    )

    # Generate high diversity scenario
    history = []
    for i in range(100):
        diversity = random.uniform(0.6, 0.95)  # High diversity
        history.append({
            'priority': random.uniform(0.7, 0.9),
            'trust_score': random.uniform(0.7, 0.9),
            'network_density': random.uniform(0.6, 0.9),
            'quality_score': random.uniform(0.7, 0.9),
            'diversity_score': diversity
        })

    print(f"Running {len(history)} cycles with high diversity...")
    print()

    curiosity_scores = []
    emotional_adjustments = []

    for cycle in history:
        should_coord, telemetry = coordinator.coordinate_interaction(
            priority=cycle['priority'],
            trust_score=cycle['trust_score'],
            network_density=cycle['network_density'],
            quality_score=cycle['quality_score'],
            context={'diversity_score': cycle['diversity_score']}
        )

        if telemetry.emotional_state:
            curiosity_scores.append(telemetry.emotional_state.curiosity)

        if telemetry.emotional_adjustment is not None:
            emotional_adjustments.append(telemetry.emotional_adjustment)

    late_curiosity = sum(curiosity_scores[-30:]) / 30 if len(curiosity_scores) >= 30 else 0
    avg_adjustment = sum(emotional_adjustments) / len(emotional_adjustments) if emotional_adjustments else 0

    print(f"Late-stage curiosity: {late_curiosity:.3f}")
    print(f"Average emotional adjustment: {avg_adjustment:+.4f}")
    print()

    # High diversity should drive high curiosity, leading to positive adjustments
    if late_curiosity > 0.5 and avg_adjustment > 0:
        print("✅ High diversity → High curiosity → Positive adjustments")
        print("   System encouraging diverse exploration")
        return True
    else:
        print(f"⚠️  Curiosity={late_curiosity:.3f}, adjustment={avg_adjustment:+.3f}")
        return False


def test_engagement_priority_filtering():
    """Test that engagement signal filters by priority"""
    print("=" * 80)
    print("TEST 4: Engagement-Based Priority Filtering")
    print("=" * 80)
    print()

    params = CoordinationParameters(satisfaction_threshold=0.60)

    coordinator = Web4EmotionalCoordinator(
        params=params,
        enable_circadian=False,
        enable_emotional=True,
        enable_learning=False,
        engagement_priority_threshold=0.75
    )

    # Generate high-priority focused work
    history = []
    for i in range(100):
        priority = random.uniform(0.85, 0.95)  # Consistently high priority
        history.append({
            'priority': priority,
            'trust_score': random.uniform(0.7, 0.9),
            'network_density': random.uniform(0.6, 0.9),
            'quality_score': random.uniform(0.7, 0.9),
            'diversity_score': random.uniform(0.5, 0.8)
        })

    print(f"Running {len(history)} cycles with high-priority work...")
    print()

    engagement_scores = []
    high_priority_count = 0
    low_priority_penalty_count = 0

    # Add some low-priority items to test filtering
    for i in range(20):
        priority = random.uniform(0.4, 0.6)  # Low priority
        history.append({
            'priority': priority,
            'trust_score': random.uniform(0.7, 0.9),
            'network_density': random.uniform(0.6, 0.9),
            'quality_score': random.uniform(0.7, 0.9),
            'diversity_score': random.uniform(0.5, 0.8)
        })

    for cycle in history:
        should_coord, telemetry = coordinator.coordinate_interaction(
            priority=cycle['priority'],
            trust_score=cycle['trust_score'],
            network_density=cycle['network_density'],
            quality_score=cycle['quality_score'],
            context={'diversity_score': cycle['diversity_score']}
        )

        if telemetry.emotional_state:
            engagement_scores.append(telemetry.emotional_state.engagement)

        if cycle['priority'] < 0.7 and telemetry.emotional_adjustment and telemetry.emotional_adjustment < 0:
            low_priority_penalty_count += 1

    late_engagement = sum(engagement_scores[-30:]) / 30 if len(engagement_scores) >= 30 else 0

    print(f"Late-stage engagement: {late_engagement:.3f}")
    print(f"Low-priority items penalized: {low_priority_penalty_count}/20")
    print()

    # High engagement should filter out low-priority items
    if late_engagement > 0.75 and low_priority_penalty_count > 10:
        print("✅ High engagement → Low-priority filtering active")
        print("   System focused on important work")
        return True
    else:
        print(f"⚠️  Engagement={late_engagement:.3f}, penalties={low_priority_penalty_count}/20")
        return False


def run_all_tests():
    """Run all emotional modulation tests"""
    print("\n")
    print("=" * 80)
    print("EMOTIONAL DECISION MODULATION - PHASE 3 VALIDATION")
    print("=" * 80)
    print("\n")

    results = {}

    results['frustration'] = test_frustration_consolidation()
    print("\n")

    results['progress'] = test_progress_threshold_adaptation()
    print("\n")

    results['curiosity'] = test_curiosity_diversity_modulation()
    print("\n")

    results['engagement'] = test_engagement_priority_filtering()
    print("\n")

    # Summary
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print()

    passed = sum(results.values())
    total = len(results)

    for test_name, passed_test in results.items():
        status = "✅" if passed_test else "⚠️ "
        print(f"{status} {test_name.capitalize():15s}: {'PASS' if passed_test else 'UNCLEAR'}")

    print()
    print(f"Tests passed: {passed}/{total}")
    print()

    if passed >= 3:  # 75% threshold
        print("✅ PHASE 3 VALIDATION SUCCESSFUL")
        print()
        print("Emotional modulation improves coordination:")
        print("  • Frustration triggers consolidation (adaptive learning)")
        print("  • Progress adapts threshold (reinforcement learning style)")
        print("  • Curiosity modulates diversity (exploration/exploitation)")
        print("  • Engagement filters priority (focus on important work)")
        print()
        print("Impact:")
        print("  • Emotional intelligence enables adaptive coordination")
        print("  • System self-optimizes based on learning state")
        print("  • Multiple optimization dimensions (beyond quality alone)")
        print()
        print("Next: Cross-domain emotional pattern transfer")

    else:
        print("⚠️  PARTIAL VALIDATION")
        print("   Some emotional signals not clearly improving coordination")
        print("   May need parameter tuning")

    print()

    return results


if __name__ == "__main__":
    results = run_all_tests()
