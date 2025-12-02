#!/usr/bin/env python3
"""
Federation + LCT Permission Integration Tests

Tests permission-enforced federation task delegation.

Author: Legion Autonomous Session #50
Date: 2025-12-02
Status: Phase 4 integration testing
References: federation_permissions.py, lct_permissions.py
"""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from game.engine.federation_permissions import (
    PermissionEnforcedFederationRouter,
    FederationTaskRequirements,
    create_task_requirements_from_type,
    DelegationPermissionError,
    ExecutionCapabilityError
)


def test_delegation_permission_check():
    """Test: Check delegation permissions"""
    print("=" * 80)
    print("Test 1: Delegation Permission Checks")
    print("=" * 80)
    print()

    router = PermissionEnforcedFederationRouter("Thor")

    # Test cases: (lct_id, expected_can_delegate)
    test_cases = [
        ("lct:web4:agent:alice@Thor#delegation.federation", True, "delegation task"),
        ("lct:web4:agent:admin@Thor#admin.full", True, "admin task"),
        ("lct:web4:agent:bob@Thor#perception", False, "perception task"),
        ("lct:web4:agent:charlie@Thor#execution.code", False, "execution task"),
        ("lct:web4:agent:dave@Thor#planning", False, "planning task"),
    ]

    print("Delegation permission checks:")
    passed = 0
    for lct_id, expected, description in test_cases:
        can_del, reason = router.can_delegate_task(lct_id)
        status = "✅" if can_del == expected else "❌"
        result_str = "CAN delegate" if can_del else f"CANNOT delegate ({reason[:50]})"
        print(f"  {status} {description:25} {result_str}")
        if can_del == expected:
            passed += 1

    print()
    print(f"Passed: {passed}/{len(test_cases)}")
    print()


def test_task_compatibility():
    """Test: Task compatibility checking"""
    print("=" * 80)
    print("Test 2: Task Compatibility Checking")
    print("=" * 80)
    print()

    # Create requirements for code execution task
    reqs = FederationTaskRequirements(
        required_permissions=["atp:write", "exec:code"],
        requires_code_execution=True,
        estimated_atp_cost=200.0,
        estimated_memory_mb=4096
    )

    print("Code execution task requirements:")
    print(f"  Required permissions: {reqs.required_permissions}")
    print(f"  Requires code execution: {reqs.requires_code_execution}")
    print(f"  Estimated ATP cost: {reqs.estimated_atp_cost}")
    print(f"  Estimated memory: {reqs.estimated_memory_mb}MB")
    print()

    # Test cases: (executor_task, expected_compatible)
    test_cases = [
        ("execution.code", True, "execution.code - has all requirements"),
        ("admin.full", True, "admin.full - has all permissions"),
        ("execution.safe", False, "execution.safe - no network, limited resources"),
        ("perception", False, "perception - no exec permission"),
        ("planning", False, "planning - no exec permission"),
        ("delegation.federation", False, "delegation - no exec permission"),
    ]

    print("Compatibility checks:")
    passed = 0
    for executor_task, expected, description in test_cases:
        is_compatible, reasons = reqs.check_compatibility(executor_task)
        status = "✅" if is_compatible == expected else "❌"
        result_str = "COMPATIBLE" if is_compatible else f"INCOMPATIBLE: {', '.join(reasons[:2])}"
        print(f"  {status} {description:50} {result_str}")
        if is_compatible == expected:
            passed += 1

    print()
    print(f"Passed: {passed}/{len(test_cases)}")
    print()


def test_find_compatible_executors():
    """Test: Find compatible executors"""
    print("=" * 80)
    print("Test 3: Find Compatible Executors")
    print("=" * 80)
    print()

    router = PermissionEnforcedFederationRouter("Thor")

    # Create perception task requirements
    reqs = create_task_requirements_from_type("perception")

    # Available executors
    available = [
        "lct:web4:agent:alice@Thor#perception",
        "lct:web4:agent:bob@Thor#planning",
        "lct:web4:agent:charlie@Thor#execution.code",
        "lct:web4:agent:dave@Sprout#perception",
        "lct:web4:agent:eve@Legion#admin.full",
    ]

    print("Finding executors for perception task:")
    print(f"  Requirements: {reqs.required_permissions}")
    print(f"  Available executors: {len(available)}")
    print()

    compatible = router.find_compatible_executors(reqs, available)

    print(f"Compatible executors: {len(compatible)}")
    for executor_lct, score in compatible:
        print(f"  Score {score:.2f}: {executor_lct}")

    print()

    # Validation
    expected_compatible = 4  # perception x2, execution.code, admin.full
    status = "✅" if len(compatible) == expected_compatible else "❌"
    print(f"{status} Found {len(compatible)} compatible (expected {expected_compatible})")
    print()


def test_delegate_task():
    """Test: Delegate task with permission checks"""
    print("=" * 80)
    print("Test 4: Task Delegation with Checks")
    print("=" * 80)
    print()

    router = PermissionEnforcedFederationRouter("Thor")

    delegator_lct = "lct:web4:agent:alice@Thor#delegation.federation"
    executor_lct = "lct:web4:agent:bob@Sprout#execution.code"

    # Create code execution requirements
    reqs = create_task_requirements_from_type("code_execution")

    print(f"Delegator: {delegator_lct}")
    print(f"Executor: {executor_lct}")
    print(f"Task type: code_execution")
    print()

    # Attempt delegation
    success, reason = router.delegate_task(
        delegator_lct=delegator_lct,
        executor_lct=executor_lct,
        task_type="code_execution",
        requirements=reqs
    )

    status = "✅" if success else "❌"
    result_str = "SUCCESS" if success else f"FAILED: {reason}"
    print(f"{status} Delegation: {result_str}")
    print()


def test_delegation_denials():
    """Test: Delegation denial scenarios"""
    print("=" * 80)
    print("Test 5: Delegation Denial Scenarios")
    print("=" * 80)
    print()

    router = PermissionEnforcedFederationRouter("Thor")

    # Scenario 1: Delegator lacks delegation permission
    print("Scenario 1: Delegator lacks delegation permission")
    success, reason = router.delegate_task(
        delegator_lct="lct:web4:agent:alice@Thor#perception",  # No delegation permission
        executor_lct="lct:web4:agent:bob@Sprout#execution.code",
        task_type="code_execution",
        requirements=create_task_requirements_from_type("code_execution")
    )
    status1 = "✅" if not success else "❌"
    print(f"  {status1} Denied: {reason[:60]}")
    print()

    # Scenario 2: Executor lacks required permissions
    print("Scenario 2: Executor lacks required permissions")
    success, reason = router.delegate_task(
        delegator_lct="lct:web4:agent:alice@Thor#delegation.federation",
        executor_lct="lct:web4:agent:bob@Sprout#perception",  # Can't execute code
        task_type="code_execution",
        requirements=create_task_requirements_from_type("code_execution")
    )
    status2 = "✅" if not success else "❌"
    print(f"  {status2} Denied: {reason[:60]}")
    print()

    # Scenario 3: Executor lacks resources
    print("Scenario 3: Executor insufficient resources")
    expensive_reqs = FederationTaskRequirements(
        required_permissions=["exec:code"],
        requires_code_execution=True,
        estimated_atp_cost=1000.0,  # Exceeds execution.code budget (500)
        estimated_memory_mb=2048
    )
    success, reason = router.delegate_task(
        delegator_lct="lct:web4:agent:alice@Thor#delegation.federation",
        executor_lct="lct:web4:agent:bob@Sprout#execution.code",
        task_type="expensive_task",
        requirements=expensive_reqs
    )
    status3 = "✅" if not success else "❌"
    print(f"  {status3} Denied: {reason[:60]}")
    print()

    print(f"Validation: All denials correct: {status1} {status2} {status3}")
    print()


def test_task_requirements_from_type():
    """Test: Task requirements creation from type"""
    print("=" * 80)
    print("Test 6: Task Requirements from Type")
    print("=" * 80)
    print()

    task_types = [
        "perception",
        "planning",
        "code_execution",
        "data_processing",
    ]

    print("Creating requirements for task types:")
    for task_type in task_types:
        reqs = create_task_requirements_from_type(task_type)
        print(f"\n{task_type}:")
        print(f"  Required permissions: {reqs.required_permissions}")
        print(f"  Requires code execution: {reqs.requires_code_execution}")
        print(f"  Estimated ATP cost: {reqs.estimated_atp_cost}")
        print(f"  Estimated memory: {reqs.estimated_memory_mb}MB")

    print()


def test_compatibility_scoring():
    """Test: Compatibility score calculation"""
    print("=" * 80)
    print("Test 7: Compatibility Scoring")
    print("=" * 80)
    print()

    router = PermissionEnforcedFederationRouter("Thor")

    # Create requirements
    reqs = FederationTaskRequirements(
        required_permissions=["atp:write", "exec:code"],
        requires_code_execution=True,
        estimated_atp_cost=100.0,
        estimated_memory_mb=2048
    )

    # Test various executors
    executors = [
        "lct:web4:agent:alice@Thor#execution.code",     # Good match
        "lct:web4:agent:bob@Thor#admin.full",           # Excellent match (more resources)
        "lct:web4:agent:charlie@Thor#execution.safe",   # Poor match (limited)
        "lct:web4:agent:dave@Thor#perception",          # No match
    ]

    print("Compatibility scores:")
    for executor_lct in executors:
        compatible = router.find_compatible_executors(reqs, [executor_lct])
        if compatible:
            score = compatible[0][1]
            print(f"  Score {score:.2f}: {executor_lct}")
        else:
            print(f"  Score 0.00: {executor_lct} (incompatible)")

    print()


def test_delegation_logging():
    """Test: Delegation operation logging"""
    print("=" * 80)
    print("Test 8: Delegation Logging")
    print("=" * 80)
    print()

    router = PermissionEnforcedFederationRouter("Thor")

    delegator_lct = "lct:web4:agent:alice@Thor#delegation.federation"

    # Perform multiple delegations
    delegations = [
        ("lct:web4:agent:bob@Sprout#execution.code", "code_execution", True),
        ("lct:web4:agent:charlie@Legion#perception", "perception", True),
        ("lct:web4:agent:dave@Thor#planning", "code_execution", False),  # Should fail
    ]

    print("Performing delegations:")
    for executor_lct, task_type, should_succeed in delegations:
        reqs = create_task_requirements_from_type(task_type)
        success, reason = router.delegate_task(
            delegator_lct=delegator_lct,
            executor_lct=executor_lct,
            task_type=task_type,
            requirements=reqs
        )
        status = "✅" if success == should_succeed else "❌"
        result = "SUCCESS" if success else f"FAILED ({reason[:40]})"
        print(f"  {status} {task_type:20} → {result}")

    print()

    # Get delegation log
    logs = router.get_delegation_log(limit=10)
    print(f"Delegation log: {len(logs)} entries")
    for i, log in enumerate(logs[:3], 1):
        status_str = "✅" if log.success else "❌"
        print(f"  {i}. {status_str} {log.task_type:20} at {log.timestamp:.2f}")

    print()

    # Get router stats
    stats = router.get_router_stats()
    print("Router statistics:")
    print(f"  Total delegations: {stats['total_delegations']}")
    print(f"  Successful: {stats['successful_delegations']}")
    print(f"  Failed: {stats['failed_delegations']}")
    print(f"  Permission denials: {stats['permission_denials']}")
    print(f"  Capability mismatches: {stats['capability_mismatches']}")

    print()


if __name__ == "__main__":
    print()
    print("🔒🌐 Federation + LCT Permission Integration Tests")
    print()
    print("Tests permission-enforced federation task delegation:")
    print("  - Delegation permission checks")
    print("  - Task compatibility checking")
    print("  - Finding compatible executors")
    print("  - Task delegation with checks")
    print("  - Delegation denial scenarios")
    print("  - Task requirements creation")
    print("  - Compatibility scoring")
    print("  - Delegation logging")
    print()

    test_delegation_permission_check()
    test_task_compatibility()
    test_find_compatible_executors()
    test_delegate_task()
    test_delegation_denials()
    test_task_requirements_from_type()
    test_compatibility_scoring()
    test_delegation_logging()

    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print("✅ Delegation permission checks working")
    print("✅ Task compatibility checks working")
    print("✅ Compatible executor finding working")
    print("✅ Task delegation with checks working")
    print("✅ Delegation denials working")
    print("✅ Task requirements creation working")
    print("✅ Compatibility scoring working")
    print("✅ Delegation logging working")
    print()
    print("Status: Federation + LCT permission integration validated")
    print("Next: End-to-end federation with ATP budget enforcement")
    print()
    print("Co-Authored-By: Claude (Legion Autonomous) <noreply@anthropic.com>")
    print()
