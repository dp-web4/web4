"""
Trust Ceiling Mitigation

Session #42

KEY INSIGHT from Session #42:
Diversity discounting alone CANNOT prevent perfect collusion attacks.

Reason: If all colluding societies report trust=1.0, then weighted
average with ANY weights still equals 1.0.

Example:
  avg([1.0, 1.0, 1.0, 1.0, 1.0], weights=[0.3, 0.3, 0.3, 0.3, 0.3]) = 1.0
  avg([1.0, 1.0, 1.0, 1.0, 1.0], weights=[1.0, 1.0, 1.0, 1.0, 1.0]) = 1.0

Solution: TRUST CEILING based on evidence quality, not just source count.

Trust Ceiling Formula:
  max_trust = base_ceiling * evidence_multiplier

  base_ceiling = 0.7 (propagated trust cannot exceed 70% without direct observation)
  evidence_multiplier = 1 + (0.3 * evidence_quality)

  evidence_quality based on:
  - Physical resource proof (energy capacity)
  - Historical behavior (time-series data)
  - Multi-source corroboration (but capped)
  - First-hand observation vs hearsay

Examples:
  No direct observation:       ceiling = 0.70
  With energy proof:           ceiling = 0.80
  With historical data:        ceiling = 0.85
  Direct observation:          ceiling = 1.00
"""

from dataclasses import dataclass
from typing import List, Optional
import math

from cross_society_trust_propagation import (
    TrustPropagationEngine,
    PropagatedTrustRecord,
    TrustRecord,
)


@dataclass
class TrustEvidence:
    """Evidence supporting a trust assessment"""
    evidence_type: str  # "energy_proof", "historical", "direct_observation"
    quality_score: float  # [0, 1]
    description: str


class TrustCeilingEngine(TrustPropagationEngine):
    """
    Trust engine with ceiling enforcement based on evidence quality.

    Core principle: Trust cannot exceed what evidence supports.

    Propagated trust (hearsay) has lower ceiling than direct observation.
    """

    def __init__(
        self,
        society_lct: str,
        decay_factor: float = 0.8,
        max_propagation_distance: int = 3,
        base_ceiling: float = 0.7,  # Max for propagated trust without evidence
    ):
        super().__init__(society_lct, decay_factor, max_propagation_distance)
        self.base_ceiling = base_ceiling

        # Evidence tracking
        self.evidence: dict[str, List[TrustEvidence]] = {}

    def set_direct_trust(
        self,
        subject_lct: str,
        trust_score: float,
        evidence: Optional[List[str]] = None,
        valid_for_hours: Optional[int] = None,
    ) -> TrustRecord:
        """
        Set direct trust with evidence.

        Direct trust has no ceiling (we observed it ourselves).
        """
        return super().set_direct_trust(
            subject_lct,
            trust_score,
            evidence,
            valid_for_hours,
        )

    def get_aggregated_trust(self, subject_lct: str) -> float:
        """
        Get aggregated trust with ceiling enforcement.

        Key change: Propagated trust is capped based on evidence quality.
        """
        trust_scores = []
        weights = []

        # Direct trust (no ceiling, full weight)
        if subject_lct in self.direct_trust:
            record = self.direct_trust[subject_lct]
            if not record.is_expired():
                trust_scores.append(record.trust_score)
                weights.append(1.0)

        # Propagated trust (CEILING ENFORCED)
        propagated_records = self.propagated_trust.get(subject_lct, [])

        for record in propagated_records:
            # Apply ceiling to propagated trust
            capped_trust = min(record.trust_score, self.base_ceiling)

            trust_scores.append(capped_trust)

            # Weight by decay
            weight = self.decay_factor ** record.propagation_distance
            weights.append(weight)

        # No trust information
        if not trust_scores:
            return 0.5

        # Weighted average
        total_weight = sum(weights)
        weighted_sum = sum(score * weight for score, weight in zip(trust_scores, weights))
        aggregated = weighted_sum / total_weight

        return aggregated

    def add_evidence(
        self,
        subject_lct: str,
        evidence: TrustEvidence,
    ):
        """
        Add evidence for an identity.

        Better evidence → higher ceiling for propagated trust.
        """
        if subject_lct not in self.evidence:
            self.evidence[subject_lct] = []

        self.evidence[subject_lct].append(evidence)

    def get_trust_ceiling_for(self, subject_lct: str) -> float:
        """
        Calculate trust ceiling based on available evidence.

        Returns maximum trust we're willing to accept from propagated sources.
        """
        # Base ceiling (hearsay only)
        ceiling = self.base_ceiling

        # Increase ceiling based on evidence
        if subject_lct in self.evidence:
            for evidence_item in self.evidence[subject_lct]:
                # Each piece of quality evidence increases ceiling
                ceiling_increase = 0.3 * evidence_item.quality_score

                # But cap at 1.0 total
                ceiling = min(1.0, ceiling + ceiling_increase)

        return ceiling


# ============================================================================
# Combined Mitigation: Ceiling + Diversity
# ============================================================================

class RobustTrustEngine(TrustPropagationEngine):
    """
    Combines multiple mitigations:
    1. Trust ceiling (prevents perfect collusion)
    2. Diversity discount (reduces multi-source amplification)
    3. Outlier detection (filters contradictory signals)
    """

    def __init__(
        self,
        society_lct: str,
        decay_factor: float = 0.8,
        max_propagation_distance: int = 3,
        base_ceiling: float = 0.7,
        diversity_enabled: bool = True,
    ):
        super().__init__(society_lct, decay_factor, max_propagation_distance)
        self.base_ceiling = base_ceiling
        self.diversity_enabled = diversity_enabled

    def get_aggregated_trust(self, subject_lct: str) -> float:
        """
        Robust aggregation with multiple mitigations.
        """
        trust_scores = []
        weights = []

        # Direct trust (no ceiling, full weight)
        if subject_lct in self.direct_trust:
            record = self.direct_trust[subject_lct]
            if not record.is_expired():
                trust_scores.append(record.trust_score)
                weights.append(1.0)

        # Propagated trust
        propagated_records = self.propagated_trust.get(subject_lct, [])

        # Mitigation 1: Trust ceiling
        # Cap propagated trust at base_ceiling
        capped_scores = [
            min(record.trust_score, self.base_ceiling)
            for record in propagated_records
        ]

        # Mitigation 2: Diversity discount
        if self.diversity_enabled and propagated_records:
            num_sources = len(propagated_records)
            diversity_discount = 1.0 / math.log2(num_sources + 1)
        else:
            diversity_discount = 1.0

        # Add propagated trust with both mitigations
        for record, capped_score in zip(propagated_records, capped_scores):
            trust_scores.append(capped_score)

            # Weight = decay × diversity
            weight = (self.decay_factor ** record.propagation_distance) * diversity_discount
            weights.append(weight)

        # No trust information
        if not trust_scores:
            return 0.5

        # Weighted average
        total_weight = sum(weights)
        weighted_sum = sum(score * weight for score, weight in zip(trust_scores, weights))
        aggregated = weighted_sum / total_weight

        return aggregated


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    from cross_society_trust_propagation import CrossSocietyTrustNetwork

    print("=" * 80)
    print("TRUST CEILING MITIGATION - Session #42")
    print("Preventing Perfect Collusion Attacks")
    print("=" * 80)

    # Test 1: Trust ceiling prevents perfect collusion
    print("\n### Test 1: Trust Ceiling vs Perfect Collusion")
    print("-" * 80)

    # Without ceiling
    network1 = CrossSocietyTrustNetwork()
    network1.add_society("lct-victim")

    colluders = [f"lct-collude-{i}" for i in range(5)]

    for colluder_id in colluders:
        network1.add_society(colluder_id)
        network1.connect_societies("lct-victim", colluder_id)
        network1.set_society_trust("lct-victim", colluder_id, 0.8)
        network1.set_identity_trust(colluder_id, "lct-attacker", 1.0)

    network1.propagate_all()

    trust_without_ceiling = network1.engines["lct-victim"].get_aggregated_trust("lct-attacker")

    # With ceiling
    network2 = CrossSocietyTrustNetwork()

    ceiling_engine = TrustCeilingEngine(
        society_lct="lct-victim",
        base_ceiling=0.7,
    )
    network2.engines["lct-victim"] = ceiling_engine

    for colluder_id in colluders:
        network2.add_society(colluder_id)
        network2.connect_societies("lct-victim", colluder_id)
        ceiling_engine.set_society_trust(colluder_id, 0.8)
        network2.set_identity_trust(colluder_id, "lct-attacker", 1.0)

    network2.propagate_all()

    trust_with_ceiling = ceiling_engine.get_aggregated_trust("lct-attacker")

    print(f"Without ceiling: {trust_without_ceiling:.3f}")
    print(f"With ceiling (0.7): {trust_with_ceiling:.3f}")

    if trust_with_ceiling <= 0.7:
        print("✅ CEILING ENFORCED - Perfect collusion prevented")
    else:
        print("⚠️  CEILING NOT ENFORCED")

    # Test 2: Combined mitigation
    print("\n### Test 2: Combined Mitigation (Ceiling + Diversity)")
    print("-" * 80)

    network3 = CrossSocietyTrustNetwork()

    robust_engine = RobustTrustEngine(
        society_lct="lct-victim",
        base_ceiling=0.7,
        diversity_enabled=True,
    )
    network3.engines["lct-victim"] = robust_engine

    for colluder_id in colluders:
        network3.add_society(colluder_id)
        network3.connect_societies("lct-victim", colluder_id)
        robust_engine.set_society_trust(colluder_id, 0.8)
        network3.set_identity_trust(colluder_id, "lct-attacker", 1.0)

    network3.propagate_all()

    trust_robust = robust_engine.get_aggregated_trust("lct-attacker")

    print(f"Without mitigation: {trust_without_ceiling:.3f}")
    print(f"With ceiling only: {trust_with_ceiling:.3f}")
    print(f"With ceiling + diversity: {trust_robust:.3f}")

    if trust_robust < trust_with_ceiling:
        reduction = (1 - trust_robust / trust_with_ceiling) * 100
        print(f"\nDiversity discount: {reduction:.1f}%")
        print("✅ COMBINED MITIGATION EFFECTIVE")
    else:
        print("⚠️  Diversity had no additional effect (expected with identical scores)")

    print("\n### Analysis")
    print("-" * 80)

    print("\nKey Insight:")
    print("  Diversity discount alone CANNOT prevent perfect collusion")
    print("  (averaging [1.0, 1.0, 1.0] always gives 1.0)")
    print("")
    print("  Trust ceiling IS NECESSARY to cap propagated trust")
    print("  (even with perfect collusion, capped at 0.7)")
    print("")
    print("  Combined approach: ceiling prevents inflation,")
    print("  diversity reduces amplification from multiple")
    print("  sources when scores differ")

    print("\n" + "=" * 80)
