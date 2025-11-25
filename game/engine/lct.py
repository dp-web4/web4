from __future__ import annotations

"""LCT (Linked Context Token) representation for Web4 game engine (v0).

This module provides a minimal LCT dataclass to bridge the gap between:
- Conceptual model: LCT as NFT on chain with embedded MRH/T3/V3
- v0 implementation: String identifiers with separate trust/context structures

The goal is to formalize LCT as a first-class object while keeping the
implementation lightweight for simulation purposes.

Key differences from reference implementation:
- No cryptographic signatures (simulation focus)
- Embedded T3 trust axes (game mechanic)
- MRH profile attached directly to LCT
- Block reference for on-chain provenance
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class LCT:
    """Linked Context Token - A non-fungible token on a society's blockchain.

    An LCT represents an entity (agent, society, role, resource) within Web4.
    Each LCT:
    - Has a unique identifier (lct_id)
    - Lives on a specific society's blockchain (owning_society_lct)
    - Carries trust metadata (T3 axes)
    - Has an MRH profile describing its temporal/spatial/complexity scope
    - Is linked to other LCTs via RDF-like edges (tracked separately)

    This is a v0 implementation - simplified but conceptually aligned with
    the whitepaper vision of LCTs as the fundamental identity/context unit.
    """

    # Core identity
    lct_id: str  # e.g., "lct:web4:agent:alice"
    lct_type: str  # "agent" | "society" | "role" | "resource" | "event"

    # Blockchain provenance
    owning_society_lct: str  # Which society's chain this LCT lives on
    created_at_block: int  # Block number where this LCT was created
    created_at_tick: int  # World tick when created

    # Trust metadata (T3-like)
    trust_axes: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # Example: {"T3": {"talent": 0.8, "training": 0.7, "temperament": 0.9, "composite": 0.8}}

    # Value metadata (V3 - Value through Verification)
    value_axes: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # Example: {"V3": {"valuation": 0.85, "veracity": 0.92, "validity": 0.95, "composite": 0.91}}

    # MRH profile (Memory, Reputation, History characteristics)
    mrh_profile: Dict[str, str] = field(default_factory=dict)
    # Example: {"deltaR": "local", "deltaT": "session", "deltaC": "agent-scale"}

    # Type-specific metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    # For agents: capabilities, resources, memberships
    # For societies: treasury, policies, member_count
    # For roles: permissions, constraints

    # Lifecycle
    is_active: bool = True
    deactivated_at_tick: Optional[int] = None

    def __post_init__(self):
        """Initialize default MRH profile if not provided."""
        if not self.mrh_profile:
            # Default MRH for most LCTs
            self.mrh_profile = {
                "deltaR": "local",
                "deltaT": "session",
                "deltaC": "agent-scale"
            }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize LCT to dictionary for storage/transmission."""
        return {
            "lct_id": self.lct_id,
            "lct_type": self.lct_type,
            "owning_society_lct": self.owning_society_lct,
            "created_at_block": self.created_at_block,
            "created_at_tick": self.created_at_tick,
            "trust_axes": self.trust_axes,
            "value_axes": self.value_axes,
            "mrh_profile": self.mrh_profile,
            "metadata": self.metadata,
            "is_active": self.is_active,
            "deactivated_at_tick": self.deactivated_at_tick
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LCT:
        """Deserialize LCT from dictionary."""
        return cls(**data)

    def deactivate(self, tick: int) -> None:
        """Mark this LCT as inactive (e.g., role revoked, agent banned)."""
        self.is_active = False
        self.deactivated_at_tick = tick

    def update_trust(self, t3_updates: Dict[str, float]) -> None:
        """Update T3 trust axes."""
        if "T3" not in self.trust_axes:
            self.trust_axes["T3"] = {
                "talent": 0.5,
                "training": 0.5,
                "temperament": 0.5,
                "composite": 0.5
            }

        for axis, value in t3_updates.items():
            self.trust_axes["T3"][axis] = value

        # Recalculate composite if individual axes updated
        if any(ax in t3_updates for ax in ["talent", "training", "temperament"]):
            t3 = self.trust_axes["T3"]
            t3["composite"] = (
                t3.get("talent", 0.5) +
                t3.get("training", 0.5) +
                t3.get("temperament", 0.5)
            ) / 3.0

    def update_value(self, v3_updates: Dict[str, float]) -> None:
        """Update V3 value axes.

        V3 represents Value through Verification:
        - Valuation: Subjective worth (variable, can exceed 1.0)
        - Veracity: Objective accuracy (0.0 to 1.0)
        - Validity: Confirmed value delivery (0.0 to 1.0)
        """
        if "V3" not in self.value_axes:
            self.value_axes["V3"] = {
                "valuation": 0.5,
                "veracity": 0.5,
                "validity": 0.5,
                "composite": 0.5
            }

        for axis, value in v3_updates.items():
            self.value_axes["V3"][axis] = value

        # Recalculate composite if individual axes updated
        if any(ax in v3_updates for ax in ["valuation", "veracity", "validity"]):
            v3 = self.value_axes["V3"]
            # Composite uses normalized valuation (clamped to 1.0) for fair averaging
            normalized_valuation = min(v3.get("valuation", 0.5), 1.0)
            v3["composite"] = (
                normalized_valuation +
                v3.get("veracity", 0.5) +
                v3.get("validity", 0.5)
            ) / 3.0


# Factory functions for creating LCTs

def create_agent_lct(
    *,
    agent_id: str,
    owning_society_lct: str,
    block_number: int,
    tick: int,
    initial_trust: Optional[Dict[str, float]] = None,
    initial_value: Optional[Dict[str, float]] = None,
    capabilities: Optional[Dict[str, float]] = None,
    resources: Optional[Dict[str, float]] = None,
    memberships: Optional[List[str]] = None
) -> LCT:
    """Create an LCT for an agent."""
    lct_id = f"lct:web4:agent:{agent_id}"

    trust_axes = {}
    if initial_trust:
        trust_axes["T3"] = initial_trust
    else:
        # Default trust profile
        trust_axes["T3"] = {
            "talent": 0.5,
            "training": 0.5,
            "temperament": 0.5,
            "composite": 0.5
        }

    value_axes = {}
    if initial_value:
        value_axes["V3"] = initial_value
    else:
        # Default value profile
        value_axes["V3"] = {
            "valuation": 0.5,
            "veracity": 0.5,
            "validity": 0.5,
            "composite": 0.5
        }

    metadata = {
        "capabilities": capabilities or {},
        "resources": resources or {},
        "memberships": memberships or []
    }

    return LCT(
        lct_id=lct_id,
        lct_type="agent",
        owning_society_lct=owning_society_lct,
        created_at_block=block_number,
        created_at_tick=tick,
        trust_axes=trust_axes,
        value_axes=value_axes,
        metadata=metadata,
        mrh_profile={
            "deltaR": "local",
            "deltaT": "day",  # Agents persist
            "deltaC": "agent-scale"
        }
    )


def create_society_lct(
    *,
    society_id: str,
    block_number: int,
    tick: int,
    initial_treasury: Optional[Dict[str, float]] = None,
    policies: Optional[Dict[str, str]] = None
) -> LCT:
    """Create an LCT for a society (self-referential ownership)."""
    lct_id = f"lct:web4:society:{society_id}"

    metadata = {
        "treasury": initial_treasury or {},
        "policies": policies or {},
        "member_count": 0
    }

    return LCT(
        lct_id=lct_id,
        lct_type="society",
        owning_society_lct=lct_id,  # Society owns itself
        created_at_block=block_number,
        created_at_tick=tick,
        trust_axes={
            "T3": {
                "talent": 0.7,
                "training": 0.7,
                "temperament": 0.7,
                "composite": 0.7
            }
        },
        metadata=metadata,
        mrh_profile={
            "deltaR": "local",
            "deltaT": "epoch",  # Societies are long-lived
            "deltaC": "society-scale"
        }
    )


def create_role_lct(
    *,
    role_name: str,
    society_lct: str,
    block_number: int,
    tick: int,
    permissions: Optional[List[str]] = None,
    constraints: Optional[Dict[str, Any]] = None
) -> LCT:
    """Create an LCT for a role within a society."""
    # Extract society fragment for role namespace
    society_fragment = society_lct.split(":")[-1]
    lct_id = f"lct:web4:role:{society_fragment}:{role_name}"

    metadata = {
        "role_name": role_name,
        "permissions": permissions or [],
        "constraints": constraints or {}
    }

    return LCT(
        lct_id=lct_id,
        lct_type="role",
        owning_society_lct=society_lct,
        created_at_block=block_number,
        created_at_tick=tick,
        metadata=metadata,
        mrh_profile={
            "deltaR": "local",
            "deltaT": "day",  # Roles persist but can be revoked
            "deltaC": "agent-scale"
        }
    )


# Registry for managing LCTs in a World

@dataclass
class LCTRegistry:
    """Registry for all LCTs in a simulation world.

    This provides a central store for LCT objects, replacing the scattered
    string-based LCT references throughout the codebase.
    """

    lcts: Dict[str, LCT] = field(default_factory=dict)  # keyed by lct_id

    def register(self, lct: LCT) -> None:
        """Add an LCT to the registry."""
        self.lcts[lct.lct_id] = lct

    def get(self, lct_id: str) -> Optional[LCT]:
        """Retrieve an LCT by ID."""
        return self.lcts.get(lct_id)

    def get_by_type(self, lct_type: str) -> List[LCT]:
        """Get all LCTs of a given type."""
        return [lct for lct in self.lcts.values() if lct.lct_type == lct_type]

    def get_by_society(self, society_lct: str) -> List[LCT]:
        """Get all LCTs owned by a specific society."""
        return [
            lct for lct in self.lcts.values()
            if lct.owning_society_lct == society_lct
        ]

    def deactivate(self, lct_id: str, tick: int) -> bool:
        """Deactivate an LCT."""
        lct = self.get(lct_id)
        if lct:
            lct.deactivate(tick)
            return True
        return False

    def get_active(self) -> List[LCT]:
        """Get all active LCTs."""
        return [lct for lct in self.lcts.values() if lct.is_active]


# Example usage and tests
if __name__ == "__main__":
    print("LCT v0 Implementation - Examples")
    print("=" * 80)

    # Create registry
    registry = LCTRegistry()

    # Create a society LCT
    society = create_society_lct(
        society_id="test-society",
        block_number=0,
        tick=0,
        initial_treasury={"ATP": 1000.0}
    )
    registry.register(society)
    print(f"\n✅ Society LCT: {society.lct_id}")
    print(f"   Type: {society.lct_type}")
    print(f"   Trust: {society.trust_axes['T3']['composite']:.2f}")
    print(f"   MRH: {society.mrh_profile}")

    # Create an agent LCT
    agent = create_agent_lct(
        agent_id="alice",
        owning_society_lct=society.lct_id,
        block_number=1,
        tick=5,
        capabilities={"witness_general": 0.8},
        resources={"ATP": 100.0},
        memberships=[society.lct_id]
    )
    registry.register(agent)
    print(f"\n✅ Agent LCT: {agent.lct_id}")
    print(f"   Type: {agent.lct_type}")
    print(f"   Owned by: {agent.owning_society_lct}")
    print(f"   Created at block: {agent.created_at_block}")

    # Create a role LCT
    role = create_role_lct(
        role_name="auditor",
        society_lct=society.lct_id,
        block_number=2,
        tick=10,
        permissions=["view_treasury", "create_audit"]
    )
    registry.register(role)
    print(f"\n✅ Role LCT: {role.lct_id}")
    print(f"   Type: {role.lct_type}")
    print(f"   Permissions: {role.metadata['permissions']}")

    # Update trust
    agent.update_trust({
        "talent": 0.9,
        "training": 0.8,
        "temperament": 0.95
    })
    print(f"\n✅ Updated agent trust (T3): {agent.trust_axes['T3']['composite']:.2f}")

    # Update value
    agent.update_value({
        "valuation": 0.85,  # High perceived value
        "veracity": 0.92,   # Very accurate
        "validity": 0.98    # Nearly always delivers
    })
    print(f"✅ Updated agent value (V3): {agent.value_axes['V3']['composite']:.2f}")
    print(f"   Valuation: {agent.value_axes['V3']['valuation']:.2f}")
    print(f"   Veracity: {agent.value_axes['V3']['veracity']:.2f}")
    print(f"   Validity: {agent.value_axes['V3']['validity']:.2f}")

    # Query registry
    print(f"\n✅ Registry stats:")
    print(f"   Total LCTs: {len(registry.lcts)}")
    print(f"   Active LCTs: {len(registry.get_active())}")
    print(f"   Agents: {len(registry.get_by_type('agent'))}")
    print(f"   Societies: {len(registry.get_by_type('society'))}")
    print(f"   Roles: {len(registry.get_by_type('role'))}")

    # Deactivate role
    registry.deactivate(role.lct_id, tick=20)
    print(f"\n✅ Deactivated role at tick {role.deactivated_at_tick}")
    print(f"   Active LCTs remaining: {len(registry.get_active())}")

    # Serialize
    print(f"\n✅ Serialization example:")
    agent_dict = agent.to_dict()
    print(f"   Keys: {list(agent_dict.keys())}")
    agent_restored = LCT.from_dict(agent_dict)
    print(f"   Restored: {agent_restored.lct_id} (trust: {agent_restored.trust_axes['T3']['composite']:.2f})")
