#!/usr/bin/env python3
"""
Grounding Quality as Epistemic Proprioception - Session 107

Applies SAGE Quality EP framework to Web4 grounding validation.

Core Insight (from Thor's Quality EP implementation):
Just as SAGE predicts response quality before generation, Web4 can predict
grounding coherence quality before validation, enabling proactive adjustment
of validation requirements.

EP Question for Grounding Quality:
"Given this identity's history, current grounding context, and validation
approach — how likely is the grounding to be low quality (vulnerable to attack)?"

Developmental Stages:
1. Immature: Validate grounding → Measure CI → Accept/reject
2. Developing: Predict quality → Adjust requirements → Validate
3. Mature: Anticipate quality issues, modulate requirements adaptively

Implementation inspired by:
- SAGE quality_pattern_predictor.py (pattern-based prediction)
- SAGE quality_ep_adjuster.py (approach adjustment)
- Web4 proportional_coherence_regulation.py (regulation framework)

Author: Claude (Session 107)
Date: 2025-12-30
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
import math

# ============================================================================
# Quality Patterns and Prediction
# ============================================================================

class GroundingRiskPattern(Enum):
    """Risk patterns in grounding context that predict low quality."""

    # Identity history patterns
    FREQUENT_LOCATION_CHANGES = "frequent_location_changes"  # Travel spoofing risk
    INCONSISTENT_CAPABILITIES = "inconsistent_capabilities"  # Device spoofing risk
    SPARSE_HISTORY = "sparse_history"  # Insufficient baseline
    RECENT_ANOMALIES = "recent_anomalies"  # Recent low-CI groundings

    # Grounding context patterns
    IMPOSSIBLE_TRAVEL = "impossible_travel"  # Spatial coherence violation
    CAPABILITY_MISMATCH = "capability_mismatch"  # Capability coherence violation
    TEMPORAL_GAP = "temporal_gap"  # Long time since last grounding
    NO_WITNESSES = "no_witnesses"  # Relational coherence weak

    # Validation approach patterns
    MINIMAL_VALIDATION = "minimal_validation"  # Few checks
    NO_SPATIAL_VALIDATION = "no_spatial_validation"  # Skip spatial checks
    WEAK_PROOF_REQUIREMENTS = "weak_proof_requirements"  # Low proof threshold


@dataclass
class GroundingQualityPrediction:
    """
    Predicted quality of grounding validation.

    Quality here means: "How confident are we that this grounding
    represents legitimate identity state vs potential attack?"

    Similar to SAGE's QualityPrediction but for grounding CI.
    """
    predicted_ci: float  # Expected coherence index [0.0, 1.0]
    confidence: float  # Confidence in prediction [0.0, 1.0]
    risk_patterns: List[GroundingRiskPattern]  # Identified risk factors
    risk_score: float  # Overall risk [0.0, 1.0]
    reasoning: str  # Why this prediction

    def should_adjust_validation(self, ci_threshold: float = 0.6) -> bool:
        """Determine if validation requirements should be adjusted."""
        return (
            self.predicted_ci < ci_threshold and
            self.confidence > 0.5  # Only adjust if confident in prediction
        )


@dataclass
class IdentityGroundingHistory:
    """
    Identity's grounding history for quality pattern recognition.

    Analogous to SAGE's query history.
    """
    lct_uri: str
    grounding_count: int
    avg_ci: float
    min_ci: float
    last_grounding_time: Optional[datetime]

    # Pattern indicators
    location_changes_per_hour: float  # Mobility pattern
    capability_changes_per_day: float  # Device switching pattern
    ci_variance: float  # Stability indicator
    anomaly_count_last_10: int  # Recent issues

    # Risk indicators
    has_impossible_travel_history: bool
    has_capability_spoofing_history: bool
    witness_vouching_rate: float  # % of groundings with witnesses


class GroundingQualityPredictor:
    """
    Predicts grounding coherence quality before full validation.

    Epistemic Proprioception: Anticipate grounding issues before they occur.

    Pattern-based prediction using identity history and context analysis.
    """

    def __init__(
        self,
        ci_threshold_low: float = 0.4,
        ci_threshold_high: float = 0.7
    ):
        """
        Initialize quality predictor.

        Args:
            ci_threshold_low: CI below this indicates severe quality issues
            ci_threshold_high: CI above this indicates good quality
        """
        self.ci_threshold_low = ci_threshold_low
        self.ci_threshold_high = ci_threshold_high

        # Pattern → Quality mapping (learned from history)
        # This would be populated from actual grounding history in production
        self.quality_patterns = self._initialize_quality_patterns()

    def _initialize_quality_patterns(self) -> Dict[str, float]:
        """
        Initialize quality patterns from known correlations.

        In production, these would be learned from grounding history.
        For now, use reasonable defaults based on Web4 coherence principles.
        """
        return {
            # Identity history patterns
            "clean_history_stable_ci": 0.85,  # High quality likely
            "sparse_history": 0.50,  # Medium quality (insufficient data)
            "frequent_anomalies": 0.30,  # Low quality likely
            "impossible_travel_history": 0.25,  # Very low quality

            # Context patterns
            "impossible_travel_detected": 0.10,  # Severe issue
            "fast_travel_no_announcement": 0.40,  # Suspicious
            "capability_mismatch": 0.35,  # Likely spoofing
            "temporal_gap_long": 0.55,  # Uncertainty
            "no_witnesses_unknown_location": 0.45,  # Weak validation

            # Validation approach patterns
            "full_validation_strong_history": 0.90,  # Excellent
            "full_validation_weak_history": 0.65,  # Good but cautious
            "minimal_validation_clean_history": 0.75,  # Acceptable risk
            "minimal_validation_suspicious": 0.30,  # Dangerous
        }

    def predict_quality(
        self,
        identity_history: IdentityGroundingHistory,
        current_context: Dict,  # Current grounding context
        validation_approach: Optional[str] = "standard"
    ) -> GroundingQualityPrediction:
        """
        Predict grounding quality before full validation.

        Args:
            identity_history: Historical grounding data for this identity
            current_context: Current grounding request context
            validation_approach: Planned validation approach

        Returns:
            Quality prediction with risk assessment
        """
        risk_patterns = []
        risk_contributions = []

        # 1. Analyze identity history patterns
        if identity_history.grounding_count < 5:
            risk_patterns.append(GroundingRiskPattern.SPARSE_HISTORY)
            risk_contributions.append(("sparse_history", 0.3))

        if identity_history.anomaly_count_last_10 > 3:
            risk_patterns.append(GroundingRiskPattern.RECENT_ANOMALIES)
            risk_contributions.append(("frequent_anomalies", 0.4))

        if identity_history.has_impossible_travel_history:
            risk_patterns.append(GroundingRiskPattern.FREQUENT_LOCATION_CHANGES)
            risk_contributions.append(("impossible_travel_history", 0.5))

        # 2. Analyze current context
        if current_context.get("impossible_travel", False):
            risk_patterns.append(GroundingRiskPattern.IMPOSSIBLE_TRAVEL)
            risk_contributions.append(("impossible_travel_detected", 0.8))

        if current_context.get("capability_mismatch", False):
            risk_patterns.append(GroundingRiskPattern.CAPABILITY_MISMATCH)
            risk_contributions.append(("capability_mismatch", 0.6))

        time_since_last = current_context.get("time_since_last_grounding", timedelta(hours=0))
        if time_since_last > timedelta(days=7):
            risk_patterns.append(GroundingRiskPattern.TEMPORAL_GAP)
            risk_contributions.append(("temporal_gap_long", 0.3))

        if not current_context.get("has_witnesses", False):
            risk_patterns.append(GroundingRiskPattern.NO_WITNESSES)
            risk_contributions.append(("no_witnesses_unknown_location", 0.2))

        # 3. Calculate predicted CI
        if len(risk_contributions) == 0:
            # No risk factors detected
            predicted_ci = max(0.8, identity_history.avg_ci)
            confidence = 0.8
        else:
            # Combine risk contributions
            # Use weighted average based on risk severity
            risk_weights = [contrib[1] for contrib in risk_contributions]
            base_quality = identity_history.avg_ci

            # Each risk factor reduces predicted CI
            risk_impact = sum(risk_weights) / len(risk_weights)
            predicted_ci = base_quality * (1 - risk_impact)

            # Confidence based on history size and pattern clarity
            confidence = min(0.9, 0.5 + (identity_history.grounding_count / 20))

        # 4. Calculate overall risk score
        risk_score = 1.0 - predicted_ci

        # 5. Generate reasoning
        reasoning = self._generate_reasoning(
            identity_history,
            risk_patterns,
            predicted_ci
        )

        return GroundingQualityPrediction(
            predicted_ci=predicted_ci,
            confidence=confidence,
            risk_patterns=risk_patterns,
            risk_score=risk_score,
            reasoning=reasoning
        )

    def _generate_reasoning(
        self,
        identity_history: IdentityGroundingHistory,
        risk_patterns: List[GroundingRiskPattern],
        predicted_ci: float
    ) -> str:
        """Generate human-readable reasoning for prediction."""
        if len(risk_patterns) == 0:
            return (
                f"Identity has clean history (avg CI={identity_history.avg_ci:.2f}, "
                f"{identity_history.grounding_count} groundings). "
                f"Predicted CI={predicted_ci:.2f} (HIGH quality)."
            )

        risk_desc = ", ".join([p.value for p in risk_patterns])
        return (
            f"Detected {len(risk_patterns)} risk patterns: {risk_desc}. "
            f"Identity history: {identity_history.grounding_count} groundings, "
            f"avg CI={identity_history.avg_ci:.2f}. "
            f"Predicted CI={predicted_ci:.2f} (quality concern)."
        )


# ============================================================================
# Validation Adjustment (Analogous to SAGE's QualityEPAdjuster)
# ============================================================================

class ValidationStrategy(Enum):
    """Validation requirement adjustment strategies."""

    # Strengthen validation
    REQUIRE_WITNESSES = "require_witnesses"  # Add witness vouching requirement
    INCREASE_SPATIAL_CHECKS = "increase_spatial_checks"  # More spatial validation
    REQUIRE_ANNOUNCEMENT = "require_announcement"  # Require travel announcement
    EXTEND_TEMPORAL_WINDOW = "extend_temporal_window"  # Check longer history

    # Maintain standard
    STANDARD_VALIDATION = "standard_validation"  # No adjustment needed

    # Relax validation (high-trust identities)
    FAST_TRACK = "fast_track"  # Minimal validation for trusted identities


@dataclass
class AdjustedValidationRequirements:
    """
    Adjusted validation requirements based on quality prediction.

    Analogous to SAGE's AdjustedApproach.
    """
    original_prediction: GroundingQualityPrediction
    adjustment_applied: bool
    strategy: ValidationStrategy
    requirements: Dict[str, any]  # Specific validation requirements
    expected_ci_improvement: float  # Expected CI increase from adjustment
    reasoning: str  # Why this adjustment


class ValidationAdjuster:
    """
    Adjusts validation requirements based on predicted quality.

    Epistemic Proprioception: Modulate validation rigor based on anticipated risk.

    Analogous to SAGE's QualityEPAdjuster.
    """

    def __init__(
        self,
        adjustment_threshold: float = 0.6,
        confidence_threshold: float = 0.5
    ):
        """
        Initialize validation adjuster.

        Args:
            adjustment_threshold: Predicted CI below this triggers adjustment
            confidence_threshold: Minimum confidence to trigger adjustment
        """
        self.adjustment_threshold = adjustment_threshold
        self.confidence_threshold = confidence_threshold

    def adjust_validation(
        self,
        prediction: GroundingQualityPrediction,
        identity_history: IdentityGroundingHistory
    ) -> AdjustedValidationRequirements:
        """
        Determine if/how to adjust validation requirements.

        Args:
            prediction: Quality prediction for this grounding
            identity_history: Identity's historical data

        Returns:
            Adjusted validation requirements
        """
        # Decision: Should we adjust?
        should_adjust = (
            prediction.predicted_ci < self.adjustment_threshold and
            prediction.confidence > self.confidence_threshold
        )

        if not should_adjust:
            # No adjustment needed
            if prediction.predicted_ci >= 0.8:
                # High quality - can use fast track for trusted identities
                if identity_history.grounding_count > 20 and identity_history.avg_ci > 0.85:
                    return self._fast_track(prediction)

            return self._no_adjustment(prediction)

        # Select adjustment strategy based on risk patterns
        strategy = self._select_strategy(prediction, identity_history)

        # Apply strategy
        return self._apply_strategy(strategy, prediction, identity_history)

    def _select_strategy(
        self,
        prediction: GroundingQualityPrediction,
        identity_history: IdentityGroundingHistory
    ) -> ValidationStrategy:
        """Select appropriate validation strategy based on risk patterns."""

        # Priority order for risk mitigation
        risk_patterns = prediction.risk_patterns

        # Severe: Impossible travel
        if GroundingRiskPattern.IMPOSSIBLE_TRAVEL in risk_patterns:
            return ValidationStrategy.REQUIRE_ANNOUNCEMENT

        # High: Capability mismatch
        if GroundingRiskPattern.CAPABILITY_MISMATCH in risk_patterns:
            return ValidationStrategy.REQUIRE_WITNESSES

        # Medium: Sparse history or recent anomalies
        if (GroundingRiskPattern.SPARSE_HISTORY in risk_patterns or
            GroundingRiskPattern.RECENT_ANOMALIES in risk_patterns):
            return ValidationStrategy.INCREASE_SPATIAL_CHECKS

        # Low: Temporal gap or no witnesses
        if (GroundingRiskPattern.TEMPORAL_GAP in risk_patterns or
            GroundingRiskPattern.NO_WITNESSES in risk_patterns):
            return ValidationStrategy.EXTEND_TEMPORAL_WINDOW

        # Default: Standard validation with extra checks
        return ValidationStrategy.INCREASE_SPATIAL_CHECKS

    def _apply_strategy(
        self,
        strategy: ValidationStrategy,
        prediction: GroundingQualityPrediction,
        identity_history: IdentityGroundingHistory
    ) -> AdjustedValidationRequirements:
        """Apply selected validation strategy."""

        requirements = {}
        expected_improvement = 0.0
        reasoning = ""

        if strategy == ValidationStrategy.REQUIRE_ANNOUNCEMENT:
            requirements = {
                "require_travel_announcement": True,
                "announcement_lead_time": timedelta(hours=1),
                "spatial_validation": "strict"
            }
            expected_improvement = 0.2  # Announcement can boost CI significantly
            reasoning = (
                "Impossible travel detected. Require travel announcement to "
                "validate legitimacy. Expected CI improvement: +0.2"
            )

        elif strategy == ValidationStrategy.REQUIRE_WITNESSES:
            requirements = {
                "min_witnesses": 2,
                "witness_trust_threshold": 0.7,
                "require_relational_validation": True
            }
            expected_improvement = 0.15
            reasoning = (
                "Capability mismatch or weak history. Require witness vouching "
                "to strengthen relational coherence. Expected CI improvement: +0.15"
            )

        elif strategy == ValidationStrategy.INCREASE_SPATIAL_CHECKS:
            requirements = {
                "spatial_validation": "strict",
                "check_velocity_profile": True,
                "verify_location_precision": True
            }
            expected_improvement = 0.10
            reasoning = (
                "Sparse history or anomalies. Increase spatial validation rigor. "
                "Expected CI improvement: +0.10"
            )

        elif strategy == ValidationStrategy.EXTEND_TEMPORAL_WINDOW:
            requirements = {
                "temporal_window_extension": timedelta(days=14),
                "require_consistency_check": True
            }
            expected_improvement = 0.08
            reasoning = (
                "Long temporal gap. Extend validation window to check consistency "
                "over longer period. Expected CI improvement: +0.08"
            )

        return AdjustedValidationRequirements(
            original_prediction=prediction,
            adjustment_applied=True,
            strategy=strategy,
            requirements=requirements,
            expected_ci_improvement=expected_improvement,
            reasoning=reasoning
        )

    def _no_adjustment(
        self,
        prediction: GroundingQualityPrediction
    ) -> AdjustedValidationRequirements:
        """No adjustment needed - standard validation."""
        return AdjustedValidationRequirements(
            original_prediction=prediction,
            adjustment_applied=False,
            strategy=ValidationStrategy.STANDARD_VALIDATION,
            requirements={"validation_mode": "standard"},
            expected_ci_improvement=0.0,
            reasoning="Predicted quality acceptable. Standard validation sufficient."
        )

    def _fast_track(
        self,
        prediction: GroundingQualityPrediction
    ) -> AdjustedValidationRequirements:
        """Fast track for high-trust identities."""
        return AdjustedValidationRequirements(
            original_prediction=prediction,
            adjustment_applied=True,
            strategy=ValidationStrategy.FAST_TRACK,
            requirements={"validation_mode": "minimal", "trust_identity": True},
            expected_ci_improvement=0.0,
            reasoning="High-trust identity with excellent history. Fast-track validation."
        )


# ============================================================================
# Demo and Testing
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("Grounding Quality Epistemic Proprioception - Session 107")
    print("="*70)

    # Create predictor and adjuster
    predictor = GroundingQualityPredictor()
    adjuster = ValidationAdjuster()

    # Test Case 1: Clean history, normal grounding
    print("\n" + "="*70)
    print("Test 1: Clean history, normal grounding")
    print("="*70)

    clean_history = IdentityGroundingHistory(
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

    clean_context = {
        "impossible_travel": False,
        "capability_mismatch": False,
        "time_since_last_grounding": timedelta(hours=2),
        "has_witnesses": True
    }

    prediction = predictor.predict_quality(clean_history, clean_context)
    adjustment = adjuster.adjust_validation(prediction, clean_history)

    print(f"\nPrediction:")
    print(f"  Predicted CI: {prediction.predicted_ci:.3f}")
    print(f"  Confidence: {prediction.confidence:.3f}")
    print(f"  Risk patterns: {[p.value for p in prediction.risk_patterns]}")
    print(f"  Reasoning: {prediction.reasoning}")

    print(f"\nValidation Adjustment:")
    print(f"  Strategy: {adjustment.strategy.value}")
    print(f"  Adjustment applied: {adjustment.adjustment_applied}")
    print(f"  Reasoning: {adjustment.reasoning}")

    # Test Case 2: Impossible travel detected
    print("\n" + "="*70)
    print("Test 2: Impossible travel detected (Portland → Tokyo in 15 min)")
    print("="*70)

    suspicious_context = {
        "impossible_travel": True,
        "capability_mismatch": False,
        "time_since_last_grounding": timedelta(minutes=15),
        "has_witnesses": False
    }

    prediction2 = predictor.predict_quality(clean_history, suspicious_context)
    adjustment2 = adjuster.adjust_validation(prediction2, clean_history)

    print(f"\nPrediction:")
    print(f"  Predicted CI: {prediction2.predicted_ci:.3f}")
    print(f"  Confidence: {prediction2.confidence:.3f}")
    print(f"  Risk patterns: {[p.value for p in prediction2.risk_patterns]}")
    print(f"  Reasoning: {prediction2.reasoning}")

    print(f"\nValidation Adjustment:")
    print(f"  Strategy: {adjustment2.strategy.value}")
    print(f"  Requirements: {adjustment2.requirements}")
    print(f"  Expected CI improvement: +{adjustment2.expected_ci_improvement:.2f}")
    print(f"  Reasoning: {adjustment2.reasoning}")

    # Test Case 3: Sparse history, new identity
    print("\n" + "="*70)
    print("Test 3: Sparse history, new identity")
    print("="*70)

    sparse_history = IdentityGroundingHistory(
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

    normal_context = {
        "impossible_travel": False,
        "capability_mismatch": False,
        "time_since_last_grounding": timedelta(days=3),
        "has_witnesses": False
    }

    prediction3 = predictor.predict_quality(sparse_history, normal_context)
    adjustment3 = adjuster.adjust_validation(prediction3, sparse_history)

    print(f"\nPrediction:")
    print(f"  Predicted CI: {prediction3.predicted_ci:.3f}")
    print(f"  Confidence: {prediction3.confidence:.3f}")
    print(f"  Risk patterns: {[p.value for p in prediction3.risk_patterns]}")
    print(f"  Reasoning: {prediction3.reasoning}")

    print(f"\nValidation Adjustment:")
    print(f"  Strategy: {adjustment3.strategy.value}")
    print(f"  Requirements: {adjustment3.requirements}")
    print(f"  Expected CI improvement: +{adjustment3.expected_ci_improvement:.2f}")
    print(f"  Reasoning: {adjustment3.reasoning}")

    print("\n" + "="*70)
    print("Quality EP enables proactive validation adjustment")
    print("="*70)
