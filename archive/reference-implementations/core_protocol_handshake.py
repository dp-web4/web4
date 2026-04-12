#!/usr/bin/env python3
"""
Web4 Core Protocol Handshake — Reference Implementation

HPKE-based handshake protocol per web4-standard/core-spec/core-protocol.md.
Implements W4-BASE-1 cryptographic suite:
  - KEM: X25519
  - Sig: Ed25519
  - AEAD: ChaCha20-Poly1305
  - Hash: SHA-256
  - KDF: HKDF

Protocol flow:
  ClientHello → ServerHello → ClientFinished → ServerFinished → [Application Data]

Also implements:
  - 3 pairing methods: direct, mediated, QR code
  - Encrypted credential exchange
  - Transcript-based MAC verification
  - Session key derivation via HKDF
  - Message encryption/decryption
  - GREASE extension support

@version 1.0.0
@see web4-standard/core-spec/core-protocol.md
@see web4-standard/implementation/tests/handshake_kat.json
"""

import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey, X25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


# ═══════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════

NONCE_SIZE = 32
SUITE_W4_BASE_1 = "W4-BASE-1"
SUITE_W4_FIPS_1 = "W4-FIPS-1"
SUITE_W4_IOT_1 = "W4-IOT-1"
ALL_SUITES = [SUITE_W4_BASE_1, SUITE_W4_FIPS_1, SUITE_W4_IOT_1]

# HKDF info strings
INFO_SEND = b"web4-send-key"
INFO_RECV = b"web4-recv-key"
INFO_SESSION = b"web4-session-id"
INFO_EXPORT = b"web4-exporter"


# ═══════════════════════════════════════════════════════════════
# Crypto Primitives (W4-BASE-1)
# ═══════════════════════════════════════════════════════════════

class CryptoSuite:
    """W4-BASE-1: X25519 + Ed25519 + ChaCha20-Poly1305 + SHA-256 + HKDF."""

    def __init__(self):
        self.suite_id = SUITE_W4_BASE_1

    def generate_kex_keypair(self) -> Tuple[X25519PrivateKey, bytes]:
        """Generate X25519 ephemeral keypair. Returns (private, public_bytes)."""
        private = X25519PrivateKey.generate()
        pub_bytes = private.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        return private, pub_bytes

    def generate_sig_keypair(self) -> Tuple[Ed25519PrivateKey, bytes]:
        """Generate Ed25519 signing keypair. Returns (private, public_bytes)."""
        private = Ed25519PrivateKey.generate()
        pub_bytes = private.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        return private, pub_bytes

    def dh(self, private: X25519PrivateKey, peer_public_bytes: bytes) -> bytes:
        """X25519 Diffie-Hellman key exchange."""
        peer_public = X25519PublicKey.from_public_bytes(peer_public_bytes)
        return private.exchange(peer_public)

    def sign(self, private: Ed25519PrivateKey, data: bytes) -> bytes:
        """Ed25519 signature."""
        return private.sign(data)

    def verify(self, public_bytes: bytes, data: bytes, signature: bytes) -> bool:
        """Ed25519 signature verification."""
        try:
            public = Ed25519PublicKey.from_public_bytes(public_bytes)
            public.verify(signature, data)
            return True
        except Exception:
            return False

    def derive_keys(self, shared_secret: bytes, transcript_hash: bytes,
                    salt: Optional[bytes] = None) -> Dict[str, bytes]:
        """Derive session keys from shared secret using HKDF."""
        if salt is None:
            salt = transcript_hash[:16]

        def _hkdf(info: bytes) -> bytes:
            return HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                info=info,
            ).derive(shared_secret)

        return {
            "k_send": _hkdf(INFO_SEND),
            "k_recv": _hkdf(INFO_RECV),
            "session_id": _hkdf(INFO_SESSION)[:16],
            "exporter_secret": _hkdf(INFO_EXPORT),
        }

    def encrypt(self, key: bytes, plaintext: bytes,
                aad: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """ChaCha20-Poly1305 encrypt. Returns (nonce, ciphertext)."""
        nonce = os.urandom(12)
        cipher = ChaCha20Poly1305(key)
        ciphertext = cipher.encrypt(nonce, plaintext, aad)
        return nonce, ciphertext

    def decrypt(self, key: bytes, nonce: bytes, ciphertext: bytes,
                aad: Optional[bytes] = None) -> bytes:
        """ChaCha20-Poly1305 decrypt."""
        cipher = ChaCha20Poly1305(key)
        return cipher.decrypt(nonce, ciphertext, aad)

    def transcript_hash(self, *messages: bytes) -> bytes:
        """SHA-256 hash of concatenated messages (transcript)."""
        h = hashlib.sha256()
        for msg in messages:
            h.update(msg)
        return h.digest()


# ═══════════════════════════════════════════════════════════════
# Protocol Messages
# ═══════════════════════════════════════════════════════════════

@dataclass
class ClientHello:
    """Client's opening handshake message."""
    supported_suites: List[str]
    client_public_key: bytes    # Ed25519 identity key
    client_kex_public: bytes    # X25519 ephemeral key
    client_w4id: str            # Web4 identifier
    nonce: bytes
    supported_extensions: List[str] = field(default_factory=list)
    grease_extensions: List[str] = field(default_factory=list)

    def serialize(self) -> bytes:
        return json.dumps({
            "type": "ClientHello",
            "suites": self.supported_suites,
            "pub_key": self.client_public_key.hex(),
            "kex_pub": self.client_kex_public.hex(),
            "w4id": self.client_w4id,
            "nonce": self.nonce.hex(),
            "ext": self.supported_extensions,
            "grease": self.grease_extensions,
        }).encode()


@dataclass
class ServerHello:
    """Server's response handshake message."""
    selected_suite: str
    server_public_key: bytes    # Ed25519 identity key
    server_kex_public: bytes    # X25519 ephemeral key
    server_w4id: str
    nonce: bytes
    encrypted_credentials: bytes  # Encrypted server credentials
    credentials_nonce: bytes      # AEAD nonce for credentials
    selected_extensions: List[str] = field(default_factory=list)

    def serialize(self) -> bytes:
        return json.dumps({
            "type": "ServerHello",
            "suite": self.selected_suite,
            "pub_key": self.server_public_key.hex(),
            "kex_pub": self.server_kex_public.hex(),
            "w4id": self.server_w4id,
            "nonce": self.nonce.hex(),
            "enc_creds": self.encrypted_credentials.hex(),
            "creds_nonce": self.credentials_nonce.hex(),
            "ext": self.selected_extensions,
        }).encode()


@dataclass
class ClientFinished:
    """Client's completion message with encrypted credentials."""
    encrypted_credentials: bytes
    credentials_nonce: bytes
    transcript_mac: bytes  # MAC over full transcript

    def serialize(self) -> bytes:
        return json.dumps({
            "type": "ClientFinished",
            "enc_creds": self.encrypted_credentials.hex(),
            "creds_nonce": self.credentials_nonce.hex(),
            "mac": self.transcript_mac.hex(),
        }).encode()


@dataclass
class ServerFinished:
    """Server's completion message confirming session."""
    transcript_mac: bytes
    session_id: bytes

    def serialize(self) -> bytes:
        return json.dumps({
            "type": "ServerFinished",
            "mac": self.transcript_mac.hex(),
            "session_id": self.session_id.hex(),
        }).encode()


# ═══════════════════════════════════════════════════════════════
# Secure Session
# ═══════════════════════════════════════════════════════════════

@dataclass
class SecureSession:
    """Established secure session between two entities."""
    session_id: bytes
    local_w4id: str
    remote_w4id: str
    k_send: bytes
    k_recv: bytes
    exporter_secret: bytes
    suite: str
    established_at: float
    send_counter: int = 0
    recv_counter: int = 0

    def encrypt_message(self, plaintext: bytes, msg_type: str = "request") -> dict:
        """Encrypt an application message."""
        suite = CryptoSuite()
        aad = json.dumps({
            "session": self.session_id.hex(),
            "seq": self.send_counter,
            "type": msg_type,
        }).encode()
        nonce, ciphertext = suite.encrypt(self.k_send, plaintext, aad)
        self.send_counter += 1
        return {
            "session_id": self.session_id.hex(),
            "seq": self.send_counter - 1,
            "type": msg_type,
            "nonce": nonce.hex(),
            "ciphertext": ciphertext.hex(),
        }

    def decrypt_message(self, msg: dict) -> bytes:
        """Decrypt an application message."""
        suite = CryptoSuite()
        aad = json.dumps({
            "session": msg["session_id"],
            "seq": msg["seq"],
            "type": msg["type"],
        }).encode()
        plaintext = suite.decrypt(
            self.k_recv,
            bytes.fromhex(msg["nonce"]),
            bytes.fromhex(msg["ciphertext"]),
            aad,
        )
        self.recv_counter += 1
        return plaintext


# ═══════════════════════════════════════════════════════════════
# Entity — Protocol Participant
# ═══════════════════════════════════════════════════════════════

class W4Entity:
    """A Web4 protocol participant with identity and ephemeral keys."""

    def __init__(self, w4id: str, supported_suites: Optional[List[str]] = None,
                 extensions: Optional[List[str]] = None):
        self.w4id = w4id
        self.supported_suites = supported_suites or [SUITE_W4_BASE_1]
        self.extensions = extensions or []
        self.suite = CryptoSuite()

        # Identity keys (long-lived)
        self._sig_private, self.sig_public = self.suite.generate_sig_keypair()

        # Credentials (e.g., LCT, attestations)
        self.credentials: Dict[str, Any] = {
            "w4id": w4id,
            "entity_type": "ai",
            "capabilities": ["witness:attest"],
        }

        # Active sessions
        self.sessions: Dict[bytes, SecureSession] = {}

    def _new_ephemeral(self) -> Tuple[X25519PrivateKey, bytes]:
        """Generate fresh ephemeral KEM keypair."""
        return self.suite.generate_kex_keypair()

    def create_client_hello(self) -> Tuple[ClientHello, X25519PrivateKey]:
        """Create ClientHello and return ephemeral private for DH."""
        kex_private, kex_public = self._new_ephemeral()
        nonce = os.urandom(NONCE_SIZE)

        # GREASE: random unknown extensions for forward compat
        grease = [f"w4_ext_{os.urandom(4).hex()}@0"]

        hello = ClientHello(
            supported_suites=self.supported_suites,
            client_public_key=self.sig_public,
            client_kex_public=kex_public,
            client_w4id=self.w4id,
            nonce=nonce,
            supported_extensions=self.extensions,
            grease_extensions=grease,
        )
        return hello, kex_private

    def process_client_hello(self, ch: ClientHello) -> Tuple[ServerHello, X25519PrivateKey, bytes]:
        """
        Server processes ClientHello, returns ServerHello.
        Returns (server_hello, kex_private, shared_secret).
        """
        # Suite negotiation: pick first mutual suite
        selected = None
        for s in ch.supported_suites:
            if s in self.supported_suites:
                selected = s
                break
        if selected is None:
            raise HandshakeError("No common cryptographic suite")

        # Extension negotiation: ack supported ones, ignore GREASE
        acked_ext = [e for e in ch.supported_extensions if e in self.extensions]

        # Generate ephemeral
        kex_private, kex_public = self._new_ephemeral()
        nonce = os.urandom(NONCE_SIZE)

        # DH shared secret
        shared_secret = self.suite.dh(kex_private, ch.client_kex_public)

        # Derive early handshake key from ClientHello transcript only
        # (both sides can compute this independently)
        early_transcript = self.suite.transcript_hash(ch.serialize())
        early_keys = self.suite.derive_keys(shared_secret, early_transcript,
                                            salt=b"web4-early-handshake")

        # Encrypt server credentials with early handshake key
        cred_bytes = json.dumps(self.credentials).encode()
        cred_nonce, enc_creds = self.suite.encrypt(early_keys["k_send"], cred_bytes)

        hello = ServerHello(
            selected_suite=selected,
            server_public_key=self.sig_public,
            server_kex_public=kex_public,
            server_w4id=self.w4id,
            nonce=nonce,
            encrypted_credentials=enc_creds,
            credentials_nonce=cred_nonce,
            selected_extensions=acked_ext,
        )
        return hello, kex_private, shared_secret

    def process_server_hello(self, sh: ServerHello, ch: ClientHello,
                             kex_private: X25519PrivateKey) -> Tuple[ClientFinished, bytes]:
        """
        Client processes ServerHello, returns ClientFinished.
        Returns (client_finished, shared_secret).
        """
        # DH shared secret
        shared_secret = self.suite.dh(kex_private, sh.server_kex_public)

        # Derive early handshake key (same as server — uses ClientHello only)
        early_transcript = self.suite.transcript_hash(ch.serialize())
        early_keys = self.suite.derive_keys(shared_secret, early_transcript,
                                            salt=b"web4-early-handshake")

        # Decrypt server credentials with early key
        server_creds = self.suite.decrypt(
            early_keys["k_send"], sh.credentials_nonce, sh.encrypted_credentials
        )
        self._peer_credentials = json.loads(server_creds)

        # Derive session keys from full transcript (CH + SH)
        full_hs_transcript = self.suite.transcript_hash(ch.serialize(), sh.serialize())
        session_keys = self.suite.derive_keys(shared_secret, full_hs_transcript)

        # Encrypt client credentials with session key
        cred_bytes = json.dumps(self.credentials).encode()
        cred_nonce, enc_creds = self.suite.encrypt(session_keys["k_send"], cred_bytes)

        # MAC over full transcript including credentials
        mac_transcript = self.suite.transcript_hash(
            ch.serialize(), sh.serialize(), cred_bytes
        )
        mac = self.suite.sign(self._sig_private, mac_transcript)

        finished = ClientFinished(
            encrypted_credentials=enc_creds,
            credentials_nonce=cred_nonce,
            transcript_mac=mac,
        )
        return finished, shared_secret

    def process_client_finished(self, cf: ClientFinished, ch: ClientHello,
                                sh: ServerHello, shared_secret: bytes) -> ServerFinished:
        """
        Server processes ClientFinished, returns ServerFinished + establishes session.
        """
        # Derive session keys from full transcript (same as client)
        full_hs_transcript = self.suite.transcript_hash(ch.serialize(), sh.serialize())
        session_keys = self.suite.derive_keys(shared_secret, full_hs_transcript)

        # Decrypt client credentials
        client_creds = self.suite.decrypt(
            session_keys["k_send"], cf.credentials_nonce, cf.encrypted_credentials
        )
        self._peer_credentials = json.loads(client_creds)

        # Verify client MAC
        mac_transcript = self.suite.transcript_hash(
            ch.serialize(), sh.serialize(), client_creds
        )
        if not self.suite.verify(ch.client_public_key, mac_transcript, cf.transcript_mac):
            raise HandshakeError("Client transcript MAC verification failed")

        # Server MAC (signs same transcript)
        server_mac = self.suite.sign(self._sig_private, mac_transcript)

        # Establish session — server SWAPS keys so client.k_send = server.k_recv
        session = SecureSession(
            session_id=session_keys["session_id"],
            local_w4id=self.w4id,
            remote_w4id=ch.client_w4id,
            k_send=session_keys["k_recv"],
            k_recv=session_keys["k_send"],
            exporter_secret=session_keys["exporter_secret"],
            suite=sh.selected_suite,
            established_at=time.time(),
        )
        self.sessions[session.session_id] = session

        return ServerFinished(
            transcript_mac=server_mac,
            session_id=session_keys["session_id"],
        )

    def process_server_finished(self, sf: ServerFinished, ch: ClientHello,
                                sh: ServerHello, shared_secret: bytes) -> SecureSession:
        """
        Client processes ServerFinished + establishes session.
        """
        # Derive session keys (same derivation as server)
        full_hs_transcript = self.suite.transcript_hash(ch.serialize(), sh.serialize())
        session_keys = self.suite.derive_keys(shared_secret, full_hs_transcript)

        # Verify server MAC
        cred_bytes = json.dumps(self.credentials).encode()
        mac_transcript = self.suite.transcript_hash(
            ch.serialize(), sh.serialize(), cred_bytes
        )
        if not self.suite.verify(sh.server_public_key, mac_transcript, sf.transcript_mac):
            raise HandshakeError("Server transcript MAC verification failed")

        # Establish session — client uses SAME keys as server
        # Both sides derive identically, so k_send is the same on both sides.
        # For application data, both encrypt with k_send, decrypt with k_recv.
        session = SecureSession(
            session_id=sf.session_id,
            local_w4id=self.w4id,
            remote_w4id=sh.server_w4id,
            k_send=session_keys["k_send"],
            k_recv=session_keys["k_recv"],
            exporter_secret=session_keys["exporter_secret"],
            suite=sh.selected_suite,
            established_at=time.time(),
        )
        self.sessions[session.session_id] = session
        return session


class HandshakeError(Exception):
    """Protocol handshake failure."""
    pass


# ═══════════════════════════════════════════════════════════════
# Pairing Methods
# ═══════════════════════════════════════════════════════════════

class PairingMethod(Enum):
    DIRECT = "direct"
    MEDIATED = "mediated"
    QR_CODE = "qr_code"


@dataclass
class QRPayload:
    """QR code pairing payload."""
    w4id: str
    public_key: str  # hex
    endpoint: str
    nonce: str  # hex
    suite: str = SUITE_W4_BASE_1

    def to_json(self) -> str:
        return json.dumps({
            "w4id": self.w4id,
            "pub": self.public_key,
            "ep": self.endpoint,
            "n": self.nonce,
            "s": self.suite,
        })

    @classmethod
    def from_json(cls, s: str) -> "QRPayload":
        d = json.loads(s)
        return cls(
            w4id=d["w4id"], public_key=d["pub"],
            endpoint=d["ep"], nonce=d["n"], suite=d.get("s", SUITE_W4_BASE_1),
        )


@dataclass
class MediatedPairing:
    """Mediated pairing through a trusted third party."""
    mediator_w4id: str
    initiator_w4id: str
    responder_w4id: str
    mediator_sig: Optional[bytes] = None
    pairing_token: Optional[str] = None

    def create_token(self, mediator_key: Ed25519PrivateKey) -> str:
        """Mediator creates a signed pairing token."""
        payload = json.dumps({
            "mediator": self.mediator_w4id,
            "initiator": self.initiator_w4id,
            "responder": self.responder_w4id,
            "ts": time.time(),
        }).encode()
        sig = mediator_key.sign(payload)
        self.mediator_sig = sig
        self.pairing_token = json.dumps({
            "payload": payload.hex(),
            "sig": sig.hex(),
        })
        return self.pairing_token

    def verify_token(self, token: str, mediator_public: bytes) -> bool:
        """Verify a mediator-signed pairing token."""
        d = json.loads(token)
        suite = CryptoSuite()
        return suite.verify(
            mediator_public,
            bytes.fromhex(d["payload"]),
            bytes.fromhex(d["sig"]),
        )


# ═══════════════════════════════════════════════════════════════
# Full Handshake Orchestrator
# ═══════════════════════════════════════════════════════════════

def direct_handshake(client: W4Entity, server: W4Entity) -> Tuple[SecureSession, SecureSession]:
    """
    Execute full 4-message direct handshake between client and server.
    Returns (client_session, server_session).
    """
    # 1. ClientHello
    ch, client_kex_private = client.create_client_hello()

    # 2. ServerHello
    sh, server_kex_private, server_shared = server.process_client_hello(ch)

    # 3. ClientFinished
    cf, client_shared = client.process_server_hello(sh, ch, client_kex_private)

    # 4. ServerFinished
    sf = server.process_client_finished(cf, ch, sh, server_shared)

    # 5. Client processes ServerFinished
    client_session = client.process_server_finished(sf, ch, sh, client_shared)
    server_session = server.sessions[sf.session_id]

    return client_session, server_session


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

    # ── T1: Crypto Suite Primitives ──
    print("\n═══ T1: Crypto Suite Primitives ═══")
    suite = CryptoSuite()

    # KEM keypair
    kex_priv, kex_pub = suite.generate_kex_keypair()
    check("T1: X25519 keypair generated", len(kex_pub) == 32)

    # Sig keypair
    sig_priv, sig_pub = suite.generate_sig_keypair()
    check("T1: Ed25519 keypair generated", len(sig_pub) == 32)

    # DH exchange
    kex_priv2, kex_pub2 = suite.generate_kex_keypair()
    shared1 = suite.dh(kex_priv, kex_pub2)
    shared2 = suite.dh(kex_priv2, kex_pub)
    check("T1: DH shared secrets match", shared1 == shared2, f"len={len(shared1)}")

    # Sign / verify
    msg = b"web4 test message"
    sig = suite.sign(sig_priv, msg)
    check("T1: Ed25519 signature", len(sig) == 64)
    check("T1: Signature verifies", suite.verify(sig_pub, msg, sig))
    check("T1: Bad message fails", not suite.verify(sig_pub, b"wrong", sig))

    # Encrypt / decrypt
    key = os.urandom(32)
    nonce, ct = suite.encrypt(key, b"hello web4", b"aad")
    pt = suite.decrypt(key, nonce, ct, b"aad")
    check("T1: ChaCha20-Poly1305 roundtrip", pt == b"hello web4")

    # Bad AAD fails
    try:
        suite.decrypt(key, nonce, ct, b"bad-aad")
        check("T1: Bad AAD fails", False, "should have raised")
    except Exception:
        check("T1: Bad AAD fails", True)

    # HKDF key derivation
    keys = suite.derive_keys(shared1, suite.transcript_hash(msg))
    check("T1: HKDF derives 4 keys", len(keys) == 4)
    check("T1: k_send is 32 bytes", len(keys["k_send"]) == 32)
    check("T1: k_recv is 32 bytes", len(keys["k_recv"]) == 32)
    check("T1: session_id is 16 bytes", len(keys["session_id"]) == 16)
    check("T1: k_send != k_recv", keys["k_send"] != keys["k_recv"])

    # ── T2: Full Direct Handshake ──
    print("\n═══ T2: Full Direct Handshake ═══")
    client = W4Entity("w4id:key:alice-001")
    server = W4Entity("w4id:key:bob-001")

    client_sess, server_sess = direct_handshake(client, server)
    check("T2: Handshake completes", client_sess is not None and server_sess is not None)
    check("T2: Same session ID", client_sess.session_id == server_sess.session_id)
    check("T2: Client knows server W4ID", client_sess.remote_w4id == "w4id:key:bob-001")
    check("T2: Server knows client W4ID", server_sess.remote_w4id == "w4id:key:alice-001")
    check("T2: Suite agreed", client_sess.suite == SUITE_W4_BASE_1)
    check("T2: Client has session", len(client.sessions) == 1)
    check("T2: Server has session", len(server.sessions) == 1)

    # ── T3: Encrypted Application Messages ──
    print("\n═══ T3: Encrypted Application Messages ═══")
    # Client sends to server
    msg1 = client_sess.encrypt_message(b'{"action": "read", "resource": "/data"}', "request")
    check("T3: Client encrypts message", "ciphertext" in msg1)
    check("T3: Message has session_id", msg1["session_id"] == client_sess.session_id.hex())
    check("T3: Message has sequence", msg1["seq"] == 0)

    # Server decrypts — keys are symmetric in this impl, need to handle
    # In real protocol, client.k_send = server.k_recv and vice versa
    # Our implementation uses same key derivation so we need to verify
    # the data flow works correctly
    pt1 = server_sess.decrypt_message(msg1)
    check("T3: Server decrypts message", b"read" in pt1)

    # Server responds
    msg2 = server_sess.encrypt_message(b'{"status": "ok", "data": [1,2,3]}', "response")
    pt2 = client_sess.decrypt_message(msg2)
    check("T3: Client decrypts response", b"ok" in pt2)

    # Multiple messages (sequence tracking)
    for i in range(5):
        m = client_sess.encrypt_message(f"msg-{i}".encode(), "event")
        p = server_sess.decrypt_message(m)
        assert p == f"msg-{i}".encode()
    check("T3: 5 sequential messages", client_sess.send_counter == 6)
    check("T3: Server recv counter", server_sess.recv_counter == 6)

    # ── T4: Suite Negotiation ──
    print("\n═══ T4: Suite Negotiation ═══")
    # Both support W4-BASE-1
    c2 = W4Entity("w4id:key:carol", supported_suites=[SUITE_W4_BASE_1, SUITE_W4_FIPS_1])
    s2 = W4Entity("w4id:key:dave", supported_suites=[SUITE_W4_BASE_1])
    cs2, ss2 = direct_handshake(c2, s2)
    check("T4: Negotiated W4-BASE-1", cs2.suite == SUITE_W4_BASE_1)

    # No common suite
    c3 = W4Entity("w4id:key:eve", supported_suites=["W4-FUTURE-1"])
    s3 = W4Entity("w4id:key:frank", supported_suites=[SUITE_W4_BASE_1])
    try:
        direct_handshake(c3, s3)
        check("T4: No common suite rejected", False)
    except HandshakeError as e:
        check("T4: No common suite rejected", "No common" in str(e))

    # ── T5: Extension Negotiation ──
    print("\n═══ T5: Extension Negotiation ═══")
    c4 = W4Entity("w4id:key:ext-client", extensions=["w4_ext_sdjwt_vp@1", "w4_ext_custom@2"])
    s4 = W4Entity("w4id:key:ext-server", extensions=["w4_ext_sdjwt_vp@1"])

    ch4, _ = c4.create_client_hello()
    check("T5: ClientHello has extensions", len(ch4.supported_extensions) == 2)
    check("T5: ClientHello has GREASE", len(ch4.grease_extensions) > 0)

    sh4, _, _ = s4.process_client_hello(ch4)
    check("T5: ServerHello acks supported extension", "w4_ext_sdjwt_vp@1" in sh4.selected_extensions)
    check("T5: ServerHello drops unsupported", "w4_ext_custom@2" not in sh4.selected_extensions)

    # ── T6: QR Code Pairing ──
    print("\n═══ T6: QR Code Pairing ═══")
    qr = QRPayload(
        w4id="w4id:key:qr-entity",
        public_key=suite.generate_sig_keypair()[1].hex(),
        endpoint="https://example.com:8443/w4",
        nonce=os.urandom(16).hex(),
    )
    qr_json = qr.to_json()
    check("T6: QR payload serializes", len(qr_json) > 0)

    qr_back = QRPayload.from_json(qr_json)
    check("T6: QR payload deserializes", qr_back.w4id == "w4id:key:qr-entity")
    check("T6: QR preserves endpoint", qr_back.endpoint == "https://example.com:8443/w4")
    check("T6: QR preserves suite", qr_back.suite == SUITE_W4_BASE_1)

    # ── T7: Mediated Pairing ──
    print("\n═══ T7: Mediated Pairing ═══")
    mediator = W4Entity("w4id:key:mediator")
    mp = MediatedPairing(
        mediator_w4id="w4id:key:mediator",
        initiator_w4id="w4id:key:alice-001",
        responder_w4id="w4id:key:bob-001",
    )
    token = mp.create_token(mediator._sig_private)
    check("T7: Mediator creates token", len(token) > 0)
    check("T7: Token verifies", mp.verify_token(token, mediator.sig_public))

    # Tampered token fails
    d = json.loads(token)
    d["sig"] = "00" * 64
    check("T7: Tampered token fails", not mp.verify_token(json.dumps(d), mediator.sig_public))

    # ── T8: Credential Exchange ──
    print("\n═══ T8: Credential Exchange ═══")
    c5 = W4Entity("w4id:key:cred-client")
    c5.credentials = {"w4id": "w4id:key:cred-client", "entity_type": "human",
                       "capabilities": ["governance:vote", "witness:attest"]}
    s5 = W4Entity("w4id:key:cred-server")
    s5.credentials = {"w4id": "w4id:key:cred-server", "entity_type": "service",
                       "capabilities": ["api:route"]}

    cs5, ss5 = direct_handshake(c5, s5)
    check("T8: Client received server credentials", hasattr(c5, "_peer_credentials"))
    check("T8: Server received client credentials", hasattr(s5, "_peer_credentials"))
    check("T8: Client sees server type",
          c5._peer_credentials.get("entity_type") == "service")
    check("T8: Server sees client capabilities",
          "governance:vote" in s5._peer_credentials.get("capabilities", []))

    # ── T9: Transcript Integrity ──
    print("\n═══ T9: Transcript Integrity ═══")
    t1 = suite.transcript_hash(b"msg1", b"msg2")
    t2 = suite.transcript_hash(b"msg1", b"msg2")
    check("T9: Transcript hash deterministic", t1 == t2)

    t3 = suite.transcript_hash(b"msg1", b"msg3")
    check("T9: Different messages → different hash", t1 != t3)

    t4 = suite.transcript_hash(b"msg1")
    check("T9: Subset → different hash", t1 != t4)

    # ── T10: Session Isolation ──
    print("\n═══ T10: Session Isolation ═══")
    c6 = W4Entity("w4id:key:iso-client")
    s6a = W4Entity("w4id:key:server-a")
    s6b = W4Entity("w4id:key:server-b")

    cs_a, ss_a = direct_handshake(c6, s6a)
    cs_b, ss_b = direct_handshake(c6, s6b)
    check("T10: Client has 2 sessions", len(c6.sessions) == 2)
    check("T10: Different session IDs", cs_a.session_id != cs_b.session_id)
    check("T10: Different send keys", cs_a.k_send != cs_b.k_send)

    # Messages don't cross sessions
    msg_a = cs_a.encrypt_message(b"for server-a", "request")
    pt_a = ss_a.decrypt_message(msg_a)
    check("T10: Correct session decrypts", pt_a == b"for server-a")

    try:
        ss_b.decrypt_message(msg_a)
        check("T10: Wrong session fails decrypt", False, "should have raised")
    except Exception:
        check("T10: Wrong session fails decrypt", True)

    # ── T11: Key Material Security ──
    print("\n═══ T11: Key Material Security ═══")
    # Each handshake produces unique keys
    c7 = W4Entity("w4id:key:unique-test")
    s7 = W4Entity("w4id:key:unique-server")

    cs7a, ss7a = direct_handshake(c7, s7)
    cs7b, ss7b = direct_handshake(c7, s7)
    check("T11: Repeated handshake → different session IDs",
          cs7a.session_id != cs7b.session_id)
    check("T11: Repeated handshake → different send keys",
          cs7a.k_send != cs7b.k_send)
    check("T11: Repeated handshake → different recv keys",
          cs7a.k_recv != cs7b.k_recv)

    # ── T12: Message Types ──
    print("\n═══ T12: Message Types ═══")
    c8 = W4Entity("w4id:key:msg-client")
    s8 = W4Entity("w4id:key:msg-server")
    cs8, ss8 = direct_handshake(c8, s8)

    for msg_type in ["request", "response", "event", "credential"]:
        enc = cs8.encrypt_message(f"type-{msg_type}".encode(), msg_type)
        check(f"T12: Message type '{msg_type}' encrypts", enc["type"] == msg_type)
        dec = ss8.decrypt_message(enc)
        check(f"T12: Message type '{msg_type}' decrypts", dec == f"type-{msg_type}".encode())

    # ── T13: Large Messages ──
    print("\n═══ T13: Large Messages ═══")
    c9 = W4Entity("w4id:key:large-client")
    s9 = W4Entity("w4id:key:large-server")
    cs9, ss9 = direct_handshake(c9, s9)

    large_msg = os.urandom(64 * 1024)  # 64KB
    enc_large = cs9.encrypt_message(large_msg, "request")
    dec_large = ss9.decrypt_message(enc_large)
    check("T13: 64KB message roundtrip", dec_large == large_msg)

    huge_msg = b"x" * (1024 * 1024)  # 1MB
    enc_huge = cs9.encrypt_message(huge_msg, "request")
    dec_huge = ss9.decrypt_message(enc_huge)
    check("T13: 1MB message roundtrip", dec_huge == huge_msg)

    # ── T14: Handshake Serialization ──
    print("\n═══ T14: Handshake Serialization ═══")
    c10 = W4Entity("w4id:key:serial-client")
    ch10, _ = c10.create_client_hello()
    serialized = ch10.serialize()
    check("T14: ClientHello serializes to JSON", b"ClientHello" in serialized)
    parsed = json.loads(serialized)
    check("T14: Has nonce field", "nonce" in parsed)
    check("T14: Has suites field", "suites" in parsed)
    check("T14: Has GREASE", len(parsed["grease"]) > 0)

    # ═══ Summary ═══
    total = passed + failed
    print(f"\n{'='*60}")
    print(f"  Core Protocol Handshake — Track M Results")
    print(f"  {passed} passed, {failed} failed out of {total} checks")
    print(f"{'='*60}")

    if failed == 0:
        print(f"\n  All {total} checks pass — HPKE handshake fully operational")
        print(f"  W4-BASE-1: X25519 + Ed25519 + ChaCha20-Poly1305 + SHA-256 + HKDF")
        print(f"  3 pairing methods: direct, mediated, QR code")
    else:
        print(f"\n  {failed} failures need investigation")

    return passed, failed


if __name__ == "__main__":
    passed, failed = run_tests()
    sys.exit(0 if failed == 0 else 1)
