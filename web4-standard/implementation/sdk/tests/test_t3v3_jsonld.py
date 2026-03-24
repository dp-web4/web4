"""
Tests for T3/V3 JSON-LD serialization (Sprint 4, V2).

Validates:
- to_jsonld() produces ontology-aligned JSON-LD documents
- from_jsonld() roundtrips correctly (composite recomputed, not stored)
- JSON Schema validation of all output formats
- Entity/role binding optional fields
- Boundary values (0.0, 1.0, defaults)
- Negative cases: schema rejects malformed documents
"""

import json
import os
import pytest

from web4.trust import T3, V3, T3_JSONLD_CONTEXT, V3_JSONLD_CONTEXT

# Conditional import for JSON Schema validation
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..",
    "schemas", "t3v3-jsonld.schema.json"
)


@pytest.fixture
def t3v3_schema():
    """Load the T3/V3 JSON-LD schema."""
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def validate(doc, schema):
    """Validate a document against the schema."""
    jsonschema.validate(doc, schema)


# ── T3 JSON-LD Serialization ──────────────────────────────────────


class TestT3ToJsonld:
    """T3.to_jsonld() output validation."""

    def test_default_t3_structure(self):
        """Default T3 produces valid JSON-LD structure."""
        t3 = T3()
        doc = t3.to_jsonld()

        assert doc["@context"] == [T3_JSONLD_CONTEXT]
        assert doc["@type"] == "T3Tensor"
        assert doc["talent"] == 0.5
        assert doc["training"] == 0.5
        assert doc["temperament"] == 0.5
        assert "composite_score" in doc
        assert "dimension_scores" in doc

    def test_custom_t3_values(self):
        """Custom T3 values serialize correctly."""
        t3 = T3(talent=0.9, training=0.8, temperament=0.7)
        doc = t3.to_jsonld()

        assert doc["talent"] == 0.9
        assert doc["training"] == 0.8
        assert doc["temperament"] == 0.7

    def test_composite_score_computed(self):
        """composite_score matches T3.composite property."""
        t3 = T3(talent=0.9, training=0.8, temperament=0.7)
        doc = t3.to_jsonld()
        expected = 0.9 * 0.4 + 0.8 * 0.3 + 0.7 * 0.3
        assert abs(doc["composite_score"] - expected) < 1e-10

    def test_dimension_scores_array(self):
        """dimension_scores array contains 3 root T3 dimensions."""
        t3 = T3(talent=0.9, training=0.8, temperament=0.7)
        doc = t3.to_jsonld()
        scores = doc["dimension_scores"]

        assert len(scores) == 3
        dims = {s["dimension"]: s["score"] for s in scores}
        assert dims["web4:Talent"] == 0.9
        assert dims["web4:Training"] == 0.8
        assert dims["web4:Temperament"] == 0.7

    def test_entity_binding(self):
        """Entity ID included when provided."""
        t3 = T3()
        doc = t3.to_jsonld(entity="lct:web4:alice")
        assert doc["entity"] == "lct:web4:alice"

    def test_role_binding(self):
        """Role included when provided."""
        t3 = T3()
        doc = t3.to_jsonld(role="web4:Surgeon")
        assert doc["role"] == "web4:Surgeon"

    def test_entity_and_role(self):
        """Both entity and role included together."""
        t3 = T3()
        doc = t3.to_jsonld(entity="lct:web4:bob", role="web4:DataAnalyst")
        assert doc["entity"] == "lct:web4:bob"
        assert doc["role"] == "web4:DataAnalyst"

    def test_no_entity_role_by_default(self):
        """entity and role omitted when not provided."""
        doc = T3().to_jsonld()
        assert "entity" not in doc
        assert "role" not in doc

    def test_boundary_zeros(self):
        """T3 with all zeros serializes correctly."""
        t3 = T3(talent=0.0, training=0.0, temperament=0.0)
        doc = t3.to_jsonld()
        assert doc["talent"] == 0.0
        assert doc["composite_score"] == 0.0

    def test_boundary_ones(self):
        """T3 with all ones serializes correctly."""
        t3 = T3(talent=1.0, training=1.0, temperament=1.0)
        doc = t3.to_jsonld()
        assert doc["talent"] == 1.0
        assert doc["composite_score"] == 1.0

    def test_to_jsonld_string(self):
        """to_jsonld_string produces valid JSON."""
        t3 = T3(talent=0.85, training=0.9, temperament=0.75)
        s = t3.to_jsonld_string()
        parsed = json.loads(s)
        assert parsed["@type"] == "T3Tensor"
        assert parsed["talent"] == 0.85

    def test_to_jsonld_string_with_bindings(self):
        """to_jsonld_string passes kwargs through."""
        s = T3().to_jsonld_string(entity="lct:web4:test")
        parsed = json.loads(s)
        assert parsed["entity"] == "lct:web4:test"


class TestT3FromJsonld:
    """T3.from_jsonld() deserialization validation."""

    def test_roundtrip_default(self):
        """Default T3 roundtrips exactly."""
        t3 = T3()
        doc = t3.to_jsonld()
        t3_rt = T3.from_jsonld(doc)
        assert t3_rt.talent == t3.talent
        assert t3_rt.training == t3.training
        assert t3_rt.temperament == t3.temperament

    def test_roundtrip_custom(self):
        """Custom T3 roundtrips exactly."""
        t3 = T3(talent=0.95, training=0.3, temperament=0.88)
        t3_rt = T3.from_jsonld(t3.to_jsonld())
        assert t3_rt.talent == t3.talent
        assert t3_rt.training == t3.training
        assert t3_rt.temperament == t3.temperament

    def test_composite_recomputed(self):
        """composite_score is recomputed, not taken from doc."""
        t3 = T3(talent=0.9, training=0.8, temperament=0.7)
        doc = t3.to_jsonld()
        doc["composite_score"] = 0.0  # Tamper
        t3_rt = T3.from_jsonld(doc)
        assert t3_rt.composite == t3.composite  # Recomputed correctly

    def test_from_plain_dict(self):
        """from_jsonld accepts plain dict (no @context/@type)."""
        t3 = T3.from_jsonld({"talent": 0.8, "training": 0.6, "temperament": 0.9})
        assert t3.talent == 0.8
        assert t3.training == 0.6
        assert t3.temperament == 0.9

    def test_missing_fields_default(self):
        """Missing fields default to 0.5."""
        t3 = T3.from_jsonld({"talent": 0.8})
        assert t3.talent == 0.8
        assert t3.training == 0.5
        assert t3.temperament == 0.5

    def test_from_jsonld_string(self):
        """from_jsonld_string parses JSON and deserializes."""
        s = T3(talent=0.75, training=0.85, temperament=0.65).to_jsonld_string()
        t3 = T3.from_jsonld_string(s)
        assert t3.talent == 0.75
        assert t3.training == 0.85

    def test_roundtrip_boundary_zeros(self):
        """Roundtrip with all-zero T3."""
        t3 = T3(talent=0.0, training=0.0, temperament=0.0)
        t3_rt = T3.from_jsonld(t3.to_jsonld())
        assert t3_rt.talent == 0.0
        assert t3_rt.training == 0.0
        assert t3_rt.temperament == 0.0

    def test_roundtrip_boundary_ones(self):
        """Roundtrip with all-one T3."""
        t3 = T3(talent=1.0, training=1.0, temperament=1.0)
        t3_rt = T3.from_jsonld(t3.to_jsonld())
        assert t3_rt.talent == 1.0


# ── V3 JSON-LD Serialization ──────────────────────────────────────


class TestV3ToJsonld:
    """V3.to_jsonld() output validation."""

    def test_default_v3_structure(self):
        """Default V3 produces valid JSON-LD structure."""
        v3 = V3()
        doc = v3.to_jsonld()

        assert doc["@context"] == [V3_JSONLD_CONTEXT]
        assert doc["@type"] == "V3Tensor"
        assert doc["valuation"] == 0.5
        assert doc["veracity"] == 0.5
        assert doc["validity"] == 0.5
        assert "composite_score" in doc
        assert "dimension_scores" in doc

    def test_custom_v3_values(self):
        """Custom V3 values serialize correctly."""
        v3 = V3(valuation=0.8, veracity=0.9, validity=0.7)
        doc = v3.to_jsonld()
        assert doc["valuation"] == 0.8
        assert doc["veracity"] == 0.9
        assert doc["validity"] == 0.7

    def test_composite_score_computed(self):
        """composite_score matches V3.composite property."""
        v3 = V3(valuation=0.8, veracity=0.9, validity=0.7)
        doc = v3.to_jsonld()
        expected = 0.8 * 0.3 + 0.9 * 0.35 + 0.7 * 0.35
        assert abs(doc["composite_score"] - expected) < 1e-10

    def test_dimension_scores_array(self):
        """dimension_scores array contains 3 root V3 dimensions."""
        v3 = V3(valuation=0.8, veracity=0.9, validity=0.7)
        doc = v3.to_jsonld()
        scores = doc["dimension_scores"]

        assert len(scores) == 3
        dims = {s["dimension"]: s["score"] for s in scores}
        assert dims["web4:Valuation"] == 0.8
        assert dims["web4:Veracity"] == 0.9
        assert dims["web4:Validity"] == 0.7

    def test_entity_binding(self):
        v3 = V3()
        doc = v3.to_jsonld(entity="lct:web4:carol")
        assert doc["entity"] == "lct:web4:carol"

    def test_role_binding(self):
        v3 = V3()
        doc = v3.to_jsonld(role="web4:Auditor")
        assert doc["role"] == "web4:Auditor"

    def test_no_entity_role_by_default(self):
        doc = V3().to_jsonld()
        assert "entity" not in doc
        assert "role" not in doc

    def test_boundary_zeros(self):
        v3 = V3(valuation=0.0, veracity=0.0, validity=0.0)
        doc = v3.to_jsonld()
        assert doc["valuation"] == 0.0
        assert doc["composite_score"] == 0.0

    def test_boundary_ones(self):
        v3 = V3(valuation=1.0, veracity=1.0, validity=1.0)
        doc = v3.to_jsonld()
        assert doc["valuation"] == 1.0
        assert abs(doc["composite_score"] - 1.0) < 1e-10

    def test_to_jsonld_string(self):
        v3 = V3(valuation=0.85, veracity=0.9, validity=0.75)
        s = v3.to_jsonld_string()
        parsed = json.loads(s)
        assert parsed["@type"] == "V3Tensor"
        assert parsed["valuation"] == 0.85


class TestV3FromJsonld:
    """V3.from_jsonld() deserialization validation."""

    def test_roundtrip_default(self):
        v3 = V3()
        v3_rt = V3.from_jsonld(v3.to_jsonld())
        assert v3_rt.valuation == v3.valuation
        assert v3_rt.veracity == v3.veracity
        assert v3_rt.validity == v3.validity

    def test_roundtrip_custom(self):
        v3 = V3(valuation=0.95, veracity=0.3, validity=0.88)
        v3_rt = V3.from_jsonld(v3.to_jsonld())
        assert v3_rt.valuation == v3.valuation
        assert v3_rt.veracity == v3.veracity
        assert v3_rt.validity == v3.validity

    def test_composite_recomputed(self):
        v3 = V3(valuation=0.8, veracity=0.9, validity=0.7)
        doc = v3.to_jsonld()
        doc["composite_score"] = 0.0
        v3_rt = V3.from_jsonld(doc)
        assert v3_rt.composite == v3.composite

    def test_from_plain_dict(self):
        v3 = V3.from_jsonld({"valuation": 0.8, "veracity": 0.6, "validity": 0.9})
        assert v3.valuation == 0.8
        assert v3.veracity == 0.6
        assert v3.validity == 0.9

    def test_missing_fields_default(self):
        v3 = V3.from_jsonld({"valuation": 0.8})
        assert v3.valuation == 0.8
        assert v3.veracity == 0.5
        assert v3.validity == 0.5

    def test_from_jsonld_string(self):
        s = V3(valuation=0.75, veracity=0.85, validity=0.65).to_jsonld_string()
        v3 = V3.from_jsonld_string(s)
        assert v3.valuation == 0.75
        assert v3.veracity == 0.85

    def test_roundtrip_boundary_zeros(self):
        v3 = V3(valuation=0.0, veracity=0.0, validity=0.0)
        v3_rt = V3.from_jsonld(v3.to_jsonld())
        assert v3_rt.valuation == 0.0

    def test_roundtrip_boundary_ones(self):
        v3 = V3(valuation=1.0, veracity=1.0, validity=1.0)
        v3_rt = V3.from_jsonld(v3.to_jsonld())
        assert v3_rt.valuation == 1.0


# ── JSON Schema Validation ────────────────────────────────────────


@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
class TestT3SchemaValidation:
    """T3 JSON-LD documents validated against JSON Schema."""

    def test_default_t3_valid(self, t3v3_schema):
        """Default T3 passes schema."""
        validate(T3().to_jsonld(), t3v3_schema)

    def test_custom_t3_valid(self, t3v3_schema):
        """Custom T3 passes schema."""
        validate(T3(talent=0.9, training=0.8, temperament=0.7).to_jsonld(), t3v3_schema)

    def test_t3_with_entity_role_valid(self, t3v3_schema):
        """T3 with entity+role passes schema."""
        validate(T3().to_jsonld(entity="lct:web4:x", role="web4:Y"), t3v3_schema)

    def test_boundary_zeros_valid(self, t3v3_schema):
        validate(T3(0.0, 0.0, 0.0).to_jsonld(), t3v3_schema)

    def test_boundary_ones_valid(self, t3v3_schema):
        validate(T3(1.0, 1.0, 1.0).to_jsonld(), t3v3_schema)

    def test_invalid_missing_type(self, t3v3_schema):
        """Missing @type rejected."""
        doc = T3().to_jsonld()
        del doc["@type"]
        with pytest.raises(jsonschema.ValidationError):
            validate(doc, t3v3_schema)

    def test_invalid_wrong_type(self, t3v3_schema):
        """Wrong @type rejected."""
        doc = T3().to_jsonld()
        doc["@type"] = "V3Tensor"
        with pytest.raises(jsonschema.ValidationError):
            validate(doc, t3v3_schema)

    def test_invalid_out_of_range(self, t3v3_schema):
        """Score > 1.0 rejected by schema."""
        doc = T3().to_jsonld()
        doc["talent"] = 1.5
        with pytest.raises(jsonschema.ValidationError):
            validate(doc, t3v3_schema)

    def test_invalid_extra_field(self, t3v3_schema):
        """Extra field rejected (additionalProperties: false)."""
        doc = T3().to_jsonld()
        doc["unknown_field"] = "bad"
        with pytest.raises(jsonschema.ValidationError):
            validate(doc, t3v3_schema)

    def test_invalid_missing_required(self, t3v3_schema):
        """Missing required field rejected."""
        doc = T3().to_jsonld()
        del doc["talent"]
        with pytest.raises(jsonschema.ValidationError):
            validate(doc, t3v3_schema)


@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
class TestV3SchemaValidation:
    """V3 JSON-LD documents validated against JSON Schema."""

    def test_default_v3_valid(self, t3v3_schema):
        validate(V3().to_jsonld(), t3v3_schema)

    def test_custom_v3_valid(self, t3v3_schema):
        validate(V3(valuation=0.8, veracity=0.9, validity=0.7).to_jsonld(), t3v3_schema)

    def test_v3_with_entity_role_valid(self, t3v3_schema):
        validate(V3().to_jsonld(entity="lct:web4:x", role="web4:Y"), t3v3_schema)

    def test_boundary_zeros_valid(self, t3v3_schema):
        validate(V3(0.0, 0.0, 0.0).to_jsonld(), t3v3_schema)

    def test_boundary_ones_valid(self, t3v3_schema):
        validate(V3(1.0, 1.0, 1.0).to_jsonld(), t3v3_schema)

    def test_invalid_missing_type(self, t3v3_schema):
        doc = V3().to_jsonld()
        del doc["@type"]
        with pytest.raises(jsonschema.ValidationError):
            validate(doc, t3v3_schema)

    def test_invalid_wrong_type(self, t3v3_schema):
        doc = V3().to_jsonld()
        doc["@type"] = "T3Tensor"
        with pytest.raises(jsonschema.ValidationError):
            validate(doc, t3v3_schema)

    def test_invalid_out_of_range(self, t3v3_schema):
        doc = V3().to_jsonld()
        doc["valuation"] = 1.5
        with pytest.raises(jsonschema.ValidationError):
            validate(doc, t3v3_schema)

    def test_invalid_extra_field(self, t3v3_schema):
        doc = V3().to_jsonld()
        doc["unknown_field"] = "bad"
        with pytest.raises(jsonschema.ValidationError):
            validate(doc, t3v3_schema)

    def test_invalid_missing_required(self, t3v3_schema):
        doc = V3().to_jsonld()
        del doc["valuation"]
        with pytest.raises(jsonschema.ValidationError):
            validate(doc, t3v3_schema)


# ── Namespace Reconciliation (B3) ────────────────────────────────


class TestNamespaceReconciliation:
    """B3: Verify namespace consistency after reconciliation."""

    def test_t3_context_uses_ns_namespace(self):
        """T3 @context no longer includes ontology# URI."""
        doc = T3().to_jsonld()
        assert doc["@context"] == [T3_JSONLD_CONTEXT]
        assert "https://web4.io/ontology#" not in doc["@context"]

    def test_v3_context_uses_ns_namespace(self):
        """V3 @context no longer includes ontology# URI."""
        doc = V3().to_jsonld()
        assert doc["@context"] == [V3_JSONLD_CONTEXT]
        assert "https://web4.io/ontology#" not in doc["@context"]

    def test_t3_context_uri_pattern(self):
        """T3 context URI follows schemas/contexts/ pattern."""
        assert T3_JSONLD_CONTEXT == "https://web4.io/contexts/t3.jsonld"

    def test_v3_context_uri_pattern(self):
        """V3 context URI follows schemas/contexts/ pattern."""
        assert V3_JSONLD_CONTEXT == "https://web4.io/contexts/v3.jsonld"

    def test_t3_from_jsonld_old_context(self):
        """T3.from_jsonld() accepts documents with old ontology# context."""
        old_doc = {
            "@context": ["https://web4.io/contexts/t3-tensor.jsonld", "https://web4.io/ontology#"],
            "@type": "T3Tensor",
            "talent": 0.9,
            "training": 0.8,
            "temperament": 0.7,
            "composite_score": 0.83,
            "dimension_scores": [
                {"dimension": "web4:Talent", "score": 0.9},
                {"dimension": "web4:Training", "score": 0.8},
                {"dimension": "web4:Temperament", "score": 0.7},
            ],
        }
        t3 = T3.from_jsonld(old_doc)
        assert t3.talent == 0.9
        assert t3.training == 0.8
        assert t3.temperament == 0.7

    def test_v3_from_jsonld_old_context(self):
        """V3.from_jsonld() accepts documents with old ontology# context."""
        old_doc = {
            "@context": ["https://web4.io/contexts/v3-tensor.jsonld", "https://web4.io/ontology#"],
            "@type": "V3Tensor",
            "valuation": 0.8,
            "veracity": 0.9,
            "validity": 0.7,
            "composite_score": 0.805,
            "dimension_scores": [
                {"dimension": "web4:Valuation", "score": 0.8},
                {"dimension": "web4:Veracity", "score": 0.9},
                {"dimension": "web4:Validity", "score": 0.7},
            ],
        }
        v3 = V3.from_jsonld(old_doc)
        assert v3.valuation == 0.8
        assert v3.veracity == 0.9
        assert v3.validity == 0.7

    def test_t3_context_file_exists(self):
        """t3.jsonld context file exists in schemas/contexts/."""
        ctx_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..",
            "schemas", "contexts", "t3.jsonld"
        )
        assert os.path.exists(ctx_path), f"Missing context file: {ctx_path}"

    def test_v3_context_file_exists(self):
        """v3.jsonld context file exists in schemas/contexts/."""
        ctx_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..",
            "schemas", "contexts", "v3.jsonld"
        )
        assert os.path.exists(ctx_path), f"Missing context file: {ctx_path}"

    def test_t3_context_file_uses_ns_namespace(self):
        """t3.jsonld uses https://web4.io/ns/ namespace."""
        ctx_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..",
            "schemas", "contexts", "t3.jsonld"
        )
        with open(ctx_path) as f:
            ctx = json.load(f)
        assert ctx["@context"]["web4"] == "https://web4.io/ns/"

    def test_v3_context_file_uses_ns_namespace(self):
        """v3.jsonld uses https://web4.io/ns/ namespace."""
        ctx_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..",
            "schemas", "contexts", "v3.jsonld"
        )
        with open(ctx_path) as f:
            ctx = json.load(f)
        assert ctx["@context"]["web4"] == "https://web4.io/ns/"

    def test_t3_context_file_has_all_dimensions(self):
        """t3.jsonld context defines T3 dimension terms."""
        ctx_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..",
            "schemas", "contexts", "t3.jsonld"
        )
        with open(ctx_path) as f:
            ctx = json.load(f)["@context"]
        for term in ["talent", "training", "temperament", "T3Tensor", "Talent", "Training", "Temperament"]:
            assert term in ctx, f"Missing term '{term}' in t3.jsonld"

    def test_v3_context_file_has_all_dimensions(self):
        """v3.jsonld context defines V3 dimension terms."""
        ctx_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..",
            "schemas", "contexts", "v3.jsonld"
        )
        with open(ctx_path) as f:
            ctx = json.load(f)["@context"]
        for term in ["valuation", "veracity", "validity", "V3Tensor", "Valuation", "Veracity", "Validity"]:
            assert term in ctx, f"Missing term '{term}' in v3.jsonld"
