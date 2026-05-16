"""
Tests for cross-society MCP types landed via PR #195.

Covers the 6 types added to web4.mcp implementing mcp-protocol.md §7.3–7.6:
OutcomeClass, PropagationScope, CrossSocietyInteractionType,
CrossSocietyContext, ReputationEnvelope, MCPContextResource.

Tests: enum values, construction, defaults, to_dict/from_dict round-trips.
"""

from web4.mcp import (
    CrossSocietyContext,
    CrossSocietyInteractionType,
    MCPContextResource,
    MCPResourceType,
    OutcomeClass,
    ProofOfAgency,
    PropagationScope,
    ReputationEnvelope,
    TrustRequirements,
)

# ── OutcomeClass (§7.3) ──────────────────────────────────────────


class TestOutcomeClass:
    def test_enum_values(self):
        assert OutcomeClass.SUCCESS.value == "success"
        assert OutcomeClass.PARTIAL.value == "partial"
        assert OutcomeClass.FAILURE.value == "failure"
        assert OutcomeClass.VIOLATION.value == "violation"

    def test_count(self):
        assert len(OutcomeClass) == 4

    def test_str_roundtrip(self):
        for oc in OutcomeClass:
            assert OutcomeClass(oc.value) is oc


# ── PropagationScope (§7.3, §7.5) ────────────────────────────────


class TestPropagationScope:
    def test_enum_values(self):
        assert PropagationScope.RESPONDING_SOCIETY.value == "responding_society"
        assert PropagationScope.CALLER_SOCIETY.value == "caller_society"
        assert PropagationScope.BOTH.value == "both"
        assert PropagationScope.ENCOMPASSING_SOCIETY.value == "encompassing_society"

    def test_count(self):
        assert len(PropagationScope) == 4

    def test_str_roundtrip(self):
        for ps in PropagationScope:
            assert PropagationScope(ps.value) is ps


# ── CrossSocietyInteractionType (§7.4) ───────────────────────────


class TestCrossSocietyInteractionType:
    def test_enum_values(self):
        assert CrossSocietyInteractionType.FIRST_CONTACT.value == "first_contact"
        assert CrossSocietyInteractionType.ESTABLISHED.value == "established"
        assert CrossSocietyInteractionType.FEDERATED.value == "federated"

    def test_count(self):
        assert len(CrossSocietyInteractionType) == 3

    def test_str_roundtrip(self):
        for it in CrossSocietyInteractionType:
            assert CrossSocietyInteractionType(it.value) is it


# ── CrossSocietyContext (§7.4) ────────────────────────────────────


class TestCrossSocietyContext:
    def test_minimal_construction(self):
        ctx = CrossSocietyContext(
            sender_lct="lct:alice",
            sender_society="society:alpha",
            responding_society="society:beta",
        )
        assert ctx.sender_lct == "lct:alice"
        assert ctx.sender_society == "society:alpha"
        assert ctx.responding_society == "society:beta"
        assert ctx.interaction_type == CrossSocietyInteractionType.ESTABLISHED

    def test_defaults(self):
        ctx = CrossSocietyContext(
            sender_lct="lct:x",
            sender_society="s:a",
            responding_society="s:b",
        )
        assert ctx.sender_role == ""
        assert ctx.responding_role_expected == ""
        assert ctx.applicable_law_oracle == ""
        assert ctx.exchange_agreement_hash == ""
        assert ctx.atp_settlement_currency == ""
        assert ctx.atp_settlement_amount == 0
        assert ctx.atp_settlement_exchange_rate is None
        assert ctx.mrh_depth == 1
        assert ctx.law_hash == ""
        assert ctx.proof_of_agency is None

    def test_full_construction(self):
        ctx = CrossSocietyContext(
            sender_lct="lct:alice",
            sender_society="society:alpha",
            responding_society="society:beta",
            interaction_type=CrossSocietyInteractionType.FIRST_CONTACT,
            sender_role="Trader",
            responding_role_expected="Merchant",
            applicable_law_oracle="oracle:encompassing",
            exchange_agreement_hash="sha256:abc123",
            atp_settlement_currency="ATP-ALPHA",
            atp_settlement_amount=100,
            atp_settlement_exchange_rate={"ATP-ALPHA": 1.0, "ATP-BETA": 0.85},
            mrh_depth=3,
            law_hash="sha256:law",
            proof_of_agency=ProofOfAgency(
                grant_id="grant:alice-trade",
                scope="cross_society_trade",
            ),
        )
        assert ctx.interaction_type == CrossSocietyInteractionType.FIRST_CONTACT
        assert ctx.atp_settlement_amount == 100

    def test_to_dict_minimal(self):
        ctx = CrossSocietyContext(
            sender_lct="lct:a",
            sender_society="s:alpha",
            responding_society="s:beta",
        )
        d = ctx.to_dict()
        assert d["sender_lct"] == "lct:a"
        assert d["sender_society"] == "s:alpha"
        assert d["responding_society"] == "s:beta"
        assert d["interaction_type"] == "established"
        assert "cross_society" in d
        assert d["cross_society"]["interaction_type"] == "established"

    def test_to_dict_with_settlement(self):
        ctx = CrossSocietyContext(
            sender_lct="lct:a",
            sender_society="s:alpha",
            responding_society="s:beta",
            atp_settlement_currency="ATP-A",
            atp_settlement_amount=50,
            atp_settlement_exchange_rate={"rate": 0.9},
        )
        d = ctx.to_dict()
        settlement = d["cross_society"]["atp_settlement"]
        assert settlement["currency"] == "ATP-A"
        assert settlement["amount"] == 50
        assert settlement["exchange_rate"] == {"rate": 0.9}

    def test_roundtrip(self):
        ctx = CrossSocietyContext(
            sender_lct="lct:alice",
            sender_society="society:alpha",
            responding_society="society:beta",
            interaction_type=CrossSocietyInteractionType.FEDERATED,
            sender_role="Diplomat",
            applicable_law_oracle="oracle:encompassing",
            atp_settlement_currency="ATP-ALPHA",
            atp_settlement_amount=200,
            mrh_depth=2,
            law_hash="sha256:lawdigest",
        )
        d = ctx.to_dict()
        restored = CrossSocietyContext.from_dict(d)
        assert restored.sender_lct == ctx.sender_lct
        assert restored.sender_society == ctx.sender_society
        assert restored.responding_society == ctx.responding_society
        assert restored.interaction_type == ctx.interaction_type
        assert restored.sender_role == ctx.sender_role
        assert restored.applicable_law_oracle == ctx.applicable_law_oracle
        assert restored.atp_settlement_currency == ctx.atp_settlement_currency
        assert restored.atp_settlement_amount == ctx.atp_settlement_amount
        assert restored.mrh_depth == ctx.mrh_depth
        assert restored.law_hash == ctx.law_hash

    def test_roundtrip_with_proof_of_agency(self):
        poa = ProofOfAgency(
            grant_id="grant:agent-trade",
            scope="cross_society_trade",
        )
        ctx = CrossSocietyContext(
            sender_lct="lct:agent",
            sender_society="s:a",
            responding_society="s:b",
            proof_of_agency=poa,
        )
        d = ctx.to_dict()
        restored = CrossSocietyContext.from_dict(d)
        assert restored.proof_of_agency is not None
        assert restored.proof_of_agency.grant_id == "grant:agent-trade"
        assert restored.proof_of_agency.scope == "cross_society_trade"

    def test_frozen(self):
        ctx = CrossSocietyContext(
            sender_lct="lct:x",
            sender_society="s:a",
            responding_society="s:b",
        )
        try:
            ctx.sender_lct = "lct:y"  # type: ignore[misc]
            assert False, "Should raise FrozenInstanceError"
        except AttributeError:
            pass


# ── ReputationEnvelope (§7.3) ─────────────────────────────────────


class TestReputationEnvelope:
    def test_minimal_construction(self):
        env = ReputationEnvelope(
            action_id="action:001",
            outcome_class=OutcomeClass.SUCCESS,
        )
        assert env.action_id == "action:001"
        assert env.outcome_class == OutcomeClass.SUCCESS
        assert env.outcome_quality == 0.5
        assert env.propagation_scope == PropagationScope.RESPONDING_SOCIETY

    def test_defaults(self):
        env = ReputationEnvelope(
            action_id="a:1",
            outcome_class=OutcomeClass.FAILURE,
        )
        assert env.responding_society == ""
        assert env.responding_society_signature == ""
        assert env.trust_dimension_updates == {}
        assert env.witness_signatures == []
        assert env.timestamp == ""

    def test_full_construction(self):
        env = ReputationEnvelope(
            action_id="action:trade-42",
            outcome_class=OutcomeClass.PARTIAL,
            outcome_quality=0.7,
            responding_society="society:beta",
            responding_society_signature="sig:beta-policy",
            trust_dimension_updates={"talent": 0.1, "temperament": -0.05},
            propagation_scope=PropagationScope.BOTH,
            witness_signatures=["sig:witness-1", "sig:witness-2"],
            timestamp="2026-05-16T00:00:00Z",
        )
        assert env.outcome_quality == 0.7
        assert len(env.trust_dimension_updates) == 2
        assert len(env.witness_signatures) == 2

    def test_to_dict_minimal(self):
        env = ReputationEnvelope(
            action_id="a:1",
            outcome_class=OutcomeClass.SUCCESS,
        )
        d = env.to_dict()
        assert d["action_id"] == "a:1"
        assert d["outcome_class"] == "success"
        assert d["outcome_quality"] == 0.5
        assert d["propagation_scope"] == "responding_society"

    def test_to_dict_with_updates(self):
        env = ReputationEnvelope(
            action_id="a:2",
            outcome_class=OutcomeClass.VIOLATION,
            trust_dimension_updates={"talent": -0.3},
            witness_signatures=["sig:w1"],
            responding_society="s:beta",
        )
        d = env.to_dict()
        assert d["trust_dimension_updates"] == {"talent": -0.3}
        assert d["witness_signatures"] == ["sig:w1"]
        assert d["responding_society"] == "s:beta"

    def test_roundtrip(self):
        env = ReputationEnvelope(
            action_id="action:trade-99",
            outcome_class=OutcomeClass.PARTIAL,
            outcome_quality=0.65,
            responding_society="society:gamma",
            responding_society_signature="sig:gamma",
            trust_dimension_updates={"talent": 0.05, "training": 0.1},
            propagation_scope=PropagationScope.ENCOMPASSING_SOCIETY,
            witness_signatures=["sig:w1"],
            timestamp="2026-05-16T12:00:00Z",
        )
        d = env.to_dict()
        restored = ReputationEnvelope.from_dict(d)
        assert restored.action_id == env.action_id
        assert restored.outcome_class == env.outcome_class
        assert restored.outcome_quality == env.outcome_quality
        assert restored.responding_society == env.responding_society
        assert restored.propagation_scope == env.propagation_scope
        assert restored.trust_dimension_updates == env.trust_dimension_updates
        assert restored.witness_signatures == env.witness_signatures
        assert restored.timestamp == env.timestamp

    def test_frozen(self):
        env = ReputationEnvelope(
            action_id="a:1",
            outcome_class=OutcomeClass.SUCCESS,
        )
        try:
            env.action_id = "a:2"  # type: ignore[misc]
            assert False, "Should raise FrozenInstanceError"
        except AttributeError:
            pass


# ── MCPContextResource (§6.3) ─────────────────────────────────────


class TestMCPContextResource:
    def test_minimal_construction(self):
        res = MCPContextResource(name="session-state")
        assert res.name == "session-state"
        assert res.context_type == "session_state"

    def test_defaults(self):
        res = MCPContextResource(name="ctx")
        assert res.description == ""
        assert res.atp_cost == 1
        assert res.ttl == 3600
        assert res.snapshot == {}

    def test_full_construction(self):
        res = MCPContextResource(
            name="trust-evolution",
            context_type="trust_snapshot",
            description="Current trust tensor snapshot",
            trust_requirements=TrustRequirements(minimum_t3={"talent": 0.5}),
            atp_cost=10,
            ttl=1800,
            snapshot={"t3": {"talent": 0.8, "training": 0.6, "temperament": 0.7}},
        )
        assert res.context_type == "trust_snapshot"
        assert res.atp_cost == 10
        assert res.snapshot["t3"]["talent"] == 0.8

    def test_to_dict(self):
        res = MCPContextResource(
            name="mrh-graph",
            context_type="mrh_snapshot",
            description="MRH graph for current session",
            atp_cost=5,
        )
        d = res.to_dict()
        assert d["resource_type"] == MCPResourceType.CONTEXT.value
        assert d["name"] == "mrh-graph"
        assert d["context_type"] == "mrh_snapshot"
        assert d["description"] == "MRH graph for current session"
        assert d["atp_cost"] == 5

    def test_roundtrip(self):
        res = MCPContextResource(
            name="trust-evolution",
            context_type="trust_snapshot",
            description="Snapshot",
            atp_cost=10,
            ttl=900,
            snapshot={"version": 2, "data": [1, 2, 3]},
        )
        d = res.to_dict()
        restored = MCPContextResource.from_dict(d)
        assert restored.name == res.name
        assert restored.context_type == res.context_type
        assert restored.description == res.description
        assert restored.atp_cost == res.atp_cost
        assert restored.ttl == res.ttl
        assert restored.snapshot == res.snapshot

    def test_frozen(self):
        res = MCPContextResource(name="x")
        try:
            res.name = "y"  # type: ignore[misc]
            assert False, "Should raise FrozenInstanceError"
        except AttributeError:
            pass


# ── Package-level imports ─────────────────────────────────────────


class TestPackageExports:
    """Verify cross-society types are accessible from the web4 package."""

    def test_outcome_class_from_package(self):
        import web4

        assert hasattr(web4, "OutcomeClass")
        assert web4.OutcomeClass.SUCCESS.value == "success"

    def test_propagation_scope_from_package(self):
        import web4

        assert hasattr(web4, "PropagationScope")
        assert web4.PropagationScope.BOTH.value == "both"

    def test_cross_society_interaction_type_from_package(self):
        import web4

        assert hasattr(web4, "CrossSocietyInteractionType")
        assert web4.CrossSocietyInteractionType.FEDERATED.value == "federated"

    def test_cross_society_context_from_package(self):
        import web4

        assert hasattr(web4, "CrossSocietyContext")
        ctx = web4.CrossSocietyContext(
            sender_lct="lct:test",
            sender_society="s:a",
            responding_society="s:b",
        )
        assert ctx.sender_lct == "lct:test"

    def test_reputation_envelope_from_package(self):
        import web4

        assert hasattr(web4, "ReputationEnvelope")
        env = web4.ReputationEnvelope(
            action_id="a:1",
            outcome_class=web4.OutcomeClass.SUCCESS,
        )
        assert env.action_id == "a:1"

    def test_mcp_context_resource_from_package(self):
        import web4

        assert hasattr(web4, "MCPContextResource")
        res = web4.MCPContextResource(name="test")
        assert res.name == "test"

    def test_cross_society_error_from_package(self):
        import web4

        assert hasattr(web4, "CrossSocietyError")
        assert issubclass(web4.CrossSocietyError, web4.Web4Error)
