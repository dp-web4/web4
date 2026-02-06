#!/usr/bin/env python3
"""
EP-Driven Closed-Loop Multi-Life Runner

Session 114: Legion autonomous research
Integrates EP-driven policy with Cascade's closed-loop multi-life framework.

This demonstrates the complete integration:
1. Web4 game engine (multi-life with karma carry-forward)
2. EP-driven policy (learning from patterns)
3. Closed-loop actions (proposals applied to world state)

Comparison to Cascade's `closed_loop_multi_life.py`:
- Uses EPDrivenPolicy instead of simple heuristic ResearchAgentDriver
- Learns from outcomes over multiple lives
- Maturation progression: IMMATURE → LEARNING → MATURE

Usage:
    python run_ep_driven_closed_loop.py

Output:
    JSON with multi-life results + EP learning statistics
"""

import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import asdict

# Add modules
sys.path.insert(0, str(Path(__file__).parent))

from engine.models import Agent, Society, World, LifeRecord
from engine.scenarios import bootstrap_home_society_world
from engine.sim_loop import tick_world
from engine.agent_actions import apply_policy_action, applied_action_to_dict
from ep_driven_policy import EPDrivenPolicy


def _select_research_agent(world: World) -> Optional[Agent]:
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


def _get_agent_t3_and_atp(agent: Agent) -> tuple[float, float]:
    """Get agent's T3 composite and ATP."""
    t_axes = (agent.trust_axes or {}).get("T3") or {}
    t3_composite = float(t_axes.get("composite", 0.0))
    atp = float((agent.resources or {}).get("ATP", 0.0))
    return t3_composite, atp


def _set_agent_initial_conditions(agent: Agent, *, initial_t3: float, initial_atp: float) -> None:
    """Set agent's initial T3 and ATP."""
    agent.trust_axes.setdefault("T3", {})
    agent.trust_axes["T3"]["composite"] = float(initial_t3)
    agent.resources["ATP"] = float(initial_atp)


def _life_id(agent_lct: str, index: int) -> str:
    """Generate life ID."""
    return f"life:{agent_lct}:{index}"


def carry_forward_state(prev_life: Optional[LifeRecord]) -> Dict[str, Any]:
    """Carry forward karma from previous life."""
    if prev_life is None:
        return {"initial_t3": 0.5, "initial_atp": 100.0, "role_hint": "research_assistant"}

    t3 = float(prev_life.final_t3)

    if t3 > 0.7:
        initial_t3 = 0.6
        role_hint = "trusted_researcher"
    elif t3 < 0.3:
        initial_t3 = 0.4
        role_hint = "rehab_researcher"
    else:
        initial_t3 = 0.5
        role_hint = "research_assistant"

    base_atp = 100.0
    atp_bonus = (t3 - 0.5) * 40.0
    initial_atp = max(20.0, base_atp + atp_bonus)

    return {"initial_t3": float(initial_t3), "initial_atp": float(initial_atp), "role_hint": role_hint}


def run_ep_driven_closed_loop_multi_life(
    *,
    num_lives: int = 3,
    steps_per_life: int = 20,
    termination_t3_threshold: float = 0.2,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Run multi-life simulation with EP-driven policy.

    This is the EP-enhanced version of Cascade's `run_closed_loop_multi_life`.

    Key differences:
    - Uses EPDrivenPolicy instead of ResearchAgentDriver
    - Tracks EP learning statistics across lives
    - Records maturation progression (IMMATURE → LEARNING → MATURE)
    """

    # Initialize world and policy
    world = bootstrap_home_society_world()
    society = next(iter(world.societies.values()))
    research_agent = _select_research_agent(world)

    if research_agent is None:
        return {"error": "No agents in world"}

    agent_lct = research_agent.agent_lct
    world.life_lineage.setdefault(agent_lct, [])

    # EP-driven policy (persists across lives for learning)
    policy = EPDrivenPolicy()

    prev_life: Optional[LifeRecord] = None
    life_action_logs: Dict[str, List[Dict[str, Any]]] = {}
    life_ep_stats: Dict[str, Dict[str, Any]] = {}
    carry_forward: Dict[str, Dict[str, Any]] = {}

    if verbose:
        print("=" * 80)
        print("EP-DRIVEN CLOSED-LOOP MULTI-LIFE SIMULATION")
        print("=" * 80)
        print(f"Lives: {num_lives}, Steps per life: {steps_per_life}")
        print(f"Agent: {agent_lct}")
        print()

    for idx in range(1, num_lives + 1):
        life_id = _life_id(agent_lct, idx)
        world.life_state[agent_lct] = {"status": "alive", "life_id": life_id}

        # Carry forward karma
        init = carry_forward_state(prev_life)
        carry_forward[life_id] = dict(init)
        _set_agent_initial_conditions(
            research_agent,
            initial_t3=float(init["initial_t3"]),
            initial_atp=float(init["initial_atp"]),
        )

        start_tick = world.tick
        t3_history: List[float] = []
        atp_history: List[float] = []
        life_state = "alive"
        termination_reason = "none"

        applied_actions: List[Dict[str, Any]] = []

        if verbose:
            stats = policy.get_learning_stats()
            print("=" * 80)
            print(f"LIFE {idx}")
            print(f"EP Maturation: {stats['maturation_stage'].upper()}")
            print(f"Pattern Corpus: {stats['total_patterns']} total")
            print("=" * 80)
            print()

        # Life loop
        for step in range(steps_per_life):
            tick_world(world)

            # Get current state
            current_t3, current_atp = _get_agent_t3_and_atp(research_agent)

            # EP-driven action proposal
            life_summary_for_policy = {
                "life_state": "alive",
                "t3_history": t3_history + [current_t3],
                "atp_history": atp_history + [current_atp],
                "life_id": life_id,
            }

            policy_result = policy.propose_action(
                agent=research_agent,
                world=world,
                life_id=life_id
            )

            proposed_action = policy_result["proposed_action"]
            ep_assessment = policy_result["ep_assessment"]

            # Apply action to world
            applied = apply_policy_action(
                world=world,
                society=society,
                agent=research_agent,
                life_id=life_id,
                proposed_action=proposed_action,
            )

            applied_actions.append({
                **applied_action_to_dict(applied),
                "ep_decision": ep_assessment["coordinated_decision"]["final_decision"],
                "ep_confidence": ep_assessment["coordinated_decision"]["confidence"],
                "learning_mode": ep_assessment["learning_mode"]
            })

            # Record post-action metrics
            t3, atp = _get_agent_t3_and_atp(research_agent)
            t3_history.append(t3)
            atp_history.append(atp)

            # Check termination
            if atp <= 0.0:
                life_state = "terminated"
                termination_reason = "atp_exhausted"
                break

            if t3 < float(termination_t3_threshold):
                life_state = "terminated"
                termination_reason = "low_trust"
                break

        end_tick = world.tick

        # Record life
        life = LifeRecord(
            life_id=life_id,
            agent_lct=agent_lct,
            start_tick=int(start_tick),
            end_tick=int(end_tick),
            life_state=life_state,
            termination_reason=termination_reason,
            t3_history=t3_history,
            atp_history=atp_history,
        )

        world.life_lineage[agent_lct].append(life)
        life_action_logs[life_id] = applied_actions
        life_ep_stats[life_id] = policy.get_learning_stats()

        # Reborn edge
        if prev_life is not None:
            world.add_context_edge(
                subject=prev_life.life_id,
                predicate="web4:rebornAs",
                object=life.life_id,
                mrh={"deltaR": "local", "deltaT": "lifespan", "deltaC": "agent-scale"},
            )

        world.life_state[agent_lct] = {"status": "transitioning", "life_id": life_id}
        prev_life = life

        if verbose:
            stats = policy.get_learning_stats()
            print(f"Life {idx} Complete:")
            print(f"  State: {life_state}")
            print(f"  Final T3: {t3_history[-1]:.3f}, ATP: {atp_history[-1]:.1f}")
            print(f"  Actions: {len(applied_actions)}")
            print(f"  Patterns: {stats['total_patterns']}")
            print(f"  Maturation: {stats['maturation_stage']}")
            print()

    if verbose:
        print("=" * 80)
        print("SIMULATION COMPLETE")
        print("=" * 80)
        final_stats = policy.get_learning_stats()
        print(f"\nFinal EP Maturation: {final_stats['maturation_stage'].upper()}")
        print(f"Total Patterns: {final_stats['total_patterns']}")
        print(f"Pattern Prediction Rate: {final_stats['pattern_rate']*100:.1f}%")
        print()

    return {
        "agent_lct": agent_lct,
        "lives": [asdict(l) for l in world.life_lineage.get(agent_lct, [])],
        "applied_actions": life_action_logs,
        "carry_forward": carry_forward,
        "ep_statistics": {
            "life_progression": life_ep_stats,
            "final_stats": policy.get_learning_stats()
        },
        "context_edges": [
            {"subject": e.subject, "predicate": e.predicate, "object": e.object, "mrh": e.mrh}
            for e in world.context_edges
        ],
        "world_tick": world.tick,
    }


if __name__ == "__main__":
    import sys

    # Run simulation
    results = run_ep_driven_closed_loop_multi_life(
        num_lives=3,
        steps_per_life=20,
        verbose=True
    )

    # Save results
    output_file = Path(__file__).parent / "ep_driven_closed_loop_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to: {output_file.name}")
    print()
