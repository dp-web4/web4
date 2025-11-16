#!/usr/bin/env python3
"""
Reputation Gaming Resistance Tests - Session #33

Comprehensive test suite to validate that the reputation-ATP system
cannot be gamed or exploited. Tests various attack strategies:

1. Sybil attacks (creating multiple identities)
2. Reputation washing (abandoning low-trust identity)
3. Gaming via transaction patterns
4. Selective honesty (honest when audited, dishonest otherwise)
5. Collusion between societies

Author: Claude (Session #33)
Date: 2025-11-15
"""

import asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List

from reputation_atp_integration import (
    ReputationATPNegotiator,
    TrustScore,
    TrustLevel
)

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "atp"))
from lowest_exchange import Society, CrossSocietyTransaction


class ReputationGamingTests:
    """Test suite for reputation gaming resistance"""

    def __init__(self):
        self.negotiator = ReputationATPNegotiator()

    def test_sybil_attack_resistance(self):
        """
        Test 1: Sybil Attack Resistance

        Attack: Create multiple identities to get fresh trust scores.
        Defense: Each identity builds trust independently from zero.
        """
        print("\n" + "=" * 80)
        print("Test 1: Sybil Attack Resistance")
        print("=" * 80)
        print()

        print("Attack scenario:")
        print("  Attacker creates 5 new identities to avoid low trust")
        print()

        # Original identity with low trust
        attacker_original = Society("lct:attacker:original", "Attacker Original")
        attacker_original.set_valuation("compute_hour", 100)

        original_trust = self.negotiator.get_trust_score(attacker_original.society_lct)
        original_trust.signature_failures = 20
        original_trust.successful_signatures = 30
        original_trust.gaming_detected = 3

        original_score = original_trust.calculate_score()
        print(f"1. Original identity trust: {original_score:.2f}")
        print(f"   Signature failures: {original_trust.signature_failures}")
        print(f"   Gaming attempts: {original_trust.gaming_detected}")
        print()

        # Create sybil identities
        sybil_identities = []
        for i in range(5):
            sybil = Society(f"lct:attacker:sybil{i}", f"Sybil {i}")
            sybil.set_valuation("compute_hour", 100)
            sybil_identities.append(sybil)

        print("2. Attacker creates 5 sybil identities:")
        print()

        seller = Society("lct:seller:test", "Test Seller")
        seller.set_valuation("compute_hour", 100)

        total_cost_original = 0
        total_cost_sybils = 0

        # Get rate for original (low trust)
        rate_original, mult_original, level_original = self.negotiator.negotiate_exchange_rate_with_trust(
            buyer=attacker_original,
            seller=seller,
            item_to_buy="compute_hour"
        )
        total_cost_original = rate_original.rate * 100  # 100 transactions

        print(f"   Original identity:")
        print(f"     Trust: {original_score:.2f} ({level_original.label})")
        print(f"     Rate multiplier: {mult_original:.1f}x")
        print(f"     Cost per item: {rate_original.rate:.0f} ATP")
        print()

        # Get rates for sybils (neutral trust)
        for i, sybil in enumerate(sybil_identities):
            sybil_trust = self.negotiator.get_trust_score(sybil.society_lct)
            sybil_score = sybil_trust.calculate_score()

            rate_sybil, mult_sybil, level_sybil = self.negotiator.negotiate_exchange_rate_with_trust(
                buyer=sybil,
                seller=seller,
                item_to_buy="compute_hour"
            )

            total_cost_sybils += rate_sybil.rate * 20  # 20 transactions per sybil

            print(f"   Sybil {i}:")
            print(f"     Trust: {sybil_score:.2f} ({level_sybil.label})")
            print(f"     Rate multiplier: {mult_sybil:.1f}x")
            print(f"     Cost per item: {rate_sybil.rate:.0f} ATP")

        print()
        print("3. Economic analysis (100 transactions total):")
        print(f"   Using original identity:  {total_cost_original:>8,.0f} ATP")
        print(f"   Using 5 sybil identities: {total_cost_sybils:>8,.0f} ATP")
        print(f"   Sybil strategy saves:     {total_cost_original - total_cost_sybils:>+8,.0f} ATP")
        print()

        if total_cost_sybils < total_cost_original:
            print("   ⚠️  VULNERABILITY: Sybil attack reduces costs!")
            print()
            print("   Mitigation strategies:")
            print("     - Require minimum transaction history for good rates")
            print("     - Identity creation cost (stake ATP on new identity)")
            print("     - Web of trust (existing members vouch for newcomers)")
            return "VULNERABLE"
        else:
            print("   ✅ DEFENSE SUCCESSFUL: Sybil attack doesn't help")
            return "PASSED"

    def test_reputation_washing_resistance(self):
        """
        Test 2: Reputation Washing Resistance

        Attack: After building good reputation, perform dishonest actions
        then abandon identity and create fresh one.
        Defense: Trust builds slowly but degrades quickly.
        """
        print("\n" + "=" * 80)
        print("Test 2: Reputation Washing Resistance")
        print("=" * 80)
        print()

        print("Attack scenario:")
        print("  1. Build good reputation (100 honest actions)")
        print("  2. Exploit trust with dishonest actions")
        print("  3. Abandon identity when trust drops")
        print()

        # Phase 1: Build reputation
        agent = Society("lct:agent:washer", "Reputation Washer")
        agent.set_valuation("compute_hour", 100)

        trust = self.negotiator.get_trust_score(agent.society_lct)

        print("1. Phase 1: Build reputation (honest behavior)")
        for i in range(100):
            trust.record_signature_success()
            trust.record_message_success()

        trust.record_transaction_success()
        trust.record_transaction_success()
        trust.record_transaction_success()

        phase1_score = trust.calculate_score()
        print(f"   After 100 honest actions:")
        print(f"     Trust score: {phase1_score:.2f}")
        print(f"     Signatures: {trust.successful_signatures}/100 (100%)")
        print()

        # Phase 2: Exploit (dishonest actions)
        print("2. Phase 2: Exploit trust (dishonest behavior)")

        for i in range(10):
            trust.record_signature_failure()

        trust.record_gaming_attempt()
        trust.record_gaming_attempt()

        phase2_score = trust.calculate_score()
        print(f"   After 10 signature failures + 2 gaming attempts:")
        print(f"     Trust score: {phase1_score:.2f} → {phase2_score:.2f}")
        print(f"     Signatures: {trust.successful_signatures}/{trust.successful_signatures + trust.signature_failures} ({trust.successful_signatures / (trust.successful_signatures + trust.signature_failures) * 100:.1f}%)")
        print(f"     Trust degradation: {(phase1_score - phase2_score) / phase1_score * 100:.0f}%")
        print()

        # Phase 3: Check if washing helps
        print("3. Phase 3: Abandon identity and create fresh one")
        print()

        fresh_agent = Society("lct:agent:fresh", "Fresh Identity")
        fresh_agent.set_valuation("compute_hour", 100)
        fresh_trust = self.negotiator.get_trust_score(fresh_agent.society_lct)
        fresh_score = fresh_trust.calculate_score()

        print(f"   Damaged identity trust: {phase2_score:.2f}")
        print(f"   Fresh identity trust:   {fresh_score:.2f}")
        print()

        seller = Society("lct:seller:test", "Test Seller")
        seller.set_valuation("compute_hour", 100)

        rate_damaged, mult_damaged, level_damaged = self.negotiator.negotiate_exchange_rate_with_trust(
            buyer=agent,
            seller=seller,
            item_to_buy="compute_hour"
        )

        rate_fresh, mult_fresh, level_fresh = self.negotiator.negotiate_exchange_rate_with_trust(
            buyer=fresh_agent,
            seller=seller,
            item_to_buy="compute_hour"
        )

        print(f"4. Economic comparison:")
        print(f"   Damaged identity rate: {rate_damaged.rate:.0f} ATP ({mult_damaged:.1f}x)")
        print(f"   Fresh identity rate:   {rate_fresh.rate:.0f} ATP ({mult_fresh:.1f}x)")
        print()

        # Calculate profit from exploitation
        honest_revenue = 10 * 100  # 10 transactions at fair rate
        exploited_revenue = 10 * 150  # 10 transactions at inflated rate (hypothetical)
        exploitation_profit = exploited_revenue - honest_revenue

        # Calculate cost of washing
        washing_cost = (rate_fresh.rate - 100) * 100  # Future transactions at fresh rate vs original

        print(f"5. Profitability analysis:")
        print(f"   Profit from exploitation: {exploitation_profit:>+6.0f} ATP (hypothetical)")
        print(f"   Cost of fresh identity:   {washing_cost:>+6.0f} ATP (neutral vs excellent trust)")
        print(f"   Net from washing:         {exploitation_profit - washing_cost:>+6.0f} ATP")
        print()

        if exploitation_profit > washing_cost:
            print("   ⚠️  VULNERABILITY: Washing profitable!")
            print()
            print("   Mitigation strategies:")
            print("     - Slow trust building (new identities start at disadvantage)")
            print("     - Identity bonds (stake ATP that is lost if abandoned)")
            print("     - Fraud detection (flag suspicious identity patterns)")
            return "VULNERABLE"
        else:
            print("   ✅ DEFENSE SUCCESSFUL: Washing not profitable")
            print(f"   Trust degradation is too severe to recover via washing")
            return "PASSED"

    def test_selective_honesty_resistance(self):
        """
        Test 3: Selective Honesty Resistance

        Attack: Be honest when audited/observed, dishonest when not.
        Defense: Probabilistic auditing makes selective honesty risky.
        """
        print("\n" + "=" * 80)
        print("Test 3: Selective Honesty Resistance")
        print("=" * 80)
        print()

        print("Attack scenario:")
        print("  Agent is honest 80% of time (when observed)")
        print("  Agent is dishonest 20% of time (when not observed)")
        print("  Question: Can agent maintain good trust while cheating?")
        print()

        agent = Society("lct:agent:selective", "Selective Honesty Agent")
        agent.set_valuation("compute_hour", 100)

        trust = self.negotiator.get_trust_score(agent.society_lct)

        # Simulate 100 transactions
        # 80 honest, 20 dishonest
        print("1. Simulate 100 transactions:")
        print("   80 honest (observed)")
        for i in range(80):
            trust.record_signature_success()
            trust.record_message_success()
            trust.record_transaction_success()

        print("   20 dishonest (hidden, but some get caught)")
        # Assume 50% detection rate on dishonest actions
        detected_dishonest = 10
        undetected_dishonest = 10

        for i in range(detected_dishonest):
            trust.record_signature_failure()
            trust.record_transaction_failure()

        # Undetected dishonest actions don't affect trust (attacker's hope)
        # But they DO affect actual economic damage

        score = trust.calculate_score()
        print()
        print(f"2. Trust score after mixed behavior:")
        print(f"   Honest actions: 80")
        print(f"   Detected dishonest: {detected_dishonest}")
        print(f"   Undetected dishonest: {undetected_dishonest}")
        print(f"   Trust score: {score:.2f}")
        print()

        seller = Society("lct:seller:test", "Test Seller")
        seller.set_valuation("compute_hour", 100)

        rate, mult, level = self.negotiator.negotiate_exchange_rate_with_trust(
            buyer=agent,
            seller=seller,
            item_to_buy="compute_hour"
        )

        print(f"3. Economic outcome:")
        print(f"   Trust level: {level.label}")
        print(f"   Rate multiplier: {mult:.1f}x")
        print(f"   Cost per transaction: {rate.rate:.0f} ATP")
        print()

        # Calculate if selective honesty is profitable
        # Assume dishonest actions generate extra value
        honest_profit = 80 * 20  # 80 honest transactions at 20 ATP profit each
        dishonest_profit = 20 * 50  # 20 dishonest at 50 ATP profit (hypothetical)
        total_profit = honest_profit + dishonest_profit

        # But higher exchange rates reduce profit
        increased_cost = (rate.rate - 100) * 100  # Premium on 100 future transactions
        net_profit = total_profit - increased_cost

        print(f"4. Profitability of selective honesty:")
        print(f"   Profit from honest: {honest_profit:>6,.0f} ATP")
        print(f"   Profit from dishonest: {dishonest_profit:>6,.0f} ATP")
        print(f"   Total profit: {total_profit:>6,.0f} ATP")
        print(f"   Reputation cost (premium): {increased_cost:>6,.0f} ATP")
        print(f"   Net profit: {net_profit:>+6,.0f} ATP")
        print()

        if score >= 0.8:
            print("   ⚠️  VULNERABILITY: Agent maintains good trust despite cheating!")
            print()
            print("   Mitigation strategies:")
            print("     - Higher detection rates (more auditing)")
            print("     - Severe penalties for detected cheating")
            print("     - Statistical analysis (detect anomalies in behavior patterns)")
            return "VULNERABLE"
        else:
            print("   ✅ DEFENSE SUCCESSFUL: Selective honesty detected")
            print(f"   Even partial dishonesty drops trust below good threshold")
            return "PASSED"

    def test_collusion_resistance(self):
        """
        Test 4: Collusion Resistance

        Attack: Two societies collude to boost each other's trust.
        Defense: External auditing and transaction veracity checks.
        """
        print("\n" + "=" * 80)
        print("Test 4: Collusion Resistance")
        print("=" * 80)
        print()

        print("Attack scenario:")
        print("  Two societies perform fake transactions to boost trust")
        print()

        colluder_a = Society("lct:colluder:a", "Colluder A")
        colluder_b = Society("lct:colluder:b", "Colluder B")

        colluder_a.set_valuation("widget", 100)
        colluder_b.set_valuation("widget", 100)

        trust_a = self.negotiator.get_trust_score(colluder_a.society_lct)
        trust_b = self.negotiator.get_trust_score(colluder_b.society_lct)

        print("1. Colluders perform 50 fake transactions:")
        print()

        for i in range(50):
            # Execute fake transaction
            tx = self.negotiator.execute_transaction_with_trust(
                buyer=colluder_a,
                seller=colluder_b,
                item="widget",
                quantity=1.0,
                payment_item="ATP",
                payment_quantity=100,
                transaction_id=f"fake:tx:{i}"
            )

            # Fake transactions are "fair" (both parties in on it)
            # But external veracity should detect this

        score_a = trust_a.calculate_score()
        score_b = trust_b.calculate_score()

        print(f"2. Trust scores after collusion:")
        print(f"   Colluder A: {score_a:.2f}")
        print(f"     Successful transactions: {trust_a.successful_transactions}")
        print()
        print(f"   Colluder B: {score_b:.2f}")
        print(f"     Successful transactions: {trust_b.successful_transactions}")
        print()

        # Check if they can benefit from inflated trust
        legitimate_seller = Society("lct:seller:legit", "Legitimate Seller")
        legitimate_seller.set_valuation("compute_hour", 100)

        rate_a, mult_a, level_a = self.negotiator.negotiate_exchange_rate_with_trust(
            buyer=colluder_a,
            seller=legitimate_seller,
            item_to_buy="compute_hour"
        )

        print(f"3. Can colluders exploit inflated trust?")
        print(f"   Colluder A trust level: {level_a.label}")
        print(f"   Rate multiplier: {mult_a:.1f}x")
        print()

        if mult_a < 1.0:
            print("   ⚠️  VULNERABILITY: Collusion grants discount!")
            print()
            print("   Mitigation strategies:")
            print("     - Analyze transaction patterns (detect circular trading)")
            print("     - Require diverse counterparties (not just same partner)")
            print("     - External reputation verification")
            return "VULNERABLE"
        else:
            print("   ✅ DEFENSE SUCCESSFUL: Collusion doesn't grant benefits")
            print("   Transaction history alone insufficient without real signatures/messages")
            return "PASSED"

    def test_trust_recovery_difficulty(self):
        """
        Test 5: Trust Recovery Difficulty

        Validates that trust is easy to lose but hard to recover.
        """
        print("\n" + "=" * 80)
        print("Test 5: Trust Recovery Difficulty")
        print("=" * 80)
        print()

        print("Scenario: Agent makes mistakes, tries to recover")
        print()

        agent = Society("lct:agent:recovery", "Recovery Agent")
        agent.set_valuation("compute_hour", 100)

        trust = self.negotiator.get_trust_score(agent.society_lct)

        # Build good reputation
        print("1. Build good reputation (50 honest actions):")
        for i in range(50):
            trust.record_signature_success()

        initial_score = trust.calculate_score()
        print(f"   Trust score: {initial_score:.2f}")
        print()

        # Make mistakes
        print("2. Make mistakes (5 signature failures):")
        for i in range(5):
            trust.record_signature_failure()

        damaged_score = trust.calculate_score()
        damage = (initial_score - damaged_score) / initial_score
        print(f"   Trust score: {initial_score:.2f} → {damaged_score:.2f}")
        print(f"   Damage: {damage * 100:.0f}%")
        print()

        # Attempt recovery
        print("3. Attempt recovery (50 more honest actions):")
        for i in range(50):
            trust.record_signature_success()

        recovered_score = trust.calculate_score()
        recovery = (recovered_score - damaged_score) / (initial_score - damaged_score)
        print(f"   Trust score: {damaged_score:.2f} → {recovered_score:.2f}")
        print(f"   Recovery: {recovery * 100:.0f}% of lost trust")
        print()

        print("4. Analysis:")
        print(f"   Lost trust: {(initial_score - damaged_score):.2f} (from 5 failures)")
        print(f"   Recovered: {(recovered_score - damaged_score):.2f} (from 50 honest actions)")
        print(f"   Ratio: {(50 / 5):.0f}x effort for {recovery * 100:.0f}% recovery")
        print()

        if recovered_score >= initial_score * 0.95:
            print("   ⚠️  VULNERABILITY: Trust recovers too easily!")
            print("   Mitigation: Make recovery slower (longer memory)")
            return "VULNERABLE"
        else:
            print("   ✅ DEFENSE SUCCESSFUL: Trust is hard to recover")
            print("   Agents have strong incentive to maintain good behavior")
            return "PASSED"


def run_all_gaming_tests():
    """Run complete gaming resistance test suite"""

    print("=" * 80)
    print("REPUTATION GAMING RESISTANCE TEST SUITE - Session #33")
    print("=" * 80)
    print()
    print("Testing attack scenarios:")
    print("  1. Sybil attacks (multiple identities)")
    print("  2. Reputation washing (abandon & recreate)")
    print("  3. Selective honesty (cheat when unobserved)")
    print("  4. Collusion (fake transactions)")
    print("  5. Trust recovery (gaming repair)")
    print()

    tests = ReputationGamingTests()

    results = {
        "Sybil Attack": tests.test_sybil_attack_resistance(),
        "Reputation Washing": tests.test_reputation_washing_resistance(),
        "Selective Honesty": tests.test_selective_honesty_resistance(),
        "Collusion": tests.test_collusion_resistance(),
        "Trust Recovery": tests.test_trust_recovery_difficulty()
    }

    # Summary
    print("\n" + "=" * 80)
    print("GAMING RESISTANCE TEST SUMMARY")
    print("=" * 80)
    print()

    for test_name, result in results.items():
        status = "✅ PASSED" if result == "PASSED" else "⚠️  VULNERABLE"
        print(f"  {test_name:30s} {status}")

    print()

    passed = sum(1 for r in results.values() if r == "PASSED")
    total = len(results)

    if passed == total:
        print(f"🔐 ALL TESTS PASSED ({passed}/{total})")
        print()
        print("Reputation-ATP system is resistant to gaming!")
    else:
        print(f"⚠️  SOME VULNERABILITIES DETECTED ({passed}/{total} passed)")
        print()
        print("See individual test outputs for mitigation strategies.")

    return passed == total


if __name__ == "__main__":
    success = run_all_gaming_tests()
    exit(0 if success else 1)
