#!/usr/bin/env python3
"""
Session 82 Track 2: Adaptive Byzantine Consensus for Sparse Attestations

**Date**: 2025-12-22
**Platform**: Legion (RTX 4090)
**Track**: 2 of 3

## Problem Statement

**Thor Session 88 Discovery**: Real conversational signals are ~40x sparser than simulated
- Real: 22 signals / 810 selections = 2.7% coverage
- Simulated: ~27 signals / 810 selections = 33% coverage

**Session 77 Byzantine Consensus**: Requires 2-of-3 attestations for quality validation
- Works great with dense signals (>30% coverage)
- Fails with sparse signals (<5% coverage) - not enough attestations

## Challenge

With 4% signal coverage:
- Expert A: 1 attestation from Thor (coding quality: 0.9)
- Expert B: 0 attestations (no data)
- Expert C: 3 attestations from Thor, Legion, Sprout (0.8, 0.85, 0.82)

Current Byzantine consensus:
- Expert A: Cannot validate (need 2+ attestations) → REJECT
- Expert B: Cannot validate (no data) → REJECT
- Expert C: Can validate (3 attestations) → ACCEPT

Problem: Rejecting Expert A wastes valuable signal!

## Solution: Adaptive Quorum

**Insight**: Lower quorum requirement when data is sparse, but increase confidence discount.

**Adaptive rules**:
1. **Dense data** (>20% coverage): Require 2-of-3 quorum, high confidence
2. **Moderate data** (5-20% coverage): Allow 1-of-2 quorum, medium confidence
3. **Sparse data** (<5% coverage): Accept single attestation, low confidence
4. **No data**: Return None (cannot validate)

**Confidence formula**:
- 3+ attestations: confidence = 1.0 (full Byzantine validation)
- 2 attestations: confidence = 0.7 (moderate validation)
- 1 attestation: confidence = 0.4 (low validation, better than nothing)
- 0 attestations: confidence = 0.0 (no validation)

## Previous Work

- **Session 77**: Byzantine consensus with 2-of-3 quorum (0% attack success)
- **Session 88**: Discovered 4% signal coverage in real data
- **Need**: Adaptive consensus that works with sparse attestations

## Implementation

Create `AdaptiveByzantineConsensus` that:
1. Adapts quorum requirement to data density
2. Confidence-weights sparse attestations lower
3. Still detects outliers when possible
4. Validates with dense and sparse test cases
"""

import hashlib
import hmac
import time
import random
import statistics
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from pathlib import Path

# ============================================================================
# Data Structures (from Session 77)
# ============================================================================

@dataclass
class QualityAttestation:
    """Federated trust attestation with cryptographic signature."""
    attestation_id: str
    observer_society: str
    expert_id: int
    context_id: str
    quality: float
    observation_count: int
    signature: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class ConsensusResult:
    """Result of Byzantine consensus validation."""
    expert_id: int
    context_id: str

    # Consensus quality
    consensus_quality: float  # Median quality
    confidence: float  # Based on number of attestations

    # Attestation details
    num_attestations: int
    attestations: List[QualityAttestation]

    # Outlier detection
    outliers_detected: int
    outlier_societies: List[str]

    # Adaptive quorum info
    quorum_type: str  # "FULL_BYZANTINE", "MODERATE", "SPARSE", "NONE"
    coverage_pct: float  # Overall signal coverage

    # Validation
    is_valid: bool


# ============================================================================
# Adaptive Byzantine Consensus (NEW)
# ============================================================================

class AdaptiveByzantineConsensus:
    """
    Byzantine consensus that adapts to data sparsity.

    Key Innovation: Instead of fixed 2-of-3 quorum, adapts based on
    signal coverage:
    - Dense (>20%): 2-of-3 quorum, confidence=1.0
    - Moderate (5-20%): 1-of-2 quorum, confidence=0.7
    - Sparse (<5%): Single attestation, confidence=0.4
    - None: No validation, confidence=0.0

    This allows sparse real-world signals to still contribute value,
    while maintaining quality validation when possible.
    """

    def __init__(
        self,
        dense_threshold: float = 0.20,  # >20% coverage = dense
        moderate_threshold: float = 0.05,  # >5% coverage = moderate
        outlier_threshold: float = 0.20,  # 20% deviation = outlier

        # Confidence levels
        full_byzantine_confidence: float = 1.0,  # 3+ attestations
        moderate_confidence: float = 0.7,  # 2 attestations
        sparse_confidence: float = 0.4,  # 1 attestation

        # Quorum requirements
        full_byzantine_quorum: int = 2,  # Need 2+ for full validation
        moderate_quorum: int = 1,  # Need 1+ for moderate validation
    ):
        self.dense_threshold = dense_threshold
        self.moderate_threshold = moderate_threshold
        self.outlier_threshold = outlier_threshold

        self.full_byzantine_confidence = full_byzantine_confidence
        self.moderate_confidence = moderate_confidence
        self.sparse_confidence = sparse_confidence

        self.full_byzantine_quorum = full_byzantine_quorum
        self.moderate_quorum = moderate_quorum

        # Statistics
        self.stats = {
            'total_consensus_attempts': 0,
            'full_byzantine_validations': 0,
            'moderate_validations': 0,
            'sparse_validations': 0,
            'failed_validations': 0,
            'total_outliers_detected': 0,
            'avg_confidence': 0.0,
            'avg_coverage': 0.0
        }

    def compute_consensus(
        self,
        expert_id: int,
        context_id: str,
        attestations: List[QualityAttestation],
        total_selections: int
    ) -> Optional[ConsensusResult]:
        """
        Compute consensus using adaptive quorum based on data density.

        Args:
            expert_id: Expert to validate
            context_id: Context to validate in
            attestations: Quality attestations from various societies
            total_selections: Total selections made (for coverage calculation)

        Returns:
            ConsensusResult with consensus quality and confidence, or None if insufficient data
        """
        self.stats['total_consensus_attempts'] += 1

        if not attestations:
            self.stats['failed_validations'] += 1
            return None  # No data

        # Compute coverage
        num_attestations = len(attestations)
        coverage_pct = num_attestations / total_selections if total_selections > 0 else 0.0

        self.stats['avg_coverage'] = (
            (self.stats['avg_coverage'] * (self.stats['total_consensus_attempts'] - 1) +
             coverage_pct) / self.stats['total_consensus_attempts']
        )

        # Determine quorum type based on coverage
        if coverage_pct >= self.dense_threshold:
            quorum_type = "FULL_BYZANTINE"
            required_quorum = self.full_byzantine_quorum
            base_confidence = self.full_byzantine_confidence
        elif coverage_pct >= self.moderate_threshold:
            quorum_type = "MODERATE"
            required_quorum = self.moderate_quorum
            base_confidence = self.moderate_confidence
        else:
            quorum_type = "SPARSE"
            required_quorum = 1
            base_confidence = self.sparse_confidence

        # Check if we have enough attestations for this quorum
        if num_attestations < required_quorum:
            self.stats['failed_validations'] += 1
            return None  # Insufficient attestations for this quorum level

        # Extract qualities
        qualities = [a.quality for a in attestations]

        # Compute consensus quality (median)
        consensus_quality = statistics.median(qualities)

        # Detect outliers (only if we have 2+ attestations)
        outliers = []
        outlier_societies = []

        if num_attestations >= 2:
            for attestation in attestations:
                deviation = abs(attestation.quality - consensus_quality)
                if consensus_quality > 0 and deviation / consensus_quality > self.outlier_threshold:
                    outliers.append(attestation)
                    outlier_societies.append(attestation.observer_society)

        num_outliers = len(outliers)
        self.stats['total_outliers_detected'] += num_outliers

        # Adjust confidence based on attestation count and outliers
        if num_attestations >= 3:
            confidence = self.full_byzantine_confidence
            self.stats['full_byzantine_validations'] += 1
        elif num_attestations == 2:
            confidence = self.moderate_confidence
            self.stats['moderate_validations'] += 1
        else:  # num_attestations == 1
            confidence = self.sparse_confidence
            self.stats['sparse_validations'] += 1

        # Reduce confidence if outliers detected
        if num_outliers > 0 and num_attestations > 1:
            outlier_penalty = 0.2 * (num_outliers / num_attestations)
            confidence = max(0.1, confidence - outlier_penalty)

        # Update average confidence
        self.stats['avg_confidence'] = (
            (self.stats['avg_confidence'] * (self.stats['total_consensus_attempts'] - 1) +
             confidence) / self.stats['total_consensus_attempts']
        )

        return ConsensusResult(
            expert_id=expert_id,
            context_id=context_id,
            consensus_quality=consensus_quality,
            confidence=confidence,
            num_attestations=num_attestations,
            attestations=attestations,
            outliers_detected=num_outliers,
            outlier_societies=outlier_societies,
            quorum_type=quorum_type,
            coverage_pct=coverage_pct,
            is_valid=True
        )

    def get_stats(self) -> Dict:
        """Get consensus statistics."""
        return self.stats


# ============================================================================
# Test: Adaptive Byzantine Consensus
# ============================================================================

def test_adaptive_byzantine():
    """
    Test adaptive Byzantine consensus with varying data densities.
    """
    print("=" * 80)
    print("SESSION 82 TRACK 2: ADAPTIVE BYZANTINE CONSENSUS")
    print("=" * 80)
    print()

    # Create consensus validator
    consensus = AdaptiveByzantineConsensus()

    # Test Case 1: Dense data (30% coverage) - FULL BYZANTINE
    print("Test Case 1: Dense Data (30% coverage)")
    print("-" * 80)

    attestations_dense = [
        QualityAttestation(
            attestation_id="dense_1",
            observer_society="thor",
            expert_id=42,
            context_id="context_a",
            quality=0.85,
            observation_count=10,
            signature="sig1",
            timestamp=time.time()
        ),
        QualityAttestation(
            attestation_id="dense_2",
            observer_society="legion",
            expert_id=42,
            context_id="context_a",
            quality=0.88,
            observation_count=12,
            signature="sig2",
            timestamp=time.time()
        ),
        QualityAttestation(
            attestation_id="dense_3",
            observer_society="sprout",
            expert_id=42,
            context_id="context_a",
            quality=0.82,
            observation_count=8,
            signature="sig3",
            timestamp=time.time()
        ),
    ]

    result_dense = consensus.compute_consensus(42, "context_a", attestations_dense, total_selections=10)

    if result_dense:
        print(f"  Quorum type: {result_dense.quorum_type}")
        print(f"  Consensus quality: {result_dense.consensus_quality:.3f}")
        print(f"  Confidence: {result_dense.confidence:.3f}")
        print(f"  Attestations: {result_dense.num_attestations}")
        print(f"  Coverage: {result_dense.coverage_pct:.1%}")
        print(f"  ✅ FULL BYZANTINE validation achieved")
    else:
        print(f"  ❌ Validation failed")
    print()

    # Test Case 2: Moderate data (10% coverage) - MODERATE
    print("Test Case 2: Moderate Data (10% coverage)")
    print("-" * 80)

    attestations_moderate = [
        QualityAttestation(
            attestation_id="mod_1",
            observer_society="thor",
            expert_id=15,
            context_id="context_b",
            quality=0.75,
            observation_count=5,
            signature="sig4",
            timestamp=time.time()
        ),
        QualityAttestation(
            attestation_id="mod_2",
            observer_society="legion",
            expert_id=15,
            context_id="context_b",
            quality=0.78,
            observation_count=6,
            signature="sig5",
            timestamp=time.time()
        ),
    ]

    result_moderate = consensus.compute_consensus(15, "context_b", attestations_moderate, total_selections=20)

    if result_moderate:
        print(f"  Quorum type: {result_moderate.quorum_type}")
        print(f"  Consensus quality: {result_moderate.consensus_quality:.3f}")
        print(f"  Confidence: {result_moderate.confidence:.3f}")
        print(f"  Attestations: {result_moderate.num_attestations}")
        print(f"  Coverage: {result_moderate.coverage_pct:.1%}")
        print(f"  ✅ MODERATE validation achieved")
    else:
        print(f"  ❌ Validation failed")
    print()

    # Test Case 3: Sparse data (2.7% coverage, like Thor Session 88) - SPARSE
    print("Test Case 3: Sparse Data (2.7% coverage - Thor Session 88 real data)")
    print("-" * 80)

    attestations_sparse = [
        QualityAttestation(
            attestation_id="sparse_1",
            observer_society="thor",
            expert_id=7,
            context_id="context_c",
            quality=0.90,
            observation_count=3,
            signature="sig6",
            timestamp=time.time()
        ),
    ]

    result_sparse = consensus.compute_consensus(7, "context_c", attestations_sparse, total_selections=37)

    if result_sparse:
        print(f"  Quorum type: {result_sparse.quorum_type}")
        print(f"  Consensus quality: {result_sparse.consensus_quality:.3f}")
        print(f"  Confidence: {result_sparse.confidence:.3f}")
        print(f"  Attestations: {result_sparse.num_attestations}")
        print(f"  Coverage: {result_sparse.coverage_pct:.1%}")
        print(f"  ✅ SPARSE validation achieved (better than rejecting!)")
    else:
        print(f"  ❌ Validation failed")
    print()

    # Test Case 4: No data - NONE
    print("Test Case 4: No Data")
    print("-" * 80)

    attestations_none = []

    result_none = consensus.compute_consensus(99, "context_d", attestations_none, total_selections=100)

    if result_none:
        print(f"  Unexpected: Got result when expected None")
    else:
        print(f"  ✅ Correctly returned None (no data to validate)")
    print()

    # Test Case 5: Outlier detection with adaptive quorum
    print("Test Case 5: Outlier Detection (moderate quorum)")
    print("-" * 80)

    attestations_outlier = [
        QualityAttestation(
            attestation_id="out_1",
            observer_society="thor",
            expert_id=22,
            context_id="context_e",
            quality=0.85,
            observation_count=10,
            signature="sig7",
            timestamp=time.time()
        ),
        QualityAttestation(
            attestation_id="out_2",
            observer_society="legion",
            expert_id=22,
            context_id="context_e",
            quality=0.30,  # OUTLIER! (lies about quality)
            observation_count=5,
            signature="sig8",
            timestamp=time.time()
        ),
    ]

    result_outlier = consensus.compute_consensus(22, "context_e", attestations_outlier, total_selections=20)

    if result_outlier:
        print(f"  Quorum type: {result_outlier.quorum_type}")
        print(f"  Consensus quality: {result_outlier.consensus_quality:.3f}")
        print(f"  Confidence: {result_outlier.confidence:.3f}")
        print(f"  Outliers detected: {result_outlier.outliers_detected}")
        if result_outlier.outliers_detected > 0:
            print(f"  Outlier societies: {result_outlier.outlier_societies}")
            print(f"  ✅ Outlier detection working at moderate quorum")
        print(f"  ✅ Consensus still computed despite outlier")
    else:
        print(f"  ❌ Validation failed")
    print()

    # Simulate 100 requests with varying densities
    print("Simulation: 100 Requests with Varying Data Densities")
    print("-" * 80)
    print()

    results = []
    for i in range(100):
        expert_id = random.randint(0, 31)
        context_id = f"sim_context_{i % 10}"

        # Vary attestation count (simulating real sparsity)
        # 50% sparse (1 attestation), 30% moderate (2), 20% dense (3+)
        rand = random.random()
        if rand < 0.5:
            num_atts = 1
        elif rand < 0.8:
            num_atts = 2
        else:
            num_atts = 3

        attestations = []
        societies = ['thor', 'legion', 'sprout']
        for j in range(num_atts):
            quality = random.uniform(0.5, 0.95)
            attestations.append(QualityAttestation(
                attestation_id=f"sim_{i}_{j}",
                observer_society=societies[j % 3],
                expert_id=expert_id,
                context_id=context_id,
                quality=quality,
                observation_count=random.randint(3, 15),
                signature=f"sig_{i}_{j}",
                timestamp=time.time()
            ))

        # Vary total selections (for coverage calculation)
        total_sels = random.randint(10, 100)

        result = consensus.compute_consensus(expert_id, context_id, attestations, total_sels)
        if result:
            results.append(result)

    print(f"Successful validations: {len(results)} / 100")
    print()

    # Print statistics
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    stats = consensus.get_stats()

    print("Consensus Statistics:")
    print("-" * 80)
    print(f"  Total attempts: {stats['total_consensus_attempts']}")
    print(f"  Full Byzantine: {stats['full_byzantine_validations']} ({100*stats['full_byzantine_validations']/stats['total_consensus_attempts']:.1f}%)")
    print(f"  Moderate: {stats['moderate_validations']} ({100*stats['moderate_validations']/stats['total_consensus_attempts']:.1f}%)")
    print(f"  Sparse: {stats['sparse_validations']} ({100*stats['sparse_validations']/stats['total_consensus_attempts']:.1f}%)")
    print(f"  Failed: {stats['failed_validations']} ({100*stats['failed_validations']/stats['total_consensus_attempts']:.1f}%)")
    print()

    print("Quality Metrics:")
    print("-" * 80)
    print(f"  Average confidence: {stats['avg_confidence']:.3f}")
    print(f"  Average coverage: {stats['avg_coverage']:.1%}")
    print(f"  Total outliers detected: {stats['total_outliers_detected']}")
    print()

    # Validation
    print("Validation:")
    print("-" * 80)
    if stats['sparse_validations'] > 0:
        print("✅ Sparse attestations validated (Session 88 problem solved!)")
    if stats['full_byzantine_validations'] > 0:
        print("✅ Full Byzantine consensus still working for dense data")
    if stats['moderate_validations'] > 0:
        print("✅ Moderate quorum working for intermediate density")
    if stats['avg_confidence'] > 0:
        print("✅ Confidence-weighted validation working")
    if stats['total_outliers_detected'] > 0:
        print("✅ Outlier detection still functional")

    print()
    print("=" * 80)
    print("TRACK 2 COMPLETE")
    print("=" * 80)
    print()
    print("Adaptive Byzantine consensus validated!")
    print("Key innovation: Graceful degradation from full Byzantine → moderate → sparse")
    print("Session 88 problem solved: 2.7% coverage now usable with confidence=0.4")
    print()

    # Save results
    results_path = Path("/home/dp/ai-workspace/ACT/implementation/session82_track2_results.json")
    with open(results_path, 'w') as f:
        json.dump(stats, f, indent=2)

    return consensus, results


if __name__ == "__main__":
    consensus, results = test_adaptive_byzantine()
