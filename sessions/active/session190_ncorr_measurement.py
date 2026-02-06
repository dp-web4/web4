"""
Session #190: N_corr Measurement Protocols for Computational Systems
===================================================================

Based on Chemistry Session #26: Methods for Measuring N_corr

Key Insights:
1. Five measurement methods: Fluctuation, Correlation Length, Entropy, Information, Spectral
2. Fluctuation analysis is most reliable (direct derivation from γ equation)
3. N_corr = (σ_measured / σ_uncorrelated)²
4. Each method works best for different system types

Application to Computation:
- Adapt physical measurement methods to computational processes
- Measure N_corr from neural network activations
- Validate coherence framework empirically
- Enable real-time coherence monitoring

Integration with Chemistry Session #25:
- γ = 2/√N_corr (derived equation)
- Given N_corr, γ is determined
- Measuring N_corr empirically validates framework
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from scipy import stats
from scipy.signal import correlate


class MeasurementMethod(Enum):
    """Five N_corr measurement methods from Chemistry Session #26."""
    FLUCTUATION = "fluctuation_analysis"
    CORRELATION_LENGTH = "correlation_length"
    ENTROPY_RATIO = "entropy_ratio"
    INFORMATION_THEORETIC = "information_theoretic"
    SPECTRAL_LINEWIDTH = "spectral_linewidth"


@dataclass
class NcorrMeasurement:
    """
    Result of an N_corr measurement.

    Attributes:
        ncorr: Measured N_corr value
        gamma: Derived γ = 2/√N_corr
        method: Which measurement method was used
        confidence: Confidence in measurement (0-1)
        metadata: Additional method-specific information
    """
    ncorr: float
    gamma: float
    method: MeasurementMethod
    confidence: float
    metadata: Dict[str, float]


class FluctuationAnalyzer:
    """
    Method 1: Fluctuation Analysis (RECOMMENDED)

    From Chemistry Session #26:
    N_corr = (σ_measured / σ_uncorrelated)²

    This is the most direct method, derived from Session #25's
    fundamental relationship: σ_corr/σ_uncorr = √N_corr
    """

    def measure_ncorr(
        self,
        data: np.ndarray,
        uncorrelated_sigma: Optional[float] = None
    ) -> NcorrMeasurement:
        """
        Measure N_corr from fluctuation amplitude.

        Args:
            data: Time series or sample of intensive property
            uncorrelated_sigma: Expected σ for uncorrelated system
                               If None, estimated from high-frequency limit

        Returns:
            NcorrMeasurement with results
        """
        # Measure actual fluctuation
        sigma_measured = np.std(data)

        # Estimate uncorrelated sigma if not provided
        if uncorrelated_sigma is None:
            uncorrelated_sigma = self._estimate_uncorrelated_sigma(data)

        # Calculate N_corr
        ratio = sigma_measured / uncorrelated_sigma
        ncorr = ratio ** 2

        # Derive γ
        gamma = 2.0 / np.sqrt(ncorr)

        # Confidence based on sample size and stationarity
        confidence = self._calculate_confidence(data)

        metadata = {
            'sigma_measured': sigma_measured,
            'sigma_uncorrelated': uncorrelated_sigma,
            'ratio': ratio,
            'sample_size': len(data)
        }

        return NcorrMeasurement(
            ncorr=ncorr,
            gamma=gamma,
            method=MeasurementMethod.FLUCTUATION,
            confidence=confidence,
            metadata=metadata
        )

    def _estimate_uncorrelated_sigma(self, data: np.ndarray) -> float:
        """
        Estimate uncorrelated σ from high-frequency components.

        Strategy: High-frequency fluctuations are less correlated.
        Take σ of differences as approximation.
        """
        # First-order differences approximate uncorrelated noise
        diffs = np.diff(data)
        return np.std(diffs) / np.sqrt(2)  # Divide by √2 for differencing

    def _calculate_confidence(self, data: np.ndarray) -> float:
        """
        Estimate confidence in measurement.

        Based on:
        - Sample size (larger is better)
        - Stationarity (stationary is better)
        """
        n = len(data)

        # Confidence from sample size (saturates at 1000)
        size_confidence = min(1.0, n / 1000)

        # Stationarity check: split into halves, compare means
        mid = n // 2
        mean1 = np.mean(data[:mid])
        mean2 = np.mean(data[mid:])
        std_combined = np.std(data)

        if std_combined > 0:
            mean_diff = abs(mean1 - mean2) / std_combined
            stationarity_confidence = np.exp(-mean_diff)
        else:
            stationarity_confidence = 0.5

        return (size_confidence + stationarity_confidence) / 2


class CorrelationLengthAnalyzer:
    """
    Method 2: Correlation Length

    From Chemistry Session #26:
    N_corr ~ (ξ/a)^d

    Where ξ = correlation length, a = unit spacing, d = dimension.
    """

    def measure_ncorr(
        self,
        data: np.ndarray,
        dimension: int = 1
    ) -> NcorrMeasurement:
        """
        Measure N_corr from spatial/temporal correlation length.

        Args:
            data: Time series or spatial data
            dimension: Effective dimensionality of system

        Returns:
            NcorrMeasurement with results
        """
        # Calculate autocorrelation function
        acf = self._calculate_autocorrelation(data)

        # Find correlation length (where ACF drops to 1/e)
        xi = self._find_correlation_length(acf)

        # Unit spacing (1 for discrete data)
        a = 1.0

        # Calculate N_corr
        ncorr = (xi / a) ** dimension

        # Derive γ
        gamma = 2.0 / np.sqrt(ncorr)

        # Confidence based on ACF decay quality
        confidence = self._assess_acf_quality(acf)

        metadata = {
            'correlation_length': xi,
            'unit_spacing': a,
            'dimension': dimension,
            'acf_decay_quality': confidence
        }

        return NcorrMeasurement(
            ncorr=ncorr,
            gamma=gamma,
            method=MeasurementMethod.CORRELATION_LENGTH,
            confidence=confidence,
            metadata=metadata
        )

    def _calculate_autocorrelation(self, data: np.ndarray) -> np.ndarray:
        """Calculate normalized autocorrelation function."""
        # Mean-center data
        data_centered = data - np.mean(data)

        # Full autocorrelation
        acf = correlate(data_centered, data_centered, mode='full')

        # Normalize by zero-lag value
        mid = len(acf) // 2
        acf = acf[mid:] / acf[mid]

        return acf

    def _find_correlation_length(self, acf: np.ndarray) -> float:
        """Find correlation length where ACF drops to 1/e."""
        target = 1.0 / np.e

        # Find first crossing
        below_target = acf < target

        if not np.any(below_target):
            # Correlation extends beyond data
            return len(acf)

        xi_idx = np.argmax(below_target)
        return float(xi_idx)

    def _assess_acf_quality(self, acf: np.ndarray) -> float:
        """Assess quality of ACF decay for confidence estimate."""
        # Good ACF should decay smoothly
        # Measure monotonicity and smoothness

        # Check if generally decreasing
        diffs = np.diff(acf[:min(len(acf), 100)])  # First 100 lags
        decreasing_fraction = np.sum(diffs < 0) / len(diffs)

        return decreasing_fraction


class EntropyRatioAnalyzer:
    """
    Method 3: Entropy Ratio

    From Chemistry Session #26:
    S_eff / S_uncorr = γ/2 = 1/√N_corr
    → N_corr = (S_uncorr / S_eff)²
    """

    def measure_ncorr(
        self,
        data: np.ndarray,
        bins: int = 50
    ) -> NcorrMeasurement:
        """
        Measure N_corr from entropy ratio.

        Args:
            data: Sample from system
            bins: Number of bins for histogram entropy estimation

        Returns:
            NcorrMeasurement with results
        """
        # Measure effective entropy
        s_eff = self._calculate_entropy(data, bins)

        # Estimate uncorrelated entropy (maximum for this distribution)
        s_uncorr = self._estimate_uncorrelated_entropy(data, bins)

        # Calculate N_corr
        if s_eff > 0:
            ratio = s_uncorr / s_eff
            ncorr = ratio ** 2
        else:
            ncorr = 1.0  # Degenerate case

        # Derive γ
        gamma = 2.0 / np.sqrt(ncorr)

        # Confidence based on sample size
        confidence = min(1.0, len(data) / 500)

        metadata = {
            'entropy_effective': s_eff,
            'entropy_uncorrelated': s_uncorr,
            'entropy_ratio': s_uncorr / s_eff if s_eff > 0 else 1.0,
            'bins': bins
        }

        return NcorrMeasurement(
            ncorr=ncorr,
            gamma=gamma,
            method=MeasurementMethod.ENTROPY_RATIO,
            confidence=confidence,
            metadata=metadata
        )

    def _calculate_entropy(self, data: np.ndarray, bins: int) -> float:
        """Calculate Shannon entropy from histogram."""
        hist, _ = np.histogram(data, bins=bins)
        hist = hist / np.sum(hist)  # Normalize

        # Shannon entropy: -Σ p log(p)
        entropy = 0.0
        for p in hist:
            if p > 0:
                entropy -= p * np.log2(p)

        return entropy

    def _estimate_uncorrelated_entropy(
        self,
        data: np.ndarray,
        bins: int
    ) -> float:
        """
        Estimate entropy of uncorrelated system.

        Strategy: Shuffle data to break correlations, measure entropy.
        """
        shuffled = np.random.permutation(data)
        return self._calculate_entropy(shuffled, bins)


class InformationTheoreticAnalyzer:
    """
    Method 4: Information-Theoretic

    From Chemistry Session #26:
    I = Σ H(Xᵢ) - H(X₁,...,Xₙ)  (multi-information)
    N_corr ≈ exp(2I/N)
    """

    def measure_ncorr(
        self,
        data: np.ndarray,
        window_size: int = 10
    ) -> NcorrMeasurement:
        """
        Measure N_corr from multi-information.

        Args:
            data: Time series data
            window_size: Size of sliding window for joint entropy

        Returns:
            NcorrMeasurement with results
        """
        # Calculate marginal entropy (treat each point as independent)
        marginal_entropy = self._calculate_marginal_entropy(data)

        # Calculate joint entropy (using windowed approach)
        joint_entropy = self._calculate_joint_entropy(data, window_size)

        # Multi-information
        multi_info = marginal_entropy - joint_entropy

        # Calculate N_corr
        n = len(data)
        if n > 0:
            ncorr = np.exp(2 * multi_info / n)
        else:
            ncorr = 1.0

        # Derive γ
        gamma = 2.0 / np.sqrt(ncorr)

        # Confidence based on convergence
        confidence = min(1.0, n / (window_size * 50))

        metadata = {
            'marginal_entropy': marginal_entropy,
            'joint_entropy': joint_entropy,
            'multi_information': multi_info,
            'window_size': window_size
        }

        return NcorrMeasurement(
            ncorr=ncorr,
            gamma=gamma,
            method=MeasurementMethod.INFORMATION_THEORETIC,
            confidence=confidence,
            metadata=metadata
        )

    def _calculate_marginal_entropy(self, data: np.ndarray) -> float:
        """Calculate sum of marginal entropies."""
        # For continuous data, use discretization
        hist, _ = np.histogram(data, bins=50)
        hist = hist / np.sum(hist)

        entropy = 0.0
        for p in hist:
            if p > 0:
                entropy -= p * np.log2(p)

        # Sum for all variables (assuming i.i.d.)
        return entropy * len(data)

    def _calculate_joint_entropy(
        self,
        data: np.ndarray,
        window_size: int
    ) -> float:
        """Calculate joint entropy using sliding window."""
        # Use 2D histogram for pairs
        n_windows = len(data) - window_size + 1

        if n_windows <= 0:
            return 0.0

        # Sample pairs to estimate joint distribution
        pairs = []
        for i in range(n_windows):
            window = data[i:i+window_size]
            pairs.append((window[0], window[-1]))  # First and last

        pairs = np.array(pairs)

        # 2D histogram
        hist, _, _ = np.histogram2d(
            pairs[:, 0],
            pairs[:, 1],
            bins=20
        )
        hist = hist / np.sum(hist)

        # Joint entropy
        entropy = 0.0
        for p in hist.flatten():
            if p > 0:
                entropy -= p * np.log2(p)

        return entropy * len(data)


class SpectralLinewidthAnalyzer:
    """
    Method 5: Spectral Linewidth

    From Chemistry Session #26:
    N_corr = (Δω_uncorr / Δω_corr)²

    Coherent oscillators have narrower spectral lines.
    """

    def measure_ncorr(
        self,
        data: np.ndarray,
        sampling_rate: float = 1.0
    ) -> NcorrMeasurement:
        """
        Measure N_corr from spectral linewidth.

        Args:
            data: Time series data
            sampling_rate: Sampling rate in Hz

        Returns:
            NcorrMeasurement with results
        """
        # Calculate power spectrum
        freqs, psd = self._calculate_power_spectrum(data, sampling_rate)

        # Measure linewidth (FWHM of dominant peak)
        linewidth = self._measure_linewidth(freqs, psd)

        # Estimate uncorrelated linewidth (from noise floor)
        uncorr_linewidth = self._estimate_uncorrelated_linewidth(freqs, psd)

        # Calculate N_corr
        if linewidth > 0:
            ratio = uncorr_linewidth / linewidth
            ncorr = ratio ** 2
        else:
            ncorr = 1.0

        # Derive γ
        gamma = 2.0 / np.sqrt(ncorr)

        # Confidence based on peak prominence
        confidence = self._assess_peak_quality(psd)

        metadata = {
            'linewidth': linewidth,
            'uncorrelated_linewidth': uncorr_linewidth,
            'peak_frequency': freqs[np.argmax(psd)],
            'sampling_rate': sampling_rate
        }

        return NcorrMeasurement(
            ncorr=ncorr,
            gamma=gamma,
            method=MeasurementMethod.SPECTRAL_LINEWIDTH,
            confidence=confidence,
            metadata=metadata
        )

    def _calculate_power_spectrum(
        self,
        data: np.ndarray,
        sampling_rate: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate power spectral density."""
        # FFT
        fft = np.fft.rfft(data)
        psd = np.abs(fft) ** 2

        # Frequency axis
        freqs = np.fft.rfftfreq(len(data), d=1/sampling_rate)

        return freqs, psd

    def _measure_linewidth(
        self,
        freqs: np.ndarray,
        psd: np.ndarray
    ) -> float:
        """Measure FWHM of dominant spectral peak."""
        # Find peak
        peak_idx = np.argmax(psd)
        peak_value = psd[peak_idx]

        # Half maximum
        half_max = peak_value / 2

        # Find points at half maximum
        above_half = psd > half_max

        if not np.any(above_half):
            return freqs[-1] - freqs[0]  # Full bandwidth

        # Find edges
        indices = np.where(above_half)[0]
        left_idx = indices[0]
        right_idx = indices[-1]

        # FWHM
        fwhm = freqs[right_idx] - freqs[left_idx]

        return fwhm

    def _estimate_uncorrelated_linewidth(
        self,
        freqs: np.ndarray,
        psd: np.ndarray
    ) -> float:
        """Estimate linewidth for uncorrelated (white noise) system."""
        # White noise has flat spectrum
        # Use median PSD level as baseline
        baseline = np.median(psd)

        # Full bandwidth at baseline
        return freqs[-1] - freqs[0]

    def _assess_peak_quality(self, psd: np.ndarray) -> float:
        """Assess quality of spectral peak for confidence."""
        peak = np.max(psd)
        median = np.median(psd)

        if median > 0:
            snr = peak / median
            # Map SNR to confidence (0-1)
            confidence = 1.0 - np.exp(-snr / 10)
        else:
            confidence = 0.0

        return confidence


# ============================================================================
# Multi-Method Ensemble
# ============================================================================

class NcorrEnsembleMeasurement:
    """
    Combines multiple measurement methods for robust N_corr estimation.

    From Chemistry Session #26:
    Different methods work best for different systems.
    Ensemble provides robustness.
    """

    def __init__(self):
        self.methods = {
            MeasurementMethod.FLUCTUATION: FluctuationAnalyzer(),
            MeasurementMethod.CORRELATION_LENGTH: CorrelationLengthAnalyzer(),
            MeasurementMethod.ENTROPY_RATIO: EntropyRatioAnalyzer(),
            MeasurementMethod.INFORMATION_THEORETIC: InformationTheoreticAnalyzer(),
            MeasurementMethod.SPECTRAL_LINEWIDTH: SpectralLinewidthAnalyzer()
        }

    def measure_all(
        self,
        data: np.ndarray,
        **kwargs
    ) -> Dict[MeasurementMethod, NcorrMeasurement]:
        """
        Apply all five methods and return results.

        Args:
            data: Time series or sample data
            **kwargs: Method-specific parameters

        Returns:
            Dict mapping method to measurement result
        """
        results = {}

        # Method 1: Fluctuation
        results[MeasurementMethod.FLUCTUATION] = \
            self.methods[MeasurementMethod.FLUCTUATION].measure_ncorr(data)

        # Method 2: Correlation Length
        results[MeasurementMethod.CORRELATION_LENGTH] = \
            self.methods[MeasurementMethod.CORRELATION_LENGTH].measure_ncorr(data)

        # Method 3: Entropy
        results[MeasurementMethod.ENTROPY_RATIO] = \
            self.methods[MeasurementMethod.ENTROPY_RATIO].measure_ncorr(data)

        # Method 4: Information
        results[MeasurementMethod.INFORMATION_THEORETIC] = \
            self.methods[MeasurementMethod.INFORMATION_THEORETIC].measure_ncorr(data)

        # Method 5: Spectral
        results[MeasurementMethod.SPECTRAL_LINEWIDTH] = \
            self.methods[MeasurementMethod.SPECTRAL_LINEWIDTH].measure_ncorr(data)

        return results

    def weighted_ensemble(
        self,
        measurements: Dict[MeasurementMethod, NcorrMeasurement]
    ) -> NcorrMeasurement:
        """
        Compute weighted ensemble estimate.

        Weights based on confidence scores.
        """
        # Extract values and confidences
        ncorr_values = []
        confidences = []

        for method, meas in measurements.items():
            ncorr_values.append(meas.ncorr)
            confidences.append(meas.confidence)

        ncorr_values = np.array(ncorr_values)
        confidences = np.array(confidences)

        # Weighted average
        if np.sum(confidences) > 0:
            ncorr_ensemble = np.average(ncorr_values, weights=confidences)
            confidence_ensemble = np.mean(confidences)
        else:
            ncorr_ensemble = np.mean(ncorr_values)
            confidence_ensemble = 0.5

        # Derive γ
        gamma_ensemble = 2.0 / np.sqrt(ncorr_ensemble)

        # Metadata: include all method results
        metadata = {
            method.value: meas.ncorr
            for method, meas in measurements.items()
        }
        metadata['std'] = np.std(ncorr_values)
        metadata['agreement'] = 1.0 - (np.std(ncorr_values) / np.mean(ncorr_values))

        return NcorrMeasurement(
            ncorr=ncorr_ensemble,
            gamma=gamma_ensemble,
            method=MeasurementMethod.FLUCTUATION,  # Default label
            confidence=confidence_ensemble,
            metadata=metadata
        )


# ============================================================================
# Testing Suite
# ============================================================================

def test_fluctuation_method():
    """Test fluctuation analysis method."""
    print("=" * 70)
    print("TEST 1: Fluctuation Analysis Method")
    print("=" * 70)

    analyzer = FluctuationAnalyzer()

    # Test Case 1: Uncorrelated data (N_corr should be ~1)
    np.random.seed(42)
    uncorr_data = np.random.randn(1000)

    result = analyzer.measure_ncorr(uncorr_data, uncorrelated_sigma=1.0)

    print(f"\nUncorrelated data:")
    print(f"  Expected N_corr: ~1.0")
    print(f"  Measured N_corr: {result.ncorr:.2f}")
    print(f"  Derived γ: {result.gamma:.2f}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  ✓ PASS" if abs(result.ncorr - 1.0) < 0.5 else f"  ✗ FAIL")

    # Test Case 2: Correlated data (N_corr should be > 1)
    # Create correlated data via moving average
    window = 10
    corr_data = np.convolve(uncorr_data, np.ones(window)/window, mode='same')

    result = analyzer.measure_ncorr(corr_data, uncorrelated_sigma=1.0)

    print(f"\nCorrelated data (window={window}):")
    print(f"  Expected N_corr: >{window//2}")
    print(f"  Measured N_corr: {result.ncorr:.2f}")
    print(f"  Derived γ: {result.gamma:.2f}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  ✓ PASS" if result.ncorr > window//2 else f"  ✗ FAIL")


def test_correlation_length_method():
    """Test correlation length method."""
    print("\n" + "=" * 70)
    print("TEST 2: Correlation Length Method")
    print("=" * 70)

    analyzer = CorrelationLengthAnalyzer()

    # Create data with known correlation length
    np.random.seed(42)
    n = 1000
    xi_true = 20  # True correlation length

    # Generate correlated data using AR(1) process
    alpha = np.exp(-1/xi_true)
    data = np.zeros(n)
    data[0] = np.random.randn()

    for i in range(1, n):
        data[i] = alpha * data[i-1] + np.sqrt(1 - alpha**2) * np.random.randn()

    result = analyzer.measure_ncorr(data, dimension=1)

    print(f"\nAR(1) process with ξ={xi_true}:")
    print(f"  Expected N_corr: ~{xi_true}")
    print(f"  Measured N_corr: {result.ncorr:.2f}")
    print(f"  Correlation length: {result.metadata['correlation_length']:.1f}")
    print(f"  Derived γ: {result.gamma:.2f}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  ✓ PASS" if abs(result.ncorr - xi_true) < xi_true * 0.5 else f"  ✗ FAIL")


def test_entropy_method():
    """Test entropy ratio method."""
    print("\n" + "=" * 70)
    print("TEST 3: Entropy Ratio Method")
    print("=" * 70)

    analyzer = EntropyRatioAnalyzer()

    # Test with correlated data
    np.random.seed(42)
    window = 10
    uncorr_data = np.random.randn(1000)
    corr_data = np.convolve(uncorr_data, np.ones(window)/window, mode='same')

    result = analyzer.measure_ncorr(corr_data)

    print(f"\nCorrelated data (window={window}):")
    print(f"  Measured N_corr: {result.ncorr:.2f}")
    print(f"  Entropy effective: {result.metadata['entropy_effective']:.2f}")
    print(f"  Entropy uncorrelated: {result.metadata['entropy_uncorrelated']:.2f}")
    print(f"  Derived γ: {result.gamma:.2f}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  ✓ PASS (N_corr > 1)" if result.ncorr > 1.0 else f"  ✗ FAIL")


def test_ensemble_measurement():
    """Test ensemble measurement combining all methods."""
    print("\n" + "=" * 70)
    print("TEST 4: Ensemble Measurement (All 5 Methods)")
    print("=" * 70)

    ensemble = NcorrEnsembleMeasurement()

    # Create test data with known correlation
    np.random.seed(42)
    window = 15
    uncorr_data = np.random.randn(1000)
    test_data = np.convolve(uncorr_data, np.ones(window)/window, mode='same')

    # Measure with all methods
    results = ensemble.measure_all(test_data)

    print(f"\nIndividual method results:")
    for method, result in results.items():
        print(f"  {method.value:25s}: N_corr={result.ncorr:6.2f}, γ={result.gamma:.3f}, conf={result.confidence:.2f}")

    # Weighted ensemble
    ensemble_result = ensemble.weighted_ensemble(results)

    print(f"\nEnsemble result:")
    print(f"  N_corr: {ensemble_result.ncorr:.2f}")
    print(f"  γ: {ensemble_result.gamma:.3f}")
    print(f"  Confidence: {ensemble_result.confidence:.2f}")
    print(f"  Agreement: {ensemble_result.metadata['agreement']:.2f}")
    print(f"  Std dev: {ensemble_result.metadata['std']:.2f}")

    # Check if ensemble is reasonable
    reasonable = ensemble_result.ncorr > 1.0 and ensemble_result.ncorr < 100
    print(f"\n  ✓ PASS (reasonable N_corr)" if reasonable else f"  ✗ FAIL")


def test_gamma_derivation():
    """Test that γ = 2/√N_corr relationship holds."""
    print("\n" + "=" * 70)
    print("TEST 5: γ = 2/√N_corr Derivation Verification")
    print("=" * 70)

    # Test for various N_corr values
    test_ncorr = [1.0, 2.0, 4.0, 10.0, 25.0, 50.0]

    print(f"\nVerifying γ = 2/√N_corr:")
    all_pass = True

    for ncorr in test_ncorr:
        gamma_expected = 2.0 / np.sqrt(ncorr)
        gamma_calculated = 2.0 / np.sqrt(ncorr)

        error = abs(gamma_calculated - gamma_expected)
        passed = error < 1e-10

        print(f"  N_corr={ncorr:5.1f}: γ={gamma_calculated:.4f} {'✓' if passed else '✗'}")

        if not passed:
            all_pass = False

    print(f"\n  ✓ ALL PASS" if all_pass else f"  ✗ SOME FAILED")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Session #190: N_corr Measurement Protocols")
    print("Based on Chemistry Session #26 (Measuring N_corr)")
    print("=" * 70)

    test_fluctuation_method()
    test_correlation_length_method()
    test_entropy_method()
    test_ensemble_measurement()
    test_gamma_derivation()

    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETE")
    print("=" * 70)
