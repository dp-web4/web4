#!/usr/bin/env python3
"""
SAGE + LCT Integration Tests

Tests SAGE consciousness integration with Web4 LCT identity system.
Validates cross-platform compatibility between web4 and HRM/SAGE.

Author: Legion Autonomous Session #51
Date: 2025-12-02
Status: SAGE + LCT integration validation
"""

import sys
from pathlib import Path
import time

# Add web4 root to path
_web4_root = Path(__file__).parent.parent
if str(_web4_root) not in sys.path:
    sys.path.insert(0, str(_web4_root))

from game.engine.lct_unified_permissions import (
    UNIFIED_TASK_PERMISSIONS,
    UNIFIED_RESOURCE_LIMITS,
    get_unified_atp_budget,
    is_consciousness_task,
    is_sage_task,
    check_unified_permission
)

from game.engine.sage_lct_integration import (
    SAGELCTManager,
    SAGEConsciousnessState,
    create_sage_identity_lct,
    get_sage_atp_budget,
    get_sage_resource_limits
)


def print_section(title: str):
    """Print test section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def print_test(test_name: str, passed: bool):
    """Print test result"""
    status = "✅" if passed else "❌"
    print(f"{status} {test_name}")


def test_unified_permissions():
    """Test 1: Unified Permission System"""
    print_section("Test 1: Unified Permission System")

    # Test 1: Verify 10 task types exist
    expected_tasks = [
        "perception",
        "planning",
        "planning.strategic",
        "execution.safe",
        "execution.code",
        "delegation.federation",
        "consciousness",
        "consciousness.sage",
        "admin.readonly",
        "admin.full"
    ]
    test_1 = all(task in UNIFIED_TASK_PERMISSIONS for task in expected_tasks)
    print_test(f"All 10 task types defined", test_1)

    # Test 2: Consciousness tasks have correct permissions
    consciousness_perms = UNIFIED_TASK_PERMISSIONS["consciousness"]["permissions"]
    test_2 = (
        "atp:write" in consciousness_perms and
        "federation:delegate" in consciousness_perms and
        "exec:code" in consciousness_perms
    )
    print_test("Consciousness has atp:write, federation:delegate, exec:code", test_2)

    # Test 3: Consciousness.sage has enhanced permissions
    sage_perms = UNIFIED_TASK_PERMISSIONS["consciousness.sage"]["permissions"]
    test_3 = (
        "storage:delete" in sage_perms and
        "atp:write" in sage_perms
    )
    print_test("Consciousness.sage has storage:delete", test_3)

    # Test 4: Resource limits defined for all tasks
    test_4 = all(task in UNIFIED_RESOURCE_LIMITS for task in expected_tasks)
    print_test("Resource limits defined for all 10 tasks", test_4)

    # Test 5: Consciousness.sage has enhanced resources
    sage_limits = UNIFIED_RESOURCE_LIMITS["consciousness.sage"]
    consciousness_limits = UNIFIED_RESOURCE_LIMITS["consciousness"]
    test_5 = (
        sage_limits.atp_budget > consciousness_limits.atp_budget and
        sage_limits.memory_mb > consciousness_limits.memory_mb
    )
    print_test("Consciousness.sage has enhanced resources", test_5)

    # Test 6: Helper functions work correctly
    test_6_a = is_consciousness_task("consciousness")
    test_6_b = is_consciousness_task("consciousness.sage")
    test_6_c = not is_consciousness_task("perception")
    test_6_d = is_sage_task("consciousness.sage")
    test_6_e = not is_sage_task("consciousness")
    test_6 = test_6_a and test_6_b and test_6_c and test_6_d and test_6_e
    print_test("Helper functions (is_consciousness_task, is_sage_task)", test_6)

    all_passed = all([test_1, test_2, test_3, test_4, test_5, test_6])
    print(f"\nTest 1: {'PASS' if all_passed else 'FAIL'}")
    return all_passed


def test_sage_identity_creation():
    """Test 2: SAGE Identity Creation"""
    print_section("Test 2: SAGE Identity Creation")

    manager = SAGELCTManager("Thor")

    # Test 1: Create standard consciousness identity
    identity1, state1 = manager.create_sage_identity("dp", use_enhanced_sage=False)
    test_1 = (
        identity1.task.task_id == "consciousness" and
        state1.task == "consciousness" and
        state1.atp_budget == 1000.0
    )
    print_test("Create standard consciousness identity", test_1)

    # Test 2: Create enhanced SAGE identity
    identity2, state2 = manager.create_sage_identity("alice", use_enhanced_sage=True)
    test_2 = (
        identity2.task.task_id == "consciousness.sage" and
        state2.task == "consciousness.sage" and
        state2.atp_budget == 2000.0
    )
    print_test("Create enhanced consciousness.sage identity", test_2)

    # Test 3: LCT identity format correct
    test_3 = (
        identity1.lct_string() == "lct:web4:agent:dp@Thor#consciousness" and
        identity2.lct_string() == "lct:web4:agent:alice@Thor#consciousness.sage"
    )
    print_test("LCT identity format correct", test_3)

    # Test 4: Consciousness state initialized
    test_4 = (
        state1.awareness_level == 0.5 and
        state1.atp_spent == 0.0 and
        state1.loop_count == 0
    )
    print_test("Consciousness state initialized correctly", test_4)

    # Test 5: Resource limits match unified standard
    sage_std_limits = UNIFIED_RESOURCE_LIMITS["consciousness.sage"]
    test_5 = (
        state2.atp_budget == sage_std_limits.atp_budget and
        state2.max_tasks == sage_std_limits.max_tasks
    )
    print_test("Resource limits match unified standard", test_5)

    # Test 6: Convenience functions work
    lct_str_1 = create_sage_identity_lct("dp", "Thor", enhanced=False)
    lct_str_2 = create_sage_identity_lct("alice", "Sprout", enhanced=True)
    test_6 = (
        lct_str_1 == "lct:web4:agent:dp@Thor#consciousness" and
        lct_str_2 == "lct:web4:agent:alice@Sprout#consciousness.sage"
    )
    print_test("Convenience functions (create_sage_identity_lct)", test_6)

    all_passed = all([test_1, test_2, test_3, test_4, test_5, test_6])
    print(f"\nTest 2: {'PASS' if all_passed else 'FAIL'}")
    return all_passed


def test_consciousness_permissions():
    """Test 3: Consciousness Permission Checking"""
    print_section("Test 3: Consciousness Permission Checking")

    manager = SAGELCTManager("Legion")
    identity, state = manager.create_sage_identity("dp", use_enhanced_sage=False)
    sage_lct = identity.lct_string()

    # Test 1: Can execute code
    can_op, reason = manager.can_perform_consciousness_operation(
        sage_lct,
        "execute_code",
        atp_cost=50.0
    )
    test_1 = can_op
    print_test("Consciousness can execute code", test_1)

    # Test 2: Can delegate
    can_op, reason = manager.can_perform_consciousness_operation(
        sage_lct,
        "delegate",
        atp_cost=0.0
    )
    test_2 = can_op
    print_test("Consciousness can delegate", test_2)

    # Test 3: Can perform loops
    can_op, reason = manager.can_perform_consciousness_operation(
        sage_lct,
        "loop",
        atp_cost=10.0
    )
    test_3 = can_op
    print_test("Consciousness can perform loops", test_3)

    # Test 4: ATP budget enforced
    can_op, reason = manager.can_perform_consciousness_operation(
        sage_lct,
        "loop",
        atp_cost=2000.0  # Exceeds 1000.0 budget
    )
    test_4 = not can_op and "budget" in reason.lower()
    print_test("ATP budget enforced (large cost blocked)", test_4)

    # Test 5: Check permission helper works
    test_5_a = check_unified_permission("consciousness", "atp:write")
    test_5_b = check_unified_permission("consciousness", "federation:delegate")
    test_5_c = not check_unified_permission("perception", "atp:write")
    test_5 = test_5_a and test_5_b and test_5_c
    print_test("Permission checking helper functions", test_5)

    all_passed = all([test_1, test_2, test_3, test_4, test_5])
    print(f"\nTest 3: {'PASS' if all_passed else 'FAIL'}")
    return all_passed


def test_consciousness_loop_tracking():
    """Test 4: Consciousness Loop Tracking"""
    print_section("Test 4: Consciousness Loop Tracking")

    manager = SAGELCTManager("Sprout")
    identity, state = manager.create_sage_identity("alice", use_enhanced_sage=True)
    sage_lct = identity.lct_string()

    # Test 1: Record consciousness loop
    success, reason = manager.record_consciousness_loop(
        sage_lct,
        atp_cost=50.0,
        duration=0.5
    )
    test_1 = success
    print_test("Record consciousness loop", test_1)

    # Test 2: ATP spending tracked
    summary = manager.get_consciousness_summary(sage_lct)
    test_2 = (
        summary is not None and
        summary["atp_spent"] == 50.0 and
        summary["loop_count"] == 1
    )
    print_test("ATP spending tracked correctly", test_2)

    # Test 3: Multiple loops
    for i in range(5):
        manager.record_consciousness_loop(sage_lct, atp_cost=20.0, duration=0.1)

    summary = manager.get_consciousness_summary(sage_lct)
    test_3 = (
        summary["atp_spent"] == 150.0 and  # 50 + 5*20
        summary["loop_count"] == 6 and  # 1 + 5
        summary["is_active"]
    )
    print_test("Multiple loops tracked", test_3)

    # Test 4: ATP budget prevents overspending
    # Budget is 2000.0, already spent 150.0
    success, reason = manager.record_consciousness_loop(
        sage_lct,
        atp_cost=2000.0,  # Would exceed budget
        duration=1.0
    )
    test_4 = not success and "budget" in reason.lower()
    print_test("ATP budget prevents overspending", test_4)

    # Test 5: Get consciousness summary
    summary = manager.get_consciousness_summary(sage_lct)
    test_5 = (
        summary["task"] == "consciousness.sage" and
        summary["atp_budget"] == 2000.0 and
        summary["atp_remaining"] == 1850.0
    )
    print_test("Get consciousness summary", test_5)

    all_passed = all([test_1, test_2, test_3, test_4, test_5])
    print(f"\nTest 4: {'PASS' if all_passed else 'FAIL'}")
    return all_passed


def test_cross_platform_sage():
    """Test 5: Cross-Platform SAGE"""
    print_section("Test 5: Cross-Platform SAGE")

    # Create SAGE instances on multiple platforms
    thor_manager = SAGELCTManager("Thor")
    legion_manager = SAGELCTManager("Legion")
    sprout_manager = SAGELCTManager("Sprout")

    thor_id, thor_state = thor_manager.create_sage_identity("dp", use_enhanced_sage=True)
    legion_id, legion_state = legion_manager.create_sage_identity("alice", use_enhanced_sage=False)
    sprout_id, sprout_state = sprout_manager.create_sage_identity("bob", use_enhanced_sage=True)

    # Test 1: Different platforms, consistent task definitions
    test_1 = (
        thor_id.lct_string() == "lct:web4:agent:dp@Thor#consciousness.sage" and
        legion_id.lct_string() == "lct:web4:agent:alice@Legion#consciousness" and
        sprout_id.lct_string() == "lct:web4:agent:bob@Sprout#consciousness.sage"
    )
    print_test("Different platforms, consistent LCT format", test_1)

    # Test 2: Same task type has same permissions across platforms
    test_2 = (
        thor_state.atp_budget == sprout_state.atp_budget == 2000.0 and
        legion_state.atp_budget == 1000.0
    )
    print_test("Same task type, same ATP budget across platforms", test_2)

    # Test 3: List active instances
    thor_manager.record_consciousness_loop(thor_id.lct_string(), 10.0, 0.1)
    legion_manager.record_consciousness_loop(legion_id.lct_string(), 5.0, 0.1)

    thor_active = thor_manager.list_active_sage_instances()
    test_3 = len(thor_active) == 1 and thor_active[0]["lct_id"] == thor_id.lct_string()
    print_test("List active SAGE instances per platform", test_3)

    # Test 4: Total ATP consumption tracking
    thor_manager.record_consciousness_loop(thor_id.lct_string(), 20.0, 0.1)
    total_atp = thor_manager.get_total_sage_atp_consumption()
    test_4 = total_atp == 30.0  # 10 + 20
    print_test("Total ATP consumption tracking", test_4)

    # Test 5: Helper functions work for all platforms
    test_5_a = get_sage_atp_budget(enhanced=True) == 2000.0
    test_5_b = get_sage_atp_budget(enhanced=False) == 1000.0
    sage_limits = get_sage_resource_limits(enhanced=True)
    test_5_c = sage_limits.memory_mb == 32768
    test_5 = test_5_a and test_5_b and test_5_c
    print_test("Helper functions work consistently", test_5)

    all_passed = all([test_1, test_2, test_3, test_4, test_5])
    print(f"\nTest 5: {'PASS' if all_passed else 'FAIL'}")
    return all_passed


def test_sage_resource_limits():
    """Test 6: SAGE Resource Limits"""
    print_section("Test 6: SAGE Resource Limits")

    # Test 1: Standard consciousness limits
    consciousness_limits = UNIFIED_RESOURCE_LIMITS["consciousness"]
    test_1 = (
        consciousness_limits.atp_budget == 1000.0 and
        consciousness_limits.memory_mb == 16384 and
        consciousness_limits.cpu_cores == 8 and
        consciousness_limits.max_tasks == 100
    )
    print_test("Standard consciousness resource limits", test_1)

    # Test 2: Enhanced SAGE limits
    sage_limits = UNIFIED_RESOURCE_LIMITS["consciousness.sage"]
    test_2 = (
        sage_limits.atp_budget == 2000.0 and
        sage_limits.memory_mb == 32768 and
        sage_limits.cpu_cores == 16 and
        sage_limits.max_tasks == 200
    )
    print_test("Enhanced consciousness.sage resource limits", test_2)

    # Test 3: SAGE has more resources than standard consciousness
    test_3 = (
        sage_limits.atp_budget > consciousness_limits.atp_budget and
        sage_limits.memory_mb > consciousness_limits.memory_mb and
        sage_limits.cpu_cores > consciousness_limits.cpu_cores and
        sage_limits.max_tasks > consciousness_limits.max_tasks
    )
    print_test("SAGE has enhanced resources vs standard consciousness", test_3)

    # Test 4: Consciousness has more than execution.code
    exec_limits = UNIFIED_RESOURCE_LIMITS["execution.code"]
    test_4 = (
        consciousness_limits.memory_mb > exec_limits.memory_mb and
        consciousness_limits.max_tasks > exec_limits.max_tasks
    )
    print_test("Consciousness has more resources than execution.code", test_4)

    # Test 5: max_concurrent_tasks alias works
    test_5 = sage_limits.max_concurrent_tasks == sage_limits.max_tasks
    print_test("max_concurrent_tasks alias works (HRM/SAGE compat)", test_5)

    all_passed = all([test_1, test_2, test_3, test_4, test_5])
    print(f"\nTest 6: {'PASS' if all_passed else 'FAIL'}")
    return all_passed


def main():
    """Run all SAGE + LCT integration tests"""
    print("\n" + "="*70)
    print("  SAGE + LCT Integration Tests")
    print("="*70)
    print("\nTests SAGE consciousness integration with Web4 LCT system.")
    print("Validates cross-platform compatibility (web4 ↔ HRM/SAGE).\n")

    results = []

    # Test 1: Unified permissions
    passed_1 = test_unified_permissions()
    results.append(("Test 1: Unified Permission System", passed_1))

    # Test 2: SAGE identity creation
    passed_2 = test_sage_identity_creation()
    results.append(("Test 2: SAGE Identity Creation", passed_2))

    # Test 3: Consciousness permissions
    passed_3 = test_consciousness_permissions()
    results.append(("Test 3: Consciousness Permission Checking", passed_3))

    # Test 4: Consciousness loop tracking
    passed_4 = test_consciousness_loop_tracking()
    results.append(("Test 4: Consciousness Loop Tracking", passed_4))

    # Test 5: Cross-platform SAGE
    passed_5 = test_cross_platform_sage()
    results.append(("Test 5: Cross-Platform SAGE", passed_5))

    # Test 6: SAGE resource limits
    passed_6 = test_sage_resource_limits()
    results.append(("Test 6: SAGE Resource Limits", passed_6))

    # Summary
    print_section("Test Results Summary")

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}  {test_name}")

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    print(f"\nTotal: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 All SAGE + LCT integration tests passed!")
        print("\nStatus: SAGE consciousness fully integrated with Web4 LCT")
        print("  ✅ Unified permission standard implemented")
        print("  ✅ consciousness and consciousness.sage tasks defined")
        print("  ✅ Cross-platform SAGE identity working")
        print("  ✅ ATP budget tracking operational")
        print("  ✅ Permission checking validated")
        print("\nReady for: Production SAGE deployment on web4")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
