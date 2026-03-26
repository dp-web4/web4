"""
Web4 Entity Type Taxonomy

Canonical implementation per web4-standard/core-spec/entity-types.md.

Every entity in Web4 has a type that determines its behavioral mode
(Agentic/Responsive/Delegative), energy metabolism pattern (Active/Passive),
and valid interaction patterns. This module provides the classification
registry and query functions for the 15 canonical entity types.

The EntityType enum itself lives in web4.lct (where it's used for LCT
creation). This module adds the behavioral and metabolic metadata that
the spec defines in sections 2.1-2.3.

Validated against: web4-standard/test-vectors/entity/
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional

from .lct import EntityType

__all__ = [
    # Classes
    "BehavioralMode", "EnergyPattern", "InteractionType", "EntityTypeInfo",
    # Functions
    "behavioral_modes", "energy_pattern",
    "is_agentic", "can_initiate", "can_delegate", "can_process_r6",
    "valid_interaction", "all_entity_types", "get_info",
    "entity_registry_to_jsonld", "entity_registry_from_jsonld",
    "entity_registry_from_jsonld_string",
    # Constants
    "ENTITY_JSONLD_CONTEXT",
]


# ── JSON-LD Context ──────────────────────────────────────────────

ENTITY_JSONLD_CONTEXT = "https://web4.io/contexts/entity.jsonld"


# ── Behavioral Modes (spec §2.2) ────────────────────────────────

class BehavioralMode(str, Enum):
    """How an entity interacts with the world."""
    AGENTIC = "agentic"         # Takes initiative, self-directed
    RESPONSIVE = "responsive"   # Reacts to external stimuli
    DELEGATIVE = "delegative"   # Authorizes others to act on its behalf


# ── Energy Metabolism (spec §2.3) ────────────────────────────────

class EnergyPattern(str, Enum):
    """How an entity participates in ATP/ADP energy metabolism."""
    ACTIVE = "active"   # Can expend ATP to produce results via R6
    PASSIVE = "passive"  # Infrastructure; ADP slashed, no reputation


# ── Interaction Types (spec §5.1) ────────────────────────────────

class InteractionType(str, Enum):
    """Valid interaction patterns between entities."""
    BINDING = "binding"         # Parent → Child (permanent attachment)
    PAIRING = "pairing"         # Peer ↔ Peer (authorized relationship)
    WITNESSING = "witnessing"   # Any → Any (trust through observation)
    DELEGATION = "delegation"   # Delegative → Agentic (authority transfer)


# ── Entity Type Info ─────────────────────────────────────────────

@dataclass(frozen=True)
class EntityTypeInfo:
    """
    Behavioral and metabolic metadata for an entity type.

    Attributes:
        entity_type: The canonical EntityType this info describes.
        modes: Set of behavioral modes this type can exhibit.
            Most types have one mode; some (Device, Oracle, Dictionary)
            can operate in multiple modes depending on configuration.
        energy: Energy metabolism pattern (Active or Passive).
        can_r6: Whether this type can process R6 transactions.
        description: Human-readable description from spec §2.1.
    """
    entity_type: EntityType
    modes: FrozenSet[BehavioralMode]
    energy: EnergyPattern
    can_r6: bool
    description: str

    def to_jsonld(self) -> Dict[str, Any]:
        """Serialize to JSON-LD per entity-types spec."""
        return {
            "@context": [ENTITY_JSONLD_CONTEXT],
            "@type": "EntityTypeInfo",
            "entity_type": self.entity_type.value,
            "modes": sorted(m.value for m in self.modes),
            "energy": self.energy.value,
            "can_r6": self.can_r6,
            "description": self.description,
        }

    def to_jsonld_string(self, indent: int = 2) -> str:
        """Serialize to JSON-LD string."""
        return json.dumps(self.to_jsonld(), indent=indent)

    @classmethod
    def from_jsonld(cls, doc: Dict[str, Any]) -> EntityTypeInfo:
        """Deserialize from JSON-LD document."""
        return cls(
            entity_type=EntityType(doc["entity_type"]),
            modes=frozenset(BehavioralMode(m) for m in doc["modes"]),
            energy=EnergyPattern(doc["energy"]),
            can_r6=doc["can_r6"],
            description=doc["description"],
        )

    @classmethod
    def from_jsonld_string(cls, s: str) -> EntityTypeInfo:
        """Deserialize from JSON-LD string."""
        return cls.from_jsonld(json.loads(s))


# ── Registry ─────────────────────────────────────────────────────
# Maps every EntityType to its spec-defined metadata.
# Source: entity-types.md §2.1 table.

_REGISTRY: dict[EntityType, EntityTypeInfo] = {
    EntityType.HUMAN: EntityTypeInfo(
        entity_type=EntityType.HUMAN,
        modes=frozenset({BehavioralMode.AGENTIC}),
        energy=EnergyPattern.ACTIVE,
        can_r6=True,
        description="Individual persons participating in Web4",
    ),
    EntityType.AI: EntityTypeInfo(
        entity_type=EntityType.AI,
        modes=frozenset({BehavioralMode.AGENTIC}),
        energy=EnergyPattern.ACTIVE,
        can_r6=True,
        description="Artificial intelligence agents with autonomous capabilities",
    ),
    EntityType.SOCIETY: EntityTypeInfo(
        entity_type=EntityType.SOCIETY,
        modes=frozenset({BehavioralMode.DELEGATIVE}),
        energy=EnergyPattern.ACTIVE,
        can_r6=True,
        description="Delegative entity with authority to issue citizenship and bind law",
    ),
    EntityType.ORGANIZATION: EntityTypeInfo(
        entity_type=EntityType.ORGANIZATION,
        modes=frozenset({BehavioralMode.DELEGATIVE}),
        energy=EnergyPattern.ACTIVE,
        can_r6=True,
        description="Collective entities representing groups",
    ),
    EntityType.ROLE: EntityTypeInfo(
        entity_type=EntityType.ROLE,
        modes=frozenset({BehavioralMode.DELEGATIVE}),
        energy=EnergyPattern.ACTIVE,
        can_r6=True,
        description="First-class entities representing functions or positions",
    ),
    EntityType.TASK: EntityTypeInfo(
        entity_type=EntityType.TASK,
        modes=frozenset({BehavioralMode.RESPONSIVE}),
        energy=EnergyPattern.ACTIVE,
        can_r6=True,
        description="Specific work units or objectives",
    ),
    EntityType.RESOURCE: EntityTypeInfo(
        entity_type=EntityType.RESOURCE,
        modes=frozenset({BehavioralMode.RESPONSIVE}),
        energy=EnergyPattern.PASSIVE,
        can_r6=False,
        description="Data, services, or assets",
    ),
    EntityType.DEVICE: EntityTypeInfo(
        entity_type=EntityType.DEVICE,
        modes=frozenset({BehavioralMode.RESPONSIVE, BehavioralMode.AGENTIC}),
        energy=EnergyPattern.ACTIVE,
        can_r6=True,
        description="Physical or virtual hardware",
    ),
    EntityType.SERVICE: EntityTypeInfo(
        entity_type=EntityType.SERVICE,
        modes=frozenset({BehavioralMode.RESPONSIVE}),
        energy=EnergyPattern.ACTIVE,
        can_r6=True,
        description="Software services and applications",
    ),
    EntityType.ORACLE: EntityTypeInfo(
        entity_type=EntityType.ORACLE,
        modes=frozenset({BehavioralMode.RESPONSIVE, BehavioralMode.DELEGATIVE}),
        energy=EnergyPattern.ACTIVE,
        can_r6=True,
        description="External data providers",
    ),
    EntityType.ACCUMULATOR: EntityTypeInfo(
        entity_type=EntityType.ACCUMULATOR,
        modes=frozenset({BehavioralMode.RESPONSIVE}),
        energy=EnergyPattern.PASSIVE,
        can_r6=False,
        description="Broadcast listeners and recorders",
    ),
    EntityType.DICTIONARY: EntityTypeInfo(
        entity_type=EntityType.DICTIONARY,
        modes=frozenset({BehavioralMode.RESPONSIVE, BehavioralMode.AGENTIC}),
        energy=EnergyPattern.ACTIVE,
        can_r6=True,
        description="Living semantic bridges managing compression-trust",
    ),
    EntityType.HYBRID: EntityTypeInfo(
        entity_type=EntityType.HYBRID,
        modes=frozenset({BehavioralMode.AGENTIC, BehavioralMode.RESPONSIVE, BehavioralMode.DELEGATIVE}),
        energy=EnergyPattern.ACTIVE,
        can_r6=True,
        description="Entities combining multiple types",
    ),
    EntityType.POLICY: EntityTypeInfo(
        entity_type=EntityType.POLICY,
        modes=frozenset({BehavioralMode.RESPONSIVE, BehavioralMode.DELEGATIVE}),
        energy=EnergyPattern.ACTIVE,
        can_r6=True,
        description="Governance rules as living entities with IRP-backed evaluation",
    ),
    EntityType.INFRASTRUCTURE: EntityTypeInfo(
        entity_type=EntityType.INFRASTRUCTURE,
        modes=frozenset(),  # Passive — no behavioral mode
        energy=EnergyPattern.PASSIVE,
        can_r6=False,
        description="Physical passive resources",
    ),
}


# ── Query Functions ──────────────────────────────────────────────

def get_info(entity_type: EntityType) -> EntityTypeInfo:
    """Look up the full metadata for an entity type.

    Raises KeyError if the type is not in the registry (should never
    happen for canonical EntityType values).
    """
    return _REGISTRY[entity_type]


def behavioral_modes(entity_type: EntityType) -> FrozenSet[BehavioralMode]:
    """Return the set of behavioral modes for an entity type."""
    return _REGISTRY[entity_type].modes


def energy_pattern(entity_type: EntityType) -> EnergyPattern:
    """Return the energy metabolism pattern for an entity type."""
    return _REGISTRY[entity_type].energy


def is_agentic(entity_type: EntityType) -> bool:
    """True if this entity type can take initiative autonomously."""
    return BehavioralMode.AGENTIC in _REGISTRY[entity_type].modes


def can_initiate(entity_type: EntityType) -> bool:
    """True if this entity type can initiate bindings and pairings.

    Per spec §2.2: Agentic entities "actively initiate bindings and
    pairings." Responsive entities "accept pairings but don't initiate."
    Delegative entities "create authorization chains through binding."
    """
    info = _REGISTRY[entity_type]
    return BehavioralMode.AGENTIC in info.modes or BehavioralMode.DELEGATIVE in info.modes


def can_delegate(entity_type: EntityType) -> bool:
    """True if this entity type can authorize others to act on its behalf."""
    return BehavioralMode.DELEGATIVE in _REGISTRY[entity_type].modes


def can_process_r6(entity_type: EntityType) -> bool:
    """True if this entity type can process R6 transactions.

    Active resources process R6 and earn reputation. Passive resources
    cannot process R6 — their ADP is slashed and they earn no reputation.
    """
    return _REGISTRY[entity_type].can_r6


def valid_interaction(
    source_type: EntityType,
    target_type: EntityType,
    interaction: InteractionType,
) -> bool:
    """Check whether an interaction between two entity types is valid.

    Rules from spec §5.1:
    - Binding: source must be able to delegate (parent → child)
    - Pairing: either side must be able to initiate
    - Witnessing: any → any (always valid for active entities)
    - Delegation: source must be delegative, target must be agentic
    """
    source_info = _REGISTRY[source_type]
    target_info = _REGISTRY[target_type]

    if interaction == InteractionType.WITNESSING:
        # Any entity can witness any other entity
        return True

    if interaction == InteractionType.BINDING:
        # Binding: parent must be delegative (creates authorization chains)
        return BehavioralMode.DELEGATIVE in source_info.modes

    if interaction == InteractionType.PAIRING:
        # Pairing: at least one side must be able to initiate
        source_can = (BehavioralMode.AGENTIC in source_info.modes
                      or BehavioralMode.DELEGATIVE in source_info.modes)
        target_can = (BehavioralMode.AGENTIC in target_info.modes
                      or BehavioralMode.DELEGATIVE in target_info.modes)
        return source_can or target_can

    if interaction == InteractionType.DELEGATION:
        # Delegation: delegative → agentic
        return (BehavioralMode.DELEGATIVE in source_info.modes
                and BehavioralMode.AGENTIC in target_info.modes)

    return False


def all_entity_types() -> list[EntityTypeInfo]:
    """Return info for all 15 canonical entity types."""
    return list(_REGISTRY.values())


def entity_registry_to_jsonld() -> Dict[str, Any]:
    """Serialize the full entity type registry to JSON-LD."""
    return {
        "@context": [ENTITY_JSONLD_CONTEXT],
        "@type": "EntityTypeRegistry",
        "entity_types": [info.to_jsonld() for info in _REGISTRY.values()],
    }


def entity_registry_from_jsonld(doc: Dict[str, Any]) -> Dict[EntityType, EntityTypeInfo]:
    """Deserialize an EntityTypeRegistry JSON-LD document.

    Args:
        doc: A JSON-LD document with @type "EntityTypeRegistry".

    Returns:
        Dict mapping EntityType to EntityTypeInfo for each entry in the registry.
    """
    return {
        EntityType(info_doc["entity_type"]): EntityTypeInfo.from_jsonld(info_doc)
        for info_doc in doc["entity_types"]
    }


def entity_registry_from_jsonld_string(s: str) -> Dict[EntityType, EntityTypeInfo]:
    """Deserialize an EntityTypeRegistry from a JSON-LD string."""
    return entity_registry_from_jsonld(json.loads(s))
