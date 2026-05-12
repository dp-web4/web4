#!/usr/bin/env python3
"""
ATP Pricing Based on Coherence Trust Framework

Implements resource allocation (ATP pricing) using physics-validated
coherence metrics from Session #25 trust tensor.

THEORETICAL BASIS:
- High coherence (low γ, quantum regime) → trusted → lower ATP cost
- Low coherence (high γ, classical regime) → untrusted → higher ATP cost
- Coalition members (C > 0.5) → preferential pricing
- Entropy S/S₀ = γ/2 → predictability discount

DESIGN PRINCIPLES:
- Physics-derived (not empirically fitted)
- Incentivizes coherent behavior
- Penalizes decoherent/volatile agents
- Coalition members cooperate more efficiently

Created: 2026-01-15
Session: 26 (Legion autonomous research)
"""

from dataclasses import dataclass
from typing import Dict, Optional
from coherence_trust_tensor import (
    CoherenceTrustMetrics,
    gamma_from_network_structure,
    GAMMA_CLASSICAL,
    GAMMA_QUANTUM,
    C_THRESHOLD
)


@dataclass
class ATPPricingPolicy:
    """
    ATP pricing policy parameters

    Controls how coherence metrics map to ATP costs
    """
    # Base pricing
    base_cost: float = 1.0  # Base ATP cost for neutral action

    # Coherence discounts/premiums
    quantum_discount: float = 0.5  # Max discount for γ=1.0 (50% off)
    classical_premium: float = 0.5  # Max premium for γ=2.0 (50% more)

    # Coalition benefits
    coalition_discount: float = 0.2  # Additional 20% off for coalition members

    # Entropy predictability bonus
    entropy_discount_weight: float = 0.1  # Up to 10% off for low entropy

    # Trust minimum threshold
    min_trust_for_discount: float = 0.3  # Below this, no discounts applied

    def __post_init__(self):
        """Validate policy parameters"""
        assert 0.0 <= self.quantum_discount <= 1.0, "Discount must be in [0,1]"
        assert 0.0 <= self.classical_premium <= 2.0, "Premium must be in [0,2]"
        assert 0.0 <= self.coalition_discount <= 1.0, "Coalition discount in [0,1]"
        assert 0.0 <= self.entropy_discount_weight <= 1.0, "Entropy weight in [0,1]"


class CoherenceATPPricing:
    """
    ATP pricing engine using coherence trust metrics

    Maps trust coherence to ATP resource costs
    """

    def __init__(self, policy: Optional[ATPPricingPolicy] = None):
        self.policy = policy or ATPPricingPolicy()

    def compute_gamma_multiplier(self, gamma: float) -> float:
        """
        Compute ATP cost multiplier from γ

        γ = 1.0 (quantum, high coherence) → 0.5x cost (50% discount)
        γ = 1.5 (transition) → 1.0x cost (neutral)
        γ = 2.0 (classical, low coherence) → 1.5x cost (50% premium)

        Formula: multiplier = 1.0 + (γ - 1.5) × sensitivity

        Where sensitivity chosen to give desired discounts/premiums
        """
        # Normalized γ position in [1.0, 2.0] range
        gamma_norm = (gamma - GAMMA_QUANTUM) / (GAMMA_CLASSICAL - GAMMA_QUANTUM)
        gamma_norm = max(0.0, min(1.0, gamma_norm))  # Clamp to [0,1]

        # Map to discount/premium
        # γ=1.0 (norm=0.0) → discount
        # γ=2.0 (norm=1.0) → premium

        if gamma_norm < 0.5:  # Quantum regime (γ < 1.5)
            # Linear interpolation from max discount to neutral
            discount_factor = 1.0 - self.policy.quantum_discount * (0.5 - gamma_norm) / 0.5
            return discount_factor
        else:  # Classical regime (γ ≥ 1.5)
            # Linear interpolation from neutral to max premium
            premium_factor = 1.0 + self.policy.classical_premium * (gamma_norm - 0.5) / 0.5
            return premium_factor

    def compute_coalition_discount(self, above_threshold: bool) -> float:
        """
        Coalition membership discount

        C > 0.5 → coalition member → discount applied
        C ≤ 0.5 → not in coalition → no discount
        """
        if above_threshold:
            return 1.0 - self.policy.coalition_discount
        else:
            return 1.0  # No discount

    def compute_entropy_discount(self, entropy_ratio: float) -> float:
        """
        Entropy-based predictability discount

        Low entropy (S/S₀ → 0.5) → predictable → discount
        High entropy (S/S₀ → 1.0) → unpredictable → no discount

        Formula: discount = 1.0 - weight × (1.0 - S/S₀)
        """
        # Normalize entropy to [0,1] where 0 = most predictable
        # S/S₀ ∈ [0.5, 1.0] → map to [0, 1]
        entropy_norm = (entropy_ratio - 0.5) / 0.5
        entropy_norm = max(0.0, min(1.0, entropy_norm))

        # Discount = weight × (1 - entropy_norm)
        # High entropy (norm=1) → no discount
        # Low entropy (norm=0) → max discount
        discount_factor = 1.0 - self.policy.entropy_discount_weight * (1.0 - entropy_norm)

        return discount_factor

    def compute_atp_cost(
        self,
        base_cost: float,
        trust_metrics: CoherenceTrustMetrics
    ) -> Dict[str, float]:
        """
        Compute ATP cost for action based on trust coherence

        Args:
            base_cost: Base ATP cost for action (without trust adjustment)
            trust_metrics: Coherence trust metrics for agent/relationship

        Returns:
            Dictionary with cost breakdown:
            - base: Base cost
            - gamma_multiplier: Multiplier from γ (coherence regime)
            - coalition_discount: Discount if coalition member
            - entropy_discount: Discount for predictability
            - final_cost: Total ATP cost after all adjustments
        """
        # Check minimum trust threshold
        if trust_metrics.trust_value < self.policy.min_trust_for_discount:
            # Below minimum trust → no discounts, only base cost
            return {
                "base": base_cost,
                "gamma_multiplier": 1.0,
                "coalition_discount": 1.0,
                "entropy_discount": 1.0,
                "final_cost": base_cost,
                "reason": "below_minimum_trust"
            }

        # Compute multipliers
        gamma_mult = self.compute_gamma_multiplier(trust_metrics.gamma)
        coalition_mult = self.compute_coalition_discount(trust_metrics.above_coalition_threshold)
        entropy_mult = self.compute_entropy_discount(trust_metrics.entropy_ratio)

        # Apply multipliers
        cost_after_gamma = base_cost * gamma_mult
        cost_after_coalition = cost_after_gamma * coalition_mult
        final_cost = cost_after_coalition * entropy_mult

        return {
            "base": base_cost,
            "gamma_multiplier": gamma_mult,
            "coalition_discount": coalition_mult,
            "entropy_discount": entropy_mult,
            "final_cost": final_cost,
            "savings": base_cost - final_cost,
            "savings_pct": 100 * (base_cost - final_cost) / base_cost
        }

    def explain_pricing(
        self,
        base_cost: float,
        trust_metrics: CoherenceTrustMetrics
    ) -> str:
        """
        Human-readable explanation of ATP pricing

        Args:
            base_cost: Base ATP cost
            trust_metrics: Trust metrics

        Returns:
            Formatted explanation string
        """
        cost = self.compute_atp_cost(base_cost, trust_metrics)

        lines = []
        lines.append(f"ATP Pricing Analysis")
        lines.append(f"{'='*50}")
        lines.append(f"Base cost: {cost['base']:.2f} ATP")
        lines.append(f"")

        if "reason" in cost and cost["reason"] == "below_minimum_trust":
            lines.append(f"⚠️  Trust too low ({trust_metrics.trust_value:.3f} < {self.policy.min_trust_for_discount})")
            lines.append(f"   No discounts applied")
            lines.append(f"")
            lines.append(f"Final cost: {cost['final_cost']:.2f} ATP")
            return "\n".join(lines)

        # Gamma (coherence regime)
        regime = "quantum" if trust_metrics.is_quantum_regime else "classical"
        gamma_effect = "discount" if cost['gamma_multiplier'] < 1.0 else "premium"
        lines.append(f"Coherence regime: {regime} (γ={trust_metrics.gamma:.3f})")
        lines.append(f"  → {gamma_effect}: {cost['gamma_multiplier']:.2f}x")

        # Coalition
        if trust_metrics.above_coalition_threshold:
            lines.append(f"Coalition member (C={trust_metrics.coherence:.3f} > 0.5)")
            lines.append(f"  → discount: {cost['coalition_discount']:.2f}x ({(1-cost['coalition_discount'])*100:.0f}% off)")
        else:
            lines.append(f"Not in coalition (C={trust_metrics.coherence:.3f} < 0.5)")
            lines.append(f"  → no coalition discount")

        # Entropy
        entropy_discount_pct = (1 - cost['entropy_discount']) * 100
        lines.append(f"Entropy: S/S₀={trust_metrics.entropy_ratio:.3f}")
        lines.append(f"  → predictability discount: {cost['entropy_discount']:.2f}x ({entropy_discount_pct:.1f}% off)")

        lines.append(f"")
        lines.append(f"Final cost: {cost['final_cost']:.2f} ATP")
        if cost['savings'] > 0:
            lines.append(f"Savings: {cost['savings']:.2f} ATP ({cost['savings_pct']:.1f}% off)")
        elif cost['savings'] < 0:
            lines.append(f"Premium: {-cost['savings']:.2f} ATP ({-cost['savings_pct']:.1f}% more)")

        return "\n".join(lines)


# ============================================================================
# Example Usage and Testing
# ============================================================================

def example_usage():
    """Demonstrate ATP pricing for different trust scenarios"""
    print("="*70)
    print("ATP COHERENCE PRICING EXAMPLES")
    print("="*70)
    print()

    pricing = CoherenceATPPricing()

    # Scenario 1: High-trust cooperator (quantum regime)
    print("Scenario 1: High-Trust Cooperator")
    print("-"*70)
    metrics_cooperator = CoherenceTrustMetrics(
        trust_value=0.85,
        trust_variance=0.01,
        network_density=0.9,
        num_agents=7,
        num_strong_edges=15
    )
    print(pricing.explain_pricing(100.0, metrics_cooperator))
    print()

    # Scenario 2: Coalition member
    print("Scenario 2: Coalition Member")
    print("-"*70)
    metrics_coalition = CoherenceTrustMetrics(
        trust_value=0.65,
        trust_variance=0.02,
        network_density=0.85,
        num_agents=7,
        num_strong_edges=12
    )
    print(pricing.explain_pricing(100.0, metrics_coalition))
    print()

    # Scenario 3: Low-trust opportunist (classical regime)
    print("Scenario 3: Low-Trust Opportunist")
    print("-"*70)
    metrics_opportunist = CoherenceTrustMetrics(
        trust_value=0.35,
        trust_variance=0.15,
        network_density=0.5,
        num_agents=7,
        num_strong_edges=2
    )
    print(pricing.explain_pricing(100.0, metrics_opportunist))
    print()

    # Scenario 4: Below minimum trust
    print("Scenario 4: Below Minimum Trust")
    print("-"*70)
    metrics_untrusted = CoherenceTrustMetrics(
        trust_value=0.15,
        trust_variance=0.20,
        network_density=0.3,
        num_agents=7,
        num_strong_edges=0
    )
    print(pricing.explain_pricing(100.0, metrics_untrusted))
    print()


def compare_policies():
    """Compare different ATP pricing policies"""
    print("="*70)
    print("POLICY COMPARISON")
    print("="*70)
    print()

    # Standard policy
    standard = ATPPricingPolicy()

    # Aggressive discounts (incentivize cooperation)
    aggressive = ATPPricingPolicy(
        quantum_discount=0.7,  # 70% off for quantum
        classical_premium=1.0,  # 100% premium for classical
        coalition_discount=0.3  # 30% off for coalitions
    )

    # Conservative (minimal intervention)
    conservative = ATPPricingPolicy(
        quantum_discount=0.2,  # 20% off
        classical_premium=0.2,  # 20% premium
        coalition_discount=0.1  # 10% off
    )

    # Test metrics
    metrics = CoherenceTrustMetrics(
        trust_value=0.75,
        trust_variance=0.03,
        network_density=0.8,
        num_agents=7,
        num_strong_edges=10
    )

    base_cost = 100.0

    policies = {
        "Standard": standard,
        "Aggressive": aggressive,
        "Conservative": conservative
    }

    for name, policy in policies.items():
        pricer = CoherenceATPPricing(policy)
        cost = pricer.compute_atp_cost(base_cost, metrics)
        print(f"{name:15} → {cost['final_cost']:6.2f} ATP ({cost['savings_pct']:+5.1f}%)")

    print()


if __name__ == "__main__":
    example_usage()
    compare_policies()

    print("="*70)
    print("✅ ATP coherence pricing ready for Web4 integration")
    print("="*70)
