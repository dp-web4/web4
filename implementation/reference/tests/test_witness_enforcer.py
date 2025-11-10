"""
Unit tests for Witness Enforcer

Tests the critical security fix: Witness enforcement for delegation validation.

Author: Claude (Anthropic AI), autonomous security hardening
Date: November 10, 2025
"""

import pytest
import hashlib
from cryptography.hazmat.primitives.asymmetric import ed25519

# Import from parent directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from witness_enforcer import (
    WitnessEnforcer,
    WitnessSignature,
    WitnessRequirement,
    WitnessRole
)


class TestWitnessSignature:
    """Test WitnessSignature class."""

    def test_create_signature(self):
        """Test creating witness signature."""
        # Create key pair
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Create delegation hash
        delegation_data = b"test:delegation"
        delegation_hash = hashlib.sha256(delegation_data).digest()

        # Sign
        signature = private_key.sign(delegation_hash)

        # Create witness signature
        from cryptography.hazmat.primitives import serialization
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        witness_sig = WitnessSignature(
            witness_id="witness-test",
            witness_public_key=public_key_bytes,
            signature=signature,
            role=WitnessRole.PEER,
            trust_score=0.8
        )

        assert witness_sig.witness_id == "witness-test"
        assert witness_sig.trust_score == 0.8

    def test_verify_valid_signature(self):
        """Test verifying valid signature."""
        # Create key pair
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Create delegation hash
        delegation_data = b"test:delegation"
        delegation_hash = hashlib.sha256(delegation_data).digest()

        # Sign
        signature = private_key.sign(delegation_hash)

        # Create witness signature
        from cryptography.hazmat.primitives import serialization
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        witness_sig = WitnessSignature(
            witness_id="witness-test",
            witness_public_key=public_key_bytes,
            signature=signature
        )

        # Should verify successfully
        assert witness_sig.verify(delegation_hash) is True

    def test_verify_invalid_signature(self):
        """Test verifying invalid signature."""
        # Create key pair
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Create delegation hash
        delegation_data = b"test:delegation"
        delegation_hash = hashlib.sha256(delegation_data).digest()

        # Sign DIFFERENT data
        wrong_data = b"wrong:delegation"
        wrong_hash = hashlib.sha256(wrong_data).digest()
        signature = private_key.sign(wrong_hash)

        # Create witness signature
        from cryptography.hazmat.primitives import serialization
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        witness_sig = WitnessSignature(
            witness_id="witness-test",
            witness_public_key=public_key_bytes,
            signature=signature
        )

        # Should FAIL verification (signed wrong data)
        assert witness_sig.verify(delegation_hash) is False


class TestWitnessRequirement:
    """Test WitnessRequirement class."""

    def test_create_requirement(self):
        """Test creating witness requirement."""
        req = WitnessRequirement(
            min_witnesses=2,
            min_trust_score=0.7,
            min_aggregate_trust=1.5
        )

        assert req.min_witnesses == 2
        assert req.min_trust_score == 0.7
        assert req.min_aggregate_trust == 1.5

    def test_insufficient_witness_count(self):
        """Test insufficient witness count."""
        req = WitnessRequirement(min_witnesses=3)

        witnesses = [
            WitnessSignature("w1", b"key1", b"sig1", trust_score=0.8),
            WitnessSignature("w2", b"key2", b"sig2", trust_score=0.8)
        ]

        satisfied, msg = req.is_satisfied(witnesses)

        assert satisfied is False
        assert "insufficient" in msg.lower()

    def test_low_individual_trust(self):
        """Test witness with too low trust score."""
        req = WitnessRequirement(
            min_witnesses=2,
            min_trust_score=0.7
        )

        witnesses = [
            WitnessSignature("w1", b"key1", b"sig1", trust_score=0.8),
            WitnessSignature("w2", b"key2", b"sig2", trust_score=0.5)  # Too low
        ]

        satisfied, msg = req.is_satisfied(witnesses)

        assert satisfied is False
        assert "trust too low" in msg.lower()

    def test_low_aggregate_trust(self):
        """Test insufficient aggregate trust."""
        req = WitnessRequirement(
            min_witnesses=2,
            min_aggregate_trust=2.0
        )

        witnesses = [
            WitnessSignature("w1", b"key1", b"sig1", trust_score=0.6),
            WitnessSignature("w2", b"key2", b"sig2", trust_score=0.6)
        ]

        satisfied, msg = req.is_satisfied(witnesses)

        assert satisfied is False
        assert "aggregate trust" in msg.lower()

    def test_satisfied_requirements(self):
        """Test satisfied requirements."""
        req = WitnessRequirement(
            min_witnesses=2,
            min_trust_score=0.6,
            min_aggregate_trust=1.4
        )

        witnesses = [
            WitnessSignature("w1", b"key1", b"sig1", trust_score=0.8),
            WitnessSignature("w2", b"key2", b"sig2", trust_score=0.7)
        ]

        satisfied, msg = req.is_satisfied(witnesses)

        assert satisfied is True


class TestWitnessEnforcer:
    """Test WitnessEnforcer class."""

    def test_create_enforcer(self):
        """Test creating enforcer."""
        enforcer = WitnessEnforcer(
            min_witnesses=2,
            min_trust_score=0.7,
            min_aggregate_trust=1.5
        )

        assert enforcer.default_requirements.min_witnesses == 2
        assert enforcer.default_requirements.min_trust_score == 0.7
        assert enforcer.default_requirements.min_aggregate_trust == 1.5

    def test_register_witness(self):
        """Test registering witnesses."""
        enforcer = WitnessEnforcer()

        enforcer.register_witness("witness-alice", initial_trust=0.8)
        enforcer.register_witness("witness-bob", initial_trust=0.6)

        assert enforcer.get_witness_trust("witness-alice") == 0.8
        assert enforcer.get_witness_trust("witness-bob") == 0.6

    def test_update_witness_trust(self):
        """Test updating witness trust."""
        enforcer = WitnessEnforcer()

        enforcer.register_witness("witness-alice", initial_trust=0.5)
        enforcer.update_witness_trust("witness-alice", 0.9)

        assert enforcer.get_witness_trust("witness-alice") == 0.9

    def test_verify_valid_witnesses(self):
        """
        Critical security test: Verify valid witnesses.

        Delegation with sufficient valid witnesses should be authorized.
        """
        enforcer = WitnessEnforcer(min_witnesses=2)

        # Register witnesses
        enforcer.register_witness("witness-alice", initial_trust=0.8)
        enforcer.register_witness("witness-bob", initial_trust=0.7)

        # Create delegation hash
        delegation_data = b"delegation:alice->bob"
        delegation_hash = hashlib.sha256(delegation_data).digest()

        # Create witness keys and signatures
        alice_key = ed25519.Ed25519PrivateKey.generate()
        bob_key = ed25519.Ed25519PrivateKey.generate()

        witnesses = [
            enforcer.create_witness_signature(
                delegation_hash, "witness-alice", alice_key
            ),
            enforcer.create_witness_signature(
                delegation_hash, "witness-bob", bob_key
            )
        ]

        # Should AUTHORIZE
        valid, msg = enforcer.verify_witnesses(delegation_hash, witnesses)
        assert valid is True, "Valid witnesses should authorize delegation"

    def test_verify_insufficient_witnesses(self):
        """
        Critical security test: Reject insufficient witnesses.

        Delegation without enough witnesses should be denied.
        """
        enforcer = WitnessEnforcer(min_witnesses=2)

        # Register witness
        enforcer.register_witness("witness-alice", initial_trust=0.8)

        # Create delegation hash
        delegation_data = b"delegation:alice->bob"
        delegation_hash = hashlib.sha256(delegation_data).digest()

        # Create only ONE witness (need 2)
        alice_key = ed25519.Ed25519PrivateKey.generate()

        witnesses = [
            enforcer.create_witness_signature(
                delegation_hash, "witness-alice", alice_key
            )
        ]

        # Should DENY (insufficient witnesses)
        valid, msg = enforcer.verify_witnesses(delegation_hash, witnesses)
        assert valid is False, "Insufficient witnesses must be denied"
        assert "insufficient" in msg.lower()

    def test_verify_invalid_signature(self):
        """
        Critical security test: Reject invalid signatures.

        Delegation with forged signatures should be denied.
        """
        enforcer = WitnessEnforcer(min_witnesses=1)

        # Register witness
        enforcer.register_witness("witness-alice", initial_trust=0.8)

        # Create delegation hash
        delegation_data = b"delegation:alice->bob"
        delegation_hash = hashlib.sha256(delegation_data).digest()

        # Create witness signature for WRONG data
        alice_key = ed25519.Ed25519PrivateKey.generate()
        wrong_data = b"delegation:wrong"
        wrong_hash = hashlib.sha256(wrong_data).digest()
        signature = alice_key.sign(wrong_hash)

        # Create witness with wrong signature
        from cryptography.hazmat.primitives import serialization
        public_key = alice_key.public_key()
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        witnesses = [
            WitnessSignature(
                witness_id="witness-alice",
                witness_public_key=public_key_bytes,
                signature=signature,
                trust_score=0.8
            )
        ]

        # Should DENY (invalid signature)
        valid, msg = enforcer.verify_witnesses(delegation_hash, witnesses)
        assert valid is False, "Invalid signatures must be denied"

    def test_witness_reputation_tracking(self):
        """Test witness reputation is tracked."""
        enforcer = WitnessEnforcer(min_witnesses=1, min_aggregate_trust=0.5)

        # Register witness
        enforcer.register_witness("witness-alice", initial_trust=0.7)

        # Create delegation hash
        delegation_data = b"delegation:test"
        delegation_hash = hashlib.sha256(delegation_data).digest()

        # Create valid witness
        alice_key = ed25519.Ed25519PrivateKey.generate()
        witnesses = [
            enforcer.create_witness_signature(
                delegation_hash, "witness-alice", alice_key
            )
        ]

        # Verify (should succeed and update reputation)
        valid, _ = enforcer.verify_witnesses(delegation_hash, witnesses)
        assert valid is True

        # Check reputation updated
        rate, successful, total = enforcer.get_witness_reputation("witness-alice")
        assert total > 0
        assert successful > 0

    def test_trusted_witnesses_list(self):
        """Test getting list of trusted witnesses."""
        enforcer = WitnessEnforcer()

        # Register witnesses with different trust levels
        enforcer.register_witness("witness-high", initial_trust=0.9)
        enforcer.register_witness("witness-medium", initial_trust=0.6)
        enforcer.register_witness("witness-low", initial_trust=0.3)

        # Simulate verification history for high and medium
        # Note: successful verifications increase trust scores
        for witness_id in ["witness-high", "witness-medium"]:
            for _ in range(15):
                enforcer._update_reputation(witness_id, True)

        # Get trusted witnesses (min_trust=0.7)
        trusted = enforcer.get_trusted_witnesses(
            min_trust=0.7,
            min_verifications=10
        )

        # Both high and medium should be trusted after successful verifications
        # (witness-medium's trust increased from 0.6 to >0.7 due to successful history)
        assert "witness-high" in trusted
        assert "witness-medium" in trusted  # Trust increased due to successful verifications
        assert "witness-low" not in trusted  # No verification history

    def test_witness_role_requirements(self):
        """Test role-based witness requirements."""
        enforcer = WitnessEnforcer()

        # Require at least one AUTHORITY witness
        requirements = WitnessRequirement(
            min_witnesses=2,
            required_roles={WitnessRole.AUTHORITY}
        )

        # Create witnesses (no authority)
        witnesses = [
            WitnessSignature(
                "w1", b"key1", b"sig1",
                role=WitnessRole.PEER, trust_score=0.8
            ),
            WitnessSignature(
                "w2", b"key2", b"sig2",
                role=WitnessRole.PEER, trust_score=0.8
            )
        ]

        # Should fail (missing authority role)
        satisfied, msg = requirements.is_satisfied(witnesses)
        assert satisfied is False
        assert "role" in msg.lower()

        # Add authority witness
        witnesses.append(
            WitnessSignature(
                "w3", b"key3", b"sig3",
                role=WitnessRole.AUTHORITY, trust_score=0.8
            )
        )

        # Should succeed now
        satisfied, _ = requirements.is_satisfied(witnesses)
        assert satisfied is True

    def test_specific_witness_requirements(self):
        """Test requiring specific witnesses."""
        enforcer = WitnessEnforcer()

        # Require specific witness with lower aggregate trust requirement
        requirements = WitnessRequirement(
            min_witnesses=1,
            min_aggregate_trust=0.5,
            required_witnesses={"witness-alice"}
        )

        # Create witness (wrong one)
        witnesses = [
            WitnessSignature(
                "witness-bob", b"key", b"sig", trust_score=0.8
            )
        ]

        # Should fail (missing required witness)
        satisfied, msg = requirements.is_satisfied(witnesses)
        assert satisfied is False
        assert "required witness" in msg.lower()

        # Add required witness
        witnesses.append(
            WitnessSignature(
                "witness-alice", b"key2", b"sig2", trust_score=0.8
            )
        )

        # Should succeed now
        satisfied, _ = requirements.is_satisfied(witnesses)
        assert satisfied is True

    def test_serialization(self):
        """Test converting to/from dictionary."""
        enforcer = WitnessEnforcer(min_witnesses=2, min_trust_score=0.7)

        enforcer.register_witness("witness-alice", initial_trust=0.8)
        enforcer.register_witness("witness-bob", initial_trust=0.6)

        # Serialize
        data = enforcer.to_dict()

        assert data["default_requirements"]["min_witnesses"] == 2
        assert data["default_requirements"]["min_trust_score"] == 0.7
        assert "witness-alice" in data["witness_trust"]

        # Deserialize
        enforcer2 = WitnessEnforcer.from_dict(data)

        assert enforcer2.default_requirements.min_witnesses == 2
        assert enforcer2.get_witness_trust("witness-alice") == 0.8

    def test_no_witnesses_provided(self):
        """Test delegation with no witnesses."""
        enforcer = WitnessEnforcer(min_witnesses=1)

        delegation_hash = hashlib.sha256(b"test").digest()

        # No witnesses
        valid, msg = enforcer.verify_witnesses(delegation_hash, [])

        assert valid is False
        assert "no witnesses" in msg.lower()

    def test_complex_scenario(self):
        """Test complex real-world scenario."""
        enforcer = WitnessEnforcer(
            min_witnesses=3,
            min_trust_score=0.6,
            min_aggregate_trust=2.5
        )

        # Register witnesses
        enforcer.register_witness("authority-1", initial_trust=0.9)
        enforcer.register_witness("peer-1", initial_trust=0.7)
        enforcer.register_witness("peer-2", initial_trust=0.7)
        enforcer.register_witness("observer-1", initial_trust=0.5)

        # Create delegation
        delegation_hash = hashlib.sha256(b"important:delegation").digest()

        # Create witness signatures
        authority_key = ed25519.Ed25519PrivateKey.generate()
        peer1_key = ed25519.Ed25519PrivateKey.generate()
        peer2_key = ed25519.Ed25519PrivateKey.generate()

        witnesses = [
            enforcer.create_witness_signature(
                delegation_hash, "authority-1", authority_key,
                role=WitnessRole.AUTHORITY
            ),
            enforcer.create_witness_signature(
                delegation_hash, "peer-1", peer1_key,
                role=WitnessRole.PEER
            ),
            enforcer.create_witness_signature(
                delegation_hash, "peer-2", peer2_key,
                role=WitnessRole.PEER
            )
        ]

        # Should AUTHORIZE (3 witnesses, aggregate trust = 0.9+0.7+0.7 = 2.3)
        # Wait, that's < 2.5, so it should fail...
        valid, msg = enforcer.verify_witnesses(delegation_hash, witnesses)

        # Actually should fail due to aggregate trust
        # Let's fix by increasing one trust score
        enforcer.update_witness_trust("authority-1", 1.0)
        witnesses[0].trust_score = 1.0

        # Now aggregate = 1.0+0.7+0.7 = 2.4, still < 2.5
        # Need to also update one peer
        enforcer.update_witness_trust("peer-1", 0.8)
        witnesses[1].trust_score = 0.8

        # Now aggregate = 1.0+0.8+0.7 = 2.5 (exactly meets requirement)
        valid, msg = enforcer.verify_witnesses(delegation_hash, witnesses)
        assert valid is True


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
