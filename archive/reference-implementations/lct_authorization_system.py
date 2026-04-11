#!/usr/bin/env python3
"""
LCT Authorization System Reference Implementation
Proposal: WEB4-AUTH-001

Implements trust-based access control built on LCT identities.
Answers: "What is this agent allowed to do?"

Key features:
- Permission claims with cryptographic signatures
- Reputation-based dynamic permissions (T3 thresholds)
- Permission hierarchy (action:resource:scope)
- Cross-organization trust attestations
- Permission revocation and expiration
- Self-grant prevention (anti-escalation)
- Audit trail for all permission operations
- ATP cost for permission grants
- Society-level authorization integration
"""

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================
# Section 1: Core Data Structures
# ============================================================

class ReputationLevel(Enum):
    NOVICE = "novice"       # T3 < 0.3
    DEVELOPING = "developing"  # 0.3 ≤ T3 < 0.5
    TRUSTED = "trusted"     # 0.5 ≤ T3 < 0.7
    EXPERT = "expert"       # 0.7 ≤ T3 < 0.9
    MASTER = "master"       # T3 ≥ 0.9


def get_reputation_level(t3_score: float) -> ReputationLevel:
    if t3_score >= 0.9:
        return ReputationLevel.MASTER
    elif t3_score >= 0.7:
        return ReputationLevel.EXPERT
    elif t3_score >= 0.5:
        return ReputationLevel.TRUSTED
    elif t3_score >= 0.3:
        return ReputationLevel.DEVELOPING
    else:
        return ReputationLevel.NOVICE


# Standard permission sets per reputation level
NOVICE_PERMISSIONS = frozenset([
    "read:public_docs",
    "write:own_profile",
    "execute:basic_tests",
])

DEVELOPING_PERMISSIONS = NOVICE_PERMISSIONS | frozenset([
    "read:shared_docs",
    "write:own_data",
    "execute:standard_tests",
])

TRUSTED_PERMISSIONS = DEVELOPING_PERMISSIONS | frozenset([
    "read:code",
    "write:code:own",
    "execute:unit_tests",
    "witness:lct:ai",
])

EXPERT_PERMISSIONS = TRUSTED_PERMISSIONS | frozenset([
    "write:code:shared",
    "execute:integration_tests",
    "execute:deploy:staging",
    "witness:lct:*",
])

MASTER_PERMISSIONS = EXPERT_PERMISSIONS | frozenset([
    "admin:org:*",
    "mint:lct:*",
    "grant:permissions:*",
    "execute:deploy:production",
])

LEVEL_PERMISSIONS = {
    ReputationLevel.NOVICE: NOVICE_PERMISSIONS,
    ReputationLevel.DEVELOPING: DEVELOPING_PERMISSIONS,
    ReputationLevel.TRUSTED: TRUSTED_PERMISSIONS,
    ReputationLevel.EXPERT: EXPERT_PERMISSIONS,
    ReputationLevel.MASTER: MASTER_PERMISSIONS,
}


@dataclass
class PermissionClaim:
    """Cryptographically signed permission grant."""
    claim_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    subject_lct: str = ""
    permission: str = ""
    resource: str = "*"
    issuer_lct: str = ""
    organization: str = ""
    issued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    conditions: List[str] = field(default_factory=list)
    claim_hash: str = ""
    signature: str = ""
    revoked: bool = False
    revoked_at: Optional[datetime] = None
    revocation_reason: Optional[str] = None

    def __post_init__(self):
        if not self.claim_hash:
            content = f"{self.subject_lct}:{self.permission}:{self.resource}:{self.issuer_lct}:{self.organization}"
            self.claim_hash = hashlib.sha256(content.encode()).hexdigest()
        if not self.signature:
            sig_input = f"{self.claim_hash}:{self.issuer_lct}"
            self.signature = hashlib.sha256(sig_input.encode()).hexdigest()[:32]

    def is_valid(self, now: datetime = None) -> bool:
        """Check if claim is currently valid."""
        if now is None:
            now = datetime.now(timezone.utc)
        if self.revoked:
            return False
        if self.expires_at and now > self.expires_at:
            return False
        return True


@dataclass
class PermissionBundle:
    """Collection of permissions for an agent."""
    lct_id: str
    claims: List[PermissionClaim] = field(default_factory=list)
    effective_permissions: Set[str] = field(default_factory=set)
    t3_score: float = 0.5
    reputation_level: ReputationLevel = ReputationLevel.TRUSTED
    organizations: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def permission_count(self) -> int:
        return len(self.effective_permissions)


@dataclass
class PermissionCondition:
    """Condition that must be met for permission to apply."""
    condition_type: str  # "reputation", "time", "organization"
    operator: str  # ">", "<", ">=", "<=", "=="
    value: Any

    def evaluate(self, context: Dict[str, Any]) -> bool:
        actual = context.get(self.condition_type)
        if actual is None:
            return False
        if self.operator == ">":
            return actual > self.value
        elif self.operator == "<":
            return actual < self.value
        elif self.operator == ">=":
            return actual >= self.value
        elif self.operator == "<=":
            return actual <= self.value
        elif self.operator == "==":
            return actual == self.value
        return False


@dataclass
class TrustAttestation:
    """Cross-organization trust attestation."""
    attestation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    subject_lct: str = ""
    attesting_org: str = ""
    recipient_org: str = ""
    trust_level: str = "trusted"
    permissions: List[str] = field(default_factory=list)
    attestation_hash: str = ""
    signature: str = ""
    issued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.attestation_hash:
            content = f"{self.subject_lct}:{self.attesting_org}:{self.recipient_org}"
            self.attestation_hash = hashlib.sha256(content.encode()).hexdigest()
        if not self.signature:
            self.signature = hashlib.sha256(
                f"{self.attestation_hash}:sig".encode()
            ).hexdigest()[:32]

    def is_valid(self, now: datetime = None) -> bool:
        if now is None:
            now = datetime.now(timezone.utc)
        if self.expires_at and now > self.expires_at:
            return False
        return True


@dataclass
class AuditEntry:
    """Audit log entry for permission operations."""
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation: str = ""  # "grant", "revoke", "check", "deny"
    subject_lct: str = ""
    permission: str = ""
    issuer_lct: str = ""
    organization: str = ""
    result: str = ""  # "allowed", "denied", "granted", "revoked"
    reason: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    atp_cost: float = 0.0


# ============================================================
# Section 2: Permission Store
# ============================================================

class PermissionStore:
    """In-memory permission store."""

    def __init__(self):
        self.claims: Dict[str, PermissionClaim] = {}
        self.attestations: Dict[str, TrustAttestation] = {}

    def store_claim(self, claim: PermissionClaim):
        self.claims[claim.claim_id] = claim

    def get_claim(self, claim_id: str) -> Optional[PermissionClaim]:
        return self.claims.get(claim_id)

    def get_claims(self, subject_lct: str, organization: str = None) -> List[PermissionClaim]:
        result = []
        for claim in self.claims.values():
            if claim.subject_lct == subject_lct and claim.is_valid():
                if organization is None or claim.organization == organization:
                    result.append(claim)
        return result

    def get_all_claims_for_subject(self, subject_lct: str) -> List[PermissionClaim]:
        return [c for c in self.claims.values() if c.subject_lct == subject_lct]

    def store_attestation(self, attestation: TrustAttestation):
        self.attestations[attestation.attestation_id] = attestation

    def get_attestations(
        self, subject_lct: str, recipient_org: str = None
    ) -> List[TrustAttestation]:
        result = []
        for att in self.attestations.values():
            if att.subject_lct == subject_lct and att.is_valid():
                if recipient_org is None or att.recipient_org == recipient_org:
                    result.append(att)
        return result


# ============================================================
# Section 3: Reputation Service
# ============================================================

class ReputationService:
    """Manages entity reputation scores."""

    def __init__(self):
        self.scores: Dict[str, Dict[str, float]] = {}  # (lct, org) → T3

    def set_t3(self, lct_id: str, organization: str, score: float):
        key = f"{lct_id}|{organization}"
        self.scores[key] = {"t3": max(0.0, min(1.0, score))}

    def get_t3(self, lct_id: str, organization: str = "") -> float:
        key = f"{lct_id}|{organization}"
        if key in self.scores:
            return self.scores[key]["t3"]
        # Check without org
        key_global = f"{lct_id}|"
        if key_global in self.scores:
            return self.scores[key_global]["t3"]
        return 0.5  # Default


# ============================================================
# Section 4: Organization Service
# ============================================================

class OrganizationService:
    """Manages organization memberships and roles."""

    def __init__(self):
        self.memberships: Dict[str, Dict[str, List[str]]] = {}  # org → {lct → [roles]}
        self.blocked: Dict[str, Set[str]] = {}  # org → {blocked_lcts}

    def add_member(self, lct_id: str, organization: str, roles: List[str]):
        if organization not in self.memberships:
            self.memberships[organization] = {}
        self.memberships[organization][lct_id] = roles

    def get_roles(self, lct_id: str, organization: str) -> List[str]:
        return self.memberships.get(organization, {}).get(lct_id, [])

    def is_member(self, lct_id: str, organization: str) -> bool:
        return lct_id in self.memberships.get(organization, {})

    def block(self, lct_id: str, organization: str):
        if organization not in self.blocked:
            self.blocked[organization] = set()
        self.blocked[organization].add(lct_id)

    def is_blocked(self, lct_id: str, organization: str) -> bool:
        return lct_id in self.blocked.get(organization, set())


# ============================================================
# Section 5: Authorization Engine
# ============================================================

class AuthorizationEngine:
    """Core authorization engine combining identity, reputation, and permissions."""

    ATP_GRANT_COST = 10.0

    def __init__(self):
        self.permission_store = PermissionStore()
        self.reputation_service = ReputationService()
        self.org_service = OrganizationService()
        self.audit_log: List[AuditEntry] = []
        self.atp_balances: Dict[str, float] = {}  # lct → ATP balance
        self.active_lcts: Set[str] = set()

    def register_entity(self, lct_id: str, atp_balance: float = 100.0):
        self.active_lcts.add(lct_id)
        self.atp_balances[lct_id] = atp_balance

    def get_reputation_permissions(self, t3_score: float) -> Set[str]:
        level = get_reputation_level(t3_score)
        return set(LEVEL_PERMISSIONS.get(level, NOVICE_PERMISSIONS))

    def get_permissions(self, lct_id: str, organization: str) -> PermissionBundle:
        """Get all effective permissions for an agent."""
        # Explicit claims
        claims = self.permission_store.get_claims(lct_id, organization)

        # Reputation
        t3 = self.reputation_service.get_t3(lct_id, organization)
        level = get_reputation_level(t3)

        # Role-based
        roles = self.org_service.get_roles(lct_id, organization)

        # Combine all permissions
        effective = set()

        # Add reputation-based
        effective.update(self.get_reputation_permissions(t3))

        # Add claim-based (only valid)
        for claim in claims:
            if claim.is_valid():
                effective.add(claim.permission)

        return PermissionBundle(
            lct_id=lct_id,
            claims=claims,
            effective_permissions=effective,
            t3_score=t3,
            reputation_level=level,
            organizations=[organization],
            roles=roles,
        )

    def is_authorized(
        self,
        lct_id: str,
        action: str,
        resource: str,
        organization: str,
    ) -> Tuple[bool, str]:
        """Make authorization decision."""
        # Check entity exists and is active
        if lct_id not in self.active_lcts:
            self._audit("check", lct_id, f"{action}:{resource}", "", organization, "denied", "Identity not found")
            return False, "Identity not found"

        # Check blocked
        if self.org_service.is_blocked(lct_id, organization):
            self._audit("check", lct_id, f"{action}:{resource}", "", organization, "denied", "Agent blocked")
            return False, "Agent blocked from organization"

        # Get permissions
        bundle = self.get_permissions(lct_id, organization)
        perm_string = f"{action}:{resource}"

        # Check exact match
        if perm_string in bundle.effective_permissions:
            self._audit("check", lct_id, perm_string, "", organization, "allowed", "Explicit permission")
            return True, "Explicit permission granted"

        # Check wildcard: action:*
        action_wildcard = f"{action}:*"
        if action_wildcard in bundle.effective_permissions:
            self._audit("check", lct_id, perm_string, "", organization, "allowed", "Wildcard permission")
            return True, "Wildcard permission granted"

        # Check admin:*
        if "admin:*" in bundle.effective_permissions:
            self._audit("check", lct_id, perm_string, "", organization, "allowed", "Admin permission")
            return True, "Admin permission granted"

        # Check admin:org:*
        if "admin:org:*" in bundle.effective_permissions:
            self._audit("check", lct_id, perm_string, "", organization, "allowed", "Org admin")
            return True, "Organization admin permission"

        # Check conditions on claims
        context = {
            "reputation": bundle.t3_score,
            "organization": organization,
        }
        for claim in bundle.claims:
            if claim.is_valid() and claim.permission == perm_string:
                conditions_met = True
                for cond_str in claim.conditions:
                    cond = self._parse_condition(cond_str)
                    if cond and not cond.evaluate(context):
                        conditions_met = False
                        break
                if conditions_met:
                    self._audit("check", lct_id, perm_string, "", organization, "allowed", "Conditional")
                    return True, "Conditional permission met"

        # Default deny
        self._audit("check", lct_id, perm_string, "", organization, "denied", "No matching permission")
        return False, "No matching permission"

    def grant_permission(
        self,
        issuer_lct: str,
        subject_lct: str,
        permission: str,
        organization: str,
        resource: str = "*",
        expires_hours: Optional[float] = None,
        conditions: List[str] = None,
    ) -> Tuple[Optional[PermissionClaim], str]:
        """Grant permission to an agent."""
        # Anti-escalation: no self-granting
        if issuer_lct == subject_lct:
            self._audit("grant", subject_lct, permission, issuer_lct, organization, "denied", "Self-grant forbidden")
            return None, "Cannot grant permissions to self"

        # Check issuer has grant authority
        can_grant, reason = self.is_authorized(issuer_lct, "grant", f"permissions:{permission}", organization)
        if not can_grant:
            # Also check if issuer has admin:*
            can_admin, _ = self.is_authorized(issuer_lct, "admin", "*", organization)
            if not can_admin:
                self._audit("grant", subject_lct, permission, issuer_lct, organization, "denied", "No grant authority")
                return None, f"Issuer not authorized to grant: {reason}"

        # Check subject exists
        if subject_lct not in self.active_lcts:
            return None, "Subject LCT not found"

        # Check ATP
        atp_balance = self.atp_balances.get(issuer_lct, 0)
        if atp_balance < self.ATP_GRANT_COST:
            return None, f"Insufficient ATP: need {self.ATP_GRANT_COST}, have {atp_balance}"

        # Create claim
        expires_at = None
        if expires_hours is not None:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)

        claim = PermissionClaim(
            subject_lct=subject_lct,
            permission=permission,
            resource=resource,
            issuer_lct=issuer_lct,
            organization=organization,
            expires_at=expires_at,
            conditions=conditions or [],
        )

        # Store and deduct ATP
        self.permission_store.store_claim(claim)
        self.atp_balances[issuer_lct] -= self.ATP_GRANT_COST

        self._audit("grant", subject_lct, permission, issuer_lct, organization, "granted", "Permission granted", self.ATP_GRANT_COST)
        return claim, "Permission granted"

    def revoke_permission(
        self,
        revoker_lct: str,
        claim_id: str,
        reason: str,
    ) -> Tuple[bool, str]:
        """Revoke a permission claim."""
        claim = self.permission_store.get_claim(claim_id)
        if not claim:
            return False, "Claim not found"

        # Check authorization to revoke: must be issuer or admin
        can_revoke = (
            revoker_lct == claim.issuer_lct or
            self.is_authorized(revoker_lct, "admin", "permissions", claim.organization)[0]
        )
        if not can_revoke:
            self._audit("revoke", claim.subject_lct, claim.permission, revoker_lct, claim.organization, "denied", "No revoke authority")
            return False, "Not authorized to revoke"

        claim.revoked = True
        claim.revoked_at = datetime.now(timezone.utc)
        claim.revocation_reason = reason

        self._audit("revoke", claim.subject_lct, claim.permission, revoker_lct, claim.organization, "revoked", reason)
        return True, "Permission revoked"

    def cross_org_authorize(
        self,
        lct_id: str,
        action: str,
        resource: str,
        requesting_org: str,
    ) -> Tuple[bool, str]:
        """Authorize action across organizations using attestations."""
        # Check direct permissions first
        direct = self.is_authorized(lct_id, action, resource, requesting_org)
        if direct[0]:
            return direct

        # Check trust attestations
        attestations = self.permission_store.get_attestations(lct_id, requesting_org)
        perm_string = f"{action}:{resource}"

        for att in attestations:
            if att.is_valid() and perm_string in att.permissions:
                self._audit("check", lct_id, perm_string, "", requesting_org, "allowed",
                           f"Cross-org: attested by {att.attesting_org}")
                return True, f"Attested by {att.attesting_org}"

        self._audit("check", lct_id, perm_string, "", requesting_org, "denied", "No cross-org auth")
        return False, "No cross-organization authorization found"

    def _parse_condition(self, cond_str: str) -> Optional[PermissionCondition]:
        """Parse condition string like 'T3 >= 0.5'."""
        parts = cond_str.strip().split()
        if len(parts) >= 3:
            ctype = parts[0].lower()
            if ctype == "t3":
                ctype = "reputation"
            op = parts[1]
            try:
                val = float(parts[2])
            except ValueError:
                val = parts[2]
            return PermissionCondition(ctype, op, val)
        return None

    def _audit(self, operation, subject, permission, issuer, organization, result, reason, atp_cost=0.0):
        self.audit_log.append(AuditEntry(
            operation=operation,
            subject_lct=subject,
            permission=permission,
            issuer_lct=issuer,
            organization=organization,
            result=result,
            reason=reason,
            atp_cost=atp_cost,
        ))


# ============================================================
# Section 6: Society Authorization
# ============================================================

class SocietyAuthorization:
    """Authorization system integrated with Web4 societies."""

    MIN_JOIN_REPUTATION = 0.1
    MIN_WITNESS_REPUTATION = 0.5
    MIN_WITNESS_ACTIONS = 3

    def __init__(self, society_id: str, auth_engine: AuthorizationEngine):
        self.society_id = society_id
        self.auth = auth_engine
        self.witness_counts: Dict[str, int] = {}

    def agent_can_join(self, lct_id: str) -> Tuple[bool, str]:
        """Check if agent can join society."""
        t3 = self.auth.reputation_service.get_t3(lct_id, self.society_id)
        if t3 < self.MIN_JOIN_REPUTATION:
            return False, f"Reputation too low ({t3:.2f} < {self.MIN_JOIN_REPUTATION})"
        if self.auth.org_service.is_blocked(lct_id, self.society_id):
            return False, "Agent blocked from society"
        return True, "Authorized to join"

    def agent_can_witness(self, lct_id: str) -> Tuple[bool, str]:
        """Check if agent can witness LCT creation."""
        has_perm = self.auth.is_authorized(lct_id, "witness", "lct:*", self.society_id)
        if not has_perm[0]:
            # Check if reputation level grants witness permission
            t3 = self.auth.reputation_service.get_t3(lct_id, self.society_id)
            if t3 < self.MIN_WITNESS_REPUTATION:
                return False, f"Reputation too low for witnessing ({t3:.2f})"

        witness_count = self.witness_counts.get(lct_id, 0)
        if witness_count < self.MIN_WITNESS_ACTIONS:
            return False, f"Insufficient witness experience ({witness_count})"

        return True, "Authorized to witness"

    def record_witness(self, lct_id: str):
        self.witness_counts[lct_id] = self.witness_counts.get(lct_id, 0) + 1


# ============================================================
# Section 7: Permission Freshness Checker
# ============================================================

class FreshnessChecker:
    """Check permission freshness (anti-replay)."""

    def __init__(self, auth_engine: AuthorizationEngine):
        self.auth = auth_engine

    def verify_fresh(self, claim: PermissionClaim) -> Tuple[bool, str]:
        """Check if permission is still valid and fresh."""
        now = datetime.now(timezone.utc)

        # Check expiration
        if claim.expires_at and now > claim.expires_at:
            return False, "Permission expired"

        # Check revocation
        if claim.revoked:
            return False, f"Permission revoked: {claim.revocation_reason}"

        # Check issuer still active
        if claim.issuer_lct not in self.auth.active_lcts:
            return False, "Issuer no longer active"

        return True, "Permission fresh and valid"


# ============================================================
# TESTS
# ============================================================

def _check(label: str, condition: bool, detail: str = ""):
    status = "PASS" if condition else "FAIL"
    msg = f"  [{status}] {label}"
    if detail and not condition:
        msg += f" — {detail}"
    print(msg)
    return condition


def run_tests():
    passed = 0
    failed = 0
    total = 0

    def check(label, condition, detail=""):
        nonlocal passed, failed, total
        total += 1
        if _check(label, condition, detail):
            passed += 1
        else:
            failed += 1

    # ── T1: Reputation Levels ──
    print("\n── T1: Reputation Levels ──")

    check("T1.1 Novice < 0.3", get_reputation_level(0.2) == ReputationLevel.NOVICE)
    check("T1.2 Developing 0.3", get_reputation_level(0.3) == ReputationLevel.DEVELOPING)
    check("T1.3 Trusted 0.5", get_reputation_level(0.5) == ReputationLevel.TRUSTED)
    check("T1.4 Expert 0.7", get_reputation_level(0.7) == ReputationLevel.EXPERT)
    check("T1.5 Master 0.9", get_reputation_level(0.9) == ReputationLevel.MASTER)
    check("T1.6 Boundary 0.0", get_reputation_level(0.0) == ReputationLevel.NOVICE)
    check("T1.7 Boundary 1.0", get_reputation_level(1.0) == ReputationLevel.MASTER)
    check("T1.8 Boundary 0.49", get_reputation_level(0.49) == ReputationLevel.DEVELOPING)

    # ── T2: Permission Sets ──
    print("\n── T2: Permission Sets ──")

    check("T2.1 Novice has read:public_docs", "read:public_docs" in NOVICE_PERMISSIONS)
    check("T2.2 Novice no code read", "read:code" not in NOVICE_PERMISSIONS)
    check("T2.3 Trusted has code read", "read:code" in TRUSTED_PERMISSIONS)
    check("T2.4 Trusted has witness:ai", "witness:lct:ai" in TRUSTED_PERMISSIONS)
    check("T2.5 Expert has deploy:staging", "execute:deploy:staging" in EXPERT_PERMISSIONS)
    check("T2.6 Master has admin:org:*", "admin:org:*" in MASTER_PERMISSIONS)
    check("T2.7 Master has grant:permissions:*", "grant:permissions:*" in MASTER_PERMISSIONS)

    # Permission hierarchy: each level is superset of previous
    check("T2.8 Developing ⊇ Novice", NOVICE_PERMISSIONS.issubset(DEVELOPING_PERMISSIONS))
    check("T2.9 Trusted ⊇ Developing", DEVELOPING_PERMISSIONS.issubset(TRUSTED_PERMISSIONS))
    check("T2.10 Expert ⊇ Trusted", TRUSTED_PERMISSIONS.issubset(EXPERT_PERMISSIONS))
    check("T2.11 Master ⊇ Expert", EXPERT_PERMISSIONS.issubset(MASTER_PERMISSIONS))

    # ── T3: Permission Claims ──
    print("\n── T3: Permission Claims ──")

    claim = PermissionClaim(
        subject_lct="lct:web4:agent:alpha",
        permission="read:code",
        issuer_lct="lct:web4:admin:root",
        organization="acme_corp",
    )
    check("T3.1 Claim ID generated", len(claim.claim_id) > 0)
    check("T3.2 Claim hash generated", len(claim.claim_hash) > 0)
    check("T3.3 Signature generated", len(claim.signature) > 0)
    check("T3.4 Claim is valid", claim.is_valid())

    # Revoked claim
    claim.revoked = True
    check("T3.5 Revoked claim invalid", not claim.is_valid())
    claim.revoked = False

    # Expired claim
    expired = PermissionClaim(
        subject_lct="alice",
        permission="read:data",
        issuer_lct="admin",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    check("T3.6 Expired claim invalid", not expired.is_valid())

    # Future expiry valid
    future = PermissionClaim(
        subject_lct="alice",
        permission="read:data",
        issuer_lct="admin",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    check("T3.7 Future claim valid", future.is_valid())

    # ── T4: Permission Bundle ──
    print("\n── T4: Permission Bundle ──")

    bundle = PermissionBundle(
        lct_id="alice",
        effective_permissions={"read:code", "write:code:own", "execute:tests"},
        t3_score=0.75,
        reputation_level=ReputationLevel.EXPERT,
        organizations=["acme"],
        roles=["developer"],
    )
    check("T4.1 Bundle has 3 permissions", bundle.permission_count == 3)
    check("T4.2 Bundle T3 score", bundle.t3_score == 0.75)
    check("T4.3 Bundle reputation level", bundle.reputation_level == ReputationLevel.EXPERT)

    # ── T5: Permission Conditions ──
    print("\n── T5: Permission Conditions ──")

    cond_rep = PermissionCondition("reputation", ">=", 0.5)
    check("T5.1 Condition met", cond_rep.evaluate({"reputation": 0.7}))
    check("T5.2 Condition not met", not cond_rep.evaluate({"reputation": 0.3}))
    check("T5.3 Missing key", not cond_rep.evaluate({}))

    cond_gt = PermissionCondition("reputation", ">", 0.5)
    check("T5.4 Greater than exact boundary", not cond_gt.evaluate({"reputation": 0.5}))
    check("T5.5 Greater than above", cond_gt.evaluate({"reputation": 0.51}))

    cond_lt = PermissionCondition("reputation", "<", 0.5)
    check("T5.6 Less than", cond_lt.evaluate({"reputation": 0.3}))

    cond_eq = PermissionCondition("organization", "==", "acme")
    check("T5.7 Equality match", cond_eq.evaluate({"organization": "acme"}))
    check("T5.8 Equality no match", not cond_eq.evaluate({"organization": "other"}))

    # ── T6: Trust Attestations ──
    print("\n── T6: Trust Attestations ──")

    att = TrustAttestation(
        subject_lct="lct:web4:agent:bob",
        attesting_org="org_alpha",
        recipient_org="org_beta",
        permissions=["read:data", "write:reports"],
    )
    check("T6.1 Attestation hash", len(att.attestation_hash) > 0)
    check("T6.2 Attestation sig", len(att.signature) > 0)
    check("T6.3 Attestation valid", att.is_valid())

    expired_att = TrustAttestation(
        subject_lct="bob",
        attesting_org="a",
        recipient_org="b",
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    check("T6.4 Expired attestation", not expired_att.is_valid())

    # ── T7: Permission Store ──
    print("\n── T7: Permission Store ──")

    store = PermissionStore()

    c1 = PermissionClaim(subject_lct="alice", permission="read:code", issuer_lct="admin", organization="acme")
    c2 = PermissionClaim(subject_lct="alice", permission="write:code", issuer_lct="admin", organization="acme")
    c3 = PermissionClaim(subject_lct="bob", permission="read:code", issuer_lct="admin", organization="acme")

    store.store_claim(c1)
    store.store_claim(c2)
    store.store_claim(c3)

    check("T7.1 Get claims alice", len(store.get_claims("alice", "acme")) == 2)
    check("T7.2 Get claims bob", len(store.get_claims("bob", "acme")) == 1)
    check("T7.3 Get claims unknown", len(store.get_claims("unknown", "acme")) == 0)
    check("T7.4 Get claim by ID", store.get_claim(c1.claim_id) is not None)

    # Attestations
    att1 = TrustAttestation(subject_lct="bob", attesting_org="alpha", recipient_org="beta", permissions=["read:data"])
    store.store_attestation(att1)
    check("T7.5 Get attestations", len(store.get_attestations("bob", "beta")) == 1)
    check("T7.6 No attestations for alice", len(store.get_attestations("alice", "beta")) == 0)

    # ── T8: Authorization Engine - Basic ──
    print("\n── T8: Authorization Engine - Basic ──")

    engine = AuthorizationEngine()
    engine.register_entity("alice", atp_balance=200)
    engine.register_entity("bob", atp_balance=100)
    engine.register_entity("admin", atp_balance=500)

    # Set reputation
    engine.reputation_service.set_t3("alice", "acme", 0.75)  # Expert
    engine.reputation_service.set_t3("bob", "acme", 0.4)     # Developing
    engine.reputation_service.set_t3("admin", "acme", 0.95)  # Master

    # Reputation-based permissions
    auth_alice, reason = engine.is_authorized("alice", "read", "code", "acme")
    check("T8.1 Alice (expert) can read code", auth_alice)

    auth_bob_code, _ = engine.is_authorized("bob", "read", "code", "acme")
    check("T8.2 Bob (developing) can't read code", not auth_bob_code)

    auth_bob_public, _ = engine.is_authorized("bob", "read", "public_docs", "acme")
    check("T8.3 Bob can read public docs", auth_bob_public)

    auth_admin, _ = engine.is_authorized("admin", "admin", "anything", "acme")
    check("T8.4 Admin (master) has admin:*", auth_admin)

    # Unknown entity
    auth_unknown, reason = engine.is_authorized("unknown", "read", "code", "acme")
    check("T8.5 Unknown entity denied", not auth_unknown)
    check("T8.6 Reason: identity not found", "not found" in reason)

    # ── T9: Permission Granting ──
    print("\n── T9: Permission Granting ──")

    # Admin grants permission to bob
    claim_granted, msg = engine.grant_permission(
        issuer_lct="admin",
        subject_lct="bob",
        permission="read:code",
        organization="acme",
    )
    check("T9.1 Grant succeeded", claim_granted is not None)
    check("T9.2 Grant message", msg == "Permission granted")

    # Bob can now read code
    auth_bob_after, _ = engine.is_authorized("bob", "read", "code", "acme")
    check("T9.3 Bob can read code after grant", auth_bob_after)

    # ATP cost deducted
    check("T9.4 ATP deducted from issuer",
          engine.atp_balances["admin"] == 500 - engine.ATP_GRANT_COST)

    # Self-grant prevention
    self_claim, self_msg = engine.grant_permission("alice", "alice", "admin:*", "acme")
    check("T9.5 Self-grant blocked", self_claim is None)
    check("T9.6 Self-grant reason", "self" in self_msg.lower())

    # Grant with expiry
    claim_exp, _ = engine.grant_permission("admin", "bob", "write:data", "acme", expires_hours=1.0)
    check("T9.7 Expiring grant created", claim_exp is not None)
    check("T9.8 Expiry set", claim_exp.expires_at is not None)

    # Unauthorized grant attempt
    bad_claim, bad_msg = engine.grant_permission("bob", "alice", "admin:*", "acme")
    check("T9.9 Unauthorized grant blocked", bad_claim is None)

    # Grant to unknown subject
    unknown_claim, unknown_msg = engine.grant_permission("admin", "nobody", "read:code", "acme")
    check("T9.10 Unknown subject blocked", unknown_claim is None)
    check("T9.11 Subject not found reason", "not found" in unknown_msg.lower())

    # ── T10: Permission Revocation ──
    print("\n── T10: Permission Revocation ──")

    # Grant a permission first
    test_claim, _ = engine.grant_permission("admin", "alice", "execute:deploy:staging", "acme")
    check("T10.1 Test claim granted", test_claim is not None)

    # Verify it works
    auth_pre, _ = engine.is_authorized("alice", "execute", "deploy:staging", "acme")
    check("T10.2 Permission works before revocation", auth_pre)

    # Revoke
    revoked, rev_msg = engine.revoke_permission("admin", test_claim.claim_id, "Testing revocation")
    check("T10.3 Revocation succeeded", revoked)
    check("T10.4 Claim marked revoked", test_claim.revoked)
    check("T10.5 Revocation reason set", test_claim.revocation_reason == "Testing revocation")
    check("T10.6 Revocation timestamp set", test_claim.revoked_at is not None)

    # Original issuer can also revoke
    claim2, _ = engine.grant_permission("admin", "bob", "write:reports", "acme")
    revoked2, _ = engine.revoke_permission("admin", claim2.claim_id, "issuer revokes")
    check("T10.7 Issuer can revoke own grant", revoked2)

    # Unauthorized revocation
    claim3, _ = engine.grant_permission("admin", "bob", "execute:tests", "acme")
    bad_rev, bad_reason = engine.revoke_permission("bob", claim3.claim_id, "trying")
    check("T10.8 Unauthorized revocation blocked", not bad_rev)

    # Non-existent claim
    no_rev, no_reason = engine.revoke_permission("admin", "nonexistent", "test")
    check("T10.9 Non-existent claim", not no_rev)

    # ── T11: Cross-Organization Authorization ──
    print("\n── T11: Cross-Organization Authorization ──")

    # Setup cross-org
    engine.register_entity("cross_user")
    engine.reputation_service.set_t3("cross_user", "org_alpha", 0.8)
    engine.reputation_service.set_t3("cross_user", "org_beta", 0.3)

    # Direct auth in alpha
    auth_alpha, _ = engine.is_authorized("cross_user", "read", "code", "org_alpha")
    check("T11.1 Direct auth in org_alpha", auth_alpha)

    # No direct auth in beta (low rep)
    auth_beta, _ = engine.is_authorized("cross_user", "read", "code", "org_beta")
    check("T11.2 No direct auth in org_beta", not auth_beta)

    # Add cross-org attestation
    att = TrustAttestation(
        subject_lct="cross_user",
        attesting_org="org_alpha",
        recipient_org="org_beta",
        permissions=["read:code", "read:data"],
    )
    engine.permission_store.store_attestation(att)

    # Cross-org auth now works
    cross_auth, cross_reason = engine.cross_org_authorize("cross_user", "read", "code", "org_beta")
    check("T11.3 Cross-org auth succeeds", cross_auth)
    check("T11.4 Attested by org_alpha", "org_alpha" in cross_reason)

    # Non-attested action still denied
    cross_deny, _ = engine.cross_org_authorize("cross_user", "write", "code", "org_beta")
    check("T11.5 Non-attested action denied", not cross_deny)

    # ── T12: Blocked Agents ──
    print("\n── T12: Blocked Agents ──")

    engine.register_entity("bad_actor")
    engine.reputation_service.set_t3("bad_actor", "acme", 0.8)
    engine.org_service.block("bad_actor", "acme")

    auth_blocked, reason = engine.is_authorized("bad_actor", "read", "public_docs", "acme")
    check("T12.1 Blocked agent denied", not auth_blocked)
    check("T12.2 Blocked reason", "blocked" in reason.lower())

    # ── T13: Society Authorization ──
    print("\n── T13: Society Authorization ──")

    society_engine = AuthorizationEngine()
    society_engine.register_entity("agent1")
    society_engine.register_entity("agent2")
    society_engine.register_entity("agent3")
    society_engine.reputation_service.set_t3("agent1", "society_alpha", 0.6)
    society_engine.reputation_service.set_t3("agent2", "society_alpha", 0.05)
    society_engine.reputation_service.set_t3("agent3", "society_alpha", 0.8)

    society = SocietyAuthorization("society_alpha", society_engine)

    # Join checks
    can_join1, _ = society.agent_can_join("agent1")
    check("T13.1 Agent1 can join (rep 0.6)", can_join1)

    can_join2, reason2 = society.agent_can_join("agent2")
    check("T13.2 Agent2 can't join (rep 0.05)", not can_join2)
    check("T13.3 Low rep reason", "too low" in reason2.lower())

    # Block agent3
    society_engine.org_service.block("agent3", "society_alpha")
    can_join3, reason3 = society.agent_can_join("agent3")
    check("T13.4 Blocked agent can't join", not can_join3)

    # Witness checks - agent1 not enough experience
    can_witness1, reason_w1 = society.agent_can_witness("agent1")
    check("T13.5 Agent1 can't witness (no experience)", not can_witness1)

    # Add experience
    for _ in range(5):
        society.record_witness("agent1")
    can_witness1b, _ = society.agent_can_witness("agent1")
    check("T13.6 Agent1 can witness after experience", can_witness1b)

    # ── T14: Audit Trail ──
    print("\n── T14: Audit Trail ──")

    audit_engine = AuthorizationEngine()
    audit_engine.register_entity("alice")
    audit_engine.register_entity("admin")
    audit_engine.reputation_service.set_t3("alice", "org", 0.6)
    audit_engine.reputation_service.set_t3("admin", "org", 0.95)

    # Various operations
    audit_engine.is_authorized("alice", "read", "code", "org")
    audit_engine.is_authorized("alice", "admin", "server", "org")
    audit_engine.grant_permission("admin", "alice", "write:data", "org")

    check("T14.1 Audit entries recorded", len(audit_engine.audit_log) >= 3)

    # Check audit has required fields
    for entry in audit_engine.audit_log:
        check(f"T14.2 Audit has operation: {entry.operation}", entry.operation in ["check", "grant", "revoke"])
        check(f"T14.3 Audit has result: {entry.result}", entry.result in ["allowed", "denied", "granted", "revoked"])
        check("T14.4 Audit has timestamp", entry.timestamp is not None)

    # Grant audit has ATP cost
    grant_entries = [e for e in audit_engine.audit_log if e.operation == "grant"]
    check("T14.5 Grant entries exist", len(grant_entries) > 0)
    if grant_entries:
        check("T14.6 Grant has ATP cost", grant_entries[0].atp_cost > 0)

    # ── T15: Permission Freshness ──
    print("\n── T15: Permission Freshness ──")

    fresh_engine = AuthorizationEngine()
    fresh_engine.register_entity("admin")
    fresh_engine.register_entity("alice")
    fresh_engine.reputation_service.set_t3("admin", "org", 0.95)

    claim_fresh, _ = fresh_engine.grant_permission("admin", "alice", "read:data", "org", expires_hours=24)
    checker = FreshnessChecker(fresh_engine)

    is_fresh, reason = checker.verify_fresh(claim_fresh)
    check("T15.1 Fresh claim valid", is_fresh)

    # Expired claim
    expired_claim = PermissionClaim(
        subject_lct="alice",
        permission="old:perm",
        issuer_lct="admin",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    is_exp, exp_reason = checker.verify_fresh(expired_claim)
    check("T15.2 Expired claim not fresh", not is_exp)
    check("T15.3 Expired reason", "expired" in exp_reason.lower())

    # Revoked claim
    revoked_claim = PermissionClaim(
        subject_lct="alice",
        permission="revoked:perm",
        issuer_lct="admin",
        revoked=True,
        revocation_reason="test",
    )
    is_rev, rev_reason = checker.verify_fresh(revoked_claim)
    check("T15.4 Revoked claim not fresh", not is_rev)
    check("T15.5 Revoked reason", "revoked" in rev_reason.lower())

    # Inactive issuer
    inactive_claim = PermissionClaim(
        subject_lct="alice",
        permission="ghost:perm",
        issuer_lct="ghost_admin",  # Not registered
    )
    is_inactive, inactive_reason = checker.verify_fresh(inactive_claim)
    check("T15.6 Inactive issuer not fresh", not is_inactive)
    check("T15.7 Inactive reason", "active" in inactive_reason.lower())

    # ── T16: Reputation-Based Dynamic Permissions ──
    print("\n── T16: Reputation-Based Dynamic Permissions ──")

    dyn_engine = AuthorizationEngine()
    dyn_engine.register_entity("agent_dyn")

    # Start as novice
    dyn_engine.reputation_service.set_t3("agent_dyn", "org", 0.2)
    auth_novice, _ = dyn_engine.is_authorized("agent_dyn", "read", "code", "org")
    check("T16.1 Novice can't read code", not auth_novice)

    # Upgrade to trusted
    dyn_engine.reputation_service.set_t3("agent_dyn", "org", 0.55)
    auth_trusted, _ = dyn_engine.is_authorized("agent_dyn", "read", "code", "org")
    check("T16.2 Trusted can read code", auth_trusted)

    # Upgrade to expert
    dyn_engine.reputation_service.set_t3("agent_dyn", "org", 0.75)
    auth_expert, _ = dyn_engine.is_authorized("agent_dyn", "execute", "deploy:staging", "org")
    check("T16.3 Expert can deploy staging", auth_expert)

    # Downgrade back to developing
    dyn_engine.reputation_service.set_t3("agent_dyn", "org", 0.35)
    auth_downgraded, _ = dyn_engine.is_authorized("agent_dyn", "execute", "deploy:staging", "org")
    check("T16.4 Developing can't deploy staging", not auth_downgraded)

    # ── T17: ATP Budget for Grants ──
    print("\n── T17: ATP Budget for Grants ──")

    atp_engine = AuthorizationEngine()
    atp_engine.register_entity("poor_admin", atp_balance=5.0)
    atp_engine.register_entity("rich_admin", atp_balance=500.0)
    atp_engine.register_entity("target")
    atp_engine.reputation_service.set_t3("poor_admin", "org", 0.95)
    atp_engine.reputation_service.set_t3("rich_admin", "org", 0.95)

    # Poor admin can't grant
    poor_claim, poor_msg = atp_engine.grant_permission("poor_admin", "target", "read:data", "org")
    check("T17.1 Insufficient ATP blocks grant", poor_claim is None)
    check("T17.2 ATP reason", "insufficient" in poor_msg.lower())

    # Rich admin can grant
    rich_claim, rich_msg = atp_engine.grant_permission("rich_admin", "target", "read:data", "org")
    check("T17.3 Sufficient ATP allows grant", rich_claim is not None)
    check("T17.4 ATP deducted", atp_engine.atp_balances["rich_admin"] == 490.0)

    # Multiple grants drain ATP (490 remaining / 10 per grant = 49 more grants)
    for i in range(49):
        atp_engine.grant_permission("rich_admin", "target", f"perm:{i}", "org")
    check("T17.5 ATP fully drained", atp_engine.atp_balances["rich_admin"] == 0.0)

    # Next grant fails
    drained_claim, _ = atp_engine.grant_permission("rich_admin", "target", "last:perm", "org")
    check("T17.6 Drained admin can't grant", drained_claim is None)

    # ── T18: Permission Hierarchy Wildcards ──
    print("\n── T18: Permission Hierarchy Wildcards ──")

    wild_engine = AuthorizationEngine()
    wild_engine.register_entity("user_wild")
    wild_engine.reputation_service.set_t3("user_wild", "org", 0.6)

    # Grant wildcard
    wild_engine.register_entity("admin_wild")
    wild_engine.reputation_service.set_t3("admin_wild", "org", 0.95)
    wild_engine.grant_permission("admin_wild", "user_wild", "read:*", "org")

    # Wildcard matches any resource
    auth_wild1, _ = wild_engine.is_authorized("user_wild", "read", "code", "org")
    check("T18.1 Wildcard matches code", auth_wild1)

    auth_wild2, _ = wild_engine.is_authorized("user_wild", "read", "data", "org")
    check("T18.2 Wildcard matches data", auth_wild2)

    auth_wild3, _ = wild_engine.is_authorized("user_wild", "read", "anything", "org")
    check("T18.3 Wildcard matches anything", auth_wild3)

    # Wildcard doesn't match different action
    auth_wild4, _ = wild_engine.is_authorized("user_wild", "write", "code", "org")
    check("T18.4 Wildcard doesn't cross actions", not auth_wild4)

    # ── T19: Conditional Permissions ──
    print("\n── T19: Conditional Permissions ──")

    cond_engine = AuthorizationEngine()
    cond_engine.register_entity("cond_user")
    cond_engine.register_entity("cond_admin")
    cond_engine.reputation_service.set_t3("cond_admin", "org", 0.95)
    cond_engine.reputation_service.set_t3("cond_user", "org", 0.6)

    # Grant with condition
    cond_claim, _ = cond_engine.grant_permission(
        "cond_admin", "cond_user", "write:production_db", "org",
        conditions=["T3 >= 0.5"],
    )
    check("T19.1 Conditional grant created", cond_claim is not None)
    check("T19.2 Condition stored", len(cond_claim.conditions) == 1)

    # Condition parsing
    parsed = cond_engine._parse_condition("T3 >= 0.5")
    check("T19.3 Condition parsed", parsed is not None)
    check("T19.4 Condition type", parsed.condition_type == "reputation")
    check("T19.5 Condition operator", parsed.operator == ">=")
    check("T19.6 Condition value", parsed.value == 0.5)

    # ── T20: Multiple Organizations ──
    print("\n── T20: Multiple Organizations ──")

    multi_engine = AuthorizationEngine()
    multi_engine.register_entity("multi_user")
    multi_engine.register_entity("admin_a")
    multi_engine.register_entity("admin_b")
    multi_engine.reputation_service.set_t3("multi_user", "org_a", 0.8)
    multi_engine.reputation_service.set_t3("multi_user", "org_b", 0.3)
    multi_engine.reputation_service.set_t3("admin_a", "org_a", 0.95)
    multi_engine.reputation_service.set_t3("admin_b", "org_b", 0.95)

    # Expert in org_a
    auth_a, _ = multi_engine.is_authorized("multi_user", "write", "code:shared", "org_a")
    check("T20.1 Expert in org_a can write shared", auth_a)

    # Developing in org_b
    auth_b, _ = multi_engine.is_authorized("multi_user", "write", "code:shared", "org_b")
    check("T20.2 Developing in org_b can't write shared", not auth_b)

    # Grant in org_a doesn't affect org_b
    multi_engine.grant_permission("admin_a", "multi_user", "execute:special", "org_a")
    auth_a_special, _ = multi_engine.is_authorized("multi_user", "execute", "special", "org_a")
    check("T20.3 Grant works in org_a", auth_a_special)

    auth_b_special, _ = multi_engine.is_authorized("multi_user", "execute", "special", "org_b")
    check("T20.4 Grant doesn't work in org_b", not auth_b_special)

    # ── T21: Edge Cases ──
    print("\n── T21: Edge Cases ──")

    edge_engine = AuthorizationEngine()
    edge_engine.register_entity("edge_user")
    edge_engine.register_entity("edge_admin")
    edge_engine.reputation_service.set_t3("edge_admin", "org", 0.95)
    edge_engine.reputation_service.set_t3("edge_user", "org", 0.5)

    # Empty permission string
    auth_empty, _ = edge_engine.is_authorized("edge_user", "", "", "org")
    check("T21.1 Empty permission denied", not auth_empty)

    # Very long permission string
    long_perm = "read:" + "x" * 1000
    edge_engine.grant_permission("edge_admin", "edge_user", long_perm, "org")
    auth_long, _ = edge_engine.is_authorized("edge_user", "read", "x" * 1000, "org")
    check("T21.2 Long permission string works", auth_long)

    # Multiple claims for same permission (should still work)
    edge_engine.grant_permission("edge_admin", "edge_user", "read:special", "org")
    edge_engine.grant_permission("edge_admin", "edge_user", "read:special", "org")
    auth_dup, _ = edge_engine.is_authorized("edge_user", "read", "special", "org")
    check("T21.3 Duplicate claims still work", auth_dup)

    # T3 boundary: exactly 0.0
    edge_engine.reputation_service.set_t3("edge_user", "zero_org", 0.0)
    perms_zero = edge_engine.get_reputation_permissions(0.0)
    check("T21.4 T3=0 gets novice permissions", "read:public_docs" in perms_zero)
    check("T21.5 T3=0 doesn't get code read", "read:code" not in perms_zero)

    # T3 boundary: exactly 1.0
    perms_max = edge_engine.get_reputation_permissions(1.0)
    check("T21.6 T3=1.0 gets master permissions", "admin:org:*" in perms_max)

    # ── T22: Comprehensive Flow ──
    print("\n── T22: Comprehensive Flow ──")

    flow_engine = AuthorizationEngine()

    # Setup entities
    flow_engine.register_entity("human_admin", 1000)
    flow_engine.register_entity("sage_agent", 200)
    flow_engine.register_entity("irp_plugin", 50)
    flow_engine.reputation_service.set_t3("human_admin", "society", 0.95)
    flow_engine.reputation_service.set_t3("sage_agent", "society", 0.7)
    flow_engine.reputation_service.set_t3("irp_plugin", "society", 0.4)

    # Admin grants to SAGE
    sage_claim, _ = flow_engine.grant_permission(
        "human_admin", "sage_agent", "execute:compute", "society",
        expires_hours=24,
    )
    check("T22.1 Admin grants to SAGE", sage_claim is not None)

    # SAGE can execute compute
    sage_auth, _ = flow_engine.is_authorized("sage_agent", "execute", "compute", "society")
    check("T22.2 SAGE can compute", sage_auth)

    # IRP plugin has only developing permissions
    irp_auth, _ = flow_engine.is_authorized("irp_plugin", "execute", "compute", "society")
    check("T22.3 IRP plugin can't compute (no grant)", not irp_auth)

    # Admin grants to IRP
    irp_claim, _ = flow_engine.grant_permission(
        "human_admin", "irp_plugin", "execute:compute", "society",
    )
    irp_auth2, _ = flow_engine.is_authorized("irp_plugin", "execute", "compute", "society")
    check("T22.4 IRP can compute after grant", irp_auth2)

    # Revoke IRP permission
    flow_engine.revoke_permission("human_admin", irp_claim.claim_id, "Session ended")
    irp_auth3, _ = flow_engine.is_authorized("irp_plugin", "execute", "compute", "society")
    check("T22.5 IRP can't compute after revocation", not irp_auth3)

    # Full audit trail
    audit_count = len(flow_engine.audit_log)
    check("T22.6 Audit trail recorded", audit_count >= 5)

    # Verify audit has grants, checks, revocations
    ops = set(e.operation for e in flow_engine.audit_log)
    check("T22.7 Audit has check ops", "check" in ops)
    check("T22.8 Audit has grant ops", "grant" in ops)
    check("T22.9 Audit has revoke ops", "revoke" in ops)

    # ── Summary ──
    print(f"\n{'='*60}")
    print(f"LCT Authorization System: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  {failed} FAILED")
    print(f"{'='*60}")
    return passed, total


if __name__ == "__main__":
    run_tests()
