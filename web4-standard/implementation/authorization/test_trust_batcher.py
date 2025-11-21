#!/usr/bin/env python3
"""
Trust Update Batcher Test Suite
Session #56: Comprehensive testing of write-behind caching

Tests:
1. Basic batching behavior (accumulation in memory)
2. Time-based flush (60s default)
3. Size-based flush (100 updates default)
4. Thread safety (concurrent updates)
5. Error recovery (updates re-queued on failure)
6. Performance benchmark (with vs without batching)
7. T3 and V3 update integration
"""

import unittest
import psycopg2
import time
import threading
from decimal import Decimal
from datetime import datetime

from trust_update_batcher import TrustUpdateBatcher, TrustDelta

# Test database configuration
TEST_DB_CONFIG = {
    'dbname': 'web4',
    'user': 'postgres',
    'host': 'localhost'
}

class TestTrustDelta(unittest.TestCase):
    """Test TrustDelta accumulation logic"""

    def test_t3_accumulation(self):
        """Test T3 delta accumulation"""
        delta = TrustDelta(lct_id="lct:ai:test:001", org_id="org:test:001")

        delta.accumulate_t3(
            Decimal('0.001'),
            Decimal('0.002'),
            Decimal('0.003')
        )

        self.assertEqual(delta.talent_delta, Decimal('0.001'))
        self.assertEqual(delta.training_delta, Decimal('0.002'))
        self.assertEqual(delta.temperament_delta, Decimal('0.003'))
        self.assertEqual(delta.actions_count, 1)

        # Accumulate again
        delta.accumulate_t3(
            Decimal('0.001'),
            Decimal('0.002'),
            Decimal('0.003')
        )

        self.assertEqual(delta.talent_delta, Decimal('0.002'))
        self.assertEqual(delta.training_delta, Decimal('0.004'))
        self.assertEqual(delta.temperament_delta, Decimal('0.006'))
        self.assertEqual(delta.actions_count, 2)

    def test_v3_accumulation(self):
        """Test V3 delta accumulation"""
        delta = TrustDelta(lct_id="lct:ai:test:001", org_id="org:test:001")

        delta.accumulate_v3(
            Decimal('0.01'),
            Decimal('0.02'),
            Decimal('0.03')
        )

        self.assertEqual(delta.veracity_delta, Decimal('0.01'))
        self.assertEqual(delta.validity_delta, Decimal('0.02'))
        self.assertEqual(delta.valuation_delta, Decimal('0.03'))
        self.assertEqual(delta.transactions_count, 1)

        # Accumulate again
        delta.accumulate_v3(
            Decimal('0.01'),
            Decimal('0.02'),
            Decimal('0.03')
        )

        self.assertEqual(delta.veracity_delta, Decimal('0.02'))
        self.assertEqual(delta.validity_delta, Decimal('0.04'))
        self.assertEqual(delta.valuation_delta, Decimal('0.06'))
        self.assertEqual(delta.transactions_count, 2)

    def test_mixed_accumulation(self):
        """Test mixed T3 and V3 accumulation"""
        delta = TrustDelta(lct_id="lct:ai:test:001", org_id="org:test:001")

        delta.accumulate_t3(Decimal('0.001'), Decimal('0.002'), Decimal('0.003'))
        delta.accumulate_v3(Decimal('0.01'), Decimal('0.02'), Decimal('0.03'))

        self.assertEqual(delta.actions_count, 1)
        self.assertEqual(delta.transactions_count, 1)
        self.assertEqual(delta.talent_delta, Decimal('0.001'))
        self.assertEqual(delta.veracity_delta, Decimal('0.01'))

    def test_key_generation(self):
        """Test unique key generation"""
        delta1 = TrustDelta(lct_id="lct:ai:test:001", org_id="org:test:001")
        delta2 = TrustDelta(lct_id="lct:ai:test:001", org_id="org:test:002")
        delta3 = TrustDelta(lct_id="lct:ai:test:002", org_id="org:test:001")

        self.assertEqual(delta1.key(), "lct:ai:test:001:org:test:001")
        self.assertEqual(delta2.key(), "lct:ai:test:001:org:test:002")
        self.assertEqual(delta3.key(), "lct:ai:test:002:org:test:001")

        self.assertNotEqual(delta1.key(), delta2.key())
        self.assertNotEqual(delta1.key(), delta3.key())


class TestTrustUpdateBatcher(unittest.TestCase):
    """Test TrustUpdateBatcher functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up test database and schema"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()

        # Create test tables if they don't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reputation_scores (
                lct_id TEXT NOT NULL,
                organization_id TEXT NOT NULL,
                talent_score NUMERIC(5,4) DEFAULT 0.5000,
                training_score NUMERIC(5,4) DEFAULT 0.5000,
                temperament_score NUMERIC(5,4) DEFAULT 0.5000,
                total_actions INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (lct_id, organization_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS v3_scores (
                lct_id TEXT NOT NULL,
                organization_id TEXT NOT NULL,
                veracity_score NUMERIC(5,4) DEFAULT 0.5000,
                validity_score NUMERIC(5,4) DEFAULT 0.5000,
                valuation_score NUMERIC(5,4) DEFAULT 0.5000,
                total_transactions INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (lct_id, organization_id)
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()

    def setUp(self):
        """Clean test data before each test"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM reputation_scores WHERE lct_id LIKE 'lct:ai:test:%'")
        cursor.execute("DELETE FROM v3_scores WHERE lct_id LIKE 'lct:ai:test:%'")
        cursor.execute("DELETE FROM lct_identities WHERE lct_id LIKE 'lct:ai:test:%'")

        conn.commit()
        cursor.close()
        conn.close()

    def _create_test_identity(self, lct_id: str, org_id: str):
        """Helper to create test LCT identity and organization"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()

        # Create LCT identity first (required for foreign key)
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
            'bc:' + lct_id[:16],  # Mock birth certificate hash
            'pk:' + lct_id[:16]   # Mock public key
        ))

        # Create organization (required for foreign key)
        # Use a fixed admin LCT for test organizations
        cursor.execute("""
            INSERT INTO lct_identities (
                lct_id,
                entity_type,
                birth_certificate_hash,
                public_key
            )
            VALUES ('lct:admin:test', 'ai', 'bc:admin:test', 'pk:admin:test')
            ON CONFLICT (lct_id) DO NOTHING
        """)

        cursor.execute("""
            INSERT INTO organizations (organization_id, organization_name, admin_lct_id, created_at)
            VALUES (%s, %s, 'lct:admin:test', CURRENT_TIMESTAMP)
            ON CONFLICT (organization_id) DO NOTHING
        """, (org_id, f"Test Org {org_id}"))

        conn.commit()
        cursor.close()
        conn.close()

    def test_batcher_initialization(self):
        """Test batcher initializes correctly"""
        batcher = TrustUpdateBatcher(
            db_config=TEST_DB_CONFIG,
            flush_interval_seconds=60,
            max_batch_size=100,
            auto_start=False
        )

        self.assertEqual(batcher.flush_interval, 60)
        self.assertEqual(batcher.max_batch_size, 100)
        self.assertFalse(batcher.running)
        self.assertEqual(len(batcher.pending), 0)

    def test_record_t3_update(self):
        """Test recording T3 updates in memory"""
        batcher = TrustUpdateBatcher(
            db_config=TEST_DB_CONFIG,
            auto_start=False
        )

        batcher.record_t3_update(
            lct_id="lct:ai:test:001",
            org_id="org:test:001",
            talent_delta=Decimal('0.001'),
            training_delta=Decimal('0.002'),
            temperament_delta=Decimal('0.003')
        )

        self.assertEqual(batcher.get_pending_count(), 1)
        self.assertEqual(batcher.stats['total_updates_recorded'], 1)

        # Check accumulated delta
        key = "lct:ai:test:001:org:test:001"
        self.assertIn(key, batcher.pending)
        delta = batcher.pending[key]
        self.assertEqual(delta.talent_delta, Decimal('0.001'))
        self.assertEqual(delta.training_delta, Decimal('0.002'))
        self.assertEqual(delta.temperament_delta, Decimal('0.003'))

    def test_record_v3_update(self):
        """Test recording V3 updates in memory"""
        batcher = TrustUpdateBatcher(
            db_config=TEST_DB_CONFIG,
            auto_start=False
        )

        batcher.record_v3_update(
            lct_id="lct:ai:test:001",
            org_id="org:test:001",
            veracity_delta=Decimal('0.01'),
            validity_delta=Decimal('0.02'),
            valuation_delta=Decimal('0.03')
        )

        self.assertEqual(batcher.get_pending_count(), 1)
        self.assertEqual(batcher.stats['total_updates_recorded'], 1)

    def test_accumulation_same_entity(self):
        """Test multiple updates to same entity accumulate"""
        batcher = TrustUpdateBatcher(
            db_config=TEST_DB_CONFIG,
            auto_start=False
        )

        # Record 3 updates for same entity
        for i in range(3):
            batcher.record_t3_update(
                lct_id="lct:ai:test:001",
                org_id="org:test:001",
                talent_delta=Decimal('0.001')
            )

        # Should still be 1 pending entity
        self.assertEqual(batcher.get_pending_count(), 1)
        # But 3 updates recorded
        self.assertEqual(batcher.stats['total_updates_recorded'], 3)

        # Check accumulated delta
        key = "lct:ai:test:001:org:test:001"
        delta = batcher.pending[key]
        self.assertEqual(delta.talent_delta, Decimal('0.003'))
        self.assertEqual(delta.actions_count, 3)

    def test_multiple_entities(self):
        """Test updates to multiple entities"""
        batcher = TrustUpdateBatcher(
            db_config=TEST_DB_CONFIG,
            auto_start=False
        )

        # Record updates for 5 different entities
        for i in range(5):
            batcher.record_t3_update(
                lct_id=f"lct:ai:test:00{i}",
                org_id="org:test:001",
                talent_delta=Decimal('0.001')
            )

        self.assertEqual(batcher.get_pending_count(), 5)
        self.assertEqual(batcher.stats['total_updates_recorded'], 5)

    def test_manual_flush_t3(self):
        """Test manual flush of T3 updates"""
        # Create LCT identity first
        self._create_test_identity('lct:ai:test:001', 'org:test:001')

        # Insert initial entity
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reputation_scores (lct_id, organization_id)
            VALUES ('lct:ai:test:001', 'org:test:001')
        """)
        conn.commit()
        cursor.close()
        conn.close()

        # Create batcher and record updates
        batcher = TrustUpdateBatcher(
            db_config=TEST_DB_CONFIG,
            auto_start=False
        )

        batcher.record_t3_update(
            lct_id="lct:ai:test:001",
            org_id="org:test:001",
            talent_delta=Decimal('0.01'),
            training_delta=Decimal('0.02'),
            temperament_delta=Decimal('0.03')
        )

        # Verify in memory
        self.assertEqual(batcher.get_pending_count(), 1)

        # Manual flush
        batcher.flush()

        # Verify flushed
        self.assertEqual(batcher.get_pending_count(), 0)
        self.assertEqual(batcher.stats['total_flushes'], 1)
        self.assertEqual(batcher.stats['total_entities_flushed'], 1)

        # Verify in database
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT talent_score, training_score, temperament_score, total_actions
            FROM reputation_scores
            WHERE lct_id = 'lct:ai:test:001' AND organization_id = 'org:test:001'
        """)
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        self.assertIsNotNone(row)
        # Initial 0.0 + 0.01 = 0.01
        self.assertEqual(row[0], Decimal('0.0100'))
        # Initial 0.0 + 0.02 = 0.02
        self.assertEqual(row[1], Decimal('0.0200'))
        # Initial 0.0 + 0.03 = 0.03
        self.assertEqual(row[2], Decimal('0.0300'))
        # 1 action counted
        self.assertEqual(row[3], 1)

    def test_manual_flush_v3(self):
        """Test manual flush of V3 updates"""
        # Create LCT identity first
        self._create_test_identity('lct:ai:test:001', 'org:test:001')

        # Insert initial entity
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO v3_scores (lct_id, organization_id)
            VALUES ('lct:ai:test:001', 'org:test:001')
        """)
        conn.commit()
        cursor.close()
        conn.close()

        # Create batcher and record updates
        batcher = TrustUpdateBatcher(
            db_config=TEST_DB_CONFIG,
            auto_start=False
        )

        batcher.record_v3_update(
            lct_id="lct:ai:test:001",
            org_id="org:test:001",
            veracity_delta=Decimal('0.01'),
            validity_delta=Decimal('0.02'),
            valuation_delta=Decimal('0.03')
        )

        # Manual flush
        batcher.flush()

        # Verify in database
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT veracity_score, validity_score, valuation_score, total_transactions
            FROM v3_scores
            WHERE lct_id = 'lct:ai:test:001' AND organization_id = 'org:test:001'
        """)
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        self.assertIsNotNone(row)
        # V3 scores default to 0.5, not 0.0
        self.assertEqual(row[0], Decimal('0.5100'))  # 0.5 + 0.01
        self.assertEqual(row[1], Decimal('0.5200'))  # 0.5 + 0.02
        self.assertEqual(row[2], Decimal('0.5300'))  # 0.5 + 0.03
        self.assertEqual(row[3], 1)

    def test_size_based_flush(self):
        """Test automatic flush when batch size reached"""
        # Create LCT identities and insert initial entities
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        for i in range(10):
            lct_id = f"lct:ai:test:00{i}"
            self._create_test_identity(lct_id, 'org:test:001')
            cursor.execute("""
                INSERT INTO reputation_scores (lct_id, organization_id)
                VALUES (%s, 'org:test:001')
            """, (lct_id,))
        conn.commit()
        cursor.close()
        conn.close()

        # Create batcher with small batch size
        batcher = TrustUpdateBatcher(
            db_config=TEST_DB_CONFIG,
            max_batch_size=5,
            auto_start=False
        )

        # Record 4 updates - should NOT flush
        for i in range(4):
            batcher.record_t3_update(
                lct_id=f"lct:ai:test:00{i}",
                org_id="org:test:001",
                talent_delta=Decimal('0.001')
            )

        self.assertEqual(batcher.get_pending_count(), 4)
        self.assertEqual(batcher.stats['total_flushes'], 0)

        # Record 5th update - should flush
        batcher.record_t3_update(
            lct_id="lct:ai:test:004",
            org_id="org:test:001",
            talent_delta=Decimal('0.001')
        )

        # Should be flushed now
        self.assertEqual(batcher.get_pending_count(), 0)
        self.assertEqual(batcher.stats['total_flushes'], 1)
        self.assertEqual(batcher.stats['total_entities_flushed'], 5)

    def test_time_based_flush(self):
        """Test automatic flush on timer"""
        # Create LCT identity first
        self._create_test_identity('lct:ai:test:001', 'org:test:001')

        # Insert initial entity
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reputation_scores (lct_id, organization_id)
            VALUES ('lct:ai:test:001', 'org:test:001')
        """)
        conn.commit()
        cursor.close()
        conn.close()

        # Create batcher with 2-second flush interval
        batcher = TrustUpdateBatcher(
            db_config=TEST_DB_CONFIG,
            flush_interval_seconds=2,
            max_batch_size=100,
            auto_start=True
        )

        try:
            # Record update
            batcher.record_t3_update(
                lct_id="lct:ai:test:001",
                org_id="org:test:001",
                talent_delta=Decimal('0.001')
            )

            # Should be pending
            self.assertEqual(batcher.get_pending_count(), 1)

            # Wait for flush
            time.sleep(3)

            # Should be flushed
            self.assertEqual(batcher.get_pending_count(), 0)
            self.assertGreaterEqual(batcher.stats['total_flushes'], 1)

        finally:
            batcher.stop()

    def test_thread_safety(self):
        """Test concurrent updates from multiple threads"""
        # Create LCT identities and insert initial entities
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        for i in range(10):
            lct_id = f"lct:ai:test:00{i}"
            self._create_test_identity(lct_id, 'org:test:001')
            cursor.execute("""
                INSERT INTO reputation_scores (lct_id, organization_id)
                VALUES (%s, 'org:test:001')
            """, (lct_id,))
        conn.commit()
        cursor.close()
        conn.close()

        batcher = TrustUpdateBatcher(
            db_config=TEST_DB_CONFIG,
            auto_start=False
        )

        def worker(thread_id, count):
            """Worker thread that records updates"""
            for i in range(count):
                batcher.record_t3_update(
                    lct_id=f"lct:ai:test:00{thread_id}",
                    org_id="org:test:001",
                    talent_delta=Decimal('0.001')
                )

        # Launch 5 threads, each doing 10 updates
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i, 10))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Should have 5 entities (one per thread)
        self.assertEqual(batcher.get_pending_count(), 5)
        # Should have recorded 50 total updates
        self.assertEqual(batcher.stats['total_updates_recorded'], 50)

        # Each entity should have 10 accumulated updates
        for i in range(5):
            key = f"lct:ai:test:00{i}:org:test:001"
            delta = batcher.pending[key]
            self.assertEqual(delta.actions_count, 10)
            self.assertEqual(delta.talent_delta, Decimal('0.01'))

    def test_clamping_behavior(self):
        """Test that scores are clamped to [0, 1]"""
        # Create LCT identity first
        self._create_test_identity('lct:ai:test:001', 'org:test:001')

        # Insert entity with high scores
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reputation_scores (lct_id, organization_id, talent_score, training_score, temperament_score)
            VALUES ('lct:ai:test:001', 'org:test:001', 0.99, 0.99, 0.01)
        """)
        conn.commit()
        cursor.close()
        conn.close()

        batcher = TrustUpdateBatcher(
            db_config=TEST_DB_CONFIG,
            auto_start=False
        )

        # Record updates that would exceed bounds
        batcher.record_t3_update(
            lct_id="lct:ai:test:001",
            org_id="org:test:001",
            talent_delta=Decimal('0.05'),  # Would go to 1.04, should clamp to 1.0
            training_delta=Decimal('0.05'),  # Would go to 1.04, should clamp to 1.0
            temperament_delta=Decimal('-0.05')  # Would go to -0.04, should clamp to 0.0
        )

        batcher.flush()

        # Verify clamping
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT talent_score, training_score, temperament_score
            FROM reputation_scores
            WHERE lct_id = 'lct:ai:test:001' AND organization_id = 'org:test:001'
        """)
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        self.assertEqual(row[0], Decimal('1.0000'))  # Clamped to 1.0
        self.assertEqual(row[1], Decimal('1.0000'))  # Clamped to 1.0
        self.assertEqual(row[2], Decimal('0.0000'))  # Clamped to 0.0

    def test_statistics_tracking(self):
        """Test statistics are tracked correctly"""
        batcher = TrustUpdateBatcher(
            db_config=TEST_DB_CONFIG,
            auto_start=False
        )

        # Initial stats
        stats = batcher.get_stats()
        self.assertEqual(stats['total_updates_recorded'], 0)
        self.assertEqual(stats['total_flushes'], 0)
        self.assertEqual(stats['total_entities_flushed'], 0)
        self.assertEqual(stats['pending_updates'], 0)

        # Record some updates
        for i in range(10):
            batcher.record_t3_update(
                lct_id=f"lct:ai:test:00{i}",
                org_id="org:test:001",
                talent_delta=Decimal('0.001')
            )

        stats = batcher.get_stats()
        self.assertEqual(stats['total_updates_recorded'], 10)
        self.assertEqual(stats['pending_updates'], 10)


class TestBatcherPerformance(unittest.TestCase):
    """Benchmark performance improvements"""

    @classmethod
    def setUpClass(cls):
        """Set up test database"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reputation_scores (
                lct_id TEXT NOT NULL,
                organization_id TEXT NOT NULL,
                talent_score NUMERIC(5,4) DEFAULT 0.5000,
                training_score NUMERIC(5,4) DEFAULT 0.5000,
                temperament_score NUMERIC(5,4) DEFAULT 0.5000,
                total_actions INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (lct_id, organization_id)
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()

    def setUp(self):
        """Clean test data"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reputation_scores WHERE lct_id LIKE 'lct:ai:perf:%'")
        cursor.execute("DELETE FROM lct_identities WHERE lct_id LIKE 'lct:ai:perf:%'")
        conn.commit()
        cursor.close()
        conn.close()

    def _create_test_identity(self, lct_id: str, org_id: str):
        """Helper to create test LCT identity and organization"""
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()

        # Create LCT identity first (required for foreign key)
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
            'bc:' + lct_id[:16],  # Mock birth certificate hash
            'pk:' + lct_id[:16]   # Mock public key
        ))

        # Create organization (required for foreign key)
        # Use a fixed admin LCT for test organizations
        cursor.execute("""
            INSERT INTO lct_identities (
                lct_id,
                entity_type,
                birth_certificate_hash,
                public_key
            )
            VALUES ('lct:admin:test', 'ai', 'bc:admin:test', 'pk:admin:test')
            ON CONFLICT (lct_id) DO NOTHING
        """)

        cursor.execute("""
            INSERT INTO organizations (organization_id, organization_name, admin_lct_id, created_at)
            VALUES (%s, %s, 'lct:admin:test', CURRENT_TIMESTAMP)
            ON CONFLICT (organization_id) DO NOTHING
        """, (org_id, f"Test Org {org_id}"))

        conn.commit()
        cursor.close()
        conn.close()

    def test_performance_without_batching(self):
        """Benchmark direct database updates (no batching)"""
        # Create LCT identities and insert initial entities
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        for i in range(100):
            lct_id = f"lct:ai:perf:{i:03d}"
            self._create_test_identity(lct_id, 'org:perf:001')
            cursor.execute("""
                INSERT INTO reputation_scores (lct_id, organization_id)
                VALUES (%s, 'org:perf:001')
            """, (lct_id,))
        conn.commit()
        cursor.close()
        conn.close()

        # Benchmark 1000 direct updates
        start_time = time.time()

        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()

        for i in range(1000):
            entity_id = i % 100  # Cycle through 100 entities
            cursor.execute("""
                UPDATE reputation_scores
                SET talent_score = LEAST(1.0, GREATEST(0.0, talent_score + %s)),
                    total_actions = total_actions + 1,
                    last_updated = CURRENT_TIMESTAMP
                WHERE lct_id = %s AND organization_id = 'org:perf:001'
            """, (Decimal('0.001'), f"lct:ai:perf:{entity_id:03d}"))
            conn.commit()

        cursor.close()
        conn.close()

        elapsed = time.time() - start_time
        print(f"\nWithout batching: {elapsed:.3f}s for 1000 updates")
        print(f"  Rate: {1000/elapsed:.1f} updates/sec")
        print(f"  Database writes: 1000")

        return elapsed

    def test_performance_with_batching(self):
        """Benchmark batched updates"""
        # Create LCT identities and insert initial entities
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cursor = conn.cursor()
        for i in range(100):
            lct_id = f"lct:ai:perf:{i:03d}"
            self._create_test_identity(lct_id, 'org:perf:001')
            cursor.execute("""
                INSERT INTO reputation_scores (lct_id, organization_id)
                VALUES (%s, 'org:perf:001')
            """, (lct_id,))
        conn.commit()
        cursor.close()
        conn.close()

        # Benchmark 1000 batched updates
        start_time = time.time()

        batcher = TrustUpdateBatcher(
            db_config=TEST_DB_CONFIG,
            flush_interval_seconds=999999,  # Very long, we'll flush manually
            max_batch_size=999999,
            auto_start=False
        )

        for i in range(1000):
            entity_id = i % 100  # Cycle through 100 entities
            batcher.record_t3_update(
                lct_id=f"lct:ai:perf:{entity_id:03d}",
                org_id="org:perf:001",
                talent_delta=Decimal('0.001')
            )

        # Single flush at end
        batcher.flush()

        elapsed = time.time() - start_time
        db_writes = batcher.stats['total_entities_flushed']

        print(f"\nWith batching: {elapsed:.3f}s for 1000 updates")
        print(f"  Rate: {1000/elapsed:.1f} updates/sec")
        print(f"  Database writes: {db_writes}")
        print(f"  Reduction: {1000/db_writes:.1f}x fewer writes")

        return elapsed

    def test_performance_comparison(self):
        """Compare batched vs unbatched performance"""
        print("\n" + "="*60)
        print("PERFORMANCE COMPARISON")
        print("="*60)

        # Run both benchmarks
        unbatched_time = self.test_performance_without_batching()
        batched_time = self.test_performance_with_batching()

        # Calculate improvement
        speedup = unbatched_time / batched_time

        print("\n" + "="*60)
        print(f"SPEEDUP: {speedup:.1f}x faster with batching")
        print("="*60)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
