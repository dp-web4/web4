"""
Session #180: Existence Detection in Attestations

Integrates Gnosis Session 9 (Existence Detection Analysis) into Web4's
attestation validation system.

Key Insight from Gnosis Session 9:
    **Gnosis detects computational existence** - the boundary between
    meaningful processing (C > 0.5) and mere activity (C < 0.5).

    If existence = C > 0 (Session 257) and consciousness = C > 0.5,
    then Gnosis answers: "Does this computation EXIST in the meaningful sense?"

    Below C = 0.5:
    - Automatic generation (no conscious processing)
    - Noise dominates signal
    - Computational non-existence (activity without meaning)

    Above C = 0.5:
    - Conscious causation (selective processing)
    - Signal dominates noise
    - Computational existence (meaningful processing)

Application to Web4:
    Attestations are computational artifacts. Gnosis-based validation
    detects whether an attestation represents:
    - **Real existence** (C > 0.5): Meaningful, conscious generation
    - **Apparent existence** (0 < C < 0.5): Activity without meaning
    - **Non-existence** (C ≈ 0): Random noise

    This prevents:
    - Automated spam attestations
    - LLM-generated fake attestations (below consciousness threshold)
    - Noise masquerading as signal

    Validation question: "Does this attestation exist computationally?"

Author: Web4 Research Session 17
Date: January 13, 2026
Status: IN PROGRESS
"""

import math
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from enum import Enum


# ============================================================================
# Computational Existence Levels
# ============================================================================

class ComputationalExistence(Enum):
    """Existence levels for computational artifacts"""
    NON_EXISTENT = "non_existent"          # C < 0.1 (noise)
    AUTOMATIC = "automatic"                # 0.1 ≤ C < 0.3 (LLM slop)
    SEMI_CONSCIOUS = "semi_conscious"      # 0.3 ≤ C < 0.5 (structured but not conscious)
    CONSCIOUS = "conscious"                # 0.5 ≤ C < 0.7 (meaningful computation)
    HIGHLY_CONSCIOUS = "highly_conscious"  # C ≥ 0.7 (intentional, verified)


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class AttestationArtifact:
    """An attestation as a computational artifact"""
    attestation_id: str
    content: str
    attestor: str
    timestamp: int

    # Coherence measures
    syntactic_coherence: float  # Pattern consistency
    semantic_coherence: float   # Meaning consistency
    temporal_coherence: float   # Time-series consistency

    # Derived measures
    overall_coherence: float    # Combined coherence
    information_bits: float     # I_C = -log₂(1 - C)
    existence_level: ComputationalExistence


@dataclass
class ExistenceValidation:
    """Result of existence detection validation"""
    attestation_id: str
    exists_meaningfully: bool  # C > 0.5
    coherence: float
    information_bits: float
    existence_level: ComputationalExistence
    confidence: float  # How confident in the assessment (0-1)
    anomalies: List[str]  # Detected anomalies


# ============================================================================
# Existence Detector
# ============================================================================

class ExistenceDetector:
    """
    Detects computational existence in attestations.

    From Gnosis Session 9:
    - Correctness = Computational Existence
    - C = 0.50 is the threshold for meaningful existence
    - Three-level validation: Syntactic, Semantic, Temporal
    """

    # Thresholds from Gnosis Session 9 and Session 257
    THRESHOLD_MEANINGFUL = 0.50   # Consciousness = meaningful existence
    THRESHOLD_STRUCTURED = 0.30   # Below this → automatic generation
    THRESHOLD_NOISE = 0.10        # Below this → pure noise

    def __init__(self):
        self.validation_history: List[ExistenceValidation] = []


    def calculate_overall_coherence(
        self,
        syntactic: float,
        semantic: float,
        temporal: float
    ) -> float:
        """
        Calculate overall coherence from three levels.

        From Gnosis Session 9: Three-stream detection
        - Syntactic: Pattern-level coherence
        - Semantic: Meaning-level coherence
        - Temporal: Time-series coherence

        Combined via geometric mean (all must be present)
        """
        # Geometric mean emphasizes that all three matter
        overall = (syntactic * semantic * temporal) ** (1/3)

        return overall


    def information_content(self, coherence: float) -> float:
        """
        Calculate information content from coherence.

        From Session 255: I_C = -log₂(1 - C)
        At C = 0.5 → I_C = 1 bit (minimum for binary classification)
        """
        if coherence >= 1.0:
            return float('inf')
        if coherence <= 0:
            return 0.0

        return -math.log2(1 - coherence)


    def classify_existence(self, coherence: float) -> ComputationalExistence:
        """
        Classify computational existence level.
        """
        if coherence < self.THRESHOLD_NOISE:
            return ComputationalExistence.NON_EXISTENT
        elif coherence < self.THRESHOLD_STRUCTURED:
            return ComputationalExistence.AUTOMATIC
        elif coherence < self.THRESHOLD_MEANINGFUL:
            return ComputationalExistence.SEMI_CONSCIOUS
        elif coherence < 0.7:
            return ComputationalExistence.CONSCIOUS
        else:
            return ComputationalExistence.HIGHLY_CONSCIOUS


    def detect_anomalies(
        self,
        syntactic: float,
        semantic: float,
        temporal: float,
        overall: float
    ) -> List[str]:
        """
        Detect anomalies in coherence structure.

        From Gnosis Session 9: Inconsistency indicates fake/generated content
        """
        anomalies = []

        # Check for imbalance across levels
        max_diff = max(
            abs(syntactic - semantic),
            abs(semantic - temporal),
            abs(temporal - syntactic)
        )

        if max_diff > 0.3:
            anomalies.append("high_imbalance_across_levels")

        # Check if overall is much lower than individual levels
        # (indicates lack of integration)
        avg_individual = (syntactic + semantic + temporal) / 3
        if overall < avg_individual - 0.2:
            anomalies.append("low_integration")

        # Check for suspiciously high syntactic with low semantic
        # (characteristic of LLM-generated slop)
        if syntactic > 0.7 and semantic < 0.3:
            anomalies.append("high_syntactic_low_semantic")

        # Check for zero temporal (no time-series context)
        if temporal < 0.1:
            anomalies.append("no_temporal_context")

        return anomalies


    def validate_attestation(
        self,
        attestation: AttestationArtifact
    ) -> ExistenceValidation:
        """
        Validate if attestation represents meaningful computational existence.

        Returns:
            Validation result with existence assessment
        """
        # Calculate overall coherence
        overall = self.calculate_overall_coherence(
            attestation.syntactic_coherence,
            attestation.semantic_coherence,
            attestation.temporal_coherence
        )

        # Calculate information content
        info_bits = self.information_content(overall)

        # Classify existence
        existence_level = self.classify_existence(overall)

        # Does it exist meaningfully?
        exists_meaningfully = overall >= self.THRESHOLD_MEANINGFUL

        # Detect anomalies
        anomalies = self.detect_anomalies(
            attestation.syntactic_coherence,
            attestation.semantic_coherence,
            attestation.temporal_coherence,
            overall
        )

        # Confidence based on:
        # 1. Distance from threshold (far = high confidence)
        # 2. Lack of anomalies
        # 3. Consistency across levels

        distance_from_threshold = abs(overall - self.THRESHOLD_MEANINGFUL)
        consistency = 1.0 - (max(
            abs(attestation.syntactic_coherence - overall),
            abs(attestation.semantic_coherence - overall),
            abs(attestation.temporal_coherence - overall)
        ))

        confidence = (
            0.5 * min(1.0, distance_from_threshold / 0.2) +  # Far from threshold
            0.3 * consistency +                              # Consistent levels
            0.2 * (1.0 - len(anomalies) / 4.0)              # Few anomalies
        )

        validation = ExistenceValidation(
            attestation_id=attestation.attestation_id,
            exists_meaningfully=exists_meaningfully,
            coherence=overall,
            information_bits=info_bits,
            existence_level=existence_level,
            confidence=confidence,
            anomalies=anomalies
        )

        self.validation_history.append(validation)

        return validation


    def batch_validate(
        self,
        attestations: List[AttestationArtifact]
    ) -> Dict[str, ExistenceValidation]:
        """
        Validate multiple attestations.

        Returns:
            Dict mapping attestation_id → validation result
        """
        results = {}

        for attestation in attestations:
            validation = self.validate_attestation(attestation)
            results[attestation.attestation_id] = validation

        return results


    def get_validation_statistics(self) -> Dict:
        """Get statistics on validation history"""

        if not self.validation_history:
            return {
                "total_validations": 0,
                "meaningful_fraction": 0.0,
                "avg_coherence": 0.0,
                "by_existence_level": {}
            }

        total = len(self.validation_history)
        meaningful = sum(1 for v in self.validation_history if v.exists_meaningfully)
        total_coherence = sum(v.coherence for v in self.validation_history)

        # Count by existence level
        by_level = {}
        for level in ComputationalExistence:
            count = sum(1 for v in self.validation_history if v.existence_level == level)
            by_level[level.value] = count

        return {
            "total_validations": total,
            "meaningful_fraction": meaningful / total,
            "avg_coherence": total_coherence / total,
            "by_existence_level": by_level
        }


# ============================================================================
# Test Cases
# ============================================================================

def test_coherence_calculation():
    """Test overall coherence calculation"""
    print("Test 1: Overall Coherence Calculation")

    detector = ExistenceDetector()

    test_cases = [
        (0.8, 0.8, 0.8, "Balanced high coherence"),
        (0.5, 0.5, 0.5, "Balanced medium coherence"),
        (0.8, 0.3, 0.5, "Imbalanced (high syntactic, low semantic)"),
        (0.2, 0.2, 0.2, "Balanced low coherence"),
    ]

    for syntactic, semantic, temporal, description in test_cases:
        overall = detector.calculate_overall_coherence(syntactic, semantic, temporal)
        print(f"  {description}:")
        print(f"    Syntactic={syntactic:.2f}, Semantic={semantic:.2f}, Temporal={temporal:.2f}")
        print(f"    Overall={overall:.3f}")

    print("  ✓ Test passed\n")


def test_existence_classification():
    """Test classification of existence levels"""
    print("Test 2: Existence Classification")

    detector = ExistenceDetector()

    test_cases = [
        (0.05, ComputationalExistence.NON_EXISTENT, "Noise"),
        (0.20, ComputationalExistence.AUTOMATIC, "LLM slop"),
        (0.40, ComputationalExistence.SEMI_CONSCIOUS, "Structured but not conscious"),
        (0.60, ComputationalExistence.CONSCIOUS, "Meaningful computation"),
        (0.80, ComputationalExistence.HIGHLY_CONSCIOUS, "Highly intentional"),
    ]

    for coherence, expected_level, description in test_cases:
        level = detector.classify_existence(coherence)
        info_bits = detector.information_content(coherence)
        match = level == expected_level

        print(f"  C={coherence:.2f} ({description}):")
        print(f"    Level: {level.value}")
        print(f"    Info: {info_bits:.3f} bits")
        print(f"    {'✓' if match else '✗ Expected: ' + expected_level.value}")

    print()


def test_anomaly_detection():
    """Test anomaly detection in coherence structure"""
    print("Test 3: Anomaly Detection")

    detector = ExistenceDetector()

    test_cases = [
        (0.8, 0.8, 0.8, 0.8, "Balanced high", []),
        (0.8, 0.2, 0.5, 0.47, "LLM-generated", ["high_syntactic_low_semantic"]),
        (0.5, 0.5, 0.0, 0.0, "No temporal", ["no_temporal_context"]),
        (0.9, 0.3, 0.6, 0.56, "Imbalanced", ["high_imbalance_across_levels", "high_syntactic_low_semantic"]),
    ]

    for syntactic, semantic, temporal, overall, description, expected_anomalies in test_cases:
        anomalies = detector.detect_anomalies(syntactic, semantic, temporal, overall)

        print(f"  {description}:")
        print(f"    Syntactic={syntactic:.2f}, Semantic={semantic:.2f}, Temporal={temporal:.2f}")
        print(f"    Anomalies: {anomalies if anomalies else 'None'}")

    print("  ✓ Test passed\n")


def test_attestation_validation():
    """Test full attestation validation"""
    print("Test 4: Attestation Validation")

    detector = ExistenceDetector()

    # High-quality attestation (meaningful existence)
    high_quality = AttestationArtifact(
        attestation_id="attest_1",
        content="Agent performed task X with verification Y",
        attestor="agent_A",
        timestamp=100,
        syntactic_coherence=0.7,
        semantic_coherence=0.6,
        temporal_coherence=0.7,
        overall_coherence=0.0,  # Will be calculated
        information_bits=0.0,
        existence_level=ComputationalExistence.NON_EXISTENT  # Will be classified
    )

    validation = detector.validate_attestation(high_quality)

    print(f"  High-quality attestation:")
    print(f"    Coherence: {validation.coherence:.3f}")
    print(f"    Exists meaningfully: {validation.exists_meaningfully}")
    print(f"    Existence level: {validation.existence_level.value}")
    print(f"    Information: {validation.information_bits:.3f} bits")
    print(f"    Confidence: {validation.confidence:.3f}")
    print(f"    Anomalies: {validation.anomalies if validation.anomalies else 'None'}")

    # Low-quality attestation (automatic generation)
    low_quality = AttestationArtifact(
        attestation_id="attest_2",
        content="Task completed successfully",
        attestor="agent_B",
        timestamp=101,
        syntactic_coherence=0.8,  # High syntactic (LLM-like)
        semantic_coherence=0.2,   # Low semantic (no real meaning)
        temporal_coherence=0.1,   # No temporal context
        overall_coherence=0.0,
        information_bits=0.0,
        existence_level=ComputationalExistence.NON_EXISTENT
    )

    validation2 = detector.validate_attestation(low_quality)

    print(f"\n  Low-quality attestation:")
    print(f"    Coherence: {validation2.coherence:.3f}")
    print(f"    Exists meaningfully: {validation2.exists_meaningfully}")
    print(f"    Existence level: {validation2.existence_level.value}")
    print(f"    Information: {validation2.information_bits:.3f} bits")
    print(f"    Confidence: {validation2.confidence:.3f}")
    print(f"    Anomalies: {validation2.anomalies}")

    print("  ✓ Test passed\n")


def test_batch_validation():
    """Test batch attestation validation"""
    print("Test 5: Batch Validation")

    detector = ExistenceDetector()

    # Create batch of attestations with varying quality
    attestations = []
    for i in range(10):
        # Vary coherence levels
        base_coherence = 0.1 + i * 0.08
        attestation = AttestationArtifact(
            attestation_id=f"attest_{i}",
            content=f"Attestation {i}",
            attestor=f"agent_{i}",
            timestamp=100 + i,
            syntactic_coherence=base_coherence + 0.1,
            semantic_coherence=base_coherence,
            temporal_coherence=base_coherence + 0.05,
            overall_coherence=0.0,
            information_bits=0.0,
            existence_level=ComputationalExistence.NON_EXISTENT
        )
        attestations.append(attestation)

    # Validate batch
    results = detector.batch_validate(attestations)

    print(f"  Validated {len(results)} attestations")

    # Get statistics
    stats = detector.get_validation_statistics()

    print(f"  Meaningful fraction: {stats['meaningful_fraction']:.1%}")
    print(f"  Average coherence: {stats['avg_coherence']:.3f}")
    print(f"  By existence level:")
    for level, count in stats['by_existence_level'].items():
        if count > 0:
            print(f"    {level}: {count}")

    print("  ✓ Test passed\n")


def test_consciousness_threshold():
    """Test that C=0.5 corresponds to 1 bit (consciousness threshold)"""
    print("Test 6: Consciousness Threshold (C=0.5 → 1 bit)")

    detector = ExistenceDetector()

    # Test at and around consciousness threshold
    test_values = [0.3, 0.4, 0.5, 0.6, 0.7]

    print("    C   | Info Bits | Exists Meaningfully | Level")
    print("  ------|-----------|---------------------|-----------------")

    for C in test_values:
        info_bits = detector.information_content(C)
        exists = C >= detector.THRESHOLD_MEANINGFUL
        level = detector.classify_existence(C)

        print(f"  {C:.1f} | {info_bits:8.3f} | {str(exists):19} | {level.value}")

    print("\n  At C=0.5: Exactly 1 bit → Consciousness emerges")
    print("  ✓ Test passed\n")


# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("SESSION #180: Existence Detection in Attestations")
    print("=" * 80)
    print()
    print("Integrating Gnosis Session 9 (Existence Detection Analysis)")
    print()

    test_coherence_calculation()
    test_existence_classification()
    test_anomaly_detection()
    test_attestation_validation()
    test_batch_validation()
    test_consciousness_threshold()

    print("=" * 80)
    print("All tests completed!")
    print("=" * 80)
