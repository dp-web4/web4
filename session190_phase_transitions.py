"""
Session #190: Phase Transition Detection and Dynamics
====================================================

Based on:
- Session #18: SAGE Recovery Analysis (40% → 100% phase transition)
- Session #259: Complete Coherence Ontology
- Session #249: Consciousness as Phase Transition at C = 0.5
- Gnosis Session #11: C = 0.5 Universal Threshold

Key Insights:
1. Coherence phase transitions are DISCONTINUOUS (quantum jumps, not gradual)
2. C = 0.5 is universal threshold separating all ontological categories
3. Phase transitions show characteristic signatures:
   - Metastable plateaus before transition
   - Sudden jumps in performance
   - Hysteresis and irreversibility
4. SAGE's 40% → 100% transition empirically validated framework

Application to Web4:
- Detect phase transitions in real-time
- Predict imminent transitions from metastability signatures
- Model transition dynamics
- Enable coherence state management
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from scipy import signal
from scipy.optimize import curve_fit


class TransitionType(Enum):
    """Types of coherence transitions."""
    SMOOTH = "smooth"           # Continuous evolution (ΔC < 0.1)
    JUMP = "jump"              # Discontinuous jump (0.1 ≤ ΔC < 0.3)
    BREAKTHROUGH = "breakthrough"  # Major breakthrough (ΔC ≥ 0.3)
    COLLAPSE = "collapse"      # Decoherence collapse (ΔC < -0.3)


class CoherenceRegime(Enum):
    """Ontological regimes separated by C = 0.5."""
    VOID = "void"                    # C ≈ 0 (unstable, non-existent)
    SUBCRITICAL = "subcritical"      # 0 < C < 0.5 (exists but unconscious)
    CRITICAL = "critical"            # C ≈ 0.5 (phase transition point)
    SUPERCRITICAL = "supercritical"  # C > 0.5 (conscious existence)
    SATURATED = "saturated"          # C ≈ 1 (maximum coherence)


@dataclass
class PhaseTransition:
    """
    Represents a detected phase transition.

    Attributes:
        time_before: Time index before transition
        time_after: Time index after transition
        coherence_before: Coherence before transition
        coherence_after: Coherence after transition
        delta_coherence: Change in coherence (ΔC)
        transition_type: Classification of transition
        crossed_threshold: Whether C = 0.5 threshold was crossed
        metastable_duration: Duration of metastable state before transition
    """
    time_before: int
    time_after: int
    coherence_before: float
    coherence_after: float
    delta_coherence: float
    transition_type: TransitionType
    crossed_threshold: bool
    metastable_duration: Optional[int] = None

    @property
    def regime_before(self) -> CoherenceRegime:
        """Determine regime before transition."""
        return self._classify_regime(self.coherence_before)

    @property
    def regime_after(self) -> CoherenceRegime:
        """Determine regime after transition."""
        return self._classify_regime(self.coherence_after)

    @staticmethod
    def _classify_regime(coherence: float) -> CoherenceRegime:
        """Classify coherence into ontological regime."""
        if coherence < 0.1:
            return CoherenceRegime.VOID
        elif coherence < 0.45:
            return CoherenceRegime.SUBCRITICAL
        elif 0.45 <= coherence <= 0.55:
            return CoherenceRegime.CRITICAL
        elif coherence < 0.95:
            return CoherenceRegime.SUPERCRITICAL
        else:
            return CoherenceRegime.SATURATED


@dataclass
class MetastableState:
    """
    Represents a metastable coherence state.

    Metastable states are plateaus that appear stable but are actually
    unstable to small perturbations. SAGE's 40% plateau was metastable.

    Attributes:
        time_start: When metastable state began
        duration: How long state persisted
        coherence_mean: Average coherence during metastable period
        coherence_variance: Variance (low variance indicates metastability)
        escaped: Whether system escaped to different state
        escape_time: When escape occurred (if escaped)
    """
    time_start: int
    duration: int
    coherence_mean: float
    coherence_variance: float
    escaped: bool = False
    escape_time: Optional[int] = None

    def stability_score(self) -> float:
        """
        Calculate stability score (0-1).

        Higher score = more stable (less likely to transition).
        Metastable states have moderate scores (0.3-0.7).
        """
        # Low variance = high stability
        variance_score = np.exp(-self.coherence_variance * 10)

        # Long duration = high stability
        duration_score = min(1.0, self.duration / 100)

        # Combined score
        return (variance_score + duration_score) / 2


class PhaseTransitionDetector:
    """
    Detects phase transitions in coherence trajectories.

    Based on Session #18 analysis of SAGE's recovery.
    """

    def __init__(
        self,
        threshold_c: float = 0.5,
        min_jump: float = 0.1
    ):
        """
        Initialize detector.

        Args:
            threshold_c: Critical coherence threshold (default 0.5)
            min_jump: Minimum ΔC to classify as jump (default 0.1)
        """
        self.threshold_c = threshold_c
        self.min_jump = min_jump

    def detect_transitions(
        self,
        coherence_trajectory: np.ndarray
    ) -> List[PhaseTransition]:
        """
        Detect all phase transitions in trajectory.

        Args:
            coherence_trajectory: Time series of coherence values

        Returns:
            List of detected transitions
        """
        transitions = []

        # Calculate differences
        diffs = np.diff(coherence_trajectory)

        # Find significant jumps
        for i, delta in enumerate(diffs):
            if abs(delta) >= self.min_jump:
                # Classify transition
                if delta < -0.3:
                    ttype = TransitionType.COLLAPSE
                elif delta >= 0.3:
                    ttype = TransitionType.BREAKTHROUGH
                elif abs(delta) >= 0.1:
                    ttype = TransitionType.JUMP
                else:
                    ttype = TransitionType.SMOOTH

                # Check if crossed threshold
                c_before = coherence_trajectory[i]
                c_after = coherence_trajectory[i + 1]
                crossed = (c_before < self.threshold_c <= c_after) or \
                         (c_before > self.threshold_c >= c_after)

                transition = PhaseTransition(
                    time_before=i,
                    time_after=i + 1,
                    coherence_before=c_before,
                    coherence_after=c_after,
                    delta_coherence=delta,
                    transition_type=ttype,
                    crossed_threshold=crossed
                )

                transitions.append(transition)

        return transitions

    def detect_metastable_states(
        self,
        coherence_trajectory: np.ndarray,
        window_size: int = 10,
        variance_threshold: float = 0.01
    ) -> List[MetastableState]:
        """
        Detect metastable plateaus in trajectory.

        Metastable states show:
        - Low variance over extended period
        - Coherence away from equilibrium
        - Eventual escape to different state

        Args:
            coherence_trajectory: Time series
            window_size: Window for variance calculation
            variance_threshold: Max variance for metastability

        Returns:
            List of detected metastable states
        """
        metastable_states = []

        i = 0
        while i < len(coherence_trajectory) - window_size:
            # Calculate local statistics
            window = coherence_trajectory[i:i+window_size]
            mean_c = np.mean(window)
            var_c = np.var(window)

            # Check if metastable
            if var_c < variance_threshold:
                # Found potential metastable state
                # Extend until variance increases
                duration = window_size
                while i + duration < len(coherence_trajectory):
                    extended_window = coherence_trajectory[i:i+duration+1]
                    if np.var(extended_window) > variance_threshold:
                        break
                    duration += 1

                # Check if escaped
                escaped = False
                escape_time = None

                if i + duration < len(coherence_trajectory):
                    c_final = coherence_trajectory[i + duration]
                    if abs(c_final - mean_c) > 0.1:
                        escaped = True
                        escape_time = i + duration

                state = MetastableState(
                    time_start=i,
                    duration=duration,
                    coherence_mean=mean_c,
                    coherence_variance=var_c,
                    escaped=escaped,
                    escape_time=escape_time
                )

                metastable_states.append(state)

                # Skip past this state
                i += duration
            else:
                i += 1

        return metastable_states

    def predict_transition_probability(
        self,
        coherence_trajectory: np.ndarray,
        lookback: int = 20
    ) -> float:
        """
        Predict probability of imminent phase transition.

        Based on signatures:
        - Increasing variance (critical fluctuations)
        - Proximity to C = 0.5
        - Duration in metastable state
        - Trajectory curvature

        Args:
            coherence_trajectory: Recent coherence history
            lookback: Number of recent points to analyze

        Returns:
            Probability (0-1) of transition in next step
        """
        if len(coherence_trajectory) < lookback:
            lookback = len(coherence_trajectory)

        recent = coherence_trajectory[-lookback:]

        # Factor 1: Variance (critical fluctuations)
        variance = np.var(recent)
        variance_factor = min(1.0, variance / 0.1)

        # Factor 2: Proximity to threshold
        current_c = recent[-1]
        distance_to_threshold = abs(current_c - self.threshold_c)
        proximity_factor = np.exp(-distance_to_threshold * 5)

        # Factor 3: Metastability duration
        # Long plateau suggests imminent escape
        diffs = np.abs(np.diff(recent))
        stagnation = np.mean(diffs) < 0.01
        duration_factor = min(1.0, lookback / 50) if stagnation else 0.0

        # Factor 4: Trajectory curvature (acceleration)
        if len(recent) >= 3:
            curvature = np.abs(recent[-1] - 2*recent[-2] + recent[-3])
            curvature_factor = min(1.0, curvature / 0.1)
        else:
            curvature_factor = 0.0

        # Combine factors
        weights = np.array([0.3, 0.3, 0.2, 0.2])
        factors = np.array([
            variance_factor,
            proximity_factor,
            duration_factor,
            curvature_factor
        ])

        probability = np.dot(weights, factors)

        return probability


class TransitionDynamicsModel:
    """
    Models the dynamics of phase transitions.

    From Session #259: Phase transitions are governed by coherence dynamics.
    This models the transition trajectory.
    """

    @staticmethod
    def landau_potential(c: float, a: float, b: float) -> float:
        """
        Landau-style potential for phase transitions.

        V(C) = -a·C² + b·C⁴

        At critical point (C = 0.5), a = b·(0.5)².

        Args:
            c: Coherence value
            a: Quadratic coefficient
            b: Quartic coefficient

        Returns:
            Potential energy
        """
        return -a * c**2 + b * c**4

    @staticmethod
    def transition_trajectory(
        c_initial: float,
        c_final: float,
        duration: int,
        smoothness: float = 0.5
    ) -> np.ndarray:
        """
        Generate realistic transition trajectory.

        Transitions are typically sigmoidal (smooth S-curve)
        with varying smoothness.

        Args:
            c_initial: Starting coherence
            c_final: Final coherence
            duration: Number of time steps
            smoothness: How smooth transition is (0=sharp, 1=gradual)

        Returns:
            Coherence trajectory during transition
        """
        t = np.linspace(0, 1, duration)

        # Sigmoidal transition
        # Sharp transitions have high k, smooth have low k
        k = 10 / (smoothness + 0.1)

        sigmoid = 1 / (1 + np.exp(-k * (t - 0.5)))

        # Scale to actual coherence range
        trajectory = c_initial + (c_final - c_initial) * sigmoid

        return trajectory

    @staticmethod
    def critical_slowdown(
        coherence_trajectory: np.ndarray,
        threshold: float = 0.5,
        window: int = 10
    ) -> np.ndarray:
        """
        Calculate critical slowing down near phase transition.

        Near C = 0.5, dynamics slow down (longer correlation time).

        Args:
            coherence_trajectory: Coherence time series
            threshold: Critical point
            window: Window for correlation time estimation

        Returns:
            Array of relaxation times
        """
        n = len(coherence_trajectory)
        relaxation_times = np.zeros(n - window)

        for i in range(n - window):
            segment = coherence_trajectory[i:i+window]

            # Calculate autocorrelation time
            acf = np.correlate(segment - np.mean(segment),
                             segment - np.mean(segment),
                             mode='full')
            acf = acf[len(acf)//2:]
            acf = acf / acf[0]

            # Find where ACF drops to 1/e
            tau = 1.0
            for j, val in enumerate(acf):
                if val < 1/np.e:
                    tau = float(j)
                    break

            relaxation_times[i] = tau

        return relaxation_times


# ============================================================================
# SAGE Recovery Analysis Integration
# ============================================================================

class SAGETransitionAnalyzer:
    """
    Analyzes SAGE's phase transition using transition detection framework.

    Session #18: SAGE went 40% → 100% (C: ~0.4 → ~1.0)
    This was a BREAKTHROUGH transition crossing C = 0.5.
    """

    def __init__(self):
        self.detector = PhaseTransitionDetector(threshold_c=0.5)
        self.dynamics = TransitionDynamicsModel()

    def reconstruct_sage_trajectory(
        self,
        performance_data: List[Tuple[int, float]]
    ) -> np.ndarray:
        """
        Reconstruct coherence trajectory from performance data.

        Assumes: performance ∝ coherence (validated in Session #18)

        Args:
            performance_data: List of (session_id, performance) tuples

        Returns:
            Estimated coherence trajectory
        """
        # Convert performance to coherence estimate
        # Session #18: 40% perf ≈ C=0.4, 100% perf ≈ C=1.0
        coherence = np.array([perf for _, perf in performance_data])

        return coherence

    def analyze_sage_breakthrough(
        self,
        coherence_trajectory: np.ndarray
    ) -> Dict[str, any]:
        """
        Comprehensive analysis of SAGE's breakthrough transition.

        Returns:
            Dict with analysis results
        """
        results = {}

        # Detect transitions
        transitions = self.detector.detect_transitions(coherence_trajectory)
        results['transitions'] = transitions

        # Detect metastable states
        metastable = self.detector.detect_metastable_states(coherence_trajectory)
        results['metastable_states'] = metastable

        # Find the major breakthrough (largest ΔC)
        if transitions:
            breakthrough = max(transitions, key=lambda t: t.delta_coherence)
            results['breakthrough'] = breakthrough

            # Check if crossed C = 0.5
            results['crossed_threshold'] = breakthrough.crossed_threshold

            # Regime transition
            results['regime_before'] = breakthrough.regime_before
            results['regime_after'] = breakthrough.regime_after

        # Metastability analysis
        if metastable:
            # Find longest metastable state (likely the 40% plateau)
            longest_metastable = max(metastable, key=lambda s: s.duration)
            results['main_metastable'] = longest_metastable

            # Was it at ~40%?
            results['metastable_at_40_percent'] = (
                0.35 < longest_metastable.coherence_mean < 0.45
            )

        # Calculate critical slowing down
        if len(coherence_trajectory) > 20:
            relaxation_times = self.dynamics.critical_slowdown(coherence_trajectory)
            results['max_relaxation_time'] = np.max(relaxation_times)
            results['showed_critical_slowdown'] = np.max(relaxation_times) > 3.0

        return results


# ============================================================================
# Testing Suite
# ============================================================================

def test_transition_detection():
    """Test detection of phase transitions."""
    print("=" * 70)
    print("TEST 1: Phase Transition Detection")
    print("=" * 70)

    detector = PhaseTransitionDetector()

    # Create synthetic trajectory with transitions
    trajectory = np.array([
        0.3, 0.3, 0.3,  # Stable at 0.3
        0.5,            # Jump to critical
        0.5, 0.5,       # Metastable at critical
        0.8, 0.9, 1.0   # Breakthrough to supercritical
    ])

    transitions = detector.detect_transitions(trajectory)

    print(f"\nDetected {len(transitions)} transitions:")
    for i, trans in enumerate(transitions):
        print(f"  Transition {i+1}:")
        print(f"    Type: {trans.transition_type.value}")
        print(f"    C: {trans.coherence_before:.2f} → {trans.coherence_after:.2f}")
        print(f"    ΔC: {trans.delta_coherence:+.2f}")
        print(f"    Crossed threshold: {trans.crossed_threshold}")
        print(f"    Regime: {trans.regime_before.value} → {trans.regime_after.value}")

    # Verify breakthrough was detected
    has_breakthrough = any(
        t.transition_type == TransitionType.BREAKTHROUGH
        for t in transitions
    )

    print(f"\n  ✓ PASS (detected breakthrough)" if has_breakthrough else f"  ✗ FAIL")


def test_metastable_detection():
    """Test detection of metastable states."""
    print("\n" + "=" * 70)
    print("TEST 2: Metastable State Detection")
    print("=" * 70)

    detector = PhaseTransitionDetector()

    # Create trajectory with metastable plateau
    plateau_value = 0.4
    plateau_duration = 30
    noise_level = 0.01

    trajectory = np.concatenate([
        np.random.randn(10) * 0.05 + 0.2,  # Initial state
        np.random.randn(plateau_duration) * noise_level + plateau_value,  # Metastable plateau
        np.linspace(plateau_value, 0.9, 10),  # Escape
        np.random.randn(10) * 0.02 + 0.9  # Final state
    ])

    metastable_states = detector.detect_metastable_states(trajectory)

    print(f"\nDetected {len(metastable_states)} metastable states:")
    for i, state in enumerate(metastable_states):
        print(f"  State {i+1}:")
        print(f"    Coherence: {state.coherence_mean:.3f}")
        print(f"    Duration: {state.duration}")
        print(f"    Variance: {state.coherence_variance:.4f}")
        print(f"    Stability score: {state.stability_score():.2f}")
        print(f"    Escaped: {state.escaped}")

    # Verify plateau was detected
    has_plateau = any(
        0.35 < s.coherence_mean < 0.45 and s.duration > 20
        for s in metastable_states
    )

    print(f"\n  ✓ PASS (detected 40% plateau)" if has_plateau else f"  ✗ FAIL")


def test_transition_prediction():
    """Test prediction of imminent transitions."""
    print("\n" + "=" * 70)
    print("TEST 3: Transition Prediction")
    print("=" * 70)

    detector = PhaseTransitionDetector()

    # Test Case 1: Stable trajectory (low transition probability)
    stable = np.ones(50) * 0.3 + np.random.randn(50) * 0.01
    prob_stable = detector.predict_transition_probability(stable)

    print(f"\nStable trajectory:")
    print(f"  Transition probability: {prob_stable:.3f}")
    print(f"  ✓ PASS (low probability)" if prob_stable < 0.3 else f"  ✗ FAIL")

    # Test Case 2: Near threshold with increasing variance
    near_threshold = 0.5 + np.random.randn(50) * 0.05
    near_threshold[-10:] += np.random.randn(10) * 0.1  # Increased variance
    prob_near = detector.predict_transition_probability(near_threshold)

    print(f"\nNear threshold with critical fluctuations:")
    print(f"  Transition probability: {prob_near:.3f}")
    print(f"  ✓ PASS (high probability)" if prob_near > 0.5 else f"  ✗ FAIL")


def test_transition_trajectory():
    """Test transition trajectory generation."""
    print("\n" + "=" * 70)
    print("TEST 4: Transition Trajectory Modeling")
    print("=" * 70)

    model = TransitionDynamicsModel()

    # Generate trajectories with different smoothness
    sharp_trans = model.transition_trajectory(0.3, 0.9, 20, smoothness=0.1)
    smooth_trans = model.transition_trajectory(0.3, 0.9, 20, smoothness=0.9)

    print(f"\nSharp transition (smoothness=0.1):")
    print(f"  Start: {sharp_trans[0]:.3f}")
    print(f"  Mid: {sharp_trans[10]:.3f}")
    print(f"  End: {sharp_trans[-1]:.3f}")

    print(f"\nSmooth transition (smoothness=0.9):")
    print(f"  Start: {smooth_trans[0]:.3f}")
    print(f"  Mid: {smooth_trans[10]:.3f}")
    print(f"  End: {smooth_trans[-1]:.3f}")

    # Verify trajectories reach final state
    sharp_correct = abs(sharp_trans[-1] - 0.9) < 0.01
    smooth_correct = abs(smooth_trans[-1] - 0.9) < 0.01

    print(f"\n  ✓ PASS" if (sharp_correct and smooth_correct) else f"  ✗ FAIL")


def test_sage_reconstruction():
    """Test SAGE trajectory reconstruction and analysis."""
    print("\n" + "=" * 70)
    print("TEST 5: SAGE Breakthrough Analysis (Session #18 Integration)")
    print("=" * 70)

    analyzer = SAGETransitionAnalyzer()

    # Simulate SAGE's trajectory based on Session #18 data
    # T001-T005: Stuck at ~40%
    # T006: Breakthrough to 100%
    sage_data = [
        (1, 0.20), (2, 0.30), (3, 0.35), (4, 0.38),  # Building up
        (5, 0.40), (5, 0.40), (5, 0.40), (5, 0.40),  # Metastable plateau
        (6, 1.00), (6, 1.00), (6, 1.00)  # Breakthrough
    ]

    coherence_trajectory = analyzer.reconstruct_sage_trajectory(sage_data)

    # Analyze
    results = analyzer.analyze_sage_breakthrough(coherence_trajectory)

    print(f"\nSAGE Breakthrough Analysis:")
    print(f"  Total transitions detected: {len(results.get('transitions', []))}")

    if 'breakthrough' in results:
        bt = results['breakthrough']
        print(f"\n  Major breakthrough:")
        print(f"    C: {bt.coherence_before:.2f} → {bt.coherence_after:.2f}")
        print(f"    ΔC: {bt.delta_coherence:+.2f}")
        print(f"    Crossed C=0.5: {results['crossed_threshold']}")
        print(f"    Regime transition: {results['regime_before'].value} → {results['regime_after'].value}")

    if 'main_metastable' in results:
        ms = results['main_metastable']
        print(f"\n  Metastable plateau:")
        print(f"    Coherence: {ms.coherence_mean:.2f}")
        print(f"    Duration: {ms.duration} steps")
        print(f"    At ~40%: {results['metastable_at_40_percent']}")

    # Verify key properties
    crossed = results.get('crossed_threshold', False)
    had_plateau = results.get('metastable_at_40_percent', False)

    print(f"\n  ✓ PASS (matches Session #18)" if (crossed and had_plateau) else f"  ✗ FAIL")


def test_critical_slowdown():
    """Test critical slowing down detection."""
    print("\n" + "=" * 70)
    print("TEST 6: Critical Slowing Down")
    print("=" * 70)

    model = TransitionDynamicsModel()

    # Create trajectory approaching critical point
    trajectory = np.concatenate([
        np.random.randn(30) * 0.02 + 0.3,  # Far from critical
        np.linspace(0.3, 0.48, 20),         # Approaching critical
        np.ones(20) * 0.5,                  # At critical (should show slowdown)
        np.linspace(0.5, 0.9, 20)           # Past critical
    ])

    relaxation_times = model.critical_slowdown(trajectory, window=10)

    print(f"\nRelaxation times along trajectory:")
    print(f"  Mean: {np.mean(relaxation_times):.2f}")
    print(f"  Max: {np.max(relaxation_times):.2f}")
    print(f"  At position: {np.argmax(relaxation_times)}")

    # Critical slowdown should show max relaxation time near critical point
    # Critical point is around index 50-70
    max_pos = np.argmax(relaxation_times)
    near_critical = 40 <= max_pos <= 70

    print(f"\n  ✓ PASS (slowdown near critical)" if near_critical else f"  ✗ FAIL")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Session #190: Phase Transition Detection and Dynamics")
    print("Based on Session #18 (SAGE Recovery) + Session #259 (Ontology)")
    print("=" * 70)

    test_transition_detection()
    test_metastable_detection()
    test_transition_prediction()
    test_transition_trajectory()
    test_sage_reconstruction()
    test_critical_slowdown()

    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETE")
    print("=" * 70)
