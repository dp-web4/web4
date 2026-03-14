#!/usr/bin/env python3
"""
Tests for SAGE Grounding Extension

Tests SAGE-specific grounding context and coherence calculation:
1. Hardware attestation context
2. Emotional/metabolic state grounding
3. Reputation grounding
4. Federation context
5. SAGE coherence index calculation
6. Integration with UnifiedSAGEIdentity
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from sage_grounding_extension import (
    HardwareAttestationContext, EmotionalMetabolicContext,
    ReputationGroundingContext, FederationContext,
    SAGEGroundingContext, SAGECoherenceWeights,
    sage_coherence_index, SAGEGroundingEdge,
    create_sage_grounding_from_identity
)
from mrh_rdf_implementation import (
    GroundingEdge, GroundingContext, LocationContext,
    CapabilitiesContext, SessionContext, ResourceState, MRHGraph
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mrh_graph():
    """MRH graph for testing"""
    return MRHGraph("sage:thor@local")


@pytest.fixture
def thor_capabilities():
    """Thor hardware capabilities"""
    return {
        "compute_power": "high",
        "memory_gb": 64,
        "gpu": "NVIDIA Thor (1792 CUDA cores)",
        "role": "development",
        "max_atp": 150.0,
        "recovery_rate": 1.5
    }


@pytest.fixture
def sage_identity_dict(thor_capabilities):
    """Sample UnifiedSAGEIdentity as dict"""
    return {
        'lct_id': {'namespace': 'sage', 'name': 'thor', 'network': 'local', 'full_id': 'lct://sage:thor@local'},
        'hardware_platform': 'Thor',
        'hardware_capabilities': thor_capabilities,
        'session_id': 'test123',
        'metabolic_state': 'WAKE',
        'curiosity': 0.7,
        'frustration': 0.2,
        'engagement': 0.8,
        'progress': 0.6,
        'regulation_enabled': True,
        'total_interventions': 5,
        'reliability': 0.85,
        'accuracy': 0.80,
        'speed': 0.75,
        'cost_efficiency': 0.70,
        'total_invocations': 100,
        'successful_invocations': 85,
        'failed_invocations': 15,
        'atp_balance': 120.0,
        'atp_max': 150.0
    }


@pytest.fixture
def base_location():
    """Base location context"""
    return LocationContext("physical", "geo:45.5231,-122.6765", "city", True)


@pytest.fixture
def base_session():
    """Base session context"""
    return SessionContext(datetime.now().isoformat(), "pattern-001", "")


# ============================================================================
# Test Hardware Attestation
# ============================================================================

def test_hardware_attestation_creation(thor_capabilities):
    """Test hardware attestation context creation"""
    attestation = HardwareAttestationContext.from_hardware(
        "Thor",
        "jetson_agx_thor",
        thor_capabilities
    )

    assert attestation.platform_id == "Thor"
    assert attestation.platform_type == "jetson_agx_thor"
    assert attestation.hardware_capabilities == thor_capabilities
    assert len(attestation.attestation_signature) == 32  # SHA256 hex truncated


def test_hardware_attestation_verification(thor_capabilities):
    """Test attestation signature verification"""
    attestation = HardwareAttestationContext.from_hardware(
        "Thor",
        "jetson_agx_thor",
        thor_capabilities
    )

    # Should verify successfully
    assert attestation.verify_attestation() == True

    # Modify signature - should fail
    attestation.attestation_signature = "invalid_signature"
    assert attestation.verify_attestation() == False


# ============================================================================
# Test Emotional/Metabolic Context
# ============================================================================

def test_emotional_context_distance():
    """Test emotional state distance calculation"""
    state1 = EmotionalMetabolicContext(
        metabolic_state="WAKE",
        curiosity=0.7,
        frustration=0.2,
        engagement=0.8,
        progress=0.6
    )

    state2 = EmotionalMetabolicContext(
        metabolic_state="WAKE",
        curiosity=0.8,  # +0.1
        frustration=0.3,  # +0.1
        engagement=0.7,  # -0.1
        progress=0.5  # -0.1
    )

    distance = state1.calculate_emotional_distance(state2)

    # Should be small (all changes ≤ 0.1)
    assert 0.0 < distance < 0.15


def test_emotional_coherent_transition():
    """Test coherent emotional transition detection"""
    state1 = EmotionalMetabolicContext(
        metabolic_state="WAKE",
        curiosity=0.5,
        frustration=0.3,
        engagement=0.6,
        progress=0.5
    )

    # Small change over 1 hour: coherent
    state2_coherent = EmotionalMetabolicContext(
        metabolic_state="WAKE",
        curiosity=0.6,  # +0.1
        frustration=0.4,  # +0.1
        engagement=0.5,  # -0.1
        progress=0.4  # -0.1
    )

    assert state1.is_coherent_transition(state2_coherent, timedelta(hours=1)) == True

    # Large change over 5 minutes: incoherent
    state2_incoherent = EmotionalMetabolicContext(
        metabolic_state="CRISIS",
        curiosity=0.1,  # -0.4
        frustration=0.9,  # +0.6
        engagement=0.2,  # -0.4
        progress=0.1  # -0.4
    )

    assert state1.is_coherent_transition(state2_incoherent, timedelta(minutes=5)) == False


def test_emotional_metabolic_state_change():
    """Test metabolic state contributes to distance"""
    state1 = EmotionalMetabolicContext(
        metabolic_state="WAKE",
        curiosity=0.5,
        frustration=0.3,
        engagement=0.6,
        progress=0.5
    )

    state2 = EmotionalMetabolicContext(
        metabolic_state="DREAM",  # Different state
        curiosity=0.5,  # Same
        frustration=0.3,  # Same
        engagement=0.6,  # Same
        progress=0.5  # Same
    )

    distance = state1.calculate_emotional_distance(state2)

    # Should have distance due to metabolic state change
    assert distance > 0.0


# ============================================================================
# Test Reputation Context
# ============================================================================

def test_reputation_composite_score():
    """Test composite reputation calculation"""
    reputation = ReputationGroundingContext(
        reliability=0.9,
        accuracy=0.8,
        speed=0.7,
        cost_efficiency=0.6
    )

    composite = reputation.calculate_composite_reputation()

    # Should be weighted average
    expected = 0.40 * 0.9 + 0.30 * 0.8 + 0.15 * 0.7 + 0.15 * 0.6
    assert abs(composite - expected) < 0.01


def test_reputation_coherent_transition():
    """Test coherent reputation transition"""
    rep1 = ReputationGroundingContext(
        reliability=0.80,
        accuracy=0.75,
        speed=0.70,
        cost_efficiency=0.65,
        total_invocations=100
    )

    # Small change with 20 invocations: coherent
    rep2_coherent = ReputationGroundingContext(
        reliability=0.82,  # +0.02
        accuracy=0.76,  # +0.01
        speed=0.71,  # +0.01
        cost_efficiency=0.66,  # +0.01
        total_invocations=120
    )

    assert rep1.is_coherent_transition(rep2_coherent, 20) == True

    # Large change with 5 invocations: incoherent
    rep2_incoherent = ReputationGroundingContext(
        reliability=0.95,  # +0.15 (too large)
        accuracy=0.90,  # +0.15
        speed=0.85,  # +0.15
        cost_efficiency=0.80,  # +0.15
        total_invocations=105
    )

    assert rep1.is_coherent_transition(rep2_incoherent, 5) == False


def test_reputation_no_change_without_invocations():
    """Test that reputation changes require invocations"""
    rep1 = ReputationGroundingContext(
        reliability=0.80,
        accuracy=0.75,
        speed=0.70,
        cost_efficiency=0.65,
        total_invocations=100
    )

    # Changed reputation with 0 invocations: incoherent
    rep2 = ReputationGroundingContext(
        reliability=0.85,  # Changed
        accuracy=0.80,  # Changed
        speed=0.75,  # Changed
        cost_efficiency=0.70,  # Changed
        total_invocations=100  # Same
    )

    assert rep1.is_coherent_transition(rep2, 0) == False


# ============================================================================
# Test Federation Context
# ============================================================================

def test_federation_witness_overlap():
    """Test witness set overlap calculation"""
    fed1 = FederationContext(
        federation_id="sage-federation",
        peer_witnesses=["sage:sprout@local", "sage:legion@local", "sage:thor@local"]
    )

    fed2 = FederationContext(
        federation_id="sage-federation",
        peer_witnesses=["sage:sprout@local", "sage:thor@local", "sage:new@local"]
    )

    overlap = fed1.calculate_witness_overlap(fed2)

    # 2 common / 4 total = 0.5
    assert abs(overlap - 0.5) < 0.01


def test_federation_no_overlap():
    """Test witness overlap with no common witnesses"""
    fed1 = FederationContext(
        federation_id="sage-federation",
        peer_witnesses=["sage:a@local", "sage:b@local"]
    )

    fed2 = FederationContext(
        federation_id="sage-federation",
        peer_witnesses=["sage:c@local", "sage:d@local"]
    )

    overlap = fed1.calculate_witness_overlap(fed2)
    assert overlap == 0.0


# ============================================================================
# Test SAGE Grounding Context
# ============================================================================

def test_sage_context_from_identity(sage_identity_dict, base_location, base_session):
    """Test creating SAGE context from identity"""
    sage_context = SAGEGroundingContext.from_sage_identity(
        sage_identity_dict,
        base_location,
        base_session,
        []
    )

    # Check hardware attestation
    assert sage_context.hardware_attestation.platform_id == "Thor"
    assert sage_context.hardware_attestation.verify_attestation() == True

    # Check emotional state
    assert sage_context.emotional_metabolic.curiosity == 0.7
    assert sage_context.emotional_metabolic.frustration == 0.2
    assert sage_context.emotional_metabolic.metabolic_state == "WAKE"

    # Check reputation
    assert sage_context.reputation.reliability == 0.85
    assert sage_context.reputation.total_invocations == 100

    # Check base context
    assert sage_context.base_context.location == base_location
    assert sage_context.base_context.session == base_session


def test_sage_context_to_base_context(sage_identity_dict, base_location, base_session):
    """Test extracting base context from SAGE context"""
    sage_context = SAGEGroundingContext.from_sage_identity(
        sage_identity_dict,
        base_location,
        base_session,
        []
    )

    base_context = sage_context.to_base_context()

    assert isinstance(base_context, GroundingContext)
    assert base_context.location == base_location
    assert base_context.session == base_session


# ============================================================================
# Test SAGE Coherence Index
# ============================================================================

def test_sage_coherence_high_continuity(mrh_graph, sage_identity_dict, base_location, base_session):
    """Test SAGE coherence with high continuity (same platform, stable emotional state)"""
    # Create first grounding
    context1 = SAGEGroundingContext.from_sage_identity(
        sage_identity_dict,
        base_location,
        base_session,
        []
    )

    from grounding_lifecycle import announce_grounding, GroundingTTLConfig
    base_edge1 = announce_grounding("sage:thor@local", context1.to_base_context(), mrh_graph, GroundingTTLConfig())
    sage_edge1 = SAGEGroundingEdge.from_base_edge(base_edge1, context1)

    # Create second grounding - same platform, similar emotional state
    identity2 = sage_identity_dict.copy()
    identity2['curiosity'] = 0.72  # Small change
    identity2['frustration'] = 0.21  # Small change
    identity2['total_invocations'] = 110  # +10 invocations
    identity2['successful_invocations'] = 93  # +8 successes

    context2 = SAGEGroundingContext.from_sage_identity(
        identity2,
        base_location,
        base_session,
        []
    )

    # Calculate coherence
    ci, breakdown = sage_coherence_index(context2, [sage_edge1], mrh_graph)

    # Should be high (same hardware, similar emotional state, coherent reputation)
    assert ci > 0.7
    assert breakdown['hardware_continuity'] > 0  # Same platform bonus
    assert breakdown['emotional_coherence'] >= -0.01  # Coherent or near-zero (fast test execution)


def test_sage_coherence_platform_migration(mrh_graph, sage_identity_dict, base_location, base_session):
    """Test SAGE coherence with platform migration"""
    # Create first grounding on Thor
    context1 = SAGEGroundingContext.from_sage_identity(
        sage_identity_dict,
        base_location,
        base_session,
        []
    )

    from grounding_lifecycle import announce_grounding, GroundingTTLConfig
    base_edge1 = announce_grounding("sage:thor@local", context1.to_base_context(), mrh_graph, GroundingTTLConfig())
    sage_edge1 = SAGEGroundingEdge.from_base_edge(base_edge1, context1)

    # Create second grounding on Sprout (migration)
    identity2 = sage_identity_dict.copy()
    identity2['hardware_platform'] = 'Sprout'
    identity2['hardware_capabilities'] = {
        "compute_power": "medium",
        "memory_gb": 8,
        "gpu": "NVIDIA Orin Nano"
    }

    context2 = SAGEGroundingContext.from_sage_identity(
        identity2,
        base_location,
        base_session,
        []
    )

    # Calculate coherence
    ci, breakdown = sage_coherence_index(context2, [sage_edge1], mrh_graph)

    # Should have penalty for platform change (but valid attestation)
    assert breakdown['hardware_continuity'] < 0  # Migration penalty
    assert breakdown['hardware_continuity'] > -0.1  # But not severe (valid attestation)


def test_sage_coherence_emotional_swing(mrh_graph, sage_identity_dict, base_location, base_session):
    """Test SAGE coherence with incoherent emotional swing"""
    # Create first grounding
    context1 = SAGEGroundingContext.from_sage_identity(
        sage_identity_dict,
        base_location,
        base_session,
        []
    )

    from grounding_lifecycle import announce_grounding, GroundingTTLConfig
    base_edge1 = announce_grounding("sage:thor@local", context1.to_base_context(), mrh_graph, GroundingTTLConfig())
    sage_edge1 = SAGEGroundingEdge.from_base_edge(base_edge1, context1)

    # Create second grounding with extreme emotional swing (suspicious)
    identity2 = sage_identity_dict.copy()
    identity2['curiosity'] = 0.1  # Was 0.7, now 0.1 (-0.6 swing)
    identity2['frustration'] = 0.95  # Was 0.2, now 0.95 (+0.75 swing)
    identity2['engagement'] = 0.2  # Was 0.8, now 0.2 (-0.6 swing)
    identity2['metabolic_state'] = 'CRISIS'  # Was WAKE

    context2 = SAGEGroundingContext.from_sage_identity(
        identity2,
        base_location,
        base_session,
        []
    )

    # Calculate coherence
    ci, breakdown = sage_coherence_index(context2, [sage_edge1], mrh_graph)

    # Should have penalty for incoherent emotional transition
    assert breakdown['emotional_coherence'] < 0  # Penalty for rapid swing


def test_sage_coherence_reputation_jump(mrh_graph, sage_identity_dict, base_location, base_session):
    """Test SAGE coherence with suspicious reputation jump"""
    # Create first grounding
    context1 = SAGEGroundingContext.from_sage_identity(
        sage_identity_dict,
        base_location,
        base_session,
        []
    )

    from grounding_lifecycle import announce_grounding, GroundingTTLConfig
    base_edge1 = announce_grounding("sage:thor@local", context1.to_base_context(), mrh_graph, GroundingTTLConfig())
    sage_edge1 = SAGEGroundingEdge.from_base_edge(base_edge1, context1)

    # Create second grounding with suspicious reputation jump (no invocations)
    identity2 = sage_identity_dict.copy()
    identity2['reliability'] = 0.95  # Was 0.85, now 0.95 (+0.10)
    identity2['accuracy'] = 0.95  # Was 0.80, now 0.95 (+0.15)
    identity2['total_invocations'] = 100  # Same (no new invocations!)

    context2 = SAGEGroundingContext.from_sage_identity(
        identity2,
        base_location,
        base_session,
        []
    )

    # Calculate coherence
    ci, breakdown = sage_coherence_index(context2, [sage_edge1], mrh_graph)

    # Should have penalty for reputation change without invocations
    assert breakdown['reputation_stability'] < 0  # Penalty


# ============================================================================
# Test Integration
# ============================================================================

def test_create_sage_grounding_from_identity(mrh_graph, sage_identity_dict, base_location, base_session):
    """Test end-to-end SAGE grounding creation"""
    sage_edge = create_sage_grounding_from_identity(
        "sage:thor@local",
        sage_identity_dict,
        base_location,
        base_session,
        [],
        mrh_graph
    )

    assert isinstance(sage_edge, SAGEGroundingEdge)
    assert sage_edge.source == "sage:thor@local"
    assert sage_edge.target.hardware_attestation.platform_id == "Thor"
    assert sage_edge.target.emotional_metabolic.curiosity == 0.7
    assert sage_edge.target.reputation.reliability == 0.85


def test_sage_grounding_edge_compatibility(mrh_graph, sage_identity_dict, base_location, base_session):
    """Test SAGE grounding edge compatibility with Web4 base"""
    sage_edge = create_sage_grounding_from_identity(
        "sage:thor@local",
        sage_identity_dict,
        base_location,
        base_session,
        [],
        mrh_graph
    )

    # Should be able to extract base edge
    base_edge = sage_edge.to_base_edge()
    assert isinstance(base_edge, GroundingEdge)
    assert base_edge.source == "sage:thor@local"

    # Should be able to extract base context
    base_context = sage_edge.target.to_base_context()
    assert isinstance(base_context, GroundingContext)


# ============================================================================
# Test Edge Cases
# ============================================================================

def test_first_sage_grounding_coherence(mrh_graph, sage_identity_dict, base_location, base_session):
    """Test coherence calculation for first grounding (no history)"""
    context = SAGEGroundingContext.from_sage_identity(
        sage_identity_dict,
        base_location,
        base_session,
        []
    )

    # Calculate coherence with empty history
    ci, breakdown = sage_coherence_index(context, [], mrh_graph)

    # Should return base CI only
    assert 'base_ci' in breakdown
    assert ci == breakdown['base_ci']


def test_federation_context_coherence(mrh_graph, sage_identity_dict, base_location, base_session):
    """Test federation witness overlap affects coherence"""
    # Create first grounding with federation context
    context1 = SAGEGroundingContext.from_sage_identity(
        sage_identity_dict,
        base_location,
        base_session,
        []
    )
    context1.federation = FederationContext(
        federation_id="sage-federation",
        peer_witnesses=["sage:sprout@local", "sage:legion@local"]
    )

    from grounding_lifecycle import announce_grounding, GroundingTTLConfig
    base_edge1 = announce_grounding("sage:thor@local", context1.to_base_context(), mrh_graph, GroundingTTLConfig())
    sage_edge1 = SAGEGroundingEdge.from_base_edge(base_edge1, context1)

    # Create second grounding with overlapping witnesses
    context2 = SAGEGroundingContext.from_sage_identity(
        sage_identity_dict,
        base_location,
        base_session,
        []
    )
    context2.federation = FederationContext(
        federation_id="sage-federation",
        peer_witnesses=["sage:sprout@local", "sage:new@local"]  # 1 common
    )

    # Calculate coherence
    ci, breakdown = sage_coherence_index(context2, [sage_edge1], mrh_graph)

    # Should have federation consensus contribution
    assert 'federation_consensus' in breakdown
    assert breakdown['federation_consensus'] > 0  # Some witness overlap


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
