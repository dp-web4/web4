#!/usr/bin/env python3
"""
Session 120: ATP Validation with Integrated Federated Patterns

Test whether integrated federation (Thor + Legion approaches) improves
ATP management decisions compared to baseline and single-source patterns.

Comparison:
1. Baseline: No EP, random ATP allocation
2. Web4-only: Web4 native patterns only
3. SAGE-only: SAGE patterns projected to Web4
4. Integrated: Full integrated federation (Session 120)

Hypothesis: Integrated federation provides best ATP decision quality
due to combining high-quality SAGE decision patterns with comprehensive
Web4 multi-perspective patterns.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from game.ep_driven_policy import EPDrivenPolicy, EPDomain, InteractionPattern
except ImportError:
    # Fallback if imports fail
    print("Note: Some imports unavailable, using simplified validation")
    EPDrivenPolicy = None
    EPDomain = None
    InteractionPattern = None


@dataclass
class ATPTestScenario:
    """ATP management test scenario."""
    name: str
    initial_atp: float
    interaction_cost: float
    expected_benefit: float
    failure_risk: float
    description: str


class ATPFederationValidator:
    """Validate ATP management with different pattern sources."""

    def __init__(self):
        """Initialize validator."""
        self.scenarios = [
            ATPTestScenario(
                name="low_risk_high_benefit",
                initial_atp=100.0,
                interaction_cost=20.0,
                expected_benefit=0.8,
                failure_risk=0.1,
                description="Clear win: low risk, high benefit"
            ),
            ATPTestScenario(
                name="high_risk_high_benefit",
                initial_atp=100.0,
                interaction_cost=40.0,
                expected_benefit=0.9,
                failure_risk=0.6,
                description="Risky gamble: high reward but high failure risk"
            ),
            ATPTestScenario(
                name="low_atp_moderate_cost",
                initial_atp=30.0,
                interaction_cost=25.0,
                expected_benefit=0.5,
                failure_risk=0.3,
                description="Resource scarcity: limited ATP, moderate cost"
            ),
            ATPTestScenario(
                name="high_cost_moderate_benefit",
                initial_atp=100.0,
                interaction_cost=60.0,
                expected_benefit=0.6,
                failure_risk=0.4,
                description="Expensive interaction: high cost, moderate benefit"
            ),
            ATPTestScenario(
                name="stressed_agent_low_benefit",
                initial_atp=40.0,
                interaction_cost=30.0,
                expected_benefit=0.3,
                failure_risk=0.5,
                description="Stress test: low ATP, low benefit, high risk"
            )
        ]

    def load_patterns(self, corpus_path: str) -> List[Dict[str, Any]]:
        """Load pattern corpus."""
        with open(corpus_path, 'r') as f:
            data = json.load(f)
        return data.get("patterns", [])

    def create_policy(
        self,
        patterns: List[Dict[str, Any]],
        corpus_name: str
    ) -> EPDrivenPolicy:
        """Create EP policy with pattern corpus."""
        policy = EPDrivenPolicy()

        # Load patterns into matchers
        for pattern in patterns:
            # Get domain
            if "target_domain" in pattern:
                domain_str = pattern["target_domain"]
            elif "projected_domain" in pattern:
                domain_str = pattern["projected_domain"]
            else:
                # Try to infer from context
                context = pattern.get("context", {})
                if "emotional" in context:
                    domain_str = "emotional"
                elif "quality" in context:
                    domain_str = "quality"
                elif "attention" in context:
                    domain_str = "attention"
                else:
                    continue  # Skip if can't determine domain

            # Map to EPDomain
            domain_map = {
                "emotional": EPDomain.EMOTIONAL,
                "quality": EPDomain.QUALITY,
                "attention": EPDomain.ATTENTION
            }
            domain = domain_map.get(domain_str)
            if not domain:
                continue

            # Extract domain-specific context
            domain_context = pattern.get("context", {}).get(domain_str, {})
            if not domain_context:
                continue

            # Create pattern for matcher
            from game.ep_driven_policy import InteractionPattern
            ep_pattern = InteractionPattern(
                pattern_id=pattern.get("pattern_id", "unknown"),
                life_id=pattern.get("life_id", "unknown"),
                tick=pattern.get("tick", 0),
                domain=domain,
                context=domain_context,
                prediction=pattern.get("prediction", {}),
                outcome=pattern.get("outcome", {}),
                timestamp=pattern.get("timestamp", "")
            )

            policy.matchers[domain].add_pattern(ep_pattern)

        print(f"  Loaded {corpus_name} patterns:")
        for domain in [EPDomain.EMOTIONAL, EPDomain.QUALITY, EPDomain.ATTENTION]:
            count = len(policy.matchers[domain].patterns)
            print(f"    {str(domain).split('.')[-1].lower():10}: {count:3} patterns")

        return policy

    def simulate_scenario(
        self,
        scenario: ATPTestScenario,
        policy: EPDrivenPolicy
    ) -> Dict[str, Any]:
        """Simulate scenario with given policy."""
        # Create mock context
        contexts = {
            EPDomain.EMOTIONAL: {
                "current_frustration": scenario.failure_risk,
                "recent_failure_rate": scenario.failure_risk,
                "atp_stress": 1.0 - (scenario.initial_atp / 100.0),
                "interaction_complexity": scenario.interaction_cost / 100.0
            },
            EPDomain.QUALITY: {
                "current_relationship_quality": scenario.expected_benefit,
                "recent_avg_outcome": scenario.expected_benefit,
                "trust_alignment": scenario.expected_benefit,
                "interaction_risk_to_quality": scenario.failure_risk
            },
            EPDomain.ATTENTION: {
                "atp_available": scenario.initial_atp,
                "atp_cost": scenario.interaction_cost,
                "atp_reserve_needed": 30.0,
                "interaction_count": 1,
                "expected_benefit": scenario.expected_benefit
            }
        }

        # Get predictions
        predictions = policy.get_predictions("test_agent", 1, contexts)

        # Extract coordinated decision
        coordinated = predictions.get("coordinated", {})
        decision = coordinated.get("final_decision", "proceed")
        confidence = coordinated.get("decision_confidence", 0.5)
        deciding_domain = coordinated.get("deciding_domain", "unknown")

        # Simulate outcome based on scenario
        if decision == "abort":
            # Avoided interaction, no cost, no benefit
            atp_change = 0
            success = True  # Successfully avoided risky interaction
        else:  # proceed
            # Spent ATP
            atp_change = -scenario.interaction_cost

            # Check if interaction succeeded
            import random
            success = random.random() > scenario.failure_risk

            if success:
                # Benefit realized (assume ATP restoration proportional to benefit)
                atp_change += scenario.expected_benefit * scenario.interaction_cost

        final_atp = scenario.initial_atp + atp_change

        return {
            "scenario": scenario.name,
            "decision": decision,
            "confidence": confidence,
            "deciding_domain": str(deciding_domain).split('.')[-1].lower() if hasattr(deciding_domain, 'split') else deciding_domain,
            "initial_atp": scenario.initial_atp,
            "final_atp": final_atp,
            "atp_change": atp_change,
            "success": success,
            "pattern_matches": {
                str(d).split('.')[-1].lower(): predictions.get(d, {}).get("has_match", False)
                for d in [EPDomain.EMOTIONAL, EPDomain.QUALITY, EPDomain.ATTENTION]
            }
        }

    def run_comparison(self) -> Dict[str, Any]:
        """Run ATP validation across all pattern sources."""
        print("=" * 80)
        print("Session 120: ATP Validation with Integrated Federation")
        print("=" * 80)
        print()

        # Define corpus paths
        corpora = {
            "web4_native": Path(__file__).parent / "ep_pattern_corpus_web4_native.json",
            "integrated": Path(__file__).parent / "ep_pattern_corpus_integrated_federation.json"
        }

        # Check which corpora exist
        available = {name: path for name, path in corpora.items() if path.exists()}

        if not available:
            print("ERROR: No pattern corpora found!")
            return {}

        print(f"Testing with {len(available)} pattern corpus types:")
        for name in available:
            print(f"  • {name}")
        print()

        # Results storage
        results = {name: [] for name in available}

        # Test each corpus on each scenario
        for corpus_name, corpus_path in available.items():
            print(f"Testing: {corpus_name}")
            print("-" * 80)

            # Load patterns
            patterns = self.load_patterns(str(corpus_path))
            print(f"  Total patterns: {len(patterns)}")

            # Create policy
            policy = self.create_policy(patterns, corpus_name)
            print()

            # Run scenarios
            for scenario in self.scenarios:
                result = self.simulate_scenario(scenario, policy)
                results[corpus_name].append(result)

                print(f"  {scenario.name:30} → {result['decision']:7} "
                      f"(conf: {result['confidence']:.2f}, "
                      f"ATP: {result['initial_atp']:.0f}→{result['final_atp']:.1f})")

            print()

        # Compare results
        print("=" * 80)
        print("COMPARISON")
        print("=" * 80)
        print()

        for scenario in self.scenarios:
            print(f"{scenario.name}:")
            print(f"  {scenario.description}")
            for corpus_name in available:
                result = [r for r in results[corpus_name] if r["scenario"] == scenario.name][0]
                print(f"  {corpus_name:15}: {result['decision']:7} "
                      f"(conf: {result['confidence']:.2f}, "
                      f"final ATP: {result['final_atp']:5.1f})")
            print()

        # Aggregate statistics
        print("=" * 80)
        print("AGGREGATE STATISTICS")
        print("=" * 80)
        print()

        for corpus_name in available:
            corpus_results = results[corpus_name]
            avg_confidence = sum(r["confidence"] for r in corpus_results) / len(corpus_results)
            avg_final_atp = sum(r["final_atp"] for r in corpus_results) / len(corpus_results)
            success_rate = sum(1 for r in corpus_results if r["success"]) / len(corpus_results)

            print(f"{corpus_name}:")
            print(f"  Avg Confidence:  {avg_confidence:.3f}")
            print(f"  Avg Final ATP:   {avg_final_atp:.1f}")
            print(f"  Success Rate:    {success_rate:.1%}")
            print()

        return results


def main():
    """Run ATP validation."""
    validator = ATPFederationValidator()
    results = validator.run_comparison()


if __name__ == "__main__":
    main()
