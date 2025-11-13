"""
Web4 Authorization System - Authorization Engine
=================================================

Makes authorization decisions based on LCT identity, permissions, and reputation.

Based on: WEB4-AUTH-001 proposal (Session #21)
Author: Web4 Authorization Implementation (Session #22)
License: MIT
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone

# Add reference implementation to path
sys.path.insert(0, str(Path(__file__).parent.parent / "reference"))

from permission_claim import (
    PermissionClaim,
    PermissionBundle,
    PermissionStatus,
    get_reputation_permissions,
    get_reputation_level
)


class PermissionStore:
    """
    In-memory storage for permission claims.

    For production, replace with persistent database (PostgreSQL, etc.)
    """

    def __init__(self):
        # claims_by_subject[subject_lct][organization] = [claims]
        self.claims_by_subject: Dict[str, Dict[str, List[PermissionClaim]]] = {}

        # claims_by_hash[claim_hash] = claim
        self.claims_by_hash: Dict[str, PermissionClaim] = {}

    def store_claim(self, claim: PermissionClaim):
        """Store a permission claim"""
        # Store by subject
        if claim.subject_lct not in self.claims_by_subject:
            self.claims_by_subject[claim.subject_lct] = {}

        if claim.organization not in self.claims_by_subject[claim.subject_lct]:
            self.claims_by_subject[claim.subject_lct][claim.organization] = []

        # Check for duplicate
        existing_claims = self.claims_by_subject[claim.subject_lct][claim.organization]
        for existing in existing_claims:
            if existing.claim_hash == claim.claim_hash:
                return  # Already stored

        self.claims_by_subject[claim.subject_lct][claim.organization].append(claim)

        # Store by hash
        self.claims_by_hash[claim.claim_hash] = claim

    def get_claims(self, subject_lct: str, organization: str) -> List[PermissionClaim]:
        """Get all claims for a subject in an organization"""
        return self.claims_by_subject.get(subject_lct, {}).get(organization, [])

    def get_claim(self, claim_hash: str) -> Optional[PermissionClaim]:
        """Get a specific claim by hash"""
        return self.claims_by_hash.get(claim_hash)

    def update_claim(self, claim: PermissionClaim):
        """Update an existing claim"""
        if claim.claim_hash in self.claims_by_hash:
            self.claims_by_hash[claim.claim_hash] = claim

            # Update in subject index
            if claim.subject_lct in self.claims_by_subject:
                if claim.organization in self.claims_by_subject[claim.subject_lct]:
                    claims = self.claims_by_subject[claim.subject_lct][claim.organization]
                    for i, existing in enumerate(claims):
                        if existing.claim_hash == claim.claim_hash:
                            claims[i] = claim
                            break

    def revoke_claim(self, claim_hash: str, reason: str, revoker_lct: str) -> bool:
        """Revoke a permission claim"""
        claim = self.get_claim(claim_hash)
        if not claim:
            return False

        claim.revoke(reason)
        self.update_claim(claim)
        return True


class ReputationService:
    """
    Mock reputation service for T3 score lookup.

    For production, integrate with actual reputation tracking system.
    """

    def __init__(self):
        # t3_scores[lct_id][organization] = score
        self.t3_scores: Dict[str, Dict[str, float]] = {}

    def get_t3(self, lct_id: str, organization: str = "default") -> float:
        """Get T3 reputation score for an agent"""
        return self.t3_scores.get(lct_id, {}).get(organization, 0.0)

    def set_t3(self, lct_id: str, score: float, organization: str = "default"):
        """Set T3 reputation score (for testing)"""
        if lct_id not in self.t3_scores:
            self.t3_scores[lct_id] = {}
        self.t3_scores[lct_id][organization] = max(0.0, min(1.0, score))  # Clamp to [0, 1]


class AuthorizationEngine:
    """
    Core authorization engine for Web4.

    Makes authorization decisions based on:
    1. Cryptographic identity (LCT)
    2. Explicit permission claims
    3. Reputation-based permissions (T3 score)
    4. Role-based permissions
    5. Organizational context
    """

    def __init__(
        self,
        permission_store: Optional[PermissionStore] = None,
        reputation_service: Optional[ReputationService] = None,
        lct_registry=None
    ):
        self.permission_store = permission_store or PermissionStore()
        self.reputation_service = reputation_service or ReputationService()
        self.lct_registry = lct_registry  # Optional LCT registry for identity verification

    def get_permission_bundle(
        self,
        lct_id: str,
        organization: str,
        include_reputation_permissions: bool = True
    ) -> PermissionBundle:
        """
        Get all permissions for an agent in a given organization.

        Combines:
        - Explicit permission claims
        - Reputation-based permissions (if enabled)
        - Role-based permissions (future)

        Args:
            lct_id: Agent's LCT identifier
            organization: Organization context
            include_reputation_permissions: Whether to include T3-based permissions

        Returns:
            PermissionBundle with all effective permissions
        """
        # Get explicit claims
        claims = self.permission_store.get_claims(lct_id, organization)

        # Get reputation
        t3_score = self.reputation_service.get_t3(lct_id, organization)
        reputation_level = get_reputation_level(t3_score)

        # Create bundle
        bundle = PermissionBundle(
            lct_id=lct_id,
            organization=organization,
            claims=claims.copy(),  # Copy to avoid mutation
            t3_score=t3_score,
            reputation_level=reputation_level,
            roles=[]  # TODO: Get from organization service
        )

        # Add reputation-based permissions as implicit claims
        if include_reputation_permissions:
            rep_permissions = get_reputation_permissions(t3_score)

            for perm in rep_permissions:
                # Parse permission string (e.g., "read:code" -> action="read", resource="code")
                parts = perm.split(":")
                action = parts[0]
                resource = parts[1] if len(parts) > 1 else "*"
                scope = parts[2] if len(parts) > 2 else None

                # Create implicit claim (not cryptographically signed, derived from reputation)
                implicit_claim = PermissionClaim(
                    subject_lct=lct_id,
                    permission=action,
                    resource=resource,
                    scope=scope,
                    issuer_lct="system:reputation",  # Issued by reputation system
                    organization=organization,
                    description=f"Reputation-based permission (T3={t3_score:.2f}, level={reputation_level})",
                    metadata={"source": "reputation", "t3_score": t3_score}
                )

                bundle.add_claim(implicit_claim)

        return bundle

    def is_authorized(
        self,
        lct_id: str,
        action: str,
        resource: str,
        organization: str,
        scope: Optional[str] = None,
        check_conditions: bool = True
    ) -> Tuple[bool, str, Optional[PermissionClaim]]:
        """
        Make authorization decision.

        Args:
            lct_id: Agent's LCT identifier
            action: Requested action (e.g., "read", "write", "execute")
            resource: Requested resource (e.g., "code", "database", "lct")
            organization: Organization context
            scope: Optional scope restriction (e.g., "own", "shared")
            check_conditions: Whether to evaluate permission conditions

        Returns:
            (authorized: bool, reason: str, matching_claim: Optional[PermissionClaim])
        """
        # Verify identity exists (if registry available)
        if self.lct_registry:
            lct = self.lct_registry.get_lct(lct_id)
            if not lct:
                return False, "Identity not found", None

        # Get permission bundle
        bundle = self.get_permission_bundle(lct_id, organization)

        # Check if permission exists
        has_perm, claim = bundle.has_permission(action, resource, scope)

        if not has_perm:
            return False, f"No permission for {action}:{resource}" + (f":{scope}" if scope else ""), None

        # Check conditions (if claim has conditions)
        if check_conditions and claim and claim.conditions:
            conditions_met, condition_reason = self._check_conditions(
                claim.conditions,
                bundle
            )

            if not conditions_met:
                return False, f"Permission condition not met: {condition_reason}", claim

        # Authorized
        return True, "Permission granted", claim

    def _check_conditions(
        self,
        conditions: List[str],
        bundle: PermissionBundle
    ) -> Tuple[bool, str]:
        """
        Check if permission conditions are met.

        Supported condition formats:
        - "T3 >= 0.5" - Reputation threshold
        - "within_org:<org_name>" - Must be in organization
        - "role:<role_name>" - Must have role

        Args:
            conditions: List of condition strings
            bundle: Permission bundle with context

        Returns:
            (conditions_met: bool, reason: str)
        """
        for condition in conditions:
            # Parse condition
            parts = condition.strip().split()

            if len(parts) == 0:
                continue

            # T3 score condition (e.g., "T3 >= 0.5")
            if parts[0] == "T3" and len(parts) >= 3:
                operator = parts[1]
                threshold = float(parts[2])

                if operator == ">=":
                    if not (bundle.t3_score >= threshold):
                        return False, f"T3 score {bundle.t3_score:.2f} < {threshold}"
                elif operator == ">":
                    if not (bundle.t3_score > threshold):
                        return False, f"T3 score {bundle.t3_score:.2f} <= {threshold}"
                elif operator == "<=":
                    if not (bundle.t3_score <= threshold):
                        return False, f"T3 score {bundle.t3_score:.2f} > {threshold}"
                elif operator == "<":
                    if not (bundle.t3_score < threshold):
                        return False, f"T3 score {bundle.t3_score:.2f} >= {threshold}"

            # Organization membership condition
            elif condition.startswith("within_org:"):
                required_org = condition.split(":", 1)[1]
                if bundle.organization != required_org:
                    return False, f"Not in required organization {required_org}"

            # Role requirement condition
            elif condition.startswith("role:"):
                required_role = condition.split(":", 1)[1]
                if required_role not in bundle.roles:
                    return False, f"Missing required role {required_role}"

            # Unknown condition type - fail safe
            else:
                return False, f"Unknown condition: {condition}"

        # All conditions met
        return True, "All conditions met"

    def grant_permission(
        self,
        subject_lct: str,
        permission: str,
        resource: str,
        organization: str,
        issuer_lct: str,
        scope: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        conditions: Optional[List[str]] = None,
        description: Optional[str] = None
    ) -> Tuple[bool, str, Optional[PermissionClaim]]:
        """
        Grant a permission to an agent.

        Authorization: Issuer must have "grant:permissions:*" permission

        Args:
            subject_lct: Who receives permission
            permission: What permission (action)
            resource: Which resource
            organization: In which organization
            issuer_lct: Who grants the permission
            scope: Optional scope restriction
            expires_at: When permission expires
            conditions: Permission conditions
            description: Human-readable description

        Returns:
            (success: bool, message: str, claim: Optional[PermissionClaim])
        """
        # Check if issuer is authorized to grant permissions
        can_grant, reason, _ = self.is_authorized(
            lct_id=issuer_lct,
            action="grant",
            resource=f"permissions:{permission}",
            organization=organization
        )

        if not can_grant:
            return False, f"Issuer not authorized to grant permissions: {reason}", None

        # Verify subject exists (if registry available)
        if self.lct_registry:
            subject_lct_obj = self.lct_registry.get_lct(subject_lct)
            if not subject_lct_obj:
                return False, "Subject LCT not found", None

        # Create permission claim
        claim = PermissionClaim(
            subject_lct=subject_lct,
            permission=permission,
            resource=resource,
            scope=scope,
            issuer_lct=issuer_lct,
            organization=organization,
            expires_at=expires_at,
            conditions=conditions or [],
            description=description
        )

        # Store claim
        self.permission_store.store_claim(claim)

        return True, "Permission granted", claim

    def revoke_permission(
        self,
        claim_hash: str,
        reason: str,
        revoker_lct: str
    ) -> Tuple[bool, str]:
        """
        Revoke a permission claim.

        Authorization: Revoker must have "revoke:permissions:*" or be original issuer

        Args:
            claim_hash: Hash of claim to revoke
            reason: Revocation reason
            revoker_lct: Who is revoking

        Returns:
            (success: bool, message: str)
        """
        claim = self.permission_store.get_claim(claim_hash)
        if not claim:
            return False, "Permission claim not found"

        # Check authorization
        can_revoke = (
            # Original issuer can revoke
            revoker_lct == claim.issuer_lct or
            # Admin with revoke permission can revoke
            self.is_authorized(
                lct_id=revoker_lct,
                action="revoke",
                resource="permissions:*",
                organization=claim.organization
            )[0]
        )

        if not can_revoke:
            return False, "Not authorized to revoke this permission"

        # Revoke claim
        success = self.permission_store.revoke_claim(claim_hash, reason, revoker_lct)

        if success:
            return True, f"Permission revoked: {reason}"
        else:
            return False, "Failed to revoke permission"


# Singleton instance for convenience
_auth_engine_instance: Optional[AuthorizationEngine] = None


def get_authorization_engine() -> AuthorizationEngine:
    """Get singleton authorization engine instance"""
    global _auth_engine_instance
    if _auth_engine_instance is None:
        _auth_engine_instance = AuthorizationEngine()
    return _auth_engine_instance


def set_authorization_engine(engine: AuthorizationEngine):
    """Set custom authorization engine instance"""
    global _auth_engine_instance
    _auth_engine_instance = engine
