"""
Trust Event Sourcing for Web4
Session 34, Track 6

CQRS/event-sourced trust state management:
- Trust events: AttestationEvent, RevocationEvent, DelegationEvent, DecayEvent
- Event store with append-only semantics
- Projections: derive current trust state from event history
- Snapshots for performance (avoid replaying entire history)
- Event replay and reconstruction
- Temporal queries (trust state at any point in time)
- Command/query separation (CQRS)
- Optimistic concurrency control

Design:
  Command side: validate + emit events (never modify state directly)
  Query side:   replay events to build read models / projections
  Invariant:    current_state = fold(events, initial_state)
  Snapshot:     (state_at_seq_N, N) lets replay start from N+1

Event sourcing ensures a complete audit trail for all trust changes,
enabling regulatory compliance, forensic investigation, and time-travel
queries ("what was entity X's trust on date Y?").
"""

import copy
import math
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple


# ─── Event Types ──────────────────────────────────────────────────

class EventType(Enum):
    ATTESTATION = "attestation"    # Trust score increased by attestation
    REVOCATION = "revocation"      # Trust score zeroed/reduced by revocation
    DELEGATION = "delegation"      # Trust delegated to another entity
    DECAY = "decay"                # Natural trust decay over time
    SNAPSHOT = "snapshot"          # Checkpoint for performance
    RESET = "reset"                # Trust reset to initial state
    CALIBRATION = "calibration"    # External calibration adjustment


@dataclass
class TrustEvent:
    """Base event. All events are immutable once appended."""
    event_id: str
    event_type: EventType
    entity_id: str
    sequence_number: int          # Monotonically increasing, global
    timestamp: float
    payload: Dict[str, Any]
    version: int = 1              # Schema version of this event
    caused_by: Optional[str] = None  # event_id that triggered this

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "entity_id": self.entity_id,
            "sequence_number": self.sequence_number,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "version": self.version,
            "caused_by": self.caused_by,
        }


def make_event(event_type: EventType, entity_id: str, seq: int,
               payload: dict, ts: Optional[float] = None,
               caused_by: Optional[str] = None) -> TrustEvent:
    eid = f"{entity_id}:{event_type.value}:{seq}"
    return TrustEvent(
        event_id=eid,
        event_type=event_type,
        entity_id=entity_id,
        sequence_number=seq,
        timestamp=ts if ts is not None else float(seq),
        payload=payload,
        caused_by=caused_by,
    )


# ─── Event Store ──────────────────────────────────────────────────

class AppendOnlyViolation(Exception):
    """Raised when attempting to modify an existing event."""
    pass


class ConcurrencyConflict(Exception):
    """Raised when optimistic concurrency check fails."""
    pass


class EventStore:
    """
    Append-only event log. Core invariant: events never modified or deleted.
    Supports optimistic concurrency via expected_version checks.
    """

    def __init__(self):
        self._events: List[TrustEvent] = []
        self._by_entity: Dict[str, List[TrustEvent]] = {}
        self._by_id: Dict[str, TrustEvent] = {}
        self._seq: int = 0

    def append(self, event: TrustEvent,
               expected_version: Optional[int] = None) -> TrustEvent:
        """
        Append event. If expected_version is given, check that entity's
        current version matches before appending (optimistic concurrency).
        """
        entity_events = self._by_entity.get(event.entity_id, [])
        current_version = len(entity_events)

        if expected_version is not None and current_version != expected_version:
            raise ConcurrencyConflict(
                f"Expected version {expected_version}, got {current_version} "
                f"for entity {event.entity_id}"
            )

        # Assign global sequence number
        self._seq += 1
        stamped = TrustEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            entity_id=event.entity_id,
            sequence_number=self._seq,
            timestamp=event.timestamp,
            payload=event.payload,
            version=event.version,
            caused_by=event.caused_by,
        )
        self._events.append(stamped)
        self._by_entity.setdefault(event.entity_id, []).append(stamped)
        self._by_id[stamped.event_id] = stamped
        return stamped

    def get_events_for_entity(self, entity_id: str,
                               from_seq: int = 0,
                               to_seq: Optional[int] = None) -> List[TrustEvent]:
        """Return all events for an entity, optionally filtered by sequence range."""
        events = self._by_entity.get(entity_id, [])
        result = [e for e in events if e.sequence_number >= from_seq]
        if to_seq is not None:
            result = [e for e in result if e.sequence_number <= to_seq]
        return result

    def get_all_events(self, from_seq: int = 0) -> List[TrustEvent]:
        """Return all events from the global log."""
        return [e for e in self._events if e.sequence_number >= from_seq]

    def get_event_by_id(self, event_id: str) -> Optional[TrustEvent]:
        return self._by_id.get(event_id)

    def entity_version(self, entity_id: str) -> int:
        """Current version (number of events) for an entity."""
        return len(self._by_entity.get(entity_id, []))

    def total_events(self) -> int:
        return len(self._events)

    def entity_count(self) -> int:
        return len(self._by_entity)

    def events_by_type(self, event_type: EventType) -> List[TrustEvent]:
        return [e for e in self._events if e.event_type == event_type]

    def immutability_check(self, event_id: str, original: TrustEvent) -> bool:
        """Verify that a stored event has not been modified."""
        stored = self._by_id.get(event_id)
        if stored is None:
            return False
        return (stored.event_id == original.event_id and
                stored.entity_id == original.entity_id and
                stored.payload == original.payload and
                stored.sequence_number == original.sequence_number)


# ─── Trust State (Projection Target) ─────────────────────────────

@dataclass
class TrustState:
    """Current trust state for one entity. Derived by projecting events."""
    entity_id: str
    trust_score: float = 0.5
    attested_count: int = 0
    revoked: bool = False
    delegations: Dict[str, float] = field(default_factory=dict)  # target -> amount
    last_updated: float = 0.0
    version: int = 0  # Number of events applied


# ─── Snapshot ─────────────────────────────────────────────────────

@dataclass
class Snapshot:
    """State checkpoint to avoid replaying all history."""
    entity_id: str
    state: TrustState
    at_sequence: int    # Global sequence number of last event included
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "at_sequence": self.at_sequence,
            "trust_score": self.state.trust_score,
            "attested_count": self.state.attested_count,
            "version": self.state.version,
        }


class SnapshotStore:
    """Stores periodic snapshots for performance optimization."""

    def __init__(self):
        self._snapshots: Dict[str, List[Snapshot]] = {}

    def save(self, snapshot: Snapshot):
        self._snapshots.setdefault(snapshot.entity_id, []).append(snapshot)

    def latest_for(self, entity_id: str) -> Optional[Snapshot]:
        snaps = self._snapshots.get(entity_id, [])
        if not snaps:
            return None
        return max(snaps, key=lambda s: s.at_sequence)

    def count_for(self, entity_id: str) -> int:
        return len(self._snapshots.get(entity_id, []))


# ─── Projection (Event Folder) ────────────────────────────────────

class TrustProjection:
    """
    Projects event streams into current TrustState.
    Pure function: state = fold(events, initial_state).
    """

    @staticmethod
    def initial_state(entity_id: str) -> TrustState:
        return TrustState(entity_id=entity_id)

    @staticmethod
    def apply_event(state: TrustState, event: TrustEvent) -> TrustState:
        """Apply a single event to produce the next state. Pure."""
        s = copy.deepcopy(state)
        s.version += 1
        s.last_updated = event.timestamp

        if event.event_type == EventType.ATTESTATION:
            delta = event.payload.get("delta", 0.0)
            weight = event.payload.get("weight", 1.0)
            s.trust_score = min(1.0, s.trust_score + delta * weight)
            s.attested_count += 1

        elif event.event_type == EventType.REVOCATION:
            severity = event.payload.get("severity", 1.0)
            s.trust_score = max(0.0, s.trust_score * (1.0 - severity))
            if event.payload.get("full_revocation", False):
                s.trust_score = 0.0
                s.revoked = True

        elif event.event_type == EventType.DELEGATION:
            target = event.payload.get("target_entity", "")
            amount = event.payload.get("amount", 0.0)
            if target:
                s.delegations[target] = amount

        elif event.event_type == EventType.DECAY:
            rate = event.payload.get("rate", 0.01)
            elapsed = event.payload.get("elapsed", 1.0)
            s.trust_score = max(0.0, s.trust_score * math.exp(-rate * elapsed))

        elif event.event_type == EventType.RESET:
            initial = event.payload.get("initial_trust", 0.5)
            s.trust_score = initial
            s.attested_count = 0
            s.revoked = False
            s.delegations = {}

        elif event.event_type == EventType.CALIBRATION:
            new_score = event.payload.get("calibrated_score")
            if new_score is not None:
                s.trust_score = max(0.0, min(1.0, new_score))

        # SNAPSHOT events are not applied to state
        return s

    @classmethod
    def project(cls, events: List[TrustEvent],
                initial: Optional[TrustState] = None) -> TrustState:
        """Fold all events onto initial state (or blank state)."""
        if not events:
            entity_id = initial.entity_id if initial else "unknown"
            return initial or cls.initial_state(entity_id)
        entity_id = events[0].entity_id
        state = initial or cls.initial_state(entity_id)
        for event in events:
            if event.event_type != EventType.SNAPSHOT:
                state = cls.apply_event(state, event)
        return state

    @classmethod
    def project_at_time(cls, events: List[TrustEvent],
                        at_time: float) -> TrustState:
        """Project state as of a specific timestamp (temporal query)."""
        filtered = [e for e in events if e.timestamp <= at_time]
        return cls.project(filtered)

    @classmethod
    def project_at_sequence(cls, events: List[TrustEvent],
                             at_seq: int) -> TrustState:
        """Project state as of a specific sequence number."""
        filtered = [e for e in events if e.sequence_number <= at_seq]
        return cls.project(filtered)


# ─── Read Model (Query Side) ──────────────────────────────────────

class TrustReadModel:
    """
    CQRS read side: maintains up-to-date projections for fast queries.
    Updated by processing new events; never directly written by commands.
    """

    def __init__(self, store: EventStore, snap_store: SnapshotStore):
        self.store = store
        self.snap_store = snap_store
        self._cache: Dict[str, TrustState] = {}

    def get_trust(self, entity_id: str) -> TrustState:
        """
        Get current trust state. Uses snapshot + replay for efficiency.
        """
        snapshot = self.snap_store.latest_for(entity_id)
        if snapshot:
            # Replay only events after the snapshot
            events = self.store.get_events_for_entity(
                entity_id,
                from_seq=snapshot.at_sequence + 1
            )
            return TrustProjection.project(events, snapshot.state)
        else:
            events = self.store.get_events_for_entity(entity_id)
            return TrustProjection.project(events)

    def get_trust_at_time(self, entity_id: str, at_time: float) -> TrustState:
        """Temporal query: what was entity's trust at a specific time?"""
        events = self.store.get_events_for_entity(entity_id)
        return TrustProjection.project_at_time(events, at_time)

    def get_trust_history(self, entity_id: str) -> List[Tuple[float, float]]:
        """Return (timestamp, trust_score) pairs for all state changes."""
        events = self.store.get_events_for_entity(entity_id)
        history = []
        state = TrustProjection.initial_state(entity_id)
        for event in events:
            if event.event_type != EventType.SNAPSHOT:
                state = TrustProjection.apply_event(state, event)
                history.append((event.timestamp, state.trust_score))
        return history

    def top_trusted_entities(self, n: int = 5) -> List[Tuple[str, float]]:
        """Query: top N entities by trust score."""
        scores = []
        for entity_id in self.store._by_entity.keys():
            state = self.get_trust(entity_id)
            scores.append((entity_id, state.trust_score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:n]

    def revoked_entities(self) -> List[str]:
        """Query: all entities with revoked trust."""
        result = []
        for entity_id in self.store._by_entity.keys():
            state = self.get_trust(entity_id)
            if state.revoked:
                result.append(entity_id)
        return result


# ─── Command Side ─────────────────────────────────────────────────

class TrustCommandHandler:
    """
    CQRS write side: validates commands and emits events.
    No direct state mutations — state is derived from events.
    """

    def __init__(self, store: EventStore):
        self.store = store
        self._seq: int = 0  # Local sequence for event ID generation

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def attest_trust(self, entity_id: str, attester_id: str,
                     delta: float, weight: float = 1.0,
                     timestamp: Optional[float] = None) -> TrustEvent:
        """Command: increase trust via attestation."""
        if not (0.0 <= delta <= 1.0):
            raise ValueError(f"delta must be in [0,1], got {delta}")
        if not (0.0 < weight <= 1.0):
            raise ValueError(f"weight must be in (0,1], got {weight}")
        event = make_event(
            EventType.ATTESTATION,
            entity_id,
            self._next_seq(),
            {"delta": delta, "weight": weight, "attester": attester_id},
            ts=timestamp,
        )
        return self.store.append(event)

    def revoke_trust(self, entity_id: str, revoker_id: str,
                     severity: float = 0.5, full: bool = False,
                     timestamp: Optional[float] = None) -> TrustEvent:
        """Command: reduce or zero trust via revocation."""
        if not (0.0 <= severity <= 1.0):
            raise ValueError(f"severity must be in [0,1], got {severity}")
        event = make_event(
            EventType.REVOCATION,
            entity_id,
            self._next_seq(),
            {"severity": severity, "revoker": revoker_id, "full_revocation": full},
            ts=timestamp,
        )
        return self.store.append(event)

    def delegate_trust(self, entity_id: str, target_entity: str,
                       amount: float,
                       timestamp: Optional[float] = None) -> TrustEvent:
        """Command: delegate a portion of trust to another entity."""
        if not (0.0 < amount <= 1.0):
            raise ValueError(f"amount must be in (0,1], got {amount}")
        event = make_event(
            EventType.DELEGATION,
            entity_id,
            self._next_seq(),
            {"target_entity": target_entity, "amount": amount},
            ts=timestamp,
        )
        return self.store.append(event)

    def apply_decay(self, entity_id: str, rate: float,
                    elapsed: float = 1.0,
                    timestamp: Optional[float] = None) -> TrustEvent:
        """Command: apply exponential trust decay."""
        if rate <= 0:
            raise ValueError(f"rate must be positive, got {rate}")
        event = make_event(
            EventType.DECAY,
            entity_id,
            self._next_seq(),
            {"rate": rate, "elapsed": elapsed},
            ts=timestamp,
        )
        return self.store.append(event)

    def reset_trust(self, entity_id: str, initial_trust: float = 0.5,
                    timestamp: Optional[float] = None) -> TrustEvent:
        """Command: reset trust to initial state."""
        event = make_event(
            EventType.RESET,
            entity_id,
            self._next_seq(),
            {"initial_trust": initial_trust},
            ts=timestamp,
        )
        return self.store.append(event)

    def calibrate_trust(self, entity_id: str, calibrated_score: float,
                        timestamp: Optional[float] = None) -> TrustEvent:
        """Command: external calibration of trust score."""
        if not (0.0 <= calibrated_score <= 1.0):
            raise ValueError(f"calibrated_score must be in [0,1]")
        event = make_event(
            EventType.CALIBRATION,
            entity_id,
            self._next_seq(),
            {"calibrated_score": calibrated_score},
            ts=timestamp,
        )
        return self.store.append(event)


# ─── Snapshot Manager ─────────────────────────────────────────────

class SnapshotManager:
    """Creates and manages snapshots for performance optimization."""

    def __init__(self, store: EventStore, snap_store: SnapshotStore,
                 snapshot_interval: int = 10):
        self.store = store
        self.snap_store = snap_store
        self.snapshot_interval = snapshot_interval

    def should_snapshot(self, entity_id: str) -> bool:
        """True if entity has accumulated enough events since last snapshot."""
        latest = self.snap_store.latest_for(entity_id)
        last_seq = latest.at_sequence if latest else 0
        all_events = self.store.get_events_for_entity(entity_id)
        events_since = sum(1 for e in all_events if e.sequence_number > last_seq)
        return events_since >= self.snapshot_interval

    def take_snapshot(self, entity_id: str) -> Optional[Snapshot]:
        """Project current state and save as snapshot."""
        latest = self.snap_store.latest_for(entity_id)
        last_seq = latest.at_sequence if latest else 0

        events = self.store.get_events_for_entity(entity_id)
        if not events:
            return None

        state = TrustProjection.project(events, latest.state if latest else None)
        max_seq = max(e.sequence_number for e in events)
        snap = Snapshot(entity_id=entity_id, state=state, at_sequence=max_seq)
        self.snap_store.save(snap)
        return snap

    def replay_from_snapshot(self, entity_id: str) -> TrustState:
        """Reconstruct state using latest snapshot + subsequent events."""
        snapshot = self.snap_store.latest_for(entity_id)
        if snapshot:
            events = self.store.get_events_for_entity(
                entity_id, from_seq=snapshot.at_sequence + 1
            )
            return TrustProjection.project(events, copy.deepcopy(snapshot.state))
        else:
            events = self.store.get_events_for_entity(entity_id)
            return TrustProjection.project(events)


# ─── Event Replay ─────────────────────────────────────────────────

class EventReplayer:
    """
    Replays event history for debugging, auditing, and reconstruction.
    Can replay to any point in time or sequence.
    """

    def __init__(self, store: EventStore):
        self.store = store

    def replay_entity(self, entity_id: str) -> List[Tuple[TrustEvent, TrustState]]:
        """Replay all events for entity, returning (event, state_after) pairs."""
        events = self.store.get_events_for_entity(entity_id)
        state = TrustProjection.initial_state(entity_id)
        result = []
        for event in events:
            if event.event_type != EventType.SNAPSHOT:
                state = TrustProjection.apply_event(state, event)
                result.append((event, copy.deepcopy(state)))
        return result

    def replay_until(self, entity_id: str,
                     until_timestamp: float) -> TrustState:
        """Replay up to (and including) a specific timestamp."""
        events = self.store.get_events_for_entity(entity_id)
        return TrustProjection.project_at_time(events, until_timestamp)

    def find_causation_chain(self, event_id: str) -> List[TrustEvent]:
        """Trace the chain of events that caused this event."""
        chain = []
        current_id = event_id
        visited = set()
        while current_id and current_id not in visited:
            visited.add(current_id)
            event = self.store.get_event_by_id(current_id)
            if event is None:
                break
            chain.append(event)
            current_id = event.caused_by
        return list(reversed(chain))

    def event_count_by_type(self, entity_id: str) -> Dict[str, int]:
        events = self.store.get_events_for_entity(entity_id)
        counts: Dict[str, int] = {}
        for e in events:
            counts[e.event_type.value] = counts.get(e.event_type.value, 0) + 1
        return counts


# ═══════════════════════════════════════════════════════════════
#  CHECKS
# ═══════════════════════════════════════════════════════════════

def run_checks():
    passed = 0
    failed = 0

    def check(name, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name}" + (f" — {detail}" if detail else ""))

    print("=" * 70)
    print("Trust Event Sourcing for Web4")
    print("Session 34, Track 6")
    print("=" * 70)

    # ── §1 Event Store Append-Only Semantics ─────────────────────
    print("\n§1 Event Store Append-Only Semantics\n")

    store = EventStore()
    check("empty_store_has_zero_events", store.total_events() == 0)
    check("empty_store_no_entities", store.entity_count() == 0)

    e1 = make_event(EventType.ATTESTATION, "alice", 1, {"delta": 0.1, "weight": 1.0}, ts=100.0)
    stored = store.append(e1)
    check("event_appended", store.total_events() == 1)
    check("entity_version_1", store.entity_version("alice") == 1)
    check("event_has_sequence_number", stored.sequence_number == 1)
    check("event_retrievable_by_id", store.get_event_by_id(stored.event_id) is not None)

    e2 = make_event(EventType.ATTESTATION, "alice", 2, {"delta": 0.05, "weight": 0.8}, ts=200.0)
    store.append(e2)
    check("second_event_appended", store.total_events() == 2)
    check("entity_version_2", store.entity_version("alice") == 2)

    # Immutability check
    check("event_immutable", store.immutability_check(stored.event_id, stored))

    # Different entity
    e3 = make_event(EventType.ATTESTATION, "bob", 3, {"delta": 0.2, "weight": 1.0}, ts=150.0)
    store.append(e3)
    check("two_entities", store.entity_count() == 2)

    # Query by entity
    alice_events = store.get_events_for_entity("alice")
    check("alice_has_2_events", len(alice_events) == 2)
    bob_events = store.get_events_for_entity("bob")
    check("bob_has_1_event", len(bob_events) == 1)

    # ── §2 Optimistic Concurrency ─────────────────────────────────
    print("\n§2 Optimistic Concurrency\n")

    store2 = EventStore()
    e = make_event(EventType.ATTESTATION, "carol", 1, {"delta": 0.1}, ts=1.0)
    store2.append(e, expected_version=0)
    check("first_append_with_version_0_ok", store2.entity_version("carol") == 1)

    # Correct expected version
    e2c = make_event(EventType.ATTESTATION, "carol", 2, {"delta": 0.1}, ts=2.0)
    store2.append(e2c, expected_version=1)
    check("second_append_with_version_1_ok", store2.entity_version("carol") == 2)

    # Wrong expected version — conflict
    e_conflict = make_event(EventType.ATTESTATION, "carol", 3, {"delta": 0.1}, ts=3.0)
    conflict_raised = False
    try:
        store2.append(e_conflict, expected_version=0)  # Should be 2
    except ConcurrencyConflict:
        conflict_raised = True
    check("concurrency_conflict_raised", conflict_raised)
    check("store_unchanged_after_conflict", store2.entity_version("carol") == 2)

    # ── §3 Trust Projection ───────────────────────────────────────
    print("\n§3 Trust Projection\n")

    proj_store = EventStore()
    cmd = TrustCommandHandler(proj_store)

    # Build up trust
    cmd.attest_trust("dave", "attester1", delta=0.2, weight=1.0, timestamp=1.0)
    cmd.attest_trust("dave", "attester2", delta=0.15, weight=0.9, timestamp=2.0)

    events = proj_store.get_events_for_entity("dave")
    state = TrustProjection.project(events)
    check("projection_entity_id", state.entity_id == "dave")
    check("projection_attested_count", state.attested_count == 2)
    expected_score = min(1.0, 0.5 + 0.2 * 1.0 + 0.15 * 0.9)  # 0.5 + 0.2 + 0.135
    check("projection_trust_score_correct",
          abs(state.trust_score - expected_score) < 1e-6,
          f"got={state.trust_score}, expected={expected_score}")
    check("projection_version_2", state.version == 2)
    check("projection_last_updated_2", state.last_updated == 2.0)

    # Decay
    cmd.apply_decay("dave", rate=0.1, elapsed=1.0, timestamp=3.0)
    events2 = proj_store.get_events_for_entity("dave")
    state2 = TrustProjection.project(events2)
    decayed = expected_score * math.exp(-0.1 * 1.0)
    check("decay_applied_correctly",
          abs(state2.trust_score - decayed) < 1e-6,
          f"got={state2.trust_score}, expected={decayed}")

    # Revocation
    cmd.revoke_trust("dave", "revoker1", severity=0.5, timestamp=4.0)
    events3 = proj_store.get_events_for_entity("dave")
    state3 = TrustProjection.project(events3)
    check("revocation_reduces_trust", state3.trust_score < state2.trust_score)
    check("revocation_trust_bounded", 0.0 <= state3.trust_score <= 1.0)

    # Full revocation
    cmd.revoke_trust("dave", "revoker2", severity=1.0, full=True, timestamp=5.0)
    events4 = proj_store.get_events_for_entity("dave")
    state4 = TrustProjection.project(events4)
    check("full_revocation_zeroes_trust", state4.trust_score == 0.0)
    check("full_revocation_sets_revoked_flag", state4.revoked)

    # Reset
    cmd.reset_trust("dave", initial_trust=0.5, timestamp=6.0)
    events5 = proj_store.get_events_for_entity("dave")
    state5 = TrustProjection.project(events5)
    check("reset_restores_initial_trust", abs(state5.trust_score - 0.5) < 1e-6)
    check("reset_clears_revoked_flag", not state5.revoked)
    check("reset_clears_attested_count", state5.attested_count == 0)

    # ── §4 Temporal Queries ───────────────────────────────────────
    print("\n§4 Temporal Queries\n")

    tq_store = EventStore()
    tq_cmd = TrustCommandHandler(tq_store)
    tq_cmd.attest_trust("eve", "a1", 0.1, timestamp=100.0)
    tq_cmd.attest_trust("eve", "a2", 0.1, timestamp=200.0)
    tq_cmd.attest_trust("eve", "a3", 0.1, timestamp=300.0)

    events_eve = tq_store.get_events_for_entity("eve")

    # State at time 150: only first attestation applied
    state_t150 = TrustProjection.project_at_time(events_eve, at_time=150.0)
    check("temporal_state_at_150_version_1", state_t150.version == 1)
    check("temporal_state_at_150_one_attestation", state_t150.attested_count == 1)

    # State at time 250: two attestations
    state_t250 = TrustProjection.project_at_time(events_eve, at_time=250.0)
    check("temporal_state_at_250_version_2", state_t250.version == 2)
    check("temporal_state_at_250_two_attestations", state_t250.attested_count == 2)

    # State at time 350: all three
    state_t350 = TrustProjection.project_at_time(events_eve, at_time=350.0)
    check("temporal_state_at_350_version_3", state_t350.version == 3)
    check("temporal_state_at_350_trust_higher",
          state_t350.trust_score > state_t150.trust_score)

    # State before any events
    state_t0 = TrustProjection.project_at_time(events_eve, at_time=50.0)
    check("temporal_state_before_events_is_initial", state_t0.trust_score == 0.5)

    # ── §5 Snapshots ──────────────────────────────────────────────
    print("\n§5 Snapshots\n")

    snap_store = SnapshotStore()
    s_store = EventStore()
    s_cmd = TrustCommandHandler(s_store)
    mgr = SnapshotManager(s_store, snap_store, snapshot_interval=3)

    # Add events
    for i in range(5):
        s_cmd.attest_trust("frank", "attester", 0.05, timestamp=float(i + 1))

    check("should_snapshot_after_5_events", mgr.should_snapshot("frank"))

    snap = mgr.take_snapshot("frank")
    check("snapshot_created", snap is not None)
    check("snapshot_at_correct_seq", snap is not None and snap.at_sequence >= 5)

    snap_count = snap_store.count_for("frank")
    check("one_snapshot_stored", snap_count == 1)

    # Add more events after snapshot
    s_cmd.attest_trust("frank", "attester", 0.05, timestamp=6.0)
    s_cmd.attest_trust("frank", "attester", 0.05, timestamp=7.0)

    # Reconstruct from snapshot + new events
    reconstructed = mgr.replay_from_snapshot("frank")
    check("reconstructed_version_correct", reconstructed.version == 7)

    # Verify consistency: full replay vs snapshot replay
    all_events = s_store.get_events_for_entity("frank")
    full_state = TrustProjection.project(all_events)
    check("snapshot_replay_matches_full_replay",
          abs(full_state.trust_score - reconstructed.trust_score) < 1e-9,
          f"full={full_state.trust_score}, snap={reconstructed.trust_score}")

    # ── §6 Command/Query Separation ───────────────────────────────
    print("\n§6 Command/Query Separation\n")

    cqrs_store = EventStore()
    cqrs_snap = SnapshotStore()
    cmd_h = TrustCommandHandler(cqrs_store)
    read_m = TrustReadModel(cqrs_store, cqrs_snap)

    # Write commands
    cmd_h.attest_trust("grace", "a1", 0.2, timestamp=1.0)
    cmd_h.attest_trust("grace", "a2", 0.15, timestamp=2.0)
    cmd_h.delegate_trust("grace", "heidi", 0.3, timestamp=3.0)
    cmd_h.attest_trust("heidi", "a1", 0.4, timestamp=4.0)

    # Query current trust
    grace_state = read_m.get_trust("grace")
    check("query_grace_trust_correct", grace_state.trust_score > 0.5)
    check("query_grace_has_delegation", "heidi" in grace_state.delegations)
    check("query_grace_delegation_amount",
          abs(grace_state.delegations["heidi"] - 0.3) < 1e-6)

    heidi_state = read_m.get_trust("heidi")
    check("query_heidi_trust_correct", heidi_state.trust_score > 0.5)

    # Trust history
    grace_history = read_m.get_trust_history("grace")
    check("history_has_3_entries", len(grace_history) == 3,
          f"len={len(grace_history)}")
    check("history_timestamps_increasing",
          all(grace_history[i][0] < grace_history[i + 1][0]
              for i in range(len(grace_history) - 1)))
    check("history_trust_monotone_increases",
          grace_history[-1][1] > grace_history[0][1])

    # Top trusted
    top = read_m.top_trusted_entities(n=2)
    check("top_trusted_returns_2", len(top) == 2)
    check("top_trusted_sorted_desc", top[0][1] >= top[1][1])

    # Revoked query
    cmd_h.revoke_trust("grace", "revoker", severity=1.0, full=True, timestamp=5.0)
    revoked = read_m.revoked_entities()
    check("revoked_entities_includes_grace", "grace" in revoked)
    check("revoked_entities_excludes_heidi", "heidi" not in revoked)

    # ── §7 Event Replay and Causation ────────────────────────────
    print("\n§7 Event Replay and Causation\n")

    rep_store = EventStore()
    rep_cmd = TrustCommandHandler(rep_store)
    replayer = EventReplayer(rep_store)

    ev1 = rep_cmd.attest_trust("ivan", "a1", 0.1, timestamp=1.0)
    ev2 = rep_cmd.apply_decay("ivan", rate=0.05, elapsed=1.0, timestamp=2.0)
    # Calibration caused by decay
    ev3 = make_event(EventType.CALIBRATION, "ivan", 99, {"calibrated_score": 0.65},
                     ts=3.0, caused_by=ev2.event_id)
    rep_store.append(ev3)

    # Full replay
    replay_result = replayer.replay_entity("ivan")
    check("replay_returns_3_entries", len(replay_result) == 3,
          f"len={len(replay_result)}")
    check("replay_last_state_calibrated",
          abs(replay_result[-1][1].trust_score - 0.65) < 1e-6,
          f"trust={replay_result[-1][1].trust_score}")

    # Causation chain
    chain = replayer.find_causation_chain(ev3.event_id)
    check("causation_chain_length_2", len(chain) == 2,
          f"len={len(chain)}")
    check("causation_chain_starts_with_cause",
          chain[0].event_id == ev2.event_id)
    check("causation_chain_ends_with_effect",
          chain[-1].event_id == ev3.event_id)

    # Event count by type
    counts = replayer.event_count_by_type("ivan")
    check("count_attestation_1", counts.get("attestation", 0) == 1)
    check("count_decay_1", counts.get("decay", 0) == 1)
    check("count_calibration_1", counts.get("calibration", 0) == 1)

    # ── §8 End-to-End CQRS Scenario ──────────────────────────────
    print("\n§8 End-to-End CQRS Scenario\n")

    # Full scenario: onboard entity, build trust, partial revoke, recover
    e2e_store = EventStore()
    e2e_snap = SnapshotStore()
    e2e_cmd = TrustCommandHandler(e2e_store)
    e2e_read = TrustReadModel(e2e_store, e2e_snap)
    e2e_mgr = SnapshotManager(e2e_store, e2e_snap, snapshot_interval=5)

    entity = "judy"
    # Phase 1: Build trust through multiple attestations
    for i in range(8):
        e2e_cmd.attest_trust(entity, f"attester_{i % 3}", 0.04, timestamp=float(i + 1))

    state_after_attestations = e2e_read.get_trust(entity)
    check("trust_built_above_initial",
          state_after_attestations.trust_score > 0.5,
          f"score={state_after_attestations.trust_score}")

    # Phase 2: Take snapshot
    snap = e2e_mgr.take_snapshot(entity)
    check("snapshot_taken_after_attestations", snap is not None)

    # Phase 3: Partial revocation
    e2e_cmd.revoke_trust(entity, "auditor", severity=0.3, timestamp=20.0)
    state_after_revoke = e2e_read.get_trust(entity)
    check("trust_reduced_after_partial_revoke",
          state_after_revoke.trust_score < state_after_attestations.trust_score,
          f"before={state_after_attestations.trust_score}, after={state_after_revoke.trust_score}")

    # Phase 4: Recovery via new attestations
    e2e_cmd.attest_trust(entity, "trusted_attester", 0.1, timestamp=30.0)
    e2e_cmd.attest_trust(entity, "trusted_attester", 0.1, timestamp=31.0)
    state_recovered = e2e_read.get_trust(entity)
    check("trust_recovers_after_new_attestations",
          state_recovered.trust_score > state_after_revoke.trust_score)

    # Phase 5: Temporal query at time of peak trust (before revocation)
    state_at_peak = e2e_read.get_trust_at_time(entity, at_time=15.0)
    check("temporal_query_at_peak_higher_than_revoked",
          state_at_peak.trust_score > state_after_revoke.trust_score)

    # Phase 6: Event store consistency
    total_events = e2e_store.total_events()
    check("total_events_correct", total_events == 11,
          f"total={total_events}")
    check("entity_version_correct", e2e_store.entity_version(entity) == 11)

    # Verify full projection vs snapshot+replay match
    full_proj = TrustProjection.project(e2e_store.get_events_for_entity(entity))
    snap_replay = e2e_mgr.replay_from_snapshot(entity)
    check("full_vs_snapshot_replay_consistent",
          abs(full_proj.trust_score - snap_replay.trust_score) < 1e-9,
          f"full={full_proj.trust_score}, snap={snap_replay.trust_score}")

    # Summary
    total = passed + failed
    print(f"\n{'=' * 70}")
    print(f"Trust Event Sourcing: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  {failed} checks FAILED")
    else:
        print(f"  All {total} checks passed")
    return passed, failed


if __name__ == "__main__":
    passed, failed = run_checks()
    exit(0 if failed == 0 else 1)
