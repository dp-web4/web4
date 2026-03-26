"""
Web4 Core Protocol Types

Canonical types per web4-standard/core-spec/core-protocol.md.

Defines the handshake, pairing, transport, and discovery type system
for Web4 entity-to-entity communication. This module provides DATA
TYPES and VALIDATION only — no networking, no cryptographic operations,
no actual handshake execution.

Key concepts:
- HandshakePhase: 4-phase HPKE handshake (ClientHello → ServerFinished)
- PairingMethod: Direct, Mediated, or QR Code pairing
- Transport: supported transports with compliance levels and capabilities
- DiscoveryMethod: mechanisms for entity discovery (DNS-SD, QR, Witness, etc.)
- Web4URI: parser/validator for web4:// URI scheme (RFC 3986 subset)
- HandshakeMessage: typed message containers for each handshake phase

Cross-module integration:
- web4.security: CryptoSuiteId for suite negotiation in handshake
- web4.lct: LCT IDs embedded in handshake credentials

Validated against: web4-standard/test-vectors/protocol/
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional

__all__ = [
    # Classes
    "HandshakePhase",
    "ClientHello", "ServerHello", "ClientFinished", "ServerFinished",
    "HandshakeMessage", "PairingMethod",
    "Transport", "TransportCompliance", "TransportProfile",
    "DiscoveryMethod", "PrivacyLevel",
    "DiscoveryRequest", "DiscoveryResponse",
    "Web4URI",
    # Functions
    "get_transport_profile", "required_transports", "negotiate_transport",
    "required_discovery_methods", "discovery_privacy",
    "web4_uri_to_dict", "web4_uri_from_dict", "transport_profile_to_dict",
    # Constants
    "TRANSPORT_PROFILES", "DISCOVERY_METADATA",
]


# ── Handshake Phases ──────────────────────────────────────────────

class HandshakePhase(IntEnum):
    """HPKE handshake phases per spec §2."""
    CLIENT_HELLO = 1
    SERVER_HELLO = 2
    CLIENT_FINISHED = 3
    SERVER_FINISHED = 4


@dataclass
class ClientHello:
    """
    First handshake message: client announces supported suites and identity.

    Per spec §2: includes supported_suites, client_public_key,
    client_w4id_ephemeral, nonce, and optional GREASE extensions.
    """
    supported_suites: List[str]
    client_public_key: str
    client_w4id_ephemeral: str
    nonce: str  # 32-byte hex nonce
    supported_extensions: List[str] = field(default_factory=list)
    grease_extensions: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.supported_suites:
            raise ValueError("ClientHello must list at least one supported suite")
        if not self.nonce:
            raise ValueError("ClientHello requires a nonce")

    @property
    def phase(self) -> HandshakePhase:
        return HandshakePhase.CLIENT_HELLO


@dataclass
class ServerHello:
    """
    Server response: selects suite, provides credentials.

    Per spec §2: includes selected_suite, server_public_key,
    server_w4id_ephemeral, nonce, and encrypted_credentials.
    """
    selected_suite: str
    server_public_key: str
    server_w4id_ephemeral: str
    nonce: str
    encrypted_credentials: str = ""
    selected_extensions: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.selected_suite:
            raise ValueError("ServerHello must select a suite")
        if not self.nonce:
            raise ValueError("ServerHello requires a nonce")

    @property
    def phase(self) -> HandshakePhase:
        return HandshakePhase.SERVER_HELLO


@dataclass
class ClientFinished:
    """
    Client completion: sends encrypted credentials and transcript MAC.

    Per spec §2: encrypted client_credentials + MAC(transcript).
    """
    encrypted_credentials: str
    transcript_mac: str

    def __post_init__(self):
        if not self.transcript_mac:
            raise ValueError("ClientFinished requires transcript MAC")

    @property
    def phase(self) -> HandshakePhase:
        return HandshakePhase.CLIENT_FINISHED


@dataclass
class ServerFinished:
    """
    Server completion: confirms handshake with transcript MAC and session ID.

    Per spec §2: MAC(transcript) + session_id. After this, application
    data can flow.
    """
    transcript_mac: str
    session_id: str

    def __post_init__(self):
        if not self.transcript_mac:
            raise ValueError("ServerFinished requires transcript MAC")
        if not self.session_id:
            raise ValueError("ServerFinished requires session_id")

    @property
    def phase(self) -> HandshakePhase:
        return HandshakePhase.SERVER_FINISHED


# ── Pairing Methods ──────────────────────────────────────────────

class PairingMethod(str, Enum):
    """Pairing methods per spec §1.3."""
    DIRECT = "direct"        # Two entities connect directly
    MEDIATED = "mediated"    # Trusted third-party mediator
    QR_CODE = "qr_code"      # QR code out-of-band pairing


# ── Transport ────────────────────────────────────────────────────

class TransportCompliance(str, Enum):
    """RFC 2119 compliance levels for transports."""
    MUST = "MUST"
    SHOULD = "SHOULD"
    MAY = "MAY"


@dataclass(frozen=True)
class TransportProfile:
    """
    A supported transport with compliance and capability metadata.

    Per spec §4.1: each transport has a compliance level, use cases,
    whether it supports standard or compressed handshake, and full
    or limited metering.
    """
    transport_id: str
    compliance: TransportCompliance
    use_cases: List[str]
    compressed_handshake: bool = False
    limited_metering: bool = False

    @property
    def full_metering(self) -> bool:
        return not self.limited_metering


class Transport(str, Enum):
    """Transport identifiers per spec §4.1."""
    TLS_1_3 = "tls_1.3"
    QUIC = "quic"
    WEB_TRANSPORT = "web_transport"
    WEB_RTC = "web_rtc"
    WEB_SOCKET = "web_socket"
    BLE_GATT = "ble_gatt"
    CAN_BUS = "can_bus"
    TCP_TLS = "tcp_tls"


# Canonical transport profiles from spec §4.1
TRANSPORT_PROFILES: Dict[Transport, TransportProfile] = {
    Transport.TLS_1_3: TransportProfile(
        transport_id="tls_1.3",
        compliance=TransportCompliance.MUST,
        use_cases=["web", "cloud"],
    ),
    Transport.QUIC: TransportProfile(
        transport_id="quic",
        compliance=TransportCompliance.MUST,
        use_cases=["low-latency", "mobile"],
    ),
    Transport.WEB_TRANSPORT: TransportProfile(
        transport_id="web_transport",
        compliance=TransportCompliance.SHOULD,
        use_cases=["browser_p2p"],
    ),
    Transport.WEB_RTC: TransportProfile(
        transport_id="web_rtc",
        compliance=TransportCompliance.SHOULD,
        use_cases=["p2p", "nat_traversal"],
    ),
    Transport.WEB_SOCKET: TransportProfile(
        transport_id="web_socket",
        compliance=TransportCompliance.MAY,
        use_cases=["legacy_browser"],
    ),
    Transport.BLE_GATT: TransportProfile(
        transport_id="ble_gatt",
        compliance=TransportCompliance.MAY,
        use_cases=["iot", "proximity"],
        compressed_handshake=True,
        limited_metering=True,
    ),
    Transport.CAN_BUS: TransportProfile(
        transport_id="can_bus",
        compliance=TransportCompliance.MAY,
        use_cases=["automotive"],
        compressed_handshake=True,
        limited_metering=True,
    ),
    Transport.TCP_TLS: TransportProfile(
        transport_id="tcp_tls",
        compliance=TransportCompliance.MAY,
        use_cases=["direct_socket"],
    ),
}


def get_transport_profile(transport: Transport) -> TransportProfile:
    """Look up the canonical profile for a transport."""
    return TRANSPORT_PROFILES[transport]


def required_transports() -> List[Transport]:
    """Return transports that all implementations MUST support."""
    return [t for t, p in TRANSPORT_PROFILES.items()
            if p.compliance == TransportCompliance.MUST]


def negotiate_transport(
    client_transports: List[Transport],
    server_transports: List[Transport],
) -> Optional[Transport]:
    """
    Select the highest-priority mutual transport per spec §4.3.

    Priority: client order wins (client advertises in priority order).
    Falls back to TLS 1.3 as universal baseline if no explicit match.
    """
    for t in client_transports:
        if t in server_transports:
            return t
    # Fallback: TLS 1.3 is universal baseline
    if Transport.TLS_1_3 in server_transports:
        return Transport.TLS_1_3
    return None


# ── Discovery Mechanisms ─────────────────────────────────────────

class DiscoveryMethod(str, Enum):
    """Entity discovery mechanisms per spec §4.2."""
    DNS_SD = "dns_sd"            # DNS-SD/mDNS — local network (SHOULD)
    QR_CODE_OOB = "qr_code_oob"  # QR code out-of-band (SHOULD)
    WITNESS_RELAY = "witness_relay"  # Bootstrap via witnesses (MUST)
    DNS_BOOTSTRAP = "dns_bootstrap"  # DNS TXT records (MAY)
    DHT_LOOKUP = "dht_lookup"    # Distributed hash table (MAY)
    BROADCAST = "broadcast"      # Unidirectional announcement (MAY)


class PrivacyLevel(str, Enum):
    """Privacy characterization for discovery methods."""
    HIGH = "high"      # Requires proximity or physical access
    MEDIUM = "medium"  # Trusted intermediary sees query
    LOW = "low"        # Broadcasts presence or queries visibly


# Discovery method metadata from spec §4.2
DISCOVERY_METADATA: Dict[DiscoveryMethod, Dict[str, Any]] = {
    DiscoveryMethod.DNS_SD: {
        "compliance": TransportCompliance.SHOULD,
        "privacy": PrivacyLevel.LOW,
        "description": "Local network discovery",
    },
    DiscoveryMethod.QR_CODE_OOB: {
        "compliance": TransportCompliance.SHOULD,
        "privacy": PrivacyLevel.HIGH,
        "description": "Out-of-band pairing via QR code",
    },
    DiscoveryMethod.WITNESS_RELAY: {
        "compliance": TransportCompliance.MUST,
        "privacy": PrivacyLevel.MEDIUM,
        "description": "Bootstrap via known witnesses",
    },
    DiscoveryMethod.DNS_BOOTSTRAP: {
        "compliance": TransportCompliance.MAY,
        "privacy": PrivacyLevel.LOW,
        "description": "DNS TXT records for services",
    },
    DiscoveryMethod.DHT_LOOKUP: {
        "compliance": TransportCompliance.MAY,
        "privacy": PrivacyLevel.LOW,
        "description": "Distributed hash table",
    },
    DiscoveryMethod.BROADCAST: {
        "compliance": TransportCompliance.MAY,
        "privacy": PrivacyLevel.LOW,
        "description": "Unidirectional announcement",
    },
}


def required_discovery_methods() -> List[DiscoveryMethod]:
    """Return discovery methods that all implementations MUST support."""
    return [m for m, meta in DISCOVERY_METADATA.items()
            if meta["compliance"] == TransportCompliance.MUST]


def discovery_privacy(method: DiscoveryMethod) -> PrivacyLevel:
    """Get the privacy level of a discovery method."""
    return DISCOVERY_METADATA[method]["privacy"]


@dataclass
class DiscoveryRequest:
    """
    Entity discovery request per spec §4.2.

    An entity generates a discovery request with desired capabilities,
    acceptable witnesses, and a nonce for replay protection.
    """
    desired_capabilities: List[str]
    acceptable_witnesses: List[str] = field(default_factory=list)
    nonce: str = ""
    preferred_methods: List[DiscoveryMethod] = field(default_factory=list)


@dataclass
class DiscoveryResponse:
    """
    Discovery response containing matching entities.

    Includes entity endpoints, current witness attestations,
    and connection info.
    """
    entities: List[Dict[str, Any]] = field(default_factory=list)
    witness_attestations: List[Dict[str, Any]] = field(default_factory=list)


# ── Web4 URI ─────────────────────────────────────────────────────

# web4://<w4id>/<path>[?query][#fragment]
_WEB4_URI_PATTERN = re.compile(
    r'^web4://([^/?#]+)'    # w4id (authority)
    r'(/[^?#]*)?'           # optional path
    r'(\?[^#]*)?'           # optional query
    r'(#.*)?$'              # optional fragment
)


@dataclass(frozen=True)
class Web4URI:
    """
    Parsed Web4 URI per spec §5.

    Format: web4://<w4id>/<path-abempty>[?query][#fragment]

    This is regex-based validation and decomposition, NOT a full
    RFC 3986 parser. The w4id component is validated as non-empty;
    further W4ID validation (DID format) should use web4.security.W4ID.
    """
    w4id: str
    path: str = "/"
    query: Optional[str] = None
    fragment: Optional[str] = None

    def __post_init__(self):
        if not self.w4id:
            raise ValueError("Web4URI requires a non-empty w4id")

    def __str__(self) -> str:
        """Reconstruct the URI string."""
        uri = f"web4://{self.w4id}{self.path}"
        if self.query is not None:
            uri += f"?{self.query}"
        if self.fragment is not None:
            uri += f"#{self.fragment}"
        return uri

    @staticmethod
    def parse(uri: str) -> Web4URI:
        """
        Parse a web4:// URI into components.

        Raises ValueError if the URI doesn't match the web4:// scheme.
        """
        match = _WEB4_URI_PATTERN.match(uri)
        if not match:
            raise ValueError(f"Invalid Web4 URI: {uri!r}")

        w4id = match.group(1)
        path = match.group(2) or "/"
        query = match.group(3)
        fragment = match.group(4)

        # Strip leading ? and # from query/fragment
        if query is not None:
            query = query[1:]  # remove '?'
        if fragment is not None:
            fragment = fragment[1:]  # remove '#'

        return Web4URI(w4id=w4id, path=path, query=query, fragment=fragment)

    @staticmethod
    def is_valid(uri: str) -> bool:
        """Check whether a string is a valid web4:// URI."""
        return _WEB4_URI_PATTERN.match(uri) is not None


# ── Handshake Message Envelope ───────────────────────────────────

@dataclass
class HandshakeMessage:
    """
    Typed envelope for handshake messages.

    Wraps any handshake phase message (ClientHello, ServerHello,
    ClientFinished, ServerFinished) with transport metadata.
    """
    phase: HandshakePhase
    payload: Any  # One of ClientHello | ServerHello | ClientFinished | ServerFinished
    transport: Transport = Transport.TLS_1_3
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dict for cross-language vectors."""
        d: Dict[str, Any] = {
            "phase": self.phase.name,
            "transport": self.transport.value,
        }
        if self.timestamp:
            d["timestamp"] = self.timestamp

        p = self.payload
        if isinstance(p, ClientHello):
            d["payload"] = {
                "supported_suites": p.supported_suites,
                "client_public_key": p.client_public_key,
                "client_w4id_ephemeral": p.client_w4id_ephemeral,
                "nonce": p.nonce,
                "supported_extensions": p.supported_extensions,
                "grease_extensions": p.grease_extensions,
            }
        elif isinstance(p, ServerHello):
            d["payload"] = {
                "selected_suite": p.selected_suite,
                "server_public_key": p.server_public_key,
                "server_w4id_ephemeral": p.server_w4id_ephemeral,
                "nonce": p.nonce,
                "encrypted_credentials": p.encrypted_credentials,
                "selected_extensions": p.selected_extensions,
            }
        elif isinstance(p, ClientFinished):
            d["payload"] = {
                "encrypted_credentials": p.encrypted_credentials,
                "transcript_mac": p.transcript_mac,
            }
        elif isinstance(p, ServerFinished):
            d["payload"] = {
                "transcript_mac": p.transcript_mac,
                "session_id": p.session_id,
            }
        return d


# ── JSON round-trip helpers ──────────────────────────────────────

def web4_uri_to_dict(uri: Web4URI) -> Dict[str, Any]:
    """Serialize a Web4URI to a JSON-compatible dict."""
    d: Dict[str, Any] = {
        "w4id": uri.w4id,
        "path": uri.path,
        "uri_string": str(uri),
    }
    if uri.query is not None:
        d["query"] = uri.query
    if uri.fragment is not None:
        d["fragment"] = uri.fragment
    return d


def web4_uri_from_dict(d: Dict[str, Any]) -> Web4URI:
    """Deserialize a Web4URI from a dict."""
    return Web4URI(
        w4id=d["w4id"],
        path=d.get("path", "/"),
        query=d.get("query"),
        fragment=d.get("fragment"),
    )


def transport_profile_to_dict(profile: TransportProfile) -> Dict[str, Any]:
    """Serialize a TransportProfile to a JSON-compatible dict."""
    return {
        "transport_id": profile.transport_id,
        "compliance": profile.compliance.value,
        "use_cases": profile.use_cases,
        "compressed_handshake": profile.compressed_handshake,
        "limited_metering": profile.limited_metering,
    }
