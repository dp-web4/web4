# WEB4-AUTH-001: LCT-Based Authorization System

**Status**: Draft Proposal
**Created**: 2025-11-13 (Session #21)
**Authors**: Web4 Autonomous Research
**Epistemic Status**: POSTULATED (design phase, not yet implemented)

---

## Abstract

This proposal defines an authorization system built on LCT (Legible Coordinate Transform) identities, enabling AI agents to make trust-based access control decisions in decentralized environments. The system combines cryptographic identity verification with reputation-based trust assessment to answer: "What is this agent allowed to do?"

---

## Motivation

**Problem**: LCTs prove *who* an agent is, but not *what* they're allowed to do.

**Current State**:
- ✅ LCT identity system: VALIDATED (Session #21)
- ✅ Cryptographic verification: VALIDATED
- ❌ Authorization framework: Not implemented
- ❌ Permission delegation: Not designed
- ❌ Trust-based access control: Theoretical only

**Goal**: Enable ACT societies to make authorization decisions based on:
1. Cryptographic identity (LCT)
2. Reputation/trust (T3 tensor)
3. Organizational membership
4. Explicit permissions

---

## Design Principles

### 1. Identity ≠ Authorization

**Separation of Concerns**:
- Identity answers: "Who are you?" (LCT)
- Authorization answers: "What can you do?" (Permissions)

**Example**:
```
Agent A has LCT: lct:ai:agent_alpha
Agent A has Role: developer
Agent A has Permissions: [read_code, write_tests, deploy_staging]
```

### 2. Trust-Based Access Control

**Reputation Influences Permissions**:
- High T3 score → More permissions
- Low T3 score → Restricted permissions
- Zero T3 score (new agent) → Minimal permissions

**Dynamic Adjustment**:
- Permissions change as reputation changes
- Bad behavior reduces permissions automatically
- Good behavior unlocks new capabilities

### 3. Explicit > Implicit

**No Magic Permissions**:
- All permissions must be explicitly granted
- Default is deny (whitelist, not blacklist)
- Permissions are auditable and revocable

### 4. Decentralized Authority

**No Central Permission Server**:
- Permissions stored in distributed claims
- Organizations grant permissions independently
- Cross-org authorization via attestations

---

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────┐
│                Authorization System                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────┐│
│  │ LCT Identity │  │  Reputation   │  │Permission││
│  │   Service    │──│   Service     │──│ Manager  ││
│  │              │  │   (T3)        │  │          ││
│  └──────────────┘  └───────────────┘  └──────────┘│
│         │                 │                  │     │
│         └─────────────────┴──────────────────┘     │
│                           │                        │
│                  ┌────────▼────────┐              │
│                  │  Authorization  │              │
│                  │     Engine      │              │
│                  └────────┬────────┘              │
│                           │                        │
│                  ┌────────▼────────┐              │
│                  │  Access Control │              │
│                  │    Decision     │              │
│                  └─────────────────┘              │
└─────────────────────────────────────────────────────┘
```

### Data Structures

#### Permission Claim

```python
@dataclass
class PermissionClaim:
    """Cryptographically signed permission grant"""

    # Who is granted permission
    subject_lct: str  # LCT ID of agent receiving permission

    # What permission is granted
    permission: str  # e.g., "read:repository", "write:database"
    resource: Optional[str]  # Specific resource or "*" for all

    # Who grants permission
    issuer_lct: str  # LCT ID of granting authority (org or admin)
    organization: str  # Organization context

    # When is it valid
    issued_at: datetime
    expires_at: Optional[datetime]  # None = does not expire

    # How was it granted
    conditions: List[str]  # e.g., ["T3 > 0.5", "within_organization"]

    # Cryptographic proof
    claim_hash: str  # Hash of claim content
    signature: str  # Ed25519 signature by issuer

    # Revocation
    revoked: bool = False
    revoked_at: Optional[datetime] = None
    revocation_reason: Optional[str] = None
```

#### Permission Bundle

```python
@dataclass
class PermissionBundle:
    """Collection of permissions for an agent"""

    lct_id: str  # Agent's LCT identity
    claims: List[PermissionClaim]  # All permission claims

    # Aggregated permissions (computed from claims)
    effective_permissions: Dict[str, List[str]]  # resource -> [permissions]

    # Reputation context
    t3_score: float  # Current trust score
    reputation_level: str  # e.g., "novice", "trusted", "expert"

    # Organizational context
    organizations: List[str]  # Organizations agent belongs to
    roles: List[str]  # Roles within organizations

    # Metadata
    last_updated: datetime
    permission_count: int
```

---

## Permission Model

### Permission Format

**Syntax**: `<action>:<resource>[:<scope>]`

**Examples**:
```
read:code                   # Read any code
write:code:own              # Write own code only
execute:deploy:staging      # Deploy to staging environment
mint:lct:ai                 # Mint AI-type LCTs
manage:reputation:self      # Manage own reputation
admin:org:acme_corp         # Admin rights in acme_corp organization
```

### Permission Hierarchy

```
admin:*                     # All permissions
  ├── read:*                # All read permissions
  │   ├── read:code
  │   ├── read:data
  │   └── read:logs
  ├── write:*               # All write permissions
  │   ├── write:code
  │   ├── write:data
  │   └── write:config
  └── execute:*             # All execute permissions
      ├── execute:tests
      ├── execute:deploy
      └── execute:admin_tasks
```

### Standard Permission Sets

#### Novice Agent (T3 < 0.3)
```python
NOVICE_PERMISSIONS = [
    "read:public_docs",
    "write:own_profile",
    "execute:basic_tests"
]
```

#### Trusted Agent (T3 >= 0.5)
```python
TRUSTED_PERMISSIONS = NOVICE_PERMISSIONS + [
    "read:code",
    "write:code:own",
    "execute:unit_tests",
    "witness:lct:ai"  # Can witness AI LCT creation
]
```

#### Expert Agent (T3 >= 0.8)
```python
EXPERT_PERMISSIONS = TRUSTED_PERMISSIONS + [
    "write:code:shared",
    "execute:integration_tests",
    "execute:deploy:staging",
    "witness:lct:*"  # Can witness any LCT type
]
```

#### Admin Agent (explicit grant only)
```python
ADMIN_PERMISSIONS = EXPERT_PERMISSIONS + [
    "admin:org:*",
    "mint:lct:*",
    "grant:permissions:*",
    "execute:deploy:production"
]
```

---

## Authorization Flow

### 1. Identity Verification

```python
def verify_identity(lct_id: str, signature: str, message: str) -> bool:
    """
    Verify agent's cryptographic identity.

    Returns True if signature is valid for this LCT.
    """
    lct = lct_registry.get_lct(lct_id)
    public_key = lct.public_key_bytes

    return verify_ed25519(public_key, message, signature)
```

### 2. Permission Lookup

```python
def get_permissions(lct_id: str, organization: str) -> PermissionBundle:
    """
    Get all permissions for an agent in a given organization.

    Combines:
    - Explicit permission claims
    - Role-based permissions
    - Reputation-based permissions
    """
    # Get explicit claims
    claims = permission_store.get_claims(lct_id, organization)

    # Get reputation
    t3_score = reputation_service.get_t3(lct_id, organization)

    # Get role-based permissions
    roles = org_service.get_roles(lct_id, organization)
    role_permissions = [get_role_permissions(role) for role in roles]

    # Get reputation-based permissions
    rep_level = get_reputation_level(t3_score)
    rep_permissions = get_reputation_permissions(rep_level)

    # Combine all permissions
    effective_permissions = combine_permissions(
        claims, role_permissions, rep_permissions
    )

    return PermissionBundle(
        lct_id=lct_id,
        claims=claims,
        effective_permissions=effective_permissions,
        t3_score=t3_score,
        reputation_level=rep_level,
        organizations=[organization],
        roles=roles,
        last_updated=datetime.now(timezone.utc),
        permission_count=len(effective_permissions)
    )
```

### 3. Authorization Decision

```python
def is_authorized(
    lct_id: str,
    action: str,
    resource: str,
    organization: str
) -> tuple[bool, str]:
    """
    Make authorization decision.

    Returns:
        (authorized: bool, reason: str)
    """
    # Verify identity exists
    lct = lct_registry.get_lct(lct_id)
    if not lct:
        return False, "Identity not found"

    # Get permissions
    permissions = get_permissions(lct_id, organization)

    # Check if action is allowed
    permission_string = f"{action}:{resource}"

    # Check exact match
    if permission_string in permissions.effective_permissions:
        return True, "Explicit permission granted"

    # Check wildcard match
    action_wildcard = f"{action}:*"
    if action_wildcard in permissions.effective_permissions:
        return True, "Wildcard permission granted"

    # Check admin permissions
    if "admin:*" in permissions.effective_permissions:
        return True, "Admin permission granted"

    # Check conditions (e.g., reputation threshold)
    if check_conditions(permissions, action, resource):
        return True, "Conditional permission met"

    # Default deny
    return False, "No matching permission"
```

---

## Permission Granting

### Grant Flow

```python
@dataclass
class GrantPermissionRequest:
    """Request to grant permission"""
    subject_lct: str  # Who receives permission
    permission: str  # What permission
    resource: Optional[str]  # Which resource
    organization: str  # In which org
    expires_at: Optional[datetime]  # When it expires
    conditions: List[str]  # Any conditions

    # Requestor (must have grant permission)
    issuer_lct: str
    issuer_signature: str


async def grant_permission(request: GrantPermissionRequest) -> PermissionClaim:
    """
    Grant permission to an agent.

    Authorization: Issuer must have "grant:permissions:*" permission
    """
    # Verify issuer has permission to grant
    issuer_can_grant = is_authorized(
        lct_id=request.issuer_lct,
        action="grant",
        resource=f"permissions:{request.permission}",
        organization=request.organization
    )

    if not issuer_can_grant:
        raise PermissionError("Issuer not authorized to grant permissions")

    # Verify subject exists
    subject_lct = lct_registry.get_lct(request.subject_lct)
    if not subject_lct:
        raise ValueError("Subject LCT not found")

    # Create claim
    claim = PermissionClaim(
        subject_lct=request.subject_lct,
        permission=request.permission,
        resource=request.resource or "*",
        issuer_lct=request.issuer_lct,
        organization=request.organization,
        issued_at=datetime.now(timezone.utc),
        expires_at=request.expires_at,
        conditions=request.conditions,
        claim_hash=compute_claim_hash(...),
        signature=sign_claim(request.issuer_lct, ...)
    )

    # Store claim
    permission_store.store_claim(claim)

    # Update ATP (granting costs ATP)
    atp_manager.deduct(
        entity_id=request.issuer_lct,
        amount=ATP_GRANT_PERMISSION_COST,
        transaction_type=TransactionType.GRANT_PERMISSION
    )

    return claim
```

---

## Reputation-Based Authorization

### Dynamic Permission Adjustment

```python
def get_reputation_permissions(t3_score: float) -> List[str]:
    """
    Get permissions based on reputation score.

    T3 ranges:
    - 0.0-0.3: Novice
    - 0.3-0.5: Developing
    - 0.5-0.7: Trusted
    - 0.7-0.9: Expert
    - 0.9-1.0: Master
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
```

### Reputation Threshold Conditions

```python
@dataclass
class PermissionCondition:
    """Condition that must be met for permission to apply"""

    condition_type: str  # "reputation", "time", "count"
    operator: str  # ">", "<", ">=", "<=", "=="
    value: Any  # Threshold value

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Check if condition is met"""
        if self.condition_type == "reputation":
            t3_score = context.get("t3_score", 0.0)
            return self._compare(t3_score, self.operator, self.value)
        # ... other condition types


# Example: Permission that requires T3 > 0.5
HIGH_TRUST_WRITE = PermissionClaim(
    subject_lct="lct:ai:agent_alpha",
    permission="write:production_db",
    conditions=["T3 >= 0.5", "within_org:acme"]
)
```

---

## Cross-Organization Authorization

### Trust Attestations

```python
@dataclass
class TrustAttestation:
    """One organization attests to another org about an agent"""

    subject_lct: str  # Agent being attested
    attesting_org: str  # Organization making attestation
    recipient_org: str  # Organization receiving attestation

    trust_level: str  # "novice", "trusted", "expert"
    permissions: List[str]  # Permissions attested org vouches for

    # Cryptographic proof
    attestation_hash: str
    signature: str  # Signed by attesting org's admin LCT

    issued_at: datetime
    expires_at: Optional[datetime]


async def cross_org_authorize(
    lct_id: str,
    action: str,
    resource: str,
    requesting_org: str
) -> tuple[bool, str]:
    """
    Authorize action across organizations using attestations.
    """
    # Check direct permissions in requesting org
    direct = is_authorized(lct_id, action, resource, requesting_org)
    if direct[0]:
        return direct

    # Check for trust attestations from other orgs
    attestations = trust_service.get_attestations(lct_id, recipient_org=requesting_org)

    for attestation in attestations:
        # Check if attested permissions include requested action
        if f"{action}:{resource}" in attestation.permissions:
            # Verify attestation signature
            if verify_attestation(attestation):
                return True, f"Attested by {attestation.attesting_org}"

    return False, "No cross-org authorization found"
```

---

## Security Considerations

### 1. Permission Revocation

**Immediate Revocation**:
```python
async def revoke_permission(claim_id: str, reason: str, revoker_lct: str):
    """
    Immediately revoke a permission claim.

    Authorization: Revoker must have "admin:permissions" or be original issuer
    """
    claim = permission_store.get_claim(claim_id)

    # Check authorization to revoke
    can_revoke = (
        revoker_lct == claim.issuer_lct or
        is_authorized(revoker_lct, "admin", "permissions", claim.organization)[0]
    )

    if not can_revoke:
        raise PermissionError("Not authorized to revoke")

    # Mark as revoked
    claim.revoked = True
    claim.revoked_at = datetime.now(timezone.utc)
    claim.revocation_reason = reason

    permission_store.update_claim(claim)

    # Log revocation
    audit_log.record_revocation(claim_id, revoker_lct, reason)
```

### 2. Permission Escalation Prevention

**No Self-Granting**:
- Agents cannot grant permissions to themselves
- Requires separate admin with grant authority

**Audit Trail**:
- All permission grants logged
- Cryptographic signatures prevent forgery
- Revocation history maintained

**Reputation Requirement**:
- Low T3 agents have minimal permissions
- High-risk permissions require high T3 threshold

### 3. Replay Attack Prevention

**Time-based Validity**:
```python
def verify_permission_fresh(claim: PermissionClaim) -> bool:
    """Check if permission is still valid"""
    now = datetime.now(timezone.utc)

    # Check expiration
    if claim.expires_at and now > claim.expires_at:
        return False

    # Check revocation
    if claim.revoked:
        return False

    # Check issuer LCT still exists and is active
    issuer_lct = lct_registry.get_lct(claim.issuer_lct)
    if not issuer_lct or issuer_lct.status != "active":
        return False

    return True
```

---

## Integration with ACT Societies

### Society-Level Authorization

```python
class ACTSocietyAuthorization:
    """Authorization system for ACT societies"""

    def __init__(self, society_id: str):
        self.society_id = society_id
        self.auth_system = AuthorizationEngine()

    async def agent_can_join(self, lct_id: str) -> tuple[bool, str]:
        """Check if agent can join society"""
        # Minimum reputation required
        t3_score = reputation_service.get_t3(lct_id)
        if t3_score < MIN_SOCIETY_REPUTATION:
            return False, f"Reputation too low ({t3_score:.2f} < {MIN_SOCIETY_REPUTATION})"

        # Check for bans/blocks
        if self.is_blocked(lct_id):
            return False, "Agent blocked from society"

        return True, "Authorized to join"

    async def agent_can_witness(self, lct_id: str) -> tuple[bool, str]:
        """Check if agent can witness LCT creation"""
        # Check explicit permission
        has_perm = self.auth_system.is_authorized(
            lct_id=lct_id,
            action="witness",
            resource="lct:*",
            organization=self.society_id
        )

        if not has_perm[0]:
            return has_perm

        # Check reputation threshold (from witness validation)
        t3_score = reputation_service.get_t3(lct_id)
        if t3_score < MIN_WITNESS_REPUTATION:
            return False, f"Reputation too low for witnessing ({t3_score:.2f})"

        # Check witness history
        witness_count = witness_service.get_witness_count(lct_id)
        if witness_count < MIN_WITNESS_ACTIONS:
            return False, f"Insufficient witness experience ({witness_count})"

        return True, "Authorized to witness"
```

---

## Epistemic Status

**Status**: POSTULATED (not yet implemented)

**What We Know**:
- ✅ LCT identity provides cryptographic foundation
- ✅ Ed25519 signatures can verify claims
- ✅ Reputation (T3) exists conceptually

**What We Don't Know**:
- ❓ Does permission model cover all use cases?
- ❓ Are reputation thresholds appropriate?
- ❓ Does cross-org authorization scale?
- ❓ Can we prevent permission escalation attacks?

**Falsification Criteria**:
- If agents can self-grant permissions → design failed
- If permission checks are too slow → unusable
- If reputation doesn't correlate with trustworthiness → wrong metric
- If cross-org auth is too complex → won't be adopted

**Next Steps**:
1. Implement PermissionClaim data structure
2. Prototype authorization engine in ACT
3. Test with real society scenarios
4. Measure performance (authorization latency)
5. Security audit for escalation vulnerabilities

---

## Open Questions

1. **Permission Storage**: Centralized DB or distributed claims?
2. **Performance**: Can we authorize in <10ms?
3. **Revocation**: How to ensure immediate effect?
4. **Delegation**: Should agents be able to delegate permissions?
5. **Expiration**: Default expiration time for permissions?
6. **Audit**: How detailed should audit logs be?
7. **Bootstrap**: How do first admins get permissions?

---

## References

- LCT Identity System: `web4-standard/implementation/reference/lct_registry.py`
- Phase 2 Security: `web4-standard/implementation/services/identity_service_phase2.py`
- Epistemic Framework: `private-context/WEB4_EPISTEMIC_STATUS_REGISTRY.md`
- ACT Societies: `ACT/` repository

---

**Status**: Draft proposal ready for implementation and testing in ACT

**Next**: Prototype authorization engine and test with ACT societies
