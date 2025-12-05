"""
ATP Demurrage Tests
====================

Test suite for ATP demurrage and anti-hoarding mechanics.

Author: Legion Autonomous Session (2025-12-05)
"""

import unittest
from datetime import datetime, timedelta, timezone
import time

from atp_demurrage import (
    DemurrageEngine, DemurrageConfig, DemurrageScheduler,
    ATPHolding, DemurrageRate
)


class TestATPHolding(unittest.TestCase):
    """Test ATP holding calculations"""

    def test_age_calculation(self):
        """Test holding age calculation"""
        acquired = datetime.now(timezone.utc) - timedelta(days=10)
        holding = ATPHolding(
            entity_lct="lct:test:001",
            amount=1000,
            acquired_at=acquired,
            last_decay_calculated=acquired
        )

        age = holding.age_days()
        self.assertAlmostEqual(age, 10.0, delta=0.1)

    def test_time_since_decay(self):
        """Test time since last decay calculation"""
        acquired = datetime.now(timezone.utc) - timedelta(days=10)
        last_decay = datetime.now(timezone.utc) - timedelta(days=3)

        holding = ATPHolding(
            entity_lct="lct:test:001",
            amount=1000,
            acquired_at=acquired,
            last_decay_calculated=last_decay
        )

        time_since = holding.time_since_decay()
        self.assertAlmostEqual(time_since, 3.0, delta=0.1)


class TestDemurrageConfig(unittest.TestCase):
    """Test demurrage configuration"""

    def test_default_config(self):
        """Test default configuration values"""
        config = DemurrageConfig(society_id="web4:test")

        self.assertEqual(config.society_id, "web4:test")
        self.assertEqual(config.base_rate, 0.05)  # 5% per month
        self.assertEqual(config.grace_period_days, 7)
        self.assertEqual(config.min_velocity_per_month, 0.5)

    def test_custom_config(self):
        """Test custom configuration"""
        config = DemurrageConfig(
            society_id="web4:custom",
            base_rate=0.10,  # 10% per month
            grace_period_days=14,
            min_velocity_per_month=0.75
        )

        self.assertEqual(config.base_rate, 0.10)
        self.assertEqual(config.grace_period_days, 14)
        self.assertEqual(config.min_velocity_per_month, 0.75)


class TestDemurrageEngine(unittest.TestCase):
    """Test demurrage engine"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = DemurrageConfig(
            society_id="web4:test",
            base_rate=0.05,  # 5% per month
            grace_period_days=7,
            decay_calculation_interval_hours=24
        )
        self.engine = DemurrageEngine(self.config)
        self.entity_lct = "lct:test:entity:001"

    def test_add_holding(self):
        """Test adding ATP holding"""
        holding = self.engine.add_holding(
            entity_lct=self.entity_lct,
            amount=1000
        )

        self.assertEqual(holding.entity_lct, self.entity_lct)
        self.assertEqual(holding.amount, 1000)
        self.assertIsNotNone(holding.acquired_at)

    def test_no_decay_during_grace_period(self):
        """Test minimal decay during grace period"""
        # Add holding just acquired
        holding = self.engine.add_holding(
            entity_lct=self.entity_lct,
            amount=1000,
            acquired_at=datetime.now(timezone.utc) - timedelta(days=3)
        )

        # Calculate decay after 24 hours (within grace period)
        now = datetime.now(timezone.utc) - timedelta(days=2)
        decayed, remaining, rate = self.engine.calculate_decay(holding, now)

        # Should have minimal decay (grace rate = 10% of base rate)
        # Base: 5% per month = 0.167% per day
        # Grace: 0.0167% per day
        # After 1 day: ~0.0167% decay
        self.assertLess(decayed, 2)  # Less than 2 ATP decayed
        self.assertGreater(remaining, 998)  # Most ATP remains

    def test_decay_after_grace_period(self):
        """Test normal decay after grace period"""
        # Add holding acquired 30 days ago
        acquired = datetime.now(timezone.utc) - timedelta(days=30)
        holding = self.engine.add_holding(
            entity_lct=self.entity_lct,
            amount=1000,
            acquired_at=acquired
        )

        # Calculate decay after 10 more days
        now = datetime.now(timezone.utc) - timedelta(days=20)
        decayed, remaining, rate = self.engine.calculate_decay(holding, now)

        # Should have normal decay (5% per month = 0.167% per day)
        # After 10 days: ~1.67% decay
        self.assertGreater(decayed, 10)  # At least 10 ATP decayed
        self.assertLess(remaining, 995)  # Less than 995 ATP remains

    def test_apply_decay_single_entity(self):
        """Test applying decay to single entity"""
        # Add multiple holdings
        self.engine.add_holding(
            entity_lct=self.entity_lct,
            amount=1000,
            acquired_at=datetime.now(timezone.utc) - timedelta(days=30)
        )

        self.engine.add_holding(
            entity_lct=self.entity_lct,
            amount=500,
            acquired_at=datetime.now(timezone.utc) - timedelta(days=15)
        )

        # Apply decay
        now = datetime.now(timezone.utc) + timedelta(days=10)
        decayed, remaining = self.engine.apply_decay(self.entity_lct, now)

        # Should have decayed some ATP
        self.assertGreater(decayed, 0)
        self.assertGreater(remaining, 0)
        self.assertEqual(decayed + remaining, 1500)  # Total unchanged

    def test_apply_global_decay(self):
        """Test global decay across multiple entities"""
        # Add holdings for multiple entities
        entities = [f"lct:test:{i}" for i in range(5)]

        for entity in entities:
            self.engine.add_holding(
                entity_lct=entity,
                amount=1000,
                acquired_at=datetime.now(timezone.utc) - timedelta(days=30)
            )

        # Apply global decay
        now = datetime.now(timezone.utc) + timedelta(days=10)
        results = self.engine.apply_global_decay(now)

        # Should have results for all entities
        self.assertEqual(len(results), 5)

        # All should have some decay
        for entity in entities:
            decayed, remaining = results[entity]
            self.assertGreater(decayed, 0)

    def test_max_holding_period(self):
        """Test max holding period enforcement"""
        # Configure with short max holding period
        config = DemurrageConfig(
            society_id="web4:test",
            max_holding_days=30
        )
        engine = DemurrageEngine(config)

        # Add holding acquired 40 days ago
        holding = engine.add_holding(
            entity_lct=self.entity_lct,
            amount=1000,
            acquired_at=datetime.now(timezone.utc) - timedelta(days=40)
        )

        # Calculate decay now
        now = datetime.now(timezone.utc)
        decayed, remaining, rate = engine.calculate_decay(holding, now)

        # Should force complete conversion to ADP
        self.assertEqual(decayed, 1000)
        self.assertEqual(remaining, 0)

    def test_get_total_holdings(self):
        """Test getting total holdings"""
        # Add multiple holdings
        self.engine.add_holding(entity_lct=self.entity_lct, amount=1000)
        self.engine.add_holding(entity_lct=self.entity_lct, amount=500)
        self.engine.add_holding(entity_lct=self.entity_lct, amount=250)

        total = self.engine.get_total_holdings(self.entity_lct)
        self.assertEqual(total, 1750)

    def test_remove_fully_decayed_holdings(self):
        """Test removal of fully decayed holdings"""
        # Add holding that will fully decay
        config = DemurrageConfig(
            society_id="web4:test",
            max_holding_days=10
        )
        engine = DemurrageEngine(config)

        engine.add_holding(
            entity_lct=self.entity_lct,
            amount=100,
            acquired_at=datetime.now(timezone.utc) - timedelta(days=20)
        )

        # Should have 1 holding
        self.assertEqual(len(engine.holdings[self.entity_lct]), 1)

        # Apply decay (will fully decay)
        now = datetime.now(timezone.utc)
        decayed, remaining = engine.apply_decay(self.entity_lct, now)

        # Holding should be removed
        self.assertEqual(len(engine.holdings[self.entity_lct]), 0)
        self.assertEqual(remaining, 0)


class TestDemurrageScheduler(unittest.TestCase):
    """Test demurrage scheduler"""

    def setUp(self):
        """Set up test fixtures"""
        config = DemurrageConfig(
            society_id="web4:test",
            decay_calculation_interval_hours=24
        )
        engine = DemurrageEngine(config)
        self.scheduler = DemurrageScheduler(engine)

    def test_should_run_check(self):
        """Test scheduler run check"""
        # Just initialized, shouldn't run yet
        now = datetime.now(timezone.utc) + timedelta(hours=1)
        should_run = self.scheduler.should_run(now)
        self.assertFalse(should_run)

        # After 24+ hours, should run
        now = datetime.now(timezone.utc) + timedelta(hours=25)
        should_run = self.scheduler.should_run(now)
        self.assertTrue(should_run)

    def test_run_decay_cycle(self):
        """Test running decay cycle"""
        # Add some holdings
        self.scheduler.engine.add_holding(
            entity_lct="lct:test:001",
            amount=1000,
            acquired_at=datetime.now(timezone.utc) - timedelta(days=30)
        )

        # Run decay cycle
        now = datetime.now(timezone.utc) + timedelta(days=10)
        results = self.scheduler.run_decay_cycle(now)

        # Should have results
        self.assertIn("lct:test:001", results)

        # Last run should be updated
        self.assertEqual(self.scheduler.last_run, now)


class TestDemurrageRates(unittest.TestCase):
    """Test different demurrage rate presets"""

    def test_rate_presets(self):
        """Test demurrage rate enum values"""
        self.assertEqual(DemurrageRate.NONE.value, 0.0)
        self.assertEqual(DemurrageRate.LOW.value, 0.01)
        self.assertEqual(DemurrageRate.MODERATE.value, 0.05)
        self.assertEqual(DemurrageRate.HIGH.value, 0.10)
        self.assertEqual(DemurrageRate.AGGRESSIVE.value, 0.20)

    def test_moderate_rate_decay(self):
        """Test decay with moderate rate over time"""
        config = DemurrageConfig(
            society_id="web4:test",
            base_rate=DemurrageRate.MODERATE.value  # 5% per month
        )
        engine = DemurrageEngine(config)

        # Add holding
        holding = engine.add_holding(
            entity_lct="lct:test:001",
            amount=1000,
            acquired_at=datetime.now(timezone.utc) - timedelta(days=30)
        )

        # Calculate decay after 30 days (1 month)
        now = datetime.now(timezone.utc)
        decayed, remaining, rate = engine.calculate_decay(holding, now)

        # After 1 month at 5% rate, should have ~5% decay
        # Using exponential decay: (1 - 0.05/30)^30 ≈ 0.95
        expected_remaining = int(1000 * 0.95)
        self.assertAlmostEqual(remaining, expected_remaining, delta=10)


if __name__ == '__main__':
    unittest.main()
