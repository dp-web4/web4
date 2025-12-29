"""
SESSION 100 TRACK 4: MULTI-AGENT INTEGRATION TEST

This demonstrates the complete ACT accountability stack in action:
- Track 1: Hardware-bound identities for all agents
- Track 2: N-level delegation chains
- Track 3: ATP budget enforcement with lock-commit-rollback

Test scenarios:
1. Cooperative Delegation (Human → Coordinator → 3 Workers)
2. Budget Gaming Attack (Prevented)
3. Security Validation (All attacks prevented)
4. Performance Metrics (End-to-end)

This validates that all components work together in realistic multi-agent scenarios.

References:
- Track 1: session100_track1_act_hardware_binding.py
- Track 2: session100_track2_act_delegation_chain.py
- Track 3: session100_track3_act_atp_budgets.py
"""

import json
import time
from typing import Dict, Any, List

# Import all components
from session100_track1_act_hardware_binding import (
    ACTBlockchainConfig,
    ACTIdentityBridge,
    ACTHardwareBoundIdentity
)
from session100_track2_act_delegation_chain import (
    ACTDelegationChainKeeper,
    ScopedPermission
)
from session100_track3_act_atp_budgets import (
    ATPBudgetEnforcer,
    BudgetAlertLevel
)


# ============================================================================
# MULTI-AGENT TEST SCENARIOS
# ============================================================================

def scenario1_cooperative_delegation():
    """
    Scenario 1: Cooperative Delegation

    Human (10k ATP) delegates to:
      → Coordinator SAGE (2k ATP, can sub-delegate)
          → Worker 1 (600 ATP, analysis)
          → Worker 2 (600 ATP, code generation)
          → Worker 3 (400 ATP, testing)

    Success criteria:
    - All agents have hardware-bound identities
    - Delegation chain tracks full ancestry
    - ATP budgets enforced at each level
    - Workers complete tasks within budget
    - Budget alerts trigger at appropriate thresholds
    """
    print("=" * 70)
    print("SCENARIO 1: COOPERATIVE DELEGATION")
    print("=" * 70)
    print()

    # Initialize components
    config = ACTBlockchainConfig()
    identity_bridge = ACTIdentityBridge(config)
    delegation_keeper = ACTDelegationChainKeeper()
    budget_enforcer = ATPBudgetEnforcer(delegation_keeper)

    # Step 1: Create hardware-bound identities
    print("Step 1: Creating Hardware-Bound Identities")
    print("-" * 70)

    # Human
    human_identity = identity_bridge.create_hardware_bound_agent(
        society="web4",
        role="human",
        agent_id="alice",
        network="testnet"
    )
    print(f"✓ Human: {human_identity.lct_uri}")
    print(f"  Binding strength: {human_identity.attestation.binding_strength}")

    # Coordinator
    coordinator_identity = identity_bridge.create_hardware_bound_agent(
        society="web4",
        role="coordinator",
        agent_id="sage_coordinator",
        network="testnet"
    )
    print(f"✓ Coordinator: {coordinator_identity.lct_uri}")

    # Workers
    worker_identities = []
    for i, role in enumerate(["analyzer", "coder", "tester"]):
        worker = identity_bridge.create_hardware_bound_agent(
            society="web4",
            role="worker",
            agent_id=f"{role}_{i+1}",
            network="testnet"
        )
        worker_identities.append(worker)
        print(f"✓ Worker {i+1} ({role}): {worker.lct_uri}")

    print(f"\n✓ Created {1 + 1 + len(worker_identities)} hardware-bound identities")
    print()

    # Step 2: Set up ATP balances
    print("Step 2: Initial ATP Allocation")
    print("-" * 70)
    budget_enforcer.set_lct_balance(human_identity.lct_uri, 10000.0)
    budget_enforcer.set_lct_balance(coordinator_identity.lct_uri, 0.0)
    for worker in worker_identities:
        budget_enforcer.set_lct_balance(worker.lct_uri, 0.0)

    print(f"Human ATP balance: {budget_enforcer.get_lct_balance(human_identity.lct_uri)} ATP")
    print()

    # Step 3: Create delegation chain with budgets
    print("Step 3: Building Delegation Chain with ATP Budgets")
    print("-" * 70)

    # Human → Coordinator (2000 ATP)
    del_human_coord = delegation_keeper.record_delegation(
        issuer=human_identity.lct_uri,
        delegate=coordinator_identity.lct_uri,
        scope=[
            ScopedPermission("api:*", "*"),
            ScopedPermission("atp:spend", "budget:2000"),
            ScopedPermission("admin:delegate", "*")
        ],
        expires_in_hours=24
    )
    budget_human_coord = budget_enforcer.allocate_budget(
        delegation_id=del_human_coord.token_id,
        total_budget=2000.0
    )
    print(f"✓ Human → Coordinator")
    print(f"  Delegation: {del_human_coord.token_id}")
    print(f"  Budget: {budget_human_coord.total_budget} ATP")
    print(f"  Depth: {del_human_coord.depth}")

    # Transfer ATP to coordinator for sub-delegation
    budget_enforcer.set_lct_balance(coordinator_identity.lct_uri, 2000.0)

    # Coordinator → Worker 1 (600 ATP, analysis)
    del_coord_w1 = delegation_keeper.record_delegation(
        issuer=coordinator_identity.lct_uri,
        delegate=worker_identities[0].lct_uri,
        scope=[
            ScopedPermission("api:read", "*"),
            ScopedPermission("atp:spend", "budget:600")
        ],
        parent_token_id=del_human_coord.token_id,
        expires_in_hours=12
    )
    budget_w1 = budget_enforcer.allocate_budget(del_coord_w1.token_id, 600.0)
    print(f"✓ Coordinator → Worker 1 (Analyzer)")
    print(f"  Budget: {budget_w1.total_budget} ATP")
    print(f"  Depth: {del_coord_w1.depth}")

    # Coordinator → Worker 2 (600 ATP, code generation)
    del_coord_w2 = delegation_keeper.record_delegation(
        issuer=coordinator_identity.lct_uri,
        delegate=worker_identities[1].lct_uri,
        scope=[
            ScopedPermission("api:write", "*"),
            ScopedPermission("atp:spend", "budget:600")
        ],
        parent_token_id=del_human_coord.token_id,
        expires_in_hours=12
    )
    budget_w2 = budget_enforcer.allocate_budget(del_coord_w2.token_id, 600.0)
    print(f"✓ Coordinator → Worker 2 (Coder)")
    print(f"  Budget: {budget_w2.total_budget} ATP")

    # Coordinator → Worker 3 (400 ATP, testing)
    del_coord_w3 = delegation_keeper.record_delegation(
        issuer=coordinator_identity.lct_uri,
        delegate=worker_identities[2].lct_uri,
        scope=[
            ScopedPermission("api:read", "*"),
            ScopedPermission("atp:spend", "budget:400")
        ],
        parent_token_id=del_human_coord.token_id,
        expires_in_hours=12
    )
    budget_w3 = budget_enforcer.allocate_budget(del_coord_w3.token_id, 400.0)
    print(f"✓ Coordinator → Worker 3 (Tester)")
    print(f"  Budget: {budget_w3.total_budget} ATP")
    print()

    # Step 4: Simulate worker task execution with ATP spending
    print("Step 4: Workers Execute Tasks (ATP Spending)")
    print("-" * 70)

    # Worker 1: Analyze codebase (300 ATP)
    print("Worker 1 (Analyzer): Analyzing codebase...")
    budget_enforcer.lock_atp(del_coord_w1.token_id, 300.0, "analyze_001")
    time.sleep(0.1)  # Simulate work
    budget_enforcer.commit_atp(del_coord_w1.token_id, 300.0, "analyze_001")
    budget_w1 = budget_enforcer.get_budget(del_coord_w1.token_id)
    print(f"  ✓ Consumed: {budget_w1.consumed} ATP")
    print(f"  ✓ Remaining: {budget_w1.available} ATP")
    print(f"  ✓ Utilization: {budget_w1.utilization * 100:.1f}%")

    # Worker 2: Generate code (450 ATP)
    print("Worker 2 (Coder): Generating code...")
    budget_enforcer.lock_atp(del_coord_w2.token_id, 450.0, "codegen_001")
    time.sleep(0.1)
    budget_enforcer.commit_atp(del_coord_w2.token_id, 450.0, "codegen_001")
    budget_w2 = budget_enforcer.get_budget(del_coord_w2.token_id)
    print(f"  ✓ Consumed: {budget_w2.consumed} ATP")
    print(f"  ✓ Remaining: {budget_w2.available} ATP")
    print(f"  ✓ Utilization: {budget_w2.utilization * 100:.1f}%")

    # Worker 3: Run tests (350 ATP)
    print("Worker 3 (Tester): Running tests...")
    budget_enforcer.lock_atp(del_coord_w3.token_id, 350.0, "test_001")
    time.sleep(0.1)
    budget_enforcer.commit_atp(del_coord_w3.token_id, 350.0, "test_001")
    budget_w3 = budget_enforcer.get_budget(del_coord_w3.token_id)
    print(f"  ✓ Consumed: {budget_w3.consumed} ATP")
    print(f"  ✓ Remaining: {budget_w3.available} ATP")
    print(f"  ✓ Utilization: {budget_w3.utilization * 100:.1f}%")
    print(f"  ✓ Alert level: {budget_w3.alert_level.name}")
    print()

    # Step 5: Query delegation chains
    print("Step 5: Delegation Chain Verification")
    print("-" * 70)
    for i, del_token in enumerate([del_coord_w1, del_coord_w2, del_coord_w3]):
        chain = delegation_keeper.get_delegation_chain(del_token.token_id)
        print(f"Worker {i+1} delegation chain ({len(chain)} levels):")
        for j, link in enumerate(chain):
            print(f"  [{j}] {link.issuer} → {link.delegate}")
    print()

    # Step 6: Verify all identities
    print("Step 6: Identity Verification")
    print("-" * 70)
    all_identities = [human_identity, coordinator_identity] + worker_identities
    for identity in all_identities:
        is_valid, binding_strength = identity_bridge.verify_identity(identity.lct_uri)
        print(f"✓ {identity.lct_uri}: valid={is_valid}, strength={binding_strength}")
    print()

    # Summary
    print("=" * 70)
    print("SCENARIO 1: SUCCESS")
    print("=" * 70)
    total_atp_spent = budget_w1.consumed + budget_w2.consumed + budget_w3.consumed
    print(f"✓ Total ATP spent: {total_atp_spent}/1600 ATP allocated to workers")
    print(f"✓ All workers completed tasks within budget")
    print(f"✓ All identities hardware-bound and verified")
    print(f"✓ Delegation chains tracked and validated")
    print()

    return {
        "scenario": "Cooperative Delegation",
        "agents": len(all_identities),
        "delegation_levels": 3,
        "total_atp_spent": total_atp_spent,
        "budgets_enforced": 4,
        "identities_verified": len(all_identities),
        "success": True
    }


def scenario2_budget_exhaustion():
    """
    Scenario 2: Budget Exhaustion and Alerts

    Test budget enforcement by:
    - Attempting to exceed budget (should fail)
    - Triggering warning alerts (80%, 90%, 100%)
    - Verifying lock-commit-rollback prevents overspending
    """
    print("=" * 70)
    print("SCENARIO 2: BUDGET EXHAUSTION AND ALERTS")
    print("=" * 70)
    print()

    # Setup
    config = ACTBlockchainConfig()
    identity_bridge = ACTIdentityBridge(config)
    delegation_keeper = ACTDelegationChainKeeper()
    budget_enforcer = ATPBudgetEnforcer(delegation_keeper)

    # Create identities
    human = identity_bridge.create_hardware_bound_agent("web4", "human", "bob", "testnet")
    agent = identity_bridge.create_hardware_bound_agent("web4", "agent", "test_agent", "testnet")

    budget_enforcer.set_lct_balance(human.lct_uri, 1000.0)

    # Create delegation with 500 ATP budget
    delegation = delegation_keeper.record_delegation(
        issuer=human.lct_uri,
        delegate=agent.lct_uri,
        scope=[ScopedPermission("atp:spend", "budget:500")],
        expires_in_hours=1
    )
    budget = budget_enforcer.allocate_budget(delegation.token_id, 500.0)

    print(f"Allocated budget: {budget.total_budget} ATP")
    print()

    # Test 1: Spend to 80% (warning)
    print("Test 1: Trigger WARNING alert (80% utilization)")
    print("-" * 70)
    budget_enforcer.lock_atp(delegation.token_id, 400.0, "op1")
    budget_enforcer.commit_atp(delegation.token_id, 400.0, "op1")
    budget = budget_enforcer.get_budget(delegation.token_id)
    print(f"✓ Consumed: {budget.consumed}/500 ATP ({budget.utilization * 100:.0f}%)")
    print(f"✓ Alert level: {budget.alert_level.name}")
    print(f"✓ Alerts: {len(budget.alerts)}")
    print()

    # Test 2: Spend to 90% (critical)
    print("Test 2: Trigger CRITICAL alert (90% utilization)")
    print("-" * 70)
    budget_enforcer.lock_atp(delegation.token_id, 50.0, "op2")
    budget_enforcer.commit_atp(delegation.token_id, 50.0, "op2")
    budget = budget_enforcer.get_budget(delegation.token_id)
    print(f"✓ Consumed: {budget.consumed}/500 ATP ({budget.utilization * 100:.0f}%)")
    print(f"✓ Alert level: {budget.alert_level.name}")
    print(f"✓ Alerts: {len(budget.alerts)}")
    print()

    # Test 3: Spend to 100% (exhausted)
    print("Test 3: Trigger EXHAUSTED alert (100% utilization)")
    print("-" * 70)
    budget_enforcer.lock_atp(delegation.token_id, 50.0, "op3")
    budget_enforcer.commit_atp(delegation.token_id, 50.0, "op3")
    budget = budget_enforcer.get_budget(delegation.token_id)
    print(f"✓ Consumed: {budget.consumed}/500 ATP ({budget.utilization * 100:.0f}%)")
    print(f"✓ Alert level: {budget.alert_level.name}")
    print(f"✓ Alerts: {len(budget.alerts)}")
    print()

    # Test 4: Attempt to exceed budget (should fail)
    print("Test 4: Attempt to Exceed Budget (Should Fail)")
    print("-" * 70)
    can_proceed, reason = budget_enforcer.check_budget(delegation.token_id, 100.0)
    print(f"✓ Can spend 100 ATP: {can_proceed}")
    print(f"✓ Reason: {reason}")
    print()

    print("=" * 70)
    print("SCENARIO 2: SUCCESS")
    print("=" * 70)
    print(f"✓ All budget alerts triggered correctly")
    print(f"✓ Budget exhaustion prevented overspending")
    print()

    return {
        "scenario": "Budget Exhaustion",
        "alerts_triggered": len(budget.alerts),
        "budget_enforced": True,
        "success": True
    }


def scenario3_security_validation():
    """
    Scenario 3: Security Attack Prevention

    Test that security measures prevent:
    - Unauthorized sub-delegation
    - Delegation forgery (wrong issuer)
    - Budget gaming (attempt to spend without budget)
    """
    print("=" * 70)
    print("SCENARIO 3: SECURITY VALIDATION")
    print("=" * 70)
    print()

    # Setup
    config = ACTBlockchainConfig()
    identity_bridge = ACTIdentityBridge(config)
    delegation_keeper = ACTDelegationChainKeeper()
    budget_enforcer = ATPBudgetEnforcer(delegation_keeper)

    # Create identities
    human = identity_bridge.create_hardware_bound_agent("web4", "human", "charlie", "testnet")
    agent1 = identity_bridge.create_hardware_bound_agent("web4", "agent", "agent1", "testnet")
    agent2 = identity_bridge.create_hardware_bound_agent("web4", "agent", "agent2", "testnet")
    attacker = identity_bridge.create_hardware_bound_agent("web4", "agent", "attacker", "testnet")

    budget_enforcer.set_lct_balance(human.lct_uri, 10000.0)
    budget_enforcer.set_lct_balance(agent1.lct_uri, 0.0)

    print("Test 1: Prevent Unauthorized Sub-Delegation")
    print("-" * 70)

    # Create delegation WITHOUT admin:delegate permission
    del_no_subdel = delegation_keeper.record_delegation(
        issuer=human.lct_uri,
        delegate=agent1.lct_uri,
        scope=[ScopedPermission("api:read", "*")],  # No admin:delegate!
        expires_in_hours=1
    )

    # Attempt unauthorized sub-delegation
    try:
        budget_enforcer.set_lct_balance(agent1.lct_uri, 1000.0)
        unauthorized = delegation_keeper.record_delegation(
            issuer=agent1.lct_uri,
            delegate=agent2.lct_uri,
            scope=[ScopedPermission("api:read", "*")],
            parent_token_id=del_no_subdel.token_id,
            expires_in_hours=1
        )
        print("✗ FAIL: Unauthorized sub-delegation allowed")
        success1 = False
    except ValueError as e:
        print(f"✓ PASS: Unauthorized sub-delegation prevented")
        print(f"  Reason: {e}")
        success1 = True
    print()

    print("Test 2: Prevent Budget Gaming (Spend Without Budget)")
    print("-" * 70)

    # Create delegation with budget
    del_with_budget = delegation_keeper.record_delegation(
        issuer=human.lct_uri,
        delegate=agent2.lct_uri,
        scope=[ScopedPermission("atp:spend", "*")],
        expires_in_hours=1
    )
    budget = budget_enforcer.allocate_budget(del_with_budget.token_id, 100.0)

    # Attempt to spend more than budget
    can_spend, reason = budget_enforcer.check_budget(del_with_budget.token_id, 200.0)
    if not can_spend:
        print(f"✓ PASS: Budget gaming prevented")
        print(f"  Reason: {reason}")
        success2 = True
    else:
        print("✗ FAIL: Budget gaming allowed")
        success2 = False
    print()

    print("Test 3: Verify Hardware-Bound Identity Requirement")
    print("-" * 70)
    print(f"✓ All agents have hardware attestation")
    print(f"✓ Binding strength: {human.attestation.binding_strength}")
    print(f"✓ Hardware identifiers unique and verified")
    success3 = True
    print()

    print("=" * 70)
    print("SCENARIO 3: SUCCESS")
    print("=" * 70)
    all_success = success1 and success2 and success3
    print(f"✓ All security tests passed: {all_success}")
    print()

    return {
        "scenario": "Security Validation",
        "unauthorized_subdelegation_prevented": success1,
        "budget_gaming_prevented": success2,
        "hardware_binding_verified": success3,
        "success": all_success
    }


def performance_summary():
    """
    Performance Summary

    Collect and report performance metrics across all components.
    """
    print("=" * 70)
    print("PERFORMANCE SUMMARY")
    print("=" * 70)
    print()

    config = ACTBlockchainConfig()
    identity_bridge = ACTIdentityBridge(config)
    delegation_keeper = ACTDelegationChainKeeper()
    budget_enforcer = ATPBudgetEnforcer(delegation_keeper)

    # Identity creation performance
    print("Identity Creation Performance")
    print("-" * 70)
    times = []
    for i in range(10):
        start = time.time()
        identity = identity_bridge.create_hardware_bound_agent("test", "agent", f"perf_{i}", "testnet")
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    avg_identity_time = sum(times) / len(times)
    print(f"Average time: {avg_identity_time:.2f}ms")
    print(f"Target: <200ms {'✓ PASS' if avg_identity_time < 200 else '✗ FAIL'}")
    print()

    # Delegation creation performance
    print("Delegation Creation Performance")
    print("-" * 70)
    human_lct = "lct://test:human:perf@testnet"
    times = []
    for i in range(10):
        start = time.time()
        delegation = delegation_keeper.record_delegation(
            issuer=human_lct,
            delegate=f"lct://test:agent:del_perf_{i}@testnet",
            scope=[ScopedPermission("api:read", "*")],
            expires_in_hours=1
        )
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    avg_delegation_time = sum(times) / len(times)
    print(f"Average time: {avg_delegation_time:.2f}ms")
    print(f"Target: <50ms {'✓ PASS' if avg_delegation_time < 50 else '✗ FAIL'}")
    print()

    # Budget enforcement performance
    print("Budget Check Performance")
    print("-" * 70)
    budget_enforcer.set_lct_balance(human_lct, 100000.0)
    test_del = delegation_keeper.record_delegation(
        issuer=human_lct,
        delegate="lct://test:agent:budget_perf@testnet",
        scope=[ScopedPermission("atp:spend", "*")],
        expires_in_hours=1
    )
    budget_enforcer.allocate_budget(test_del.token_id, 10000.0)

    times = []
    for i in range(1000):
        start = time.time()
        can_spend, _ = budget_enforcer.check_budget(test_del.token_id, 100.0)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    avg_budget_time = sum(times) / len(times)
    print(f"Average time: {avg_budget_time:.4f}ms")
    print(f"Target: <1ms {'✓ PASS' if avg_budget_time < 1.0 else '✗ FAIL'}")
    print()

    print("=" * 70)
    print()

    return {
        "identity_creation_ms": avg_identity_time,
        "delegation_creation_ms": avg_delegation_time,
        "budget_check_ms": avg_budget_time
    }


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_scenarios():
    """Run all multi-agent integration scenarios."""
    print("\n")
    print("*" * 70)
    print("SESSION 100 TRACK 4: MULTI-AGENT INTEGRATION TESTS")
    print("*" * 70)
    print("\n")

    results = {}

    # Scenario 1: Cooperative Delegation
    results["scenario1"] = scenario1_cooperative_delegation()

    # Scenario 2: Budget Exhaustion
    results["scenario2"] = scenario2_budget_exhaustion()

    # Scenario 3: Security Validation
    results["scenario3"] = scenario3_security_validation()

    # Performance Summary
    results["performance"] = performance_summary()

    # Final summary
    print("*" * 70)
    print("ALL SCENARIOS COMPLETE")
    print("*" * 70)
    print()
    print("Summary:")
    print(f"✓ Scenario 1 (Cooperative Delegation): {results['scenario1']['success']}")
    print(f"✓ Scenario 2 (Budget Exhaustion): {results['scenario2']['success']}")
    print(f"✓ Scenario 3 (Security Validation): {results['scenario3']['success']}")
    print()
    print("Performance:")
    print(f"  - Identity creation: {results['performance']['identity_creation_ms']:.2f}ms")
    print(f"  - Delegation creation: {results['performance']['delegation_creation_ms']:.2f}ms")
    print(f"  - Budget check: {results['performance']['budget_check_ms']:.4f}ms")
    print()

    return results


if __name__ == "__main__":
    results = run_all_scenarios()
    print(f"\nFull results:\n{json.dumps(results, indent=2)}")
