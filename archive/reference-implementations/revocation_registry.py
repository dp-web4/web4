"""
Revocation Registry for LCT Delegations

Implements delegation revocation mechanism for Web4 authorization system.

Key Features:
- Sign and verify delegation revocations
- Prevent use of compromised credentials
- Emergency stop mechanism for security incidents
- Persistent storage of revocations
- Audit trail of all revocations

Fixes Critical Vulnerability #2:
- Previously no way to revoke compromised delegations
- Compromised keys remained valid forever
- No emergency stop for security incidents
- This implementation enables delegation revocation and verification

Usage:
    registry = RevocationRegistry(storage_path="revocations.json")

    # Revoke a delegation (must have delegator's private key)
    revocation = registry.revoke_delegation(
        delegation=delegation,
        delegator_private_key=dennis_private_key,
        reason="security_incident"
    )

    # Check if delegation is revoked
    if registry.is_revoked(delegation):
        # Deny authorization
        pass

Author: Claude (Anthropic AI), autonomous security hardening
Date: November 9, 2025
"""

import json
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path

# Import from lct_identity module
from lct_identity import Delegation, sign_data, verify_signature, Ed25519PrivateKey, Ed25519PublicKey


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RevocationEntry:
    """Single revocation record."""
    version: str = "1.0"
    delegation_hash: str = ""  # SHA256 of delegation signature (unique ID)
    delegator: str = ""  # Entity ID of delegator
    delegatee: str = ""  # Entity ID of delegatee
    revoked_at: str = ""  # ISO 8601 timestamp
    reason: str = ""  # Reason code or description
    revoker_signature: str = ""  # Signed by delegator to prove authority
    metadata: Dict = None  # Optional additional info

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if not self.revoked_at:
            self.revoked_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def signing_data(self) -> bytes:
        """Get canonical data for signing (excludes signature field)."""
        d = self.to_dict()
        d.pop('revoker_signature', None)  # Exclude signature
        canonical = json.dumps(d, sort_keys=True, separators=(',', ':'))
        return canonical.encode('utf-8')


class RevocationRegistry:
    """Registry of revoked delegations."""

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize revocation registry.

        Args:
            storage_path: Path to JSON file for persistent storage (optional)
        """
        self.revoked: Dict[str, RevocationEntry] = {}  # delegation_hash -> entry
        self.storage_path = storage_path

        if storage_path:
            self.storage_file = Path(storage_path)
            self.load_from_storage()
        else:
            self.storage_file = None

        logger.info(f"RevocationRegistry initialized with {len(self.revoked)} revoked delegations")

    def _compute_delegation_hash(self, delegation: Delegation) -> str:
        """
        Compute unique hash for delegation.

        Uses SHA256 of delegation signature as unique identifier.
        """
        if not delegation.signature:
            raise ValueError("Delegation must be signed to compute hash")

        return hashlib.sha256(
            delegation.signature.encode('utf-8')
        ).hexdigest()

    def revoke_delegation(
        self,
        delegation: Delegation,
        delegator_private_key: Ed25519PrivateKey,
        reason: str = "revoked",
        metadata: Optional[Dict] = None
    ) -> RevocationEntry:
        """
        Revoke a delegation (must be signed by delegator).

        Args:
            delegation: Delegation to revoke
            delegator_private_key: Delegator's private key (to sign revocation)
            reason: Reason for revocation (e.g., "security_incident", "contract_ended")
            metadata: Optional additional info (e.g., {"incident_report": "IR-2025-001"})

        Returns:
            RevocationEntry that was created

        Raises:
            ValueError: If delegation not signed or already revoked
        """
        # Validate delegation
        if not delegation.signature:
            raise ValueError("Cannot revoke unsigned delegation")

        # Compute delegation hash (unique ID)
        delegation_hash = self._compute_delegation_hash(delegation)

        # Check if already revoked
        if delegation_hash in self.revoked:
            logger.warning(f"Delegation {delegation_hash[:8]}... already revoked")
            return self.revoked[delegation_hash]

        # Create revocation entry
        entry = RevocationEntry(
            delegation_hash=delegation_hash,
            delegator=delegation.delegator,
            delegatee=delegation.delegatee,
            revoked_at=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            reason=reason,
            metadata=metadata or {}
        )

        # Sign revocation with delegator's private key
        signing_data = entry.signing_data()
        entry.revoker_signature = sign_data(signing_data, delegator_private_key)

        # Store revocation
        self.revoked[delegation_hash] = entry

        # Persist to disk
        if self.storage_file:
            self.save_to_storage()

        logger.warning(
            f"Delegation revoked: {delegation.delegatee} by {delegation.delegator} "
            f"(hash: {delegation_hash[:8]}..., reason: {reason})"
        )

        return entry

    def is_revoked(self, delegation: Delegation) -> bool:
        """
        Check if delegation has been revoked.

        Args:
            delegation: Delegation to check

        Returns:
            True if revoked, False otherwise
        """
        if not delegation.signature:
            logger.warning("Cannot check revocation status of unsigned delegation")
            return False

        try:
            delegation_hash = self._compute_delegation_hash(delegation)
            is_revoked = delegation_hash in self.revoked

            if is_revoked:
                entry = self.revoked[delegation_hash]
                logger.info(
                    f"Delegation is REVOKED: {delegation.delegatee} "
                    f"(revoked at {entry.revoked_at}, reason: {entry.reason})"
                )

            return is_revoked

        except Exception as e:
            logger.error(f"Error checking revocation status: {e}")
            return False

    def get_revocation_info(self, delegation: Delegation) -> Optional[RevocationEntry]:
        """
        Get revocation details if delegation is revoked.

        Args:
            delegation: Delegation to check

        Returns:
            RevocationEntry if revoked, None otherwise
        """
        if not delegation.signature:
            return None

        try:
            delegation_hash = self._compute_delegation_hash(delegation)
            return self.revoked.get(delegation_hash)
        except Exception as e:
            logger.error(f"Error getting revocation info: {e}")
            return None

    def verify_revocation_signature(
        self,
        entry: RevocationEntry,
        delegator_public_key: Ed25519PublicKey
    ) -> bool:
        """
        Verify revocation was signed by legitimate delegator.

        This prevents unauthorized revocation - only the delegator
        can revoke their own delegations.

        Args:
            entry: Revocation entry to verify
            delegator_public_key: Delegator's public key

        Returns:
            True if signature is valid
        """
        if not entry.revoker_signature:
            logger.warning("Revocation entry has no signature")
            return False

        try:
            signing_data = entry.signing_data()
            is_valid = verify_signature(
                signing_data,
                entry.revoker_signature,
                delegator_public_key
            )

            if not is_valid:
                logger.warning(
                    f"Invalid revocation signature for {entry.delegatee} "
                    f"by {entry.delegator}"
                )

            return is_valid

        except Exception as e:
            logger.error(f"Error verifying revocation signature: {e}")
            return False

    def list_revocations(
        self,
        delegator: Optional[str] = None,
        delegatee: Optional[str] = None,
        reason: Optional[str] = None
    ) -> List[RevocationEntry]:
        """
        List revocations with optional filtering.

        Args:
            delegator: Filter by delegator entity ID (optional)
            delegatee: Filter by delegatee entity ID (optional)
            reason: Filter by reason (optional)

        Returns:
            List of matching RevocationEntry objects
        """
        results = []

        for entry in self.revoked.values():
            # Apply filters
            if delegator and entry.delegator != delegator:
                continue
            if delegatee and entry.delegatee != delegatee:
                continue
            if reason and entry.reason != reason:
                continue

            results.append(entry)

        return results

    def get_revocation_count(self) -> int:
        """Get total number of revocations."""
        return len(self.revoked)

    def get_stats(self) -> Dict:
        """
        Get revocation statistics.

        Returns:
            Dictionary with stats (counts by reason, delegator, delegatee)
        """
        stats = {
            "total_revocations": len(self.revoked),
            "by_reason": {},
            "by_delegator": {},
            "by_delegatee": {}
        }

        for entry in self.revoked.values():
            # Count by reason
            reason = entry.reason
            stats["by_reason"][reason] = stats["by_reason"].get(reason, 0) + 1

            # Count by delegator
            delegator = entry.delegator
            stats["by_delegator"][delegator] = stats["by_delegator"].get(delegator, 0) + 1

            # Count by delegatee
            delegatee = entry.delegatee
            stats["by_delegatee"][delegatee] = stats["by_delegatee"].get(delegatee, 0) + 1

        return stats

    def save_to_storage(self):
        """Persist revocation registry to disk."""
        if not self.storage_file:
            return

        data = {
            "version": "1.0",
            "saved_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "revocations": {
                hash: entry.to_dict()
                for hash, entry in self.revoked.items()
            }
        }

        # Atomic write (write to temp file, then rename)
        temp_file = self.storage_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            temp_file.rename(self.storage_file)
            logger.debug(f"Revocation registry saved to {self.storage_file}")
        except Exception as e:
            logger.error(f"Failed to save revocation registry: {e}")
            if temp_file.exists():
                temp_file.unlink()

    def load_from_storage(self):
        """Load revocation registry from disk."""
        if not self.storage_file or not self.storage_file.exists():
            logger.info("No existing revocation storage, starting fresh")
            return

        try:
            with open(self.storage_file, 'r') as f:
                data = json.load(f)

            revocations_data = data.get("revocations", {})
            for hash, entry_data in revocations_data.items():
                self.revoked[hash] = RevocationEntry(
                    version=entry_data.get("version", "1.0"),
                    delegation_hash=entry_data["delegation_hash"],
                    delegator=entry_data["delegator"],
                    delegatee=entry_data["delegatee"],
                    revoked_at=entry_data["revoked_at"],
                    reason=entry_data["reason"],
                    revoker_signature=entry_data["revoker_signature"],
                    metadata=entry_data.get("metadata", {})
                )

            logger.info(
                f"Loaded {len(self.revoked)} revocations from {self.storage_file}"
            )

        except Exception as e:
            logger.error(f"Failed to load revocation registry: {e}")


# Example usage
if __name__ == "__main__":
    print("Revocation Registry - Example Usage\n" + "="*60)

    # Import LCT identity examples
    from lct_identity import (
        create_dennis_lct_example,
        create_claude_lct_and_delegation_example
    )

    # Create identities
    print("\n1. Creating LCT identities and delegation...")
    dennis_private, dennis_public, dennis_lct = create_dennis_lct_example()
    claude_private, claude_public, claude_lct, delegation = \
        create_claude_lct_and_delegation_example(
            dennis_private, dennis_public, dennis_lct
        )

    # Create registry
    print("\n2. Creating revocation registry...")
    registry = RevocationRegistry()

    # Check if delegation is revoked (should be False initially)
    print("\n3. Checking revocation status...")
    is_revoked = registry.is_revoked(delegation)
    print(f"  Delegation revoked? {is_revoked}")

    # Revoke the delegation
    print("\n4. Revoking delegation...")
    revocation = registry.revoke_delegation(
        delegation=delegation,
        delegator_private_key=dennis_private,
        reason="security_test",
        metadata={"test": True}
    )
    print(f"  Revoked at: {revocation.revoked_at}")
    print(f"  Reason: {revocation.reason}")

    # Check again (should be True now)
    print("\n5. Checking revocation status after revocation...")
    is_revoked = registry.is_revoked(delegation)
    print(f"  Delegation revoked? {is_revoked}")

    # Get revocation info
    print("\n6. Getting revocation details...")
    info = registry.get_revocation_info(delegation)
    if info:
        print(f"  Delegatee: {info.delegatee}")
        print(f"  Revoked at: {info.revoked_at}")
        print(f"  Reason: {info.reason}")

    # Verify revocation signature
    print("\n7. Verifying revocation signature...")
    signature_valid = registry.verify_revocation_signature(revocation, dennis_public)
    print(f"  Signature valid? {signature_valid}")

    # Get stats
    print("\n8. Registry statistics...")
    stats = registry.get_stats()
    print(f"  Total revocations: {stats['total_revocations']}")
    print(f"  By reason: {stats['by_reason']}")

    print("\n" + "="*60)
    print("✅ Revocation Registry operational - Critical vulnerability fixed!")
    print("="*60)
    print("\nKey capability: Compromised delegations can now be revoked!")
    print("Security impact: Emergency stop mechanism for credentials.")
