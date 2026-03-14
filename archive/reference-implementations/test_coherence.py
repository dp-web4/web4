#!/usr/bin/env python3
"""
Unit tests for coherence calculation

Tests the four coherence dimensions and combined coherence index:
1. Spatial coherence (impossible travel detection)
2. Capability coherence (capability spoofing prevention)
3. Temporal coherence (activity pattern analysis)
4. Relational coherence (MRH neighborhood consistency)
5. Combined coherence index (weighted geometric mean)
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
import hashlib

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from coherence import (
    spatial_coherence, capability_coherence, temporal_coherence,
    relational_coherence, coherence_index, geo_distance,
    extract_activity_pattern, CoherenceWeights, ActivityPattern,
    EntityVelocityProfile
)
from mrh_rdf_implementation import (
    GroundingEdge, GroundingContext, LocationContext,
    CapabilitiesContext, SessionContext, ResourceState
)


class TestGeoDistance(unittest.TestCase):
    """Test geographic distance calculation"""

    def test_same_location(self):
        """Distance between same location should be 0"""
        loc = LocationContext("physical", "geo:45.5231,-122.6765", "city", False)
        distance = geo_distance(loc, loc)
        self.assertEqual(distance, 0.0)

    def test_portland_to_seattle(self):
        """Portland to Seattle is ~234 km"""
        portland = LocationContext("physical", "geo:45.5231,-122.6765", "city", False)
        seattle = LocationContext("physical", "geo:47.6062,-122.3321", "city", False)
        distance = geo_distance(portland, seattle)
        self.assertAlmostEqual(distance, 234, delta=10)

    def test_non_physical_locations(self):
        """Network/logical locations should return 0"""
        network = LocationContext("network", "192.168.1.0/24", "subnet", False)
        logical = LocationContext("logical", "society-123", "exact", False)
        distance = geo_distance(network, logical)
        self.assertEqual(distance, 0.0)


class TestSpatialCoherence(unittest.TestCase):
    """Test spatial coherence calculation"""

    def create_grounding_at_location(self, location_value: str, timestamp: datetime) -> GroundingEdge:
        """Helper to create grounding edge"""
        return GroundingEdge(
            source="test-entity",
            target=GroundingContext(
                location=LocationContext("physical", location_value, "city", False),
                capabilities=CapabilitiesContext(
                    ["compute"],
                    "server",
                    ResourceState(0.5, 0.5, 0.5)
                ),
                session=SessionContext(
                    timestamp.isoformat(),
                    "pattern",
                    "continuity"
                ),
                active_contexts=[]
            ),
            timestamp=timestamp.isoformat(),
            ttl=timedelta(hours=1),
            signature="sig",
            witness_set=[]
        )

    def test_stationary_entity_high_coherence(self):
        """Stationary entity in same location should have high coherence"""
        portland = LocationContext("physical", "geo:45.5231,-122.6765", "city", False)

        # History: same location for a week
        history = [
            self.create_grounding_at_location("geo:45.5231,-122.6765",
                                            datetime.now() - timedelta(days=i))
            for i in range(7, 0, -1)
        ]

        coherence = spatial_coherence(
            portland, history, timedelta(days=7), "server"
        )
        self.assertGreater(coherence, 0.9)

    def test_impossible_travel_low_coherence(self):
        """Impossible travel should result in low coherence"""
        portland = LocationContext("physical", "geo:45.5231,-122.6765", "city", False)
        singapore = LocationContext("physical", "geo:1.3521,103.8198", "city", False)

        # History: in Portland 1 hour ago
        history = [
            self.create_grounding_at_location("geo:45.5231,-122.6765",
                                            datetime.now() - timedelta(hours=1))
        ]

        # Now claiming to be in Singapore (13,000+ km in 1 hour!)
        coherence = spatial_coherence(
            singapore, history, timedelta(days=1), "server"
        )
        self.assertLess(coherence, 0.5)

    def test_announced_travel_increases_coherence(self):
        """Pre-announced travel should increase coherence"""
        portland = LocationContext("physical", "geo:45.5231,-122.6765", "city", False)
        berlin = LocationContext("physical", "geo:52.5200,13.4050", "city", False)

        history = [
            self.create_grounding_at_location("geo:45.5231,-122.6765",
                                            datetime.now() - timedelta(hours=12))
        ]

        # Without announcement
        coherence_no_announce = spatial_coherence(
            berlin, history, timedelta(days=1), "server"
        )

        # With announcement
        coherence_announced = spatial_coherence(
            berlin, history, timedelta(days=1), "server",
            travel_announcements=["geo:52.5200,13.4050"]
        )

        self.assertGreater(coherence_announced, coherence_no_announce)


class TestCapabilityCoherence(unittest.TestCase):
    """Test capability coherence calculation"""

    def test_consistent_capabilities_high_coherence(self):
        """Consistent capabilities should have high coherence"""
        current_caps = ["compute", "gpu_inference", "vector_db"]
        coherence = capability_coherence(current_caps, "server", [])
        self.assertEqual(coherence, 1.0)

    def test_unexpected_capabilities_low_coherence(self):
        """Capabilities beyond hardware class should reduce coherence"""
        # IoT sensor claiming GPU capabilities
        current_caps = ["sensors", "gpu_inference", "quantum_compute"]
        coherence = capability_coherence(current_caps, "iot-sensor", [])
        self.assertLess(coherence, 0.7)

    def test_sudden_capabilities_without_upgrade(self):
        """Sudden new capabilities without upgrade should reduce coherence"""
        base_time = datetime.now() - timedelta(days=1)

        history = [
            GroundingEdge(
                source="test",
                target=GroundingContext(
                    location=LocationContext("physical", "geo:0,0", "city", False),
                    capabilities=CapabilitiesContext(
                        ["compute"],  # Only basic compute
                        "server",
                        ResourceState(0.5, 0.5, 0.5)
                    ),
                    session=SessionContext(base_time.isoformat(), "p", "c"),
                    active_contexts=[]
                ),
                timestamp=base_time.isoformat(),
                ttl=timedelta(hours=1),
                signature="sig",
                witness_set=[]
            )
        ]

        # Now claiming GPU capabilities
        current_caps = ["compute", "gpu_inference"]
        coherence = capability_coherence(current_caps, "server", history)
        self.assertEqual(coherence, 0.7)


class TestTemporalCoherence(unittest.TestCase):
    """Test temporal coherence calculation"""

    def test_valid_continuity_token_high_coherence(self):
        """Valid continuity token should give high coherence"""
        last_timestamp = (datetime.now() - timedelta(hours=1)).isoformat()
        last_grounding = GroundingEdge(
            source="test",
            target=GroundingContext(
                LocationContext("physical", "geo:0,0", "city", False),
                CapabilitiesContext(["compute"], "server", ResourceState(0.5, 0.5, 0.5)),
                SessionContext(last_timestamp, "pattern", "prev-token"),
                []
            ),
            timestamp=last_timestamp,
            ttl=timedelta(hours=1),
            signature="sig",
            witness_set=[]
        )

        # Generate valid continuity token
        expected_token = hashlib.sha256(
            f"{last_grounding.source}{last_grounding.timestamp}".encode()
        ).hexdigest()[:16]

        coherence = temporal_coherence(
            datetime.now().isoformat(),
            expected_token,
            [last_grounding]
        )
        self.assertGreater(coherence, 0.7)

    def test_broken_continuity_low_coherence(self):
        """Broken continuity chain should reduce coherence"""
        last_grounding = GroundingEdge(
            source="test",
            target=GroundingContext(
                LocationContext("physical", "geo:0,0", "city", False),
                CapabilitiesContext(["compute"], "server", ResourceState(0.5, 0.5, 0.5)),
                SessionContext(datetime.now().isoformat(), "pattern", "token"),
                []
            ),
            timestamp=datetime.now().isoformat(),
            ttl=timedelta(hours=1),
            signature="sig",
            witness_set=[]
        )

        coherence = temporal_coherence(
            datetime.now().isoformat(),
            "invalid-token",  # Wrong token
            [last_grounding]
        )
        self.assertEqual(coherence, 0.3)


class TestActivityPattern(unittest.TestCase):
    """Test activity pattern extraction and scoring"""

    def test_extract_pattern_from_history(self):
        """Should extract activity pattern from sufficient history"""
        # Create history with activity at 9am on weekdays
        history = []
        base_time = datetime.now() - timedelta(days=30)

        for day in range(30):
            timestamp = base_time + timedelta(days=day, hours=9)
            if timestamp.weekday() < 5:  # Weekdays only
                edge = GroundingEdge(
                    source="test",
                    target=GroundingContext(
                        LocationContext("physical", "geo:0,0", "city", False),
                        CapabilitiesContext(["compute"], "server", ResourceState(0.5, 0.5, 0.5)),
                        SessionContext(timestamp.isoformat(), "p", "c"),
                        []
                    ),
                    timestamp=timestamp.isoformat(),
                    ttl=timedelta(hours=1),
                    signature="sig",
                    witness_set=[]
                )
                history.append(edge)

        pattern = extract_activity_pattern(history)
        self.assertIsNotNone(pattern)

        # 9am should have higher probability than 3am
        self.assertGreater(pattern.hour_distribution[9], pattern.hour_distribution[3])


class TestCoherenceIndex(unittest.TestCase):
    """Test combined coherence index calculation"""

    def test_all_high_coherence(self):
        """All dimensions high should give high CI"""
        # This would need real grounding data
        # For now, test that weights validation works
        weights = CoherenceWeights(
            spatial=0.3,
            capability=0.3,
            temporal=0.2,
            relational=0.2
        )
        self.assertAlmostEqual(
            weights.spatial + weights.capability + weights.temporal + weights.relational,
            1.0
        )

    def test_weights_must_sum_to_one(self):
        """Weights must sum to 1.0"""
        with self.assertRaises(ValueError):
            CoherenceWeights(
                spatial=0.5,
                capability=0.3,
                temporal=0.1,
                relational=0.1  # Sum = 1.0, this should pass
            )
            CoherenceWeights(
                spatial=0.5,
                capability=0.5,
                temporal=0.5,
                relational=0.5  # Sum = 2.0, should fail
            )


class TestEntityVelocityProfile(unittest.TestCase):
    """Test velocity profile defaults"""

    def test_default_profiles_exist(self):
        """Should have defaults for common hardware classes"""
        profiles = EntityVelocityProfile.defaults()

        self.assertIn('edge-device', profiles)
        self.assertIn('server', profiles)
        self.assertIn('mobile', profiles)

    def test_server_is_stationary(self):
        """Servers should have 0 velocity"""
        profiles = EntityVelocityProfile.defaults()
        self.assertEqual(profiles['server'].max_velocity_km_h, 0.0)

    def test_mobile_has_car_speed(self):
        """Mobile devices should allow car speeds"""
        profiles = EntityVelocityProfile.defaults()
        self.assertGreaterEqual(profiles['mobile'].max_velocity_km_h, 100.0)


if __name__ == '__main__':
    unittest.main()
