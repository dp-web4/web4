#!/usr/bin/env python3
"""
EP Maturation Demonstration: IMMATURE → LEARNING → MATURE

Session 115: Legion autonomous research

Demonstrates EP maturation across 3 lives with pattern learning:
- Life 1 (IMMATURE): 0 patterns → 100% heuristic → conservative
- Life 2 (LEARNING): 65 patterns (Thor's) → ~50% pattern-based → calibrated
- Life 3 (MATURE): 85+ patterns (Thor's + Life 2) → ~90% pattern-based → optimal

Architecture:
1. Life 1: EPDrivenPolicy() with no patterns
2. Life 2: Load Thor's 65 patterns from Sessions 144-145
3. Life 3: Continue with patterns from Life 2 (corpus growth)

Each life collects patterns from its experiences, feeding into next life.

Usage:
    python run_maturation_demo.py
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
from ep_driven_policy import EPDrivenPolicy, create_policy_with_thor_patterns, create_policy_with_web4_patterns


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


def run_maturation_demo(
    *,
    num_lives: int = 3,
    steps_per_life: int = 20,
    termination_t3_threshold: float = 0.2,
    pattern_source: str = "web4",  # "web4", "thor", or "none"
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Run maturation demonstration across 3 lives.

    Life 1: IMMATURE (0 patterns)
    Life 2: LEARNING (patterns from corpus)
    Life 3: MATURE (corpus + Life 2 patterns)

    Args:
        pattern_source: "web4" for Web4-native patterns (Session 116),
                       "thor" for Thor's SAGE patterns (Session 115),
                       "none" for heuristic-only baseline
    """

    # Initialize world
    world = bootstrap_home_society_world()
    society = next(iter(world.societies.values()))
    research_agent = _select_research_agent(world)

    if research_agent is None:
        return {"error": "No agents in world"}

    agent_lct = research_agent.agent_lct
    world.life_lineage.setdefault(agent_lct, [])

    prev_life: Optional[LifeRecord] = None
    life_action_logs: Dict[str, List[Dict[str, Any]]] = {}
    life_ep_stats: Dict[str, Dict[str, Any]] = {}
    carry_forward: Dict[str, Dict[str, Any]] = {}

    # Life-specific policies
    policies: List[EPDrivenPolicy] = []

    if verbose:
        print("=" * 80)
        print("EP MATURATION DEMONSTRATION: IMMATURE → LEARNING → MATURE")
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

        # Create policy for this life
        if idx == 1:
            # Life 1: IMMATURE (no patterns)
            policy = EPDrivenPolicy()
            if verbose:
                print("Life 1: IMMATURE - Starting with 0 patterns")
        elif idx == 2:
            # Life 2: LEARNING (load corpus patterns + Life 1 patterns)
            if pattern_source == "thor":
                hrm_path = Path("/home/dp/ai-workspace/HRM")
                policy = create_policy_with_thor_patterns(hrm_path)
                source_desc = "Thor's SAGE corpus"
            elif pattern_source == "web4":
                policy = create_policy_with_web4_patterns()
                source_desc = "Web4-native ATP corpus"
            else:  # pattern_source == "none"
                policy = EPDrivenPolicy()
                source_desc = "no external corpus"

            # Add Life 1's collected patterns
            if policies:
                for domain, matcher in policies[0].matchers.items():
                    for pattern in matcher.patterns:
                        policy.matchers[domain].add_pattern(pattern)
            if verbose:
                stats = policy.get_learning_stats()
                print(f"Life 2: LEARNING - Loaded {stats['total_patterns']} patterns ({source_desc} + Life 1)")
        else:
            # Life 3: MATURE (continue from Life 2)
            policy = policies[1]  # Reuse Life 2 policy with accumulated patterns
            if verbose:
                stats = policy.get_learning_stats()
                print(f"Life 3: MATURE - Continuing with {stats['total_patterns']} patterns from Life 2")

        policies.append(policy)

        start_tick = world.tick
        t3_history: List[float] = []
        atp_history: List[float] = []
        life_state = "alive"
        termination_reason = "none"

        applied_actions: List[Dict[str, Any]] = []

        if verbose:
            stats = policy.get_learning_stats()
            print(f"  Maturation: {stats['maturation_stage'].upper()}")
            print(f"  Patterns: {stats['total_patterns']}")
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

            # Record post-action metrics
            t3, atp = _get_agent_t3_and_atp(research_agent)

            # Record pattern for learning
            outcome = {
                "action_type": proposed_action["action_type"],
                "final_decision": ep_assessment["coordinated_decision"]["final_decision"],
                "atp_before": current_atp,
                "atp_after": atp,
                "t3_before": current_t3,
                "t3_after": t3,
                "success": atp > 0 and t3 >= termination_t3_threshold
            }

            policy.record_outcome(
                life_id=life_id,
                tick=world.tick,
                contexts=ep_assessment["contexts"],
                predictions=ep_assessment["predictions"],
                action_taken=proposed_action,
                outcome=outcome
            )

            applied_actions.append({
                **applied_action_to_dict(applied),
                "ep_decision": ep_assessment["coordinated_decision"]["final_decision"],
                "ep_confidence": ep_assessment["coordinated_decision"]["confidence"],
                "learning_mode": ep_assessment["learning_mode"],
                "maturation_stage": ep_assessment["maturation_stage"],
                "pattern_matches": sum(ep_assessment["pattern_matches"].values())
            })

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
            print(f"  Patterns collected this life: {stats['total_patterns'] - life_ep_stats.get(f'life:{agent_lct}:{idx-1}', {}).get('total_patterns', 0) if idx > 1 else stats['total_patterns']}")
            print(f"  Pattern prediction rate: {stats['pattern_rate']*100:.1f}%")
            print(f"  Maturation: {stats['maturation_stage']}")
            print()

    if verbose:
        print("=" * 80)
        print("MATURATION DEMONSTRATION COMPLETE")
        print("=" * 80)
        final_stats = policies[-1].get_learning_stats()
        print(f"\nFinal EP State:")
        print(f"  Maturation: {final_stats['maturation_stage'].upper()}")
        print(f"  Total Patterns: {final_stats['total_patterns']}")
        print(f"  Pattern Prediction Rate: {final_stats['pattern_rate']*100:.1f}%")
        print()

    return {
        "agent_lct": agent_lct,
        "lives": [asdict(l) for l in world.life_lineage.get(agent_lct, [])],
        "applied_actions": life_action_logs,
        "carry_forward": carry_forward,
        "ep_statistics": {
            "life_progression": life_ep_stats,
            "final_stats": policies[-1].get_learning_stats()
        },
        "context_edges": [
            {"subject": e.subject, "predicate": e.predicate, "object": e.object, "mrh": e.mrh}
            for e in world.context_edges
        ],
        "world_tick": world.tick,
    }


if __name__ == "__main__":
    import sys

    # Parse CLI arguments
    pattern_source = "web4"  # Default to Web4-native patterns (Session 116)
    if len(sys.argv) > 1:
        pattern_source = sys.argv[1]  # "web4", "thor", or "none"

    print(f"Pattern Source: {pattern_source.upper()}")
    print()

    # Run maturation demonstration
    results = run_maturation_demo(
        num_lives=3,
        steps_per_life=20,
        pattern_source=pattern_source,
        verbose=True
    )

    # Save results
    output_file = Path(__file__).parent / f"maturation_demo_results_{pattern_source}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to: {output_file.name}")
    print()
