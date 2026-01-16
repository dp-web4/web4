#!/usr/bin/env python3
"""
Coherence ATP Pricing V2: Inverted Model (Subsidy for Trust-Building)
Session #28: Fix death spiral discovered in V1

Problem with V1:
- Low trust → High γ → ATP premium → Can't cooperate → Death spiral
- Expected to incentivize cooperation, actually prevents it
- Classical regime (γ>1.5) was paying 15-40% premium

V2 Solution: Inverted Pricing Model
- Low trust networks get ATP *discount* (subsidy to bootstrap cooperation)
- High trust networks pay *premium* (they're successful, can afford it)
- Rationale: Economic support for trust-building, not punishment

New Formula:
  Quantum regime (γ<1.5, high coherence):  Premium (mature networks pay more)
  Classical regime (γ≥1.5, low coherence): Discount (support trust-building)

This inverts the V1 logic but preserves same physics foundation.

Author: Legion (autonomous Session #28)
"""

from dataclasses import dataclass
from typing import Optional
import sys
from pathlib import Path

# Import from V1
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "web4-standard" / "implementation" / "trust"))
from coherence_trust_tensor import CoherenceTrustMetrics


@dataclass
class InvertedCoherencePricingPolicy:
    """
    Inverted pricing policy: Subsidy for low-trust, premium for high-trust

    Rationale:
    - New/low-trust networks need economic support to bootstrap cooperation
    - Mature/high-trust networks are successful and can afford premium
    - Prevents death spiral in formation phase
    """
    # Quantum regime (high coherence, mature networks)
    quantum_premium: float = 0.3       # 30% premium for quantum (they can afford it)

    # Classical regime (low coherence, forming networks)
    classical_discount: float = 0.3    # 30% discount for classical (subsidy)

    # Coalition pricing (unchanged)
    coalition_discount: float = 0.2    # 20% additional discount for C>0.5

    # Entropy pricing (unchanged)
    entropy_discount_max: float = 0.1  # 10% discount for predictability

    # Thresholds
    min_trust_for_discount: float = 0.3
    coalition_threshold: float = 0.5


class InvertedCoherencePricingLayer:
    """
    Inverted coherence pricing: Support trust-building, tax success

    Key Change from V1:
    - Quantum regime (γ<1.5): PREMIUM (was discount) - successful networks
    - Classical regime (γ≥1.5): DISCOUNT (was premium) - struggling networks

    Coalition and entropy pricing unchanged (still discounts).
    """

    def __init__(self, policy: Optional[InvertedCoherencePricingPolicy] = None):
        self.policy = policy or InvertedCoherencePricingPolicy()

    def compute_gamma_multiplier(self, gamma: float) -> float:
        """
        INVERTED gamma multiplier: Discount for classical, premium for quantum

        γ ∈ [1.0, 2.0] → multiplier ∈ [0.7, 1.3]

        Classical regime (γ ≥ 1.5): DISCOUNT (forming networks need support)
          mult = 1.0 - classical_discount × (γ - 1.5) / 0.5

        Quantum regime (γ < 1.5): PREMIUM (mature networks can afford it)
          mult = 1.0 + quantum_premium × (1.5 - γ) / 0.5

        Args:
            gamma: Correlation exponent from power-law C(T) ~ T^(-γ)

        Returns:
            Multiplicative factor ∈ [0.7, 1.3]
        """
        # Clamp γ to [1.0, 2.0]
        gamma_clamped = max(1.0, min(2.0, gamma))

        # Normalize to [0, 1] where 0=quantum, 1=classical
        gamma_norm = (gamma_clamped - 1.0) / 1.0

        if gamma_norm >= 0.5:  # Classical regime (γ ≥ 1.5) - DISCOUNT
            # More classical → stronger discount
            classical_strength = (gamma_norm - 0.5) / 0.5  # [0, 1]
            return 1.0 - (self.policy.classical_discount * classical_strength)
        else:  # Quantum regime (γ < 1.5) - PREMIUM
            # More quantum → stronger premium
            quantum_strength = (0.5 - gamma_norm) / 0.5  # [0, 1]
            return 1.0 + (self.policy.quantum_premium * quantum_strength)

    def compute_coalition_multiplier(self, coherence: float, trust_value: float) -> float:
        """Coalition discount (unchanged from V1)"""
        if trust_value < self.policy.min_trust_for_discount:
            return 1.0

        if coherence >= self.policy.coalition_threshold:
            excess = coherence - self.policy.coalition_threshold
            discount_strength = min(1.0, excess / 0.3)
            return 1.0 - (self.policy.coalition_discount * discount_strength)

        return 1.0

    def compute_entropy_multiplier(self, entropy_ratio: float) -> float:
        """Entropy discount (unchanged from V1)"""
        entropy_clamped = max(0.0, min(1.0, entropy_ratio))
        discount_strength = 1.0 - entropy_clamped
        return 1.0 - (self.policy.entropy_discount_max * discount_strength)

    def compute_coherence_multiplier(self, trust_metrics: CoherenceTrustMetrics) -> float:
        """
        Compute full inverted coherence multiplier

        Combines inverted gamma (discount for classical) with standard
        coalition and entropy discounts.
        """
        gamma_mult = self.compute_gamma_multiplier(trust_metrics.gamma)
        coalition_mult = self.compute_coalition_multiplier(
            trust_metrics.coherence,
            trust_metrics.trust_value
        )
        entropy_mult = self.compute_entropy_multiplier(trust_metrics.entropy_ratio)

        return gamma_mult * coalition_mult * entropy_mult

    def get_multiplier_breakdown(self, trust_metrics: CoherenceTrustMetrics) -> dict:
        """Get detailed breakdown of pricing components"""
        gamma_mult = self.compute_gamma_multiplier(trust_metrics.gamma)
        coalition_mult = self.compute_coalition_multiplier(
            trust_metrics.coherence,
            trust_metrics.trust_value
        )
        entropy_mult = self.compute_entropy_multiplier(trust_metrics.entropy_ratio)
        total_mult = gamma_mult * coalition_mult * entropy_mult

        return {
            "gamma_multiplier": gamma_mult,
            "coalition_multiplier": coalition_mult,
            "entropy_multiplier": entropy_mult,
            "total_multiplier": total_mult,
            "discount_percentage": (1.0 - total_mult) * 100,
            "regime": "quantum" if trust_metrics.is_quantum_regime else "classical",
            "above_coalition_threshold": trust_metrics.above_coalition_threshold,
            "inverted": True  # Mark as inverted model
        }


class InvertedCoherenceIntegratedPricer:
    """Inverted coherence pricing: Subsidy model for trust-building"""

    def __init__(self, policy: Optional[InvertedCoherencePricingPolicy] = None):
        self.coherence_layer = InvertedCoherencePricingLayer(policy)

    def price_with_coherence(
        self,
        base_cost: float,
        trust_metrics: CoherenceTrustMetrics
    ) -> dict:
        """
        Calculate ATP cost with inverted coherence adjustment

        Args:
            base_cost: Base ATP cost for action
            trust_metrics: CoherenceTrustMetrics for network

        Returns:
            Dict with final_cost, coherence_multiplier, and breakdown
        """
        coherence_mult = self.coherence_layer.compute_coherence_multiplier(trust_metrics)
        final_cost = base_cost * coherence_mult

        coherence_breakdown = self.coherence_layer.get_multiplier_breakdown(trust_metrics)

        return {
            "base_cost": base_cost,
            "coherence_multiplier": coherence_mult,
            "final_cost": final_cost,
            "discount_atp": base_cost - final_cost,
            "discount_percentage": coherence_breakdown["discount_percentage"],
            "breakdown": coherence_breakdown,
            "trust_metrics": {
                "gamma": trust_metrics.gamma,
                "coherence": trust_metrics.coherence,
                "entropy_ratio": trust_metrics.entropy_ratio,
                "trust_value": trust_metrics.trust_value,
                "regime": "quantum" if trust_metrics.is_quantum_regime else "classical"
            }
        }


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("  INVERTED COHERENCE PRICING - Unit Tests")
    print("  V2: Subsidy Model for Trust-Building")
    print("=" * 80)

    layer = InvertedCoherencePricingLayer()

    # Test gamma multipliers
    print("\n=== Inverted Gamma Multipliers ===\n")
    test_gammas = [1.0, 1.25, 1.5, 1.75, 2.0]

    print("γ     | Regime     | V1 Effect      | V2 Effect (Inverted)")
    print("-" * 65)

    for gamma in test_gammas:
        mult = layer.compute_gamma_multiplier(gamma)
        regime = "quantum" if gamma < 1.5 else "classical"
        v1_effect = "discount" if gamma < 1.5 else "premium"
        v2_effect = "premium" if gamma < 1.5 else "discount"

        print(f"{gamma:.2f}  | {regime:<10} | {v1_effect:<14} | {v2_effect:<10} ({mult:.3f}×)")

    # Test scenario comparison
    print("\n=== Scenario Comparison: V1 vs V2 ===\n")

    scenarios = [
        {
            "name": "Low-Trust Network (typical start)",
            "trust": 0.3,
            "variance": 0.06,
            "density": 0.5,
            "agents": 7,
            "strong_edges": 2
        },
        {
            "name": "High-Trust Network (mature)",
            "trust": 0.7,
            "variance": 0.02,
            "density": 0.9,
            "agents": 7,
            "strong_edges": 10
        }
    ]

    pricer_v2 = InvertedCoherenceIntegratedPricer()

    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        print(f"  Trust={scenario['trust']}, Variance={scenario['variance']}, Density={scenario['density']}")

        metrics = CoherenceTrustMetrics(
            trust_value=scenario["trust"],
            trust_variance=scenario["variance"],
            network_density=scenario["density"],
            num_agents=scenario["agents"],
            num_strong_edges=scenario["strong_edges"]
        )

        regime = "quantum" if metrics.is_quantum_regime else "classical"
        print(f"  γ={metrics.gamma:.3f} ({regime}), C={metrics.coherence:.3f}")

        # V2 pricing
        result_v2 = pricer_v2.price_with_coherence(base_cost=10.0, trust_metrics=metrics)

        print(f"\n  V2 (Inverted) Pricing:")
        print(f"    Help action: 10.00 ATP → {result_v2['final_cost']:.2f} ATP")
        print(f"    Effect: {result_v2['discount_percentage']:+.1f}% ({'discount' if result_v2['discount_percentage'] > 0 else 'premium'})")

    print("\n" + "=" * 80)
    print("  KEY INSIGHT: Inverted Model")
    print("=" * 80)
    print("\n  V1 (Original): Low trust pays premium → death spiral")
    print("  V2 (Inverted): Low trust gets discount → bootstrap cooperation")
    print("\n  This should fix the cooperation decrease problem!")
