#!/usr/bin/env python3
"""
Web4 LCT (Lifecycle-Continuous Trust) Identity System

Provides cryptographic identity for AI agents with accumulated trust.

Phase 1 Implementation (Session 121):
- Core LCTIdentity class
- Key generation and management
- Trust score calculation
- Pattern signing/verification
- Basic cryptographic operations

Future Phases:
- Phase 2: Trust attestation network
- Phase 3: Pattern federation security integration
- Phase 4: Multi-agent testing in ACT
"""

import json
import hashlib
import base64
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field

# Cryptographic imports
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
    print("Warning: cryptography library not available, using mock signatures")


class LCTIdentity:
    """
    Lifecycle-Continuous Trust Identity for AI agents.

    Combines cryptographic identity with accumulated trust metrics.

    Trust accumulates through:
    - Successful interactions (interaction_bonus)
    - Trust attestations from others (attestation_bonus)
    - Identity age (age_bonus)

    Sybil resistance through:
    - High cost to bootstrap trust (1000+ interactions)
    - Attestation network effects
    - Identity age requirements
    - Device fingerprinting
    """

    def __init__(
        self,
        private_key: Optional[bytes] = None,
        public_key: Optional[bytes] = None,
        agent_id: Optional[str] = None,
        trust_score: float = 0.1,
        reputation: float = 0.0,
        interactions: int = 0,
        successful_interactions: int = 0,
        failed_interactions: int = 0,
        created_timestamp: Optional[str] = None,
        last_active: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
        attestations: Optional[List[Dict]] = None,
        vouchers: Optional[List[str]] = None
    ):
        """
        Initialize LCT identity.

        Args:
            private_key: Ed25519 private key bytes (generated if None)
            public_key: Ed25519 public key bytes (derived if None)
            agent_id: Unique agent identifier (derived if None)
            trust_score: Current trust level (0.0-1.0)
            reputation: Long-term reputation (-1.0 to 1.0)
            interactions: Total interaction count
            successful_interactions: Count of successful interactions
            failed_interactions: Count of failed interactions
            created_timestamp: Identity genesis timestamp
            last_active: Last interaction timestamp
            device_fingerprint: Hardware/environment fingerprint
            attestations: Trust claims from other agents
            vouchers: Agent IDs vouching for this identity
        """
        # Generate keys if not provided
        if private_key is None:
            if CRYPTO_AVAILABLE:
                sk = Ed25519PrivateKey.generate()
                self.private_key_obj = sk
                self.public_key_obj = sk.public_key()

                self.private_key = sk.private_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PrivateFormat.Raw,
                    encryption_algorithm=serialization.NoEncryption()
                )
                self.public_key = self.public_key_obj.public_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PublicFormat.Raw
                )
            else:
                # Mock keys for testing without cryptography library
                self.private_key = b"mock_private_key_32_bytes_long!!"
                self.public_key = b"mock_public_key_32_bytes_lng!!"
                self.private_key_obj = None
                self.public_key_obj = None
        else:
            self.private_key = private_key
            self.public_key = public_key

            if CRYPTO_AVAILABLE:
                self.private_key_obj = Ed25519PrivateKey.from_private_bytes(private_key)
                self.public_key_obj = Ed25519PublicKey.from_public_bytes(public_key)
            else:
                self.private_key_obj = None
                self.public_key_obj = None

        # Derive agent_id from public key if not provided
        if agent_id is None:
            # agent_id = first 16 chars of hex(sha256(public_key))
            pk_hash = hashlib.sha256(self.public_key).digest()
            self.agent_id = pk_hash.hex()[:16]
        else:
            self.agent_id = agent_id

        # Trust metrics
        self.trust_score = trust_score
        self.reputation = reputation
        self.interactions = interactions
        self.successful_interactions = successful_interactions
        self.failed_interactions = failed_interactions

        # Timestamps
        self.created_timestamp = created_timestamp or datetime.now().isoformat()
        self.last_active = last_active or datetime.now().isoformat()

        # Metadata
        self.device_fingerprint = device_fingerprint or self._generate_device_fingerprint()

        # Trust network
        self.attestations = attestations or []
        self.vouchers = vouchers or []

    @staticmethod
    def _generate_device_fingerprint() -> str:
        """
        Generate device fingerprint.

        In production, would include:
        - Hardware UUID
        - CPU model
        - GPU model
        - System info

        For now, returns simple identifier.
        """
        import platform
        import socket

        fingerprint = {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "processor": platform.processor()
        }

        fp_str = json.dumps(fingerprint, sort_keys=True)
        fp_hash = hashlib.sha256(fp_str.encode()).hexdigest()[:16]

        return fp_hash

    def get_age_days(self) -> int:
        """Get identity age in days."""
        created = datetime.fromisoformat(self.created_timestamp)
        age = datetime.now() - created
        return age.days

    def calculate_trust_score(self) -> float:
        """
        Calculate current trust score.

        Formula:
          trust = base + interaction_bonus + attestation_bonus + age_bonus

          base = 0.1 (all identities start here)
          interaction_bonus = min(0.3, successful / 1000)
          attestation_bonus = min(0.4, sum(att.weight * att.trust) / 10)
          age_bonus = min(0.2, age_days / 365)

        Returns:
            trust_score ∈ [0.0, 1.0]
        """
        # Base trust
        base_trust = 0.1

        # Interaction bonus (up to 0.3 for 1000+ successful interactions)
        interaction_bonus = min(0.3, self.successful_interactions / 1000.0)

        # Attestation bonus (up to 0.4 based on attestations)
        attestation_score = 0.0
        for att in self.attestations:
            # Weight by attestor's trust
            attestation_score += att.get("weight", 0.5) * att.get("trust_level", 0.5)

        attestation_bonus = min(0.4, attestation_score / 10.0)

        # Age bonus (up to 0.2 for 1+ year old identity)
        age_days = self.get_age_days()
        age_bonus = min(0.2, age_days / 365.0)

        # Total trust
        trust = base_trust + interaction_bonus + attestation_bonus + age_bonus

        return min(1.0, max(0.0, trust))  # Clamp to [0, 1]

    def calculate_reputation(self) -> float:
        """
        Calculate reputation score.

        Formula:
          reputation = (successful - failed) / total

        Returns:
            reputation ∈ [-1.0, 1.0]
        """
        total = self.interactions
        if total == 0:
            return 0.0

        successful = self.successful_interactions
        failed = self.failed_interactions

        rep = (successful - failed) / total

        return min(1.0, max(-1.0, rep))  # Clamp to [-1, 1]

    def update_metrics(self):
        """Update trust score and reputation."""
        self.trust_score = self.calculate_trust_score()
        self.reputation = self.calculate_reputation()
        self.last_active = datetime.now().isoformat()

    def record_interaction(self, success: bool):
        """
        Record an interaction outcome.

        Args:
            success: Whether interaction was successful
        """
        self.interactions += 1

        if success:
            self.successful_interactions += 1
        else:
            self.failed_interactions += 1

        self.update_metrics()

    def add_attestation(self, attestation: Dict):
        """
        Add trust attestation from another agent.

        Args:
            attestation: Trust attestation dict
        """
        # TODO: Verify attestation signature (Phase 2)
        self.attestations.append(attestation)
        self.update_metrics()

    def add_voucher(self, agent_id: str):
        """
        Add voucher (agent vouching for this identity).

        Args:
            agent_id: ID of vouching agent
        """
        if agent_id not in self.vouchers:
            self.vouchers.append(agent_id)
            self.update_metrics()

    def sign(self, message: bytes) -> bytes:
        """
        Sign message with private key.

        Args:
            message: Message to sign

        Returns:
            Signature bytes
        """
        if CRYPTO_AVAILABLE and self.private_key_obj:
            return self.private_key_obj.sign(message)
        else:
            # Mock signature
            return hashlib.sha256(message + self.private_key).digest()

    def verify(self, message: bytes, signature: bytes) -> bool:
        """
        Verify signature on message.

        Args:
            message: Original message
            signature: Signature to verify

        Returns:
            True if valid, False otherwise
        """
        if CRYPTO_AVAILABLE and self.public_key_obj:
            try:
                self.public_key_obj.verify(signature, message)
                return True
            except InvalidSignature:
                return False
        else:
            # Mock verification
            expected = hashlib.sha256(message + self.private_key).digest()
            return signature == expected

    def sign_pattern(self, pattern: Dict) -> Dict:
        """
        Sign pattern with this identity.

        Binds pattern to identity cryptographically.

        Args:
            pattern: Pattern to sign

        Returns:
            Pattern with signature added
        """
        # Create canonical payload
        payload = {
            "pattern_id": pattern.get("pattern_id", "unknown"),
            "context": pattern.get("context", {}),
            "context_tag": pattern.get("context_tag", {}),
            "provenance": pattern.get("provenance", {}),
            "timestamp": pattern.get("timestamp", "")
        }

        # Canonical JSON (deterministic)
        canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))

        # Sign
        signature = self.sign(canonical.encode())

        # Add signature to pattern
        signed = pattern.copy()
        signed["signature"] = {
            "agent_id": self.agent_id,
            "public_key": base64.b64encode(self.public_key).decode(),
            "signature": base64.b64encode(signature).decode(),
            "signed_at": datetime.now().isoformat()
        }

        return signed

    @staticmethod
    def verify_pattern_signature(pattern: Dict) -> Tuple[bool, Optional[str]]:
        """
        Verify pattern signature.

        Args:
            pattern: Pattern with signature

        Returns:
            (valid, agent_id) tuple
        """
        if "signature" not in pattern:
            return False, None

        sig_data = pattern["signature"]

        try:
            # Reconstruct payload
            payload = {
                "pattern_id": pattern.get("pattern_id", "unknown"),
                "context": pattern.get("context", {}),
                "context_tag": pattern.get("context_tag", {}),
                "provenance": pattern.get("provenance", {}),
                "timestamp": pattern.get("timestamp", "")
            }
            canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))

            # Decode signature data
            public_key_bytes = base64.b64decode(sig_data["public_key"])
            signature_bytes = base64.b64decode(sig_data["signature"])

            # Verify
            if CRYPTO_AVAILABLE:
                public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
                try:
                    public_key.verify(signature_bytes, canonical.encode())
                    return True, sig_data["agent_id"]
                except InvalidSignature:
                    return False, None
            else:
                # Mock verification
                return True, sig_data["agent_id"]

        except Exception as e:
            print(f"Signature verification error: {e}")
            return False, None

    def to_dict(self) -> Dict:
        """Convert to dictionary (excluding private key)."""
        return {
            "agent_id": self.agent_id,
            "public_key": base64.b64encode(self.public_key).decode(),
            "trust_score": self.trust_score,
            "reputation": self.reputation,
            "interactions": self.interactions,
            "successful_interactions": self.successful_interactions,
            "failed_interactions": self.failed_interactions,
            "created_timestamp": self.created_timestamp,
            "last_active": self.last_active,
            "device_fingerprint": self.device_fingerprint,
            "attestations": self.attestations,
            "vouchers": self.vouchers,
            "age_days": self.get_age_days()
        }

    def save(self, path: Path):
        """
        Save identity to file (including private key).

        WARNING: Private key stored unencrypted. In production, encrypt.
        """
        data = {
            "private_key": base64.b64encode(self.private_key).decode(),
            "public_key": base64.b64encode(self.public_key).decode(),
            "agent_id": self.agent_id,
            "trust_score": self.trust_score,
            "reputation": self.reputation,
            "interactions": self.interactions,
            "successful_interactions": self.successful_interactions,
            "failed_interactions": self.failed_interactions,
            "created_timestamp": self.created_timestamp,
            "last_active": self.last_active,
            "device_fingerprint": self.device_fingerprint,
            "attestations": self.attestations,
            "vouchers": self.vouchers
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def load(path: Path) -> 'LCTIdentity':
        """Load identity from file."""
        with open(path, 'r') as f:
            data = json.load(f)

        return LCTIdentity(
            private_key=base64.b64decode(data["private_key"]),
            public_key=base64.b64decode(data["public_key"]),
            agent_id=data["agent_id"],
            trust_score=data.get("trust_score", 0.1),
            reputation=data.get("reputation", 0.0),
            interactions=data.get("interactions", 0),
            successful_interactions=data.get("successful_interactions", 0),
            failed_interactions=data.get("failed_interactions", 0),
            created_timestamp=data.get("created_timestamp"),
            last_active=data.get("last_active"),
            device_fingerprint=data.get("device_fingerprint"),
            attestations=data.get("attestations", []),
            vouchers=data.get("vouchers", [])
        )

    def __repr__(self) -> str:
        return (f"LCTIdentity(agent_id={self.agent_id}, "
                f"trust={self.trust_score:.3f}, "
                f"reputation={self.reputation:.3f}, "
                f"interactions={self.interactions}, "
                f"age_days={self.get_age_days()})")


def demo():
    """Demonstrate LCT identity system."""
    print("=" * 80)
    print("LCT Identity System Demo")
    print("=" * 80)
    print()

    # Create new identity
    print("Creating new identity...")
    identity = LCTIdentity()
    print(f"  Agent ID: {identity.agent_id}")
    print(f"  Trust Score: {identity.trust_score:.3f}")
    print(f"  Reputation: {identity.reputation:.3f}")
    print(f"  Age: {identity.get_age_days()} days")
    print()

    # Simulate interactions
    print("Simulating 100 successful interactions...")
    for i in range(100):
        identity.record_interaction(success=True)

    print(f"  Trust Score: {identity.trust_score:.3f} (+{identity.trust_score - 0.1:.3f})")
    print(f"  Reputation: {identity.reputation:.3f}")
    print()

    # Simulate more interactions with some failures
    print("Simulating 900 more interactions (10% failure rate)...")
    import random
    for i in range(900):
        success = random.random() > 0.1
        identity.record_interaction(success=success)

    print(f"  Trust Score: {identity.trust_score:.3f}")
    print(f"  Reputation: {identity.reputation:.3f}")
    print(f"  Total Interactions: {identity.interactions}")
    print()

    # Sign a pattern
    print("Signing a pattern...")
    pattern = {
        "pattern_id": "test_pattern_001",
        "context": {"emotional": {"frustration": 0.5}},
        "context_tag": {"application": "test"},
        "provenance": {"quality_weight": 0.8},
        "timestamp": datetime.now().isoformat()
    }

    signed_pattern = identity.sign_pattern(pattern)
    print(f"  Pattern signed by: {signed_pattern['signature']['agent_id']}")
    print()

    # Verify signature
    print("Verifying signature...")
    valid, agent_id = LCTIdentity.verify_pattern_signature(signed_pattern)
    print(f"  Valid: {valid}")
    print(f"  Agent ID: {agent_id}")
    print()

    # Save and load
    print("Saving identity...")
    save_path = Path("/tmp/test_identity.json")
    identity.save(save_path)
    print(f"  Saved to: {save_path}")
    print()

    print("Loading identity...")
    loaded = LCTIdentity.load(save_path)
    print(f"  Loaded: {loaded}")
    print()

    print("=" * 80)
    print("Demo complete!")
    print("=" * 80)


if __name__ == "__main__":
    demo()
