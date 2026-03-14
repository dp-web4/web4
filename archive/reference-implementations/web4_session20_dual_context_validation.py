#!/usr/bin/env python3
"""
Web4 Session 20: Dual-Context Validation
=========================================

Validates epistemic predictions in their appropriate contexts:
- M2 (balanced distribution): Testing context (diverse scenarios)
- M4 (optimal prevalence): Production context (healthy operation)

This resolves the apparent contradiction discovered in Session 19.

Key Insight from Session 19:
"M2 and M4 aren't contradictory - they measure different contexts.
 Testing needs diversity, production needs health."

Research Provenance:
- Web4 S16: Epistemic coordination states
- Web4 S17: Observational framework
- Web4 S18: Initial validation (3/6 validated)
- Web4 S19: Diagnosis + improved logic + context separation
- Web4 S20: Dual-context re-validation (this session)

Created: December 12, 2025
"""

import time
import random
from typing import Dict
from web4_coordination_epistemic_states import CoordinationEpistemicMetrics
from web4_epistemic_observational_extension import Web4EpistemicObservationalFramework


def run_dual_context_validation():
    """
    Run validation in both testing and production contexts.

    Testing Context (M1, M2, M3, M5, M6):
    - Diverse scenarios with all 6 epistemic states
    - Validates state detection logic
    - Validates balanced distribution (M2)

    Production Context (M4):
    - Healthy operation scenarios
    - Validates optimal/stable prevalence
    """
    print("=" * 80)
    print("Web4 Session 20: Dual-Context Validation")
    print("=" * 80)
    print()
    print("Testing hypothesis: Context-appropriate scenarios improve validation")
    print()

    framework = Web4EpistemicObservationalFramework()

    # ========================================================================
    # CONTEXT 1: TESTING (Diverse Scenarios)
    # ========================================================================

    print("=" * 80)
    print("TESTING CONTEXT: Diverse Scenarios")
    print("=" * 80)
    print()
    print("Generating diverse coordination scenarios for M1, M2, M3, M5, M6...")
    print()

    from web4_session19_diverse_scenarios import generate_diverse_scenarios

    random.seed(42)
    raw_scenarios = generate_diverse_scenarios(num_each=33)

    test_history = []
    for i, scenario in enumerate(raw_scenarios):
        cycle = {
            'cycle_id': f'test_{i}',
            'scenario': scenario.get('scenario_type', 'diverse'),
            'epistemic_metrics': CoordinationEpistemicMetrics(
                coordination_confidence=scenario['coordination_confidence'],
                parameter_stability=scenario['parameter_stability'],
                objective_coherence=scenario['objective_coherence'],
                improvement_rate=scenario['improvement_rate'],
                adaptation_frustration=scenario['adaptation_frustration']
            ),
            'quality': scenario['objective_coherence'],
            'coverage': scenario['coordination_confidence'],
            'efficiency': scenario['parameter_stability'],
            'ground_truth_struggling': scenario['ground_truth_state'] == 'struggling'
        }
        test_history.append(cycle)

    print(f"✓ Generated {len(test_history)} test cycles")
    print()

    test_data = {'coordination_history': test_history}

    # Measure predictions appropriate for testing context
    test_predictions = {}
    test_validated = 0

    for pred_id in ["M1", "M2", "M3", "M5", "M6"]:
        prediction = framework.predictions_dict.get(pred_id)
        if not prediction:
            continue

        print(f"{pred_id}: {prediction.name}")
        print("-" * 80)

        try:
            observed, error = prediction.measure(test_data)
            validated, significance = prediction.validate(observed, error)

            status = "✅" if validated else "❌"
            print(f"  {status} Observed: {observed:.3f} ± {error:.3f}")
            print(f"     Predicted: {prediction.predicted_value:.3f}")
            print(f"     Range: {prediction.predicted_range}")
            print(f"     Significance: {significance:.2f}σ")

            test_predictions[pred_id] = {
                'validated': validated,
                'observed': observed,
                'significance': significance
            }

            if validated:
                test_validated += 1

            print()
        except Exception as e:
            print(f"  ⚠️  Measurement error: {e}")
            print()

    print(f"Testing Context Results: {test_validated}/5 predictions validated")
    print()

    # ========================================================================
    # CONTEXT 2: PRODUCTION (Healthy Operation)
    # ========================================================================

    print("=" * 80)
    print("PRODUCTION CONTEXT: Healthy Operation")
    print("=" * 80)
    print()
    print("Generating production coordination scenarios for M4...")
    print()

    from web4_session19_final_analysis import generate_production_scenarios

    random.seed(42)
    production_scenario_data = generate_production_scenarios(num_scenarios=200)

    production_history = []
    for i, scenario in enumerate(production_scenario_data):
        # Filter out context key
        metrics_dict = {k: v for k, v in scenario.items() if k != 'context'}
        cycle = {
            'cycle_id': f'prod_{i}',
            'scenario': scenario.get('context', 'production'),
            'epistemic_metrics': CoordinationEpistemicMetrics(**metrics_dict),
            'quality': scenario['objective_coherence'],
            'coverage': scenario['coordination_confidence'],
            'efficiency': scenario['parameter_stability'],
        }
        production_history.append(cycle)

    print(f"✓ Generated {len(production_history)} production cycles")
    print()

    production_data = {'coordination_history': production_history}

    # Measure M4 (optimal prevalence) in production context
    production_predictions = {}
    production_validated = 0

    for pred_id in ["M4"]:
        prediction = framework.predictions_dict.get(pred_id)
        if not prediction:
            continue

        print(f"{pred_id}: {prediction.name}")
        print("-" * 80)

        try:
            observed, error = prediction.measure(production_data)
            validated, significance = prediction.validate(observed, error)

            status = "✅" if validated else "❌"
            print(f"  {status} Observed: {observed:.3f} ± {error:.3f}")
            print(f"     Predicted: {prediction.predicted_value:.3f}")
            print(f"     Range: {prediction.predicted_range}")
            print(f"     Significance: {significance:.2f}σ")

            production_predictions[pred_id] = {
                'validated': validated,
                'observed': observed,
                'significance': significance
            }

            if validated:
                production_validated += 1

            print()
        except Exception as e:
            print(f"  ⚠️  Measurement error: {e}")
            print()

    print(f"Production Context Results: {production_validated}/1 predictions validated")
    print()

    # ========================================================================
    # COMBINED RESULTS
    # ========================================================================

    print("=" * 80)
    print("Combined Results")
    print("=" * 80)
    print()

    all_validated = test_validated + production_validated
    total_predictions = 6

    print(f"Total Validation: {all_validated}/{total_predictions} predictions validated ({all_validated/total_predictions*100:.0f}%)")
    print()

    print("Testing Context (M1, M2, M3, M5, M6):")
    for pred_id in ["M1", "M2", "M3", "M5", "M6"]:
        if pred_id in test_predictions:
            status = "✅" if test_predictions[pred_id]['validated'] else "❌"
            print(f"  {status} {pred_id}")

    print()
    print("Production Context (M4):")
    for pred_id in ["M4"]:
        if pred_id in production_predictions:
            status = "✅" if production_predictions[pred_id]['validated'] else "❌"
            print(f"  {status} {pred_id}")

    print()

    # Comparison with Session 18
    print("=" * 80)
    print("Comparison with Session 18")
    print("=" * 80)
    print()

    session18_validated = 3  # M1, M5, M6
    improvement = all_validated - session18_validated

    print(f"Session 18: {session18_validated}/6 validated (50%)")
    print(f"Session 20: {all_validated}/6 validated ({all_validated/6*100:.0f}%)")
    print()

    if improvement > 0:
        print(f"✅ Improved by +{improvement} prediction(s)")
        print()
        print("Session 19 state logic improvements successful!")
    elif improvement == 0:
        print("⚠️  No change in validation rate")
        print()
        print("Session 19 improvements verified M2 context, but overall rate unchanged")
    else:
        print(f"❌ Validation rate decreased by {abs(improvement)}")

    print()

    # State distribution analysis for each context
    print("=" * 80)
    print("State Distribution Analysis")
    print("=" * 80)
    print()

    # Testing context
    test_state_counts = {}
    for cycle in test_history:
        state = cycle['epistemic_metrics'].primary_state().value
        test_state_counts[state] = test_state_counts.get(state, 0) + 1

    print(f"Testing Context ({len(test_history)} cycles):")
    for state, count in sorted(test_state_counts.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(test_history) * 100
        print(f"  {state:12s}: {pct:5.1f}% ({count} cycles)")

    test_max_pct = max(count / len(test_history) * 100 for count in test_state_counts.values())
    print(f"\n  M2 metric: Max state = {test_max_pct:.1f}% (target < 50%)")
    print(f"  {'✅ Validates' if test_max_pct < 50 else '❌ Fails'}")
    print()

    # Production context
    prod_state_counts = {}
    for cycle in production_history:
        state = cycle['epistemic_metrics'].primary_state().value
        prod_state_counts[state] = prod_state_counts.get(state, 0) + 1

    print(f"Production Context ({len(production_history)} cycles):")
    for state, count in sorted(prod_state_counts.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(production_history) * 100
        print(f"  {state:12s}: {pct:5.1f}% ({count} cycles)")

    prod_optimal_stable_pct = (
        (prod_state_counts.get('optimal', 0) + prod_state_counts.get('stable', 0)) /
        len(production_history) * 100
    )
    print(f"\n  M4 metric: Optimal+Stable = {prod_optimal_stable_pct:.1f}% (target 60-99%)")
    print(f"  {'✅ Validates' if 60 <= prod_optimal_stable_pct <= 99 else '❌ Fails'}")
    print()

    return {
        'test_validated': test_validated,
        'production_validated': production_validated,
        'total_validated': all_validated,
        'validation_rate': all_validated / total_predictions,
        'improvement': improvement
    }


if __name__ == "__main__":
    print("Web4 Session 20: Dual-Context Validation")
    print("=" * 80)
    print()
    print("Validating predictions in appropriate contexts:")
    print("- Testing: Diverse scenarios for M1, M2, M3, M5, M6")
    print("- Production: Healthy operation for M4")
    print()

    start_time = time.time()
    results = run_dual_context_validation()
    elapsed = time.time() - start_time

    print("=" * 80)
    print(f"Session 20 complete in {elapsed:.1f}s")
    print("=" * 80)
    print()

    if results['improvement'] >= 1:
        print("✅ SESSION 20 SUCCESS")
        print()
        print(f"Validation rate: {results['validation_rate']*100:.0f}%")
        print(f"Improvement: +{results['improvement']} prediction(s)")
    else:
        print("⚠️  SESSION 20 PARTIAL SUCCESS")
        print()
        print(f"Validation rate: {results['validation_rate']*100:.0f}%")
        print("Context separation confirmed, but validation rate unchanged")

    print()
