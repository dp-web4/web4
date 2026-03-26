"""
Tests for Entity Type Taxonomy JSON-LD serialization (A3).

Validates that EntityTypeInfo.to_jsonld() produces spec-compliant documents
and that from_jsonld() round-trips cleanly.
"""

import json
import pytest

from web4.entity import (
    BehavioralMode,
    EnergyPattern,
    EntityTypeInfo,
    ENTITY_JSONLD_CONTEXT,
    all_entity_types,
    get_info,
    entity_registry_to_jsonld,
    entity_registry_from_jsonld,
    entity_registry_from_jsonld_string,
)
from web4.lct import EntityType


# ── EntityTypeInfo JSON-LD ────────────────────────────────────────


class TestEntityTypeInfoJsonLd:
    """EntityTypeInfo.to_jsonld() / from_jsonld() tests."""

    def test_context_and_type(self):
        """JSON-LD document has correct @context and @type."""
        info = get_info(EntityType.HUMAN)
        doc = info.to_jsonld()
        assert doc["@context"] == [ENTITY_JSONLD_CONTEXT]
        assert doc["@type"] == "EntityTypeInfo"

    def test_human_entity(self):
        """Human entity serializes with agentic mode and active energy."""
        info = get_info(EntityType.HUMAN)
        doc = info.to_jsonld()
        assert doc["entity_type"] == "human"
        assert doc["modes"] == ["agentic"]
        assert doc["energy"] == "active"
        assert doc["can_r6"] is True
        assert "Individual persons" in doc["description"]

    def test_infrastructure_entity(self):
        """Infrastructure entity serializes with empty modes and passive energy."""
        info = get_info(EntityType.INFRASTRUCTURE)
        doc = info.to_jsonld()
        assert doc["entity_type"] == "infrastructure"
        assert doc["modes"] == []
        assert doc["energy"] == "passive"
        assert doc["can_r6"] is False

    def test_multi_mode_entity(self):
        """Device entity serializes multiple modes (sorted)."""
        info = get_info(EntityType.DEVICE)
        doc = info.to_jsonld()
        assert doc["entity_type"] == "device"
        assert doc["modes"] == ["agentic", "responsive"]
        assert doc["energy"] == "active"

    def test_hybrid_all_modes(self):
        """Hybrid entity has all three behavioral modes."""
        info = get_info(EntityType.HYBRID)
        doc = info.to_jsonld()
        assert doc["modes"] == ["agentic", "delegative", "responsive"]

    def test_passive_entities(self):
        """Passive entities (Resource, Accumulator, Infrastructure) serialize correctly."""
        for et in [EntityType.RESOURCE, EntityType.ACCUMULATOR, EntityType.INFRASTRUCTURE]:
            info = get_info(et)
            doc = info.to_jsonld()
            assert doc["energy"] == "passive"
            assert doc["can_r6"] is False

    def test_delegative_entities(self):
        """Delegative entities serialize with delegative mode."""
        for et in [EntityType.SOCIETY, EntityType.ORGANIZATION, EntityType.ROLE]:
            info = get_info(et)
            doc = info.to_jsonld()
            assert "delegative" in doc["modes"]

    def test_roundtrip(self):
        """to_jsonld() -> from_jsonld() preserves all fields."""
        info = get_info(EntityType.DEVICE)
        doc = info.to_jsonld()
        restored = EntityTypeInfo.from_jsonld(doc)
        assert restored.entity_type == info.entity_type
        assert restored.modes == info.modes
        assert restored.energy == info.energy
        assert restored.can_r6 == info.can_r6
        assert restored.description == info.description

    def test_roundtrip_all_types(self):
        """Round-trip works for all 15 entity types."""
        for info in all_entity_types():
            doc = info.to_jsonld()
            restored = EntityTypeInfo.from_jsonld(doc)
            assert restored == info

    def test_string_roundtrip(self):
        """to_jsonld_string() -> from_jsonld_string() round-trips."""
        info = get_info(EntityType.AI)
        s = info.to_jsonld_string()
        restored = EntityTypeInfo.from_jsonld_string(s)
        assert restored == info

    def test_json_valid(self):
        """to_jsonld_string() produces valid JSON."""
        info = get_info(EntityType.ORACLE)
        s = info.to_jsonld_string()
        parsed = json.loads(s)
        assert parsed["@type"] == "EntityTypeInfo"

    def test_from_jsonld_ignores_extra_fields(self):
        """from_jsonld() works with extra JSON-LD metadata."""
        doc = {
            "@context": [ENTITY_JSONLD_CONTEXT],
            "@type": "EntityTypeInfo",
            "entity_type": "human",
            "modes": ["agentic"],
            "energy": "active",
            "can_r6": True,
            "description": "Test entity",
        }
        info = EntityTypeInfo.from_jsonld(doc)
        assert info.entity_type == EntityType.HUMAN

    def test_modes_sorted_deterministic(self):
        """Modes are always sorted alphabetically for deterministic output."""
        info = get_info(EntityType.ORACLE)  # responsive + delegative
        doc1 = info.to_jsonld()
        doc2 = info.to_jsonld()
        assert doc1["modes"] == doc2["modes"]
        assert doc1["modes"] == sorted(doc1["modes"])


# ── EntityTypeRegistry JSON-LD ────────────────────────────────────


class TestEntityRegistryJsonLd:
    """entity_registry_to_jsonld() tests."""

    def test_context_and_type(self):
        """Registry document has correct @context and @type."""
        doc = entity_registry_to_jsonld()
        assert doc["@context"] == [ENTITY_JSONLD_CONTEXT]
        assert doc["@type"] == "EntityTypeRegistry"

    def test_contains_all_15_types(self):
        """Registry contains all 15 canonical entity types."""
        doc = entity_registry_to_jsonld()
        assert len(doc["entity_types"]) == 15

    def test_each_entry_has_required_fields(self):
        """Each registry entry has all required JSON-LD fields."""
        doc = entity_registry_to_jsonld()
        for entry in doc["entity_types"]:
            assert "@context" in entry
            assert "@type" in entry
            assert "entity_type" in entry
            assert "modes" in entry
            assert "energy" in entry
            assert "can_r6" in entry
            assert "description" in entry

    def test_entity_types_unique(self):
        """All entity types in registry are unique."""
        doc = entity_registry_to_jsonld()
        types = [e["entity_type"] for e in doc["entity_types"]]
        assert len(types) == len(set(types))

    def test_registry_json_serializable(self):
        """Full registry is JSON-serializable."""
        doc = entity_registry_to_jsonld()
        s = json.dumps(doc, indent=2)
        parsed = json.loads(s)
        assert len(parsed["entity_types"]) == 15

    def test_registry_roundtrip(self):
        """entity_registry_to_jsonld() -> entity_registry_from_jsonld() preserves all entries."""
        doc = entity_registry_to_jsonld()
        restored = entity_registry_from_jsonld(doc)
        assert len(restored) == 15
        for et, info in restored.items():
            original = get_info(et)
            assert info == original

    def test_registry_roundtrip_keys(self):
        """Round-tripped registry has all 15 EntityType keys."""
        doc = entity_registry_to_jsonld()
        restored = entity_registry_from_jsonld(doc)
        expected_types = {et for et in EntityType}
        assert set(restored.keys()) == expected_types

    def test_registry_string_roundtrip(self):
        """entity_registry_to_jsonld() -> JSON string -> entity_registry_from_jsonld_string()."""
        doc = entity_registry_to_jsonld()
        s = json.dumps(doc)
        restored = entity_registry_from_jsonld_string(s)
        assert len(restored) == 15
        for et, info in restored.items():
            assert info == get_info(et)

    def test_registry_roundtrip_preserves_modes(self):
        """Round-trip preserves multi-mode entities (frozenset equality)."""
        doc = entity_registry_to_jsonld()
        restored = entity_registry_from_jsonld(doc)
        # Device has {agentic, responsive}
        assert restored[EntityType.DEVICE].modes == frozenset({
            BehavioralMode.AGENTIC, BehavioralMode.RESPONSIVE
        })
        # Infrastructure has empty modes
        assert restored[EntityType.INFRASTRUCTURE].modes == frozenset()

    def test_registry_roundtrip_preserves_energy(self):
        """Round-trip preserves energy patterns."""
        doc = entity_registry_to_jsonld()
        restored = entity_registry_from_jsonld(doc)
        assert restored[EntityType.RESOURCE].energy == EnergyPattern.PASSIVE
        assert restored[EntityType.HUMAN].energy == EnergyPattern.ACTIVE
