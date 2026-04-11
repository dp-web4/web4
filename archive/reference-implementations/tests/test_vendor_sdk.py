"""
Unit tests for Web4 Vendor SDK

Tests the merchant integration library for authorization verification.

Author: Claude (Anthropic AI), autonomous development
Date: November 10, 2025
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone

# Import from parent directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vendor_sdk import Web4Verifier, VerificationStatus
from atp_tracker import ATPTracker
from revocation_registry import RevocationRegistry
from nonce_tracker import NonceTracker
from timestamp_validator import TimestampValidator
from key_rotation import KeyRotationManager
from witness_enforcer import WitnessEnforcer
from resource_constraints import ResourceConstraints, PermissionLevel
from financial_binding import FinancialBinding, PaymentMethod, PaymentMethodType


class TestWeb4Verifier:
    """Test Web4Verifier class."""

    def test_create_verifier(self):
        """Test creating verifier with all components."""
        verifier = Web4Verifier(
            atp_tracker=ATPTracker(),
            revocation_registry=RevocationRegistry(),
            nonce_tracker=NonceTracker(),
            timestamp_validator=TimestampValidator(),
            key_rotation_manager=KeyRotationManager(),
            witness_enforcer=WitnessEnforcer()
        )

        assert verifier.atp_tracker is not None
        assert verifier.revocation_registry is not None

    def test_verify_authorization_basic(self):
        """Test basic authorization verification."""
        # Setup components
        atp_tracker = ATPTracker()
        atp_tracker.create_account("agent-test", daily_limit=1000, per_action_limit=100)

        constraints = ResourceConstraints()
        constraints.add_allowed("test:resource/*")

        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Test User"
        )

        binding = FinancialBinding(
            lct_id="agent-test",
            payment_method=card,
            daily_limit=Decimal("1000.00"),
            per_transaction_limit=Decimal("100.00")
        )

        verifier = Web4Verifier(
            atp_tracker=atp_tracker,
            revocation_registry=RevocationRegistry(),
            nonce_tracker=NonceTracker(),
            timestamp_validator=TimestampValidator(),
            key_rotation_manager=KeyRotationManager(),
            witness_enforcer=WitnessEnforcer(),
            resource_constraints_registry={"user-123": constraints},
            financial_binding_registry={"agent-test": binding}
        )

        # Create LCT chain
        lct_chain = {
            "delegator": "user-123",
            "delegatee": "agent-test",
            "delegation_timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "delegation_signature": "sig-user-...",
            "request_signature": "sig-agent-...",
            "witnesses": []
        }

        # Verify
        result = verifier.verify_authorization(
            lct_chain=lct_chain,
            resource_id="test:resource/item-123",
            amount=Decimal("50.00"),
            merchant="test-merchant",
            description="Test purchase"
        )

        assert result.authorized is True
        assert result.status == VerificationStatus.AUTHORIZED
        assert result.delegator_id == "user-123"
        assert result.delegatee_id == "agent-test"

    def test_verify_purchase_shorthand(self):
        """Test simplified purchase verification."""
        # Setup
        atp_tracker = ATPTracker()
        atp_tracker.create_account("agent-test", daily_limit=1000, per_action_limit=100)

        constraints = ResourceConstraints()
        constraints.add_allowed("amazon.com:products/*")

        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Test User"
        )

        binding = FinancialBinding(
            lct_id="agent-test",
            payment_method=card,
            daily_limit=Decimal("1000.00"),
            per_transaction_limit=Decimal("100.00"),
            allowed_merchants=["amazon.com"]
        )

        verifier = Web4Verifier(
            atp_tracker=atp_tracker,
            revocation_registry=RevocationRegistry(),
            nonce_tracker=NonceTracker(),
            timestamp_validator=TimestampValidator(),
            key_rotation_manager=KeyRotationManager(),
            witness_enforcer=WitnessEnforcer(),
            resource_constraints_registry={"user-123": constraints},
            financial_binding_registry={"agent-test": binding}
        )

        lct_chain = {
            "delegator": "user-123",
            "delegatee": "agent-test",
            "delegation_timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }

        # Verify purchase
        result = verifier.verify_purchase(
            lct_chain=lct_chain,
            item_id="books/isbn-123",
            amount=Decimal("75.00"),
            merchant="amazon.com",
            category="books"
        )

        assert result.authorized is True

    def test_record_purchase(self):
        """Test recording purchase after verification."""
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Test User"
        )

        binding = FinancialBinding(
            lct_id="agent-test",
            payment_method=card,
            daily_limit=Decimal("1000.00"),
            per_transaction_limit=Decimal("100.00")
        )

        verifier = Web4Verifier(
            atp_tracker=ATPTracker(),
            revocation_registry=RevocationRegistry(),
            nonce_tracker=NonceTracker(),
            timestamp_validator=TimestampValidator(),
            key_rotation_manager=KeyRotationManager(),
            witness_enforcer=WitnessEnforcer(),
            financial_binding_registry={"agent-test": binding}
        )

        # Record purchase
        recorded = verifier.record_purchase(
            delegatee_id="agent-test",
            amount=Decimal("50.00"),
            merchant="test-merchant",
            item_id="item-123",
            category="books"
        )

        assert recorded is True
        assert len(binding.charges) == 1
        assert binding.charges[0].amount == Decimal("50.00")

    def test_verification_result_to_dict(self):
        """Test verification result serialization."""
        from vendor_sdk import VerificationResult

        result = VerificationResult(
            status=VerificationStatus.AUTHORIZED,
            authorized=True,
            delegator_id="user-123",
            delegatee_id="agent-test"
        )

        result.add_check("Test Check", True, "Check passed")

        data = result.to_dict()

        assert data["status"] == "authorized"
        assert data["authorized"] is True
        assert data["delegator_id"] == "user-123"
        assert len(data["checks"]) == 1

    def test_resource_not_authorized(self):
        """Test denial when resource not in scope."""
        constraints = ResourceConstraints()
        constraints.add_allowed("amazon.com:products/books/*")

        verifier = Web4Verifier(
            atp_tracker=ATPTracker(),
            revocation_registry=RevocationRegistry(),
            nonce_tracker=NonceTracker(),
            timestamp_validator=TimestampValidator(),
            key_rotation_manager=KeyRotationManager(),
            witness_enforcer=WitnessEnforcer(),
            resource_constraints_registry={"user-123": constraints}
        )

        lct_chain = {
            "delegator": "user-123",
            "delegatee": "agent-test",
            "delegation_timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }

        # Try to access electronics (not in scope)
        result = verifier.verify_authorization(
            lct_chain=lct_chain,
            resource_id="amazon.com:products/electronics/laptop-456",
            permission_level=PermissionLevel.WRITE
        )

        assert result.authorized is False
        assert result.status == VerificationStatus.DENIED
        assert "resource" in result.denial_reason.lower()

    def test_amount_over_limit(self):
        """Test denial when amount exceeds limit."""
        atp_tracker = ATPTracker()
        atp_tracker.create_account("agent-test", daily_limit=1000, per_action_limit=100)

        constraints = ResourceConstraints()
        constraints.add_allowed("test:*")

        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Test User"
        )

        binding = FinancialBinding(
            lct_id="agent-test",
            payment_method=card,
            daily_limit=Decimal("1000.00"),
            per_transaction_limit=Decimal("100.00")
        )

        verifier = Web4Verifier(
            atp_tracker=atp_tracker,
            revocation_registry=RevocationRegistry(),
            nonce_tracker=NonceTracker(),
            timestamp_validator=TimestampValidator(),
            key_rotation_manager=KeyRotationManager(),
            witness_enforcer=WitnessEnforcer(),
            resource_constraints_registry={"user-123": constraints},
            financial_binding_registry={"agent-test": binding}
        )

        lct_chain = {
            "delegator": "user-123",
            "delegatee": "agent-test",
            "delegation_timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }

        # Try to charge $150 (over $100 per-transaction limit)
        result = verifier.verify_authorization(
            lct_chain=lct_chain,
            resource_id="test:item",
            amount=Decimal("150.00"),
            merchant="test-merchant"
        )

        assert result.authorized is False
        assert "per-transaction limit" in result.denial_reason.lower()

    def test_replay_attack_prevention(self):
        """Test nonce-based replay prevention."""
        nonce_tracker = NonceTracker()

        # Generate nonce
        nonce = nonce_tracker.generate_nonce("agent-test")

        constraints = ResourceConstraints()
        constraints.add_allowed("test:*")

        verifier = Web4Verifier(
            atp_tracker=ATPTracker(),
            revocation_registry=RevocationRegistry(),
            nonce_tracker=nonce_tracker,
            timestamp_validator=TimestampValidator(),
            key_rotation_manager=KeyRotationManager(),
            witness_enforcer=WitnessEnforcer(),
            resource_constraints_registry={"user-123": constraints}
        )

        lct_chain = {
            "delegator": "user-123",
            "delegatee": "agent-test",
            "delegation_timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }

        # First request (should work)
        result1 = verifier.verify_authorization(
            lct_chain=lct_chain,
            resource_id="test:item",
            nonce=nonce
        )
        assert result1.authorized is True

        # Second request with same nonce (should fail - replay attack)
        result2 = verifier.verify_authorization(
            lct_chain=lct_chain,
            resource_id="test:item",
            nonce=nonce
        )
        assert result2.authorized is False
        assert "replay" in result2.denial_reason.lower()


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
