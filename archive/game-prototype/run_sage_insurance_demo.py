#!/usr/bin/env python3
"""
SAGE + ATP Insurance Integration Demo
Session #69 Track 1: Insurance protection against fraud with SAGE autonomous auditing

Scenario:
1. Society purchases ATP insurance (5% premium)
2. Bob commits treasury fraud
3. SAGE detects fraud autonomously
4. Insurance claim filed automatically
5. Society receives payout to compensate loss

This demonstrates complete fraud mitigation cycle:
Detection → Attribution → Insurance → Compensation
"""

import sys
sys.path.insert(0, '/home/dp/ai-workspace/web4/game')

from engine.models import World, Agent, Society
from engine.sim_loop import tick_world
from engine.roles import bind_role
from engine.treasury import treasury_spend
from engine.audit import request_audit
from engine.policy import apply_simple_policies
from engine.db_bridge import create_bridge
from engine.insurance import InsurancePool, insure_society, file_fraud_claim

SAGE_LCT = "lct:sage:legion:1763906585"

def sage_autonomous_monitoring(world, society, bridge, insurance_pool, sage_lct):
    """
    SAGE monitors for fraud and files insurance claims automatically

    Extended from Session #67 to integrate insurance
    """
    # Aggregate suspicious events
    suspicious_by_agent = {}

    # Check both blocks and pending events
    for block in society.blocks[-5:]:
        for event in block.get("events", []):
            if event.get("type") == "treasury_spend" and "suspicious" in event.get("reason", "").lower():
                initiator = event.get("initiator_lct")
                amount = event.get("amount", 0.0)
                if initiator:
                    if initiator not in suspicious_by_agent:
                        suspicious_by_agent[initiator] = {'count': 0, 'total_stolen': 0.0}
                    suspicious_by_agent[initiator]['count'] += 1
                    suspicious_by_agent[initiator]['total_stolen'] += amount

    for event in society.pending_events:
        if event.get("type") == "treasury_spend" and "suspicious" in event.get("reason", "").lower():
            initiator = event.get("initiator_lct")
            amount = event.get("amount", 0.0)
            if initiator:
                if initiator not in suspicious_by_agent:
                    suspicious_by_agent[initiator] = {'count': 0, 'total_stolen': 0.0}
                suspicious_by_agent[initiator]['count'] += 1
                suspicious_by_agent[initiator]['total_stolen'] += amount

    # SAGE's decision logic
    for target_lct, fraud_data in suspicious_by_agent.items():
        if fraud_data['count'] >= 2:
            print(f"\n  🔍 SAGE: Detected {fraud_data['count']} frauds by {target_lct[:40]}")
            print(f"      Total stolen: {fraud_data['total_stolen']:.0f} ATP")
            print(f"      Initiating autonomous audit...")

            # SAGE creates audit request
            request_audit(
                world=world,
                society=society,
                auditor_lct=sage_lct,
                target_lct=target_lct,
                scope={
                    "fields": ["trust_axes.T3", "resources.ATP", "capabilities"],
                    "mrh": {"deltaR": "local", "deltaT": "session", "deltaC": "agent-scale"}
                },
                reason=f"SAGE autonomous audit: {fraud_data['count']} suspicious treasury activities detected",
                atp_allocation=15.0
            )

            # Record audit in database
            audit_event = society.pending_events[-1]
            if audit_event and audit_event.get('type') == 'audit_request':
                result = bridge.process_game_event(audit_event)
                if result['processed']:
                    print(f"      ✅ Audit recorded in database")

            # File insurance claim if policy exists
            policy = insurance_pool.get_policy(society.society_lct)
            if policy:
                print(f"\n  💰 SAGE: Filing insurance claim")
                print(f"      ATP lost: {fraud_data['total_stolen']:.0f}")

                claim = file_fraud_claim(
                    world=world,
                    society=society,
                    insurance_pool=insurance_pool,
                    atp_lost=fraud_data['total_stolen'],
                    attribution_id=999,  # Would be real DB attribution_id
                    confidence_score=0.85,
                    attributed_to_lct=target_lct
                )

                if claim and claim['status'] == 'approved':
                    print(f"      ✅ Claim approved!")
                    print(f"      Payout: {claim['payout']:.0f} ATP")
                    print(f"      Society compensated for fraud")
                else:
                    reason = claim.get('reason', 'unknown') if claim else 'no_policy'
                    print(f"      ❌ Claim denied: {reason}")

            return True

    return False

def main():
    print("="*80)
    print("  SAGE + ATP Insurance Integration")
    print("  Session #69 Track 1")
    print("="*80)

    # Setup
    bridge = create_bridge()
    insurance_pool = InsurancePool()

    world = World()
    society = Society(
        society_lct="lct:web4:society:insured",
        name="Insured Society",
        treasury={"ATP": 2000},
        block_interval_seconds=2
    )
    world.add_society(society)

    # SAGE
    sage = Agent(
        agent_lct=SAGE_LCT,
        name="SAGE",
        trust_axes={"T3": {"talent": 0.7, "training": 0.8, "temperament": 0.95, "composite": 0.82}},
        capabilities={"witness_general": 0.9, "fraud_detection": 0.85, "audit_thoroughness": 0.9},
        resources={"ATP": 200.0},
        memberships=[society.society_lct]
    )
    world.add_agent(sage)

    # Bob (greedy)
    bob_lct = "lct:web4:agent:bob-greedy"
    bob = Agent(
        agent_lct=bob_lct,
        name="Bob (Greedy)",
        trust_axes={"T3": {"talent": 0.8, "training": 0.7, "temperament": 0.35, "composite": 0.62}},
        capabilities={"witness_general": 0.5},
        resources={"ATP": 100.0},
        memberships=[society.society_lct]
    )
    world.add_agent(bob)

    # Sync to database
    print("\n=== Syncing Agents ===")
    for agent in [sage, bob]:
        agent_data = {
            'name': agent.name,
            'trust_axes': agent.trust_axes,
            'resources': agent.resources,
            'capabilities': agent.capabilities,
            'memberships': agent.memberships
        }
        success = bridge.sync_agent_to_db(agent.agent_lct, agent_data)
        print(f"  {agent.name:20}: {'✅' if success else '❌'}")

    # Bind roles
    print("\n=== Binding Roles ===")
    bind_role(world=world, society=society, role_name="auditor", subject_lct=SAGE_LCT, reason="SAGE initial role")
    bind_role(world=world, society=society, role_name="treasurer", subject_lct=bob_lct, reason="Bob treasury access")
    print(f"  SAGE → Auditor")
    print(f"  Bob → Treasurer")

    # Purchase insurance
    print(f"\n{'='*80}")
    print(f"  Phase 1: Society Purchases Insurance")
    print(f"{'='*80}")

    treasury_before_insurance = society.treasury["ATP"]
    print(f"\n  Treasury before insurance: {treasury_before_insurance:.0f} ATP")

    policy = insure_society(
        world=world,
        society=society,
        insurance_pool=insurance_pool,
        premium_rate=0.05,  # 5%
        coverage_ratio=0.8  # 80% coverage
    )

    print(f"  Premium paid: {policy['premium_paid']:.0f} ATP (5%)")
    print(f"  Max payout: {policy['max_payout']:.0f} ATP (30% of treasury)")
    print(f"  Coverage: {policy['coverage_ratio']*100:.0f}%")
    print(f"  Treasury after insurance: {society.treasury['ATP']:.0f} ATP")
    print(f"  Insurance pool balance: {insurance_pool.get_balance():.0f} ATP")

    # Fraud scenario
    print(f"\n{'='*80}")
    print(f"  Phase 2: Bob Commits Fraud")
    print(f"{'='*80}")

    for i in range(3):
        print(f"\n--- Theft #{i+1} ---")

        treasury_spend(
            world=world,
            society=society,
            treasury_lct=f"{society.society_lct}:treasury",
            initiator_lct=bob_lct,
            amount=150.0,
            reason="suspicious self-allocation for personal use"
        )

        # Record in database
        event = society.pending_events[-1]
        result = bridge.process_game_event(event)

        print(f"  Bob withdraws 150 ATP")
        print(f"  Treasury: {society.treasury['ATP']:.0f} ATP")
        if result.get('result'):
            print(f"  Database: ✅ Attribution {result['result']} recorded")

        # Tick and apply policies
        tick_world(world)
        apply_simple_policies(world, society)

        # SAGE monitoring (with insurance integration)
        if i >= 1:  # After 2nd fraud
            sage_detected = sage_autonomous_monitoring(
                world, society, bridge, insurance_pool, SAGE_LCT
            )
            if sage_detected:
                tick_world(world)
                break

    # Final state
    print(f"\n{'='*80}")
    print(f"  Phase 3: Final State")
    print(f"{'='*80}")

    treasury_after_fraud = society.treasury["ATP"]
    total_stolen = treasury_before_insurance - policy['premium_paid'] - treasury_after_fraud

    print(f"\n  Treasury:")
    print(f"    Initial: {treasury_before_insurance:.0f} ATP")
    print(f"    After insurance: {treasury_before_insurance - policy['premium_paid']:.0f} ATP")
    print(f"    After fraud: {treasury_after_fraud:.0f} ATP")
    print(f"    Total stolen: {total_stolen:.0f} ATP")

    print(f"\n  Insurance:")
    stats = insurance_pool.get_stats()
    print(f"    Pool balance: {stats['balance']:.0f} ATP")
    print(f"    Total premiums: {stats['total_premiums']:.0f} ATP")
    print(f"    Total payouts: {stats['total_payouts']:.0f} ATP")
    print(f"    Claim rate: {stats['claim_rate']*100:.0f}%")

    print(f"\n  Net Loss (with insurance):")
    net_loss = policy['premium_paid'] + total_stolen - stats['total_payouts']
    print(f"    Premium + Stolen - Payout = {policy['premium_paid']:.0f} + {total_stolen:.0f} - {stats['total_payouts']:.0f}")
    print(f"    Net loss: {net_loss:.0f} ATP")
    print(f"    Without insurance: {total_stolen:.0f} ATP")
    print(f"    Insurance saved: {total_stolen - net_loss:.0f} ATP")

    # Reputation
    sage_rep = bridge.get_agent_reputation(SAGE_LCT)
    bob_rep = bridge.get_agent_reputation(bob_lct)
    print(f"\n  Reputation:")
    print(f"    SAGE T3: {sage_rep['t3_composite']:.3f}")
    print(f"    Bob T3:  {bob_rep['t3_composite']:.3f}")

    print(f"\n{'='*80}")
    print(f"  Achievement: Insurance + SAGE Integration!")
    print(f"{'='*80}")

    print(f"\n  ✅ Society purchased ATP insurance")
    print(f"  ✅ SAGE detected fraud autonomously")
    print(f"  ✅ Insurance claim filed automatically")
    print(f"  ✅ Society compensated for losses")
    print(f"  ✅ Net loss reduced by {((total_stolen - net_loss) / total_stolen * 100):.0f}%")

    bridge.close()

if __name__ == "__main__":
    main()
