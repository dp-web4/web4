#!/usr/bin/env python3
"""
Distributed Tracing & Diagnostics
===================================

Trace context propagation, span-based debugging, federation
trace aggregation, causal ordering, and diagnostic tooling
for Web4 distributed systems.

Session 21 — Track 5
"""

from __future__ import annotations
import hashlib
import math
import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# ─── Trace Context ─────────────────────────────────────────────────────────

@dataclass
class TraceContext:
    """
    W3C Trace Context compatible context propagation.

    Carries trace identity through distributed operations.
    """
    trace_id: str      # 128-bit hex trace identifier
    span_id: str       # 64-bit hex span identifier
    parent_span_id: Optional[str] = None
    trace_flags: int = 1  # 0=not sampled, 1=sampled
    baggage: Dict[str, str] = field(default_factory=dict)

    @staticmethod
    def new_trace() -> TraceContext:
        """Create a new root trace context."""
        return TraceContext(
            trace_id=os.urandom(16).hex(),
            span_id=os.urandom(8).hex(),
        )

    def child_span(self) -> TraceContext:
        """Create a child span context."""
        return TraceContext(
            trace_id=self.trace_id,
            span_id=os.urandom(8).hex(),
            parent_span_id=self.span_id,
            trace_flags=self.trace_flags,
            baggage=dict(self.baggage),
        )

    def to_header(self) -> str:
        """Serialize to W3C traceparent header format."""
        return f"00-{self.trace_id}-{self.span_id}-{self.trace_flags:02x}"

    @staticmethod
    def from_header(header: str) -> TraceContext:
        """Parse W3C traceparent header."""
        parts = header.split("-")
        return TraceContext(
            trace_id=parts[1],
            span_id=parts[2],
            trace_flags=int(parts[3], 16),
        )

    def to_baggage_header(self) -> str:
        """Serialize baggage items."""
        return ",".join(f"{k}={v}" for k, v in self.baggage.items())


# ─── Spans ──────────────────────────────────────────────────────────────────

class SpanKind(Enum):
    """Type of operation a span represents."""
    INTERNAL = "internal"
    CLIENT = "client"
    SERVER = "server"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(Enum):
    """Status of a span's operation."""
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


@dataclass
class SpanEvent:
    """A timestamped event within a span."""
    name: str
    timestamp: float
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpanLink:
    """A link to another span (causal relationship)."""
    trace_id: str
    span_id: str
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Span:
    """
    A unit of work in a distributed trace.

    Spans form a tree within a trace, with parent-child relationships.
    """
    context: TraceContext
    name: str
    kind: SpanKind = SpanKind.INTERNAL
    start_time: float = 0.0
    end_time: float = 0.0
    status: SpanStatus = SpanStatus.UNSET
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[SpanEvent] = field(default_factory=list)
    links: List[SpanLink] = field(default_factory=list)

    def __post_init__(self):
        if not self.start_time:
            self.start_time = time.time()

    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return (time.time() - self.start_time) * 1000

    def add_event(self, name: str, **attributes):
        self.events.append(SpanEvent(name, time.time(), attributes))

    def add_link(self, other_span: Span, **attributes):
        self.links.append(SpanLink(
            other_span.context.trace_id,
            other_span.context.span_id,
            attributes,
        ))

    def set_status(self, status: SpanStatus, description: str = ""):
        self.status = status
        if description:
            self.attributes["status.description"] = description

    def end(self):
        self.end_time = time.time()
        if self.status == SpanStatus.UNSET:
            self.status = SpanStatus.OK


# ─── Tracer ─────────────────────────────────────────────────────────────────

class Tracer:
    """
    Creates and manages spans for a service/component.
    """

    def __init__(self, service_name: str, component: str = ""):
        self.service_name = service_name
        self.component = component
        self.spans: List[Span] = []
        self._active_spans: Dict[str, Span] = {}  # span_id → Span

    def start_span(self, name: str,
                   parent: Optional[TraceContext] = None,
                   kind: SpanKind = SpanKind.INTERNAL,
                   **attributes) -> Span:
        """Start a new span."""
        if parent:
            ctx = parent.child_span()
        else:
            ctx = TraceContext.new_trace()

        span = Span(
            context=ctx, name=name, kind=kind,
            attributes={
                "service.name": self.service_name,
                "component": self.component,
                **attributes,
            },
        )
        self._active_spans[ctx.span_id] = span
        return span

    def end_span(self, span: Span):
        """End a span and record it."""
        span.end()
        self._active_spans.pop(span.context.span_id, None)
        self.spans.append(span)

    def active_span_count(self) -> int:
        return len(self._active_spans)

    def completed_span_count(self) -> int:
        return len(self.spans)


# ─── Trace Collector ───────────────────────────────────────────────────────

@dataclass
class TraceRecord:
    """A completed trace with all its spans."""
    trace_id: str
    spans: List[Span]
    root_span: Optional[Span] = None
    start_time: float = 0.0
    end_time: float = 0.0
    duration_ms: float = 0.0
    span_count: int = 0
    error_count: int = 0
    service_count: int = 0


class TraceCollector:
    """
    Aggregates spans from multiple services into complete traces.
    """

    def __init__(self, max_traces: int = 10000):
        self.max_traces = max_traces
        self._span_buffer: Dict[str, List[Span]] = defaultdict(list)
        self.traces: Dict[str, TraceRecord] = {}
        self.total_spans_received: int = 0

    def ingest_span(self, span: Span):
        """Receive a span from a tracer."""
        self.total_spans_received += 1
        self._span_buffer[span.context.trace_id].append(span)

    def ingest_batch(self, spans: List[Span]):
        """Receive a batch of spans."""
        for span in spans:
            self.ingest_span(span)

    def assemble_trace(self, trace_id: str) -> Optional[TraceRecord]:
        """Assemble a complete trace from buffered spans."""
        spans = self._span_buffer.get(trace_id, [])
        if not spans:
            return None

        # Find root span (no parent)
        root = None
        for s in spans:
            if s.context.parent_span_id is None:
                root = s
                break

        start = min(s.start_time for s in spans)
        end = max(s.end_time for s in spans if s.end_time > 0)
        services = {s.attributes.get("service.name", "") for s in spans}
        errors = sum(1 for s in spans if s.status == SpanStatus.ERROR)

        record = TraceRecord(
            trace_id=trace_id,
            spans=spans,
            root_span=root,
            start_time=start,
            end_time=end,
            duration_ms=(end - start) * 1000 if end > start else 0,
            span_count=len(spans),
            error_count=errors,
            service_count=len(services),
        )

        self.traces[trace_id] = record
        return record

    def assemble_all(self) -> int:
        """Assemble all buffered traces."""
        count = 0
        for trace_id in list(self._span_buffer.keys()):
            if self.assemble_trace(trace_id):
                count += 1
        return count

    def query_traces(self, service: Optional[str] = None,
                     min_duration_ms: float = 0,
                     has_errors: Optional[bool] = None
                     ) -> List[TraceRecord]:
        """Query traces by criteria."""
        results = []
        for record in self.traces.values():
            if min_duration_ms > 0 and record.duration_ms < min_duration_ms:
                continue
            if has_errors is True and record.error_count == 0:
                continue
            if has_errors is False and record.error_count > 0:
                continue
            if service:
                services = {s.attributes.get("service.name")
                            for s in record.spans}
                if service not in services:
                    continue
            results.append(record)
        return results


# ─── Causal Ordering ───────────────────────────────────────────────────────

@dataclass
class CausalEvent:
    """An event with causal ordering via vector clock."""
    event_id: str
    node_id: str
    vector_clock: Dict[str, int]
    span_id: Optional[str] = None
    trace_id: Optional[str] = None
    event_type: str = ""
    timestamp: float = 0.0

    def happens_before(self, other: CausalEvent) -> bool:
        """Check if this event causally precedes other."""
        all_leq = True
        any_lt = False
        for node in set(self.vector_clock) | set(other.vector_clock):
            s = self.vector_clock.get(node, 0)
            o = other.vector_clock.get(node, 0)
            if s > o:
                return False
            if s < o:
                any_lt = True
        return any_lt

    def concurrent_with(self, other: CausalEvent) -> bool:
        """Check if events are concurrent (neither happens-before)."""
        return (not self.happens_before(other) and
                not other.happens_before(self))


class CausalTracer:
    """Track causal ordering of distributed events."""

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.clock: Dict[str, int] = {node_id: 0}
        self.events: List[CausalEvent] = []

    def local_event(self, event_type: str, **kwargs) -> CausalEvent:
        """Record a local event."""
        self.clock[self.node_id] = self.clock.get(self.node_id, 0) + 1
        event = CausalEvent(
            event_id=f"{self.node_id}_{self.clock[self.node_id]}",
            node_id=self.node_id,
            vector_clock=dict(self.clock),
            event_type=event_type,
            timestamp=time.time(),
            **kwargs,
        )
        self.events.append(event)
        return event

    def send_event(self, event_type: str, **kwargs) -> CausalEvent:
        """Record a send event."""
        return self.local_event(f"send:{event_type}", **kwargs)

    def receive_event(self, sender_clock: Dict[str, int],
                      event_type: str, **kwargs) -> CausalEvent:
        """Record a receive event, merging clocks."""
        # Merge: component-wise max
        for node, val in sender_clock.items():
            self.clock[node] = max(self.clock.get(node, 0), val)
        return self.local_event(f"recv:{event_type}", **kwargs)


# ─── Diagnostic Toolkit ────────────────────────────────────────────────────

@dataclass
class DiagnosticReport:
    """Diagnostic report for a trace or system state."""
    category: str
    severity: str  # "info", "warning", "error", "critical"
    message: str
    affected_spans: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class DiagnosticEngine:
    """
    Analyze traces and system state to produce diagnostic reports.
    """

    def __init__(self):
        self.reports: List[DiagnosticReport] = []

    def analyze_trace(self, record: TraceRecord) -> List[DiagnosticReport]:
        """Analyze a trace for issues."""
        reports = []

        # Check for errors
        if record.error_count > 0:
            error_spans = [s.context.span_id for s in record.spans
                           if s.status == SpanStatus.ERROR]
            reports.append(DiagnosticReport(
                category="errors",
                severity="error",
                message=f"Trace has {record.error_count} error(s)",
                affected_spans=error_spans,
                recommendations=["Check error span attributes for details"],
            ))

        # Check for slow spans
        for span in record.spans:
            if span.duration_ms > 1000:  # > 1 second
                reports.append(DiagnosticReport(
                    category="latency",
                    severity="warning",
                    message=f"Slow span: {span.name} took {span.duration_ms:.0f}ms",
                    affected_spans=[span.context.span_id],
                    recommendations=["Consider caching or parallel execution"],
                ))

        # Check for orphan spans (no parent, not root)
        if record.root_span:
            root_trace = record.root_span.context.trace_id
            for span in record.spans:
                if (span.context.parent_span_id and
                        not any(s.context.span_id == span.context.parent_span_id
                                for s in record.spans)):
                    reports.append(DiagnosticReport(
                        category="topology",
                        severity="warning",
                        message=f"Orphan span: {span.name} (parent not in trace)",
                        affected_spans=[span.context.span_id],
                        recommendations=["Check span propagation"],
                    ))

        # Check for high fan-out
        children_count: Dict[str, int] = defaultdict(int)
        for span in record.spans:
            if span.context.parent_span_id:
                children_count[span.context.parent_span_id] += 1
        for span_id, count in children_count.items():
            if count > 10:
                reports.append(DiagnosticReport(
                    category="fan-out",
                    severity="warning",
                    message=f"High fan-out: span has {count} children",
                    affected_spans=[span_id],
                    recommendations=["Consider batching or reducing parallelism"],
                ))

        self.reports.extend(reports)
        return reports

    def analyze_latency_distribution(self, traces: List[TraceRecord]
                                     ) -> Dict[str, Any]:
        """Analyze latency distribution across traces."""
        durations = [t.duration_ms for t in traces if t.duration_ms > 0]
        if not durations:
            return {"count": 0}

        durations.sort()
        n = len(durations)
        return {
            "count": n,
            "min_ms": durations[0],
            "max_ms": durations[-1],
            "avg_ms": sum(durations) / n,
            "p50_ms": durations[n // 2],
            "p95_ms": durations[int(n * 0.95)] if n >= 20 else durations[-1],
            "p99_ms": durations[int(n * 0.99)] if n >= 100 else durations[-1],
        }

    def find_critical_path(self, record: TraceRecord) -> List[Span]:
        """Find the critical path (longest sequential chain) in a trace."""
        if not record.spans:
            return []

        # Build parent→children map
        children: Dict[str, List[Span]] = defaultdict(list)
        span_map: Dict[str, Span] = {}
        for span in record.spans:
            span_map[span.context.span_id] = span
            if span.context.parent_span_id:
                children[span.context.parent_span_id].append(span)

        # DFS to find longest path by duration
        def longest_path(span_id: str) -> Tuple[float, List[Span]]:
            span = span_map.get(span_id)
            if not span:
                return 0.0, []

            child_spans = children.get(span_id, [])
            if not child_spans:
                return span.duration_ms, [span]

            best_dur = 0.0
            best_path: List[Span] = []
            for child in child_spans:
                dur, path = longest_path(child.context.span_id)
                if dur > best_dur:
                    best_dur = dur
                    best_path = path

            return span.duration_ms + best_dur, [span] + best_path

        if record.root_span:
            _, path = longest_path(record.root_span.context.span_id)
            return path
        return []


# ─── Metrics Aggregation ───────────────────────────────────────────────────

@dataclass
class MetricPoint:
    """A single metric data point."""
    name: str
    value: float
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsRegistry:
    """
    Collect and aggregate metrics from distributed components.
    """

    def __init__(self):
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.points: List[MetricPoint] = []

    def increment(self, name: str, value: float = 1.0,
                  labels: Optional[Dict[str, str]] = None):
        key = self._key(name, labels)
        self.counters[key] += value
        self.points.append(MetricPoint(name, value, time.time(),
                                       labels or {}))

    def set_gauge(self, name: str, value: float,
                  labels: Optional[Dict[str, str]] = None):
        key = self._key(name, labels)
        self.gauges[key] = value

    def observe(self, name: str, value: float,
                labels: Optional[Dict[str, str]] = None):
        key = self._key(name, labels)
        self.histograms[key].append(value)

    def get_counter(self, name: str,
                    labels: Optional[Dict[str, str]] = None) -> float:
        return self.counters.get(self._key(name, labels), 0.0)

    def get_gauge(self, name: str,
                  labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        return self.gauges.get(self._key(name, labels))

    def get_histogram_stats(self, name: str,
                            labels: Optional[Dict[str, str]] = None
                            ) -> Dict[str, float]:
        key = self._key(name, labels)
        values = self.histograms.get(key, [])
        if not values:
            return {}
        values.sort()
        n = len(values)
        return {
            "count": n,
            "sum": sum(values),
            "min": values[0],
            "max": values[-1],
            "avg": sum(values) / n,
            "p50": values[n // 2],
            "p99": values[int(n * 0.99)] if n >= 100 else values[-1],
        }

    @staticmethod
    def _key(name: str, labels: Optional[Dict[str, str]]) -> str:
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"


# ─── Federation Trace Aggregation ──────────────────────────────────────────

@dataclass
class FederationTraceSync:
    """
    Synchronize trace data across federation boundaries.
    """
    federation_id: str
    collectors: Dict[str, TraceCollector] = field(default_factory=dict)
    cross_fed_traces: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))

    def register_collector(self, node_id: str, collector: TraceCollector):
        self.collectors[node_id] = collector

    def sync_traces(self) -> int:
        """
        Synchronize traces across federation nodes.
        Returns number of cross-federation traces found.
        """
        # Collect all trace IDs from all nodes
        trace_to_nodes: Dict[str, Set[str]] = defaultdict(set)
        for node_id, collector in self.collectors.items():
            for trace_id in collector._span_buffer:
                trace_to_nodes[trace_id].add(node_id)

        # Identify cross-node traces
        cross_count = 0
        for trace_id, nodes in trace_to_nodes.items():
            if len(nodes) > 1:
                self.cross_fed_traces[trace_id] = nodes
                cross_count += 1

        return cross_count

    def merge_trace(self, trace_id: str) -> Optional[TraceRecord]:
        """Merge a trace from multiple collectors."""
        all_spans = []
        for node_id, collector in self.collectors.items():
            spans = collector._span_buffer.get(trace_id, [])
            all_spans.extend(spans)

        if not all_spans:
            return None

        # Use a temporary collector to assemble
        merged = TraceCollector()
        for span in all_spans:
            merged.ingest_span(span)
        return merged.assemble_trace(trace_id)


# ─── Checks ─────────────────────────────────────────────────────────────────

def run_checks():
    checks = []
    t0 = time.time()

    # ── S1: Trace Context ────────────────────────────────────────────────

    # S1.1: New trace context
    ctx = TraceContext.new_trace()
    checks.append(("s1_trace_id", len(ctx.trace_id) == 32))

    # S1.2: Span ID
    checks.append(("s1_span_id", len(ctx.span_id) == 16))

    # S1.3: Child span inherits trace ID
    child = ctx.child_span()
    checks.append(("s1_child_trace_id", child.trace_id == ctx.trace_id))

    # S1.4: Child span has different span ID
    checks.append(("s1_child_span_id", child.span_id != ctx.span_id))

    # S1.5: Child span parent is original
    checks.append(("s1_child_parent", child.parent_span_id == ctx.span_id))

    # S1.6: Header serialization round-trip
    header = ctx.to_header()
    restored = TraceContext.from_header(header)
    checks.append(("s1_header_roundtrip",
                    restored.trace_id == ctx.trace_id and
                    restored.span_id == ctx.span_id))

    # S1.7: Baggage propagation
    ctx.baggage["entity_id"] = "ent_42"
    child2 = ctx.child_span()
    checks.append(("s1_baggage_propagated",
                    child2.baggage.get("entity_id") == "ent_42"))

    # S1.8: Baggage header
    bh = ctx.to_baggage_header()
    checks.append(("s1_baggage_header", "entity_id=ent_42" in bh))

    # ── S2: Spans ────────────────────────────────────────────────────────

    # S2.1: Create span
    span = Span(ctx, "test_operation", SpanKind.SERVER)
    checks.append(("s2_span_created", span.name == "test_operation"))

    # S2.2: Span duration
    time.sleep(0.001)
    span.end()
    checks.append(("s2_span_duration", span.duration_ms > 0))

    # S2.3: Span events
    span2 = Span(ctx.child_span(), "with_events")
    span2.add_event("checkpoint", progress=50)
    span2.end()
    checks.append(("s2_span_event", len(span2.events) == 1 and
                    span2.events[0].name == "checkpoint"))

    # S2.4: Span status
    span3 = Span(ctx.child_span(), "failing_op")
    span3.set_status(SpanStatus.ERROR, "timeout")
    span3.end()
    checks.append(("s2_span_error", span3.status == SpanStatus.ERROR))

    # S2.5: Span links
    other = Span(TraceContext.new_trace(), "other_trace")
    span4 = Span(ctx.child_span(), "linked")
    span4.add_link(other, relationship="causal")
    span4.end()
    checks.append(("s2_span_link", len(span4.links) == 1))

    # S2.6: Default status is OK after end
    auto_span = Span(ctx.child_span(), "auto_ok")
    auto_span.end()
    checks.append(("s2_auto_ok", auto_span.status == SpanStatus.OK))

    # ── S3: Tracer ───────────────────────────────────────────────────────

    tracer = Tracer("lct-service", "lifecycle")

    # S3.1: Start span
    s1 = tracer.start_span("activate_lct", kind=SpanKind.SERVER)
    checks.append(("s3_active_span", tracer.active_span_count() == 1))

    # S3.2: Nested span
    s2 = tracer.start_span("verify_witness", parent=s1.context)
    checks.append(("s3_nested_span",
                    s2.context.parent_span_id == s1.context.span_id))

    # S3.3: End spans
    tracer.end_span(s2)
    tracer.end_span(s1)
    checks.append(("s3_completed", tracer.completed_span_count() == 2))

    # S3.4: Service attribute
    checks.append(("s3_service_attr",
                    s1.attributes.get("service.name") == "lct-service"))

    # S3.5: No active spans after cleanup
    checks.append(("s3_no_active", tracer.active_span_count() == 0))

    # ── S4: Trace Collector ──────────────────────────────────────────────

    collector = TraceCollector()

    # Create a multi-span trace
    root_ctx = TraceContext.new_trace()
    root = Span(root_ctx, "request", SpanKind.SERVER)
    root.end_time = root.start_time + 0.1

    child1_ctx = root_ctx.child_span()
    ch1 = Span(child1_ctx, "db_query", SpanKind.CLIENT)
    ch1.end_time = ch1.start_time + 0.05

    child2_ctx = root_ctx.child_span()
    ch2 = Span(child2_ctx, "cache_lookup", SpanKind.CLIENT)
    ch2.end_time = ch2.start_time + 0.01
    ch2.set_status(SpanStatus.ERROR, "cache miss")

    collector.ingest_batch([root, ch1, ch2])

    # S4.1: Spans ingested
    checks.append(("s4_spans_ingested", collector.total_spans_received == 3))

    # S4.2: Assemble trace
    record = collector.assemble_trace(root_ctx.trace_id)
    checks.append(("s4_trace_assembled", record is not None and
                    record.span_count == 3))

    # S4.3: Root span identified
    checks.append(("s4_root_span",
                    record.root_span is not None and
                    record.root_span.name == "request"))

    # S4.4: Error count
    checks.append(("s4_error_count", record.error_count == 1))

    # S4.5: Query traces with errors
    error_traces = collector.query_traces(has_errors=True)
    checks.append(("s4_query_errors", len(error_traces) == 1))

    # S4.6: Query by service
    root.attributes["service.name"] = "api-gateway"
    collector.assemble_trace(root_ctx.trace_id)  # re-assemble
    api_traces = collector.query_traces(service="api-gateway")
    checks.append(("s4_query_service", len(api_traces) == 1))

    # ── S5: Causal Ordering ──────────────────────────────────────────────

    # S5.1: Local events are ordered
    ct_a = CausalTracer("node_a")
    e1 = ct_a.local_event("activate")
    e2 = ct_a.local_event("witness")
    checks.append(("s5_local_order", e1.happens_before(e2)))

    # S5.2: Send-receive ordering
    ct_b = CausalTracer("node_b")
    send = ct_a.send_event("message")
    recv = ct_b.receive_event(send.vector_clock, "message")
    checks.append(("s5_send_recv_order", send.happens_before(recv)))

    # S5.3: Concurrent events
    ct_c = CausalTracer("node_c")
    e_c = ct_c.local_event("independent")
    checks.append(("s5_concurrent", e1.concurrent_with(e_c)))

    # S5.4: Vector clock merge
    checks.append(("s5_clock_merge",
                    ct_b.clock.get("node_a", 0) >= send.vector_clock.get("node_a", 0)))

    # S5.5: Event history
    checks.append(("s5_event_history", len(ct_a.events) >= 3))

    # ── S6: Diagnostic Engine ────────────────────────────────────────────

    diag = DiagnosticEngine()

    # S6.1: Analyze trace with errors
    reports = diag.analyze_trace(record)
    error_reports = [r for r in reports if r.category == "errors"]
    checks.append(("s6_error_report", len(error_reports) == 1))

    # S6.2: Reports have recommendations
    checks.append(("s6_recommendations",
                    all(len(r.recommendations) > 0 for r in reports)))

    # S6.3: Latency distribution
    # Create multiple traces
    coll2 = TraceCollector()
    for i in range(20):
        ctx_i = TraceContext.new_trace()
        s = Span(ctx_i, f"op_{i}", SpanKind.SERVER)
        s.end_time = s.start_time + (i + 1) * 0.001
        s.attributes["service.name"] = "test"
        coll2.ingest_span(s)
    coll2.assemble_all()
    all_records = list(coll2.traces.values())
    lat_dist = diag.analyze_latency_distribution(all_records)
    checks.append(("s6_latency_dist",
                    lat_dist["count"] == 20 and lat_dist["p50_ms"] > 0))

    # S6.4: Critical path analysis
    # Build a deeper trace
    deep_ctx = TraceContext.new_trace()
    deep_root = Span(deep_ctx, "root", SpanKind.SERVER)
    deep_root.end_time = deep_root.start_time + 0.1

    dc1_ctx = deep_ctx.child_span()
    dc1 = Span(dc1_ctx, "step_1", SpanKind.CLIENT)
    dc1.end_time = dc1.start_time + 0.05

    dc2_ctx = dc1_ctx.child_span()
    dc2 = Span(dc2_ctx, "step_2", SpanKind.CLIENT)
    dc2.end_time = dc2.start_time + 0.03

    deep_coll = TraceCollector()
    deep_coll.ingest_batch([deep_root, dc1, dc2])
    deep_record = deep_coll.assemble_trace(deep_ctx.trace_id)
    crit_path = diag.find_critical_path(deep_record)
    checks.append(("s6_critical_path", len(crit_path) == 3))

    # S6.5: Critical path order
    checks.append(("s6_path_order",
                    crit_path[0].name == "root" and
                    crit_path[1].name == "step_1" and
                    crit_path[2].name == "step_2"))

    # ── S7: Metrics Registry ────────────────────────────────────────────

    metrics = MetricsRegistry()

    # S7.1: Counter
    metrics.increment("requests_total", labels={"method": "GET"})
    metrics.increment("requests_total", labels={"method": "GET"})
    checks.append(("s7_counter",
                    metrics.get_counter("requests_total",
                                        labels={"method": "GET"}) == 2.0))

    # S7.2: Gauge
    metrics.set_gauge("active_connections", 42)
    checks.append(("s7_gauge",
                    metrics.get_gauge("active_connections") == 42))

    # S7.3: Histogram
    for i in range(100):
        metrics.observe("request_duration_ms", i * 1.0)
    stats = metrics.get_histogram_stats("request_duration_ms")
    checks.append(("s7_histogram",
                    stats["count"] == 100 and stats["avg"] == 49.5))

    # S7.4: Histogram percentiles
    checks.append(("s7_percentiles",
                    stats["p50"] == 50.0 and stats["p99"] == 99.0))

    # S7.5: Labeled metrics isolation
    metrics.increment("errors", labels={"service": "lct"})
    metrics.increment("errors", labels={"service": "atp"})
    checks.append(("s7_label_isolation",
                    metrics.get_counter("errors", {"service": "lct"}) == 1.0 and
                    metrics.get_counter("errors", {"service": "atp"}) == 1.0))

    # ── S8: Federation Trace Sync ────────────────────────────────────────

    fed_sync = FederationTraceSync("fed_1")
    coll_a = TraceCollector()
    coll_b = TraceCollector()
    fed_sync.register_collector("node_a", coll_a)
    fed_sync.register_collector("node_b", coll_b)

    # Create a cross-node trace
    cross_ctx = TraceContext.new_trace()
    span_a = Span(cross_ctx, "node_a_work", SpanKind.SERVER)
    span_a.end_time = span_a.start_time + 0.01
    span_a.attributes["service.name"] = "node_a"

    span_b_ctx = cross_ctx.child_span()
    span_b = Span(span_b_ctx, "node_b_work", SpanKind.CLIENT)
    span_b.end_time = span_b.start_time + 0.02
    span_b.attributes["service.name"] = "node_b"

    coll_a.ingest_span(span_a)
    coll_b.ingest_span(span_b)

    # S8.1: Sync detects cross-node trace
    cross_count = fed_sync.sync_traces()
    checks.append(("s8_cross_node_detected", cross_count == 1))

    # S8.2: Merge cross-node trace
    merged = fed_sync.merge_trace(cross_ctx.trace_id)
    checks.append(("s8_merged_spans", merged is not None and
                    merged.span_count == 2))

    # S8.3: Merged trace has both services
    checks.append(("s8_merged_services", merged.service_count == 2))

    # S8.4: Single-node trace not flagged as cross-node
    local_ctx = TraceContext.new_trace()
    local_span = Span(local_ctx, "local_only")
    local_span.end_time = local_span.start_time + 0.01
    coll_a.ingest_span(local_span)
    fed_sync.sync_traces()
    checks.append(("s8_local_not_cross",
                    local_ctx.trace_id not in fed_sync.cross_fed_traces))

    # ── S9: End-to-End Tracing Scenario ──────────────────────────────────

    # Simulate: LCT activation → witness verification → ATP transfer
    lct_tracer = Tracer("lct-service")
    atp_tracer = Tracer("atp-service")

    # S9.1: Start LCT activation
    lct_root = lct_tracer.start_span("activate_lct",
                                      kind=SpanKind.SERVER,
                                      entity_id="ent_42")
    lct_root.add_event("witness_check_start")

    # S9.2: Verify witness (child span)
    witness_span = lct_tracer.start_span("verify_witness",
                                          parent=lct_root.context,
                                          kind=SpanKind.CLIENT)
    witness_span.add_event("witness_valid", witness_id="w1")
    lct_tracer.end_span(witness_span)

    # S9.3: Cross-service: trigger ATP allocation
    atp_span = atp_tracer.start_span("allocate_atp",
                                      parent=lct_root.context,
                                      kind=SpanKind.SERVER,
                                      amount=100.0)
    atp_tracer.end_span(atp_span)
    lct_tracer.end_span(lct_root)

    # S9.4: Collect all spans
    e2e_collector = TraceCollector()
    e2e_collector.ingest_batch(lct_tracer.spans)
    e2e_collector.ingest_batch(atp_tracer.spans)
    e2e_collector.assemble_all()

    e2e_trace = list(e2e_collector.traces.values())[0]

    checks.append(("s9_e2e_spans", e2e_trace.span_count == 3))
    checks.append(("s9_e2e_services", e2e_trace.service_count == 2))
    checks.append(("s9_e2e_no_errors", e2e_trace.error_count == 0))

    # S9.5: Critical path includes all 3 spans
    e2e_path = diag.find_critical_path(e2e_trace)
    checks.append(("s9_e2e_critical_path", len(e2e_path) >= 2))

    # ── S10: Sampling ────────────────────────────────────────────────────

    # S10.1: Sampled flag propagation
    sampled = TraceContext.new_trace()
    sampled.trace_flags = 1
    child_sampled = sampled.child_span()
    checks.append(("s10_sampled_propagated", child_sampled.trace_flags == 1))

    # S10.2: Not-sampled flag
    not_sampled = TraceContext.new_trace()
    not_sampled.trace_flags = 0
    child_ns = not_sampled.child_span()
    checks.append(("s10_not_sampled", child_ns.trace_flags == 0))

    # S10.3: Header preserves flags
    hdr = sampled.to_header()
    checks.append(("s10_flags_in_header", hdr.endswith("-01")))

    # ── S11: Performance ─────────────────────────────────────────────────

    # S11.1: 10K span creation
    t_start = time.time()
    perf_tracer = Tracer("perf")
    for i in range(10000):
        s = perf_tracer.start_span(f"op_{i}")
        perf_tracer.end_span(s)
    span_time = time.time() - t_start
    checks.append(("s11_10k_spans", span_time < 5.0))

    # S11.2: 10K span ingestion
    perf_coll = TraceCollector()
    t_start = time.time()
    perf_coll.ingest_batch(perf_tracer.spans)
    ingest_time = time.time() - t_start
    checks.append(("s11_10k_ingest", ingest_time < 2.0))

    # S11.3: 1K causal events
    t_start = time.time()
    perf_ct = CausalTracer("perf_node")
    for i in range(1000):
        perf_ct.local_event(f"evt_{i}")
    causal_time = time.time() - t_start
    checks.append(("s11_1k_causal", causal_time < 2.0))

    # S11.4: 10K metric observations
    perf_metrics = MetricsRegistry()
    t_start = time.time()
    for i in range(10000):
        perf_metrics.observe("latency", float(i))
    metric_time = time.time() - t_start
    checks.append(("s11_10k_metrics", metric_time < 2.0))

    # ── Report ───────────────────────────────────────────────────────────

    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    elapsed = time.time() - t0

    print("=" * 60)
    print(f"  Distributed Tracing — {passed}/{total} checks passed")
    print("=" * 60)

    failures = []
    for name, ok in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")
        if not ok:
            failures.append(name)

    if failures:
        print(f"\n  FAILURES:")
        for f in failures:
            print(f"    ✗ {f}")

    print(f"\n  Time: {elapsed:.2f}s")
    return passed == total


if __name__ == "__main__":
    success = run_checks()
    raise SystemExit(0 if success else 1)
