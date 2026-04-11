"""
Unit tests for ATP Budget Tracker

Tests the critical security fix: ATP budget enforcement
that was previously missing from the LCT identity system.

Author: Claude (Anthropic AI), autonomous security hardening
Date: November 9, 2025
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import date

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from atp_tracker import ATPTracker, ATPAccount


class TestATPAccount:
    """Test ATPAccount data class."""

    def test_account_creation(self):
        """Test creating an ATP account."""
        account = ATPAccount(
            entity_id="test-entity",
            daily_limit=1000,
            per_action_limit=100
        )

        assert account.entity_id == "test-entity"
        assert account.daily_limit == 1000
        assert account.per_action_limit == 100
        assert account.get_usage_today() == 0
        assert account.remaining_today() == 1000

    def test_can_afford(self):
        """Test can_afford check."""
        account = ATPAccount(
            entity_id="test-entity",
            daily_limit=1000,
            per_action_limit=100
        )

        # Within limits
        assert account.can_afford(50) is True
        assert account.can_afford(100) is True

        # Exceeds per-action limit
        assert account.can_afford(150) is False

    def test_deduct(self):
        """Test ATP deduction."""
        account = ATPAccount(
            entity_id="test-entity",
            daily_limit=1000,
            per_action_limit=100
        )

        # First deduction
        assert account.deduct(50) is True
        assert account.get_usage_today() == 50
        assert account.remaining_today() == 950

        # Second deduction
        assert account.deduct(100) is True
        assert account.get_usage_today() == 150
        assert account.remaining_today() == 850

    def test_deduct_insufficient_funds(self):
        """Test deduction fails when insufficient funds."""
        account = ATPAccount(
            entity_id="test-entity",
            daily_limit=100,
            per_action_limit=50
        )

        # Use up budget (within per-action limit)
        account.deduct(50)
        account.deduct(50)

        # Should fail - no funds left
        assert account.deduct(50) is False
        assert account.get_usage_today() == 100

    def test_deduct_exceeds_per_action_limit(self):
        """Test deduction fails when exceeding per-action limit."""
        account = ATPAccount(
            entity_id="test-entity",
            daily_limit=1000,
            per_action_limit=100
        )

        # Should fail - exceeds per-action limit
        assert account.deduct(150) is False
        assert account.get_usage_today() == 0

    def test_add_earned_atp(self):
        """Test earning ATP increases daily limit."""
        account = ATPAccount(
            entity_id="test-entity",
            daily_limit=1000,
            per_action_limit=100
        )

        # Earn ATP
        account.add_earned_atp(200, "good_work")

        assert account.total_earned == 200
        assert account.daily_limit == 1200  # Increased by earned amount


class TestATPTracker:
    """Test ATPTracker class."""

    def test_create_account(self):
        """Test creating accounts."""
        tracker = ATPTracker()

        account = tracker.create_account("entity-001", 1000, 100)

        assert account.entity_id == "entity-001"
        assert account.daily_limit == 1000
        assert account.per_action_limit == 100
        assert tracker.get_balance("entity-001") == 1000

    def test_check_and_deduct_success(self):
        """Test successful authorization and deduction."""
        tracker = ATPTracker()
        tracker.create_account("entity-001", 1000, 100)

        # First action
        success, msg = tracker.check_and_deduct("entity-001", 50)

        assert success is True
        assert "Authorized" in msg
        assert tracker.get_balance("entity-001") == 950

    def test_check_and_deduct_no_account(self):
        """Test authorization fails when account doesn't exist."""
        tracker = ATPTracker()

        success, msg = tracker.check_and_deduct("nonexistent", 50)

        assert success is False
        assert "No ATP account" in msg

    def test_check_and_deduct_exceeds_per_action(self):
        """Test authorization fails when exceeding per-action limit."""
        tracker = ATPTracker()
        tracker.create_account("entity-001", 1000, 100)

        success, msg = tracker.check_and_deduct("entity-001", 150)

        assert success is False
        assert "Per-action limit exceeded" in msg
        assert tracker.get_balance("entity-001") == 1000  # No deduction

    def test_check_and_deduct_exceeds_daily(self):
        """Test authorization fails when exceeding daily limit."""
        tracker = ATPTracker()
        tracker.create_account("entity-001", 100, 50)

        # Use up budget (within per-action limit)
        tracker.check_and_deduct("entity-001", 50)
        tracker.check_and_deduct("entity-001", 50)

        # Should fail - budget exhausted
        success, msg = tracker.check_and_deduct("entity-001", 50)

        assert success is False
        assert "Daily limit exceeded" in msg

    def test_exhaustion_attack_prevention(self):
        """
        Critical security test: Prevent resource exhaustion attacks.

        An attacker with authorization should not be able to
        perform unlimited actions by bypassing ATP limits.
        """
        tracker = ATPTracker()
        tracker.create_account("attacker", 1000, 100)

        # Attacker tries to perform 50 actions (should fail after 10)
        successful_actions = 0
        for i in range(50):
            success, msg = tracker.check_and_deduct("attacker", 100)
            if success:
                successful_actions += 1

        # Should only succeed 10 times (1000 / 100)
        assert successful_actions == 10, \
            f"Expected 10 successful actions, got {successful_actions}"

        # Balance should be 0
        assert tracker.get_balance("attacker") == 0

        # Further attempts should fail
        success, msg = tracker.check_and_deduct("attacker", 50)
        assert success is False

    def test_recharge_daily(self):
        """Test daily recharge resets usage."""
        tracker = ATPTracker()
        tracker.create_account("entity-001", 1000, 100)

        # Use some ATP (within per-action limit)
        for i in range(5):
            tracker.check_and_deduct("entity-001", 100)
        assert tracker.get_balance("entity-001") == 500

        # Daily recharge
        tracker.recharge_daily()

        # Balance should be restored
        assert tracker.get_balance("entity-001") == 1000

    def test_award_atp(self):
        """Test awarding ATP for good behavior."""
        tracker = ATPTracker()
        tracker.create_account("entity-001", 1000, 100)

        # Award ATP
        tracker.award_atp("entity-001", 200, "excellent_work")

        stats = tracker.get_account_stats("entity-001")
        assert stats["total_earned"] == 200
        assert stats["daily_limit"] == 1200  # Increased

    def test_get_account_stats(self):
        """Test retrieving account statistics."""
        tracker = ATPTracker()
        tracker.create_account("entity-001", 1000, 100)
        # Use ATP (within per-action limit)
        tracker.check_and_deduct("entity-001", 100)
        tracker.check_and_deduct("entity-001", 100)
        tracker.check_and_deduct("entity-001", 50)

        stats = tracker.get_account_stats("entity-001")

        assert stats["entity_id"] == "entity-001"
        assert stats["daily_limit"] == 1000
        assert stats["per_action_limit"] == 100
        assert stats["used_today"] == 250
        assert stats["remaining_today"] == 750
        assert stats["total_spent"] == 250

    def test_persistence(self):
        """Test saving and loading from storage."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            storage_path = f.name

        try:
            # Create tracker and accounts
            tracker1 = ATPTracker(storage_path=storage_path)
            tracker1.create_account("entity-001", 1000, 100)
            tracker1.create_account("entity-002", 500, 50)
            # Use ATP (within per-action limit)
            tracker1.check_and_deduct("entity-001", 100)
            tracker1.check_and_deduct("entity-001", 100)
            tracker1.check_and_deduct("entity-001", 50)

            # Load into new tracker
            tracker2 = ATPTracker(storage_path=storage_path)

            # Verify data persisted
            assert tracker2.get_balance("entity-001") == 750
            assert tracker2.get_balance("entity-002") == 500

            stats = tracker2.get_account_stats("entity-001")
            assert stats["used_today"] == 250
            assert stats["total_spent"] == 250

        finally:
            # Cleanup
            Path(storage_path).unlink(missing_ok=True)

    def test_multiple_entities(self):
        """Test tracking multiple entities independently."""
        tracker = ATPTracker()
        tracker.create_account("entity-001", 1000, 100)
        tracker.create_account("entity-002", 500, 50)

        # Entity 1 uses ATP (within per-action limit)
        tracker.check_and_deduct("entity-001", 100)
        tracker.check_and_deduct("entity-001", 100)

        # Entity 2 should be unaffected
        assert tracker.get_balance("entity-001") == 800
        assert tracker.get_balance("entity-002") == 500

        # Entity 2 uses ATP (within per-action limit)
        tracker.check_and_deduct("entity-002", 50)
        tracker.check_and_deduct("entity-002", 50)

        # Entity 1 should be unaffected
        assert tracker.get_balance("entity-001") == 800
        assert tracker.get_balance("entity-002") == 400

    def test_get_all_accounts(self):
        """Test retrieving all account statistics."""
        tracker = ATPTracker()
        tracker.create_account("entity-001", 1000, 100)
        tracker.create_account("entity-002", 500, 50)

        all_stats = tracker.get_all_accounts()

        assert len(all_stats) == 2
        assert "entity-001" in all_stats
        assert "entity-002" in all_stats


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
