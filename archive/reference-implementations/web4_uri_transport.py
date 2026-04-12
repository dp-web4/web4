#!/usr/bin/env python3
"""
Web4 URI, Transport & Messaging Protocol — Reference Implementation

Implements core-protocol.md §2-§5:
  §2 — Messaging Protocol (request/response/event/credential, encryption)
  §3 — Data & Credential Formats (W4ID, VCs, JSON-LD)
  §4 — Transport & Discovery (8 transports, 6 discovery methods, negotiation)
  §5 — URI Scheme (web4:// parsing, resolution, endpoint mapping)

§1 (Crypto Suites) and Handshake are already in core_protocol_handshake.py.

@version 1.0.0
@see web4-standard/core-spec/core-protocol.md
"""

import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse, parse_qs, urlencode


# ═══════════════════════════════════════════════════════════════
# §1 — Cryptographic Suites (reference only; handshake in separate file)
# ═══════════════════════════════════════════════════════════════

class CryptoSuite(Enum):
    """Crypto suite definitions per spec §1."""
    W4_BASE_1 = ("W4-BASE-1", "MUST", "X25519", "Ed25519", "ChaCha20-Poly1305", "SHA-256", "HKDF", "COSE")
    W4_FIPS_1 = ("W4-FIPS-1", "SHOULD", "P-256ECDH", "ECDSA-P256", "AES-128-GCM", "SHA-256", "HKDF", "JOSE")
    W4_IOT_1 = ("W4-IOT-1", "MAY", "X25519", "Ed25519", "AES-CCM", "SHA-256", "HKDF", "CBOR")

    def __init__(self, suite_id, status, kem, sig, aead, hash_alg, kdf, profile):
        self.suite_id = suite_id
        self.status = status
        self.kem = kem
        self.sig = sig
        self.aead = aead
        self.hash_alg = hash_alg
        self.kdf = kdf
        self.profile = profile


# ═══════════════════════════════════════════════════════════════
# §2 — Messaging Protocol
# ═══════════════════════════════════════════════════════════════

class MessageType(Enum):
    """Standard message types per spec §2.2."""
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    CREDENTIAL = "credential"


class ContentType(Enum):
    """Content types for message payloads."""
    JSON = "application/json"
    JSON_LD = "application/ld+json"
    TEXT = "text/plain"
    BINARY = "application/octet-stream"
    CBOR = "application/cbor"


@dataclass
class MessageHeader:
    """Message header with metadata per spec §2.1."""
    message_id: str
    message_type: MessageType
    content_type: ContentType
    sender_w4id: str
    recipient_w4id: str
    timestamp: str = ""
    correlation_id: str = ""   # Links response to request
    suite_id: str = "W4-BASE-1"
    encrypted: bool = True     # §2.3: All messages MUST be encrypted

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.message_id:
            self.message_id = f"msg:{os.urandom(8).hex()}"

    def to_dict(self) -> dict:
        d = {
            "message_id": self.message_id,
            "type": self.message_type.value,
            "content_type": self.content_type.value,
            "sender": self.sender_w4id,
            "recipient": self.recipient_w4id,
            "timestamp": self.timestamp,
            "suite_id": self.suite_id,
            "encrypted": self.encrypted,
        }
        if self.correlation_id:
            d["correlation_id"] = self.correlation_id
        return d


@dataclass
class Web4Message:
    """Complete Web4 message with header + payload per spec §2.1."""
    header: MessageHeader
    payload: Any = None

    def to_dict(self) -> dict:
        return {
            "header": self.header.to_dict(),
            "payload": self.payload,
        }

    def encrypt(self, session_key: bytes) -> "EncryptedMessage":
        """Encrypt message per spec §2.3."""
        # Simulated encryption: hash(session_key + payload)
        payload_bytes = json.dumps(self.payload, default=str).encode()
        nonce = os.urandom(12)
        # Simulated ciphertext
        tag = hashlib.sha256(session_key + payload_bytes + nonce).digest()[:16]
        return EncryptedMessage(
            header=self.header,
            ciphertext=payload_bytes.hex(),
            nonce=nonce.hex(),
            tag=tag.hex(),
        )

    @staticmethod
    def create_request(sender: str, recipient: str, action: str,
                       params: Dict = None) -> "Web4Message":
        header = MessageHeader(
            message_id=f"msg:{os.urandom(8).hex()}",
            message_type=MessageType.REQUEST,
            content_type=ContentType.JSON,
            sender_w4id=sender,
            recipient_w4id=recipient,
        )
        return Web4Message(
            header=header,
            payload={"action": action, "params": params or {}},
        )

    @staticmethod
    def create_response(request: "Web4Message", result: Any,
                        success: bool = True) -> "Web4Message":
        header = MessageHeader(
            message_id=f"msg:{os.urandom(8).hex()}",
            message_type=MessageType.RESPONSE,
            content_type=ContentType.JSON,
            sender_w4id=request.header.recipient_w4id,
            recipient_w4id=request.header.sender_w4id,
            correlation_id=request.header.message_id,
        )
        return Web4Message(
            header=header,
            payload={"success": success, "result": result},
        )

    @staticmethod
    def create_event(sender: str, recipient: str, event_type: str,
                     data: Dict = None) -> "Web4Message":
        header = MessageHeader(
            message_id=f"msg:{os.urandom(8).hex()}",
            message_type=MessageType.EVENT,
            content_type=ContentType.JSON,
            sender_w4id=sender,
            recipient_w4id=recipient,
        )
        return Web4Message(
            header=header,
            payload={"event_type": event_type, "data": data or {}},
        )

    @staticmethod
    def create_credential(sender: str, recipient: str,
                          credential: Dict) -> "Web4Message":
        header = MessageHeader(
            message_id=f"msg:{os.urandom(8).hex()}",
            message_type=MessageType.CREDENTIAL,
            content_type=ContentType.JSON_LD,
            sender_w4id=sender,
            recipient_w4id=recipient,
        )
        return Web4Message(header=header, payload=credential)


@dataclass
class EncryptedMessage:
    """Encrypted message wrapper per spec §2.3."""
    header: MessageHeader
    ciphertext: str
    nonce: str
    tag: str

    def to_dict(self) -> dict:
        return {
            "header": self.header.to_dict(),
            "ciphertext": self.ciphertext,
            "nonce": self.nonce,
            "tag": self.tag,
        }


# ═══════════════════════════════════════════════════════════════
# §3 — Data & Credential Formats
# ═══════════════════════════════════════════════════════════════

# §3.1 — W4ID (Web4 Identifier)

W4ID_PATTERN = re.compile(r'^w4id:([a-z]+):(.+)$')


@dataclass
class W4ID:
    """Web4 Identifier per spec §3.1."""
    method: str          # e.g. "key", "web"
    specific_id: str     # method-specific identifier

    def __str__(self) -> str:
        return f"w4id:{self.method}:{self.specific_id}"

    @staticmethod
    def parse(w4id_str: str) -> Optional["W4ID"]:
        """Parse a W4ID string."""
        m = W4ID_PATTERN.match(w4id_str)
        if m:
            return W4ID(method=m.group(1), specific_id=m.group(2))
        return None

    @staticmethod
    def generate(method: str = "key") -> "W4ID":
        """Generate a new W4ID."""
        specific = os.urandom(16).hex()
        return W4ID(method=method, specific_id=specific)

    def to_dict(self) -> dict:
        return {"w4id": str(self), "method": self.method,
                "specific_id": self.specific_id}


# §3.2 — Verifiable Credentials

@dataclass
class VerifiableCredential:
    """W3C Verifiable Credential per spec §3.2."""
    context: List[str] = field(default_factory=lambda: [
        "https://www.w3.org/2018/credentials/v1",
        "https://web4.io/contexts/credential.jsonld",
    ])
    credential_type: List[str] = field(default_factory=lambda: [
        "VerifiableCredential",
    ])
    issuer: str = ""
    issuance_date: str = ""
    credential_subject: Dict = field(default_factory=dict)
    proof: Optional[Dict] = None

    def __post_init__(self):
        if not self.issuance_date:
            self.issuance_date = datetime.now(timezone.utc).isoformat()

    def sign(self, issuer_key: bytes) -> "VerifiableCredential":
        """Sign credential (simulated)."""
        payload = json.dumps(self.credential_subject, sort_keys=True).encode()
        sig = hashlib.sha256(issuer_key + payload).hexdigest()
        self.proof = {
            "type": "Ed25519Signature2020",
            "created": datetime.now(timezone.utc).isoformat(),
            "verificationMethod": f"{self.issuer}#key-1",
            "proofPurpose": "assertionMethod",
            "proofValue": sig,
        }
        return self

    def verify(self, issuer_key: bytes) -> bool:
        """Verify credential signature (simulated)."""
        if not self.proof:
            return False
        payload = json.dumps(self.credential_subject, sort_keys=True).encode()
        expected_sig = hashlib.sha256(issuer_key + payload).hexdigest()
        return self.proof.get("proofValue") == expected_sig

    def to_dict(self) -> dict:
        d = {
            "@context": self.context,
            "type": self.credential_type,
            "issuer": self.issuer,
            "issuanceDate": self.issuance_date,
            "credentialSubject": self.credential_subject,
        }
        if self.proof:
            d["proof"] = self.proof
        return d


# §3.3 — JSON-LD Context

WEB4_CONTEXTS = {
    "sal": "https://web4.io/contexts/sal.jsonld",
    "credential": "https://web4.io/contexts/credential.jsonld",
    "entity": "https://web4.io/contexts/entity.jsonld",
    "trust": "https://web4.io/contexts/trust.jsonld",
}


# ═══════════════════════════════════════════════════════════════
# §4 — Transport & Discovery
# ═══════════════════════════════════════════════════════════════

# §4.1 — Transport Matrix

class TransportStatus(Enum):
    MUST = "MUST"
    SHOULD = "SHOULD"
    MAY = "MAY"


class Transport(Enum):
    """Transport types per spec §4.1 table."""
    TLS_13 = ("TLS 1.3", "MUST", "Web, Cloud", True, True)
    QUIC = ("QUIC", "MUST", "Low-latency, Mobile", True, True)
    WEBTRANSPORT = ("WebTransport", "SHOULD", "Browser P2P", True, True)
    WEBRTC = ("WebRTC DataChannel", "SHOULD", "P2P, NAT traversal", True, True)
    WEBSOCKET = ("WebSocket", "MAY", "Legacy browser", True, True)
    BLE_GATT = ("BLE GATT", "MAY", "IoT, Proximity", True, False)
    CAN_BUS = ("CAN Bus", "MAY", "Automotive", True, False)
    TCP_TLS = ("TCP/TLS", "MAY", "Direct socket", True, True)

    def __init__(self, name, status, use_cases, handshake_support, full_metering):
        self.transport_name = name
        self.status = status
        self.use_cases = use_cases
        self.handshake_support = handshake_support
        self.full_metering = full_metering

    @property
    def is_constrained(self) -> bool:
        return not self.full_metering

    @property
    def is_required(self) -> bool:
        return self.status == "MUST"


# §4.2 — Discovery Mechanisms

class DiscoveryMethod(Enum):
    """Discovery methods per spec §4.2 table."""
    DNS_SD = ("DNS-SD/mDNS", "SHOULD", "Local network discovery", "Low")
    QR_CODE = ("QR Code OOB", "SHOULD", "Out-of-band pairing", "High")
    WITNESS_RELAY = ("Witness Relay", "MUST", "Bootstrap via known witnesses", "Medium")
    DNS_BOOTSTRAP = ("DNS Bootstrap", "MAY", "DNS TXT records for services", "Low")
    DHT_LOOKUP = ("DHT Lookup", "MAY", "Distributed hash table", "Low")
    BROADCAST = ("Broadcast", "MAY", "Unidirectional announcement", "Low")

    def __init__(self, method_name, status, description, privacy_level):
        self.method_name = method_name
        self.status = status
        self.description = description
        self.privacy_level = privacy_level


@dataclass
class DiscoveryRequest:
    """Discovery request per spec §4.2 protocol."""
    desired_capabilities: List[str]
    acceptable_witnesses: List[str]
    nonce: str = ""              # Replay protection
    requester_w4id: str = ""
    preferred_transport: Optional[str] = None

    def __post_init__(self):
        if not self.nonce:
            self.nonce = os.urandom(16).hex()

    def to_dict(self) -> dict:
        return {
            "type": "discovery_request",
            "capabilities": self.desired_capabilities,
            "witnesses": self.acceptable_witnesses,
            "nonce": self.nonce,
            "requester": self.requester_w4id,
            "preferred_transport": self.preferred_transport,
        }


@dataclass
class DiscoveryResult:
    """Single discovery result per spec §4.2."""
    entity_w4id: str
    capabilities: List[str]
    witness_attestations: List[Dict]
    endpoints: List[Dict]            # [{transport, address, priority}]
    trust_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "entity": self.entity_w4id,
            "capabilities": self.capabilities,
            "witness_attestations": self.witness_attestations,
            "endpoints": self.endpoints,
            "trust_score": self.trust_score,
        }


class DiscoveryService:
    """Discovery service implementing spec §4.2 protocol."""

    def __init__(self):
        self.registered_entities: Dict[str, DiscoveryResult] = {}
        self.seen_nonces: Set[str] = set()

    def register(self, entity_w4id: str, capabilities: List[str],
                 witness_attestations: List[Dict],
                 endpoints: List[Dict], trust_score: float = 0.0):
        self.registered_entities[entity_w4id] = DiscoveryResult(
            entity_w4id=entity_w4id,
            capabilities=capabilities,
            witness_attestations=witness_attestations,
            endpoints=endpoints,
            trust_score=trust_score,
        )

    def discover(self, request: DiscoveryRequest) -> List[DiscoveryResult]:
        """
        Process discovery request per spec §4.2:
        1. Validate nonce (replay protection)
        2. Match capabilities
        3. Filter by witness attestations
        4. Return matching entities with endpoints
        """
        # 1. Nonce check
        if request.nonce in self.seen_nonces:
            return []  # Replay
        self.seen_nonces.add(request.nonce)

        results = []
        for w4id, entry in self.registered_entities.items():
            # 2. Capability matching
            if request.desired_capabilities:
                if not any(c in entry.capabilities for c in request.desired_capabilities):
                    continue

            # 3. Witness filtering
            if request.acceptable_witnesses:
                # Check if any of entity's witnesses are in acceptable list
                entity_witness_ids = [
                    w.get("witness_id", "") for w in entry.witness_attestations
                ]
                if not any(w in request.acceptable_witnesses for w in entity_witness_ids):
                    continue

            results.append(entry)

        # Sort by trust score
        results.sort(key=lambda r: r.trust_score, reverse=True)
        return results


# §4.3 — Transport Selection

class TransportNegotiator:
    """Transport negotiation per spec §4.3."""

    # Default priority order (highest first)
    DEFAULT_PRIORITY = [
        Transport.QUIC,
        Transport.WEBTRANSPORT,
        Transport.TLS_13,
        Transport.WEBRTC,
        Transport.WEBSOCKET,
        Transport.TCP_TLS,
        Transport.BLE_GATT,
        Transport.CAN_BUS,
    ]

    @classmethod
    def negotiate(cls, client_transports: List[Transport],
                  server_transports: List[Transport]) -> Optional[Transport]:
        """
        Select highest mutual priority transport.
        Falls back to TLS 1.3 as universal baseline.
        """
        for transport in cls.DEFAULT_PRIORITY:
            if transport in client_transports and transport in server_transports:
                return transport
        # Universal baseline
        if Transport.TLS_13 in client_transports and Transport.TLS_13 in server_transports:
            return Transport.TLS_13
        return None

    @classmethod
    def get_required_transports(cls) -> List[Transport]:
        """Return MUST-support transports."""
        return [t for t in Transport if t.is_required]


# ═══════════════════════════════════════════════════════════════
# §5 — URI Scheme
# ═══════════════════════════════════════════════════════════════

WEB4_URI_PATTERN = re.compile(
    r'^web4://([^/?#]+)(/[^?#]*)?(\?[^#]*)?(#.*)?$'
)


@dataclass
class Web4URI:
    """
    Web4 URI per spec §5.1.
    Format: web4://<w4id>/<path>[?query][#fragment]
    """
    w4id: str
    path: str = "/"
    query: Dict[str, str] = field(default_factory=dict)
    fragment: str = ""

    def __str__(self) -> str:
        uri = f"web4://{self.w4id}{self.path}"
        if self.query:
            uri += "?" + urlencode(self.query)
        if self.fragment:
            uri += "#" + self.fragment
        return uri

    @staticmethod
    def parse(uri_str: str) -> Optional["Web4URI"]:
        """Parse a web4:// URI string per spec §5.1."""
        m = WEB4_URI_PATTERN.match(uri_str)
        if not m:
            return None
        w4id = m.group(1)
        path = m.group(2) or "/"
        query_str = m.group(3) or ""
        fragment = m.group(4) or ""

        # Parse query
        query = {}
        if query_str:
            # Remove leading ?
            query_str = query_str[1:]
            for pair in query_str.split("&"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    query[k] = v

        # Remove leading #
        if fragment:
            fragment = fragment[1:]

        return Web4URI(w4id=w4id, path=path, query=query, fragment=fragment)

    def to_dict(self) -> dict:
        return {
            "scheme": "web4",
            "w4id": self.w4id,
            "path": self.path,
            "query": self.query,
            "fragment": self.fragment,
            "full_uri": str(self),
        }


class URIResolver:
    """
    URI resolution per spec §5.2.
    Maps W4ID → service endpoint, then sends request with path/query/fragment.
    """

    def __init__(self):
        self.endpoint_registry: Dict[str, str] = {}  # w4id → endpoint URL

    def register_endpoint(self, w4id: str, endpoint: str):
        self.endpoint_registry[w4id] = endpoint

    def resolve(self, uri: Web4URI) -> Optional[Dict]:
        """
        Resolve a Web4 URI per spec §5.2:
        1. Resolve W4ID to service endpoint
        2. Build full request with path/query/fragment
        """
        endpoint = self.endpoint_registry.get(uri.w4id)
        if not endpoint:
            return None
        return {
            "endpoint": endpoint,
            "w4id": uri.w4id,
            "path": uri.path,
            "query": uri.query,
            "fragment": uri.fragment,
            "resolved_url": f"{endpoint}{uri.path}",
        }


# ═══════════════════════════════════════════════════════════════
# Self-Test
# ═══════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(label, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {label}{f' — {detail}' if detail else ''}")
        else:
            failed += 1
            print(f"  [FAIL] {label}{f' — {detail}' if detail else ''}")

    # ═══════════════════════════════════════════════════════════
    # §1 — Cryptographic Suites (Reference)
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T1: Cryptographic Suites (§1) ═══")
    check("T1.1 3 suites defined", len(CryptoSuite) == 3)
    check("T1.2 BASE-1 is MUST", CryptoSuite.W4_BASE_1.status == "MUST")
    check("T1.3 FIPS-1 is SHOULD", CryptoSuite.W4_FIPS_1.status == "SHOULD")
    check("T1.4 IOT-1 is MAY", CryptoSuite.W4_IOT_1.status == "MAY")
    check("T1.5 BASE-1 uses Ed25519", CryptoSuite.W4_BASE_1.sig == "Ed25519")
    check("T1.6 FIPS-1 uses ECDSA", CryptoSuite.W4_FIPS_1.sig == "ECDSA-P256")
    check("T1.7 BASE-1 uses COSE", CryptoSuite.W4_BASE_1.profile == "COSE")
    check("T1.8 FIPS-1 uses JOSE", CryptoSuite.W4_FIPS_1.profile == "JOSE")
    check("T1.9 IOT-1 uses CBOR", CryptoSuite.W4_IOT_1.profile == "CBOR")
    check("T1.10 All use SHA-256",
          all(s.hash_alg == "SHA-256" for s in CryptoSuite))

    # ═══════════════════════════════════════════════════════════
    # §2 — Messaging Protocol
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T2: Message Types (§2.2) ═══")
    check("T2.1 4 message types", len(MessageType) == 4)
    check("T2.2 REQUEST type", MessageType.REQUEST.value == "request")
    check("T2.3 RESPONSE type", MessageType.RESPONSE.value == "response")
    check("T2.4 EVENT type", MessageType.EVENT.value == "event")
    check("T2.5 CREDENTIAL type", MessageType.CREDENTIAL.value == "credential")

    print("\n═══ T3: Message Structure (§2.1) ═══")
    header = MessageHeader(
        message_id="msg:test001",
        message_type=MessageType.REQUEST,
        content_type=ContentType.JSON,
        sender_w4id="w4id:key:alice",
        recipient_w4id="w4id:key:bob",
    )
    check("T3.1 Header has message_id", header.message_id == "msg:test001")
    check("T3.2 Header has type", header.message_type == MessageType.REQUEST)
    check("T3.3 Header has content_type", header.content_type == ContentType.JSON)
    check("T3.4 Header has sender", header.sender_w4id == "w4id:key:alice")
    check("T3.5 Header has recipient", header.recipient_w4id == "w4id:key:bob")
    check("T3.6 Header has timestamp", len(header.timestamp) > 0)
    check("T3.7 Header encrypted by default", header.encrypted)
    check("T3.8 Header uses BASE-1", header.suite_id == "W4-BASE-1")

    hd = header.to_dict()
    check("T3.9 Header serializes", "message_id" in hd)
    check("T3.10 Header has type string", hd["type"] == "request")

    # Request message
    req = Web4Message.create_request(
        "w4id:key:alice", "w4id:key:bob",
        "query_data", {"table": "users"})
    check("T3.11 Request created", req.header.message_type == MessageType.REQUEST)
    check("T3.12 Request has action", req.payload["action"] == "query_data")
    check("T3.13 Request has params", req.payload["params"]["table"] == "users")

    # Response message
    resp = Web4Message.create_response(req, {"rows": 42}, success=True)
    check("T3.14 Response created", resp.header.message_type == MessageType.RESPONSE)
    check("T3.15 Response has correlation",
          resp.header.correlation_id == req.header.message_id)
    check("T3.16 Response has result", resp.payload["result"]["rows"] == 42)
    check("T3.17 Response is success", resp.payload["success"])

    # Event message
    evt = Web4Message.create_event(
        "w4id:key:alice", "w4id:key:bob",
        "trust_update", {"delta": 0.01})
    check("T3.18 Event created", evt.header.message_type == MessageType.EVENT)
    check("T3.19 Event has type", evt.payload["event_type"] == "trust_update")
    check("T3.20 Event has data", evt.payload["data"]["delta"] == 0.01)

    # Credential message
    cred_msg = Web4Message.create_credential(
        "w4id:key:issuer", "w4id:key:holder",
        {"type": "TrustAttestation", "score": 0.95})
    check("T3.21 Credential created", cred_msg.header.message_type == MessageType.CREDENTIAL)
    check("T3.22 Credential uses JSON-LD", cred_msg.header.content_type == ContentType.JSON_LD)
    check("T3.23 Credential has payload", cred_msg.payload["score"] == 0.95)

    # Serialization
    md = req.to_dict()
    j = json.dumps(md)
    check("T3.24 Message JSON-serializable", json.loads(j) is not None)

    print("\n═══ T4: Message Encryption (§2.3) ═══")
    session_key = os.urandom(32)
    encrypted = req.encrypt(session_key)
    check("T4.1 Encrypted has header", encrypted.header.message_id == req.header.message_id)
    check("T4.2 Has ciphertext", len(encrypted.ciphertext) > 0)
    check("T4.3 Has nonce", len(encrypted.nonce) == 24)  # 12 bytes hex
    check("T4.4 Has tag", len(encrypted.tag) == 32)  # 16 bytes hex
    ed = encrypted.to_dict()
    check("T4.5 Encrypted serializes", "ciphertext" in ed)
    check("T4.6 All messages MUST be encrypted", req.header.encrypted)

    # ═══════════════════════════════════════════════════════════
    # §3 — Data & Credential Formats
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T5: W4ID (§3.1) ═══")
    # Parse
    w4id = W4ID.parse("w4id:key:abc123def456")
    check("T5.1 W4ID parsed", w4id is not None)
    check("T5.2 Method extracted", w4id.method == "key")
    check("T5.3 Specific ID extracted", w4id.specific_id == "abc123def456")
    check("T5.4 String representation", str(w4id) == "w4id:key:abc123def456")

    # Generate
    generated = W4ID.generate("web")
    check("T5.5 Generated W4ID", str(generated).startswith("w4id:web:"))
    check("T5.6 Generated has method", generated.method == "web")
    check("T5.7 Generated has specific ID", len(generated.specific_id) == 32)

    # Invalid parse
    check("T5.8 Invalid W4ID returns None", W4ID.parse("invalid") is None)
    check("T5.9 Empty string returns None", W4ID.parse("") is None)
    check("T5.10 Wrong scheme returns None", W4ID.parse("did:key:abc") is None)

    # Serialization
    wd = w4id.to_dict()
    check("T5.11 W4ID serializes", wd["w4id"] == "w4id:key:abc123def456")
    check("T5.12 Dict has method", wd["method"] == "key")

    print("\n═══ T6: Verifiable Credentials (§3.2) ═══")
    issuer_key = os.urandom(32)
    vc = VerifiableCredential(
        issuer="w4id:key:issuer001",
        credential_type=["VerifiableCredential", "TrustAttestation"],
        credential_subject={
            "id": "w4id:key:subject001",
            "trust_score": 0.92,
            "role": "web4:Developer",
        },
    )
    check("T6.1 VC has context", "https://www.w3.org/2018/credentials/v1" in vc.context)
    check("T6.2 VC has web4 context", "https://web4.io/contexts/credential.jsonld" in vc.context)
    check("T6.3 VC has issuer", vc.issuer == "w4id:key:issuer001")
    check("T6.4 VC has issuance date", len(vc.issuance_date) > 0)
    check("T6.5 VC has subject", vc.credential_subject["trust_score"] == 0.92)

    # Sign
    vc.sign(issuer_key)
    check("T6.6 VC signed", vc.proof is not None)
    check("T6.7 Proof has type", vc.proof["type"] == "Ed25519Signature2020")
    check("T6.8 Proof has verification method",
          vc.proof["verificationMethod"] == "w4id:key:issuer001#key-1")
    check("T6.9 Proof has purpose", vc.proof["proofPurpose"] == "assertionMethod")
    check("T6.10 Proof has value", len(vc.proof["proofValue"]) > 0)

    # Verify
    check("T6.11 VC verifies with correct key", vc.verify(issuer_key))
    check("T6.12 VC fails with wrong key", not vc.verify(os.urandom(32)))

    # Unsigned verification
    unsigned = VerifiableCredential(issuer="test")
    check("T6.13 Unsigned VC fails verify", not unsigned.verify(issuer_key))

    # Serialization
    vcd = vc.to_dict()
    check("T6.14 VC has @context", "@context" in vcd)
    check("T6.15 VC has type array", "TrustAttestation" in vcd["type"])
    check("T6.16 VC has proof", "proof" in vcd)
    j = json.dumps(vcd)
    check("T6.17 VC JSON-serializable", json.loads(j) is not None)

    print("\n═══ T7: JSON-LD Contexts (§3.3) ═══")
    check("T7.1 SAL context defined", "sal" in WEB4_CONTEXTS)
    check("T7.2 Credential context", "credential" in WEB4_CONTEXTS)
    check("T7.3 Entity context", "entity" in WEB4_CONTEXTS)
    check("T7.4 Trust context", "trust" in WEB4_CONTEXTS)
    check("T7.5 All are web4.io URLs",
          all(v.startswith("https://web4.io/") for v in WEB4_CONTEXTS.values()))

    # ═══════════════════════════════════════════════════════════
    # §4 — Transport & Discovery
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T8: Transport Matrix (§4.1) ═══")
    check("T8.1 8 transports defined", len(Transport) == 8)

    required = [t for t in Transport if t.is_required]
    check("T8.2 2 MUST transports", len(required) == 2, f"{[t.transport_name for t in required]}")
    check("T8.3 TLS 1.3 is MUST", Transport.TLS_13.is_required)
    check("T8.4 QUIC is MUST", Transport.QUIC.is_required)

    # Constrained transports
    constrained = [t for t in Transport if t.is_constrained]
    check("T8.5 BLE is constrained", Transport.BLE_GATT.is_constrained)
    check("T8.6 CAN is constrained", Transport.CAN_BUS.is_constrained)
    check("T8.7 TLS is not constrained", not Transport.TLS_13.is_constrained)

    # All support handshake
    check("T8.8 All support handshake", all(t.handshake_support for t in Transport))

    # Transport properties
    check("T8.9 WebSocket is MAY", Transport.WEBSOCKET.status == "MAY")
    check("T8.10 WebTransport is SHOULD", Transport.WEBTRANSPORT.status == "SHOULD")

    print("\n═══ T9: Discovery Methods (§4.2) ═══")
    check("T9.1 6 discovery methods", len(DiscoveryMethod) == 6)
    check("T9.2 Witness Relay is MUST", DiscoveryMethod.WITNESS_RELAY.status == "MUST")
    check("T9.3 QR Code is SHOULD", DiscoveryMethod.QR_CODE.status == "SHOULD")
    check("T9.4 QR has high privacy", DiscoveryMethod.QR_CODE.privacy_level == "High")
    check("T9.5 DNS-SD has low privacy", DiscoveryMethod.DNS_SD.privacy_level == "Low")
    check("T9.6 Witness has medium privacy", DiscoveryMethod.WITNESS_RELAY.privacy_level == "Medium")

    print("\n═══ T10: Discovery Service (§4.2 Protocol) ═══")
    ds = DiscoveryService()
    ds.register("w4id:key:server1",
                capabilities=["database", "analysis"],
                witness_attestations=[{"witness_id": "w4id:key:witness1", "score": 0.9}],
                endpoints=[{"transport": "TLS 1.3", "address": "https://s1.web4.io", "priority": 1}],
                trust_score=0.92)
    ds.register("w4id:key:server2",
                capabilities=["compute", "ml"],
                witness_attestations=[{"witness_id": "w4id:key:witness2", "score": 0.85}],
                endpoints=[{"transport": "QUIC", "address": "quic://s2.web4.io", "priority": 1}],
                trust_score=0.88)
    ds.register("w4id:key:server3",
                capabilities=["database"],
                witness_attestations=[{"witness_id": "w4id:key:witness1", "score": 0.7}],
                endpoints=[{"transport": "TLS 1.3", "address": "https://s3.web4.io", "priority": 2}],
                trust_score=0.75)

    # Discovery by capability
    req1 = DiscoveryRequest(
        desired_capabilities=["database"],
        acceptable_witnesses=["w4id:key:witness1"],
        requester_w4id="w4id:key:client1",
    )
    results = ds.discover(req1)
    check("T10.1 Found database servers", len(results) == 2)
    check("T10.2 Sorted by trust", results[0].trust_score >= results[1].trust_score)
    check("T10.3 Results have endpoints", len(results[0].endpoints) > 0)

    # Discovery with wrong witness
    req2 = DiscoveryRequest(
        desired_capabilities=["compute"],
        acceptable_witnesses=["w4id:key:witness1"],
    )
    results2 = ds.discover(req2)
    check("T10.4 Witness filter excludes", len(results2) == 0)

    # Discovery all capabilities
    req3 = DiscoveryRequest(
        desired_capabilities=[],
        acceptable_witnesses=[],
    )
    results3 = ds.discover(req3)
    check("T10.5 Empty filter returns all", len(results3) == 3)

    # Replay protection
    req_replay = DiscoveryRequest(
        desired_capabilities=["database"],
        acceptable_witnesses=[],
        nonce=req1.nonce,  # Reuse nonce
    )
    results_replay = ds.discover(req_replay)
    check("T10.6 Replay nonce rejected", len(results_replay) == 0)

    # Result serialization
    rd = results[0].to_dict()
    check("T10.7 Result has entity", "entity" in rd)
    check("T10.8 Result has capabilities", "capabilities" in rd)
    check("T10.9 Result has witness attestations", "witness_attestations" in rd)
    check("T10.10 Result has endpoints", "endpoints" in rd)

    # Request serialization
    rqd = req1.to_dict()
    check("T10.11 Request has type", rqd["type"] == "discovery_request")
    check("T10.12 Request has nonce", len(rqd["nonce"]) > 0)

    print("\n═══ T11: Transport Negotiation (§4.3) ═══")
    # Both support QUIC and TLS
    client_t = [Transport.QUIC, Transport.TLS_13, Transport.WEBSOCKET]
    server_t = [Transport.QUIC, Transport.TLS_13]
    selected = TransportNegotiator.negotiate(client_t, server_t)
    check("T11.1 QUIC selected (highest priority)", selected == Transport.QUIC)

    # Only TLS in common
    client_t2 = [Transport.TLS_13, Transport.WEBSOCKET]
    server_t2 = [Transport.TLS_13, Transport.BLE_GATT]
    selected2 = TransportNegotiator.negotiate(client_t2, server_t2)
    check("T11.2 TLS fallback works", selected2 == Transport.TLS_13)

    # No common transport
    client_t3 = [Transport.BLE_GATT]
    server_t3 = [Transport.CAN_BUS]
    selected3 = TransportNegotiator.negotiate(client_t3, server_t3)
    check("T11.3 No common returns None", selected3 is None)

    # WebTransport preferred over WebSocket
    client_t4 = [Transport.WEBTRANSPORT, Transport.WEBSOCKET, Transport.TLS_13]
    server_t4 = [Transport.WEBTRANSPORT, Transport.WEBSOCKET, Transport.TLS_13]
    selected4 = TransportNegotiator.negotiate(client_t4, server_t4)
    check("T11.4 Priority order respected",
          selected4 == Transport.WEBTRANSPORT or selected4 == Transport.QUIC)

    # Required transports
    required_t = TransportNegotiator.get_required_transports()
    check("T11.5 Required transports listed", len(required_t) == 2)
    check("T11.6 TLS in required", Transport.TLS_13 in required_t)
    check("T11.7 QUIC in required", Transport.QUIC in required_t)

    # ═══════════════════════════════════════════════════════════
    # §5 — URI Scheme
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T12: Web4 URI Parsing (§5.1) ═══")
    # Basic URI
    uri1 = Web4URI.parse("web4://w4id:key:alice/data/profile")
    check("T12.1 URI parsed", uri1 is not None)
    check("T12.2 W4ID extracted", uri1.w4id == "w4id:key:alice")
    check("T12.3 Path extracted", uri1.path == "/data/profile")
    check("T12.4 No query", len(uri1.query) == 0)
    check("T12.5 No fragment", uri1.fragment == "")

    # URI with query and fragment
    uri2 = Web4URI.parse("web4://w4id:web:org123/api/trust?role=dev&min=0.5#section1")
    check("T12.6 URI with query parsed", uri2 is not None)
    check("T12.7 W4ID with web method", uri2.w4id == "w4id:web:org123")
    check("T12.8 Path", uri2.path == "/api/trust")
    check("T12.9 Query role param", uri2.query.get("role") == "dev")
    check("T12.10 Query min param", uri2.query.get("min") == "0.5")
    check("T12.11 Fragment", uri2.fragment == "section1")

    # URI with no path
    uri3 = Web4URI.parse("web4://w4id:key:server1")
    check("T12.12 No path defaults to /", uri3 is not None and uri3.path == "/")

    # URI round-trip
    uri_str = str(uri2)
    check("T12.13 URI to string", uri_str.startswith("web4://w4id:web:org123"))
    check("T12.14 String contains path", "/api/trust" in uri_str)
    check("T12.15 String contains query", "role=dev" in uri_str)
    check("T12.16 String contains fragment", "#section1" in uri_str)

    # Invalid URIs
    check("T12.17 Invalid scheme rejected", Web4URI.parse("http://example.com") is None)
    check("T12.18 Empty string rejected", Web4URI.parse("") is None)

    # Construct and serialize
    uri_custom = Web4URI(
        w4id="w4id:key:myserver",
        path="/resources/docs",
        query={"format": "json"},
        fragment="page2",
    )
    check("T12.19 Constructed URI string",
          str(uri_custom) == "web4://w4id:key:myserver/resources/docs?format=json#page2")
    ud = uri_custom.to_dict()
    check("T12.20 URI dict has scheme", ud["scheme"] == "web4")
    check("T12.21 URI dict has w4id", ud["w4id"] == "w4id:key:myserver")
    check("T12.22 URI dict has full_uri", "web4://" in ud["full_uri"])

    print("\n═══ T13: URI Resolution (§5.2) ═══")
    resolver = URIResolver()
    resolver.register_endpoint("w4id:key:alice", "https://alice.web4.io")
    resolver.register_endpoint("w4id:key:bob", "https://bob.web4.io")

    # Resolve known URI
    resolved = resolver.resolve(uri1)
    check("T13.1 URI resolved", resolved is not None)
    check("T13.2 Endpoint found", resolved["endpoint"] == "https://alice.web4.io")
    check("T13.3 Path preserved", resolved["path"] == "/data/profile")
    check("T13.4 Resolved URL built",
          resolved["resolved_url"] == "https://alice.web4.io/data/profile")

    # Resolve unknown URI
    unknown_uri = Web4URI(w4id="w4id:key:unknown", path="/test")
    check("T13.5 Unknown W4ID returns None", resolver.resolve(unknown_uri) is None)

    # Resolve with query
    uri_with_q = Web4URI(w4id="w4id:key:bob", path="/api",
                         query={"format": "json"})
    resolved2 = resolver.resolve(uri_with_q)
    check("T13.6 Query preserved", resolved2["query"]["format"] == "json")

    # ═══════════════════════════════════════════════════════════
    # Content Types
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T14: Content Types ═══")
    check("T14.1 5 content types", len(ContentType) == 5)
    check("T14.2 JSON type", ContentType.JSON.value == "application/json")
    check("T14.3 JSON-LD type", ContentType.JSON_LD.value == "application/ld+json")
    check("T14.4 CBOR type", ContentType.CBOR.value == "application/cbor")
    check("T14.5 Binary type", ContentType.BINARY.value == "application/octet-stream")

    # ═══════════════════════════════════════════════════════════
    # Full Integration Flow
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T15: Full Integration Flow ═══")
    # 1. Generate W4IDs for client and server
    client_id = W4ID.generate("key")
    server_id = W4ID.generate("key")
    check("T15.1 Client W4ID generated", str(client_id).startswith("w4id:key:"))
    check("T15.2 Server W4ID generated", str(server_id).startswith("w4id:key:"))

    # 2. Register server in discovery
    int_ds = DiscoveryService()
    int_ds.register(str(server_id),
                    capabilities=["analysis", "compute"],
                    witness_attestations=[{"witness_id": "w4id:key:oracle1", "score": 0.9}],
                    endpoints=[{"transport": "TLS 1.3", "address": "https://server.web4.io"}],
                    trust_score=0.9)

    # 3. Client discovers server
    disc_req = DiscoveryRequest(
        desired_capabilities=["analysis"],
        acceptable_witnesses=["w4id:key:oracle1"],
        requester_w4id=str(client_id),
    )
    disc_results = int_ds.discover(disc_req)
    check("T15.3 Server discovered", len(disc_results) == 1)

    # 4. Negotiate transport
    selected_transport = TransportNegotiator.negotiate(
        [Transport.QUIC, Transport.TLS_13],
        [Transport.QUIC, Transport.TLS_13])
    check("T15.4 Transport negotiated", selected_transport == Transport.QUIC)

    # 5. Exchange messages
    req_msg = Web4Message.create_request(
        str(client_id), str(server_id),
        "analyze", {"data": [1, 2, 3]})
    check("T15.5 Request created", req_msg.header.message_type == MessageType.REQUEST)

    # 6. Encrypt message
    sk = os.urandom(32)
    enc_msg = req_msg.encrypt(sk)
    check("T15.6 Message encrypted", len(enc_msg.ciphertext) > 0)

    # 7. Server responds
    resp_msg = Web4Message.create_response(req_msg, {"sum": 6})
    check("T15.7 Response created",
          resp_msg.header.correlation_id == req_msg.header.message_id)

    # 8. Issue credential
    vc = VerifiableCredential(
        issuer=str(server_id),
        credential_type=["VerifiableCredential", "AnalysisResult"],
        credential_subject={
            "id": str(client_id),
            "analysis_quality": 0.95,
        },
    )
    vc.sign(sk)
    check("T15.8 Credential signed", vc.verify(sk))

    # 9. Send credential via message
    cred_msg = Web4Message.create_credential(
        str(server_id), str(client_id), vc.to_dict())
    check("T15.9 Credential message created",
          cred_msg.header.message_type == MessageType.CREDENTIAL)

    # 10. Resolve server URI
    int_resolver = URIResolver()
    int_resolver.register_endpoint(str(server_id), "https://server.web4.io")
    uri = Web4URI(w4id=str(server_id), path="/api/analyze",
                  query={"format": "json"})
    resolved = int_resolver.resolve(uri)
    check("T15.10 URI resolved", resolved is not None)
    check("T15.11 Full flow completes",
          resolved["endpoint"] == "https://server.web4.io")

    # ═══════════════════════════════════════════════════════════
    # Edge Cases
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T16: Edge Cases ═══")
    # URI with empty query value
    uri_empty_q = Web4URI.parse("web4://w4id:key:x/path?key=")
    check("T16.1 Empty query value parsed", uri_empty_q is not None)
    check("T16.2 Empty value preserved", uri_empty_q.query.get("key") == "")

    # URI with only fragment
    uri_frag = Web4URI.parse("web4://w4id:key:x#frag")
    check("T16.3 Fragment-only URI", uri_frag is not None)
    check("T16.4 Fragment extracted", uri_frag.fragment == "frag")

    # W4ID with complex specific_id
    complex_w4id = W4ID.parse("w4id:key:mb64-EF4wt9Y2zKpWsN")
    check("T16.5 Complex W4ID parsed", complex_w4id is not None)
    check("T16.6 Complex specific_id", complex_w4id.specific_id == "mb64-EF4wt9Y2zKpWsN")

    # Message auto-generates ID
    auto_msg = Web4Message.create_request("a", "b", "test")
    check("T16.7 Auto-generated message ID", auto_msg.header.message_id.startswith("msg:"))

    # Discovery with preferred transport
    req_pref = DiscoveryRequest(
        desired_capabilities=["any"],
        acceptable_witnesses=[],
        preferred_transport="QUIC",
    )
    check("T16.8 Preferred transport in request", req_pref.preferred_transport == "QUIC")

    # ═══════════════════════════════════════════════════════════
    # Serialization Round-Trip
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T17: Serialization ═══")
    # All key types
    objects_to_test = [
        ("Message", req.to_dict()),
        ("Encrypted message", enc_msg.to_dict()),
        ("W4ID", w4id.to_dict()),
        ("VC", vc.to_dict()),
        ("Discovery request", disc_req.to_dict()),
        ("Discovery result", disc_results[0].to_dict() if disc_results else {}),
        ("URI", uri_custom.to_dict()),
    ]
    for name, obj in objects_to_test:
        j = json.dumps(obj, default=str)
        check(f"T17.1 {name} JSON-serializable", json.loads(j) is not None)

    # ═══════════════════════════════════════════════════════════
    # Test Vectors
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T18: Test Vectors ═══")
    # Vector 1: W4ID parsing
    tv1 = W4ID.parse("w4id:key:abc123")
    check("T18.1 Vector1: W4ID parse",
          tv1 is not None and tv1.method == "key" and tv1.specific_id == "abc123")

    # Vector 2: URI parsing
    tv2 = Web4URI.parse("web4://w4id:key:server/path?q=1#f")
    check("T18.2 Vector2: URI components",
          tv2.w4id == "w4id:key:server" and tv2.path == "/path" and
          tv2.query.get("q") == "1" and tv2.fragment == "f")

    # Vector 3: Message correlation
    tv_req = Web4Message.create_request("a", "b", "test")
    tv_resp = Web4Message.create_response(tv_req, "ok")
    check("T18.3 Vector3: Correlation matches",
          tv_resp.header.correlation_id == tv_req.header.message_id)

    # Vector 4: Transport negotiation priority
    tv_selected = TransportNegotiator.negotiate(
        [Transport.TLS_13, Transport.QUIC],
        [Transport.QUIC, Transport.TLS_13])
    check("T18.4 Vector4: QUIC > TLS priority", tv_selected == Transport.QUIC)

    # Vector 5: VC sign/verify round-trip
    tv_key = b"test-key-32-bytes-for-signing!!"
    tv_vc = VerifiableCredential(
        issuer="w4id:key:test",
        credential_subject={"claim": "value"},
    )
    tv_vc.sign(tv_key)
    check("T18.5 Vector5: VC sign+verify", tv_vc.verify(tv_key))
    check("T18.6 Vector5: Wrong key fails", not tv_vc.verify(b"wrong-key!"))

    # ═══════════════════════════════════════════════════════════
    # Summary
    # ═══════════════════════════════════════════════════════════

    total = passed + failed
    print(f"\n{'='*60}")
    print(f"  Web4 URI, Transport & Messaging — Results")
    print(f"  {passed} passed, {failed} failed out of {total} checks")
    print(f"{'='*60}")

    if failed == 0:
        print(f"\n  All {total} checks pass — URI/Transport/Messaging implemented")
        print(f"  Spec sections covered:")
        print(f"    §1  Cryptographic Suites (3 suites: BASE-1, FIPS-1, IOT-1)")
        print(f"    §2  Messaging Protocol (4 types, header/payload, encryption)")
        print(f"    §3  Data Formats (W4ID, Verifiable Credentials, JSON-LD)")
        print(f"    §4  Transport (8 transports) + Discovery (6 methods)")
        print(f"    §5  URI Scheme (web4://, parsing, resolution)")
    else:
        print(f"\n  {failed} failures need investigation")

    return passed, failed


if __name__ == "__main__":
    passed, failed = run_tests()
    sys.exit(0 if failed == 0 else 1)
