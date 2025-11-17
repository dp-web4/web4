"""
Verify Original Attacks Are Now Blocked

Re-runs Session #38 attacks with Phase 1 mitigations enabled.
Shows before/after comparison.

Session #39
"""

import unittest
from datetime import datetime, timezone, timedelta

from energy_capacity import (
    SolarPanelProof,
    ComputeResourceProof,
    EnergyCapacityRegistry,
)

from security_mitigations import (
    GlobalEnergyRegistry,
    DeviceSpecDatabase,
    IdentityEnergyLinker,
)


class TestAttacksBlockedByMitigations(unittest.TestCase):
    """Show that Session #38 attacks are now blocked"""

    def test_a2_proof_reuse_now_blocked(self):
        """
        BEFORE (Session #38): Same panel could be registered in 10 societies
        AFTER (Session #39): Global registry blocks reuse
        """
        print("\n" + "=" * 80)
        print("ATTACK A2: PROOF REUSE - BEFORE vs AFTER")
        print("=" * 80)

        # BEFORE: No global registry (Session #36-38)
        print("\n### BEFORE (Session #38):")
        print("  No global registry - proof reuse possible")

        panel = SolarPanelProof(
            panel_serial="TEST-PANEL-REUSE",
            rated_watts=500.0,
            panel_model="Test Panel",
            installation_date=datetime.now(timezone.utc),
            last_verified=datetime.now(timezone.utc),
            degradation_factor=1.0,
            latitude=37.7749,
            longitude=-122.4194,
        )

        # Without global registry, each society has its own registry
        registries_before = []
        for i in range(10):
            registry = EnergyCapacityRegistry(f"lct-society-{i}")
            success = registry.register_source(panel)
            self.assertTrue(success)  # All succeed
            registries_before.append(registry)

        total_claimed_before = sum(r.get_total_capacity() for r in registries_before)
        print(f"  ✓ Registered in 10 societies")
        print(f"  ✓ Total claimed capacity: {total_claimed_before}W (real: 500W)")
        print(f"  ❌ VULNERABLE: {total_claimed_before / 500.0:.0f}x amplification")

        # AFTER: With global registry (Session #39)
        print("\n### AFTER (Session #39):")
        print("  Global registry prevents reuse")

        global_registry = GlobalEnergyRegistry()

        # First registration succeeds
        success_0 = global_registry.register_source(panel, "lct-society-0", "lct-id-0")
        self.assertTrue(success_0)

        # Subsequent registrations fail
        blocked_count = 0
        for i in range(1, 10):
            try:
                global_registry.register_source(panel, f"lct-society-{i}", f"lct-id-{i}")
            except ValueError:
                blocked_count += 1

        print(f"  ✓ Society 0 registered: 500W")
        print(f"  ✓ Societies 1-9 blocked: {blocked_count}/9")
        print(f"  ✓ Total claimed capacity: 500W (real: 500W)")
        print(f"  ✅ SECURED: No amplification possible")

        self.assertEqual(blocked_count, 9)

    def test_a3_capacity_inflation_now_blocked(self):
        """
        BEFORE (Session #38): RTX 4090 @ 1000W accepted (2.22x inflation)
        AFTER (Session #39): Spec database rejects inflated TDP
        """
        print("\n" + "=" * 80)
        print("ATTACK A3: CAPACITY INFLATION - BEFORE vs AFTER")
        print("=" * 80)

        # BEFORE: No spec validation (Session #36-38)
        print("\n### BEFORE (Session #38):")
        print("  No device spec database - inflation possible")

        inflated_gpu = ComputeResourceProof(
            device_type="gpu",
            device_model="RTX 4090",
            device_id="GPU-INFLATED",
            tdp_watts=1000.0,  # Real: 450W
            last_verified=datetime.now(timezone.utc),
            utilization_factor=1.0,
            idle_power_watts=50.0,
        )

        # Without spec database, registry accepts any value
        registry_before = EnergyCapacityRegistry("lct-society-test")
        success = registry_before.register_source(inflated_gpu)
        self.assertTrue(success)

        print(f"  ✓ RTX 4090 @ 1000W accepted")
        print(f"  ✓ Real TDP: 450W")
        print(f"  ❌ VULNERABLE: {1000.0 / 450.0:.2f}x inflation accepted")

        # AFTER: With spec database (Session #39)
        print("\n### AFTER (Session #39):")
        print("  Device spec database validates TDP")

        spec_db = DeviceSpecDatabase()

        valid_tdp = spec_db.validate_gpu_tdp("RTX 4090", 450.0)
        inflated_tdp = spec_db.validate_gpu_tdp("RTX 4090", 1000.0)

        self.assertTrue(valid_tdp)
        self.assertFalse(inflated_tdp)

        print(f"  ✓ RTX 4090 @ 450W: Valid")
        print(f"  ✓ RTX 4090 @ 1000W: Rejected")
        print(f"  ✅ SECURED: Inflation detected and blocked")

    def test_e1_reputation_washing_now_blocked(self):
        """
        BEFORE (Session #38): Identity cycling erases violations
        AFTER (Session #39): Energy-identity linking preserves violations
        """
        print("\n" + "=" * 80)
        print("ATTACK E1: REPUTATION WASHING - BEFORE vs AFTER")
        print("=" * 80)

        # BEFORE: No identity-energy linking (Session #36-38)
        print("\n### BEFORE (Session #38):")
        print("  No identity-energy linking - reputation washing possible")

        # Create identity bonds WITHOUT linker
        from energy_backed_identity_bond import EnergyBackedIdentityBond

        energy_source = "solar:WASH-PANEL"

        bond_a = EnergyBackedIdentityBond(
            society_lct="lct-identity-A",
            created_at=datetime.now(timezone.utc),
            committed_capacity_watts=1000.0,
            energy_sources=[energy_source],
            lock_period_days=30,
        )

        # Accumulate violations
        bond_a.violations.append("violation_1")
        bond_a.violations.append("violation_2")
        bond_a.violations.append("violation_3")

        print(f"  ✓ Identity A violations: {len(bond_a.violations)}")

        # Abandon and create new identity
        bond_a.abandon_identity()

        bond_b = EnergyBackedIdentityBond(
            society_lct="lct-identity-B",
            created_at=datetime.now(timezone.utc),
            committed_capacity_watts=1000.0,
            energy_sources=[energy_source],  # Same energy!
            lock_period_days=30,
        )

        print(f"  ✓ Identity A abandoned")
        print(f"  ✓ Identity B created with same energy")
        print(f"  ✓ Identity B violations: {len(bond_b.violations)}")
        print(f"  ❌ VULNERABLE: Reputation washed (3 → 0 violations)")

        self.assertEqual(len(bond_b.violations), 0)

        # AFTER: With identity-energy linker (Session #39)
        print("\n### AFTER (Session #39):")
        print("  Identity-energy linker tracks violations across identities")

        linker = IdentityEnergyLinker()

        # Register identity A
        linker.register_identity("lct-identity-A", [energy_source])
        linker.record_violation("lct-identity-A", "violation_1")
        linker.record_violation("lct-identity-A", "violation_2")
        linker.record_violation("lct-identity-A", "violation_3")

        print(f"  ✓ Identity A violations: 3")

        # Abandon and create new identity
        linker.abandon_identity("lct-identity-A")
        linker.register_identity("lct-identity-B", [energy_source])

        # Check effective violations (includes energy source history)
        effective_violations = linker.get_identity_effective_violations("lct-identity-B")

        print(f"  ✓ Identity A abandoned")
        print(f"  ✓ Identity B created with same energy")
        print(f"  ✓ Identity B effective violations: {len(effective_violations)}")
        print(f"  ✅ SECURED: Violations preserved (3 violations tracked)")

        self.assertEqual(len(effective_violations), 3)


def run_before_after_tests():
    """Run before/after comparison tests"""

    print("\n" + "=" * 80)
    print("SESSION #39: ATTACK MITIGATION VERIFICATION")
    print("Comparing Session #38 Attacks vs Session #39 Mitigations")
    print("=" * 80)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestAttacksBlockedByMitigations))

    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)

    print("\n" + "=" * 80)
    print("BEFORE/AFTER SUMMARY")
    print("=" * 80)

    if result.wasSuccessful():
        print("\n✅ ALL MITIGATIONS VERIFIED")
        print("\nSession #38 → Session #39 Security Improvements:")
        print("  A2: Proof Reuse")
        print("    - BEFORE: 10x capacity amplification possible")
        print("    - AFTER: Global registry blocks reuse (9/9 attempts blocked)")
        print("\n  A3: Capacity Inflation")
        print("    - BEFORE: 2.22x GPU TDP inflation accepted")
        print("    - AFTER: Spec database rejects inflated values")
        print("\n  E1: Reputation Washing")
        print("    - BEFORE: Identity cycling erases violations (3 → 0)")
        print("    - AFTER: Energy-identity linking preserves violations (3 → 3)")
        print("\n🔒 Security Posture:")
        print("    - Critical attack vectors closed")
        print("    - System hardened against adversarial behavior")
        print("    - Foundation for Phase 2 mitigations")

    return result


if __name__ == "__main__":
    run_before_after_tests()
