"""
Protocol Conformance & Interop Testing — Session 22 Track 1
============================================================
Validates deployment profiles, wire format cross-checking, handshake
state machines, cipher suite negotiation, and cross-implementation
conformance for Web4 protocols.

Sections:
  S1:  Deployment Profiles (Edge/Cloud/P2P/Blockchain)
  S2:  Wire Format Validation
  S3:  Handshake State Machine
  S4:  Cipher Suite Negotiation
  S5:  Extension Registry
  S6:  Cross-Implementation Conformance
  S7:  Error Code Registry
  S8:  Version Negotiation
  S9:  Protocol Feature Gates
  S10: Conformance Report Generation
  S11: Performance
"""

from __future__ import annotations
import dataclasses
import enum
import hashlib
import hmac
import json
import secrets
import struct
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ── S1: Deployment Profiles ────────────────────────────────────────────

class DeploymentProfile(enum.Enum):
    EDGE = "edge"
    CLOUD = "cloud"
    P2P = "p2p"
    BLOCKCHAIN = "blockchain"


class TransportProto(enum.Enum):
    TCP = "tcp"
    HTTP2 = "http2"
    WEBSOCKET = "websocket"
    COAP = "coap"
    QUIC = "quic"


class AuthMethod(enum.Enum):
    MUTUAL_TLS = "mutual_tls"
    TOKEN_BEARER = "token_bearer"
    HMAC_SIGNED = "hmac_signed"
    PSK = "pre_shared_key"
    NONE = "none"


class DataFormat(enum.Enum):
    JSON = "json"
    CBOR = "cbor"
    PROTOBUF = "protobuf"
    MSGPACK = "msgpack"


class CryptoSuite(enum.Enum):
    W4_BASE_1 = "W4-BASE-1"       # AES-256-GCM + ECDSA-P256 + SHA-256
    W4_FIPS_1 = "W4-FIPS-1"       # AES-256-GCM + ECDSA-P384 + SHA-384
    W4_IOT_1 = "W4-IOT-1"         # ChaCha20-Poly1305 + Ed25519 + SHA-256
    W4_QUANTUM_1 = "W4-QUANTUM-1" # Kyber-1024 + Dilithium5 + SHA-3-256


@dataclass
class ProfileSpec:
    profile: DeploymentProfile
    required_transports: List[TransportProto]
    optional_transports: List[TransportProto]
    auth_methods: List[AuthMethod]
    data_formats: List[DataFormat]
    crypto_suites: List[CryptoSuite]
    min_key_bits: int
    mutual_auth_required: bool
    max_message_size: int
    keepalive_interval_s: int
    max_concurrent_streams: int


PROFILE_SPECS: Dict[DeploymentProfile, ProfileSpec] = {
    DeploymentProfile.EDGE: ProfileSpec(
        profile=DeploymentProfile.EDGE,
        required_transports=[TransportProto.COAP],
        optional_transports=[TransportProto.TCP],
        auth_methods=[AuthMethod.PSK, AuthMethod.HMAC_SIGNED],
        data_formats=[DataFormat.CBOR],
        crypto_suites=[CryptoSuite.W4_IOT_1],
        min_key_bits=128,
        mutual_auth_required=False,
        max_message_size=1024,
        keepalive_interval_s=60,
        max_concurrent_streams=4,
    ),
    DeploymentProfile.CLOUD: ProfileSpec(
        profile=DeploymentProfile.CLOUD,
        required_transports=[TransportProto.HTTP2],
        optional_transports=[TransportProto.QUIC, TransportProto.WEBSOCKET],
        auth_methods=[AuthMethod.MUTUAL_TLS, AuthMethod.TOKEN_BEARER],
        data_formats=[DataFormat.JSON, DataFormat.PROTOBUF],
        crypto_suites=[CryptoSuite.W4_BASE_1, CryptoSuite.W4_FIPS_1],
        min_key_bits=256,
        mutual_auth_required=True,
        max_message_size=16 * 1024 * 1024,
        keepalive_interval_s=30,
        max_concurrent_streams=100,
    ),
    DeploymentProfile.P2P: ProfileSpec(
        profile=DeploymentProfile.P2P,
        required_transports=[TransportProto.WEBSOCKET],
        optional_transports=[TransportProto.QUIC, TransportProto.TCP],
        auth_methods=[AuthMethod.MUTUAL_TLS, AuthMethod.HMAC_SIGNED],
        data_formats=[DataFormat.CBOR, DataFormat.MSGPACK],
        crypto_suites=[CryptoSuite.W4_BASE_1, CryptoSuite.W4_IOT_1],
        min_key_bits=256,
        mutual_auth_required=True,
        max_message_size=1024 * 1024,
        keepalive_interval_s=15,
        max_concurrent_streams=32,
    ),
    DeploymentProfile.BLOCKCHAIN: ProfileSpec(
        profile=DeploymentProfile.BLOCKCHAIN,
        required_transports=[TransportProto.TCP],
        optional_transports=[TransportProto.HTTP2],
        auth_methods=[AuthMethod.MUTUAL_TLS],
        data_formats=[DataFormat.CBOR, DataFormat.JSON],
        crypto_suites=[CryptoSuite.W4_BASE_1, CryptoSuite.W4_FIPS_1, CryptoSuite.W4_QUANTUM_1],
        min_key_bits=256,
        mutual_auth_required=True,
        max_message_size=4 * 1024 * 1024,
        keepalive_interval_s=10,
        max_concurrent_streams=16,
    ),
}


class ProfileValidator:
    """Validates a node configuration against a deployment profile."""

    @staticmethod
    def validate(spec: ProfileSpec, node_config: Dict[str, Any]) -> List[str]:
        errors = []
        node_transports = set(node_config.get("transports", []))
        for req in spec.required_transports:
            if req.value not in node_transports:
                errors.append(f"Missing required transport: {req.value}")

        node_auth = set(node_config.get("auth_methods", []))
        if not node_auth.intersection({a.value for a in spec.auth_methods}):
            errors.append("No supported auth method configured")

        node_formats = set(node_config.get("data_formats", []))
        if not node_formats.intersection({f.value for f in spec.data_formats}):
            errors.append("No supported data format configured")

        node_suite = node_config.get("crypto_suite", "")
        valid_suites = {s.value for s in spec.crypto_suites}
        if node_suite not in valid_suites:
            errors.append(f"Unsupported crypto suite: {node_suite}")

        key_bits = node_config.get("key_bits", 0)
        if key_bits < spec.min_key_bits:
            errors.append(f"Key bits {key_bits} < minimum {spec.min_key_bits}")

        if spec.mutual_auth_required and not node_config.get("mutual_auth", False):
            errors.append("Mutual authentication required but not enabled")

        msg_size = node_config.get("max_message_size", 0)
        if msg_size > spec.max_message_size:
            errors.append(f"Message size {msg_size} > max {spec.max_message_size}")

        return errors


# ── S2: Wire Format Validation ─────────────────────────────────────────

class MessageType(enum.IntEnum):
    HANDSHAKE_INIT = 0x01
    HANDSHAKE_RESP = 0x02
    HANDSHAKE_FINISH = 0x03
    DATA = 0x10
    ACK = 0x11
    ERROR = 0x20
    PING = 0x30
    PONG = 0x31
    CLOSE = 0x40


# Wire header: version(1) + type(1) + flags(2) + seq(4) + length(4) + trace_id(16) = 28 bytes
WIRE_HEADER_FORMAT = '!BBHII16s'
WIRE_HEADER_SIZE = struct.calcsize(WIRE_HEADER_FORMAT)  # 28

WIRE_VERSION = 1
FLAG_ENCRYPTED = 0x0001
FLAG_COMPRESSED = 0x0002
FLAG_FRAGMENTED = 0x0004
FLAG_FINAL = 0x0008


@dataclass
class WireMessage:
    version: int
    msg_type: MessageType
    flags: int
    sequence: int
    payload: bytes
    trace_id: bytes = field(default_factory=lambda: secrets.token_bytes(16))

    def serialize(self) -> bytes:
        header = struct.pack(
            WIRE_HEADER_FORMAT,
            self.version, self.msg_type.value, self.flags,
            self.sequence, len(self.payload), self.trace_id
        )
        return header + self.payload

    @staticmethod
    def deserialize(data: bytes) -> WireMessage:
        if len(data) < WIRE_HEADER_SIZE:
            raise ValueError(f"Short header: {len(data)} < {WIRE_HEADER_SIZE}")
        ver, mtype, flags, seq, length, trace_id = struct.unpack(
            WIRE_HEADER_FORMAT, data[:WIRE_HEADER_SIZE]
        )
        payload = data[WIRE_HEADER_SIZE:WIRE_HEADER_SIZE + length]
        if len(payload) != length:
            raise ValueError(f"Payload truncated: {len(payload)} != {length}")
        return WireMessage(ver, MessageType(mtype), flags, seq, payload, trace_id)


class WireFormatValidator:
    """Validates wire format messages for conformance."""

    VALID_VERSIONS = {1}
    MAX_PAYLOAD_SIZE = 16 * 1024 * 1024  # 16 MB

    @staticmethod
    def validate(data: bytes) -> List[str]:
        errors = []
        if len(data) < WIRE_HEADER_SIZE:
            errors.append(f"Message too short: {len(data)} < {WIRE_HEADER_SIZE}")
            return errors

        ver, mtype, flags, seq, length, trace_id = struct.unpack(
            WIRE_HEADER_FORMAT, data[:WIRE_HEADER_SIZE]
        )

        if ver not in WireFormatValidator.VALID_VERSIONS:
            errors.append(f"Unknown version: {ver}")

        valid_types = {t.value for t in MessageType}
        if mtype not in valid_types:
            errors.append(f"Unknown message type: 0x{mtype:02x}")

        known_flags = FLAG_ENCRYPTED | FLAG_COMPRESSED | FLAG_FRAGMENTED | FLAG_FINAL
        if flags & ~known_flags:
            errors.append(f"Unknown flags: 0x{flags & ~known_flags:04x}")

        if length > WireFormatValidator.MAX_PAYLOAD_SIZE:
            errors.append(f"Payload too large: {length}")

        actual_payload = len(data) - WIRE_HEADER_SIZE
        if actual_payload < length:
            errors.append(f"Payload truncated: {actual_payload} < {length}")

        if trace_id == b'\x00' * 16:
            errors.append("Trace ID is all zeros")

        return errors


# ── S3: Handshake State Machine ────────────────────────────────────────

class HandshakeState(enum.Enum):
    IDLE = "idle"
    INIT_SENT = "init_sent"
    INIT_RECEIVED = "init_received"
    RESP_SENT = "resp_sent"
    RESP_RECEIVED = "resp_received"
    ESTABLISHED = "established"
    FAILED = "failed"
    CLOSED = "closed"


@dataclass
class HandshakeContext:
    state: HandshakeState = HandshakeState.IDLE
    role: str = "initiator"  # "initiator" or "responder"
    local_nonce: bytes = field(default_factory=lambda: secrets.token_bytes(32))
    remote_nonce: Optional[bytes] = None
    negotiated_suite: Optional[CryptoSuite] = None
    negotiated_version: int = 0
    session_key: Optional[bytes] = None
    error: Optional[str] = None
    events: List[Tuple[str, HandshakeState, HandshakeState]] = field(default_factory=list)

    def _transition(self, event: str, target: HandshakeState):
        old = self.state
        self.state = target
        self.events.append((event, old, target))


HANDSHAKE_TRANSITIONS: Dict[Tuple[str, HandshakeState], HandshakeState] = {
    ("initiator", HandshakeState.IDLE): HandshakeState.INIT_SENT,
    ("initiator", HandshakeState.RESP_RECEIVED): HandshakeState.ESTABLISHED,
    ("responder", HandshakeState.IDLE): HandshakeState.INIT_RECEIVED,
    ("responder", HandshakeState.INIT_RECEIVED): HandshakeState.RESP_SENT,
    ("responder", HandshakeState.RESP_SENT): HandshakeState.ESTABLISHED,
}


class HandshakeProtocol:
    """Three-phase handshake: INIT → RESP → FINISH."""

    def __init__(self, supported_suites: List[CryptoSuite], version: int = 1):
        self.supported_suites = supported_suites
        self.version = version

    def create_init(self, ctx: HandshakeContext) -> Dict[str, Any]:
        if ctx.state != HandshakeState.IDLE:
            ctx.error = f"Cannot init from state {ctx.state.value}"
            ctx._transition("init_error", HandshakeState.FAILED)
            return {}
        msg = {
            "type": "handshake_init",
            "version": self.version,
            "suites": [s.value for s in self.supported_suites],
            "nonce": ctx.local_nonce.hex(),
        }
        ctx._transition("send_init", HandshakeState.INIT_SENT)
        return msg

    def receive_init(self, ctx: HandshakeContext,
                     msg: Dict[str, Any]) -> Dict[str, Any]:
        if ctx.state != HandshakeState.IDLE:
            ctx.error = f"Cannot receive init in state {ctx.state.value}"
            ctx._transition("recv_init_error", HandshakeState.FAILED)
            return {}

        ctx.role = "responder"
        ctx._transition("recv_init", HandshakeState.INIT_RECEIVED)
        ctx.remote_nonce = bytes.fromhex(msg["nonce"])
        remote_version = msg.get("version", 1)
        ctx.negotiated_version = min(self.version, remote_version)

        remote_suites = set(msg.get("suites", []))
        local_suites = [s.value for s in self.supported_suites]
        common = [s for s in local_suites if s in remote_suites]
        if not common:
            ctx.error = "No common cipher suite"
            ctx._transition("no_common_suite", HandshakeState.FAILED)
            return {"type": "handshake_error", "error": "no_common_suite"}

        ctx.negotiated_suite = CryptoSuite(common[0])
        resp = {
            "type": "handshake_resp",
            "version": ctx.negotiated_version,
            "suite": ctx.negotiated_suite.value,
            "nonce": ctx.local_nonce.hex(),
        }
        ctx._transition("send_resp", HandshakeState.RESP_SENT)
        return resp

    def receive_resp(self, ctx: HandshakeContext,
                     msg: Dict[str, Any]) -> Dict[str, Any]:
        if ctx.state != HandshakeState.INIT_SENT:
            ctx.error = f"Cannot receive resp in state {ctx.state.value}"
            ctx._transition("recv_resp_error", HandshakeState.FAILED)
            return {}

        ctx.remote_nonce = bytes.fromhex(msg["nonce"])
        ctx.negotiated_suite = CryptoSuite(msg["suite"])
        ctx.negotiated_version = msg["version"]
        ctx._transition("recv_resp", HandshakeState.RESP_RECEIVED)

        # Derive session key
        key_material = ctx.local_nonce + ctx.remote_nonce
        ctx.session_key = hashlib.sha256(key_material).digest()

        finish = {
            "type": "handshake_finish",
            "verify": hmac.new(ctx.session_key, b"handshake_verify",
                               hashlib.sha256).hexdigest(),
        }
        ctx._transition("send_finish", HandshakeState.ESTABLISHED)
        return finish

    def receive_finish(self, ctx: HandshakeContext,
                       msg: Dict[str, Any]) -> bool:
        if ctx.state != HandshakeState.RESP_SENT:
            ctx.error = f"Cannot receive finish in state {ctx.state.value}"
            ctx._transition("recv_finish_error", HandshakeState.FAILED)
            return False

        key_material = ctx.remote_nonce + ctx.local_nonce
        ctx.session_key = hashlib.sha256(key_material).digest()

        expected = hmac.new(ctx.session_key, b"handshake_verify",
                            hashlib.sha256).hexdigest()
        if not hmac.compare_digest(msg.get("verify", ""), expected):
            ctx.error = "Verify mismatch"
            ctx._transition("verify_fail", HandshakeState.FAILED)
            return False

        ctx._transition("recv_finish", HandshakeState.ESTABLISHED)
        return True


# ── S4: Cipher Suite Negotiation ───────────────────────────────────────

@dataclass
class CipherSuiteSpec:
    name: str
    key_exchange: str
    signature: str
    cipher: str
    hash_alg: str
    key_bits: int
    security_level: int  # 1=basic, 2=standard, 3=high, 4=post-quantum


CIPHER_SUITE_SPECS: Dict[CryptoSuite, CipherSuiteSpec] = {
    CryptoSuite.W4_BASE_1: CipherSuiteSpec(
        "W4-BASE-1", "ECDH-P256", "ECDSA-P256", "AES-256-GCM", "SHA-256",
        256, 2
    ),
    CryptoSuite.W4_FIPS_1: CipherSuiteSpec(
        "W4-FIPS-1", "ECDH-P384", "ECDSA-P384", "AES-256-GCM", "SHA-384",
        384, 3
    ),
    CryptoSuite.W4_IOT_1: CipherSuiteSpec(
        "W4-IOT-1", "X25519", "Ed25519", "ChaCha20-Poly1305", "SHA-256",
        256, 2
    ),
    CryptoSuite.W4_QUANTUM_1: CipherSuiteSpec(
        "W4-QUANTUM-1", "Kyber-1024", "Dilithium5", "AES-256-GCM", "SHA3-256",
        512, 4
    ),
}


class SuiteNegotiator:
    """Negotiate highest common cipher suite between two parties."""

    @staticmethod
    def negotiate(
        client_suites: List[CryptoSuite],
        server_suites: List[CryptoSuite],
        min_security_level: int = 1,
    ) -> Optional[CryptoSuite]:
        # Client preference order, filtered by server support
        for suite in client_suites:
            if suite in server_suites:
                spec = CIPHER_SUITE_SPECS[suite]
                if spec.security_level >= min_security_level:
                    return suite
        return None

    @staticmethod
    def downgrade_check(
        negotiated: CryptoSuite,
        initiator_best: CryptoSuite,
    ) -> bool:
        """Returns True if negotiated is a downgrade from initiator's best."""
        neg_level = CIPHER_SUITE_SPECS[negotiated].security_level
        best_level = CIPHER_SUITE_SPECS[initiator_best].security_level
        return neg_level < best_level


# ── S5: Extension Registry ────────────────────────────────────────────

@dataclass
class ProtocolExtension:
    ext_id: int
    name: str
    required: bool
    data: bytes = b""
    is_grease: bool = False


class ExtensionRegistry:
    """IANA-style extension registry for protocol negotiation."""

    # Reserved ranges
    GREASE_IDS = {0x0A0A, 0x1A1A, 0x2A2A, 0x3A3A, 0x4A4A}
    RESERVED_MAX = 0x00FF
    PRIVATE_MIN = 0xFF00

    def __init__(self):
        self.registered: Dict[int, ProtocolExtension] = {}
        self._next_id = 0x0100  # First assignable ID

    def register(self, name: str, required: bool = False,
                 ext_id: Optional[int] = None) -> ProtocolExtension:
        if ext_id is None:
            ext_id = self._next_id
            self._next_id += 1
        elif ext_id in self.registered:
            raise ValueError(f"Extension ID 0x{ext_id:04x} already registered")

        ext = ProtocolExtension(ext_id, name, required)
        self.registered[ext_id] = ext
        return ext

    def validate_extensions(self, ext_list: List[ProtocolExtension]) -> List[str]:
        errors = []
        seen_ids: Set[int] = set()
        grease_count = 0
        total_count = len(ext_list)

        for ext in ext_list:
            if ext.ext_id in seen_ids:
                errors.append(f"Duplicate extension ID: 0x{ext.ext_id:04x}")
            seen_ids.add(ext.ext_id)

            if ext.ext_id in self.GREASE_IDS:
                grease_count += 1
                ext.is_grease = True

        if total_count > 20:
            errors.append(f"Too many extensions: {total_count} > 20")
        if grease_count > 5:
            errors.append(f"Too many GREASE extensions: {grease_count} > 5")
        if total_count > 0 and grease_count == 0:
            errors.append("At least 1 GREASE extension required")

        # Check required extensions present
        for ext_id, reg_ext in self.registered.items():
            if reg_ext.required and ext_id not in seen_ids:
                errors.append(f"Missing required extension: {reg_ext.name}")

        return errors

    def negotiate_extensions(
        self,
        client_exts: List[ProtocolExtension],
        server_exts: List[ProtocolExtension],
    ) -> List[ProtocolExtension]:
        """Return extensions supported by both sides (excluding GREASE)."""
        client_ids = {e.ext_id for e in client_exts if not e.is_grease and e.ext_id not in self.GREASE_IDS}
        result = []
        for ext in server_exts:
            if ext.ext_id in self.GREASE_IDS:
                continue
            if ext.ext_id in client_ids:
                result.append(ext)
        return result


# ── S6: Cross-Implementation Conformance ──────────────────────────────

@dataclass
class TestVector:
    name: str
    input_data: bytes
    expected_output: bytes
    suite: CryptoSuite
    operation: str  # "serialize", "hash", "sign", "encrypt"


class ConformanceEngine:
    """Validates cross-implementation conformance via test vectors."""

    def __init__(self):
        self.vectors: List[TestVector] = []
        self.results: Dict[str, Dict[str, bool]] = {}  # impl → vector → pass

    def add_vector(self, vector: TestVector):
        self.vectors.append(vector)

    def run_impl(self, impl_name: str,
                 processor: Any) -> Dict[str, bool]:
        results = {}
        for vec in self.vectors:
            try:
                output = processor(vec.input_data, vec.suite, vec.operation)
                results[vec.name] = (output == vec.expected_output)
            except Exception:
                results[vec.name] = False
        self.results[impl_name] = results
        return results

    def cross_check(self) -> Dict[str, List[str]]:
        """Find vectors where implementations disagree."""
        disagreements: Dict[str, List[str]] = {}
        for vec in self.vectors:
            impl_results = []
            for impl_name, results in self.results.items():
                impl_results.append((impl_name, results.get(vec.name, False)))
            values = {r for _, r in impl_results}
            if len(values) > 1:
                failing = [name for name, r in impl_results if not r]
                disagreements[vec.name] = failing
        return disagreements

    def coverage_matrix(self) -> Dict[str, float]:
        """Per-implementation pass rate."""
        coverage = {}
        for impl_name, results in self.results.items():
            if results:
                coverage[impl_name] = sum(1 for v in results.values() if v) / len(results)
            else:
                coverage[impl_name] = 0.0
        return coverage


# ── S7: Error Code Registry ──────────────────────────────────────────

class ErrorCategory(enum.Enum):
    TRANSPORT = "transport"
    HANDSHAKE = "handshake"
    AUTH = "authentication"
    PROTOCOL = "protocol"
    RESOURCE = "resource"
    TRUST = "trust"


@dataclass
class ErrorCode:
    code: int
    category: ErrorCategory
    name: str
    description: str
    retryable: bool
    severity: int  # 1=info, 2=warning, 3=error, 4=fatal


class ErrorRegistry:
    """Standardized error codes for all protocol layers."""

    def __init__(self):
        self.codes: Dict[int, ErrorCode] = {}

    def register(self, code: int, category: ErrorCategory, name: str,
                 description: str, retryable: bool = False, severity: int = 3):
        self.codes[code] = ErrorCode(code, category, name, description,
                                     retryable, severity)

    def lookup(self, code: int) -> Optional[ErrorCode]:
        return self.codes.get(code)

    def by_category(self, category: ErrorCategory) -> List[ErrorCode]:
        return [c for c in self.codes.values() if c.category == category]

    def retryable_codes(self) -> List[int]:
        return [c.code for c in self.codes.values() if c.retryable]


def build_standard_errors() -> ErrorRegistry:
    reg = ErrorRegistry()
    # Transport errors (1xx)
    reg.register(100, ErrorCategory.TRANSPORT, "CONNECTION_REFUSED",
                 "Remote endpoint refused connection", True, 3)
    reg.register(101, ErrorCategory.TRANSPORT, "TIMEOUT",
                 "Connection or operation timed out", True, 3)
    reg.register(102, ErrorCategory.TRANSPORT, "MESSAGE_TOO_LARGE",
                 "Message exceeds maximum size", False, 3)
    # Handshake errors (2xx)
    reg.register(200, ErrorCategory.HANDSHAKE, "VERSION_MISMATCH",
                 "No common protocol version", False, 4)
    reg.register(201, ErrorCategory.HANDSHAKE, "NO_COMMON_SUITE",
                 "No common cipher suite", False, 4)
    reg.register(202, ErrorCategory.HANDSHAKE, "VERIFY_FAILED",
                 "Handshake verification failed", False, 4)
    reg.register(203, ErrorCategory.HANDSHAKE, "DOWNGRADE_DETECTED",
                 "Cipher suite downgrade attack detected", False, 4)
    # Auth errors (3xx)
    reg.register(300, ErrorCategory.AUTH, "AUTH_REQUIRED",
                 "Authentication required", False, 3)
    reg.register(301, ErrorCategory.AUTH, "AUTH_FAILED",
                 "Authentication credentials invalid", False, 4)
    reg.register(302, ErrorCategory.AUTH, "CERT_EXPIRED",
                 "Certificate has expired", False, 3)
    # Protocol errors (4xx)
    reg.register(400, ErrorCategory.PROTOCOL, "INVALID_MESSAGE",
                 "Message format is invalid", False, 3)
    reg.register(401, ErrorCategory.PROTOCOL, "SEQUENCE_GAP",
                 "Message sequence number gap detected", True, 2)
    reg.register(402, ErrorCategory.PROTOCOL, "DUPLICATE_MESSAGE",
                 "Duplicate message received", False, 1)
    # Resource errors (5xx)
    reg.register(500, ErrorCategory.RESOURCE, "RATE_LIMITED",
                 "Request rate limit exceeded", True, 2)
    reg.register(501, ErrorCategory.RESOURCE, "ATP_INSUFFICIENT",
                 "Insufficient ATP balance", False, 3)
    # Trust errors (6xx)
    reg.register(600, ErrorCategory.TRUST, "TRUST_TOO_LOW",
                 "Trust score below minimum threshold", False, 3)
    reg.register(601, ErrorCategory.TRUST, "ENTITY_REVOKED",
                 "Entity has been revoked", False, 4)
    reg.register(602, ErrorCategory.TRUST, "WITNESS_REQUIRED",
                 "Witness attestation required for this operation", False, 3)
    return reg


# ── S8: Version Negotiation ──────────────────────────────────────────

@dataclass
class VersionRange:
    min_version: int
    max_version: int
    preferred: int

    def supports(self, version: int) -> bool:
        return self.min_version <= version <= self.max_version


class VersionNegotiator:
    """Negotiate protocol version between client and server."""

    @staticmethod
    def negotiate(client: VersionRange, server: VersionRange) -> Optional[int]:
        overlap_min = max(client.min_version, server.min_version)
        overlap_max = min(client.max_version, server.max_version)
        if overlap_min > overlap_max:
            return None
        # Prefer highest common version
        return overlap_max

    @staticmethod
    def is_compatible(v1: int, v2: int) -> bool:
        """Major version must match for compatibility."""
        return v1 // 100 == v2 // 100  # e.g., 100-199 compatible


# ── S9: Protocol Feature Gates ────────────────────────────────────────

class FeatureGate(enum.Enum):
    COMPRESSION = "compression"
    FRAGMENTATION = "fragmentation"
    MULTIPLEXING = "multiplexing"
    PRIORITY_QUEUES = "priority_queues"
    BACKPRESSURE = "backpressure"
    ZERO_RTT = "zero_rtt"
    SESSION_RESUMPTION = "session_resumption"
    CERTIFICATE_PINNING = "cert_pinning"


@dataclass
class FeatureCapabilities:
    enabled: Set[FeatureGate] = field(default_factory=set)
    version_required: Dict[FeatureGate, int] = field(default_factory=dict)

    def is_available(self, feature: FeatureGate, current_version: int) -> bool:
        if feature not in self.enabled:
            return False
        min_ver = self.version_required.get(feature, 1)
        return current_version >= min_ver

    def negotiate_features(
        self, remote: FeatureCapabilities, version: int
    ) -> Set[FeatureGate]:
        common = self.enabled & remote.enabled
        return {f for f in common if self.is_available(f, version)
                and remote.is_available(f, version)}


# ── S10: Conformance Report Generation ────────────────────────────────

@dataclass
class ConformanceResult:
    test_name: str
    passed: bool
    details: str = ""
    category: str = ""


@dataclass
class ConformanceReport:
    implementation: str
    profile: DeploymentProfile
    timestamp: float = field(default_factory=time.time)
    results: List[ConformanceResult] = field(default_factory=list)

    def pass_rate(self) -> float:
        if not self.results:
            return 0.0
        return sum(1 for r in self.results if r.passed) / len(self.results)

    def by_category(self) -> Dict[str, Tuple[int, int]]:
        cats: Dict[str, Tuple[int, int]] = {}
        for r in self.results:
            p, t = cats.get(r.category, (0, 0))
            cats[r.category] = (p + (1 if r.passed else 0), t + 1)
        return cats

    def to_json(self) -> str:
        return json.dumps({
            "implementation": self.implementation,
            "profile": self.profile.value,
            "timestamp": self.timestamp,
            "pass_rate": self.pass_rate(),
            "results": [
                {"test": r.test_name, "passed": r.passed,
                 "details": r.details, "category": r.category}
                for r in self.results
            ],
            "categories": {k: {"passed": v[0], "total": v[1]}
                           for k, v in self.by_category().items()},
        }, indent=2)


class ConformanceReportGenerator:
    """Generate conformance reports for a given implementation against a profile."""

    def __init__(self, profile: DeploymentProfile):
        self.profile = profile
        self.spec = PROFILE_SPECS[profile]

    def run_suite(self, node_config: Dict[str, Any],
                  impl_name: str = "default") -> ConformanceReport:
        report = ConformanceReport(impl_name, self.profile)

        # Profile validation
        errors = ProfileValidator.validate(self.spec, node_config)
        report.results.append(ConformanceResult(
            "profile_compliance", len(errors) == 0,
            "; ".join(errors) if errors else "All checks passed",
            "profile"
        ))

        # Transport checks
        node_transports = set(node_config.get("transports", []))
        for req in self.spec.required_transports:
            report.results.append(ConformanceResult(
                f"transport_{req.value}",
                req.value in node_transports,
                category="transport"
            ))

        # Crypto suite check
        node_suite = node_config.get("crypto_suite", "")
        valid = node_suite in {s.value for s in self.spec.crypto_suites}
        report.results.append(ConformanceResult(
            "crypto_suite", valid,
            f"Suite: {node_suite}", "crypto"
        ))

        # Auth check
        node_auth = set(node_config.get("auth_methods", []))
        valid_auth = node_auth.intersection({a.value for a in self.spec.auth_methods})
        report.results.append(ConformanceResult(
            "auth_method", len(valid_auth) > 0,
            f"Common methods: {valid_auth}", "auth"
        ))

        # Mutual auth
        if self.spec.mutual_auth_required:
            report.results.append(ConformanceResult(
                "mutual_auth", node_config.get("mutual_auth", False),
                category="auth"
            ))

        # Key bits
        key_bits = node_config.get("key_bits", 0)
        report.results.append(ConformanceResult(
            "key_strength", key_bits >= self.spec.min_key_bits,
            f"{key_bits} bits (min {self.spec.min_key_bits})", "crypto"
        ))

        return report


# ── S11: Performance ──────────────────────────────────────────────────

def run_checks():
    checks: List[Tuple[str, bool]] = []

    # ── S1: Deployment Profiles ───────────────────────────────────────
    # Valid edge config
    edge_config = {
        "transports": ["coap", "tcp"],
        "auth_methods": ["pre_shared_key"],
        "data_formats": ["cbor"],
        "crypto_suite": "W4-IOT-1",
        "key_bits": 256,
        "mutual_auth": False,
        "max_message_size": 512,
    }
    edge_errors = ProfileValidator.validate(PROFILE_SPECS[DeploymentProfile.EDGE], edge_config)
    checks.append(("s1_edge_valid", len(edge_errors) == 0))

    # Invalid edge config (wrong suite)
    bad_edge = {**edge_config, "crypto_suite": "W4-FIPS-1"}
    bad_errors = ProfileValidator.validate(PROFILE_SPECS[DeploymentProfile.EDGE], bad_edge)
    checks.append(("s1_edge_bad_suite", any("Unsupported crypto suite" in e for e in bad_errors)))

    # Cloud config requires mutual auth
    cloud_config = {
        "transports": ["http2"],
        "auth_methods": ["mutual_tls"],
        "data_formats": ["json"],
        "crypto_suite": "W4-BASE-1",
        "key_bits": 256,
        "mutual_auth": True,
        "max_message_size": 1024 * 1024,
    }
    cloud_errors = ProfileValidator.validate(PROFILE_SPECS[DeploymentProfile.CLOUD], cloud_config)
    checks.append(("s1_cloud_valid", len(cloud_errors) == 0))

    # Cloud without mutual auth
    no_mutual = {**cloud_config, "mutual_auth": False}
    no_mutual_errors = ProfileValidator.validate(PROFILE_SPECS[DeploymentProfile.CLOUD], no_mutual)
    checks.append(("s1_cloud_needs_mutual", any("Mutual" in e for e in no_mutual_errors)))

    # All 4 profiles exist
    checks.append(("s1_all_profiles", len(PROFILE_SPECS) == 4))

    # ── S2: Wire Format Validation ────────────────────────────────────
    msg = WireMessage(
        version=1, msg_type=MessageType.DATA, flags=FLAG_ENCRYPTED,
        sequence=42, payload=b"hello web4"
    )
    serialized = msg.serialize()
    checks.append(("s2_header_size", WIRE_HEADER_SIZE == 28))
    checks.append(("s2_roundtrip", WireMessage.deserialize(serialized).payload == b"hello web4"))
    checks.append(("s2_sequence", WireMessage.deserialize(serialized).sequence == 42))

    # Valid message
    errors = WireFormatValidator.validate(serialized)
    checks.append(("s2_valid_msg", len(errors) == 0))

    # Short message
    short_errors = WireFormatValidator.validate(b"\x00" * 10)
    checks.append(("s2_short_msg", any("too short" in e for e in short_errors)))

    # Bad version
    bad_ver = struct.pack(WIRE_HEADER_FORMAT, 99, 0x10, 0, 1, 0,
                          secrets.token_bytes(16))
    bad_ver_errors = WireFormatValidator.validate(bad_ver)
    checks.append(("s2_bad_version", any("Unknown version" in e for e in bad_ver_errors)))

    # ── S3: Handshake State Machine ───────────────────────────────────
    proto = HandshakeProtocol(
        [CryptoSuite.W4_BASE_1, CryptoSuite.W4_IOT_1]
    )
    initiator = HandshakeContext(role="initiator")
    responder = HandshakeContext(role="responder")

    init_msg = proto.create_init(initiator)
    checks.append(("s3_init_sent", initiator.state == HandshakeState.INIT_SENT))
    checks.append(("s3_init_has_suites", "suites" in init_msg))

    resp_msg = proto.receive_init(responder, init_msg)
    checks.append(("s3_resp_sent", responder.state == HandshakeState.RESP_SENT))
    checks.append(("s3_suite_negotiated", responder.negotiated_suite is not None))

    finish_msg = proto.receive_resp(initiator, resp_msg)
    checks.append(("s3_established_init", initiator.state == HandshakeState.ESTABLISHED))
    checks.append(("s3_session_key_init", initiator.session_key is not None))

    ok = proto.receive_finish(responder, finish_msg)
    checks.append(("s3_established_resp", responder.state == HandshakeState.ESTABLISHED))
    checks.append(("s3_verify_ok", ok))
    checks.append(("s3_session_key_resp", responder.session_key is not None))

    # Keys derived from same nonces should match
    checks.append(("s3_keys_match", initiator.session_key == responder.session_key))

    # No common suite → fail
    proto_iot = HandshakeProtocol([CryptoSuite.W4_IOT_1])
    proto_fips = HandshakeProtocol([CryptoSuite.W4_FIPS_1])
    init_ctx = HandshakeContext(role="initiator")
    resp_ctx = HandshakeContext(role="responder")
    init_m = proto_iot.create_init(init_ctx)
    fail_resp = proto_fips.receive_init(resp_ctx, init_m)
    checks.append(("s3_no_common_fail", resp_ctx.state == HandshakeState.FAILED))

    # ── S4: Cipher Suite Negotiation ──────────────────────────────────
    result = SuiteNegotiator.negotiate(
        [CryptoSuite.W4_FIPS_1, CryptoSuite.W4_BASE_1],
        [CryptoSuite.W4_BASE_1, CryptoSuite.W4_IOT_1],
    )
    checks.append(("s4_negotiate_common", result == CryptoSuite.W4_BASE_1))

    # Min security level filter
    result_high = SuiteNegotiator.negotiate(
        [CryptoSuite.W4_IOT_1, CryptoSuite.W4_BASE_1],
        [CryptoSuite.W4_IOT_1, CryptoSuite.W4_BASE_1],
        min_security_level=3,
    )
    checks.append(("s4_min_level_filter", result_high is None))

    # Downgrade detection
    is_dg = SuiteNegotiator.downgrade_check(
        CryptoSuite.W4_IOT_1, CryptoSuite.W4_FIPS_1
    )
    checks.append(("s4_downgrade_detected", is_dg))

    no_dg = SuiteNegotiator.downgrade_check(
        CryptoSuite.W4_FIPS_1, CryptoSuite.W4_BASE_1
    )
    checks.append(("s4_no_downgrade", not no_dg))

    # All 4 suites have specs
    checks.append(("s4_all_specs", len(CIPHER_SUITE_SPECS) == 4))

    # ── S5: Extension Registry ────────────────────────────────────────
    registry = ExtensionRegistry()
    ext_comp = registry.register("compression", required=True)
    ext_frag = registry.register("fragmentation")
    checks.append(("s5_registered", len(registry.registered) == 2))

    # Valid extensions list (with GREASE)
    ext_list = [
        ext_comp, ext_frag,
        ProtocolExtension(0x0A0A, "grease1", False),
    ]
    ext_errors = registry.validate_extensions(ext_list)
    checks.append(("s5_valid_exts", len(ext_errors) == 0))

    # Missing required extension
    ext_only_grease = [ProtocolExtension(0x0A0A, "grease1", False)]
    missing_errors = registry.validate_extensions(ext_only_grease)
    checks.append(("s5_missing_required", any("Missing required" in e for e in missing_errors)))

    # No GREASE
    no_grease = [ext_comp, ext_frag]
    grease_errors = registry.validate_extensions(no_grease)
    checks.append(("s5_no_grease_error", any("GREASE" in e for e in grease_errors)))

    # Extension negotiation
    client_exts = [ext_comp, ext_frag, ProtocolExtension(0x0A0A, "grease", False)]
    server_exts = [ext_comp]
    negotiated_exts = registry.negotiate_extensions(client_exts, server_exts)
    checks.append(("s5_negotiate_common", len(negotiated_exts) == 1))
    checks.append(("s5_negotiate_name", negotiated_exts[0].name == "compression"))

    # ── S6: Cross-Implementation Conformance ──────────────────────────
    engine = ConformanceEngine()

    # Add test vectors
    tv1 = TestVector("hash_basic", b"web4 trust", hashlib.sha256(b"web4 trust").digest(),
                     CryptoSuite.W4_BASE_1, "hash")
    tv2 = TestVector("hash_empty", b"", hashlib.sha256(b"").digest(),
                     CryptoSuite.W4_BASE_1, "hash")
    engine.add_vector(tv1)
    engine.add_vector(tv2)

    # Python impl (correct)
    def py_processor(data, suite, op):
        if op == "hash":
            return hashlib.sha256(data).digest()
        return b""

    py_results = engine.run_impl("python", py_processor)
    checks.append(("s6_py_pass", all(py_results.values())))

    # Buggy impl (wrong hash)
    def buggy_processor(data, suite, op):
        if op == "hash":
            return hashlib.md5(data).digest()
        return b""

    buggy_results = engine.run_impl("buggy", buggy_processor)
    checks.append(("s6_buggy_fail", not all(buggy_results.values())))

    # Cross-check finds disagreement
    disagreements = engine.cross_check()
    checks.append(("s6_disagreement", len(disagreements) > 0))

    # Coverage matrix
    coverage = engine.coverage_matrix()
    checks.append(("s6_py_coverage", coverage["python"] == 1.0))
    checks.append(("s6_buggy_coverage", coverage["buggy"] == 0.0))

    # ── S7: Error Code Registry ───────────────────────────────────────
    err_reg = build_standard_errors()
    checks.append(("s7_error_count", len(err_reg.codes) >= 15))

    timeout_err = err_reg.lookup(101)
    checks.append(("s7_timeout_retryable", timeout_err is not None and timeout_err.retryable))

    auth_err = err_reg.lookup(301)
    checks.append(("s7_auth_fatal", auth_err is not None and auth_err.severity == 4))

    transport_errors = err_reg.by_category(ErrorCategory.TRANSPORT)
    checks.append(("s7_transport_count", len(transport_errors) >= 3))

    retryable = err_reg.retryable_codes()
    checks.append(("s7_retryable_exists", len(retryable) >= 3))

    # ── S8: Version Negotiation ───────────────────────────────────────
    client_ver = VersionRange(100, 103, 103)
    server_ver = VersionRange(101, 105, 105)
    negotiated_ver = VersionNegotiator.negotiate(client_ver, server_ver)
    checks.append(("s8_version_negotiated", negotiated_ver == 103))

    # No overlap
    no_overlap = VersionNegotiator.negotiate(
        VersionRange(100, 102, 102),
        VersionRange(103, 105, 105),
    )
    checks.append(("s8_no_overlap", no_overlap is None))

    # Compatibility
    checks.append(("s8_compatible", VersionNegotiator.is_compatible(100, 199)))
    checks.append(("s8_incompatible", not VersionNegotiator.is_compatible(100, 200)))

    # ── S9: Protocol Feature Gates ────────────────────────────────────
    local_features = FeatureCapabilities(
        enabled={FeatureGate.COMPRESSION, FeatureGate.MULTIPLEXING,
                 FeatureGate.ZERO_RTT},
        version_required={FeatureGate.ZERO_RTT: 102},
    )
    remote_features = FeatureCapabilities(
        enabled={FeatureGate.COMPRESSION, FeatureGate.FRAGMENTATION,
                 FeatureGate.ZERO_RTT},
        version_required={FeatureGate.ZERO_RTT: 102},
    )
    common_features = local_features.negotiate_features(remote_features, 102)
    checks.append(("s9_common_features", FeatureGate.COMPRESSION in common_features))
    checks.append(("s9_zero_rtt_ok", FeatureGate.ZERO_RTT in common_features))

    # Version too low for feature
    old_common = local_features.negotiate_features(remote_features, 100)
    checks.append(("s9_version_gate", FeatureGate.ZERO_RTT not in old_common))

    # ── S10: Conformance Report ───────────────────────────────────────
    gen = ConformanceReportGenerator(DeploymentProfile.CLOUD)
    report = gen.run_suite(cloud_config, "test_impl")
    checks.append(("s10_report_pass_rate", report.pass_rate() == 1.0))
    checks.append(("s10_report_json", "pass_rate" in report.to_json()))

    categories = report.by_category()
    checks.append(("s10_has_categories", len(categories) >= 3))

    # Failing report
    bad_report = gen.run_suite({"transports": [], "auth_methods": [], "data_formats": [],
                                "crypto_suite": "NONE", "key_bits": 0}, "bad_impl")
    checks.append(("s10_bad_report", bad_report.pass_rate() < 1.0))

    # ── S11: Performance ──────────────────────────────────────────────
    # 10K wire message serialize/deserialize
    t0 = time.time()
    for i in range(10000):
        m = WireMessage(1, MessageType.DATA, 0, i, b"perf" * 10)
        WireMessage.deserialize(m.serialize())
    dt = time.time() - t0
    checks.append(("s11_10k_wire", dt < 5.0))

    # 1K handshakes
    t0 = time.time()
    for _ in range(1000):
        p = HandshakeProtocol([CryptoSuite.W4_BASE_1])
        ic = HandshakeContext(role="initiator")
        rc = HandshakeContext(role="responder")
        im = p.create_init(ic)
        rm = p.receive_init(rc, im)
        fm = p.receive_resp(ic, rm)
        p.receive_finish(rc, fm)
    dt = time.time() - t0
    checks.append(("s11_1k_handshakes", dt < 5.0))

    # 1K profile validations
    t0 = time.time()
    for _ in range(1000):
        for profile in DeploymentProfile:
            ProfileValidator.validate(PROFILE_SPECS[profile], cloud_config)
    dt = time.time() - t0
    checks.append(("s11_4k_validations", dt < 3.0))

    # ── Report ────────────────────────────────────────────────────────
    passed = sum(1 for _, v in checks if v)
    total = len(checks)
    width = 60
    title = f"Protocol Conformance & Interop — {passed}/{total} checks passed"
    print("=" * width)
    print(f"  {title}")
    print("=" * width)
    for name, ok in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")
    dt_total = time.time() - t0
    print(f"\n  Time: {dt_total:.2f}s\n")
    return passed == total


if __name__ == "__main__":
    success = run_checks()
    raise SystemExit(0 if success else 1)
