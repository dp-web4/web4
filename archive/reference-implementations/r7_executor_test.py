#!/usr/bin/env python3
"""
R7 Action Framework — Test Suite
==================================

Tests the R7 executor's compliance with web4-standard/core-spec/r7-framework.md.

Covers:
1. Full R7 transaction flow (validate → execute → reputation → settle)
2. Role-contextualized reputation (same entity, different roles)
3. Even failures produce reputation deltas (R7 requirement)
4. ATP staking amplifies reputation
5. Prohibition enforcement
6. Resource insufficiency handling
7. Custom reputation rules
8. Ledger hash-chain integrity
9. Reputation history and analytics
10. Multiple actions accumulate reputation on MRH role pairing

Date: 2026-02-20
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from r7_executor import (
    R7Executor, R7Action, R7ActionBuilder, R7Result,
    R7Rules, R7Role, R7Request, R7Reference, R7Resource,
    ReputationDelta, ReputationRule, ReputationRuleType,
    TensorDelta, ContributingFactor,
    R7Error, RuleViolation, RoleUnauthorized, ResourceInsufficient,
)
from web4_entity import T3Tensor, V3Tensor


def test_simple_success():
    """Test 1: Basic successful action produces positive reputation."""
    executor = R7Executor()
    action = (R7ActionBuilder("read", "data:test")
        .as_actor("lct:web4:human:alice", "lct:web4:role:reader")
        .with_resources(atp_required=1.0, atp_available=100.0)
        .build())

    result, rep = executor.process(action)

    assert result.status == "success", f"Expected success, got {result.status}"
    assert result.atp_consumed == 1.0
    assert rep.net_trust_change > 0, "Successful action should increase trust"
    assert rep.net_value_change > 0, "Successful action should increase value"
    assert rep.subject_lct == "lct:web4:human:alice"
    assert rep.role_lct == "lct:web4:role:reader"
    assert rep.action_type == "read"
    assert len(rep.contributing_factors) > 0
    print("  ✓ Test 1: Simple success — positive reputation delta")


def test_failure_penalty():
    """Test 2: Failed actions produce negative reputation (R7 requirement)."""
    executor = R7Executor()

    def always_fail(action):
        raise RuntimeError("Intentional failure")

    executor.register_effector("risky_action", always_fail)

    action = (R7ActionBuilder("risky_action", "resource:fragile")
        .as_actor("lct:web4:ai:agent", "lct:web4:role:operator")
        .with_resources(atp_required=20.0, atp_available=200.0)
        .build())

    result, rep = executor.process(action)

    assert result.status == "failure"
    assert rep.net_trust_change < 0, "Failed action should decrease trust"
    assert result.atp_consumed < 20.0, "Failure should have reduced ATP cost"
    assert result.error == "Intentional failure"
    print("  ✓ Test 2: Failure penalty — negative reputation delta")


def test_prohibition_enforcement():
    """Test 3: Prohibited actions are rejected with reputation impact."""
    executor = R7Executor()
    action = (R7ActionBuilder("delete", "data:protected")
        .as_actor("lct:web4:human:eve", "lct:web4:role:viewer")
        .with_rules(prohibitions=["delete"])
        .with_resources(atp_required=10.0, atp_available=100.0)
        .build())

    result, rep = executor.process(action)

    assert result.status == "error"
    assert "prohibited" in result.error.lower()
    assert rep.net_trust_change < 0, "Prohibited action attempt should decrease trust"
    print("  ✓ Test 3: Prohibition enforcement — action rejected")


def test_resource_insufficient():
    """Test 4: Insufficient resources are caught in validation."""
    executor = R7Executor()
    action = (R7ActionBuilder("train", "dataset:huge")
        .as_actor("lct:web4:ai:trainer", "lct:web4:role:ml_engineer")
        .with_resources(atp_required=500.0, atp_available=50.0)
        .build())

    result, rep = executor.process(action)

    assert result.status == "error"
    assert "Insufficient ATP" in result.error
    print("  ✓ Test 4: Resource insufficient — validation error")


def test_role_contextualized_reputation():
    """Test 5: Same entity, different roles → independent reputations (R7 core)."""
    executor = R7Executor()

    # Entity acts as analyst (success)
    action_analyst = (R7ActionBuilder("analyze", "data:financials")
        .as_actor("lct:web4:ai:sage", "lct:web4:role:analyst")
        .with_resources(atp_required=10.0, atp_available=500.0)
        .build())
    r1, rep1 = executor.process(action_analyst)
    assert r1.status == "success"

    # Same entity acts as operator (failure)
    def fail_deploy(action):
        raise RuntimeError("Deployment failed")
    executor.register_effector("deploy", fail_deploy)

    action_operator = (R7ActionBuilder("deploy", "service:prod")
        .as_actor("lct:web4:ai:sage", "lct:web4:role:operator")
        .with_resources(atp_required=30.0, atp_available=500.0)
        .build())
    r2, rep2 = executor.process(action_operator)
    assert r2.status == "failure"

    # Check reputations are independent
    all_reps = executor.get_cumulative_reputation("lct:web4:ai:sage")
    assert "lct:web4:role:analyst" in all_reps
    assert "lct:web4:role:operator" in all_reps

    analyst_t3 = all_reps["lct:web4:role:analyst"]["t3"]["composite"]
    operator_t3 = all_reps["lct:web4:role:operator"]["t3"]["composite"]

    assert analyst_t3 > operator_t3, (
        f"Analyst (success) should have higher T3 ({analyst_t3:.4f}) "
        f"than operator (failure) ({operator_t3:.4f})"
    )
    print("  ✓ Test 5: Role-contextualized reputation — independent per role")


def test_atp_staking_amplifies_reputation():
    """Test 6: ATP staking amplifies reputation rewards."""
    executor = R7Executor()

    # Action without stake
    action_no_stake = (R7ActionBuilder("query", "data:test")
        .as_actor("lct:web4:human:alice", "lct:web4:role:researcher")
        .with_resources(atp_required=5.0, atp_available=500.0)
        .build())
    r1, rep1 = executor.process(action_no_stake)

    # Action with large stake (separate executor to isolate)
    executor2 = R7Executor()
    action_staked = (R7ActionBuilder("query", "data:test")
        .as_actor("lct:web4:human:alice", "lct:web4:role:researcher")
        .with_resources(atp_required=5.0, atp_available=500.0)
        .with_stake(200.0)
        .build())
    r2, rep2 = executor2.process(action_staked)

    assert rep2.net_trust_change > rep1.net_trust_change, (
        f"Staked ({rep2.net_trust_change:+.4f}) should exceed unstaked ({rep1.net_trust_change:+.4f})"
    )
    print(f"  ✓ Test 6: ATP staking amplifies reputation — "
          f"unstaked={rep1.net_trust_change:+.4f}, staked={rep2.net_trust_change:+.4f}")


def test_custom_reputation_rules():
    """Test 7: Custom reputation rules can be defined per-action."""
    executor = R7Executor()

    custom_rule = ReputationRule(
        rule_id="bonus_training_complete",
        rule_type=ReputationRuleType.SUCCESS_REWARD,
        action_pattern="complete_training",
        affects_t3={"training": 0.05, "talent": 0.03},
        affects_v3={"veracity": 0.04},
    )

    action = (R7ActionBuilder("complete_training", "course:ml-advanced")
        .as_actor("lct:web4:human:bob", "lct:web4:role:student")
        .with_resources(atp_required=10.0, atp_available=100.0)
        .with_reputation_rule(custom_rule)
        .build())

    result, rep = executor.process(action)

    assert result.status == "success"
    # Custom rule should produce larger deltas than defaults
    assert rep.net_trust_change >= 0.05, (
        f"Custom rule should boost trust significantly, got {rep.net_trust_change:+.4f}"
    )
    print(f"  ✓ Test 7: Custom reputation rules — net_trust={rep.net_trust_change:+.4f}")


def test_ledger_integrity():
    """Test 8: Ledger hash chain integrity after multiple actions."""
    executor = R7Executor()

    # Execute several actions
    for i in range(5):
        action = (R7ActionBuilder(f"action_{i}", f"target_{i}")
            .as_actor("lct:web4:ai:agent", "lct:web4:role:worker")
            .with_resources(atp_required=5.0, atp_available=500.0)
            .build())
        executor.process(action)

    valid, count = executor.verify_ledger_integrity()
    assert valid, "Ledger hash chain should be valid"
    assert count == 5, f"Expected 5 entries, got {count}"

    # Verify entries are properly chained
    for i in range(1, len(executor.ledger)):
        assert executor.ledger[i].prev_hash == executor.ledger[i-1].entry_hash, \
            f"Entry {i} prev_hash mismatch"

    print(f"  ✓ Test 8: Ledger integrity — {count} entries, chain valid")


def test_reputation_history():
    """Test 9: Reputation history tracks all actions with role filtering."""
    executor = R7Executor()

    # 3 actions as analyst, 2 as operator
    for i in range(3):
        action = (R7ActionBuilder(f"analyze_{i}", f"data_{i}")
            .as_actor("lct:web4:ai:sage", "lct:web4:role:analyst")
            .with_resources(atp_required=5.0, atp_available=500.0)
            .build())
        executor.process(action)

    for i in range(2):
        action = (R7ActionBuilder(f"operate_{i}", f"service_{i}")
            .as_actor("lct:web4:ai:sage", "lct:web4:role:operator")
            .with_resources(atp_required=10.0, atp_available=500.0)
            .build())
        executor.process(action)

    # All history
    all_history = executor.get_reputation_history("lct:web4:ai:sage")
    assert len(all_history) == 5, f"Expected 5 entries, got {len(all_history)}"

    # Filtered by role
    analyst_history = executor.get_reputation_history("lct:web4:ai:sage", "lct:web4:role:analyst")
    assert len(analyst_history) == 3, f"Expected 3 analyst entries, got {len(analyst_history)}"

    operator_history = executor.get_reputation_history("lct:web4:ai:sage", "lct:web4:role:operator")
    assert len(operator_history) == 2, f"Expected 2 operator entries, got {len(operator_history)}"

    print(f"  ✓ Test 9: Reputation history — 5 total, 3 analyst, 2 operator")


def test_reputation_accumulation():
    """Test 10: Multiple actions accumulate on MRH role pairing link."""
    executor = R7Executor()

    # 10 successful actions in same role
    for i in range(10):
        action = (R7ActionBuilder(f"build_{i}", f"feature_{i}")
            .as_actor("lct:web4:human:dev", "lct:web4:role:engineer")
            .with_resources(atp_required=10.0, atp_available=500.0)
            .build())
        executor.process(action)

    # Check accumulated reputation
    reps = executor.get_cumulative_reputation("lct:web4:human:dev")
    eng_t3 = reps["lct:web4:role:engineer"]["t3"]
    eng_v3 = reps["lct:web4:role:engineer"]["v3"]

    # After 10 successes, trust should be above baseline (0.5)
    # Default rules: +0.01 training, +0.005 temperament per success
    # 10 × 0.01 = +0.1 training, 10 × 0.005 = +0.05 temperament
    # Composite = 0.4×0.5 + 0.3×0.6 + 0.3×0.55 = 0.545
    assert eng_t3["composite"] > 0.53, (
        f"10 successes should raise T3 composite above 0.53, got {eng_t3['composite']:.4f}"
    )
    assert eng_v3["composite"] > 0.35, (
        f"10 successes should raise V3 composite above baseline, got {eng_v3['composite']:.4f}"
    )

    print(f"  ✓ Test 10: Reputation accumulation — T3={eng_t3['composite']:.4f}, V3={eng_v3['composite']:.4f}")


def test_escrow_refund_on_failure():
    """Test 11: Escrowed ATP is partially refunded on failure."""
    executor = R7Executor()

    def fail_compute(action):
        raise RuntimeError("Out of memory")
    executor.register_effector("heavy_compute", fail_compute)

    action = (R7ActionBuilder("heavy_compute", "dataset:large")
        .as_actor("lct:web4:ai:worker", "lct:web4:role:processor")
        .with_resources(atp_required=100.0, atp_available=500.0, escrow=100.0)
        .build())

    result, rep = executor.process(action)

    assert result.status == "failure"
    assert result.atp_refunded > 0, "Failed action should get partial escrow refund"
    assert result.atp_refunded == 80.0, f"Expected 80% refund (80.0), got {result.atp_refunded}"
    print(f"  ✓ Test 11: Escrow refund on failure — refunded {result.atp_refunded} ATP")


def test_missing_actor_validation():
    """Test 12: Actions without actor LCT are rejected."""
    executor = R7Executor()
    action = R7Action()
    action.request.action = "read"
    action.resource.required_atp = 1.0
    action.resource.available_atp = 100.0

    result, rep = executor.process(action)
    assert result.status == "error"
    assert "Missing actor" in result.error
    print("  ✓ Test 12: Missing actor validation — rejected")


def test_permission_check():
    """Test 13: Actions not in permissions list are rejected."""
    executor = R7Executor()
    action = (R7ActionBuilder("write", "data:important")
        .as_actor("lct:web4:human:alice", "lct:web4:role:reader")
        .with_rules(permissions=["read"])  # only read allowed
        .with_resources(atp_required=5.0, atp_available=100.0)
        .build())

    result, rep = executor.process(action)
    assert result.status == "error"
    assert "not in permitted" in result.error
    print("  ✓ Test 13: Permission check — write rejected for reader role")


def test_reputation_delta_serialization():
    """Test 14: ReputationDelta serializes to spec-compliant JSON."""
    executor = R7Executor()
    action = (R7ActionBuilder("analyze", "data:test")
        .as_actor("lct:web4:ai:sage", "lct:web4:role:analyst")
        .with_resources(atp_required=10.0, atp_available=500.0)
        .with_stake(50.0)
        .with_witnesses("lct:web4:witness:w1")
        .build())

    result, rep = executor.process(action)
    rep_dict = rep.to_dict()

    # Check all required fields from spec §1.7
    assert "subject_lct" in rep_dict
    assert "role_lct" in rep_dict
    assert "action_type" in rep_dict
    assert "action_id" in rep_dict
    assert "t3_delta" in rep_dict
    assert "v3_delta" in rep_dict
    assert "contributing_factors" in rep_dict
    assert "witnesses" in rep_dict
    assert "net_trust_change" in rep_dict
    assert "net_value_change" in rep_dict
    assert "timestamp" in rep_dict
    assert rep_dict["witnesses"] == ["lct:web4:witness:w1"]
    print("  ✓ Test 14: Reputation serialization — spec-compliant JSON")


def main():
    print("=" * 70)
    print("  R7 Action Framework — Test Suite")
    print("=" * 70)

    tests = [
        test_simple_success,
        test_failure_penalty,
        test_prohibition_enforcement,
        test_resource_insufficient,
        test_role_contextualized_reputation,
        test_atp_staking_amplifies_reputation,
        test_custom_reputation_rules,
        test_ledger_integrity,
        test_reputation_history,
        test_reputation_accumulation,
        test_escrow_refund_on_failure,
        test_missing_actor_validation,
        test_permission_check,
        test_reputation_delta_serialization,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__}: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"  Results: {passed}/{passed + failed} tests passed")
    if failed == 0:
        print("  All tests passed!")
    else:
        print(f"  {failed} test(s) FAILED")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
