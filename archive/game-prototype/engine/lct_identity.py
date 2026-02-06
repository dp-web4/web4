"""
LCT Identity System - Core Implementation

Lineage-Context-Task identity system for AI agents in Web4 distributed societies.

Author: Legion Autonomous Session #47
Date: 2025-12-01
Status: Phase 1 implementation - core identity structure
References: LCT_IDENTITY_SYSTEM.md (design specification)

Identity Format: lct:web4:agent:{lineage}@{context}#{task}

Example: lct:web4:agent:alice@Thor#perception
- Lineage: alice (creator)
- Context: Thor (platform)
- Task: perception (authorized capability)
"""

import re
import time
import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple


# LCT Identity Format Pattern
LCT_PATTERN = re.compile(
    r'^lct:web4:agent:(?P<lineage>[a-zA-Z0-9._:-]+)@(?P<context>[a-zA-Z0-9._:-]+)#(?P<task>[a-zA-Z0-9._-]+)$'
)


@dataclass
class LCTLineage:
    """
    Lineage component: Who created/authorized this agent.

    Hierarchical structure: creator.sub_creator.sub_sub_creator
    Example: alice.assistant1.researcher
    """

    creator_id: str  # Root creator (e.g., "alice")
    hierarchy: List[str] = field(default_factory=list)  # Delegation chain
    creator_pubkey: str = ""  # Ed25519 public key
    creation_timestamp: float = field(default_factory=time.time)
    revocation_endpoint: str = ""  # URL to check revocation status

    def full_lineage(self) -> str:
        """Get full lineage string"""
        if self.hierarchy:
            return f"{self.creator_id}.{'.'.join(self.hierarchy)}"
        return self.creator_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "creator_id": self.creator_id,
            "hierarchy": self.hierarchy,
            "creator_pubkey": self.creator_pubkey,
            "creation_timestamp": self.creation_timestamp,
            "revocation_endpoint": self.revocation_endpoint
        }


@dataclass
class LCTContext:
    """
    Context component: What platform/environment the agent runs in.

    Examples: Thor, Sprout, cloud:aws-east-1, mobile:iphone14
    """

    platform_id: str  # Platform identifier
    platform_pubkey: str = ""  # Ed25519 public key
    attestation_timestamp: float = field(default_factory=time.time)
    capabilities: List[str] = field(default_factory=list)  # ["consensus", "federation", "atp_ledger"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "platform_id": self.platform_id,
            "platform_pubkey": self.platform_pubkey,
            "attestation_timestamp": self.attestation_timestamp,
            "capabilities": self.capabilities
        }


@dataclass
class LCTTask:
    """
    Task component: What the agent is authorized to do.

    Hierarchical structure: task_type.task_variant
    Examples: perception, planning.strategic, execution.code
    """

    task_id: str  # Task identifier
    permissions: List[str] = field(default_factory=list)  # ["atp:read", "network:http"]
    resource_limits: Dict[str, Any] = field(default_factory=dict)  # {"atp_budget": 1000, "memory_mb": 2048}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "task_id": self.task_id,
            "permissions": self.permissions,
            "resource_limits": self.resource_limits
        }


@dataclass
class LCTIdentity:
    """
    Complete LCT identity.

    Format: lct:web4:agent:{lineage}@{context}#{task}
    """

    lineage: LCTLineage
    context: LCTContext
    task: LCTTask
    creator_signature: str = ""  # Ed25519 signature by creator
    platform_signature: str = ""  # Ed25519 signature by platform
    validity_start: float = field(default_factory=time.time)
    validity_end: float = 0.0  # 0 = never expires
    can_renew: bool = True

    def lct_string(self) -> str:
        """Get full LCT identity string"""
        return f"lct:web4:agent:{self.lineage.full_lineage()}@{self.context.platform_id}#{self.task.task_id}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for certificate)"""
        return {
            "lct_id": self.lct_string(),
            "lineage": self.lineage.to_dict(),
            "context": self.context.to_dict(),
            "task": self.task.to_dict(),
            "signatures": {
                "creator_signature": self.creator_signature,
                "platform_signature": self.platform_signature
            },
            "validity": {
                "not_before": self.validity_start,
                "not_after": self.validity_end,
                "can_renew": self.can_renew
            }
        }

    def is_valid(self, current_time: Optional[float] = None) -> bool:
        """Check if identity is currently valid"""
        if current_time is None:
            current_time = time.time()

        # Check start time
        if current_time < self.validity_start:
            return False

        # Check end time (0 = never expires)
        if self.validity_end > 0 and current_time > self.validity_end:
            return False

        return True

    def signable_content_creator(self) -> str:
        """Content signed by creator (lineage + task)"""
        data = {
            "lineage": self.lineage.to_dict(),
            "task": self.task.to_dict(),
            "validity_start": self.validity_start,
            "validity_end": self.validity_end
        }
        return json.dumps(data, sort_keys=True)

    def signable_content_platform(self) -> str:
        """Content signed by platform (context + creator_signature)"""
        data = {
            "context": self.context.to_dict(),
            "creator_signature": self.creator_signature,
            "lineage": self.lineage.full_lineage(),
            "task": self.task.task_id
        }
        return json.dumps(data, sort_keys=True)


def parse_lct_id(lct_id: str) -> Optional[Tuple[str, str, str]]:
    """
    Parse LCT identity string into components.

    Args:
        lct_id: LCT identity string (e.g., "lct:web4:agent:alice@Thor#perception")

    Returns:
        (lineage, context, task) tuple or None if invalid

    Examples:
        >>> parse_lct_id("lct:web4:agent:alice@Thor#perception")
        ("alice", "Thor", "perception")

        >>> parse_lct_id("lct:web4:agent:alice.assistant1@Sprout#planning.strategic")
        ("alice.assistant1", "Sprout", "planning.strategic")
    """
    match = LCT_PATTERN.match(lct_id)
    if not match:
        return None

    return (
        match.group("lineage"),
        match.group("context"),
        match.group("task")
    )


def parse_lineage(lineage_str: str) -> Tuple[str, List[str]]:
    """
    Parse lineage string into creator and hierarchy.

    Args:
        lineage_str: Lineage string (e.g., "alice.assistant1.researcher")

    Returns:
        (creator_id, hierarchy) tuple

    Examples:
        >>> parse_lineage("alice")
        ("alice", [])

        >>> parse_lineage("alice.assistant1.researcher")
        ("alice", ["assistant1", "researcher"])
    """
    parts = lineage_str.split(".")
    creator_id = parts[0]
    hierarchy = parts[1:] if len(parts) > 1 else []
    return (creator_id, hierarchy)


def create_lct_identity(
    lineage_str: str,
    context_str: str,
    task_str: str,
    lineage_pubkey: str = "",
    context_pubkey: str = "",
    permissions: Optional[List[str]] = None,
    resource_limits: Optional[Dict[str, Any]] = None,
    validity_hours: float = 24.0
) -> LCTIdentity:
    """
    Create new LCT identity.

    Args:
        lineage_str: Lineage string (e.g., "alice.assistant1")
        context_str: Context string (e.g., "Thor")
        task_str: Task string (e.g., "perception")
        lineage_pubkey: Creator's Ed25519 public key
        context_pubkey: Platform's Ed25519 public key
        permissions: List of permissions (e.g., ["atp:read", "network:http"])
        resource_limits: Resource limits dict (e.g., {"atp_budget": 1000})
        validity_hours: Validity period in hours (default: 24)

    Returns:
        LCTIdentity object (unsigned - needs creator and platform signatures)

    Example:
        >>> identity = create_lct_identity(
        ...     lineage_str="alice",
        ...     context_str="Thor",
        ...     task_str="perception",
        ...     lineage_pubkey="ed25519:ABC123...",
        ...     context_pubkey="ed25519:DEF456...",
        ...     permissions=["atp:read", "network:http"],
        ...     resource_limits={"atp_budget": 1000, "memory_mb": 2048}
        ... )
    """
    # Parse lineage
    creator_id, hierarchy = parse_lineage(lineage_str)

    # Create components
    lineage = LCTLineage(
        creator_id=creator_id,
        hierarchy=hierarchy,
        creator_pubkey=lineage_pubkey,
        creation_timestamp=time.time()
    )

    context = LCTContext(
        platform_id=context_str,
        platform_pubkey=context_pubkey,
        attestation_timestamp=time.time()
    )

    task = LCTTask(
        task_id=task_str,
        permissions=permissions or [],
        resource_limits=resource_limits or {}
    )

    # Calculate validity period
    validity_start = time.time()
    validity_end = validity_start + (validity_hours * 3600) if validity_hours > 0 else 0.0

    return LCTIdentity(
        lineage=lineage,
        context=context,
        task=task,
        validity_start=validity_start,
        validity_end=validity_end
    )


def sign_identity_creator(identity: LCTIdentity, signing_func) -> LCTIdentity:
    """
    Sign identity with creator's private key.

    Args:
        identity: LCTIdentity object
        signing_func: Function to sign content (content: str) -> signature: str

    Returns:
        LCTIdentity with creator_signature set
    """
    content = identity.signable_content_creator()
    identity.creator_signature = signing_func(content)
    return identity


def sign_identity_platform(identity: LCTIdentity, signing_func) -> LCTIdentity:
    """
    Sign identity with platform's private key.

    Args:
        identity: LCTIdentity object
        signing_func: Function to sign content (content: str) -> signature: str

    Returns:
        LCTIdentity with platform_signature set
    """
    content = identity.signable_content_platform()
    identity.platform_signature = signing_func(content)
    return identity


def verify_identity_creator(identity: LCTIdentity, verification_func) -> bool:
    """
    Verify creator signature.

    Args:
        identity: LCTIdentity object
        verification_func: Function to verify signature
                          (content: str, signature: str, pubkey: str) -> bool

    Returns:
        True if signature valid, False otherwise
    """
    content = identity.signable_content_creator()
    return verification_func(content, identity.creator_signature, identity.lineage.creator_pubkey)


def verify_identity_platform(identity: LCTIdentity, verification_func) -> bool:
    """
    Verify platform signature.

    Args:
        identity: LCTIdentity object
        verification_func: Function to verify signature
                          (content: str, signature: str, pubkey: str) -> bool

    Returns:
        True if signature valid, False otherwise
    """
    content = identity.signable_content_platform()
    return verification_func(content, identity.platform_signature, identity.context.platform_pubkey)


def verify_identity_complete(identity: LCTIdentity, verification_func) -> Tuple[bool, str]:
    """
    Complete identity verification.

    Checks:
    1. Creator signature valid
    2. Platform signature valid
    3. Identity not expired
    4. Signatures not empty

    Args:
        identity: LCTIdentity object
        verification_func: Function to verify signature

    Returns:
        (is_valid, reason) tuple

    Example:
        >>> is_valid, reason = verify_identity_complete(identity, verify_func)
        >>> if not is_valid:
        ...     print(f"Identity invalid: {reason}")
    """
    # Check signatures not empty
    if not identity.creator_signature:
        return (False, "Missing creator signature")
    if not identity.platform_signature:
        return (False, "Missing platform signature")

    # Check validity period
    if not identity.is_valid():
        return (False, "Identity expired or not yet valid")

    # Verify creator signature
    if not verify_identity_creator(identity, verification_func):
        return (False, "Invalid creator signature")

    # Verify platform signature
    if not verify_identity_platform(identity, verification_func):
        return (False, "Invalid platform signature")

    return (True, "Valid")


def get_identity_hash(identity: LCTIdentity) -> str:
    """
    Compute SHA-256 hash of identity.

    Used for identity lookup and deduplication.

    Args:
        identity: LCTIdentity object

    Returns:
        SHA-256 hex digest
    """
    identity_json = json.dumps(identity.to_dict(), sort_keys=True)
    return hashlib.sha256(identity_json.encode()).hexdigest()
