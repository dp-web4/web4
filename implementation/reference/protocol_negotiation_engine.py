#!/usr/bin/env python3
"""
Web4 Protocol Negotiation Engine
=================================

Full implementation of the web4:// handshake lifecycle:

1. Discovery  — Find entities via witness relay, DNS-SD, QR OOB
2. Negotiation — Suite selection (W4-BASE-1/FIPS-1/IOT-1), transport, media type
3. Handshake  — ClientHello → ServerHello → ClientFinished → ServerFinished
4. Capability — Trust-gated capability advertisement with T3/V3 requirements
5. Session    — Encrypted session with rekey/rotation support
6. GREASE     — Forward-compatibility with unknown extensions

Spec references:
  - web4-standard/protocols/web4-handshake.md (§1-§13)
  - web4-standard/core-spec/core-protocol.md (§1-§5)
  - web4-standard/core-spec/mcp-protocol.md (§8: capabilities)

Date: 2026-02-27
"""

import hashlib
import json
import os
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, List, Any, Tuple, Set


# ═══════════════════════════════════════════════════════════════
# Cryptographic Suites (§3)
# ═══════════════════════════════════════════════════════════════

class CryptoSuite(str, Enum):
    """Web4 cryptographic suites per spec §3."""
    W4_BASE_1 = "W4-BASE-1"  # MUST: X25519 + Ed25519 + ChaCha20-Poly1305 + SHA-256 (COSE)
    W4_FIPS_1 = "W4-FIPS-1"  # SHOULD: P-256ECDH + ECDSA-P256 + AES-128-GCM + SHA-256 (JOSE)
    W4_IOT_1 = "W4-IOT-1"   # MAY: X25519 + Ed25519 + AES-CCM (CBOR compressed)


class MediaType(str, Enum):
    """Negotiated media types."""
    CBOR = "application/cbor"
    JSON = "application/json"
    JSON_LD = "application/ld+json"


class SignatureProfile(str, Enum):
    """Signature canonicalization profiles (§6.0)."""
    COSE = "cose"  # CBOR deterministic + Ed25519/EdDSA
    JOSE = "jose"  # JCS (RFC 8785) + ECDSA-P256


# Suite → default media/signature mappings
SUITE_PROFILES = {
    CryptoSuite.W4_BASE_1: (MediaType.CBOR, SignatureProfile.COSE),
    CryptoSuite.W4_FIPS_1: (MediaType.JSON, SignatureProfile.JOSE),
    CryptoSuite.W4_IOT_1: (MediaType.CBOR, SignatureProfile.COSE),
}


# ═══════════════════════════════════════════════════════════════
# Transport Layer (§4.1)
# ═══════════════════════════════════════════════════════════════

class TransportType(str, Enum):
    """Supported transport types with priority."""
    TLS_1_3 = "tls_1.3"           # MUST — universal baseline
    QUIC = "quic"                  # MUST — low latency
    WEB_TRANSPORT = "webtransport"  # SHOULD — browser P2P
    WEB_RTC = "webrtc"             # SHOULD — NAT traversal
    WEBSOCKET = "websocket"        # MAY — legacy browser
    BLE_GATT = "ble_gatt"         # MAY — IoT proximity
    CAN_BUS = "can_bus"           # MAY — automotive
    TCP_TLS = "tcp_tls"           # MAY — direct socket


@dataclass
class TransportEndpoint:
    """A transport endpoint with metadata."""
    transport: TransportType
    address: str           # e.g., "tls://node.web4.io:8443"
    priority: int = 0      # Higher = preferred
    constrained: bool = False  # BLE/CAN = constrained
    supports_full_metering: bool = True


# ═══════════════════════════════════════════════════════════════
# Discovery (§4.2)
# ═══════════════════════════════════════════════════════════════

class DiscoveryMethod(str, Enum):
    """Discovery mechanisms per §4.2."""
    WITNESS_RELAY = "witness_relay"  # MUST
    DNS_SD = "dns_sd"               # SHOULD
    QR_OOB = "qr_oob"              # SHOULD — out-of-band
    DNS_BOOTSTRAP = "dns_bootstrap"  # MAY
    DHT_LOOKUP = "dht_lookup"       # MAY
    BROADCAST = "broadcast"          # MAY


@dataclass
class DiscoveryRecord:
    """Entity discovery record."""
    w4id: str
    entity_type: str
    name: str
    capabilities: List[str] = field(default_factory=list)
    endpoints: List[TransportEndpoint] = field(default_factory=list)
    witness_attestations: List[str] = field(default_factory=list)
    t3_composite: float = 0.5
    trust_ceiling: float = 0.85
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    signature: str = ""  # Self-signed discovery record

    def best_endpoint(self) -> Optional[TransportEndpoint]:
        """Return highest priority endpoint."""
        if not self.endpoints:
            return None
        return max(self.endpoints, key=lambda e: e.priority)


@dataclass
class DiscoveryRequest:
    """Discovery query."""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    desired_capabilities: List[str] = field(default_factory=list)
    acceptable_witnesses: List[str] = field(default_factory=list)
    min_trust: float = 0.0
    nonce: str = field(default_factory=lambda: os.urandom(16).hex())
    method: DiscoveryMethod = DiscoveryMethod.WITNESS_RELAY


class DiscoveryService:
    """Discovery service — resolves W4IDs and finds capabilities."""

    def __init__(self):
        self.registry: Dict[str, DiscoveryRecord] = {}
        self._nonce_cache: Set[str] = set()

    def register(self, record: DiscoveryRecord):
        """Register an entity for discovery."""
        record.signature = hashlib.sha256(
            f"{record.w4id}:{record.timestamp}".encode()
        ).hexdigest()[:32]
        self.registry[record.w4id] = record

    def query(self, request: DiscoveryRequest) -> List[DiscoveryRecord]:
        """Find entities matching discovery request."""
        # Replay protection
        if request.nonce in self._nonce_cache:
            return []
        self._nonce_cache.add(request.nonce)

        results = []
        for record in self.registry.values():
            # Capability filter
            if request.desired_capabilities:
                if not any(cap in record.capabilities
                          for cap in request.desired_capabilities):
                    continue

            # Witness filter
            if request.acceptable_witnesses:
                if not any(w in record.witness_attestations
                          for w in request.acceptable_witnesses):
                    continue

            # Trust filter
            if record.t3_composite < request.min_trust:
                continue

            results.append(record)

        # Sort by trust (highest first)
        return sorted(results, key=lambda r: r.t3_composite, reverse=True)

    def resolve(self, w4id: str) -> Optional[DiscoveryRecord]:
        """Resolve a W4ID to its discovery record."""
        return self.registry.get(w4id)


# ═══════════════════════════════════════════════════════════════
# GREASE Extensions (§5)
# ═══════════════════════════════════════════════════════════════

@dataclass
class Extension:
    """Protocol extension."""
    ext_id: str
    data: bytes = b""
    is_grease: bool = False

    @staticmethod
    def make_grease() -> "Extension":
        """Generate a GREASE extension with random ID."""
        grease_id = f"w4_ext_{os.urandom(4).hex()}@0"
        return Extension(ext_id=grease_id, data=os.urandom(8), is_grease=True)


# ═══════════════════════════════════════════════════════════════
# Handshake Messages (§4-§6)
# ═══════════════════════════════════════════════════════════════

@dataclass
class ClientHello:
    """ClientHello message (§4)."""
    supported_suites: List[CryptoSuite]
    media_profiles: List[MediaType]
    extensions: List[Extension]
    nonce: str = field(default_factory=lambda: os.urandom(32).hex())
    ephemeral_key: str = field(default_factory=lambda: os.urandom(32).hex())
    client_w4id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def has_grease(self) -> bool:
        """MUST have at least one GREASE extension per §5."""
        return any(e.is_grease for e in self.extensions)

    def validate(self) -> Tuple[bool, str]:
        """Validate ClientHello per spec."""
        if not self.supported_suites:
            return False, "No supported suites"
        if CryptoSuite.W4_BASE_1 not in self.supported_suites:
            return False, "W4-BASE-1 is MTI (mandatory to implement)"
        if not self.has_grease():
            return False, "At least one GREASE extension required"
        if not self.nonce or len(self.nonce) < 32:
            return False, "Nonce too short (need 16+ bytes)"
        return True, "Valid"


@dataclass
class ServerHello:
    """ServerHello message (§4)."""
    selected_suite: CryptoSuite
    selected_media: MediaType
    selected_profile: SignatureProfile
    acknowledged_extensions: List[str]  # Extension IDs the server supports
    encrypted_credentials: str = ""  # Server's encrypted credentials
    ephemeral_key: str = field(default_factory=lambda: os.urandom(32).hex())
    server_w4id: str = ""
    nonce: str = field(default_factory=lambda: os.urandom(32).hex())
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def validate(self) -> Tuple[bool, str]:
        if not self.selected_suite:
            return False, "No suite selected"
        if not self.encrypted_credentials:
            return False, "Missing encrypted credentials"
        return True, "Valid"


@dataclass
class ClientFinished:
    """ClientFinished message (§4)."""
    encrypted_credentials: str = ""
    transcript_mac: str = ""  # MAC over entire transcript
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ServerFinished:
    """ServerFinished message (§4)."""
    session_id: str = ""
    transcript_mac: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ═══════════════════════════════════════════════════════════════
# Session State Machine (§8)
# ═══════════════════════════════════════════════════════════════

class SessionState(str, Enum):
    """Handshake session states (§8)."""
    IDLE = "idle"
    HELLO_SENT = "hello_sent"
    HELLO_RECEIVED = "hello_received"
    NEGOTIATED = "negotiated"
    AUTHENTICATED = "authenticated"
    ESTABLISHED = "established"
    REKEYING = "rekeying"
    CLOSED = "closed"
    ERROR = "error"


# ═══════════════════════════════════════════════════════════════
# Capability Advertisement
# ═══════════════════════════════════════════════════════════════

@dataclass
class CapabilityRequirement:
    """Trust/ATP requirement for a capability."""
    min_t3_composite: float = 0.0
    min_t3_talent: float = 0.0
    min_t3_training: float = 0.0
    atp_stake: float = 0.0
    required_roles: List[str] = field(default_factory=list)


@dataclass
class Capability:
    """An advertised capability with trust gating."""
    name: str
    description: str = ""
    requirement: CapabilityRequirement = field(default_factory=CapabilityRequirement)
    category: str = "general"  # tool, prompt, context, resource

    def is_accessible(self, t3_composite: float, roles: List[str] = None,
                      atp_available: float = 0.0) -> bool:
        """Check if a client meets the requirements."""
        if t3_composite < self.requirement.min_t3_composite:
            return False
        if atp_available < self.requirement.atp_stake:
            return False
        if self.requirement.required_roles:
            if not roles or not any(r in self.requirement.required_roles for r in roles):
                return False
        return True


@dataclass
class CapabilityAdvertisement:
    """Full capability advertisement from a server."""
    server_w4id: str
    capabilities: List[Capability]
    protocols: List[str] = field(default_factory=lambda: ["web4/1.0"])
    trust_level: str = "standard"
    availability: float = 0.999
    ttl: int = 3600
    signature: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ═══════════════════════════════════════════════════════════════
# Transcript Hash (§6 — Transcript Binding)
# ═══════════════════════════════════════════════════════════════

class TranscriptHash:
    """Maintains running hash of handshake transcript."""

    def __init__(self):
        self._messages: List[str] = []
        self._hash = hashlib.sha256()

    def update(self, message_type: str, content: str):
        """Add a message to the transcript."""
        entry = f"{message_type}:{content}"
        self._messages.append(entry)
        self._hash.update(entry.encode())

    def digest(self) -> str:
        """Current transcript hash."""
        return self._hash.hexdigest()[:32]

    def compute_mac(self, key: str) -> str:
        """Compute MAC over transcript with session key."""
        import hmac
        return hmac.new(
            key.encode(), self.digest().encode(), hashlib.sha256
        ).hexdigest()[:32]

    @property
    def message_count(self) -> int:
        return len(self._messages)


# ═══════════════════════════════════════════════════════════════
# Error Handling (RFC 9457 Problem Details)
# ═══════════════════════════════════════════════════════════════

class W4ErrorCode(str, Enum):
    """Web4 error codes per spec."""
    BINDING_INVALID = "W4_ERR_BINDING_INVALID"
    PAIRING_REJECTED = "W4_ERR_PAIRING_REJECTED"
    WITNESS_INSUFFICIENT = "W4_ERR_WITNESS_INSUFFICIENT"
    AUTHZ_DENIED = "W4_ERR_AUTHZ_DENIED"
    CRYPTO_SUITE_MISMATCH = "W4_ERR_CRYPTO_SUITE_MISMATCH"
    PROTO_INVALID_STATE = "W4_ERR_PROTO_INVALID_STATE"
    PROTO_REPLAY_DETECTED = "W4_ERR_PROTO_REPLAY_DETECTED"
    PROTO_TIMEOUT = "W4_ERR_PROTO_TIMEOUT"


@dataclass
class W4Error:
    """RFC 9457 Problem Details for Web4."""
    code: W4ErrorCode
    title: str
    detail: str = ""
    status: int = 400
    instance: str = ""

    def to_dict(self) -> dict:
        return {
            "type": "about:blank",
            "title": self.title,
            "status": self.status,
            "code": self.code.value,
            "detail": self.detail,
            "instance": self.instance,
        }


# ═══════════════════════════════════════════════════════════════
# Protocol Negotiation Engine
# ═══════════════════════════════════════════════════════════════

class NegotiationEngine:
    """
    Complete web4:// protocol negotiation engine.

    Implements the full handshake lifecycle:
    1. Discovery (find peer, resolve endpoints)
    2. ClientHello → ServerHello (suite/media/extension negotiation)
    3. ClientFinished → ServerFinished (authentication + transcript binding)
    4. Session establishment with capability advertisement
    5. Rekey support for long-lived sessions
    """

    def __init__(self, w4id: str, supported_suites: List[CryptoSuite] = None,
                 supported_transports: List[TransportType] = None):
        self.w4id = w4id
        self.supported_suites = supported_suites or [
            CryptoSuite.W4_BASE_1,  # MTI
            CryptoSuite.W4_FIPS_1,
        ]
        self.supported_transports = supported_transports or [
            TransportType.QUIC,
            TransportType.TLS_1_3,
        ]
        self.capabilities: List[Capability] = []
        self.sessions: Dict[str, "SecureSession"] = {}
        self._nonce_cache: Set[str] = set()  # Anti-replay

    def add_capability(self, capability: Capability):
        self.capabilities.append(capability)

    # ─── Server-side negotiation ──────────────────────────────

    def process_client_hello(self, hello: ClientHello) -> Tuple[Optional[ServerHello], Optional[W4Error]]:
        """Process incoming ClientHello, return ServerHello or error."""
        # Validate
        valid, reason = hello.validate()
        if not valid:
            return None, W4Error(
                W4ErrorCode.PROTO_INVALID_STATE, "Invalid ClientHello", reason
            )

        # Anti-replay
        if hello.nonce in self._nonce_cache:
            return None, W4Error(
                W4ErrorCode.PROTO_REPLAY_DETECTED, "Replay detected",
                "Nonce already seen"
            )
        self._nonce_cache.add(hello.nonce)

        # Suite selection: first mutually supported
        selected_suite = None
        for suite in hello.supported_suites:
            if suite in self.supported_suites:
                selected_suite = suite
                break

        if not selected_suite:
            return None, W4Error(
                W4ErrorCode.CRYPTO_SUITE_MISMATCH, "No common suite",
                f"Client: {[s.value for s in hello.supported_suites]}, "
                f"Server: {[s.value for s in self.supported_suites]}"
            )

        # Media/profile from suite
        media, profile = SUITE_PROFILES[selected_suite]

        # Extension acknowledgment (ignore unknown/GREASE per §5)
        acked = [e.ext_id for e in hello.extensions if not e.is_grease
                 and not e.ext_id.startswith("w4_ext_")]

        # Build credentials
        cred_data = json.dumps({
            "w4id": self.w4id,
            "suite": selected_suite.value,
            "capabilities": [c.name for c in self.capabilities],
        })
        encrypted_creds = hashlib.sha256(cred_data.encode()).hexdigest()[:32]

        server_hello = ServerHello(
            selected_suite=selected_suite,
            selected_media=media,
            selected_profile=profile,
            acknowledged_extensions=acked,
            encrypted_credentials=encrypted_creds,
            server_w4id=self.w4id,
        )

        return server_hello, None

    def create_session(self, client_hello: ClientHello,
                       server_hello: ServerHello,
                       client_finished: ClientFinished) -> Tuple[Optional["SecureSession"], Optional[W4Error]]:
        """Create session after full handshake."""
        # Build transcript
        transcript = TranscriptHash()
        transcript.update("ClientHello", client_hello.nonce)
        transcript.update("ServerHello", server_hello.nonce)
        transcript.update("ClientFinished", client_finished.encrypted_credentials)

        # Derive session key (simulated HKDF)
        key_material = f"{client_hello.ephemeral_key}:{server_hello.ephemeral_key}"
        session_key = hashlib.sha256(key_material.encode()).hexdigest()[:32]

        # Verify transcript MAC
        expected_mac = transcript.compute_mac(session_key)
        if client_finished.transcript_mac != expected_mac:
            return None, W4Error(
                W4ErrorCode.CRYPTO_SUITE_MISMATCH, "Transcript MAC mismatch",
                "Client's transcript MAC does not match server computation"
            )

        # Build ServerFinished
        session_id = str(uuid.uuid4())[:12]
        server_finished = ServerFinished(
            session_id=session_id,
            transcript_mac=transcript.compute_mac(session_key + ":server"),
        )

        # Create session
        session = SecureSession(
            session_id=session_id,
            client_w4id=client_hello.client_w4id,
            server_w4id=self.w4id,
            suite=server_hello.selected_suite,
            media=server_hello.selected_media,
            session_key=session_key,
            transcript=transcript,
        )

        self.sessions[session_id] = session
        return session, None

    # ─── Client-side negotiation ──────────────────────────────

    def create_client_hello(self, server_w4id: str = "") -> ClientHello:
        """Create a ClientHello for initiating a handshake."""
        extensions = [Extension.make_grease()]  # At least one GREASE required
        return ClientHello(
            supported_suites=self.supported_suites,
            media_profiles=[MediaType.CBOR, MediaType.JSON],
            extensions=extensions,
            client_w4id=self.w4id,
        )

    def process_server_hello(self, server_hello: ServerHello,
                             client_hello: ClientHello) -> Tuple[Optional[ClientFinished], Optional[W4Error]]:
        """Process ServerHello, return ClientFinished."""
        valid, reason = server_hello.validate()
        if not valid:
            return None, W4Error(
                W4ErrorCode.PROTO_INVALID_STATE, "Invalid ServerHello", reason
            )

        # Verify selected suite is one we offered
        if server_hello.selected_suite not in client_hello.supported_suites:
            return None, W4Error(
                W4ErrorCode.CRYPTO_SUITE_MISMATCH, "Suite not offered",
                f"Server selected {server_hello.selected_suite.value} which was not offered"
            )

        # Build transcript
        transcript = TranscriptHash()
        transcript.update("ClientHello", client_hello.nonce)
        transcript.update("ServerHello", server_hello.nonce)

        # Derive session key
        key_material = f"{client_hello.ephemeral_key}:{server_hello.ephemeral_key}"
        session_key = hashlib.sha256(key_material.encode()).hexdigest()[:32]

        # Build ClientFinished with credentials
        cred_data = json.dumps({"w4id": self.w4id, "suite": server_hello.selected_suite.value})
        encrypted_creds = hashlib.sha256(cred_data.encode()).hexdigest()[:32]

        transcript.update("ClientFinished", encrypted_creds)
        mac = transcript.compute_mac(session_key)

        return ClientFinished(
            encrypted_credentials=encrypted_creds,
            transcript_mac=mac,
        ), None

    # ─── Transport selection ──────────────────────────────────

    def select_transport(self, peer_transports: List[TransportType]) -> Optional[TransportType]:
        """Select highest mutual priority transport."""
        for t in self.supported_transports:
            if t in peer_transports:
                return t
        # Fallback to TLS 1.3 (universal baseline)
        if TransportType.TLS_1_3 in peer_transports:
            return TransportType.TLS_1_3
        return None


# ═══════════════════════════════════════════════════════════════
# Secure Session
# ═══════════════════════════════════════════════════════════════

class SecureSession:
    """An established secure session after handshake."""

    def __init__(self, session_id: str, client_w4id: str, server_w4id: str,
                 suite: CryptoSuite, media: MediaType, session_key: str,
                 transcript: TranscriptHash):
        self.session_id = session_id
        self.client_w4id = client_w4id
        self.server_w4id = server_w4id
        self.suite = suite
        self.media = media
        self.session_key = session_key
        self.transcript = transcript
        self.state = SessionState.ESTABLISHED
        self.message_count = 0
        self.rekey_count = 0
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.capabilities_exchanged = False

    def send_message(self, msg_type: str, payload: dict) -> dict:
        """Send an encrypted message."""
        if self.state != SessionState.ESTABLISHED:
            raise ValueError(f"Cannot send in state {self.state}")
        self.message_count += 1
        content = json.dumps(payload)
        encrypted = hashlib.sha256(
            f"{self.session_key}:{self.message_count}:{content}".encode()
        ).hexdigest()[:32]
        return {
            "session_id": self.session_id,
            "msg_id": self.message_count,
            "type": msg_type,
            "encrypted_payload": encrypted,
            "media": self.media.value,
        }

    def rekey(self) -> str:
        """Perform one-way ratchet rekey (§7)."""
        if self.state not in (SessionState.ESTABLISHED, SessionState.REKEYING):
            raise ValueError(f"Cannot rekey in state {self.state}")
        self.state = SessionState.REKEYING
        # One-way ratchet: new_key = HKDF(old_key || "rekey" || counter)
        self.session_key = hashlib.sha256(
            f"{self.session_key}:rekey:{self.rekey_count}".encode()
        ).hexdigest()[:32]
        self.rekey_count += 1
        self.state = SessionState.ESTABLISHED
        return self.session_key

    def close(self):
        self.state = SessionState.CLOSED


# ═══════════════════════════════════════════════════════════════
# W4ID Resolution (§5 — web4:// URI scheme)
# ═══════════════════════════════════════════════════════════════

@dataclass
class W4URI:
    """Parsed web4:// URI."""
    w4id: str
    path: str = ""
    query: Dict[str, str] = field(default_factory=dict)
    fragment: str = ""

    @staticmethod
    def parse(uri: str) -> "W4URI":
        """Parse a web4:// URI."""
        if not uri.startswith("web4://"):
            raise ValueError(f"Not a web4 URI: {uri}")
        rest = uri[7:]  # Strip scheme

        # Fragment
        fragment = ""
        if "#" in rest:
            rest, fragment = rest.rsplit("#", 1)

        # Query
        query = {}
        if "?" in rest:
            rest, query_str = rest.split("?", 1)
            for pair in query_str.split("&"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    query[k] = v

        # W4ID and path
        parts = rest.split("/", 1)
        w4id = parts[0]
        path = "/" + parts[1] if len(parts) > 1 else ""

        return W4URI(w4id=w4id, path=path, query=query, fragment=fragment)

    def to_string(self) -> str:
        result = f"web4://{self.w4id}{self.path}"
        if self.query:
            qs = "&".join(f"{k}={v}" for k, v in self.query.items())
            result += f"?{qs}"
        if self.fragment:
            result += f"#{self.fragment}"
        return result


# ═══════════════════════════════════════════════════════════════
# Pairwise W4IDp (§4 — privacy-preserving per-peer IDs)
# ═══════════════════════════════════════════════════════════════

class PairwiseIDManager:
    """Generates privacy-preserving pairwise identifiers."""

    def __init__(self, base_w4id: str, secret: str = ""):
        self.base_w4id = base_w4id
        self._secret = secret or os.urandom(32).hex()
        self._pairs: Dict[str, str] = {}

    def derive_pairwise(self, peer_w4id: str) -> str:
        """Derive a pairwise W4IDp for a specific peer (HKDF-based)."""
        if peer_w4id in self._pairs:
            return self._pairs[peer_w4id]
        # HKDF derivation (simulated)
        material = f"{self._secret}:{self.base_w4id}:{peer_w4id}"
        w4idp = f"w4idp:{hashlib.sha256(material.encode()).hexdigest()[:16]}"
        self._pairs[peer_w4id] = w4idp
        return w4idp

    def resolve_peer(self, w4idp: str) -> Optional[str]:
        """Reverse-lookup: which peer does this W4IDp belong to?"""
        for peer, pid in self._pairs.items():
            if pid == w4idp:
                return peer
        return None


# ═══════════════════════════════════════════════════════════════
# CHECKS
# ═══════════════════════════════════════════════════════════════

passed = 0
failed = 0
total = 0
current_section = ""


def check(condition: bool, description: str):
    global passed, failed, total
    total += 1
    if condition:
        passed += 1
    else:
        failed += 1
        print(f"  FAIL [{current_section}] #{total}: {description}")


def section(name: str):
    global current_section
    current_section = name
    print(f"Section: {name}")


def run_checks():
    global passed, failed, total

    # ═══════════════════════════════════════════════════════════
    # Section 1: Crypto Suite Configuration
    # ═══════════════════════════════════════════════════════════
    section("1. Crypto Suite Configuration")

    # Suite profiles
    media, profile = SUITE_PROFILES[CryptoSuite.W4_BASE_1]
    check(media == MediaType.CBOR, "W4-BASE-1 uses CBOR")
    check(profile == SignatureProfile.COSE, "W4-BASE-1 uses COSE")

    media, profile = SUITE_PROFILES[CryptoSuite.W4_FIPS_1]
    check(media == MediaType.JSON, "W4-FIPS-1 uses JSON")
    check(profile == SignatureProfile.JOSE, "W4-FIPS-1 uses JOSE")

    media, profile = SUITE_PROFILES[CryptoSuite.W4_IOT_1]
    check(media == MediaType.CBOR, "W4-IOT-1 uses CBOR (compressed)")
    check(profile == SignatureProfile.COSE, "W4-IOT-1 uses COSE")

    # All suites defined
    check(len(CryptoSuite) == 3, "3 crypto suites defined")
    check(len(TransportType) == 8, "8 transport types defined")
    check(len(DiscoveryMethod) == 6, "6 discovery methods defined")

    # ═══════════════════════════════════════════════════════════
    # Section 2: Discovery Service
    # ═══════════════════════════════════════════════════════════
    section("2. Discovery Service")

    disco = DiscoveryService()

    # Register entities
    disco.register(DiscoveryRecord(
        w4id="w4id:alice:abc123",
        entity_type="human",
        name="Alice",
        capabilities=["code_review", "deploy"],
        endpoints=[
            TransportEndpoint(TransportType.QUIC, "quic://alice.web4.io:4433", priority=10),
            TransportEndpoint(TransportType.TLS_1_3, "tls://alice.web4.io:8443", priority=5),
        ],
        witness_attestations=["w4id:witness1", "w4id:witness2"],
        t3_composite=0.8,
    ))
    disco.register(DiscoveryRecord(
        w4id="w4id:bob:def456",
        entity_type="ai",
        name="Bob",
        capabilities=["code_review", "test"],
        endpoints=[
            TransportEndpoint(TransportType.TLS_1_3, "tls://bob.web4.io:8443", priority=5),
        ],
        witness_attestations=["w4id:witness1"],
        t3_composite=0.6,
    ))
    disco.register(DiscoveryRecord(
        w4id="w4id:iot:ghi789",
        entity_type="device",
        name="Sensor",
        capabilities=["telemetry"],
        endpoints=[
            TransportEndpoint(TransportType.BLE_GATT, "ble://sensor-01", priority=3, constrained=True,
                             supports_full_metering=False),
        ],
        witness_attestations=["w4id:witness3"],
        t3_composite=0.4,
    ))

    check(len(disco.registry) == 3, "3 entities registered")

    # Resolve by W4ID
    record = disco.resolve("w4id:alice:abc123")
    check(record is not None, "Alice resolved by W4ID")
    check(record.name == "Alice", "Correct name resolved")
    check(record.signature != "", "Discovery record is signed")

    # Best endpoint
    best = record.best_endpoint()
    check(best is not None, "Best endpoint found")
    check(best.transport == TransportType.QUIC, "QUIC is highest priority")

    # Query by capability
    req = DiscoveryRequest(desired_capabilities=["code_review"])
    results = disco.query(req)
    check(len(results) == 2, "2 entities have code_review capability")
    check(results[0].t3_composite >= results[1].t3_composite, "Results sorted by trust (desc)")

    # Query by witness
    req2 = DiscoveryRequest(acceptable_witnesses=["w4id:witness3"])
    results2 = disco.query(req2)
    check(len(results2) == 1, "Only sensor has witness3")
    check(results2[0].name == "Sensor", "Correct entity filtered by witness")

    # Query by trust threshold
    req3 = DiscoveryRequest(min_trust=0.7)
    results3 = disco.query(req3)
    check(len(results3) == 1, "Only Alice has T3 ≥ 0.7")

    # Replay protection
    req4 = DiscoveryRequest(nonce=req.nonce)  # Reuse nonce
    results4 = disco.query(req4)
    check(len(results4) == 0, "Replay detected — nonce reuse blocked")

    # Unknown entity
    check(disco.resolve("w4id:unknown") is None, "Unknown W4ID returns None")

    # ═══════════════════════════════════════════════════════════
    # Section 3: GREASE Extensions
    # ═══════════════════════════════════════════════════════════
    section("3. GREASE Extensions")

    grease = Extension.make_grease()
    check(grease.is_grease, "GREASE extension flagged")
    check(grease.ext_id.startswith("w4_ext_"), "GREASE ID format correct")
    check(grease.ext_id.endswith("@0"), "GREASE ID ends with @0")
    check(len(grease.data) == 8, "GREASE has random data")

    # Two GREASE extensions should have different IDs (with very high probability)
    grease2 = Extension.make_grease()
    check(grease.ext_id != grease2.ext_id, "GREASE IDs are unique")

    # Regular extension
    regular = Extension(ext_id="capability_advertisement", data=b"v1")
    check(not regular.is_grease, "Regular extension is not GREASE")

    # ═══════════════════════════════════════════════════════════
    # Section 4: ClientHello Validation
    # ═══════════════════════════════════════════════════════════
    section("4. ClientHello Validation")

    # Valid ClientHello
    hello = ClientHello(
        supported_suites=[CryptoSuite.W4_BASE_1, CryptoSuite.W4_FIPS_1],
        media_profiles=[MediaType.CBOR, MediaType.JSON],
        extensions=[Extension.make_grease()],
        client_w4id="w4id:client:test",
    )
    valid, reason = hello.validate()
    check(valid, "Valid ClientHello passes validation")
    check(hello.has_grease(), "ClientHello has GREASE")

    # Missing MTI suite
    bad_hello = ClientHello(
        supported_suites=[CryptoSuite.W4_FIPS_1],  # No BASE-1
        media_profiles=[MediaType.JSON],
        extensions=[Extension.make_grease()],
    )
    valid, reason = bad_hello.validate()
    check(not valid, "Missing W4-BASE-1 is invalid")
    check("MTI" in reason, "Error mentions MTI requirement")

    # No GREASE
    no_grease = ClientHello(
        supported_suites=[CryptoSuite.W4_BASE_1],
        media_profiles=[MediaType.CBOR],
        extensions=[Extension(ext_id="real_ext")],  # No GREASE
    )
    valid, reason = no_grease.validate()
    check(not valid, "Missing GREASE is invalid")

    # Empty suites
    empty = ClientHello(
        supported_suites=[],
        media_profiles=[],
        extensions=[Extension.make_grease()],
    )
    valid, reason = empty.validate()
    check(not valid, "Empty suites is invalid")

    # Short nonce
    short_nonce = ClientHello(
        supported_suites=[CryptoSuite.W4_BASE_1],
        media_profiles=[MediaType.CBOR],
        extensions=[Extension.make_grease()],
        nonce="short",
    )
    valid, reason = short_nonce.validate()
    check(not valid, "Short nonce is invalid")

    # ═══════════════════════════════════════════════════════════
    # Section 5: Full Handshake — Happy Path
    # ═══════════════════════════════════════════════════════════
    section("5. Full Handshake — Happy Path")

    # Server setup
    server = NegotiationEngine(
        "w4id:server:main",
        supported_suites=[CryptoSuite.W4_BASE_1, CryptoSuite.W4_FIPS_1],
    )
    server.add_capability(Capability("read_data", "Read from database", CapabilityRequirement(min_t3_composite=0.3)))
    server.add_capability(Capability("write_data", "Write to database", CapabilityRequirement(min_t3_composite=0.6)))

    # Client setup
    client = NegotiationEngine(
        "w4id:client:alice",
        supported_suites=[CryptoSuite.W4_BASE_1],
    )

    # Step 1: Client creates ClientHello
    client_hello = client.create_client_hello("w4id:server:main")
    check(client_hello.client_w4id == "w4id:client:alice", "ClientHello has correct W4ID")
    check(CryptoSuite.W4_BASE_1 in client_hello.supported_suites, "ClientHello offers BASE-1")
    check(client_hello.has_grease(), "ClientHello includes GREASE")

    # Step 2: Server processes ClientHello
    server_hello, err = server.process_client_hello(client_hello)
    check(err is None, "No error processing ClientHello")
    check(server_hello is not None, "ServerHello created")
    check(server_hello.selected_suite == CryptoSuite.W4_BASE_1, "Server selected W4-BASE-1")
    check(server_hello.selected_media == MediaType.CBOR, "Server selected CBOR media")
    check(server_hello.selected_profile == SignatureProfile.COSE, "Server selected COSE profile")
    check(server_hello.encrypted_credentials != "", "Server credentials encrypted")
    check(len(server_hello.acknowledged_extensions) == 0,
          "No non-GREASE extensions to acknowledge")

    # Step 3: Client processes ServerHello → ClientFinished
    client_finished, err = client.process_server_hello(server_hello, client_hello)
    check(err is None, "No error processing ServerHello")
    check(client_finished is not None, "ClientFinished created")
    check(client_finished.transcript_mac != "", "Transcript MAC computed")
    check(client_finished.encrypted_credentials != "", "Client credentials encrypted")

    # Step 4: Server creates session
    session, err = server.create_session(client_hello, server_hello, client_finished)
    check(err is None, "No error creating session")
    check(session is not None, "Session created")
    check(session.state == SessionState.ESTABLISHED, "Session is ESTABLISHED")
    check(session.suite == CryptoSuite.W4_BASE_1, "Session uses BASE-1")
    check(session.media == MediaType.CBOR, "Session uses CBOR")
    check(session.session_key != "", "Session key derived")
    check(session.client_w4id == "w4id:client:alice", "Session tracks client W4ID")
    check(session.server_w4id == "w4id:server:main", "Session tracks server W4ID")

    # ═══════════════════════════════════════════════════════════
    # Section 6: Session Operations
    # ═══════════════════════════════════════════════════════════
    section("6. Session Operations")

    # Send messages
    msg1 = session.send_message("request", {"action": "read", "resource": "users"})
    check(msg1["type"] == "request", "Message type is request")
    check(msg1["session_id"] == session.session_id, "Message has session ID")
    check(msg1["msg_id"] == 1, "First message ID is 1")
    check(msg1["encrypted_payload"] != "", "Payload is encrypted")
    check(msg1["media"] == MediaType.CBOR.value, "Message uses negotiated media")

    msg2 = session.send_message("response", {"status": "ok", "data": [1, 2, 3]})
    check(msg2["msg_id"] == 2, "Second message ID is 2")
    check(session.message_count == 2, "Message count tracks correctly")

    # Rekey (one-way ratchet per §7)
    old_key = session.session_key
    new_key = session.rekey()
    check(new_key != old_key, "Rekey produces different key")
    check(session.rekey_count == 1, "Rekey count incremented")
    check(session.state == SessionState.ESTABLISHED, "Session stays ESTABLISHED after rekey")

    # Second rekey produces yet another key
    new_key2 = session.rekey()
    check(new_key2 != new_key, "Second rekey produces different key")
    check(new_key2 != old_key, "Second rekey differs from original")
    check(session.rekey_count == 2, "Rekey count = 2")

    # Can still send after rekey
    msg3 = session.send_message("event", {"type": "update"})
    check(msg3["msg_id"] == 3, "Message count continues after rekey")

    # Close
    session.close()
    check(session.state == SessionState.CLOSED, "Session closed")

    try:
        session.send_message("request", {})
        check(False, "Should not send on closed session")
    except ValueError:
        check(True, "Closed session rejects messages")

    try:
        session.rekey()
        check(False, "Should not rekey closed session")
    except ValueError:
        check(True, "Closed session rejects rekey")

    # ═══════════════════════════════════════════════════════════
    # Section 7: Handshake Failure Paths
    # ═══════════════════════════════════════════════════════════
    section("7. Handshake Failure Paths")

    # No common suite
    iot_only = NegotiationEngine("w4id:iot", supported_suites=[CryptoSuite.W4_IOT_1])
    fips_only = NegotiationEngine("w4id:fips", supported_suites=[CryptoSuite.W4_FIPS_1])
    iot_hello = ClientHello(
        supported_suites=[CryptoSuite.W4_IOT_1],
        media_profiles=[MediaType.CBOR],
        extensions=[Extension.make_grease()],
    )
    # IOT-1 only client missing BASE-1 → invalid hello
    # But let's test suite mismatch with a valid hello (has BASE-1)
    mixed_hello = ClientHello(
        supported_suites=[CryptoSuite.W4_BASE_1, CryptoSuite.W4_IOT_1],
        media_profiles=[MediaType.CBOR],
        extensions=[Extension.make_grease()],
    )
    sh, err = fips_only.process_client_hello(mixed_hello)
    # Server only has FIPS-1, client offers BASE-1 and IOT-1 — no match
    check(sh is None, "No ServerHello when no common suite")
    check(err is not None, "Error returned for suite mismatch")
    check(err.code == W4ErrorCode.CRYPTO_SUITE_MISMATCH, "Correct error code")

    # Replay attack
    replay_server = NegotiationEngine("w4id:replay_test", supported_suites=[CryptoSuite.W4_BASE_1])
    good_hello = ClientHello(
        supported_suites=[CryptoSuite.W4_BASE_1],
        media_profiles=[MediaType.CBOR],
        extensions=[Extension.make_grease()],
    )
    sh1, err1 = replay_server.process_client_hello(good_hello)
    check(sh1 is not None, "First hello succeeds")
    sh2, err2 = replay_server.process_client_hello(good_hello)
    check(sh2 is None, "Replay hello rejected")
    check(err2.code == W4ErrorCode.PROTO_REPLAY_DETECTED, "Replay error code")

    # Invalid ClientHello (server-side validation)
    invalid_hello = ClientHello(
        supported_suites=[],  # Empty
        media_profiles=[],
        extensions=[Extension.make_grease()],
    )
    sh, err = server.process_client_hello(invalid_hello)
    check(sh is None, "Invalid hello rejected")
    check(err.code == W4ErrorCode.PROTO_INVALID_STATE, "Protocol state error")

    # Transcript MAC mismatch
    valid_hello = client.create_client_hello()
    sh, _ = server.process_client_hello(valid_hello)
    bad_finished = ClientFinished(
        encrypted_credentials="some_creds",
        transcript_mac="WRONG_MAC_VALUE_HERE",
    )
    sess, err = server.create_session(valid_hello, sh, bad_finished)
    check(sess is None, "Bad MAC rejects session")
    check(err.code == W4ErrorCode.CRYPTO_SUITE_MISMATCH, "MAC mismatch error")

    # ═══════════════════════════════════════════════════════════
    # Section 8: Capability Advertisement & Gating
    # ═══════════════════════════════════════════════════════════
    section("8. Capability Advertisement & Gating")

    # Capabilities with different trust requirements
    cap_public = Capability("public_info", "Public data", CapabilityRequirement())
    cap_standard = Capability("standard_op", "Standard operation",
                             CapabilityRequirement(min_t3_composite=0.5, atp_stake=10))
    cap_admin = Capability("admin_op", "Admin action",
                          CapabilityRequirement(min_t3_composite=0.9, atp_stake=100,
                                               required_roles=["admin"]))

    # Public access
    check(cap_public.is_accessible(0.1), "Public cap accessible to anyone")
    check(cap_public.is_accessible(0.0), "Public cap accessible at zero trust")

    # Standard access
    check(cap_standard.is_accessible(0.6, atp_available=50), "Standard cap accessible with good trust + ATP")
    check(not cap_standard.is_accessible(0.3, atp_available=50), "Standard cap denied: low trust")
    check(not cap_standard.is_accessible(0.6, atp_available=5), "Standard cap denied: low ATP")

    # Admin access
    check(cap_admin.is_accessible(0.95, roles=["admin", "dev"], atp_available=200),
          "Admin cap accessible with role + trust + ATP")
    check(not cap_admin.is_accessible(0.95, roles=["dev"], atp_available=200),
          "Admin cap denied: missing admin role")
    check(not cap_admin.is_accessible(0.95, roles=["admin"], atp_available=50),
          "Admin cap denied: insufficient ATP")

    # Capability advertisement
    advert = CapabilityAdvertisement(
        server_w4id="w4id:server:main",
        capabilities=[cap_public, cap_standard, cap_admin],
        protocols=["web4/1.0", "mcp/1.0"],
        ttl=7200,
    )
    check(len(advert.capabilities) == 3, "3 capabilities advertised")
    check("web4/1.0" in advert.protocols, "Web4 protocol advertised")
    check(advert.ttl == 7200, "Custom TTL set")

    # ═══════════════════════════════════════════════════════════
    # Section 9: W4URI Parsing
    # ═══════════════════════════════════════════════════════════
    section("9. W4URI Parsing")

    # Basic URI
    uri = W4URI.parse("web4://w4id:alice:abc123/messages/inbox")
    check(uri.w4id == "w4id:alice:abc123", "W4ID parsed correctly")
    check(uri.path == "/messages/inbox", "Path parsed correctly")
    check(uri.query == {}, "No query params")
    check(uri.fragment == "", "No fragment")

    # URI with query and fragment
    uri2 = W4URI.parse("web4://w4id:bob:def/api/v1?limit=10&offset=0#section2")
    check(uri2.w4id == "w4id:bob:def", "W4ID from complex URI")
    check(uri2.path == "/api/v1", "Path from complex URI")
    check(uri2.query == {"limit": "10", "offset": "0"}, "Query params parsed")
    check(uri2.fragment == "section2", "Fragment parsed")

    # Round-trip
    check(uri2.to_string() == "web4://w4id:bob:def/api/v1?limit=10&offset=0#section2",
          "URI round-trips correctly")

    # Minimal URI (no path)
    uri3 = W4URI.parse("web4://w4id:simple")
    check(uri3.w4id == "w4id:simple", "Minimal URI parsed")
    check(uri3.path == "", "No path in minimal URI")

    # Invalid scheme
    try:
        W4URI.parse("https://example.com")
        check(False, "Should reject non-web4 URI")
    except ValueError:
        check(True, "Non-web4 URI rejected")

    # ═══════════════════════════════════════════════════════════
    # Section 10: Pairwise W4IDp
    # ═══════════════════════════════════════════════════════════
    section("10. Pairwise W4IDp")

    pw = PairwiseIDManager("w4id:alice:real", secret="alice_secret_key")

    # Derive pairwise IDs
    pid_bob = pw.derive_pairwise("w4id:bob:real")
    pid_charlie = pw.derive_pairwise("w4id:charlie:real")

    check(pid_bob.startswith("w4idp:"), "Pairwise ID has correct prefix")
    check(pid_bob != pid_charlie, "Different peers get different pairwise IDs")
    check(pid_bob != "w4id:alice:real", "Pairwise ID differs from real W4ID")

    # Deterministic — same input → same output
    pid_bob2 = pw.derive_pairwise("w4id:bob:real")
    check(pid_bob == pid_bob2, "Pairwise derivation is deterministic")

    # Reverse lookup
    peer = pw.resolve_peer(pid_bob)
    check(peer == "w4id:bob:real", "Reverse lookup works")

    peer_unknown = pw.resolve_peer("w4idp:unknown")
    check(peer_unknown is None, "Unknown pairwise returns None")

    # Different base entities produce different pairwise IDs for same peer
    pw2 = PairwiseIDManager("w4id:dave:real", secret="dave_secret_key")
    pid_bob_from_dave = pw2.derive_pairwise("w4id:bob:real")
    check(pid_bob_from_dave != pid_bob, "Different entities derive different pairwise IDs")

    # ═══════════════════════════════════════════════════════════
    # Section 11: Transport Negotiation
    # ═══════════════════════════════════════════════════════════
    section("11. Transport Negotiation")

    engine = NegotiationEngine("w4id:test",
                              supported_transports=[TransportType.QUIC, TransportType.TLS_1_3])

    # Mutual support
    peer_transports = [TransportType.TLS_1_3, TransportType.WEBSOCKET]
    selected = engine.select_transport(peer_transports)
    check(selected == TransportType.TLS_1_3, "TLS 1.3 selected as mutual transport")

    # Prefer QUIC when available
    peer2 = [TransportType.QUIC, TransportType.TLS_1_3]
    selected2 = engine.select_transport(peer2)
    check(selected2 == TransportType.QUIC, "QUIC preferred when mutual")

    # Fallback to TLS 1.3
    iot_engine = NegotiationEngine("w4id:iot",
                                  supported_transports=[TransportType.BLE_GATT])
    selected3 = iot_engine.select_transport([TransportType.TLS_1_3, TransportType.QUIC])
    check(selected3 == TransportType.TLS_1_3, "Fallback to TLS 1.3 baseline")

    # No common transport at all
    ble_only = [TransportType.BLE_GATT]
    quic_only_engine = NegotiationEngine("w4id:q", supported_transports=[TransportType.QUIC])
    selected4 = quic_only_engine.select_transport(ble_only)
    check(selected4 is None, "No common transport returns None")

    # ═══════════════════════════════════════════════════════════
    # Section 12: Error Handling (RFC 9457)
    # ═══════════════════════════════════════════════════════════
    section("12. Error Handling (RFC 9457)")

    err = W4Error(
        code=W4ErrorCode.AUTHZ_DENIED,
        title="Unauthorized",
        detail="Credential lacks scope write:lct",
        status=401,
        instance="web4://w4id:test/messages/123",
    )
    d = err.to_dict()
    check(d["type"] == "about:blank", "RFC 9457 type field")
    check(d["title"] == "Unauthorized", "Error title")
    check(d["status"] == 401, "HTTP status code")
    check(d["code"] == "W4_ERR_AUTHZ_DENIED", "Web4 error code")
    check(d["detail"] == "Credential lacks scope write:lct", "Error detail")
    check(d["instance"] == "web4://w4id:test/messages/123", "Error instance URI")

    # All error codes
    check(len(W4ErrorCode) == 8, "8 error codes defined")

    # ═══════════════════════════════════════════════════════════
    # Section 13: Transcript Hash & Binding
    # ═══════════════════════════════════════════════════════════
    section("13. Transcript Hash & Binding")

    th = TranscriptHash()
    check(th.message_count == 0, "Empty transcript has 0 messages")

    th.update("ClientHello", "nonce_abc")
    th.update("ServerHello", "nonce_xyz")
    check(th.message_count == 2, "2 messages in transcript")

    digest1 = th.digest()
    check(len(digest1) == 32, "Transcript digest is 32 hex chars")

    # MAC with key
    mac = th.compute_mac("session_key_123")
    check(len(mac) == 32, "MAC is 32 hex chars")
    check(mac != digest1, "MAC differs from raw digest")

    # Same key produces same MAC
    mac2 = th.compute_mac("session_key_123")
    check(mac == mac2, "MAC is deterministic")

    # Different key produces different MAC
    mac3 = th.compute_mac("different_key")
    check(mac3 != mac, "Different key → different MAC")

    # Adding more messages changes digest
    th.update("ClientFinished", "creds")
    digest2 = th.digest()
    check(digest2 != digest1, "Digest changes with new messages")

    # ═══════════════════════════════════════════════════════════
    # Section 14: Integrated Scenario — Full Lifecycle
    # ═══════════════════════════════════════════════════════════
    section("14. Integrated Scenario — Full Lifecycle")

    # Setup: Server and Client with discovery
    discovery = DiscoveryService()

    # Server registers for discovery
    srv_engine = NegotiationEngine(
        "w4id:srv:prod",
        supported_suites=[CryptoSuite.W4_BASE_1, CryptoSuite.W4_FIPS_1],
        supported_transports=[TransportType.QUIC, TransportType.TLS_1_3],
    )
    srv_engine.add_capability(Capability("query_db", "Database query",
                                        CapabilityRequirement(min_t3_composite=0.4, atp_stake=5)))
    srv_engine.add_capability(Capability("admin_panel", "Admin access",
                                        CapabilityRequirement(min_t3_composite=0.9, required_roles=["admin"])))

    discovery.register(DiscoveryRecord(
        w4id="w4id:srv:prod",
        entity_type="service",
        name="ProductionDB",
        capabilities=["query_db", "admin_panel"],
        endpoints=[
            TransportEndpoint(TransportType.QUIC, "quic://db.web4.io:4433", priority=10),
            TransportEndpoint(TransportType.TLS_1_3, "tls://db.web4.io:8443", priority=5),
        ],
        witness_attestations=["w4id:trusted_witness_1"],
        t3_composite=0.9,
    ))

    # Client discovers the server
    cli_engine = NegotiationEngine(
        "w4id:cli:alice",
        supported_suites=[CryptoSuite.W4_BASE_1],
        supported_transports=[TransportType.QUIC, TransportType.TLS_1_3],
    )

    # Step 1: Discovery
    query = DiscoveryRequest(
        desired_capabilities=["query_db"],
        acceptable_witnesses=["w4id:trusted_witness_1"],
        min_trust=0.5,
    )
    found = discovery.query(query)
    check(len(found) == 1, "Discovered 1 matching service")
    check(found[0].w4id == "w4id:srv:prod", "Found correct server")

    # Step 2: Transport selection
    server_record = found[0]
    peer_transports = [ep.transport for ep in server_record.endpoints]
    transport = cli_engine.select_transport(peer_transports)
    check(transport == TransportType.QUIC, "Selected QUIC transport")

    # Step 3: Handshake
    ch = cli_engine.create_client_hello("w4id:srv:prod")
    sh, err = srv_engine.process_client_hello(ch)
    check(err is None, "Server accepted ClientHello")

    cf, err = cli_engine.process_server_hello(sh, ch)
    check(err is None, "Client accepted ServerHello")

    sess, err = srv_engine.create_session(ch, sh, cf)
    check(err is None, "Session established successfully")
    check(sess.state == SessionState.ESTABLISHED, "Session is live")

    # Step 4: Use session
    msg = sess.send_message("request", {"query": "SELECT * FROM users", "db": "web4"})
    check(msg["type"] == "request", "Query sent through session")

    # Step 5: Capability check
    check(srv_engine.capabilities[0].is_accessible(0.5, atp_available=10),
          "Client can access query_db (T3=0.5, ATP=10)")
    check(not srv_engine.capabilities[1].is_accessible(0.5, roles=["user"], atp_available=100),
          "Client cannot access admin_panel (no admin role)")

    # Step 6: Rekey after N messages
    for i in range(5):
        sess.send_message("request", {"query": f"q{i}"})
    check(sess.message_count == 6, "6 messages sent")
    sess.rekey()
    check(sess.rekey_count == 1, "Rekeyed once")

    # Step 7: Pairwise privacy
    srv_pairwise = PairwiseIDManager("w4id:srv:prod")
    pid = srv_pairwise.derive_pairwise("w4id:cli:alice")
    check(pid.startswith("w4idp:"), "Pairwise ID for session")
    check(pid != "w4id:srv:prod", "Pairwise hides real W4ID")

    # Step 8: URI resolution
    uri = W4URI.parse("web4://w4id:srv:prod/api/query?db=web4&limit=100")
    resolved = discovery.resolve(uri.w4id)
    check(resolved is not None, "URI W4ID resolves via discovery")
    check(resolved.name == "ProductionDB", "Resolved to correct server")
    check(uri.path == "/api/query", "URI path preserved for routing")

    # Step 9: Session teardown
    sess.close()
    check(sess.state == SessionState.CLOSED, "Session properly closed")

    # ═══════════════════════════════════════════════════════════
    # Section 15: Edge Cases
    # ═══════════════════════════════════════════════════════════
    section("15. Edge Cases")

    # Empty discovery registry
    empty_disco = DiscoveryService()
    check(empty_disco.query(DiscoveryRequest()) == [], "Empty registry returns nothing")
    check(empty_disco.resolve("w4id:anything") is None, "Empty registry resolves nothing")

    # URI with only W4ID
    bare = W4URI.parse("web4://w4id:bare")
    check(bare.w4id == "w4id:bare", "Bare URI parses")
    check(bare.path == "", "No path on bare URI")
    check(bare.to_string() == "web4://w4id:bare", "Bare URI round-trips")

    # Discovery record with no endpoints
    no_ep = DiscoveryRecord(w4id="w4id:ghost", entity_type="service", name="Ghost")
    check(no_ep.best_endpoint() is None, "No endpoint returns None")

    # Session with zero messages
    fresh = SecureSession("sid:0", "c", "s", CryptoSuite.W4_BASE_1,
                         MediaType.CBOR, "key", TranscriptHash())
    check(fresh.message_count == 0, "Fresh session has 0 messages")
    check(fresh.rekey_count == 0, "Fresh session has 0 rekeys")

    # Pairwise derivation for self (degenerate but valid)
    pw_self = PairwiseIDManager("w4id:me")
    pid_self = pw_self.derive_pairwise("w4id:me")
    check(pid_self.startswith("w4idp:"), "Self-pairwise still valid")

    # Multiple GREASE extensions allowed
    multi_grease_hello = ClientHello(
        supported_suites=[CryptoSuite.W4_BASE_1],
        media_profiles=[MediaType.CBOR],
        extensions=[Extension.make_grease(), Extension.make_grease(), Extension.make_grease()],
    )
    valid, _ = multi_grease_hello.validate()
    check(valid, "Multiple GREASE extensions are valid")

    # ═══════════════════════════════════════════════════════════
    # Report
    # ═══════════════════════════════════════════════════════════
    print(f"\n{'=' * 60}")
    print(f"Protocol Negotiation Engine: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  {failed} checks FAILED")
    else:
        print(f"  All checks passed!")
    print(f"{'=' * 60}")

    print(f"\nComponents validated:")
    print(f"  - 3 crypto suites (BASE-1/FIPS-1/IOT-1)")
    print(f"  - 8 transport types with priority selection")
    print(f"  - 6 discovery methods with replay protection")
    print(f"  - 4-message handshake (ClientHello→ServerHello→ClientFinished→ServerFinished)")
    print(f"  - GREASE forward compatibility")
    print(f"  - Transcript binding with HMAC")
    print(f"  - Trust-gated capability advertisement")
    print(f"  - web4:// URI parsing and resolution")
    print(f"  - Pairwise W4IDp privacy-preserving identifiers")
    print(f"  - RFC 9457 error handling")
    print(f"  - Full lifecycle: discover → negotiate → handshake → use → rekey → close")


if __name__ == "__main__":
    run_checks()
