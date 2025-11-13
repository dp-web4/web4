"""
Unit tests for T3 (Trust Tensor) Tracker

Tests the T3 reputation tracking system that was previously missing
from the Web4 implementation (0% → working implementation).

Tests cover:
- Profile creation and storage
- Transaction recording
- T3 score calculations (talent, training, temperament)
- Composite trust scoring
- Statistics and reporting

Author: Claude (Anthropic AI), autonomous Web4 development
Date: November 12, 2025
"""

import pytest
import tempfile
import json
from pathlib import Path

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from t3_tracker import T3Tracker, T3Profile, TransactionRecord


class TestT3Profile:
    """Test T3Profile data class."""

    def test_profile_creation(self):
        """Test creating a T3 profile."""
        profile = T3Profile(
            agent_id="test-agent-001",
            talent=0.7,
            training=0.5,
            temperament=0.8
        )

        assert profile.agent_id == "test-agent-001"
        assert profile.talent == 0.7
        assert profile.training == 0.5
        assert profile.temperament == 0.8
        assert profile.total_transactions == 0
        assert profile.successful_transactions == 0
        assert profile.created_at != ""

    def test_success_rate_calculation(self):
        """Test success rate calculation for talent."""
        profile = T3Profile(agent_id="test")

        # No transactions
        assert profile.get_success_rate() == 0.5  # Neutral default

        # Add some transactions
        profile.total_transactions = 10
        profile.successful_transactions = 8
        assert profile.get_success_rate() == 0.8

        profile.successful_transactions = 10
        assert profile.get_success_rate() == 1.0

    def test_constraint_adherence_calculation(self):
        """Test constraint adherence for temperament."""
        profile = T3Profile(agent_id="test")

        # No transactions
        assert profile.get_constraint_adherence_rate() == 0.5  # Neutral default

        # Perfect adherence
        profile.total_transactions = 10
        profile.constraint_violations = 0
        assert profile.get_constraint_adherence_rate() == 1.0

        # Some violations
        profile.constraint_violations = 2
        assert profile.get_constraint_adherence_rate() == 0.8

    def test_experience_level_calculation(self):
        """Test experience level calculation for training."""
        profile = T3Profile(agent_id="test")

        # No experience
        assert profile.get_experience_level() == 0.0

        # Growing experience (logarithmic)
        profile.total_transactions = 1
        exp_1 = profile.get_experience_level()
        assert 0.0 < exp_1 < 0.2  # Low experience

        profile.total_transactions = 10
        exp_10 = profile.get_experience_level()
        assert 0.4 < exp_10 < 0.6  # Medium experience

        profile.total_transactions = 100
        exp_100 = profile.get_experience_level()
        assert exp_100 >= 0.95  # High experience

        # Verify logarithmic growth
        assert exp_10 > exp_1
        assert exp_100 > exp_10


class TestTransactionRecord:
    """Test TransactionRecord data class."""

    def test_record_creation(self):
        """Test creating a transaction record."""
        record = TransactionRecord(
            timestamp="2025-11-12T12:00:00Z",
            transaction_type="purchase",
            success=True,
            amount=50.00,
            within_constraints=True,
            quality_score=0.9
        )

        assert record.transaction_type == "purchase"
        assert record.success is True
        assert record.amount == 50.00
        assert record.quality_score == 0.9

    def test_auto_timestamp(self):
        """Test automatic timestamp generation."""
        record = TransactionRecord(
            timestamp="",  # Should auto-generate
            transaction_type="purchase",
            success=True,
            amount=50.00,
            within_constraints=True
        )

        assert record.timestamp != ""
        assert "Z" in record.timestamp  # UTC marker


class TestT3Tracker:
    """Test T3Tracker main class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Use temporary file for each test
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.tracker = T3Tracker(storage_path=self.temp_file.name)

    def teardown_method(self):
        """Clean up after tests."""
        Path(self.temp_file.name).unlink(missing_ok=True)

    def test_tracker_initialization(self):
        """Test tracker initialization."""
        assert self.tracker.storage_path.exists()
        assert len(self.tracker.profiles) == 0

    def test_create_profile(self):
        """Test creating a new T3 profile."""
        profile = self.tracker.create_profile(
            "agent-001",
            initial_talent=0.7,
            initial_training=0.5,
            initial_temperament=0.8
        )

        assert profile.agent_id == "agent-001"
        assert profile.talent == 0.7
        assert profile.training == 0.5
        assert profile.temperament == 0.8

        # Verify it's stored
        assert "agent-001" in self.tracker.profiles

    def test_create_profile_with_defaults(self):
        """Test creating profile with default scores."""
        profile = self.tracker.create_profile("agent-002")

        assert profile.talent == 0.5
        assert profile.training == 0.5
        assert profile.temperament == 0.5

    def test_create_profile_validation(self):
        """Test profile creation validates scores."""
        with pytest.raises(ValueError):
            self.tracker.create_profile("bad-agent", initial_talent=1.5)

        with pytest.raises(ValueError):
            self.tracker.create_profile("bad-agent", initial_training=-0.1)

    def test_get_profile(self):
        """Test retrieving a profile."""
        self.tracker.create_profile("agent-001")

        profile = self.tracker.get_profile("agent-001")
        assert profile is not None
        assert profile.agent_id == "agent-001"

        # Non-existent profile
        profile = self.tracker.get_profile("non-existent")
        assert profile is None

    def test_record_transaction_creates_profile(self):
        """Test recording transaction auto-creates profile."""
        success, msg = self.tracker.record_transaction(
            agent_id="new-agent",
            transaction_type="purchase",
            success=True,
            amount=50.00
        )

        assert success is True
        assert "new-agent" in self.tracker.profiles

        profile = self.tracker.get_profile("new-agent")
        assert profile.total_transactions == 1

    def test_record_successful_transaction(self):
        """Test recording successful transaction updates stats."""
        self.tracker.create_profile("agent-001")

        self.tracker.record_transaction(
            agent_id="agent-001",
            transaction_type="purchase",
            success=True,
            amount=50.00,
            within_constraints=True,
            quality_score=0.9
        )

        profile = self.tracker.get_profile("agent-001")
        assert profile.total_transactions == 1
        assert profile.successful_transactions == 1
        assert profile.constraint_violations == 0
        assert profile.total_value_handled == 50.00

    def test_record_failed_transaction(self):
        """Test recording failed transaction updates stats."""
        self.tracker.create_profile("agent-001")

        self.tracker.record_transaction(
            agent_id="agent-001",
            transaction_type="purchase",
            success=False,
            amount=150.00,
            within_constraints=False,  # Exceeded limit
            quality_score=0.3
        )

        profile = self.tracker.get_profile("agent-001")
        assert profile.total_transactions == 1
        assert profile.successful_transactions == 0
        assert profile.constraint_violations == 1

    def test_t3_score_updates(self):
        """Test T3 scores update based on transactions."""
        profile = self.tracker.create_profile("agent-001", 0.5, 0.0, 0.5)
        initial_training = profile.training

        # Record several successful transactions
        for i in range(10):  # More transactions for meaningful training increase
            self.tracker.record_transaction(
                agent_id="agent-001",
                transaction_type="purchase",
                success=True,
                amount=50.00,
                within_constraints=True,
                quality_score=0.9
            )

        profile = self.tracker.get_profile("agent-001")

        # Talent should increase (high success rate + quality)
        assert profile.talent > 0.5

        # Training should increase (more transactions mean more experience)
        assert profile.training > initial_training

        # Temperament should be high (perfect constraint adherence + consistency)
        assert profile.temperament > 0.5

    def test_talent_calculation(self):
        """Test talent score calculation."""
        self.tracker.create_profile("agent-001")

        # All successful with high quality
        for i in range(10):
            self.tracker.record_transaction(
                agent_id="agent-001",
                transaction_type="purchase",
                success=True,
                within_constraints=True,
                quality_score=0.95
            )

        profile = self.tracker.get_profile("agent-001")
        # Talent = 0.7 * success_rate + 0.3 * avg_quality
        # Should be high (success_rate=1.0, quality=0.95)
        assert profile.talent > 0.9

    def test_training_grows_with_experience(self):
        """Test training score grows with transaction count."""
        self.tracker.create_profile("agent-001")

        # Record transactions and check training growth
        training_scores = []

        for count in [1, 5, 10, 20, 50]:
            while self.tracker.get_profile("agent-001").total_transactions < count:
                self.tracker.record_transaction(
                    agent_id="agent-001",
                    transaction_type="purchase",
                    success=True,
                    within_constraints=True
                )
            training_scores.append(self.tracker.get_profile("agent-001").training)

        # Training should increase
        assert training_scores[1] > training_scores[0]
        assert training_scores[2] > training_scores[1]
        assert training_scores[3] > training_scores[2]
        assert training_scores[4] > training_scores[3]

    def test_temperament_affected_by_violations(self):
        """Test temperament decreases with constraint violations."""
        # Create profile with high temperament (positional args)
        self.tracker.create_profile("agent-001", 0.5, 0.5, 0.9)

        initial_temperament = self.tracker.get_profile("agent-001").temperament

        # Record violations
        for i in range(10):
            self.tracker.record_transaction(
                agent_id="agent-001",
                transaction_type="purchase",
                success=True,
                within_constraints=False,  # Violation!
                quality_score=0.7
            )

        profile = self.tracker.get_profile("agent-001")

        # Temperament should decrease due to violations
        assert profile.temperament < initial_temperament

    def test_get_t3_scores(self):
        """Test getting T3 scores dict."""
        self.tracker.create_profile("agent-001", 0.7, 0.6, 0.8)

        scores = self.tracker.get_t3_scores("agent-001")

        assert scores is not None
        assert scores["talent"] == 0.7
        assert scores["training"] == 0.6
        assert scores["temperament"] == 0.8

        # Non-existent agent
        scores = self.tracker.get_t3_scores("non-existent")
        assert scores is None

    def test_composite_trust_default_weights(self):
        """Test composite trust score with default weights."""
        self.tracker.create_profile(
            "agent-001",
            initial_talent=0.6,
            initial_training=0.8,
            initial_temperament=0.7
        )

        composite = self.tracker.get_composite_trust("agent-001")

        # Default weights: talent=30%, training=50%, temperament=20%
        expected = 0.3 * 0.6 + 0.5 * 0.8 + 0.2 * 0.7
        assert abs(composite - expected) < 0.001

    def test_composite_trust_custom_weights(self):
        """Test composite trust score with custom weights."""
        self.tracker.create_profile(
            "agent-001",
            initial_talent=0.6,
            initial_training=0.8,
            initial_temperament=0.7
        )

        # Custom weights: equal importance
        weights = {"talent": 1/3, "training": 1/3, "temperament": 1/3}
        composite = self.tracker.get_composite_trust("agent-001", weights=weights)

        expected = (0.6 + 0.8 + 0.7) / 3
        assert abs(composite - expected) < 0.001

    def test_composite_trust_validation(self):
        """Test composite trust validates weights sum to 1.0."""
        self.tracker.create_profile("agent-001")

        # Invalid weights (don't sum to 1.0)
        with pytest.raises(ValueError):
            self.tracker.get_composite_trust(
                "agent-001",
                weights={"talent": 0.5, "training": 0.3, "temperament": 0.1}
            )

    def test_get_stats(self):
        """Test getting comprehensive statistics."""
        self.tracker.create_profile("agent-001")

        # Record some transactions
        for i in range(5):
            self.tracker.record_transaction(
                agent_id="agent-001",
                transaction_type="purchase",
                success=True,
                amount=50.00,
                within_constraints=True,
                quality_score=0.9
            )

        stats = self.tracker.get_stats("agent-001")

        assert stats is not None
        assert stats["agent_id"] == "agent-001"
        assert "t3_scores" in stats
        assert "statistics" in stats
        assert "timestamps" in stats

        assert stats["t3_scores"]["composite"] is not None
        assert stats["statistics"]["total_transactions"] == 5
        assert stats["statistics"]["success_rate"] == 1.0

    def test_persistence(self):
        """Test T3 profiles persist to storage."""
        # Create profile and record transaction
        self.tracker.create_profile("agent-001", 0.7, 0.6, 0.8)
        self.tracker.record_transaction(
            "agent-001", "purchase", True, 50.00, True, 0.9
        )

        # Get the updated scores before creating new tracker
        original_profile = self.tracker.get_profile("agent-001")

        # Create new tracker with same storage
        tracker2 = T3Tracker(storage_path=self.temp_file.name)

        # Should load existing profile with same data
        profile = tracker2.get_profile("agent-001")
        assert profile is not None
        assert profile.talent == pytest.approx(original_profile.talent, abs=0.001)
        assert profile.training == pytest.approx(original_profile.training, abs=0.001)
        assert profile.temperament == pytest.approx(original_profile.temperament, abs=0.001)
        assert profile.total_transactions == 1

    def test_transaction_history_limit(self):
        """Test transaction history keeps last 100 transactions."""
        self.tracker.create_profile("agent-001")

        # Record 150 transactions
        for i in range(150):
            self.tracker.record_transaction(
                "agent-001", "purchase", True, 10.00, True
            )

        profile = self.tracker.get_profile("agent-001")

        # Should keep only last 100
        assert len(profile.transaction_history) == 100
        assert profile.total_transactions == 150  # But count all

    def test_list_profiles(self):
        """Test listing all agent profiles."""
        self.tracker.create_profile("agent-001")
        self.tracker.create_profile("agent-002")
        self.tracker.create_profile("agent-003")

        profiles = self.tracker.list_profiles()

        assert len(profiles) == 3
        assert "agent-001" in profiles
        assert "agent-002" in profiles
        assert "agent-003" in profiles

    def test_get_all_stats(self):
        """Test getting stats for all agents."""
        self.tracker.create_profile("agent-001")
        self.tracker.create_profile("agent-002")

        all_stats = self.tracker.get_all_stats()

        assert len(all_stats) == 2
        assert "agent-001" in all_stats
        assert "agent-002" in all_stats
        assert all_stats["agent-001"]["agent_id"] == "agent-001"


class TestT3Integration:
    """Integration tests for T3 tracker."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.tracker = T3Tracker(storage_path=self.temp_file.name)

    def teardown_method(self):
        """Clean up after tests."""
        Path(self.temp_file.name).unlink(missing_ok=True)

    def test_agent_reputation_improves_with_performance(self):
        """Test agent reputation improves with good performance."""
        self.tracker.create_profile("good-agent", 0.5, 0.5, 0.5)

        initial_trust = self.tracker.get_composite_trust("good-agent")

        # Perform well over 20 transactions
        for i in range(20):
            self.tracker.record_transaction(
                "good-agent",
                transaction_type="purchase",
                success=True,
                amount=50.00,
                within_constraints=True,
                quality_score=0.95
            )

        final_trust = self.tracker.get_composite_trust("good-agent")

        # Trust should improve
        assert final_trust > initial_trust
        assert final_trust > 0.7  # Should be significantly higher

    def test_agent_reputation_degrades_with_poor_performance(self):
        """Test agent reputation degrades with poor performance."""
        self.tracker.create_profile("bad-agent", 0.7, 0.7, 0.7)

        initial_trust = self.tracker.get_composite_trust("bad-agent")

        # Perform poorly over 20 transactions
        for i in range(10):
            # Mix of failures and constraint violations
            self.tracker.record_transaction(
                "bad-agent",
                transaction_type="purchase",
                success=False,
                amount=150.00,
                within_constraints=False,
                quality_score=0.3
            )

        final_trust = self.tracker.get_composite_trust("bad-agent")

        # Trust should degrade
        assert final_trust < initial_trust
        assert final_trust < 0.5  # Should be significantly lower

    def test_real_world_scenario(self):
        """Test realistic agent behavior over time."""
        # New agent starts neutral
        self.tracker.create_profile("realistic-agent", 0.5, 0.5, 0.5)

        # Phase 1: Learning (some failures)
        for i in range(10):
            success = i > 3  # First few fail
            self.tracker.record_transaction(
                "realistic-agent",
                "purchase",
                success=success,
                amount=50.00,
                within_constraints=True,
                quality_score=0.7 if success else 0.4
            )

        phase1_trust = self.tracker.get_composite_trust("realistic-agent")

        # Phase 2: Improving (mostly successful)
        for i in range(20):
            success = i < 18  # 90% success rate
            self.tracker.record_transaction(
                "realistic-agent",
                "purchase",
                success=success,
                amount=50.00,
                within_constraints=True,
                quality_score=0.85 if success else 0.5
            )

        phase2_trust = self.tracker.get_composite_trust("realistic-agent")

        # Phase 3: Expert (high quality)
        for i in range(30):
            self.tracker.record_transaction(
                "realistic-agent",
                "purchase",
                success=True,
                amount=50.00,
                within_constraints=True,
                quality_score=0.95
            )

        phase3_trust = self.tracker.get_composite_trust("realistic-agent")

        # Trust should improve through phases
        assert phase2_trust > phase1_trust
        assert phase3_trust > phase2_trust

        # Final trust should be high
        assert phase3_trust > 0.75

        stats = self.tracker.get_stats("realistic-agent")
        assert stats["statistics"]["total_transactions"] == 60


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
