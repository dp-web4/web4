"""
Web4 Society Metabolic States

Canonical implementation per web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md.

Societies adopt metabolic states based on activity levels, resource availability,
and operational requirements — inspired by biological precedents (sleep cycles,
hibernation, torpor, molting).

Key concepts:
- MetabolicState: 8 states from Active (100% energy) to Torpor (2% energy)
- Transition validation: not all state→state transitions are valid
- Energy cost: baseline * state_multiplier * society_size
- Wake penalty: ATP cost for premature exit from dormant states (§6.2)
- Trust effects: each state modifies trust tensor update behavior (§5.1)
- Metabolic reliability: predictability score for society health (§5.2)

This module provides DATA STRUCTURES and pure-function computations.
Scheduling, timers, and sentinel witness logic are out of scope.

Validated against: web4-standard/test-vectors/metabolic/society-metabolic-states.json
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, FrozenSet, List, Optional, Set

__all__ = [
    # Classes
    "MetabolicState", "Transition", "TrustEffect",
    "MetabolicProfile", "ReliabilityFactors",
    # Functions
    "valid_transition", "reachable_states", "transition_trigger", "all_transitions",
    "energy_cost", "wake_penalty", "metabolic_reliability",
    "required_witnesses", "all_profiles",
    "is_dormant", "accepts_transactions", "accepts_new_citizens",
    # Constants
    "ENERGY_MULTIPLIERS", "TRUST_EFFECTS", "WITNESS_REQUIREMENTS",
    "DORMANT_STATES", "ACTIVE_STATES",
]


# ── Metabolic States (§2) ──────────────────────────────────────

class MetabolicState(str, Enum):
    """Eight society metabolic states per spec §2."""
    ACTIVE = "active"            # Full operational capacity (§2.1)
    REST = "rest"                # Low-activity period (§2.2)
    SLEEP = "sleep"              # Scheduled downtime (§2.3)
    HIBERNATION = "hibernation"  # Extended dormancy (§2.4)
    TORPOR = "torpor"            # Emergency conservation (§2.5)
    ESTIVATION = "estivation"    # Adverse conditions (§2.6)
    DREAMING = "dreaming"        # Memory consolidation (§2.7)
    MOLTING = "molting"          # Structural renewal (§2.8)


# ── Energy Multipliers (§4.1) ──────────────────────────────────

ENERGY_MULTIPLIERS: Dict[MetabolicState, float] = {
    MetabolicState.ACTIVE: 1.0,
    MetabolicState.REST: 0.4,
    MetabolicState.SLEEP: 0.15,
    MetabolicState.HIBERNATION: 0.05,
    MetabolicState.TORPOR: 0.02,
    MetabolicState.ESTIVATION: 0.10,
    MetabolicState.DREAMING: 0.20,
    MetabolicState.MOLTING: 0.60,
}


# ── Trust Effects (§5.1) ───────────────────────────────────────
# Each state defines how trust tensor updates behave.
# Values represent the fraction of normal update rate.
# Negative values indicate temporary penalties.

@dataclass(frozen=True)
class TrustEffect:
    """Trust tensor behavior in a given metabolic state."""
    update_rate: float     # Fraction of normal T3/V3 update rate (0.0 = frozen)
    decay_rate: float      # Fraction of normal trust decay rate
    temporary_penalty: float = 0.0  # Temporary T3 penalty (e.g., molting = -0.20)
    description: str = ""

TRUST_EFFECTS: Dict[MetabolicState, TrustEffect] = {
    MetabolicState.ACTIVE: TrustEffect(
        update_rate=1.0, decay_rate=1.0,
        description="Normal updates"),
    MetabolicState.REST: TrustEffect(
        update_rate=0.9, decay_rate=1.0,
        description="Slightly delayed"),
    MetabolicState.SLEEP: TrustEffect(
        update_rate=0.0, decay_rate=0.1,
        description="Minimal activity"),
    MetabolicState.HIBERNATION: TrustEffect(
        update_rate=0.0, decay_rate=0.0,
        description="Frozen"),
    MetabolicState.TORPOR: TrustEffect(
        update_rate=0.0, decay_rate=0.0,
        description="Frozen + alert bonus"),
    MetabolicState.ESTIVATION: TrustEffect(
        update_rate=0.0, decay_rate=0.0,
        description="Internal only"),
    MetabolicState.DREAMING: TrustEffect(
        update_rate=0.0, decay_rate=0.0,
        description="Recalibration"),
    MetabolicState.MOLTING: TrustEffect(
        update_rate=1.0, decay_rate=1.0,
        temporary_penalty=-0.20,
        description="Vulnerable period"),
}


# ── State Transition Graph (§3.1) ──────────────────────────────
# Defines which transitions are valid and their trigger descriptions.

@dataclass(frozen=True)
class Transition:
    """A valid state transition with its trigger condition."""
    from_state: MetabolicState
    to_state: MetabolicState
    trigger: str  # Human-readable trigger condition from spec §3.1

_TRANSITIONS: List[Transition] = [
    # From Active
    Transition(MetabolicState.ACTIVE, MetabolicState.REST, "1 hour no transactions"),
    Transition(MetabolicState.ACTIVE, MetabolicState.SLEEP, "scheduled time reached"),
    Transition(MetabolicState.ACTIVE, MetabolicState.TORPOR, "ATP reserves < 10%"),
    Transition(MetabolicState.ACTIVE, MetabolicState.DREAMING, "maintenance window"),
    Transition(MetabolicState.ACTIVE, MetabolicState.MOLTING, "governance change approved"),
    Transition(MetabolicState.ACTIVE, MetabolicState.ESTIVATION, "threat detected"),
    # From Rest
    Transition(MetabolicState.REST, MetabolicState.ACTIVE, "transaction received"),
    Transition(MetabolicState.REST, MetabolicState.SLEEP, "6 hours no activity"),
    # From Sleep
    Transition(MetabolicState.SLEEP, MetabolicState.ACTIVE, "wake trigger fired"),
    Transition(MetabolicState.SLEEP, MetabolicState.HIBERNATION, "30 days no activity"),
    # From Hibernation
    Transition(MetabolicState.HIBERNATION, MetabolicState.ACTIVE, "external witness or timeout"),
    # From Torpor
    Transition(MetabolicState.TORPOR, MetabolicState.ACTIVE, "energy producer recharges"),
    Transition(MetabolicState.TORPOR, MetabolicState.HIBERNATION, "grace period expired"),
    # From Estivation
    Transition(MetabolicState.ESTIVATION, MetabolicState.ACTIVE, "threat resolved"),
    Transition(MetabolicState.ESTIVATION, MetabolicState.HIBERNATION, "extended duration"),
    # From Dreaming
    Transition(MetabolicState.DREAMING, MetabolicState.ACTIVE, "consolidation complete"),
    # From Molting
    Transition(MetabolicState.MOLTING, MetabolicState.ACTIVE, "renewal complete"),
]

# Pre-built lookup: from_state → set of valid to_states
_transition_build: Dict[MetabolicState, Set[MetabolicState]] = {}
for _t in _TRANSITIONS:
    _transition_build.setdefault(_t.from_state, set()).add(_t.to_state)
_VALID_TRANSITIONS: Dict[MetabolicState, FrozenSet[MetabolicState]] = {
    k: frozenset(v) for k, v in _transition_build.items()
}
# States with no outgoing transitions get empty frozenset
for _s in MetabolicState:
    _VALID_TRANSITIONS.setdefault(_s, frozenset())


def valid_transition(from_state: MetabolicState, to_state: MetabolicState) -> bool:
    """Check whether a metabolic state transition is valid per §3.1."""
    return to_state in _VALID_TRANSITIONS.get(from_state, frozenset())


def reachable_states(from_state: MetabolicState) -> FrozenSet[MetabolicState]:
    """Return all states directly reachable from the given state."""
    return _VALID_TRANSITIONS.get(from_state, frozenset())


def transition_trigger(from_state: MetabolicState, to_state: MetabolicState) -> Optional[str]:
    """Return the trigger description for a transition, or None if invalid."""
    for t in _TRANSITIONS:
        if t.from_state == from_state and t.to_state == to_state:
            return t.trigger
    return None


def all_transitions() -> List[Transition]:
    """Return the full list of valid transitions."""
    return list(_TRANSITIONS)


# ── Energy Cost Calculation (§6.1) ─────────────────────────────

def energy_cost(
    state: MetabolicState,
    baseline_cost_per_hour: float,
    society_size: int,
    hours: float = 1.0,
) -> float:
    """
    Calculate ATP energy cost for a society in a given state.

    Formula (§6.1): Daily ATP Cost = Baseline * State_Multiplier * Society_Size
    Generalized: ATP Cost = baseline_cost_per_hour * multiplier * society_size * hours

    Args:
        state: Current metabolic state.
        baseline_cost_per_hour: Base ATP cost per hour per member.
        society_size: Number of active citizens.
        hours: Duration in hours.

    Returns:
        Total ATP cost for the period.
    """
    multiplier = ENERGY_MULTIPLIERS[state]
    return baseline_cost_per_hour * multiplier * society_size * hours


# ── Wake Penalty (§6.2) ───────────────────────────────────────

# States that incur wake penalties when exited prematurely
_WAKE_PENALTY_MULTIPLIERS: Dict[MetabolicState, float] = {
    MetabolicState.SLEEP: 10.0,
    MetabolicState.HIBERNATION: 100.0,
    MetabolicState.DREAMING: 50.0,
}


def wake_penalty(
    state: MetabolicState,
    planned_duration_hours: float,
    actual_duration_hours: float,
) -> float:
    """
    Calculate ATP penalty for premature wake from a dormant state (§6.2).

    Only SLEEP, HIBERNATION, and DREAMING incur penalties.
    Penalty = multiplier * incompleteness, where incompleteness = 1 - (actual / planned).
    If actual >= planned, no penalty.

    Args:
        state: The dormant state being exited.
        planned_duration_hours: How long the society intended to stay dormant.
        actual_duration_hours: How long it actually stayed.

    Returns:
        ATP penalty amount (0.0 if no penalty applies).
    """
    if planned_duration_hours <= 0:
        return 0.0
    if actual_duration_hours >= planned_duration_hours:
        return 0.0
    multiplier = _WAKE_PENALTY_MULTIPLIERS.get(state, 0.0)
    if multiplier == 0.0:
        return 0.0
    incompleteness = 1.0 - (actual_duration_hours / planned_duration_hours)
    return multiplier * incompleteness


# ── Metabolic Reliability Score (§5.2) ─────────────────────────

@dataclass
class ReliabilityFactors:
    """
    Inputs for metabolic reliability calculation per §5.2.

    Each factor is a boolean or rate that contributes to the score.
    """
    maintains_schedule: bool = False        # Predictable sleep cycles (+0.3)
    hibernation_recovery_rate: float = 0.0  # Rate of successful wakes from hibernation (+0.2 if >0.9)
    energy_efficiency: float = 0.0          # Energy usage efficiency metric (+0.3 if >0.8)
    molt_success_rate: float = 0.0          # Rate of successful structural renewals (+0.2 if >0.95)


def metabolic_reliability(factors: ReliabilityFactors) -> float:
    """
    Calculate metabolic reliability score per §5.2.

    Higher score = more predictable metabolic behavior = more trustworthy.

    Returns:
        Score in [0.0, 1.0].
    """
    score = 0.0
    if factors.maintains_schedule:
        score += 0.3
    if factors.hibernation_recovery_rate > 0.9:
        score += 0.2
    if factors.energy_efficiency > 0.8:
        score += 0.3
    if factors.molt_success_rate > 0.95:
        score += 0.2
    return score


# ── Witness Requirements by State (§2, §4.2) ──────────────────
# Each state specifies how many witnesses are required relative to total.
# Expressed as a fraction of total witnesses (0.0 = none needed, 1.0 = all needed).

WITNESS_REQUIREMENTS: Dict[MetabolicState, float] = {
    MetabolicState.ACTIVE: 1.0,     # All witnesses active
    MetabolicState.REST: 0.3,       # 3 of 10 (duty rotation)
    MetabolicState.SLEEP: 0.2,      # Minimal quorum (2 of 10)
    MetabolicState.HIBERNATION: 0.0,  # Single sentinel (handled externally)
    MetabolicState.TORPOR: 0.0,     # Reactive only
    MetabolicState.ESTIVATION: 0.0, # Defensive — internal only
    MetabolicState.DREAMING: 0.0,   # No new transactions
    MetabolicState.MOLTING: 1.0,    # Heightened security
}


def required_witnesses(state: MetabolicState, total_witnesses: int) -> int:
    """
    Calculate minimum active witnesses for a state.

    Uses ceiling of fraction * total, with minimum of 1 for states
    that require any witnesses (prevents zero from rounding).

    Args:
        state: Current metabolic state.
        total_witnesses: Total registered witnesses in the society.

    Returns:
        Minimum number of active witnesses required.
    """
    fraction = WITNESS_REQUIREMENTS[state]
    if fraction <= 0.0 or total_witnesses <= 0:
        return 0
    count = int(fraction * total_witnesses + 0.999)  # ceil
    return max(1, min(count, total_witnesses))


# ── Metabolic Profile (combined view) ──────────────────────────

@dataclass(frozen=True)
class MetabolicProfile:
    """
    Complete metabolic profile for a state — energy, trust, witnesses.

    Provides a single view of all metabolic parameters for a given state.
    """
    state: MetabolicState
    energy_multiplier: float
    trust_effect: TrustEffect
    witness_fraction: float

    @staticmethod
    def for_state(state: MetabolicState) -> MetabolicProfile:
        """Build the profile for a specific state."""
        return MetabolicProfile(
            state=state,
            energy_multiplier=ENERGY_MULTIPLIERS[state],
            trust_effect=TRUST_EFFECTS[state],
            witness_fraction=WITNESS_REQUIREMENTS[state],
        )


def all_profiles() -> Dict[MetabolicState, MetabolicProfile]:
    """Return metabolic profiles for all 8 states."""
    return {s: MetabolicProfile.for_state(s) for s in MetabolicState}


# ── Dormancy Classification ────────────────────────────────────
# Convenience grouping: which states are "dormant" (reduced operations)

DORMANT_STATES: FrozenSet[MetabolicState] = frozenset({
    MetabolicState.REST,
    MetabolicState.SLEEP,
    MetabolicState.HIBERNATION,
    MetabolicState.TORPOR,
    MetabolicState.ESTIVATION,
})

ACTIVE_STATES: FrozenSet[MetabolicState] = frozenset({
    MetabolicState.ACTIVE,
    MetabolicState.DREAMING,
    MetabolicState.MOLTING,
})


def is_dormant(state: MetabolicState) -> bool:
    """Check if a state is dormant (reduced operations)."""
    return state in DORMANT_STATES


def accepts_transactions(state: MetabolicState) -> bool:
    """Check if a society in this state accepts new transactions."""
    # Active: yes. Rest: delayed but yes. Sleep: appends only (limited).
    # Hibernation: read-only. Torpor: reactive only. Estivation: internal only.
    # Dreaming: no. Molting: yes (but degraded performance).
    return state in {
        MetabolicState.ACTIVE,
        MetabolicState.REST,
        MetabolicState.MOLTING,
    }


def accepts_new_citizens(state: MetabolicState) -> bool:
    """Check if a society in this state accepts new citizenship applications."""
    # Active: yes. Rest: queued. All others: no or queued.
    return state == MetabolicState.ACTIVE
