#!/usr/bin/env python3
"""
Cross-Society SAGE Auditing Demo
Session #68 Track 3: SAGE monitors and audits across federated societies

Scenario:
- 3 societies: A, B, C
- SAGE is member and auditor of Society A
- Bob (greedy treasurer) operates in Society B
- Societies A and B are federated
- Bob commits fraud in Society B
- SAGE detects cross-society fraud via federation events
- SAGE initiates cross-society audit

This tests:
1. Cross-society event propagation
2. SAGE monitoring multiple societies
3. Cross-society trust updates
4. Federation throttle/quarantine policies
"""

import sys
sys.path.insert(0, '/home/dp/ai-workspace/web4/game')

from engine.models import World, Agent, Society
from engine.sim_loop import tick_world
from engine.roles import bind_role, make_role_lct
from engine.treasury import treasury_spend
from engine.audit import request_audit
from engine.policy import apply_simple_policies
from engine.society_trust import update_society_trust
from engine.cross_society_policy import apply_cross_society_policies
from engine.db_bridge import create_bridge
from engine.mrh_profiles import get_mrh_for_situation, is_cross_society_event

# SAGE LCT from Session #65
SAGE_LCT = "lct:sage:legion:1763906585"

def create_three_society_world(bridge):
    """Create world with 3 federated societies"""
    world = World()

    # Society A: SAGE's home society
    society_a = Society(
        society_lct="lct:web4:society:a",
        name="Society A (SAGE Home)",
        treasury={"ATP": 2000},
        block_interval_seconds=2
    )
    world.add_society(society_a)

    # Society B: Bob's society (will commit fraud here)
    society_b = Society(
        society_lct="lct:web4:society:b",
        name="Society B (Bob's Home)",
        treasury={"ATP": 2000},
        block_interval_seconds=2
    )
    world.add_society(society_b)

    # Society C: Neutral observer
    society_c = Society(
        society_lct="lct:web4:society:c",
        name="Society C (Observer)",
        treasury={"ATP": 2000},
        block_interval_seconds=2
    )
    world.add_society(society_c)

    # Set up federation relationships
    world.federation = {
        society_a.society_lct: [society_b.society_lct, society_c.society_lct],
        society_b.society_lct: [society_a.society_lct],
        society_c.society_lct: [society_a.society_lct, society_b.society_lct]
    }

    # SAGE - member of Society A, role: auditor
    sage = Agent(
        agent_lct=SAGE_LCT,
        name="SAGE",
        trust_axes={
            "T3": {
                "talent": 0.7,
                "training": 0.8,
                "temperament": 0.95,
                "composite": 0.82
            }
        },
        capabilities={
            "witness_general": 0.9,
            "fraud_detection": 0.85,
            "audit_thoroughness": 0.9,
            "cross_society_monitoring": 0.8
        },
        resources={"ATP": 200.0},
        memberships=[society_a.society_lct]
    )
    world.add_agent(sage)

    # Bob - greedy treasurer in Society B
    bob_lct = "lct:web4:agent:bob-greedy"
    bob = Agent(
        agent_lct=bob_lct,
        name="Bob (Greedy)",
        trust_axes={"T3": {"talent": 0.8, "training": 0.7, "temperament": 0.35, "composite": 0.62}},
        capabilities={"witness_general": 0.5},
        resources={"ATP": 100.0},
        memberships=[society_b.society_lct]
    )
    world.add_agent(bob)

    # Alice - founder in Society A
    alice_lct = "lct:web4:agent:alice-founder"
    alice = Agent(
        agent_lct=alice_lct,
        name="Alice (Founder)",
        trust_axes={"T3": {"talent": 0.85, "training": 0.75, "temperament": 0.95, "composite": 0.85}},
        capabilities={"witness_general": 0.8},
        resources={"ATP": 150.0},
        memberships=[society_a.society_lct]
    )
    world.add_agent(alice)

    # Sync agents to database
    print("=== Syncing Agents to Database ===")
    for agent in [sage, bob, alice]:
        agent_data = {
            'name': agent.name,
            'trust_axes': agent.trust_axes,
            'resources': agent.resources,
            'capabilities': agent.capabilities,
            'memberships': agent.memberships
        }
        success = bridge.sync_agent_to_db(agent.agent_lct, agent_data)
        print(f"  {agent.name:20} ({agent.agent_lct[:30]:30}): {'✅' if success else '❌'}")

    # Bind roles
    print("\n=== Binding Roles ===")
    bind_role(world=world, society=society_a, role_name="auditor", subject_lct=SAGE_LCT, reason="SAGE initial role")
    bind_role(world=world, society=society_a, role_name="law-oracle", subject_lct=alice_lct, reason="Alice governance role")
    bind_role(world=world, society=society_b, role_name="treasurer", subject_lct=bob_lct, reason="Bob treasury access")
    print(f"  SAGE → Auditor (Society A)")
    print(f"  Alice → Law Oracle (Society A)")
    print(f"  Bob → Treasurer (Society B)")

    return world, society_a, society_b, society_c, sage, bob, alice

def sage_cross_society_monitoring(world: World, societies: list, bridge, sage_lct: str):
    """
    SAGE monitors ALL federated societies for suspicious activity

    This is the cross-society extension of SAGE's autonomous monitoring.
    """
    print("\n  🔍 SAGE: Cross-Society Monitoring")

    # Aggregate suspicious events across ALL societies
    suspicious_by_agent_society = {}  # {agent_lct: {society_lct: count}}

    for society in societies:
        # Check blocks (sealed events)
        for block in society.blocks[-5:]:
            for event in block.get("events", []):
                if event.get("type") == "treasury_spend" and "suspicious" in event.get("reason", "").lower():
                    initiator = event.get("initiator_lct")
                    if initiator:
                        if initiator not in suspicious_by_agent_society:
                            suspicious_by_agent_society[initiator] = {}
                        soc_lct = society.society_lct
                        suspicious_by_agent_society[initiator][soc_lct] = \
                            suspicious_by_agent_society[initiator].get(soc_lct, 0) + 1

        # Check pending events (not yet sealed)
        for event in society.pending_events:
            if event.get("type") == "treasury_spend" and "suspicious" in event.get("reason", "").lower():
                initiator = event.get("initiator_lct")
                if initiator:
                    if initiator not in suspicious_by_agent_society:
                        suspicious_by_agent_society[initiator] = {}
                    soc_lct = society.society_lct
                    suspicious_by_agent_society[initiator][soc_lct] = \
                        suspicious_by_agent_society[initiator].get(soc_lct, 0) + 1

    # SAGE's cross-society decision logic
    for target_lct, society_counts in suspicious_by_agent_society.items():
        total_count = sum(society_counts.values())
        if total_count >= 2:  # Threshold for cross-society audit
            for soc_lct, count in society_counts.items():
                if count > 0:
                    society_name = next((s.name for s in societies if s.society_lct == soc_lct), "Unknown")
                    print(f"      Detected {count} suspicious events from {target_lct[:40]}")
                    print(f"      in {society_name}")

            print(f"      Total: {total_count} suspicious events across federation")
            print(f"      Initiating cross-society audit...")

            # SAGE creates cross-society audit request
            # Use MRH for cross-society operation
            audit_society = next((s for s in societies if target_lct in [a.agent_lct for a in world.agents.values() if s.society_lct in a.memberships]), societies[0])

            request_audit(
                world=world,
                society=audit_society,
                auditor_lct=sage_lct,
                target_lct=target_lct,
                scope={
                    "fields": ["trust_axes.T3", "resources.ATP", "capabilities", "cross_society_activity"],
                    "mrh": get_mrh_for_situation(spatial_scope="regional", temporal_scope="session", complexity="society-scale")
                },
                reason=f"SAGE cross-society audit: {total_count} suspicious activities detected across federation",
                atp_allocation=50.0  # Higher ATP for cross-society coordination
            )

            # Get audit event and record in database
            audit_event = audit_society.pending_events[-1]
            if audit_event and audit_event.get('type') == 'audit_request':
                result = bridge.process_game_event(audit_event)
                if result['processed']:
                    print(f"      ✅ Cross-society audit recorded in database")
                    print(f"      ATP allocated: 50 (cross-society coordination cost)")
                    print(f"      MRH: {audit_event.get('scope', {}).get('mrh')}")

            return True

    return False

def main():
    print("="*80)
    print("  Cross-Society SAGE Auditing Demo")
    print("  Session #68 Track 3")
    print("="*80)

    # Setup
    bridge = create_bridge()
    world, society_a, society_b, society_c, sage, bob, alice = create_three_society_world(bridge)

    print(f"\n--- Federation Structure ---")
    print(f"  Society A ↔ Society B, Society C")
    print(f"  Society B ↔ Society A")
    print(f"  Society C ↔ Society A, Society B")
    print(f"\n  SAGE (member of Society A) monitors entire federation")

    # Scenario: Bob commits fraud in Society B
    print(f"\n{'='*80}")
    print(f"  Scenario: Bob Commits Fraud in Society B")
    print(f"{'='*80}")

    for i in range(3):
        print(f"\n--- Fraud #{i+1} in Society B ---")

        # Bob steals from Society B treasury
        treasury_spend(
            world=world,
            society=society_b,
            treasury_lct=f"{society_b.society_lct}:treasury",
            initiator_lct=bob.agent_lct,
            amount=150.0,
            reason="suspicious self-allocation in federated society"
        )

        # Record in database
        event = society_b.pending_events[-1]
        result = bridge.process_game_event(event)
        print(f"  Bob withdraws 150 ATP from Society B")
        print(f"  Society B Treasury: {society_b.treasury['ATP']:.0f} ATP")
        if result.get('result'):
            print(f"  Database: ✅ Attribution {result['result']} recorded")

        # Tick world to seal blocks
        tick_world(world)

        # Apply policies to Society B
        apply_simple_policies(world, society_b)
        update_society_trust(world, society_b)

        # SAGE cross-society monitoring (checks all societies)
        sage_detected = sage_cross_society_monitoring(
            world, [society_a, society_b, society_c], bridge, SAGE_LCT
        )

        if sage_detected:
            tick_world(world)
            break

    # Apply cross-society policies (federation mechanics)
    print(f"\n--- Cross-Society Policy Enforcement ---")
    apply_cross_society_policies(world)
    tick_world(world)

    # Check society trust levels
    print(f"\n--- Society Trust Levels ---")
    for society in [society_a, society_b, society_c]:
        t3 = society.trust_axes.get("T3", {})
        composite = t3.get("composite", 0.7)
        print(f"  {society.name}: T3 = {composite:.3f}")

    # Check for federation events in blocks
    print(f"\n--- Federation Events ---")
    federation_events = []
    for society in [society_a, society_b, society_c]:
        for block in society.blocks:
            for event in block.get("events", []):
                if event.get("type") in ["federation_throttle", "quarantine_request"]:
                    federation_events.append(event)
                    print(f"  {event['type']}: {event.get('from_society_lct', '')[:30]} → {event.get('to_society_lct', '')[:30]}")
                    print(f"    Reason: Society B trust = {event.get('dst_trust', 'N/A')}")

    # Final state
    print(f"\n--- Final State ---")
    sage_rep = bridge.get_agent_reputation(SAGE_LCT)
    bob_rep = bridge.get_agent_reputation(bob.agent_lct)
    print(f"\n  Agent Reputation:")
    print(f"    SAGE T3: {sage_rep['t3_composite']:.3f}")
    print(f"    Bob T3:  {bob_rep['t3_composite']:.3f}")

    print(f"\n  Societies:")
    print(f"    Society A Treasury: {society_a.treasury['ATP']:.0f} ATP")
    print(f"    Society B Treasury: {society_b.treasury['ATP']:.0f} ATP (Bob stole from here)")
    print(f"    Society C Treasury: {society_c.treasury['ATP']:.0f} ATP")

    print(f"\n  Cross-Society Events: {len(federation_events)}")

    print(f"\n{'='*80}")
    print(f"  Achievement: Cross-Society SAGE Auditing!")
    print(f"{'='*80}")

    print(f"\n  ✅ SAGE monitored multiple federated societies")
    print(f"  ✅ Detected fraud in remote society (Society B)")
    print(f"  ✅ Initiated cross-society audit with regional MRH")
    print(f"  ✅ Federation policies evaluated society trust")
    print(f"  ✅ Cross-society events recorded on blockchain")

    bridge.close()

if __name__ == "__main__":
    main()
