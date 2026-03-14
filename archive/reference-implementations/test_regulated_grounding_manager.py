#!/usr/bin/env python3
"""
Tests for Regulated Grounding Manager

Tests integration of coherence regulation into grounding lifecycle:
1. CI tracking and history maintenance
2. Regulation application in announce/heartbeat
3. ATP cost calculation with regulation
4. Cascade prevention in extended scenarios
5. Comparison of regulated vs unregulated
"""

import pytest
from datetime import datetime, timedelta
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from regulated_grounding_manager import (
    RegulatedGroundingManager, simulate_grounding_lifecycle,
    compare_regulated_vs_unregulated
)
from mrh_rdf_implementation import (
    GroundingEdge, GroundingContext, LocationContext,
    CapabilitiesContext, SessionContext, ResourceState, MRHGraph
)
from coherence_regulation import CoherenceRegulationConfig


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mrh_graph():
    """MRH graph"""
    return MRHGraph("test-entity-001")


@pytest.fixture
def context_portland():
    """Grounding context in Portland"""
    return GroundingContext(
        location=LocationContext("physical", "geo:45.5231,-122.6765", "city", True),
        capabilities=CapabilitiesContext(["text"], "edge-device", ResourceState(0.7, 0.8, 0.9)),
        session=SessionContext(datetime.now().isoformat(), "pattern-001", ""),
        active_contexts=[]
    )


def create_context_at_location(location: str, timestamp: Optional[datetime] = None) -> GroundingContext:
    """Helper to create context at specific location"""
    ts = timestamp or datetime.now()
    return GroundingContext(
        location=LocationContext("physical", location, "city", True),
        capabilities=CapabilitiesContext(["text"], "edge-device", ResourceState(0.7, 0.8, 0.9)),
        session=SessionContext(ts.isoformat(), "pattern", ""),
        active_contexts=[]
    )


# ============================================================================
# Test Basic Integration
# ============================================================================

def test_regulated_manager_initialization(mrh_graph):
    """Test RegulatedGroundingManager initialization"""
    manager = RegulatedGroundingManager("lct:test", mrh_graph)

    assert manager.entity_lct == "lct:test"
    assert manager.enable_regulation == True
    assert len(manager.ci_history) == 0
    assert len(manager.regulation_metadata_history) == 0


def test_announce_with_ci_tracking(mrh_graph, context_portland):
    """Test that announce tracks CI"""
    manager = RegulatedGroundingManager("lct:test", mrh_graph)

    grounding, ci, metadata = manager.announce(context_portland)

    assert grounding is not None
    assert isinstance(ci, float)
    assert 0.0 <= ci <= 1.0
    assert len(manager.ci_history) == 1
    assert manager.ci_history[0][0] == ci
    assert 'raw_ci' in metadata
    assert 'final_ci' in metadata


def test_heartbeat_with_regulation(mrh_graph):
    """Test heartbeat applies regulation"""
    manager = RegulatedGroundingManager("lct:test", mrh_graph)

    # Initial announcement
    context1 = create_context_at_location("geo:45.5,-122.6")
    grounding1, ci1, metadata1 = manager.announce(context1)

    # Heartbeat with same context (no change)
    grounding2, action, ci2, metadata2 = manager.heartbeat(context1)

    assert action == "refreshed (TTL extended)"
    assert len(manager.ci_history) == 2
    assert ci1 > 0.8  # Should be high (same location)
    assert ci2 > 0.8  # Should remain high


def test_check_status_with_ci(mrh_graph, context_portland):
    """Test status check includes current CI"""
    manager = RegulatedGroundingManager("lct:test", mrh_graph)

    # Before any grounding
    status, time, ci, metadata = manager.check_status_with_ci()
    assert ci is None

    # After announcement
    manager.announce(context_portland)
    status, time, ci, metadata = manager.check_status_with_ci()

    assert ci is not None
    assert isinstance(ci, float)
    assert 'raw_ci' in metadata


# ============================================================================
# Test Regulation Integration
# ============================================================================

def test_regulation_can_be_disabled(mrh_graph, context_portland):
    """Test that regulation can be disabled"""
    manager = RegulatedGroundingManager(
        "lct:test",
        mrh_graph,
        enable_regulation=False
    )

    grounding, ci, metadata = manager.announce(context_portland)

    # With regulation disabled, raw_ci should equal final_ci
    assert metadata['raw_ci'] == metadata.get('final_ci', metadata['raw_ci'])
    assert len(metadata.get('regulations_applied', [])) == 0


def test_regulation_summary_tracking(mrh_graph):
    """Test regulation summary statistics"""
    manager = RegulatedGroundingManager("lct:test", mrh_graph)

    # Multiple heartbeats
    for i in range(5):
        context = create_context_at_location(f"geo:45.{i},-122.6")
        if i == 0:
            manager.announce(context)
        else:
            manager.heartbeat(context)

    summary = manager.get_regulation_summary()

    assert summary['total_cycles'] == 5
    assert 'avg_raw_ci' in summary
    assert 'avg_final_ci' in summary
    assert 'regulation_types' in summary


def test_ci_history_retrieval(mrh_graph):
    """Test CI history retrieval with time window"""
    manager = RegulatedGroundingManager("lct:test", mrh_graph)

    # Add groundings over time
    base_time = datetime.now()
    for i in range(3):
        context = create_context_at_location("geo:45.5,-122.6", base_time + timedelta(minutes=i*15))
        if i == 0:
            manager.announce(context)
        else:
            manager.heartbeat(context)

    # Get all history
    all_history = manager.get_ci_history()
    assert len(all_history) == 3

    # Get recent history (last 20 minutes)
    recent_history = manager.get_ci_history(window=timedelta(minutes=20))
    assert len(recent_history) >= 1  # At least one should be within 20 min


# ============================================================================
# Test ATP Cost Calculation
# ============================================================================

def test_regulated_atp_cost(mrh_graph, context_portland):
    """Test ATP cost uses regulated CI"""
    manager = RegulatedGroundingManager("lct:test", mrh_graph)

    manager.announce(context_portland)

    # Calculate cost
    cost = manager.calculate_regulated_atp_cost(100.0)

    # With high CI, cost should be close to base
    assert 100.0 <= cost <= 120.0  # Allow small variation


def test_atp_cost_with_low_ci_gets_regulated(mrh_graph):
    """Test that low CI gets regulated to prevent excessive cost"""
    # Create config with strict regulation
    reg_config = CoherenceRegulationConfig(
        min_effective_ci=0.2,
        max_atp_multiplier=5.0
    )

    manager = RegulatedGroundingManager(
        "lct:test",
        mrh_graph,
        regulation_config=reg_config
    )

    # This test is structural - verifies regulation is applied
    # Actual CI values depend on grounding history
    manager.announce(create_context_at_location("geo:45.5,-122.6"))

    cost = manager.calculate_regulated_atp_cost(100.0)

    # Cost should be regulated (not astronomical)
    assert cost < 1000.0  # Should not hit unregulated extremes


# ============================================================================
# Test Extended Scenarios
# ============================================================================

def test_simulate_stable_grounding(mrh_graph):
    """Test simulation with stable grounding (same location)"""
    contexts = [create_context_at_location("geo:45.5,-122.6") for _ in range(5)]

    results = simulate_grounding_lifecycle("lct:test", mrh_graph, contexts)

    # Stable grounding should have high CI throughout
    assert results['final_ci'] > 0.8
    assert all(ci > 0.8 for ci in results['ci_values'])
    assert len(results['groundings']) == 5


def test_simulate_impossible_travel(mrh_graph):
    """Test simulation with impossible travel (cascade scenario)"""
    # Simulate rapid impossible travel
    locations = [
        "geo:45.5,-122.6",   # Portland
        "geo:47.6,-122.3",   # Seattle (plausible)
        "geo:51.0,-114.0",   # Calgary (getting implausible)
        "geo:60.0,-95.0",    # Northern Canada (impossible in 15 min)
        "geo:64.0,-21.9",    # Iceland (impossible)
    ]

    contexts = [create_context_at_location(loc) for loc in locations]

    results = simulate_grounding_lifecycle("lct:test", mrh_graph, contexts, enable_regulation=True)

    # With regulation, should not cascade to 0
    assert results['final_ci'] > 0.2  # Soft floor prevents total collapse
    summary = results['regulation_summary']
    assert summary['total_cycles'] == 5


def test_comparison_regulated_vs_unregulated(mrh_graph):
    """Test comparison shows regulation benefit"""
    # Create scenario that would cascade without regulation
    locations = ["geo:45.5,-122.6", "geo:47.6,-122.3", "geo:51.0,-114.0"]
    contexts = [create_context_at_location(loc) for loc in locations]

    comparison = compare_regulated_vs_unregulated("lct:test", mrh_graph, contexts)

    # Both should complete
    assert comparison['regulated']['final_ci'] is not None
    assert comparison['unregulated']['final_ci'] is not None

    # Regulated should have higher or equal CI
    # (In some cases they may be similar if no cascade occurs)
    assert comparison['improvement']['final_ci_delta'] >= -0.1  # Allow small negative variation


# ============================================================================
# Test Cascade Prevention
# ============================================================================

def test_cascade_detection_integration(mrh_graph):
    """Test that cascade detection works in integrated manager"""
    manager = RegulatedGroundingManager("lct:test", mrh_graph)

    # Create scenario that triggers cascade detection
    # Need multiple low CI groundings
    contexts = [create_context_at_location("geo:45.5,-122.6") for _ in range(6)]

    for i, context in enumerate(contexts):
        if i == 0:
            manager.announce(context)
        else:
            manager.heartbeat(context)

    summary = manager.get_regulation_summary()

    # Check that regulation was applied (structure test)
    assert summary['total_cycles'] == 6
    assert 'regulation_types' in summary


def test_regulation_prevents_lock_out(mrh_graph):
    """Integration test: Verify regulation prevents lock-out"""
    manager = RegulatedGroundingManager("lct:test", mrh_graph)

    # Simulate 10 cycles
    contexts = [create_context_at_location("geo:45.5,-122.6") for _ in range(10)]

    for i, context in enumerate(contexts):
        if i == 0:
            grounding, ci, metadata = manager.announce(context)
        else:
            grounding, action, ci, metadata = manager.heartbeat(context)

        # CI should never drop below soft floor
        assert ci >= 0.2  # Soft floor from regulation

    # Get summary
    summary = manager.get_regulation_summary()
    assert summary['total_cycles'] == 10


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
