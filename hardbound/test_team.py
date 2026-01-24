#!/usr/bin/env python3
"""Test Hardbound Team implementation."""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hardbound.team import Team, TeamConfig, list_teams
from hardbound.policy import Policy, PolicyRule, ApprovalType
from hardbound.r6 import R6Workflow, R6Status


def test_team_creation():
    """Test team creation."""
    print("Testing team creation...")

    config = TeamConfig(
        name="test-team",
        description="A test team for Hardbound",
        default_member_budget=100
    )

    team = Team(config=config)

    assert team.team_id.startswith("web4:team:")
    assert team.config.name == "test-team"
    print(f"  Created team: {team.team_id}")

    return team


def test_admin_and_members(team: Team):
    """Test admin and member management."""
    print("\nTesting admin and member management...")

    # Set admin
    admin_lct = "web4:soft:admin:12345"
    result = team.set_admin(admin_lct, binding_type="software")
    assert team.admin_lct == admin_lct
    print(f"  Set admin: {admin_lct}")

    # Add members
    dev_lct = "web4:soft:dev:67890"
    dev = team.add_member(dev_lct, role="developer", atp_budget=50)
    assert dev["atp_budget"] == 50
    print(f"  Added developer: {dev_lct}")

    reviewer_lct = "web4:soft:reviewer:11111"
    team.add_member(reviewer_lct, role="reviewer")
    print(f"  Added reviewer: {reviewer_lct}")

    # List members
    members = team.list_members()
    assert len(members) == 2
    print(f"  Total members: {len(members)}")

    return admin_lct, dev_lct, reviewer_lct


def test_atp_and_trust(team: Team, dev_lct: str):
    """Test ATP and trust management."""
    print("\nTesting ATP and trust...")

    # Check initial ATP
    atp = team.get_member_atp(dev_lct)
    assert atp == 50
    print(f"  Initial ATP: {atp}")

    # Consume ATP
    remaining = team.consume_member_atp(dev_lct, 10)
    assert remaining == 40
    print(f"  After consuming 10: {remaining}")

    # Update trust
    trust = team.update_member_trust(dev_lct, "success", 0.5)
    print(f"  After success: reliability={trust['reliability']:.3f}")

    trust = team.update_member_trust(dev_lct, "failure", 0.2)
    print(f"  After failure: reliability={trust['reliability']:.3f}")


def test_r6_workflow(team: Team, admin_lct: str, dev_lct: str, reviewer_lct: str):
    """Test R6 request workflow."""
    print("\nTesting R6 workflow...")

    policy = Policy()
    workflow = R6Workflow(team, policy)

    # Create request
    request = workflow.create_request(
        requester_lct=dev_lct,
        action_type="commit",
        description="Add new feature",
        target="feature-branch",
        reference_type="issue",
        reference_id="123"
    )

    assert request.status == R6Status.PENDING
    print(f"  Created request: {request.r6_id}")
    print(f"  Status: {request.status.value}")

    # Approve by peer (reviewer)
    request = workflow.approve_request(request.r6_id, reviewer_lct)
    assert request.status == R6Status.APPROVED
    print(f"  After approval: {request.status.value}")

    # Execute
    response = workflow.execute_request(
        request.r6_id,
        success=True,
        result_data={"commit_hash": "abc123"}
    )

    assert response.status == R6Status.EXECUTED
    print(f"  After execution: {response.status.value}")
    print(f"  ATP consumed: {response.atp_consumed}")


def test_audit_trail(team: Team):
    """Test audit trail and verification."""
    print("\nTesting audit trail...")

    trail = team.get_audit_trail()
    print(f"  Audit entries: {len(trail)}")

    for entry in trail[:3]:
        print(f"    [{entry['sequence']}] {entry['action_type']}")

    # Verify chain
    valid, error = team.verify_audit_chain()
    print(f"  Chain valid: {valid}")
    if error:
        print(f"  Error: {error}")


def test_team_summary(team: Team):
    """Test team summary."""
    print("\nTeam Summary:")
    summary = team.summary()
    print(f"  Team ID: {summary['team_id']}")
    print(f"  Name: {summary['name']}")
    print(f"  Admin: {summary['admin_lct']}")
    print(f"  Members: {summary['member_count']}")
    for m in summary['members']:
        print(f"    - {m['role']}: trust={m['trust_score']:.2f}, ATP={m['atp_remaining']}")


def test_trust_decay():
    """Test trust decay over time."""
    from datetime import timedelta
    from hardbound.trust_decay import TrustDecayCalculator

    print("\nTesting trust decay...")

    calc = TrustDecayCalculator()

    # Simulate trust from 30 days ago
    high_trust = {
        'competence': 0.9,
        'reliability': 0.85,
        'consistency': 0.8,
        'witnesses': 0.7,
        'lineage': 0.9,
        'alignment': 0.75
    }

    # Apply 30 days of decay with no activity
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    last_update = now - timedelta(days=30)

    decayed = calc.apply_decay(high_trust, last_update, now, actions_since_update=0)

    print(f"  Original (30 days ago): avg={sum(high_trust.values())/6:.3f}")
    print(f"  After decay (no activity): avg={sum(decayed.values())/6:.3f}")

    # Witnesses should decay fastest (0.10 rate)
    witness_decay = high_trust['witnesses'] - decayed['witnesses']
    lineage_decay = high_trust['lineage'] - decayed['lineage']
    print(f"  Witness decay: {witness_decay:.3f} (fastest)")
    print(f"  Lineage decay: {lineage_decay:.3f} (slowest)")

    assert witness_decay > lineage_decay, "Witnesses should decay faster than lineage"
    assert decayed['witnesses'] > 0.5, "Trust should not go below baseline"

    print("  Trust decay working correctly!")


def main():
    print("=" * 60)
    print("Hardbound Team Test")
    print("=" * 60)

    team = test_team_creation()
    admin_lct, dev_lct, reviewer_lct = test_admin_and_members(team)
    test_atp_and_trust(team, dev_lct)
    test_r6_workflow(team, admin_lct, dev_lct, reviewer_lct)
    test_audit_trail(team)
    test_team_summary(team)
    test_trust_decay()

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
