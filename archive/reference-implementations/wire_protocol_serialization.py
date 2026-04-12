"""
Wire Protocol & Tensor Serialization
======================================

Implements canonical binary encoding for Web4 trust tensors, ATP
packets, and attestation proofs crossing federation boundaries.
Includes framing, compression, version negotiation, and roundtrip
property-based fuzz testing.

Sections:
  S1  — Primitive Type Encoding (varint, float, string, bytes)
  S2  — Trust Tensor Serialization (T3, V3)
  S3  — ATP Packet Encoding
  S4  — Attestation Proof Encoding
  S5  — Message Envelope & Framing
  S6  — Version Negotiation
  S7  — Compression (optional payload compression)
  S8  — Batch Encoding
  S9  — Roundtrip Fuzz Testing
  S10 — Cross-Federation Message Format
  S11 — Performance & Size Benchmarks
"""

from __future__ import annotations
import math
import struct
import random
import hashlib
import zlib
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from enum import IntEnum


# ============================================================
# S1 — Primitive Type Encoding
# ============================================================

def encode_varint(value: int) -> bytes:
    """Encode unsigned integer as variable-length integer (LEB128)."""
    if value < 0:
        raise ValueError("varint must be non-negative")
    result = bytearray()
    while value > 0x7F:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.append(value & 0x7F)
    return bytes(result)


def decode_varint(data: bytes, offset: int = 0) -> Tuple[int, int]:
    """Decode varint, return (value, new_offset)."""
    value = 0
    shift = 0
    while offset < len(data):
        byte = data[offset]
        value |= (byte & 0x7F) << shift
        offset += 1
        if not (byte & 0x80):
            break
        shift += 7
    return value, offset


def encode_float64(value: float) -> bytes:
    """Encode float64 in IEEE 754 big-endian."""
    return struct.pack('>d', value)


def decode_float64(data: bytes, offset: int = 0) -> Tuple[float, int]:
    return struct.unpack_from('>d', data, offset)[0], offset + 8


def encode_string(value: str) -> bytes:
    """Length-prefixed UTF-8 string."""
    encoded = value.encode('utf-8')
    return encode_varint(len(encoded)) + encoded


def decode_string(data: bytes, offset: int = 0) -> Tuple[str, int]:
    length, offset = decode_varint(data, offset)
    value = data[offset:offset + length].decode('utf-8')
    return value, offset + length


def encode_bytes_field(value: bytes) -> bytes:
    """Length-prefixed bytes."""
    return encode_varint(len(value)) + value


def decode_bytes_field(data: bytes, offset: int = 0) -> Tuple[bytes, int]:
    length, offset = decode_varint(data, offset)
    return data[offset:offset + length], offset + length


def test_section_1():
    checks = []

    # Varint roundtrip
    for v in [0, 1, 127, 128, 255, 300, 16383, 16384, 2097151, 2**21]:
        encoded = encode_varint(v)
        decoded, _ = decode_varint(encoded)
        if decoded != v:
            checks.append((f"varint_{v}", False))
            break
    else:
        checks.append(("varint_roundtrip", True))

    # Varint size efficiency
    checks.append(("varint_1_byte", len(encode_varint(127)) == 1))
    checks.append(("varint_2_bytes", len(encode_varint(128)) == 2))
    checks.append(("varint_3_bytes", len(encode_varint(16384)) == 3))

    # Float64 roundtrip
    for v in [0.0, 1.0, -1.0, 3.14159, 1e-10, float('inf')]:
        encoded = encode_float64(v)
        decoded, _ = decode_float64(encoded)
        if v != v:  # NaN
            checks.append(("float_nan", decoded != decoded))
        elif decoded != v:
            checks.append(("float_roundtrip", False))
            break
    else:
        checks.append(("float64_roundtrip", True))

    # String roundtrip
    for s in ["", "hello", "日本語", "a" * 1000]:
        encoded = encode_string(s)
        decoded, _ = decode_string(encoded)
        if decoded != s:
            checks.append(("string_roundtrip", False))
            break
    else:
        checks.append(("string_roundtrip", True))

    # Bytes roundtrip
    test_bytes = b'\x00\x01\x02\xff' * 100
    encoded = encode_bytes_field(test_bytes)
    decoded, _ = decode_bytes_field(encoded)
    checks.append(("bytes_roundtrip", decoded == test_bytes))

    # Negative varint rejected
    try:
        encode_varint(-1)
        checks.append(("negative_varint_rejected", False))
    except ValueError:
        checks.append(("negative_varint_rejected", True))

    return checks


# ============================================================
# S2 — Trust Tensor Serialization (T3, V3)
# ============================================================

class TensorType(IntEnum):
    T3 = 1  # Trust tensor
    V3 = 2  # Value tensor


@dataclass
class TrustTensor:
    tensor_type: TensorType
    entity_id: str
    talent: float       # T3 dim 1
    training: float     # T3 dim 2
    temperament: float  # T3 dim 3
    confidence: float = 1.0
    timestamp: float = 0.0

    @property
    def composite(self) -> float:
        return (self.talent + self.training + self.temperament) / 3.0

    def encode(self) -> bytes:
        result = bytearray()
        result.append(self.tensor_type)
        result.extend(encode_string(self.entity_id))
        result.extend(encode_float64(self.talent))
        result.extend(encode_float64(self.training))
        result.extend(encode_float64(self.temperament))
        result.extend(encode_float64(self.confidence))
        result.extend(encode_float64(self.timestamp))
        return bytes(result)

    @classmethod
    def decode(cls, data: bytes, offset: int = 0) -> Tuple['TrustTensor', int]:
        tensor_type = TensorType(data[offset])
        offset += 1
        entity_id, offset = decode_string(data, offset)
        talent, offset = decode_float64(data, offset)
        training, offset = decode_float64(data, offset)
        temperament, offset = decode_float64(data, offset)
        confidence, offset = decode_float64(data, offset)
        timestamp, offset = decode_float64(data, offset)
        return cls(tensor_type, entity_id, talent, training, temperament,
                   confidence, timestamp), offset


def test_section_2():
    checks = []

    t3 = TrustTensor(TensorType.T3, "alice", 0.8, 0.6, 0.7, 0.95, 1709164800.0)
    encoded = t3.encode()
    decoded, _ = TrustTensor.decode(encoded)

    checks.append(("t3_type", decoded.tensor_type == TensorType.T3))
    checks.append(("t3_entity", decoded.entity_id == "alice"))
    checks.append(("t3_talent", abs(decoded.talent - 0.8) < 1e-10))
    checks.append(("t3_training", abs(decoded.training - 0.6) < 1e-10))
    checks.append(("t3_temperament", abs(decoded.temperament - 0.7) < 1e-10))
    checks.append(("t3_confidence", abs(decoded.confidence - 0.95) < 1e-10))
    checks.append(("t3_timestamp", abs(decoded.timestamp - 1709164800.0) < 1e-6))

    # Size: 1 (type) + ~6 (entity) + 5*8 (floats) = ~47 bytes
    checks.append(("t3_compact", len(encoded) < 60))

    # V3 tensor
    v3 = TrustTensor(TensorType.V3, "bob", 0.9, 0.85, 0.75)
    v3_enc = v3.encode()
    v3_dec, _ = TrustTensor.decode(v3_enc)
    checks.append(("v3_type", v3_dec.tensor_type == TensorType.V3))
    checks.append(("v3_roundtrip", abs(v3_dec.talent - 0.9) < 1e-10))

    # Composite preserved
    checks.append(("composite_preserved", abs(decoded.composite - t3.composite) < 1e-10))

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
    timestamp: float
    nonce: int = 0
    federation_id: str = ""

    def encode(self) -> bytes:
        result = bytearray()
        result.append(self.packet_type)
        result.extend(encode_string(self.from_entity))
        result.extend(encode_string(self.to_entity))
        result.extend(encode_float64(self.amount))
        result.extend(encode_float64(self.fee))
        result.extend(encode_float64(self.timestamp))
        result.extend(encode_varint(self.nonce))
        result.extend(encode_string(self.federation_id))
        return bytes(result)

    @classmethod
    def decode(cls, data: bytes, offset: int = 0) -> Tuple['ATPPacket', int]:
        packet_type = ATPPacketType(data[offset])
        offset += 1
        from_entity, offset = decode_string(data, offset)
        to_entity, offset = decode_string(data, offset)
        amount, offset = decode_float64(data, offset)
        fee, offset = decode_float64(data, offset)
        timestamp, offset = decode_float64(data, offset)
        nonce, offset = decode_varint(data, offset)
        federation_id, offset = decode_string(data, offset)
        return cls(packet_type, from_entity, to_entity, amount, fee,
                   timestamp, nonce, federation_id), offset

    def content_hash(self) -> str:
        return hashlib.sha256(self.encode()).hexdigest()


def test_section_3():
    checks = []

    pkt = ATPPacket(ATPPacketType.TRANSFER, "alice", "bob", 50.0, 2.5,
                    1709164800.0, nonce=42, federation_id="fed-alpha")
    encoded = pkt.encode()
    decoded, _ = ATPPacket.decode(encoded)

    checks.append(("atp_type", decoded.packet_type == ATPPacketType.TRANSFER))
    checks.append(("atp_from", decoded.from_entity == "alice"))
    checks.append(("atp_to", decoded.to_entity == "bob"))
    checks.append(("atp_amount", abs(decoded.amount - 50.0) < 1e-10))
    checks.append(("atp_fee", abs(decoded.fee - 2.5) < 1e-10))
    checks.append(("atp_nonce", decoded.nonce == 42))
    checks.append(("atp_federation", decoded.federation_id == "fed-alpha"))

    # Compact
    checks.append(("atp_compact", len(encoded) < 80))

    # Content hash deterministic
    h1 = pkt.content_hash()
    h2 = pkt.content_hash()
    checks.append(("hash_deterministic", h1 == h2))

    # Different packet -> different hash
    pkt2 = ATPPacket(ATPPacketType.TRANSFER, "alice", "bob", 51.0, 2.5,
                     1709164800.0, nonce=42, federation_id="fed-alpha")
    checks.append(("hash_differs", pkt.content_hash() != pkt2.content_hash()))

    return checks


# ============================================================
# S4 — Attestation Proof Encoding
# ============================================================

@dataclass
class AttestationProof:
    attestor_id: str
    subject_id: str
    trust_snapshot: TrustTensor
    signature: bytes
    merkle_path: List[bytes]  # inclusion proof
    timestamp: float

    def encode(self) -> bytes:
        result = bytearray()
        result.extend(encode_string(self.attestor_id))
        result.extend(encode_string(self.subject_id))
        result.extend(self.trust_snapshot.encode())
        result.extend(encode_bytes_field(self.signature))
        result.extend(encode_varint(len(self.merkle_path)))
        for node in self.merkle_path:
            result.extend(encode_bytes_field(node))
        result.extend(encode_float64(self.timestamp))
        return bytes(result)

    @classmethod
    def decode(cls, data: bytes, offset: int = 0) -> Tuple['AttestationProof', int]:
        attestor_id, offset = decode_string(data, offset)
        subject_id, offset = decode_string(data, offset)
        trust_snapshot, offset = TrustTensor.decode(data, offset)
        signature, offset = decode_bytes_field(data, offset)
        path_len, offset = decode_varint(data, offset)
        merkle_path = []
        for _ in range(path_len):
            node, offset = decode_bytes_field(data, offset)
            merkle_path.append(node)
        timestamp, offset = decode_float64(data, offset)
        return cls(attestor_id, subject_id, trust_snapshot, signature,
                   merkle_path, timestamp), offset


def test_section_4():
    checks = []

    tensor = TrustTensor(TensorType.T3, "bob", 0.7, 0.6, 0.8)
    sig = hashlib.sha256(b"attestation_signature").digest()
    merkle = [hashlib.sha256(f"node_{i}".encode()).digest() for i in range(4)]

    proof = AttestationProof("alice", "bob", tensor, sig, merkle, 1709164800.0)
    encoded = proof.encode()
    decoded, _ = AttestationProof.decode(encoded)

    checks.append(("proof_attestor", decoded.attestor_id == "alice"))
    checks.append(("proof_subject", decoded.subject_id == "bob"))
    checks.append(("proof_tensor", abs(decoded.trust_snapshot.talent - 0.7) < 1e-10))
    checks.append(("proof_sig", decoded.signature == sig))
    checks.append(("proof_merkle_len", len(decoded.merkle_path) == 4))
    checks.append(("proof_merkle_match", decoded.merkle_path[0] == merkle[0]))

    # Size with 4-node Merkle path: should fit in ~256 bytes
    checks.append(("proof_size", len(encoded) < 300))

    # Empty Merkle path
    empty_proof = AttestationProof("a", "b", tensor, b"", [], 0.0)
    enc2 = empty_proof.encode()
    dec2, _ = AttestationProof.decode(enc2)
    checks.append(("empty_merkle", len(dec2.merkle_path) == 0))

    return checks


# ============================================================
# S5 — Message Envelope & Framing
# ============================================================

class MessageType(IntEnum):
    TRUST_UPDATE = 1
    ATP_TRANSFER = 2
    ATTESTATION = 3
    HEARTBEAT = 4
    CONSENSUS = 5
    FEDERATION_SYNC = 6


@dataclass
class MessageEnvelope:
    version: int
    message_type: MessageType
    sender_id: str
    recipient_id: str  # "" for broadcast
    payload: bytes
    mac: bytes = b""  # HMAC for integrity

    def encode(self) -> bytes:
        result = bytearray()
        # Magic bytes + version
        result.extend(b'W4')  # 2-byte magic
        result.extend(encode_varint(self.version))
        result.append(self.message_type)
        result.extend(encode_string(self.sender_id))
        result.extend(encode_string(self.recipient_id))
        result.extend(encode_bytes_field(self.payload))
        result.extend(encode_bytes_field(self.mac))
        # Length prefix for framing
        frame = encode_varint(len(result)) + bytes(result)
        return frame

    @classmethod
    def decode(cls, data: bytes, offset: int = 0) -> Tuple['MessageEnvelope', int]:
        frame_len, offset = decode_varint(data, offset)
        # Magic check
        if data[offset:offset+2] != b'W4':
            raise ValueError("Invalid magic bytes")
        offset += 2
        version, offset = decode_varint(data, offset)
        message_type = MessageType(data[offset])
        offset += 1
        sender_id, offset = decode_string(data, offset)
        recipient_id, offset = decode_string(data, offset)
        payload, offset = decode_bytes_field(data, offset)
        mac, offset = decode_bytes_field(data, offset)
        return cls(version, message_type, sender_id, recipient_id, payload, mac), offset

    def compute_mac(self, key: bytes) -> bytes:
        import hmac as hmac_mod
        content = self.version.to_bytes(2, 'big') + self.message_type.to_bytes(1, 'big')
        content += self.sender_id.encode() + self.recipient_id.encode() + self.payload
        return hmac_mod.new(key, content, hashlib.sha256).digest()

    def sign(self, key: bytes):
        self.mac = self.compute_mac(key)

    def verify(self, key: bytes) -> bool:
        import hmac as hmac_mod
        expected = self.compute_mac(key)
        return hmac_mod.compare_digest(self.mac, expected)


def test_section_5():
    checks = []

    payload = b"test_payload_data"
    msg = MessageEnvelope(1, MessageType.ATP_TRANSFER, "alice", "bob", payload)

    encoded = msg.encode()
    decoded, _ = MessageEnvelope.decode(encoded)

    checks.append(("msg_version", decoded.version == 1))
    checks.append(("msg_type", decoded.message_type == MessageType.ATP_TRANSFER))
    checks.append(("msg_sender", decoded.sender_id == "alice"))
    checks.append(("msg_recipient", decoded.recipient_id == "bob"))
    checks.append(("msg_payload", decoded.payload == payload))

    # HMAC signing
    key = b"federation_secret_key"
    msg.sign(key)
    checks.append(("mac_signed", len(msg.mac) == 32))

    encoded_signed = msg.encode()
    decoded_signed, _ = MessageEnvelope.decode(encoded_signed)
    checks.append(("mac_verifies", decoded_signed.verify(key)))
    checks.append(("mac_wrong_key", not decoded_signed.verify(b"wrong_key")))

    # Invalid magic
    try:
        bad_data = encode_varint(10) + b'XX' + b'\x00' * 8
        MessageEnvelope.decode(bad_data)
        checks.append(("bad_magic_rejected", False))
    except ValueError:
        checks.append(("bad_magic_rejected", True))

    return checks


# ============================================================
# S6 — Version Negotiation
# ============================================================

@dataclass
class VersionNegotiator:
    """Negotiate wire protocol version between two endpoints."""
    supported_versions: List[int] = field(default_factory=lambda: [1, 2, 3])
    min_version: int = 1

    def propose(self) -> bytes:
        """Encode version proposal."""
        result = bytearray()
        result.extend(encode_varint(len(self.supported_versions)))
        for v in sorted(self.supported_versions, reverse=True):
            result.extend(encode_varint(v))
        return bytes(result)

    @classmethod
    def decode_proposal(cls, data: bytes, offset: int = 0) -> Tuple[List[int], int]:
        count, offset = decode_varint(data, offset)
        versions = []
        for _ in range(count):
            v, offset = decode_varint(data, offset)
            versions.append(v)
        return versions, offset

    def negotiate(self, remote_versions: List[int]) -> Optional[int]:
        """Find highest common version."""
        common = set(self.supported_versions) & set(remote_versions)
        valid = [v for v in common if v >= self.min_version]
        return max(valid) if valid else None


def test_section_6():
    checks = []

    local = VersionNegotiator(supported_versions=[1, 2, 3])
    remote = VersionNegotiator(supported_versions=[2, 3, 4])

    # Proposal encoding
    proposal = local.propose()
    decoded_versions, _ = VersionNegotiator.decode_proposal(proposal)
    checks.append(("proposal_roundtrip", set(decoded_versions) == {1, 2, 3}))

    # Negotiation
    agreed = local.negotiate(remote.supported_versions)
    checks.append(("negotiated_v3", agreed == 3))

    # No common version
    incompatible = VersionNegotiator(supported_versions=[5, 6])
    checks.append(("no_common", local.negotiate(incompatible.supported_versions) is None))

    # Min version enforcement
    min_v2 = VersionNegotiator(supported_versions=[1, 2, 3], min_version=2)
    checks.append(("min_version", min_v2.negotiate([1, 2]) == 2))
    checks.append(("below_min", min_v2.negotiate([1]) is None))

    # Self-negotiation
    checks.append(("self_negotiate", local.negotiate(local.supported_versions) == 3))

    return checks


# ============================================================
# S7 — Compression
# ============================================================

@dataclass
class CompressedPayload:
    """Optional zlib compression for large payloads."""
    COMPRESSION_THRESHOLD = 128  # only compress if larger

    @staticmethod
    def compress(data: bytes) -> Tuple[bytes, bool]:
        """Compress if beneficial. Returns (data, is_compressed)."""
        if len(data) < CompressedPayload.COMPRESSION_THRESHOLD:
            return data, False
        compressed = zlib.compress(data, level=6)
        if len(compressed) < len(data):
            return compressed, True
        return data, False

    @staticmethod
    def decompress(data: bytes, is_compressed: bool) -> bytes:
        if is_compressed:
            return zlib.decompress(data)
        return data

    @staticmethod
    def encode(data: bytes) -> bytes:
        """Encode with compression flag."""
        compressed, is_compressed = CompressedPayload.compress(data)
        flag = b'\x01' if is_compressed else b'\x00'
        return flag + encode_bytes_field(compressed)

    @staticmethod
    def decode(data: bytes, offset: int = 0) -> Tuple[bytes, int]:
        is_compressed = data[offset] == 0x01
        offset += 1
        payload, offset = decode_bytes_field(data, offset)
        return CompressedPayload.decompress(payload, is_compressed), offset


def test_section_7():
    checks = []

    # Small data: no compression
    small = b"hello"
    compressed, is_comp = CompressedPayload.compress(small)
    checks.append(("small_not_compressed", not is_comp))

    # Large repetitive data: compression helps
    large = b"trust_tensor_data_" * 100
    compressed, is_comp = CompressedPayload.compress(large)
    checks.append(("large_compressed", is_comp))
    checks.append(("compression_saves", len(compressed) < len(large)))

    # Roundtrip
    encoded = CompressedPayload.encode(large)
    decoded, _ = CompressedPayload.decode(encoded)
    checks.append(("compression_roundtrip", decoded == large))

    # Small data roundtrip
    enc_small = CompressedPayload.encode(small)
    dec_small, _ = CompressedPayload.decode(enc_small)
    checks.append(("small_roundtrip", dec_small == small))

    # Random data (low compressibility)
    random_data = bytes(random.getrandbits(8) for _ in range(500))
    enc_random = CompressedPayload.encode(random_data)
    dec_random, _ = CompressedPayload.decode(enc_random)
    checks.append(("random_roundtrip", dec_random == random_data))

    # Compression ratio
    ratio = len(compressed) / len(large)
    checks.append(("good_ratio", ratio < 0.3))

    return checks


# ============================================================
# S8 — Batch Encoding
# ============================================================

@dataclass
class BatchMessage:
    """Encode multiple messages in a single frame."""
    messages: List[MessageEnvelope] = field(default_factory=list)

    def encode(self) -> bytes:
        result = bytearray()
        result.extend(b'W4B')  # batch magic
        result.extend(encode_varint(len(self.messages)))
        for msg in self.messages:
            msg_bytes = msg.encode()
            result.extend(encode_bytes_field(msg_bytes))
        return bytes(result)

    @classmethod
    def decode(cls, data: bytes, offset: int = 0) -> Tuple['BatchMessage', int]:
        if data[offset:offset+3] != b'W4B':
            raise ValueError("Invalid batch magic")
        offset += 3
        count, offset = decode_varint(data, offset)
        messages = []
        for _ in range(count):
            msg_bytes, offset = decode_bytes_field(data, offset)
            msg, _ = MessageEnvelope.decode(msg_bytes)
            messages.append(msg)
        return cls(messages), offset


def test_section_8():
    checks = []

    batch = BatchMessage()
    for i in range(5):
        msg = MessageEnvelope(1, MessageType.TRUST_UPDATE, f"e{i}", "broadcast",
                              f"trust_data_{i}".encode())
        batch.messages.append(msg)

    encoded = batch.encode()
    decoded, _ = BatchMessage.decode(encoded)

    checks.append(("batch_count", len(decoded.messages) == 5))
    checks.append(("batch_first", decoded.messages[0].sender_id == "e0"))
    checks.append(("batch_last", decoded.messages[4].sender_id == "e4"))

    # Batch size vs individual
    individual_size = sum(len(msg.encode()) for msg in batch.messages)
    checks.append(("batch_reasonable_size", len(encoded) < individual_size * 1.5))

    # Empty batch
    empty = BatchMessage()
    enc_empty = empty.encode()
    dec_empty, _ = BatchMessage.decode(enc_empty)
    checks.append(("empty_batch", len(dec_empty.messages) == 0))

    # Invalid batch magic
    try:
        BatchMessage.decode(b'XXX\x00')
        checks.append(("bad_batch_magic", False))
    except ValueError:
        checks.append(("bad_batch_magic", True))

    return checks


# ============================================================
# S9 — Roundtrip Fuzz Testing
# ============================================================

def random_trust_tensor() -> TrustTensor:
    return TrustTensor(
        tensor_type=random.choice([TensorType.T3, TensorType.V3]),
        entity_id=f"entity_{random.randint(0, 999)}",
        talent=random.uniform(0, 1),
        training=random.uniform(0, 1),
        temperament=random.uniform(0, 1),
        confidence=random.uniform(0, 1),
        timestamp=random.uniform(0, 2e9),
    )


def random_atp_packet() -> ATPPacket:
    return ATPPacket(
        packet_type=random.choice(list(ATPPacketType)),
        from_entity=f"from_{random.randint(0, 99)}",
        to_entity=f"to_{random.randint(0, 99)}",
        amount=random.uniform(0, 10000),
        fee=random.uniform(0, 100),
        timestamp=random.uniform(0, 2e9),
        nonce=random.randint(0, 2**20),
        federation_id=f"fed_{random.randint(0, 9)}",
    )


def random_message() -> MessageEnvelope:
    return MessageEnvelope(
        version=random.randint(1, 5),
        message_type=random.choice(list(MessageType)),
        sender_id=f"sender_{random.randint(0, 99)}",
        recipient_id=f"recipient_{random.randint(0, 99)}",
        payload=bytes(random.getrandbits(8) for _ in range(random.randint(0, 200))),
    )


def test_section_9():
    checks = []
    random.seed(42)

    # Fuzz trust tensors
    tensor_failures = 0
    for _ in range(200):
        t = random_trust_tensor()
        encoded = t.encode()
        decoded, _ = TrustTensor.decode(encoded)
        if (decoded.entity_id != t.entity_id or
            abs(decoded.talent - t.talent) > 1e-10 or
            abs(decoded.training - t.training) > 1e-10 or
            abs(decoded.temperament - t.temperament) > 1e-10):
            tensor_failures += 1
    checks.append(("fuzz_tensors_200", tensor_failures == 0))

    # Fuzz ATP packets
    atp_failures = 0
    for _ in range(200):
        p = random_atp_packet()
        encoded = p.encode()
        decoded, _ = ATPPacket.decode(encoded)
        if (decoded.from_entity != p.from_entity or
            decoded.to_entity != p.to_entity or
            abs(decoded.amount - p.amount) > 1e-10 or
            decoded.nonce != p.nonce):
            atp_failures += 1
    checks.append(("fuzz_atp_200", atp_failures == 0))

    # Fuzz message envelopes
    msg_failures = 0
    for _ in range(200):
        m = random_message()
        encoded = m.encode()
        decoded, _ = MessageEnvelope.decode(encoded)
        if (decoded.sender_id != m.sender_id or
            decoded.payload != m.payload or
            decoded.version != m.version):
            msg_failures += 1
    checks.append(("fuzz_messages_200", msg_failures == 0))

    # Fuzz attestation proofs
    proof_failures = 0
    for _ in range(100):
        tensor = random_trust_tensor()
        sig = bytes(random.getrandbits(8) for _ in range(32))
        path = [bytes(random.getrandbits(8) for _ in range(32))
                for _ in range(random.randint(0, 8))]
        proof = AttestationProof(f"attestor_{random.randint(0, 99)}",
                                 f"subject_{random.randint(0, 99)}",
                                 tensor, sig, path, random.uniform(0, 2e9))
        encoded = proof.encode()
        decoded, _ = AttestationProof.decode(encoded)
        if (decoded.attestor_id != proof.attestor_id or
            decoded.signature != proof.signature or
            len(decoded.merkle_path) != len(proof.merkle_path)):
            proof_failures += 1
    checks.append(("fuzz_proofs_100", proof_failures == 0))

    # Fuzz batch messages
    batch_failures = 0
    for _ in range(50):
        batch = BatchMessage([random_message() for _ in range(random.randint(0, 10))])
        encoded = batch.encode()
        decoded, _ = BatchMessage.decode(encoded)
        if len(decoded.messages) != len(batch.messages):
            batch_failures += 1
    checks.append(("fuzz_batches_50", batch_failures == 0))

    return checks


# ============================================================
# S10 — Cross-Federation Message Format
# ============================================================

@dataclass
class CrossFederationTransfer:
    """ATP transfer between two federations."""
    source_federation: str
    target_federation: str
    source_entity: str
    target_entity: str
    amount: float
    cross_fee: float
    source_trust: TrustTensor
    attestation: AttestationProof
    nonce: int

    def encode(self) -> bytes:
        result = bytearray()
        result.extend(b'W4X')  # cross-federation magic
        result.extend(encode_string(self.source_federation))
        result.extend(encode_string(self.target_federation))
        result.extend(encode_string(self.source_entity))
        result.extend(encode_string(self.target_entity))
        result.extend(encode_float64(self.amount))
        result.extend(encode_float64(self.cross_fee))
        result.extend(self.source_trust.encode())
        result.extend(self.attestation.encode())
        result.extend(encode_varint(self.nonce))
        return bytes(result)

    @classmethod
    def decode(cls, data: bytes, offset: int = 0) -> Tuple['CrossFederationTransfer', int]:
        if data[offset:offset+3] != b'W4X':
            raise ValueError("Invalid cross-federation magic")
        offset += 3
        source_fed, offset = decode_string(data, offset)
        target_fed, offset = decode_string(data, offset)
        source_entity, offset = decode_string(data, offset)
        target_entity, offset = decode_string(data, offset)
        amount, offset = decode_float64(data, offset)
        cross_fee, offset = decode_float64(data, offset)
        trust, offset = TrustTensor.decode(data, offset)
        attestation, offset = AttestationProof.decode(data, offset)
        nonce, offset = decode_varint(data, offset)
        return cls(source_fed, target_fed, source_entity, target_entity,
                   amount, cross_fee, trust, attestation, nonce), offset


def test_section_10():
    checks = []

    trust = TrustTensor(TensorType.T3, "alice", 0.8, 0.7, 0.9, 0.95, 1709164800.0)
    sig = hashlib.sha256(b"cross_fed_sig").digest()
    proof = AttestationProof("validator", "alice", trust, sig,
                             [hashlib.sha256(b"m1").digest()], 1709164800.0)

    xfer = CrossFederationTransfer(
        source_federation="fed-alpha",
        target_federation="fed-beta",
        source_entity="alice",
        target_entity="bob",
        amount=100.0,
        cross_fee=10.0,
        source_trust=trust,
        attestation=proof,
        nonce=12345,
    )

    encoded = xfer.encode()
    decoded, _ = CrossFederationTransfer.decode(encoded)

    checks.append(("xfed_source", decoded.source_federation == "fed-alpha"))
    checks.append(("xfed_target", decoded.target_federation == "fed-beta"))
    checks.append(("xfed_amount", abs(decoded.amount - 100.0) < 1e-10))
    checks.append(("xfed_fee", abs(decoded.cross_fee - 10.0) < 1e-10))
    checks.append(("xfed_trust", abs(decoded.source_trust.talent - 0.8) < 1e-10))
    checks.append(("xfed_proof", decoded.attestation.attestor_id == "validator"))
    checks.append(("xfed_nonce", decoded.nonce == 12345))

    # Size check: full cross-fed message with proof should be < 512 bytes
    checks.append(("xfed_compact", len(encoded) < 512))

    return checks


# ============================================================
# S11 — Performance & Size Benchmarks
# ============================================================

def test_section_11():
    checks = []
    random.seed(42)

    import time as time_mod

    # Tensor encoding speed
    start = time_mod.perf_counter()
    for _ in range(10000):
        t = TrustTensor(TensorType.T3, "entity_123", 0.8, 0.6, 0.7, 0.95, 1e9)
        encoded = t.encode()
        TrustTensor.decode(encoded)
    tensor_time = time_mod.perf_counter() - start
    checks.append(("10k_tensors_fast", tensor_time < 3.0))

    # ATP packet speed
    start = time_mod.perf_counter()
    for _ in range(10000):
        p = ATPPacket(ATPPacketType.TRANSFER, "alice", "bob", 50.0, 2.5, 1e9, 42, "fed")
        encoded = p.encode()
        ATPPacket.decode(encoded)
    atp_time = time_mod.perf_counter() - start
    checks.append(("10k_atp_fast", atp_time < 3.0))

    # Message envelope speed
    start = time_mod.perf_counter()
    for _ in range(5000):
        m = MessageEnvelope(1, MessageType.TRUST_UPDATE, "sender", "receiver",
                           b"x" * 100)
        encoded = m.encode()
        MessageEnvelope.decode(encoded)
    msg_time = time_mod.perf_counter() - start
    checks.append(("5k_messages_fast", msg_time < 3.0))

    # Size benchmarks
    t3_size = len(TrustTensor(TensorType.T3, "entity_id", 0.8, 0.6, 0.7).encode())
    checks.append(("t3_under_55_bytes", t3_size < 55))  # 1 type + 10 entity + 40 floats = 51

    atp_size = len(ATPPacket(ATPPacketType.TRANSFER, "alice", "bob", 50.0, 2.5,
                             1e9, 42, "fed_id").encode())
    checks.append(("atp_under_70_bytes", atp_size < 70))

    # Batch efficiency: 100 messages in one frame
    batch = BatchMessage([MessageEnvelope(1, MessageType.HEARTBEAT, f"e{i}", "",
                                         b"hb") for i in range(100)])
    batch_size = len(batch.encode())
    single_size = sum(len(MessageEnvelope(1, MessageType.HEARTBEAT, f"e{i}", "",
                                          b"hb").encode()) for i in range(100))
    checks.append(("batch_efficient", batch_size < single_size * 1.2))

    # Compression on batch
    compressed = CompressedPayload.encode(batch.encode())
    checks.append(("batch_compresses", len(compressed) < batch_size))

    return checks


# ============================================================
# Main
# ============================================================

def main():
    random.seed(42)

    sections = [
        ("S1 Primitive Type Encoding", test_section_1),
        ("S2 Trust Tensor Serialization", test_section_2),
        ("S3 ATP Packet Encoding", test_section_3),
        ("S4 Attestation Proof Encoding", test_section_4),
        ("S5 Message Envelope & Framing", test_section_5),
        ("S6 Version Negotiation", test_section_6),
        ("S7 Compression", test_section_7),
        ("S8 Batch Encoding", test_section_8),
        ("S9 Roundtrip Fuzz Testing", test_section_9),
        ("S10 Cross-Federation Message", test_section_10),
        ("S11 Performance & Size Benchmarks", test_section_11),
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
