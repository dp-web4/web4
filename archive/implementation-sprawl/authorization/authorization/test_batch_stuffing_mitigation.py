#!/usr/bin/env python3
"""
Test Suite for Batch Stuffing Mitigation
Session #62: P1 Security Verification

Tests that rate limiting prevents the Batch Stuffing attack
from ATTACK_VECTORS.md (Attack Vector 1.1).

Attack Pattern (from ATTACK_VECTORS.md):
- Attacker floods system with 1000 low-value updates
- Forces batch flush at max_batch_size (100 updates)
- 1000 updates = 10 flushes instead of 1
- Degrades 79x performance to ~8x

Mitigation (Already Implemented):
- max_updates_per_minute_per_lct = 60 (default)
- Rolling 60-second rate limit window
- RuntimeError on limit exceeded
- Statistics tracking

This test verifies the existing mitigation works correctly.
"""

import unittest
import psycopg2
from decimal import Decimal
import sys
import os
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from trust_update_batcher import TrustUpdateBatcher


class TestBatchStuffingMitigation(unittest.TestCase):
    """Test batch stuffing attack prevention via rate limiting"""

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
        for i in range(150):  # Need more than rate limit
            cursor.execute("""
                INSERT INTO lct_identities (lct_id, entity_type, birth_certificate_hash, public_key)
                VALUES (%s, 'ai', %s, %s)
                ON CONFLICT (lct_id) DO NOTHING
            """, (f'lct:batch:test:{i:04d}', f'bc:batch:{i}', f'pubkey:batch:{i}'))

        cursor.execute("""
            INSERT INTO organizations (organization_id, organization_name)
            VALUES ('org:batch:test', 'Batch Test Org')
            ON CONFLICT (organization_id) DO NOTHING
        """)

        # Create reputation scores
        for i in range(150):
            cursor.execute("""
                INSERT INTO reputation_scores (lct_id, organization_id)
                VALUES (%s, 'org:batch:test')
                ON CONFLICT (lct_id, organization_id) DO NOTHING
            """, (f'lct:batch:test:{i:04d}',))

        conn.commit()
        cursor.close()
        conn.close()

    def test_attack_scenario_from_attack_vectors(self):
        """
        Test exact attack from ATTACK_VECTORS.md:

        Attack:
        - Flood system with 1000 low-value updates
        - Force frequent flushes
        - Degrade performance from 79x to ~8x

        Expected:
        - Rate limit blocks excessive updates
        - System accepts max 60 updates/minute per LCT
        - Performance degradation prevented
        """
        print("\n=== Test: ATTACK_VECTORS.md Attack Scenario ===")

        batcher = TrustUpdateBatcher(
            db_config=self.db_config,
            flush_interval_seconds=3600,  # Very long (won't auto-flush)
            max_batch_size=100,
            max_updates_per_minute_per_lct=60,  # Standard rate limit
            auto_start=False
        )

        print(f"  Configuration:")
        print(f"    max_updates_per_minute_per_lct: {batcher.max_updates_per_minute_per_lct}")
        print(f"    max_batch_size: {batcher.max_batch_size}")

        # Attempt batch stuffing attack: 1000 updates from single LCT
        print(f"\n  Attempting batch stuffing: 1000 updates from single LCT...")

        accepted_count = 0
        rejected_count = 0
        attacker_lct = "lct:batch:test:0000"

        for i in range(1000):
            try:
                batcher.record_t3_update(
                    lct_id=attacker_lct,
                    org_id="org:batch:test",
                    talent_delta=Decimal('0.001')
                )
                accepted_count += 1
            except RuntimeError as e:
                if "Rate limit exceeded" in str(e):
                    rejected_count += 1
                else:
                    raise

        print(f"\n  Results:")
        print(f"    Accepted: {accepted_count} updates")
        print(f"    Rejected: {rejected_count} updates (rate limit enforcement)")
        print(f"    Pending in memory: {batcher.get_pending_count()}")

        # Verify rate limit enforcement
        self.assertEqual(accepted_count, 60,
                        "Should accept exactly max_updates_per_minute_per_lct updates")
        self.assertEqual(rejected_count, 940,
                        "Should reject updates beyond rate limit")

        # Check statistics
        stats = batcher.get_stats()
        self.assertEqual(stats['rate_limit_rejections'], 940,
                        "Should track rate limit rejections")

        print(f"\n  ✅ ATTACK MITIGATED:")
        print(f"     Attacker attempted 1000 updates")
        print(f"     System accepted 60, rejected 940")
        print(f"     Rate limit enforcement: {rejected_count / 1000 * 100:.0f}% blocked")

        # Calculate prevented flushes
        without_mitigation_flushes = 1000 // 100  # 10 flushes
        with_mitigation_flushes = 60 // 100 + (1 if 60 % 100 > 0 else 0)  # 1 flush
        prevented_flushes = without_mitigation_flushes - with_mitigation_flushes

        print(f"\n  Performance Protection:")
        print(f"     Without mitigation: {without_mitigation_flushes} flushes")
        print(f"     With mitigation: {with_mitigation_flushes} flush(es)")
        print(f"     Prevented flushes: {prevented_flushes} ({prevented_flushes / without_mitigation_flushes * 100:.0f}%)")

        batcher.stop()

    def test_rate_limit_per_lct(self):
        """Test that rate limit is enforced per LCT independently"""
        print("\n=== Test: Per-LCT Rate Limit Independence ===")

        batcher = TrustUpdateBatcher(
            db_config=self.db_config,
            flush_interval_seconds=3600,
            max_batch_size=1000,
            max_updates_per_minute_per_lct=10,  # Low limit for fast testing
            auto_start=False
        )

        print(f"  Rate limit: {batcher.max_updates_per_minute_per_lct} updates/minute per LCT")

        # Try to add 20 updates from each of 3 different LCTs
        results = {}
        for lct_num in range(3):
            lct_id = f"lct:batch:test:{lct_num:04d}"
            accepted = 0
            rejected = 0

            for i in range(20):
                try:
                    batcher.record_t3_update(
                        lct_id=lct_id,
                        org_id="org:batch:test",
                        talent_delta=Decimal('0.001')
                    )
                    accepted += 1
                except RuntimeError as e:
                    if "Rate limit exceeded" in str(e):
                        rejected += 1
                    else:
                        raise

            results[lct_id] = {'accepted': accepted, 'rejected': rejected}
            print(f"    {lct_id}: {accepted} accepted, {rejected} rejected")

        # Each LCT should get exactly 10 updates
        for lct_id, result in results.items():
            self.assertEqual(result['accepted'], 10,
                           f"{lct_id} should accept exactly 10 updates")
            self.assertEqual(result['rejected'], 10,
                           f"{lct_id} should reject 10 updates")

        print(f"  ✅ Rate limits enforced independently per LCT")
        print(f"     Total accepted: {sum(r['accepted'] for r in results.values())}")
        print(f"     Total rejected: {sum(r['rejected'] for r in results.values())}")

        batcher.stop()

    def test_rate_limit_window_reset(self):
        """Test that rate limit window resets after 60 seconds"""
        print("\n=== Test: Rate Limit Window Reset ===")

        batcher = TrustUpdateBatcher(
            db_config=self.db_config,
            flush_interval_seconds=3600,
            max_batch_size=1000,
            max_updates_per_minute_per_lct=5,  # Very low for fast testing
            auto_start=False
        )

        lct_id = "lct:batch:test:0000"

        # First window: Fill rate limit
        print(f"  First window: Attempting 10 updates (limit: 5)...")
        accepted_first = 0
        rejected_first = 0

        for i in range(10):
            try:
                batcher.record_t3_update(
                    lct_id=lct_id,
                    org_id="org:batch:test",
                    talent_delta=Decimal('0.001')
                )
                accepted_first += 1
            except RuntimeError as e:
                if "Rate limit exceeded" in str(e):
                    rejected_first += 1

        print(f"    Accepted: {accepted_first}, Rejected: {rejected_first}")
        self.assertEqual(accepted_first, 5, "Should accept 5 in first window")
        self.assertEqual(rejected_first, 5, "Should reject 5 in first window")

        # Manually reset window by manipulating rate_limits (simulate 60s passage)
        # In production, this would happen naturally after 60 seconds
        print(f"  Simulating 60-second window expiration...")
        from datetime import timedelta
        if lct_id in batcher.rate_limits:
            count, window_start = batcher.rate_limits[lct_id]
            # Set window_start to 61 seconds ago
            batcher.rate_limits[lct_id] = (count, window_start - timedelta(seconds=61))

        # Second window: Should be able to add more
        print(f"  Second window: Attempting 10 updates (limit: 5)...")
        accepted_second = 0
        rejected_second = 0

        for i in range(10):
            try:
                batcher.record_t3_update(
                    lct_id=lct_id,
                    org_id="org:batch:test",
                    talent_delta=Decimal('0.001')
                )
                accepted_second += 1
            except RuntimeError as e:
                if "Rate limit exceeded" in str(e):
                    rejected_second += 1

        print(f"    Accepted: {accepted_second}, Rejected: {rejected_second}")
        self.assertEqual(accepted_second, 5, "Should accept 5 in second window")
        self.assertEqual(rejected_second, 5, "Should reject 5 in second window")

        print(f"  ✅ Rate limit window resets correctly")
        print(f"     Total accepted across both windows: {accepted_first + accepted_second}")

        batcher.stop()

    def test_multiple_attackers(self):
        """Test that rate limits prevent coordinated attacks"""
        print("\n=== Test: Multiple Concurrent Attackers ===")

        batcher = TrustUpdateBatcher(
            db_config=self.db_config,
            flush_interval_seconds=3600,
            max_batch_size=1000,  # High, so we don't auto-flush
            max_updates_per_minute_per_lct=20,
            max_pending_total=100,  # Also test pending limit
            auto_start=False
        )

        print(f"  Configuration:")
        print(f"    Rate limit: {batcher.max_updates_per_minute_per_lct} updates/min per LCT")
        print(f"    Pending limit: {batcher.max_pending_total} unique keys")

        # 10 attackers, each trying to add 50 updates
        num_attackers = 10
        updates_per_attacker = 50
        total_accepted = 0
        total_rejected = 0

        print(f"\n  Simulating {num_attackers} attackers × {updates_per_attacker} updates each...")

        for attacker_num in range(num_attackers):
            lct_id = f"lct:batch:test:{attacker_num:04d}"

            for i in range(updates_per_attacker):
                try:
                    batcher.record_t3_update(
                        lct_id=lct_id,
                        org_id="org:batch:test",
                        talent_delta=Decimal('0.001')
                    )
                    total_accepted += 1
                except RuntimeError as e:
                    if "limit exceeded" in str(e).lower():
                        total_rejected += 1
                    else:
                        raise

        print(f"\n  Results:")
        print(f"    Total attempted: {num_attackers * updates_per_attacker}")
        print(f"    Total accepted: {total_accepted}")
        print(f"    Total rejected: {total_rejected}")
        print(f"    Rejection rate: {total_rejected / (num_attackers * updates_per_attacker) * 100:.1f}%")
        print(f"    Unique keys in pending: {len(batcher.pending)}")

        # Each of 10 attackers gets max 20 updates (rate limited)
        # 10 attackers × 20 = 200 total
        # We have 10 unique keys (10 LCTs × 1 org), which is under pending limit (100)
        # So all 200 should be accepted
        self.assertEqual(total_accepted, 200,
                        "10 attackers × 20 rate limit = 200 total accepted")
        self.assertEqual(total_rejected, 300,
                        "10 attackers × 30 over limit = 300 total rejected")
        self.assertEqual(len(batcher.pending), 10,
                        "10 unique keys (LCT:ORG combinations)")

        stats = batcher.get_stats()
        print(f"\n  Statistics:")
        print(f"    Rate limit rejections: {stats['rate_limit_rejections']}")
        print(f"    Pending limit rejections: {stats['pending_limit_rejections']}")

        print(f"\n  ✅ Multiple-attacker scenario handled")
        print(f"     Rate limits enforced independently per LCT")
        print(f"     Each attacker limited to {batcher.max_updates_per_minute_per_lct} updates/min")

        batcher.stop()

    def test_statistics_tracking(self):
        """Test that rate limit statistics are properly tracked"""
        print("\n=== Test: Statistics Tracking ===")

        batcher = TrustUpdateBatcher(
            db_config=self.db_config,
            flush_interval_seconds=3600,
            max_batch_size=1000,
            max_updates_per_minute_per_lct=15,
            auto_start=False
        )

        # Trigger some rate limit rejections
        lct_id = "lct:batch:test:0000"
        for i in range(30):
            try:
                batcher.record_t3_update(
                    lct_id=lct_id,
                    org_id="org:batch:test",
                    talent_delta=Decimal('0.001')
                )
            except RuntimeError:
                pass  # Expected

        stats = batcher.get_stats()

        print(f"  Statistics:")
        print(f"    Total update attempts: {stats['total_updates_recorded']}")
        print(f"    Rate limit rejections: {stats['rate_limit_rejections']}")
        print(f"    Pending updates: {stats.get('pending_updates', batcher.get_pending_count())}")

        self.assertEqual(stats['total_updates_recorded'], 15,
                        "Should record 15 successful updates")
        self.assertEqual(stats['rate_limit_rejections'], 15,
                        "Should record 15 rejections")

        print(f"  ✅ Rate limit statistics properly tracked")

        batcher.stop()


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
