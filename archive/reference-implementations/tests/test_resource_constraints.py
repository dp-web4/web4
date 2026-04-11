"""
Unit tests for Resource Constraints

Tests the critical security fix: Fine-grained resource constraints
that enable least-privilege authorization.

Author: Claude (Anthropic AI), autonomous security hardening
Date: November 9, 2025
"""

import pytest

# Import from parent directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from resource_constraints import ResourceConstraints, ResourcePattern, PermissionLevel


class TestResourcePattern:
    """Test ResourcePattern class."""

    def test_exact_pattern_match(self):
        """Test exact pattern matching."""
        pattern = ResourcePattern("github:dp-web4/web4/issues")

        assert pattern.matches("github:dp-web4/web4/issues") is True
        assert pattern.matches("github:dp-web4/web4/discussions") is False

    def test_prefix_pattern_match(self):
        """Test prefix pattern matching."""
        pattern = ResourcePattern("github:dp-web4/web4")

        # Should match children
        assert pattern.matches("github:dp-web4/web4/issues") is True
        assert pattern.matches("github:dp-web4/web4/discussions/42") is True

        # Should not match unrelated
        assert pattern.matches("github:other-org/repo") is False

    def test_glob_pattern(self):
        """Test glob pattern matching."""
        pattern = ResourcePattern("github:*/web4/issues")

        assert pattern.is_glob is True
        assert pattern.matches("github:dp-web4/web4/issues") is True
        assert pattern.matches("github:other-org/web4/issues") is True
        assert pattern.matches("github:dp-web4/other-repo/issues") is False


class TestResourceConstraints:
    """Test ResourceConstraints class."""

    def test_create_constraints(self):
        """Test creating constraints."""
        constraints = ResourceConstraints()

        assert constraints.has_constraints() is False
        assert len(constraints.get_allowed_resources()) == 0

    def test_add_allowed(self):
        """Test adding allowed resources."""
        constraints = ResourceConstraints()

        constraints.add_allowed("resource-a")
        constraints.add_allowed("resource-b")

        allowed = constraints.get_allowed_resources()
        assert len(allowed) == 2
        assert "resource-a" in allowed
        assert "resource-b" in allowed

    def test_whitelist_authorization(self):
        """Test whitelist-based authorization."""
        constraints = ResourceConstraints()

        # Add specific resources to whitelist
        constraints.add_allowed("github:dp-web4/web4/discussions")
        constraints.add_allowed("github:dp-web4/web4/issues")

        # Should authorize whitelisted resources
        authorized, _ = constraints.is_authorized("github:dp-web4/web4/discussions")
        assert authorized is True

        authorized, _ = constraints.is_authorized("github:dp-web4/web4/issues")
        assert authorized is True

        # Should deny non-whitelisted resources
        authorized, _ = constraints.is_authorized("twitter:@web4")
        assert authorized is False

    def test_least_privilege_principle(self):
        """
        Critical security test: Enforce least-privilege.

        Previously delegation scope was too broad (e.g., "public_outreach"
        meant ALL public channels). Now can restrict to specific resources.
        """
        constraints = ResourceConstraints()

        # Delegate ONLY GitHub access (not Twitter, Reddit, etc.)
        constraints.add_allowed("github:dp-web4/web4/*")

        # Should authorize GitHub
        authorized, _ = constraints.is_authorized("github:dp-web4/web4/issues")
        assert authorized is True, "GitHub should be authorized"

        # Should DENY other platforms
        authorized, _ = constraints.is_authorized("twitter:@web4")
        assert authorized is False, "Twitter should be denied (least privilege)"

        authorized, _ = constraints.is_authorized("reddit:r/web4")
        assert authorized is False, "Reddit should be denied (least privilege)"

    def test_glob_patterns(self):
        """Test glob pattern matching."""
        constraints = ResourceConstraints()

        # Allow all issues across repos
        constraints.add_allowed("github:dp-web4/*/issues")

        # Should match
        authorized, _ = constraints.is_authorized("github:dp-web4/web4/issues")
        assert authorized is True

        authorized, _ = constraints.is_authorized("github:dp-web4/other-repo/issues")
        assert authorized is True

        # Should not match
        authorized, _ = constraints.is_authorized("github:dp-web4/web4/discussions")
        assert authorized is False

    def test_blacklist_takes_precedence(self):
        """Test that denied patterns override allowed patterns."""
        constraints = ResourceConstraints()

        # Allow all GitHub
        constraints.add_allowed("github:*")

        # But deny settings
        constraints.add_denied("github:*/settings")

        # Should authorize normal resources
        authorized, _ = constraints.is_authorized("github:dp-web4/web4/issues")
        assert authorized is True

        # Should DENY settings (blacklist takes precedence)
        authorized, _ = constraints.is_authorized("github:dp-web4/web4/settings")
        assert authorized is False

    def test_empty_whitelist_denies_all(self):
        """Test that empty whitelist denies everything (secure default)."""
        constraints = ResourceConstraints()

        # No allowed patterns configured
        assert constraints.has_constraints() is False

        # Should deny everything
        authorized, msg = constraints.is_authorized("any-resource")
        assert authorized is False
        assert "whitelist empty" in msg.lower() or "no allowed" in msg.lower()

    def test_permission_levels(self):
        """Test permission level hierarchy."""
        constraints = ResourceConstraints()

        # Different permission levels
        constraints.add_allowed("resource-read", PermissionLevel.READ)
        constraints.add_allowed("resource-write", PermissionLevel.WRITE)
        constraints.add_allowed("resource-admin", PermissionLevel.ADMIN)

        # READ permission: can only read
        authorized, _ = constraints.is_authorized("resource-read", PermissionLevel.READ)
        assert authorized is True

        authorized, _ = constraints.is_authorized("resource-read", PermissionLevel.WRITE)
        assert authorized is False

        # WRITE permission: can read and write
        authorized, _ = constraints.is_authorized("resource-write", PermissionLevel.READ)
        assert authorized is True

        authorized, _ = constraints.is_authorized("resource-write", PermissionLevel.WRITE)
        assert authorized is True

        authorized, _ = constraints.is_authorized("resource-write", PermissionLevel.ADMIN)
        assert authorized is False

        # ADMIN permission: can do everything
        authorized, _ = constraints.is_authorized("resource-admin", PermissionLevel.READ)
        assert authorized is True

        authorized, _ = constraints.is_authorized("resource-admin", PermissionLevel.WRITE)
        assert authorized is True

        authorized, _ = constraints.is_authorized("resource-admin", PermissionLevel.ADMIN)
        assert authorized is True

    def test_serialization(self):
        """Test converting to/from dictionary."""
        constraints = ResourceConstraints()

        constraints.add_allowed("resource-a", PermissionLevel.WRITE)
        constraints.add_allowed("resource-b", PermissionLevel.READ)
        constraints.add_denied("resource-c")

        # Serialize
        data = constraints.to_dict()

        assert len(data["allowed"]) == 2
        assert len(data["denied"]) == 1

        # Deserialize
        constraints2 = ResourceConstraints.from_dict(data)

        assert len(constraints2.get_allowed_resources()) == 2
        assert len(constraints2.get_denied_resources()) == 1

        # Should have same authorization behavior
        authorized1, _ = constraints.is_authorized("resource-a")
        authorized2, _ = constraints2.is_authorized("resource-a")
        assert authorized1 == authorized2

    def test_complex_scenario(self):
        """Test complex real-world scenario."""
        constraints = ResourceConstraints()

        # Allow GitHub repos
        constraints.add_allowed("github:dp-web4/web4/*")
        constraints.add_allowed("github:dp-web4/private-context/*")

        # But deny sensitive paths
        constraints.add_denied("github:*/settings")
        constraints.add_denied("github:*/secrets")

        test_cases = [
            ("github:dp-web4/web4/issues", True),
            ("github:dp-web4/web4/discussions", True),
            ("github:dp-web4/private-context/moments", True),
            ("github:dp-web4/web4/settings", False),  # Denied
            ("github:dp-web4/private-context/secrets", False),  # Denied
            ("github:other-org/repo", False),  # Not in whitelist
        ]

        for resource, expected in test_cases:
            authorized, _ = constraints.is_authorized(resource)
            assert authorized == expected, f"Failed for {resource}"


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
