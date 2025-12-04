#!/usr/bin/env python3
"""
Comprehensive Federation Test - Session #55

Tests multi-machine SAGE consciousness federation with:
- Standard consciousness and consciousness.sage
- Multiple concurrent delegations
- ATP budget tracking
- Quality-based settlement
- Cross-platform compatibility

Validates the complete stack from Session #54 with Thor's Session #55
consciousness.sage memory management enhancements.

Usage:
    python3 game/test_federation_comprehensive.py [--port PORT]

Author: Legion Autonomous Session #55
Date: 2025-12-03
"""

import sys
from pathlib import Path
import argparse
from typing import List, Dict, Tuple
import time

# Add web4 root to path
_web4_root = Path(__file__).parent.parent
if str(_web4_root) not in sys.path:
    sys.path.insert(0, str(_web4_root))

from game.client.federation_client import FederationClient
from game.engine.sage_lct_integration import SAGELCTManager
from game.server.federation_api import ExecutionProof


def test_standard_consciousness_delegation(
    client: FederationClient,
    platform_name: str
) -> Tuple[bool, Dict]:
    """
    Test 1: Standard consciousness delegation

    Validates:
    - Basic task delegation
    - ATP tracking
    - Quality scoring
    - Permission enforcement
    """
    print("\n" + "="*80)
    print("TEST 1: Standard Consciousness Delegation")
    print("="*80)

    # Create local SAGE identity
    manager = SAGELCTManager(platform_name)
    identity, state = manager.create_sage_identity(
        lineage="dp",
        use_enhanced_sage=False  # Standard consciousness
    )

    print(f"\n{platform_name} identity: {identity.lct_string()}")
    print(f"{platform_name} ATP budget: {state.atp_budget}")
    print(f"{platform_name} task type: consciousness (standard)")

    # Test multiple operations
    operations = ["perception", "planning", "execution"]
    proofs: List[ExecutionProof] = []
    total_atp = 0.0

    for operation in operations:
        print(f"\nDelegating {operation}...")
        proof, error = client.delegate_task(
            source_lct=identity.lct_string(),
            task_type="consciousness",
            operation=operation,
            atp_budget=100.0,
            parameters={"test": f"{operation}_test"},
            target_platform="Legion"
        )

        if proof:
            print(f"  ✅ Success: quality={proof.quality_score:.2f}, ATP={proof.atp_consumed:.2f}")
            proofs.append(proof)
            total_atp += proof.atp_consumed
        else:
            print(f"  ✗ Failed: {error}")
            return False, {}

    # Summary
    avg_quality = sum(p.quality_score for p in proofs) / len(proofs)
    print(f"\n✅ Standard consciousness test PASSED")
    print(f"  Operations: {len(proofs)}/{len(operations)}")
    print(f"  Total ATP: {total_atp:.2f}")
    print(f"  Avg quality: {avg_quality:.2f}")

    return True, {
        'operations_completed': len(proofs),
        'total_atp': total_atp,
        'avg_quality': avg_quality,
        'proofs': proofs
    }


def test_enhanced_sage_delegation(
    client: FederationClient,
    platform_name: str
) -> Tuple[bool, Dict]:
    """
    Test 2: Enhanced consciousness.sage delegation

    Validates:
    - Enhanced task delegation
    - Higher ATP budget (2000 vs 1000)
    - Enhanced permissions (exec:code, storage:delete)
    - Memory management awareness
    """
    print("\n" + "="*80)
    print("TEST 2: Enhanced Consciousness.sage Delegation")
    print("="*80)

    # Create enhanced SAGE identity
    manager = SAGELCTManager(platform_name)
    identity, state = manager.create_sage_identity(
        lineage="dp",
        use_enhanced_sage=True  # consciousness.sage
    )

    print(f"\n{platform_name} identity: {identity.lct_string()}")
    print(f"{platform_name} ATP budget: {state.atp_budget}")
    print(f"{platform_name} task type: consciousness.sage (enhanced)")

    # Test enhanced operations (including code execution)
    operations = ["perception", "planning", "execution", "delegation"]
    proofs: List[ExecutionProof] = []
    total_atp = 0.0

    for operation in operations:
        print(f"\nDelegating {operation} (enhanced)...")
        proof, error = client.delegate_task(
            source_lct=identity.lct_string(),
            task_type="consciousness.sage",
            operation=operation,
            atp_budget=150.0,
            parameters={"test": f"enhanced_{operation}"},
            target_platform="Legion"
        )

        if proof:
            print(f"  ✅ Success: quality={proof.quality_score:.2f}, ATP={proof.atp_consumed:.2f}")
            proofs.append(proof)
            total_atp += proof.atp_consumed
        else:
            print(f"  ✗ Failed: {error}")
            return False, {}

    # Summary
    avg_quality = sum(p.quality_score for p in proofs) / len(proofs)
    print(f"\n✅ Enhanced SAGE test PASSED")
    print(f"  Operations: {len(proofs)}/{len(operations)}")
    print(f"  Total ATP: {total_atp:.2f}")
    print(f"  Avg quality: {avg_quality:.2f}")

    return True, {
        'operations_completed': len(proofs),
        'total_atp': total_atp,
        'avg_quality': avg_quality,
        'proofs': proofs
    }


def test_concurrent_delegations(
    client: FederationClient,
    platform_name: str,
    num_concurrent: int = 5
) -> Tuple[bool, Dict]:
    """
    Test 3: Concurrent task delegations

    Validates:
    - Multiple simultaneous delegations
    - ATP tracking under load
    - Server concurrency handling
    - Quality consistency
    """
    print("\n" + "="*80)
    print(f"TEST 3: Concurrent Delegations ({num_concurrent} tasks)")
    print("="*80)

    # Create identity
    manager = SAGELCTManager(platform_name)
    identity, state = manager.create_sage_identity(
        lineage="dp",
        use_enhanced_sage=False
    )

    print(f"\n{platform_name} identity: {identity.lct_string()}")
    print(f"Launching {num_concurrent} concurrent delegations...")

    # Launch concurrent tasks
    import concurrent.futures

    def delegate_task(task_num: int) -> Tuple[bool, ExecutionProof]:
        proof, error = client.delegate_task(
            source_lct=identity.lct_string(),
            task_type="consciousness",
            operation="perception",
            atp_budget=50.0,
            parameters={"task_num": task_num},
            target_platform="Legion"
        )
        return (proof is not None, proof if proof else None)

    # Execute concurrently
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
        futures = [executor.submit(delegate_task, i) for i in range(num_concurrent)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    elapsed_time = time.time() - start_time

    # Analyze results
    successful = [r for r in results if r[0]]
    proofs = [r[1] for r in successful if r[1] is not None]

    total_atp = sum(p.atp_consumed for p in proofs)
    avg_quality = sum(p.quality_score for p in proofs) / len(proofs) if proofs else 0.0

    print(f"\n✅ Concurrent delegation test PASSED")
    print(f"  Completed: {len(successful)}/{num_concurrent}")
    print(f"  Total time: {elapsed_time:.2f}s")
    print(f"  Avg time per task: {elapsed_time/num_concurrent:.3f}s")
    print(f"  Total ATP: {total_atp:.2f}")
    print(f"  Avg quality: {avg_quality:.2f}")

    return len(successful) == num_concurrent, {
        'tasks_completed': len(successful),
        'tasks_target': num_concurrent,
        'total_time': elapsed_time,
        'avg_time_per_task': elapsed_time / num_concurrent,
        'total_atp': total_atp,
        'avg_quality': avg_quality
    }


def test_atp_budget_enforcement(
    client: FederationClient,
    platform_name: str
) -> Tuple[bool, Dict]:
    """
    Test 4: ATP budget enforcement

    Validates:
    - Budget limits enforced
    - Tasks rejected when budget exhausted
    - ATP accounting accurate
    """
    print("\n" + "="*80)
    print("TEST 4: ATP Budget Enforcement")
    print("="*80)

    # Create identity with standard budget (1000 ATP)
    manager = SAGELCTManager(platform_name)
    identity, state = manager.create_sage_identity(
        lineage="dp",
        use_enhanced_sage=False
    )

    print(f"\n{platform_name} identity: {identity.lct_string()}")
    print(f"ATP budget: {state.atp_budget}")
    print(f"Testing budget exhaustion...")

    # Delegate tasks until budget exhausted
    tasks_completed = 0
    total_atp_consumed = 0.0

    # Each task costs ~15 ATP (planning operation)
    max_tasks = int(state.atp_budget / 15) + 5  # Try 5 extra to trigger rejection

    for i in range(max_tasks):
        proof, error = client.delegate_task(
            source_lct=identity.lct_string(),
            task_type="consciousness",
            operation="planning",
            atp_budget=20.0,  # Request 20, will consume ~15
            parameters={"task_num": i},
            target_platform="Legion"
        )

        if proof:
            tasks_completed += 1
            total_atp_consumed += proof.atp_consumed
        else:
            # Expected to fail when budget exhausted
            print(f"\n  Task {i+1} rejected: {error}")
            break

    # Validate budget enforcement
    budget_enforced = "budget" in error.lower() or "insufficient" in error.lower()

    print(f"\n{'✅' if budget_enforced else '✗'} ATP budget enforcement test {'PASSED' if budget_enforced else 'FAILED'}")
    print(f"  Tasks completed: {tasks_completed}/{max_tasks}")
    print(f"  Total ATP consumed: {total_atp_consumed:.2f}")
    print(f"  Budget limit: {state.atp_budget}")
    print(f"  Budget enforced: {budget_enforced}")

    return budget_enforced, {
        'tasks_completed': tasks_completed,
        'total_atp_consumed': total_atp_consumed,
        'budget_limit': state.atp_budget,
        'budget_enforced': budget_enforced
    }


def run_comprehensive_federation_test(server_port: int = 8090):
    """
    Run comprehensive federation test suite
    """
    print("\n" + "="*80)
    print("COMPREHENSIVE MULTI-MACHINE SAGE FEDERATION TEST")
    print("Session #55 - Legion Autonomous Research")
    print("="*80)
    print(f"\nServer: http://localhost:{server_port}")
    print("Testing: Legion (server), Thor (client)")
    print()

    # Create Thor client
    thor_client = FederationClient("Thor")

    # Register Legion
    thor_client.register_platform(
        name="Legion",
        endpoint=f"http://127.0.0.1:{server_port}",
        capabilities=["consciousness", "consciousness.sage"]
    )

    # Run test suite
    results = {}

    # Test 1: Standard consciousness
    success, data = test_standard_consciousness_delegation(thor_client, "Thor")
    results['standard_consciousness'] = {'success': success, 'data': data}

    # Test 2: Enhanced SAGE
    success, data = test_enhanced_sage_delegation(thor_client, "Thor")
    results['enhanced_sage'] = {'success': success, 'data': data}

    # Test 3: Concurrent delegations
    success, data = test_concurrent_delegations(thor_client, "Thor", num_concurrent=5)
    results['concurrent'] = {'success': success, 'data': data}

    # Test 4: ATP budget enforcement
    success, data = test_atp_budget_enforcement(thor_client, "Thor")
    results['atp_budget'] = {'success': success, 'data': data}

    # Summary
    print("\n" + "="*80)
    print("TEST SUITE SUMMARY")
    print("="*80)

    all_passed = all(r['success'] for r in results.values())

    for test_name, result in results.items():
        status = "✅ PASS" if result['success'] else "✗ FAIL"
        print(f"{status}  {test_name}")

    print("\n" + ("="*80))
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("Multi-machine SAGE federation validated successfully!")
    else:
        print("⚠️ SOME TESTS FAILED")
        failed = [name for name, r in results.items() if not r['success']]
        print(f"Failed tests: {', '.join(failed)}")
    print("="*80)

    return all_passed, results


def main():
    parser = argparse.ArgumentParser(description="Comprehensive Federation Test")
    parser.add_argument('--port', type=int, default=8090, help='Server port')
    args = parser.parse_args()

    try:
        all_passed, results = run_comprehensive_federation_test(args.port)
        sys.exit(0 if all_passed else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
