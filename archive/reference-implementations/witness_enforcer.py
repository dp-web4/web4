"""
Witness Enforcer for Delegation Validation

Implements witness enforcement for Web4 delegations - requiring trusted
third parties to attest to delegation authenticity.

Key Features:
- Witness signature verification
- Minimum witness count requirements
- Witness reputation tracking
- Trust-weighted witness validation
- Quorum-based authorization
- Witness discovery and selection

Fixes Critical Vulnerability #6:
- Previously no witness enforcement
- Delegations could be fabricated without third-party validation
- No distributed validation mechanism
- Single point of failure in delegation chain
- This implementation requires witness attestation

Usage:
    enforcer = WitnessEnforcer(min_witnesses=2, min_trust_score=0.7)

    # Add witnesses to delegation
    delegation.add_witness(witness_lct, witness_signature)

    # Verify witnesses during authorization
    valid, msg = enforcer.verify_witnesses(delegation)
    if not valid:
        deny_authorization()

Author: Claude (Anthropic AI), autonomous security hardening
Date: November 10, 2025
"""

import logging
from typing import List, Set, Optional, Tuple, Dict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PublicKey,
    Ed25519PrivateKey
)
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WitnessRole(Enum):
    """Witness role in validation."""
    AUTHORITY = "authority"        # Trusted authority (high weight)
    PEER = "peer"                  # Peer witness (medium weight)
    OBSERVER = "observer"          # Observer (low weight)


@dataclass
class WitnessSignature:
    """Witness signature for a delegation."""
    witness_id: str                     # Witness LCT identifier
    witness_public_key: bytes           # Witness public key
    signature: bytes                    # Ed25519 signature
    role: WitnessRole = WitnessRole.PEER
    timestamp: str = field(default_factory=lambda:
        datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'))
    trust_score: float = 0.5           # Witness trust score (0.0-1.0)

    def verify(self, delegation_hash: bytes) -> bool:
        """Verify witness signature."""
        try:
            public_key = Ed25519PublicKey.from_public_bytes(
                self.witness_public_key
            )
            public_key.verify(self.signature, delegation_hash)
            return True
        except InvalidSignature:
            return False
        except Exception as e:
            logger.error(f"Error verifying witness signature: {e}")
            return False


@dataclass
class WitnessRequirement:
    """Witness requirements for a delegation."""
    min_witnesses: int = 1                      # Minimum witness count
    min_trust_score: float = 0.5               # Minimum individual trust
    min_aggregate_trust: float = 1.0           # Minimum total trust
    required_roles: Set[WitnessRole] = field(
        default_factory=set
    )                                           # Required witness roles
    required_witnesses: Set[str] = field(
        default_factory=set
    )                                           # Specific required witnesses

    def is_satisfied(
        self,
        witnesses: List[WitnessSignature]
    ) -> Tuple[bool, str]:
        """Check if witness requirements are satisfied."""

        # Check minimum count
        if len(witnesses) < self.min_witnesses:
            return False, (
                f"Insufficient witnesses: {len(witnesses)} "
                f"(min: {self.min_witnesses})"
            )

        # Check individual trust scores
        low_trust = [w for w in witnesses if w.trust_score < self.min_trust_score]
        if low_trust:
            return False, (
                f"Witness trust too low: {low_trust[0].witness_id} "
                f"({low_trust[0].trust_score:.2f} < {self.min_trust_score})"
            )

        # Check aggregate trust
        total_trust = sum(w.trust_score for w in witnesses)
        if total_trust < self.min_aggregate_trust:
            return False, (
                f"Aggregate trust too low: {total_trust:.2f} "
                f"(min: {self.min_aggregate_trust})"
            )

        # Check required roles
        witness_roles = {w.role for w in witnesses}
        missing_roles = self.required_roles - witness_roles
        if missing_roles:
            return False, f"Missing required roles: {missing_roles}"

        # Check required witnesses
        witness_ids = {w.witness_id for w in witnesses}
        missing_witnesses = self.required_witnesses - witness_ids
        if missing_witnesses:
            return False, f"Missing required witnesses: {missing_witnesses}"

        return True, "Witness requirements satisfied"


class WitnessEnforcer:
    """
    Enforce witness requirements for delegations.

    Validates that delegations have sufficient witness attestations
    before authorizing actions.
    """

    def __init__(
        self,
        min_witnesses: int = 1,
        min_trust_score: float = 0.5,
        min_aggregate_trust: float = 1.0
    ):
        """
        Initialize witness enforcer.

        Args:
            min_witnesses: Minimum number of witnesses required
            min_trust_score: Minimum trust score per witness
            min_aggregate_trust: Minimum total trust score
        """
        self.default_requirements = WitnessRequirement(
            min_witnesses=min_witnesses,
            min_trust_score=min_trust_score,
            min_aggregate_trust=min_aggregate_trust
        )

        # Witness trust registry
        self.witness_trust: Dict[str, float] = {}

        # Witness reputation history
        self.witness_history: Dict[str, List[bool]] = {}

        logger.info(
            f"WitnessEnforcer initialized "
            f"(min_witnesses: {min_witnesses}, "
            f"min_trust: {min_trust_score}, "
            f"min_aggregate: {min_aggregate_trust})"
        )

    def verify_witnesses(
        self,
        delegation_hash: bytes,
        witnesses: List[WitnessSignature],
        requirements: Optional[WitnessRequirement] = None
    ) -> Tuple[bool, str]:
        """
        Verify witnesses for a delegation.

        Args:
            delegation_hash: Hash of delegation being witnessed
            witnesses: List of witness signatures
            requirements: Witness requirements (uses default if None)

        Returns:
            Tuple of (valid: bool, message: str)
        """
        if requirements is None:
            requirements = self.default_requirements

        # No witnesses provided
        if not witnesses:
            logger.warning("No witnesses provided for delegation")
            return False, "No witnesses provided"

        # Verify each witness signature
        valid_witnesses = []
        for witness in witnesses:
            if witness.verify(delegation_hash):
                # Update trust score from registry
                if witness.witness_id in self.witness_trust:
                    witness.trust_score = self.witness_trust[witness.witness_id]

                valid_witnesses.append(witness)
                logger.debug(
                    f"✅ Valid witness: {witness.witness_id} "
                    f"(trust: {witness.trust_score:.2f})"
                )
            else:
                logger.warning(
                    f"❌ Invalid witness signature: {witness.witness_id}"
                )

        # Check if requirements satisfied
        satisfied, msg = requirements.is_satisfied(valid_witnesses)

        if satisfied:
            logger.info(
                f"✅ Witness enforcement passed: {len(valid_witnesses)} witnesses, "
                f"aggregate trust: {sum(w.trust_score for w in valid_witnesses):.2f}"
            )

            # Update witness reputation (positive)
            for witness in valid_witnesses:
                self._update_reputation(witness.witness_id, True)
        else:
            logger.warning(f"❌ Witness enforcement failed: {msg}")

            # Update witness reputation (negative for invalid)
            for witness in witnesses:
                if witness not in valid_witnesses:
                    self._update_reputation(witness.witness_id, False)

        return satisfied, msg

    def register_witness(
        self,
        witness_id: str,
        initial_trust: float = 0.5
    ):
        """
        Register a witness with initial trust score.

        Args:
            witness_id: Witness LCT identifier
            initial_trust: Initial trust score (0.0-1.0)
        """
        initial_trust = max(0.0, min(1.0, initial_trust))
        self.witness_trust[witness_id] = initial_trust
        self.witness_history[witness_id] = []

        logger.info(f"Registered witness: {witness_id} (trust: {initial_trust:.2f})")

    def update_witness_trust(
        self,
        witness_id: str,
        trust_score: float
    ):
        """
        Update witness trust score.

        Args:
            witness_id: Witness LCT identifier
            trust_score: New trust score (0.0-1.0)
        """
        trust_score = max(0.0, min(1.0, trust_score))
        old_trust = self.witness_trust.get(witness_id, 0.5)
        self.witness_trust[witness_id] = trust_score

        logger.info(
            f"Updated witness trust: {witness_id} "
            f"({old_trust:.2f} → {trust_score:.2f})"
        )

    def get_witness_trust(self, witness_id: str) -> float:
        """Get witness trust score."""
        return self.witness_trust.get(witness_id, 0.5)

    def get_witness_reputation(self, witness_id: str) -> Tuple[float, int, int]:
        """
        Get witness reputation metrics.

        Returns:
            Tuple of (success_rate, successful_verifications, total_verifications)
        """
        history = self.witness_history.get(witness_id, [])
        if not history:
            return 0.5, 0, 0

        successful = sum(history)
        total = len(history)
        success_rate = successful / total if total > 0 else 0.5

        return success_rate, successful, total

    def _update_reputation(self, witness_id: str, success: bool):
        """Update witness reputation history (internal)."""
        if witness_id not in self.witness_history:
            self.witness_history[witness_id] = []

        self.witness_history[witness_id].append(success)

        # Keep only last 100 entries
        if len(self.witness_history[witness_id]) > 100:
            self.witness_history[witness_id] = self.witness_history[witness_id][-100:]

        # Update trust based on recent reputation
        recent_history = self.witness_history[witness_id][-20:]
        success_rate = sum(recent_history) / len(recent_history)

        # Adjust trust score based on reputation
        current_trust = self.witness_trust.get(witness_id, 0.5)
        new_trust = (current_trust * 0.8) + (success_rate * 0.2)
        self.witness_trust[witness_id] = new_trust

    def create_witness_signature(
        self,
        delegation_hash: bytes,
        witness_id: str,
        witness_private_key: Ed25519PrivateKey,
        role: WitnessRole = WitnessRole.PEER
    ) -> WitnessSignature:
        """
        Create a witness signature for a delegation.

        Args:
            delegation_hash: Hash of delegation to witness
            witness_id: Witness LCT identifier
            witness_private_key: Witness private key
            role: Witness role

        Returns:
            WitnessSignature object
        """
        # Sign delegation hash
        signature = witness_private_key.sign(delegation_hash)

        # Get public key
        public_key = witness_private_key.public_key()
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        # Get trust score
        trust_score = self.get_witness_trust(witness_id)

        witness_sig = WitnessSignature(
            witness_id=witness_id,
            witness_public_key=public_key_bytes,
            signature=signature,
            role=role,
            trust_score=trust_score
        )

        logger.debug(
            f"Created witness signature: {witness_id} "
            f"(role: {role.value}, trust: {trust_score:.2f})"
        )

        return witness_sig

    def get_trusted_witnesses(
        self,
        min_trust: float = 0.7,
        min_verifications: int = 10
    ) -> List[str]:
        """
        Get list of highly trusted witnesses.

        Args:
            min_trust: Minimum trust score
            min_verifications: Minimum verification count

        Returns:
            List of trusted witness IDs
        """
        trusted = []

        for witness_id, trust in self.witness_trust.items():
            if trust >= min_trust:
                _, successful, total = self.get_witness_reputation(witness_id)
                if total >= min_verifications:
                    trusted.append(witness_id)

        return trusted

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "default_requirements": {
                "min_witnesses": self.default_requirements.min_witnesses,
                "min_trust_score": self.default_requirements.min_trust_score,
                "min_aggregate_trust": self.default_requirements.min_aggregate_trust
            },
            "witness_trust": self.witness_trust,
            "witness_history": {
                k: list(v) for k, v in self.witness_history.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'WitnessEnforcer':
        """Create from dictionary."""
        req = data.get("default_requirements", {})
        enforcer = cls(
            min_witnesses=req.get("min_witnesses", 1),
            min_trust_score=req.get("min_trust_score", 0.5),
            min_aggregate_trust=req.get("min_aggregate_trust", 1.0)
        )

        enforcer.witness_trust = data.get("witness_trust", {})
        enforcer.witness_history = {
            k: list(v) for k, v in data.get("witness_history", {}).items()
        }

        return enforcer


# Example usage
if __name__ == "__main__":
    print("Witness Enforcer - Example Usage\n" + "="*60)

    from cryptography.hazmat.primitives.asymmetric import ed25519
    import hashlib

    # Create enforcer
    print("\n1. Creating witness enforcer...")
    enforcer = WitnessEnforcer(
        min_witnesses=2,
        min_trust_score=0.6,
        min_aggregate_trust=1.5
    )

    # Register witnesses
    print("\n2. Registering witnesses...")
    enforcer.register_witness("witness-alice", initial_trust=0.8)
    enforcer.register_witness("witness-bob", initial_trust=0.7)
    enforcer.register_witness("witness-charlie", initial_trust=0.5)

    # Create a fake delegation hash
    print("\n3. Creating delegation hash...")
    delegation_data = b"delegation:alice->bob:github_access"
    delegation_hash = hashlib.sha256(delegation_data).digest()
    print(f"  Delegation: {delegation_data.decode()}")

    # Create witness keys
    print("\n4. Creating witness signatures...")
    alice_key = ed25519.Ed25519PrivateKey.generate()
    bob_key = ed25519.Ed25519PrivateKey.generate()

    # Create witness signatures
    witnesses = [
        enforcer.create_witness_signature(
            delegation_hash,
            "witness-alice",
            alice_key,
            role=WitnessRole.AUTHORITY
        ),
        enforcer.create_witness_signature(
            delegation_hash,
            "witness-bob",
            bob_key,
            role=WitnessRole.PEER
        )
    ]

    print(f"  Created {len(witnesses)} witness signatures")

    # Verify witnesses
    print("\n5. Verifying witnesses...")
    valid, msg = enforcer.verify_witnesses(delegation_hash, witnesses)
    status = "✅ VALID" if valid else "❌ INVALID"
    print(f"  {status}: {msg}")

    # Test insufficient witnesses
    print("\n6. Testing insufficient witnesses (should fail)...")
    valid, msg = enforcer.verify_witnesses(delegation_hash, [witnesses[0]])
    status = "✅ VALID" if valid else "❌ INVALID"
    print(f"  {status}: {msg}")

    # Get trusted witnesses
    print("\n7. Getting trusted witnesses...")
    trusted = enforcer.get_trusted_witnesses(min_trust=0.6)
    print(f"  Trusted witnesses (trust >= 0.6): {trusted}")

    # Show reputation
    print("\n8. Witness reputation...")
    for witness_id in ["witness-alice", "witness-bob"]:
        rate, successful, total = enforcer.get_witness_reputation(witness_id)
        print(f"  {witness_id}: {rate*100:.0f}% ({successful}/{total})")

    print("\n" + "="*60)
    print("✅ Witness Enforcer operational - Distributed validation enabled!")
    print("="*60)
    print("\nKey capabilities:")
    print("- Cryptographic witness signature verification")
    print("- Minimum witness count requirements")
    print("- Trust-weighted validation")
    print("- Witness reputation tracking")
    print("- Role-based witness requirements")
