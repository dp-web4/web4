"""
Tests for web4.entity — entity type taxonomy, behavioral modes, energy patterns.

Tests cover:
1. Registry completeness (all 15 types)
2. Behavioral mode classification
3. Energy metabolism patterns
4. R6 processing capability
5. Interaction validity rules
6. Test vector validation
"""

import json
import os

import pytest

from web4.lct import EntityType
from web4.entity import (
    BehavioralMode, EnergyPattern, InteractionType,
    EntityTypeInfo, get_info, behavioral_modes, energy_pattern,
    is_agentic, can_initiate, can_delegate, can_process_r6,
    valid_interaction, all_entity_types,
)


# ── Registry Completeness ────────────────────────────────────────

class TestRegistryCompleteness:
    """Every EntityType must have an entry in the registry."""

    def test_all_15_types_registered(self):
        infos = all_entity_types()
        assert len(infos) == 15

    def test_every_entity_type_has_info(self):
        for et in EntityType:
            info = get_info(et)
            assert info.entity_type == et

    def test_all_types_have_description(self):
        for et in EntityType:
            info = get_info(et)
            assert len(info.description) > 0

    def test_info_is_frozen(self):
        info = get_info(EntityType.HUMAN)
        with pytest.raises(AttributeError):
            info.can_r6 = False


# ── Behavioral Modes ─────────────────────────────────────────────

class TestBehavioralModes:
    """Spec §2.2: Agentic, Responsive, Delegative classification."""

    def test_human_is_agentic(self):
        assert is_agentic(EntityType.HUMAN)
        assert BehavioralMode.AGENTIC in behavioral_modes(EntityType.HUMAN)

    def test_ai_is_agentic(self):
        assert is_agentic(EntityType.AI)

    def test_society_is_delegative(self):
        assert can_delegate(EntityType.SOCIETY)
        assert not is_agentic(EntityType.SOCIETY)

    def test_organization_is_delegative(self):
        assert can_delegate(EntityType.ORGANIZATION)

    def test_role_is_delegative(self):
        assert can_delegate(EntityType.ROLE)

    def test_task_is_responsive(self):
        modes = behavioral_modes(EntityType.TASK)
        assert BehavioralMode.RESPONSIVE in modes
        assert not is_agentic(EntityType.TASK)

    def test_resource_is_responsive(self):
        modes = behavioral_modes(EntityType.RESOURCE)
        assert BehavioralMode.RESPONSIVE in modes

    def test_device_is_dual_mode(self):
        """Devices can be responsive or agentic depending on configuration."""
        modes = behavioral_modes(EntityType.DEVICE)
        assert BehavioralMode.RESPONSIVE in modes
        assert BehavioralMode.AGENTIC in modes

    def test_oracle_is_dual_mode(self):
        """Oracles can be responsive or delegative."""
        modes = behavioral_modes(EntityType.ORACLE)
        assert BehavioralMode.RESPONSIVE in modes
        assert BehavioralMode.DELEGATIVE in modes

    def test_dictionary_is_dual_mode(self):
        """Dictionaries can be responsive or agentic."""
        modes = behavioral_modes(EntityType.DICTIONARY)
        assert BehavioralMode.RESPONSIVE in modes
        assert BehavioralMode.AGENTIC in modes

    def test_hybrid_has_all_modes(self):
        modes = behavioral_modes(EntityType.HYBRID)
        assert len(modes) == 3

    def test_infrastructure_has_no_modes(self):
        """Infrastructure is purely passive — no behavioral mode."""
        modes = behavioral_modes(EntityType.INFRASTRUCTURE)
        assert len(modes) == 0


# ── Energy Patterns ──────────────────────────────────────────────

class TestEnergyPatterns:
    """Spec §2.3: Active vs Passive energy metabolism."""

    @pytest.mark.parametrize("et", [
        EntityType.HUMAN, EntityType.AI, EntityType.SOCIETY,
        EntityType.ORGANIZATION, EntityType.ROLE, EntityType.TASK,
        EntityType.DEVICE, EntityType.SERVICE, EntityType.ORACLE,
        EntityType.DICTIONARY, EntityType.HYBRID, EntityType.POLICY,
    ])
    def test_active_entities(self, et):
        assert energy_pattern(et) == EnergyPattern.ACTIVE

    @pytest.mark.parametrize("et", [
        EntityType.RESOURCE, EntityType.ACCUMULATOR,
        EntityType.INFRASTRUCTURE,
    ])
    def test_passive_entities(self, et):
        assert energy_pattern(et) == EnergyPattern.PASSIVE


# ── R6 Processing ────────────────────────────────────────────────

class TestR6Processing:
    """Spec §2.3: Active resources can process R6; passive cannot."""

    def test_active_entities_can_process_r6(self):
        active = [et for et in EntityType if energy_pattern(et) == EnergyPattern.ACTIVE]
        for et in active:
            assert can_process_r6(et), f"{et.value} is active but cannot process R6"

    def test_passive_entities_cannot_process_r6(self):
        passive = [et for et in EntityType if energy_pattern(et) == EnergyPattern.PASSIVE]
        for et in passive:
            assert not can_process_r6(et), f"{et.value} is passive but can process R6"


# ── Initiation ───────────────────────────────────────────────────

class TestInitiation:
    """Spec §2.2: Who can initiate vs only accept interactions."""

    def test_agentic_can_initiate(self):
        assert can_initiate(EntityType.HUMAN)
        assert can_initiate(EntityType.AI)

    def test_delegative_can_initiate(self):
        assert can_initiate(EntityType.SOCIETY)
        assert can_initiate(EntityType.ORGANIZATION)

    def test_pure_responsive_cannot_initiate(self):
        assert not can_initiate(EntityType.TASK)
        assert not can_initiate(EntityType.SERVICE)
        assert not can_initiate(EntityType.ACCUMULATOR)

    def test_infrastructure_cannot_initiate(self):
        assert not can_initiate(EntityType.INFRASTRUCTURE)


# ── Interaction Validity ─────────────────────────────────────────

class TestInteractionValidity:
    """Spec §5.1: Valid interaction patterns between entity types."""

    def test_witnessing_always_valid(self):
        """Any entity can witness any other."""
        for s in EntityType:
            for t in EntityType:
                assert valid_interaction(s, t, InteractionType.WITNESSING)

    def test_binding_requires_delegative_source(self):
        # Organization can bind a Role
        assert valid_interaction(
            EntityType.ORGANIZATION, EntityType.ROLE, InteractionType.BINDING
        )
        # Human (agentic, not delegative) cannot bind
        assert not valid_interaction(
            EntityType.HUMAN, EntityType.ROLE, InteractionType.BINDING
        )

    def test_delegation_requires_delegative_to_agentic(self):
        # Role (delegative) → Human (agentic) = valid
        assert valid_interaction(
            EntityType.ROLE, EntityType.HUMAN, InteractionType.DELEGATION
        )
        # Role (delegative) → Task (responsive) = invalid
        assert not valid_interaction(
            EntityType.ROLE, EntityType.TASK, InteractionType.DELEGATION
        )
        # Human (agentic) → AI (agentic) = invalid (source not delegative)
        assert not valid_interaction(
            EntityType.HUMAN, EntityType.AI, InteractionType.DELEGATION
        )

    def test_pairing_needs_at_least_one_initiator(self):
        # Human ↔ AI = valid (both agentic)
        assert valid_interaction(
            EntityType.HUMAN, EntityType.AI, InteractionType.PAIRING
        )
        # Human ↔ Service = valid (human can initiate)
        assert valid_interaction(
            EntityType.HUMAN, EntityType.SERVICE, InteractionType.PAIRING
        )
        # Infrastructure ↔ Accumulator = invalid (neither can initiate)
        assert not valid_interaction(
            EntityType.INFRASTRUCTURE, EntityType.ACCUMULATOR, InteractionType.PAIRING
        )

    def test_society_can_bind_and_delegate(self):
        """Society is delegative: can bind roles and delegate to agents."""
        assert valid_interaction(
            EntityType.SOCIETY, EntityType.ROLE, InteractionType.BINDING
        )
        assert valid_interaction(
            EntityType.SOCIETY, EntityType.AI, InteractionType.DELEGATION
        )


# ── Test Vectors ─────────────────────────────────────────────────

class TestVectors:
    """Cross-language test vector validation."""

    @pytest.fixture
    def vectors(self):
        vec_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..",
            "test-vectors", "entity", "entity-taxonomy.json"
        )
        with open(vec_path) as f:
            return json.load(f)

    def test_vector_count(self, vectors):
        assert len(vectors["vectors"]) >= 5

    @pytest.mark.parametrize("idx", range(5))
    def test_vector(self, vectors, idx):
        vec = vectors["vectors"][idx]
        et = EntityType(vec["entity_type"])
        info = get_info(et)

        # Check modes
        expected_modes = set(vec["expected"]["modes"])
        actual_modes = {m.value for m in info.modes}
        assert actual_modes == expected_modes, f"{et.value}: modes mismatch"

        # Check energy
        assert info.energy.value == vec["expected"]["energy"]

        # Check R6 capability
        assert info.can_r6 == vec["expected"]["can_r6"]

        # Check interaction results if present
        if "interactions" in vec:
            for interaction in vec["interactions"]:
                target = EntityType(interaction["target"])
                itype = InteractionType(interaction["type"])
                expected = interaction["valid"]
                actual = valid_interaction(et, target, itype)
                assert actual == expected, (
                    f"{et.value} → {target.value} via {itype.value}: "
                    f"expected {expected}, got {actual}"
                )
