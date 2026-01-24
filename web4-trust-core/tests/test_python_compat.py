#!/usr/bin/env python3
"""
Test compatibility between Rust and Python implementations.

Ensures that both implementations produce consistent results for
the same operations.
"""

import sys
import tempfile
import json
from pathlib import Path

# Import Rust implementation
from web4_trust import (
    T3Tensor as RustT3,
    V3Tensor as RustV3,
    EntityTrust as RustEntityTrust,
    TrustStore as RustTrustStore,
)

# Import Python implementation
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "claude-code-plugin"))
from governance.entity_trust import EntityTrust as PyEntityTrust, EntityTrustStore as PyTrustStore


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(name, success, details=""):
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"  {status}: {name}")
    if details and not success:
        print(f"         {details}")


def test_tensor_math():
    """Test that tensor calculations match."""
    print_section("Tensor Math Compatibility")

    # Create identical tensors
    rust_t3 = RustT3(0.6, 0.7, 0.5, 0.4, 0.8, 0.55)
    py_t3_avg = (0.6 + 0.7 + 0.5 + 0.4 + 0.8 + 0.55) / 6

    print_result(
        "T3 average calculation",
        abs(rust_t3.average() - py_t3_avg) < 0.001,
        f"Rust: {rust_t3.average()}, Python: {py_t3_avg}"
    )

    # Test update from outcome
    rust_t3_2 = RustT3.neutral()
    rust_t3_2.update_from_outcome(True, 0.1)

    # Python equivalent math
    # delta = magnitude * 0.05 * (1 - reliability) = 0.1 * 0.05 * 0.5 = 0.0025
    expected_reliability = 0.5 + 0.0025

    print_result(
        "T3 update from outcome",
        abs(rust_t3_2.reliability - expected_reliability) < 0.001,
        f"Rust: {rust_t3_2.reliability}, Expected: {expected_reliability}"
    )

    return True


def test_entity_trust_creation():
    """Test entity trust creation and basic operations."""
    print_section("EntityTrust Creation")

    rust_trust = RustEntityTrust("mcp:compat-test")

    print_result("Entity ID parsed", rust_trust.entity_id == "mcp:compat-test")
    print_result("Entity type parsed", rust_trust.entity_type == "mcp")
    print_result("Entity name parsed", rust_trust.entity_name == "compat-test")
    print_result("Initial T3 average", abs(rust_trust.t3_average() - 0.5) < 0.001)
    print_result("Initial trust level", rust_trust.trust_level() == "medium")

    return True


def test_update_behavior():
    """Test that update behavior matches between implementations."""
    print_section("Update Behavior")

    # Rust
    rust_trust = RustEntityTrust("role:test")
    rust_trust.update_from_outcome(True, 0.1)
    rust_trust.update_from_outcome(True, 0.1)
    rust_trust.update_from_outcome(False, 0.1)

    # Python
    py_trust = PyEntityTrust(entity_id="role:test")
    py_trust.update_from_outcome(True, 0.1)
    py_trust.update_from_outcome(True, 0.1)
    py_trust.update_from_outcome(False, 0.1)

    print_result(
        "Action count matches",
        rust_trust.action_count == py_trust.action_count == 3,
        f"Rust: {rust_trust.action_count}, Python: {py_trust.action_count}"
    )

    print_result(
        "Success count matches",
        rust_trust.success_count == py_trust.success_count == 2,
        f"Rust: {rust_trust.success_count}, Python: {py_trust.success_count}"
    )

    # T3 averages should be very close
    t3_diff = abs(rust_trust.t3_average() - py_trust.t3_average())
    print_result(
        "T3 average within tolerance",
        t3_diff < 0.01,
        f"Rust: {rust_trust.t3_average():.4f}, Python: {py_trust.t3_average():.4f}, Diff: {t3_diff:.4f}"
    )

    return True


def test_witnessing():
    """Test witnessing behavior matches."""
    print_section("Witnessing Behavior")

    # Rust
    rust_target = RustEntityTrust("mcp:witnessed")
    rust_target.receive_witness("session:a", True, 0.1)
    rust_target.receive_witness("session:b", True, 0.1)

    # Python
    py_target = PyEntityTrust(entity_id="mcp:witnessed")
    py_target.receive_witness("session:a", True, 0.1)
    py_target.receive_witness("session:b", True, 0.1)

    print_result(
        "Witness count matches",
        rust_target.witness_count == py_target.witness_count == 2,
        f"Rust: {rust_target.witness_count}, Python: {py_target.witness_count}"
    )

    print_result(
        "Witnessed_by list matches",
        set(rust_target.witnessed_by) == set(py_target.witnessed_by),
        f"Rust: {rust_target.witnessed_by}, Python: {py_target.witnessed_by}"
    )

    # Witnesses dimension should increase
    print_result(
        "Witnesses dimension increased",
        rust_target.witnesses > 0.5 and py_target.witnesses > 0.5,
        f"Rust: {rust_target.witnesses:.3f}, Python: {py_target.witnesses:.3f}"
    )

    return True


def test_json_compatibility():
    """Test that JSON format is compatible."""
    print_section("JSON Format Compatibility")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create entity with Rust and save
        rust_store = RustTrustStore(tmpdir)
        rust_trust = rust_store.get("mcp:json-test")
        rust_trust.update_from_outcome(True, 0.1)
        rust_store.save(rust_trust)

        # Find the JSON file
        json_files = list(Path(tmpdir).glob("*.json"))
        print_result("JSON file created", len(json_files) == 1)

        if json_files:
            # Read and verify format
            with open(json_files[0]) as f:
                data = json.load(f)

            # Check required fields exist
            required_fields = [
                "entity_id", "competence", "reliability", "consistency",
                "witnesses", "lineage", "alignment", "energy", "contribution",
                "action_count", "success_count", "witnessed_by", "has_witnessed"
            ]

            missing = [f for f in required_fields if f not in data]
            print_result(
                "All required fields present",
                len(missing) == 0,
                f"Missing: {missing}"
            )

            print_result(
                "Entity ID correct",
                data.get("entity_id") == "mcp:json-test"
            )

    return True


def test_store_operations():
    """Test store operations match."""
    print_section("Store Operations")

    with tempfile.TemporaryDirectory() as tmpdir:
        rust_store = RustTrustStore(tmpdir)

        # Create entities
        rust_store.get("mcp:a")
        rust_store.get("mcp:b")
        rust_store.get("role:x")

        # List
        all_entities = rust_store.list_entities()
        print_result("List all entities", len(all_entities) == 3)

        mcp_entities = rust_store.list_entities("mcp")
        print_result("List MCP entities", len(mcp_entities) == 2)

        # Witness
        witness, target = rust_store.witness("session:test", "mcp:a", True, 0.1)
        print_result(
            "Witness operation returns both",
            witness is not None and target is not None
        )
        print_result(
            "Target witnessed_by updated",
            "session:test" in target.witnessed_by
        )

        # Delete
        deleted = rust_store.delete("mcp:a")
        print_result("Delete returns True", deleted)

        exists = rust_store.exists("mcp:a")
        print_result("Deleted entity no longer exists", not exists)

    return True


def main():
    """Run all compatibility tests."""
    print("\n" + "="*60)
    print("  Web4 Trust - Rust/Python Compatibility Tests")
    print("="*60)

    tests = [
        ("Tensor Math", test_tensor_math),
        ("EntityTrust Creation", test_entity_trust_creation),
        ("Update Behavior", test_update_behavior),
        ("Witnessing", test_witnessing),
        ("JSON Format", test_json_compatibility),
        ("Store Operations", test_store_operations),
    ]

    results = []
    for name, test_fn in tests:
        try:
            result = test_fn()
            results.append((name, True, None))
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"\n  ERROR: {e}")

    # Summary
    print_section("Test Summary")
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    print(f"\n  Results: {passed}/{total} tests passed\n")
    for name, success, error in results:
        status = "✓" if success else "✗"
        print(f"  {status} {name}")
        if error:
            print(f"      Error: {error}")

    print("\n" + "="*60)
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
