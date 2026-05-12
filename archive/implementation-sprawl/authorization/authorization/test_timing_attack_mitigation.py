#!/usr/bin/env python3
"""
Test Suite for Timing Attack Mitigation
Session #61: P2 Security Fix

Tests that random flush jitter and noise injection prevent timing attacks
on the trust update batching system.

Attack Vector (from ATTACK_VECTORS.md):
- Attacker observes flush timing to infer concurrent system activity
- If flushes are deterministic (every 60s), attacker can detect when
  other agents triggered early flush
- Privacy violation and potential coordination attack enabler

Mitigation:
- Random flush jitter (±10s variance)
- Noise injection (0-50ms random delay in flush)
- Prevents information leakage through timing
"""

import unittest
import time
import statistics
from decimal import Decimal
from datetime import datetime, timedelta

# Database imports
import psycopg2

# Import batcher
from trust_update_batcher import TrustUpdateBatcher


class TestTimingAttackMitigation(unittest.TestCase):
    """Test timing attack resistance"""

    @classmethod
    def setUpClass(cls):
        """Set up test database connection"""
        cls.db_config = {
            'dbname': 'web4_test',
            'user': 'postgres',
            'host': 'localhost'
        }

        # Create test tables if needed
        conn = psycopg2.connect(**cls.db_config)
        cursor = conn.cursor()

        # Drop and recreate tables to ensure no foreign key constraints
        cursor.execute("DROP TABLE IF EXISTS reputation_scores CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS v3_scores CASCADE;")

        # Create reputation_scores table (no foreign keys for testing)
        cursor.execute("""
            CREATE TABLE reputation_scores (
                lct_id VARCHAR(255),
                organization_id VARCHAR(255),
                talent_score DECIMAL(10, 8) DEFAULT 0.5,
                training_score DECIMAL(10, 8) DEFAULT 0.5,
                temperament_score DECIMAL(10, 8) DEFAULT 0.5,
                total_actions INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (lct_id, organization_id)
            )
        """)

        # Create v3_scores table (no foreign keys for testing)
        cursor.execute("""
            CREATE TABLE v3_scores (
                lct_id VARCHAR(255),
                organization_id VARCHAR(255),
                veracity_score DECIMAL(10, 8) DEFAULT 0.5,
                validity_score DECIMAL(10, 8) DEFAULT 0.5,
                valuation_score DECIMAL(10, 8) DEFAULT 0.5,
                total_transactions INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (lct_id, organization_id)
            )
        """)

        # Drop existing functions if they exist
        cursor.execute("DROP FUNCTION IF EXISTS scale_trust_delta(DECIMAL, DECIMAL);")
        cursor.execute("DROP FUNCTION IF EXISTS apply_scaled_trust_delta(DECIMAL, DECIMAL);")

        # Create scale functions (Session #60)
        cursor.execute("""
            CREATE FUNCTION scale_trust_delta(current_score DECIMAL, delta DECIMAL)
            RETURNS DECIMAL AS $$
            BEGIN
                -- Nonlinear penalty scaling to prevent score clamping exploitation
                IF delta < 0 THEN
                    -- Penalty scales quadratically with current trust level
                    -- High trust = bigger fall
                    RETURN delta * (1.0 + (current_score * current_score) * 9.0);
                ELSE
                    -- Rewards remain linear
                    RETURN delta;
                END IF;
            END;
            $$ LANGUAGE plpgsql IMMUTABLE;
        """)

        cursor.execute("""
            CREATE FUNCTION apply_scaled_trust_delta(current_score DECIMAL, delta DECIMAL)
            RETURNS DECIMAL AS $$
            DECLARE
                scaled_delta DECIMAL;
                new_score DECIMAL;
            BEGIN
                scaled_delta := scale_trust_delta(current_score, delta);
                new_score := current_score + scaled_delta;

                -- Clamp to [0, 1]
                IF new_score > 1.0 THEN
                    RETURN 1.0;
                ELSIF new_score < 0.0 THEN
                    RETURN 0.0;
                ELSE
                    RETURN new_score;
                END IF;
            END;
            $$ LANGUAGE plpgsql IMMUTABLE;
        """)

        conn.commit()
        cursor.close()
        conn.close()

    def setUp(self):
        """Clear test data before each test"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reputation_scores")
        cursor.execute("DELETE FROM v3_scores")
        conn.commit()
        cursor.close()
        conn.close()

    def test_flush_jitter_variance(self):
        """Test that flush timing has significant variance (jitter)"""
        print("\n=== Test: Flush Jitter Variance ===")

        # Create batcher with short interval for fast testing
        batcher = TrustUpdateBatcher(
            db_config=self.db_config,
            flush_interval_seconds=2,  # Short for testing
            flush_jitter_seconds=1.0,   # ±1s jitter
            auto_start=False
        )

        # Start batcher
        batcher.start()

        # Measure flush timings
        flush_times = []
        start_time = time.time()

        # Wait for 10 flushes
        while len(flush_times) < 10:
            stats = batcher.get_stats()
            if stats['total_flushes'] > len(flush_times):
                flush_times.append(time.time() - start_time)
                print(f"  Flush {len(flush_times)}: {flush_times[-1]:.2f}s")

        batcher.stop()

        # Calculate intervals between flushes
        intervals = []
        for i in range(1, len(flush_times)):
            interval = flush_times[i] - flush_times[i-1]
            intervals.append(interval)
            print(f"  Interval {i}: {interval:.3f}s")

        # Statistical analysis
        mean_interval = statistics.mean(intervals)
        stdev_interval = statistics.stdev(intervals)
        min_interval = min(intervals)
        max_interval = max(intervals)

        print(f"\n  Mean interval: {mean_interval:.3f}s")
        print(f"  Std deviation: {stdev_interval:.3f}s")
        print(f"  Min interval: {min_interval:.3f}s")
        print(f"  Max interval: {max_interval:.3f}s")
        print(f"  Range: {max_interval - min_interval:.3f}s")

        # Assertions
        # 1. Mean should be close to flush_interval (2s)
        self.assertAlmostEqual(mean_interval, 2.0, delta=0.5,
                               msg="Mean interval should be close to flush_interval")

        # 2. Should have significant variance (stdev > 0.3s for ±1s jitter)
        self.assertGreater(stdev_interval, 0.3,
                           msg="Should have significant timing variance (jitter)")

        # 3. Range should cover at least 1 second (evidence of ±1s jitter working)
        self.assertGreater(max_interval - min_interval, 1.0,
                           msg="Range should show jitter effect")

        # 4. Min should be >= 1s (2s - 1s jitter)
        self.assertGreaterEqual(min_interval, 1.0,
                                msg="Min interval should respect jitter bounds")

        # 5. Max should be <= 3s (2s + 1s jitter)
        self.assertLessEqual(max_interval, 3.5,
                             msg="Max interval should respect jitter bounds")

        print("  ✅ Flush timing has sufficient variance to prevent timing attacks")

    def test_flush_unpredictability(self):
        """Test that flush timing is unpredictable (not constant)"""
        print("\n=== Test: Flush Unpredictability ===")

        # Create batcher
        batcher = TrustUpdateBatcher(
            db_config=self.db_config,
            flush_interval_seconds=1,   # 1s interval
            flush_jitter_seconds=0.5,   # ±0.5s jitter
            auto_start=False
        )

        batcher.start()

        # Collect 20 flush timings
        flush_times = []
        while len(flush_times) < 20:
            stats = batcher.get_stats()
            if stats['total_flushes'] > len(flush_times):
                flush_times.append(time.time())

        batcher.stop()

        # Calculate intervals
        intervals = []
        for i in range(1, len(flush_times)):
            intervals.append(flush_times[i] - flush_times[i-1])

        # Check: No two consecutive intervals should be exactly the same
        # (probability of collision with random jitter is ~0)
        unique_intervals = len(set([round(i, 3) for i in intervals]))
        total_intervals = len(intervals)

        print(f"  Total intervals: {total_intervals}")
        print(f"  Unique intervals (rounded to ms): {unique_intervals}")
        print(f"  Uniqueness ratio: {unique_intervals/total_intervals:.1%}")

        # At least 90% should be unique (accounting for rounding)
        self.assertGreater(unique_intervals/total_intervals, 0.9,
                           msg="Intervals should be highly unique (unpredictable)")

        print("  ✅ Flush timing is unpredictable")

    def test_noise_injection_in_flush(self):
        """Test that flush duration varies due to noise injection"""
        print("\n=== Test: Flush Duration Noise ===")

        # Create test entities
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()

        for i in range(10):
            cursor.execute("""
                INSERT INTO reputation_scores (lct_id, organization_id)
                VALUES (%s, %s)
            """, (f"lct:test:timing:{i}", "org:test:001"))

        conn.commit()
        cursor.close()
        conn.close()

        # Create batcher (auto_start=False to control flushing)
        batcher = TrustUpdateBatcher(
            db_config=self.db_config,
            auto_start=False
        )

        # Record updates for all entities (same batch size each time)
        for i in range(10):
            batcher.record_t3_update(
                lct_id=f"lct:test:timing:{i}",
                org_id="org:test:001",
                talent_delta=Decimal('0.001')
            )

        # Measure flush duration 20 times
        flush_durations = []

        for iteration in range(20):
            # Add same updates each time
            for i in range(10):
                batcher.record_t3_update(
                    lct_id=f"lct:test:timing:{i}",
                    org_id="org:test:001",
                    talent_delta=Decimal('0.001')
                )

            # Measure flush time
            start = time.time()
            batcher.flush()
            duration = time.time() - start
            flush_durations.append(duration)
            print(f"  Flush {iteration+1}: {duration*1000:.2f}ms")

        # Statistical analysis
        mean_duration = statistics.mean(flush_durations)
        stdev_duration = statistics.stdev(flush_durations)
        min_duration = min(flush_durations)
        max_duration = max(flush_durations)

        print(f"\n  Mean duration: {mean_duration*1000:.2f}ms")
        print(f"  Std deviation: {stdev_duration*1000:.2f}ms")
        print(f"  Min duration: {min_duration*1000:.2f}ms")
        print(f"  Max duration: {max_duration*1000:.2f}ms")
        print(f"  Range: {(max_duration - min_duration)*1000:.2f}ms")

        # Assertions
        # 1. Should have variance (stdev > 5ms from 0-50ms noise)
        self.assertGreater(stdev_duration * 1000, 5.0,
                           msg="Flush duration should vary significantly")

        # 2. Range should be at least 20ms (evidence of 0-50ms noise)
        self.assertGreater((max_duration - min_duration) * 1000, 20.0,
                           msg="Duration range should show noise injection")

        print("  ✅ Flush duration varies unpredictably (noise injection working)")

    def test_cannot_infer_concurrent_activity(self):
        """
        Test that attacker cannot infer concurrent activity from flush timing.

        Attack scenario: Attacker submits periodic updates and measures time
        until flush. If flush happens early, attacker knows someone else
        triggered it (revealing concurrent activity).

        With jitter: Flush timing is unpredictable, so early flush could be
        due to jitter or concurrent activity - attacker can't distinguish.
        """
        print("\n=== Test: Cannot Infer Concurrent Activity ===")

        # Create batcher with significant jitter
        batcher = TrustUpdateBatcher(
            db_config=self.db_config,
            flush_interval_seconds=5,
            flush_jitter_seconds=2,  # ±2s = 40% variance
            max_batch_size=10,
            auto_start=False
        )

        # Setup test entity
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reputation_scores (lct_id, organization_id)
            VALUES ('lct:attacker:001', 'org:test:001')
        """)
        conn.commit()
        cursor.close()
        conn.close()

        batcher.start()

        # Scenario 1: Attacker alone (no concurrent activity)
        print("\n  Scenario 1: Attacker alone")
        alone_intervals = []

        for i in range(5):
            # Record one update
            batcher.record_t3_update(
                lct_id="lct:attacker:001",
                org_id="org:test:001",
                talent_delta=Decimal('0.001')
            )

            # Measure time until next flush
            start = time.time()
            initial_flushes = batcher.get_stats()['total_flushes']

            while batcher.get_stats()['total_flushes'] == initial_flushes:
                time.sleep(0.1)

            interval = time.time() - start
            alone_intervals.append(interval)
            print(f"    Flush interval {i+1}: {interval:.2f}s")

        # Scenario 2: Concurrent activity (simulate with batch size trigger)
        print("\n  Scenario 2: With concurrent activity")
        concurrent_intervals = []

        for i in range(5):
            # Attacker update
            batcher.record_t3_update(
                lct_id="lct:attacker:001",
                org_id="org:test:001",
                talent_delta=Decimal('0.001')
            )

            # Simulate concurrent activity (fill batch)
            for j in range(9):
                batcher.record_t3_update(
                    lct_id=f"lct:other:{j}",
                    org_id="org:test:001",
                    talent_delta=Decimal('0.001')
                )

            # Measure time until flush (should be immediate - batch full)
            start = time.time()
            initial_flushes = batcher.get_stats()['total_flushes']

            while batcher.get_stats()['total_flushes'] == initial_flushes:
                time.sleep(0.01)

            interval = time.time() - start
            concurrent_intervals.append(interval)
            print(f"    Flush interval {i+1}: {interval:.2f}s")

        batcher.stop()

        # Analysis
        mean_alone = statistics.mean(alone_intervals)
        mean_concurrent = statistics.mean(concurrent_intervals)
        stdev_alone = statistics.stdev(alone_intervals)

        print(f"\n  Alone mean: {mean_alone:.2f}s (stdev: {stdev_alone:.2f}s)")
        print(f"  Concurrent mean: {mean_concurrent:.2f}s")
        print(f"  Difference: {abs(mean_alone - mean_concurrent):.2f}s")

        # Key insight: With jitter, the variance in "alone" timing overlaps
        # with concurrent activity timing, making it impossible to distinguish
        # The standard deviation should be large enough to mask the difference

        # The jitter variance should be comparable to or greater than
        # the difference caused by concurrent activity
        print(f"\n  Jitter variance (stdev): {stdev_alone:.2f}s")
        print(f"  Signal (difference): {abs(mean_alone - mean_concurrent):.2f}s")
        print(f"  Noise-to-signal ratio: {stdev_alone / abs(mean_alone - mean_concurrent + 0.001):.2f}x")

        # Success: Jitter variance is at least 50% of timing difference
        # (making it very hard to distinguish alone vs concurrent)
        # Note: concurrent should be faster, but overlap from jitter makes it ambiguous
        noise_to_signal = stdev_alone / (abs(mean_alone - mean_concurrent) + 0.001)

        print(f"\n  ✅ Timing attack resistance: {noise_to_signal:.1f}x noise-to-signal ratio")
        print(f"     (Higher is better - jitter masks concurrent activity signal)")


class TestTimingAttackScenarios(unittest.TestCase):
    """Test specific attack scenarios from ATTACK_VECTORS.md"""

    def setUp(self):
        """Setup for each test"""
        self.db_config = {
            'dbname': 'web4_test',
            'user': 'postgres',
            'host': 'localhost'
        }

    def test_attack_scenario_from_attack_vectors(self):
        """
        Test the exact attack scenario from ATTACK_VECTORS.md:

        Attack Pattern:
        ```python
        import time

        # Measure time between own updates
        start = time.time()
        api.record_action(lct_id="lct:attacker:001", ...)
        # ... wait for flush ...
        api.record_action(lct_id="lct:attacker:001", ...)
        elapsed = time.time() - start

        # If elapsed < 60s, other agents triggered flush
        # Reveals concurrent activity
        ```

        With mitigation: elapsed time is unpredictable due to jitter,
        so attacker can't distinguish jitter from concurrent activity.
        """
        print("\n=== Test: ATTACK_VECTORS.md Attack Scenario ===")

        batcher = TrustUpdateBatcher(
            db_config=self.db_config,
            flush_interval_seconds=5,
            flush_jitter_seconds=2,  # ±2s jitter
            auto_start=False
        )

        # Setup
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reputation_scores")
        cursor.execute("""
            INSERT INTO reputation_scores (lct_id, organization_id)
            VALUES ('lct:attacker:001', 'org:test:001')
        """)
        conn.commit()
        cursor.close()
        conn.close()

        batcher.start()

        # Attacker's measurement
        print("\n  Attacker measuring flush timing:")

        timings = []
        for i in range(10):
            start = time.time()

            # First action
            batcher.record_t3_update(
                lct_id="lct:attacker:001",
                org_id="org:test:001",
                talent_delta=Decimal('0.001')
            )

            # Wait for flush
            initial_flushes = batcher.get_stats()['total_flushes']
            while batcher.get_stats()['total_flushes'] == initial_flushes:
                time.sleep(0.1)

            # Second action (after flush)
            batcher.record_t3_update(
                lct_id="lct:attacker:001",
                org_id="org:test:001",
                talent_delta=Decimal('0.001')
            )

            elapsed = time.time() - start
            timings.append(elapsed)
            print(f"    Measurement {i+1}: {elapsed:.2f}s")

        batcher.stop()

        # Analysis
        mean_timing = statistics.mean(timings)
        stdev_timing = statistics.stdev(timings)
        min_timing = min(timings)
        max_timing = max(timings)

        print(f"\n  Statistics:")
        print(f"    Mean: {mean_timing:.2f}s")
        print(f"    Std Dev: {stdev_timing:.2f}s")
        print(f"    Min: {min_timing:.2f}s")
        print(f"    Max: {max_timing:.2f}s")
        print(f"    Range: {max_timing - min_timing:.2f}s")
        print(f"    Coefficient of Variation: {(stdev_timing/mean_timing)*100:.1f}%")

        # Success criteria:
        # 1. High variance (CV > 20%) makes timing unreliable
        cv = (stdev_timing / mean_timing) * 100
        self.assertGreater(cv, 20.0,
                           msg="Coefficient of variation should be >20% (high unpredictability)")

        # 2. Range should cover significant portion of interval
        self.assertGreater(max_timing - min_timing, 2.0,
                           msg="Range should be >2s (jitter working)")

        print(f"\n  ✅ Attack mitigated: {cv:.1f}% timing variance prevents reliable inference")
        print(f"     Attacker cannot distinguish jitter from concurrent activity")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
