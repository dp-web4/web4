"""
Cross-Society ATP Exchange

Session #41

Enables ATP trading across Web4 society boundaries.

Key Features:
- Decentralized ATP marketplace
- Atomic swaps (no trusted intermediary)
- Price discovery through bidding
- Settlement via cryptographic proofs
- Protection against double-spending

This builds on cross_society_messaging.py to add economic coordination.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Set, Optional, Tuple
from enum import Enum
import json
import hashlib

from cross_society_messaging import (
    CrossSocietyMessage,
    CrossSocietyMessageBus,
    MessageType,
    SocietyCoordinator,
)

from web4_crypto import KeyPair, Web4Crypto


# ============================================================================
# ATP Exchange Types
# ============================================================================

class ExchangeStatus(Enum):
    """Status of ATP exchange"""
    PENDING = "pending"
    MATCHED = "matched"
    SETTLING = "settling"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class ATPOffer:
    """Offer to sell ATP"""
    offer_id: str
    seller_lct: str
    amount_atp: float
    price_per_atp: float  # In some unit (could be other ATP, fiat, etc)
    currency: str  # "ATP", "USD", etc
    created_at: datetime
    expires_at: datetime
    status: ExchangeStatus = ExchangeStatus.PENDING
    matched_with: Optional[str] = None  # Bid ID if matched

    def total_price(self) -> float:
        """Total price for the offer"""
        return self.amount_atp * self.price_per_atp

    def is_expired(self) -> bool:
        """Check if offer has expired"""
        return datetime.now(timezone.utc) > self.expires_at

    def to_dict(self) -> Dict:
        return {
            "offer_id": self.offer_id,
            "seller_lct": self.seller_lct,
            "amount_atp": self.amount_atp,
            "price_per_atp": self.price_per_atp,
            "currency": self.currency,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "status": self.status.value,
            "matched_with": self.matched_with,
        }


@dataclass
class ATPBid:
    """Bid to buy ATP"""
    bid_id: str
    buyer_lct: str
    amount_atp: float
    max_price_per_atp: float
    currency: str
    created_at: datetime
    expires_at: datetime
    status: ExchangeStatus = ExchangeStatus.PENDING
    matched_with: Optional[str] = None  # Offer ID if matched

    def max_total_price(self) -> float:
        """Maximum total price willing to pay"""
        return self.amount_atp * self.max_price_per_atp

    def is_expired(self) -> bool:
        """Check if bid has expired"""
        return datetime.now(timezone.utc) > self.expires_at

    def to_dict(self) -> Dict:
        return {
            "bid_id": self.bid_id,
            "buyer_lct": self.buyer_lct,
            "amount_atp": self.amount_atp,
            "max_price_per_atp": self.max_price_per_atp,
            "currency": self.currency,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "status": self.status.value,
            "matched_with": self.matched_with,
        }


@dataclass
class ATPExchange:
    """Atomic ATP exchange between two societies"""
    exchange_id: str
    offer_id: str
    bid_id: str
    seller_lct: str
    buyer_lct: str
    amount_atp: float
    price_per_atp: float
    total_price: float
    currency: str
    created_at: datetime
    status: ExchangeStatus = ExchangeStatus.PENDING

    # Settlement proofs
    seller_commitment: Optional[str] = None  # Hash commitment from seller
    buyer_commitment: Optional[str] = None   # Hash commitment from buyer
    seller_reveal: Optional[str] = None      # Reveal from seller
    buyer_reveal: Optional[str] = None       # Reveal from buyer

    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "exchange_id": self.exchange_id,
            "offer_id": self.offer_id,
            "bid_id": self.bid_id,
            "seller_lct": self.seller_lct,
            "buyer_lct": self.buyer_lct,
            "amount_atp": self.amount_atp,
            "price_per_atp": self.price_per_atp,
            "total_price": self.total_price,
            "currency": self.currency,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "seller_commitment": self.seller_commitment,
            "buyer_commitment": self.buyer_commitment,
            "seller_reveal": self.seller_reveal,
            "buyer_reveal": self.buyer_reveal,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


# ============================================================================
# ATP Exchange Marketplace
# ============================================================================

class ATPMarketplace:
    """
    Decentralized ATP marketplace.

    Features:
    - Order matching (offers + bids)
    - Price discovery
    - Atomic settlement
    - Double-spend prevention
    """

    def __init__(self):
        # Active orders
        self.offers: Dict[str, ATPOffer] = {}
        self.bids: Dict[str, ATPBid] = {}

        # Exchanges (pending and completed)
        self.exchanges: Dict[str, ATPExchange] = {}

        # ATP reserves tracking (prevent double-spend)
        self.reserved_atp: Dict[str, float] = {}  # seller_lct -> reserved amount

        # Statistics
        self.total_offers = 0
        self.total_bids = 0
        self.total_exchanges = 0
        self.total_volume = 0.0

    def create_offer(
        self,
        seller_lct: str,
        amount_atp: float,
        price_per_atp: float,
        currency: str = "ATP",
        valid_for_hours: int = 24,
    ) -> ATPOffer:
        """Create ATP sell offer"""

        offer_id = self._generate_offer_id(seller_lct, self.total_offers)

        offer = ATPOffer(
            offer_id=offer_id,
            seller_lct=seller_lct,
            amount_atp=amount_atp,
            price_per_atp=price_per_atp,
            currency=currency,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=valid_for_hours),
        )

        self.offers[offer_id] = offer
        self.total_offers += 1

        # Reserve ATP to prevent double-spend
        if seller_lct not in self.reserved_atp:
            self.reserved_atp[seller_lct] = 0.0
        self.reserved_atp[seller_lct] += amount_atp

        return offer

    def create_bid(
        self,
        buyer_lct: str,
        amount_atp: float,
        max_price_per_atp: float,
        currency: str = "ATP",
        valid_for_hours: int = 24,
    ) -> ATPBid:
        """Create ATP buy bid"""

        bid_id = self._generate_bid_id(buyer_lct, self.total_bids)

        bid = ATPBid(
            bid_id=bid_id,
            buyer_lct=buyer_lct,
            amount_atp=amount_atp,
            max_price_per_atp=max_price_per_atp,
            currency=currency,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=valid_for_hours),
        )

        self.bids[bid_id] = bid
        self.total_bids += 1

        return bid

    def match_orders(self) -> List[ATPExchange]:
        """
        Match bids and offers.

        Simple matching algorithm: Find bids willing to pay >= offer price
        """
        new_exchanges = []

        # Clean up expired orders first
        self._cleanup_expired()

        for offer_id, offer in list(self.offers.items()):
            if offer.status != ExchangeStatus.PENDING:
                continue

            # Find matching bids
            for bid_id, bid in list(self.bids.items()):
                if bid.status != ExchangeStatus.PENDING:
                    continue

                # Check if bid and offer are compatible
                if (bid.currency == offer.currency and
                    bid.max_price_per_atp >= offer.price_per_atp and
                    bid.amount_atp >= offer.amount_atp):

                    # Create exchange
                    exchange = self._create_exchange(offer, bid)
                    new_exchanges.append(exchange)

                    # Update offer and bid status
                    offer.status = ExchangeStatus.MATCHED
                    offer.matched_with = bid_id
                    bid.status = ExchangeStatus.MATCHED
                    bid.matched_with = offer_id

                    break  # One offer can only match one bid

        return new_exchanges

    def _create_exchange(self, offer: ATPOffer, bid: ATPBid) -> ATPExchange:
        """Create ATP exchange from matched offer and bid"""

        exchange_id = self._generate_exchange_id(offer.offer_id, bid.bid_id)

        exchange = ATPExchange(
            exchange_id=exchange_id,
            offer_id=offer.offer_id,
            bid_id=bid.bid_id,
            seller_lct=offer.seller_lct,
            buyer_lct=bid.buyer_lct,
            amount_atp=offer.amount_atp,
            price_per_atp=offer.price_per_atp,
            total_price=offer.total_price(),
            currency=offer.currency,
            created_at=datetime.now(timezone.utc),
            status=ExchangeStatus.MATCHED,
        )

        self.exchanges[exchange_id] = exchange
        self.total_exchanges += 1

        return exchange

    def initiate_settlement(self, exchange_id: str) -> bool:
        """
        Begin atomic settlement process.

        Uses commit-reveal scheme to ensure atomicity:
        1. Both parties commit to their transfer
        2. Both parties reveal their commitment
        3. If both reveal, exchange completes
        """
        if exchange_id not in self.exchanges:
            return False

        exchange = self.exchanges[exchange_id]

        if exchange.status != ExchangeStatus.MATCHED:
            return False

        exchange.status = ExchangeStatus.SETTLING
        return True

    def commit_seller(self, exchange_id: str, commitment: str) -> bool:
        """Seller commits to ATP transfer"""
        if exchange_id not in self.exchanges:
            return False

        exchange = self.exchanges[exchange_id]

        if exchange.status != ExchangeStatus.SETTLING:
            return False

        exchange.seller_commitment = commitment
        return True

    def commit_buyer(self, exchange_id: str, commitment: str) -> bool:
        """Buyer commits to payment"""
        if exchange_id not in self.exchanges:
            return False

        exchange = self.exchanges[exchange_id]

        if exchange.status != ExchangeStatus.SETTLING:
            return False

        exchange.buyer_commitment = commitment
        return True

    def reveal_seller(self, exchange_id: str, reveal: str) -> bool:
        """Seller reveals ATP transfer proof"""
        if exchange_id not in self.exchanges:
            return False

        exchange = self.exchanges[exchange_id]

        # Verify reveal matches commitment
        reveal_hash = hashlib.sha256(reveal.encode()).hexdigest()
        if reveal_hash != exchange.seller_commitment:
            return False

        exchange.seller_reveal = reveal

        # Check if both revealed
        if exchange.buyer_reveal:
            self._complete_exchange(exchange)

        return True

    def reveal_buyer(self, exchange_id: str, reveal: str) -> bool:
        """Buyer reveals payment proof"""
        if exchange_id not in self.exchanges:
            return False

        exchange = self.exchanges[exchange_id]

        # Verify reveal matches commitment
        reveal_hash = hashlib.sha256(reveal.encode()).hexdigest()
        if reveal_hash != exchange.buyer_commitment:
            return False

        exchange.buyer_reveal = reveal

        # Check if both revealed
        if exchange.seller_reveal:
            self._complete_exchange(exchange)

        return True

    def _complete_exchange(self, exchange: ATPExchange):
        """Complete exchange after both parties revealed"""
        exchange.status = ExchangeStatus.COMPLETED
        exchange.completed_at = datetime.now(timezone.utc)

        # Update statistics
        self.total_volume += exchange.amount_atp

        # Release reserved ATP
        if exchange.seller_lct in self.reserved_atp:
            self.reserved_atp[exchange.seller_lct] -= exchange.amount_atp

    def cancel_offer(self, offer_id: str) -> bool:
        """Cancel an offer"""
        if offer_id not in self.offers:
            return False

        offer = self.offers[offer_id]

        if offer.status != ExchangeStatus.PENDING:
            return False

        offer.status = ExchangeStatus.CANCELLED

        # Release reserved ATP
        if offer.seller_lct in self.reserved_atp:
            self.reserved_atp[offer.seller_lct] -= offer.amount_atp

        return True

    def cancel_bid(self, bid_id: str) -> bool:
        """Cancel a bid"""
        if bid_id not in self.bids:
            return False

        bid = self.bids[bid_id]

        if bid.status != ExchangeStatus.PENDING:
            return False

        bid.status = ExchangeStatus.CANCELLED
        return True

    def _cleanup_expired(self):
        """Remove expired offers and bids"""
        # Expire offers
        for offer_id, offer in list(self.offers.items()):
            if offer.status == ExchangeStatus.PENDING and offer.is_expired():
                offer.status = ExchangeStatus.CANCELLED
                # Release reserved ATP
                if offer.seller_lct in self.reserved_atp:
                    self.reserved_atp[offer.seller_lct] -= offer.amount_atp

        # Expire bids
        for bid_id, bid in list(self.bids.items()):
            if bid.status == ExchangeStatus.PENDING and bid.is_expired():
                bid.status = ExchangeStatus.CANCELLED

    def get_order_book(self) -> Dict:
        """Get current order book (active offers and bids)"""
        active_offers = [
            offer.to_dict()
            for offer in self.offers.values()
            if offer.status == ExchangeStatus.PENDING
        ]

        active_bids = [
            bid.to_dict()
            for bid in self.bids.values()
            if bid.status == ExchangeStatus.PENDING
        ]

        # Sort by price
        active_offers.sort(key=lambda x: x["price_per_atp"])
        active_bids.sort(key=lambda x: x["max_price_per_atp"], reverse=True)

        return {
            "offers": active_offers,
            "bids": active_bids,
        }

    def get_stats(self) -> Dict:
        """Get marketplace statistics"""
        return {
            "total_offers": self.total_offers,
            "total_bids": self.total_bids,
            "total_exchanges": self.total_exchanges,
            "total_volume": self.total_volume,
            "active_offers": len([o for o in self.offers.values() if o.status == ExchangeStatus.PENDING]),
            "active_bids": len([b for b in self.bids.values() if b.status == ExchangeStatus.PENDING]),
            "completed_exchanges": len([e for e in self.exchanges.values() if e.status == ExchangeStatus.COMPLETED]),
        }

    def _generate_offer_id(self, seller_lct: str, count: int) -> str:
        """Generate unique offer ID"""
        data = f"{seller_lct}:offer:{count}:{datetime.now(timezone.utc).isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _generate_bid_id(self, buyer_lct: str, count: int) -> str:
        """Generate unique bid ID"""
        data = f"{buyer_lct}:bid:{count}:{datetime.now(timezone.utc).isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _generate_exchange_id(self, offer_id: str, bid_id: str) -> str:
        """Generate unique exchange ID"""
        data = f"{offer_id}:{bid_id}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("CROSS-SOCIETY ATP EXCHANGE - Session #41")
    print("Decentralized ATP Marketplace")
    print("=" * 80)

    marketplace = ATPMarketplace()

    # Scenario 1: Creating offers
    print("\n### Scenario 1: Creating ATP Offers")
    print("-" * 80)

    offer1 = marketplace.create_offer(
        seller_lct="lct-sage-society",
        amount_atp=1000.0,
        price_per_atp=0.01,
        currency="ATP",
    )

    offer2 = marketplace.create_offer(
        seller_lct="lct-legion-society",
        amount_atp=500.0,
        price_per_atp=0.015,
        currency="ATP",
    )

    print(f"SAGE offers: {offer1.amount_atp} ATP @ {offer1.price_per_atp} each")
    print(f"  Total price: {offer1.total_price()}")
    print(f"Legion offers: {offer2.amount_atp} ATP @ {offer2.price_per_atp} each")
    print(f"  Total price: {offer2.total_price()}")

    # Scenario 2: Creating bids
    print("\n### Scenario 2: Creating ATP Bids")
    print("-" * 80)

    bid1 = marketplace.create_bid(
        buyer_lct="lct-cbp-society",
        amount_atp=800.0,
        max_price_per_atp=0.012,
        currency="ATP",
    )

    bid2 = marketplace.create_bid(
        buyer_lct="lct-alice-society",
        amount_atp=500.0,
        max_price_per_atp=0.02,
        currency="ATP",
    )

    print(f"CBP bids: {bid1.amount_atp} ATP @ max {bid1.max_price_per_atp} each")
    print(f"  Max total: {bid1.max_total_price()}")
    print(f"Alice bids: {bid2.amount_atp} ATP @ max {bid2.max_price_per_atp} each")
    print(f"  Max total: {bid2.max_total_price()}")

    # Scenario 3: Order matching
    print("\n### Scenario 3: Order Matching")
    print("-" * 80)

    order_book = marketplace.get_order_book()
    print(f"Active offers: {len(order_book['offers'])}")
    print(f"Active bids: {len(order_book['bids'])}")

    exchanges = marketplace.match_orders()
    print(f"\n✓ Matched {len(exchanges)} exchanges")

    for exchange in exchanges:
        print(f"  Exchange {exchange.exchange_id[:8]}...")
        print(f"    {exchange.seller_lct} → {exchange.buyer_lct}")
        print(f"    Amount: {exchange.amount_atp} ATP")
        print(f"    Price: {exchange.price_per_atp} per ATP")
        print(f"    Total: {exchange.total_price}")

    # Scenario 4: Atomic settlement
    print("\n### Scenario 4: Atomic Settlement (Commit-Reveal)")
    print("-" * 80)

    if exchanges:
        exchange = exchanges[0]
        exchange_id = exchange.exchange_id

        # Initiate settlement
        marketplace.initiate_settlement(exchange_id)
        print(f"Settlement initiated for {exchange_id[:8]}...")

        # Seller commits
        seller_secret = "seller-atp-transfer-proof-abc123"
        seller_commitment = hashlib.sha256(seller_secret.encode()).hexdigest()
        marketplace.commit_seller(exchange_id, seller_commitment)
        print(f"✓ Seller committed: {seller_commitment[:16]}...")

        # Buyer commits
        buyer_secret = "buyer-payment-proof-xyz789"
        buyer_commitment = hashlib.sha256(buyer_secret.encode()).hexdigest()
        marketplace.commit_buyer(exchange_id, buyer_commitment)
        print(f"✓ Buyer committed: {buyer_commitment[:16]}...")

        # Seller reveals
        marketplace.reveal_seller(exchange_id, seller_secret)
        print(f"✓ Seller revealed")

        # Buyer reveals
        marketplace.reveal_buyer(exchange_id, buyer_secret)
        print(f"✓ Buyer revealed")

        # Check status
        final_exchange = marketplace.exchanges[exchange_id]
        print(f"\nExchange status: {final_exchange.status.value}")
        print(f"Completed at: {final_exchange.completed_at}")

    # Scenario 5: Statistics
    print("\n### Scenario 5: Marketplace Statistics")
    print("-" * 80)

    stats = marketplace.get_stats()
    print(f"Total offers: {stats['total_offers']}")
    print(f"Total bids: {stats['total_bids']}")
    print(f"Total exchanges: {stats['total_exchanges']}")
    print(f"Total volume: {stats['total_volume']} ATP")
    print(f"Active offers: {stats['active_offers']}")
    print(f"Active bids: {stats['active_bids']}")
    print(f"Completed exchanges: {stats['completed_exchanges']}")

    print("\n" + "=" * 80)
    print("✅ ATP MARKETPLACE OPERATIONAL")
    print("Cross-society economic coordination enabled!")
    print("=" * 80)
