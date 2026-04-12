#!/usr/bin/env python3
"""
Web4 Error Handler — RFC 9457 Problem Details Reference Implementation

Standardized error taxonomy per web4-standard/core-spec/errors.md.
24 error codes across 6 categories, HTTP status mapping, JSON serialization.

Provides:
  - ProblemDetails: RFC 9457 compliant error object
  - W4Error enum: all 24 Web4 error codes with metadata
  - Web4Exception: typed exception hierarchy
  - error() factory: quick error construction
  - ErrorContext: context manager for structured error wrapping

@version 1.0.0
@see web4-standard/core-spec/errors.md
@see RFC 9457: Problem Details for HTTP APIs
"""

import json
import sys
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════
# Error Code Registry — 24 codes, 6 categories
# ═══════════════════════════════════════════════════════════════

class W4Error(Enum):
    """Web4 error codes per errors.md taxonomy."""

    # 2.1 Binding Errors
    BINDING_EXISTS     = ("W4_ERR_BINDING_EXISTS",    "Binding Already Exists",   409)
    BINDING_INVALID    = ("W4_ERR_BINDING_INVALID",   "Invalid Binding",          400)
    BINDING_REVOKED    = ("W4_ERR_BINDING_REVOKED",   "Binding Revoked",          410)
    BINDING_PROOF_FAIL = ("W4_ERR_BINDING_PROOF_FAIL","Binding Proof Failed",     401)

    # 2.2 Pairing Errors
    PAIRING_DENIED     = ("W4_ERR_PAIRING_DENIED",    "Pairing Denied",           403)
    PAIRING_TIMEOUT    = ("W4_ERR_PAIRING_TIMEOUT",   "Pairing Timeout",          408)
    PAIRING_INVALID    = ("W4_ERR_PAIRING_INVALID",   "Invalid Pairing",          400)
    PAIRING_EXPIRED    = ("W4_ERR_PAIRING_EXPIRED",   "Pairing Expired",          410)

    # 2.3 Witness Errors
    WITNESS_UNAVAIL    = ("W4_ERR_WITNESS_UNAVAIL",   "Witness Unavailable",      503)
    WITNESS_REJECTED   = ("W4_ERR_WITNESS_REJECTED",  "Witness Rejected",         403)
    WITNESS_INVALID    = ("W4_ERR_WITNESS_INVALID",   "Invalid Witness",          400)
    WITNESS_QUORUM     = ("W4_ERR_WITNESS_QUORUM",    "Quorum Not Met",           409)

    # 2.4 Authorization Errors
    AUTHZ_DENIED       = ("W4_ERR_AUTHZ_DENIED",      "Authorization Denied",     401)
    AUTHZ_EXPIRED      = ("W4_ERR_AUTHZ_EXPIRED",     "Authorization Expired",    401)
    AUTHZ_SCOPE        = ("W4_ERR_AUTHZ_SCOPE",       "Insufficient Scope",       403)
    AUTHZ_RATE         = ("W4_ERR_AUTHZ_RATE",        "Rate Limit Exceeded",      429)

    # 2.5 Cryptographic Errors
    CRYPTO_SUITE       = ("W4_ERR_CRYPTO_SUITE",      "Unsupported Suite",        400)
    CRYPTO_VERIFY      = ("W4_ERR_CRYPTO_VERIFY",     "Verification Failed",      401)
    CRYPTO_DECRYPT     = ("W4_ERR_CRYPTO_DECRYPT",    "Decryption Failed",        400)
    CRYPTO_KEY         = ("W4_ERR_CRYPTO_KEY",        "Invalid Key",              400)

    # 2.6 Protocol Errors
    PROTO_VERSION      = ("W4_ERR_PROTO_VERSION",     "Version Mismatch",         400)
    PROTO_SEQUENCE     = ("W4_ERR_PROTO_SEQUENCE",    "Sequence Error",           400)
    PROTO_REPLAY       = ("W4_ERR_PROTO_REPLAY",      "Replay Detected",          409)
    PROTO_DOWNGRADE    = ("W4_ERR_PROTO_DOWNGRADE",   "Downgrade Detected",       400)

    def __init__(self, code: str, title: str, status: int):
        self.code = code
        self.title = title
        self.status = status

    @property
    def category(self) -> str:
        """Extract category from code (e.g., 'BINDING', 'PAIRING')."""
        return self.code.split("_")[2]

    @classmethod
    def from_code(cls, code: str) -> "W4Error":
        """Look up error by code string."""
        for member in cls:
            if member.code == code:
                return member
        raise ValueError(f"Unknown error code: {code}")

    @classmethod
    def by_category(cls, category: str) -> List["W4Error"]:
        """Get all errors in a category."""
        return [m for m in cls if m.category == category]

    @classmethod
    def by_status(cls, status: int) -> List["W4Error"]:
        """Get all errors with a given HTTP status."""
        return [m for m in cls if m.status == status]


# ═══════════════════════════════════════════════════════════════
# RFC 9457 Problem Details
# ═══════════════════════════════════════════════════════════════

@dataclass
class ProblemDetails:
    """
    RFC 9457 Problem Details for HTTP APIs.

    Required: type, title, status, code
    Optional: detail, instance, extensions
    """
    type: str                          # URI identifying error type
    title: str                         # Human-readable summary
    status: int                        # HTTP status code
    code: str                          # Web4 error code
    detail: Optional[str] = None       # Occurrence-specific explanation
    instance: Optional[str] = None     # URI identifying this occurrence
    extensions: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_w4error(cls, err: W4Error, detail: Optional[str] = None,
                     instance: Optional[str] = None,
                     **extensions) -> "ProblemDetails":
        """Create ProblemDetails from a W4Error enum member."""
        return cls(
            type="about:blank",
            title=err.title,
            status=err.status,
            code=err.code,
            detail=detail,
            instance=instance,
            extensions=extensions,
        )

    def to_dict(self) -> dict:
        """Serialize to dict (application/problem+json)."""
        d = {
            "type": self.type,
            "title": self.title,
            "status": self.status,
            "code": self.code,
        }
        if self.detail is not None:
            d["detail"] = self.detail
        if self.instance is not None:
            d["instance"] = self.instance
        d.update(self.extensions)
        return d

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON with application/problem+json content type."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, d: dict) -> "ProblemDetails":
        """Deserialize from dict."""
        known = {"type", "title", "status", "code", "detail", "instance"}
        extensions = {k: v for k, v in d.items() if k not in known}
        return cls(
            type=d["type"],
            title=d["title"],
            status=d["status"],
            code=d["code"],
            detail=d.get("detail"),
            instance=d.get("instance"),
            extensions=extensions,
        )

    @classmethod
    def from_json(cls, s: str) -> "ProblemDetails":
        return cls.from_dict(json.loads(s))

    @property
    def content_type(self) -> str:
        return "application/problem+json"

    def is_retryable(self) -> bool:
        """Whether this error suggests a retry might succeed."""
        return self.status in (408, 429, 503)

    def is_client_error(self) -> bool:
        return 400 <= self.status < 500

    def is_server_error(self) -> bool:
        return 500 <= self.status < 600


# ═══════════════════════════════════════════════════════════════
# Typed Exception Hierarchy
# ═══════════════════════════════════════════════════════════════

class Web4Exception(Exception):
    """Base Web4 exception with ProblemDetails attached."""

    def __init__(self, problem: ProblemDetails):
        self.problem = problem
        super().__init__(f"[{problem.code}] {problem.title}: {problem.detail or ''}")

    @classmethod
    def from_error(cls, err: W4Error, detail: Optional[str] = None,
                   instance: Optional[str] = None, **ext) -> "Web4Exception":
        problem = ProblemDetails.from_w4error(err, detail, instance, **ext)
        return cls(problem)

    def to_response(self) -> dict:
        """Convert to HTTP response dict."""
        return {
            "status_code": self.problem.status,
            "content_type": self.problem.content_type,
            "body": self.problem.to_dict(),
        }


class BindingError(Web4Exception):
    """Binding-related errors."""
    pass

class PairingError(Web4Exception):
    """Pairing-related errors."""
    pass

class WitnessError(Web4Exception):
    """Witness-related errors."""
    pass

class AuthzError(Web4Exception):
    """Authorization-related errors."""
    pass

class CryptoError(Web4Exception):
    """Cryptographic errors."""
    pass

class ProtocolError(Web4Exception):
    """Protocol-level errors."""
    pass


# Category → exception class mapping
_CATEGORY_EXCEPTIONS = {
    "BINDING": BindingError,
    "PAIRING": PairingError,
    "WITNESS": WitnessError,
    "AUTHZ": AuthzError,
    "CRYPTO": CryptoError,
    "PROTO": ProtocolError,
}


# ═══════════════════════════════════════════════════════════════
# Factory Functions
# ═══════════════════════════════════════════════════════════════

def error(err: W4Error, detail: Optional[str] = None,
          instance: Optional[str] = None, **ext) -> ProblemDetails:
    """Quick factory for ProblemDetails."""
    return ProblemDetails.from_w4error(err, detail, instance, **ext)


def raise_w4(err: W4Error, detail: Optional[str] = None,
             instance: Optional[str] = None, **ext):
    """Raise typed Web4 exception."""
    problem = ProblemDetails.from_w4error(err, detail, instance, **ext)
    exc_class = _CATEGORY_EXCEPTIONS.get(err.category, Web4Exception)
    raise exc_class(problem)


# ═══════════════════════════════════════════════════════════════
# Error Context Manager
# ═══════════════════════════════════════════════════════════════

class ErrorContext:
    """
    Context manager for wrapping operations with Web4 error handling.

    Usage:
        with ErrorContext("handshake", w4id="w4id:key:alice") as ctx:
            # ... operations that might fail ...
            if suite_mismatch:
                ctx.fail(W4Error.CRYPTO_SUITE, "No common suite")

    On exception, produces structured ProblemDetails.
    """

    def __init__(self, operation: str, **context):
        self.operation = operation
        self.context = context
        self.errors: List[ProblemDetails] = []
        self._failed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, Web4Exception):
            self.errors.append(exc_val.problem)
            return True  # suppress — already structured
        if exc_type is not None:
            # Wrap unexpected exceptions as protocol errors
            problem = error(
                W4Error.PROTO_SEQUENCE,
                detail=f"Unexpected error in {self.operation}: {exc_val}",
                operation=self.operation,
                **self.context,
            )
            self.errors.append(problem)
            return True  # suppress
        return False

    def fail(self, err: W4Error, detail: Optional[str] = None, **ext):
        """Record a failure and raise typed exception."""
        raise_w4(err, detail, **ext, **self.context)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


# ═══════════════════════════════════════════════════════════════
# Error Aggregator
# ═══════════════════════════════════════════════════════════════

class ErrorLog:
    """Accumulate and analyze errors across operations."""

    def __init__(self):
        self.entries: List[Dict[str, Any]] = []

    def record(self, problem: ProblemDetails, source: str = ""):
        self.entries.append({
            "ts": time.time(),
            "source": source,
            "code": problem.code,
            "status": problem.status,
            "detail": problem.detail,
            "retryable": problem.is_retryable(),
        })

    def by_category(self) -> Dict[str, int]:
        """Count errors by category."""
        counts: Dict[str, int] = {}
        for e in self.entries:
            cat = e["code"].split("_")[2]
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def by_status(self) -> Dict[int, int]:
        """Count errors by HTTP status."""
        counts: Dict[int, int] = {}
        for e in self.entries:
            counts[e["status"]] = counts.get(e["status"], 0) + 1
        return counts

    def retryable_count(self) -> int:
        return sum(1 for e in self.entries if e["retryable"])

    def summary(self) -> dict:
        return {
            "total": len(self.entries),
            "by_category": self.by_category(),
            "by_status": self.by_status(),
            "retryable": self.retryable_count(),
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

    # ── T1: Error Code Registry ──
    print("\n═══ T1: Error Code Registry ═══")
    check("T1: 24 error codes defined", len(W4Error) == 24)

    # Category counts
    cats = {}
    for e in W4Error:
        cats[e.category] = cats.get(e.category, 0) + 1
    check("T1: 6 categories", len(cats) == 6)
    check("T1: 4 binding errors", cats.get("BINDING") == 4)
    check("T1: 4 pairing errors", cats.get("PAIRING") == 4)
    check("T1: 4 witness errors", cats.get("WITNESS") == 4)
    check("T1: 4 authz errors", cats.get("AUTHZ") == 4)
    check("T1: 4 crypto errors", cats.get("CRYPTO") == 4)
    check("T1: 4 protocol errors", cats.get("PROTO") == 4)

    # Lookup
    e = W4Error.from_code("W4_ERR_AUTHZ_DENIED")
    check("T1: from_code lookup", e == W4Error.AUTHZ_DENIED)
    check("T1: Status = 401", e.status == 401)
    check("T1: Title correct", e.title == "Authorization Denied")

    # By category
    binding_errors = W4Error.by_category("BINDING")
    check("T1: by_category returns 4", len(binding_errors) == 4)

    # By status
    status_400 = W4Error.by_status(400)
    check("T1: Multiple 400 errors", len(status_400) >= 8,
          f"count={len(status_400)}")

    # ── T2: ProblemDetails ──
    print("\n═══ T2: ProblemDetails ═══")
    pd = error(W4Error.AUTHZ_DENIED,
               detail="Credential lacks scope write:lct",
               instance="web4://w4idp-ABCD/messages/123")
    check("T2: Type is about:blank", pd.type == "about:blank")
    check("T2: Title from enum", pd.title == "Authorization Denied")
    check("T2: Status = 401", pd.status == 401)
    check("T2: Code correct", pd.code == "W4_ERR_AUTHZ_DENIED")
    check("T2: Detail set", pd.detail == "Credential lacks scope write:lct")
    check("T2: Instance set", pd.instance == "web4://w4idp-ABCD/messages/123")
    check("T2: Content type", pd.content_type == "application/problem+json")
    check("T2: Is client error", pd.is_client_error())
    check("T2: Not retryable", not pd.is_retryable())

    # ── T3: Serialization ──
    print("\n═══ T3: Serialization ═══")
    d = pd.to_dict()
    check("T3: to_dict has required fields",
          all(k in d for k in ["type", "title", "status", "code"]))
    check("T3: to_dict has optional detail", "detail" in d)

    json_str = pd.to_json()
    check("T3: Valid JSON", json.loads(json_str) is not None)

    pd_back = ProblemDetails.from_json(json_str)
    check("T3: Roundtrip preserves code", pd_back.code == pd.code)
    check("T3: Roundtrip preserves detail", pd_back.detail == pd.detail)
    check("T3: Roundtrip preserves status", pd_back.status == pd.status)
    check("T3: Roundtrip preserves instance", pd_back.instance == pd.instance)

    # ── T4: Extensions ──
    print("\n═══ T4: Extensions ═══")
    pd_ext = error(W4Error.AUTHZ_RATE,
                   detail="Request rate 5001/min exceeds limit 5000/min",
                   limit=5000, current=5001, retry_after=60)
    d = pd_ext.to_dict()
    check("T4: Extension 'limit' in dict", d.get("limit") == 5000)
    check("T4: Extension 'current' in dict", d.get("current") == 5001)
    check("T4: Extension 'retry_after' in dict", d.get("retry_after") == 60)
    check("T4: Status = 429", pd_ext.status == 429)
    check("T4: Is retryable", pd_ext.is_retryable())

    # Roundtrip with extensions
    pd_ext_back = ProblemDetails.from_json(pd_ext.to_json())
    check("T4: Extensions survive roundtrip",
          pd_ext_back.extensions.get("limit") == 5000)

    # ── T5: Typed Exceptions ──
    print("\n═══ T5: Typed Exceptions ═══")
    try:
        raise_w4(W4Error.BINDING_EXISTS, "Entity already bound to device-12345")
    except BindingError as e:
        check("T5: BindingError raised", True)
        check("T5: Has problem details", e.problem.code == "W4_ERR_BINDING_EXISTS")
        check("T5: Has detail", "device-12345" in str(e))

    try:
        raise_w4(W4Error.CRYPTO_VERIFY, "Ed25519 signature invalid")
    except CryptoError as e:
        check("T5: CryptoError raised", True)
        check("T5: Status = 401", e.problem.status == 401)

    try:
        raise_w4(W4Error.WITNESS_QUORUM, "Only 2 of 3 required witnesses")
    except WitnessError as e:
        check("T5: WitnessError raised", True)
        resp = e.to_response()
        check("T5: Response has status_code", resp["status_code"] == 409)
        check("T5: Response has content_type",
              resp["content_type"] == "application/problem+json")

    # ── T6: ErrorContext ──
    print("\n═══ T6: ErrorContext ═══")
    # Successful operation
    with ErrorContext("test-success") as ctx:
        pass
    check("T6: Successful context is ok", ctx.ok)
    check("T6: No errors recorded", len(ctx.errors) == 0)

    # Failed operation
    with ErrorContext("handshake", w4id="w4id:key:alice") as ctx:
        ctx.fail(W4Error.CRYPTO_SUITE, "No common cryptographic suite")
    check("T6: Failed context has error", not ctx.ok)
    check("T6: Error recorded", len(ctx.errors) == 1)
    check("T6: Error has context",
          ctx.errors[0].extensions.get("w4id") == "w4id:key:alice")

    # Unexpected exception wrapped
    with ErrorContext("unexpected") as ctx:
        raise ValueError("something broke")
    check("T6: Unexpected error wrapped", not ctx.ok)
    check("T6: Wrapped as PROTO_SEQUENCE", ctx.errors[0].code == "W4_ERR_PROTO_SEQUENCE")
    check("T6: Detail includes original message",
          "something broke" in ctx.errors[0].detail)

    # ── T7: ErrorLog ──
    print("\n═══ T7: ErrorLog ═══")
    log = ErrorLog()
    log.record(error(W4Error.AUTHZ_DENIED, "no scope"), "handshake")
    log.record(error(W4Error.AUTHZ_RATE, "rate exceeded"), "api")
    log.record(error(W4Error.WITNESS_UNAVAIL, "witness down"), "attestation")
    log.record(error(W4Error.BINDING_INVALID, "bad format"), "binding")
    log.record(error(W4Error.PAIRING_TIMEOUT, "timed out"), "pairing")

    s = log.summary()
    check("T7: Total = 5", s["total"] == 5)
    check("T7: 2 AUTHZ errors", s["by_category"].get("AUTHZ") == 2)
    check("T7: 1 WITNESS error", s["by_category"].get("WITNESS") == 1)
    check("T7: 3 retryable (429 + 503 + 408)", s["retryable"] == 3)
    check("T7: Status 401 counted", s["by_status"].get(401) == 1)

    # ── T8: All Status Codes ──
    print("\n═══ T8: HTTP Status Code Coverage ═══")
    expected_statuses = {400, 401, 403, 408, 409, 410, 429, 503}
    actual_statuses = {e.status for e in W4Error}
    check("T8: All 8 HTTP statuses covered",
          actual_statuses == expected_statuses,
          f"expected={expected_statuses}, actual={actual_statuses}")

    # Retryable classification
    for e in W4Error:
        pd = error(e)
        if pd.status in (408, 429, 503):
            check(f"T8: {e.code} is retryable", pd.is_retryable())
        else:
            check(f"T8: {e.code} is not retryable", not pd.is_retryable())

    # ── T9: Spec Examples ──
    print("\n═══ T9: Spec Examples ═══")
    # Example 3.1 from errors.md
    ex1 = error(W4Error.AUTHZ_DENIED,
                detail="Credential lacks scope write:lct",
                instance="web4://w4idp-ABCD/messages/123")
    d1 = ex1.to_dict()
    check("T9: Example 3.1 matches spec",
          d1["code"] == "W4_ERR_AUTHZ_DENIED" and d1["status"] == 401)

    # Example 3.2 from errors.md
    ex2 = error(W4Error.WITNESS_QUORUM,
                detail="Only 2 of 3 required witnesses responded",
                instance="web4://w4idp-EFGH/attestations/456")
    d2 = ex2.to_dict()
    check("T9: Example 3.2 matches spec",
          d2["code"] == "W4_ERR_WITNESS_QUORUM" and d2["status"] == 409)

    # Example 3.3 from errors.md
    ex3 = error(W4Error.AUTHZ_RATE,
                detail="Request rate 5001/min exceeds limit 5000/min",
                instance="web4://w4idp-IJKL/api/v1/query")
    d3 = ex3.to_dict()
    check("T9: Example 3.3 matches spec",
          d3["code"] == "W4_ERR_AUTHZ_RATE" and d3["status"] == 429)

    # ── T10: Exception Hierarchy ──
    print("\n═══ T10: Exception Hierarchy ═══")
    # All typed exceptions are Web4Exception subclasses
    for cat, exc_cls in _CATEGORY_EXCEPTIONS.items():
        check(f"T10: {exc_cls.__name__} is Web4Exception subclass",
              issubclass(exc_cls, Web4Exception))

    # Generic catch
    try:
        raise_w4(W4Error.PAIRING_DENIED, "entity refused")
    except Web4Exception as e:
        check("T10: Caught via base class", True)
        check("T10: Has correct type", isinstance(e, PairingError))

    # ── T11: Unknown Code Handling ──
    print("\n═══ T11: Edge Cases ═══")
    try:
        W4Error.from_code("W4_ERR_NONEXISTENT")
        check("T11: Unknown code raises ValueError", False)
    except ValueError:
        check("T11: Unknown code raises ValueError", True)

    # ProblemDetails with no optional fields
    pd_min = ProblemDetails(
        type="about:blank", title="Test", status=400, code="W4_ERR_TEST"
    )
    d = pd_min.to_dict()
    check("T11: Minimal ProblemDetails serializes", "detail" not in d)
    check("T11: Minimal has required fields", d["code"] == "W4_ERR_TEST")

    # Server error classification
    pd_503 = error(W4Error.WITNESS_UNAVAIL)
    check("T11: 503 is server error", pd_503.is_server_error())
    check("T11: 503 is not client error", not pd_503.is_client_error())

    # ═══ Summary ═══
    total = passed + failed
    print(f"\n{'='*60}")
    print(f"  Web4 Error Handler — Track N Results")
    print(f"  {passed} passed, {failed} failed out of {total} checks")
    print(f"{'='*60}")

    if failed == 0:
        print(f"\n  All {total} checks pass — RFC 9457 error handling operational")
        print(f"  24 error codes across 6 categories")
        print(f"  Typed exceptions: Binding/Pairing/Witness/Authz/Crypto/Protocol")
    else:
        print(f"\n  {failed} failures need investigation")

    return passed, failed


if __name__ == "__main__":
    passed, failed = run_tests()
    sys.exit(0 if failed == 0 else 1)
