"""
Tests for web4.metabolic — society metabolic states.

Tests cover:
1. MetabolicState enum completeness
2. Energy multiplier validation
3. State transition graph (valid + invalid)
4. Energy cost calculation
5. Wake penalty calculation
6. Metabolic reliability score
7. Witness requirements
8. Metabolic profiles
9. Dormancy classification
10. Test vector validation
"""

import json
import math
import os

import pytest

from web4.metabolic import (
    MetabolicState,
    ENERGY_MULTIPLIERS, TRUST_EFFECTS, WITNESS_REQUIREMENTS,
    DORMANT_STATES, ACTIVE_STATES,
    TrustEffect, Transition, ReliabilityFactors, MetabolicProfile,
    valid_transition, reachable_states, transition_trigger, all_transitions,
    energy_cost, wake_penalty, metabolic_reliability,
    required_witnesses, all_profiles,
    is_dormant, accepts_transactions, accepts_new_citizens,
)


# ── MetabolicState Enum ────────────────────────────────────────

class TestMetabolicStateEnum:
    """All 8 states exist and have correct string values."""

    def test_8_states(self):
        assert len(MetabolicState) == 8

    def test_state_values(self):
        expected = {
            "active", "rest", "sleep", "hibernation",
            "torpor", "estivation", "dreaming", "molting",
        }
        assert {s.value for s in MetabolicState} == expected

    def test_string_roundtrip(self):
        for s in MetabolicState:
            assert MetabolicState(s.value) == s


# ── Energy Multipliers ─────────────────────────────────────────

class TestEnergyMultipliers:
    """Every state has an energy multiplier per spec §4.1."""

    def test_all_states_have_multiplier(self):
        for s in MetabolicState:
            assert s in ENERGY_MULTIPLIERS

    def test_active_is_baseline(self):
        assert ENERGY_MULTIPLIERS[MetabolicState.ACTIVE] == 1.0

    def test_torpor_is_lowest(self):
        assert ENERGY_MULTIPLIERS[MetabolicState.TORPOR] == 0.02
        for s in MetabolicState:
            assert ENERGY_MULTIPLIERS[s] >= 0.02

    def test_ordering(self):
        """Torpor < Hibernation < Estivation < Sleep < Dreaming < Rest < Molting < Active."""
        m = ENERGY_MULTIPLIERS
        assert m[MetabolicState.TORPOR] < m[MetabolicState.HIBERNATION]
        assert m[MetabolicState.HIBERNATION] < m[MetabolicState.ESTIVATION]
        assert m[MetabolicState.ESTIVATION] < m[MetabolicState.SLEEP]
        assert m[MetabolicState.SLEEP] < m[MetabolicState.DREAMING]
        assert m[MetabolicState.DREAMING] < m[MetabolicState.REST]
        assert m[MetabolicState.REST] < m[MetabolicState.MOLTING]
        assert m[MetabolicState.MOLTING] < m[MetabolicState.ACTIVE]

    def test_all_positive(self):
        for s, mult in ENERGY_MULTIPLIERS.items():
            assert mult > 0, f"{s} has non-positive multiplier"

    def test_all_at_most_1(self):
        for s, mult in ENERGY_MULTIPLIERS.items():
            assert mult <= 1.0, f"{s} exceeds baseline"


# ── Trust Effects ──────────────────────────────────────────────

class TestTrustEffects:
    """Trust behavior per state per spec §5.1."""

    def test_all_states_have_effect(self):
        for s in MetabolicState:
            assert s in TRUST_EFFECTS

    def test_active_full_updates(self):
        te = TRUST_EFFECTS[MetabolicState.ACTIVE]
        assert te.update_rate == 1.0
        assert te.decay_rate == 1.0
        assert te.temporary_penalty == 0.0

    def test_hibernation_frozen(self):
        te = TRUST_EFFECTS[MetabolicState.HIBERNATION]
        assert te.update_rate == 0.0
        assert te.decay_rate == 0.0

    def test_molting_penalty(self):
        te = TRUST_EFFECTS[MetabolicState.MOLTING]
        assert te.temporary_penalty == pytest.approx(-0.20)

    def test_sleep_decay_reduced(self):
        te = TRUST_EFFECTS[MetabolicState.SLEEP]
        assert te.update_rate == 0.0
        assert te.decay_rate == pytest.approx(0.1)

    def test_effects_are_frozen(self):
        te = TRUST_EFFECTS[MetabolicState.ACTIVE]
        with pytest.raises(AttributeError):
            te.update_rate = 0.5


# ── State Transitions ──────────────────────────────────────────

class TestStateTransitions:
    """Transition validation per spec §3.1."""

    def test_active_can_reach_6_states(self):
        r = reachable_states(MetabolicState.ACTIVE)
        assert len(r) == 6
        assert MetabolicState.REST in r
        assert MetabolicState.SLEEP in r
        assert MetabolicState.TORPOR in r
        assert MetabolicState.DREAMING in r
        assert MetabolicState.MOLTING in r
        assert MetabolicState.ESTIVATION in r

    def test_active_cannot_hibernate_directly(self):
        assert not valid_transition(MetabolicState.ACTIVE, MetabolicState.HIBERNATION)

    def test_rest_to_active(self):
        assert valid_transition(MetabolicState.REST, MetabolicState.ACTIVE)

    def test_rest_to_sleep(self):
        assert valid_transition(MetabolicState.REST, MetabolicState.SLEEP)

    def test_sleep_to_hibernation(self):
        assert valid_transition(MetabolicState.SLEEP, MetabolicState.HIBERNATION)

    def test_hibernation_only_to_active(self):
        r = reachable_states(MetabolicState.HIBERNATION)
        assert r == frozenset({MetabolicState.ACTIVE})

    def test_torpor_to_active_or_hibernation(self):
        r = reachable_states(MetabolicState.TORPOR)
        assert r == frozenset({MetabolicState.ACTIVE, MetabolicState.HIBERNATION})

    def test_dreaming_only_to_active(self):
        r = reachable_states(MetabolicState.DREAMING)
        assert r == frozenset({MetabolicState.ACTIVE})

    def test_molting_only_to_active(self):
        r = reachable_states(MetabolicState.MOLTING)
        assert r == frozenset({MetabolicState.ACTIVE})

    def test_estivation_to_active_or_hibernation(self):
        r = reachable_states(MetabolicState.ESTIVATION)
        assert r == frozenset({MetabolicState.ACTIVE, MetabolicState.HIBERNATION})

    def test_self_transition_invalid(self):
        for s in MetabolicState:
            assert not valid_transition(s, s)

    def test_total_transition_count(self):
        transitions = all_transitions()
        assert len(transitions) == 17

    def test_trigger_descriptions_exist(self):
        for t in all_transitions():
            assert len(t.trigger) > 0

    def test_trigger_lookup(self):
        trigger = transition_trigger(MetabolicState.ACTIVE, MetabolicState.TORPOR)
        assert trigger == "ATP reserves < 10%"

    def test_invalid_trigger_returns_none(self):
        trigger = transition_trigger(MetabolicState.HIBERNATION, MetabolicState.SLEEP)
        assert trigger is None


# ── Energy Cost ────────────────────────────────────────────────

class TestEnergyCost:
    """Energy cost calculation per spec §6.1."""

    def test_active_baseline(self):
        cost = energy_cost(MetabolicState.ACTIVE, baseline_cost_per_hour=100.0, society_size=10)
        assert cost == pytest.approx(1000.0)

    def test_rest_40_percent(self):
        cost = energy_cost(MetabolicState.REST, baseline_cost_per_hour=100.0, society_size=10)
        assert cost == pytest.approx(400.0)

    def test_torpor_minimal(self):
        cost = energy_cost(MetabolicState.TORPOR, baseline_cost_per_hour=100.0, society_size=10)
        assert cost == pytest.approx(20.0)

    def test_duration_scaling(self):
        cost = energy_cost(MetabolicState.ACTIVE, baseline_cost_per_hour=100.0, society_size=1, hours=24.0)
        assert cost == pytest.approx(2400.0)

    def test_zero_society_zero_cost(self):
        cost = energy_cost(MetabolicState.ACTIVE, baseline_cost_per_hour=100.0, society_size=0)
        assert cost == pytest.approx(0.0)


# ── Wake Penalty ───────────────────────────────────────────────

class TestWakePenalty:
    """Wake penalty calculation per spec §6.2."""

    def test_full_duration_no_penalty(self):
        penalty = wake_penalty(MetabolicState.SLEEP, planned_duration_hours=8.0, actual_duration_hours=8.0)
        assert penalty == pytest.approx(0.0)

    def test_exceeded_duration_no_penalty(self):
        penalty = wake_penalty(MetabolicState.SLEEP, planned_duration_hours=8.0, actual_duration_hours=10.0)
        assert penalty == pytest.approx(0.0)

    def test_sleep_half_penalty(self):
        # Sleep multiplier = 10.0, incompleteness = 0.5
        penalty = wake_penalty(MetabolicState.SLEEP, planned_duration_hours=8.0, actual_duration_hours=4.0)
        assert penalty == pytest.approx(5.0)

    def test_hibernation_early_wake(self):
        # Hibernation multiplier = 100.0, incompleteness = 0.75
        penalty = wake_penalty(MetabolicState.HIBERNATION, planned_duration_hours=100.0, actual_duration_hours=25.0)
        assert penalty == pytest.approx(75.0)

    def test_dreaming_interrupted(self):
        # Dreaming multiplier = 50.0, incompleteness = 1.0 (zero actual)
        penalty = wake_penalty(MetabolicState.DREAMING, planned_duration_hours=2.0, actual_duration_hours=0.0)
        assert penalty == pytest.approx(50.0)

    def test_active_no_penalty(self):
        penalty = wake_penalty(MetabolicState.ACTIVE, planned_duration_hours=8.0, actual_duration_hours=2.0)
        assert penalty == pytest.approx(0.0)

    def test_rest_no_penalty(self):
        penalty = wake_penalty(MetabolicState.REST, planned_duration_hours=8.0, actual_duration_hours=2.0)
        assert penalty == pytest.approx(0.0)

    def test_zero_planned_no_penalty(self):
        penalty = wake_penalty(MetabolicState.SLEEP, planned_duration_hours=0.0, actual_duration_hours=0.0)
        assert penalty == pytest.approx(0.0)


# ── Metabolic Reliability ──────────────────────────────────────

class TestMetabolicReliability:
    """Metabolic reliability score per spec §5.2."""

    def test_all_factors_perfect(self):
        factors = ReliabilityFactors(
            maintains_schedule=True,
            hibernation_recovery_rate=0.95,
            energy_efficiency=0.85,
            molt_success_rate=0.96,
        )
        assert metabolic_reliability(factors) == pytest.approx(1.0)

    def test_no_factors(self):
        factors = ReliabilityFactors()
        assert metabolic_reliability(factors) == pytest.approx(0.0)

    def test_schedule_only(self):
        factors = ReliabilityFactors(maintains_schedule=True)
        assert metabolic_reliability(factors) == pytest.approx(0.3)

    def test_boundary_hibernation(self):
        # Exactly 0.9 is NOT > 0.9
        factors = ReliabilityFactors(hibernation_recovery_rate=0.9)
        assert metabolic_reliability(factors) == pytest.approx(0.0)
        # Just above
        factors = ReliabilityFactors(hibernation_recovery_rate=0.91)
        assert metabolic_reliability(factors) == pytest.approx(0.2)

    def test_boundary_efficiency(self):
        factors = ReliabilityFactors(energy_efficiency=0.8)
        assert metabolic_reliability(factors) == pytest.approx(0.0)
        factors = ReliabilityFactors(energy_efficiency=0.81)
        assert metabolic_reliability(factors) == pytest.approx(0.3)

    def test_boundary_molt(self):
        factors = ReliabilityFactors(molt_success_rate=0.95)
        assert metabolic_reliability(factors) == pytest.approx(0.0)
        factors = ReliabilityFactors(molt_success_rate=0.96)
        assert metabolic_reliability(factors) == pytest.approx(0.2)

    def test_score_bounded(self):
        # Max possible is 1.0
        factors = ReliabilityFactors(
            maintains_schedule=True,
            hibernation_recovery_rate=1.0,
            energy_efficiency=1.0,
            molt_success_rate=1.0,
        )
        assert metabolic_reliability(factors) <= 1.0


# ── Witness Requirements ───────────────────────────────────────

class TestWitnessRequirements:
    """Witness duty rotation per state per spec §4.2."""

    def test_active_all_witnesses(self):
        assert required_witnesses(MetabolicState.ACTIVE, 10) == 10

    def test_rest_3_of_10(self):
        assert required_witnesses(MetabolicState.REST, 10) == 3

    def test_sleep_2_of_10(self):
        assert required_witnesses(MetabolicState.SLEEP, 10) == 2

    def test_hibernation_zero(self):
        # Sentinel handled externally
        assert required_witnesses(MetabolicState.HIBERNATION, 10) == 0

    def test_molting_all_witnesses(self):
        assert required_witnesses(MetabolicState.MOLTING, 10) == 10

    def test_minimum_1_when_nonzero_fraction(self):
        # Even with 1 total witness, REST fraction 0.3 should give 1
        assert required_witnesses(MetabolicState.REST, 1) == 1

    def test_zero_total_zero_required(self):
        assert required_witnesses(MetabolicState.ACTIVE, 0) == 0


# ── Metabolic Profiles ─────────────────────────────────────────

class TestMetabolicProfiles:
    """MetabolicProfile combines energy, trust, and witnesses."""

    def test_all_8_profiles(self):
        profiles = all_profiles()
        assert len(profiles) == 8

    def test_profile_for_active(self):
        p = MetabolicProfile.for_state(MetabolicState.ACTIVE)
        assert p.energy_multiplier == 1.0
        assert p.trust_effect.update_rate == 1.0
        assert p.witness_fraction == 1.0

    def test_profile_is_frozen(self):
        p = MetabolicProfile.for_state(MetabolicState.REST)
        with pytest.raises(AttributeError):
            p.energy_multiplier = 0.5


# ── Dormancy Classification ───────────────────────────────────

class TestDormancy:
    """Dormant vs active state classification."""

    def test_5_dormant_states(self):
        assert len(DORMANT_STATES) == 5

    def test_3_active_states(self):
        assert len(ACTIVE_STATES) == 3

    def test_partition(self):
        """Dormant + Active = all states."""
        assert DORMANT_STATES | ACTIVE_STATES == set(MetabolicState)
        assert DORMANT_STATES & ACTIVE_STATES == set()

    def test_is_dormant(self):
        assert is_dormant(MetabolicState.SLEEP)
        assert is_dormant(MetabolicState.TORPOR)
        assert not is_dormant(MetabolicState.ACTIVE)
        assert not is_dormant(MetabolicState.MOLTING)

    def test_accepts_transactions(self):
        assert accepts_transactions(MetabolicState.ACTIVE)
        assert accepts_transactions(MetabolicState.REST)
        assert accepts_transactions(MetabolicState.MOLTING)
        assert not accepts_transactions(MetabolicState.SLEEP)
        assert not accepts_transactions(MetabolicState.HIBERNATION)
        assert not accepts_transactions(MetabolicState.DREAMING)

    def test_accepts_new_citizens(self):
        assert accepts_new_citizens(MetabolicState.ACTIVE)
        for s in MetabolicState:
            if s != MetabolicState.ACTIVE:
                assert not accepts_new_citizens(s)


# ── Test Vector Validation ─────────────────────────────────────

class TestVectors:
    """Validate against cross-language test vectors."""

    @pytest.fixture
    def vectors(self):
        path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..", "test-vectors", "metabolic", "society-metabolic-states.json",
        )
        with open(path) as f:
            return json.load(f)["vectors"]

    def test_vectors_exist(self, vectors):
        assert len(vectors) >= 5

    def test_energy_cost_vectors(self, vectors):
        for v in vectors:
            if v["id"].startswith("metabolic-energy-"):
                state = MetabolicState(v["state"])
                result = energy_cost(
                    state,
                    baseline_cost_per_hour=v["baseline"],
                    society_size=v["society_size"],
                    hours=v.get("hours", 1.0),
                )
                assert result == pytest.approx(v["expected"]["cost"], rel=1e-6), \
                    f"Vector {v['id']} failed: {result} != {v['expected']['cost']}"

    def test_wake_penalty_vectors(self, vectors):
        for v in vectors:
            if v["id"].startswith("metabolic-wake-"):
                state = MetabolicState(v["state"])
                result = wake_penalty(
                    state,
                    planned_duration_hours=v["planned_hours"],
                    actual_duration_hours=v["actual_hours"],
                )
                assert result == pytest.approx(v["expected"]["penalty"], rel=1e-6), \
                    f"Vector {v['id']} failed: {result} != {v['expected']['penalty']}"

    def test_transition_vectors(self, vectors):
        for v in vectors:
            if v["id"].startswith("metabolic-transition-"):
                from_s = MetabolicState(v["from_state"])
                to_s = MetabolicState(v["to_state"])
                result = valid_transition(from_s, to_s)
                assert result == v["expected"]["valid"], \
                    f"Vector {v['id']} failed: {result} != {v['expected']['valid']}"

    def test_reliability_vectors(self, vectors):
        for v in vectors:
            if v["id"].startswith("metabolic-reliability-"):
                f = v["factors"]
                factors = ReliabilityFactors(
                    maintains_schedule=f["maintains_schedule"],
                    hibernation_recovery_rate=f["hibernation_recovery_rate"],
                    energy_efficiency=f["energy_efficiency"],
                    molt_success_rate=f["molt_success_rate"],
                )
                result = metabolic_reliability(factors)
                assert result == pytest.approx(v["expected"]["score"], rel=1e-6), \
                    f"Vector {v['id']} failed: {result} != {v['expected']['score']}"
