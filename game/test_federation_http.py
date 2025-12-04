#!/usr/bin/env python3
"""
Quick HTTP Federation Test

Tests the running federation server with HTTP client.

Usage:
    python3 game/test_federation_http.py [--port PORT]
"""

import sys
from pathlib import Path
import argparse

# Add web4 root to path
_web4_root = Path(__file__).parent.parent
if str(_web4_root) not in sys.path:
    sys.path.insert(0, str(_web4_root))

from game.client.federation_client import FederationClient
from game.engine.sage_lct_integration import SAGELCTManager


def main():
    parser = argparse.ArgumentParser(description="Test Federation HTTP")
    parser.add_argument('--port', type=int, default=8090, help='Server port')
    args = parser.parse_args()

    print("="*80)
    print("FEDERATION HTTP TEST")
    print("="*80)
    print(f"\nTesting against server at localhost:{args.port}")

    # Test 1: Health check
    print("\n" + "="*80)
    print("TEST 1: Health Check")
    print("="*80)
    import requests
    response = requests.get(f"http://127.0.0.1:{args.port}/api/v1/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    # Test 2: Basic delegation
    print("\n" + "="*80)
    print("TEST 2: Basic Task Delegation (Thor → Legion)")
    print("="*80)

    # Create Thor client
    thor_client = FederationClient("Thor")

    # Register Legion as remote platform
    thor_client.register_platform(
        name="Legion",
        endpoint=f"http://127.0.0.1:{args.port}",
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


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
