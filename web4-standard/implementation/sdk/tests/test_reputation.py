"""
Tests for web4.reputation — rule-based reputation computation, aggregation, decay.

Tests cover:
1. ReputationRule matching
2. ReputationEngine multi-rule evaluation with modifiers
3. Factor analysis
4. ReputationStore time-weighted aggregation
5. Inactivity decay
6. Test vector validation
"""

import json
import math
import os
from datetime import datetime, timezone, timedelta

import pytest

from web4.trust import T3, V3
from web4.r6 import (
    R7Action, Role, Request, Rules, Result, ResourceRequirements,
    ActionStatus, ReputationDelta, ContributingFactor, TensorDelta,
)
from web4.reputation import (
    ReputationRule, DimensionImpact, Modifier,
    ReputationEngine, ReputationStore,
    analyze_factors,
)


# ── Fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def alice_analyst_action():
    """A successful analysis action by Alice in her analyst role."""
    return R7Action(
        rules=Rules(permissions=["analyze_dataset"]),
        role=Role(
            actor="lct:web4:entity:alice",
            role_lct="lct:web4:role:analyst:abc123",
            t3_in_role=T3(0.85, 0.90, 0.88),
            v3_in_role=V3(0.5, 0.80, 1.0),
        ),
        request=Request(
            action="analyze_dataset",
            target="resource:web4:dataset:quarterly",
            atp_stake=100,
        ),
        resource=ResourceRequirements(required_atp=100, available_atp=500),
        result=Result(
            status=ActionStatus.SUCCESS,
            output={"quality": 0.97, "accuracy": 0.97},
            atp_consumed=90,
        ),
    )


@pytest.fixture
def success_rule():
    """A rule for successful analysis completion."""
    return ReputationRule(
        rule_id="successful_analysis_completion",
        trigger_conditions={
            "action_type": "analyze_dataset",
            "result_status": "success",
            "quality_threshold": 0.95,
        },
        t3_impacts={
            "training": DimensionImpact(
                base_delta=0.01,
                modifiers=[
                    Modifier(condition="deadline_met", multiplier=1.5),
                    Modifier(condition="high_accuracy", multiplier=1.2),
                ],
            ),
            "temperament": DimensionImpact(
                base_delta=0.005,
                modifiers=[
                    Modifier(condition="early_completion", multiplier=1.3),
                ],
            ),
        },
        v3_impacts={
            "veracity": DimensionImpact(
                base_delta=0.02,
                modifiers=[
                    Modifier(condition="high_accuracy", multiplier=1.1),
                ],
            ),
        },
        witnesses_required=2,
        law_oracle="lct:web4:oracle:data_science_society",
    )


@pytest.fixture
def failure_rule():
    """A rule for failed actions."""
    return ReputationRule(
        rule_id="analysis_failure",
        trigger_conditions={
            "action_type": "analyze_dataset",
            "result_status": "failure",
        },
        t3_impacts={
            "training": DimensionImpact(base_delta=-0.005),
            "temperament": DimensionImpact(base_delta=-0.01),
        },
        v3_impacts={
            "validity": DimensionImpact(base_delta=-0.01),
        },
    )


# ── Rule Matching ────────────────────────────────────────────────

class TestReputationRuleMatching:

    def test_rule_matches_action_type(self, success_rule, alice_analyst_action):
        assert success_rule.matches(alice_analyst_action)

    def test_rule_rejects_wrong_action_type(self, success_rule):
        action = R7Action(
            role=Role(actor="lct:alice", role_lct="lct:role"),
            request=Request(action="train_model"),
            result=Result(status=ActionStatus.SUCCESS, output={"quality": 0.99}),
        )
        assert not success_rule.matches(action)

    def test_rule_rejects_wrong_status(self, success_rule):
        action = R7Action(
            role=Role(actor="lct:alice", role_lct="lct:role"),
            request=Request(action="analyze_dataset"),
            result=Result(status=ActionStatus.FAILURE),
        )
        assert not success_rule.matches(action)

    def test_rule_rejects_below_quality_threshold(self, success_rule):
        action = R7Action(
            role=Role(actor="lct:alice", role_lct="lct:role"),
            request=Request(action="analyze_dataset"),
            result=Result(
                status=ActionStatus.SUCCESS,
                output={"quality": 0.80},
            ),
        )
        assert not success_rule.matches(action)

    def test_rule_matches_without_optional_conditions(self):
        rule = ReputationRule(
            rule_id="any_success",
            trigger_conditions={"result_status": "success"},
        )
        action = R7Action(
            role=Role(actor="lct:alice", role_lct="lct:role"),
            request=Request(action="anything"),
            result=Result(status=ActionStatus.SUCCESS),
        )
        assert rule.matches(action)

    def test_rule_min_atp_stake(self):
        rule = ReputationRule(
            rule_id="high_stake",
            trigger_conditions={"min_atp_stake": 50},
        )
        action_low = R7Action(
            role=Role(actor="lct:a", role_lct="lct:r"),
            request=Request(action="x", atp_stake=10),
        )
        action_high = R7Action(
            role=Role(actor="lct:a", role_lct="lct:r"),
            request=Request(action="x", atp_stake=100),
        )
        assert not rule.matches(action_low)
        assert rule.matches(action_high)

    def test_rule_to_dict(self, success_rule):
        d = success_rule.to_dict()
        assert d["rule_id"] == "successful_analysis_completion"
        assert "training" in d["t3_impacts"]
        assert d["t3_impacts"]["training"]["base_delta"] == 0.01


# ── Factor Analysis ──────────────────────────────────────────────

class TestFactorAnalysis:

    def test_high_accuracy_factor(self, alice_analyst_action):
        factors = analyze_factors(alice_analyst_action)
        names = {f.factor for f in factors}
        assert "high_accuracy" in names

    def test_resource_efficiency_factor(self, alice_analyst_action):
        factors = analyze_factors(alice_analyst_action)
        names = {f.factor for f in factors}
        assert "resource_efficiency" in names

    def test_deadline_met_factor(self):
        action = R7Action(
            role=Role(actor="lct:a", role_lct="lct:r"),
            request=Request(
                action="x",
                constraints={"deadline_met": True},
            ),
            result=Result(status=ActionStatus.SUCCESS),
        )
        factors = analyze_factors(action)
        names = {f.factor for f in factors}
        assert "deadline_met" in names

    def test_no_factors_for_low_quality(self):
        action = R7Action(
            role=Role(actor="lct:a", role_lct="lct:r"),
            request=Request(action="x"),
            result=Result(
                status=ActionStatus.SUCCESS,
                output={"quality": 0.3},
            ),
        )
        factors = analyze_factors(action)
        names = {f.factor for f in factors}
        assert "high_accuracy" not in names


# ── Reputation Engine ────────────────────────────────────────────

class TestReputationEngine:

    def test_no_rules_returns_none(self, alice_analyst_action):
        engine = ReputationEngine()
        assert engine.evaluate(alice_analyst_action) is None

    def test_no_matching_rules_returns_none(self, failure_rule, alice_analyst_action):
        engine = ReputationEngine()
        engine.add_rule(failure_rule)
        # alice_analyst_action has SUCCESS, failure_rule wants FAILURE
        assert engine.evaluate(alice_analyst_action) is None

    def test_basic_rule_evaluation(self, success_rule, alice_analyst_action):
        engine = ReputationEngine()
        engine.add_rule(success_rule)
        delta = engine.evaluate(alice_analyst_action)
        assert delta is not None
        assert delta.subject_lct == "lct:web4:entity:alice"
        assert delta.role_lct == "lct:web4:role:analyst:abc123"
        assert delta.net_trust_change > 0
        assert delta.net_value_change > 0

    def test_modifier_applied(self, success_rule, alice_analyst_action):
        engine = ReputationEngine()
        engine.add_rule(success_rule)
        # alice has quality=0.97, so high_accuracy factor is present
        # training base=0.01, high_accuracy multiplier=1.2 → 0.012
        delta = engine.evaluate(alice_analyst_action)
        training_change = delta.t3_delta["training"].change
        # Without modifier: 0.01, with high_accuracy: 0.012
        assert training_change == pytest.approx(0.012, abs=0.001)

    def test_multiple_modifiers_multiply(self, success_rule):
        """When deadline_met AND high_accuracy both apply, modifiers multiply."""
        engine = ReputationEngine()
        engine.add_rule(success_rule)

        action = R7Action(
            role=Role(
                actor="lct:bob", role_lct="lct:role:analyst",
                t3_in_role=T3(0.5, 0.5, 0.5),
            ),
            request=Request(
                action="analyze_dataset",
                constraints={"deadline_met": True},
            ),
            result=Result(
                status=ActionStatus.SUCCESS,
                output={"quality": 0.97},
            ),
        )
        delta = engine.evaluate(action)
        # training: base 0.01, high_accuracy 1.2, deadline_met 1.5 → 0.018
        assert delta.t3_delta["training"].change == pytest.approx(0.018, abs=0.001)

    def test_failure_rule_produces_negative_deltas(self, failure_rule):
        engine = ReputationEngine()
        engine.add_rule(failure_rule)

        action = R7Action(
            role=Role(
                actor="lct:carol", role_lct="lct:role:analyst",
                t3_in_role=T3(0.7, 0.7, 0.7),
                v3_in_role=V3(0.5, 0.7, 0.7),
            ),
            request=Request(action="analyze_dataset"),
            result=Result(status=ActionStatus.FAILURE, error="bad params"),
        )
        delta = engine.evaluate(action)
        assert delta is not None
        assert delta.net_trust_change < 0
        assert delta.t3_delta["training"].change < 0
        assert delta.t3_delta["temperament"].change < 0

    def test_multiple_rules_stack(self, success_rule):
        """Two rules matching the same action stack their deltas."""
        bonus_rule = ReputationRule(
            rule_id="bonus_for_high_quality",
            trigger_conditions={
                "action_type": "analyze_dataset",
                "result_status": "success",
            },
            t3_impacts={
                "talent": DimensionImpact(base_delta=0.02),
            },
        )
        engine = ReputationEngine()
        engine.add_rule(success_rule)
        engine.add_rule(bonus_rule)

        action = R7Action(
            role=Role(
                actor="lct:alice", role_lct="lct:role:analyst",
                t3_in_role=T3(0.85, 0.9, 0.88),
                v3_in_role=V3(0.5, 0.8, 1.0),
            ),
            request=Request(action="analyze_dataset"),
            result=Result(
                status=ActionStatus.SUCCESS,
                output={"quality": 0.97},
            ),
        )
        delta = engine.evaluate(action)
        assert "talent" in delta.t3_delta
        assert delta.t3_delta["talent"].change == pytest.approx(0.02, abs=0.001)
        assert "training" in delta.t3_delta  # from success_rule

    def test_delta_sets_action_reputation(self, success_rule, alice_analyst_action):
        engine = ReputationEngine()
        engine.add_rule(success_rule)
        delta = engine.evaluate(alice_analyst_action)
        assert alice_analyst_action.reputation is delta

    def test_clamping_at_boundaries(self):
        """Deltas are clamped so tensor values stay in [0, 1]."""
        rule = ReputationRule(
            rule_id="big_boost",
            trigger_conditions={"result_status": "success"},
            t3_impacts={
                "talent": DimensionImpact(base_delta=0.5),
            },
        )
        engine = ReputationEngine()
        engine.add_rule(rule)

        action = R7Action(
            role=Role(
                actor="lct:x", role_lct="lct:r",
                t3_in_role=T3(0.9, 0.5, 0.5),
            ),
            request=Request(action="x"),
            result=Result(status=ActionStatus.SUCCESS),
        )
        delta = engine.evaluate(action)
        # from 0.9, adding 0.5 should clamp to 1.0 → change = 0.1
        assert delta.t3_delta["talent"].to_value == 1.0
        assert delta.t3_delta["talent"].change == pytest.approx(0.1, abs=0.001)

    def test_engine_rules_property(self, success_rule, failure_rule):
        engine = ReputationEngine()
        engine.add_rule(success_rule)
        engine.add_rule(failure_rule)
        assert len(engine.rules) == 2

    def test_custom_factors_override(self, success_rule, alice_analyst_action):
        """Caller can pass custom factors to override auto-analysis."""
        engine = ReputationEngine()
        engine.add_rule(success_rule)
        custom = [ContributingFactor(factor="deadline_met", weight=1.0)]
        delta = engine.evaluate(alice_analyst_action, factors=custom)
        # training: base 0.01, deadline_met 1.5 → 0.015 (no high_accuracy)
        assert delta.t3_delta["training"].change == pytest.approx(0.015, abs=0.001)


# ── Reputation Store ─────────────────────────────────────────────

class TestReputationStore:

    def test_neutral_for_unknown(self):
        store = ReputationStore()
        score = store.current("lct:unknown", "lct:role", "training")
        assert score == 0.5

    def test_positive_deltas_increase_reputation(self):
        store = ReputationStore()
        now = datetime(2026, 3, 15, tzinfo=timezone.utc)
        delta = ReputationDelta(
            subject_lct="lct:alice",
            role_lct="lct:role:analyst",
            t3_delta={
                "training": TensorDelta(change=0.05, from_value=0.5, to_value=0.55),
            },
            timestamp=now.isoformat(),
        )
        store.record(delta, now=now)
        score = store.current("lct:alice", "lct:role:analyst", "training", now=now)
        assert score > 0.5

    def test_negative_deltas_decrease_reputation(self):
        store = ReputationStore()
        now = datetime(2026, 3, 15, tzinfo=timezone.utc)
        delta = ReputationDelta(
            subject_lct="lct:bob",
            role_lct="lct:role:dev",
            t3_delta={
                "temperament": TensorDelta(change=-0.1, from_value=0.7, to_value=0.6),
            },
            timestamp=now.isoformat(),
        )
        store.record(delta, now=now)
        score = store.current("lct:bob", "lct:role:dev", "temperament", now=now)
        assert score < 0.5

    def test_recent_deltas_weighted_more(self):
        store = ReputationStore()
        now = datetime(2026, 3, 15, tzinfo=timezone.utc)
        old = now - timedelta(days=60)

        # Old negative delta
        store.record(ReputationDelta(
            subject_lct="lct:alice", role_lct="lct:role",
            t3_delta={"training": TensorDelta(change=-0.1, from_value=0.5, to_value=0.4)},
            timestamp=old.isoformat(),
        ), now=old)

        # Recent positive delta
        store.record(ReputationDelta(
            subject_lct="lct:alice", role_lct="lct:role",
            t3_delta={"training": TensorDelta(change=0.1, from_value=0.4, to_value=0.5)},
            timestamp=now.isoformat(),
        ), now=now)

        score = store.current("lct:alice", "lct:role", "training", now=now)
        # Recent positive should outweigh old negative
        assert score > 0.5

    def test_horizon_excludes_old_deltas(self):
        store = ReputationStore()
        now = datetime(2026, 3, 15, tzinfo=timezone.utc)
        very_old = now - timedelta(days=200)

        store.record(ReputationDelta(
            subject_lct="lct:alice", role_lct="lct:role",
            t3_delta={"talent": TensorDelta(change=0.5, from_value=0.5, to_value=1.0)},
            timestamp=very_old.isoformat(),
        ), now=very_old)

        score = store.current("lct:alice", "lct:role", "talent", now=now)
        # Beyond 90-day horizon, should return neutral
        assert score == 0.5

    def test_role_contextualized(self):
        """Same entity, different roles, different reputations."""
        store = ReputationStore()
        now = datetime(2026, 3, 15, tzinfo=timezone.utc)

        store.record(ReputationDelta(
            subject_lct="lct:alice", role_lct="lct:role:analyst",
            t3_delta={"training": TensorDelta(change=0.2, from_value=0.5, to_value=0.7)},
            timestamp=now.isoformat(),
        ), now=now)

        store.record(ReputationDelta(
            subject_lct="lct:alice", role_lct="lct:role:surgeon",
            t3_delta={"training": TensorDelta(change=-0.2, from_value=0.5, to_value=0.3)},
            timestamp=now.isoformat(),
        ), now=now)

        analyst = store.current("lct:alice", "lct:role:analyst", "training", now=now)
        surgeon = store.current("lct:alice", "lct:role:surgeon", "training", now=now)
        assert analyst > 0.5
        assert surgeon < 0.5

    def test_has_history(self):
        store = ReputationStore()
        now = datetime(2026, 3, 15, tzinfo=timezone.utc)
        assert not store.has_history("lct:alice", "lct:role")
        store.record(ReputationDelta(
            subject_lct="lct:alice", role_lct="lct:role",
            t3_delta={"talent": TensorDelta(change=0.01, from_value=0.5, to_value=0.51)},
            timestamp=now.isoformat(),
        ), now=now)
        assert store.has_history("lct:alice", "lct:role")


# ── Inactivity Decay ─────────────────────────────────────────────

class TestInactivityDecay:

    def test_no_decay_within_grace_period(self):
        store = ReputationStore()
        now = datetime(2026, 3, 15, tzinfo=timezone.utc)
        store.record(ReputationDelta(
            subject_lct="lct:alice", role_lct="lct:role",
            t3_delta={"talent": TensorDelta(change=0.01, from_value=0.5, to_value=0.51)},
            timestamp=now.isoformat(),
        ), now=now)

        check = now + timedelta(days=15)
        decay = store.inactivity_decay("lct:alice", "lct:role", now=check)
        assert decay == 0.0

    def test_decay_after_grace_period(self):
        store = ReputationStore()
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        store.record(ReputationDelta(
            subject_lct="lct:alice", role_lct="lct:role",
            t3_delta={"talent": TensorDelta(change=0.01, from_value=0.5, to_value=0.51)},
            timestamp=now.isoformat(),
        ), now=now)

        # 60 days later = 2 months inactive
        check = now + timedelta(days=60)
        decay = store.inactivity_decay("lct:alice", "lct:role", now=check)
        assert decay < 0
        assert decay == pytest.approx(-0.02, abs=0.005)

    def test_decay_accelerates_after_6_months(self):
        store = ReputationStore()
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        store.record(ReputationDelta(
            subject_lct="lct:alice", role_lct="lct:role",
            t3_delta={"talent": TensorDelta(change=0.01, from_value=0.5, to_value=0.51)},
            timestamp=now.isoformat(),
        ), now=now)

        # 240 days = 8 months (past 6-month threshold)
        check = now + timedelta(days=240)
        decay = store.inactivity_decay("lct:alice", "lct:role", now=check)
        # 8 months * 0.01 * 1.5 = -0.12
        assert decay == pytest.approx(-0.12, abs=0.01)

    def test_decay_capped(self):
        store = ReputationStore()
        now = datetime(2020, 1, 1, tzinfo=timezone.utc)
        store.record(ReputationDelta(
            subject_lct="lct:alice", role_lct="lct:role",
            t3_delta={"talent": TensorDelta(change=0.01, from_value=0.5, to_value=0.51)},
            timestamp=now.isoformat(),
        ), now=now)

        # 5 years later
        check = now + timedelta(days=365 * 5)
        decay = store.inactivity_decay("lct:alice", "lct:role", now=check)
        assert decay >= -0.5

    def test_no_history_no_decay(self):
        store = ReputationStore()
        decay = store.inactivity_decay("lct:unknown", "lct:role")
        assert decay == 0.0


# ── Effective Reputation ─────────────────────────────────────────

class TestEffectiveReputation:

    def test_effective_includes_decay(self):
        store = ReputationStore()
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        store.record(ReputationDelta(
            subject_lct="lct:alice", role_lct="lct:role",
            t3_delta={"training": TensorDelta(change=0.1, from_value=0.5, to_value=0.6)},
            timestamp=now.isoformat(),
        ), now=now)

        # 90 days later — within horizon, but past grace period
        check = now + timedelta(days=60)
        base = store.current("lct:alice", "lct:role", "training", now=check)
        effective = store.effective_reputation("lct:alice", "lct:role", "training", now=check)
        assert effective < base

    def test_effective_clamped_to_zero(self):
        store = ReputationStore()
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        store.record(ReputationDelta(
            subject_lct="lct:alice", role_lct="lct:role",
            t3_delta={"training": TensorDelta(change=-0.4, from_value=0.5, to_value=0.1)},
            timestamp=now.isoformat(),
        ), now=now)

        # Long inactivity + negative base → should clamp to 0
        check = now + timedelta(days=300)
        effective = store.effective_reputation("lct:alice", "lct:role", "training", now=check)
        assert effective >= 0.0


# ── Test Vector Validation ───────────────────────────────────────

class TestVectors:

    @pytest.fixture
    def vectors(self):
        path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..", "test-vectors", "reputation", "reputation-operations.json",
        )
        with open(path) as f:
            return json.load(f)["vectors"]

    def test_rep001_rule_triggered_positive(self, vectors):
        """rep-001: Positive reputation from successful action with modifiers."""
        v = next(x for x in vectors if x["id"] == "rep-001")

        rule = ReputationRule(
            rule_id=v["input"]["rule"]["rule_id"],
            trigger_conditions=v["input"]["rule"]["trigger_conditions"],
            t3_impacts={
                k: DimensionImpact(
                    base_delta=imp["base_delta"],
                    modifiers=[Modifier(**m) for m in imp.get("modifiers", [])],
                )
                for k, imp in v["input"]["rule"].get("t3_impacts", {}).items()
            },
            v3_impacts={
                k: DimensionImpact(
                    base_delta=imp["base_delta"],
                    modifiers=[Modifier(**m) for m in imp.get("modifiers", [])],
                )
                for k, imp in v["input"]["rule"].get("v3_impacts", {}).items()
            },
        )

        action = R7Action(
            role=Role(
                actor=v["input"]["actor"],
                role_lct=v["input"]["role_lct"],
                t3_in_role=T3(**v["input"]["t3"]),
                v3_in_role=V3(**v["input"]["v3"]),
            ),
            request=Request(action=v["input"]["action"]),
            result=Result(
                status=ActionStatus(v["input"]["result_status"]),
                output=v["input"]["result_output"],
            ),
        )

        engine = ReputationEngine()
        engine.add_rule(rule)
        factors = [ContributingFactor(**f) for f in v["input"]["factors"]]
        delta = engine.evaluate(action, factors=factors)

        tol = v.get("tolerance", 0.001)
        assert delta is not None
        for dim, expected in v["expected"]["t3_deltas"].items():
            assert delta.t3_delta[dim].change == pytest.approx(expected["change"], abs=tol)
        for dim, expected in v["expected"]["v3_deltas"].items():
            assert delta.v3_delta[dim].change == pytest.approx(expected["change"], abs=tol)

    def test_rep002_no_rules_no_change(self, vectors):
        """rep-002: No matching rules → no reputation change."""
        v = next(x for x in vectors if x["id"] == "rep-002")
        engine = ReputationEngine()
        action = R7Action(
            role=Role(actor=v["input"]["actor"], role_lct=v["input"]["role_lct"]),
            request=Request(action=v["input"]["action"]),
            result=Result(status=ActionStatus(v["input"]["result_status"])),
        )
        delta = engine.evaluate(action)
        assert delta is None

    def test_rep003_time_weighted_aggregation(self, vectors):
        """rep-003: Recent deltas weighted more heavily than old ones."""
        v = next(x for x in vectors if x["id"] == "rep-003")
        store = ReputationStore()
        now = datetime.fromisoformat(v["input"]["now"])

        for entry in v["input"]["deltas"]:
            store.record(ReputationDelta(
                subject_lct=v["input"]["entity"],
                role_lct=v["input"]["role"],
                t3_delta={
                    entry["dimension"]: TensorDelta(
                        change=entry["change"],
                        from_value=0.5,
                        to_value=0.5 + entry["change"],
                    ),
                },
                timestamp=entry["timestamp"],
            ), now=datetime.fromisoformat(entry["timestamp"]))

        score = store.current(
            v["input"]["entity"], v["input"]["role"],
            v["input"]["query_dimension"], now=now,
        )
        tol = v.get("tolerance", 0.01)
        assert score == pytest.approx(v["expected"]["score"], abs=tol)

    def test_rep004_inactivity_decay(self, vectors):
        """rep-004: Inactivity decay after grace period."""
        v = next(x for x in vectors if x["id"] == "rep-004")
        store = ReputationStore()
        action_time = datetime.fromisoformat(v["input"]["last_action_timestamp"])

        store.record(ReputationDelta(
            subject_lct=v["input"]["entity"],
            role_lct=v["input"]["role"],
            t3_delta={"talent": TensorDelta(change=0.01, from_value=0.5, to_value=0.51)},
            timestamp=action_time.isoformat(),
        ), now=action_time)

        check_time = datetime.fromisoformat(v["input"]["check_timestamp"])
        decay = store.inactivity_decay(
            v["input"]["entity"], v["input"]["role"], now=check_time,
        )
        tol = v.get("tolerance", 0.005)
        assert decay == pytest.approx(v["expected"]["decay"], abs=tol)

    def test_rep005_negative_rule(self, vectors):
        """rep-005: Failure rule produces negative deltas."""
        v = next(x for x in vectors if x["id"] == "rep-005")

        rule = ReputationRule(
            rule_id=v["input"]["rule"]["rule_id"],
            trigger_conditions=v["input"]["rule"]["trigger_conditions"],
            t3_impacts={
                k: DimensionImpact(base_delta=imp["base_delta"])
                for k, imp in v["input"]["rule"].get("t3_impacts", {}).items()
            },
            v3_impacts={
                k: DimensionImpact(base_delta=imp["base_delta"])
                for k, imp in v["input"]["rule"].get("v3_impacts", {}).items()
            },
        )

        action = R7Action(
            role=Role(
                actor=v["input"]["actor"],
                role_lct=v["input"]["role_lct"],
                t3_in_role=T3(**v["input"]["t3"]),
                v3_in_role=V3(**v["input"]["v3"]),
            ),
            request=Request(action=v["input"]["action"]),
            result=Result(status=ActionStatus(v["input"]["result_status"])),
        )

        engine = ReputationEngine()
        engine.add_rule(rule)
        delta = engine.evaluate(action, factors=[])

        assert delta is not None
        tol = v.get("tolerance", 0.001)
        for dim, expected in v["expected"]["t3_deltas"].items():
            assert delta.t3_delta[dim].change == pytest.approx(expected["change"], abs=tol)
        for dim, expected in v["expected"]["v3_deltas"].items():
            assert delta.v3_delta[dim].change == pytest.approx(expected["change"], abs=tol)
