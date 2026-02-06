from __future__ import annotations

"""Three-society federation / suppression sandbox (v0).

This scenario creates three societies A, B, C with different policies
and initial treasuries, plus agents that exercise both cooperative and
adversarial behavior.
"""

from .models import World, Society, Agent, make_agent_lct, make_society_lct
from .roles import bind_role, pair_role_with_lct
from .membership import membership_join


def bootstrap_three_societies_world() -> World:
    world = World()

    # Societies
    socA_lct = make_society_lct("A")
    socA = Society(
        society_lct=socA_lct,
        name="Society A (strict)",
        treasury={"ATP": 1500.0},
        members=[],
        policies={"admission": "review", "governance": "super-majority"},
    )
    world.add_society(socA)

    socB_lct = make_society_lct("B")
    socB = Society(
        society_lct=socB_lct,
        name="Society B (balanced)",
        treasury={"ATP": 1000.0},
        members=[],
        policies={"admission": "open", "governance": "simple-majority"},
    )
    world.add_society(socB)

    socC_lct = make_society_lct("C")
    socC = Society(
        society_lct=socC_lct,
        name="Society C (risky)",
        treasury={"ATP": 600.0},
        members=[],
        policies={"admission": "open", "governance": "loose"},
    )
    world.add_society(socC)

    # Federation links A<->B<->C
    world.add_context_edge(
        subject=socA_lct,
        predicate="web4:federatesWith",
        object=socB_lct,
        mrh={"deltaR": "regional", "deltaT": "session", "deltaC": "society-scale"},
    )
    world.add_context_edge(
        subject=socB_lct,
        predicate="web4:federatesWith",
        object=socA_lct,
        mrh={"deltaR": "regional", "deltaT": "session", "deltaC": "society-scale"},
    )
    world.add_context_edge(
        subject=socB_lct,
        predicate="web4:federatesWith",
        object=socC_lct,
        mrh={"deltaR": "regional", "deltaT": "session", "deltaC": "society-scale"},
    )
    world.add_context_edge(
        subject=socC_lct,
        predicate="web4:federatesWith",
        object=socB_lct,
        mrh={"deltaR": "regional", "deltaT": "session", "deltaC": "society-scale"},
    )

    # Agents
    alice_lct = make_agent_lct("alice-A")
    alice = Agent(
        agent_lct=alice_lct,
        name="Alice A",
        trust_axes={"T3": {"talent": 0.7, "training": 0.7, "temperament": 0.8, "composite": 0.73}},
        capabilities={"witness_general": 0.8},
        resources={"ATP": 150.0},
        memberships=[],
    )
    world.add_agent(alice)
    membership_join(world=world, society=socA, agent_lct=alice_lct, reason="founder of A")

    bob_lct = make_agent_lct("bob-B")
    bob = Agent(
        agent_lct=bob_lct,
        name="Bob B",
        trust_axes={"T3": {"talent": 0.6, "training": 0.5, "temperament": 0.5, "composite": 0.53}},
        capabilities={"witness_general": 0.6},
        resources={"ATP": 120.0},
        memberships=[],
    )
    world.add_agent(bob)
    membership_join(world=world, society=socB, agent_lct=bob_lct, reason="founder of B")

    carol_lct = make_agent_lct("carol-C")
    carol = Agent(
        agent_lct=carol_lct,
        name="Carol C",
        trust_axes={"T3": {"talent": 0.8, "training": 0.4, "temperament": 0.3, "composite": 0.5}},
        capabilities={"witness_general": 0.4},
        resources={"ATP": 90.0},
        memberships=[],
    )
    world.add_agent(carol)
    membership_join(world=world, society=socC, agent_lct=carol_lct, reason="founder of C (risky)")

    # Bridge agent between A and B
    dana_lct = make_agent_lct("dana-AB")
    dana = Agent(
        agent_lct=dana_lct,
        name="Dana AB",
        trust_axes={"T3": {"talent": 0.7, "training": 0.6, "temperament": 0.7, "composite": 0.67}},
        capabilities={"witness_general": 0.7},
        resources={"ATP": 130.0},
        memberships=[],
    )
    world.add_agent(dana)
    membership_join(world=world, society=socA, agent_lct=dana_lct, reason="bridge A/B")
    membership_join(world=world, society=socB, agent_lct=dana_lct, reason="bridge A/B")

    # Roles/treasuries
    treasuryA_lct = f"{socA_lct}:treasury:primary"
    treasuryB_lct = f"{socB_lct}:treasury:primary"
    treasuryC_lct = f"{socC_lct}:treasury:primary"

    alice_auditor_A = bind_role(
        world=world,
        society=socA,
        role_name="auditor",
        subject_lct=alice_lct,
        reason="Alice audits A",
    )
    dana_treasurer_A = bind_role(
        world=world,
        society=socA,
        role_name="treasurer",
        subject_lct=dana_lct,
        reason="Dana manages A treasury",
    )
    pair_role_with_lct(
        world=world,
        society=socA,
        role_lct=dana_treasurer_A,
        other_lct=treasuryA_lct,
        reason="Dana controls A primary treasury",
    )

    bob_treasurer_B = bind_role(
        world=world,
        society=socB,
        role_name="treasurer",
        subject_lct=bob_lct,
        reason="Bob manages B treasury",
    )
    pair_role_with_lct(
        world=world,
        society=socB,
        role_lct=bob_treasurer_B,
        other_lct=treasuryB_lct,
        reason="Bob controls B primary treasury",
    )

    carol_treasurer_C = bind_role(
        world=world,
        society=socC,
        role_name="treasurer",
        subject_lct=carol_lct,
        reason="Carol manages C treasury (risky)",
    )
    pair_role_with_lct(
        world=world,
        society=socC,
        role_lct=carol_treasurer_C,
        other_lct=treasuryC_lct,
        reason="Carol controls C primary treasury",
    )

    return world
