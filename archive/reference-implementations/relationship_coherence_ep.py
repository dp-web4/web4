"""
Relationship Coherence Epistemic Proprioception

Predicts relationship coherence degradation BEFORE interactions complete,
enabling proactive verification and security adjustments.

Based on:
- Session 107: Grounding Quality EP framework
- Thor's EP Trinity: Emotional, Quality, Attention EP (2025-12-30)
- Web4 Entity Relationship Spec (2025-12-30)
- SAGE Relationship Schema

The EP Question:
"Given relationship history and current interaction characteristics,
will this interaction cause coherence index (CI) to drop significantly?"

Pattern Structure:
- RelationshipContext: Current state (trust, stance, history)
- InteractionCharacteristics: What's happening now
- CoherenceOutcome: CI change, violations detected

Stages:
1. Immature: Measure CI after interaction (reactive)
2. Learning: Predict CI change before interaction (pattern-based)
3. Mature: Adjust verification/stance proactively (high-confidence)

Created: 2025-12-30
Session: 108 (Legion autonomous research)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import math


class CoherenceRiskPattern(Enum):
    """Risk patterns that predict coherence degradation."""

    # Behavioral inconsistency
    RESPONSE_TIME_ANOMALY = "response_time_anomaly"
    CAPABILITY_SHIFT = "capability_shift"
    COMMUNICATION_STYLE_CHANGE = "communication_style_change"

    # Trust violations
    CLAIM_ACTION_MISMATCH = "claim_action_mismatch"
    COMMITMENT_BROKEN = "commitment_broken"
    DECEPTION_DETECTED = "deception_detected"

    # Temporal patterns
    IMPOSSIBLE_TIMING = "impossible_timing"
    FREQUENCY_ANOMALY = "frequency_anomaly"
    TEMPORAL_GAP_UNUSUAL = "temporal_gap_unusual"

    # Stance shifts
    STANCE_INVERSION = "stance_inversion"  # Collaborative → Adversarial rapidly
    RECIPROCITY_IMBALANCE = "reciprocity_imbalance"

    # Identity concerns
    GROUNDING_FAILURE = "grounding_failure"
    IDENTITY_COHERENCE_LOW = "identity_coherence_low"


@dataclass
class TrustTensor:
    """Four-dimensional trust assessment."""
    competence: float  # Can they do what they claim? [0.0, 1.0]
    reliability: float  # Do they show up consistently? [0.0, 1.0]
    benevolence: float  # Do they act in my interest? [0.0, 1.0]
    integrity: float  # Are they honest? [0.0, 1.0]

    def average(self) -> float:
        return (self.competence + self.reliability +
                self.benevolence + self.integrity) / 4.0

    def to_dict(self) -> Dict:
        return {
            "competence": self.competence,
            "reliability": self.reliability,
            "benevolence": self.benevolence,
            "integrity": self.integrity
        }


@dataclass
class StanceVector:
    """Probability distribution over relationship stances."""
    collaborative: float  # Shared goals, mutual benefit [0.0, 1.0]
    indifferent: float  # No significant engagement [0.0, 1.0]
    competitive: float  # Overlapping goals, bounded conflict [0.0, 1.0]
    adversarial: float  # Opposing goals, potential harm [0.0, 1.0]

    def __post_init__(self):
        total = self.collaborative + self.indifferent + self.competitive + self.adversarial
        if not math.isclose(total, 1.0, abs_tol=0.01):
            raise ValueError(f"Stance vector must sum to 1.0, got {total}")

    def dominant_stance(self) -> str:
        stances = {
            "collaborative": self.collaborative,
            "indifferent": self.indifferent,
            "competitive": self.competitive,
            "adversarial": self.adversarial
        }
        return max(stances, key=stances.get)

    def to_dict(self) -> Dict:
        return {
            "collaborative": self.collaborative,
            "indifferent": self.indifferent,
            "competitive": self.competitive,
            "adversarial": self.adversarial
        }


@dataclass
class RelationshipHistory:
    """Historical relationship state and patterns."""
    relationship_lct: str
    participant_lcts: Tuple[str, str]
    formed_date: str
    source: str  # predefined, crystallized, introduced, witnessed

    # Current state
    current_trust: TrustTensor
    current_stance: StanceVector
    current_ci: float

    # Interaction history
    total_interactions: int
    recent_interactions: int  # Last 7 days
    positive_interactions: int
    negative_interactions: int
    repair_events: int

    # Temporal patterns
    avg_response_time: timedelta
    response_time_variance: float
    avg_interaction_gap: timedelta
    last_interaction: datetime

    # Trust evolution
    trust_trajectory: str  # "improving", "stable", "declining"
    stance_stability: float  # 0.0-1.0, how much stance fluctuates
    ci_history: List[float] = field(default_factory=list)  # Last 10 CI values

    def get_ci_trend(self) -> str:
        """Analyze CI trend from history."""
        if len(self.ci_history) < 3:
            return "insufficient_data"

        recent = self.ci_history[-3:]
        if all(recent[i] < recent[i-1] for i in range(1, len(recent))):
            return "declining"
        elif all(recent[i] > recent[i-1] for i in range(1, len(recent))):
            return "improving"
        else:
            return "stable"

    def get_reciprocity_balance(self) -> float:
        """Calculate give/take balance. 0.5 = balanced."""
        if self.total_interactions == 0:
            return 0.5
        # Simplified: ratio of positive to total
        return self.positive_interactions / self.total_interactions


@dataclass
class InteractionCharacteristics:
    """Current interaction being evaluated."""
    interaction_type: str  # "request", "response", "announcement", "challenge"
    complexity: str  # "LOW", "MEDIUM", "HIGH"
    expected_response_time: Optional[timedelta]
    actual_response_time: Optional[timedelta]

    # Content analysis
    claims_made: int
    commitments_made: int
    resources_requested: float  # ATP or equivalent

    # Context
    time_since_last: timedelta
    grounding_ci: Optional[float]  # From grounding validation if available
    witness_count: int

    # Anomaly flags
    timing_anomaly: bool = False
    behavior_anomaly: bool = False
    claim_mismatch: bool = False


@dataclass
class CoherenceOutcome:
    """Result of interaction on relationship coherence."""
    ci_before: float
    ci_after: float
    ci_change: float

    risk_patterns_detected: List[CoherenceRiskPattern]

    # Trust tensor changes
    trust_before: TrustTensor
    trust_after: TrustTensor

    # Stance changes
    stance_before: StanceVector
    stance_after: StanceVector

    violation_occurred: bool
    repair_attempted: bool

    def is_significant_degradation(self, threshold: float = 0.15) -> bool:
        """Check if CI drop is significant."""
        return self.ci_change < -threshold


@dataclass
class RelationshipCoherencePattern:
    """Complete pattern for learning."""
    pattern_id: str
    timestamp: str

    # The core relationship
    context: RelationshipHistory
    interaction: InteractionCharacteristics
    outcome: CoherenceOutcome

    # Learning metadata
    prediction_error: Optional[float] = None  # If predicted, how far off?


@dataclass
class CoherencePrediction:
    """Predicted coherence outcome."""
    predicted_ci_change: float  # Expected CI delta
    predicted_ci_after: float  # Expected CI after interaction
    confidence: float  # 0.0-1.0

    risk_patterns: List[CoherenceRiskPattern]
    risk_score: float  # 0.0-1.0, overall risk

    reasoning: str
    similar_pattern_count: int

    def should_increase_verification(self, ci_threshold: float = 0.6,
                                    degradation_threshold: float = -0.15) -> bool:
        """Should we increase verification requirements?"""
        return (
            self.predicted_ci_after < ci_threshold or
            self.predicted_ci_change < degradation_threshold
        ) and self.confidence >= 0.5

    def is_high_risk(self, risk_threshold: float = 0.7) -> bool:
        """Is this a high-risk interaction?"""
        return self.risk_score >= risk_threshold and self.confidence > 0.3


class RelationshipCoherencePredictor:
    """Predicts relationship coherence degradation before interaction completes."""

    def __init__(self, pattern_library: Optional[List[RelationshipCoherencePattern]] = None):
        self.patterns = pattern_library or []
        self.min_patterns_for_prediction = 3

    def predict_coherence(
        self,
        relationship: RelationshipHistory,
        interaction: InteractionCharacteristics
    ) -> CoherencePrediction:
        """Predict CI change before interaction completes."""

        # 1. Detect risk patterns from context
        risk_patterns = self._detect_risk_patterns(relationship, interaction)

        # 2. Find similar historical patterns
        similar_patterns = self._find_similar_patterns(relationship, interaction)

        # 3. Calculate prediction from patterns
        if len(similar_patterns) >= self.min_patterns_for_prediction:
            predicted_change, confidence = self._predict_from_patterns(similar_patterns)
        else:
            # Fall back to risk-based prediction
            predicted_change, confidence = self._predict_from_risks(
                relationship, risk_patterns
            )

        predicted_ci_after = max(0.0, min(1.0, relationship.current_ci + predicted_change))

        # 4. Calculate risk score
        risk_score = self._calculate_risk_score(risk_patterns, relationship)

        # 5. Generate reasoning
        reasoning = self._generate_reasoning(
            relationship, interaction, risk_patterns,
            similar_patterns, predicted_change
        )

        return CoherencePrediction(
            predicted_ci_change=predicted_change,
            predicted_ci_after=predicted_ci_after,
            confidence=confidence,
            risk_patterns=risk_patterns,
            risk_score=risk_score,
            reasoning=reasoning,
            similar_pattern_count=len(similar_patterns)
        )

    def _detect_risk_patterns(
        self,
        relationship: RelationshipHistory,
        interaction: InteractionCharacteristics
    ) -> List[CoherenceRiskPattern]:
        """Detect risk patterns from current context."""
        risks = []

        # Temporal anomalies
        if interaction.actual_response_time and interaction.expected_response_time:
            ratio = (interaction.actual_response_time.total_seconds() /
                    interaction.expected_response_time.total_seconds())
            if ratio > 3.0 or ratio < 0.3:
                risks.append(CoherenceRiskPattern.RESPONSE_TIME_ANOMALY)

        if interaction.timing_anomaly:
            risks.append(CoherenceRiskPattern.IMPOSSIBLE_TIMING)

        # Behavioral anomalies
        if interaction.behavior_anomaly:
            risks.append(CoherenceRiskPattern.COMMUNICATION_STYLE_CHANGE)

        if interaction.claim_mismatch:
            risks.append(CoherenceRiskPattern.CLAIM_ACTION_MISMATCH)

        # Stance shifts
        if relationship.current_stance.adversarial > 0.3:
            if relationship.current_stance.collaborative < 0.2:
                risks.append(CoherenceRiskPattern.STANCE_INVERSION)

        # Reciprocity
        reciprocity = relationship.get_reciprocity_balance()
        if reciprocity < 0.3 or reciprocity > 0.7:
            risks.append(CoherenceRiskPattern.RECIPROCITY_IMBALANCE)

        # Grounding issues
        if interaction.grounding_ci is not None and interaction.grounding_ci < 0.6:
            risks.append(CoherenceRiskPattern.GROUNDING_FAILURE)

        # CI trend
        if relationship.get_ci_trend() == "declining":
            risks.append(CoherenceRiskPattern.IDENTITY_COHERENCE_LOW)

        # Temporal gaps
        if interaction.time_since_last > relationship.avg_interaction_gap * 3:
            risks.append(CoherenceRiskPattern.TEMPORAL_GAP_UNUSUAL)

        return risks

    def _find_similar_patterns(
        self,
        relationship: RelationshipHistory,
        interaction: InteractionCharacteristics
    ) -> List[RelationshipCoherencePattern]:
        """Find similar patterns from history."""
        similar = []

        for pattern in self.patterns:
            similarity = self._calculate_similarity(
                relationship, interaction,
                pattern.context, pattern.interaction
            )

            if similarity > 0.6:  # Threshold for similarity
                similar.append(pattern)

        return similar

    def _calculate_similarity(
        self,
        current_rel: RelationshipHistory,
        current_int: InteractionCharacteristics,
        pattern_rel: RelationshipHistory,
        pattern_int: InteractionCharacteristics
    ) -> float:
        """Calculate similarity between current and pattern."""
        similarities = []

        # Trust tensor similarity
        trust_sim = 1.0 - abs(
            current_rel.current_trust.average() -
            pattern_rel.current_trust.average()
        )
        similarities.append(trust_sim)

        # Stance similarity (dominant stance match)
        stance_sim = 1.0 if (
            current_rel.current_stance.dominant_stance() ==
            pattern_rel.current_stance.dominant_stance()
        ) else 0.5
        similarities.append(stance_sim)

        # CI similarity
        ci_sim = 1.0 - abs(current_rel.current_ci - pattern_rel.current_ci)
        similarities.append(ci_sim)

        # Interaction type match
        type_sim = 1.0 if current_int.interaction_type == pattern_int.interaction_type else 0.5
        similarities.append(type_sim)

        return sum(similarities) / len(similarities)

    def _predict_from_patterns(
        self,
        similar_patterns: List[RelationshipCoherencePattern]
    ) -> Tuple[float, float]:
        """Predict CI change from similar patterns."""
        ci_changes = [p.outcome.ci_change for p in similar_patterns]

        # Average CI change from similar patterns
        predicted_change = sum(ci_changes) / len(ci_changes)

        # Confidence based on pattern count and variance
        confidence = min(1.0, len(similar_patterns) / 10.0)

        # Reduce confidence if high variance
        if len(ci_changes) > 1:
            variance = sum((x - predicted_change) ** 2 for x in ci_changes) / len(ci_changes)
            if variance > 0.1:
                confidence *= 0.7

        return predicted_change, confidence

    def _predict_from_risks(
        self,
        relationship: RelationshipHistory,
        risks: List[CoherenceRiskPattern]
    ) -> Tuple[float, float]:
        """Predict CI change from risk patterns when no similar patterns."""
        if not risks:
            return 0.0, 0.3  # No risks, low confidence

        # High-severity risks
        severe_risks = {
            CoherenceRiskPattern.DECEPTION_DETECTED,
            CoherenceRiskPattern.CLAIM_ACTION_MISMATCH,
            CoherenceRiskPattern.STANCE_INVERSION,
            CoherenceRiskPattern.GROUNDING_FAILURE
        }

        severe_count = sum(1 for r in risks if r in severe_risks)
        moderate_count = len(risks) - severe_count

        # Predict larger drops for severe risks
        predicted_change = -(severe_count * 0.20 + moderate_count * 0.08)

        # Moderate confidence in risk-based prediction
        confidence = 0.5

        return predicted_change, confidence

    def _calculate_risk_score(
        self,
        risks: List[CoherenceRiskPattern],
        relationship: RelationshipHistory
    ) -> float:
        """Calculate overall risk score 0.0-1.0."""
        if not risks:
            return 0.0

        # Base risk from count
        risk = min(1.0, len(risks) * 0.15)

        # Amplify if trust already low
        if relationship.current_trust.average() < 0.4:
            risk = min(1.0, risk * 1.3)

        # Amplify if CI already low
        if relationship.current_ci < 0.5:
            risk = min(1.0, risk * 1.2)

        # Amplify if adversarial stance
        if relationship.current_stance.adversarial > 0.3:
            risk = min(1.0, risk * 1.5)

        return risk

    def _generate_reasoning(
        self,
        relationship: RelationshipHistory,
        interaction: InteractionCharacteristics,
        risks: List[CoherenceRiskPattern],
        similar_patterns: List[RelationshipCoherencePattern],
        predicted_change: float
    ) -> str:
        """Generate human-readable reasoning."""
        parts = []

        # Pattern-based reasoning
        if similar_patterns:
            parts.append(
                f"Found {len(similar_patterns)} similar interaction patterns. "
                f"Historical CI change: {predicted_change:+.2f} average."
            )

        # Risk-based reasoning
        if risks:
            parts.append(
                f"Detected {len(risks)} risk patterns: " +
                ", ".join(r.value for r in risks[:3])
            )

        # State-based reasoning
        if relationship.current_ci < 0.6:
            parts.append(f"Relationship CI already low ({relationship.current_ci:.2f}).")

        if relationship.current_trust.average() < 0.5:
            parts.append(
                f"Trust below average ({relationship.current_trust.average():.2f})."
            )

        if relationship.current_stance.adversarial > 0.2:
            parts.append(
                f"Elevated adversarial stance ({relationship.current_stance.adversarial:.2f})."
            )

        # Trend
        trend = relationship.get_ci_trend()
        if trend == "declining":
            parts.append("CI trending downward recently.")

        return " ".join(parts) if parts else "No significant risk indicators."

    def add_pattern(self, pattern: RelationshipCoherencePattern):
        """Add a new pattern to learning corpus."""
        self.patterns.append(pattern)

    def get_pattern_count(self) -> int:
        """Get total pattern count."""
        return len(self.patterns)


class VerificationStrategy(Enum):
    """Verification adjustment strategies."""
    REQUIRE_WITNESSES = "require_witnesses"
    INCREASE_GROUNDING_CHECKS = "increase_grounding_checks"
    REQUEST_PROOF = "request_proof"
    DEFER_INTERACTION = "defer_interaction"
    HEIGHTENED_SCRUTINY = "heightened_scrutiny"
    STANDARD_VERIFICATION = "standard_verification"
    FAST_TRACK = "fast_track"  # High trust, low risk


@dataclass
class AdjustedVerificationRequirements:
    """Adjusted verification based on prediction."""
    strategy: VerificationStrategy
    requirements: Dict
    expected_ci_protection: float  # How much CI drop prevented
    reasoning: str


class CoherenceVerificationAdjuster:
    """Adjusts verification requirements based on coherence prediction."""

    def __init__(self,
                 ci_threshold: float = 0.6,
                 degradation_threshold: float = -0.15,
                 confidence_threshold: float = 0.5):
        self.ci_threshold = ci_threshold
        self.degradation_threshold = degradation_threshold
        self.confidence_threshold = confidence_threshold

    def adjust_verification(
        self,
        prediction: CoherencePrediction,
        relationship: RelationshipHistory
    ) -> AdjustedVerificationRequirements:
        """Adjust verification requirements based on prediction."""

        should_adjust = (
            (prediction.predicted_ci_after < self.ci_threshold or
             prediction.predicted_ci_change < self.degradation_threshold) and
            prediction.confidence >= self.confidence_threshold
        )

        if not should_adjust:
            # Check for fast track opportunity (high trust, high predicted CI)
            if (prediction.predicted_ci_after >= 0.85 and
                relationship.current_trust.average() >= 0.8 and
                relationship.total_interactions > 50 and
                prediction.predicted_ci_change >= 0):
                return self._fast_track(prediction, relationship)

            # No adjustment needed if CI will stay acceptable
            return self._no_adjustment(prediction)

        # Select adjustment strategy based on risks
        strategy = self._select_strategy(prediction, relationship)

        return self._apply_strategy(strategy, prediction, relationship)

    def _select_strategy(
        self,
        prediction: CoherencePrediction,
        relationship: RelationshipHistory
    ) -> VerificationStrategy:
        """Select appropriate verification strategy."""

        # Critical risks require deferral
        critical_risks = {
            CoherenceRiskPattern.DECEPTION_DETECTED,
            CoherenceRiskPattern.GROUNDING_FAILURE,
            CoherenceRiskPattern.STANCE_INVERSION
        }

        if any(r in critical_risks for r in prediction.risk_patterns):
            if prediction.risk_score > 0.8:
                return VerificationStrategy.DEFER_INTERACTION

        # Grounding issues
        if CoherenceRiskPattern.GROUNDING_FAILURE in prediction.risk_patterns:
            return VerificationStrategy.INCREASE_GROUNDING_CHECKS

        # Claim mismatches
        if CoherenceRiskPattern.CLAIM_ACTION_MISMATCH in prediction.risk_patterns:
            return VerificationStrategy.REQUEST_PROOF

        # Multiple moderate risks
        if len(prediction.risk_patterns) >= 3:
            return VerificationStrategy.REQUIRE_WITNESSES

        # Default: heightened scrutiny
        return VerificationStrategy.HEIGHTENED_SCRUTINY

    def _apply_strategy(
        self,
        strategy: VerificationStrategy,
        prediction: CoherencePrediction,
        relationship: RelationshipHistory
    ) -> AdjustedVerificationRequirements:
        """Apply selected strategy."""

        if strategy == VerificationStrategy.DEFER_INTERACTION:
            return AdjustedVerificationRequirements(
                strategy=strategy,
                requirements={
                    "defer": True,
                    "defer_reason": "High risk of significant CI degradation",
                    "defer_until": "trust_recovery_or_explanation"
                },
                expected_ci_protection=abs(prediction.predicted_ci_change),
                reasoning=(
                    f"Risk score {prediction.risk_score:.2f} too high. "
                    f"Predicted CI drop {prediction.predicted_ci_change:.2f}. "
                    f"Defer until relationship stabilizes."
                )
            )

        elif strategy == VerificationStrategy.INCREASE_GROUNDING_CHECKS:
            return AdjustedVerificationRequirements(
                strategy=strategy,
                requirements={
                    "grounding_frequency": "every_interaction",
                    "min_grounding_ci": 0.8,
                    "require_witnesses": True,
                    "spatial_validation": True
                },
                expected_ci_protection=0.15,
                reasoning=(
                    "Grounding coherence issues detected. "
                    "Require high-confidence grounding validation."
                )
            )

        elif strategy == VerificationStrategy.REQUEST_PROOF:
            return AdjustedVerificationRequirements(
                strategy=strategy,
                requirements={
                    "proof_required": True,
                    "proof_type": "cryptographic_signature_or_witness",
                    "claim_verification": "all_claims",
                    "commitment_tracking": True
                },
                expected_ci_protection=0.12,
                reasoning=(
                    "Claim-action mismatches detected in history. "
                    "Require proof for all claims."
                )
            )

        elif strategy == VerificationStrategy.REQUIRE_WITNESSES:
            return AdjustedVerificationRequirements(
                strategy=strategy,
                requirements={
                    "min_witnesses": 2,
                    "witness_trust_threshold": 0.7,
                    "cross_validate_witnesses": True
                },
                expected_ci_protection=0.10,
                reasoning=(
                    f"Multiple risk patterns detected ({len(prediction.risk_patterns)}). "
                    "Require witness validation."
                )
            )

        elif strategy == VerificationStrategy.HEIGHTENED_SCRUTINY:
            return AdjustedVerificationRequirements(
                strategy=strategy,
                requirements={
                    "claim_verification": "significant_claims",
                    "behavioral_monitoring": True,
                    "timing_validation": True,
                    "stance_tracking": "per_interaction"
                },
                expected_ci_protection=0.08,
                reasoning=(
                    f"Predicted CI change {prediction.predicted_ci_change:.2f}. "
                    "Increase monitoring and validation."
                )
            )

        else:  # Should not reach here
            return self._no_adjustment(prediction)

    def _fast_track(
        self,
        prediction: CoherencePrediction,
        relationship: RelationshipHistory
    ) -> AdjustedVerificationRequirements:
        """Fast track for high-trust, low-risk relationships."""
        return AdjustedVerificationRequirements(
            strategy=VerificationStrategy.FAST_TRACK,
            requirements={
                "minimal_verification": True,
                "trust_based_approval": True,
                "monitoring_only": True
            },
            expected_ci_protection=0.0,
            reasoning=(
                f"High trust ({relationship.current_trust.average():.2f}), "
                f"high CI ({prediction.predicted_ci_after:.2f}), "
                f"extensive history ({relationship.total_interactions} interactions). "
                "Fast track approved."
            )
        )

    def _no_adjustment(
        self,
        prediction: CoherencePrediction
    ) -> AdjustedVerificationRequirements:
        """No adjustment needed."""
        return AdjustedVerificationRequirements(
            strategy=VerificationStrategy.STANDARD_VERIFICATION,
            requirements={"standard_protocols": True},
            expected_ci_protection=0.0,
            reasoning=(
                f"Predicted CI {prediction.predicted_ci_after:.2f} within acceptable range. "
                "Standard verification sufficient."
            )
        )


# Example usage and demonstration
if __name__ == "__main__":
    print("=== Relationship Coherence EP Demonstration ===\n")

    # Create predictor
    predictor = RelationshipCoherencePredictor()
    adjuster = CoherenceVerificationAdjuster()

    # Example 1: Stable collaborative relationship
    print("Example 1: Stable Collaborative Relationship")
    print("-" * 60)

    stable_rel = RelationshipHistory(
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

    normal_interaction = InteractionCharacteristics(
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

    prediction = predictor.predict_coherence(stable_rel, normal_interaction)
    adjustment = adjuster.adjust_verification(prediction, stable_rel)

    print(f"Relationship: {stable_rel.relationship_lct}")
    print(f"Current CI: {stable_rel.current_ci:.2f}")
    print(f"Current Trust: {stable_rel.current_trust.average():.2f}")
    print(f"Stance: {stable_rel.current_stance.dominant_stance()}")
    print(f"\nPredicted CI Change: {prediction.predicted_ci_change:+.2f}")
    print(f"Predicted CI After: {prediction.predicted_ci_after:.2f}")
    print(f"Confidence: {prediction.confidence:.2f}")
    print(f"Risk Score: {prediction.risk_score:.2f}")
    print(f"Risk Patterns: {[r.value for r in prediction.risk_patterns]}")
    print(f"\nReasoning: {prediction.reasoning}")
    print(f"\nVerification Strategy: {adjustment.strategy.value}")
    print(f"Adjustment Reasoning: {adjustment.reasoning}")
    print()

    # Example 2: Declining relationship with risks
    print("\nExample 2: Declining Relationship with Risk Patterns")
    print("-" * 60)

    risky_rel = RelationshipHistory(
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

    risky_interaction = InteractionCharacteristics(
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

    prediction2 = predictor.predict_coherence(risky_rel, risky_interaction)
    adjustment2 = adjuster.adjust_verification(prediction2, risky_rel)

    print(f"Relationship: {risky_rel.relationship_lct}")
    print(f"Current CI: {risky_rel.current_ci:.2f}")
    print(f"Current Trust: {risky_rel.current_trust.average():.2f}")
    print(f"Stance: {risky_rel.current_stance.dominant_stance()}")
    print(f"\nPredicted CI Change: {prediction2.predicted_ci_change:+.2f}")
    print(f"Predicted CI After: {prediction2.predicted_ci_after:.2f}")
    print(f"Confidence: {prediction2.confidence:.2f}")
    print(f"Risk Score: {prediction2.risk_score:.2f}")
    print(f"Risk Patterns Detected:")
    for risk in prediction2.risk_patterns:
        print(f"  - {risk.value}")
    print(f"\nReasoning: {prediction2.reasoning}")
    print(f"\nVerification Strategy: {adjustment2.strategy.value}")
    print(f"Requirements:")
    for k, v in adjustment2.requirements.items():
        print(f"  {k}: {v}")
    print(f"Expected CI Protection: {adjustment2.expected_ci_protection:+.2f}")
    print(f"Adjustment Reasoning: {adjustment2.reasoning}")

    print("\n=== Demonstration Complete ===")
