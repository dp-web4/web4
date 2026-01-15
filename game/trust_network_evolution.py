#!/usr/bin/env python3
"""
Trust Network Evolution Simulation

Session #11: Legion 4-Life autonomous research
Goal: Demonstrate how trust networks form, strengthen, and evolve through agent interactions

This simulation creates a small society of 5-7 agents with different behavioral profiles:
- Cooperator: Helps others, builds trust steadily
- Opportunist: Helps when convenient, mixed trust signals
- Free-rider: Takes without giving, loses trust
- Learner: Starts naive, learns from consequences
- Maverick: High-risk high-reward, volatile trust

Key Innovations for 4-Life Visualization:
1. Agent-to-agent trust tracking (not just individual karma)
2. Trust edge evolution (formation, strengthening, decay)
3. Network topology changes (connections form/break)
4. Emergent coalitions (trusted subgroups)
5. Trust cascade events (one failure affects network)

Output Format:
- Timestamped trust network snapshots
- Agent interaction events with trust impacts
- Coalition formation/dissolution events
- Trust cascade detection
- Network metrics (density, centralization, clustering)
"""

import sys
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Add Web4 game engine
game_dir = Path(__file__).parent
sys.path.insert(0, str(game_dir))

from engine.models import Agent, Society, World, ContextEdge
from engine.scenarios import bootstrap_home_society_world
from engine.sim_loop import tick_world
from engine.agent_actions import apply_policy_action


# ============================================================================
# Agent Behavioral Profiles
# ============================================================================

@dataclass
class BehavioralProfile:
    """Defines an agent's behavioral tendencies"""
    name: str
    cooperation_rate: float  # 0-1: likelihood to help others
    reliability: float  # 0-1: consistency in following through
    risk_tolerance: float  # 0-1: willingness to try risky actions
    learning_rate: float  # 0-1: how quickly they adapt from experience
    description: str


BEHAVIORAL_PROFILES = {
    "cooperator": BehavioralProfile(
        name="Cooperator",
        cooperation_rate=0.9,
        reliability=0.85,
        risk_tolerance=0.3,
        learning_rate=0.5,
        description="Helps others consistently, builds trust steadily through reliability"
    ),
    "opportunist": BehavioralProfile(
        name="Opportunist",
        cooperation_rate=0.5,
        reliability=0.6,
        risk_tolerance=0.6,
        learning_rate=0.7,
        description="Helps when convenient, mixed trust signals, adapts to incentives"
    ),
    "freerider": BehavioralProfile(
        name="Free-Rider",
        cooperation_rate=0.2,
        reliability=0.4,
        risk_tolerance=0.8,
        learning_rate=0.3,
        description="Takes without giving, loses trust over time, slow to learn"
    ),
    "learner": BehavioralProfile(
        name="Learner",
        cooperation_rate=0.5,
        reliability=0.5,
        risk_tolerance=0.5,
        learning_rate=0.9,
        description="Starts naive, learns quickly from consequences, trust evolves"
    ),
    "maverick": BehavioralProfile(
        name="Maverick",
        cooperation_rate=0.6,
        reliability=0.5,
        risk_tolerance=0.9,
        learning_rate=0.6,
        description="High-risk high-reward, volatile trust, creates drama"
    ),
}


# ============================================================================
# Trust Network Tracking
# ============================================================================

@dataclass
class TrustEdge:
    """Represents trust from source to target agent"""
    source_lct: str
    target_lct: str
    trust_value: float  # 0-1
    interactions: int
    last_interaction_tick: int
    formation_tick: int
    edge_type: str  # "forming", "stable", "degrading", "broken"


@dataclass
class TrustNetworkSnapshot:
    """Snapshot of trust network at a point in time"""
    tick: int
    agents: List[Dict[str, Any]]  # agent state
    edges: List[Dict[str, Any]]  # trust edges
    coalitions: List[List[str]]  # groups of mutually trusting agents
    metrics: Dict[str, float]  # network metrics


@dataclass
class InteractionEvent:
    """Records an agent-to-agent interaction"""
    tick: int
    source_lct: str
    target_lct: str
    action_type: str
    cooperation: bool  # Did source cooperate with target?
    trust_change: float
    reason: str


class TrustNetworkTracker:
    """Tracks evolution of trust network over time"""

    def __init__(self):
        self.edges: Dict[Tuple[str, str], TrustEdge] = {}
        self.snapshots: List[TrustNetworkSnapshot] = []
        self.events: List[InteractionEvent] = []
        self.trust_threshold = 0.5  # Minimum trust for coalition membership

    def record_interaction(
        self,
        tick: int,
        source_lct: str,
        target_lct: str,
        action_type: str,
        cooperation: bool,
        trust_change: float,
        reason: str
    ):
        """Record agent-to-agent interaction"""
        # Update or create edge
        edge_key = (source_lct, target_lct)

        if edge_key not in self.edges:
            self.edges[edge_key] = TrustEdge(
                source_lct=source_lct,
                target_lct=target_lct,
                trust_value=0.5,  # Neutral starting trust
                interactions=0,
                last_interaction_tick=tick,
                formation_tick=tick,
                edge_type="forming"
            )

        edge = self.edges[edge_key]
        edge.interactions += 1
        edge.last_interaction_tick = tick
        edge.trust_value = max(0.0, min(1.0, edge.trust_value + trust_change))

        # Update edge type based on trust trajectory
        if edge.interactions < 3:
            edge.edge_type = "forming"
        elif trust_change < -0.05:
            edge.edge_type = "degrading"
        elif edge.trust_value < 0.3:
            edge.edge_type = "broken"
        else:
            edge.edge_type = "stable"

        # Record event
        self.events.append(InteractionEvent(
            tick=tick,
            source_lct=source_lct,
            target_lct=target_lct,
            action_type=action_type,
            cooperation=cooperation,
            trust_change=trust_change,
            reason=reason
        ))

    def take_snapshot(self, tick: int, world: World):
        """Capture current state of trust network"""
        # Agent states
        agents = []
        for agent_lct, agent in world.agents.items():
            agents.append({
                "agent_lct": agent_lct,
                "name": agent.name,
                "atp": agent.resources.get("ATP", 0.0),
                "trust_composite": agent.trust_axes.get("T3", {}).get("composite", 0.5),
            })

        # Trust edges
        edges = []
        for edge_key, edge in self.edges.items():
            edges.append({
                "source": edge.source_lct,
                "target": edge.target_lct,
                "trust": edge.trust_value,
                "interactions": edge.interactions,
                "type": edge.edge_type,
                "age": tick - edge.formation_tick
            })

        # Detect coalitions
        coalitions = self._detect_coalitions()

        # Calculate network metrics
        metrics = self._calculate_network_metrics()

        snapshot = TrustNetworkSnapshot(
            tick=tick,
            agents=agents,
            edges=edges,
            coalitions=coalitions,
            metrics=metrics
        )

        self.snapshots.append(snapshot)

    def _detect_coalitions(self) -> List[List[str]]:
        """Detect groups of mutually trusting agents"""
        # Simple coalition detection: find connected components where all edges > threshold
        agents = set()
        for edge_key in self.edges:
            agents.add(edge_key[0])
            agents.add(edge_key[1])

        # For now, simple version: group agents with bidirectional trust > threshold
        coalitions = []
        processed = set()

        for agent in agents:
            if agent in processed:
                continue

            coalition = [agent]
            processed.add(agent)

            # Find agents this agent trusts and who trust back
            for other in agents:
                if other == agent or other in processed:
                    continue

                forward_edge = self.edges.get((agent, other))
                backward_edge = self.edges.get((other, agent))

                if (forward_edge and forward_edge.trust_value >= self.trust_threshold and
                    backward_edge and backward_edge.trust_value >= self.trust_threshold):
                    coalition.append(other)
                    processed.add(other)

            if len(coalition) > 1:
                coalitions.append(coalition)

        return coalitions

    def _calculate_network_metrics(self) -> Dict[str, float]:
        """Calculate network-level trust metrics"""
        if not self.edges:
            return {
                "density": 0.0,
                "avg_trust": 0.0,
                "trust_variance": 0.0,
                "strong_edges": 0,
                "broken_edges": 0
            }

        trust_values = [e.trust_value for e in self.edges.values()]
        strong_edges = sum(1 for e in self.edges.values() if e.trust_value >= 0.7)
        broken_edges = sum(1 for e in self.edges.values() if e.trust_value < 0.3)

        return {
            "density": len(self.edges) / max(1, len(set(e[0] for e in self.edges)) * len(set(e[1] for e in self.edges))),
            "avg_trust": sum(trust_values) / len(trust_values),
            "trust_variance": sum((t - sum(trust_values)/len(trust_values))**2 for t in trust_values) / len(trust_values),
            "strong_edges": strong_edges,
            "broken_edges": broken_edges
        }


# ============================================================================
# Simulation Runner
# ============================================================================

def create_trust_network_world() -> Tuple[World, Dict[str, Agent], TrustNetworkTracker]:
    """Create a world with diverse agents for trust network evolution"""

    # Bootstrap basic world
    world = bootstrap_home_society_world()

    # Clear default agents
    world.agents.clear()

    # Create agents with different behavioral profiles
    agent_configs = [
        ("alice", "cooperator"),
        ("bob", "opportunist"),
        ("charlie", "freerider"),
        ("diana", "learner"),
        ("eve", "maverick"),
    ]

    agents = {}
    agent_profiles = {}  # Track profiles separately
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
            capabilities={"behavioral_profile": float(hash(profile_key) % 100)}  # Store profile indicator
        )
        world.add_agent(agent)
        agents[name] = agent
        agent_profiles[agent.agent_lct] = profile_key

    tracker = TrustNetworkTracker()

    return world, agents, tracker, agent_profiles


def simulate_agent_interaction(
    world: World,
    source: Agent,
    target: Agent,
    profile: BehavioralProfile,
    tracker: TrustNetworkTracker,
    tick: int
) -> Dict[str, Any]:
    """Simulate interaction between two agents based on source's behavioral profile"""

    # Determine if source cooperates with target
    import random
    cooperates = random.random() < profile.cooperation_rate

    # Determine action type based on cooperation
    if cooperates:
        action_type = "help"
        atp_cost = 10.0
        trust_change = 0.05 if random.random() < profile.reliability else -0.02
        reason = f"{source.name} helps {target.name} (cooperator tendency)"
    else:
        action_type = "ignore"
        atp_cost = 2.0
        trust_change = -0.03
        reason = f"{source.name} ignores {target.name} (self-interest)"

    # Apply ATP cost
    source.resources["ATP"] = max(0.0, source.resources["ATP"] - atp_cost)

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
        "atp_cost": atp_cost
    }


def run_trust_network_simulation(
    num_ticks: int = 30,
    snapshot_interval: int = 5
) -> Dict[str, Any]:
    """Run trust network evolution simulation"""

    world, agents, tracker, agent_profiles = create_trust_network_world()

    # Run simulation
    import random
    agent_list = list(agents.values())

    for tick in range(1, num_ticks + 1):
        # Each tick, simulate 2-3 random interactions
        num_interactions = random.randint(2, 3)

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
        "simulation_type": "trust_network_evolution",
        "num_ticks": num_ticks,
        "num_agents": len(agents),
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
            "generator": "trust_network_evolution.py",
            "session": "Legion Session #11"
        }
    }

    return results


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("Running Trust Network Evolution Simulation...")
    print("=" * 60)

    results = run_trust_network_simulation(num_ticks=30, snapshot_interval=5)

    # Save results
    output_dir = Path(__file__).parent.parent.parent / "4-life" / "public"
    output_path = output_dir / "trust_network_evolution.json"

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Simulation complete!")
    print(f"📊 Generated {len(results['snapshots'])} network snapshots")
    print(f"🤝 Recorded {len(results['events'])} interactions")
    print(f"💾 Saved to: {output_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("TRUST NETWORK SUMMARY")
    print("=" * 60)

    final_snapshot = results["snapshots"][-1]
    print(f"\nFinal Network Metrics (Tick {final_snapshot['tick']}):")
    for key, value in final_snapshot["metrics"].items():
        print(f"  {key}: {value:.3f}")

    print(f"\nCoalitions Formed: {len(final_snapshot['coalitions'])}")
    for i, coalition in enumerate(final_snapshot['coalitions']):
        agent_names = [a.split(":")[-1].capitalize() for a in coalition]
        print(f"  Coalition {i+1}: {', '.join(agent_names)}")

    print(f"\nAgent Final States:")
    for agent in results["agents"]:
        print(f"  {agent['name']} ({agent['profile']}): ATP={agent['final_atp']:.1f}, Trust={agent['final_trust']:.2f}")
