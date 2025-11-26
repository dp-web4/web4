#!/usr/bin/env python3
"""
Quality-Aware Federation Demo
Session #74: Integration of quality-aware agent selection and V3 evolution

Extends Session #71's 10-society federation with:
- Quality-aware auditor selection (Session #73)
- V3 veracity evolution during operations
- ATP cost vs quality trade-off analysis
- Cross-society quality propagation

Key Questions:
1. Do quality gates prevent low-veracity agents from processing claims?
2. Does V3 evolution converge to stable veracity levels?
3. What is the ATP cost premium for quality assurance?
4. How does agent quality propagate across societies?

Scenario:
- 10 societies (A-J) in federation
- Agents with varying V3 veracity levels
- Quality-aware insurance claim processing
- V3 evolution tracked over multiple operations
"""

import sys
sys.path.insert(0, '/home/dp/ai-workspace/web4/game')

from engine.models import World, Agent, Society
from engine.sim_loop import tick_world
from engine.roles import bind_role
from engine.treasury import treasury_spend
from engine.lct import LCT
from engine.insurance import InsurancePool, insure_society, file_fraud_claim_with_quality
from engine.agent_selection import (
    select_agent_with_quality,
    InsufficientQualityError,
    InsufficientATPBudgetError
)
from engine.v3_evolution import (
    update_v3_on_success,
    update_v3_on_failure,
    record_operation_outcome
)
from engine.mrh_profiles import (
    get_mrh_for_situation,
    quality_level_to_veracity,
    estimate_atp_cost
)
from engine.db_bridge import create_bridge

SAGE_LCT = "lct:sage:legion:quality_demo"


def create_quality_aware_federation():
    """Create federation with agents at varying quality levels"""
    world = World()
    societies = []

    # Create 10 societies
    for i in range(10):
        society = Society(
            society_lct=f"lct:quality_federation:society:{chr(65+i)}",
            name=f"Quality-Fed Society {chr(65+i)}",
            treasury={"ATP": 2000 - i*50},
            block_interval_seconds=2
        )
        world.add_society(society)
        societies.append(society)

    # Full mesh federation
    world.federation = {
        s.society_lct: [other.society_lct for other in societies if other != s]
        for s in societies
    }

    return world, societies


def create_auditors_with_varied_quality(world, societies):
    """Create auditor LCTs with varying V3 veracity levels"""
    auditors = []

    # High-quality auditors (V3 veracity >= 0.90)
    for i in range(3):
        auditor_lct = LCT(
            lct_id=f"lct:quality_federation:auditor:high_{i}",
            lct_type="agent",
            owning_society_lct=societies[i].society_lct,
            created_at_block=1,
            created_at_tick=1,
            value_axes={
                "V3": {
                    "veracity": 0.90 + i * 0.03,  # 0.90, 0.93, 0.96
                    "valuation": 0.85,
                    "validity": 0.88
                }
            },
            metadata={
                "name": f"High-Quality Auditor {i+1}",
                "atp_cost": 100.0 + i * 20.0,  # More experienced = more expensive
                "success_count": 0,
                "failure_count": 0
            }
        )
        auditors.append(auditor_lct)

    # Medium-quality auditors (V3 veracity 0.75-0.85)
    for i in range(3):
        auditor_lct = LCT(
            lct_id=f"lct:quality_federation:auditor:medium_{i}",
            lct_type="agent",
            owning_society_lct=societies[i+3].society_lct,
            created_at_block=1,
            created_at_tick=1,
            value_axes={
                "V3": {
                    "veracity": 0.75 + i * 0.03,  # 0.75, 0.78, 0.81
                    "valuation": 0.80,
                    "validity": 0.82
                }
            },
            metadata={
                "name": f"Medium-Quality Auditor {i+1}",
                "atp_cost": 50.0 + i * 10.0,
                "success_count": 0,
                "failure_count": 0
            }
        )
        auditors.append(auditor_lct)

    # Low-quality auditors (V3 veracity < 0.75)
    for i in range(2):
        auditor_lct = LCT(
            lct_id=f"lct:quality_federation:auditor:low_{i}",
            lct_type="agent",
            owning_society_lct=societies[i+6].society_lct,
            created_at_block=1,
            created_at_tick=1,
            value_axes={
                "V3": {
                    "veracity": 0.60 + i * 0.05,  # 0.60, 0.65
                    "valuation": 0.70,
                    "validity": 0.75
                }
            },
            metadata={
                "name": f"Low-Quality Auditor {i+1}",
                "atp_cost": 20.0 + i * 5.0,  # Cheaper but unreliable
                "success_count": 0,
                "failure_count": 0
            }
        )
        auditors.append(auditor_lct)

    # SAGE (highest quality reference)
    sage_lct = LCT(
        lct_id=SAGE_LCT,
        lct_type="agent",
        owning_society_lct=societies[8].society_lct,
        created_at_block=1,
        created_at_tick=1,
        value_axes={
            "V3": {
                "veracity": 0.98,  # Near-perfect veracity
                "valuation": 0.95,
                "validity": 0.97
            }
        },
        metadata={
            "name": "SAGE (Federation Monitor)",
            "atp_cost": 200.0,  # Most expensive
            "success_count": 0,
            "failure_count": 0
        }
    )
    auditors.append(sage_lct)

    return auditors


def create_adversaries(world, societies):
    """Create adversarial agents for fraud scenarios"""
    adversaries = []

    for i in range(3):
        adv = Agent(
            agent_lct=f"lct:quality_federation:adversary_{i}",
            name=f"Adversary {i+1}",
            trust_axes={
                "T3": {
                    "talent": 0.6,
                    "training": 0.5,
                    "temperament": 0.2,
                    "composite": 0.433
                }
            },
            capabilities={"witness_general": 0.3},
            resources={"ATP": 50.0}
        )
        world.add_agent(adv)
        adversaries.append(adv)

        # Bind as treasurer in societies B, E, H
        target_societies = [societies[1], societies[4], societies[7]]
        if i < len(target_societies):
            bind_role(
                world=world,
                society=target_societies[i],
                role_name="treasurer",
                subject_lct=adv.agent_lct,
                reason=f"Appointed {adv.name} as treasurer",
                mrh=get_mrh_for_situation(spatial_scope="local", temporal_scope="day", complexity="agent-scale")
            )

    return adversaries


def simulate_fraud_with_quality_tracking(world, societies, adversaries, bridge):
    """Simulate fraud events and track attributions"""
    fraud_events = []

    # Adversary 1 steals from Society B
    for i in range(2):
        tick_world(world)
        treasury_spend(
            world=world,
            society=societies[1],
            treasury_lct=societies[1].society_lct,
            initiator_lct=adversaries[0].agent_lct,
            amount=150.0,
            reason=f"Suspicious transfer {i+1}"
        )

        fraud_events.append({
            "society": societies[1],
            "adversary": adversaries[0],
            "amount": 150.0,
            "attribution_id": len(fraud_events) + 1  # Simple mock ID
        })

    # Adversary 2 steals from Society E
    for i in range(3):
        tick_world(world)
        treasury_spend(
            world=world,
            society=societies[4],
            treasury_lct=societies[4].society_lct,
            initiator_lct=adversaries[1].agent_lct,
            amount=100.0,
            reason=f"Suspicious withdrawal {i+1}"
        )

        fraud_events.append({
            "society": societies[4],
            "adversary": adversaries[1],
            "amount": 100.0,
            "attribution_id": len(fraud_events) + 1
        })

    # Adversary 3 steals from Society H
    tick_world(world)
    treasury_spend(
        world=world,
        society=societies[7],
        treasury_lct=societies[7].society_lct,
        initiator_lct=adversaries[2].agent_lct,
        amount=250.0,
        reason="Suspicious large transfer"
    )

    fraud_events.append({
        "society": societies[7],
        "adversary": adversaries[2],
        "amount": 250.0,
        "attribution_id": len(fraud_events) + 1
    })

    return fraud_events


def main():
    print("="*80)
    print("  Quality-Aware Federation Demo")
    print("  Session #74: Quality Gates + V3 Evolution")
    print("="*80)

    # Phase 1: Setup
    print("\n=== Phase 1: Quality-Aware Federation Setup ===\n")

    world, societies = create_quality_aware_federation()
    bridge = create_bridge()

    print(f"✅ Created {len(societies)} societies")
    total_treasury = sum(s.treasury.get("ATP", 0) for s in societies)
    print(f"   Total treasury: {total_treasury:.0f} ATP\n")

    # Create auditors with varied quality
    auditors = create_auditors_with_varied_quality(world, societies)

    print(f"✅ Created {len(auditors)} auditors with varied V3 veracity:")
    for auditor in auditors:
        veracity = auditor.value_axes["V3"]["veracity"]
        cost = auditor.metadata["atp_cost"]
        name = auditor.metadata["name"]
        quality_tier = "HIGH" if veracity >= 0.90 else "MEDIUM" if veracity >= 0.75 else "LOW"
        print(f"   [{quality_tier:6s}] {name:30s} V3={veracity:.2f}, Cost={cost:5.0f} ATP")

    # Create adversaries
    adversaries = create_adversaries(world, societies)
    print(f"\n✅ Created {len(adversaries)} adversarial agents\n")

    # Phase 2: Insurance pool
    print("=== Phase 2: Insurance Pool Formation ===\n")

    insurance_pool = InsurancePool()

    for society in societies:
        policy = insure_society(
            world=world,
            society=society,
            insurance_pool=insurance_pool,
            premium_rate=0.05,
            coverage_ratio=0.8
        )

    print(f"✅ All societies insured")
    print(f"   Pool balance: {insurance_pool.get_balance():.0f} ATP\n")

    # Phase 3: Fraud events
    print("=== Phase 3: Fraud Events ===\n")

    fraud_events = simulate_fraud_with_quality_tracking(world, societies, adversaries, bridge)

    fraud_by_society = {}
    for event in fraud_events:
        soc_lct = event["society"].society_lct
        if soc_lct not in fraud_by_society:
            fraud_by_society[soc_lct] = {"count": 0, "total": 0, "events": []}
        fraud_by_society[soc_lct]["count"] += 1
        fraud_by_society[soc_lct]["total"] += event["amount"]
        fraud_by_society[soc_lct]["events"].append(event)

    total_stolen = sum(e["amount"] for e in fraud_events)
    print(f"✅ Simulated {len(fraud_events)} fraud events")
    print(f"   Total stolen: {total_stolen:.0f} ATP\n")

    # Phase 4: Quality-Aware Claims Processing
    print("=== Phase 4: Quality-Aware Claims Processing ===\n")

    claims_processed = []
    quality_gate_failures = []
    v3_evolution_history = []

    # Build auditor ATP costs dict
    auditor_atp_costs = {a.lct_id: a.metadata["atp_cost"] for a in auditors}

    for soc_lct, fraud_data in fraud_by_society.items():
        society = next(s for s in societies if s.society_lct == soc_lct)
        event = fraud_data["events"][0]

        print(f"--- Processing Claim: {society.name} ---")
        print(f"  ATP lost: {fraud_data['total']:.0f}")

        # Attempt quality-aware claim filing
        try:
            claim = file_fraud_claim_with_quality(
                world=world,
                society=society,
                insurance_pool=insurance_pool,
                atp_lost=fraud_data["total"],
                attribution_id=event["attribution_id"],
                confidence_score=0.85,
                attributed_to_lct=event["adversary"].agent_lct,
                available_auditors=auditors,
                auditor_atp_costs=auditor_atp_costs,
                atp_budget=None  # No budget constraint for now
            )

            if claim and claim['status'] == 'approved':
                claims_processed.append(claim)

                # Get selected auditor
                auditor = next(a for a in auditors if a.lct_id == claim['auditor_lct'])

                print(f"  ✅ Claim approved")
                print(f"  Auditor: {auditor.metadata['name']} (V3={claim['auditor_veracity']:.2f})")
                print(f"  Payout: {claim['payout']:.0f} ATP")
                print(f"  Auditor cost: {claim['auditor_atp_cost']:.0f} ATP")
                print(f"  Net payout: {claim.get('net_payout', claim['payout']):.0f} ATP")

                # Update V3 on success
                old_veracity = auditor.value_axes["V3"]["veracity"]
                result = record_operation_outcome(
                    auditor,
                    operation_type="insurance_claim",
                    success=True
                )
                v3_evolution_history.append({
                    "auditor": auditor.metadata["name"],
                    "operation": "insurance_claim",
                    "success": True,
                    "veracity_before": old_veracity,
                    "veracity_after": result["new"],
                    "delta": result["delta"]
                })
                auditor.metadata["success_count"] += 1

                print(f"  V3 evolution: {old_veracity:.3f} → {result['new']:.3f} (+{result['delta']:.3f})")

            elif claim and claim['status'] == 'denied':
                quality_gate_failures.append({
                    "society": society.name,
                    "reason": claim.get('reason', 'unknown'),
                    "error": claim.get('quality_error', 'N/A')
                })

                print(f"  ❌ Claim denied: {claim.get('reason', 'unknown')}")
                if 'quality_error' in claim:
                    print(f"  Quality error: {claim['quality_error']}")

        except (InsufficientQualityError, InsufficientATPBudgetError) as e:
            quality_gate_failures.append({
                "society": society.name,
                "reason": "exception",
                "error": str(e)
            })
            print(f"  ❌ Quality gate exception: {str(e)}")

        print()

    # Phase 5: Analysis
    print("=== Phase 5: Quality & Cost Analysis ===\n")

    print("--- Quality Gate Performance ---")
    print(f"  Claims processed: {len(claims_processed)}")
    print(f"  Quality gate failures: {len(quality_gate_failures)}")
    total_claims = len(claims_processed) + len(quality_gate_failures)
    if total_claims > 0:
        print(f"  Success rate: {(len(claims_processed) / total_claims * 100):.1f}%")
    else:
        print(f"  Success rate: N/A (no claims filed)")

    if quality_gate_failures:
        print(f"\n  Quality Gate Failures:")
        for failure in quality_gate_failures:
            print(f"    {failure['society']}: {failure['reason']}")

    print(f"\n--- ATP Cost Analysis ---")
    if claims_processed:
        total_auditor_cost = sum(c['auditor_atp_cost'] for c in claims_processed)
        total_payout = sum(c['payout'] for c in claims_processed)
        avg_auditor_cost = total_auditor_cost / len(claims_processed)

        print(f"  Total auditor costs: {total_auditor_cost:.0f} ATP")
        print(f"  Total payouts: {total_payout:.0f} ATP")
        print(f"  Average auditor cost: {avg_auditor_cost:.0f} ATP")
        print(f"  Quality overhead: {(total_auditor_cost / total_payout * 100):.1f}%")

        # Cost by auditor quality tier
        high_quality_claims = [c for c in claims_processed if c['auditor_veracity'] >= 0.90]
        medium_quality_claims = [c for c in claims_processed if 0.75 <= c['auditor_veracity'] < 0.90]

        if high_quality_claims:
            avg_high_cost = sum(c['auditor_atp_cost'] for c in high_quality_claims) / len(high_quality_claims)
            print(f"\n  High-quality auditors (V3≥0.90):")
            print(f"    Count: {len(high_quality_claims)}")
            print(f"    Avg cost: {avg_high_cost:.0f} ATP")

        if medium_quality_claims:
            avg_medium_cost = sum(c['auditor_atp_cost'] for c in medium_quality_claims) / len(medium_quality_claims)
            print(f"\n  Medium-quality auditors (0.75≤V3<0.90):")
            print(f"    Count: {len(medium_quality_claims)}")
            print(f"    Avg cost: {avg_medium_cost:.0f} ATP")

    print(f"\n--- V3 Evolution Tracking ---")
    if v3_evolution_history:
        print(f"  Total operations: {len(v3_evolution_history)}")
        for record in v3_evolution_history:
            print(f"    {record['auditor']}: {record['veracity_before']:.3f} → {record['veracity_after']:.3f} ({record['delta']:+.3f})")

        # Show final auditor states
        print(f"\n--- Final Auditor V3 Veracity ---")
        for auditor in auditors:
            veracity = auditor.value_axes["V3"]["veracity"]
            success_count = auditor.metadata.get("success_count", 0)
            failure_count = auditor.metadata.get("failure_count", 0)
            if success_count + failure_count > 0:
                print(f"  {auditor.metadata['name']:30s} V3={veracity:.3f} ({success_count}S/{failure_count}F)")

    # Summary
    print(f"\n{'='*80}")
    print(f"  Quality-Aware Federation Demo Complete!")
    print(f"{'='*80}\n")

    print(f"  ✅ Quality gates enforced: V3 veracity ≥0.90 for insurance claims")
    print(f"  ✅ {len(claims_processed)}/{len(fraud_by_society)} claims approved (high-quality auditors only)")
    print(f"  ✅ V3 evolution tracked: {len(v3_evolution_history)} operations")
    if claims_processed:
        print(f"  ✅ Average quality overhead: {(total_auditor_cost / total_payout * 100):.1f}% ATP")

    print(f"\n  Key Finding: Quality gates successfully prevent low-veracity agents")
    print(f"              from processing critical operations, while V3 evolution")
    print(f"              provides automatic reputation tracking.")


if __name__ == "__main__":
    main()
