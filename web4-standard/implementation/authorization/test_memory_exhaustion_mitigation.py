#!/usr/bin/env python3
"""
Test Suite for Memory Exhaustion Mitigation
Session #62: P1 Security Verification

Tests that pending update limits prevent the Memory Exhaustion attack
from ATTACK_VECTORS.md (Attack Vector 1.3).

Attack Pattern (from ATTACK_VECTORS.md):
- Attacker creates millions of pending updates
- Each TrustDelta ~200 bytes
- 10M updates = 2GB RAM → OOM denial of service

Mitigation (Already Implemented):
- max_pending_total = 10,000 (absolute limit)
- max_pending_per_lct = 100 (per-entity limit)
- Force flush when limits approached
- RuntimeError on limit exceeded

This test verifies the existing mitigation works correctly.
"""

import unittest
import psycopg2
from decimal import Decimal
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from trust_update_batcher import TrustUpdateBatcher


class TestMemoryExhaustionMitigation(unittest.TestCase):
    """Test memory exhaustion attack prevention"""

    @classmethod
    def setUpClass(cls):
        """Setup test database"""
        cls.db_config = {
            'dbname': 'web4_test',
            'user': 'postgres',
            'host': 'localhost'
        }

        # Ensure test entities exist
        conn = psycopg2.connect(**cls.db_config)
        cursor = conn.cursor()

        # Create test LCTs
        for i in range(150):  # Need more than max_pending_per_lct
            cursor.execute("""
                INSERT INTO lct_identities (lct_id, entity_type, birth_certificate_hash, public_key)
                VALUES (%s, 'ai', %s, %s)
                ON CONFLICT (lct_id) DO NOTHING
            """, (f'lct:mem:test:{i:04d}', f'bc:mem:{i}', f'pubkey:mem:{i}'))

        cursor.execute("""
            INSERT INTO organizations (organization_id, organization_name)
            VALUES ('org:mem:test', 'Memory Test Org')
            ON CONFLICT (organization_id) DO NOTHING
        """)

        # Create reputation scores
        for i in range(150):
            cursor.execute("""
                INSERT INTO reputation_scores (lct_id, organization_id)
                VALUES (%s, 'org:mem:test')
                ON CONFLICT (lct_id, organization_id) DO NOTHING
            """, (f'lct:mem:test:{i:04d}',))

        conn.commit()
        cursor.close()
        conn.close()

    def test_attack_scenario_from_attack_vectors(self):
        """
        Test exact attack from ATTACK_VECTORS.md:

        Attack:
        - Create updates for millions of unique entities
        - Each TrustDelta ~200 bytes
        - Attempt to exhaust memory

        Expected:
        - System rejects updates after max_pending_total (10,000)
        - Memory bounded, OOM prevented
        """
        print("\n=== Test: ATTACK_VECTORS.md Attack Scenario ===")

        batcher = TrustUpdateBatcher(
            db_config=self.db_config,
            flush_interval_seconds=3600,  # Very long (won't auto-flush)
            max_batch_size=1000000,       # Very high (won't trigger flush)
            max_pending_total=100,        # Low limit for fast testing
            max_pending_per_lct=10,       # Low limit for fast testing
            auto_start=False
        )

        print(f"  Configuration:")
        print(f"    max_pending_total: {batcher.max_pending_total}")
        print(f"    max_pending_per_lct: {batcher.max_pending_per_lct}")

        # Attempt to create 200 unique pending updates (exceeds 100 limit)
        print(f"\n  Attempting to create 200 unique pending updates...")

        accepted_count = 0
        rejected_count = 0

        for i in range(200):
            try:
                batcher.record_t3_update(
                    lct_id=f"lct:mem:test:{i:04d}",
                    org_id="org:mem:test",
                    talent_delta=Decimal('0.001')
                )
                accepted_count += 1
            except RuntimeError as e:
                if "Pending limit exceeded" in str(e):
                    rejected_count += 1
                else:
                    raise

        print(f"\n  Results:")
        print(f"    Accepted: {accepted_count} updates")
        print(f"    Rejected: {rejected_count} updates (limit enforcement)")
        print(f"    Pending in memory: {batcher.get_pending_count()}")

        # Verify limit enforcement
        self.assertEqual(accepted_count, 100,
                        "Should accept exactly max_pending_total updates")
        self.assertEqual(rejected_count, 100,
                        "Should reject updates beyond limit")
        self.assertEqual(batcher.get_pending_count(), 100,
                        "Should have max_pending_total in memory")

        print(f"\n  ✅ ATTACK MITIGATED:")
        print(f"     Attacker attempted 200 updates")
        print(f"     System accepted 100, rejected 100")
        print(f"     Memory bounded at {batcher.get_pending_count()} updates")

        # Calculate prevented memory growth
        prevented_updates = rejected_count
        bytes_per_update = 200
        prevented_mb = (prevented_updates * bytes_per_update) / (1024 * 1024)

        print(f"\n  Memory Protection:")
        print(f"     Updates prevented: {prevented_updates}")
        print(f"     Memory saved: {prevented_mb:.2f} MB")
        print(f"     If attacker attempted 10M updates: {(10_000_000 * 200) / (1024**2):.0f} MB blocked")

        batcher.stop()

    def test_per_lct_limit_enforcement(self):
        """Test that per-LCT limits prevent single entity from exhausting memory"""
        print("\n=== Test: Per-LCT Limit Enforcement ===")

        batcher = TrustUpdateBatcher(
            db_config=self.db_config,
            flush_interval_seconds=3600,
            max_batch_size=1000000,
            max_pending_total=1000,
            max_pending_per_lct=10,  # Limit per entity
            auto_start=False
        )

        print(f"  max_pending_per_lct: {batcher.max_pending_per_lct}")

        # Attempt to queue 20 updates for same LCT (exceeds 10 limit)
        accepted = 0
        rejected = 0

        print(f"\n  Attempting 20 updates for single LCT...")

        for i in range(20):
            try:
                batcher.record_t3_update(
                    lct_id="lct:mem:test:0000",
                    org_id="org:mem:test",
                    talent_delta=Decimal('0.001')
                )
                accepted += 1
            except RuntimeError as e:
                if "Pending limit exceeded" in str(e):
                    rejected += 1
                else:
                    raise

        print(f"\n  Results:")
        print(f"    Accepted: {accepted} updates")
        print(f"    Rejected: {rejected} updates")

        # Each update accumulates on same entity, so we get 10 updates before limit
        self.assertLessEqual(accepted, 10,
                           "Should not exceed max_pending_per_lct")
        self.assertGreater(rejected, 0,
                          "Should reject updates beyond per-LCT limit")

        print(f"  ✅ Per-LCT limit enforced")

        batcher.stop()

    def test_memory_bounded_under_attack(self):
        """Test that memory usage stays bounded during sustained attack"""
        print("\n=== Test: Memory Bounded Under Sustained Attack ===")

        batcher = TrustUpdateBatcher(
            db_config=self.db_config,
            flush_interval_seconds=3600,
            max_batch_size=1000000,
            max_pending_total=50,
            max_pending_per_lct=5,
            auto_start=False
        )

        print(f"  Simulating sustained attack...")

        # Simulate attacker repeatedly trying to add updates
        attempts_per_round = 100
        rounds = 10
        total_attempts = 0
        total_accepted = 0
        total_rejected = 0

        for round_num in range(rounds):
            round_accepted = 0
            round_rejected = 0

            for i in range(attempts_per_round):
                try:
                    batcher.record_t3_update(
                        lct_id=f"lct:mem:test:{(total_attempts % 150):04d}",
                        org_id="org:mem:test",
                        talent_delta=Decimal('0.001')
                    )
                    round_accepted += 1
                    total_accepted += 1
                except RuntimeError:
                    round_rejected += 1
                    total_rejected += 1

                total_attempts += 1

            print(f"  Round {round_num+1:2d}: {round_accepted:3d} accepted, "
                  f"{round_rejected:3d} rejected, "
                  f"pending={batcher.get_pending_count()}")

        print(f"\n  Total:")
        print(f"    Attempts: {total_attempts}")
        print(f"    Accepted: {total_accepted}")
        print(f"    Rejected: {total_rejected}")
        print(f"    Final pending: {batcher.get_pending_count()}")

        # Memory should never exceed limit
        self.assertLessEqual(batcher.get_pending_count(), 50,
                           "Pending count should never exceed max_pending_total")

        print(f"\n  ✅ Memory usage remained bounded throughout attack")
        print(f"     Max memory: ~{batcher.get_pending_count() * 200 / 1024:.1f} KB")

        batcher.stop()

    def test_statistics_tracking(self):
        """Test that rejection statistics are tracked"""
        print("\n=== Test: Statistics Tracking ===")

        batcher = TrustUpdateBatcher(
            db_config=self.db_config,
            flush_interval_seconds=3600,
            max_batch_size=1000000,
            max_pending_total=20,
            max_pending_per_lct=5,
            auto_start=False
        )

        # Trigger some rejections
        for i in range(50):
            try:
                batcher.record_t3_update(
                    lct_id=f"lct:mem:test:{i:04d}",
                    org_id="org:mem:test",
                    talent_delta=Decimal('0.001')
                )
            except RuntimeError:
                pass  # Expected

        stats = batcher.get_stats()

        print(f"  Statistics:")
        print(f"    Total update attempts: {stats['total_updates_recorded']}")
        print(f"    Pending limit rejections: {stats['pending_limit_rejections']}")
        print(f"    Pending count: {stats['pending_updates']}")

        self.assertGreater(stats['pending_limit_rejections'], 0,
                          "Should have some rejections")
        self.assertEqual(stats['pending_updates'], 20,
                        "Should have max_pending_total pending")

        print(f"  ✅ Rejection statistics properly tracked")

        batcher.stop()


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
