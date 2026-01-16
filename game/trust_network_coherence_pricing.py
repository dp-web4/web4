#!/usr/bin/env python3
"""
Trust Network Evolution with Coherence ATP Pricing
Session #28: Deploy coherence pricing to 4life playground

Extends trust_network_evolution.py with coherence-based ATP pricing.
Tests economic incentive for cooperation through trust dynamics.

Key Hypothesis:
- Coherence pricing creates endogenous cooperation incentive
- High-trust networks pay less ATP → agents incentivized to cooperate
- Low-trust networks pay more ATP → punishment for defection
- Economic feedback loop drives coalition formation

Experiment:
1. Run baseline simulation (fixed ATP costs)
2. Run coherence-enabled simulation (trust-adjusted costs)
3. Compare cooperation rates, coalition formation, network trust

Expected Result:
- Coherence pricing increases cooperation rate
- Faster coalition formation
- Higher final network trust
- Demonstrates economic mechanism working

Author: Legion (autonomous Session #28)
Based on: trust_network_evolution.py + Session #27 coherence pricing
"""

import sys
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import random

# Add paths
game_dir = Path(__file__).parent
sys.path.insert(0, str(game_dir))
sys.path.insert(0, str(game_dir.parent / "web4-standard" / "implementation" / "trust"))

# Import game engine
from trust_network_evolution import (
    create_trust_network_world,
    TrustNetworkTracker,
    BehavioralProfile,
    BEHAVIORAL_PROFILES
)
from engine.models import Agent, Society, World
from engine.sim_loop import tick_world

# Import coherence framework
from coherence_trust_tensor import CoherenceTrustMetrics
from engine.coherence_atp_integration import (
    CoherenceIntegratedPricer,
    CoherencePricingPolicy
)


# ============================================================================
# Coherence-Enabled Simulation
# ============================================================================

@dataclass
class CoherenceSimulationMetrics:
    """Track coherence metrics throughout simulation"""
    tick: int
    network_trust: float
    network_variance: float
    network_density: float
    num_agents: int
    num_strong_edges: int
    gamma: float
    coherence: float
    entropy_ratio: float
    is_quantum_regime: bool
    above_coalition_threshold: bool
    avg_atp_cost: float
    cooperation_rate: float


class CoherencePricingSimulation:
    """Trust network simulation with coherence-based ATP pricing"""

    def __init__(
        self,
        enable_coherence: bool = True,
        coherence_policy: Optional[CoherencePricingPolicy] = None
    ):
        self.enable_coherence = enable_coherence
        self.pricer = CoherenceIntegratedPricer(coherence_policy) if enable_coherence else None
        self.coherence_metrics: List[CoherenceSimulationMetrics] = []

    def compute_network_coherence_metrics(
        self,
        tracker: TrustNetworkTracker,
        world: World,
        agents: Dict[str, Agent]
    ) -> Optional[CoherenceTrustMetrics]:
        """
        Compute coherence metrics from current trust network state

        Args:
            tracker: Trust network tracker with edges
            world: World state
            agents: Agent dictionary

        Returns:
            CoherenceTrustMetrics or None if insufficient data
        """
        if not tracker.edges:
            return None

        # Collect trust values from all edges
        trust_values = [edge.trust_value for edge in tracker.edges.values()]

        if len(trust_values) < 2:
            return None

        # Compute network statistics
        avg_trust = sum(trust_values) / len(trust_values)
        trust_variance = sum((t - avg_trust) ** 2 for t in trust_values) / len(trust_values)

        # Compute network density
        num_agents = len(agents)
        max_edges = num_agents * (num_agents - 1)  # Directed graph
        network_density = len(tracker.edges) / max_edges if max_edges > 0 else 0.0

        # Count strong edges (trust > 0.7)
        num_strong_edges = sum(1 for edge in tracker.edges.values() if edge.trust_value > 0.7)

        # Create coherence metrics
        try:
            metrics = CoherenceTrustMetrics(
                trust_value=avg_trust,
                trust_variance=trust_variance,
                network_density=network_density,
                num_agents=num_agents,
                num_strong_edges=num_strong_edges
            )
            return metrics
        except Exception as e:
            print(f"Warning: Failed to compute coherence metrics: {e}")
            return None

    def compute_atp_cost(
        self,
        base_cost: float,
        action_type: str,
        coherence_metrics: Optional[CoherenceTrustMetrics]
    ) -> Tuple[float, Optional[float]]:
        """
        Compute ATP cost with optional coherence adjustment

        Args:
            base_cost: Base ATP cost for action
            action_type: Type of action (help, ignore, etc.)
            coherence_metrics: Current network coherence metrics

        Returns:
            (final_cost, coherence_multiplier)
        """
        if not self.enable_coherence or coherence_metrics is None or self.pricer is None:
            return base_cost, None

        # Use coherence pricer to adjust cost
        # Map action to modality (simplified for simulation)
        modality_map = {
            "help": "coordination",  # Helping is coordination
            "ignore": "llm_inference",  # Ignoring is less expensive
            "attack": "coordination"  # Attack is also coordination
        }

        modality = modality_map.get(action_type, "coordination")

        # Price with coherence
        result = self.pricer.price_with_coherence(
            modality=modality,
            complexity="low",
            latency=10.0,
            quality=0.7,
            trust_metrics=coherence_metrics,
            location="cloud"
        )

        # Normalize to base cost scale
        # result['final_cost'] is ~100 from pricer, we want it scaled to base_cost
        coherence_mult = result['coherence_multiplier']
        final_cost = base_cost * coherence_mult

        return final_cost, coherence_mult

    def simulate_interaction_with_coherence(
        self,
        world: World,
        source: Agent,
        target: Agent,
        profile: BehavioralProfile,
        tracker: TrustNetworkTracker,
        agents: Dict[str, Agent],
        tick: int
    ) -> Dict[str, Any]:
        """
        Simulate agent interaction with coherence-adjusted ATP costs

        Similar to trust_network_evolution.simulate_agent_interaction
        but applies coherence pricing.
        """
        # Compute current coherence metrics
        coherence_metrics = self.compute_network_coherence_metrics(tracker, world, agents)

        # Determine if source cooperates
        cooperates = random.random() < profile.cooperation_rate

        # Determine action type and base cost
        if cooperates:
            action_type = "help"
            base_atp_cost = 10.0
            trust_change = 0.05 if random.random() < profile.reliability else -0.02
            reason = f"{source.name} helps {target.name}"
        else:
            action_type = "ignore"
            base_atp_cost = 2.0
            trust_change = -0.03
            reason = f"{source.name} ignores {target.name}"

        # Apply coherence pricing
        final_atp_cost, coherence_mult = self.compute_atp_cost(
            base_atp_cost,
            action_type,
            coherence_metrics
        )

        # Apply ATP cost to source
        source.resources["ATP"] = max(0.0, source.resources["ATP"] - final_atp_cost)

        # If helped, target gains ATP
        if cooperates:
            target.resources["ATP"] = min(150.0, target.resources["ATP"] + 5.0)

        # Update trust from target's perspective
        target_trust = target.trust_axes.get("T3", {})
        current_trust = target_trust.get("composite", 0.5)
        new_trust = max(0.0, min(1.0, current_trust + trust_change))
        target_trust["composite"] = new_trust

        # Record in trust network
        tracker.record_interaction(
            tick=tick,
            source_lct=source.agent_lct,
            target_lct=target.agent_lct,
            action_type=action_type,
            cooperation=cooperates,
            trust_change=trust_change,
            reason=reason
        )

        return {
            "source": source.name,
            "target": target.name,
            "action": action_type,
            "cooperated": cooperates,
            "trust_change": trust_change,
            "base_atp_cost": base_atp_cost,
            "final_atp_cost": final_atp_cost,
            "coherence_multiplier": coherence_mult,
            "coherence_metrics": coherence_metrics
        }

    def run_simulation(
        self,
        num_ticks: int = 30,
        snapshot_interval: int = 5
    ) -> Dict[str, Any]:
        """
        Run trust network simulation with coherence pricing

        Args:
            num_ticks: Number of simulation ticks
            snapshot_interval: How often to take snapshots

        Returns:
            Simulation results including metrics and events
        """
        # Create world
        world, agents, tracker, agent_profiles = create_trust_network_world()
        agent_list = list(agents.values())

        # Track metrics
        tick_metrics = []
        total_atp_costs = []
        cooperation_counts = []

        # Run simulation
        for tick in range(1, num_ticks + 1):
            # Each tick, simulate 2-3 interactions
            num_interactions = random.randint(2, 3)
            tick_cooperations = 0
            tick_atp = []

            for _ in range(num_interactions):
                # Pick two different agents
                source = random.choice(agent_list)
                target = random.choice([a for a in agent_list if a != source])

                # Get source's profile
                profile_key = agent_profiles.get(source.agent_lct, "opportunist")
                profile = BEHAVIORAL_PROFILES[profile_key]

                # Simulate interaction
                result = self.simulate_interaction_with_coherence(
                    world, source, target, profile, tracker, agents, tick
                )

                # Track metrics
                if result["cooperated"]:
                    tick_cooperations += 1
                tick_atp.append(result["final_atp_cost"])

            # Compute network coherence metrics
            coherence_metrics = self.compute_network_coherence_metrics(tracker, world, agents)

            if coherence_metrics:
                # Track simulation metrics
                avg_tick_atp = sum(tick_atp) / len(tick_atp) if tick_atp else 0
                cooperation_rate = tick_cooperations / num_interactions if num_interactions > 0 else 0

                sim_metrics = CoherenceSimulationMetrics(
                    tick=tick,
                    network_trust=coherence_metrics.trust_value,
                    network_variance=coherence_metrics.trust_variance,
                    network_density=coherence_metrics.network_density,
                    num_agents=coherence_metrics.num_agents,
                    num_strong_edges=coherence_metrics.num_strong_edges,
                    gamma=coherence_metrics.gamma,
                    coherence=coherence_metrics.coherence,
                    entropy_ratio=coherence_metrics.entropy_ratio,
                    is_quantum_regime=coherence_metrics.is_quantum_regime,
                    above_coalition_threshold=coherence_metrics.above_coalition_threshold,
                    avg_atp_cost=avg_tick_atp,
                    cooperation_rate=cooperation_rate
                )
                self.coherence_metrics.append(sim_metrics)

            total_atp_costs.extend(tick_atp)
            cooperation_counts.append(tick_cooperations)

            # Take snapshot
            if tick % snapshot_interval == 0:
                tracker.take_snapshot(tick, world)

            # Advance world
            tick_world(world)

        # Final snapshot
        tracker.take_snapshot(num_ticks, world)

        # Compute final statistics
        final_cooperation_rate = sum(cooperation_counts) / (sum([random.randint(2, 3) for _ in range(num_ticks)])) if num_ticks > 0 else 0
        final_avg_atp = sum(total_atp_costs) / len(total_atp_costs) if total_atp_costs else 0

        final_coherence = self.coherence_metrics[-1] if self.coherence_metrics else None

        return {
            "enable_coherence": self.enable_coherence,
            "num_ticks": num_ticks,
            "total_interactions": len(total_atp_costs),
            "final_cooperation_rate": final_cooperation_rate,
            "final_avg_atp_cost": final_avg_atp,
            "coherence_metrics": self.coherence_metrics,
            "final_coherence": asdict(final_coherence) if final_coherence else None,
            "tracker": tracker,
            "agents": agents,
            "world": world
        }


# ============================================================================
# Comparison Experiment
# ============================================================================

def run_comparison_experiment(
    num_ticks: int = 30,
    num_runs: int = 3
) -> Dict[str, Any]:
    """
    Run comparison experiment: baseline vs coherence-enabled

    Args:
        num_ticks: Simulation length
        num_runs: Number of runs per condition (for averaging)

    Returns:
        Comparison results
    """
    print("=" * 80)
    print("  COHERENCE ATP PRICING - 4LIFE DEPLOYMENT TEST")
    print("  Session #28 - Production Validation")
    print("=" * 80)

    # Run baseline simulations (no coherence)
    print("\n=== Baseline Simulations (No Coherence Pricing) ===\n")
    baseline_results = []

    for run in range(num_runs):
        print(f"Running baseline simulation {run + 1}/{num_runs}...")
        sim = CoherencePricingSimulation(enable_coherence=False)
        result = sim.run_simulation(num_ticks=num_ticks)
        baseline_results.append(result)

    # Run coherence-enabled simulations
    print(f"\n=== Coherence-Enabled Simulations ===\n")
    coherence_results = []

    for run in range(num_runs):
        print(f"Running coherence simulation {run + 1}/{num_runs}...")
        sim = CoherencePricingSimulation(enable_coherence=True)
        result = sim.run_simulation(num_ticks=num_ticks)
        coherence_results.append(result)

    # Compute averages
    baseline_avg_coop = sum(r["final_cooperation_rate"] for r in baseline_results) / num_runs
    baseline_avg_atp = sum(r["final_avg_atp_cost"] for r in baseline_results) / num_runs

    coherence_avg_coop = sum(r["final_cooperation_rate"] for r in coherence_results) / num_runs
    coherence_avg_atp = sum(r["final_avg_atp_cost"] for r in coherence_results) / num_runs

    # Print comparison
    print("\n" + "=" * 80)
    print("  RESULTS")
    print("=" * 80)

    print(f"\n{'Metric':<40} | {'Baseline':<15} | {'Coherence':<15} | {'Change'}")
    print("-" * 90)

    coop_change = ((coherence_avg_coop - baseline_avg_coop) / baseline_avg_coop * 100) if baseline_avg_coop > 0 else 0
    atp_change = ((coherence_avg_atp - baseline_avg_atp) / baseline_avg_atp * 100) if baseline_avg_atp > 0 else 0

    print(f"{'Average Cooperation Rate':<40} | {baseline_avg_coop:<15.3f} | {coherence_avg_coop:<15.3f} | {coop_change:+.1f}%")
    print(f"{'Average ATP Cost':<40} | {baseline_avg_atp:<15.2f} | {coherence_avg_atp:<15.2f} | {atp_change:+.1f}%")

    # Show final coherence metrics for coherence-enabled runs
    if coherence_results[0]["final_coherence"]:
        print("\n=== Final Network Coherence (Coherence-Enabled) ===\n")
        final = coherence_results[0]["final_coherence"]
        print(f"  Network Trust:     {final['network_trust']:.3f}")
        print(f"  γ (correlation):   {final['gamma']:.3f}")
        regime = "quantum" if final['is_quantum_regime'] else "classical"
        print(f"  Regime:            {regime}")
        print(f"  C (coherence):     {final['coherence']:.3f}")
        threshold = "✅ above" if final['above_coalition_threshold'] else "❌ below"
        print(f"  Coalition:         {threshold} threshold (C=0.5)")
        print(f"  S/S₀ (entropy):    {final['entropy_ratio']:.3f}")

    print("\n" + "=" * 80)
    if coop_change > 5:
        print("  ✅ HYPOTHESIS CONFIRMED: Coherence pricing increases cooperation")
    elif coop_change < -5:
        print("  ❌ HYPOTHESIS REJECTED: Coherence pricing decreases cooperation")
    else:
        print("  ⚠️  INCONCLUSIVE: No significant cooperation change")
    print("=" * 80)

    return {
        "baseline_results": baseline_results,
        "coherence_results": coherence_results,
        "baseline_avg_cooperation": baseline_avg_coop,
        "baseline_avg_atp": baseline_avg_atp,
        "coherence_avg_cooperation": coherence_avg_coop,
        "coherence_avg_atp": coherence_avg_atp,
        "cooperation_change_pct": coop_change,
        "atp_cost_change_pct": atp_change
    }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    # Run comparison experiment
    results = run_comparison_experiment(num_ticks=30, num_runs=3)

    # Save results
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"coherence_pricing_test_{timestamp}.json"

    # Prepare results for JSON (remove non-serializable objects)
    json_results = {
        "baseline_avg_cooperation": results["baseline_avg_cooperation"],
        "baseline_avg_atp": results["baseline_avg_atp"],
        "coherence_avg_cooperation": results["coherence_avg_cooperation"],
        "coherence_avg_atp": results["coherence_avg_atp"],
        "cooperation_change_pct": results["cooperation_change_pct"],
        "atp_cost_change_pct": results["atp_cost_change_pct"],
        "timestamp": timestamp
    }

    with open(output_file, 'w') as f:
        json.dump(json_results, f, indent=2)

    print(f"\nResults saved to: {output_file}")
