# SPDX-License-Identifier: MIT
# Pytest-compatible wrappers for Hardbound test suites
#
# Runs the existing sequential test suites (test_team.py, test_integration.py,
# attack_simulations.py) through pytest discovery.

import pytest
from hardbound.team import Team, TeamConfig


class TestTeamSuite:
    """Run the full team test suite as a single pytest test."""

    def test_full_team_suite(self):
        """Execute all team tests sequentially (they share state)."""
        from hardbound.test_team import main
        main()


class TestIntegrationSuite:
    """Run cross-layer integration tests."""

    def test_integration_suite(self):
        """Execute all integration tests."""
        from hardbound.test_integration import main
        main()


class TestAttackSimulations:
    """Run attack simulation suite."""

    def test_attack_simulations(self):
        """Execute all 6 attack vectors."""
        from hardbound.attack_simulations import run_all_attacks
        results = run_all_attacks()
        assert len(results) == 6


class TestStandaloneComponents:
    """Individual component tests that don't require shared state."""

    def test_team_creation(self):
        config = TeamConfig(name="pytest-team", description="Created by pytest")
        team = Team(config=config)
        assert team.team_id.startswith("web4:team:")
        assert team.config.name == "pytest-team"

    def test_member_management(self):
        config = TeamConfig(name="member-test", description="Member management")
        team = Team(config=config)
        team.set_admin("web4:soft:admin:pytest")
        team.add_member("web4:soft:dev:pytest", role="developer", atp_budget=100)
        member = team.get_member("web4:soft:dev:pytest")
        assert member is not None
        assert member["role"] == "developer"
        assert member["atp_budget"] == 100

    def test_trust_velocity_caps(self):
        """Verify velocity caps limit per-day trust growth."""
        config = TeamConfig(name="velocity-test", description="Velocity cap test")
        team = Team(config=config)
        team.set_admin("web4:soft:admin:vel")
        team.add_member("web4:soft:dev:vel", role="developer")

        # Rapid-fire 50 success updates (same epoch/day)
        for _ in range(50):
            team.update_member_trust("web4:soft:dev:vel", "success", 1.0)

        trust = team.get_member_trust("web4:soft:dev:vel")
        # With velocity caps, no dimension should exceed base + cap
        for dim, val in trust.items():
            cap = Team.TRUST_VELOCITY_CAPS.get(dim, 0.10)
            assert val <= 0.5 + cap + 0.01, (
                f"{dim} exceeded velocity cap: {val:.3f} > {0.5 + cap:.3f}"
            )

    def test_atp_consumption(self):
        config = TeamConfig(name="atp-test", description="ATP test")
        team = Team(config=config)
        team.set_admin("web4:soft:admin:atp")
        team.add_member("web4:soft:dev:atp", role="developer", atp_budget=100)
        remaining = team.consume_member_atp("web4:soft:dev:atp", 30)
        assert remaining == 70
        assert team.get_member_atp("web4:soft:dev:atp") == 70

    def test_audit_chain_integrity(self):
        config = TeamConfig(name="audit-test", description="Audit chain test")
        team = Team(config=config)
        team.set_admin("web4:soft:admin:audit")
        team.add_member("web4:soft:dev:audit", role="developer")
        valid, error = team.verify_audit_chain()
        assert valid is True, f"Audit chain invalid: {error}"


class TestActivityQuality:
    """Activity quality scoring tests."""

    def test_activity_quality_self_test(self):
        """Run the full activity quality self-test."""
        from hardbound.activity_quality import _self_test
        _self_test()

    def test_micro_ping_detection(self):
        """Micro-pings should get minimal trust decay credit."""
        from hardbound.activity_quality import (
            ActivityWindow, ActivityTier, compute_quality_adjusted_decay
        )
        from datetime import datetime, timezone, timedelta

        now = datetime.now(timezone.utc)
        window = ActivityWindow(entity_id="test:micro", window_seconds=86400*7)
        for day in range(7):
            ts = (now - timedelta(days=6-day)).isoformat()
            window.record("presence_ping", ts)

        assert window.tier == ActivityTier.TRIVIAL
        adjusted = compute_quality_adjusted_decay(7, window)
        assert adjusted < 1.0, "Micro-pings should get <1.0 credit for 7 days"

    def test_diverse_work_scores_high(self):
        """Diverse meaningful actions should score well."""
        from hardbound.activity_quality import ActivityWindow, ActivityTier
        from datetime import datetime, timezone, timedelta

        now = datetime.now(timezone.utc)
        window = ActivityWindow(entity_id="test:diverse")
        types = ["r6_created", "r6_approved", "r6_completed", "trust_update",
                 "multisig_vote", "heartbeat", "audit_record"]
        for i, tx_type in enumerate(types):
            ts = (now - timedelta(hours=6-i)).isoformat()
            window.record(tx_type, ts, atp_cost=2.0 if i % 2 == 0 else 0.0)

        assert window.quality_score > 0.4
        assert window.tier in (ActivityTier.HIGH, ActivityTier.CRITICAL)


class TestSybilDetection:
    """Sybil detection tests."""

    def test_sybil_self_test(self):
        """Run the full Sybil detection self-test."""
        from hardbound.sybil_detection import _self_test
        _self_test()

    def test_clean_team_no_false_positives(self):
        """Clean team with diverse trust should not trigger detection."""
        from hardbound.sybil_detection import SybilDetector, SybilRisk

        detector = SybilDetector()
        trusts = {
            "dev_a": {"reliability": 0.75, "competence": 0.60, "alignment": 0.80,
                      "consistency": 0.70, "witnesses": 0.55, "lineage": 0.65},
            "dev_b": {"reliability": 0.50, "competence": 0.85, "alignment": 0.45,
                      "consistency": 0.60, "witnesses": 0.70, "lineage": 0.40},
        }
        report = detector.analyze_team("test:clean", trusts)
        assert report.overall_risk == SybilRisk.NONE

    def test_identical_trust_detected(self):
        """Members with identical trust should be flagged."""
        from hardbound.sybil_detection import SybilDetector, SybilRisk

        detector = SybilDetector()
        same = {"reliability": 0.55, "competence": 0.55, "alignment": 0.55,
                "consistency": 0.55, "witnesses": 0.55, "lineage": 0.55}
        trusts = {
            "sybil_1": same.copy(),
            "sybil_2": same.copy(),
            "honest": {"reliability": 0.80, "competence": 0.60, "alignment": 0.70,
                       "consistency": 0.65, "witnesses": 0.75, "lineage": 0.50},
        }
        report = detector.analyze_team("test:sybil", trusts)
        assert len(report.clusters) > 0
        assert any("sybil_1" in c.members and "sybil_2" in c.members
                   for c in report.clusters)
