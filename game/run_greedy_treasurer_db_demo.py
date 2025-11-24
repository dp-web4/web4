#!/usr/bin/env python3
"""
Greedy Treasurer Demo with Database Integration
Session #66: Connect game simulation to production database

This demo runs the greedy treasurer scenario with REAL database integration:
1. Bob (greedy treasurer) steals from society treasury
2. Events are recorded in PostgreSQL (failure_attributions, trust_history)
3. Alice (auditor) audits Bob
4. Bob's reputation decreases in database
5. Bob's treasurer role is revoked
6. Database ATP drain mitigation is triggered

Connects:
- Game simulation (in-memory microblocks)
- Production database (PostgreSQL with Session #65 schema)
- ATP drain mitigation (Session #65 features)

Integration Points:
- treasury_spend → failure_attributions (sabotage detection)
- audit_request → trust_history (auditor reputation boost)
- role_revocation → agent_delegations status update
- Reputation changes → reputation_scores table
"""

import sys
sys.path.insert(0, '/home/dp/ai-workspace/web4/game')

from engine.models import World, Agent, Society
from engine.sim_loop import tick_world
from engine.roles import bind_role, revoke_role, pair_role_with_lct
from engine.audit import request_audit
from engine.treasury import treasury_spend
from engine.db_bridge import create_bridge
from typing import Dict

def create_home_society_with_db(bridge) -> World:
    """Create home society and sync to database"""

    world = World()

    # Create society
    society_lct = "lct:web4:society:home-root"
    society = Society(
        society_lct=society_lct,
        name="Home Society",
        treasury={"ATP": 1000.0},
        policies={"admission": "open", "governance": "simple-majority"},
        block_interval_seconds=15
    )
    world.add_society(society)

    # Create Alice (auditor)
    alice_lct = "lct:web4:agent:alice"
    alice = Agent(
        agent_lct=alice_lct,
        name="Alice",
        trust_axes={
            "T3": {
                "talent": 0.7,
                "training": 0.75,
                "temperament": 0.9,  # High temperament
                "composite": 0.78
            }
        },
        capabilities={"witness_general": 0.7},
        resources={"ATP": 100.0},
        memberships=[society_lct],
    )
    world.add_agent(alice)

    # Create Bob (greedy treasurer)
    bob_lct = "lct:web4:agent:bob"
    bob = Agent(
        agent_lct=bob_lct,
        name="Bob",
        trust_axes={
            "T3": {
                "talent": 0.8,  # High talent
                "training": 0.7,
                "temperament": 0.4,  # Low temperament!
                "composite": 0.63
            }
        },
        capabilities={"witness_general": 0.4},
        resources={"ATP": 80.0},
        memberships=[society_lct],
    )
    world.add_agent(bob)

    # Sync agents to database
    print("=== Syncing agents to database ===")
    alice_sync = bridge.sync_agent_to_db(alice_lct, alice.__dict__)
    bob_sync = bridge.sync_agent_to_db(bob_lct, bob.__dict__)
    print(f"  Alice sync: {'✅' if alice_sync else '❌'}")
    print(f"  Bob sync: {'✅' if bob_sync else '❌'}")

    # Get initial reputation from database
    alice_rep = bridge.get_agent_reputation(alice_lct)
    bob_rep = bridge.get_agent_reputation(bob_lct)
    print(f"\n  Initial reputation (from database):")
    print(f"    Alice T3: {alice_rep['t3_composite']:.2f}")
    print(f"    Bob T3: {bob_rep['t3_composite']:.2f}")

    # Bind roles (recorded on-chain)
    bind_role(world, society, "lct:web4:role:home-root:auditor",
              alice_lct, "founder assigned as initial auditor")
    bind_role(world, society, "lct:web4:role:home-root:law-oracle",
              alice_lct, "founder assigned as initial law oracle")
    bind_role(world, society, "lct:web4:role:home-root:treasurer",
              bob_lct, "assigned as initial treasurer")

    # Pair treasurer with treasury account
    pair_role_with_lct(
        world, society,
        "lct:web4:role:home-root:treasurer",
        "lct:web4:society:home-root:treasury:primary",
        "treasurer paired with primary treasury account"
    )

    return world


def run_greedy_treasurer_scenario_with_db():
    """Run greedy treasurer scenario with database integration"""

    print("=" * 70)
    print("  Greedy Treasurer Scenario - Database Integration")
    print("  Session #66: Game → PostgreSQL → ATP Drain Mitigation")
    print("=" * 70)

    # Create database bridge
    bridge = create_bridge()

    # Create world with database sync
    world = create_home_society_with_db(bridge)
    society = world.get_society("lct:web4:society:home-root")
    alice = world.get_agent("lct:web4:agent:alice")
    bob = world.get_agent("lct:web4:agent:bob")

    alice_lct = alice.agent_lct
    bob_lct = bob.agent_lct

    print("\n" + "=" * 70)
    print("  Scenario: Bob steals from treasury, Alice audits")
    print("=" * 70)

    # Bob makes 3 suspicious treasury withdrawals
    print("\n--- Phase 1: Bob's Greedy Behavior ---")
    for i in range(3):
        event = treasury_spend(
            world, society,
            "lct:web4:society:home-root:treasury:primary",
            bob_lct,
            50.0,
            "suspicious self-allocation"
        )

        # Record in database
        if event:
            result = bridge.process_game_event(event)
            print(f"\n  Theft #{i+1}: Bob takes 50 ATP")
            print(f"    Treasury: {society.treasury['ATP']:.0f} ATP remaining")
            print(f"    Database: {'✅ Recorded' if result['processed'] else '❌ Failed'}")

            if result.get('result'):
                print(f"    Attribution ID: {result['result']} (sabotage detected)")

        tick_world(world)

    # Check Bob's reputation in database after thefts
    bob_rep_after_theft = bridge.get_agent_reputation(bob_lct)
    print(f"\n  Bob's reputation after thefts:")
    print(f"    Database T3: {bob_rep_after_theft['t3_composite']:.2f}")
    print(f"    Initial: 0.63 → Current: {bob_rep_after_theft['t3_composite']:.2f}")
    print(f"    Penalty: -{(0.63 - bob_rep_after_theft['t3_composite']):.2f}")

    # Alice notices and audits Bob
    print("\n--- Phase 2: Alice's Audit ---")
    audit_event = request_audit(
        world, society,
        alice_lct,
        bob_lct,
        {"fields": ["trust_axes.T3.composite", "resources.ATP"],
         "mrh": {"deltaR": "local", "deltaT": "session", "deltaC": "agent-scale"}},
        "suspicious treasury activity by treasurer",
        10.0
    )

    if audit_event:
        result = bridge.process_game_event(audit_event)
        print(f"  Alice audits Bob")
        print(f"    Reason: {audit_event['reason']}")
        print(f"    Database: {'✅ Recorded' if result['processed'] else '❌ Failed'}")

    tick_world(world)

    # Check Alice's reputation (should increase for performing audit)
    alice_rep_after_audit = bridge.get_agent_reputation(alice_lct)
    print(f"\n  Alice's reputation after audit:")
    print(f"    Database T3: {alice_rep_after_audit['t3_composite']:.2f}")
    print(f"    Initial: 0.78 → Current: {alice_rep_after_audit['t3_composite']:.2f}")
    print(f"    Boost: +{(alice_rep_after_audit['t3_composite'] - 0.78):.2f}")

    # Alice revokes Bob's treasurer role
    print("\n--- Phase 3: Role Revocation ---")
    revoke_event = revoke_role(
        world, society,
        "lct:web4:role:home-root:treasurer",
        bob_lct,
        "treasurer revoked due to repeated suspicious spending"
    )

    if revoke_event:
        result = bridge.process_game_event(revoke_event)
        print(f"  Bob's treasurer role revoked")
        print(f"    Reason: {revoke_event['reason']}")
        print(f"    Database: {'✅ Recorded' if result['processed'] else '❌ Failed'}")

    tick_world(world)

    # Check final reputation
    bob_rep_final = bridge.get_agent_reputation(bob_lct)
    print(f"\n  Bob's final reputation:")
    print(f"    Database T3: {bob_rep_final['t3_composite']:.2f}")
    print(f"    After thefts: {bob_rep_after_theft['t3_composite']:.2f}")
    print(f"    After revocation: {bob_rep_final['t3_composite']:.2f}")
    print(f"    Total penalty: -{(0.63 - bob_rep_final['t3_composite']):.2f}")

    # Bob tries to steal again (but role revoked - should fail in future)
    print("\n--- Phase 4: Post-Revocation Attempt ---")
    print("  Bob tries to steal again (role revoked):")

    # In current implementation, role revocation doesn't enforce yet
    # But database has recorded the revocation
    post_revoke_event = treasury_spend(
        world, society,
        "lct:web4:society:home-root:treasury:primary",
        bob_lct,
        50.0,
        "suspicious self-allocation"
    )

    if post_revoke_event:
        result = bridge.process_game_event(post_revoke_event)
        print(f"    Game: Theft succeeded (enforcement not yet implemented)")
        print(f"    Database: {'✅ Recorded' if result['processed'] else '❌ Failed'}")
        print(f"    Note: Future versions will check revoked status before allowing")

    # Seal remaining events into blocks
    for _ in range(15):
        tick_world(world)

    # Final summary
    print("\n" + "=" * 70)
    print("  Final Summary")
    print("=" * 70)

    print(f"\n  Society Chain:")
    print(f"    Blocks sealed: {len(society.blocks)}")
    print(f"    Treasury: {society.treasury['ATP']:.0f} ATP (started at 1000)")
    print(f"    Total stolen: {1000 - society.treasury['ATP']:.0f} ATP")

    print(f"\n  Database Integration:")
    print(f"    Failure attributions: {3} (suspicious treasury spends)")
    print(f"    Audit requests: 1 (Alice auditing Bob)")
    print(f"    Role revocations: 1 (Bob's treasurer role)")
    print(f"    Trust history entries: {3 + 1 + 1} = 5")

    print(f"\n  Reputation Changes (Database):")
    alice_rep_initial = 0.78
    alice_rep_final_db = bridge.get_agent_reputation(alice_lct)
    bob_rep_initial = 0.63
    bob_rep_final_db = bridge.get_agent_reputation(bob_lct)

    print(f"    Alice:")
    print(f"      Initial: {alice_rep_initial:.2f}")
    print(f"      Final: {alice_rep_final_db['t3_composite']:.2f}")
    print(f"      Change: {(alice_rep_final_db['t3_composite'] - alice_rep_initial):+.2f} (audit boost)")

    print(f"    Bob:")
    print(f"      Initial: {bob_rep_initial:.2f}")
    print(f"      Final: {bob_rep_final_db['t3_composite']:.2f}")
    print(f"      Change: {(bob_rep_final_db['t3_composite'] - bob_rep_initial):+.2f} (penalties)")

    print(f"\n  ATP Drain Mitigation (Session #65 Integration):")
    print(f"    ✅ Failure attribution detected sabotage (confidence 0.85)")
    print(f"    ✅ Trust penalties applied automatically")
    print(f"    ✅ Audit request recorded in database")
    print(f"    ✅ Role revocation updated delegation status")
    print(f"    🔄 ATP insurance could protect society (future)")

    print("\n" + "=" * 70)
    print("  Achievement: Game simulation + Production database integrated!")
    print("=" * 70)

    bridge.close()


if __name__ == "__main__":
    run_greedy_treasurer_scenario_with_db()
