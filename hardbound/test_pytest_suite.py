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
