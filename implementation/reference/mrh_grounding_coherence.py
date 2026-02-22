"""
MRH Grounding & Coherence Index — Reference Implementation

Implements the MRH Grounding Proposal (proposals/MRH_GROUNDING_PROPOSAL.md):
- Grounding as fifth MRH relationship type (ephemeral operational presence)
- GroundingContext: spatial + capability + temporal + relational state
- GroundingEdge: MRH edge with TTL, heartbeat, witness verification
- Coherence Index (CI): 4-dimension weighted geometric mean
- Consequence Index (CX): action consequence classification + CI/CX gating
- Trust modulation: CI gates effective T3, ATP costs, witness requirements
- Grounding lifecycle: announce → heartbeat → refresh → expire
- Security: impossible travel, capability spoofing, history poisoning detection

Key insight from proposal: "Coherence doesn't grant trust — it gates how trust
is applied. High CI = full T3 available. Low CI = only fraction accessible."
CI/CX gating: "Don't operate machinery while impaired."

Spec: proposals/MRH_GROUNDING_PROPOSAL.md
"""

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class LocationType(Enum):
    PHYSICAL = "physical"
    NETWORK = "network"
    LOGICAL = "logical"

class PrecisionLevel(Enum):
    EXACT = "exact"
    CITY = "city"
    REGION = "region"
    COUNTRY = "country"
    GLOBAL = "global"

class HardwareClass(Enum):
    EDGE_DEVICE = "edge-device"
    MOBILE = "mobile"
    WORKSTATION = "workstation"
    SERVER = "server"
    CLUSTER = "cluster"

class ResourceLevel(Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAXIMUM = "maximum"

class EdgeStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    REFRESHED = "refreshed"

class CXLevel(Enum):
    """Consequence Index classification per §5.4."""
    TRIVIAL = "trivial"         # 0.0-0.2: read-only queries, logging
    MODERATE = "moderate"       # 0.2-0.5: state modifications, API calls
    SIGNIFICANT = "significant" # 0.5-0.7: financial transactions, deployments
    HIGH = "high"               # 0.7-0.9: irreversible actions, deletions
    CRITICAL = "critical"       # 0.9-1.0: critical infrastructure, safety-relevant

class EscalationPath(Enum):
    """When CI < required threshold for CX."""
    DELEGATE = "delegate"       # Find higher-CI entity
    WAIT = "wait"               # Let coherence improve
    REDUCE_SCOPE = "reduce"     # Break into lower-CX steps
    COSIGN = "cosign"           # Multiple entities jointly meet threshold


# Hardware class → expected capabilities (§4.3)
HARDWARE_CAPABILITIES = {
    HardwareClass.EDGE_DEVICE: {"compute", "storage", "sensors"},
    HardwareClass.MOBILE: {"compute", "storage", "sensors", "gps", "camera"},
    HardwareClass.WORKSTATION: {"compute", "storage", "display", "audio"},
    HardwareClass.SERVER: {"compute", "storage", "network", "database"},
    HardwareClass.CLUSTER: {"compute", "storage", "network", "distributed", "gpu"},
}

# Hardware class → max velocity in km/h (for impossible travel detection)
MAX_VELOCITY = {
    HardwareClass.EDGE_DEVICE: 0,        # Stationary
    HardwareClass.MOBILE: 1000,           # Aircraft speed
    HardwareClass.WORKSTATION: 200,       # Ground transport
    HardwareClass.SERVER: 0,              # Stationary
    HardwareClass.CLUSTER: 0,             # Stationary
}

# Default grounding TTL by hardware class (seconds)
DEFAULT_TTL = {
    HardwareClass.EDGE_DEVICE: 3600,      # 1 hour
    HardwareClass.MOBILE: 1800,           # 30 minutes
    HardwareClass.WORKSTATION: 3600,      # 1 hour
    HardwareClass.SERVER: 7200,           # 2 hours
    HardwareClass.CLUSTER: 7200,          # 2 hours
}


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Location:
    type: LocationType
    value: str                        # GPS coords, IP, society ID
    precision: PrecisionLevel
    verifiable: bool = False
    lat: float = 0.0                  # For physical locations
    lon: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type.value, "value": self.value,
                "precision": self.precision.value, "verifiable": self.verifiable,
                "lat": self.lat, "lon": self.lon}


@dataclass
class Capabilities:
    advertised: List[str]
    hardware_class: HardwareClass
    resource_state: Dict[str, str]    # resource → ResourceLevel value
    sensors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"advertised": self.advertised,
                "hardware_class": self.hardware_class.value,
                "resource_state": self.resource_state, "sensors": self.sensors}


@dataclass
class SessionInfo:
    started: str
    activity_pattern: str             # Hash of recent activity timing
    continuity_token: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"started": self.started, "activity_pattern": self.activity_pattern,
                "continuity_token": self.continuity_token}


@dataclass
class GroundingContext:
    """Current operational context (§3.2)."""
    location: Location
    capabilities: Capabilities
    session: SessionInfo
    active_contexts: List[str] = field(default_factory=list)  # LCT URIs
    surface: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"location": self.location.to_dict(),
                "capabilities": self.capabilities.to_dict(),
                "session": self.session.to_dict(),
                "active_contexts": self.active_contexts,
                "surface": self.surface}


@dataclass
class TravelAnnouncement:
    """Pre-announced travel reduces coherence penalty (§4.2)."""
    entity: str
    destination_value: str
    start_time: str
    end_time: str
    witnessed_by: List[str] = field(default_factory=list)


@dataclass
class UpgradeEvent:
    """Known hardware/capability upgrade (§4.3)."""
    entity: str
    timestamp: str
    new_capabilities: List[str]
    witnessed_by: List[str] = field(default_factory=list)


@dataclass
class GroundingEdge:
    """MRH grounding edge — fifth relationship type (§3.1)."""
    edge_id: str
    source: str               # LCT URI
    target: GroundingContext
    timestamp: str
    ttl: int                  # seconds
    expires_at: str
    signature: str
    witness_set: List[str] = field(default_factory=list)
    status: EdgeStatus = EdgeStatus.ACTIVE

    def to_dict(self) -> Dict[str, Any]:
        return {"edge_id": self.edge_id, "source": self.source,
                "target": self.target.to_dict(), "timestamp": self.timestamp,
                "ttl": self.ttl, "expires_at": self.expires_at,
                "signature": self.signature, "witness_set": self.witness_set,
                "status": self.status.value}

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now(timezone.utc)
        expires = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
        return now > expires

    def is_active(self, now: Optional[datetime] = None) -> bool:
        return self.status == EdgeStatus.ACTIVE and not self.is_expired(now)


@dataclass
class CoherenceWeights:
    """Society-configurable weights for CI calculation (§4.6)."""
    spatial: float = 0.3
    capability: float = 0.3
    temporal: float = 0.2
    relational: float = 0.2
    spatial_window: int = 86400       # 24-hour lookback

    def total(self) -> float:
        return self.spatial + self.capability + self.temporal + self.relational


@dataclass
class CoherenceBreakdown:
    """Detailed CI breakdown for audit trail."""
    spatial: float
    capability: float
    temporal: float
    relational: float
    combined: float
    weights: CoherenceWeights


@dataclass
class ActionSpec:
    """Action with consequence classification (§5.4)."""
    action_id: str
    name: str
    cx: float                # Consequence Index [0,1]
    cx_level: CXLevel
    base_atp_cost: float = 1.0
    base_witnesses: int = 0

    @staticmethod
    def classify(cx: float) -> CXLevel:
        if cx < 0.2: return CXLevel.TRIVIAL
        if cx < 0.5: return CXLevel.MODERATE
        if cx < 0.7: return CXLevel.SIGNIFICANT
        if cx < 0.9: return CXLevel.HIGH
        return CXLevel.CRITICAL


@dataclass
class GatingResult:
    """Result of CI/CX gating check."""
    allowed: bool
    ci: float
    required_ci: float
    cx: float
    escalation_paths: List[EscalationPath] = field(default_factory=list)
    effective_trust: float = 0.0
    adjusted_atp_cost: float = 0.0
    required_witnesses: int = 0


@dataclass
class WitnessVerification:
    """Witness verification of a grounding claim (§6.4)."""
    witness: str
    edge_id: str
    timestamp: str
    method: str               # "co-located", "network", "society-active"
    signature: str


# ============================================================================
# COHERENCE CALCULATOR (§4)
# ============================================================================

class CoherenceCalculator:
    """Computes CI from grounding history. CI ∈ [0,1]."""

    def __init__(self, weights: Optional[CoherenceWeights] = None):
        self.weights = weights or CoherenceWeights()

    def compute(self, current: GroundingContext,
                history: List[GroundingEdge],
                travel_announcements: Optional[List[TravelAnnouncement]] = None,
                upgrade_events: Optional[List[UpgradeEvent]] = None,
                mrh_neighborhood: Optional[Set[str]] = None) -> CoherenceBreakdown:
        """Compute CI using weighted geometric mean (§4.6)."""
        s = self.spatial_coherence(current.location, history,
                                   travel_announcements or [])
        c = self.capability_coherence(current.capabilities, history,
                                       upgrade_events or [])
        t = self.temporal_coherence(current.session, history)
        r = self.relational_coherence(current.active_contexts, history,
                                       mrh_neighborhood)

        w = self.weights
        wt = w.total()
        # Weighted geometric mean — multiplicative so low dimension strongly impacts
        ci = (s ** (w.spatial / wt) *
              c ** (w.capability / wt) *
              t ** (w.temporal / wt) *
              r ** (w.relational / wt))
        ci = max(0.0, min(1.0, ci))

        return CoherenceBreakdown(spatial=s, capability=c, temporal=t,
                                  relational=r, combined=ci, weights=w)

    def spatial_coherence(self, current: Location,
                          history: List[GroundingEdge],
                          travel_announcements: List[TravelAnnouncement]) -> float:
        """§4.2: Location plausibility given movement history."""
        if not history:
            return 0.5  # No history → neutral

        # Filter to recent history within spatial window
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=self.weights.spatial_window)
        recent = [e for e in history
                  if datetime.fromisoformat(e.timestamp.replace("Z", "+00:00")) > window_start]
        if not recent:
            return 0.5

        last = recent[-1]
        last_loc = last.target.location

        # Same location → perfect
        if (current.type == last_loc.type and current.value == last_loc.value):
            return 1.0

        # Physical → physical: check impossible travel
        if current.type == LocationType.PHYSICAL and last_loc.type == LocationType.PHYSICAL:
            distance_km = self._haversine(current.lat, current.lon,
                                           last_loc.lat, last_loc.lon)
            elapsed_h = max((now - datetime.fromisoformat(
                last.timestamp.replace("Z", "+00:00"))).total_seconds() / 3600, 0.001)
            max_vel = MAX_VELOCITY.get(last.target.capabilities.hardware_class, 1000)

            if max_vel == 0 and distance_km > 1:
                # Stationary device moved — very suspicious
                base = 0.1
            elif distance_km / elapsed_h > max_vel:
                # Impossible travel
                base = 0.1
                # Pre-announced travel?
                if self._has_travel_announcement(travel_announcements, current.value):
                    base += 0.4
                # Witness at destination?
                if current.verifiable:
                    base += 0.3
                return min(base, 1.0)
            else:
                # Plausible travel — gradual reduction with distance
                return max(0.5, 1.0 - (distance_km / (max_vel * elapsed_h + 1)))

        # Logical locations — check familiarity
        if current.type == LocationType.LOGICAL:
            known = any(e.target.location.type == LocationType.LOGICAL
                        and e.target.location.value == current.value
                        for e in history)
            return 0.95 if known else 0.6

        # Network locations
        if current.type == LocationType.NETWORK:
            known = any(e.target.location.type == LocationType.NETWORK
                        and e.target.location.value == current.value
                        for e in history)
            return 0.9 if known else 0.5

        return 0.5

    def capability_coherence(self, current: Capabilities,
                              history: List[GroundingEdge],
                              upgrade_events: List[UpgradeEvent]) -> float:
        """§4.3: Capability plausibility given hardware class."""
        expected = HARDWARE_CAPABILITIES.get(current.hardware_class, set())
        advertised = set(current.advertised)

        # Capabilities beyond hardware class
        unexpected = advertised - expected
        base = max(0.5, 1.0 - len(unexpected) * 0.15)

        # Check for sudden capability changes
        if history:
            last_caps = set(history[-1].target.capabilities.advertised)
            new_caps = advertised - last_caps
            removed_caps = last_caps - advertised

            change_count = len(new_caps | removed_caps)
            total_caps = max(len(advertised), len(last_caps), 1)
            change_ratio = change_count / total_caps

            if new_caps:
                # New capabilities: check for upgrade event
                upgrade_caps = set()
                for ue in upgrade_events:
                    upgrade_caps.update(ue.new_capabilities)
                unexplained_new = new_caps - upgrade_caps
                if unexplained_new:
                    base *= 0.7  # Unexplained new capabilities

            if change_ratio > 0.5:
                base *= 0.7  # Major shift

            # Hardware class change
            if history[-1].target.capabilities.hardware_class != current.hardware_class:
                base *= 0.5  # Very suspicious

        return max(0.0, min(1.0, base))

    def temporal_coherence(self, current: SessionInfo,
                           history: List[GroundingEdge]) -> float:
        """§4.4: Activity timing consistency."""
        if not history:
            return 0.5

        # Continuity token chain
        if current.continuity_token:
            last = history[-1]
            expected_token = hashlib.sha256(last.edge_id.encode()).hexdigest()[:16]
            if current.continuity_token != expected_token:
                return 0.3  # Broken chain

        # Activity pattern consistency
        recent_patterns = [e.target.session.activity_pattern for e in history[-5:]]
        if current.activity_pattern in recent_patterns:
            return 1.0

        # Different pattern but not broken chain
        return 0.8

    def relational_coherence(self, current_contexts: List[str],
                              history: List[GroundingEdge],
                              mrh_neighborhood: Optional[Set[str]]) -> float:
        """§4.5: Interaction pattern consistency."""
        if not current_contexts:
            return 1.0  # No contexts → nothing to check
        if not history:
            return 0.5

        # Build historical context set
        historical = set()
        for e in history:
            historical.update(e.target.active_contexts)

        current_set = set(current_contexts)
        # Use MRH neighborhood if available, else fall back to history
        neighborhood = mrh_neighborhood or historical
        familiar = current_set & neighborhood
        familiarity_ratio = len(familiar) / len(current_set) if current_set else 1.0

        return 0.5 + (familiarity_ratio * 0.5)

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine distance in km."""
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @staticmethod
    def _has_travel_announcement(announcements: List[TravelAnnouncement],
                                  destination: str) -> bool:
        return any(a.destination_value == destination for a in announcements)


# ============================================================================
# TRUST MODULATOR (§5)
# ============================================================================

class TrustModulator:
    """Modulates T3, ATP costs, and witness requirements by CI."""

    @staticmethod
    def effective_trust(base_trust: float, ci: float, sensitivity: float = 1.0) -> float:
        """§5.1: CI gates how T3 is applied. sensitivity ∈ [0,1]."""
        modulation = 1.0 - (sensitivity * (1.0 - ci))
        return base_trust * max(0.0, modulation)

    @staticmethod
    def adjusted_atp_cost(base_cost: float, ci: float) -> float:
        """§5.2: Low coherence → higher ATP cost. Capped at 10×."""
        if ci >= 0.9:
            return base_cost
        safe_ci = max(ci, 0.1)  # Avoid division by zero
        multiplier = min(1.0 / (safe_ci ** 2), 10.0)
        return base_cost * multiplier

    @staticmethod
    def required_witnesses(base_requirement: int, ci: float) -> int:
        """§5.3: Low coherence → more witnesses. Up to +8 additional."""
        if ci >= 0.8:
            return base_requirement
        additional = math.ceil((0.8 - ci) * 10)
        return base_requirement + additional

    @staticmethod
    def ci_threshold_for_cx(cx: float) -> float:
        """§5.4: Higher consequence → higher coherence required.
        Range: 0.3 (trivial) to 0.9 (critical)."""
        return 0.3 + (cx * 0.6)


# ============================================================================
# CI/CX GATING ENGINE (§5.4)
# ============================================================================

class CXGatingEngine:
    """Gates actions by CI × CX. "Don't operate machinery while impaired." """

    def __init__(self):
        self.modulator = TrustModulator()

    def check(self, ci: float, action: ActionSpec, base_trust: float = 0.8) -> GatingResult:
        """Check whether entity can execute action given current CI."""
        required_ci = self.modulator.ci_threshold_for_cx(action.cx)
        allowed = ci >= required_ci

        escalation_paths = []
        if not allowed:
            escalation_paths = [
                EscalationPath.DELEGATE,
                EscalationPath.WAIT,
                EscalationPath.REDUCE_SCOPE,
                EscalationPath.COSIGN,
            ]

        eff_trust = self.modulator.effective_trust(base_trust, ci)
        atp_cost = self.modulator.adjusted_atp_cost(action.base_atp_cost, ci)
        witnesses = self.modulator.required_witnesses(action.base_witnesses, ci)

        return GatingResult(
            allowed=allowed, ci=ci, required_ci=required_ci, cx=action.cx,
            escalation_paths=escalation_paths, effective_trust=eff_trust,
            adjusted_atp_cost=atp_cost, required_witnesses=witnesses)


# ============================================================================
# GROUNDING MANAGER (§6)
# ============================================================================

class GroundingManager:
    """Manages grounding lifecycle: announce → heartbeat → expire."""

    def __init__(self, weights: Optional[CoherenceWeights] = None):
        self.groundings: Dict[str, List[GroundingEdge]] = {}
        self.current: Dict[str, GroundingEdge] = {}
        self.calculator = CoherenceCalculator(weights)
        self.modulator = TrustModulator()
        self.gating = CXGatingEngine()
        self.travel_announcements: List[TravelAnnouncement] = []
        self.upgrade_events: List[UpgradeEvent] = []
        self.witness_verifications: Dict[str, List[WitnessVerification]] = {}
        self.mrh_neighborhoods: Dict[str, Set[str]] = {}

    def announce_grounding(self, entity: str, context: GroundingContext,
                           ttl: Optional[int] = None) -> GroundingEdge:
        """§6.1: Announce grounding, create edge, compute continuity token."""
        if ttl is None:
            ttl = DEFAULT_TTL.get(context.capabilities.hardware_class, 3600)

        # Continuity token from previous grounding
        if entity in self.current:
            last = self.current[entity]
            token = hashlib.sha256(last.edge_id.encode()).hexdigest()[:16]
            context.session.continuity_token = token

        now = datetime.now(timezone.utc)
        ts = now.isoformat()
        expires = (now + timedelta(seconds=ttl)).isoformat()
        edge_id = f"ground:{hashlib.sha256(f'{entity}:{ts}'.encode()).hexdigest()[:16]}"

        sig = hashlib.sha256(json.dumps(
            {"entity": entity, "context": context.to_dict(), "ts": ts},
            sort_keys=True).encode()).hexdigest()

        edge = GroundingEdge(edge_id=edge_id, source=entity, target=context,
                             timestamp=ts, ttl=ttl, expires_at=expires,
                             signature=sig)

        self.groundings.setdefault(entity, []).append(edge)
        self.current[entity] = edge
        return edge

    def heartbeat(self, entity: str, context: Optional[GroundingContext] = None) -> Optional[GroundingEdge]:
        """§6.2: Refresh grounding. If context changed significantly, re-announce."""
        if entity not in self.current:
            return None
        cur = self.current[entity]
        if context and self._context_changed(context, cur.target):
            return self.announce_grounding(entity, context, cur.ttl)
        # Extend TTL
        now = datetime.now(timezone.utc)
        cur.expires_at = (now + timedelta(seconds=cur.ttl)).isoformat()
        cur.status = EdgeStatus.REFRESHED
        return cur

    def expire_grounding(self, entity: str) -> bool:
        """§6.3: Mark current grounding as expired."""
        if entity not in self.current:
            return False
        self.current[entity].status = EdgeStatus.EXPIRED
        del self.current[entity]
        return True

    def verify_grounding(self, witness: str, entity: str,
                          method: str = "co-located") -> Optional[WitnessVerification]:
        """§6.4: Witness verifies grounding claim."""
        if entity not in self.current:
            return None
        edge = self.current[entity]
        ts = datetime.now(timezone.utc).isoformat()
        sig = hashlib.sha256(f"{witness}:{edge.edge_id}:{ts}".encode()).hexdigest()
        v = WitnessVerification(witness=witness, edge_id=edge.edge_id,
                                 timestamp=ts, method=method, signature=sig)
        edge.witness_set.append(witness)
        self.witness_verifications.setdefault(edge.edge_id, []).append(v)
        return v

    def announce_travel(self, entity: str, destination: str,
                        start: str, end: str, witnesses: Optional[List[str]] = None) -> TravelAnnouncement:
        """Pre-announce travel to reduce coherence penalty (§4.2)."""
        ta = TravelAnnouncement(entity=entity, destination_value=destination,
                                 start_time=start, end_time=end,
                                 witnessed_by=witnesses or [])
        self.travel_announcements.append(ta)
        return ta

    def record_upgrade(self, entity: str, new_caps: List[str],
                        witnesses: Optional[List[str]] = None) -> UpgradeEvent:
        """Record capability upgrade event (§4.3)."""
        ts = datetime.now(timezone.utc).isoformat()
        ue = UpgradeEvent(entity=entity, timestamp=ts,
                           new_capabilities=new_caps, witnessed_by=witnesses or [])
        self.upgrade_events.append(ue)
        return ue

    def set_mrh_neighborhood(self, entity: str, neighborhood: Set[str]):
        """Set entity's MRH neighborhood for relational coherence (§4.5)."""
        self.mrh_neighborhoods[entity] = neighborhood

    def get_coherence(self, entity: str) -> CoherenceBreakdown:
        """Calculate current CI for entity."""
        cur = self.current.get(entity)
        if not cur:
            return CoherenceBreakdown(0.0, 0.0, 0.0, 0.0, 0.0,
                                      self.calculator.weights)
        history = self.groundings.get(entity, [])[:-1]
        travel = [a for a in self.travel_announcements if a.entity == entity]
        upgrades = [u for u in self.upgrade_events if u.entity == entity]
        neighborhood = self.mrh_neighborhoods.get(entity)
        return self.calculator.compute(cur.target, history, travel,
                                        upgrades, neighborhood)

    def get_ci(self, entity: str) -> float:
        return self.get_coherence(entity).combined

    def check_action(self, entity: str, action: ActionSpec,
                      base_trust: float = 0.8) -> GatingResult:
        """CI/CX gating check for action execution."""
        ci = self.get_ci(entity)
        return self.gating.check(ci, action, base_trust)

    def get_effective_trust(self, entity: str, base_trust: float,
                             sensitivity: float = 1.0) -> float:
        ci = self.get_ci(entity)
        return self.modulator.effective_trust(base_trust, ci, sensitivity)

    def get_adjusted_atp_cost(self, entity: str, base_cost: float) -> float:
        ci = self.get_ci(entity)
        return self.modulator.adjusted_atp_cost(base_cost, ci)

    @staticmethod
    def _context_changed(a: GroundingContext, b: GroundingContext) -> bool:
        """Detect significant context change requiring re-announcement."""
        if a.location.value != b.location.value:
            return True
        if set(a.capabilities.advertised) != set(b.capabilities.advertised):
            return True
        if a.capabilities.hardware_class != b.capabilities.hardware_class:
            return True
        return False


# ============================================================================
# SECURITY SCENARIO ANALYZER (§9)
# ============================================================================

class SecurityAnalyzer:
    """Detects specific attack patterns from §9."""

    @staticmethod
    def detect_impossible_travel(history: List[GroundingEdge]) -> List[Tuple[str, str, float]]:
        """§9.1: Detect impossible travel between consecutive groundings."""
        violations = []
        for i in range(1, len(history)):
            prev = history[i-1]
            curr = history[i]
            if (prev.target.location.type == LocationType.PHYSICAL and
                curr.target.location.type == LocationType.PHYSICAL):
                dist = CoherenceCalculator._haversine(
                    prev.target.location.lat, prev.target.location.lon,
                    curr.target.location.lat, curr.target.location.lon)
                elapsed_h = max((datetime.fromisoformat(curr.timestamp.replace("Z", "+00:00")) -
                                  datetime.fromisoformat(prev.timestamp.replace("Z", "+00:00"))
                                  ).total_seconds() / 3600, 0.001)
                max_vel = MAX_VELOCITY.get(prev.target.capabilities.hardware_class, 1000)
                if max_vel > 0 and dist / elapsed_h > max_vel:
                    violations.append((prev.edge_id, curr.edge_id, dist / elapsed_h))
                elif max_vel == 0 and dist > 1:
                    violations.append((prev.edge_id, curr.edge_id, float('inf')))
        return violations

    @staticmethod
    def detect_capability_spoofing(history: List[GroundingEdge]) -> List[Tuple[str, Set[str]]]:
        """§9.1: Detect capabilities inconsistent with hardware class."""
        spoofs = []
        for e in history:
            expected = HARDWARE_CAPABILITIES.get(e.target.capabilities.hardware_class, set())
            actual = set(e.target.capabilities.advertised)
            excess = actual - expected
            if excess:
                spoofs.append((e.edge_id, excess))
        return spoofs

    @staticmethod
    def detect_history_poisoning(history: List[GroundingEdge],
                                  min_consistency_window: int = 10) -> bool:
        """§9.3: Detect attempt to build false history for cover."""
        if len(history) < min_consistency_window:
            return False
        # Check for suspiciously perfect consistency followed by sudden shift
        recent = history[-min_consistency_window:]
        patterns = [e.target.session.activity_pattern for e in recent]
        locations = [e.target.location.value for e in recent]
        # All identical → then sudden change = possible poisoning setup
        return (len(set(patterns)) == 1 and len(set(locations)) == 1
                and len(history) > min_consistency_window)


# ============================================================================
# RDF REPRESENTATION (§3.3)
# ============================================================================

class GroundingRDFSerializer:
    """Serialize grounding edges as Turtle (§3.3)."""

    @staticmethod
    def to_turtle(edge: GroundingEdge) -> str:
        loc = edge.target.location
        caps = edge.target.capabilities
        lines = [
            f'@prefix mrh: <https://web4.io/mrh#> .',
            f'@prefix ground: <https://web4.io/mrh/grounding#> .',
            f'@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .',
            f'',
            f'<{edge.source}> mrh:grounding [',
            f'    a ground:GroundingEdge ;',
            f'    ground:edgeId "{edge.edge_id}" ;',
            f'    ground:timestamp "{edge.timestamp}"^^xsd:dateTime ;',
            f'    ground:ttl "PT{edge.ttl}S"^^xsd:duration ;',
            f'    ground:status "{edge.status.value}" ;',
            f'    ground:location [',
            f'        ground:type "{loc.type.value}" ;',
            f'        ground:value "{loc.value}" ;',
            f'        ground:precision "{loc.precision.value}" ;',
            f'    ] ;',
            f'    ground:capabilities [',
            f'        ground:advertised ( {" ".join(repr(c) for c in caps.advertised)} ) ;',
            f'        ground:hardwareClass "{caps.hardware_class.value}" ;',
            f'    ] ;',
            f'    ground:signature "{edge.signature}" ;',
        ]
        if edge.witness_set:
            witnesses = " ".join(f'<{w}>' for w in edge.witness_set)
            lines.append(f'    ground:witnesses ( {witnesses} ) ;')
        if edge.target.session.continuity_token:
            lines.append(f'    ground:continuityToken "{edge.target.session.continuity_token}" ;')
        lines.append(f'] .')
        return "\n".join(lines)


# ============================================================================
# TESTS
# ============================================================================

def _ts(delta_minutes: float = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=delta_minutes)).isoformat()

def _loc(val: str, lat: float = 0.0, lon: float = 0.0,
         typ: LocationType = LocationType.PHYSICAL,
         prec: PrecisionLevel = PrecisionLevel.CITY,
         verifiable: bool = False) -> Location:
    return Location(type=typ, value=val, precision=prec,
                    verifiable=verifiable, lat=lat, lon=lon)

def _caps(advertised: List[str], hw: HardwareClass = HardwareClass.EDGE_DEVICE) -> Capabilities:
    return Capabilities(advertised=advertised, hardware_class=hw,
                        resource_state={"compute": "medium"})

def _ctx(loc: Location, caps: Capabilities,
         pattern: str = "pat_a", contexts: Optional[List[str]] = None) -> GroundingContext:
    return GroundingContext(location=loc, capabilities=caps,
                           session=SessionInfo(started=_ts(), activity_pattern=pattern),
                           active_contexts=contexts or [])


def run_tests():
    passed = 0
    failed = 0
    def check(name, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name}")

    # ================================================================
    # T1: Location types and precision levels
    # ================================================================
    print("T1: Location Types")
    check("T1.1 Physical location", LocationType.PHYSICAL.value == "physical")
    check("T1.2 Network location", LocationType.NETWORK.value == "network")
    check("T1.3 Logical location", LocationType.LOGICAL.value == "logical")
    check("T1.4 Precision exact", PrecisionLevel.EXACT.value == "exact")
    check("T1.5 Precision city", PrecisionLevel.CITY.value == "city")
    check("T1.6 Location to_dict", _loc("geo:45,-122").to_dict()["type"] == "physical")

    # ================================================================
    # T2: Hardware classes and expected capabilities
    # ================================================================
    print("T2: Hardware Classes")
    check("T2.1 Edge device capabilities", "sensors" in HARDWARE_CAPABILITIES[HardwareClass.EDGE_DEVICE])
    check("T2.2 Mobile capabilities", "gps" in HARDWARE_CAPABILITIES[HardwareClass.MOBILE])
    check("T2.3 Server capabilities", "database" in HARDWARE_CAPABILITIES[HardwareClass.SERVER])
    check("T2.4 Cluster capabilities", "gpu" in HARDWARE_CAPABILITIES[HardwareClass.CLUSTER])
    check("T2.5 Edge max velocity 0", MAX_VELOCITY[HardwareClass.EDGE_DEVICE] == 0)
    check("T2.6 Mobile max velocity 1000", MAX_VELOCITY[HardwareClass.MOBILE] == 1000)
    check("T2.7 Default TTL edge 3600", DEFAULT_TTL[HardwareClass.EDGE_DEVICE] == 3600)

    # ================================================================
    # T3: GroundingContext construction
    # ================================================================
    print("T3: GroundingContext")
    ctx = _ctx(_loc("portland", 45.52, -122.68), _caps(["compute", "storage"]))
    d = ctx.to_dict()
    check("T3.1 Context to_dict location", d["location"]["value"] == "portland")
    check("T3.2 Context to_dict capabilities", "compute" in d["capabilities"]["advertised"])
    check("T3.3 Context to_dict session", "activity_pattern" in d["session"])
    check("T3.4 Context active_contexts default", d["active_contexts"] == [])
    check("T3.5 Context surface default", d["surface"] is None)

    # ================================================================
    # T4: GroundingEdge lifecycle
    # ================================================================
    print("T4: GroundingEdge Lifecycle")
    mgr = GroundingManager()
    e1 = mgr.announce_grounding("lct:alice", _ctx(
        _loc("portland", 45.52, -122.68), _caps(["compute", "storage", "sensors"])))
    check("T4.1 Edge created", e1.edge_id.startswith("ground:"))
    check("T4.2 Edge source", e1.source == "lct:alice")
    check("T4.3 Edge active", e1.is_active())
    check("T4.4 Edge not expired", not e1.is_expired())
    check("T4.5 Edge signature present", len(e1.signature) == 64)
    check("T4.6 Edge stored", len(mgr.groundings["lct:alice"]) == 1)
    check("T4.7 Current grounding set", mgr.current["lct:alice"] == e1)

    # ================================================================
    # T5: Continuity token chain
    # ================================================================
    print("T5: Continuity Token Chain")
    e2 = mgr.announce_grounding("lct:alice", _ctx(
        _loc("portland", 45.52, -122.68), _caps(["compute", "storage", "sensors"])))
    expected_token = hashlib.sha256(e1.edge_id.encode()).hexdigest()[:16]
    check("T5.1 Continuity token set", e2.target.session.continuity_token == expected_token)
    check("T5.2 History grows", len(mgr.groundings["lct:alice"]) == 2)
    e3 = mgr.announce_grounding("lct:alice", _ctx(
        _loc("portland", 45.52, -122.68), _caps(["compute", "storage", "sensors"])))
    token3 = hashlib.sha256(e2.edge_id.encode()).hexdigest()[:16]
    check("T5.3 Chain continues", e3.target.session.continuity_token == token3)

    # ================================================================
    # T6: Coherence — no history (neutral)
    # ================================================================
    print("T6: Coherence No History")
    mgr2 = GroundingManager()
    mgr2.announce_grounding("lct:bob", _ctx(
        _loc("seattle", 47.61, -122.33), _caps(["compute"])))
    bd = mgr2.get_coherence("lct:bob")
    check("T6.1 Spatial neutral", bd.spatial == 0.5)
    check("T6.2 Temporal neutral", bd.temporal == 0.5)
    check("T6.3 Relational 1.0", bd.relational == 1.0)  # No contexts
    check("T6.4 Combined ~0.5-0.8", 0.4 <= bd.combined <= 0.85)

    # ================================================================
    # T7: Coherence — consistent location (high CI)
    # ================================================================
    print("T7: Coherence Consistent Location")
    mgr3 = GroundingManager()
    for _ in range(3):
        mgr3.announce_grounding("lct:carol", _ctx(
            _loc("portland", 45.52, -122.68), _caps(["compute", "storage", "sensors"]),
            pattern="pat_a", contexts=["soc:genesis"]))
    bd3 = mgr3.get_coherence("lct:carol")
    check("T7.1 Spatial = 1.0", bd3.spatial == 1.0)
    check("T7.2 Capability = 1.0", bd3.capability == 1.0)
    check("T7.3 Temporal = 1.0", bd3.temporal == 1.0)
    check("T7.4 Combined high", bd3.combined >= 0.9)

    # ================================================================
    # T8: Coherence — impossible travel (low CI)
    # ================================================================
    print("T8: Impossible Travel Detection")
    mgr4 = GroundingManager()
    # Build history in Portland
    for _ in range(3):
        mgr4.announce_grounding("lct:dave", _ctx(
            _loc("portland", 45.52, -122.68), _caps(["compute"], HardwareClass.WORKSTATION),
            pattern="pat_a"))
    # Sudden jump to Singapore
    mgr4.announce_grounding("lct:dave", _ctx(
        _loc("singapore", 1.35, 103.82), _caps(["compute"], HardwareClass.WORKSTATION),
        pattern="pat_a"))
    bd4 = mgr4.get_coherence("lct:dave")
    check("T8.1 Spatial low", bd4.spatial <= 0.5)
    check("T8.2 Combined low", bd4.combined < 0.7)
    # Security analyzer
    violations = SecurityAnalyzer.detect_impossible_travel(mgr4.groundings["lct:dave"])
    check("T8.3 Violation detected", len(violations) >= 1)
    check("T8.4 Violation velocity > max", violations[0][2] > MAX_VELOCITY[HardwareClass.WORKSTATION])

    # ================================================================
    # T9: Travel announcement reduces penalty
    # ================================================================
    print("T9: Travel Announcement")
    mgr5 = GroundingManager()
    for _ in range(3):
        mgr5.announce_grounding("lct:eve", _ctx(
            _loc("portland", 45.52, -122.68), _caps(["compute"], HardwareClass.MOBILE),
            pattern="pat_a"))
    mgr5.announce_travel("lct:eve", "berlin", _ts(-60), _ts(60*24))
    mgr5.announce_grounding("lct:eve", _ctx(
        _loc("berlin", 52.52, 13.41), _caps(["compute"], HardwareClass.MOBILE),
        pattern="pat_a"))
    bd5 = mgr5.get_coherence("lct:eve")
    check("T9.1 Spatial > 0.4 with travel announcement", bd5.spatial >= 0.4)
    # Compare without announcement
    mgr5b = GroundingManager()
    for _ in range(3):
        mgr5b.announce_grounding("lct:eve2", _ctx(
            _loc("portland", 45.52, -122.68), _caps(["compute"], HardwareClass.MOBILE),
            pattern="pat_a"))
    mgr5b.announce_grounding("lct:eve2", _ctx(
        _loc("berlin", 52.52, 13.41), _caps(["compute"], HardwareClass.MOBILE),
        pattern="pat_a"))
    bd5b = mgr5b.get_coherence("lct:eve2")
    check("T9.2 Travel announcement helps", bd5.spatial >= bd5b.spatial)

    # ================================================================
    # T10: Capability spoofing detection
    # ================================================================
    print("T10: Capability Spoofing")
    mgr6 = GroundingManager()
    mgr6.announce_grounding("lct:frank", _ctx(
        _loc("portland", 45.52, -122.68),
        _caps(["compute", "storage", "sensors", "gpu", "distributed"], HardwareClass.EDGE_DEVICE)))
    bd6 = mgr6.get_coherence("lct:frank")
    check("T10.1 Capability coherence < 1.0", bd6.capability < 1.0)
    spoofs = SecurityAnalyzer.detect_capability_spoofing(mgr6.groundings["lct:frank"])
    check("T10.2 Spoofing detected", len(spoofs) >= 1)
    check("T10.3 Excess capabilities found", "gpu" in spoofs[0][1] or "distributed" in spoofs[0][1])

    # ================================================================
    # T11: Upgrade event legitimizes new capabilities
    # ================================================================
    print("T11: Upgrade Events")
    mgr7 = GroundingManager()
    mgr7.announce_grounding("lct:grace", _ctx(
        _loc("portland", 45.52, -122.68), _caps(["compute", "storage"], HardwareClass.SERVER)))
    mgr7.record_upgrade("lct:grace", ["gpu"])
    mgr7.announce_grounding("lct:grace", _ctx(
        _loc("portland", 45.52, -122.68), _caps(["compute", "storage", "gpu"], HardwareClass.SERVER)))
    bd7 = mgr7.get_coherence("lct:grace")
    # Compare without upgrade
    mgr7b = GroundingManager()
    mgr7b.announce_grounding("lct:grace2", _ctx(
        _loc("portland", 45.52, -122.68), _caps(["compute", "storage"], HardwareClass.SERVER)))
    mgr7b.announce_grounding("lct:grace2", _ctx(
        _loc("portland", 45.52, -122.68), _caps(["compute", "storage", "gpu"], HardwareClass.SERVER)))
    bd7b = mgr7b.get_coherence("lct:grace2")
    check("T11.1 Upgrade helps capability coherence", bd7.capability >= bd7b.capability)

    # ================================================================
    # T12: Temporal coherence — broken continuity
    # ================================================================
    print("T12: Temporal Coherence")
    mgr8 = GroundingManager()
    mgr8.announce_grounding("lct:hank", _ctx(
        _loc("portland", 45.52, -122.68), _caps(["compute"]), pattern="pat_a"))
    # Manually break continuity token
    ctx_broken = _ctx(_loc("portland", 45.52, -122.68), _caps(["compute"]), pattern="pat_a")
    ctx_broken.session.continuity_token = "wrong_token"
    edge_broken = GroundingEdge(
        edge_id="ground:broken", source="lct:hank", target=ctx_broken,
        timestamp=_ts(), ttl=3600, expires_at=_ts(60),
        signature="sig_broken")
    mgr8.groundings["lct:hank"].append(edge_broken)
    mgr8.current["lct:hank"] = edge_broken
    bd8 = mgr8.get_coherence("lct:hank")
    check("T12.1 Broken continuity → low temporal", bd8.temporal == 0.3)

    # ================================================================
    # T13: Relational coherence — familiar vs novel contexts
    # ================================================================
    print("T13: Relational Coherence")
    mgr9 = GroundingManager()
    mgr9.announce_grounding("lct:iris", _ctx(
        _loc("portland", 45.52, -122.68), _caps(["compute"]),
        contexts=["soc:genesis", "soc:dev"]))
    mgr9.announce_grounding("lct:iris", _ctx(
        _loc("portland", 45.52, -122.68), _caps(["compute"]),
        contexts=["soc:genesis", "soc:dev"]))
    bd9a = mgr9.get_coherence("lct:iris")
    check("T13.1 Familiar contexts → high relational", bd9a.relational >= 0.9)

    # Novel contexts
    mgr9.announce_grounding("lct:iris", _ctx(
        _loc("portland", 45.52, -122.68), _caps(["compute"]),
        contexts=["soc:unknown1", "soc:unknown2"]))
    bd9b = mgr9.get_coherence("lct:iris")
    check("T13.2 Novel contexts → lower relational", bd9b.relational < bd9a.relational)

    # ================================================================
    # T14: MRH neighborhood
    # ================================================================
    print("T14: MRH Neighborhood")
    mgr10 = GroundingManager()
    mgr10.announce_grounding("lct:jake", _ctx(
        _loc("portland", 45.52, -122.68), _caps(["compute"]),
        contexts=["soc:alpha"]))
    mgr10.set_mrh_neighborhood("lct:jake", {"soc:alpha", "soc:beta"})
    mgr10.announce_grounding("lct:jake", _ctx(
        _loc("portland", 45.52, -122.68), _caps(["compute"]),
        contexts=["soc:alpha"]))
    bd10a = mgr10.get_coherence("lct:jake")
    check("T14.1 In neighborhood → high relational", bd10a.relational >= 0.9)
    mgr10.announce_grounding("lct:jake", _ctx(
        _loc("portland", 45.52, -122.68), _caps(["compute"]),
        contexts=["soc:gamma"]))  # Not in neighborhood
    bd10b = mgr10.get_coherence("lct:jake")
    check("T14.2 Outside neighborhood → lower relational", bd10b.relational < bd10a.relational)

    # ================================================================
    # T15: Trust modulation
    # ================================================================
    print("T15: Trust Modulation")
    tm = TrustModulator()
    check("T15.1 Full CI → full trust", tm.effective_trust(0.8, 1.0) == 0.8)
    check("T15.2 Zero CI → zero trust (sensitivity=1)", tm.effective_trust(0.8, 0.0, 1.0) == 0.0)
    check("T15.3 Half CI → reduced trust", 0.3 < tm.effective_trust(0.8, 0.5) < 0.8)
    check("T15.4 Low sensitivity → less modulation",
          tm.effective_trust(0.8, 0.5, 0.2) > tm.effective_trust(0.8, 0.5, 1.0))
    check("T15.5 ATP cost at CI=1.0", tm.adjusted_atp_cost(100, 1.0) == 100)
    check("T15.6 ATP cost at CI=0.5 > base", tm.adjusted_atp_cost(100, 0.5) > 100)
    check("T15.7 ATP cost capped at 10x", tm.adjusted_atp_cost(100, 0.1) <= 1000)
    check("T15.8 Witnesses at CI=0.9", tm.required_witnesses(1, 0.9) == 1)
    check("T15.9 Witnesses at CI=0.5", tm.required_witnesses(1, 0.5) >= 4)
    check("T15.10 Witnesses at CI=0.2", tm.required_witnesses(1, 0.2) >= 7)

    # ================================================================
    # T16: CX classification
    # ================================================================
    print("T16: Consequence Index Classification")
    check("T16.1 CX 0.1 → trivial", ActionSpec.classify(0.1) == CXLevel.TRIVIAL)
    check("T16.2 CX 0.3 → moderate", ActionSpec.classify(0.3) == CXLevel.MODERATE)
    check("T16.3 CX 0.6 → significant", ActionSpec.classify(0.6) == CXLevel.SIGNIFICANT)
    check("T16.4 CX 0.8 → high", ActionSpec.classify(0.8) == CXLevel.HIGH)
    check("T16.5 CX 0.95 → critical", ActionSpec.classify(0.95) == CXLevel.CRITICAL)

    # ================================================================
    # T17: CI/CX gating
    # ================================================================
    print("T17: CI/CX Gating")
    gating = CXGatingEngine()
    # Trivial action (CX=0.1) needs CI >= 0.36
    trivial = ActionSpec("a1", "read_log", 0.1, CXLevel.TRIVIAL)
    r1 = gating.check(0.5, trivial)
    check("T17.1 Trivial action allowed at CI=0.5", r1.allowed)
    check("T17.2 Required CI for trivial", 0.3 <= r1.required_ci <= 0.4)

    # Critical action (CX=0.95) needs CI >= 0.87
    critical = ActionSpec("a2", "delete_infrastructure", 0.95, CXLevel.CRITICAL, 100, 3)
    r2 = gating.check(0.5, critical)
    check("T17.3 Critical action blocked at CI=0.5", not r2.allowed)
    check("T17.4 Escalation paths provided", len(r2.escalation_paths) == 4)
    check("T17.5 DELEGATE in paths", EscalationPath.DELEGATE in r2.escalation_paths)

    r3 = gating.check(0.95, critical)
    check("T17.6 Critical action allowed at CI=0.95", r3.allowed)
    check("T17.7 No escalation needed", len(r3.escalation_paths) == 0)

    # Significant action (CX=0.6)
    deploy = ActionSpec("a3", "deploy_service", 0.6, CXLevel.SIGNIFICANT, 50, 1)
    r4 = gating.check(0.70, deploy)
    check("T17.8 Deploy allowed at CI=0.70", r4.allowed)
    r5 = gating.check(0.5, deploy)
    check("T17.9 Deploy blocked at CI=0.5", not r5.allowed)

    # ================================================================
    # T18: CI/CX trust modulation in gating result
    # ================================================================
    print("T18: Gating Result Details")
    r6 = gating.check(0.95, critical, base_trust=0.9)
    check("T18.1 Effective trust high at CI=0.95", r6.effective_trust > 0.85)
    check("T18.2 ATP cost ~base at CI=0.95", r6.adjusted_atp_cost <= 105)
    check("T18.3 Witnesses = base at CI=0.95", r6.required_witnesses == 3)

    r7 = gating.check(0.4, trivial, base_trust=0.9)
    check("T18.4 Effective trust reduced at CI=0.4", r7.effective_trust < 0.9)
    check("T18.5 ATP cost elevated at CI=0.4", r7.adjusted_atp_cost > 1.0)
    check("T18.6 Witnesses elevated at CI=0.4", r7.required_witnesses >= 4)

    # ================================================================
    # T19: Grounding heartbeat
    # ================================================================
    print("T19: Heartbeat")
    mgr11 = GroundingManager()
    e_hb = mgr11.announce_grounding("lct:kate", _ctx(
        _loc("portland", 45.52, -122.68), _caps(["compute"]), pattern="pat_a"))
    old_expires = e_hb.expires_at
    refreshed = mgr11.heartbeat("lct:kate")
    check("T19.1 Heartbeat returns edge", refreshed is not None)
    check("T19.2 TTL extended", refreshed.expires_at >= old_expires)
    check("T19.3 Status refreshed", refreshed.status == EdgeStatus.REFRESHED)
    # Heartbeat with changed context → re-announce
    new_ctx = _ctx(_loc("seattle", 47.61, -122.33), _caps(["compute"]), pattern="pat_a")
    re_announced = mgr11.heartbeat("lct:kate", new_ctx)
    check("T19.4 Changed context → new edge", re_announced.edge_id != e_hb.edge_id)
    check("T19.5 New location", re_announced.target.location.value == "seattle")

    # ================================================================
    # T20: Grounding expiration
    # ================================================================
    print("T20: Expiration")
    mgr12 = GroundingManager()
    e_exp = mgr12.announce_grounding("lct:leo", _ctx(
        _loc("portland", 45.52, -122.68), _caps(["compute"])), ttl=1)
    check("T20.1 Initially active", e_exp.is_active())
    # Simulate expiration by setting expires_at to past
    e_exp.expires_at = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    check("T20.2 Now expired", e_exp.is_expired())
    check("T20.3 No longer active", not e_exp.is_active())
    expired = mgr12.expire_grounding("lct:leo")
    check("T20.4 Expire returns True", expired)
    check("T20.5 No current grounding", "lct:leo" not in mgr12.current)
    ci_after = mgr12.get_ci("lct:leo")
    check("T20.6 CI = 0 after expiration", ci_after == 0.0)

    # ================================================================
    # T21: Witness verification
    # ================================================================
    print("T21: Witness Verification")
    mgr13 = GroundingManager()
    mgr13.announce_grounding("lct:mia", _ctx(
        _loc("portland", 45.52, -122.68), _caps(["compute"])))
    wv = mgr13.verify_grounding("lct:witness1", "lct:mia", "co-located")
    check("T21.1 Verification created", wv is not None)
    check("T21.2 Witness method", wv.method == "co-located")
    check("T21.3 Witness added to edge", "lct:witness1" in mgr13.current["lct:mia"].witness_set)
    wv2 = mgr13.verify_grounding("lct:witness2", "lct:mia", "network")
    check("T21.4 Multiple witnesses", len(mgr13.current["lct:mia"].witness_set) == 2)
    # Verifying nonexistent entity
    wv3 = mgr13.verify_grounding("lct:witness3", "lct:nobody")
    check("T21.5 Nonexistent entity → None", wv3 is None)

    # ================================================================
    # T22: Verified grounding improves spatial coherence
    # ================================================================
    print("T22: Witnessed Grounding")
    mgr14 = GroundingManager()
    for _ in range(3):
        mgr14.announce_grounding("lct:nina", _ctx(
            _loc("portland", 45.52, -122.68), _caps(["compute"], HardwareClass.MOBILE)))
    # Travel to Berlin with witness verification at destination
    mgr14.announce_grounding("lct:nina", _ctx(
        _loc("berlin", 52.52, 13.41, verifiable=True), _caps(["compute"], HardwareClass.MOBILE)))
    bd14 = mgr14.get_coherence("lct:nina")
    # Without verifiable
    mgr14b = GroundingManager()
    for _ in range(3):
        mgr14b.announce_grounding("lct:nina2", _ctx(
            _loc("portland", 45.52, -122.68), _caps(["compute"], HardwareClass.MOBILE)))
    mgr14b.announce_grounding("lct:nina2", _ctx(
        _loc("berlin", 52.52, 13.41, verifiable=False), _caps(["compute"], HardwareClass.MOBILE)))
    bd14b = mgr14b.get_coherence("lct:nina2")
    check("T22.1 Verified destination → better spatial", bd14.spatial >= bd14b.spatial)

    # ================================================================
    # T23: Logical and network locations
    # ================================================================
    print("T23: Logical/Network Locations")
    mgr15 = GroundingManager()
    mgr15.announce_grounding("lct:oscar", _ctx(
        _loc("soc:genesis", typ=LocationType.LOGICAL), _caps(["compute"])))
    mgr15.announce_grounding("lct:oscar", _ctx(
        _loc("soc:genesis", typ=LocationType.LOGICAL), _caps(["compute"])))
    bd15a = mgr15.get_coherence("lct:oscar")
    check("T23.1 Known logical location → high spatial", bd15a.spatial >= 0.9)
    mgr15.announce_grounding("lct:oscar", _ctx(
        _loc("soc:new_society", typ=LocationType.LOGICAL), _caps(["compute"])))
    bd15b = mgr15.get_coherence("lct:oscar")
    check("T23.2 New logical location → lower spatial", bd15b.spatial < bd15a.spatial)

    # Network location
    mgr16 = GroundingManager()
    mgr16.announce_grounding("lct:pete", _ctx(
        _loc("192.168.1.0/24", typ=LocationType.NETWORK), _caps(["compute"])))
    mgr16.announce_grounding("lct:pete", _ctx(
        _loc("192.168.1.0/24", typ=LocationType.NETWORK), _caps(["compute"])))
    bd16 = mgr16.get_coherence("lct:pete")
    check("T23.3 Known network → high spatial", bd16.spatial >= 0.85)

    # ================================================================
    # T24: Stationary device travel (impossible for edge/server)
    # ================================================================
    print("T24: Stationary Device Travel")
    mgr17 = GroundingManager()
    mgr17.announce_grounding("lct:server1", _ctx(
        _loc("dc-east", 38.9, -77.0), _caps(["compute", "storage", "network"], HardwareClass.SERVER)))
    mgr17.announce_grounding("lct:server1", _ctx(
        _loc("dc-west", 37.8, -122.4), _caps(["compute", "storage", "network"], HardwareClass.SERVER)))
    violations = SecurityAnalyzer.detect_impossible_travel(mgr17.groundings["lct:server1"])
    check("T24.1 Stationary device travel detected", len(violations) >= 1)
    check("T24.2 Infinite velocity for stationary", violations[0][2] == float('inf'))

    # ================================================================
    # T25: History poisoning detection
    # ================================================================
    print("T25: History Poisoning")
    mgr18 = GroundingManager()
    for _ in range(12):
        mgr18.announce_grounding("lct:poison", _ctx(
            _loc("portland", 45.52, -122.68), _caps(["compute"]), pattern="pat_x"))
    is_poison = SecurityAnalyzer.detect_history_poisoning(
        mgr18.groundings["lct:poison"], min_consistency_window=10)
    check("T25.1 Suspiciously perfect history detected", is_poison)
    # Short history
    is_not = SecurityAnalyzer.detect_history_poisoning(
        mgr18.groundings["lct:poison"][:5], min_consistency_window=10)
    check("T25.2 Short history → no poisoning flag", not is_not)

    # ================================================================
    # T26: CoherenceWeights normalization
    # ================================================================
    print("T26: Coherence Weights")
    w1 = CoherenceWeights(spatial=0.6, capability=0.6, temporal=0.4, relational=0.4)
    check("T26.1 Weights total", abs(w1.total() - 2.0) < 0.01)
    # Geometric mean still works with unnormalized — we normalize in compute
    calc = CoherenceCalculator(w1)
    check("T26.2 Calculator uses custom weights", calc.weights.spatial == 0.6)

    # ================================================================
    # T27: Haversine distance
    # ================================================================
    print("T27: Haversine Distance")
    # Portland to Singapore ~13,000 km
    d1 = CoherenceCalculator._haversine(45.52, -122.68, 1.35, 103.82)
    check("T27.1 Portland→Singapore ~13k km", 12000 < d1 < 14000)
    # Same point → 0
    d2 = CoherenceCalculator._haversine(45.52, -122.68, 45.52, -122.68)
    check("T27.2 Same point = 0 km", d2 < 0.01)
    # Portland to Seattle ~233 km
    d3 = CoherenceCalculator._haversine(45.52, -122.68, 47.61, -122.33)
    check("T27.3 Portland→Seattle ~233 km", 200 < d3 < 300)

    # ================================================================
    # T28: RDF Turtle serialization
    # ================================================================
    print("T28: RDF Serialization")
    mgr19 = GroundingManager()
    e_rdf = mgr19.announce_grounding("lct:rdf_test", _ctx(
        _loc("portland", 45.52, -122.68), _caps(["compute", "storage"])))
    mgr19.verify_grounding("lct:w1", "lct:rdf_test")
    turtle = GroundingRDFSerializer.to_turtle(mgr19.current["lct:rdf_test"])
    check("T28.1 Has @prefix mrh", "@prefix mrh:" in turtle)
    check("T28.2 Has ground:GroundingEdge", "ground:GroundingEdge" in turtle)
    check("T28.3 Has edge ID", "ground:edgeId" in turtle)
    check("T28.4 Has location", "ground:location" in turtle)
    check("T28.5 Has witnesses", "ground:witnesses" in turtle)
    check("T28.6 Has signature", "ground:signature" in turtle)

    # ================================================================
    # T29: Manager-level convenience methods
    # ================================================================
    print("T29: Manager Convenience")
    mgr20 = GroundingManager()
    for _ in range(3):
        mgr20.announce_grounding("lct:mgr", _ctx(
            _loc("portland", 45.52, -122.68), _caps(["compute", "storage", "sensors"])))
    eff = mgr20.get_effective_trust("lct:mgr", 0.8)
    check("T29.1 Effective trust computes", 0 < eff <= 0.8)
    cost = mgr20.get_adjusted_atp_cost("lct:mgr", 100)
    check("T29.2 ATP cost computes", cost >= 100)
    action = ActionSpec("a1", "read", 0.1, CXLevel.TRIVIAL)
    result = mgr20.check_action("lct:mgr", action)
    check("T29.3 Action check works", result.allowed)

    # ================================================================
    # T30: Hardware class change → low coherence
    # ================================================================
    print("T30: Hardware Class Change")
    mgr21 = GroundingManager()
    mgr21.announce_grounding("lct:hw_change", _ctx(
        _loc("portland", 45.52, -122.68), _caps(["compute", "storage", "sensors"], HardwareClass.EDGE_DEVICE)))
    mgr21.announce_grounding("lct:hw_change", _ctx(
        _loc("portland", 45.52, -122.68), _caps(["compute", "storage", "gpu", "distributed"], HardwareClass.CLUSTER)))
    bd30 = mgr21.get_coherence("lct:hw_change")
    check("T30.1 Hardware class change → low capability", bd30.capability < 0.5)

    # ================================================================
    # T31: E2E scenario
    # ================================================================
    print("T31: E2E Scenario")
    mgr22 = GroundingManager()
    entity = "lct:agent:sage_sprout"

    # Phase 1: Establish grounding with history
    for _ in range(5):
        mgr22.announce_grounding(entity, _ctx(
            _loc("portland", 45.52, -122.68), _caps(["compute", "storage", "sensors"]),
            contexts=["soc:genesis", "soc:dev"]))
    mgr22.set_mrh_neighborhood(entity, {"soc:genesis", "soc:dev", "soc:staging"})

    ci_stable = mgr22.get_ci(entity)
    check("T31.1 Stable CI high", ci_stable >= 0.85)

    # Phase 2: Trivial action → allowed
    trivial = ActionSpec("a1", "read_log", 0.05, CXLevel.TRIVIAL, 1, 0)
    r_trivial = mgr22.check_action(entity, trivial, 0.9)
    check("T31.2 Trivial action allowed", r_trivial.allowed)

    # Phase 3: Critical action → allowed (high CI)
    critical = ActionSpec("a2", "deploy_prod", 0.85, CXLevel.HIGH, 100, 2)
    r_critical = mgr22.check_action(entity, critical, 0.9)
    check("T31.3 Critical action allowed at high CI", r_critical.allowed)

    # Phase 4: Suspicious context shift
    mgr22.announce_grounding(entity, _ctx(
        _loc("singapore", 1.35, 103.82),
        _caps(["compute", "storage", "gpu", "distributed"], HardwareClass.CLUSTER),
        pattern="pat_different",
        contexts=["soc:unknown"]))

    ci_suspicious = mgr22.get_ci(entity)
    check("T31.4 CI dropped", ci_suspicious < ci_stable)

    # Phase 5: Critical action now blocked
    r_blocked = mgr22.check_action(entity, critical, 0.9)
    check("T31.5 Critical action blocked after shift", not r_blocked.allowed)
    check("T31.6 Escalation paths available", len(r_blocked.escalation_paths) > 0)

    # Phase 6: Trivial action still allowed
    r_trivial2 = mgr22.check_action(entity, trivial, 0.9)
    check("T31.7 Trivial action still allowed", r_trivial2.allowed)

    # Phase 7: Trust modulation
    eff_high = TrustModulator.effective_trust(0.9, ci_stable)
    eff_low = TrustModulator.effective_trust(0.9, ci_suspicious)
    check("T31.8 Trust reduced with low CI", eff_low < eff_high)
    check("T31.9 Cost increased with low CI",
          TrustModulator.adjusted_atp_cost(100, ci_suspicious) >
          TrustModulator.adjusted_atp_cost(100, ci_stable))
    check("T31.10 More witnesses with low CI",
          TrustModulator.required_witnesses(1, ci_suspicious) >=
          TrustModulator.required_witnesses(1, ci_stable))

    # ================================================================
    # T32: Edge cases
    # ================================================================
    print("T32: Edge Cases")
    # Empty entity
    empty_ci = mgr22.get_ci("lct:nonexistent")
    check("T32.1 Nonexistent entity CI = 0", empty_ci == 0.0)

    # Heartbeat on nonexistent entity
    hb = mgr22.heartbeat("lct:nonexistent")
    check("T32.2 Heartbeat nonexistent → None", hb is None)

    # Expire nonexistent entity
    exp = mgr22.expire_grounding("lct:nonexistent")
    check("T32.3 Expire nonexistent → False", not exp)

    # Zero CI → max ATP cost
    max_cost = TrustModulator.adjusted_atp_cost(100, 0.0)
    check("T32.4 Zero CI → 10× cost (capped)", max_cost == 1000)

    # CI = 1.0 → base cost
    base_cost = TrustModulator.adjusted_atp_cost(100, 1.0)
    check("T32.5 CI=1.0 → base cost", base_cost == 100)

    # CX threshold boundary
    threshold_0 = TrustModulator.ci_threshold_for_cx(0.0)
    threshold_1 = TrustModulator.ci_threshold_for_cx(1.0)
    check("T32.6 CX=0 threshold = 0.3", threshold_0 == 0.3)
    check("T32.7 CX=1 threshold ≈ 0.9", abs(threshold_1 - 0.9) < 0.001)

    # ================================================================
    print()
    print("=" * 60)
    total = passed + failed
    print(f"MRH Grounding & Coherence Index: {passed}/{total} checks passed")
    if failed == 0:
        print("  All checks passed!")
    else:
        print(f"  {failed} checks FAILED")
    print("=" * 60)
    return passed, failed


if __name__ == "__main__":
    run_tests()
