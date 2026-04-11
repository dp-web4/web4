"""
Observability & Trust Telemetry
================================

Implements operational telemetry for Web4 federations: distributed
tracing of ATP flows, trust tensor evolution metrics, event streaming
with immutable logs, SPARQL-like query interface over trust graphs,
and anomaly detection (sybil bursts, trust entropy spikes, partition
detection).

Sections:
  S1  — Event Log & Immutable Append
  S2  — Distributed Tracing (span-based)
  S3  — Trust Tensor Time Series
  S4  — ATP Flow Tracing
  S5  — Federation Health Metrics
  S6  — Anomaly Detection (sybil, entropy, partition)
  S7  — Alerting & Threshold Engine
  S8  — Query Interface (filter, aggregate, window)
  S9  — Dashboard Aggregation
  S10 — Retention & Compaction
  S11 — Performance Under Load
"""

from __future__ import annotations
import math
import time
import random
import hashlib
import json
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any, Set, Callable
from collections import defaultdict, deque
from enum import Enum


# ============================================================
# S1 — Event Log & Immutable Append
# ============================================================

class EventType(Enum):
    ENTITY_BIRTH = "entity_birth"
    ENTITY_REVOKE = "entity_revoke"
    TRUST_UPDATE = "trust_update"
    ATP_TRANSFER = "atp_transfer"
    ATP_MINT = "atp_mint"
    ATP_BURN = "atp_burn"
    DELEGATION_GRANT = "delegation_grant"
    DELEGATION_REVOKE = "delegation_revoke"
    FEDERATION_JOIN = "federation_join"
    FEDERATION_LEAVE = "federation_leave"
    CONSENSUS_ROUND = "consensus_round"
    ALERT_TRIGGERED = "alert_triggered"


@dataclass
class Event:
    event_type: EventType
    timestamp: float
    entity_id: str
    data: Dict[str, Any]
    sequence: int = 0
    prev_hash: str = ""
    event_hash: str = ""

    def compute_hash(self) -> str:
        content = f"{self.event_type.value}:{self.timestamp}:{self.entity_id}:{json.dumps(self.data, sort_keys=True)}:{self.sequence}:{self.prev_hash}"
        return hashlib.sha256(content.encode()).hexdigest()

    def seal(self):
        self.event_hash = self.compute_hash()


@dataclass
class EventLog:
    events: List[Event] = field(default_factory=list)
    _hash_index: Dict[str, int] = field(default_factory=dict)
    _entity_index: Dict[str, List[int]] = field(default_factory=lambda: defaultdict(list))
    _type_index: Dict[EventType, List[int]] = field(default_factory=lambda: defaultdict(list))

    def append(self, event_type: EventType, entity_id: str, data: Dict[str, Any],
               timestamp: Optional[float] = None) -> Event:
        seq = len(self.events)
        prev_hash = self.events[-1].event_hash if self.events else "genesis"
        evt = Event(
            event_type=event_type,
            timestamp=timestamp if timestamp is not None else time.time(),
            entity_id=entity_id,
            data=data,
            sequence=seq,
            prev_hash=prev_hash,
        )
        evt.seal()
        self.events.append(evt)
        self._hash_index[evt.event_hash] = seq
        self._entity_index[entity_id].append(seq)
        self._type_index[event_type].append(seq)
        return evt

    def verify_chain(self) -> bool:
        for i, evt in enumerate(self.events):
            if evt.compute_hash() != evt.event_hash:
                return False
            if i == 0:
                if evt.prev_hash != "genesis":
                    return False
            else:
                if evt.prev_hash != self.events[i - 1].event_hash:
                    return False
        return True

    def by_entity(self, entity_id: str) -> List[Event]:
        return [self.events[i] for i in self._entity_index.get(entity_id, [])]

    def by_type(self, event_type: EventType) -> List[Event]:
        return [self.events[i] for i in self._type_index.get(event_type, [])]

    def range_query(self, start_time: float, end_time: float) -> List[Event]:
        return [e for e in self.events if start_time <= e.timestamp <= end_time]


def test_section_1():
    checks = []

    log = EventLog()

    # Append events
    e1 = log.append(EventType.ENTITY_BIRTH, "alice", {"trust": 0.5})
    e2 = log.append(EventType.ATP_MINT, "alice", {"amount": 100.0})
    e3 = log.append(EventType.TRUST_UPDATE, "alice", {"talent": 0.6, "training": 0.5, "temperament": 0.7})

    checks.append(("three_events", len(log.events) == 3))
    checks.append(("chain_valid", log.verify_chain()))
    checks.append(("genesis_link", e1.prev_hash == "genesis"))
    checks.append(("chain_linked", e2.prev_hash == e1.event_hash))

    # Tamper detection
    log.events[1].data["amount"] = 999.0
    checks.append(("tamper_detected", not log.verify_chain()))
    log.events[1].data["amount"] = 100.0  # restore
    log.events[1].seal()  # re-seal: original data → original hash → chain heals (binding property)
    checks.append(("reseal_heals_chain", log.verify_chain()))

    # Fresh log for indexing
    log2 = EventLog()
    log2.append(EventType.ENTITY_BIRTH, "alice", {}, timestamp=1.0)
    log2.append(EventType.ENTITY_BIRTH, "bob", {}, timestamp=2.0)
    log2.append(EventType.TRUST_UPDATE, "alice", {"t": 0.6}, timestamp=3.0)
    log2.append(EventType.ATP_TRANSFER, "alice", {"to": "bob", "amount": 50}, timestamp=4.0)

    checks.append(("entity_index", len(log2.by_entity("alice")) == 3))
    checks.append(("type_index", len(log2.by_type(EventType.ENTITY_BIRTH)) == 2))
    checks.append(("range_query", len(log2.range_query(2.0, 3.5)) == 2))

    return checks


# ============================================================
# S2 — Distributed Tracing (span-based)
# ============================================================

@dataclass
class Span:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation: str
    entity_id: str
    start_time: float
    end_time: float = 0.0
    tags: Dict[str, str] = field(default_factory=dict)
    status: str = "ok"

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time if self.end_time > 0 else 0.0


@dataclass
class TraceCollector:
    spans: List[Span] = field(default_factory=list)
    _trace_index: Dict[str, List[int]] = field(default_factory=lambda: defaultdict(list))
    _counter: int = 0

    def _next_id(self) -> str:
        self._counter += 1
        return hashlib.sha256(f"span-{self._counter}".encode()).hexdigest()[:16]

    def start_trace(self, operation: str, entity_id: str,
                    start_time: float = 0.0) -> Span:
        trace_id = self._next_id()
        span = Span(
            trace_id=trace_id,
            span_id=self._next_id(),
            parent_span_id=None,
            operation=operation,
            entity_id=entity_id,
            start_time=start_time,
        )
        idx = len(self.spans)
        self.spans.append(span)
        self._trace_index[trace_id].append(idx)
        return span

    def start_child(self, parent: Span, operation: str, entity_id: str,
                    start_time: float = 0.0) -> Span:
        span = Span(
            trace_id=parent.trace_id,
            span_id=self._next_id(),
            parent_span_id=parent.span_id,
            operation=operation,
            entity_id=entity_id,
            start_time=start_time,
        )
        idx = len(self.spans)
        self.spans.append(span)
        self._trace_index[parent.trace_id].append(idx)
        return span

    def finish(self, span: Span, end_time: float = 0.0, status: str = "ok"):
        span.end_time = end_time
        span.status = status

    def trace_spans(self, trace_id: str) -> List[Span]:
        return [self.spans[i] for i in self._trace_index.get(trace_id, [])]

    def trace_tree(self, trace_id: str) -> Dict[str, List[Span]]:
        """Return {parent_span_id: [children]}."""
        spans = self.trace_spans(trace_id)
        tree = defaultdict(list)
        for s in spans:
            tree[s.parent_span_id or "root"].append(s)
        return dict(tree)


def test_section_2():
    checks = []

    tc = TraceCollector()

    # Simulate ATP transfer trace
    root = tc.start_trace("atp_transfer", "alice", start_time=0.0)
    validate = tc.start_child(root, "validate_balance", "alice", start_time=0.1)
    tc.finish(validate, end_time=0.2)
    debit = tc.start_child(root, "debit_sender", "alice", start_time=0.2)
    tc.finish(debit, end_time=0.3)
    credit = tc.start_child(root, "credit_receiver", "bob", start_time=0.3)
    tc.finish(credit, end_time=0.4)
    reputation = tc.start_child(root, "update_reputation", "alice", start_time=0.4)
    tc.finish(reputation, end_time=0.5)
    tc.finish(root, end_time=0.5)

    # Trace structure
    spans = tc.trace_spans(root.trace_id)
    checks.append(("trace_5_spans", len(spans) == 5))
    checks.append(("root_duration", abs(root.duration - 0.5) < 0.01))
    checks.append(("child_links", all(s.parent_span_id == root.span_id
                                      for s in spans if s != root)))

    # Tree structure
    tree = tc.trace_tree(root.trace_id)
    checks.append(("tree_root", len(tree.get("root", [])) == 1))
    checks.append(("tree_children", len(tree.get(root.span_id, [])) == 4))

    # Cross-entity trace
    entities = set(s.entity_id for s in spans)
    checks.append(("cross_entity", len(entities) == 2))

    # Error trace
    err_root = tc.start_trace("failed_transfer", "charlie", start_time=1.0)
    err_val = tc.start_child(err_root, "validate_balance", "charlie", start_time=1.1)
    tc.finish(err_val, end_time=1.2, status="error:insufficient_balance")
    tc.finish(err_root, end_time=1.2, status="error")
    checks.append(("error_status", err_root.status == "error"))

    return checks


# ============================================================
# S3 — Trust Tensor Time Series
# ============================================================

@dataclass
class TrustSnapshot:
    entity_id: str
    timestamp: float
    talent: float
    training: float
    temperament: float

    @property
    def composite(self) -> float:
        return (self.talent + self.training + self.temperament) / 3.0


@dataclass
class TrustTimeSeries:
    """Track trust tensor evolution per entity."""
    snapshots: Dict[str, List[TrustSnapshot]] = field(default_factory=lambda: defaultdict(list))

    def record(self, entity_id: str, timestamp: float,
               talent: float, training: float, temperament: float):
        snap = TrustSnapshot(entity_id, timestamp, talent, training, temperament)
        self.snapshots[entity_id].append(snap)

    def latest(self, entity_id: str) -> Optional[TrustSnapshot]:
        snaps = self.snapshots.get(entity_id, [])
        return snaps[-1] if snaps else None

    def velocity(self, entity_id: str) -> Optional[float]:
        """Rate of change of composite trust per time unit."""
        snaps = self.snapshots.get(entity_id, [])
        if len(snaps) < 2:
            return None
        dt = snaps[-1].timestamp - snaps[-2].timestamp
        if dt == 0:
            return 0.0
        dc = snaps[-1].composite - snaps[-2].composite
        return dc / dt

    def moving_average(self, entity_id: str, window: int = 5) -> Optional[float]:
        snaps = self.snapshots.get(entity_id, [])
        if not snaps:
            return None
        recent = snaps[-window:]
        return sum(s.composite for s in recent) / len(recent)

    def volatility(self, entity_id: str, window: int = 10) -> Optional[float]:
        """Standard deviation of composite trust over window."""
        snaps = self.snapshots.get(entity_id, [])
        if len(snaps) < 2:
            return None
        recent = snaps[-window:]
        composites = [s.composite for s in recent]
        mean = sum(composites) / len(composites)
        var = sum((c - mean) ** 2 for c in composites) / len(composites)
        return math.sqrt(var)


def test_section_3():
    checks = []

    ts = TrustTimeSeries()

    # Record evolution
    for t in range(20):
        talent = 0.3 + 0.02 * t + random.uniform(-0.01, 0.01)
        training = 0.4 + 0.015 * t
        temperament = 0.5 + 0.01 * t
        ts.record("alice", float(t), min(0.95, talent), min(0.95, training), min(0.95, temperament))

    checks.append(("recorded_20", len(ts.snapshots["alice"]) == 20))

    latest = ts.latest("alice")
    checks.append(("latest_exists", latest is not None))
    checks.append(("latest_high", latest.composite > 0.5))

    vel = ts.velocity("alice")
    checks.append(("positive_velocity", vel is not None and vel > 0))

    ma = ts.moving_average("alice", window=5)
    checks.append(("ma_computed", ma is not None and 0 < ma < 1))

    vol = ts.volatility("alice", window=10)
    checks.append(("low_volatility", vol is not None and vol < 0.2))

    # Declining trust
    for t in range(20, 30):
        ts.record("bob", float(t), 0.8 - 0.03 * (t - 20), 0.7 - 0.02 * (t - 20), 0.6 - 0.01 * (t - 20))

    vel_bob = ts.velocity("bob")
    checks.append(("negative_velocity", vel_bob is not None and vel_bob < 0))

    return checks


# ============================================================
# S4 — ATP Flow Tracing
# ============================================================

@dataclass
class ATPFlowRecord:
    from_entity: str
    to_entity: str
    amount: float
    fee: float
    timestamp: float
    flow_type: str  # "transfer", "mint", "burn", "stake", "reward"
    trace_id: str = ""


@dataclass
class ATPFlowTracer:
    flows: List[ATPFlowRecord] = field(default_factory=list)
    _entity_outflows: Dict[str, List[int]] = field(default_factory=lambda: defaultdict(list))
    _entity_inflows: Dict[str, List[int]] = field(default_factory=lambda: defaultdict(list))

    def record(self, from_entity: str, to_entity: str, amount: float,
               fee: float, timestamp: float, flow_type: str, trace_id: str = ""):
        idx = len(self.flows)
        self.flows.append(ATPFlowRecord(from_entity, to_entity, amount, fee,
                                        timestamp, flow_type, trace_id))
        self._entity_outflows[from_entity].append(idx)
        self._entity_inflows[to_entity].append(idx)

    def net_flow(self, entity_id: str) -> float:
        inflow = sum(self.flows[i].amount for i in self._entity_inflows.get(entity_id, []))
        outflow = sum(self.flows[i].amount + self.flows[i].fee
                      for i in self._entity_outflows.get(entity_id, []))
        return inflow - outflow

    def total_fees(self) -> float:
        return sum(f.fee for f in self.flows)

    def circular_flow_ratio(self, entity_id: str) -> float:
        """Detect wash trading: ratio of bidirectional flows."""
        out_targets = defaultdict(float)
        in_sources = defaultdict(float)
        for i in self._entity_outflows.get(entity_id, []):
            out_targets[self.flows[i].to_entity] += self.flows[i].amount
        for i in self._entity_inflows.get(entity_id, []):
            in_sources[self.flows[i].from_entity] += self.flows[i].amount

        circular = 0.0
        total = 0.0
        for target, amount in out_targets.items():
            total += amount
            if target in in_sources:
                circular += min(amount, in_sources[target])

        return circular / total if total > 0 else 0.0

    def flow_graph(self) -> Dict[str, Dict[str, float]]:
        """Adjacency matrix of ATP flows."""
        graph = defaultdict(lambda: defaultdict(float))
        for f in self.flows:
            if f.flow_type == "transfer":
                graph[f.from_entity][f.to_entity] += f.amount
        return {k: dict(v) for k, v in graph.items()}


def test_section_4():
    checks = []

    tracer = ATPFlowTracer()

    # Normal transfers
    tracer.record("alice", "bob", 50.0, 2.5, 1.0, "transfer")
    tracer.record("bob", "charlie", 30.0, 1.5, 2.0, "transfer")
    tracer.record("charlie", "alice", 10.0, 0.5, 3.0, "transfer")

    # Net flows
    net_alice = tracer.net_flow("alice")
    checks.append(("alice_net_negative", net_alice < 0))  # sent 52.5, received 10

    net_bob = tracer.net_flow("bob")
    checks.append(("bob_net_positive", net_bob > 0))  # received 50, sent 31.5

    # Total fees
    checks.append(("total_fees", abs(tracer.total_fees() - 4.5) < 0.01))

    # Circular flow detection
    tracer.record("alice", "dave", 100.0, 5.0, 4.0, "transfer")
    tracer.record("dave", "alice", 95.0, 4.75, 5.0, "transfer")
    cfr = tracer.circular_flow_ratio("alice")
    checks.append(("wash_detected", cfr > 0.5))  # alice↔dave is circular

    # Flow graph
    graph = tracer.flow_graph()
    checks.append(("graph_has_alice", "bob" in graph.get("alice", {})))
    checks.append(("graph_amount", abs(graph["alice"]["bob"] - 50.0) < 0.01))

    # Mint/burn
    tracer.record("system", "alice", 1000.0, 0.0, 0.0, "mint")
    tracer.record("alice", "system", 100.0, 0.0, 6.0, "burn")
    checks.append(("mint_tracked", len(tracer._entity_inflows["alice"]) == 3))

    return checks


# ============================================================
# S5 — Federation Health Metrics
# ============================================================

@dataclass
class FederationMetrics:
    """Aggregate health metrics for a federation."""
    entity_count: int = 0
    active_entities: int = 0
    total_atp: float = 0.0
    gini: float = 0.0
    mean_trust: float = 0.0
    trust_entropy: float = 0.0
    consensus_rounds: int = 0
    avg_consensus_time: float = 0.0
    partition_count: int = 0
    timestamp: float = 0.0


def compute_trust_entropy(trusts: List[float]) -> float:
    """Shannon entropy of trust distribution (normalized)."""
    if not trusts:
        return 0.0
    total = sum(trusts)
    if total == 0:
        return 0.0
    probs = [t / total for t in trusts if t > 0]
    entropy = -sum(p * math.log2(p) for p in probs)
    max_entropy = math.log2(len(trusts)) if len(trusts) > 1 else 1.0
    return entropy / max_entropy if max_entropy > 0 else 0.0


def gini_coefficient(values: List[float]) -> float:
    if not values or all(v == 0 for v in values):
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    total = sum(sorted_vals)
    if total == 0:
        return 0.0
    cumulative = 0.0
    area = 0.0
    for v in sorted_vals:
        cumulative += v
        area += cumulative
    b = area / (n * total)
    return 1.0 - 2.0 * b + 1.0 / n


@dataclass
class FederationMonitor:
    history: List[FederationMetrics] = field(default_factory=list)

    def snapshot(self, balances: Dict[str, float], trusts: Dict[str, float],
                 active_set: Set[str], consensus_time: float = 0.0,
                 timestamp: float = 0.0) -> FederationMetrics:
        bal_list = list(balances.values())
        trust_list = list(trusts.values())

        metrics = FederationMetrics(
            entity_count=len(balances),
            active_entities=len(active_set),
            total_atp=sum(bal_list),
            gini=gini_coefficient(bal_list),
            mean_trust=sum(trust_list) / len(trust_list) if trust_list else 0.0,
            trust_entropy=compute_trust_entropy(trust_list),
            consensus_rounds=len(self.history) + 1,
            avg_consensus_time=consensus_time,
            timestamp=timestamp,
        )
        self.history.append(metrics)
        return metrics

    def trend(self, metric: str, window: int = 5) -> Optional[float]:
        """Linear trend of a metric over recent snapshots."""
        recent = self.history[-window:]
        if len(recent) < 2:
            return None
        values = [getattr(m, metric, 0.0) for m in recent]
        n = len(values)
        x_mean = (n - 1) / 2.0
        y_mean = sum(values) / n
        num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        den = sum((i - x_mean) ** 2 for i in range(n))
        return num / den if den > 0 else 0.0


def test_section_5():
    checks = []

    monitor = FederationMonitor()

    # Simulate 10 rounds
    random.seed(42)
    for t in range(10):
        n = 20
        balances = {f"e{i}": 100.0 + random.uniform(-20, 50) * (t + 1) / 10
                    for i in range(n)}
        trusts = {f"e{i}": min(0.95, 0.3 + 0.03 * t + random.uniform(-0.05, 0.05))
                  for i in range(n)}
        active = {f"e{i}" for i in range(n) if random.random() > 0.1}

        monitor.snapshot(balances, trusts, active, consensus_time=0.5 + 0.1 * t,
                        timestamp=float(t))

    checks.append(("10_snapshots", len(monitor.history) == 10))

    latest = monitor.history[-1]
    checks.append(("entity_count", latest.entity_count == 20))
    checks.append(("gini_computed", 0 <= latest.gini <= 1))
    checks.append(("entropy_computed", 0 <= latest.trust_entropy <= 1))

    # Trends
    trust_trend = monitor.trend("mean_trust", window=5)
    checks.append(("trust_trending", trust_trend is not None))

    gini_trend = monitor.trend("gini", window=5)
    checks.append(("gini_trend_computed", gini_trend is not None))

    # Trust entropy is high for similar trusts
    checks.append(("entropy_high", latest.trust_entropy > 0.8))

    return checks


# ============================================================
# S6 — Anomaly Detection
# ============================================================

@dataclass
class AnomalyDetector:
    """Detect anomalous patterns in federation telemetry."""
    sybil_window: int = 10       # time window for sybil burst
    sybil_threshold: int = 5     # max new entities before alert
    entropy_decay_threshold: float = 0.1  # max entropy drop per period
    partition_silence_threshold: int = 3  # rounds of silence = partition

    def detect_sybil_burst(self, event_log: EventLog,
                           current_time: float) -> List[Dict[str, Any]]:
        """Detect sudden burst of new entity registrations."""
        births = event_log.by_type(EventType.ENTITY_BIRTH)
        recent = [e for e in births
                  if e.timestamp >= current_time - self.sybil_window]
        alerts = []
        if len(recent) >= self.sybil_threshold:
            alerts.append({
                "type": "sybil_burst",
                "count": len(recent),
                "window": self.sybil_window,
                "entities": [e.entity_id for e in recent],
            })
        return alerts

    def detect_entropy_drop(self, monitor: FederationMonitor) -> List[Dict[str, Any]]:
        """Detect sudden trust homogenization (potential collusion)."""
        if len(monitor.history) < 2:
            return []
        prev = monitor.history[-2].trust_entropy
        curr = monitor.history[-1].trust_entropy
        drop = prev - curr
        alerts = []
        if drop > self.entropy_decay_threshold:
            alerts.append({
                "type": "entropy_drop",
                "drop": drop,
                "previous": prev,
                "current": curr,
            })
        return alerts

    def detect_partition(self, entity_last_seen: Dict[str, float],
                         current_time: float,
                         heartbeat_interval: float = 1.0) -> List[Dict[str, Any]]:
        """Detect entities that have gone silent (potential partition)."""
        silent = []
        threshold = heartbeat_interval * self.partition_silence_threshold
        for eid, last in entity_last_seen.items():
            if current_time - last > threshold:
                silent.append(eid)

        alerts = []
        if len(silent) > 0:
            # If many entities go silent at once, it's likely a partition
            alerts.append({
                "type": "partition_suspected" if len(silent) > 2 else "entity_silent",
                "silent_entities": silent,
                "count": len(silent),
            })
        return alerts

    def detect_trust_oscillation(self, time_series: TrustTimeSeries,
                                 entity_id: str,
                                 window: int = 10) -> List[Dict[str, Any]]:
        """Detect rapid trust oscillation (potential gaming)."""
        snaps = time_series.snapshots.get(entity_id, [])
        if len(snaps) < window:
            return []
        recent = snaps[-window:]
        composites = [s.composite for s in recent]

        # Count direction changes
        changes = 0
        for i in range(1, len(composites) - 1):
            if (composites[i] - composites[i-1]) * (composites[i+1] - composites[i]) < 0:
                changes += 1

        alerts = []
        if changes >= window * 0.6:  # oscillating > 60% of the time
            alerts.append({
                "type": "trust_oscillation",
                "entity_id": entity_id,
                "direction_changes": changes,
                "window": window,
            })
        return alerts


def test_section_6():
    checks = []

    detector = AnomalyDetector(sybil_window=10, sybil_threshold=5)

    # Sybil burst detection
    log = EventLog()
    for i in range(7):
        log.append(EventType.ENTITY_BIRTH, f"sybil_{i}", {}, timestamp=100.0 + i)
    alerts = detector.detect_sybil_burst(log, current_time=107.0)
    checks.append(("sybil_detected", len(alerts) == 1 and alerts[0]["type"] == "sybil_burst"))
    checks.append(("sybil_count", alerts[0]["count"] == 7))

    # No sybil for spread-out registrations
    log2 = EventLog()
    for i in range(3):
        log2.append(EventType.ENTITY_BIRTH, f"legit_{i}", {}, timestamp=100.0 + i * 5)
    alerts2 = detector.detect_sybil_burst(log2, current_time=115.0)
    checks.append(("no_sybil_spread", len(alerts2) == 0))

    # Entropy drop
    monitor = FederationMonitor()
    monitor.history.append(FederationMetrics(trust_entropy=0.9, timestamp=1.0))
    monitor.history.append(FederationMetrics(trust_entropy=0.7, timestamp=2.0))
    entropy_alerts = detector.detect_entropy_drop(monitor)
    checks.append(("entropy_drop_detected", len(entropy_alerts) == 1))

    # Partition detection
    last_seen = {"e0": 10.0, "e1": 10.0, "e2": 3.0, "e3": 2.0, "e4": 1.0}
    partition_alerts = detector.detect_partition(last_seen, current_time=10.0,
                                                heartbeat_interval=1.0)
    checks.append(("partition_detected", len(partition_alerts) == 1))
    checks.append(("partition_type", partition_alerts[0]["type"] == "partition_suspected"))

    # Trust oscillation
    ts = TrustTimeSeries()
    for t in range(20):
        # Alternating high/low trust
        val = 0.7 if t % 2 == 0 else 0.3
        ts.record("gamer", float(t), val, val, val)
    osc_alerts = detector.detect_trust_oscillation(ts, "gamer", window=10)
    checks.append(("oscillation_detected", len(osc_alerts) == 1))

    # No oscillation for steady growth
    ts2 = TrustTimeSeries()
    for t in range(20):
        val = 0.3 + 0.03 * t
        ts2.record("honest", float(t), val, val, val)
    osc_alerts2 = detector.detect_trust_oscillation(ts2, "honest", window=10)
    checks.append(("no_oscillation_honest", len(osc_alerts2) == 0))

    return checks


# ============================================================
# S7 — Alerting & Threshold Engine
# ============================================================

class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    alert_id: str
    severity: Severity
    message: str
    data: Dict[str, Any]
    timestamp: float
    acknowledged: bool = False


@dataclass
class AlertRule:
    name: str
    condition: Callable[[FederationMetrics], bool]
    severity: Severity
    message_template: str
    cooldown: float = 10.0  # minimum time between alerts
    last_fired: float = -1e9


@dataclass
class AlertEngine:
    rules: List[AlertRule] = field(default_factory=list)
    alerts: List[Alert] = field(default_factory=list)
    _counter: int = 0

    def add_rule(self, name: str, condition: Callable, severity: Severity,
                 message: str, cooldown: float = 10.0):
        self.rules.append(AlertRule(name, condition, severity, message, cooldown))

    def evaluate(self, metrics: FederationMetrics) -> List[Alert]:
        fired = []
        for rule in self.rules:
            if metrics.timestamp - rule.last_fired < rule.cooldown:
                continue
            if rule.condition(metrics):
                self._counter += 1
                alert = Alert(
                    alert_id=f"alert-{self._counter}",
                    severity=rule.severity,
                    message=rule.message_template,
                    data={"rule": rule.name, "metrics_timestamp": metrics.timestamp},
                    timestamp=metrics.timestamp,
                )
                self.alerts.append(alert)
                fired.append(alert)
                rule.last_fired = metrics.timestamp
        return fired

    def unacknowledged(self) -> List[Alert]:
        return [a for a in self.alerts if not a.acknowledged]


def test_section_7():
    checks = []

    engine = AlertEngine()
    engine.add_rule("high_gini", lambda m: m.gini > 0.5, Severity.WARNING,
                    "Wealth inequality exceeds threshold", cooldown=5.0)
    engine.add_rule("low_active", lambda m: m.active_entities < m.entity_count * 0.5,
                    Severity.CRITICAL, "Less than 50% entities active", cooldown=5.0)

    # Normal metrics — no alerts
    normal = FederationMetrics(entity_count=20, active_entities=18,
                               gini=0.3, timestamp=1.0)
    alerts = engine.evaluate(normal)
    checks.append(("no_alerts_normal", len(alerts) == 0))

    # High inequality
    bad = FederationMetrics(entity_count=20, active_entities=18,
                            gini=0.7, timestamp=2.0)
    alerts = engine.evaluate(bad)
    checks.append(("gini_alert", len(alerts) == 1 and alerts[0].severity == Severity.WARNING))

    # Low activity
    crisis = FederationMetrics(entity_count=20, active_entities=5,
                                gini=0.8, timestamp=10.0)
    alerts = engine.evaluate(crisis)
    checks.append(("both_alerts", len(alerts) == 2))

    # Cooldown prevents re-fire
    crisis2 = FederationMetrics(entity_count=20, active_entities=5,
                                 gini=0.8, timestamp=11.0)
    alerts = engine.evaluate(crisis2)
    checks.append(("cooldown_blocks", len(alerts) == 0))

    # After cooldown expires
    crisis3 = FederationMetrics(entity_count=20, active_entities=5,
                                 gini=0.8, timestamp=20.0)
    alerts = engine.evaluate(crisis3)
    checks.append(("cooldown_expired", len(alerts) == 2))

    # Unacknowledged
    checks.append(("unacked", len(engine.unacknowledged()) == 5))
    engine.alerts[0].acknowledged = True
    checks.append(("one_acked", len(engine.unacknowledged()) == 4))

    return checks


# ============================================================
# S8 — Query Interface
# ============================================================

@dataclass
class TelemetryQuery:
    """Query interface over event log and metrics."""

    @staticmethod
    def filter_events(events: List[Event],
                      entity_id: Optional[str] = None,
                      event_type: Optional[EventType] = None,
                      start_time: Optional[float] = None,
                      end_time: Optional[float] = None) -> List[Event]:
        result = events
        if entity_id:
            result = [e for e in result if e.entity_id == entity_id]
        if event_type:
            result = [e for e in result if e.event_type == event_type]
        if start_time is not None:
            result = [e for e in result if e.timestamp >= start_time]
        if end_time is not None:
            result = [e for e in result if e.timestamp <= end_time]
        return result

    @staticmethod
    def aggregate(events: List[Event], group_by: str = "entity_id",
                  agg: str = "count") -> Dict[str, float]:
        groups = defaultdict(list)
        for e in events:
            key = getattr(e, group_by, str(e.event_type.value))
            groups[key].append(e)

        result = {}
        for key, evts in groups.items():
            if agg == "count":
                result[key] = float(len(evts))
            elif agg == "sum_amount":
                result[key] = sum(e.data.get("amount", 0) for e in evts)
        return result

    @staticmethod
    def windowed_count(events: List[Event], window_size: float,
                       start: float, end: float) -> List[Tuple[float, int]]:
        """Count events per time window."""
        buckets = []
        t = start
        while t < end:
            count = sum(1 for e in events if t <= e.timestamp < t + window_size)
            buckets.append((t, count))
            t += window_size
        return buckets


def test_section_8():
    checks = []

    log = EventLog()
    for i in range(5):
        log.append(EventType.ENTITY_BIRTH, f"e{i}", {}, timestamp=float(i))
    for i in range(5):
        log.append(EventType.ATP_TRANSFER, f"e{i % 3}", {"amount": 10.0 * (i + 1)},
                   timestamp=5.0 + i)

    # Filter by type
    births = TelemetryQuery.filter_events(log.events, event_type=EventType.ENTITY_BIRTH)
    checks.append(("filter_type", len(births) == 5))

    # Filter by entity
    e0_events = TelemetryQuery.filter_events(log.events, entity_id="e0")
    checks.append(("filter_entity", len(e0_events) == 3))  # 1 birth + 2 transfers

    # Filter by time range
    recent = TelemetryQuery.filter_events(log.events, start_time=5.0)
    checks.append(("filter_time", len(recent) == 5))

    # Aggregate count by entity
    counts = TelemetryQuery.aggregate(log.events, group_by="entity_id", agg="count")
    checks.append(("agg_count", counts["e0"] == 3))

    # Aggregate sum
    transfers = TelemetryQuery.filter_events(log.events, event_type=EventType.ATP_TRANSFER)
    sums = TelemetryQuery.aggregate(transfers, group_by="entity_id", agg="sum_amount")
    checks.append(("agg_sum", sums["e0"] == 10.0 + 40.0))  # i=0: 10, i=3: 40

    # Windowed count
    windows = TelemetryQuery.windowed_count(log.events, window_size=3.0,
                                            start=0.0, end=10.0)
    checks.append(("windowed", len(windows) == 4))  # [0,3), [3,6), [6,9), [9,12)
    checks.append(("window_counts", windows[0][1] == 3))  # t=0,1,2

    return checks


# ============================================================
# S9 — Dashboard Aggregation
# ============================================================

@dataclass
class DashboardSnapshot:
    """Pre-computed dashboard view for UI rendering."""
    timestamp: float
    entity_count: int
    active_ratio: float
    total_atp: float
    gini: float
    mean_trust: float
    trust_entropy: float
    alert_count: int
    top_entities: List[Tuple[str, float]]  # (entity_id, trust_composite)
    trust_distribution: Dict[str, int]     # bucket -> count


def build_dashboard(monitor: FederationMonitor, engine: AlertEngine,
                    trusts: Dict[str, float]) -> DashboardSnapshot:
    latest = monitor.history[-1] if monitor.history else FederationMetrics()

    # Trust distribution buckets
    buckets = {"0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0}
    for t in trusts.values():
        if t < 0.2:
            buckets["0.0-0.2"] += 1
        elif t < 0.4:
            buckets["0.2-0.4"] += 1
        elif t < 0.6:
            buckets["0.4-0.6"] += 1
        elif t < 0.8:
            buckets["0.6-0.8"] += 1
        else:
            buckets["0.8-1.0"] += 1

    # Top entities by trust
    sorted_trusts = sorted(trusts.items(), key=lambda x: x[1], reverse=True)
    top = sorted_trusts[:5]

    return DashboardSnapshot(
        timestamp=latest.timestamp,
        entity_count=latest.entity_count,
        active_ratio=latest.active_entities / max(1, latest.entity_count),
        total_atp=latest.total_atp,
        gini=latest.gini,
        mean_trust=latest.mean_trust,
        trust_entropy=latest.trust_entropy,
        alert_count=len(engine.unacknowledged()),
        top_entities=top,
        trust_distribution=buckets,
    )


def test_section_9():
    checks = []
    random.seed(42)

    # Build state
    monitor = FederationMonitor()
    n = 30
    balances = {f"e{i}": 50.0 + random.uniform(0, 100) for i in range(n)}
    trusts = {f"e{i}": min(0.95, 0.2 + 0.6 * random.random()) for i in range(n)}
    active = {f"e{i}" for i in range(n) if random.random() > 0.1}

    monitor.snapshot(balances, trusts, active, timestamp=1.0)

    engine = AlertEngine()
    engine.add_rule("test", lambda m: m.gini > 0.3, Severity.INFO, "test alert")
    engine.evaluate(monitor.history[-1])

    dash = build_dashboard(monitor, engine, trusts)

    checks.append(("dash_entity_count", dash.entity_count == n))
    checks.append(("dash_active_ratio", 0 < dash.active_ratio <= 1))
    checks.append(("dash_gini", 0 <= dash.gini <= 1))
    checks.append(("dash_top_5", len(dash.top_entities) == 5))
    checks.append(("dash_top_sorted", all(dash.top_entities[i][1] >= dash.top_entities[i+1][1]
                                          for i in range(len(dash.top_entities)-1))))
    checks.append(("dash_distribution", sum(dash.trust_distribution.values()) == n))
    checks.append(("dash_alerts", dash.alert_count >= 0))

    return checks


# ============================================================
# S10 — Retention & Compaction
# ============================================================

@dataclass
class RetentionPolicy:
    """Define how long telemetry data is retained."""
    raw_retention_periods: int = 100     # keep raw events
    summary_retention_periods: int = 1000  # keep summaries
    compaction_ratio: int = 10           # summarize every N events

    def compact(self, events: List[Event]) -> Tuple[List[Event], List[Dict[str, Any]]]:
        """Compact old events into summaries, keep recent raw."""
        if len(events) <= self.raw_retention_periods:
            return events, []

        keep_raw = events[-self.raw_retention_periods:]
        to_compact = events[:-self.raw_retention_periods]

        summaries = []
        for i in range(0, len(to_compact), self.compaction_ratio):
            batch = to_compact[i:i + self.compaction_ratio]
            summary = {
                "start_seq": batch[0].sequence,
                "end_seq": batch[-1].sequence,
                "start_time": batch[0].timestamp,
                "end_time": batch[-1].timestamp,
                "count": len(batch),
                "types": dict(defaultdict(int)),
                "entities": list(set(e.entity_id for e in batch)),
                "start_hash": batch[0].event_hash,
                "end_hash": batch[-1].event_hash,
            }
            for e in batch:
                if e.event_type.value not in summary["types"]:
                    summary["types"][e.event_type.value] = 0
                summary["types"][e.event_type.value] += 1
            summaries.append(summary)

        return keep_raw, summaries


def test_section_10():
    checks = []

    policy = RetentionPolicy(raw_retention_periods=50, compaction_ratio=10)

    # Create 200 events
    log = EventLog()
    for i in range(200):
        log.append(EventType.TRUST_UPDATE, f"e{i % 10}",
                   {"value": 0.5 + i * 0.001}, timestamp=float(i))

    raw, summaries = policy.compact(log.events)

    checks.append(("raw_count", len(raw) == 50))
    checks.append(("summaries_created", len(summaries) == 15))  # 150 / 10

    # Summaries have correct structure
    first_summary = summaries[0]
    checks.append(("summary_count", first_summary["count"] == 10))
    checks.append(("summary_has_hash", len(first_summary["start_hash"]) == 64))

    # Raw events are the most recent
    checks.append(("raw_recent", raw[0].sequence == 150))

    # Total coverage
    total_covered = sum(s["count"] for s in summaries) + len(raw)
    checks.append(("total_coverage", total_covered == 200))

    # Compaction preserves hash references
    checks.append(("hash_chain_ref",
                    summaries[-1]["end_hash"] == log.events[149].event_hash))

    return checks


# ============================================================
# S11 — Performance Under Load
# ============================================================

def test_section_11():
    checks = []

    import time as time_mod

    # Event log performance: 10K events
    log = EventLog()
    start = time_mod.perf_counter()
    for i in range(10000):
        log.append(EventType.TRUST_UPDATE, f"e{i % 100}",
                   {"value": random.random()}, timestamp=float(i))
    elapsed = time_mod.perf_counter() - start
    checks.append(("10k_events_fast", elapsed < 5.0))

    # Chain verification
    start = time_mod.perf_counter()
    valid = log.verify_chain()
    verify_time = time_mod.perf_counter() - start
    checks.append(("chain_valid_10k", valid))
    checks.append(("verify_fast", verify_time < 10.0))

    # Index query performance
    start = time_mod.perf_counter()
    for _ in range(1000):
        log.by_entity(f"e{random.randint(0, 99)}")
    query_time = time_mod.perf_counter() - start
    checks.append(("index_query_fast", query_time < 2.0))

    # Tracing: 1000 traces
    tc = TraceCollector()
    start = time_mod.perf_counter()
    for i in range(1000):
        root = tc.start_trace("op", f"e{i % 50}", start_time=float(i))
        for j in range(3):
            child = tc.start_child(root, f"sub_{j}", f"e{(i+j) % 50}",
                                   start_time=float(i) + j * 0.1)
            tc.finish(child, end_time=float(i) + (j + 1) * 0.1)
        tc.finish(root, end_time=float(i) + 0.4)
    trace_time = time_mod.perf_counter() - start
    checks.append(("1k_traces_fast", trace_time < 3.0))
    checks.append(("4k_spans", len(tc.spans) == 4000))

    # Anomaly detection on large log
    detector = AnomalyDetector(sybil_window=100, sybil_threshold=50)
    start = time_mod.perf_counter()
    alerts = detector.detect_sybil_burst(log, current_time=10000.0)
    detect_time = time_mod.perf_counter() - start
    checks.append(("anomaly_fast", detect_time < 2.0))

    # Compaction
    policy = RetentionPolicy(raw_retention_periods=1000, compaction_ratio=100)
    start = time_mod.perf_counter()
    raw, summaries = policy.compact(log.events)
    compact_time = time_mod.perf_counter() - start
    checks.append(("compaction_fast", compact_time < 2.0))

    return checks


# ============================================================
# Main
# ============================================================

def main():
    random.seed(42)

    sections = [
        ("S1 Event Log & Immutable Append", test_section_1),
        ("S2 Distributed Tracing", test_section_2),
        ("S3 Trust Tensor Time Series", test_section_3),
        ("S4 ATP Flow Tracing", test_section_4),
        ("S5 Federation Health Metrics", test_section_5),
        ("S6 Anomaly Detection", test_section_6),
        ("S7 Alerting & Threshold Engine", test_section_7),
        ("S8 Query Interface", test_section_8),
        ("S9 Dashboard Aggregation", test_section_9),
        ("S10 Retention & Compaction", test_section_10),
        ("S11 Performance Under Load", test_section_11),
    ]

    total_pass = 0
    total_fail = 0
    failures = []

    for name, test_fn in sections:
        checks = test_fn()
        passed = sum(1 for _, ok in checks if ok)
        failed = sum(1 for _, ok in checks if not ok)
        total_pass += passed
        total_fail += failed
        status = "✓" if failed == 0 else "✗"
        print(f"  {status} {name}: {passed}/{passed+failed}")
        for check_name, ok in checks:
            if not ok:
                failures.append(f"    FAIL: {check_name}")

    print(f"\nTotal: {total_pass}/{total_pass+total_fail}")
    if failures:
        print(f"\nFailed checks:")
        for f in failures:
            print(f)


if __name__ == "__main__":
    main()
