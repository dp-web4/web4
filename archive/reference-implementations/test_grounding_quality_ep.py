#!/usr/bin/env python3
"""
Test Grounding Quality Epistemic Proprioception - Session 107

Tests the grounding quality prediction and validation adjustment system.

Author: Claude (Session 107)
Date: 2025-12-30
"""

import pytest
from datetime import datetime, timedelta
from grounding_quality_ep import (
    GroundingQualityPredictor,
    ValidationAdjuster,
    IdentityGroundingHistory,
    GroundingRiskPattern,
    ValidationStrategy
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def clean_history():
    """High-trust identity with clean grounding history."""
    return IdentityGroundingHistory(
        lct_uri="lct:example.com:alice",
        grounding_count=50,
        avg_ci=0.87,
        min_ci=0.75,
        last_grounding_time=datetime.now() - timedelta(hours=2),
        location_changes_per_hour=0.1,
        capability_changes_per_day=0.0,
        ci_variance=0.02,
        anomaly_count_last_10=0,
        has_impossible_travel_history=False,
        has_capability_spoofing_history=False,
        witness_vouching_rate=0.4
    )


@pytest.fixture
def sparse_history():
    """New identity with limited grounding history."""
    return IdentityGroundingHistory(
        lct_uri="lct:example.com:newuser",
        grounding_count=2,
        avg_ci=0.65,
        min_ci=0.60,
        last_grounding_time=datetime.now() - timedelta(days=3),
        location_changes_per_hour=0.0,
        capability_changes_per_day=0.0,
        ci_variance=0.05,
        anomaly_count_last_10=0,
        has_impossible_travel_history=False,
        has_capability_spoofing_history=False,
        witness_vouching_rate=0.0
    )


@pytest.fixture
def suspicious_history():
    """Identity with history of anomalies."""
    return IdentityGroundingHistory(
        lct_uri="lct:example.com:suspicious",
        grounding_count=20,
        avg_ci=0.45,
        min_ci=0.20,
        last_grounding_time=datetime.now() - timedelta(hours=1),
        location_changes_per_hour=2.5,  # Very high mobility
        capability_changes_per_day=3.0,  # Frequent device changes
        ci_variance=0.15,  # High variance
        anomaly_count_last_10=5,  # Many recent anomalies
        has_impossible_travel_history=True,
        has_capability_spoofing_history=True,
        witness_vouching_rate=0.1
    )


@pytest.fixture
def predictor():
    return GroundingQualityPredictor()


@pytest.fixture
def adjuster():
    return ValidationAdjuster()


# ============================================================================
# Test Quality Prediction
# ============================================================================

def test_clean_history_normal_grounding(predictor, clean_history):
    """Test prediction for clean history with normal grounding."""
    context = {
        "impossible_travel": False,
        "capability_mismatch": False,
        "time_since_last_grounding": timedelta(hours=2),
        "has_witnesses": True
    }

    prediction = predictor.predict_quality(clean_history, context)

    print(f"\nClean history, normal grounding:")
    print(f"  Predicted CI: {prediction.predicted_ci:.3f}")
    print(f"  Risk patterns: {len(prediction.risk_patterns)}")

    # Should predict high quality
    assert prediction.predicted_ci >= 0.8, "Clean history should predict high CI"
    assert len(prediction.risk_patterns) == 0, "Should detect no risk patterns"
    assert prediction.confidence > 0.7, "Should have high confidence"


def test_impossible_travel_detected(predictor, clean_history):
    """Test prediction when impossible travel is detected."""
    context = {
        "impossible_travel": True,
        "capability_mismatch": False,
        "time_since_last_grounding": timedelta(minutes=15),
        "has_witnesses": False
    }

    prediction = predictor.predict_quality(clean_history, context)

    print(f"\nImpossible travel detected:")
    print(f"  Predicted CI: {prediction.predicted_ci:.3f}")
    print(f"  Risk patterns: {[p.value for p in prediction.risk_patterns]}")

    # Should predict low quality
    assert prediction.predicted_ci < 0.6, "Impossible travel should predict low CI"
    assert GroundingRiskPattern.IMPOSSIBLE_TRAVEL in prediction.risk_patterns
    assert prediction.confidence > 0.8, "Should have high confidence in detection"


def test_sparse_history_reduces_confidence(predictor, sparse_history):
    """Test that sparse history reduces prediction confidence."""
    context = {
        "impossible_travel": False,
        "capability_mismatch": False,
        "time_since_last_grounding": timedelta(days=3),
        "has_witnesses": False
    }

    prediction = predictor.predict_quality(sparse_history, context)

    print(f"\nSparse history:")
    print(f"  Predicted CI: {prediction.predicted_ci:.3f}")
    print(f"  Confidence: {prediction.confidence:.3f}")
    print(f"  Risk patterns: {[p.value for p in prediction.risk_patterns]}")

    # Should have reduced confidence
    assert prediction.confidence < 0.7, "Sparse history should reduce confidence"
    assert GroundingRiskPattern.SPARSE_HISTORY in prediction.risk_patterns


def test_suspicious_history_low_prediction(predictor, suspicious_history):
    """Test prediction for identity with suspicious history."""
    context = {
        "impossible_travel": False,
        "capability_mismatch": True,
        "time_since_last_grounding": timedelta(hours=1),
        "has_witnesses": False
    }

    prediction = predictor.predict_quality(suspicious_history, context)

    print(f"\nSuspicious history:")
    print(f"  Predicted CI: {prediction.predicted_ci:.3f}")
    print(f"  Risk patterns: {[p.value for p in prediction.risk_patterns]}")

    # Should predict low quality
    assert prediction.predicted_ci < 0.5, "Suspicious history should predict low CI"
    assert len(prediction.risk_patterns) >= 2, "Should detect multiple risk patterns"


# ============================================================================
# Test Validation Adjustment
# ============================================================================

def test_high_quality_fast_track(predictor, adjuster, clean_history):
    """Test fast-track for high-quality predictions."""
    context = {
        "impossible_travel": False,
        "capability_mismatch": False,
        "time_since_last_grounding": timedelta(hours=2),
        "has_witnesses": True
    }

    prediction = predictor.predict_quality(clean_history, context)
    adjustment = adjuster.adjust_validation(prediction, clean_history)

    print(f"\nHigh quality fast-track:")
    print(f"  Strategy: {adjustment.strategy.value}")
    print(f"  Adjustment applied: {adjustment.adjustment_applied}")

    # Should fast-track
    assert adjustment.strategy == ValidationStrategy.FAST_TRACK
    assert adjustment.adjustment_applied == True
    assert adjustment.expected_ci_improvement == 0.0


def test_impossible_travel_requires_announcement(predictor, adjuster, clean_history):
    """Test that impossible travel triggers announcement requirement."""
    context = {
        "impossible_travel": True,
        "capability_mismatch": False,
        "time_since_last_grounding": timedelta(minutes=15),
        "has_witnesses": False
    }

    prediction = predictor.predict_quality(clean_history, context)
    adjustment = adjuster.adjust_validation(prediction, clean_history)

    print(f"\nImpossible travel adjustment:")
    print(f"  Strategy: {adjustment.strategy.value}")
    print(f"  Requirements: {adjustment.requirements}")
    print(f"  Expected improvement: +{adjustment.expected_ci_improvement:.2f}")

    # Should require announcement
    assert adjustment.strategy == ValidationStrategy.REQUIRE_ANNOUNCEMENT
    assert adjustment.adjustment_applied == True
    assert adjustment.requirements["require_travel_announcement"] == True
    assert adjustment.expected_ci_improvement > 0.15


def test_capability_mismatch_requires_witnesses(predictor, adjuster, sparse_history):
    """Test that capability mismatch triggers witness requirement."""
    context = {
        "impossible_travel": False,
        "capability_mismatch": True,
        "time_since_last_grounding": timedelta(hours=24),
        "has_witnesses": False
    }

    prediction = predictor.predict_quality(sparse_history, context)
    adjustment = adjuster.adjust_validation(prediction, sparse_history)

    print(f"\nCapability mismatch adjustment:")
    print(f"  Strategy: {adjustment.strategy.value}")
    print(f"  Requirements: {adjustment.requirements}")

    # Should require witnesses
    assert adjustment.strategy == ValidationStrategy.REQUIRE_WITNESSES
    assert adjustment.adjustment_applied == True
    assert adjustment.requirements["min_witnesses"] >= 2


def test_sparse_history_increases_spatial_checks(predictor, adjuster, sparse_history):
    """Test that sparse history increases spatial validation."""
    context = {
        "impossible_travel": False,
        "capability_mismatch": False,
        "time_since_last_grounding": timedelta(days=3),
        "has_witnesses": False
    }

    prediction = predictor.predict_quality(sparse_history, context)
    adjustment = adjuster.adjust_validation(prediction, sparse_history)

    print(f"\nSparse history adjustment:")
    print(f"  Strategy: {adjustment.strategy.value}")
    print(f"  Requirements: {adjustment.requirements}")

    # Should increase spatial checks
    assert adjustment.strategy == ValidationStrategy.INCREASE_SPATIAL_CHECKS
    assert adjustment.adjustment_applied == True
    assert adjustment.requirements["spatial_validation"] == "strict"


def test_no_adjustment_for_medium_quality(predictor, adjuster):
    """Test that medium quality with low confidence doesn't trigger adjustment."""
    medium_history = IdentityGroundingHistory(
        lct_uri="lct:example.com:medium",
        grounding_count=10,
        avg_ci=0.70,
        min_ci=0.65,
        last_grounding_time=datetime.now() - timedelta(hours=6),
        location_changes_per_hour=0.2,
        capability_changes_per_day=0.1,
        ci_variance=0.03,
        anomaly_count_last_10=1,
        has_impossible_travel_history=False,
        has_capability_spoofing_history=False,
        witness_vouching_rate=0.3
    )

    context = {
        "impossible_travel": False,
        "capability_mismatch": False,
        "time_since_last_grounding": timedelta(hours=6),
        "has_witnesses": True
    }

    prediction = predictor.predict_quality(medium_history, context)
    adjustment = adjuster.adjust_validation(prediction, medium_history)

    print(f"\nMedium quality (no adjustment):")
    print(f"  Predicted CI: {prediction.predicted_ci:.3f}")
    print(f"  Strategy: {adjustment.strategy.value}")

    # Should not adjust (CI >= 0.6 threshold)
    if prediction.predicted_ci >= 0.6:
        assert adjustment.strategy == ValidationStrategy.STANDARD_VALIDATION
        assert adjustment.adjustment_applied == False


# ============================================================================
# Test Risk Pattern Detection
# ============================================================================

def test_multiple_risk_patterns_detected(predictor, suspicious_history):
    """Test detection of multiple concurrent risk patterns."""
    context = {
        "impossible_travel": True,
        "capability_mismatch": True,
        "time_since_last_grounding": timedelta(days=10),
        "has_witnesses": False
    }

    prediction = predictor.predict_quality(suspicious_history, context)

    print(f"\nMultiple risk patterns:")
    print(f"  Patterns detected: {len(prediction.risk_patterns)}")
    print(f"  Patterns: {[p.value for p in prediction.risk_patterns]}")

    # Should detect multiple patterns
    assert len(prediction.risk_patterns) >= 4, "Should detect multiple risk patterns"
    assert GroundingRiskPattern.IMPOSSIBLE_TRAVEL in prediction.risk_patterns
    assert GroundingRiskPattern.CAPABILITY_MISMATCH in prediction.risk_patterns


def test_prediction_reasoning_quality(predictor, clean_history):
    """Test that prediction reasoning is informative."""
    context = {
        "impossible_travel": True,
        "capability_mismatch": False,
        "time_since_last_grounding": timedelta(minutes=15),
        "has_witnesses": False
    }

    prediction = predictor.predict_quality(clean_history, context)

    print(f"\nPrediction reasoning:")
    print(f"  {prediction.reasoning}")

    # Reasoning should mention key factors
    assert "risk pattern" in prediction.reasoning.lower() or "clean history" in prediction.reasoning.lower()
    assert str(clean_history.grounding_count) in prediction.reasoning
    assert len(prediction.reasoning) > 50, "Reasoning should be substantial"


# ============================================================================
# Integration Tests
# ============================================================================

def test_full_ep_workflow_impossible_travel(predictor, adjuster, clean_history):
    """Test complete EP workflow for impossible travel scenario."""
    context = {
        "impossible_travel": True,
        "capability_mismatch": False,
        "time_since_last_grounding": timedelta(minutes=15),
        "has_witnesses": False
    }

    # 1. Predict quality
    prediction = predictor.predict_quality(clean_history, context)

    # 2. Adjust validation
    adjustment = adjuster.adjust_validation(prediction, clean_history)

    print(f"\nFull EP workflow (impossible travel):")
    print(f"  Predicted CI: {prediction.predicted_ci:.3f}")
    print(f"  Should adjust: {prediction.should_adjust_validation()}")
    print(f"  Strategy: {adjustment.strategy.value}")
    print(f"  Expected improvement: +{adjustment.expected_ci_improvement:.2f}")

    # Validate workflow
    assert prediction.should_adjust_validation() == True
    assert adjustment.adjustment_applied == True
    assert adjustment.strategy == ValidationStrategy.REQUIRE_ANNOUNCEMENT
    assert adjustment.expected_ci_improvement > 0


def test_full_ep_workflow_clean(predictor, adjuster, clean_history):
    """Test complete EP workflow for clean grounding."""
    context = {
        "impossible_travel": False,
        "capability_mismatch": False,
        "time_since_last_grounding": timedelta(hours=2),
        "has_witnesses": True
    }

    # 1. Predict quality
    prediction = predictor.predict_quality(clean_history, context)

    # 2. Adjust validation
    adjustment = adjuster.adjust_validation(prediction, clean_history)

    print(f"\nFull EP workflow (clean):")
    print(f"  Predicted CI: {prediction.predicted_ci:.3f}")
    print(f"  Should adjust: {prediction.should_adjust_validation()}")
    print(f"  Strategy: {adjustment.strategy.value}")

    # Validate workflow
    assert prediction.should_adjust_validation() == False
    # May fast-track, which is also an adjustment
    assert adjustment.strategy in [ValidationStrategy.STANDARD_VALIDATION, ValidationStrategy.FAST_TRACK]


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
