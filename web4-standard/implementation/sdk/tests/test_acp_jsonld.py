"""
Tests for ACP JSON-LD serialization (A2).

Validates that to_jsonld() produces spec-compliant documents matching
the acp-framework spec, and that from_jsonld() round-trips cleanly.
"""

import json
import pytest

from web4.acp import (
    ACP_JSONLD_CONTEXT,
    AgentPlan,
    PlanStep,
    Trigger,
    TriggerKind,
    Guards,
    ResourceCaps,
    HumanApproval,
    ApprovalMode,
    ProofOfAgency,
    Intent,
    Decision,
    DecisionType,
    ExecutionRecord,
)


# ── Helpers ──────────────────────────────────────────────────────

def make_plan(**overrides) -> AgentPlan:
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


def make_intent(**overrides) -> Intent:
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


def make_decision(**overrides) -> Decision:
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


def make_execution_record(**overrides) -> ExecutionRecord:
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


# ── AgentPlan JSON-LD ────────────────────────────────────────────


class TestAgentPlanJsonLd:
    """AgentPlan.to_jsonld() / from_jsonld() tests."""

    def test_context_and_type(self):
        plan = make_plan()
        doc = plan.to_jsonld()
        assert doc["@context"] == [ACP_JSONLD_CONTEXT]
        assert doc["@type"] == "AgentPlan"

    def test_required_fields(self):
        plan = make_plan()
        doc = plan.to_jsonld()
        assert doc["planId"] == "plan-001"
        assert doc["principal"] == "lct:principal:abc"
        assert doc["agent"] == "lct:agent:xyz"
        assert doc["grantId"] == "grant-001"
        assert doc["createdAt"] == "2026-03-21T18:00:00+00:00"
        assert "canonicalHash" in doc
        assert len(doc["canonicalHash"]) == 64

    def test_steps_serialized(self):
        plan = make_plan()
        doc = plan.to_jsonld()
        assert len(doc["steps"]) == 1
        assert doc["steps"][0]["id"] == "s1"
        assert doc["steps"][0]["mcp"] == "invoice.search"

    def test_step_dependencies(self):
        plan = make_plan(steps=[
            PlanStep(step_id="s1", mcp_tool="a.get"),
            PlanStep(step_id="s2", mcp_tool="b.put", depends_on=["s1"]),
        ])
        doc = plan.to_jsonld()
        assert doc["steps"][1]["dependsOn"] == ["s1"]

    def test_guards_structure(self):
        plan = make_plan()
        doc = plan.to_jsonld()
        g = doc["guards"]
        assert g["lawHash"] == "abc123"
        assert g["witnessLevel"] == 2
        assert g["resourceCaps"]["maxAtp"] == 100.0
        assert g["resourceCaps"]["maxExecutions"] == 10
        assert g["humanApproval"]["mode"] == "conditional"
        assert g["humanApproval"]["autoThreshold"] == 50.0

    def test_triggers_included(self):
        plan = make_plan()
        doc = plan.to_jsonld()
        assert len(doc["triggers"]) == 1
        assert doc["triggers"][0]["kind"] == "cron"
        assert doc["triggers"][0]["expr"] == "0 * * * *"

    def test_triggers_with_authorized(self):
        plan = make_plan(triggers=[
            Trigger(kind=TriggerKind.MANUAL, authorized=["lct:user:u1"]),
        ])
        doc = plan.to_jsonld()
        assert doc["triggers"][0]["authorized"] == ["lct:user:u1"]

    def test_no_triggers_omitted(self):
        plan = make_plan(triggers=[])
        doc = plan.to_jsonld()
        assert "triggers" not in doc

    def test_roundtrip(self):
        plan = make_plan()
        doc = plan.to_jsonld()
        restored = AgentPlan.from_jsonld(doc)
        assert restored.plan_id == plan.plan_id
        assert restored.principal == plan.principal
        assert restored.agent == plan.agent
        assert restored.grant_id == plan.grant_id
        assert restored.created_at == plan.created_at
        assert len(restored.steps) == len(plan.steps)

    def test_roundtrip_preserves_guards(self):
        plan = make_plan()
        doc = plan.to_jsonld()
        restored = AgentPlan.from_jsonld(doc)
        assert restored.guards.resource_caps.max_atp == 100.0
        assert restored.guards.resource_caps.max_executions == 10
        assert restored.guards.human_approval.mode == ApprovalMode.CONDITIONAL
        assert restored.guards.expires_at == "2026-12-31T23:59:59+00:00"

    def test_roundtrip_preserves_triggers(self):
        plan = make_plan()
        doc = plan.to_jsonld()
        restored = AgentPlan.from_jsonld(doc)
        assert len(restored.triggers) == 1
        assert restored.triggers[0].kind == TriggerKind.CRON

    def test_canonical_hash_stable(self):
        plan = make_plan()
        doc = plan.to_jsonld()
        restored = AgentPlan.from_jsonld(doc)
        assert restored.canonical_hash() == plan.canonical_hash()

    def test_string_roundtrip(self):
        plan = make_plan()
        s = plan.to_jsonld_string()
        restored = AgentPlan.from_jsonld_string(s)
        assert restored.plan_id == plan.plan_id

    def test_json_parseable(self):
        plan = make_plan()
        s = plan.to_jsonld_string()
        parsed = json.loads(s)
        assert parsed["@type"] == "AgentPlan"


# ── Intent JSON-LD ──────────────────────────────────────────────


class TestIntentJsonLd:
    """Intent.to_jsonld() / from_jsonld() tests."""

    def test_context_and_type(self):
        intent = make_intent()
        doc = intent.to_jsonld()
        assert doc["@context"] == [ACP_JSONLD_CONTEXT]
        assert doc["@type"] == "Intent"

    def test_required_fields(self):
        intent = make_intent()
        doc = intent.to_jsonld()
        assert doc["intentId"] == "acp:intent:abc123"
        assert doc["planId"] == "plan-001"
        assert doc["stepId"] == "s1"
        assert doc["createdAt"] == "2026-03-21T18:00:00+00:00"

    def test_proposed_action(self):
        intent = make_intent()
        doc = intent.to_jsonld()
        assert doc["proposedAction"] == {"mcp": "invoice.search", "args": {"q": "test"}}

    def test_proof_of_agency(self):
        intent = make_intent()
        doc = intent.to_jsonld()
        poa = doc["proofOfAgency"]
        assert poa["grantId"] == "grant-001"
        assert poa["planId"] == "plan-001"
        assert poa["intentId"] == "acp:intent:abc123"
        assert poa["nonce"] == "fixed_nonce_1234"

    def test_proof_audience_included(self):
        intent = make_intent(proof=ProofOfAgency(
            grant_id="g1", plan_id="p1", intent_id="i1", nonce="n1",
            audience=["lct:aud:a1"],
        ))
        doc = intent.to_jsonld()
        assert doc["proofOfAgency"]["audience"] == ["lct:aud:a1"]

    def test_proof_expires_at_included(self):
        intent = make_intent(proof=ProofOfAgency(
            grant_id="g1", plan_id="p1", intent_id="i1", nonce="n1",
            expires_at="2026-12-31T00:00:00+00:00",
        ))
        doc = intent.to_jsonld()
        assert doc["proofOfAgency"]["expiresAt"] == "2026-12-31T00:00:00+00:00"

    def test_explanation_fields(self):
        intent = make_intent()
        doc = intent.to_jsonld()
        assert doc["explanation"] == "Search for matching invoices"
        assert doc["confidence"] == 0.85
        assert doc["riskAssessment"] == "low"
        assert doc["needsApproval"] is False

    def test_empty_explanation_omitted(self):
        intent = make_intent(explanation="")
        doc = intent.to_jsonld()
        assert "explanation" not in doc

    def test_roundtrip(self):
        intent = make_intent()
        doc = intent.to_jsonld()
        restored = Intent.from_jsonld(doc)
        assert restored.intent_id == intent.intent_id
        assert restored.plan_id == intent.plan_id
        assert restored.confidence == intent.confidence
        assert restored.proof.nonce == intent.proof.nonce

    def test_string_roundtrip(self):
        intent = make_intent()
        s = intent.to_jsonld_string()
        restored = Intent.from_jsonld_string(s)
        assert restored.intent_id == intent.intent_id


# ── Decision JSON-LD ─────────────────────────────────────────────


class TestDecisionJsonLd:
    """Decision.to_jsonld() / from_jsonld() tests."""

    def test_context_and_type(self):
        dec = make_decision()
        doc = dec.to_jsonld()
        assert doc["@context"] == [ACP_JSONLD_CONTEXT]
        assert doc["@type"] == "Decision"

    def test_required_fields(self):
        dec = make_decision()
        doc = dec.to_jsonld()
        assert doc["intentId"] == "acp:intent:abc123"
        assert doc["decision"] == "approve"
        assert doc["decidedBy"] == "lct:reviewer:r1"
        assert doc["timestamp"] == "2026-03-21T18:01:00+00:00"

    def test_rationale_included(self):
        dec = make_decision()
        doc = dec.to_jsonld()
        assert doc["rationale"] == "Action is within policy bounds"

    def test_empty_rationale_omitted(self):
        dec = make_decision(rationale="")
        doc = dec.to_jsonld()
        assert "rationale" not in doc

    def test_witnesses_included(self):
        dec = make_decision()
        doc = dec.to_jsonld()
        assert doc["witnesses"] == ["lct:witness:w1", "lct:witness:w2"]

    def test_no_witnesses_omitted(self):
        dec = make_decision(witnesses=[])
        doc = dec.to_jsonld()
        assert "witnesses" not in doc

    def test_deny_decision(self):
        dec = make_decision(decision=DecisionType.DENY, rationale="Too risky")
        doc = dec.to_jsonld()
        assert doc["decision"] == "deny"

    def test_modify_with_modifications(self):
        dec = make_decision(
            decision=DecisionType.MODIFY,
            modifications={"args": {"limit": 10}},
        )
        doc = dec.to_jsonld()
        assert doc["modifications"] == {"args": {"limit": 10}}

    def test_no_modifications_omitted(self):
        dec = make_decision(modifications=None)
        doc = dec.to_jsonld()
        assert "modifications" not in doc

    def test_roundtrip(self):
        dec = make_decision()
        doc = dec.to_jsonld()
        restored = Decision.from_jsonld(doc)
        assert restored.intent_id == dec.intent_id
        assert restored.decision == dec.decision
        assert restored.decided_by == dec.decided_by
        assert restored.witnesses == dec.witnesses

    def test_roundtrip_modify(self):
        dec = make_decision(
            decision=DecisionType.MODIFY,
            modifications={"args": {"limit": 5}},
        )
        doc = dec.to_jsonld()
        restored = Decision.from_jsonld(doc)
        assert restored.decision == DecisionType.MODIFY
        assert restored.modifications == {"args": {"limit": 5}}

    def test_string_roundtrip(self):
        dec = make_decision()
        s = dec.to_jsonld_string()
        restored = Decision.from_jsonld_string(s)
        assert restored.decided_by == dec.decided_by


# ── ExecutionRecord JSON-LD ──────────────────────────────────────


class TestExecutionRecordJsonLd:
    """ExecutionRecord.to_jsonld() / from_jsonld() tests."""

    def test_context_and_type(self):
        rec = make_execution_record()
        doc = rec.to_jsonld()
        assert doc["@context"] == [ACP_JSONLD_CONTEXT]
        assert doc["@type"] == "ExecutionRecord"

    def test_required_fields(self):
        rec = make_execution_record()
        doc = rec.to_jsonld()
        assert doc["recordId"] == "rec-001"
        assert doc["intentId"] == "acp:intent:abc123"
        assert doc["grantId"] == "grant-001"
        assert doc["lawHash"] == "abc123"
        assert doc["timestamp"] == "2026-03-21T18:02:00+00:00"

    def test_mcp_call(self):
        rec = make_execution_record()
        doc = rec.to_jsonld()
        assert doc["mcpCall"] == {"resource": "invoice.search", "args": {"q": "test"}}

    def test_result_structure(self):
        rec = make_execution_record()
        doc = rec.to_jsonld()
        assert doc["result"]["status"] == "success"
        assert doc["result"]["output"]["invoices"][0]["id"] == "inv-1"
        assert doc["result"]["resourcesConsumed"]["atp"] == 5.0

    def test_failure_result(self):
        rec = make_execution_record(result_status="failure", result_output={"error": "timeout"})
        doc = rec.to_jsonld()
        assert doc["result"]["status"] == "failure"

    def test_empty_output_omitted(self):
        rec = make_execution_record(result_output={}, resources_consumed={})
        doc = rec.to_jsonld()
        assert "output" not in doc["result"]
        assert "resourcesConsumed" not in doc["result"]

    def test_t3v3_delta(self):
        rec = make_execution_record()
        doc = rec.to_jsonld()
        assert doc["t3v3Delta"] == {"talent": 0.01}

    def test_empty_t3v3_delta_omitted(self):
        rec = make_execution_record(t3v3_delta={})
        doc = rec.to_jsonld()
        assert "t3v3Delta" not in doc

    def test_witnesses(self):
        rec = make_execution_record()
        doc = rec.to_jsonld()
        assert doc["witnesses"] == ["lct:witness:w1"]

    def test_no_witnesses_omitted(self):
        rec = make_execution_record(witnesses=[])
        doc = rec.to_jsonld()
        assert "witnesses" not in doc

    def test_canonical_hash(self):
        rec = make_execution_record()
        doc = rec.to_jsonld()
        assert "canonicalHash" in doc
        assert len(doc["canonicalHash"]) == 64

    def test_roundtrip(self):
        rec = make_execution_record()
        doc = rec.to_jsonld()
        restored = ExecutionRecord.from_jsonld(doc)
        assert restored.record_id == rec.record_id
        assert restored.intent_id == rec.intent_id
        assert restored.result_status == rec.result_status
        assert restored.result_output == rec.result_output
        assert restored.resources_consumed == rec.resources_consumed

    def test_canonical_hash_stable(self):
        rec = make_execution_record()
        doc = rec.to_jsonld()
        restored = ExecutionRecord.from_jsonld(doc)
        assert restored.canonical_hash() == rec.canonical_hash()

    def test_string_roundtrip(self):
        rec = make_execution_record()
        s = rec.to_jsonld_string()
        restored = ExecutionRecord.from_jsonld_string(s)
        assert restored.record_id == rec.record_id


# ── Schema Compliance ────────────────────────────────────────────


class TestSchemaCompliance:
    """Verify to_jsonld() output has no unexpected keys."""

    def test_agent_plan_no_additional_properties(self):
        doc = make_plan().to_jsonld()
        known = {"@context", "@type", "planId", "principal", "agent", "grantId",
                 "steps", "guards", "canonicalHash", "createdAt", "triggers"}
        assert set(doc.keys()).issubset(known)

    def test_intent_no_additional_properties(self):
        doc = make_intent().to_jsonld()
        known = {"@context", "@type", "intentId", "planId", "stepId",
                 "proposedAction", "proofOfAgency", "explanation", "confidence",
                 "riskAssessment", "needsApproval", "createdAt"}
        assert set(doc.keys()).issubset(known)

    def test_decision_no_additional_properties(self):
        doc = make_decision().to_jsonld()
        known = {"@context", "@type", "intentId", "decision", "decidedBy",
                 "rationale", "modifications", "witnesses", "timestamp"}
        assert set(doc.keys()).issubset(known)

    def test_execution_record_no_additional_properties(self):
        doc = make_execution_record().to_jsonld()
        known = {"@context", "@type", "recordId", "intentId", "grantId",
                 "lawHash", "mcpCall", "result", "t3v3Delta", "witnesses",
                 "canonicalHash", "timestamp"}
        assert set(doc.keys()).issubset(known)
