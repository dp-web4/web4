"""
Tests for web4.acp — Agentic Context Protocol module.

Tests ACP data structures, state machine transitions, guard validation,
plan validation, and intent construction.
"""

import json
import os
import pytest

from web4.acp import (
    # Errors
    ACPError,
    NoValidGrant,
    ScopeViolation,
    ApprovalRequired,
    WitnessDeficit,
    PlanExpired,
    LedgerWriteFailure,
    InvalidTransition,
    ResourceCapExceeded,
    # Enums
    ACPState,
    TriggerKind,
    DecisionType,
    ApprovalMode,
    # Data structures
    Trigger,
    ResourceCaps,
    HumanApproval,
    Guards,
    PlanStep,
    AgentPlan,
    ProofOfAgency,
    Intent,
    Decision,
    ExecutionRecord,
    # State machine
    ACPStateMachine,
    VALID_TRANSITIONS,
    # Functions
    validate_plan,
    build_intent,
)


# ── Helpers ──────────────────────────────────────────────────────

VECTORS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "test-vectors")


def load_vectors(path: str) -> dict:
    full_path = os.path.join(VECTORS_DIR, path)
    with open(full_path) as f:
        return json.load(f)


def make_plan(**overrides) -> AgentPlan:
    """Create a standard test plan."""
    defaults = dict(
        plan_id="acp:plan:test",
        principal="lct:web4:human:alice",
        agent="lct:web4:ai:bot-001",
        grant_id="agy:grant:test-auth",
        triggers=[Trigger(kind=TriggerKind.MANUAL)],
        steps=[
            PlanStep(step_id="fetch", mcp_tool="data.search", args={"limit": 10}),
            PlanStep(step_id="process", mcp_tool="data.transform", depends_on=["fetch"]),
            PlanStep(step_id="store", mcp_tool="data.write", depends_on=["process"]),
        ],
        guards=Guards(
            law_hash="sha256:abc123",
            resource_caps=ResourceCaps(max_atp=100, max_executions=50),
            witness_level=2,
        ),
    )
    defaults.update(overrides)
    return AgentPlan(**defaults)


def make_intent(plan: AgentPlan, step_id: str = "fetch") -> Intent:
    """Create a standard test intent."""
    step = plan.get_step(step_id)
    return Intent(
        intent_id="acp:intent:test001",
        plan_id=plan.plan_id,
        step_id=step_id,
        proposed_action={"mcp": step.mcp_tool, "args": step.args},
        proof=ProofOfAgency(
            grant_id=plan.grant_id,
            plan_id=plan.plan_id,
            intent_id="acp:intent:test001",
        ),
        explanation="Test intent",
        confidence=0.9,
    )


# ══════════════════════════════════════════════════════════════════
#  ERROR HIERARCHY
# ══════════════════════════════════════════════════════════════════

class TestACPErrors:
    """ACP error types and hierarchy."""

    def test_all_inherit_from_acp_error(self):
        errors = [NoValidGrant, ScopeViolation, ApprovalRequired,
                  WitnessDeficit, PlanExpired, LedgerWriteFailure,
                  InvalidTransition, ResourceCapExceeded]
        for err_cls in errors:
            assert issubclass(err_cls, ACPError)

    def test_error_codes_unique(self):
        errors = [NoValidGrant, ScopeViolation, ApprovalRequired,
                  WitnessDeficit, PlanExpired, LedgerWriteFailure,
                  InvalidTransition, ResourceCapExceeded]
        codes = [e.error_code for e in errors]
        assert len(codes) == len(set(codes)), "Duplicate error codes"

    def test_error_code_prefix(self):
        assert NoValidGrant.error_code.startswith("W4_ERR_ACP_")
        assert ScopeViolation.error_code.startswith("W4_ERR_ACP_")


# ══════════════════════════════════════════════════════════════════
#  TRIGGERS
# ══════════════════════════════════════════════════════════════════

class TestTrigger:

    def test_cron_trigger(self):
        t = Trigger(kind=TriggerKind.CRON, expr="0 */6 * * *")
        assert t.kind == TriggerKind.CRON
        assert t.expr == "0 */6 * * *"

    def test_event_trigger(self):
        t = Trigger(kind=TriggerKind.EVENT, expr="invoice.ready")
        assert t.kind == TriggerKind.EVENT

    def test_manual_trigger(self):
        t = Trigger(kind=TriggerKind.MANUAL, authorized=["lct:alice"])
        assert t.authorized == ["lct:alice"]


# ══════════════════════════════════════════════════════════════════
#  GUARDS
# ══════════════════════════════════════════════════════════════════

class TestResourceCaps:

    def test_atp_within_cap(self):
        caps = ResourceCaps(max_atp=100)
        assert caps.check_atp(50) is True
        assert caps.check_atp(100) is True
        assert caps.check_atp(101) is False

    def test_no_cap(self):
        caps = ResourceCaps()
        assert caps.check_atp(999) is True

    def test_execution_cap(self):
        caps = ResourceCaps(max_executions=10)
        assert caps.check_executions(10) is True
        assert caps.check_executions(11) is False


class TestHumanApproval:

    def test_auto_mode(self):
        ha = HumanApproval(mode=ApprovalMode.AUTO)
        assert ha.needs_human(999) is False

    def test_manual_mode(self):
        ha = HumanApproval(mode=ApprovalMode.MANUAL)
        assert ha.needs_human(0) is True

    def test_conditional_below_threshold(self):
        ha = HumanApproval(mode=ApprovalMode.CONDITIONAL, auto_threshold=10)
        assert ha.needs_human(5) is False

    def test_conditional_above_threshold(self):
        ha = HumanApproval(mode=ApprovalMode.CONDITIONAL, auto_threshold=10)
        assert ha.needs_human(15) is True


class TestGuards:

    def test_not_expired(self):
        g = Guards(expires_at="2099-12-31T23:59:59Z")
        assert g.is_expired() is False

    def test_expired(self):
        g = Guards(expires_at="2020-01-01T00:00:00Z")
        assert g.is_expired() is True

    def test_no_expiry(self):
        g = Guards()
        assert g.is_expired() is False

    def test_witness_validation(self):
        g = Guards(witness_level=3)
        assert g.validate_witnesses(3) is True
        assert g.validate_witnesses(2) is False
        assert g.validate_witnesses(5) is True


# ══════════════════════════════════════════════════════════════════
#  PLAN STEPS
# ══════════════════════════════════════════════════════════════════

class TestPlanStep:

    def test_basic_step(self):
        s = PlanStep(step_id="fetch", mcp_tool="data.search", args={"limit": 10})
        assert s.step_id == "fetch"
        assert s.mcp_tool == "data.search"

    def test_to_dict(self):
        s = PlanStep(step_id="process", mcp_tool="data.transform", depends_on=["fetch"])
        d = s.to_dict()
        assert d["id"] == "process"
        assert d["mcp"] == "data.transform"
        assert d["dependsOn"] == ["fetch"]

    def test_to_dict_no_deps(self):
        s = PlanStep(step_id="fetch", mcp_tool="data.search")
        d = s.to_dict()
        assert "dependsOn" not in d


# ══════════════════════════════════════════════════════════════════
#  AGENT PLAN
# ══════════════════════════════════════════════════════════════════

class TestAgentPlan:

    def test_basic_plan(self):
        plan = make_plan()
        assert plan.plan_id == "acp:plan:test"
        assert plan.principal == "lct:web4:human:alice"
        assert plan.agent == "lct:web4:ai:bot-001"
        assert len(plan.steps) == 3

    def test_step_order(self):
        plan = make_plan()
        order = plan.step_order
        assert order.index("fetch") < order.index("process")
        assert order.index("process") < order.index("store")

    def test_get_step(self):
        plan = make_plan()
        step = plan.get_step("process")
        assert step is not None
        assert step.mcp_tool == "data.transform"

    def test_get_step_not_found(self):
        plan = make_plan()
        assert plan.get_step("nonexistent") is None

    def test_canonical_hash_deterministic(self):
        plan1 = make_plan(created_at="2026-01-01T00:00:00Z")
        plan2 = make_plan(created_at="2026-01-01T00:00:00Z")
        assert plan1.canonical_hash() == plan2.canonical_hash()

    def test_canonical_hash_changes_with_content(self):
        plan1 = make_plan()
        plan2 = make_plan(agent="lct:web4:ai:different-agent")
        assert plan1.canonical_hash() != plan2.canonical_hash()

    def test_to_dict(self):
        plan = make_plan()
        d = plan.to_dict()
        assert d["type"] == "ACP.AgentPlan"
        assert d["planId"] == "acp:plan:test"
        assert len(d["steps"]) == 3
        assert d["guards"]["witnessLevel"] == 2


# ══════════════════════════════════════════════════════════════════
#  PROOF OF AGENCY
# ══════════════════════════════════════════════════════════════════

class TestProofOfAgency:

    def test_auto_nonce(self):
        p = ProofOfAgency(grant_id="g1", plan_id="p1", intent_id="i1")
        assert len(p.nonce) == 16

    def test_nonce_unique(self):
        p1 = ProofOfAgency(grant_id="g1", plan_id="p1", intent_id="i1")
        p2 = ProofOfAgency(grant_id="g1", plan_id="p1", intent_id="i2")
        assert p1.nonce != p2.nonce


# ══════════════════════════════════════════════════════════════════
#  INTENT
# ══════════════════════════════════════════════════════════════════

class TestIntent:

    def test_basic_intent(self):
        plan = make_plan()
        intent = make_intent(plan)
        assert intent.intent_id == "acp:intent:test001"
        assert intent.plan_id == "acp:plan:test"
        assert intent.confidence == 0.9

    def test_to_dict(self):
        plan = make_plan()
        intent = make_intent(plan)
        d = intent.to_dict()
        assert d["type"] == "ACP.Intent"
        assert d["proofOfAgency"]["grantId"] == "agy:grant:test-auth"
        assert d["explain"]["confidence"] == 0.9


# ══════════════════════════════════════════════════════════════════
#  DECISION
# ══════════════════════════════════════════════════════════════════

class TestDecision:

    def test_approve(self):
        d = Decision(
            intent_id="i1",
            decision=DecisionType.APPROVE,
            decided_by="lct:alice",
            rationale="Within limits",
        )
        assert d.approved is True
        assert d.denied is False

    def test_deny(self):
        d = Decision(
            intent_id="i1",
            decision=DecisionType.DENY,
            decided_by="lct:alice",
            rationale="Too risky",
        )
        assert d.approved is False
        assert d.denied is True

    def test_modify(self):
        d = Decision(
            intent_id="i1",
            decision=DecisionType.MODIFY,
            decided_by="lct:alice",
            modifications={"amount": 5},
        )
        assert d.approved is False
        assert d.denied is False
        assert d.modifications == {"amount": 5}

    def test_to_dict(self):
        d = Decision(
            intent_id="i1",
            decision=DecisionType.APPROVE,
            decided_by="lct:alice",
            witnesses=["w1", "w2"],
        )
        dd = d.to_dict()
        assert dd["type"] == "ACP.Decision"
        assert dd["decision"] == "approve"
        assert dd["witnesses"] == ["w1", "w2"]


# ══════════════════════════════════════════════════════════════════
#  EXECUTION RECORD
# ══════════════════════════════════════════════════════════════════

class TestExecutionRecord:

    def test_success_record(self):
        r = ExecutionRecord(
            record_id="rec:001",
            intent_id="i1",
            grant_id="g1",
            law_hash="sha256:abc",
            mcp_call={"resource": "data.write", "args": {"key": "v"}},
            result_status="success",
            result_output={"tx": "txn123"},
            resources_consumed={"atp": 5},
        )
        assert r.success is True
        assert r.result_output["tx"] == "txn123"

    def test_failure_record(self):
        r = ExecutionRecord(
            record_id="rec:002",
            intent_id="i1",
            grant_id="g1",
            law_hash="sha256:abc",
            mcp_call={"resource": "data.write", "args": {}},
            result_status="failure",
        )
        assert r.success is False

    def test_canonical_hash_deterministic(self):
        kwargs = dict(
            record_id="rec:001",
            intent_id="i1",
            grant_id="g1",
            law_hash="sha256:abc",
            mcp_call={"resource": "data.write", "args": {}},
            timestamp="2026-01-01T00:00:00Z",
        )
        r1 = ExecutionRecord(**kwargs)
        r2 = ExecutionRecord(**kwargs)
        assert r1.canonical_hash() == r2.canonical_hash()

    def test_to_dict(self):
        r = ExecutionRecord(
            record_id="rec:001",
            intent_id="i1",
            grant_id="g1",
            law_hash="sha256:abc",
            mcp_call={"resource": "data.write", "args": {}},
            witnesses=["w1"],
        )
        d = r.to_dict()
        assert d["type"] == "ACP.ExecutionRecord"
        assert d["witnesses"] == ["w1"]
        assert d["result"]["status"] == "success"


# ══════════════════════════════════════════════════════════════════
#  STATE MACHINE
# ══════════════════════════════════════════════════════════════════

class TestACPStateMachine:

    def test_initial_state(self):
        plan = make_plan()
        sm = ACPStateMachine(plan)
        assert sm.state == ACPState.IDLE

    def test_happy_path(self):
        """Full lifecycle: idle → planning → intent → approval → exec → record → complete."""
        plan = make_plan()
        sm = ACPStateMachine(plan)

        sm.start_planning()
        assert sm.state == ACPState.PLANNING

        intent = make_intent(plan)
        sm.create_intent(intent)
        assert sm.state == ACPState.INTENT_CREATED

        sm.enter_approval_gate()
        assert sm.state == ACPState.APPROVAL_GATE

        decision = Decision(
            intent_id=intent.intent_id,
            decision=DecisionType.APPROVE,
            decided_by="lct:alice",
        )
        sm.approve(decision)
        assert sm.state == ACPState.EXECUTING

        record = ExecutionRecord(
            record_id="rec:001",
            intent_id=intent.intent_id,
            grant_id=plan.grant_id,
            law_hash=plan.guards.law_hash,
            mcp_call=intent.proposed_action,
        )
        sm.record_execution(record)
        assert sm.state == ACPState.RECORDING

        sm.complete()
        assert sm.state == ACPState.COMPLETE

    def test_denial_fails(self):
        """Denial transitions to FAILED."""
        plan = make_plan()
        sm = ACPStateMachine(plan)

        sm.start_planning()
        intent = make_intent(plan)
        sm.create_intent(intent)
        sm.enter_approval_gate()

        decision = Decision(
            intent_id=intent.intent_id,
            decision=DecisionType.DENY,
            decided_by="lct:alice",
            rationale="Too risky",
        )
        sm.approve(decision)
        assert sm.state == ACPState.FAILED
        assert "Denied" in sm.error

    def test_invalid_transition_raises(self):
        plan = make_plan()
        sm = ACPStateMachine(plan)
        with pytest.raises(InvalidTransition):
            sm.complete()  # Can't go from IDLE to COMPLETE

    def test_expired_plan(self):
        plan = make_plan(
            guards=Guards(expires_at="2020-01-01T00:00:00Z")
        )
        sm = ACPStateMachine(plan)
        with pytest.raises(PlanExpired):
            sm.start_planning()
        assert sm.state == ACPState.FAILED

    def test_resource_cap_exceeded(self):
        plan = make_plan(
            guards=Guards(resource_caps=ResourceCaps(max_atp=10))
        )
        sm = ACPStateMachine(plan)
        sm.start_planning()

        intent = Intent(
            intent_id="i1",
            plan_id=plan.plan_id,
            step_id="fetch",
            proposed_action={"mcp": "data.search", "args": {"atp": 50}},
            proof=ProofOfAgency(grant_id=plan.grant_id, plan_id=plan.plan_id, intent_id="i1"),
        )
        with pytest.raises(ResourceCapExceeded):
            sm.create_intent(intent)
        assert sm.state == ACPState.FAILED

    def test_reset_from_complete(self):
        plan = make_plan()
        sm = ACPStateMachine(plan)

        # Run through happy path
        sm.start_planning()
        intent = make_intent(plan)
        sm.create_intent(intent)
        sm.enter_approval_gate()
        sm.approve(Decision(intent_id="i", decision=DecisionType.APPROVE, decided_by="a"))
        sm.record_execution(ExecutionRecord(
            record_id="r", intent_id="i", grant_id="g",
            law_hash="h", mcp_call={"resource": "x", "args": {}},
        ))
        sm.complete()
        assert sm.state == ACPState.COMPLETE

        sm.reset()
        assert sm.state == ACPState.IDLE
        assert sm.intent is None

    def test_reset_from_failed(self):
        plan = make_plan(guards=Guards(expires_at="2020-01-01T00:00:00Z"))
        sm = ACPStateMachine(plan)
        try:
            sm.start_planning()
        except PlanExpired:
            pass
        assert sm.state == ACPState.FAILED

        sm.reset()
        assert sm.state == ACPState.IDLE

    def test_history_tracked(self):
        plan = make_plan()
        sm = ACPStateMachine(plan)
        sm.start_planning()
        assert len(sm.history) >= 2  # init + planning
        assert sm.history[-1]["to"] == "planning"

    def test_modify_decision_updates_action(self):
        plan = make_plan()
        sm = ACPStateMachine(plan)
        sm.start_planning()
        intent = make_intent(plan)
        sm.create_intent(intent)
        sm.enter_approval_gate()

        decision = Decision(
            intent_id=intent.intent_id,
            decision=DecisionType.MODIFY,
            decided_by="lct:alice",
            modifications={"limit": 5},
        )
        sm.approve(decision)
        assert sm.state == ACPState.EXECUTING
        assert sm.intent.proposed_action.get("limit") == 5


# ══════════════════════════════════════════════════════════════════
#  PLAN VALIDATION
# ══════════════════════════════════════════════════════════════════

class TestPlanValidation:

    def test_valid_plan(self):
        plan = make_plan()
        errors = validate_plan(plan)
        assert errors == []

    def test_missing_plan_id(self):
        plan = make_plan(plan_id="")
        errors = validate_plan(plan)
        assert any("plan_id" in e for e in errors)

    def test_missing_principal(self):
        plan = make_plan(principal="")
        errors = validate_plan(plan)
        assert any("principal" in e for e in errors)

    def test_missing_steps(self):
        plan = make_plan(steps=[])
        errors = validate_plan(plan)
        assert any("step" in e.lower() for e in errors)

    def test_unknown_dependency(self):
        plan = make_plan(steps=[
            PlanStep(step_id="a", mcp_tool="x", depends_on=["nonexistent"]),
        ])
        errors = validate_plan(plan)
        assert any("nonexistent" in e for e in errors)

    def test_cycle_detection(self):
        plan = make_plan(steps=[
            PlanStep(step_id="a", mcp_tool="x", depends_on=["b"]),
            PlanStep(step_id="b", mcp_tool="y", depends_on=["a"]),
        ])
        errors = validate_plan(plan)
        assert any("cycle" in e.lower() for e in errors)


# ══════════════════════════════════════════════════════════════════
#  INTENT BUILDER
# ══════════════════════════════════════════════════════════════════

class TestBuildIntent:

    def test_basic_build(self):
        plan = make_plan()
        intent = build_intent(plan, "fetch", explanation="Get data")
        assert intent.plan_id == plan.plan_id
        assert intent.step_id == "fetch"
        assert intent.proposed_action["mcp"] == "data.search"
        assert intent.explanation == "Get data"

    def test_args_override(self):
        plan = make_plan()
        intent = build_intent(plan, "fetch", args={"limit": 50})
        assert intent.proposed_action["args"]["limit"] == 50

    def test_proof_auto_created(self):
        plan = make_plan()
        intent = build_intent(plan, "fetch")
        assert intent.proof.grant_id == plan.grant_id
        assert intent.proof.plan_id == plan.plan_id
        assert len(intent.proof.nonce) == 16

    def test_unknown_step_raises(self):
        plan = make_plan()
        with pytest.raises(ValueError, match="not found"):
            build_intent(plan, "nonexistent")

    def test_approval_from_step(self):
        plan = make_plan(steps=[
            PlanStep(step_id="approve", mcp_tool="invoice.approve",
                     requires_approval="if_amount > 10"),
        ])
        intent = build_intent(plan, "approve")
        assert intent.needs_approval is True


# ══════════════════════════════════════════════════════════════════
#  CROSS-MODULE INTEGRATION
# ══════════════════════════════════════════════════════════════════

class TestCrossModuleIntegration:

    def test_acp_with_trust_delta(self):
        """ExecutionRecord can carry T3/V3 deltas."""
        from web4.trust import T3
        t3 = T3(talent=0.8, training=0.7, temperament=0.9)
        updated = t3.update(quality=0.8, success=True)

        record = ExecutionRecord(
            record_id="rec:trust",
            intent_id="i1",
            grant_id="g1",
            law_hash="sha256:abc",
            mcp_call={"resource": "task.complete", "args": {}},
            t3v3_delta={
                "agent": {
                    "t3": {
                        "talent": updated.talent - t3.talent,
                        "training": updated.training - t3.training,
                        "temperament": updated.temperament - t3.temperament,
                    }
                }
            },
        )
        delta = record.t3v3_delta["agent"]["t3"]
        assert delta["talent"] > 0  # quality > 0.5 → positive delta

    def test_acp_with_lct_identity(self):
        """ACP plan references LCT entity IDs."""
        from web4.lct import LCT, EntityType
        lct = LCT.create(entity_type=EntityType.AI, public_key="testkey")

        plan = AgentPlan(
            plan_id="acp:plan:lct-test",
            principal="lct:web4:human:owner",
            agent=lct.lct_id,
            grant_id="agy:grant:lct-test",
            steps=[PlanStep(step_id="s1", mcp_tool="tool.action")],
        )
        assert plan.agent == lct.lct_id

    def test_acp_with_atp_resource_tracking(self):
        """ExecutionRecord tracks ATP consumption."""
        from web4.atp import ATPAccount
        acct = ATPAccount(available=100)
        acct.lock(25)  # Reserve ATP for operation

        record = ExecutionRecord(
            record_id="rec:atp",
            intent_id="i1",
            grant_id="g1",
            law_hash="sha256:abc",
            mcp_call={"resource": "payment.process", "args": {}},
            resources_consumed={"atp": 25},
        )
        acct.commit(25)  # Discharge locked ATP

        assert acct.available == 75
        assert acct.adp == 25
        assert record.resources_consumed["atp"] == 25

    def test_acp_with_federation_law(self):
        """ACP plan references federation law hash."""
        from web4.federation import LawDataset, Norm

        law = LawDataset(
            law_id="law:acme:v1",
            version="1.0",
            society_id="lct:web4:society:acme",
            norms=[Norm(norm_id="MAX-ATP", selector="r6.resource.atp", op="<=", value=100)],
        )

        plan = make_plan(guards=Guards(law_hash=law.hash))
        assert plan.guards.law_hash == law.hash

        # Verify the norm would pass for our plan's resource cap
        assert law.check_norm("MAX-ATP", plan.guards.resource_caps.max_atp) is True


# ══════════════════════════════════════════════════════════════════
#  CANONICAL TEST VECTORS
# ══════════════════════════════════════════════════════════════════

class TestACPVectors:
    """Tests against acp/plan-operations.json vectors."""

    @classmethod
    def setup_class(cls):
        cls.vectors = load_vectors("acp/plan-operations.json")["vectors"]

    def _vec(self, vec_id: str) -> dict:
        return next(v for v in self.vectors if v["id"] == vec_id)

    def test_plan_hash(self):
        """acp-001: Plan canonical hash."""
        v = self._vec("acp-001")
        inp = v["input"]
        plan = AgentPlan(
            plan_id=inp["planId"],
            principal=inp["principal"],
            agent=inp["agent"],
            grant_id=inp["grantId"],
            steps=[PlanStep(
                step_id=s["id"],
                mcp_tool=s["mcp"],
                args=s.get("args", {}),
                depends_on=s.get("dependsOn", []),
            ) for s in inp["steps"]],
            guards=Guards(
                law_hash=inp["guards"]["lawHash"],
                witness_level=inp["guards"]["witnessLevel"],
                resource_caps=ResourceCaps(
                    max_atp=inp["guards"]["resourceCaps"]["maxAtp"],
                    max_executions=inp["guards"]["resourceCaps"]["maxExecutions"],
                ),
            ),
        )
        assert plan.canonical_hash() == v["expected"]["hash"]

    def test_state_transitions(self):
        """acp-002: State machine transition count."""
        v = self._vec("acp-002")
        inp = v["input"]

        # Count valid transitions
        total = sum(len(targets) for targets in VALID_TRANSITIONS.values())
        assert total == v["expected"]["totalValidTransitions"]

        # Verify specific states
        assert len(ACPState) == v["expected"]["totalStates"]

    def test_plan_validation(self):
        """acp-003: Plan validation catches errors."""
        v = self._vec("acp-003")

        for case in v["input"]["cases"]:
            steps = [PlanStep(
                step_id=s["id"],
                mcp_tool=s.get("mcp", ""),
                depends_on=s.get("dependsOn", []),
            ) for s in case.get("steps", [])]

            plan = AgentPlan(
                plan_id=case.get("planId", ""),
                principal=case.get("principal", ""),
                agent=case.get("agent", ""),
                grant_id=case.get("grantId", ""),
                steps=steps,
            )
            errors = validate_plan(plan)
            assert (len(errors) > 0) == case["expectErrors"], \
                f"Case '{case['name']}': expected errors={case['expectErrors']}, got {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
