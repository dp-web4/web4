# SPDX-License-Identifier: MIT
# Hardbound pytest configuration

import pytest
from .team import Team, TeamConfig


@pytest.fixture
def team():
    """Create a fresh team for testing."""
    config = TeamConfig(name="test-team", description="Pytest test team")
    return Team(config=config)


@pytest.fixture
def team_with_members(team):
    """Team with admin and members set up."""
    admin_lct = "web4:soft:admin:12345"
    dev_lct = "web4:soft:dev:67890"
    reviewer_lct = "web4:soft:reviewer:11111"

    team.set_admin(admin_lct)
    team.add_member(dev_lct, role="developer", atp_budget=50)
    team.add_member(reviewer_lct, role="reviewer")

    return team, admin_lct, dev_lct, reviewer_lct
