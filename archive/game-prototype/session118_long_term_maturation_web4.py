#!/usr/bin/env python3
"""
Session 118: Long-Term EP Maturation Dynamics for Web4 ATP Management

Parallel to Thor's Session 152 (SAGE consciousness), studying how EP-driven
ATP management evolves over extended use.

Research Questions (Web4-specific):
1. Does Web4 pattern match rate stay at 100% or degrade with corpus growth?
2. How does ATP survival rate evolve with larger pattern corpus?
3. Which Web4 domains (emotional/quality/attention) dominate organic growth?
4. Do Web4 patterns show emotional-domain concentration like SAGE?
5. What is optimal corpus size for ATP management?
6. Is there evidence of diminishing returns in ATP decisions?

Context from Session 117:
- Web4-native patterns: 100 patterns (Session 116 corpus)
- Hybrid safety override: Ensures survival regardless of pattern quality
- 3 domains: emotional, quality, attention (vs SAGE's 5 domains)

Approach:
- Run 100 ATP management scenarios (vs Session 117's 20 steps × 3 lives = 60)
- Track pattern growth, match rates, domain distribution
- Analyze if emotional domain dominates (like SAGE Session 152)
- Compare Web4 maturation dynamics to SAGE findings
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter

# Add modules
sys.path.insert(0, str(Path(__file__).parent))

from engine.models import Agent, Society, World, LifeRecord
from engine.scenarios import bootstrap_home_society_world
from engine.sim_loop import tick_world
from engine.agent_actions import apply_policy_action, applied_action_to_dict
from ep_driven_policy import EPDrivenPolicy, create_policy_with_web4_patterns


class LongTermWeb4MaturationStudy:
    """
    Study long-term EP maturation for Web4 ATP management.

    Tracks how pattern learning evolves over 100+ decision points.
    """

    def __init__(self, initial_pattern_source: str = "web4"):
        """
        Initialize maturation study.

        Args:
            initial_pattern_source: "web4", "thor", or "none"
        """
        self.pattern_source = initial_pattern_source
        self.results: List[Dict[str, Any]] = []
        self.snapshots: List[Dict[str, Any]] = []

    def run_study(self, num_scenarios: int = 100, verbose: bool = True) -> Dict[str, Any]:
        """
        Run long-term maturation study.

        Args:
            num_scenarios: Number of decision scenarios to run (default 100)
            verbose: Print progress

        Returns:
            Study results with temporal analysis
        """
        if verbose:
            print("=" * 80)
            print(f"WEB4 LONG-TERM MATURATION STUDY")
            print("=" * 80)
            print(f"Scenarios: {num_scenarios}")
            print(f"Initial pattern source: {self.pattern_source}")
            print()

        # Create policy with initial patterns
        if self.pattern_source == "web4":
            policy = create_policy_with_web4_patterns()
            if verbose:
                stats = policy.get_learning_stats()
                print(f"Loaded {stats['total_patterns']} Web4-native patterns")
        elif self.pattern_source == "thor":
            from ep_driven_policy import create_policy_with_thor_patterns
            hrm_path = Path("/home/dp/ai-workspace/HRM")
            policy = create_policy_with_thor_patterns(hrm_path)
            if verbose:
                stats = policy.get_learning_stats()
                print(f"Loaded {stats['total_patterns']} Thor SAGE patterns")
        else:
            policy = EPDrivenPolicy()
            if verbose:
                print("Starting with 0 patterns (heuristic baseline)")

        initial_stats = policy.get_learning_stats()
        initial_pattern_count = initial_stats['total_patterns']

        if verbose:
            print(f"Initial maturation: {initial_stats['maturation_stage']}")
            print(f"Initial corpus: {initial_pattern_count} patterns")
            print()

        # Initialize world
        world = bootstrap_home_society_world()
        research_agent = self._select_research_agent(world)

        if research_agent is None:
            return {"error": "No agents in world"}

        agent_lct = research_agent.agent_lct

        # Get society for action application
        if not world.societies:
            return {"error": "No societies in world"}
        home_society_lct = sorted(world.societies.keys())[0]
        home_society = world.societies[home_society_lct]

        # Set initial conditions (medium ATP, neutral T3)
        research_agent.trust_axes.setdefault("T3", {})
        research_agent.trust_axes["T3"]["composite"] = 0.5
        research_agent.resources["ATP"] = 100.0

        survival_count = 0
        death_count = 0

        # Track temporal evolution
        temporal_snapshots = []

        # Run scenarios
        for scenario_idx in range(num_scenarios):
            tick_world(world)

            # Get current state
            t3_composite = float((research_agent.trust_axes.get("T3") or {}).get("composite", 0.0))
            atp = float(research_agent.resources.get("ATP", 0.0))

            # EP-driven action proposal
            life_id = f"maturation_study_{scenario_idx}"

            policy_result = policy.propose_action(
                agent=research_agent,
                world=world,
                life_id=life_id
            )

            proposed_action = policy_result["proposed_action"]
            ep_assessment = policy_result["ep_assessment"]

            # Apply action
            result = apply_policy_action(
                world=world,
                society=home_society,
                agent=research_agent,
                life_id=life_id,
                proposed_action=proposed_action
            )

            # Record outcome from AppliedAction dataclass
            outcome = {
                "success": True,  # Action was applied successfully
                "atp_before": result.atp_before,
                "atp_after": result.atp_after,
                "t3_before": result.trust_before,
                "t3_after": result.trust_after,
                "survived": result.atp_after > 0.0
            }

            # Record pattern (this grows the corpus)
            # Get contexts and predictions from ep_assessment
            if "contexts" in ep_assessment and "predictions" in ep_assessment:
                policy.record_outcome(
                    life_id=life_id,
                    tick=world.tick,
                    contexts=ep_assessment["contexts"],
                    predictions=ep_assessment["predictions"],
                    action_taken=proposed_action,
                    outcome=outcome
                )

            # Track survival
            if outcome["survived"]:
                survival_count += 1
            else:
                death_count += 1

            # Store scenario result
            current_stats = policy.get_learning_stats()
            scenario_result = {
                "scenario_idx": scenario_idx,
                "tick": world.tick,
                "atp_before": result.atp_before,
                "atp_after": result.atp_after,
                "t3_before": result.trust_before,
                "t3_after": result.trust_after,
                "action": proposed_action,
                "survived": outcome["survived"],
                "total_patterns": current_stats['total_patterns'],
                "pattern_rate": current_stats['pattern_rate'],
                "maturation": current_stats['maturation_stage'],
                "domains": {k.name if hasattr(k, 'name') else str(k): v for k, v in current_stats['patterns_by_domain'].items()},
                "pattern_matches": {k.name if hasattr(k, 'name') else str(k): v for k, v in ep_assessment.get("pattern_matches", {}).items()},
                "learning_mode": ep_assessment.get("learning_mode", "unknown")
            }
            self.results.append(scenario_result)

            # Snapshot every 10 scenarios
            if (scenario_idx + 1) % 10 == 0:
                snapshot = {
                    "scenario": scenario_idx + 1,
                    "total_patterns": current_stats['total_patterns'],
                    "pattern_rate": current_stats['pattern_rate'],
                    "maturation": current_stats['maturation_stage'],
                    "patterns_by_domain": {k.name if hasattr(k, 'name') else str(k): v for k, v in current_stats['patterns_by_domain'].items()},
                    "survival_rate": survival_count / (scenario_idx + 1)
                }
                temporal_snapshots.append(snapshot)

                if verbose:
                    print(f"Scenario {scenario_idx + 1}/{num_scenarios}:")
                    print(f"  Corpus: {current_stats['total_patterns']} patterns")
                    print(f"  Maturation: {current_stats['maturation_stage']}")
                    print(f"  Survival: {survival_count}/{scenario_idx + 1} ({100*survival_count/(scenario_idx+1):.1f}%)")
                    print(f"  Domains: {self._format_domains(current_stats['patterns_by_domain'])}")

        # Final analysis
        final_stats = policy.get_learning_stats()

        # Calculate domain growth
        domain_growth = {}
        for domain_key in final_stats['patterns_by_domain']:
            domain_name = domain_key.split('.')[-1]
            initial_count = initial_stats['patterns_by_domain'].get(domain_key, 0)
            final_count = final_stats['patterns_by_domain'][domain_key]
            growth = final_count - initial_count
            domain_growth[domain_name] = {
                'initial': initial_count,
                'final': final_count,
                'growth': growth,
                'growth_pct': 100 * growth / num_scenarios if num_scenarios > 0 else 0
            }

        if verbose:
            print("\n" + "=" * 80)
            print("STUDY COMPLETE")
            print("=" * 80)
            print(f"\nFinal Corpus: {final_stats['total_patterns']} patterns")
            print(f"Growth: +{final_stats['total_patterns'] - initial_pattern_count} patterns")
            print(f"Survival Rate: {100*survival_count/num_scenarios:.1f}%")
            print(f"\nDomain Distribution:")
            for domain, info in domain_growth.items():
                print(f"  {domain:12s}: {info['initial']:3d} → {info['final']:3d} (+{info['growth']:3d}, {info['growth_pct']:.1f}% of growth)")

        return {
            "configuration": {
                "num_scenarios": num_scenarios,
                "pattern_source": self.pattern_source,
                "initial_pattern_count": initial_pattern_count
            },
            "final_metrics": {
                "total_patterns": final_stats['total_patterns'],
                "corpus_growth": final_stats['total_patterns'] - initial_pattern_count,
                "survival_rate": survival_count / num_scenarios,
                "death_rate": death_count / num_scenarios,
                "maturation_stage": final_stats['maturation_stage'],
                "pattern_match_rate": final_stats['pattern_rate']
            },
            "domain_growth": domain_growth,
            "temporal_snapshots": temporal_snapshots,
            "scenario_results": self.results
        }

    def _select_research_agent(self, world: World) -> Optional[Agent]:
        """Select the research agent (treasurer or first agent)."""
        if not world.agents:
            return None

        # Prefer treasurer
        home_society = None
        if world.societies:
            home_society_lct = sorted(world.societies.keys())[0]
            home_society = world.societies[home_society_lct]

        treasurer_role_lct = None
        if home_society is not None:
            society_slug = home_society.society_lct.split(":")[-1]
            treasurer_role_lct = f"lct:web4:role:{society_slug}:treasurer"

        if treasurer_role_lct is not None:
            treasurer_holders = sorted(
                {
                    e.subject
                    for e in world.context_edges
                    if e.predicate == "web4:hasRole" and e.object == treasurer_role_lct
                }
            )
            for agent_lct in treasurer_holders:
                agent = world.agents.get(agent_lct)
                if agent is not None:
                    return agent

        # Fallback to first agent
        agent_lct = sorted(world.agents.keys())[0]
        return world.agents[agent_lct]

    def _format_domains(self, domains_dict: Dict[str, int]) -> str:
        """Format domain distribution for display."""
        parts = []
        for domain_key, count in domains_dict.items():
            domain_name = domain_key.split('.')[-1][:3].upper()
            parts.append(f"{domain_name}:{count}")
        return ", ".join(parts)


def main():
    """Run long-term Web4 maturation study."""
    import argparse

    parser = argparse.ArgumentParser(description="Web4 Long-Term EP Maturation Study")
    parser.add_argument(
        "--pattern-source",
        choices=["web4", "thor", "none"],
        default="web4",
        help="Initial pattern source (default: web4)"
    )
    parser.add_argument(
        "--scenarios",
        type=int,
        default=100,
        help="Number of scenarios to run (default: 100)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file for results (default: session118_results/maturation_{source}.json)"
    )

    args = parser.parse_args()

    # Run study
    study = LongTermWeb4MaturationStudy(initial_pattern_source=args.pattern_source)
    results = study.run_study(num_scenarios=args.scenarios, verbose=True)

    # Save results
    if args.output is None:
        output_dir = Path(__file__).parent / "session118_results"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"maturation_{args.pattern_source}.json"
    else:
        output_file = args.output

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
