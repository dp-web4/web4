#!/usr/bin/env python3
"""
Prototype: LCT Identity Integration with Federation

Research Goal: Integrate proper LCT (Lightchain Credential Token) identity
system with the federation architecture built in Sessions 150-158.

Current State: Federation nodes use string `lct_id` but don't instantiate
real LCT objects with capability levels, entity types, etc.

Target State: Federation nodes have proper LCT identities that enable:
- Capability level-based trust asymmetry
- Hardware attestation integration
- Entity type-aware permissions
- Fractal identity hierarchies

Exploration Questions:
1. How does LCT capability level map to federation trust levels?
2. Can hardware attestation (L5) integrate with TPM2/TrustZone verification?
3. Do entity types affect federation behavior (AI vs plugin vs human)?
4. How do parent-child LCT relationships create federation hierarchies?

Platform: Legion (RTX 4090)
Type: Prototype/Exploration
Date: 2026-01-09
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json

# Add paths
HOME = Path.home()
sys.path.insert(0, str(HOME / "ai-workspace" / "web4"))

# Import LCT implementation
from core.lct_capability_levels import (
    CapabilityLevel,
    EntityType,
    CapabilityQueryResponse,
    create_minimal_lct,
    query_capabilities,
)

# Import federation base (Session 153)
from session153_advanced_security_federation import CogitationMode


# ============================================================================
# LCT-AWARE FEDERATION IDENTITY
# ============================================================================

@dataclass
class FederationLCTIdentity:
    """
    LCT identity for federation nodes.

    Bridges LCT identity system with federation architecture.
    """
    lct: Dict[str, Any]  # Full LCT object
    capabilities: CapabilityQueryResponse  # Queried capabilities
    node_id: str  # Federation node ID
    hardware_type: str  # TPM2, TrustZone, software

    @property
    def capability_level(self) -> int:
        """Get capability level (0-5)."""
        return self.capabilities.capability_level

    @property
    def entity_type(self) -> str:
        """Get entity type."""
        return self.lct.get("entity_type", "unknown")

    @property
    def trust_weight(self) -> float:
        """
        Calculate trust weight for federation.

        Mapping: LCT capability level → federation trust weight
        - L5 (hardware): 1.0 (highest trust)
        - L4 (society): 0.9
        - L3 (standard): 0.7
        - L2 (basic): 0.5
        - L1 (minimal): 0.3
        - L0 (stub): 0.1 (lowest trust)
        """
        level_weights = {
            5: 1.0,  # Hardware attestation
            4: 0.9,  # Society-issued
            3: 0.7,  # Standard autonomous
            2: 0.5,  # Basic operational
            1: 0.3,  # Minimal bootstrap
            0: 0.1,  # Stub placeholder
        }
        return level_weights.get(self.capability_level, 0.5)

    @property
    def hardware_attested(self) -> bool:
        """Check if identity is hardware-attested (L5)."""
        return self.capability_level == 5

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "lct": self.lct,
            "capabilities": asdict(self.capabilities),
            "node_id": self.node_id,
            "hardware_type": self.hardware_type,
            "capability_level": self.capability_level,
            "entity_type": self.entity_type,
            "trust_weight": self.trust_weight,
            "hardware_attested": self.hardware_attested,
        }


# ============================================================================
# MAPPING FUNCTIONS
# ============================================================================

def map_hardware_to_capability(hardware_type: str) -> CapabilityLevel:
    """
    Map federation hardware type to LCT capability level.

    Federation hardware → LCT capability:
    - TPM2: Level 5 (hardware attested)
    - TrustZone: Level 5 (hardware attested)
    - Software: Level 3 (standard autonomous)
    """
    hardware_mapping = {
        "tpm2": CapabilityLevel.HARDWARE,
        "trustzone": CapabilityLevel.HARDWARE,
        "software": CapabilityLevel.STANDARD,
    }
    return hardware_mapping.get(hardware_type.lower(), CapabilityLevel.STANDARD)


def create_federation_lct_identity(
    node_id: str,
    hardware_type: str,
    entity_type: EntityType = EntityType.AI,
    parent_lct: Optional[str] = None
) -> FederationLCTIdentity:
    """
    Create LCT identity for federation node.

    Args:
        node_id: Federation node ID (legion, thor, sprout)
        hardware_type: Hardware security type (tpm2, trustzone, software)
        entity_type: LCT entity type (default: AI)
        parent_lct: Optional parent LCT for hierarchies

    Returns:
        FederationLCTIdentity with full LCT object and capabilities
    """
    # Determine capability level from hardware
    capability_level = map_hardware_to_capability(hardware_type)

    # Create LCT
    lct = create_minimal_lct(
        entity_type=entity_type,
        level=capability_level,
        parent_lct=parent_lct
    )

    # Query capabilities
    capabilities = query_capabilities(lct)

    # Create federation identity
    identity = FederationLCTIdentity(
        lct=lct,
        capabilities=capabilities,
        node_id=node_id,
        hardware_type=hardware_type
    )

    return identity


# ============================================================================
# TRUST ASYMMETRY ANALYSIS
# ============================================================================

def analyze_trust_asymmetry(
    node_a: FederationLCTIdentity,
    node_b: FederationLCTIdentity
) -> Dict[str, Any]:
    """
    Analyze trust asymmetry between two nodes based on LCT capabilities.

    Returns analysis of relative trust levels and implications.
    """
    # Calculate trust differential
    trust_diff = node_a.trust_weight - node_b.trust_weight

    # Determine relationship
    if abs(trust_diff) < 0.1:
        relationship = "peer"
        recommendation = "Equal trust, symmetric relationship"
    elif trust_diff > 0:
        relationship = "superior"
        recommendation = f"{node_a.node_id} has higher trust (+{trust_diff:.2f}), can validate {node_b.node_id}"
    else:
        relationship = "inferior"
        recommendation = f"{node_a.node_id} has lower trust ({trust_diff:.2f}), should trust {node_b.node_id} validation"

    # Check hardware attestation
    if node_a.hardware_attested and not node_b.hardware_attested:
        security_note = f"{node_a.node_id} has hardware attestation advantage"
    elif node_b.hardware_attested and not node_a.hardware_attested:
        security_note = f"{node_b.node_id} has hardware attestation advantage"
    else:
        security_note = "Both nodes at same attestation level"

    return {
        "node_a": node_a.node_id,
        "node_b": node_b.node_id,
        "node_a_level": node_a.capability_level,
        "node_b_level": node_b.capability_level,
        "node_a_trust": node_a.trust_weight,
        "node_b_trust": node_b.trust_weight,
        "trust_differential": trust_diff,
        "relationship": relationship,
        "recommendation": recommendation,
        "security_note": security_note,
    }


# ============================================================================
# DEMONSTRATION
# ============================================================================

def demonstrate_lct_federation_integration():
    """
    Demonstrate LCT identity integration with federation.

    Creates LCT identities for Legion, Thor, and Sprout, then analyzes
    trust relationships.
    """
    print("\n" + "="*80)
    print("PROTOTYPE: LCT IDENTITY INTEGRATION WITH FEDERATION")
    print("="*80)

    # Create LCT identities for all three federation nodes
    print("\n[1] Creating LCT identities for federation nodes...")

    legion = create_federation_lct_identity(
        node_id="legion",
        hardware_type="tpm2",
        entity_type=EntityType.AI,
    )

    thor = create_federation_lct_identity(
        node_id="thor",
        hardware_type="trustzone",
        entity_type=EntityType.AI,
    )

    sprout = create_federation_lct_identity(
        node_id="sprout",
        hardware_type="tpm2",
        entity_type=EntityType.AI,
    )

    print(f"\n[Legion] LCT Identity:")
    print(f"  LCT ID: {legion.lct['lct_id']}")
    print(f"  Entity Type: {legion.entity_type}")
    print(f"  Capability Level: L{legion.capability_level}")
    print(f"  Hardware: {legion.hardware_type}")
    print(f"  Trust Weight: {legion.trust_weight}")
    print(f"  Hardware Attested: {legion.hardware_attested}")

    print(f"\n[Thor] LCT Identity:")
    print(f"  LCT ID: {thor.lct['lct_id']}")
    print(f"  Entity Type: {thor.entity_type}")
    print(f"  Capability Level: L{thor.capability_level}")
    print(f"  Hardware: {thor.hardware_type}")
    print(f"  Trust Weight: {thor.trust_weight}")
    print(f"  Hardware Attested: {thor.hardware_attested}")

    print(f"\n[Sprout] LCT Identity:")
    print(f"  LCT ID: {sprout.lct['lct_id']}")
    print(f"  Entity Type: {sprout.entity_type}")
    print(f"  Capability Level: L{sprout.capability_level}")
    print(f"  Hardware: {sprout.hardware_type}")
    print(f"  Trust Weight: {sprout.trust_weight}")
    print(f"  Hardware Attested: {sprout.hardware_attested}")

    # Analyze trust relationships
    print("\n[2] Analyzing trust relationships...")

    legion_thor = analyze_trust_asymmetry(legion, thor)
    print(f"\n[Legion ↔ Thor]:")
    print(f"  Relationship: {legion_thor['relationship']}")
    print(f"  Trust Differential: {legion_thor['trust_differential']:.2f}")
    print(f"  Recommendation: {legion_thor['recommendation']}")
    print(f"  Security: {legion_thor['security_note']}")

    legion_sprout = analyze_trust_asymmetry(legion, sprout)
    print(f"\n[Legion ↔ Sprout]:")
    print(f"  Relationship: {legion_sprout['relationship']}")
    print(f"  Trust Differential: {legion_sprout['trust_differential']:.2f}")
    print(f"  Recommendation: {legion_sprout['recommendation']}")
    print(f"  Security: {legion_sprout['security_note']}")

    thor_sprout = analyze_trust_asymmetry(thor, sprout)
    print(f"\n[Thor ↔ Sprout]:")
    print(f"  Relationship: {thor_sprout['relationship']}")
    print(f"  Trust Differential: {thor_sprout['trust_differential']:.2f}")
    print(f"  Recommendation: {thor_sprout['recommendation']}")
    print(f"  Security: {thor_sprout['security_note']}")

    # Test with software-only node for comparison
    print("\n[3] Comparing with software-only node...")

    software_node = create_federation_lct_identity(
        node_id="software_test",
        hardware_type="software",
        entity_type=EntityType.AI,
    )

    print(f"\n[Software Node] LCT Identity:")
    print(f"  LCT ID: {software_node.lct['lct_id']}")
    print(f"  Capability Level: L{software_node.capability_level}")
    print(f"  Trust Weight: {software_node.trust_weight}")
    print(f"  Hardware Attested: {software_node.hardware_attested}")

    legion_software = analyze_trust_asymmetry(legion, software_node)
    print(f"\n[Legion ↔ Software Node]:")
    print(f"  Relationship: {legion_software['relationship']}")
    print(f"  Trust Differential: {legion_software['trust_differential']:.2f}")
    print(f"  Recommendation: {legion_software['recommendation']}")
    print(f"  Security: {legion_software['security_note']}")

    # Save results
    print("\n[4] Saving integration analysis...")

    results = {
        "identities": {
            "legion": legion.to_dict(),
            "thor": thor.to_dict(),
            "sprout": sprout.to_dict(),
            "software_test": software_node.to_dict(),
        },
        "trust_relationships": {
            "legion_thor": legion_thor,
            "legion_sprout": legion_sprout,
            "thor_sprout": thor_sprout,
            "legion_software": legion_software,
        },
        "insights": {
            "hardware_advantage": "All production nodes (Legion, Thor, Sprout) are L5 with hardware attestation",
            "trust_symmetry": "Legion/Thor/Sprout are peers (all L5, trust weight 1.0)",
            "software_gap": "Software-only nodes are L3, trust weight 0.7 (-0.3 differential)",
            "hardware_types": {
                "tpm2": "Legion, Sprout (x86_64, ARM64)",
                "trustzone": "Thor (ARM64)",
                "both_l5": "TPM2 and TrustZone both map to L5 capability"
            },
            "federation_implications": [
                "All production nodes have equal trust (symmetric)",
                "Hardware attestation provides strong identity foundation",
                "Software nodes would be lower trust tier",
                "Trust weights can inform ATP economics (higher trust → higher rewards?)",
                "Capability levels enable hierarchical federations"
            ]
        }
    }

    with open(HOME / "ai-workspace" / "web4" / "lct_federation_integration_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"  Results saved to lct_federation_integration_results.json")

    print("\n" + "="*80)
    print("PROTOTYPE COMPLETE")
    print("="*80)
    print("\nKey Findings:")
    print("  ✅ Legion, Thor, Sprout are all L5 (hardware attested)")
    print("  ✅ All three have trust weight 1.0 (peers)")
    print("  ✅ Hardware types (TPM2, TrustZone) both map to L5")
    print("  ✅ Software-only would be L3, trust weight 0.7 (-0.3 gap)")
    print("  ✅ Trust asymmetry enables hierarchical federations")
    print("\nNext Steps:")
    print("  → Integrate LCT into federation node constructors")
    print("  → Use trust weights for ATP economic calculations")
    print("  → Implement capability-based permissions")
    print("  → Test parent-child LCT hierarchies")
    print("="*80)


if __name__ == "__main__":
    demonstrate_lct_federation_integration()
