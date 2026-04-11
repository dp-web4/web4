"""
Reactive Trust Event Bus — Reference Implementation

Push-based trust state change propagation. Bridges transport abstraction
(Session 21), distributed tracing (Session 21), and observability
(Session 19) into a reactive streaming architecture.

Key features:
- Trust tensor change events with delta encoding
- Subscription model with entity/dimension/threshold filters
- Federation-aware event fan-out via gossip
- Back-pressure handling with flow control
- ATP-gated subscriptions (high-frequency costs more)
- Anomaly detection feeding into alarm escalation
- Causal ordering of trust events via vector clocks

Checks: 68
"""
from __future__ import annotations
import hashlib
import math
import secrets
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Set, Tuple


# ─── Trust Event Types ───────────────────────────────────────────────────────

class TrustDimension(Enum):
    TALENT = "talent"
    TRAINING = "training"
    TEMPERAMENT = "temperament"
    COMPOSITE = "composite"


class EventType(Enum):
    TRUST_DELTA = auto()        # Incremental T3 change
    TRUST_SNAPSHOT = auto()     # Full T3 state
    THRESHOLD_CROSSED = auto()  # Trust crossed a boundary
    ANOMALY_DETECTED = auto()   # Unusual trust pattern
    FEDERATION_SYNC = auto()    # Cross-node trust update
    SUBSCRIPTION_ACK = auto()   # Subscription confirmed


class EventPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class TrustDelta:
    """Delta encoding of a trust tensor change."""
    entity_id: str
    dimension: TrustDimension
    old_value: float
    new_value: float
    delta: float
    source: str         # What caused the change
    timestamp: float

    @property
    def magnitude(self) -> float:
        return abs(self.delta)


@dataclass
class TrustEvent:
    """A trust state change event."""
    event_id: str
    event_type: EventType
    entity_id: str
    deltas: List[TrustDelta]
    priority: EventPriority
    timestamp: float
    source_node: str = ""
    vector_clock: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def causal_hash(self) -> str:
        vc_str = ":".join(f"{k}={v}" for k, v in sorted(self.vector_clock.items()))
        return hashlib.sha256(
            f"{self.event_id}:{self.entity_id}:{vc_str}".encode()
        ).hexdigest()[:16]


# ─── Subscription Model ──────────────────────────────────────────────────────

@dataclass
class SubscriptionFilter:
    """Filter criteria for trust event subscriptions."""
    entity_ids: Optional[Set[str]] = None       # None = all entities
    dimensions: Optional[Set[TrustDimension]] = None  # None = all dims
    min_delta: float = 0.0                      # Minimum change magnitude
    threshold: Optional[float] = None           # Alert when crossing this value
    event_types: Optional[Set[EventType]] = None
    priority_min: EventPriority = EventPriority.LOW

    def matches(self, event: TrustEvent) -> bool:
        if self.entity_ids and event.entity_id not in self.entity_ids:
            return False
        if self.event_types and event.event_type not in self.event_types:
            return False
        if event.priority.value < self.priority_min.value:
            return False
        if self.dimensions and event.deltas:
            if not any(d.dimension in self.dimensions for d in event.deltas):
                return False
        if self.min_delta > 0 and event.deltas:
            if not any(d.magnitude >= self.min_delta for d in event.deltas):
                return False
        return True


@dataclass
class Subscription:
    """An active subscription to trust events."""
    sub_id: str
    subscriber_id: str
    filter: SubscriptionFilter
    callback: Optional[Callable[[TrustEvent], None]] = None
    created_at: float = field(default_factory=time.time)
    atp_cost_per_event: float = 0.01
    max_events_per_second: float = 100.0
    active: bool = True
    events_delivered: int = 0
    last_delivery: float = 0.0


# ─── Flow Control ────────────────────────────────────────────────────────────

class FlowControlStatus(Enum):
    OPEN = auto()
    THROTTLED = auto()
    BLOCKED = auto()


@dataclass
class FlowController:
    """Back-pressure handling for event delivery."""
    max_buffer_size: int = 1000
    throttle_threshold: float = 0.8  # Start throttling at 80% buffer
    block_threshold: float = 0.95    # Block at 95%

    buffer: List[TrustEvent] = field(default_factory=list)
    dropped: int = 0
    delivered: int = 0

    @property
    def status(self) -> FlowControlStatus:
        ratio = len(self.buffer) / max(self.max_buffer_size, 1)
        if ratio >= self.block_threshold:
            return FlowControlStatus.BLOCKED
        elif ratio >= self.throttle_threshold:
            return FlowControlStatus.THROTTLED
        return FlowControlStatus.OPEN

    def enqueue(self, event: TrustEvent) -> bool:
        if self.status == FlowControlStatus.BLOCKED:
            self.dropped += 1
            return False
        self.buffer.append(event)
        return True

    def dequeue(self, max_count: int = 10) -> List[TrustEvent]:
        batch = self.buffer[:max_count]
        self.buffer = self.buffer[max_count:]
        self.delivered += len(batch)
        return batch


# ─── Event Bus ────────────────────────────────────────────────────────────────

class TrustEventBus:
    """
    Core event bus for trust state changes.
    Supports pub/sub with filtering, flow control, and ATP gating.
    """

    def __init__(self, node_id: str = "local"):
        self.node_id = node_id
        self.subscriptions: Dict[str, Subscription] = {}
        self.flow_controllers: Dict[str, FlowController] = {}
        self.event_log: List[TrustEvent] = []
        self.vector_clock: Dict[str, int] = {node_id: 0}
        self.total_atp_collected: float = 0.0
        self._sub_counter = 0

    def subscribe(self, subscriber_id: str, filter: SubscriptionFilter,
                   callback: Optional[Callable] = None,
                   atp_cost: float = 0.01,
                   max_rate: float = 100.0) -> Subscription:
        self._sub_counter += 1
        sub_id = f"sub_{self._sub_counter}"
        sub = Subscription(
            sub_id=sub_id,
            subscriber_id=subscriber_id,
            filter=filter,
            callback=callback,
            atp_cost_per_event=atp_cost,
            max_events_per_second=max_rate,
        )
        self.subscriptions[sub_id] = sub
        self.flow_controllers[sub_id] = FlowController()
        return sub

    def unsubscribe(self, sub_id: str) -> bool:
        if sub_id in self.subscriptions:
            self.subscriptions[sub_id].active = False
            return True
        return False

    def _increment_clock(self) -> Dict[str, int]:
        self.vector_clock[self.node_id] = self.vector_clock.get(self.node_id, 0) + 1
        return dict(self.vector_clock)

    def publish(self, event: TrustEvent) -> int:
        """Publish a trust event. Returns number of subscribers notified."""
        event.vector_clock = self._increment_clock()
        event.source_node = self.node_id
        self.event_log.append(event)

        notified = 0
        for sub_id, sub in self.subscriptions.items():
            if not sub.active:
                continue
            if not sub.filter.matches(event):
                continue

            fc = self.flow_controllers[sub_id]
            if fc.enqueue(event):
                sub.events_delivered += 1
                sub.last_delivery = event.timestamp
                self.total_atp_collected += sub.atp_cost_per_event
                notified += 1

                if sub.callback:
                    batch = fc.dequeue(1)
                    for e in batch:
                        sub.callback(e)

        return notified

    def emit_delta(self, entity_id: str, dimension: TrustDimension,
                    old_value: float, new_value: float,
                    source: str = "system") -> TrustEvent:
        """Convenience: emit a trust delta event."""
        delta = TrustDelta(entity_id, dimension, old_value, new_value,
                           new_value - old_value, source, time.time())

        priority = EventPriority.NORMAL
        if abs(delta.delta) > 0.1:
            priority = EventPriority.HIGH
        if abs(delta.delta) > 0.3:
            priority = EventPriority.CRITICAL

        event = TrustEvent(
            event_id=f"evt_{secrets.token_hex(8)}",
            event_type=EventType.TRUST_DELTA,
            entity_id=entity_id,
            deltas=[delta],
            priority=priority,
            timestamp=time.time(),
        )
        self.publish(event)
        return event

    def emit_threshold_crossing(self, entity_id: str,
                                  dimension: TrustDimension,
                                  old_value: float, new_value: float,
                                  threshold: float) -> TrustEvent:
        """Emit an event when trust crosses a threshold."""
        delta = TrustDelta(entity_id, dimension, old_value, new_value,
                           new_value - old_value, "threshold_crossing", time.time())
        event = TrustEvent(
            event_id=f"evt_{secrets.token_hex(8)}",
            event_type=EventType.THRESHOLD_CROSSED,
            entity_id=entity_id,
            deltas=[delta],
            priority=EventPriority.HIGH,
            timestamp=time.time(),
            metadata={"threshold": threshold, "direction": "up" if new_value > old_value else "down"},
        )
        self.publish(event)
        return event


# ─── Anomaly Detection ───────────────────────────────────────────────────────

@dataclass
class AnomalyAlert:
    anomaly_type: str
    entity_id: str
    details: str
    severity: float
    timestamp: float


class TrustAnomalyDetector:
    """Detect unusual trust patterns from event streams."""

    def __init__(self, window_size: int = 50, spike_threshold: float = 0.15):
        self.window_size = window_size
        self.spike_threshold = spike_threshold
        self.entity_history: Dict[str, List[float]] = defaultdict(list)
        self.alerts: List[AnomalyAlert] = []

    def process_event(self, event: TrustEvent) -> List[AnomalyAlert]:
        alerts = []
        for delta in event.deltas:
            history = self.entity_history[event.entity_id]
            history.append(delta.delta)
            if len(history) > self.window_size:
                history.pop(0)

            # Spike detection: delta >> historical average
            if len(history) >= 5:
                avg = sum(abs(d) for d in history[:-1]) / (len(history) - 1)
                if avg > 0 and abs(delta.delta) > max(self.spike_threshold, avg * 3):
                    alert = AnomalyAlert(
                        "TRUST_SPIKE",
                        event.entity_id,
                        f"Delta {delta.delta:.4f} >> avg {avg:.4f} on {delta.dimension.value}",
                        min(1.0, abs(delta.delta) / max(avg, 0.001)),
                        event.timestamp,
                    )
                    alerts.append(alert)

            # Oscillation: alternating positive/negative with similar magnitude
            if len(history) >= 6:
                recent = history[-6:]
                signs = [1 if d > 0 else -1 for d in recent if d != 0]
                if len(signs) >= 6:
                    alternations = sum(1 for i in range(1, len(signs)) if signs[i] != signs[i-1])
                    if alternations >= 4:
                        alert = AnomalyAlert(
                            "TRUST_OSCILLATION",
                            event.entity_id,
                            f"Rapid oscillation detected ({alternations} alternations in 6 events)",
                            0.6,
                            event.timestamp,
                        )
                        alerts.append(alert)

            # Monotone decline: steady negative trend
            if len(history) >= 10:
                recent = history[-10:]
                negative_count = sum(1 for d in recent if d < 0)
                if negative_count >= 8:
                    alert = AnomalyAlert(
                        "MONOTONE_DECLINE",
                        event.entity_id,
                        f"{negative_count}/10 recent deltas are negative",
                        0.7,
                        event.timestamp,
                    )
                    alerts.append(alert)

        self.alerts.extend(alerts)
        return alerts


# ─── Federation Event Fan-out ─────────────────────────────────────────────────

@dataclass
class FederationNode:
    node_id: str
    vector_clock: Dict[str, int] = field(default_factory=dict)
    received_events: List[TrustEvent] = field(default_factory=list)


class FederationEventSync:
    """Cross-node trust event propagation via gossip."""

    def __init__(self, fan_out: int = 3):
        self.fan_out = fan_out
        self.nodes: Dict[str, FederationNode] = {}
        self.gossip_rounds: int = 0
        self.total_messages: int = 0

    def add_node(self, node_id: str) -> FederationNode:
        node = FederationNode(node_id)
        self.nodes[node_id] = node
        return node

    def merge_vector_clocks(self, vc1: Dict[str, int],
                             vc2: Dict[str, int]) -> Dict[str, int]:
        merged = dict(vc1)
        for k, v in vc2.items():
            merged[k] = max(merged.get(k, 0), v)
        return merged

    def is_causally_before(self, vc1: Dict[str, int],
                            vc2: Dict[str, int]) -> bool:
        """Check if vc1 happens-before vc2."""
        all_keys = set(vc1.keys()) | set(vc2.keys())
        at_least_one_less = False
        for k in all_keys:
            v1 = vc1.get(k, 0)
            v2 = vc2.get(k, 0)
            if v1 > v2:
                return False
            if v1 < v2:
                at_least_one_less = True
        return at_least_one_less

    def propagate_event(self, source_node_id: str, event: TrustEvent,
                         rng=None) -> int:
        """Gossip-propagate an event from source to neighbors."""
        import random
        rng = rng or random.Random(42)

        source = self.nodes.get(source_node_id)
        if not source:
            return 0

        source.received_events.append(event)
        source.vector_clock = self.merge_vector_clocks(source.vector_clock, event.vector_clock)

        # Gossip: select fan_out random neighbors
        others = [nid for nid in self.nodes if nid != source_node_id]
        targets = rng.sample(others, min(self.fan_out, len(others)))

        delivered = 0
        for target_id in targets:
            target = self.nodes[target_id]
            # Check if target already has this event
            if any(e.event_id == event.event_id for e in target.received_events):
                continue
            target.received_events.append(event)
            target.vector_clock = self.merge_vector_clocks(
                target.vector_clock, event.vector_clock)
            delivered += 1
            self.total_messages += 1

        self.gossip_rounds += 1
        return delivered

    def full_propagation(self, source_node_id: str, event: TrustEvent,
                          max_rounds: int = 20) -> int:
        """Run gossip until all nodes have the event."""
        import random
        rng = random.Random(42)

        source = self.nodes[source_node_id]
        source.received_events.append(event)
        source.vector_clock = self.merge_vector_clocks(source.vector_clock, event.vector_clock)

        for _ in range(max_rounds):
            # All infected nodes gossip
            infected = [nid for nid, n in self.nodes.items()
                        if any(e.event_id == event.event_id for e in n.received_events)]
            if len(infected) == len(self.nodes):
                break

            for nid in infected:
                others = [n for n in self.nodes if n != nid]
                targets = rng.sample(others, min(self.fan_out, len(others)))
                for tid in targets:
                    target = self.nodes[tid]
                    if not any(e.event_id == event.event_id for e in target.received_events):
                        target.received_events.append(event)
                        target.vector_clock = self.merge_vector_clocks(
                            target.vector_clock, event.vector_clock)
                        self.total_messages += 1

            self.gossip_rounds += 1

        return sum(1 for n in self.nodes.values()
                   if any(e.event_id == event.event_id for e in n.received_events))


# ─── ATP-Gated Subscriptions ─────────────────────────────────────────────────

class ATPGatedBus(TrustEventBus):
    """Event bus where subscriptions cost ATP."""

    def __init__(self, node_id: str = "local"):
        super().__init__(node_id)
        self.balances: Dict[str, float] = {}

    def set_balance(self, subscriber_id: str, balance: float):
        self.balances[subscriber_id] = balance

    def subscribe_gated(self, subscriber_id: str, filter: SubscriptionFilter,
                         atp_cost: float = 0.01) -> Optional[Subscription]:
        balance = self.balances.get(subscriber_id, 0)
        if balance < atp_cost * 10:  # Need at least 10 events worth
            return None
        return self.subscribe(subscriber_id, filter, atp_cost=atp_cost)

    def publish(self, event: TrustEvent) -> int:
        """Publish with ATP deduction."""
        event.vector_clock = self._increment_clock()
        event.source_node = self.node_id
        self.event_log.append(event)

        notified = 0
        for sub_id, sub in self.subscriptions.items():
            if not sub.active:
                continue
            if not sub.filter.matches(event):
                continue

            # Check ATP balance
            balance = self.balances.get(sub.subscriber_id, 0)
            if balance < sub.atp_cost_per_event:
                sub.active = False  # Deactivate when funds exhausted
                continue

            fc = self.flow_controllers[sub_id]
            if fc.enqueue(event):
                self.balances[sub.subscriber_id] -= sub.atp_cost_per_event
                self.total_atp_collected += sub.atp_cost_per_event
                sub.events_delivered += 1
                notified += 1

                if sub.callback:
                    batch = fc.dequeue(1)
                    for e in batch:
                        sub.callback(e)

        return notified


# ─── Alarm Escalation Pipeline ────────────────────────────────────────────────

class AlarmLevel(Enum):
    INFO = 1
    WARNING = 2
    ALERT = 3
    CRITICAL = 4


@dataclass
class Alarm:
    alarm_id: str
    level: AlarmLevel
    source: str
    message: str
    entity_id: str
    timestamp: float
    acknowledged: bool = False


class AlarmPipeline:
    """Escalation pipeline: anomaly → alarm → action."""

    def __init__(self):
        self.alarms: List[Alarm] = []
        self.escalation_rules: Dict[str, AlarmLevel] = {
            "TRUST_SPIKE": AlarmLevel.ALERT,
            "TRUST_OSCILLATION": AlarmLevel.WARNING,
            "MONOTONE_DECLINE": AlarmLevel.CRITICAL,
        }

    def process_anomaly(self, anomaly: AnomalyAlert) -> Alarm:
        level = self.escalation_rules.get(anomaly.anomaly_type, AlarmLevel.INFO)
        # Severity can escalate level
        if anomaly.severity > 0.8 and level.value < AlarmLevel.CRITICAL.value:
            level = AlarmLevel(level.value + 1)

        alarm = Alarm(
            alarm_id=f"alarm_{secrets.token_hex(6)}",
            level=level,
            source=anomaly.anomaly_type,
            message=anomaly.details,
            entity_id=anomaly.entity_id,
            timestamp=anomaly.timestamp,
        )
        self.alarms.append(alarm)
        return alarm

    def acknowledge(self, alarm_id: str) -> bool:
        for a in self.alarms:
            if a.alarm_id == alarm_id:
                a.acknowledged = True
                return True
        return False

    def unacknowledged(self, min_level: AlarmLevel = AlarmLevel.WARNING) -> List[Alarm]:
        return [a for a in self.alarms
                if not a.acknowledged and a.level.value >= min_level.value]


# ─── Checks ──────────────────────────────────────────────────────────────────

def run_checks():
    checks = []
    t0 = time.time()

    # ── S1: Trust Delta Events ────────────────────────────────────────────
    delta = TrustDelta("entity_1", TrustDimension.TALENT, 0.7, 0.75, 0.05,
                        "witness", time.time())
    checks.append(("s1_delta_magnitude", abs(delta.magnitude - 0.05) < 0.001))

    event = TrustEvent(
        event_id="evt_001",
        event_type=EventType.TRUST_DELTA,
        entity_id="entity_1",
        deltas=[delta],
        priority=EventPriority.NORMAL,
        timestamp=time.time(),
    )
    checks.append(("s1_event_has_id", event.event_id == "evt_001"))
    checks.append(("s1_causal_hash", len(event.causal_hash()) == 16))

    # ── S2: Subscription Filters ──────────────────────────────────────────
    f1 = SubscriptionFilter(entity_ids={"entity_1"})
    checks.append(("s2_entity_match", f1.matches(event)))
    f2 = SubscriptionFilter(entity_ids={"entity_2"})
    checks.append(("s2_entity_no_match", not f2.matches(event)))

    f3 = SubscriptionFilter(dimensions={TrustDimension.TALENT})
    checks.append(("s2_dim_match", f3.matches(event)))
    f4 = SubscriptionFilter(dimensions={TrustDimension.TEMPERAMENT})
    checks.append(("s2_dim_no_match", not f4.matches(event)))

    f5 = SubscriptionFilter(min_delta=0.1)
    checks.append(("s2_min_delta_no_match", not f5.matches(event)))
    f6 = SubscriptionFilter(min_delta=0.01)
    checks.append(("s2_min_delta_match", f6.matches(event)))

    f7 = SubscriptionFilter(priority_min=EventPriority.HIGH)
    checks.append(("s2_priority_no_match", not f7.matches(event)))

    # ── S3: Event Bus Publish/Subscribe ───────────────────────────────────
    bus = TrustEventBus("node_1")
    received = []
    sub = bus.subscribe("watcher_1",
                         SubscriptionFilter(entity_ids={"entity_A"}),
                         callback=lambda e: received.append(e))
    checks.append(("s3_sub_created", sub.sub_id is not None))

    evt = bus.emit_delta("entity_A", TrustDimension.TRAINING, 0.5, 0.55, "action")
    checks.append(("s3_event_published", len(bus.event_log) == 1))
    checks.append(("s3_callback_fired", len(received) == 1))
    checks.append(("s3_atp_collected", bus.total_atp_collected > 0))

    # Non-matching entity → not delivered
    bus.emit_delta("entity_B", TrustDimension.TALENT, 0.6, 0.65, "action")
    checks.append(("s3_filter_works", len(received) == 1))

    # Unsubscribe
    bus.unsubscribe(sub.sub_id)
    bus.emit_delta("entity_A", TrustDimension.TALENT, 0.5, 0.55, "action")
    checks.append(("s3_unsubscribed", len(received) == 1))

    # ── S4: Priority-Based Events ─────────────────────────────────────────
    bus2 = TrustEventBus("node_2")
    # Small delta → NORMAL
    e_small = bus2.emit_delta("e1", TrustDimension.TALENT, 0.5, 0.52, "minor")
    checks.append(("s4_small_normal", e_small.priority == EventPriority.NORMAL))

    # Large delta → HIGH
    e_large = bus2.emit_delta("e1", TrustDimension.TALENT, 0.5, 0.65, "major")
    checks.append(("s4_large_high", e_large.priority == EventPriority.HIGH))

    # Huge delta → CRITICAL
    e_huge = bus2.emit_delta("e1", TrustDimension.TALENT, 0.5, 0.85, "crisis")
    checks.append(("s4_huge_critical", e_huge.priority == EventPriority.CRITICAL))

    # ── S5: Threshold Crossing ────────────────────────────────────────────
    bus3 = TrustEventBus("node_3")
    threshold_events = []
    bus3.subscribe("watcher_th",
                    SubscriptionFilter(event_types={EventType.THRESHOLD_CROSSED}),
                    callback=lambda e: threshold_events.append(e))
    bus3.emit_threshold_crossing("e2", TrustDimension.TEMPERAMENT, 0.49, 0.51, 0.5)
    checks.append(("s5_threshold_event", len(threshold_events) == 1))
    checks.append(("s5_threshold_direction",
                    threshold_events[0].metadata.get("direction") == "up"))

    # ── S6: Flow Control ─────────────────────────────────────────────────
    fc = FlowController(max_buffer_size=10)
    checks.append(("s6_initial_open", fc.status == FlowControlStatus.OPEN))

    for i in range(8):
        evt_fc = TrustEvent(f"fc_{i}", EventType.TRUST_DELTA, "e1", [],
                             EventPriority.NORMAL, time.time())
        fc.enqueue(evt_fc)
    checks.append(("s6_throttled", fc.status == FlowControlStatus.THROTTLED))

    fc.enqueue(TrustEvent("fc_8", EventType.TRUST_DELTA, "e1", [],
                            EventPriority.NORMAL, time.time()))
    fc.enqueue(TrustEvent("fc_9", EventType.TRUST_DELTA, "e1", [],
                            EventPriority.NORMAL, time.time()))
    # 10 items in buffer of 10 = blocked
    blocked = not fc.enqueue(TrustEvent("fc_10", EventType.TRUST_DELTA, "e1", [],
                                          EventPriority.NORMAL, time.time()))
    checks.append(("s6_blocked", blocked))
    checks.append(("s6_dropped", fc.dropped == 1))

    batch = fc.dequeue(5)
    checks.append(("s6_dequeue_5", len(batch) == 5))
    checks.append(("s6_after_dequeue_open", fc.status == FlowControlStatus.OPEN))

    # ── S7: Anomaly Detection ─────────────────────────────────────────────
    detector = TrustAnomalyDetector(window_size=20, spike_threshold=0.1)

    # Build baseline with small deltas
    for i in range(10):
        e = TrustEvent(f"norm_{i}", EventType.TRUST_DELTA, "entity_X",
                        [TrustDelta("entity_X", TrustDimension.TALENT,
                                     0.5 + i * 0.01, 0.5 + (i + 1) * 0.01, 0.01,
                                     "normal", time.time())],
                        EventPriority.NORMAL, time.time())
        detector.process_event(e)

    # Spike: sudden large delta
    spike_event = TrustEvent("spike", EventType.TRUST_DELTA, "entity_X",
                              [TrustDelta("entity_X", TrustDimension.TALENT,
                                           0.6, 0.9, 0.3, "attack", time.time())],
                              EventPriority.CRITICAL, time.time())
    spike_alerts = detector.process_event(spike_event)
    checks.append(("s7_spike_detected", any(a.anomaly_type == "TRUST_SPIKE" for a in spike_alerts)))

    # Oscillation detection
    detector2 = TrustAnomalyDetector(window_size=20)
    for i in range(8):
        sign = 1 if i % 2 == 0 else -1
        e = TrustEvent(f"osc_{i}", EventType.TRUST_DELTA, "entity_Y",
                        [TrustDelta("entity_Y", TrustDimension.TRAINING,
                                     0.5, 0.5 + sign * 0.05, sign * 0.05,
                                     "oscillation", time.time())],
                        EventPriority.NORMAL, time.time())
        osc_alerts = detector2.process_event(e)

    checks.append(("s7_oscillation_detected",
                    any(a.anomaly_type == "TRUST_OSCILLATION" for a in detector2.alerts)))

    # Monotone decline
    detector3 = TrustAnomalyDetector(window_size=20)
    for i in range(12):
        e = TrustEvent(f"dec_{i}", EventType.TRUST_DELTA, "entity_Z",
                        [TrustDelta("entity_Z", TrustDimension.TEMPERAMENT,
                                     0.5 - i * 0.02, 0.5 - (i + 1) * 0.02, -0.02,
                                     "decay", time.time())],
                        EventPriority.NORMAL, time.time())
        detector3.process_event(e)
    checks.append(("s7_decline_detected",
                    any(a.anomaly_type == "MONOTONE_DECLINE" for a in detector3.alerts)))

    # ── S8: Federation Gossip ─────────────────────────────────────────────
    fed = FederationEventSync(fan_out=3)
    for i in range(20):
        fed.add_node(f"node_{i}")

    gossip_event = TrustEvent("fed_evt", EventType.TRUST_DELTA, "e_fed",
                                [TrustDelta("e_fed", TrustDimension.TALENT,
                                             0.5, 0.6, 0.1, "update", time.time())],
                                EventPriority.HIGH, time.time(),
                                vector_clock={"node_0": 1})

    reached = fed.full_propagation("node_0", gossip_event)
    checks.append(("s8_full_coverage", reached == 20))
    checks.append(("s8_gossip_efficient", fed.total_messages < 20 * 19))  # Much less than broadcast

    # ── S9: Vector Clock Ordering ─────────────────────────────────────────
    checks.append(("s9_before",
                    fed.is_causally_before({"a": 1, "b": 2}, {"a": 2, "b": 3})))
    checks.append(("s9_not_before",
                    not fed.is_causally_before({"a": 2, "b": 3}, {"a": 1, "b": 2})))
    checks.append(("s9_concurrent",
                    not fed.is_causally_before({"a": 1, "b": 3}, {"a": 2, "b": 2})))
    checks.append(("s9_equal_not_before",
                    not fed.is_causally_before({"a": 1}, {"a": 1})))

    merged = fed.merge_vector_clocks({"a": 1, "b": 3}, {"a": 2, "c": 1})
    checks.append(("s9_merge", merged == {"a": 2, "b": 3, "c": 1}))

    # ── S10: ATP-Gated Bus ────────────────────────────────────────────────
    gated_bus = ATPGatedBus("gated_node")
    gated_bus.set_balance("rich", 100.0)
    gated_bus.set_balance("poor", 0.05)

    rich_sub = gated_bus.subscribe_gated("rich", SubscriptionFilter(), atp_cost=0.1)
    checks.append(("s10_rich_sub", rich_sub is not None))

    poor_sub = gated_bus.subscribe_gated("poor", SubscriptionFilter(), atp_cost=0.1)
    checks.append(("s10_poor_denied", poor_sub is None))

    # Rich receives events until balance depleted
    for i in range(5):
        gated_bus.publish(TrustEvent(
            f"gated_{i}", EventType.TRUST_DELTA, "e1", [],
            EventPriority.NORMAL, time.time()))
    checks.append(("s10_rich_received", rich_sub.events_delivered == 5))
    checks.append(("s10_atp_deducted", gated_bus.balances["rich"] < 100.0))

    # ── S11: Alarm Pipeline ───────────────────────────────────────────────
    pipeline = AlarmPipeline()
    spike_anomaly = AnomalyAlert("TRUST_SPIKE", "e_alarm", "Large delta", 0.9, time.time())
    alarm = pipeline.process_anomaly(spike_anomaly)
    checks.append(("s11_alarm_created", alarm.level == AlarmLevel.CRITICAL))  # 0.9 severity escalates
    checks.append(("s11_not_acked", not alarm.acknowledged))

    decline_anomaly = AnomalyAlert("MONOTONE_DECLINE", "e_alarm2", "Steady decline", 0.7, time.time())
    alarm2 = pipeline.process_anomaly(decline_anomaly)
    checks.append(("s11_decline_critical", alarm2.level == AlarmLevel.CRITICAL))

    unacked = pipeline.unacknowledged()
    checks.append(("s11_unacked_count", len(unacked) == 2))

    pipeline.acknowledge(alarm.alarm_id)
    checks.append(("s11_acked", len(pipeline.unacknowledged()) == 1))

    # ── S12: Multi-Subscriber Fan-out ─────────────────────────────────────
    bus4 = TrustEventBus("node_fan")
    counts = {"a": 0, "b": 0, "c": 0}

    bus4.subscribe("sub_a", SubscriptionFilter(dimensions={TrustDimension.TALENT}),
                    callback=lambda e: counts.__setitem__("a", counts["a"] + 1))
    bus4.subscribe("sub_b", SubscriptionFilter(dimensions={TrustDimension.TRAINING}),
                    callback=lambda e: counts.__setitem__("b", counts["b"] + 1))
    bus4.subscribe("sub_c", SubscriptionFilter(),  # all events
                    callback=lambda e: counts.__setitem__("c", counts["c"] + 1))

    bus4.emit_delta("e1", TrustDimension.TALENT, 0.5, 0.6, "test")
    checks.append(("s12_a_received", counts["a"] == 1))
    checks.append(("s12_b_not_received", counts["b"] == 0))
    checks.append(("s12_c_received", counts["c"] == 1))

    bus4.emit_delta("e1", TrustDimension.TRAINING, 0.5, 0.6, "test")
    checks.append(("s12_b_now_received", counts["b"] == 1))
    checks.append(("s12_c_both", counts["c"] == 2))

    # ── S13: Event Bus Vector Clocks ──────────────────────────────────────
    bus5 = TrustEventBus("node_vc")
    e1 = bus5.emit_delta("e1", TrustDimension.TALENT, 0.5, 0.6, "t1")
    e2 = bus5.emit_delta("e1", TrustDimension.TRAINING, 0.5, 0.6, "t2")
    checks.append(("s13_vc_incrementing",
                    e2.vector_clock["node_vc"] > e1.vector_clock["node_vc"]))

    # ── S14: Performance ──────────────────────────────────────────────────
    perf_bus = TrustEventBus("perf")
    for i in range(10):
        perf_bus.subscribe(f"perf_sub_{i}", SubscriptionFilter())

    pt0 = time.time()
    for i in range(1000):
        perf_bus.emit_delta(f"e_{i % 100}", TrustDimension.TALENT,
                             0.5, 0.5 + (i % 10) * 0.01, "perf")
    pt1 = time.time()
    checks.append(("s14_1000_events_under_2s", pt1 - pt0 < 2.0))
    checks.append(("s14_all_logged", len(perf_bus.event_log) == 1000))

    elapsed = time.time() - t0

    # ── Print Results ─────────────────────────────────────────────────────
    passed = sum(1 for _, v in checks if v)
    total = len(checks)
    title = f"Reactive Trust Event Bus — {passed}/{total} checks passed"
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")
    for name, val in checks:
        print(f"  [{'PASS' if val else 'FAIL'}] {name}")

    failed = [n for n, v in checks if not v]
    if failed:
        print(f"\n  FAILURES:")
        for f in failed:
            print(f"    ✗ {f}")

    print(f"\n  Time: {elapsed:.2f}s\n")
    return passed == total


if __name__ == "__main__":
    run_checks()
