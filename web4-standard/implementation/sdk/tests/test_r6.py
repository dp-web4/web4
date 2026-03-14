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
