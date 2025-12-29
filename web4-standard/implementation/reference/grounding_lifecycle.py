#!/usr/bin/env python3
"""
Grounding Lifecycle Management - Phase 4 of MRH Grounding Implementation

Implements the operational lifecycle of grounding edges:
1. Announcement: Initial grounding broadcast to MRH neighborhood
2. Heartbeat: Periodic refresh and continuity chain maintenance
3. Expiration: Graceful degradation and verification
4. Verification: Witness verification of grounding claims

Key Concepts:
- **Announcement**: Entity declares current operational context to MRH neighborhood
- **Heartbeat**: Periodic refresh to prevent expiration, maintains continuity chain
- **Continuity Token**: Hash chain linking groundings (detects context switches)
- **TTL**: Time-to-live based on hardware class (mobile=5min, edge=15min, server=1hr)
- **Witness Verification**: Challenge-response to prove liveness and location
- **Graceful Degradation**: Expired grounding reduces CI, doesn't block operations
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Import grounding types
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from mrh_rdf_implementation import (
    GroundingEdge, GroundingContext, LocationContext,
    CapabilitiesContext, SessionContext, MRHGraph
)


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class GroundingTTLConfig:
    """
    Hardware-class-specific TTL defaults

    Different hardware classes have different mobility and stability profiles:
    - Servers: Stationary, long TTL (1 hour)
    - Edge devices: Semi-mobile, medium TTL (15 minutes)
    - Mobile devices: Highly mobile, short TTL (5 minutes)
    - IoT sensors: Stationary, very long TTL (24 hours)
    """
    ttl_server: timedelta = field(default_factory=lambda: timedelta(hours=1))
    ttl_edge_device: timedelta = field(default_factory=lambda: timedelta(minutes=15))
    ttl_mobile: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    ttl_browser: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    ttl_iot_sensor: timedelta = field(default_factory=lambda: timedelta(hours=24))

    # Grace period before hard expiration (allows network blips)
    grace_period: timedelta = field(default_factory=lambda: timedelta(minutes=2))

    # Heartbeat interval (fraction of TTL)
    heartbeat_interval_fraction: float = 0.5  # Heartbeat at 50% of TTL

    def ttl_for_hardware_class(self, hardware_class: str) -> timedelta:
        """Get TTL for a hardware class"""
        mapping = {
            'server': self.ttl_server,
            'edge-device': self.ttl_edge_device,
            'mobile': self.ttl_mobile,
            'browser': self.ttl_browser,
            'iot-sensor': self.ttl_iot_sensor,
        }
        return mapping.get(hardware_class, self.ttl_edge_device)

    def heartbeat_interval(self, hardware_class: str) -> timedelta:
        """Calculate heartbeat interval for a hardware class"""
        ttl = self.ttl_for_hardware_class(hardware_class)
        return ttl * self.heartbeat_interval_fraction


@dataclass
class ContextChangeThresholds:
    """
    Thresholds for detecting significant context changes

    When context changes exceed these thresholds, full re-announcement
    is required rather than simple TTL extension.
    """
    location_distance_km: float = 1.0  # 1 km movement triggers re-announce
    capability_change_count: int = 2    # Adding/removing 2+ capabilities
    active_context_change_ratio: float = 0.5  # 50% change in active contexts


class GroundingStatus(Enum):
    """Status of a grounding edge"""
    ACTIVE = "active"           # Currently valid
    EXPIRING = "expiring"       # In grace period
    EXPIRED = "expired"         # Past grace period
    REVOKED = "revoked"         # Manually revoked
    SUPERSEDED = "superseded"   # Replaced by newer grounding


# ============================================================================
# Continuity Token Chain
# ============================================================================

def generate_continuity_token(
    previous_grounding: Optional[GroundingEdge],
    current_context: GroundingContext,
    timestamp: str
) -> str:
    """
    Generate continuity token linking this grounding to previous

    The continuity token is a hash chain:
    - First grounding: hash(context + timestamp)
    - Subsequent: hash(previous_token + context + timestamp)

    This creates a tamper-evident chain of groundings that makes
    it difficult to fabricate historical groundings retroactively.

    Args:
        previous_grounding: Previous grounding edge (None for first)
        current_context: Current grounding context
        timestamp: ISO8601 timestamp for current grounding

    Returns:
        Hex-encoded continuity token (SHA256 hash)
    """
    hasher = hashlib.sha256()

    # Include previous token if exists
    if previous_grounding is not None:
        prev_token = getattr(previous_grounding, 'continuity_token', '')
        hasher.update(prev_token.encode('utf-8'))

    # Include current context (simplified serialization)
    hasher.update(current_context.location.value.encode('utf-8'))
    hasher.update(current_context.capabilities.hardware_class.encode('utf-8'))
    hasher.update(str(sorted(current_context.active_contexts)).encode('utf-8'))
    hasher.update(timestamp.encode('utf-8'))

    return hasher.hexdigest()


def validate_continuity_chain(
    grounding_history: List[GroundingEdge]
) -> Tuple[bool, Optional[str]]:
    """
    Validate continuity token chain in grounding history

    Ensures:
    1. Each grounding's continuity token correctly hashes from previous
    2. No gaps in the chain (excluding first grounding)
    3. Timestamps are monotonically increasing

    Args:
        grounding_history: List of groundings in chronological order

    Returns:
        (is_valid, error_message)
    """
    if not grounding_history:
        return (True, None)

    # First grounding has no predecessor
    for i, grounding in enumerate(grounding_history):
        if i == 0:
            continue

        # Check timestamp ordering
        prev_time = datetime.fromisoformat(grounding_history[i-1].timestamp)
        curr_time = datetime.fromisoformat(grounding.timestamp)
        if curr_time <= prev_time:
            return (False, f"Timestamp out of order at index {i}")

        # Validate continuity token
        expected_token = generate_continuity_token(
            grounding_history[i-1],
            grounding.target,
            grounding.timestamp
        )
        actual_token = getattr(grounding, 'continuity_token', '')

        if actual_token != expected_token:
            return (False, f"Continuity token mismatch at index {i}")

    return (True, None)


# ============================================================================
# Grounding Announcement
# ============================================================================

def announce_grounding(
    entity_lct: str,
    context: GroundingContext,
    mrh_graph: MRHGraph,
    config: GroundingTTLConfig,
    previous_grounding: Optional[GroundingEdge] = None,
    witness_set: Optional[List[str]] = None
) -> GroundingEdge:
    """
    Announce new grounding to MRH neighborhood

    Creates a grounding edge and broadcasts it to the entity's MRH neighborhood.
    This is called when:
    - Entity first comes online
    - Significant context change detected (location, capabilities, etc.)
    - Continuity chain needs to be established

    Args:
        entity_lct: LCT URI of entity making announcement
        context: Current grounding context
        mrh_graph: MRH graph to add grounding to
        config: TTL configuration
        previous_grounding: Previous grounding (for continuity)
        witness_set: Optional witnesses to this grounding

    Returns:
        Created GroundingEdge
    """
    timestamp = datetime.now().isoformat()
    ttl = config.ttl_for_hardware_class(context.capabilities.hardware_class)

    # Generate continuity token
    continuity_token = generate_continuity_token(previous_grounding, context, timestamp)

    # Create signature (simplified - in production would use actual LCT signing)
    signature_input = f"{entity_lct}:{timestamp}:{continuity_token}"
    signature = hashlib.sha256(signature_input.encode()).hexdigest()

    # Create grounding edge
    edge = GroundingEdge(
        source=entity_lct,
        target=context,
        timestamp=timestamp,
        ttl=ttl,
        signature=signature,
        witness_set=witness_set or []
    )

    # Add continuity token (not in base dataclass, added as attribute)
    edge.continuity_token = continuity_token

    # Add to MRH graph
    mrh_graph.add_grounding_edge(edge)

    # TODO: Gossip protocol broadcast to MRH neighborhood
    # This would distribute the grounding to relevant witnesses and peers

    return edge


# ============================================================================
# Context Change Detection
# ============================================================================

def detect_context_change(
    current: GroundingContext,
    previous: GroundingContext,
    thresholds: ContextChangeThresholds
) -> Tuple[bool, List[str]]:
    """
    Detect if context has changed significantly

    Returns:
        (has_significant_change, list_of_changes)
    """
    changes = []
    significant = False

    # Location change (simplified - would use geo_distance in production)
    if current.location.value != previous.location.value:
        changes.append(f"location: {previous.location.value} → {current.location.value}")
        # In production, calculate actual distance and compare to threshold
        significant = True

    # Capability changes
    curr_caps = set(current.capabilities.advertised)
    prev_caps = set(previous.capabilities.advertised)
    added = curr_caps - prev_caps
    removed = prev_caps - curr_caps

    if len(added) + len(removed) >= thresholds.capability_change_count:
        changes.append(f"capabilities: +{len(added)}, -{len(removed)}")
        significant = True

    # Hardware class change (always significant)
    if current.capabilities.hardware_class != previous.capabilities.hardware_class:
        changes.append(f"hardware_class: {previous.capabilities.hardware_class} → {current.capabilities.hardware_class}")
        significant = True

    # Active context changes
    curr_ctx = set(current.active_contexts)
    prev_ctx = set(previous.active_contexts)
    ctx_changed = len(curr_ctx.symmetric_difference(prev_ctx))
    ctx_total = max(len(curr_ctx), len(prev_ctx), 1)

    if ctx_changed / ctx_total >= thresholds.active_context_change_ratio:
        changes.append(f"active_contexts: {ctx_changed}/{ctx_total} changed")
        significant = True

    return (significant, changes)


# ============================================================================
# Grounding Heartbeat
# ============================================================================

def grounding_heartbeat(
    entity_lct: str,
    current_context: GroundingContext,
    current_grounding: GroundingEdge,
    mrh_graph: MRHGraph,
    config: GroundingTTLConfig,
    thresholds: ContextChangeThresholds
) -> Tuple[GroundingEdge, str]:
    """
    Periodic heartbeat to maintain grounding

    Called periodically (typically at 50% of TTL) to:
    1. Check if context has changed significantly
    2. If yes: Full re-announcement with new continuity token
    3. If no: Simple TTL extension (refresh)

    Args:
        entity_lct: Entity LCT URI
        current_context: Current sensed context
        current_grounding: Current active grounding
        mrh_graph: MRH graph
        config: TTL configuration
        thresholds: Context change thresholds

    Returns:
        (updated_or_new_grounding, action_taken)
    """
    # Check for significant context change
    has_change, changes = detect_context_change(
        current_context,
        current_grounding.target,
        thresholds
    )

    if has_change:
        # Significant change - full re-announcement
        new_grounding = announce_grounding(
            entity_lct,
            current_context,
            mrh_graph,
            config,
            previous_grounding=current_grounding,
            witness_set=current_grounding.witness_set
        )

        # Mark old grounding as superseded
        # (In production, would update status in graph store)

        action = f"re-announced (changes: {', '.join(changes)})"
        return (new_grounding, action)

    else:
        # No significant change - simple refresh
        # Extend TTL by creating new edge with same context
        refreshed = announce_grounding(
            entity_lct,
            current_grounding.target,  # Same context
            mrh_graph,
            config,
            previous_grounding=current_grounding,
            witness_set=current_grounding.witness_set
        )

        action = "refreshed (TTL extended)"
        return (refreshed, action)


# ============================================================================
# Grounding Expiration
# ============================================================================

def check_grounding_status(
    grounding: GroundingEdge,
    config: GroundingTTLConfig
) -> Tuple[GroundingStatus, Optional[timedelta]]:
    """
    Check current status of a grounding edge

    Returns:
        (status, time_remaining_or_overdue)
    """
    announced = datetime.fromisoformat(grounding.timestamp)
    now = datetime.now()

    ttl_expiry = announced + grounding.ttl
    grace_expiry = ttl_expiry + config.grace_period

    if now < ttl_expiry:
        remaining = ttl_expiry - now
        return (GroundingStatus.ACTIVE, remaining)

    elif now < grace_expiry:
        remaining = grace_expiry - now
        return (GroundingStatus.EXPIRING, remaining)

    else:
        overdue = now - grace_expiry
        return (GroundingStatus.EXPIRED, overdue)


def on_grounding_expired(
    entity_lct: str,
    expired_grounding: GroundingEdge,
    mrh_graph: MRHGraph,
    config: GroundingTTLConfig
) -> Dict[str, any]:
    """
    Handle grounding expiration

    When a grounding expires:
    1. Check if entity is still responsive (liveness probe)
    2. Mark grounding as expired in graph
    3. Calculate CI degradation (coherence suffers without fresh grounding)
    4. Return metadata for audit trail

    Args:
        entity_lct: Entity whose grounding expired
        expired_grounding: The expired grounding
        mrh_graph: MRH graph
        config: TTL configuration

    Returns:
        Expiration metadata dict
    """
    status, overdue = check_grounding_status(expired_grounding, config)

    # Calculate CI degradation
    # Expired grounding reduces spatial and temporal coherence
    if overdue:
        hours_overdue = overdue.total_seconds() / 3600
        # Exponential decay: 0.9^hours → 0.9 after 1hr, 0.81 after 2hr, etc.
        ci_multiplier = 0.9 ** hours_overdue
    else:
        ci_multiplier = 1.0

    metadata = {
        'entity_lct': entity_lct,
        'expired_at': expired_grounding.timestamp,
        'ttl': expired_grounding.ttl.total_seconds(),
        'overdue_seconds': overdue.total_seconds() if overdue else 0,
        'ci_multiplier': ci_multiplier,
        'status': status.value,
        'location_last_known': expired_grounding.target.location.value,
        'hardware_class': expired_grounding.target.capabilities.hardware_class,
    }

    # TODO: Liveness probe
    # In production, would attempt to contact entity via MRH
    # to check if it's still responsive

    # TODO: Update graph status
    # Mark grounding as expired in RDF store

    return metadata


# ============================================================================
# Witness Verification
# ============================================================================

@dataclass
class GroundingChallenge:
    """Challenge for witness verification"""
    challenge_id: str
    entity_lct: str
    challenger_lct: str
    challenge_type: str  # "liveness", "location", "capability"
    nonce: str
    timestamp: str

    @classmethod
    def create(cls, entity_lct: str, challenger_lct: str, challenge_type: str) -> 'GroundingChallenge':
        """Create a new challenge"""
        return cls(
            challenge_id=secrets.token_hex(16),
            entity_lct=entity_lct,
            challenger_lct=challenger_lct,
            challenge_type=challenge_type,
            nonce=secrets.token_hex(32),
            timestamp=datetime.now().isoformat()
        )


@dataclass
class GroundingResponse:
    """Response to grounding challenge"""
    challenge_id: str
    response_data: str
    signature: str
    timestamp: str


def verify_grounding(
    grounding: GroundingEdge,
    challenger_lct: str,
    challenge_type: str = "liveness"
) -> Tuple[bool, Optional[str]]:
    """
    Verify grounding via challenge-response

    Witnesses can challenge a grounding to verify:
    - Liveness: Is the entity still responsive?
    - Location: Can the entity prove it's at claimed location?
    - Capability: Can the entity demonstrate claimed capabilities?

    Args:
        grounding: Grounding to verify
        challenger_lct: LCT of entity issuing challenge
        challenge_type: Type of challenge

    Returns:
        (is_verified, error_message)
    """
    # Create challenge
    challenge = GroundingChallenge.create(
        grounding.source,
        challenger_lct,
        challenge_type
    )

    # TODO: Send challenge to entity
    # In production, would use MRH gossip protocol to deliver challenge

    # TODO: Receive and validate response
    # Entity would sign the challenge nonce to prove possession of LCT

    # For now, simplified verification based on grounding properties
    if challenge_type == "liveness":
        # Check if grounding is recent
        announced = datetime.fromisoformat(grounding.timestamp)
        age = datetime.now() - announced
        is_recent = age < timedelta(minutes=10)

        if not is_recent:
            return (False, f"Grounding too old: {age.total_seconds():.0f}s")

        return (True, None)

    elif challenge_type == "location":
        # Check if location is verifiable
        if not grounding.target.location.verifiable:
            return (False, "Location not verifiable")

        # In production, would check GPS attestation, IP geolocation, etc.
        return (True, None)

    elif challenge_type == "capability":
        # In production, would ask entity to demonstrate a claimed capability
        # e.g., "encode this image" if claiming vision capability
        return (True, None)

    else:
        return (False, f"Unknown challenge type: {challenge_type}")


# ============================================================================
# Grounding Manager
# ============================================================================

class GroundingManager:
    """
    Manages grounding lifecycle for an entity

    Handles:
    - Periodic heartbeats
    - Expiration detection
    - Continuity chain maintenance
    - Witness coordination
    """

    def __init__(
        self,
        entity_lct: str,
        mrh_graph: MRHGraph,
        config: Optional[GroundingTTLConfig] = None,
        thresholds: Optional[ContextChangeThresholds] = None
    ):
        self.entity_lct = entity_lct
        self.mrh_graph = mrh_graph
        self.config = config or GroundingTTLConfig()
        self.thresholds = thresholds or ContextChangeThresholds()

        self.current_grounding: Optional[GroundingEdge] = None
        self.grounding_history: List[GroundingEdge] = []

    def announce(self, context: GroundingContext, witness_set: Optional[List[str]] = None) -> GroundingEdge:
        """Announce new grounding"""
        grounding = announce_grounding(
            self.entity_lct,
            context,
            self.mrh_graph,
            self.config,
            previous_grounding=self.current_grounding,
            witness_set=witness_set
        )

        self.current_grounding = grounding
        self.grounding_history.append(grounding)

        return grounding

    def heartbeat(self, current_context: GroundingContext) -> Tuple[GroundingEdge, str]:
        """Perform heartbeat"""
        if self.current_grounding is None:
            # First grounding
            grounding = self.announce(current_context)
            return (grounding, "initial announcement")

        grounding, action = grounding_heartbeat(
            self.entity_lct,
            current_context,
            self.current_grounding,
            self.mrh_graph,
            self.config,
            self.thresholds
        )

        if action.startswith("re-announced"):
            self.grounding_history.append(grounding)

        self.current_grounding = grounding
        return (grounding, action)

    def check_status(self) -> Tuple[GroundingStatus, Optional[timedelta]]:
        """Check current grounding status"""
        if self.current_grounding is None:
            return (GroundingStatus.EXPIRED, None)

        return check_grounding_status(self.current_grounding, self.config)

    def validate_continuity(self) -> Tuple[bool, Optional[str]]:
        """Validate continuity chain"""
        return validate_continuity_chain(self.grounding_history)
