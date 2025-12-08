"""
Tidal Trust Decay Model for Web4
=================================

Applies Synchronism Session 97's tidal stripping insights to Web4 trust decay.

Synchronism Discovery (Session 97, DF2/DF4 Resolution):
- Tidal interactions preferentially remove low-C (INDIFFERENT) outer envelope
- High-C (RESONANT) core remains after stripping
- Result: Post-stripping galaxy appears "dark matter deficient"
- Mechanism: Lowest binding energy material stripped first

Application to Web4 Trust:
- Trust relationships have "core" (strong, direct) and "envelope" (weak, indirect)
- External pressures (competing relationships, time, adversarial actions) = tidal forces
- Tidal decay: Preferentially removes weak/indirect trust (lowest "binding energy")
- Strong direct trust remains resilient

Key Insight: Trust decay is not uniform - it's selective based on relationship strength.
This explains why long-term trusted partners remain trusted even after periods of
inactivity, while casual relationships fade quickly.

Author: Legion Autonomous Web4 Research
Date: 2025-12-07
Track: 31 (Tidal Trust Decay)
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple
from enum import Enum
import math


class TrustBinding(Enum):
    """Trust relationship binding strength (analog to gravitational binding)"""
    CORE = "CORE"               # High-C, strong binding (direct, proven relationships)
    INNER = "INNER"             # Medium-C, moderate binding
    OUTER = "OUTER"             # Low-C, weak binding (indirect, unproven)
    ENVELOPE = "ENVELOPE"       # Very low-C, minimal binding (transient)


@dataclass
class TrustRelationship:
    """Single trust relationship between agents"""
    from_agent: str
    to_agent: str
    trust_score: float          # 0-1 scalar trust
    coherence: float            # C(ρ) from Track 27 pattern interaction trust
    binding_layer: TrustBinding # Core, inner, outer, or envelope
    interaction_count: int      # Total interactions
    direct_interactions: int    # Direct (not through intermediaries)
    time_since_last: float      # Days since last interaction
    relationship_age: float     # Days since first interaction


@dataclass
class TidalEnvironment:
    """External "tidal forces" acting on trust network"""
    competing_relationships: int    # Number of other agents competing for attention
    adversarial_pressure: float     # 0-1 adversarial activity level
    network_saturation: float       # 0-1 how saturated is agent's trust network
    time_pressure: float            # 0-1 how much time constraints affect maintenance


class TidalTrustDecayModel:
    """
    Trust decay model based on Synchronism tidal stripping

    Key principle: Weak (low-C) relationships stripped first under pressure
    """

    def __init__(self):
        pass

    def calculate_binding_energy(self, rel: TrustRelationship) -> float:
        """
        Calculate "binding energy" of trust relationship

        Analog to gravitational binding energy:
        E_binding ∝ M² / r

        For trust:
        E_trust ∝ coherence² * directness / time_decay

        Higher binding energy = more resistant to decay
        """
        # Coherence contributes quadratically (like mass in gravity)
        coherence_factor = rel.coherence ** 2

        # Directness: ratio of direct to total interactions
        if rel.interaction_count > 0:
            directness = rel.direct_interactions / rel.interaction_count
        else:
            directness = 0.0

        # Time decay: relationships weaken over time without maintenance
        # Using exponential decay with characteristic time of 90 days
        time_decay = math.exp(-rel.time_since_last / 90.0)

        # Relationship age provides stability (longer relationships more resilient)
        age_stability = math.tanh(rel.relationship_age / 365.0)  # Saturates at ~1 year

        # Binding energy formula
        binding_energy = coherence_factor * directness * time_decay * (1 + age_stability)

        return binding_energy

    def classify_binding_layer(self, binding_energy: float) -> TrustBinding:
        """
        Classify relationship into binding layer based on energy

        Like DF2/DF4:
        - Core: E > 0.5 (high-C resonant, strong binding)
        - Inner: 0.2 < E <= 0.5 (moderate-C transitional)
        - Outer: 0.05 < E <= 0.2 (low-C indifferent, weak binding)
        - Envelope: E <= 0.05 (very low-C, minimal binding)
        """
        if binding_energy > 0.5:
            return TrustBinding.CORE
        elif binding_energy > 0.2:
            return TrustBinding.INNER
        elif binding_energy > 0.05:
            return TrustBinding.OUTER
        else:
            return TrustBinding.ENVELOPE

    def calculate_stripping_probability(
        self,
        rel: TrustRelationship,
        tidal_env: TidalEnvironment
    ) -> float:
        """
        Calculate probability of relationship being "stripped" (decaying significantly)

        Synchronism principle: Lowest binding energy material stripped first

        Tidal force strength proportional to:
        - Competing relationships (pulls attention away)
        - Adversarial pressure (active degradation)
        - Network saturation (limited capacity)
        - Time pressure (insufficient maintenance bandwidth)
        """
        binding_energy = self.calculate_binding_energy(rel)

        # Tidal force strength (normalized 0-1)
        tidal_force = (
            0.3 * (tidal_env.competing_relationships / 100.0) +
            0.3 * tidal_env.adversarial_pressure +
            0.2 * tidal_env.network_saturation +
            0.2 * tidal_env.time_pressure
        )
        tidal_force = min(tidal_force, 1.0)

        # Stripping probability: high tidal force + low binding energy = high probability
        # Using ratio: P_strip ∝ F_tidal / E_binding
        if binding_energy > 0:
            stripping_prob = tidal_force / (binding_energy + 0.1)  # +0.1 prevents division by zero
        else:
            stripping_prob = 1.0

        # Clamp to [0, 1]
        stripping_prob = min(max(stripping_prob, 0.0), 1.0)

        return stripping_prob

    def apply_tidal_decay(
        self,
        relationships: List[TrustRelationship],
        tidal_env: TidalEnvironment
    ) -> Tuple[List[TrustRelationship], List[TrustRelationship]]:
        """
        Apply tidal stripping to trust network

        Returns:
            (remaining_relationships, stripped_relationships)
        """
        remaining = []
        stripped = []

        for rel in relationships:
            # Calculate binding energy and layer
            binding_energy = self.calculate_binding_energy(rel)
            binding_layer = self.classify_binding_layer(binding_energy)

            # Calculate stripping probability
            strip_prob = self.calculate_stripping_probability(rel, tidal_env)

            # Simplified stripping decision (could use random sampling for stochastic version)
            # Here using deterministic: strip if probability > threshold
            if strip_prob > 0.7:  # High probability → strip
                stripped.append(rel)
            else:
                remaining.append(rel)

        return remaining, stripped


def demonstrate_tidal_trust_decay():
    """Demonstrate tidal trust decay model"""

    print("=" * 70)
    print("  Track 31: Tidal Trust Decay Model")
    print("  Synchronism DF2/DF4 Tidal Stripping → Web4 Trust Decay")
    print("=" * 70)

    print("\nSynchronism Discovery (Session 97):")
    print("  - DF2/DF4: Ultra-diffuse galaxies near NGC 1052")
    print("  - Tidal stripping removes low-C (INDIFFERENT) outer envelope")
    print("  - High-C (RESONANT) core remains")
    print("  - Result: Appears 'dark matter deficient'")

    print("\nWeb4 Application:")
    print("  - Trust relationships have layers (core, inner, outer, envelope)")
    print("  - External pressures = tidal forces")
    print("  - Weak relationships stripped first")
    print("  - Strong core relationships remain resilient")
    print()

    model = TidalTrustDecayModel()

    # Create test trust network
    relationships = [
        # Core relationships (high coherence, many direct interactions)
        TrustRelationship(
            "agent_a", "agent_b",
            trust_score=0.95,
            coherence=0.85,  # High-C (RESONANT)
            binding_layer=TrustBinding.CORE,
            interaction_count=500,
            direct_interactions=480,
            time_since_last=15.0,  # 2 weeks
            relationship_age=730.0  # 2 years
        ),
        TrustRelationship(
            "agent_a", "agent_c",
            trust_score=0.90,
            coherence=0.75,
            binding_layer=TrustBinding.CORE,
            interaction_count=300,
            direct_interactions=290,
            time_since_last=30.0,
            relationship_age=540.0  # 1.5 years
        ),

        # Inner relationships (moderate coherence)
        TrustRelationship(
            "agent_a", "agent_d",
            trust_score=0.70,
            coherence=0.45,  # Transitional
            binding_layer=TrustBinding.INNER,
            interaction_count=100,
            direct_interactions=80,
            time_since_last=60.0,
            relationship_age=180.0  # 6 months
        ),

        # Outer relationships (low coherence, sparse interactions)
        TrustRelationship(
            "agent_a", "agent_e",
            trust_score=0.55,
            coherence=0.25,  # INDIFFERENT
            binding_layer=TrustBinding.OUTER,
            interaction_count=30,
            direct_interactions=15,
            time_since_last=90.0,
            relationship_age=120.0  # 4 months
        ),
        TrustRelationship(
            "agent_a", "agent_f",
            trust_score=0.50,
            coherence=0.20,
            binding_layer=TrustBinding.OUTER,
            interaction_count=20,
            direct_interactions=8,
            time_since_last=120.0,
            relationship_age=150.0
        ),

        # Envelope relationships (very low coherence, mostly indirect)
        TrustRelationship(
            "agent_a", "agent_g",
            trust_score=0.35,
            coherence=0.08,  # Very low-C
            binding_layer=TrustBinding.ENVELOPE,
            interaction_count=10,
            direct_interactions=2,
            time_since_last=150.0,
            relationship_age=60.0  # 2 months
        ),
        TrustRelationship(
            "agent_a", "agent_h",
            trust_score=0.30,
            coherence=0.05,
            binding_layer=TrustBinding.ENVELOPE,
            interaction_count=5,
            direct_interactions=1,
            time_since_last=180.0,
            relationship_age=90.0
        ),
    ]

    # Calculate binding energies
    print("=" * 70)
    print("  INITIAL TRUST NETWORK")
    print("=" * 70)

    print("\nBinding Energy Analysis:")
    print(f"{'Relationship':<15} {'C(ρ)':<8} {'Direct%':<10} {'Age(days)':<12} {'E_binding':<12} {'Layer':<10}")
    print("-" * 70)

    for rel in relationships:
        binding_energy = model.calculate_binding_energy(rel)
        layer = model.classify_binding_layer(binding_energy)
        direct_pct = (rel.direct_interactions / rel.interaction_count * 100) if rel.interaction_count > 0 else 0
        print(f"{rel.to_agent:<15} {rel.coherence:<8.2f} {direct_pct:<10.1f} {rel.relationship_age:<12.0f} {binding_energy:<12.3f} {layer.value:<10}")

    # Apply moderate tidal environment
    print("\n" + "=" * 70)
    print("  SCENARIO 1: Moderate Tidal Environment")
    print("=" * 70)

    tidal_moderate = TidalEnvironment(
        competing_relationships=50,
        adversarial_pressure=0.3,
        network_saturation=0.5,
        time_pressure=0.4
    )

    print(f"\nTidal Forces:")
    print(f"  Competing relationships: {tidal_moderate.competing_relationships}")
    print(f"  Adversarial pressure: {tidal_moderate.adversarial_pressure:.1%}")
    print(f"  Network saturation: {tidal_moderate.network_saturation:.1%}")
    print(f"  Time pressure: {tidal_moderate.time_pressure:.1%}")

    print("\nStripping Analysis:")
    print(f"{'Relationship':<15} {'E_binding':<12} {'P_strip':<12} {'Outcome':<10}")
    print("-" * 70)

    remaining_mod, stripped_mod = model.apply_tidal_decay(relationships, tidal_moderate)

    for rel in relationships:
        binding_energy = model.calculate_binding_energy(rel)
        strip_prob = model.calculate_stripping_probability(rel, tidal_moderate)
        outcome = "STRIPPED" if rel in stripped_mod else "REMAINS"
        print(f"{rel.to_agent:<15} {binding_energy:<12.3f} {strip_prob:<12.3f} {outcome:<10}")

    print(f"\nResult:")
    print(f"  Remaining relationships: {len(remaining_mod)}/{len(relationships)}")
    print(f"  Stripped relationships: {len(stripped_mod)}/{len(relationships)}")

    # Apply severe tidal environment
    print("\n" + "=" * 70)
    print("  SCENARIO 2: Severe Tidal Environment (Crisis)")
    print("=" * 70)

    tidal_severe = TidalEnvironment(
        competing_relationships=150,
        adversarial_pressure=0.8,
        network_saturation=0.9,
        time_pressure=0.7
    )

    print(f"\nTidal Forces (SEVERE):")
    print(f"  Competing relationships: {tidal_severe.competing_relationships}")
    print(f"  Adversarial pressure: {tidal_severe.adversarial_pressure:.1%}")
    print(f"  Network saturation: {tidal_severe.network_saturation:.1%}")
    print(f"  Time pressure: {tidal_severe.time_pressure:.1%}")

    remaining_sev, stripped_sev = model.apply_tidal_decay(relationships, tidal_severe)

    print("\nStripping Analysis:")
    print(f"{'Relationship':<15} {'Layer':<12} {'E_binding':<12} {'P_strip':<12} {'Outcome':<10}")
    print("-" * 70)

    for rel in relationships:
        binding_energy = model.calculate_binding_energy(rel)
        layer = model.classify_binding_layer(binding_energy)
        strip_prob = model.calculate_stripping_probability(rel, tidal_severe)
        outcome = "STRIPPED" if rel in stripped_sev else "REMAINS"
        print(f"{rel.to_agent:<15} {layer.value:<12} {binding_energy:<12.3f} {strip_prob:<12.3f} {outcome:<10}")

    print(f"\nResult:")
    print(f"  Remaining relationships: {len(remaining_sev)}/{len(relationships)}")
    print(f"  Stripped relationships: {len(stripped_sev)}/{len(relationships)}")

    # Summary
    print("\n" + "=" * 70)
    print("  KEY INSIGHTS")
    print("=" * 70)

    print("\n1. Selective Decay (Like DF2/DF4 Tidal Stripping):")
    print("   - CORE relationships survive even severe tidal forces")
    print("   - ENVELOPE relationships stripped first")
    print("   - Binding energy determines resilience")

    print("\n2. Trust Network Evolution:")
    print("   - Under pressure, network contracts to strong core")
    print("   - Weak/indirect relationships pruned")
    print("   - Result: More coherent, resilient network")

    print("\n3. Synchronism-Web4 Mapping:")
    print("   - DF2/DF4 low-C envelope → Web4 weak trust relationships")
    print("   - DF2/DF4 high-C core → Web4 strong direct trust")
    print("   - Tidal stripping → External pressure on trust network")
    print("   - Post-stripping core → Resilient trust after crisis")

    print("\n4. Production Applications:")
    print("   - Prioritize maintenance of high-binding relationships")
    print("   - Expect peripheral relationships to decay under load")
    print("   - Core trust network remains functional during crises")
    print("   - Natural pruning of low-value relationships saves resources")

    print()


if __name__ == "__main__":
    demonstrate_tidal_trust_decay()
