"""Check which imports from integrated_society_node.py are broken"""

import sys

# Test each import separately
imports_to_test = [
    ("energy_capacity", ["EnergyCapacityRegistry", "EnergySourceType"]),
    ("energy_backed_atp", ["EnergyBackedATP", "ATPAllocation"]),
    ("energy_backed_identity_bond", ["EnergyBackedIdentityBond", "IdentityBond"]),
    ("hardened_energy_system", ["HardenedEnergyCapacityRegistry", "HardenedEnergyBackedIdentityBond"]),
    ("cross_society_messaging", ["CrossSocietyMessage", "CrossSocietyMessageBus", "MessageType", "SocietyCoordinator"]),
    ("cross_society_atp_exchange", ["ATPMarketplace", "ATPOffer", "ATPBid", "ATPExchange"]),
    ("cross_society_trust_propagation", ["TrustPropagationEngine", "TrustRecord"]),
    ("cross_society_security_mitigations", ["SecureATPMarketplace", "SybilIsolationEngine", "RateLimitedMessageBus"]),
    ("trust_ceiling_mitigation", ["TrustCeilingEngine", "RobustTrustEngine"]),
    ("energy_based_sybil_resistance", ["EnergyCapacityProof", "EnergySybilResistance"]),
    ("web4_crypto", ["KeyPair", "Web4Crypto"]),
]

print("=" * 80)
print("IMPORT CHECK FOR integrated_society_node.py")
print("=" * 80)

broken_imports = []

for module_name, items in imports_to_test:
    print(f"\n### Checking {module_name}")
    try:
        module = __import__(module_name)
        for item in items:
            if hasattr(module, item):
                print(f"  ✅ {item}")
            else:
                print(f"  ❌ {item} (not found in module)")
                broken_imports.append((module_name, item))
    except ImportError as e:
        print(f"  ❌ Module import failed: {e}")
        for item in items:
            broken_imports.append((module_name, item))

print("\n" + "=" * 80)
if broken_imports:
    print(f"BROKEN IMPORTS: {len(broken_imports)}")
    print("=" * 80)
    for module, item in broken_imports:
        print(f"  {module}.{item}")
else:
    print("ALL IMPORTS OK")
    print("=" * 80)
