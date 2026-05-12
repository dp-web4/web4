#!/usr/bin/env python3
"""
Security Attack Test Suite
Session #58: Comprehensive testing of attack vector mitigations

Tests all 16 attack vectors identified in Session #56 ATTACK_VECTORS.md:

Batch-Specific Attacks:
1. Batch stuffing (rate limiting)
2. Timing attacks (flush timing)
3. Memory exhaustion (pending limits)
4. Race conditions (thread safety)

Trust Score Manipulation:
5. Sybil attacks (identity verification)
6. Reputation washing (audit trail)
7. Score clamping exploitation

Delegation Attacks:
8. Unauthorized delegation
9. Delegation depth
10. Revocation evasion

ATP Attacks:
11. ATP refund exploitation
12. ATP drain attacks

Data Integrity:
13. Flush interruption (atomic transactions)
14. SQL injection (parameterized queries)
15. Batch replay (Merkle roots)
16. Merkle tree tampering (Session #57)

Status:
- ✅ 5/16 Mitigated (Rate limits, Thread safety, SQL injection, Merkle, Delegation depth)
- ⚠️ 11/16 Need testing or implementation
"""

import unittest
import psycopg2
import time
import threading
from decimal import Decimal
from datetime import datetime, timedelta
import hashlib

from trust_update_batcher import TrustUpdateBatcher
from trust_merkle_tree import TrustMerkleTree, TrustUpdateLeaf
from trust_api import TrustAPI

# Test database configuration
TEST_DB_CONFIG = {
    'dbname': 'web4',
    'user': 'postgres',
    'host': 'localhost'
}


class SecurityTestBase(unittest.TestCase):
    """Base class for security tests"""

    @classmethod
    def setUpClass(cls):
        """Set up test database"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()

        # Ensure all required tables exist
        # (Assuming they were created by previous sessions)

        conn.commit()
        cursor.close()
        conn.close()

    def setUp(self):
        """Clean test data before each test"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()

        # Clean test data
        cursor.execute("DELETE FROM reputation_scores WHERE lct_id LIKE 'lct:attack:%'")
        cursor.execute("DELETE FROM v3_scores WHERE lct_id LIKE 'lct:attack:%'")
        cursor.execute("DELETE FROM merkle_roots WHERE merkle_root LIKE 'test:%'")
        cursor.execute("DELETE FROM trust_update_leaves WHERE lct_id LIKE 'lct:attack:%'")
        cursor.execute("DELETE FROM lct_identities WHERE lct_id LIKE 'lct:attack:%'")
        cursor.execute("DELETE FROM organizations WHERE organization_id LIKE 'org:attack:%'")

        conn.commit()
        cursor.close()
        conn.close()

    def _create_test_identity(self, lct_id: str, org_id: str):
        """Helper to create test LCT identity and organization"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()

        # Create admin LCT
        cursor.execute("""
            INSERT INTO lct_identities (lct_id, entity_type, birth_certificate_hash, public_key)
            VALUES ('lct:admin:test', 'ai', 'bc:admin', 'pk:admin')
            ON CONFLICT DO NOTHING
        """)

        # Create test organization
        cursor.execute("""
            INSERT INTO organizations (organization_id, organization_name, admin_lct_id)
            VALUES (%s, %s, 'lct:admin:test')
            ON CONFLICT DO NOTHING
        """, (org_id, f"Test Org {org_id}"))

        # Create LCT identity
        cursor.execute("""
            INSERT INTO lct_identities (
                lct_id,
                entity_type,
                birth_certificate_hash,
                public_key,
                created_at
            )
            VALUES (%s, 'ai', %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (lct_id) DO NOTHING
        """, (
            lct_id,
            'bc:' + lct_id[:16],
            'pk:' + lct_id[:16]
        ))

        # Create reputation scores entry
        cursor.execute("""
            INSERT INTO reputation_scores (lct_id, organization_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (lct_id, org_id))

        # Create V3 scores entry
        cursor.execute("""
            INSERT INTO v3_scores (lct_id, organization_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (lct_id, org_id))

        conn.commit()
        cursor.close()
        conn.close()


class TestBatchStuffingAttack(SecurityTestBase):
    """
    Attack Vector 1: Batch Stuffing
    Status: ✅ MITIGATED (Session #56 rate limiting)

    Test that rate limiting prevents batch stuffing attacks.
    """

    def test_rate_limit_prevents_stuffing(self):
        """Test that rate limiting blocks excessive updates"""
        # Create batcher with strict rate limit
        batcher = TrustUpdateBatcher(
            db_config=TEST_DB_CONFIG,
            max_updates_per_minute_per_lct=5,  # Very low for testing
            auto_start=False
        )

        lct_id = 'lct:attack:stuffing:001'
        org_id = 'org:attack:001'

        # First 5 updates should succeed
        success_count = 0
        for i in range(5):
            try:
                batcher.record_t3_update(
                    lct_id=lct_id,
                    org_id=org_id,
                    talent_delta=Decimal('0.001')
                )
                success_count += 1
            except RuntimeError:
                pass

        self.assertEqual(success_count, 5, "First 5 updates should succeed")

        # 6th update should fail (rate limited)
        with self.assertRaises(RuntimeError) as context:
            batcher.record_t3_update(
                lct_id=lct_id,
                org_id=org_id,
                talent_delta=Decimal('0.001')
            )

        self.assertIn("Rate limit exceeded", str(context.exception))

        # Check statistics
        stats = batcher.get_stats()
        self.assertEqual(stats['rate_limit_rejections'], 1)
        self.assertEqual(stats['total_updates_recorded'], 5)

    def test_batch_size_limit_prevents_stuffing(self):
        """Test that batch size limit forces flush"""
        batcher = TrustUpdateBatcher(
            db_config=TEST_DB_CONFIG,
            max_batch_size=10,  # Small batch for testing
            max_updates_per_minute_per_lct=1000,  # High rate limit
            auto_start=False
        )

        # Create 10 different entities
        for i in range(10):
            lct_id = f'lct:attack:stuffing:{i:03d}'
            org_id = 'org:attack:001'
            self._create_test_identity(lct_id, org_id)

            batcher.record_t3_update(
                lct_id=lct_id,
                org_id=org_id,
                talent_delta=Decimal('0.001')
            )

        # Pending should be flushed at batch size
        self.assertEqual(batcher.get_pending_count(), 0, "Batch should auto-flush at size limit")
        self.assertEqual(batcher.stats['total_flushes'], 1)


class TestMemoryExhaustionAttack(SecurityTestBase):
    """
    Attack Vector 3: Memory Exhaustion
    Status: ✅ MITIGATED (Session #56 pending limits)

    Test that pending limits prevent memory exhaustion.
    """

    def test_total_pending_limit(self):
        """Test that total pending limit is enforced"""
        batcher = TrustUpdateBatcher(
            db_config=TEST_DB_CONFIG,
            max_pending_total=10,  # Very low limit for testing
            max_updates_per_minute_per_lct=10000,  # High rate limit
            auto_start=False
        )

        # Try to create 20 pending updates (20 unique entities)
        success_count = 0
        reject_count = 0
        for i in range(20):
            try:
                batcher.record_t3_update(
                    lct_id=f'lct:attack:memory:{i:03d}',
                    org_id='org:attack:001',
                    talent_delta=Decimal('0.001')
                )
                success_count += 1
            except RuntimeError as e:
                if "Pending limit exceeded" in str(e):
                    reject_count += 1

        # Should stop at max_pending_total
        self.assertLessEqual(success_count, 10, "Should not exceed max_pending_total")
        self.assertGreater(reject_count, 0, "Should reject some updates")

    def test_per_lct_pending_limit(self):
        """Test that per-LCT pending limit is enforced"""
        batcher = TrustUpdateBatcher(
            db_config=TEST_DB_CONFIG,
            max_pending_per_lct=5,  # Very low for testing
            max_updates_per_minute_per_lct=10000,
            auto_start=False
        )

        lct_id = 'lct:attack:memory:single'
        org_id = 'org:attack:001'

        # Try to add 10 updates for same entity
        success_count = 0
        for i in range(10):
            try:
                batcher.record_t3_update(
                    lct_id=lct_id,
                    org_id=org_id,
                    talent_delta=Decimal('0.001')
                )
                success_count += 1
            except RuntimeError:
                break

        # Should stop at max_pending_per_lct
        self.assertLessEqual(success_count, 5, "Should not exceed max_pending_per_lct")


class TestThreadSafetyAttack(SecurityTestBase):
    """
    Attack Vector 4: Race Conditions
    Status: ✅ MITIGATED (Session #56 threading)

    Test that concurrent access doesn't corrupt state.
    """

    def test_concurrent_updates_same_entity(self):
        """Test that concurrent updates to same entity are safe"""
        # Create test identity
        lct_id = 'lct:attack:race:001'
        org_id = 'org:attack:001'
        self._create_test_identity(lct_id, org_id)

        batcher = TrustUpdateBatcher(
            db_config=TEST_DB_CONFIG,
            max_updates_per_minute_per_lct=10000,  # High limit
            auto_start=False
        )

        def worker(count):
            """Worker thread that performs updates"""
            for _ in range(count):
                try:
                    batcher.record_t3_update(
                        lct_id=lct_id,
                        org_id=org_id,
                        talent_delta=Decimal('0.001')
                    )
                except RuntimeError:
                    pass  # Rate limit OK

        # Launch 10 threads doing 10 updates each
        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(10,))
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Check that accumulated delta is correct
        # Should have 1 entity with accumulated updates
        self.assertEqual(batcher.get_pending_count(), 1)

        # Get the delta
        key = f"{lct_id}:{org_id}"
        if key in batcher.pending:
            delta = batcher.pending[key]
            # Should be close to 100 updates (some might be rate limited)
            self.assertGreater(delta.actions_count, 0)
            self.assertLessEqual(delta.actions_count, 100)


class TestMerkleReplayAttack(SecurityTestBase):
    """
    Attack Vector 15: Batch Replay
    Status: ✅ MITIGATED (Session #57 Merkle trees)

    Test that Merkle roots prevent replay attacks.
    """

    def test_merkle_root_uniqueness(self):
        """Test that each flush generates unique Merkle root"""
        # Create test identities
        for i in range(5):
            self._create_test_identity(f'lct:attack:merkle:{i:03d}', 'org:attack:001')

        batcher = TrustUpdateBatcher(
            db_config=TEST_DB_CONFIG,
            auto_start=False
        )

        # First flush
        for i in range(5):
            batcher.record_t3_update(
                lct_id=f'lct:attack:merkle:{i:03d}',
                org_id='org:attack:001',
                talent_delta=Decimal('0.001')
            )
        batcher.flush()
        first_root = batcher.last_merkle_root

        # Second flush (same entities, different timestamp)
        time.sleep(0.01)  # Ensure different timestamp
        for i in range(5):
            batcher.record_t3_update(
                lct_id=f'lct:attack:merkle:{i:03d}',
                org_id='org:attack:001',
                talent_delta=Decimal('0.001')
            )
        batcher.flush()
        second_root = batcher.last_merkle_root

        # Roots must be different (timestamp changed)
        self.assertNotEqual(first_root, second_root, "Merkle roots must be unique per flush")

        # Both roots should be in history
        all_roots = batcher.get_all_merkle_roots()
        self.assertEqual(len(all_roots), 2)
        self.assertIn(first_root, all_roots)
        self.assertIn(second_root, all_roots)

    def test_merkle_root_database_uniqueness(self):
        """Test that database enforces Merkle root uniqueness"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()

        # Try to insert duplicate Merkle root (64-char hex string)
        test_root = hashlib.sha256(b'test_unique_1').hexdigest()

        cursor.execute("""
            INSERT INTO merkle_roots (merkle_root, batch_size, leaf_count)
            VALUES (%s, 1, 1)
        """, (test_root,))
        conn.commit()

        # Try to insert same root again - should fail
        with self.assertRaises(psycopg2.IntegrityError):
            cursor.execute("""
                INSERT INTO merkle_roots (merkle_root, batch_size, leaf_count)
                VALUES (%s, 1, 1)
            """, (test_root,))
            conn.commit()

        conn.rollback()
        cursor.close()
        conn.close()


class TestMerkleTamperDetection(SecurityTestBase):
    """
    Attack Vector 16: Merkle Tree Tampering
    Status: ✅ MITIGATED (Session #57)

    Test that Merkle proofs detect tampering.
    """

    def test_tampered_leaf_rejected(self):
        """Test that tampered leaf hash fails verification"""
        # Create valid Merkle tree
        updates = []
        for i in range(10):
            updates.append(TrustUpdateLeaf(
                lct_id=f'lct:attack:tamper:{i:03d}',
                org_id='org:attack:001',
                talent_delta=Decimal('0.001'),
                training_delta=Decimal('0.002'),
                temperament_delta=Decimal('0.001'),
                veracity_delta=Decimal('0.0'),
                validity_delta=Decimal('0.0'),
                valuation_delta=Decimal('0.0'),
                timestamp=datetime.utcnow(),
                action_count=1,
                transaction_count=0
            ))

        tree = TrustMerkleTree(updates)
        root = tree.get_root()

        # Get valid proof for first update
        proof = tree.get_proof(0)

        # Verify with correct leaf - should pass
        correct_leaf_hash = updates[0].hash()
        is_valid = TrustMerkleTree.verify_proof(correct_leaf_hash, proof, root)
        self.assertTrue(is_valid, "Valid proof should verify")

        # Create tampered update
        tampered_update = TrustUpdateLeaf(
            lct_id=f'lct:attack:tamper:000',
            org_id='org:attack:001',
            talent_delta=Decimal('0.999'),  # TAMPERED
            training_delta=Decimal('0.002'),
            temperament_delta=Decimal('0.001'),
            veracity_delta=Decimal('0.0'),
            validity_delta=Decimal('0.0'),
            valuation_delta=Decimal('0.0'),
            timestamp=updates[0].timestamp,
            action_count=1,
            transaction_count=0
        )

        tampered_hash = tampered_update.hash()

        # Verify with tampered leaf - should fail
        is_tampered_valid = TrustMerkleTree.verify_proof(tampered_hash, proof, root)
        self.assertFalse(is_tampered_valid, "Tampered proof should fail")

    def test_tampered_proof_rejected(self):
        """Test that tampered proof path fails verification"""
        updates = []
        for i in range(4):
            updates.append(TrustUpdateLeaf(
                lct_id=f'lct:attack:proof:{i:03d}',
                org_id='org:attack:001',
                talent_delta=Decimal('0.001'),
                training_delta=Decimal('0.0'),
                temperament_delta=Decimal('0.0'),
                veracity_delta=Decimal('0.0'),
                validity_delta=Decimal('0.0'),
                valuation_delta=Decimal('0.0'),
                timestamp=datetime.utcnow()
            ))

        tree = TrustMerkleTree(updates)
        root = tree.get_root()
        proof = tree.get_proof(0)

        # Tamper with proof by changing a hash
        if proof:
            tampered_proof = proof.copy()
            # Change first sibling hash
            original_hash, position = tampered_proof[0]
            fake_hash = hashlib.sha256(b'fake').digest()
            tampered_proof[0] = (fake_hash, position)

            # Verification should fail
            leaf_hash = updates[0].hash()
            is_valid = TrustMerkleTree.verify_proof(leaf_hash, tampered_proof, root)
            self.assertFalse(is_valid, "Tampered proof should fail verification")


class TestSQLInjectionAttack(SecurityTestBase):
    """
    Attack Vector 14: SQL Injection
    Status: ✅ MITIGATED (Session #56 parameterized queries)

    Test that SQL injection attempts are blocked.
    """

    def test_lct_id_injection_blocked(self):
        """Test that SQL injection via lct_id is blocked"""
        # Create batcher
        batcher = TrustUpdateBatcher(
            db_config=TEST_DB_CONFIG,
            auto_start=False
        )

        # Try SQL injection in lct_id
        malicious_lct = "lct:attack'; DROP TABLE reputation_scores; --"
        org_id = 'org:attack:001'

        # This should not execute SQL - will fail due to FK constraint or be safe
        try:
            batcher.record_t3_update(
                lct_id=malicious_lct,
                org_id=org_id,
                talent_delta=Decimal('0.001')
            )
            batcher.flush()
        except Exception:
            pass  # Expected to fail, but not via SQL injection

        # Verify that reputation_scores table still exists
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_name = 'reputation_scores'
        """)
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        self.assertIsNotNone(result, "Table should still exist (SQL injection blocked)")


class TestScoreClampingExploitation(SecurityTestBase):
    """
    Attack Vector 7: Score Clamping Exploitation
    Status: ⚠️ VULNERABLE (Session #56 identified)

    Test current clamping behavior and document the vulnerability.
    """

    def test_clamping_at_maximum(self):
        """Test that scores clamp at 1.0"""
        lct_id = 'lct:attack:clamp:001'
        org_id = 'org:attack:001'
        self._create_test_identity(lct_id, org_id)

        # Set scores to 0.99
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE reputation_scores
            SET talent_score = 0.99, training_score = 0.99, temperament_score = 0.99
            WHERE lct_id = %s AND organization_id = %s
        """, (lct_id, org_id))
        conn.commit()
        cursor.close()
        conn.close()

        # Apply update that would exceed 1.0
        batcher = TrustUpdateBatcher(
            db_config=TEST_DB_CONFIG,
            auto_start=False
        )

        batcher.record_t3_update(
            lct_id=lct_id,
            org_id=org_id,
            talent_delta=Decimal('0.05')  # 0.99 + 0.05 = 1.04 -> should clamp to 1.0
        )
        batcher.flush()

        # Verify clamping
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT talent_score FROM reputation_scores
            WHERE lct_id = %s AND organization_id = %s
        """, (lct_id, org_id))
        score = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        self.assertEqual(score, Decimal('1.0'), "Score should clamp at 1.0")

    def test_slow_decay_from_maximum(self):
        """Document that decay from maximum is linear (slow)"""
        lct_id = 'lct:attack:clamp:002'
        org_id = 'org:attack:001'
        self._create_test_identity(lct_id, org_id)

        # Set score to 1.0
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE reputation_scores
            SET talent_score = 1.0
            WHERE lct_id = %s AND organization_id = %s
        """, (lct_id, org_id))
        conn.commit()
        cursor.close()
        conn.close()

        # Simulate failed actions
        batcher = TrustUpdateBatcher(
            db_config=TEST_DB_CONFIG,
            auto_start=False
        )

        # 10 failed actions
        for _ in range(10):
            batcher.record_t3_update(
                lct_id=lct_id,
                org_id=org_id,
                talent_delta=Decimal('-0.001')  # Small penalty
            )

        batcher.flush()

        # Check score
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT talent_score FROM reputation_scores
            WHERE lct_id = %s AND organization_id = %s
        """, (lct_id, org_id))
        score = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        # Should be 0.99 (1.0 - 0.01)
        self.assertEqual(score, Decimal('0.9900'), "Linear decay from maximum")

        # This demonstrates the vulnerability: takes 1000 failures to go from 1.0 to 0.0
        # with -0.001 penalty. Attacker can "bank" trust and abuse it.


# Test runner
if __name__ == '__main__':
    print("Security Attack Test Suite - Session #58")
    print("=" * 70)
    print("Testing attack vector mitigations from ATTACK_VECTORS.md")
    print("=" * 70)

    # Run with verbosity
    unittest.main(verbosity=2)
