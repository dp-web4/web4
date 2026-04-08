"""Tests for process_action_outcome() — the action → consequence pipeline.

Tests the cross-module composition: R7Action + ReputationEngine + TrustProfile
+ ATPAccount → ActionOutcomeResult with updated trust and ATP settlement.
"""

from __future__ import annotations

import pytest

from web4.atp import ATPAccount
from web4.r6 import (
    ActionStatus,
    ContributingFactor,
    R7Action,
    Request,
    ResourceRequirements,
    Result,
    Role,
    Rules,
)
from web4.reputation import (
    ActionOutcomeResult,
    DimensionImpact,
    Modifier,
    ReputationEngine,
    ReputationRule,
    ReputationStore,
    process_action_outcome,
)
from web4.trust import T3, TrustProfile, V3


# ── Fixtures ───────────────────────────────────────────────────


def _make_action(
    *,
    status: ActionStatus = ActionStatus.SUCCESS,
    action_type: str = "data_analysis",
    quality: float = 0.8,
    atp_stake: float = 10.0,
    actor: str = "lct:alice",
    role_lct: str = "web4:DataAnalyst",
    t3: T3 | None = None,
    v3: V3 | None = None,
) -> R7Action:
    """Build a completed R7Action for testing."""
    return R7Action(
        rules=Rules(permissions=[action_type]),
        role=Role(
            actor=actor,
            role_lct=role_lct,
            t3_in_role=t3 or T3(0.7, 0.8, 0.9),
            v3_in_role=v3 or V3(0.6, 0.7, 0.8),
        ),
        request=Request(action=action_type, atp_stake=atp_stake),
        resource=ResourceRequirements(required_atp=atp_stake, available_atp=atp_stake),
        result=Result(
            status=status,
            output={"quality": quality},
        ),
    )


def _make_engine() -> ReputationEngine:
    """Build an engine with a standard rule for data_analysis actions."""
    engine = ReputationEngine()
    engine.add_rule(ReputationRule(
        rule_id="R001",
        trigger_conditions={"action_type": "data_analysis", "result_status": "success"},
        t3_impacts={
            "talent": DimensionImpact(base_delta=0.05),
            "training": DimensionImpact(
                base_delta=0.03,
                modifiers=[Modifier(condition="high_accuracy", multiplier=1.5)],
            ),
        },
        v3_impacts={
            "veracity": DimensionImpact(base_delta=0.02),
        },
    ))
    return engine


# ── Success path ───────────────────────────────────────────────


class TestSuccessPath:
    """Tests for successful action outcomes."""

    def test_basic_success_returns_result(self) -> None:
        action = _make_action()
        engine = _make_engine()
        profile = TrustProfile("lct:alice")
        profile.set_role("web4:DataAnalyst", T3(0.7, 0.8, 0.9), V3(0.6, 0.7, 0.8))
        account = ATPAccount(available=0.0, locked=10.0)

        result = process_action_outcome(action, engine, profile, account)

        assert isinstance(result, ActionOutcomeResult)
        assert result.delta is not None
        assert result.atp_committed == 10.0
        assert result.atp_rolled_back == 0.0

    def test_t3_updated_in_profile(self) -> None:
        action = _make_action()
        engine = _make_engine()
        profile = TrustProfile("lct:alice")
        profile.set_role("web4:DataAnalyst", T3(0.7, 0.8, 0.9))
        account = ATPAccount(available=0.0, locked=10.0)

        result = process_action_outcome(action, engine, profile, account)

        # Talent should increase by 0.05
        assert result.updated_t3.talent == pytest.approx(0.75, abs=1e-6)
        # Profile should be mutated
        assert profile.get_t3("web4:DataAnalyst").talent == pytest.approx(0.75, abs=1e-6)

    def test_v3_updated_in_profile(self) -> None:
        action = _make_action()
        engine = _make_engine()
        profile = TrustProfile("lct:alice")
        # V3 field order: valuation, veracity, validity
        profile.set_role("web4:DataAnalyst", v3=V3(0.6, 0.7, 0.8))
        account = ATPAccount(available=0.0, locked=10.0)

        result = process_action_outcome(action, engine, profile, account)

        # Veracity (0.7) should increase by 0.02 → 0.72
        assert result.updated_v3.veracity == pytest.approx(0.72, abs=1e-6)
        assert profile.get_v3("web4:DataAnalyst").veracity == pytest.approx(0.72, abs=1e-6)

    def test_atp_committed_on_success(self) -> None:
        action = _make_action(atp_stake=15.0)
        engine = _make_engine()
        profile = TrustProfile("lct:alice")
        account = ATPAccount(available=0.0, locked=15.0)

        result = process_action_outcome(action, engine, profile, account)

        assert result.atp_committed == 15.0
        assert account.locked == 0.0
        assert account.adp == 15.0

    def test_modifier_applied_with_high_quality(self) -> None:
        action = _make_action(quality=0.9)  # triggers high_accuracy factor
        engine = _make_engine()
        profile = TrustProfile("lct:alice")
        profile.set_role("web4:DataAnalyst", T3(0.7, 0.8, 0.9))
        account = ATPAccount(available=0.0, locked=10.0)

        result = process_action_outcome(action, engine, profile, account)

        # Training base_delta=0.03 * 1.5 (high_accuracy modifier) = 0.045
        assert result.updated_t3.training == pytest.approx(0.845, abs=1e-6)


# ── Failure path ───────────────────────────────────────────────


class TestFailurePath:
    """Tests for failed action outcomes."""

    def test_atp_rolled_back_on_failure(self) -> None:
        action = _make_action(status=ActionStatus.FAILURE)
        engine = _make_engine()
        profile = TrustProfile("lct:alice")
        account = ATPAccount(available=0.0, locked=10.0)

        result = process_action_outcome(action, engine, profile, account)

        assert result.atp_committed == 0.0
        assert result.atp_rolled_back == 10.0
        assert account.locked == 0.0
        assert account.available == 10.0

    def test_no_delta_when_no_rules_match_failure(self) -> None:
        # Engine only has a rule for result_status=success
        action = _make_action(status=ActionStatus.FAILURE)
        engine = _make_engine()
        profile = TrustProfile("lct:alice")
        profile.set_role("web4:DataAnalyst", T3(0.7, 0.8, 0.9))
        account = ATPAccount(available=0.0, locked=10.0)

        result = process_action_outcome(action, engine, profile, account)

        assert result.delta is None
        # Trust unchanged
        assert result.updated_t3.talent == pytest.approx(0.7, abs=1e-6)

    def test_failure_with_matching_rule(self) -> None:
        action = _make_action(status=ActionStatus.FAILURE)
        engine = ReputationEngine()
        engine.add_rule(ReputationRule(
            rule_id="R002",
            trigger_conditions={"action_type": "data_analysis", "result_status": "failure"},
            t3_impacts={
                "temperament": DimensionImpact(base_delta=-0.05),
            },
        ))
        profile = TrustProfile("lct:alice")
        profile.set_role("web4:DataAnalyst", T3(0.7, 0.8, 0.9))
        account = ATPAccount(available=0.0, locked=10.0)

        result = process_action_outcome(action, engine, profile, account)

        assert result.delta is not None
        assert result.updated_t3.temperament == pytest.approx(0.85, abs=1e-6)
        assert result.atp_rolled_back == 10.0


# ── Edge cases ─────────────────────────────────────────────────


class TestEdgeCases:
    """Edge cases and validation."""

    def test_rejects_pending_action(self) -> None:
        action = _make_action()
        action.result.status = ActionStatus.PENDING
        engine = _make_engine()
        profile = TrustProfile("lct:alice")
        account = ATPAccount(available=100.0)

        with pytest.raises(ValueError, match="expected 'success' or 'failure'"):
            process_action_outcome(action, engine, profile, account)

    def test_rejects_in_progress_action(self) -> None:
        action = _make_action()
        action.result.status = ActionStatus.IN_PROGRESS
        engine = _make_engine()
        profile = TrustProfile("lct:alice")
        account = ATPAccount(available=100.0)

        with pytest.raises(ValueError, match="expected 'success' or 'failure'"):
            process_action_outcome(action, engine, profile, account)

    def test_zero_atp_stake(self) -> None:
        action = _make_action(atp_stake=0.0)
        engine = _make_engine()
        profile = TrustProfile("lct:alice")
        account = ATPAccount(available=100.0)

        result = process_action_outcome(action, engine, profile, account)

        assert result.atp_committed == 0.0
        assert result.atp_rolled_back == 0.0
        assert account.available == 100.0

    def test_no_matching_rules(self) -> None:
        action = _make_action(action_type="unknown_action")
        engine = _make_engine()
        profile = TrustProfile("lct:alice")
        profile.set_role("web4:DataAnalyst", T3(0.7, 0.8, 0.9), V3(0.6, 0.7, 0.8))
        account = ATPAccount(available=0.0, locked=10.0)

        result = process_action_outcome(action, engine, profile, account)

        assert result.delta is None
        assert result.updated_t3.talent == pytest.approx(0.7, abs=1e-6)
        # V3(0.6, 0.7, 0.8) → valuation=0.6, veracity=0.7, validity=0.8
        assert result.updated_v3.veracity == pytest.approx(0.7, abs=1e-6)
        # ATP still committed (success path)
        assert result.atp_committed == 10.0

    def test_profile_without_prior_role(self) -> None:
        """Profile has no entry for the role — should use defaults (0.5)."""
        action = _make_action()
        engine = _make_engine()
        profile = TrustProfile("lct:alice")
        # Don't set role — profile defaults to T3(0.5, 0.5, 0.5)
        # But engine computes delta based on action.role.t3_in_role = T3(0.7, 0.8, 0.9)
        # Delta to_value for talent = 0.7 + 0.05 = 0.75
        # process_action_outcome applies delta to_value directly to profile
        account = ATPAccount(available=0.0, locked=10.0)

        result = process_action_outcome(action, engine, profile, account)

        assert result.delta is not None
        # Delta to_value = 0.75 (computed from action's T3, not profile's)
        assert result.updated_t3.talent == pytest.approx(0.75, abs=1e-6)
        # Profile should now have the role set
        assert "web4:DataAnalyst" in profile.roles


# ── Store integration ──────────────────────────────────────────


class TestStoreIntegration:
    """Tests for optional ReputationStore recording."""

    def test_delta_recorded_in_store(self) -> None:
        action = _make_action()
        engine = _make_engine()
        profile = TrustProfile("lct:alice")
        account = ATPAccount(available=0.0, locked=10.0)
        store = ReputationStore()

        process_action_outcome(action, engine, profile, account, store=store)

        assert store.has_history("lct:alice", "web4:DataAnalyst")

    def test_no_store_recording_without_delta(self) -> None:
        action = _make_action(action_type="unknown_action")
        engine = _make_engine()
        profile = TrustProfile("lct:alice")
        account = ATPAccount(available=0.0, locked=10.0)
        store = ReputationStore()

        process_action_outcome(action, engine, profile, account, store=store)

        assert not store.has_history("lct:alice", "web4:DataAnalyst")

    def test_no_store_recording_when_store_not_provided(self) -> None:
        action = _make_action()
        engine = _make_engine()
        profile = TrustProfile("lct:alice")
        account = ATPAccount(available=0.0, locked=10.0)

        # Should not raise even without store
        result = process_action_outcome(action, engine, profile, account)
        assert result.delta is not None


# ── Import from web4 root ──────────────────────────────────────


class TestRootImport:
    """Verify exports are accessible from web4 root."""

    def test_process_action_outcome_importable(self) -> None:
        from web4 import process_action_outcome as pao
        assert callable(pao)

    def test_action_outcome_result_importable(self) -> None:
        from web4 import ActionOutcomeResult as AOR
        assert AOR is not None
