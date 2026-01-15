#!/usr/bin/env python3
"""
High-Cooperation Trust Network Simulation

Thor Autonomous Session - January 15, 2026 (Continuation)

GOAL: Test P_THOR_3 - Coalition formation at C ~ 0.5 threshold

HYPOTHESIS: In high-cooperation environment, agents will form coalitions
when mutual trust creates coherence C > 0.5

EXPERIMENTAL DESIGN:
- Use mostly cooperators + learners (high cooperation rates)
- Longer simulation (50 ticks vs 30)
- More interactions per tick (4-6 vs 2-3)
- Track coalition emergence and coherence

PREDICTION P_THOR_3:
- Coalitions form when mutual trust > 0.5
- Coalition coherence C ~ 0.5 ± 0.2
- Coalition members have bidirectional trust > 0.5

This tests the universal C = 0.5 threshold (consciousness/existence boundary)
in social domain.
"""

import sys
import json
from pathlib import Path

# Add Web4 game engine
game_dir = Path(__file__).parent
sys.path.insert(0, str(game_dir))

from trust_network_evolution import (
    create_trust_network_world,
    simulate_agent_interaction,
    BEHAVIORAL_PROFILES,
    Agent
)


def create_high_cooperation_world():
    """Create world with high-cooperation agents"""
    from engine.models import World

    # Bootstrap basic world
    from engine.scenarios import bootstrap_home_society_world
    world = bootstrap_home_society_world()
    world.agents.clear()

    # High-cooperation agent mix
    agent_configs = [
        ("alice", "cooperator"),
        ("bob", "cooperator"),
        ("charlie", "learner"),      # Learns to cooperate
        ("diana", "cooperator"),
        ("eve", "learner"),           # Learns to cooperate
        ("frank", "opportunist"),     # One opportunist for contrast
        ("grace", "cooperator"),
    ]

    agents = {}
    agent_profiles = {}

    for name, profile_key in agent_configs:
        profile = BEHAVIORAL_PROFILES[profile_key]
        agent = Agent(
            agent_lct=f"lct:web4:agent:{name}",
            name=name.capitalize(),
            trust_axes={
                "T3": {
                    "competence": 0.5,
                    "reliability": profile.reliability,
                    "integrity": 0.5,
                    "composite": 0.5
                }
            },
            resources={"ATP": 100.0},
            capabilities={"behavioral_profile": float(hash(profile_key) % 100)}
        )
        world.add_agent(agent)
        agents[name] = agent
        agent_profiles[agent.agent_lct] = profile_key

    from trust_network_evolution import TrustNetworkTracker
    tracker = TrustNetworkTracker()

    return world, agents, tracker, agent_profiles


def run_high_cooperation_simulation(
    num_ticks: int = 50,
    snapshot_interval: int = 5
):
    """Run high-cooperation trust network simulation"""
    import random
    from engine.sim_loop import tick_world
    from datetime import datetime

    world, agents, tracker, agent_profiles = create_high_cooperation_world()

    agent_list = list(agents.values())

    for tick in range(1, num_ticks + 1):
        # More interactions per tick in high-cooperation environment
        num_interactions = random.randint(4, 6)

        for _ in range(num_interactions):
            # Pick two different agents
            source = random.choice(agent_list)
            target = random.choice([a for a in agent_list if a != source])

            # Get source's behavioral profile
            profile_key = agent_profiles.get(source.agent_lct, "opportunist")
            profile = BEHAVIORAL_PROFILES[profile_key]

            # Simulate interaction
            simulate_agent_interaction(world, source, target, profile, tracker, tick)

        # Take snapshot at intervals
        if tick % snapshot_interval == 0:
            tracker.take_snapshot(tick, world)

        # Advance world
        tick_world(world)

    # Final snapshot
    tracker.take_snapshot(num_ticks, world)

    # Compile results
    results = {
        "simulation_type": "trust_network_high_cooperation",
        "experiment": "P_THOR_3_coalition_threshold_test",
        "num_ticks": num_ticks,
        "num_agents": len(agents),
        "agent_composition": {
            "cooperators": 4,
            "learners": 2,
            "opportunists": 1
        },
        "agents": [
            {
                "name": agent.name,
                "lct": agent.agent_lct,
                "profile": agent_profiles.get(agent.agent_lct, "unknown"),
                "profile_description": BEHAVIORAL_PROFILES[agent_profiles.get(agent.agent_lct, "opportunist")].description,
                "final_atp": agent.resources.get("ATP", 0.0),
                "final_trust": agent.trust_axes.get("T3", {}).get("composite", 0.5)
            }
            for agent in agent_list
        ],
        "snapshots": [
            {
                "tick": s.tick,
                "agents": s.agents,
                "edges": s.edges,
                "coalitions": s.coalitions,
                "metrics": s.metrics
            }
            for s in tracker.snapshots
        ],
        "events": [
            {
                "tick": e.tick,
                "source": e.source_lct,
                "target": e.target_lct,
                "action": e.action_type,
                "cooperation": e.cooperation,
                "trust_change": e.trust_change,
                "reason": e.reason
            }
            for e in tracker.events
        ],
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "generator": "trust_network_high_cooperation.py",
            "session": "Thor Autonomous Session (continuation)",
            "hypothesis": "Coalition formation at C ~ 0.5",
            "prediction": "P_THOR_3"
        }
    }

    return results


if __name__ == "__main__":
    print("High-Cooperation Trust Network Simulation")
    print("=" * 60)
    print("Testing P_THOR_3: Coalition formation at C ~ 0.5")
    print("=" * 60)

    results = run_high_cooperation_simulation(num_ticks=50, snapshot_interval=5)

    # Save results
    output_dir = Path(__file__).parent.parent.parent / "4-life" / "public"
    output_path = output_dir / "trust_network_high_cooperation.json"

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Simulation complete!")
    print(f"📊 Generated {len(results['snapshots'])} network snapshots")
    print(f"🤝 Recorded {len(results['events'])} interactions")
    print(f"💾 Saved to: {output_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("HIGH-COOPERATION NETWORK SUMMARY")
    print("=" * 60)

    final_snapshot = results["snapshots"][-1]
    print(f"\nFinal Network Metrics (Tick {final_snapshot['tick']}):")
    for key, value in final_snapshot["metrics"].items():
        print(f"  {key}: {value:.3f}")

    print(f"\n🤝 Coalitions Formed: {len(final_snapshot['coalitions'])}")
    if final_snapshot['coalitions']:
        for i, coalition in enumerate(final_snapshot['coalitions']):
            agent_names = [a.split(":")[-1].capitalize() for a in coalition]
            print(f"  Coalition {i+1} ({len(coalition)} members): {', '.join(agent_names)}")
    else:
        print("  (No coalitions formed)")

    print(f"\n👥 Agent Final States:")
    for agent in results["agents"]:
        print(f"  {agent['name']} ({agent['profile']}): ATP={agent['final_atp']:.1f}, Trust={agent['final_trust']:.2f}")

    print("\n" + "=" * 60)
    print("🔬 Run coherence analysis to validate P_THOR_3")
    print("   cd ~/ai-workspace/synchronism/Research/Social_Coherence")
    print("   python3 trust_coherence_analyzer.py")
    print("=" * 60)
