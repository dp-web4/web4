"""
Web4 Authorization System - Permission Claims
==============================================

Cryptographically signed permission grants for LCT-based authorization.

Based on: WEB4-AUTH-001 proposal (Session #21)
Author: Web4 Authorization Implementation (Session #22)
License: MIT
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum
import hashlib
import json


class PermissionStatus(str, Enum):
    """Status of a permission claim"""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass
class PermissionClaim:
    """
    Cryptographically signed permission grant.

    A PermissionClaim represents a single permission granted to an agent (subject)
    by an authority (issuer) within an organization context.

    Format: <action>:<resource>:<scope>
    Examples:
        - "read:code" - Read any code
        - "write:code:own" - Write own code only
        - "execute:deploy:staging" - Deploy to staging
        - "witness:lct:ai" - Witness AI LCT creation
        - "admin:org:acme" - Admin rights in acme org
    """

    # Required fields (no defaults)
    subject_lct: str  # Who is granted permission
    permission: str  # What permission (action)
    issuer_lct: str  # Who grants permission
    organization: str  # Organization context

    # Optional fields (with defaults)
    resource: str = "*"  # Specific resource or "*" for all
    scope: Optional[str] = None  # Optional scope restriction

    # When is it valid
    issued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None  # None = does not expire

    # Conditions for permission to apply
    conditions: List[str] = field(default_factory=list)  # e.g., ["T3 > 0.5"]

    # Metadata
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Cryptographic proof
    claim_hash: str = ""  # Hash of claim content
    signature: str = ""  # Ed25519 signature by issuer

    # Revocation
    status: PermissionStatus = PermissionStatus.ACTIVE
    revoked_at: Optional[datetime] = None
    revocation_reason: Optional[str] = None

    def __post_init__(self):
        """Generate claim hash if not provided"""
        if not self.claim_hash:
            self.claim_hash = self.compute_hash()

    def compute_hash(self) -> str:
        """
        Compute SHA-256 hash of claim content.

        Used for:
        - Tamper detection
        - Signature verification
        - Claim deduplication
        """
        content = {
            "subject_lct": self.subject_lct,
            "permission": self.permission,
            "resource": self.resource,
            "scope": self.scope,
            "issuer_lct": self.issuer_lct,
            "organization": self.organization,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "conditions": sorted(self.conditions),  # Sort for deterministic hash
        }

        content_json = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_json.encode()).hexdigest()

    def is_valid(self, current_time: Optional[datetime] = None) -> tuple[bool, str]:
        """
        Check if claim is currently valid.

        Returns:
            (valid: bool, reason: str)
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        # Check revocation
        if self.status == PermissionStatus.REVOKED:
            return False, f"Permission revoked: {self.revocation_reason}"

        # Check expiration
        if self.expires_at and current_time > self.expires_at:
            return False, f"Permission expired at {self.expires_at.isoformat()}"

        # Valid
        return True, "Permission is active"

    def matches(self, action: str, resource: str, scope: Optional[str] = None) -> bool:
        """
        Check if this claim matches the requested action/resource/scope.

        Supports:
        - Exact match: permission="read:code", action="read", resource="code"
        - Wildcard resource: resource="*" matches any resource
        - Wildcard scope: scope=None matches any scope

        Args:
            action: Requested action (e.g., "read", "write", "execute")
            resource: Requested resource (e.g., "code", "database", "lct")
            scope: Optional scope restriction (e.g., "own", "shared", "staging")

        Returns:
            True if claim authorizes the request
        """
        # Check if claim is valid
        if not self.is_valid()[0]:
            return False

        # Permission format: <action>:<resource>
        # But permission might be stored as just "action" or "action:resource"
        parts = self.permission.split(":")
        claim_action = parts[0] if parts else self.permission

        # Check action match
        if claim_action != action and claim_action != "*":
            return False

        # Check resource match
        # Supports:
        # - "*" matches anything
        # - "permissions:*" matches "permissions:deploy", "permissions:read", etc.
        # - "code" only matches "code" exactly
        if self.resource == "*":
            # Wildcard matches everything
            pass
        elif self.resource.endswith(":*"):
            # Partial wildcard (e.g., "permissions:*")
            prefix = self.resource[:-2]  # Remove ":*"
            if not resource.startswith(prefix + ":"):
                return False
        elif self.resource != resource:
            # Exact match required
            return False

        # Check scope match (if claim has scope restriction)
        if self.scope is not None:
            if scope != self.scope and self.scope != "*":
                return False

        return True

    def revoke(self, reason: str):
        """
        Revoke this permission claim.

        Args:
            reason: Human-readable revocation reason
        """
        self.status = PermissionStatus.REVOKED
        self.revoked_at = datetime.now(timezone.utc)
        self.revocation_reason = reason

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "subject_lct": self.subject_lct,
            "permission": self.permission,
            "resource": self.resource,
            "scope": self.scope,
            "issuer_lct": self.issuer_lct,
            "organization": self.organization,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "conditions": self.conditions,
            "description": self.description,
            "metadata": self.metadata,
            "claim_hash": self.claim_hash,
            "signature": self.signature,
            "status": self.status.value,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "revocation_reason": self.revocation_reason
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PermissionClaim':
        """Deserialize from dictionary"""
        # Parse datetimes
        issued_at = datetime.fromisoformat(data["issued_at"])
        expires_at = datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
        revoked_at = datetime.fromisoformat(data["revoked_at"]) if data.get("revoked_at") else None

        return cls(
            subject_lct=data["subject_lct"],
            permission=data["permission"],
            resource=data.get("resource", "*"),
            scope=data.get("scope"),
            issuer_lct=data["issuer_lct"],
            organization=data["organization"],
            issued_at=issued_at,
            expires_at=expires_at,
            conditions=data.get("conditions", []),
            description=data.get("description"),
            metadata=data.get("metadata", {}),
            claim_hash=data["claim_hash"],
            signature=data["signature"],
            status=PermissionStatus(data.get("status", "active")),
            revoked_at=revoked_at,
            revocation_reason=data.get("revocation_reason")
        )


@dataclass
class PermissionBundle:
    """
    Collection of permissions for an agent.

    Aggregates all permission claims for a subject, providing:
    - Effective permissions (computed from all claims)
    - Reputation context (T3 score)
    - Organizational membership
    - Role-based permissions
    """

    lct_id: str  # Agent's LCT identity
    organization: str  # Organization context

    # Permission claims
    claims: List[PermissionClaim] = field(default_factory=list)

    # Reputation context
    t3_score: float = 0.0  # Current trust score (0.0-1.0)
    reputation_level: str = "novice"  # Derived from T3 score

    # Organizational context
    roles: List[str] = field(default_factory=list)  # Roles within organization

    # Metadata
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def get_effective_permissions(self) -> Dict[str, List[str]]:
        """
        Compute effective permissions from all claims.

        Returns:
            Dictionary mapping action -> list of resources
            Example: {"read": ["code", "docs"], "write": ["code:own"]}
        """
        effective: Dict[str, List[str]] = {}

        for claim in self.claims:
            # Skip invalid claims
            if not claim.is_valid()[0]:
                continue

            # Extract action from permission
            parts = claim.permission.split(":")
            action = parts[0]

            # Build resource string
            if claim.scope:
                resource_str = f"{claim.resource}:{claim.scope}"
            else:
                resource_str = claim.resource

            # Add to effective permissions
            if action not in effective:
                effective[action] = []

            if resource_str not in effective[action]:
                effective[action].append(resource_str)

        return effective

    def has_permission(self, action: str, resource: str, scope: Optional[str] = None) -> tuple[bool, Optional[PermissionClaim]]:
        """
        Check if agent has specific permission.

        Returns:
            (has_permission: bool, matching_claim: Optional[PermissionClaim])
        """
        for claim in self.claims:
            if claim.matches(action, resource, scope):
                return True, claim

        return False, None

    def add_claim(self, claim: PermissionClaim):
        """Add a permission claim to the bundle"""
        # Check for duplicates
        for existing in self.claims:
            if existing.claim_hash == claim.claim_hash:
                return  # Already have this claim

        self.claims.append(claim)
        self.last_updated = datetime.now(timezone.utc)

    def remove_claim(self, claim_hash: str):
        """Remove a permission claim by hash"""
        self.claims = [c for c in self.claims if c.claim_hash != claim_hash]
        self.last_updated = datetime.now(timezone.utc)

    def get_active_claim_count(self) -> int:
        """Count active (non-revoked, non-expired) claims"""
        return sum(1 for c in self.claims if c.is_valid()[0])

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "lct_id": self.lct_id,
            "organization": self.organization,
            "claims": [c.to_dict() for c in self.claims],
            "t3_score": self.t3_score,
            "reputation_level": self.reputation_level,
            "roles": self.roles,
            "last_updated": self.last_updated.isoformat(),
            "effective_permissions": self.get_effective_permissions(),
            "active_claim_count": self.get_active_claim_count()
        }


# Standard permission sets (from WEB4-AUTH-001)

NOVICE_PERMISSIONS = [
    "read:public_docs",
    "write:own_profile",
    "execute:basic_tests"
]

DEVELOPING_PERMISSIONS = NOVICE_PERMISSIONS + [
    "read:shared_docs",
    "write:own_code",
    "execute:unit_tests"
]

TRUSTED_PERMISSIONS = DEVELOPING_PERMISSIONS + [
    "read:code",
    "write:code:own",
    "execute:integration_tests",
    "witness:lct:ai"  # Can witness AI LCT creation
]

EXPERT_PERMISSIONS = TRUSTED_PERMISSIONS + [
    "write:code:shared",
    "execute:deploy:staging",
    "witness:lct:*",  # Can witness any LCT type
    "review:code"
]

MASTER_PERMISSIONS = EXPERT_PERMISSIONS + [
    "write:critical_systems",
    "execute:deploy:production",
    "grant:permissions:limited",
    "admin:team"
]

ADMIN_PERMISSIONS = MASTER_PERMISSIONS + [
    "admin:org:*",
    "grant:permissions:*",
    "revoke:permissions:*",
    "manage:security"
]


def get_reputation_permissions(t3_score: float) -> List[str]:
    """
    Get standard permissions based on reputation score.

    T3 ranges:
    - 0.0-0.3: Novice
    - 0.3-0.5: Developing
    - 0.5-0.7: Trusted
    - 0.7-0.9: Expert
    - 0.9-1.0: Master

    Admin permissions require explicit grant, not just reputation.
    """
    if t3_score >= 0.9:
        return MASTER_PERMISSIONS
    elif t3_score >= 0.7:
        return EXPERT_PERMISSIONS
    elif t3_score >= 0.5:
        return TRUSTED_PERMISSIONS
    elif t3_score >= 0.3:
        return DEVELOPING_PERMISSIONS
    else:
        return NOVICE_PERMISSIONS


def get_reputation_level(t3_score: float) -> str:
    """Get reputation level name from T3 score"""
    if t3_score >= 0.9:
        return "master"
    elif t3_score >= 0.7:
        return "expert"
    elif t3_score >= 0.5:
        return "trusted"
    elif t3_score >= 0.3:
        return "developing"
    else:
        return "novice"
