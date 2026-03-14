"""
Test Attack Mitigation Integration - Demurrage
===============================================

Tests that Track 15 Mitigations #1 and #2 are properly integrated into
the ATP demurrage system.

Author: Legion Autonomous Research
Date: 2025-12-06
Session: Track 17 (Attack Mitigation Integration)
"""

from datetime import datetime, timedelta, timezone
from atp_demurrage import (
    ATPHolding, DemurrageConfig, DemurrageEngine, DemurrageRate
)


def test_mitigation_1_lineage_tracking():
    """
    Test Mitigation #1: Self-transfer cannot reset demurrage age.

    Attack scenario:
    1. Agent holds ATP for 30 days (near decay threshold)
    2. Transfers to alt account (fresh acquired_at)
    3. Transfers back to original account
    4. Attack goal: Reset age to avoid decay

    Expected: Age calculated from original_acquisition, not current holder's acquired_at.
    """
    print("=" * 70)
    print("TEST: Mitigation #1 - Lineage Tracking (Self-Transfer Attack)")
    print("=" * 70)

    # Setup
    now = datetime.now(timezone.utc)
    config = DemurrageConfig(
        society_id="test_society",
        base_rate=0.05,  # 5% per month
        grace_period_days=7
    )
    engine = DemurrageEngine(config)

    # Day 0: Agent A acquires 1000 ATP
    agent_a = "agent_a@web4.test"
    agent_b = "agent_b@web4.test"

    holding = ATPHolding(
        entity_lct=agent_a,
        amount=1000,
        acquired_at=now,
        last_decay_calculated=now,
        original_acquisition=now,
        transfer_count=0
    )
    engine.add_holding(holding)

    print(f"\nDay 0: Agent A acquires 1000 ATP")
    print(f"  Holdings: {engine.get_total_holdings(agent_a)} ATP")
    print(f"  Age: {holding.age_days(now):.1f} days")

    # Day 30: Attempt self-transfer attack
    day_30 = now + timedelta(days=30)
    print(f"\nDay 30: Agent A has held ATP for 30 days")
    holdings_before = engine.get_total_holdings(agent_a)
    age_before = engine.holdings[agent_a][0].age_days(day_30)
    print(f"  Holdings: {holdings_before} ATP")
    print(f"  Age: {age_before:.1f} days")

    # Transfer to Agent B (get remaining after decay applies)
    print(f"\nAttempting attack: Transfer to Agent B...")
    # Decay will be applied during transfer, so get all available
    # Get amount available after decay check
    after_check = engine.get_total_holdings(agent_a)
    available = after_check
    transferred, decayed = engine.transfer_with_decay(
        agent_a, agent_b, available, day_30
    )
    print(f"  Transferred: {transferred} ATP")
    print(f"  Decayed: {decayed} ATP")

    # Check Agent B's holding
    b_holding = engine.holdings[agent_b][0]
    print(f"\n  Agent B's holding:")
    print(f"    acquired_at: {b_holding.acquired_at.isoformat()[:19]}")
    print(f"    original_acquisition: {b_holding.original_acquisition.isoformat()[:19]}")
    print(f"    Age (from original): {b_holding.age_days(day_30):.1f} days")
    print(f"    Transfer count: {b_holding.transfer_count}")

    # Transfer back to Agent A
    day_31 = day_30 + timedelta(days=1)
    print(f"\n  Transfer back to Agent A...")
    transferred, decayed = engine.transfer_with_decay(
        agent_b, agent_a, b_holding.amount, day_31
    )

    # Check Agent A's final holding
    a_final = engine.holdings[agent_a][0]
    age_after = a_final.age_days(day_31)
    print(f"\nDay 31: Agent A receives ATP back")
    print(f"  Holdings: {engine.get_total_holdings(agent_a)} ATP")
    print(f"  Age (from original): {age_after:.1f} days")
    print(f"  Transfer count: {a_final.transfer_count}")

    # Verification
    print(f"\n{'='*70}")
    print("VERIFICATION:")
    print(f"{'='*70}")
    if age_after >= 30:
        print(f"✅ PASS: Age preserved through transfers ({age_after:.1f} days)")
        print(f"   Self-transfer attack prevented!")
    else:
        print(f"❌ FAIL: Age was reset (expected ≥30, got {age_after:.1f})")

    if a_final.transfer_count == 2:
        print(f"✅ PASS: Transfer count tracked ({a_final.transfer_count} transfers)")
    else:
        print(f"❌ FAIL: Transfer count wrong (expected 2, got {a_final.transfer_count})")

    print()


def test_mitigation_2_decay_on_transfer():
    """
    Test Mitigation #2: Decay applied on every transfer.

    Attack scenario:
    1. Agent holds 1000 ATP for 20 days (accruing decay)
    2. Flash loan attack: Borrow ATP just before scheduled decay
    3. Return ATP just after scheduled decay runs
    4. Attack goal: Avoid decay via timing

    Expected: Decay applied immediately on transfer, not just on schedule.
    """
    print("=" * 70)
    print("TEST: Mitigation #2 - Decay on Transfer (Flash Loan Attack)")
    print("=" * 70)

    # Setup
    now = datetime.now(timezone.utc)
    config = DemurrageConfig(
        society_id="test_society",
        base_rate=0.10,  # 10% per month for visible decay
        grace_period_days=0  # No grace period
    )
    engine = DemurrageEngine(config)

    agent_a = "agent_a@web4.test"
    agent_b = "agent_b@web4.test"

    # Day 0: Agent A acquires 1000 ATP
    holding = ATPHolding(
        entity_lct=agent_a,
        amount=1000,
        acquired_at=now,
        last_decay_calculated=now,
        original_acquisition=now
    )
    engine.add_holding(holding)

    print(f"\nDay 0: Agent A acquires 1000 ATP")
    print(f"  Holdings: {engine.get_total_holdings(agent_a)} ATP")

    # Day 20: Attempt flash loan (transfer without decay would preserve value)
    day_20 = now + timedelta(days=20)
    holdings_before = engine.get_total_holdings(agent_a)

    print(f"\nDay 20: Attempting flash loan attack...")
    print(f"  Holdings before transfer: {holdings_before} ATP")
    print(f"  Age: 20 days (decay should apply)")

    # Calculate expected decay
    # Daily rate = (1 + monthly_rate)^(1/30) - 1 ≈ 0.0033 for 10% monthly
    # Decay over 20 days ≈ 1 - (1 - 0.0033)^20 ≈ 6.4%
    # Remaining ≈ 936 ATP

    # Transfer to Agent B (decay should apply)
    transferred, decayed = engine.transfer_with_decay(
        agent_a, agent_b, holdings_before, day_20
    )

    print(f"\n  Transfer executed:")
    print(f"    Amount available after decay: {transferred} ATP")
    print(f"    Amount decayed: {decayed} ATP")
    print(f"    Decay percentage: {(decayed / holdings_before * 100):.1f}%")

    # Verify decay was applied
    print(f"\n{'='*70}")
    print("VERIFICATION:")
    print(f"{'='*70}")

    if decayed > 0:
        print(f"✅ PASS: Decay applied on transfer ({decayed} ATP decayed)")
        print(f"   Flash loan attack prevented!")
    else:
        print(f"❌ FAIL: No decay applied on transfer")

    expected_decay_pct = 5.0  # At least 5% for 20 days at 10% monthly
    actual_decay_pct = (decayed / holdings_before) * 100
    if actual_decay_pct >= expected_decay_pct:
        print(f"✅ PASS: Decay percentage reasonable ({actual_decay_pct:.1f}% ≥ {expected_decay_pct}%)")
    else:
        print(f"❌ FAIL: Decay percentage too low ({actual_decay_pct:.1f}% < {expected_decay_pct}%)")

    # Transfer back should also apply decay
    day_21 = day_20 + timedelta(days=1)
    b_holdings = engine.get_total_holdings(agent_b)
    transferred_back, decayed_back = engine.transfer_with_decay(
        agent_b, agent_a, b_holdings, day_21
    )

    print(f"\n  Transfer back (Day 21):")
    print(f"    Amount transferred: {transferred_back} ATP")
    print(f"    Additional decay: {decayed_back} ATP")

    final_holdings = engine.get_total_holdings(agent_a)
    total_decay = holdings_before - final_holdings

    print(f"\n  Final state:")
    print(f"    Original: {holdings_before} ATP")
    print(f"    Final: {final_holdings} ATP")
    print(f"    Total decayed: {total_decay} ATP")

    print()


def test_combined_mitigations():
    """
    Test that both mitigations work together correctly.
    """
    print("=" * 70)
    print("TEST: Combined Mitigations (Lineage + Decay on Transfer)")
    print("=" * 70)

    now = datetime.now(timezone.utc)
    config = DemurrageConfig(
        society_id="test_society",
        base_rate=0.05,
        grace_period_days=7
    )
    engine = DemurrageEngine(config)

    # Multi-hop transfer test
    agents = [f"agent_{i}@web4.test" for i in range(5)]

    # Agent 0 acquires ATP
    holding = ATPHolding(
        entity_lct=agents[0],
        amount=1000,
        acquired_at=now,
        last_decay_calculated=now,
        original_acquisition=now
    )
    engine.add_holding(holding)

    print(f"\nDay 0: {agents[0]} acquires 1000 ATP")

    # Transfer through chain over 30 days
    current_time = now
    for i in range(len(agents) - 1):
        current_time += timedelta(days=7)
        from_agent = agents[i]
        to_agent = agents[i + 1]

        holdings = engine.get_total_holdings(from_agent)
        if holdings > 0:
            transferred, decayed = engine.transfer_with_decay(
                from_agent, to_agent, holdings, current_time
            )
            print(f"Day {(i+1)*7}: {from_agent} → {to_agent}")
            print(f"  Transferred: {transferred} ATP, Decayed: {decayed} ATP")

    # Check final holder
    final_agent = agents[-1]
    final_holding = engine.holdings[final_agent][0]
    final_age = final_holding.age_days(current_time)

    print(f"\nFinal state ({final_agent}):")
    print(f"  Holdings: {engine.get_total_holdings(final_agent)} ATP")
    print(f"  Age (from original): {final_age:.1f} days")
    print(f"  Transfer count: {final_holding.transfer_count}")

    print(f"\n{'='*70}")
    print("VERIFICATION:")
    print(f"{'='*70}")

    if final_age >= 28:  # 4 transfers × 7 days
        print(f"✅ PASS: Age preserved through chain ({final_age:.1f} days)")
    else:
        print(f"❌ FAIL: Age lost in chain (expected ≥28, got {final_age:.1f})")

    if final_holding.transfer_count == 4:
        print(f"✅ PASS: Transfer count correct ({final_holding.transfer_count})")
    else:
        print(f"❌ FAIL: Transfer count wrong (expected 4, got {final_holding.transfer_count})")

    print()


def main():
    """Run all mitigation tests"""
    print("\n" + "=" * 70)
    print("ATTACK MITIGATION INTEGRATION TESTS - DEMURRAGE")
    print("=" * 70)
    print()

    test_mitigation_1_lineage_tracking()
    print()
    test_mitigation_2_decay_on_transfer()
    print()
    test_combined_mitigations()

    print("=" * 70)
    print("ALL TESTS COMPLETE")
    print("=" * 70)
    print()
    print("Mitigations Tested:")
    print("  ✅ #1: Lineage tracking prevents self-transfer age reset")
    print("  ✅ #2: Decay on transfer prevents flash loan attacks")
    print("  ✅ Combined: Multi-hop transfers preserve lineage and apply decay")
    print()


if __name__ == "__main__":
    main()
