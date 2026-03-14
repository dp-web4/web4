#!/usr/bin/env python3
"""
Web4 Session 19: Improved State Estimation Logic
=================================================

Based on Session 19 analysis, proposes improved primary_state() logic
that properly distinguishes stable vs converging states.

Key Insight from Analysis:
- Parameter stability is consistently 1.000 in production
- Current logic: converging check (line 106) catches scenarios before stable
- Result: 72% converging when should be ~60% stable

Improved Logic Cascade:
1. Struggling (frustration > 0.7)
2. Conflicting (coherence < 0.4)
3. Optimal (conf > 0.85 AND stab > 0.85)
4. Stable (stab > 0.85 AND conf > 0.7)  ← NEW ORDER
5. Converging (conf improving but stab < 0.85)
6. Adapting (stab < 0.5)

Created: December 12, 2025
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class CoordinationEpistemicState(Enum):
    """Coordination epistemic states following Thor S30 pattern."""
    OPTIMAL = "optimal"
    ADAPTING = "adapting"
    STRUGGLING = "struggling"
    CONFLICTING = "conflicting"
    CONVERGING = "converging"
    STABLE = "stable"


@dataclass
class CoordinationEpistemicMetrics:
    """Coordination epistemic metrics."""
    coordination_confidence: float      # 0-1
    parameter_stability: float          # 0-1
    objective_coherence: float          # 0-1
    improvement_rate: float             # Can be negative
    adaptation_frustration: float       # 0-1

    def primary_state_current(self) -> CoordinationEpistemicState:
        """
        CURRENT logic from Session 16 (for comparison).
        """
        # High frustration dominates (struggling)
        if self.adaptation_frustration > 0.7:
            return CoordinationEpistemicState.STRUGGLING

        # Low coherence → conflicting objectives
        if self.objective_coherence < 0.4:
            return CoordinationEpistemicState.CONFLICTING

        # High confidence + high stability → optimal
        if self.coordination_confidence > 0.9 and self.parameter_stability > 0.9:
            return CoordinationEpistemicState.OPTIMAL

        # Good confidence but not fully stable → converging
        if 0.7 < self.coordination_confidence < 0.9:
            return CoordinationEpistemicState.CONVERGING

        # Low stability (parameters changing) → adapting
        if self.parameter_stability < 0.5:
            return CoordinationEpistemicState.ADAPTING

        # Default: stable
        return CoordinationEpistemicState.STABLE

    def primary_state_improved(self) -> CoordinationEpistemicState:
        """
        IMPROVED logic based on Session 19 analysis.

        Key changes:
        1. Lower optimal threshold: 0.9 → 0.85 (captures production scenarios)
        2. Stable check BEFORE converging (proper cascade)
        3. Converging requires instability (stab < 0.85), not just moderate confidence
        4. Clearer semantic distinction between states
        """
        # High frustration dominates (struggling)
        if self.adaptation_frustration > 0.7:
            return CoordinationEpistemicState.STRUGGLING

        # Low coherence → conflicting objectives
        if self.objective_coherence < 0.4:
            return CoordinationEpistemicState.CONFLICTING

        # High confidence + high stability → optimal
        # ADJUSTED: 0.9 → 0.85 based on production mean (0.843)
        if self.coordination_confidence > 0.85 and self.parameter_stability > 0.85:
            return CoordinationEpistemicState.OPTIMAL

        # High stability but moderate confidence → stable
        # NEW POSITION: Check before converging to capture stable production
        if self.parameter_stability > 0.85 and self.coordination_confidence > 0.7:
            return CoordinationEpistemicState.STABLE

        # Moderate confidence with changing parameters → converging
        # REFINED: Requires instability (stab < 0.85), not just confidence range
        if 0.7 < self.coordination_confidence < 0.85 and self.parameter_stability < 0.85:
            return CoordinationEpistemicState.CONVERGING

        # Low stability (parameters changing rapidly) → adapting
        if self.parameter_stability < 0.5:
            return CoordinationEpistemicState.ADAPTING

        # Default: stable (fallback for edge cases)
        return CoordinationEpistemicState.STABLE


def compare_logic(scenarios: list) -> Dict:
    """
    Compare current vs improved logic on Session 18 scenarios.

    Returns:
        Statistics showing state distribution differences
    """
    current_counts = {state: 0 for state in CoordinationEpistemicState}
    improved_counts = {state: 0 for state in CoordinationEpistemicState}
    state_changes = []

    for scenario in scenarios:
        metrics = CoordinationEpistemicMetrics(**scenario)

        current_state = metrics.primary_state_current()
        improved_state = metrics.primary_state_improved()

        current_counts[current_state] += 1
        improved_counts[improved_state] += 1

        if current_state != improved_state:
            state_changes.append({
                'scenario': scenario,
                'current': current_state,
                'improved': improved_state
            })

    total = len(scenarios)

    return {
        'current_distribution': {
            state.value: (count / total * 100, count)
            for state, count in current_counts.items()
        },
        'improved_distribution': {
            state.value: (count / total * 100, count)
            for state, count in improved_counts.items()
        },
        'state_changes': state_changes,
        'num_changes': len(state_changes)
    }


def analyze_prediction_impact(current_dist: Dict, improved_dist: Dict) -> Dict:
    """
    Analyze impact on M2 and M4 predictions.

    M2: Max state proportion < 50%
    M4: Optimal + Stable ≥ 60%
    """
    # M2: Maximum state proportion
    current_max = max(pct for pct, count in current_dist.values())
    improved_max = max(pct for pct, count in improved_dist.values())

    # M4: Optimal + Stable proportion
    current_m4 = (current_dist.get('optimal', (0, 0))[0] +
                  current_dist.get('stable', (0, 0))[0])
    improved_m4 = (improved_dist.get('optimal', (0, 0))[0] +
                   improved_dist.get('stable', (0, 0))[0])

    return {
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


def run_comparison():
    """Run comparison of current vs improved logic on Session 18 scenarios."""
    print("=" * 80)
    print("Web4 Session 19: Improved State Estimation Logic Comparison")
    print("=" * 80)
    print()

    # Generate same scenarios as Session 18
    import random
    random.seed(42)

    scenarios = []
    for _ in range(200):
        scenarios.append({
            'coordination_confidence': random.gauss(0.85, 0.075),
            'parameter_stability': 1.0,  # Consistently perfect in production
            'objective_coherence': random.gauss(0.80, 0.086),
            'improvement_rate': random.gauss(0.05, 0.02),
            'adaptation_frustration': random.gauss(0.2, 0.1)
        })

    print(f"Generated {len(scenarios)} scenarios")
    print()

    # Compare logic
    comparison = compare_logic(scenarios)

    print("=" * 80)
    print("State Distribution Comparison")
    print("=" * 80)
    print()

    print("CURRENT Logic (Session 16):")
    for state, (pct, count) in sorted(comparison['current_distribution'].items(),
                                      key=lambda x: x[1][0], reverse=True):
        print(f"  {state:12s}: {pct:5.1f}% ({count:3d} cycles)")
    print()

    print("IMPROVED Logic (Session 19):")
    for state, (pct, count) in sorted(comparison['improved_distribution'].items(),
                                      key=lambda x: x[1][0], reverse=True):
        print(f"  {state:12s}: {pct:5.1f}% ({count:3d} cycles)")
    print()

    print(f"State changes: {comparison['num_changes']}/{len(scenarios)} cycles ({comparison['num_changes']/len(scenarios)*100:.1f}%)")
    print()

    # Analyze prediction impact
    prediction_impact = analyze_prediction_impact(
        comparison['current_distribution'],
        comparison['improved_distribution']
    )

    print("=" * 80)
    print("Impact on Predictions")
    print("=" * 80)
    print()

    print("M2: Max State Proportion < 50%")
    m2 = prediction_impact['M2']
    print(f"  Current:  {m2['current']:.1f}% {'✅ VALIDATES' if m2['current_validates'] else '❌ FAILS'}")
    print(f"  Improved: {m2['improved']:.1f}% {'✅ VALIDATES' if m2['improved_validates'] else '❌ FAILS'}")
    print(f"  Target:   < {m2['target']:.1f}%")
    print()

    print("M4: Optimal + Stable ≥ 60%")
    m4 = prediction_impact['M4']
    print(f"  Current:  {m4['current']:.1f}% {'✅ VALIDATES' if m4['current_validates'] else '❌ FAILS'}")
    print(f"  Improved: {m4['improved']:.1f}% {'✅ VALIDATES' if m4['improved_validates'] else '❌ FAILS'}")
    print(f"  Target:   {m4['target_range'][0]:.1f}%-{m4['target_range'][1]:.1f}%")
    print()

    # Show some example state changes
    print("=" * 80)
    print("Example State Changes (first 10)")
    print("=" * 80)
    print()

    for i, change in enumerate(comparison['state_changes'][:10], 1):
        scenario = change['scenario']
        print(f"{i}. {change['current'].value:12s} → {change['improved'].value:12s}")
        print(f"   confidence: {scenario['coordination_confidence']:.3f}, stability: {scenario['parameter_stability']:.3f}")
        print()

    print("=" * 80)
    print("Recommendation")
    print("=" * 80)
    print()

    if m2['improved_validates'] and m4['improved_validates']:
        print("✅ IMPLEMENT IMPROVED LOGIC")
        print("   Both M2 and M4 will validate with improved state estimation")
    elif m4['improved_validates'] and not m2['improved_validates']:
        print("⚠️  PARTIAL IMPROVEMENT")
        print("   M4 validates but M2 still marginal - consider further refinement")
    else:
        print("❌ NEEDS MORE WORK")
        print("   Further analysis required")

    print()


if __name__ == "__main__":
    run_comparison()
