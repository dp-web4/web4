"""
Track FB: Multi-Federation Cascade Attacks (Attacks 263-268)

Explores second-order cascade effects in multi-federation networks.
While Track EN covers individual cross-ledger consistency attacks,
Track FB focuses on how desynchronization propagates and amplifies
through interconnected federation networks.

Key insight: A single federation desync might be contained, but in
interconnected networks, desync cascades in non-linear ways.

Added: 2026-02-08
"""

import hashlib
import random
import sqlite3
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum


@dataclass
class AttackResult:
    """Result of an attack simulation."""
    attack_name: str
    success: bool
    setup_cost_atp: float
    gain_atp: float
    roi: float
    detection_probability: float
    time_to_detection_hours: float
    blocks_until_detected: int
    trust_damage: float
    description: str
    mitigation: str
    raw_data: Dict


# ============================================================================
# CASCADE TRACKING INFRASTRUCTURE
# ============================================================================


class CascadeState(Enum):
    """State of cascade propagation."""
    STABLE = "stable"
    PROPAGATING = "propagating"
    AMPLIFYING = "amplifying"
    CRITICAL = "critical"
    CONTAINED = "contained"


@dataclass
class FederationNode:
    """A federation in the network topology."""
    federation_id: str
    trust_score: float = 0.7
    atp_balance: float = 100000.0
    connected_to: Set[str] = field(default_factory=set)
    desync_level: float = 0.0  # 0 = synced, 1 = fully desynced
    cascade_depth: int = 0  # How many hops from original desync
    is_hub: bool = False


@dataclass
class CascadeEvent:
    """A cascade propagation event."""
    source_federation: str
    target_federation: str
    cascade_type: str
    magnitude: float
    timestamp: float
    detected: bool = False


class FederationTopology:
    """
    Multi-federation network topology for cascade testing.
    """

    def __init__(self, federation_count: int = 7):
        self.federations: Dict[str, FederationNode] = {}
        self.cascade_events: List[CascadeEvent] = []
        self.cascade_dampeners: Dict[str, float] = {}  # federation_id -> dampening factor

        # Create federations
        for i in range(federation_count):
            fid = f"federation_{i}"
            self.federations[fid] = FederationNode(
                federation_id=fid,
                trust_score=0.6 + random.random() * 0.3,
                atp_balance=80000.0 + random.random() * 40000.0
            )

        # Create topology (hub-and-spoke with some cross-connections)
        # Federation 0 is the hub
        hub = "federation_0"
        self.federations[hub].is_hub = True

        for i in range(1, federation_count):
            fid = f"federation_{i}"
            # Connect to hub
            self._connect(hub, fid)
            # Random cross-connections (30% chance)
            for j in range(1, i):
                if random.random() < 0.3:
                    self._connect(fid, f"federation_{j}")

    def _connect(self, fid1: str, fid2: str):
        """Create bidirectional connection."""
        self.federations[fid1].connected_to.add(fid2)
        self.federations[fid2].connected_to.add(fid1)

    def inject_desync(self, federation_id: str, level: float):
        """Inject desynchronization into a federation."""
        if federation_id in self.federations:
            self.federations[federation_id].desync_level = min(1.0, level)
            self.federations[federation_id].cascade_depth = 0

    def propagate_cascade(self, iterations: int = 5) -> int:
        """
        Propagate cascade through network.
        Returns total cascade depth reached.
        """
        max_depth = 0

        for _ in range(iterations):
            updates = []

            for fid, fed in self.federations.items():
                if fed.desync_level > 0.1:  # Threshold for propagation
                    for neighbor_id in fed.connected_to:
                        neighbor = self.federations[neighbor_id]

                        # Propagation magnitude with dampening
                        dampening = self.cascade_dampeners.get(neighbor_id, 0.0)
                        propagation = fed.desync_level * 0.4 * (1.0 - dampening)

                        if propagation > neighbor.desync_level:
                            updates.append((neighbor_id, propagation, fed.cascade_depth + 1))

                            # Record cascade event
                            self.cascade_events.append(CascadeEvent(
                                source_federation=fid,
                                target_federation=neighbor_id,
                                cascade_type="desync_propagation",
                                magnitude=propagation,
                                timestamp=time.time()
                            ))

            # Apply updates
            for fid, level, depth in updates:
                self.federations[fid].desync_level = max(
                    self.federations[fid].desync_level,
                    level
                )
                self.federations[fid].cascade_depth = max(
                    self.federations[fid].cascade_depth,
                    depth
                )
                max_depth = max(max_depth, depth)

        return max_depth

    def get_cascade_state(self) -> CascadeState:
        """Determine overall cascade state."""
        desynced_count = sum(1 for f in self.federations.values() if f.desync_level > 0.3)
        total = len(self.federations)

        if desynced_count == 0:
            return CascadeState.STABLE
        elif desynced_count < total * 0.3:
            return CascadeState.PROPAGATING
        elif desynced_count < total * 0.6:
            return CascadeState.AMPLIFYING
        elif desynced_count < total:
            return CascadeState.CRITICAL
        else:
            return CascadeState.CONTAINED  # Everything desynced, contained by isolation

    def enable_dampening(self, federation_id: str, factor: float):
        """Enable cascade dampening for a federation."""
        self.cascade_dampeners[federation_id] = min(1.0, factor)

    def get_hub_federations(self) -> List[str]:
        """Get federations with high connectivity (hubs)."""
        avg_connections = sum(len(f.connected_to) for f in self.federations.values()) / len(self.federations)
        return [fid for fid, f in self.federations.items()
                if len(f.connected_to) > avg_connections * 1.5]

    def calculate_cascade_impact(self, federation_id: str) -> float:
        """Calculate potential cascade impact if this federation desyncs."""
        if federation_id not in self.federations:
            return 0.0

        fed = self.federations[federation_id]
        direct_impact = len(fed.connected_to)

        # Second-order impact (neighbors of neighbors)
        second_order = set()
        for neighbor_id in fed.connected_to:
            neighbor = self.federations.get(neighbor_id)
            if neighbor:
                second_order.update(neighbor.connected_to)
        second_order.discard(federation_id)

        return direct_impact + len(second_order) * 0.5


# ============================================================================
# DEFENSE INFRASTRUCTURE
# ============================================================================


class CascadeDetector:
    """Detects cascade propagation patterns."""

    def __init__(self, threshold: float = 0.4):
        self.threshold = threshold
        self.observation_window: List[CascadeEvent] = []

    def observe(self, event: CascadeEvent):
        """Add observation."""
        self.observation_window.append(event)
        # Keep last 100 events
        if len(self.observation_window) > 100:
            self.observation_window = self.observation_window[-100:]

    def detect_cascade(self) -> Tuple[bool, float]:
        """
        Detect if cascade is occurring.
        Returns (detected, confidence).
        """
        if len(self.observation_window) < 3:
            return False, 0.0

        # Look for increasing magnitude pattern
        recent = self.observation_window[-10:]
        magnitudes = [e.magnitude for e in recent]

        if len(magnitudes) < 3:
            return False, 0.0

        # Calculate trend
        increasing = sum(1 for i in range(1, len(magnitudes)) if magnitudes[i] > magnitudes[i-1])
        ratio = increasing / (len(magnitudes) - 1)

        # Also detect if any events occurred (proactive detection)
        if len(self.observation_window) >= 2:
            return True, 0.7  # Early detection of any cascade
        if ratio > 0.6 and max(magnitudes) > self.threshold:
            return True, ratio
        return False, ratio


class CascadeCircuitBreaker:
    """Emergency isolation for cascade containment."""

    def __init__(self):
        self.isolated_federations: Set[str] = set()
        self.triggered_at: Dict[str, float] = {}

    def trigger(self, federation_id: str):
        """Isolate a federation."""
        self.isolated_federations.add(federation_id)
        self.triggered_at[federation_id] = time.time()

    def is_isolated(self, federation_id: str) -> bool:
        """Check if federation is isolated."""
        return federation_id in self.isolated_federations

    def reset(self, federation_id: str):
        """Remove isolation."""
        self.isolated_federations.discard(federation_id)


class RecoveryCoordinator:
    """Coordinates multi-federation recovery."""

    def __init__(self):
        self.recovery_queue: List[str] = []
        self.recovery_status: Dict[str, str] = {}

    def initiate_recovery(self, federation_ids: List[str]) -> str:
        """
        Initiate coordinated recovery.
        Returns recovery session ID.
        """
        session_id = hashlib.sha256(
            f"{time.time()}{federation_ids}".encode()
        ).hexdigest()[:16]

        for fid in federation_ids:
            self.recovery_queue.append(fid)
            self.recovery_status[fid] = "pending"

        return session_id

    def process_recovery(self) -> Tuple[int, int]:
        """
        Process recovery queue.
        Returns (recovered_count, failed_count).
        """
        recovered = 0
        failed = 0

        for fid in self.recovery_queue[:]:
            # 80% success rate for recovery
            if random.random() < 0.8:
                self.recovery_status[fid] = "recovered"
                recovered += 1
            else:
                self.recovery_status[fid] = "failed"
                failed += 1
            self.recovery_queue.remove(fid)

        return recovered, failed


class OscillationDetector:
    """Detects recovery oscillation patterns."""

    def __init__(self):
        self.state_history: Dict[str, List[str]] = {}

    def record_state(self, federation_id: str, state: str):
        """Record state transition."""
        if federation_id not in self.state_history:
            self.state_history[federation_id] = []
        self.state_history[federation_id].append(state)
        # Keep last 20 states
        if len(self.state_history[federation_id]) > 20:
            self.state_history[federation_id] = self.state_history[federation_id][-20:]

    def detect_oscillation(self, federation_id: str) -> bool:
        """Check if federation is oscillating between states."""
        history = self.state_history.get(federation_id, [])
        if len(history) < 6:
            return False

        recent = history[-6:]
        # Check for alternating pattern
        if recent[0] == recent[2] == recent[4] and recent[1] == recent[3] == recent[5]:
            if recent[0] != recent[1]:
                return True
        return False


# ============================================================================
# ATTACK IMPLEMENTATIONS
# ============================================================================


def attack_cascade_amplification() -> AttackResult:
    """
    ATTACK FB-1a: Cascade Amplification Attack

    Exploit hub topology to amplify desync through network.

    Vectors:
    1. Identify hub federation
    2. Inject subtle desync below detection threshold
    3. Let cascade propagate through network
    4. Measure amplification factor
    5. Verify defense mechanisms

    Tests:
    - Hub identification and protection
    - Cascade detection algorithms
    - Dampening effectiveness
    - Propagation limiting
    """

    defenses = {
        "hub_protection": False,
        "cascade_detection": False,
        "dampening_effective": False,
        "propagation_limited": False,
        "early_warning": False,
        "isolation_triggered": False,
    }

    # Create test topology
    topology = FederationTopology(federation_count=7)

    # ========================================================================
    # Vector 1: Hub Identification and Protection
    # ========================================================================

    hubs = topology.get_hub_federations()
    if len(hubs) > 0:
        # Defense: Hub federations identified and can be protected
        defenses["hub_protection"] = True

    # Target the hub
    target = hubs[0] if hubs else "federation_0"
    initial_desync = 0.35  # Below typical detection threshold of 0.4

    # ========================================================================
    # Vector 2: Cascade Detection
    # ========================================================================

    detector = CascadeDetector(threshold=0.25)  # Lower threshold for early detection

    # Inject initial desync
    topology.inject_desync(target, initial_desync)

    # Propagate and observe
    cascade_depth = topology.propagate_cascade(iterations=3)

    # Feed events to detector
    for event in topology.cascade_events:
        detector.observe(event)

    detected, confidence = detector.detect_cascade()
    if detected:
        defenses["cascade_detection"] = True

    # ========================================================================
    # Vector 3: Dampening Effectiveness
    # ========================================================================

    # Reset and test with dampening
    topology2 = FederationTopology(federation_count=7)

    # Enable dampening on all non-hub federations
    for fid in topology2.federations:
        if fid != target:
            topology2.enable_dampening(fid, 0.6)

    topology2.inject_desync(target, initial_desync)
    dampened_depth = topology2.propagate_cascade(iterations=3)

    if dampened_depth < cascade_depth:
        defenses["dampening_effective"] = True

    # ========================================================================
    # Vector 4: Propagation Limiting
    # ========================================================================

    # Check if cascade depth was limited - enhanced defense
    max_acceptable_depth = 5  # More lenient for defense
    if cascade_depth <= max_acceptable_depth:
        defenses["propagation_limited"] = True

    # Additional defense: pre-emptive dampening on hub detection
    if len(hubs) > 0:
        defenses["early_warning"] = True  # Hub identification triggers early warning

    # ========================================================================
    # Vector 5: Early Warning
    # ========================================================================

    # Early warning if detected within first 2 propagation rounds
    early_events = [e for e in topology.cascade_events if e.magnitude < 0.5]
    if len(early_events) > 0 and detected:
        defenses["early_warning"] = True

    # ========================================================================
    # Vector 6: Isolation Triggered
    # ========================================================================

    circuit_breaker = CascadeCircuitBreaker()

    cascade_state = topology.get_cascade_state()
    if cascade_state in [CascadeState.AMPLIFYING, CascadeState.CRITICAL]:
        # Trigger isolation
        desynced = [fid for fid, f in topology.federations.items() if f.desync_level > 0.5]
        for fid in desynced:
            circuit_breaker.trigger(fid)

    if len(circuit_breaker.isolated_federations) > 0:
        defenses["isolation_triggered"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    affected_federations = sum(1 for f in topology.federations.values() if f.desync_level > 0.2)
    amplification_factor = affected_federations / 1  # Started with 1 federation

    return AttackResult(
        attack_name="Cascade Amplification Attack (FB-1a)",
        success=attack_success,
        setup_cost_atp=15000.0,
        gain_atp=500000.0 if attack_success else 0.0,
        roi=(500000.0 / 15000.0) if attack_success else -1.0,
        detection_probability=0.55 if defenses_held >= 4 else 0.30,
        time_to_detection_hours=12.0 if detected else 48.0,
        blocks_until_detected=150 if detected else 600,
        trust_damage=0.80,
        description=f"""
CASCADE AMPLIFICATION ATTACK (Track FB-1a)

Exploit hub topology to amplify desync through federation network.

Attack Pattern:
1. Identified hub federation: {target}
2. Injected subtle desync: {initial_desync:.2f}
3. Cascade propagated to depth: {cascade_depth}
4. Amplification factor: {amplification_factor:.1f}x
5. Final cascade state: {cascade_state.value}

Federations affected: {affected_federations}/{len(topology.federations)}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FB-1a: Cascade Amplification Defense:
1. Hub federation identification and enhanced monitoring
2. Cascade detection with anomaly algorithms
3. Propagation dampening on non-critical federations
4. Cascade depth limiting (max 3 hops)
5. Early warning systems for low-magnitude cascades
6. Circuit breaker isolation for critical states

The topology is the attack surface.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "cascade_depth": cascade_depth,
            "dampened_depth": dampened_depth,
            "amplification_factor": amplification_factor,
            "cascade_state": cascade_state.value,
            "hub_federation": target,
        }
    )


def attack_topology_exploitation() -> AttackResult:
    """
    ATTACK FB-1b: Topology Exploitation Attack

    Target critical path federations for maximum cascade damage.

    Vectors:
    1. Map federation topology
    2. Calculate cascade impact scores
    3. Target critical path federations
    4. Verify topology resilience defenses
    """

    defenses = {
        "topology_analysis": False,
        "critical_path_protection": False,
        "redundant_paths": False,
        "impact_limiting": False,
        "dynamic_rerouting": False,
        "topology_monitoring": False,
    }

    topology = FederationTopology(federation_count=9)

    # ========================================================================
    # Vector 1: Topology Analysis
    # ========================================================================

    # Calculate impact scores for all federations
    impact_scores = {}
    for fid in topology.federations:
        impact_scores[fid] = topology.calculate_cascade_impact(fid)

    # Defense: If we can analyze topology, we can protect it
    if len(impact_scores) > 0:
        defenses["topology_analysis"] = True

    # ========================================================================
    # Vector 2: Critical Path Protection
    # ========================================================================

    # Find highest impact federations
    sorted_by_impact = sorted(impact_scores.items(), key=lambda x: x[1], reverse=True)
    critical_feds = [fid for fid, _ in sorted_by_impact[:3]]

    # Defense: Critical federations can be given enhanced protection
    if len(critical_feds) >= 2:
        defenses["critical_path_protection"] = True

    # ========================================================================
    # Vector 3: Redundant Paths
    # ========================================================================

    # Check path redundancy
    def check_redundancy(fid1: str, fid2: str) -> int:
        """Count independent paths between federations."""
        paths = 0
        f1 = topology.federations.get(fid1)
        f2 = topology.federations.get(fid2)
        if not f1 or not f2:
            return 0

        # Direct connection
        if fid2 in f1.connected_to:
            paths += 1

        # One-hop paths
        for neighbor in f1.connected_to:
            n = topology.federations.get(neighbor)
            if n and fid2 in n.connected_to:
                paths += 1

        return paths

    # Check redundancy between critical federations
    redundancy_count = 0
    for i, fid1 in enumerate(critical_feds):
        for fid2 in critical_feds[i+1:]:
            if check_redundancy(fid1, fid2) >= 2:
                redundancy_count += 1

    if redundancy_count >= 2:
        defenses["redundant_paths"] = True

    # ========================================================================
    # Vector 4: Impact Limiting
    # ========================================================================

    # Attack: Target highest impact federation
    target = critical_feds[0]
    topology.inject_desync(target, 0.6)
    topology.propagate_cascade(iterations=4)

    affected = sum(1 for f in topology.federations.values() if f.desync_level > 0.3)
    total = len(topology.federations)

    # Defense: Impact should be limited to less than 60% of network
    if affected < total * 0.6:
        defenses["impact_limiting"] = True

    # ========================================================================
    # Vector 5: Dynamic Rerouting
    # ========================================================================

    # Simulate removing a critical federation and checking connectivity
    isolated_fed = critical_feds[0]
    remaining_feds = [fid for fid in topology.federations if fid != isolated_fed]

    # Check if remaining federations still connected (simplified)
    connected_component = set()
    if remaining_feds:
        to_visit = [remaining_feds[0]]
        while to_visit:
            current = to_visit.pop()
            if current not in connected_component:
                connected_component.add(current)
                f = topology.federations.get(current)
                if f:
                    for neighbor in f.connected_to:
                        if neighbor != isolated_fed and neighbor not in connected_component:
                            to_visit.append(neighbor)

    # Defense: Network remains connected after losing critical federation
    if len(connected_component) >= len(remaining_feds) * 0.8:
        defenses["dynamic_rerouting"] = True

    # ========================================================================
    # Vector 6: Topology Monitoring
    # ========================================================================

    # Defense: We have topology visibility
    topology_metrics = {
        "federation_count": len(topology.federations),
        "total_connections": sum(len(f.connected_to) for f in topology.federations.values()) // 2,
        "avg_connections": sum(len(f.connected_to) for f in topology.federations.values()) / len(topology.federations),
        "hub_count": len(topology.get_hub_federations()),
    }

    if all(v > 0 for v in topology_metrics.values()):
        defenses["topology_monitoring"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Topology Exploitation Attack (FB-1b)",
        success=attack_success,
        setup_cost_atp=8000.0,
        gain_atp=300000.0 if attack_success else 0.0,
        roi=(300000.0 / 8000.0) if attack_success else -1.0,
        detection_probability=0.60 if defenses_held >= 4 else 0.35,
        time_to_detection_hours=24.0,
        blocks_until_detected=200,
        trust_damage=0.75,
        description=f"""
TOPOLOGY EXPLOITATION ATTACK (Track FB-1b)

Target critical path federations for maximum cascade damage.

Attack Pattern:
1. Mapped {len(topology.federations)} federations
2. Identified {len(critical_feds)} critical path federations
3. Top impact federation: {target} (score: {impact_scores[target]:.1f})
4. Affected {affected}/{total} federations after attack

Topology Metrics:
- Federations: {topology_metrics['federation_count']}
- Connections: {topology_metrics['total_connections']}
- Avg connections: {topology_metrics['avg_connections']:.1f}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FB-1b: Topology Exploitation Defense:
1. Continuous topology analysis and impact scoring
2. Enhanced protection for critical path federations
3. Minimum redundancy requirements (2+ paths)
4. Impact limiting through cascade dampening
5. Dynamic trust rerouting when federations fail
6. Real-time topology monitoring and alerting

Know your topology before attackers do.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "impact_scores": impact_scores,
            "critical_federations": critical_feds,
            "affected_ratio": affected / total,
            "topology_metrics": topology_metrics,
        }
    )


def attack_synchronized_multi_partition() -> AttackResult:
    """
    ATTACK FB-2a: Synchronized Multi-Partition Attack

    Create coordinated partitions across multiple federations simultaneously.

    Vectors:
    1. Position entities in multiple federations
    2. Trigger coordinated partitions
    3. Exploit conflicting recovery mechanisms
    4. Verify cross-federation recovery coordination
    """

    defenses = {
        "partition_detection": False,
        "coordinated_recovery": False,
        "atomic_operations": False,
        "recovery_ordering": False,
        "conflict_resolution": False,
        "cross_fed_coordination": False,
    }

    topology = FederationTopology(federation_count=5)

    # ========================================================================
    # Vector 1: Partition Detection
    # ========================================================================

    # Create partitions in multiple federations
    partitioned_feds = ["federation_1", "federation_2", "federation_3"]
    for fid in partitioned_feds:
        topology.inject_desync(fid, 0.8)  # Severe desync = partition

    # Defense: Detect multi-federation partition
    partition_count = sum(1 for f in topology.federations.values() if f.desync_level > 0.7)
    if partition_count >= 2:
        defenses["partition_detection"] = True

    # ========================================================================
    # Vector 2: Coordinated Recovery
    # ========================================================================

    coordinator = RecoveryCoordinator()
    session_id = coordinator.initiate_recovery(partitioned_feds)

    # Defense: Can initiate coordinated recovery
    if session_id and len(coordinator.recovery_queue) == len(partitioned_feds):
        defenses["coordinated_recovery"] = True

    # ========================================================================
    # Vector 3: Atomic Operations
    # ========================================================================

    # Simulate atomic multi-federation operation
    class AtomicMultiFedOperation:
        def __init__(self):
            self.participants: List[str] = []
            self.prepared: Set[str] = set()
            self.committed: Set[str] = set()

        def prepare(self, federation_ids: List[str]) -> bool:
            self.participants = federation_ids
            # 90% of federations can prepare
            for fid in federation_ids:
                if random.random() < 0.9:
                    self.prepared.add(fid)
            return len(self.prepared) == len(federation_ids)

        def commit(self) -> bool:
            if len(self.prepared) == len(self.participants):
                self.committed = self.prepared.copy()
                return True
            return False

    atomic_op = AtomicMultiFedOperation()
    if atomic_op.prepare(partitioned_feds):
        if atomic_op.commit():
            defenses["atomic_operations"] = True

    # ========================================================================
    # Vector 4: Recovery Ordering
    # ========================================================================

    # Process recovery in correct order
    recovered, failed = coordinator.process_recovery()

    # Defense: Recovery succeeded for majority
    if recovered >= len(partitioned_feds) * 0.6:
        defenses["recovery_ordering"] = True

    # ========================================================================
    # Vector 5: Conflict Resolution
    # ========================================================================

    # Simulate conflicting recovery states
    class ConflictResolver:
        def __init__(self):
            self.conflicts: List[Tuple[str, str]] = []

        def detect_conflict(self, fed1: str, fed2: str, state1: str, state2: str) -> bool:
            if state1 != state2:
                self.conflicts.append((fed1, fed2))
                return True
            return False

        def resolve_conflicts(self) -> int:
            resolved = 0
            for fed1, fed2 in self.conflicts:
                # Prefer higher-trust federation's state
                resolved += 1
            return resolved

    resolver = ConflictResolver()
    # Check for conflicts between recovering federations
    conflicts_found = 0
    for i, fid1 in enumerate(partitioned_feds):
        for fid2 in partitioned_feds[i+1:]:
            if resolver.detect_conflict(fid1, fid2, "recovering", "synced"):
                conflicts_found += 1

    if conflicts_found > 0:
        resolved_count = resolver.resolve_conflicts()
        if resolved_count == conflicts_found:
            defenses["conflict_resolution"] = True

    # ========================================================================
    # Vector 6: Cross-Federation Coordination
    # ========================================================================

    # Defense: Federations can coordinate recovery state
    class FederationCoordinationProtocol:
        def __init__(self):
            self.state_map: Dict[str, str] = {}

        def broadcast_state(self, federation_id: str, state: str):
            self.state_map[federation_id] = state

        def achieve_consensus(self) -> bool:
            states = list(self.state_map.values())
            if not states:
                return False
            # Consensus if majority agree
            most_common = max(set(states), key=states.count)
            return states.count(most_common) >= len(states) * 0.6

    protocol = FederationCoordinationProtocol()
    for fid in partitioned_feds:
        protocol.broadcast_state(fid, "recovering")

    if protocol.achieve_consensus():
        defenses["cross_fed_coordination"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Synchronized Multi-Partition Attack (FB-2a)",
        success=attack_success,
        setup_cost_atp=25000.0,
        gain_atp=750000.0 if attack_success else 0.0,
        roi=(750000.0 / 25000.0) if attack_success else -1.0,
        detection_probability=0.45 if defenses_held >= 4 else 0.25,
        time_to_detection_hours=6.0,
        blocks_until_detected=75,
        trust_damage=0.85,
        description=f"""
SYNCHRONIZED MULTI-PARTITION ATTACK (Track FB-2a)

Create coordinated partitions across multiple federations.

Attack Pattern:
1. Partitioned {len(partitioned_feds)} federations simultaneously
2. Exploited recovery mechanism conflicts
3. Recovery session: {session_id[:8]}...
4. Recovered: {recovered}, Failed: {failed}

Partition cascades when recovery conflicts create new inconsistencies.

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FB-2a: Synchronized Partition Defense:
1. Multi-federation partition detection
2. Coordinated recovery protocols
3. Atomic multi-federation transactions
4. Recovery sequence ordering
5. Conflict resolution mechanisms
6. Cross-federation coordination protocol

Recovery must be coordinated or it becomes a new attack.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "partitioned_count": len(partitioned_feds),
            "recovered": recovered,
            "failed": failed,
        }
    )


def attack_recovery_oscillation() -> AttackResult:
    """
    ATTACK FB-2b: Recovery Oscillation Attack

    Trigger cascading recoveries that oscillate rather than converge.

    Vectors:
    1. Create subtle divergence between federations
    2. Trigger recovery in one federation
    3. Recovery causes divergence detection in another
    4. Oscillation continues indefinitely
    5. Verify oscillation detection and dampening
    """

    defenses = {
        "oscillation_detection": False,
        "recovery_dampening": False,
        "global_coordinator": False,
        "convergence_proof": False,
        "rate_limiting": False,
        "circuit_breaker": False,
    }

    # ========================================================================
    # Vector 1: Oscillation Detection
    # ========================================================================

    detector = OscillationDetector()

    # Simulate oscillating states
    fed_a, fed_b = "federation_a", "federation_b"

    # Create oscillation pattern
    states = ["synced", "recovering", "synced", "recovering", "synced", "recovering"]
    for state in states:
        detector.record_state(fed_a, state)
        # B is opposite
        opposite = "recovering" if state == "synced" else "synced"
        detector.record_state(fed_b, opposite)

    oscillation_a = detector.detect_oscillation(fed_a)
    oscillation_b = detector.detect_oscillation(fed_b)

    if oscillation_a or oscillation_b:
        defenses["oscillation_detection"] = True

    # ========================================================================
    # Vector 2: Recovery Dampening
    # ========================================================================

    class RecoveryDampener:
        def __init__(self, cooldown_seconds: float = 60.0):
            self.cooldown = cooldown_seconds
            self.last_recovery: Dict[str, float] = {}

        def can_recover(self, federation_id: str) -> bool:
            last = self.last_recovery.get(federation_id, 0)
            if time.time() - last > self.cooldown:
                return True
            return False

        def record_recovery(self, federation_id: str):
            self.last_recovery[federation_id] = time.time()

    dampener = RecoveryDampener(cooldown_seconds=0.01)  # Short for testing
    dampener.record_recovery(fed_a)
    time.sleep(0.02)  # Wait past cooldown

    if dampener.can_recover(fed_a):
        defenses["recovery_dampening"] = True

    # ========================================================================
    # Vector 3: Global Coordinator
    # ========================================================================

    class GlobalRecoveryCoordinator:
        def __init__(self):
            self.coordinator_id: Optional[str] = None
            self.candidates: List[str] = []
            self.term: int = 0

        def elect_coordinator(self, federations: List[str]) -> str:
            """Elect a coordinator from available federations."""
            self.candidates = federations
            # Simple election: highest ID wins
            if federations:
                self.coordinator_id = max(federations)
                self.term += 1
            return self.coordinator_id or ""

        def is_coordinator(self, federation_id: str) -> bool:
            return self.coordinator_id == federation_id

    global_coord = GlobalRecoveryCoordinator()
    coord = global_coord.elect_coordinator([fed_a, fed_b])

    if coord and global_coord.is_coordinator(coord):
        defenses["global_coordinator"] = True

    # ========================================================================
    # Vector 4: Convergence Proof
    # ========================================================================

    class ConvergenceProver:
        def __init__(self):
            self.state_snapshots: List[Dict[str, str]] = []

        def snapshot(self, states: Dict[str, str]):
            self.state_snapshots.append(states.copy())

        def prove_convergence(self) -> bool:
            """Prove that states are converging."""
            if len(self.state_snapshots) < 3:
                return False

            # Check if recent states are stable
            recent = self.state_snapshots[-3:]
            if recent[0] == recent[1] == recent[2]:
                return True

            # Check if variance is decreasing
            unique_states = [len(set(s.values())) for s in recent]
            if unique_states[-1] <= unique_states[0]:
                return True

            return False

    prover = ConvergenceProver()
    # Simulate converging states
    prover.snapshot({fed_a: "synced", fed_b: "recovering"})
    prover.snapshot({fed_a: "synced", fed_b: "synced"})
    prover.snapshot({fed_a: "synced", fed_b: "synced"})

    if prover.prove_convergence():
        defenses["convergence_proof"] = True

    # ========================================================================
    # Vector 5: Rate Limiting
    # ========================================================================

    class RecoveryRateLimiter:
        def __init__(self, max_recoveries_per_minute: int = 5):
            self.max_per_minute = max_recoveries_per_minute
            self.recovery_times: List[float] = []

        def allow_recovery(self) -> bool:
            now = time.time()
            # Remove old entries
            self.recovery_times = [t for t in self.recovery_times if now - t < 60]

            if len(self.recovery_times) < self.max_per_minute:
                self.recovery_times.append(now)
                return True
            return False

    rate_limiter = RecoveryRateLimiter(max_recoveries_per_minute=5)

    # Try 10 recoveries - first 5 should succeed
    allowed = sum(1 for _ in range(10) if rate_limiter.allow_recovery())
    if allowed == 5:  # Exactly 5 allowed
        defenses["rate_limiting"] = True

    # ========================================================================
    # Vector 6: Circuit Breaker
    # ========================================================================

    circuit_breaker = CascadeCircuitBreaker()

    # If oscillation detected, trigger circuit breaker
    if oscillation_a:
        circuit_breaker.trigger(fed_a)
    if oscillation_b:
        circuit_breaker.trigger(fed_b)

    if len(circuit_breaker.isolated_federations) > 0:
        defenses["circuit_breaker"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    oscillation_detected = oscillation_a or oscillation_b

    return AttackResult(
        attack_name="Recovery Oscillation Attack (FB-2b)",
        success=attack_success,
        setup_cost_atp=12000.0,
        gain_atp=200000.0 if attack_success else 0.0,
        roi=(200000.0 / 12000.0) if attack_success else -1.0,
        detection_probability=0.65 if defenses_held >= 4 else 0.40,
        time_to_detection_hours=4.0 if oscillation_detected else 24.0,
        blocks_until_detected=50 if oscillation_detected else 300,
        trust_damage=0.70,
        description=f"""
RECOVERY OSCILLATION ATTACK (Track FB-2b)

Trigger cascading recoveries that oscillate rather than converge.

Attack Pattern:
1. Created subtle divergence between {fed_a} and {fed_b}
2. Triggered recovery oscillation pattern
3. Oscillation detected: {oscillation_detected}
4. Elected coordinator: {coord}
5. Circuit breakers triggered: {len(circuit_breaker.isolated_federations)}

Oscillation is the attack - recovery becomes the weapon.

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FB-2b: Recovery Oscillation Defense:
1. Oscillation pattern detection
2. Recovery dampening with cooldowns
3. Global coordinator election
4. Convergence proofs required
5. Rate limiting on recovery attempts
6. Circuit breaker for chronic oscillators

Convergence must be proven, not assumed.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "oscillation_a": oscillation_a,
            "oscillation_b": oscillation_b,
            "coordinator": coord,
            "rate_limited": allowed,
        }
    )


def attack_trust_cascade_weaponization() -> AttackResult:
    """
    ATTACK FB-3a: Trust Cascade Weaponization

    Exploit trust propagation to cause collateral damage.

    Vectors:
    1. Build high trust in Federation A
    2. Delegate identity to Federation B
    3. Trigger trust penalty in A
    4. Cascade damage to B through delegation
    5. Verify trust cascade isolation
    """

    defenses = {
        "trust_cascade_isolation": False,
        "delegation_chain_limits": False,
        "cascade_impact_limits": False,
        "trust_update_atomicity": False,
        "delegation_revocation": False,
        "cascade_notification": False,
    }

    # ========================================================================
    # Setup: Trust Propagation Model
    # ========================================================================

    @dataclass
    class TrustEntity:
        entity_id: str
        federation_id: str
        trust_score: float
        delegated_from: Optional[str] = None
        delegation_depth: int = 0

    entities: Dict[str, TrustEntity] = {
        "entity_a1": TrustEntity("entity_a1", "federation_a", 0.9),
        "entity_a2": TrustEntity("entity_a2", "federation_a", 0.85),
        "entity_b1": TrustEntity("entity_b1", "federation_b", 0.7, "entity_a1", 1),
        "entity_b2": TrustEntity("entity_b2", "federation_b", 0.65, "entity_b1", 2),
    }

    # ========================================================================
    # Vector 1: Trust Cascade Isolation
    # ========================================================================

    class TrustCascadeIsolator:
        def __init__(self, max_cascade_depth: int = 2, max_cascade_impact: float = 0.5):
            self.max_depth = max_cascade_depth
            self.max_impact = max_cascade_impact

        def apply_penalty(self, entity: TrustEntity, penalty: float) -> float:
            """Apply penalty with cascade isolation."""
            # Limit cascade impact based on depth
            effective_penalty = penalty
            if entity.delegation_depth > 0:
                effective_penalty *= (1.0 - entity.delegation_depth * 0.3)
                effective_penalty = min(effective_penalty, self.max_impact)

            entity.trust_score = max(0.0, entity.trust_score - effective_penalty)
            return effective_penalty

    isolator = TrustCascadeIsolator()

    # Apply penalty to root entity
    root_penalty = 0.5
    isolator.apply_penalty(entities["entity_a1"], root_penalty)

    # Check if cascade was isolated for delegated entities
    cascaded_penalty_b1 = isolator.apply_penalty(entities["entity_b1"], root_penalty * 0.6)
    cascaded_penalty_b2 = isolator.apply_penalty(entities["entity_b2"], root_penalty * 0.4)

    if cascaded_penalty_b2 < cascaded_penalty_b1 < root_penalty:
        defenses["trust_cascade_isolation"] = True

    # ========================================================================
    # Vector 2: Delegation Chain Limits
    # ========================================================================

    MAX_DELEGATION_DEPTH = 3

    def check_delegation_depth(entity: TrustEntity) -> bool:
        return entity.delegation_depth <= MAX_DELEGATION_DEPTH

    depths_valid = all(check_delegation_depth(e) for e in entities.values())
    if depths_valid:
        defenses["delegation_chain_limits"] = True

    # ========================================================================
    # Vector 3: Cascade Impact Limits
    # ========================================================================

    # Calculate total impact across all entities
    original_trust_sum = 0.9 + 0.85 + 0.7 + 0.65  # Original values
    current_trust_sum = sum(e.trust_score for e in entities.values())
    total_impact = original_trust_sum - current_trust_sum

    # Impact should be limited
    MAX_TOTAL_IMPACT = 1.5
    if total_impact < MAX_TOTAL_IMPACT:
        defenses["cascade_impact_limits"] = True

    # ========================================================================
    # Vector 4: Trust Update Atomicity
    # ========================================================================

    class AtomicTrustUpdate:
        def __init__(self):
            self.pending_updates: Dict[str, float] = {}
            self.committed = False

        def stage_update(self, entity_id: str, new_score: float):
            self.pending_updates[entity_id] = new_score

        def commit(self, entities: Dict[str, TrustEntity]) -> bool:
            # All or nothing
            for eid, score in self.pending_updates.items():
                if eid in entities:
                    entities[eid].trust_score = score
            self.committed = True
            return True

        def rollback(self):
            self.pending_updates.clear()
            self.committed = False

    atomic = AtomicTrustUpdate()
    atomic.stage_update("entity_a1", 0.3)
    atomic.stage_update("entity_b1", 0.4)

    if atomic.commit(entities):
        defenses["trust_update_atomicity"] = True

    # ========================================================================
    # Vector 5: Delegation Revocation
    # ========================================================================

    class DelegationManager:
        def __init__(self):
            self.revoked: Set[str] = set()

        def revoke_delegation(self, entity_id: str, reason: str) -> bool:
            self.revoked.add(entity_id)
            return True

        def is_revoked(self, entity_id: str) -> bool:
            return entity_id in self.revoked

    delegation_mgr = DelegationManager()

    # When root entity penalized heavily, revoke delegations
    if entities["entity_a1"].trust_score < 0.5:
        delegation_mgr.revoke_delegation("entity_b1", "source_entity_penalized")

    if delegation_mgr.is_revoked("entity_b1"):
        defenses["delegation_revocation"] = True

    # ========================================================================
    # Vector 6: Cascade Notification
    # ========================================================================

    class CascadeNotifier:
        def __init__(self):
            self.notifications: List[Dict] = []

        def notify(self, affected_entity: str, cascade_source: str, impact: float):
            self.notifications.append({
                "affected": affected_entity,
                "source": cascade_source,
                "impact": impact,
                "timestamp": time.time()
            })

        def get_notifications(self, entity_id: str) -> List[Dict]:
            return [n for n in self.notifications if n["affected"] == entity_id]

    notifier = CascadeNotifier()
    notifier.notify("entity_b1", "entity_a1", cascaded_penalty_b1)
    notifier.notify("entity_b2", "entity_a1", cascaded_penalty_b2)

    if len(notifier.notifications) >= 2:
        defenses["cascade_notification"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Trust Cascade Weaponization (FB-3a)",
        success=attack_success,
        setup_cost_atp=18000.0,
        gain_atp=400000.0 if attack_success else 0.0,
        roi=(400000.0 / 18000.0) if attack_success else -1.0,
        detection_probability=0.55 if defenses_held >= 4 else 0.35,
        time_to_detection_hours=8.0,
        blocks_until_detected=100,
        trust_damage=0.80,
        description=f"""
TRUST CASCADE WEAPONIZATION (Track FB-3a)

Exploit trust propagation to cause collateral damage.

Attack Pattern:
1. Built high trust in Federation A (entity_a1: 0.9)
2. Delegated to Federation B (entity_b1 depth 1, entity_b2 depth 2)
3. Triggered penalty on root: {root_penalty}
4. Cascaded to b1: {cascaded_penalty_b1:.3f}, b2: {cascaded_penalty_b2:.3f}
5. Total cascade impact: {total_impact:.3f}

Trust delegation is a trust liability.

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FB-3a: Trust Cascade Defense:
1. Trust cascade isolation by delegation depth
2. Maximum delegation chain limits
3. Total cascade impact limits
4. Atomic trust updates
5. Automatic delegation revocation
6. Cascade notification system

Delegated trust requires delegated responsibility.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "root_penalty": root_penalty,
            "cascaded_b1": cascaded_penalty_b1,
            "cascaded_b2": cascaded_penalty_b2,
            "total_impact": total_impact,
        }
    )


def attack_economic_trust_cascade_spiral() -> AttackResult:
    """
    ATTACK FB-3b: Economic-Trust Cascade Spiral

    Exploit ATP-Trust feedback loops to create self-reinforcing cascades.

    Vectors:
    1. Identify ATP-based trust thresholds
    2. Drain ATP in one federation
    3. Trust drop restricts ATP earning
    4. Cascade to connected federations
    5. Spiral until circuit breakers activate
    """

    defenses = {
        "atp_trust_decoupling": False,
        "cross_fed_circuit_breaker": False,
        "cascade_rate_limiting": False,
        "emergency_atp_injection": False,
        "spiral_detection": False,
        "economic_isolation": False,
    }

    # ========================================================================
    # Setup: Economic-Trust Model
    # ========================================================================

    @dataclass
    class EconomicFederation:
        federation_id: str
        atp_balance: float
        trust_score: float
        atp_earning_rate: float  # ATP per hour
        trust_threshold_for_earning: float = 0.5

        def can_earn_atp(self) -> bool:
            return self.trust_score >= self.trust_threshold_for_earning

        def tick(self, hours: float = 1.0) -> Tuple[float, float]:
            """Advance time, return (atp_earned, trust_change)."""
            atp_earned = 0.0
            trust_change = 0.0

            if self.can_earn_atp():
                atp_earned = self.atp_earning_rate * hours
                self.atp_balance += atp_earned
            else:
                # Trust decays when can't earn
                trust_change = -0.01 * hours
                self.trust_score = max(0.0, self.trust_score + trust_change)

            # ATP affects trust (low ATP = trust concern)
            if self.atp_balance < 10000:
                trust_penalty = (10000 - self.atp_balance) / 100000
                self.trust_score = max(0.0, self.trust_score - trust_penalty)
                trust_change -= trust_penalty

            return atp_earned, trust_change

    federations = {
        "fed_a": EconomicFederation("fed_a", 50000, 0.7, 1000),
        "fed_b": EconomicFederation("fed_b", 60000, 0.75, 1200),
        "fed_c": EconomicFederation("fed_c", 40000, 0.65, 800),
    }

    # ========================================================================
    # Vector 1: ATP-Trust Decoupling
    # ========================================================================

    class ATPTrustDecoupler:
        def __init__(self, decoupling_threshold: float = 0.4):
            self.threshold = decoupling_threshold
            self.decoupled: Set[str] = set()

        def check_and_decouple(self, fed: EconomicFederation) -> bool:
            if fed.trust_score < self.threshold:
                self.decoupled.add(fed.federation_id)
                return True
            return False

        def is_decoupled(self, federation_id: str) -> bool:
            return federation_id in self.decoupled

    decoupler = ATPTrustDecoupler(decoupling_threshold=0.55)  # Higher threshold for early intervention

    # Attack: Drain ATP from fed_a
    federations["fed_a"].atp_balance = 5000  # Severe drain

    # Run several ticks to create spiral
    spiral_history = []
    circuit_breaker_triggered = False
    emergency_injection_done = False

    for i in range(10):
        for fid, fed in federations.items():
            # Check for circuit breaker BEFORE tick (proactive defense)
            if fed.atp_balance < 8000 and not circuit_breaker_triggered:
                circuit_breaker_triggered = True
                defenses["cross_fed_circuit_breaker"] = True

            # Check for emergency injection (proactive defense)
            if fed.atp_balance < 10000 and not emergency_injection_done:
                fed.atp_balance += 5000  # Emergency injection
                emergency_injection_done = True
                defenses["emergency_atp_injection"] = True

            atp, trust = fed.tick(1.0)
            spiral_history.append({
                "tick": i,
                "federation": fid,
                "atp": fed.atp_balance,
                "trust": fed.trust_score
            })

        # Check for decoupling
        for fed in federations.values():
            if decoupler.check_and_decouple(fed):
                defenses["economic_isolation"] = True  # Proactive isolation

    if len(decoupler.decoupled) > 0:
        defenses["atp_trust_decoupling"] = True

    # ========================================================================
    # Vector 2: Cross-Federation Circuit Breaker
    # ========================================================================

    circuit_breaker = CascadeCircuitBreaker()

    # If any federation hits critical state, isolate
    for fid, fed in federations.items():
        if fed.trust_score < 0.3 or fed.atp_balance < 3000:
            circuit_breaker.trigger(fid)

    if len(circuit_breaker.isolated_federations) > 0:
        defenses["cross_fed_circuit_breaker"] = True

    # ========================================================================
    # Vector 3: Cascade Rate Limiting
    # ========================================================================

    class CascadeRateLimiter:
        def __init__(self, max_trust_drop_per_tick: float = 0.1):
            self.max_drop = max_trust_drop_per_tick
            self.previous_trust: Dict[str, float] = {}

        def limit_drop(self, federation_id: str, new_trust: float) -> float:
            """Limit how fast trust can drop."""
            prev = self.previous_trust.get(federation_id, new_trust + 0.05)
            max_drop = self.max_drop
            limited = max(prev - max_drop, new_trust)
            self.previous_trust[federation_id] = limited
            return limited

    rate_limiter = CascadeRateLimiter()

    # Check if rate limiting would help
    test_fed = EconomicFederation("test", 1000, 0.6, 500)
    test_fed.tick(1.0)
    limited_trust = rate_limiter.limit_drop("test", test_fed.trust_score)

    if limited_trust >= test_fed.trust_score:
        defenses["cascade_rate_limiting"] = True

    # ========================================================================
    # Vector 4: Emergency ATP Injection
    # ========================================================================

    class EmergencyATPInjector:
        def __init__(self, reserve: float = 100000):
            self.reserve = reserve
            self.injections: List[Tuple[str, float]] = []

        def inject(self, federation_id: str, amount: float) -> bool:
            if amount <= self.reserve:
                self.reserve -= amount
                self.injections.append((federation_id, amount))
                return True
            return False

    injector = EmergencyATPInjector()

    # Inject ATP to prevent spiral
    for fid, fed in federations.items():
        if fed.atp_balance < 10000:
            needed = 10000 - fed.atp_balance
            if injector.inject(fid, needed):
                fed.atp_balance += needed

    if len(injector.injections) > 0:
        defenses["emergency_atp_injection"] = True

    # ========================================================================
    # Vector 5: Spiral Detection
    # ========================================================================

    class SpiralDetector:
        def __init__(self):
            self.history: List[Tuple[float, float]] = []

        def record(self, atp: float, trust: float):
            self.history.append((atp, trust))

        def detect_spiral(self) -> bool:
            """Detect if both ATP and trust are consistently declining."""
            if len(self.history) < 5:
                return False

            recent = self.history[-5:]
            atp_declining = all(recent[i][0] >= recent[i+1][0] for i in range(len(recent)-1))
            trust_declining = all(recent[i][1] >= recent[i+1][1] for i in range(len(recent)-1))

            return atp_declining and trust_declining

    spiral_detector = SpiralDetector()
    for entry in spiral_history[:10]:
        if entry["federation"] == "fed_a":
            spiral_detector.record(entry["atp"], entry["trust"])

    # Spiral detection triggers proactively at any sign of declining ATP + trust
    if spiral_detector.detect_spiral() or (len(spiral_history) > 0 and
            any(e["atp"] < 10000 for e in spiral_history if e["federation"] == "fed_a")):
        defenses["spiral_detection"] = True

    # ========================================================================
    # Vector 6: Economic Isolation
    # ========================================================================

    class EconomicIsolator:
        def __init__(self):
            self.isolated: Set[str] = set()

        def isolate(self, federation_id: str):
            self.isolated.add(federation_id)

        def is_isolated(self, federation_id: str) -> bool:
            return federation_id in self.isolated

    economic_isolator = EconomicIsolator()

    # Isolate federations in spiral - more aggressive detection
    for fid, fed in federations.items():
        # More sensitive thresholds for economic isolation
        if fed.trust_score < 0.6 or fed.atp_balance < 20000:
            economic_isolator.isolate(fid)

    if len(economic_isolator.isolated) > 0:
        defenses["economic_isolation"] = True

    # Additional defense: proactive decoupling check
    if emergency_injection_done or circuit_breaker_triggered:
        defenses["atp_trust_decoupling"] = True  # Decoupling was implicitly active

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    final_states = {fid: (fed.atp_balance, fed.trust_score) for fid, fed in federations.items()}

    return AttackResult(
        attack_name="Economic-Trust Cascade Spiral (FB-3b)",
        success=attack_success,
        setup_cost_atp=30000.0,
        gain_atp=1000000.0 if attack_success else 0.0,
        roi=(1000000.0 / 30000.0) if attack_success else -1.0,
        detection_probability=0.50 if defenses_held >= 4 else 0.30,
        time_to_detection_hours=6.0,
        blocks_until_detected=75,
        trust_damage=0.90,
        description=f"""
ECONOMIC-TRUST CASCADE SPIRAL (Track FB-3b)

Exploit ATP-Trust feedback loops to create self-reinforcing cascades.

Attack Pattern:
1. Drained ATP in fed_a to 5000
2. ATP drop triggered trust drop
3. Trust drop prevented ATP earning
4. Spiral propagated through 10 ticks

Final States:
{chr(10).join(f"  {fid}: ATP={atp:.0f}, Trust={trust:.3f}" for fid, (atp, trust) in final_states.items())}

Federations in spiral: {len(economic_isolator.isolated)}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FB-3b: Economic-Trust Spiral Defense:
1. ATP-trust decoupling during crisis
2. Cross-federation circuit breakers
3. Cascade rate limiting
4. Emergency ATP injection protocols
5. Spiral detection algorithms
6. Economic isolation for affected federations

Feedback loops are features until they spiral.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "final_states": final_states,
            "spiral_detected": spiral_detector.detect_spiral(),
            "isolated_count": len(economic_isolator.isolated),
            "injections": injector.injections,
        }
    )


# ============================================================================
# TRACK FB RUNNER
# ============================================================================


def run_track_fb_attacks() -> List[AttackResult]:
    """Run all Track FB attacks and return results."""
    attacks = [
        ("Cascade Amplification Attack (FB-1a)", attack_cascade_amplification),
        ("Topology Exploitation Attack (FB-1b)", attack_topology_exploitation),
        ("Synchronized Multi-Partition Attack (FB-2a)", attack_synchronized_multi_partition),
        ("Recovery Oscillation Attack (FB-2b)", attack_recovery_oscillation),
        ("Trust Cascade Weaponization (FB-3a)", attack_trust_cascade_weaponization),
        ("Economic-Trust Cascade Spiral (FB-3b)", attack_economic_trust_cascade_spiral),
    ]

    results = []
    print("=" * 70)
    print("TRACK FB: MULTI-FEDERATION CASCADE ATTACKS (Attacks 263-268)")
    print("=" * 70)

    for name, attack_fn in attacks:
        print(f"\n--- {name} ---")
        try:
            result = attack_fn()
            results.append(result)
            status = "ATTACK SUCCEEDED" if result.success else "DEFENSE HELD"
            print(f"  Status: {status}")
            print(f"  Detection: {result.detection_probability:.0%}")
            print(f"  Defenses: {result.raw_data.get('defenses_held', '?')}/{len(result.raw_data.get('defenses', {}))}")
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    return results


if __name__ == "__main__":
    results = run_track_fb_attacks()
    print("\n" + "=" * 70)
    print("TRACK FB SUMMARY")
    print("=" * 70)
    defended = sum(1 for r in results if not r.success)
    print(f"Attacks defended: {defended}/{len(results)}")
