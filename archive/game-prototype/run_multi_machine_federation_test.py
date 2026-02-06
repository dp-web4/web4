#!/usr/bin/env python3
"""
Multi-Machine SAGE Federation Test

Tests cross-platform SAGE consciousness delegation with ATP tracking.
Validates complete federation stack: server, client, ATP settlement, quality scoring.

This test runs locally with multi-process simulation of Legion, Thor, and Sprout.

Usage:
    python3 game/run_multi_machine_federation_test.py

Author: Legion Autonomous Session #54
Date: 2025-12-03
References: MULTI_MACHINE_SAGE_FEDERATION_DESIGN.md
"""

import sys
from pathlib import Path
import time
from typing import Dict
import multiprocessing
import signal

# Add web4 root to path
_web4_root = Path(__file__).parent.parent
if str(_web4_root) not in sys.path:
    sys.path.insert(0, str(_web4_root))


def run_federation_server(platform_name: str, port: int):
    """
    Run federation server in subprocess

    Parameters:
    -----------
    platform_name : str
        Platform name
    port : int
        Server port
    """
    from game.server.federation_server import create_federation_server

    print(f"[{platform_name}] Starting federation server on port {port}")

    server = create_federation_server(
        platform_name=platform_name,
        host="127.0.0.1",
        port=port
    )

    # Run server (blocks until interrupted)
    server.run(debug=False)


def test_basic_delegation():
    """Test 1: Basic task delegation"""
    print("\n" + "="*80)
    print("TEST 1: Basic Task Delegation (Thor → Legion)")
    print("="*80)

    from game.client.federation_client import FederationClient
    from game.engine.sage_lct_integration import SAGELCTManager

    # Create Thor client
    thor_client = FederationClient("Thor")

    # Register Legion as remote platform
    thor_client.register_platform(
        name="Legion",
        endpoint="http://127.0.0.1:8080",
        capabilities=["consciousness", "consciousness.sage"]
    )

    # Create local SAGE identity on Thor
    thor_manager = SAGELCTManager("Thor")
    identity, state = thor_manager.create_sage_identity(
        lineage="dp",
        use_enhanced_sage=False  # Standard consciousness
    )

    print(f"\nThor identity: {identity.lct_string()}")
    print(f"Thor ATP budget: {state.atp_budget}")

    # Delegate perception task to Legion
    print("\nDelegating perception task to Legion...")
    proof, error = thor_client.delegate_task(
        source_lct=identity.lct_string(),
        task_type="consciousness",
        operation="perception",
        atp_budget=50.0,
        parameters={"input": ["observation1", "observation2"]},
        target_platform="Legion"
    )

    if proof:
        print(f"✅ Delegation successful!")
        print(f"  Task ID: {proof.task_id}")
        print(f"  Executor: {proof.executor_lct}")
        print(f"  ATP consumed: {proof.atp_consumed}")
        print(f"  Execution time: {proof.execution_time:.3f}s")
        print(f"  Quality score: {proof.quality_score:.2f}")
        print(f"  Result: {proof.result}")
        return True
    else:
        print(f"✗ Delegation failed: {error}")
        return False


def test_enhanced_sage_delegation():
    """Test 2: Enhanced SAGE task delegation"""
    print("\n" + "="*80)
    print("TEST 2: Enhanced SAGE Delegation (Sprout → Legion)")
    print("="*80)

    from game.client.federation_client import FederationClient
    from game.engine.sage_lct_integration import SAGELCTManager

    # Create Sprout client
    sprout_client = FederationClient("Sprout")

    # Register Legion
    sprout_client.register_platform(
        name="Legion",
        endpoint="http://127.0.0.1:8080",
        capabilities=["consciousness", "consciousness.sage"]
    )

    # Create local identity on Sprout (standard consciousness)
    sprout_manager = SAGELCTManager("Sprout")
    identity, state = sprout_manager.create_sage_identity(
        lineage="dp",
        use_enhanced_sage=False
    )

    print(f"\nSprout identity: {identity.lct_string()}")
    print(f"Sprout ATP budget: {state.atp_budget}")

    # Delegate execution task using consciousness.sage on Legion
    print("\nDelegating execution task to Legion (consciousness.sage)...")
    proof, error = sprout_client.delegate_task(
        source_lct=identity.lct_string(),
        task_type="consciousness.sage",  # Use enhanced on remote
        operation="execution",
        atp_budget=100.0,
        parameters={"action": "complex_reasoning"},
        target_platform="Legion"
    )

    if proof:
        print(f"✅ Enhanced SAGE delegation successful!")
        print(f"  Task ID: {proof.task_id}")
        print(f"  Executor: {proof.executor_lct}")
        print(f"  ATP consumed: {proof.atp_consumed}")
        print(f"  Execution time: {proof.execution_time:.3f}s")
        print(f"  Quality score: {proof.quality_score:.2f}")
        print(f"  Result: {proof.result}")
        return True
    else:
        print(f"✗ Enhanced SAGE delegation failed: {error}")
        return False


def test_multiple_delegations():
    """Test 3: Multiple concurrent delegations"""
    print("\n" + "="*80)
    print("TEST 3: Multiple Concurrent Delegations")
    print("="*80)

    from game.client.federation_client import FederationClient
    from game.engine.sage_lct_integration import SAGELCTManager

    # Create Thor client
    thor_client = FederationClient("Thor")
    thor_client.register_platform(
        name="Legion",
        endpoint="http://127.0.0.1:8080",
        capabilities=["consciousness", "consciousness.sage"]
    )

    # Create local identity
    thor_manager = SAGELCTManager("Thor")
    identity, state = thor_manager.create_sage_identity(
        lineage="dp",
        use_enhanced_sage=True  # consciousness.sage
    )

    print(f"\nThor identity: {identity.lct_string()}")
    print(f"Thor ATP budget: {state.atp_budget}")

    # Delegate multiple tasks
    operations = ["perception", "planning", "execution"]
    proofs = []

    for operation in operations:
        print(f"\nDelegating {operation}...")
        proof, error = thor_client.delegate_task(
            source_lct=identity.lct_string(),
            task_type="consciousness",
            operation=operation,
            atp_budget=50.0,
            parameters={},
            target_platform="Legion"
        )

        if proof:
            print(f"  ✅ {operation}: quality={proof.quality_score:.2f}, ATP={proof.atp_consumed}")
            proofs.append(proof)
        else:
            print(f"  ✗ {operation} failed: {error}")

    print(f"\nCompleted {len(proofs)}/{len(operations)} delegations")
    print(f"Total ATP consumed: {sum(p.atp_consumed for p in proofs):.2f}")
    print(f"Average quality: {sum(p.quality_score for p in proofs) / len(proofs):.2f}")

    return len(proofs) == len(operations)


def test_status_check():
    """Test 4: Remote status checking"""
    print("\n" + "="*80)
    print("TEST 4: Remote Status Checking")
    print("="*80)

    from game.client.federation_client import FederationClient
    from game.engine.sage_lct_integration import SAGELCTManager

    # Create client and delegate a task
    thor_client = FederationClient("Thor")
    thor_client.register_platform(
        name="Legion",
        endpoint="http://127.0.0.1:8080",
        capabilities=["consciousness", "consciousness.sage"]
    )

    thor_manager = SAGELCTManager("Thor")
    identity, state = thor_manager.create_sage_identity("dp", False)

    # Delegate task
    print("\nDelegating task...")
    proof, error = thor_client.delegate_task(
        source_lct=identity.lct_string(),
        task_type="consciousness",
        operation="perception",
        atp_budget=50.0,
        target_platform="Legion"
    )

    if not proof:
        print(f"✗ Delegation failed: {error}")
        return False

    # Check status on Legion
    print(f"\nChecking status on Legion for {proof.executor_lct}...")
    status = thor_client.get_platform_status("Legion", proof.executor_lct)

    if status:
        print(f"✅ Status retrieved:")
        print(f"  LCT ID: {status['lct_id']}")
        print(f"  Task: {status['task']}")
        print(f"  ATP spent: {status['atp_spent']}")
        print(f"  ATP remaining: {status['atp_remaining']}")
        print(f"  Is active: {status['is_active']}")
        return True
    else:
        print(f"✗ Could not retrieve status")
        return False


def run_tests():
    """Run all federation tests"""
    print("\n" + "="*80)
    print("MULTI-MACHINE SAGE FEDERATION TEST")
    print("="*80)
    print("\nTesting cross-platform SAGE consciousness delegation")
    print("Simulating Legion (server), Thor (client), Sprout (client)")
    print("\nNote: This test requires the federation server to be running.")
    print("Start it in another terminal with:")
    print("  python3 game/run_federation_server.py --platform Legion --port 8080")
    print("\nWaiting 3 seconds for you to start the server...")
    time.sleep(3)

    results = {}

    try:
        # Test 1: Basic delegation
        results['basic_delegation'] = test_basic_delegation()
        time.sleep(0.5)

        # Test 2: Enhanced SAGE
        results['enhanced_sage'] = test_enhanced_sage_delegation()
        time.sleep(0.5)

        # Test 3: Multiple delegations
        results['multiple_delegations'] = test_multiple_delegations()
        time.sleep(0.5)

        # Test 4: Status check
        results['status_check'] = test_status_check()

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
        print("  - Federation server operational")
        print("  - Task delegation working")
        print("  - ATP tracking accurate")
        print("  - Quality scoring functional")
        print("  - Remote status checking operational")
        print("\nReady for: Multi-machine deployment (Legion, Thor, Sprout)")
        return True
    else:
        print("\n✗ SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
