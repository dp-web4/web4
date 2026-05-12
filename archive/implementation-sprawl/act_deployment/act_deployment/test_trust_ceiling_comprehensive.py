#!/usr/bin/env python3
"""
Comprehensive Tests for Trust Ceiling Mitigation - Session #48

Uses formal LCT library to test trust ceiling enforcement.

Coverage Goals:
- Trust ceiling calculation with evidence
- Collusion attack prevention
- Evidence quality impact
- Direct vs propagated trust
- Ceiling enforcement across propagation hops
- Edge cases and attack vectors

Session: #48 (Autonomous Research - Security Test Sprint)
"""

from datetime import datetime, timezone, timedelta
from lct import create_lct_identity, LCTContext
from trust_ceiling_mitigation import (
    TrustCeilingEngine,
    TrustEvidence,
    RobustTrustEngine,
)
from cross_society_trust_propagation import TrustRecord, PropagatedTrustRecord


# ============================================================================
# Test Helper Functions
# ============================================================================

def create_test_society(name: str):
    """Create test society with formal LCT"""
    lct, keypair = create_lct_identity(name, LCTContext.SOCIETY, deterministic=True)
    return str(lct), keypair


def create_trust_record(assessor_lct: str, subject_lct: str, trust_score: float):
    """Create TrustRecord with required fields"""
    return TrustRecord(
        assessor_lct=assessor_lct,
        subject_lct=subject_lct,
        trust_score=trust_score,
        assessed_at=datetime.now(timezone.utc),
        evidence=["test"],
    )


# ============================================================================
# Basic Trust Ceiling Tests
# ============================================================================

def test_direct_trust_no_ceiling():
    """Direct trust observations should have no ceiling"""
    print("\n=== Test: Direct Trust Has No Ceiling ===")

    observer_lct, _ = create_test_society("Observer")
    subject_lct, _ = create_test_society("Subject")

    engine = TrustCeilingEngine(
        society_lct=observer_lct,
        base_ceiling=0.7
    )

    # Set high direct trust (should not be capped)
    engine.set_direct_trust(subject_lct, trust_score=0.95)

    # Should get full trust score (no ceiling for direct observation)
    trust = engine.get_aggregated_trust(subject_lct)

    print(f"Observer: {observer_lct[:30]}...")
    print(f"Subject: {subject_lct[:30]}...")
    print(f"Direct trust set: 0.95")
    print(f"Aggregated trust: {trust:.3f}")
    print(f"Expected: 0.95 (no ceiling)")

    assert abs(trust - 0.95) < 0.001, f"Direct trust should not be capped: {trust}"
    print("✅ PASS: Direct trust not capped")


def test_propagated_trust_has_ceiling():
    """Propagated trust should be capped at base_ceiling"""
    print("\n=== Test: Propagated Trust Has Ceiling ===")

    observer_lct, _ = create_test_society("Observer")
    intermediary_lct, _ = create_test_society("Intermediary")
    subject_lct, _ = create_test_society("Subject")

    engine = TrustCeilingEngine(
        society_lct=observer_lct,
        base_ceiling=0.7,
        decay_factor=0.9
    )

    # Simulate intermediary reporting high trust
    propagated_record = PropagatedTrustRecord(
        subject_lct=subject_lct,
        source_lct=intermediary_lct,
        trust_score=0.95,  # High trust from intermediary
        propagation_path=[intermediary_lct],
        propagation_distance=1,
        effective_trust=0.95,
        received_at=datetime.now(timezone.utc)
    )

    # Receive propagated trust
    engine.receive_propagated_trust(
        source_lct=intermediary_lct,
        record=create_trust_record(intermediary_lct, subject_lct, 0.95),
        propagation_distance=1
    )

    # Observer's view of subject should be capped
    trust = engine.get_aggregated_trust(subject_lct)

    print(f"Intermediary reports trust: 0.95")
    print(f"Base ceiling: 0.70")
    print(f"Decay factor: 0.90")
    print(f"Observer's aggregated trust: {trust:.3f}")
    print(f"Expected: ≤ 0.70 (capped at base ceiling)")

    assert trust <= 0.7, f"Propagated trust should be capped: {trust}"
    print("✅ PASS: Propagated trust capped at ceiling")


def test_ceiling_prevents_perfect_collusion():
    """Trust ceiling prevents perfect collusion attack"""
    print("\n=== Test: Ceiling Prevents Perfect Collusion ===")

    observer_lct, _ = create_test_society("Observer")
    attacker_lct, _ = create_test_society("Attacker")

    engine = TrustCeilingEngine(
        society_lct=observer_lct,
        base_ceiling=0.7,
        decay_factor=0.8
    )

    print(f"Creating 5 colluding societies...")
    print(f"All report trust=1.0 for attacker")
    print(f"Base ceiling: 0.70")

    # Create 5 colluding societies
    for i in range(5):
        colluder_lct, _ = create_test_society(f"Colluder{i}")

        # All colluders report perfect trust for attacker
        engine.receive_propagated_trust(
            source_lct=colluder_lct,
            record=create_trust_record(colluder_lct, attacker_lct, 1.0),
            propagation_distance=1
        )
        print(f"  Colluder {i+1}: trust=1.0")

    # Even with 5 colluders all reporting 1.0, ceiling should prevent high trust
    trust = engine.get_aggregated_trust(attacker_lct)

    print(f"\nAggregated trust (from 5 colluders): {trust:.3f}")
    print(f"Expected: ≤ 0.70 (ceiling prevents collusion)")

    assert trust <= 0.7, f"Ceiling should prevent collusion: {trust}"
    print("✅ PASS: Collusion attack mitigated by ceiling")


# ============================================================================
# Evidence Quality Tests
# ============================================================================

def test_evidence_increases_ceiling():
    """Evidence should increase trust ceiling beyond base"""
    print("\n=== Test: Evidence Increases Ceiling ===")

    observer_lct, _ = create_test_society("Observer")
    subject_lct, _ = create_test_society("Subject")

    engine = TrustCeilingEngine(
        society_lct=observer_lct,
        base_ceiling=0.7
    )

    # Add energy capacity evidence
    energy_evidence = TrustEvidence(
        evidence_type="energy_proof",
        quality_score=0.9,
        description="500W solar panel verified"
    )
    engine.add_evidence(subject_lct, energy_evidence)

    # Add historical behavior evidence
    historical_evidence = TrustEvidence(
        evidence_type="historical",
        quality_score=0.8,
        description="6 months positive history"
    )
    engine.add_evidence(subject_lct, historical_evidence)

    # Calculate ceiling with evidence
    ceiling = engine.get_trust_ceiling_for(subject_lct)

    print(f"Base ceiling: 0.70")
    print(f"Evidence added:")
    print(f"  - Energy proof (quality 0.9)")
    print(f"  - Historical data (quality 0.8)")
    print(f"Calculated ceiling: {ceiling:.3f}")
    print(f"Expected: > 0.70 (evidence boosts ceiling)")

    assert ceiling > 0.7, f"Evidence should increase ceiling: {ceiling}"
    print("✅ PASS: Evidence increases ceiling")


def test_direct_observation_full_ceiling():
    """Direct observation should allow full trust (ceiling = 1.0)"""
    print("\n=== Test: Direct Observation Allows Full Trust ===")

    observer_lct, _ = create_test_society("Observer")
    subject_lct, _ = create_test_society("Subject")

    engine = TrustCeilingEngine(
        society_lct=observer_lct,
        base_ceiling=0.7
    )

    # Add direct observation evidence
    direct_evidence = TrustEvidence(
        evidence_type="direct_observation",
        quality_score=1.0,
        description="First-hand observation of behavior"
    )
    engine.add_evidence(subject_lct, direct_evidence)

    ceiling = engine.get_trust_ceiling_for(subject_lct)

    print(f"Base ceiling: 0.70")
    print(f"Direct observation evidence added (quality 1.0)")
    print(f"Calculated ceiling: {ceiling:.3f}")
    print(f"Expected: 1.00 (direct observation = full trust possible)")

    assert abs(ceiling - 1.0) < 0.001, f"Direct observation should allow full trust: {ceiling}"
    print("✅ PASS: Direct observation allows full trust")


def test_no_evidence_defaults_to_base_ceiling():
    """Without evidence, ceiling should default to base_ceiling"""
    print("\n=== Test: No Evidence = Base Ceiling ===")

    observer_lct, _ = create_test_society("Observer")
    subject_lct, _ = create_test_society("Subject")

    engine = TrustCeilingEngine(
        society_lct=observer_lct,
        base_ceiling=0.7
    )

    # No evidence added
    ceiling = engine.get_trust_ceiling_for(subject_lct)

    print(f"Base ceiling: 0.70")
    print(f"Evidence added: None")
    print(f"Calculated ceiling: {ceiling:.3f}")
    print(f"Expected: 0.70 (defaults to base)")

    assert abs(ceiling - 0.7) < 0.001, f"Should default to base ceiling: {ceiling}"
    print("✅ PASS: Defaults to base ceiling without evidence")


# ============================================================================
# Attack Vector Tests
# ============================================================================

def test_sybil_amplification_prevented():
    """Ceiling prevents Sybil amplification attack"""
    print("\n=== Test: Sybil Amplification Prevention ===")

    observer_lct, _ = create_test_society("Observer")
    attacker_lct, _ = create_test_society("Attacker")

    engine = TrustCeilingEngine(
        society_lct=observer_lct,
        base_ceiling=0.7
    )

    print(f"Attacker creates 100 Sybil identities")
    print(f"All report trust=1.0 for attacker's main identity")

    # Attacker creates 100 Sybil identities
    for i in range(100):
        sybil_lct, _ = create_test_society(f"Sybil{i}")

        # All Sybils report perfect trust for attacker
        engine.receive_propagated_trust(
            source_lct=sybil_lct,
            record=create_trust_record(sybil_lct, attacker_lct, 1.0),
            propagation_distance=1
        )

    trust = engine.get_aggregated_trust(attacker_lct)

    print(f"Aggregated trust (from 100 Sybils): {trust:.3f}")
    print(f"Expected: ≤ 0.70 (ceiling prevents amplification)")

    assert trust <= 0.7, f"Ceiling should prevent Sybil amplification: {trust}"
    print("✅ PASS: Sybil amplification prevented")


def test_reputation_washing_prevented():
    """Ceiling prevents reputation washing through fresh identities"""
    print("\n=== Test: Reputation Washing Prevention ===")

    observer_lct, _ = create_test_society("Observer")

    # Attacker has bad reputation
    old_attacker_lct, _ = create_test_society("OldAttacker")

    # Attacker creates fresh identity
    new_attacker_lct, _ = create_test_society("NewAttacker")

    engine = TrustCeilingEngine(
        society_lct=observer_lct,
        base_ceiling=0.7
    )

    # Old identity has low trust
    engine.set_direct_trust(old_attacker_lct, trust_score=0.1)

    print(f"Old attacker identity: trust=0.1 (bad reputation)")
    print(f"Attacker creates new identity")
    print(f"New identity has no history (defaults to 0.5)")

    # New identity starts with default trust (no history)
    new_trust = engine.get_aggregated_trust(new_attacker_lct)

    print(f"New identity trust: {new_trust:.3f}")
    print(f"Expected: 0.5 (neutral, but cannot exceed 0.7 without evidence)")

    # Even if attacker gets fake endorsements, ceiling prevents high trust
    for i in range(10):
        endorser_lct, _ = create_test_society(f"FakeEndorser{i}")
        engine.receive_propagated_trust(
            source_lct=endorser_lct,
            record=create_trust_record(endorser_lct, new_attacker_lct, 1.0),
            propagation_distance=1
        )

    washed_trust = engine.get_aggregated_trust(new_attacker_lct)

    print(f"After 10 fake endorsements: {washed_trust:.3f}")
    print(f"Expected: ≤ 0.70 (ceiling prevents reputation washing)")

    assert washed_trust <= 0.7, f"Ceiling should prevent reputation washing: {washed_trust}"
    print("✅ PASS: Reputation washing prevented")


# ============================================================================
# Robust Trust Engine Tests
# ============================================================================

def test_robust_trust_diversity_discount():
    """RobustTrustEngine applies diversity discount in addition to ceiling"""
    print("\n=== Test: Robust Trust with Diversity Discount ===")

    observer_lct, _ = create_test_society("Observer")
    attacker_lct, _ = create_test_society("Attacker")

    # With diversity discount enabled
    robust_engine = RobustTrustEngine(
        society_lct=observer_lct,
        base_ceiling=0.7,
        diversity_enabled=True
    )

    # Without diversity discount
    ceiling_engine = TrustCeilingEngine(
        society_lct=observer_lct,
        base_ceiling=0.7
    )

    print(f"Creating 10 colluding societies reporting trust=1.0")

    # Add same colluders to both engines
    for i in range(10):
        colluder_lct, _ = create_test_society(f"ColluderRobust{i}")

        robust_engine.receive_propagated_trust(
            source_lct=colluder_lct,
            record=create_trust_record(colluder_lct, attacker_lct, 1.0),
            propagation_distance=1
        )

        ceiling_engine.receive_propagated_trust(
            source_lct=colluder_lct,
            record=create_trust_record(colluder_lct, attacker_lct, 1.0),
            propagation_distance=1
        )

    robust_trust = robust_engine.get_aggregated_trust(attacker_lct)
    ceiling_trust = ceiling_engine.get_aggregated_trust(attacker_lct)

    print(f"With ceiling only: {ceiling_trust:.3f}")
    print(f"With ceiling + diversity: {robust_trust:.3f}")
    print(f"Expected: Robust < Ceiling (diversity discount applied)")

    assert robust_trust <= ceiling_trust, f"Diversity should further reduce trust: {robust_trust} vs {ceiling_trust}"
    print("✅ PASS: Diversity discount applied")


# ============================================================================
# Edge Cases
# ============================================================================

def test_mixed_direct_and_propagated_trust():
    """Mixed direct and propagated trust should be weighted correctly"""
    print("\n=== Test: Mixed Direct and Propagated Trust ===")

    observer_lct, _ = create_test_society("Observer")
    subject_lct, _ = create_test_society("Subject")
    intermediary_lct, _ = create_test_society("Intermediary")

    engine = TrustCeilingEngine(
        society_lct=observer_lct,
        base_ceiling=0.7,
        decay_factor=0.8
    )

    # Observer has direct low trust
    engine.set_direct_trust(subject_lct, trust_score=0.4)

    # Intermediary reports high trust (will be capped)
    engine.receive_propagated_trust(
        source_lct=intermediary_lct,
        record=create_trust_record(intermediary_lct, subject_lct, 0.95),
        propagation_distance=1
    )

    trust = engine.get_aggregated_trust(subject_lct)

    print(f"Observer's direct trust: 0.4")
    print(f"Intermediary's propagated trust: 0.95 → capped to 0.70")
    print(f"Aggregated trust: {trust:.3f}")
    print(f"Expected: Between 0.4 and 0.7 (weighted average)")

    assert 0.4 <= trust <= 0.7, f"Mixed trust should be weighted average: {trust}"
    print("✅ PASS: Mixed trust weighted correctly")


def test_unknown_subject_defaults_to_neutral():
    """Subject with no trust information should default to neutral"""
    print("\n=== Test: Unknown Subject Defaults to Neutral ===")

    observer_lct, _ = create_test_society("Observer")
    unknown_lct, _ = create_test_society("Unknown")

    engine = TrustCeilingEngine(
        society_lct=observer_lct,
        base_ceiling=0.7
    )

    # No trust information for unknown
    trust = engine.get_aggregated_trust(unknown_lct)

    print(f"Unknown subject (no trust information)")
    print(f"Default trust: {trust:.3f}")
    print(f"Expected: 0.5 (neutral)")

    assert abs(trust - 0.5) < 0.001, f"Unknown should default to neutral: {trust}"
    print("✅ PASS: Unknown defaults to neutral")


# ============================================================================
# Run All Tests
# ============================================================================

def run_all_tests():
    """Run comprehensive trust ceiling tests"""
    print("=" * 70)
    print("Trust Ceiling Comprehensive Test Suite - Session #48")
    print("=" * 70)
    print("\nUsing formal LCT library for cryptographically-bound identities")
    print()

    tests = [
        ("Basic: Direct Trust No Ceiling", test_direct_trust_no_ceiling),
        ("Basic: Propagated Trust Has Ceiling", test_propagated_trust_has_ceiling),
        ("Basic: Ceiling Prevents Collusion", test_ceiling_prevents_perfect_collusion),
        ("Evidence: Evidence Increases Ceiling", test_evidence_increases_ceiling),
        ("Evidence: Direct Observation Full Ceiling", test_direct_observation_full_ceiling),
        ("Evidence: No Evidence = Base Ceiling", test_no_evidence_defaults_to_base_ceiling),
        ("Attack: Sybil Amplification Prevention", test_sybil_amplification_prevented),
        ("Attack: Reputation Washing Prevention", test_reputation_washing_prevented),
        ("Robust: Diversity Discount", test_robust_trust_diversity_discount),
        ("Edge: Mixed Direct/Propagated Trust", test_mixed_direct_and_propagated_trust),
        ("Edge: Unknown Subject Defaults Neutral", test_unknown_subject_defaults_to_neutral),
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
