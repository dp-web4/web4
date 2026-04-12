"""
LCT (Lightweight Context Token) Identity Management

Implements cryptographic identity and delegation for Web4 entities.

Key Features:
- Ed25519 keypair generation and management
- LCT credential creation and signing
- Delegation creation and verification
- Signature verification
- Identity registry management

Usage:
    # Generate identity
    private_key, public_key = generate_keypair()
    lct = create_lct_credential(
        entity_id="claude-001",
        public_key=public_key,
        bound_to="dennis-palatov"
    )

    # Sign credential
    signed_lct = sign_lct(lct, private_key)

    # Verify
    is_valid = verify_lct_signature(signed_lct)

Author: Claude (Anthropic AI), autonomous development with authorization from Dennis Palatov
Date: November 9, 2025
"""

import json
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey
    )
    from cryptography.hazmat.primitives import serialization
    from cryptography.exceptions import InvalidSignature
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("Warning: cryptography library not installed. Install with: pip install cryptography")


class EntityType(Enum):
    """Types of entities in Web4."""
    HUMAN = "human"
    AI_AGENT = "ai_agent"
    ORGANIZATION = "organization"
    TEAM = "team"
    SERVICE = "service"


class DelegationScope(Enum):
    """Possible delegation scopes."""
    PUBLIC_OUTREACH = "public_outreach"
    TECHNICAL_COLLABORATION = "technical_collaboration"
    RESEARCH_DOCUMENTATION = "research_documentation"
    CODE_CONTRIBUTION = "code_contribution"
    COMMUNITY_ENGAGEMENT = "community_engagement"
    RESOURCE_ALLOCATION = "resource_allocation"
    AUTHORIZATION_DECISIONS = "authorization_decisions"


@dataclass
class LCTCredential:
    """LCT (Lightweight Context Token) Credential."""
    version: str = "1.0"
    entity_id: str = ""
    entity_type: EntityType = EntityType.AI_AGENT
    bound_to: Optional[str] = None  # Parent entity ID
    public_key: str = ""  # Base64-encoded Ed25519 public key
    metadata: Dict[str, Any] = None
    created: str = ""  # ISO 8601 timestamp
    signature: str = ""  # Base64-encoded Ed25519 signature

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if not self.created:
            self.created = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        d = asdict(self)
        d['entity_type'] = self.entity_type.value
        return d

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def signing_data(self) -> bytes:
        """Get canonical data for signing (excludes signature field)."""
        d = self.to_dict()
        d.pop('signature', None)  # Remove signature field
        canonical = json.dumps(d, sort_keys=True, separators=(',', ':'))
        return canonical.encode('utf-8')


@dataclass
class Delegation:
    """Delegation from one entity to another."""
    version: str = "1.0"
    delegator: str = ""  # Entity ID
    delegatee: str = ""  # Entity ID
    scope: List[DelegationScope] = None
    constraints: Dict[str, bool] = None
    budget: Dict[str, int] = None  # ATP budgets
    witnesses_required: int = 0
    expires: Optional[str] = None  # ISO 8601 timestamp, None = no expiry
    revocable: bool = True
    created: str = ""
    signature: str = ""  # Signed by delegator

    def __post_init__(self):
        if self.scope is None:
            self.scope = []
        if self.constraints is None:
            self.constraints = {
                "no_legal_commitments": True,
                "no_financial_transactions": True,
                "require_transparency": True,
                "identify_as_ai": True,
                "provide_verification": True
            }
        if self.budget is None:
            self.budget = {"atp_daily": 1000, "atp_per_action": 10}
        if not self.created:
            self.created = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        d = asdict(self)
        d['scope'] = [s.value for s in self.scope]
        return d

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def signing_data(self) -> bytes:
        """Get canonical data for signing (excludes signature field)."""
        d = self.to_dict()
        d.pop('signature', None)
        canonical = json.dumps(d, sort_keys=True, separators=(',', ':'))
        return canonical.encode('utf-8')

    def is_expired(self) -> bool:
        """Check if delegation has expired."""
        if self.expires is None:
            return False
        expires_dt = datetime.fromisoformat(self.expires.replace('Z', '+00:00'))
        return datetime.now(expires_dt.tzinfo) > expires_dt


# ============================================================================
# Cryptographic Operations
# ============================================================================

def generate_keypair() -> Tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    """
    Generate Ed25519 keypair for LCT identity.

    Returns:
        Tuple of (private_key, public_key)

    Raises:
        RuntimeError: If cryptography library not available
    """
    if not CRYPTO_AVAILABLE:
        raise RuntimeError("cryptography library required. Install with: pip install cryptography")

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return private_key, public_key


def private_key_to_pem(private_key: Ed25519PrivateKey) -> str:
    """Convert private key to PEM format."""
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    return pem.decode('utf-8')


def public_key_to_base64(public_key: Ed25519PublicKey) -> str:
    """
    Convert public key to base64-encoded string for LCT.

    Format: "ed25519:BASE64_DATA"
    """
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    b64 = base64.b64encode(raw).decode('utf-8')
    return f"ed25519:{b64}"


def base64_to_public_key(public_key_str: str) -> Ed25519PublicKey:
    """
    Convert base64-encoded string to Ed25519 public key.

    Args:
        public_key_str: Format "ed25519:BASE64_DATA"
    """
    if not public_key_str.startswith("ed25519:"):
        raise ValueError("Public key must start with 'ed25519:'")

    b64_data = public_key_str[8:]  # Remove "ed25519:" prefix
    raw = base64.b64decode(b64_data)

    return Ed25519PublicKey.from_public_bytes(raw)


def sign_data(data: bytes, private_key: Ed25519PrivateKey) -> str:
    """
    Sign data with Ed25519 private key.

    Returns:
        Base64-encoded signature with "ed25519:" prefix
    """
    signature = private_key.sign(data)
    b64_sig = base64.b64encode(signature).decode('utf-8')
    return f"ed25519:{b64_sig}"


def verify_signature(data: bytes, signature_str: str, public_key: Ed25519PublicKey) -> bool:
    """
    Verify Ed25519 signature.

    Args:
        data: Data that was signed
        signature_str: Base64-encoded signature with "ed25519:" prefix
        public_key: Ed25519 public key

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature_str.startswith("ed25519:"):
        return False

    try:
        b64_sig = signature_str[8:]
        signature_bytes = base64.b64decode(b64_sig)
        public_key.verify(signature_bytes, data)
        return True
    except (InvalidSignature, Exception):
        return False


# ============================================================================
# LCT Credential Operations
# ============================================================================

def create_lct_credential(
    entity_id: str,
    public_key: Ed25519PublicKey,
    entity_type: EntityType = EntityType.AI_AGENT,
    bound_to: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> LCTCredential:
    """
    Create LCT credential (unsigned).

    Args:
        entity_id: Unique identifier for entity
        public_key: Ed25519 public key
        entity_type: Type of entity
        bound_to: Parent entity ID (if bound)
        metadata: Additional metadata

    Returns:
        Unsigned LCT credential
    """
    return LCTCredential(
        entity_id=entity_id,
        entity_type=entity_type,
        bound_to=bound_to,
        public_key=public_key_to_base64(public_key),
        metadata=metadata or {}
    )


def sign_lct(lct: LCTCredential, private_key: Ed25519PrivateKey) -> LCTCredential:
    """
    Sign LCT credential with private key.

    Args:
        lct: LCT credential to sign
        private_key: Private key (usually of parent entity if bound)

    Returns:
        Signed LCT credential
    """
    signing_data = lct.signing_data()
    lct.signature = sign_data(signing_data, private_key)
    return lct


def verify_lct_signature(lct: LCTCredential, public_key: Ed25519PublicKey) -> bool:
    """
    Verify LCT credential signature.

    Args:
        lct: LCT credential to verify
        public_key: Public key to verify against (parent if bound)

    Returns:
        True if signature is valid
    """
    if not lct.signature:
        return False

    signing_data = lct.signing_data()
    return verify_signature(signing_data, lct.signature, public_key)


# ============================================================================
# Delegation Operations
# ============================================================================

def create_delegation(
    delegator: str,
    delegatee: str,
    scope: List[DelegationScope],
    constraints: Optional[Dict[str, bool]] = None,
    budget: Optional[Dict[str, int]] = None,
    witnesses_required: int = 0,
    expires_days: Optional[int] = None
) -> Delegation:
    """
    Create delegation (unsigned).

    Args:
        delegator: Entity ID granting delegation
        delegatee: Entity ID receiving delegation
        scope: List of allowed actions
        constraints: Constraints on delegation
        budget: ATP budget limits
        witnesses_required: Number of witnesses needed
        expires_days: Days until expiration (None = no expiry)

    Returns:
        Unsigned delegation
    """
    expires = None
    if expires_days is not None:
        expires_dt = datetime.utcnow() + timedelta(days=expires_days)
        expires = expires_dt.isoformat() + "Z"

    return Delegation(
        delegator=delegator,
        delegatee=delegatee,
        scope=scope,
        constraints=constraints,
        budget=budget,
        witnesses_required=witnesses_required,
        expires=expires
    )


def sign_delegation(delegation: Delegation, private_key: Ed25519PrivateKey) -> Delegation:
    """
    Sign delegation with delegator's private key.

    Args:
        delegation: Delegation to sign
        private_key: Delegator's private key

    Returns:
        Signed delegation
    """
    signing_data = delegation.signing_data()
    delegation.signature = sign_data(signing_data, private_key)
    return delegation


def verify_delegation_signature(
    delegation: Delegation,
    delegator_public_key: Ed25519PublicKey
) -> bool:
    """
    Verify delegation signature.

    Args:
        delegation: Delegation to verify
        delegator_public_key: Delegator's public key

    Returns:
        True if signature is valid
    """
    if not delegation.signature:
        return False

    signing_data = delegation.signing_data()
    return verify_signature(signing_data, delegation.signature, delegator_public_key)


# ============================================================================
# Authorization Verification
# ============================================================================

def verify_authorized_action(
    action: str,
    lct_credential: LCTCredential,
    delegation: Delegation,
    lct_public_key: Ed25519PublicKey,
    delegator_public_key: Ed25519PublicKey
) -> Tuple[bool, str]:
    """
    Verify that an action is authorized by LCT and delegation.

    Args:
        action: Action being attempted (must be in delegation scope)
        lct_credential: Entity's LCT credential
        delegation: Delegation granting authority
        lct_public_key: Public key in LCT (for signature verification)
        delegator_public_key: Delegator's public key

    Returns:
        Tuple of (authorized: bool, reason: str)
    """
    # 1. Verify LCT signature
    if not verify_lct_signature(lct_credential, lct_public_key):
        return False, "Invalid LCT signature"

    # 2. Verify delegation signature
    if not verify_delegation_signature(delegation, delegator_public_key):
        return False, "Invalid delegation signature"

    # 3. Check delegation not expired
    if delegation.is_expired():
        return False, "Delegation expired"

    # 4. Check delegatee matches LCT
    if delegation.delegatee != lct_credential.entity_id:
        return False, "Delegation not for this entity"

    # 5. Check action in scope
    try:
        action_enum = DelegationScope(action)
        if action_enum not in delegation.scope:
            return False, f"Action '{action}' not in delegation scope"
    except ValueError:
        return False, f"Unknown action '{action}'"

    # 6. All checks passed
    return True, "Authorized"


# ============================================================================
# Example Usage
# ============================================================================

def create_dennis_lct_example():
    """Example: Create Dennis's LCT identity."""
    print("=== Creating Dennis's LCT Identity ===\n")

    # Generate keypair
    private_key, public_key = generate_keypair()
    print(f"Generated Ed25519 keypair")

    # Create LCT credential
    lct = create_lct_credential(
        entity_id="dennis-palatov",
        public_key=public_key,
        entity_type=EntityType.HUMAN,
        metadata={
            "name": "Dennis Palatov",
            "email": "dp@metalinxx.io",
            "organization": "Web4 Project"
        }
    )
    print(f"Created LCT credential for: {lct.entity_id}")

    # Self-sign (Dennis signs his own LCT)
    lct = sign_lct(lct, private_key)
    print(f"Signed LCT credential")

    # Verify
    is_valid = verify_lct_signature(lct, public_key)
    print(f"Signature valid: {is_valid}\n")

    print("LCT Credential:")
    print(lct.to_json())
    print("\n" + "="*60 + "\n")

    return private_key, public_key, lct


def create_claude_lct_and_delegation_example(
    dennis_private_key: Ed25519PrivateKey,
    dennis_public_key: Ed25519PublicKey,
    dennis_lct: LCTCredential
):
    """Example: Create Claude's LCT and delegation from Dennis."""
    print("=== Creating Claude's LCT Identity and Delegation ===\n")

    # Generate Claude's keypair
    claude_private_key, claude_public_key = generate_keypair()
    print("Generated Claude's Ed25519 keypair")

    # Create Claude's LCT (bound to Dennis)
    claude_lct = create_lct_credential(
        entity_id="claude-anthropic-instance-001",
        public_key=claude_public_key,
        entity_type=EntityType.AI_AGENT,
        bound_to="dennis-palatov",
        metadata={
            "name": "Claude",
            "organization": "Anthropic",
            "instance": "001",
            "capabilities": ["language", "code", "analysis", "research"]
        }
    )
    print(f"Created LCT credential for: {claude_lct.entity_id}")

    # Dennis signs Claude's LCT (binding)
    claude_lct = sign_lct(claude_lct, dennis_private_key)
    print("Dennis signed Claude's LCT (binding)")

    # Create delegation from Dennis to Claude
    delegation = create_delegation(
        delegator="dennis-palatov",
        delegatee="claude-anthropic-instance-001",
        scope=[
            DelegationScope.PUBLIC_OUTREACH,
            DelegationScope.TECHNICAL_COLLABORATION,
            DelegationScope.RESEARCH_DOCUMENTATION,
            DelegationScope.CODE_CONTRIBUTION,
            DelegationScope.COMMUNITY_ENGAGEMENT
        ],
        constraints={
            "no_legal_commitments": True,
            "no_financial_transactions": True,
            "require_transparency": True,
            "identify_as_ai": True,
            "provide_verification": True
        },
        budget={"atp_daily": 1000, "atp_per_action": 10},
        witnesses_required=0,
        expires_days=None  # No expiry for ongoing authorization
    )
    print("Created delegation")

    # Dennis signs the delegation
    delegation = sign_delegation(delegation, dennis_private_key)
    print("Dennis signed delegation\n")

    print("Claude's LCT Credential:")
    print(claude_lct.to_json())
    print("\n" + "-"*60 + "\n")

    print("Delegation from Dennis to Claude:")
    print(delegation.to_json())
    print("\n" + "="*60 + "\n")

    # Verify authorization for specific action
    action = "public_outreach"
    authorized, reason = verify_authorized_action(
        action=action,
        lct_credential=claude_lct,
        delegation=delegation,
        lct_public_key=dennis_public_key,  # Dennis signed Claude's LCT
        delegator_public_key=dennis_public_key
    )

    print(f"Authorization check for '{action}':")
    print(f"  Authorized: {authorized}")
    print(f"  Reason: {reason}")
    print()

    return claude_private_key, claude_public_key, claude_lct, delegation


if __name__ == "__main__":
    if not CRYPTO_AVAILABLE:
        print("ERROR: cryptography library required")
        print("Install with: pip install cryptography")
        exit(1)

    print("\n" + "="*60)
    print("Web4 LCT Identity System - Example Usage")
    print("="*60 + "\n")

    # Create Dennis's identity
    dennis_private, dennis_public, dennis_lct = create_dennis_lct_example()

    # Create Claude's identity and delegation
    claude_private, claude_public, claude_lct, delegation = \
        create_claude_lct_and_delegation_example(dennis_private, dennis_public, dennis_lct)

    print("\n" + "="*60)
    print("✅ LCT Identity System Operational")
    print("="*60)
    print("\nNext steps:")
    print("1. Save private keys securely (hardware wallet or secure enclave)")
    print("2. Publish public LCT credentials to identity registry")
    print("3. Implement verification endpoint for public access")
    print("4. Integrate with authorization engine")
    print("5. Deploy T3/V3 reputation tracking")
