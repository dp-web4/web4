#!/usr/bin/env python3
"""
ATP Lowest-Exchange Principle Implementation
=============================================

Implements the economic forcing function for cross-society transactions:
societies MUST accept items as payment at their stated internal valuations,
preventing valuation gaming.

Key Concepts:
- Internal Autonomy: Each society sets its own ATP values
- Adversarial Exchange: Negotiation between societies is self-interested
- Forcing Function: Must accept items at stated prices (consistency enforced)
- Audit Trail: Misalignments are recorded and penalize trust

Created: Session #29 (2025-11-14)
Related: WAL (Session #27), Reputation (Sessions #24-27), BEC Prevention
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from enum import Enum

# Import reputation system
sys.path.insert(0, str(Path(__file__).parent.parent / "reputation"))
from reputation_tracker import ReputationTracker, BehaviorType


class TransactionType(str, Enum):
    """Types of cross-society transactions"""
    GOODS_FOR_ATP = "goods_for_atp"
    GOODS_FOR_GOODS = "goods_for_goods"
    SERVICES_FOR_ATP = "services_for_atp"
    MIXED = "mixed"


@dataclass
class InternalValuation:
    """Internal valuation of an item by a society"""
    item_id: str
    atp_value: float  # ATP price for this item
    timestamp: datetime
    society_lct: str
    description: str = ""

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class ExchangeRate:
    """Exchange rate between two items/societies"""
    from_item: str
    to_item: str
    rate: float  # Units of to_item per unit of from_item
    society_a_lct: str
    society_b_lct: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class CrossSocietyTransaction:
    """
    Record of transaction between societies.

    Includes multi-perspective validation (V³ pattern):
    - Valuation (buyer): Was it fair from buyer's perspective?
    - Valuation (seller): Was it fair from seller's perspective?
    - Validity: Did the transaction actually occur?
    - Veracity (external): External auditor assessment of fairness
    """
    transaction_id: str
    item_exchanged: str
    quantity: float
    atp_paid: float
    buyer_society_lct: str
    seller_society_lct: str
    timestamp: datetime

    # Multi-perspective validation
    valuation_buyer: float      # 0.0-1.0: Buyer satisfaction
    valuation_seller: float     # 0.0-1.0: Seller satisfaction
    validity: float             # 0.0-1.0: Transaction occurred
    veracity_external: float    # 0.0-1.0: External fairness assessment

    # Metadata
    exchange_rate_used: Optional[float] = None
    lowest_exchange_applied: bool = False
    payment_method: str = "ATP"
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

    def is_fair(self, threshold: float = 0.5) -> bool:
        """Check if transaction is considered fair by all parties"""
        return (
            self.valuation_buyer >= threshold and
            self.valuation_seller >= threshold and
            self.veracity_external >= threshold
        )

    def is_exploitative(self, veracity_threshold: float = 0.1) -> bool:
        """Detect exploitative transactions (low external veracity)"""
        return self.veracity_external < veracity_threshold


class Society:
    """
    A Web4 society with internal ATP valuations.

    Each society:
    - Maintains internal price list (item → ATP value)
    - Records transaction history
    - Must accept items at stated prices (forcing function)
    """

    def __init__(self, society_lct: str, name: str = ""):
        self.society_lct = society_lct
        self.name = name or society_lct
        self.internal_valuations: Dict[str, InternalValuation] = {}
        self.transaction_history: List[CrossSocietyTransaction] = []

    def set_valuation(self, item_id: str, atp_value: float, description: str = ""):
        """Set internal valuation for an item"""
        self.internal_valuations[item_id] = InternalValuation(
            item_id=item_id,
            atp_value=atp_value,
            timestamp=datetime.now(timezone.utc),
            society_lct=self.society_lct,
            description=description
        )

    def get_valuation(self, item_id: str) -> Optional[float]:
        """Get ATP valuation for an item"""
        valuation = self.internal_valuations.get(item_id)
        return valuation.atp_value if valuation else None

    def record_transaction(self, transaction: CrossSocietyTransaction):
        """Record a transaction in history"""
        self.transaction_history.append(transaction)

    def accepts_item_as_payment(self, item_id: str) -> bool:
        """Check if society has accepted this item as payment before"""
        for tx in self.transaction_history:
            if tx.payment_method == item_id and tx.seller_society_lct == self.society_lct:
                return True
        return False


class LowestExchangeNegotiator:
    """
    Implements adversarial exchange rate negotiation with forcing function.

    Key mechanism: Payer chooses lowest-cost payment option,
    but receiver MUST accept items at their stated internal valuations.
    """

    def __init__(self):
        self.exchange_rates: Dict[Tuple[str, str, str, str], ExchangeRate] = {}

    def negotiate_exchange_rate(
        self,
        buyer: Society,
        seller: Society,
        item_to_buy: str
    ) -> ExchangeRate:
        """
        Adversarial negotiation with lowest-exchange forcing function.

        Buyer perspective: Pay minimum cost
        Seller perspective: Must accept per stated valuations (forcing function)

        Args:
            buyer: Buying society
            seller: Selling society
            item_to_buy: Item buyer wants to purchase

        Returns:
            ExchangeRate for the transaction
        """
        # Seller's asking price
        seller_valuation = seller.get_valuation(item_to_buy)
        if seller_valuation is None:
            raise ValueError(f"{seller.name} has no valuation for {item_to_buy}")

        # Buyer finds lowest-cost payment option
        payment_options = []

        # Option 1: Pay in ATP
        # (payment_item, quantity_needed, cost_to_buyer)
        payment_options.append(("ATP", seller_valuation, seller_valuation))

        # Option 2: Pay in items buyer has that seller values
        for item_id, valuation in buyer.internal_valuations.items():
            seller_item_value = seller.get_valuation(item_id)
            if seller_item_value and seller_item_value > 0:
                # How many units of buyer's item = seller's asking price?
                quantity_needed = seller_valuation / seller_item_value
                # Cost to buyer in ATP
                cost_to_buyer = quantity_needed * valuation.atp_value

                payment_options.append((item_id, quantity_needed, cost_to_buyer))

        # Buyer chooses cheapest option
        best_option = min(payment_options, key=lambda x: x[2])
        payment_item, quantity, cost = best_option

        # Create exchange rate
        rate = ExchangeRate(
            from_item=payment_item,
            to_item=item_to_buy,
            rate=quantity,  # Units of payment_item per unit of item_to_buy
            society_a_lct=buyer.society_lct,
            society_b_lct=seller.society_lct
        )

        # Store for future reference
        key = (buyer.society_lct, seller.society_lct, payment_item, item_to_buy)
        self.exchange_rates[key] = rate

        return rate

    def execute_transaction(
        self,
        buyer: Society,
        seller: Society,
        item: str,
        quantity: float,
        payment_item: str,
        payment_quantity: float,
        transaction_id: str
    ) -> CrossSocietyTransaction:
        """
        Execute cross-society transaction with multi-perspective validation.

        Args:
            buyer: Buying society
            seller: Selling society
            item: Item being purchased
            quantity: Quantity of item
            payment_item: Item used for payment
            payment_quantity: Quantity of payment item
            transaction_id: Unique transaction ID

        Returns:
            CrossSocietyTransaction record
        """
        # Calculate ATP equivalents
        seller_item_value = seller.get_valuation(item)
        seller_payment_value = seller.get_valuation(payment_item) if payment_item != "ATP" else 1.0

        buyer_item_value = buyer.get_valuation(item) or seller_item_value
        buyer_payment_value = buyer.get_valuation(payment_item) if payment_item != "ATP" else 1.0

        # ATP paid (from buyer's perspective)
        atp_paid = payment_quantity * (buyer_payment_value or 1.0)

        # Valuation scores (0.0-1.0)
        # Buyer: Did I get good value?
        expected_cost = quantity * (buyer_item_value or seller_item_value)
        valuation_buyer = min(1.0, expected_cost / (atp_paid + 1e-10))

        # Seller: Did I get fair payment?
        expected_payment = quantity * seller_item_value
        received_payment = payment_quantity * (seller_payment_value or 1.0)
        valuation_seller = min(1.0, received_payment / (expected_payment + 1e-10))

        # External veracity: Geometric mean (fair if both parties satisfied)
        veracity = (valuation_buyer * valuation_seller) ** 0.5

        # Create transaction record
        transaction = CrossSocietyTransaction(
            transaction_id=transaction_id,
            item_exchanged=item,
            quantity=quantity,
            atp_paid=atp_paid,
            buyer_society_lct=buyer.society_lct,
            seller_society_lct=seller.society_lct,
            timestamp=datetime.now(timezone.utc),
            valuation_buyer=valuation_buyer,
            valuation_seller=valuation_seller,
            validity=1.0,  # Transaction occurred
            veracity_external=veracity,
            exchange_rate_used=payment_quantity / quantity if quantity > 0 else 0,
            lowest_exchange_applied=True,
            payment_method=payment_item
        )

        # Record in both societies
        buyer.record_transaction(transaction)
        seller.record_transaction(transaction)

        return transaction


class ValueMisalignmentDetector:
    """
    Detects societies gaming their internal valuations.

    Mechanism: If society values item X highly internally but refuses
    to accept X as payment externally, they are gaming the system.
    """

    def __init__(self, reputation_tracker: Optional[ReputationTracker] = None):
        self.reputation_tracker = reputation_tracker or ReputationTracker()

    def audit_society(
        self,
        society: Society,
        high_value_threshold: float = 1000.0,
        organization: str = "default"
    ) -> Dict:
        """
        Audit society for valuation gaming.

        Args:
            society: Society to audit
            high_value_threshold: ATP threshold for "high value" items
            organization: Organization context for reputation

        Returns:
            Audit report with misalignments and trust adjustment
        """
        misalignments = []

        for item_id, valuation in society.internal_valuations.items():
            if valuation.atp_value < high_value_threshold:
                continue  # Only audit high-value claims

            # Check if society accepts this item as payment
            accepted_as_payment = society.accepts_item_as_payment(item_id)

            if not accepted_as_payment:
                # Gaming detected: Claims high value but won't accept as payment
                misalignments.append({
                    'item': item_id,
                    'stated_value': valuation.atp_value,
                    'accepted_externally': False,
                    'veracity': 0.001,  # Extremely low
                    'description': f"Claims {item_id} worth {valuation.atp_value} ATP but won't accept as payment"
                })

        # Calculate consistency score
        total_high_value_items = sum(
            1 for v in society.internal_valuations.values()
            if v.atp_value >= high_value_threshold
        )

        consistency_score = 1.0 - (len(misalignments) / max(total_high_value_items, 1))

        # Reputation penalty for gaming
        if len(misalignments) > 0:
            self.reputation_tracker.record_event(
                agent_lct=society.society_lct,
                behavior_type=BehaviorType.FALSE_WITNESS,  # Gaming = lying
                organization=organization,
                description=f"Valuation gaming detected: {len(misalignments)} misalignments",
                metadata={
                    'misalignments': len(misalignments),
                    'consistency_score': consistency_score
                }
            )

        return {
            'society_lct': society.society_lct,
            'society_name': society.name,
            'consistency_score': consistency_score,
            'gaming_detected': len(misalignments) > 0,
            'misalignments': misalignments,
            'trust_adjustment': -0.1 * len(misalignments),
            'high_value_items_audited': total_high_value_items
        }


# Example usage / Demo
if __name__ == "__main__":
    print("=" * 80)
    print("ATP Lowest-Exchange Principle - Demo")
    print("=" * 80)
    print()

    # Create societies
    art_society = Society("lct:society:art", "Art Society")
    engineering_society = Society("lct:society:engineering", "Engineering Society")

    print("Scenario: The $1M Banana\n")

    # Setup 1: Art Society values banana at 1M ATP
    print("1. Art Society sets internal valuations:")
    art_society.set_valuation("banana", 1_000_000, "Conceptual art piece")
    art_society.set_valuation("sculpture", 500_000, "Bronze sculpture")
    print(f"   Banana: {art_society.get_valuation('banana'):,.0f} ATP")
    print(f"   Sculpture: {art_society.get_valuation('sculpture'):,.0f} ATP")
    print()

    # Setup 2: Engineering Society values banana at 1 ATP
    print("2. Engineering Society sets internal valuations:")
    engineering_society.set_valuation("banana", 1, "Food item")
    engineering_society.set_valuation("blueprint", 10_000, "Engineering design")
    print(f"   Banana: {engineering_society.get_valuation('banana'):,.0f} ATP")
    print(f"   Blueprint: {engineering_society.get_valuation('blueprint'):,.0f} ATP")
    print()

    # Transaction 1: Engineer buys sculpture from Art Society
    print("3. Engineer wants to buy sculpture from Art Society:")
    print(f"   Art Society asking price: {art_society.get_valuation('sculpture'):,.0f} ATP")
    print()

    negotiator = LowestExchangeNegotiator()
    rate = negotiator.negotiate_exchange_rate(
        engineering_society,
        art_society,
        "sculpture"
    )

    print(f"   Exchange rate negotiated:")
    print(f"     Payment: {rate.from_item}")
    print(f"     Rate: {rate.rate:.2f} {rate.from_item} per {rate.to_item}")
    print()

    # Execute with lowest-exchange: Pay in bananas!
    print("4. Engineer uses lowest-exchange principle:")
    print(f"   Art Society values banana at 1M ATP")
    print(f"   Sculpture costs 500K ATP")
    print(f"   → Engineer can pay with 0.5 bananas!")
    print()

    tx = negotiator.execute_transaction(
        buyer=engineering_society,
        seller=art_society,
        item="sculpture",
        quantity=1.0,
        payment_item="banana",
        payment_quantity=0.5,
        transaction_id="tx:001"
    )

    print(f"   Transaction executed:")
    print(f"     Paid: {tx.atp_paid:.0f} ATP (from engineer's perspective)")
    print(f"     Buyer satisfaction: {tx.valuation_buyer:.2f}")
    print(f"     Seller satisfaction: {tx.valuation_seller:.2f}")
    print(f"     External veracity: {tx.veracity_external:.2f}")
    print()

    if tx.is_fair():
        print("   ✅ Transaction considered FAIR by all parties")
    elif tx.is_exploitative():
        print("   ⚠️  Transaction flagged as EXPLOITATIVE")
    print()

    # Audit Art Society
    print("5. External auditor checks Art Society:")
    detector = ValueMisalignmentDetector()
    audit = detector.audit_society(art_society, high_value_threshold=100_000)

    print(f"   Consistency score: {audit['consistency_score']:.2f}")
    print(f"   Gaming detected: {audit['gaming_detected']}")

    if audit['gaming_detected']:
        print(f"   ⚠️  MISALIGNMENTS FOUND:")
        for m in audit['misalignments']:
            print(f"      - {m['item']}: Claims {m['stated_value']:,.0f} ATP")
            print(f"        but doesn't accept as payment!")
            print(f"        Veracity: {m['veracity']}")
    print()

    # Forcing function demonstration
    print("6. Forcing Function in Action:")
    print("   Art Society MUST now either:")
    print("   a) Accept bananas as payment for ALL goods (consistent)")
    print("   b) Lower banana valuation internally (honest)")
    print("   c) Lose external trust (penalized for gaming)")
    print()

    print("=" * 80)
    print("ATP Lowest-Exchange: OPERATIONAL")
    print("=" * 80)
    print()
    print("Key Mechanisms:")
    print("  ✅ Internal autonomy (each society sets prices)")
    print("  ✅ Adversarial exchange (buyer minimizes cost)")
    print("  ✅ Forcing function (must accept at stated prices)")
    print("  ✅ Audit trail (gaming detected and penalized)")
    print("  ✅ Multi-perspective validation (V³: buyer/seller/external)")
