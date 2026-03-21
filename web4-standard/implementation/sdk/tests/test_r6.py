"""
Test web4 R7 action framework (r6 module).

Tests the R7 action grammar: Rules + Role + Request + Reference + Resource
→ Result + Reputation. Validates data structures, validation logic,
reputation computation, hash chaining, and cross-module integration.

Test vectors: web4-standard/test-vectors/r6/
"""

import json
import os

import pytest

from web4.trust import T3, V3
from web4.lct import LCT, EntityType
from web4.atp import ATPAccount
from web4.r6 import (
    # Enums & errors
    ActionStatus, R7Error, RuleViolation, RoleUnauthorized,
    RequestMalformed, ResourceInsufficient,
    # Components
    Constraint, Rules, Role, Request, ProofOfAgency,
    Precedent, WitnessAttestation, Reference,
    ResourceRequirements, Result,
    TensorDelta, ContributingFactor, ReputationDelta,
    # Composite
    R7Action, ActionChain,
    # Builder
    build_action,
    # JSON-LD
    R7_JSONLD_CONTEXT,
)

# ── Helpers ──────────────────────────────────────────────────────

VECTORS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "test-vectors")


def load_vectors(path: str) -> dict:
    full_path = os.path.join(VECTORS_DIR, path)
    with open(full_path) as f:
        return json.load(f)


# ══════════════════════════════════════════════════════════════════
#  COMPONENT CONSTRUCTION
# ══════════════════════════════════════════════════════════════════

class TestRules:
    """Rules component — constraints, permissions, prohibitions."""

    def test_empty_rules(self):
        rules = Rules()
        assert rules.has_permission("read")  # no permissions = permissive
        assert rules.to_dict()["lawHash"] == ""

    def test_permission_check(self):
        rules = Rules(permissions=["read", "write"], prohibitions=["delete"])
        assert rules.has_permission("read")
        assert rules.has_permission("write")
        assert not rules.has_permission("delete")  # prohibited
        assert not rules.has_permission("execute")  # not in allowed list

    def test_prohibition_overrides_permission(self):
        rules = Rules(permissions=["read", "delete"], prohibitions=["delete"])
        assert not rules.has_permission("delete")

    def test_constraint_minimum(self):
        rules = Rules(constraints=[
            Constraint(constraint_type="atp_minimum", value=50),
        ])
        assert rules.check_constraint("atp_minimum", 100)
        assert rules.check_constraint("atp_minimum", 50)
        assert not rules.check_constraint("atp_minimum", 49)

    def test_constraint_maximum(self):
        rules = Rules(constraints=[
            Constraint(constraint_type="rate_limit", value=100),
        ])
        assert rules.check_constraint("rate_limit", 50)
        assert rules.check_constraint("rate_limit", 100)
        assert not rules.check_constraint("rate_limit", 101)

    def test_no_matching_constraint(self):
        rules = Rules(constraints=[
            Constraint(constraint_type="atp_minimum", value=50),
        ])
        # No constraint for "rate_limit" → passes
        assert rules.check_constraint("rate_limit", 999)


class TestRole:
    """Role component — actor identity with T3/V3 context."""

    def test_role_with_tensors(self):
        t3 = T3(talent=0.85, training=0.90, temperament=0.88)
        v3 = V3(veracity=0.92, validity=0.88, valuation=0.85)
        role = Role(
            actor="lct:web4:entity:alice",
            role_lct="lct:web4:role:analyst:abc123",
            t3_in_role=t3,
            v3_in_role=v3,
        )
        d = role.to_dict()
        assert d["actor"] == "lct:web4:entity:alice"
        assert d["t3InRole"]["talent"] == 0.85
        assert d["v3InRole"]["veracity"] == 0.92

    def test_role_without_tensors(self):
        role = Role(actor="lct:web4:entity:bob", role_lct="lct:web4:role:reader:xyz")
        d = role.to_dict()
        assert "t3InRole" not in d
        assert "v3InRole" not in d


class TestRequest:
    """Request component — action intent."""

    def test_basic_request(self):
        req = Request(action="analyze_dataset", target="resource:data:quarterly")
        assert req.action == "analyze_dataset"
        d = req.to_dict()
        assert d["action"] == "analyze_dataset"
        assert d["atpStake"] == 0.0

    def test_request_with_agency(self):
        agency = ProofOfAgency(grant_id="agy:abc", scope="finance:payments")
        req = Request(
            action="approve_invoice",
            target="invoice:123",
            atp_stake=100.0,
            proof_of_agency=agency,
        )
        d = req.to_dict()
        assert d["proofOfAgency"]["grantId"] == "agy:abc"
        assert d["atpStake"] == 100.0


class TestReference:
    """Reference component — precedents and witnesses."""

    def test_with_precedents(self):
        ref = Reference(
            precedents=[Precedent(action_hash="sha256:abc", outcome="success", relevance=0.9)],
            witnesses=[WitnessAttestation(lct="lct:web4:witness:w1")],
            mrh_depth=2,
        )
        d = ref.to_dict()
        assert len(d["precedents"]) == 1
        assert d["precedents"][0]["relevance"] == 0.9
        assert d["mrhContext"]["depth"] == 2


class TestResourceRequirements:
    """Resource component — ATP and compute requirements."""

    def test_sufficient_atp(self):
        res = ResourceRequirements(required_atp=50, available_atp=100)
        assert res.has_sufficient_atp

    def test_insufficient_atp(self):
        res = ResourceRequirements(required_atp=100, available_atp=50)
        assert not res.has_sufficient_atp

    def test_escrow(self):
        res = ResourceRequirements(escrow_amount=100, escrow_condition="result_verified")
        d = res.to_dict()
        assert d["escrow"]["amount"] == 100


class TestResult:
    """Result component — action outcome."""

    def test_success_result(self):
        result = Result(
            status=ActionStatus.SUCCESS,
            output={"data": "analysis_complete"},
            atp_consumed=95.0,
        )
        d = result.to_dict()
        assert d["status"] == "success"
        assert d["resourceConsumed"]["atp"] == 95.0

    def test_failure_result(self):
        result = Result(
            status=ActionStatus.FAILURE,
            error="timeout exceeded",
            atp_consumed=10.0,
        )
        d = result.to_dict()
        assert d["status"] == "failure"
        assert d["error"]["message"] == "timeout exceeded"


class TestReputationDelta:
    """Reputation component — R7 innovation."""

    def test_positive_reputation(self):
        rep = ReputationDelta(
            subject_lct="lct:web4:entity:alice",
            role_lct="lct:web4:role:analyst:abc",
            t3_delta={
                "training": TensorDelta(change=0.01, from_value=0.90, to_value=0.91),
            },
            v3_delta={
                "veracity": TensorDelta(change=0.02, from_value=0.85, to_value=0.87),
            },
            reason="Completed analysis under deadline",
        )
        assert rep.net_trust_change == 0.01
        assert rep.net_value_change == 0.02

    def test_negative_reputation(self):
        rep = ReputationDelta(
            subject_lct="lct:web4:entity:bob",
            role_lct="lct:web4:role:engineer:xyz",
            t3_delta={
                "temperament": TensorDelta(change=-0.005, from_value=0.85, to_value=0.845),
            },
        )
        assert rep.net_trust_change == -0.005
        assert rep.net_value_change == 0.0

    def test_empty_reputation(self):
        rep = ReputationDelta(
            subject_lct="lct:web4:entity:charlie",
            role_lct="lct:web4:role:reader:abc",
        )
        assert rep.net_trust_change == 0.0
        assert rep.net_value_change == 0.0


# ══════════════════════════════════════════════════════════════════
#  R7 ACTION COMPOSITE
# ══════════════════════════════════════════════════════════════════

class TestR7Action:
    """Complete R7 action — all 7 components."""

    def test_action_construction(self):
        action = R7Action(
            rules=Rules(permissions=["read"]),
            role=Role(actor="lct:web4:entity:alice", role_lct="lct:web4:role:reader:abc"),
            request=Request(action="read", target="data:quarterly"),
            resource=ResourceRequirements(required_atp=1, available_atp=100),
        )
        assert action.action_id.startswith("r7:")
        assert action.is_valid
        assert action.timestamp != ""

    def test_action_validates_missing_actor(self):
        action = R7Action(
            role=Role(actor="", role_lct="lct:web4:role:reader:abc"),
            request=Request(action="read"),
        )
        errors = action.validate()
        assert "role.actor is required" in errors

    def test_action_validates_missing_role_lct(self):
        action = R7Action(
            role=Role(actor="lct:web4:entity:alice", role_lct=""),
            request=Request(action="read"),
        )
        errors = action.validate()
        assert "role.role_lct is required" in errors

    def test_action_validates_missing_action(self):
        action = R7Action(
            role=Role(actor="lct:web4:entity:alice", role_lct="lct:web4:role:reader:abc"),
            request=Request(action=""),
        )
        errors = action.validate()
        assert "request.action is required" in errors

    def test_action_validates_permission(self):
        action = R7Action(
            rules=Rules(prohibitions=["delete"]),
            role=Role(actor="lct:web4:entity:alice", role_lct="lct:web4:role:reader:abc"),
            request=Request(action="delete"),
            resource=ResourceRequirements(required_atp=0, available_atp=0),
        )
        errors = action.validate()
        assert any("not permitted" in e for e in errors)

    def test_action_validates_atp(self):
        action = R7Action(
            role=Role(actor="lct:web4:entity:alice", role_lct="lct:web4:role:reader:abc"),
            request=Request(action="read"),
            resource=ResourceRequirements(required_atp=100, available_atp=50),
        )
        errors = action.validate()
        assert any("insufficient ATP" in e for e in errors)

    def test_action_serialization(self):
        action = build_action(
            actor="lct:web4:entity:alice",
            role_lct="lct:web4:role:analyst:abc",
            action="analyze",
            target="data:quarterly",
            atp_stake=100,
            available_atp=500,
        )
        d = action.to_dict()
        assert "action_id" in d
        assert d["role"]["actor"] == "lct:web4:entity:alice"
        assert d["request"]["action"] == "analyze"
        assert d["resource"]["required"]["atp"] == 100

    def test_canonical_hash_deterministic(self):
        """Same inputs → same hash (determinism requirement)."""
        kwargs = dict(
            rules=Rules(law_hash="sha256:abc"),
            role=Role(actor="lct:alice", role_lct="lct:role:x", paired_at="2025-01-01T00:00:00Z"),
            request=Request(action="read", nonce="n1"),
            resource=ResourceRequirements(required_atp=1, available_atp=100),
            timestamp="2025-01-01T00:00:00Z",
        )
        a1 = R7Action(**kwargs)
        a2 = R7Action(**kwargs)
        assert a1.canonical_hash() == a2.canonical_hash()


# ══════════════════════════════════════════════════════════════════
#  REPUTATION COMPUTATION
# ══════════════════════════════════════════════════════════════════

class TestReputationComputation:
    """R7 reputation computation from action outcomes."""

    def test_positive_outcome(self):
        """High quality → positive T3/V3 deltas."""
        action = build_action(
            actor="lct:web4:entity:alice",
            role_lct="lct:web4:role:analyst:abc",
            action="analyze",
            target="data:quarterly",
            t3=T3(talent=0.85, training=0.90, temperament=0.88),
            v3=V3(veracity=0.80, validity=0.85, valuation=0.75),
        )
        action.result = Result(status=ActionStatus.SUCCESS)
        rep = action.compute_reputation(quality=0.9)

        assert rep.net_trust_change > 0
        assert rep.net_value_change > 0
        assert rep.subject_lct == "lct:web4:entity:alice"
        assert rep.role_lct == "lct:web4:role:analyst:abc"
        assert rep.action_type == "analyze"

    def test_negative_outcome(self):
        """Low quality → negative T3/V3 deltas."""
        action = build_action(
            actor="lct:web4:entity:bob",
            role_lct="lct:web4:role:engineer:xyz",
            action="deploy",
            t3=T3(talent=0.70, training=0.75, temperament=0.60),
            v3=V3(veracity=0.70, validity=0.70, valuation=0.65),
        )
        action.result = Result(status=ActionStatus.FAILURE, error="deployment crash")
        rep = action.compute_reputation(quality=0.2)

        assert rep.net_trust_change < 0
        assert rep.net_value_change < 0

    def test_neutral_outcome(self):
        """Quality 0.5 → no change."""
        action = build_action(
            actor="lct:web4:entity:charlie",
            role_lct="lct:web4:role:reader:abc",
            action="read",
            t3=T3(0.5, 0.5, 0.5),
            v3=V3(0.5, 0.5, 0.5),
        )
        action.result = Result(status=ActionStatus.SUCCESS)
        rep = action.compute_reputation(quality=0.5)

        assert rep.net_trust_change == 0.0
        assert rep.net_value_change == 0.0

    def test_reputation_stored_on_action(self):
        """compute_reputation() sets action.reputation."""
        action = build_action(
            actor="lct:alice", role_lct="lct:role:x", action="test",
        )
        action.result = Result(status=ActionStatus.SUCCESS)
        assert action.reputation is None
        action.compute_reputation(quality=0.8)
        assert action.reputation is not None
        assert action.reputation.action_id == action.action_id

    def test_reputation_with_factors(self):
        """Contributing factors are preserved."""
        action = build_action(
            actor="lct:alice", role_lct="lct:role:x", action="train_model",
            t3=T3(0.85, 0.88, 0.90),
        )
        action.result = Result(status=ActionStatus.SUCCESS)
        factors = [
            ContributingFactor(factor="model_accuracy", weight=0.5),
            ContributingFactor(factor="resource_efficiency", weight=0.3),
            ContributingFactor(factor="completion_time", weight=0.2),
        ]
        rep = action.compute_reputation(
            quality=0.9,
            rule_triggered="successful_training",
            factors=factors,
        )
        assert len(rep.contributing_factors) == 3
        assert rep.rule_triggered == "successful_training"

    def test_reputation_bounded(self):
        """T3/V3 values clamped to [0, 1] after update."""
        action = build_action(
            actor="lct:alice", role_lct="lct:role:x", action="test",
            t3=T3(0.99, 0.99, 0.99),
            v3=V3(0.99, 0.99, 0.99),
        )
        action.result = Result(status=ActionStatus.SUCCESS)
        rep = action.compute_reputation(quality=1.0)

        for delta in rep.t3_delta.values():
            assert delta.to_value <= 1.0
        for delta in rep.v3_delta.values():
            assert delta.to_value <= 1.0


# ══════════════════════════════════════════════════════════════════
#  HASH CHAIN
# ══════════════════════════════════════════════════════════════════

class TestActionChain:
    """ActionChain — tamper-evident audit trail."""

    def test_empty_chain(self):
        chain = ActionChain()
        assert chain.length == 0
        assert chain.head is None
        assert chain.verify_chain()

    def test_single_action(self):
        chain = ActionChain()
        a = build_action(actor="lct:alice", role_lct="lct:role:x", action="read")
        chain.append(a)
        assert chain.length == 1
        assert a.prev_action_hash == ""
        assert chain.verify_chain()

    def test_chain_linking(self):
        chain = ActionChain()
        a1 = build_action(actor="lct:alice", role_lct="lct:role:x", action="read")
        a2 = build_action(actor="lct:alice", role_lct="lct:role:x", action="write")
        a3 = build_action(actor="lct:alice", role_lct="lct:role:x", action="analyze")

        chain.append(a1)
        chain.append(a2)
        chain.append(a3)

        assert chain.length == 3
        assert a2.prev_action_hash == a1.canonical_hash()
        assert a3.prev_action_hash == a2.canonical_hash()
        assert chain.verify_chain()

    def test_chain_tamper_detection(self):
        chain = ActionChain()
        a1 = build_action(actor="lct:alice", role_lct="lct:role:x", action="read")
        a2 = build_action(actor="lct:alice", role_lct="lct:role:x", action="write")
        chain.append(a1)
        chain.append(a2)

        # Tamper with a1's request
        a1.request.action = "TAMPERED"

        # Chain should now be invalid — a2's prev hash no longer matches a1
        assert not chain.verify_chain()

    def test_chain_serialization(self):
        chain = ActionChain()
        chain.append(build_action(actor="lct:alice", role_lct="lct:role:x", action="read"))
        chain.append(build_action(actor="lct:alice", role_lct="lct:role:x", action="write"))

        d = chain.to_dict()
        assert d["length"] == 2
        assert d["chain_valid"] is True
        assert len(d["actions"]) == 2


# ══════════════════════════════════════════════════════════════════
#  BUILDER
# ══════════════════════════════════════════════════════════════════

class TestBuildAction:
    """build_action() convenience function."""

    def test_minimal_build(self):
        action = build_action(
            actor="lct:web4:entity:alice",
            role_lct="lct:web4:role:reader:abc",
            action="read",
        )
        assert action.role.actor == "lct:web4:entity:alice"
        assert action.request.action == "read"
        assert action.request.nonce != ""  # auto-generated

    def test_build_with_tensors(self):
        t3 = T3(0.85, 0.90, 0.88)
        v3 = V3(0.80, 0.85, 0.92)
        action = build_action(
            actor="lct:alice",
            role_lct="lct:role:analyst",
            action="analyze",
            target="data:quarterly",
            t3=t3, v3=v3,
            atp_stake=100, available_atp=500,
        )
        assert action.role.t3_in_role.talent == 0.85
        assert action.role.v3_in_role.veracity == 0.85
        assert action.resource.required_atp == 100
        assert action.is_valid

    def test_build_with_society(self):
        action = build_action(
            actor="lct:alice",
            role_lct="lct:role:citizen",
            action="vote",
            society="lct:web4:society:genesis",
            law_hash="sha256:abc",
        )
        assert action.rules.society == "lct:web4:society:genesis"
        assert action.rules.law_hash == "sha256:abc"


# ══════════════════════════════════════════════════════════════════
#  CROSS-MODULE INTEGRATION
# ══════════════════════════════════════════════════════════════════

class TestCrossModuleIntegration:
    """R7 actions integrating with trust, lct, atp, federation modules."""

    def test_lct_entity_creates_action(self):
        """An LCT entity can construct an R7 action."""
        lct = LCT.create(
            entity_type=EntityType.AI,
            public_key="test_key_r7",
            society="lct:web4:society:genesis",
            witnesses=["lct:web4:witness:w1"],
        )
        action = build_action(
            actor=lct.lct_id,
            role_lct=lct.birth_certificate.citizen_role,
            action="interact",
            t3=lct.t3,
            v3=lct.v3,
        )
        assert action.role.actor == lct.lct_id
        assert action.is_valid

    def test_trust_update_via_reputation(self):
        """R7 reputation computation uses T3.update() from trust module."""
        t3 = T3(talent=0.85, training=0.90, temperament=0.88)
        action = build_action(
            actor="lct:alice",
            role_lct="lct:role:analyst",
            action="analyze",
            t3=t3,
        )
        action.result = Result(status=ActionStatus.SUCCESS)
        rep = action.compute_reputation(quality=0.9)

        # Verify T3 deltas use canonical update math
        updated_t3 = t3.update(0.9)
        for dim in ("talent", "training", "temperament"):
            expected_change = getattr(updated_t3, dim) - getattr(t3, dim)
            if dim in rep.t3_delta:
                assert abs(rep.t3_delta[dim].change - expected_change) < 1e-9

    def test_atp_resource_tracking(self):
        """R7 resources track ATP via ATPAccount."""
        account = ATPAccount(available=500.0)
        action = build_action(
            actor="lct:alice",
            role_lct="lct:role:analyst",
            action="analyze",
            atp_stake=100,
            available_atp=account.available,
        )
        assert action.resource.has_sufficient_atp
        assert action.is_valid

    def test_action_chain_with_reputation(self):
        """Chain of actions each with reputation deltas."""
        chain = ActionChain()

        # Action 1: successful read
        a1 = build_action(
            actor="lct:alice", role_lct="lct:role:reader", action="read",
            t3=T3(0.5, 0.5, 0.5), v3=V3(0.5, 0.5, 0.5),
        )
        a1.result = Result(status=ActionStatus.SUCCESS)
        a1.compute_reputation(quality=0.8)
        chain.append(a1)

        # Action 2: failed write
        a2 = build_action(
            actor="lct:alice", role_lct="lct:role:writer", action="write",
            t3=T3(0.5, 0.5, 0.5), v3=V3(0.5, 0.5, 0.5),
        )
        a2.result = Result(status=ActionStatus.FAILURE, error="disk full")
        a2.compute_reputation(quality=0.2)
        chain.append(a2)

        assert chain.length == 2
        assert chain.verify_chain()

        # First action positive, second negative
        assert a1.reputation.net_trust_change > 0
        assert a2.reputation.net_trust_change < 0

        # Both have role context
        assert a1.reputation.role_lct == "lct:role:reader"
        assert a2.reputation.role_lct == "lct:role:writer"


# ══════════════════════════════════════════════════════════════════
#  TEST VECTORS
# ══════════════════════════════════════════════════════════════════

class TestR6Vectors:
    """Tests against r6/action-operations.json vectors."""

    @classmethod
    def setup_class(cls):
        try:
            cls.vectors = load_vectors("r6/action-operations.json")["vectors"]
        except FileNotFoundError:
            pytest.skip("R6 test vectors not yet generated")

    def _vec(self, vec_id: str) -> dict:
        return next(v for v in self.vectors if v["id"] == vec_id)

    # r6-001: Action construction and validation
    def test_action_construction(self):
        v = self._vec("r6-001")
        inp = v["input"]
        action = build_action(
            actor=inp["actor"],
            role_lct=inp["role_lct"],
            action=inp["action"],
            target=inp.get("target", ""),
            atp_stake=inp.get("atp_stake", 0),
            available_atp=inp.get("available_atp", 0),
        )
        expected = v["expected"]
        assert action.is_valid == expected["is_valid"]

    # r6-002: Reputation from positive outcome
    def test_reputation_positive(self):
        v = self._vec("r6-002")
        inp = v["input"]
        t3 = T3(**inp["t3"])
        action = build_action(
            actor=inp["actor"],
            role_lct=inp["role_lct"],
            action=inp["action"],
            t3=t3,
        )
        action.result = Result(status=ActionStatus.SUCCESS)
        rep = action.compute_reputation(quality=inp["quality"])
        expected = v["expected"]
        assert abs(rep.net_trust_change - expected["net_trust_change"]) < v["tolerance"]

    # r6-003: Reputation from negative outcome
    def test_reputation_negative(self):
        v = self._vec("r6-003")
        inp = v["input"]
        t3 = T3(**inp["t3"])
        action = build_action(
            actor=inp["actor"],
            role_lct=inp["role_lct"],
            action=inp["action"],
            t3=t3,
        )
        action.result = Result(status=ActionStatus.FAILURE)
        rep = action.compute_reputation(quality=inp["quality"])
        expected = v["expected"]
        assert abs(rep.net_trust_change - expected["net_trust_change"]) < v["tolerance"]

    # r6-004: Hash chain integrity
    def test_chain_integrity(self):
        v = self._vec("r6-004")
        inp = v["input"]
        chain = ActionChain()
        for act_data in inp["actions"]:
            a = R7Action(
                rules=Rules(law_hash=act_data.get("law_hash", "")),
                role=Role(actor=act_data["actor"], role_lct=act_data["role_lct"],
                          paired_at="2025-01-01T00:00:00Z"),
                request=Request(action=act_data["action"], nonce=act_data.get("nonce", "")),
                resource=ResourceRequirements(),
                timestamp=act_data.get("timestamp", "2025-01-01T00:00:00Z"),
            )
            chain.append(a)
        expected = v["expected"]
        assert chain.verify_chain() == expected["chain_valid"]
        assert chain.length == expected["length"]


# ══════════════════════════════════════════════════════════════════
#  JSON-LD SERIALIZATION
# ══════════════════════════════════════════════════════════════════

class TestReputationDeltaJsonLD:
    """ReputationDelta JSON-LD serialization and roundtrip."""

    def test_jsonld_structure(self):
        """JSON-LD output has @context and @type."""
        rep = ReputationDelta(
            subject_lct="lct:web4:entity:alice",
            role_lct="lct:web4:role:analyst:abc",
            action_type="analyze",
            action_target="data:quarterly",
            action_id="r7:abc123",
            t3_delta={
                "training": TensorDelta(change=0.01, from_value=0.90, to_value=0.91),
            },
            reason="Completed analysis",
            timestamp="2025-09-15T17:55:00Z",
        )
        doc = rep.to_jsonld()
        assert doc["@context"] == [R7_JSONLD_CONTEXT]
        assert doc["@type"] == "ReputationDelta"
        assert doc["subject_lct"] == "lct:web4:entity:alice"
        assert doc["role_lct"] == "lct:web4:role:analyst:abc"
        assert doc["net_trust_change"] == 0.01
        assert doc["net_value_change"] == 0.0

    def test_jsonld_optional_fields_excluded(self):
        """Empty optional fields are excluded from JSON-LD output."""
        rep = ReputationDelta(
            subject_lct="lct:alice",
            role_lct="lct:role:x",
        )
        doc = rep.to_jsonld()
        assert "rule_triggered" not in doc
        assert "reason" not in doc
        assert "t3_delta" not in doc
        assert "v3_delta" not in doc
        assert "contributing_factors" not in doc
        assert "witnesses" not in doc
        assert "timestamp" not in doc

    def test_jsonld_roundtrip(self):
        """from_jsonld(rep.to_jsonld()) produces equivalent object."""
        rep = ReputationDelta(
            subject_lct="lct:web4:entity:alice",
            role_lct="lct:web4:role:analyst:abc",
            action_type="analyze",
            action_target="data:quarterly",
            action_id="r7:abc123",
            rule_triggered="successful_analysis",
            reason="Completed high-quality analysis",
            t3_delta={
                "training": TensorDelta(change=0.01, from_value=0.90, to_value=0.91),
                "temperament": TensorDelta(change=0.005, from_value=0.88, to_value=0.885),
            },
            v3_delta={
                "veracity": TensorDelta(change=0.02, from_value=0.85, to_value=0.87),
            },
            contributing_factors=[
                ContributingFactor(factor="deadline_met", weight=0.6),
                ContributingFactor(factor="accuracy", weight=0.4),
            ],
            witnesses=[
                WitnessAttestation(lct="lct:web4:witness:w1", attestation="verified"),
            ],
            timestamp="2025-09-15T17:55:00Z",
        )
        doc = rep.to_jsonld()
        restored = ReputationDelta.from_jsonld(doc)

        assert restored.subject_lct == rep.subject_lct
        assert restored.role_lct == rep.role_lct
        assert restored.action_type == rep.action_type
        assert restored.action_id == rep.action_id
        assert restored.rule_triggered == rep.rule_triggered
        assert restored.reason == rep.reason
        assert len(restored.t3_delta) == 2
        assert abs(restored.t3_delta["training"].change - 0.01) < 1e-9
        assert abs(restored.t3_delta["temperament"].to_value - 0.885) < 1e-9
        assert len(restored.v3_delta) == 1
        assert abs(restored.v3_delta["veracity"].change - 0.02) < 1e-9
        assert len(restored.contributing_factors) == 2
        assert restored.contributing_factors[0].factor == "deadline_met"
        assert len(restored.witnesses) == 1
        assert restored.timestamp == "2025-09-15T17:55:00Z"
        assert abs(restored.net_trust_change - rep.net_trust_change) < 1e-9
        assert abs(restored.net_value_change - rep.net_value_change) < 1e-9

    def test_from_jsonld_plain_dict(self):
        """from_jsonld accepts plain dict (no @context)."""
        data = {
            "subject_lct": "lct:bob",
            "role_lct": "lct:role:eng",
            "t3_delta": {
                "talent": {"change": -0.01, "from": 0.80, "to": 0.79},
            },
        }
        rep = ReputationDelta.from_jsonld(data)
        assert rep.subject_lct == "lct:bob"
        assert rep.t3_delta["talent"].change == -0.01


class TestR7ActionJsonLD:
    """R7Action JSON-LD serialization and roundtrip."""

    def _make_full_action(self) -> R7Action:
        """Create a fully-populated R7Action for testing."""
        return R7Action(
            rules=Rules(
                law_hash="sha256:governance_v2",
                society="lct:web4:society:genesis",
                constraints=[
                    Constraint(constraint_type="atp_minimum", value=50),
                    Constraint(constraint_type="rate_limit", value=100),
                ],
                permissions=["read", "analyze"],
                prohibitions=["delete"],
            ),
            role=Role(
                actor="lct:web4:entity:alice",
                role_lct="lct:web4:role:analyst:abc123",
                paired_at="2025-09-15T12:00:00Z",
                t3_in_role=T3(talent=0.85, training=0.90, temperament=0.88),
                v3_in_role=V3(veracity=0.92, validity=0.88, valuation=0.85),
            ),
            request=Request(
                action="analyze_dataset",
                target="resource:web4:dataset:quarterly",
                parameters={"algorithm": "neural_net_v2"},
                atp_stake=100.0,
                nonce="unique_nonce_001",
            ),
            reference=Reference(
                precedents=[
                    Precedent(action_hash="sha256:prev_analysis", outcome="success", relevance=0.9),
                ],
                mrh_depth=2,
                relevant_entities=["lct:web4:entity:bob"],
                witnesses=[
                    WitnessAttestation(lct="lct:web4:witness:w1", attestation="verified"),
                ],
            ),
            resource=ResourceRequirements(
                required_atp=100.0,
                available_atp=500.0,
                escrow_amount=100.0,
                escrow_condition="result_verified",
            ),
            result=Result(
                status=ActionStatus.SUCCESS,
                output={"data": "analysis_complete", "confidence": 0.95},
                atp_consumed=95.0,
            ),
            timestamp="2025-09-15T17:55:00Z",
        )

    def test_jsonld_structure(self):
        """JSON-LD output has @context, @type, and all 7 components."""
        action = self._make_full_action()
        doc = action.to_jsonld()

        assert doc["@context"] == [R7_JSONLD_CONTEXT]
        assert doc["@type"] == "R7Action"
        assert doc["action_id"].startswith("r7:")
        assert doc["timestamp"] == "2025-09-15T17:55:00Z"
        assert "rules" in doc
        assert "role" in doc
        assert "request" in doc
        assert "reference" in doc
        assert "resource" in doc
        assert "result" in doc

    def test_jsonld_rules_component(self):
        """Rules are correctly serialized."""
        action = self._make_full_action()
        doc = action.to_jsonld()
        rules = doc["rules"]

        assert rules["lawHash"] == "sha256:governance_v2"
        assert rules["society"] == "lct:web4:society:genesis"
        assert len(rules["constraints"]) == 2
        assert rules["permissions"] == ["read", "analyze"]
        assert rules["prohibitions"] == ["delete"]

    def test_jsonld_role_with_tensors(self):
        """Role includes T3/V3 when present."""
        action = self._make_full_action()
        doc = action.to_jsonld()
        role = doc["role"]

        assert role["actor"] == "lct:web4:entity:alice"
        assert role["roleLCT"] == "lct:web4:role:analyst:abc123"
        assert role["t3InRole"]["talent"] == 0.85
        assert role["v3InRole"]["veracity"] == 0.92

    def test_jsonld_role_without_tensors(self):
        """Role omits T3/V3 when absent."""
        action = build_action(
            actor="lct:bob",
            role_lct="lct:role:reader",
            action="read",
        )
        doc = action.to_jsonld()
        assert "t3InRole" not in doc["role"]
        assert "v3InRole" not in doc["role"]

    def test_jsonld_request_with_agency(self):
        """Request includes proofOfAgency when present."""
        action = R7Action(
            role=Role(actor="lct:alice", role_lct="lct:role:x"),
            request=Request(
                action="delegate",
                proof_of_agency=ProofOfAgency(
                    grant_id="agy:abc",
                    scope="finance:payments",
                    audience=["mcp:web4://tool/*"],
                ),
            ),
            timestamp="2025-01-01T00:00:00Z",
        )
        doc = action.to_jsonld()
        assert doc["request"]["proofOfAgency"]["grantId"] == "agy:abc"
        assert doc["request"]["proofOfAgency"]["scope"] == "finance:payments"

    def test_jsonld_no_reputation_when_not_computed(self):
        """Reputation is excluded when not computed."""
        action = self._make_full_action()
        doc = action.to_jsonld()
        assert "reputation" not in doc

    def test_jsonld_reputation_included_when_computed(self):
        """Reputation is included as first-class output when computed."""
        action = self._make_full_action()
        action.compute_reputation(
            quality=0.9,
            rule_triggered="successful_analysis",
            factors=[ContributingFactor(factor="deadline_met", weight=0.6)],
        )
        doc = action.to_jsonld()

        assert "reputation" in doc
        rep = doc["reputation"]
        assert rep["subject_lct"] == "lct:web4:entity:alice"
        assert rep["role_lct"] == "lct:web4:role:analyst:abc123"
        assert rep["net_trust_change"] > 0
        assert rep["rule_triggered"] == "successful_analysis"
        assert len(rep["contributing_factors"]) == 1

    def test_jsonld_prev_action_hash(self):
        """prev_action_hash included only when non-empty."""
        action = self._make_full_action()
        doc = action.to_jsonld()
        assert "prev_action_hash" not in doc  # no chain link yet

        action.prev_action_hash = "sha256:abc123def456"
        doc = action.to_jsonld()
        assert doc["prev_action_hash"] == "sha256:abc123def456"

    def test_jsonld_string_roundtrip(self):
        """to_jsonld_string → from_jsonld_string roundtrip."""
        action = self._make_full_action()
        action.compute_reputation(quality=0.85)

        json_str = action.to_jsonld_string()
        restored = R7Action.from_jsonld_string(json_str)

        assert restored.action_id == action.action_id
        assert restored.timestamp == action.timestamp
        assert restored.role.actor == action.role.actor
        assert restored.request.action == action.request.action

    def test_jsonld_roundtrip_minimal(self):
        """Minimal action roundtrip preserves structure."""
        action = build_action(
            actor="lct:alice",
            role_lct="lct:role:reader",
            action="read",
            target="data:test",
        )
        doc = action.to_jsonld()
        restored = R7Action.from_jsonld(doc)

        assert restored.action_id == action.action_id
        assert restored.role.actor == "lct:alice"
        assert restored.role.role_lct == "lct:role:reader"
        assert restored.request.action == "read"
        assert restored.request.target == "data:test"

    def test_jsonld_roundtrip_full(self):
        """Full action with all components roundtrip."""
        action = self._make_full_action()
        action.compute_reputation(
            quality=0.9,
            rule_triggered="successful_analysis",
            reason="High-quality analysis under deadline",
            factors=[
                ContributingFactor(factor="deadline_met", weight=0.6),
                ContributingFactor(factor="accuracy", weight=0.4),
            ],
        )
        doc = action.to_jsonld()
        restored = R7Action.from_jsonld(doc)

        # Identity
        assert restored.action_id == action.action_id
        assert restored.timestamp == action.timestamp

        # Rules
        assert restored.rules.law_hash == "sha256:governance_v2"
        assert restored.rules.society == "lct:web4:society:genesis"
        assert len(restored.rules.constraints) == 2
        assert restored.rules.permissions == ["read", "analyze"]
        assert restored.rules.prohibitions == ["delete"]

        # Role
        assert restored.role.actor == "lct:web4:entity:alice"
        assert restored.role.role_lct == "lct:web4:role:analyst:abc123"
        assert restored.role.t3_in_role.talent == 0.85
        assert restored.role.v3_in_role.veracity == 0.92

        # Request
        assert restored.request.action == "analyze_dataset"
        assert restored.request.target == "resource:web4:dataset:quarterly"
        assert restored.request.parameters == {"algorithm": "neural_net_v2"}
        assert restored.request.atp_stake == 100.0
        assert restored.request.nonce == "unique_nonce_001"

        # Reference
        assert len(restored.reference.precedents) == 1
        assert restored.reference.precedents[0].action_hash == "sha256:prev_analysis"
        assert restored.reference.mrh_depth == 2
        assert restored.reference.relevant_entities == ["lct:web4:entity:bob"]
        assert len(restored.reference.witnesses) == 1

        # Resource
        assert restored.resource.required_atp == 100.0
        assert restored.resource.available_atp == 500.0
        assert restored.resource.escrow_amount == 100.0

        # Result
        assert restored.result.status == ActionStatus.SUCCESS
        assert restored.result.atp_consumed == 95.0

        # Reputation
        assert restored.reputation is not None
        assert restored.reputation.subject_lct == "lct:web4:entity:alice"
        assert restored.reputation.rule_triggered == "successful_analysis"
        assert restored.reputation.net_trust_change > 0

    def test_jsonld_roundtrip_with_proof_of_agency(self):
        """ProofOfAgency roundtrips correctly."""
        action = R7Action(
            role=Role(actor="lct:alice", role_lct="lct:role:agent"),
            request=Request(
                action="delegate",
                target="service:payment",
                proof_of_agency=ProofOfAgency(
                    grant_id="agy:delegation_001",
                    inclusion_proof="hash:merkle_proof",
                    scope="finance:payments",
                    audience=["mcp:web4://tool/*"],
                ),
                nonce="nonce123",
            ),
            timestamp="2025-01-01T00:00:00Z",
        )
        doc = action.to_jsonld()
        restored = R7Action.from_jsonld(doc)

        assert restored.request.proof_of_agency is not None
        assert restored.request.proof_of_agency.grant_id == "agy:delegation_001"
        assert restored.request.proof_of_agency.scope == "finance:payments"
        assert restored.request.proof_of_agency.audience == ["mcp:web4://tool/*"]

    def test_jsonld_roundtrip_failure_result(self):
        """Failed action with error roundtrips correctly."""
        action = build_action(
            actor="lct:bob",
            role_lct="lct:role:engineer",
            action="deploy",
            target="service:prod",
            t3=T3(0.70, 0.75, 0.60),
        )
        action.result = Result(
            status=ActionStatus.FAILURE,
            error="deployment timeout exceeded",
            atp_consumed=10.0,
        )
        action.compute_reputation(quality=0.2)

        doc = action.to_jsonld()
        restored = R7Action.from_jsonld(doc)

        assert restored.result.status == ActionStatus.FAILURE
        assert restored.result.error == "deployment timeout exceeded"
        assert restored.result.atp_consumed == 10.0
        assert restored.reputation is not None
        assert restored.reputation.net_trust_change < 0

    def test_jsonld_escrow_roundtrip(self):
        """Escrow fields roundtrip correctly."""
        action = R7Action(
            role=Role(actor="lct:alice", role_lct="lct:role:x"),
            request=Request(action="escrow_test"),
            resource=ResourceRequirements(
                required_atp=100.0,
                available_atp=500.0,
                escrow_amount=100.0,
                escrow_condition="result_verified",
            ),
            timestamp="2025-01-01T00:00:00Z",
        )
        doc = action.to_jsonld()
        assert "escrow" in doc["resource"]
        assert doc["resource"]["escrow"]["amount"] == 100.0

        restored = R7Action.from_jsonld(doc)
        assert restored.resource.escrow_amount == 100.0
        assert restored.resource.escrow_condition == "result_verified"


class TestActionChainJsonLD:
    """ActionChain JSON-LD serialization and roundtrip."""

    def test_empty_chain_jsonld(self):
        """Empty chain produces valid JSON-LD."""
        chain = ActionChain()
        doc = chain.to_jsonld()

        assert doc["@context"] == [R7_JSONLD_CONTEXT]
        assert doc["@type"] == "ActionChain"
        assert doc["length"] == 0
        assert doc["actions"] == []
        assert doc["chain_valid"] is True

    def test_chain_jsonld_structure(self):
        """Chain JSON-LD includes all actions with context."""
        chain = ActionChain()
        chain.append(build_action(actor="lct:alice", role_lct="lct:role:x", action="read"))
        chain.append(build_action(actor="lct:alice", role_lct="lct:role:x", action="write"))

        doc = chain.to_jsonld()
        assert doc["length"] == 2
        assert doc["chain_valid"] is True
        assert len(doc["actions"]) == 2
        # Each action in the chain has its own @type
        assert all(a["@type"] == "R7Action" for a in doc["actions"])

    def test_chain_jsonld_roundtrip(self):
        """Chain roundtrip preserves actions and hash linking."""
        chain = ActionChain()
        a1 = build_action(
            actor="lct:alice", role_lct="lct:role:x", action="read",
            t3=T3(0.5, 0.5, 0.5),
        )
        a1.result = Result(status=ActionStatus.SUCCESS)
        a1.compute_reputation(quality=0.8)
        chain.append(a1)

        a2 = build_action(
            actor="lct:alice", role_lct="lct:role:x", action="write",
        )
        chain.append(a2)

        doc = chain.to_jsonld()
        restored = ActionChain.from_jsonld(doc)

        assert restored.length == 2
        assert restored.verify_chain()
        assert restored.actions[0].action_id == a1.action_id
        assert restored.actions[1].action_id == a2.action_id
        assert restored.actions[1].prev_action_hash == a1.canonical_hash()
        assert restored.actions[0].reputation is not None

    def test_chain_jsonld_roundtrip_with_reputation(self):
        """Chain with reputation deltas roundtrips correctly."""
        chain = ActionChain()

        a1 = build_action(
            actor="lct:alice", role_lct="lct:role:analyst", action="analyze",
            t3=T3(0.8, 0.8, 0.8), v3=V3(0.7, 0.7, 0.7),
        )
        a1.result = Result(status=ActionStatus.SUCCESS)
        a1.compute_reputation(quality=0.9)
        chain.append(a1)

        a2 = build_action(
            actor="lct:alice", role_lct="lct:role:analyst", action="report",
            t3=T3(0.8, 0.8, 0.8), v3=V3(0.7, 0.7, 0.7),
        )
        a2.result = Result(status=ActionStatus.FAILURE, error="report format invalid")
        a2.compute_reputation(quality=0.3)
        chain.append(a2)

        doc = chain.to_jsonld()
        restored = ActionChain.from_jsonld(doc)

        assert restored.length == 2
        assert restored.verify_chain()
        assert restored.actions[0].reputation.net_trust_change > 0
        assert restored.actions[1].reputation.net_trust_change < 0


class TestJsonLDSchemaValidation:
    """Validate JSON-LD output against JSON Schema (if jsonschema available)."""

    @classmethod
    def setup_class(cls):
        try:
            import jsonschema
            cls.jsonschema = jsonschema
        except ImportError:
            pytest.skip("jsonschema not installed")

        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "schemas",
            "r7-action-jsonld.schema.json",
        )
        with open(schema_path) as f:
            cls.schema = json.load(f)

    def test_minimal_action_validates(self):
        """Minimal action output passes schema validation."""
        action = build_action(
            actor="lct:alice",
            role_lct="lct:role:reader",
            action="read",
        )
        doc = action.to_jsonld()
        self.jsonschema.validate(doc, self.schema)

    def test_full_action_validates(self):
        """Full action with all components passes schema validation."""
        action = R7Action(
            rules=Rules(
                law_hash="sha256:abc",
                society="lct:society:genesis",
                constraints=[Constraint(constraint_type="atp_minimum", value=50)],
                permissions=["read"],
            ),
            role=Role(
                actor="lct:web4:entity:alice",
                role_lct="lct:web4:role:analyst:abc",
                paired_at="2025-09-15T12:00:00Z",
                t3_in_role=T3(0.85, 0.90, 0.88),
                v3_in_role=V3(0.80, 0.85, 0.92),
            ),
            request=Request(
                action="analyze",
                target="data:quarterly",
                atp_stake=100.0,
                nonce="nonce_001",
            ),
            reference=Reference(
                precedents=[Precedent(action_hash="sha256:prev", outcome="success", relevance=0.9)],
                mrh_depth=2,
                relevant_entities=["lct:web4:entity:bob"],
                witnesses=[WitnessAttestation(lct="lct:witness:w1")],
            ),
            resource=ResourceRequirements(
                required_atp=100.0,
                available_atp=500.0,
                escrow_amount=100.0,
            ),
            result=Result(
                status=ActionStatus.SUCCESS,
                output={"data": "done"},
                atp_consumed=95.0,
            ),
            timestamp="2025-09-15T17:55:00Z",
        )
        action.compute_reputation(
            quality=0.9,
            rule_triggered="success",
            factors=[ContributingFactor(factor="deadline_met", weight=0.6)],
        )
        doc = action.to_jsonld()
        self.jsonschema.validate(doc, self.schema)

    def test_action_with_proof_of_agency_validates(self):
        """Action with ProofOfAgency passes schema validation."""
        action = R7Action(
            role=Role(actor="lct:alice", role_lct="lct:role:agent"),
            request=Request(
                action="delegate",
                proof_of_agency=ProofOfAgency(
                    grant_id="agy:abc",
                    scope="finance",
                    audience=["mcp:web4://tool/*"],
                ),
                nonce="n1",
            ),
            timestamp="2025-01-01T00:00:00Z",
        )
        doc = action.to_jsonld()
        self.jsonschema.validate(doc, self.schema)

    def test_failure_action_validates(self):
        """Failed action with error passes schema validation."""
        action = build_action(
            actor="lct:bob",
            role_lct="lct:role:eng",
            action="deploy",
        )
        action.result = Result(
            status=ActionStatus.FAILURE,
            error="timeout",
            atp_consumed=10.0,
        )
        doc = action.to_jsonld()
        self.jsonschema.validate(doc, self.schema)
