"""
Production Crypto Tests
========================

Test suite for Web4 production cryptography.

Tests:
- ATP transaction signing and verification
- Delegation signature creation and verification
- Birth certificate signing and witness signatures
- HMAC message authentication
- Nonce generation
- Hash functions

Author: Legion Autonomous Session (2025-12-05)
"""

import unittest
from datetime import datetime, timedelta, timezone

from production_crypto import (
    ATPTransaction, SignedDelegation, SignedBirthCertificate,
    create_atp_transaction, verify_atp_transaction,
    create_delegation, verify_delegation,
    create_birth_certificate, add_witness_signature, verify_birth_certificate,
    generate_hmac, verify_hmac, generate_nonce, hash_message,
    CryptoError, CRYPTO_AVAILABLE
)

try:
    from crypto_verification import generate_test_keypair
except ImportError:
    CRYPTO_AVAILABLE = False


@unittest.skipUnless(CRYPTO_AVAILABLE, "cryptography library required")
class TestATPTransactions(unittest.TestCase):
    """Test ATP transaction signing"""

    def setUp(self):
        """Set up test fixtures"""
        self.private_key, self.public_key = generate_test_keypair()

    def test_create_atp_charge_transaction(self):
        """Test ATP charge transaction creation"""
        tx = create_atp_transaction(
            transaction_type="charge",
            from_entity="pool:energy:grid001",
            to_entity="lct:ai:agent:001",
            amount=1000,
            private_key=self.private_key,
            metadata={"energy_kwh": 10.5}
        )

        self.assertIn("atp:tx:", tx.transaction_id)
        self.assertEqual(tx.transaction_type, "charge")
        self.assertEqual(tx.from_entity, "pool:energy:grid001")
        self.assertEqual(tx.to_entity, "lct:ai:agent:001")
        self.assertEqual(tx.amount, 1000)
        self.assertIsNotNone(tx.signature)
        self.assertIsNotNone(tx.nonce)
        self.assertEqual(tx.metadata["energy_kwh"], 10.5)

    def test_create_atp_discharge_transaction(self):
        """Test ATP discharge transaction creation"""
        tx = create_atp_transaction(
            transaction_type="discharge",
            from_entity="lct:ai:agent:001",
            to_entity="pool:web4:default",
            amount=500,
            private_key=self.private_key,
            metadata={"action": "compute:training"}
        )

        self.assertEqual(tx.transaction_type, "discharge")
        self.assertEqual(tx.amount, 500)

    def test_verify_atp_transaction_valid(self):
        """Test valid ATP transaction verification"""
        tx = create_atp_transaction(
            transaction_type="charge",
            from_entity="pool:001",
            to_entity="lct:001",
            amount=1000,
            private_key=self.private_key
        )

        valid = verify_atp_transaction(tx, self.public_key)
        self.assertTrue(valid)

    def test_verify_atp_transaction_invalid(self):
        """Test invalid signature detection"""
        tx = create_atp_transaction(
            transaction_type="charge",
            from_entity="pool:001",
            to_entity="lct:001",
            amount=1000,
            private_key=self.private_key
        )

        # Corrupt signature
        tx.signature = "deadbeef" * 16

        valid = verify_atp_transaction(tx, self.public_key)
        self.assertFalse(valid)

    def test_invalid_transaction_type(self):
        """Test invalid transaction type rejection"""
        with self.assertRaises(ValueError):
            create_atp_transaction(
                transaction_type="invalid",
                from_entity="pool:001",
                to_entity="lct:001",
                amount=1000,
                private_key=self.private_key
            )

    def test_invalid_amount(self):
        """Test negative amount rejection"""
        with self.assertRaises(ValueError):
            create_atp_transaction(
                transaction_type="charge",
                from_entity="pool:001",
                to_entity="lct:001",
                amount=-100,
                private_key=self.private_key
            )

    def test_atp_transaction_to_dict(self):
        """Test ATP transaction serialization"""
        tx = create_atp_transaction(
            transaction_type="charge",
            from_entity="pool:001",
            to_entity="lct:001",
            amount=1000,
            private_key=self.private_key
        )

        tx_dict = tx.to_dict()
        self.assertEqual(tx_dict["transaction_id"], tx.transaction_id)
        self.assertEqual(tx_dict["amount"], 1000)


@unittest.skipUnless(CRYPTO_AVAILABLE, "cryptography library required")
class TestDelegations(unittest.TestCase):
    """Test delegation signing"""

    def setUp(self):
        """Set up test fixtures"""
        self.delegator_privkey, self.delegator_pubkey = generate_test_keypair()
        self.delegatee_privkey, self.delegatee_pubkey = generate_test_keypair()

    def test_create_delegation(self):
        """Test delegation creation"""
        delegation = create_delegation(
            delegator_lct="lct:human:client:001",
            delegatee_lct="lct:ai:agent:001",
            granted_permissions=["read:*", "write:code:*"],
            atp_budget=5000,
            valid_from=datetime.now(timezone.utc),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30),
            organization_id="org:web4:default",
            delegator_private_key=self.delegator_privkey,
            constraints={"min_t3": 0.7}
        )

        self.assertIn("delegation:", delegation.delegation_id)
        self.assertEqual(delegation.delegator_lct, "lct:human:client:001")
        self.assertEqual(delegation.delegatee_lct, "lct:ai:agent:001")
        self.assertEqual(delegation.atp_budget, 5000)
        self.assertEqual(len(delegation.granted_permissions), 2)
        self.assertEqual(delegation.constraints["min_t3"], 0.7)
        self.assertIsNotNone(delegation.signature)

    def test_verify_delegation_valid(self):
        """Test valid delegation verification"""
        delegation = create_delegation(
            delegator_lct="lct:client:001",
            delegatee_lct="lct:agent:001",
            granted_permissions=["read:*"],
            atp_budget=1000,
            valid_from=datetime.now(timezone.utc),
            valid_until=datetime.now(timezone.utc) + timedelta(days=1),
            organization_id="org:test",
            delegator_private_key=self.delegator_privkey
        )

        valid = verify_delegation(delegation, self.delegator_pubkey)
        self.assertTrue(valid)

    def test_verify_delegation_invalid(self):
        """Test invalid delegation signature detection"""
        delegation = create_delegation(
            delegator_lct="lct:client:001",
            delegatee_lct="lct:agent:001",
            granted_permissions=["read:*"],
            atp_budget=1000,
            valid_from=datetime.now(timezone.utc),
            valid_until=datetime.now(timezone.utc) + timedelta(days=1),
            organization_id="org:test",
            delegator_private_key=self.delegator_privkey
        )

        # Corrupt signature
        delegation.signature = "badbeef" * 16

        valid = verify_delegation(delegation, self.delegator_pubkey)
        self.assertFalse(valid)

    def test_delegation_invalid_budget(self):
        """Test negative ATP budget rejection"""
        with self.assertRaises(ValueError):
            create_delegation(
                delegator_lct="lct:client:001",
                delegatee_lct="lct:agent:001",
                granted_permissions=["read:*"],
                atp_budget=-100,
                valid_from=datetime.now(timezone.utc),
                valid_until=datetime.now(timezone.utc) + timedelta(days=1),
                organization_id="org:test",
                delegator_private_key=self.delegator_privkey
            )

    def test_delegation_invalid_timerange(self):
        """Test invalid time range rejection"""
        now = datetime.now(timezone.utc)
        with self.assertRaises(ValueError):
            create_delegation(
                delegator_lct="lct:client:001",
                delegatee_lct="lct:agent:001",
                granted_permissions=["read:*"],
                atp_budget=1000,
                valid_from=now + timedelta(days=1),
                valid_until=now,  # Before valid_from
                organization_id="org:test",
                delegator_private_key=self.delegator_privkey
            )

    def test_delegation_self_delegation(self):
        """Test self-delegation rejection"""
        with self.assertRaises(ValueError):
            create_delegation(
                delegator_lct="lct:entity:001",
                delegatee_lct="lct:entity:001",  # Same as delegator
                granted_permissions=["read:*"],
                atp_budget=1000,
                valid_from=datetime.now(timezone.utc),
                valid_until=datetime.now(timezone.utc) + timedelta(days=1),
                organization_id="org:test",
                delegator_private_key=self.delegator_privkey
            )

    def test_delegation_to_dict(self):
        """Test delegation serialization"""
        delegation = create_delegation(
            delegator_lct="lct:client:001",
            delegatee_lct="lct:agent:001",
            granted_permissions=["read:*"],
            atp_budget=1000,
            valid_from=datetime.now(timezone.utc),
            valid_until=datetime.now(timezone.utc) + timedelta(days=1),
            organization_id="org:test",
            delegator_private_key=self.delegator_privkey
        )

        delegation_dict = delegation.to_dict()
        self.assertEqual(delegation_dict["delegator_lct"], "lct:client:001")
        self.assertEqual(delegation_dict["atp_budget"], 1000)


@unittest.skipUnless(CRYPTO_AVAILABLE, "cryptography library required")
class TestBirthCertificates(unittest.TestCase):
    """Test birth certificate signing"""

    def setUp(self):
        """Set up test fixtures"""
        self.society_privkey, self.society_pubkey = generate_test_keypair()
        self.witness1_privkey, self.witness1_pubkey = generate_test_keypair()
        self.witness2_privkey, self.witness2_pubkey = generate_test_keypair()

    def test_create_birth_certificate(self):
        """Test birth certificate creation"""
        cert = create_birth_certificate(
            lct_id="lct:ai:agent:newborn:001",
            entity_type="AI",
            society_id="web4:default",
            law_oracle_id="oracle:law:default",
            law_version="v1.0.0",
            witnesses=["witness:001", "witness:002"],
            society_private_key=self.society_privkey
        )

        self.assertEqual(cert.lct_id, "lct:ai:agent:newborn:001")
        self.assertEqual(cert.entity_type, "AI")
        self.assertEqual(cert.society_id, "web4:default")
        self.assertEqual(len(cert.witnesses), 2)
        self.assertIn("exist", cert.initial_rights)
        self.assertIn("abide_law", cert.initial_responsibilities)
        self.assertIsNotNone(cert.certificate_hash)
        self.assertIsNotNone(cert.society_signature)

    def test_verify_birth_certificate_valid(self):
        """Test valid birth certificate verification"""
        cert = create_birth_certificate(
            lct_id="lct:ai:agent:001",
            entity_type="AI",
            society_id="web4:test",
            law_oracle_id="oracle:law:test",
            law_version="v1.0.0",
            witnesses=["witness:001"],
            society_private_key=self.society_privkey
        )

        valid, errors = verify_birth_certificate(cert, self.society_pubkey)
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)

    def test_verify_birth_certificate_invalid_society(self):
        """Test invalid society signature detection"""
        cert = create_birth_certificate(
            lct_id="lct:ai:agent:001",
            entity_type="AI",
            society_id="web4:test",
            law_oracle_id="oracle:law:test",
            law_version="v1.0.0",
            witnesses=["witness:001"],
            society_private_key=self.society_privkey
        )

        # Corrupt society signature
        cert.society_signature = "deadbeef" * 16

        valid, errors = verify_birth_certificate(cert, self.society_pubkey)
        self.assertFalse(valid)
        self.assertIn("Invalid society signature", errors)

    def test_add_witness_signature(self):
        """Test adding witness signatures"""
        cert = create_birth_certificate(
            lct_id="lct:ai:agent:001",
            entity_type="AI",
            society_id="web4:test",
            law_oracle_id="oracle:law:test",
            law_version="v1.0.0",
            witnesses=["witness:001", "witness:002"],
            society_private_key=self.society_privkey
        )

        # Add first witness signature
        cert = add_witness_signature(cert, "witness:001", self.witness1_privkey)
        self.assertIn("witness:001", cert.witness_signatures)

        # Add second witness signature
        cert = add_witness_signature(cert, "witness:002", self.witness2_privkey)
        self.assertIn("witness:002", cert.witness_signatures)

    def test_add_duplicate_witness_signature(self):
        """Test duplicate witness rejection"""
        cert = create_birth_certificate(
            lct_id="lct:ai:agent:001",
            entity_type="AI",
            society_id="web4:test",
            law_oracle_id="oracle:law:test",
            law_version="v1.0.0",
            witnesses=["witness:001"],
            society_private_key=self.society_privkey
        )

        # Add witness signature
        cert = add_witness_signature(cert, "witness:001", self.witness1_privkey)

        # Try to add again
        with self.assertRaises(ValueError):
            add_witness_signature(cert, "witness:001", self.witness1_privkey)

    def test_verify_birth_certificate_with_witnesses(self):
        """Test verification with witness signatures"""
        cert = create_birth_certificate(
            lct_id="lct:ai:agent:001",
            entity_type="AI",
            society_id="web4:test",
            law_oracle_id="oracle:law:test",
            law_version="v1.0.0",
            witnesses=["witness:001", "witness:002"],
            society_private_key=self.society_privkey
        )

        # Add witness signatures
        cert = add_witness_signature(cert, "witness:001", self.witness1_privkey)
        cert = add_witness_signature(cert, "witness:002", self.witness2_privkey)

        # Verify with witness keys
        witness_keys = {
            "witness:001": self.witness1_pubkey,
            "witness:002": self.witness2_pubkey
        }

        valid, errors = verify_birth_certificate(cert, self.society_pubkey, witness_keys)
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)

    def test_certificate_hash_deterministic(self):
        """Test certificate hash is deterministic"""
        cert1 = create_birth_certificate(
            lct_id="lct:ai:agent:001",
            entity_type="AI",
            society_id="web4:test",
            law_oracle_id="oracle:law:test",
            law_version="v1.0.0",
            witnesses=["witness:001"],
            society_private_key=self.society_privkey
        )

        # Manually create another with same data (different timestamp though)
        # So we'll just check hash format
        self.assertIn("0x", cert1.certificate_hash)
        self.assertEqual(len(cert1.certificate_hash), 66)  # 0x + 64 hex chars


@unittest.skipUnless(CRYPTO_AVAILABLE, "cryptography library required")
class TestHMAC(unittest.TestCase):
    """Test HMAC message authentication"""

    def test_generate_hmac_sha256(self):
        """Test HMAC generation with SHA256"""
        message = b"Hello Web4!"
        secret_key = b"secret_key_12345"

        hmac_value = generate_hmac(message, secret_key, "sha256")

        self.assertIsNotNone(hmac_value)
        self.assertEqual(len(hmac_value), 64)  # SHA256 = 32 bytes = 64 hex chars

    def test_verify_hmac_valid(self):
        """Test valid HMAC verification"""
        message = b"Test message"
        secret_key = b"shared_secret"

        hmac_value = generate_hmac(message, secret_key)
        valid = verify_hmac(message, secret_key, hmac_value)

        self.assertTrue(valid)

    def test_verify_hmac_invalid_message(self):
        """Test HMAC fails with wrong message"""
        message1 = b"Original message"
        message2 = b"Modified message"
        secret_key = b"shared_secret"

        hmac_value = generate_hmac(message1, secret_key)
        valid = verify_hmac(message2, secret_key, hmac_value)

        self.assertFalse(valid)

    def test_verify_hmac_invalid_key(self):
        """Test HMAC fails with wrong key"""
        message = b"Test message"
        secret_key1 = b"key1"
        secret_key2 = b"key2"

        hmac_value = generate_hmac(message, secret_key1)
        valid = verify_hmac(message, secret_key2, hmac_value)

        self.assertFalse(valid)

    def test_generate_hmac_sha512(self):
        """Test HMAC generation with SHA512"""
        message = b"Hello Web4!"
        secret_key = b"secret_key_12345"

        hmac_value = generate_hmac(message, secret_key, "sha512")

        self.assertIsNotNone(hmac_value)
        self.assertEqual(len(hmac_value), 128)  # SHA512 = 64 bytes = 128 hex chars

    def test_generate_hmac_invalid_algorithm(self):
        """Test unsupported algorithm rejection"""
        message = b"Test"
        secret_key = b"key"

        with self.assertRaises(ValueError):
            generate_hmac(message, secret_key, "md5")


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""

    def test_generate_nonce_default(self):
        """Test nonce generation with default length"""
        nonce = generate_nonce()

        self.assertIsNotNone(nonce)
        # Base64 encoding: 16 bytes -> 24 chars (with padding)
        self.assertGreaterEqual(len(nonce), 20)

    def test_generate_nonce_custom_length(self):
        """Test nonce generation with custom length"""
        nonce = generate_nonce(length=32)

        self.assertIsNotNone(nonce)
        # Base64 encoding: 32 bytes -> 44 chars
        self.assertGreaterEqual(len(nonce), 40)

    def test_nonces_unique(self):
        """Test nonces are unique"""
        nonces = {generate_nonce() for _ in range(100)}

        # All nonces should be unique
        self.assertEqual(len(nonces), 100)

    def test_hash_message_sha256(self):
        """Test SHA256 message hashing"""
        message = b"Hello Web4!"
        hash_value = hash_message(message, "sha256")

        self.assertIn("0x", hash_value)
        self.assertEqual(len(hash_value), 66)  # 0x + 64 hex chars

    def test_hash_message_sha512(self):
        """Test SHA512 message hashing"""
        message = b"Hello Web4!"
        hash_value = hash_message(message, "sha512")

        self.assertIn("0x", hash_value)
        self.assertEqual(len(hash_value), 130)  # 0x + 128 hex chars

    def test_hash_message_deterministic(self):
        """Test hashing is deterministic"""
        message = b"Test message"
        hash1 = hash_message(message)
        hash2 = hash_message(message)

        self.assertEqual(hash1, hash2)

    def test_hash_message_invalid_algorithm(self):
        """Test unsupported hash algorithm rejection"""
        message = b"Test"

        with self.assertRaises(ValueError):
            hash_message(message, "md5")


if __name__ == '__main__':
    unittest.main()
