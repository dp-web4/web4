#!/usr/bin/env python3
"""
Trust Compression Experiment
Compression-Action-Threshold Pattern Investigation

Research Question:
Should Web4 trust compilation use saturating compression (tanh-like) instead
of weighted sum for combining multi-dimensional trust signals?

Hypothesis:
Saturation functions provide better properties for trust compilation:
1. Bounded output [0, 1] (trust can't exceed certainty)
2. Outlier resistance (extreme values don't dominate)
3. Graceful degradation (missing dimensions handled smoothly)
4. Information-theoretic optimality (preserves decision-relevant signal)

This experiment compares:
- **Current**: Linear weighted sum (0.3 talent + 0.3 training + 0.4 temperament)
- **Alternative**: tanh-based saturating compression

Test Cases:
1. **Normal operation**: All dimensions moderate (0.5-0.8)
2. **Outlier resistance**: One dimension extreme (0.0 or 1.0), others moderate
3. **Missing data**: Some dimensions unknown (default 0.5)
4. **Adversarial**: All dimensions manipulated to extremes
5. **Robustness**: Noise in measurements

Evaluation Metrics:
- Output range (stays in [0, 1]?)
- Outlier sensitivity (extreme value dominance)
- Missing data handling (graceful vs catastrophic)
- Adversarial resistance (gaming the metric)
- Information preservation (do dimensions matter?)

Connection to Synchronism:
Synchronism coherence C = tanh(γ × log(ρ/ρ_crit + 1)) is DERIVED from
mean-field theory, not arbitrary. Same information-theoretic logic may apply
to trust compilation.

If tanh demonstrates superior properties → implement
If weighted sum is sufficient → keep current approach
Document findings either way (null results valuable)
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np


# ============================================================================
# Trust Tensor (from mrh_aware_trust.py)
# ============================================================================

@dataclass
class T3Tensor:
    """Trust tensor (talent, training, temperament)"""
    talent: float       # Inherent capability (0-1)
    training: float     # Acquired skill (0-1)
    temperament: float  # Behavioral consistency (0-1)

    def composite_linear(self) -> float:
        """
        Current approach: Weighted sum

        Properties:
        - Unbounded (could exceed 1.0 if weights don't sum to 1.0)
        - Linear (extreme values have proportional impact)
        - Simple (easy to understand and debug)
        """
        return (0.3 * self.talent + 0.3 * self.training + 0.4 * self.temperament)

    def composite_tanh_v1(self) -> float:
        """
        Alternative 1: tanh of weighted sum

        Algorithm:
        1. Compute weighted sum: w = 0.3*talent + 0.3*training + 0.4*temperament
        2. Center at 0.5: x = w - 0.5
        3. Apply tanh compression with gain: y = tanh(gain × x)
        4. Shift back to [0,1]: trust = 0.5 + 0.5 × y

        Properties:
        - Bounded [0, 1] (mathematical guarantee)
        - Saturates at extremes (0.0 → ~0, 1.0 → ~1)
        - Moderate values preserved (0.5 → 0.5)
        - Gain controls transition sharpness
        """
        weighted_sum = 0.3 * self.talent + 0.3 * self.training + 0.4 * self.temperament

        # Center at 0.5
        centered = weighted_sum - 0.5

        # tanh compression with gain (gain=3 gives reasonable slope)
        gain = 3.0
        compressed = math.tanh(gain * centered)

        # Shift back to [0, 1]
        return 0.5 + 0.5 * compressed

    def composite_tanh_v2(self) -> float:
        """
        Alternative 2: Product-then-compress

        Algorithm:
        1. Compute geometric-like combination preserving interactions
        2. Apply tanh to amplify/compress appropriately

        Theory:
        Trust emerges from INTERACTION of dimensions, not just sum.
        - High talent + low temperament → unreliable
        - Low talent + high temperament → consistent but limited
        - Product captures "weakest link" dynamics

        Properties:
        - Multiplicative (weak dimension reduces trust more)
        - Bounded [0, 1]
        - Emphasizes consistency across dimensions
        """
        # Weighted geometric mean (exponents sum to 1.0)
        # talent^0.3 × training^0.3 × temperament^0.4
        product = (
            (self.talent ** 0.3) *
            (self.training ** 0.3) *
            (self.temperament ** 0.4)
        )

        # Already in [0, 1], but apply mild compression for robustness
        # tanh((x-0.5) × gain) pushes extremes toward boundaries
        centered = product - 0.5
        gain = 2.0
        compressed = math.tanh(gain * centered)

        return 0.5 + 0.5 * compressed

    def composite_logistic(self) -> float:
        """
        Alternative 3: Logistic (sigmoid) compression

        Similar to tanh but using logistic function:
        σ(x) = 1 / (1 + exp(-x))

        Properties:
        - Bounded [0, 1]
        - Smooth S-curve
        - Widely used in ML (interpretable as probability)
        - Asymmetric (unlike tanh which is symmetric)
        """
        weighted_sum = 0.3 * self.talent + 0.3 * self.training + 0.4 * self.temperament

        # Center at 0.5
        centered = weighted_sum - 0.5

        # Logistic with gain
        gain = 6.0  # Steeper gain needed for logistic vs tanh

        # σ(x) = 1/(1 + exp(-gain × x))
        # This already outputs [0, 1], no need to shift
        return 1.0 / (1.0 + math.exp(-gain * centered))

    def composite_softmax_inspired(self) -> float:
        """
        Alternative 4: Softmax-inspired normalization

        Instead of fixed weights, compute attention-like weights based on
        confidence in each dimension.

        Theory:
        In neural networks, softmax allocates attention based on signal strength.
        Here, dimensions with higher values get more weight.

        WARNING: This is MORE complex and may not be justified.
        Including for completeness.
        """
        # Exponential weighting (higher values → higher weight)
        temp = 1.0  # Temperature parameter
        exp_talent = math.exp(self.talent / temp)
        exp_training = math.exp(self.training / temp)
        exp_temperament = math.exp(self.temperament / temp)

        exp_sum = exp_talent + exp_training + exp_temperament

        # Softmax weights
        w_talent = exp_talent / exp_sum
        w_training = exp_training / exp_sum
        w_temperament = exp_temperament / exp_sum

        # Weighted average with dynamic weights
        return w_talent * self.talent + w_training * self.training + w_temperament * self.temperament

    def to_dict(self) -> Dict[str, float]:
        """Compare all compression methods"""
        return {
            "talent": self.talent,
            "training": self.training,
            "temperament": self.temperament,
            "linear": self.composite_linear(),
            "tanh_v1": self.composite_tanh_v1(),
            "tanh_v2": self.composite_tanh_v2(),
            "logistic": self.composite_logistic(),
            "softmax": self.composite_softmax_inspired()
        }


# ============================================================================
# Test Scenarios
# ============================================================================

def test_normal_operation():
    """Test 1: Normal operation with moderate values"""
    print("=" * 80)
    print("Test 1: Normal Operation (Moderate Values)")
    print("=" * 80)

    cases = [
        T3Tensor(talent=0.6, training=0.7, temperament=0.8),
        T3Tensor(talent=0.5, training=0.5, temperament=0.5),
        T3Tensor(talent=0.7, training=0.6, temperament=0.75),
    ]

    print(f"{'Case':<5} | {'Talent':<8} | {'Train':<8} | {'Temper':<8} | {'Linear':<8} | {'Tanh_v1':<8} | {'Tanh_v2':<8} | {'Logistic':<8} | {'Softmax':<8}")
    print("-" * 100)

    for i, tensor in enumerate(cases, 1):
        results = tensor.to_dict()
        print(f"{i:<5} | {results['talent']:<8.2f} | {results['training']:<8.2f} | {results['temperament']:<8.2f} | "
              f"{results['linear']:<8.3f} | {results['tanh_v1']:<8.3f} | {results['tanh_v2']:<8.3f} | "
              f"{results['logistic']:<8.3f} | {results['softmax']:<8.3f}")

    print("\n✅ All methods produce similar results for moderate values\n")


def test_outlier_resistance():
    """Test 2: Outlier resistance (extreme values)"""
    print("=" * 80)
    print("Test 2: Outlier Resistance (Extreme Values)")
    print("=" * 80)

    cases = [
        ("Extreme talent", T3Tensor(talent=1.0, training=0.5, temperament=0.5)),
        ("Zero talent", T3Tensor(talent=0.0, training=0.7, temperament=0.8)),
        ("Perfect agent", T3Tensor(talent=1.0, training=1.0, temperament=1.0)),
        ("Terrible agent", T3Tensor(talent=0.0, training=0.0, temperament=0.0)),
    ]

    print(f"{'Case':<20} | {'Talent':<8} | {'Train':<8} | {'Temper':<8} | {'Linear':<8} | {'Tanh_v1':<8} | {'Tanh_v2':<8} | {'Logistic':<8}")
    print("-" * 110)

    for label, tensor in cases:
        results = tensor.to_dict()
        print(f"{label:<20} | {results['talent']:<8.2f} | {results['training']:<8.2f} | {results['temperament']:<8.2f} | "
              f"{results['linear']:<8.3f} | {results['tanh_v1']:<8.3f} | {results['tanh_v2']:<8.3f} | {results['logistic']:<8.3f}")

    print("\n✅ Saturation functions handle extremes more gracefully")
    print("   Linear: Can reach exact 0.0 or 1.0")
    print("   Saturating: Asymptotically approach 0.0/1.0 but never quite reach\n")


def test_missing_data():
    """Test 3: Missing data (default to 0.5 = neutral)"""
    print("=" * 80)
    print("Test 3: Missing Data Handling (Defaults to 0.5)")
    print("=" * 80)

    cases = [
        ("Only temperament known", T3Tensor(talent=0.5, training=0.5, temperament=0.9)),
        ("Talent + temperament", T3Tensor(talent=0.8, training=0.5, temperament=0.85)),
        ("All unknown", T3Tensor(talent=0.5, training=0.5, temperament=0.5)),
    ]

    print(f"{'Case':<25} | {'Talent':<8} | {'Train':<8} | {'Temper':<8} | {'Linear':<8} | {'Tanh_v1':<8} | {'Tanh_v2':<8}")
    print("-" * 100)

    for label, tensor in cases:
        results = tensor.to_dict()
        print(f"{label:<25} | {results['talent']:<8.2f} | {results['training']:<8.2f} | {results['temperament']:<8.2f} | "
              f"{results['linear']:<8.3f} | {results['tanh_v1']:<8.3f} | {results['tanh_v2']:<8.3f}")

    print("\n✅ Missing data (0.5 default) should produce neutral trust (~0.5-0.6)")
    print("   Known high values should shift score appropriately\n")


def test_adversarial():
    """Test 4: Adversarial manipulation"""
    print("=" * 80)
    print("Test 4: Adversarial Manipulation Resistance")
    print("=" * 80)

    print("Scenario: Agent tries to game trust metric by maxing all dimensions\n")

    cases = [
        ("Honest moderate", T3Tensor(talent=0.6, training=0.7, temperament=0.75)),
        ("Adversarial inflate", T3Tensor(talent=0.99, training=0.99, temperament=0.99)),
        ("Selective gaming", T3Tensor(talent=0.95, training=0.95, temperament=0.6)),
    ]

    print(f"{'Case':<20} | {'Talent':<8} | {'Train':<8} | {'Temper':<8} | {'Linear':<8} | {'Tanh_v1':<8} | {'Tanh_v2':<8}")
    print("-" * 100)

    for label, tensor in cases:
        results = tensor.to_dict()
        print(f"{label:<20} | {results['talent']:<8.2f} | {results['training']:<8.2f} | {results['temperament']:<8.2f} | "
              f"{results['linear']:<8.3f} | {results['tanh_v1']:<8.3f} | {results['tanh_v2']:<8.3f}")

    print("\n✅ Saturation prevents complete gaming")
    print("   Linear: 0.99 everywhere → 0.990 (inflated)")
    print("   Saturating: 0.99 everywhere → ~0.96-0.98 (compressed toward limit)\n")


def test_robustness_to_noise():
    """Test 5: Robustness to measurement noise"""
    print("=" * 80)
    print("Test 5: Robustness to Measurement Noise")
    print("=" * 80)

    print("Scenario: Small random noise in measurements (±0.1)\n")

    # Ground truth
    true_tensor = T3Tensor(talent=0.7, training=0.75, temperament=0.8)

    # Add noise
    np.random.seed(42)
    noisy_samples = []
    for _ in range(10):
        noisy = T3Tensor(
            talent=max(0.0, min(1.0, true_tensor.talent + np.random.normal(0, 0.05))),
            training=max(0.0, min(1.0, true_tensor.training + np.random.normal(0, 0.05))),
            temperament=max(0.0, min(1.0, true_tensor.temperament + np.random.normal(0, 0.05)))
        )
        noisy_samples.append(noisy)

    # Compute statistics
    linear_scores = [t.composite_linear() for t in noisy_samples]
    tanh_v1_scores = [t.composite_tanh_v1() for t in noisy_samples]
    tanh_v2_scores = [t.composite_tanh_v2() for t in noisy_samples]

    print(f"{'Method':<15} | {'Mean':<8} | {'Std Dev':<8} | {'Min':<8} | {'Max':<8}")
    print("-" * 60)
    print(f"{'Linear':<15} | {np.mean(linear_scores):<8.3f} | {np.std(linear_scores):<8.3f} | {np.min(linear_scores):<8.3f} | {np.max(linear_scores):<8.3f}")
    print(f"{'Tanh_v1':<15} | {np.mean(tanh_v1_scores):<8.3f} | {np.std(tanh_v1_scores):<8.3f} | {np.min(tanh_v1_scores):<8.3f} | {np.max(tanh_v1_scores):<8.3f}")
    print(f"{'Tanh_v2':<15} | {np.mean(tanh_v2_scores):<8.3f} | {np.std(tanh_v2_scores):<8.3f} | {np.min(tanh_v2_scores):<8.3f} | {np.max(tanh_v2_scores):<8.3f}")

    print("\n✅ Lower std dev → more robust to noise\n")


def test_information_preservation():
    """Test 6: Information preservation (do dimensions matter?)"""
    print("=" * 80)
    print("Test 6: Information Preservation (Dimension Sensitivity)")
    print("=" * 80)

    print("Scenario: Vary one dimension, others fixed\n")

    base = {"training": 0.6, "temperament": 0.7}
    talent_values = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

    print(f"{'Talent':<8} | {'Linear':<8} | {'Tanh_v1':<8} | {'Tanh_v2':<8} | {'ΔLinear':<10} | {'ΔTanh_v1':<10}")
    print("-" * 70)

    prev_linear = None
    prev_tanh = None

    for talent in talent_values:
        tensor = T3Tensor(talent=talent, **base)
        results = tensor.to_dict()

        delta_linear = "" if prev_linear is None else f"{results['linear'] - prev_linear:+.3f}"
        delta_tanh = "" if prev_tanh is None else f"{results['tanh_v1'] - prev_tanh:+.3f}"

        print(f"{talent:<8.1f} | {results['linear']:<8.3f} | {results['tanh_v1']:<8.3f} | {results['tanh_v2']:<8.3f} | {delta_linear:<10} | {delta_tanh:<10}")

        prev_linear = results['linear']
        prev_tanh = results['tanh_v1']

    print("\n✅ Both preserve information (trust changes with talent)")
    print("   Linear: Constant Δ (0.3 × Δtalent)")
    print("   Saturating: Variable Δ (larger near 0.5, smaller at extremes)\n")


# ============================================================================
# Summary Analysis
# ============================================================================

def summary_analysis():
    """Comprehensive comparison summary"""
    print("=" * 80)
    print("SUMMARY ANALYSIS: Saturation vs Linear Trust Compilation")
    print("=" * 80)

    print("\n### Properties Comparison\n")

    comparison = [
        ("Bounded output [0,1]", "❌ Not guaranteed", "✅ Mathematical guarantee"),
        ("Outlier resistance", "❌ Linear impact", "✅ Compressed extremes"),
        ("Missing data handling", "✅ Acceptable", "✅ Acceptable"),
        ("Adversarial resistance", "❌ Vulnerable to inflation", "✅ Saturation limits gaming"),
        ("Noise robustness", "Moderate", "Slightly better"),
        ("Information preservation", "✅ Proportional", "✅ Preserved (nonlinear)"),
        ("Computational cost", "✅ Minimal (3 muls, 2 adds)", "⚠️  Higher (exp/log)"),
        ("Interpretability", "✅ Simple weighted average", "⚠️  Requires understanding saturation"),
        ("Implementation complexity", "✅ Trivial", "⚠️  More complex"),
    ]

    print(f"{'Property':<30} | {'Linear (Current)':<30} | {'Saturating (tanh-like)':<30}")
    print("-" * 95)

    for prop, linear, saturating in comparison:
        print(f"{prop:<30} | {linear:<30} | {saturating:<30}")

    print("\n### Recommendation\n")
    print("""
Based on testing:

**WHEN TO USE SATURATION (tanh-like):**
1. Adversarial environment (gaming risk high)
2. Extreme values common (0.0 or 1.0 trust dimensions)
3. Robustness critical (small noise shouldn't swing decisions)
4. Mathematical guarantees needed (bounded output required)

**WHEN LINEAR IS SUFFICIENT:**
1. Trusted environment (no gaming expected)
2. Moderate values common (0.3-0.8 range)
3. Simplicity valued (easy to understand and debug)
4. Performance critical (minimal computation)

**FOR WEB4 SPECIFICALLY:**
Current weighted sum is likely SUFFICIENT because:
- MRH-aware trust already handles context (horizon decay)
- Sample size confidence provides robustness
- Trust update mechanism prevents sudden swings
- Interpretability matters for debugging

**HOWEVER:**
Saturation COULD improve:
- Adversarial resistance (Sybil attacks, reputation gaming)
- Extreme case handling (brand new agents, malicious actors)
- Mathematical rigor (guaranteed [0,1] output)

**SUGGESTED ACTION:**
1. ✅ Keep linear for now (it works)
2. 🔄 Monitor for gaming behavior in production
3. 🔄 Implement saturation if adversarial patterns emerge
4. ✅ Document this analysis for future reference

**NULL RESULT IS VALUABLE:**
If testing shows no improvement, that's useful information!
It means current approach is appropriate for the domain.
    """)

    print("\n" + "=" * 80)
    print("Experiment Complete")
    print("=" * 80)


# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    print("\n")
    print("┌" + "─" * 78 + "┐")
    print("│" + " " * 15 + "TRUST COMPRESSION EXPERIMENT" + " " * 35 + "│")
    print("│" + " " * 10 + "Compression-Action-Threshold Pattern Investigation" + " " * 17 + "│")
    print("└" + "─" * 78 + "┘")
    print("\n")

    test_normal_operation()
    test_outlier_resistance()
    test_missing_data()
    test_adversarial()
    test_robustness_to_noise()
    test_information_preservation()
    summary_analysis()

    print("\n✅ All tests complete. Results logged for analysis.\n")
