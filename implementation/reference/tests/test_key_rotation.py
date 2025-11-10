"""
Unit tests for Key Rotation Manager

Tests the critical security fix: Key rotation support for long-lived identities.

Author: Claude (Anthropic AI), autonomous security hardening
Date: November 10, 2025
"""

import pytest
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives.asymmetric import ed25519

# Import from parent directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from key_rotation import (
    KeyRotationManager,
    KeyVersion,
    KeyStatus
)


class TestKeyVersion:
    """Test KeyVersion class."""

    def test_create_key_version(self):
        """Test creating key version."""
        key = ed25519.Ed25519PrivateKey.generate()
        public_key = key.public_key()

        from cryptography.hazmat.primitives import serialization
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        key_version = KeyVersion(
            entity_id="entity-test",
            version=1,
            public_key=public_key_bytes,
            status=KeyStatus.ACTIVE
        )

        assert key_version.entity_id == "entity-test"
        assert key_version.version == 1
        assert key_version.status == KeyStatus.ACTIVE

    def test_key_validity_at_timestamp(self):
        """Test key validity checking."""
        key = ed25519.Ed25519PrivateKey.generate()
        public_key = key.public_key()

        from cryptography.hazmat.primitives import serialization
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        now = datetime.now(timezone.utc)
        future = now + timedelta(days=30)

        key_version = KeyVersion(
            entity_id="entity-test",
            version=1,
            public_key=public_key_bytes,
            status=KeyStatus.ACTIVE,
            activated_at=now.isoformat().replace('+00:00', 'Z'),
            expires_at=future.isoformat().replace('+00:00', 'Z')
        )

        # Should be valid now
        assert key_version.is_valid_at(now) is True

        # Should be valid in 15 days
        mid_point = now + timedelta(days=15)
        assert key_version.is_valid_at(mid_point) is True

        # Should be invalid after expiry
        after_expiry = future + timedelta(days=1)
        assert key_version.is_valid_at(after_expiry) is False

    def test_revoked_key_invalid(self):
        """Test revoked keys are invalid."""
        key = ed25519.Ed25519PrivateKey.generate()
        public_key = key.public_key()

        from cryptography.hazmat.primitives import serialization
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        now = datetime.now(timezone.utc)

        key_version = KeyVersion(
            entity_id="entity-test",
            version=1,
            public_key=public_key_bytes,
            status=KeyStatus.REVOKED
        )

        # Should be invalid even if within time bounds
        assert key_version.is_valid_at(now) is False


class TestKeyRotationManager:
    """Test KeyRotationManager class."""

    def test_create_manager(self):
        """Test creating manager."""
        manager = KeyRotationManager(default_overlap_days=30)
        assert manager.default_overlap_days == 30

    def test_register_initial_key(self):
        """Test registering initial key."""
        manager = KeyRotationManager()

        key = ed25519.Ed25519PrivateKey.generate()
        key_version = manager.register_initial_key("entity-alice", key)

        assert key_version.entity_id == "entity-alice"
        assert key_version.version == 1
        assert key_version.status == KeyStatus.ACTIVE

    def test_sign_and_verify(self):
        """
        Critical security test: Sign and verify with current key.

        Basic key operation must work correctly.
        """
        manager = KeyRotationManager()

        # Register key
        key = ed25519.Ed25519PrivateKey.generate()
        manager.register_initial_key("entity-alice", key)

        # Sign data
        data = b"test:delegation"
        signature, version = manager.sign_data("entity-alice", data)

        assert version == 1

        # Verify signature
        valid, msg = manager.verify_signature("entity-alice", data, signature)
        assert valid is True, "Signature verification must succeed"

    def test_rotate_key(self):
        """
        Critical security test: Key rotation.

        Entities must be able to rotate keys for security.
        """
        manager = KeyRotationManager(default_overlap_days=30)

        # Register initial key
        key1 = ed25519.Ed25519PrivateKey.generate()
        manager.register_initial_key("entity-alice", key1)

        # Rotate to new key
        key2 = ed25519.Ed25519PrivateKey.generate()
        new_version = manager.rotate_key(
            "entity-alice",
            key2,
            rotation_reason="scheduled"
        )

        assert new_version.version == 2
        assert new_version.status == KeyStatus.ACTIVE

        # Old key should be OVERLAPPING
        old_key = manager.entity_keys["entity-alice"][0]
        assert old_key.status == KeyStatus.OVERLAPPING

    def test_sign_with_new_key(self):
        """Test signing with new key after rotation."""
        manager = KeyRotationManager()

        # Register and rotate
        key1 = ed25519.Ed25519PrivateKey.generate()
        manager.register_initial_key("entity-alice", key1)

        key2 = ed25519.Ed25519PrivateKey.generate()
        manager.rotate_key("entity-alice", key2)

        # Sign with new key
        data = b"new:delegation"
        signature, version = manager.sign_data("entity-alice", data)

        assert version == 2

        # Should verify
        valid, msg = manager.verify_signature("entity-alice", data, signature)
        assert valid is True

    def test_backward_compatibility(self):
        """
        Critical security test: Backward compatibility.

        Old signatures must remain valid during overlap period.
        """
        manager = KeyRotationManager(default_overlap_days=30)

        # Register initial key
        key1 = ed25519.Ed25519PrivateKey.generate()
        manager.register_initial_key("entity-alice", key1)

        # Sign with old key and record timestamp
        data = b"old:delegation"
        signature, version = manager.sign_data("entity-alice", data)
        signature_timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        assert version == 1

        # Rotate key
        key2 = ed25519.Ed25519PrivateKey.generate()
        manager.rotate_key("entity-alice", key2)

        # Old signature should STILL be valid (backward compatibility)
        # Use the timestamp from when signature was created
        valid, msg = manager.verify_signature(
            "entity-alice", data, signature, timestamp=signature_timestamp
        )

        assert valid is True, "Old signatures must remain valid during overlap"

    def test_forward_security(self):
        """
        Critical security test: Forward security.

        Old keys cannot sign data AFTER rotation (forward security).
        """
        manager = KeyRotationManager(default_overlap_days=30)

        # Register initial key
        key1 = ed25519.Ed25519PrivateKey.generate()
        manager.register_initial_key("entity-alice", key1)

        # Rotate to new key
        key2 = ed25519.Ed25519PrivateKey.generate()
        manager.rotate_key("entity-alice", key2)

        # Current key should be v2
        current = manager.get_current_key("entity-alice")
        assert current.version == 2, "Current key must be v2 after rotation"

        # Signing uses current key only (forward security)
        data = b"future:delegation"
        signature, version = manager.sign_data("entity-alice", data)
        assert version == 2, "New signatures must use new key"

    def test_revoke_key(self):
        """
        Critical security test: Emergency key revocation.

        Compromised keys must be immediately revoked.
        """
        manager = KeyRotationManager()

        # Register key
        key = ed25519.Ed25519PrivateKey.generate()
        manager.register_initial_key("entity-alice", key)

        # Sign data
        data = b"delegation:before:compromise"
        signature, _ = manager.sign_data("entity-alice", data)

        # Verify works
        valid, _ = manager.verify_signature("entity-alice", data, signature)
        assert valid is True

        # Revoke key (compromise detected!)
        manager.revoke_key("entity-alice", version=1, reason="compromised")

        # Signature should now FAIL
        valid, msg = manager.verify_signature("entity-alice", data, signature)
        assert valid is False, "Revoked key signatures must be rejected"

    def test_get_key_at_timestamp(self):
        """Test getting key valid at specific timestamp."""
        manager = KeyRotationManager(default_overlap_days=10)

        # Register initial key
        key1 = ed25519.Ed25519PrivateKey.generate()
        manager.register_initial_key("entity-alice", key1)

        # Record time
        time1 = datetime.now(timezone.utc)

        # Wait a bit (simulate time passing)
        import time
        time.sleep(0.1)

        # Rotate key
        key2 = ed25519.Ed25519PrivateKey.generate()
        manager.rotate_key("entity-alice", key2)

        time2 = datetime.now(timezone.utc)

        # Key at time1 should be v1
        key_at_time1 = manager.get_key_at_timestamp("entity-alice", time1)
        assert key_at_time1.version == 1

        # Key at time2 should be v2
        key_at_time2 = manager.get_key_at_timestamp("entity-alice", time2)
        assert key_at_time2.version == 2

    def test_key_history(self):
        """Test key rotation history."""
        manager = KeyRotationManager()

        # Register and rotate multiple times
        key1 = ed25519.Ed25519PrivateKey.generate()
        manager.register_initial_key("entity-alice", key1)

        key2 = ed25519.Ed25519PrivateKey.generate()
        manager.rotate_key("entity-alice", key2, rotation_reason="scheduled")

        key3 = ed25519.Ed25519PrivateKey.generate()
        manager.rotate_key("entity-alice", key3, rotation_reason="compromise")

        # Get history
        history = manager.get_key_history("entity-alice")

        assert len(history) == 3
        assert history[0]["version"] == 1
        assert history[1]["version"] == 2
        assert history[1]["rotation_reason"] == "scheduled"
        assert history[2]["version"] == 3
        assert history[2]["rotation_reason"] == "compromise"

    def test_overlap_period(self):
        """Test overlap period for smooth transition."""
        manager = KeyRotationManager(default_overlap_days=30)

        # Register initial key
        key1 = ed25519.Ed25519PrivateKey.generate()
        manager.register_initial_key("entity-alice", key1)

        # Rotate key
        key2 = ed25519.Ed25519PrivateKey.generate()
        manager.rotate_key("entity-alice", key2, overlap_days=30)

        # Old key should have expiry set
        old_key = manager.entity_keys["entity-alice"][0]
        assert old_key.expires_at is not None
        assert old_key.status == KeyStatus.OVERLAPPING

        # Parse expiry
        expiry = datetime.fromisoformat(old_key.expires_at.replace('Z', '+00:00'))
        created = datetime.fromisoformat(old_key.created_at.replace('Z', '+00:00'))

        # Should be roughly 30 days (within 1 minute tolerance)
        delta = (expiry - created).total_seconds()
        expected = 30 * 24 * 3600
        assert abs(delta - expected) < 60, f"Overlap period should be ~30 days, got {delta/86400:.1f} days"

    def test_verify_with_timestamp(self):
        """Test signature verification with specific timestamp."""
        manager = KeyRotationManager()

        # Register key
        key = ed25519.Ed25519PrivateKey.generate()
        manager.register_initial_key("entity-alice", key)

        # Sign data
        data = b"timestamped:delegation"
        signature, _ = manager.sign_data("entity-alice", data)

        # Verify with explicit timestamp
        now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        valid, msg = manager.verify_signature(
            "entity-alice",
            data,
            signature,
            timestamp=now
        )

        assert valid is True

    def test_multiple_entities(self):
        """Test managing keys for multiple entities."""
        manager = KeyRotationManager()

        # Register keys for multiple entities
        alice_key = ed25519.Ed25519PrivateKey.generate()
        manager.register_initial_key("entity-alice", alice_key)

        bob_key = ed25519.Ed25519PrivateKey.generate()
        manager.register_initial_key("entity-bob", bob_key)

        # Sign with each
        alice_sig, alice_ver = manager.sign_data("entity-alice", b"alice:data")
        bob_sig, bob_ver = manager.sign_data("entity-bob", b"bob:data")

        # Verify each
        alice_valid, _ = manager.verify_signature("entity-alice", b"alice:data", alice_sig)
        bob_valid, _ = manager.verify_signature("entity-bob", b"bob:data", bob_sig)

        assert alice_valid is True
        assert bob_valid is True

    def test_serialization(self):
        """Test converting to/from dictionary."""
        manager = KeyRotationManager(default_overlap_days=45)

        # Register and rotate
        key1 = ed25519.Ed25519PrivateKey.generate()
        manager.register_initial_key("entity-alice", key1)

        key2 = ed25519.Ed25519PrivateKey.generate()
        manager.rotate_key("entity-alice", key2)

        # Serialize
        data = manager.to_dict()

        assert data["default_overlap_days"] == 45
        assert "entity-alice" in data["entity_keys"]
        assert len(data["entity_keys"]["entity-alice"]) == 2

        # Deserialize
        manager2 = KeyRotationManager.from_dict(data)

        assert manager2.default_overlap_days == 45
        assert "entity-alice" in manager2.entity_keys
        assert len(manager2.entity_keys["entity-alice"]) == 2

        # Should work the same
        current = manager2.get_current_key("entity-alice")
        assert current.version == 2

    def test_cleanup_expired_keys(self):
        """Test cleaning up old expired keys."""
        manager = KeyRotationManager()

        # Register key
        key1 = ed25519.Ed25519PrivateKey.generate()
        manager.register_initial_key("entity-alice", key1)

        # Manually expire it (simulate very old key)
        old_expiry = datetime.now(timezone.utc) - timedelta(days=100)
        manager.entity_keys["entity-alice"][0].status = KeyStatus.EXPIRED
        manager.entity_keys["entity-alice"][0].expires_at = old_expiry.isoformat().replace('+00:00', 'Z')

        # Add new key
        key2 = ed25519.Ed25519PrivateKey.generate()
        manager.rotate_key("entity-alice", key2)

        # Should have 2 keys
        assert len(manager.entity_keys["entity-alice"]) == 2

        # Cleanup (90-day grace period)
        manager.cleanup_expired_keys(grace_period_days=90)

        # Old key should be removed
        assert len(manager.entity_keys["entity-alice"]) == 1
        assert manager.entity_keys["entity-alice"][0].version == 2

    def test_no_active_key_error(self):
        """Test error when no active key available."""
        manager = KeyRotationManager()

        # Register key then revoke it
        key = ed25519.Ed25519PrivateKey.generate()
        manager.register_initial_key("entity-alice", key)
        manager.revoke_key("entity-alice", version=1, reason="compromised")

        # Should raise error when trying to sign
        with pytest.raises(ValueError):
            manager.sign_data("entity-alice", b"test")

    def test_unregistered_entity_error(self):
        """Test error for unregistered entity."""
        manager = KeyRotationManager()

        # Should raise error
        with pytest.raises(ValueError):
            key = ed25519.Ed25519PrivateKey.generate()
            manager.rotate_key("unknown-entity", key)

    def test_invalid_signature(self):
        """Test detecting invalid signatures."""
        manager = KeyRotationManager()

        # Register key
        key = ed25519.Ed25519PrivateKey.generate()
        manager.register_initial_key("entity-alice", key)

        # Sign data
        data = b"correct:data"
        signature, _ = manager.sign_data("entity-alice", data)

        # Verify with WRONG data
        wrong_data = b"wrong:data"
        valid, msg = manager.verify_signature("entity-alice", wrong_data, signature)

        assert valid is False

    def test_complex_rotation_scenario(self):
        """Test complex multi-rotation scenario."""
        manager = KeyRotationManager(default_overlap_days=30)

        # Initial key
        key1 = ed25519.Ed25519PrivateKey.generate()
        manager.register_initial_key("entity-alice", key1)

        # Sign with v1
        data1 = b"phase1:delegation"
        sig1, ver1 = manager.sign_data("entity-alice", data1)
        time1 = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        assert ver1 == 1

        # Rotate to v2
        key2 = ed25519.Ed25519PrivateKey.generate()
        manager.rotate_key("entity-alice", key2)

        # Sign with v2
        data2 = b"phase2:delegation"
        sig2, ver2 = manager.sign_data("entity-alice", data2)
        time2 = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        assert ver2 == 2

        # Rotate to v3
        key3 = ed25519.Ed25519PrivateKey.generate()
        manager.rotate_key("entity-alice", key3)

        # Sign with v3
        data3 = b"phase3:delegation"
        sig3, ver3 = manager.sign_data("entity-alice", data3)
        time3 = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        assert ver3 == 3

        # All signatures should verify with their respective timestamps
        assert manager.verify_signature("entity-alice", data1, sig1, timestamp=time1)[0] is True
        assert manager.verify_signature("entity-alice", data2, sig2, timestamp=time2)[0] is True
        assert manager.verify_signature("entity-alice", data3, sig3, timestamp=time3)[0] is True


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
