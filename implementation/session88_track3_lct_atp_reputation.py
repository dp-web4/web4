#!/usr/bin/env python3
"""
Session 88 Track 3: LCT-ATP-Reputation Integration

**Date**: 2025-12-25
**Platform**: Legion (RTX 4090)
**Track**: 3 of 5 - Multi-Dimensional Reputation

## Integration Architecture

**Three Systems Converging**:

1. **Session 82 Track 1**: Multi-Dimensional ATP Allocation
   - ATP cost/reward based on 4-dimensional trust
   - Internal (35%), Conversational (25%), Byzantine (25%), Federation (15%)

2. **Session 87**: Hardened Byzantine Consensus
   - Production-ready quality attestation
   - 100% attack defense rate

3. **Session 88 Track 1**: LCT-Based Society Authentication
   - Cryptographic society identity
   - Dynamic registration

**This Track**: Connect all three systems:
- LCT-authenticated societies provide quality attestations
- Quality attestations feed Byzantine consensus
- Byzantine consensus scores feed ATP allocation
- ATP allocation determines resource access

## The Complete Flow

```
LCT Society Registration
  ↓
Quality Attestation (LCT-signed)
  ↓
Byzantine Consensus (hardened)
  ↓
Multi-Dimensional Trust Score
  ↓
ATP Allocation
  ↓
Resource Access
```

## Key Innovation

**Reputation = Multi-Dimensional Trust from LCT-Authenticated Attestations**

Traditional reputation: Single score based on past behavior
Web4 reputation: 4-dimensional composite from cryptographically-verified observations

Benefits:
- **Cryptographically Verified**: LCT signatures prevent forgery
- **Multi-Dimensional**: Captures different trust facets
- **Byzantine-Hardened**: Attack-resistant consensus
- **Resource-Aware**: ATP allocation reflects true trustworthiness

## Expected Results

Demonstrate full pipeline from LCT registration → ATP allocation:
1. Register societies with LCT credentials
2. Collect quality attestations
3. Compute Byzantine consensus
4. Calculate multi-dimensional trust
5. Allocate ATP based on trust
6. Validate higher-trust agents get better resource access
"""

import hashlib
import hmac
import secrets
import random
import time
import statistics
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path

# Import from previous tracks
from session88_track1_lct_society_authentication import (
    LCTIdentity,
    LCTAttestation,
    LCTSocietyAuthenticator,
    LCTQualityAttestation,
    LCTHardenedByzantineConsensus,
    ConsensusResult,
    create_test_lct_identity,
    create_attestation,
)

# ============================================================================
# Multi-Dimensional Trust (from Session 82 Track 1)
# ============================================================================

@dataclass
class InternalQualityScore:
    """Internal quality observation (within society)."""
    expert_id: int
    context: str
    quality: float
    observation_count: int
    confidence: float


@dataclass
class ConversationalTrustScore:
    """Conversational dynamics scoring."""
    expert_id: int
    context: str
    relationship_score: float
    engagement_count: int
    reassurance_count: int
    abandonment_count: int
    correction_count: int


@dataclass
class ByzantineConsensusScore:
    """Byzantine consensus from federated attestations."""
    expert_id: int
    context: str
    consensus_quality: float
    num_attestations: int
    outliers_detected: int
    consensus_confidence: float


@dataclass
class FederationTrustScore:
    """Federation-wide trust aggregation."""
    expert_id: int
    context: str
    federated_quality: float
    source_societies: List[str]
    diversity_score: float


@dataclass
class MultiDimensionalTrustScore:
    """Composite trust score across 4 dimensions."""
    expert_id: int
    context: str
    internal_quality: Optional[InternalQualityScore]
    conversational_trust: Optional[ConversationalTrustScore]
    byzantine_consensus: Optional[ByzantineConsensusScore]
    federation_trust: Optional[FederationTrustScore]
    composite_score: float
    confidence: float
    dimensions_available: int
    trust_tier: str  # "HIGH", "MEDIUM", "LOW", "UNTRUSTED"


# ============================================================================
# Multi-Dimensional ATP Allocator
# ============================================================================

@dataclass
class ATPAllocation:
    """ATP allocation result."""
    expert_id: int
    base_atp: int
    trust_multiplier: float  # Based on multi-dimensional trust
    allocated_atp: int
    trust_score: float
    trust_confidence: float
    dimensions_available: int
    trust_tier: str


class MultiDimensionalATPAllocator:
    """
    Allocates ATP based on multi-dimensional trust scores.

    High trust → More ATP
    Low trust → Less ATP
    Multi-dimensional → Higher confidence in allocation
    """

    def __init__(
        self,
        base_atp: int = 100,
        high_trust_multiplier: float = 2.0,
        medium_trust_multiplier: float = 1.0,
        low_trust_multiplier: float = 0.5,
        untrusted_multiplier: float = 0.1,
    ):
        """
        Args:
            base_atp: Base ATP allocation
            high_trust_multiplier: Multiplier for high-trust agents (>0.8)
            medium_trust_multiplier: Multiplier for medium-trust agents (0.5-0.8)
            low_trust_multiplier: Multiplier for low-trust agents (0.3-0.5)
            untrusted_multiplier: Multiplier for untrusted agents (<0.3)
        """
        self.base_atp = base_atp
        self.high_trust_multiplier = high_trust_multiplier
        self.medium_trust_multiplier = medium_trust_multiplier
        self.low_trust_multiplier = low_trust_multiplier
        self.untrusted_multiplier = untrusted_multiplier

    def allocate(
        self,
        expert_id: int,
        trust_score: MultiDimensionalTrustScore
    ) -> ATPAllocation:
        """
        Allocate ATP based on multi-dimensional trust.

        Args:
            expert_id: Agent requesting ATP
            trust_score: Multi-dimensional trust assessment

        Returns:
            ATP allocation result
        """
        composite = trust_score.composite_score

        # Determine multiplier based on trust tier
        if trust_score.trust_tier == "HIGH":
            multiplier = self.high_trust_multiplier
        elif trust_score.trust_tier == "MEDIUM":
            multiplier = self.medium_trust_multiplier
        elif trust_score.trust_tier == "LOW":
            multiplier = self.low_trust_multiplier
        else:  # UNTRUSTED
            multiplier = self.untrusted_multiplier

        # Apply confidence adjustment (more dimensions = higher confidence)
        # Full 4 dimensions = 1.0x, 1 dimension = 0.7x
        confidence_adjustment = 0.7 + (0.3 * trust_score.dimensions_available / 4)
        adjusted_multiplier = multiplier * confidence_adjustment

        allocated_atp = int(self.base_atp * adjusted_multiplier)

        return ATPAllocation(
            expert_id=expert_id,
            base_atp=self.base_atp,
            trust_multiplier=adjusted_multiplier,
            allocated_atp=allocated_atp,
            trust_score=composite,
            trust_confidence=trust_score.confidence,
            dimensions_available=trust_score.dimensions_available,
            trust_tier=trust_score.trust_tier
        )


# ============================================================================
# Multi-Dimensional Trust Computer
# ============================================================================

class MultiDimensionalTrustComputer:
    """
    Computes multi-dimensional trust scores from various signals.

    Integrates:
    - Internal quality observations
    - Conversational trust dynamics
    - Byzantine consensus from federation
    - Cross-federation trust aggregation
    """

    def __init__(
        self,
        internal_weight: float = 0.35,
        conversational_weight: float = 0.25,
        byzantine_weight: float = 0.25,
        federation_weight: float = 0.15,
    ):
        """
        Args:
            internal_weight: Weight for internal quality dimension
            conversational_weight: Weight for conversational trust dimension
            byzantine_weight: Weight for Byzantine consensus dimension
            federation_weight: Weight for federation trust dimension
        """
        self.internal_weight = internal_weight
        self.conversational_weight = conversational_weight
        self.byzantine_weight = byzantine_weight
        self.federation_weight = federation_weight

    def compute_trust(
        self,
        expert_id: int,
        context: str,
        internal_quality: Optional[InternalQualityScore] = None,
        conversational_trust: Optional[ConversationalTrustScore] = None,
        byzantine_consensus: Optional[ByzantineConsensusScore] = None,
        federation_trust: Optional[FederationTrustScore] = None,
    ) -> MultiDimensionalTrustScore:
        """
        Compute multi-dimensional trust score.

        Gracefully handles missing dimensions (weighted average of available).

        Returns:
            Multi-dimensional trust score
        """
        scores = {}
        weights = {}

        # Dimension 1: Internal Quality
        if internal_quality:
            scores['internal'] = internal_quality.quality
            weights['internal'] = self.internal_weight

        # Dimension 2: Conversational Trust
        if conversational_trust:
            scores['conversational'] = conversational_trust.relationship_score
            weights['conversational'] = self.conversational_weight

        # Dimension 3: Byzantine Consensus
        if byzantine_consensus:
            scores['byzantine'] = byzantine_consensus.consensus_quality
            weights['byzantine'] = self.byzantine_weight

        # Dimension 4: Federation Trust
        if federation_trust:
            scores['federated'] = federation_trust.federated_quality
            weights['federated'] = self.federation_weight

        # Compute weighted composite
        if not scores:
            # No dimensions available
            composite_score = 0.0
            confidence = 0.0
            trust_tier = "UNTRUSTED"
        else:
            total_weight = sum(weights.values())
            composite_score = sum(
                scores[dim] * weights[dim] / total_weight
                for dim in scores
            )

            # Confidence based on number of dimensions
            confidence = len(scores) / 4.0

            # Trust tier
            if composite_score >= 0.8:
                trust_tier = "HIGH"
            elif composite_score >= 0.5:
                trust_tier = "MEDIUM"
            elif composite_score >= 0.3:
                trust_tier = "LOW"
            else:
                trust_tier = "UNTRUSTED"

        return MultiDimensionalTrustScore(
            expert_id=expert_id,
            context=context,
            internal_quality=internal_quality,
            conversational_trust=conversational_trust,
            byzantine_consensus=byzantine_consensus,
            federation_trust=federation_trust,
            composite_score=composite_score,
            confidence=confidence,
            dimensions_available=len(scores),
            trust_tier=trust_tier
        )


# ============================================================================
# End-to-End Integration Test
# ============================================================================

def test_lct_to_atp_pipeline():
    """
    Test complete pipeline: LCT → Attestations → Byzantine Consensus → Trust → ATP.

    Scenarios:
    1. High-quality expert (0.9 quality) → HIGH trust → 2.0x ATP
    2. Medium-quality expert (0.6 quality) → MEDIUM trust → 1.0x ATP
    3. Low-quality expert (0.3 quality) → LOW trust → 0.5x ATP
    """
    print("=" * 80)
    print("LCT → ATP COMPLETE PIPELINE TEST")
    print("=" * 80)
    print()

    # Setup: Register 3 societies
    authenticator = LCTSocietyAuthenticator(network="web4.network")

    societies = []
    for i in range(3):
        identity, private_key = create_test_lct_identity(f"society_{i}")
        attestation = create_attestation(identity, private_key)
        authenticator.register_society(identity, attestation)
        societies.append((identity, private_key))

    consensus_engine = LCTHardenedByzantineConsensus(
        authenticator=authenticator,
        min_legitimate_attestations=2
    )

    trust_computer = MultiDimensionalTrustComputer()
    atp_allocator = MultiDimensionalATPAllocator(base_atp=100)

    # Test 3 experts with different quality levels
    experts = [
        (101, 0.9, "HIGH"),
        (102, 0.6, "MEDIUM"),
        (103, 0.3, "LOW"),
    ]

    results = []

    for expert_id, true_quality, expected_tier in experts:
        print(f"Expert {expert_id} (true quality: {true_quality}, expected tier: {expected_tier})")
        print("-" * 80)

        # Step 1: Collect LCT-authenticated quality attestations
        attestations = []
        for identity, private_key in societies:
            challenge = secrets.token_hex(16)
            attestation_quality = true_quality + random.uniform(-0.05, 0.05)

            message = f"{expert_id}:context_a:{attestation_quality}:{challenge}"
            signature = hmac.new(
                identity.public_key.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()

            attestation = LCTQualityAttestation(
                attestation_id=f"att_{expert_id}_{identity.agent_id}",
                observer_society_lct=identity.to_lct_uri(),
                expert_id=expert_id,
                context_id="context_a",
                quality=attestation_quality,
                observation_count=5,
                society_public_key=identity.public_key,
                challenge=challenge,
                signature=signature
            )
            attestations.append(attestation)

        # Step 2: Byzantine consensus
        consensus_result = consensus_engine.compute_consensus(
            expert_id, "context_a", attestations
        )

        if not consensus_result:
            print("  ❌ Consensus failed")
            continue

        print(f"  Byzantine consensus: {consensus_result.consensus_quality:.3f}")
        print(f"  Coverage: {consensus_result.coverage:.1%}")
        print(f"  LCT-verified societies: {consensus_result.lct_verified_societies}")

        # Step 3: Multi-dimensional trust (using Byzantine dimension only for this test)
        byzantine_score = ByzantineConsensusScore(
            expert_id=expert_id,
            context="context_a",
            consensus_quality=consensus_result.consensus_quality,
            num_attestations=consensus_result.num_attestations,
            outliers_detected=consensus_result.outliers_detected,
            consensus_confidence=consensus_result.confidence
        )

        trust_score = trust_computer.compute_trust(
            expert_id=expert_id,
            context="context_a",
            byzantine_consensus=byzantine_score
        )

        print(f"  Trust score: {trust_score.composite_score:.3f}")
        print(f"  Trust tier: {trust_score.trust_tier}")
        print(f"  Confidence: {trust_score.confidence:.1%}")

        # Step 4: ATP allocation
        atp_allocation = atp_allocator.allocate(expert_id, trust_score)

        print(f"  ATP allocated: {atp_allocation.allocated_atp} (base: {atp_allocation.base_atp})")
        print(f"  Trust multiplier: {atp_allocation.trust_multiplier:.2f}x")
        print()

        results.append({
            'expert_id': expert_id,
            'true_quality': true_quality,
            'consensus_quality': consensus_result.consensus_quality,
            'trust_score': trust_score.composite_score,
            'trust_tier': trust_score.trust_tier,
            'expected_tier': expected_tier,
            'atp_allocated': atp_allocation.allocated_atp,
            'tier_correct': trust_score.trust_tier == expected_tier
        })

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    all_correct = all(r['tier_correct'] for r in results)

    if all_correct:
        print("✅ SUCCESS: All experts correctly tiered based on quality")
        print()
        for r in results:
            print(f"  Expert {r['expert_id']}: {r['trust_tier']} tier, {r['atp_allocated']} ATP")
        print()
        print("  Pipeline validation:")
        print("    - LCT authentication: All attestations cryptographically verified")
        print("    - Byzantine consensus: Attack-resistant quality computation")
        print("    - Multi-dimensional trust: Composite scoring across dimensions")
        print("    - ATP allocation: Resource access reflects trustworthiness")
    else:
        print("❌ FAILURE: Some experts incorrectly tiered")
        for r in results:
            status = "✅" if r['tier_correct'] else "❌"
            print(f"  {status} Expert {r['expert_id']}: expected {r['expected_tier']}, got {r['trust_tier']}")

    print()

    # Save results
    results_path = Path("/home/dp/ai-workspace/web4/implementation/session88_track3_lct_atp_results.json")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to: {results_path}")
    print()

    return results


# ============================================================================
# Main
# ============================================================================

def main():
    """Run LCT-ATP-Reputation integration test."""
    print("=" * 80)
    print("SESSION 88 TRACK 3: LCT-ATP-REPUTATION INTEGRATION")
    print("=" * 80)
    print()

    print("Objective: Demonstrate complete pipeline from LCT registration to ATP allocation")
    print("Flow: LCT → Attestations → Byzantine Consensus → Trust → ATP")
    print()

    results = test_lct_to_atp_pipeline()

    return results


if __name__ == "__main__":
    main()
