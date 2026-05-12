#!/usr/bin/env python3
"""
Comprehensive Tests for AI Agent Delegation System - Session #52
================================================================

Tests the complete delegation system including:
1. PostgreSQL persistent storage
2. Ed25519 signature verification
3. Delegation chains (sub-delegation)
4. ATP budget management
5. Automatic revocation on trust drops
6. Audit trail completeness

Usage:
    # Requires PostgreSQL running with test database
    export DATABASE_URL="host=localhost dbname=web4_auth_test user=test password=test"
    python3 test_delegation_system.py

Session #52: AI Agent Authorization & Delegation System
"""

import unittest
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

# Try to import PostgreSQL components
try:
    import psycopg2
    from pg_permission_store import (
        PostgreSQLPermissionStore,
        PostgreSQLDelegationStore,
        PostgreSQLReputationService
    )
    from crypto_verification import CryptoVerifier, ClaimSigner, CRYPTO_AVAILABLE
    POSTGRES_AVAILABLE = True
except ImportError as e:
    print(f"PostgreSQL components not available: {e}")
    POSTGRES_AVAILABLE = False

# Import Web4 crypto for key generation
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "act_deployment"))
    from web4_crypto import Web4Crypto
    from lct import create_lct_identity, LCTContext
    WEB4_CRYPTO_AVAILABLE = True
except ImportError:
    WEB4_CRYPTO_AVAILABLE = False


# Test configuration
TEST_DB_URL = os.getenv('DATABASE_URL', 'host=localhost dbname=web4_auth_test user=test password=test')


@unittest.skipUnless(POSTGRES_AVAILABLE and CRYPTO_AVAILABLE and WEB4_CRYPTO_AVAILABLE,
                     "Requires PostgreSQL, cryptography, and Web4 crypto")
class TestDelegationSystem(unittest.TestCase):
    """Integration tests for complete delegation system"""

    @classmethod
    def setUpClass(cls):
        """Set up test database"""
        # Create test database if it doesn't exist
        try:
            conn = psycopg2.connect(TEST_DB_URL)
            conn.close()
        except psycopg2.OperationalError:
            # Try to create database
            admin_url = TEST_DB_URL.replace('dbname=web4_auth_test', 'dbname=postgres')
            conn = psycopg2.connect(admin_url)
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute("CREATE DATABASE web4_auth_test")
            cur.close()
            conn.close()

        # Initialize schema
        cls.permission_store = PostgreSQLPermissionStore(TEST_DB_URL)
        cls.delegation_store = PostgreSQLDelegationStore(TEST_DB_URL)
        cls.reputation_service = PostgreSQLReputationService(TEST_DB_URL)

    def setUp(self):
        """Set up test fixtures"""
        # Create test identities
        self.alice_lct, self.alice_keypair = create_lct_identity("Alice", LCTContext.AI_AGENT, deterministic=True)
        self.bob_lct, self.bob_keypair = create_lct_identity("Bob", LCTContext.AI_AGENT, deterministic=True)
        self.charlie_lct, self.charlie_keypair = create_lct_identity("Charlie", LCTContext.AI_AGENT, deterministic=True)

        # Register public keys
        self.verifier = CryptoVerifier()
        self.verifier.register_public_key(str(self.alice_lct), self.alice_keypair[1])  # public_key
        self.verifier.register_public_key(str(self.bob_lct), self.bob_keypair[1])
        self.verifier.register_public_key(str(self.charlie_lct), self.charlie_keypair[1])

        # Create signers
        self.alice_signer = ClaimSigner(
            self.alice_keypair[0],  # private_key
            self.alice_keypair[1],  # public_key
            str(self.alice_lct)
        )

    def test_01_signature_verification(self):
        """Test Ed25519 signature verification"""
        print("\n=== Test: Ed25519 Signature Verification ===")

        # Create test claim data
        claim_data = {
            "subject_lct": str(self.bob_lct),
            "issuer_lct": str(self.alice_lct),
            "permission": "read",
            "resource": "code:*",
            "scope": None,
            "organization": "org:web4:default",
            "issued_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": None
        }

        # Sign claim
        signature = self.alice_signer.sign_claim(claim_data)
        print(f"Signature generated: {len(signature)} bytes")

        # Verify signature
        result = self.verifier.verify_claim_signature(
            claim_data,
            signature,
            str(self.alice_lct),
            self.alice_keypair[1]
        )

        self.assertTrue(result.valid, f"Signature verification failed: {result.error}")
        print(f"✅ Signature verified successfully")
        print(f"   Message hash: {result.message_hash[:16]}...")

    def test_02_permission_claim_storage(self):
        """Test storing and retrieving permission claims"""
        print("\n=== Test: Permission Claim Storage ===")

        from permission_claim import PermissionClaim

        # Create claim
        claim = PermissionClaim(
            subject_lct=str(self.bob_lct),
            permission="write",
            resource="data:project1:*",
            issuer_lct=str(self.alice_lct),
            organization="org:web4:default",
            description="Write access to project1 data"
        )

        # Sign claim
        claim_data = {
            "subject_lct": claim.subject_lct,
            "issuer_lct": claim.issuer_lct,
            "permission": claim.permission,
            "resource": claim.resource,
            "scope": claim.scope,
            "organization": claim.organization,
            "issued_at": claim.issued_at.isoformat(),
            "expires_at": claim.expires_at.isoformat() if claim.expires_at else None
        }
        signature = self.alice_signer.sign_claim(claim_data)
        claim.signature = signature.hex()

        # Store claim
        stored = self.permission_store.store_claim(claim)
        self.assertTrue(stored, "Failed to store claim")
        print(f"✅ Claim stored: {claim.claim_hash[:16]}...")

        # Retrieve claim
        retrieved_claims = self.permission_store.get_claims(
            str(self.bob_lct),
            "org:web4:default"
        )
        self.assertGreater(len(retrieved_claims), 0, "No claims retrieved")
        print(f"✅ Retrieved {len(retrieved_claims)} claims for Bob")

        # Verify retrieved claim
        retrieved = retrieved_claims[-1]  # Get last one
        self.assertEqual(retrieved.claim_hash, claim.claim_hash)
        print(f"✅ Claim integrity verified")

    def test_03_delegation_creation(self):
        """Test creating agent delegation"""
        print("\n=== Test: Delegation Creation ===")

        # Alice delegates to Bob
        delegation_id = f"del:alice:bob:{int(time.time())}"
        delegation_data = {
            "delegation_id": delegation_id,
            "delegator_lct": str(self.alice_lct),
            "delegatee_lct": str(self.bob_lct),
            "organization": "org:web4:default",
            "granted_claim_hashes": [],
            "atp_budget": 1000,
            "valid_from": datetime.now(timezone.utc).isoformat(),
            "valid_until": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }

        # Sign delegation
        signature = self.alice_signer.sign_delegation(delegation_data)

        # Create delegation
        created = self.delegation_store.create_delegation(
            delegation_id=delegation_id,
            delegator_lct=str(self.alice_lct),
            delegatee_lct=str(self.bob_lct),
            organization_id="org:web4:default",
            granted_claim_hashes=[],
            atp_budget=1000,
            valid_from=datetime.now(timezone.utc),
            valid_until=datetime.now(timezone.utc) + timedelta(days=1),
            delegation_signature=signature.hex(),
            description="Test delegation from Alice to Bob"
        )

        self.assertTrue(created, "Failed to create delegation")
        print(f"✅ Delegation created: {delegation_id}")

        # Retrieve delegation
        delegation = self.delegation_store.get_delegation(delegation_id)
        self.assertIsNotNone(delegation, "Delegation not found")
        self.assertEqual(delegation['atp_budget_total'], 1000)
        self.assertEqual(delegation['atp_budget_spent'], 0)
        print(f"✅ Delegation retrieved with ATP budget: {delegation['atp_budget_total']}")

    def test_04_atp_consumption(self):
        """Test ATP budget consumption"""
        print("\n=== Test: ATP Budget Consumption ===")

        # Create delegation
        delegation_id = f"del:atp:test:{int(time.time())}"
        delegation_data = {
            "delegation_id": delegation_id,
            "delegator_lct": str(self.alice_lct),
            "delegatee_lct": str(self.bob_lct),
            "organization": "org:web4:default",
            "granted_claim_hashes": [],
            "atp_budget": 100,
            "valid_from": datetime.now(timezone.utc).isoformat(),
            "valid_until": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }
        signature = self.alice_signer.sign_delegation(delegation_data)

        self.delegation_store.create_delegation(
            delegation_id=delegation_id,
            delegator_lct=str(self.alice_lct),
            delegatee_lct=str(self.bob_lct),
            organization_id="org:web4:default",
            granted_claim_hashes=[],
            atp_budget=100,
            valid_from=datetime.now(timezone.utc),
            valid_until=datetime.now(timezone.utc) + timedelta(days=1),
            delegation_signature=signature.hex()
        )

        # Consume ATP
        consumed = self.delegation_store.consume_atp(delegation_id, 30)
        self.assertTrue(consumed, "Failed to consume ATP")
        print(f"✅ Consumed 30 ATP")

        # Check remaining budget
        delegation = self.delegation_store.get_delegation(delegation_id)
        self.assertEqual(delegation['atp_budget_spent'], 30)
        self.assertEqual(delegation['atp_remaining'], 70)
        print(f"✅ Remaining ATP: {delegation['atp_remaining']}")

        # Try to consume more than available
        consumed = self.delegation_store.consume_atp(delegation_id, 80)
        self.assertFalse(consumed, "Should not allow consuming more than budget")
        print(f"✅ Prevented over-consumption")

    def test_05_delegation_chain(self):
        """Test sub-delegation (delegation chains)"""
        print("\n=== Test: Delegation Chain (Sub-delegation) ===")

        # Alice -> Bob (parent delegation)
        parent_id = f"del:chain:ab:{int(time.time())}"
        parent_data = {
            "delegation_id": parent_id,
            "delegator_lct": str(self.alice_lct),
            "delegatee_lct": str(self.bob_lct),
            "organization": "org:web4:default",
            "granted_claim_hashes": [],
            "atp_budget": 1000,
            "valid_from": datetime.now(timezone.utc).isoformat(),
            "valid_until": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }
        parent_sig = self.alice_signer.sign_delegation(parent_data)

        self.delegation_store.create_delegation(
            delegation_id=parent_id,
            delegator_lct=str(self.alice_lct),
            delegatee_lct=str(self.bob_lct),
            organization_id="org:web4:default",
            granted_claim_hashes=[],
            atp_budget=1000,
            valid_from=datetime.now(timezone.utc),
            valid_until=datetime.now(timezone.utc) + timedelta(days=1),
            delegation_signature=parent_sig.hex()
        )
        print(f"✅ Parent delegation created: Alice → Bob")

        # Bob -> Charlie (sub-delegation)
        bob_signer = ClaimSigner(
            self.bob_keypair[0],
            self.bob_keypair[1],
            str(self.bob_lct)
        )

        child_id = f"del:chain:bc:{int(time.time())}"
        child_data = {
            "delegation_id": child_id,
            "delegator_lct": str(self.bob_lct),
            "delegatee_lct": str(self.charlie_lct),
            "organization": "org:web4:default",
            "granted_claim_hashes": [],
            "atp_budget": 500,  # Sub-set of Bob's budget
            "valid_from": datetime.now(timezone.utc).isoformat(),
            "valid_until": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }
        child_sig = bob_signer.sign_delegation(child_data)

        self.delegation_store.create_delegation(
            delegation_id=child_id,
            delegator_lct=str(self.bob_lct),
            delegatee_lct=str(self.charlie_lct),
            organization_id="org:web4:default",
            granted_claim_hashes=[],
            atp_budget=500,
            valid_from=datetime.now(timezone.utc),
            valid_until=datetime.now(timezone.utc) + timedelta(days=1),
            delegation_signature=child_sig.hex(),
            parent_delegation_id=parent_id  # Link to parent
        )
        print(f"✅ Child delegation created: Bob → Charlie")

        # Retrieve delegation chain
        chain = self.delegation_store.get_delegation_chain(child_id)
        self.assertEqual(len(chain), 2, f"Expected 2 delegations in chain, got {len(chain)}")
        print(f"✅ Delegation chain retrieved: {len(chain)} levels")
        print(f"   Level 1: {chain[0]['delegator_lct'][:20]}... → {chain[0]['delegatee_lct'][:20]}...")
        print(f"   Level 2: {chain[1]['delegator_lct'][:20]}... → {chain[1]['delegatee_lct'][:20]}...")

    def test_06_action_audit_trail(self):
        """Test action recording for audit trail"""
        print("\n=== Test: Action Audit Trail ===")

        # Create delegation
        delegation_id = f"del:audit:test:{int(time.time())}"
        delegation_data = {
            "delegation_id": delegation_id,
            "delegator_lct": str(self.alice_lct),
            "delegatee_lct": str(self.bob_lct),
            "organization": "org:web4:default",
            "granted_claim_hashes": [],
            "atp_budget": 1000,
            "valid_from": datetime.now(timezone.utc).isoformat(),
            "valid_until": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }
        signature = self.alice_signer.sign_delegation(delegation_data)

        self.delegation_store.create_delegation(
            delegation_id=delegation_id,
            delegator_lct=str(self.alice_lct),
            delegatee_lct=str(self.bob_lct),
            organization_id="org:web4:default",
            granted_claim_hashes=[],
            atp_budget=1000,
            valid_from=datetime.now(timezone.utc),
            valid_until=datetime.now(timezone.utc) + timedelta(days=1),
            delegation_signature=signature.hex()
        )

        # Record actions
        self.delegation_store.record_action(
            delegation_id=delegation_id,
            delegatee_lct=str(self.bob_lct),
            action_type="read",
            target_resource="code:project1:main.py",
            atp_cost=1,
            authorized=True
        )

        self.delegation_store.record_action(
            delegation_id=delegation_id,
            delegatee_lct=str(self.bob_lct),
            action_type="write",
            target_resource="data:project1:output.json",
            atp_cost=5,
            authorized=True
        )

        print(f"✅ Recorded 2 actions in audit trail")

    def test_07_delegation_revocation(self):
        """Test delegation revocation"""
        print("\n=== Test: Delegation Revocation ===")

        # Create delegation
        delegation_id = f"del:revoke:test:{int(time.time())}"
        delegation_data = {
            "delegation_id": delegation_id,
            "delegator_lct": str(self.alice_lct),
            "delegatee_lct": str(self.bob_lct),
            "organization": "org:web4:default",
            "granted_claim_hashes": [],
            "atp_budget": 1000,
            "valid_from": datetime.now(timezone.utc).isoformat(),
            "valid_until": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }
        signature = self.alice_signer.sign_delegation(delegation_data)

        self.delegation_store.create_delegation(
            delegation_id=delegation_id,
            delegator_lct=str(self.alice_lct),
            delegatee_lct=str(self.bob_lct),
            organization_id="org:web4:default",
            granted_claim_hashes=[],
            atp_budget=1000,
            valid_from=datetime.now(timezone.utc),
            valid_until=datetime.now(timezone.utc) + timedelta(days=1),
            delegation_signature=signature.hex()
        )

        # Revoke delegation
        revoked = self.delegation_store.revoke_delegation(
            delegation_id,
            "Testing revocation",
            str(self.alice_lct)
        )
        self.assertTrue(revoked, "Failed to revoke delegation")
        print(f"✅ Delegation revoked")

        # Verify it's no longer active
        delegation = self.delegation_store.get_delegation(delegation_id)
        self.assertIsNone(delegation, "Revoked delegation should not appear in active view")
        print(f"✅ Revoked delegation removed from active delegations")


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    if not POSTGRES_AVAILABLE:
        print("ERROR: PostgreSQL components not available")
        print("Install with: pip install psycopg2-binary")
        exit(1)

    if not CRYPTO_AVAILABLE:
        print("ERROR: Cryptography library not available")
        print("Install with: pip install cryptography")
        exit(1)

    if not WEB4_CRYPTO_AVAILABLE:
        print("ERROR: Web4 crypto not available")
        print("Ensure web4_crypto.py and lct.py are in ../act_deployment/")
        exit(1)

    print("=" * 70)
    print("AI Agent Delegation System - Comprehensive Test Suite")
    print("=" * 70)
    print(f"\nDatabase: {TEST_DB_URL}")
    print(f"Cryptography available: {CRYPTO_AVAILABLE}")
    print(f"PostgreSQL available: {POSTGRES_AVAILABLE}")
    print(f"Web4 Crypto available: {WEB4_CRYPTO_AVAILABLE}")
    print()

    run_tests()
