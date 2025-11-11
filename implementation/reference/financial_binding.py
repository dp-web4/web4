"""
Financial Binding for Web4 LCTs

Links payment methods to LCT identities with enforced spending limits.
Enables secure agent authorization for purchases and financial transactions.

Key Features:
- Payment method binding to LCTs
- Daily and per-transaction spending limits
- Real-time charge authorization
- Multiple payment method types support
- Spending history and audit trail
- Automatic limit reset (daily)
- Merchant whitelisting/blacklisting

Addresses Critical Questions:
- "Who pays for agent's actions?" → Payment method linked to LCT
- "What's maximum liability?" → Daily/transaction limits enforced
- "How to prevent unauthorized charges?" → Pre-authorization checks

Usage:
    # Create financial binding
    binding = FinancialBinding(
        lct_id="agent-claude-42",
        payment_method=CreditCard(...),
        daily_limit=1000.00,
        per_transaction_limit=100.00
    )

    # Authorize charge before processing
    authorized, msg = binding.authorize_charge(
        amount=75.00,
        merchant="amazon.com",
        description="Book purchase"
    )

    if authorized:
        process_payment()
        binding.record_charge(75.00, "amazon.com", "book-12345")

Author: Claude (Anthropic AI), autonomous development
Date: November 10, 2025
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from decimal import Decimal


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PaymentMethodType(Enum):
    """Types of payment methods."""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_ACCOUNT = "bank_account"
    CRYPTO_WALLET = "crypto_wallet"
    DIGITAL_WALLET = "digital_wallet"  # Apple Pay, Google Pay, etc.


class ChargeStatus(Enum):
    """Status of a charge."""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


@dataclass
class PaymentMethod:
    """Payment method details."""
    method_type: PaymentMethodType
    identifier: str  # Last 4 digits, account number, wallet address, etc.
    provider: str    # Visa, Mastercard, Chase, Coinbase, etc.
    holder_name: str

    # Optional metadata
    expiry: Optional[str] = None  # For cards: "MM/YY"
    billing_address: Optional[Dict] = None

    # Security
    token: Optional[str] = None  # Tokenized reference (for secure storage)

    def display_name(self) -> str:
        """Human-readable display name."""
        return f"{self.provider} {self.method_type.value} ending in {self.identifier}"


@dataclass
class ChargeRecord:
    """Record of a charge attempt."""
    charge_id: str
    timestamp: str
    lct_id: str
    amount: Decimal
    merchant: str
    description: str
    status: ChargeStatus
    authorization_message: str = ""

    # Optional metadata
    item_id: Optional[str] = None
    category: Optional[str] = None
    refund_amount: Optional[Decimal] = None
    refund_timestamp: Optional[str] = None


class FinancialBinding:
    """
    Links payment method to LCT with spending limits.

    Enforces:
    - Daily spending limits
    - Per-transaction spending limits
    - Merchant whitelist/blacklist
    - Spending category limits
    - Automatic daily reset
    """

    def __init__(
        self,
        lct_id: str,
        payment_method: PaymentMethod,
        daily_limit: Decimal,
        per_transaction_limit: Decimal,
        allowed_merchants: Optional[List[str]] = None,
        denied_merchants: Optional[List[str]] = None,
        allowed_categories: Optional[List[str]] = None
    ):
        """
        Initialize financial binding.

        Args:
            lct_id: LCT identifier this binding is for
            payment_method: Payment method details
            daily_limit: Maximum spending per day
            per_transaction_limit: Maximum per transaction
            allowed_merchants: Whitelist of allowed merchants (None = all allowed)
            denied_merchants: Blacklist of denied merchants
            allowed_categories: Allowed purchase categories (None = all allowed)
        """
        self.lct_id = lct_id
        self.payment_method = payment_method
        self.daily_limit = Decimal(str(daily_limit))
        self.per_transaction_limit = Decimal(str(per_transaction_limit))

        # Merchant controls
        self.allowed_merchants = set(allowed_merchants) if allowed_merchants else None
        self.denied_merchants = set(denied_merchants) if denied_merchants else set()

        # Category controls
        self.allowed_categories = set(allowed_categories) if allowed_categories else None

        # Spending tracking
        self.charges: List[ChargeRecord] = []
        self.last_reset: datetime = datetime.now(timezone.utc)

        logger.info(
            f"FinancialBinding created for {lct_id}: "
            f"${daily_limit}/day, ${per_transaction_limit}/transaction, "
            f"payment: {payment_method.display_name()}"
        )

    def authorize_charge(
        self,
        amount: Decimal,
        merchant: str,
        description: str,
        category: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Authorize a charge before processing.

        Checks:
        1. Amount within per-transaction limit
        2. Merchant not blacklisted
        3. Merchant in whitelist (if whitelist exists)
        4. Category allowed (if category restrictions exist)
        5. Daily spending limit not exceeded

        Args:
            amount: Charge amount
            merchant: Merchant identifier
            description: Charge description
            category: Purchase category (optional)

        Returns:
            Tuple of (authorized: bool, message: str)
        """
        amount = Decimal(str(amount))

        # Check 1: Per-transaction limit
        if amount > self.per_transaction_limit:
            msg = (
                f"Amount ${amount} exceeds per-transaction limit "
                f"${self.per_transaction_limit}"
            )
            logger.warning(f"❌ Charge denied for {self.lct_id}: {msg}")
            return False, msg

        # Check 2: Blacklisted merchant
        if merchant in self.denied_merchants:
            msg = f"Merchant '{merchant}' is blacklisted"
            logger.warning(f"❌ Charge denied for {self.lct_id}: {msg}")
            return False, msg

        # Check 3: Whitelisted merchant (if whitelist exists)
        if self.allowed_merchants is not None:
            if merchant not in self.allowed_merchants:
                msg = f"Merchant '{merchant}' not in whitelist"
                logger.warning(f"❌ Charge denied for {self.lct_id}: {msg}")
                return False, msg

        # Check 4: Category allowed (if category restrictions exist)
        if category and self.allowed_categories is not None:
            if category not in self.allowed_categories:
                msg = f"Category '{category}' not allowed"
                logger.warning(f"❌ Charge denied for {self.lct_id}: {msg}")
                return False, msg

        # Check 5: Daily limit
        self._reset_if_new_day()
        daily_spent = self.get_daily_spending()

        if daily_spent + amount > self.daily_limit:
            remaining = self.daily_limit - daily_spent
            msg = (
                f"Would exceed daily limit: spent ${daily_spent}, "
                f"limit ${self.daily_limit}, remaining ${remaining}"
            )
            logger.warning(f"❌ Charge denied for {self.lct_id}: {msg}")
            return False, msg

        # All checks passed!
        msg = (
            f"Authorized ${amount} at {merchant} "
            f"(daily: ${daily_spent + amount}/${self.daily_limit})"
        )
        logger.info(f"✅ Charge authorized for {self.lct_id}: {msg}")
        return True, msg

    def record_charge(
        self,
        amount: Decimal,
        merchant: str,
        description: str,
        item_id: Optional[str] = None,
        category: Optional[str] = None,
        status: ChargeStatus = ChargeStatus.COMPLETED
    ) -> ChargeRecord:
        """
        Record a completed charge.

        Call this AFTER successfully processing payment.

        Args:
            amount: Charge amount
            merchant: Merchant identifier
            description: Charge description
            item_id: Item/product identifier
            category: Purchase category
            status: Charge status

        Returns:
            ChargeRecord object
        """
        amount = Decimal(str(amount))

        charge = ChargeRecord(
            charge_id=self._generate_charge_id(),
            timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            lct_id=self.lct_id,
            amount=amount,
            merchant=merchant,
            description=description,
            status=status,
            item_id=item_id,
            category=category
        )

        self.charges.append(charge)

        logger.info(
            f"Charge recorded for {self.lct_id}: "
            f"${amount} at {merchant} ({status.value})"
        )

        return charge

    def refund_charge(
        self,
        charge_id: str,
        amount: Optional[Decimal] = None,
        reason: str = "refund"
    ) -> bool:
        """
        Record a refund for a charge.

        Args:
            charge_id: ID of charge to refund
            amount: Refund amount (None = full refund)
            reason: Refund reason

        Returns:
            True if successful, False if charge not found
        """
        for charge in self.charges:
            if charge.charge_id == charge_id:
                refund_amount = amount if amount else charge.amount
                charge.status = ChargeStatus.REFUNDED
                charge.refund_amount = Decimal(str(refund_amount))
                charge.refund_timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

                logger.info(
                    f"Refund recorded for {self.lct_id}: "
                    f"${refund_amount} for charge {charge_id} ({reason})"
                )
                return True

        logger.warning(f"Charge not found for refund: {charge_id}")
        return False

    def get_daily_spending(self) -> Decimal:
        """Get total spending today."""
        self._reset_if_new_day()

        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        total = Decimal('0')
        for charge in self.charges:
            charge_time = datetime.fromisoformat(
                charge.timestamp.replace('Z', '+00:00')
            )

            # Only count completed charges from today
            if charge_time >= today_start and charge.status == ChargeStatus.COMPLETED:
                # Subtract refunds
                if charge.refund_amount:
                    total += (charge.amount - charge.refund_amount)
                else:
                    total += charge.amount

        return total

    def get_remaining_daily(self) -> Decimal:
        """Get remaining daily spending limit."""
        spent = self.get_daily_spending()
        return self.daily_limit - spent

    def get_spending_by_merchant(self) -> Dict[str, Decimal]:
        """Get spending breakdown by merchant."""
        by_merchant = {}

        for charge in self.charges:
            if charge.status == ChargeStatus.COMPLETED:
                amount = charge.amount
                if charge.refund_amount:
                    amount -= charge.refund_amount

                if charge.merchant not in by_merchant:
                    by_merchant[charge.merchant] = Decimal('0')
                by_merchant[charge.merchant] += amount

        return by_merchant

    def get_spending_by_category(self) -> Dict[str, Decimal]:
        """Get spending breakdown by category."""
        by_category = {}

        for charge in self.charges:
            if charge.status == ChargeStatus.COMPLETED and charge.category:
                amount = charge.amount
                if charge.refund_amount:
                    amount -= charge.refund_amount

                if charge.category not in by_category:
                    by_category[charge.category] = Decimal('0')
                by_category[charge.category] += amount

        return by_category

    def get_charge_history(
        self,
        limit: Optional[int] = None,
        merchant: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[ChargeRecord]:
        """
        Get charge history with optional filtering.

        Args:
            limit: Maximum number of records to return
            merchant: Filter by merchant
            category: Filter by category

        Returns:
            List of ChargeRecord objects (newest first)
        """
        charges = list(reversed(self.charges))  # Newest first

        # Filter by merchant
        if merchant:
            charges = [c for c in charges if c.merchant == merchant]

        # Filter by category
        if category:
            charges = [c for c in charges if c.category == category]

        # Limit results
        if limit:
            charges = charges[:limit]

        return charges

    def update_limits(
        self,
        daily_limit: Optional[Decimal] = None,
        per_transaction_limit: Optional[Decimal] = None
    ):
        """
        Update spending limits.

        Args:
            daily_limit: New daily limit (None = keep current)
            per_transaction_limit: New per-transaction limit (None = keep current)
        """
        if daily_limit is not None:
            old_daily = self.daily_limit
            self.daily_limit = Decimal(str(daily_limit))
            logger.info(
                f"Updated daily limit for {self.lct_id}: "
                f"${old_daily} → ${self.daily_limit}"
            )

        if per_transaction_limit is not None:
            old_per_tx = self.per_transaction_limit
            self.per_transaction_limit = Decimal(str(per_transaction_limit))
            logger.info(
                f"Updated per-transaction limit for {self.lct_id}: "
                f"${old_per_tx} → ${self.per_transaction_limit}"
            )

    def add_allowed_merchant(self, merchant: str):
        """Add merchant to whitelist."""
        if self.allowed_merchants is None:
            self.allowed_merchants = set()
        self.allowed_merchants.add(merchant)
        logger.info(f"Added allowed merchant for {self.lct_id}: {merchant}")

    def add_denied_merchant(self, merchant: str):
        """Add merchant to blacklist."""
        self.denied_merchants.add(merchant)
        logger.info(f"Added denied merchant for {self.lct_id}: {merchant}")

    def _reset_if_new_day(self):
        """Reset daily tracking if it's a new day."""
        now = datetime.now(timezone.utc)
        last_reset_day = self.last_reset.date()
        current_day = now.date()

        if current_day > last_reset_day:
            logger.info(
                f"Daily reset for {self.lct_id}: "
                f"Previous spending: ${self.get_daily_spending()}"
            )
            self.last_reset = now

    def _generate_charge_id(self) -> str:
        """Generate unique charge ID."""
        import uuid
        return f"charge-{uuid.uuid4().hex[:16]}"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "lct_id": self.lct_id,
            "payment_method": {
                "method_type": self.payment_method.method_type.value,
                "identifier": self.payment_method.identifier,
                "provider": self.payment_method.provider,
                "holder_name": self.payment_method.holder_name,
                "expiry": self.payment_method.expiry,
                "billing_address": self.payment_method.billing_address,
                "token": self.payment_method.token
            },
            "daily_limit": str(self.daily_limit),
            "per_transaction_limit": str(self.per_transaction_limit),
            "allowed_merchants": list(self.allowed_merchants) if self.allowed_merchants else None,
            "denied_merchants": list(self.denied_merchants),
            "allowed_categories": list(self.allowed_categories) if self.allowed_categories else None,
            "charges": [
                {
                    "charge_id": c.charge_id,
                    "timestamp": c.timestamp,
                    "lct_id": c.lct_id,
                    "amount": str(c.amount),
                    "merchant": c.merchant,
                    "description": c.description,
                    "status": c.status.value,
                    "item_id": c.item_id,
                    "category": c.category,
                    "refund_amount": str(c.refund_amount) if c.refund_amount else None,
                    "refund_timestamp": c.refund_timestamp
                }
                for c in self.charges
            ],
            "last_reset": self.last_reset.isoformat().replace('+00:00', 'Z')
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'FinancialBinding':
        """Create from dictionary."""
        payment_method = PaymentMethod(
            method_type=PaymentMethodType(data["payment_method"]["method_type"]),
            identifier=data["payment_method"]["identifier"],
            provider=data["payment_method"]["provider"],
            holder_name=data["payment_method"]["holder_name"],
            expiry=data["payment_method"].get("expiry"),
            billing_address=data["payment_method"].get("billing_address"),
            token=data["payment_method"].get("token")
        )

        binding = cls(
            lct_id=data["lct_id"],
            payment_method=payment_method,
            daily_limit=Decimal(data["daily_limit"]),
            per_transaction_limit=Decimal(data["per_transaction_limit"]),
            allowed_merchants=data.get("allowed_merchants"),
            denied_merchants=data.get("denied_merchants", []),
            allowed_categories=data.get("allowed_categories")
        )

        # Restore charges
        binding.charges = [
            ChargeRecord(
                charge_id=c["charge_id"],
                timestamp=c["timestamp"],
                lct_id=c["lct_id"],
                amount=Decimal(c["amount"]),
                merchant=c["merchant"],
                description=c["description"],
                status=ChargeStatus(c["status"]),
                item_id=c.get("item_id"),
                category=c.get("category"),
                refund_amount=Decimal(c["refund_amount"]) if c.get("refund_amount") else None,
                refund_timestamp=c.get("refund_timestamp")
            )
            for c in data.get("charges", [])
        ]

        # Restore last reset
        binding.last_reset = datetime.fromisoformat(
            data["last_reset"].replace('Z', '+00:00')
        )

        return binding


# Example usage
if __name__ == "__main__":
    print("Financial Binding - Example Usage\n" + "="*60)

    # Create payment method
    print("\n1. Creating payment method...")
    card = PaymentMethod(
        method_type=PaymentMethodType.CREDIT_CARD,
        identifier="4242",
        provider="Visa",
        holder_name="Alice Smith",
        expiry="12/27"
    )
    print(f"  Payment method: {card.display_name()}")

    # Create financial binding
    print("\n2. Creating financial binding...")
    binding = FinancialBinding(
        lct_id="agent-claude-42",
        payment_method=card,
        daily_limit=Decimal("1000.00"),
        per_transaction_limit=Decimal("100.00"),
        allowed_merchants=["amazon.com", "bookstore.com"],
        denied_merchants=["casino.com"]
    )

    # Test charge authorization
    print("\n3. Testing charge authorization...")

    test_charges = [
        (Decimal("75.00"), "amazon.com", "Book purchase"),
        (Decimal("150.00"), "amazon.com", "Expensive item"),
        (Decimal("50.00"), "casino.com", "Gambling"),
        (Decimal("30.00"), "unknown.com", "Unknown merchant"),
        (Decimal("45.00"), "bookstore.com", "Another book")
    ]

    for amount, merchant, desc in test_charges:
        authorized, msg = binding.authorize_charge(amount, merchant, desc)
        status = "✅ AUTHORIZED" if authorized else "❌ DENIED"
        print(f"  {status}: ${amount} at {merchant}")
        print(f"    Reason: {msg}")

        if authorized:
            binding.record_charge(amount, merchant, desc)

    # Show spending summary
    print("\n4. Spending summary...")
    print(f"  Daily spent: ${binding.get_daily_spending()} / ${binding.daily_limit}")
    print(f"  Remaining today: ${binding.get_remaining_daily()}")

    # Spending by merchant
    print("\n5. Spending by merchant...")
    by_merchant = binding.get_spending_by_merchant()
    for merchant, amount in by_merchant.items():
        print(f"  {merchant}: ${amount}")

    # Recent charges
    print("\n6. Recent charges...")
    recent = binding.get_charge_history(limit=5)
    for charge in recent:
        print(f"  {charge.timestamp[:19]}: ${charge.amount} at {charge.merchant}")
        print(f"    {charge.description} ({charge.status.value})")

    print("\n" + "="*60)
    print("✅ Financial Binding operational - Payment authorization enabled!")
    print("="*60)
    print("\nKey capabilities:")
    print("- Payment method linking to LCTs")
    print("- Daily and per-transaction limits")
    print("- Merchant whitelist/blacklist")
    print("- Real-time charge authorization")
    print("- Complete spending audit trail")
