#!/usr/bin/env python3
"""
Test Role Revocation in Web4 Game Engine
Session #68: Verify that policy enforcement actually revokes roles after fraud threshold
"""

import sys
sys.path.insert(0, '/home/dp/ai-workspace/web4/game')

from engine.models import World, Agent, Society
from engine.sim_loop import tick_world
from engine.roles import bind_role, make_role_lct
from engine.treasury import treasury_spend
from engine.policy import apply_simple_policies

def has_role(world: World, agent_lct: str, role_lct: str) -> bool:
    """Check if agent has a specific role by examining context edges"""
    for edge in world.context_edges:
        if (edge.subject == agent_lct and
            edge.predicate == 'web4:hasRole' and
            edge.object == role_lct):
            return True
    return False

def had_role(world: World, agent_lct: str, role_lct: str) -> bool:
    """Check if agent previously had role (revoked) by examining context edges"""
    for edge in world.context_edges:
        if (edge.subject == agent_lct and
            edge.predicate == 'web4:hadRole' and
            edge.object == role_lct):
            return True
    return False

def main():
    print("="*80)
    print("  Role Revocation Test - Session #68")
    print("="*80)

    # Setup
    world = World()
    society = Society(
        society_lct="lct:test:society",
        name="Test Society",
        treasury={"ATP": 2000},
        block_interval_seconds=1  # Seal blocks quickly
    )
    world.add_society(society)

    bob_lct = "lct:test:bob"
    bob = Agent(
        agent_lct=bob_lct,
        name="Bob",
        trust_axes={"T3": {"talent": 0.8, "training": 0.7, "temperament": 0.35, "composite": 0.62}},
        capabilities={},
        resources={"ATP": 100},
        memberships=[society.society_lct]
    )
    world.add_agent(bob)

    # Bind Bob as treasurer
    treasurer_role = make_role_lct(society.society_lct, "treasurer")
    bind_role(
        world=world,
        society=society,
        role_name="treasurer",
        subject_lct=bob_lct,
        reason="initial role binding"
    )

    print(f"\n--- Initial State ---")
    print(f"  Bob LCT: {bob_lct}")
    print(f"  Treasurer Role: {treasurer_role}")
    print(f"  Bob has treasurer role: {has_role(world, bob_lct, treasurer_role)}")
    print(f"  Bob T3: {bob.trust_axes['T3']['composite']:.3f}")
    print(f"  Treasury: {society.treasury['ATP']} ATP")
    print(f"  Blocks sealed: {len(society.blocks)}")

    # Fraud scenario: Bob steals 4 times (threshold is 3)
    print(f"\n--- Fraud Scenario: Bob Steals 4 Times ---")
    for i in range(4):
        treasury_spend(
            world=world,
            society=society,
            treasury_lct=f"{society.society_lct}:treasury",
            initiator_lct=bob_lct,
            amount=100.0,
            reason="suspicious self-allocation for personal use"
        )

        # Tick to seal block
        tick_world(world)

        print(f"\n  Theft #{i+1}:")
        print(f"    Treasury: {society.treasury['ATP']} ATP")
        print(f"    Blocks sealed: {len(society.blocks)}")
        print(f"    Pending events: {len(society.pending_events)}")

        # Count suspicious events in blocks
        suspicious_count = 0
        for block in society.blocks:
            for ev in block.get("events", []):
                if ev.get("type") == "treasury_spend" and "suspicious" in ev.get("reason", ""):
                    suspicious_count += 1
        print(f"    Suspicious events in blocks: {suspicious_count}")

        # Check Bob's current state BEFORE policy
        print(f"    Bob has treasurer role (before policy): {has_role(world, bob_lct, treasurer_role)}")
        print(f"    Bob had treasurer role (revoked): {had_role(world, bob_lct, treasurer_role)}")

        # Apply policy (checks blocks for fraud)
        apply_simple_policies(world, society)

        # Check Bob's state AFTER policy
        bob_current = world.agents.get(bob_lct)
        has_t_role = has_role(world, bob_lct, treasurer_role)
        had_t_role = had_role(world, bob_lct, treasurer_role)

        print(f"    Bob T3 (after policy): {bob_current.trust_axes.get('T3', {}).get('composite', 0):.3f}")
        print(f"    Bob has treasurer role (after policy): {has_t_role}")
        print(f"    Bob had treasurer role (revoked): {had_t_role}")

        # Check if revocation event was created
        revocation_events = [e for e in society.pending_events if e.get('type') == 'role_revocation']
        if revocation_events:
            print(f"    ✅ Role revocation event created!")
            print(f"       Reason: {revocation_events[-1].get('reason')}")

        if had_t_role and not has_t_role:
            print(f"\n✅ SUCCESS: Role revoked after {i+1} thefts!")
            break

    # Final state
    print(f"\n--- Final State ---")
    print(f"  Bob T3: {bob_current.trust_axes.get('T3', {}).get('composite', 0):.3f}")
    print(f"  Bob has treasurer role: {has_role(world, bob_lct, treasurer_role)}")
    print(f"  Bob had treasurer role (revoked): {had_role(world, bob_lct, treasurer_role)}")
    print(f"  Treasury remaining: {society.treasury['ATP']} ATP")
    print(f"  Total blocks: {len(society.blocks)}")

    # Check for revocation events in blocks
    revocation_in_blocks = 0
    for block in society.blocks:
        for ev in block.get("events", []):
            if ev.get("type") == "role_revocation":
                revocation_in_blocks += 1
                print(f"\n  Role revocation in block {block.get('index')}:")
                print(f"    Reason: {ev.get('reason')}")

    if revocation_in_blocks > 0:
        print(f"\n✅ Role revocation events found in blockchain: {revocation_in_blocks}")
    else:
        print(f"\n⚠️  No role revocation events in blockchain")

    # Verify Bob can't perform treasury operations
    print(f"\n--- Verification: Can Bob Still Spend? ---")
    if not has_role(world, bob_lct, treasurer_role):
        print(f"  Bob no longer has treasurer role")
        print(f"  (Treasury operations would be unauthorized)")
        print(f"  ✅ Role revocation effective!")
    else:
        print(f"  ⚠️  Bob still has treasurer role - revocation may not have worked")

if __name__ == "__main__":
    main()
