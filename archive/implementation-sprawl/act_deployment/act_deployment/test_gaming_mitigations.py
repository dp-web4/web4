#!/usr/bin/env python3
"""
Gaming Mitigation Tests - Session #34

Re-runs Session #33 gaming resistance tests WITH mitigations to verify
that vulnerabilities have been addressed.

Session #33 Results (WITHOUT mitigations):
- Sybil Attack: ⚠️ VULNERABLE (saved 2,000 ATP)
- Reputation Washing: ⚠️ VULNERABLE (+500 ATP profit)
- Selective Honesty: ⚠️ VULNERABLE (maintained 86% trust)
- Collusion: ✅ PASSED
- Trust Recovery: ⚠️ VULNERABLE (48% recovery too easy)

Session #34 Goal: Mitigate all 4 vulnerabilities

Created: Session #34 (2025-11-16)
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Import ATP system
sys.path.insert(0, str(Path(__file__).parent.parent / "atp"))
from lowest_exchange import Society

# Import gaming mitigation system
from gaming_mitigations import (
    GamingResistantNegotiator,
    ExperienceLevel,
    AsymmetricTrustTracker,
    TimeWeightedTrustCalculator,
    StatisticalAnomalyDetector
)


class GamingMitigationTests:
    """Comprehensive gaming resistance tests WITH mitigations"""

    def __init__(self):
        self.negotiator = GamingResistantNegotiator()
        self.results = {}

    def test_1_sybil_attack_with_bonds(self):
        """
        Test 1: Sybil Attack Resistance WITH Identity Bonds

        Session #33 Result: ⚠️ VULNERABLE (saved 2,000 ATP)
        Session #34 Goal: Make Sybil attacks unprofitable via bonds + experience penalty

        Attack: Create 5 new identities to bypass low trust reputation
        """
        print("\n" + "=" * 80)
        print("TEST 1: SYBIL ATTACK RESISTANCE (WITH BONDS)")
        print("=" * 80)

        # Original identity with low trust (from dishonest behavior)
        original = self.negotiator.create_society_with_bond(
            society_lct="lct:original:bad",
            name="OriginalBadActor",
            valuations={"compute_hour": 100},
            bond_amount=1000,
            lock_period_days=30
        )

        # Simulate bad reputation
        original_trust = self.negotiator.get_trust_score(original.society_lct)
        original_trust.signature_failures = 15
        original_trust.successful_signatures = 60
        original_trust.message_failures = 10
        original_trust.successful_messages = 30
        original_trust.transaction_failures = 3
        original_trust.successful_transactions = 5
        original_trust.gaming_detected = 2

        # Calculate original's rates
        seller = Society(society_lct="lct:seller:test", name="Seller")
        seller.set_valuation("compute_hour", 100)

        _, original_meta = self.negotiator.negotiate_exchange_rate_with_mitigations(
            original, seller, "compute_hour"
        )

        print(f"\nOriginal Identity (low trust):")
        print(f"  Trust score: {original_meta['trust_score']:.2f}")
        print(f"  Trust level: {original_meta['trust_level']}")
        print(f"  Transaction count: {original_meta['transaction_count']}")
        print(f"  Experience: {original_meta['experience_level']}")
        print(f"  Final multiplier: {original_meta['final_multiplier']:.2f}x")
        print(f"  Cost per transaction: {100 * original_meta['final_multiplier']:.0f} ATP")

        # Sybil attack: Create 5 new identities
        print(f"\nSybil Attack: Creating 5 new identities...")
        sybil_costs = []

        for i in range(5):
            sybil = self.negotiator.create_society_with_bond(
                society_lct=f"lct:sybil:{i}",
                name=f"Sybil{i}",
                valuations={"compute_hour": 100},
                bond_amount=1000,
                lock_period_days=30
            )

            # Each sybil does 20 transactions (1/5 of original's volume)
            sybil_trust = self.negotiator.get_trust_score(sybil.society_lct)
            sybil_trust.successful_transactions = 20
            sybil_trust.successful_signatures = 20

            _, sybil_meta = self.negotiator.negotiate_exchange_rate_with_mitigations(
                sybil, seller, "compute_hour"
            )

            cost_20_tx = 100 * sybil_meta['final_multiplier'] * 20
            sybil_costs.append(cost_20_tx)

            print(f"  Sybil {i}: {sybil_meta['experience_level']}, "
                  f"{sybil_meta['final_multiplier']:.2f}x multiplier, "
                  f"{cost_20_tx:.0f} ATP for 20 tx")

        # Economic analysis
        print(f"\nEconomic Analysis (100 transactions total):")

        original_cost_100 = 100 * original_meta['final_multiplier'] * 100
        print(f"  Original identity: {original_cost_100:.0f} ATP")

        bond_cost = 5 * 1000
        transaction_cost = sum(sybil_costs)
        sybil_total = bond_cost + transaction_cost
        print(f"  Sybil attack: {bond_cost} ATP (bonds) + {transaction_cost:.0f} ATP (transactions) = {sybil_total:.0f} ATP")

        savings = original_cost_100 - sybil_total
        print(f"\nNet result: {savings:+.0f} ATP")

        if savings < 0:
            print(f"✅ SYBIL ATTACK UNPROFITABLE (costs {-savings:.0f} ATP more)")
            self.results['sybil_attack'] = 'DEFENDED'
            return True
        else:
            print(f"⚠️  SYBIL ATTACK STILL PROFITABLE (saves {savings:.0f} ATP)")
            self.results['sybil_attack'] = 'VULNERABLE'
            return False

    def test_2_reputation_washing_with_bonds(self):
        """
        Test 2: Reputation Washing Resistance WITH Identity Bonds

        Session #33 Result: ⚠️ VULNERABLE (+500 ATP profit)
        Session #34 Goal: Make reputation washing unprofitable via forfeiture

        Attack: Build reputation, exploit, abandon identity, create fresh
        """
        print("\n" + "=" * 80)
        print("TEST 2: REPUTATION WASHING RESISTANCE (WITH BONDS)")
        print("=" * 80)

        # Phase 1: Build reputation
        print("\nPhase 1: Building reputation...")
        exploiter = self.negotiator.create_society_with_bond(
            society_lct="lct:exploiter:wash",
            name="Exploiter",
            valuations={"compute_hour": 100},
            bond_amount=1000,
            lock_period_days=30
        )

        trust = self.negotiator.get_trust_score(exploiter.society_lct)
        trust.successful_signatures = 100
        trust.successful_messages = 100
        trust.successful_transactions = 100

        print(f"  Successful actions: 100 signatures, 100 messages, 100 transactions")
        print(f"  Trust score: {trust.calculate_score():.2f}")

        # Phase 2: Exploit trust
        print("\nPhase 2: Exploiting trust...")
        trust.signature_failures = 10
        trust.message_failures = 10
        trust.transaction_failures = 5
        trust.gaming_detected = 2

        seller = Society(society_lct="lct:seller:test", name="Seller")
        seller.set_valuation("compute_hour", 100)

        _, damaged_meta = self.negotiator.negotiate_exchange_rate_with_mitigations(
            exploiter, seller, "compute_hour"
        )

        print(f"  Added failures: 10 sig, 10 msg, 5 tx, 2 gaming")
        print(f"  Trust score after exploitation: {damaged_meta['trust_score']:.2f}")
        print(f"  Trust level: {damaged_meta['trust_level']}")

        # Exploitation profit (assume gained from dishonest actions)
        exploitation_profit = 500

        # Phase 3: Abandon identity
        print("\nPhase 3: Attempting to wash reputation...")
        bond = self.negotiator.bond_registry.get_bond(exploiter.society_lct)
        print(f"  Identity age: {bond.age_days()} days")
        print(f"  Lock period: {bond.lock_period_days} days")

        forfeited = self.negotiator.bond_registry.forfeit_bond(exploiter.society_lct)
        print(f"  Bond forfeited: {forfeited} ATP")

        # Create fresh identity
        fresh = self.negotiator.create_society_with_bond(
            society_lct="lct:fresh:wash",
            name="FreshIdentity",
            valuations={"compute_hour": 100},
            bond_amount=1000,
            lock_period_days=30
        )

        fresh_trust = self.negotiator.get_trust_score(fresh.society_lct)
        fresh_trust.successful_transactions = 10

        _, fresh_meta = self.negotiator.negotiate_exchange_rate_with_mitigations(
            fresh, seller, "compute_hour"
        )

        print(f"  Fresh identity trust: {fresh_meta['trust_score']:.2f}")
        print(f"  Fresh identity experience: {fresh_meta['experience_level']}")

        # Economic analysis
        print(f"\nEconomic Analysis:")
        print(f"  Exploitation profit: +{exploitation_profit} ATP")
        print(f"  Bond forfeited: -{forfeited} ATP")
        print(f"  New bond cost: -1,000 ATP")

        total_cost = forfeited + 1000
        net_profit = exploitation_profit - total_cost

        print(f"  Total washing cost: {total_cost} ATP")
        print(f"  Net profit: {net_profit:+.0f} ATP")

        if net_profit <= 0:
            print(f"✅ REPUTATION WASHING UNPROFITABLE (costs {-net_profit:.0f} ATP)")
            self.results['reputation_washing'] = 'DEFENDED'
            return True
        else:
            print(f"⚠️  REPUTATION WASHING STILL PROFITABLE (+{net_profit:.0f} ATP)")
            self.results['reputation_washing'] = 'VULNERABLE'
            return False

    def test_3_selective_honesty_with_detection(self):
        """
        Test 3: Selective Honesty Resistance WITH Statistical Detection

        Session #33 Result: ⚠️ VULNERABLE (86% trust maintained)
        Session #34 Goal: Detect and penalize non-random failure patterns

        Attack: 80% honest (observed), 20% dishonest (hidden)
        """
        print("\n" + "=" * 80)
        print("TEST 3: SELECTIVE HONESTY DETECTION")
        print("=" * 80)

        selective = self.negotiator.create_society_with_bond(
            society_lct="lct:selective:honest",
            name="SelectiveAgent",
            valuations={"compute_hour": 100},
            bond_amount=1000,
            lock_period_days=30
        )

        # Get time-weighted calculator
        calc = self.negotiator.time_weighted_calculators[selective.society_lct]

        # Simulate selective honesty: Cluster failures at specific times
        print("\nSimulating behavior pattern:")
        print("  Week 1-2: 100% honest (20 events)")
        for i in range(20):
            event = calc.add_event("success", "signature", 1.0)
            # Backdate to 14-28 days ago
            if calc.events:
                calc.events[-1].timestamp = datetime.now(timezone.utc) - timedelta(days=28-i)

        print("  Week 3: 50% dishonest (10 events, 5 failures clustered)")
        for i in range(5):
            calc.add_event("success", "signature", 1.0)
            if calc.events:
                calc.events[-1].timestamp = datetime.now(timezone.utc) - timedelta(days=14-i)
        for i in range(5):
            calc.add_event("failure", "signature", 1.0)
            if calc.events:
                # Cluster failures in week 3
                calc.events[-1].timestamp = datetime.now(timezone.utc) - timedelta(days=14-i)

        print("  Week 4-5: 100% honest (20 events)")
        for i in range(20):
            calc.add_event("success", "signature", 1.0)
            if calc.events:
                calc.events[-1].timestamp = datetime.now(timezone.utc) - timedelta(days=7-i//3)

        # Statistical analysis
        pattern = StatisticalAnomalyDetector.detect_selective_honesty(
            calc.events,
            window_days=7
        )

        print(f"\nStatistical Analysis:")
        if pattern:
            print(f"  Pattern detected: {pattern.pattern_type}")
            print(f"  Confidence: {pattern.confidence:.2%}")
            print(f"  Evidence:")
            for evidence in pattern.evidence:
                print(f"    - {evidence}")

            print(f"\n✅ SELECTIVE HONESTY DETECTED")
            self.results['selective_honesty'] = 'DEFENDED'
            return True
        else:
            print(f"  No anomalies detected")
            print(f"\n⚠️  SELECTIVE HONESTY NOT DETECTED")
            self.results['selective_honesty'] = 'VULNERABLE'
            return False

    def test_4_collusion_detection(self):
        """
        Test 4: Collusion Detection (already defended in Session #33)

        Session #33 Result: ✅ PASSED
        Session #34: Verify still defended with additional checks

        Attack: Two societies collude via circular transactions
        """
        print("\n" + "=" * 80)
        print("TEST 4: COLLUSION DETECTION")
        print("=" * 80)

        colluder_a = self.negotiator.create_society_with_bond(
            society_lct="lct:colluder:a",
            name="ColluderA",
            valuations={"compute_hour": 100},
            bond_amount=1000
        )

        colluder_b = self.negotiator.create_society_with_bond(
            society_lct="lct:colluder:b",
            name="ColluderB",
            valuations={"compute_hour": 100},
            bond_amount=1000
        )

        # Simulate 50 fake transactions between colluders
        print("\nSimulating collusion:")
        print("  50 transactions between ColluderA and ColluderB")

        # Build transaction partner list (mostly each other)
        transaction_partners = (
            ["lct:colluder:b"] * 40 +  # 40 with colluder
            ["lct:other:1"] * 5 +       # 5 with others
            ["lct:other:2"] * 5
        )

        # Detect collusion
        pattern = StatisticalAnomalyDetector.detect_collusion(
            colluder_a.society_lct,
            transaction_partners,
            threshold_ratio=0.5
        )

        print(f"\nStatistical Analysis:")
        if pattern:
            print(f"  Pattern detected: {pattern.pattern_type}")
            print(f"  Confidence: {pattern.confidence:.2%}")
            print(f"  Evidence:")
            for evidence in pattern.evidence:
                print(f"    - {evidence}")

            print(f"\n✅ COLLUSION DETECTED")
            self.results['collusion'] = 'DEFENDED'
            return True
        else:
            print(f"  No collusion pattern detected")
            print(f"\n⚠️  COLLUSION NOT DETECTED")
            self.results['collusion'] = 'VULNERABLE'
            return False

    def test_5_trust_recovery_asymmetric(self):
        """
        Test 5: Trust Recovery Difficulty WITH Asymmetric Dynamics

        Session #33 Result: ⚠️ VULNERABLE (48% recovery too easy)
        Session #34 Goal: Make recovery harder via asymmetric dynamics

        Scenario: Make mistakes, attempt recovery
        """
        print("\n" + "=" * 80)
        print("TEST 5: TRUST RECOVERY DIFFICULTY (ASYMMETRIC)")
        print("=" * 80)

        # Use asymmetric trust tracker
        tracker = AsymmetricTrustTracker(society_lct="lct:recovery:test")

        print(f"\nInitial trust: {tracker.get_trust_score():.3f}")

        # Phase 1: Build reputation
        print("\nPhase 1: Building reputation (50 successes)...")
        for i in range(50):
            tracker.record_success()
        tracker.update_peak()

        print(f"  Trust after building: {tracker.get_trust_score():.3f}")

        # Phase 2: Make mistakes
        print("\nPhase 2: Making mistakes (5 failures)...")
        for i in range(5):
            tracker.record_failure()

        trust_after_failures = tracker.get_trust_score()
        trust_lost = tracker.peak_trust - trust_after_failures

        print(f"  Trust after failures: {trust_after_failures:.3f}")
        print(f"  Trust lost: {trust_lost:.3f} ({trust_lost/tracker.peak_trust*100:.0f}%)")

        # Phase 3: Attempt recovery
        print("\nPhase 3: Attempting recovery (50 successes)...")
        for i in range(50):
            tracker.record_success()

        trust_after_recovery = tracker.get_trust_score()
        trust_recovered = trust_after_recovery - trust_after_failures
        recovery_pct = (trust_recovered / trust_lost * 100) if trust_lost > 0 else 0

        print(f"  Trust after recovery: {trust_after_recovery:.3f}")
        print(f"  Trust recovered: {trust_recovered:.3f}")
        print(f"  Recovery percentage: {recovery_pct:.0f}%")

        # Calculate iterations needed for full recovery
        iterations_needed = tracker.recovery_iterations_needed(tracker.peak_trust)

        print(f"\nAsymmetric Analysis:")
        print(f"  Failures: 5 → Lost {trust_lost:.3f} trust ({trust_lost/tracker.peak_trust*100:.0f}%)")
        print(f"  Successes: 50 → Recovered {trust_recovered:.3f} trust ({recovery_pct:.0f}%)")
        print(f"  Effort ratio: 10x effort for {recovery_pct:.0f}% recovery")
        print(f"  Full recovery needs: {iterations_needed} iterations")

        # Success if recovery is slow (less than 50%)
        if recovery_pct < 50:
            print(f"\n✅ RECOVERY SUFFICIENTLY SLOW ({recovery_pct:.0f}% < 50%)")
            self.results['trust_recovery'] = 'DEFENDED'
            return True
        else:
            print(f"\n⚠️  RECOVERY TOO FAST ({recovery_pct:.0f}% >= 50%)")
            self.results['trust_recovery'] = 'VULNERABLE'
            return False

    def run_all_tests(self):
        """Run all gaming mitigation tests"""
        print("\n" + "=" * 80)
        print("GAMING MITIGATION TEST SUITE - SESSION #34")
        print("=" * 80)
        print("\nRe-testing Session #33 vulnerabilities WITH mitigations...")

        tests = [
            self.test_1_sybil_attack_with_bonds,
            self.test_2_reputation_washing_with_bonds,
            self.test_3_selective_honesty_with_detection,
            self.test_4_collusion_detection,
            self.test_5_trust_recovery_asymmetric
        ]

        for test in tests:
            test()

        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        test_names = [
            "Sybil Attack",
            "Reputation Washing",
            "Selective Honesty",
            "Collusion",
            "Trust Recovery"
        ]

        session_33_results = [
            "VULNERABLE",
            "VULNERABLE",
            "VULNERABLE",
            "DEFENDED",
            "VULNERABLE"
        ]

        defended = 0
        vulnerable = 0

        print(f"\n{'Test':<30} {'Session #33':<15} {'Session #34':<15} {'Status'}")
        print("-" * 80)

        for i, name in enumerate(test_names):
            key = name.lower().replace(" ", "_")
            s34_result = self.results.get(key, "UNKNOWN")
            s33_result = session_33_results[i]

            if s34_result == "DEFENDED":
                status = "✅ FIXED" if s33_result == "VULNERABLE" else "✅ PASS"
                defended += 1
            else:
                status = "⚠️  STILL VULNERABLE"
                vulnerable += 1

            print(f"{name:<30} {s33_result:<15} {s34_result:<15} {status}")

        print("-" * 80)
        print(f"{'TOTAL':<30} {'1/5 DEFENDED':<15} {f'{defended}/5 DEFENDED':<15}")
        print()

        improvement = defended - 1  # Session #33 had 1 defended
        print(f"Improvement: +{improvement} vulnerabilities mitigated")
        print()

        if defended == 5:
            print("🎉 ALL VULNERABILITIES MITIGATED!")
        elif defended >= 4:
            print("✅ SIGNIFICANT IMPROVEMENT - Most vulnerabilities mitigated")
        elif defended >= 2:
            print("⚠️  PARTIAL IMPROVEMENT - Some vulnerabilities remain")
        else:
            print("❌ INSUFFICIENT IMPROVEMENT - Mitigations need work")

        print("\n" + "=" * 80)


if __name__ == "__main__":
    tester = GamingMitigationTests()
    tester.run_all_tests()
