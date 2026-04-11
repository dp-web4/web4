"""Generate minimal valid JSON-LD documents for any web4 type.

Each factory produces a minimal but schema-valid instance of a web4 type,
serialized to JSON-LD via ``to_jsonld()``.  Useful for bootstrapping
documents, cross-language conformance testing, and documentation examples.

Usage::

    from web4.generate import generate
    doc = generate("T3Tensor")        # -> dict (JSON-LD)

    from web4.generate import generate_string
    print(generate_string("R7Action"))  # -> JSON string

    from web4.generate import available_types
    print(available_types())           # -> ['ActionChain', 'AgentPlan', ...]
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional


class UnsupportedTypeError(Exception):
    """Raised when the requested type name is not recognized."""

    def __init__(self, type_name: str) -> None:
        self.type_name = type_name
        super().__init__(
            f"Unsupported type: {type_name!r}. "
            f"Use available_types() to list recognized types."
        )


# ---------------------------------------------------------------------------
# Lazy registry -- built on first use to avoid circular imports
# ---------------------------------------------------------------------------

_registry: Optional[Dict[str, Callable[[], Dict[str, Any]]]] = None


def _make_t3() -> Dict[str, Any]:
    from .trust import T3
    return T3(talent=0.8, training=0.7, temperament=0.9).to_jsonld()


def _make_v3() -> Dict[str, Any]:
    from .trust import V3
    return V3(valuation=0.7, veracity=0.85, validity=0.8).to_jsonld()


def _make_trust_query() -> Dict[str, Any]:
    from .trust import TrustQuery
    q = TrustQuery(
        querier="lct:web4:alice",
        target_entity="lct:web4:bob",
        requested_role="web4:DataAnalyst",
        intended_interaction="data-analysis",
        atp_stake=100,
        validity_period=3600,
        signature="example-signature",
    )
    # TrustQuery uses to_jsonld() for dispatcher compatibility but the
    # trust-query.schema.json does not allow @context/@type, so we produce
    # a dict that works with both: @type for the dispatcher, validated via
    # to_dict() in schema tests.
    return q.to_jsonld()


def _make_attestation_envelope() -> Dict[str, Any]:
    from .attestation import AnchorInfo, AttestationEnvelope, Proof
    return AttestationEnvelope(
        entity_id="lct://web4:example@active",
        public_key="MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE_example",
        anchor=AnchorInfo(type="software"),
        proof=Proof(
            format="ecdsa_software",
            signature="example-sig",
            challenge="example-challenge",
        ),
        timestamp=1710864000.0,
        challenge_issued_at=1710863990.0,
        challenge_ttl=300.0,
        envelope_version="0.1",
    ).to_jsonld()


def _make_atp_account() -> Dict[str, Any]:
    from .atp import ATPAccount
    return ATPAccount(available=1000.0).to_jsonld()


def _make_transfer_result() -> Dict[str, Any]:
    from .atp import ATPAccount, transfer
    sender = ATPAccount(available=1000.0)
    receiver = ATPAccount(available=0.0)
    return transfer(sender, receiver, 200.0).to_jsonld()


def _make_agent_plan() -> Dict[str, Any]:
    from .acp import AgentPlan, PlanStep
    return AgentPlan(
        plan_id="plan:example-001",
        principal="lct:web4:human:alice",
        agent="lct:web4:agent:assistant",
        grant_id="grant-001",
        steps=[PlanStep(step_id="s1", mcp_tool="data.query", args={"q": "example"})],
    ).to_jsonld()


def _make_intent() -> Dict[str, Any]:
    from .acp import AgentPlan, PlanStep, build_intent
    plan = AgentPlan(
        plan_id="plan:example-001",
        principal="lct:web4:human:alice",
        agent="lct:web4:agent:assistant",
        grant_id="grant-001",
        steps=[PlanStep(step_id="s1", mcp_tool="data.query", args={"q": "example"})],
    )
    return build_intent(plan, "s1", explanation="Querying data").to_jsonld()


def _make_decision() -> Dict[str, Any]:
    from .acp import Decision, DecisionType
    return Decision(
        intent_id="intent-001",
        decision=DecisionType.APPROVE,
        decided_by="lct:web4:human:reviewer",
        rationale="Request is within policy bounds",
    ).to_jsonld()


def _make_execution_record() -> Dict[str, Any]:
    from .acp import ExecutionRecord
    return ExecutionRecord(
        record_id="rec:example-001",
        intent_id="intent-001",
        grant_id="grant-001",
        law_hash="law:policy:v1",
        mcp_call={"tool": "data.query", "args": {"q": "example"}},
        result_status="success",
        result_output={"rows": 42},
    ).to_jsonld()


def _make_entity_type_info() -> Dict[str, Any]:
    from .entity import get_info
    from .lct import EntityType as ET
    return get_info(ET.HUMAN).to_jsonld()


def _make_entity_type_registry() -> Dict[str, Any]:
    from .entity import entity_registry_to_jsonld
    return entity_registry_to_jsonld()


def _make_level_requirement() -> Dict[str, Any]:
    from .capability import CapabilityLevel, LevelRequirement
    return LevelRequirement(
        level=CapabilityLevel.BASIC,
        name="Basic",
        description="Basic capability level",
        requirements=["identity_verified"],
        trust_range=(0.3, 0.6),
    ).to_jsonld()


def _make_capability_assessment() -> Dict[str, Any]:
    from .capability import capability_assessment_to_jsonld
    from .lct import LCT
    from .lct import EntityType as ET
    lct = LCT.create(
        entity_type=ET.AI,
        public_key="example_key",
        witnesses=["w1"],
    )
    return capability_assessment_to_jsonld(lct)


def _make_capability_framework() -> Dict[str, Any]:
    from .capability import capability_framework_to_jsonld
    return capability_framework_to_jsonld()


def _make_dictionary_spec() -> Dict[str, Any]:
    from .dictionary import DictionarySpec, DictionaryType
    return DictionarySpec(
        source_domain="medical",
        target_domain="legal",
        dictionary_type=DictionaryType.DOMAIN,
    ).to_jsonld()


def _make_translation_result() -> Dict[str, Any]:
    from .dictionary import (
        DictionaryEntity,
        TranslationRequest,
    )
    entity = DictionaryEntity.create("medical", "legal", "dict_key_001")
    result = entity.record_translation(
        TranslationRequest("informed consent", "medical", "legal"),
        content="legally binding agreement to treatment",
        confidence=0.88,
    )
    return result.to_jsonld()


def _make_translation_chain() -> Dict[str, Any]:
    from .dictionary import TranslationChain
    chain = TranslationChain()
    chain.add_step("medical", "legal", "lct:dict:med-legal", 0.92)
    chain.add_step("legal", "regulatory", "lct:dict:legal-reg", 0.88)
    return chain.to_jsonld()


def _make_dictionary_entity() -> Dict[str, Any]:
    from .dictionary import DictionaryEntity
    return DictionaryEntity.create("medical", "legal", "dict_key_001").to_jsonld()


def _make_r7_action() -> Dict[str, Any]:
    from .r6 import build_action
    from .trust import T3, V3
    return build_action(
        actor="lct:web4:agent:analyzer",
        role_lct="role:data-analyst",
        action="analyze_dataset",
        target="customer_segments",
        t3=T3(0.82, 0.78, 0.85),
        v3=V3(0.70, 0.85, 0.80),
        atp_stake=15.0,
        available_atp=200.0,
    ).to_jsonld()


def _make_reputation_delta() -> Dict[str, Any]:
    from .r6 import build_action
    from .trust import T3, V3
    action = build_action(
        actor="lct:web4:agent:analyzer",
        role_lct="role:data-analyst",
        action="analyze_dataset",
        target="customer_segments",
        t3=T3(0.82, 0.78, 0.85),
        v3=V3(0.70, 0.85, 0.80),
    )
    return action.compute_reputation(quality=0.9).to_jsonld()


def _make_action_chain() -> Dict[str, Any]:
    from .r6 import ActionChain, ActionStatus, Result, build_action
    from .trust import T3, V3
    action = build_action(
        actor="lct:web4:agent:analyzer",
        role_lct="role:data-analyst",
        action="analyze_dataset",
        target="customer_segments",
        t3=T3(0.82, 0.78, 0.85),
        v3=V3(0.70, 0.85, 0.80),
    )
    action.result = Result(status=ActionStatus.SUCCESS, output={}, atp_consumed=5.0)
    chain = ActionChain()
    chain.append(action)
    return chain.to_jsonld()


def _make_lct() -> Dict[str, Any]:
    from .lct import LCT, EntityType
    lct = LCT.create(
        entity_type=EntityType.HUMAN,
        public_key="example_public_key_001",
        society="lct:web4:society:example",
        witnesses=["witness-1", "witness-2"],
    )
    return lct.to_jsonld()


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def _build_registry() -> Dict[str, Callable[[], Dict[str, Any]]]:
    """Build the type_name -> factory mapping."""
    return {
        "T3Tensor": _make_t3,
        "V3Tensor": _make_v3,
        "TrustQuery": _make_trust_query,
        "LinkedContextToken": _make_lct,
        "AttestationEnvelope": _make_attestation_envelope,
        "ATPAccount": _make_atp_account,
        "TransferResult": _make_transfer_result,
        "AgentPlan": _make_agent_plan,
        "Intent": _make_intent,
        "Decision": _make_decision,
        "ExecutionRecord": _make_execution_record,
        "EntityTypeInfo": _make_entity_type_info,
        "EntityTypeRegistry": _make_entity_type_registry,
        "LevelRequirement": _make_level_requirement,
        "CapabilityAssessment": _make_capability_assessment,
        "CapabilityFramework": _make_capability_framework,
        "DictionarySpec": _make_dictionary_spec,
        "TranslationResult": _make_translation_result,
        "TranslationChain": _make_translation_chain,
        "DictionaryEntity": _make_dictionary_entity,
        "R7Action": _make_r7_action,
        "ReputationDelta": _make_reputation_delta,
        "ActionChain": _make_action_chain,
    }


def _get_registry() -> Dict[str, Callable[[], Dict[str, Any]]]:
    """Return the registry, building it on first access."""
    global _registry  # noqa: PLW0603
    if _registry is None:
        _registry = _build_registry()
    return _registry


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate(type_name: str) -> Dict[str, Any]:
    """Generate a minimal valid JSON-LD document for the given web4 type.

    Args:
        type_name: The ``@type`` value (e.g. ``"T3Tensor"``, ``"R7Action"``).
            Both bare and ``web4:``-prefixed forms are accepted.

    Returns:
        A dict representing a valid JSON-LD document.

    Raises:
        UnsupportedTypeError: If *type_name* is not recognized.
    """
    # Strip web4: prefix if present
    bare = type_name.removeprefix("web4:")

    registry = _get_registry()
    factory = registry.get(bare)
    if factory is None:
        raise UnsupportedTypeError(type_name)
    return factory()


def generate_string(type_name: str, *, indent: int = 2) -> str:
    """Generate a minimal valid JSON-LD document as a formatted string.

    Args:
        type_name: The ``@type`` value.
        indent: JSON indentation level (default 2).

    Returns:
        A JSON string.
    """
    return json.dumps(generate(type_name), indent=indent)


def available_types() -> List[str]:
    """Return the sorted list of type names that :func:`generate` supports.

    Returns:
        Sorted list of bare type names (without ``web4:`` prefix).
    """
    return sorted(_get_registry().keys())


__all__ = [
    "UnsupportedTypeError",
    "available_types",
    "generate",
    "generate_string",
]
