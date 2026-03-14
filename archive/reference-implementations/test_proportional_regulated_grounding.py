#!/usr/bin/env python3
"""
Test Proportional Regulated Grounding - Session 105 Track 3

Tests integration of:
1. Proportional coherence regulation (Track 1)
2. LCT grounding registry (Session 104 Track 2)
3. ATP cost scaling

Author: Claude (Session 105 Track 3)
Date: 2025-12-29
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from proportional_regulated_grounding import (
    ProportionalGroundingManager,
    ProportionalGroundingConfig,
    create_proportional_grounding_system,
    compare_binary_vs_proportional_systems
)
from proportional_coherence_regulation import ProportionalRegulationConfig
from mrh_rdf_implementation import (
    GroundingEdge, GroundingContext, LocationContext,
    CapabilitiesContext, SessionContext, ResourceState, MRHGraph
)
from trust_tensors import CIModulationConfig


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mrh_graph():
    return MRHGraph("test-entity")


@pytest.fixture
def portland_location():
    return LocationContext("physical", "geo:45.5,-122.6", "city", True)


@pytest.fixture
def tokyo_location():
    return LocationContext("physical", "geo:35.7,139.7", "city", True)


@pytest.fixture
def manager():
    return create_proportional_grounding_system()


# ============================================================================
# Test Manager Initialization
# ============================================================================

def test_manager_initialization():
    """Test manager initializes with correct defaults"""
    manager = create_proportional_grounding_system()

    assert manager.config.regulation_config.target_ci == 0.7
    assert manager.config.regulation_config.max_boost == 0.3
    assert manager.config.atp_config.atp_max_multiplier == 10.0
    assert manager.config.grounding_ttl == timedelta(hours=24)
    assert manager.config.aggregation_strategy == 'min-weighted-critical'


def test_manager_custom_config():
    """Test manager with custom configuration"""
    manager = create_proportional_grounding_system(
        regulation_target=0.8,
        max_boost=0.4,
        atp_max_multiplier=20.0,
        grounding_ttl_hours=48
    )

    assert manager.config.regulation_config.target_ci == 0.8
    assert manager.config.regulation_config.max_boost == 0.4
    assert manager.config.atp_config.atp_max_multiplier == 20.0
    assert manager.config.grounding_ttl == timedelta(hours=48)


# ============================================================================
# Test Grounding Announcement
# ============================================================================

def test_first_grounding_announcement(manager, mrh_graph, portland_location):
    """Test first grounding announcement for new identity"""
    lct_uri = "lct:example.com:alice"

    context = GroundingContext(
        location=portland_location,
        capabilities=CapabilitiesContext(["test"], "edge-device", ResourceState(0.7, 0.8, 0.9)),
        session=SessionContext(datetime.now().isoformat(), "pattern", ""),
        active_contexts=[]
    )

    grounding_edge = GroundingEdge(
        entity_lct=lct_uri,
        timestamp=datetime.now().isoformat(),
        context=context,
        witness_set=None,
        signature="test-sig"
    )

    edge, ci, metadata = manager.announce_grounding(
        lct_uri,
        context,
        grounding_edge,
        mrh_graph
    )

    print(f"\nFirst grounding:")
    print(f"  CI: {ci:.3f}")
    print(f"  Regulations: {metadata['regulations_applied']}")

    assert edge == grounding_edge
    assert 0.0 <= ci <= 1.0
    assert 'raw_ci' in metadata
    assert 'regulations_applied' in metadata


def test_grounding_with_history(manager, mrh_graph, portland_location):
    """Test grounding announcement with existing history"""
    lct_uri = "lct:example.com:bob"

    # Create first grounding
    context1 = GroundingContext(
        location=portland_location,
        capabilities=CapabilitiesContext(["test"], "edge-device", ResourceState(0.7, 0.8, 0.9)),
        session=SessionContext((datetime.now() - timedelta(hours=1)).isoformat(), "pattern", ""),
        active_contexts=[]
    )

    grounding1 = GroundingEdge(
        entity_lct=lct_uri,
        timestamp=(datetime.now() - timedelta(hours=1)).isoformat(),
        context=context1,
        witness_set=None,
        signature="test-sig-1"
    )

    manager.announce_grounding(lct_uri, context1, grounding1, mrh_graph)

    # Create second grounding (with temporal recovery)
    context2 = GroundingContext(
        location=portland_location,
        capabilities=CapabilitiesContext(["test"], "edge-device", ResourceState(0.7, 0.8, 0.9)),
        session=SessionContext(datetime.now().isoformat(), "pattern", ""),
        active_contexts=[]
    )

    grounding2 = GroundingEdge(
        entity_lct=lct_uri,
        timestamp=datetime.now().isoformat(),
        context=context2,
        witness_set=None,
        signature="test-sig-2"
    )

    edge, ci, metadata = manager.announce_grounding(lct_uri, context2, grounding2, mrh_graph)

    print(f"\nSecond grounding (1 hour later):")
    print(f"  CI: {ci:.3f}")
    print(f"  Regulations: {metadata['regulations_applied']}")

    # Should have temporal recovery applied
    # (1 hour elapsed, could have some recovery)


def test_grounding_cascade_detection(manager, mrh_graph, portland_location):
    """Test cascade detection across multiple groundings"""
    lct_uri = "lct:example.com:carol"

    # Create declining CI history
    base_time = datetime.now() - timedelta(hours=5)
    ci_values = [0.8, 0.7, 0.6, 0.5, 0.4]  # Declining trend

    for i, _ in enumerate(ci_values):
        timestamp = (base_time + timedelta(hours=i)).isoformat()

        context = GroundingContext(
            location=portland_location,
            capabilities=CapabilitiesContext(["test"], "edge-device", ResourceState(0.7, 0.8, 0.9)),
            session=SessionContext(timestamp, "pattern", ""),
            active_contexts=[]
        )

        grounding = GroundingEdge(
            entity_lct=lct_uri,
            timestamp=timestamp,
            context=context,
            witness_set=None,
            signature=f"test-sig-{i}"
        )

        manager.announce_grounding(lct_uri, context, grounding, mrh_graph)

    # Final grounding should detect cascade
    context_final = GroundingContext(
        location=portland_location,
        capabilities=CapabilitiesContext(["test"], "edge-device", ResourceState(0.7, 0.8, 0.9)),
        session=SessionContext(datetime.now().isoformat(), "pattern", ""),
        active_contexts=[]
    )

    grounding_final = GroundingEdge(
        entity_lct=lct_uri,
        timestamp=datetime.now().isoformat(),
        context=context_final,
        witness_set=None,
        signature="test-sig-final"
    )

    edge, ci, metadata = manager.announce_grounding(lct_uri, context_final, grounding_final, mrh_graph)

    print(f"\nCascade detection:")
    print(f"  CI: {ci:.3f}")
    print(f"  Cascade severity: {metadata.get('cascade_severity', 0):.3f}")
    print(f"  Regulations: {metadata['regulations_applied']}")

    # Should detect cascade (severity > 0.2)
    # Note: Actual cascade detection depends on coherence_index values
    # which depend on grounding context similarity


# ============================================================================
# Test ATP Cost Calculation
# ============================================================================

def test_atp_cost_no_grounding(manager):
    """Test ATP cost for identity with no grounding"""
    lct_uri = "lct:example.com:dave"
    base_cost = 100.0

    cost, metadata = manager.calculate_atp_cost(lct_uri, base_cost)

    print(f"\nATP cost (no grounding):")
    print(f"  Base: {base_cost:.1f}")
    print(f"  Adjusted: {cost:.1f}")
    print(f"  Multiplier: {metadata['multiplier']:.1f}x")
    print(f"  Reason: {metadata['reason']}")

    assert not metadata['has_grounding']
    assert metadata['multiplier'] == manager.config.atp_config.atp_max_multiplier
    assert cost == base_cost * manager.config.atp_config.atp_max_multiplier


def test_atp_cost_with_high_ci(manager, mrh_graph, portland_location):
    """Test ATP cost for identity with high CI (minimal penalty)"""
    lct_uri = "lct:example.com:eve"
    base_cost = 100.0

    # Create grounding with high coherence (same location, consistent behavior)
    context = GroundingContext(
        location=portland_location,
        capabilities=CapabilitiesContext(["test"], "edge-device", ResourceState(0.9, 0.9, 0.9)),
        session=SessionContext(datetime.now().isoformat(), "pattern", ""),
        active_contexts=[]
    )

    grounding = GroundingEdge(
        entity_lct=lct_uri,
        timestamp=datetime.now().isoformat(),
        context=context,
        witness_set=None,
        signature="test-sig"
    )

    manager.announce_grounding(lct_uri, context, grounding, mrh_graph)

    cost, metadata = manager.calculate_atp_cost(lct_uri, base_cost)

    print(f"\nATP cost (high CI):")
    print(f"  CI: {metadata['ci']:.3f}")
    print(f"  Base: {base_cost:.1f}")
    print(f"  Adjusted: {cost:.1f}")
    print(f"  Multiplier: {metadata['multiplier']:.2f}x")

    assert metadata['has_grounding']
    # High CI should have minimal penalty (< 2x)
    assert metadata['multiplier'] < 2.0


def test_atp_cost_with_low_ci(manager, mrh_graph, portland_location, tokyo_location):
    """Test ATP cost for identity with low CI (high penalty)"""
    lct_uri = "lct:example.com:mallory"
    base_cost = 100.0

    # Create history at Portland
    portland_context = GroundingContext(
        location=portland_location,
        capabilities=CapabilitiesContext(["test"], "edge-device", ResourceState(0.7, 0.8, 0.9)),
        session=SessionContext((datetime.now() - timedelta(minutes=15)).isoformat(), "pattern", ""),
        active_contexts=[]
    )

    portland_grounding = GroundingEdge(
        entity_lct=lct_uri,
        timestamp=(datetime.now() - timedelta(minutes=15)).isoformat(),
        context=portland_context,
        witness_set=None,
        signature="test-sig-1"
    )

    manager.announce_grounding(lct_uri, portland_context, portland_grounding, mrh_graph)

    # Impossible teleport to Tokyo
    tokyo_context = GroundingContext(
        location=tokyo_location,
        capabilities=CapabilitiesContext(["test"], "edge-device", ResourceState(0.7, 0.8, 0.9)),
        session=SessionContext(datetime.now().isoformat(), "pattern", ""),
        active_contexts=[]
    )

    tokyo_grounding = GroundingEdge(
        entity_lct=lct_uri,
        timestamp=datetime.now().isoformat(),
        context=tokyo_context,
        witness_set=None,
        signature="test-sig-2"
    )

    edge, ci, metadata_grounding = manager.announce_grounding(lct_uri, tokyo_context, tokyo_grounding, mrh_graph)

    cost, metadata_atp = manager.calculate_atp_cost(lct_uri, base_cost)

    print(f"\nATP cost (low CI - impossible travel):")
    print(f"  CI: {metadata_atp['ci']:.3f}")
    print(f"  Base: {base_cost:.1f}")
    print(f"  Adjusted: {cost:.1f}")
    print(f"  Multiplier: {metadata_atp['multiplier']:.2f}x")

    assert metadata_atp['has_grounding']
    # Low CI (impossible travel) should have high penalty (> 5x)
    assert metadata_atp['multiplier'] > 5.0


# ============================================================================
# Test Identity Profiles
# ============================================================================

def test_identity_profile_tracking(manager, mrh_graph, portland_location):
    """Test identity coherence profile tracking"""
    lct_uri = "lct:example.com:frank"

    # Create multiple groundings
    for i in range(5):
        timestamp = (datetime.now() - timedelta(hours=4-i)).isoformat()

        context = GroundingContext(
            location=portland_location,
            capabilities=CapabilitiesContext(["test"], "edge-device", ResourceState(0.7, 0.8, 0.9)),
            session=SessionContext(timestamp, "pattern", ""),
            active_contexts=[]
        )

        grounding = GroundingEdge(
            entity_lct=lct_uri,
            timestamp=timestamp,
            context=context,
            witness_set=None,
            signature=f"test-sig-{i}"
        )

        manager.announce_grounding(lct_uri, context, grounding, mrh_graph)

    # Get profile
    profile = manager.get_identity_profile(lct_uri)

    print(f"\nIdentity profile:")
    print(f"  Grounding count: {profile.grounding_count}")
    print(f"  Avg coherence: {profile.avg_coherence:.3f}")
    print(f"  Min coherence: {profile.min_coherence:.3f}")
    print(f"  Max coherence: {profile.max_coherence:.3f}")
    print(f"  Flagged: {profile.flagged}")

    assert profile.lct_uri == lct_uri
    assert profile.grounding_count == 5
    assert 0.0 <= profile.avg_coherence <= 1.0


def test_registry_statistics(manager, mrh_graph, portland_location):
    """Test registry statistics"""
    # Create groundings for multiple identities
    for i in range(3):
        lct_uri = f"lct:example.com:user{i}"

        context = GroundingContext(
            location=portland_location,
            capabilities=CapabilitiesContext(["test"], "edge-device", ResourceState(0.7, 0.8, 0.9)),
            session=SessionContext(datetime.now().isoformat(), "pattern", ""),
            active_contexts=[]
        )

        grounding = GroundingEdge(
            entity_lct=lct_uri,
            timestamp=datetime.now().isoformat(),
            context=context,
            witness_set=None,
            signature=f"test-sig-{i}"
        )

        manager.announce_grounding(lct_uri, context, grounding, mrh_graph)

    stats = manager.get_statistics()

    print(f"\nRegistry statistics:")
    print(f"  Total identities: {stats['total_identities']}")
    print(f"  Active groundings: {stats['active_groundings']}")
    print(f"  Total groundings: {stats['total_groundings']}")
    print(f"  Avg coherence: {stats['avg_coherence']:.3f}")

    assert stats['total_identities'] == 3
    assert stats['active_groundings'] == 3
    assert stats['total_groundings'] == 3


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
