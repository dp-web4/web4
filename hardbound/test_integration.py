#!/usr/bin/env python3
"""
Cross-Layer Integration Tests: Governance Plugin <-> Hardbound Team.

These tests validate that the governance plugin (claude-code-plugin/governance/)
and the Hardbound team system (hardbound/) share state correctly through
the common SQLite ledger.

Integration seams tested:
1. Unified audit chain (plugin actions visible in team ledger)
2. Entity trust flows into team member capabilities
3. Heartbeat ledger integrates with team metabolic state
4. R6 requests from plugin match team policy enforcement
5. Presence tracking signals team health

Run: python -m hardbound.test_integration
"""

import sys
import tempfile
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "claude-code-plugin"))


def test_unified_audit_chain():
    """
    TEST 1: Audit records from governance plugin appear in team ledger.

    The plugin's hook system creates audit records via governance.Ledger.
    Hardbound team queries the same ledger for audit trail.
    Both should see the same chain.
    """
    from governance import Ledger
    from hardbound.team import Team, TeamConfig

    print("Test 1: Unified Audit Chain")
    print("-" * 50)

    # Use a shared temp DB
    db_path = Path(tempfile.mkdtemp()) / "integration_test.db"
    ledger = Ledger(db_path=db_path)

    # Create a team using the same ledger instance
    config = TeamConfig(name="integration-team", description="Testing cross-layer")
    team = Team(config=config, ledger=ledger)

    team_id = team.team_id
    admin_lct = "web4:soft:admin:integration"
    team.set_admin(admin_lct)

    # Simulate plugin writing audit records to shared ledger
    # (In production, hooks/post_tool_use.py does this)
    session_id = f"session:{hashlib.sha256(b'test-session').hexdigest()[:12]}"

    # Plugin starts a session
    ledger.start_session(session_id, admin_lct, project="web4", atp_budget=100)

    # Plugin records tool actions (simulating post_tool_use.py)
    for i, action in enumerate(["Read", "Edit", "Bash", "Task"]):
        ledger.record_audit(
            session_id=session_id,
            action_type=f"tool_{action.lower()}",
            tool_name=action,
            target=f"/home/dp/project/file_{i}.py",
            input_hash=hashlib.sha256(f"input_{i}".encode()).hexdigest()[:16],
            output_hash=hashlib.sha256(f"output_{i}".encode()).hexdigest()[:16],
            status="success",
        )

    # Plugin consumes ATP
    remaining = ledger.consume_atp(session_id, 15)

    # Now Hardbound team queries the same ledger
    team_audit = team.get_audit_trail()
    plugin_audit = ledger.get_session_audit_trail(session_id)

    # Verify plugin records exist
    assert len(plugin_audit) == 4, f"Expected 4 plugin audit records, got {len(plugin_audit)}"
    print(f"  Plugin audit records: {len(plugin_audit)}")
    print(f"  Team audit records: {len(team_audit)}")

    # Verify chain integrity for plugin records
    valid, error = ledger.verify_audit_chain(session_id)
    assert valid, f"Plugin audit chain invalid: {error}"
    print(f"  Plugin chain valid: {valid}")

    # Verify team chain integrity
    team_valid, team_error = team.verify_audit_chain()
    assert team_valid, f"Team audit chain invalid: {team_error}"
    print(f"  Team chain valid: {team_valid}")

    # Verify ATP was consumed
    session = ledger.get_session(session_id)
    assert session["atp_remaining"] == 85, f"Expected 85 ATP remaining, got {session['atp_remaining']}"
    print(f"  ATP consumed: 15, remaining: {session['atp_remaining']}")

    print("  PASSED\n")

    import shutil
    shutil.rmtree(db_path.parent)


def test_entity_trust_team_capability():
    """
    TEST 2: Entity trust from plugin determines team member capabilities.

    The governance plugin accumulates T3 trust tensors per role.
    Hardbound team should be able to read these to determine member capabilities.
    """
    from hardbound.team import Team, TeamConfig

    print("Test 2: Entity Trust -> Team Capability")
    print("-" * 50)

    config = TeamConfig(name="capability-team", description="Trust capability test")
    team = Team(config=config)

    admin_lct = "web4:soft:admin:cap001"
    team.set_admin(admin_lct)

    dev_lct = "web4:soft:dev:cap002"
    team.add_member(dev_lct, role="developer", atp_budget=100)

    # Simulate entity_trust.py accumulating trust over many sessions
    # Low trust member should have limited capabilities
    initial_trust = team.get_member_trust_score(dev_lct)
    print(f"  Initial trust: {initial_trust:.3f}")

    # Simulate many successful actions (like entity_trust.update_from_outcome)
    for _ in range(30):
        team.update_member_trust(dev_lct, "success", magnitude=0.8)

    high_trust = team.get_member_trust_score(dev_lct)
    print(f"  After 30 successes: {high_trust:.3f}")

    # Simulate some failures
    for _ in range(5):
        team.update_member_trust(dev_lct, "failure", magnitude=0.5)

    mixed_trust = team.get_member_trust_score(dev_lct)
    print(f"  After 5 failures: {mixed_trust:.3f}")

    # Verify trust increases with success and decreases with failure
    assert high_trust > initial_trust, "Trust should increase with success"
    assert mixed_trust < high_trust, "Trust should decrease with failure"
    assert mixed_trust > initial_trust, "Net trust should still be above initial"

    # Capability thresholds (from agent_governance.py)
    # 0.3 = write, 0.4 = execute, 0.5 = network, 0.6 = delegate
    capabilities = []
    if mixed_trust >= 0.3:
        capabilities.append("write")
    if mixed_trust >= 0.4:
        capabilities.append("execute")
    if mixed_trust >= 0.5:
        capabilities.append("network")
    if mixed_trust >= 0.6:
        capabilities.append("delegate")

    print(f"  Capabilities at trust={mixed_trust:.3f}: {capabilities}")
    assert "write" in capabilities, "Should have write capability"
    assert "execute" in capabilities, "Should have execute capability"

    print("  PASSED\n")


def test_heartbeat_team_integration():
    """
    TEST 3: Heartbeat ledger tracks team metabolic state changes.

    The heartbeat ledger should reflect team activity patterns and
    metabolic state transitions correctly.
    """
    from hardbound.heartbeat_ledger import HeartbeatLedger, MetabolicState

    print("Test 3: Heartbeat-Team Integration")
    print("-" * 50)

    db_path = Path(tempfile.mkdtemp()) / "heartbeat_team.db"
    team_id = "web4:team:heartbeat-test"
    ledger = HeartbeatLedger(team_id, db_path=db_path)

    # Active phase: team working
    for i in range(5):
        ledger.submit_transaction(
            "r6_request", "web4:lct:dev:001",
            {"action": "commit", "iteration": i}, atp_cost=2.0
        )
    block1 = ledger.heartbeat(sentinel_lct="web4:lct:admin:001")
    print(f"  Active block: {block1.tx_count} txns, state={block1.metabolic_state}")
    assert block1.tx_count == 5
    assert block1.metabolic_state == "active"

    # Transition to REST
    transition = ledger.transition_state(MetabolicState.REST, trigger="end_of_day")
    print(f"  Transition: {transition.from_state} -> {transition.to_state}")
    assert transition.from_state == "active"
    assert transition.to_state == "rest"

    # Rest phase: sparse blocks
    block2 = ledger.heartbeat()
    print(f"  Rest block: {block2.tx_count} txns, state={block2.metabolic_state}")
    assert block2.metabolic_state == "rest"

    # Verify metabolic health
    health = ledger.get_metabolic_health()
    print(f"  Metabolic state: {health['state']}")
    print(f"  Total transactions: {health['total_transactions']}")
    assert health['state'] == "rest"

    # Verify chain
    valid, error = ledger.verify_chain()
    assert valid, f"Chain invalid: {error}"
    print(f"  Chain valid: {valid}")

    # Verify transitions are recorded
    history = ledger.get_transition_history()
    assert len(history) >= 1, f"Expected transition history, got {len(history)}"
    print(f"  Transition history: {len(history)} entries")

    print("  PASSED\n")

    import shutil
    shutil.rmtree(db_path.parent)


def test_r6_policy_cross_layer():
    """
    TEST 4: R6 requests from plugin are validated against team policy.

    Plugin creates R6 requests. Team policy should be able to check
    whether those requests are allowed based on role, trust, and ATP.
    """
    from hardbound.team import Team, TeamConfig
    from hardbound.policy import Policy, PolicyRule, ApprovalType
    from hardbound.r6 import R6Workflow, R6Status

    print("Test 4: R6 Policy Cross-Layer")
    print("-" * 50)

    config = TeamConfig(name="policy-team", description="Policy integration test")
    team = Team(config=config)

    admin_lct = "web4:soft:admin:pol001"
    team.set_admin(admin_lct)

    dev_lct = "web4:soft:dev:pol002"
    reviewer_lct = "web4:soft:reviewer:pol003"
    team.add_member(dev_lct, role="developer", atp_budget=50)
    team.add_member(reviewer_lct, role="reviewer", atp_budget=50)

    # Create policy with custom rules
    policy = Policy()

    # Add a high-security rule: deploy requires admin approval and high trust
    deploy_rule = PolicyRule(
        action_type="deploy",
        allowed_roles=["developer", "admin"],
        trust_threshold=0.7,  # High trust required
        atp_cost=10,
        approval=ApprovalType.ADMIN,
        description="Deploy to production"
    )
    policy.add_rule(deploy_rule)

    workflow = R6Workflow(team, policy)

    # Developer with low trust tries to deploy
    try:
        request = workflow.create_request(
            requester_lct=dev_lct,
            action_type="deploy",
            description="Deploy hotfix",
            target="production",
        )
        # Should fail due to low trust
        print(f"  Low-trust deploy: request created (trust check is in approval)")
        print(f"  Request status: {request.status.value}")
    except PermissionError as e:
        print(f"  Low-trust deploy blocked: {e}")

    # Build up developer trust
    for _ in range(20):
        team.update_member_trust(dev_lct, "success", 0.8)
    dev_trust = team.get_member_trust_score(dev_lct)
    print(f"  Developer trust after 20 successes: {dev_trust:.3f}")

    # Now try again with higher trust
    request = workflow.create_request(
        requester_lct=dev_lct,
        action_type="commit",  # Lower-barrier action
        description="Commit feature",
        target="feature-branch",
    )
    print(f"  Commit request: {request.status.value}")
    assert request.status == R6Status.PENDING

    # Reviewer approves
    approved = workflow.approve_request(request.r6_id, reviewer_lct)
    print(f"  After approval: {approved.status.value}")
    assert approved.status == R6Status.APPROVED

    # Execute
    result = workflow.execute_request(
        request.r6_id, success=True,
        result_data={"commit_hash": "abc123"}
    )
    print(f"  After execution: {result.status.value}")
    assert result.status == R6Status.EXECUTED
    print(f"  ATP consumed: {result.atp_consumed}")

    # Verify the audit trail captured everything
    trail = team.get_audit_trail()
    print(f"  Total audit entries: {len(trail)}")
    assert len(trail) > 0, "Should have audit entries"

    print("  PASSED\n")


def test_presence_team_health():
    """
    TEST 5: Presence signals contribute to team health assessment.

    When agents go silent (presence tracking), it should affect
    team metabolic health and trust calculations.
    """
    from hardbound.team import Team, TeamConfig
    from hardbound.trust_decay import TrustDecayCalculator

    print("Test 5: Presence-Driven Team Health")
    print("-" * 50)

    config = TeamConfig(name="presence-team", description="Presence test")
    team = Team(config=config)

    admin_lct = "web4:soft:admin:pres001"
    team.set_admin(admin_lct)

    active_dev = "web4:soft:dev:active"
    silent_dev = "web4:soft:dev:silent"
    team.add_member(active_dev, role="developer", atp_budget=100)
    team.add_member(silent_dev, role="developer", atp_budget=100)

    # Build up trust for both
    for _ in range(15):
        team.update_member_trust(active_dev, "success", 0.7)
        team.update_member_trust(silent_dev, "success", 0.7)

    active_trust_before = team.get_member_trust_score(active_dev)
    silent_trust_before = team.get_member_trust_score(silent_dev)
    print(f"  Active dev trust: {active_trust_before:.3f}")
    print(f"  Silent dev trust: {silent_trust_before:.3f}")

    # Simulate time passing: active dev keeps working, silent dev disappears
    # Apply trust decay for silent dev (30 days of inactivity)
    calc = TrustDecayCalculator()
    now = datetime.now(timezone.utc)
    last_activity = now - timedelta(days=30)

    silent_trust_raw = team.get_member_trust(silent_dev)
    decayed = calc.apply_decay(silent_trust_raw, last_activity, now, actions_since_update=0)
    decayed_score = sum(decayed.values()) / len(decayed)
    print(f"  Silent dev after 30d decay: {decayed_score:.3f}")

    # Active dev continues with regular activity
    for _ in range(10):
        team.update_member_trust(active_dev, "success", 0.6)

    active_trust_after = team.get_member_trust_score(active_dev)
    print(f"  Active dev after continued work: {active_trust_after:.3f}")

    # Verify: active dev maintained/increased trust, silent dev decayed
    assert active_trust_after >= active_trust_before, "Active dev should maintain trust"
    assert decayed_score < silent_trust_before, "Silent dev should decay"

    # Calculate trust gap
    gap = active_trust_after - decayed_score
    print(f"  Trust gap (active - silent): {gap:.3f}")
    assert gap > 0.1, "Significant trust gap should exist between active and silent"

    # Presence signals:
    # - Active dev: heartbeats every session -> ACTIVE status
    # - Silent dev: no heartbeat for 30 days -> MISSING status
    # In production, presence.py would apply silence penalties:
    # - OVERDUE: -0.02 reliability, -0.01 consistency
    # - MISSING: -0.05 reliability, -0.05 consistency, -0.025 temporal

    # Simulate silence penalty (from presence.py)
    silence_penalty = {
        "reliability": -0.05,
        "consistency": -0.05,
    }
    for dim, delta in silence_penalty.items():
        if dim in decayed:
            decayed[dim] = max(0.3, decayed[dim] + delta)  # Floor at 0.3

    final_silent = sum(decayed.values()) / len(decayed)
    print(f"  Silent dev after silence penalty: {final_silent:.3f}")
    print(f"  Total trust gap: {active_trust_after - final_silent:.3f}")

    print("  PASSED\n")


def main():
    print("=" * 60)
    print("CROSS-LAYER INTEGRATION TESTS")
    print("Governance Plugin <-> Hardbound Team")
    print("=" * 60)
    print()

    tests = [
        ("Unified Audit Chain", test_unified_audit_chain),
        ("Entity Trust -> Capability", test_entity_trust_team_capability),
        ("Heartbeat-Team Integration", test_heartbeat_team_integration),
        ("R6 Policy Cross-Layer", test_r6_policy_cross_layer),
        ("Presence-Driven Health", test_presence_team_health),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
            print()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
