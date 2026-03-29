"""
Web4 Society — Core organizational primitive.

Canonical implementation per web4-standard/core-spec/SOCIETY_SPECIFICATION.md.

A Society is a self-governing collective of LCT-bearing entities that maintains
shared laws, ledger, economy, and identity. This module composes existing SDK
components (federation.Society, metabolic states, ATP, LCT, trust tensors) into
a unified orchestration layer.

Key concepts:
- SocietyPhase: Genesis → Bootstrap → Operational lifecycle (§1.3)
- SocietyLedger: Append-only event log with amendment support (§4)
- Treasury: ATP pool with allocation tracking (§1.2.3)
- SocietyState: Composite type tying society + metabolic + treasury + ledger + trust
- Fractal hierarchies: Societies as citizens of other societies (§3)

This module provides DATA STRUCTURES and pure-function operations.
Persistence, networking, and consensus are out of scope.

Validated against: web4-standard/test-vectors/society/society-vectors.json
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from web4.federation import (
    Society,
    CitizenshipRecord,
    CitizenshipStatus,
    LedgerType,
    LawDataset,
    QuorumPolicy,
    QuorumMode,
)
from web4.metabolic import (
    MetabolicState,
    energy_cost,
    valid_transition as valid_metabolic_transition,
    is_dormant,
    accepts_transactions,
    accepts_new_citizens,
)
from web4.atp import ATPAccount
from web4.trust import T3, TrustProfile, compute_team_t3, operational_health

__all__ = [
    # Classes
    "SocietyPhase", "LedgerEventType",
    "LedgerEntry", "SocietyLedger", "Treasury", "SocietyState",
    # Functions
    "create_society",
    "admit_citizen", "suspend_citizen", "reinstate_citizen", "terminate_citizen",
    "transition_metabolic_state",
    "deposit_treasury", "allocate_treasury", "record_law_change",
    "compute_society_t3", "society_energy_cost", "society_health",
    "incorporate_child", "society_depth", "society_ancestry",
]


# ── Enums ─────────────────────────────────────────────────────────


class SocietyPhase(str, Enum):
    """Formation lifecycle phase per spec §1.3."""
    GENESIS = "genesis"          # Founding entities agree on initial laws
    BOOTSTRAP = "bootstrap"      # Initial citizens recorded, treasury allocated
    OPERATIONAL = "operational"   # Accepting citizens, economic activity


class LedgerEventType(str, Enum):
    """Types of events recorded on the society ledger per spec §4.2.1."""
    CITIZENSHIP = "citizenship"   # join/leave/suspend/reinstate
    LAW_CHANGE = "law_change"     # propose/ratify/amend/repeal
    ECONOMIC = "economic"         # allocate/deposit/reclaim
    METABOLIC = "metabolic"       # state transitions
    FORMATION = "formation"       # phase transitions, incorporation


# ── Data Structures ───────────────────────────────────────────────


@dataclass(frozen=True)
class LedgerEntry:
    """Immutable ledger entry per spec §4.2.

    Once recorded, entries cannot be modified — only superseded via amendment.
    The amends/superseded_by fields create a provenance chain (§4.2.2).
    """
    entry_id: str
    event_type: LedgerEventType
    action: str                    # e.g. "grant", "suspend", "allocate", "ratify"
    data: Dict[str, Any]            # event-specific payload
    timestamp: str
    witnesses: List[str] = field(default_factory=list)
    superseded_by: Optional[str] = None   # entry_id of amendment that replaces this
    amends: Optional[str] = None          # entry_id of entry this amends


@dataclass
class SocietyLedger:
    """Append-only society ledger per spec §4.

    Supports three ledger types (confined, witnessed, participatory) and
    immutability-with-corrections via the amend() method (§4.2.2).
    """
    ledger_type: LedgerType
    entries: List[LedgerEntry] = field(default_factory=list)

    def append(self, entry: LedgerEntry) -> None:
        """Record an event on the ledger."""
        self.entries.append(entry)

    def query(
        self,
        event_type: Optional[LedgerEventType] = None,
        action: Optional[str] = None,
    ) -> List[LedgerEntry]:
        """Query entries by type and/or action."""
        result = self.entries
        if event_type is not None:
            result = [e for e in result if e.event_type == event_type]
        if action is not None:
            result = [e for e in result if e.action == action]
        return result

    def get_entry(self, entry_id: str) -> Optional[LedgerEntry]:
        """Get a specific entry by ID."""
        for e in self.entries:
            if e.entry_id == entry_id:
                return e
        return None

    def amend(self, original_id: str, amendment: LedgerEntry) -> bool:
        """Amend an existing entry per spec §4.2.2.

        Original entry is marked superseded; amendment links to it.
        Both entries remain in the ledger (immutability with corrections).
        Returns False if original not found or already superseded.
        """
        original = self.get_entry(original_id)
        if original is None:
            return False
        if original.superseded_by is not None:
            return False  # already amended

        # Replace original with superseded version (frozen → reconstruct)
        idx = next(i for i, e in enumerate(self.entries) if e.entry_id == original_id)
        self.entries[idx] = LedgerEntry(
            entry_id=original.entry_id,
            event_type=original.event_type,
            action=original.action,
            data=original.data,
            timestamp=original.timestamp,
            witnesses=original.witnesses,
            superseded_by=amendment.entry_id,
            amends=original.amends,
        )
        self.entries.append(amendment)
        return True

    @property
    def active_entries(self) -> List[LedgerEntry]:
        """Get non-superseded entries."""
        return [e for e in self.entries if e.superseded_by is None]

    @property
    def entry_count(self) -> int:
        """Total entries including superseded."""
        return len(self.entries)


@dataclass
class Treasury:
    """Society ATP pool per spec §1.2.3.

    Tracks deposits, allocations to citizens, and reclaims.
    Balance = deposits - allocations + reclaims.
    """
    balance: float = 0.0
    total_deposited: float = 0.0
    total_allocated: float = 0.0
    allocations: Dict[str, float] = field(default_factory=dict)  # entity_lct → amount

    def deposit(self, amount: float) -> None:
        """Deposit ATP into treasury."""
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.balance += amount
        self.total_deposited += amount

    def allocate(self, entity_lct: str, amount: float) -> bool:
        """Allocate ATP from treasury to a citizen. Returns False if insufficient funds."""
        if amount <= 0:
            raise ValueError("Allocation amount must be positive")
        if amount > self.balance:
            return False
        self.balance -= amount
        self.total_allocated += amount
        self.allocations[entity_lct] = self.allocations.get(entity_lct, 0.0) + amount
        return True

    def reclaim(self, entity_lct: str, amount: float) -> bool:
        """Reclaim ATP from a citizen back to treasury. Returns False if over-reclaim."""
        if amount <= 0:
            raise ValueError("Reclaim amount must be positive")
        current = self.allocations.get(entity_lct, 0.0)
        if amount > current:
            return False
        self.allocations[entity_lct] = current - amount
        if self.allocations[entity_lct] == 0:
            del self.allocations[entity_lct]
        self.balance += amount
        return True

    @property
    def total_outstanding(self) -> float:
        """Total ATP currently allocated to entities."""
        return sum(self.allocations.values())


@dataclass
class SocietyState:
    """Composite society state — the core orchestration type.

    Composes federation.Society with metabolic state, treasury, ledger,
    and citizen trust profiles. Per the spec: "A society is not just a
    group — it's a living entity with laws as DNA, ledger as memory,
    and citizens as cells."
    """
    society: Society
    phase: SocietyPhase
    metabolic_state: MetabolicState
    treasury: Treasury
    ledger: SocietyLedger
    citizen_trust: Dict[str, TrustProfile] = field(default_factory=dict)
    founded_at: str = ""

    @property
    def society_id(self) -> str:
        return self.society.society_id

    @property
    def name(self) -> str:
        return self.society.name

    @property
    def citizen_count(self) -> int:
        return len(self.society.citizens)

    @property
    def is_operational(self) -> bool:
        return self.phase == SocietyPhase.OPERATIONAL

    @property
    def is_active(self) -> bool:
        """Society is active if operational and in a non-dormant metabolic state."""
        return self.is_operational and not is_dormant(self.metabolic_state)


# ── Society Lifecycle ─────────────────────────────────────────────


def create_society(
    society_id: str,
    name: str,
    founders: List[str],
    timestamp: str,
    initial_law: Optional[LawDataset] = None,
    ledger_type: LedgerType = LedgerType.CONFINED,
    quorum_policy: Optional[QuorumPolicy] = None,
    initial_treasury: float = 0.0,
    parent: Optional[Society] = None,
) -> SocietyState:
    """Create a new society per spec §1.3 formation process.

    Requires at least 2 founders. Progresses through GENESIS → BOOTSTRAP →
    OPERATIONAL, recording each phase transition on the ledger.

    Args:
        society_id: Unique society identifier (typically an LCT ID).
        name: Human-readable name.
        founders: LCT IDs of founding entities (minimum 2).
        timestamp: ISO timestamp of formation.
        initial_law: Optional law dataset to publish at genesis.
        ledger_type: Type of ledger (CONFINED, WITNESSED, PARTICIPATORY).
        quorum_policy: Witness quorum requirements (defaults to UNANIMOUS among founders).
        initial_treasury: ATP to seed the treasury with.
        parent: Parent society for fractal hierarchy.

    Returns:
        SocietyState in OPERATIONAL phase with founders as active citizens.
    """
    if len(founders) < 2:
        raise ValueError("Society requires at least 2 founders")

    if quorum_policy is None:
        quorum_policy = QuorumPolicy(mode=QuorumMode.UNANIMOUS, required=len(founders))

    # Create federation.Society
    fed_society = Society(
        society_id=society_id,
        name=name,
        quorum_policy=quorum_policy,
        ledger_type=ledger_type,
        parent=parent,
    )

    if initial_law is not None:
        fed_society.set_law(initial_law)

    # Create ledger and record genesis
    ledger = SocietyLedger(ledger_type=ledger_type)
    ledger.append(LedgerEntry(
        entry_id=f"{society_id}-genesis",
        event_type=LedgerEventType.FORMATION,
        action="genesis",
        data={"founders": founders, "name": name},
        timestamp=timestamp,
        witnesses=founders,
    ))

    # Create treasury
    treasury = Treasury()
    if initial_treasury > 0:
        treasury.deposit(initial_treasury)

    # Build state starting at GENESIS
    state = SocietyState(
        society=fed_society,
        phase=SocietyPhase.GENESIS,
        metabolic_state=MetabolicState.ACTIVE,
        treasury=treasury,
        ledger=ledger,
        founded_at=timestamp,
    )

    # Register founders as citizens
    for founder_lct in founders:
        _register_citizen(state, founder_lct, timestamp, founders)

    # Transition to BOOTSTRAP
    state.phase = SocietyPhase.BOOTSTRAP
    ledger.append(LedgerEntry(
        entry_id=f"{society_id}-bootstrap",
        event_type=LedgerEventType.FORMATION,
        action="bootstrap",
        data={"citizen_count": len(founders), "treasury": initial_treasury},
        timestamp=timestamp,
        witnesses=founders,
    ))

    # Transition to OPERATIONAL
    state.phase = SocietyPhase.OPERATIONAL
    ledger.append(LedgerEntry(
        entry_id=f"{society_id}-operational",
        event_type=LedgerEventType.FORMATION,
        action="operational",
        data={},
        timestamp=timestamp,
        witnesses=founders,
    ))

    return state


def _register_citizen(
    state: SocietyState,
    entity_lct: str,
    timestamp: str,
    witnesses: List[str],
) -> None:
    """Internal: register a citizen without ledger recording (used during formation)."""
    state.society.citizens.add(entity_lct)
    record = CitizenshipRecord(
        entity_lct=entity_lct,
        society_id=state.society_id,
        status=CitizenshipStatus.ACTIVE,
        rights=["vote", "propose", "allocate"],
        obligations=["abide_law", "witness"],
        witnesses=witnesses,
        granted_at=timestamp,
    )
    state.society.citizenship_records[entity_lct] = record
    state.citizen_trust[entity_lct] = TrustProfile(entity_id=entity_lct)


# ── Membership Operations ─────────────────────────────────────────


def admit_citizen(
    state: SocietyState,
    entity_lct: str,
    timestamp: str,
    witnesses: List[str],
    rights: Optional[List[str]] = None,
    obligations: Optional[List[str]] = None,
) -> bool:
    """Admit a new citizen to the society.

    Requires society to be operational and metabolic state to accept new citizens.
    Returns False if preconditions not met or entity already a citizen.
    """
    if not state.is_operational:
        return False
    if not accepts_new_citizens(state.metabolic_state):
        return False
    if state.society.is_citizen(entity_lct):
        return False

    if rights is None:
        rights = ["vote", "propose"]
    if obligations is None:
        obligations = ["abide_law", "witness"]

    state.society.citizens.add(entity_lct)
    record = CitizenshipRecord(
        entity_lct=entity_lct,
        society_id=state.society_id,
        status=CitizenshipStatus.ACTIVE,
        rights=rights,
        obligations=obligations,
        witnesses=witnesses,
        granted_at=timestamp,
    )
    state.society.citizenship_records[entity_lct] = record
    state.citizen_trust[entity_lct] = TrustProfile(entity_id=entity_lct)

    state.ledger.append(LedgerEntry(
        entry_id=f"{state.society_id}-citizen-{entity_lct}-admit",
        event_type=LedgerEventType.CITIZENSHIP,
        action="grant",
        data={"entity_lct": entity_lct, "rights": rights, "obligations": obligations},
        timestamp=timestamp,
        witnesses=witnesses,
    ))

    return True


def suspend_citizen(
    state: SocietyState,
    entity_lct: str,
    timestamp: str,
    witnesses: List[str],
    reason: str = "",
) -> bool:
    """Suspend a citizen's membership. Returns False if not a citizen or invalid transition."""
    if not state.society.is_citizen(entity_lct):
        return False

    result = state.society.suspend_citizen(entity_lct)
    if not result:
        return False

    state.ledger.append(LedgerEntry(
        entry_id=f"{state.society_id}-citizen-{entity_lct}-suspend-{timestamp}",
        event_type=LedgerEventType.CITIZENSHIP,
        action="suspend",
        data={"entity_lct": entity_lct, "reason": reason},
        timestamp=timestamp,
        witnesses=witnesses,
    ))

    return True


def reinstate_citizen(
    state: SocietyState,
    entity_lct: str,
    timestamp: str,
    witnesses: List[str],
) -> bool:
    """Reinstate a suspended citizen. Returns False if not suspended."""
    record = state.society.get_citizenship(entity_lct)
    if record is None:
        return False
    if record.status != CitizenshipStatus.SUSPENDED:
        return False

    result = state.society.reinstate_citizen(entity_lct)
    if not result:
        return False

    state.ledger.append(LedgerEntry(
        entry_id=f"{state.society_id}-citizen-{entity_lct}-reinstate-{timestamp}",
        event_type=LedgerEventType.CITIZENSHIP,
        action="reinstate",
        data={"entity_lct": entity_lct},
        timestamp=timestamp,
        witnesses=witnesses,
    ))

    return True


def terminate_citizen(
    state: SocietyState,
    entity_lct: str,
    timestamp: str,
    witnesses: List[str],
    reason: str = "",
) -> bool:
    """Terminate a citizen's membership permanently.

    Reclaims any outstanding treasury allocations back to the society pool.
    """
    if not state.society.is_citizen(entity_lct):
        return False

    # Reclaim outstanding allocations before termination
    allocated = state.treasury.allocations.get(entity_lct, 0.0)
    if allocated > 0:
        state.treasury.reclaim(entity_lct, allocated)

    result = state.society.terminate_citizen(entity_lct)
    if not result:
        return False

    state.ledger.append(LedgerEntry(
        entry_id=f"{state.society_id}-citizen-{entity_lct}-terminate-{timestamp}",
        event_type=LedgerEventType.CITIZENSHIP,
        action="terminate",
        data={
            "entity_lct": entity_lct,
            "reason": reason,
            "atp_reclaimed": allocated,
        },
        timestamp=timestamp,
        witnesses=witnesses,
    ))

    return True


# ── Metabolic State ───────────────────────────────────────────────


def transition_metabolic_state(
    state: SocietyState,
    new_state: MetabolicState,
    timestamp: str,
    witnesses: List[str],
) -> bool:
    """Transition the society's metabolic state.

    Validates transition legality per metabolic module rules.
    Records the transition on the ledger.
    """
    if not valid_metabolic_transition(state.metabolic_state, new_state):
        return False

    old_state = state.metabolic_state
    state.metabolic_state = new_state

    state.ledger.append(LedgerEntry(
        entry_id=f"{state.society_id}-metabolic-{timestamp}",
        event_type=LedgerEventType.METABOLIC,
        action="transition",
        data={"from": old_state.value, "to": new_state.value},
        timestamp=timestamp,
        witnesses=witnesses,
    ))

    return True


# ── Treasury Operations ───────────────────────────────────────────


def deposit_treasury(
    state: SocietyState,
    amount: float,
    timestamp: str,
    source: str = "",
) -> None:
    """Deposit ATP into the society treasury. Records on ledger."""
    state.treasury.deposit(amount)

    state.ledger.append(LedgerEntry(
        entry_id=f"{state.society_id}-deposit-{timestamp}",
        event_type=LedgerEventType.ECONOMIC,
        action="deposit",
        data={"amount": amount, "source": source, "token_type": "ATP"},
        timestamp=timestamp,
    ))


def allocate_treasury(
    state: SocietyState,
    entity_lct: str,
    amount: float,
    timestamp: str,
    purpose: str = "",
) -> bool:
    """Allocate ATP from treasury to a citizen.

    Requires society to accept transactions in current metabolic state
    and entity to be an active citizen.
    """
    if not accepts_transactions(state.metabolic_state):
        return False
    if not state.society.is_citizen(entity_lct):
        return False

    result = state.treasury.allocate(entity_lct, amount)
    if not result:
        return False

    state.ledger.append(LedgerEntry(
        entry_id=f"{state.society_id}-alloc-{entity_lct}-{timestamp}",
        event_type=LedgerEventType.ECONOMIC,
        action="allocate",
        data={
            "entity_lct": entity_lct,
            "amount": amount,
            "purpose": purpose,
            "token_type": "ATP",
        },
        timestamp=timestamp,
    ))

    return True


# ── Law Recording ─────────────────────────────────────────────────


def record_law_change(
    state: SocietyState,
    law: LawDataset,
    timestamp: str,
    witnesses: List[str],
    action: str = "ratify",
) -> None:
    """Record a law change and update the society's active law.

    action should be one of: "propose", "ratify", "amend", "repeal".
    """
    state.society.set_law(law)

    state.ledger.append(LedgerEntry(
        entry_id=f"{state.society_id}-law-{law.law_id}-{timestamp}",
        event_type=LedgerEventType.LAW_CHANGE,
        action=action,
        data={
            "law_id": law.law_id,
            "version": law.version,
            "norm_count": len(law.norms),
            "procedure_count": len(law.procedures),
        },
        timestamp=timestamp,
        witnesses=witnesses,
    ))


# ── Trust Computation ─────────────────────────────────────────────


def compute_society_t3(
    state: SocietyState,
    role: str = "citizen",
) -> Optional[T3]:
    """Compute aggregate society-level T3 from active citizens' trust per spec §5.3.

    Uses compute_team_t3 from trust module — weighted average of all
    active citizens' trust tensors in the given role.
    Returns None if no active citizens with trust profiles.
    """
    profiles = []
    for lct_id, profile in state.citizen_trust.items():
        record = state.society.get_citizenship(lct_id)
        if record and record.is_active:
            profiles.append(profile)

    if not profiles:
        return None

    return compute_team_t3(profiles, role)


def society_energy_cost(
    state: SocietyState,
    hours: float = 1.0,
    baseline_cost_per_hour: float = 1.0,
) -> float:
    """Compute energy cost for the society in its current metabolic state.

    Uses the metabolic module's energy_cost formula:
    baseline_cost * energy_multiplier * society_size * hours
    """
    return energy_cost(
        state.metabolic_state,
        baseline_cost_per_hour,
        state.citizen_count,
        hours,
    )


def society_health(
    state: SocietyState,
    role: str = "citizen",
) -> Optional[float]:
    """Compute society operational health score.

    Combines aggregate T3 composite with treasury energy ratio via
    the trust module's operational_health function.
    Returns None if no active citizens with trust profiles.
    """
    t3 = compute_society_t3(state, role)
    if t3 is None:
        return None

    # Energy ratio: balance / (balance + outstanding allocations)
    total_energy = state.treasury.balance + state.treasury.total_outstanding
    if total_energy == 0:
        energy_ratio = 0.5  # neutral if no economic activity yet
    else:
        energy_ratio = state.treasury.balance / total_energy

    # Use T3 composite as proxy for V3 since V3 is not aggregated at society level
    return operational_health(t3.composite, t3.composite, energy_ratio)


# ── Fractal Hierarchy ─────────────────────────────────────────────


def incorporate_child(
    parent_state: SocietyState,
    child_state: SocietyState,
    timestamp: str,
) -> bool:
    """Incorporate a child society per spec §3 (fractal hierarchies).

    Sets parent-child relationship and records on both ledgers.
    Returns False if child already has a parent.
    """
    if child_state.society.parent is not None:
        return False

    child_state.society.parent = parent_state.society
    parent_state.society.children.append(child_state.society)

    parent_state.ledger.append(LedgerEntry(
        entry_id=f"{parent_state.society_id}-child-{child_state.society_id}-{timestamp}",
        event_type=LedgerEventType.FORMATION,
        action="incorporate_child",
        data={
            "child_society_id": child_state.society_id,
            "child_name": child_state.name,
        },
        timestamp=timestamp,
    ))

    child_state.ledger.append(LedgerEntry(
        entry_id=f"{child_state.society_id}-parent-{parent_state.society_id}-{timestamp}",
        event_type=LedgerEventType.FORMATION,
        action="incorporated_by",
        data={
            "parent_society_id": parent_state.society_id,
            "parent_name": parent_state.name,
        },
        timestamp=timestamp,
    ))

    return True


def society_depth(state: SocietyState) -> int:
    """Get the depth of this society in the fractal hierarchy."""
    return state.society.depth


def society_ancestry(state: SocietyState) -> List[str]:
    """Get the ancestry chain (society IDs from root to self)."""
    return state.society.ancestry
