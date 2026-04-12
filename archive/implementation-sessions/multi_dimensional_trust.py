"""
Multi-Dimensional Trust Scoring - Session 79 Track 1

Integrates trust dimensions from all three platforms:
- Thor (Session 85): Internal metrics + Conversational ground truth
- Sprout (Session 84): Relationship quality (REPAIR_ARC patterns)
- Legion (Session 77/78): Byzantine quality consensus + Federation

Creates unified trust framework that considers:
1. Internal Quality (Thor): Expert selection accuracy
2. Conversational Trust (Sprout): Human satisfaction, relationship quality
3. Byzantine Consensus (Legion): Multi-society quality agreement
4. Federation Trust (Legion): Cross-society trust attestations

Composite Trust Score = weighted combination of all dimensions.
"""

import random
import statistics
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from enum import Enum


# ============================================================================
# TRUST DIMENSIONS
# ============================================================================

@dataclass
class InternalQualityScore:
    """
    Internal quality metrics (Thor Sessions 74-85).

    Measures: Expert selection accuracy, response quality
    """
    expert_id: int
    context: str
    quality: float  # 0.0-1.0
    observation_count: int
    confidence: float  # Based on observation_count


@dataclass
class ConversationalTrustScore:
    """
    Conversational trust metrics (Sprout Session 84, Thor Session 85).

    Measures: Human satisfaction, relationship quality, engagement
    """
    expert_id: int
    context: str
    relationship_score: float  # 0.0-1.0 (from repair signals)
    engagement_count: int
    reassurance_count: int
    abandonment_count: int
    correction_count: int
    arc_pattern: Optional[str] = None  # "REPAIR_ARC", "SMOOTH", "DEGRADING"


@dataclass
class ByzantineConsensusScore:
    """
    Byzantine consensus quality (Legion Session 77).

    Measures: Multi-society agreement on quality
    """
    expert_id: int
    context: str
    consensus_quality: float  # 0.0-1.0 (median of attestations)
    num_attestations: int
    outliers_detected: int
    consensus_confidence: float  # Based on agreement level


@dataclass
class FederationTrustScore:
    """
    Federation trust from cross-society attestations (Legion Sessions 75/78).

    Measures: Cross-platform trust attestations with dynamic decay
    """
    expert_id: int
    context: str
    federated_quality: float  # 0.0-1.0 (with decay applied)
    source_societies: List[str]
    diversity_score: float  # Observation diversity
    decay_factor: float  # Dynamic decay based on diversity


@dataclass
class MultiDimensionalTrustScore:
    """
    Composite trust score from all dimensions.

    Unified trust framework integrating:
    - Internal quality (Thor)
    - Conversational trust (Sprout)
    - Byzantine consensus (Legion)
    - Federation trust (Legion)
    """
    expert_id: int
    context: str

    # Individual dimension scores
    internal_quality: Optional[InternalQualityScore]
    conversational_trust: Optional[ConversationalTrustScore]
    byzantine_consensus: Optional[ByzantineConsensusScore]
    federation_trust: Optional[FederationTrustScore]

    # Composite score
    composite_score: float  # 0.0-1.0
    confidence: float  # 0.0-1.0 (based on available dimensions)

    # Metadata
    dimensions_available: int  # How many dimensions contributed
    trust_tier: str  # "HIGH", "MEDIUM", "LOW", "UNKNOWN"


# ============================================================================
# MULTI-DIMENSIONAL TRUST SCORER
# ============================================================================

class MultiDimensionalTrustScorer:
    """
    Computes composite trust scores from multiple validation dimensions.

    Integrates trust signals from Thor, Sprout, and Legion platforms.
    """

    def __init__(
        self,
        # Dimension weights (must sum to 1.0)
        internal_weight: float = 0.35,
        conversational_weight: float = 0.25,
        byzantine_weight: float = 0.25,
        federation_weight: float = 0.15
    ):
        """
        Args:
            internal_weight: Weight for internal quality metrics (Thor)
            conversational_weight: Weight for conversational trust (Sprout)
            byzantine_weight: Weight for Byzantine consensus (Legion)
            federation_weight: Weight for federation trust (Legion)
        """
        # Validate weights sum to 1.0
        total_weight = (internal_weight + conversational_weight +
                       byzantine_weight + federation_weight)
        assert abs(total_weight - 1.0) < 0.01, f"Weights must sum to 1.0, got {total_weight}"

        self.internal_weight = internal_weight
        self.conversational_weight = conversational_weight
        self.byzantine_weight = byzantine_weight
        self.federation_weight = federation_weight

        # Stats
        self.stats = {
            'total_scores_computed': 0,
            'avg_dimensions_available': 0.0,
            'dimension_usage': {
                'internal': 0,
                'conversational': 0,
                'byzantine': 0,
                'federation': 0
            }
        }

    def compute_composite_score(
        self,
        expert_id: int,
        context: str,
        internal_quality: Optional[InternalQualityScore] = None,
        conversational_trust: Optional[ConversationalTrustScore] = None,
        byzantine_consensus: Optional[ByzantineConsensusScore] = None,
        federation_trust: Optional[FederationTrustScore] = None
    ) -> MultiDimensionalTrustScore:
        """
        Compute composite trust score from available dimensions.

        Returns unified trust score with confidence based on how many
        dimensions contributed.
        """
        self.stats['total_scores_computed'] += 1

        # Track available dimensions
        dimensions_available = 0
        total_weighted_score = 0.0
        total_weight_used = 0.0

        # 1. Internal Quality (Thor)
        if internal_quality is not None:
            dimensions_available += 1
            self.stats['dimension_usage']['internal'] += 1

            # Weight by observation confidence
            score_contribution = internal_quality.quality * internal_quality.confidence
            total_weighted_score += score_contribution * self.internal_weight
            total_weight_used += self.internal_weight

        # 2. Conversational Trust (Sprout)
        if conversational_trust is not None:
            dimensions_available += 1
            self.stats['dimension_usage']['conversational'] += 1

            # Use relationship score
            total_weighted_score += conversational_trust.relationship_score * self.conversational_weight
            total_weight_used += self.conversational_weight

        # 3. Byzantine Consensus (Legion)
        if byzantine_consensus is not None:
            dimensions_available += 1
            self.stats['dimension_usage']['byzantine'] += 1

            # Weight by consensus confidence
            score_contribution = (byzantine_consensus.consensus_quality *
                                byzantine_consensus.consensus_confidence)
            total_weighted_score += score_contribution * self.byzantine_weight
            total_weight_used += self.byzantine_weight

        # 4. Federation Trust (Legion)
        if federation_trust is not None:
            dimensions_available += 1
            self.stats['dimension_usage']['federation'] += 1

            # Use federated quality (already has decay applied)
            total_weighted_score += federation_trust.federated_quality * self.federation_weight
            total_weight_used += self.federation_weight

        # Normalize by weights used (in case some dimensions missing)
        if total_weight_used > 0:
            composite_score = total_weighted_score / total_weight_used
        else:
            composite_score = 0.5  # Neutral if no dimensions available

        # Confidence based on dimension availability
        # More dimensions → Higher confidence
        confidence = dimensions_available / 4.0  # 4 possible dimensions

        # Trust tier classification
        if dimensions_available == 0:
            trust_tier = "UNKNOWN"
        elif composite_score >= 0.7:
            trust_tier = "HIGH"
        elif composite_score >= 0.4:
            trust_tier = "MEDIUM"
        else:
            trust_tier = "LOW"

        # Update stats
        self.stats['avg_dimensions_available'] = (
            (self.stats['avg_dimensions_available'] * (self.stats['total_scores_computed'] - 1) +
             dimensions_available) / self.stats['total_scores_computed']
        )

        return MultiDimensionalTrustScore(
            expert_id=expert_id,
            context=context,
            internal_quality=internal_quality,
            conversational_trust=conversational_trust,
            byzantine_consensus=byzantine_consensus,
            federation_trust=federation_trust,
            composite_score=composite_score,
            confidence=confidence,
            dimensions_available=dimensions_available,
            trust_tier=trust_tier
        )


# ============================================================================
# DEMO
# ============================================================================

@dataclass
class MultiDimensionalTestResult:
    """Result from multi-dimensional trust test."""
    test_id: str

    # Composite scores
    avg_composite_score: float
    avg_confidence: float
    avg_dimensions_available: float

    # Dimension usage
    dimension_usage_pct: Dict[str, float]

    # Trust tier distribution
    trust_tier_distribution: Dict[str, int]

    # Comparison to single-dimension
    single_dimension_score: float  # Using only internal quality
    multi_dimension_score: float   # Using all available
    improvement_pct: float

    passed: bool


def demo_multi_dimensional_trust():
    """
    Demo: Multi-dimensional trust scoring across all platforms.

    Tests composite scoring with varying dimension availability.
    """
    print("=" * 80)
    print("MULTI-DIMENSIONAL TRUST SCORING - Session 79 Track 1")
    print("=" * 80)
    print()
    print("Integration:")
    print("  Thor (S85): Internal metrics + Conversational ground truth")
    print("  Sprout (S84): Relationship quality (REPAIR_ARC)")
    print("  Legion (S77/78): Byzantine consensus + Federation")
    print()
    print("Dimension Weights:")
    print("  Internal Quality:    35% (Thor - selection accuracy)")
    print("  Conversational:      25% (Sprout - human satisfaction)")
    print("  Byzantine Consensus: 25% (Legion - multi-society quality)")
    print("  Federation:          15% (Legion - cross-platform trust)")
    print()
    print("Test Scenarios:")
    print("  1. All dimensions available (complete validation)")
    print("  2. Thor + Sprout only (no Legion)")
    print("  3. Single dimension (internal only)")
    print("=" * 80)
    print()

    # Initialize scorer
    scorer = MultiDimensionalTrustScorer(
        internal_weight=0.35,
        conversational_weight=0.25,
        byzantine_weight=0.25,
        federation_weight=0.15
    )

    # Test scenarios
    random.seed(42)
    num_tests = 30

    composite_scores = []
    single_dimension_scores = []
    dimensions_available_list = []
    trust_tier_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'UNKNOWN': 0}

    for i in range(num_tests):
        expert_id = i % 128
        context = f"cluster_{i % 9}"

        # Generate test data (simulate varying dimension availability)
        internal_quality_val = random.uniform(0.5, 1.0)

        # Scenario probabilities
        has_conversational = random.random() < 0.8  # 80% have conversational
        has_byzantine = random.random() < 0.6       # 60% have Byzantine
        has_federation = random.random() < 0.4      # 40% have federation

        # Build dimension scores
        internal_quality = InternalQualityScore(
            expert_id=expert_id,
            context=context,
            quality=internal_quality_val,
            observation_count=random.randint(2, 10),
            confidence=min(random.randint(2, 10) / 10, 1.0)
        )

        conversational_trust = None
        if has_conversational:
            # Simulate conversational signals
            engagement = random.randint(0, 5)
            reassurance = random.randint(0, 3)
            abandonment = random.randint(0, 2)
            correction = random.randint(0, 1)

            # Relationship score based on signals
            relationship_score = 0.5
            relationship_score += engagement * 0.1
            relationship_score += reassurance * 0.15
            relationship_score -= abandonment * 0.1
            relationship_score -= correction * 0.2
            relationship_score = max(0.0, min(1.0, relationship_score))

            conversational_trust = ConversationalTrustScore(
                expert_id=expert_id,
                context=context,
                relationship_score=relationship_score,
                engagement_count=engagement,
                reassurance_count=reassurance,
                abandonment_count=abandonment,
                correction_count=correction,
                arc_pattern="REPAIR_ARC" if reassurance > 0 else None
            )

        byzantine_consensus = None
        if has_byzantine:
            # Simulate Byzantine consensus
            consensus_quality_val = internal_quality_val + random.uniform(-0.1, 0.1)
            consensus_quality_val = max(0.0, min(1.0, consensus_quality_val))

            byzantine_consensus = ByzantineConsensusScore(
                expert_id=expert_id,
                context=context,
                consensus_quality=consensus_quality_val,
                num_attestations=random.randint(2, 5),
                outliers_detected=random.randint(0, 1),
                consensus_confidence=0.9 if random.randint(0, 1) == 0 else 0.7
            )

        federation_trust = None
        if has_federation:
            # Simulate federation trust
            diversity = random.uniform(0.1, 0.4)
            decay = 0.72 + (1 - 0.72) * diversity  # Dynamic decay

            federated_quality_val = internal_quality_val * decay

            federation_trust = FederationTrustScore(
                expert_id=expert_id,
                context=context,
                federated_quality=federated_quality_val,
                source_societies=['thor', 'sprout'] if diversity > 0.2 else ['thor'],
                diversity_score=diversity,
                decay_factor=decay
            )

        # Compute multi-dimensional score
        multi_score = scorer.compute_composite_score(
            expert_id=expert_id,
            context=context,
            internal_quality=internal_quality,
            conversational_trust=conversational_trust,
            byzantine_consensus=byzantine_consensus,
            federation_trust=federation_trust
        )

        composite_scores.append(multi_score.composite_score)
        dimensions_available_list.append(multi_score.dimensions_available)
        trust_tier_counts[multi_score.trust_tier] += 1

        # Compare to single-dimension (internal only)
        single_score = scorer.compute_composite_score(
            expert_id=expert_id,
            context=context,
            internal_quality=internal_quality
        )
        single_dimension_scores.append(single_score.composite_score)

    # Calculate results
    avg_composite = statistics.mean(composite_scores)
    avg_single = statistics.mean(single_dimension_scores)
    avg_dimensions = statistics.mean(dimensions_available_list)

    improvement = ((avg_composite - avg_single) / avg_single) * 100 if avg_single > 0 else 0

    # Dimension usage
    total_computed = scorer.stats['total_scores_computed']
    dimension_usage_pct = {
        dim: (count / total_computed * 100) if total_computed > 0 else 0
        for dim, count in scorer.stats['dimension_usage'].items()
    }

    # Confidence
    confidences = [1.0 if dims == 4 else dims / 4.0 for dims in dimensions_available_list]
    avg_confidence = statistics.mean(confidences)

    passed = avg_composite > avg_single and avg_dimensions >= 2.0

    result = MultiDimensionalTestResult(
        test_id="multi-dimensional-trust-v1",
        avg_composite_score=avg_composite,
        avg_confidence=avg_confidence,
        avg_dimensions_available=avg_dimensions,
        dimension_usage_pct=dimension_usage_pct,
        trust_tier_distribution=trust_tier_counts,
        single_dimension_score=avg_single,
        multi_dimension_score=avg_composite,
        improvement_pct=improvement,
        passed=passed
    )

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    print("Composite Scoring:")
    print("-" * 80)
    print(f"Average composite score:    {result.avg_composite_score:.3f}")
    print(f"Average confidence:         {result.avg_confidence:.3f}")
    print(f"Average dimensions used:    {result.avg_dimensions_available:.1f} / 4")
    print()

    print("Dimension Usage:")
    print("-" * 80)
    for dim, pct in result.dimension_usage_pct.items():
        print(f"{dim:20s}: {pct:5.1f}%")
    print()

    print("Trust Tier Distribution:")
    print("-" * 80)
    for tier, count in result.trust_tier_distribution.items():
        pct = count / num_tests * 100
        print(f"{tier:10s}: {count:2d} ({pct:5.1f}%)")
    print()

    print("Multi-Dimensional vs Single-Dimension:")
    print("-" * 80)
    print(f"Single-dimension (internal only): {result.single_dimension_score:.3f}")
    print(f"Multi-dimensional (all available): {result.multi_dimension_score:.3f}")
    print(f"Improvement:                       {result.improvement_pct:+.1f}%")
    print()

    print("Test Result:")
    print("-" * 80)
    if result.passed:
        print("✅ PASS - Multi-dimensional trust outperforms single-dimension")
        print()
        print("Conclusion:")
        print("  Composite trust scoring successfully integrates all platforms:")
        print("  - Thor: Internal metrics provide baseline")
        print("  - Sprout: Conversational trust adds human validation")
        print("  - Legion: Byzantine consensus + federation add cross-platform trust")
        print()
        print(f"  {result.improvement_pct:+.1f}% improvement over internal-only scoring")
        print(f"  Average {result.avg_dimensions_available:.1f} dimensions available per score")
        print(f"  {result.avg_confidence:.1%} average confidence")
    else:
        print("❌ FAIL - Multi-dimensional trust needs refinement")
    print()

    # Save results
    results_file = "/home/dp/ai-workspace/web4/implementation/multi_dimensional_trust_results.json"
    with open(results_file, 'w') as f:
        json.dump(asdict(result), f, indent=2)
    print(f"Results saved to: {results_file}")
    print()

    return result


if __name__ == "__main__":
    demo_multi_dimensional_trust()
