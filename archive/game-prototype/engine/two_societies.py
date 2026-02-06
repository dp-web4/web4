from __future__ import annotations

"""Multi-society federation sandbox for the Web4 game (v0).

This module defines a world setup with two societies that have distinct
roles, treasuries, and simple federation links.
"""

from .models import World, Society, Agent, make_agent_lct, make_society_lct
from .roles import bind_role, pair_role_with_lct
from .membership import membership_join


def bootstrap_two_societies_world() -> World:
    """Create a world with two federated societies and shared agents."""

    world = World()

    # Society A: stricter
    socA_lct = make_society_lct("socA")
    socA = Society(
        society_lct=socA_lct,
        name="Society A (strict)",
        treasury={"ATP": 1500.0},
        members=[],
        policies={
            "admission": "review",
            "governance": "super-majority",
        },
    )
    world.add_society(socA)

    # Society B: looser
    socB_lct = make_society_lct("socB")
    socB = Society(
        society_lct=socB_lct,
        name="Society B (loose)",
        treasury={"ATP": 800.0},
        members=[],
        policies={
            "admission": "open",
            "governance": "simple-majority",
        },
    )
    world.add_society(socB)

    # Agents
    # Alice: prefers Society A
    alice_lct = make_agent_lct("alice-A")
    alice = Agent(
        agent_lct=alice_lct,
        name="Alice A",
        trust_axes={
            "T3": {
                "talent": 0.7,
                "training": 0.6,
                "temperament": 0.8,
                "composite": 0.7,
            }
        },
        capabilities={"witness_general": 0.8},
        resources={"ATP": 120.0},
        memberships=[],
    )
    world.add_agent(alice)
    membership_join(world=world, society=socA, agent_lct=alice_lct, reason="founding member of A")

    # Bob: prefers Society B
    bob_lct = make_agent_lct("bob-B")
    bob = Agent(
        agent_lct=bob_lct,
        name="Bob B",
        trust_axes={
            "T3": {
                "talent": 0.8,
                "training": 0.4,
                "temperament": 0.4,
                "composite": 0.53,
            }
        },
        capabilities={"witness_general": 0.5},
        resources={"ATP": 90.0},
        memberships=[],
    )
    world.add_agent(bob)
    membership_join(world=world, society=socB, agent_lct=bob_lct, reason="founding member of B")

    # Carol: bridge agent, member of both societies
    carol_lct = make_agent_lct("carol-AB")
    carol = Agent(
        agent_lct=carol_lct,
        name="Carol AB",
        trust_axes={
            "T3": {
                "talent": 0.6,
                "training": 0.7,
                "temperament": 0.7,
                "composite": 0.67,
            }
        },
        capabilities={"witness_general": 0.6},
        resources={"ATP": 110.0},
        memberships=[],
    )
    world.add_agent(carol)
    membership_join(world=world, society=socA, agent_lct=carol_lct, reason="bridge member of A and B")
    membership_join(world=world, society=socB, agent_lct=carol_lct, reason="bridge member of A and B")

    # Federation context edges via roles helpers are not necessary; use
    # context graph directly to signal federation.
    world.add_context_edge(
        subject=socA_lct,
        predicate="web4:federatesWith",
        object=socB_lct,
        mrh={"deltaR": "local", "deltaT": "session", "deltaC": "society-scale"},
    )
    world.add_context_edge(
        subject=socB_lct,
        predicate="web4:federatesWith",
        object=socA_lct,
        mrh={"deltaR": "local", "deltaT": "session", "deltaC": "society-scale"},
    )

    # Roles and treasuries
    # Society A: Alice as auditor, Carol as treasurer
    alice_auditor_role = bind_role(
        world=world,
        society=socA,
        role_name="auditor",
        subject_lct=alice_lct,
        reason="Alice A is primary auditor for A",
    )
    carol_treasurer_A_role = bind_role(
        world=world,
        society=socA,
        role_name="treasurer",
        subject_lct=carol_lct,
        reason="Carol AB is treasurer for A",
    )
    treasuryA_lct = f"{socA_lct}:treasury:primary"
    pair_role_with_lct(
        world=world,
        society=socA,
        role_lct=carol_treasurer_A_role,
        other_lct=treasuryA_lct,
        reason="Carol AB controls primary treasury A",
    )

    # Society B: Bob as treasurer, Carol as auditor
    bob_treasurer_B_role = bind_role(
        world=world,
        society=socB,
        role_name="treasurer",
        subject_lct=bob_lct,
        reason="Bob B is treasurer for B",
    )
    carol_auditor_B_role = bind_role(
        world=world,
        society=socB,
        role_name="auditor",
        subject_lct=carol_lct,
        reason="Carol AB is auditor for B",
    )
    treasuryB_lct = f"{socB_lct}:treasury:primary"
    pair_role_with_lct(
        world=world,
        society=socB,
        role_lct=bob_treasurer_B_role,
        other_lct=treasuryB_lct,
        reason="Bob B controls primary treasury B",
    )

    return world
