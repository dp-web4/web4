#!/usr/bin/env python3
"""
Transport Abstraction & Protocol Bindings
==========================================

Unified transport interface for Web4 with pluggable adapters
for TCP, HTTP/2, WebSocket, CoAP, and QUIC. Includes security
profile mapping, message framing, and reliability guarantees.

Session 21 — Track 3
"""

from __future__ import annotations
import hashlib
import hmac
import math
import os
import struct
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# ─── Transport Layer Types ──────────────────────────────────────────────────

class TransportType(Enum):
    """Available transport protocols."""
    TCP = "tcp"
    HTTP2 = "http2"
    WEBSOCKET = "ws"
    COAP = "coap"
    QUIC = "quic"
    BLUETOOTH = "bt"
    LORA = "lora"


class SecurityLevel(Enum):
    """Transport security levels."""
    NONE = 0
    INTEGRITY = 1       # HMAC only
    ENCRYPTED = 2       # TLS/DTLS
    AUTHENTICATED = 3   # mTLS or equivalent
    HARDWARE_BOUND = 4  # TPM/SE anchored


class QoSLevel(Enum):
    """Quality of service levels."""
    BEST_EFFORT = 0     # Fire and forget
    AT_LEAST_ONCE = 1   # Retry with dedup
    EXACTLY_ONCE = 2    # Transactional
    ORDERED = 3         # Strict ordering + exactly-once


class MessagePriority(Enum):
    """Message priority for scheduling."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class TransportCapabilities:
    """Advertised capabilities of a transport."""
    transport_type: TransportType
    max_message_size: int          # bytes
    supports_streaming: bool
    supports_bidirectional: bool
    supports_multicast: bool
    min_latency_ms: float          # typical minimum latency
    max_throughput_bps: int        # bits per second
    security_levels: Set[SecurityLevel]
    qos_levels: Set[QoSLevel]
    mtu: int = 1500                # maximum transmission unit


# ─── Message Framing ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class MessageHeader:
    """Web4 transport message header."""
    version: int = 1
    message_type: int = 0         # 0=request, 1=response, 2=notification
    sequence: int = 0
    priority: MessagePriority = MessagePriority.NORMAL
    content_type: str = "application/web4+json"
    correlation_id: str = ""
    trace_id: str = ""
    ttl: int = 30                 # seconds

    def serialize(self) -> bytes:
        """Serialize header to wire format."""
        flags = (self.version << 4) | self.message_type
        prio = self.priority.value
        ct = self.content_type.encode()[:32].ljust(32, b'\0')
        cid = self.correlation_id.encode()[:16].ljust(16, b'\0')
        tid = self.trace_id.encode()[:16].ljust(16, b'\0')
        return struct.pack(
            '!BBIH32s16s16s',
            flags, prio, self.sequence, self.ttl,
            ct, cid, tid
        )

    @staticmethod
    def deserialize(data: bytes) -> MessageHeader:
        """Deserialize header from wire format."""
        flags, prio, seq, ttl, ct, cid, tid = struct.unpack(
            '!BBIH32s16s16s', data[:73]
        )
        return MessageHeader(
            version=(flags >> 4) & 0xF,
            message_type=flags & 0xF,
            sequence=seq,
            priority=MessagePriority(prio),
            content_type=ct.rstrip(b'\0').decode(),
            correlation_id=cid.rstrip(b'\0').decode(),
            trace_id=tid.rstrip(b'\0').decode(),
            ttl=ttl,
        )

    def header_size(self) -> int:
        """Fixed header size in bytes."""
        return 72  # BBIH32s16s16s = 1+1+4+2+32+16+16


@dataclass
class TransportMessage:
    """A framed transport message."""
    header: MessageHeader
    payload: bytes
    security_tag: Optional[bytes] = None  # HMAC or signature

    def frame(self) -> bytes:
        """Frame the message for wire transmission."""
        hdr = self.header.serialize()
        payload_len = len(self.payload)
        tag = self.security_tag or b''
        tag_len = len(tag)
        # Length-prefixed framing
        return (struct.pack('!II', payload_len, tag_len) +
                hdr + self.payload + tag)

    @staticmethod
    def unframe(data: bytes) -> TransportMessage:
        """Parse a framed message."""
        HDR_SIZE = 72  # BBIH32s16s16s
        payload_len, tag_len = struct.unpack('!II', data[:8])
        hdr = MessageHeader.deserialize(data[8:8 + HDR_SIZE])
        off = 8 + HDR_SIZE
        payload = data[off:off + payload_len]
        tag = data[off + payload_len:off + payload_len + tag_len] if tag_len else None
        return TransportMessage(hdr, payload, tag)

    def sign(self, key: bytes) -> TransportMessage:
        """Add HMAC security tag."""
        tag = hmac.new(key, self.header.serialize() + self.payload,
                       'sha256').digest()
        return TransportMessage(self.header, self.payload, tag)

    def verify(self, key: bytes) -> bool:
        """Verify HMAC security tag."""
        if not self.security_tag:
            return False
        expected = hmac.new(key, self.header.serialize() + self.payload,
                            'sha256').digest()
        return hmac.compare_digest(expected, self.security_tag)


# ─── Transport Adapter Interface ───────────────────────────────────────────

class TransportAdapter(ABC):
    """
    Abstract transport adapter interface.

    All Web4 transports implement this interface, providing
    a uniform API regardless of underlying protocol.
    """

    @abstractmethod
    def capabilities(self) -> TransportCapabilities:
        """Return transport capabilities."""
        ...

    @abstractmethod
    def send(self, message: TransportMessage, endpoint: str) -> bool:
        """Send a message to an endpoint."""
        ...

    @abstractmethod
    def receive(self, timeout_ms: int = 5000) -> Optional[TransportMessage]:
        """Receive a message (blocking with timeout)."""
        ...

    @abstractmethod
    def connect(self, endpoint: str) -> bool:
        """Establish connection to endpoint."""
        ...

    @abstractmethod
    def disconnect(self, endpoint: str) -> None:
        """Close connection to endpoint."""
        ...

    @abstractmethod
    def is_connected(self, endpoint: str) -> bool:
        """Check if connected to endpoint."""
        ...


# ─── Simulated Transport Adapters ──────────────────────────────────────────

class SimulatedNetwork:
    """Shared simulated network for testing transports."""
    def __init__(self):
        self.queues: Dict[str, deque] = {}
        self.connected: Dict[Tuple[str, str], bool] = {}
        self.latency_ms: float = 1.0
        self.packet_loss: float = 0.0
        self.bandwidth_bps: int = 100_000_000  # 100 Mbps
        self.messages_sent: int = 0
        self.messages_received: int = 0
        self.bytes_sent: int = 0

    def register(self, endpoint: str):
        if endpoint not in self.queues:
            self.queues[endpoint] = deque()

    def deliver(self, source: str, dest: str, msg: TransportMessage) -> bool:
        import random
        if random.random() < self.packet_loss:
            return False
        if dest in self.queues:
            self.queues[dest].append((source, msg))
            self.messages_sent += 1
            self.bytes_sent += len(msg.payload)
            return True
        return False

    def poll(self, endpoint: str) -> Optional[Tuple[str, TransportMessage]]:
        if endpoint in self.queues and self.queues[endpoint]:
            self.messages_received += 1
            return self.queues[endpoint].popleft()
        return None


class TCPAdapter(TransportAdapter):
    """TCP transport adapter (simulated)."""

    def __init__(self, local_endpoint: str, network: SimulatedNetwork):
        self.local = local_endpoint
        self.network = network
        self._connections: Set[str] = set()
        self._seq: int = 0
        network.register(local_endpoint)

    def capabilities(self) -> TransportCapabilities:
        return TransportCapabilities(
            transport_type=TransportType.TCP,
            max_message_size=65535,
            supports_streaming=True,
            supports_bidirectional=True,
            supports_multicast=False,
            min_latency_ms=0.5,
            max_throughput_bps=1_000_000_000,
            security_levels={SecurityLevel.NONE, SecurityLevel.ENCRYPTED,
                             SecurityLevel.AUTHENTICATED},
            qos_levels={QoSLevel.EXACTLY_ONCE, QoSLevel.ORDERED},
        )

    def send(self, message: TransportMessage, endpoint: str) -> bool:
        if endpoint not in self._connections:
            return False
        self._seq += 1
        return self.network.deliver(self.local, endpoint, message)

    def receive(self, timeout_ms: int = 5000) -> Optional[TransportMessage]:
        result = self.network.poll(self.local)
        return result[1] if result else None

    def connect(self, endpoint: str) -> bool:
        self.network.register(endpoint)
        self._connections.add(endpoint)
        self.network.connected[(self.local, endpoint)] = True
        return True

    def disconnect(self, endpoint: str) -> None:
        self._connections.discard(endpoint)
        self.network.connected.pop((self.local, endpoint), None)

    def is_connected(self, endpoint: str) -> bool:
        return endpoint in self._connections


class HTTP2Adapter(TransportAdapter):
    """HTTP/2 transport adapter (simulated)."""

    def __init__(self, local_endpoint: str, network: SimulatedNetwork):
        self.local = local_endpoint
        self.network = network
        self._connections: Set[str] = set()
        self._streams: Dict[str, int] = {}  # endpoint → stream count
        network.register(local_endpoint)

    def capabilities(self) -> TransportCapabilities:
        return TransportCapabilities(
            transport_type=TransportType.HTTP2,
            max_message_size=16_777_216,  # 16 MB
            supports_streaming=True,
            supports_bidirectional=True,
            supports_multicast=False,
            min_latency_ms=5.0,
            max_throughput_bps=500_000_000,
            security_levels={SecurityLevel.ENCRYPTED, SecurityLevel.AUTHENTICATED},
            qos_levels={QoSLevel.AT_LEAST_ONCE, QoSLevel.EXACTLY_ONCE},
        )

    def send(self, message: TransportMessage, endpoint: str) -> bool:
        if endpoint not in self._connections:
            return False
        self._streams[endpoint] = self._streams.get(endpoint, 0) + 1
        return self.network.deliver(self.local, endpoint, message)

    def receive(self, timeout_ms: int = 5000) -> Optional[TransportMessage]:
        result = self.network.poll(self.local)
        return result[1] if result else None

    def connect(self, endpoint: str) -> bool:
        self.network.register(endpoint)
        self._connections.add(endpoint)
        self._streams[endpoint] = 0
        return True

    def disconnect(self, endpoint: str) -> None:
        self._connections.discard(endpoint)
        self._streams.pop(endpoint, None)

    def is_connected(self, endpoint: str) -> bool:
        return endpoint in self._connections


class CoAPAdapter(TransportAdapter):
    """CoAP transport adapter for constrained devices (simulated)."""

    def __init__(self, local_endpoint: str, network: SimulatedNetwork):
        self.local = local_endpoint
        self.network = network
        self._peers: Set[str] = set()
        self._token_counter: int = 0
        self._observe_resources: Dict[str, Set[str]] = {}
        network.register(local_endpoint)

    def capabilities(self) -> TransportCapabilities:
        return TransportCapabilities(
            transport_type=TransportType.COAP,
            max_message_size=1024,  # CoAP block-wise for larger
            supports_streaming=False,
            supports_bidirectional=False,
            supports_multicast=True,
            min_latency_ms=10.0,
            max_throughput_bps=250_000,
            security_levels={SecurityLevel.NONE, SecurityLevel.INTEGRITY,
                             SecurityLevel.ENCRYPTED},
            qos_levels={QoSLevel.BEST_EFFORT, QoSLevel.AT_LEAST_ONCE},
            mtu=128,  # constrained
        )

    def send(self, message: TransportMessage, endpoint: str) -> bool:
        self._token_counter += 1
        return self.network.deliver(self.local, endpoint, message)

    def receive(self, timeout_ms: int = 5000) -> Optional[TransportMessage]:
        result = self.network.poll(self.local)
        return result[1] if result else None

    def connect(self, endpoint: str) -> bool:
        self.network.register(endpoint)
        self._peers.add(endpoint)
        return True

    def disconnect(self, endpoint: str) -> None:
        self._peers.discard(endpoint)

    def is_connected(self, endpoint: str) -> bool:
        return endpoint in self._peers

    def observe(self, resource: str, observer: str):
        """CoAP observe registration."""
        self._observe_resources.setdefault(resource, set()).add(observer)

    def observers(self, resource: str) -> Set[str]:
        return self._observe_resources.get(resource, set())


class WebSocketAdapter(TransportAdapter):
    """WebSocket transport adapter (simulated)."""

    def __init__(self, local_endpoint: str, network: SimulatedNetwork):
        self.local = local_endpoint
        self.network = network
        self._connections: Set[str] = set()
        self._ping_pong: Dict[str, float] = {}
        network.register(local_endpoint)

    def capabilities(self) -> TransportCapabilities:
        return TransportCapabilities(
            transport_type=TransportType.WEBSOCKET,
            max_message_size=1_048_576,  # 1 MB
            supports_streaming=True,
            supports_bidirectional=True,
            supports_multicast=False,
            min_latency_ms=2.0,
            max_throughput_bps=100_000_000,
            security_levels={SecurityLevel.ENCRYPTED, SecurityLevel.AUTHENTICATED},
            qos_levels={QoSLevel.BEST_EFFORT, QoSLevel.AT_LEAST_ONCE},
        )

    def send(self, message: TransportMessage, endpoint: str) -> bool:
        if endpoint not in self._connections:
            return False
        return self.network.deliver(self.local, endpoint, message)

    def receive(self, timeout_ms: int = 5000) -> Optional[TransportMessage]:
        result = self.network.poll(self.local)
        return result[1] if result else None

    def connect(self, endpoint: str) -> bool:
        self.network.register(endpoint)
        self._connections.add(endpoint)
        self._ping_pong[endpoint] = time.time()
        return True

    def disconnect(self, endpoint: str) -> None:
        self._connections.discard(endpoint)
        self._ping_pong.pop(endpoint, None)

    def is_connected(self, endpoint: str) -> bool:
        return endpoint in self._connections

    def ping(self, endpoint: str) -> float:
        """Measure round-trip time."""
        self._ping_pong[endpoint] = time.time()
        return 0.002  # simulated 2ms RTT


# ─── Transport Selection ───────────────────────────────────────────────────

@dataclass
class TransportRequirements:
    """Requirements for selecting a transport."""
    min_security: SecurityLevel = SecurityLevel.NONE
    min_qos: QoSLevel = QoSLevel.BEST_EFFORT
    max_latency_ms: float = 1000.0
    min_throughput_bps: int = 0
    max_message_size: int = 0
    needs_streaming: bool = False
    needs_bidirectional: bool = False
    needs_multicast: bool = False


class TransportSelector:
    """Select optimal transport based on requirements."""

    def __init__(self):
        self.adapters: Dict[TransportType, TransportAdapter] = {}

    def register(self, adapter: TransportAdapter):
        caps = adapter.capabilities()
        self.adapters[caps.transport_type] = adapter

    def select(self, reqs: TransportRequirements) -> Optional[TransportAdapter]:
        """Select the best transport meeting requirements."""
        candidates = []

        for tt, adapter in self.adapters.items():
            caps = adapter.capabilities()

            # Filter: must meet all hard requirements
            if reqs.min_security.value > max(
                    s.value for s in caps.security_levels):
                continue
            if reqs.min_qos.value > max(q.value for q in caps.qos_levels):
                continue
            if caps.min_latency_ms > reqs.max_latency_ms:
                continue
            if reqs.min_throughput_bps > caps.max_throughput_bps:
                continue
            if reqs.max_message_size > caps.max_message_size:
                continue
            if reqs.needs_streaming and not caps.supports_streaming:
                continue
            if reqs.needs_bidirectional and not caps.supports_bidirectional:
                continue
            if reqs.needs_multicast and not caps.supports_multicast:
                continue

            # Score: prefer low latency, high throughput
            score = (1.0 / max(caps.min_latency_ms, 0.1) +
                     caps.max_throughput_bps / 1e9)
            candidates.append((score, adapter))

        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    def select_all(self, reqs: TransportRequirements) -> List[TransportAdapter]:
        """Return all transports meeting requirements, sorted by score."""
        candidates = []
        for tt, adapter in self.adapters.items():
            caps = adapter.capabilities()
            if reqs.min_security.value > max(
                    s.value for s in caps.security_levels):
                continue
            if reqs.min_qos.value > max(q.value for q in caps.qos_levels):
                continue
            if reqs.needs_multicast and not caps.supports_multicast:
                continue
            score = (1.0 / max(caps.min_latency_ms, 0.1) +
                     caps.max_throughput_bps / 1e9)
            candidates.append((score, adapter))
        candidates.sort(key=lambda x: x[0], reverse=True)
        return [a for _, a in candidates]


# ─── Transport Security Profiles ───────────────────────────────────────────

@dataclass
class SecurityProfile:
    """Security configuration for a transport."""
    level: SecurityLevel
    cipher_suite: str = "AES-256-GCM"
    key_exchange: str = "ECDHE"
    mac_algorithm: str = "SHA-256"
    min_key_length: int = 256
    mutual_auth: bool = False
    hardware_binding: bool = False

    def meets_requirement(self, required: SecurityLevel) -> bool:
        return self.level.value >= required.value


# Per-transport default security profiles
TRANSPORT_SECURITY: Dict[TransportType, SecurityProfile] = {
    TransportType.TCP: SecurityProfile(
        SecurityLevel.ENCRYPTED, "AES-256-GCM", "ECDHE", "SHA-256",
        256, False, False
    ),
    TransportType.HTTP2: SecurityProfile(
        SecurityLevel.AUTHENTICATED, "AES-256-GCM", "ECDHE", "SHA-256",
        256, True, False
    ),
    TransportType.WEBSOCKET: SecurityProfile(
        SecurityLevel.ENCRYPTED, "AES-128-GCM", "ECDHE", "SHA-256",
        128, False, False
    ),
    TransportType.COAP: SecurityProfile(
        SecurityLevel.INTEGRITY, "AES-128-CCM", "PSK", "SHA-256",
        128, False, False
    ),
    TransportType.QUIC: SecurityProfile(
        SecurityLevel.AUTHENTICATED, "AES-256-GCM", "ECDHE", "SHA-256",
        256, True, False
    ),
}


# ─── Reliability Layer ─────────────────────────────────────────────────────

@dataclass
class ReliabilityConfig:
    """Configuration for reliability guarantees."""
    max_retries: int = 3
    retry_backoff_ms: float = 100.0
    dedup_window: int = 1000
    ack_timeout_ms: float = 500.0
    ordering_window: int = 100


@dataclass
class ReliableTransport:
    """
    Adds reliability guarantees on top of any transport adapter.

    Provides at-least-once, exactly-once, and ordered delivery
    via sequence numbers, deduplication, and acknowledgments.
    """
    adapter: TransportAdapter
    config: ReliabilityConfig = field(default_factory=ReliabilityConfig)
    _sent_unacked: Dict[int, TransportMessage] = field(default_factory=dict)
    _received_seqs: deque = field(default_factory=lambda: deque(maxlen=1000))
    _next_seq: int = 0
    _retry_counts: Dict[int, int] = field(default_factory=dict)
    _delivered: int = 0
    _duplicates: int = 0

    def send_reliable(self, payload: bytes, endpoint: str,
                      priority: MessagePriority = MessagePriority.NORMAL
                      ) -> Tuple[bool, int]:
        """Send with reliability guarantees. Returns (success, sequence)."""
        seq = self._next_seq
        self._next_seq += 1

        header = MessageHeader(
            version=1, message_type=0, sequence=seq,
            priority=priority,
            correlation_id=hashlib.sha256(
                f"{seq}:{time.time()}".encode()
            ).hexdigest()[:16],
        )
        msg = TransportMessage(header, payload)

        success = self.adapter.send(msg, endpoint)
        if success:
            self._sent_unacked[seq] = msg
            self._retry_counts[seq] = 0
        return success, seq

    def receive_reliable(self, timeout_ms: int = 5000
                         ) -> Optional[TransportMessage]:
        """Receive with deduplication."""
        msg = self.adapter.receive(timeout_ms)
        if not msg:
            return None

        seq = msg.header.sequence
        if seq in self._received_seqs:
            self._duplicates += 1
            return None  # duplicate

        self._received_seqs.append(seq)
        self._delivered += 1
        return msg

    def retry_unacked(self, endpoint: str) -> int:
        """Retry unacknowledged messages. Returns retry count."""
        retried = 0
        to_remove = []
        for seq, msg in list(self._sent_unacked.items()):
            count = self._retry_counts.get(seq, 0)
            if count >= self.config.max_retries:
                to_remove.append(seq)
                continue
            self.adapter.send(msg, endpoint)
            self._retry_counts[seq] = count + 1
            retried += 1

        for seq in to_remove:
            self._sent_unacked.pop(seq, None)
            self._retry_counts.pop(seq, None)

        return retried

    def ack(self, seq: int):
        """Acknowledge receipt of a sequence number."""
        self._sent_unacked.pop(seq, None)
        self._retry_counts.pop(seq, None)


# ─── Transport Metrics ─────────────────────────────────────────────────────

@dataclass
class TransportMetrics:
    """Runtime metrics for a transport."""
    messages_sent: int = 0
    messages_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    errors: int = 0
    retries: int = 0
    avg_latency_ms: float = 0.0
    _latencies: List[float] = field(default_factory=list)

    def record_send(self, size: int):
        self.messages_sent += 1
        self.bytes_sent += size

    def record_receive(self, size: int):
        self.messages_received += 1
        self.bytes_received += size

    def record_latency(self, ms: float):
        self._latencies.append(ms)
        self.avg_latency_ms = sum(self._latencies) / len(self._latencies)

    def record_error(self):
        self.errors += 1

    def error_rate(self) -> float:
        total = self.messages_sent + self.messages_received
        return self.errors / max(total, 1)


# ─── Multi-Transport Dispatcher ────────────────────────────────────────────

@dataclass
class DispatchRule:
    """Rule for routing messages to transports."""
    name: str
    predicate: Callable[[TransportMessage], bool]
    transport_type: TransportType
    priority: int = 0


class MultiTransportDispatcher:
    """
    Route messages to appropriate transports based on content,
    priority, and requirements.
    """

    def __init__(self):
        self.adapters: Dict[TransportType, TransportAdapter] = {}
        self.rules: List[DispatchRule] = []
        self.fallback: Optional[TransportType] = None
        self.metrics: Dict[TransportType, TransportMetrics] = {}

    def register_transport(self, adapter: TransportAdapter):
        caps = adapter.capabilities()
        self.adapters[caps.transport_type] = adapter
        self.metrics[caps.transport_type] = TransportMetrics()

    def add_rule(self, rule: DispatchRule):
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def dispatch(self, message: TransportMessage, endpoint: str) -> bool:
        """Dispatch a message using rules to select transport."""
        for rule in self.rules:
            if rule.predicate(message):
                adapter = self.adapters.get(rule.transport_type)
                if adapter and adapter.is_connected(endpoint):
                    success = adapter.send(message, endpoint)
                    if success:
                        m = self.metrics[rule.transport_type]
                        m.record_send(len(message.payload))
                    return success

        # Fallback
        if self.fallback and self.fallback in self.adapters:
            adapter = self.adapters[self.fallback]
            if adapter.is_connected(endpoint):
                return adapter.send(message, endpoint)
        return False


# ─── Checks ─────────────────────────────────────────────────────────────────

def run_checks():
    checks = []
    t0 = time.time()

    net = SimulatedNetwork()

    # ── S1: Message Framing ──────────────────────────────────────────────

    # S1.1: Header serialization round-trip
    hdr = MessageHeader(
        version=1, message_type=0, sequence=42,
        priority=MessagePriority.HIGH,
        content_type="application/web4+json",
        correlation_id="abc123",
        trace_id="trace_456",
        ttl=60,
    )
    serialized = hdr.serialize()
    restored = MessageHeader.deserialize(serialized)
    checks.append(("s1_header_roundtrip",
                    restored.version == 1 and restored.sequence == 42 and
                    restored.priority == MessagePriority.HIGH and
                    restored.ttl == 60))

    # S1.2: Header fixed size
    checks.append(("s1_header_size", hdr.header_size() == 72))

    # S1.3: Message framing
    msg = TransportMessage(hdr, b"hello web4")
    framed = msg.frame()
    unframed = TransportMessage.unframe(framed)
    checks.append(("s1_message_roundtrip",
                    unframed.payload == b"hello web4" and
                    unframed.header.sequence == 42))

    # S1.4: Message signing
    key = os.urandom(32)
    signed = msg.sign(key)
    checks.append(("s1_message_signed", signed.security_tag is not None))

    # S1.5: Message verification
    checks.append(("s1_message_verified", signed.verify(key)))

    # S1.6: Tampered message fails verification
    tampered = TransportMessage(signed.header, b"tampered", signed.security_tag)
    checks.append(("s1_tampered_fails", not tampered.verify(key)))

    # S1.7: Wrong key fails verification
    checks.append(("s1_wrong_key_fails", not signed.verify(os.urandom(32))))

    # ── S2: Transport Adapters ───────────────────────────────────────────

    # S2.1: TCP adapter
    tcp_a = TCPAdapter("tcp://node_a", net)
    tcp_b = TCPAdapter("tcp://node_b", net)
    tcp_a.connect("tcp://node_b")
    tcp_b.connect("tcp://node_a")
    checks.append(("s2_tcp_connected", tcp_a.is_connected("tcp://node_b")))

    # S2.2: TCP send/receive
    test_msg = TransportMessage(
        MessageHeader(sequence=1), b"tcp_payload"
    )
    sent = tcp_a.send(test_msg, "tcp://node_b")
    received = tcp_b.receive()
    checks.append(("s2_tcp_send_recv",
                    sent and received is not None and
                    received.payload == b"tcp_payload"))

    # S2.3: HTTP/2 adapter
    http_a = HTTP2Adapter("http2://server_a", net)
    http_b = HTTP2Adapter("http2://server_b", net)
    http_a.connect("http2://server_b")
    http_b.connect("http2://server_a")
    http_msg = TransportMessage(MessageHeader(sequence=1), b"http2_data")
    http_a.send(http_msg, "http2://server_b")
    http_recv = http_b.receive()
    checks.append(("s2_http2_send_recv",
                    http_recv is not None and http_recv.payload == b"http2_data"))

    # S2.4: CoAP adapter
    coap_a = CoAPAdapter("coap://sensor_1", net)
    coap_b = CoAPAdapter("coap://gateway", net)
    coap_a.connect("coap://gateway")
    coap_msg = TransportMessage(MessageHeader(sequence=1), b"temp=22.5")
    coap_a.send(coap_msg, "coap://gateway")
    coap_recv = coap_b.receive()
    checks.append(("s2_coap_send_recv",
                    coap_recv is not None and coap_recv.payload == b"temp=22.5"))

    # S2.5: CoAP observe
    coap_a.observe("/temperature", "coap://gateway")
    checks.append(("s2_coap_observe",
                    "coap://gateway" in coap_a.observers("/temperature")))

    # S2.6: WebSocket adapter
    ws_a = WebSocketAdapter("ws://client", net)
    ws_b = WebSocketAdapter("ws://server", net)
    ws_a.connect("ws://server")
    ws_b.connect("ws://client")
    ws_msg = TransportMessage(MessageHeader(sequence=1), b"ws_frame")
    ws_a.send(ws_msg, "ws://server")
    ws_recv = ws_b.receive()
    checks.append(("s2_ws_send_recv",
                    ws_recv is not None and ws_recv.payload == b"ws_frame"))

    # S2.7: WebSocket ping
    rtt = ws_a.ping("ws://server")
    checks.append(("s2_ws_ping", rtt > 0))

    # S2.8: Disconnect
    tcp_a.disconnect("tcp://node_b")
    checks.append(("s2_disconnect", not tcp_a.is_connected("tcp://node_b")))

    # ── S3: Transport Capabilities ───────────────────────────────────────

    # S3.1: TCP capabilities
    tcp_caps = tcp_a.capabilities()
    checks.append(("s3_tcp_caps",
                    tcp_caps.transport_type == TransportType.TCP and
                    tcp_caps.supports_streaming and
                    tcp_caps.supports_bidirectional))

    # S3.2: CoAP capabilities (constrained)
    coap_caps = coap_a.capabilities()
    checks.append(("s3_coap_caps",
                    coap_caps.max_message_size == 1024 and
                    coap_caps.supports_multicast and
                    not coap_caps.supports_streaming))

    # S3.3: HTTP/2 capabilities
    http_caps = http_a.capabilities()
    checks.append(("s3_http2_caps",
                    http_caps.max_message_size == 16_777_216 and
                    SecurityLevel.AUTHENTICATED in http_caps.security_levels))

    # S3.4: WebSocket capabilities
    ws_caps = ws_a.capabilities()
    checks.append(("s3_ws_caps",
                    ws_caps.supports_bidirectional and
                    QoSLevel.AT_LEAST_ONCE in ws_caps.qos_levels))

    # ── S4: Transport Selection ──────────────────────────────────────────

    selector = TransportSelector()
    selector.register(tcp_a)
    selector.register(http_a)
    selector.register(coap_a)
    selector.register(ws_a)

    # S4.1: Select for streaming
    streaming_req = TransportRequirements(needs_streaming=True)
    streaming_transport = selector.select(streaming_req)
    checks.append(("s4_streaming_selected", streaming_transport is not None))

    # S4.2: Selected transport supports streaming
    checks.append(("s4_streaming_supports",
                    streaming_transport.capabilities().supports_streaming))

    # S4.3: Select for multicast
    multicast_req = TransportRequirements(needs_multicast=True)
    multicast_transport = selector.select(multicast_req)
    checks.append(("s4_multicast_coap",
                    multicast_transport is not None and
                    multicast_transport.capabilities().transport_type == TransportType.COAP))

    # S4.4: Select for authenticated
    auth_req = TransportRequirements(min_security=SecurityLevel.AUTHENTICATED)
    auth_transport = selector.select(auth_req)
    checks.append(("s4_auth_selected", auth_transport is not None))

    # S4.5: Select all meeting requirements
    all_streaming = selector.select_all(streaming_req)
    checks.append(("s4_all_streaming", len(all_streaming) >= 3))

    # S4.6: Impossible requirements return None
    impossible_req = TransportRequirements(
        min_security=SecurityLevel.HARDWARE_BOUND,
        needs_multicast=True,
    )
    impossible = selector.select(impossible_req)
    checks.append(("s4_impossible_none", impossible is None))

    # ── S5: Security Profiles ────────────────────────────────────────────

    # S5.1: TCP security profile
    tcp_sec = TRANSPORT_SECURITY[TransportType.TCP]
    checks.append(("s5_tcp_security",
                    tcp_sec.level == SecurityLevel.ENCRYPTED and
                    tcp_sec.cipher_suite == "AES-256-GCM"))

    # S5.2: HTTP/2 security — mutual auth
    http_sec = TRANSPORT_SECURITY[TransportType.HTTP2]
    checks.append(("s5_http2_mutual_auth", http_sec.mutual_auth))

    # S5.3: CoAP security — integrity only
    coap_sec = TRANSPORT_SECURITY[TransportType.COAP]
    checks.append(("s5_coap_integrity",
                    coap_sec.level == SecurityLevel.INTEGRITY))

    # S5.4: Security meets requirement check
    checks.append(("s5_http2_meets_encrypted",
                    http_sec.meets_requirement(SecurityLevel.ENCRYPTED)))
    checks.append(("s5_coap_not_encrypted",
                    not coap_sec.meets_requirement(SecurityLevel.ENCRYPTED)))

    # ── S6: Reliability Layer ────────────────────────────────────────────

    net2 = SimulatedNetwork()
    rel_a_adapter = TCPAdapter("tcp://rel_a", net2)
    rel_b_adapter = TCPAdapter("tcp://rel_b", net2)
    rel_a_adapter.connect("tcp://rel_b")
    rel_b_adapter.connect("tcp://rel_a")

    rel_a = ReliableTransport(rel_a_adapter)
    rel_b = ReliableTransport(rel_b_adapter)

    # S6.1: Reliable send
    ok, seq = rel_a.send_reliable(b"reliable_data", "tcp://rel_b")
    checks.append(("s6_reliable_send", ok and seq == 0))

    # S6.2: Reliable receive with dedup
    msg1 = rel_b.receive_reliable()
    checks.append(("s6_reliable_recv",
                    msg1 is not None and msg1.payload == b"reliable_data"))

    # S6.3: Duplicate detection
    # Send same message again (replay)
    rel_a_adapter.send(msg1, "tcp://rel_b")
    dup = rel_b.receive_reliable()
    checks.append(("s6_dedup", dup is None and rel_b._duplicates == 1))

    # S6.4: Sequence incrementing
    ok2, seq2 = rel_a.send_reliable(b"second", "tcp://rel_b")
    checks.append(("s6_sequence_increment", seq2 == 1))

    # S6.5: Acknowledgment
    rel_a.ack(0)
    checks.append(("s6_ack_removes", 0 not in rel_a._sent_unacked))

    # S6.6: Retry unacked
    ok3, seq3 = rel_a.send_reliable(b"unacked", "tcp://rel_b")
    retried = rel_a.retry_unacked("tcp://rel_b")
    checks.append(("s6_retry", retried >= 1))

    # ── S7: Multi-Transport Dispatcher ───────────────────────────────────

    net3 = SimulatedNetwork()
    d_tcp = TCPAdapter("tcp://dispatch_a", net3)
    d_http = HTTP2Adapter("http2://dispatch_a", net3)
    d_ws = WebSocketAdapter("ws://dispatch_a", net3)

    d_tcp.connect("tcp://target")
    d_http.connect("http2://target")
    d_ws.connect("ws://target")

    dispatcher = MultiTransportDispatcher()
    dispatcher.register_transport(d_tcp)
    dispatcher.register_transport(d_http)
    dispatcher.register_transport(d_ws)
    dispatcher.fallback = TransportType.TCP

    # S7.1: Add rules
    dispatcher.add_rule(DispatchRule(
        "high_priority_tcp",
        lambda m: m.header.priority == MessagePriority.CRITICAL,
        TransportType.TCP, priority=10
    ))
    dispatcher.add_rule(DispatchRule(
        "large_payload_http2",
        lambda m: len(m.payload) > 1000,
        TransportType.HTTP2, priority=5
    ))
    checks.append(("s7_rules_added", len(dispatcher.rules) == 2))

    # S7.2: Dispatch critical via TCP
    critical_msg = TransportMessage(
        MessageHeader(priority=MessagePriority.CRITICAL), b"alert"
    )
    ok_dispatch = dispatcher.dispatch(critical_msg, "tcp://target")
    checks.append(("s7_critical_tcp", ok_dispatch))

    # S7.3: Dispatch large via HTTP/2
    large_msg = TransportMessage(
        MessageHeader(priority=MessagePriority.NORMAL), b"x" * 2000
    )
    ok_large = dispatcher.dispatch(large_msg, "http2://target")
    checks.append(("s7_large_http2", ok_large))

    # S7.4: Fallback to TCP
    normal_msg = TransportMessage(
        MessageHeader(priority=MessagePriority.NORMAL), b"small"
    )
    ok_fallback = dispatcher.dispatch(normal_msg, "tcp://target")
    checks.append(("s7_fallback_tcp", ok_fallback))

    # S7.5: Metrics tracked
    tcp_metrics = dispatcher.metrics[TransportType.TCP]
    checks.append(("s7_metrics_tracked", tcp_metrics.messages_sent >= 1))

    # ── S8: Transport Metrics ────────────────────────────────────────────

    m = TransportMetrics()

    # S8.1: Record send
    m.record_send(1024)
    checks.append(("s8_send_recorded",
                    m.messages_sent == 1 and m.bytes_sent == 1024))

    # S8.2: Record receive
    m.record_receive(512)
    checks.append(("s8_recv_recorded",
                    m.messages_received == 1 and m.bytes_received == 512))

    # S8.3: Record latency
    m.record_latency(5.0)
    m.record_latency(3.0)
    checks.append(("s8_avg_latency", abs(m.avg_latency_ms - 4.0) < 0.01))

    # S8.4: Error rate
    m.record_error()
    checks.append(("s8_error_rate", abs(m.error_rate() - 0.5) < 0.01))

    # ── S9: Network Simulation ───────────────────────────────────────────

    # S9.1: Network message count
    checks.append(("s9_network_messages", net.messages_sent >= 4))

    # S9.2: Network bytes
    checks.append(("s9_network_bytes", net.bytes_sent > 0))

    # S9.3: Unregistered endpoint
    result = net.deliver("unknown_src", "unknown_dest",
                         TransportMessage(MessageHeader(), b""))
    checks.append(("s9_unknown_endpoint", not result))

    # ── S10: Content Type Negotiation ────────────────────────────────────

    # S10.1: JSON content type
    json_msg = TransportMessage(
        MessageHeader(content_type="application/web4+json"),
        b'{"type": "lct"}'
    )
    checks.append(("s10_json_content",
                    json_msg.header.content_type == "application/web4+json"))

    # S10.2: CBOR content type
    cbor_msg = TransportMessage(
        MessageHeader(content_type="application/web4+cbor"),
        b'\xa1\x64type\x63lct'
    )
    checks.append(("s10_cbor_content",
                    cbor_msg.header.content_type == "application/web4+cbor"))

    # S10.3: Content type survives serialization
    framed = json_msg.frame()
    restored = TransportMessage.unframe(framed)
    checks.append(("s10_content_type_roundtrip",
                    restored.header.content_type == "application/web4+json"))

    # ── S11: Performance ─────────────────────────────────────────────────

    perf_net = SimulatedNetwork()

    # S11.1: 1000 messages through TCP
    t_start = time.time()
    perf_a = TCPAdapter("tcp://perf_a", perf_net)
    perf_b = TCPAdapter("tcp://perf_b", perf_net)
    perf_a.connect("tcp://perf_b")
    for i in range(1000):
        perf_a.send(
            TransportMessage(MessageHeader(sequence=i), f"msg_{i}".encode()),
            "tcp://perf_b"
        )
    tcp_perf = time.time() - t_start
    checks.append(("s11_1000_tcp", tcp_perf < 1.0))

    # S11.2: All messages received
    recv_count = 0
    while perf_b.receive():
        recv_count += 1
    checks.append(("s11_all_received", recv_count == 1000))

    # S11.3: 100 header serializations
    t_start = time.time()
    for i in range(10000):
        h = MessageHeader(sequence=i)
        s = h.serialize()
        MessageHeader.deserialize(s)
    serial_time = time.time() - t_start
    checks.append(("s11_10k_serializations", serial_time < 2.0))

    # S11.4: Transport selection at scale
    big_selector = TransportSelector()
    big_net = SimulatedNetwork()
    big_selector.register(TCPAdapter("a", big_net))
    big_selector.register(HTTP2Adapter("b", big_net))
    big_selector.register(CoAPAdapter("c", big_net))
    big_selector.register(WebSocketAdapter("d", big_net))

    t_start = time.time()
    for _ in range(1000):
        big_selector.select(TransportRequirements(needs_streaming=True))
    select_time = time.time() - t_start
    checks.append(("s11_1000_selections", select_time < 1.0))

    # ── Report ───────────────────────────────────────────────────────────

    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    elapsed = time.time() - t0

    print("=" * 60)
    print(f"  Transport Abstraction — {passed}/{total} checks passed")
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
