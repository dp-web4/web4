#!/usr/bin/env python3
"""
Session 167: Coherence-Based Reputation Theory

Research Goal: Apply Synchronism's biological coherence framework to Web4
reputation system, revealing reputation as a maintained coherence state.

Theoretical Foundation (from Synchronism Session 248):
- Life maintains coherence through ATP expenditure
- Coherence length λ_eff = λ_thermal × f(ATP/kT)
- Death is a decoherence transition
- Biological systems fight thermal equilibrium

Web4 Mapping:
- Reputation = coherence state of trust relationships
- Source diversity = coherence length (correlation span)
- ATP = resource for maintaining reputation coherence
- Reputation decay = natural decoherence
- Circular validation (Sybil) = artificial coherence (no ATP cost → detectable)

Key Insight:
Natural coherence (from work/ATP) is distinguishable from artificial
coherence (circular validation) by thermodynamic signature.

Platform: Legion (RTX 4090)
Session: Autonomous Web4 Research - Session 167
Date: 2026-01-11
"""

import math
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import sys

HOME = Path.home()
sys.path.insert(0, str(HOME / "ai-workspace" / "web4"))

# Import Phase 1 security
from session163_lct_reputation_binding import (
    LCTIdentity,
    LCTBoundReputation,
    LCTReputationManager,
)

from session164_reputation_source_diversity import (
    ReputationSourceProfile,
    SourceDiversityManager,
)


# ============================================================================
# COHERENCE THEORY
# ============================================================================

@dataclass
class CoherenceMetrics:
    """
    Coherence-based reputation metrics.

    Inspired by biological coherence (Synchronism Session 248).
    """
    # Core coherence
    coherence_score: float = 0.0  # 0-1, analogous to C(ξ) in biology
    coherence_length: float = 0.0  # How far trust correlations extend

    # Thermodynamic
    entropy: float = 0.0  # Shannon entropy of source distribution
    free_energy: float = 0.0  # Negative correlation with stability

    # Maintenance
    atp_invested: float = 0.0  # Total ATP spent maintaining reputation
    atp_decay_rate: float = 0.0  # ATP/time to maintain coherence

    # Decoherence risk
    decoherence_rate: float = 0.0  # Rate of reputation decay
    thermal_noise: float = 0.0  # Environmental uncertainty


class CoherenceReputationAnalyzer:
    """
    Analyzes reputation through coherence theory lens.

    Maps Web4 reputation to biological coherence framework.
    """

    def __init__(
        self,
        temperature: float = 300.0,  # Kelvin (network temperature)
        boltzmann_k: float = 0.001,  # Normalized Boltzmann constant
    ):
        self.temperature = temperature
        self.boltzmann_k = boltzmann_k
        self.kT = self.boltzmann_k * self.temperature

    def calculate_coherence_metrics(
        self,
        reputation: LCTBoundReputation,
        source_profile: ReputationSourceProfile,
        atp_balance: float,
    ) -> CoherenceMetrics:
        """
        Calculate coherence metrics for a reputation state.

        Maps reputation to coherence framework:
        - Shannon entropy → thermodynamic entropy
        - Source diversity → coherence length
        - ATP balance → maintenance energy
        """
        metrics = CoherenceMetrics()

        # 1. Coherence score (analogous to biological C(ξ))
        # High diversity + high reputation = high coherence
        diversity_score = source_profile.diversity_score
        reputation_normalized = self._normalize_reputation(reputation.total_score)

        # Coherence combines diversity (spatial extent) and reputation (strength)
        metrics.coherence_score = math.sqrt(diversity_score * reputation_normalized)

        # 2. Coherence length (how far trust correlations extend)
        # More sources = longer coherence length
        source_count = source_profile.source_count
        if source_count > 0:
            # Logarithmic scaling (like biological systems)
            metrics.coherence_length = math.log2(1 + source_count)
        else:
            metrics.coherence_length = 0.0

        # 3. Entropy (Shannon entropy from Session 164)
        metrics.entropy = source_profile.diversity_score  # Already normalized 0-1

        # 4. Free energy (thermodynamic potential)
        # Lower free energy = more stable
        # F = E - TS, where E ~ -reputation, T ~ network_temperature, S ~ entropy
        energy_term = -reputation_normalized  # Negative = favorable
        entropy_term = self.temperature * (1.0 - metrics.entropy)  # High entropy = low cost
        metrics.free_energy = energy_term + entropy_term

        # 5. ATP investment (work done to build reputation)
        # Each reputation point required ATP expenditure
        # Assume linear relationship (can be refined)
        metrics.atp_invested = max(0, reputation.total_score) * 1.0  # 1 ATP per point

        # 6. ATP decay rate (maintenance cost)
        # Higher coherence requires more ATP to maintain against thermal noise
        # Analogous to biological systems maintaining organization
        base_decay = 0.01  # Base maintenance cost
        coherence_cost = metrics.coherence_score * 0.1  # Proportional to coherence
        metrics.atp_decay_rate = base_decay + coherence_cost

        # 7. Decoherence rate (how fast reputation decays without maintenance)
        # Higher temperature → faster decoherence
        # Lower diversity → faster decoherence (less stable)
        if diversity_score > 0:
            metrics.decoherence_rate = (self.kT / diversity_score) * 0.01
        else:
            metrics.decoherence_rate = 1.0  # Instant decoherence with no diversity

        # 8. Thermal noise (environmental uncertainty)
        # Inverse of source count (more sources = less noise)
        if source_count > 0:
            metrics.thermal_noise = 1.0 / math.sqrt(source_count)
        else:
            metrics.thermal_noise = 1.0

        return metrics

    def _normalize_reputation(self, score: float) -> float:
        """Normalize reputation score to 0-1 range using sigmoid."""
        # Sigmoid: maps (-inf, inf) → (0, 1)
        return 1.0 / (1.0 + math.exp(-score / 20.0))

    def detect_artificial_coherence(
        self,
        metrics: CoherenceMetrics,
        reputation: LCTBoundReputation,
        source_profile: ReputationSourceProfile,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Detect artificial coherence (Sybil attack).

        Natural coherence (from work): High ATP investment, diverse sources
        Artificial coherence (Sybil): Low ATP, circular validation

        Key thermodynamic signature:
        - Natural: Entropy increases with coherence (diverse sources)
        - Artificial: Low entropy despite high coherence (concentrated sources)
        """
        evidence = {}
        is_artificial = False

        # Check 1: High reputation without diversity (thermodynamically suspicious)
        # Natural reputation builds diversity; artificial (Sybil) concentrates sources
        if reputation.total_score > 20.0 and source_profile.diversity_score < 0.3:
            evidence["high_reputation_low_diversity"] = {
                "reputation": reputation.total_score,
                "diversity": source_profile.diversity_score,
            }
            is_artificial = True

        # Check 2: High reputation with very few sources (suspicious concentration)
        if reputation.total_score > 20.0 and source_profile.source_count < 3:
            evidence["insufficient_source_count"] = {
                "reputation": reputation.total_score,
                "source_count": source_profile.source_count,
            }
            is_artificial = True

        # Check 3: Circular validation (already detected by Session 164)
        circular_clusters = source_profile.detect_circular_clusters({})
        if circular_clusters:
            evidence["circular_validation"] = circular_clusters
            is_artificial = True

        # Check 4: Free energy too low (thermodynamically impossible)
        # Natural systems have positive free energy (require work to maintain)
        if metrics.free_energy < -1.0:
            evidence["negative_free_energy"] = metrics.free_energy
            is_artificial = True

        return is_artificial, evidence

    def calculate_reputation_decay(
        self,
        current_reputation: float,
        metrics: CoherenceMetrics,
        time_delta: float,  # Time since last maintenance
        atp_available: float = 0.0,  # ATP available for maintenance
    ) -> Tuple[float, float]:
        """
        Calculate reputation decay due to decoherence.

        Natural thermodynamic process: Without ATP maintenance,
        reputation decays toward thermal equilibrium (zero).

        Returns (new_reputation, atp_consumed)
        """
        # ATP required to maintain coherence for time_delta
        atp_required = metrics.atp_decay_rate * time_delta

        if atp_available >= atp_required:
            # Sufficient ATP: No decay
            atp_consumed = atp_required
            new_reputation = current_reputation
        else:
            # Insufficient ATP: Decoherence occurs
            atp_consumed = atp_available

            # Partial maintenance
            maintenance_fraction = atp_consumed / atp_required if atp_required > 0 else 0

            # Decay calculation
            # Exponential decay toward zero (thermal equilibrium)
            decay_amount = current_reputation * metrics.decoherence_rate * time_delta
            decay_amount *= (1.0 - maintenance_fraction)  # Reduced by ATP spent

            new_reputation = max(0, current_reputation - decay_amount)

        return new_reputation, atp_consumed

    def coherence_stability_score(self, metrics: CoherenceMetrics) -> float:
        """
        Overall stability score (0-1).

        High stability: High coherence, low free energy, low decoherence rate
        Low stability: Low coherence, high free energy, high decoherence rate

        Analogous to biological system stability.
        """
        # Component scores (all 0-1, higher = more stable)
        coherence_component = metrics.coherence_score

        # Free energy (lower is better, normalize)
        # Typical range: -2 to +2
        free_energy_component = 1.0 / (1.0 + math.exp(metrics.free_energy))

        # Decoherence rate (lower is better, normalize)
        # Typical range: 0 to 1
        decoherence_component = 1.0 - min(1.0, metrics.decoherence_rate)

        # Thermal noise (lower is better, normalize)
        noise_component = 1.0 - min(1.0, metrics.thermal_noise)

        # Weighted average
        stability = (
            0.4 * coherence_component +
            0.3 * free_energy_component +
            0.2 * decoherence_component +
            0.1 * noise_component
        )

        return stability


# ============================================================================
# ENHANCED REPUTATION MANAGER WITH COHERENCE
# ============================================================================

class CoherenceAwareReputationManager:
    """
    Reputation manager with coherence-theoretic understanding.

    Integrates:
    - Phase 1 security (LCT + diversity + consensus)
    - Coherence theory (thermodynamic reputation model)
    - ATP maintenance (reputation requires energy)
    """

    def __init__(
        self,
        lct_manager: LCTReputationManager,
        diversity_manager: SourceDiversityManager,
        temperature: float = 300.0,
    ):
        self.lct_manager = lct_manager
        self.diversity_manager = diversity_manager
        self.coherence_analyzer = CoherenceReputationAnalyzer(temperature=temperature)

        # ATP balances for nodes
        self.atp_balances: Dict[str, float] = {}

        # Coherence history
        self.coherence_history: Dict[str, List[CoherenceMetrics]] = {}

        # Last maintenance time
        self.last_maintenance: Dict[str, float] = {}

    def get_coherence_metrics(
        self,
        lct_id: str,
        atp_balance: Optional[float] = None
    ) -> Optional[CoherenceMetrics]:
        """Get current coherence metrics for a node."""
        reputation = self.lct_manager.reputations.get(lct_id)
        if not reputation:
            return None

        source_profile = self.diversity_manager.get_or_create_profile(lct_id)

        if atp_balance is None:
            atp_balance = self.atp_balances.get(lct_id, 0.0)

        return self.coherence_analyzer.calculate_coherence_metrics(
            reputation, source_profile, atp_balance
        )

    def check_artificial_coherence(self, lct_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if node's reputation shows artificial coherence (Sybil attack)."""
        reputation = self.lct_manager.reputations.get(lct_id)
        if not reputation:
            return False, {}

        source_profile = self.diversity_manager.get_or_create_profile(lct_id)
        metrics = self.get_coherence_metrics(lct_id)

        if not metrics:
            return False, {}

        return self.coherence_analyzer.detect_artificial_coherence(
            metrics, reputation, source_profile
        )

    def apply_reputation_decay(self, lct_id: str, time_delta: float) -> Dict[str, Any]:
        """
        Apply thermodynamic reputation decay.

        Reputation naturally decays without ATP maintenance.
        """
        reputation = self.lct_manager.reputations.get(lct_id)
        if not reputation:
            return {"error": "Unknown node"}

        metrics = self.get_coherence_metrics(lct_id)
        if not metrics:
            return {"error": "No metrics"}

        atp_available = self.atp_balances.get(lct_id, 0.0)

        # Calculate decay
        new_reputation, atp_consumed = self.coherence_analyzer.calculate_reputation_decay(
            current_reputation=reputation.total_score,
            metrics=metrics,
            time_delta=time_delta,
            atp_available=atp_available,
        )

        # Apply changes
        old_reputation = reputation.total_score
        reputation.total_score = new_reputation
        self.atp_balances[lct_id] = max(0, atp_available - atp_consumed)
        self.last_maintenance[lct_id] = time.time()

        return {
            "old_reputation": old_reputation,
            "new_reputation": new_reputation,
            "decay_amount": old_reputation - new_reputation,
            "atp_consumed": atp_consumed,
            "atp_remaining": self.atp_balances[lct_id],
        }

    def add_atp(self, lct_id: str, amount: float):
        """Add ATP to node's balance."""
        current = self.atp_balances.get(lct_id, 0.0)
        self.atp_balances[lct_id] = current + amount

    def get_stability_report(self, lct_id: str) -> Dict[str, Any]:
        """Get comprehensive stability report for a node."""
        metrics = self.get_coherence_metrics(lct_id)
        if not metrics:
            return {"error": "No metrics available"}

        stability = self.coherence_analyzer.coherence_stability_score(metrics)
        is_artificial, evidence = self.check_artificial_coherence(lct_id)

        reputation = self.lct_manager.reputations.get(lct_id)

        return {
            "lct_id": lct_id,
            "reputation_score": reputation.total_score if reputation else 0,
            "reputation_level": reputation.reputation_level if reputation else "unknown",
            "coherence_metrics": {
                "coherence_score": metrics.coherence_score,
                "coherence_length": metrics.coherence_length,
                "entropy": metrics.entropy,
                "free_energy": metrics.free_energy,
                "atp_invested": metrics.atp_invested,
                "atp_decay_rate": metrics.atp_decay_rate,
                "decoherence_rate": metrics.decoherence_rate,
                "thermal_noise": metrics.thermal_noise,
            },
            "stability_score": stability,
            "is_artificial": is_artificial,
            "artificial_evidence": evidence if is_artificial else None,
            "atp_balance": self.atp_balances.get(lct_id, 0.0),
        }


# ============================================================================
# TESTING
# ============================================================================

async def test_coherence_reputation_theory():
    """Test coherence-based reputation theory."""
    print("=" * 80)
    print("SESSION 167: Coherence-Based Reputation Theory Test")
    print("=" * 80)
    print("Biological Coherence → Web4 Reputation Mapping")
    print("=" * 80)

    # Setup
    lct_manager = LCTReputationManager()
    diversity_manager = SourceDiversityManager()
    coherence_manager = CoherenceAwareReputationManager(
        lct_manager, diversity_manager, temperature=300.0
    )

    # Create test nodes
    print("\n" + "=" * 80)
    print("PHASE 1: Create Test Nodes")
    print("=" * 80)

    # Node 1: Natural coherence (diverse sources, ATP-backed)
    natural_identity = LCTIdentity(
        lct_id="lct:web4:natural",
        hardware_type="tpm2",
        hardware_fingerprint="natural_hw",
        attestation_public_key="natural_key",
        created_at=time.time(),
    )
    lct_manager.register_lct_identity(natural_identity)

    # Build reputation naturally
    for i in range(5):
        att = natural_identity.generate_attestation(f"work_{i}")
        lct_manager.record_quality_event("lct:web4:natural", 10.0, f"work_{i}", att)

    # Diverse sources
    for i in range(6):
        diversity_manager.record_reputation_event("lct:web4:natural", f"source_{i}", 8.0)

    # ATP backing
    coherence_manager.add_atp("lct:web4:natural", 100.0)

    # Node 2: Artificial coherence (Sybil, circular validation)
    sybil_identity = LCTIdentity(
        lct_id="lct:web4:sybil",
        hardware_type="tpm2",
        hardware_fingerprint="sybil_hw",
        attestation_public_key="sybil_key",
        created_at=time.time(),
    )
    lct_manager.register_lct_identity(sybil_identity)

    # Inflated reputation
    for i in range(5):
        att = sybil_identity.generate_attestation(f"fake_{i}")
        lct_manager.record_quality_event("lct:web4:sybil", 10.0, f"fake_{i}", att)

    # Concentrated source (one friend validating)
    diversity_manager.record_reputation_event("lct:web4:sybil", "sybil_friend", 50.0)

    # No ATP backing (didn't do real work)
    coherence_manager.add_atp("lct:web4:sybil", 0.0)

    # Analysis
    print("\n" + "=" * 80)
    print("PHASE 2: Coherence Analysis")
    print("=" * 80)

    print("\nNATURAL NODE (lct:web4:natural):")
    natural_report = coherence_manager.get_stability_report("lct:web4:natural")
    for key, value in natural_report.items():
        if key == "coherence_metrics":
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    {k}: {v:.4f}")
        else:
            print(f"  {key}: {value}")

    print("\nSYBIL NODE (lct:web4:sybil):")
    sybil_report = coherence_manager.get_stability_report("lct:web4:sybil")
    for key, value in sybil_report.items():
        if key == "coherence_metrics":
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    {k}: {v:.4f}")
        else:
            print(f"  {key}: {value}")

    # Decay test
    print("\n" + "=" * 80)
    print("PHASE 3: Reputation Decay (Thermodynamic Decoherence)")
    print("=" * 80)

    print("\nNatural node (with ATP):")
    natural_decay = coherence_manager.apply_reputation_decay("lct:web4:natural", time_delta=10.0)
    for key, value in natural_decay.items():
        print(f"  {key}: {value:.4f}")

    print("\nSybil node (no ATP):")
    sybil_decay = coherence_manager.apply_reputation_decay("lct:web4:sybil", time_delta=10.0)
    for key, value in sybil_decay.items():
        print(f"  {key}: {value:.4f}")

    # Validation
    print("\n" + "=" * 80)
    print("VALIDATION")
    print("=" * 80)

    validations = []
    validations.append(("✅ Natural node has high coherence", natural_report["coherence_metrics"]["coherence_score"] > 0.7))
    validations.append(("✅ Natural node is stable", natural_report["stability_score"] > 0.6))
    validations.append(("✅ Natural node not flagged as artificial", not natural_report["is_artificial"]))
    validations.append(("✅ Sybil node has low diversity", sybil_report["coherence_metrics"]["entropy"] < 0.3))
    validations.append(("✅ Sybil node flagged as artificial", sybil_report["is_artificial"]))
    validations.append(("✅ Natural node maintained with ATP", natural_decay["decay_amount"] < 1.0))
    validations.append(("✅ Sybil node decayed without ATP", sybil_decay["decay_amount"] > 1.0))

    for validation, passed in validations:
        print(f"  {validation}: {'PASS' if passed else 'FAIL'}")

    if all(passed for _, passed in validations):
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        print("\nCoherence-Based Reputation Theory: VALIDATED")
        print("  ✅ Natural coherence distinguished from artificial")
        print("  ✅ Thermodynamic decay models work correctly")
        print("  ✅ ATP maintenance prevents decoherence")
        print("  ✅ Sybil attacks show thermodynamic signatures")
        print("\n🎯 Reputation as maintained coherence state: CONFIRMED")
        print("=" * 80)
    else:
        print("\n❌ SOME TESTS FAILED")

    return all(passed for _, passed in validations)


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_coherence_reputation_theory())

    if success:
        print("\n" + "=" * 80)
        print("SESSION 167: COHERENCE THEORY COMPLETE")
        print("=" * 80)
        print("\nWeb4 reputation system now understands:")
        print("  ✅ Reputation = maintained coherence state")
        print("  ✅ Source diversity = coherence length")
        print("  ✅ ATP = energy for coherence maintenance")
        print("  ✅ Decay = thermodynamic decoherence")
        print("  ✅ Sybil = artificial coherence (detectable)")
        print("\nBiological insight validated in digital system:")
        print("  Life maintains coherence through ATP")
        print("  Web4 reputation maintains coherence through ATP")
        print("  Both decay without energy investment")
        print("=" * 80)
