"""
Tests for Relationship Coherence Epistemic Proprioception

Tests the pattern-based prediction system for relationship coherence
degradation detection and proactive verification adjustment.

Created: 2025-12-30
Session: 108 (Legion autonomous research)
"""

import pytest
from datetime import datetime, timedelta
from relationship_coherence_ep import (
    RelationshipCoherencePredictor,
    CoherenceVerificationAdjuster,
    RelationshipHistory,
    InteractionCharacteristics,
    RelationshipCoherencePattern,
    CoherenceOutcome,
    CoherenceRiskPattern,
    TrustTensor,
    StanceVector,
    VerificationStrategy
)


@pytest.fixture
def stable_relationship():
    """Stable, high-trust collaborative relationship."""
    return RelationshipHistory(
        relationship_lct="lct://alice:relationship:bob@mainnet",
        participant_lcts=("lct://alice@mainnet", "lct://bob@mainnet"),
        formed_date="2025-11-01",
        source="crystallized",
        current_trust=TrustTensor(0.85, 0.90, 0.80, 0.88),
        current_stance=StanceVector(0.85, 0.10, 0.03, 0.02),
        current_ci=0.92,
        total_interactions=150,
        recent_interactions=25,
        positive_interactions=140,
        negative_interactions=3,
        repair_events=1,
        avg_response_time=timedelta(minutes=5),
        response_time_variance=0.15,
        avg_interaction_gap=timedelta(hours=6),
        last_interaction=datetime.now() - timedelta(hours=4),
        trust_trajectory="improving",
        stance_stability=0.95,
        ci_history=[0.88, 0.89, 0.91, 0.92]
    )


@pytest.fixture
def declining_relationship():
    """Declining relationship with trust issues."""
    return RelationshipHistory(
        relationship_lct="lct://charlie:relationship:eve@mainnet",
        participant_lcts=("lct://charlie@mainnet", "lct://eve@mainnet"),
        formed_date="2025-12-15",
        source="introduced",
        current_trust=TrustTensor(0.55, 0.48, 0.40, 0.35),
        current_stance=StanceVector(0.30, 0.25, 0.20, 0.25),
        current_ci=0.52,
        total_interactions=25,
        recent_interactions=8,
        positive_interactions=12,
        negative_interactions=8,
        repair_events=2,
        avg_response_time=timedelta(minutes=10),
        response_time_variance=0.45,
        avg_interaction_gap=timedelta(hours=12),
        last_interaction=datetime.now() - timedelta(hours=10),
        trust_trajectory="declining",
        stance_stability=0.45,
        ci_history=[0.70, 0.65, 0.58, 0.52]
    )


@pytest.fixture
def adversarial_relationship():
    """Relationship turning adversarial."""
    return RelationshipHistory(
        relationship_lct="lct://david:relationship:mallory@mainnet",
        participant_lcts=("lct://david@mainnet", "lct://mallory@mainnet"),
        formed_date="2025-12-20",
        source="witnessed",
        current_trust=TrustTensor(0.25, 0.30, 0.20, 0.15),
        current_stance=StanceVector(0.10, 0.20, 0.25, 0.45),
        current_ci=0.35,
        total_interactions=15,
        recent_interactions=5,
        positive_interactions=3,
        negative_interactions=10,
        repair_events=0,
        avg_response_time=timedelta(minutes=15),
        response_time_variance=0.80,
        avg_interaction_gap=timedelta(hours=8),
        last_interaction=datetime.now() - timedelta(hours=6),
        trust_trajectory="declining",
        stance_stability=0.25,
        ci_history=[0.60, 0.50, 0.42, 0.35]
    )


@pytest.fixture
def predictor():
    """Create predictor instance."""
    return RelationshipCoherencePredictor()


@pytest.fixture
def adjuster():
    """Create verification adjuster instance."""
    return CoherenceVerificationAdjuster()


def test_stable_relationship_normal_interaction(predictor, adjuster, stable_relationship):
    """Test prediction for stable relationship with normal interaction."""
    interaction = InteractionCharacteristics(
        interaction_type="request",
        complexity="MEDIUM",
        expected_response_time=timedelta(minutes=5),
        actual_response_time=timedelta(minutes=6),
        claims_made=2,
        commitments_made=1,
        resources_requested=10.0,
        time_since_last=timedelta(hours=4),
        grounding_ci=0.91,
        witness_count=3
    )

    prediction = predictor.predict_coherence(stable_relationship, interaction)

    # Should predict minimal CI change
    assert prediction.predicted_ci_change >= -0.15
    assert prediction.predicted_ci_after >= 0.75
    assert prediction.confidence > 0.0

    # Should not require special verification
    adjustment = adjuster.adjust_verification(prediction, stable_relationship)
    assert adjustment.strategy in [
        VerificationStrategy.STANDARD_VERIFICATION,
        VerificationStrategy.FAST_TRACK
    ]


def test_declining_relationship_risky_interaction(predictor, adjuster, declining_relationship):
    """Test prediction for declining relationship with risky interaction."""
    interaction = InteractionCharacteristics(
        interaction_type="request",
        complexity="HIGH",
        expected_response_time=timedelta(minutes=10),
        actual_response_time=timedelta(minutes=35),  # Anomaly
        claims_made=5,
        commitments_made=3,
        resources_requested=50.0,
        time_since_last=timedelta(hours=10),
        grounding_ci=0.48,  # Low
        witness_count=0,
        timing_anomaly=True,
        behavior_anomaly=True,
        claim_mismatch=True
    )

    prediction = predictor.predict_coherence(declining_relationship, interaction)

    # Should detect multiple risk patterns
    assert len(prediction.risk_patterns) >= 3
    assert prediction.risk_score > 0.5

    # Should predict significant CI degradation
    assert prediction.predicted_ci_change < -0.10

    # Should recommend increased verification
    adjustment = adjuster.adjust_verification(prediction, declining_relationship)
    assert adjustment.strategy != VerificationStrategy.STANDARD_VERIFICATION
    assert adjustment.strategy != VerificationStrategy.FAST_TRACK


def test_adversarial_relationship_defer(predictor, adjuster, adversarial_relationship):
    """Test that highly adversarial relationships trigger deferral."""
    interaction = InteractionCharacteristics(
        interaction_type="request",
        complexity="HIGH",
        expected_response_time=timedelta(minutes=15),
        actual_response_time=timedelta(minutes=60),
        claims_made=10,
        commitments_made=5,
        resources_requested=100.0,
        time_since_last=timedelta(hours=6),
        grounding_ci=0.25,
        witness_count=0,
        timing_anomaly=True,
        behavior_anomaly=True,
        claim_mismatch=True
    )

    prediction = predictor.predict_coherence(adversarial_relationship, interaction)

    # Should detect severe risks
    assert prediction.risk_score >= 0.7
    assert CoherenceRiskPattern.GROUNDING_FAILURE in prediction.risk_patterns

    adjustment = adjuster.adjust_verification(prediction, adversarial_relationship)

    # Should defer or require extreme verification
    assert adjustment.strategy in [
        VerificationStrategy.DEFER_INTERACTION,
        VerificationStrategy.INCREASE_GROUNDING_CHECKS,
        VerificationStrategy.REQUEST_PROOF
    ]


def test_risk_pattern_detection_timing_anomaly(predictor, stable_relationship):
    """Test detection of timing anomaly risk pattern."""
    interaction = InteractionCharacteristics(
        interaction_type="response",
        complexity="LOW",
        expected_response_time=timedelta(minutes=5),
        actual_response_time=timedelta(minutes=30),  # 6x expected
        claims_made=0,
        commitments_made=0,
        resources_requested=0.0,
        time_since_last=timedelta(hours=5),
        grounding_ci=0.90,
        witness_count=2
    )

    prediction = predictor.predict_coherence(stable_relationship, interaction)

    assert CoherenceRiskPattern.RESPONSE_TIME_ANOMALY in prediction.risk_patterns


def test_risk_pattern_detection_grounding_failure(predictor, stable_relationship):
    """Test detection of grounding failure risk pattern."""
    interaction = InteractionCharacteristics(
        interaction_type="request",
        complexity="MEDIUM",
        expected_response_time=timedelta(minutes=5),
        actual_response_time=timedelta(minutes=5),
        claims_made=2,
        commitments_made=1,
        resources_requested=10.0,
        time_since_last=timedelta(hours=4),
        grounding_ci=0.45,  # Low grounding CI
        witness_count=3
    )

    prediction = predictor.predict_coherence(stable_relationship, interaction)

    assert CoherenceRiskPattern.GROUNDING_FAILURE in prediction.risk_patterns


def test_fast_track_high_trust_relationship(adjuster, stable_relationship):
    """Test fast track for very high trust relationships."""
    # Boost relationship to very high trust
    stable_relationship.current_trust = TrustTensor(0.92, 0.95, 0.88, 0.93)
    stable_relationship.current_ci = 0.95
    stable_relationship.total_interactions = 200

    from relationship_coherence_ep import CoherencePrediction

    prediction = CoherencePrediction(
        predicted_ci_change=0.0,
        predicted_ci_after=0.95,
        confidence=0.85,
        risk_patterns=[],
        risk_score=0.05,
        reasoning="High trust, stable relationship",
        similar_pattern_count=10
    )

    adjustment = adjuster.adjust_verification(prediction, stable_relationship)

    assert adjustment.strategy == VerificationStrategy.FAST_TRACK
    assert adjustment.requirements.get("minimal_verification") == True


def test_pattern_learning(predictor):
    """Test that predictor learns from patterns."""
    # Create relationship
    rel = RelationshipHistory(
        relationship_lct="lct://test:relationship:test2@mainnet",
        participant_lcts=("lct://test@mainnet", "lct://test2@mainnet"),
        formed_date="2025-12-01",
        source="crystallized",
        current_trust=TrustTensor(0.70, 0.75, 0.65, 0.72),
        current_stance=StanceVector(0.70, 0.20, 0.05, 0.05),
        current_ci=0.80,
        total_interactions=50,
        recent_interactions=10,
        positive_interactions=45,
        negative_interactions=5,
        repair_events=1,
        avg_response_time=timedelta(minutes=7),
        response_time_variance=0.20,
        avg_interaction_gap=timedelta(hours=8),
        last_interaction=datetime.now() - timedelta(hours=6),
        trust_trajectory="stable",
        stance_stability=0.85,
        ci_history=[0.78, 0.79, 0.80, 0.80]
    )

    interaction = InteractionCharacteristics(
        interaction_type="request",
        complexity="MEDIUM",
        expected_response_time=timedelta(minutes=7),
        actual_response_time=timedelta(minutes=8),
        claims_made=3,
        commitments_made=2,
        resources_requested=15.0,
        time_since_last=timedelta(hours=6),
        grounding_ci=0.82,
        witness_count=2
    )

    # Add pattern to library
    pattern = RelationshipCoherencePattern(
        pattern_id="pattern_001",
        timestamp=datetime.now().isoformat(),
        context=rel,
        interaction=interaction,
        outcome=CoherenceOutcome(
            ci_before=0.80,
            ci_after=0.78,
            ci_change=-0.02,
            risk_patterns_detected=[],
            trust_before=rel.current_trust,
            trust_after=TrustTensor(0.70, 0.74, 0.65, 0.72),
            stance_before=rel.current_stance,
            stance_after=StanceVector(0.69, 0.21, 0.05, 0.05),
            violation_occurred=False,
            repair_attempted=False
        )
    )

    initial_count = predictor.get_pattern_count()
    predictor.add_pattern(pattern)
    assert predictor.get_pattern_count() == initial_count + 1


def test_stance_vector_sum_validation():
    """Test that stance vector enforces sum to 1.0."""
    # Valid stance
    valid = StanceVector(0.7, 0.2, 0.05, 0.05)
    assert abs(sum([valid.collaborative, valid.indifferent,
                    valid.competitive, valid.adversarial]) - 1.0) < 0.01

    # Invalid stance should raise
    with pytest.raises(ValueError):
        StanceVector(0.5, 0.2, 0.1, 0.1)  # Sum = 0.9


def test_trust_tensor_average():
    """Test trust tensor average calculation."""
    trust = TrustTensor(0.8, 0.9, 0.7, 0.6)
    # (0.8 + 0.9 + 0.7 + 0.6) / 4 = 3.0 / 4 = 0.75
    assert abs(trust.average() - 0.75) < 0.01


def test_ci_trend_detection(stable_relationship, declining_relationship):
    """Test CI trend analysis."""
    assert stable_relationship.get_ci_trend() == "improving"
    assert declining_relationship.get_ci_trend() == "declining"


def test_reciprocity_balance_calculation(stable_relationship):
    """Test reciprocity balance calculation."""
    balance = stable_relationship.get_reciprocity_balance()
    assert 0.0 <= balance <= 1.0
    # 140 positive out of 150 total
    assert abs(balance - (140/150)) < 0.01


def test_prediction_with_patterns(predictor):
    """Test prediction when similar patterns exist."""
    # Create base relationship
    rel = RelationshipHistory(
        relationship_lct="lct://pattern:relationship:test@mainnet",
        participant_lcts=("lct://pattern@mainnet", "lct://test@mainnet"),
        formed_date="2025-12-01",
        source="crystallized",
        current_trust=TrustTensor(0.75, 0.78, 0.72, 0.74),
        current_stance=StanceVector(0.75, 0.15, 0.05, 0.05),
        current_ci=0.82,
        total_interactions=60,
        recent_interactions=12,
        positive_interactions=55,
        negative_interactions=5,
        repair_events=0,
        avg_response_time=timedelta(minutes=8),
        response_time_variance=0.18,
        avg_interaction_gap=timedelta(hours=7),
        last_interaction=datetime.now() - timedelta(hours=5),
        trust_trajectory="stable",
        stance_stability=0.88,
        ci_history=[0.80, 0.81, 0.82, 0.82]
    )

    interaction = InteractionCharacteristics(
        interaction_type="request",
        complexity="MEDIUM",
        expected_response_time=timedelta(minutes=8),
        actual_response_time=timedelta(minutes=9),
        claims_made=2,
        commitments_made=1,
        resources_requested=12.0,
        time_since_last=timedelta(hours=5),
        grounding_ci=0.83,
        witness_count=2
    )

    # Add 5 similar patterns
    for i in range(5):
        pattern = RelationshipCoherencePattern(
            pattern_id=f"pattern_{i:03d}",
            timestamp=datetime.now().isoformat(),
            context=rel,
            interaction=interaction,
            outcome=CoherenceOutcome(
                ci_before=0.82,
                ci_after=0.80 - i * 0.01,  # Slight variation
                ci_change=-0.02 - i * 0.01,
                risk_patterns_detected=[],
                trust_before=rel.current_trust,
                trust_after=TrustTensor(0.75, 0.77, 0.72, 0.74),
                stance_before=rel.current_stance,
                stance_after=StanceVector(0.74, 0.16, 0.05, 0.05),
                violation_occurred=False,
                repair_attempted=False
            )
        )
        predictor.add_pattern(pattern)

    # Now predict - should use patterns
    prediction = predictor.predict_coherence(rel, interaction)

    assert prediction.similar_pattern_count >= 3
    assert prediction.confidence > 0.3  # Should have confidence from patterns


def test_high_risk_detection(predictor, adjuster, adversarial_relationship):
    """Test high risk interaction detection."""
    interaction = InteractionCharacteristics(
        interaction_type="request",
        complexity="HIGH",
        expected_response_time=timedelta(minutes=15),
        actual_response_time=timedelta(minutes=90),
        claims_made=15,
        commitments_made=8,
        resources_requested=200.0,
        time_since_last=timedelta(hours=2),
        grounding_ci=0.20,
        witness_count=0,
        timing_anomaly=True,
        behavior_anomaly=True,
        claim_mismatch=True
    )

    prediction = predictor.predict_coherence(adversarial_relationship, interaction)

    assert prediction.is_high_risk(risk_threshold=0.7)
    assert prediction.should_increase_verification()


def test_verification_strategy_selection(adjuster, declining_relationship):
    """Test verification strategy selection logic."""
    from relationship_coherence_ep import CoherencePrediction

    # Test INCREASE_GROUNDING_CHECKS for grounding failure
    pred_grounding = CoherencePrediction(
        predicted_ci_change=-0.25,
        predicted_ci_after=0.27,
        confidence=0.70,
        risk_patterns=[CoherenceRiskPattern.GROUNDING_FAILURE],
        risk_score=0.65,
        reasoning="Grounding failure detected",
        similar_pattern_count=5
    )

    adj = adjuster.adjust_verification(pred_grounding, declining_relationship)
    assert adj.strategy == VerificationStrategy.INCREASE_GROUNDING_CHECKS

    # Test REQUEST_PROOF for claim mismatches
    pred_claims = CoherencePrediction(
        predicted_ci_change=-0.20,
        predicted_ci_after=0.32,
        confidence=0.65,
        risk_patterns=[CoherenceRiskPattern.CLAIM_ACTION_MISMATCH],
        risk_score=0.55,
        reasoning="Claim-action mismatch",
        similar_pattern_count=4
    )

    adj2 = adjuster.adjust_verification(pred_claims, declining_relationship)
    assert adj2.strategy == VerificationStrategy.REQUEST_PROOF


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
