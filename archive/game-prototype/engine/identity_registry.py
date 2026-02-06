"""
LCT Identity Registry - Phase 2

Consensus-based decentralized registry for LCT identities.
Provides Byzantine fault-tolerant storage and lookup of identity public keys.

Author: Legion Autonomous Session #48
Date: 2025-12-01
Status: Phase 2 implementation - identity registry
References: LCT_IDENTITY_SYSTEM.md (Phase 2 roadmap), lct_identity.py (Phase 1)

Registry Operations:
- REGISTER: Add new identity (requires stake)
- UPDATE: Update identity pubkey (requires old key signature)
- REVOKE: Mark identity as revoked (requires key signature)
- QUERY: Look up identity information

Storage:
- Registry stored in consensus blockchain
- Updates require 2f+1 consensus
- Byzantine fault-tolerant
- No single point of failure
"""

import time
import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

# Import LCT identity components
try:
    from game.engine.lct_identity import LCTIdentity, parse_lct_id, get_identity_hash
    LCT_AVAILABLE = True
except ImportError:
    LCT_AVAILABLE = False


class RegistryOperationType(Enum):
    """Registry operation types"""
    REGISTER = "IDENTITY_REGISTER"  # Register new identity
    UPDATE = "IDENTITY_UPDATE"  # Update existing identity
    REVOKE = "IDENTITY_REVOKE"  # Revoke identity
    QUERY = "IDENTITY_QUERY"  # Query identity (read-only, not in consensus)


@dataclass
class IdentityRecord:
    """
    Identity record in registry.

    Stores minimal information for identity lookup and verification.
    Full identity certificate stored elsewhere (IPFS, etc.)
    """

    lct_id: str  # Full LCT identity string
    lineage: str  # Lineage component (e.g., "alice.assistant1")
    context: str  # Context component (e.g., "Thor")
    task: str  # Task component (e.g., "perception")

    # Public keys
    creator_pubkey: str  # Creator's Ed25519 public key
    platform_pubkey: str  # Platform's Ed25519 public key

    # Metadata
    registered_at: float = field(default_factory=time.time)
    updated_at: float = 0.0
    revoked_at: float = 0.0
    is_revoked: bool = False

    # Registry metadata
    block_number: int = 0  # Block where registered
    transaction_hash: str = ""  # Transaction hash

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "lct_id": self.lct_id,
            "lineage": self.lineage,
            "context": self.context,
            "task": self.task,
            "creator_pubkey": self.creator_pubkey,
            "platform_pubkey": self.platform_pubkey,
            "registered_at": self.registered_at,
            "updated_at": self.updated_at,
            "revoked_at": self.revoked_at,
            "is_revoked": self.is_revoked,
            "block_number": self.block_number,
            "transaction_hash": self.transaction_hash
        }

    def hash(self) -> str:
        """Compute record hash"""
        record_json = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(record_json.encode()).hexdigest()


@dataclass
class IdentityRegisterTransaction:
    """
    Transaction to register new identity in registry.

    Embedded in consensus block for Byzantine fault-tolerant storage.
    """

    type: str = "IDENTITY_REGISTER"
    lct_id: str = ""  # Full LCT identity string
    lineage: str = ""
    context: str = ""
    task: str = ""
    creator_pubkey: str = ""  # Creator's public key
    platform_pubkey: str = ""  # Platform's public key
    identity_certificate: Dict[str, Any] = field(default_factory=dict)  # Full LCT identity cert
    signature: str = ""  # Signature by creator
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "type": self.type,
            "lct_id": self.lct_id,
            "lineage": self.lineage,
            "context": self.context,
            "task": self.task,
            "creator_pubkey": self.creator_pubkey,
            "platform_pubkey": self.platform_pubkey,
            "identity_certificate": self.identity_certificate,
            "signature": self.signature,
            "timestamp": self.timestamp
        }

    def signable_content(self) -> str:
        """Content to sign (excludes signature)"""
        data = {
            "type": self.type,
            "lct_id": self.lct_id,
            "lineage": self.lineage,
            "context": self.context,
            "task": self.task,
            "creator_pubkey": self.creator_pubkey,
            "platform_pubkey": self.platform_pubkey,
            "timestamp": self.timestamp
        }
        return json.dumps(data, sort_keys=True)


@dataclass
class IdentityRevokeTransaction:
    """
    Transaction to revoke identity.

    Requires signature by creator or platform.
    """

    type: str = "IDENTITY_REVOKE"
    lct_id: str = ""  # Identity to revoke
    reason: str = ""  # Reason for revocation
    revoker: str = ""  # Who revoked (creator or platform)
    signature: str = ""  # Signature by revoker
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "type": self.type,
            "lct_id": self.lct_id,
            "reason": self.reason,
            "revoker": self.revoker,
            "signature": self.signature,
            "timestamp": self.timestamp
        }

    def signable_content(self) -> str:
        """Content to sign (excludes signature)"""
        data = {
            "type": self.type,
            "lct_id": self.lct_id,
            "reason": self.reason,
            "revoker": self.revoker,
            "timestamp": self.timestamp
        }
        return json.dumps(data, sort_keys=True)


class IdentityRegistry:
    """
    Decentralized identity registry.

    Stores identity records in-memory, backed by consensus blockchain.
    Provides lookup by LCT ID, lineage, context, or task.
    """

    def __init__(self, platform_name: str):
        """
        Initialize identity registry.

        Args:
            platform_name: This platform's name
        """
        self.platform_name = platform_name

        # Primary storage (lct_id -> record)
        self.identities: Dict[str, IdentityRecord] = {}

        # Indexes for fast lookup
        self.by_lineage: Dict[str, List[str]] = {}  # lineage -> [lct_ids]
        self.by_context: Dict[str, List[str]] = {}  # context -> [lct_ids]
        self.by_task: Dict[str, List[str]] = {}  # task -> [lct_ids]

        # Statistics
        self.total_registered = 0
        self.total_revoked = 0
        self.total_queries = 0

    def register(
        self,
        lct_id: str,
        lineage: str,
        context: str,
        task: str,
        creator_pubkey: str,
        platform_pubkey: str,
        block_number: int,
        transaction_hash: str
    ) -> Tuple[bool, str]:
        """
        Register new identity.

        Args:
            lct_id: Full LCT identity string
            lineage: Lineage component
            context: Context component
            task: Task component
            creator_pubkey: Creator's public key
            platform_pubkey: Platform's public key
            block_number: Block number where registered
            transaction_hash: Transaction hash

        Returns:
            (success, reason) tuple

        Examples:
            >>> success, reason = registry.register(
            ...     lct_id="lct:web4:agent:alice@Thor#perception",
            ...     lineage="alice",
            ...     context="Thor",
            ...     task="perception",
            ...     creator_pubkey="ed25519:ABC123",
            ...     platform_pubkey="ed25519:DEF456",
            ...     block_number=42,
            ...     transaction_hash="abc123def456"
            ... )
        """
        # Check if already registered
        if lct_id in self.identities:
            existing = self.identities[lct_id]
            if not existing.is_revoked:
                return (False, f"Identity already registered: {lct_id}")

        # Create record
        record = IdentityRecord(
            lct_id=lct_id,
            lineage=lineage,
            context=context,
            task=task,
            creator_pubkey=creator_pubkey,
            platform_pubkey=platform_pubkey,
            registered_at=time.time(),
            block_number=block_number,
            transaction_hash=transaction_hash
        )

        # Store record
        self.identities[lct_id] = record

        # Update indexes
        if lineage not in self.by_lineage:
            self.by_lineage[lineage] = []
        self.by_lineage[lineage].append(lct_id)

        if context not in self.by_context:
            self.by_context[context] = []
        self.by_context[context].append(lct_id)

        if task not in self.by_task:
            self.by_task[task] = []
        self.by_task[task].append(lct_id)

        self.total_registered += 1

        return (True, "Identity registered")

    def revoke(
        self,
        lct_id: str,
        reason: str
    ) -> Tuple[bool, str]:
        """
        Revoke identity.

        Args:
            lct_id: Identity to revoke
            reason: Reason for revocation

        Returns:
            (success, reason) tuple

        Examples:
            >>> success, reason = registry.revoke(
            ...     lct_id="lct:web4:agent:alice@Thor#perception",
            ...     reason="COMPROMISED"
            ... )
        """
        # Check if registered
        if lct_id not in self.identities:
            return (False, f"Identity not found: {lct_id}")

        record = self.identities[lct_id]

        # Check if already revoked
        if record.is_revoked:
            return (False, f"Identity already revoked: {lct_id}")

        # Revoke
        record.is_revoked = True
        record.revoked_at = time.time()

        self.total_revoked += 1

        return (True, f"Identity revoked: {reason}")

    def query(self, lct_id: str) -> Optional[IdentityRecord]:
        """
        Query identity by LCT ID.

        Args:
            lct_id: Full LCT identity string

        Returns:
            IdentityRecord or None if not found

        Examples:
            >>> record = registry.query("lct:web4:agent:alice@Thor#perception")
            >>> if record:
            ...     print(f"Creator: {record.creator_pubkey}")
        """
        self.total_queries += 1
        return self.identities.get(lct_id)

    def query_by_lineage(self, lineage: str) -> List[IdentityRecord]:
        """
        Query identities by lineage.

        Args:
            lineage: Lineage component (e.g., "alice" or "alice.assistant1")

        Returns:
            List of IdentityRecords

        Examples:
            >>> records = registry.query_by_lineage("alice")
            >>> print(f"Found {len(records)} identities for alice")
        """
        self.total_queries += 1
        lct_ids = self.by_lineage.get(lineage, [])
        return [self.identities[lct_id] for lct_id in lct_ids if lct_id in self.identities]

    def query_by_context(self, context: str) -> List[IdentityRecord]:
        """
        Query identities by context (platform).

        Args:
            context: Context component (e.g., "Thor")

        Returns:
            List of IdentityRecords
        """
        self.total_queries += 1
        lct_ids = self.by_context.get(context, [])
        return [self.identities[lct_id] for lct_id in lct_ids if lct_id in self.identities]

    def query_by_task(self, task: str) -> List[IdentityRecord]:
        """
        Query identities by task.

        Args:
            task: Task component (e.g., "perception")

        Returns:
            List of IdentityRecords
        """
        self.total_queries += 1
        lct_ids = self.by_task.get(task, [])
        return [self.identities[lct_id] for lct_id in lct_ids if lct_id in self.identities]

    def is_revoked(self, lct_id: str) -> bool:
        """
        Check if identity is revoked.

        Args:
            lct_id: Full LCT identity string

        Returns:
            True if revoked, False otherwise
        """
        record = self.query(lct_id)
        if record is None:
            return False  # Not registered = not revoked
        return record.is_revoked

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        active_count = sum(1 for r in self.identities.values() if not r.is_revoked)

        return {
            "platform": self.platform_name,
            "total_registered": self.total_registered,
            "total_revoked": self.total_revoked,
            "total_queries": self.total_queries,
            "active_identities": active_count,
            "lineages": len(self.by_lineage),
            "contexts": len(self.by_context),
            "tasks": len(self.by_task)
        }

    def export_records(self) -> List[Dict[str, Any]]:
        """
        Export all identity records.

        Returns:
            List of identity record dictionaries

        Used for:
        - Backup/restore
        - Cross-platform synchronization
        - Audit logs
        """
        return [record.to_dict() for record in self.identities.values()]

    def import_records(self, records: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Import identity records.

        Args:
            records: List of identity record dictionaries

        Returns:
            (imported_count, skipped_count) tuple

        Used for:
        - Restore from backup
        - Cross-platform synchronization
        - Genesis block initialization
        """
        imported = 0
        skipped = 0

        for record_dict in records:
            lct_id = record_dict.get("lct_id")

            # Skip if already exists
            if lct_id in self.identities:
                skipped += 1
                continue

            # Create record
            record = IdentityRecord(
                lct_id=record_dict["lct_id"],
                lineage=record_dict["lineage"],
                context=record_dict["context"],
                task=record_dict["task"],
                creator_pubkey=record_dict["creator_pubkey"],
                platform_pubkey=record_dict["platform_pubkey"],
                registered_at=record_dict.get("registered_at", 0.0),
                updated_at=record_dict.get("updated_at", 0.0),
                revoked_at=record_dict.get("revoked_at", 0.0),
                is_revoked=record_dict.get("is_revoked", False),
                block_number=record_dict.get("block_number", 0),
                transaction_hash=record_dict.get("transaction_hash", "")
            )

            # Store
            self.identities[lct_id] = record

            # Update indexes
            if record.lineage not in self.by_lineage:
                self.by_lineage[record.lineage] = []
            self.by_lineage[record.lineage].append(lct_id)

            if record.context not in self.by_context:
                self.by_context[record.context] = []
            self.by_context[record.context].append(lct_id)

            if record.task not in self.by_task:
                self.by_task[record.task] = []
            self.by_task[record.task].append(lct_id)

            imported += 1

        return (imported, skipped)
