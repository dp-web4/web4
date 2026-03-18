"""
Tests for web4.society — society composition module.

Tests cover:
1. SocietyPhase and LedgerEventType enums
2. LedgerEntry immutability
3. SocietyLedger operations (append, query, amend)
4. Treasury operations (deposit, allocate, reclaim)
5. SocietyState properties
6. Society creation (create_society lifecycle)
7. Citizen admission (metabolic gating, duplicates, ledger recording)
8. Citizen lifecycle (suspend, reinstate, terminate)
9. Metabolic state transitions
10. Treasury allocation (with metabolic gating)
11. Law recording
12. Society-level T3 computation
13. Society health scoring
14. Fractal hierarchy (incorporate_child)
15. Test vector validation
"""

import json
import os

import pytest

from web4.society import (
    SocietyPhase, LedgerEventType,
    LedgerEntry, SocietyLedger, Treasury, SocietyState,
    create_society,
    admit_citizen, suspend_citizen, reinstate_citizen, terminate_citizen,
    transition_metabolic_state,
    deposit_treasury, allocate_treasury,
    record_law_change,
    compute_society_t3, society_energy_cost, society_health,
    incorporate_child, society_depth, society_ancestry,
)
from web4.federation import (
    LedgerType, LawDataset, Norm, Procedure, QuorumPolicy, QuorumMode,
    CitizenshipStatus,
)
from web4.metabolic import MetabolicState
from web4.trust import T3, TrustProfile


# ── Helpers ───────────────────────────────────────────────────────

TIMESTAMP = "2026-03-17T18:00:00Z"
FOUNDERS = ["lct:alice", "lct:bob"]
WITNESSES = ["lct:alice", "lct:bob"]


def _make_society(**kwargs) -> SocietyState:
    """Create a default operational society for testing."""
    defaults = dict(
        society_id="lct:society:test",
        name="Test Society",
        founders=FOUNDERS,
        timestamp=TIMESTAMP,
    )
    defaults.update(kwargs)
    return create_society(**defaults)


def _make_law(law_id="law-v1", version="1.0") -> LawDataset:
    """Create a minimal law dataset for testing."""
    return LawDataset(
        law_id=law_id,
        version=version,
        society_id="lct:society:test",
        norms=[Norm(
            norm_id="NORM-001",
            selector="atp_minimum",
            op=">=",
            value=10,
            description="Minimum ATP",
        )],
        procedures=[Procedure(
            procedure_id="PROC-001",
            requires_witnesses=2,
            description="Witness requirement",
        )],
    )


# ── Enums ─────────────────────────────────────────────────────────


class TestEnums:
    """SocietyPhase and LedgerEventType enums."""

    def test_society_phase_values(self):
        assert SocietyPhase.GENESIS.value == "genesis"
        assert SocietyPhase.BOOTSTRAP.value == "bootstrap"
        assert SocietyPhase.OPERATIONAL.value == "operational"

    def test_society_phase_count(self):
        assert len(SocietyPhase) == 3

    def test_ledger_event_type_values(self):
        assert LedgerEventType.CITIZENSHIP.value == "citizenship"
        assert LedgerEventType.LAW_CHANGE.value == "law_change"
        assert LedgerEventType.ECONOMIC.value == "economic"
        assert LedgerEventType.METABOLIC.value == "metabolic"
        assert LedgerEventType.FORMATION.value == "formation"

    def test_ledger_event_type_count(self):
        assert len(LedgerEventType) == 5


# ── LedgerEntry ───────────────────────────────────────────────────


class TestLedgerEntry:
    """LedgerEntry is frozen (immutable)."""

    def test_create(self):
        entry = LedgerEntry(
            entry_id="e1",
            event_type=LedgerEventType.CITIZENSHIP,
            action="grant",
            data={"entity": "alice"},
            timestamp=TIMESTAMP,
            witnesses=["w1"],
        )
        assert entry.entry_id == "e1"
        assert entry.event_type == LedgerEventType.CITIZENSHIP
        assert entry.action == "grant"
        assert entry.superseded_by is None
        assert entry.amends is None

    def test_immutable(self):
        entry = LedgerEntry(
            entry_id="e1",
            event_type=LedgerEventType.FORMATION,
            action="genesis",
            data={},
            timestamp=TIMESTAMP,
        )
        with pytest.raises(AttributeError):
            entry.action = "modified"


# ── SocietyLedger ─────────────────────────────────────────────────


class TestSocietyLedger:
    """SocietyLedger append, query, amend operations."""

    def test_append_and_count(self):
        ledger = SocietyLedger(ledger_type=LedgerType.CONFINED)
        assert ledger.entry_count == 0
        ledger.append(LedgerEntry(
            entry_id="e1",
            event_type=LedgerEventType.FORMATION,
            action="genesis",
            data={},
            timestamp=TIMESTAMP,
        ))
        assert ledger.entry_count == 1

    def test_query_by_event_type(self):
        ledger = SocietyLedger(ledger_type=LedgerType.CONFINED)
        ledger.append(LedgerEntry("e1", LedgerEventType.FORMATION, "genesis", {}, TIMESTAMP))
        ledger.append(LedgerEntry("e2", LedgerEventType.CITIZENSHIP, "grant", {}, TIMESTAMP))
        ledger.append(LedgerEntry("e3", LedgerEventType.FORMATION, "bootstrap", {}, TIMESTAMP))

        formation = ledger.query(event_type=LedgerEventType.FORMATION)
        assert len(formation) == 2
        citizenship = ledger.query(event_type=LedgerEventType.CITIZENSHIP)
        assert len(citizenship) == 1

    def test_query_by_action(self):
        ledger = SocietyLedger(ledger_type=LedgerType.CONFINED)
        ledger.append(LedgerEntry("e1", LedgerEventType.CITIZENSHIP, "grant", {}, TIMESTAMP))
        ledger.append(LedgerEntry("e2", LedgerEventType.CITIZENSHIP, "suspend", {}, TIMESTAMP))

        grants = ledger.query(action="grant")
        assert len(grants) == 1
        assert grants[0].entry_id == "e1"

    def test_query_combined_filters(self):
        ledger = SocietyLedger(ledger_type=LedgerType.CONFINED)
        ledger.append(LedgerEntry("e1", LedgerEventType.ECONOMIC, "deposit", {}, TIMESTAMP))
        ledger.append(LedgerEntry("e2", LedgerEventType.ECONOMIC, "allocate", {}, TIMESTAMP))
        ledger.append(LedgerEntry("e3", LedgerEventType.CITIZENSHIP, "grant", {}, TIMESTAMP))

        result = ledger.query(event_type=LedgerEventType.ECONOMIC, action="allocate")
        assert len(result) == 1
        assert result[0].entry_id == "e2"

    def test_get_entry(self):
        ledger = SocietyLedger(ledger_type=LedgerType.CONFINED)
        ledger.append(LedgerEntry("e1", LedgerEventType.FORMATION, "genesis", {}, TIMESTAMP))
        assert ledger.get_entry("e1") is not None
        assert ledger.get_entry("e1").entry_id == "e1"
        assert ledger.get_entry("nonexistent") is None

    def test_amend_entry(self):
        ledger = SocietyLedger(ledger_type=LedgerType.CONFINED)
        ledger.append(LedgerEntry(
            "original", LedgerEventType.ECONOMIC, "allocate",
            {"amount": 100}, TIMESTAMP,
        ))

        amendment = LedgerEntry(
            entry_id="amendment-1",
            event_type=LedgerEventType.ECONOMIC,
            action="allocate",
            data={"amount": 90, "correction": "calculation error"},
            timestamp="2026-03-17T19:00:00Z",
            amends="original",
        )

        assert ledger.amend("original", amendment)
        assert ledger.entry_count == 2  # both preserved

        # Original is superseded
        orig = ledger.get_entry("original")
        assert orig.superseded_by == "amendment-1"

        # Amendment links back
        amend = ledger.get_entry("amendment-1")
        assert amend.amends == "original"

    def test_amend_nonexistent_fails(self):
        ledger = SocietyLedger(ledger_type=LedgerType.CONFINED)
        amendment = LedgerEntry("a1", LedgerEventType.ECONOMIC, "allocate", {}, TIMESTAMP)
        assert not ledger.amend("nonexistent", amendment)

    def test_amend_already_superseded_fails(self):
        ledger = SocietyLedger(ledger_type=LedgerType.CONFINED)
        ledger.append(LedgerEntry("e1", LedgerEventType.ECONOMIC, "allocate", {"amount": 100}, TIMESTAMP))

        a1 = LedgerEntry("a1", LedgerEventType.ECONOMIC, "allocate", {"amount": 90}, TIMESTAMP, amends="e1")
        assert ledger.amend("e1", a1)

        a2 = LedgerEntry("a2", LedgerEventType.ECONOMIC, "allocate", {"amount": 80}, TIMESTAMP, amends="e1")
        assert not ledger.amend("e1", a2)  # already superseded

    def test_active_entries(self):
        ledger = SocietyLedger(ledger_type=LedgerType.CONFINED)
        ledger.append(LedgerEntry("e1", LedgerEventType.ECONOMIC, "deposit", {"amount": 100}, TIMESTAMP))
        ledger.append(LedgerEntry("e2", LedgerEventType.ECONOMIC, "allocate", {"amount": 50}, TIMESTAMP))

        amendment = LedgerEntry("a1", LedgerEventType.ECONOMIC, "allocate", {"amount": 40}, TIMESTAMP, amends="e2")
        ledger.amend("e2", amendment)

        active = ledger.active_entries
        assert len(active) == 2  # e1 + a1 (e2 is superseded)
        active_ids = {e.entry_id for e in active}
        assert "e1" in active_ids
        assert "a1" in active_ids
        assert "e2" not in active_ids


# ── Treasury ──────────────────────────────────────────────────────


class TestTreasury:
    """Treasury deposit, allocate, reclaim operations."""

    def test_deposit(self):
        t = Treasury()
        t.deposit(100.0)
        assert t.balance == 100.0
        assert t.total_deposited == 100.0

    def test_deposit_negative_raises(self):
        t = Treasury()
        with pytest.raises(ValueError):
            t.deposit(-10)

    def test_allocate_success(self):
        t = Treasury()
        t.deposit(100.0)
        assert t.allocate("alice", 30.0)
        assert t.balance == 70.0
        assert t.allocations["alice"] == 30.0
        assert t.total_outstanding == 30.0

    def test_allocate_insufficient_funds(self):
        t = Treasury()
        t.deposit(10.0)
        assert not t.allocate("alice", 20.0)
        assert t.balance == 10.0  # unchanged

    def test_allocate_accumulates(self):
        t = Treasury()
        t.deposit(100.0)
        t.allocate("alice", 20.0)
        t.allocate("alice", 10.0)
        assert t.allocations["alice"] == 30.0

    def test_reclaim_success(self):
        t = Treasury()
        t.deposit(100.0)
        t.allocate("alice", 30.0)
        assert t.reclaim("alice", 10.0)
        assert t.balance == 80.0
        assert t.allocations["alice"] == 20.0

    def test_reclaim_full_removes_key(self):
        t = Treasury()
        t.deposit(100.0)
        t.allocate("alice", 30.0)
        assert t.reclaim("alice", 30.0)
        assert "alice" not in t.allocations

    def test_reclaim_over_allocated_fails(self):
        t = Treasury()
        t.deposit(100.0)
        t.allocate("alice", 30.0)
        assert not t.reclaim("alice", 50.0)

    def test_reclaim_nonexistent_fails(self):
        t = Treasury()
        assert not t.reclaim("nobody", 10.0)

    def test_total_outstanding(self):
        t = Treasury()
        t.deposit(100.0)
        t.allocate("alice", 30.0)
        t.allocate("bob", 20.0)
        assert t.total_outstanding == 50.0


# ── Society Creation ──────────────────────────────────────────────


class TestCreateSociety:
    """create_society lifecycle: genesis → bootstrap → operational."""

    def test_basic_creation(self):
        state = _make_society()
        assert state.society_id == "lct:society:test"
        assert state.name == "Test Society"
        assert state.phase == SocietyPhase.OPERATIONAL
        assert state.metabolic_state == MetabolicState.ACTIVE
        assert state.citizen_count == 2
        assert state.is_operational
        assert state.is_active

    def test_founders_are_citizens(self):
        state = _make_society()
        assert state.society.is_citizen("lct:alice")
        assert state.society.is_citizen("lct:bob")

    def test_founders_have_trust_profiles(self):
        state = _make_society()
        assert "lct:alice" in state.citizen_trust
        assert "lct:bob" in state.citizen_trust
        assert isinstance(state.citizen_trust["lct:alice"], TrustProfile)

    def test_ledger_records_formation(self):
        state = _make_society()
        formation = state.ledger.query(event_type=LedgerEventType.FORMATION)
        assert len(formation) == 3  # genesis, bootstrap, operational
        actions = [e.action for e in formation]
        assert actions == ["genesis", "bootstrap", "operational"]

    def test_genesis_entry_has_founders(self):
        state = _make_society()
        genesis = state.ledger.get_entry("lct:society:test-genesis")
        assert genesis is not None
        assert set(genesis.data["founders"]) == {"lct:alice", "lct:bob"}

    def test_requires_two_founders(self):
        with pytest.raises(ValueError, match="at least 2 founders"):
            create_society("s1", "Solo", ["lct:alone"], TIMESTAMP)

    def test_initial_treasury(self):
        state = _make_society(initial_treasury=500.0)
        assert state.treasury.balance == 500.0
        assert state.treasury.total_deposited == 500.0

    def test_zero_treasury_default(self):
        state = _make_society()
        assert state.treasury.balance == 0.0

    def test_custom_quorum_policy(self):
        qp = QuorumPolicy(mode=QuorumMode.MAJORITY, required=2)
        state = _make_society(quorum_policy=qp)
        assert state.society.quorum_policy.mode == QuorumMode.MAJORITY

    def test_initial_law(self):
        law = _make_law()
        state = _make_society(initial_law=law)
        assert state.society.law is not None
        assert state.society.law.law_id == "law-v1"

    def test_founded_at_recorded(self):
        state = _make_society()
        assert state.founded_at == TIMESTAMP


# ── Citizen Admission ─────────────────────────────────────────────


class TestAdmitCitizen:
    """Citizen admission with metabolic gating and ledger recording."""

    def test_admit_success(self):
        state = _make_society()
        result = admit_citizen(state, "lct:charlie", TIMESTAMP, WITNESSES)
        assert result is True
        assert state.society.is_citizen("lct:charlie")
        assert state.citizen_count == 3

    def test_admit_records_on_ledger(self):
        state = _make_society()
        admit_citizen(state, "lct:charlie", TIMESTAMP, WITNESSES)
        grants = state.ledger.query(event_type=LedgerEventType.CITIZENSHIP, action="grant")
        assert len(grants) == 1
        assert grants[0].data["entity_lct"] == "lct:charlie"

    def test_admit_creates_trust_profile(self):
        state = _make_society()
        admit_citizen(state, "lct:charlie", TIMESTAMP, WITNESSES)
        assert "lct:charlie" in state.citizen_trust

    def test_admit_duplicate_fails(self):
        state = _make_society()
        assert not admit_citizen(state, "lct:alice", TIMESTAMP, WITNESSES)

    def test_admit_blocked_in_dormant_state(self):
        state = _make_society()
        transition_metabolic_state(state, MetabolicState.REST, TIMESTAMP, WITNESSES)
        transition_metabolic_state(state, MetabolicState.SLEEP, TIMESTAMP, WITNESSES)
        assert not admit_citizen(state, "lct:charlie", TIMESTAMP, WITNESSES)

    def test_admit_custom_rights(self):
        state = _make_society()
        admit_citizen(state, "lct:charlie", TIMESTAMP, WITNESSES,
                      rights=["read"], obligations=["contribute"])
        record = state.society.get_citizenship("lct:charlie")
        assert "read" in record.rights
        assert "contribute" in record.obligations


# ── Citizen Lifecycle ─────────────────────────────────────────────


class TestCitizenLifecycle:
    """Suspend, reinstate, terminate with ledger recording."""

    def test_suspend(self):
        state = _make_society()
        result = suspend_citizen(state, "lct:alice", TIMESTAMP, WITNESSES, reason="misconduct")
        assert result is True
        record = state.society.get_citizenship("lct:alice")
        assert record.status == CitizenshipStatus.SUSPENDED

    def test_suspend_records_on_ledger(self):
        state = _make_society()
        suspend_citizen(state, "lct:alice", TIMESTAMP, WITNESSES, reason="misconduct")
        suspensions = state.ledger.query(event_type=LedgerEventType.CITIZENSHIP, action="suspend")
        assert len(suspensions) == 1
        assert suspensions[0].data["reason"] == "misconduct"

    def test_reinstate(self):
        state = _make_society()
        suspend_citizen(state, "lct:alice", TIMESTAMP, WITNESSES)
        result = reinstate_citizen(state, "lct:alice", TIMESTAMP, WITNESSES)
        assert result is True
        record = state.society.get_citizenship("lct:alice")
        assert record.status == CitizenshipStatus.ACTIVE

    def test_reinstate_non_suspended_fails(self):
        state = _make_society()
        assert not reinstate_citizen(state, "lct:alice", TIMESTAMP, WITNESSES)

    def test_terminate(self):
        state = _make_society()
        result = terminate_citizen(state, "lct:alice", TIMESTAMP, WITNESSES, reason="left")
        assert result is True
        assert not state.society.is_citizen("lct:alice")

    def test_terminate_records_on_ledger(self):
        state = _make_society()
        terminate_citizen(state, "lct:alice", TIMESTAMP, WITNESSES)
        terms = state.ledger.query(event_type=LedgerEventType.CITIZENSHIP, action="terminate")
        assert len(terms) == 1

    def test_terminate_reclaims_treasury(self):
        state = _make_society(initial_treasury=100.0)
        allocate_treasury(state, "lct:alice", 30.0, TIMESTAMP, "grant")
        assert state.treasury.balance == 70.0
        terminate_citizen(state, "lct:alice", TIMESTAMP, WITNESSES)
        assert state.treasury.balance == 100.0

    def test_terminate_nonexistent_fails(self):
        state = _make_society()
        assert not terminate_citizen(state, "lct:nobody", TIMESTAMP, WITNESSES)

    def test_suspend_nonexistent_fails(self):
        state = _make_society()
        assert not suspend_citizen(state, "lct:nobody", TIMESTAMP, WITNESSES)

    def test_reinstate_nonexistent_fails(self):
        state = _make_society()
        assert not reinstate_citizen(state, "lct:nobody", TIMESTAMP, WITNESSES)


# ── Metabolic State Transitions ───────────────────────────────────


class TestMetabolicTransitions:
    """Metabolic state transitions with validation and ledger recording."""

    def test_valid_transition(self):
        state = _make_society()
        assert state.metabolic_state == MetabolicState.ACTIVE
        result = transition_metabolic_state(state, MetabolicState.REST, TIMESTAMP, WITNESSES)
        assert result is True
        assert state.metabolic_state == MetabolicState.REST

    def test_invalid_transition_rejected(self):
        state = _make_society()
        # ACTIVE → HIBERNATION is not a valid direct transition
        result = transition_metabolic_state(state, MetabolicState.HIBERNATION, TIMESTAMP, WITNESSES)
        assert result is False
        assert state.metabolic_state == MetabolicState.ACTIVE  # unchanged

    def test_transition_records_on_ledger(self):
        state = _make_society()
        transition_metabolic_state(state, MetabolicState.REST, TIMESTAMP, WITNESSES)
        metabolic_events = state.ledger.query(event_type=LedgerEventType.METABOLIC)
        assert len(metabolic_events) == 1
        assert metabolic_events[0].data["from"] == "active"
        assert metabolic_events[0].data["to"] == "rest"

    def test_dormant_blocks_new_citizens(self):
        state = _make_society()
        transition_metabolic_state(state, MetabolicState.REST, TIMESTAMP, WITNESSES)
        transition_metabolic_state(state, MetabolicState.SLEEP, TIMESTAMP, WITNESSES)
        assert not admit_citizen(state, "lct:charlie", TIMESTAMP, WITNESSES)


# ── Treasury Allocation ───────────────────────────────────────────


class TestTreasuryAllocation:
    """Treasury operations with metabolic gating and ledger recording."""

    def test_deposit(self):
        state = _make_society()
        deposit_treasury(state, 200.0, TIMESTAMP, source="genesis_fund")
        assert state.treasury.balance == 200.0

    def test_deposit_records_on_ledger(self):
        state = _make_society()
        deposit_treasury(state, 200.0, TIMESTAMP, source="genesis_fund")
        deposits = state.ledger.query(event_type=LedgerEventType.ECONOMIC, action="deposit")
        assert len(deposits) == 1
        assert deposits[0].data["amount"] == 200.0
        assert deposits[0].data["source"] == "genesis_fund"

    def test_allocate_to_citizen(self):
        state = _make_society(initial_treasury=100.0)
        result = allocate_treasury(state, "lct:alice", 30.0, TIMESTAMP, "reward")
        assert result is True
        assert state.treasury.balance == 70.0
        assert state.treasury.allocations["lct:alice"] == 30.0

    def test_allocate_records_on_ledger(self):
        state = _make_society(initial_treasury=100.0)
        allocate_treasury(state, "lct:alice", 30.0, TIMESTAMP, "reward")
        allocs = state.ledger.query(event_type=LedgerEventType.ECONOMIC, action="allocate")
        assert len(allocs) == 1
        assert allocs[0].data["entity_lct"] == "lct:alice"
        assert allocs[0].data["amount"] == 30.0

    def test_allocate_insufficient_funds(self):
        state = _make_society(initial_treasury=10.0)
        result = allocate_treasury(state, "lct:alice", 20.0, TIMESTAMP)
        assert result is False

    def test_allocate_to_non_citizen_fails(self):
        state = _make_society(initial_treasury=100.0)
        result = allocate_treasury(state, "lct:stranger", 10.0, TIMESTAMP)
        assert result is False

    def test_allocate_blocked_in_dormant_state(self):
        state = _make_society(initial_treasury=100.0)
        transition_metabolic_state(state, MetabolicState.REST, TIMESTAMP, WITNESSES)
        transition_metabolic_state(state, MetabolicState.SLEEP, TIMESTAMP, WITNESSES)
        result = allocate_treasury(state, "lct:alice", 10.0, TIMESTAMP)
        assert result is False


# ── Law Recording ─────────────────────────────────────────────────


class TestLawRecording:
    """Law change recording with ledger events."""

    def test_record_law(self):
        state = _make_society()
        law = _make_law()
        record_law_change(state, law, TIMESTAMP, WITNESSES, action="ratify")
        assert state.society.law is not None
        assert state.society.law.law_id == "law-v1"

    def test_record_law_on_ledger(self):
        state = _make_society()
        law = _make_law()
        record_law_change(state, law, TIMESTAMP, WITNESSES, action="ratify")
        law_events = state.ledger.query(event_type=LedgerEventType.LAW_CHANGE)
        assert len(law_events) == 1
        assert law_events[0].action == "ratify"
        assert law_events[0].data["law_id"] == "law-v1"

    def test_law_amendment(self):
        state = _make_society()
        law_v1 = _make_law(law_id="law-v1", version="1.0")
        record_law_change(state, law_v1, TIMESTAMP, WITNESSES, action="ratify")

        law_v2 = _make_law(law_id="law-v2", version="2.0")
        record_law_change(state, law_v2, "2026-03-18T00:00:00Z", WITNESSES, action="amend")

        assert state.society.law.law_id == "law-v2"
        law_events = state.ledger.query(event_type=LedgerEventType.LAW_CHANGE)
        assert len(law_events) == 2


# ── Trust Computation ─────────────────────────────────────────────


class TestTrustComputation:
    """Society-level T3 computation from citizen trust profiles."""

    def test_compute_society_t3_requires_role_set(self):
        state = _make_society()
        # Fresh TrustProfiles have no roles set, so compute_team_t3 returns None
        t3 = compute_society_t3(state)
        assert t3 is None

    def test_compute_society_t3_with_defaults(self):
        state = _make_society()
        # Set the "citizen" role on both founders — now they qualify
        state.citizen_trust["lct:alice"].set_role("citizen", T3(0.5, 0.5, 0.5))
        state.citizen_trust["lct:bob"].set_role("citizen", T3(0.5, 0.5, 0.5))
        t3 = compute_society_t3(state)
        assert t3 is not None
        assert t3.talent == pytest.approx(0.5, abs=0.01)
        assert t3.training == pytest.approx(0.5, abs=0.01)
        assert t3.temperament == pytest.approx(0.5, abs=0.01)

    def test_compute_society_t3_with_set_roles(self):
        state = _make_society()
        # Set explicit trust for founders
        state.citizen_trust["lct:alice"].set_role("citizen", T3(0.8, 0.7, 0.9))
        state.citizen_trust["lct:bob"].set_role("citizen", T3(0.6, 0.5, 0.7))

        t3 = compute_society_t3(state)
        assert t3 is not None
        # Average of (0.8, 0.7, 0.9) and (0.6, 0.5, 0.7) = (0.7, 0.6, 0.8)
        assert t3.talent == pytest.approx(0.7, abs=0.01)
        assert t3.training == pytest.approx(0.6, abs=0.01)
        assert t3.temperament == pytest.approx(0.8, abs=0.01)

    def test_suspended_citizens_excluded(self):
        state = _make_society()
        state.citizen_trust["lct:alice"].set_role("citizen", T3(0.8, 0.8, 0.8))
        state.citizen_trust["lct:bob"].set_role("citizen", T3(0.2, 0.2, 0.2))

        suspend_citizen(state, "lct:bob", TIMESTAMP, WITNESSES)

        t3 = compute_society_t3(state)
        # Only alice (0.8, 0.8, 0.8) contributes
        assert t3 is not None
        assert t3.talent == pytest.approx(0.8, abs=0.01)

    def test_no_active_citizens_returns_none(self):
        state = _make_society()
        suspend_citizen(state, "lct:alice", TIMESTAMP, WITNESSES)
        suspend_citizen(state, "lct:bob", TIMESTAMP, WITNESSES)
        assert compute_society_t3(state) is None


# ── Society Health ────────────────────────────────────────────────


class TestSocietyHealth:
    """Society health score from aggregate trust and treasury."""

    def test_health_with_treasury(self):
        state = _make_society(initial_treasury=100.0)
        state.citizen_trust["lct:alice"].set_role("citizen", T3(0.8, 0.7, 0.9))
        state.citizen_trust["lct:bob"].set_role("citizen", T3(0.7, 0.6, 0.8))

        health = society_health(state)
        assert health is not None
        assert 0.0 <= health <= 1.0

    def test_health_no_citizens_returns_none(self):
        state = _make_society()
        suspend_citizen(state, "lct:alice", TIMESTAMP, WITNESSES)
        suspend_citizen(state, "lct:bob", TIMESTAMP, WITNESSES)
        assert society_health(state) is None

    def test_energy_cost(self):
        state = _make_society()
        cost = society_energy_cost(state, hours=1.0, baseline_cost_per_hour=1.0)
        # Active state multiplier = 1.0, 2 citizens, 1 hour
        assert cost == pytest.approx(2.0, abs=0.01)


# ── Fractal Hierarchy ─────────────────────────────────────────────


class TestFractalHierarchy:
    """Fractal society hierarchy: incorporate, depth, ancestry."""

    def test_incorporate_child(self):
        parent = _make_society(society_id="lct:society:parent", name="Parent")
        child = _make_society(society_id="lct:society:child", name="Child")

        result = incorporate_child(parent, child, TIMESTAMP)
        assert result is True
        assert child.society.parent is parent.society
        assert len(parent.society.children) == 1

    def test_incorporate_records_on_both_ledgers(self):
        parent = _make_society(society_id="lct:society:parent", name="Parent")
        child = _make_society(society_id="lct:society:child", name="Child")
        incorporate_child(parent, child, TIMESTAMP)

        parent_events = parent.ledger.query(action="incorporate_child")
        assert len(parent_events) == 1
        child_events = child.ledger.query(action="incorporated_by")
        assert len(child_events) == 1

    def test_double_incorporate_fails(self):
        parent1 = _make_society(society_id="lct:society:p1", name="P1")
        parent2 = _make_society(society_id="lct:society:p2", name="P2")
        child = _make_society(society_id="lct:society:child", name="Child")

        assert incorporate_child(parent1, child, TIMESTAMP)
        assert not incorporate_child(parent2, child, TIMESTAMP)

    def test_depth(self):
        root = _make_society(society_id="lct:root", name="Root")
        mid = _make_society(society_id="lct:mid", name="Mid")
        leaf = _make_society(society_id="lct:leaf", name="Leaf")

        incorporate_child(root, mid, TIMESTAMP)
        incorporate_child(mid, leaf, TIMESTAMP)

        assert society_depth(root) == 0
        assert society_depth(mid) == 1
        assert society_depth(leaf) == 2

    def test_ancestry(self):
        root = _make_society(society_id="lct:root", name="Root")
        mid = _make_society(society_id="lct:mid", name="Mid")
        leaf = _make_society(society_id="lct:leaf", name="Leaf")

        incorporate_child(root, mid, TIMESTAMP)
        incorporate_child(mid, leaf, TIMESTAMP)

        assert society_ancestry(leaf) == ["lct:root", "lct:mid", "lct:leaf"]
        assert society_ancestry(root) == ["lct:root"]


# ── Test Vector Validation ────────────────────────────────────────


class TestVectors:
    """Cross-language test vector validation."""

    @pytest.fixture
    def vectors(self):
        vec_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..",
            "test-vectors", "society", "society-vectors.json",
        )
        with open(vec_path) as f:
            return json.load(f)

    def test_vector_count(self, vectors):
        assert len(vectors["vectors"]) >= 6

    def test_minimal_society(self, vectors):
        vec = next(v for v in vectors["vectors"] if v["name"] == "minimal_society")
        state = create_society(**{
            "society_id": vec["input"]["society_id"],
            "name": vec["input"]["name"],
            "founders": vec["input"]["founders"],
            "timestamp": vec["input"]["timestamp"],
        })
        assert state.phase.value == vec["expected"]["phase"]
        assert state.citizen_count == vec["expected"]["citizen_count"]
        assert state.metabolic_state.value == vec["expected"]["metabolic_state"]
        assert state.ledger.entry_count == vec["expected"]["ledger_entry_count"]

    def test_society_with_treasury(self, vectors):
        vec = next(v for v in vectors["vectors"] if v["name"] == "society_with_treasury")
        state = create_society(**{
            "society_id": vec["input"]["society_id"],
            "name": vec["input"]["name"],
            "founders": vec["input"]["founders"],
            "timestamp": vec["input"]["timestamp"],
            "initial_treasury": vec["input"]["initial_treasury"],
        })
        assert state.treasury.balance == vec["expected"]["treasury_balance"]
        assert state.treasury.total_deposited == vec["expected"]["total_deposited"]

    def test_citizen_admission(self, vectors):
        vec = next(v for v in vectors["vectors"] if v["name"] == "citizen_admission")
        state = create_society(**{
            "society_id": vec["input"]["society_id"],
            "name": vec["input"]["name"],
            "founders": vec["input"]["founders"],
            "timestamp": vec["input"]["timestamp"],
        })
        result = admit_citizen(
            state,
            vec["input"]["new_citizen"],
            vec["input"]["admit_timestamp"],
            vec["input"]["witnesses"],
        )
        assert result == vec["expected"]["admit_success"]
        assert state.citizen_count == vec["expected"]["citizen_count"]

    def test_treasury_allocation(self, vectors):
        vec = next(v for v in vectors["vectors"] if v["name"] == "treasury_allocation")
        state = create_society(**{
            "society_id": vec["input"]["society_id"],
            "name": vec["input"]["name"],
            "founders": vec["input"]["founders"],
            "timestamp": vec["input"]["timestamp"],
            "initial_treasury": vec["input"]["initial_treasury"],
        })
        result = allocate_treasury(
            state,
            vec["input"]["allocate_to"],
            vec["input"]["allocate_amount"],
            vec["input"]["timestamp"],
        )
        assert result == vec["expected"]["allocate_success"]
        assert state.treasury.balance == pytest.approx(vec["expected"]["remaining_balance"])

    def test_metabolic_transition(self, vectors):
        vec = next(v for v in vectors["vectors"] if v["name"] == "metabolic_transition")
        state = create_society(**{
            "society_id": vec["input"]["society_id"],
            "name": vec["input"]["name"],
            "founders": vec["input"]["founders"],
            "timestamp": vec["input"]["timestamp"],
        })
        result = transition_metabolic_state(
            state,
            MetabolicState(vec["input"]["target_state"]),
            vec["input"]["timestamp"],
            vec["input"]["witnesses"],
        )
        assert result == vec["expected"]["transition_success"]
        assert state.metabolic_state.value == vec["expected"]["final_state"]

    def test_fractal_hierarchy(self, vectors):
        vec = next(v for v in vectors["vectors"] if v["name"] == "fractal_hierarchy")
        parent = create_society(**{
            "society_id": vec["input"]["parent_id"],
            "name": vec["input"]["parent_name"],
            "founders": vec["input"]["founders"],
            "timestamp": vec["input"]["timestamp"],
        })
        child = create_society(**{
            "society_id": vec["input"]["child_id"],
            "name": vec["input"]["child_name"],
            "founders": vec["input"]["founders"],
            "timestamp": vec["input"]["timestamp"],
        })
        result = incorporate_child(parent, child, vec["input"]["timestamp"])
        assert result == vec["expected"]["incorporate_success"]
        assert society_depth(child) == vec["expected"]["child_depth"]
        assert society_ancestry(child) == vec["expected"]["child_ancestry"]
