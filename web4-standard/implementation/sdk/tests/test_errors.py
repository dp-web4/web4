"""
Tests for web4.errors — error taxonomy, RFC 9457 serialization.

Tests cover:
1. Registry completeness (all 24 codes, 6 categories)
2. Error code metadata (title, status, description)
3. Web4Error construction and fields
4. Category subclass dispatch
5. RFC 9457 Problem Details serialization round-trips
6. make_error convenience constructor
7. Test vector validation
"""

import json
import os

import pytest

from web4.errors import (
    ErrorCategory, ErrorCode, ErrorMeta,
    Web4Error, BindingError, PairingError, WitnessError,
    AuthzError, CryptoError, ProtoError,
    get_error_meta, codes_for_category, make_error,
)


# ── Registry Completeness ────────────────────────────────────────

class TestRegistryCompleteness:
    """Every ErrorCode must have metadata in the registry."""

    def test_all_24_codes_registered(self):
        for code in ErrorCode:
            meta = get_error_meta(code)
            assert meta.code == code

    def test_exactly_24_codes(self):
        assert len(ErrorCode) == 24

    def test_exactly_6_categories(self):
        assert len(ErrorCategory) == 6

    def test_4_codes_per_category(self):
        for cat in ErrorCategory:
            codes = codes_for_category(cat)
            assert len(codes) == 4, f"{cat} has {len(codes)} codes, expected 4"

    def test_all_codes_have_title(self):
        for code in ErrorCode:
            meta = get_error_meta(code)
            assert len(meta.title) > 0

    def test_all_codes_have_valid_status(self):
        for code in ErrorCode:
            meta = get_error_meta(code)
            assert 100 <= meta.status <= 599


# ── Error Code Metadata ──────────────────────────────────────────

class TestErrorMetadata:
    """Spot-check specific error codes against the spec."""

    def test_binding_exists(self):
        meta = get_error_meta(ErrorCode.BINDING_EXISTS)
        assert meta.category == ErrorCategory.BINDING
        assert meta.title == "Binding Already Exists"
        assert meta.status == 409

    def test_pairing_timeout(self):
        meta = get_error_meta(ErrorCode.PAIRING_TIMEOUT)
        assert meta.category == ErrorCategory.PAIRING
        assert meta.title == "Pairing Timeout"
        assert meta.status == 408

    def test_witness_quorum(self):
        meta = get_error_meta(ErrorCode.WITNESS_QUORUM)
        assert meta.category == ErrorCategory.WITNESS
        assert meta.title == "Quorum Not Met"
        assert meta.status == 409

    def test_authz_rate(self):
        meta = get_error_meta(ErrorCode.AUTHZ_RATE)
        assert meta.category == ErrorCategory.AUTHZ
        assert meta.title == "Rate Limit Exceeded"
        assert meta.status == 429

    def test_crypto_verify(self):
        meta = get_error_meta(ErrorCode.CRYPTO_VERIFY)
        assert meta.category == ErrorCategory.CRYPTO
        assert meta.title == "Verification Failed"
        assert meta.status == 401

    def test_proto_replay(self):
        meta = get_error_meta(ErrorCode.PROTO_REPLAY)
        assert meta.category == ErrorCategory.PROTO
        assert meta.title == "Replay Detected"
        assert meta.status == 409


# ── Web4Error Construction ────────────────────────────────────────

class TestWeb4Error:
    """Web4Error base class with RFC 9457 fields."""

    def test_is_exception(self):
        err = Web4Error(ErrorCode.AUTHZ_DENIED)
        assert isinstance(err, Exception)

    def test_default_detail_from_spec(self):
        err = Web4Error(ErrorCode.AUTHZ_DENIED)
        assert err.detail == "Credential lacks required capability"

    def test_custom_detail(self):
        err = Web4Error(ErrorCode.AUTHZ_DENIED, detail="Missing scope: write:lct")
        assert err.detail == "Missing scope: write:lct"

    def test_instance_field(self):
        err = Web4Error(
            ErrorCode.AUTHZ_DENIED,
            instance="web4://w4idp-ABCD/messages/123",
        )
        assert err.instance == "web4://w4idp-ABCD/messages/123"

    def test_fields_populated_from_registry(self):
        err = Web4Error(ErrorCode.BINDING_EXISTS)
        assert err.code == ErrorCode.BINDING_EXISTS
        assert err.category == ErrorCategory.BINDING
        assert err.title == "Binding Already Exists"
        assert err.status == 409
        assert err.error_type == "about:blank"

    def test_str_is_detail(self):
        err = Web4Error(ErrorCode.AUTHZ_DENIED, detail="test message")
        assert str(err) == "test message"

    def test_raise_and_catch(self):
        with pytest.raises(Web4Error) as exc_info:
            raise Web4Error(ErrorCode.PROTO_REPLAY, detail="duplicate nonce")
        assert exc_info.value.code == ErrorCode.PROTO_REPLAY
        assert exc_info.value.status == 409


# ── Category Subclasses ───────────────────────────────────────────

class TestCategorySubclasses:
    """Each category has a subclass of Web4Error."""

    @pytest.mark.parametrize("cls,code", [
        (BindingError, ErrorCode.BINDING_EXISTS),
        (PairingError, ErrorCode.PAIRING_DENIED),
        (WitnessError, ErrorCode.WITNESS_UNAVAIL),
        (AuthzError, ErrorCode.AUTHZ_DENIED),
        (CryptoError, ErrorCode.CRYPTO_SUITE),
        (ProtoError, ErrorCode.PROTO_VERSION),
    ])
    def test_subclass_is_web4error(self, cls, code):
        err = cls(code)
        assert isinstance(err, Web4Error)
        assert isinstance(err, cls)

    def test_catch_by_category(self):
        with pytest.raises(BindingError):
            raise BindingError(ErrorCode.BINDING_REVOKED)

    def test_catch_by_base(self):
        with pytest.raises(Web4Error):
            raise CryptoError(ErrorCode.CRYPTO_KEY)


# ── RFC 9457 Serialization ────────────────────────────────────────

class TestSerialization:
    """to_problem_json / from_problem_json round-trip."""

    def test_to_problem_json_required_fields(self):
        err = Web4Error(ErrorCode.AUTHZ_DENIED)
        pj = err.to_problem_json()
        assert pj["type"] == "about:blank"
        assert pj["title"] == "Authorization Denied"
        assert pj["status"] == 401
        assert pj["code"] == "W4_ERR_AUTHZ_DENIED"

    def test_to_problem_json_with_detail(self):
        err = Web4Error(ErrorCode.AUTHZ_DENIED, detail="Missing scope: write:lct")
        pj = err.to_problem_json()
        assert pj["detail"] == "Missing scope: write:lct"

    def test_to_problem_json_with_instance(self):
        err = Web4Error(
            ErrorCode.WITNESS_QUORUM,
            detail="Only 2 of 3 required witnesses responded",
            instance="web4://w4idp-EFGH/attestations/456",
        )
        pj = err.to_problem_json()
        assert pj["instance"] == "web4://w4idp-EFGH/attestations/456"

    def test_to_problem_json_omits_none_fields(self):
        err = Web4Error(ErrorCode.PROTO_VERSION)
        pj = err.to_problem_json()
        assert "instance" not in pj

    def test_round_trip(self):
        original = Web4Error(
            ErrorCode.AUTHZ_RATE,
            detail="Request rate 5001/min exceeds limit 5000/min",
            instance="web4://w4idp-IJKL/api/v1/query",
        )
        pj = original.to_problem_json()
        restored = Web4Error.from_problem_json(pj)
        assert restored.code == original.code
        assert restored.status == original.status
        assert restored.title == original.title
        assert restored.detail == original.detail
        assert restored.instance == original.instance

    def test_round_trip_preserves_subclass(self):
        original = BindingError(ErrorCode.BINDING_EXISTS)
        pj = original.to_problem_json()
        restored = Web4Error.from_problem_json(pj)
        assert isinstance(restored, BindingError)

    def test_to_json_string(self):
        err = Web4Error(ErrorCode.AUTHZ_DENIED)
        j = err.to_json()
        data = json.loads(j)
        assert data["code"] == "W4_ERR_AUTHZ_DENIED"

    def test_from_problem_json_unknown_code_raises(self):
        with pytest.raises(ValueError):
            Web4Error.from_problem_json({"code": "W4_ERR_UNKNOWN_FAKE"})


# ── make_error Convenience ────────────────────────────────────────

class TestMakeError:
    """make_error returns the right subclass."""

    def test_returns_binding_error(self):
        err = make_error(ErrorCode.BINDING_INVALID)
        assert isinstance(err, BindingError)

    def test_returns_authz_error(self):
        err = make_error(ErrorCode.AUTHZ_SCOPE, detail="Need admin scope")
        assert isinstance(err, AuthzError)
        assert err.detail == "Need admin scope"

    def test_returns_proto_error_with_instance(self):
        err = make_error(
            ErrorCode.PROTO_DOWNGRADE,
            instance="web4://node-1/handshake/99",
        )
        assert isinstance(err, ProtoError)
        assert err.instance == "web4://node-1/handshake/99"


# ── Test Vectors ──────────────────────────────────────────────────

VECTORS_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "test-vectors", "errors",
)


class TestVectors:
    """Cross-language test vector validation."""

    @pytest.fixture
    def vectors(self):
        path = os.path.join(VECTORS_DIR, "error-taxonomy.json")
        with open(path) as f:
            return json.load(f)

    def test_vector_count(self, vectors):
        assert len(vectors["vectors"]) == 5

    def test_all_vectors_round_trip(self, vectors):
        for v in vectors["vectors"]:
            problem = v["problem_json"]
            err = Web4Error.from_problem_json(problem)
            assert err.code.value == problem["code"]
            assert err.status == problem["status"]
            assert err.title == problem["title"]
            rt = err.to_problem_json()
            assert rt["code"] == problem["code"]
            assert rt["status"] == problem["status"]

    def test_vector_categories(self, vectors):
        for v in vectors["vectors"]:
            code = ErrorCode(v["problem_json"]["code"])
            meta = get_error_meta(code)
            assert meta.category.value == v["expected_category"]

    def test_vector_subclasses(self, vectors):
        for v in vectors["vectors"]:
            err = Web4Error.from_problem_json(v["problem_json"])
            expected_cls = v["expected_subclass"]
            assert type(err).__name__ == expected_cls
