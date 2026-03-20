"""
Cross-language LCT JSON-LD test vectors.

Validates LCT JSON-LD roundtrip fidelity: from_jsonld(doc) -> to_jsonld() should
reproduce the original document. These vectors define the canonical JSON-LD output
that all language implementations must match.

Test vectors: web4-standard/test-vectors/lct/lct-jsonld-vectors.json
Spec reference: web4-standard/core-spec/LCT-linked-context-token.md §2.3
"""

import json
import os

import pytest

from web4.lct import LCT, LCT_JSONLD_CONTEXT

VECTORS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "test-vectors"
)


def load_vectors():
    path = os.path.join(VECTORS_DIR, "lct", "lct-jsonld-vectors.json")
    with open(path) as f:
        data = json.load(f)
    return data["vectors"], data["meta"].get("tolerance", 1e-10)


VECTORS, TOLERANCE = load_vectors()
VECTOR_IDS = [v["id"] for v in VECTORS]


def _approx_equal(a, b, tol):
    """Compare values with tolerance for floats."""
    if isinstance(a, float) and isinstance(b, float):
        return abs(a - b) < tol
    return a == b


def _deep_compare(expected, actual, tol, path=""):
    """Deep comparison with float tolerance."""
    if isinstance(expected, dict) and isinstance(actual, dict):
        assert set(expected.keys()) == set(actual.keys()), (
            f"Key mismatch at {path}: expected {sorted(expected.keys())}, "
            f"got {sorted(actual.keys())}"
        )
        for key in expected:
            _deep_compare(expected[key], actual[key], tol, f"{path}.{key}")
    elif isinstance(expected, list) and isinstance(actual, list):
        assert len(expected) == len(actual), (
            f"Length mismatch at {path}: expected {len(expected)}, got {len(actual)}"
        )
        for i, (e, a) in enumerate(zip(expected, actual)):
            _deep_compare(e, a, tol, f"{path}[{i}]")
    elif isinstance(expected, float) or isinstance(actual, float):
        assert _approx_equal(expected, actual, tol), (
            f"Float mismatch at {path}: expected {expected}, got {actual}"
        )
    else:
        assert expected == actual, (
            f"Value mismatch at {path}: expected {expected!r}, got {actual!r}"
        )


# ── Roundtrip Tests ──────────────────────────────────────────────


class TestLCTJsonLDRoundtrip:
    """Verify from_jsonld -> to_jsonld reproduces the vector document."""

    @pytest.mark.parametrize("vec_id", VECTOR_IDS)
    def test_roundtrip(self, vec_id):
        vec = next(v for v in VECTORS if v["id"] == vec_id)
        doc = vec["jsonld"]

        # Parse the JSON-LD document
        lct = LCT.from_jsonld(doc)

        # Re-serialize
        roundtripped = lct.to_jsonld()

        # Compare with tolerance
        _deep_compare(doc, roundtripped, TOLERANCE)


# ── Structure Tests ──────────────────────────────────────────────


class TestLCTJsonLDStructure:
    """Verify JSON-LD structural requirements per spec §2.3."""

    @pytest.mark.parametrize("vec_id", VECTOR_IDS)
    def test_context_header(self, vec_id):
        """Every JSON-LD document must have @context."""
        doc = next(v for v in VECTORS if v["id"] == vec_id)["jsonld"]
        assert "@context" in doc
        assert LCT_JSONLD_CONTEXT in doc["@context"]

    @pytest.mark.parametrize("vec_id", VECTOR_IDS)
    def test_required_fields(self, vec_id):
        """Every JSON-LD document must have lct_id, subject, binding, mrh, policy, t3_tensor, v3_tensor, revocation."""
        doc = next(v for v in VECTORS if v["id"] == vec_id)["jsonld"]
        for field in ["lct_id", "subject", "binding", "mrh", "policy",
                       "t3_tensor", "v3_tensor", "revocation"]:
            assert field in doc, f"Missing required field: {field}"

    @pytest.mark.parametrize("vec_id", VECTOR_IDS)
    def test_binding_structure(self, vec_id):
        """Binding must have entity_type, public_key, created_at, binding_proof."""
        doc = next(v for v in VECTORS if v["id"] == vec_id)["jsonld"]
        binding = doc["binding"]
        for field in ["entity_type", "public_key", "created_at", "binding_proof"]:
            assert field in binding, f"Missing binding field: {field}"

    @pytest.mark.parametrize("vec_id", VECTOR_IDS)
    def test_mrh_structure(self, vec_id):
        """MRH must have bound, paired, witnessing, horizon_depth, last_updated."""
        doc = next(v for v in VECTORS if v["id"] == vec_id)["jsonld"]
        mrh = doc["mrh"]
        for field in ["bound", "paired", "witnessing", "horizon_depth", "last_updated"]:
            assert field in mrh, f"Missing MRH field: {field}"

    @pytest.mark.parametrize("vec_id", VECTOR_IDS)
    def test_tensor_structure(self, vec_id):
        """T3 and V3 tensors must have all dimension fields plus composite_score."""
        doc = next(v for v in VECTORS if v["id"] == vec_id)["jsonld"]
        for field in ["talent", "training", "temperament", "composite_score"]:
            assert field in doc["t3_tensor"], f"Missing T3 field: {field}"
        for field in ["valuation", "veracity", "validity", "composite_score"]:
            assert field in doc["v3_tensor"], f"Missing V3 field: {field}"

    @pytest.mark.parametrize("vec_id", VECTOR_IDS)
    def test_revocation_structure(self, vec_id):
        """Revocation must have status, ts, reason."""
        doc = next(v for v in VECTORS if v["id"] == vec_id)["jsonld"]
        rev = doc["revocation"]
        for field in ["status", "ts", "reason"]:
            assert field in rev, f"Missing revocation field: {field}"

    @pytest.mark.parametrize("vec_id", VECTOR_IDS)
    def test_mrh_bound_structured(self, vec_id):
        """MRH bound entries must be objects with lct_id key (JSON-LD format)."""
        doc = next(v for v in VECTORS if v["id"] == vec_id)["jsonld"]
        for entry in doc["mrh"]["bound"]:
            assert isinstance(entry, dict), f"Bound entry must be dict, got {type(entry)}"
            assert "lct_id" in entry

    @pytest.mark.parametrize("vec_id", VECTOR_IDS)
    def test_mrh_witnessing_structured(self, vec_id):
        """MRH witnessing entries must be objects with lct_id key (JSON-LD format)."""
        doc = next(v for v in VECTORS if v["id"] == vec_id)["jsonld"]
        for entry in doc["mrh"]["witnessing"]:
            assert isinstance(entry, dict), f"Witnessing entry must be dict, got {type(entry)}"
            assert "lct_id" in entry


# ── Field Value Tests (specific vectors) ─────────────────────────


class TestLCTJsonLDValues:
    """Verify specific field values in individual vectors."""

    def _doc(self, vec_id):
        return next(v for v in VECTORS if v["id"] == vec_id)["jsonld"]

    def test_001_minimal_defaults(self):
        """lct-jsonld-001: Default T3/V3 values."""
        doc = self._doc("lct-jsonld-001")
        assert doc["t3_tensor"]["talent"] == 0.5
        assert doc["t3_tensor"]["training"] == 0.5
        assert doc["t3_tensor"]["temperament"] == 0.5
        assert doc["v3_tensor"]["valuation"] == 0.5
        assert doc["v3_tensor"]["veracity"] == 0.5
        assert doc["v3_tensor"]["validity"] == 0.5
        assert doc["revocation"]["status"] == "active"
        assert "attestations" not in doc
        assert "lineage" not in doc

    def test_002_full_optional_fields(self):
        """lct-jsonld-002: All optional fields present."""
        doc = self._doc("lct-jsonld-002")
        assert "hardware_anchor" in doc["binding"]
        assert doc["binding"]["hardware_anchor"] == "tpm2:sha256:abcdef1234"
        assert "genesis_block_hash" in doc["birth_certificate"]
        assert doc["birth_certificate"]["genesis_block_hash"] == "sha256:abcdef0123456789"
        assert "attestations" in doc
        assert len(doc["attestations"]) == 2
        assert "lineage" in doc
        assert len(doc["lineage"]) == 2
        assert doc["policy"]["constraints"]["max_delegation_depth"] == 3

    def test_003_revoked_fields(self):
        """lct-jsonld-003: Revocation fields populated."""
        doc = self._doc("lct-jsonld-003")
        assert doc["revocation"]["status"] == "revoked"
        assert doc["revocation"]["ts"] == "2026-02-15T12:00:00Z"
        assert doc["revocation"]["reason"] == "compromise"

    def test_004_attestation_types(self):
        """lct-jsonld-004: Three distinct attestation types."""
        doc = self._doc("lct-jsonld-004")
        types = [a["type"] for a in doc["attestations"]]
        assert types == ["time", "capability", "trust"]

    def test_005_lineage_reasons(self):
        """lct-jsonld-005: Three lineage reasons."""
        doc = self._doc("lct-jsonld-005")
        reasons = [le["reason"] for le in doc["lineage"]]
        assert reasons == ["genesis", "rotation", "upgrade"]

    def test_006_complex_mrh(self):
        """lct-jsonld-006: Multiple MRH entries."""
        doc = self._doc("lct-jsonld-006")
        assert len(doc["mrh"]["bound"]) == 2
        assert len(doc["mrh"]["paired"]) == 2
        assert len(doc["mrh"]["witnessing"]) == 2
        assert doc["mrh"]["horizon_depth"] == 7

    def test_007_boundary_tensors(self):
        """lct-jsonld-007: T3/V3 with 0.0 and 1.0 extremes."""
        doc = self._doc("lct-jsonld-007")
        assert doc["t3_tensor"]["talent"] == 0.0
        assert doc["t3_tensor"]["training"] == 1.0
        assert doc["v3_tensor"]["valuation"] == 1.0
        assert doc["v3_tensor"]["veracity"] == 0.0

    def test_008_suspended_status(self):
        """lct-jsonld-008: Suspended (third revocation state)."""
        doc = self._doc("lct-jsonld-008")
        assert doc["revocation"]["status"] == "suspended"
        assert doc["revocation"]["reason"] == "investigation"

    def test_009_genesis_block_hash(self):
        """lct-jsonld-009: Birth certificate with genesis_block_hash."""
        doc = self._doc("lct-jsonld-009")
        assert "genesis_block_hash" in doc["birth_certificate"]
        assert doc["birth_certificate"]["genesis_block_hash"].startswith("sha256:")

    def test_010_no_birth_certificate(self):
        """lct-jsonld-010: LCT without birth certificate."""
        doc = self._doc("lct-jsonld-010")
        assert "birth_certificate" not in doc


# ── JSON-LD Spec Compliance ──────────────────────────────────────


class TestLCTJsonLDSpecCompliance:
    """Verify spec §2.3 JSON-LD specific requirements."""

    def test_birth_context_not_context(self):
        """JSON-LD uses 'birth_context' not 'context' in birth certificate."""
        for vec in VECTORS:
            doc = vec["jsonld"]
            if "birth_certificate" in doc:
                assert "birth_context" in doc["birth_certificate"], (
                    f"{vec['id']}: birth_certificate uses 'context' instead of 'birth_context'"
                )

    def test_optional_sections_absent_when_empty(self):
        """Attestations and lineage absent when not populated."""
        # Vector 001 (minimal) should not have attestations or lineage
        doc = next(v for v in VECTORS if v["id"] == "lct-jsonld-001")["jsonld"]
        assert "attestations" not in doc
        assert "lineage" not in doc

    def test_optional_sections_present_when_populated(self):
        """Attestations and lineage present when populated."""
        doc = next(v for v in VECTORS if v["id"] == "lct-jsonld-002")["jsonld"]
        assert "attestations" in doc
        assert "lineage" in doc

    def test_hardware_anchor_absent_when_none(self):
        """hardware_anchor omitted when not set."""
        doc = next(v for v in VECTORS if v["id"] == "lct-jsonld-001")["jsonld"]
        assert "hardware_anchor" not in doc["binding"]

    def test_hardware_anchor_present_when_set(self):
        """hardware_anchor included when set."""
        doc = next(v for v in VECTORS if v["id"] == "lct-jsonld-002")["jsonld"]
        assert "hardware_anchor" in doc["binding"]

    def test_genesis_block_hash_absent_when_none(self):
        """genesis_block_hash omitted when not set."""
        doc = next(v for v in VECTORS if v["id"] == "lct-jsonld-001")["jsonld"]
        assert "genesis_block_hash" not in doc["birth_certificate"]

    def test_entity_types_valid(self):
        """All entity_type values are valid LCT entity types."""
        valid_types = {
            "human", "ai", "society", "organization", "role", "task",
            "resource", "device", "service", "oracle", "accumulator",
            "dictionary", "hybrid", "policy", "infrastructure",
        }
        for vec in VECTORS:
            et = vec["jsonld"]["binding"]["entity_type"]
            assert et in valid_types, f"{vec['id']}: invalid entity_type '{et}'"

    def test_revocation_status_valid(self):
        """All revocation status values are valid."""
        valid_statuses = {"active", "revoked", "suspended"}
        for vec in VECTORS:
            status = vec["jsonld"]["revocation"]["status"]
            assert status in valid_statuses, f"{vec['id']}: invalid status '{status}'"


# ── From-Dict Compatibility ──────────────────────────────────────


class TestLCTJsonLDFromDictCompat:
    """Verify from_jsonld accepts both JSON-LD and SDK internal format."""

    def test_from_jsonld_accepts_jsonld(self):
        """from_jsonld works with @context-bearing JSON-LD documents."""
        doc = next(v for v in VECTORS if v["id"] == "lct-jsonld-001")["jsonld"]
        lct = LCT.from_jsonld(doc)
        assert lct.lct_id == doc["lct_id"]

    def test_from_jsonld_accepts_sdk_format(self):
        """from_jsonld works with SDK internal format (no @context, uses 'context' not 'birth_context')."""
        lct = LCT.from_jsonld({
            "lct_id": "lct:test:compat",
            "subject": "did:test:compat",
            "binding": {
                "entity_type": "ai",
                "public_key": "testkey",
                "created_at": "2026-01-01T00:00:00Z",
            },
            "birth_certificate": {
                "issuing_society": "lct:web4:society-genesis",
                "citizen_role": "lct:web4:role:citizen:platform",
                "birth_timestamp": "2026-01-01T00:00:00Z",
                "context": "platform",  # SDK format uses "context"
            },
        })
        assert lct.birth_certificate.context == "platform"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
