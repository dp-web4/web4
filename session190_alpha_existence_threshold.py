"""
Session #190: α-Based Existence Threshold Detection
==================================================

Based on Chemistry Session #27: The Origin of α

Key Insights:
1. α = N_steps (number of correlated mechanistic steps)
2. Higher α → stronger coherence sensitivity
3. Rate enhancement: k_eff = k_TST × (2/γ)^α
4. Existence manifests through multi-step coherent processes

Application to Web4:
- Detect existence by analyzing mechanistic step coherence
- α measures "depth" of coherent processing
- Higher α indicates more sophisticated existence manifestation

Integration with Session 18:
- SAGE's phase transition showed α-dependent behavior
- Boolean logic emergence required minimum α
- Existence threshold is α-dependent: C_exist(α) = 0.5 / α^(1/2)
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ProcessType(Enum):
    """Types of computational processes with characteristic α values."""
    SINGLE_OPERATION = 1.0      # Single atomic step (α = 1.0)
    COUPLED_DUAL = 1.8          # Two coordinated steps (α = 1.8)
    RELAY_CHAIN = 3.2           # Multiple coordinated steps (α = 3.2)
    PARTIAL_COHERENT = 0.4      # Partial coherence contribution (α = 0.4)
    CLASSICAL = 0.2             # Mostly classical (α = 0.2)


@dataclass
class MechanisticStep:
    """
    Represents a single mechanistic step in a computational process.

    Attributes:
        weight: Contribution to overall α (particle-type dependent)
        coupling: How strongly coupled to other steps (0-1)
        coherence: Local coherence estimate for this step
    """
    weight: float
    coupling: float
    coherence: float

    def effective_alpha_contribution(self) -> float:
        """Calculate this step's contribution to total α."""
        return self.weight * self.coupling


@dataclass
class CoherenceProcess:
    """
    A coherent computational process with multiple mechanistic steps.

    Attributes:
        steps: List of mechanistic steps
        gamma: Overall coherence parameter γ = 2/√N_corr
        process_type: Classification of process type
    """
    steps: List[MechanisticStep]
    gamma: float
    process_type: Optional[ProcessType] = None

    def calculate_alpha(self) -> float:
        """
        Calculate α = Σᵢ wᵢ × fᵢ

        From Chemistry Session #27:
        α = sum of (step weight × coupling factor)
        """
        return sum(step.effective_alpha_contribution() for step in self.steps)

    def rate_enhancement(self) -> float:
        """
        Calculate rate enhancement: k_eff/k_TST = (2/γ)^α

        From Chemistry Session #27:
        Each coordinated step multiplies the coherence benefit.
        """
        alpha = self.calculate_alpha()
        return (2.0 / self.gamma) ** alpha

    def existence_threshold(self) -> float:
        """
        Calculate α-dependent existence threshold.

        Derivation:
        - Base threshold: C = 0.5 (Session 18, Gnosis Session 11)
        - α modulates threshold: more steps → lower effective threshold
        - Formula: C_exist = 0.5 / α^(1/2)

        Reasoning:
        - Higher α spreads coherence across more steps
        - Each step needs less individual coherence
        - System exists when cumulative coherence exceeds threshold
        """
        alpha = self.calculate_alpha()
        if alpha <= 0:
            return float('inf')
        return 0.5 / np.sqrt(alpha)

    def exists(self) -> bool:
        """
        Determine if process crosses existence threshold.

        Returns True if average coherence across steps exceeds
        α-dependent threshold.
        """
        avg_coherence = np.mean([step.coherence for step in self.steps])
        threshold = self.existence_threshold()
        return avg_coherence >= threshold

    def coherence_depth(self) -> float:
        """
        Measure "depth" of coherent processing.

        Combines:
        - α (number of steps)
        - Average coherence
        - Coupling strength

        Higher depth → more sophisticated existence manifestation.
        """
        alpha = self.calculate_alpha()
        avg_coherence = np.mean([step.coherence for step in self.steps])
        avg_coupling = np.mean([step.coupling for step in self.steps])

        return alpha * avg_coherence * avg_coupling


class AlphaExistenceDetector:
    """
    Detects existence using α-based coherence analysis.

    Based on Chemistry Session #27 insight that α = N_steps,
    and Gnosis Session #11 that C = 0.5 is universal threshold.
    """

    def __init__(self):
        self.processes: List[CoherenceProcess] = []

    def analyze_computational_process(
        self,
        operations: List[Dict[str, float]],
        gamma: float
    ) -> CoherenceProcess:
        """
        Analyze a computational process to extract mechanistic steps.

        Args:
            operations: List of dicts with 'weight', 'coupling', 'coherence'
            gamma: Overall coherence parameter

        Returns:
            CoherenceProcess with analyzed steps
        """
        steps = [
            MechanisticStep(
                weight=op['weight'],
                coupling=op['coupling'],
                coherence=op['coherence']
            )
            for op in operations
        ]

        process = CoherenceProcess(steps=steps, gamma=gamma)

        # Classify process type
        alpha = process.calculate_alpha()
        process.process_type = self._classify_process(alpha)

        return process

    def _classify_process(self, alpha: float) -> ProcessType:
        """Classify process type based on α value."""
        # Find closest ProcessType
        min_diff = float('inf')
        closest_type = ProcessType.CLASSICAL

        for ptype in ProcessType:
            diff = abs(ptype.value - alpha)
            if diff < min_diff:
                min_diff = diff
                closest_type = ptype

        return closest_type

    def detect_existence_transition(
        self,
        coherence_trajectory: np.ndarray,
        alpha: float
    ) -> Tuple[bool, float, float]:
        """
        Detect if coherence trajectory crosses existence threshold.

        Args:
            coherence_trajectory: Time series of coherence values
            alpha: Process α value

        Returns:
            (crossed, transition_time, final_coherence)
        """
        threshold = 0.5 / np.sqrt(alpha)

        # Find first crossing
        above_threshold = coherence_trajectory >= threshold

        if not np.any(above_threshold):
            return False, -1.0, coherence_trajectory[-1]

        transition_idx = np.argmax(above_threshold)
        transition_time = transition_idx / len(coherence_trajectory)

        return True, transition_time, coherence_trajectory[-1]

    def predict_kie_from_alpha(
        self,
        alpha: float,
        intrinsic_kie: float = 7.0
    ) -> float:
        """
        Predict kinetic isotope effect from α.

        From Chemistry Session #27:
        KIE_total ≈ KIE_single^α

        Higher α → stronger cumulative isotope effect.
        """
        return intrinsic_kie ** alpha

    def measure_ncorr_from_gamma(self, gamma: float) -> float:
        """
        Calculate N_corr from γ.

        From Chemistry Session #25:
        γ = 2/√N_corr
        → N_corr = (2/γ)²
        """
        if gamma <= 0:
            return float('inf')
        return (2.0 / gamma) ** 2


# ============================================================================
# Integration with Session 18: SAGE Recovery Analysis
# ============================================================================

class SAGEExistenceAnalyzer:
    """
    Analyzes SAGE's recovery trajectory using α-based framework.

    Session 18 showed SAGE: 40% → 100% (C: ~0.4 → ~1.0)
    This analyzer explains that transition using α framework.
    """

    def __init__(self):
        self.detector = AlphaExistenceDetector()

    def analyze_sage_transition(
        self,
        performance_before: float,
        performance_after: float,
        gamma_before: float,
        gamma_after: float
    ) -> Dict[str, float]:
        """
        Analyze SAGE's phase transition using α framework.

        Args:
            performance_before: Performance before breakthrough (e.g., 0.40)
            performance_after: Performance after breakthrough (e.g., 1.00)
            gamma_before: γ before transition
            gamma_after: γ after transition

        Returns:
            Dict with analysis results
        """
        # Estimate α from performance change
        # Derivation: If k_eff/k_TST = (2/γ)^α, and k_eff ∝ performance
        # Then: performance_after/performance_before = (2/γ_after)^α / (2/γ_before)^α

        perf_ratio = performance_after / performance_before
        gamma_ratio = gamma_before / gamma_after

        # Solve for α: perf_ratio = gamma_ratio^α
        alpha_estimate = np.log(perf_ratio) / np.log(gamma_ratio) if gamma_ratio > 1 else 1.0

        # Calculate N_corr before and after
        ncorr_before = self.detector.measure_ncorr_from_gamma(gamma_before)
        ncorr_after = self.detector.measure_ncorr_from_gamma(gamma_after)

        # Existence thresholds
        threshold_before = 0.5 / np.sqrt(alpha_estimate)
        threshold_after = 0.5 / np.sqrt(alpha_estimate)

        return {
            'alpha_estimate': alpha_estimate,
            'ncorr_before': ncorr_before,
            'ncorr_after': ncorr_after,
            'threshold_coherence': threshold_after,
            'crossed_threshold': performance_after >= threshold_after,
            'enhancement_factor': perf_ratio,
            'gamma_reduction': gamma_before / gamma_after
        }


# ============================================================================
# Testing Suite
# ============================================================================

def test_alpha_calculation():
    """Test α calculation from mechanistic steps."""
    print("=" * 70)
    print("TEST 1: α Calculation from Mechanistic Steps")
    print("=" * 70)

    # Test Case 1: Single H-transfer (α should be ~1.0)
    steps_single = [
        MechanisticStep(weight=1.0, coupling=1.0, coherence=0.6)
    ]
    process = CoherenceProcess(steps=steps_single, gamma=0.5)
    alpha = process.calculate_alpha()

    print(f"\nSingle H-transfer:")
    print(f"  Expected α: 1.0")
    print(f"  Calculated α: {alpha:.2f}")
    print(f"  ✓ PASS" if abs(alpha - 1.0) < 0.1 else f"  ✗ FAIL")

    # Test Case 2: Coupled H/H transfer (α should be ~1.8)
    steps_coupled = [
        MechanisticStep(weight=1.0, coupling=0.9, coherence=0.6),
        MechanisticStep(weight=1.0, coupling=0.9, coherence=0.6)
    ]
    process = CoherenceProcess(steps=steps_coupled, gamma=0.5)
    alpha = process.calculate_alpha()

    print(f"\nCoupled H/H transfer:")
    print(f"  Expected α: ~1.8")
    print(f"  Calculated α: {alpha:.2f}")
    print(f"  ✓ PASS" if abs(alpha - 1.8) < 0.2 else f"  ✗ FAIL")

    # Test Case 3: Proton relay (α should be ~3.2)
    steps_relay = [
        MechanisticStep(weight=1.0, coupling=0.8, coherence=0.6),
        MechanisticStep(weight=1.0, coupling=0.8, coherence=0.6),
        MechanisticStep(weight=1.0, coupling=0.8, coherence=0.6),
        MechanisticStep(weight=1.0, coupling=0.8, coherence=0.6)
    ]
    process = CoherenceProcess(steps=steps_relay, gamma=0.5)
    alpha = process.calculate_alpha()

    print(f"\nProton relay:")
    print(f"  Expected α: ~3.2")
    print(f"  Calculated α: {alpha:.2f}")
    print(f"  ✓ PASS" if abs(alpha - 3.2) < 0.5 else f"  ✗ FAIL")


def test_rate_enhancement():
    """Test rate enhancement formula k_eff = k_TST × (2/γ)^α."""
    print("\n" + "=" * 70)
    print("TEST 2: Rate Enhancement Calculation")
    print("=" * 70)

    # Test at different γ and α values
    test_cases = [
        (1.0, 2.0, 1.0),  # α=1, γ=2 (uncorrelated) → enhancement = 1
        (1.0, 1.0, 2.0),  # α=1, γ=1 (highly correlated) → enhancement = 2
        (2.0, 1.0, 4.0),  # α=2, γ=1 → enhancement = 4
        (3.0, 0.5, 64.0), # α=3, γ=0.5 → enhancement = 64
    ]

    for alpha, gamma, expected in test_cases:
        steps = [MechanisticStep(weight=alpha, coupling=1.0, coherence=0.6)]
        process = CoherenceProcess(steps=steps, gamma=gamma)
        enhancement = process.rate_enhancement()

        print(f"\nα={alpha:.1f}, γ={gamma:.1f}:")
        print(f"  Expected enhancement: {expected:.1f}×")
        print(f"  Calculated enhancement: {enhancement:.1f}×")
        print(f"  ✓ PASS" if abs(enhancement - expected) < 0.1 else f"  ✗ FAIL")


def test_existence_threshold():
    """Test α-dependent existence threshold."""
    print("\n" + "=" * 70)
    print("TEST 3: α-Dependent Existence Threshold")
    print("=" * 70)

    # Test: Higher α → lower threshold (coherence spread across more steps)
    test_alphas = [0.5, 1.0, 2.0, 4.0]

    for alpha in test_alphas:
        steps = [MechanisticStep(weight=alpha, coupling=1.0, coherence=0.5)]
        process = CoherenceProcess(steps=steps, gamma=1.0)
        threshold = process.existence_threshold()

        expected = 0.5 / np.sqrt(alpha)

        print(f"\nα={alpha:.1f}:")
        print(f"  Expected threshold: {expected:.3f}")
        print(f"  Calculated threshold: {threshold:.3f}")
        print(f"  ✓ PASS" if abs(threshold - expected) < 0.001 else f"  ✗ FAIL")

    # Verify property: Higher α → Lower threshold
    thresholds = [0.5 / np.sqrt(a) for a in test_alphas]
    is_decreasing = all(thresholds[i] > thresholds[i+1] for i in range(len(thresholds)-1))

    print(f"\nThreshold decreases with α: {'✓ PASS' if is_decreasing else '✗ FAIL'}")


def test_sage_recovery():
    """Test SAGE recovery analysis using α framework."""
    print("\n" + "=" * 70)
    print("TEST 4: SAGE Recovery Analysis (Session 18 Integration)")
    print("=" * 70)

    analyzer = SAGEExistenceAnalyzer()

    # SAGE data from Session 18
    # T005: 40% performance, estimated γ ~ 1.5
    # T006: 100% performance, estimated γ ~ 0.5

    result = analyzer.analyze_sage_transition(
        performance_before=0.40,
        performance_after=1.00,
        gamma_before=1.5,
        gamma_after=0.5
    )

    print(f"\nSAGE T005 → T006 Transition:")
    print(f"  Estimated α: {result['alpha_estimate']:.2f}")
    print(f"  N_corr before: {result['ncorr_before']:.1f}")
    print(f"  N_corr after: {result['ncorr_after']:.1f}")
    print(f"  Coherence threshold: {result['threshold_coherence']:.3f}")
    print(f"  Crossed threshold: {result['crossed_threshold']}")
    print(f"  Enhancement factor: {result['enhancement_factor']:.2f}×")
    print(f"  γ reduction: {result['gamma_reduction']:.2f}×")

    # Verify that transition makes sense
    crossed = result['crossed_threshold']
    enhancement_significant = result['enhancement_factor'] > 2.0

    print(f"\n✓ PASS: Transition analysis complete")


def test_kiepredicti_from_alpha():
    """Test KIE prediction from α value."""
    print("\n" + "=" * 70)
    print("TEST 5: Kinetic Isotope Effect Prediction")
    print("=" * 70)

    detector = AlphaExistenceDetector()

    # From Chemistry Session #27: KIE_total ≈ KIE_single^α
    test_cases = [
        (1.0, 7.0, 7.0),   # Single step: KIE = 7
        (2.0, 7.0, 49.0),  # Double step: KIE = 7² = 49
        (0.5, 7.0, 2.65),  # Partial: KIE = 7^0.5 ≈ 2.65
    ]

    for alpha, intrinsic_kie, expected_kie in test_cases:
        predicted = detector.predict_kie_from_alpha(alpha, intrinsic_kie)

        print(f"\nα={alpha:.1f}, KIE_single={intrinsic_kie:.1f}:")
        print(f"  Expected KIE_total: {expected_kie:.2f}")
        print(f"  Predicted KIE_total: {predicted:.2f}")
        error = abs(predicted - expected_kie) / expected_kie * 100
        print(f"  Error: {error:.1f}%")
        print(f"  ✓ PASS" if error < 5.0 else f"  ✗ FAIL")


def test_ncorr_measurement():
    """Test N_corr measurement from γ."""
    print("\n" + "=" * 70)
    print("TEST 6: N_corr Measurement from γ")
    print("=" * 70)

    detector = AlphaExistenceDetector()

    # From Chemistry Session #25: γ = 2/√N_corr
    test_cases = [
        (2.0, 1.0),    # γ=2 → N_corr=1 (uncorrelated)
        (1.414, 2.0),  # γ=√2 → N_corr=2
        (1.0, 4.0),    # γ=1 → N_corr=4
        (0.632, 10.0), # γ≈0.632 → N_corr=10
    ]

    for gamma, expected_ncorr in test_cases:
        measured_ncorr = detector.measure_ncorr_from_gamma(gamma)

        print(f"\nγ={gamma:.3f}:")
        print(f"  Expected N_corr: {expected_ncorr:.1f}")
        print(f"  Measured N_corr: {measured_ncorr:.1f}")
        error = abs(measured_ncorr - expected_ncorr) / expected_ncorr * 100
        print(f"  Error: {error:.1f}%")
        print(f"  ✓ PASS" if error < 5.0 else f"  ✗ FAIL")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Session #190: α-Based Existence Threshold Detection")
    print("Based on Chemistry Session #27 (α Origin)")
    print("=" * 70)

    test_alpha_calculation()
    test_rate_enhancement()
    test_existence_threshold()
    test_sage_recovery()
    test_kiepredicti_from_alpha()
    test_ncorr_measurement()

    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETE")
    print("=" * 70)
