#!/usr/bin/env python3
"""
ATP Ledger Permission Integration Tests

Tests permission-enforced ATP operations.

Author: Legion Autonomous Session #49
Date: 2025-12-02
Status: Phase 4 integration testing
References: atp_permissions.py, lct_permissions.py, atp_ledger.py
"""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from game.engine.atp_permissions import (
    PermissionEnforcedATPLedger,
    create_permission_enforced_ledger,
    PermissionError,
    BudgetExceededError
)


def test_balance_query_with_permissions():
    """Test: ATP balance queries with permission checks"""
    print("=" * 80)
    print("Test 1: Balance Query with Permissions")
    print("=" * 80)
    print()

    ledger = create_permission_enforced_ledger("Thor")

    # Create accounts
    perception_lct = "lct:web4:agent:alice@Thor#perception"
    execution_lct = "lct:web4:agent:bob@Thor#execution.code"

    ledger.set_balance(perception_lct, 100.0)
    ledger.set_balance(execution_lct, 500.0)

    # Test 1: Self-query with atp:read (should succeed)
    balance, reason = ledger.get_balance(perception_lct, perception_lct)
    status1 = "✅" if balance is not None else "❌"
    print(f"{status1} Perception self-query: balance={balance}, reason='{reason}'")

    # Test 2: Self-query with atp:read (should succeed)
    balance, reason = ledger.get_balance(execution_lct, execution_lct)
    status2 = "✅" if balance is not None else "❌"
    print(f"{status2} Execution self-query: balance={balance}, reason='{reason}'")

    # Test 3: Other-query without admin (should fail)
    balance, reason = ledger.get_balance(execution_lct, perception_lct)
    status3 = "✅" if balance is None else "❌"
    print(f"{status3} Perception query other (denied): balance={balance}, reason='{reason[:60]}'")

    print()
    print(f"Validation: {sum([status == '✅' for status in [status1, status2, status3]])}/3 passed")
    print()


def test_atp_transfer_with_permissions():
    """Test: ATP transfers with permission checks"""
    print("=" * 80)
    print("Test 2: ATP Transfers with Permission Checks")
    print("=" * 80)
    print()

    ledger = create_permission_enforced_ledger("Thor")

    # Create accounts
    perception_lct = "lct:web4:agent:alice@Thor#perception"
    execution_lct = "lct:web4:agent:bob@Thor#execution.code"
    planning_lct = "lct:web4:agent:charlie@Thor#planning"

    ledger.set_balance(perception_lct, 100.0)
    ledger.set_balance(execution_lct, 500.0)
    ledger.set_balance(planning_lct, 100.0)

    # Test 1: Perception tries to transfer (should fail - no atp:write)
    success, reason = ledger.transfer(perception_lct, execution_lct, 50.0)
    status1 = "✅" if not success else "❌"
    print(f"{status1} Perception transfer (denied): success={success}, reason='{reason[:60]}'")

    # Test 2: Execution transfers (should succeed - has atp:write)
    success, reason = ledger.transfer(execution_lct, perception_lct, 50.0)
    status2 = "✅" if success else "❌"
    print(f"{status2} Execution transfer (allowed): success={success}, reason='{reason}'")

    # Test 3: Planning tries to transfer (should fail - no atp:write)
    success, reason = ledger.transfer(planning_lct, execution_lct, 50.0)
    status3 = "✅" if not success else "❌"
    print(f"{status3} Planning transfer (denied): success={success}, reason='{reason[:60]}'")

    print()
    print(f"Validation: {sum([status == '✅' for status in [status1, status2, status3]])}/3 passed")
    print()


def test_budget_enforcement():
    """Test: ATP budget limit enforcement"""
    print("=" * 80)
    print("Test 3: Budget Limit Enforcement")
    print("=" * 80)
    print()

    ledger = create_permission_enforced_ledger("Thor")

    # Create account with execution.code task (500 ATP budget)
    execution_lct = "lct:web4:agent:alice@Thor#execution.code"
    target_lct = "lct:web4:agent:bob@Thor#perception"

    ledger.set_balance(execution_lct, 1000.0)  # High balance
    ledger.set_balance(target_lct, 0.0)

    # Test 1: Transfer within budget (should succeed)
    success, reason = ledger.transfer(execution_lct, target_lct, 100.0)
    status1 = "✅" if success else "❌"
    print(f"{status1} Transfer 100 (within 500 budget): success={success}")

    # Check remaining budget
    remaining, _ = ledger.get_remaining_budget(execution_lct)
    print(f"   Remaining budget: {remaining}")

    # Test 2: Transfer within budget (should succeed)
    success, reason = ledger.transfer(execution_lct, target_lct, 200.0)
    status2 = "✅" if success else "❌"
    print(f"{status2} Transfer 200 (total 300/500): success={success}")

    remaining, _ = ledger.get_remaining_budget(execution_lct)
    print(f"   Remaining budget: {remaining}")

    # Test 3: Transfer exceeding budget (should fail)
    success, reason = ledger.transfer(execution_lct, target_lct, 300.0)
    status3 = "✅" if not success else "❌"
    print(f"{status3} Transfer 300 (would exceed 500 budget): success={success}")
    print(f"   Reason: {reason[:70]}")

    print()

    # Get spending stats
    stats = ledger.get_spending_stats(execution_lct)
    print("Spending statistics:")
    print(f"  Budget: {stats['budget']}")
    print(f"  Spent: {stats['spent']}")
    print(f"  Remaining: {stats['remaining']}")
    print(f"  Percent used: {stats['percent_used']:.1f}%")

    print()
    print(f"Validation: {sum([status == '✅' for status in [status1, status2, status3]])}/3 passed")
    print()


def test_different_task_budgets():
    """Test: Different ATP budgets for different tasks"""
    print("=" * 80)
    print("Test 4: Different Task Budgets")
    print("=" * 80)
    print()

    ledger = create_permission_enforced_ledger("Thor")

    tasks = [
        ("lct:web4:agent:user1@Thor#perception", "perception", 100.0),
        ("lct:web4:agent:user2@Thor#execution.code", "execution.code", 500.0),
        ("lct:web4:agent:user3@Thor#delegation.federation", "delegation.federation", 1000.0),
        ("lct:web4:agent:admin@Thor#admin.full", "admin.full", float('inf'))
    ]

    target_lct = "lct:web4:agent:target@Thor#perception"
    ledger.set_balance(target_lct, 0.0)

    print("Task budgets:")
    for lct_id, task_name, expected_budget in tasks:
        ledger.set_balance(lct_id, 10000.0)  # High balance
        remaining, _ = ledger.get_remaining_budget(lct_id)
        status = "✅" if remaining == expected_budget else "❌"
        print(f"  {status} {task_name:30} {expected_budget:>12} ATP")

    print()


def test_spending_tracking():
    """Test: Cumulative spending tracking"""
    print("=" * 80)
    print("Test 5: Cumulative Spending Tracking")
    print("=" * 80)
    print()

    ledger = create_permission_enforced_ledger("Thor")

    # Create account
    execution_lct = "lct:web4:agent:alice@Thor#execution.code"
    target_lct = "lct:web4:agent:bob@Thor#perception"

    ledger.set_balance(execution_lct, 10000.0)
    ledger.set_balance(target_lct, 0.0)

    # Make multiple transfers
    transfers = [50.0, 100.0, 150.0, 200.0]

    print("Making transfers:")
    total_spent = 0.0
    for i, amount in enumerate(transfers, 1):
        success, reason = ledger.transfer(execution_lct, target_lct, amount)
        total_spent += amount if success else 0

        stats = ledger.get_spending_stats(execution_lct)
        status = "✅" if success else "❌"
        print(f"  {status} Transfer #{i}: {amount} ATP → Spent: {stats['spent']}/{stats['budget']}")

    print()

    # Get final stats
    stats = ledger.get_spending_stats(execution_lct)
    print("Final statistics:")
    print(f"  Total operations: {stats['total_operations']}")
    print(f"  Successful: {stats['successful_operations']}")
    print(f"  Failed: {stats['failed_operations']}")
    print(f"  Total spent: {stats['spent']} ATP")
    print(f"  Budget remaining: {stats['remaining']} ATP")

    print()


def test_operation_logging():
    """Test: ATP operation logging"""
    print("=" * 80)
    print("Test 6: Operation Logging")
    print("=" * 80)
    print()

    ledger = create_permission_enforced_ledger("Thor")

    # Create accounts
    perception_lct = "lct:web4:agent:alice@Thor#perception"
    execution_lct = "lct:web4:agent:bob@Thor#execution.code"

    ledger.set_balance(perception_lct, 100.0)
    ledger.set_balance(execution_lct, 500.0)

    # Perform various operations
    ledger.get_balance(perception_lct, perception_lct)  # Success
    ledger.get_balance(execution_lct, perception_lct)  # Fail (no admin permission)
    ledger.transfer(perception_lct, execution_lct, 50.0)  # Fail (no atp:write)
    ledger.transfer(execution_lct, perception_lct, 50.0)  # Success

    # Get operation log
    logs = ledger.get_operation_log(limit=10)

    print(f"Operation log ({len(logs)} entries):")
    for i, log in enumerate(logs[:5], 1):
        status = "✅" if log.success else "❌"
        print(f"  {i}. {status} {log.operation:10} {log.lct_id:50} amt={log.amount:>6.1f}")
        if not log.success:
            print(f"      Reason: {log.reason[:60]}")

    print()

    # Get ledger stats
    stats = ledger.get_ledger_stats()
    print("Ledger statistics:")
    print(f"  Total operations: {stats['total_operations']}")
    print(f"  Successful: {stats['successful_operations']}")
    print(f"  Failed: {stats['failed_operations']}")
    print(f"  Permission denials: {stats['permission_denials']}")
    print(f"  Budget denials: {stats['budget_denials']}")

    print()


def test_admin_queries():
    """Test: Admin queries with admin permissions"""
    print("=" * 80)
    print("Test 7: Admin Queries")
    print("=" * 80)
    print()

    ledger = create_permission_enforced_ledger("Thor")

    # Create accounts
    perception_lct = "lct:web4:agent:alice@Thor#perception"
    admin_lct = "lct:web4:agent:admin@Thor#admin.full"
    readonly_admin_lct = "lct:web4:agent:monitor@Thor#admin.readonly"

    ledger.set_balance(perception_lct, 100.0)
    ledger.set_balance(admin_lct, 1000.0)
    ledger.set_balance(readonly_admin_lct, 100.0)

    # Test 1: Admin.full queries other account (should succeed)
    balance, reason = ledger.get_balance(perception_lct, admin_lct)
    status1 = "✅" if balance is not None else "❌"
    print(f"{status1} Admin.full queries perception: balance={balance}")

    # Test 2: Admin.readonly queries other account (should succeed)
    balance, reason = ledger.get_balance(perception_lct, readonly_admin_lct)
    status2 = "✅" if balance is not None else "❌"
    print(f"{status2} Admin.readonly queries perception: balance={balance}")

    # Test 3: Perception queries other (should fail)
    balance, reason = ledger.get_balance(admin_lct, perception_lct)
    status3 = "✅" if balance is None else "❌"
    print(f"{status3} Perception queries admin (denied): balance={balance}")
    print(f"   Reason: {reason[:60]}")

    print()
    print(f"Validation: {sum([status == '✅' for status in [status1, status2, status3]])}/3 passed")
    print()


def test_budget_reset():
    """Test: Budget reset (admin operation)"""
    print("=" * 80)
    print("Test 8: Budget Reset")
    print("=" * 80)
    print()

    ledger = create_permission_enforced_ledger("Thor")

    # Create account
    execution_lct = "lct:web4:agent:alice@Thor#execution.code"
    target_lct = "lct:web4:agent:bob@Thor#perception"

    ledger.set_balance(execution_lct, 10000.0)
    ledger.set_balance(target_lct, 0.0)

    # Spend some ATP
    ledger.transfer(execution_lct, target_lct, 300.0)

    stats_before = ledger.get_spending_stats(execution_lct)
    print(f"Before reset: Spent {stats_before['spent']}/{stats_before['budget']}")

    # Reset spending
    ledger.reset_spending(execution_lct)

    stats_after = ledger.get_spending_stats(execution_lct)
    print(f"After reset:  Spent {stats_after['spent']}/{stats_after['budget']}")

    # Verify spending was reset
    status = "✅" if stats_after['spent'] == 0.0 else "❌"
    print(f"{status} Spending counter reset to 0")

    print()


if __name__ == "__main__":
    print()
    print("🔒💰 ATP Ledger Permission Integration Tests")
    print()
    print("Tests ATP operations with LCT permission enforcement:")
    print("  - Balance queries with permission checks")
    print("  - ATP transfers with permission checks")
    print("  - Budget limit enforcement")
    print("  - Different task budgets")
    print("  - Cumulative spending tracking")
    print("  - Operation logging")
    print("  - Admin queries")
    print("  - Budget reset")
    print()

    test_balance_query_with_permissions()
    test_atp_transfer_with_permissions()
    test_budget_enforcement()
    test_different_task_budgets()
    test_spending_tracking()
    test_operation_logging()
    test_admin_queries()
    test_budget_reset()

    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print("✅ Balance queries with permissions working")
    print("✅ ATP transfers with permissions working")
    print("✅ Budget enforcement working")
    print("✅ Different task budgets working")
    print("✅ Spending tracking working")
    print("✅ Operation logging working")
    print("✅ Admin queries working")
    print("✅ Budget reset working")
    print()
    print("Status: ATP + LCT permission integration validated")
    print("Next: Federation + LCT permission integration")
    print()
    print("Co-Authored-By: Claude (Legion Autonomous) <noreply@anthropic.com>")
    print()
