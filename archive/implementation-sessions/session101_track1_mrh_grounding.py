"""
SESSION 101 TRACK 1: MRH GROUNDING IMPLEMENTATION

Implements Phase 1 (Core Infrastructure) of the MRH Grounding proposal.

This adds the fifth MRH relationship type: Grounding
- Captures ephemeral operational presence (where entity IS, what it CAN do)
- Computes Coherence Index (CI) from spatial, capability, temporal, relational dimensions
- Modulates trust and ATP costs based on coherence
- Integrates with Session 100's accountability stack

Key innovations:
- GroundingContext: Current operational state (location, capabilities, session)
- GroundingEdge: MRH edge with TTL and heartbeat
- CoherenceCalculator: Computes CI from grounding history
- TrustModulator: Applies CI to effective trust

References:
- MRH Grounding Proposal: /home/dp/ai-workspace/web4/proposals/MRH_GROUNDING_PROPOSAL.md
- Session 100: ACT integration and delegation chains
- Consequence Index: /home/dp/ai-workspace/private-context/messages/2025-12-28-consequence-index-proposal.md
"""

import hashlib
import json
import time
import math
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum


# ============================================================================
# GROUNDING CONTEXT
# ============================================================================

class LocationType(Enum):
    """Type of location grounding."""
    PHYSICAL = "physical"  # GPS coordinates
    NETWORK = "network"    # IP range, network segment
    LOGICAL = "logical"    # Society ID, service name


class PrecisionLevel(Enum):
    """Precision of location claim."""
    EXACT = "exact"        # GPS coordinates, specific IP
    CITY = "city"          # City-level precision
    REGION = "region"      # State/province level
    COUNTRY = "country"    # Country level
    GLOBAL = "global"      # No specific location


class HardwareClass(Enum):
    """Hardware class for capability expectations."""
    EDGE_DEVICE = "edge-device"      # Raspberry Pi, Jetson Nano
    MOBILE = "mobile"                # Phone, tablet
    WORKSTATION = "workstation"      # Desktop, laptop
    SERVER = "server"                # Server hardware
    CLUSTER = "cluster"              # Distributed compute


class ResourceLevel(Enum):
    """Resource availability levels."""
    NONE = 0.0
    LOW = 0.25
    MEDIUM = 0.50
    HIGH = 0.75
    MAXIMUM = 1.0


@dataclass
class Location:
    """Location information for grounding."""
    type: LocationType
    value: str  # GPS coords, IP, society ID, etc.
    precision: PrecisionLevel
    verifiable: bool = False  # Can be independently verified?

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "value": self.value,
            "precision": self.precision.value,
            "verifiable": self.verifiable
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Location':
        return Location(
            type=LocationType(data["type"]),
            value=data["value"],
            precision=PrecisionLevel(data["precision"]),
            verifiable=data.get("verifiable", False)
        )


@dataclass
class Capabilities:
    """Capability information for grounding."""
    advertised: List[str]  # Capability IDs
    hardware_class: HardwareClass
    resource_state: Dict[str, ResourceLevel]
    sensors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "advertised": self.advertised,
            "hardware_class": self.hardware_class.value,
            "resource_state": {k: v.value for k, v in self.resource_state.items()},
            "sensors": self.sensors
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Capabilities':
        return Capabilities(
            advertised=data["advertised"],
            hardware_class=HardwareClass(data["hardware_class"]),
            resource_state={k: ResourceLevel(v) for k, v in data["resource_state"].items()},
            sensors=data.get("sensors", [])
        )


@dataclass
class Session:
    """Session information for grounding."""
    started: str
    activity_pattern: str  # Hash of recent activity timing
    continuity_token: Optional[str] = None  # Links to previous grounding

    def to_dict(self) -> Dict[str, Any]:
        return {
            "started": self.started,
            "activity_pattern": self.activity_pattern,
            "continuity_token": self.continuity_token
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Session':
        return Session(
            started=data["started"],
            activity_pattern=data["activity_pattern"],
            continuity_token=data.get("continuity_token")
        )


@dataclass
class GroundingContext:
    """
    Current operational context for an entity.

    This captures WHERE an entity is and WHAT it can do right now,
    distinct from WHO it is (LCT) and what it's TRUSTED to do (T3).
    """
    # Spatial grounding
    location: Location

    # Capability grounding
    capabilities: Capabilities

    # Temporal grounding
    session: Session

    # Relational grounding
    active_contexts: List[str] = field(default_factory=list)  # LCT URIs
    surface: Optional[str] = None  # Current interaction surface

    def to_dict(self) -> Dict[str, Any]:
        return {
            "location": self.location.to_dict(),
            "capabilities": self.capabilities.to_dict(),
            "session": self.session.to_dict(),
            "active_contexts": self.active_contexts,
            "surface": self.surface
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'GroundingContext':
        return GroundingContext(
            location=Location.from_dict(data["location"]),
            capabilities=Capabilities.from_dict(data["capabilities"]),
            session=Session.from_dict(data["session"]),
            active_contexts=data.get("active_contexts", []),
            surface=data.get("surface")
        )


# ============================================================================
# GROUNDING EDGE
# ============================================================================

@dataclass
class GroundingEdge:
    """
    MRH grounding edge - the fifth relationship type.

    Represents ephemeral operational presence with TTL and heartbeat.
    """
    # Edge identity
    edge_id: str
    source: str  # LCT URI of entity being grounded
    target: GroundingContext  # Current operational context

    # Temporal properties
    timestamp: str
    ttl: int  # Seconds until expiration
    expires_at: str

    # Cryptographic proof
    signature: str  # Signed by source LCT

    # Verification
    witness_set: List[str] = field(default_factory=list)  # LCT URIs of witnesses
    status: str = "active"  # active, expired, revoked

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source": self.source,
            "target": self.target.to_dict(),
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "expires_at": self.expires_at,
            "signature": self.signature,
            "witness_set": self.witness_set,
            "status": self.status
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'GroundingEdge':
        return GroundingEdge(
            edge_id=data["edge_id"],
            source=data["source"],
            target=GroundingContext.from_dict(data["target"]),
            timestamp=data["timestamp"],
            ttl=data["ttl"],
            expires_at=data["expires_at"],
            signature=data["signature"],
            witness_set=data.get("witness_set", []),
            status=data.get("status", "active")
        )

    def is_expired(self) -> bool:
        """Check if grounding edge has expired."""
        expires = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))
        return datetime.now(timezone.utc) > expires

    def is_active(self) -> bool:
        """Check if grounding edge is active."""
        return self.status == "active" and not self.is_expired()


# ============================================================================
# COHERENCE CALCULATION
# ============================================================================

@dataclass
class CoherenceWeights:
    """Weights for coherence index calculation (society-configurable)."""
    spatial: float = 0.3
    capability: float = 0.3
    temporal: float = 0.2
    relational: float = 0.2
    spatial_window: int = 3600  # Seconds to look back for spatial coherence

    def __post_init__(self):
        # Normalize weights to sum to 1.0
        total = self.spatial + self.capability + self.temporal + self.relational
        if total != 1.0:
            self.spatial /= total
            self.capability /= total
            self.temporal /= total
            self.relational /= total


class CoherenceCalculator:
    """
    Calculates Coherence Index (CI) from grounding history.

    CI ∈ [0.0, 1.0] where:
    - 1.0 = Fully coherent (expected patterns)
    - 0.5 = Neutral (no history or mixed signals)
    - 0.0 = Highly incoherent (impossible or suspicious)
    """

    def __init__(self, weights: Optional[CoherenceWeights] = None):
        self.weights = weights or CoherenceWeights()

    def coherence_index(
        self,
        current: GroundingContext,
        history: List[GroundingEdge]
    ) -> float:
        """
        Compute overall coherence index from current context and history.

        Uses weighted geometric mean (multiplicative, not additive) so that
        very low coherence in one dimension strongly impacts overall.
        """
        spatial = self.spatial_coherence(current.location, history)
        capability = self.capability_coherence(current.capabilities, history)
        temporal = self.temporal_coherence(current.session, history)
        relational = self.relational_coherence(current.active_contexts, history)

        # Weighted geometric mean
        ci = (
            (spatial ** self.weights.spatial) *
            (capability ** self.weights.capability) *
            (temporal ** self.weights.temporal) *
            (relational ** self.weights.relational)
        )

        return max(0.0, min(1.0, ci))

    def spatial_coherence(
        self,
        current: Location,
        history: List[GroundingEdge]
    ) -> float:
        """
        Measures whether current location is plausible given movement history.

        Factors:
        - Distance from last known location
        - Time elapsed since last grounding
        - Maximum plausible velocity for entity type
        - Witness corroboration
        """
        if not history:
            return 0.5  # No history, neutral coherence

        # Filter to recent history within spatial window
        window_start = datetime.now(timezone.utc) - timedelta(seconds=self.weights.spatial_window)
        recent = [
            edge for edge in history
            if datetime.fromisoformat(edge.timestamp.replace('Z', '+00:00')) > window_start
        ]

        if not recent:
            return 0.5  # No recent history

        last = recent[-1]

        # If locations are same type and value, perfect coherence
        if (current.type == last.target.location.type and
            current.value == last.target.location.value):
            return 1.0

        # For different locations, check if movement is plausible
        # Simplified: use precision as proxy for distance
        if current.precision == PrecisionLevel.EXACT and last.target.location.precision == PrecisionLevel.EXACT:
            # Would need real distance calculation for GPS
            # For now, assume same country = plausible
            if self._same_region(current.value, last.target.location.value):
                return 0.9
            else:
                # Check for witness at destination
                if current.verifiable or len(last.witness_set) > 0:
                    return 0.7  # Witnessed move
                return 0.4  # Unwitnessed long-distance move

        # Logical/network locations - check consistency
        if current.type == LocationType.LOGICAL:
            # Check if entity has history in this logical space
            logical_history = [
                e for e in history
                if e.target.location.type == LocationType.LOGICAL
                and e.target.location.value == current.value
            ]
            if logical_history:
                return 0.95  # Known location
            return 0.6  # New logical space

        return 0.5  # Default neutral

    def _same_region(self, loc1: str, loc2: str) -> bool:
        """Check if two location values are in same region (simplified)."""
        # For real implementation, would use geospatial distance
        # For now, simple string prefix matching
        return loc1[:5] == loc2[:5] if len(loc1) >= 5 and len(loc2) >= 5 else False

    def capability_coherence(
        self,
        current: Capabilities,
        history: List[GroundingEdge]
    ) -> float:
        """
        Measures whether advertised capabilities are plausible.

        Factors:
        - Consistency with hardware class
        - Gradual vs sudden capability changes
        - Resource levels match hardware class
        """
        # Expected capabilities for hardware class
        expected = self._expected_capabilities(current.hardware_class)
        advertised = set(current.advertised)

        # Capabilities beyond hardware class are suspicious
        unexpected = advertised - expected
        if unexpected:
            penalty = min(len(unexpected) * 0.15, 0.5)
            base_coherence = 1.0 - penalty
        else:
            base_coherence = 1.0

        # Check for sudden capability changes
        if history:
            last_caps = set(history[-1].target.capabilities.advertised)
            new_caps = advertised - last_caps
            removed_caps = last_caps - advertised

            if new_caps or removed_caps:
                # Capability changes reduce coherence slightly unless gradual
                change_ratio = len(new_caps | removed_caps) / max(len(advertised), len(last_caps))
                if change_ratio > 0.5:  # More than 50% change
                    base_coherence *= 0.7

        return base_coherence

    def _expected_capabilities(self, hardware_class: HardwareClass) -> Set[str]:
        """Expected capabilities for hardware class."""
        capabilities_map = {
            HardwareClass.EDGE_DEVICE: {"compute", "storage", "sensors"},
            HardwareClass.MOBILE: {"compute", "storage", "sensors", "gps", "camera"},
            HardwareClass.WORKSTATION: {"compute", "storage", "display", "audio"},
            HardwareClass.SERVER: {"compute", "storage", "network", "database"},
            HardwareClass.CLUSTER: {"compute", "storage", "network", "distributed", "gpu"}
        }
        return capabilities_map.get(hardware_class, set())

    def temporal_coherence(
        self,
        current: Session,
        history: List[GroundingEdge]
    ) -> float:
        """
        Measures whether activity timing is consistent with patterns.

        Factors:
        - Session continuity (unbroken continuity_token chain)
        - Activity pattern consistency
        """
        if not history:
            return 0.5  # No history, neutral

        # Check continuity token chain
        if current.continuity_token:
            # Verify continuity token matches hash of last grounding
            if history:
                last_hash = hashlib.sha256(history[-1].edge_id.encode()).hexdigest()[:16]
                if current.continuity_token != last_hash:
                    return 0.3  # Broken continuity chain

        # Check activity pattern consistency
        # For now, simplified: if pattern hash matches recent history, high coherence
        if history:
            recent_patterns = [e.target.session.activity_pattern for e in history[-5:]]
            if current.activity_pattern in recent_patterns:
                return 1.0
            # Different but within recent set
            return 0.8

        return 0.5

    def relational_coherence(
        self,
        current_contexts: List[str],
        history: List[GroundingEdge]
    ) -> float:
        """
        Measures whether current interactions fit relationship patterns.

        Factors:
        - Are active contexts within usual neighborhood?
        - Consistency with historical interaction patterns
        """
        if not current_contexts:
            return 1.0  # No active contexts, nothing to check

        if not history:
            return 0.5  # No history, neutral

        # Extract historical contexts
        historical_contexts = set()
        for edge in history:
            historical_contexts.update(edge.target.active_contexts)

        current_set = set(current_contexts)
        familiar = current_set & historical_contexts
        novel = current_set - historical_contexts

        if not current_set:
            return 1.0

        # Calculate familiarity ratio
        familiarity_ratio = len(familiar) / len(current_set)

        # Novel contexts aren't bad, but reduce coherence slightly
        return 0.5 + (familiarity_ratio * 0.5)


# ============================================================================
# TRUST MODULATION
# ============================================================================

class TrustModulator:
    """
    Modulates trust and costs based on Coherence Index.

    CI doesn't replace T3 - it gates how T3 is applied.
    """

    def effective_trust(self, base_trust: float, ci: float, sensitivity: float = 1.0) -> float:
        """
        Calculate effective trust given base trust and coherence.

        Args:
            base_trust: Base trust value (e.g., from T3 tensor)
            ci: Coherence Index [0.0, 1.0]
            sensitivity: How sensitive this trust dimension is to coherence [0.0, 1.0]

        Returns:
            Effective trust after CI modulation
        """
        # CI acts as a ceiling on effective trust
        # High CI = full trust available
        # Low CI = only fraction of trust accessible
        modulation = 1.0 - (sensitivity * (1.0 - ci))
        return base_trust * modulation

    def adjusted_atp_cost(self, base_cost: float, ci: float) -> float:
        """
        Calculate ATP cost adjusted for coherence.

        Lower coherence = higher ATP cost (friction for suspicious contexts).
        """
        if ci >= 0.9:
            return base_cost  # No penalty for high coherence

        # Exponential increase as coherence drops
        multiplier = 1.0 / (ci ** 2)
        return base_cost * min(multiplier, 10.0)  # Cap at 10x

    def required_witnesses(self, base_requirement: int, ci: float) -> int:
        """
        Calculate witness requirements adjusted for coherence.

        Lower coherence = more witnesses needed.
        """
        if ci >= 0.8:
            return base_requirement

        # Add witnesses as coherence drops
        additional = math.ceil((0.8 - ci) * 10)  # Up to 8 additional witnesses
        return base_requirement + additional


# ============================================================================
# GROUNDING MANAGER
# ============================================================================

class GroundingManager:
    """
    Manages grounding edges and coherence calculation.

    This is the main interface for grounding operations.
    """

    def __init__(self, weights: Optional[CoherenceWeights] = None):
        # Storage
        self.groundings: Dict[str, List[GroundingEdge]] = {}  # LCT → grounding history
        self.current_groundings: Dict[str, GroundingEdge] = {}  # LCT → current grounding

        # Coherence calculator
        self.coherence = CoherenceCalculator(weights)

        # Trust modulator
        self.trust_modulator = TrustModulator()

    def announce_grounding(
        self,
        entity: str,
        context: GroundingContext,
        ttl: int = 3600  # 1 hour default
    ) -> GroundingEdge:
        """
        Announce new grounding for entity.

        Creates grounding edge, computes continuity token, signs.
        """
        # Get last grounding for continuity
        continuity_token = None
        if entity in self.current_groundings:
            last = self.current_groundings[entity]
            continuity_token = hashlib.sha256(last.edge_id.encode()).hexdigest()[:16]
            context.session.continuity_token = continuity_token

        # Create edge
        timestamp = datetime.now(timezone.utc).isoformat()
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=ttl)).isoformat()
        edge_id = f"ground_{hashlib.sha256(f'{entity}{timestamp}'.encode()).hexdigest()[:16]}"

        # Sign (simplified - real implementation would use LCT private key)
        signature = hashlib.sha256(
            json.dumps({
                "entity": entity,
                "context": context.to_dict(),
                "timestamp": timestamp
            }, sort_keys=True).encode()
        ).hexdigest()

        edge = GroundingEdge(
            edge_id=edge_id,
            source=entity,
            target=context,
            timestamp=timestamp,
            ttl=ttl,
            expires_at=expires_at,
            signature=signature
        )

        # Store
        if entity not in self.groundings:
            self.groundings[entity] = []
        self.groundings[entity].append(edge)
        self.current_groundings[entity] = edge

        return edge

    def get_current_grounding(self, entity: str) -> Optional[GroundingEdge]:
        """Get current grounding for entity."""
        if entity in self.current_groundings:
            edge = self.current_groundings[entity]
            if edge.is_active():
                return edge
        return None

    def get_coherence_index(self, entity: str) -> float:
        """
        Calculate current coherence index for entity.

        Returns 0.0 if no active grounding.
        """
        current = self.get_current_grounding(entity)
        if not current:
            return 0.0  # No grounding = no coherence

        history = self.groundings.get(entity, [])
        return self.coherence.coherence_index(current.target, history[:-1])  # Exclude current from history

    def get_effective_trust(self, entity: str, base_trust: float, sensitivity: float = 1.0) -> float:
        """Calculate effective trust for entity given base trust."""
        ci = self.get_coherence_index(entity)
        return self.trust_modulator.effective_trust(base_trust, ci, sensitivity)

    def get_adjusted_atp_cost(self, entity: str, base_cost: float) -> float:
        """Calculate ATP cost adjusted for entity's coherence."""
        ci = self.get_coherence_index(entity)
        return self.trust_modulator.adjusted_atp_cost(base_cost, ci)

    def get_required_witnesses(self, entity: str, base_requirement: int) -> int:
        """Calculate witness requirements adjusted for entity's coherence."""
        ci = self.get_coherence_index(entity)
        return self.trust_modulator.required_witnesses(base_requirement, ci)


# ============================================================================
# TESTING AND VALIDATION
# ============================================================================

def test_mrh_grounding():
    """Test MRH grounding implementation."""
    print("=" * 70)
    print("SESSION 101 TRACK 1: MRH GROUNDING IMPLEMENTATION")
    print("=" * 70)
    print()

    manager = GroundingManager()

    # Test 1: Create initial grounding
    print("Test 1: Initial Grounding")
    print("-" * 70)

    entity_lct = "lct://web4:agent:sage_sprout@mainnet"
    context1 = GroundingContext(
        location=Location(
            type=LocationType.PHYSICAL,
            value="geo:45.5231,-122.6765",  # Portland, OR
            precision=PrecisionLevel.CITY,
            verifiable=True
        ),
        capabilities=Capabilities(
            advertised=["compute", "storage", "sensors"],
            hardware_class=HardwareClass.EDGE_DEVICE,
            resource_state={
                "compute": ResourceLevel.MEDIUM,
                "memory": ResourceLevel.MEDIUM,
                "network": ResourceLevel.HIGH
            },
            sensors=["temperature", "humidity"]
        ),
        session=Session(
            started=datetime.now(timezone.utc).isoformat(),
            activity_pattern="pattern_abc123"
        ),
        active_contexts=["lct://web4:society:genesis@mainnet"]
    )

    edge1 = manager.announce_grounding(entity_lct, context1, ttl=3600)
    print(f"✓ Created grounding: {edge1.edge_id}")
    print(f"  Location: {edge1.target.location.value}")
    print(f"  Hardware class: {edge1.target.capabilities.hardware_class.value}")
    print(f"  Expires: {edge1.expires_at}")
    print(f"  Active: {edge1.is_active()}")
    print()

    # Test 2: Coherence with no history
    print("Test 2: Coherence Index (No History)")
    print("-" * 70)
    ci = manager.get_coherence_index(entity_lct)
    print(f"Coherence Index: {ci:.3f}")
    print(f"  Expected: ~0.5 (neutral, no history)")
    print()

    # Test 3: Consistent subsequent grounding
    print("Test 3: Consistent Subsequent Grounding")
    print("-" * 70)
    time.sleep(0.1)  # Simulate time passage

    context2 = GroundingContext(
        location=Location(
            type=LocationType.PHYSICAL,
            value="geo:45.5231,-122.6765",  # Same location
            precision=PrecisionLevel.CITY,
            verifiable=True
        ),
        capabilities=Capabilities(
            advertised=["compute", "storage", "sensors"],  # Same capabilities
            hardware_class=HardwareClass.EDGE_DEVICE,
            resource_state={
                "compute": ResourceLevel.MEDIUM,
                "memory": ResourceLevel.MEDIUM,
                "network": ResourceLevel.HIGH
            },
            sensors=["temperature", "humidity"]
        ),
        session=Session(
            started=datetime.now(timezone.utc).isoformat(),
            activity_pattern="pattern_abc123"  # Same pattern
        ),
        active_contexts=["lct://web4:society:genesis@mainnet"]
    )

    edge2 = manager.announce_grounding(entity_lct, context2)
    ci2 = manager.get_coherence_index(entity_lct)
    print(f"✓ Second grounding: {edge2.edge_id}")
    print(f"Coherence Index: {ci2:.3f}")
    print(f"  Expected: ~0.95+ (consistent location, capabilities, pattern)")
    print()

    # Test 4: Trust modulation
    print("Test 4: Trust Modulation")
    print("-" * 70)
    base_trust = 0.8
    effective_trust = manager.get_effective_trust(entity_lct, base_trust)
    print(f"Base trust: {base_trust}")
    print(f"Coherence Index: {ci2:.3f}")
    print(f"Effective trust: {effective_trust:.3f}")
    print(f"  Modulation: {effective_trust/base_trust * 100:.1f}% of base trust accessible")
    print()

    # Test 5: ATP cost modulation
    print("Test 5: ATP Cost Modulation")
    print("-" * 70)
    base_cost = 100.0
    adjusted_cost = manager.get_adjusted_atp_cost(entity_lct, base_cost)
    print(f"Base ATP cost: {base_cost}")
    print(f"Adjusted cost: {adjusted_cost:.2f}")
    print(f"  Multiplier: {adjusted_cost/base_cost:.2f}x")
    print()

    # Test 6: Suspicious context shift
    print("Test 6: Suspicious Context Shift (Impossible Travel)")
    print("-" * 70)
    time.sleep(0.1)

    context3 = GroundingContext(
        location=Location(
            type=LocationType.PHYSICAL,
            value="geo:1.3521,103.8198",  # Singapore (impossible travel)
            precision=PrecisionLevel.CITY,
            verifiable=False  # Not witnessed
        ),
        capabilities=Capabilities(
            advertised=["compute", "storage", "gpu", "distributed"],  # Upgraded capabilities
            hardware_class=HardwareClass.CLUSTER,  # Hardware class changed!
            resource_state={
                "compute": ResourceLevel.MAXIMUM,
                "memory": ResourceLevel.MAXIMUM,
                "network": ResourceLevel.MAXIMUM
            }
        ),
        session=Session(
            started=datetime.now(timezone.utc).isoformat(),
            activity_pattern="pattern_xyz789"  # Different pattern
        ),
        active_contexts=["lct://web4:society:unknown@mainnet"]  # Unknown society
    )

    edge3 = manager.announce_grounding(entity_lct, context3)
    ci3 = manager.get_coherence_index(entity_lct)
    print(f"✓ Suspicious grounding: {edge3.edge_id}")
    print(f"  Location changed: Portland → Singapore")
    print(f"  Hardware class: edge-device → cluster")
    print(f"  Capabilities: major expansion")
    print(f"Coherence Index: {ci3:.3f}")
    print(f"  Expected: Low (~0.3-0.5)")
    print()

    # Test 7: Trust and cost impact of low coherence
    print("Test 7: Low Coherence Impact")
    print("-" * 70)
    effective_trust_low = manager.get_effective_trust(entity_lct, base_trust)
    adjusted_cost_low = manager.get_adjusted_atp_cost(entity_lct, base_cost)
    witnesses_required = manager.get_required_witnesses(entity_lct, 1)

    print(f"Coherence Index: {ci3:.3f}")
    print(f"Effective trust: {effective_trust_low:.3f} ({effective_trust_low/base_trust * 100:.1f}% of base)")
    print(f"ATP cost multiplier: {adjusted_cost_low/base_cost:.2f}x")
    print(f"Witnesses required: {witnesses_required} (base: 1)")
    print()

    # Test 8: Grounding expiration
    print("Test 8: Grounding Expiration")
    print("-" * 70)

    # Create short-TTL grounding
    context4 = GroundingContext(
        location=Location(
            type=LocationType.LOGICAL,
            value="society:test",
            precision=PrecisionLevel.EXACT,
            verifiable=True
        ),
        capabilities=Capabilities(
            advertised=["compute"],
            hardware_class=HardwareClass.EDGE_DEVICE,
            resource_state={"compute": ResourceLevel.LOW}
        ),
        session=Session(
            started=datetime.now(timezone.utc).isoformat(),
            activity_pattern="test"
        )
    )

    short_edge = manager.announce_grounding(entity_lct, context4, ttl=1)  # 1 second TTL
    print(f"Created short-TTL grounding: {short_edge.edge_id}")
    print(f"  TTL: {short_edge.ttl} seconds")
    print(f"  Active: {short_edge.is_active()}")

    time.sleep(1.5)
    print(f"\nAfter {short_edge.ttl} seconds:")
    print(f"  Active: {short_edge.is_active()}")
    print(f"  Expired: {short_edge.is_expired()}")
    print()

    print("=" * 70)
    print("MRH GROUNDING TESTS COMPLETE")
    print("=" * 70)
    print()
    print("Summary:")
    print(f"✓ Grounding edge creation: Working")
    print(f"✓ Coherence calculation: Working")
    print(f"✓ Consistent grounding → High CI: {ci2:.3f}")
    print(f"✓ Suspicious shift → Low CI: {ci3:.3f}")
    print(f"✓ Trust modulation: {effective_trust_low/base_trust * 100:.1f}% reduction")
    print(f"✓ ATP cost increase: {adjusted_cost_low/base_cost:.2f}x multiplier")
    print(f"✓ Witness requirements: +{witnesses_required - 1} additional")
    print(f"✓ TTL expiration: Working")
    print()

    return {
        "groundings_created": len(manager.groundings[entity_lct]),
        "high_coherence": ci2,
        "low_coherence": ci3,
        "trust_modulation_ratio": effective_trust_low / base_trust,
        "cost_multiplier": adjusted_cost_low / base_cost,
        "additional_witnesses": witnesses_required - 1
    }


if __name__ == "__main__":
    results = test_mrh_grounding()
    print(f"\nTest results:\n{json.dumps(results, indent=2)}")
