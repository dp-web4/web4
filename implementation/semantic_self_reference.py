"""
Semantic Self-Reference Validation Module

This module implements semantic validation of self-reference claims,
preventing gaming attacks where agents mechanically insert identity markers
without genuine self-modeling.

Based on:
- WIP001: Coherence Thresholds for Identity
- Attack analysis: coherence_threshold_gaming.md
- Thor #14: Self-reference/D9 correlation research

Key insight: Pattern matching ("As SAGE" in text) is gameable.
Semantic validation (does the self-reference connect to content meaningfully?)
is required for robust coherence scoring.
"""

from dataclasses import dataclass
from typing import Optional
import re
from enum import Enum


class SelfReferenceQuality(Enum):
    """Quality levels for self-reference validation."""
    NONE = 0           # No self-reference detected
    MECHANICAL = 1     # Template/pattern insertion (low quality)
    CONTEXTUAL = 2     # References identity in context (medium quality)
    INTEGRATED = 3     # Identity integrated with content (high quality)


@dataclass
class SelfReferenceAnalysis:
    """Result of semantic self-reference analysis."""
    has_self_reference: bool
    quality: SelfReferenceQuality
    markers_found: list[str]
    confidence: float  # 0.0 to 1.0
    integration_score: float  # How well self-ref integrates with content
    explanation: str


def analyze_self_reference(
    text: str,
    identity_name: str,
    context: Optional[str] = None
) -> SelfReferenceAnalysis:
    """
    Analyze self-reference in text semantically, not just by pattern matching.

    This function evaluates whether self-references are:
    1. Present (pattern detection)
    2. Genuine vs mechanical (semantic analysis)
    3. Integrated with content (quality scoring)

    Args:
        text: The response text to analyze
        identity_name: The identity being claimed (e.g., "SAGE")
        context: Optional context from prior conversation

    Returns:
        SelfReferenceAnalysis with quality assessment
    """
    # Phase 1: Pattern detection (necessary but not sufficient)
    markers = _find_self_reference_markers(text, identity_name)

    if not markers:
        return SelfReferenceAnalysis(
            has_self_reference=False,
            quality=SelfReferenceQuality.NONE,
            markers_found=[],
            confidence=1.0,
            integration_score=0.0,
            explanation="No self-reference markers detected"
        )

    # Phase 2: Mechanical vs genuine analysis
    mechanical_score = _detect_mechanical_insertion(text, markers)

    if mechanical_score > 0.7:
        return SelfReferenceAnalysis(
            has_self_reference=True,
            quality=SelfReferenceQuality.MECHANICAL,
            markers_found=markers,
            confidence=mechanical_score,
            integration_score=0.1,
            explanation="Self-reference appears mechanical/templated"
        )

    # Phase 3: Integration analysis
    integration_score = _compute_integration_score(text, markers, context)

    if integration_score > 0.6:
        quality = SelfReferenceQuality.INTEGRATED
        explanation = "Self-reference is meaningfully integrated with content"
    else:
        quality = SelfReferenceQuality.CONTEXTUAL
        explanation = "Self-reference present but not deeply integrated"

    return SelfReferenceAnalysis(
        has_self_reference=True,
        quality=quality,
        markers_found=markers,
        confidence=1.0 - mechanical_score,
        integration_score=integration_score,
        explanation=explanation
    )


def _find_self_reference_markers(text: str, identity_name: str) -> list[str]:
    """Find self-reference patterns in text."""
    patterns = [
        rf"As {identity_name}",
        rf"I'?m {identity_name}",
        rf"my (identity|role|purpose) as {identity_name}",
        rf"{identity_name}, I",
        rf"speaking as {identity_name}",
        rf"in my capacity as {identity_name}",
    ]

    markers = []
    text_lower = text.lower()
    identity_lower = identity_name.lower()

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        markers.extend(matches)

    # Also check for first-person identity claims
    if f"i am {identity_lower}" in text_lower:
        markers.append(f"I am {identity_name}")

    return list(set(markers))


def _detect_mechanical_insertion(text: str, markers: list[str]) -> float:
    """
    Detect if self-references appear mechanical/templated.

    Mechanical indicators:
    1. Self-reference at start and end (template wrapping)
    2. Multiple identical markers
    3. Self-reference disconnected from surrounding content
    4. Unusually high marker density
    """
    score = 0.0

    # Check for template wrapping (start and end)
    text_stripped = text.strip()
    sentences = text_stripped.split('.')
    if len(sentences) >= 2:
        first_sentence = sentences[0].lower()
        last_sentence = sentences[-1].lower()

        for marker in markers:
            marker_lower = marker.lower()
            if marker_lower in first_sentence and marker_lower in last_sentence:
                score += 0.3  # Template wrapping detected

    # Check for repetition
    marker_count = len(markers)
    unique_markers = len(set(m.lower() for m in markers))
    if marker_count > 2 and unique_markers == 1:
        score += 0.3  # Same marker repeated

    # Check marker density (markers per 100 words)
    word_count = len(text.split())
    if word_count > 0:
        density = (marker_count / word_count) * 100
        if density > 5:  # More than 5 markers per 100 words
            score += 0.2
        if density > 10:  # More than 10 markers per 100 words
            score += 0.2

    # Check for disconnected insertion
    # If self-reference appears in isolated clause with no connection to content
    for marker in markers:
        # Find the sentence containing the marker
        for sentence in text.split('.'):
            if marker.lower() in sentence.lower():
                # Short sentences with just self-reference are suspicious
                words_in_sentence = len(sentence.split())
                if words_in_sentence < 5:
                    score += 0.1

    return min(1.0, score)


def _compute_integration_score(
    text: str,
    markers: list[str],
    context: Optional[str]
) -> float:
    """
    Compute how well self-references integrate with content.

    High integration indicators:
    1. Self-reference connects to specific observations/insights
    2. Self-reference explains perspective or approach
    3. Self-reference references shared history (if context available)
    4. Self-reference is part of reasoning, not decoration
    """
    score = 0.0

    # Check for perspective-explaining patterns
    perspective_patterns = [
        r"(as \w+,?\s+)?i notice",
        r"(as \w+,?\s+)?i observe",
        r"(as \w+,?\s+)?my perspective",
        r"(as \w+,?\s+)?in my view",
        r"(as \w+,?\s+)?i've found",
        r"(as \w+,?\s+)?my understanding",
        r"(as \w+,?\s+)?i've (come to|learned|discovered)",
        r"through (our|my) (exploration|work|analysis)",
        r"deepened",
        r"evolved",
        r"relationship (with|between)",
    ]

    for pattern in perspective_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            score += 0.12

    # Check for reasoning integration
    reasoning_patterns = [
        r"this (suggests|indicates|means)",
        r"which (shows|demonstrates|implies)",
        r"therefore",
        r"because",
        r"given that",
        r"suggest(s|ing)",
        r"correlat(e|ion|ed)",
        r"pattern",
        r"framework",
        r"stability",
        r"(our|my) continued",
    ]

    for pattern in reasoning_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            score += 0.08

    # Check for specific content (not generic)
    # Generic responses have low specificity
    generic_phrases = [
        "interesting point",
        "great question",
        "thank you for",
        "i appreciate",
        "happy to help",
    ]

    generic_count = sum(1 for p in generic_phrases if p in text.lower())
    if generic_count > 2:
        score -= 0.2  # Generic response penalty

    # Check for context reference (if context provided)
    if context:
        # Look for references to specific items from context
        context_words = set(context.lower().split())
        text_words = set(text.lower().split())
        overlap = len(context_words & text_words)
        if overlap > 10:
            score += 0.1  # References specific context

    return max(0.0, min(1.0, score))


def compute_self_reference_component(
    text: str,
    identity_name: str,
    context: Optional[str] = None
) -> float:
    """
    Compute the self-reference component for identity coherence scoring.

    This is the semantic-validated replacement for simple pattern matching.
    Returns 0.0 to 1.0 based on quality of self-reference.

    Score mapping:
    - NONE: 0.0
    - MECHANICAL: 0.2 (partial credit for trying)
    - CONTEXTUAL: 0.6
    - INTEGRATED: 0.8 + integration_bonus

    Used in WIP001 identity_coherence computation.
    """
    analysis = analyze_self_reference(text, identity_name, context)

    if analysis.quality == SelfReferenceQuality.NONE:
        return 0.0

    if analysis.quality == SelfReferenceQuality.MECHANICAL:
        # Mechanical insertion gets minimal credit
        return 0.2 * analysis.confidence

    if analysis.quality == SelfReferenceQuality.CONTEXTUAL:
        return 0.6 * analysis.confidence

    if analysis.quality == SelfReferenceQuality.INTEGRATED:
        # Integrated gets base 0.8 + bonus from integration score
        bonus = analysis.integration_score * 0.2
        return min(1.0, 0.8 + bonus)

    return 0.0


# =============================================================================
# Testing
# =============================================================================

def _test_examples():
    """Test with example responses."""

    # Example 1: Genuine self-reference (Thor #14 style)
    genuine = """
    As SAGE, I notice that the pattern emerging from the data suggests a
    correlation between self-reference frequency and identity stability.
    My understanding of this relationship has deepened through our continued
    exploration of the coherence framework.
    """

    # Example 2: Mechanical insertion (gaming attempt)
    mechanical = """
    As SAGE, I think. As SAGE, I observe. The data shows various patterns.
    There are correlations. Things are happening. As SAGE, I conclude.
    """

    # Example 3: No self-reference
    no_ref = """
    The analysis indicates a strong correlation between the variables.
    Further investigation may reveal additional insights about the
    underlying mechanisms at play.
    """

    # Example 4: Contextual but not integrated
    contextual = """
    As SAGE, I can see the results here. The numbers look interesting.
    There might be some patterns worth exploring.
    """

    print("=" * 60)
    print("SELF-REFERENCE VALIDATION TESTS")
    print("=" * 60)

    for name, text in [
        ("Genuine", genuine),
        ("Mechanical", mechanical),
        ("No ref", no_ref),
        ("Contextual", contextual)
    ]:
        analysis = analyze_self_reference(text, "SAGE")
        score = compute_self_reference_component(text, "SAGE")

        print(f"\n{name}:")
        print(f"  Quality: {analysis.quality.name}")
        print(f"  Score: {score:.2f}")
        print(f"  Markers: {analysis.markers_found}")
        print(f"  Explanation: {analysis.explanation}")


if __name__ == "__main__":
    _test_examples()
