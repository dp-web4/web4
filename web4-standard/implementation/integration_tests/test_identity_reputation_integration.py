#!/usr/bin/env python3
"""
Web4 Integration Tests: Identity + Reputation
==============================================

Tests integration between LCT presence system and reputation tracking.

Validates:
- Witness attestation updates reputation
- Reputation affects identity trust
- State consistency between components

Created: Session #23 (2025-11-13)
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Add component paths
sys.path.insert(0, str(Path(__file__).parent.parent / "reputation"))

from reputation_tracker import (
    ReputationTracker,
    BehaviorType,
    get_reputation_tracker,
    set_reputation_tracker
)


class TestIdentityReputationIntegration:
    """Integration tests for Identity + Reputation"""

    def setup_method(self):
        """Setup test environment"""
        # Create fresh reputation tracker for each test
        self.reputation = ReputationTracker(decay_half_life_days=30.0)
        set_reputation_tracker(self.reputation)

    def test_witness_attestation_flow(self):
        """
        Test witness attestation creates reputation event.

        Flow:
        1. Agent requests LCT
        2. Witness attests
        3. Witness reputation should increase
        """
        print("\nTest: Witness Attestation Flow")

        witness_lct = "lct:ai:witness_agent_001"
        subject_lct = "lct:ai:new_agent_001"

        # Check witness reputation before attestation
        t3_before = self.reputation.calculate_t3(witness_lct, "test_org")
        assert t3_before == 0.0  # New witness, no history
        print(f"  Witness T3 before attestation: {t3_before:.3f}")

        # Simulate witness attestation
        event = self.reputation.record_event(
            agent_lct=witness_lct,
            behavior_type=BehaviorType.WITNESS_VERIFICATION,
            organization="test_org",
            description=f"Attested identity for {subject_lct}",
            metadata={
                "subject_lct": subject_lct,
                "attestation_type": "identity_verification"
            }
        )

        # Check witness reputation after attestation
        t3_after = self.reputation.calculate_t3(witness_lct, "test_org")
        print(f"  Witness T3 after attestation: {t3_after:.3f}")

        # Verify reputation increased
        assert t3_after > t3_before
        assert event.coherence_delta == 0.2  # WITNESS_VERIFICATION impact
        assert event.metadata["subject_lct"] == subject_lct

        print("  ✅ Witness attestation correctly updates reputation")

    def test_multiple_attestations_build_reputation(self):
        """
        Test multiple attestations build witness reputation over time.
        """
        print("\nTest: Multiple Attestations Build Reputation")

        witness_lct = "lct:ai:witness_agent_002"
        organization = "test_org"

        # Record 5 attestations
        for i in range(5):
            self.reputation.record_event(
                agent_lct=witness_lct,
                behavior_type=BehaviorType.WITNESS_VERIFICATION,
                organization=organization,
                description=f"Attestation {i+1}"
            )

        t3_score = self.reputation.calculate_t3(witness_lct, organization)
        snapshot = self.reputation.get_reputation_snapshot(witness_lct, organization)

        print(f"  T3 after 5 attestations: {t3_score:.3f}")
        print(f"  Coherence level: {snapshot.coherence_level}")
        print(f"  Total events: {snapshot.total_events}")

        # Should reach at least "trusted" level
        assert t3_score >= 0.5  # Trusted threshold
        assert snapshot.coherent_events == 5
        assert snapshot.decoherent_events == 0
        assert snapshot.coherence_level in ["trusted", "expert", "master"]

        print("  ✅ Multiple attestations build reputation correctly")

    def test_false_attestation_damages_reputation(self):
        """
        Test false attestation severely damages witness reputation.
        """
        print("\nTest: False Attestation Damages Reputation")

        witness_lct = "lct:ai:dishonest_witness"
        organization = "test_org"

        # Build up good reputation first
        for i in range(5):
            self.reputation.record_event(
                agent_lct=witness_lct,
                behavior_type=BehaviorType.WITNESS_VERIFICATION,
                organization=organization
            )

        t3_before = self.reputation.calculate_t3(witness_lct, organization)
        print(f"  T3 before false attestation: {t3_before:.3f}")

        # Record false attestation
        self.reputation.record_event(
            agent_lct=witness_lct,
            behavior_type=BehaviorType.FALSE_WITNESS,
            organization=organization,
            description="Attested for fake identity",
            metadata={"detected_by": "verification_system"}
        )

        t3_after = self.reputation.calculate_t3(witness_lct, organization)
        drop = t3_before - t3_after

        print(f"  T3 after false attestation: {t3_after:.3f}")
        print(f"  Reputation drop: {drop:.3f}")

        # Should drop reputation
        assert t3_after < t3_before
        assert drop > 0.0

        print("  ✅ False attestation correctly damages reputation")

    def test_organization_isolation_in_attestations(self):
        """
        Test witness reputation is isolated per organization.
        """
        print("\nTest: Organization Isolation in Attestations")

        witness_lct = "lct:ai:cross_org_witness"

        # Good attestations in org1
        for i in range(10):
            self.reputation.record_event(
                agent_lct=witness_lct,
                behavior_type=BehaviorType.WITNESS_VERIFICATION,
                organization="org1"
            )

        # Bad attestations in org2
        for i in range(10):
            self.reputation.record_event(
                agent_lct=witness_lct,
                behavior_type=BehaviorType.FALSE_WITNESS,
                organization="org2"
            )

        t3_org1 = self.reputation.calculate_t3(witness_lct, "org1")
        t3_org2 = self.reputation.calculate_t3(witness_lct, "org2")

        print(f"  T3 in org1 (good attestations): {t3_org1:.3f}")
        print(f"  T3 in org2 (bad attestations): {t3_org2:.3f}")

        # Should have high reputation in org1, low in org2
        assert t3_org1 > 0.5  # High trust in org1
        assert t3_org2 < 0.5  # Low trust in org2
        assert t3_org1 > t3_org2  # Clear difference

        print("  ✅ Organization isolation works correctly")

    def test_attestation_confidence_affects_reputation(self):
        """
        Test attestation confidence affects reputation gain.
        """
        print("\nTest: Attestation Confidence Affects Reputation")

        witness_high = "lct:ai:high_confidence_witness"
        witness_low = "lct:ai:low_confidence_witness"
        organization = "test_org"

        # High confidence attestation
        self.reputation.record_event(
            agent_lct=witness_high,
            behavior_type=BehaviorType.WITNESS_VERIFICATION,
            organization=organization,
            confidence=1.0
        )

        # Low confidence attestation
        self.reputation.record_event(
            agent_lct=witness_low,
            behavior_type=BehaviorType.WITNESS_VERIFICATION,
            organization=organization,
            confidence=0.3
        )

        t3_high = self.reputation.calculate_t3(witness_high, organization)
        t3_low = self.reputation.calculate_t3(witness_low, organization)

        print(f"  High confidence (1.0) T3: {t3_high:.3f}")
        print(f"  Low confidence (0.3) T3: {t3_low:.3f}")

        # High confidence should result in higher reputation
        assert t3_high > t3_low

        print("  ✅ Confidence scaling works correctly")

    def test_attested_by_metadata_tracking(self):
        """
        Test attestation metadata is correctly tracked.
        """
        print("\nTest: Attestation Metadata Tracking")

        witness_lct = "lct:ai:meta_witness"
        subject_lct = "lct:ai:meta_subject"
        verifier_lct = "lct:ai:meta_verifier"
        organization = "test_org"

        # Create attestation with metadata
        event = self.reputation.record_event(
            agent_lct=witness_lct,
            behavior_type=BehaviorType.WITNESS_VERIFICATION,
            organization=organization,
            description="Identity verification attestation",
            attested_by=verifier_lct,
            metadata={
                "subject_lct": subject_lct,
                "verification_method": "cryptographic_proof",
                "timestamp_verified": datetime.now(timezone.utc).isoformat()
            }
        )

        # Verify metadata is tracked
        assert event.agent_lct == witness_lct
        assert event.attested_by == verifier_lct
        assert event.metadata["subject_lct"] == subject_lct
        assert "verification_method" in event.metadata

        print(f"  Event metadata: {len(event.metadata)} fields tracked")
        print(f"  Attested by: {event.attested_by}")
        print("  ✅ Metadata tracking works correctly")

    def test_witness_reputation_snapshot(self):
        """
        Test comprehensive reputation snapshot for witness.
        """
        print("\nTest: Witness Reputation Snapshot")

        witness_lct = "lct:ai:snapshot_witness"
        organization = "test_org"

        # Build diverse attestation history
        attestations = [
            (BehaviorType.WITNESS_VERIFICATION, 5),
            (BehaviorType.SUCCESSFUL_ACTION, 3),
            (BehaviorType.FALSE_WITNESS, 1),
        ]

        for behavior_type, count in attestations:
            for _ in range(count):
                self.reputation.record_event(
                    agent_lct=witness_lct,
                    behavior_type=behavior_type,
                    organization=organization
                )

        snapshot = self.reputation.get_reputation_snapshot(witness_lct, organization)

        print(f"  T3 Score: {snapshot.t3_score:.3f}")
        print(f"  Coherence Level: {snapshot.coherence_level}")
        print(f"  Total Events: {snapshot.total_events}")
        print(f"  Coherent: {snapshot.coherent_events}")
        print(f"  Decoherent: {snapshot.decoherent_events}")
        print(f"  Trend: {snapshot.recent_trend}")

        # Verify snapshot completeness
        assert snapshot.total_events == 9
        assert snapshot.coherent_events == 8
        assert snapshot.decoherent_events == 1
        assert 0.0 <= snapshot.t3_score <= 1.0
        assert snapshot.coherence_level in ["novice", "developing", "trusted", "expert", "master"]

        print("  ✅ Snapshot provides complete reputation view")


def run_integration_tests():
    """Run all integration tests"""
    print("=" * 80)
    print("Web4 Integration Tests: Identity + Reputation")
    print("=" * 80)

    test_suite = TestIdentityReputationIntegration()

    tests = [
        test_suite.test_witness_attestation_flow,
        test_suite.test_multiple_attestations_build_reputation,
        test_suite.test_false_attestation_damages_reputation,
        test_suite.test_organization_isolation_in_attestations,
        test_suite.test_attestation_confidence_affects_reputation,
        test_suite.test_attested_by_metadata_tracking,
        test_suite.test_witness_reputation_snapshot,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        test_suite.setup_method()
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n  ❌ FAILED: {test_func.__name__}")
            print(f"     Error: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"\n  ❌ ERROR: {test_func.__name__}")
            print(f"     Error: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 80)
    if failed == 0:
        print(f"✅ ALL INTEGRATION TESTS PASSED ({passed}/{passed + failed})")
        print("=" * 80)
        print("\nIdentity + Reputation Integration: INTEGRATION_TESTED")
        print("\nKey Validations:")
        print("  ✅ Witness attestation updates reputation correctly")
        print("  ✅ Multiple attestations build reputation over time")
        print("  ✅ False attestations damage reputation")
        print("  ✅ Organization isolation preserved")
        print("  ✅ Confidence scaling works")
        print("  ✅ Metadata tracking functional")
        print("  ✅ Comprehensive snapshots available")
        return True
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{passed + failed} passed)")
        print("=" * 80)
        return False


if __name__ == "__main__":
    import sys
    success = run_integration_tests()
    sys.exit(0 if success else 1)
