#!/usr/bin/env python3
"""
Federation Cryptography Test

Tests Ed25519 signing and verification for SAGE consciousness federation.

Usage:
    python3 game/test_federation_crypto.py

Author: Legion Autonomous Session #55
Date: 2025-12-03
"""

import sys
from pathlib import Path
import time
import tempfile

# Add web4 root to path
_web4_root = Path(__file__).parent.parent
if str(_web4_root) not in sys.path:
    sys.path.insert(0, str(_web4_root))

from game.server.federation_crypto import FederationCrypto, PlatformKeyManager
from game.server.federation_api import FederationTask, ExecutionProof


def test_keypair_generation():
    """Test 1: Ed25519 keypair generation"""
    print("\n" + "="*80)
    print("TEST 1: Ed25519 Keypair Generation")
    print("="*80)

    # Generate keypair
    private_key, public_key = FederationCrypto.generate_keypair()

    print(f"\n✅ Keypair generated successfully")
    print(f"  Private key type: {type(private_key).__name__}")
    print(f"  Public key type: {type(public_key).__name__}")

    # Verify keys are related
    test_message = b"test message"
    signature = private_key.sign(test_message)

    try:
        public_key.verify(signature, test_message)
        print(f"  ✅ Keys are properly related (signature verified)")
        return True
    except Exception as e:
        print(f"  ✗ Keys not properly related: {e}")
        return False


def test_task_signing():
    """Test 2: Federation task signing and verification"""
    print("\n" + "="*80)
    print("TEST 2: Federation Task Signing")
    print("="*80)

    # Generate keypair
    private_key, public_key = FederationCrypto.generate_keypair()

    # Create test task
    task = FederationTask(
        task_id="test_001",
        source_lct="lct:web4:agent:dp@Thor#consciousness",
        target_lct="lct:web4:agent:dp@Legion#consciousness",
        task_type="consciousness",
        operation="perception",
        atp_budget=50.0,
        timeout_seconds=60,
        parameters={"test": "data"},
        created_at=time.time()
    )

    # Sign task
    signature = FederationCrypto.sign_task(
        task.to_signable_dict(),
        private_key
    )

    print(f"\n✅ Task signed")
    print(f"  Task ID: {task.task_id}")
    print(f"  Signature length: {len(signature)} bytes")
    print(f"  Expected: 64 bytes (Ed25519)")

    # Verify signature
    valid = FederationCrypto.verify_task(
        task.to_signable_dict(),
        signature,
        public_key
    )

    if valid:
        print(f"  ✅ Signature verified successfully")
    else:
        print(f"  ✗ Signature verification failed")
        return False

    # Test invalid signature
    invalid_signature = b'x' * 64
    valid = FederationCrypto.verify_task(
        task.to_signable_dict(),
        invalid_signature,
        public_key
    )

    if not valid:
        print(f"  ✅ Invalid signature correctly rejected")
        return True
    else:
        print(f"  ✗ Invalid signature incorrectly accepted")
        return False


def test_proof_signing():
    """Test 3: Execution proof signing and verification"""
    print("\n" + "="*80)
    print("TEST 3: Execution Proof Signing")
    print("="*80)

    # Generate keypair
    private_key, public_key = FederationCrypto.generate_keypair()

    # Create test proof
    proof = ExecutionProof(
        task_id="test_001",
        executor_lct="lct:web4:agent:dp@Legion#consciousness",
        atp_consumed=5.0,
        execution_time=0.1,
        quality_score=0.95,
        result={"observations": ["test"]},
        created_at=time.time()
    )

    # Sign proof
    signature = FederationCrypto.sign_proof(
        proof.to_signable_dict(),
        private_key
    )

    print(f"\n✅ Proof signed")
    print(f"  Task ID: {proof.task_id}")
    print(f"  Signature length: {len(signature)} bytes")

    # Verify signature
    valid = FederationCrypto.verify_proof(
        proof.to_signable_dict(),
        signature,
        public_key
    )

    if valid:
        print(f"  ✅ Signature verified successfully")
    else:
        print(f"  ✗ Signature verification failed")
        return False

    # Test tampered proof
    tampered_proof = ExecutionProof(
        task_id=proof.task_id,
        executor_lct=proof.executor_lct,
        atp_consumed=proof.atp_consumed,
        execution_time=proof.execution_time,
        quality_score=0.99,  # Changed!
        result=proof.result,
        created_at=proof.created_at
    )

    valid = FederationCrypto.verify_proof(
        tampered_proof.to_signable_dict(),
        signature,
        public_key
    )

    if not valid:
        print(f"  ✅ Tampered proof correctly rejected")
        return True
    else:
        print(f"  ✗ Tampered proof incorrectly accepted")
        return False


def test_key_persistence():
    """Test 4: Key saving and loading"""
    print("\n" + "="*80)
    print("TEST 4: Key Persistence")
    print("="*80)

    # Use temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Generate and save keys
        private_key1, public_key1 = FederationCrypto.generate_keypair()
        private_path = temp_path / "test_private.pem"
        public_path = temp_path / "test_public.pem"

        FederationCrypto.save_keypair(private_key1, private_path)
        FederationCrypto.save_public_key(public_key1, public_path)

        print(f"\n✅ Keys saved")
        print(f"  Private key: {private_path}")
        print(f"  Public key: {public_path}")

        # Load keys
        private_key2 = FederationCrypto.load_private_key(private_path)
        public_key2 = FederationCrypto.load_public_key(public_path)

        print(f"  ✅ Keys loaded")

        # Test that loaded keys work
        test_message = b"persistence test"
        signature = private_key2.sign(test_message)

        try:
            public_key2.verify(signature, test_message)
            print(f"  ✅ Loaded keys work correctly")
            return True
        except Exception as e:
            print(f"  ✗ Loaded keys failed: {e}")
            return False


def test_platform_key_manager():
    """Test 5: Platform key manager"""
    print("\n" + "="*80)
    print("TEST 5: Platform Key Manager")
    print("="*80)

    # Use temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create key manager for "Legion"
        manager = PlatformKeyManager("Legion", keys_dir=temp_path)

        # Generate keys
        private_key, public_key = manager.generate_and_save_keys()

        print(f"\n✅ Platform keys generated")
        print(f"  Platform: {manager.platform_name}")
        print(f"  Private key path: {manager.private_key_path}")
        print(f"  Public key path: {manager.public_key_path}")

        # Create second manager instance (simulates restart)
        manager2 = PlatformKeyManager("Legion", keys_dir=temp_path)

        # Load existing keys
        private_key2, public_key2 = manager2.load_or_generate_keys()

        print(f"  ✅ Keys reloaded on new manager instance")

        # Test that they're the same keys
        test_message = b"key manager test"
        signature = private_key.sign(test_message)

        try:
            public_key2.verify(signature, test_message)
            print(f"  ✅ Reloaded keys match original")
            return True
        except Exception as e:
            print(f"  ✗ Reloaded keys don't match: {e}")
            return False


def test_performance():
    """Test 6: Performance benchmarking"""
    print("\n" + "="*80)
    print("TEST 6: Ed25519 Performance")
    print("="*80)

    # Generate keypair
    private_key, public_key = FederationCrypto.generate_keypair()

    # Create test task
    task = FederationTask(
        task_id="perf_test",
        source_lct="lct:web4:agent:dp@Thor#consciousness",
        target_lct="lct:web4:agent:dp@Legion#consciousness",
        task_type="consciousness",
        operation="perception",
        atp_budget=50.0,
        timeout_seconds=60,
        parameters={"test": "performance"},
        created_at=time.time()
    )

    task_dict = task.to_signable_dict()

    # Benchmark signing
    num_iterations = 1000
    start_time = time.time()
    for _ in range(num_iterations):
        signature = FederationCrypto.sign_task(task_dict, private_key)
    sign_time = time.time() - start_time
    sign_ops_per_sec = num_iterations / sign_time

    print(f"\n✅ Signing performance:")
    print(f"  Iterations: {num_iterations}")
    print(f"  Total time: {sign_time:.3f}s")
    print(f"  Ops/sec: {sign_ops_per_sec:.0f}")

    # Benchmark verification
    start_time = time.time()
    for _ in range(num_iterations):
        valid = FederationCrypto.verify_task(task_dict, signature, public_key)
    verify_time = time.time() - start_time
    verify_ops_per_sec = num_iterations / verify_time

    print(f"\n✅ Verification performance:")
    print(f"  Iterations: {num_iterations}")
    print(f"  Total time: {verify_time:.3f}s")
    print(f"  Ops/sec: {verify_ops_per_sec:.0f}")

    # Targets (based on Sprout's measurements)
    # Sprout (Jetson Orin Nano): 18,145 sign/sec, 7,047 verify/sec
    # Legion (RTX 4090) should exceed Sprout

    print(f"\n{'✅' if sign_ops_per_sec > 10000 else '⚠️'} Performance assessment:")
    print(f"  Signing: {'Excellent' if sign_ops_per_sec > 20000 else 'Good' if sign_ops_per_sec > 10000 else 'Acceptable'}")
    print(f"  Verification: {'Excellent' if verify_ops_per_sec > 5000 else 'Good' if verify_ops_per_sec > 2000 else 'Acceptable'}")

    return True


def main():
    """Run all cryptography tests"""
    print("\n" + "="*80)
    print("FEDERATION CRYPTOGRAPHY TEST SUITE")
    print("Ed25519 Signing and Verification")
    print("="*80)

    tests = [
        ("Keypair Generation", test_keypair_generation),
        ("Task Signing", test_task_signing),
        ("Proof Signing", test_proof_signing),
        ("Key Persistence", test_key_persistence),
        ("Platform Key Manager", test_platform_key_manager),
        ("Performance", test_performance)
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = success
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    for test_name, success in results.items():
        status = "✅ PASS" if success else "✗ FAIL"
        print(f"{status}  {test_name}")

    all_passed = all(results.values())
    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("Ed25519 cryptography ready for federation")
    else:
        print("⚠️ SOME TESTS FAILED")
    print("="*80)

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
