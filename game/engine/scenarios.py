"""Scripted world setup scenarios for the Web4 game (v0).

These helpers create initial `World` instances that can be used for
manual exploration or future tests.
"""

from __future__ import annotations

from .models import (
    Agent,
    Society,
    World,
    make_agent_lct,
    make_society_lct,
)


def bootstrap_home_society_world() -> World:
    """Create a minimal "home society" world for experimentation.

    This is a stand-in for a future hardware-bound society bootstrap
    kit. For now it simply creates:

    - One root society with a canonical LCT.
    - Two agents with different T3-like trust profiles.
    - Membership links from agents to the society.
    """

    world = World()

    # Root society for this local world
    root_society_lct = make_society_lct("home-root")
    root_society = Society(
        society_lct=root_society_lct,
        name="Home Society",
        treasury={"ATP": 1000.0},
        members=[],
        policies={
            "admission": "open",  # placeholder
            "governance": "simple-majority",
        },
    )
    world.add_society(root_society)

    # Agent A: cautious, high-temperament trust
    agent_a_lct = make_agent_lct("alice")
    agent_a = Agent(
        agent_lct=agent_a_lct,
        name="Alice",
        trust_axes={
            "T3": {
                "talent": 0.6,
                "training": 0.4,
                "temperament": 0.8,
                "composite": 0.6,
            }
        },
        capabilities={"witness_general": 0.7},
        resources={"ATP": 100.0},
        memberships=[root_society_lct],
    )
    world.add_agent(agent_a)
    root_society.members.append(agent_a_lct)

    # Agent B: ambitious, lower temperament trust
    agent_b_lct = make_agent_lct("bob")
    agent_b = Agent(
        agent_lct=agent_b_lct,
        name="Bob",
        trust_axes={
            "T3": {
                "talent": 0.8,
                "training": 0.3,
                "temperament": 0.3,
                "composite": 0.5,
            }
        },
        capabilities={"witness_general": 0.4},
        resources={"ATP": 80.0},
        memberships=[root_society_lct],
    )
    world.add_agent(agent_b)
    root_society.members.append(agent_b_lct)

    return world
