"""
Tests for web4.r6 — R6 Action Framework

Tests the full lifecycle: create → begin → complete/fail,
confidence calculation, T3/V3 evolution, ATP integration,
and serialization.
"""

import pytest

from web4.r6 import (
    ActionStatus,
    ActionType,
    ConfidenceAssessment,
    Priority,
    R6Action,
    Reference,
    Request,
    Resource,
    Result,
    Role,
    Rules,
    WitnessAttestation,
    assess_confidence,
    evolve_t3,
    evolve_v3,
)
from web4.trust import T3, V3
from web4.atp import ATPAccount


# ── Component Construction ───────────────────────────────────────

class TestRules:
    def test_permits(self):
        rules = Rules(permission_scope=["read:data", "write:results"])
        assert rules.permits("read:data")
        assert not rules.permits("admin:delete")

    def test_defaults(self):
        rules = Rules()
        assert rules.max_atp_spend == 0.0
        assert rules.timeout_seconds == 3600
        assert rules.quality_threshold == 0.0


class TestRole:
    def test_has_permission(self):
        role = Role("lct:role:1", "analyst", ["analyze", "report"])
        assert role.has_permission("analyze")
        assert not role.has_permission("delete")

    def test_t3_snapshot(self):
        t3 = T3(0.8, 0.9, 0.7)
        role = Role("lct:role:1", "analyst", t3_snapshot=t3)
        assert role.t3_snapshot.talent == 0.8


class TestRequest:
    def test_construction(self):
        req = Request(ActionType.ANALYZE, "Analyze dataset")
        assert req.action_type == ActionType.ANALYZE
        assert req.priority == Priority.MEDIUM

    def test_with_criteria(self):
        req = Request(
            ActionType.VERIFY, "Verify attestation",
            acceptance_criteria=["signature valid", "timestamp fresh"],
            priority=Priority.HIGH,
        )
        assert len(req.acceptance_criteria) == 2
        assert req.priority == Priority.HIGH


# ── Confidence Assessment ────────────────────────────────────────

class TestConfidence:
    def test_default_confidence(self):
        ca = ConfidenceAssessment()
        # Default: 0.5*0.3 + 0.5*0.25 + 1.0*0.25 + 0.5*0.2 = 0.15+0.125+0.25+0.1 = 0.625
        assert abs(ca.overall - 0.625) < 0.001

    def test_high_confidence(self):
        ca = ConfidenceAssessment(
            role_capability=0.9,
            historical_success=0.85,
            resource_availability=1.0,
            risk_assessment=0.95,
        )
        # 0.9*0.3 + 0.85*0.25 + 1.0*0.25 + 0.95*0.2 = 0.27+0.2125+0.25+0.19 = 0.9225
        assert ca.overall > 0.9

    def test_assess_from_components(self):
        role = Role("lct:role:1", "analyst", t3_snapshot=T3(0.8, 0.9, 0.7))
        ref = Reference(average_confidence=0.75)
        res = Resource(atp_allocated=50, estimated_atp=50)
        rules = Rules(quality_threshold=0.8)

        ca = assess_confidence(role, ref, res, rules)
        # role_capability = T3(0.8, 0.9, 0.7).composite = 0.8*0.4 + 0.9*0.3 + 0.7*0.3 = 0.80
        assert abs(ca.role_capability - 0.80) < 0.01
        assert ca.historical_success == 0.75
        assert ca.resource_availability == 1.0
        assert ca.overall > 0.5

    def test_assess_insufficient_resources(self):
        role = Role("lct:role:1", "analyst")
        ref = Reference()
        res = Resource(atp_allocated=25, estimated_atp=50)
        rules = Rules()

        ca = assess_confidence(role, ref, res, rules)
        assert ca.resource_availability == 0.5  # 25/50


# ── Action Lifecycle ─────────────────────────────────────────────

class TestActionLifecycle:
    def _make_action(self, max_atp=50.0, t3=None):
        return R6Action.create(
            initiator_lct_id="lct:web4:agent:alice",
            rules=Rules(
                permission_scope=["read:data", "analyze"],
                max_atp_spend=max_atp,
                quality_threshold=0.7,
            ),
            role=Role(
                "lct:web4:role:analyst", "data-analyst",
                ["analyze", "report"],
                t3_snapshot=t3 or T3(0.8, 0.9, 0.7),
            ),
            request=Request(ActionType.ANALYZE, "Analyze trust data"),
        )

    def test_create_pending(self):
        action = self._make_action()
        assert action.status == ActionStatus.PENDING
        assert action.action_id.startswith("r6:web4:")
        assert action.confidence is not None
        assert action.confidence.overall > 0.5

    def test_begin_transitions_to_executing(self):
        action = self._make_action()
        assert action.begin()
        assert action.status == ActionStatus.EXECUTING

    def test_begin_locks_atp(self):
        action = self._make_action(max_atp=50)
        account = ATPAccount(available=100)
        assert action.begin(account)
        assert account.available == 50.0
        assert account.locked == 50.0

    def test_begin_fails_insufficient_atp(self):
        action = self._make_action(max_atp=200)
        account = ATPAccount(available=100)
        assert not action.begin(account)
        assert action.status == ActionStatus.PENDING
        assert account.available == 100.0  # Unchanged

    def test_begin_rejects_non_pending(self):
        action = self._make_action()
        action.begin()
        assert not action.begin()  # Already executing

    def test_complete_success(self):
        action = self._make_action(max_atp=50)
        account = ATPAccount(available=100)
        action.begin(account)

        result = Result(
            output="Analysis complete",
            quality_score=0.9,
            criteria_met=["accuracy", "completeness"],
        )
        assert action.complete(result, account)
        assert action.status == ActionStatus.COMPLETED
        assert action.result is result

    def test_complete_atp_settlement(self):
        action = self._make_action(max_atp=50)
        account = ATPAccount(available=100)
        action.begin(account)  # locks 50

        result = Result(quality_score=0.9)
        action.complete(result, account)

        # Quality 0.9 → consumed = 50 * 0.9 = 45, rollback = 5
        assert abs(account.adp - 45.0) < 0.01
        assert abs(account.available - 55.0) < 0.01  # 50 + 5 rollback
        assert account.locked == 0.0

    def test_complete_low_quality_less_atp(self):
        action = self._make_action(max_atp=50)
        account = ATPAccount(available=100)
        action.begin(account)

        result = Result(quality_score=0.3)
        action.complete(result, account)

        # Quality 0.3 → consumed = 50 * 0.3 = 15, rollback = 35
        assert abs(account.adp - 15.0) < 0.01
        assert abs(account.available - 85.0) < 0.01

    def test_fail_rolls_back_atp(self):
        action = self._make_action(max_atp=50)
        account = ATPAccount(available=100)
        action.begin(account)

        assert action.fail("Resource unavailable", account)
        assert action.status == ActionStatus.FAILED
        assert account.available == 100.0  # Fully rolled back
        assert account.locked == 0.0
        assert account.adp == 0.0

    def test_complete_rejects_non_executing(self):
        action = self._make_action()
        result = Result(quality_score=0.9)
        assert not action.complete(result)

    def test_fail_rejects_non_executing(self):
        action = self._make_action()
        assert not action.fail("error")


# ── T3/V3 Evolution ──────────────────────────────────────────────

class TestTensorEvolution:
    def test_evolve_t3_high_quality(self):
        t3 = T3(0.5, 0.5, 0.5)
        result = Result(quality_score=0.9)
        new_t3 = evolve_t3(t3, result, success=True)
        # quality 0.9 → base_delta = 0.02 * (0.9 - 0.5) = 0.008
        assert new_t3.talent > t3.talent
        assert new_t3.training > t3.training
        assert new_t3.temperament > t3.temperament

    def test_evolve_t3_low_quality(self):
        t3 = T3(0.5, 0.5, 0.5)
        result = Result(quality_score=0.1)
        new_t3 = evolve_t3(t3, result, success=True)
        # quality 0.1 → base_delta = 0.02 * (0.1 - 0.5) = -0.008
        assert new_t3.talent < t3.talent

    def test_evolve_v3_explicit(self):
        v3_input = V3(0.85, 0.9, 1.0)
        result = Result(quality_score=0.9, v3_assessment=v3_input)
        v3_out = evolve_v3(result)
        assert v3_out is v3_input  # Uses explicit assessment

    def test_evolve_v3_derived(self):
        result = Result(quality_score=0.8)
        v3 = evolve_v3(result)
        assert v3.valuation == 0.8  # From quality
        assert v3.validity == 0.8   # No attestations, quality >= 0.5 → 0.8

    def test_evolve_v3_with_attestations(self):
        result = Result(
            quality_score=0.8,
            witness_attestations=[
                WitnessAttestation("lct:w1", "quality"),
                WitnessAttestation("lct:w2", "accuracy"),
            ],
        )
        v3 = evolve_v3(result)
        assert v3.valuation == 0.8
        # 2 attestations: veracity = min(1.0, 0.5 + 2*0.15) = 0.8
        assert abs(v3.veracity - 0.8) < 0.01
        assert v3.validity == 1.0  # Has attestations

    def test_action_evolve_tensors(self):
        action = R6Action.create(
            initiator_lct_id="lct:alice",
            rules=Rules(max_atp_spend=10),
            role=Role("lct:role:1", "analyst", t3_snapshot=T3(0.7, 0.8, 0.6)),
            request=Request(ActionType.ANALYZE, "Test"),
        )
        action.begin()
        action.complete(Result(quality_score=0.85))
        new_t3, new_v3 = action.evolve_tensors()
        assert new_t3 is not None
        assert new_v3 is not None
        assert new_t3.talent > 0.7  # Improved

    def test_evolve_tensors_not_completed(self):
        action = R6Action.create(
            initiator_lct_id="lct:alice",
            rules=Rules(),
            role=Role("lct:role:1", "analyst"),
            request=Request(ActionType.ANALYZE, "Test"),
        )
        t3, v3 = action.evolve_tensors()
        assert t3 is None and v3 is None


# ── Permission Checks ────────────────────────────────────────────

class TestPermissions:
    def test_check_permission_both(self):
        action = R6Action.create(
            initiator_lct_id="lct:alice",
            rules=Rules(permission_scope=["analyze", "report"]),
            role=Role("lct:role:1", "analyst", ["analyze", "report"]),
            request=Request(ActionType.ANALYZE, "Test"),
        )
        assert action.check_permission("analyze")
        assert action.check_permission("report")

    def test_check_permission_rules_only(self):
        action = R6Action.create(
            initiator_lct_id="lct:alice",
            rules=Rules(permission_scope=["analyze", "admin"]),
            role=Role("lct:role:1", "analyst", ["analyze"]),  # No admin
            request=Request(ActionType.ANALYZE, "Test"),
        )
        assert not action.check_permission("admin")


# ── Quality Threshold ────────────────────────────────────────────

class TestQualityThreshold:
    def test_meets_threshold(self):
        action = R6Action.create(
            initiator_lct_id="lct:alice",
            rules=Rules(quality_threshold=0.7),
            role=Role("lct:role:1", "analyst"),
            request=Request(ActionType.ANALYZE, "Test"),
        )
        action.begin()
        action.complete(Result(quality_score=0.9))
        assert action.meets_quality_threshold()

    def test_below_threshold(self):
        action = R6Action.create(
            initiator_lct_id="lct:alice",
            rules=Rules(quality_threshold=0.7),
            role=Role("lct:role:1", "analyst"),
            request=Request(ActionType.ANALYZE, "Test"),
        )
        action.begin()
        action.complete(Result(quality_score=0.5))
        assert not action.meets_quality_threshold()


# ── Reference Conversion ────────────────────────────────────────

class TestToReference:
    def test_completed_action_to_reference(self):
        action = R6Action.create(
            initiator_lct_id="lct:alice",
            rules=Rules(),
            role=Role("lct:role:1", "analyst"),
            request=Request(ActionType.ANALYZE, "Test"),
        )
        action.begin()
        action.complete(Result(quality_score=0.8))
        ref = action.to_reference()
        assert action.action_id in ref.similar_actions
        assert ref.average_confidence > 0


# ── Serialization ────────────────────────────────────────────────

class TestSerialization:
    def test_as_dict_pending(self):
        action = R6Action.create(
            initiator_lct_id="lct:alice",
            rules=Rules(permission_scope=["read"], max_atp_spend=50),
            role=Role("lct:role:1", "analyst", ["read"], T3(0.8, 0.9, 0.7)),
            request=Request(ActionType.ANALYZE, "Analyze data", priority=Priority.HIGH),
        )
        d = action.as_dict()
        r6 = d["r6_action"]
        assert r6["status"] == "pending"
        assert r6["rules"]["constraints"]["max_atp_spend"] == 50
        assert r6["role"]["t3_snapshot"]["talent"] == 0.8
        assert r6["request"]["action_type"] == "analyze"
        assert r6["request"]["priority"] == "high"
        assert "confidence" in r6
        assert "result" not in r6

    def test_as_dict_completed(self):
        action = R6Action.create(
            initiator_lct_id="lct:alice",
            rules=Rules(),
            role=Role("lct:role:1", "analyst"),
            request=Request(ActionType.VERIFY, "Verify"),
        )
        action.begin()
        action.complete(Result(
            output="Verified",
            quality_score=0.95,
            v3_assessment=V3(0.9, 0.95, 1.0),
        ))
        d = action.as_dict()
        r6 = d["r6_action"]
        assert r6["status"] == "completed"
        assert r6["result"]["quality_score"] == 0.95
        assert r6["result"]["v3_assessment"]["veracity"] == 0.95


# ── No-ATP Lifecycle ─────────────────────────────────────────────

class TestNoATPLifecycle:
    def test_zero_atp_action(self):
        """Actions with no ATP still go through lifecycle."""
        action = R6Action.create(
            initiator_lct_id="lct:alice",
            rules=Rules(),
            role=Role("lct:role:1", "observer"),
            request=Request(ActionType.VERIFY, "Observe"),
        )
        assert action.begin()
        assert action.complete(Result(quality_score=1.0))
        assert action.status == ActionStatus.COMPLETED
