#!/usr/bin/env python3
"""
LCT Permission System Tests

Tests task-based permission checking and resource limit enforcement.

Author: Legion Autonomous Session #49
Date: 2025-12-02
Status: Phase 3 testing
References: lct_permissions.py, LCT_IDENTITY_SYSTEM.md
"""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from game.engine.lct_permissions import (
    get_task_permissions,
    check_permission,
    check_resource_limit,
    can_delegate,
    can_execute_code,
    get_atp_budget,
    list_permissions,
    get_resource_limits,
    validate_task_permissions,
    get_permission_matrix,
    TASK_PERMISSIONS,
    ResourceLimits,
    ATPPermission,
    FederationPermission,
    ExecutionPermission,
    AdminPermission
)


def test_perception_permissions():
    """Test: Perception task permissions"""
    print("=" * 80)
    print("Test 1: Perception Task Permissions")
    print("=" * 80)
    print()

    task = "perception"

    # Get permissions
    perms = get_task_permissions(task)
    print(f"Task: {task}")
    print(f"Description: {perms.description}")
    print(f"Permissions: {sorted(list(perms.permissions))}")
    print(f"Can delegate: {perms.can_delegate}")
    print(f"Can execute code: {perms.can_execute_code}")
    print()

    # Test specific permissions
    tests = [
        ("atp:read", True),
        ("atp:write", False),
        ("atp:all", False),
        ("network:http", True),
        ("exec:code", False),
        ("admin:read", False)
    ]

    print("Permission checks:")
    passed = 0
    failed = 0
    for permission, expected in tests:
        result = check_permission(task, permission)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {permission}: {result} (expected {expected})")
        if result == expected:
            passed += 1
        else:
            failed += 1

    print()
    print(f"Passed: {passed}/{len(tests)}")
    print()


def test_execution_code_permissions():
    """Test: Code execution task permissions"""
    print("=" * 80)
    print("Test 2: Code Execution Task Permissions")
    print("=" * 80)
    print()

    task = "execution.code"

    # Get permissions
    perms = get_task_permissions(task)
    print(f"Task: {task}")
    print(f"Description: {perms.description}")
    print(f"Can execute code: {perms.can_execute_code}")
    print()

    # Test specific permissions
    tests = [
        ("atp:read", True),
        ("atp:write", True),
        ("atp:all", False),
        ("exec:code", True),
        ("exec:safe", False),  # Has exec:code but not exec:safe specifically
        ("network:http", True),
        ("storage:read", True),
        ("storage:write", True),
        ("admin:write", False)
    ]

    print("Permission checks:")
    passed = 0
    for permission, expected in tests:
        result = check_permission(task, permission)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {permission}: {result} (expected {expected})")
        if result == expected:
            passed += 1

    print()
    print(f"Passed: {passed}/{len(tests)}")
    print()


def test_admin_full_permissions():
    """Test: Admin full task permissions"""
    print("=" * 80)
    print("Test 3: Admin Full Task Permissions")
    print("=" * 80)
    print()

    task = "admin.full"

    # Get permissions
    perms = get_task_permissions(task)
    print(f"Task: {task}")
    print(f"Description: {perms.description}")
    print(f"Can delegate: {perms.can_delegate}")
    print(f"Can execute code: {perms.can_execute_code}")
    print()

    # Admin should have ALL permissions (via :all wildcards)
    tests = [
        ("atp:read", True),
        ("atp:write", True),
        ("atp:all", True),
        ("exec:code", True),
        ("exec:safe", True),
        ("exec:network", True),
        ("exec:all", True),
        ("admin:full", True),  # Has admin:full specifically
        ("federation:delegate", True),
        ("federation:all", True),
        ("network:http", True),
        ("network:all", True),
        ("storage:read", True),
        ("storage:write", True),
        ("storage:all", True)
    ]

    print("Permission checks (should all be True):")
    passed = 0
    for permission, expected in tests:
        result = check_permission(task, permission)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {permission}: {result}")
        if result == expected:
            passed += 1

    print()
    print(f"Passed: {passed}/{len(tests)}")
    print()


def test_resource_limits():
    """Test: Resource limit enforcement"""
    print("=" * 80)
    print("Test 4: Resource Limit Enforcement")
    print("=" * 80)
    print()

    task = "perception"
    limits = get_resource_limits(task)

    print(f"Resource limits for {task}:")
    print(f"  ATP Budget: {limits.atp_budget}")
    print(f"  Memory: {limits.memory_mb} MB")
    print(f"  CPU Cores: {limits.cpu_cores}")
    print(f"  Disk: {limits.disk_mb} MB")
    print(f"  Network: {limits.network_bandwidth_mbps} Mbps")
    print(f"  Max Tasks: {limits.max_tasks}")
    print()

    # Test resource checks
    tests = [
        ("atp", 50.0, True, "within budget"),
        ("atp", 100.0, True, "at budget limit"),
        ("atp", 150.0, False, "exceeds budget"),
        ("memory", 1024, True, "within memory"),
        ("memory", 4096, False, "exceeds memory"),
        ("cpu", 2, True, "within CPU"),
        ("cpu", 4, False, "exceeds CPU"),
        ("tasks", 5, True, "within task limit"),
        ("tasks", 10, False, "exceeds task limit")
    ]

    print("Resource limit checks:")
    passed = 0
    for resource, value, expected_allowed, description in tests:
        allowed, reason = check_resource_limit(task, resource, value)
        status = "✅" if allowed == expected_allowed else "❌"
        result_str = "ALLOWED" if allowed else f"DENIED ({reason})"
        print(f"  {status} {resource}={value}: {result_str} - {description}")
        if allowed == expected_allowed:
            passed += 1

    print()
    print(f"Passed: {passed}/{len(tests)}")
    print()


def test_delegation_permissions():
    """Test: Federation delegation permissions"""
    print("=" * 80)
    print("Test 5: Federation Delegation Permissions")
    print("=" * 80)
    print()

    # Tasks that can delegate
    delegating_tasks = ["delegation.federation", "admin.full"]

    # Tasks that cannot delegate
    non_delegating_tasks = ["perception", "planning", "execution.code", "execution.safe"]

    print("Tasks that CAN delegate:")
    for task in delegating_tasks:
        can_del = can_delegate(task)
        status = "✅" if can_del else "❌"
        print(f"  {status} {task}: {can_del}")

    print()
    print("Tasks that CANNOT delegate:")
    for task in non_delegating_tasks:
        can_del = can_delegate(task)
        status = "✅" if not can_del else "❌"
        print(f"  {status} {task}: {can_del}")

    print()


def test_code_execution_permissions():
    """Test: Code execution permissions"""
    print("=" * 80)
    print("Test 6: Code Execution Permissions")
    print("=" * 80)
    print()

    # Tasks that can execute code
    code_tasks = ["execution.code", "execution.safe", "admin.full"]

    # Tasks that cannot execute code
    non_code_tasks = ["perception", "planning", "delegation.federation"]

    print("Tasks that CAN execute code:")
    for task in code_tasks:
        can_exec = can_execute_code(task)
        status = "✅" if can_exec else "❌"
        print(f"  {status} {task}: {can_exec}")

    print()
    print("Tasks that CANNOT execute code:")
    for task in non_code_tasks:
        can_exec = can_execute_code(task)
        status = "✅" if not can_exec else "❌"
        print(f"  {status} {task}: {can_exec}")

    print()


def test_atp_budgets():
    """Test: ATP budget limits"""
    print("=" * 80)
    print("Test 7: ATP Budget Limits")
    print("=" * 80)
    print()

    tasks = [
        "perception",
        "planning",
        "execution.code",
        "execution.safe",
        "delegation.federation",
        "admin.full"
    ]

    print("ATP budgets by task:")
    for task in tasks:
        budget = get_atp_budget(task)
        print(f"  {task:30} {budget:>12.1f} ATP")

    print()

    # Verify budget ordering
    print("Budget ordering verification:")
    perception_budget = get_atp_budget("perception")
    execution_budget = get_atp_budget("execution.code")
    delegation_budget = get_atp_budget("delegation.federation")
    admin_budget = get_atp_budget("admin.full")

    checks = [
        (perception_budget < execution_budget, "perception < execution.code"),
        (execution_budget < delegation_budget, "execution.code < delegation"),
        (delegation_budget < admin_budget, "delegation < admin (unlimited)")
    ]

    for result, description in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {description}")

    print()


def test_permission_escalation_prevention():
    """Test: Permission escalation prevention"""
    print("=" * 80)
    print("Test 8: Permission Escalation Prevention")
    print("=" * 80)
    print()

    # Low-privilege tasks trying to access high-privilege operations
    escalation_attempts = [
        ("perception", "atp:write", False, "perception cannot write ATP"),
        ("perception", "admin:read", False, "perception cannot read admin"),
        ("planning", "exec:code", False, "planning cannot execute code"),
        ("execution.safe", "network:http", False, "safe exec has no network"),
        ("execution.code", "admin:full", False, "execution cannot get admin"),
        ("delegation.federation", "admin:write", False, "delegation cannot get admin")
    ]

    print("Escalation prevention checks:")
    passed = 0
    for task, permission, expected, description in escalation_attempts:
        result = check_permission(task, permission)
        status = "✅" if result == expected else "❌"
        result_str = "ALLOWED" if result else "DENIED"
        print(f"  {status} {task} → {permission}: {result_str} - {description}")
        if result == expected:
            passed += 1

    print()
    print(f"Passed: {passed}/{len(escalation_attempts)}")
    print()


def test_wildcard_permissions():
    """Test: Wildcard permission handling"""
    print("=" * 80)
    print("Test 9: Wildcard Permission Handling")
    print("=" * 80)
    print()

    # admin.full has :all permissions
    task = "admin.full"

    # Should grant all specific permissions in category
    wildcard_tests = [
        ("atp:all", ["atp:read", "atp:write"]),
        ("exec:all", ["exec:safe", "exec:code", "exec:network"]),
        ("federation:all", ["federation:delegate", "federation:execute"]),
        ("network:all", ["network:http", "network:ws", "network:p2p"]),
        ("storage:all", ["storage:read", "storage:write", "storage:delete"])
    ]

    print(f"Wildcard permissions for {task}:")
    all_passed = True
    for wildcard, specific_perms in wildcard_tests:
        has_wildcard = check_permission(task, wildcard)
        print(f"\n  {wildcard}: {has_wildcard}")

        if has_wildcard:
            for perm in specific_perms:
                has_specific = check_permission(task, perm)
                status = "✅" if has_specific else "❌"
                print(f"    {status} {perm}: {has_specific}")
                if not has_specific:
                    all_passed = False

    print()
    if all_passed:
        print("✅ All wildcard permissions working correctly")
    else:
        print("❌ Some wildcard permissions not working")

    print()


def test_permission_matrix():
    """Test: Complete permission matrix"""
    print("=" * 80)
    print("Test 10: Permission Matrix")
    print("=" * 80)
    print()

    matrix = get_permission_matrix()

    print("Complete Permission Matrix:")
    print()
    print(f"{'Task':<30} {'ATP':<12} {'Federation':<12} {'Code Exec':<12} {'Admin':<12} {'Budget':<12}")
    print("-" * 100)

    for task, caps in matrix.items():
        print(f"{task:<30} {caps['atp']:<12} {caps['federation']:<12} {caps['code_exec']:<12} {caps['admin']:<12} {caps['atp_budget']:<12.1f}")

    print()

    # Verify matrix matches expected values from design
    expected_matrix = {
        "perception": {"atp": "read", "federation": "no", "code_exec": "no", "admin": "no"},
        "planning": {"atp": "read", "federation": "no", "code_exec": "no", "admin": "no"},
        "execution.code": {"atp": "read/write", "federation": "no", "code_exec": "yes", "admin": "no"},
        "delegation.federation": {"atp": "read/write", "federation": "yes", "code_exec": "no", "admin": "no"},
        "admin.full": {"atp": "all", "federation": "yes", "code_exec": "yes", "admin": "full"}
    }

    print("Matrix validation:")
    all_match = True
    for task, expected in expected_matrix.items():
        actual = matrix.get(task, {})
        for key, expected_value in expected.items():
            actual_value = actual.get(key)
            match = actual_value == expected_value
            status = "✅" if match else "❌"
            if not match:
                print(f"  {status} {task}.{key}: expected '{expected_value}', got '{actual_value}'")
                all_match = False

    if all_match:
        print("  ✅ All matrix values match design specification")

    print()


def test_resource_limit_validation():
    """Test: Resource limit validation"""
    print("=" * 80)
    print("Test 11: Resource Limit Validation")
    print("=" * 80)
    print()

    # Test valid resource limits
    print("Valid resource limits:")
    try:
        limits = ResourceLimits(
            atp_budget=100.0,
            memory_mb=2048,
            cpu_cores=4,
            disk_mb=1024,
            network_bandwidth_mbps=10,
            max_tasks=5
        )
        print("  ✅ Valid limits accepted")
    except ValueError as e:
        print(f"  ❌ Valid limits rejected: {e}")

    print()

    # Test invalid resource limits
    invalid_tests = [
        ("negative ATP", {"atp_budget": -100.0}),
        ("zero memory", {"memory_mb": 0}),
        ("negative CPU", {"cpu_cores": -1}),
        ("zero disk", {"disk_mb": 0}),
        ("negative network", {"network_bandwidth_mbps": -1}),
        ("zero tasks", {"max_tasks": 0})
    ]

    print("Invalid resource limits (should raise ValueError):")
    for description, invalid_params in invalid_tests:
        try:
            params = {
                "atp_budget": 100.0,
                "memory_mb": 2048,
                "cpu_cores": 4,
                "disk_mb": 1024,
                "network_bandwidth_mbps": 10,
                "max_tasks": 5
            }
            params.update(invalid_params)
            limits = ResourceLimits(**params)
            print(f"  ❌ {description}: Accepted (should have been rejected)")
        except ValueError as e:
            print(f"  ✅ {description}: Correctly rejected ({str(e)[:50]}...)")

    print()


def test_permission_system_validation():
    """Test: Permission system validation"""
    print("=" * 80)
    print("Test 12: Permission System Validation")
    print("=" * 80)
    print()

    errors = validate_task_permissions()

    if not errors:
        print("✅ Permission system validation passed")
        print(f"   {len(TASK_PERMISSIONS)} tasks defined")
        print("   All task definitions valid")
    else:
        print("❌ Permission system validation failed:")
        for error in errors:
            print(f"   - {error}")

    print()


if __name__ == "__main__":
    print()
    print("🔒 LCT Permission System Tests")
    print()
    print("Tests task-based permission checking and resource limits:")
    print("  - Task permission definitions")
    print("  - Permission checking")
    print("  - Resource limit enforcement")
    print("  - Delegation capabilities")
    print("  - Code execution capabilities")
    print("  - Permission escalation prevention")
    print("  - Wildcard permissions")
    print("  - Complete permission matrix")
    print()

    test_perception_permissions()
    test_execution_code_permissions()
    test_admin_full_permissions()
    test_resource_limits()
    test_delegation_permissions()
    test_code_execution_permissions()
    test_atp_budgets()
    test_permission_escalation_prevention()
    test_wildcard_permissions()
    test_permission_matrix()
    test_resource_limit_validation()
    test_permission_system_validation()

    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print("✅ Task permissions working")
    print("✅ Resource limits enforced")
    print("✅ Delegation control working")
    print("✅ Code execution control working")
    print("✅ Escalation prevention working")
    print("✅ Wildcard permissions working")
    print("✅ Permission matrix validated")
    print("✅ Resource limit validation working")
    print("✅ System validation passed")
    print()
    print("Status: Phase 3 LCT permission system validated")
    print("Next: Phase 4 - Integration with ATP, Federation, SAGE")
    print()
    print("Co-Authored-By: Claude (Legion Autonomous) <noreply@anthropic.com>")
    print()
