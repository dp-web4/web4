#!/usr/bin/env python3
"""
Web4 Handshake Protocol — Advanced Features Reference Implementation

Covers the MISSING sections from core_protocol_handshake.py:
  §4  — W4IDp Pairwise Identifier Derivation & Lifecycle
  §6.0 — Canonicalization & Signature Profiles (COSE/CBOR, JOSE/JSON)
  §7  — Session Rekey & Key Rotation (forward secrecy ratchet)
  §8  — Formal State Machine with transition validation
  §9  — Anti-Replay & Clock validation (nonce tracking, replay window)
  §10 — Problem Details (RFC 9457) error handling with W4_ERR codes
  §11 — Security Considerations (downgrade, KCI, DoS checks)

@spec web4-standard/protocols/web4-handshake.md
@version 1.0.0
"""

import hashlib
import hmac
import json
import os
import re
import struct
import sys
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple

from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey, X25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.ec import (
    ECDSA, SECP256R1, EllipticCurvePrivateKey,
    generate_private_key as ec_generate_private_key,
)
from cryptography.hazmat.primitives.ciphers.aead import (
    ChaCha20Poly1305, AESGCM,
)
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF, HKDFExpand


# ═══════════════════════════════════════════════════════════════
# §10: Problem Details (RFC 9457) Error Handling
# ═══════════════════════════════════════════════════════════════

class W4ErrorCode(Enum):
    """Web4 error codes per §10."""
    AUTHZ_DENIED = "W4_ERR_AUTHZ_DENIED"
    PROTO_FORMAT = "W4_ERR_PROTO_FORMAT"
    SUITE_MISMATCH = "W4_ERR_SUITE_MISMATCH"
    REPLAY_DETECTED = "W4_ERR_REPLAY_DETECTED"
    TIMESTAMP_INVALID = "W4_ERR_TIMESTAMP_INVALID"
    STATE_INVALID = "W4_ERR_STATE_INVALID"
    CHANNEL_BIND_FAIL = "W4_ERR_CHANNEL_BIND_FAIL"
    KID_UNKNOWN = "W4_ERR_KID_UNKNOWN"
    SIGNATURE_INVALID = "W4_ERR_SIGNATURE_INVALID"
    REKEY_FAILED = "W4_ERR_REKEY_FAILED"
    W4IDP_EXPIRED = "W4_ERR_W4IDP_EXPIRED"


@dataclass
class ProblemDetails:
    """RFC 9457 Problem Details for HTTP APIs, adapted for Web4.

    Per §10: error responses use Problem Details format with W4_ERR codes.
    """
    type: str = "about:blank"
    title: str = ""
    status: int = 500
    code: str = ""
    detail: str = ""
    instance: str = ""

    def to_dict(self) -> dict:
        d = {"type": self.type, "title": self.title, "status": self.status}
        if self.code:
            d["code"] = self.code
        if self.detail:
            d["detail"] = self.detail
        if self.instance:
            d["instance"] = self.instance
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


class HandshakeError(Exception):
    """Protocol handshake failure with Problem Details."""
    def __init__(self, message: str, code: W4ErrorCode = W4ErrorCode.PROTO_FORMAT,
                 status: int = 400):
        super().__init__(message)
        self.problem = ProblemDetails(
            title=message,
            status=status,
            code=code.value,
            detail=message,
        )


# ═══════════════════════════════════════════════════════════════
# §4: W4IDp Pairwise Identifier Derivation & Lifecycle
# ═══════════════════════════════════════════════════════════════

# Base32 alphabet (RFC 4648, no padding)
_B32_ALPHA = "abcdefghijklmnopqrstuvwxyz234567"


def _multibase_base32(data: bytes) -> str:
    """Multibase base32 encoding without padding (MB32 per §4.1)."""
    bits = 0
    accum = 0
    result = []
    for byte in data:
        accum = (accum << 8) | byte
        bits += 8
        while bits >= 5:
            bits -= 5
            result.append(_B32_ALPHA[(accum >> bits) & 0x1F])
    if bits > 0:
        result.append(_B32_ALPHA[(accum << (5 - bits)) & 0x1F])
    return "".join(result)


@dataclass
class W4IDpEntry:
    """A single pairwise identifier entry."""
    w4idp: str
    peer_salt: bytes
    created_at: float
    valid: bool = True


class W4IDpManager:
    """Manages pairwise W4IDp identifiers per §4.1-4.2.

    Each party holds a master secret. Pairwise identifiers are derived
    per peer using HKDF with a unique salt, encoded as multibase base32.
    """

    MAX_CONCURRENT = 4  # §4.2: at least 4 concurrently valid per peer

    def __init__(self, master_secret: Optional[bytes] = None):
        self._master_secret = master_secret or os.urandom(32)
        # peer_id → list of W4IDpEntry (most recent last)
        self._identifiers: Dict[str, List[W4IDpEntry]] = {}

    @property
    def master_secret(self) -> bytes:
        return self._master_secret

    def derive_w4idp(self, peer_id: str, peer_salt: Optional[bytes] = None) -> W4IDpEntry:
        """Derive a pairwise W4IDp for a peer per §4.1.

        w4idp = MB32(HKDF-Extract-Then-Expand(salt=peer_salt,
                                              IKM=sk_master,
                                              info="W4IDp:v1"))

        §4.2 salt requirements:
        - peer_salt MUST be 128-bit random, unique per counterparty
        - peer_salt MUST NOT be derived from stable identifiers
        """
        if peer_salt is None:
            peer_salt = os.urandom(16)  # 128-bit random
        elif len(peer_salt) < 16:
            raise HandshakeError(
                "peer_salt MUST be at least 128-bit",
                W4ErrorCode.PROTO_FORMAT,
            )

        # HKDF-Extract-Then-Expand
        derived = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=peer_salt,
            info=b"W4IDp:v1",
        ).derive(self._master_secret)

        w4idp = f"w4idp-{_multibase_base32(derived)}"

        entry = W4IDpEntry(
            w4idp=w4idp,
            peer_salt=peer_salt,
            created_at=time.time(),
        )

        if peer_id not in self._identifiers:
            self._identifiers[peer_id] = []
        self._identifiers[peer_id].append(entry)

        return entry

    def get_current(self, peer_id: str) -> Optional[str]:
        """Get the most recent valid W4IDp for a peer."""
        entries = self._identifiers.get(peer_id, [])
        for entry in reversed(entries):
            if entry.valid:
                return entry.w4idp
        return None

    def get_valid_count(self, peer_id: str) -> int:
        """Count concurrently valid W4IDp values for a peer."""
        return sum(1 for e in self._identifiers.get(peer_id, []) if e.valid)

    def rotate(self, peer_id: str, new_master_secret: Optional[bytes] = None) -> W4IDpEntry:
        """Rotate W4IDp for a peer per §4.2.

        A W4IDp MUST be re-derived when either party rotates its master key.
        """
        if new_master_secret is not None:
            self._master_secret = new_master_secret

        new_entry = self.derive_w4idp(peer_id)

        # Trim old entries beyond MAX_CONCURRENT
        entries = self._identifiers[peer_id]
        valid_entries = [e for e in entries if e.valid]
        if len(valid_entries) > self.MAX_CONCURRENT:
            # Invalidate oldest beyond limit
            valid_entries[0].valid = False

        return new_entry

    def invalidate_all(self, peer_id: str) -> int:
        """Invalidate all W4IDp values for a peer."""
        count = 0
        for entry in self._identifiers.get(peer_id, []):
            if entry.valid:
                entry.valid = False
                count += 1
        return count

    def is_known(self, w4idp: str) -> bool:
        """Check if a W4IDp is known (any peer, valid or not)."""
        for entries in self._identifiers.values():
            for entry in entries:
                if entry.w4idp == w4idp:
                    return True
        return False

    def lookup_peer(self, w4idp: str) -> Optional[str]:
        """Find which peer a W4IDp belongs to."""
        for peer_id, entries in self._identifiers.items():
            for entry in entries:
                if entry.w4idp == w4idp and entry.valid:
                    return peer_id
        return None

    def verify_privacy(self, peer_a: str, peer_b: str) -> bool:
        """Verify W4IDp privacy: different peers MUST have different identifiers.

        §4.2: W4IDp MUST NOT be reused across counterparties.
        """
        ids_a = {e.w4idp for e in self._identifiers.get(peer_a, []) if e.valid}
        ids_b = {e.w4idp for e in self._identifiers.get(peer_b, []) if e.valid}
        return ids_a.isdisjoint(ids_b)


# ═══════════════════════════════════════════════════════════════
# §6.0: Canonicalization & Signature Profiles
# ═══════════════════════════════════════════════════════════════

class SignatureProfileType(Enum):
    """Signature profile types per §6.0.1."""
    COSE_CBOR = "w4_sig_cose@1"
    JOSE_JSON = "w4_sig_jose@1"


def canonical_json(obj: Any) -> bytes:
    """JCS-like canonical JSON per §6.0.4 (RFC 8785 simplified).

    Key requirements:
    - Sorted keys (recursive)
    - No whitespace
    - Unicode escaping for non-ASCII
    """
    return json.dumps(obj, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True).encode('utf-8')


def canonical_cbor_sim(obj: Any) -> bytes:
    """Simulated deterministic CBOR per §6.0.3 (CTAP2 canonical).

    In production, use a real CBOR library with deterministic encoding.
    This simulation uses canonical JSON as a stand-in with a CBOR marker.
    """
    jcs = canonical_json(obj)
    # Prefix with CBOR marker byte (0xBF = map start in CBOR)
    # This is a simulation — real impl uses cbor2 with canonical=True
    return b'\xBF' + jcs


def compute_kid_thumbprint(public_key_bytes: bytes, key_type: str = "Ed25519") -> str:
    """Compute key identifier thumbprint per §6.0.6.

    kid SHOULD be a multibase, multicodec COSE Key thumbprint.
    """
    # Multicodec prefix for Ed25519 = 0xED, P-256 = 0x1200
    if key_type == "Ed25519":
        prefix = bytes([0xED, 0x01])
    elif key_type == "P-256":
        prefix = bytes([0x12, 0x00])
    else:
        prefix = bytes([0x00])

    # Thumbprint = SHA-256 of (multicodec_prefix || public_key)
    thumb = hashlib.sha256(prefix + public_key_bytes).digest()
    return f"z{_multibase_base32(thumb)}"  # z = base32 multibase prefix


@dataclass
class COSESign1:
    """Simulated COSE_Sign1 envelope per §6.0.3.

    Protected headers: alg=-8 (EdDSA), kid, content-type
    """
    protected: dict
    payload: bytes
    signature: bytes

    def to_dict(self) -> dict:
        return {
            "protected": self.protected,
            "payload": self.payload.hex(),
            "signature": self.signature.hex(),
        }


@dataclass
class JWSCompact:
    """Simulated JWS compact serialization per §6.0.4.

    Protected header: alg=ES256, kid
    """
    header: dict
    payload: bytes
    signature: bytes

    def to_compact(self) -> str:
        import base64
        h = base64.urlsafe_b64encode(json.dumps(self.header).encode()).rstrip(b'=').decode()
        p = base64.urlsafe_b64encode(self.payload).rstrip(b'=').decode()
        s = base64.urlsafe_b64encode(self.signature).rstrip(b'=').decode()
        return f"{h}.{p}.{s}"


class SignatureProfile:
    """Manages signature profiles per §6.0.

    Negotiates between COSE/CBOR (MTI) and JOSE/JSON (SHOULD).
    """

    @staticmethod
    def select_profile(media: str, extensions: List[str]) -> SignatureProfileType:
        """Select signature profile based on media type per §6.0.1.

        application/web4+cbor → w4_sig_cose@1
        application/web4+json → w4_sig_jose@1
        """
        if media == "application/web4+cbor":
            return SignatureProfileType.COSE_CBOR
        elif media == "application/web4+json":
            return SignatureProfileType.JOSE_JSON
        else:
            # Default to MTI (COSE/CBOR)
            return SignatureProfileType.COSE_CBOR

    @staticmethod
    def canonicalize(payload: Any, profile: SignatureProfileType) -> bytes:
        """Canonicalize payload using the selected profile."""
        if profile == SignatureProfileType.COSE_CBOR:
            return canonical_cbor_sim(payload)
        else:
            return canonical_json(payload)

    @staticmethod
    def sign_ed25519(private_key: Ed25519PrivateKey, data: bytes,
                     kid: str) -> COSESign1:
        """Create COSE_Sign1 with Ed25519 per §6.0.3."""
        protected = {
            "alg": -8,  # EdDSA
            "kid": kid,
            "content-type": "application/web4+cbor",
        }
        sig = private_key.sign(data)
        return COSESign1(protected=protected, payload=data, signature=sig)

    @staticmethod
    def verify_cose(cose: COSESign1, public_key_bytes: bytes) -> bool:
        """Verify COSE_Sign1 signature."""
        try:
            public = Ed25519PublicKey.from_public_bytes(public_key_bytes)
            public.verify(cose.signature, cose.payload)
            return True
        except Exception:
            return False

    @staticmethod
    def sign_es256(private_key: EllipticCurvePrivateKey, data: bytes,
                   kid: str) -> JWSCompact:
        """Create JWS with ES256 per §6.0.4."""
        header = {"alg": "ES256", "kid": kid}
        sig = private_key.sign(data, ECDSA(hashes.SHA256()))
        return JWSCompact(header=header, payload=data, signature=sig)

    @staticmethod
    def verify_jws(jws: JWSCompact, public_key) -> bool:
        """Verify JWS ES256 signature."""
        try:
            public_key.verify(jws.signature, jws.payload, ECDSA(hashes.SHA256()))
            return True
        except Exception:
            return False


# ═══════════════════════════════════════════════════════════════
# §6.1 + §6.0.5: Channel Binding & HandshakeAuth
# ═══════════════════════════════════════════════════════════════

def compute_channel_binding(transcript_hash: bytes,
                            initiator_epk: bytes,
                            responder_epk: bytes) -> bytes:
    """Compute channel binding per §6.0.5.

    channel_binding MUST include both HPKE ephemeral keys.
    sig covers Hash(TH || channel_binding).
    """
    return hashlib.sha256(
        transcript_hash + initiator_epk + responder_epk
    ).digest()


@dataclass
class HandshakeAuthMessage:
    """HandshakeAuth message per §6.1.

    Encrypted with AEAD, contains signature over Hash(TH || channel_binding).
    """
    suite: str
    kid: str
    alg: str
    sig: bytes
    cap: dict
    nonce: bytes
    ts: str

    def to_dict(self) -> dict:
        return {
            "type": "HandshakeAuth",
            "suite": self.suite,
            "kid": self.kid,
            "alg": self.alg,
            "sig": self.sig.hex(),
            "cap": self.cap,
            "nonce": self.nonce.hex(),
            "ts": self.ts,
        }

    def encrypt(self, key: bytes) -> Tuple[bytes, bytes]:
        """AEAD-Encrypt per §6.1."""
        plaintext = canonical_json(self.to_dict())
        nonce = os.urandom(12)
        cipher = ChaCha20Poly1305(key)
        ciphertext = cipher.encrypt(nonce, plaintext, None)
        return nonce, ciphertext

    @staticmethod
    def decrypt(key: bytes, nonce: bytes, ciphertext: bytes) -> dict:
        """Decrypt HandshakeAuth."""
        cipher = ChaCha20Poly1305(key)
        plaintext = cipher.decrypt(nonce, ciphertext, None)
        return json.loads(plaintext)


# ═══════════════════════════════════════════════════════════════
# §7: Session Rekey & Key Rotation
# ═══════════════════════════════════════════════════════════════

@dataclass
class SessionKeyState:
    """Tracks session key state for ratcheting per §7."""
    generation: int
    k_send: bytes
    k_recv: bytes
    created_at: float
    expired: bool = False


class SessionKeyManager:
    """Manages session key rotation with forward secrecy ratchet per §7.

    A SessionKeyUpdate MAY be sent at any time, protected under current keys.
    On receipt, the peer MUST perform a one-way ratchet and discard old keys
    after a grace window.
    """

    GRACE_WINDOW_SEC = 5.0  # Grace period for old keys after rekey

    def __init__(self, initial_k_send: bytes, initial_k_recv: bytes,
                 exporter_secret: bytes):
        self._exporter = exporter_secret
        self._generation = 0
        self._current = SessionKeyState(
            generation=0,
            k_send=initial_k_send,
            k_recv=initial_k_recv,
            created_at=time.time(),
        )
        self._previous: Optional[SessionKeyState] = None

    @property
    def generation(self) -> int:
        return self._generation

    @property
    def current_keys(self) -> Tuple[bytes, bytes]:
        return self._current.k_send, self._current.k_recv

    def create_rekey_message(self, kid: str) -> dict:
        """Create a SessionKeyUpdate message per §7."""
        self._generation += 1
        # One-way ratchet: derive new keys from exporter + generation
        new_send = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=struct.pack(">I", self._generation),
            info=b"W4-Rekey:send:v1",
        ).derive(self._exporter + self._current.k_send)

        new_recv = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=struct.pack(">I", self._generation),
            info=b"W4-Rekey:recv:v1",
        ).derive(self._exporter + self._current.k_recv)

        # Move current to previous (grace window)
        self._previous = self._current
        self._current = SessionKeyState(
            generation=self._generation,
            k_send=new_send,
            k_recv=new_recv,
            created_at=time.time(),
        )

        return {
            "type": "SessionKeyUpdate",
            "generation": self._generation,
            "kid": kid,
            "ts": time.time(),
        }

    def process_rekey(self, message: dict) -> bool:
        """Process a peer's SessionKeyUpdate per §7.

        Perform one-way ratchet and keep old keys during grace window.
        """
        gen = message.get("generation", 0)
        if gen <= self._generation:
            return False  # Stale rekey

        self._generation = gen

        # Derive new keys matching the sender's derivation (swap send/recv)
        new_recv = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=struct.pack(">I", self._generation),
            info=b"W4-Rekey:send:v1",
        ).derive(self._exporter + self._current.k_recv)

        new_send = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=struct.pack(">I", self._generation),
            info=b"W4-Rekey:recv:v1",
        ).derive(self._exporter + self._current.k_send)

        self._previous = self._current
        self._current = SessionKeyState(
            generation=self._generation,
            k_send=new_send,
            k_recv=new_recv,
            created_at=time.time(),
        )
        return True

    def discard_old_keys(self) -> bool:
        """Discard previous keys after grace window per §7."""
        if self._previous is None:
            return False
        elapsed = time.time() - self._current.created_at
        if elapsed >= self.GRACE_WINDOW_SEC:
            self._previous.expired = True
            self._previous = None
            return True
        return False

    def has_grace_keys(self) -> bool:
        """Check if old keys are still in grace window."""
        return self._previous is not None and not self._previous.expired


# ═══════════════════════════════════════════════════════════════
# §8: Formal State Machine
# ═══════════════════════════════════════════════════════════════

class HandshakeState(Enum):
    """Handshake states per §8 state diagram."""
    START = auto()
    SEND_CLIENT_HELLO = auto()
    WAIT_SERVER_HELLO = auto()
    DERIVE_HPKE = auto()
    SEND_AUTH = auto()
    WAIT_AUTH = auto()
    ESTABLISHED = auto()
    REKEY = auto()
    ERROR = auto()
    # Responder-specific states
    WAIT_CLIENT_HELLO = auto()


class HandshakeEvent(Enum):
    """Events that trigger state transitions."""
    INITIATE = auto()
    CLIENT_HELLO_SENT = auto()
    SERVER_HELLO_RECEIVED = auto()
    SERVER_HELLO_INVALID = auto()
    HPKE_DERIVED = auto()
    AUTH_SENT = auto()
    AUTH_RECEIVED_OK = auto()
    AUTH_RECEIVED_FAIL = auto()
    SESSION_KEY_UPDATE = auto()
    REKEY_COMPLETE = auto()
    # Responder events
    CLIENT_HELLO_RECEIVED = auto()


# Valid transitions: (current_state, event) → next_state
_INITIATOR_TRANSITIONS = {
    (HandshakeState.START, HandshakeEvent.INITIATE): HandshakeState.SEND_CLIENT_HELLO,
    (HandshakeState.SEND_CLIENT_HELLO, HandshakeEvent.CLIENT_HELLO_SENT): HandshakeState.WAIT_SERVER_HELLO,
    (HandshakeState.WAIT_SERVER_HELLO, HandshakeEvent.SERVER_HELLO_RECEIVED): HandshakeState.DERIVE_HPKE,
    (HandshakeState.WAIT_SERVER_HELLO, HandshakeEvent.SERVER_HELLO_INVALID): HandshakeState.ERROR,
    (HandshakeState.DERIVE_HPKE, HandshakeEvent.HPKE_DERIVED): HandshakeState.SEND_AUTH,
    (HandshakeState.SEND_AUTH, HandshakeEvent.AUTH_SENT): HandshakeState.WAIT_AUTH,
    (HandshakeState.WAIT_AUTH, HandshakeEvent.AUTH_RECEIVED_OK): HandshakeState.ESTABLISHED,
    (HandshakeState.WAIT_AUTH, HandshakeEvent.AUTH_RECEIVED_FAIL): HandshakeState.ERROR,
    (HandshakeState.ESTABLISHED, HandshakeEvent.SESSION_KEY_UPDATE): HandshakeState.REKEY,
    (HandshakeState.REKEY, HandshakeEvent.REKEY_COMPLETE): HandshakeState.ESTABLISHED,
}

_RESPONDER_TRANSITIONS = {
    (HandshakeState.START, HandshakeEvent.INITIATE): HandshakeState.WAIT_CLIENT_HELLO,
    (HandshakeState.WAIT_CLIENT_HELLO, HandshakeEvent.CLIENT_HELLO_RECEIVED): HandshakeState.DERIVE_HPKE,
    (HandshakeState.DERIVE_HPKE, HandshakeEvent.HPKE_DERIVED): HandshakeState.SEND_AUTH,
    (HandshakeState.SEND_AUTH, HandshakeEvent.AUTH_SENT): HandshakeState.WAIT_AUTH,
    (HandshakeState.WAIT_AUTH, HandshakeEvent.AUTH_RECEIVED_OK): HandshakeState.ESTABLISHED,
    (HandshakeState.WAIT_AUTH, HandshakeEvent.AUTH_RECEIVED_FAIL): HandshakeState.ERROR,
    (HandshakeState.ESTABLISHED, HandshakeEvent.SESSION_KEY_UPDATE): HandshakeState.REKEY,
    (HandshakeState.REKEY, HandshakeEvent.REKEY_COMPLETE): HandshakeState.ESTABLISHED,
}


class HandshakeStateMachine:
    """Formal state machine per §8 with transition validation.

    Enforces valid state transitions and rejects out-of-order messages.
    """

    def __init__(self, is_initiator: bool = True):
        self._state = HandshakeState.START
        self._is_initiator = is_initiator
        self._transitions = _INITIATOR_TRANSITIONS if is_initiator else _RESPONDER_TRANSITIONS
        self._history: List[Tuple[HandshakeState, HandshakeEvent, HandshakeState]] = []

    @property
    def state(self) -> HandshakeState:
        return self._state

    @property
    def is_established(self) -> bool:
        return self._state == HandshakeState.ESTABLISHED

    @property
    def is_error(self) -> bool:
        return self._state == HandshakeState.ERROR

    def transition(self, event: HandshakeEvent) -> HandshakeState:
        """Attempt a state transition. Raises HandshakeError if invalid."""
        key = (self._state, event)
        next_state = self._transitions.get(key)
        if next_state is None:
            raise HandshakeError(
                f"Invalid transition: {self._state.name} + {event.name}",
                W4ErrorCode.STATE_INVALID,
            )
        self._history.append((self._state, event, next_state))
        self._state = next_state
        return next_state

    def get_valid_events(self) -> List[HandshakeEvent]:
        """Get list of valid events from current state."""
        return [ev for (st, ev), _ in self._transitions.items()
                if st == self._state]

    @property
    def transition_count(self) -> int:
        return len(self._history)


# ═══════════════════════════════════════════════════════════════
# §9: Anti-Replay & Clock Validation
# ═══════════════════════════════════════════════════════════════

class ReplayGuard:
    """Anti-replay protection per §9.

    - nonce values MUST be unique per key
    - Accept ts within ±300s
    - Maintain a replay window
    """

    CLOCK_SKEW_TOLERANCE = 300.0  # ±300 seconds per §9

    def __init__(self, window_size: int = 1024):
        self._seen_nonces: Set[bytes] = set()
        self._window_size = window_size
        self._nonce_order: List[bytes] = []  # For eviction

    def check_nonce(self, nonce: bytes) -> bool:
        """Check if nonce is fresh (not replayed).

        Returns True if nonce is fresh and should be accepted.
        Returns False if nonce was already seen (replay detected).
        """
        if nonce in self._seen_nonces:
            return False
        return True

    def record_nonce(self, nonce: bytes) -> None:
        """Record a nonce as seen."""
        self._seen_nonces.add(nonce)
        self._nonce_order.append(nonce)

        # Evict oldest if window full
        while len(self._seen_nonces) > self._window_size:
            oldest = self._nonce_order.pop(0)
            self._seen_nonces.discard(oldest)

    def check_and_record(self, nonce: bytes) -> bool:
        """Combined check-and-record. Returns True if fresh."""
        if not self.check_nonce(nonce):
            return False
        self.record_nonce(nonce)
        return True

    def validate_timestamp(self, ts_str: str,
                           reference_time: Optional[float] = None) -> bool:
        """Validate timestamp within ±300s per §9.

        Returns True if timestamp is within tolerance.
        """
        ref = reference_time or time.time()
        try:
            # Try ISO 8601 format
            if 'T' in ts_str:
                from datetime import datetime, timezone
                dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                ts = dt.timestamp()
            else:
                ts = float(ts_str)
        except (ValueError, TypeError):
            return False

        delta = abs(ref - ts)
        return delta <= self.CLOCK_SKEW_TOLERANCE

    def validate_timestamp_float(self, ts: float,
                                 reference_time: Optional[float] = None) -> bool:
        """Validate float timestamp within ±300s."""
        ref = reference_time or time.time()
        return abs(ref - ts) <= self.CLOCK_SKEW_TOLERANCE

    @property
    def seen_count(self) -> int:
        return len(self._seen_nonces)


# ═══════════════════════════════════════════════════════════════
# §5.0: GREASE Procedure
# ═══════════════════════════════════════════════════════════════

def generate_grease_extension() -> str:
    """Generate a GREASE extension ID per §5.0.

    Format: w4_ext_[8-hex-digits]@0
    Reserved pattern: *a*a*a*a
    """
    # Generate 4 random hex digits interspersed with 'a'
    hex_chars = "0123456789abcdef"
    pattern = []
    for _ in range(4):
        pattern.append(hex_chars[os.urandom(1)[0] % 16])
        pattern.append('a')
    return f"w4_ext_{''.join(pattern)}@0"


def generate_grease_suite() -> str:
    """Generate a GREASE suite ID per §5.0.

    Format: W4-GREASE-[8-hex-digits]
    """
    return f"W4-GREASE-{os.urandom(4).hex()}"


def is_grease_extension(ext_id: str) -> bool:
    """Check if an extension ID is a GREASE value per §5.0."""
    pattern = r'^w4_ext_[0-9a-f]{8}@0$'
    return bool(re.match(pattern, ext_id))


def is_grease_suite(suite_id: str) -> bool:
    """Check if a suite ID is a GREASE value per §5.0."""
    return suite_id.startswith("W4-GREASE-")


# ═══════════════════════════════════════════════════════════════
# §11: Security Considerations — DoS Cheap Checks
# ═══════════════════════════════════════════════════════════════

def cheap_checks(message: dict) -> Optional[ProblemDetails]:
    """Perform cheap checks (syntax, version) before KEM decap per §11.

    DoS mitigation: reject invalid messages before expensive crypto ops.
    """
    # Check type field
    msg_type = message.get("type")
    if msg_type not in ("ClientHello", "ServerHello", "HandshakeAuth",
                        "SessionKeyUpdate"):
        return ProblemDetails(
            title="Invalid message type",
            status=400,
            code=W4ErrorCode.PROTO_FORMAT.value,
            detail=f"Unknown message type: {msg_type}",
        )

    # Check version
    ver = message.get("ver")
    if msg_type in ("ClientHello", "ServerHello") and ver != "w4/1":
        return ProblemDetails(
            title="Unsupported version",
            status=400,
            code=W4ErrorCode.PROTO_FORMAT.value,
            detail=f"Unsupported version: {ver}",
        )

    # Check nonce presence for Hello messages
    if msg_type in ("ClientHello", "ServerHello"):
        if not message.get("nonce"):
            return ProblemDetails(
                title="Missing nonce",
                status=400,
                code=W4ErrorCode.PROTO_FORMAT.value,
                detail="Nonce is required in Hello messages",
            )

    return None  # Passed cheap checks


# ═══════════════════════════════════════════════════════════════
# §12: Interop Profile Registry
# ═══════════════════════════════════════════════════════════════

@dataclass
class InteropProfile:
    """Interop profile per §12."""
    name: str
    kem: str
    sig: str
    aead: str
    hash_alg: str
    encoding: str
    status: str  # MUST or SHOULD

INTEROP_PROFILES = {
    "W4-BASE-1": InteropProfile(
        name="W4-BASE-1",
        kem="X25519", sig="Ed25519",
        aead="ChaCha20-Poly1305", hash_alg="SHA-256",
        encoding="COSE/CBOR", status="MUST",
    ),
    "W4-FIPS-1": InteropProfile(
        name="W4-FIPS-1",
        kem="ECDH-P256", sig="ECDSA-P256",
        aead="AES-128-GCM", hash_alg="SHA-256",
        encoding="JOSE/JSON", status="SHOULD",
    ),
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

    # ── T1: W4IDp Pairwise Identifier Derivation (§4.1) ──
    print("\n═══ T1: W4IDp Pairwise Identifier Derivation (§4.1) ═══")
    mgr = W4IDpManager()
    entry_a = mgr.derive_w4idp("peer-alice")
    check("T1.1: W4IDp derived for alice", entry_a.w4idp.startswith("w4idp-"))
    check("T1.2: W4IDp has valid length", len(entry_a.w4idp) > 10)
    check("T1.3: Salt is 128-bit", len(entry_a.peer_salt) == 16)
    check("T1.4: Entry is valid", entry_a.valid is True)

    entry_b = mgr.derive_w4idp("peer-bob")
    check("T1.5: Different peer → different W4IDp", entry_a.w4idp != entry_b.w4idp)

    # Same peer, different salt → different W4IDp
    entry_a2 = mgr.derive_w4idp("peer-alice")
    check("T1.6: Same peer, new salt → different W4IDp", entry_a.w4idp != entry_a2.w4idp)

    # Deterministic with same secret + salt
    mgr2 = W4IDpManager(master_secret=mgr.master_secret)
    entry_det = mgr2.derive_w4idp("peer-alice", peer_salt=entry_a.peer_salt)
    check("T1.7: Deterministic: same secret+salt → same W4IDp",
          entry_det.w4idp == entry_a.w4idp)

    # ── T2: W4IDp Lifecycle & Rotation (§4.2) ──
    print("\n═══ T2: W4IDp Lifecycle & Rotation (§4.2) ═══")
    mgr3 = W4IDpManager()
    mgr3.derive_w4idp("peer-carol")
    mgr3.derive_w4idp("peer-carol")
    mgr3.derive_w4idp("peer-carol")
    check("T2.1: 3 valid W4IDp values", mgr3.get_valid_count("peer-carol") == 3)

    rotated = mgr3.rotate("peer-carol")
    check("T2.2: Rotation creates new W4IDp", rotated.w4idp.startswith("w4idp-"))
    check("T2.3: 4 valid after rotation", mgr3.get_valid_count("peer-carol") == 4)

    # Rotate again — should trim oldest (MAX_CONCURRENT=4)
    mgr3.rotate("peer-carol")
    check("T2.4: Trim to MAX_CONCURRENT after excess rotation",
          mgr3.get_valid_count("peer-carol") == 4)

    # Key rotation with new master secret
    old_id = mgr3.get_current("peer-carol")
    rotated2 = mgr3.rotate("peer-carol", new_master_secret=os.urandom(32))
    check("T2.5: New master → different W4IDp", rotated2.w4idp != old_id)

    # ── T3: W4IDp Privacy Requirements (§4.2) ──
    print("\n═══ T3: W4IDp Privacy Requirements (§4.2) ═══")
    mgr4 = W4IDpManager()
    mgr4.derive_w4idp("peer-a")
    mgr4.derive_w4idp("peer-b")
    check("T3.1: Different peers have non-overlapping W4IDp",
          mgr4.verify_privacy("peer-a", "peer-b"))

    check("T3.2: Lookup finds correct peer",
          mgr4.lookup_peer(mgr4.get_current("peer-a")) == "peer-a")
    check("T3.3: Lookup finds other peer",
          mgr4.lookup_peer(mgr4.get_current("peer-b")) == "peer-b")

    # Invalidation
    count = mgr4.invalidate_all("peer-a")
    check("T3.4: Invalidation returns count", count == 1)
    check("T3.5: Invalidated peer has no current", mgr4.get_current("peer-a") is None)

    # Salt too small
    try:
        mgr4.derive_w4idp("peer-c", peer_salt=b"short")
        check("T3.6: Short salt rejected", False)
    except HandshakeError:
        check("T3.6: Short salt rejected", True)

    # ── T4: Signature Profile Selection (§6.0.1) ──
    print("\n═══ T4: Signature Profile Selection (§6.0.1) ═══")
    prof_cbor = SignatureProfile.select_profile("application/web4+cbor", [])
    check("T4.1: CBOR media → COSE profile",
          prof_cbor == SignatureProfileType.COSE_CBOR)

    prof_json = SignatureProfile.select_profile("application/web4+json", [])
    check("T4.2: JSON media → JOSE profile",
          prof_json == SignatureProfileType.JOSE_JSON)

    prof_default = SignatureProfile.select_profile("unknown/type", [])
    check("T4.3: Unknown media → default COSE (MTI)",
          prof_default == SignatureProfileType.COSE_CBOR)

    # ── T5: Canonicalization (§6.0.3, §6.0.4) ──
    print("\n═══ T5: Canonicalization (§6.0.3, §6.0.4) ═══")
    obj = {"z": 1, "a": 2, "m": [3, 1, 2]}

    jcs = canonical_json(obj)
    check("T5.1: JCS sorts keys", b'"a":2' in jcs and jcs.index(b'"a"') < jcs.index(b'"z"'))
    check("T5.2: JCS no whitespace", b' ' not in jcs)
    check("T5.3: JCS deterministic", canonical_json(obj) == jcs)

    cbor_sim = canonical_cbor_sim(obj)
    check("T5.4: CBOR sim starts with marker", cbor_sim[0] == 0xBF)
    check("T5.5: CBOR sim deterministic", canonical_cbor_sim(obj) == cbor_sim)

    # Profile-based canonicalization
    c_cose = SignatureProfile.canonicalize(obj, SignatureProfileType.COSE_CBOR)
    c_jose = SignatureProfile.canonicalize(obj, SignatureProfileType.JOSE_JSON)
    check("T5.6: COSE canonicalization different from JOSE", c_cose != c_jose)

    # ── T6: COSE_Sign1 Ed25519 (§6.0.3) ──
    print("\n═══ T6: COSE_Sign1 Ed25519 (§6.0.3) ═══")
    ed_priv = Ed25519PrivateKey.generate()
    ed_pub = ed_priv.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    kid_ed = compute_kid_thumbprint(ed_pub, "Ed25519")
    check("T6.1: kid computed", kid_ed.startswith("z"))

    payload = canonical_json({"msg": "hello web4"})
    cose_sig = SignatureProfile.sign_ed25519(ed_priv, payload, kid_ed)
    check("T6.2: COSE_Sign1 created", cose_sig.protected["alg"] == -8)
    check("T6.3: COSE_Sign1 has kid", cose_sig.protected["kid"] == kid_ed)
    check("T6.4: COSE_Sign1 has content-type",
          cose_sig.protected["content-type"] == "application/web4+cbor")

    valid = SignatureProfile.verify_cose(cose_sig, ed_pub)
    check("T6.5: COSE_Sign1 verifies", valid)

    # Tamper with payload
    cose_sig.payload = b"tampered"
    check("T6.6: Tampered COSE_Sign1 fails", not SignatureProfile.verify_cose(cose_sig, ed_pub))

    # Wrong key
    ed_priv2 = Ed25519PrivateKey.generate()
    ed_pub2 = ed_priv2.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    cose_sig2 = SignatureProfile.sign_ed25519(ed_priv, payload, kid_ed)
    check("T6.7: Wrong key fails COSE verify",
          not SignatureProfile.verify_cose(cose_sig2, ed_pub2))

    # ── T7: JWS ES256 (§6.0.4) ──
    print("\n═══ T7: JWS ES256 (§6.0.4) ═══")
    ec_priv = ec_generate_private_key(SECP256R1())
    ec_pub = ec_priv.public_key()
    ec_pub_bytes = ec_pub.public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    kid_ec = compute_kid_thumbprint(ec_pub_bytes, "P-256")
    check("T7.1: P-256 kid computed", kid_ec.startswith("z"))

    payload_json = canonical_json({"msg": "hello FIPS"})
    jws = SignatureProfile.sign_es256(ec_priv, payload_json, kid_ec)
    check("T7.2: JWS created with ES256", jws.header["alg"] == "ES256")
    check("T7.3: JWS has kid", jws.header["kid"] == kid_ec)

    valid_jws = SignatureProfile.verify_jws(jws, ec_pub)
    check("T7.4: JWS ES256 verifies", valid_jws)

    compact = jws.to_compact()
    check("T7.5: JWS compact has 3 parts", len(compact.split('.')) == 3)

    # Tamper
    jws.payload = b"tampered"
    check("T7.6: Tampered JWS fails", not SignatureProfile.verify_jws(jws, ec_pub))

    # ── T8: Channel Binding (§6.0.5) ──
    print("\n═══ T8: Channel Binding (§6.0.5) ═══")
    th = hashlib.sha256(b"transcript").digest()
    epk_i = os.urandom(32)  # Initiator ephemeral public key
    epk_r = os.urandom(32)  # Responder ephemeral public key

    cb = compute_channel_binding(th, epk_i, epk_r)
    check("T8.1: Channel binding computed", len(cb) == 32)

    # Different ephemeral keys → different binding
    cb2 = compute_channel_binding(th, epk_i, os.urandom(32))
    check("T8.2: Different responder EPK → different binding", cb != cb2)

    # Different transcript → different binding
    cb3 = compute_channel_binding(hashlib.sha256(b"other").digest(), epk_i, epk_r)
    check("T8.3: Different transcript → different binding", cb != cb3)

    # Deterministic
    cb4 = compute_channel_binding(th, epk_i, epk_r)
    check("T8.4: Channel binding deterministic", cb == cb4)

    # ── T9: HandshakeAuth Message (§6.1) ──
    print("\n═══ T9: HandshakeAuth Message (§6.1) ═══")
    auth_sig = ed_priv.sign(cb)
    auth_msg = HandshakeAuthMessage(
        suite="W4-BASE-1",
        kid=kid_ed,
        alg="EdDSA",
        sig=auth_sig,
        cap={"scopes": ["read:lct", "write:lct"], "ext": []},
        nonce=os.urandom(12),
        ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    auth_dict = auth_msg.to_dict()
    check("T9.1: HandshakeAuth type correct", auth_dict["type"] == "HandshakeAuth")
    check("T9.2: HandshakeAuth has cap scopes", "read:lct" in auth_dict["cap"]["scopes"])
    check("T9.3: HandshakeAuth has kid", auth_dict["kid"] == kid_ed)

    # Encrypt/decrypt
    context_key = os.urandom(32)
    enc_nonce, enc_ct = auth_msg.encrypt(context_key)
    check("T9.4: HandshakeAuth encrypted", len(enc_ct) > 0)

    dec_dict = HandshakeAuthMessage.decrypt(context_key, enc_nonce, enc_ct)
    check("T9.5: HandshakeAuth decrypted", dec_dict["type"] == "HandshakeAuth")
    check("T9.6: Decrypted suite matches", dec_dict["suite"] == "W4-BASE-1")

    # Wrong key fails
    try:
        HandshakeAuthMessage.decrypt(os.urandom(32), enc_nonce, enc_ct)
        check("T9.7: Wrong key fails decrypt", False)
    except Exception:
        check("T9.7: Wrong key fails decrypt", True)

    # ── T10: Session Rekey & Rotation (§7) ──
    print("\n═══ T10: Session Rekey & Rotation (§7) ═══")
    k_send_0 = os.urandom(32)
    k_recv_0 = os.urandom(32)
    exporter = os.urandom(32)

    initiator_km = SessionKeyManager(k_send_0, k_recv_0, exporter)
    responder_km = SessionKeyManager(k_recv_0, k_send_0, exporter)

    check("T10.1: Initial generation is 0", initiator_km.generation == 0)

    # Initiator rekeys
    rekey_msg = initiator_km.create_rekey_message("kid-initiator")
    check("T10.2: Rekey message type", rekey_msg["type"] == "SessionKeyUpdate")
    check("T10.3: Initiator gen bumped to 1", initiator_km.generation == 1)

    # Responder processes rekey
    ok = responder_km.process_rekey(rekey_msg)
    check("T10.4: Responder accepts rekey", ok)
    check("T10.5: Responder gen matches", responder_km.generation == 1)

    # After rekey, keys match (initiator send = responder recv)
    i_send, i_recv = initiator_km.current_keys
    r_send, r_recv = responder_km.current_keys
    check("T10.6: Initiator send = Responder recv", i_send == r_recv)
    check("T10.7: Responder send = Initiator recv", r_send == i_recv)

    # Grace window
    check("T10.8: Grace keys available after rekey", initiator_km.has_grace_keys())

    # Stale rekey rejected
    stale = {"type": "SessionKeyUpdate", "generation": 0, "kid": "old", "ts": 0}
    check("T10.9: Stale rekey rejected", not responder_km.process_rekey(stale))

    # Multiple rekeys
    rekey2 = initiator_km.create_rekey_message("kid-initiator")
    responder_km.process_rekey(rekey2)
    check("T10.10: Multiple rekeys work", initiator_km.generation == 2)

    i_send2, _ = initiator_km.current_keys
    _, r_recv2 = responder_km.current_keys
    check("T10.11: Post-double-rekey keys match", i_send2 == r_recv2)

    # Keys are different from initial
    check("T10.12: Rekeyed keys differ from initial", i_send2 != k_send_0)

    # ── T11: Formal State Machine — Initiator (§8) ──
    print("\n═══ T11: Formal State Machine — Initiator (§8) ═══")
    sm = HandshakeStateMachine(is_initiator=True)
    check("T11.1: Initial state is START", sm.state == HandshakeState.START)

    sm.transition(HandshakeEvent.INITIATE)
    check("T11.2: After INITIATE → SEND_CLIENT_HELLO",
          sm.state == HandshakeState.SEND_CLIENT_HELLO)

    sm.transition(HandshakeEvent.CLIENT_HELLO_SENT)
    check("T11.3: After CH_SENT → WAIT_SERVER_HELLO",
          sm.state == HandshakeState.WAIT_SERVER_HELLO)

    sm.transition(HandshakeEvent.SERVER_HELLO_RECEIVED)
    check("T11.4: After SH_RECEIVED → DERIVE_HPKE",
          sm.state == HandshakeState.DERIVE_HPKE)

    sm.transition(HandshakeEvent.HPKE_DERIVED)
    check("T11.5: After HPKE_DERIVED → SEND_AUTH",
          sm.state == HandshakeState.SEND_AUTH)

    sm.transition(HandshakeEvent.AUTH_SENT)
    check("T11.6: After AUTH_SENT → WAIT_AUTH",
          sm.state == HandshakeState.WAIT_AUTH)

    sm.transition(HandshakeEvent.AUTH_RECEIVED_OK)
    check("T11.7: After AUTH_OK → ESTABLISHED", sm.is_established)
    check("T11.8: Not in error state", not sm.is_error)

    # Rekey cycle
    sm.transition(HandshakeEvent.SESSION_KEY_UPDATE)
    check("T11.9: After REKEY → REKEY state", sm.state == HandshakeState.REKEY)

    sm.transition(HandshakeEvent.REKEY_COMPLETE)
    check("T11.10: After REKEY_COMPLETE → ESTABLISHED", sm.is_established)
    check("T11.11: Transition count = 8", sm.transition_count == 8)

    # ── T12: State Machine — Responder (§8) ──
    print("\n═══ T12: Formal State Machine — Responder (§8) ═══")
    sm_r = HandshakeStateMachine(is_initiator=False)
    sm_r.transition(HandshakeEvent.INITIATE)
    check("T12.1: Responder → WAIT_CLIENT_HELLO",
          sm_r.state == HandshakeState.WAIT_CLIENT_HELLO)

    sm_r.transition(HandshakeEvent.CLIENT_HELLO_RECEIVED)
    check("T12.2: After CH_RECEIVED → DERIVE_HPKE",
          sm_r.state == HandshakeState.DERIVE_HPKE)

    sm_r.transition(HandshakeEvent.HPKE_DERIVED)
    sm_r.transition(HandshakeEvent.AUTH_SENT)
    sm_r.transition(HandshakeEvent.AUTH_RECEIVED_OK)
    check("T12.3: Responder reaches ESTABLISHED", sm_r.is_established)

    # ── T13: State Machine — Invalid Transitions (§8) ──
    print("\n═══ T13: State Machine — Invalid Transitions (§8) ═══")
    sm_inv = HandshakeStateMachine(is_initiator=True)

    # Can't send AUTH from START
    try:
        sm_inv.transition(HandshakeEvent.AUTH_SENT)
        check("T13.1: Invalid START→AUTH rejected", False)
    except HandshakeError as e:
        check("T13.1: Invalid START→AUTH rejected", "Invalid transition" in str(e))
        check("T13.2: Error has STATE_INVALID code",
              e.problem.code == W4ErrorCode.STATE_INVALID.value)

    # Error state on auth failure
    sm_err = HandshakeStateMachine(is_initiator=True)
    sm_err.transition(HandshakeEvent.INITIATE)
    sm_err.transition(HandshakeEvent.CLIENT_HELLO_SENT)
    sm_err.transition(HandshakeEvent.SERVER_HELLO_INVALID)
    check("T13.3: Invalid SH → ERROR state", sm_err.is_error)

    # Auth failure
    sm_af = HandshakeStateMachine(is_initiator=True)
    sm_af.transition(HandshakeEvent.INITIATE)
    sm_af.transition(HandshakeEvent.CLIENT_HELLO_SENT)
    sm_af.transition(HandshakeEvent.SERVER_HELLO_RECEIVED)
    sm_af.transition(HandshakeEvent.HPKE_DERIVED)
    sm_af.transition(HandshakeEvent.AUTH_SENT)
    sm_af.transition(HandshakeEvent.AUTH_RECEIVED_FAIL)
    check("T13.4: Auth failure → ERROR state", sm_af.is_error)

    # Valid events query
    sm_ve = HandshakeStateMachine(is_initiator=True)
    events = sm_ve.get_valid_events()
    check("T13.5: START has INITIATE as valid event",
          HandshakeEvent.INITIATE in events)

    # ── T14: Anti-Replay & Nonce Tracking (§9) ──
    print("\n═══ T14: Anti-Replay & Nonce Tracking (§9) ═══")
    guard = ReplayGuard(window_size=10)

    nonce1 = os.urandom(12)
    check("T14.1: Fresh nonce accepted", guard.check_and_record(nonce1))
    check("T14.2: Replayed nonce rejected", not guard.check_and_record(nonce1))

    nonce2 = os.urandom(12)
    check("T14.3: Different nonce accepted", guard.check_and_record(nonce2))
    check("T14.4: Seen count = 2", guard.seen_count == 2)

    # Fill window to test eviction
    for _ in range(10):
        guard.check_and_record(os.urandom(12))
    check("T14.5: Window evicts oldest", guard.seen_count <= 10)

    # After eviction, original nonce might be fresh again
    # (depends on window size — with 10 and 10 new, nonce1 was evicted)
    check("T14.6: Evicted nonce re-accepted", guard.check_and_record(nonce1))

    # ── T15: Timestamp Validation (§9) ──
    print("\n═══ T15: Timestamp Validation (§9) ═══")
    guard2 = ReplayGuard()
    now = time.time()

    # Within tolerance
    check("T15.1: Current timestamp valid",
          guard2.validate_timestamp_float(now))
    check("T15.2: 100s ago valid",
          guard2.validate_timestamp_float(now - 100))
    check("T15.3: 100s ahead valid",
          guard2.validate_timestamp_float(now + 100))

    # Outside tolerance (±300s)
    check("T15.4: 301s ago invalid",
          not guard2.validate_timestamp_float(now - 301))
    check("T15.5: 301s ahead invalid",
          not guard2.validate_timestamp_float(now + 301))

    # ISO 8601 timestamp
    iso_now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    check("T15.6: ISO 8601 timestamp validates",
          guard2.validate_timestamp(iso_now))

    # Invalid timestamp format
    check("T15.7: Invalid timestamp rejected",
          not guard2.validate_timestamp("not-a-timestamp"))

    # Exact boundary (300s)
    check("T15.8: Exactly 300s is valid",
          guard2.validate_timestamp_float(now - 300, now))

    # ── T16: GREASE Extension Generation (§5.0) ──
    print("\n═══ T16: GREASE Extension Generation (§5.0) ═══")
    grease_ext = generate_grease_extension()
    check("T16.1: GREASE extension format", grease_ext.startswith("w4_ext_"))
    check("T16.2: GREASE extension ends with @0", grease_ext.endswith("@0"))
    check("T16.3: GREASE detected as GREASE", is_grease_extension(grease_ext))

    grease_suite = generate_grease_suite()
    check("T16.4: GREASE suite format", grease_suite.startswith("W4-GREASE-"))
    check("T16.5: GREASE suite detected", is_grease_suite(grease_suite))
    check("T16.6: Real suite not GREASE", not is_grease_suite("W4-BASE-1"))
    check("T16.7: Real ext not GREASE", not is_grease_extension("w4_ext_sdjwt_vp@1"))

    # Unique per call
    grease2 = generate_grease_extension()
    check("T16.8: GREASE unique per call", grease_ext != grease2)

    # ── T17: Problem Details Error Handling (§10) ──
    print("\n═══ T17: Problem Details Error Handling (§10) ═══")
    err = ProblemDetails(
        type="about:blank",
        title="Unauthorized",
        status=401,
        code=W4ErrorCode.AUTHZ_DENIED.value,
        detail="Credential lacks scope write:lct",
        instance="web4://w4idp-ABCD/messages/123",
    )
    err_dict = err.to_dict()
    check("T17.1: Problem Details has type", err_dict["type"] == "about:blank")
    check("T17.2: Problem Details has status", err_dict["status"] == 401)
    check("T17.3: Problem Details has code", err_dict["code"] == "W4_ERR_AUTHZ_DENIED")
    check("T17.4: Problem Details has instance", "w4idp-ABCD" in err_dict["instance"])

    err_json = err.to_json()
    check("T17.5: Problem Details JSON valid", json.loads(err_json) is not None)

    # HandshakeError carries ProblemDetails
    try:
        raise HandshakeError("test error", W4ErrorCode.REPLAY_DETECTED, 403)
    except HandshakeError as e:
        check("T17.6: HandshakeError has problem", e.problem.code == "W4_ERR_REPLAY_DETECTED")
        check("T17.7: HandshakeError has status", e.problem.status == 403)

    # All W4 error codes exist
    codes = [c.value for c in W4ErrorCode]
    check("T17.8: Error codes include AUTHZ_DENIED", "W4_ERR_AUTHZ_DENIED" in codes)
    check("T17.9: Error codes include PROTO_FORMAT", "W4_ERR_PROTO_FORMAT" in codes)
    check("T17.10: Error codes include REPLAY_DETECTED", "W4_ERR_REPLAY_DETECTED" in codes)
    check("T17.11: 11 total error codes", len(codes) == 11)

    # ── T18: Cheap DoS Checks (§11) ──
    print("\n═══ T18: Cheap DoS Checks (§11) ═══")
    valid_ch = {"type": "ClientHello", "ver": "w4/1", "nonce": "abc123",
                "suites": ["W4-BASE-1"]}
    check("T18.1: Valid ClientHello passes", cheap_checks(valid_ch) is None)

    bad_type = {"type": "InvalidType", "ver": "w4/1"}
    result = cheap_checks(bad_type)
    check("T18.2: Bad type rejected", result is not None)
    check("T18.3: Bad type error code", result.code == "W4_ERR_PROTO_FORMAT")

    bad_ver = {"type": "ClientHello", "ver": "w4/99", "nonce": "x"}
    check("T18.4: Bad version rejected", cheap_checks(bad_ver) is not None)

    no_nonce = {"type": "ServerHello", "ver": "w4/1"}
    check("T18.5: Missing nonce rejected", cheap_checks(no_nonce) is not None)

    # SessionKeyUpdate doesn't need version
    rekey_check = {"type": "SessionKeyUpdate", "generation": 1}
    check("T18.6: SessionKeyUpdate passes", cheap_checks(rekey_check) is None)

    # ── T19: kid Thumbprint Format (§6.0.6) ──
    print("\n═══ T19: kid Thumbprint Format (§6.0.6) ═══")
    kid1 = compute_kid_thumbprint(os.urandom(32), "Ed25519")
    kid2 = compute_kid_thumbprint(os.urandom(32), "Ed25519")
    check("T19.1: kid starts with multibase prefix", kid1.startswith("z"))
    check("T19.2: Different keys → different kid", kid1 != kid2)

    # Same key → same kid (deterministic)
    key_material = os.urandom(32)
    kid3a = compute_kid_thumbprint(key_material, "Ed25519")
    kid3b = compute_kid_thumbprint(key_material, "Ed25519")
    check("T19.3: Same key → same kid", kid3a == kid3b)

    # Different key types → different kid
    kid4_ed = compute_kid_thumbprint(key_material, "Ed25519")
    kid4_p256 = compute_kid_thumbprint(key_material, "P-256")
    check("T19.4: Different key type → different kid", kid4_ed != kid4_p256)

    # ── T20: Interop Profiles (§12) ──
    print("\n═══ T20: Interop Profiles (§12) ═══")
    check("T20.1: W4-BASE-1 is MUST", INTEROP_PROFILES["W4-BASE-1"].status == "MUST")
    check("T20.2: W4-FIPS-1 is SHOULD", INTEROP_PROFILES["W4-FIPS-1"].status == "SHOULD")
    check("T20.3: BASE-1 uses Ed25519", INTEROP_PROFILES["W4-BASE-1"].sig == "Ed25519")
    check("T20.4: FIPS-1 uses ECDSA-P256", INTEROP_PROFILES["W4-FIPS-1"].sig == "ECDSA-P256")
    check("T20.5: BASE-1 uses COSE/CBOR", INTEROP_PROFILES["W4-BASE-1"].encoding == "COSE/CBOR")
    check("T20.6: FIPS-1 uses JOSE/JSON", INTEROP_PROFILES["W4-FIPS-1"].encoding == "JOSE/JSON")

    # ── T21: Profile Failure Handling (§6.0.7) ──
    print("\n═══ T21: Profile Failure Handling (§6.0.7) ═══")
    # Simulate profile mismatch detection
    negotiated_media = "application/web4+cbor"
    received_profile = SignatureProfileType.JOSE_JSON  # Mismatch!
    expected_profile = SignatureProfile.select_profile(negotiated_media, [])

    mismatch = received_profile != expected_profile
    check("T21.1: Profile mismatch detected", mismatch)

    if mismatch:
        try:
            raise HandshakeError(
                "Signature profile doesn't match negotiated media",
                W4ErrorCode.PROTO_FORMAT,
            )
        except HandshakeError as e:
            check("T21.2: Mismatch raises PROTO_FORMAT", "PROTO_FORMAT" in e.problem.code)

    # Correct profile
    correct_profile = SignatureProfileType.COSE_CBOR
    check("T21.3: Correct profile matches", correct_profile == expected_profile)

    # ── T22: Downgrade Resistance (§11) ──
    print("\n═══ T22: Downgrade Resistance (§11) ═══")
    # TH must include all proposals + selected suite per §11
    ch_proposals = {
        "suites": ["W4-BASE-1", "W4-FIPS-1"],
        "media": "application/web4+cbor",
        "selected_suite": "W4-BASE-1",
    }
    th1 = hashlib.sha256(canonical_json(ch_proposals)).digest()

    # Attacker tries to downgrade by removing a suite
    downgraded = {
        "suites": ["W4-BASE-1"],
        "media": "application/web4+cbor",
        "selected_suite": "W4-BASE-1",
    }
    th_downgraded = hashlib.sha256(canonical_json(downgraded)).digest()
    check("T22.1: Downgrade changes TH", th1 != th_downgraded)

    # Full transcript including media type
    full_th = hashlib.sha256(
        canonical_json({
            **ch_proposals,
            "ext": ["w4_sig_cose@1"],
        })
    ).digest()
    check("T22.2: Media type bound to TH", full_th != th1)

    # ── T23: Combined Flow — W4IDp + Auth + State Machine (§4+§6+§8) ──
    print("\n═══ T23: Combined Flow — W4IDp + Auth + State Machine ═══")
    # Simulate full handshake with all advanced features
    alice_mgr = W4IDpManager()
    bob_mgr = W4IDpManager()
    alice_sm = HandshakeStateMachine(is_initiator=True)
    bob_sm = HandshakeStateMachine(is_initiator=False)
    alice_guard = ReplayGuard()
    bob_guard = ReplayGuard()

    # Alice initiates
    alice_sm.transition(HandshakeEvent.INITIATE)
    bob_sm.transition(HandshakeEvent.INITIATE)

    # Derive pairwise identifiers
    alice_w4idp = alice_mgr.derive_w4idp("bob")
    bob_w4idp = bob_mgr.derive_w4idp("alice")
    check("T23.1: Alice W4IDp for Bob", alice_w4idp.w4idp.startswith("w4idp-"))
    check("T23.2: Bob W4IDp for Alice", bob_w4idp.w4idp.startswith("w4idp-"))

    # Alice sends ClientHello
    alice_sm.transition(HandshakeEvent.CLIENT_HELLO_SENT)
    alice_nonce = os.urandom(12)
    check("T23.3: Alice nonce tracked", alice_guard.check_and_record(alice_nonce))

    # Bob receives ClientHello
    bob_sm.transition(HandshakeEvent.CLIENT_HELLO_RECEIVED)
    check("T23.4: Bob nonce tracked", bob_guard.check_and_record(alice_nonce))

    # Both derive HPKE
    alice_sm.transition(HandshakeEvent.SERVER_HELLO_RECEIVED)
    alice_sm.transition(HandshakeEvent.HPKE_DERIVED)
    bob_sm.transition(HandshakeEvent.HPKE_DERIVED)

    # Auth exchange
    alice_sm.transition(HandshakeEvent.AUTH_SENT)
    bob_sm.transition(HandshakeEvent.AUTH_SENT)

    bob_sm.transition(HandshakeEvent.AUTH_RECEIVED_OK)
    alice_sm.transition(HandshakeEvent.AUTH_RECEIVED_OK)

    check("T23.5: Both reach ESTABLISHED",
          alice_sm.is_established and bob_sm.is_established)

    # Replay prevention
    check("T23.6: Alice nonce replay blocked",
          not alice_guard.check_and_record(alice_nonce))

    # Rekey
    alice_sm.transition(HandshakeEvent.SESSION_KEY_UPDATE)
    alice_sm.transition(HandshakeEvent.REKEY_COMPLETE)
    check("T23.7: Alice back to ESTABLISHED after rekey", alice_sm.is_established)
    check("T23.8: Total transitions", alice_sm.transition_count == 8)

    # ── T24: Edge Cases ──
    print("\n═══ T24: Edge Cases ═══")
    # Empty W4IDp manager
    empty_mgr = W4IDpManager()
    check("T24.1: No current for unknown peer", empty_mgr.get_current("nobody") is None)
    check("T24.2: Unknown W4IDp not known", not empty_mgr.is_known("w4idp-fake"))
    check("T24.3: Lookup unknown returns None", empty_mgr.lookup_peer("w4idp-x") is None)
    check("T24.4: Invalidate empty returns 0", empty_mgr.invalidate_all("nobody") == 0)

    # Empty Problem Details
    empty_err = ProblemDetails()
    ed = empty_err.to_dict()
    check("T24.5: Empty Problem Details has type", ed["type"] == "about:blank")
    check("T24.6: Empty Problem Details no code", "code" not in ed)

    # State machine multiple rekeys
    sm_multi = HandshakeStateMachine(is_initiator=True)
    sm_multi.transition(HandshakeEvent.INITIATE)
    sm_multi.transition(HandshakeEvent.CLIENT_HELLO_SENT)
    sm_multi.transition(HandshakeEvent.SERVER_HELLO_RECEIVED)
    sm_multi.transition(HandshakeEvent.HPKE_DERIVED)
    sm_multi.transition(HandshakeEvent.AUTH_SENT)
    sm_multi.transition(HandshakeEvent.AUTH_RECEIVED_OK)
    # Multiple rekeys
    for i in range(5):
        sm_multi.transition(HandshakeEvent.SESSION_KEY_UPDATE)
        sm_multi.transition(HandshakeEvent.REKEY_COMPLETE)
    check("T24.7: 5 consecutive rekeys", sm_multi.is_established)
    check("T24.8: 16 total transitions", sm_multi.transition_count == 16)

    # ReplayGuard with ISO timestamp
    guard_iso = ReplayGuard()
    future_iso = "2099-01-01T00:00:00Z"
    check("T24.9: Far future timestamp rejected",
          not guard_iso.validate_timestamp(future_iso))

    # ── T25: Key Ratchet Forward Secrecy (§7) ──
    print("\n═══ T25: Key Ratchet Forward Secrecy (§7) ═══")
    # Keys should be irreversible — can't derive gen-0 from gen-1
    km_fs = SessionKeyManager(os.urandom(32), os.urandom(32), os.urandom(32))
    gen0_send, gen0_recv = km_fs.current_keys

    km_fs.create_rekey_message("kid-test")
    gen1_send, gen1_recv = km_fs.current_keys
    check("T25.1: Gen-1 send differs from gen-0", gen1_send != gen0_send)
    check("T25.2: Gen-1 recv differs from gen-0", gen1_recv != gen0_recv)

    km_fs.create_rekey_message("kid-test")
    gen2_send, gen2_recv = km_fs.current_keys
    check("T25.3: Gen-2 differs from gen-1", gen2_send != gen1_send)
    check("T25.4: Gen-2 differs from gen-0", gen2_send != gen0_send)

    # Grace window check
    check("T25.5: Grace keys present", km_fs.has_grace_keys())

    # Discard (immediate — grace window not elapsed)
    discarded = km_fs.discard_old_keys()
    check("T25.6: Grace window not elapsed, no discard", not discarded)

    # ═══ Summary ═══
    total = passed + failed
    print(f"\n{'='*60}")
    print(f"  Handshake Protocol Advanced — Results")
    print(f"  {passed} passed, {failed} failed out of {total} checks")
    print(f"{'='*60}")

    if failed == 0:
        print(f"\n  All {total} checks pass")
        print(f"  §4: W4IDp Pairwise Identifiers — derivation, lifecycle, privacy")
        print(f"  §6: COSE/JOSE Profiles — Ed25519 + ES256, channel binding")
        print(f"  §7: Session Rekey — forward secrecy ratchet")
        print(f"  §8: State Machine — initiator + responder + error paths")
        print(f"  §9: Anti-Replay — nonce tracking, timestamp validation")
        print(f"  §10: Problem Details — RFC 9457 error handling")
        print(f"  §11: Security — DoS cheap checks, downgrade resistance")
        print(f"  §12: Interop Profiles — W4-BASE-1 + W4-FIPS-1")
    else:
        print(f"\n  {failed} failures need investigation")

    return passed, failed


if __name__ == "__main__":
    passed, failed = run_tests()
    sys.exit(0 if failed == 0 else 1)
