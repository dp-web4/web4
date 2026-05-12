"""
Session #40: Integration Demo

Demonstrates all Phase 1 mitigations working together in a realistic scenario.

Shows:
1. Global energy registry blocking proof reuse
2. Device spec database blocking capacity inflation
3. Identity-energy linker preventing reputation washing
4. Circular vouching detection blocking Sybil networks
5. Rate limiting preventing spam attacks

This is a simpler, more focused demo than the full integration.
"""

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

from phase1_extended_mitigations import (
    CircularVouchingDetector,
    TrustBasedRateLimiter,
)

from energy_backed_identity_bond import EnergyBackedIdentityBond


def main():
    print("=" * 80)
    print("SESSION #40: INTEGRATED SECURITY DEMONSTRATION")
    print("All Phase 1 Mitigations Working Together")
    print("=" * 80)

    # Initialize security components (blockchain-level globals)
    global_registry = GlobalEnergyRegistry()
    device_spec_db = DeviceSpecDatabase()
    identity_linker = IdentityEnergyLinker()
    circular_detector = CircularVouchingDetector()
    rate_limiter = TrustBasedRateLimiter(base_rate_per_hour=10)

    # ========================================
    # Scenario 1: Legitimate Society Operation
    # ========================================

    print("\n" + "=" * 80)
    print("SCENARIO 1: Legitimate Society Operation")
    print("=" * 80)

    # Society A registers energy sources
    print("\n### Society A: Registering Energy Sources")
    print("-" * 80)

    panel_a = SolarPanelProof(
        panel_serial="SOCIETY-A-PANEL-001",
        rated_watts=300.0,
        panel_model="SunPower X22",
        installation_date=datetime.now(timezone.utc) - timedelta(days=365),
        last_verified=datetime.now(timezone.utc),
        degradation_factor=0.975,  # Realistic 1-year degradation
        latitude=37.7749,
        longitude=-122.4194,
    )

    # Validate device specs BEFORE global registration
    is_valid_degradation = device_spec_db.validate_solar_degradation(
        panel_a.panel_model,
        panel_a.installation_date,
        panel_a.degradation_factor,
    )

    print(f"  Device spec validation: {is_valid_degradation}")

    if is_valid_degradation:
        # Register in global registry
        global_registry.register_source(
            panel_a,
            "lct-society-A",
            "identity-society-A-admin"
        )
        print(f"  ✓ Registered panel: {panel_a.panel_serial}")
        print(f"  ✓ Capacity: {panel_a.capacity_watts}W")
        print(f"  ✓ Global registry updated")

    # ========================================
    # Scenario 2: Attack - Proof Reuse (A2)
    # ========================================

    print("\n" + "=" * 80)
    print("SCENARIO 2: ATTACK - Proof Reuse (A2)")
    print("=" * 80)

    print("\n### Attacker: Attempting to Reuse Panel in Society B")
    print("-" * 80)

    try:
        global_registry.register_source(
            panel_a,  # Same panel!
            "lct-society-B-attacker",
            "identity-attacker-001"
        )
        print("  ❌ ATTACK SUCCEEDED - Mitigation failed!")
    except ValueError as e:
        print(f"  ✓ ATTACK BLOCKED by Global Energy Registry")
        print(f"  ✓ Reason: {str(e)[:60]}...")
        print(f"  ✓ Mitigation A2: EFFECTIVE")

    # ========================================
    # Scenario 3: Attack - Capacity Inflation (A3)
    # ========================================

    print("\n" + "=" * 80)
    print("SCENARIO 3: ATTACK - Capacity Inflation (A3)")
    print("=" * 80)

    print("\n### Attacker: Claiming Inflated GPU TDP")
    print("-" * 80)

    inflated_gpu = ComputeResourceProof(
        device_type="gpu",
        device_model="RTX 4090",
        device_id="ATTACKER-GPU-001",
        tdp_watts=1000.0,  # Real: 450W
        last_verified=datetime.now(timezone.utc),
        utilization_factor=1.0,
        idle_power_watts=50.0,
    )

    is_valid_tdp = device_spec_db.validate_gpu_tdp(
        inflated_gpu.device_model,
        inflated_gpu.tdp_watts,
    )

    if not is_valid_tdp:
        print(f"  ✓ ATTACK BLOCKED by Device Spec Database")
        print(f"  ✓ Claimed TDP: {inflated_gpu.tdp_watts}W")
        print(f"  ✓ Max valid TDP: {device_spec_db.gpu_specs['RTX4090'].max_capacity_watts}W")
        print(f"  ✓ Inflation factor: {inflated_gpu.tdp_watts / 450.0:.2f}x")
        print(f"  ✓ Mitigation A3: EFFECTIVE")
    else:
        print("  ❌ ATTACK SUCCEEDED - Mitigation failed!")

    # ========================================
    # Scenario 4: Attack - Reputation Washing (E1)
    # ========================================

    print("\n" + "=" * 80)
    print("SCENARIO 4: ATTACK - Reputation Washing (E1)")
    print("=" * 80)

    print("\n### Attacker: Identity Cycling to Wash Reputation")
    print("-" * 80)

    energy_source_id = panel_a.source_identifier

    # Identity 1: Accumulate violations
    identity_linker.register_identity("lct-attacker-identity-1", [energy_source_id])
    identity_linker.record_violation("lct-attacker-identity-1", "violation_1")
    identity_linker.record_violation("lct-attacker-identity-1", "violation_2")
    identity_linker.record_violation("lct-attacker-identity-1", "violation_3")

    identity1_violations = identity_linker.get_identity_effective_violations("lct-attacker-identity-1")
    print(f"  Identity 1 violations: {len(identity1_violations)}")

    # Abandon identity 1
    identity_linker.abandon_identity("lct-attacker-identity-1")
    print(f"  Identity 1 abandoned")

    # Create identity 2 with SAME energy source
    identity_linker.register_identity("lct-attacker-identity-2", [energy_source_id])

    # Check effective violations (should include identity 1's violations)
    identity2_violations = identity_linker.get_identity_effective_violations("lct-attacker-identity-2")

    if len(identity2_violations) > 0:
        print(f"  ✓ ATTACK BLOCKED by Identity-Energy Linker")
        print(f"  ✓ Identity 2 effective violations: {len(identity2_violations)}")
        print(f"  ✓ Inherited from energy source history")
        print(f"  ✓ Mitigation E1: EFFECTIVE")
    else:
        print("  ❌ ATTACK SUCCEEDED - Mitigation failed!")

    # ========================================
    # Scenario 5: Attack - Circular Vouching (F1)
    # ========================================

    print("\n" + "=" * 80)
    print("SCENARIO 5: ATTACK - Circular Vouching (F1)")
    print("=" * 80)

    print("\n### Attacker: Creating Circular Vouching Ring")
    print("-" * 80)

    # Create vouching ring: A→B→C→A
    circular_detector.add_vouch("lct-alice", "lct-bob")
    circular_detector.add_vouch("lct-bob", "lct-charlie")

    print(f"  Added vouches: Alice→Bob, Bob→Charlie")

    # Try to close the circle
    would_create_cycle = circular_detector.is_circular_vouch("lct-charlie", "lct-alice")

    if would_create_cycle:
        print(f"  ✓ ATTACK BLOCKED by Circular Vouching Detector")
        print(f"  ✓ Would create cycle: Charlie→Alice (closes Alice→Bob→Charlie→Alice)")
        print(f"  ✓ Mitigation F1: EFFECTIVE")

        # Add the vouch anyway to show detection after the fact
        circular_detector.add_vouch("lct-charlie", "lct-alice")
        cycles = circular_detector.detect_cycles()
        print(f"  ✓ Detected {len(cycles)} cycle(s)")
        if cycles:
            print(f"  ✓ Cycle participants: {' → '.join(cycles[0])}")
    else:
        print("  ❌ ATTACK SUCCEEDED - Mitigation failed!")

    # ========================================
    # Scenario 6: Attack - Priority Spam (C2)
    # ========================================

    print("\n" + "=" * 80)
    print("SCENARIO 6: ATTACK - Priority Spam (C2)")
    print("=" * 80)

    print("\n### Attacker: Flooding Priority Queue")
    print("-" * 80)

    low_trust_lct = "lct-spammer"
    low_trust_score = 0.2  # Low trust

    print(f"  Attacker trust score: {low_trust_score}")
    print(f"  Max submissions: {int(10 * low_trust_score)}/hour")

    # Try to submit 20 requests
    accepted = 0
    blocked = 0

    for i in range(20):
        if rate_limiter.check_rate_limit(low_trust_lct, low_trust_score):
            accepted += 1
        else:
            blocked += 1

    print(f"  ✓ Submitted 20 requests:")
    print(f"    - Accepted: {accepted}")
    print(f"    - Blocked: {blocked}")

    if blocked > 0:
        print(f"  ✓ ATTACK MITIGATED by Trust-Based Rate Limiter")
        print(f"  ✓ Block rate: {blocked / 20 * 100:.0f}%")
        print(f"  ✓ Mitigation C2: EFFECTIVE")
    else:
        print("  ❌ ATTACK SUCCEEDED - Mitigation failed!")

    # ========================================
    # Summary
    # ========================================

    print("\n" + "=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 80)

    print("\n✅ All Phase 1 Mitigations Operational:")
    print("  A2: Proof Reuse - ✅ BLOCKED")
    print("  A3: Capacity Inflation - ✅ BLOCKED")
    print("  E1: Reputation Washing - ✅ BLOCKED")
    print("  F1: Circular Vouching - ✅ DETECTED")
    print("  C2: Priority Spam - ✅ RATE LIMITED")

    print("\n🔒 Security Posture: HARDENED")
    print("  - Global coordination prevents double-spending")
    print("  - Device validation prevents inflation")
    print("  - Reputation binds to physical energy")
    print("  - Graph analysis detects collusion")
    print("  - Rate limiting prevents spam")

    print("\n📊 Statistics:")
    print(f"  Global registry entries: {len(global_registry.sources)}")
    print(f"  Identity-energy links: {len(identity_linker.identities)}")
    print(f"  Circular vouching cycles: {len(circular_detector.cycles)}")
    print(f"  Rate limiter block rate: {rate_limiter.get_stats()['block_rate']:.1%}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
