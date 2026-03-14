#!/usr/bin/env python3
"""
Tests for Coherence Regulation (Cascade Prevention)

Tests regulation mechanisms that prevent coherence death spirals:
1. Temporal decay of CI penalties
2. Soft bounds preventing total lock-out
3. Cascade detection and recovery
4. Grace periods for first coherence drop
5. Integrated regulation manager
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from coherence_regulation import (
    CoherenceRegulationConfig, calculate_decay_factor, apply_temporal_decay,
    apply_soft_bounds, adjusted_atp_cost_regulated,
    detect_coherence_cascade, apply_cascade_recovery,
    check_grace_period, apply_grace_period_floor,
    CoherenceRegulationManager, GracePeriodStatus, CoherenceCascadeDetection
)

from mrh_rdf_implementation import (
    GroundingEdge, GroundingContext, LocationContext,
    CapabilitiesContext, SessionContext, ResourceState
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def config():
    """Default regulation configuration"""
    return CoherenceRegulationConfig()


@pytest.fixture
def strict_config():
    """Strict regulation configuration"""
    return CoherenceRegulationConfig(
        decay_half_life_hours=12.0,  # Slower decay
        min_effective_ci=0.1,  # Lower floor
        max_atp_multiplier=8.0,  # Higher max cost
        cascade_ci_threshold=0.3,  # Stricter cascade threshold
        grace_period_duration=timedelta(hours=1)  # Shorter grace
    )


@pytest.fixture
def lenient_config():
    """Lenient regulation configuration"""
    return CoherenceRegulationConfig(
        decay_half_life_hours=3.0,  # Faster decay
        min_effective_ci=0.4,  # Higher floor
        max_atp_multiplier=3.0,  # Lower max cost
        cascade_ci_threshold=0.5,  # Lenient cascade threshold
        grace_period_duration=timedelta(hours=4)  # Longer grace
    )


def create_grounding(
    location_value: str,
    timestamp: datetime,
    ttl: timedelta = timedelta(minutes=15)
) -> GroundingEdge:
    """Helper to create grounding edge"""
    context = GroundingContext(
        location=LocationContext("physical", location_value, "city", True),
        capabilities=CapabilitiesContext(["text"], "edge-device", ResourceState(0.5, 0.5, 0.5)),
        session=SessionContext(timestamp.isoformat(), "pattern", ""),
        active_contexts=[]
    )

    return GroundingEdge(
        source="lct:test-entity",
        target=context,
        timestamp=timestamp.isoformat(),
        ttl=ttl,
        signature="test-sig"
    )


# ============================================================================
# Test Temporal Decay
# ============================================================================

def test_decay_factor_calculation():
    """Test exponential decay factor"""
    # No time elapsed
    assert calculate_decay_factor(timedelta(hours=0), 6.0) == 1.0

    # One half-life
    assert abs(calculate_decay_factor(timedelta(hours=6), 6.0) - 0.5) < 0.01

    # Two half-lives
    assert abs(calculate_decay_factor(timedelta(hours=12), 6.0) - 0.25) < 0.01

    # Three half-lives
    assert abs(calculate_decay_factor(timedelta(hours=18), 6.0) - 0.125) < 0.01


def test_temporal_decay_recent_issue(config):
    """Test decay with recent coherence issue (minimal decay)"""
    recent_time = (datetime.now() - timedelta(minutes=30)).isoformat()
    ci_with_decay = apply_temporal_decay(0.6, recent_time, config)

    # Should be only slightly higher than original (minimal decay)
    assert ci_with_decay > 0.6
    assert ci_with_decay < 0.65


def test_temporal_decay_old_issue(config):
    """Test decay with old coherence issue (significant decay)"""
    old_time = (datetime.now() - timedelta(hours=12)).isoformat()  # 2 half-lives
    ci_with_decay = apply_temporal_decay(0.5, old_time, config)

    # Should be significantly recovered
    assert ci_with_decay > 0.8  # Most of penalty decayed
    assert ci_with_decay <= 1.0


def test_temporal_decay_disabled():
    """Test that decay can be disabled"""
    config = CoherenceRegulationConfig(enable_temporal_decay=False)
    old_time = (datetime.now() - timedelta(hours=12)).isoformat()

    ci_with_decay = apply_temporal_decay(0.5, old_time, config)

    # Should be unchanged
    assert ci_with_decay == 0.5


def test_temporal_decay_high_ci():
    """Test that decay doesn't affect already-high CI"""
    config = CoherenceRegulationConfig()
    old_time = (datetime.now() - timedelta(hours=12)).isoformat()

    ci_with_decay = apply_temporal_decay(0.95, old_time, config)

    # Should be unchanged (already high)
    assert ci_with_decay == 0.95


# ============================================================================
# Test Soft Bounds
# ============================================================================

def test_soft_bounds_normal_ci(config):
    """Test soft bounds with normal CI"""
    bounded = apply_soft_bounds(0.7, config)
    assert bounded == 0.7  # Unchanged


def test_soft_bounds_low_ci(config):
    """Test soft bounds with very low CI"""
    bounded = apply_soft_bounds(0.05, config)
    assert bounded == config.min_effective_ci  # Floored at 0.2


def test_soft_bounds_zero_ci(config):
    """Test soft bounds with zero CI"""
    bounded = apply_soft_bounds(0.0, config)
    assert bounded == config.min_effective_ci  # Floored at 0.2


def test_adjusted_atp_cost_regulated_high_ci(config):
    """Test ATP cost with high CI (no penalty)"""
    cost = adjusted_atp_cost_regulated(100.0, 0.95, config)
    assert cost == 100.0  # No penalty


def test_adjusted_atp_cost_regulated_low_ci(config):
    """Test ATP cost with low CI (with soft floor)"""
    # CI = 0.1 would normally give 100x multiplier
    # But with soft floor at 0.2, should be capped at 5x
    cost = adjusted_atp_cost_regulated(100.0, 0.1, config)

    # With soft floor 0.2: multiplier = 1/(0.2^2) = 25
    # But capped at max_multiplier = 5.0
    assert cost == 500.0  # 100 * 5x cap


def test_adjusted_atp_cost_comparison():
    """Test that regulated cost is lower than unregulated for very low CI"""
    config = CoherenceRegulationConfig()

    # With CI = 0.1:
    # Unregulated: 1/(0.1^2) = 100x → 10,000 (capped at 10x → 1,000)
    # Regulated: soft floor 0.2 → 1/(0.2^2) = 25x → 2,500 (capped at 5x → 500)

    regulated = adjusted_atp_cost_regulated(100.0, 0.1, config)
    assert regulated == 500.0  # Regulated is lower, preventing lock-out


# ============================================================================
# Test Cascade Detection
# ============================================================================

def test_detect_cascade_insufficient_history(config):
    """Test cascade detection with insufficient history"""
    history = [create_grounding("geo:45,-122", datetime.now())]

    detection = detect_coherence_cascade("lct:test", history, config)

    assert not detection.is_cascade
    assert "insufficient history" in detection.recovery_action_recommended.lower()


def test_detect_cascade_all_high_ci():
    """Test cascade detection with all high CI (no cascade)"""
    config = CoherenceRegulationConfig()

    # All high CI values
    ci_history = [0.9, 0.95, 0.92, 0.94, 0.91]

    detection = detect_coherence_cascade("lct:test", ci_history, config)

    assert not detection.is_cascade
    assert detection.consecutive_low_ci == 0


def test_detect_cascade_monotonic_degradation():
    """Test cascade detection with monotonically degrading CI"""
    config = CoherenceRegulationConfig()

    # Monotonically degrading CI values (simulating impossible travel)
    # All 5 values below threshold (0.4) to trigger cascade
    ci_history = [0.38, 0.35, 0.30, 0.25, 0.20]

    detection = detect_coherence_cascade("lct:test", ci_history, config)

    # All CIs below threshold (0.4) and monotonic degradation
    assert detection.is_cascade
    assert detection.consecutive_low_ci == 5
    assert detection.min_ci_in_window == 0.2
    assert "URGENT" in detection.recovery_action_recommended


def test_cascade_recovery_boost(config):
    """Test cascade recovery boost application"""
    detection = CoherenceCascadeDetection(
        is_cascade=True,
        consecutive_low_ci=5,
        min_ci_in_window=0.25,
        recovery_action_recommended="URGENT"
    )

    recovered = apply_cascade_recovery(0.3, detection, config)

    # Should boost by config.cascade_recovery_boost (0.3)
    # 0.3 + 0.3 = 0.6, but floor at 0.5
    assert recovered >= 0.5
    assert recovered > 0.3  # Boosted


def test_cascade_recovery_no_cascade(config):
    """Test that recovery not applied when no cascade"""
    detection = CoherenceCascadeDetection(
        is_cascade=False,
        consecutive_low_ci=2,
        min_ci_in_window=0.7,
        recovery_action_recommended="OK"
    )

    recovered = apply_cascade_recovery(0.7, detection, config)

    assert recovered == 0.7  # Unchanged


# ============================================================================
# Test Grace Periods
# ============================================================================

def test_grace_period_no_drop():
    """Test grace period when no CI drop has occurred"""
    config = CoherenceRegulationConfig()
    base_time = datetime.now()

    # All high CI values
    ci_history = [
        (0.95, (base_time + timedelta(minutes=i*15)).isoformat())
        for i in range(3)
    ]

    grace = check_grace_period("lct:test", 0.95, ci_history, config)

    assert not grace.in_grace_period


def test_grace_period_first_drop_active():
    """Test grace period active after first drop (simplified)"""
    config = CoherenceRegulationConfig()

    # For this test, we'll manually construct grace status
    # In reality, check_grace_period would calculate from history
    grace = GracePeriodStatus(
        in_grace_period=True,
        grace_started=datetime.now().isoformat(),
        grace_expires=(datetime.now() + timedelta(hours=2)).isoformat(),
        first_drop_ci=0.7,
        grace_ci_floor=0.5
    )

    # Apply grace floor
    floored_ci = apply_grace_period_floor(0.4, grace)

    assert floored_ci == 0.5  # Floored to grace level


def test_grace_period_disabled():
    """Test grace periods can be disabled"""
    config = CoherenceRegulationConfig(grace_period_first_drop=False)

    history = [create_grounding("geo:45,-122", datetime.now())]

    grace = check_grace_period("lct:test", 0.6, history, config)

    assert not grace.in_grace_period


# ============================================================================
# Test Integrated Regulation Manager
# ============================================================================

def test_regulation_manager_high_ci():
    """Test regulation manager with high CI (minimal regulation)"""
    manager = CoherenceRegulationManager()

    regulated_ci, metadata = manager.regulate_coherence(
        "lct:test",
        0.95  # High CI
    )

    assert regulated_ci == 0.95  # Unchanged
    assert len(metadata['regulations_applied']) == 0  # No regulations needed


def test_regulation_manager_low_ci_with_soft_bounds():
    """Test regulation manager with very low CI (soft bounds applied)"""
    manager = CoherenceRegulationManager()

    regulated_ci, metadata = manager.regulate_coherence(
        "lct:test",
        0.05  # Very low CI
    )

    assert regulated_ci == 0.2  # Soft floor applied
    assert 'soft_bounds' in metadata['regulations_applied']


def test_regulation_manager_with_decay():
    """Test regulation manager with temporal decay"""
    manager = CoherenceRegulationManager()

    # Issue was 12 hours ago (2 half-lives)
    old_issue_time = (datetime.now() - timedelta(hours=12)).isoformat()

    regulated_ci, metadata = manager.regulate_coherence(
        "lct:test",
        0.5,  # Low CI from old issue
        last_issue_time=old_issue_time
    )

    # Should have decayed significantly
    assert regulated_ci > 0.5
    assert 'temporal_decay' in metadata['regulations_applied']
    assert 'decay_delta' in metadata
    assert metadata['decay_delta'] > 0


def test_regulation_manager_atp_cost():
    """Test ATP cost calculation with regulation"""
    manager = CoherenceRegulationManager()

    # Low CI but regulated
    regulated_ci = 0.2  # Soft floor

    cost = manager.calculate_regulated_atp_cost(100.0, regulated_ci)

    # Should be capped at 5x
    assert cost == 500.0


def test_regulation_manager_different_configs():
    """Test regulation manager with different configs"""
    strict_config = CoherenceRegulationConfig(
        min_effective_ci=0.1,
        max_atp_multiplier=8.0
    )

    lenient_config = CoherenceRegulationConfig(
        min_effective_ci=0.4,
        max_atp_multiplier=3.0
    )

    strict_manager = CoherenceRegulationManager(strict_config)
    lenient_manager = CoherenceRegulationManager(lenient_config)

    # Same low CI
    strict_ci, _ = strict_manager.regulate_coherence("lct:test", 0.05)
    lenient_ci, _ = lenient_manager.regulate_coherence("lct:test", 0.05)

    # Lenient should have higher floor
    assert lenient_ci > strict_ci
    assert lenient_ci == 0.4  # Lenient floor
    assert strict_ci == 0.1  # Strict floor

    # Lenient should have lower max cost
    strict_cost = strict_manager.calculate_regulated_atp_cost(100.0, strict_ci)
    lenient_cost = lenient_manager.calculate_regulated_atp_cost(100.0, lenient_ci)

    assert lenient_cost < strict_cost


def test_regulation_metadata_tracking():
    """Test that regulation metadata is tracked correctly"""
    manager = CoherenceRegulationManager()

    regulated_ci, metadata = manager.regulate_coherence(
        "lct:test",
        0.1
    )

    # Check metadata structure
    assert 'raw_ci' in metadata
    assert 'regulations_applied' in metadata
    assert 'final_ci' in metadata

    assert metadata['raw_ci'] == 0.1
    assert metadata['final_ci'] == regulated_ci


def test_cascade_prevention_integration():
    """Integration test: Verify cascade cannot occur with regulation"""
    manager = CoherenceRegulationManager()

    # Simulate cascade scenario: CI drops to 0.05
    # Without regulation: 0.05 → 400x ATP cost → lock-out
    # With regulation: 0.05 → soft floor 0.2 → max 5x cost → recoverable

    regulated_ci, metadata = manager.regulate_coherence("lct:test", 0.05)
    cost = manager.calculate_regulated_atp_cost(100.0, regulated_ci)

    # Verify cascade prevented
    assert regulated_ci >= 0.2  # Soft floor prevents complete failure
    assert cost <= 500.0  # Cost capped, still expensive but not lock-out
    assert cost < 1000.0  # Much lower than unregulated (would be 10x cap = 1000)


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    # Run with: python3 test_coherence_regulation.py
    pytest.main([__file__, "-v", "--tb=short"])
