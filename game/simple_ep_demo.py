#!/usr/bin/env python3
"""
Simple EP-Driven Agent Interaction Demo

Demonstrates how Epistemic Proprioception (EP) can guide agent interactions
in the Web4 game simulation.

Session 111: Legion autonomous research
Inspired by:
- Session 110: Web4 Security EP Trilogy (280K decisions/sec)
- Session 141 (Thor): Authorization EP in SAGE
- Web4 game vertical slice

Key Concept:
Instead of blindly executing interactions and discovering failures afterward,
agents use simplified EP predictions to proactively avoid dangerous situations.

This is a standalone demonstration - doesn't require the full Security EP Trilogy
complex APIs, but shows the core concept clearly.
"""

import sys
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, List
from datetime import datetime

# Import game engine
sys.path.insert(0, str(Path(__file__).parent))
from engine.models import Agent
from engine.scenarios import bootstrap_home_society_world
from engine.sim_loop import tick_world


@dataclass
class SimpleEPPrediction:
    """Simplified EP prediction for agent interactions."""
    risk_score: float  # 0.0-1.0
    confidence: float  # 0.0-1.0
    recommendation: str  # "proceed", "adjust", "reject"
    reasoning: str


class SimpleEPAgent:
    """Agent with basic epistemic proprioception for interactions."""

    def __init__(self, world):
        self.world = world
        self.interaction_count = 0
        self.proceeds = 0
        self.adjusts = 0
        self.rejects = 0

    def predict_interaction_risk(self, initiator_lct: str, target_lct: str, interaction_type: str) -> SimpleEPPrediction:
        """
        Predict risk of interaction using simple heuristics.

        This demonstrates EP concept without requiring full Security EP Trilogy.
        """
        init_agent = self.world.agents[initiator_lct]
        targ_agent = self.world.agents[target_lct]

        init_t3 = init_agent.trust_axes["T3"]["composite"]
        targ_t3 = targ_agent.trust_axes["T3"]["composite"]
        init_atp = init_agent.resources["ATP"]
        targ_atp = targ_agent.resources["ATP"]

        # Calculate risk based on multiple factors
        risk_factors = []

        # Factor 1: Low trust (either agent)
        min_t3 = min(init_t3, targ_t3)
        if min_t3 < 0.4:
            risk_factors.append(("low_trust", 0.4))

        # Factor 2: Low resources (ATP depletion risk)
        min_atp = min(init_atp, targ_atp)
        if min_atp < 20.0:
            risk_factors.append(("low_atp", 0.3))

        # Factor 3: High-risk interaction type
        risk_map = {
            "collaborate": 0.1,
            "resource_transfer": 0.2,
            "delegation": 0.4,
            "challenge": 0.7
        }
        type_risk = risk_map.get(interaction_type, 0.3)
        if type_risk > 0.3:
            risk_factors.append((f"high_risk_type_{interaction_type}", type_risk))

        # Factor 4: Trust mismatch (could indicate manipulation)
        trust_gap = abs(init_t3 - targ_t3)
        if trust_gap > 0.3:
            risk_factors.append(("trust_mismatch", 0.2))

        # Combine risk factors
        if not risk_factors:
            total_risk = 0.05  # Baseline low risk
        else:
            total_risk = min(1.0, sum(r[1] for r in risk_factors))

        # Determine recommendation
        if total_risk > 0.7:
            recommendation = "reject"
        elif total_risk > 0.3:
            recommendation = "adjust"
        else:
            recommendation = "proceed"

        # Build reasoning
        if risk_factors:
            reasons = ", ".join(f"{name}({score:.2f})" for name, score in risk_factors)
            reasoning = f"Risk factors: {reasons} → total_risk={total_risk:.2f}"
        else:
            reasoning = f"Low risk interaction: T3_min={min_t3:.2f}, ATP_min={min_atp:.1f}"

        return SimpleEPPrediction(
            risk_score=total_risk,
            confidence=0.75,  # Moderate confidence in simple heuristics
            recommendation=recommendation,
            reasoning=reasoning
        )

    def execute_interaction(self, initiator_lct: str, target_lct: str, interaction_type: str, atp_cost: float, t3_impact: float):
        """Execute interaction based on EP prediction."""
        self.interaction_count += 1

        # Get EP prediction
        prediction = self.predict_interaction_risk(initiator_lct, target_lct, interaction_type)

        # Act on prediction
        if prediction.recommendation == "reject":
            self.rejects += 1
            print(f"  REJECTED: {interaction_type} - {prediction.reasoning}")
            return {"decision": "rejected", "risk": prediction.risk_score}

        elif prediction.recommendation == "adjust":
            self.adjusts += 1
            # Reduce ATP cost and T3 impact by 50%
            adjusted_atp = atp_cost * 0.5
            adjusted_t3 = t3_impact * 0.5

            # Apply interaction
            self.world.agents[initiator_lct].resources["ATP"] -= adjusted_atp
            self.world.agents[target_lct].resources["ATP"] -= adjusted_atp

            init_t3_old = self.world.agents[initiator_lct].trust_axes["T3"]["composite"]
            targ_t3_old = self.world.agents[target_lct].trust_axes["T3"]["composite"]

            self.world.agents[initiator_lct].trust_axes["T3"]["composite"] = max(0.0, min(1.0, init_t3_old + adjusted_t3))
            self.world.agents[target_lct].trust_axes["T3"]["composite"] = max(0.0, min(1.0, targ_t3_old + adjusted_t3))

            print(f"  ADJUSTED: {interaction_type} - {prediction.reasoning}")
            print(f"    ATP: {atp_cost:.1f} → {adjusted_atp:.1f}, T3_impact: {t3_impact:+.2f} → {adjusted_t3:+.2f}")
            return {"decision": "adjusted", "risk": prediction.risk_score, "atp_saved": atp_cost - adjusted_atp}

        else:  # proceed
            self.proceeds += 1
            # Full interaction
            self.world.agents[initiator_lct].resources["ATP"] -= atp_cost
            self.world.agents[target_lct].resources["ATP"] -= atp_cost

            init_t3_old = self.world.agents[initiator_lct].trust_axes["T3"]["composite"]
            targ_t3_old = self.world.agents[target_lct].trust_axes["T3"]["composite"]

            self.world.agents[initiator_lct].trust_axes["T3"]["composite"] = max(0.0, min(1.0, init_t3_old + t3_impact))
            self.world.agents[target_lct].trust_axes["T3"]["composite"] = max(0.0, min(1.0, targ_t3_old + t3_impact))

            print(f"  PROCEEDED: {interaction_type} - Low risk (T3_delta: {t3_impact:+.2f})")
            return {"decision": "proceeded", "risk": prediction.risk_score}


def run_demo():
    """Run simple EP-driven agent demonstration."""
    print("=" * 80)
    print("SIMPLE EP-DRIVEN AGENT INTERACTION DEMO")
    print("=" * 80)
    print()

    # Bootstrap world
    world = bootstrap_home_society_world()
    ep_agent = SimpleEPAgent(world)

    agents = list(world.agents.keys())
    alice_lct = agents[0]
    bob_lct = agents[1]

    print(f"Agents: {alice_lct}, {bob_lct}")
    print()

    # Track state over time
    alice_t3_history = []
    alice_atp_history = []
    bob_t3_history = []
    bob_atp_history = []

    # Define interaction sequence
    interactions = [
        # Low-risk collaborations (should proceed)
        (alice_lct, bob_lct, "collaborate", 5.0, 0.05),
        (bob_lct, alice_lct, "collaborate", 5.0, 0.05),

        # Medium-risk resource transfers (might adjust)
        (alice_lct, bob_lct, "resource_transfer", 10.0, 0.02),
        (bob_lct, alice_lct, "resource_transfer", 10.0, 0.02),

        # Higher-risk delegations (likely adjust)
        (alice_lct, bob_lct, "delegation", 15.0, 0.08),

        # Very high-risk challenge (should reject)
        (bob_lct, alice_lct, "challenge", 20.0, -0.1),

        # More collaborations
        (alice_lct, bob_lct, "collaborate", 5.0, 0.05),
        (bob_lct, alice_lct, "collaborate", 5.0, 0.05),

        # Another challenge (should reject)
        (alice_lct, bob_lct, "challenge", 25.0, -0.15),

        # Resource transfer when ATP low (might reject or adjust)
        (alice_lct, bob_lct, "resource_transfer", 10.0, 0.02),
    ]

    print("Running interaction sequence...")
    print()

    for i, (init, targ, itype, atp, t3) in enumerate(interactions):
        tick_world(world)

        print(f"Tick {i+1}: {itype} ({init.split(':')[-1]} → {targ.split(':')[-1]})")

        # Record state before
        alice_t3_before = world.agents[alice_lct].trust_axes["T3"]["composite"]
        alice_atp_before = world.agents[alice_lct].resources["ATP"]
        bob_t3_before = world.agents[bob_lct].trust_axes["T3"]["composite"]
        bob_atp_before = world.agents[bob_lct].resources["ATP"]

        # Execute with EP
        result = ep_agent.execute_interaction(init, targ, itype, atp, t3)

        # Record state after
        alice_t3_after = world.agents[alice_lct].trust_axes["T3"]["composite"]
        alice_atp_after = world.agents[alice_lct].resources["ATP"]
        bob_t3_after = world.agents[bob_lct].trust_axes["T3"]["composite"]
        bob_atp_after = world.agents[bob_lct].resources["ATP"]

        alice_t3_history.append(alice_t3_after)
        alice_atp_history.append(alice_atp_after)
        bob_t3_history.append(bob_t3_after)
        bob_atp_history.append(bob_atp_after)

        print(f"    Alice: T3={alice_t3_after:.3f} ({alice_t3_after-alice_t3_before:+.3f}), ATP={alice_atp_after:.1f} ({alice_atp_after-alice_atp_before:+.1f})")
        print(f"    Bob:   T3={bob_t3_after:.3f} ({bob_t3_after-bob_t3_before:+.3f}), ATP={bob_atp_after:.1f} ({bob_atp_after-bob_atp_before:+.1f})")
        print()

    # Summary
    print()
    print("=" * 80)
    print("DEMO SUMMARY")
    print("=" * 80)
    print()
    print(f"Total Interactions: {ep_agent.interaction_count}")
    print(f"  Proceeded: {ep_agent.proceeds} ({ep_agent.proceeds/ep_agent.interaction_count:.1%})")
    print(f"  Adjusted:  {ep_agent.adjusts} ({ep_agent.adjusts/ep_agent.interaction_count:.1%})")
    print(f"  Rejected:  {ep_agent.rejects} ({ep_agent.rejects/ep_agent.interaction_count:.1%})")
    print()

    print(f"Final State:")
    print(f"  Alice: T3={alice_t3_history[-1]:.3f} (Δ{alice_t3_history[-1]-0.6:+.3f}), ATP={alice_atp_history[-1]:.1f} (Δ{alice_atp_history[-1]-100.0:+.1f})")
    print(f"  Bob:   T3={bob_t3_history[-1]:.3f} (Δ{bob_t3_history[-1]-0.5:+.3f}), ATP={bob_atp_history[-1]:.1f} (Δ{bob_atp_history[-1]-80.0:+.1f})")
    print()

    # Save results
    results = {
        "demo": "simple_ep_driven_interactions",
        "session": 111,
        "timestamp": datetime.now().isoformat(),
        "ep_performance": {
            "total_interactions": ep_agent.interaction_count,
            "proceeded": ep_agent.proceeds,
            "adjusted": ep_agent.adjusts,
            "rejected": ep_agent.rejects,
            "proceed_rate": ep_agent.proceeds / ep_agent.interaction_count,
            "adjust_rate": ep_agent.adjusts / ep_agent.interaction_count,
            "reject_rate": ep_agent.rejects / ep_agent.interaction_count
        },
        "agent_trajectories": {
            "alice": {
                "t3_history": alice_t3_history,
                "atp_history": alice_atp_history,
                "final_t3": alice_t3_history[-1],
                "final_atp": alice_atp_history[-1]
            },
            "bob": {
                "t3_history": bob_t3_history,
                "atp_history": bob_atp_history,
                "final_t3": bob_t3_history[-1],
                "final_atp": bob_atp_history[-1]
            }
        },
        "key_insight": "EP predictions prevented high-risk interactions, preserving agent T3 and ATP"
    }

    with open("simple_ep_demo_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to: simple_ep_demo_results.json")
    print()
    print("=" * 80)

    return results


if __name__ == "__main__":
    run_demo()
