"""
Integration Tests for T3 Trust Tracking in Authorization Flow

Tests the complete integration of T3 (Talent/Training/Temperament) trust
tracking with the Web4 vendor SDK authorization system.

Key test scenarios:
- T3 trust threshold enforcement
- Trust score updates from transaction outcomes
- Impact of successful vs failed transactions
- Composite trust calculation in real authorization flow
- Trust evolution over multiple transactions

Author: Claude (Anthropic AI), interactive development
Date: November 18, 2025
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone

# Import components
from t3_tracker import T3Tracker
from vendor_sdk import Web4Verifier
from atp_tracker import ATPTracker
from revocation_registry import RevocationRegistry
from nonce_tracker import NonceTracker
from timestamp_validator import TimestampValidator
from key_rotation import KeyRotationManager
from witness_enforcer import WitnessEnforcer
from resource_constraints import ResourceConstraints, PermissionLevel
from financial_binding import FinancialBinding, PaymentMethod, PaymentMethodType


class TestT3Authorization:
    """Test T3 trust tracking integration with authorization."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create all security components
        self.atp_tracker = ATPTracker()
        self.revocation_registry = RevocationRegistry()
        self.nonce_tracker = NonceTracker()
        self.timestamp_validator = TimestampValidator()
        self.key_rotation_manager = KeyRotationManager()
        self.witness_enforcer = WitnessEnforcer()

        # Create T3 tracker with unique storage file for this test
        import tempfile
        import os
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        self.t3_tracker = T3Tracker(storage_path=self.temp_file.name)

        # Create resource constraints
        self.constraints = ResourceConstraints()
        self.constraints.add_allowed("amazon.com:products/*")

        # Create financial binding
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Alice Smith"
        )

        self.binding = FinancialBinding(
            lct_id="agent-test-01",
            payment_method=card,
            daily_limit=Decimal("1000.00"),
            per_transaction_limit=Decimal("100.00"),
            allowed_merchants=["amazon.com"]
        )

        # Set up ATP account
        self.atp_tracker.create_account("agent-test-01", daily_limit=1000, per_action_limit=100)

    def teardown_method(self):
        """Clean up test fixtures."""
        import os
        if hasattr(self, 'temp_file') and os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_trust_threshold_enforcement(self):
        """Test that authorization is denied when trust is below threshold."""
        # Create verifier with min trust threshold of 0.5 (50%)
        verifier = Web4Verifier(
            atp_tracker=self.atp_tracker,
            revocation_registry=self.revocation_registry,
            nonce_tracker=self.nonce_tracker,
            timestamp_validator=self.timestamp_validator,
            key_rotation_manager=self.key_rotation_manager,
            witness_enforcer=self.witness_enforcer,
            resource_constraints_registry={"human-alice": self.constraints},
            financial_binding_registry={"agent-test-01": self.binding},
            t3_tracker=self.t3_tracker,
            min_trust_threshold=0.5  # Require 50% trust
        )

        # Create T3 profile with low trust
        self.t3_tracker.create_profile(
            "agent-test-01",
            initial_talent=0.3,
            initial_training=0.0,
            initial_temperament=0.3
        )

        # Check composite trust (should be around 0.24)
        composite = self.t3_tracker.get_composite_trust("agent-test-01")
        assert composite < 0.5, f"Trust should be below threshold: {composite}"

        # Create authorization request
        lct_chain = {
            "delegator": "human-alice",
            "delegatee": "agent-test-01",
            "delegation_timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "delegation_signature": "sig-alice",
            "request_signature": "sig-agent",
            "witnesses": []
        }

        # Verify authorization - should be DENIED due to low trust
        result = verifier.verify_authorization(
            lct_chain=lct_chain,
            resource_id="amazon.com:products/book-123",
            amount=Decimal("50.00"),
            merchant="amazon.com"
        )

        assert not result.authorized, "Authorization should be denied due to low trust"
        assert "Trust Score (T3)" in [c.check_name for c in result.checks]

        # Find the trust check
        trust_check = [c for c in result.checks if c.check_name == "Trust Score (T3)"][0]
        assert not trust_check.passed, "Trust check should fail"
        assert "Trust too low" in trust_check.message

    def test_trust_improvement_allows_authorization(self):
        """Test that improving trust through transactions eventually allows authorization."""
        # Create verifier with min trust threshold of 0.4 (40%)
        verifier = Web4Verifier(
            atp_tracker=self.atp_tracker,
            revocation_registry=self.revocation_registry,
            nonce_tracker=self.nonce_tracker,
            timestamp_validator=self.timestamp_validator,
            key_rotation_manager=self.key_rotation_manager,
            witness_enforcer=self.witness_enforcer,
            resource_constraints_registry={"human-alice": self.constraints},
            financial_binding_registry={"agent-test-01": self.binding},
            t3_tracker=self.t3_tracker,
            min_trust_threshold=0.4
        )

        # Create T3 profile with moderate initial talent but no training
        self.t3_tracker.create_profile(
            "agent-test-01",
            initial_talent=0.6,
            initial_training=0.0,
            initial_temperament=0.6
        )

        # Initial trust should be around 0.36 (below threshold)
        initial_trust = self.t3_tracker.get_composite_trust("agent-test-01")
        assert initial_trust < 0.4, f"Initial trust should be below threshold: {initial_trust}"

        # Record several successful transactions to build training
        for i in range(5):
            success, msg = self.t3_tracker.record_transaction(
                agent_id="agent-test-01",
                transaction_type="purchase",
                success=True,
                amount=25.0,
                within_constraints=True,
                quality_score=0.9
            )
            assert success, f"Transaction recording should succeed: {msg}"

        # Trust should have improved significantly
        improved_trust = self.t3_tracker.get_composite_trust("agent-test-01")
        assert improved_trust > initial_trust, "Trust should improve after successful transactions"
        assert improved_trust >= 0.4, f"Trust should now be above threshold: {improved_trust}"

        # Now authorization should PASS
        lct_chain = {
            "delegator": "human-alice",
            "delegatee": "agent-test-01",
            "delegation_timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "delegation_signature": "sig-alice",
            "request_signature": "sig-agent",
            "witnesses": []
        }

        result = verifier.verify_authorization(
            lct_chain=lct_chain,
            resource_id="amazon.com:products/book-456",
            amount=Decimal("30.00"),
            merchant="amazon.com"
        )

        assert result.authorized, "Authorization should pass with improved trust"

        # Find the trust check
        trust_check = [c for c in result.checks if c.check_name == "Trust Score (T3)"][0]
        assert trust_check.passed, "Trust check should pass"
        assert "Trust:" in trust_check.message

    def test_failed_transactions_lower_trust(self):
        """Test that failed transactions decrease trust scores."""
        # Create verifier with low threshold
        verifier = Web4Verifier(
            atp_tracker=self.atp_tracker,
            revocation_registry=self.revocation_registry,
            nonce_tracker=self.nonce_tracker,
            timestamp_validator=self.timestamp_validator,
            key_rotation_manager=self.key_rotation_manager,
            witness_enforcer=self.witness_enforcer,
            resource_constraints_registry={"human-alice": self.constraints},
            financial_binding_registry={"agent-test-01": self.binding},
            t3_tracker=self.t3_tracker,
            min_trust_threshold=0.3
        )

        # Create T3 profile with good initial scores
        self.t3_tracker.create_profile(
            "agent-test-01",
            initial_talent=0.8,
            initial_training=0.5,
            initial_temperament=0.8
        )

        initial_trust = self.t3_tracker.get_composite_trust("agent-test-01")
        assert initial_trust >= 0.3, "Initial trust should be above threshold"

        # Record several FAILED transactions
        for i in range(5):
            self.t3_tracker.record_transaction(
                agent_id="agent-test-01",
                transaction_type="purchase",
                success=False,  # Failed!
                amount=25.0,
                within_constraints=True,
                quality_score=0.2  # Low quality
            )

        # Trust should have decreased
        degraded_trust = self.t3_tracker.get_composite_trust("agent-test-01")
        assert degraded_trust < initial_trust, f"Trust should decrease after failures: {degraded_trust} vs {initial_trust}"

        # Talent specifically should be lower due to poor quality and failures
        scores = self.t3_tracker.get_t3_scores("agent-test-01")
        assert scores["talent"] < 0.8, f"Talent should decrease after failures: {scores['talent']}"

    def test_constraint_violations_hurt_temperament(self):
        """Test that transactions violating constraints hurt temperament score."""
        # Create T3 profile
        self.t3_tracker.create_profile(
            "agent-test-01",
            initial_talent=0.7,
            initial_training=0.5,
            initial_temperament=0.9  # High temperament initially
        )

        initial_temperament = self.t3_tracker.get_t3_scores("agent-test-01")["temperament"]

        # Record transactions that violate constraints
        for i in range(3):
            self.t3_tracker.record_transaction(
                agent_id="agent-test-01",
                transaction_type="purchase",
                success=True,  # Transaction succeeded
                amount=25.0,
                within_constraints=False,  # But violated constraints!
                quality_score=0.9
            )

        # Temperament should decrease due to constraint violations
        new_scores = self.t3_tracker.get_t3_scores("agent-test-01")
        assert new_scores["temperament"] < initial_temperament, \
            f"Temperament should decrease after violations: {new_scores['temperament']} vs {initial_temperament}"

    def test_first_transaction_creates_profile(self):
        """Test that first transaction for unknown agent creates T3 profile."""
        # Create verifier
        verifier = Web4Verifier(
            atp_tracker=self.atp_tracker,
            revocation_registry=self.revocation_registry,
            nonce_tracker=self.nonce_tracker,
            timestamp_validator=self.timestamp_validator,
            key_rotation_manager=self.key_rotation_manager,
            witness_enforcer=self.witness_enforcer,
            resource_constraints_registry={"human-alice": self.constraints},
            financial_binding_registry={"agent-test-01": self.binding},
            t3_tracker=self.t3_tracker,
            min_trust_threshold=0.3
        )

        # Agent has no T3 profile yet
        assert self.t3_tracker.get_profile("agent-test-01") is None

        # Authorize transaction
        lct_chain = {
            "delegator": "human-alice",
            "delegatee": "agent-test-01",
            "delegation_timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "delegation_signature": "sig-alice",
            "request_signature": "sig-agent",
            "witnesses": []
        }

        result = verifier.verify_authorization(
            lct_chain=lct_chain,
            resource_id="amazon.com:products/book-789",
            amount=Decimal("20.00"),
            merchant="amazon.com"
        )

        # Should be authorized (new agent, no history)
        assert result.authorized, "First transaction should be authorized"

        # Find trust check
        trust_check = [c for c in result.checks if c.check_name == "Trust Score (T3)"][0]
        assert trust_check.passed, "Trust check should pass for new agent"
        assert "New agent" in trust_check.message

        # Now record the purchase
        verifier.record_purchase(
            delegatee_id="agent-test-01",
            amount=Decimal("20.00"),
            merchant="amazon.com",
            item_id="book-789",
            success=True,
            within_constraints=True,
            quality_score=0.8
        )

        # T3 profile should now exist
        assert self.t3_tracker.get_profile("agent-test-01") is not None
        assert self.t3_tracker.get_composite_trust("agent-test-01") is not None

    def test_trust_scores_in_verification_result(self):
        """Test that trust scores are included in verification result."""
        verifier = Web4Verifier(
            atp_tracker=self.atp_tracker,
            revocation_registry=self.revocation_registry,
            nonce_tracker=self.nonce_tracker,
            timestamp_validator=self.timestamp_validator,
            key_rotation_manager=self.key_rotation_manager,
            witness_enforcer=self.witness_enforcer,
            resource_constraints_registry={"human-alice": self.constraints},
            financial_binding_registry={"agent-test-01": self.binding},
            t3_tracker=self.t3_tracker,
            min_trust_threshold=0.3
        )

        # Create T3 profile
        self.t3_tracker.create_profile(
            "agent-test-01",
            initial_talent=0.7,
            initial_training=0.4,
            initial_temperament=0.8
        )

        lct_chain = {
            "delegator": "human-alice",
            "delegatee": "agent-test-01",
            "delegation_timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "delegation_signature": "sig-alice",
            "request_signature": "sig-agent",
            "witnesses": []
        }

        result = verifier.verify_authorization(
            lct_chain=lct_chain,
            resource_id="amazon.com:products/test-item",
            amount=Decimal("15.00"),
            merchant="amazon.com"
        )

        assert result.authorized, "Authorization should pass"

        # Find trust check in results
        trust_check = [c for c in result.checks if c.check_name == "Trust Score (T3)"][0]
        assert trust_check.passed, "Trust check should pass"

        # Message should include individual scores
        assert "Talent:" in trust_check.message
        assert "Training:" in trust_check.message
        assert "Temperament:" in trust_check.message

    def test_composite_trust_weighting(self):
        """Test that composite trust uses correct weighting formula."""
        # Create profile with known scores
        self.t3_tracker.create_profile(
            "agent-test-01",
            initial_talent=1.0,
            initial_training=0.0,
            initial_temperament=0.5
        )

        # Composite should be: 0.3*1.0 + 0.5*0.0 + 0.2*0.5 = 0.3 + 0.0 + 0.1 = 0.4
        composite = self.t3_tracker.get_composite_trust("agent-test-01")
        assert abs(composite - 0.4) < 0.01, f"Composite trust calculation incorrect: {composite}"

        # Create another profile
        self.t3_tracker.create_profile(
            "agent-test-02",
            initial_talent=0.6,
            initial_training=0.8,
            initial_temperament=0.7
        )

        # Composite should be: 0.3*0.6 + 0.5*0.8 + 0.2*0.7 = 0.18 + 0.4 + 0.14 = 0.72
        composite2 = self.t3_tracker.get_composite_trust("agent-test-02")
        assert abs(composite2 - 0.72) < 0.01, f"Composite trust calculation incorrect: {composite2}"


class TestT3RecordPurchase:
    """Test T3 integration with record_purchase method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.atp_tracker = ATPTracker()
        self.revocation_registry = RevocationRegistry()
        self.nonce_tracker = NonceTracker()
        self.timestamp_validator = TimestampValidator()
        self.key_rotation_manager = KeyRotationManager()
        self.witness_enforcer = WitnessEnforcer()

        # Create T3 tracker with unique storage file for this test
        import tempfile
        import os
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        self.t3_tracker = T3Tracker(storage_path=self.temp_file.name)

        # Create financial binding
        card = PaymentMethod(
            method_type=PaymentMethodType.CREDIT_CARD,
            identifier="4242",
            provider="Visa",
            holder_name="Bob Jones"
        )

        self.binding = FinancialBinding(
            lct_id="agent-purchase-test",
            payment_method=card,
            daily_limit=Decimal("500.00"),
            per_transaction_limit=Decimal("50.00"),
            allowed_merchants=["store.com"]
        )

        self.verifier = Web4Verifier(
            atp_tracker=self.atp_tracker,
            revocation_registry=self.revocation_registry,
            nonce_tracker=self.nonce_tracker,
            timestamp_validator=self.timestamp_validator,
            key_rotation_manager=self.key_rotation_manager,
            witness_enforcer=self.witness_enforcer,
            financial_binding_registry={"agent-purchase-test": self.binding},
            t3_tracker=self.t3_tracker
        )

    def teardown_method(self):
        """Clean up test fixtures."""
        import os
        if hasattr(self, 'temp_file') and os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_record_purchase_creates_t3_profile(self):
        """Test that record_purchase creates T3 profile if doesn't exist."""
        # No profile initially
        assert self.t3_tracker.get_profile("agent-purchase-test") is None

        # Record purchase
        self.verifier.record_purchase(
            delegatee_id="agent-purchase-test",
            amount=Decimal("25.00"),
            merchant="store.com",
            item_id="item-123",
            success=True,
            within_constraints=True,
            quality_score=0.85
        )

        # Profile should now exist
        profile = self.t3_tracker.get_profile("agent-purchase-test")
        assert profile is not None
        assert profile.total_transactions == 1

    def test_record_purchase_updates_trust(self):
        """Test that record_purchase updates T3 trust scores."""
        # Create initial profile
        self.t3_tracker.create_profile(
            "agent-purchase-test",
            initial_talent=0.5,
            initial_training=0.0,
            initial_temperament=0.5
        )

        initial_trust = self.t3_tracker.get_composite_trust("agent-purchase-test")

        # Record successful purchase
        self.verifier.record_purchase(
            delegatee_id="agent-purchase-test",
            amount=Decimal("30.00"),
            merchant="store.com",
            item_id="item-456",
            success=True,
            within_constraints=True,
            quality_score=0.95
        )

        # Trust should improve
        new_trust = self.t3_tracker.get_composite_trust("agent-purchase-test")
        assert new_trust > initial_trust, f"Trust should improve: {new_trust} vs {initial_trust}"

        # Training should have increased
        scores = self.t3_tracker.get_t3_scores("agent-purchase-test")
        assert scores["training"] > 0.0, "Training should increase from experience"

    def test_record_purchase_with_failure(self):
        """Test that record_purchase handles failures correctly."""
        # Create profile
        self.t3_tracker.create_profile(
            "agent-purchase-test",
            initial_talent=0.8,
            initial_training=0.5,
            initial_temperament=0.8
        )

        initial_talent = self.t3_tracker.get_t3_scores("agent-purchase-test")["talent"]

        # Record failed purchase
        self.verifier.record_purchase(
            delegatee_id="agent-purchase-test",
            amount=Decimal("20.00"),
            merchant="store.com",
            item_id="item-fail",
            success=False,  # Failed!
            within_constraints=True,
            quality_score=0.1  # Poor quality
        )

        # Talent should decrease
        new_talent = self.t3_tracker.get_t3_scores("agent-purchase-test")["talent"]
        assert new_talent < initial_talent, f"Talent should decrease after failure: {new_talent} vs {initial_talent}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
