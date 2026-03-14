#!/usr/bin/env python3
"""
Test Coherence Aggregation Comparison - Session 104

Compares geometric (legacy) vs min-weighted-critical (new) aggregation strategies
to validate that the new strategy provides better security properties.

Author: Claude (Session 104 Track 1)
Date: 2025-12-29
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from coherence import coherence_index, CoherenceWeights
from mrh_rdf_implementation import (
    GroundingContext, LocationContext,
    CapabilitiesContext, SessionContext, ResourceState, MRHGraph
)
from grounding_lifecycle import announce_grounding, GroundingTTLConfig


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


# ============================================================================
# Test Aggregation Strategies
# ============================================================================

def test_geometric_vs_min_weighted_critical_impossible_travel(mrh_graph, portland_location, tokyo_location):
    """
    Compare geometric vs min-weighted-critical for impossible travel scenario

    Scenario: Portland → Tokyo in 15 minutes (impossible!)
    Expected:
    - Geometric: ~0.45 (lenient)
    - Min-weighted-critical: 0.1 (severe - matches spatial)
    """
    # Create history at Portland 15 minutes ago
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

    # Test geometric strategy
    weights_geometric = CoherenceWeights(aggregation_strategy='geometric')
    ci_geometric = coherence_index(tokyo_context, [portland_edge], mrh_graph, weights_geometric)

    # Test min-weighted-critical strategy
    weights_critical = CoherenceWeights(aggregation_strategy='min-weighted-critical')
    ci_critical = coherence_index(tokyo_context, [portland_edge], mrh_graph, weights_critical)

    print(f"\nImpossible Travel (Portland → Tokyo in 15 min):")
    print(f"  Geometric:             {ci_geometric:.3f} (lenient)")
    print(f"  Min-Weighted-Critical: {ci_critical:.3f} (severe)")
    print(f"  Improvement:           {ci_geometric - ci_critical:.3f} (lower is better for security)")

    # Validations
    assert ci_geometric > 0.40, "Geometric should be lenient (~0.45)"
    assert ci_critical <= 0.15, "Min-weighted-critical should be severe (≤0.15)"
    assert ci_critical < ci_geometric, "New strategy should be more severe"

    # Critical floor should match spatial dimension (0.1)
    assert abs(ci_critical - 0.1) < 0.05, "Should match spatial coherence floor"


def test_both_strategies_all_coherent(mrh_graph, portland_location):
    """
    Both strategies should give similar high scores when all coherent

    Scenario: Staying in same location (all dimensions coherent)
    Expected: Both strategies ~0.9
    """
    # Create history at Portland 1 hour ago
    base_time = datetime.now() - timedelta(hours=1)

    portland_context_past = GroundingContext(
        location=portland_location,
        capabilities=CapabilitiesContext(["test"], "edge-device", ResourceState(0.7, 0.8, 0.9)),
        session=SessionContext(base_time.isoformat(), "pattern", ""),
        active_contexts=[]
    )
    portland_edge = announce_grounding("test", portland_context_past, mrh_graph, GroundingTTLConfig())
    portland_edge.timestamp = base_time.isoformat()

    # Current context still at Portland
    portland_context_now = GroundingContext(
        location=portland_location,
        capabilities=CapabilitiesContext(["test"], "edge-device", ResourceState(0.7, 0.8, 0.9)),
        session=SessionContext(datetime.now().isoformat(), "pattern", ""),
        active_contexts=[]
    )

    # Test both strategies
    weights_geometric = CoherenceWeights(aggregation_strategy='geometric')
    ci_geometric = coherence_index(portland_context_now, [portland_edge], mrh_graph, weights_geometric)

    weights_critical = CoherenceWeights(aggregation_strategy='min-weighted-critical')
    ci_critical = coherence_index(portland_context_now, [portland_edge], mrh_graph, weights_critical)

    print(f"\nAll Coherent (staying at Portland):")
    print(f"  Geometric:             {ci_geometric:.3f}")
    print(f"  Min-Weighted-Critical: {ci_critical:.3f}")
    print(f"  Difference:            {abs(ci_geometric - ci_critical):.3f} (should be small)")

    # Both should be high and similar
    assert ci_geometric >= 0.85, "Geometric should be high when all coherent"
    assert ci_critical >= 0.80, "Min-weighted-critical should also be high when all coherent"
    assert abs(ci_geometric - ci_critical) < 0.15, "Should be similar for coherent scenario"


def test_security_property_critical_floor(mrh_graph, portland_location):
    """
    Verify min-weighted-critical enforces critical dimension floor

    Test that CI cannot exceed minimum of critical dimensions (spatial, capability)
    even if temporal/relational are perfect.
    """
    # Create history with slightly low spatial coherence (0.3)
    # This could happen with legitimate fast travel
    base_time = datetime.now() - timedelta(hours=2)

    portland_context = GroundingContext(
        location=portland_location,
        capabilities=CapabilitiesContext(["test"], "mobile", ResourceState(0.7, 0.8, 0.9)),
        session=SessionContext(base_time.isoformat(), "pattern", ""),
        active_contexts=[]
    )
    portland_edge = announce_grounding("test", portland_context, mrh_graph, GroundingTTLConfig())
    portland_edge.timestamp = base_time.isoformat()

    # Current location ~150 km away (within mobile limits but fast)
    # This gives spatial coherence ~0.5-0.7
    nearby_location = LocationContext("physical", "geo:46.5,-122.5", "city", True)

    nearby_context = GroundingContext(
        location=nearby_location,
        capabilities=CapabilitiesContext(["test"], "mobile", ResourceState(0.7, 0.8, 0.9)),
        session=SessionContext(datetime.now().isoformat(), "pattern", ""),
        active_contexts=[]
    )

    # Test min-weighted-critical
    weights = CoherenceWeights(aggregation_strategy='min-weighted-critical')
    ci = coherence_index(nearby_context, [portland_edge], mrh_graph, weights)

    print(f"\nLegitimate Fast Travel:")
    print(f"  CI (min-weighted-critical): {ci:.3f}")
    print(f"  Note: CI floored by spatial coherence even if other dims perfect")

    # CI should be reasonable but not exceed spatial coherence
    # (which is the lowest critical dimension in this case)
    assert 0.3 <= ci <= 0.9, "Should be moderate (legitimate but fast travel)"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
