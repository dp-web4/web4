"""
Web4 Error Taxonomy

Canonical implementation per web4-standard/core-spec/errors.md.

Standardized error types for the Web4 protocol based on RFC 9457
Problem Details. Defines 24 error codes across 6 categories:
Binding, Pairing, Witness, Authorization, Cryptographic, Protocol.

All errors serialize to/from RFC 9457 Problem Details JSON format
(application/problem+json).

Validated against: web4-standard/test-vectors/errors/
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

__all__ = [
    # Classes
    "ErrorCode", "ErrorCategory", "ErrorMeta",
    "Web4Error", "BindingError", "PairingError", "WitnessError",
    "AuthzError", "CryptoError", "ProtoError",
    # Functions
    "get_error_meta", "codes_for_category", "make_error",
]


# ── Error Categories (spec §2) ────────────────────────────────

class ErrorCategory(str, Enum):
    """Web4 error code categories per spec §2."""
    BINDING = "BINDING"
    PAIRING = "PAIRING"
    WITNESS = "WITNESS"
    AUTHZ = "AUTHZ"
    CRYPTO = "CRYPTO"
    PROTO = "PROTO"


# ── Error Codes (spec §2.1-2.6) ───────────────────────────────

class ErrorCode(str, Enum):
    """All 24 Web4 error codes from the error taxonomy spec."""
    # §2.1 Binding Errors
    BINDING_EXISTS = "W4_ERR_BINDING_EXISTS"
    BINDING_INVALID = "W4_ERR_BINDING_INVALID"
    BINDING_REVOKED = "W4_ERR_BINDING_REVOKED"
    BINDING_PROOF_FAIL = "W4_ERR_BINDING_PROOF_FAIL"

    # §2.2 Pairing Errors
    PAIRING_DENIED = "W4_ERR_PAIRING_DENIED"
    PAIRING_TIMEOUT = "W4_ERR_PAIRING_TIMEOUT"
    PAIRING_INVALID = "W4_ERR_PAIRING_INVALID"
    PAIRING_EXPIRED = "W4_ERR_PAIRING_EXPIRED"

    # §2.3 Witness Errors
    WITNESS_UNAVAIL = "W4_ERR_WITNESS_UNAVAIL"
    WITNESS_REJECTED = "W4_ERR_WITNESS_REJECTED"
    WITNESS_INVALID = "W4_ERR_WITNESS_INVALID"
    WITNESS_QUORUM = "W4_ERR_WITNESS_QUORUM"

    # §2.4 Authorization Errors
    AUTHZ_DENIED = "W4_ERR_AUTHZ_DENIED"
    AUTHZ_EXPIRED = "W4_ERR_AUTHZ_EXPIRED"
    AUTHZ_SCOPE = "W4_ERR_AUTHZ_SCOPE"
    AUTHZ_RATE = "W4_ERR_AUTHZ_RATE"

    # §2.5 Cryptographic Errors
    CRYPTO_SUITE = "W4_ERR_CRYPTO_SUITE"
    CRYPTO_VERIFY = "W4_ERR_CRYPTO_VERIFY"
    CRYPTO_DECRYPT = "W4_ERR_CRYPTO_DECRYPT"
    CRYPTO_KEY = "W4_ERR_CRYPTO_KEY"

    # §2.6 Protocol Errors
    PROTO_VERSION = "W4_ERR_PROTO_VERSION"
    PROTO_SEQUENCE = "W4_ERR_PROTO_SEQUENCE"
    PROTO_REPLAY = "W4_ERR_PROTO_REPLAY"
    PROTO_DOWNGRADE = "W4_ERR_PROTO_DOWNGRADE"


# ── Error Metadata ─────────────────────────────────────────────

@dataclass(frozen=True)
class ErrorMeta:
    """Metadata for a Web4 error code from the spec."""
    code: ErrorCode
    category: ErrorCategory
    title: str
    status: int
    description: str


# Registry: every ErrorCode → its spec-defined metadata
_ERROR_REGISTRY: Dict[ErrorCode, ErrorMeta] = {
    # §2.1 Binding
    ErrorCode.BINDING_EXISTS: ErrorMeta(
        ErrorCode.BINDING_EXISTS, ErrorCategory.BINDING,
        "Binding Already Exists", 409,
        "Entity already has an active binding",
    ),
    ErrorCode.BINDING_INVALID: ErrorMeta(
        ErrorCode.BINDING_INVALID, ErrorCategory.BINDING,
        "Invalid Binding", 400,
        "Binding parameters are malformed",
    ),
    ErrorCode.BINDING_REVOKED: ErrorMeta(
        ErrorCode.BINDING_REVOKED, ErrorCategory.BINDING,
        "Binding Revoked", 410,
        "Referenced binding has been revoked",
    ),
    ErrorCode.BINDING_PROOF_FAIL: ErrorMeta(
        ErrorCode.BINDING_PROOF_FAIL, ErrorCategory.BINDING,
        "Binding Proof Failed", 401,
        "Binding proof signature verification failed",
    ),
    # §2.2 Pairing
    ErrorCode.PAIRING_DENIED: ErrorMeta(
        ErrorCode.PAIRING_DENIED, ErrorCategory.PAIRING,
        "Pairing Denied", 403,
        "Entity denied pairing request",
    ),
    ErrorCode.PAIRING_TIMEOUT: ErrorMeta(
        ErrorCode.PAIRING_TIMEOUT, ErrorCategory.PAIRING,
        "Pairing Timeout", 408,
        "Pairing handshake timed out",
    ),
    ErrorCode.PAIRING_INVALID: ErrorMeta(
        ErrorCode.PAIRING_INVALID, ErrorCategory.PAIRING,
        "Invalid Pairing", 400,
        "Pairing parameters are malformed",
    ),
    ErrorCode.PAIRING_EXPIRED: ErrorMeta(
        ErrorCode.PAIRING_EXPIRED, ErrorCategory.PAIRING,
        "Pairing Expired", 410,
        "Pairing session has expired",
    ),
    # §2.3 Witness
    ErrorCode.WITNESS_UNAVAIL: ErrorMeta(
        ErrorCode.WITNESS_UNAVAIL, ErrorCategory.WITNESS,
        "Witness Unavailable", 503,
        "Required witness is not available",
    ),
    ErrorCode.WITNESS_REJECTED: ErrorMeta(
        ErrorCode.WITNESS_REJECTED, ErrorCategory.WITNESS,
        "Witness Rejected", 403,
        "Witness rejected attestation request",
    ),
    ErrorCode.WITNESS_INVALID: ErrorMeta(
        ErrorCode.WITNESS_INVALID, ErrorCategory.WITNESS,
        "Invalid Witness", 400,
        "Witness signature or format invalid",
    ),
    ErrorCode.WITNESS_QUORUM: ErrorMeta(
        ErrorCode.WITNESS_QUORUM, ErrorCategory.WITNESS,
        "Quorum Not Met", 409,
        "Insufficient witnesses for quorum",
    ),
    # §2.4 Authorization
    ErrorCode.AUTHZ_DENIED: ErrorMeta(
        ErrorCode.AUTHZ_DENIED, ErrorCategory.AUTHZ,
        "Authorization Denied", 401,
        "Credential lacks required capability",
    ),
    ErrorCode.AUTHZ_EXPIRED: ErrorMeta(
        ErrorCode.AUTHZ_EXPIRED, ErrorCategory.AUTHZ,
        "Authorization Expired", 401,
        "Authorization token has expired",
    ),
    ErrorCode.AUTHZ_SCOPE: ErrorMeta(
        ErrorCode.AUTHZ_SCOPE, ErrorCategory.AUTHZ,
        "Insufficient Scope", 403,
        "Operation requires additional scopes",
    ),
    ErrorCode.AUTHZ_RATE: ErrorMeta(
        ErrorCode.AUTHZ_RATE, ErrorCategory.AUTHZ,
        "Rate Limit Exceeded", 429,
        "Metering rate limit exceeded",
    ),
    # §2.5 Cryptographic
    ErrorCode.CRYPTO_SUITE: ErrorMeta(
        ErrorCode.CRYPTO_SUITE, ErrorCategory.CRYPTO,
        "Unsupported Suite", 400,
        "Cryptographic suite not supported",
    ),
    ErrorCode.CRYPTO_VERIFY: ErrorMeta(
        ErrorCode.CRYPTO_VERIFY, ErrorCategory.CRYPTO,
        "Verification Failed", 401,
        "Signature verification failed",
    ),
    ErrorCode.CRYPTO_DECRYPT: ErrorMeta(
        ErrorCode.CRYPTO_DECRYPT, ErrorCategory.CRYPTO,
        "Decryption Failed", 400,
        "Failed to decrypt message",
    ),
    ErrorCode.CRYPTO_KEY: ErrorMeta(
        ErrorCode.CRYPTO_KEY, ErrorCategory.CRYPTO,
        "Invalid Key", 400,
        "Public key format or encoding invalid",
    ),
    # §2.6 Protocol
    ErrorCode.PROTO_VERSION: ErrorMeta(
        ErrorCode.PROTO_VERSION, ErrorCategory.PROTO,
        "Version Mismatch", 400,
        "Protocol version not supported",
    ),
    ErrorCode.PROTO_SEQUENCE: ErrorMeta(
        ErrorCode.PROTO_SEQUENCE, ErrorCategory.PROTO,
        "Sequence Error", 400,
        "Message sequence out of order",
    ),
    ErrorCode.PROTO_REPLAY: ErrorMeta(
        ErrorCode.PROTO_REPLAY, ErrorCategory.PROTO,
        "Replay Detected", 409,
        "Message replay attack detected",
    ),
    ErrorCode.PROTO_DOWNGRADE: ErrorMeta(
        ErrorCode.PROTO_DOWNGRADE, ErrorCategory.PROTO,
        "Downgrade Detected", 400,
        "Protocol downgrade attack detected",
    ),
}


# ── Lookup helpers ─────────────────────────────────────────────

def get_error_meta(code: ErrorCode) -> ErrorMeta:
    """Look up the spec-defined metadata for an error code."""
    return _ERROR_REGISTRY[code]


def codes_for_category(category: ErrorCategory) -> list[ErrorCode]:
    """Return all error codes belonging to a category."""
    return [
        m.code for m in _ERROR_REGISTRY.values()
        if m.category == category
    ]


# ── Base Exception ─────────────────────────────────────────────

class Web4Error(Exception):
    """Base exception for all Web4 protocol errors.

    Carries RFC 9457 Problem Details fields so that any Web4 error
    can be serialized to ``application/problem+json``.
    """

    def __init__(
        self,
        code: ErrorCode,
        detail: Optional[str] = None,
        instance: Optional[str] = None,
        *,
        error_type: str = "about:blank",
    ) -> None:
        meta = get_error_meta(code)
        self.code = code
        self.category = meta.category
        self.title = meta.title
        self.status = meta.status
        self.detail = detail or meta.description
        self.instance = instance
        self.error_type = error_type
        super().__init__(self.detail)

    def to_problem_json(self) -> Dict[str, Any]:
        """Serialize to RFC 9457 Problem Details dict."""
        result: Dict[str, Any] = {
            "type": self.error_type,
            "title": self.title,
            "status": self.status,
            "code": self.code.value,
        }
        if self.detail:
            result["detail"] = self.detail
        if self.instance:
            result["instance"] = self.instance
        return result

    def to_json(self) -> str:
        """Serialize to RFC 9457 Problem Details JSON string."""
        return json.dumps(self.to_problem_json(), indent=2)

    @classmethod
    def from_problem_json(cls, data: Dict[str, Any]) -> Web4Error:
        """Deserialize from RFC 9457 Problem Details dict.

        Returns the appropriate category subclass if one exists.
        """
        code = ErrorCode(data["code"])
        meta = get_error_meta(code)
        subclass: type[Web4Error] = _CATEGORY_SUBCLASS.get(meta.category, cls)
        return subclass(
            code,
            detail=data.get("detail"),
            instance=data.get("instance"),
            error_type=data.get("type", "about:blank"),
        )


# ── Category Subclasses ────────────────────────────────────────

class BindingError(Web4Error):
    """Error related to entity binding operations (spec §2.1)."""
    pass


class PairingError(Web4Error):
    """Error related to entity pairing operations (spec §2.2)."""
    pass


class WitnessError(Web4Error):
    """Error related to witness/attestation operations (spec §2.3)."""
    pass


class AuthzError(Web4Error):
    """Error related to authorization operations (spec §2.4)."""
    pass


class CryptoError(Web4Error):
    """Error related to cryptographic operations (spec §2.5)."""
    pass


class ProtoError(Web4Error):
    """Error related to protocol-level operations (spec §2.6)."""
    pass


# Map categories to their subclass for from_problem_json dispatch
_CATEGORY_SUBCLASS: Dict[ErrorCategory, type[Web4Error]] = {
    ErrorCategory.BINDING: BindingError,
    ErrorCategory.PAIRING: PairingError,
    ErrorCategory.WITNESS: WitnessError,
    ErrorCategory.AUTHZ: AuthzError,
    ErrorCategory.CRYPTO: CryptoError,
    ErrorCategory.PROTO: ProtoError,
}


# ── Convenience Constructor ────────────────────────────────────

def make_error(
    code: ErrorCode,
    detail: Optional[str] = None,
    instance: Optional[str] = None,
) -> Web4Error:
    """Create the appropriate Web4Error subclass for a given error code.

    Returns a BindingError for BINDING codes, AuthzError for AUTHZ codes, etc.
    """
    meta = get_error_meta(code)
    subclass: type[Web4Error] = _CATEGORY_SUBCLASS.get(meta.category, Web4Error)
    return subclass(code, detail=detail, instance=instance)
