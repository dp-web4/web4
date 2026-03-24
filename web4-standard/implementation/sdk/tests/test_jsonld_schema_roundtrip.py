"""
B4: Schema-validated JSON-LD round-trip tests.

For each of the 10 JSON-LD types, this test:
1. Constructs a representative object
2. Calls to_jsonld()
3. Validates the output against the corresponding JSON Schema
4. Calls from_jsonld() on the output
5. Asserts the round-tripped object matches the original

This is the programmatic schema validation layer that was missing from
per-module tests. It catches schema/code drift.
"""

import json
import os

import jsonschema
import pytest

# ── Schema loading ──────────────────────────────────────────────────

SCHEMA_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..",
    "schemas",
)


def load_schema(filename: str) -> dict:
    """Load a JSON Schema file from the schemas directory."""
    path = os.path.join(SCHEMA_DIR, filename)
    with open(path) as f:
        return json.load(f)


def validate(doc: dict, schema: dict) -> None:
    """Validate a JSON-LD document against its schema."""
    jsonschema.validate(doc, schema)


# ── 1. LCT ──────────────────────────────────────────────────────────

from web4.lct import (
    LCT, EntityType, Attestation, BirthCertificate, LineageEntry,
    LCT_JSONLD_CONTEXT,
)
from web4.trust import T3, V3


class TestLCTSchemaRoundtrip:
    """LCT to_jsonld() schema validation and round-trip."""

    @pytest.fixture
    def schema(self):
        return load_schema("lct-jsonld.schema.json")

    def _make_lct(self) -> LCT:
        return LCT.create(
            entity_type=EntityType.AI,
            public_key="mb64:testkey123456789",
            society="lct:web4:society:testnet",
            context="platform",
            witnesses=["lct:web4:witness:w1", "lct:web4:witness:w2", "lct:web4:witness:w3"],
            timestamp="2025-10-01T00:00:00Z",
            t3=T3(talent=0.85, training=0.92, temperament=0.78),
            v3=V3(valuation=0.89, veracity=0.91, validity=0.76),
        )

    def test_minimal_lct_validates(self, schema):
        """Minimal LCT to_jsonld() passes schema validation."""
        lct = self._make_lct()
        doc = lct.to_jsonld()
        validate(doc, schema)

    def test_full_lct_validates(self, schema):
        """LCT with attestations and lineage passes schema validation."""
        lct = self._make_lct()
        lct.attestations = [
            Attestation(
                witness="lct:web4:attestor:a1",
                type="identity_verification",
                claims={"level": "high"},
                ts="2025-10-01T01:00:00Z",
            ),
        ]
        lct.lineage = [
            LineageEntry(
                parent="lct:web4:parent:p1",
                reason="derived_from",
                ts="2025-09-30T00:00:00Z",
            ),
        ]
        doc = lct.to_jsonld()
        validate(doc, schema)

    def test_roundtrip(self, schema):
        """to_jsonld → validate → from_jsonld preserves state."""
        lct = self._make_lct()
        doc = lct.to_jsonld()
        validate(doc, schema)

        restored = LCT.from_jsonld(doc)
        assert restored.lct_id == lct.lct_id
        assert restored.subject == lct.subject
        assert restored.t3.talent == lct.t3.talent
        assert restored.v3.veracity == lct.v3.veracity


# ── 2. AttestationEnvelope ──────────────────────────────────────────

from web4.attestation import (
    AttestationEnvelope, AnchorInfo, Proof, PlatformState,
    ATTESTATION_JSONLD_CONTEXT,
)


class TestAttestationEnvelopeSchemaRoundtrip:
    """AttestationEnvelope to_jsonld() schema validation and round-trip."""

    @pytest.fixture
    def schema(self):
        return load_schema("attestation-envelope-jsonld.schema.json")

    def _make_envelope(self, **overrides) -> AttestationEnvelope:
        defaults = dict(
            entity_id="lct://web4:test:agent@active",
            public_key="MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE_test_key",
            anchor=AnchorInfo(type="software"),
            proof=Proof(
                format="ecdsa_software",
                signature="MEUCIQD_test_sig",
                challenge="challenge-abc-123",
            ),
            timestamp=1710864000.0,
            challenge_issued_at=1710863990.0,
            challenge_ttl=300.0,
            envelope_version="0.1",
        )
        defaults.update(overrides)
        return AttestationEnvelope(**defaults)

    def test_software_envelope_validates(self, schema):
        """Software anchor envelope passes schema validation."""
        env = self._make_envelope()
        doc = env.to_jsonld()
        validate(doc, schema)

    def test_tpm2_envelope_validates(self, schema):
        """TPM2 anchor envelope with platform state passes schema validation."""
        env = self._make_envelope(
            anchor=AnchorInfo(
                type="tpm2",
                manufacturer="Intel",
                firmware_version="1.38",
            ),
            proof=Proof(
                format="tpm2_quote",
                signature="MEUCIQD_tpm_sig",
                challenge="challenge-tpm-456",
            ),
            platform_state=PlatformState(
                available=True,
                boot_verified=True,
                pcr_values={0: "sha256:abc", 1: "sha256:def", 7: "sha256:ghi"},
            ),
        )
        doc = env.to_jsonld()
        validate(doc, schema)

    def test_roundtrip(self, schema):
        """to_jsonld → validate → from_jsonld preserves state."""
        env = self._make_envelope()
        doc = env.to_jsonld()
        validate(doc, schema)

        restored = AttestationEnvelope.from_jsonld(doc)
        assert restored.entity_id == env.entity_id
        assert restored.anchor.type == env.anchor.type
        assert restored.proof.challenge == env.proof.challenge


# ── 3. T3 ───────────────────────────────────────────────────────────

from web4.trust import T3_JSONLD_CONTEXT, V3_JSONLD_CONTEXT


class TestT3SchemaRoundtrip:
    """T3 to_jsonld() schema validation and round-trip."""

    @pytest.fixture
    def schema(self):
        return load_schema("t3v3-jsonld.schema.json")

    def test_default_t3_validates(self, schema):
        """Default T3 passes schema validation."""
        t3 = T3()
        doc = t3.to_jsonld()
        validate(doc, schema)

    def test_custom_t3_validates(self, schema):
        """T3 with custom values passes schema validation."""
        t3 = T3(talent=0.9, training=0.1, temperament=0.5)
        doc = t3.to_jsonld()
        validate(doc, schema)

    def test_t3_with_entity_validates(self, schema):
        """T3 with entity/role binding passes schema validation."""
        t3 = T3(talent=0.8, training=0.7, temperament=0.6)
        doc = t3.to_jsonld(entity="lct:alice", role="analyst")
        validate(doc, schema)

    def test_roundtrip(self, schema):
        """to_jsonld → validate → from_jsonld preserves state."""
        t3 = T3(talent=0.85, training=0.72, temperament=0.93)
        doc = t3.to_jsonld()
        validate(doc, schema)

        restored = T3.from_jsonld(doc)
        assert restored.talent == t3.talent
        assert restored.training == t3.training
        assert restored.temperament == t3.temperament


# ── 4. V3 ───────────────────────────────────────────────────────────


class TestV3SchemaRoundtrip:
    """V3 to_jsonld() schema validation and round-trip."""

    @pytest.fixture
    def schema(self):
        return load_schema("t3v3-jsonld.schema.json")

    def test_default_v3_validates(self, schema):
        """Default V3 passes schema validation."""
        v3 = V3()
        doc = v3.to_jsonld()
        validate(doc, schema)

    def test_custom_v3_validates(self, schema):
        """V3 with custom values passes schema validation."""
        v3 = V3(valuation=0.95, veracity=0.88, validity=0.72)
        doc = v3.to_jsonld()
        validate(doc, schema)

    def test_roundtrip(self, schema):
        """to_jsonld → validate → from_jsonld preserves state."""
        v3 = V3(valuation=0.65, veracity=0.78, validity=0.91)
        doc = v3.to_jsonld()
        validate(doc, schema)

        restored = V3.from_jsonld(doc)
        assert restored.valuation == v3.valuation
        assert restored.veracity == v3.veracity
        assert restored.validity == v3.validity


# ── 5. R7Action ─────────────────────────────────────────────────────

from web4.r6 import (
    R7Action, build_action, R7_JSONLD_CONTEXT,
    ActionChain, ReputationDelta,
)


class TestR7ActionSchemaRoundtrip:
    """R7Action to_jsonld() schema validation and round-trip."""

    @pytest.fixture
    def schema(self):
        return load_schema("r7-action-jsonld.schema.json")

    def _make_action(self) -> R7Action:
        return build_action(
            actor="lct:web4:entity:alice",
            role_lct="lct:web4:role:analyst:abc123",
            action="analyze_dataset",
            target="data:sales:q4",
            t3=T3(0.85, 0.90, 0.88),
            v3=V3(0.89, 0.91, 0.76),
            atp_stake=10.0,
            available_atp=100.0,
            permissions=["analyze_dataset", "read_data"],
        )

    def test_minimal_action_validates(self, schema):
        """Minimal R7Action passes schema validation."""
        action = build_action(
            actor="lct:alice",
            role_lct="lct:role:reader",
            action="read",
            target="data:test",
        )
        doc = action.to_jsonld()
        validate(doc, schema)

    def test_full_action_validates(self, schema):
        """Full R7Action with reputation passes schema validation."""
        action = self._make_action()
        action.compute_reputation(quality=0.85)
        doc = action.to_jsonld()
        validate(doc, schema)

    def test_roundtrip(self, schema):
        """to_jsonld → validate → from_jsonld preserves state."""
        action = self._make_action()
        doc = action.to_jsonld()
        validate(doc, schema)

        restored = R7Action.from_jsonld(doc)
        assert restored.action_id == action.action_id
        assert restored.role.actor == action.role.actor
        assert restored.request.action == action.request.action


# ── 6. ATPAccount ───────────────────────────────────────────────────

from web4.atp import ATPAccount, TransferResult, ATP_JSONLD_CONTEXT, transfer


class TestATPAccountSchemaRoundtrip:
    """ATPAccount to_jsonld() schema validation and round-trip."""

    @pytest.fixture
    def schema(self):
        return load_schema("atp-jsonld.schema.json")

    def test_empty_account_validates(self, schema):
        """Default empty account passes schema validation."""
        acct = ATPAccount()
        doc = acct.to_jsonld()
        validate(doc, schema)

    def test_funded_account_validates(self, schema):
        """Funded account passes schema validation."""
        acct = ATPAccount(available=1000.0, locked=200.0, initial_balance=1200.0)
        doc = acct.to_jsonld()
        validate(doc, schema)

    def test_roundtrip(self, schema):
        """to_jsonld → validate → from_jsonld preserves state."""
        acct = ATPAccount(available=500.0, locked=50.0, adp=30.0, initial_balance=580.0)
        doc = acct.to_jsonld()
        validate(doc, schema)

        restored = ATPAccount.from_jsonld(doc)
        assert restored.available == acct.available
        assert restored.locked == acct.locked
        assert restored.adp == acct.adp


# ── 7. TransferResult ───────────────────────────────────────────────


class TestTransferResultSchemaRoundtrip:
    """TransferResult to_jsonld() schema validation and round-trip."""

    @pytest.fixture
    def schema(self):
        return load_schema("atp-jsonld.schema.json")

    def test_successful_transfer_validates(self, schema):
        """Successful transfer result passes schema validation."""
        sender = ATPAccount(available=100.0, initial_balance=100.0)
        receiver = ATPAccount(available=50.0, initial_balance=50.0)
        result = transfer(sender, receiver, 25.0)
        doc = result.to_jsonld()
        validate(doc, schema)

    def test_roundtrip(self, schema):
        """to_jsonld → validate → from_jsonld preserves state."""
        sender = ATPAccount(available=100.0, initial_balance=100.0)
        receiver = ATPAccount(available=50.0, initial_balance=50.0)
        result = transfer(sender, receiver, 25.0)
        doc = result.to_jsonld()
        validate(doc, schema)

        restored = TransferResult.from_jsonld(doc)
        assert restored.fee == result.fee
        assert restored.sender_balance == result.sender_balance
        assert restored.actual_credit == result.actual_credit


# ── 8. ACP Types ────────────────────────────────────────────────────

from web4.acp import (
    ACP_JSONLD_CONTEXT,
    AgentPlan, PlanStep, Trigger, TriggerKind,
    Guards, ResourceCaps, HumanApproval, ApprovalMode,
    ProofOfAgency, Intent, Decision, DecisionType, ExecutionRecord,
)


def _make_plan(**overrides) -> AgentPlan:
    defaults = dict(
        plan_id="plan-001",
        principal="lct:principal:abc",
        agent="lct:agent:xyz",
        grant_id="grant-001",
        steps=[PlanStep(step_id="s1", mcp_tool="invoice.search", args={"q": "test"})],
        guards=Guards(
            law_hash="abc123",
            witness_level=2,
            resource_caps=ResourceCaps(max_atp=100.0, max_executions=10, rate_limit="5/hour"),
            human_approval=HumanApproval(
                mode=ApprovalMode.CONDITIONAL,
                auto_threshold=50.0,
                timeout=7200,
                fallback="deny",
            ),
            expires_at="2026-12-31T23:59:59+00:00",
        ),
        triggers=[Trigger(kind=TriggerKind.CRON, expr="0 * * * *")],
        created_at="2026-03-21T18:00:00+00:00",
    )
    defaults.update(overrides)
    return AgentPlan(**defaults)


def _make_intent(**overrides) -> Intent:
    defaults = dict(
        intent_id="acp:intent:abc123",
        plan_id="plan-001",
        step_id="s1",
        proposed_action={"mcp": "invoice.search", "args": {"q": "test"}},
        proof=ProofOfAgency(
            grant_id="grant-001",
            plan_id="plan-001",
            intent_id="acp:intent:abc123",
            nonce="fixed_nonce_1234",
        ),
        explanation="Search for matching invoices",
        confidence=0.85,
        risk_assessment="low",
        needs_approval=False,
        created_at="2026-03-21T18:00:00+00:00",
    )
    defaults.update(overrides)
    return Intent(**defaults)


def _make_decision(**overrides) -> Decision:
    defaults = dict(
        intent_id="acp:intent:abc123",
        decision=DecisionType.APPROVE,
        decided_by="lct:reviewer:r1",
        rationale="Action is within policy bounds",
        witnesses=["lct:witness:w1", "lct:witness:w2"],
        timestamp="2026-03-21T18:01:00+00:00",
    )
    defaults.update(overrides)
    return Decision(**defaults)


def _make_execution_record(**overrides) -> ExecutionRecord:
    defaults = dict(
        record_id="rec-001",
        intent_id="acp:intent:abc123",
        grant_id="grant-001",
        law_hash="abc123",
        mcp_call={"resource": "invoice.search", "args": {"q": "test"}},
        result_status="success",
        result_output={"invoices": [{"id": "inv-1", "amount": 42.0}]},
        resources_consumed={"atp": 5.0, "time_ms": 120},
        t3v3_delta={"talent": 0.01},
        witnesses=["lct:witness:w1"],
        timestamp="2026-03-21T18:02:00+00:00",
    )
    defaults.update(overrides)
    return ExecutionRecord(**defaults)


class TestACPSchemaRoundtrip:
    """ACP types to_jsonld() schema validation and round-trip."""

    @pytest.fixture
    def schema(self):
        return load_schema("acp-jsonld.schema.json")

    def test_agent_plan_validates(self, schema):
        """AgentPlan to_jsonld() passes schema validation."""
        plan = _make_plan()
        doc = plan.to_jsonld()
        validate(doc, schema)

    def test_agent_plan_roundtrip(self, schema):
        """AgentPlan to_jsonld → from_jsonld preserves state."""
        plan = _make_plan()
        doc = plan.to_jsonld()
        validate(doc, schema)

        restored = AgentPlan.from_jsonld(doc)
        assert restored.plan_id == plan.plan_id
        assert restored.principal == plan.principal
        assert restored.agent == plan.agent

    def test_intent_validates(self, schema):
        """Intent to_jsonld() passes schema validation."""
        intent = _make_intent()
        doc = intent.to_jsonld()
        validate(doc, schema)

    def test_intent_roundtrip(self, schema):
        """Intent to_jsonld → from_jsonld preserves state."""
        intent = _make_intent()
        doc = intent.to_jsonld()
        validate(doc, schema)

        restored = Intent.from_jsonld(doc)
        assert restored.intent_id == intent.intent_id
        assert restored.confidence == intent.confidence

    def test_decision_validates(self, schema):
        """Decision to_jsonld() passes schema validation."""
        decision = _make_decision()
        doc = decision.to_jsonld()
        validate(doc, schema)

    def test_decision_roundtrip(self, schema):
        """Decision to_jsonld → from_jsonld preserves state."""
        decision = _make_decision()
        doc = decision.to_jsonld()
        validate(doc, schema)

        restored = Decision.from_jsonld(doc)
        assert restored.intent_id == decision.intent_id
        assert restored.decision == decision.decision

    def test_execution_record_validates(self, schema):
        """ExecutionRecord to_jsonld() passes schema validation."""
        record = _make_execution_record()
        doc = record.to_jsonld()
        validate(doc, schema)

    def test_execution_record_roundtrip(self, schema):
        """ExecutionRecord to_jsonld → from_jsonld preserves state."""
        record = _make_execution_record()
        doc = record.to_jsonld()
        validate(doc, schema)

        restored = ExecutionRecord.from_jsonld(doc)
        assert restored.record_id == record.record_id
        assert restored.result_status == record.result_status


# ── 9. Entity ───────────────────────────────────────────────────────

from web4.entity import (
    EntityTypeInfo, ENTITY_JSONLD_CONTEXT,
    get_info, entity_registry_to_jsonld,
)


class TestEntitySchemaRoundtrip:
    """Entity type JSON-LD schema validation and round-trip."""

    @pytest.fixture
    def schema(self):
        return load_schema("entity-jsonld.schema.json")

    def test_entity_type_info_validates(self, schema):
        """EntityTypeInfo to_jsonld() passes schema validation."""
        info = get_info(EntityType.HUMAN)
        doc = info.to_jsonld()
        validate(doc, schema)

    def test_all_entity_types_validate(self, schema):
        """All entity types pass schema validation."""
        for et in EntityType:
            info = get_info(et)
            doc = info.to_jsonld()
            validate(doc, schema)

    def test_entity_registry_validates(self, schema):
        """entity_registry_to_jsonld() passes schema validation."""
        doc = entity_registry_to_jsonld()
        validate(doc, schema)

    def test_roundtrip(self, schema):
        """to_jsonld → validate → from_jsonld preserves state."""
        info = get_info(EntityType.AI)
        doc = info.to_jsonld()
        validate(doc, schema)

        restored = EntityTypeInfo.from_jsonld(doc)
        assert restored.entity_type == info.entity_type
        assert restored.energy == info.energy


# ── 10. Capability ──────────────────────────────────────────────────

from web4.capability import (
    LevelRequirement, CAPABILITY_JSONLD_CONTEXT,
    level_requirements, capability_assessment_to_jsonld,
    capability_framework_to_jsonld,
)
from web4.lct import Binding, MRH, Policy


class TestCapabilitySchemaRoundtrip:
    """Capability JSON-LD schema validation and round-trip."""

    @pytest.fixture
    def schema(self):
        return load_schema("capability-jsonld.schema.json")

    def test_level_requirement_validates(self, schema):
        """LevelRequirement to_jsonld() passes schema validation."""
        req = level_requirements(3)
        doc = req.to_jsonld()
        validate(doc, schema)

    def test_all_levels_validate(self, schema):
        """All 6 capability levels pass schema validation."""
        for lvl in range(6):
            req = level_requirements(lvl)
            doc = req.to_jsonld()
            validate(doc, schema)

    def test_capability_framework_validates(self, schema):
        """capability_framework_to_jsonld() passes schema validation."""
        doc = capability_framework_to_jsonld()
        validate(doc, schema)

    def test_capability_assessment_validates(self, schema):
        """capability_assessment_to_jsonld() passes schema validation."""
        lct = LCT.create(
            entity_type=EntityType.HUMAN,
            public_key="mb64:captest123",
            society="lct:web4:society:testnet",
            witnesses=["lct:w1", "lct:w2", "lct:w3"],
            t3=T3(0.7, 0.8, 0.6),
            v3=V3(0.75, 0.85, 0.65),
        )
        doc = capability_assessment_to_jsonld(lct)
        validate(doc, schema)

    def test_level_requirement_roundtrip(self, schema):
        """to_jsonld → validate → from_jsonld preserves state."""
        req = level_requirements(4)
        doc = req.to_jsonld()
        validate(doc, schema)

        restored = LevelRequirement.from_jsonld(doc)
        assert restored.level == req.level
        assert restored.name == req.name
        assert restored.trust_range == req.trust_range


# ── 11. Dictionary ──────────────────────────────────────────────────

from web4.dictionary import (
    DictionarySpec, TranslationResult, TranslationChain,
    DictionaryEntity, DomainCoverage, CompressionProfile,
    DICTIONARY_JSONLD_CONTEXT,
)


class TestDictionarySchemaRoundtrip:
    """Dictionary JSON-LD schema validation and round-trip."""

    @pytest.fixture
    def schema(self):
        return load_schema("dictionary-jsonld.schema.json")

    def test_dictionary_spec_validates(self, schema):
        """DictionarySpec to_jsonld() passes schema validation."""
        spec = DictionarySpec(
            source_domain="medical",
            target_domain="legal",
            coverage=DomainCoverage(terms=500, concepts=120, relationships=80),
        )
        doc = spec.to_jsonld()
        validate(doc, schema)

    def test_dictionary_spec_minimal_validates(self, schema):
        """Minimal DictionarySpec passes schema validation."""
        spec = DictionarySpec(source_domain="finance", target_domain="tech")
        doc = spec.to_jsonld()
        validate(doc, schema)

    def test_dictionary_spec_roundtrip(self, schema):
        """DictionarySpec to_jsonld → from_jsonld preserves state."""
        spec = DictionarySpec(
            source_domain="medical",
            target_domain="legal",
            bidirectional=False,
            version="2.1.0",
        )
        doc = spec.to_jsonld()
        validate(doc, schema)

        restored = DictionarySpec.from_jsonld(doc)
        assert restored.source_domain == spec.source_domain
        assert restored.target_domain == spec.target_domain
        assert restored.bidirectional == spec.bidirectional

    def test_translation_result_validates(self, schema):
        """TranslationResult to_jsonld() passes schema validation."""
        result = TranslationResult(
            content="heart attack",
            confidence=0.95,
            degradation=0.05,
            dictionary_lct_id="lct:dict:med2common",
        )
        doc = result.to_jsonld()
        validate(doc, schema)

    def test_translation_result_roundtrip(self, schema):
        """TranslationResult to_jsonld → from_jsonld preserves state."""
        result = TranslationResult(
            content="contract violation",
            confidence=0.88,
            degradation=0.12,
            dictionary_lct_id="lct:dict:legal2biz",
        )
        doc = result.to_jsonld()
        validate(doc, schema)

        restored = TranslationResult.from_jsonld(doc)
        assert restored.content == result.content
        assert restored.confidence == result.confidence

    def test_translation_chain_validates(self, schema):
        """TranslationChain to_jsonld() passes schema validation."""
        chain = TranslationChain()
        chain.add_step(
            source_domain="medical",
            target_domain="nursing",
            dictionary_lct_id="lct:dict:med2nurse",
            confidence=0.9,
        )
        doc = chain.to_jsonld()
        validate(doc, schema)

    def test_translation_chain_roundtrip(self, schema):
        """TranslationChain to_jsonld → from_jsonld preserves state."""
        chain = TranslationChain()
        chain.add_step(
            source_domain="medical",
            target_domain="nursing",
            dictionary_lct_id="lct:dict:med2nurse",
            confidence=0.92,
        )
        chain.add_step(
            source_domain="nursing",
            target_domain="common",
            dictionary_lct_id="lct:dict:nurse2common",
            confidence=0.88,
        )
        doc = chain.to_jsonld()
        validate(doc, schema)

        restored = TranslationChain.from_jsonld(doc)
        assert len(restored.steps) == len(chain.steps)
        assert restored.steps[0].confidence == chain.steps[0].confidence

    def test_dictionary_entity_validates(self, schema):
        """DictionaryEntity to_jsonld() passes schema validation."""
        entity = DictionaryEntity.create(
            source_domain="medical",
            target_domain="legal",
            public_key="mb64:dict_key_123",
        )
        doc = entity.to_jsonld()
        validate(doc, schema)

    def test_dictionary_entity_roundtrip(self, schema):
        """DictionaryEntity to_jsonld → from_jsonld preserves state."""
        entity = DictionaryEntity.create(
            source_domain="finance",
            target_domain="regulatory",
            public_key="mb64:dict_key_456",
        )
        doc = entity.to_jsonld()
        validate(doc, schema)

        restored = DictionaryEntity.from_jsonld(doc)
        assert restored.spec.source_domain == entity.spec.source_domain
        assert restored.spec.target_domain == entity.spec.target_domain


# ── Summary parametrized test ───────────────────────────────────────


class TestAllTypesSchemaValidation:
    """Parametrized test ensuring every to_jsonld() type validates against its schema."""

    @pytest.fixture
    def all_docs(self):
        """Generate one document per type with schema filename."""
        docs = []

        # LCT
        lct = LCT.create(
            entity_type=EntityType.AI,
            public_key="mb64:param_test_key",
            society="lct:web4:society:testnet",
            witnesses=["lct:w1", "lct:w2", "lct:w3"],
            t3=T3(0.8, 0.8, 0.8),
            v3=V3(0.8, 0.8, 0.8),
        )
        docs.append(("lct-jsonld.schema.json", "LCT", lct.to_jsonld()))

        # AttestationEnvelope
        env = AttestationEnvelope(
            entity_id="lct://web4:test:param@active",
            public_key="MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE_param",
            anchor=AnchorInfo(type="software"),
            proof=Proof(format="ecdsa_software", signature="sig", challenge="ch"),
            timestamp=1710864000.0,
            challenge_issued_at=1710863990.0,
            challenge_ttl=300.0,
            envelope_version="0.1",
        )
        docs.append(("attestation-envelope-jsonld.schema.json", "AttestationEnvelope", env.to_jsonld()))

        # T3
        docs.append(("t3v3-jsonld.schema.json", "T3", T3(0.7, 0.8, 0.9).to_jsonld()))

        # V3
        docs.append(("t3v3-jsonld.schema.json", "V3", V3(0.7, 0.8, 0.9).to_jsonld()))

        # R7Action
        action = build_action(
            actor="lct:param:alice",
            role_lct="lct:param:role",
            action="test_action",
            target="data:param",
        )
        docs.append(("r7-action-jsonld.schema.json", "R7Action", action.to_jsonld()))

        # ATPAccount
        docs.append(("atp-jsonld.schema.json", "ATPAccount", ATPAccount(available=100.0).to_jsonld()))

        # TransferResult
        s, r = ATPAccount(available=100.0, initial_balance=100.0), ATPAccount(available=0.0)
        docs.append(("atp-jsonld.schema.json", "TransferResult", transfer(s, r, 10.0).to_jsonld()))

        # ACP - AgentPlan
        docs.append(("acp-jsonld.schema.json", "AgentPlan", _make_plan().to_jsonld()))

        # ACP - Intent
        docs.append(("acp-jsonld.schema.json", "Intent", _make_intent().to_jsonld()))

        # ACP - Decision
        docs.append(("acp-jsonld.schema.json", "Decision", _make_decision().to_jsonld()))

        # ACP - ExecutionRecord
        docs.append(("acp-jsonld.schema.json", "ExecutionRecord", _make_execution_record().to_jsonld()))

        # Entity
        docs.append(("entity-jsonld.schema.json", "EntityTypeInfo", get_info(EntityType.HUMAN).to_jsonld()))

        # Entity Registry
        docs.append(("entity-jsonld.schema.json", "EntityTypeRegistry", entity_registry_to_jsonld()))

        # Capability - LevelRequirement
        docs.append(("capability-jsonld.schema.json", "LevelRequirement", level_requirements(3).to_jsonld()))

        # Capability - Framework
        docs.append(("capability-jsonld.schema.json", "CapabilityFramework", capability_framework_to_jsonld()))

        # Dictionary - Spec
        docs.append(("dictionary-jsonld.schema.json", "DictionarySpec",
                      DictionarySpec(source_domain="a", target_domain="b").to_jsonld()))

        # Dictionary - TranslationResult
        docs.append(("dictionary-jsonld.schema.json", "TranslationResult",
                      TranslationResult(content="translated", confidence=0.9,
                                        degradation=0.1,
                                        dictionary_lct_id="lct:dict:test").to_jsonld()))

        # Dictionary - TranslationChain
        chain = TranslationChain()
        chain.add_step(source_domain="a", target_domain="b",
                       dictionary_lct_id="lct:dict:a2b", confidence=0.9)
        docs.append(("dictionary-jsonld.schema.json", "TranslationChain", chain.to_jsonld()))

        # Dictionary - DictionaryEntity
        de = DictionaryEntity.create(source_domain="a", target_domain="b",
                                     public_key="mb64:dict_param")
        docs.append(("dictionary-jsonld.schema.json", "DictionaryEntity", de.to_jsonld()))

        return docs

    def test_all_types_validate(self, all_docs):
        """Every to_jsonld() type validates against its JSON Schema."""
        failures = []
        for schema_file, type_name, doc in all_docs:
            schema = load_schema(schema_file)
            try:
                validate(doc, schema)
            except jsonschema.ValidationError as e:
                failures.append(f"{type_name}: {e.message}")

        if failures:
            pytest.fail(f"{len(failures)} schema validation failure(s):\n" +
                        "\n".join(f"  - {f}" for f in failures))
