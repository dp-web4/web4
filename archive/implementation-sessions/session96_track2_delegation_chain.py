"""
SESSION 96 TRACK 2: AUTHORIZATION DELEGATION CHAIN

From AI Agent Accountability doc:
> "Identity Binding Hierarchy:
   Hardware Root → LCT Identity → Delegation Chain
     ├─ Human (direct action)
     └─ SAGE (delegated authority, scope-limited)
           └─ IRP Plugin (e.g., browser-automation-irp)"

This implements explicit authorization delegation with:
1. Permission tokens with scope limits (actions, resources, time bounds)
2. Delegation chain tracking (human → SAGE → plugin)
3. Revocation mechanisms (immediate and time-based)
4. Audit trails for accountability

Key innovations:
- DelegationToken: Cryptographically signed permission token
- ScopedPermission: Fine-grained action/resource authorization
- DelegationChain: Complete ancestry tracking
- RevocationList: Immediate delegation termination

Integration with:
- Track 1: Hardware-bound identity (issuer/delegate binding)
- Session 95: UnifiedLCTProfile (ATP budgets, reputation)
- AI Agent Accountability doc: Scope-limited delegation

Example delegation chain:
  Human (dennis@laptop)
    └─ SAGE instance (sage:main@mainnet)
          └─ IRP Plugin (sage:browser_automation@mainnet)
                └─ Action: navigate(url="https://...")

Each level has:
- Scope limits (what actions are allowed)
- Time bounds (expiration)
- Resource limits (ATP budget from Track 3)
- Revocation capability

References:
- OAuth 2.0 RFC 6749 (delegation patterns)
- SPIFFE/SPIRE (workload identity and delegation)
- Macaroons (decentralized authorization)
"""

import hashlib
import json
import secrets
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum


# ============================================================================
# SCOPED PERMISSIONS
# ============================================================================

class PermissionScope(Enum):
    """Predefined permission scopes for common operations."""
    # Browser automation
    BROWSER_NAVIGATE = "browser:navigate"
    BROWSER_CLICK = "browser:click"
    BROWSER_INPUT = "browser:input"
    BROWSER_SCREENSHOT = "browser:screenshot"

    # API operations
    API_READ = "api:read"
    API_WRITE = "api:write"
    API_DELETE = "api:delete"

    # File operations
    FILE_READ = "file:read"
    FILE_WRITE = "file:write"
    FILE_EXECUTE = "file:execute"

    # IRP operations
    IRP_INVOKE = "irp:invoke"
    IRP_REGISTER = "irp:register"
    IRP_QUERY = "irp:query"

    # Administrative
    ADMIN_DELEGATE = "admin:delegate"  # Can create sub-delegations
    ADMIN_REVOKE = "admin:revoke"      # Can revoke delegations


@dataclass
class ScopedPermission:
    """
    Fine-grained permission with action and resource constraints.

    Examples:
    - Action: "browser:navigate", Resource: "https://example.com/*"
    - Action: "api:read", Resource: "github.com/repos/*"
    - Action: "irp:invoke", Resource: "lct://sage:*@mainnet"
    """
    action: str  # Permission action (e.g., "browser:navigate")
    resource: str  # Resource pattern (supports wildcards)
    constraints: Dict[str, Any] = field(default_factory=dict)  # Additional constraints

    def matches(self, action: str, resource: str) -> bool:
        """
        Check if permission allows action on resource.

        Supports wildcard matching:
        - "https://example.com/*" matches "https://example.com/page"
        - "lct://sage:*@mainnet" matches "lct://sage:expert_a@mainnet"
        """
        # Check action
        if self.action != action:
            return False

        # Check resource (wildcard support)
        if "*" in self.resource:
            # Convert wildcard pattern to prefix match
            prefix = self.resource.split("*")[0]
            return resource.startswith(prefix)
        else:
            # Exact match
            return self.resource == resource

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "resource": self.resource,
            "constraints": self.constraints
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ScopedPermission":
        return ScopedPermission(
            action=data["action"],
            resource=data["resource"],
            constraints=data.get("constraints", {})
        )


# ============================================================================
# DELEGATION TOKEN
# ============================================================================

@dataclass
class DelegationToken:
    """
    Cryptographically signed authorization token.

    Token lifecycle:
    1. Issuer (human or delegator) creates token
    2. Delegate (SAGE or plugin) receives token
    3. Delegate uses token to authorize actions
    4. Token expires or is revoked
    """
    token_id: str  # Unique token identifier
    issuer: str  # LCT identity of issuer (who grants permission)
    delegate: str  # LCT identity of delegate (who receives permission)

    # Permissions
    permissions: List[ScopedPermission]

    # Time bounds
    issued_at: str
    expires_at: str
    not_before: Optional[str] = None  # Token not valid before this time

    # Revocation
    revoked: bool = False
    revoked_at: Optional[str] = None
    revocation_reason: Optional[str] = None

    # Signature (from issuer's hardware-bound key)
    signature: Optional[str] = None

    # Metadata
    delegation_depth: int = 0  # 0 = human, 1 = SAGE, 2 = plugin, etc.
    parent_token_id: Optional[str] = None  # Token that delegated to this one
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """Check if token is currently valid (not expired, not revoked)."""
        if self.revoked:
            return False

        now = datetime.now(timezone.utc)

        # Check expiration
        expires_at = datetime.fromisoformat(self.expires_at)
        if now > expires_at:
            return False

        # Check not_before
        if self.not_before:
            not_before = datetime.fromisoformat(self.not_before)
            if now < not_before:
                return False

        return True

    def can_perform(self, action: str, resource: str) -> bool:
        """Check if token allows action on resource."""
        if not self.is_valid:
            return False

        for permission in self.permissions:
            if permission.matches(action, resource):
                return True

        return False

    def revoke(self, reason: str = "user_requested"):
        """Revoke token (cannot be undone)."""
        self.revoked = True
        self.revoked_at = datetime.now(timezone.utc).isoformat()
        self.revocation_reason = reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_id": self.token_id,
            "issuer": self.issuer,
            "delegate": self.delegate,
            "permissions": [p.to_dict() for p in self.permissions],
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "not_before": self.not_before,
            "revoked": self.revoked,
            "revoked_at": self.revoked_at,
            "revocation_reason": self.revocation_reason,
            "signature": self.signature,
            "delegation_depth": self.delegation_depth,
            "parent_token_id": self.parent_token_id,
            "metadata": self.metadata
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "DelegationToken":
        return DelegationToken(
            token_id=data["token_id"],
            issuer=data["issuer"],
            delegate=data["delegate"],
            permissions=[ScopedPermission.from_dict(p) for p in data["permissions"]],
            issued_at=data["issued_at"],
            expires_at=data["expires_at"],
            not_before=data.get("not_before"),
            revoked=data.get("revoked", False),
            revoked_at=data.get("revoked_at"),
            revocation_reason=data.get("revocation_reason"),
            signature=data.get("signature"),
            delegation_depth=data.get("delegation_depth", 0),
            parent_token_id=data.get("parent_token_id"),
            metadata=data.get("metadata", {})
        )


# ============================================================================
# DELEGATION CHAIN
# ============================================================================

@dataclass
class DelegationChain:
    """
    Complete ancestry of delegation from human to current actor.

    Example chain:
      Human (dennis@laptop)
        ↓ token_abc123
      SAGE (sage:main@mainnet)
        ↓ token_def456
      Plugin (sage:browser_automation@mainnet)

    Chain properties:
    - Traceability: Full path from human to current actor
    - Scope narrowing: Each level has narrower permissions
    - Accountability: Any action traces back to human origin
    """
    tokens: List[DelegationToken]  # Ordered from root (human) to current

    @property
    def root_identity(self) -> str:
        """Get LCT identity of chain root (typically human)."""
        return self.tokens[0].issuer if self.tokens else ""

    @property
    def current_identity(self) -> str:
        """Get LCT identity of current delegate."""
        return self.tokens[-1].delegate if self.tokens else ""

    @property
    def depth(self) -> int:
        """Get delegation depth (0 = human, 1 = SAGE, etc.)."""
        return len(self.tokens)

    @property
    def is_valid(self) -> bool:
        """Check if entire chain is valid (all tokens valid)."""
        return all(token.is_valid for token in self.tokens)

    def get_effective_permissions(self) -> List[ScopedPermission]:
        """
        Get effective permissions (intersection of all tokens in chain).

        Delegation can only narrow permissions, not expand them.
        """
        if not self.tokens:
            return []

        # Start with first token's permissions
        effective = set((p.action, p.resource) for p in self.tokens[0].permissions)

        # Intersect with each subsequent token
        for token in self.tokens[1:]:
            token_perms = set((p.action, p.resource) for p in token.permissions)
            effective = effective.intersection(token_perms)

        # Convert back to ScopedPermission objects
        return [
            ScopedPermission(action=action, resource=resource)
            for action, resource in effective
        ]

    def can_perform(self, action: str, resource: str) -> bool:
        """Check if chain allows action on resource."""
        if not self.is_valid:
            return False

        # All tokens must allow the action
        return all(token.can_perform(action, resource) for token in self.tokens)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tokens": [t.to_dict() for t in self.tokens],
            "root_identity": self.root_identity,
            "current_identity": self.current_identity,
            "depth": self.depth,
            "is_valid": self.is_valid
        }


# ============================================================================
# DELEGATION MANAGER
# ============================================================================

class DelegationManager:
    """
    Manages delegation tokens and chains.

    Responsibilities:
    - Create delegation tokens
    - Verify delegation chains
    - Revoke delegations
    - Maintain audit trail
    """

    def __init__(self):
        self.tokens: Dict[str, DelegationToken] = {}
        self.revocation_list: Set[str] = set()  # Revoked token IDs

    def create_delegation(
        self,
        issuer: str,
        delegate: str,
        permissions: List[ScopedPermission],
        duration_hours: int = 24,
        parent_token_id: Optional[str] = None
    ) -> DelegationToken:
        """
        Create new delegation token.

        Args:
            issuer: LCT identity of issuer
            delegate: LCT identity of delegate
            permissions: List of granted permissions
            duration_hours: Token validity duration
            parent_token_id: Parent token (if sub-delegation)

        Returns:
            DelegationToken signed by issuer
        """
        token_id = f"token_{secrets.token_hex(16)}"

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=duration_hours)

        # Determine delegation depth
        depth = 0
        if parent_token_id and parent_token_id in self.tokens:
            parent_token = self.tokens[parent_token_id]
            depth = parent_token.delegation_depth + 1

            # Verify issuer is the delegate of parent token
            if parent_token.delegate != issuer:
                raise ValueError(
                    f"Issuer {issuer} is not delegate of parent token {parent_token_id}"
                )

            # Verify parent token is valid
            if not parent_token.is_valid:
                raise ValueError(f"Parent token {parent_token_id} is not valid")

        token = DelegationToken(
            token_id=token_id,
            issuer=issuer,
            delegate=delegate,
            permissions=permissions,
            issued_at=now.isoformat(),
            expires_at=expires_at.isoformat(),
            delegation_depth=depth,
            parent_token_id=parent_token_id
        )

        # Sign token (in production, with issuer's hardware-bound key from Track 1)
        token.signature = self._sign_token(token, issuer)

        self.tokens[token_id] = token

        return token

    def get_delegation_chain(self, token_id: str) -> Optional[DelegationChain]:
        """
        Build complete delegation chain from token.

        Returns:
            DelegationChain from root to current token
        """
        if token_id not in self.tokens:
            return None

        # Build chain by following parent pointers
        chain_tokens = []
        current_id = token_id

        while current_id:
            if current_id not in self.tokens:
                return None

            token = self.tokens[current_id]
            chain_tokens.insert(0, token)  # Insert at beginning (reverse order)
            current_id = token.parent_token_id

        return DelegationChain(tokens=chain_tokens)

    def revoke_delegation(
        self,
        token_id: str,
        reason: str = "user_requested",
        cascade: bool = True
    ) -> List[str]:
        """
        Revoke delegation token.

        Args:
            token_id: Token to revoke
            reason: Revocation reason
            cascade: If True, also revoke child delegations

        Returns:
            List of revoked token IDs
        """
        if token_id not in self.tokens:
            return []

        revoked = []

        # Revoke token
        token = self.tokens[token_id]
        token.revoke(reason)
        self.revocation_list.add(token_id)
        revoked.append(token_id)

        # Cascade to children if requested
        if cascade:
            for child_id, child_token in self.tokens.items():
                if child_token.parent_token_id == token_id:
                    revoked.extend(self.revoke_delegation(child_id, f"parent_revoked:{token_id}", cascade=True))

        return revoked

    def verify_action(
        self,
        token_id: str,
        action: str,
        resource: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify token allows action on resource.

        Returns:
            (is_allowed, error_message)
        """
        # Get delegation chain
        chain = self.get_delegation_chain(token_id)

        if not chain:
            return False, f"Token not found: {token_id}"

        # Check chain validity
        if not chain.is_valid:
            return False, "Delegation chain contains invalid token"

        # Check if chain allows action
        if not chain.can_perform(action, resource):
            return False, f"Permission denied: {action} on {resource}"

        return True, None

    def _sign_token(self, token: DelegationToken, issuer: str) -> str:
        """
        Sign token with issuer's hardware-bound key.

        In production, would use hardware-bound key from Track 1.
        For testing, using hash-based simulation.
        """
        canonical = json.dumps(token.to_dict(), sort_keys=True)
        signature = hashlib.sha256(f"{canonical}:{issuer}".encode()).hexdigest()
        return signature


# ============================================================================
# TEST SCENARIOS
# ============================================================================

def test_scoped_permission_matching():
    """Test scoped permission matching with wildcards."""
    print("="*80)
    print("TEST SCENARIO 1: Scoped Permission Matching")
    print("="*80)

    # Create permission with wildcard
    perm = ScopedPermission(
        action="browser:navigate",
        resource="https://github.com/*"
    )

    print(f"\n📝 Permission created:")
    print(f"   Action: {perm.action}")
    print(f"   Resource: {perm.resource}")

    # Test matches
    tests = [
        ("browser:navigate", "https://github.com/dp-web4", True),
        ("browser:navigate", "https://github.com/dp-web4/web4", True),
        ("browser:navigate", "https://example.com", False),
        ("browser:click", "https://github.com/dp-web4", False),
    ]

    print(f"\n🔍 Testing matches:")
    all_correct = True
    for action, resource, expected in tests:
        result = perm.matches(action, resource)
        status = "✅" if result == expected else "❌"
        print(f"   {status} {action} on {resource}: {result} (expected: {expected})")
        all_correct = all_correct and (result == expected)

    return all_correct


def test_delegation_token_creation():
    """Test creating delegation tokens."""
    print("\n" + "="*80)
    print("TEST SCENARIO 2: Delegation Token Creation")
    print("="*80)

    manager = DelegationManager()

    # Human delegates to SAGE
    human_to_sage = manager.create_delegation(
        issuer="lct://user:dennis@laptop",
        delegate="lct://sage:main@mainnet",
        permissions=[
            ScopedPermission(action="browser:navigate", resource="https://github.com/*"),
            ScopedPermission(action="browser:click", resource="https://github.com/*"),
        ],
        duration_hours=24
    )

    print(f"\n✅ Delegation token created:")
    print(f"   Token ID: {human_to_sage.token_id}")
    print(f"   Issuer: {human_to_sage.issuer}")
    print(f"   Delegate: {human_to_sage.delegate}")
    print(f"   Permissions: {len(human_to_sage.permissions)}")
    print(f"   Delegation depth: {human_to_sage.delegation_depth}")
    print(f"   Valid: {human_to_sage.is_valid}")
    print(f"   Signature: {human_to_sage.signature[:32]}...")

    # Test permission check
    can_navigate = human_to_sage.can_perform("browser:navigate", "https://github.com/dp-web4")
    can_delete = human_to_sage.can_perform("api:delete", "https://github.com/dp-web4")

    print(f"\n🔍 Permission checks:")
    print(f"   Can navigate GitHub: {can_navigate}")
    print(f"   Can delete (not granted): {can_delete}")

    return can_navigate and not can_delete


def test_delegation_chain():
    """Test building delegation chains."""
    print("\n" + "="*80)
    print("TEST SCENARIO 3: Delegation Chain")
    print("="*80)

    manager = DelegationManager()

    # Level 0: Human delegates to SAGE
    human_to_sage = manager.create_delegation(
        issuer="lct://user:dennis@laptop",
        delegate="lct://sage:main@mainnet",
        permissions=[
            ScopedPermission(action="browser:navigate", resource="https://github.com/*"),
            ScopedPermission(action="browser:click", resource="https://github.com/*"),
        ]
    )

    print(f"\n✅ Level 0: Human → SAGE")
    print(f"   Token: {human_to_sage.token_id}")
    print(f"   Depth: {human_to_sage.delegation_depth}")

    # Level 1: SAGE delegates to plugin
    sage_to_plugin = manager.create_delegation(
        issuer="lct://sage:main@mainnet",
        delegate="lct://sage:browser_automation@mainnet",
        permissions=[
            ScopedPermission(action="browser:navigate", resource="https://github.com/dp-web4/*"),
        ],
        parent_token_id=human_to_sage.token_id
    )

    print(f"\n✅ Level 1: SAGE → Plugin")
    print(f"   Token: {sage_to_plugin.token_id}")
    print(f"   Depth: {sage_to_plugin.delegation_depth}")
    print(f"   Parent: {sage_to_plugin.parent_token_id}")

    # Build chain
    chain = manager.get_delegation_chain(sage_to_plugin.token_id)

    print(f"\n📊 Delegation chain:")
    print(f"   Root: {chain.root_identity}")
    print(f"   Current: {chain.current_identity}")
    print(f"   Depth: {chain.depth}")
    print(f"   Tokens: {len(chain.tokens)}")
    print(f"   Valid: {chain.is_valid}")

    # Test action verification
    allowed, error = manager.verify_action(
        sage_to_plugin.token_id,
        "browser:navigate",
        "https://github.com/dp-web4/web4"
    )

    print(f"\n🔍 Action verification:")
    print(f"   Allowed: {allowed}")
    if error:
        print(f"   Error: {error}")

    return allowed and chain.depth == 2


def test_scope_narrowing():
    """Test that delegation can only narrow permissions."""
    print("\n" + "="*80)
    print("TEST SCENARIO 4: Scope Narrowing")
    print("="*80)

    manager = DelegationManager()

    # Parent: Can navigate all of github.com
    parent_token = manager.create_delegation(
        issuer="lct://user:dennis@laptop",
        delegate="lct://sage:main@mainnet",
        permissions=[
            ScopedPermission(action="browser:navigate", resource="https://github.com/*"),
        ]
    )

    # Child: Can only navigate dp-web4 repos (narrower scope)
    child_token = manager.create_delegation(
        issuer="lct://sage:main@mainnet",
        delegate="lct://sage:browser_plugin@mainnet",
        permissions=[
            ScopedPermission(action="browser:navigate", resource="https://github.com/dp-web4/*"),
        ],
        parent_token_id=parent_token.token_id
    )

    print(f"\n📊 Parent permissions:")
    print(f"   {parent_token.permissions[0].action}: {parent_token.permissions[0].resource}")

    print(f"\n📊 Child permissions (narrowed):")
    print(f"   {child_token.permissions[0].action}: {child_token.permissions[0].resource}")

    # Test access
    can_access_dp_web4 = child_token.can_perform("browser:navigate", "https://github.com/dp-web4/web4")
    can_access_other = child_token.can_perform("browser:navigate", "https://github.com/other/repo")

    print(f"\n🔍 Access tests:")
    print(f"   Can navigate dp-web4: {can_access_dp_web4}")
    print(f"   Can navigate other: {can_access_other}")

    return can_access_dp_web4 and not can_access_other


def test_revocation_cascade():
    """Test cascading revocation."""
    print("\n" + "="*80)
    print("TEST SCENARIO 5: Revocation Cascade")
    print("="*80)

    manager = DelegationManager()

    # Create chain: Human → SAGE → Plugin
    human_token = manager.create_delegation(
        issuer="lct://user:dennis@laptop",
        delegate="lct://sage:main@mainnet",
        permissions=[ScopedPermission(action="browser:navigate", resource="https://github.com/*")]
    )

    sage_token = manager.create_delegation(
        issuer="lct://sage:main@mainnet",
        delegate="lct://sage:plugin@mainnet",
        permissions=[ScopedPermission(action="browser:navigate", resource="https://github.com/*")],
        parent_token_id=human_token.token_id
    )

    print(f"\n✅ Created chain:")
    print(f"   Human token: {human_token.token_id}")
    print(f"   SAGE token: {sage_token.token_id}")

    # Verify initial state
    chain = manager.get_delegation_chain(sage_token.token_id)
    print(f"\n📊 Initial state:")
    print(f"   Chain valid: {chain.is_valid}")

    # Revoke parent token (should cascade to child)
    revoked = manager.revoke_delegation(human_token.token_id, reason="test_revocation", cascade=True)

    print(f"\n🚫 Revoked tokens: {len(revoked)}")
    for token_id in revoked:
        print(f"   - {token_id}")

    # Verify revocation
    chain_after = manager.get_delegation_chain(sage_token.token_id)
    print(f"\n📊 After revocation:")
    print(f"   Chain valid: {chain_after.is_valid}")
    print(f"   Human token revoked: {human_token.revoked}")
    print(f"   SAGE token revoked: {sage_token.revoked}")

    return len(revoked) == 2 and not chain_after.is_valid


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all test scenarios."""
    print("="*80)
    print("SESSION 96 TRACK 2: AUTHORIZATION DELEGATION CHAIN")
    print("="*80)
    print("\nFrom AI Agent Accountability doc:")
    print("  Hardware Root → LCT Identity → Delegation Chain")
    print("    ├─ Human (direct action)")
    print("    └─ SAGE (delegated authority, scope-limited)")
    print("          └─ IRP Plugin (e.g., browser-automation-irp)")
    print()

    results = []

    # Run tests
    results.append(("Scoped permission matching", test_scoped_permission_matching()))
    results.append(("Delegation token creation", test_delegation_token_creation()))
    results.append(("Delegation chain", test_delegation_chain()))
    results.append(("Scope narrowing", test_scope_narrowing()))
    results.append(("Revocation cascade", test_revocation_cascade()))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    all_passed = all(result for _, result in results)
    print(f"\n✅ All scenarios passed: {all_passed}")

    print(f"\nScenarios tested:")
    for i, (name, passed) in enumerate(results, 1):
        status = "✅" if passed else "❌"
        print(f"  {i}. {status} {name}")

    # Save results
    output = {
        "session": "96",
        "track": "2",
        "focus": "Authorization Delegation Chain",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test_results": [
            {"scenario": name, "passed": passed}
            for name, passed in results
        ],
        "all_passed": all_passed,
        "innovations": [
            "ScopedPermission with wildcard matching",
            "DelegationToken with cryptographic signatures",
            "DelegationChain with complete ancestry tracking",
            "Scope narrowing (delegation can only reduce permissions)",
            "Cascading revocation (parent revoked → children revoked)",
        ]
    }

    output_path = "/home/dp/ai-workspace/web4/implementation/session96_track2_results.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Results saved to: {output_path}")

    print("\n" + "="*80)
    print("Key Innovations:")
    print("="*80)
    for i, innovation in enumerate(output["innovations"], 1):
        print(f"{i}. {innovation}")

    print("\n" + "="*80)
    print("Delegation chain properties:")
    print("- Traceability: Full path from human to current actor")
    print("- Scope narrowing: Each level has narrower permissions")
    print("- Accountability: Any action traces back to human origin")
    print("- Revocation: Immediate termination with cascade")
    print("- Time-bound: Automatic expiration")
    print("="*80)

    return all_passed


if __name__ == "__main__":
    run_all_tests()
