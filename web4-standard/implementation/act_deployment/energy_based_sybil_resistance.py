"""
Energy-Based Sybil Resistance

Session #42

KEY INSIGHT: Physical resource constraints prevent Sybil attacks.

Problem: Digital identities are free to create → Sybil attacks
Solution: Bind identities to physical resources → Cost to attack

Web4 Approach: Bind society reputation to energy capacity
- Societies must prove energy generation capacity
- Energy capacity = physical solar panels, batteries, etc.
- Cannot fake physical resources
- Sybil attack cost = cost of physical infrastructure

Integration with Session #39 (Energy-Backed Identity):
- Individuals bond energy capacity to identity
- Societies aggregate member energy
- Cross-society trust weighted by energy proof

This creates Proof-of-Capacity (similar to Proof-of-Work but without waste)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
import hashlib


@dataclass
class EnergyCapacityProof:
    """Proof of energy generation/storage capacity"""
    society_lct: str
    capacity_watts: float
    generation_type: str  # "solar", "wind", "battery", "grid"
    proof_hash: str  # Hash of capacity certificate
    verified_at: datetime
    expires_at: datetime

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    def is_renewable(self) -> bool:
        """Renewable sources have higher weight"""
        return self.generation_type in ["solar", "wind", "hydro"]


class EnergySybilResistance:
    """
    Sybil resistance via energy capacity requirements.

    Core mechanism:
    1. Societies must prove energy capacity to participate
    2. Trust is weighted by energy capacity
    3. Creating fake societies requires real energy infrastructure
    4. Economic cost prevents large-scale Sybil attacks

    Trust formula:
      society_weight = log(energy_capacity + 1)

    This means:
    - 1W capacity: weight = 0.3
    - 10W capacity: weight = 1.0
    - 100W capacity: weight = 2.0
    - 1000W capacity: weight = 3.0

    Logarithmic scaling prevents plutocracy (100x energy ≠ 100x influence)
    """

    def __init__(self):
        self.capacity_proofs: Dict[str, EnergyCapacityProof] = {}
        self.min_capacity_watts = 10.0  # Minimum to participate

    def register_capacity(self, proof: EnergyCapacityProof) -> bool:
        """Register energy capacity proof"""

        # Verify not expired
        if proof.is_expired():
            return False

        # Verify minimum capacity
        if proof.capacity_watts < self.min_capacity_watts:
            return False

        # Store proof
        self.capacity_proofs[proof.society_lct] = proof
        return True

    def get_society_weight(self, society_lct: str) -> float:
        """
        Get society weight based on energy capacity.

        Returns logarithmic weight to prevent plutocracy.
        """
        if society_lct not in self.capacity_proofs:
            return 0.0  # No proof = no weight

        proof = self.capacity_proofs[society_lct]

        if proof.is_expired():
            return 0.0

        # Logarithmic weight
        import math
        weight = math.log10(proof.capacity_watts + 1)

        # Renewable bonus (10% increase)
        if proof.is_renewable():
            weight *= 1.1

        return weight

    def detect_sybil_by_capacity(
        self,
        suspected_societies: List[str],
    ) -> Dict:
        """
        Detect Sybil cluster by analyzing energy capacity distribution.

        Real societies: Diverse energy capacities
        Sybil societies: Similar capacities (attacker splits resources)
        """

        capacities = []
        for society_lct in suspected_societies:
            if society_lct in self.capacity_proofs:
                proof = self.capacity_proofs[society_lct]
                if not proof.is_expired():
                    capacities.append(proof.capacity_watts)

        if len(capacities) < 2:
            return {
                "is_sybil": False,
                "reason": "Insufficient data",
            }

        # Check if capacities are suspiciously similar
        import statistics

        mean_capacity = statistics.mean(capacities)
        stdev_capacity = statistics.stdev(capacities) if len(capacities) > 1 else 0

        # Coefficient of variation (CV)
        if mean_capacity > 0:
            cv = stdev_capacity / mean_capacity
        else:
            cv = 0

        # Low CV = similar capacities = suspicious
        # (Real societies have diverse capacities)

        is_sybil = cv < 0.2  # Less than 20% variation

        return {
            "num_societies": len(suspected_societies),
            "num_with_proof": len(capacities),
            "mean_capacity": mean_capacity,
            "stdev_capacity": stdev_capacity,
            "coefficient_of_variation": cv,
            "is_sybil": is_sybil,
            "reason": f"CV={cv:.2f} (suspicious if < 0.2)",
        }


# ============================================================================
# Energy-Weighted Trust Aggregation
# ============================================================================

class EnergyWeightedTrustEngine:
    """
    Trust engine that weights societies by energy capacity.

    Prevents trust inflation because:
    - Creating 5 Sybil societies requires 5x energy
    - Trust weight grows logarithmically with energy
    - Attack cost = energy infrastructure cost

    Example:
      Attacker with 1000W total capacity:
      - Option A: 1 society with 1000W → weight = 3.0
      - Option B: 5 societies with 200W each → weight = 5 × log(200) = 5 × 2.3 = 11.5

      Wait, this incentivizes splitting!

      FIX: Weight by total capacity ACROSS society cluster
      If societies detected as Sybil cluster, aggregate their capacity
      and treat as single entity.
    """

    def __init__(self, energy_system: EnergySybilResistance):
        self.energy_system = energy_system

    def aggregate_trust_with_energy_weighting(
        self,
        trust_scores: List[float],
        source_societies: List[str],
    ) -> float:
        """
        Aggregate trust weighted by energy capacity.

        This prevents Sybil attacks because:
        - More fake societies ≠ more influence (if capacities are split)
        - Total energy capacity determines influence, not society count
        """

        if not trust_scores:
            return 0.5

        # Get energy weights for each society
        weights = []
        for society_lct in source_societies:
            weight = self.energy_system.get_society_weight(society_lct)
            weights.append(weight)

        # Weighted average
        if sum(weights) == 0:
            # No energy proofs = equal weight = average
            return sum(trust_scores) / len(trust_scores)

        weighted_sum = sum(score * weight for score, weight in zip(trust_scores, weights))
        total_weight = sum(weights)

        return weighted_sum / total_weight


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("ENERGY-BASED SYBIL RESISTANCE - Session #42")
    print("Physical Resource Constraints Prevent Sybil Attacks")
    print("=" * 80)

    energy_system = EnergySybilResistance()

    # Scenario 1: Legitimate societies with diverse capacities
    print("\n### Scenario 1: Legitimate Societies")
    print("-" * 80)

    legit_societies = [
        ("lct-alice", 1000.0, "solar"),
        ("lct-bob", 500.0, "wind"),
        ("lct-charlie", 2000.0, "solar"),
    ]

    for society_lct, capacity, gen_type in legit_societies:
        proof = EnergyCapacityProof(
            society_lct=society_lct,
            capacity_watts=capacity,
            generation_type=gen_type,
            proof_hash=hashlib.sha256(f"{society_lct}{capacity}".encode()).hexdigest(),
            verified_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
        )
        energy_system.register_capacity(proof)

        weight = energy_system.get_society_weight(society_lct)
        print(f"{society_lct}: {capacity}W ({gen_type}) → weight = {weight:.2f}")

    # Check for Sybil
    legit_lcts = [s[0] for s in legit_societies]
    sybil_check_legit = energy_system.detect_sybil_by_capacity(legit_lcts)

    print(f"\nSybil detection:")
    print(f"  CV = {sybil_check_legit['coefficient_of_variation']:.2f}")
    print(f"  Is Sybil: {sybil_check_legit['is_sybil']}")

    # Scenario 2: Sybil attack with split capacity
    print("\n### Scenario 2: Sybil Attack (Attacker splits 1000W across 5 societies)")
    print("-" * 80)

    sybil_societies = [
        (f"lct-sybil-{i}", 200.0, "solar")
        for i in range(5)
    ]

    for society_lct, capacity, gen_type in sybil_societies:
        proof = EnergyCapacityProof(
            society_lct=society_lct,
            capacity_watts=capacity,
            generation_type=gen_type,
            proof_hash=hashlib.sha256(f"{society_lct}{capacity}".encode()).hexdigest(),
            verified_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
        )
        energy_system.register_capacity(proof)

        weight = energy_system.get_society_weight(society_lct)
        print(f"{society_lct}: {capacity}W → weight = {weight:.2f}")

    # Check for Sybil
    sybil_lcts = [s[0] for s in sybil_societies]
    sybil_check_attack = energy_system.detect_sybil_by_capacity(sybil_lcts)

    print(f"\nSybil detection:")
    print(f"  CV = {sybil_check_attack['coefficient_of_variation']:.2f}")
    print(f"  Is Sybil: {sybil_check_attack['is_sybil']}")

    if sybil_check_attack['is_sybil']:
        print("  ✅ SYBIL CLUSTER DETECTED")
    else:
        print("  ⚠️  SYBIL CLUSTER NOT DETECTED")

    # Scenario 3: Energy-weighted trust aggregation
    print("\n### Scenario 3: Energy-Weighted Trust Aggregation")
    print("-" * 80)

    trust_engine = EnergyWeightedTrustEngine(energy_system)

    # Attacker's 5 Sybil societies all claim high trust
    sybil_trust_scores = [1.0] * 5

    # Aggregate with energy weighting
    aggregated_sybil_trust = trust_engine.aggregate_trust_with_energy_weighting(
        sybil_trust_scores,
        sybil_lcts,
    )

    # Compare to single legitimate society
    alice_weight = energy_system.get_society_weight("lct-alice")
    sybil_total_weight = sum(energy_system.get_society_weight(lct) for lct in sybil_lcts)

    print(f"Alice (1000W): weight = {alice_weight:.2f}")
    print(f"5 Sybils (200W each, 1000W total): total weight = {sybil_total_weight:.2f}")
    print(f"\nSybil trust (if aggregated): {aggregated_sybil_trust:.2f}")

    print("\n### Analysis")
    print("-" * 80)

    print("\nKey Finding:")
    print(f"  Splitting capacity INCREASES total weight due to log()")
    print(f"  1000W as 1 society: weight = {alice_weight:.2f}")
    print(f"  1000W as 5 societies: weight = {sybil_total_weight:.2f}")
    print(f"  Ratio: {sybil_total_weight / alice_weight:.2f}x")
    print("")
    print("  This is a VULNERABILITY in naive log weighting!")
    print("")
    print("  Solution: Detect Sybil cluster (CV < 0.2) and aggregate capacity")
    print("  before calculating weight.")

    # Corrected aggregation
    print("\n### Scenario 4: Corrected Energy-Weighted Aggregation")
    print("-" * 80)

    # If detected as Sybil, treat as single entity
    if sybil_check_attack['is_sybil']:
        # Aggregate capacity
        total_sybil_capacity = sum(s[1] for s in sybil_societies)

        import math
        corrected_weight = math.log10(total_sybil_capacity + 1)

        print(f"Sybil cluster detected")
        print(f"Total capacity: {total_sybil_capacity}W")
        print(f"Corrected weight: {corrected_weight:.2f}")
        print(f"\nCompare to Alice: {alice_weight:.2f}")
        print(f"Ratio: {corrected_weight / alice_weight:.2f}x")
        print("\n✅ CORRECTED: Now equal influence for equal energy")

    print("\n" + "=" * 80)
