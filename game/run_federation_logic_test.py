#!/usr/bin/env python3
"""
Federation Logic Test - No HTTP Server Required

Tests core federation logic without HTTP dependencies.
Validates task validation, execution, ATP tracking, and quality scoring.

Usage:
    python3 game/run_federation_logic_test.py

Author: Legion Autonomous Session #54
Date: 2025-12-03
"""

import sys
from pathlib import Path
import time

# Add web4 root to path
_web4_root = Path(__file__).parent.parent
if str(_web4_root) not in sys.path:
    sys.path.insert(0, str(_web4_root))

from game.server.federation_api import (
    FederationAPI,
    FederationTask,
    ExecutionProof
)


def test_task_validation():
    """Test 1: Task validation"""
    print("\n" + "="*80)
    print("TEST 1: Federation Task Validation")
    print("="*80)

    api = FederationAPI("Legion")

    # Valid task
    task1 = FederationTask(
        task_id="test_001",
        source_lct="lct:web4:agent:dp@Thor#consciousness",
        target_lct="lct:web4:agent:dp@Legion#consciousness",
        task_type="consciousness",
        operation="perception",
        atp_budget=50.0,
        timeout_seconds=60,
        parameters={},
        created_at=time.time()
    )

    valid, reason = api.validate_task(task1)
    print(f"Valid task: {valid}")
    if not valid:
        print(f"  Reason: {reason}")
        return False

    # Invalid task type
    task2 = FederationTask(
        task_id="test_002",
        source_lct="lct:web4:agent:dp@Thor#consciousness",
        target_lct="lct:web4:agent:dp@Legion#invalid",
        task_type="invalid",
        operation="perception",
        atp_budget=50.0,
        timeout_seconds=60,
        parameters={},
        created_at=time.time()
    )

    valid, reason = api.validate_task(task2)
    print(f"Invalid task type: not {valid} (expected)")
    if valid:
        print(f"  ERROR: Should have been invalid!")
        return False
    print(f"  Reason: {reason}")

    # Wrong platform
    task3 = FederationTask(
        task_id="test_003",
        source_lct="lct:web4:agent:dp@Thor#consciousness",
        target_lct="lct:web4:agent:dp@WrongPlatform#consciousness",
        task_type="consciousness",
        operation="perception",
        atp_budget=50.0,
        timeout_seconds=60,
        parameters={},
        created_at=time.time()
    )

    valid, reason = api.validate_task(task3)
    print(f"Wrong platform: not {valid} (expected)")
    if valid:
        print(f"  ERROR: Should have been invalid!")
        return False
    print(f"  Reason: {reason}")

    print("\n✅ Task validation working correctly")
    return True


def test_consciousness_task_execution():
    """Test 2: Consciousness task execution"""
    print("\n" + "="*80)
    print("TEST 2: Consciousness Task Execution")
    print("="*80)

    api = FederationAPI("Legion")

    # Create perception task
    task = FederationTask(
        task_id="perception_001",
        source_lct="lct:web4:agent:dp@Thor#consciousness",
        target_lct="lct:web4:agent:dp@Legion#consciousness",
        task_type="consciousness",
        operation="perception",
        atp_budget=50.0,
        timeout_seconds=60,
        parameters={"input": ["obs1", "obs2", "obs3"]},
        created_at=time.time()
    )

    print(f"Task: {task.operation}")
    print(f"Source: {task.source_lct}")
    print(f"Target: {task.target_lct}")
    print(f"ATP budget: {task.atp_budget}")

    # Execute task
    proof, error = api.delegate_consciousness_task(task, b'')

    if not proof:
        print(f"✗ Execution failed: {error}")
        return False

    print(f"\n✅ Execution successful!")
    print(f"  Task ID: {proof.task_id}")
    print(f"  Executor: {proof.executor_lct}")
    print(f"  ATP consumed: {proof.atp_consumed}")
    print(f"  Execution time: {proof.execution_time:.3f}s")
    print(f"  Quality score: {proof.quality_score:.2f}")
    print(f"  Result keys: {list(proof.result.keys())}")

    # Verify proof
    if proof.atp_consumed > task.atp_budget:
        print(f"✗ ATP consumed exceeds budget!")
        return False

    if proof.quality_score < 0.0 or proof.quality_score > 1.0:
        print(f"✗ Quality score out of range!")
        return False

    return True


def test_enhanced_sage_execution():
    """Test 3: Enhanced SAGE execution"""
    print("\n" + "="*80)
    print("TEST 3: Enhanced SAGE (consciousness.sage) Execution")
    print("="*80)

    api = FederationAPI("Legion")

    # Create execution task with consciousness.sage
    task = FederationTask(
        task_id="execution_sage_001",
        source_lct="lct:web4:agent:dp@Sprout#consciousness",
        target_lct="lct:web4:agent:dp@Legion#consciousness.sage",
        task_type="consciousness.sage",
        operation="execution",
        atp_budget=100.0,
        timeout_seconds=120,
        parameters={"action": "complex_reasoning"},
        created_at=time.time()
    )

    print(f"Task: {task.operation}")
    print(f"Task type: {task.task_type} (enhanced)")
    print(f"ATP budget: {task.atp_budget}")

    # Execute
    proof, error = api.delegate_consciousness_task(task, b'')

    if not proof:
        print(f"✗ Execution failed: {error}")
        return False

    print(f"\n✅ Enhanced SAGE execution successful!")
    print(f"  ATP consumed: {proof.atp_consumed}")
    print(f"  Quality score: {proof.quality_score:.2f}")
    print(f"  Result: {proof.result}")

    # Check that executor has consciousness.sage task type
    if "consciousness.sage" not in proof.executor_lct:
        print(f"✗ Executor LCT should have consciousness.sage!")
        return False

    return True


def test_atp_budget_enforcement():
    """Test 4: ATP budget enforcement"""
    print("\n" + "="*80)
    print("TEST 4: ATP Budget Enforcement")
    print("="*80)

    api = FederationAPI("Legion")

    # Create identity with limited budget
    from game.engine.sage_lct_integration import SAGELCTManager
    manager = SAGELCTManager("Legion")
    identity, state = manager.create_sage_identity("dp", False)

    print(f"Identity: {identity.lct_string()}")
    print(f"Initial ATP budget: {state.atp_budget}")

    # Execute tasks until budget exhausted
    task_count = 0
    while state.atp_spent < state.atp_budget:
        task = FederationTask(
            task_id=f"budget_test_{task_count}",
            source_lct="lct:web4:agent:dp@Thor#consciousness",
            target_lct=identity.lct_string(),
            task_type="consciousness",
            operation="planning",
            atp_budget=100.0,
            timeout_seconds=60,
            parameters={},
            created_at=time.time()
        )

        proof, error = api.delegate_consciousness_task(task, b'')

        if proof:
            print(f"  Task {task_count}: consumed {proof.atp_consumed} ATP")
            task_count += 1
        else:
            print(f"  Task {task_count}: blocked - {error}")
            break

    # Try one more task (should fail)
    final_task = FederationTask(
        task_id="budget_test_final",
        source_lct="lct:web4:agent:dp@Thor#consciousness",
        target_lct=identity.lct_string(),
        task_type="consciousness",
        operation="planning",
        atp_budget=100.0,
        timeout_seconds=60,
        parameters={},
        created_at=time.time()
    )

    proof, error = api.delegate_consciousness_task(final_task, b'')

    if proof:
        print(f"✗ Task should have been blocked due to budget!")
        return False

    print(f"\n✅ Budget enforcement working!")
    print(f"  Completed {task_count} tasks")
    print(f"  Total ATP consumed: {state.atp_spent}")
    print(f"  Budget limit: {state.atp_budget}")
    print(f"  Final task blocked: {error}")

    return True


def test_multiple_operations():
    """Test 5: Multiple operation types"""
    print("\n" + "="*80)
    print("TEST 5: Multiple Operation Types")
    print("="*80)

    api = FederationAPI("Legion")

    operations = ["perception", "planning", "execution", "delegation"]
    results = []

    for operation in operations:
        task = FederationTask(
            task_id=f"multi_op_{operation}",
            source_lct="lct:web4:agent:dp@Thor#consciousness",
            target_lct="lct:web4:agent:dp@Legion#consciousness",
            task_type="consciousness",
            operation=operation,
            atp_budget=60.0,
            timeout_seconds=60,
            parameters={},
            created_at=time.time()
        )

        print(f"\nExecuting {operation}...")
        proof, error = api.delegate_consciousness_task(task, b'')

        if proof:
            print(f"  ✅ Quality: {proof.quality_score:.2f}, ATP: {proof.atp_consumed:.2f}")
            results.append(proof)
        else:
            print(f"  ✗ Failed: {error}")

    if len(results) != len(operations):
        print(f"\n✗ Not all operations succeeded")
        return False

    print(f"\n✅ All operations successful!")
    print(f"  Total ATP consumed: {sum(p.atp_consumed for p in results):.2f}")
    print(f"  Average quality: {sum(p.quality_score for p in results) / len(results):.2f}")

    return True


def run_all_tests():
    """Run all federation logic tests"""
    print("\n" + "="*80)
    print("FEDERATION LOGIC TEST - Session #54")
    print("="*80)
    print("\nTesting core federation logic (no HTTP server required)")
    print("Validating:")
    print("  - Task validation")
    print("  - Consciousness task execution")
    print("  - Enhanced SAGE (consciousness.sage)")
    print("  - ATP budget enforcement")
    print("  - Multiple operation types")

    results = {}

    try:
        results['task_validation'] = test_task_validation()
        results['consciousness_execution'] = test_consciousness_task_execution()
        results['enhanced_sage'] = test_enhanced_sage_execution()
        results['atp_budget'] = test_atp_budget_enforcement()
        results['multiple_operations'] = test_multiple_operations()

    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Summary
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "✗ FAIL"
        print(f"{status}  {test_name}")

    total = len(results)
    passed = sum(1 for p in results.values() if p)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ ALL TESTS PASSED")
        print("\nConclusion:")
        print("  - Federation API logic working correctly")
        print("  - Task validation functional")
        print("  - ATP tracking accurate")
        print("  - Budget enforcement operational")
        print("  - Quality scoring functional")
        print("  - Ready for HTTP server deployment")
        return True
    else:
        print("\n✗ SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
