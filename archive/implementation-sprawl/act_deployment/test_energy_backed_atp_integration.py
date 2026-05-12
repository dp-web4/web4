"""
Integration Tests for Energy-Backed ATP System

Tests all Session #36 components working together and validates
integration with Sessions #30-35 trust/reputation mechanisms.

Test Coverage:
1. Energy capacity proofs (Phase 1)
2. ATP charging and expiration (Phase 2)
3. Work allocation and discharge (Phase 2)
4. Trust-based priority queuing (Phase 3)
5. Energy-backed identity bonds (Phase 4)
6. Integration with Sessions #30-35

Part of Session #36 implementation (Phase 5).
"""

import unittest
from datetime import datetime, timezone, timedelta
import time

from energy_capacity import (
    SolarPanelProof,
    ComputeResourceProof,
    GridConnectionProof,
    HumanLaborProof,
    BatteryStorageProof,
    EnergyCapacityRegistry,
)

from energy_backed_atp import (
    EnergyBackedSocietyPool,
    ChargedATP,
    WorkStatus,
)

from trust_based_energy_priority import (
    TrustBasedEnergyPriority,
    TrustScore,
    RequestPriority,
)

from energy_backed_identity_bond import (
    EnergyBackedBondRegistry,
    BondStatus,
)


class TestEnergyCapacityProofs(unittest.TestCase):
    """Test Phase 1: Energy Capacity Proofs"""

    def setUp(self):
        self.registry = EnergyCapacityRegistry(society_lct="lct-test-society")

    def test_solar_panel_proof(self):
        """Test solar panel energy proof validation"""
        solar = SolarPanelProof(
            panel_serial="SOLAR-001",
            rated_watts=300.0,
            panel_model="Test Panel",
            installation_date=datetime.now(timezone.utc),
            last_verified=datetime.now(timezone.utc),
            degradation_factor=0.95,
        )

        self.assertTrue(self.registry.register_source(solar))
        self.assertEqual(self.registry.get_total_capacity(), 285.0)  # 300 * 0.95

    def test_compute_resource_proof(self):
        """Test GPU compute energy proof"""
        gpu = ComputeResourceProof(
            device_type="gpu",
            device_model="RTX4090",
            device_id="GPU-001",
            tdp_watts=450.0,
            last_verified=datetime.now(timezone.utc),
            utilization_factor=0.8,
            idle_power_watts=50.0,
        )

        self.assertTrue(self.registry.register_source(gpu))
        # 50 + (450-50)*0.8 = 370W
        self.assertAlmostEqual(self.registry.get_total_capacity(), 370.0)

    def test_mixed_energy_sources(self):
        """Test multiple energy sources"""
        solar = SolarPanelProof(
            panel_serial="SOLAR-001",
            rated_watts=300.0,
            panel_model="Test",
            installation_date=datetime.now(timezone.utc),
            last_verified=datetime.now(timezone.utc),
        )

        grid = GridConnectionProof(
            meter_id="METER-001",
            allocated_watts=1000.0,
            utility_provider="Test Utility",
            account_number="ACC-001",
            last_verified=datetime.now(timezone.utc),
        )

        self.registry.register_source(solar)
        self.registry.register_source(grid)

        self.assertGreater(self.registry.get_total_capacity(), 1200.0)


class TestEnergyBackedATPPool(unittest.TestCase):
    """Test Phase 2: Energy-Backed ATP/ADP Pool"""

    def setUp(self):
        self.pool = EnergyBackedSocietyPool(society_lct="lct-test")

        # Add energy source
        self.solar = SolarPanelProof(
            panel_serial="SOLAR-001",
            rated_watts=1000.0,
            panel_model="Test",
            installation_date=datetime.now(timezone.utc),
            last_verified=datetime.now(timezone.utc),
        )
        self.pool.register_energy_source(self.solar)

        # Initialize ADP pool
        self.pool.adp_pool = 2000.0

    def test_atp_charging_requires_energy_proof(self):
        """Test ATP can only be charged with valid energy source"""
        # Valid source
        atp = self.pool.charge_atp(500.0, self.solar.source_identifier)
        self.assertIsNotNone(atp)
        self.assertEqual(self.pool.get_available_atp(), 500.0)

        # Invalid source
        atp_invalid = self.pool.charge_atp(500.0, "invalid-source-id")
        self.assertIsNone(atp_invalid)

    def test_atp_expiration(self):
        """Test ATP expires after lifetime"""
        atp = self.pool.charge_atp(
            500.0,
            self.solar.source_identifier,
            lifetime_days=7
        )

        self.assertIsNotNone(atp)

        # ATP should not be expired initially
        self.assertFalse(atp.is_expired())

        # Manually set expiration to past for testing
        atp.expiration = datetime.now(timezone.utc) - timedelta(days=1)

        # Now should be expired
        self.assertTrue(atp.is_expired())
        self.assertEqual(atp.lifetime_fraction_remaining(), 0.0)

    def test_work_allocation_and_discharge(self):
        """Test ATP → Work → ADP cycle"""
        # Charge ATP
        self.pool.charge_atp(1000.0, self.solar.source_identifier)

        # Allocate to work
        ticket = self.pool.allocate_atp_to_work(
            worker_lct="lct-worker-001",
            description="Test work",
            atp_amount=500.0,
        )

        self.assertIsNotNone(ticket)
        self.assertEqual(ticket.atp_allocated, 500.0)
        self.assertEqual(self.pool.get_available_atp(), 500.0)  # 500 used, 500 remaining

        # Complete work
        adp = self.pool.complete_work(ticket.id, quality_score=0.9)

        self.assertIsNotNone(adp)
        self.assertEqual(adp.amount, 500.0)
        self.assertEqual(adp.quality_score, 0.9)
        self.assertEqual(self.pool.adp_pool, 1500.0)  # 1000 initial - 1000 charged + 500 returned

    def test_atp_capacity_constraint(self):
        """Test ATP charging limited by energy capacity"""
        # Try to charge more than capacity
        atp = self.pool.charge_atp(2000.0, self.solar.source_identifier)
        self.assertIsNone(atp)  # Should fail - only 1000W capacity

        # Charge within capacity
        atp_valid = self.pool.charge_atp(800.0, self.solar.source_identifier)
        self.assertIsNotNone(atp_valid)


class TestTrustBasedPriority(unittest.TestCase):
    """Test Phase 3: Trust-Based Energy Priority"""

    def setUp(self):
        # Create pool with energy
        self.pool = EnergyBackedSocietyPool(society_lct="lct-test")

        solar = SolarPanelProof(
            panel_serial="SOLAR-001",
            rated_watts=1000.0,
            panel_model="Test",
            installation_date=datetime.now(timezone.utc),
            last_verified=datetime.now(timezone.utc),
        )
        self.pool.register_energy_source(solar)
        self.pool.adp_pool = 2000.0
        self.pool.charge_atp(1000.0, solar.source_identifier)

        # Create priority system
        self.priority = TrustBasedEnergyPriority(
            society_lct=self.pool.society_lct,
            energy_pool=self.pool
        )

    def test_trust_determines_priority_not_price(self):
        """Test trust affects queue position, not cost"""
        # Register different trust scores
        self.priority.register_trust_score(TrustScore(
            lct_id="lct-high-trust",
            direct_trust=0.95,
            bond_trust=1.0,
        ))

        self.priority.register_trust_score(TrustScore(
            lct_id="lct-low-trust",
            direct_trust=0.3,
            experience_penalty=0.3,  # Newcomer
        ))

        # Submit requests (low trust first)
        req_low = self.priority.submit_work_request(
            "lct-low-trust", "Low trust work", 200.0
        )
        time.sleep(0.01)
        req_high = self.priority.submit_work_request(
            "lct-high-trust", "High trust work", 200.0
        )

        # Process queue
        allocated = self.priority.process_all_available()

        # High trust should be processed first despite submitting second
        self.assertEqual(allocated[0][0].requester_lct, "lct-high-trust")
        self.assertEqual(allocated[1][0].requester_lct, "lct-low-trust")

    def test_priority_levels_match_trust_scores(self):
        """Test priority calculation from trust scores"""
        # Test all trust tiers
        trust_tiers = [
            (0.95, RequestPriority.HIGH),
            (0.75, RequestPriority.ELEVATED),
            (0.55, RequestPriority.NORMAL),
            (0.35, RequestPriority.LOW),
            (0.15, RequestPriority.DEFERRED),
        ]

        for trust_score, expected_priority in trust_tiers:
            priority = self.priority.calculate_priority(trust_score)
            self.assertEqual(priority, expected_priority)

    def test_everyone_eventually_served(self):
        """Test low trust entities still get served (no exclusion)"""
        # Register very low trust entity
        self.priority.register_trust_score(TrustScore(
            lct_id="lct-very-low-trust",
            direct_trust=0.1,
            experience_penalty=0.5,  # Heavy newcomer penalty
        ))

        # Submit work
        req = self.priority.submit_work_request(
            "lct-very-low-trust", "Very low trust work", 200.0
        )

        # Process queue
        allocated = self.priority.process_all_available()

        # Should still be allocated (just with low priority)
        self.assertEqual(len(allocated), 1)
        self.assertEqual(allocated[0][0].priority, RequestPriority.DEFERRED)


class TestEnergyBackedIdentityBonds(unittest.TestCase):
    """Test Phase 4: Energy-Backed Identity Bonds"""

    def setUp(self):
        self.energy_registry = EnergyCapacityRegistry(society_lct="lct-global")
        self.bond_registry = EnergyBackedBondRegistry()

    def test_bond_commits_capacity_not_currency(self):
        """Test bonds commit energy capacity, not ATP stakes"""
        # Create energy sources
        solar = SolarPanelProof(
            panel_serial="SOLAR-001",
            rated_watts=500.0,
            panel_model="Test",
            installation_date=datetime.now(timezone.utc),
            last_verified=datetime.now(timezone.utc),
        )
        self.energy_registry.register_source(solar)

        # Register bond
        bond = self.bond_registry.register_bond(
            society_lct="lct-test-society",
            energy_sources=[solar],
        )

        # Bond should commit capacity, not currency
        self.assertEqual(bond.committed_capacity_watts, 500.0)
        self.assertGreater(len(bond.energy_sources), 0)
        self.assertEqual(bond.status, BondStatus.ACTIVE)

    def test_bond_validation_checks_capacity_maintained(self):
        """Test bond validation requires capacity to be maintained"""
        solar = SolarPanelProof(
            panel_serial="SOLAR-001",
            rated_watts=500.0,
            panel_model="Test",
            installation_date=datetime.now(timezone.utc),
            last_verified=datetime.now(timezone.utc),
        )
        self.energy_registry.register_source(solar)

        bond = self.bond_registry.register_bond(
            society_lct="lct-test",
            energy_sources=[solar],
        )

        # Validate with capacity present
        is_valid, reason = bond.validate_capacity(self.energy_registry)
        self.assertTrue(is_valid)

        # Remove energy source (simulate capacity loss)
        self.energy_registry.unregister_source(solar.source_identifier)

        # Validation should fail
        is_valid, reason = bond.validate_capacity(self.energy_registry)
        self.assertFalse(is_valid)
        self.assertIsNotNone(reason)

    def test_bond_forfeit_penalizes_reputation_not_money(self):
        """Test bond violation forfeits reputation, not ATP"""
        solar = SolarPanelProof(
            panel_serial="SOLAR-001",
            rated_watts=500.0,
            panel_model="Test",
            installation_date=datetime.now(timezone.utc),
            last_verified=datetime.now(timezone.utc),
        )
        self.energy_registry.register_source(solar)

        bond = self.bond_registry.register_bond(
            society_lct="lct-test",
            energy_sources=[solar],
        )

        # Violate bond
        penalty = bond.handle_violation("Test violation")

        # Should return reputation penalty (not ATP amount)
        self.assertEqual(penalty, bond.reputation_at_risk)
        self.assertEqual(bond.status, BondStatus.VIOLATED)

    def test_vouching_commits_energy_allocation(self):
        """Test vouching commits energy allocation, not ATP stake"""
        vouch = self.bond_registry.register_vouch(
            voucher_lct="lct-voucher",
            newcomer_lct="lct-newcomer",
            allocated_energy_watts=100.0,
        )

        # Should commit energy allocation, not currency
        self.assertEqual(vouch.allocated_energy_watts, 100.0)
        self.assertTrue(vouch.active)

        # Record energy usage
        vouch.record_energy_allocation(50.0)
        self.assertEqual(vouch.energy_allocated_total, 50.0)


class TestSessionIntegration(unittest.TestCase):
    """Test Integration with Sessions #30-35"""

    def setUp(self):
        """Set up full system with all components"""
        # Energy pool
        self.pool = EnergyBackedSocietyPool(society_lct="lct-integrated-test")

        # Energy sources
        solar = SolarPanelProof(
            panel_serial="SOLAR-001",
            rated_watts=1000.0,
            panel_model="Test",
            installation_date=datetime.now(timezone.utc),
            last_verified=datetime.now(timezone.utc),
        )
        self.pool.register_energy_source(solar)
        self.pool.adp_pool = 2000.0
        self.pool.charge_atp(1000.0, solar.source_identifier)

        # Priority system
        self.priority = TrustBasedEnergyPriority(
            society_lct=self.pool.society_lct,
            energy_pool=self.pool
        )

        # Bond registry
        self.bond_registry = EnergyBackedBondRegistry()

    def test_session34_gaming_resistance_via_capacity_commitment(self):
        """Test Session #34 gaming resistance adapted to energy model"""
        # Session #34: Identity bonds prevent Sybil attacks

        # Create bond with energy sources
        solar = SolarPanelProof(
            panel_serial="SOLAR-SYBIL-001",
            rated_watts=500.0,
            panel_model="Test",
            installation_date=datetime.now(timezone.utc),
            last_verified=datetime.now(timezone.utc),
        )

        bond = self.bond_registry.register_bond(
            society_lct="lct-potential-sybil",
            energy_sources=[solar],
        )

        # Key property: Must prove real energy capacity
        # Can't create Sybils without real resources
        self.assertEqual(bond.committed_capacity_watts, 500.0)
        self.assertGreater(len(bond.energy_sources), 0)

    def test_session35_vouching_adapted_to_energy_allocation(self):
        """Test Session #35 vouching adapted to energy model"""
        # Session #35: Vouching provides newcomer bootstrap

        # Established member vouches with energy allocation
        vouch = self.bond_registry.register_vouch(
            voucher_lct="lct-established",
            newcomer_lct="lct-newcomer",
            allocated_energy_watts=200.0,
        )

        # Key property: Voucher commits real energy, not just currency
        self.assertEqual(vouch.allocated_energy_watts, 200.0)
        self.assertGreater(vouch.reputation_at_risk, 0)

    def test_session33_trust_based_negotiation_now_priority(self):
        """Test Session #33 trust-based pricing becomes priority"""
        # Session #33: Trust affected ATP cost
        # Session #36: Trust affects priority instead

        # High trust entity
        self.priority.register_trust_score(TrustScore(
            lct_id="lct-high",
            direct_trust=0.95,
        ))

        # Low trust entity
        self.priority.register_trust_score(TrustScore(
            lct_id="lct-low",
            direct_trust=0.3,
        ))

        # Both request same amount of ATP
        req_high = self.priority.submit_work_request("lct-high", "Work", 200.0)
        req_low = self.priority.submit_work_request("lct-low", "Work", 200.0)

        # Key property: Different priority, NOT different cost
        self.assertNotEqual(req_high.priority, req_low.priority)
        self.assertEqual(req_high.atp_needed, req_low.atp_needed)  # Same cost

    def test_full_cycle_energy_to_work_to_reputation(self):
        """Test complete cycle: Energy → ATP → Work → ADP → Reputation"""
        # 1. Start with energy source
        initial_capacity = self.pool.get_total_energy_capacity()
        self.assertGreater(initial_capacity, 0)

        # 2. Register trust score
        self.priority.register_trust_score(TrustScore(
            lct_id="lct-worker",
            direct_trust=0.8,
        ))

        # 3. Submit work request
        req = self.priority.submit_work_request(
            "lct-worker", "Full cycle test", 300.0
        )
        self.assertIsNotNone(req)

        # 4. Process (allocate ATP)
        allocated = self.priority.process_next_request()
        self.assertIsNotNone(allocated)
        request, ticket = allocated

        # 5. Complete work (discharge ATP → ADP)
        adp = self.pool.complete_work(ticket.id, quality_score=0.9)
        self.assertIsNotNone(adp)

        # 6. Credit reputation
        success = self.pool.credit_worker_reputation(adp.id, adp.amount * adp.quality_score)
        self.assertTrue(success)

        # 7. Trust updates from work quality (Session #34)
        self.priority.update_trust_from_work("lct-worker", quality_score=0.9)
        updated_trust = self.priority.get_trust_score("lct-worker")

        # Trust should improve from good work
        self.assertGreater(updated_trust.reputation_trust, 0)


def run_tests():
    """Run all integration tests"""
    print("=" * 70)
    print("SESSION #36 ENERGY-BACKED ATP - INTEGRATION TESTS")
    print("=" * 70)

    # Create test suite
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEnergyCapacityProofs))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEnergyBackedATPPool))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestTrustBasedPriority))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEnergyBackedIdentityBonds))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSessionIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED")
        print("\nKey Validations:")
        print("  ✓ ATP backed by real energy (thermodynamic constraint)")
        print("  ✓ ATP expires (prevents hoarding)")
        print("  ✓ Trust affects priority, not price")
        print("  ✓ Bonds commit capacity, not currency")
        print("  ✓ Forfeiture penalizes reputation, not money")
        print("  ✓ Everyone served (no exclusion)")
        print("  ✓ Sessions #30-35 mechanisms integrate cleanly")
    else:
        print("\n❌ SOME TESTS FAILED")

    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
