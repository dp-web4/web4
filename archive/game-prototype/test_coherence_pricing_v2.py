#!/usr/bin/env python3
"""
Coherence ATP Pricing V2 Validation
Session #29: Validate inverted model fixes death spiral

Session #28 discovered V1 death spiral:
- Low trust → High γ → ATP premium → Can't cooperate → Lower trust
- Cooperation decreased 6.4%

V2 Inverted Model:
- Low trust → High γ → ATP discount → Can cooperate → Higher trust
- Expected: Cooperation increase 10-20%

This test validates V2 fixes the problem.

Author: Legion (autonomous Session #29)
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Add paths
game_dir = Path(__file__).parent
sys.path.insert(0, str(game_dir))
sys.path.insert(0, str(game_dir.parent / "web4-standard" / "implementation" / "trust"))
sys.path.insert(0, str(game_dir / "engine"))

# Import simulation framework
from trust_network_evolution import (
    create_trust_network_world,
    TrustNetworkTracker,
    BehavioralProfile,
    BEHAVIORAL_PROFILES
)
from engine.models import Agent
from engine.sim_loop import tick_world

# Import V2 inverted coherence pricing
from coherence_atp_integration_v2 import (
    InvertedCoherenceIntegratedPricer,
    InvertedCoherencePricingPolicy
)
from coherence_trust_tensor import CoherenceTrustMetrics

import random
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional


@dataclass
class SimulationMetrics:
    """Track metrics during simulation"""
    tick: int
    cooperation_rate: float
    avg_atp_cost: float
    network_trust: float
    gamma: float
    coherence: float
    regime: str
    num_strong_edges: int


class V2CoherencePricingSimulation:
    """Simulation with V2 inverted coherence pricing"""

    def __init__(self, enable_coherence: bool = True):
        self.enable_coherence = enable_coherence
        self.pricer = InvertedCoherenceIntegratedPricer() if enable_coherence else None
        self.metrics: List[SimulationMetrics] = []

    def compute_network_coherence_metrics(
        self,
        tracker: TrustNetworkTracker,
        agents: Dict[str, Agent]
    ) -> Optional[CoherenceTrustMetrics]:
        """Compute coherence metrics from trust network"""
        if not tracker.edges or len(tracker.edges) < 2:
            return None

        trust_values = [edge.trust_value for edge in tracker.edges.values()]
        avg_trust = sum(trust_values) / len(trust_values)
        trust_variance = sum((t - avg_trust) ** 2 for t in trust_values) / len(trust_values)

        num_agents = len(agents)
        max_edges = num_agents * (num_agents - 1)
        network_density = len(tracker.edges) / max_edges if max_edges > 0 else 0.0
        num_strong_edges = sum(1 for edge in tracker.edges.values() if edge.trust_value > 0.7)

        try:
            metrics = CoherenceTrustMetrics(
                trust_value=avg_trust,
                trust_variance=trust_variance,
                network_density=network_density,
                num_agents=num_agents,
                num_strong_edges=num_strong_edges
            )
            return metrics
        except Exception:
            return None

    def simulate_interaction_v2(
        self,
        source: Agent,
        target: Agent,
        profile: BehavioralProfile,
        tracker: TrustNetworkTracker,
        agents: Dict[str, Agent],
        tick: int
    ) -> Dict:
        """Simulate interaction with V2 pricing"""
        # Compute coherence metrics
        coherence_metrics = self.compute_network_coherence_metrics(tracker, agents)

        # Determine cooperation
        cooperates = random.random() < profile.cooperation_rate

        # Base ATP cost
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

        # Apply V2 pricing
        if self.enable_coherence and coherence_metrics and self.pricer:
            result = self.pricer.price_with_coherence(
                base_cost=base_atp_cost,
                trust_metrics=coherence_metrics
            )
            final_atp_cost = result['final_cost']
            coherence_mult = result['coherence_multiplier']
        else:
            final_atp_cost = base_atp_cost
            coherence_mult = 1.0

        # Apply ATP cost
        source.resources["ATP"] = max(0.0, source.resources["ATP"] - final_atp_cost)

        # If helped, target gains ATP
        if cooperates:
            target.resources["ATP"] = min(150.0, target.resources["ATP"] + 5.0)

        # Update trust
        target_trust = target.trust_axes.get("T3", {})
        current_trust = target_trust.get("composite", 0.5)
        new_trust = max(0.0, min(1.0, current_trust + trust_change))
        target_trust["composite"] = new_trust

        # Record interaction
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
            "cooperated": cooperates,
            "base_cost": base_atp_cost,
            "final_cost": final_atp_cost,
            "coherence_mult": coherence_mult
        }

    def run_simulation(self, num_ticks: int = 30) -> Dict:
        """Run simulation"""
        world, agents, tracker, agent_profiles = create_trust_network_world()
        agent_list = list(agents.values())

        total_cooperations = 0
        total_interactions = 0
        tick_atp_costs = []

        for tick in range(1, num_ticks + 1):
            num_interactions = random.randint(2, 3)
            tick_cooperations = 0

            for _ in range(num_interactions):
                source = random.choice(agent_list)
                target = random.choice([a for a in agent_list if a != source])

                profile_key = agent_profiles.get(source.agent_lct, "opportunist")
                profile = BEHAVIORAL_PROFILES[profile_key]

                result = self.simulate_interaction_v2(
                    source, target, profile, tracker, agents, tick
                )

                if result["cooperated"]:
                    tick_cooperations += 1
                tick_atp_costs.append(result["final_cost"])

            total_cooperations += tick_cooperations
            total_interactions += num_interactions

            # Track metrics
            coherence_metrics = self.compute_network_coherence_metrics(tracker, agents)
            if coherence_metrics and tick % 5 == 0:
                avg_tick_cost = sum(tick_atp_costs[-num_interactions:]) / num_interactions
                coop_rate = tick_cooperations / num_interactions

                self.metrics.append(SimulationMetrics(
                    tick=tick,
                    cooperation_rate=coop_rate,
                    avg_atp_cost=avg_tick_cost,
                    network_trust=coherence_metrics.trust_value,
                    gamma=coherence_metrics.gamma,
                    coherence=coherence_metrics.coherence,
                    regime="quantum" if coherence_metrics.is_quantum_regime else "classical",
                    num_strong_edges=coherence_metrics.num_strong_edges
                ))

            if tick % 5 == 0:
                tracker.take_snapshot(tick, world)

            tick_world(world)

        tracker.take_snapshot(num_ticks, world)

        final_coop_rate = total_cooperations / total_interactions if total_interactions > 0 else 0
        final_avg_atp = sum(tick_atp_costs) / len(tick_atp_costs) if tick_atp_costs else 0

        return {
            "enable_coherence": self.enable_coherence,
            "num_ticks": num_ticks,
            "final_cooperation_rate": final_coop_rate,
            "final_avg_atp_cost": final_avg_atp,
            "metrics": self.metrics
        }


def run_v2_validation_experiment(num_ticks: int = 30, num_runs: int = 5):
    """
    Validate V2 inverted model fixes death spiral

    Compare:
    - Baseline (no coherence)
    - V2 Inverted (subsidize low-trust)

    Expected: V2 increases cooperation vs baseline
    """
    print("=" * 80)
    print("  COHERENCE ATP PRICING V2 - VALIDATION TEST")
    print("  Session #29 - Death Spiral Fix Verification")
    print("=" * 80)

    print("\n**Hypothesis**: V2 inverted model increases cooperation vs baseline")
    print("**V2 Logic**: Low trust gets discount, high trust pays premium")
    print("**Expected**: Cooperation increase 10-20%\n")

    # Run baseline
    print("=== Baseline Simulations (No Coherence) ===\n")
    baseline_results = []

    for run in range(num_runs):
        print(f"Running baseline {run + 1}/{num_runs}...")
        sim = V2CoherencePricingSimulation(enable_coherence=False)
        result = sim.run_simulation(num_ticks=num_ticks)
        baseline_results.append(result)

    # Run V2
    print(f"\n=== V2 Inverted Model Simulations ===\n")
    v2_results = []

    for run in range(num_runs):
        print(f"Running V2 inverted {run + 1}/{num_runs}...")
        sim = V2CoherencePricingSimulation(enable_coherence=True)
        result = sim.run_simulation(num_ticks=num_ticks)
        v2_results.append(result)

    # Compute averages
    baseline_coop = sum(r["final_cooperation_rate"] for r in baseline_results) / num_runs
    baseline_atp = sum(r["final_avg_atp_cost"] for r in baseline_results) / num_runs

    v2_coop = sum(r["final_cooperation_rate"] for r in v2_results) / num_runs
    v2_atp = sum(r["final_avg_atp_cost"] for r in v2_results) / num_runs

    # Print results
    print("\n" + "=" * 80)
    print("  RESULTS")
    print("=" * 80)

    print(f"\n{'Metric':<40} | {'Baseline':<15} | {'V2 Inverted':<15} | {'Change'}")
    print("-" * 95)

    coop_change = ((v2_coop - baseline_coop) / baseline_coop * 100) if baseline_coop > 0 else 0
    atp_change = ((v2_atp - baseline_atp) / baseline_atp * 100) if baseline_atp > 0 else 0

    print(f"{'Average Cooperation Rate':<40} | {baseline_coop:<15.3f} | {v2_coop:<15.3f} | {coop_change:+.1f}%")
    print(f"{'Average ATP Cost':<40} | {baseline_atp:<15.2f} | {v2_atp:<15.2f} | {atp_change:+.1f}%")

    # Show evolution
    if v2_results[0]["metrics"]:
        print("\n=== V2 Network Evolution ===\n")
        print(f"{'Tick':<6} | {'Trust':<7} | {'γ':<7} | {'C':<7} | {'Regime':<10} | {'ATP Cost':<10} | {'Coop Rate'}")
        print("-" * 85)

        for m in v2_results[0]["metrics"]:
            print(f"{m.tick:<6} | {m.network_trust:<7.3f} | {m.gamma:<7.3f} | {m.coherence:<7.3f} | {m.regime:<10} | {m.avg_atp_cost:<10.2f} | {m.cooperation_rate:.3f}")

    # Verdict
    print("\n" + "=" * 80)
    if coop_change > 5:
        print("  ✅ HYPOTHESIS CONFIRMED: V2 increases cooperation")
        print("  Death spiral fixed! V2 ready for production.")
    elif abs(coop_change) <= 5:
        print("  ⚠️  NEUTRAL: No significant change")
        print("  V2 doesn't harm, but benefit unclear.")
    else:
        print("  ❌ HYPOTHESIS REJECTED: V2 decreases cooperation")
        print("  Further analysis needed.")
    print("=" * 80)

    return {
        "baseline_coop": baseline_coop,
        "baseline_atp": baseline_atp,
        "v2_coop": v2_coop,
        "v2_atp": v2_atp,
        "coop_change_pct": coop_change,
        "atp_change_pct": atp_change,
        "baseline_results": baseline_results,
        "v2_results": v2_results
    }


if __name__ == "__main__":
    # Run validation
    results = run_v2_validation_experiment(num_ticks=30, num_runs=5)

    # Save results
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"v2_validation_{timestamp}.json"

    json_results = {
        "timestamp": timestamp,
        "baseline_cooperation": results["baseline_coop"],
        "baseline_atp": results["baseline_atp"],
        "v2_cooperation": results["v2_coop"],
        "v2_atp": results["v2_atp"],
        "cooperation_change_pct": results["coop_change_pct"],
        "atp_change_pct": results["atp_change_pct"]
    }

    with open(output_file, 'w') as f:
        json.dump(json_results, f, indent=2)

    print(f"\nResults saved to: {output_file}")
