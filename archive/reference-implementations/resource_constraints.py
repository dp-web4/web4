"""
Resource Constraints for Fine-Grained Authorization

Implements fine-grained resource constraints for Web4 delegations.

Key Features:
- Resource-specific authorization (not just broad scopes)
- Whitelist/blacklist patterns for resources
- Glob pattern matching for flexibility
- Per-resource permission levels
- Constraint validation and enforcement

Fixes Critical Vulnerability #7:
- Previously delegation scopes too broad
- Could not implement least-privilege principle
- "public_outreach" meant ALL public channels
- No way to restrict to specific resources
- This implementation enables fine-grained control

Usage:
    constraints = ResourceConstraints()

    # Add allowed resources
    constraints.add_allowed("github:dp-web4/web4/discussions")
    constraints.add_allowed("github:dp-web4/web4/issues")

    # Check if resource is authorized
    if constraints.is_authorized("github:dp-web4/web4/discussions/42"):
        allow_action()
    else:
        deny_action()

Author: Claude (Anthropic AI), autonomous security hardening
Date: November 9, 2025
"""

import re
import fnmatch
import logging
from typing import List, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """Permission levels for resources."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


@dataclass
class ResourcePattern:
    """Resource pattern (whitelist or blacklist)."""
    pattern: str
    permission_level: PermissionLevel = PermissionLevel.WRITE
    is_glob: bool = False  # True if pattern contains wildcards

    def __post_init__(self):
        # Detect if pattern is glob (contains * or ?)
        self.is_glob = '*' in self.pattern or '?' in self.pattern

    def matches(self, resource_id: str) -> bool:
        """Check if resource matches this pattern."""
        if self.is_glob:
            # Use fnmatch for glob patterns
            return fnmatch.fnmatch(resource_id, self.pattern)
        else:
            # Exact match or prefix match
            return (
                resource_id == self.pattern or
                resource_id.startswith(self.pattern + '/')
            )


class ResourceConstraints:
    """
    Fine-grained resource constraints for delegations.

    Implements least-privilege principle by restricting
    authorization to specific resources within a scope.
    """

    def __init__(self):
        """Initialize resource constraints."""
        self.allowed_patterns: List[ResourcePattern] = []
        self.denied_patterns: List[ResourcePattern] = []

        logger.debug("ResourceConstraints initialized")

    def add_allowed(
        self,
        pattern: str,
        permission_level: PermissionLevel = PermissionLevel.WRITE
    ):
        """
        Add allowed resource pattern.

        Args:
            pattern: Resource pattern (supports wildcards: * and ?)
            permission_level: Permission level for this resource
        """
        resource_pattern = ResourcePattern(
            pattern=pattern,
            permission_level=permission_level
        )

        self.allowed_patterns.append(resource_pattern)

        logger.debug(
            f"Added allowed pattern: {pattern} ({permission_level.value})"
        )

    def add_denied(
        self,
        pattern: str
    ):
        """
        Add denied resource pattern (blacklist).

        Denied patterns take precedence over allowed patterns.

        Args:
            pattern: Resource pattern to deny (supports wildcards)
        """
        resource_pattern = ResourcePattern(
            pattern=pattern,
            permission_level=PermissionLevel.READ  # Doesn't matter for deny
        )

        self.denied_patterns.append(resource_pattern)

        logger.debug(f"Added denied pattern: {pattern}")

    def is_authorized(
        self,
        resource_id: str,
        required_permission: PermissionLevel = PermissionLevel.WRITE
    ) -> Tuple[bool, str]:
        """
        Check if resource is authorized.

        Args:
            resource_id: Resource identifier to check
            required_permission: Required permission level

        Returns:
            Tuple of (authorized: bool, reason: str)
        """
        # Check denied patterns first (blacklist takes precedence)
        for pattern in self.denied_patterns:
            if pattern.matches(resource_id):
                logger.warning(
                    f"Resource DENIED by blacklist: {resource_id} "
                    f"(pattern: {pattern.pattern})"
                )
                return False, f"Resource denied by pattern: {pattern.pattern}"

        # If no allowed patterns, deny by default (whitelist-only mode)
        if not self.allowed_patterns:
            logger.warning(
                f"Resource DENIED (no whitelist): {resource_id}"
            )
            return False, "No allowed resources configured (whitelist empty)"

        # Check allowed patterns
        for pattern in self.allowed_patterns:
            if pattern.matches(resource_id):
                # Check permission level
                if self._has_permission(pattern.permission_level, required_permission):
                    logger.debug(
                        f"✅ Resource AUTHORIZED: {resource_id} "
                        f"(pattern: {pattern.pattern}, "
                        f"level: {pattern.permission_level.value})"
                    )
                    return True, f"Authorized by pattern: {pattern.pattern}"
                else:
                    logger.warning(
                        f"Resource DENIED (insufficient permission): {resource_id} "
                        f"(has: {pattern.permission_level.value}, "
                        f"needs: {required_permission.value})"
                    )
                    return False, (
                        f"Insufficient permission: has {pattern.permission_level.value}, "
                        f"needs {required_permission.value}"
                    )

        # No pattern matched
        logger.warning(
            f"Resource DENIED (no pattern match): {resource_id}"
        )
        return False, "Resource not in allowed list"

    def _has_permission(
        self,
        granted: PermissionLevel,
        required: PermissionLevel
    ) -> bool:
        """
        Check if granted permission satisfies required permission.

        Permission hierarchy: ADMIN > WRITE > READ
        """
        hierarchy = {
            PermissionLevel.READ: 1,
            PermissionLevel.WRITE: 2,
            PermissionLevel.ADMIN: 3
        }

        return hierarchy[granted] >= hierarchy[required]

    def get_allowed_resources(self) -> List[str]:
        """Get list of allowed resource patterns."""
        return [p.pattern for p in self.allowed_patterns]

    def get_denied_resources(self) -> List[str]:
        """Get list of denied resource patterns."""
        return [p.pattern for p in self.denied_patterns]

    def has_constraints(self) -> bool:
        """Check if any constraints are configured."""
        return len(self.allowed_patterns) > 0 or len(self.denied_patterns) > 0

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "allowed": [
                {
                    "pattern": p.pattern,
                    "permission": p.permission_level.value
                }
                for p in self.allowed_patterns
            ],
            "denied": [p.pattern for p in self.denied_patterns]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ResourceConstraints':
        """Create from dictionary."""
        constraints = cls()

        for allowed in data.get("allowed", []):
            constraints.add_allowed(
                allowed["pattern"],
                PermissionLevel(allowed.get("permission", "write"))
            )

        for denied in data.get("denied", []):
            constraints.add_denied(denied)

        return constraints


# Example usage
if __name__ == "__main__":
    print("Resource Constraints - Example Usage\n" + "="*60)

    # Create constraints
    print("\n1. Creating resource constraints...")
    constraints = ResourceConstraints()

    # Add allowed resources (GitHub only)
    print("\n2. Adding allowed resources (GitHub only)...")
    constraints.add_allowed("github:dp-web4/web4/discussions")
    constraints.add_allowed("github:dp-web4/web4/issues")

    print(f"  Allowed: {constraints.get_allowed_resources()}")

    # Test authorization
    print("\n3. Testing authorization...")

    test_resources = [
        ("github:dp-web4/web4/discussions/1", PermissionLevel.WRITE),
        ("github:dp-web4/web4/issues/42", PermissionLevel.WRITE),
        ("twitter:@web4_project", PermissionLevel.WRITE),
        ("reddit:r/web4", PermissionLevel.WRITE),
    ]

    for resource, permission in test_resources:
        authorized, reason = constraints.is_authorized(resource, permission)
        status = "✅ ALLOW" if authorized else "❌ DENY"
        print(f"  {status}: {resource}")
        print(f"    Reason: {reason}")

    # Test glob patterns
    print("\n4. Testing glob patterns...")
    constraints2 = ResourceConstraints()
    constraints2.add_allowed("github:dp-web4/*/issues")  # All repos issues
    constraints2.add_allowed("github:dp-web4/web4/*")     # All web4 resources

    test_globs = [
        "github:dp-web4/web4/discussions",
        "github:dp-web4/another-repo/issues",
        "github:other-org/repo/issues",
    ]

    for resource in test_globs:
        authorized, reason = constraints2.is_authorized(resource)
        status = "✅ ALLOW" if authorized else "❌ DENY"
        print(f"  {status}: {resource}")

    # Test blacklist
    print("\n5. Testing blacklist (denied patterns)...")
    constraints3 = ResourceConstraints()
    constraints3.add_allowed("github:*")  # Allow all GitHub
    constraints3.add_denied("github:*/settings")  # But deny settings

    test_blacklist = [
        "github:dp-web4/web4/issues",
        "github:dp-web4/web4/settings",
        "github:any-org/any-repo/settings",
    ]

    for resource in test_blacklist:
        authorized, reason = constraints3.is_authorized(resource)
        status = "✅ ALLOW" if authorized else "❌ DENY"
        print(f"  {status}: {resource}")

    # Test permission levels
    print("\n6. Testing permission levels...")
    constraints4 = ResourceConstraints()
    constraints4.add_allowed("resource-a", PermissionLevel.READ)
    constraints4.add_allowed("resource-b", PermissionLevel.WRITE)
    constraints4.add_allowed("resource-c", PermissionLevel.ADMIN)

    test_permissions = [
        ("resource-a", PermissionLevel.READ, True),   # READ on READ = OK
        ("resource-a", PermissionLevel.WRITE, False), # WRITE on READ = DENY
        ("resource-b", PermissionLevel.READ, True),   # READ on WRITE = OK
        ("resource-b", PermissionLevel.WRITE, True),  # WRITE on WRITE = OK
        ("resource-c", PermissionLevel.ADMIN, True),  # ADMIN on ADMIN = OK
    ]

    for resource, required, expected in test_permissions:
        authorized, reason = constraints4.is_authorized(resource, required)
        status = "✅" if authorized == expected else "❌"
        print(f"  {status} {resource} (required: {required.value}, result: {authorized})")

    print("\n" + "="*60)
    print("✅ Resource Constraints operational - Least-privilege enabled!")
    print("="*60)
    print("\nKey capabilities:")
    print("- Fine-grained resource control (not just broad scopes)")
    print("- Glob pattern matching for flexibility")
    print("- Blacklist support (denied patterns)")
    print("- Permission level hierarchy (READ < WRITE < ADMIN)")
