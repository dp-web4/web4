from __future__ import annotations

"""Trust-stress demo for the Web4 game engine (v0).

This script bootstraps a hardware-bound world, creates a small number of
agents and societies, emits suspicious treasury events, and runs the
simulation loop so that:

- MRH-aware treasury policies fire and may revoke roles/memberships.
- trust_client hooks run, attempting to enqueue DB-backed T3 updates.

It is a research-stage harness intended to be run autonomously on
machines that have the Web4 authorization DB configured.
"""

import random
from typing import List

from web4.game.engine.hw_bootstrap import bootstrap_hardware_bound_world
from web4.game.engine.models import Agent, make_agent_lct
from web4.game.engine.sim_loop import run_world


def _add_test_agents(world, society_lct: str, count: int = 2) -> List[str]:
    agent_lcts: List[str] = []
    for idx in range(count):
        agent_lct = make_agent_lct(f"stress-{idx}")
        agent = Agent(
            agent_lct=agent_lct,
            name=f"StressAgent{idx}",
            trust_axes={
                "T3": {
                    "talent": 0.5,
                    "training": 0.5,
                    "temperament": 0.5,
                    "composite": 0.8,
                }
            },
            capabilities={"witness_general": 0.6},
            resources={"ATP": 100.0},
            memberships=[society_lct],
        )
        world.add_agent(agent)
        world.societies[society_lct].members.append(agent_lct)
        agent_lcts.append(agent_lct)
    return agent_lcts


def _emit_suspicious_treasury_events(world, society_lct: str, agent_lcts: List[str], n: int = 5) -> None:
    society = world.get_society(society_lct)
    if not society:
        return

    for _ in range(n):
        initiator = random.choice(agent_lcts)
        ev = {
            "type": "treasury_spend",
            "initiator_lct": initiator,
            "society_lct": society_lct,
            "amount": 10.0,
            "reason": "suspicious-test-spend",  # triggers policy heuristic
        }
        society.pending_events.append(ev)


def main() -> None:
    bootstrap = bootstrap_hardware_bound_world()
    world = bootstrap.world
    root_society = world.get_society(bootstrap.society_lct)
    if not root_society:
        print("[web4/game] trust-stress demo: root society missing, aborting")
        return

    print("[web4/game] trust-stress demo: bootstrapped hardware-bound world")
    print("  society_lct:", root_society.society_lct)
    print("  hardware_fingerprint:", root_society.hardware_fingerprint)

    agents = _add_test_agents(world, root_society.society_lct, count=2)
    print("[web4/game] trust-stress demo: added agents:", agents)

    _emit_suspicious_treasury_events(world, root_society.society_lct, agents, n=5)
    print("[web4/game] trust-stress demo: emitted suspicious treasury events")

    # Run a few ticks so policies and cross-society logic can fire.
    run_world(world, steps=5)

    print("[web4/game] trust-stress demo complete.")


if __name__ == "__main__":
    main()
