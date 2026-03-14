#!/usr/bin/env python3
"""
Web4 Session 19: Diverse Epistemic Scenario Generator
======================================================

Creates scenarios designed to trigger all 6 coordination epistemic states,
not just optimal/stable.

Key Insight from Calibration Analysis:
- Previous scenarios only tested "healthy production" (high conf, high stab)
- This naturally produces 100% optimal+stable
- Need scenarios representing:
  - Struggling: High frustration
  - Conflicting: Low coherence
  - Converging: Improving confidence, unstable parameters
  - Adapting: Rapid parameter changes
  - Stable: Good but not optimal
  - Optimal: Everything perfect

Following SAGE S36 pattern: Create "sketches" of each epistemic state.

Created: December 12, 2025
"""

import random
from typing import List, Dict
from web4_session19_improved_state_logic import CoordinationEpistemicMetrics


def generate_diverse_scenarios(num_each: int = 20) -> List[Dict]:
    """
    Generate scenarios designed to trigger each epistemic state.

    Args:
        num_each: Number of scenarios for each state

    Returns:
        List of scenario dictionaries with ground_truth_state label
    """
    scenarios = []

    # 1. STRUGGLING: High adaptation_frustration > 0.7
    for i in range(num_each):
        scenarios.append({
            'coordination_confidence': random.uniform(0.4, 0.7),
            'parameter_stability': random.uniform(0.3, 0.7),
            'objective_coherence': random.uniform(0.5, 0.8),
            'improvement_rate': random.uniform(-0.05, 0.0),  # Negative or zero
            'adaptation_frustration': random.uniform(0.7, 0.95),  # High!
            'ground_truth_state': 'struggling',
            'scenario_type': 'coordination_problems'
        })

    # 2. CONFLICTING: Low objective_coherence < 0.4
    for i in range(num_each):
        scenarios.append({
            'coordination_confidence': random.uniform(0.5, 0.8),
            'parameter_stability': random.uniform(0.4, 0.8),
            'objective_coherence': random.uniform(0.1, 0.4),  # Low!
            'improvement_rate': random.uniform(-0.02, 0.02),
            'adaptation_frustration': random.uniform(0.3, 0.6),
            'ground_truth_state': 'conflicting',
            'scenario_type': 'objective_conflicts'
        })

    # 3. OPTIMAL: High confidence > 0.85 AND high stability > 0.85
    for i in range(num_each):
        scenarios.append({
            'coordination_confidence': random.uniform(0.85, 0.98),  # High
            'parameter_stability': random.uniform(0.85, 1.0),  # High
            'objective_coherence': random.uniform(0.7, 0.95),
            'improvement_rate': random.uniform(0.0, 0.05),
            'adaptation_frustration': random.uniform(0.05, 0.3),
            'ground_truth_state': 'optimal',
            'scenario_type': 'best_case_production'
        })

    # 4. STABLE: High stability > 0.85 but moderate confidence (0.7-0.85)
    for i in range(num_each):
        scenarios.append({
            'coordination_confidence': random.uniform(0.70, 0.85),  # Moderate
            'parameter_stability': random.uniform(0.85, 1.0),  # High
            'objective_coherence': random.uniform(0.6, 0.85),
            'improvement_rate': random.uniform(-0.01, 0.03),
            'adaptation_frustration': random.uniform(0.1, 0.4),
            'ground_truth_state': 'stable',
            'scenario_type': 'steady_state_production'
        })

    # 5. CONVERGING: Moderate confidence (0.7-0.85) AND low stability < 0.85
    for i in range(num_each):
        scenarios.append({
            'coordination_confidence': random.uniform(0.70, 0.85),  # Moderate
            'parameter_stability': random.uniform(0.50, 0.85),  # Changing
            'objective_coherence': random.uniform(0.6, 0.85),
            'improvement_rate': random.uniform(0.02, 0.10),  # Positive
            'adaptation_frustration': random.uniform(0.2, 0.5),
            'ground_truth_state': 'converging',
            'scenario_type': 'learning_phase'
        })

    # 6. ADAPTING: Very low stability < 0.5
    for i in range(num_each):
        scenarios.append({
            'coordination_confidence': random.uniform(0.5, 0.8),
            'parameter_stability': random.uniform(0.2, 0.5),  # Very low
            'objective_coherence': random.uniform(0.5, 0.8),
            'improvement_rate': random.uniform(-0.05, 0.08),
            'adaptation_frustration': random.uniform(0.3, 0.6),
            'ground_truth_state': 'adapting',
            'scenario_type': 'environmental_change'
        })

    # Shuffle to avoid sequential bias
    random.shuffle(scenarios)

    return scenarios


def test_state_detection(scenarios: List[Dict]) -> Dict:
    """
    Test state detection accuracy on diverse scenarios.

    Args:
        scenarios: Scenarios with ground_truth_state labels

    Returns:
        Detection accuracy statistics
    """
    correct_current = 0
    correct_improved = 0
    total = len(scenarios)

    state_accuracy = {
        'struggling': {'correct_current': 0, 'correct_improved': 0, 'total': 0},
        'conflicting': {'correct_current': 0, 'correct_improved': 0, 'total': 0},
        'optimal': {'correct_current': 0, 'correct_improved': 0, 'total': 0},
        'stable': {'correct_current': 0, 'correct_improved': 0, 'total': 0},
        'converging': {'correct_current': 0, 'correct_improved': 0, 'total': 0},
        'adapting': {'correct_current': 0, 'correct_improved': 0, 'total': 0}
    }

    confusion_matrix_current = {}
    confusion_matrix_improved = {}

    for scenario in scenarios:
        ground_truth = scenario['ground_truth_state']
        metrics = CoordinationEpistemicMetrics(
            coordination_confidence=scenario['coordination_confidence'],
            parameter_stability=scenario['parameter_stability'],
            objective_coherence=scenario['objective_coherence'],
            improvement_rate=scenario['improvement_rate'],
            adaptation_frustration=scenario['adaptation_frustration']
        )

        predicted_current = metrics.primary_state_current().value
        predicted_improved = metrics.primary_state_improved().value

        # Overall accuracy
        if predicted_current == ground_truth:
            correct_current += 1
        if predicted_improved == ground_truth:
            correct_improved += 1

        # Per-state accuracy
        state_accuracy[ground_truth]['total'] += 1
        if predicted_current == ground_truth:
            state_accuracy[ground_truth]['correct_current'] += 1
        if predicted_improved == ground_truth:
            state_accuracy[ground_truth]['correct_improved'] += 1

        # Confusion matrices
        key_current = (ground_truth, predicted_current)
        key_improved = (ground_truth, predicted_improved)
        confusion_matrix_current[key_current] = confusion_matrix_current.get(key_current, 0) + 1
        confusion_matrix_improved[key_improved] = confusion_matrix_improved.get(key_improved, 0) + 1

    return {
        'overall_accuracy_current': correct_current / total,
        'overall_accuracy_improved': correct_improved / total,
        'per_state_accuracy': state_accuracy,
        'confusion_matrix_current': confusion_matrix_current,
        'confusion_matrix_improved': confusion_matrix_improved
    }


def analyze_state_distribution(scenarios: List[Dict]) -> Dict:
    """
    Analyze state distribution with current vs improved logic.

    Returns M2/M4 validation results.
    """
    from web4_session19_improved_state_logic import CoordinationEpistemicMetrics

    current_counts = {}
    improved_counts = {}

    for scenario in scenarios:
        metrics = CoordinationEpistemicMetrics(
            coordination_confidence=scenario['coordination_confidence'],
            parameter_stability=scenario['parameter_stability'],
            objective_coherence=scenario['objective_coherence'],
            improvement_rate=scenario['improvement_rate'],
            adaptation_frustration=scenario['adaptation_frustration']
        )

        current_state = metrics.primary_state_current().value
        improved_state = metrics.primary_state_improved().value

        current_counts[current_state] = current_counts.get(current_state, 0) + 1
        improved_counts[improved_state] = improved_counts.get(improved_state, 0) + 1

    total = len(scenarios)

    current_dist = {state: (count / total * 100, count) for state, count in current_counts.items()}
    improved_dist = {state: (count / total * 100, count) for state, count in improved_counts.items()}

    # M2: Max state proportion
    current_max = max(pct for pct, count in current_dist.values())
    improved_max = max(pct for pct, count in improved_dist.values())

    # M4: Optimal + Stable proportion
    current_m4 = (current_dist.get('optimal', (0, 0))[0] +
                  current_dist.get('stable', (0, 0))[0])
    improved_m4 = (improved_dist.get('optimal', (0, 0))[0] +
                   improved_dist.get('stable', (0, 0))[0])

    return {
        'current_distribution': current_dist,
        'improved_distribution': improved_dist,
        'M2': {
            'current': current_max,
            'improved': improved_max,
            'target': 50.0,
            'current_validates': current_max < 50.0,
            'improved_validates': improved_max < 50.0
        },
        'M4': {
            'current': current_m4,
            'improved': improved_m4,
            'target_range': (60.0, 85.0),
            'current_validates': 60.0 <= current_m4 <= 85.0,
            'improved_validates': 60.0 <= improved_m4 <= 85.0
        }
    }


def run_diverse_scenario_test():
    """Run complete diverse scenario testing."""
    print("=" * 80)
    print("Web4 Session 19: Diverse Epistemic Scenario Testing")
    print("=" * 80)
    print()

    random.seed(42)

    # Generate diverse scenarios
    scenarios = generate_diverse_scenarios(num_each=20)
    print(f"Generated {len(scenarios)} scenarios (20 per state)")
    print()

    # Test state detection accuracy
    print("=" * 80)
    print("State Detection Accuracy")
    print("=" * 80)
    print()

    accuracy_results = test_state_detection(scenarios)

    print(f"Overall Accuracy (Current):  {accuracy_results['overall_accuracy_current']*100:.1f}%")
    print(f"Overall Accuracy (Improved): {accuracy_results['overall_accuracy_improved']*100:.1f}%")
    print()

    print("Per-State Accuracy:")
    print()
    for state, stats in accuracy_results['per_state_accuracy'].items():
        total = stats['total']
        current_acc = stats['correct_current'] / total * 100 if total > 0 else 0
        improved_acc = stats['correct_improved'] / total * 100 if total > 0 else 0

        print(f"  {state:12s}: Current {current_acc:5.1f}%, Improved {improved_acc:5.1f}% ({total} scenarios)")

    print()

    # Analyze distribution
    print("=" * 80)
    print("State Distribution Analysis")
    print("=" * 80)
    print()

    dist_analysis = analyze_state_distribution(scenarios)

    print("CURRENT Logic Distribution:")
    for state, (pct, count) in sorted(dist_analysis['current_distribution'].items(),
                                      key=lambda x: x[1][0], reverse=True):
        print(f"  {state:12s}: {pct:5.1f}% ({count:3d} scenarios)")
    print()

    print("IMPROVED Logic Distribution:")
    for state, (pct, count) in sorted(dist_analysis['improved_distribution'].items(),
                                      key=lambda x: x[1][0], reverse=True):
        print(f"  {state:12s}: {pct:5.1f}% ({count:3d} scenarios)")
    print()

    # Prediction validation
    print("=" * 80)
    print("Prediction Validation (Diverse Scenarios)")
    print("=" * 80)
    print()

    m2 = dist_analysis['M2']
    print("M2: Max State Proportion < 50%")
    print(f"  Current:  {m2['current']:5.1f}% {'✅ VALIDATES' if m2['current_validates'] else '❌ FAILS'}")
    print(f"  Improved: {m2['improved']:5.1f}% {'✅ VALIDATES' if m2['improved_validates'] else '❌ FAILS'}")
    print()

    m4 = dist_analysis['M4']
    print("M4: Optimal + Stable ≥ 60%")
    print(f"  Current:  {m4['current']:5.1f}% {'✅ VALIDATES' if m4['current_validates'] else '❌ FAILS'}")
    print(f"  Improved: {m4['improved']:5.1f}% {'✅ VALIDATES' if m4['improved_validates'] else '❌ FAILS'}")
    print()

    # Summary
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()

    if m2['improved_validates'] and m4['improved_validates']:
        print("✅ BOTH PREDICTIONS VALIDATE WITH IMPROVED LOGIC!")
        print()
        print("Key Findings:")
        print("- Diverse scenarios create balanced state distribution")
        print("- Improved logic properly distinguishes stable vs converging")
        print("- M2 and M4 validate when scenarios represent full epistemic range")
        print()
        print("Next Steps:")
        print("1. Implement improved primary_state() logic in Session 16 code")
        print("2. Re-run Session 18 validation with diverse scenarios")
        print("3. Document Session 19 findings")
    elif m2['improved_validates'] or m4['improved_validates']:
        print("⚠️  PARTIAL IMPROVEMENT")
        print()
        if m2['improved_validates']:
            print("✓ M2 validates with improved logic")
        else:
            print("✗ M2 still fails - further threshold adjustment needed")
        if m4['improved_validates']:
            print("✓ M4 validates with improved logic")
        else:
            print("✗ M4 still fails - scenario mix or prediction target issue")
    else:
        print("❌ STILL FAILING")
        print()
        print("Both predictions fail even with diverse scenarios")
        print("Consider prediction target adjustment")

    print()


if __name__ == "__main__":
    run_diverse_scenario_test()
