"""
Unit tests for Nonce Tracker

Tests the critical security fix: Replay attack prevention
that was previously missing from the LCT identity system.

Author: Claude (Anthropic AI), autonomous security hardening
Date: November 9, 2025
"""

import pytest
import time

# Import from parent directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nonce_tracker import NonceTracker, NonceEntry


class TestNonceEntry:
    """Test NonceEntry data class."""

    def test_entry_creation(self):
        """Test creating a nonce entry."""
        entry = NonceEntry(
            nonce="test-nonce-123",
            entity_id="entity-001",
            created_at=time.time(),
            expires_at=time.time() + 300
        )

        assert entry.nonce == "test-nonce-123"
        assert entry.entity_id == "entity-001"
        assert not entry.consumed


class TestNonceTracker:
    """Test NonceTracker class."""

    def test_create_tracker(self):
        """Test creating tracker."""
        tracker = NonceTracker(max_age_seconds=300)

        assert tracker.max_age_seconds == 300
        stats = tracker.get_stats()
        assert stats["total_nonces"] == 0

    def test_generate_nonce(self):
        """Test nonce generation."""
        tracker = NonceTracker()

        nonce = tracker.generate_nonce("entity-001")

        # Nonce should be non-empty string
        assert nonce
        assert isinstance(nonce, str)
        assert len(nonce) > 20  # URL-safe base64 of 32 bytes

    def test_nonces_are_unique(self):
        """Test that generated nonces are unique."""
        tracker = NonceTracker()

        nonces = set()
        for i in range(100):
            nonce = tracker.generate_nonce("entity-001")
            nonces.add(nonce)

        # All nonces should be unique
        assert len(nonces) == 100

    def test_verify_and_consume_success(self):
        """Test successful nonce verification."""
        tracker = NonceTracker()

        nonce = tracker.generate_nonce("entity-001")

        # First use should succeed
        valid, msg = tracker.verify_and_consume("entity-001", nonce)

        assert valid is True
        assert "valid" in msg.lower()

    def test_replay_attack_prevented(self):
        """
        Critical security test: Prevent replay attacks.

        An attacker intercepts a valid authorization request and
        tries to replay it. The nonce system should detect and block this.
        """
        tracker = NonceTracker()

        # Legitimate user generates nonce and makes request
        nonce = tracker.generate_nonce("entity-001")

        # First use: succeeds
        valid1, msg1 = tracker.verify_and_consume("entity-001", nonce)
        assert valid1 is True

        # Attacker intercepts and tries to replay
        valid2, msg2 = tracker.verify_and_consume("entity-001", nonce)

        # Should be BLOCKED
        assert valid2 is False, "Replay attack must be prevented"
        assert "already used" in msg2.lower() or "replay" in msg2.lower()

    def test_unknown_nonce_rejected(self):
        """Test that unknown nonces are rejected."""
        tracker = NonceTracker()

        # Try to use nonce that was never generated
        valid, msg = tracker.verify_and_consume("entity-001", "fake-nonce-123")

        assert valid is False
        assert "not found" in msg.lower()

    def test_wrong_entity_rejected(self):
        """Test that nonce cannot be used by different entity."""
        tracker = NonceTracker()

        # Entity 1 generates nonce
        nonce = tracker.generate_nonce("entity-001")

        # Entity 2 tries to use it
        valid, msg = tracker.verify_and_consume("entity-002", nonce)

        # Should be rejected
        assert valid is False
        assert "entity-001" in msg  # Should mention correct entity

    def test_expired_nonce_rejected(self):
        """Test that expired nonces are rejected."""
        tracker = NonceTracker(max_age_seconds=1)  # 1 second expiry

        nonce = tracker.generate_nonce("entity-001")

        # Wait for expiry
        time.sleep(1.1)

        # Try to use expired nonce
        valid, msg = tracker.verify_and_consume("entity-001", nonce)

        # Should be rejected
        assert valid is False
        assert "expired" in msg.lower()

    def test_is_valid_check(self):
        """Test read-only validation."""
        tracker = NonceTracker()

        nonce = tracker.generate_nonce("entity-001")

        # Should be valid before consumption
        assert tracker.is_valid("entity-001", nonce) is True

        # Consume it
        tracker.verify_and_consume("entity-001", nonce)

        # Should not be valid after consumption
        assert tracker.is_valid("entity-001", nonce) is False

    def test_cleanup_expired(self):
        """Test cleanup of expired nonces."""
        tracker = NonceTracker(max_age_seconds=1)

        # Generate some nonces
        tracker.generate_nonce("entity-001")
        tracker.generate_nonce("entity-002")

        # Wait for expiry
        time.sleep(1.1)

        # Generate fresh nonce
        tracker.generate_nonce("entity-003")

        # Cleanup
        cleaned = tracker.cleanup_expired()

        # Should have cleaned up 2 expired nonces
        assert cleaned == 2

        stats = tracker.get_stats()
        assert stats["total_nonces"] == 1  # Only fresh one remains

    def test_cleanup_consumed(self):
        """Test cleanup of old consumed nonces."""
        tracker = NonceTracker()

        nonce1 = tracker.generate_nonce("entity-001")
        nonce2 = tracker.generate_nonce("entity-002")

        # Consume first nonce
        tracker.verify_and_consume("entity-001", nonce1)

        # Cleanup with very short min age (so it gets removed)
        time.sleep(0.1)
        cleaned = tracker.cleanup_consumed(min_age_seconds=0)

        # Should have cleaned up 1 consumed nonce
        assert cleaned == 1

        # Second nonce should still exist (not consumed)
        stats = tracker.get_stats()
        assert stats["total_nonces"] == 1

    def test_get_entity_nonces(self):
        """Test retrieving nonces by entity."""
        tracker = NonceTracker()

        nonce1 = tracker.generate_nonce("entity-001")
        nonce2 = tracker.generate_nonce("entity-001")
        nonce3 = tracker.generate_nonce("entity-002")

        # Entity 1 should have 2 nonces
        entity1_nonces = tracker.get_entity_nonces("entity-001")
        assert len(entity1_nonces) == 2
        assert nonce1 in entity1_nonces
        assert nonce2 in entity1_nonces

        # Entity 2 should have 1 nonce
        entity2_nonces = tracker.get_entity_nonces("entity-002")
        assert len(entity2_nonces) == 1
        assert nonce3 in entity2_nonces

    def test_get_stats(self):
        """Test statistics generation."""
        tracker = NonceTracker()

        # Generate and consume some nonces
        nonce1 = tracker.generate_nonce("entity-001")
        nonce2 = tracker.generate_nonce("entity-001")
        tracker.generate_nonce("entity-002")

        tracker.verify_and_consume("entity-001", nonce1)

        stats = tracker.get_stats()

        assert stats["total_nonces"] == 3
        assert stats["consumed"] == 1
        assert stats["entities"] == 2
        assert stats["by_entity"]["entity-001"] == 2
        assert stats["by_entity"]["entity-002"] == 1

    def test_revoke_entity_nonces(self):
        """Test emergency revocation of all entity nonces."""
        tracker = NonceTracker()

        # Generate nonces for entity
        nonce1 = tracker.generate_nonce("entity-001")
        nonce2 = tracker.generate_nonce("entity-001")
        tracker.generate_nonce("entity-002")

        # Emergency revoke entity-001
        revoked = tracker.revoke_entity_nonces("entity-001")

        # Should have revoked 2 nonces
        assert revoked == 2

        # Entity-001 nonces should be invalid
        assert not tracker.is_valid("entity-001", nonce1)
        assert not tracker.is_valid("entity-001", nonce2)

        # Entity-002 should be unaffected
        stats = tracker.get_stats()
        assert stats["total_nonces"] == 1

    def test_multiple_entities_isolated(self):
        """Test that entity nonces are isolated."""
        tracker = NonceTracker()

        # Generate nonces for different entities
        nonce1 = tracker.generate_nonce("entity-001")
        nonce2 = tracker.generate_nonce("entity-002")

        # Entity 1 consumes their nonce
        valid, _ = tracker.verify_and_consume("entity-001", nonce1)
        assert valid is True

        # Entity 2's nonce should still be valid
        assert tracker.is_valid("entity-002", nonce2) is True

        # Entity 2 can consume their nonce
        valid, _ = tracker.verify_and_consume("entity-002", nonce2)
        assert valid is True

    def test_timing_window(self):
        """Test nonce timing window."""
        tracker = NonceTracker(max_age_seconds=2)

        nonce = tracker.generate_nonce("entity-001")

        # Should be valid immediately
        assert tracker.is_valid("entity-001", nonce) is True

        # Should be valid after 1 second
        time.sleep(1)
        assert tracker.is_valid("entity-001", nonce) is True

        # Should be invalid after 2+ seconds
        time.sleep(1.1)
        assert tracker.is_valid("entity-001", nonce) is False

    def test_high_volume_nonces(self):
        """Test tracker handles high volume of nonces."""
        tracker = NonceTracker()

        # Generate many nonces
        nonces = []
        for i in range(1000):
            nonce = tracker.generate_nonce(f"entity-{i % 10}")
            nonces.append(nonce)

        # All should be unique
        assert len(set(nonces)) == 1000

        # Stats should be correct
        stats = tracker.get_stats()
        assert stats["total_nonces"] == 1000
        assert stats["entities"] == 10


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
