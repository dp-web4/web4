"""Multi-life runner for the Web4 game home-society scenario (v0).

This module chains multiple "lives" for a single research agent within a
single World instance, applying a simple carry-forward (karma) function.

It records lineage links as MRH/LCT context edges:
- `prev_life_id --web4:rebornAs--> next_life_id`

This is a local-first research primitive; it does not depend on external
services.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple

from engine.models import Agent, LifeRecord, World
from engine.scenarios import bootstrap_home_society_world
from engine.sim_loop import tick_world


def _select_research_agent(world: World) -> Optional[Agent]:
    if not world.agents:
        return None
    agent_lct = sorted(world.agents.keys())[0]
    return world.agents[agent_lct]


def _get_agent_t3_and_atp(agent: Agent) -> Tuple[float, float]:
    t_axes = (agent.trust_axes or {}).get("T3") or {}
    t3_composite = float(t_axes.get("composite", 0.0))
    atp = float((agent.resources or {}).get("ATP", 0.0))
    return t3_composite, atp


def _set_agent_initial_conditions(agent: Agent, *, initial_t3: float, initial_atp: float) -> None:
    agent.trust_axes.setdefault("T3", {})
    agent.trust_axes["T3"]["composite"] = float(initial_t3)
    agent.resources["ATP"] = float(initial_atp)


def _life_id(agent_lct: str, index: int) -> str:
    return f"life:{agent_lct}:{index}"


def carry_forward_state(prev_life: Optional[LifeRecord]) -> Dict[str, Any]:
    if prev_life is None:
        return {
            "initial_t3": 0.5,
            "initial_atp": 100.0,
            "role_hint": "research_assistant",
        }

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

    return {
        "initial_t3": float(initial_t3),
        "initial_atp": float(initial_atp),
        "role_hint": role_hint,
    }


def run_multi_life(
    *,
    num_lives: int = 3,
    steps_per_life: int = 20,
    termination_t3_threshold: float = 0.2,
) -> Dict[str, Any]:
    world = bootstrap_home_society_world()
    research_agent = _select_research_agent(world)

    if research_agent is None:
        return {"error": "No agents in world"}

    agent_lct = research_agent.agent_lct
    world.life_lineage.setdefault(agent_lct, [])

    prev_life: Optional[LifeRecord] = None
    carry_forward: Dict[str, Dict[str, Any]] = {}

    for idx in range(1, num_lives + 1):
        life_id = _life_id(agent_lct, idx)
        world.life_state[agent_lct] = {"status": "alive", "life_id": life_id}

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

        for _ in range(steps_per_life):
            tick_world(world)
            t3, atp = _get_agent_t3_and_atp(research_agent)
            t3_history.append(t3)
            atp_history.append(atp)

            if atp <= 0.0:
                life_state = "terminated"
                termination_reason = "atp_exhausted"
                break

            if t3 < float(termination_t3_threshold):
                life_state = "terminated"
                termination_reason = "low_trust"
                break

        end_tick = world.tick

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

        # Record lineage edge in MRH/LCT context.
        if prev_life is not None:
            world.add_context_edge(
                subject=prev_life.life_id,
                predicate="web4:rebornAs",
                object=life.life_id,
                mrh={"deltaR": "local", "deltaT": "lifespan", "deltaC": "agent-scale"},
            )

        world.life_state[agent_lct] = {"status": "transitioning", "life_id": life_id}
        prev_life = life

    # Snapshot export
    return {
        "agent_lct": agent_lct,
        "lives": [asdict(l) for l in world.life_lineage.get(agent_lct, [])],
        "carry_forward": carry_forward,
        "context_edges": [
            {
                "subject": e.subject,
                "predicate": e.predicate,
                "object": e.object,
                "mrh": e.mrh,
            }
            for e in world.context_edges
        ],
        "world_tick": world.tick,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_multi_life(num_lives=3, steps_per_life=20), indent=2, sort_keys=True))
