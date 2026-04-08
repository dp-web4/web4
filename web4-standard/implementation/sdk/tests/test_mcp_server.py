"""Tests for web4.mcp_server — MCP tool handlers."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List

import pytest

from web4.mcp_server import (
    mcp,
    web4_evaluate_trust,
    web4_generate,
    web4_info,
    web4_list_types,
    web4_resolve_trust,
    web4_roundtrip,
    web4_validate,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _call_tool(name: str, arguments: Dict[str, Any] | None = None) -> Any:
    """Call an MCP tool synchronously and return the structured result."""
    if arguments is None:
        arguments = {}
    content_blocks, extra = asyncio.run(mcp.call_tool(name, arguments))
    # FastMCP returns structured output in extra["result"]
    return extra["result"]


# ---------------------------------------------------------------------------
# web4_info
# ---------------------------------------------------------------------------


class TestWeb4Info:
    """Tests for the web4_info tool."""

    def test_returns_version(self) -> None:
        result = web4_info()
        assert "version" in result
        assert isinstance(result["version"], str)

    def test_returns_module_count(self) -> None:
        result = web4_info()
        assert result["modules"] == 22

    def test_returns_module_names(self) -> None:
        result = web4_info()
        assert "trust" in result["module_names"]
        assert "lct" in result["module_names"]
        assert "generate" in result["module_names"]

    def test_returns_export_count(self) -> None:
        result = web4_info()
        assert isinstance(result["exports"], int)
        assert result["exports"] >= 359

    def test_returns_schema_info(self) -> None:
        result = web4_info()
        assert isinstance(result["schemas"], int)
        assert result["schemas"] >= 9

    def test_via_mcp_call(self) -> None:
        result = _call_tool("web4_info")
        assert result["modules"] == 22


# ---------------------------------------------------------------------------
# web4_validate
# ---------------------------------------------------------------------------


class TestWeb4Validate:
    """Tests for the web4_validate tool."""

    def test_valid_t3_document(self) -> None:
        from web4.generate import generate
        doc = generate("T3Tensor")
        result = web4_validate(json.dumps(doc))
        assert result["valid"] is True
        assert result["schema"] == "t3v3"

    def test_valid_with_explicit_schema(self) -> None:
        from web4.generate import generate
        doc = generate("T3Tensor")
        result = web4_validate(json.dumps(doc), schema_name="t3v3")
        assert result["valid"] is True

    def test_invalid_json(self) -> None:
        result = web4_validate("{not valid json")
        assert result["valid"] is False
        assert "Invalid JSON" in result["error"]

    def test_non_object_document(self) -> None:
        result = web4_validate('"just a string"')
        assert result["valid"] is False
        assert "JSON object" in result["error"]

    def test_no_type_no_schema(self) -> None:
        result = web4_validate('{"foo": "bar"}')
        assert result["valid"] is False
        assert "detect schema" in result["error"].lower() or "Cannot" in result["error"]

    def test_unknown_schema(self) -> None:
        result = web4_validate('{"@type": "T3Tensor"}', schema_name="nonexistent")
        assert result["valid"] is False

    def test_invalid_document_against_schema(self) -> None:
        # Missing required fields
        doc = {"@type": "T3Tensor", "@context": []}
        result = web4_validate(json.dumps(doc), schema_name="t3v3")
        assert result["valid"] is False
        assert "errors" in result

    def test_via_mcp_call(self) -> None:
        from web4.generate import generate
        doc = generate("ATPAccount")
        result = _call_tool("web4_validate", {"document": json.dumps(doc)})
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# web4_generate
# ---------------------------------------------------------------------------


class TestWeb4Generate:
    """Tests for the web4_generate tool."""

    def test_generate_t3(self) -> None:
        result = web4_generate("T3Tensor")
        assert result["type"] == "T3Tensor"
        assert isinstance(result["document"], dict)
        assert result["document"]["@type"] == "T3Tensor"

    def test_generate_compact(self) -> None:
        result = web4_generate("T3Tensor", compact=True)
        assert result["type"] == "T3Tensor"
        # Compact mode returns a JSON string, not a dict
        assert isinstance(result["document"], str)
        parsed = json.loads(result["document"])
        assert parsed["@type"] == "T3Tensor"

    def test_generate_unknown_type(self) -> None:
        result = web4_generate("NonexistentType")
        assert "error" in result
        assert "available_types" in result

    def test_generate_all_types(self) -> None:
        from web4.generate import available_types
        for type_name in available_types():
            result = web4_generate(type_name)
            assert "error" not in result, f"Failed for {type_name}: {result}"
            assert result["type"] == type_name

    def test_via_mcp_call(self) -> None:
        result = _call_tool("web4_generate", {"type_name": "R7Action"})
        assert result["type"] == "R7Action"
        assert isinstance(result["document"], dict)


# ---------------------------------------------------------------------------
# web4_roundtrip
# ---------------------------------------------------------------------------


class TestWeb4Roundtrip:
    """Tests for the web4_roundtrip tool."""

    def test_roundtrip_t3(self) -> None:
        from web4.generate import generate
        doc = generate("T3Tensor")
        result = web4_roundtrip(json.dumps(doc))
        assert result["success"] is True
        assert result["preserved"] is True

    def test_roundtrip_class_based_types(self) -> None:
        """Roundtrip all class-based types (those with to_jsonld on the object)."""
        from web4.generate import available_types, generate

        # These types use function-based deserialization (return dicts, not objects)
        function_based = {
            "CapabilityAssessment", "CapabilityFramework", "EntityTypeRegistry",
        }
        for type_name in available_types():
            if type_name in function_based:
                continue
            doc = generate(type_name)
            result = web4_roundtrip(json.dumps(doc))
            assert result["success"] is True, f"Failed for {type_name}: {result}"

    def test_roundtrip_function_based_types_report_error(self) -> None:
        """Function-based types can't roundtrip (no to_jsonld on the result)."""
        from web4.generate import generate
        for type_name in ("CapabilityAssessment", "CapabilityFramework", "EntityTypeRegistry"):
            doc = generate(type_name)
            result = web4_roundtrip(json.dumps(doc))
            # These correctly report that re-serialization isn't supported
            assert result["success"] is False

    def test_roundtrip_invalid_json(self) -> None:
        result = web4_roundtrip("not json")
        assert result["success"] is False
        assert "Invalid JSON" in result["error"]

    def test_roundtrip_non_object(self) -> None:
        result = web4_roundtrip("[1,2,3]")
        assert result["success"] is False
        assert "JSON object" in result["error"]

    def test_roundtrip_unknown_type(self) -> None:
        result = web4_roundtrip('{"@type": "FakeType123"}')
        assert result["success"] is False

    def test_via_mcp_call(self) -> None:
        from web4.generate import generate
        doc = generate("V3Tensor")
        result = _call_tool("web4_roundtrip", {"document": json.dumps(doc)})
        assert result["success"] is True
        assert result["preserved"] is True


# ---------------------------------------------------------------------------
# web4_list_types
# ---------------------------------------------------------------------------


class TestWeb4ListTypes:
    """Tests for the web4_list_types tool."""

    def test_returns_generate_types(self) -> None:
        result = web4_list_types()
        assert result["generate_count"] == 23
        assert "T3Tensor" in result["generate_types"]
        assert "V3Tensor" in result["generate_types"]

    def test_returns_deserialize_types(self) -> None:
        result = web4_list_types()
        assert result["deserialize_count"] == 23
        assert "R7Action" in result["deserialize_types"]

    def test_types_are_sorted(self) -> None:
        result = web4_list_types()
        assert result["generate_types"] == sorted(result["generate_types"])
        assert result["deserialize_types"] == sorted(result["deserialize_types"])

    def test_via_mcp_call(self) -> None:
        result = _call_tool("web4_list_types")
        assert result["generate_count"] == 23
        assert result["deserialize_count"] == 23


# ---------------------------------------------------------------------------
# Server registration
# ---------------------------------------------------------------------------


class TestServerRegistration:
    """Tests for MCP server tool registration."""

    def test_server_name(self) -> None:
        assert mcp.name == "web4"

    def test_eight_tools_registered(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 8

    def test_tool_names(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        names = {t.name for t in tools}
        assert names == {
            "web4_info",
            "web4_validate",
            "web4_generate",
            "web4_roundtrip",
            "web4_list_types",
            "web4_evaluate_trust",
            "web4_resolve_trust",
            "web4_process_action_outcome",
        }

    def test_all_tools_have_descriptions(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        for tool in tools:
            assert tool.description, f"Tool {tool.name} missing description"
            assert len(tool.description) > 20


# ---------------------------------------------------------------------------
# web4_evaluate_trust
# ---------------------------------------------------------------------------


def _make_query_json(
    querier: str = "lct:alice",
    target: str = "lct:bob",
    role: str = "analyst",
    stake: int = 100,
    validity: int = 3600,
    disclosure: str = "precise",
) -> str:
    """Build a TrustQuery JSON string for testing."""
    return json.dumps({
        "querier": querier,
        "target_entity": target,
        "requested_role": role,
        "intended_interaction": "test interaction",
        "atp_stake": stake,
        "validity_period": validity,
        "signature": "test-sig-001",
        "disclosure_level": disclosure,
    })


class TestWeb4EvaluateTrust:
    """Tests for the web4_evaluate_trust tool."""

    def test_approved_precise(self) -> None:
        result = web4_evaluate_trust(
            query=_make_query_json(),
            profile_entity_id="lct:bob",
            profile_roles=json.dumps({
                "analyst": {"talent": 0.8, "training": 0.9, "temperament": 0.7},
            }),
            atp_balance=1000.0,
        )
        assert result["status"] == "APPROVED"
        resp = result["response"]
        assert resp["entity"] == "lct:bob"
        assert resp["role"] == "analyst"
        assert resp["t3_in_role"]["talent"] == 0.8

    def test_approved_binary_disclosure(self) -> None:
        result = web4_evaluate_trust(
            query=_make_query_json(disclosure="binary"),
            profile_entity_id="lct:bob",
            profile_roles=json.dumps({
                "analyst": {"talent": 0.8, "training": 0.9, "temperament": 0.7},
            }),
        )
        assert result["status"] == "APPROVED"
        # Binary disclosure doesn't reveal T3 dimensions
        assert result["response"].get("t3_in_role") is None

    def test_approved_range_disclosure(self) -> None:
        result = web4_evaluate_trust(
            query=_make_query_json(disclosure="range"),
            profile_entity_id="lct:bob",
            profile_roles=json.dumps({
                "analyst": {"talent": 0.8, "training": 0.9, "temperament": 0.7},
            }),
        )
        assert result["status"] == "APPROVED"
        t3 = result["response"]["t3_in_role"]
        # Range: all dimensions equal the composite
        assert t3["talent"] == t3["training"] == t3["temperament"]

    def test_rejected_insufficient_atp(self) -> None:
        result = web4_evaluate_trust(
            query=_make_query_json(stake=500),
            profile_entity_id="lct:bob",
            atp_balance=100.0,  # less than stake
        )
        assert result["status"] == "REJECTED"
        assert result["error"]["code"] == "INSUFFICIENT_STAKE"

    def test_default_profile_roles(self) -> None:
        """Empty profile_roles uses default T3(0.5, 0.5, 0.5)."""
        result = web4_evaluate_trust(
            query=_make_query_json(),
            profile_entity_id="lct:bob",
        )
        assert result["status"] == "APPROVED"
        t3 = result["response"]["t3_in_role"]
        assert t3["talent"] == 0.5

    def test_invalid_query_json(self) -> None:
        result = web4_evaluate_trust(
            query="not json",
            profile_entity_id="lct:bob",
        )
        assert "error" in result
        assert "Invalid query JSON" in result["error"]

    def test_invalid_query_fields(self) -> None:
        result = web4_evaluate_trust(
            query='{"querier": "alice"}',  # missing required fields
            profile_entity_id="lct:bob",
        )
        assert "error" in result
        assert "Invalid TrustQuery" in result["error"]

    def test_invalid_profile_roles_json(self) -> None:
        result = web4_evaluate_trust(
            query=_make_query_json(),
            profile_entity_id="lct:bob",
            profile_roles="not json",
        )
        assert "error" in result
        assert "Invalid profile_roles JSON" in result["error"]

    def test_with_timestamp(self) -> None:
        result = web4_evaluate_trust(
            query=_make_query_json(),
            profile_entity_id="lct:bob",
            timestamp="2026-04-07T18:00:00Z",
        )
        assert result["status"] == "APPROVED"
        assert result["response"]["validity_until"] is not None

    def test_via_mcp_call(self) -> None:
        result = _call_tool("web4_evaluate_trust", {
            "query": _make_query_json(),
            "profile_entity_id": "lct:bob",
            "profile_roles": json.dumps({
                "analyst": {"talent": 0.85, "training": 0.9, "temperament": 0.75},
            }),
        })
        assert result["status"] == "APPROVED"


# ---------------------------------------------------------------------------
# web4_resolve_trust
# ---------------------------------------------------------------------------


def _make_edges_json(*edges: tuple[str, str, float]) -> str:
    """Build MRH edges JSON. Each tuple is (source, target, weight)."""
    return json.dumps([
        {"source": s, "target": t, "relation": "pairedWith", "weight": w}
        for s, t, w in edges
    ])


class TestWeb4ResolveTrust:
    """Tests for the web4_resolve_trust tool."""

    def test_direct_self_trust(self) -> None:
        result = web4_resolve_trust(
            observer="lct:alice",
            target="lct:alice",
            role="analyst",
            edges="[]",
            profiles=json.dumps({
                "lct:alice": {"analyst": {"talent": 0.9, "training": 0.8, "temperament": 0.7}},
            }),
        )
        assert result["method"] == "direct"
        assert result["path_trust"] == 1.0
        assert result["hops"] == 0
        assert result["effective_t3"]["talent"] == 0.9

    def test_indirect_one_hop(self) -> None:
        result = web4_resolve_trust(
            observer="lct:alice",
            target="lct:bob",
            role="analyst",
            edges=_make_edges_json(("lct:alice", "lct:bob", 0.8)),
            profiles=json.dumps({
                "lct:bob": {"analyst": {"talent": 0.9, "training": 0.8, "temperament": 0.7}},
            }),
        )
        assert result["method"] == "indirect"
        assert result["path_trust"] > 0.0
        assert result["effective_t3"] is not None
        # T3 is attenuated by path trust
        assert result["effective_t3"]["talent"] <= 0.9

    def test_no_path(self) -> None:
        """No edge between observer and target → method 'none'."""
        result = web4_resolve_trust(
            observer="lct:alice",
            target="lct:charlie",
            role="analyst",
            edges=_make_edges_json(("lct:alice", "lct:bob", 0.9)),
        )
        assert result["method"] == "none"
        assert result["path_trust"] == 0.0
        assert result.get("effective_t3") is None

    def test_multi_hop(self) -> None:
        result = web4_resolve_trust(
            observer="lct:alice",
            target="lct:charlie",
            role="analyst",
            edges=_make_edges_json(
                ("lct:alice", "lct:bob", 0.9),
                ("lct:bob", "lct:charlie", 0.8),
            ),
            profiles=json.dumps({
                "lct:charlie": {"analyst": {"talent": 0.9, "training": 0.9, "temperament": 0.9}},
            }),
        )
        assert result["method"] == "indirect"
        assert result["hops"] >= 2
        # Multi-hop decays more
        assert result["path_trust"] < 0.8

    def test_custom_strategy_and_decay(self) -> None:
        result = web4_resolve_trust(
            observer="lct:alice",
            target="lct:bob",
            role="analyst",
            edges=_make_edges_json(("lct:alice", "lct:bob", 0.9)),
            strategy="multiplicative",
            decay_factor=0.5,
        )
        assert result["strategy"] == "multiplicative"
        assert result["method"] == "indirect"

    def test_invalid_edges_json(self) -> None:
        result = web4_resolve_trust(
            observer="lct:alice",
            target="lct:bob",
            role="analyst",
            edges="not json",
        )
        assert "error" in result

    def test_edges_not_array(self) -> None:
        result = web4_resolve_trust(
            observer="lct:alice",
            target="lct:bob",
            role="analyst",
            edges='{"not": "array"}',
        )
        assert "error" in result
        assert "array" in result["error"]

    def test_invalid_edge_data(self) -> None:
        result = web4_resolve_trust(
            observer="lct:alice",
            target="lct:bob",
            role="analyst",
            edges='[{"source": "a"}]',  # missing required fields
        )
        assert "error" in result

    def test_invalid_profiles_json(self) -> None:
        result = web4_resolve_trust(
            observer="lct:alice",
            target="lct:bob",
            role="analyst",
            edges="[]",
            profiles="not json",
        )
        assert "error" in result

    def test_via_mcp_call(self) -> None:
        result = _call_tool("web4_resolve_trust", {
            "observer": "lct:alice",
            "target": "lct:bob",
            "role": "analyst",
            "edges": _make_edges_json(("lct:alice", "lct:bob", 0.85)),
            "profiles": json.dumps({
                "lct:bob": {"analyst": {"talent": 0.8, "training": 0.9, "temperament": 0.7}},
            }),
        })
        assert result["method"] == "indirect"
        assert result["path_trust"] > 0.0


# ---------------------------------------------------------------------------
# Integration: generate → validate → roundtrip pipeline
# ---------------------------------------------------------------------------


class TestPipeline:
    """Integration tests for the generate → validate → roundtrip pipeline."""

    @pytest.mark.parametrize("type_name", [
        "T3Tensor", "V3Tensor", "R7Action", "ATPAccount", "AgentPlan",
        "AttestationEnvelope", "DictionarySpec",
    ])
    def test_generate_validate_roundtrip(self, type_name: str) -> None:
        """Generate a document, validate it, then roundtrip it."""
        # Generate
        gen_result = web4_generate(type_name)
        assert "error" not in gen_result
        doc = gen_result["document"]
        doc_str = json.dumps(doc)

        # Validate
        val_result = web4_validate(doc_str)
        assert val_result["valid"] is True, f"Validation failed for {type_name}: {val_result}"

        # Roundtrip
        rt_result = web4_roundtrip(doc_str)
        assert rt_result["success"] is True

    def test_lct_roundtrip_succeeds(self) -> None:
        """LCT generates and round-trips correctly even though it has special @type handling."""
        gen_result = web4_generate("LinkedContextToken")
        assert "error" not in gen_result
        doc = gen_result["document"]

        # LCT round-trips successfully via the dispatcher
        rt_result = web4_roundtrip(json.dumps(doc))
        assert rt_result["success"] is True

    def test_lct_schema_note(self) -> None:
        """LCT spec §2.3 omits @type; generate adds it for dispatch. Schema rejects it.

        This is a known characteristic: generate() adds @type for dispatcher
        compatibility, but the LCT schema per spec §2.3 forbids @type at
        top level. Validation with the raw generated doc thus fails.
        """
        gen_result = web4_generate("LinkedContextToken")
        doc = gen_result["document"]

        # Remove @type to match spec §2.3
        doc_no_type = {k: v for k, v in doc.items() if k != "@type"}
        val_result = web4_validate(json.dumps(doc_no_type), schema_name="lct")
        assert val_result["valid"] is True
