"""
Cascading Failure & Chaos Engineering — Session 22 Track 2
==========================================================
Multi-layer fault injection, cascade propagation analysis,
convergence metrics, and recovery SLO validation for Web4.

Sections:
  S1:  System Layer Model
  S2:  Fault Injection Primitives
  S3:  Cascade Propagation Engine
  S4:  Circuit Breaker Integration
  S5:  Convergence Metrics
  S6:  Recovery SLO Validation
  S7:  Partition Simulation
  S8:  Byzantine Fault Injection
  S9:  Resource Exhaustion
  S10: Multi-Layer Scenario
  S11: Performance
"""

from __future__ import annotations
import enum
import hashlib
import math
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# ── S1: System Layer Model ────────────────────────────────────────────

class SystemLayer(enum.Enum):
    HARDWARE = "hardware"       # TPM, Secure Enclave
    TRANSPORT = "transport"     # TCP, HTTP/2, WebSocket
    IDENTITY = "identity"       # LCT, key management
    TRUST = "trust"             # T3/V3 tensors
    CONSENSUS = "consensus"     # BFT, leader election
    ATP = "atp"                 # Energy metabolism
    FEDERATION = "federation"   # Cross-org trust


class NodeState(enum.Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    DEAD = "dead"
    RECOVERING = "recovering"


@dataclass
class LayerHealth:
    layer: SystemLayer
    state: NodeState = NodeState.HEALTHY
    error_rate: float = 0.0         # 0.0 - 1.0
    latency_ms: float = 1.0
    throughput_pct: float = 100.0   # % of normal
    active_faults: List[str] = field(default_factory=list)

    def overall_score(self) -> float:
        """0.0 = dead, 1.0 = fully healthy."""
        if self.state == NodeState.DEAD:
            return 0.0
        score = 1.0
        score -= self.error_rate * 0.4
        # Latency penalty: above 100ms starts degrading
        if self.latency_ms > 100:
            score -= min(0.3, (self.latency_ms - 100) / 1000)
        score *= self.throughput_pct / 100.0
        return max(0.0, min(1.0, score))


@dataclass
class SystemNode:
    node_id: str
    layers: Dict[SystemLayer, LayerHealth] = field(default_factory=dict)
    trust_score: float = 0.8
    atp_balance: float = 100.0
    is_byzantine: bool = False
    recovery_start: Optional[float] = None

    def __post_init__(self):
        if not self.layers:
            for layer in SystemLayer:
                self.layers[layer] = LayerHealth(layer)

    def overall_health(self) -> float:
        if not self.layers:
            return 0.0
        return sum(lh.overall_score() for lh in self.layers.values()) / len(self.layers)

    def worst_layer(self) -> Optional[SystemLayer]:
        if not self.layers:
            return None
        return min(self.layers, key=lambda l: self.layers[l].overall_score())


# Dependency graph: layer A depends on layer B
LAYER_DEPENDENCIES: Dict[SystemLayer, List[SystemLayer]] = {
    SystemLayer.FEDERATION: [SystemLayer.CONSENSUS, SystemLayer.TRUST],
    SystemLayer.CONSENSUS: [SystemLayer.TRANSPORT, SystemLayer.IDENTITY],
    SystemLayer.ATP: [SystemLayer.CONSENSUS, SystemLayer.IDENTITY],
    SystemLayer.TRUST: [SystemLayer.IDENTITY, SystemLayer.HARDWARE],
    SystemLayer.IDENTITY: [SystemLayer.HARDWARE],
    SystemLayer.TRANSPORT: [SystemLayer.HARDWARE],
    SystemLayer.HARDWARE: [],
}


# ── S2: Fault Injection Primitives ────────────────────────────────────

class FaultType(enum.Enum):
    CRASH = "crash"                 # Node dies
    LATENCY = "latency"             # Increased latency
    PACKET_LOSS = "packet_loss"     # Random drops
    CORRUPTION = "corruption"       # Data corruption
    PARTITION = "partition"         # Network split
    RESOURCE_EXHAUST = "resource"   # CPU/memory/disk
    BYZANTINE = "byzantine"         # Arbitrary behavior
    CLOCK_SKEW = "clock_skew"       # Time desync


@dataclass
class FaultSpec:
    fault_type: FaultType
    target_layer: SystemLayer
    target_nodes: List[str]
    severity: float = 0.5          # 0.0-1.0
    duration_s: float = 10.0
    start_time: float = 0.0

    @property
    def end_time(self) -> float:
        return self.start_time + self.duration_s


class FaultInjector:
    """Injects faults into system nodes."""

    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random(42)
        self.active_faults: List[FaultSpec] = []
        self.fault_history: List[FaultSpec] = []

    def inject(self, fault: FaultSpec, nodes: Dict[str, SystemNode]):
        self.active_faults.append(fault)
        self.fault_history.append(fault)

        for nid in fault.target_nodes:
            node = nodes.get(nid)
            if not node:
                continue
            layer = node.layers.get(fault.target_layer)
            if not layer:
                continue

            layer.active_faults.append(fault.fault_type.value)

            if fault.fault_type == FaultType.CRASH:
                layer.state = NodeState.DEAD
                layer.throughput_pct = 0.0
                layer.error_rate = 1.0
            elif fault.fault_type == FaultType.LATENCY:
                layer.latency_ms *= (1 + fault.severity * 10)
                if layer.state == NodeState.HEALTHY:
                    layer.state = NodeState.DEGRADED
            elif fault.fault_type == FaultType.PACKET_LOSS:
                layer.error_rate = min(1.0, layer.error_rate + fault.severity)
                layer.throughput_pct *= (1 - fault.severity)
                if fault.severity > 0.5:
                    layer.state = NodeState.FAILING
                else:
                    layer.state = NodeState.DEGRADED
            elif fault.fault_type == FaultType.CORRUPTION:
                layer.error_rate = min(1.0, layer.error_rate + fault.severity * 0.3)
                layer.state = NodeState.DEGRADED
            elif fault.fault_type == FaultType.RESOURCE_EXHAUST:
                layer.throughput_pct *= (1 - fault.severity * 0.8)
                layer.latency_ms *= (1 + fault.severity * 5)
                layer.state = NodeState.DEGRADED if fault.severity < 0.8 else NodeState.FAILING
            elif fault.fault_type == FaultType.BYZANTINE:
                node.is_byzantine = True
                layer.state = NodeState.DEGRADED
            elif fault.fault_type == FaultType.CLOCK_SKEW:
                layer.latency_ms += fault.severity * 500  # Skew as added latency
                layer.state = NodeState.DEGRADED

    def expire_faults(self, current_time: float, nodes: Dict[str, SystemNode]):
        remaining = []
        for fault in self.active_faults:
            if current_time >= fault.end_time:
                # Recover affected nodes
                for nid in fault.target_nodes:
                    node = nodes.get(nid)
                    if not node:
                        continue
                    layer = node.layers.get(fault.target_layer)
                    if layer and fault.fault_type.value in layer.active_faults:
                        layer.active_faults.remove(fault.fault_type.value)
                        if not layer.active_faults:
                            layer.state = NodeState.RECOVERING
                            node.recovery_start = current_time
            else:
                remaining.append(fault)
        self.active_faults = remaining


# ── S3: Cascade Propagation Engine ────────────────────────────────────

@dataclass
class CascadeEvent:
    source_node: str
    source_layer: SystemLayer
    target_node: str
    target_layer: SystemLayer
    severity: float
    timestamp: float
    depth: int


class CascadeEngine:
    """Models failure cascade through layer dependencies."""

    def __init__(self, decay_factor: float = 0.7, threshold: float = 0.3):
        self.decay_factor = decay_factor
        self.threshold = threshold  # Min severity to propagate
        self.events: List[CascadeEvent] = []

    def propagate(
        self,
        nodes: Dict[str, SystemNode],
        source_node: str,
        source_layer: SystemLayer,
        severity: float,
        timestamp: float,
        depth: int = 0,
        max_depth: int = 5,
    ) -> List[CascadeEvent]:
        if depth >= max_depth or severity < self.threshold:
            return []

        new_events = []
        # Propagate UP through dependent layers on same node
        for dep_layer, deps in LAYER_DEPENDENCIES.items():
            if source_layer in deps:
                node = nodes.get(source_node)
                if not node:
                    continue
                layer = node.layers.get(dep_layer)
                if not layer or layer.state == NodeState.DEAD:
                    continue

                cascaded_severity = severity * self.decay_factor
                event = CascadeEvent(
                    source_node, source_layer, source_node,
                    dep_layer, cascaded_severity, timestamp, depth + 1
                )
                self.events.append(event)
                new_events.append(event)

                # Apply cascade effect
                layer.error_rate = min(1.0, layer.error_rate + cascaded_severity * 0.3)
                layer.throughput_pct *= (1 - cascaded_severity * 0.2)
                if cascaded_severity > 0.5:
                    layer.state = NodeState.FAILING
                elif layer.state == NodeState.HEALTHY:
                    layer.state = NodeState.DEGRADED

                # Recurse
                new_events.extend(self.propagate(
                    nodes, source_node, dep_layer,
                    cascaded_severity, timestamp, depth + 1, max_depth
                ))

        return new_events

    def cascade_depth(self) -> int:
        if not self.events:
            return 0
        return max(e.depth for e in self.events)

    def affected_layers(self) -> Set[SystemLayer]:
        return {e.target_layer for e in self.events}


# ── S4: Circuit Breaker Integration ───────────────────────────────────

class BreakerState(enum.Enum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, reject requests
    HALF_OPEN = "half_open" # Testing recovery


@dataclass
class CircuitBreaker:
    name: str
    layer: SystemLayer
    failure_threshold: int = 5
    recovery_timeout_s: float = 10.0
    half_open_max_calls: int = 3
    state: BreakerState = BreakerState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    half_open_calls: int = 0
    state_changes: List[Tuple[float, BreakerState, BreakerState]] = field(default_factory=list)

    def _change_state(self, new_state: BreakerState, now: float):
        old = self.state
        self.state = new_state
        self.state_changes.append((now, old, new_state))

    def record_success(self, now: float):
        if self.state == BreakerState.HALF_OPEN:
            self.success_count += 1
            self.half_open_calls += 1
            if self.success_count >= self.half_open_max_calls:
                self._change_state(BreakerState.CLOSED, now)
                self.failure_count = 0
                self.success_count = 0
                self.half_open_calls = 0
        elif self.state == BreakerState.CLOSED:
            self.success_count += 1

    def record_failure(self, now: float):
        self.failure_count += 1
        self.last_failure_time = now

        if self.state == BreakerState.HALF_OPEN:
            self._change_state(BreakerState.OPEN, now)
            self.half_open_calls = 0
        elif self.state == BreakerState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self._change_state(BreakerState.OPEN, now)

    def should_allow(self, now: float) -> bool:
        if self.state == BreakerState.CLOSED:
            return True
        if self.state == BreakerState.OPEN:
            if now - self.last_failure_time >= self.recovery_timeout_s:
                self._change_state(BreakerState.HALF_OPEN, now)
                self.half_open_calls = 0
                self.success_count = 0
                return True
            return False
        # HALF_OPEN
        return self.half_open_calls < self.half_open_max_calls


# ── S5: Convergence Metrics ──────────────────────────────────────────

@dataclass
class ConvergenceMetrics:
    """Tracks system convergence after a fault."""
    health_samples: List[Tuple[float, float]] = field(default_factory=list)
    # (timestamp, system_health_score)

    def record(self, timestamp: float, health: float):
        self.health_samples.append((timestamp, health))

    def time_to_recovery(self, threshold: float = 0.8) -> Optional[float]:
        """Time from first degradation to recovery above threshold."""
        if not self.health_samples:
            return None
        first_degraded = None
        for ts, h in self.health_samples:
            if h < threshold and first_degraded is None:
                first_degraded = ts
            if first_degraded is not None and h >= threshold:
                return ts - first_degraded
        return None  # Never recovered

    def min_health(self) -> float:
        if not self.health_samples:
            return 1.0
        return min(h for _, h in self.health_samples)

    def steady_state_health(self, window: int = 5) -> float:
        """Average health over last `window` samples."""
        if not self.health_samples:
            return 0.0
        recent = self.health_samples[-window:]
        return sum(h for _, h in recent) / len(recent)

    def recovery_curve_slope(self) -> float:
        """Slope of health recovery (positive = improving)."""
        if len(self.health_samples) < 2:
            return 0.0
        # Linear regression on last half of samples
        n = len(self.health_samples)
        samples = self.health_samples[n // 2:]
        if len(samples) < 2:
            return 0.0
        x_vals = [s[0] for s in samples]
        y_vals = [s[1] for s in samples]
        x_mean = sum(x_vals) / len(x_vals)
        y_mean = sum(y_vals) / len(y_vals)
        num = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, y_vals))
        den = sum((x - x_mean) ** 2 for x in x_vals)
        if den == 0:
            return 0.0
        return num / den


# ── S6: Recovery SLO Validation ──────────────────────────────────────

@dataclass
class RecoverySLO:
    name: str
    max_recovery_time_s: float
    min_health_threshold: float
    max_cascade_depth: int
    max_affected_layers: int


STANDARD_SLOS: Dict[str, RecoverySLO] = {
    "critical": RecoverySLO("critical", 3.0, 0.7, 1, 2),
    "standard": RecoverySLO("standard", 30.0, 0.5, 4, 5),
    "relaxed": RecoverySLO("relaxed", 120.0, 0.3, 6, 7),
}


@dataclass
class SLOResult:
    slo_name: str
    met: bool
    actual_recovery_time: Optional[float]
    actual_min_health: float
    actual_cascade_depth: int
    actual_affected_layers: int
    violations: List[str] = field(default_factory=list)


class SLOValidator:
    """Validates recovery against SLO targets."""

    @staticmethod
    def validate(
        slo: RecoverySLO,
        metrics: ConvergenceMetrics,
        cascade: CascadeEngine,
    ) -> SLOResult:
        violations = []
        recovery_time = metrics.time_to_recovery(slo.min_health_threshold)

        if recovery_time is not None and recovery_time > slo.max_recovery_time_s:
            violations.append(
                f"Recovery time {recovery_time:.1f}s > {slo.max_recovery_time_s}s")

        min_health = metrics.min_health()
        cascade_depth = cascade.cascade_depth()
        affected = len(cascade.affected_layers())

        if cascade_depth > slo.max_cascade_depth:
            violations.append(
                f"Cascade depth {cascade_depth} > {slo.max_cascade_depth}")

        if affected > slo.max_affected_layers:
            violations.append(
                f"Affected layers {affected} > {slo.max_affected_layers}")

        return SLOResult(
            slo.name, len(violations) == 0,
            recovery_time, min_health,
            cascade_depth, affected, violations
        )


# ── S7: Partition Simulation ─────────────────────────────────────────

@dataclass
class NetworkPartition:
    partition_a: Set[str]  # Node IDs in partition A
    partition_b: Set[str]  # Node IDs in partition B
    start_time: float
    duration_s: float
    asymmetric: bool = False  # If True, A→B blocked but B→A ok

    @property
    def end_time(self) -> float:
        return self.start_time + self.duration_s

    def is_active(self, current_time: float) -> bool:
        return self.start_time <= current_time < self.end_time

    def can_communicate(self, src: str, dst: str, current_time: float) -> bool:
        if not self.is_active(current_time):
            return True
        if src in self.partition_a and dst in self.partition_b:
            return False
        if not self.asymmetric and src in self.partition_b and dst in self.partition_a:
            return False
        return True


class PartitionSimulator:
    """Simulates network partitions and measures impact."""

    def __init__(self, nodes: Dict[str, SystemNode]):
        self.nodes = nodes
        self.partitions: List[NetworkPartition] = []
        self.message_log: List[Tuple[str, str, float, bool]] = []

    def add_partition(self, partition: NetworkPartition):
        self.partitions.append(partition)

    def try_send(self, src: str, dst: str, current_time: float) -> bool:
        for p in self.partitions:
            if not p.can_communicate(src, dst, current_time):
                self.message_log.append((src, dst, current_time, False))
                return False
        self.message_log.append((src, dst, current_time, True))
        return True

    def delivery_rate(self) -> float:
        if not self.message_log:
            return 1.0
        delivered = sum(1 for _, _, _, ok in self.message_log if ok)
        return delivered / len(self.message_log)

    def partition_impact(self) -> Dict[str, float]:
        """Per-node message delivery rate."""
        node_stats: Dict[str, Tuple[int, int]] = {}  # sent, delivered
        for src, _, _, ok in self.message_log:
            s, d = node_stats.get(src, (0, 0))
            node_stats[src] = (s + 1, d + (1 if ok else 0))
        return {nid: d / s if s > 0 else 1.0
                for nid, (s, d) in node_stats.items()}


# ── S8: Byzantine Fault Injection ─────────────────────────────────────

class ByzantineBehavior(enum.Enum):
    EQUIVOCATE = "equivocate"       # Send conflicting messages
    WITHHOLD = "withhold"           # Don't respond
    DELAY = "delay"                 # Respond late
    FORGE = "forge"                 # Forge signatures/data
    COLLUDE = "collude"             # Coordinate with other Byzantine nodes


@dataclass
class ByzantineNode:
    node_id: str
    behaviors: List[ByzantineBehavior]
    detection_probability: float = 0.0
    detected: bool = False
    actions_taken: int = 0

    def act(self, rng: random.Random) -> ByzantineBehavior:
        self.actions_taken += 1
        # Detection probability increases with actions
        self.detection_probability = min(
            0.95, 1.0 - (1.0 - 0.1) ** self.actions_taken
        )
        if rng.random() < self.detection_probability:
            self.detected = True
        return rng.choice(self.behaviors)


class ByzantineFaultInjector:
    """Manages Byzantine node behavior in consensus."""

    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random(42)
        self.byzantine_nodes: Dict[str, ByzantineNode] = {}

    def add_byzantine(self, node_id: str,
                      behaviors: List[ByzantineBehavior]) -> ByzantineNode:
        bn = ByzantineNode(node_id, behaviors)
        self.byzantine_nodes[node_id] = bn
        return bn

    def simulate_round(self, total_nodes: int) -> Dict[str, Any]:
        """Simulate one consensus round with Byzantine nodes."""
        f = len(self.byzantine_nodes)
        n = total_nodes
        bft_bound = (n - 1) // 3  # Max f for BFT: n >= 3f + 1

        actions = {}
        for nid, bn in self.byzantine_nodes.items():
            action = bn.act(self.rng)
            actions[nid] = action.value

        detected = [nid for nid, bn in self.byzantine_nodes.items() if bn.detected]

        return {
            "byzantine_count": f,
            "total_nodes": n,
            "bft_bound": bft_bound,
            "within_bound": f <= bft_bound,
            "actions": actions,
            "detected": detected,
            "consensus_possible": f <= bft_bound,
        }


# ── S9: Resource Exhaustion ──────────────────────────────────────────

@dataclass
class ResourceState:
    cpu_pct: float = 10.0
    memory_pct: float = 30.0
    disk_pct: float = 20.0
    connections: int = 10
    max_connections: int = 1000
    atp_balance: float = 100.0

    def is_exhausted(self) -> bool:
        return (self.cpu_pct >= 95 or self.memory_pct >= 95
                or self.disk_pct >= 95
                or self.connections >= self.max_connections
                or self.atp_balance <= 0)

    def health_score(self) -> float:
        scores = [
            1.0 - self.cpu_pct / 100.0,
            1.0 - self.memory_pct / 100.0,
            1.0 - self.disk_pct / 100.0,
            1.0 - self.connections / self.max_connections,
            min(1.0, self.atp_balance / 100.0),
        ]
        return sum(scores) / len(scores)


class ResourceExhaustionSimulator:
    """Simulates gradual resource exhaustion."""

    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random(42)
        self.resources: Dict[str, ResourceState] = {}

    def add_node(self, node_id: str, state: Optional[ResourceState] = None):
        self.resources[node_id] = state or ResourceState()

    def simulate_load(self, node_id: str, load_factor: float) -> ResourceState:
        """Apply load to a node's resources."""
        rs = self.resources.get(node_id)
        if not rs:
            return ResourceState()

        rs.cpu_pct = min(100, rs.cpu_pct + load_factor * 20 + self.rng.gauss(0, 5))
        rs.memory_pct = min(100, rs.memory_pct + load_factor * 10 + self.rng.gauss(0, 3))
        rs.disk_pct = min(100, rs.disk_pct + load_factor * 2)
        rs.connections = min(rs.max_connections,
                            rs.connections + int(load_factor * 50))
        rs.atp_balance = max(0, rs.atp_balance - load_factor * 5)
        return rs

    def exhausted_nodes(self) -> List[str]:
        return [nid for nid, rs in self.resources.items() if rs.is_exhausted()]


# ── S10: Multi-Layer Scenario ─────────────────────────────────────────

class ChaosScenario:
    """Complete chaos engineering scenario across multiple layers."""

    def __init__(self, num_nodes: int = 10, seed: int = 42):
        self.rng = random.Random(seed)
        self.nodes: Dict[str, SystemNode] = {}
        self.injector = FaultInjector(self.rng)
        self.cascade = CascadeEngine()
        self.metrics = ConvergenceMetrics()
        self.breakers: Dict[str, CircuitBreaker] = {}

        for i in range(num_nodes):
            nid = f"node_{i}"
            self.nodes[nid] = SystemNode(nid)
            for layer in SystemLayer:
                self.breakers[f"{nid}_{layer.value}"] = CircuitBreaker(
                    f"{nid}_{layer.value}", layer,
                    failure_threshold=3, recovery_timeout_s=5.0
                )

    def system_health(self) -> float:
        if not self.nodes:
            return 0.0
        return sum(n.overall_health() for n in self.nodes.values()) / len(self.nodes)

    def run_scenario(
        self, faults: List[FaultSpec], duration_s: float = 30.0,
        step_s: float = 1.0
    ) -> Dict[str, Any]:
        t = 0.0
        # Inject faults at their scheduled times
        pending_faults = sorted(faults, key=lambda f: f.start_time)
        fault_idx = 0

        while t < duration_s:
            # Inject due faults
            while fault_idx < len(pending_faults) and pending_faults[fault_idx].start_time <= t:
                fault = pending_faults[fault_idx]
                self.injector.inject(fault, self.nodes)

                # Trigger cascade
                for nid in fault.target_nodes:
                    self.cascade.propagate(
                        self.nodes, nid, fault.target_layer,
                        fault.severity, t
                    )
                fault_idx += 1

            # Expire finished faults
            self.injector.expire_faults(t, self.nodes)

            # Recovery for nodes without active faults
            for node in self.nodes.values():
                for layer_type, layer in node.layers.items():
                    if layer.state == NodeState.RECOVERING and not layer.active_faults:
                        # Gradual recovery
                        layer.error_rate = max(0, layer.error_rate - 0.1)
                        layer.throughput_pct = min(100, layer.throughput_pct + 10)
                        layer.latency_ms = max(1.0, layer.latency_ms * 0.8)
                        if layer.error_rate <= 0.05 and layer.throughput_pct >= 95:
                            layer.state = NodeState.HEALTHY

            # Record metrics
            self.metrics.record(t, self.system_health())

            # Update circuit breakers
            for node in self.nodes.values():
                for layer_type, layer in node.layers.items():
                    key = f"{node.node_id}_{layer_type.value}"
                    breaker = self.breakers.get(key)
                    if breaker:
                        if layer.error_rate > 0.3:
                            breaker.record_failure(t)
                        else:
                            breaker.record_success(t)

            t += step_s

        return {
            "final_health": self.system_health(),
            "min_health": self.metrics.min_health(),
            "cascade_depth": self.cascade.cascade_depth(),
            "cascade_events": len(self.cascade.events),
            "affected_layers": len(self.cascade.affected_layers()),
            "recovery_time": self.metrics.time_to_recovery(0.7),
            "steady_state": self.metrics.steady_state_health(),
        }


# ── S11: Performance ──────────────────────────────────────────────────

def run_checks():
    checks: List[Tuple[str, bool]] = []

    # ── S1: System Layer Model ────────────────────────────────────────
    node = SystemNode("test1")
    checks.append(("s1_all_layers", len(node.layers) == 7))
    checks.append(("s1_healthy", node.overall_health() == 1.0))

    node.layers[SystemLayer.TRANSPORT].error_rate = 0.5
    node.layers[SystemLayer.TRANSPORT].state = NodeState.DEGRADED
    checks.append(("s1_degraded", node.overall_health() < 1.0))
    checks.append(("s1_worst_layer", node.worst_layer() == SystemLayer.TRANSPORT))

    # Layer dependencies
    checks.append(("s1_deps_exist", len(LAYER_DEPENDENCIES) == 7))
    checks.append(("s1_fed_deps", SystemLayer.CONSENSUS in LAYER_DEPENDENCIES[SystemLayer.FEDERATION]))

    # ── S2: Fault Injection ───────────────────────────────────────────
    nodes = {f"n{i}": SystemNode(f"n{i}") for i in range(5)}
    injector = FaultInjector()

    crash_fault = FaultSpec(FaultType.CRASH, SystemLayer.TRANSPORT,
                            ["n0"], severity=1.0, duration_s=5.0)
    injector.inject(crash_fault, nodes)
    checks.append(("s2_crash_dead", nodes["n0"].layers[SystemLayer.TRANSPORT].state == NodeState.DEAD))
    checks.append(("s2_crash_throughput", nodes["n0"].layers[SystemLayer.TRANSPORT].throughput_pct == 0))

    latency_fault = FaultSpec(FaultType.LATENCY, SystemLayer.CONSENSUS,
                              ["n1"], severity=0.5, duration_s=3.0)
    injector.inject(latency_fault, nodes)
    checks.append(("s2_latency_increased", nodes["n1"].layers[SystemLayer.CONSENSUS].latency_ms > 1.0))
    checks.append(("s2_latency_degraded", nodes["n1"].layers[SystemLayer.CONSENSUS].state == NodeState.DEGRADED))

    # Fault expiry
    injector.expire_faults(6.0, nodes)
    checks.append(("s2_expired", nodes["n0"].layers[SystemLayer.TRANSPORT].state == NodeState.RECOVERING))

    # ── S3: Cascade Propagation ───────────────────────────────────────
    cascade_nodes = {f"c{i}": SystemNode(f"c{i}") for i in range(3)}
    cascade = CascadeEngine(decay_factor=0.7, threshold=0.2)

    # Hardware failure should cascade up
    cascade_nodes["c0"].layers[SystemLayer.HARDWARE].state = NodeState.DEAD
    events = cascade.propagate(cascade_nodes, "c0", SystemLayer.HARDWARE, 0.9, 0.0)
    checks.append(("s3_cascade_events", len(events) > 0))
    checks.append(("s3_cascade_depth", cascade.cascade_depth() >= 2))

    affected = cascade.affected_layers()
    checks.append(("s3_affects_identity", SystemLayer.IDENTITY in affected))
    checks.append(("s3_affects_transport", SystemLayer.TRANSPORT in affected))

    # ── S4: Circuit Breaker ───────────────────────────────────────────
    breaker = CircuitBreaker("test", SystemLayer.TRANSPORT,
                             failure_threshold=3, recovery_timeout_s=5.0)
    checks.append(("s4_starts_closed", breaker.state == BreakerState.CLOSED))

    for i in range(3):
        breaker.record_failure(float(i))
    checks.append(("s4_opens_after_threshold", breaker.state == BreakerState.OPEN))

    checks.append(("s4_rejects_when_open", not breaker.should_allow(3.0)))

    # After recovery timeout, transitions to half-open
    checks.append(("s4_half_open_after_timeout", breaker.should_allow(9.0)))
    checks.append(("s4_half_open_state", breaker.state == BreakerState.HALF_OPEN))

    # Successes in half-open close the breaker
    for i in range(3):
        breaker.record_success(10.0 + i)
    checks.append(("s4_closes_on_success", breaker.state == BreakerState.CLOSED))

    # ── S5: Convergence Metrics ───────────────────────────────────────
    metrics = ConvergenceMetrics()
    metrics.record(0.0, 1.0)
    metrics.record(1.0, 0.8)
    metrics.record(2.0, 0.4)  # Degradation
    metrics.record(3.0, 0.3)  # Low point
    metrics.record(4.0, 0.5)
    metrics.record(5.0, 0.7)
    metrics.record(6.0, 0.85)  # Recovery

    checks.append(("s5_min_health", abs(metrics.min_health() - 0.3) < 0.01))
    ttr = metrics.time_to_recovery(0.8)
    checks.append(("s5_ttr", ttr is not None and abs(ttr - 5.0) < 1.1))
    checks.append(("s5_steady_state", metrics.steady_state_health() > 0.5))
    checks.append(("s5_positive_slope", metrics.recovery_curve_slope() > 0))

    # ── S6: Recovery SLO ──────────────────────────────────────────────
    slo_cascade = CascadeEngine()
    slo_cascade.events = [
        CascadeEvent("n0", SystemLayer.HARDWARE, "n0", SystemLayer.IDENTITY, 0.5, 0, 1),
        CascadeEvent("n0", SystemLayer.IDENTITY, "n0", SystemLayer.TRUST, 0.35, 0, 2),
    ]

    relaxed_slo = STANDARD_SLOS["relaxed"]
    result = SLOValidator.validate(relaxed_slo, metrics, slo_cascade)
    checks.append(("s6_relaxed_met", result.met))

    critical_slo = STANDARD_SLOS["critical"]
    crit_result = SLOValidator.validate(critical_slo, metrics, slo_cascade)
    checks.append(("s6_critical_violations", not crit_result.met))
    checks.append(("s6_has_violations", len(crit_result.violations) > 0))

    # ── S7: Partition Simulation ──────────────────────────────────────
    part_nodes = {f"p{i}": SystemNode(f"p{i}") for i in range(6)}
    part_sim = PartitionSimulator(part_nodes)

    partition = NetworkPartition(
        partition_a={"p0", "p1", "p2"},
        partition_b={"p3", "p4", "p5"},
        start_time=1.0, duration_s=5.0
    )
    part_sim.add_partition(partition)

    # Before partition
    checks.append(("s7_before_ok", part_sim.try_send("p0", "p3", 0.5)))

    # During partition
    checks.append(("s7_cross_blocked", not part_sim.try_send("p0", "p3", 2.0)))
    checks.append(("s7_same_side_ok", part_sim.try_send("p0", "p1", 2.0)))

    # After partition
    checks.append(("s7_after_ok", part_sim.try_send("p0", "p3", 7.0)))

    # Delivery rate
    checks.append(("s7_delivery_rate", part_sim.delivery_rate() < 1.0))

    # Asymmetric partition
    asym = NetworkPartition(
        partition_a={"p0"}, partition_b={"p1"},
        start_time=0.0, duration_s=10.0, asymmetric=True
    )
    asym_sim = PartitionSimulator(part_nodes)
    asym_sim.add_partition(asym)
    checks.append(("s7_asym_blocked", not asym_sim.try_send("p0", "p1", 1.0)))
    checks.append(("s7_asym_reverse_ok", asym_sim.try_send("p1", "p0", 1.0)))

    # ── S8: Byzantine Fault Injection ─────────────────────────────────
    byz_injector = ByzantineFaultInjector()
    byz_injector.add_byzantine("evil1", [ByzantineBehavior.EQUIVOCATE, ByzantineBehavior.WITHHOLD])
    byz_injector.add_byzantine("evil2", [ByzantineBehavior.FORGE])

    result = byz_injector.simulate_round(10)
    checks.append(("s8_within_bound", result["within_bound"]))  # 2 <= 3
    checks.append(("s8_consensus_ok", result["consensus_possible"]))
    checks.append(("s8_actions_logged", len(result["actions"]) == 2))

    # Exceed BFT bound
    for i in range(3, 8):
        byz_injector.add_byzantine(f"evil{i}", [ByzantineBehavior.COLLUDE])
    result_bad = byz_injector.simulate_round(10)
    checks.append(("s8_exceeds_bound", not result_bad["within_bound"]))

    # Detection increases with actions
    byz = ByzantineNode("test_byz", [ByzantineBehavior.EQUIVOCATE])
    rng = random.Random(42)
    for _ in range(20):
        byz.act(rng)
    checks.append(("s8_detection_increases", byz.detection_probability > 0.5))

    # ── S9: Resource Exhaustion ───────────────────────────────────────
    res_sim = ResourceExhaustionSimulator()
    res_sim.add_node("r0")
    res_sim.add_node("r1")

    # Apply load
    for _ in range(5):
        res_sim.simulate_load("r0", 1.5)
    checks.append(("s9_loaded", res_sim.resources["r0"].cpu_pct > 50))
    checks.append(("s9_atp_drained", res_sim.resources["r0"].atp_balance < 100))

    # Resource health degrades
    checks.append(("s9_health_drops", res_sim.resources["r0"].health_score() < 0.7))

    # Unloaded node is fine
    checks.append(("s9_unloaded_ok", res_sim.resources["r1"].health_score() > 0.7))

    # ── S10: Multi-Layer Scenario ─────────────────────────────────────
    scenario = ChaosScenario(num_nodes=10, seed=42)

    faults = [
        # Hardware crash on nodes 0-2 at t=2
        FaultSpec(FaultType.CRASH, SystemLayer.HARDWARE,
                  ["node_0", "node_1", "node_2"],
                  severity=1.0, duration_s=10.0, start_time=2.0),
        # Latency on transport for nodes 3,4 at t=3
        FaultSpec(FaultType.LATENCY, SystemLayer.TRANSPORT,
                  ["node_3", "node_4"],
                  severity=0.8, duration_s=8.0, start_time=3.0),
        # Packet loss on consensus for nodes 5,6 at t=4
        FaultSpec(FaultType.PACKET_LOSS, SystemLayer.CONSENSUS,
                  ["node_5", "node_6"],
                  severity=0.6, duration_s=6.0, start_time=4.0),
    ]

    result = scenario.run_scenario(faults, duration_s=30.0, step_s=0.5)
    checks.append(("s10_health_recovers", result["final_health"] > 0.5))
    checks.append(("s10_cascaded", result["cascade_events"] > 0))
    checks.append(("s10_cascade_bounded", result["cascade_depth"] <= 5))
    checks.append(("s10_min_health_drop", result["min_health"] < 0.9))
    checks.append(("s10_steady_state", result["steady_state"] > 0.5))

    # ── S11: Performance ──────────────────────────────────────────────
    # 100-node chaos scenario
    t0 = time.time()
    big_scenario = ChaosScenario(num_nodes=100, seed=123)
    big_faults = [
        FaultSpec(FaultType.CRASH, SystemLayer.HARDWARE,
                  [f"node_{i}" for i in range(10)],
                  severity=1.0, duration_s=5.0, start_time=1.0),
        FaultSpec(FaultType.LATENCY, SystemLayer.TRANSPORT,
                  [f"node_{i}" for i in range(10, 30)],
                  severity=0.5, duration_s=8.0, start_time=2.0),
    ]
    big_result = big_scenario.run_scenario(big_faults, duration_s=20.0, step_s=1.0)
    dt = time.time() - t0
    checks.append(("s11_100_node_chaos", dt < 10.0))
    checks.append(("s11_big_recovers", big_result["final_health"] > 0.3))

    # 10K fault injections
    t0 = time.time()
    perf_nodes = {f"pn{i}": SystemNode(f"pn{i}") for i in range(10)}
    perf_injector = FaultInjector()
    for i in range(10000):
        fault = FaultSpec(
            FaultType.LATENCY, SystemLayer.TRANSPORT,
            [f"pn{i % 10}"], severity=0.1, duration_s=0.1,
            start_time=float(i) * 0.01
        )
        perf_injector.inject(fault, perf_nodes)
    dt = time.time() - t0
    checks.append(("s11_10k_injections", dt < 5.0))

    # ── Report ────────────────────────────────────────────────────────
    passed = sum(1 for _, v in checks if v)
    total = len(checks)
    width = 60
    title = f"Cascading Failure & Chaos Engineering — {passed}/{total} checks passed"
    print("=" * width)
    print(f"  {title}")
    print("=" * width)
    for name, ok in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")
    print(f"\n  Time: {time.time() - t0:.2f}s\n")
    return passed == total


if __name__ == "__main__":
    success = run_checks()
    raise SystemExit(0 if success else 1)
