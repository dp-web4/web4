"""Tests for cross-society MCP types (mcp-protocol.md §7.3–7.6)."""

from web4.errors import (
    CrossSocietyError,
    ErrorCategory,
    ErrorCode,
    Web4Error,
    codes_for_category,
    get_error_meta,
    make_error,
)
from web4.mcp import (
    CrossSocietyContext,
    CrossSocietyInteractionType,
    MCPContextResource,
    OutcomeClass,
    PropagationScope,
    ReputationEnvelope,
    TrustContext,
    TrustRequirements,
)


# ── OutcomeClass Enum ────────────────────────────────────────────


class TestOutcomeClass:
    def test_enum_values(self) -> None:
        assert OutcomeClass.SUCCESS.value == "success"
        assert OutcomeClass.PARTIAL.value == "partial"
        assert OutcomeClass.FAILURE.value == "failure"
        assert OutcomeClass.VIOLATION.value == "violation"

    def test_enum_count(self) -> None:
        assert len(OutcomeClass) == 4

    def test_string_construction(self) -> None:
        assert OutcomeClass("success") is OutcomeClass.SUCCESS
        assert OutcomeClass("violation") is OutcomeClass.VIOLATION


# ── PropagationScope Enum ────────────────────────────────────────


class TestPropagationScope:
    def test_enum_values(self) -> None:
        assert PropagationScope.RESPONDING_SOCIETY.value == "responding_society"
        assert PropagationScope.CALLER_SOCIETY.value == "caller_society"
        assert PropagationScope.BOTH.value == "both"
        assert PropagationScope.ENCOMPASSING_SOCIETY.value == "encompassing_society"

    def test_enum_count(self) -> None:
        assert len(PropagationScope) == 4


# ── CrossSocietyInteractionType Enum ─────────────────────────────


class TestCrossSocietyInteractionType:
    def test_enum_values(self) -> None:
        assert CrossSocietyInteractionType.FIRST_CONTACT.value == "first_contact"
        assert CrossSocietyInteractionType.ESTABLISHED.value == "established"
        assert CrossSocietyInteractionType.FEDERATED.value == "federated"

    def test_enum_count(self) -> None:
        assert len(CrossSocietyInteractionType) == 3


# ── CrossSocietyContext ──────────────────────────────────────────


class TestCrossSocietyContext:
    def test_minimal_construction(self) -> None:
        ctx = CrossSocietyContext(
            sender_lct="lct:web4:entity:alice",
            sender_society="lct:web4:society:A",
            responding_society="lct:web4:society:B",
        )
        assert ctx.sender_lct == "lct:web4:entity:alice"
        assert ctx.sender_society == "lct:web4:society:A"
        assert ctx.responding_society == "lct:web4:society:B"
        assert ctx.interaction_type is CrossSocietyInteractionType.ESTABLISHED

    def test_full_construction(self) -> None:
        ctx = CrossSocietyContext(
            sender_lct="lct:web4:entity:alice",
            sender_society="lct:web4:society:A",
            responding_society="lct:web4:society:B",
            interaction_type=CrossSocietyInteractionType.FIRST_CONTACT,
            sender_role="web4:role:resource_consumer",
            responding_role_expected="web4:role:resource_provider",
            applicable_law_oracle="lct:web4:society:A:law-oracle",
            exchange_agreement_hash="sha256:abc123",
            atp_settlement_currency="ATP-A",
            atp_settlement_amount=100,
            atp_settlement_exchange_rate={"rate": 1.5, "referent": "compute_hour"},
            mrh_depth=2,
            law_hash="sha256:law123",
        )
        assert ctx.interaction_type is CrossSocietyInteractionType.FIRST_CONTACT
        assert ctx.atp_settlement_amount == 100

    def test_to_dict_minimal(self) -> None:
        ctx = CrossSocietyContext(
            sender_lct="lct:alice",
            sender_society="lct:society:A",
            responding_society="lct:society:B",
        )
        d = ctx.to_dict()
        assert d["sender_lct"] == "lct:alice"
        assert d["sender_society"] == "lct:society:A"
        assert d["responding_society"] == "lct:society:B"
        assert d["interaction_type"] == "established"
        assert "cross_society" in d
        assert d["cross_society"]["interaction_type"] == "established"
        assert d["mrh_depth"] == 1

    def test_to_dict_with_settlement(self) -> None:
        ctx = CrossSocietyContext(
            sender_lct="lct:alice",
            sender_society="lct:society:A",
            responding_society="lct:society:B",
            atp_settlement_currency="ATP-A",
            atp_settlement_amount=50,
        )
        d = ctx.to_dict()
        settlement = d["cross_society"]["atp_settlement"]
        assert settlement["currency"] == "ATP-A"
        assert settlement["amount"] == 50

    def test_roundtrip(self) -> None:
        ctx = CrossSocietyContext(
            sender_lct="lct:alice",
            sender_society="lct:society:A",
            responding_society="lct:society:B",
            interaction_type=CrossSocietyInteractionType.FEDERATED,
            sender_role="web4:role:consumer",
            responding_role_expected="web4:role:provider",
            applicable_law_oracle="lct:law-oracle:X",
            exchange_agreement_hash="sha256:xyz",
            atp_settlement_currency="ATP-A",
            atp_settlement_amount=100,
            atp_settlement_exchange_rate={"rate": 1.2},
            mrh_depth=3,
            law_hash="sha256:law",
        )
        d = ctx.to_dict()
        restored = CrossSocietyContext.from_dict(d)
        assert restored.sender_lct == ctx.sender_lct
        assert restored.sender_society == ctx.sender_society
        assert restored.responding_society == ctx.responding_society
        assert restored.interaction_type == ctx.interaction_type
        assert restored.sender_role == ctx.sender_role
        assert restored.responding_role_expected == ctx.responding_role_expected
        assert restored.applicable_law_oracle == ctx.applicable_law_oracle
        assert restored.exchange_agreement_hash == ctx.exchange_agreement_hash
        assert restored.atp_settlement_currency == ctx.atp_settlement_currency
        assert restored.atp_settlement_amount == ctx.atp_settlement_amount
        assert restored.atp_settlement_exchange_rate == ctx.atp_settlement_exchange_rate
        assert restored.mrh_depth == ctx.mrh_depth
        assert restored.law_hash == ctx.law_hash

    def test_frozen(self) -> None:
        ctx = CrossSocietyContext(
            sender_lct="lct:alice",
            sender_society="lct:society:A",
            responding_society="lct:society:B",
        )
        try:
            ctx.sender_lct = "changed"  # type: ignore[misc]
            assert False, "Should have raised"
        except AttributeError:
            pass


# ── ReputationEnvelope ───────────────────────────────────────────


class TestReputationEnvelope:
    def test_minimal_construction(self) -> None:
        env = ReputationEnvelope(
            action_id="action:123",
            outcome_class=OutcomeClass.SUCCESS,
        )
        assert env.action_id == "action:123"
        assert env.outcome_class is OutcomeClass.SUCCESS
        assert env.outcome_quality == 0.5
        assert env.propagation_scope is PropagationScope.RESPONDING_SOCIETY

    def test_full_construction(self) -> None:
        env = ReputationEnvelope(
            action_id="action:456",
            outcome_class=OutcomeClass.PARTIAL,
            outcome_quality=0.7,
            responding_society="lct:society:B",
            responding_society_signature="cose:sig123",
            trust_dimension_updates={"talent": 0.01, "training": 0.005},
            propagation_scope=PropagationScope.BOTH,
            witness_signatures=["cose:witness1", "cose:witness2"],
            timestamp="2026-05-15T12:00:00Z",
        )
        assert env.outcome_quality == 0.7
        assert len(env.trust_dimension_updates) == 2
        assert len(env.witness_signatures) == 2

    def test_to_dict_minimal(self) -> None:
        env = ReputationEnvelope(
            action_id="action:789",
            outcome_class=OutcomeClass.FAILURE,
        )
        d = env.to_dict()
        assert d["action_id"] == "action:789"
        assert d["outcome_class"] == "failure"
        assert d["outcome_quality"] == 0.5
        assert d["propagation_scope"] == "responding_society"
        assert "responding_society" not in d  # empty string omitted
        assert "witness_signatures" not in d  # empty list omitted

    def test_to_dict_full(self) -> None:
        env = ReputationEnvelope(
            action_id="action:456",
            outcome_class=OutcomeClass.VIOLATION,
            outcome_quality=0.1,
            responding_society="lct:society:B",
            responding_society_signature="cose:sig",
            trust_dimension_updates={"temperament": -0.05},
            propagation_scope=PropagationScope.ENCOMPASSING_SOCIETY,
            witness_signatures=["cose:w1"],
            timestamp="2026-05-15T12:00:00Z",
        )
        d = env.to_dict()
        assert d["outcome_class"] == "violation"
        assert d["responding_society"] == "lct:society:B"
        assert d["trust_dimension_updates"]["temperament"] == -0.05
        assert d["propagation_scope"] == "encompassing_society"
        assert d["witness_signatures"] == ["cose:w1"]
        assert d["timestamp"] == "2026-05-15T12:00:00Z"

    def test_roundtrip(self) -> None:
        env = ReputationEnvelope(
            action_id="action:rt",
            outcome_class=OutcomeClass.PARTIAL,
            outcome_quality=0.8,
            responding_society="lct:society:X",
            responding_society_signature="cose:sigX",
            trust_dimension_updates={"talent": 0.02, "training": -0.01},
            propagation_scope=PropagationScope.CALLER_SOCIETY,
            witness_signatures=["cose:w1", "cose:w2"],
            timestamp="2026-05-15T00:00:00Z",
        )
        d = env.to_dict()
        restored = ReputationEnvelope.from_dict(d)
        assert restored.action_id == env.action_id
        assert restored.outcome_class == env.outcome_class
        assert restored.outcome_quality == env.outcome_quality
        assert restored.responding_society == env.responding_society
        assert restored.responding_society_signature == env.responding_society_signature
        assert restored.trust_dimension_updates == env.trust_dimension_updates
        assert restored.propagation_scope == env.propagation_scope
        assert restored.witness_signatures == env.witness_signatures
        assert restored.timestamp == env.timestamp

    def test_frozen(self) -> None:
        env = ReputationEnvelope(
            action_id="action:f",
            outcome_class=OutcomeClass.SUCCESS,
        )
        try:
            env.action_id = "changed"  # type: ignore[misc]
            assert False, "Should have raised"
        except AttributeError:
            pass


# ── MCPContextResource ───────────────────────────────────────────


class TestMCPContextResource:
    def test_minimal_construction(self) -> None:
        res = MCPContextResource(name="session_state")
        assert res.name == "session_state"
        assert res.context_type == "session_state"
        assert res.atp_cost == 1
        assert res.ttl == 3600

    def test_full_construction(self) -> None:
        res = MCPContextResource(
            name="mrh_snapshot",
            context_type="mrh_graph",
            description="Current MRH graph snapshot",
            trust_requirements=TrustRequirements(
                minimum_t3={"talent": 0.5},
                atp_stake=10,
            ),
            atp_cost=5,
            ttl=1800,
            snapshot={"nodes": 42, "edges": 100},
        )
        assert res.context_type == "mrh_graph"
        assert res.atp_cost == 5
        assert res.snapshot["nodes"] == 42

    def test_to_dict(self) -> None:
        res = MCPContextResource(
            name="test_resource",
            description="A test resource",
            atp_cost=3,
        )
        d = res.to_dict()
        assert d["resource_type"] == "mcp_context"
        assert d["name"] == "test_resource"
        assert d["context_type"] == "session_state"
        assert d["description"] == "A test resource"
        assert d["atp_cost"] == 3
        assert d["ttl"] == 3600

    def test_roundtrip(self) -> None:
        res = MCPContextResource(
            name="trust_evolution",
            context_type="trust_history",
            description="Trust tensor evolution data",
            trust_requirements=TrustRequirements(
                minimum_t3={"talent": 0.3},
                atp_stake=5,
            ),
            atp_cost=2,
            ttl=7200,
            snapshot={"t3_values": [0.5, 0.6, 0.7]},
        )
        d = res.to_dict()
        restored = MCPContextResource.from_dict(d)
        assert restored.name == res.name
        assert restored.context_type == res.context_type
        assert restored.description == res.description
        assert restored.atp_cost == res.atp_cost
        assert restored.ttl == res.ttl
        assert restored.snapshot == res.snapshot


# ── Cross-Society Error Codes ────────────────────────────────────


class TestCrossSocietyErrors:
    def test_error_category_exists(self) -> None:
        assert ErrorCategory.CROSS_SOCIETY.value == "CROSS_SOCIETY"

    def test_error_code_count(self) -> None:
        cs_codes = codes_for_category(ErrorCategory.CROSS_SOCIETY)
        assert len(cs_codes) == 6

    def test_error_codes_match_spec(self) -> None:
        """Verify error codes match mcp-protocol.md §7.6 table."""
        expected = {
            ErrorCode.CROSS_SOCIETY_UNRECOGNIZED_LCT: 403,
            ErrorCode.CROSS_SOCIETY_EXCHANGE_INVALID: 409,
            ErrorCode.CROSS_SOCIETY_LAW_CONFLICT: 409,
            ErrorCode.CROSS_SOCIETY_WITNESS_REQUIRED: 412,
            ErrorCode.R7_REPUTATION_INVALID: 400,
            ErrorCode.PROPAGATION_SCOPE_UNSUPPORTED: 400,
        }
        for code, status in expected.items():
            meta = get_error_meta(code)
            assert meta.status == status, f"{code.name}: expected {status}, got {meta.status}"
            assert meta.category == ErrorCategory.CROSS_SOCIETY

    def test_make_error_returns_cross_society_error(self) -> None:
        err = make_error(ErrorCode.CROSS_SOCIETY_UNRECOGNIZED_LCT)
        assert isinstance(err, CrossSocietyError)
        assert isinstance(err, Web4Error)

    def test_from_problem_json_dispatch(self) -> None:
        err = make_error(
            ErrorCode.CROSS_SOCIETY_LAW_CONFLICT,
            detail="Law Oracle X disagrees with Law Oracle Y",
        )
        pj = err.to_problem_json()
        restored = Web4Error.from_problem_json(pj)
        assert isinstance(restored, CrossSocietyError)
        assert restored.code == ErrorCode.CROSS_SOCIETY_LAW_CONFLICT
        assert "Law Oracle X" in (restored.detail or "")

    def test_all_codes_roundtrip_via_problem_json(self) -> None:
        for code in codes_for_category(ErrorCategory.CROSS_SOCIETY):
            err = make_error(code, detail=f"Test detail for {code.name}")
            pj = err.to_problem_json()
            restored = Web4Error.from_problem_json(pj)
            assert restored.code == code
            assert isinstance(restored, CrossSocietyError)


# ── Root Exports ─────────────────────────────────────────────────


class TestRootExports:
    def test_mcp_types_exported(self) -> None:
        import web4

        for name in [
            "OutcomeClass",
            "PropagationScope",
            "CrossSocietyInteractionType",
            "CrossSocietyContext",
            "ReputationEnvelope",
            "MCPContextResource",
        ]:
            assert name in web4.__all__, f"{name} not in web4.__all__"
            assert hasattr(web4, name), f"{name} not importable from web4"

    def test_cross_society_error_exported(self) -> None:
        import web4

        assert "CrossSocietyError" in web4.__all__
        assert hasattr(web4, "CrossSocietyError")

    def test_export_count(self) -> None:
        import web4

        assert len(web4.__all__) == 376
