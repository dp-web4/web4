"""One-society, one-agent life loop for Web4 game (v0).

This module will provide a minimal entrypoint to:
- bootstrap a home society world,
- mark a single research agent,
- run a short life (fixed number of ticks), and
- export a JSON summary of T3/ATP and key MRH events.

Implementation to be filled in by Cascade.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from engine.models import Agent
from engine.scenarios import bootstrap_home_society_world
from engine.sim_loop import tick_world


def _select_research_agent(world) -> Optional[Agent]:
    """Select a single agent to act as the research agent for this life.

    For now we choose the first agent in the world's registry. Future
    versions can make this configurable or driven by LCT metadata.
    """

    if not world.agents:
        return None
    # Deterministic selection by sorted LCT ID for reproducibility.
    agent_lct = sorted(world.agents.keys())[0]
    return world.agents[agent_lct]


def _get_agent_t3_and_atp(agent: Agent) -> Tuple[float, float]:
    """Extract T3 composite trust and ATP for the given agent.

    Falls back to 0.0 if the fields are missing so callers don't need to
    worry about KeyError.
    """

    t_axes = (agent.trust_axes or {}).get("T3") or {}
    t3_composite = float(t_axes.get("composite", 0.0))
    atp = float((agent.resources or {}).get("ATP", 0.0))
    return t3_composite, atp


def run_single_life(steps: int = 20) -> Dict[str, Any]:
    """Run a minimal life in the home society world and return a summary.

    This helper boots the home-society scenario, selects a single
    research agent, and then advances the world tick-by-tick while
    tracking that agent's T3 composite trust and ATP.

    Life semantics (v0):
    - The life is considered "terminated" if either:
      * the agent's ATP reaches 0, or
      * T3 composite falls below 0.2.
    - Otherwise, the life_state is "alive" after the configured steps.
    """

    world = bootstrap_home_society_world()
    research_agent = _select_research_agent(world)

    t3_history: List[float] = []
    atp_history: List[float] = []
    life_state = "alive"

    for _ in range(steps):
        # Advance the world one tick so that membership edges and
        # microblocks evolve over time.
        tick_world(world)

        if research_agent is None:
            # If no agent, we still advance ticks but cannot track a life.
            continue

        t3, atp = _get_agent_t3_and_atp(research_agent)
        t3_history.append(t3)
        atp_history.append(atp)

        if atp <= 0.0 or t3 < 0.2:
            life_state = "terminated"
            break

    # For now, return a simple summary of societies, agents, and this
    # agent's life metrics.
    return {
        "tick": world.tick,
        "life_state": life_state,
        "research_agent_lct": research_agent.agent_lct if research_agent else None,
        "t3_history": t3_history,
        "atp_history": atp_history,
        "societies": {
            soc_id: {
                "name": soc.name,
                "treasury": soc.treasury,
                "trust_axes": soc.trust_axes,
                "blocks": len(soc.blocks),
            }
            for soc_id, soc in world.societies.items()
        },
        "agents": {
            agent_id: {
                "name": agent.name,
                "trust_axes": agent.trust_axes,
                "resources": agent.resources,
                "memberships": agent.memberships,
            }
            for agent_id, agent in world.agents.items()
        },
        "context_edges": [
            {
                "subject": edge.subject,
                "predicate": edge.predicate,
                "object": edge.object,
                "mrh": edge.mrh,
            }
            for edge in world.context_edges
        ],
    }


if __name__ == "__main__":
    import json

    summary = run_single_life(steps=20)
    print(json.dumps(summary, indent=2, sort_keys=True))
