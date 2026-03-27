"""
Web4 Security Primitives

Canonical types per web4-standard/core-spec/security-framework.md and
web4-standard/core-spec/data-formats.md.

Provides:
- CryptoSuite: standardized cryptographic suite definitions (W4-BASE-1, W4-FIPS-1)
- W4ID: Web4 Identifier (DID:web4) parsing, validation, and pairwise derivation
- KeyPolicy: key rotation and storage policy types
- SignatureEnvelope: signed payload container

This module defines TYPES and VALIDATION only — no actual cryptographic
operations. Signing, encryption, and key generation use standard libraries
(e.g. cryptography, nacl) and are NOT provided here.

Cross-module integration:
- web4.lct: LCT IDs can embed W4IDs as entity identifiers
- web4.r6: R7Action signatures use CryptoSuite for algorithm selection
- web4.binding: hardware anchors reference key storage policies

Validated against: web4-standard/test-vectors/security/
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

__all__ = [
    # Classes
    "CryptoSuiteId", "CryptoSuite", "EncodingProfile",
    "W4IDError", "W4ID",
    "KeyStorageLevel", "KeyPolicy",
    "SignatureEnvelope", "VerifiableCredential",
    # Functions
    "get_suite", "negotiate_suite",
    "parse_w4id", "derive_pairwise_w4id",
    # Constants
    "SUITE_BASE", "SUITE_FIPS", "SUITES", "KNOWN_METHODS",
]


# ── Crypto Suites ─────────────────────────────────────────────────

class CryptoSuiteId(str, Enum):
    """Standardized cryptographic suite identifiers per spec §1.1."""
    W4_BASE_1 = "W4-BASE-1"   # MUST — Ed25519 + X25519 + ChaCha20-Poly1305
    W4_FIPS_1 = "W4-FIPS-1"   # SHOULD — ECDSA-P256 + AES-128-GCM


class EncodingProfile(str, Enum):
    """Payload encoding profiles per spec §1.3."""
    COSE = "COSE"  # MUST — CBOR-based (RFC 8152)
    JOSE = "JOSE"  # SHOULD — JSON-based (RFC 7515/7516)


@dataclass(frozen=True)
class CryptoSuite:
    """
    A complete cryptographic suite definition.

    Per spec §1.1: defines KEM, signature, AEAD, hash, KDF, and encoding
    for a given suite ID. Implementations MUST support W4-BASE-1.
    """
    suite_id: CryptoSuiteId
    kem: str            # Key Encapsulation Mechanism (e.g. "X25519")
    sig: str            # Signature algorithm (e.g. "Ed25519")
    aead: str           # Authenticated encryption (e.g. "ChaCha20-Poly1305")
    hash_alg: str       # Hash function (e.g. "SHA-256")
    kdf: str            # Key Derivation Function (e.g. "HKDF-SHA256")
    encoding: EncodingProfile

    def to_dict(self) -> Dict[str, str]:
        """Serialize suite definition to dict with all algorithm identifiers."""
        return {
            "suite_id": self.suite_id.value,
            "kem": self.kem,
            "sig": self.sig,
            "aead": self.aead,
            "hash": self.hash_alg,
            "kdf": self.kdf,
            "encoding": self.encoding.value,
        }


# Canonical suite instances per spec §1.2
SUITE_BASE = CryptoSuite(
    suite_id=CryptoSuiteId.W4_BASE_1,
    kem="X25519",
    sig="Ed25519",
    aead="ChaCha20-Poly1305",
    hash_alg="SHA-256",
    kdf="HKDF-SHA256",
    encoding=EncodingProfile.COSE,
)

SUITE_FIPS = CryptoSuite(
    suite_id=CryptoSuiteId.W4_FIPS_1,
    kem="ECDH-P256",
    sig="ECDSA-P256",
    aead="AES-128-GCM",
    hash_alg="SHA-256",
    kdf="HKDF-SHA256",
    encoding=EncodingProfile.JOSE,
)

SUITES: Dict[CryptoSuiteId, CryptoSuite] = {
    CryptoSuiteId.W4_BASE_1: SUITE_BASE,
    CryptoSuiteId.W4_FIPS_1: SUITE_FIPS,
}


def get_suite(suite_id: CryptoSuiteId) -> CryptoSuite:
    """Look up a crypto suite by ID. Raises KeyError for unknown suites."""
    return SUITES[suite_id]


def negotiate_suite(
    offered: List[CryptoSuiteId],
    supported: Optional[List[CryptoSuiteId]] = None,
) -> Optional[CryptoSuiteId]:
    """
    Suite negotiation per spec §1.1.

    Returns the best mutually-supported suite, preferring BASE over FIPS.
    Returns None if no mutual suite exists.

    Per spec: "Other suites MAY be offered but MUST NOT be negotiated as MTI."
    Only known suites (W4-BASE-1, W4-FIPS-1) can be negotiated.
    """
    if supported is None:
        supported = [CryptoSuiteId.W4_BASE_1]

    # Preference order: BASE first (mandatory), then FIPS
    preference = [CryptoSuiteId.W4_BASE_1, CryptoSuiteId.W4_FIPS_1]

    for suite in preference:
        if suite in offered and suite in supported:
            return suite

    return None


# ── W4ID (Web4 Identifier) ───────────────────────────────────────

# W4ID ABNF: "did:web4:" method-name ":" method-specific-id
_W4ID_PATTERN = re.compile(
    r"^did:web4:([a-z][a-z0-9]*):(.+)$"
)

# Known methods per spec §1.2 of data-formats.md
KNOWN_METHODS = frozenset({"key", "web"})


class W4IDError(ValueError):
    """Invalid W4ID format."""


@dataclass(frozen=True)
class W4ID:
    """
    Web4 Identifier — a DID per data-formats.md §1.

    Format: did:web4:<method>:<method-specific-id>

    Methods:
    - key: method-specific-id is a public key (self-certifying)
    - web: method-specific-id is a domain name (web-resolvable)
    """
    method: str
    method_specific_id: str

    def __post_init__(self):
        if not self.method:
            raise W4IDError("method is required")
        if not self.method_specific_id:
            raise W4IDError("method_specific_id is required")

    @property
    def did(self) -> str:
        """Full DID string."""
        return f"did:web4:{self.method}:{self.method_specific_id}"

    @property
    def is_known_method(self) -> bool:
        """True if method is one of the spec-defined methods."""
        return self.method in KNOWN_METHODS

    def to_dict(self) -> Dict[str, str]:
        """Serialize W4ID to dict with full DID string, method, and method-specific ID."""
        return {
            "did": self.did,
            "method": self.method,
            "method_specific_id": self.method_specific_id,
        }

    def __str__(self) -> str:
        return self.did

    def __eq__(self, other: object) -> bool:
        if isinstance(other, W4ID):
            return self.did == other.did
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.did)


def parse_w4id(did_string: str) -> W4ID:
    """
    Parse a DID string into a W4ID.

    Raises W4IDError if the format is invalid.

    Examples:
        parse_w4id("did:web4:key:z6Mkf5rGMoatrSj1f...")
        parse_w4id("did:web4:web:example.com")
    """
    match = _W4ID_PATTERN.match(did_string)
    if not match:
        raise W4IDError(
            f"invalid W4ID format: {did_string!r} "
            f"(expected did:web4:<method>:<method-specific-id>)"
        )
    return W4ID(method=match.group(1), method_specific_id=match.group(2))


def derive_pairwise_w4id(master_secret: bytes, peer_identifier: str) -> W4ID:
    """
    Derive a pairwise pseudonymous W4ID for privacy per data-formats.md §4.

    Creates a unique, unlinkable identifier for each relationship,
    preventing correlation across peers.
    """
    salt = hashlib.sha256(peer_identifier.encode()).digest()
    derived = hashlib.sha256(master_secret + salt).hexdigest()
    return W4ID(method="key", method_specific_id=derived)


# ── Key Management Policy ────────────────────────────────────────

class KeyStorageLevel(str, Enum):
    """Key storage security levels per spec §2.2."""
    HSM = "hsm"                    # Hardware Security Module
    SECURE_ENCLAVE = "secure_enclave"  # TEE / Secure Enclave
    ENCRYPTED = "encrypted"        # Software-encrypted storage
    PLAINTEXT = "plaintext"        # Unprotected (testing only)


@dataclass(frozen=True)
class KeyPolicy:
    """
    Key management policy per spec §2.

    Defines storage level, rotation interval, and allowed suites
    for an entity's key management strategy.
    """
    storage_level: KeyStorageLevel
    rotation_days: int = 365       # Key rotation interval in days
    allowed_suites: List[CryptoSuiteId] = field(
        default_factory=lambda: [CryptoSuiteId.W4_BASE_1]
    )

    def __post_init__(self):
        if self.rotation_days < 1:
            raise ValueError("rotation_days must be >= 1")

    @property
    def is_hardware_backed(self) -> bool:
        """True if keys are stored in hardware (HSM or Secure Enclave)."""
        return self.storage_level in (KeyStorageLevel.HSM, KeyStorageLevel.SECURE_ENCLAVE)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize key policy to dict with storage level, rotation interval, and allowed suites."""
        return {
            "storage_level": self.storage_level.value,
            "rotation_days": self.rotation_days,
            "allowed_suites": [s.value for s in self.allowed_suites],
            "is_hardware_backed": self.is_hardware_backed,
        }


# ── Signature Envelope ───────────────────────────────────────────

@dataclass(frozen=True)
class SignatureEnvelope:
    """
    A signed payload container per spec §1.3.

    Wraps a payload with its signature, signer identity, suite used,
    and timestamp. Does NOT perform signing — that's the crypto layer's job.
    """
    payload_hash: str              # SHA-256 of canonical payload
    signature: str                 # Base64/hex-encoded signature bytes
    signer: str                    # W4ID or LCT of signer
    suite_id: CryptoSuiteId = CryptoSuiteId.W4_BASE_1
    timestamp: str = ""            # ISO 8601 timestamp

    def to_dict(self) -> Dict[str, str]:
        """Serialize signature envelope to dict with payload hash, signature, and signer identity."""
        return {
            "payload_hash": self.payload_hash,
            "signature": self.signature,
            "signer": self.signer,
            "suite_id": self.suite_id.value,
            "timestamp": self.timestamp,
        }


# ── Verifiable Credential Structure ──────────────────────────────

@dataclass
class VerifiableCredential:
    """
    Verifiable Credential structure per data-formats.md §2.

    Follows W3C VC Data Model v1.1. This is a structural type —
    actual verification requires crypto operations not provided here.
    """
    id: str                                     # Unique credential ID
    issuer: str                                 # W4ID of issuer
    subject: str                                # W4ID of subject
    credential_type: str = "Web4Credential"     # Credential type
    issuance_date: str = ""                     # ISO 8601
    expiration_date: str = ""                   # ISO 8601 (optional)
    claims: Dict[str, Any] = field(default_factory=dict)
    proof: Optional[SignatureEnvelope] = None

    @property
    def is_expired(self) -> bool:
        """Check if credential has an expiration date that's been set."""
        # Actual date comparison requires parsing — this just checks presence.
        # Real expiration checking would compare against current time.
        return bool(self.expiration_date)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to W3C Verifiable Credential dict with @context, claims, and optional proof."""
        d: Dict[str, Any] = {
            "@context": ["https://www.w3.org/2018/credentials/v1"],
            "id": self.id,
            "type": ["VerifiableCredential", self.credential_type],
            "issuer": self.issuer,
            "issuanceDate": self.issuance_date,
            "credentialSubject": {
                "id": self.subject,
                **self.claims,
            },
        }
        if self.expiration_date:
            d["expirationDate"] = self.expiration_date
        if self.proof:
            d["proof"] = self.proof.to_dict()
        return d
