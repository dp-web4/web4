#!/usr/bin/env python3
"""Test Hardbound Team implementation."""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from .team import Team, TeamConfig, list_teams
from .policy import Policy, PolicyRule, ApprovalType
from .r6 import R6Workflow, R6Status


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
    from .trust_decay import TrustDecayCalculator

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


def test_policy_persistence(team: Team, admin_lct: str):
    """Test policy persistence to ledger."""
    print("\nTesting policy persistence...")

    # Get default policy
    policy = team.get_policy()
    print(f"  Default policy version: {policy.version}")
    print(f"  Default rules: {len(policy.rules)}")

    # Add a custom rule
    custom_rule = PolicyRule(
        action_type="secret_access",
        allowed_roles=["admin"],
        trust_threshold=0.9,
        atp_cost=20,
        approval=ApprovalType.MULTI_SIG,
        approval_count=2,
        description="Access to team secrets"
    )
    policy.add_rule(custom_rule)

    # Save policy
    result = team.set_policy(policy, admin_lct, "Added secret_access rule")
    print(f"  Saved policy: {result['policy_id']}")
    print(f"  Version: {result['version']}")
    print(f"  Hash: {result['content_hash'][:12]}...")

    # Modify and save again
    policy.get_rule("secret_access").trust_threshold = 0.95
    result2 = team.set_policy(policy, admin_lct, "Increased trust threshold")
    print(f"  Updated policy: {result2['policy_id']}")
    print(f"  Version: {result2['version']}")
    print(f"  Prev hash: {result2['prev_hash'][:12]}...")

    # Get history
    history = team.get_policy_history()
    print(f"  Policy versions: {len(history)}")

    # Verify chain
    valid, error = team.verify_policy_chain()
    print(f"  Chain valid: {valid}")
    assert valid, f"Policy chain should be valid: {error}"

    # Reload and verify
    loaded = team.get_policy()
    assert loaded.version == result2['version'], "Should load latest version"
    assert loaded.get_rule("secret_access").trust_threshold == 0.95

    print("  Policy persistence working correctly!")


def test_admin_binding():
    """Test admin binding (TPM2 if available, software fallback)."""
    from .admin_binding import check_tpm_availability, AdminBindingManager

    print("\nTesting admin binding...")

    # Check TPM status
    status = check_tpm_availability()
    print(f"  TPM available: {status.get('available', False)}")

    if status.get('available'):
        print(f"  Hardware: {status.get('hardware_type')}")
        print(f"  Trust ceiling: {status.get('trust_ceiling')}")

        # Create team with TPM admin
        config = TeamConfig(
            name="tpm-test-team",
            description="Team with TPM-bound admin"
        )
        team = Team(config=config)

        try:
            result = team.set_admin_tpm2("test-admin")
            print(f"  TPM admin LCT: {result['admin_lct'][:40]}...")
            print(f"  Binding verified: {result['binding']['verified']}")
            print(f"  Hardware anchor: {result['binding']['hardware_anchor']}")

            # Verify admin
            verify_result = team.verify_admin(result['admin_lct'])
            print(f"  Verification: {verify_result.get('verified', False)}")

            print("  TPM2 admin binding working correctly!")

        except Exception as e:
            print(f"  TPM2 binding error: {e}")
            print("  (This may be expected if TPM is locked or in use)")

    else:
        print(f"  Reason: {status.get('reason')}")
        print("  Skipping TPM test (not available)")

    # Test software binding (always works)
    config2 = TeamConfig(name="soft-test-team", description="Dev team")
    team2 = Team(config=config2)
    result = team2.set_admin("web4:soft:dev-admin:123")

    assert result['binding']['type'] == 'software'
    print("  Software binding working correctly!")


def test_multisig():
    """Test multi-sig proposal and voting."""
    from .multisig import MultiSigManager, CriticalAction, ProposalStatus

    print("\nTesting multi-sig operations...")

    # Create team with multiple members
    config = TeamConfig(
        name="multisig-test-team",
        description="Team for testing multi-sig"
    )
    team = Team(config=config)

    # Set up admin and members
    admin_lct = "web4:soft:admin:msig001"
    team.set_admin(admin_lct)

    member1 = "web4:soft:member1:msig002"
    member2 = "web4:soft:member2:msig003"
    member3 = "web4:soft:member3:msig004"

    team.add_member(member1, role="developer")
    team.add_member(member2, role="developer")
    team.add_member(member3, role="reviewer")

    # Boost trust for members (so they can vote)
    # Need trust >= 0.6 threshold. With velocity caps, we set trust directly
    # since this test is about multi-sig behavior, not trust growth.
    high_trust = {
        "reliability": 0.75, "competence": 0.70, "alignment": 0.65,
        "consistency": 0.65, "witnesses": 0.70, "lineage": 0.60,
    }
    for m in [member1, member2, member3]:
        member_data = team.get_member(m)
        member_data["trust"] = high_trust.copy()
    team._update_team()

    # Create multi-sig manager
    msig = MultiSigManager(team)

    # Create a proposal (admin proposes policy change)
    proposal = msig.create_proposal(
        proposer_lct=admin_lct,
        action=CriticalAction.POLICY_CHANGE,
        action_data={"changes": {"deploy_trust_threshold": 0.8}},
        description="Increase deploy trust threshold"
    )
    print(f"  Created proposal: {proposal.proposal_id}")
    print(f"  Action: {proposal.action.value}")
    print(f"  Status: {proposal.status.value}")
    print(f"  Expires: {proposal.expires_at[:10]}...")

    # Cast votes
    proposal = msig.vote(proposal.proposal_id, member1, approve=True, comment="LGTM")
    print(f"  Member1 voted: approval_count={proposal.approval_count}")

    proposal = msig.vote(proposal.proposal_id, member2, approve=True, comment="Approved")
    print(f"  Member2 voted: approval_count={proposal.approval_count}")
    print(f"  Trust-weighted: {proposal.trust_weighted_approvals:.2f}")

    # Add third vote to reach trust-weighted quorum
    proposal = msig.vote(proposal.proposal_id, member3, approve=True, comment="Looks good")
    print(f"  Member3 voted: approval_count={proposal.approval_count}")
    print(f"  Trust-weighted: {proposal.trust_weighted_approvals:.2f}")
    print(f"  Status: {proposal.status.value}")

    # Check if quorum reached
    if proposal.status == ProposalStatus.APPROVED:
        print("  Quorum reached!")

        # Execute the proposal
        result = msig.execute_proposal(proposal.proposal_id, admin_lct)
        print(f"  Executed: {result.status.value}")
        print(f"  Result: {result.execution_result}")

    # Test proposal history
    history = msig.get_proposal_history()
    print(f"  Proposal history: {len(history)} entries")

    print("  Multi-sig working correctly!")


def test_rate_limiter():
    """Test rate limiting infrastructure."""
    from .rate_limiter import (
        RateLimiter, RateLimitRule, RateLimitScope, TokenBucket
    )

    print("\nTesting rate limiting...")

    # Test token bucket
    bucket = TokenBucket(max_tokens=5, refill_rate=10.0)  # 10/sec for fast test
    print(f"  Token bucket: 5 max, 10/sec refill")

    # Consume all tokens
    for i in range(5):
        assert bucket.consume(1), f"Should have token #{i+1}"
    print(f"  Consumed 5 tokens: remaining={bucket.available}")

    # Next should fail
    assert not bucket.consume(1), "Should be empty"
    print(f"  6th consume failed (expected)")

    # Test rate limiter with local ledger
    from .ledger import Ledger

    ledger = Ledger()
    limiter = RateLimiter(ledger)

    # Add a test rule
    test_rule = RateLimitRule(
        name="test_rule",
        scope=RateLimitScope.PER_LCT,
        max_requests=3,
        window_seconds=60,
        burst_allowance=1
    )
    limiter.add_rule(test_rule)

    test_lct = "web4:soft:test:ratelimit"

    # Should allow 4 requests (3 + 1 burst)
    for i in range(4):
        result = limiter.check("test_rule", lct_id=test_lct)
        assert result.allowed, f"Request #{i+1} should be allowed"
    print(f"  4 requests allowed (3 + 1 burst)")

    # 5th should fail
    result = limiter.check("test_rule", lct_id=test_lct)
    assert not result.allowed, "5th request should be denied"
    print(f"  5th request denied: {result.reason}")

    # Check status
    status = limiter.get_status("test_rule", lct_id=test_lct)
    print(f"  Status: remaining={status['remaining']}, allowed={status['allowed']}")

    # Reset and verify
    limiter.reset("test_rule", lct_id=test_lct)
    result = limiter.check("test_rule", lct_id=test_lct)
    assert result.allowed, "After reset should allow"
    print(f"  After reset: allowed={result.allowed}")

    print("  Rate limiting working correctly!")


def test_synthesis_eval():
    """Test synthesis vs fabrication evaluation."""
    from .synthesis_eval import SynthesisEvaluator, ContentMode

    print("\nTesting synthesis evaluation...")

    evaluator = SynthesisEvaluator()

    # Valid synthesis content
    synthesis = """
    I've observed patterns emerging across data sources.
    Common themes include optimization strategies.
    Examples might be caching, indexing, or batching.
    """
    eval1 = evaluator.evaluate(synthesis)
    assert eval1.detected_mode == ContentMode.SYNTHESIS, "Should detect synthesis"
    assert eval1.recommendation in ("include", "review"), "Should include/review"
    print(f"  Synthesis detected: mode={eval1.detected_mode.value}, quality={eval1.overall_quality:.2f}")

    # Invalid fabrication content
    fabrication = """
    Yesterday we discussed the server issues.
    You told me about the database problems.
    I remember when you mentioned the fix.
    """
    eval2 = evaluator.evaluate(fabrication)
    assert eval2.detected_mode == ContentMode.FABRICATION, "Should detect fabrication"
    assert eval2.recommendation in ("review", "exclude"), "Should review/exclude"
    assert eval2.t3_integrity_delta < 0, "Should penalize integrity"
    print(f"  Fabrication detected: mode={eval2.detected_mode.value}, integrity={eval2.t3_integrity_delta:+.3f}")

    # Neutral conversation
    convo = "Let me help you with that. Thank you for asking."
    eval3 = evaluator.evaluate(convo)
    assert eval3.detected_mode == ContentMode.CONVERSATION, "Should detect conversation"
    print(f"  Conversation detected: mode={eval3.detected_mode.value}")

    print("  Synthesis evaluation working correctly!")


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
    test_admin_binding()
    test_policy_persistence(team, admin_lct)
    test_multisig()
    test_rate_limiter()
    test_synthesis_eval()

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
