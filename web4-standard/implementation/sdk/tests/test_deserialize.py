"""Tests for web4.deserialize -- generic JSON-LD deserialization dispatcher.

Uses parametrized tests per policy review condition: one parametrized test
covers all 22 supported types rather than separate test functions per type.
"""

from __future__ import annotations

import json
from typing import Any, Dict

import pytest

from web4.deserialize import (
    UnknownTypeError,
    from_jsonld,
    from_jsonld_string,
    supported_types,
)

# ---------------------------------------------------------------------------
# Fixture helpers -- build minimal JSON-LD documents for each supported type
# ---------------------------------------------------------------------------


def _make_t3_doc() -> Dict[str, Any]:
    from web4.trust import T3

    return T3(talent=0.8, training=0.7, temperament=0.9).to_jsonld()


def _make_v3_doc() -> Dict[str, Any]:
    from web4.trust import V3

    return V3(valuation=0.6, veracity=0.8, validity=0.7).to_jsonld()


def _make_lct_doc() -> Dict[str, Any]:
    from web4.lct import LCT, EntityType

    return LCT.create(entity_type=EntityType.AI, public_key="test-key").to_jsonld()


def _make_atp_account_doc() -> Dict[str, Any]:
    from web4.atp import ATPAccount

    return ATPAccount(available=100.0).to_jsonld()


def _make_transfer_result_doc() -> Dict[str, Any]:
    from web4.atp import TransferResult

    return TransferResult(
        fee=0.05, sender_balance=99.95, receiver_balance=100.0, actual_credit=100.0
    ).to_jsonld()


def _make_attestation_doc() -> Dict[str, Any]:
    from web4.attestation import AttestationEnvelope

    return AttestationEnvelope(
        entity_id="lct:entity:abc", public_key="test-key"
    ).to_jsonld()


def _make_agent_plan_doc() -> Dict[str, Any]:
    from web4.acp import AgentPlan, PlanStep

    return AgentPlan(
        plan_id="plan-001",
        principal="lct:p:abc",
        agent="lct:a:xyz",
        grant_id="grant-001",
        steps=[PlanStep(step_id="s1", mcp_tool="test.tool")],
    ).to_jsonld()


def _make_intent_doc() -> Dict[str, Any]:
    from web4.acp import Intent, ProofOfAgency

    return Intent(
        intent_id="acp:intent:abc123",
        plan_id="plan-001",
        step_id="s1",
        proposed_action={"mcp": "test.tool", "args": {}},
        proof=ProofOfAgency(
            grant_id="grant-001", plan_id="plan-001", intent_id="acp:intent:abc123"
        ),
    ).to_jsonld()


def _make_decision_doc() -> Dict[str, Any]:
    from web4.acp import Decision, DecisionType

    return Decision(
        intent_id="acp:intent:abc123",
        decision=DecisionType.APPROVE,
        decided_by="lct:r:r1",
    ).to_jsonld()


def _make_execution_record_doc() -> Dict[str, Any]:
    from web4.acp import ExecutionRecord

    return ExecutionRecord(
        record_id="rec-001",
        intent_id="acp:intent:abc123",
        grant_id="grant-001",
        law_hash="abc123",
        mcp_call={"resource": "test.tool", "args": {}},
    ).to_jsonld()


def _make_entity_type_info_doc() -> Dict[str, Any]:
    from web4.entity import EntityType, get_info

    return get_info(EntityType.HUMAN).to_jsonld()


def _make_entity_registry_doc() -> Dict[str, Any]:
    from web4.entity import entity_registry_to_jsonld

    return entity_registry_to_jsonld()


def _make_level_requirement_doc() -> Dict[str, Any]:
    from web4.capability import level_requirements

    return level_requirements(1).to_jsonld()


def _make_capability_assessment_doc() -> Dict[str, Any]:
    from web4.capability import capability_assessment_to_jsonld
    from web4.lct import LCT, EntityType

    lct = LCT.create(entity_type=EntityType.AI, public_key="test-key")
    return capability_assessment_to_jsonld(lct)


def _make_capability_framework_doc() -> Dict[str, Any]:
    from web4.capability import capability_framework_to_jsonld

    return capability_framework_to_jsonld()


def _make_dictionary_spec_doc() -> Dict[str, Any]:
    from web4.dictionary import DictionarySpec

    return DictionarySpec(source_domain="medical", target_domain="legal").to_jsonld()


def _make_translation_result_doc() -> Dict[str, Any]:
    from web4.dictionary import TranslationResult

    return TranslationResult(
        content="translated", confidence=0.95, degradation=0.05,
        dictionary_lct_id="lct:dict:abc",
    ).to_jsonld()


def _make_translation_chain_doc() -> Dict[str, Any]:
    from web4.dictionary import TranslationChain

    return TranslationChain().to_jsonld()


def _make_dictionary_entity_doc() -> Dict[str, Any]:
    from web4.dictionary import DictionaryEntity

    return DictionaryEntity.create(
        source_domain="medical", target_domain="legal", public_key="mb64dictkey"
    ).to_jsonld()


def _make_r7_action_doc() -> Dict[str, Any]:
    from web4.r6 import Result, build_action

    action = build_action(
        actor="lct:actor:abc", role_lct="lct:role:xyz", action="analyze"
    )
    action.result = Result()
    return action.to_jsonld()


def _make_reputation_delta_doc() -> Dict[str, Any]:
    from web4.r6 import ReputationDelta

    return ReputationDelta(
        subject_lct="lct:actor:abc", role_lct="lct:role:xyz"
    ).to_jsonld()


def _make_action_chain_doc() -> Dict[str, Any]:
    from web4.r6 import ActionChain, Result, build_action

    action = build_action(
        actor="lct:actor:abc", role_lct="lct:role:xyz", action="analyze"
    )
    action.result = Result()
    ac = ActionChain()
    ac.actions.append(action)
    return ac.to_jsonld()


def _make_trust_query_doc() -> Dict[str, Any]:
    from web4.trust import TrustQuery

    q = TrustQuery(
        querier="lct:web4:alice",
        target_entity="lct:web4:bob",
        requested_role="web4:Surgeon",
        intended_interaction="surgical-procedure",
        atp_stake=100,
        validity_period=3600,
        signature="test-sig",
    )
    return q.to_jsonld()


# ---------------------------------------------------------------------------
# All-types parametrized fixture
# ---------------------------------------------------------------------------

# (bare_type_name, doc_factory, expected_class_name_or_"dict")
ALL_TYPES = [
    ("T3Tensor", _make_t3_doc, "T3"),
    ("V3Tensor", _make_v3_doc, "V3"),
    ("LinkedContextToken", _make_lct_doc, "LCT"),
    ("ATPAccount", _make_atp_account_doc, "ATPAccount"),
    ("TransferResult", _make_transfer_result_doc, "TransferResult"),
    ("AttestationEnvelope", _make_attestation_doc, "AttestationEnvelope"),
    ("AgentPlan", _make_agent_plan_doc, "AgentPlan"),
    ("Intent", _make_intent_doc, "Intent"),
    ("Decision", _make_decision_doc, "Decision"),
    ("ExecutionRecord", _make_execution_record_doc, "ExecutionRecord"),
    ("EntityTypeInfo", _make_entity_type_info_doc, "EntityTypeInfo"),
    ("EntityTypeRegistry", _make_entity_registry_doc, "dict"),
    ("LevelRequirement", _make_level_requirement_doc, "LevelRequirement"),
    ("CapabilityAssessment", _make_capability_assessment_doc, "CapabilityAssessment"),
    ("CapabilityFramework", _make_capability_framework_doc, "list"),
    ("DictionarySpec", _make_dictionary_spec_doc, "DictionarySpec"),
    ("TranslationResult", _make_translation_result_doc, "TranslationResult"),
    ("TranslationChain", _make_translation_chain_doc, "TranslationChain"),
    ("DictionaryEntity", _make_dictionary_entity_doc, "DictionaryEntity"),
    ("R7Action", _make_r7_action_doc, "R7Action"),
    ("ReputationDelta", _make_reputation_delta_doc, "ReputationDelta"),
    ("ActionChain", _make_action_chain_doc, "ActionChain"),
    ("TrustQuery", _make_trust_query_doc, "TrustQuery"),
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFromJsonldAllTypes:
    """Parametrized test covering all 22 supported types."""

    @pytest.mark.parametrize(
        "bare_type,doc_factory,expected_class",
        ALL_TYPES,
        ids=[t[0] for t in ALL_TYPES],
    )
    def test_bare_type_dispatch(
        self, bare_type: str, doc_factory: Any, expected_class: str
    ) -> None:
        """from_jsonld dispatches correctly for bare @type values."""
        doc = doc_factory()
        result = from_jsonld(doc)
        actual = type(result).__name__
        assert actual == expected_class, f"{bare_type}: expected {expected_class}, got {actual}"

    @pytest.mark.parametrize(
        "bare_type,doc_factory,expected_class",
        ALL_TYPES,
        ids=[f"web4:{t[0]}" for t in ALL_TYPES],
    )
    def test_prefixed_type_dispatch(
        self, bare_type: str, doc_factory: Any, expected_class: str
    ) -> None:
        """from_jsonld dispatches correctly for web4:-prefixed @type values."""
        doc = doc_factory()
        original_type = doc["@type"]
        if isinstance(original_type, str) and not original_type.startswith("web4:"):
            doc["@type"] = f"web4:{original_type}"
        result = from_jsonld(doc)
        actual = type(result).__name__
        assert actual == expected_class


class TestFromJsonldErrors:
    """Error handling tests."""

    def test_no_type_field(self) -> None:
        with pytest.raises(ValueError, match="no @type"):
            from_jsonld({"data": "test"})

    def test_unknown_type(self) -> None:
        with pytest.raises(UnknownTypeError, match="FakeType"):
            from_jsonld({"@type": "FakeType"})

    def test_unknown_type_has_attribute(self) -> None:
        with pytest.raises(UnknownTypeError) as exc_info:
            from_jsonld({"@type": "NoSuchType"})
        assert exc_info.value.type_value == "NoSuchType"

    def test_not_a_dict(self) -> None:
        with pytest.raises(TypeError, match="Expected dict"):
            from_jsonld("not a dict")  # type: ignore[arg-type]

    def test_type_not_string_or_list(self) -> None:
        with pytest.raises(ValueError, match="string or list"):
            from_jsonld({"@type": 42})

    def test_list_type_no_match(self) -> None:
        with pytest.raises(UnknownTypeError):
            from_jsonld({"@type": ["UnknownA", "UnknownB"]})

    def test_list_type_with_match(self) -> None:
        """List @type should dispatch on the first recognized value."""
        doc = _make_t3_doc()
        doc["@type"] = ["UnrecognizedPrefix", "T3Tensor"]
        result = from_jsonld(doc)
        assert type(result).__name__ == "T3"


class TestFromJsonldString:
    """Tests for the string convenience wrapper."""

    def test_roundtrip_from_string(self) -> None:
        doc = _make_t3_doc()
        s = json.dumps(doc)
        result = from_jsonld_string(s)
        assert type(result).__name__ == "T3"

    def test_invalid_json(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            from_jsonld_string("{not valid json}")


class TestSupportedTypes:
    """Tests for supported_types()."""

    def test_returns_sorted_list(self) -> None:
        types = supported_types()
        assert types == sorted(types)

    def test_no_prefixed_names(self) -> None:
        types = supported_types()
        assert not any(t.startswith("web4:") for t in types)

    def test_count_matches_all_types(self) -> None:
        types = supported_types()
        assert len(types) == 23

    def test_all_test_types_in_supported(self) -> None:
        """Every type in ALL_TYPES is in supported_types()."""
        types = set(supported_types())
        for bare_type, _, _ in ALL_TYPES:
            assert bare_type in types, f"{bare_type} missing from supported_types()"


class TestPackageExports:
    """Verify the deserialize module is properly exported from web4."""

    def test_from_jsonld_importable(self) -> None:
        from web4 import from_jsonld as fn

        assert callable(fn)

    def test_from_jsonld_string_importable(self) -> None:
        from web4 import from_jsonld_string as fn

        assert callable(fn)

    def test_supported_types_importable(self) -> None:
        from web4 import supported_types as fn

        assert callable(fn)

    def test_unknown_type_error_importable(self) -> None:
        from web4 import UnknownTypeError as cls

        assert issubclass(cls, Exception)

    def test_in_all(self) -> None:
        import web4

        for name in ("from_jsonld", "from_jsonld_string", "supported_types", "UnknownTypeError"):
            assert name in web4.__all__, f"{name} not in web4.__all__"
