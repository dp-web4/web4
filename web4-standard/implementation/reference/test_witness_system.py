"""
Witness System Tests
====================

Comprehensive test suite for Web4 witness attestation system.

Tests:
- Witness registration and capabilities
- Attestation creation and signing
- Signature verification
- Freshness window validation
- Nonce replay protection
- Type-specific claim validation
- Multi-witness validation
- Consensus checking
- Reputation tracking

Author: Legion Autonomous Session (2025-12-05)
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta, timezone
import base64
import secrets

from witness_system import (
    WitnessType, WitnessAttestation, WitnessRequirements,
    WitnessRegistry, WitnessSystem, WitnessError,
    create_time_attestation, create_audit_attestation, create_action_attestation
)

try:
    from crypto_verification import generate_test_keypair, sign_message
    CRYPTO_AVAILABLE = True
except:
    CRYPTO_AVAILABLE = False


class TestWitnessRegistry(unittest.TestCase):
    """Test witness registry functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.registry = WitnessRegistry()

    def test_register_witness(self):
        """Test witness registration"""
        self.registry.register_witness(
            witness_did="did:web4:witness:001",
            public_key="abcd1234",
            capabilities={WitnessType.TIME, WitnessType.AUDIT}
        )

        self.assertTrue(self.registry.is_witness_registered("did:web4:witness:001"))
        self.assertEqual(self.registry.get_witness_public_key("did:web4:witness:001"), "abcd1234")
        self.assertEqual(
            self.registry.get_witness_capabilities("did:web4:witness:001"),
            {WitnessType.TIME, WitnessType.AUDIT}
        )

    def test_reputation_tracking(self):
        """Test reputation score tracking"""
        witness_did = "did:web4:witness:001"
        self.registry.register_witness(witness_did, "key", {WitnessType.TIME})

        # Initial score
        self.assertEqual(self.registry.get_reputation_score(witness_did), 0.5)

        # Record successes
        for _ in range(8):
            self.registry.record_success(witness_did)

        # Record failures
        for _ in range(2):
            self.registry.record_failure(witness_did)

        # Score should be 8/10 = 0.8
        self.assertAlmostEqual(self.registry.get_reputation_score(witness_did), 0.8, places=2)

    def test_nonce_replay_protection(self):
        """Test nonce uniqueness checking"""
        nonce = "test_nonce_12345"

        # First use should succeed
        self.assertTrue(self.registry.check_nonce(nonce))

        # Second use should fail (replay)
        self.assertFalse(self.registry.check_nonce(nonce))

    def test_unknown_witness_reputation(self):
        """Test reputation for unknown witness"""
        score = self.registry.get_reputation_score("did:web4:unknown")
        self.assertEqual(score, 0.5)  # Default


@unittest.skipUnless(CRYPTO_AVAILABLE, "cryptography library required")
class TestWitnessSystem(unittest.TestCase):
    """Test witness system with real cryptography"""

    def setUp(self):
        """Set up test fixtures"""
        self.system = WitnessSystem()

        # Generate test keypair
        self.private_key, self.public_key = generate_test_keypair()
        from cryptography.hazmat.primitives import serialization
        pub_key_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        self.pub_key_hex = pub_key_bytes.hex()

        # Register witness
        self.witness_did = "did:web4:witness:test001"
        self.system.registry.register_witness(
            witness_did=self.witness_did,
            public_key=self.pub_key_hex,
            capabilities={WitnessType.TIME, WitnessType.AUDIT, WitnessType.ACTION}
        )

    def test_create_time_attestation(self):
        """Test time attestation creation"""
        nonce = base64.b64encode(secrets.token_bytes(16)).decode('ascii')

        attestation = create_time_attestation(
            witness_system=self.system,
            witness_did=self.witness_did,
            private_key=self.private_key,
            nonce=nonce,
            subject="did:web4:entity:001"
        )

        self.assertEqual(attestation.witness_did, self.witness_did)
        self.assertEqual(attestation.witness_type, WitnessType.TIME)
        self.assertEqual(attestation.subject, "did:web4:entity:001")
        self.assertIn('ts', attestation.claims)
        self.assertIn('nonce', attestation.claims)

    def test_verify_valid_attestation(self):
        """Test verification of valid attestation"""
        nonce = base64.b64encode(secrets.token_bytes(16)).decode('ascii')

        attestation = create_time_attestation(
            witness_system=self.system,
            witness_did=self.witness_did,
            private_key=self.private_key,
            nonce=nonce
        )

        valid, error = self.system.verify_attestation(attestation)
        self.assertTrue(valid)
        self.assertIsNone(error)

    def test_verify_unknown_witness(self):
        """Test verification fails for unknown witness"""
        attestation = WitnessAttestation(
            witness_did="did:web4:unknown",
            witness_type=WitnessType.TIME,
            claims={"ts": datetime.now(timezone.utc).isoformat(), "nonce": "abc"},
            signature="fake_sig",
            timestamp=datetime.now(timezone.utc),
            nonce="abc"
        )

        valid, error = self.system.verify_attestation(attestation)
        self.assertFalse(valid)
        self.assertIn("Unknown witness", error)

    def test_verify_unauthorized_type(self):
        """Test verification fails for unauthorized witness type"""
        # Register witness without ORACLE capability
        witness_did = "did:web4:witness:limited"
        self.system.registry.register_witness(
            witness_did=witness_did,
            public_key=self.pub_key_hex,
            capabilities={WitnessType.TIME}  # Only TIME, not ORACLE
        )

        # Try to create ORACLE attestation
        attestation = self.system.create_attestation(
            witness_did=witness_did,
            witness_type=WitnessType.ORACLE,
            claims={"source": "example.com", "data": "test", "ts": datetime.now(timezone.utc).isoformat()},
            private_key=self.private_key
        )

        valid, error = self.system.verify_attestation(attestation)
        self.assertFalse(valid)
        self.assertIn("not authorized", error)

    def test_freshness_window(self):
        """Test freshness window validation"""
        # Create attestation with old timestamp
        attestation = self.system.create_attestation(
            witness_did=self.witness_did,
            witness_type=WitnessType.TIME,
            claims={"ts": datetime.now(timezone.utc).isoformat(), "nonce": "test"},
            private_key=self.private_key
        )

        # Manually set old timestamp
        attestation.timestamp = datetime.now(timezone.utc) - timedelta(seconds=400)

        # Should fail freshness check (default ±300s)
        valid, error = self.system.verify_attestation(attestation)
        self.assertFalse(valid)
        self.assertIn("too old", error)

    def test_nonce_replay_prevention(self):
        """Test nonce replay attack prevention"""
        nonce1 = base64.b64encode(secrets.token_bytes(16)).decode('ascii')

        # First attestation should succeed
        attestation1 = create_time_attestation(
            witness_system=self.system,
            witness_did=self.witness_did,
            private_key=self.private_key,
            nonce=nonce1
        )
        valid1, _ = self.system.verify_attestation(attestation1)
        self.assertTrue(valid1)

        # Second attestation with same ATTESTATION nonce should fail
        # Manually create attestation with same nonce
        attestation2 = self.system.create_attestation(
            witness_did=self.witness_did,
            witness_type=WitnessType.TIME,
            claims={"ts": datetime.now(timezone.utc).isoformat(), "nonce": "test"},
            private_key=self.private_key
        )
        # Use same nonce as first attestation
        attestation2.nonce = attestation1.nonce

        valid2, error2 = self.system.verify_attestation(attestation2)
        self.assertFalse(valid2)
        self.assertIn("already used", error2)

    def test_invalid_signature(self):
        """Test verification fails with invalid signature"""
        nonce = base64.b64encode(secrets.token_bytes(16)).decode('ascii')

        attestation = create_time_attestation(
            witness_system=self.system,
            witness_did=self.witness_did,
            private_key=self.private_key,
            nonce=nonce
        )

        # Corrupt signature
        attestation.signature = "deadbeef" * 16

        valid, error = self.system.verify_attestation(attestation)
        self.assertFalse(valid)
        self.assertIn("signature", error.lower())

    def test_type_specific_claims_time(self):
        """Test TIME witness claim validation"""
        # Missing required 'ts' claim
        attestation = self.system.create_attestation(
            witness_did=self.witness_did,
            witness_type=WitnessType.TIME,
            claims={"nonce": "test"},  # Missing 'ts'
            private_key=self.private_key
        )

        valid, error = self.system.verify_attestation(attestation)
        self.assertFalse(valid)
        self.assertIn("missing 'ts'", error)

    def test_type_specific_claims_audit(self):
        """Test AUDIT witness claim validation"""
        # Missing required claims
        attestation = self.system.create_attestation(
            witness_did=self.witness_did,
            witness_type=WitnessType.AUDIT,
            claims={"policy_met": True},  # Missing 'evidence' and 'policy_id'
            private_key=self.private_key
        )

        valid, error = self.system.verify_attestation(attestation)
        self.assertFalse(valid)
        self.assertIn("missing", error)

    def test_multi_witness_validation(self):
        """Test validation with multiple witnesses"""
        # Create two witnesses
        witness_did_2 = "did:web4:witness:test002"
        private_key_2, public_key_2 = generate_test_keypair()
        from cryptography.hazmat.primitives import serialization
        pub_key_bytes_2 = public_key_2.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        pub_key_hex_2 = pub_key_bytes_2.hex()

        self.system.registry.register_witness(
            witness_did=witness_did_2,
            public_key=pub_key_hex_2,
            capabilities={WitnessType.TIME, WitnessType.AUDIT}
        )

        # Create attestations from both witnesses
        nonce1 = base64.b64encode(secrets.token_bytes(16)).decode('ascii')
        nonce2 = base64.b64encode(secrets.token_bytes(16)).decode('ascii')

        attestation1 = create_time_attestation(
            witness_system=self.system,
            witness_did=self.witness_did,
            private_key=self.private_key,
            nonce=nonce1
        )

        attestation2 = create_audit_attestation(
            witness_system=self.system,
            witness_did=witness_did_2,
            private_key=private_key_2,
            policy_id="policy://baseline-v1",
            policy_met=True,
            evidence="base64_evidence_data"
        )

        # Validate both
        requirements = WitnessRequirements(
            required_types={WitnessType.TIME, WitnessType.AUDIT},
            min_witnesses=2
        )

        result = self.system.validate_witnesses([attestation1, attestation2], requirements)
        self.assertTrue(result.valid)
        self.assertEqual(len(result.verified_attestations), 2)
        self.assertEqual(len(result.failed_attestations), 0)

    def test_insufficient_witnesses(self):
        """Test validation fails with insufficient witnesses"""
        nonce = base64.b64encode(secrets.token_bytes(16)).decode('ascii')

        attestation = create_time_attestation(
            witness_system=self.system,
            witness_did=self.witness_did,
            private_key=self.private_key,
            nonce=nonce
        )

        # Require 2 witnesses, but only provide 1
        requirements = WitnessRequirements(
            required_types={WitnessType.TIME},
            min_witnesses=2
        )

        result = self.system.validate_witnesses([attestation], requirements)
        self.assertFalse(result.valid)
        self.assertIn("Insufficient witnesses", result.error)

    def test_missing_required_type(self):
        """Test validation fails with missing required type"""
        nonce = base64.b64encode(secrets.token_bytes(16)).decode('ascii')

        attestation = create_time_attestation(
            witness_system=self.system,
            witness_did=self.witness_did,
            private_key=self.private_key,
            nonce=nonce
        )

        # Require AUDIT type, but only provide TIME
        requirements = WitnessRequirements(
            required_types={WitnessType.TIME, WitnessType.AUDIT},
            min_witnesses=1
        )

        result = self.system.validate_witnesses([attestation], requirements)
        self.assertFalse(result.valid)
        self.assertIn("Missing required witness types", result.error)

    def test_witness_whitelist(self):
        """Test witness whitelist enforcement"""
        nonce = base64.b64encode(secrets.token_bytes(16)).decode('ascii')

        attestation = create_time_attestation(
            witness_system=self.system,
            witness_did=self.witness_did,
            private_key=self.private_key,
            nonce=nonce
        )

        # Whitelist that doesn't include our witness
        requirements = WitnessRequirements(
            required_types={WitnessType.TIME},
            min_witnesses=1,
            allowed_witnesses={"did:web4:witness:different"}
        )

        result = self.system.validate_witnesses([attestation], requirements)
        self.assertFalse(result.valid)
        self.assertIn("not in allowed list", result.failed_attestations[0][1])


class TestWitnessAttestation(unittest.TestCase):
    """Test witness attestation dataclass"""

    def test_to_dict(self):
        """Test attestation serialization"""
        attestation = WitnessAttestation(
            witness_did="did:web4:witness:001",
            witness_type=WitnessType.TIME,
            claims={"ts": "2025-01-01T00:00:00Z", "nonce": "abc"},
            signature="sig123",
            timestamp=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            nonce="abc",
            subject="did:web4:entity:001"
        )

        data = attestation.to_dict()

        self.assertEqual(data["witness"], "did:web4:witness:001")
        self.assertEqual(data["type"], "time")
        self.assertEqual(data["sig"], "sig123")
        self.assertEqual(data["subject"], "did:web4:entity:001")

    def test_to_signing_data(self):
        """Test canonical signing data generation"""
        attestation = WitnessAttestation(
            witness_did="did:web4:witness:001",
            witness_type=WitnessType.TIME,
            claims={"ts": "2025-01-01T00:00:00Z", "nonce": "abc"},
            signature="",
            timestamp=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            nonce="abc"
        )

        signing_data = attestation.to_signing_data()

        # Should be deterministic JSON
        self.assertIsInstance(signing_data, bytes)
        self.assertIn(b'"witness":"did:web4:witness:001"', signing_data)
        self.assertIn(b'"type":"time"', signing_data)


if __name__ == '__main__':
    unittest.main()
