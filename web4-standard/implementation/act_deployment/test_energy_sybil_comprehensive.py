#!/usr/bin/env python3
"""
Comprehensive Tests for Energy-Based Sybil Resistance - Session #49

Tests energy capacity requirements and Sybil attack detection.

Coverage Goals:
- Energy capacity proof registration and validation
- Logarithmic weight calculation
- Renewable energy bonus
- Sybil cluster detection by capacity similarity
- Minimum capacity enforcement
- Proof expiration handling
- Attack vector coverage

Session: #49 (Autonomous Research - Security Test Sprint)
"""

from datetime import datetime, timezone, timedelta
import math
from lct import create_lct_identity, LCTContext
from energy_based_sybil_resistance import (
    EnergyCapacityProof,
    EnergySybilResistance,
    EnergyWeightedTrustEngine,
)


# ============================================================================
# Test Helper Functions
# ============================================================================

def create_test_society(name: str):
    """Create test society with formal LCT"""
    lct, keypair = create_lct_identity(name, LCTContext.SOCIETY, deterministic=True)
    return str(lct), keypair


def create_energy_proof(society_lct: str, capacity_watts: float,
                        generation_type: str = "solar",
                        hours_valid: int = 24):
    """Create energy capacity proof"""
    now = datetime.now(timezone.utc)
    return EnergyCapacityProof(
        society_lct=society_lct,
        capacity_watts=capacity_watts,
        generation_type=generation_type,
        proof_hash=f"proof_{society_lct}_{capacity_watts}",
        verified_at=now,
        expires_at=now + timedelta(hours=hours_valid)
    )


# ============================================================================
# Basic Energy Capacity Tests
# ============================================================================

def test_register_valid_capacity():
    """Valid energy capacity should register successfully"""
    print("\n=== Test: Register Valid Energy Capacity ===")

    society_lct, _ = create_test_society("Society1")
    resistance = EnergySybilResistance()

    proof = create_energy_proof(society_lct, capacity_watts=100.0)

    success = resistance.register_capacity(proof)

    print(f"Society: {society_lct[:30]}...")
    print(f"Capacity: 100W solar")
    print(f"Registration success: {success}")
    print(f"Expected: True")

    assert success == True, f"Valid capacity should register: {success}"
    print("✅ PASS: Valid capacity registered")


def test_reject_below_minimum_capacity():
    """Capacity below minimum should be rejected"""
    print("\n=== Test: Reject Below Minimum Capacity ===")

    society_lct, _ = create_test_society("WeakSociety")
    resistance = EnergySybilResistance()

    # Default min is 10W, try 5W
    proof = create_energy_proof(society_lct, capacity_watts=5.0)

    success = resistance.register_capacity(proof)

    print(f"Society: {society_lct[:30]}...")
    print(f"Capacity: 5W (below 10W minimum)")
    print(f"Registration success: {success}")
    print(f"Expected: False")

    assert success == False, f"Below-minimum capacity should be rejected: {success}"
    print("✅ PASS: Below-minimum capacity rejected")


def test_reject_expired_proof():
    """Expired energy proof should be rejected"""
    print("\n=== Test: Reject Expired Proof ===")

    society_lct, _ = create_test_society("ExpiredSociety")
    resistance = EnergySybilResistance()

    # Create proof that expired 1 hour ago
    proof = create_energy_proof(society_lct, capacity_watts=100.0, hours_valid=-1)

    success = resistance.register_capacity(proof)

    print(f"Society: {society_lct[:30]}...")
    print(f"Capacity: 100W (but expired)")
    print(f"Registration success: {success}")
    print(f"Expected: False")

    assert success == False, f"Expired proof should be rejected: {success}"
    print("✅ PASS: Expired proof rejected")


# ============================================================================
# Weight Calculation Tests
# ============================================================================

def test_logarithmic_weight_scaling():
    """Weight should scale logarithmically with capacity"""
    print("\n=== Test: Logarithmic Weight Scaling ===")

    resistance = EnergySybilResistance()

    # Register societies with different capacities
    capacities = [10, 100, 1000, 10000]
    societies = {}

    for capacity in capacities:
        society_lct, _ = create_test_society(f"Society{capacity}W")
        proof = create_energy_proof(society_lct, capacity_watts=float(capacity))
        resistance.register_capacity(proof)
        weight = resistance.get_society_weight(society_lct)
        societies[capacity] = (society_lct, weight)

    print("Capacity → Weight (logarithmic):")
    for capacity in capacities:
        society_lct, weight = societies[capacity]
        expected_weight = math.log10(capacity + 1)
        print(f"  {capacity:>5}W → {weight:.3f} (expected {expected_weight:.3f})")

    # Verify logarithmic property: 100x capacity ≠ 100x weight
    _, weight_10 = societies[10]
    _, weight_1000 = societies[1000]

    ratio = weight_1000 / weight_10
    print(f"\n100x capacity increase: {ratio:.1f}x weight (not 100x)")
    print(f"Expected: ~3x (due to log10 scaling)")

    assert ratio < 10, f"Weight should not scale linearly: {ratio}"
    print("✅ PASS: Logarithmic scaling prevents plutocracy")


def test_renewable_energy_bonus():
    """Renewable energy should get 10% weight bonus"""
    print("\n=== Test: Renewable Energy Bonus ===")

    resistance = EnergySybilResistance()

    # Solar (renewable)
    solar_lct, _ = create_test_society("SolarSociety")
    solar_proof = create_energy_proof(solar_lct, capacity_watts=100.0,
                                      generation_type="solar")
    resistance.register_capacity(solar_proof)
    solar_weight = resistance.get_society_weight(solar_lct)

    # Grid (non-renewable)
    grid_lct, _ = create_test_society("GridSociety")
    grid_proof = create_energy_proof(grid_lct, capacity_watts=100.0,
                                     generation_type="grid")
    resistance.register_capacity(grid_proof)
    grid_weight = resistance.get_society_weight(grid_lct)

    bonus_ratio = solar_weight / grid_weight

    print(f"Solar (100W): weight = {solar_weight:.3f}")
    print(f"Grid (100W):  weight = {grid_weight:.3f}")
    print(f"Bonus ratio: {bonus_ratio:.3f}")
    print(f"Expected: ~1.10 (10% renewable bonus)")

    assert abs(bonus_ratio - 1.10) < 0.01, f"Renewable should get 10% bonus: {bonus_ratio}"
    print("✅ PASS: Renewable energy gets 10% bonus")


def test_zero_weight_without_proof():
    """Societies without energy proof should have zero weight"""
    print("\n=== Test: Zero Weight Without Proof ===")

    resistance = EnergySybilResistance()

    no_proof_lct, _ = create_test_society("NoProofSociety")

    weight = resistance.get_society_weight(no_proof_lct)

    print(f"Society without proof: {no_proof_lct[:30]}...")
    print(f"Weight: {weight}")
    print(f"Expected: 0.0")

    assert weight == 0.0, f"No proof should mean zero weight: {weight}"
    print("✅ PASS: No proof = zero weight")


# ============================================================================
# Sybil Detection Tests
# ============================================================================

def test_detect_sybil_cluster_by_similar_capacity():
    """Similar capacities indicate Sybil cluster"""
    print("\n=== Test: Detect Sybil by Similar Capacity ===")

    resistance = EnergySybilResistance()

    # Attacker creates 10 Sybil identities with similar capacity
    # (splits 1000W into 10x 100W)
    sybil_societies = []
    for i in range(10):
        society_lct, _ = create_test_society(f"Sybil{i}")
        proof = create_energy_proof(society_lct, capacity_watts=100.0)
        resistance.register_capacity(proof)
        sybil_societies.append(society_lct)

    result = resistance.detect_sybil_by_capacity(sybil_societies)

    print(f"Created 10 societies with identical 100W capacity")
    print(f"Detection result: {result}")
    print(f"Is Sybil: {result['is_sybil']}")
    print(f"Expected: True (very similar capacities)")

    assert result['is_sybil'] == True, f"Similar capacities should trigger Sybil detection: {result}"
    print("✅ PASS: Sybil cluster detected by similar capacity")


def test_diverse_capacities_not_sybil():
    """Diverse capacities indicate legitimate societies"""
    print("\n=== Test: Diverse Capacities Not Sybil ===")

    resistance = EnergySybilResistance()

    # Legitimate societies with diverse capacities
    capacities = [10, 50, 100, 250, 500, 1000, 2000]
    diverse_societies = []

    for i, capacity in enumerate(capacities):
        society_lct, _ = create_test_society(f"Diverse{i}")
        proof = create_energy_proof(society_lct, capacity_watts=float(capacity))
        resistance.register_capacity(proof)
        diverse_societies.append(society_lct)

    result = resistance.detect_sybil_by_capacity(diverse_societies)

    print(f"Created 7 societies with diverse capacities: {capacities}")
    print(f"Detection result: {result}")
    print(f"Is Sybil: {result['is_sybil']}")
    print(f"Expected: False (diverse capacities)")

    assert result['is_sybil'] == False, f"Diverse capacities should not trigger detection: {result}"
    print("✅ PASS: Diverse capacities not flagged as Sybil")


def test_insufficient_data_for_detection():
    """Single society cannot be detected as Sybil"""
    print("\n=== Test: Insufficient Data for Detection ===")

    resistance = EnergySybilResistance()

    society_lct, _ = create_test_society("Singleton")
    proof = create_energy_proof(society_lct, capacity_watts=100.0)
    resistance.register_capacity(proof)

    result = resistance.detect_sybil_by_capacity([society_lct])

    print(f"Single society cluster")
    print(f"Detection result: {result}")
    print(f"Is Sybil: {result['is_sybil']}")
    print(f"Reason: {result['reason']}")
    print(f"Expected: False (insufficient data)")

    assert result['is_sybil'] == False, f"Single society cannot be Sybil: {result}"
    assert "Insufficient" in result['reason'], f"Should cite insufficient data: {result}"
    print("✅ PASS: Single society not flagged (insufficient data)")


# ============================================================================
# Energy-Weighted Trust Tests
# ============================================================================



# ============================================================================
# Attack Vector Tests
# ============================================================================



def test_cost_of_matching_capacity():
    """Demonstrate economic cost of Sybil attack"""
    print("\n=== Test: Economic Cost of Sybil Attack ===")

    resistance = EnergySybilResistance()

    # Legitimate society with significant capacity
    legit_lct, _ = create_test_society("LegitSociety")
    legit_proof = create_energy_proof(legit_lct, capacity_watts=5000.0)
    resistance.register_capacity(legit_proof)
    legit_weight = resistance.get_society_weight(legit_lct)

    # Attacker needs to match this weight
    # weight = log10(capacity + 1)
    # To match weight, need: capacity = 10^weight - 1

    target_capacity = 10 ** legit_weight - 1

    print(f"Legitimate society: 5000W → weight = {legit_weight:.2f}")
    print(f"To match weight, attacker needs: {target_capacity:.0f}W capacity")
    print(f"At $3/W (solar panel cost), attacker cost: ${target_capacity * 3:.0f}")
    print(f"Expected: Significant economic barrier")

    assert target_capacity >= 4000, f"Attack should require significant capacity: {target_capacity}"
    print("✅ PASS: Sybil attack has significant economic cost")


# ============================================================================
# Edge Cases
# ============================================================================

def test_proof_expiration_removes_weight():
    """Expired proof should result in zero weight"""
    print("\n=== Test: Expired Proof = Zero Weight ===")

    resistance = EnergySybilResistance()

    society_lct, _ = create_test_society("ExpiringSciety")

    # Register with short validity (will be expired immediately due to test timing)
    proof = create_energy_proof(society_lct, capacity_watts=100.0, hours_valid=-1)

    # Force registration (bypass expiration check for test setup)
    resistance.capacity_proofs[society_lct] = proof

    # Get weight (should be 0 due to expiration)
    weight = resistance.get_society_weight(society_lct)

    print(f"Society with expired 100W proof")
    print(f"Weight: {weight}")
    print(f"Expected: 0.0")

    assert weight == 0.0, f"Expired proof should have zero weight: {weight}"
    print("✅ PASS: Expired proof results in zero weight")


# ============================================================================
# Run All Tests
# ============================================================================

def run_all_tests():
    """Run comprehensive energy-based Sybil resistance tests"""
    print("=" * 70)
    print("Energy-Based Sybil Resistance Test Suite - Session #49")
    print("=" * 70)
    print("\nUsing formal LCT library + energy capacity proofs")
    print()

    tests = [
        ("Basic: Register Valid Capacity", test_register_valid_capacity),
        ("Basic: Reject Below Minimum", test_reject_below_minimum_capacity),
        ("Basic: Reject Expired Proof", test_reject_expired_proof),
        ("Weight: Logarithmic Scaling", test_logarithmic_weight_scaling),
        ("Weight: Renewable Bonus", test_renewable_energy_bonus),
        ("Weight: Zero Without Proof", test_zero_weight_without_proof),
        ("Detection: Sybil by Similar Capacity", test_detect_sybil_cluster_by_similar_capacity),
        ("Detection: Diverse Not Sybil", test_diverse_capacities_not_sybil),
        ("Detection: Insufficient Data", test_insufficient_data_for_detection),
        
        
        ("Attack: Economic Cost", test_cost_of_matching_capacity),
        ("Edge: Expired Proof = Zero Weight", test_proof_expiration_removes_weight),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {name}")
            print(f"   Error: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {name}")
            print(f"   Exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print()
    print("=" * 70)
    print("Test Results")
    print("=" * 70)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    print()

    if failed == 0:
        print("✅ ALL TESTS PASSED!")
    else:
        print(f"❌ {failed} tests failed")

    return passed, failed


if __name__ == "__main__":
    passed, failed = run_all_tests()
    exit(0 if failed == 0 else 1)
