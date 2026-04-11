"""
Nonce Tracker for Replay Attack Prevention

Implements nonce-based replay attack prevention for Web4 authorization system.

Key Features:
- Cryptographically random nonce generation
- Single-use enforcement (nonces consumed after verification)
- Time-based expiry (configurable max age)
- Automatic cleanup of expired nonces
- Per-entity nonce tracking
- Comprehensive logging for security audit

Fixes Critical Vulnerability #3:
- Previously no replay attack prevention
- Same authorization request could be reused indefinitely
- Intercepted valid requests could be replayed by attackers
- This implementation prevents signature reuse with single-use nonces

Usage:
    tracker = NonceTracker(max_age_seconds=300)  # 5 minute window

    # Generate nonce for authorization request
    nonce = tracker.generate_nonce("entity-001")

    # Client includes nonce in signed request
    # Server verifies nonce (marks as used)
    valid, msg = tracker.verify_and_consume("entity-001", nonce)
    if not valid:
        # Replay attack detected
        deny_authorization()

Author: Claude (Anthropic AI), autonomous security hardening
Date: November 9, 2025
"""

import secrets
import time
import logging
from typing import Dict, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime, timezone


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NonceEntry:
    """Single nonce record."""
    nonce: str
    entity_id: str
    created_at: float  # Unix timestamp
    expires_at: float  # Unix timestamp
    consumed: bool = False
    consumed_at: Optional[float] = None


class NonceTracker:
    """
    Track nonces to prevent replay attacks.

    Nonces are single-use tokens that prevent an attacker from
    reusing intercepted authorization requests.
    """

    def __init__(self, max_age_seconds: int = 300):
        """
        Initialize nonce tracker.

        Args:
            max_age_seconds: Maximum age of nonce before expiry (default 5 minutes)
        """
        self.max_age_seconds = max_age_seconds
        self.nonces: Dict[str, NonceEntry] = {}  # nonce -> entry
        self.entity_nonces: Dict[str, Set[str]] = {}  # entity_id -> set of nonces

        logger.info(f"NonceTracker initialized (max_age: {max_age_seconds}s)")

    def generate_nonce(self, entity_id: str) -> str:
        """
        Generate cryptographically random nonce.

        Uses secrets.token_urlsafe() which is cryptographically strong
        and suitable for security-sensitive applications.

        Args:
            entity_id: Entity ID requesting nonce

        Returns:
            Base64-encoded random nonce (256 bits of entropy)
        """
        # Generate 32 bytes (256 bits) of cryptographically random data
        nonce = secrets.token_urlsafe(32)

        now = time.time()

        # Create nonce entry
        entry = NonceEntry(
            nonce=nonce,
            entity_id=entity_id,
            created_at=now,
            expires_at=now + self.max_age_seconds,
            consumed=False
        )

        # Store nonce
        self.nonces[nonce] = entry

        # Track by entity
        if entity_id not in self.entity_nonces:
            self.entity_nonces[entity_id] = set()
        self.entity_nonces[entity_id].add(nonce)

        logger.debug(
            f"Generated nonce for {entity_id}: {nonce[:8]}... "
            f"(expires in {self.max_age_seconds}s)"
        )

        return nonce

    def verify_and_consume(
        self,
        entity_id: str,
        nonce: str
    ) -> Tuple[bool, str]:
        """
        Verify nonce is valid and mark as consumed (single-use).

        This is the main enforcement function called during authorization.

        Args:
            entity_id: Entity ID using the nonce
            nonce: Nonce to verify

        Returns:
            Tuple of (valid: bool, message: str)
        """
        # Check if nonce exists
        if nonce not in self.nonces:
            logger.warning(
                f"Replay attack detected: Unknown nonce from {entity_id} "
                f"(nonce: {nonce[:8]}...)"
            )
            return False, "Nonce not found (may have expired or never generated)"

        entry = self.nonces[nonce]

        # Check if nonce is for correct entity
        if entry.entity_id != entity_id:
            logger.warning(
                f"Nonce mismatch: {nonce[:8]}... issued for {entry.entity_id}, "
                f"but used by {entity_id}"
            )
            return False, f"Nonce issued for {entry.entity_id}, not {entity_id}"

        # Check if already consumed (REPLAY ATTACK)
        if entry.consumed:
            logger.error(
                f"🚨 REPLAY ATTACK DETECTED: {entity_id} attempted to reuse "
                f"nonce {nonce[:8]}... (consumed at {entry.consumed_at})"
            )
            return False, "Nonce already used (replay attack detected)"

        # Check if expired
        now = time.time()
        if now > entry.expires_at:
            age = now - entry.created_at
            logger.warning(
                f"Expired nonce from {entity_id}: {nonce[:8]}... "
                f"(age: {age:.1f}s, max: {self.max_age_seconds}s)"
            )
            # Clean up expired nonce
            del self.nonces[nonce]
            if entity_id in self.entity_nonces:
                self.entity_nonces[entity_id].discard(nonce)
            return False, f"Nonce expired (max age: {self.max_age_seconds}s)"

        # ✅ Valid! Consume the nonce (mark as used)
        entry.consumed = True
        entry.consumed_at = now

        logger.info(
            f"✅ Nonce verified and consumed: {entity_id} "
            f"(nonce: {nonce[:8]}..., age: {now - entry.created_at:.2f}s)"
        )

        return True, "Nonce valid and consumed"

    def is_valid(self, entity_id: str, nonce: str) -> bool:
        """
        Check if nonce is valid WITHOUT consuming it.

        Use this for read-only validation. For actual authorization,
        use verify_and_consume() instead.

        Args:
            entity_id: Entity ID to check
            nonce: Nonce to validate

        Returns:
            True if valid (exists, not consumed, not expired)
        """
        if nonce not in self.nonces:
            return False

        entry = self.nonces[nonce]

        if entry.entity_id != entity_id:
            return False

        if entry.consumed:
            return False

        now = time.time()
        if now > entry.expires_at:
            return False

        return True

    def cleanup_expired(self) -> int:
        """
        Remove expired nonces (call periodically).

        Returns:
            Number of nonces removed
        """
        now = time.time()
        expired_nonces = []

        for nonce, entry in self.nonces.items():
            if now > entry.expires_at:
                expired_nonces.append(nonce)

        # Remove expired nonces
        for nonce in expired_nonces:
            entry = self.nonces[nonce]
            entity_id = entry.entity_id

            del self.nonces[nonce]

            if entity_id in self.entity_nonces:
                self.entity_nonces[entity_id].discard(nonce)
                if not self.entity_nonces[entity_id]:
                    del self.entity_nonces[entity_id]

        if expired_nonces:
            logger.info(f"Cleaned up {len(expired_nonces)} expired nonces")

        return len(expired_nonces)

    def cleanup_consumed(self, min_age_seconds: int = 60) -> int:
        """
        Remove consumed nonces older than min_age (save memory).

        Keep recent consumed nonces for audit trail, but remove
        old ones after they're no longer needed.

        Args:
            min_age_seconds: Minimum age before removing consumed nonce

        Returns:
            Number of nonces removed
        """
        now = time.time()
        old_consumed = []

        for nonce, entry in self.nonces.items():
            if entry.consumed and entry.consumed_at:
                age = now - entry.consumed_at
                if age > min_age_seconds:
                    old_consumed.append(nonce)

        # Remove old consumed nonces
        for nonce in old_consumed:
            entry = self.nonces[nonce]
            entity_id = entry.entity_id

            del self.nonces[nonce]

            if entity_id in self.entity_nonces:
                self.entity_nonces[entity_id].discard(nonce)
                if not self.entity_nonces[entity_id]:
                    del self.entity_nonces[entity_id]

        if old_consumed:
            logger.debug(f"Cleaned up {len(old_consumed)} old consumed nonces")

        return len(old_consumed)

    def get_entity_nonces(self, entity_id: str) -> list:
        """
        Get all nonces for entity (for debugging/audit).

        Args:
            entity_id: Entity ID

        Returns:
            List of nonce strings
        """
        if entity_id not in self.entity_nonces:
            return []

        return list(self.entity_nonces[entity_id])

    def get_stats(self) -> Dict:
        """
        Get tracker statistics.

        Returns:
            Dictionary with stats (total, consumed, expired, by entity)
        """
        now = time.time()

        total = len(self.nonces)
        consumed = sum(1 for entry in self.nonces.values() if entry.consumed)
        expired = sum(1 for entry in self.nonces.values() if now > entry.expires_at)
        valid = total - consumed - expired

        stats = {
            "total_nonces": total,
            "valid": valid,
            "consumed": consumed,
            "expired": expired,
            "entities": len(self.entity_nonces),
            "by_entity": {
                entity_id: len(nonces)
                for entity_id, nonces in self.entity_nonces.items()
            }
        }

        return stats

    def revoke_entity_nonces(self, entity_id: str) -> int:
        """
        Revoke all nonces for an entity (emergency use).

        Use this if an entity's credentials are compromised and
        you need to invalidate all their pending requests.

        Args:
            entity_id: Entity ID to revoke nonces for

        Returns:
            Number of nonces revoked
        """
        if entity_id not in self.entity_nonces:
            return 0

        nonces_to_remove = list(self.entity_nonces[entity_id])

        for nonce in nonces_to_remove:
            if nonce in self.nonces:
                del self.nonces[nonce]

        del self.entity_nonces[entity_id]

        logger.warning(
            f"Emergency revocation: All nonces for {entity_id} invalidated "
            f"({len(nonces_to_remove)} nonces)"
        )

        return len(nonces_to_remove)


# Example usage
if __name__ == "__main__":
    print("Nonce Tracker - Example Usage\n" + "="*60)

    # Create tracker
    print("\n1. Creating nonce tracker (5 second expiry for demo)...")
    tracker = NonceTracker(max_age_seconds=5)

    # Generate nonces
    print("\n2. Generating nonces for entity-001...")
    nonce1 = tracker.generate_nonce("entity-001")
    nonce2 = tracker.generate_nonce("entity-001")
    print(f"  Nonce 1: {nonce1[:16]}...")
    print(f"  Nonce 2: {nonce2[:16]}...")

    # Verify and consume first nonce
    print("\n3. Using first nonce (should succeed)...")
    valid, msg = tracker.verify_and_consume("entity-001", nonce1)
    print(f"  Valid? {valid}")
    print(f"  Message: {msg}")

    # Try to reuse first nonce (REPLAY ATTACK)
    print("\n4. Attempting to reuse first nonce (REPLAY ATTACK)...")
    valid, msg = tracker.verify_and_consume("entity-001", nonce1)
    print(f"  Valid? {valid}")
    print(f"  Message: {msg}")

    # Try wrong entity ID
    print("\n5. Attempting to use nonce2 with wrong entity...")
    valid, msg = tracker.verify_and_consume("entity-002", nonce2)
    print(f"  Valid? {valid}")
    print(f"  Message: {msg}")

    # Use correct nonce
    print("\n6. Using nonce2 correctly...")
    valid, msg = tracker.verify_and_consume("entity-001", nonce2)
    print(f"  Valid? {valid}")
    print(f"  Message: {msg}")

    # Test expiry
    print("\n7. Testing nonce expiry...")
    nonce3 = tracker.generate_nonce("entity-001")
    print(f"  Generated nonce3: {nonce3[:16]}...")
    print("  Waiting 6 seconds for expiry...")
    time.sleep(6)
    valid, msg = tracker.verify_and_consume("entity-001", nonce3)
    print(f"  Valid? {valid}")
    print(f"  Message: {msg}")

    # Show stats
    print("\n8. Tracker statistics...")
    stats = tracker.get_stats()
    print(f"  Total nonces: {stats['total_nonces']}")
    print(f"  Valid: {stats['valid']}")
    print(f"  Consumed: {stats['consumed']}")
    print(f"  Expired: {stats['expired']}")

    # Cleanup
    print("\n9. Cleaning up expired nonces...")
    cleaned = tracker.cleanup_expired()
    print(f"  Removed {cleaned} expired nonces")

    print("\n" + "="*60)
    print("✅ Nonce Tracker operational - Replay attacks prevented!")
    print("="*60)
    print("\nKey capability: Authorization requests now single-use!")
    print("Security impact: Intercepted requests cannot be replayed.")
