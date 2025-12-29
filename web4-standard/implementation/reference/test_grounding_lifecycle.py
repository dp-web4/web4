#!/usr/bin/env python3
"""
Tests for Grounding Lifecycle Management (Phase 4)

Tests:
1. Grounding announcement and continuity tokens
2. Heartbeat with context changes
3. Expiration detection and handling
4. Witness verification challenges
5. GroundingManager integration
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from grounding_lifecycle import (
    GroundingTTLConfig, ContextChangeThresholds, GroundingStatus,
    generate_continuity_token, validate_continuity_chain,
    announce_grounding, detect_context_change, grounding_heartbeat,
    check_grounding_status, on_grounding_expired, verify_grounding,
    GroundingManager, GroundingChallenge
)

from mrh_rdf_implementation import (
    GroundingEdge, GroundingContext, LocationContext,
    CapabilitiesContext, SessionContext, ResourceState, MRHGraph
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def config():
    """Default TTL configuration"""
    return GroundingTTLConfig()


@pytest.fixture
def thresholds():
    """Default context change thresholds"""
    return ContextChangeThresholds()


@pytest.fixture
def mrh_graph():
    """Empty MRH graph"""
    return MRHGraph("test-entity-001")


@pytest.fixture
def context_portland():
    """Grounding context in Portland"""
    return GroundingContext(
        location=LocationContext(
            type="physical",
            value="geo:45.5231,-122.6765",
            precision="city",
            verifiable=True
        ),
        capabilities=CapabilitiesContext(
            advertised=["vision", "text", "code"],
            hardware_class="edge-device",
            resource_state=ResourceState(compute=0.7, memory=0.8, network=0.9)
        ),
        session=SessionContext(
            started=datetime.now().isoformat(),
            activity_pattern="pattern-001",
            continuity_token=""
        ),
        active_contexts=["lct:user-alice", "lct:project-web4"]
    )


@pytest.fixture
def context_seattle():
    """Grounding context in Seattle (different location)"""
    return GroundingContext(
        location=LocationContext(
            type="physical",
            value="geo:47.6062,-122.3321",
            precision="city",
            verifiable=True
        ),
        capabilities=CapabilitiesContext(
            advertised=["vision", "text", "code"],
            hardware_class="edge-device",
            resource_state=ResourceState(compute=0.7, memory=0.8, network=0.9)
        ),
        session=SessionContext(
            started=datetime.now().isoformat(),
            activity_pattern="pattern-002",
            continuity_token=""
        ),
        active_contexts=["lct:user-alice", "lct:project-web4"]
    )


# ============================================================================
# Test Continuity Tokens
# ============================================================================

def test_continuity_token_generation():
    """Test continuity token generation"""
    context = GroundingContext(
        location=LocationContext("physical", "geo:45.5,-122.6", "city", True),
        capabilities=CapabilitiesContext(["text"], "edge-device", ResourceState(0.5, 0.5, 0.5)),
        session=SessionContext(datetime.now().isoformat(), "pattern-hash", ""),
        active_contexts=[]
    )

    timestamp = "2025-12-29T10:00:00"

    # First grounding (no previous)
    token1 = generate_continuity_token(None, context, timestamp)
    assert len(token1) == 64  # SHA256 hex = 64 chars
    assert isinstance(token1, str)

    # Second grounding (with previous)
    grounding1 = GroundingEdge(
        source="lct:entity-001",
        target=context,
        timestamp=timestamp,
        ttl=timedelta(minutes=15),
        signature="sig1"
    )
    grounding1.continuity_token = token1

    token2 = generate_continuity_token(grounding1, context, "2025-12-29T10:15:00")
    assert len(token2) == 64
    assert token2 != token1  # Different because timestamp changed


def test_continuity_chain_validation():
    """Test continuity chain validation"""
    context = GroundingContext(
        location=LocationContext("physical", "geo:45.5,-122.6", "city", True),
        capabilities=CapabilitiesContext(["text"], "edge-device", ResourceState(0.5, 0.5, 0.5)),
        session=SessionContext(datetime.now().isoformat(), "pattern-hash", ""),
        active_contexts=[]
    )

    # Create valid chain
    history = []
    for i in range(3):
        timestamp = f"2025-12-29T10:{i*15:02d}:00"
        prev = history[-1] if history else None

        token = generate_continuity_token(prev, context, timestamp)

        grounding = GroundingEdge(
            source="lct:entity-001",
            target=context,
            timestamp=timestamp,
            ttl=timedelta(minutes=15),
            signature=f"sig{i}"
        )
        grounding.continuity_token = token

        history.append(grounding)

    # Valid chain
    is_valid, error = validate_continuity_chain(history)
    assert is_valid
    assert error is None

    # Break the chain by tampering with a token
    history[1].continuity_token = "0" * 64
    is_valid, error = validate_continuity_chain(history)
    assert not is_valid
    assert "Continuity token mismatch" in error


def test_continuity_chain_timestamp_ordering():
    """Test that continuity chain validates timestamp ordering"""
    context = GroundingContext(
        location=LocationContext("physical", "geo:45.5,-122.6", "city", True),
        capabilities=CapabilitiesContext(["text"], "edge-device", ResourceState(0.5, 0.5, 0.5)),
        session=SessionContext(datetime.now().isoformat(), "pattern-hash", ""),
        active_contexts=[]
    )

    # Create chain with out-of-order timestamps
    history = []
    timestamps = ["2025-12-29T10:00:00", "2025-12-29T09:50:00"]  # Second is earlier!

    for i, timestamp in enumerate(timestamps):
        prev = history[-1] if history else None
        token = generate_continuity_token(prev, context, timestamp)

        grounding = GroundingEdge(
            source="lct:entity-001",
            target=context,
            timestamp=timestamp,
            ttl=timedelta(minutes=15),
            signature=f"sig{i}"
        )
        grounding.continuity_token = token
        history.append(grounding)

    is_valid, error = validate_continuity_chain(history)
    assert not is_valid
    assert "Timestamp out of order" in error


# ============================================================================
# Test Grounding Announcement
# ============================================================================

def test_announce_grounding(mrh_graph, context_portland, config):
    """Test grounding announcement"""
    edge = announce_grounding(
        "lct:entity-001",
        context_portland,
        mrh_graph,
        config
    )

    assert edge.source == "lct:entity-001"
    assert edge.target == context_portland
    assert edge.ttl == config.ttl_edge_device  # Default for edge-device
    assert len(edge.signature) == 64  # SHA256
    assert hasattr(edge, 'continuity_token')
    assert len(edge.continuity_token) == 64


def test_announce_grounding_with_witnesses(mrh_graph, context_portland, config):
    """Test grounding announcement with witnesses"""
    witnesses = ["lct:witness-001", "lct:witness-002"]

    edge = announce_grounding(
        "lct:entity-001",
        context_portland,
        mrh_graph,
        config,
        witness_set=witnesses
    )

    assert edge.witness_set == witnesses


def test_announce_grounding_ttl_by_hardware_class(mrh_graph, config):
    """Test that TTL varies by hardware class"""
    # Server (1 hour)
    context_server = GroundingContext(
        location=LocationContext("logical", "datacenter-us-west", "datacenter", False),
        capabilities=CapabilitiesContext(["compute"], "server", ResourceState(1.0, 1.0, 1.0)),
        session=SessionContext(datetime.now().isoformat(), "pattern-hash", ""),
        active_contexts=[]
    )

    edge_server = announce_grounding("lct:server-001", context_server, mrh_graph, config)
    assert edge_server.ttl == timedelta(hours=1)

    # Mobile (5 minutes)
    context_mobile = GroundingContext(
        location=LocationContext("physical", "geo:45.5,-122.6", "city", True),
        capabilities=CapabilitiesContext(["text"], "mobile", ResourceState(0.3, 0.3, 0.3)),
        session=SessionContext(datetime.now().isoformat(), "pattern-hash-mobile", ""),
        active_contexts=[]
    )

    edge_mobile = announce_grounding("lct:mobile-001", context_mobile, mrh_graph, config)
    assert edge_mobile.ttl == timedelta(minutes=5)


# ============================================================================
# Test Context Change Detection
# ============================================================================

def test_detect_no_context_change(context_portland, thresholds):
    """Test that identical contexts show no change"""
    has_change, changes = detect_context_change(
        context_portland,
        context_portland,
        thresholds
    )

    assert not has_change
    assert len(changes) == 0


def test_detect_location_change(context_portland, context_seattle, thresholds):
    """Test location change detection"""
    has_change, changes = detect_context_change(
        context_seattle,
        context_portland,
        thresholds
    )

    assert has_change
    assert any("location" in c for c in changes)


def test_detect_capability_change(context_portland, thresholds):
    """Test capability change detection"""
    context_more_caps = GroundingContext(
        location=context_portland.location,
        capabilities=CapabilitiesContext(
            advertised=["vision", "text", "code", "audio", "video"],  # Added 2 capabilities
            hardware_class="edge-device",
            resource_state=ResourceState(0.7, 0.8, 0.9)
        ),
        session=context_portland.session,
        active_contexts=context_portland.active_contexts
    )

    has_change, changes = detect_context_change(
        context_more_caps,
        context_portland,
        thresholds
    )

    assert has_change
    assert any("capabilities" in c for c in changes)


def test_detect_hardware_class_change(context_portland, thresholds):
    """Test hardware class change detection"""
    context_upgraded = GroundingContext(
        location=context_portland.location,
        capabilities=CapabilitiesContext(
            advertised=context_portland.capabilities.advertised,
            hardware_class="server",  # Upgraded from edge-device
            resource_state=ResourceState(1.0, 1.0, 1.0)
        ),
        session=context_portland.session,
        active_contexts=context_portland.active_contexts
    )

    has_change, changes = detect_context_change(
        context_upgraded,
        context_portland,
        thresholds
    )

    assert has_change
    assert any("hardware_class" in c for c in changes)


# ============================================================================
# Test Grounding Heartbeat
# ============================================================================

def test_heartbeat_no_change(mrh_graph, context_portland, config, thresholds):
    """Test heartbeat with no context change (simple refresh)"""
    # Initial announcement
    initial = announce_grounding("lct:entity-001", context_portland, mrh_graph, config)

    # Heartbeat with same context
    refreshed, action = grounding_heartbeat(
        "lct:entity-001",
        context_portland,
        initial,
        mrh_graph,
        config,
        thresholds
    )

    assert "refreshed" in action
    assert refreshed.source == initial.source
    assert refreshed.target.location.value == initial.target.location.value


def test_heartbeat_with_location_change(mrh_graph, context_portland, context_seattle, config, thresholds):
    """Test heartbeat with significant location change (re-announcement)"""
    # Initial announcement
    initial = announce_grounding("lct:entity-001", context_portland, mrh_graph, config)

    # Heartbeat with changed location
    updated, action = grounding_heartbeat(
        "lct:entity-001",
        context_seattle,
        initial,
        mrh_graph,
        config,
        thresholds
    )

    assert "re-announced" in action
    assert "location" in action
    assert updated.target.location.value == context_seattle.location.value


# ============================================================================
# Test Grounding Status and Expiration
# ============================================================================

def test_check_grounding_status_active(mrh_graph, context_portland, config):
    """Test status check for active grounding"""
    edge = announce_grounding("lct:entity-001", context_portland, mrh_graph, config)

    status, remaining = check_grounding_status(edge, config)

    assert status == GroundingStatus.ACTIVE
    assert remaining is not None
    assert remaining > timedelta(0)


def test_check_grounding_status_expired():
    """Test status check for expired grounding"""
    config = GroundingTTLConfig()

    # Create grounding that expired 1 hour ago
    past_time = (datetime.now() - timedelta(hours=1)).isoformat()

    context = GroundingContext(
        location=LocationContext("physical", "geo:45.5,-122.6", "city", True),
        capabilities=CapabilitiesContext(["text"], "edge-device", ResourceState(0.5, 0.5, 0.5)),
        session=SessionContext(past_time, "pattern-hash", ""),
        active_contexts=[]
    )

    edge = GroundingEdge(
        source="lct:entity-001",
        target=context,
        timestamp=past_time,
        ttl=timedelta(minutes=15),  # Expired long ago
        signature="sig"
    )

    status, overdue = check_grounding_status(edge, config)

    assert status == GroundingStatus.EXPIRED
    assert overdue is not None
    assert overdue > timedelta(0)


def test_on_grounding_expired_ci_degradation(mrh_graph, config):
    """Test CI degradation calculation on expiration"""
    past_time = (datetime.now() - timedelta(hours=2)).isoformat()

    context = GroundingContext(
        location=LocationContext("physical", "geo:45.5,-122.6", "city", True),
        capabilities=CapabilitiesContext(["text"], "edge-device", ResourceState(0.5, 0.5, 0.5)),
        session=SessionContext(past_time, "pattern-hash", ""),
        active_contexts=[]
    )

    edge = GroundingEdge(
        source="lct:entity-001",
        target=context,
        timestamp=past_time,
        ttl=timedelta(minutes=15),
        signature="sig"
    )

    metadata = on_grounding_expired("lct:entity-001", edge, mrh_graph, config)

    assert metadata['entity_lct'] == "lct:entity-001"
    assert metadata['status'] == GroundingStatus.EXPIRED.value
    assert 'ci_multiplier' in metadata
    assert 0 < metadata['ci_multiplier'] < 1.0  # Degraded but not zero
    assert metadata['overdue_seconds'] > 0


# ============================================================================
# Test Witness Verification
# ============================================================================

def test_grounding_challenge_creation():
    """Test creating verification challenges"""
    challenge = GroundingChallenge.create(
        "lct:entity-001",
        "lct:witness-001",
        "liveness"
    )

    assert challenge.entity_lct == "lct:entity-001"
    assert challenge.challenger_lct == "lct:witness-001"
    assert challenge.challenge_type == "liveness"
    assert len(challenge.nonce) == 64  # 32 bytes hex
    assert len(challenge.challenge_id) == 32  # 16 bytes hex


def test_verify_grounding_liveness(mrh_graph, context_portland, config):
    """Test liveness verification"""
    # Recent grounding (should pass liveness check)
    edge = announce_grounding("lct:entity-001", context_portland, mrh_graph, config)

    is_verified, error = verify_grounding(edge, "lct:witness-001", "liveness")

    assert is_verified
    assert error is None


def test_verify_grounding_liveness_stale():
    """Test liveness verification fails for stale grounding"""
    config = GroundingTTLConfig()

    # Old grounding (20 minutes ago)
    old_time = (datetime.now() - timedelta(minutes=20)).isoformat()

    context = GroundingContext(
        location=LocationContext("physical", "geo:45.5,-122.6", "city", True),
        capabilities=CapabilitiesContext(["text"], "edge-device", ResourceState(0.5, 0.5, 0.5)),
        session=SessionContext(old_time, "pattern-hash", ""),
        active_contexts=[]
    )

    edge = GroundingEdge(
        source="lct:entity-001",
        target=context,
        timestamp=old_time,
        ttl=timedelta(minutes=15),
        signature="sig"
    )

    is_verified, error = verify_grounding(edge, "lct:witness-001", "liveness")

    assert not is_verified
    assert "too old" in error


def test_verify_grounding_location_not_verifiable():
    """Test location verification fails for non-verifiable location"""
    context = GroundingContext(
        location=LocationContext(
            type="logical",
            value="somewhere",
            precision="unknown",
            verifiable=False  # Not verifiable
        ),
        capabilities=CapabilitiesContext(["text"], "edge-device", ResourceState(0.5, 0.5, 0.5)),
        session=SessionContext(datetime.now().isoformat(), "pattern-hash", ""),
        active_contexts=[]
    )

    edge = GroundingEdge(
        source="lct:entity-001",
        target=context,
        timestamp=datetime.now().isoformat(),
        ttl=timedelta(minutes=15),
        signature="sig"
    )

    is_verified, error = verify_grounding(edge, "lct:witness-001", "location")

    assert not is_verified
    assert "not verifiable" in error


# ============================================================================
# Test GroundingManager
# ============================================================================

def test_grounding_manager_initial_announcement(mrh_graph, context_portland):
    """Test GroundingManager initial announcement"""
    manager = GroundingManager("lct:entity-001", mrh_graph)

    grounding, action = manager.heartbeat(context_portland)

    assert "initial" in action
    assert manager.current_grounding is not None
    assert len(manager.grounding_history) == 1


def test_grounding_manager_heartbeat_sequence(mrh_graph, context_portland):
    """Test sequence of heartbeats"""
    manager = GroundingManager("lct:entity-001", mrh_graph)

    # Initial
    g1, a1 = manager.heartbeat(context_portland)
    assert "initial" in a1

    # Refresh (no change)
    g2, a2 = manager.heartbeat(context_portland)
    assert "refreshed" in a2

    # Another refresh
    g3, a3 = manager.heartbeat(context_portland)
    assert "refreshed" in a3

    # All groundings should be chained
    is_valid, error = manager.validate_continuity()
    assert is_valid


def test_grounding_manager_context_change(mrh_graph, context_portland, context_seattle):
    """Test manager handles context changes"""
    manager = GroundingManager("lct:entity-001", mrh_graph)

    # Initial in Portland
    g1, a1 = manager.heartbeat(context_portland)

    # Move to Seattle
    g2, a2 = manager.heartbeat(context_seattle)
    assert "re-announced" in a2
    assert "location" in a2

    # Should have 2 entries in history (initial + re-announce)
    assert len(manager.grounding_history) == 2


def test_grounding_manager_status_check(mrh_graph, context_portland):
    """Test manager status checking"""
    manager = GroundingManager("lct:entity-001", mrh_graph)

    # Before any grounding
    status, _ = manager.check_status()
    assert status == GroundingStatus.EXPIRED

    # After announcement
    manager.heartbeat(context_portland)
    status, remaining = manager.check_status()
    assert status == GroundingStatus.ACTIVE
    assert remaining > timedelta(0)


def test_grounding_manager_continuity_validation(mrh_graph, context_portland):
    """Test continuity chain validation via manager"""
    manager = GroundingManager("lct:entity-001", mrh_graph)

    # Create chain of groundings
    for i in range(5):
        manager.heartbeat(context_portland)

    # Validate chain
    is_valid, error = manager.validate_continuity()
    assert is_valid
    assert error is None


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    # Run with: python3 test_grounding_lifecycle.py
    pytest.main([__file__, "-v", "--tb=short"])
