"""
Unit tests for Revocation Registry

Tests the critical security fix: Delegation revocation mechanism
that was previously missing from the LCT identity system.

Author: Claude (Anthropic AI), autonomous security hardening
Date: November 9, 2025
"""

import pytest
import tempfile
from pathlib import Path

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from revocation_registry import RevocationRegistry, RevocationEntry
from lct_identity import (
    create_dennis_lct_example,
    create_claude_lct_and_delegation_example,
    Delegation,
    DelegationScope
)


class TestRevocationEntry:
    """Test RevocationEntry data class."""

    def test_entry_creation(self):
        """Test creating a revocation entry."""
        entry = RevocationEntry(
            delegation_hash="abc123",
            delegator="dennis-001",
            delegatee="claude-001",
            reason="test_revocation"
        )

        assert entry.delegation_hash == "abc123"
        assert entry.delegator == "dennis-001"
        assert entry.delegatee == "claude-001"
        assert entry.reason == "test_revocation"
        assert entry.revoked_at  # Should be auto-generated

    def test_entry_to_json(self):
        """Test JSON serialization."""
        entry = RevocationEntry(
            delegation_hash="abc123",
            delegator="dennis-001",
            delegatee="claude-001",
            reason="test"
        )

        json_str = entry.to_json()
        assert "abc123" in json_str
        assert "dennis-001" in json_str
        assert "claude-001" in json_str


class TestRevocationRegistry:
    """Test RevocationRegistry class."""

    def setup_method(self):
        """Setup test fixtures (run before each test)."""
        # Create test identities and delegation
        self.dennis_private, self.dennis_public, self.dennis_lct = \
            create_dennis_lct_example()

        self.claude_private, self.claude_public, self.claude_lct, self.delegation = \
            create_claude_lct_and_delegation_example(
                self.dennis_private,
                self.dennis_public,
                self.dennis_lct
            )

    def test_create_registry(self):
        """Test creating empty registry."""
        registry = RevocationRegistry()

        assert registry.get_revocation_count() == 0
        assert not registry.is_revoked(self.delegation)

    def test_revoke_delegation(self):
        """Test revoking a delegation."""
        registry = RevocationRegistry()

        # Initially not revoked
        assert not registry.is_revoked(self.delegation)

        # Revoke it
        revocation = registry.revoke_delegation(
            delegation=self.delegation,
            delegator_private_key=self.dennis_private,
            reason="test_revocation"
        )

        # Should be revoked now
        assert registry.is_revoked(self.delegation)
        assert revocation.delegatee == "claude-anthropic-instance-001"
        assert revocation.reason == "test_revocation"

    def test_revoke_prevents_reuse(self):
        """
        Critical security test: Revoked delegation cannot be reused.

        This tests the core security fix - compromised credentials
        can be immediately invalidated.
        """
        registry = RevocationRegistry()

        # Delegation starts valid
        assert not registry.is_revoked(self.delegation)

        # Simulate: delegation gets compromised, Dennis revokes it
        registry.revoke_delegation(
            delegation=self.delegation,
            delegator_private_key=self.dennis_private,
            reason="security_incident"
        )

        # Attacker tries to use revoked delegation
        is_revoked = registry.is_revoked(self.delegation)

        # Should be blocked
        assert is_revoked, "Revoked delegation must not be usable"

    def test_cannot_revoke_unsigned_delegation(self):
        """Test that unsigned delegations cannot be revoked."""
        registry = RevocationRegistry()

        # Create unsigned delegation
        unsigned = Delegation(
            delegator="dennis-001",
            delegatee="claude-001",
            scope=[DelegationScope.PUBLIC_OUTREACH]
        )

        # Should raise error
        with pytest.raises(ValueError, match="unsigned"):
            registry.revoke_delegation(
                delegation=unsigned,
                delegator_private_key=self.dennis_private,
                reason="test"
            )

    def test_revoke_idempotent(self):
        """Test that revoking same delegation twice is safe."""
        registry = RevocationRegistry()

        # Revoke once
        revocation1 = registry.revoke_delegation(
            delegation=self.delegation,
            delegator_private_key=self.dennis_private,
            reason="first"
        )

        # Revoke again (should not fail)
        revocation2 = registry.revoke_delegation(
            delegation=self.delegation,
            delegator_private_key=self.dennis_private,
            reason="second"
        )

        # Should still be revoked, but only one entry
        assert registry.is_revoked(self.delegation)
        assert registry.get_revocation_count() == 1

        # First revocation should be preserved (not overwritten)
        info = registry.get_revocation_info(self.delegation)
        assert info.reason == "first"  # Original reason preserved

    def test_get_revocation_info(self):
        """Test retrieving revocation details."""
        registry = RevocationRegistry()

        # No info initially
        info = registry.get_revocation_info(self.delegation)
        assert info is None

        # Revoke
        registry.revoke_delegation(
            delegation=self.delegation,
            delegator_private_key=self.dennis_private,
            reason="test_reason",
            metadata={"incident_id": "IR-001"}
        )

        # Info should be available
        info = registry.get_revocation_info(self.delegation)
        assert info is not None
        assert info.reason == "test_reason"
        assert info.metadata["incident_id"] == "IR-001"

    def test_verify_revocation_signature(self):
        """Test verifying revocation signatures."""
        registry = RevocationRegistry()

        # Revoke delegation
        revocation = registry.revoke_delegation(
            delegation=self.delegation,
            delegator_private_key=self.dennis_private,
            reason="test"
        )

        # Verify with correct key
        is_valid = registry.verify_revocation_signature(
            revocation,
            self.dennis_public
        )
        assert is_valid

        # Verify with wrong key (Claude's key instead of Dennis's)
        is_invalid = registry.verify_revocation_signature(
            revocation,
            self.claude_public  # Wrong key!
        )
        assert not is_invalid, "Revocation should not verify with wrong key"

    def test_list_revocations(self):
        """Test listing revocations with filters."""
        registry = RevocationRegistry()

        # Create multiple revocations
        registry.revoke_delegation(
            self.delegation,
            self.dennis_private,
            reason="reason_a"
        )

        # List all
        all_revocations = registry.list_revocations()
        assert len(all_revocations) == 1

        # List by delegatee
        by_delegatee = registry.list_revocations(
            delegatee="claude-anthropic-instance-001"
        )
        assert len(by_delegatee) == 1

        # List by reason
        by_reason = registry.list_revocations(reason="reason_a")
        assert len(by_reason) == 1

        by_wrong_reason = registry.list_revocations(reason="nonexistent")
        assert len(by_wrong_reason) == 0

    def test_get_stats(self):
        """Test revocation statistics."""
        registry = RevocationRegistry()

        # Revoke delegation
        registry.revoke_delegation(
            self.delegation,
            self.dennis_private,
            reason="security_incident"
        )

        stats = registry.get_stats()

        assert stats["total_revocations"] == 1
        assert stats["by_reason"]["security_incident"] == 1
        assert stats["by_delegator"]["dennis-palatov"] == 1
        assert stats["by_delegatee"]["claude-anthropic-instance-001"] == 1

    def test_persistence(self):
        """Test saving and loading from storage."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            storage_path = f.name

        try:
            # Create registry and revoke delegation
            registry1 = RevocationRegistry(storage_path=storage_path)
            registry1.revoke_delegation(
                self.delegation,
                self.dennis_private,
                reason="test_persistence"
            )

            # Load into new registry
            registry2 = RevocationRegistry(storage_path=storage_path)

            # Verify data persisted
            assert registry2.is_revoked(self.delegation)
            assert registry2.get_revocation_count() == 1

            info = registry2.get_revocation_info(self.delegation)
            assert info.reason == "test_persistence"

        finally:
            # Cleanup
            Path(storage_path).unlink(missing_ok=True)

    def test_multiple_revocations(self):
        """Test tracking multiple independent revocations."""
        registry = RevocationRegistry()

        # Revoke first delegation
        registry.revoke_delegation(
            self.delegation,
            self.dennis_private,
            reason="first"
        )

        # Delegation should be revoked
        assert registry.is_revoked(self.delegation)
        assert registry.get_revocation_count() == 1

    def test_reason_codes(self):
        """Test different revocation reasons."""
        registry = RevocationRegistry()

        reasons = [
            "security_incident",
            "contract_ended",
            "policy_violation",
            "key_compromised",
            "scope_change_required"
        ]

        for reason in reasons:
            # Create new delegation for each test
            _, _, _, new_delegation = create_claude_lct_and_delegation_example(
                self.dennis_private,
                self.dennis_public,
                self.dennis_lct
            )

            registry.revoke_delegation(
                new_delegation,
                self.dennis_private,
                reason=reason
            )

        stats = registry.get_stats()
        assert stats["total_revocations"] == 5

        for reason in reasons:
            assert reason in stats["by_reason"]


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
