"""
Wire Protocol & Tensor Serialization
======================================

Implements canonical binary formats for Web4 cross-federation messages:
trust tensor encoding, ATP packet framing, message envelopes with
integrity, version negotiation, compression, roundtrip fuzz testing,
and protocol handshake.

Sections:
  S1  — Primitive Encoding (varint, float, string)
  S2  — Trust Tensor Serialization
  S3  — ATP Packet Encoding
  S4  — Message Envelope & Integrity
  S5  — Version Negotiation
  S6  — Compression
  S7  — Batch Encoding
  S8  — Roundtrip Fuzz Testing
  S9  — Protocol Handshake
  S10 — Error Recovery
  S11 — Performance & Throughput
"""

from __future__ import annotations
import math
import random
import struct
import hashlib
import zlib
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any, Set
from enum import Enum, IntEnum
from io import BytesIO


# ============================================================
# S1 — Primitive Encoding (varint, float, string)
# ============================================================

def encode_varint(value: int) -> bytes:
    """Encode unsigned integer as variable-length bytes (LEB128)."""
    if value < 0:
        raise ValueError("varint must be non-negative")
    result = bytearray()
    while value > 0x7f:
        result.append((value & 0x7f) | 0x80)
        value >>= 7
    result.append(value & 0x7f)
    return bytes(result)


def decode_varint(data: bytes, offset: int = 0) -> Tuple[int, int]:
    """Decode varint, return (value, bytes_consumed)."""
    value = 0
    shift = 0
    consumed = 0
    while offset + consumed < len(data):
        byte = data[offset + consumed]
        value |= (byte & 0x7f) << shift
        consumed += 1
        if not (byte & 0x80):
            break
        shift += 7
    return value, consumed


def encode_float64(value: float) -> bytes:
    """Encode as IEEE 754 double (8 bytes, big-endian)."""
    return struct.pack(">d", value)


def decode_float64(data: bytes, offset: int = 0) -> Tuple[float, int]:
    return struct.unpack_from(">d", data, offset)[0], 8


def encode_string(value: str) -> bytes:
    """Length-prefixed UTF-8 string."""
    encoded = value.encode("utf-8")
    return encode_varint(len(encoded)) + encoded


def decode_string(data: bytes, offset: int = 0) -> Tuple[str, int]:
    length, consumed = decode_varint(data, offset)
    start = offset + consumed
    return data[start:start + length].decode("utf-8"), consumed + length


def encode_bytes_field(value: bytes) -> bytes:
    """Length-prefixed raw bytes."""
    return encode_varint(len(value)) + value


def decode_bytes_field(data: bytes, offset: int = 0) -> Tuple[bytes, int]:
    length, consumed = decode_varint(data, offset)
    start = offset + consumed
    return data[start:start + length], consumed + length


def test_section_1():
    checks = []

    # Varint encoding
    checks.append(("varint_0", encode_varint(0) == b'\x00'))
    checks.append(("varint_127", encode_varint(127) == b'\x7f'))
    checks.append(("varint_128", encode_varint(128) == b'\x80\x01'))
    checks.append(("varint_300", encode_varint(300) == b'\xac\x02'))

    # Varint roundtrip
    for val in [0, 1, 127, 128, 255, 1000, 65535, 1000000]:
        decoded, consumed = decode_varint(encode_varint(val))
        checks.append((f"varint_rt_{val}", decoded == val))

    # Float64 roundtrip
    for val in [0.0, 1.0, -1.0, 3.14159, 1e-10, float('inf')]:
        decoded, _ = decode_float64(encode_float64(val))
        if math.isinf(val):
            checks.append((f"float_rt_inf", math.isinf(decoded)))
        else:
            checks.append((f"float_rt_{val}", abs(decoded - val) < 1e-15))

    # String roundtrip
    for s in ["", "hello", "Web4 Trust™", "日本語"]:
        decoded, _ = decode_string(encode_string(s))
        checks.append((f"string_rt_{len(s)}", decoded == s))

    return checks


# ============================================================
# S2 — Trust Tensor Serialization
# ============================================================

class TensorFieldTag(IntEnum):
    TALENT = 1
    TRAINING = 2
    TEMPERAMENT = 3
    COMPOSITE = 4
    CONFIDENCE = 5
    VERSION = 6


@dataclass
class TrustTensor:
    talent: float
    training: float
    temperament: float
    confidence: float = 1.0
    version: int = 1

    @property
    def composite(self) -> float:
        return (self.talent + self.training + self.temperament) / 3.0

    def encode(self) -> bytes:
        buf = BytesIO()
        # Tag-length-value format
        for tag, value in [
            (TensorFieldTag.TALENT, self.talent),
            (TensorFieldTag.TRAINING, self.training),
            (TensorFieldTag.TEMPERAMENT, self.temperament),
            (TensorFieldTag.CONFIDENCE, self.confidence),
        ]:
            buf.write(encode_varint(tag))
            buf.write(encode_float64(value))
        buf.write(encode_varint(TensorFieldTag.VERSION))
        buf.write(encode_varint(self.version))
        return buf.getvalue()

    @classmethod
    def decode(cls, data: bytes) -> 'TrustTensor':
        offset = 0
        fields = {}
        while offset < len(data):
            tag, consumed = decode_varint(data, offset)
            offset += consumed
            if tag == TensorFieldTag.VERSION:
                val, consumed = decode_varint(data, offset)
                fields['version'] = val
            else:
                val, consumed = decode_float64(data, offset)
                fields[TensorFieldTag(tag).name.lower()] = val
            offset += consumed
        return cls(
            talent=fields.get('talent', 0.0),
            training=fields.get('training', 0.0),
            temperament=fields.get('temperament', 0.0),
            confidence=fields.get('confidence', 1.0),
            version=fields.get('version', 1),
        )


def test_section_2():
    checks = []

    t = TrustTensor(talent=0.8, training=0.6, temperament=0.7, confidence=0.95)
    encoded = t.encode()

    checks.append(("encoded_bytes", len(encoded) > 0))
    checks.append(("compact_size", len(encoded) < 50))  # should be ~37 bytes

    decoded = TrustTensor.decode(encoded)
    checks.append(("rt_talent", abs(decoded.talent - 0.8) < 1e-10))
    checks.append(("rt_training", abs(decoded.training - 0.6) < 1e-10))
    checks.append(("rt_temperament", abs(decoded.temperament - 0.7) < 1e-10))
    checks.append(("rt_confidence", abs(decoded.confidence - 0.95) < 1e-10))
    checks.append(("rt_version", decoded.version == 1))
    checks.append(("rt_composite", abs(decoded.composite - t.composite) < 1e-10))

    # Boundary values
    boundary = TrustTensor(0.0, 1.0, 0.5)
    decoded_b = TrustTensor.decode(boundary.encode())
    checks.append(("boundary_zero", decoded_b.talent == 0.0))
    checks.append(("boundary_one", decoded_b.training == 1.0))

    return checks


# ============================================================
# S3 — ATP Packet Encoding
# ============================================================

class ATPPacketType(IntEnum):
    TRANSFER = 1
    MINT = 2
    BURN = 3
    STAKE = 4
    REWARD = 5


@dataclass
class ATPPacket:
    packet_type: ATPPacketType
    from_entity: str
    to_entity: str
    amount: float
    fee: float
    nonce: int
    timestamp: float

    def encode(self) -> bytes:
        buf = BytesIO()
        buf.write(encode_varint(self.packet_type))
        buf.write(encode_string(self.from_entity))
        buf.write(encode_string(self.to_entity))
        buf.write(encode_float64(self.amount))
        buf.write(encode_float64(self.fee))
        buf.write(encode_varint(self.nonce))
        buf.write(encode_float64(self.timestamp))
        return buf.getvalue()

    @classmethod
    def decode(cls, data: bytes) -> 'ATPPacket':
        offset = 0
        ptype, consumed = decode_varint(data, offset); offset += consumed
        from_e, consumed = decode_string(data, offset); offset += consumed
        to_e, consumed = decode_string(data, offset); offset += consumed
        amount, consumed = decode_float64(data, offset); offset += consumed
        fee, consumed = decode_float64(data, offset); offset += consumed
        nonce, consumed = decode_varint(data, offset); offset += consumed
        timestamp, consumed = decode_float64(data, offset); offset += consumed
        return cls(ATPPacketType(ptype), from_e, to_e, amount, fee, nonce, timestamp)

    def content_hash(self) -> str:
        return hashlib.sha256(self.encode()).hexdigest()


def test_section_3():
    checks = []

    pkt = ATPPacket(
        packet_type=ATPPacketType.TRANSFER,
        from_entity="alice",
        to_entity="bob",
        amount=100.0,
        fee=5.0,
        nonce=12345,
        timestamp=1709136000.0,
    )

    encoded = pkt.encode()
    checks.append(("atp_encoded", len(encoded) > 0))
    checks.append(("atp_compact", len(encoded) < 100))

    decoded = ATPPacket.decode(encoded)
    checks.append(("atp_rt_type", decoded.packet_type == ATPPacketType.TRANSFER))
    checks.append(("atp_rt_from", decoded.from_entity == "alice"))
    checks.append(("atp_rt_to", decoded.to_entity == "bob"))
    checks.append(("atp_rt_amount", abs(decoded.amount - 100.0) < 1e-10))
    checks.append(("atp_rt_fee", abs(decoded.fee - 5.0) < 1e-10))
    checks.append(("atp_rt_nonce", decoded.nonce == 12345))

    # Hash determinism
    checks.append(("hash_deterministic", pkt.content_hash() == ATPPacket.decode(encoded).content_hash()))

    return checks


# ============================================================
# S4 — Message Envelope & Integrity
# ============================================================

class MessageType(IntEnum):
    TRUST_UPDATE = 1
    ATP_TRANSFER = 2
    DELEGATION = 3
    CONSENSUS = 4
    HEARTBEAT = 5


@dataclass
class MessageEnvelope:
    message_type: MessageType
    sender: str
    federation_id: str
    payload: bytes
    sequence: int = 0

    def encode(self) -> bytes:
        buf = BytesIO()
        # Magic bytes
        buf.write(b'W4')
        # Version
        buf.write(encode_varint(1))
        # Type
        buf.write(encode_varint(self.message_type))
        # Sender
        buf.write(encode_string(self.sender))
        # Federation
        buf.write(encode_string(self.federation_id))
        # Sequence
        buf.write(encode_varint(self.sequence))
        # Payload
        buf.write(encode_bytes_field(self.payload))
        # Integrity: SHA-256 over all preceding bytes
        content = buf.getvalue()
        mac = hashlib.sha256(content).digest()
        buf.write(mac)
        return buf.getvalue()

    @classmethod
    def decode(cls, data: bytes) -> Tuple['MessageEnvelope', bool]:
        """Decode and verify. Returns (envelope, integrity_ok)."""
        if data[:2] != b'W4':
            raise ValueError("Invalid magic bytes")

        # Integrity check: last 32 bytes are SHA-256
        content = data[:-32]
        mac = data[-32:]
        expected_mac = hashlib.sha256(content).digest()
        integrity_ok = mac == expected_mac

        if not integrity_ok:
            # Don't attempt to decode corrupted content
            return cls(MessageType.HEARTBEAT, "", "", b"", 0), False

        offset = 2
        version, consumed = decode_varint(content, offset); offset += consumed
        msg_type, consumed = decode_varint(content, offset); offset += consumed
        sender, consumed = decode_string(content, offset); offset += consumed
        fed_id, consumed = decode_string(content, offset); offset += consumed
        seq, consumed = decode_varint(content, offset); offset += consumed
        payload, consumed = decode_bytes_field(content, offset); offset += consumed

        return cls(MessageType(msg_type), sender, fed_id, payload, seq), integrity_ok


def test_section_4():
    checks = []

    tensor = TrustTensor(0.8, 0.6, 0.7)
    env = MessageEnvelope(
        message_type=MessageType.TRUST_UPDATE,
        sender="alice",
        federation_id="fed-001",
        payload=tensor.encode(),
        sequence=42,
    )

    encoded = env.encode()
    checks.append(("envelope_has_magic", encoded[:2] == b'W4'))

    decoded, integrity = MessageEnvelope.decode(encoded)
    checks.append(("integrity_ok", integrity))
    checks.append(("rt_sender", decoded.sender == "alice"))
    checks.append(("rt_fed", decoded.federation_id == "fed-001"))
    checks.append(("rt_seq", decoded.sequence == 42))

    # Payload is trust tensor
    inner = TrustTensor.decode(decoded.payload)
    checks.append(("inner_tensor", abs(inner.talent - 0.8) < 1e-10))

    # Tamper detection
    tampered = bytearray(encoded)
    tampered[10] ^= 0xff  # flip a byte
    _, tampered_ok = MessageEnvelope.decode(bytes(tampered))
    checks.append(("tamper_detected", not tampered_ok))

    return checks


# ============================================================
# S5 — Version Negotiation
# ============================================================

@dataclass
class VersionCapability:
    min_version: int = 1
    max_version: int = 1
    supported_types: Set[MessageType] = field(default_factory=lambda: set(MessageType))
    extensions: Set[str] = field(default_factory=set)

    def negotiate(self, other: 'VersionCapability') -> Optional[int]:
        """Find highest mutually supported version."""
        overlap_min = max(self.min_version, other.min_version)
        overlap_max = min(self.max_version, other.max_version)
        if overlap_min > overlap_max:
            return None
        return overlap_max

    def common_types(self, other: 'VersionCapability') -> Set[MessageType]:
        return self.supported_types & other.supported_types

    def common_extensions(self, other: 'VersionCapability') -> Set[str]:
        return self.extensions & other.extensions


def test_section_5():
    checks = []

    v1 = VersionCapability(min_version=1, max_version=3,
                           supported_types={MessageType.TRUST_UPDATE, MessageType.ATP_TRANSFER},
                           extensions={"compression", "batching"})
    v2 = VersionCapability(min_version=2, max_version=4,
                           supported_types={MessageType.ATP_TRANSFER, MessageType.CONSENSUS},
                           extensions={"compression", "streaming"})

    # Version negotiation
    agreed = v1.negotiate(v2)
    checks.append(("version_3", agreed == 3))

    # Common types
    common = v1.common_types(v2)
    checks.append(("common_atp", MessageType.ATP_TRANSFER in common))
    checks.append(("not_common_trust", MessageType.TRUST_UPDATE not in common))

    # Common extensions
    common_ext = v1.common_extensions(v2)
    checks.append(("common_compression", "compression" in common_ext))
    checks.append(("no_streaming", "streaming" not in common_ext))

    # No overlap
    v3 = VersionCapability(min_version=5, max_version=6)
    checks.append(("no_overlap", v1.negotiate(v3) is None))

    # Same version
    v4 = VersionCapability(min_version=1, max_version=1)
    checks.append(("exact_match", v1.negotiate(v4) == 1))

    return checks


# ============================================================
# S6 — Compression
# ============================================================

def compress_payload(data: bytes, level: int = 6) -> Tuple[bytes, float]:
    """Compress payload with zlib. Returns (compressed, ratio)."""
    compressed = zlib.compress(data, level)
    ratio = len(compressed) / len(data) if len(data) > 0 else 1.0
    return compressed, ratio


def decompress_payload(data: bytes) -> bytes:
    return zlib.decompress(data)


def auto_compress(data: bytes, threshold: float = 0.9) -> Tuple[bytes, bool]:
    """Only compress if ratio < threshold (compression actually helps)."""
    if len(data) < 32:
        return data, False
    compressed, ratio = compress_payload(data)
    if ratio < threshold:
        return compressed, True
    return data, False


def test_section_6():
    checks = []

    # Repetitive data compresses well
    data = b"trust_tensor_update " * 100
    compressed, ratio = compress_payload(data)
    checks.append(("compresses", ratio < 0.2))

    # Roundtrip
    decompressed = decompress_payload(compressed)
    checks.append(("decompress_match", decompressed == data))

    # Random data doesn't compress well
    random_data = bytes(random.getrandbits(8) for _ in range(1000))
    _, ratio_random = compress_payload(random_data)
    checks.append(("random_ratio_high", ratio_random > 0.8))

    # Auto-compress skips small data
    small, was_compressed = auto_compress(b"tiny")
    checks.append(("skip_small", not was_compressed))

    # Auto-compress uses compression when beneficial
    big_repetitive = b"x" * 1000
    big_compressed, was = auto_compress(big_repetitive)
    checks.append(("auto_compresses", was))

    # Auto-compress skips when not beneficial
    random_big = bytes(random.getrandbits(8) for _ in range(1000))
    _, was_random = auto_compress(random_big, threshold=0.5)
    checks.append(("skip_random", not was_random))

    return checks


# ============================================================
# S7 — Batch Encoding
# ============================================================

@dataclass
class MessageBatch:
    """Batch multiple messages for efficient wire transport."""
    messages: List[MessageEnvelope] = field(default_factory=list)

    def encode(self) -> bytes:
        buf = BytesIO()
        buf.write(b'W4B')  # batch magic
        buf.write(encode_varint(len(self.messages)))
        for msg in self.messages:
            encoded_msg = msg.encode()
            buf.write(encode_bytes_field(encoded_msg))
        # Batch integrity
        content = buf.getvalue()
        buf.write(hashlib.sha256(content).digest())
        return buf.getvalue()

    @classmethod
    def decode(cls, data: bytes) -> Tuple['MessageBatch', bool]:
        if data[:3] != b'W4B':
            raise ValueError("Invalid batch magic")

        content = data[:-32]
        mac = data[-32:]
        integrity_ok = hashlib.sha256(content).digest() == mac

        offset = 3
        count, consumed = decode_varint(content, offset); offset += consumed

        messages = []
        for _ in range(count):
            msg_bytes, consumed = decode_bytes_field(content, offset); offset += consumed
            msg, _ = MessageEnvelope.decode(msg_bytes)
            messages.append(msg)

        return cls(messages), integrity_ok


def test_section_7():
    checks = []

    batch = MessageBatch()
    for i in range(10):
        tensor = TrustTensor(random.random(), random.random(), random.random())
        env = MessageEnvelope(
            message_type=MessageType.TRUST_UPDATE,
            sender=f"entity_{i}",
            federation_id="fed-001",
            payload=tensor.encode(),
            sequence=i,
        )
        batch.messages.append(env)

    encoded = batch.encode()
    checks.append(("batch_magic", encoded[:3] == b'W4B'))

    decoded, integrity = MessageBatch.decode(encoded)
    checks.append(("batch_integrity", integrity))
    checks.append(("batch_count", len(decoded.messages) == 10))
    checks.append(("batch_sender", decoded.messages[5].sender == "entity_5"))

    # Batch is more compact than individual messages
    individual_size = sum(len(msg.encode()) for msg in batch.messages)
    batch_size = len(encoded)
    # Batch adds batch header + length prefixes but saves nothing on compression
    # However batch has only ONE integrity hash instead of 10
    checks.append(("batch_overhead_small", batch_size < individual_size * 1.2))

    # Tamper detection
    tampered = bytearray(encoded)
    tampered[20] ^= 0xff
    _, tampered_ok = MessageBatch.decode(bytes(tampered))
    checks.append(("batch_tamper_detected", not tampered_ok))

    return checks


# ============================================================
# S8 — Roundtrip Fuzz Testing
# ============================================================

def fuzz_trust_tensor(n_iterations: int = 100, seed: int = 42) -> Tuple[int, int]:
    """Property-based roundtrip testing for trust tensors."""
    random.seed(seed)
    passed = 0
    failed = 0

    for _ in range(n_iterations):
        t = TrustTensor(
            talent=random.uniform(0.0, 1.0),
            training=random.uniform(0.0, 1.0),
            temperament=random.uniform(0.0, 1.0),
            confidence=random.uniform(0.0, 1.0),
            version=random.randint(1, 100),
        )
        encoded = t.encode()
        decoded = TrustTensor.decode(encoded)

        if (abs(decoded.talent - t.talent) < 1e-10 and
            abs(decoded.training - t.training) < 1e-10 and
            abs(decoded.temperament - t.temperament) < 1e-10 and
            abs(decoded.confidence - t.confidence) < 1e-10 and
            decoded.version == t.version):
            passed += 1
        else:
            failed += 1

    return passed, failed


def fuzz_atp_packet(n_iterations: int = 100, seed: int = 42) -> Tuple[int, int]:
    """Property-based roundtrip testing for ATP packets."""
    random.seed(seed)
    passed = 0
    failed = 0
    names = ["alice", "bob", "charlie", "dave", "eve", "frank"]

    for _ in range(n_iterations):
        pkt = ATPPacket(
            packet_type=random.choice(list(ATPPacketType)),
            from_entity=random.choice(names),
            to_entity=random.choice(names),
            amount=random.uniform(0.01, 10000.0),
            fee=random.uniform(0.0, 500.0),
            nonce=random.randint(0, 2**32),
            timestamp=random.uniform(1e9, 2e9),
        )
        encoded = pkt.encode()
        decoded = ATPPacket.decode(encoded)

        if (decoded.packet_type == pkt.packet_type and
            decoded.from_entity == pkt.from_entity and
            decoded.to_entity == pkt.to_entity and
            abs(decoded.amount - pkt.amount) < 1e-10 and
            abs(decoded.fee - pkt.fee) < 1e-10 and
            decoded.nonce == pkt.nonce):
            passed += 1
        else:
            failed += 1

    return passed, failed


def fuzz_envelope(n_iterations: int = 50, seed: int = 42) -> Tuple[int, int]:
    """Roundtrip test for message envelopes with random payloads."""
    random.seed(seed)
    passed = 0
    failed = 0

    for i in range(n_iterations):
        payload = bytes(random.getrandbits(8) for _ in range(random.randint(10, 200)))
        env = MessageEnvelope(
            message_type=random.choice(list(MessageType)),
            sender=f"entity_{random.randint(0, 99)}",
            federation_id=f"fed-{random.randint(1, 10):03d}",
            payload=payload,
            sequence=i,
        )
        encoded = env.encode()
        decoded, integrity = MessageEnvelope.decode(encoded)

        if (integrity and
            decoded.sender == env.sender and
            decoded.federation_id == env.federation_id and
            decoded.payload == env.payload and
            decoded.sequence == env.sequence):
            passed += 1
        else:
            failed += 1

    return passed, failed


def test_section_8():
    checks = []

    # Fuzz trust tensors
    tp, tf = fuzz_trust_tensor(200)
    checks.append(("fuzz_tensor_200", tp == 200 and tf == 0))

    # Fuzz ATP packets
    ap, af = fuzz_atp_packet(200)
    checks.append(("fuzz_atp_200", ap == 200 and af == 0))

    # Fuzz envelopes
    ep, ef = fuzz_envelope(100)
    checks.append(("fuzz_envelope_100", ep == 100 and ef == 0))

    # Edge cases
    edge = TrustTensor(0.0, 0.0, 0.0, 0.0, 1)
    decoded = TrustTensor.decode(edge.encode())
    checks.append(("edge_zeros", decoded.talent == 0.0 and decoded.training == 0.0))

    max_t = TrustTensor(1.0, 1.0, 1.0, 1.0, 999)
    decoded_max = TrustTensor.decode(max_t.encode())
    checks.append(("edge_ones", decoded_max.talent == 1.0 and decoded_max.version == 999))

    return checks


# ============================================================
# S9 — Protocol Handshake
# ============================================================

@dataclass
class HandshakeRequest:
    sender: str
    federation_id: str
    capability: VersionCapability
    challenge: bytes = field(default_factory=lambda: bytes(random.getrandbits(8) for _ in range(32)))

    def encode(self) -> bytes:
        buf = BytesIO()
        buf.write(b'W4H')  # handshake magic
        buf.write(encode_string(self.sender))
        buf.write(encode_string(self.federation_id))
        buf.write(encode_varint(self.capability.min_version))
        buf.write(encode_varint(self.capability.max_version))
        buf.write(encode_varint(len(self.capability.supported_types)))
        for t in sorted(self.capability.supported_types, key=lambda x: x.value):
            buf.write(encode_varint(t))
        buf.write(encode_bytes_field(self.challenge))
        return buf.getvalue()


@dataclass
class HandshakeResponse:
    responder: str
    agreed_version: Optional[int]
    common_types: Set[MessageType]
    challenge_response: bytes  # SHA-256(challenge)
    accepted: bool

    def verify_challenge(self, original_challenge: bytes) -> bool:
        expected = hashlib.sha256(original_challenge).digest()
        return self.challenge_response == expected


def perform_handshake(request: HandshakeRequest,
                      responder_cap: VersionCapability,
                      responder_id: str) -> HandshakeResponse:
    agreed = request.capability.negotiate(responder_cap)
    common = request.capability.common_types(responder_cap)
    challenge_resp = hashlib.sha256(request.challenge).digest()

    return HandshakeResponse(
        responder=responder_id,
        agreed_version=agreed,
        common_types=common,
        challenge_response=challenge_resp,
        accepted=agreed is not None and len(common) > 0,
    )


def test_section_9():
    checks = []

    cap_a = VersionCapability(1, 3,
                              {MessageType.TRUST_UPDATE, MessageType.ATP_TRANSFER},
                              {"compression"})
    cap_b = VersionCapability(2, 4,
                              {MessageType.ATP_TRANSFER, MessageType.CONSENSUS},
                              {"compression", "batching"})

    req = HandshakeRequest("alice", "fed-001", cap_a)
    resp = perform_handshake(req, cap_b, "bob")

    checks.append(("handshake_accepted", resp.accepted))
    checks.append(("agreed_v3", resp.agreed_version == 3))
    checks.append(("challenge_verified", resp.verify_challenge(req.challenge)))
    checks.append(("common_type_atp", MessageType.ATP_TRANSFER in resp.common_types))

    # Encoding
    encoded_req = req.encode()
    checks.append(("handshake_magic", encoded_req[:3] == b'W4H'))
    checks.append(("handshake_compact", len(encoded_req) < 100))

    # Failed handshake (no overlap)
    cap_c = VersionCapability(5, 6, {MessageType.HEARTBEAT})
    req2 = HandshakeRequest("charlie", "fed-002", cap_c)
    resp2 = perform_handshake(req2, cap_a, "dave")
    checks.append(("handshake_rejected", not resp2.accepted))

    return checks


# ============================================================
# S10 — Error Recovery
# ============================================================

@dataclass
class FrameReader:
    """Read framed messages with error recovery."""
    buffer: bytearray = field(default_factory=bytearray)
    _good_frames: int = 0
    _bad_frames: int = 0

    def feed(self, data: bytes):
        self.buffer.extend(data)

    def read_frames(self) -> List[bytes]:
        """Extract valid frames from buffer."""
        frames = []
        while len(self.buffer) >= 2:
            # Look for magic bytes
            idx = self.buffer.find(b'W4')
            if idx < 0:
                self._bad_frames += 1
                self.buffer.clear()
                break
            if idx > 0:
                self._bad_frames += 1
                del self.buffer[:idx]

            # Try to decode
            if len(self.buffer) < 36:  # minimum frame size
                break

            # Extract length from varint after version
            try:
                # Read past magic (2) + version varint
                offset = 2
                _, consumed = decode_varint(bytes(self.buffer), offset)
                offset += consumed

                # Try full decode to find frame boundary
                # For simplicity, try to find next W4 or end of buffer
                next_magic = self.buffer.find(b'W4', 2)
                if next_magic > 0:
                    frame = bytes(self.buffer[:next_magic])
                else:
                    frame = bytes(self.buffer)

                # Verify integrity (last 32 bytes should be valid SHA-256)
                if len(frame) > 32:
                    content = frame[:-32]
                    mac = frame[-32:]
                    if hashlib.sha256(content).digest() == mac:
                        frames.append(frame)
                        self._good_frames += 1
                        del self.buffer[:len(frame)]
                        continue

                # If integrity check failed, skip this W4 marker
                del self.buffer[:2]
                self._bad_frames += 1

            except Exception:
                del self.buffer[:2]
                self._bad_frames += 1

        return frames


def test_section_10():
    checks = []

    # Normal frames
    reader = FrameReader()
    env1 = MessageEnvelope(MessageType.HEARTBEAT, "a", "f1", b"ping", 1)
    env2 = MessageEnvelope(MessageType.HEARTBEAT, "b", "f1", b"pong", 2)

    reader.feed(env1.encode())
    reader.feed(env2.encode())

    frames = reader.read_frames()
    checks.append(("two_frames", len(frames) == 2))

    # Garbage between frames
    reader2 = FrameReader()
    reader2.feed(b"garbage" + env1.encode() + b"more_garbage" + env2.encode())
    frames2 = reader2.read_frames()
    checks.append(("recovery_works", len(frames2) >= 1))

    # Partial frame
    reader3 = FrameReader()
    partial = env1.encode()[:10]  # truncated
    reader3.feed(partial)
    frames3 = reader3.read_frames()
    checks.append(("partial_buffered", len(frames3) == 0 and len(reader3.buffer) > 0))

    # Stats
    checks.append(("good_frame_count", reader._good_frames == 2))

    return checks


# ============================================================
# S11 — Performance & Throughput
# ============================================================

def test_section_11():
    checks = []

    import time as time_mod
    random.seed(42)

    # Tensor serialization throughput
    start = time_mod.perf_counter()
    for _ in range(10000):
        t = TrustTensor(random.random(), random.random(), random.random())
        encoded = t.encode()
        TrustTensor.decode(encoded)
    tensor_time = time_mod.perf_counter() - start
    checks.append(("10k_tensors_fast", tensor_time < 3.0))

    # ATP packet throughput
    start = time_mod.perf_counter()
    for i in range(10000):
        pkt = ATPPacket(ATPPacketType.TRANSFER, "alice", "bob",
                        100.0, 5.0, i, 1e9)
        encoded = pkt.encode()
        ATPPacket.decode(encoded)
    atp_time = time_mod.perf_counter() - start
    checks.append(("10k_atp_fast", atp_time < 3.0))

    # Envelope throughput
    start = time_mod.perf_counter()
    for i in range(1000):
        env = MessageEnvelope(MessageType.TRUST_UPDATE, f"e{i}", "fed",
                              b"payload" * 10, i)
        encoded = env.encode()
        MessageEnvelope.decode(encoded)
    env_time = time_mod.perf_counter() - start
    checks.append(("1k_envelopes_fast", env_time < 3.0))

    # Batch throughput
    batch = MessageBatch()
    for i in range(100):
        batch.messages.append(MessageEnvelope(
            MessageType.ATP_TRANSFER, f"e{i}", "fed",
            ATPPacket(ATPPacketType.TRANSFER, f"e{i}", "dest", 50.0, 2.5, i, 1e9).encode(),
            i
        ))
    start = time_mod.perf_counter()
    encoded = batch.encode()
    decoded, ok = MessageBatch.decode(encoded)
    batch_time = time_mod.perf_counter() - start
    checks.append(("batch_100_fast", batch_time < 2.0))
    checks.append(("batch_integrity", ok))

    # Size analysis
    tensor_size = len(TrustTensor(0.8, 0.6, 0.7).encode())
    atp_size = len(ATPPacket(ATPPacketType.TRANSFER, "alice", "bob", 100.0, 5.0, 1, 1e9).encode())
    checks.append(("tensor_compact", tensor_size < 50))
    checks.append(("atp_compact", atp_size < 60))

    return checks


# ============================================================
# Main
# ============================================================

def main():
    random.seed(42)

    sections = [
        ("S1 Primitive Encoding", test_section_1),
        ("S2 Trust Tensor Serialization", test_section_2),
        ("S3 ATP Packet Encoding", test_section_3),
        ("S4 Message Envelope & Integrity", test_section_4),
        ("S5 Version Negotiation", test_section_5),
        ("S6 Compression", test_section_6),
        ("S7 Batch Encoding", test_section_7),
        ("S8 Roundtrip Fuzz Testing", test_section_8),
        ("S9 Protocol Handshake", test_section_9),
        ("S10 Error Recovery", test_section_10),
        ("S11 Performance & Throughput", test_section_11),
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
