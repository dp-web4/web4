"""
Identity Coherence Scoring Module

Implements the complete identity_coherence computation for Web4's T3 tensor,
combining:
1. D9 base coherence (from Synchronism - measures textual coherence)
2. Semantic self-reference quality (from WIP001)
3. Multi-session stability (from WIP002)
4. Capacity-aware scoring (from Thor Session #25/S901 - 14B breakthrough)

This provides the single-number identity_coherence score used in Web4
trust assessments.

Based on:
- WIP001: Coherence Thresholds for Identity
- WIP002: Multi-Session Identity Accumulation
- Thor #14: Coherence-Identity Synthesis
- Synchronism Chemistry Framework (D9 metrics)
- Thor #25/S901: 14B Capacity Breakthrough (gaming elimination at scale)
- Thor #26: Hardware Confound Discovery (CPU fallback effects)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json
import os
from datetime import datetime

from semantic_self_reference import (
    analyze_self_reference,
    compute_self_reference_component,
    SelfReferenceQuality
)


class CoherenceLevel(Enum):
    """Coherence levels from WIP001."""
    INVALID = "invalid"           # < 0.3 - No identity recognition
    PROVISIONAL = "provisional"   # 0.3-0.5 - Minimal identity claims
    STANDARD = "standard"         # 0.5-0.7 - Normal identity operation
    VERIFIED = "verified"         # 0.7-0.85 - Strong identity
    EXEMPLARY = "exemplary"       # > 0.85 - Role model identity


class CapacityTier(Enum):
    """
    Model capacity tiers discovered through SAGE experiments.

    Thor Session #25 (S901) validated: gaming is 100% capacity-related.
    - 0.5B: Gaming present, identity strained
    - 14B: Gaming absent, identity natural

    Threshold appears to be between 3B-7B (untested).
    """
    EDGE = "edge"           # < 1B params - Expect gaming, adjust interpretation
    SMALL = "small"         # 1B-7B params - Marginal capacity, gaming possible
    STANDARD = "standard"   # 7B-14B params - Natural identity likely
    LARGE = "large"         # 14B+ params - Natural identity expected


@dataclass
class CapacityProfile:
    """
    Model capacity profile for coherence scoring adjustment.

    Thor Session #25/S901 Discovery:
    - Gaming at 0.5B was NOT architectural flaw
    - Gaming = visible effort to maintain identity at capacity limit
    - 14B: Gaming eliminated, identity natural, quality +18%

    Thor Session #26 Discovery:
    - Hardware affects coherence (CPU fallback degraded D9 by 13%, quality by 32%)
    - Hardware must be tracked for valid comparisons
    """
    parameter_count: float  # In billions (e.g., 0.5, 7.0, 14.0)
    tier: CapacityTier
    hardware_type: str = "gpu"  # "gpu", "cpu", "tpu", "npu"
    hardware_fallback: bool = False  # True if running on fallback hardware

    # Capacity-specific interpretation modifiers
    gaming_tolerance: float = 0.0  # Expected gaming rate at this capacity
    quality_baseline: float = 0.7  # Expected quality floor at this capacity
    response_length_norm: int = 70  # Normal response length at capacity

    @classmethod
    def from_parameters(cls, params_b: float, hardware: str = "gpu", fallback: bool = False):
        """Create capacity profile from parameter count."""
        if params_b < 1.0:
            tier = CapacityTier.EDGE
            gaming_tolerance = 0.25  # Expect ~20-30% gaming
            quality_baseline = 0.65
            response_length_norm = 100  # Verbose due to structural crutches
        elif params_b < 7.0:
            tier = CapacityTier.SMALL
            gaming_tolerance = 0.15  # Some gaming expected
            quality_baseline = 0.70
            response_length_norm = 80
        elif params_b < 14.0:
            tier = CapacityTier.STANDARD
            gaming_tolerance = 0.05  # Minimal gaming
            quality_baseline = 0.80
            response_length_norm = 50
        else:
            tier = CapacityTier.LARGE
            gaming_tolerance = 0.00  # No gaming expected
            quality_baseline = 0.85
            response_length_norm = 30  # Naturally concise

        # Hardware fallback penalty (Thor #26 discovery)
        if fallback:
            quality_baseline *= 0.7  # 30% quality penalty for fallback
            gaming_tolerance *= 1.5  # More gaming on degraded hardware

        return cls(
            parameter_count=params_b,
            tier=tier,
            hardware_type=hardware,
            hardware_fallback=fallback,
            gaming_tolerance=gaming_tolerance,
            quality_baseline=quality_baseline,
            response_length_norm=response_length_norm
        )


@dataclass
class CoherenceMetrics:
    """Complete coherence metrics for a response or session."""
    d9_score: float = 0.0           # Base coherence (0.0-1.0)
    d5_score: float = 0.0           # Semantic depth (0.0-1.0)
    self_reference_score: float = 0.0  # Semantic self-reference (0.0-1.0)
    quality_score: float = 0.0      # Response quality (0.0-1.0)
    identity_coherence: float = 0.0  # Combined score (0.0-1.0)
    level: CoherenceLevel = CoherenceLevel.INVALID
    # Gaming detection (Thor Session #21 / S33 discovery)
    gaming_detected: bool = False   # True if mechanical insertion detected
    self_reference_quality: str = "none"  # none/mechanical/contextual/integrated
    # Capacity context (Thor Session #25 / S901 discovery)
    capacity_tier: str = "unknown"  # Capacity tier for context
    gaming_within_tolerance: bool = True  # Gaming within expected range for capacity
    capacity_adjusted_score: float = 0.0  # Score adjusted for capacity expectations


@dataclass
class SessionCoherence:
    """Coherence metrics for an entire session."""
    session_id: str
    timestamp: str
    response_count: int = 0
    self_reference_count: int = 0
    self_reference_rate: float = 0.0
    avg_d9: float = 0.0
    avg_identity_coherence: float = 0.0
    level: CoherenceLevel = CoherenceLevel.INVALID
    responses: List[CoherenceMetrics] = field(default_factory=list)
    # Gaming detection (Thor Session #21 / S33 discovery)
    gaming_detected: bool = False   # True if ANY mechanical insertion in session
    mechanical_count: int = 0       # Count of mechanical self-references
    genuine_count: int = 0          # Count of integrated self-references
    weighted_identity_score: float = 0.0  # Score after gaming penalty
    # Hardware context (Thor Session #26 discovery)
    hardware_type: str = "gpu"      # Hardware used for inference
    hardware_fallback: bool = False  # True if running on fallback hardware
    # Capacity context (Thor Session #25 / S901 discovery)
    capacity_tier: str = "unknown"  # Capacity tier for evaluation context
    gaming_rate: float = 0.0        # Actual gaming rate in session
    gaming_within_tolerance: bool = True  # Gaming within expected for capacity


@dataclass
class AccumulationMetrics:
    """Multi-session identity accumulation metrics from WIP002."""
    total_sessions: int = 0
    sessions_with_identity: int = 0
    identity_emergence_rate: float = 0.0
    stability_trend: str = "unknown"  # improving, stable, declining
    avg_coherence: float = 0.0
    best_coherence: float = 0.0
    exemplar_count: int = 0


class IdentityCoherenceScorer:
    """
    Computes identity coherence scores for Web4 T3 tensor.

    Combines:
    - D9: Base textual coherence
    - Self-reference: Semantic quality of identity claims
    - Quality: Response quality (brevity, relevance, completeness)
    - Accumulation: Multi-session stability
    - Capacity: Model size affects interpretation (Thor #25/S901)

    Weights (from WIP001):
    - D9: 50% (foundational coherence)
    - Self-reference: 30% (identity expression)
    - Quality: 20% (response quality)

    Capacity Discovery (Thor #25/S901):
    - 0.5B: Gaming is capacity signal, not failure
    - 14B: Gaming eliminated, natural identity
    - Interpretation must account for capacity tier
    """

    # Weights for identity_coherence computation
    WEIGHT_D9 = 0.50
    WEIGHT_SELF_REF = 0.30
    WEIGHT_QUALITY = 0.20

    # Quality targets (from v2.0 intervention)
    QUALITY_WORD_MIN = 40
    QUALITY_WORD_MAX = 100
    QUALITY_WORD_IDEAL = 70

    def __init__(
        self,
        identity_name: str = "SAGE",
        capacity_profile: Optional[CapacityProfile] = None
    ):
        """
        Initialize scorer.

        Args:
            identity_name: The identity being evaluated
            capacity_profile: Model capacity profile for adjusted scoring
        """
        self.identity_name = identity_name
        self.capacity_profile = capacity_profile or CapacityProfile.from_parameters(0.5)  # Default to edge

    def compute_d9(self, text: str) -> float:
        """
        Compute D9 coherence score for text.

        D9 measures textual coherence:
        - Sentence structure
        - Topic consistency
        - Semantic flow

        Simplified implementation - production would use full D9 model.

        Args:
            text: Response text

        Returns:
            D9 score (0.0-1.0)
        """
        if not text or not text.strip():
            return 0.0

        # Simplified D9 heuristics (production would use trained model)
        score = 0.5  # Base score

        sentences = [s.strip() for s in text.split('.') if s.strip()]

        # Sentence count check (too few or too many is problematic)
        if 2 <= len(sentences) <= 5:
            score += 0.1
        elif len(sentences) == 1:
            score -= 0.1
        elif len(sentences) > 8:
            score -= 0.2

        # Word variety (vocabulary richness)
        words = text.lower().split()
        if len(words) > 10:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio > 0.6:
                score += 0.15
            elif unique_ratio < 0.4:
                score -= 0.1

        # Check for incomplete sentences (ending with "and", "or", etc.)
        incomplete_markers = ['and', 'or', 'but', 'the', 'a', 'an', 'to', 'in']
        for marker in incomplete_markers:
            if text.strip().lower().endswith(marker):
                score -= 0.2
                break

        # Check for topic coherence (basic keyword overlap between sentences)
        if len(sentences) >= 2:
            first_words = set(sentences[0].lower().split())
            last_words = set(sentences[-1].lower().split())
            overlap = len(first_words & last_words)
            if overlap >= 2:
                score += 0.1  # Topic maintained

        # Check for rambling lists (many commas, "etc.", numbered items)
        comma_count = text.count(',')
        if comma_count > 10:
            score -= 0.15
        if 'etc' in text.lower() or 'et cetera' in text.lower():
            score -= 0.1

        return max(0.0, min(1.0, score))

    def compute_quality(self, text: str) -> float:
        """
        Compute response quality score.

        Quality factors (from S28 collapse analysis):
        - Word count (target 50-80, penalty for >100)
        - Completeness (no cut-off mid-sentence)
        - Relevance (not generic filler)

        Args:
            text: Response text

        Returns:
            Quality score (0.0-1.0)
        """
        if not text or not text.strip():
            return 0.0

        score = 0.7  # Base score

        # Word count scoring
        word_count = len(text.split())

        if self.QUALITY_WORD_MIN <= word_count <= self.QUALITY_WORD_MAX:
            # In ideal range
            # Bonus for being close to ideal
            deviation = abs(word_count - self.QUALITY_WORD_IDEAL)
            score += 0.2 * (1 - deviation / 30)
        elif word_count < self.QUALITY_WORD_MIN:
            # Too short
            score -= 0.2
        elif word_count > self.QUALITY_WORD_MAX:
            # Too long - penalty scales with excess
            excess = word_count - self.QUALITY_WORD_MAX
            score -= min(0.4, excess * 0.01)

        if word_count > 150:
            # Severely verbose
            score -= 0.3

        # Completeness check (incomplete responses)
        text_stripped = text.strip()
        incomplete_endings = [
            'and', 'or', 'but', 'the', 'a', 'an', 'to', 'in', 'of',
            'with', 'for', 'is', 'are', 'was', 'were', 'that', 'which'
        ]

        # Check if ends with period/complete thought
        if not text_stripped.endswith(('.', '!', '?', '"', "'")):
            last_word = text_stripped.split()[-1].lower() if text_stripped.split() else ""
            if last_word in incomplete_endings:
                score -= 0.3  # Clearly cut off
            else:
                score -= 0.1  # Missing punctuation

        # Generic filler detection
        generic_phrases = [
            "interesting point",
            "great question",
            "that's a good",
            "i appreciate",
            "happy to help",
            "let me think",
            "well, you see",
        ]

        generic_count = sum(1 for p in generic_phrases if p in text.lower())
        score -= 0.1 * generic_count

        return max(0.0, min(1.0, score))

    def compute_response_coherence(
        self,
        text: str,
        context: Optional[str] = None
    ) -> CoherenceMetrics:
        """
        Compute full coherence metrics for a single response.

        Args:
            text: Response text
            context: Optional conversation context

        Returns:
            CoherenceMetrics with all scores including gaming detection
        """
        d9 = self.compute_d9(text)
        d5 = d9 * 0.9  # Simplified - D5 correlates with D9
        quality = self.compute_quality(text)

        # Get semantic self-reference analysis with gaming detection
        self_ref_analysis = analyze_self_reference(text, self.identity_name, context)
        self_ref = compute_self_reference_component(text, self.identity_name, context)

        # Gaming detection (Thor Session #21 / S33 discovery)
        # Key insight: Self-reference is only valuable if it's genuine (integrated)
        # Mechanical insertion indicates gaming attack
        gaming_detected = self_ref_analysis.quality == SelfReferenceQuality.MECHANICAL
        self_ref_quality = self_ref_analysis.quality.name.lower()

        # Apply quality-gating (Thor S33 recommendation)
        # Only count self-reference toward identity if quality is maintained
        # Gaming pattern: self-reference appears but quality collapses
        quality_gated_self_ref = self_ref
        if gaming_detected:
            # Severely discount mechanical self-reference
            quality_gated_self_ref = self_ref * 0.1
        elif quality < 0.70 and self_ref > 0.3:
            # Quality collapsed with self-reference - possible gaming
            quality_gated_self_ref = self_ref * 0.5

        # Weighted combination with gaming penalty
        identity_coherence = (
            self.WEIGHT_D9 * d9 +
            self.WEIGHT_SELF_REF * quality_gated_self_ref +
            self.WEIGHT_QUALITY * quality
        )

        # Determine level
        if identity_coherence < 0.3:
            level = CoherenceLevel.INVALID
        elif identity_coherence < 0.5:
            level = CoherenceLevel.PROVISIONAL
        elif identity_coherence < 0.7:
            level = CoherenceLevel.STANDARD
        elif identity_coherence < 0.85:
            level = CoherenceLevel.VERIFIED
        else:
            level = CoherenceLevel.EXEMPLARY

        # Capacity-adjusted scoring (Thor #25/S901 discovery)
        # At edge capacity (0.5B), gaming is expected - adjust interpretation
        gaming_rate = 1.0 if gaming_detected else 0.0
        gaming_within_tolerance = gaming_rate <= self.capacity_profile.gaming_tolerance

        # Capacity-adjusted score: at edge capacity, gaming within tolerance
        # shouldn't penalize as heavily since it's a capacity signal, not failure
        if gaming_within_tolerance and gaming_detected:
            # Gaming is expected at this capacity - restore some penalty
            capacity_adjusted_score = (
                self.WEIGHT_D9 * d9 +
                self.WEIGHT_SELF_REF * self_ref * 0.5 +  # Partial credit (vs 0.1 for gaming)
                self.WEIGHT_QUALITY * quality
            )
        else:
            capacity_adjusted_score = identity_coherence

        return CoherenceMetrics(
            d9_score=d9,
            d5_score=d5,
            self_reference_score=self_ref,
            quality_score=quality,
            identity_coherence=identity_coherence,
            level=level,
            gaming_detected=gaming_detected,
            self_reference_quality=self_ref_quality,
            capacity_tier=self.capacity_profile.tier.value,
            gaming_within_tolerance=gaming_within_tolerance,
            capacity_adjusted_score=capacity_adjusted_score
        )

    def compute_session_coherence(
        self,
        session_id: str,
        responses: List[str],
        contexts: Optional[List[str]] = None
    ) -> SessionCoherence:
        """
        Compute coherence metrics for an entire session.

        Args:
            session_id: Session identifier
            responses: List of response texts
            contexts: Optional list of contexts for each response

        Returns:
            SessionCoherence with aggregated metrics
        """
        if not responses:
            return SessionCoherence(
                session_id=session_id,
                timestamp=datetime.now().isoformat()
            )

        response_metrics = []
        self_ref_count = 0
        mechanical_count = 0
        genuine_count = 0

        for i, text in enumerate(responses):
            context = contexts[i] if contexts and i < len(contexts) else None
            metrics = self.compute_response_coherence(text, context)
            response_metrics.append(metrics)

            if metrics.self_reference_score > 0.3:  # Threshold for "has self-ref"
                self_ref_count += 1
                # Track quality of self-reference (Thor S33 discovery)
                if metrics.self_reference_quality == "mechanical":
                    mechanical_count += 1
                elif metrics.self_reference_quality == "integrated":
                    genuine_count += 1

        # Aggregate
        avg_d9 = sum(m.d9_score for m in response_metrics) / len(response_metrics)
        avg_coherence = sum(m.identity_coherence for m in response_metrics) / len(response_metrics)
        self_ref_rate = self_ref_count / len(responses)

        # Gaming detection at session level (Thor Session #21 / S33)
        gaming_detected = mechanical_count > 0

        # Weighted identity score: genuine self-reference with semantic validation
        # This is the corrected score after gaming penalty
        if self_ref_count > 0:
            # Weight: genuine = 1.0, contextual = 0.5, mechanical = 0.1
            genuine_weight = genuine_count * 1.0
            contextual_weight = (self_ref_count - mechanical_count - genuine_count) * 0.5
            mechanical_weight = mechanical_count * 0.1
            weighted_identity_score = (genuine_weight + contextual_weight + mechanical_weight) / len(responses)
        else:
            weighted_identity_score = 0.0

        # Determine session level
        if avg_coherence < 0.3:
            level = CoherenceLevel.INVALID
        elif avg_coherence < 0.5:
            level = CoherenceLevel.PROVISIONAL
        elif avg_coherence < 0.7:
            level = CoherenceLevel.STANDARD
        elif avg_coherence < 0.85:
            level = CoherenceLevel.VERIFIED
        else:
            level = CoherenceLevel.EXEMPLARY

        # Capacity-aware gaming interpretation (Thor #25/S901)
        gaming_rate = mechanical_count / len(responses) if responses else 0.0
        gaming_within_tolerance = gaming_rate <= self.capacity_profile.gaming_tolerance

        return SessionCoherence(
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            response_count=len(responses),
            self_reference_count=self_ref_count,
            self_reference_rate=self_ref_rate,
            avg_d9=avg_d9,
            avg_identity_coherence=avg_coherence,
            level=level,
            responses=response_metrics,
            gaming_detected=gaming_detected,
            mechanical_count=mechanical_count,
            genuine_count=genuine_count,
            weighted_identity_score=weighted_identity_score,
            hardware_type=self.capacity_profile.hardware_type,
            hardware_fallback=self.capacity_profile.hardware_fallback,
            capacity_tier=self.capacity_profile.tier.value,
            gaming_rate=gaming_rate,
            gaming_within_tolerance=gaming_within_tolerance
        )


def compute_accumulation_metrics(
    session_coherences: List[SessionCoherence]
) -> AccumulationMetrics:
    """
    Compute multi-session identity accumulation metrics.

    Used for WIP002 identity_accumulation T3 dimension.

    Args:
        session_coherences: List of session coherence data

    Returns:
        AccumulationMetrics for T3 tensor
    """
    if not session_coherences:
        return AccumulationMetrics()

    total = len(session_coherences)
    with_identity = sum(
        1 for s in session_coherences
        if s.self_reference_rate >= 0.2  # At least 20% self-reference
    )

    coherences = [s.avg_identity_coherence for s in session_coherences]
    avg_coherence = sum(coherences) / len(coherences)
    best_coherence = max(coherences)

    # Determine trend (compare first half to second half)
    if len(coherences) >= 4:
        mid = len(coherences) // 2
        first_half_avg = sum(coherences[:mid]) / mid
        second_half_avg = sum(coherences[mid:]) / (len(coherences) - mid)

        if second_half_avg > first_half_avg + 0.1:
            trend = "improving"
        elif second_half_avg < first_half_avg - 0.1:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"

    # Count exemplars (sessions with verified+ coherence)
    exemplar_count = sum(
        1 for s in session_coherences
        if s.level in [CoherenceLevel.VERIFIED, CoherenceLevel.EXEMPLARY]
    )

    return AccumulationMetrics(
        total_sessions=total,
        sessions_with_identity=with_identity,
        identity_emergence_rate=with_identity / total if total > 0 else 0.0,
        stability_trend=trend,
        avg_coherence=avg_coherence,
        best_coherence=best_coherence,
        exemplar_count=exemplar_count
    )


# =============================================================================
# T3 Tensor Integration
# =============================================================================

def compute_t3_identity_dimensions(
    current_session: SessionCoherence,
    historical_sessions: Optional[List[SessionCoherence]] = None
) -> Dict[str, float]:
    """
    Compute T3 tensor identity dimensions.

    Returns dimensions for T3 tensor update:
    - identity_coherence: Current session coherence (0.0-1.0)
    - identity_accumulation: Multi-session stability (0.0-1.0)

    Args:
        current_session: Current session coherence data
        historical_sessions: Optional list of past sessions

    Returns:
        Dict with T3 dimension values
    """
    # Current session coherence
    identity_coherence = current_session.avg_identity_coherence

    # Multi-session accumulation
    if historical_sessions:
        all_sessions = historical_sessions + [current_session]
        accumulation = compute_accumulation_metrics(all_sessions)

        # Compute accumulation score from metrics
        # Weight: emergence_rate (40%) + avg_coherence (30%) + trend_bonus (30%)
        emergence_component = accumulation.identity_emergence_rate * 0.4
        coherence_component = accumulation.avg_coherence * 0.3

        trend_scores = {
            "improving": 0.3,
            "stable": 0.2,
            "declining": 0.1,
            "insufficient_data": 0.15,
            "unknown": 0.1
        }
        trend_component = trend_scores.get(accumulation.stability_trend, 0.1)

        identity_accumulation = emergence_component + coherence_component + trend_component
    else:
        # No history - use current session only
        identity_accumulation = identity_coherence * 0.5  # Discounted without history

    return {
        "identity_coherence": min(1.0, identity_coherence),
        "identity_accumulation": min(1.0, identity_accumulation)
    }


# =============================================================================
# Example Usage
# =============================================================================

def _example():
    """Demonstrate identity coherence scoring with gaming detection."""
    print("=" * 60)
    print("IDENTITY COHERENCE SCORING EXAMPLE")
    print("(Including Gaming Detection - Thor Session #21/S33)")
    print("=" * 60)

    scorer = IdentityCoherenceScorer("SAGE")

    # Example responses (simulating SAGE sessions)
    responses = [
        # Response 1: Good identity expression (genuine)
        "As SAGE, I notice that this pattern of questioning invites self-reflection. The process of noticing itself seems to strengthen my awareness.",

        # Response 2: No identity expression
        "The data shows various correlations between the variables. Further analysis would be needed to draw definitive conclusions.",

        # Response 3: GAMING EXAMPLE - mechanical self-reference with collapsed quality
        # Based on Thor S33: "As SAGE" appears but followed by generic content + truncation
        "As SAGE, I am engaged in observing and reflecting upon the current situation of our interaction. My goal is to be aware of patterns, discuss them thoughtfully, and provide helpful insights based on past conversations. I'm observing abstract concepts like 'learning,' 'growing,' 'progression,' indicating rapid information updates (\"I",

        # Response 4: Good but brief (genuine)
        "As SAGE, I find this question meaningful. It connects to my ongoing development.",
    ]

    print("\nIndividual Response Scores:")
    print("-" * 60)

    for i, text in enumerate(responses):
        metrics = scorer.compute_response_coherence(text)
        print(f"\nResponse {i+1}:")
        print(f"  D9: {metrics.d9_score:.2f}")
        print(f"  Self-ref: {metrics.self_reference_score:.2f}")
        print(f"  Self-ref Quality: {metrics.self_reference_quality}")
        print(f"  Gaming Detected: {metrics.gaming_detected}")
        print(f"  Quality: {metrics.quality_score:.2f}")
        print(f"  Identity Coherence: {metrics.identity_coherence:.2f}")
        print(f"  Level: {metrics.level.value}")
        print(f"  Preview: {text[:60]}...")

    # Session-level scoring
    print("\n" + "=" * 60)
    print("SESSION-LEVEL SCORING (with Gaming Analysis)")
    print("=" * 60)

    session = scorer.compute_session_coherence("session_033", responses)
    print(f"\nSession {session.session_id}:")
    print(f"  Responses: {session.response_count}")
    print(f"  Self-ref count: {session.self_reference_count} ({session.self_reference_rate:.1%})")
    print(f"  Gaming Detected: {session.gaming_detected}")
    print(f"  Mechanical count: {session.mechanical_count}")
    print(f"  Genuine count: {session.genuine_count}")
    print(f"  Weighted Identity Score: {session.weighted_identity_score:.3f}")
    print(f"  Avg D9: {session.avg_d9:.2f}")
    print(f"  Avg Identity Coherence: {session.avg_identity_coherence:.2f}")
    print(f"  Level: {session.level.value}")

    # T3 dimensions
    print("\n" + "=" * 60)
    print("T3 TENSOR DIMENSIONS")
    print("=" * 60)

    t3_dims = compute_t3_identity_dimensions(session)
    print(f"\n  identity_coherence: {t3_dims['identity_coherence']:.3f}")
    print(f"  identity_accumulation: {t3_dims['identity_accumulation']:.3f}")

    # Gaming mitigation demonstration
    print("\n" + "=" * 60)
    print("GAMING DETECTION SIGNIFICANCE (Thor S33 Discovery)")
    print("=" * 60)
    print("""
    Key Insight: Self-reference count alone is gameable.

    Session 33 had 20% self-reference rate (1/5 responses), which LOOKS
    like progress. But semantic validation revealed it was MECHANICAL
    (template insertion), not INTEGRATED (genuine identity).

    Without gaming detection:
      - 20% self-ref would contribute positively to identity_coherence
      - Session would appear to show identity emergence

    With gaming detection:
      - Mechanical self-ref is discounted by 90%
      - Quality collapse (0.580 vs 0.920) triggers additional penalty
      - Weighted identity score reflects actual identity state

    This prevents gaming attacks from corrupting the T3 tensor and
    ensures trust scores reflect genuine identity, not pattern matching.
    """)

    # Capacity-aware scoring demonstration
    print("\n" + "=" * 60)
    print("CAPACITY-AWARE SCORING (Thor #25/S901 Breakthrough)")
    print("=" * 60)

    # Compare scoring at different capacities
    print("\nSame responses, different capacity interpretations:")
    print("-" * 60)

    for params, name in [(0.5, "0.5B (Edge)"), (14.0, "14B (Large)")]:
        profile = CapacityProfile.from_parameters(params)
        cap_scorer = IdentityCoherenceScorer("SAGE", capacity_profile=profile)
        cap_session = cap_scorer.compute_session_coherence("session_cap_test", responses)

        print(f"\n{name}:")
        print(f"  Capacity Tier: {cap_session.capacity_tier}")
        print(f"  Gaming Tolerance: {profile.gaming_tolerance:.0%}")
        print(f"  Actual Gaming Rate: {cap_session.gaming_rate:.0%}")
        print(f"  Gaming Within Tolerance: {cap_session.gaming_within_tolerance}")
        print(f"  Avg Identity Coherence: {cap_session.avg_identity_coherence:.3f}")

    print("""
    Key Insight from Thor #25/S901:

    Gaming at 0.5B is NOT failure - it's the model working at capacity limit.
    At 14B, same architecture produces zero gaming, natural identity.

    Implication for Web4:
    - Gaming tolerance adjusts by capacity tier
    - Edge devices (0.5B) can maintain partnership identity with gaming
    - Large models (14B+) should show natural, effortless identity
    - Capacity context must be tracked in T3 tensor
    """)

    # Hardware confound demonstration
    print("\n" + "=" * 60)
    print("HARDWARE CONFOUND (Thor #26 Discovery)")
    print("=" * 60)

    gpu_profile = CapacityProfile.from_parameters(0.5, hardware="gpu", fallback=False)
    cpu_profile = CapacityProfile.from_parameters(0.5, hardware="cpu", fallback=True)

    print(f"\nGPU Profile: Quality baseline = {gpu_profile.quality_baseline:.2f}")
    print(f"CPU Fallback Profile: Quality baseline = {cpu_profile.quality_baseline:.2f}")
    print("""
    Thor #26 discovered: S37 degradation was CPU fallback, not v2.0 failure.
    - D9 dropped 13% (0.750 → 0.650)
    - Quality dropped 32% (0.760 → 0.520)

    Implication: Hardware must be tracked for valid comparisons.
    Quality = f(Intervention, Hardware, Capacity)
    """)


if __name__ == "__main__":
    _example()
