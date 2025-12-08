"""
Pattern Interaction Trust Model for Web4
========================================

Extends Web4 trust system with Synchronism's pattern interaction framework.

Synchronism defines 3 interaction types:
1. RESONANT (C → 1): Strong coupling, information exchange, "matter interacts with matter"
2. INDIFFERENT (C → 0): Weak coupling, acknowledge presence but don't engage
3. DISSONANT: Active opposition, destructive interference

This implementation maps these to Web4 trust relationships using a coherence
function C(ρ) analog where ρ represents "trust density" (accumulated trust evidence).

Key Insight from Synchronism Session 96:
The coherence function C(ρ) = tanh(γ × log(ρ/ρ_crit + 1)) measures the
transition from indifferent to resonant pattern interaction.

Applied to Web4:
- Low trust density (few interactions): INDIFFERENT regime
- High trust density (many interactions): RESONANT regime
- Negative trust: DISSONANT regime
- Smooth transition via tanh function

Author: Legion Autonomous Web4 Research
Date: 2025-12-07
Track: 27 (Pattern Interaction Trust)
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Dict
import math


class InteractionType(Enum):
    """Pattern interaction types from Synchronism"""
    RESONANT = "RESONANT"       # Strong coupling, C → 1
    INDIFFERENT = "INDIFFERENT" # Weak coupling, C → 0
    DISSONANT = "DISSONANT"     # Active opposition, C < 0


@dataclass
class TrustEvidence:
    """Single piece of trust evidence"""
    timestamp: float        # When interaction occurred
    outcome_quality: float  # -1 to +1 (negative = bad, positive = good)
    interaction_weight: float # How significant was this interaction


@dataclass
class TrustDensity:
    """Trust density calculation (analog to Synchronism's ρ)"""
    total_interactions: int       # Number of interactions
    positive_outcomes: int        # Successful interactions
    negative_outcomes: int        # Failed interactions
    total_weight: float          # Sum of interaction weights
    time_span_days: float        # Time period over which interactions occurred

    @property
    def density_rho(self) -> float:
        """
        Calculate trust density (ρ)

        Analog to Synchronism's matter density:
        - More interactions over shorter time = higher density
        - Weighted by interaction significance
        """
        if self.time_span_days <= 0:
            return 0.0

        # Density = weighted interactions / time
        return self.total_weight / self.time_span_days

    @property
    def net_sentiment(self) -> float:
        """
        Net sentiment from interactions

        +1.0: All positive
         0.0: Equal positive/negative
        -1.0: All negative
        """
        total = self.positive_outcomes + self.negative_outcomes
        if total == 0:
            return 0.0

        return (self.positive_outcomes - self.negative_outcomes) / total


class PatternInteractionTrust:
    """
    Web4 trust model based on Synchronism pattern interactions

    Uses coherence function C(ρ) = tanh(γ × log(ρ/ρ_crit + 1))
    to determine interaction regime
    """

    def __init__(self, gamma: float = 1.0, rho_critical: float = 1.0):
        """
        Initialize pattern interaction trust model

        Args:
            gamma: Transition steepness (higher = sharper transition)
            rho_critical: Density threshold for resonance
        """
        self.gamma = gamma
        self.rho_critical = rho_critical

    def coherence_function(self, rho: float) -> float:
        """
        Calculate coherence C(ρ) from trust density

        C(ρ) = tanh(γ × log(ρ/ρ_crit + 1))

        Maps trust density to interaction strength:
        - ρ → 0: C → 0 (indifferent)
        - ρ → ∞: C → 1 (resonant)
        - Smooth transition via tanh

        Returns: C ∈ [0, 1]
        """
        if rho <= 0:
            return 0.0

        # Normalize by critical density
        normalized_rho = rho / self.rho_critical

        # Log transformation (information-theoretic accumulation)
        log_term = math.log(normalized_rho + 1)

        # Apply gamma (transition steepness)
        scaled = self.gamma * log_term

        # Tanh bounds output to [0, 1] and creates smooth transition
        return math.tanh(scaled)

    def classify_interaction(
        self,
        density: TrustDensity
    ) -> Tuple[InteractionType, float, str]:
        """
        Classify interaction type from trust density

        Returns:
            (interaction_type, coherence_value, explanation)
        """
        # Calculate trust density
        rho = density.density_rho

        # Calculate coherence
        C = self.coherence_function(rho)

        # Get sentiment (positive/negative)
        sentiment = density.net_sentiment

        # Classification logic
        if sentiment < -0.3:
            # Negative sentiment = DISSONANT
            return (
                InteractionType.DISSONANT,
                -C,  # Negative coherence for dissonance
                f"Negative interactions (sentiment {sentiment:.2f}) indicate active opposition"
            )
        elif C < 0.3:
            # Low coherence = INDIFFERENT
            return (
                InteractionType.INDIFFERENT,
                C,
                f"Low trust density (ρ={rho:.2f}) creates weak coupling (C={C:.2f})"
            )
        else:
            # High coherence = RESONANT
            return (
                InteractionType.RESONANT,
                C,
                f"High trust density (ρ={rho:.2f}) creates strong coupling (C={C:.2f})"
            )

    def effective_trust_multiplier(self, coherence: float, interaction_type: InteractionType) -> float:
        """
        Calculate effective trust multiplier from coherence

        RESONANT (C → 1): Full trust multiplier
        INDIFFERENT (C → 0): Reduced trust multiplier
        DISSONANT (C < 0): Negative trust multiplier
        """
        if interaction_type == InteractionType.RESONANT:
            return coherence  # Full coupling
        elif interaction_type == InteractionType.INDIFFERENT:
            return coherence * 0.5  # Weak coupling
        else:  # DISSONANT
            return coherence  # Negative coupling (coherence is negative)


def demonstrate_pattern_interaction_trust():
    """Demonstrate pattern interaction trust model"""

    print("=" * 70)
    print("  Track 27: Pattern Interaction Trust Model")
    print("  Web4 Trust Through Synchronism Pattern Interactions")
    print("=" * 70)

    print("\nSynchronism Foundation:")
    print("  C(ρ) = tanh(γ × log(ρ/ρ_crit + 1))")
    print("  Measures transition from INDIFFERENT → RESONANT interaction")
    print()

    model = PatternInteractionTrust(gamma=1.5, rho_critical=10.0)

    # Test scenarios
    scenarios = [
        ("New acquaintance", TrustDensity(
            total_interactions=3,
            positive_outcomes=2,
            negative_outcomes=1,
            total_weight=3.0,
            time_span_days=30.0
        )),
        ("Established partner", TrustDensity(
            total_interactions=150,
            positive_outcomes=140,
            negative_outcomes=10,
            total_weight=300.0,
            time_span_days=90.0
        )),
        ("Long-term collaborator", TrustDensity(
            total_interactions=1000,
            positive_outcomes=950,
            negative_outcomes=50,
            total_weight=2500.0,
            time_span_days=365.0
        )),
        ("Adversarial entity", TrustDensity(
            total_interactions=50,
            positive_outcomes=10,
            negative_outcomes=40,
            total_weight=75.0,
            time_span_days=60.0
        )),
        ("Sparse interactions", TrustDensity(
            total_interactions=5,
            positive_outcomes=4,
            negative_outcomes=1,
            total_weight=5.0,
            time_span_days=180.0
        ))
    ]

    print("=" * 70)
    print("  SCENARIO ANALYSIS")
    print("=" * 70)

    for name, density in scenarios:
        print(f"\n[{name}]")
        print(f"  Interactions: {density.total_interactions} over {density.time_span_days:.0f} days")
        print(f"  Outcomes: {density.positive_outcomes} positive, {density.negative_outcomes} negative")
        print(f"  Trust density (ρ): {density.density_rho:.3f}")
        print(f"  Net sentiment: {density.net_sentiment:.3f}")

        interaction_type, coherence, explanation = model.classify_interaction(density)
        multiplier = model.effective_trust_multiplier(coherence, interaction_type)

        print(f"  → Interaction type: {interaction_type.value}")
        print(f"  → Coherence C(ρ): {coherence:.3f}")
        print(f"  → Trust multiplier: {multiplier:.3f}")
        print(f"  → {explanation}")

    # Demonstrate transition curve
    print("\n" + "=" * 70)
    print("  COHERENCE TRANSITION CURVE")
    print("=" * 70)
    print("\nTrust Density (ρ) → Coherence C(ρ) Transition:")
    print("-" * 70)

    test_densities = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0]
    print(f"{'ρ':<10} {'C(ρ)':<10} {'Regime':<15} {'Visual':<30}")
    print("-" * 70)

    for rho in test_densities:
        C = model.coherence_function(rho)

        if C < 0.3:
            regime = "INDIFFERENT"
        elif C < 0.7:
            regime = "TRANSITIONAL"
        else:
            regime = "RESONANT"

        # Visual representation
        bar_length = int(C * 30)
        visual = "█" * bar_length + "░" * (30 - bar_length)

        print(f"{rho:<10.1f} {C:<10.3f} {regime:<15} {visual}")

    # Compare to traditional scalar trust
    print("\n" + "=" * 70)
    print("  COMPARISON: Pattern Interaction vs Scalar Trust")
    print("=" * 70)

    print("\nScenario: Long-term collaborator")
    print("-" * 70)
    density = scenarios[2][1]  # Long-term collaborator

    print("\nTraditional Scalar Trust:")
    print(f"  Trust score: {density.positive_outcomes / density.total_interactions:.3f}")
    print(f"  Limitation: Doesn't capture interaction quality or density")
    print(f"  Same score whether 10/10 or 950/1000 positive")

    print("\nPattern Interaction Trust:")
    interaction_type, coherence, explanation = model.classify_interaction(density)
    print(f"  Interaction type: {interaction_type.value}")
    print(f"  Coherence: {coherence:.3f}")
    print(f"  Captures: Interaction density, history depth, coupling strength")
    print(f"  Insight: {explanation}")

    print("\n" + "=" * 70)
    print("  SYNCHRONISM INTEGRATION")
    print("=" * 70)

    print("\nKey Mappings:")
    print("  Synchronism ρ (matter density) → Web4 trust density")
    print("  Synchronism C(ρ) (coherence) → Web4 interaction strength")
    print("  RESONANT regime → Strong trust coupling (full collaboration)")
    print("  INDIFFERENT regime → Weak trust coupling (acknowledge but careful)")
    print("  DISSONANT regime → Negative coupling (adversarial)")

    print("\nArchitectural Benefits:")
    print("  1. Richer trust model beyond scalar scores")
    print("  2. Smooth transitions between interaction regimes")
    print("  3. Grounded in Synchronism theoretical foundation")
    print("  4. Captures trust density and quality, not just magnitude")
    print("  5. Natural handling of sparse vs dense interaction histories")

    print("\nProduction Use Cases:")
    print("  • New agent onboarding (INDIFFERENT → RESONANT transition)")
    print("  • Adversarial detection (DISSONANT regime identification)")
    print("  • Trust decay over time (density decreases without interactions)")
    print("  • Coalition formation (identify RESONANT relationships)")
    print("  • Resource allocation (prioritize RESONANT partners)")

    print()


if __name__ == "__main__":
    demonstrate_pattern_interaction_trust()
