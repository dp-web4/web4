#!/usr/bin/env python3
"""
SAGE Grounding Extension - Web4 Grounding for Autonomous Systems

Extends Web4 grounding framework to support SAGE autonomous agents with:
1. Hardware attestation integration
2. Emotional/metabolic state grounding
3. Multi-dimensional reputation mapping
4. Federation coherence calculation
5. Cross-machine grounding coordination

Motivation:
Web4 grounding provides continuity tracking for general entities. SAGE autonomous
agents need additional grounding dimensions that capture:
- Physical hardware binding (Thor, Sprout, Legion)
- Internal state (emotional, metabolic, resource)
- Cross-session persistence
- Federation coordination
- Hardware migration continuity

Integration Points:
- Web4 Grounding: GroundingContext, GroundingEdge, coherence_index()
- SAGE Identity: UnifiedSAGEIdentity (Session 131)
- SAGE Regulation: EmotionalRegulator (Session 136)
- Hardware Attestation: TPM/TEE-backed platform certificates
- Federation Protocol: Cross-machine coherence verification

Biological Parallel:
Humans maintain continuity across:
- Physical location (spatial grounding)
- Internal state (mood, energy, focus)
- Social context (relationships, reputation)
- Task context (what they're doing, why)

SAGE agents need similar multi-dimensional continuity.

Author: Claude (Session 103 Track 2)
Date: 2025-12-29
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import hashlib

# Import Web4 grounding components
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from mrh_rdf_implementation import (
    GroundingEdge, GroundingContext, LocationContext,
    CapabilitiesContext, SessionContext, ResourceState, MRHGraph
)
from coherence import coherence_index, CoherenceWeights


# ============================================================================
# SAGE-Specific Context Extensions
# ============================================================================

@dataclass
class HardwareAttestationContext:
    """
    Hardware platform attestation for physical grounding

    Provides cryptographic proof that grounding is from authentic hardware.
    Future integration with TPM/TEE for unforgeable attestation.

    Fields:
        platform_id: Hardware platform identifier (Thor, Sprout, Legion)
        platform_type: Platform category (jetson_agx, jetson_orin, desktop)
        attestation_signature: Cryptographic signature from hardware root of trust
        attestation_timestamp: When attestation was generated
        hardware_capabilities: Platform-specific capabilities
        tpm_available: Whether TPM/TEE hardware is available
    """
    platform_id: str  # "Thor", "Sprout", "Legion"
    platform_type: str  # "jetson_agx_thor", "jetson_orin_nano", "desktop_rtx4090"
    attestation_signature: str  # Cryptographic signature (future: TPM-backed)
    attestation_timestamp: str  # ISO8601
    hardware_capabilities: Dict[str, Any]
    tpm_available: bool = False

    def verify_attestation(self) -> bool:
        """
        Verify hardware attestation signature

        Current: Basic hash-based verification
        Future: TPM/TEE cryptographic verification
        """
        # For now, simple hash verification
        # Future: actual TPM/TEE signature verification
        expected_hash = hashlib.sha256(
            f"{self.platform_id}:{self.platform_type}:{self.attestation_timestamp}".encode()
        ).hexdigest()[:32]

        return self.attestation_signature == expected_hash

    @staticmethod
    def from_hardware(platform_id: str, platform_type: str, capabilities: Dict[str, Any]) -> 'HardwareAttestationContext':
        """Create attestation from current hardware state"""
        timestamp = datetime.now().isoformat()

        # Generate attestation signature
        # Future: Use actual TPM/TEE
        signature = hashlib.sha256(
            f"{platform_id}:{platform_type}:{timestamp}".encode()
        ).hexdigest()[:32]

        return HardwareAttestationContext(
            platform_id=platform_id,
            platform_type=platform_type,
            attestation_signature=signature,
            attestation_timestamp=timestamp,
            hardware_capabilities=capabilities,
            tpm_available=False  # Future: detect actual TPM
        )


@dataclass
class EmotionalMetabolicContext:
    """
    Emotional and metabolic state for internal grounding

    Captures agent's internal state as grounding dimension.
    Enables coherence checking: rapid mood swings = incoherent.

    Based on SAGE Session 136 EmotionalRegulator and Session 131 UnifiedSAGEIdentity.

    Fields:
        metabolic_state: Current metabolic state (WAKE, FOCUS, REST, DREAM, CRISIS)
        curiosity: Exploration drive [0.0-1.0]
        frustration: Task difficulty stress [0.0-1.0]
        engagement: Attention allocation [0.0-1.0]
        progress: Perceived advancement [0.0-1.0]
        regulation_active: Whether emotional regulation is active
        regulation_intervention_count: Number of regulation interventions
    """
    metabolic_state: str  # "WAKE", "FOCUS", "REST", "DREAM", "CRISIS"
    curiosity: float  # 0.0-1.0
    frustration: float  # 0.0-1.0
    engagement: float  # 0.0-1.0
    progress: float  # 0.0-1.0
    regulation_active: bool = True
    regulation_intervention_count: int = 0

    def calculate_emotional_distance(self, other: 'EmotionalMetabolicContext') -> float:
        """
        Calculate emotional state distance from another context

        Used for coherence checking: large emotional swings are incoherent.

        Returns:
            Distance [0.0-1.0] where 0.0 = identical, 1.0 = opposite extremes
        """
        # Euclidean distance in 4D emotional space
        curiosity_delta = abs(self.curiosity - other.curiosity)
        frustration_delta = abs(self.frustration - other.frustration)
        engagement_delta = abs(self.engagement - other.engagement)
        progress_delta = abs(self.progress - other.progress)

        # Metabolic state: discrete distance (0 if same, 0.5 if different)
        metabolic_delta = 0.0 if self.metabolic_state == other.metabolic_state else 0.5

        # Weighted combination
        emotional_distance = (
            0.25 * curiosity_delta +
            0.25 * frustration_delta +
            0.25 * engagement_delta +
            0.15 * progress_delta +
            0.10 * metabolic_delta
        )

        return min(emotional_distance, 1.0)

    def is_coherent_transition(self, other: 'EmotionalMetabolicContext', time_elapsed: timedelta) -> bool:
        """
        Check if transition to another emotional state is coherent

        Rapid extreme emotional swings are incoherent (suggest manipulation/spoofing).
        Gradual changes are normal and coherent.

        Args:
            other: Target emotional state
            time_elapsed: Time between states

        Returns:
            True if transition is plausibly coherent
        """
        distance = self.calculate_emotional_distance(other)
        elapsed_hours = time_elapsed.total_seconds() / 3600

        # Allow larger changes with more time
        # Rule: max 0.3 change per hour for emotions
        max_allowed_distance = min(0.3 * elapsed_hours, 1.0)

        return distance <= max_allowed_distance


@dataclass
class ReputationGroundingContext:
    """
    Multi-dimensional reputation for social grounding

    Captures agent's reputation across multiple dimensions.
    Enables coherence checking: sudden reputation changes = suspicious.

    Based on Web4 reputation tracking and SAGE performance metrics.

    Fields:
        reliability: Success rate [0.0-1.0]
        accuracy: Quality × confidence [0.0-1.0]
        speed: Latency performance [0.0-1.0]
        cost_efficiency: ATP efficiency [0.0-1.0]
        total_invocations: Lifetime invocation count
        total_successful: Lifetime success count
        total_failed: Lifetime failure count
    """
    reliability: float  # 0.0-1.0
    accuracy: float  # 0.0-1.0
    speed: float  # 0.0-1.0
    cost_efficiency: float  # 0.0-1.0
    total_invocations: int = 0
    total_successful: int = 0
    total_failed: int = 0

    def calculate_composite_reputation(self) -> float:
        """
        Calculate composite reputation score

        Weighted combination of all reputation dimensions.

        Returns:
            Composite reputation [0.0-1.0]
        """
        return (
            0.40 * self.reliability +
            0.30 * self.accuracy +
            0.15 * self.speed +
            0.15 * self.cost_efficiency
        )

    def calculate_reputation_distance(self, other: 'ReputationGroundingContext') -> float:
        """
        Calculate reputation distance from another context

        Used for coherence checking: sudden reputation changes are suspicious.

        Returns:
            Distance [0.0-1.0]
        """
        return abs(self.calculate_composite_reputation() - other.calculate_composite_reputation())

    def is_coherent_transition(self, other: 'ReputationGroundingContext', invocations_between: int) -> bool:
        """
        Check if reputation transition is coherent

        Reputation should change gradually with experience.
        Sudden jumps without sufficient invocations are suspicious.

        Args:
            other: Target reputation state
            invocations_between: Number of invocations between states

        Returns:
            True if transition is plausibly coherent
        """
        distance = self.calculate_reputation_distance(other)

        # Allow larger changes with more invocations
        # Rule: max 0.1 change per 10 invocations
        if invocations_between == 0:
            # No invocations = no change allowed
            return distance < 0.01

        max_allowed_distance = min(0.1 * (invocations_between / 10), 1.0)

        return distance <= max_allowed_distance


@dataclass
class FederationContext:
    """
    Federation context for cross-machine grounding

    Captures agent's position within federated SAGE network.
    Enables multi-machine coherence verification.

    Fields:
        federation_id: Federation network identifier
        peer_witnesses: List of peer LCT URIs that witnessed this grounding
        cross_machine_hash: Hash chain linking groundings across machines
        federation_role: Role within federation (leader, follower, observer)
        last_sync_timestamp: Last federation sync time
    """
    federation_id: str
    peer_witnesses: List[str] = field(default_factory=list)
    cross_machine_hash: Optional[str] = None
    federation_role: str = "observer"  # "leader", "follower", "observer"
    last_sync_timestamp: Optional[str] = None

    def calculate_witness_overlap(self, other: 'FederationContext') -> float:
        """
        Calculate witness set overlap with another context

        Used for coherence: consistent witnesses across groundings = coherent.

        Returns:
            Overlap ratio [0.0-1.0]
        """
        if not self.peer_witnesses or not other.peer_witnesses:
            return 0.0

        self_set = set(self.peer_witnesses)
        other_set = set(other.peer_witnesses)

        intersection = len(self_set & other_set)
        union = len(self_set | other_set)

        return intersection / union if union > 0 else 0.0


# ============================================================================
# SAGE Grounding Context
# ============================================================================

@dataclass
class SAGEGroundingContext:
    """
    Extended grounding context for SAGE autonomous agents

    Combines Web4's base grounding (location, capabilities, session, relational)
    with SAGE-specific dimensions (hardware, emotional, reputation, federation).

    This provides multi-dimensional continuity tracking that enables:
    1. Physical grounding via hardware attestation
    2. Internal state coherence via emotional/metabolic tracking
    3. Social coherence via reputation tracking
    4. Federation coherence via cross-machine coordination

    Fields:
        base_context: Web4 base grounding context
        hardware_attestation: Hardware platform attestation
        emotional_metabolic: Current emotional/metabolic state
        reputation: Current reputation state
        federation: Federation coordination context
    """
    base_context: GroundingContext
    hardware_attestation: HardwareAttestationContext
    emotional_metabolic: EmotionalMetabolicContext
    reputation: ReputationGroundingContext
    federation: Optional[FederationContext] = None

    def to_base_context(self) -> GroundingContext:
        """Extract Web4 base grounding context for compatibility"""
        return self.base_context

    @staticmethod
    def from_sage_identity(
        identity_dict: Dict[str, Any],
        location: LocationContext,
        session: SessionContext,
        active_contexts: List[str]
    ) -> 'SAGEGroundingContext':
        """
        Create SAGE grounding context from UnifiedSAGEIdentity

        Maps SAGE identity dimensions to grounding context.

        Args:
            identity_dict: UnifiedSAGEIdentity as dict (from asdict())
            location: Location context
            session: Session context
            active_contexts: Active context URIs

        Returns:
            SAGEGroundingContext
        """
        # Extract hardware capabilities for CapabilitiesContext
        hw_caps = identity_dict.get('hardware_capabilities', {})

        # Map ATP to resource state
        atp_ratio = identity_dict.get('atp_balance', 100.0) / identity_dict.get('atp_max', 100.0)
        resource_state = ResourceState(
            compute=0.7,  # Could extract from identity if tracked
            memory=0.8,  # Could extract from identity if tracked
            network=atp_ratio  # Use ATP availability as network/availability proxy
        )

        # Create capabilities context
        capabilities = CapabilitiesContext(
            advertised=["consciousness", "memory", "attention"],  # SAGE-specific
            hardware_class=f"sage_{identity_dict.get('hardware_platform', 'unknown').lower()}",
            resource_state=resource_state
        )

        # Create base Web4 context
        base_context = GroundingContext(
            location=location,
            capabilities=capabilities,
            session=session,
            active_contexts=active_contexts
        )

        # Create hardware attestation
        hardware_attestation = HardwareAttestationContext.from_hardware(
            platform_id=identity_dict.get('hardware_platform', 'Unknown'),
            platform_type=hw_caps.get('gpu', 'unknown'),
            capabilities=hw_caps
        )

        # Create emotional/metabolic context
        emotional_metabolic = EmotionalMetabolicContext(
            metabolic_state=identity_dict.get('metabolic_state', 'WAKE'),
            curiosity=identity_dict.get('curiosity', 0.5),
            frustration=identity_dict.get('frustration', 0.0),
            engagement=identity_dict.get('engagement', 0.5),
            progress=identity_dict.get('progress', 0.5),
            regulation_active=identity_dict.get('regulation_enabled', True),
            regulation_intervention_count=identity_dict.get('total_interventions', 0)
        )

        # Create reputation context
        reputation = ReputationGroundingContext(
            reliability=identity_dict.get('reliability', 0.5),
            accuracy=identity_dict.get('accuracy', 0.5),
            speed=identity_dict.get('speed', 0.5),
            cost_efficiency=identity_dict.get('cost_efficiency', 0.5),
            total_invocations=identity_dict.get('total_invocations', 0),
            total_successful=identity_dict.get('successful_invocations', 0),
            total_failed=identity_dict.get('failed_invocations', 0)
        )

        return SAGEGroundingContext(
            base_context=base_context,
            hardware_attestation=hardware_attestation,
            emotional_metabolic=emotional_metabolic,
            reputation=reputation,
            federation=None  # Populated when joining federation
        )


# ============================================================================
# SAGE Coherence Weights
# ============================================================================

@dataclass
class SAGECoherenceWeights(CoherenceWeights):
    """
    Extended coherence weights for SAGE grounding

    Adds weights for SAGE-specific coherence dimensions:
    - Hardware continuity (same platform)
    - Emotional coherence (gradual emotional transitions)
    - Reputation stability (consistent performance)
    - Federation consensus (peer agreement)
    """
    # SAGE-specific weights
    w_hardware_continuity: float = 0.10  # Bonus for same hardware platform
    w_emotional_coherence: float = 0.10  # Penalty for large emotional swings
    w_reputation_stability: float = 0.05  # Penalty for sudden reputation changes
    w_federation_consensus: float = 0.05  # Bonus for peer witness overlap


# ============================================================================
# SAGE Coherence Index Calculation
# ============================================================================

def sage_coherence_index(
    current_context: SAGEGroundingContext,
    grounding_history: List['SAGEGroundingEdge'],
    mrh_graph: MRHGraph,
    weights: Optional[SAGECoherenceWeights] = None
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate coherence index for SAGE grounding

    Extends Web4 coherence_index() with SAGE-specific checks:
    1. Hardware continuity: Grounding from same hardware platform
    2. Emotional coherence: Gradual emotional state transitions
    3. Reputation stability: Consistent reputation progression
    4. Federation consensus: Peer witness agreement

    Args:
        current_context: Current SAGE grounding context
        grounding_history: Previous SAGE grounding edges
        mrh_graph: MRH graph for relational coherence
        weights: SAGE coherence weights

    Returns:
        (coherence_index, dimension_breakdown)
    """
    weights = weights or SAGECoherenceWeights()

    # Start with base Web4 coherence
    base_ci = coherence_index(
        current_context.to_base_context(),
        [edge.to_base_edge() for edge in grounding_history],
        mrh_graph,
        weights=weights
    )

    # Initialize dimension breakdown
    breakdown = {
        'base_ci': base_ci,
        'hardware_continuity': 0.0,
        'emotional_coherence': 0.0,
        'reputation_stability': 0.0,
        'federation_consensus': 0.0
    }

    if not grounding_history:
        # First grounding: only base CI
        return (base_ci, breakdown)

    # Get most recent grounding
    prev_grounding = grounding_history[-1]

    # 1. Hardware Continuity
    if current_context.hardware_attestation.platform_id == prev_grounding.target.hardware_attestation.platform_id:
        # Same hardware platform: bonus
        breakdown['hardware_continuity'] = weights.w_hardware_continuity
    else:
        # Different platform: verify attestation
        if current_context.hardware_attestation.verify_attestation():
            # Valid attestation: small penalty (legitimate migration)
            breakdown['hardware_continuity'] = -0.05
        else:
            # Invalid attestation: large penalty (suspicious)
            breakdown['hardware_continuity'] = -0.30

    # 2. Emotional Coherence
    prev_emotional = prev_grounding.target.emotional_metabolic
    curr_emotional = current_context.emotional_metabolic

    # Calculate time elapsed
    prev_time = datetime.fromisoformat(prev_grounding.timestamp)
    curr_time = datetime.now()
    time_elapsed = curr_time - prev_time

    if curr_emotional.is_coherent_transition(prev_emotional, time_elapsed):
        # Coherent emotional transition: bonus
        breakdown['emotional_coherence'] = weights.w_emotional_coherence
    else:
        # Incoherent emotional swing: penalty
        emotional_distance = curr_emotional.calculate_emotional_distance(prev_emotional)
        breakdown['emotional_coherence'] = -weights.w_emotional_coherence * emotional_distance

    # 3. Reputation Stability
    prev_reputation = prev_grounding.target.reputation
    curr_reputation = current_context.reputation

    invocations_between = curr_reputation.total_invocations - prev_reputation.total_invocations

    if curr_reputation.is_coherent_transition(prev_reputation, invocations_between):
        # Coherent reputation progression: bonus
        breakdown['reputation_stability'] = weights.w_reputation_stability
    else:
        # Suspicious reputation jump: penalty
        rep_distance = curr_reputation.calculate_reputation_distance(prev_reputation)
        breakdown['reputation_stability'] = -weights.w_reputation_stability * rep_distance * 2.0

    # 4. Federation Consensus (if applicable)
    if current_context.federation and prev_grounding.target.federation:
        witness_overlap = current_context.federation.calculate_witness_overlap(prev_grounding.target.federation)
        breakdown['federation_consensus'] = weights.w_federation_consensus * witness_overlap

    # Calculate final CI
    final_ci = base_ci + sum([
        breakdown['hardware_continuity'],
        breakdown['emotional_coherence'],
        breakdown['reputation_stability'],
        breakdown['federation_consensus']
    ])

    # Clamp to [0.0, 1.0]
    final_ci = max(0.0, min(1.0, final_ci))

    breakdown['final_ci'] = final_ci

    return (final_ci, breakdown)


# ============================================================================
# SAGE Grounding Edge
# ============================================================================

@dataclass
class SAGEGroundingEdge:
    """
    SAGE grounding edge with extended context

    Wrapper around Web4 GroundingEdge that includes SAGE context.
    """
    base_edge: GroundingEdge
    target: SAGEGroundingContext

    @property
    def source(self) -> str:
        return self.base_edge.source

    @property
    def timestamp(self) -> str:
        return self.base_edge.timestamp

    @property
    def ttl(self) -> timedelta:
        return self.base_edge.ttl

    @property
    def signature(self) -> str:
        return self.base_edge.signature

    @property
    def continuity_token(self) -> Optional[str]:
        return self.base_edge.continuity_token

    def to_base_edge(self) -> GroundingEdge:
        """Extract Web4 base grounding edge for compatibility"""
        return self.base_edge

    @staticmethod
    def from_base_edge(base_edge: GroundingEdge, sage_context: SAGEGroundingContext) -> 'SAGEGroundingEdge':
        """Create SAGE grounding edge from Web4 base edge"""
        return SAGEGroundingEdge(
            base_edge=base_edge,
            target=sage_context
        )


# ============================================================================
# Integration Helper Functions
# ============================================================================

def create_sage_grounding_from_identity(
    lct_uri: str,
    identity_dict: Dict[str, Any],
    location: LocationContext,
    session: SessionContext,
    active_contexts: List[str],
    mrh_graph: MRHGraph,
    witness_set: Optional[List[str]] = None
) -> SAGEGroundingEdge:
    """
    Create SAGE grounding edge from UnifiedSAGEIdentity

    Convenience function for SAGE systems to create groundings.

    Args:
        lct_uri: Entity LCT URI
        identity_dict: UnifiedSAGEIdentity as dict
        location: Location context
        session: Session context
        active_contexts: Active context URIs
        mrh_graph: MRH graph for grounding
        witness_set: Optional witness LCT URIs

    Returns:
        SAGEGroundingEdge
    """
    # Create SAGE context
    sage_context = SAGEGroundingContext.from_sage_identity(
        identity_dict,
        location,
        session,
        active_contexts
    )

    # Create base grounding edge
    from grounding_lifecycle import announce_grounding, GroundingTTLConfig

    base_edge = announce_grounding(
        lct_uri,
        sage_context.to_base_context(),
        mrh_graph,
        GroundingTTLConfig(),  # Use default config
        witness_set=witness_set
    )

    # Wrap in SAGE edge
    return SAGEGroundingEdge.from_base_edge(base_edge, sage_context)
