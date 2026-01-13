"""
Session 176: Causality and Verification for Web4

Integrates Synchronism Session 254's causality framework into Web4,
modeling attestation verification as causal coherence transfer through
the network.

Key insight from Session 254:
Causality = Coherence Transfer

When attestation A causes verification B:
1. A has coherence pattern C_A
2. Pattern propagates through network
3. Arrives at B's node (respecting light cone)
4. B's coherence C_B incorporates A's pattern

Causal transfer equation:
T(A→B, t) = ∫ C_A(τ) × K(r, t-τ) dτ

Propagation kernel:
K(r, τ) = exp(-γr) × Θ(τ - r/c) × exp(-(τ - r/c)²/2σ²)

Key properties:
- Zero outside light cone (causality respected)
- Peaks at light cone boundary (information speed limit)
- Exponential decay with distance
- Gaussian spread (quantum uncertainty)

Based on:
- Synchronism Session 254: Causality from Coherence
- Session 169: Quantum Measurement for Attestation
- Session 174: Arrow of Time Temporal Dynamics
- Session 175: Agency and Autonomy
"""

import asyncio
import math
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional, Tuple, Callable
import numpy as np


class CausalRelation(Enum):
    """Causal relationship types."""
    CAUSAL = "causal"              # A in past light cone of B
    ACAUSAL = "acausal"            # Outside light cone
    SIMULTANEOUS = "simultaneous"   # At light cone boundary
    FUTURE = "future"               # In future light cone


@dataclass
class CausalEvent:
    """
    Event with spacetime coordinates and coherence.

    In Web4: Events are attestations, verifications, or reputation updates.
    """
    event_id: str
    timestamp: float  # When event occurred (seconds)
    location: np.ndarray  # Spatial coordinates (meters)
    coherence: float  # C value at event
    event_type: str  # attestation, verification, etc.


@dataclass
class CausalTransfer:
    """
    Result of coherence transfer from A to B.

    Quantifies causal influence.
    """
    source_event: CausalEvent
    target_event: CausalEvent
    transfer_amount: float  # How much coherence transferred
    causal_strength: float  # |∂C_B/∂C_A|
    relation: CausalRelation
    propagation_time: float  # Actual time taken
    light_cone_time: float  # Minimum time (r/c)


class CausalityFramework:
    """
    Causality as coherence transfer from Session 254.

    Key insight: Causality is not mysterious - it's coherence propagating
    through spacetime, constrained by light cone.
    """

    def __init__(
        self,
        speed_of_propagation: float = 3e8,  # m/s (light speed for physical)
        decay_coefficient: float = 1e-6,     # 1/m (network decay)
        temporal_spread: float = 0.1,        # seconds (uncertainty)
    ):
        """
        Initialize causality framework.

        Args:
            speed_of_propagation: c (information speed limit)
            decay_coefficient: γ (exponential decay with distance)
            temporal_spread: σ (Gaussian temporal spread)
        """
        self.c = speed_of_propagation
        self.gamma = decay_coefficient
        self.sigma = temporal_spread

    def propagation_kernel(
        self,
        spatial_distance: float,
        temporal_delay: float,
    ) -> float:
        """
        Calculate propagation kernel K(r, τ).

        K(r, τ) = exp(-γr) × Θ(τ - r/c) × exp(-(τ - r/c)²/2σ²)

        Args:
            spatial_distance: r (meters)
            temporal_delay: τ = t - t_source (seconds)

        Returns:
            Kernel value (0 if outside light cone)
        """
        # Light cone boundary
        light_cone_time = spatial_distance / self.c

        # Heaviside step: Zero outside light cone
        if temporal_delay < light_cone_time:
            return 0.0

        # Spatial decay
        spatial_factor = math.exp(-self.gamma * spatial_distance)

        # Temporal spread (Gaussian peaked at light cone)
        time_deviation = temporal_delay - light_cone_time
        temporal_factor = math.exp(-(time_deviation**2) / (2 * self.sigma**2))

        return spatial_factor * temporal_factor

    def causal_transfer(
        self,
        source: CausalEvent,
        target: CausalEvent,
    ) -> CausalTransfer:
        """
        Calculate causal transfer from source to target.

        T(A→B) = C_A × K(r, Δt)

        Args:
            source: Source event (cause)
            target: Target event (effect)

        Returns:
            CausalTransfer object
        """
        # Spacetime separation
        spatial_distance = np.linalg.norm(target.location - source.location)
        temporal_delay = target.timestamp - source.timestamp

        # Light cone time
        light_cone_time = spatial_distance / self.c

        # Classify causal relation
        if temporal_delay < 0:
            # Future
            relation = CausalRelation.FUTURE
        elif temporal_delay < light_cone_time - 1e-6:
            # Outside past light cone (spacelike)
            relation = CausalRelation.ACAUSAL
        elif temporal_delay >= light_cone_time - 1e-6:
            # In or on past light cone boundary (timelike/lightlike)
            # Both are causal - boundary has maximum transfer
            relation = CausalRelation.CAUSAL
        else:
            # Should never reach here
            relation = CausalRelation.SIMULTANEOUS

        # Propagation kernel
        kernel = self.propagation_kernel(spatial_distance, temporal_delay)

        # Transfer amount: How much coherence propagates
        transfer_amount = source.coherence * kernel

        # Causal strength: How strongly A affects B
        # Approximation: strength ∝ transfer
        causal_strength = kernel

        return CausalTransfer(
            source_event=source,
            target_event=target,
            transfer_amount=transfer_amount,
            causal_strength=causal_strength,
            relation=relation,
            propagation_time=temporal_delay,
            light_cone_time=light_cone_time,
        )

    def classify_causal_relation(
        self,
        spatial_distance: float,
        temporal_delay: float,
    ) -> CausalRelation:
        """
        Classify causal relationship based on spacetime separation.

        Args:
            spatial_distance: r (meters)
            temporal_delay: Δt (seconds)

        Returns:
            CausalRelation
        """
        light_cone_time = spatial_distance / self.c

        if temporal_delay < light_cone_time - 1e-9:
            return CausalRelation.ACAUSAL
        elif abs(temporal_delay - light_cone_time) < 1e-9:
            return CausalRelation.SIMULTANEOUS
        elif temporal_delay > 0:
            return CausalRelation.CAUSAL
        else:
            return CausalRelation.FUTURE


class AttestationCausality:
    """
    Models causal propagation of attestations through Web4 network.

    Key insight: Attestation A can only cause verification B if A is in
    B's past light cone.
    """

    def __init__(self):
        self.causality = CausalityFramework(
            speed_of_propagation=1e8,  # Network propagation ~1/3 light speed
            decay_coefficient=1e-7,    # Weak decay for digital networks
            temporal_spread=0.01,      # 10ms uncertainty
        )

    def attestation_influences_verification(
        self,
        attestation: CausalEvent,
        verification: CausalEvent,
    ) -> CausalTransfer:
        """
        Calculate if and how attestation causally influences verification.

        Args:
            attestation: Attestation event
            verification: Verification event

        Returns:
            CausalTransfer
        """
        return self.causality.causal_transfer(attestation, verification)

    def find_causal_ancestors(
        self,
        event: CausalEvent,
        all_events: List[CausalEvent],
    ) -> List[CausalTransfer]:
        """
        Find all events in past light cone (causal ancestors).

        Args:
            event: Target event
            all_events: All events in network

        Returns:
            List of causal transfers from ancestors
        """
        ancestors = []

        for candidate in all_events:
            if candidate.event_id == event.event_id:
                continue

            transfer = self.causality.causal_transfer(candidate, event)

            if transfer.relation == CausalRelation.CAUSAL:
                ancestors.append(transfer)

        # Sort by causal strength (strongest first)
        ancestors.sort(key=lambda t: t.causal_strength, reverse=True)

        return ancestors

    def causal_chain_strength(
        self,
        chain: List[CausalEvent],
    ) -> float:
        """
        Calculate total causal strength of event chain.

        Args:
            chain: Ordered list of events (cause → effect)

        Returns:
            Total causal strength (product of individual strengths)
        """
        if len(chain) < 2:
            return 0.0

        total_strength = 1.0

        for i in range(len(chain) - 1):
            transfer = self.causality.causal_transfer(chain[i], chain[i+1])
            total_strength *= transfer.causal_strength

        return total_strength


class VerificationCausality:
    """
    Models causal structure of verification process.

    Key insight: Verification outcome B is causally determined by
    all attestations in its past light cone.
    """

    def __init__(self):
        self.attestation_causality = AttestationCausality()

    def verify_with_causal_analysis(
        self,
        attestations: List[CausalEvent],
        verification_point: Tuple[float, np.ndarray],  # (time, location)
    ) -> Dict[str, any]:
        """
        Perform verification with causal analysis.

        Args:
            attestations: All attestation events
            verification_point: Where/when verification happens

        Returns:
            Dict with verification result and causal analysis
        """
        # Create verification event
        verification = CausalEvent(
            event_id="verification",
            timestamp=verification_point[0],
            location=verification_point[1],
            coherence=0.0,  # To be determined
            event_type="verification",
        )

        # Find causal ancestors
        causal_ancestors = self.attestation_causality.find_causal_ancestors(
            verification, attestations
        )

        # Calculate total causal influence
        total_transfer = sum(t.transfer_amount for t in causal_ancestors)

        # Verification coherence = sum of causal transfers
        verification.coherence = min(total_transfer, 1.0)

        # Identify dominant cause (strongest influence)
        dominant_cause = causal_ancestors[0] if causal_ancestors else None

        return {
            'verification_coherence': verification.coherence,
            'causal_ancestor_count': len(causal_ancestors),
            'total_causal_transfer': total_transfer,
            'dominant_cause': dominant_cause,
            'all_ancestors': causal_ancestors,
        }


class NetworkCausalStructure:
    """
    Analyzes causal structure of entire Web4 network.

    From Session 254: Network has intrinsic causal structure from
    coherence transfer patterns.
    """

    def __init__(self):
        self.causality = CausalityFramework()

    def build_causal_graph(
        self,
        events: List[CausalEvent],
    ) -> Dict[str, List[str]]:
        """
        Build causal graph from events.

        Args:
            events: All events in network

        Returns:
            Dict mapping event_id → list of causal ancestors
        """
        causal_graph = {}

        for event in events:
            ancestors = []

            for candidate in events:
                if candidate.event_id == event.event_id:
                    continue

                transfer = self.causality.causal_transfer(candidate, event)

                if transfer.relation == CausalRelation.CAUSAL:
                    ancestors.append(candidate.event_id)

            causal_graph[event.event_id] = ancestors

        return causal_graph

    def identify_causal_bottlenecks(
        self,
        causal_graph: Dict[str, List[str]],
    ) -> List[str]:
        """
        Identify events that are causal bottlenecks.

        Bottleneck = event that many other events depend on.

        Args:
            causal_graph: Causal dependency graph

        Returns:
            List of bottleneck event IDs
        """
        # Count how many events depend on each event
        dependency_count = {}

        for event_id, ancestors in causal_graph.items():
            for ancestor_id in ancestors:
                dependency_count[ancestor_id] = dependency_count.get(ancestor_id, 0) + 1

        # Sort by dependency count
        sorted_events = sorted(
            dependency_count.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Top 10% are bottlenecks
        threshold = len(sorted_events) // 10
        bottlenecks = [event_id for event_id, _ in sorted_events[:threshold]]

        return bottlenecks


# ============================================================================
# Test Suite
# ============================================================================

async def test_causality_verification_web4():
    """Test causality and verification framework for Web4."""

    print("=" * 80)
    print("SESSION 176: Causality and Verification for Web4 Test")
    print("=" * 80)
    print("Causality = Coherence Transfer")
    print("=" * 80)

    causality_framework = CausalityFramework()
    attestation_causality = AttestationCausality()
    verification_causality = VerificationCausality()
    network_structure = NetworkCausalStructure()

    # Test 1: Propagation Kernel
    print("\n" + "=" * 80)
    print("TEST 1: Propagation Kernel K(r, τ)")
    print("=" * 80)

    print("\nK(r, τ) = exp(-γr) × Θ(τ - r/c) × exp(-(τ - r/c)²/2σ²)")

    distance = 1000.0  # 1 km
    light_cone_time = distance / causality_framework.c

    print(f"\nDistance: {distance:.0f} m")
    print(f"Light cone time: {light_cone_time*1e6:.2f} μs")

    print("\nTemporal delay → Kernel value:")
    for delay_factor in [0.5, 0.9, 1.0, 1.1, 2.0]:
        delay = light_cone_time * delay_factor
        kernel = causality_framework.propagation_kernel(distance, delay)
        print(f"  τ = {delay*1e6:.2f} μs ({delay_factor:.1f}× light cone): K = {kernel:.6f}")

    # Test 2: Causal Relationships
    print("\n" + "=" * 80)
    print("TEST 2: Causal Relationship Classification")
    print("=" * 80)

    # Create test events
    event_A = CausalEvent(
        event_id="A",
        timestamp=0.0,
        location=np.array([0.0, 0.0, 0.0]),
        coherence=0.8,
        event_type="attestation",
    )

    test_scenarios = [
        ("Causal (A→B)", np.array([100.0, 0.0, 0.0]), 1e-5),     # Well after light cone
        ("Light cone boundary", np.array([100.0, 0.0, 0.0]), 100.0/3e8),  # Exactly at boundary
        ("Acausal (spacelike)", np.array([100.0, 0.0, 0.0]), 1e-7),  # Before light cone
        ("Future", np.array([100.0, 0.0, 0.0]), -1e-6),         # Negative time
    ]

    for desc, location, timestamp in test_scenarios:
        event_B = CausalEvent(
            event_id="B",
            timestamp=timestamp,
            location=location,
            coherence=0.5,
            event_type="verification",
        )

        transfer = causality_framework.causal_transfer(event_A, event_B)

        print(f"\n  {desc}:")
        print(f"    Relation: {transfer.relation.value}")
        print(f"    Transfer: {transfer.transfer_amount:.6f}")
        print(f"    Strength: {transfer.causal_strength:.6f}")

    # Test 3: Attestation Causality
    print("\n" + "=" * 80)
    print("TEST 3: Attestation Influences Verification")
    print("=" * 80)

    attestation = CausalEvent(
        event_id="attestation_1",
        timestamp=0.0,
        location=np.array([0.0, 0.0, 0.0]),
        coherence=0.9,
        event_type="attestation",
    )

    verification = CausalEvent(
        event_id="verification_1",
        timestamp=5e-6,  # 5 μs later (well after light cone time of 3μs)
        location=np.array([300.0, 0.0, 0.0]),  # 300m away
        coherence=0.0,  # To be determined
        event_type="verification",
    )

    transfer = attestation_causality.attestation_influences_verification(
        attestation, verification
    )

    print(f"\nAttestation at t=0, x=0")
    print(f"Verification at t={verification.timestamp*1e6:.1f} μs, x={verification.location[0]:.0f}m")
    print(f"\nLight cone time: {transfer.light_cone_time*1e6:.2f} μs")
    print(f"Actual time: {transfer.propagation_time*1e6:.2f} μs")
    print(f"Relation: {transfer.relation.value}")
    print(f"Causal transfer: {transfer.transfer_amount:.4f}")
    print(f"Causal strength: {transfer.causal_strength:.4f}")

    # Test 4: Causal Ancestors
    print("\n" + "=" * 80)
    print("TEST 4: Finding Causal Ancestors")
    print("=" * 80)

    # Create chain of events
    events = [
        CausalEvent("E0", 0.0, np.array([0.0, 0.0, 0.0]), 0.9, "attestation"),
        CausalEvent("E1", 1e-6, np.array([100.0, 0.0, 0.0]), 0.8, "attestation"),
        CausalEvent("E2", 2e-6, np.array([200.0, 0.0, 0.0]), 0.7, "attestation"),
        CausalEvent("E3", 3e-6, np.array([300.0, 0.0, 0.0]), 0.6, "verification"),
    ]

    target = events[3]
    ancestors = attestation_causality.find_causal_ancestors(target, events)

    print(f"\nTarget event: {target.event_id} at t={target.timestamp*1e6:.1f} μs")
    print(f"Found {len(ancestors)} causal ancestors:")
    for i, transfer in enumerate(ancestors, 1):
        print(f"\n  {i}. {transfer.source_event.event_id}:")
        print(f"     Strength: {transfer.causal_strength:.4f}")
        print(f"     Transfer: {transfer.transfer_amount:.4f}")

    # Test 5: Verification with Causal Analysis
    print("\n" + "=" * 80)
    print("TEST 5: Verification with Causal Analysis")
    print("=" * 80)

    attestations = events[:3]  # First 3 events
    verification_point = (3e-6, np.array([300.0, 0.0, 0.0]))

    result = verification_causality.verify_with_causal_analysis(
        attestations, verification_point
    )

    print(f"\nVerification at t={verification_point[0]*1e6:.1f} μs")
    print(f"Results:")
    print(f"  Coherence: {result['verification_coherence']:.4f}")
    print(f"  Causal ancestors: {result['causal_ancestor_count']}")
    print(f"  Total transfer: {result['total_causal_transfer']:.4f}")

    if result['dominant_cause']:
        dom = result['dominant_cause']
        print(f"  Dominant cause: {dom.source_event.event_id} (strength={dom.causal_strength:.4f})")

    # Test 6: Network Causal Structure
    print("\n" + "=" * 80)
    print("TEST 6: Network Causal Structure Analysis")
    print("=" * 80)

    causal_graph = network_structure.build_causal_graph(events)

    print("\nCausal dependency graph:")
    for event_id, ancestors in causal_graph.items():
        print(f"  {event_id}: depends on {ancestors}")

    bottlenecks = network_structure.identify_causal_bottlenecks(causal_graph)
    print(f"\nCausal bottlenecks: {bottlenecks}")

    # Validation
    print("\n" + "=" * 80)
    print("VALIDATION")
    print("=" * 80)

    validations = []
    validations.append(("✅ Kernel zero outside light cone", causality_framework.propagation_kernel(100, 1e-9) == 0.0))
    validations.append(("✅ Kernel positive inside light cone", causality_framework.propagation_kernel(100, 1e-5) > 0.0))
    validations.append(("✅ Causal relation classified correctly", transfer.relation == CausalRelation.CAUSAL))
    validations.append(("✅ Causal ancestors found", len(ancestors) > 0))
    validations.append(("✅ Verification coherence computed", result['verification_coherence'] > 0))
    validations.append(("✅ Causal graph built", len(causal_graph) == len(events)))

    for validation, passed in validations:
        print(f"  {validation}: {'PASS' if passed else 'FAIL'}")

    if all(passed for _, passed in validations):
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        print("\nCausality and Verification Framework: VALIDATED")
        print("  ✅ Causality = coherence transfer")
        print("  ✅ Light cone constraint enforced")
        print("  ✅ Propagation kernel functional")
        print("  ✅ Causal relationships classified")
        print("  ✅ Causal ancestors identified")
        print("  ✅ Network structure analyzed")
        print("\n🎯 Web4 now has causal verification framework")
        print("=" * 80)
    else:
        print("\n❌ SOME TESTS FAILED")

    print("\n" + "=" * 80)
    print("SESSION 176: CAUSALITY FRAMEWORK COMPLETE")
    print("=" * 80)
    print("\nWeb4 causal verification:")
    print("  ✅ Causality = coherence transfer through spacetime")
    print("  ✅ Light cone constraint (no FTL causation)")
    print("  ✅ Exponential decay with distance")
    print("  ✅ Causal ancestors determine verification")
    print("  ✅ Network causal structure analyzable")
    print("\nKey insights:")
    print("  • Verification outcome causally determined by past light cone")
    print("  • Attestations propagate as coherence patterns")
    print("  • Distance and time affect causal strength")
    print("  • Bottlenecks identifiable from causal graph")
    print("  • Same physics as spacetime causality")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_causality_verification_web4())
