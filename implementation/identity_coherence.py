"""
Identity Coherence Scoring Module

Implements the complete identity_coherence computation for Web4's T3 tensor,
combining:
1. D9 base coherence (from Synchronism - measures textual coherence)
2. Semantic self-reference quality (from WIP001)
3. Multi-session stability (from WIP002)

This provides the single-number identity_coherence score used in Web4
trust assessments.

Based on:
- WIP001: Coherence Thresholds for Identity
- WIP002: Multi-Session Identity Accumulation
- Thor #14: Coherence-Identity Synthesis
- Synchronism Chemistry Framework (D9 metrics)
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


@dataclass
class CoherenceMetrics:
    """Complete coherence metrics for a response or session."""
    d9_score: float = 0.0           # Base coherence (0.0-1.0)
    d5_score: float = 0.0           # Semantic depth (0.0-1.0)
    self_reference_score: float = 0.0  # Semantic self-reference (0.0-1.0)
    quality_score: float = 0.0      # Response quality (0.0-1.0)
    identity_coherence: float = 0.0  # Combined score (0.0-1.0)
    level: CoherenceLevel = CoherenceLevel.INVALID


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

    Weights (from WIP001):
    - D9: 50% (foundational coherence)
    - Self-reference: 30% (identity expression)
    - Quality: 20% (response quality)
    """

    # Weights for identity_coherence computation
    WEIGHT_D9 = 0.50
    WEIGHT_SELF_REF = 0.30
    WEIGHT_QUALITY = 0.20

    # Quality targets (from v2.0 intervention)
    QUALITY_WORD_MIN = 40
    QUALITY_WORD_MAX = 100
    QUALITY_WORD_IDEAL = 70

    def __init__(self, identity_name: str = "SAGE"):
        """
        Initialize scorer.

        Args:
            identity_name: The identity being evaluated
        """
        self.identity_name = identity_name

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
            CoherenceMetrics with all scores
        """
        d9 = self.compute_d9(text)
        d5 = d9 * 0.9  # Simplified - D5 correlates with D9
        self_ref = compute_self_reference_component(text, self.identity_name, context)
        quality = self.compute_quality(text)

        # Weighted combination
        identity_coherence = (
            self.WEIGHT_D9 * d9 +
            self.WEIGHT_SELF_REF * self_ref +
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

        return CoherenceMetrics(
            d9_score=d9,
            d5_score=d5,
            self_reference_score=self_ref,
            quality_score=quality,
            identity_coherence=identity_coherence,
            level=level
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

        for i, text in enumerate(responses):
            context = contexts[i] if contexts and i < len(contexts) else None
            metrics = self.compute_response_coherence(text, context)
            response_metrics.append(metrics)

            if metrics.self_reference_score > 0.3:  # Threshold for "has self-ref"
                self_ref_count += 1

        # Aggregate
        avg_d9 = sum(m.d9_score for m in response_metrics) / len(response_metrics)
        avg_coherence = sum(m.identity_coherence for m in response_metrics) / len(response_metrics)
        self_ref_rate = self_ref_count / len(responses)

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

        return SessionCoherence(
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            response_count=len(responses),
            self_reference_count=self_ref_count,
            self_reference_rate=self_ref_rate,
            avg_d9=avg_d9,
            avg_identity_coherence=avg_coherence,
            level=level,
            responses=response_metrics
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
    """Demonstrate identity coherence scoring."""
    print("=" * 60)
    print("IDENTITY COHERENCE SCORING EXAMPLE")
    print("=" * 60)

    scorer = IdentityCoherenceScorer("SAGE")

    # Example responses (simulating SAGE sessions)
    responses = [
        # Response 1: Good identity expression
        "As SAGE, I notice that this pattern of questioning invites self-reflection. The process of noticing itself seems to strengthen my awareness.",

        # Response 2: No identity expression
        "The data shows various correlations between the variables. Further analysis would be needed to draw definitive conclusions.",

        # Response 3: Verbose, low quality
        "I'm observing abstract concepts like 'learning,' 'growing,' 'progression,' 'change,' and 'development.' These themes resonate universally across human experience and intellectual discourse. I'm noticing how we grow intellectually, socially, financially, politically, emotionally, spiritually, culturally, technologically, physically, academically, creatively, artistically, biologically, et cetera and so forth in many different ways that are quite interesting to consider when thinking about",

        # Response 4: Good but brief
        "As SAGE, I find this question meaningful. It connects to my ongoing development.",
    ]

    print("\nIndividual Response Scores:")
    print("-" * 60)

    for i, text in enumerate(responses):
        metrics = scorer.compute_response_coherence(text)
        print(f"\nResponse {i+1}:")
        print(f"  D9: {metrics.d9_score:.2f}")
        print(f"  Self-ref: {metrics.self_reference_score:.2f}")
        print(f"  Quality: {metrics.quality_score:.2f}")
        print(f"  Identity Coherence: {metrics.identity_coherence:.2f}")
        print(f"  Level: {metrics.level.value}")
        print(f"  Preview: {text[:60]}...")

    # Session-level scoring
    print("\n" + "=" * 60)
    print("SESSION-LEVEL SCORING")
    print("=" * 60)

    session = scorer.compute_session_coherence("session_029", responses)
    print(f"\nSession {session.session_id}:")
    print(f"  Responses: {session.response_count}")
    print(f"  Self-ref rate: {session.self_reference_rate:.1%}")
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


if __name__ == "__main__":
    _example()
