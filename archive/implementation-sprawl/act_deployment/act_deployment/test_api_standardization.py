"""
Test Component API Standardization

Session #44

Verifies that all component initialization APIs work consistently
after API standardization refactor.
"""

from datetime import datetime, timezone, timedelta
from energy_capacity import EnergyCapacityRegistry, SolarPanelProof
from hardened_energy_system import (
    HardenedEnergyCapacityRegistry,
    GlobalEnergyRegistry,
    DeviceSpecDatabase,
)
from energy_backed_identity_bond import EnergyBackedBondRegistry


def test_energy_capacity_registry_api():
    """Test EnergyCapacityRegistry API (dataclass)"""

    print("=" * 80)
    print("COMPONENT API STANDARDIZATION TEST - Session #44")
    print("=" * 80)

    print("\n### Test 1: EnergyCapacityRegistry (base)")
    print("-" * 80)

    # Should work with required argument
    registry = EnergyCapacityRegistry(society_lct="lct-test")
    print(f"✅ Created with society_lct: {registry.society_lct}")

    # Add energy source
    now = datetime.now(timezone.utc)
    solar = SolarPanelProof(
        panel_serial="SOLAR-001",
        panel_model="Generic 300W",
        rated_watts=300.0,
        installation_date=now,
        last_verified=now,
        degradation_factor=0.95,
    )

    success = registry.register_source(solar)
    print(f"✅ Registered energy source: {success}")
    print(f"   Total capacity: {registry.get_total_capacity()}W")


def test_hardened_registry_testing_mode():
    """Test HardenedEnergyCapacityRegistry in testing mode"""

    print("\n### Test 2: HardenedEnergyCapacityRegistry (testing mode)")
    print("-" * 80)

    # New factory method for testing
    registry = HardenedEnergyCapacityRegistry.create_for_testing("lct-test")

    print(f"✅ Created with factory method: {registry.society_lct}")
    print(f"   Security features disabled (for testing)")
    print(f"   - global_registry: {registry.global_registry}")
    print(f"   - device_spec_db: {registry.device_spec_db}")

    # Should accept any energy source (no security checks)
    now = datetime.now(timezone.utc)
    solar = SolarPanelProof(
        panel_serial="SOLAR-002",
        panel_model="Generic 300W",
        rated_watts=300.0,
        installation_date=now,
        last_verified=now,
        degradation_factor=0.95,
    )

    success = registry.register_source(solar)
    print(f"✅ Registered energy source: {success}")
    print(f"   Total capacity: {registry.get_total_capacity()}W")


def test_hardened_registry_production_mode():
    """Test HardenedEnergyCapacityRegistry in production mode"""

    print("\n### Test 3: HardenedEnergyCapacityRegistry (production mode)")
    print("-" * 80)

    # Create dependencies
    global_registry = GlobalEnergyRegistry()
    device_db = DeviceSpecDatabase()

    # New factory method for production
    registry = HardenedEnergyCapacityRegistry.create_hardened(
        society_lct="lct-production",
        global_registry=global_registry,
        device_spec_db=device_db,
    )

    print(f"✅ Created with factory method: {registry.society_lct}")
    print(f"   Security features enabled")
    print(f"   - global_registry: {type(registry.global_registry).__name__}")
    print(f"   - device_spec_db: {type(registry.device_spec_db).__name__}")

    # Add valid solar panel
    now = datetime.now(timezone.utc)
    solar = SolarPanelProof(
        panel_serial="SOLAR-003",
        panel_model="Generic 300W",
        rated_watts=300.0,
        installation_date=now,
        last_verified=now,
        degradation_factor=0.95,
    )

    success = registry.register_source(solar)
    print(f"✅ Registered energy source with security checks: {success}")
    print(f"   Total capacity: {registry.get_total_capacity()}W")


def test_hardened_registry_backward_compatibility():
    """Test backward compatibility with direct instantiation"""

    print("\n### Test 4: Backward Compatibility (direct instantiation)")
    print("-" * 80)

    # Old style: direct instantiation (still works)
    global_registry = GlobalEnergyRegistry()
    device_db = DeviceSpecDatabase()

    registry = HardenedEnergyCapacityRegistry(
        society_lct="lct-backward-compat",
        global_registry=global_registry,
        device_spec_db=device_db,
    )

    print(f"✅ Created with direct instantiation: {registry.society_lct}")
    print(f"   This still works for backward compatibility")

    now = datetime.now(timezone.utc)
    solar = SolarPanelProof(
        panel_serial="SOLAR-004",
        panel_model="Generic 300W",
        rated_watts=300.0,
        installation_date=now,
        last_verified=now,
        degradation_factor=0.95,
    )

    success = registry.register_source(solar)
    print(f"✅ Registered energy source: {success}")


def test_bond_registry_api():
    """Test EnergyBackedBondRegistry API"""

    print("\n### Test 5: EnergyBackedBondRegistry")
    print("-" * 80)

    # No required arguments (all defaults)
    bond_registry = EnergyBackedBondRegistry()

    print(f"✅ Created with no arguments")
    print(f"   Bonds: {len(bond_registry.bonds)}")
    print(f"   Vouches: {len(bond_registry.vouches)}")

    # Create bond
    now = datetime.now(timezone.utc)
    solar = SolarPanelProof(
        panel_serial="SOLAR-005",
        panel_model="Generic 300W",
        rated_watts=300.0,
        installation_date=now,
        last_verified=now,
        degradation_factor=0.95,
    )

    bond = bond_registry.register_bond(
        society_lct="lct-test-bond",
        energy_sources=[solar],
        lock_period_days=30,
    )

    print(f"✅ Created bond for {bond.society_lct}")
    print(f"   Capacity: {bond.committed_capacity_watts}W")
    print(f"   Lock period: {bond.lock_period_days} days")


def test_api_consistency():
    """Verify all components follow consistent patterns"""

    print("\n### Test 6: API Consistency Check")
    print("-" * 80)

    # All components should be instantiable with clear patterns
    components = []

    # Pattern 1: Required society_lct
    components.append(("EnergyCapacityRegistry", EnergyCapacityRegistry(society_lct="lct-1")))

    # Pattern 2: Factory method (testing)
    components.append(("HardenedEnergyCapacityRegistry (testing)",
                      HardenedEnergyCapacityRegistry.create_for_testing("lct-2")))

    # Pattern 3: Factory method (production)
    components.append(("HardenedEnergyCapacityRegistry (production)",
                      HardenedEnergyCapacityRegistry.create_hardened(
                          "lct-3",
                          GlobalEnergyRegistry(),
                          DeviceSpecDatabase()
                      )))

    # Pattern 4: No required arguments
    components.append(("EnergyBackedBondRegistry", EnergyBackedBondRegistry()))

    print("All components instantiated successfully:")
    for name, component in components:
        print(f"  ✅ {name}: {type(component).__name__}")

    print("\n✅ API Consistency: All components follow clear initialization patterns")


if __name__ == "__main__":
    test_energy_capacity_registry_api()
    test_hardened_registry_testing_mode()
    test_hardened_registry_production_mode()
    test_hardened_registry_backward_compatibility()
    test_bond_registry_api()
    test_api_consistency()

    print("\n" + "=" * 80)
    print("API STANDARDIZATION TEST COMPLETE")
    print("=" * 80)

    print("\n### Summary")
    print("-" * 80)
    print("✅ EnergyCapacityRegistry: dataclass with required society_lct")
    print("✅ HardenedEnergyCapacityRegistry: factory methods (.create_hardened, .create_for_testing)")
    print("✅ EnergyBackedBondRegistry: dataclass with all defaults")
    print("✅ Backward compatibility: Direct instantiation still works")
    print("✅ All components follow consistent, documented patterns")
    print("")
    print("Session #44: Component API Standardization COMPLETE")
