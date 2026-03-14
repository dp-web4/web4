#!/usr/bin/env python3
"""
Test Spatial Coherence Tightening - Session 104 Track 1

Validates that spatial coherence properly detects impossible travel and that
tightening the velocity profiles correctly penalizes rapid teleportation.

Test Scenarios:
1. Baseline: Verify current spatial_coherence() detects impossible travel
2. Velocity profiles: Test edge-device, mobile, server velocity limits
3. Impossible travel cases: Portland → Tokyo, NYC → Sydney
4. Legitimate travel: Slow movement, pre-announced travel
5. Witness validation: Destination witnesses increase coherence
6. Integration: Verify coherence_index() uses spatial coherence

Based on Session 103 Track 3 discovery that impossible travel wasn't heavily penalized.

Author: Claude (Session 104 Track 1)
Date: 2025-12-29
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from coherence import (
    spatial_coherence, geo_distance, coherence_index,
    EntityVelocityProfile, CoherenceWeights
)
from mrh_rdf_implementation import (
    GroundingEdge, GroundingContext, LocationContext,
    CapabilitiesContext, SessionContext, ResourceState, MRHGraph
)
from grounding_lifecycle import announce_grounding, GroundingTTLConfig


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mrh_graph():
    """MRH graph for testing"""
    return MRHGraph("test-entity")


@pytest.fixture
def portland_location():
    """Portland, OR location"""
    return LocationContext("physical", "geo:45.5,-122.6", "city", True)


@pytest.fixture
def seattle_location():
    """Seattle, WA location (300 km from Portland)"""
    return LocationContext("physical", "geo:47.6,-122.3", "city", True)


@pytest.fixture
def tokyo_location():
    """Tokyo, Japan location (~8500 km from Portland)"""
    return LocationContext("physical", "geo:35.7,139.7", "city", True)


@pytest.fixture
def sydney_location():
    """Sydney, Australia location (~12000 km from Portland)"""
    return LocationContext("physical", "geo:-33.9,151.2", "city", True)


# ============================================================================
# Test Geo Distance Calculation
# ============================================================================

def test_geo_distance_same_location(portland_location):
    """Test distance between same location is 0"""
    distance = geo_distance(portland_location, portland_location)
    assert distance == 0.0


def test_geo_distance_portland_seattle(portland_location, seattle_location):
    """Test Portland → Seattle distance (~235 km)"""
    distance = geo_distance(portland_location, seattle_location)
    # Haversine gives ~235 km
    assert 200 < distance < 270


def test_geo_distance_portland_tokyo(portland_location, tokyo_location):
    """Test Portland → Tokyo distance (~7800 km)"""
    distance = geo_distance(portland_location, tokyo_location)
    # Haversine gives ~7800 km
    assert 7500 < distance < 8100


def test_geo_distance_portland_sydney(portland_location, sydney_location):
    """Test Portland → Sydney distance (~12000 km)"""
    distance = geo_distance(portland_location, sydney_location)
    # Haversine should give ~11000-13000 km
    assert 11000 < distance < 13000


# ============================================================================
# Test Velocity Profiles
# ============================================================================

def test_velocity_profile_edge_device():
    """Test edge-device velocity profile (walking speed)"""
    profiles = EntityVelocityProfile.defaults()
    edge = profiles['edge-device']
    assert edge.max_velocity_km_h == 10.0  # Walking speed


def test_velocity_profile_mobile():
    """Test mobile velocity profile (car speed)"""
    profiles = EntityVelocityProfile.defaults()
    mobile = profiles['mobile']
    assert mobile.max_velocity_km_h == 100.0  # Car speed


def test_velocity_profile_server():
    """Test server velocity profile (stationary)"""
    profiles = EntityVelocityProfile.defaults()
    server = profiles['server']
    assert server.max_velocity_km_h == 0.0  # Stationary


# ============================================================================
# Test Spatial Coherence - Legitimate Travel
# ============================================================================

def test_spatial_coherence_no_history(portland_location):
    """Test spatial coherence with no history (neutral)"""
    coherence = spatial_coherence(
        portland_location,
        [],  # No history
        timedelta(days=7),
        "edge-device"
    )
    assert coherence == 0.5  # Neutral


def test_spatial_coherence_same_location(portland_location, mrh_graph):
    """Test spatial coherence staying in same location"""
    # Create grounding history at Portland
    history = []
    base_time = datetime.now() - timedelta(hours=1)

    for i in range(5):
        timestamp = (base_time + timedelta(minutes=i*10)).isoformat()
        context = GroundingContext(
            location=portland_location,
            capabilities=CapabilitiesContext(["test"], "edge-device", ResourceState(0.7, 0.8, 0.9)),
            session=SessionContext(timestamp, "pattern", ""),
            active_contexts=[]
        )
        edge = announce_grounding("test", context, mrh_graph, GroundingTTLConfig())
        edge.timestamp = timestamp
        history.append(edge)

    # Check coherence for staying at Portland
    coherence = spatial_coherence(
        portland_location,
        history,
        timedelta(days=7),
        "edge-device"
    )

    # Should be high (same location, no travel)
    assert coherence >= 0.9


def test_spatial_coherence_slow_movement(portland_location, seattle_location, mrh_graph):
    """Test spatial coherence for slow legitimate movement"""
    # Portland → Seattle: ~300 km in 5 hours = 60 km/h (car speed, within mobile limits)
    base_time = datetime.now() - timedelta(hours=5)

    # Grounding at Portland 5 hours ago
    portland_context = GroundingContext(
        location=portland_location,
        capabilities=CapabilitiesContext(["test"], "mobile", ResourceState(0.7, 0.8, 0.9)),
        session=SessionContext(base_time.isoformat(), "pattern", ""),
        active_contexts=[]
    )
    portland_edge = announce_grounding("test", portland_context, mrh_graph, GroundingTTLConfig())
    portland_edge.timestamp = base_time.isoformat()

    # Check coherence for arriving at Seattle
    coherence = spatial_coherence(
        seattle_location,
        [portland_edge],
        timedelta(days=7),
        "mobile"
    )

    # Should be high (60 km/h < 100 km/h max for mobile)
    assert coherence >= 0.7


# ============================================================================
# Test Spatial Coherence - Impossible Travel
# ============================================================================

def test_spatial_coherence_impossible_teleport_tokyo(portland_location, tokyo_location, mrh_graph):
    """Test spatial coherence for impossible teleport Portland → Tokyo"""
    # Portland → Tokyo: ~8500 km in 15 minutes = 34,000 km/h (IMPOSSIBLE)
    base_time = datetime.now() - timedelta(minutes=15)

    # Grounding at Portland 15 minutes ago
    portland_context = GroundingContext(
        location=portland_location,
        capabilities=CapabilitiesContext(["test"], "edge-device", ResourceState(0.7, 0.8, 0.9)),
        session=SessionContext(base_time.isoformat(), "pattern", ""),
        active_contexts=[]
    )
    portland_edge = announce_grounding("test", portland_context, mrh_graph, GroundingTTLConfig())
    portland_edge.timestamp = base_time.isoformat()

    # Check coherence for teleport to Tokyo
    coherence = spatial_coherence(
        tokyo_location,
        [portland_edge],
        timedelta(days=7),
        "edge-device"  # Max 10 km/h
    )

    # Should be VERY LOW (impossible travel)
    print(f"\nImpossible travel coherence: {coherence}")
    assert coherence <= 0.15  # Base 0.1 for impossible travel


def test_spatial_coherence_impossible_with_announcement(portland_location, tokyo_location, mrh_graph):
    """Test spatial coherence for impossible travel WITH pre-announcement"""
    # Same impossible travel but with announcement
    base_time = datetime.now() - timedelta(minutes=15)

    portland_context = GroundingContext(
        location=portland_location,
        capabilities=CapabilitiesContext(["test"], "edge-device", ResourceState(0.7, 0.8, 0.9)),
        session=SessionContext(base_time.isoformat(), "pattern", ""),
        active_contexts=[]
    )
    portland_edge = announce_grounding("test", portland_context, mrh_graph, GroundingTTLConfig())
    portland_edge.timestamp = base_time.isoformat()

    # With travel announcement
    coherence = spatial_coherence(
        tokyo_location,
        [portland_edge],
        timedelta(days=7),
        "edge-device",
        travel_announcements=["geo:35.7,139.7"]  # Announced Tokyo
    )

    # Should be higher than impossible alone (0.1 + 0.4 = 0.5)
    print(f"\nImpossible travel WITH announcement: {coherence}")
    assert 0.45 <= coherence <= 0.55


def test_spatial_coherence_impossible_with_witnesses(portland_location, tokyo_location, mrh_graph):
    """Test spatial coherence for impossible travel WITH witnesses"""
    # Same impossible travel but with witnesses at destination
    base_time = datetime.now() - timedelta(minutes=15)

    portland_context = GroundingContext(
        location=portland_location,
        capabilities=CapabilitiesContext(["test"], "edge-device", ResourceState(0.7, 0.8, 0.9)),
        session=SessionContext(base_time.isoformat(), "pattern", ""),
        active_contexts=[]
    )
    portland_edge = announce_grounding("test", portland_context, mrh_graph, GroundingTTLConfig())
    portland_edge.timestamp = base_time.isoformat()

    # With witnesses
    coherence = spatial_coherence(
        tokyo_location,
        [portland_edge],
        timedelta(days=7),
        "edge-device",
        witnesses_at_destination=["witness1", "witness2"]
    )

    # Should be higher than impossible alone (0.1 + 0.3 = 0.4)
    print(f"\nImpossible travel WITH witnesses: {coherence}")
    assert 0.35 <= coherence <= 0.45


def test_spatial_coherence_impossible_with_both(portland_location, tokyo_location, mrh_graph):
    """Test spatial coherence for impossible travel WITH announcement AND witnesses"""
    base_time = datetime.now() - timedelta(minutes=15)

    portland_context = GroundingContext(
        location=portland_location,
        capabilities=CapabilitiesContext(["test"], "edge-device", ResourceState(0.7, 0.8, 0.9)),
        session=SessionContext(base_time.isoformat(), "pattern", ""),
        active_contexts=[]
    )
    portland_edge = announce_grounding("test", portland_context, mrh_graph, GroundingTTLConfig())
    portland_edge.timestamp = base_time.isoformat()

    # With both announcement and witnesses
    coherence = spatial_coherence(
        tokyo_location,
        [portland_edge],
        timedelta(days=7),
        "edge-device",
        travel_announcements=["geo:35.7,139.7"],
        witnesses_at_destination=["witness1", "witness2"]
    )

    # Should be higher (0.1 + 0.4 + 0.3 = 0.8)
    print(f"\nImpossible travel WITH announcement AND witnesses: {coherence}")
    assert 0.75 <= coherence <= 0.85


# ============================================================================
# Test Integration with coherence_index()
# ============================================================================

def test_coherence_index_uses_spatial(portland_location, tokyo_location, mrh_graph):
    """Test that coherence_index() properly uses spatial coherence"""
    # Create history at Portland
    base_time = datetime.now() - timedelta(minutes=15)

    portland_context = GroundingContext(
        location=portland_location,
        capabilities=CapabilitiesContext(["test"], "edge-device", ResourceState(0.7, 0.8, 0.9)),
        session=SessionContext(base_time.isoformat(), "pattern", ""),
        active_contexts=[]
    )
    portland_edge = announce_grounding("test", portland_context, mrh_graph, GroundingTTLConfig())
    portland_edge.timestamp = base_time.isoformat()

    # Current context at Tokyo (impossible)
    tokyo_context = GroundingContext(
        location=tokyo_location,
        capabilities=CapabilitiesContext(["test"], "edge-device", ResourceState(0.7, 0.8, 0.9)),
        session=SessionContext(datetime.now().isoformat(), "pattern", ""),
        active_contexts=[]
    )

    # Calculate overall coherence
    ci = coherence_index(tokyo_context, [portland_edge], mrh_graph)

    # Should be LOW because spatial coherence is low
    print(f"\nOverall CI with impossible travel: {ci}")
    assert ci < 0.5  # Impossible travel tanks overall CI


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
