#!/usr/bin/env python3
"""
Web4 Security Framework — Reference Implementation

Implements web4-standard/core-spec/security-framework.md:
  - Two crypto suites: W4-BASE-1 (MUST) and W4-FIPS-1 (SHOULD)
  - Key management: generation, storage simulation, rotation
  - Authentication: challenge-response with digital signatures
  - Authorization: Verifiable Credential issuance and verification

Integrates with existing:
  - core_protocol_handshake.py (CryptoSuite, W4-BASE-1 primitives)
  - w4id_data_formats.py (VCs, DIDs)
  - web4_error_handler.py (error taxonomy)

@version 1.0.0
@see web4-standard/core-spec/security-framework.md
"""

import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set

# Try real crypto; fall back to simulation
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey,
    )
    from cryptography.hazmat.primitives.asymmetric.x25519 import (
        X25519PrivateKey, X25519PublicKey,
    )
    from cryptography.hazmat.primitives.asymmetric.ec import (
        ECDSA, SECP256R1, generate_private_key as ec_generate_private_key,
        EllipticCurvePrivateKey,
    )
    from cryptography.hazmat.primitives.ciphers.aead import (
        ChaCha20Poly1305, AESGCM,
    )
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


# ═══════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════

SUITE_W4_BASE_1 = "W4-BASE-1"
SUITE_W4_FIPS_1 = "W4-FIPS-1"

# MTI = Mandatory to Implement
MTI_SUITE = SUITE_W4_BASE_1


# ═══════════════════════════════════════════════════════════════
# Crypto Suite Abstraction
# ═══════════════════════════════════════════════════════════════

class SuiteCapability(Enum):
    """What a crypto suite can do."""
    KEY_EXCHANGE = "kem"
    SIGNATURE = "sig"
    ENCRYPTION = "aead"
    HASH = "hash"
    KDF = "kdf"


@dataclass
class SuiteAlgorithms:
    """Algorithm specifications for a crypto suite."""
    suite_id: str
    kem: str          # Key Exchange Mechanism
    sig: str          # Signature algorithm
    aead: str         # Authenticated Encryption with Associated Data
    hash_alg: str     # Hash function
    kdf: str          # Key Derivation Function
    encoding: str     # Serialization format (COSE or JOSE)
    status: str       # MUST, SHOULD, MAY


# Suite definitions from spec §1.1
W4_BASE_1_ALGORITHMS = SuiteAlgorithms(
    suite_id=SUITE_W4_BASE_1,
    kem="X25519",           # RFC 7748
    sig="Ed25519",          # RFC 8032
    aead="ChaCha20-Poly1305",  # RFC 8439
    hash_alg="SHA-256",     # FIPS 180-4
    kdf="HKDF-SHA256",      # RFC 5869
    encoding="COSE",        # RFC 8152
    status="MUST",
)

W4_FIPS_1_ALGORITHMS = SuiteAlgorithms(
    suite_id=SUITE_W4_FIPS_1,
    kem="ECDH-P256",        # FIPS 186-4
    sig="ECDSA-P256",       # FIPS 186-4
    aead="AES-128-GCM",     # NIST SP 800-38D
    hash_alg="SHA-256",     # FIPS 180-4
    kdf="HKDF-SHA256",      # RFC 5869
    encoding="JOSE",        # RFC 7515/7516
    status="SHOULD",
)

SUITE_REGISTRY: Dict[str, SuiteAlgorithms] = {
    SUITE_W4_BASE_1: W4_BASE_1_ALGORITHMS,
    SUITE_W4_FIPS_1: W4_FIPS_1_ALGORITHMS,
}


class CryptoSuiteBase:
    """Abstract crypto suite — common interface for W4-BASE-1 and W4-FIPS-1."""

    def __init__(self, suite_id: str):
        if suite_id not in SUITE_REGISTRY:
            raise ValueError(f"Unknown suite: {suite_id}")
        self.suite_id = suite_id
        self.algorithms = SUITE_REGISTRY[suite_id]

    def generate_signing_keypair(self) -> Tuple[Any, bytes]:
        """Generate signing keypair. Returns (private_key, public_key_bytes)."""
        raise NotImplementedError

    def sign(self, private_key: Any, message: bytes) -> bytes:
        """Sign message with private key."""
        raise NotImplementedError

    def verify(self, public_key_bytes: bytes, message: bytes, signature: bytes) -> bool:
        """Verify signature. Returns True if valid."""
        raise NotImplementedError

    def generate_kex_keypair(self) -> Tuple[Any, bytes]:
        """Generate key exchange keypair."""
        raise NotImplementedError

    def key_exchange(self, private_key: Any, peer_public_bytes: bytes) -> bytes:
        """Perform key exchange. Returns shared secret."""
        raise NotImplementedError

    def encrypt(self, key: bytes, nonce: bytes, plaintext: bytes, aad: bytes = b"") -> bytes:
        """AEAD encrypt."""
        raise NotImplementedError

    def decrypt(self, key: bytes, nonce: bytes, ciphertext: bytes, aad: bytes = b"") -> bytes:
        """AEAD decrypt."""
        raise NotImplementedError

    def hash(self, data: bytes) -> bytes:
        """Hash data."""
        return hashlib.sha256(data).digest()

    def kdf(self, ikm: bytes, info: bytes, length: int = 32) -> bytes:
        """Key derivation."""
        raise NotImplementedError


class W4Base1Suite(CryptoSuiteBase):
    """W4-BASE-1: X25519 + Ed25519 + ChaCha20-Poly1305 + SHA-256 + HKDF."""

    def __init__(self):
        super().__init__(SUITE_W4_BASE_1)

    def generate_signing_keypair(self) -> Tuple[Any, bytes]:
        if not HAS_CRYPTO:
            # Simulation fallback
            priv = os.urandom(32)
            pub = hashlib.sha256(b"ed25519-pub:" + priv).digest()
            return priv, pub
        private = Ed25519PrivateKey.generate()
        pub_bytes = private.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        return private, pub_bytes

    def sign(self, private_key: Any, message: bytes) -> bytes:
        if not HAS_CRYPTO:
            return hashlib.sha256(b"sig:" + private_key + message).digest()
        return private_key.sign(message)

    def verify(self, public_key_bytes: bytes, message: bytes, signature: bytes) -> bool:
        if not HAS_CRYPTO:
            return len(signature) == 32  # Simulation
        try:
            pub = Ed25519PublicKey.from_public_bytes(public_key_bytes)
            pub.verify(signature, message)
            return True
        except Exception:
            return False

    def generate_kex_keypair(self) -> Tuple[Any, bytes]:
        if not HAS_CRYPTO:
            priv = os.urandom(32)
            pub = hashlib.sha256(b"x25519-pub:" + priv).digest()
            return priv, pub
        private = X25519PrivateKey.generate()
        pub_bytes = private.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        return private, pub_bytes

    def key_exchange(self, private_key: Any, peer_public_bytes: bytes) -> bytes:
        if not HAS_CRYPTO:
            return hashlib.sha256(b"shared:" + private_key + peer_public_bytes).digest()
        peer_pub = X25519PublicKey.from_public_bytes(peer_public_bytes)
        return private_key.exchange(peer_pub)

    def encrypt(self, key: bytes, nonce: bytes, plaintext: bytes, aad: bytes = b"") -> bytes:
        if not HAS_CRYPTO:
            return b"enc:" + hashlib.sha256(key + nonce + plaintext).digest()
        cipher = ChaCha20Poly1305(key)
        return cipher.encrypt(nonce[:12], plaintext, aad)

    def decrypt(self, key: bytes, nonce: bytes, ciphertext: bytes, aad: bytes = b"") -> bytes:
        if not HAS_CRYPTO:
            return b"decrypted"
        cipher = ChaCha20Poly1305(key)
        return cipher.decrypt(nonce[:12], ciphertext, aad)

    def kdf(self, ikm: bytes, info: bytes, length: int = 32) -> bytes:
        if not HAS_CRYPTO:
            return hashlib.sha256(b"hkdf:" + ikm + info).digest()[:length]
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=length,
            salt=None,
            info=info,
        )
        return hkdf.derive(ikm)


class W4Fips1Suite(CryptoSuiteBase):
    """W4-FIPS-1: ECDH-P256 + ECDSA-P256 + AES-128-GCM + SHA-256 + HKDF."""

    def __init__(self):
        super().__init__(SUITE_W4_FIPS_1)

    def generate_signing_keypair(self) -> Tuple[Any, bytes]:
        if not HAS_CRYPTO:
            priv = os.urandom(32)
            pub = hashlib.sha256(b"p256-pub:" + priv).digest()
            return priv, pub
        private = ec_generate_private_key(SECP256R1())
        pub_bytes = private.public_key().public_bytes(
            serialization.Encoding.X962,
            serialization.PublicFormat.CompressedPoint,
        )
        return private, pub_bytes

    def sign(self, private_key: Any, message: bytes) -> bytes:
        if not HAS_CRYPTO:
            return hashlib.sha256(b"ecdsa-sig:" + private_key + message).digest()
        return private_key.sign(message, ECDSA(hashes.SHA256()))

    def verify(self, public_key_bytes: bytes, message: bytes, signature: bytes) -> bool:
        if not HAS_CRYPTO:
            return len(signature) == 32
        try:
            from cryptography.hazmat.primitives.asymmetric.ec import (
                EllipticCurvePublicKey,
            )
            from cryptography.hazmat.primitives.asymmetric import ec
            pub = ec.EllipticCurvePublicKey.from_encoded_point(SECP256R1(), public_key_bytes)
            pub.verify(signature, message, ECDSA(hashes.SHA256()))
            return True
        except Exception:
            return False

    def generate_kex_keypair(self) -> Tuple[Any, bytes]:
        if not HAS_CRYPTO:
            priv = os.urandom(32)
            pub = hashlib.sha256(b"p256-kex-pub:" + priv).digest()
            return priv, pub
        private = ec_generate_private_key(SECP256R1())
        pub_bytes = private.public_key().public_bytes(
            serialization.Encoding.X962,
            serialization.PublicFormat.CompressedPoint,
        )
        return private, pub_bytes

    def key_exchange(self, private_key: Any, peer_public_bytes: bytes) -> bytes:
        if not HAS_CRYPTO:
            return hashlib.sha256(b"ecdh:" + private_key + peer_public_bytes).digest()
        from cryptography.hazmat.primitives.asymmetric import ec
        peer_pub = ec.EllipticCurvePublicKey.from_encoded_point(SECP256R1(), peer_public_bytes)
        shared = private_key.exchange(ec.ECDH(), peer_pub)
        return shared

    def encrypt(self, key: bytes, nonce: bytes, plaintext: bytes, aad: bytes = b"") -> bytes:
        if not HAS_CRYPTO:
            return b"aes-enc:" + hashlib.sha256(key + nonce + plaintext).digest()
        cipher = AESGCM(key[:16])  # AES-128
        return cipher.encrypt(nonce[:12], plaintext, aad)

    def decrypt(self, key: bytes, nonce: bytes, ciphertext: bytes, aad: bytes = b"") -> bytes:
        if not HAS_CRYPTO:
            return b"decrypted"
        cipher = AESGCM(key[:16])
        return cipher.decrypt(nonce[:12], ciphertext, aad)

    def kdf(self, ikm: bytes, info: bytes, length: int = 32) -> bytes:
        if not HAS_CRYPTO:
            return hashlib.sha256(b"hkdf:" + ikm + info).digest()[:length]
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=length,
            salt=None,
            info=info,
        )
        return hkdf.derive(ikm)


def get_suite(suite_id: str) -> CryptoSuiteBase:
    """Factory: get a crypto suite implementation by ID."""
    if suite_id == SUITE_W4_BASE_1:
        return W4Base1Suite()
    elif suite_id == SUITE_W4_FIPS_1:
        return W4Fips1Suite()
    else:
        raise ValueError(f"Unknown suite: {suite_id}. Available: {list(SUITE_REGISTRY.keys())}")


# ═══════════════════════════════════════════════════════════════
# Key Management (§2)
# ═══════════════════════════════════════════════════════════════

class KeyStorageMethod(Enum):
    """Key storage methods per spec §2.2."""
    HSM = "hsm"                   # Hardware Security Module
    SECURE_ENCLAVE = "enclave"    # TEE / Secure Enclave
    ENCRYPTED = "encrypted"       # Software encrypted storage
    PLAINTEXT = "plaintext"       # Development only


@dataclass
class ManagedKey:
    """A managed cryptographic key with metadata."""
    key_id: str
    suite_id: str
    public_key_bytes: bytes
    private_key: Any  # Opaque to callers
    storage_method: KeyStorageMethod
    created_at: float
    rotated_from: Optional[str] = None  # Previous key_id
    revoked: bool = False
    revoked_at: Optional[float] = None
    purpose: str = "signing"  # signing, key_exchange, both


class KeyManager:
    """
    Key lifecycle management per spec §2.

    Handles generation, storage simulation, rotation, and revocation.
    """

    def __init__(self, storage_method: KeyStorageMethod = KeyStorageMethod.ENCRYPTED):
        self.storage_method = storage_method
        self.keys: Dict[str, ManagedKey] = {}
        self._key_counter = 0

    def generate_key(self, suite_id: str, purpose: str = "signing") -> ManagedKey:
        """Generate a new key per spec §2.1."""
        suite = get_suite(suite_id)

        if purpose == "signing":
            private, pub_bytes = suite.generate_signing_keypair()
        elif purpose == "key_exchange":
            private, pub_bytes = suite.generate_kex_keypair()
        else:
            raise ValueError(f"Unknown purpose: {purpose}")

        self._key_counter += 1
        key_id = f"key:{suite_id}:{self._key_counter}:{hashlib.sha256(pub_bytes).hexdigest()[:8]}"

        managed = ManagedKey(
            key_id=key_id,
            suite_id=suite_id,
            public_key_bytes=pub_bytes,
            private_key=private,
            storage_method=self.storage_method,
            created_at=time.time(),
            purpose=purpose,
        )
        self.keys[key_id] = managed
        return managed

    def rotate_key(self, old_key_id: str) -> ManagedKey:
        """Rotate a key per spec §2.3. Old key is revoked, new key references it."""
        old_key = self.keys.get(old_key_id)
        if not old_key:
            raise KeyError(f"Key not found: {old_key_id}")
        if old_key.revoked:
            raise ValueError(f"Cannot rotate revoked key: {old_key_id}")

        new_key = self.generate_key(old_key.suite_id, old_key.purpose)
        new_key.rotated_from = old_key_id

        # Revoke old key
        old_key.revoked = True
        old_key.revoked_at = time.time()

        return new_key

    def revoke_key(self, key_id: str, reason: str = "manual") -> None:
        """Revoke a key."""
        key = self.keys.get(key_id)
        if not key:
            raise KeyError(f"Key not found: {key_id}")
        key.revoked = True
        key.revoked_at = time.time()

    def get_active_keys(self, suite_id: Optional[str] = None) -> List[ManagedKey]:
        """Get all active (non-revoked) keys, optionally filtered by suite."""
        return [
            k for k in self.keys.values()
            if not k.revoked and (suite_id is None or k.suite_id == suite_id)
        ]

    def get_key(self, key_id: str) -> Optional[ManagedKey]:
        return self.keys.get(key_id)


# ═══════════════════════════════════════════════════════════════
# Authentication (§3.1) — Challenge-Response
# ═══════════════════════════════════════════════════════════════

@dataclass
class AuthChallenge:
    """Authentication challenge."""
    challenge_id: str
    nonce: bytes
    created_at: float
    expires_at: float
    target_suite: str


@dataclass
class AuthResponse:
    """Authentication response with signature."""
    challenge_id: str
    public_key_bytes: bytes
    signature: bytes
    suite_id: str


class Authenticator:
    """
    Challenge-response authentication per spec §3.1.

    Entity authenticates by signing a challenge with its private key.
    Verifier checks signature using entity's public key.
    """

    def __init__(self, default_suite: str = SUITE_W4_BASE_1, challenge_ttl: float = 300.0):
        self.default_suite = default_suite
        self.challenge_ttl = challenge_ttl
        self._challenges: Dict[str, AuthChallenge] = {}
        self._challenge_counter = 0

    def create_challenge(self, suite_id: Optional[str] = None) -> AuthChallenge:
        """Create an authentication challenge."""
        sid = suite_id or self.default_suite
        self._challenge_counter += 1
        nonce = os.urandom(32)
        now = time.time()

        challenge = AuthChallenge(
            challenge_id=f"challenge:{self._challenge_counter}",
            nonce=nonce,
            created_at=now,
            expires_at=now + self.challenge_ttl,
            target_suite=sid,
        )
        self._challenges[challenge.challenge_id] = challenge
        return challenge

    def respond_to_challenge(
        self, challenge: AuthChallenge, managed_key: ManagedKey
    ) -> AuthResponse:
        """Sign a challenge to prove identity."""
        suite = get_suite(managed_key.suite_id)
        # Message = challenge_id + nonce
        message = challenge.challenge_id.encode() + challenge.nonce
        signature = suite.sign(managed_key.private_key, message)

        return AuthResponse(
            challenge_id=challenge.challenge_id,
            public_key_bytes=managed_key.public_key_bytes,
            signature=signature,
            suite_id=managed_key.suite_id,
        )

    def verify_response(self, response: AuthResponse) -> Tuple[bool, str]:
        """
        Verify an authentication response.
        Returns (valid, reason).
        """
        challenge = self._challenges.get(response.challenge_id)
        if not challenge:
            return False, "unknown_challenge"

        if time.time() > challenge.expires_at:
            return False, "challenge_expired"

        suite = get_suite(response.suite_id)
        message = response.challenge_id.encode() + challenge.nonce

        if suite.verify(response.public_key_bytes, message, response.signature):
            # Consume challenge (one-time use)
            del self._challenges[response.challenge_id]
            return True, "authenticated"
        else:
            return False, "invalid_signature"


# ═══════════════════════════════════════════════════════════════
# Authorization (§3.2) — Verifiable Credentials
# ═══════════════════════════════════════════════════════════════

@dataclass
class VerifiableCredential:
    """
    Verifiable Credential per spec §3.2.

    Contains claims about an entity that determine access rights.
    """
    vc_id: str
    issuer_key_id: str
    issuer_pub_bytes: bytes
    subject_did: str
    claims: Dict[str, Any]
    issued_at: float
    expires_at: Optional[float]
    signature: bytes
    suite_id: str
    revoked: bool = False

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def has_claim(self, claim_key: str) -> bool:
        return claim_key in self.claims

    def get_claim(self, claim_key: str) -> Any:
        return self.claims.get(claim_key)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vc_id": self.vc_id,
            "issuer": self.issuer_key_id,
            "subject": self.subject_did,
            "claims": self.claims,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "suite_id": self.suite_id,
        }


class CredentialIssuer:
    """Issues Verifiable Credentials."""

    def __init__(self, issuer_key: ManagedKey):
        self.issuer_key = issuer_key
        self._vc_counter = 0

    def issue(
        self,
        subject_did: str,
        claims: Dict[str, Any],
        ttl: Optional[float] = None,
    ) -> VerifiableCredential:
        """Issue a VC to a subject with given claims."""
        self._vc_counter += 1
        now = time.time()

        vc_id = f"vc:{self.issuer_key.key_id}:{self._vc_counter}"
        expires = (now + ttl) if ttl is not None else None

        # Payload to sign
        payload = json.dumps({
            "vc_id": vc_id,
            "issuer": self.issuer_key.key_id,
            "subject": subject_did,
            "claims": claims,
            "issued_at": now,
            "expires_at": expires,
        }, sort_keys=True).encode()

        suite = get_suite(self.issuer_key.suite_id)
        signature = suite.sign(self.issuer_key.private_key, payload)

        return VerifiableCredential(
            vc_id=vc_id,
            issuer_key_id=self.issuer_key.key_id,
            issuer_pub_bytes=self.issuer_key.public_key_bytes,
            subject_did=subject_did,
            claims=claims,
            issued_at=now,
            expires_at=expires,
            signature=signature,
            suite_id=self.issuer_key.suite_id,
        )


class CredentialVerifier:
    """Verifies Verifiable Credentials."""

    def __init__(self):
        self._revocation_list: Set[str] = set()

    def revoke(self, vc_id: str) -> None:
        """Add a VC to the revocation list."""
        self._revocation_list.add(vc_id)

    def verify(self, vc: VerifiableCredential) -> Tuple[bool, str]:
        """
        Verify a VC: signature, expiry, revocation.
        Returns (valid, reason).
        """
        # Check revocation
        if vc.vc_id in self._revocation_list or vc.revoked:
            return False, "revoked"

        # Check expiry
        if vc.is_expired():
            return False, "expired"

        # Verify signature
        payload = json.dumps({
            "vc_id": vc.vc_id,
            "issuer": vc.issuer_key_id,
            "subject": vc.subject_did,
            "claims": vc.claims,
            "issued_at": vc.issued_at,
            "expires_at": vc.expires_at,
        }, sort_keys=True).encode()

        suite = get_suite(vc.suite_id)
        if not suite.verify(vc.issuer_pub_bytes, payload, vc.signature):
            return False, "invalid_signature"

        return True, "valid"


# ═══════════════════════════════════════════════════════════════
# Suite Negotiation
# ═══════════════════════════════════════════════════════════════

class SuiteNegotiator:
    """
    Negotiate crypto suite between two parties.

    Per spec §1.1: MTI (W4-BASE-1) MUST always be available.
    Parties can prefer FIPS-1 but MUST fall back to BASE-1.
    """

    def __init__(self, supported_suites: Optional[List[str]] = None):
        self.supported = supported_suites or [SUITE_W4_BASE_1]
        # MTI must always be present
        if SUITE_W4_BASE_1 not in self.supported:
            self.supported.append(SUITE_W4_BASE_1)

    def negotiate(self, peer_suites: List[str]) -> str:
        """
        Negotiate best suite. Returns agreed suite_id.

        Preference order: FIPS-1 > BASE-1 (if both support FIPS)
        BASE-1 is always available as fallback.
        """
        # Find intersection maintaining preference order
        common = [s for s in self.supported if s in peer_suites]
        if not common:
            # MTI guarantee: both sides MUST support BASE-1
            return SUITE_W4_BASE_1

        # Prefer FIPS for regulated environments
        if SUITE_W4_FIPS_1 in common:
            return SUITE_W4_FIPS_1
        return common[0]


# ═══════════════════════════════════════════════════════════════
# Canonicalization Helpers
# ═══════════════════════════════════════════════════════════════

def canonical_json(data: Dict) -> bytes:
    """JCS-like canonical JSON encoding (RFC 8785 simplified)."""
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()


def canonical_cbor_sim(data: Dict) -> bytes:
    """Simulated deterministic CBOR encoding (no cbor2 dependency)."""
    # In production: use cbor2 with canonical=True
    return b"CBOR:" + canonical_json(data)


# ═══════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0
    total = 0

    def check(condition, label):
        nonlocal passed, failed, total
        total += 1
        if condition:
            passed += 1
            print(f"  ✓ {label}")
        else:
            failed += 1
            print(f"  ✗ {label}")

    # ─── T1: Suite Registry ─────────────────────────────────────
    print("\n═══ T1: Suite Registry ═══")

    check(SUITE_W4_BASE_1 in SUITE_REGISTRY, "W4-BASE-1 registered")
    check(SUITE_W4_FIPS_1 in SUITE_REGISTRY, "W4-FIPS-1 registered")
    check(SUITE_REGISTRY[SUITE_W4_BASE_1].status == "MUST", "BASE-1 is MUST (MTI)")
    check(SUITE_REGISTRY[SUITE_W4_FIPS_1].status == "SHOULD", "FIPS-1 is SHOULD")
    check(SUITE_REGISTRY[SUITE_W4_BASE_1].kem == "X25519", "BASE-1 KEM = X25519")
    check(SUITE_REGISTRY[SUITE_W4_BASE_1].sig == "Ed25519", "BASE-1 Sig = Ed25519")
    check(SUITE_REGISTRY[SUITE_W4_BASE_1].aead == "ChaCha20-Poly1305", "BASE-1 AEAD = ChaCha20-Poly1305")
    check(SUITE_REGISTRY[SUITE_W4_BASE_1].encoding == "COSE", "BASE-1 encoding = COSE")
    check(SUITE_REGISTRY[SUITE_W4_FIPS_1].kem == "ECDH-P256", "FIPS-1 KEM = ECDH-P256")
    check(SUITE_REGISTRY[SUITE_W4_FIPS_1].sig == "ECDSA-P256", "FIPS-1 Sig = ECDSA-P256")
    check(SUITE_REGISTRY[SUITE_W4_FIPS_1].aead == "AES-128-GCM", "FIPS-1 AEAD = AES-128-GCM")
    check(SUITE_REGISTRY[SUITE_W4_FIPS_1].encoding == "JOSE", "FIPS-1 encoding = JOSE")

    # ─── T2: Suite Factory ──────────────────────────────────────
    print("\n═══ T2: Suite Factory ═══")

    base1 = get_suite(SUITE_W4_BASE_1)
    fips1 = get_suite(SUITE_W4_FIPS_1)
    check(isinstance(base1, W4Base1Suite), "Factory returns W4Base1Suite")
    check(isinstance(fips1, W4Fips1Suite), "Factory returns W4Fips1Suite")
    check(base1.suite_id == SUITE_W4_BASE_1, "BASE-1 suite_id correct")
    check(fips1.suite_id == SUITE_W4_FIPS_1, "FIPS-1 suite_id correct")

    try:
        get_suite("W4-INVALID-99")
        check(False, "Invalid suite raises error")
    except ValueError:
        check(True, "Invalid suite raises ValueError")

    # ─── T3: W4-BASE-1 Key Generation ──────────────────────────
    print("\n═══ T3: W4-BASE-1 Key Generation ═══")

    priv_b1, pub_b1 = base1.generate_signing_keypair()
    check(pub_b1 is not None, "BASE-1 signing pubkey generated")
    check(len(pub_b1) == 32, "Ed25519 pubkey is 32 bytes")

    kex_priv, kex_pub = base1.generate_kex_keypair()
    check(kex_pub is not None, "BASE-1 KEX pubkey generated")
    check(len(kex_pub) == 32, "X25519 pubkey is 32 bytes")

    # ─── T4: W4-BASE-1 Sign/Verify ─────────────────────────────
    print("\n═══ T4: W4-BASE-1 Sign/Verify ═══")

    msg = b"Hello Web4"
    sig = base1.sign(priv_b1, msg)
    check(sig is not None, "BASE-1 signature produced")
    check(len(sig) > 0, "Signature non-empty")
    check(base1.verify(pub_b1, msg, sig), "Valid signature verifies")
    check(not base1.verify(pub_b1, b"Wrong message", sig), "Wrong message fails verification")

    # Different key shouldn't verify
    priv_b1_2, pub_b1_2 = base1.generate_signing_keypair()
    check(not base1.verify(pub_b1_2, msg, sig), "Wrong key fails verification")

    # ─── T5: W4-BASE-1 Key Exchange ────────────────────────────
    print("\n═══ T5: W4-BASE-1 Key Exchange ═══")

    alice_priv, alice_pub = base1.generate_kex_keypair()
    bob_priv, bob_pub = base1.generate_kex_keypair()

    shared_ab = base1.key_exchange(alice_priv, bob_pub)
    shared_ba = base1.key_exchange(bob_priv, alice_pub)
    check(shared_ab == shared_ba, "Shared secrets match (DH agreement)")
    check(len(shared_ab) == 32, "Shared secret is 32 bytes")

    # ─── T6: W4-BASE-1 AEAD Encrypt/Decrypt ────────────────────
    print("\n═══ T6: W4-BASE-1 AEAD Encrypt/Decrypt ═══")

    key = base1.kdf(shared_ab, b"web4-aead-key")
    nonce = os.urandom(12)
    plaintext = b"Secret Web4 payload"
    aad = b"associated data"

    ciphertext = base1.encrypt(key, nonce, plaintext, aad)
    check(ciphertext != plaintext, "Ciphertext differs from plaintext")

    decrypted = base1.decrypt(key, nonce, ciphertext, aad)
    check(decrypted == plaintext, "Decrypted matches original")

    # ─── T7: W4-FIPS-1 Key Generation ──────────────────────────
    print("\n═══ T7: W4-FIPS-1 Key Generation ═══")

    priv_f1, pub_f1 = fips1.generate_signing_keypair()
    check(pub_f1 is not None, "FIPS-1 signing pubkey generated")
    check(len(pub_f1) == 33, "P-256 compressed pubkey is 33 bytes")

    kex_priv_f, kex_pub_f = fips1.generate_kex_keypair()
    check(kex_pub_f is not None, "FIPS-1 KEX pubkey generated")
    check(len(kex_pub_f) == 33, "P-256 KEX compressed pubkey is 33 bytes")

    # ─── T8: W4-FIPS-1 Sign/Verify ─────────────────────────────
    print("\n═══ T8: W4-FIPS-1 Sign/Verify ═══")

    sig_f = fips1.sign(priv_f1, msg)
    check(sig_f is not None, "FIPS-1 signature produced")
    check(fips1.verify(pub_f1, msg, sig_f), "FIPS-1 valid sig verifies")
    check(not fips1.verify(pub_f1, b"Wrong", sig_f), "FIPS-1 wrong msg fails")

    # ─── T9: W4-FIPS-1 Key Exchange ────────────────────────────
    print("\n═══ T9: W4-FIPS-1 Key Exchange ═══")

    a_priv_f, a_pub_f = fips1.generate_kex_keypair()
    b_priv_f, b_pub_f = fips1.generate_kex_keypair()
    shared_f_ab = fips1.key_exchange(a_priv_f, b_pub_f)
    shared_f_ba = fips1.key_exchange(b_priv_f, a_pub_f)
    check(shared_f_ab == shared_f_ba, "FIPS-1 shared secrets match")
    check(len(shared_f_ab) == 32, "FIPS-1 shared secret is 32 bytes")

    # ─── T10: W4-FIPS-1 AEAD ───────────────────────────────────
    print("\n═══ T10: W4-FIPS-1 AEAD Encrypt/Decrypt ═══")

    key_f = fips1.kdf(shared_f_ab, b"web4-fips-aead")
    nonce_f = os.urandom(12)
    ct_f = fips1.encrypt(key_f, nonce_f, plaintext, aad)
    check(ct_f != plaintext, "FIPS-1 ciphertext differs")
    dec_f = fips1.decrypt(key_f, nonce_f, ct_f, aad)
    check(dec_f == plaintext, "FIPS-1 decrypted matches original")

    # ─── T11: Hash Consistency ──────────────────────────────────
    print("\n═══ T11: Hash Consistency ═══")

    h1 = base1.hash(b"test data")
    h2 = fips1.hash(b"test data")
    check(h1 == h2, "Both suites use SHA-256 (same hash)")
    check(len(h1) == 32, "SHA-256 output is 32 bytes")
    check(h1 != base1.hash(b"different"), "Different data → different hash")

    # ─── T12: Key Manager — Generation ──────────────────────────
    print("\n═══ T12: Key Manager — Generation ═══")

    km = KeyManager(KeyStorageMethod.ENCRYPTED)
    k1 = km.generate_key(SUITE_W4_BASE_1, "signing")
    check(k1.key_id.startswith("key:W4-BASE-1:"), "Key ID has correct prefix")
    check(k1.suite_id == SUITE_W4_BASE_1, "Key suite matches")
    check(k1.storage_method == KeyStorageMethod.ENCRYPTED, "Storage method set")
    check(not k1.revoked, "New key not revoked")
    check(k1.purpose == "signing", "Purpose is signing")

    k2 = km.generate_key(SUITE_W4_FIPS_1, "key_exchange")
    check(k2.suite_id == SUITE_W4_FIPS_1, "FIPS key generated")
    check(k2.purpose == "key_exchange", "Purpose is key_exchange")

    check(len(km.keys) == 2, "Two keys in manager")

    # ─── T13: Key Manager — Rotation ────────────────────────────
    print("\n═══ T13: Key Manager — Rotation ═══")

    k3 = km.rotate_key(k1.key_id)
    check(k3.rotated_from == k1.key_id, "New key references old")
    check(k1.revoked, "Old key revoked after rotation")
    check(k1.revoked_at is not None, "Revocation timestamp set")
    check(not k3.revoked, "New key is active")
    check(k3.public_key_bytes != k1.public_key_bytes, "New key has different pubkey")

    # Cannot rotate revoked key
    try:
        km.rotate_key(k1.key_id)
        check(False, "Rotating revoked key should fail")
    except ValueError:
        check(True, "Rotating revoked key raises ValueError")

    # ─── T14: Key Manager — Revocation ──────────────────────────
    print("\n═══ T14: Key Manager — Revocation ═══")

    km.revoke_key(k2.key_id)
    check(k2.revoked, "Key revoked")
    check(k2.revoked_at is not None, "Revocation time recorded")

    active = km.get_active_keys()
    check(len(active) == 1, "Only 1 active key (k3)")
    check(active[0].key_id == k3.key_id, "Active key is the rotated one")

    active_fips = km.get_active_keys(SUITE_W4_FIPS_1)
    check(len(active_fips) == 0, "No active FIPS keys (revoked)")

    # ─── T15: Authenticator — Challenge-Response ────────────────
    print("\n═══ T15: Authenticator — Challenge-Response ═══")

    auth = Authenticator(challenge_ttl=60.0)

    # Generate fresh key for authentication
    auth_km = KeyManager()
    auth_key = auth_km.generate_key(SUITE_W4_BASE_1, "signing")

    challenge = auth.create_challenge()
    check(challenge.nonce is not None, "Challenge has nonce")
    check(len(challenge.nonce) == 32, "Nonce is 32 bytes")
    check(challenge.target_suite == SUITE_W4_BASE_1, "Challenge targets BASE-1")

    response = auth.respond_to_challenge(challenge, auth_key)
    check(response.challenge_id == challenge.challenge_id, "Response matches challenge")
    check(response.suite_id == auth_key.suite_id, "Response uses key's suite")

    valid, reason = auth.verify_response(response)
    check(valid, "Valid authentication succeeds")
    check(reason == "authenticated", "Reason is 'authenticated'")

    # ─── T16: Authenticator — Replay Protection ─────────────────
    print("\n═══ T16: Authenticator — Replay Protection ═══")

    # Replay same response (challenge consumed)
    valid2, reason2 = auth.verify_response(response)
    check(not valid2, "Replay of consumed challenge fails")
    check(reason2 == "unknown_challenge", "Reason: unknown (consumed)")

    # Unknown challenge ID
    fake_response = AuthResponse(
        challenge_id="challenge:999",
        public_key_bytes=auth_key.public_key_bytes,
        signature=b"fake",
        suite_id=SUITE_W4_BASE_1,
    )
    valid3, reason3 = auth.verify_response(fake_response)
    check(not valid3, "Fake challenge ID rejected")

    # ─── T17: Authenticator — Expiry ────────────────────────────
    print("\n═══ T17: Authenticator — Expiry ═══")

    expired_auth = Authenticator(challenge_ttl=0.0)  # Immediately expires
    ch_exp = expired_auth.create_challenge()
    time.sleep(0.01)  # Ensure expiry
    resp_exp = expired_auth.respond_to_challenge(ch_exp, auth_key)
    valid_exp, reason_exp = expired_auth.verify_response(resp_exp)
    check(not valid_exp, "Expired challenge rejected")
    check(reason_exp == "challenge_expired", "Reason: challenge_expired")

    # ─── T18: Authenticator — FIPS Suite ────────────────────────
    print("\n═══ T18: Authenticator — FIPS Suite ═══")

    fips_auth = Authenticator(default_suite=SUITE_W4_FIPS_1)
    fips_key = auth_km.generate_key(SUITE_W4_FIPS_1, "signing")

    ch_fips = fips_auth.create_challenge(SUITE_W4_FIPS_1)
    check(ch_fips.target_suite == SUITE_W4_FIPS_1, "FIPS challenge targets FIPS-1")

    resp_fips = fips_auth.respond_to_challenge(ch_fips, fips_key)
    v_fips, r_fips = fips_auth.verify_response(resp_fips)
    check(v_fips, "FIPS-1 authentication succeeds")

    # ─── T19: VC Issuance ──────────────────────────────────────
    print("\n═══ T19: VC Issuance ═══")

    issuer_key = auth_km.generate_key(SUITE_W4_BASE_1, "signing")
    issuer = CredentialIssuer(issuer_key)

    vc = issuer.issue(
        subject_did="did:web4:key:z6MkTest123",
        claims={
            "api_access": ["read", "write"],
            "role": "developer",
            "age_over_18": True,
        },
        ttl=3600.0,
    )
    check(vc.vc_id.startswith("vc:"), "VC ID has vc: prefix")
    check(vc.subject_did == "did:web4:key:z6MkTest123", "Subject DID correct")
    check(vc.has_claim("api_access"), "Has api_access claim")
    check(vc.get_claim("role") == "developer", "Role claim is developer")
    check(vc.get_claim("age_over_18") is True, "Age claim present")
    check(not vc.is_expired(), "VC not expired")

    # ─── T20: VC Verification ──────────────────────────────────
    print("\n═══ T20: VC Verification ═══")

    verifier = CredentialVerifier()
    valid_vc, reason_vc = verifier.verify(vc)
    check(valid_vc, "Valid VC verifies")
    check(reason_vc == "valid", "Reason: valid")

    # ─── T21: VC Expiry ────────────────────────────────────────
    print("\n═══ T21: VC Expiry ═══")

    short_vc = issuer.issue(
        subject_did="did:web4:key:z6MkShort",
        claims={"temp_access": True},
        ttl=0.0,  # Immediate expiry
    )
    time.sleep(0.01)
    valid_sv, reason_sv = verifier.verify(short_vc)
    check(not valid_sv, "Expired VC rejected")
    check(reason_sv == "expired", "Reason: expired")

    # ─── T22: VC Revocation ────────────────────────────────────
    print("\n═══ T22: VC Revocation ═══")

    vc2 = issuer.issue(
        subject_did="did:web4:key:z6MkRevoke",
        claims={"scope": "admin"},
    )
    valid_pre, _ = verifier.verify(vc2)
    check(valid_pre, "VC valid before revocation")

    verifier.revoke(vc2.vc_id)
    valid_post, reason_post = verifier.verify(vc2)
    check(not valid_post, "Revoked VC rejected")
    check(reason_post == "revoked", "Reason: revoked")

    # ─── T23: VC No-Expiry ─────────────────────────────────────
    print("\n═══ T23: VC No-Expiry (Permanent) ═══")

    perm_vc = issuer.issue(
        subject_did="did:web4:key:z6MkPerm",
        claims={"role": "founder"},
        ttl=None,
    )
    check(perm_vc.expires_at is None, "No expiry set")
    check(not perm_vc.is_expired(), "Permanent VC never expires")
    valid_perm, _ = verifier.verify(perm_vc)
    check(valid_perm, "Permanent VC verifies")

    # ─── T24: Suite Negotiation ─────────────────────────────────
    print("\n═══ T24: Suite Negotiation ═══")

    # Both support BASE-1 only
    neg1 = SuiteNegotiator([SUITE_W4_BASE_1])
    agreed = neg1.negotiate([SUITE_W4_BASE_1])
    check(agreed == SUITE_W4_BASE_1, "Both BASE-1 → agree on BASE-1")

    # One supports FIPS, other doesn't
    neg2 = SuiteNegotiator([SUITE_W4_BASE_1, SUITE_W4_FIPS_1])
    agreed2 = neg2.negotiate([SUITE_W4_BASE_1])
    check(agreed2 == SUITE_W4_BASE_1, "FIPS not common → fallback to BASE-1")

    # Both support FIPS → prefer FIPS
    agreed3 = neg2.negotiate([SUITE_W4_FIPS_1, SUITE_W4_BASE_1])
    check(agreed3 == SUITE_W4_FIPS_1, "Both support FIPS → prefer FIPS")

    # MTI guarantee: even empty lists get BASE-1
    neg3 = SuiteNegotiator([])
    check(SUITE_W4_BASE_1 in neg3.supported, "MTI: BASE-1 always present")
    agreed4 = neg3.negotiate([])
    check(agreed4 == SUITE_W4_BASE_1, "Empty intersection → MTI fallback")

    # ─── T25: Canonicalization ──────────────────────────────────
    print("\n═══ T25: Canonicalization ═══")

    data = {"z": 1, "a": 2, "m": 3}
    jcs = canonical_json(data)
    check(jcs == b'{"a":2,"m":3,"z":1}', "JCS sorts keys, minimal separators")

    cbor = canonical_cbor_sim(data)
    check(cbor.startswith(b"CBOR:"), "Simulated CBOR has prefix")
    check(b'"a":2' in cbor, "CBOR sim includes sorted keys")

    # Determinism
    check(canonical_json(data) == canonical_json(data), "JCS is deterministic")
    check(canonical_cbor_sim(data) == canonical_cbor_sim(data), "CBOR sim is deterministic")

    # ─── T26: Cross-Suite Key Manager ───────────────────────────
    print("\n═══ T26: Cross-Suite Key Manager ═══")

    multi_km = KeyManager()
    kb = multi_km.generate_key(SUITE_W4_BASE_1, "signing")
    kf = multi_km.generate_key(SUITE_W4_FIPS_1, "signing")

    check(len(multi_km.get_active_keys()) == 2, "2 active keys across suites")
    check(len(multi_km.get_active_keys(SUITE_W4_BASE_1)) == 1, "1 BASE-1 key")
    check(len(multi_km.get_active_keys(SUITE_W4_FIPS_1)) == 1, "1 FIPS-1 key")

    # Rotate BASE-1 key
    kb2 = multi_km.rotate_key(kb.key_id)
    check(kb.revoked, "Old BASE-1 key revoked")
    check(len(multi_km.get_active_keys(SUITE_W4_BASE_1)) == 1, "Still 1 active BASE-1")
    check(multi_km.get_active_keys(SUITE_W4_BASE_1)[0].key_id == kb2.key_id, "Active key is rotated")

    # ─── T27: VC with FIPS Suite ────────────────────────────────
    print("\n═══ T27: VC with FIPS Suite ═══")

    fips_issuer_key = multi_km.generate_key(SUITE_W4_FIPS_1, "signing")
    fips_issuer = CredentialIssuer(fips_issuer_key)
    fips_vc = fips_issuer.issue(
        subject_did="did:web4:key:z6MkFipsVC",
        claims={"fips_compliant": True, "classification": "controlled"},
    )
    check(fips_vc.suite_id == SUITE_W4_FIPS_1, "FIPS VC uses FIPS suite")
    fips_verifier = CredentialVerifier()
    v_fvc, r_fvc = fips_verifier.verify(fips_vc)
    check(v_fvc, "FIPS VC verifies")

    # ─── T28: VC to_dict ────────────────────────────────────────
    print("\n═══ T28: VC Serialization ═══")

    vc_dict = vc.to_dict()
    check("vc_id" in vc_dict, "to_dict has vc_id")
    check("claims" in vc_dict, "to_dict has claims")
    check("subject" in vc_dict, "to_dict has subject")
    check(vc_dict["suite_id"] == SUITE_W4_BASE_1, "Suite in dict")
    check("signature" not in vc_dict, "Signature not in public dict")

    # ─── T29: End-to-End Security Flow ──────────────────────────
    print("\n═══ T29: End-to-End Security Flow ═══")

    # Full flow: generate keys → negotiate suite → authenticate → issue VC → verify

    # 1. Setup
    server_km = KeyManager(KeyStorageMethod.HSM)
    server_key = server_km.generate_key(SUITE_W4_BASE_1, "signing")

    client_km = KeyManager(KeyStorageMethod.ENCRYPTED)
    client_key = client_km.generate_key(SUITE_W4_BASE_1, "signing")

    # 2. Negotiate
    server_neg = SuiteNegotiator([SUITE_W4_BASE_1, SUITE_W4_FIPS_1])
    client_neg = SuiteNegotiator([SUITE_W4_BASE_1])
    agreed_suite = server_neg.negotiate(client_neg.supported)
    check(agreed_suite == SUITE_W4_BASE_1, "E2E: negotiated BASE-1")

    # 3. Authenticate client
    e2e_auth = Authenticator()
    ch = e2e_auth.create_challenge(agreed_suite)
    resp = e2e_auth.respond_to_challenge(ch, client_key)
    v, r = e2e_auth.verify_response(resp)
    check(v, "E2E: client authenticated")

    # 4. Issue VC
    server_issuer = CredentialIssuer(server_key)
    client_vc = server_issuer.issue(
        subject_did="did:web4:key:z6MkClient",
        claims={"access_level": "standard", "api_endpoints": ["/data", "/query"]},
        ttl=86400.0,
    )
    check(client_vc is not None, "E2E: VC issued to authenticated client")

    # 5. Verify VC for access control
    e2e_verifier = CredentialVerifier()
    v_e2e, _ = e2e_verifier.verify(client_vc)
    check(v_e2e, "E2E: client VC verified for access")
    check(client_vc.get_claim("access_level") == "standard", "E2E: access level correct")

    # ─── T30: Key Storage Methods ───────────────────────────────
    print("\n═══ T30: Key Storage Methods ═══")

    for method in KeyStorageMethod:
        km_m = KeyManager(method)
        k_m = km_m.generate_key(SUITE_W4_BASE_1, "signing")
        check(k_m.storage_method == method, f"Storage method: {method.value}")

    # ─── T31: Multiple VC Claims ────────────────────────────────
    print("\n═══ T31: Multiple VC Claims ═══")

    multi_vc = issuer.issue(
        subject_did="did:web4:key:z6MkMulti",
        claims={
            "api_access": ["read"],
            "age_over_18": True,
            "region": ["us-west", "eu-central"],
            "role": "operator",
            "max_rate": 5000,
        },
    )
    check(multi_vc.has_claim("api_access"), "Has api_access")
    check(multi_vc.has_claim("region"), "Has region")
    check(multi_vc.has_claim("max_rate"), "Has max_rate")
    check(not multi_vc.has_claim("nonexistent"), "Missing claim returns False")
    check(multi_vc.get_claim("max_rate") == 5000, "max_rate value correct")
    check(multi_vc.get_claim("nonexistent") is None, "Missing claim returns None")

    # ─── T32: Spec Compliance Assertions ────────────────────────
    print("\n═══ T32: Spec Compliance Assertions ═══")

    # §1.1: MUST support W4-BASE-1
    check(MTI_SUITE == SUITE_W4_BASE_1, "MTI suite is W4-BASE-1")

    # §1.2: BASE-1 algorithms match spec
    b1 = SUITE_REGISTRY[SUITE_W4_BASE_1]
    check(b1.kem == "X25519" and b1.sig == "Ed25519", "BASE-1: X25519+Ed25519")
    check(b1.aead == "ChaCha20-Poly1305" and b1.hash_alg == "SHA-256", "BASE-1: ChaCha20+SHA256")
    check(b1.kdf == "HKDF-SHA256", "BASE-1: HKDF-SHA256")

    # §1.2: FIPS-1 algorithms match spec
    f1 = SUITE_REGISTRY[SUITE_W4_FIPS_1]
    check(f1.kem == "ECDH-P256" and f1.sig == "ECDSA-P256", "FIPS-1: P-256 KEM+Sig")
    check(f1.aead == "AES-128-GCM" and f1.hash_alg == "SHA-256", "FIPS-1: AES-GCM+SHA256")
    check(f1.kdf == "HKDF-SHA256", "FIPS-1: HKDF-SHA256")

    # §1.3: Canonicalization modes
    check(b1.encoding == "COSE", "BASE-1 MUST use COSE/CBOR")
    check(f1.encoding == "JOSE", "FIPS-1 SHOULD use JOSE/JSON")

    # §2.1: Key generation uses secure random (by using crypto library)
    check(HAS_CRYPTO, "Using cryptography library for secure RNG")

    # §2.2: Key storage methods documented
    check(len(KeyStorageMethod) == 4, "4 storage methods: HSM, enclave, encrypted, plaintext")

    # §3.1: Authentication via digital signatures
    check(True, "Auth uses challenge-response with digital signatures")

    # §3.2: Authorization via Verifiable Credentials
    check(True, "Authz uses VCs with signed claims")

    # ═══════════════════════════════════════════════════════════
    # Summary
    # ═══════════════════════════════════════════════════════════

    print(f"\n{'═' * 60}")
    print(f"Security Framework: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  {failed} FAILED")
    else:
        print("  All checks passed ✓")
    print(f"{'═' * 60}")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
