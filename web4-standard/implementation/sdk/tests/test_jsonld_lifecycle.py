"""
Sprint 18 T1: JSON-LD document lifecycle integration tests.

Tests the full JSON-LD document lifecycle through the SDK's integrated
pipeline — NOT through direct schema loading or type-specific from_jsonld().

Pipeline under test:
    create object → to_jsonld() → web4.validation.validate()
                                → web4.from_jsonld() (generic dispatcher)
                                → verify round-trip fidelity

What this tests that existing tests DO NOT:
- test_jsonld_schema_roundtrip.py: uses direct jsonschema, NOT web4.validation
- test_jsonld_schema_roundtrip.py: uses type-specific from_jsonld(), NOT generic dispatcher
- test_deserialize.py: tests dispatcher with synthetic dicts, NOT real to_jsonld() output
- test_schema_validation_vectors.py: tests schemas with vectors, NOT SDK round-trip

This test proves that a JSON-LD document produced by one SDK instance can be
validated and consumed by another through the public SDK API — the core
interoperability guarantee.
"""

import json

import pytest

# ── Generic dispatcher and validation ────────────────────────────
from web4.deserialize import from_jsonld, from_jsonld_string, supported_types
from web4.validation import validate as sdk_validate, list_schemas

# ── SDK types used to construct test objects ──────────────────────
from web4.trust import T3, V3
from web4.lct import (
    LCT, EntityType, Attestation, LineageEntry,
)
from web4.attestation import (
    AttestationEnvelope, AnchorInfo, Proof, PlatformState,
)
from web4.atp import ATPAccount, TransferResult, transfer
from web4.r6 import (
    R7Action, ActionStatus, Rules, Role, Request, Result,
    ActionChain, ReputationDelta, build_action,
)
from web4.acp import (
    AgentPlan, PlanStep, Intent, Decision, DecisionType,
    ExecutionRecord, Guards, ResourceCaps, HumanApproval,
    ApprovalMode, Trigger, TriggerKind, build_intent,
)
from web4.entity import EntityType as ET, entity_registry_to_jsonld
from web4.capability import (
    CapabilityLevel, LevelRequirement,
    capability_assessment_to_jsonld, capability_framework_to_jsonld,
)
from web4.dictionary import (
    DictionaryEntity, DictionarySpec, DictionaryType,
    TranslationRequest, TranslationChain, TranslationResult,
    CompressionProfile, DomainCoverage,
)


# ═══════════════════════════════════════════════════════════════════
# Helper: type -> schema name mapping (mirrors __main__.py)
# ═══════════════════════════════════════════════════════════════════

_TYPE_SCHEMA = {
    "LinkedContextToken": "lct",
    "AttestationEnvelope": "attestation-envelope",
    "T3Tensor": "t3v3",
    "V3Tensor": "t3v3",
    "ATPAccount": "atp",
    "TransferResult": "atp",
    "AgentPlan": "acp",
    "Intent": "acp",
    "Decision": "acp",
    "ExecutionRecord": "acp",
    "EntityTypeInfo": "entity",
    "EntityTypeRegistry": "entity",
    "LevelRequirement": "capability",
    "CapabilityAssessment": "capability",
    "CapabilityFramework": "capability",
    "DictionarySpec": "dictionary",
    "TranslationResult": "dictionary",
    "TranslationChain": "dictionary",
    "DictionaryEntity": "dictionary",
    "R7Action": "r7-action",
    # Note: ReputationDelta and ActionChain have distinct @type values
    # but the r7-action JSON Schema only validates R7Action @type.
    # These types pass through the generic dispatcher but don't have
    # dedicated schema validation.
}


def _schema_for_type(type_name: str) -> str | None:
    """Get the schema name for a bare @type value."""
    return _TYPE_SCHEMA.get(type_name)


# ═══════════════════════════════════════════════════════════════════
# 1. Deep per-type lifecycle tests (representative types)
# ═══════════════════════════════════════════════════════════════════


class TestLCTLifecycle:
    """LCT: most complex type — nested MRH, attestations, birth cert."""

    def test_minimal_lct_lifecycle(self):
        """Minimal LCT: create → to_jsonld → validate → from_jsonld → verify."""
        lct = LCT.create(
            entity_type=EntityType.HUMAN,
            public_key="test_pub_key_001",
            society="lct:web4:society:test",
            witnesses=["w1", "w2"],
        )
        doc = lct.to_jsonld()

        restored = LCT.from_jsonld(doc)
        assert restored.lct_id == lct.lct_id
        assert restored.subject == lct.subject
        assert restored.binding.entity_type == lct.binding.entity_type
        assert restored.birth_certificate.issuing_society == lct.birth_certificate.issuing_society

        # Schema validation via SDK validate()
        result = sdk_validate(doc, "lct")
        assert result.valid, f"LCT validation failed: {result.errors}"

    def test_full_lct_with_attestations_and_lineage(self):
        """LCT with all optional fields: attestations, lineage, revocation."""
        lct = LCT.create(
            entity_type=EntityType.AI,
            public_key="ai_key_full_001",
            society="lct:web4:society:full",
            witnesses=["w1", "w2", "w3"],
            t3=T3(talent=0.85, training=0.92, temperament=0.78),
            v3=V3(valuation=0.89, veracity=0.91, validity=0.76),
        )
        lct.attestations = [
            Attestation(
                witness="lct:web4:witness:w1",
                type="identity_verification",
                claims={"level": "high", "method": "biometric"},
                ts="2026-01-01T00:00:00Z",
            ),
            Attestation(
                witness="lct:web4:witness:w2",
                type="skill_verification",
                claims={"domain": "NLP"},
                ts="2026-01-02T00:00:00Z",
            ),
        ]
        lct.lineage = [
            LineageEntry(
                parent="lct:web4:parent:genesis",
                reason="genesis",
                ts="2025-12-31T00:00:00Z",
            ),
        ]

        doc = lct.to_jsonld()
        result = sdk_validate(doc, "lct")
        assert result.valid, f"Full LCT validation failed: {result.errors}"

        restored = LCT.from_jsonld(doc)
        assert restored.t3.talent == pytest.approx(0.85)
        assert restored.v3.veracity == pytest.approx(0.91)
        assert len(restored.attestations) == 2
        assert restored.attestations[0].type == "identity_verification"
        assert len(restored.lineage) == 1
        assert restored.lineage[0].reason == "genesis"

    def test_lct_json_string_roundtrip(self):
        """LCT survives JSON string serialization/deserialization."""
        lct = LCT.create(
            entity_type=EntityType.DEVICE,
            public_key="device_key_001",
            society="lct:web4:society:iot",
            witnesses=["w1"],
            t3=T3(0.7, 0.8, 0.6),
        )
        doc = lct.to_jsonld()
        json_str = json.dumps(doc)
        doc_parsed = json.loads(json_str)
        restored = LCT.from_jsonld(doc_parsed)
        assert restored.lct_id == lct.lct_id
        assert restored.t3.composite == pytest.approx(lct.t3.composite)


class TestT3V3Lifecycle:
    """T3/V3 trust tensors — simple structures, test boundary values."""

    def test_t3_full_lifecycle(self):
        """T3 tensor: create → to_jsonld → validate → from_jsonld → verify."""
        t3 = T3(talent=0.85, training=0.92, temperament=0.78)
        doc = t3.to_jsonld()

        result = sdk_validate(doc, "t3v3")
        assert result.valid, f"T3 validation failed: {result.errors}"

        restored = from_jsonld(doc)
        assert isinstance(restored, T3)
        assert restored.talent == pytest.approx(0.85)
        assert restored.training == pytest.approx(0.92)
        assert restored.temperament == pytest.approx(0.78)
        assert restored.composite == pytest.approx(t3.composite)

    def test_v3_full_lifecycle(self):
        """V3 tensor: create → to_jsonld → validate → from_jsonld → verify."""
        v3 = V3(valuation=0.70, veracity=0.95, validity=0.80)
        doc = v3.to_jsonld()

        result = sdk_validate(doc, "t3v3")
        assert result.valid, f"V3 validation failed: {result.errors}"

        restored = from_jsonld(doc)
        assert isinstance(restored, V3)
        assert restored.valuation == pytest.approx(0.70)
        assert restored.veracity == pytest.approx(0.95)
        assert restored.validity == pytest.approx(0.80)

    def test_t3_boundary_values(self):
        """T3 with edge-case values (0.0, 1.0) round-trips correctly."""
        t3 = T3(talent=0.0, training=1.0, temperament=0.5)
        doc = t3.to_jsonld()
        result = sdk_validate(doc, "t3v3")
        assert result.valid

        restored = from_jsonld(doc)
        assert restored.talent == pytest.approx(0.0)
        assert restored.training == pytest.approx(1.0)
        assert restored.temperament == pytest.approx(0.5)

    def test_t3_json_string_roundtrip(self):
        """T3 survives JSON string path via from_jsonld_string()."""
        t3 = T3(talent=0.65, training=0.70, temperament=0.75)
        doc = t3.to_jsonld()
        json_str = json.dumps(doc)

        restored = from_jsonld_string(json_str)
        assert isinstance(restored, T3)
        assert restored.composite == pytest.approx(t3.composite)


class TestAttestationEnvelopeLifecycle:
    """AttestationEnvelope: hardware trust primitive with nested structures."""

    def test_software_envelope_lifecycle(self):
        """Software attestation: create → to_jsonld → validate → from_jsonld."""
        env = AttestationEnvelope(
            entity_id="lct://web4:test:agent@active",
            public_key="MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE_test",
            anchor=AnchorInfo(type="software"),
            proof=Proof(
                format="ecdsa_software",
                signature="MEUCIQD_test_sig",
                challenge="challenge-001",
            ),
            timestamp=1710864000.0,
            challenge_issued_at=1710863990.0,
            challenge_ttl=300.0,
            envelope_version="0.1",
        )
        doc = env.to_jsonld()

        result = sdk_validate(doc, "attestation-envelope")
        assert result.valid, f"AttestationEnvelope validation failed: {result.errors}"

        restored = from_jsonld(doc)
        assert isinstance(restored, AttestationEnvelope)
        assert restored.entity_id == env.entity_id
        assert restored.anchor.type == "software"
        assert restored.proof.challenge == "challenge-001"

    def test_tpm2_envelope_with_platform_state(self):
        """TPM2 attestation with full platform state round-trips correctly."""
        env = AttestationEnvelope(
            entity_id="lct://web4:hw:device@active",
            public_key="MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE_tpm",
            anchor=AnchorInfo(
                type="tpm2",
                manufacturer="Intel",
                model="INTC TPM2.0",
                firmware_version="1.38",
            ),
            proof=Proof(
                format="tpm2_quote",
                signature="MEUCIQD_tpm_quote_sig",
                challenge="challenge-tpm-002",
            ),
            platform_state=PlatformState(
                available=True,
                boot_verified=True,
                pcr_values={0: "sha256:aaa", 1: "sha256:bbb", 7: "sha256:ccc"},
            ),
            timestamp=1710864000.0,
            challenge_issued_at=1710863990.0,
            challenge_ttl=300.0,
            envelope_version="0.1",
        )
        doc = env.to_jsonld()
        result = sdk_validate(doc, "attestation-envelope")
        assert result.valid

        restored = from_jsonld(doc)
        assert restored.anchor.type == "tpm2"
        assert restored.anchor.manufacturer == "Intel"
        assert restored.platform_state is not None
        assert restored.platform_state.boot_verified is True


class TestATPLifecycle:
    """ATP accounts and transfer results — financial primitives."""

    def test_atp_account_lifecycle(self):
        """ATPAccount: create → to_jsonld → validate → from_jsonld."""
        account = ATPAccount(available=500.0)
        account.lock(100.0)
        account.commit(50.0)
        # Now: available=400, locked=50, adp=50

        doc = account.to_jsonld()
        result = sdk_validate(doc, "atp")
        assert result.valid, f"ATPAccount validation failed: {result.errors}"

        restored = from_jsonld(doc)
        assert isinstance(restored, ATPAccount)
        assert restored.available == pytest.approx(400.0)
        assert restored.adp == pytest.approx(50.0)

    def test_transfer_result_lifecycle(self):
        """TransferResult from a real transfer: serialize → validate → deserialize."""
        sender = ATPAccount(available=1000.0)
        receiver = ATPAccount(available=100.0)
        xfer_result = transfer(sender, receiver, 200.0, fee_rate=0.05)

        doc = xfer_result.to_jsonld()
        result = sdk_validate(doc, "atp")
        assert result.valid, f"TransferResult validation failed: {result.errors}"

        restored = from_jsonld(doc)
        assert isinstance(restored, TransferResult)
        assert restored.actual_credit == pytest.approx(xfer_result.actual_credit)
        assert restored.fee == pytest.approx(xfer_result.fee)


class TestR7ActionLifecycle:
    """R7 actions — complex type with nested components."""

    def test_r7_action_lifecycle(self):
        """R7Action from build_action: create → to_jsonld → validate → from_jsonld."""
        action = build_action(
            actor="lct:web4:agent:analyzer",
            role_lct="role:data-analyst",
            action="analyze_dataset",
            target="customer_segments",
            t3=T3(0.82, 0.78, 0.85),
            v3=V3(0.70, 0.85, 0.80),
            atp_stake=15.0,
            available_atp=200.0,
            permissions=["analyze", "read"],
            society="lct:web4:society:research",
            law_hash="law:research:v1",
        )
        doc = action.to_jsonld()
        result = sdk_validate(doc, "r7-action")
        assert result.valid, f"R7Action validation failed: {result.errors}"

        restored = from_jsonld(doc)
        assert isinstance(restored, R7Action)
        assert restored.role.actor == "lct:web4:agent:analyzer"
        assert restored.request.action == "analyze_dataset"

    def test_r7_action_with_result(self):
        """R7Action with completed result round-trips correctly."""
        action = build_action(
            actor="lct:web4:agent:worker",
            role_lct="role:worker",
            action="process",
            target="batch_001",
            t3=T3(0.7, 0.7, 0.7),
            v3=V3(0.7, 0.7, 0.7),
        )
        action.result = Result(
            status=ActionStatus.SUCCESS,
            output={"processed": 42, "quality": 0.95},
            atp_consumed=10.0,
        )

        doc = action.to_jsonld()
        result = sdk_validate(doc, "r7-action")
        assert result.valid

        restored = from_jsonld(doc)
        assert restored.result is not None
        assert restored.result.status == ActionStatus.SUCCESS

    def test_reputation_delta_lifecycle(self):
        """ReputationDelta from action.compute_reputation round-trips."""
        action = build_action(
            actor="lct:web4:agent:eval",
            role_lct="role:evaluator",
            action="evaluate",
            target="submission",
            t3=T3(0.85, 0.80, 0.90),
            v3=V3(0.75, 0.85, 0.80),
        )
        rep_delta = action.compute_reputation(quality=0.9, rule_triggered=False)

        doc = rep_delta.to_jsonld()
        # Note: ReputationDelta @type != R7Action, so r7-action schema
        # doesn't validate it directly. Test dispatcher + round-trip only.

        restored = from_jsonld(doc)
        assert isinstance(restored, ReputationDelta)
        assert restored.subject_lct == action.role.actor

    def test_action_chain_lifecycle(self):
        """ActionChain with two actions round-trips correctly."""
        a1 = build_action(
            actor="lct:web4:agent:chain",
            role_lct="role:processor",
            action="step_1",
            target="data",
            t3=T3(0.8, 0.8, 0.8),
            v3=V3(0.8, 0.8, 0.8),
        )
        a1.result = Result(status=ActionStatus.SUCCESS, output={"step": 1}, atp_consumed=5.0)

        a2 = build_action(
            actor="lct:web4:agent:chain",
            role_lct="role:processor",
            action="step_2",
            target="data",
            t3=T3(0.8, 0.8, 0.8),
            v3=V3(0.8, 0.8, 0.8),
        )
        a2.result = Result(status=ActionStatus.SUCCESS, output={"step": 2}, atp_consumed=3.0)

        chain = ActionChain()
        chain.append(a1)
        chain.append(a2)

        doc = chain.to_jsonld()
        # Note: ActionChain @type != R7Action, so r7-action schema
        # doesn't validate it. Test dispatcher + round-trip only.

        restored = from_jsonld(doc)
        assert isinstance(restored, ActionChain)
        assert restored.length == 2
        assert restored.verify_chain()


class TestACPLifecycle:
    """ACP types — complex nested plans with guards and triggers."""

    def test_agent_plan_lifecycle(self):
        """AgentPlan with steps, guards, triggers: full lifecycle."""
        plan = AgentPlan(
            plan_id="plan:lifecycle-test-001",
            principal="lct:web4:human:alice",
            agent="lct:web4:agent:bot",
            grant_id="grant-001",
            triggers=[Trigger(kind=TriggerKind.MANUAL, expr="user_request")],
            steps=[
                PlanStep(step_id="s1", mcp_tool="data.query",
                         args={"table": "sensors", "limit": 100}),
                PlanStep(step_id="s2", mcp_tool="data.transform",
                         args={"format": "json"}, depends_on=["s1"]),
            ],
            guards=Guards(
                law_hash="law:test:v1",
                resource_caps=ResourceCaps(max_atp=200.0, max_executions=10),
                witness_level=1,
                human_approval=HumanApproval(
                    mode=ApprovalMode.CONDITIONAL,
                    auto_threshold=100.0,
                ),
            ),
        )
        doc = plan.to_jsonld()
        result = sdk_validate(doc, "acp")
        assert result.valid, f"AgentPlan validation failed: {result.errors}"

        restored = from_jsonld(doc)
        assert isinstance(restored, AgentPlan)
        assert restored.plan_id == plan.plan_id
        assert restored.principal == "lct:web4:human:alice"
        assert len(restored.steps) == 2
        assert restored.steps[1].depends_on == ["s1"]
        assert restored.guards.resource_caps.max_atp == pytest.approx(200.0)

    def test_intent_lifecycle(self):
        """Intent built from a plan: create → to_jsonld → from_jsonld."""
        plan = AgentPlan(
            plan_id="plan:intent-test",
            principal="lct:web4:human:bob",
            agent="lct:web4:agent:helper",
            grant_id="grant-002",
            steps=[PlanStep(step_id="s1", mcp_tool="tool.run", args={})],
        )
        intent = build_intent(plan, "s1", explanation="Test intent lifecycle")

        doc = intent.to_jsonld()
        result = sdk_validate(doc, "acp")
        assert result.valid, f"Intent validation failed: {result.errors}"

        restored = from_jsonld(doc)
        assert isinstance(restored, Intent)
        assert restored.plan_id == plan.plan_id
        assert restored.explanation == "Test intent lifecycle"

    def test_decision_lifecycle(self):
        """Decision: approve an intent and round-trip."""
        decision = Decision(
            intent_id="intent-001",
            decision=DecisionType.APPROVE,
            decided_by="lct:web4:human:approver",
            rationale="Looks good, proceed",
            witnesses=["lct:web4:witness:w1"],
        )
        doc = decision.to_jsonld()
        result = sdk_validate(doc, "acp")
        assert result.valid, f"Decision validation failed: {result.errors}"

        restored = from_jsonld(doc)
        assert isinstance(restored, Decision)
        assert restored.decision == DecisionType.APPROVE
        assert restored.rationale == "Looks good, proceed"

    def test_execution_record_lifecycle(self):
        """ExecutionRecord: record execution and round-trip."""
        record = ExecutionRecord(
            record_id="rec:lifecycle-001",
            intent_id="intent-001",
            grant_id="grant-002",
            law_hash="law:test:v1",
            mcp_call={"tool": "data.query", "args": {"table": "sensors"}},
            result_status="success",
            result_output={"rows": 42},
            resources_consumed={"atp": 15.0},
            witnesses=["lct:web4:witness:w1"],
        )
        doc = record.to_jsonld()
        result = sdk_validate(doc, "acp")
        assert result.valid, f"ExecutionRecord validation failed: {result.errors}"

        restored = from_jsonld(doc)
        assert isinstance(restored, ExecutionRecord)
        assert restored.record_id == "rec:lifecycle-001"
        assert restored.result_status == "success"
        assert restored.resources_consumed == {"atp": 15.0}


class TestDictionaryLifecycle:
    """Dictionary types — entity with coverage, compression, translations."""

    def test_dictionary_entity_lifecycle(self):
        """DictionaryEntity: full lifecycle with coverage and compression."""
        entity = DictionaryEntity.create(
            source_domain="medical",
            target_domain="legal",
            public_key="dict_key_001",
            bidirectional=False,
            coverage=DomainCoverage(terms=500, concepts=120, relationships=80),
            compression=CompressionProfile(average_ratio=0.6, lossy_threshold=0.1),
            t3=T3(0.85, 0.90, 0.80),
            v3=V3(0.80, 0.85, 0.75),
        )
        doc = entity.to_jsonld()
        result = sdk_validate(doc, "dictionary")
        assert result.valid, f"DictionaryEntity validation failed: {result.errors}"

        restored = from_jsonld(doc)
        assert isinstance(restored, DictionaryEntity)
        assert restored.spec.source_domain == "medical"
        assert restored.spec.target_domain == "legal"
        assert not restored.spec.bidirectional
        # Note: T3/V3 are NOT in JSON-LD output (DictionaryEntity.to_jsonld()
        # serializes spec + translation stats, not trust tensors).
        # Also, lct_id is derived from constructor params so may differ
        # if from_jsonld re-derives it. Verify spec fields instead.
        assert restored.translation_count == 0

    def test_translation_chain_lifecycle(self):
        """TranslationChain with multiple steps round-trips correctly."""
        chain = TranslationChain()
        chain.add_step("medical", "legal", "lct:dict:med-legal", 0.92)
        chain.add_step("legal", "regulatory", "lct:dict:legal-reg", 0.88)

        doc = chain.to_jsonld()
        result = sdk_validate(doc, "dictionary")
        assert result.valid, f"TranslationChain validation failed: {result.errors}"

        restored = from_jsonld(doc)
        assert isinstance(restored, TranslationChain)
        assert restored.length == 2
        assert restored.cumulative_confidence == pytest.approx(0.92 * 0.88, abs=0.001)


# ═══════════════════════════════════════════════════════════════════
# 2. Parametrized dispatcher test: all 22 types through from_jsonld()
# ═══════════════════════════════════════════════════════════════════


def _make_lct_doc() -> dict:
    return LCT.create(entity_type=EntityType.AI, public_key="test-key").to_jsonld()


def _make_t3_doc() -> dict:
    return T3(0.8, 0.8, 0.8).to_jsonld()


def _make_v3_doc() -> dict:
    return V3(0.8, 0.8, 0.8).to_jsonld()


def _make_attestation_doc() -> dict:
    return AttestationEnvelope(
        entity_id="lct://web4:test@active",
        public_key="test_key",
        anchor=AnchorInfo(type="software"),
        proof=Proof(format="ecdsa_software", signature="sig", challenge="ch"),
        timestamp=1710864000.0,
        challenge_issued_at=1710863990.0,
        challenge_ttl=300.0,
        envelope_version="0.1",
    ).to_jsonld()


def _make_atp_account_doc() -> dict:
    return ATPAccount(available=100.0).to_jsonld()


def _make_transfer_result_doc() -> dict:
    s, r = ATPAccount(available=100.0), ATPAccount(available=0.0)
    return transfer(s, r, 50.0).to_jsonld()


def _make_agent_plan_doc() -> dict:
    return AgentPlan(
        plan_id="p1", principal="pr1", agent="ag1", grant_id="g1",
        steps=[PlanStep(step_id="s1", mcp_tool="tool", args={})],
    ).to_jsonld()


def _make_intent_doc() -> dict:
    plan = AgentPlan(
        plan_id="p1", principal="pr1", agent="ag1", grant_id="g1",
        steps=[PlanStep(step_id="s1", mcp_tool="tool", args={})],
    )
    return build_intent(plan, "s1").to_jsonld()


def _make_decision_doc() -> dict:
    return Decision(
        intent_id="i1", decision=DecisionType.APPROVE,
        decided_by="approver",
    ).to_jsonld()


def _make_execution_record_doc() -> dict:
    return ExecutionRecord(
        record_id="r1", intent_id="i1", grant_id="g1",
        law_hash="law1", mcp_call={"tool": "t"}, result_status="success",
    ).to_jsonld()


def _make_entity_info_doc() -> dict:
    from web4.entity import get_info
    return get_info(ET.HUMAN).to_jsonld()


def _make_entity_registry_doc() -> dict:
    return entity_registry_to_jsonld()


def _make_level_requirement_doc() -> dict:
    return LevelRequirement(
        level=CapabilityLevel.BASIC,
        name="Basic",
        description="Basic capability level",
        requirements=["identity_verified"],
        trust_range=(0.3, 0.6),
    ).to_jsonld()


def _make_capability_assessment_doc() -> dict:
    lct = LCT.create(entity_type=EntityType.AI, public_key="k1", witnesses=["w1"])
    return capability_assessment_to_jsonld(lct)


def _make_capability_framework_doc() -> dict:
    return capability_framework_to_jsonld()


def _make_dictionary_spec_doc() -> dict:
    return DictionarySpec(
        source_domain="tech", target_domain="business",
        dictionary_type=DictionaryType.DOMAIN,
    ).to_jsonld()


def _make_translation_result_doc() -> dict:
    entity = DictionaryEntity.create("tech", "biz", "k1")
    result = entity.record_translation(
        TranslationRequest("API rate limit", "tech", "biz"),
        content="Usage cap reached", confidence=0.85,
    )
    return result.to_jsonld()


def _make_translation_chain_doc() -> dict:
    chain = TranslationChain()
    chain.add_step("a", "b", "dict1", 0.9)
    return chain.to_jsonld()


def _make_dictionary_entity_doc() -> dict:
    return DictionaryEntity.create("tech", "biz", "k1").to_jsonld()


def _make_r7_action_doc() -> dict:
    return build_action(
        actor="a1", role_lct="r1", action="act", target="tgt",
        t3=T3(0.8, 0.8, 0.8), v3=V3(0.8, 0.8, 0.8),
    ).to_jsonld()


def _make_reputation_delta_doc() -> dict:
    action = build_action(
        actor="a1", role_lct="r1", action="act", target="tgt",
        t3=T3(0.8, 0.8, 0.8), v3=V3(0.8, 0.8, 0.8),
    )
    return action.compute_reputation(quality=0.9).to_jsonld()


def _make_action_chain_doc() -> dict:
    a1 = build_action(
        actor="a1", role_lct="r1", action="a", target="t",
        t3=T3(0.8, 0.8, 0.8), v3=V3(0.8, 0.8, 0.8),
    )
    a1.result = Result(status=ActionStatus.SUCCESS, output={}, atp_consumed=1.0)
    chain = ActionChain()
    chain.append(a1)
    return chain.to_jsonld()


def _make_trust_query_doc() -> dict:
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


_ALL_DISPATCHER_TYPES = [
    ("LinkedContextToken", _make_lct_doc),
    ("T3Tensor", _make_t3_doc),
    ("V3Tensor", _make_v3_doc),
    ("AttestationEnvelope", _make_attestation_doc),
    ("ATPAccount", _make_atp_account_doc),
    ("TransferResult", _make_transfer_result_doc),
    ("AgentPlan", _make_agent_plan_doc),
    ("Intent", _make_intent_doc),
    ("Decision", _make_decision_doc),
    ("ExecutionRecord", _make_execution_record_doc),
    ("EntityTypeInfo", _make_entity_info_doc),
    ("EntityTypeRegistry", _make_entity_registry_doc),
    ("LevelRequirement", _make_level_requirement_doc),
    ("CapabilityAssessment", _make_capability_assessment_doc),
    ("CapabilityFramework", _make_capability_framework_doc),
    ("DictionarySpec", _make_dictionary_spec_doc),
    ("TranslationResult", _make_translation_result_doc),
    ("TranslationChain", _make_translation_chain_doc),
    ("DictionaryEntity", _make_dictionary_entity_doc),
    ("R7Action", _make_r7_action_doc),
    ("ReputationDelta", _make_reputation_delta_doc),
    ("ActionChain", _make_action_chain_doc),
    ("TrustQuery", _make_trust_query_doc),
]


@pytest.mark.parametrize(
    "type_name,factory",
    _ALL_DISPATCHER_TYPES,
    ids=[t[0] for t in _ALL_DISPATCHER_TYPES],
)
def test_generic_dispatcher_with_real_to_jsonld(type_name: str, factory):
    """Every type's to_jsonld() output is accepted by the generic from_jsonld() dispatcher."""
    doc = factory()
    assert "@type" in doc, f"{type_name} to_jsonld() output has no @type"

    # Generic dispatcher produces an object (type correctness tested per-class above)
    obj = from_jsonld(doc)
    assert obj is not None, f"from_jsonld() returned None for {type_name}"


@pytest.mark.parametrize(
    "type_name,factory",
    [(t, f) for t, f in _ALL_DISPATCHER_TYPES if _schema_for_type(t) is not None],
    ids=[t for t, _ in _ALL_DISPATCHER_TYPES if _schema_for_type(t) is not None],
)
def test_sdk_validate_with_real_to_jsonld(type_name: str, factory):
    """Every type's to_jsonld() output passes web4.validation.validate()."""
    doc = factory()
    schema_name = _schema_for_type(type_name)
    assert schema_name is not None

    result = sdk_validate(doc, schema_name)
    assert result.valid, f"{type_name} failed {schema_name} validation: {result.errors}"


# ═══════════════════════════════════════════════════════════════════
# 3. Cross-module composition: serialize intermediate state
# ═══════════════════════════════════════════════════════════════════


class TestCrossModuleDocumentExchange:
    """
    Simulate a workflow where different components produce and consume
    JSON-LD documents — proving the interoperability guarantee.

    Scenario: An R7Action is created, its trust tensors are extracted and
    serialized independently, the action itself is serialized, then
    everything is reconstructed from the serialized documents alone.
    """

    def test_action_tensor_extraction_and_reconstruction(self):
        """
        Workflow:
        1. Create an R7Action with T3/V3
        2. Serialize T3, V3, and the action as separate JSON-LD documents
        3. Validate each document with SDK validation
        4. Deserialize each via generic dispatcher
        5. Verify the reconstructed tensors match the action's tensors
        """
        # 1. Create action
        t3 = T3(talent=0.85, training=0.92, temperament=0.78)
        v3 = V3(valuation=0.70, veracity=0.88, validity=0.82)
        action = build_action(
            actor="lct:web4:agent:composer",
            role_lct="role:analyst",
            action="analyze",
            target="dataset",
            t3=t3, v3=v3,
            atp_stake=20.0,
            available_atp=500.0,
        )

        # 2. Serialize each piece independently
        t3_doc = t3.to_jsonld()
        v3_doc = v3.to_jsonld()
        action_doc = action.to_jsonld()

        # 3. Validate all three
        assert sdk_validate(t3_doc, "t3v3").valid
        assert sdk_validate(v3_doc, "t3v3").valid
        assert sdk_validate(action_doc, "r7-action").valid

        # 4. Deserialize via generic dispatcher
        t3_restored = from_jsonld(t3_doc)
        v3_restored = from_jsonld(v3_doc)
        action_restored = from_jsonld(action_doc)

        # 5. Verify consistency
        assert isinstance(t3_restored, T3)
        assert isinstance(v3_restored, V3)
        assert isinstance(action_restored, R7Action)

        assert t3_restored.talent == pytest.approx(t3.talent)
        assert t3_restored.training == pytest.approx(t3.training)
        assert v3_restored.veracity == pytest.approx(v3.veracity)

    def test_plan_to_intent_to_decision_lifecycle(self):
        """
        ACP lifecycle as separate serialized documents:
        1. Create plan, serialize it
        2. Build intent from plan, serialize it
        3. Create decision, serialize it
        4. Deserialize all three from JSON-LD and verify relationships
        """
        # Plan
        plan = AgentPlan(
            plan_id="plan:compose-001",
            principal="lct:web4:human:planner",
            agent="lct:web4:agent:executor",
            grant_id="grant-compose-001",
            steps=[
                PlanStep(step_id="s1", mcp_tool="data.query", args={"q": "SELECT *"}),
                PlanStep(step_id="s2", mcp_tool="data.export", args={}, depends_on=["s1"]),
            ],
            guards=Guards(law_hash="law:compose:v1"),
        )
        plan_doc = plan.to_jsonld()

        # Intent from plan
        intent = build_intent(plan, "s1", explanation="Query all data")
        intent_doc = intent.to_jsonld()

        # Decision for intent
        decision = Decision(
            intent_id=intent.intent_id,
            decision=DecisionType.APPROVE,
            decided_by="lct:web4:human:planner",
            rationale="Within resource caps",
        )
        decision_doc = decision.to_jsonld()

        # Validate all
        assert sdk_validate(plan_doc, "acp").valid
        assert sdk_validate(intent_doc, "acp").valid
        assert sdk_validate(decision_doc, "acp").valid

        # Deserialize via generic dispatcher
        plan_r = from_jsonld(plan_doc)
        intent_r = from_jsonld(intent_doc)
        decision_r = from_jsonld(decision_doc)

        # Verify cross-document relationships
        assert isinstance(plan_r, AgentPlan)
        assert isinstance(intent_r, Intent)
        assert isinstance(decision_r, Decision)

        assert intent_r.plan_id == plan_r.plan_id
        assert decision_r.intent_id == intent_r.intent_id
        assert decision_r.decision == DecisionType.APPROVE

    def test_json_string_roundtrip_all_types(self):
        """
        Verify from_jsonld_string() works for representative types.
        This tests the JSON serialization boundary that external systems
        would cross when exchanging documents.
        """
        docs = [
            T3(0.8, 0.8, 0.8).to_jsonld(),
            V3(0.7, 0.7, 0.7).to_jsonld(),
            ATPAccount(available=100.0).to_jsonld(),
            Decision(intent_id="i1", decision=DecisionType.DENY, decided_by="d1").to_jsonld(),
        ]

        for doc in docs:
            type_name = doc["@type"]
            json_str = json.dumps(doc)
            restored = from_jsonld_string(json_str)
            assert restored is not None, f"from_jsonld_string failed for {type_name}"


# ═══════════════════════════════════════════════════════════════════
# 4. Consistency: dispatcher types == supported_types()
# ═══════════════════════════════════════════════════════════════════


class TestDispatcherCompleteness:
    """Verify dispatcher metadata is consistent with test coverage."""

    def test_supported_types_count(self):
        """supported_types() returns the expected 23 types."""
        types = supported_types()
        assert len(types) == 23, f"Expected 23 types, got {len(types)}: {types}"

    def test_all_dispatcher_types_in_supported(self):
        """Every type tested in the parametrized suite is in supported_types()."""
        supported = set(supported_types())
        tested = {t for t, _ in _ALL_DISPATCHER_TYPES}
        missing = tested - supported
        assert not missing, f"Types tested but not in supported_types(): {missing}"

    def test_all_json_ld_schemas_available(self):
        """All JSON-LD schemas in list_schemas() are accessible."""
        schemas = list_schemas()
        jsonld_schemas = [s for s in schemas if not s.endswith("-raw") and s != "trust-query"]
        assert len(jsonld_schemas) == 9, f"Expected 9 JSON-LD schemas, got {len(jsonld_schemas)}"
