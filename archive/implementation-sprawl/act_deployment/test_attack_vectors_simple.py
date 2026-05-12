"""
Simplified Attack Vector Tests for Energy-Backed ATP System

Tests critical vulnerabilities from ATTACK_VECTORS_SESSION_38.md using actual API.
"""

import unittest
from datetime import datetime, timezone, timedelta

from energy_capacity import (
    SolarPanelProof,
    ComputeResourceProof,
    EnergyCapacityRegistry,
    EnergySourceType,
)

from energy_backed_identity_bond import (
    EnergyBackedIdentityBond,
    EnergyBackedVouch,
    BondStatus,
)


class TestA1_FakeEnergyProof(unittest.TestCase):
    """A1: Fake Energy Capacity Proof - Can create ATP from non-existent energy"""

    def test_fake_solar_panel_accepted(self):
        """VULNERABILITY: System accepts completely fabricated solar panel proof"""

        registry = EnergyCapacityRegistry(society_lct="lct-test-society")

        # Attacker submits COMPLETELY FAKE solar panel
        fake_solar = SolarPanelProof(
            panel_serial="TOTALLY-FAKE-12345",
            rated_watts=10000.0,  # Claims 10kW
            panel_model="Imaginary SuperPanel 9000",
            installation_date=datetime.now(timezone.utc),
            last_verified=datetime.now(timezone.utc),
            degradation_factor=1.0,
            latitude=37.7749,
            longitude=-122.4194,
        )

        # ATTACK: Register fake proof
        success = registry.register_source(fake_solar)

        # VULNERABILITY CONFIRMED: Fake proof accepted
        self.assertTrue(success, "Fake proof accepted - VULNERABILITY!")
        self.assertEqual(registry.get_total_capacity(), 10000.0)

        print("\n[ATTACK A1] Fake Solar Panel Attack")
        print(f"  ❌ Accepted fake panel: {fake_solar.panel_serial}")
        print(f"  ❌ Claimed capacity: {fake_solar.capacity_watts}W")
        print(f"  ❌ Total capacity now: {registry.get_total_capacity()}W")
        print(f"  💥 Impact: Can charge {fake_solar.capacity_watts}W of ATP from nothing!")

    def test_fake_gpu_accepted(self):
        """VULNERABILITY: System accepts non-existent GPU"""

        registry = EnergyCapacityRegistry(society_lct="lct-test-society")

        # Attacker claims GPU that doesn't exist
        fake_gpu = ComputeResourceProof(
            device_type="gpu",
            device_model="RTX 9090 Ti Super",  # Doesn't exist
            device_id="FAKE-GPU-12345",
            tdp_watts=600.0,
            last_verified=datetime.now(timezone.utc),
            utilization_factor=1.0,
            idle_power_watts=50.0,
        )

        success = registry.register_source(fake_gpu)

        self.assertTrue(success, "Fake GPU accepted - VULNERABILITY!")

        print("\n[ATTACK A1] Fake GPU Attack")
        print(f"  ❌ Accepted fake GPU: {fake_gpu.device_model}")
        print(f"  ❌ Claimed TDP: {fake_gpu.tdp_watts}W")
        print(f"  💥 Impact: {fake_gpu.tdp_watts}W capacity from imaginary hardware!")

    def test_capacity_multiplication_via_fakes(self):
        """VULNERABILITY: Can create unlimited capacity via multiple fake proofs"""

        registry = EnergyCapacityRegistry(society_lct="lct-test-society")

        # Submit 10 fake solar panels
        for i in range(10):
            fake = SolarPanelProof(
                panel_serial=f"FAKE-PANEL-{i:03d}",
                rated_watts=1000.0,
                panel_model="FakePanel",
                installation_date=datetime.now(timezone.utc),
                last_verified=datetime.now(timezone.utc),
                degradation_factor=1.0,
                latitude=37.7749,
                longitude=-122.4194,
            )
            registry.register_source(fake)

        total = registry.get_total_capacity()

        self.assertEqual(total, 10000.0)

        print("\n[ATTACK A1] Capacity Multiplication Attack")
        print(f"  ❌ Submitted 10 fake solar panels")
        print(f"  ❌ Total fake capacity: {total}W")
        print(f"  💥 Impact: Unlimited ATP from zero real energy!")


class TestA2_ProofReuseAttack(unittest.TestCase):
    """A2: Proof Reuse - Same energy source registered in multiple societies"""

    def test_same_panel_multiple_societies(self):
        """VULNERABILITY: Same solar panel can back ATP in multiple societies"""

        # Create real solar panel
        real_panel = SolarPanelProof(
            panel_serial="REAL-PANEL-ABC123",
            rated_watts=300.0,
            panel_model="SunPower X22",
            installation_date=datetime.now(timezone.utc) - timedelta(days=365),
            last_verified=datetime.now(timezone.utc),
            degradation_factor=0.95,
            latitude=37.7749,
            longitude=-122.4194,
        )

        # Society A registers the panel
        registry_a = EnergyCapacityRegistry(society_lct="lct-society-A")
        success_a = registry_a.register_source(real_panel)
        self.assertTrue(success_a)

        # ATTACK: Society B registers SAME panel
        registry_b = EnergyCapacityRegistry(society_lct="lct-society-B")
        success_b = registry_b.register_source(real_panel)

        # VULNERABILITY: Same panel accepted by both societies
        self.assertTrue(success_b, "Proof reuse accepted - VULNERABILITY!")

        total_claimed = registry_a.get_total_capacity() + registry_b.get_total_capacity()
        actual_capacity = real_panel.capacity_watts

        print("\n[ATTACK A2] Energy Double-Spending Attack")
        print(f"  🔋 Real solar panel: {real_panel.panel_serial}")
        print(f"  🔋 Actual capacity: {actual_capacity}W")
        print(f"  ❌ Society A claims: {registry_a.get_total_capacity()}W")
        print(f"  ❌ Society B claims: {registry_b.get_total_capacity()}W")
        print(f"  ❌ Total claimed: {total_claimed}W")
        print(f"  💥 Impact: {total_claimed / actual_capacity}x capacity from same source!")

    def test_proof_reuse_scaling(self):
        """VULNERABILITY: Can register same proof in many societies for Nx amplification"""

        real_panel = SolarPanelProof(
            panel_serial="SHARED-PANEL-001",
            rated_watts=500.0,
            panel_model="SharedPanel",
            installation_date=datetime.now(timezone.utc),
            last_verified=datetime.now(timezone.utc),
            degradation_factor=1.0,
            latitude=37.7749,
            longitude=-122.4194,
        )

        # Register in 10 societies
        registries = []
        for i in range(10):
            registry = EnergyCapacityRegistry(society_lct=f"lct-society-{i}")
            success = registry.register_source(real_panel)
            self.assertTrue(success)
            registries.append(registry)

        total_claimed = sum(r.get_total_capacity() for r in registries)
        actual_capacity = real_panel.capacity_watts

        print("\n[ATTACK A2] Scaled Proof Reuse Attack")
        print(f"  🔋 Real capacity: {actual_capacity}W")
        print(f"  ❌ Societies exploiting: 10")
        print(f"  ❌ Total claimed: {total_claimed}W")
        print(f"  💥 Impact: {total_claimed / actual_capacity:.0f}x amplification!")


class TestA3_CapacityInflation(unittest.TestCase):
    """A3: Capacity Inflation - Claiming higher capacity than device actually has"""

    def test_gpu_tdp_inflation(self):
        """VULNERABILITY: Can claim higher TDP than GPU actually has"""

        registry = EnergyCapacityRegistry(society_lct="lct-test-society")

        # Real RTX 4090 has TDP of 450W
        # Attacker claims 1000W
        inflated_gpu = ComputeResourceProof(
            device_type="gpu",
            device_model="RTX 4090",
            device_id="REAL-SERIAL-123",  # Real serial
            tdp_watts=1000.0,  # INFLATED (real: 450W)
            last_verified=datetime.now(timezone.utc),
            utilization_factor=1.0,
            idle_power_watts=50.0,
        )

        success = registry.register_source(inflated_gpu)

        self.assertTrue(success, "Inflated TDP accepted - VULNERABILITY!")

        real_tdp = 450.0
        claimed_tdp = inflated_gpu.tdp_watts

        print("\n[ATTACK A3] GPU TDP Inflation Attack")
        print(f"  🎮 Device: {inflated_gpu.device_model}")
        print(f"  ✅ Real TDP: {real_tdp}W")
        print(f"  ❌ Claimed TDP: {claimed_tdp}W")
        print(f"  💥 Impact: {claimed_tdp - real_tdp}W of fake capacity ({claimed_tdp/real_tdp:.2f}x inflation)")

    def test_solar_degradation_manipulation(self):
        """VULNERABILITY: Can claim perfect degradation for old panels"""

        registry = EnergyCapacityRegistry(society_lct="lct-test-society")

        # 10-year-old panel should have ~0.80 degradation
        # Attacker claims 1.0 (perfect)
        old_panel = SolarPanelProof(
            panel_serial="OLD-PANEL-2015",
            rated_watts=300.0,
            panel_model="Old Panel",
            installation_date=datetime.now(timezone.utc) - timedelta(days=3650),
            last_verified=datetime.now(timezone.utc),
            degradation_factor=1.0,  # Should be ~0.80
            latitude=37.7749,
            longitude=-122.4194,
        )

        success = registry.register_source(old_panel)

        self.assertTrue(success, "Inflated degradation accepted - VULNERABILITY!")

        realistic_degradation = 0.80
        claimed_capacity = old_panel.capacity_watts
        realistic_capacity = old_panel.rated_watts * realistic_degradation

        print("\n[ATTACK A3] Solar Degradation Manipulation Attack")
        print(f"  ☀️  Panel age: 10 years")
        print(f"  ✅ Realistic capacity: {realistic_capacity}W (0.80 degradation)")
        print(f"  ❌ Claimed capacity: {claimed_capacity}W (1.0 degradation)")
        print(f"  💥 Impact: {claimed_capacity - realistic_capacity}W inflated")


class TestE1_IdentityAbandonment(unittest.TestCase):
    """E1: Identity Abandonment - Reputation washing via identity switching"""

    def test_reputation_washing_via_new_identity(self):
        """VULNERABILITY: Can abandon bad identity and create new one with same energy"""

        energy_source_id = "solar:shared-panel-001"

        # Identity A accumulates violations
        bond_a = EnergyBackedIdentityBond(
            society_lct="lct-identity-A",
            created_at=datetime.now(timezone.utc),
            committed_capacity_watts=1000.0,
            energy_sources=[energy_source_id],
            lock_period_days=30,
        )

        # Simulate bad behavior
        bond_a.violations.append("failed_work_001")
        bond_a.violations.append("failed_work_002")
        bond_a.violations.append("spam_detected")

        violations_a = len(bond_a.violations)

        # ATTACK: Abandon identity A, create identity B with SAME energy
        bond_a.abandon_identity()

        bond_b = EnergyBackedIdentityBond(
            society_lct="lct-identity-B",  # New identity
            created_at=datetime.now(timezone.utc),
            committed_capacity_watts=1000.0,
            energy_sources=[energy_source_id],  # SAME energy!
            lock_period_days=30,
        )

        violations_b = len(bond_b.violations)

        # VULNERABILITY: New identity has clean slate despite same energy source
        self.assertEqual(violations_a, 3)
        self.assertEqual(violations_b, 0, "New identity has clean slate - VULNERABILITY!")

        print("\n[ATTACK E1] Reputation Washing Attack")
        print(f"  🆔 Identity A violations: {violations_a}")
        print(f"  ❌ Identity A abandoned")
        print(f"  🆔 Identity B violations: {violations_b} (clean slate)")
        print(f"  🔋 Shared energy source: {energy_source_id}")
        print(f"  💥 Impact: Circumvented reputation penalties!")

    def test_identity_cycling(self):
        """VULNERABILITY: Can cycle through many identities indefinitely"""

        energy_source_id = "solar:cycling-panel-001"
        identities = []
        total_violations = 0

        # Create 5 identities, accumulate violations, abandon each
        for i in range(5):
            bond = EnergyBackedIdentityBond(
                society_lct=f"lct-cycle-{i}",
                created_at=datetime.now(timezone.utc),
                committed_capacity_watts=500.0,
                energy_sources=[energy_source_id],
                lock_period_days=30,
            )

            # Each identity commits violations
            for j in range(i + 1):
                bond.violations.append(f"violation_{i}_{j}")
                total_violations += 1

            bond.abandon_identity()
            identities.append(bond)

        # Current identity is clean despite 15 total violations
        current_bond = EnergyBackedIdentityBond(
            society_lct="lct-cycle-current",
            created_at=datetime.now(timezone.utc),
            committed_capacity_watts=500.0,
            energy_sources=[energy_source_id],
            lock_period_days=30,
        )

        print("\n[ATTACK E1] Identity Cycling Attack")
        print(f"  🔄 Identities cycled: {len(identities)}")
        print(f"  ❌ Total violations across all: {total_violations}")
        print(f"  🆔 Current identity violations: {len(current_bond.violations)}")
        print(f"  🔋 Shared energy source: {energy_source_id}")
        print(f"  💥 Impact: Indefinite reputation washing!")


class TestF1_CircularVouching(unittest.TestCase):
    """F1: Circular Vouching - Sybil amplification via vouching rings"""

    def test_circular_vouching_ring(self):
        """VULNERABILITY: Can create self-referential vouching rings"""

        # Create 5-identity vouching ring
        identities = [f"lct-ring-{i}" for i in range(5)]
        vouches = []

        # Each vouches for next (circular)
        for i in range(5):
            voucher = identities[i]
            newcomer = identities[(i + 1) % 5]

            vouch = EnergyBackedVouch(
                voucher_lct=voucher,
                newcomer_lct=newcomer,
                created_at=datetime.now(timezone.utc),
                allocated_energy_watts=100.0,
                bootstrap_period_days=30,
            )
            vouches.append(vouch)

        # VULNERABILITY: All vouches accepted despite being circular
        all_active = all(v.active for v in vouches)

        self.assertTrue(all_active, "Circular vouching accepted - VULNERABILITY!")

        print("\n[ATTACK F1] Circular Vouching Ring Attack")
        print(f"  🔗 Ring size: {len(identities)} identities")
        print(f"  ❌ Vouching pattern (circular):")
        for v in vouches:
            print(f"     {v.voucher_lct} → {v.newcomer_lct}")
        print(f"  💥 Impact: Entire ring bootstraps with NO external trust!")
        print(f"  💥 Sybil amplification: {len(identities)}x")


def run_tests():
    """Run all attack tests with results summary"""

    print("=" * 80)
    print("ATTACK VECTOR TEST SUITE - Session #38")
    print("Testing Energy-Backed ATP System Security")
    print("=" * 80)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestA1_FakeEnergyProof))
    suite.addTests(loader.loadTestsFromTestCase(TestA2_ProofReuseAttack))
    suite.addTests(loader.loadTestsFromTestCase(TestA3_CapacityInflation))
    suite.addTests(loader.loadTestsFromTestCase(TestE1_IdentityAbandonment))
    suite.addTests(loader.loadTestsFromTestCase(TestF1_CircularVouching))

    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 80)
    print("VULNERABILITY ASSESSMENT SUMMARY")
    print("=" * 80)
    print(f"Total tests: {result.testsRun}")
    print(f"Vulnerabilities confirmed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n⚠️  ALL ATTACKS SUCCESSFUL - SYSTEM IS VULNERABLE")
        print("\n📋 Critical Vulnerabilities Confirmed:")
        print("   A1: Fake Energy Proof - Can create ATP from nothing")
        print("   A2: Proof Reuse - Can double-spend energy across societies")
        print("   A3: Capacity Inflation - Can claim more capacity than exists")
        print("   E1: Identity Abandonment - Can wash reputation indefinitely")
        print("   F1: Circular Vouching - Can bootstrap Sybil networks")
        print("\n🔧 Next Steps:")
        print("   1. Implement global energy registry (prevent A2)")
        print("   2. Add device spec database (prevent A3)")
        print("   3. Link identities to energy sources (prevent E1)")
        print("   4. Add circular vouching detection (prevent F1)")
        print("   5. Add external validation (prevent A1)")

    return result


if __name__ == "__main__":
    run_tests()
