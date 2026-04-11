"""
Unit tests for Financial Binding

Tests the payment integration layer for Web4 agent authorization.

Author: Claude (Anthropic AI), autonomous development
Date: November 10, 2025
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta, timezone

# Import from parent directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from financial_binding import (
    FinancialBinding,
    PaymentMethod,
    PaymentMethodType,
    ChargeStatus,
    ChargeRecord
)


class TestPaymentMethod:
    """Test PaymentMethod class."""

    def test_create_credit_card(self):
        """Test creating credit card payment method."""
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Alice Smith",
            expiry="12/27"
        )

        assert card.method_type == PaymentMethodType.CREDIT_CARD
        assert card.identifier == "4242"
        assert card.provider == "Visa"
        assert card.holder_name == "Alice Smith"

    def test_display_name(self):
        """Test payment method display name."""
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Alice Smith"
        )

        display = card.display_name()
        assert "Visa" in display
        assert "4242" in display
        assert "credit_card" in display


class TestFinancialBinding:
    """Test FinancialBinding class."""

    def test_create_binding(self):
        """Test creating financial binding."""
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Alice Smith"
        )

        binding = FinancialBinding(
            lct_id="agent-test",
            payment_method=card,
            daily_limit=Decimal("1000.00"),
            per_transaction_limit=Decimal("100.00")
        )

        assert binding.lct_id == "agent-test"
        assert binding.daily_limit == Decimal("1000.00")
        assert binding.per_transaction_limit == Decimal("100.00")

    def test_authorize_valid_charge(self):
        """Test authorizing valid charge."""
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Alice"
        )

        binding = FinancialBinding(
            lct_id="agent-test",
            payment_method=card,
            daily_limit=Decimal("1000.00"),
            per_transaction_limit=Decimal("100.00")
        )

        # Should authorize
        authorized, msg = binding.authorize_charge(
            Decimal("50.00"),
            "amazon.com",
            "Test purchase"
        )

        assert authorized is True

    def test_per_transaction_limit(self):
        """
        Critical test: Enforce per-transaction limit.

        Prevents agents from making single large purchases.
        """
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Alice"
        )

        binding = FinancialBinding(
            lct_id="agent-test",
            payment_method=card,
            daily_limit=Decimal("1000.00"),
            per_transaction_limit=Decimal("100.00")
        )

        # Try to charge $150 (over $100 limit)
        authorized, msg = binding.authorize_charge(
            Decimal("150.00"),
            "amazon.com",
            "Expensive item"
        )

        assert authorized is False, "Should reject charge over per-transaction limit"
        assert "per-transaction limit" in msg.lower()

    def test_daily_limit(self):
        """
        Critical test: Enforce daily spending limit.

        Prevents agents from unlimited spending.
        """
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Alice"
        )

        binding = FinancialBinding(
            lct_id="agent-test",
            payment_method=card,
            daily_limit=Decimal("100.00"),
            per_transaction_limit=Decimal("50.00")
        )

        # Charge $50 (OK)
        auth1, _ = binding.authorize_charge(Decimal("50.00"), "store1.com", "Item 1")
        assert auth1 is True
        binding.record_charge(Decimal("50.00"), "store1.com", "Item 1")

        # Charge another $50 (OK)
        auth2, _ = binding.authorize_charge(Decimal("50.00"), "store2.com", "Item 2")
        assert auth2 is True
        binding.record_charge(Decimal("50.00"), "store2.com", "Item 2")

        # Try to charge $10 more (should fail - would exceed $100 daily limit)
        auth3, msg = binding.authorize_charge(Decimal("10.00"), "store3.com", "Item 3")

        assert auth3 is False, "Should reject charge exceeding daily limit"
        assert "daily limit" in msg.lower()

    def test_merchant_blacklist(self):
        """
        Critical test: Prevent purchases from blacklisted merchants.

        User can block specific merchants (gambling, adult content, etc.)
        """
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Alice"
        )

        binding = FinancialBinding(
            lct_id="agent-test",
            payment_method=card,
            daily_limit=Decimal("1000.00"),
            per_transaction_limit=Decimal("100.00"),
            denied_merchants=["casino.com", "adultsite.com"]
        )

        # Try to charge at blacklisted merchant
        authorized, msg = binding.authorize_charge(
            Decimal("50.00"),
            "casino.com",
            "Gambling"
        )

        assert authorized is False, "Should reject blacklisted merchant"
        assert "blacklist" in msg.lower()

    def test_merchant_whitelist(self):
        """
        Critical test: Restrict to whitelisted merchants only.

        User can specify ONLY allowed merchants.
        """
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Alice"
        )

        binding = FinancialBinding(
            lct_id="agent-test",
            payment_method=card,
            daily_limit=Decimal("1000.00"),
            per_transaction_limit=Decimal("100.00"),
            allowed_merchants=["amazon.com", "bookstore.com"]
        )

        # Allowed merchant should work
        auth1, _ = binding.authorize_charge(
            Decimal("50.00"),
            "amazon.com",
            "Book"
        )
        assert auth1 is True

        # Non-whitelisted merchant should fail
        auth2, msg = binding.authorize_charge(
            Decimal("50.00"),
            "randomstore.com",
            "Item"
        )
        assert auth2 is False, "Should reject non-whitelisted merchant"
        assert "whitelist" in msg.lower()

    def test_category_restrictions(self):
        """Test purchase category restrictions."""
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Alice"
        )

        binding = FinancialBinding(
            lct_id="agent-test",
            payment_method=card,
            daily_limit=Decimal("1000.00"),
            per_transaction_limit=Decimal("100.00"),
            allowed_categories=["books", "music"]
        )

        # Allowed category
        auth1, _ = binding.authorize_charge(
            Decimal("30.00"),
            "store.com",
            "Book",
            category="books"
        )
        assert auth1 is True

        # Denied category
        auth2, msg = binding.authorize_charge(
            Decimal("30.00"),
            "store.com",
            "Electronics",
            category="electronics"
        )
        assert auth2 is False
        assert "category" in msg.lower()

    def test_record_charge(self):
        """Test recording completed charges."""
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Alice"
        )

        binding = FinancialBinding(
            lct_id="agent-test",
            payment_method=card,
            daily_limit=Decimal("1000.00"),
            per_transaction_limit=Decimal("100.00")
        )

        # Record charge
        charge = binding.record_charge(
            Decimal("50.00"),
            "amazon.com",
            "Book purchase",
            item_id="book-123"
        )

        assert charge.amount == Decimal("50.00")
        assert charge.merchant == "amazon.com"
        assert charge.status == ChargeStatus.COMPLETED
        assert len(binding.charges) == 1

    def test_get_daily_spending(self):
        """Test calculating daily spending."""
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Alice"
        )

        binding = FinancialBinding(
            lct_id="agent-test",
            payment_method=card,
            daily_limit=Decimal("1000.00"),
            per_transaction_limit=Decimal("100.00")
        )

        # Record multiple charges
        binding.record_charge(Decimal("50.00"), "store1.com", "Item 1")
        binding.record_charge(Decimal("30.00"), "store2.com", "Item 2")
        binding.record_charge(Decimal("20.00"), "store3.com", "Item 3")

        total = binding.get_daily_spending()
        assert total == Decimal("100.00")

    def test_get_remaining_daily(self):
        """Test calculating remaining daily budget."""
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Alice"
        )

        binding = FinancialBinding(
            lct_id="agent-test",
            payment_method=card,
            daily_limit=Decimal("500.00"),
            per_transaction_limit=Decimal("100.00")
        )

        # Spend $300
        binding.record_charge(Decimal("150.00"), "store1.com", "Item 1")
        binding.record_charge(Decimal("150.00"), "store2.com", "Item 2")

        remaining = binding.get_remaining_daily()
        assert remaining == Decimal("200.00")

    def test_refund_charge(self):
        """Test recording refunds."""
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Alice"
        )

        binding = FinancialBinding(
            lct_id="agent-test",
            payment_method=card,
            daily_limit=Decimal("1000.00"),
            per_transaction_limit=Decimal("100.00")
        )

        # Record charge
        charge = binding.record_charge(
            Decimal("50.00"),
            "amazon.com",
            "Book"
        )

        # Refund it
        success = binding.refund_charge(charge.charge_id, reason="returned")

        assert success is True
        assert charge.status == ChargeStatus.REFUNDED
        assert charge.refund_amount == Decimal("50.00")

    def test_spending_with_refunds(self):
        """Test daily spending calculation includes refunds."""
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Alice"
        )

        binding = FinancialBinding(
            lct_id="agent-test",
            payment_method=card,
            daily_limit=Decimal("1000.00"),
            per_transaction_limit=Decimal("100.00")
        )

        # Charge $100
        charge1 = binding.record_charge(Decimal("100.00"), "store.com", "Item 1")

        # Charge $50
        charge2 = binding.record_charge(Decimal("50.00"), "store.com", "Item 2")

        # Total should be $150
        assert binding.get_daily_spending() == Decimal("150.00")

        # Refund first charge
        binding.refund_charge(charge1.charge_id)

        # Total should now be $50
        assert binding.get_daily_spending() == Decimal("50.00")

    def test_spending_by_merchant(self):
        """Test spending breakdown by merchant."""
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Alice"
        )

        binding = FinancialBinding(
            lct_id="agent-test",
            payment_method=card,
            daily_limit=Decimal("1000.00"),
            per_transaction_limit=Decimal("100.00")
        )

        # Multiple charges at different merchants
        binding.record_charge(Decimal("50.00"), "amazon.com", "Book 1")
        binding.record_charge(Decimal("30.00"), "amazon.com", "Book 2")
        binding.record_charge(Decimal("40.00"), "bookstore.com", "Book 3")

        by_merchant = binding.get_spending_by_merchant()

        assert by_merchant["amazon.com"] == Decimal("80.00")
        assert by_merchant["bookstore.com"] == Decimal("40.00")

    def test_spending_by_category(self):
        """Test spending breakdown by category."""
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Alice"
        )

        binding = FinancialBinding(
            lct_id="agent-test",
            payment_method=card,
            daily_limit=Decimal("1000.00"),
            per_transaction_limit=Decimal("100.00")
        )

        # Charges in different categories
        binding.record_charge(
            Decimal("50.00"), "store.com", "Book", category="books"
        )
        binding.record_charge(
            Decimal("30.00"), "store.com", "Album", category="music"
        )
        binding.record_charge(
            Decimal("20.00"), "store.com", "Book 2", category="books"
        )

        by_category = binding.get_spending_by_category()

        assert by_category["books"] == Decimal("70.00")
        assert by_category["music"] == Decimal("30.00")

    def test_charge_history(self):
        """Test retrieving charge history."""
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Alice"
        )

        binding = FinancialBinding(
            lct_id="agent-test",
            payment_method=card,
            daily_limit=Decimal("1000.00"),
            per_transaction_limit=Decimal("100.00")
        )

        # Record several charges
        for i in range(5):
            binding.record_charge(
                Decimal(f"{10*(i+1)}.00"),
                "store.com",
                f"Item {i+1}"
            )

        # Get recent charges
        recent = binding.get_charge_history(limit=3)

        assert len(recent) == 3
        # Should be newest first
        assert recent[0].amount == Decimal("50.00")  # Item 5

    def test_update_limits(self):
        """Test updating spending limits."""
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Alice"
        )

        binding = FinancialBinding(
            lct_id="agent-test",
            payment_method=card,
            daily_limit=Decimal("1000.00"),
            per_transaction_limit=Decimal("100.00")
        )

        # Update limits
        binding.update_limits(
            daily_limit=Decimal("500.00"),
            per_transaction_limit=Decimal("50.00")
        )

        assert binding.daily_limit == Decimal("500.00")
        assert binding.per_transaction_limit == Decimal("50.00")

    def test_add_merchants(self):
        """Test adding merchants to whitelist/blacklist."""
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Alice"
        )

        binding = FinancialBinding(
            lct_id="agent-test",
            payment_method=card,
            daily_limit=Decimal("1000.00"),
            per_transaction_limit=Decimal("100.00")
        )

        # Add to whitelist
        binding.add_allowed_merchant("newstore.com")
        assert "newstore.com" in binding.allowed_merchants

        # Add to blacklist
        binding.add_denied_merchant("badstore.com")
        assert "badstore.com" in binding.denied_merchants

    def test_serialization(self):
        """Test converting to/from dictionary."""
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Alice Smith",
            expiry="12/27"
        )

        binding = FinancialBinding(
            lct_id="agent-test",
            payment_method=card,
            daily_limit=Decimal("1000.00"),
            per_transaction_limit=Decimal("100.00"),
            allowed_merchants=["amazon.com"]
        )

        # Add some charges
        binding.record_charge(Decimal("50.00"), "amazon.com", "Book")

        # Serialize
        data = binding.to_dict()

        assert data["lct_id"] == "agent-test"
        assert data["daily_limit"] == "1000.00"
        assert len(data["charges"]) == 1

        # Deserialize
        binding2 = FinancialBinding.from_dict(data)

        assert binding2.lct_id == "agent-test"
        assert binding2.daily_limit == Decimal("1000.00")
        assert len(binding2.charges) == 1
        assert binding2.charges[0].amount == Decimal("50.00")

    def test_complex_scenario(self):
        """Test complex real-world scenario."""
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Alice Smith"
        )

        # Agent with $500/day, $100/transaction, books only
        binding = FinancialBinding(
            lct_id="agent-claude-42",
            payment_method=card,
            daily_limit=Decimal("500.00"),
            per_transaction_limit=Decimal("100.00"),
            allowed_merchants=["amazon.com", "bookstore.com"],
            denied_merchants=["casino.com"],
            allowed_categories=["books", "educational"]
        )

        test_cases = [
            # (amount, merchant, category, should_authorize)
            (Decimal("75.00"), "amazon.com", "books", True),
            (Decimal("150.00"), "amazon.com", "books", False),  # Over per-tx limit
            (Decimal("50.00"), "casino.com", "books", False),   # Blacklisted
            (Decimal("40.00"), "randomstore.com", "books", False),  # Not whitelisted
            (Decimal("30.00"), "amazon.com", "electronics", False),  # Wrong category
            (Decimal("80.00"), "bookstore.com", "books", True),
        ]

        authorized_count = 0
        for amount, merchant, category, should_auth in test_cases:
            auth, msg = binding.authorize_charge(
                amount, merchant, f"Test {category}", category=category
            )

            assert auth == should_auth, f"Failed for {amount} at {merchant} ({category})"

            if auth:
                binding.record_charge(amount, merchant, f"Test {category}", category=category)
                authorized_count += 1

        # Should have authorized 2 charges ($75 + $80 = $155)
        assert authorized_count == 2
        assert binding.get_daily_spending() == Decimal("155.00")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
