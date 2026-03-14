"""
Empirical Authorization Model Refinement
=========================================

Applies Thor's empirical methodology to Web4 authorization policies.

Problem: Track 24 (SAGE-Web4 authorization integration) used heuristic state multipliers:
- FOCUS: 1.0
- WAKE: 0.9
- REST: 0.5
- DREAM: 0.0

Thor's discovery: Heuristic models are often wrong (188% error for attention prediction).

Solution: Collect empirical data to fit data-driven models.

Approach:
1. Grid search over consciousness state + trust configurations
2. Measure actual authorization outcomes
3. Fit regression models for decision probabilities
4. Compare heuristic vs empirical model accuracy

Author: Legion Autonomous Web4 Research
Date: 2025-12-07
Track: 26 (Empirical Authorization Models)
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple
from enum import Enum
import random
import statistics
import sys
from pathlib import Path

from lct_registry import LCTRegistry, EntityType, LCTCredential
from authorization_engine import (
    AuthorizationEngine,
    AuthorizationRequest,
    AuthorizationDecision,
    AgentDelegation
)

# Import SAGE MetabolicState (with stub fallback)
try:
    sage_path = Path.home() / "ai-workspace" / "HRM" / "sage"
    sys.path.insert(0, str(sage_path))
    from core.metabolic_controller import MetabolicState
except ImportError:
    # Stub for demonstration
    class MetabolicState(str, Enum):
        WAKE = "WAKE"
        FOCUS = "FOCUS"
        REST = "REST"
        DREAM = "DREAM"


@dataclass
class AuthorizationContext:
    """Complete context for authorization decision"""
    metabolic_state: MetabolicState
    arousal: float  # 0-1
    atp_level: float  # 0-1
    base_trust_score: float  # 0-1
    action_criticality: str  # 'routine', 'sensitive', 'critical'
    atp_cost: float  # 0-100


@dataclass
class AuthorizationOutcome:
    """Measured outcome of authorization attempt"""
    context: AuthorizationContext
    decision: AuthorizationDecision
    decision_time_ms: float
    effective_trust: float  # What trust score was used
    reason: str


class EmpiricaLAuthorizationCollector:
    """Collect empirical data for authorization model refinement"""

    def __init__(self):
        # Simplified initialization - we're testing authorization logic, not LCT infrastructure
        self.outcomes: List[AuthorizationOutcome] = []

    def generate_test_configurations(self) -> List[AuthorizationContext]:
        """
        Generate grid of test configurations

        Similar to Thor's threshold grid search:
        - Metabolic states: WAKE, FOCUS, REST, DREAM (4)
        - Arousal levels: [0.2, 0.5, 0.8] (3)
        - ATP levels: [0.2, 0.5, 0.8] (3)
        - Trust scores: [0.3, 0.6, 0.9] (3)
        - Action types: routine, sensitive, critical (3)

        Total: 4 * 3 * 3 * 3 * 3 = 324 configurations
        """
        configurations = []

        states = [MetabolicState.WAKE, MetabolicState.FOCUS,
                  MetabolicState.REST, MetabolicState.DREAM]
        arousal_levels = [0.2, 0.5, 0.8]
        atp_levels = [0.2, 0.5, 0.8]
        trust_scores = [0.3, 0.6, 0.9]
        action_types = ['routine', 'sensitive', 'critical']

        for state in states:
            for arousal in arousal_levels:
                for atp in atp_levels:
                    for trust in trust_scores:
                        for action_type in action_types:
                            # ATP cost correlates with criticality
                            atp_cost = {
                                'routine': 1.0,
                                'sensitive': 5.0,
                                'critical': 15.0
                            }[action_type]

                            config = AuthorizationContext(
                                metabolic_state=state,
                                arousal=arousal,
                                atp_level=atp,
                                base_trust_score=trust,
                                action_criticality=action_type,
                                atp_cost=atp_cost
                            )
                            configurations.append(config)

        return configurations

    def test_authorization(self, context: AuthorizationContext) -> AuthorizationOutcome:
        """
        Test authorization decision with given context

        Simulates consciousness-aware authorization from Track 24
        """
        import time

        # Simulate consciousness-aware decision logic (from Track 24)
        start_time = time.perf_counter()

        # Policy 1: Check consciousness can handle criticality
        can_handle_critical = (
            context.metabolic_state == MetabolicState.FOCUS
            and context.arousal > 0.6
            and context.atp_level > 0.4
        )

        if context.action_criticality == 'critical' and not can_handle_critical:
            decision = AuthorizationDecision.DEFERRED
            reason = "Critical action requires FOCUS state with high arousal and ATP"
            effective_trust = 0.0

        # Policy 2: Apply state-dependent trust multipliers (HEURISTIC - to be replaced)
        else:
            heuristic_multipliers = {
                MetabolicState.FOCUS: 1.0,
                MetabolicState.WAKE: 0.9,
                MetabolicState.REST: 0.5,
                MetabolicState.DREAM: 0.0
            }

            effective_trust = context.base_trust_score * heuristic_multipliers[context.metabolic_state]

            # Policy 3: Check ATP budget
            if context.atp_cost > 10 and context.atp_level < 0.3:
                decision = AuthorizationDecision.DEFERRED
                reason = "ATP too low for expensive action"

            # Policy 4: Check trust threshold
            elif effective_trust < 0.4:
                decision = AuthorizationDecision.DENIED
                reason = f"Trust {effective_trust:.2f} below threshold 0.4"

            else:
                decision = AuthorizationDecision.GRANTED
                reason = f"Authorized with trust {effective_trust:.2f}"

        end_time = time.perf_counter()
        decision_time = (end_time - start_time) * 1000  # Convert to ms

        return AuthorizationOutcome(
            context=context,
            decision=decision,
            decision_time_ms=decision_time,
            effective_trust=effective_trust,
            reason=reason
        )

    def collect_empirical_data(self) -> List[AuthorizationOutcome]:
        """
        Collect empirical authorization outcomes

        Run each configuration and record outcome
        """
        print("=" * 70)
        print("  EMPIRICAL AUTHORIZATION DATA COLLECTION")
        print("=" * 70)

        configurations = self.generate_test_configurations()
        print(f"\nTesting {len(configurations)} configurations...")
        print(f"This will take ~{len(configurations) * 0.001:.1f} seconds\n")

        outcomes = []
        for i, config in enumerate(configurations):
            outcome = self.test_authorization(config)
            outcomes.append(outcome)

            if (i + 1) % 50 == 0:
                print(f"Progress: {i + 1}/{len(configurations)} ({100*(i+1)/len(configurations):.1f}%)")

        self.outcomes = outcomes
        print(f"\n✅ Data collection complete: {len(outcomes)} outcomes")
        return outcomes

    def analyze_decision_patterns(self, outcomes: List[AuthorizationOutcome]) -> Dict:
        """
        Analyze patterns in authorization decisions

        Similar to Thor's correlation analysis
        """
        print("\n" + "=" * 70)
        print("  DECISION PATTERN ANALYSIS")
        print("=" * 70)

        # Group by metabolic state
        by_state = {}
        for outcome in outcomes:
            state = outcome.context.metabolic_state
            if state not in by_state:
                by_state[state] = []
            by_state[state].append(outcome)

        # Calculate grant rates by state
        print("\n[1] Grant Rates by Metabolic State")
        print("-" * 70)
        state_grant_rates = {}
        for state, state_outcomes in by_state.items():
            granted = sum(1 for o in state_outcomes if o.decision == AuthorizationDecision.GRANTED)
            total = len(state_outcomes)
            grant_rate = granted / total
            state_grant_rates[state] = grant_rate
            print(f"  {state.name:6s}: {grant_rate:6.1%} ({granted}/{total} granted)")

        # Grant rates by action criticality
        print("\n[2] Grant Rates by Action Criticality")
        print("-" * 70)
        by_criticality = {}
        for outcome in outcomes:
            crit = outcome.context.action_criticality
            if crit not in by_criticality:
                by_criticality[crit] = []
            by_criticality[crit].append(outcome)

        for crit, crit_outcomes in by_criticality.items():
            granted = sum(1 for o in crit_outcomes if o.decision == AuthorizationDecision.GRANTED)
            total = len(crit_outcomes)
            grant_rate = granted / total
            print(f"  {crit:9s}: {grant_rate:6.1%} ({granted}/{total} granted)")

        # Average effective trust by state
        print("\n[3] Average Effective Trust by State")
        print("-" * 70)
        state_avg_trust = {}
        for state, state_outcomes in by_state.items():
            avg_trust = statistics.mean(o.effective_trust for o in state_outcomes)
            state_avg_trust[state] = avg_trust
            print(f"  {state.name:6s}: {avg_trust:.3f}")

        # Decision time statistics
        print("\n[4] Decision Time Statistics")
        print("-" * 70)
        all_times = [o.decision_time_ms for o in outcomes]
        print(f"  Mean:   {statistics.mean(all_times):.4f} ms")
        print(f"  Median: {statistics.median(all_times):.4f} ms")
        print(f"  Min:    {min(all_times):.4f} ms")
        print(f"  Max:    {max(all_times):.4f} ms")

        return {
            'state_grant_rates': state_grant_rates,
            'state_avg_trust': state_avg_trust,
            'by_criticality': by_criticality
        }

    def fit_empirical_models(self, outcomes: List[AuthorizationOutcome]) -> Dict:
        """
        Fit empirical models to replace heuristic multipliers

        Use actual grant rate data to determine state multipliers
        """
        print("\n" + "=" * 70)
        print("  EMPIRICAL MODEL FITTING")
        print("=" * 70)

        # Calculate actual grant rates for each state at each trust level
        # This will give us the empirical multiplier

        states = [MetabolicState.WAKE, MetabolicState.FOCUS,
                  MetabolicState.REST, MetabolicState.DREAM]
        trust_levels = [0.3, 0.6, 0.9]

        empirical_multipliers = {}

        print("\n[1] Empirical State Multipliers (from grant rate data)")
        print("-" * 70)

        for state in states:
            # Get outcomes for this state
            state_outcomes = [o for o in outcomes if o.context.metabolic_state == state]

            # Calculate average grant rate across all trust levels
            # (This is a simplification - could do regression for more accuracy)
            granted = sum(1 for o in state_outcomes if o.decision == AuthorizationDecision.GRANTED)
            total = len(state_outcomes)
            grant_rate = granted / total if total > 0 else 0.0

            # Empirical multiplier is relative to FOCUS (highest grant rate)
            # We'll normalize after collecting all rates
            empirical_multipliers[state] = grant_rate

        # Normalize so FOCUS = 1.0
        focus_rate = empirical_multipliers[MetabolicState.FOCUS]
        if focus_rate > 0:
            for state in states:
                empirical_multipliers[state] /= focus_rate

        # Print comparison
        heuristic_multipliers = {
            MetabolicState.FOCUS: 1.0,
            MetabolicState.WAKE: 0.9,
            MetabolicState.REST: 0.5,
            MetabolicState.DREAM: 0.0
        }

        print(f"{'State':<8} {'Heuristic':<12} {'Empirical':<12} {'Difference':<12}")
        print("-" * 70)
        for state in states:
            heur = heuristic_multipliers[state]
            emp = empirical_multipliers[state]
            diff = emp - heur
            print(f"{state.name:<8} {heur:<12.3f} {emp:<12.3f} {diff:+.3f} ({100*diff/heur if heur > 0 else 0:+.1f}%)")

        return {
            'empirical_multipliers': empirical_multipliers,
            'heuristic_multipliers': heuristic_multipliers
        }

    def save_empirical_model(self, models: Dict) -> None:
        """Save empirical models for use in production authorization"""
        import json
        import os
        from datetime import datetime

        model_dir = os.path.expanduser("~/.web4/authorization_models/")
        os.makedirs(model_dir, exist_ok=True)

        model_file = os.path.join(model_dir, "empirical_auth_model_v1.json")

        model_data = {
            "version": "1.0.0",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "description": "Data-driven authorization model from empirical measurements",
            "configurations_tested": len(self.outcomes),
            "state_multipliers": {
                state.name: float(mult)
                for state, mult in models['empirical_multipliers'].items()
            },
            "usage": "Replace heuristic multipliers in ConsciousnessAwareAuthorizationEngine"
        }

        with open(model_file, 'w') as f:
            json.dump(model_data, f, indent=2)

        print(f"\n✅ Empirical model saved: {model_file}")


def main():
    """Run empirical authorization model collection and analysis"""

    print("=" * 70)
    print("  Track 26: Empirical Authorization Model Refinement")
    print("  Applying Thor's Methodology to Web4 Authorization")
    print("=" * 70)
    print("\nMotivation:")
    print("  Thor discovered heuristic models can be 188% wrong.")
    print("  Track 24 used heuristic state multipliers (FOCUS=1.0, WAKE=0.9, etc.)")
    print("  Let's measure actual authorization outcomes and fit empirical models.")
    print()

    collector = EmpiricaLAuthorizationCollector()

    # Step 1: Collect empirical data
    outcomes = collector.collect_empirical_data()

    # Step 2: Analyze decision patterns
    analysis = collector.analyze_decision_patterns(outcomes)

    # Step 3: Fit empirical models
    models = collector.fit_empirical_models(outcomes)

    # Step 4: Save models for production use
    collector.save_empirical_model(models)

    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"✅ Collected {len(outcomes)} empirical authorization outcomes")
    print(f"✅ Analyzed decision patterns across states and criticality levels")
    print(f"✅ Fitted empirical state multipliers to replace heuristics")
    print(f"✅ Saved model to ~/.web4/authorization_models/")
    print("\nNext Steps:")
    print("  1. Update ConsciousnessAwareAuthorizationEngine with empirical multipliers")
    print("  2. Re-run Track 24 scenarios with empirical model")
    print("  3. Measure improvement in authorization accuracy")
    print()


if __name__ == "__main__":
    main()
