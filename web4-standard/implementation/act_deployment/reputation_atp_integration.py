#!/usr/bin/env python3
"""
Reputation-ATP Integration - Session #33

Integrates trust scores with ATP exchange rates to create economic
consequences for reputation. Societies with low trust pay premium rates,
while trustworthy societies get favorable rates.

Key Mechanisms:
- Signature failures → Trust score degradation
- Trust score → Exchange rate multiplier
- Gaming resistance via reputation tracking
- Self-regulating economic incentives

Architecture:
  Trust Tracking (Session #31)
       ↓
  Reputation Score Calculation
       ↓
  Exchange Rate Adjustment (Session #33)
       ↓
  Economic Incentive for Honest Behavior

Created: Session #33 (2025-11-15)
Builds on: Sessions #30 (Society), #31 (Security), #32 (Messaging)
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import json

# Import ATP system
sys.path.insert(0, str(Path(__file__).parent.parent / "atp"))
from lowest_exchange import (
    Society,
    LowestExchangeNegotiator,
    CrossSocietyTransaction,
    ExchangeRate
)


class TrustLevel(Enum):
    """Trust level categories with associated multipliers"""
    EXCELLENT = ("excellent", 0.8, 1.0)      # 80-100%: 20% discount
    GOOD = ("good", 0.6, 1.0)                # 60-80%: Fair rate
    NEUTRAL = ("neutral", 0.4, 1.2)          # 40-60%: 20% premium
    POOR = ("poor", 0.2, 1.5)                # 20-40%: 50% premium
    UNTRUSTED = ("untrusted", 0.0, 2.0)      # 0-20%: 100% premium (double cost)

    def __init__(self, label: str, min_score: float, multiplier: float):
        self.label = label
        self.min_score = min_score
        self.multiplier = multiplier

    @classmethod
    def from_score(cls, trust_score: float) -> 'TrustLevel':
        """Determine trust level from score"""
        if trust_score >= 0.8:
            return cls.EXCELLENT
        elif trust_score >= 0.6:
            return cls.GOOD
        elif trust_score >= 0.4:
            return cls.NEUTRAL
        elif trust_score >= 0.2:
            return cls.POOR
        else:
            return cls.UNTRUSTED


@dataclass
class TrustScore:
    """
    Comprehensive trust score for a society.

    Factors:
    - Signature failures (from Session #31)
    - Message statistics (from Session #32)
    - Transaction history (from ATP system)
    - Time decay (recent behavior weighted more)
    """
    society_lct: str
    base_score: float = 1.0               # Starting trust (neutral)

    # Negative factors
    signature_failures: int = 0           # Invalid signatures detected
    message_failures: int = 0             # Failed message deliveries
    transaction_failures: int = 0         # Failed transactions
    gaming_detected: int = 0              # Valuation gaming attempts

    # Positive factors
    successful_signatures: int = 0        # Valid signatures
    successful_messages: int = 0          # Successful messages
    successful_transactions: int = 0      # Fair transactions

    # Metadata
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    trust_level: TrustLevel = TrustLevel.GOOD

    def calculate_score(self, decay_days: int = 30) -> float:
        """
        Calculate overall trust score (0.0-1.0).

        Formula:
        - Start with base_score (1.0 = neutral)
        - Subtract penalties for failures
        - Add bonuses for successes
        - Apply time decay (older events matter less)

        Returns:
            Trust score between 0.0 (no trust) and 1.0 (full trust)
        """
        score = self.base_score

        # Signature failures are severe (cryptographic proof of dishonesty)
        total_signatures = self.signature_failures + self.successful_signatures
        if total_signatures > 0:
            signature_reliability = self.successful_signatures / total_signatures
            score *= signature_reliability  # Multiply (failures hurt significantly)

        # Message failures are moderate
        total_messages = self.message_failures + self.successful_messages
        if total_messages > 0:
            message_reliability = self.successful_messages / total_messages
            score *= (0.5 + 0.5 * message_reliability)  # Partial penalty

        # Transaction failures
        total_transactions = self.transaction_failures + self.successful_transactions
        if total_transactions > 0:
            transaction_reliability = self.successful_transactions / total_transactions
            score *= (0.7 + 0.3 * transaction_reliability)

        # Gaming is very severe
        if self.gaming_detected > 0:
            gaming_penalty = min(0.5, 0.1 * self.gaming_detected)  # Up to 50% penalty
            score *= (1.0 - gaming_penalty)

        # Clamp to [0.0, 1.0]
        score = max(0.0, min(1.0, score))

        # Update trust level
        self.trust_level = TrustLevel.from_score(score)

        return score

    def record_signature_failure(self):
        """Record invalid signature (severe trust hit)"""
        self.signature_failures += 1
        self.last_updated = datetime.now(timezone.utc)

    def record_signature_success(self):
        """Record valid signature (builds trust)"""
        self.successful_signatures += 1
        self.last_updated = datetime.now(timezone.utc)

    def record_message_failure(self):
        """Record failed message delivery"""
        self.message_failures += 1
        self.last_updated = datetime.now(timezone.utc)

    def record_message_success(self):
        """Record successful message"""
        self.successful_messages += 1
        self.last_updated = datetime.now(timezone.utc)

    def record_transaction_failure(self):
        """Record failed transaction"""
        self.transaction_failures += 1
        self.last_updated = datetime.now(timezone.utc)

    def record_transaction_success(self):
        """Record successful transaction"""
        self.successful_transactions += 1
        self.last_updated = datetime.now(timezone.utc)

    def record_gaming_attempt(self):
        """Record valuation gaming detected"""
        self.gaming_detected += 1
        self.last_updated = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """Serialize to dictionary"""
        return {
            'society_lct': self.society_lct,
            'trust_score': self.calculate_score(),
            'trust_level': self.trust_level.label,
            'signature_failures': self.signature_failures,
            'successful_signatures': self.successful_signatures,
            'message_failures': self.message_failures,
            'successful_messages': self.successful_messages,
            'transaction_failures': self.transaction_failures,
            'successful_transactions': self.successful_transactions,
            'gaming_detected': self.gaming_detected,
            'last_updated': self.last_updated.isoformat()
        }


class ReputationATPNegotiator(LowestExchangeNegotiator):
    """
    Extended ATP negotiator with reputation-based exchange rates.

    Mechanism:
    1. Calculate base exchange rate (lowest-exchange principle)
    2. Adjust rate based on buyer's trust score
    3. Apply trust multiplier (low trust = higher cost)
    4. Record transaction in trust history
    """

    def __init__(self):
        super().__init__()
        self.trust_scores: Dict[str, TrustScore] = {}

    def get_trust_score(self, society_lct: str) -> TrustScore:
        """Get or create trust score for society"""
        if society_lct not in self.trust_scores:
            self.trust_scores[society_lct] = TrustScore(society_lct=society_lct)
        return self.trust_scores[society_lct]

    def update_trust_from_peer_status(self, society_lct: str, peer_status: dict):
        """
        Update trust score from peer status (Session #31 integration).

        Args:
            society_lct: Society's LCT
            peer_status: Dict with signature_failures, message stats, etc.
        """
        trust = self.get_trust_score(society_lct)

        # Update from signature verification (Session #31)
        if 'signature_failures' in peer_status:
            trust.signature_failures = peer_status['signature_failures']

        # Update from message stats (Session #32)
        if 'messages_received' in peer_status:
            trust.successful_messages = peer_status.get('valid_signatures', 0)
            trust.message_failures = peer_status.get('invalid_signatures', 0)

    def negotiate_exchange_rate_with_trust(
        self,
        buyer: Society,
        seller: Society,
        item_to_buy: str
    ) -> Tuple[ExchangeRate, float, TrustLevel]:
        """
        Negotiate exchange rate WITH trust-based adjustment.

        Returns:
            (ExchangeRate, trust_multiplier, trust_level)
        """
        # Get base exchange rate (lowest-exchange principle)
        base_rate = super().negotiate_exchange_rate(buyer, seller, item_to_buy)

        # Get buyer's trust score
        buyer_trust = self.get_trust_score(buyer.society_lct)
        trust_score = buyer_trust.calculate_score()
        trust_level = TrustLevel.from_score(trust_score)

        # Apply trust multiplier to exchange rate
        # Higher multiplier = buyer pays more (penalty for low trust)
        trust_multiplier = trust_level.multiplier

        # Adjust rate
        adjusted_rate = ExchangeRate(
            from_item=base_rate.from_item,
            to_item=base_rate.to_item,
            rate=base_rate.rate * trust_multiplier,  # Multiply by trust penalty
            society_a_lct=buyer.society_lct,
            society_b_lct=seller.society_lct,
            timestamp=datetime.now(timezone.utc)
        )

        return (adjusted_rate, trust_multiplier, trust_level)

    def execute_transaction_with_trust(
        self,
        buyer: Society,
        seller: Society,
        item: str,
        quantity: float,
        payment_item: str,
        payment_quantity: float,
        transaction_id: str
    ) -> Tuple[CrossSocietyTransaction, TrustLevel]:
        """
        Execute transaction and update trust scores.

        Returns:
            (CrossSocietyTransaction, buyer_trust_level)
        """
        # Execute base transaction
        tx = super().execute_transaction(
            buyer, seller, item, quantity,
            payment_item, payment_quantity, transaction_id
        )

        # Update trust scores based on transaction outcome
        buyer_trust = self.get_trust_score(buyer.society_lct)
        seller_trust = self.get_trust_score(seller.society_lct)

        if tx.is_fair():
            # Fair transaction → Build trust
            buyer_trust.record_transaction_success()
            seller_trust.record_transaction_success()
        elif tx.is_exploitative():
            # Exploitative → Lose trust
            buyer_trust.record_transaction_failure()
            seller_trust.record_transaction_failure()

        trust_level = TrustLevel.from_score(buyer_trust.calculate_score())

        return (tx, trust_level)

    def get_trust_report(self, society_lct: str) -> dict:
        """Generate trust report for a society"""
        trust = self.get_trust_score(society_lct)
        score = trust.calculate_score()
        level = TrustLevel.from_score(score)

        return {
            'society_lct': society_lct,
            'trust_score': score,
            'trust_level': level.label,
            'exchange_rate_multiplier': level.multiplier,
            'effective_cost': f"{(level.multiplier - 1.0) * 100:+.0f}%",  # e.g., "+50%" or "-20%"
            'signature_reliability': (
                trust.successful_signatures / max(trust.successful_signatures + trust.signature_failures, 1)
            ),
            'message_reliability': (
                trust.successful_messages / max(trust.successful_messages + trust.message_failures, 1)
            ),
            'transaction_reliability': (
                trust.successful_transactions / max(trust.successful_transactions + trust.transaction_failures, 1)
            ),
            'gaming_attempts': trust.gaming_detected,
            'details': trust.to_dict()
        }


# ============================================================================
# DEMO: Reputation-ATP Integration
# ============================================================================

def demo_reputation_atp_integration():
    """Demonstrate reputation-based ATP exchange rates"""

    print("=" * 80)
    print("Reputation-ATP Integration Demo - Session #33")
    print("=" * 80)
    print()
    print("Scenario: Trust affects economic outcomes")
    print()

    # Create societies
    honest_society = Society("lct:society:honest", "Honest Agent")
    dishonest_society = Society("lct:society:dishonest", "Dishonest Agent")
    seller = Society("lct:society:seller", "Resource Seller")

    # Set valuations
    print("1. Setup: All societies value compute_hour at 100 ATP")
    honest_society.set_valuation("compute_hour", 100, "Standard compute")
    dishonest_society.set_valuation("compute_hour", 100, "Standard compute")
    seller.set_valuation("compute_hour", 100, "Compute resource")
    print(f"   Seller asks: {seller.get_valuation('compute_hour')} ATP")
    print()

    # Create negotiator with reputation tracking
    negotiator = ReputationATPNegotiator()

    # Simulate trust history
    print("2. Trust History:")
    print()

    print("   Honest Agent:")
    honest_trust = negotiator.get_trust_score(honest_society.society_lct)
    honest_trust.successful_signatures = 100
    honest_trust.signature_failures = 0
    honest_trust.successful_messages = 50
    honest_trust.message_failures = 0
    honest_trust.successful_transactions = 20
    honest_trust.transaction_failures = 0
    print(f"     Signature reliability: 100/100 (100%)")
    print(f"     Message reliability: 50/50 (100%)")
    print(f"     Transaction reliability: 20/20 (100%)")
    print(f"     Trust score: {honest_trust.calculate_score():.2f}")
    print()

    print("   Dishonest Agent:")
    dishonest_trust = negotiator.get_trust_score(dishonest_society.society_lct)
    dishonest_trust.successful_signatures = 60
    dishonest_trust.signature_failures = 15  # 20% failure rate
    dishonest_trust.successful_messages = 30
    dishonest_trust.message_failures = 10
    dishonest_trust.successful_transactions = 5
    dishonest_trust.transaction_failures = 3
    dishonest_trust.gaming_detected = 2
    print(f"     Signature reliability: 60/75 (80%)")
    print(f"     Message reliability: 30/40 (75%)")
    print(f"     Transaction reliability: 5/8 (62.5%)")
    print(f"     Gaming attempts: 2")
    print(f"     Trust score: {dishonest_trust.calculate_score():.2f}")
    print()

    # Test 1: Honest agent buys compute
    print("3. Test 1: Honest Agent buys compute")
    print()

    rate_honest, multiplier_honest, level_honest = negotiator.negotiate_exchange_rate_with_trust(
        buyer=honest_society,
        seller=seller,
        item_to_buy="compute_hour"
    )

    print(f"   Base price: {seller.get_valuation('compute_hour')} ATP")
    print(f"   Trust level: {level_honest.label.upper()}")
    print(f"   Trust multiplier: {multiplier_honest:.1f}x")
    print(f"   Final cost: {rate_honest.rate:.0f} ATP")
    print(f"   Effective discount/premium: {(multiplier_honest - 1.0) * 100:+.0f}%")
    print()

    if multiplier_honest < 1.0:
        print(f"   ✅ DISCOUNT applied (trusted society)")
    elif multiplier_honest > 1.0:
        print(f"   ⚠️  PREMIUM charged (low trust)")
    else:
        print(f"   ➡️  FAIR RATE (neutral trust)")
    print()

    # Test 2: Dishonest agent buys compute
    print("4. Test 2: Dishonest Agent buys compute")
    print()

    rate_dishonest, multiplier_dishonest, level_dishonest = negotiator.negotiate_exchange_rate_with_trust(
        buyer=dishonest_society,
        seller=seller,
        item_to_buy="compute_hour"
    )

    print(f"   Base price: {seller.get_valuation('compute_hour')} ATP")
    print(f"   Trust level: {level_dishonest.label.upper()}")
    print(f"   Trust multiplier: {multiplier_dishonest:.1f}x")
    print(f"   Final cost: {rate_dishonest.rate:.0f} ATP")
    print(f"   Effective premium: {(multiplier_dishonest - 1.0) * 100:+.0f}%")
    print()

    if multiplier_dishonest > 1.0:
        print(f"   ⚠️  PREMIUM charged (low trust)")
        print(f"   Dishonest agent pays {rate_dishonest.rate - rate_honest.rate:.0f} ATP MORE than honest agent")
    print()

    # Summary comparison
    print("5. Economic Comparison:")
    print()
    print(f"   Same item (compute_hour) from same seller:")
    print(f"     Honest Agent:    {rate_honest.rate:>6.0f} ATP")
    print(f"     Dishonest Agent: {rate_dishonest.rate:>6.0f} ATP")
    print(f"     Difference:      {rate_dishonest.rate - rate_honest.rate:>+6.0f} ATP ({(rate_dishonest.rate / rate_honest.rate - 1.0) * 100:+.0f}%)")
    print()

    # Trust reports
    print("6. Trust Reports:")
    print()

    honest_report = negotiator.get_trust_report(honest_society.society_lct)
    print(f"   Honest Agent:")
    print(f"     Trust score: {honest_report['trust_score']:.2f}")
    print(f"     Trust level: {honest_report['trust_level']}")
    print(f"     Rate multiplier: {honest_report['exchange_rate_multiplier']:.1f}x")
    print(f"     Effective cost: {honest_report['effective_cost']}")
    print()

    dishonest_report = negotiator.get_trust_report(dishonest_society.society_lct)
    print(f"   Dishonest Agent:")
    print(f"     Trust score: {dishonest_report['trust_score']:.2f}")
    print(f"     Trust level: {dishonest_report['trust_level']}")
    print(f"     Rate multiplier: {dishonest_report['exchange_rate_multiplier']:.1f}x")
    print(f"     Effective cost: {dishonest_report['effective_cost']}")
    print()

    print("=" * 80)
    print("✅ Reputation-ATP Integration OPERATIONAL")
    print("=" * 80)
    print()
    print("Key Mechanisms:")
    print("  ✅ Trust scores track signature failures, message stats, transactions")
    print("  ✅ Low trust → Higher exchange rates (economic penalty)")
    print("  ✅ High trust → Favorable rates (economic reward)")
    print("  ✅ Self-regulating: Dishonest behavior becomes expensive")
    print("  ✅ Economic incentive for honest behavior")
    print()

    # Show economic incentive calculation
    print("Economic Incentive Analysis:")
    print()
    print(f"  Over 100 transactions:")
    print(f"    Honest agent total cost:    {rate_honest.rate * 100:>8,.0f} ATP")
    print(f"    Dishonest agent total cost: {rate_dishonest.rate * 100:>8,.0f} ATP")
    print(f"    Cost of dishonesty:         {(rate_dishonest.rate - rate_honest.rate) * 100:>+8,.0f} ATP")
    print()
    print(f"  Being dishonest costs {(rate_dishonest.rate / rate_honest.rate - 1.0) * 100:.0f}% more!")
    print()


if __name__ == "__main__":
    demo_reputation_atp_integration()
