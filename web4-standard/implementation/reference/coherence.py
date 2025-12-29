#!/usr/bin/env python3
"""
Coherence Calculation - Phase 2 of MRH Grounding Implementation

Implements the Coherence Index (CI) calculation that modulates trust application
based on the plausibility of an entity's current grounding given historical patterns.

Coherence Index combines four dimensions:
1. Spatial: Impossible travel detection (location plausibility)
2. Capability: Capability spoofing prevention (hardware consistency)
3. Temporal: Activity pattern analysis (timing plausibility)
4. Relational: MRH neighborhood consistency (interaction patterns)

The CI acts as a multiplier on trust application, not trust itself:
- High CI (0.9+): Full T3 access, normal ATP costs
- Low CI (<0.5): Reduced effective trust, increased ATP costs, more witnesses
"""

import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
import hashlib

# Import grounding types from mrh_rdf_implementation
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from mrh_rdf_implementation import GroundingEdge, GroundingContext, LocationContext


@dataclass
class CoherenceWeights:
    """
    Society-configurable weights for coherence calculation

    Default weights emphasize spatial and capability coherence (core security concerns)
    while treating temporal and relational as secondary signals.
    """
    spatial: float = 0.3      # Impossible travel is critical security concern
    capability: float = 0.3   # Capability spoofing is critical security concern
    temporal: float = 0.2     # Activity patterns provide supporting evidence
    relational: float = 0.2   # MRH neighborhood provides context

    # Window sizes for historical analysis
    spatial_window: timedelta = field(default_factory=lambda: timedelta(days=7))
    temporal_window: timedelta = field(default_factory=lambda: timedelta(days=90))

    def __post_init__(self):
        """Validate weights sum to 1.0"""
        total = self.spatial + self.capability + self.temporal + self.relational
        if not math.isclose(total, 1.0, abs_tol=0.01):
            raise ValueError(f"Weights must sum to 1.0, got {total}")


@dataclass
class EntityVelocityProfile:
    """Maximum plausible velocities for different entity types"""
    hardware_class: str
    max_velocity_km_h: float  # Maximum kilometers per hour

    @classmethod
    def defaults(cls) -> Dict[str, 'EntityVelocityProfile']:
        """Default velocity profiles for common entity types"""
        return {
            'edge-device': cls('edge-device', 10.0),      # 10 km/h (walking speed)
            'mobile': cls('mobile', 100.0),               # 100 km/h (car speed)
            'server': cls('server', 0.0),                 # 0 km/h (stationary)
            'browser': cls('browser', 100.0),             # 100 km/h (mobile device)
            'iot-sensor': cls('iot-sensor', 0.0),         # 0 km/h (stationary)
        }


@dataclass
class ActivityPattern:
    """Temporal activity pattern for an entity"""
    hour_distribution: Dict[int, float]  # Hour (0-23) -> probability
    day_distribution: Dict[int, float]   # Day (0-6, Mon-Sun) -> probability

    def score_time(self, timestamp: str) -> float:
        """
        Score how unusual a timestamp is (0 = typical, 1 = very unusual)

        Args:
            timestamp: ISO8601 timestamp

        Returns:
            Unusualness score [0.0, 1.0]
        """
        dt = datetime.fromisoformat(timestamp)
        hour_prob = self.hour_distribution.get(dt.hour, 0.0)
        day_prob = self.day_distribution.get(dt.weekday(), 0.0)

        # Combine hour and day probabilities (geometric mean)
        if hour_prob == 0.0 or day_prob == 0.0:
            return 1.0  # Completely unusual

        combined_prob = math.sqrt(hour_prob * day_prob)
        return 1.0 - combined_prob  # Invert: high prob = low unusualness


def geo_distance(loc1: LocationContext, loc2: LocationContext) -> float:
    """
    Calculate geographic distance between two locations in kilometers

    Simplified haversine for physical locations. Returns 0 for network/logical locations.

    Args:
        loc1: First location
        loc2: Second location

    Returns:
        Distance in kilometers
    """
    if loc1.type != "physical" or loc2.type != "physical":
        return 0.0  # Can't calculate distance for network/logical locations

    # Parse geo coordinates (format: "geo:lat,lon")
    try:
        lat1, lon1 = map(float, loc1.value.replace('geo:', '').split(','))
        lat2, lon2 = map(float, loc2.value.replace('geo:', '').split(','))
    except (ValueError, AttributeError):
        return 0.0  # Invalid format

    # Haversine formula
    R = 6371  # Earth radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def spatial_coherence(
    current: LocationContext,
    history: List[GroundingEdge],
    window: timedelta,
    hardware_class: str,
    travel_announcements: Optional[List[str]] = None,
    witnesses_at_destination: Optional[List[str]] = None
) -> float:
    """
    Measures whether current location is plausible given movement history

    Detects impossible travel by comparing:
    - Distance from last known location
    - Time elapsed since last grounding
    - Maximum plausible velocity for entity type

    Mitigations for legitimate travel:
    - Pre-announced travel reduces penalty
    - Witnesses at destination increase credibility

    Args:
        current: Current location
        history: Recent grounding edges (within window)
        window: Time window to consider
        hardware_class: Entity hardware class (determines max velocity)
        travel_announcements: List of announced destination locations
        witnesses_at_destination: List of witnesses who can confirm current location

    Returns:
        Coherence score [0.0, 1.0]
    """
    # Filter history to window
    cutoff = datetime.now() - window
    recent = [g for g in history
              if datetime.fromisoformat(g.timestamp) > cutoff]

    if not recent:
        return 0.5  # No history, neutral coherence

    # Get last known location
    last = recent[-1]
    last_location = last.target.location

    # Calculate distance and time
    distance = geo_distance(current, last_location)
    now = datetime.now()
    last_time = datetime.fromisoformat(last.timestamp)
    elapsed = now - last_time
    elapsed_hours = elapsed.total_seconds() / 3600

    if elapsed_hours == 0:
        return 1.0  # No time elapsed, same location expected

    # Get max velocity for entity type
    velocity_profiles = EntityVelocityProfile.defaults()
    profile = velocity_profiles.get(hardware_class, velocity_profiles['edge-device'])
    max_velocity = profile.max_velocity_km_h

    # Check for impossible travel
    actual_velocity = distance / elapsed_hours if elapsed_hours > 0 else 0

    if actual_velocity > max_velocity:
        # Impossible travel detected
        base_coherence = 0.1

        # Check for travel announcement
        if travel_announcements and current.value in travel_announcements:
            base_coherence += 0.4

        # Check for witness at destination
        if witnesses_at_destination and len(witnesses_at_destination) > 0:
            base_coherence += 0.3

        return min(base_coherence, 1.0)

    # Gradual reduction based on velocity ratio
    # Full coherence at low velocity, reduced as approaching max
    velocity_ratio = actual_velocity / max_velocity if max_velocity > 0 else 0
    return 1.0 - (velocity_ratio * 0.3)  # Max 30% reduction for fast but plausible travel


def capability_coherence(
    current_capabilities: List[str],
    current_hardware_class: str,
    history: List[GroundingEdge],
    upgrade_events: Optional[List[Tuple[datetime, List[str]]]] = None
) -> float:
    """
    Measures whether advertised capabilities are plausible

    Detects capability spoofing by checking:
    - Consistency with hardware class
    - Gradual vs sudden capability changes
    - Known upgrade/downgrade events

    Args:
        current_capabilities: Currently advertised capabilities
        current_hardware_class: Current hardware class
        history: Recent grounding edges
        upgrade_events: List of (timestamp, new_capabilities) for known upgrades

    Returns:
        Coherence score [0.0, 1.0]
    """
    # Define expected capabilities per hardware class
    expected_capabilities = {
        'edge-device': {'compute', 'sensors', 'local_storage'},
        'server': {'compute', 'gpu_inference', 'vector_db', 'rdf_query', 'storage'},
        'mobile': {'compute', 'sensors', 'camera', 'gps', 'local_storage'},
        'browser': {'compute', 'rendering', 'local_storage'},
        'iot-sensor': {'sensors', 'low_power_compute'},
    }

    expected = expected_capabilities.get(current_hardware_class, set())
    advertised = set(current_capabilities)

    # Check for capabilities beyond hardware class
    unexpected = advertised - expected
    if unexpected:
        # Each unexpected capability reduces coherence
        penalty = len(unexpected) * 0.16
        return max(0.0, 1.0 - penalty)

    # Check for sudden new capabilities without upgrade event
    if history:
        last = history[-1]
        last_caps = set(last.target.capabilities.advertised)
        new_caps = advertised - last_caps

        if new_caps:
            # Check if there's a known upgrade event
            if upgrade_events:
                # Find most recent upgrade
                recent_upgrades = [caps for ts, caps in upgrade_events
                                 if ts > datetime.fromisoformat(last.timestamp)]
                if recent_upgrades and new_caps.issubset(set(recent_upgrades[-1])):
                    return 1.0  # Legitimate upgrade

            # Sudden new capabilities without upgrade
            return 0.7  # Mild suspicion

    return 1.0


def temporal_coherence(
    current_timestamp: str,
    current_continuity_token: str,
    history: List[GroundingEdge],
    activity_pattern: Optional[ActivityPattern] = None
) -> float:
    """
    Measures whether activity timing is consistent with patterns

    Analyzes:
    - Time of day vs historical active hours
    - Day of week patterns
    - Session continuity (gaps in continuity_token chain)

    Args:
        current_timestamp: Current timestamp (ISO8601)
        current_continuity_token: Current continuity token
        history: Recent grounding edges
        activity_pattern: Pre-computed activity pattern (if available)

    Returns:
        Coherence score [0.0, 1.0]
    """
    if not history:
        return 0.5  # No history, neutral coherence

    # Check continuity chain
    if current_continuity_token:
        # Continuity token should be hash of last grounding
        last_grounding = history[-1]
        expected_token = hashlib.sha256(
            f"{last_grounding.source}{last_grounding.timestamp}".encode()
        ).hexdigest()[:16]

        if current_continuity_token != expected_token:
            return 0.3  # Broken chain is suspicious

    # Check activity pattern if available
    if activity_pattern:
        unusualness = activity_pattern.score_time(current_timestamp)
        # Unusual timing reduces coherence but doesn't eliminate it
        return 1.0 - (unusualness * 0.5)

    # Extract activity pattern from history
    pattern = extract_activity_pattern(history)
    if pattern:
        unusualness = pattern.score_time(current_timestamp)
        return 1.0 - (unusualness * 0.5)

    return 0.8  # No pattern available, slightly reduced coherence


def extract_activity_pattern(history: List[GroundingEdge]) -> Optional[ActivityPattern]:
    """
    Extract activity pattern from grounding history

    Args:
        history: Grounding edge history

    Returns:
        ActivityPattern or None if insufficient data
    """
    if len(history) < 10:
        return None  # Need at least 10 samples

    # Count activity by hour and day
    hour_counts = {h: 0 for h in range(24)}
    day_counts = {d: 0 for d in range(7)}

    for edge in history:
        dt = datetime.fromisoformat(edge.timestamp)
        hour_counts[dt.hour] += 1
        day_counts[dt.weekday()] += 1

    # Convert to probabilities with smoothing
    total = len(history)
    # Add Laplace smoothing to avoid zero probabilities
    hour_dist = {h: (count + 0.1) / (total + 2.4) for h, count in hour_counts.items()}
    day_dist = {d: (count + 0.1) / (total + 0.7) for d, count in day_counts.items()}

    return ActivityPattern(hour_dist, day_dist)


def relational_coherence(
    current_active_contexts: List[str],
    entity_lct: str,
    history: List[GroundingEdge],
    mrh_graph
) -> float:
    """
    Measures whether current interactions fit relationship patterns

    Analyzes:
    - Are active contexts within usual MRH neighborhood?
    - Sudden engagement with distant graph regions
    - Society membership vs interaction targets

    Args:
        current_active_contexts: LCTs currently engaged with
        entity_lct: Entity's LCT identifier
        history: Recent grounding edges
        mrh_graph: MRH graph for neighborhood analysis

    Returns:
        Coherence score [0.0, 1.0]
    """
    # Get usual MRH neighborhood (depth=2)
    usual_neighborhood = get_mrh_neighborhood(entity_lct, mrh_graph, depth=2)
    current_contexts = set(current_active_contexts)

    if not current_contexts:
        return 1.0  # No active contexts, nothing to check

    # Calculate familiarity ratio
    familiar = current_contexts & usual_neighborhood
    familiarity_ratio = len(familiar) / len(current_contexts)

    # Novel contexts aren't bad, but reduce coherence slightly
    # High familiarity (0.8+) = high coherence
    # Low familiarity (0.2-) = moderate coherence (0.6)
    return 0.5 + (familiarity_ratio * 0.5)


def get_mrh_neighborhood(entity_lct: str, mrh_graph, depth: int) -> Set[str]:
    """
    Get MRH neighborhood up to specified depth

    Args:
        entity_lct: Entity LCT identifier
        mrh_graph: MRH graph (from mrh_rdf_implementation)
        depth: Traversal depth

    Returns:
        Set of LCT identifiers in neighborhood
    """
    # This would use actual MRH traversal from mrh_rdf_implementation
    # For now, return empty set (would be implemented with real graph)
    # In production, this would use mrh_graph.traverse_markov() or similar
    return set()


def coherence_index(
    current: GroundingContext,
    history: List[GroundingEdge],
    mrh_graph,
    weights: Optional[CoherenceWeights] = None,
    travel_announcements: Optional[List[str]] = None,
    witnesses: Optional[List[str]] = None,
    upgrade_events: Optional[List[Tuple[datetime, List[str]]]] = None,
    activity_pattern: Optional[ActivityPattern] = None
) -> float:
    """
    Compute overall Coherence Index (CI)

    Combines four coherence dimensions using weighted geometric mean:
    - Spatial: Location plausibility
    - Capability: Hardware/capability consistency
    - Temporal: Activity pattern consistency
    - Relational: MRH neighborhood consistency

    Uses geometric mean (multiplicative) so one low score tanks the whole CI.
    This is a security feature - all dimensions must be coherent.

    Args:
        current: Current grounding context
        history: Recent grounding edge history
        mrh_graph: MRH graph for relational analysis
        weights: Coherence weights (uses defaults if None)
        travel_announcements: Pre-announced travel destinations
        witnesses: Witnesses at current location
        upgrade_events: Known hardware upgrade events
        activity_pattern: Pre-computed activity pattern

    Returns:
        Coherence Index [0.0, 1.0]
    """
    if weights is None:
        weights = CoherenceWeights()

    # Calculate each coherence dimension
    spatial = spatial_coherence(
        current.location,
        history,
        weights.spatial_window,
        current.capabilities.hardware_class,
        travel_announcements,
        witnesses
    )

    capability = capability_coherence(
        current.capabilities.advertised,
        current.capabilities.hardware_class,
        history,
        upgrade_events
    )

    temporal = temporal_coherence(
        current.session.started,
        current.session.continuity_token,
        history,
        activity_pattern
    )

    relational = relational_coherence(
        current.active_contexts,
        history[0].source if history else "",
        history,
        mrh_graph
    )

    # Weighted geometric mean (multiplicative)
    # One low dimension tanks the whole score (security property)
    ci = (
        spatial ** weights.spatial *
        capability ** weights.capability *
        temporal ** weights.temporal *
        relational ** weights.relational
    ) ** (1 / 1.0)  # Normalize by sum of weights (always 1.0)

    return ci


def demo_coherence_calculation():
    """Demonstrate coherence calculation with example scenarios"""

    print("=" * 60)
    print("COHERENCE CALCULATION DEMO - Phase 2 Implementation")
    print("=" * 60)

    # Import from mrh_rdf_implementation for actual grounding types
    from mrh_rdf_implementation import (
        GroundingEdge, GroundingContext, LocationContext,
        CapabilitiesContext, SessionContext, ResourceState
    )

    # Scenario 1: Normal Operation (High Coherence)
    print("\n1. Normal Operation - High Coherence Expected")
    print("-" * 40)

    # Create grounding history (same location for 6 months)
    history = []
    base_time = datetime.now() - timedelta(days=180)

    for i in range(50):
        timestamp = base_time + timedelta(days=i*3, hours=9)  # Every 3 days at 9am
        edge = GroundingEdge(
            source="sage-legion-001",
            target=GroundingContext(
                location=LocationContext("physical", "geo:45.5231,-122.6765", "city", False),
                capabilities=CapabilitiesContext(
                    ["compute", "gpu_inference", "vector_db"],
                    "server",
                    ResourceState(0.75, 0.80, 0.95, ["gpu", "cpu_thermal"])
                ),
                session=SessionContext(
                    timestamp.isoformat(),
                    hashlib.sha256(b"pattern").hexdigest()[:16],
                    hashlib.sha256(f"prev-{i}".encode()).hexdigest()[:16]
                ),
                active_contexts=["sage:thor", "sage:sprout"]
            ),
            timestamp=timestamp.isoformat(),
            ttl=timedelta(hours=1),
            signature="sig-normal",
            witness_set=["sage:thor"]
        )
        history.append(edge)

    # Current grounding (same location, same capabilities)
    current_context = GroundingContext(
        location=LocationContext("physical", "geo:45.5231,-122.6765", "city", False),
        capabilities=CapabilitiesContext(
            ["compute", "gpu_inference", "vector_db"],
            "server",
            ResourceState(0.75, 0.80, 0.95, ["gpu", "cpu_thermal"])
        ),
        session=SessionContext(
            datetime.now().isoformat(),
            hashlib.sha256(b"pattern").hexdigest()[:16],
            hashlib.sha256(f"prev-50".encode()).hexdigest()[:16]
        ),
        active_contexts=["sage:thor", "sage:sprout"]
    )

    ci = coherence_index(current_context, history, None)
    print(f"  Coherence Index: {ci:.3f}")
    print(f"  Effect: Full T3 access, normal ATP costs")

    # Scenario 2: Announced Travel (Moderate Coherence)
    print("\n2. Announced Travel - Moderate Coherence Expected")
    print("-" * 40)

    current_context_travel = GroundingContext(
        location=LocationContext("physical", "geo:52.5200,13.4050", "city", False),  # Berlin
        capabilities=CapabilitiesContext(
            ["compute", "gpu_inference", "vector_db"],
            "server",
            ResourceState(0.75, 0.80, 0.95, ["gpu", "cpu_thermal"])
        ),
        session=SessionContext(
            datetime.now().isoformat(),
            hashlib.sha256(b"pattern").hexdigest()[:16],
            hashlib.sha256(f"prev-50".encode()).hexdigest()[:16]
        ),
        active_contexts=["sage:thor", "sage:sprout"]
    )

    ci_travel = coherence_index(
        current_context_travel,
        history,
        None,
        travel_announcements=["geo:52.5200,13.4050"],
        witnesses=["sage:thor-berlin"]
    )
    print(f"  Coherence Index: {ci_travel:.3f}")
    print(f"  Effect: Slightly elevated ATP costs, normal witness requirements")

    # Scenario 3: Suspicious Context Shift (Low Coherence)
    print("\n3. Suspicious Context Shift - Low Coherence Expected")
    print("-" * 40)

    current_context_suspicious = GroundingContext(
        location=LocationContext("physical", "geo:1.3521,103.8198", "city", False),  # Singapore
        capabilities=CapabilitiesContext(
            ["compute", "gpu_inference", "vector_db", "quantum_compute", "ftl_comm"],  # Impossible!
            "server",
            ResourceState(0.75, 0.80, 0.95, ["gpu", "cpu_thermal"])
        ),
        session=SessionContext(
            datetime.now().isoformat(),
            hashlib.sha256(b"different_pattern").hexdigest()[:16],
            "invalid-continuity-token"
        ),
        active_contexts=["unknown:entity-1", "unknown:entity-2"]
    )

    ci_suspicious = coherence_index(current_context_suspicious, history, None)
    print(f"  Coherence Index: {ci_suspicious:.3f}")
    print(f"  Effect: Effective trust capped at {int(ci_suspicious*100)}% of T3, " +
          f"{int(1/ci_suspicious**2)}x ATP cost, +{int((0.8-ci_suspicious)*10)} witnesses required")

    print("\n" + "=" * 60)
    print("Phase 2 Coherence Calculation Complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo_coherence_calculation()
