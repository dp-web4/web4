"""Minimal simulation loop for the Web4 game (v0).

This module defines a very simple tick-based simulation loop that
advances a `World` instance. Behavior is intentionally minimal and
will be extended over time.
"""

from __future__ import annotations

from typing import Callable, Optional

from .models import World, Agent, Society


def tick_world(world: World) -> None:
    """Advance the world by one tick.

    For v0 this simply increments the tick counter and calls
    placeholder hooks for agent and society behavior.
    """

    world.tick += 1

    # Placeholder: iterate over agents and societies and allow them to
    # take actions. Future versions will plug in real decision
    # policies, trust updates, and economic flows.
    for agent in list(world.agents.values()):
        _agent_step(world, agent)

    for society in list(world.societies.values()):
        _society_step(world, society)


def _agent_step(world: World, agent: Agent) -> None:
    """Placeholder for per-agent behavior in a single tick."""

    # Future work: choose actions based on trust, resources,
    # memberships, and available societies/tasks.

    # For now, just record MRH/LCT context edges for memberships so we can
    # inspect the evolving society graph. We use a coarse MRH profile.
    mrh_profile = {
        "deltaR": "local",
        "deltaT": "session",
        "deltaC": "agent-scale",
    }
    for society_lct in agent.memberships:
        world.add_context_edge(
            subject=agent.agent_lct,
            predicate="web4:participantIn",
            object=society_lct,
            mrh=mrh_profile,
        )


def _society_step(world: World, society: Society) -> None:
    """Placeholder for per-society behavior in a single tick."""

    # Future work: evaluate membership requests, tasks, treasury, and
    # update trust and MRH context.
    _ = world  # unused for now
    _ = society


def run_world(world: World, steps: int) -> World:
    """Run the world for a fixed number of ticks (v0 helper)."""

    for _ in range(steps):
        tick_world(world)
    return world
