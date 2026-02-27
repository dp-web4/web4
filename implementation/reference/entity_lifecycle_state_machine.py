#!/usr/bin/env python3
"""
Entity Lifecycle State Machine — Formal FSM for Web4 Entity Lifecycle

Comprehensive state machine covering all entity lifecycle dimensions:
  1. LCT Lifecycle: GENESIS → ACTIVE → ROTATING → SUPERSEDED/REVOKED
  2. Society Lifecycle: GENESIS → BOOTSTRAP → OPERATIONAL(8 metabolic) → DISSOLVED
  3. Role Lifecycle: UNASSIGNED → ASSIGNED → ACTIVE → INACTIVE/REVOKED
  4. Pairing Lifecycle: UNPAIRED → NEGOTIATING → PAIRED → ACTIVE → CLOSED/REVOKED
  5. ATP Account: CREATED → FUNDED → ACTIVE → DEPLETED/CLOSED
  6. Key Rotation: PENDING → ACTIVE → OVERLAPPING → EXPIRED/REVOKED
  7. Witness Attestation: OBSERVING → ATTESTING → ATTESTED → VERIFIED/EXPIRED

Each FSM enforces:
  - Valid transitions only (invalid → raise TransitionError)
  - Guard conditions on transitions
  - Invariants checked after each transition
  - Event history with timestamps

Session: Legion Autonomous 2026-02-27 (Session 11, Track 1)
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional


# ═══════════════════════════════════════════════════════════════
# FSM FRAMEWORK
# ═══════════════════════════════════════════════════════════════

class TransitionError(Exception):
    """Invalid state transition."""
    pass


@dataclass
class Transition:
    """A valid state transition with optional guard."""
    from_state: str
    to_state: str
    event: str
    guard: Optional[Callable] = None  # Returns True if transition allowed
    description: str = ""


@dataclass
class StateEvent:
    """Record of a state transition."""
    from_state: str
    to_state: str
    event: str
    timestamp: str
    metadata: dict = field(default_factory=dict)


class StateMachine:
    """Generic finite state machine with guards, history, and invariants."""

    def __init__(self, name: str, initial_state: str,
                 transitions: list[Transition],
                 invariants: list[Callable] = None):
        self.name = name
        self.state = initial_state
        self.transitions = transitions
        self.invariants = invariants or []
        self.history: list[StateEvent] = []
        self.context: dict[str, Any] = {}

        # Build transition map: (from_state, event) → [Transition]
        self._map: dict[tuple[str, str], list[Transition]] = {}
        for t in transitions:
            key = (t.from_state, t.event)
            if key not in self._map:
                self._map[key] = []
            self._map[key].append(t)

    @property
    def valid_events(self) -> list[str]:
        """Events valid from current state."""
        return list(set(
            event for (state, event) in self._map
            if state == self.state
        ))

    @property
    def all_states(self) -> set[str]:
        states = {t.from_state for t in self.transitions}
        states.update(t.to_state for t in self.transitions)
        return states

    def can_transition(self, event: str) -> bool:
        """Check if event is valid from current state."""
        key = (self.state, event)
        if key not in self._map:
            return False
        for t in self._map[key]:
            if t.guard is None or t.guard(self.context):
                return True
        return False

    def transition(self, event: str, metadata: dict = None) -> str:
        """Execute a state transition."""
        key = (self.state, event)
        if key not in self._map:
            raise TransitionError(
                f"{self.name}: No transition from '{self.state}' on event '{event}'. "
                f"Valid events: {self.valid_events}"
            )

        # Find first transition where guard passes
        for t in self._map[key]:
            if t.guard is None or t.guard(self.context):
                old_state = self.state
                self.state = t.to_state

                self.history.append(StateEvent(
                    from_state=old_state,
                    to_state=t.to_state,
                    event=event,
                    timestamp=datetime.utcnow().isoformat(),
                    metadata=metadata or {}
                ))

                # Check invariants
                for inv in self.invariants:
                    if not inv(self):
                        # Rollback
                        self.state = old_state
                        self.history.pop()
                        raise TransitionError(
                            f"{self.name}: Invariant violated after "
                            f"'{old_state}' → '{t.to_state}' on '{event}'"
                        )

                return self.state

        raise TransitionError(
            f"{self.name}: Guard conditions not met for "
            f"'{self.state}' on event '{event}'"
        )


# ═══════════════════════════════════════════════════════════════
# 1. LCT LIFECYCLE FSM
# ═══════════════════════════════════════════════════════════════

def create_lct_fsm(lct_id: str = "lct:web4:ai:agent") -> StateMachine:
    """Create the LCT lifecycle state machine."""
    transitions = [
        Transition("GENESIS", "ACTIVE", "birth_witnessed",
                   description="Birth certificate signed by ≥3 witnesses"),
        Transition("ACTIVE", "ROTATING", "rotation_initiated",
                   description="Key rotation started, overlap window opens"),
        Transition("ACTIVE", "SUSPENDED", "suspend",
                   description="Temporarily disabled by authority"),
        Transition("ACTIVE", "REVOKED", "revoke",
                   description="Permanently terminated"),
        Transition("ROTATING", "ACTIVE", "rotation_complete",
                   description="New key operational, old key superseded"),
        Transition("ROTATING", "REVOKED", "revoke",
                   description="Revoked during rotation (compromise)"),
        Transition("SUSPENDED", "ACTIVE", "reinstate",
                   description="Suspension lifted"),
        Transition("SUSPENDED", "REVOKED", "revoke",
                   description="Terminated while suspended"),
    ]

    def no_orphan_invariant(fsm: StateMachine) -> bool:
        """Entity must have at least one witness in MRH."""
        if fsm.state == "GENESIS":
            return True
        return fsm.context.get("witness_count", 0) >= 1

    fsm = StateMachine(f"LCT({lct_id})", "GENESIS", transitions,
                        invariants=[no_orphan_invariant])
    fsm.context["lct_id"] = lct_id
    fsm.context["witness_count"] = 3  # Default: 3 birth witnesses
    return fsm


# ═══════════════════════════════════════════════════════════════
# 2. SOCIETY LIFECYCLE FSM
# ═══════════════════════════════════════════════════════════════

def create_society_fsm(society_id: str = "soc:web4:governance") -> StateMachine:
    """Create the society lifecycle state machine with metabolic states."""
    transitions = [
        # Phase transitions
        Transition("GENESIS", "BOOTSTRAP", "laws_ratified",
                   description="Initial laws approved by founders"),
        Transition("BOOTSTRAP", "ACTIVE", "quorum_reached",
                   description="Minimum citizens onboarded"),

        # Metabolic transitions from ACTIVE
        Transition("ACTIVE", "REST", "idle_1h",
                   description="No transactions for 1 hour"),
        Transition("ACTIVE", "TORPOR", "atp_critical",
                   lambda ctx: ctx.get("atp_level", 100) < 10,
                   "ATP below 10%"),
        Transition("ACTIVE", "DREAMING", "maintenance_window",
                   description="Scheduled maintenance/consolidation"),
        Transition("ACTIVE", "MOLTING", "governance_change",
                   description="Governance structure renewal"),
        Transition("ACTIVE", "ESTIVATION", "threat_detected",
                   description="Hostile environment detected"),
        Transition("ACTIVE", "SUSPENDED", "authority_suspend",
                   description="Authority suspends operations"),

        # Return to ACTIVE
        Transition("REST", "ACTIVE", "transaction_received",
                   description="Activity resumes"),
        Transition("REST", "SLEEP", "idle_6h",
                   description="No activity for 6 hours"),
        Transition("SLEEP", "ACTIVE", "wake_trigger",
                   description="Explicit wake signal"),
        Transition("SLEEP", "HIBERNATION", "idle_30d",
                   description="No activity for 30 days"),
        Transition("HIBERNATION", "ACTIVE", "external_wake",
                   description="External wake signal"),
        Transition("TORPOR", "ACTIVE", "energy_recharged",
                   lambda ctx: ctx.get("atp_level", 0) >= 20,
                   "ATP recharged above 20%"),
        Transition("TORPOR", "HIBERNATION", "grace_expired",
                   description="Torpor grace period exhausted"),
        Transition("ESTIVATION", "ACTIVE", "threat_resolved",
                   description="Hostile conditions cleared"),
        Transition("ESTIVATION", "HIBERNATION", "extended_threat",
                   description="Threat persists beyond capacity"),
        Transition("DREAMING", "ACTIVE", "consolidation_complete",
                   description="Maintenance/consolidation done"),
        Transition("MOLTING", "ACTIVE", "renewal_complete",
                   description="Governance renewal finalized"),

        # Suspension and dissolution
        Transition("SUSPENDED", "ACTIVE", "reinstate",
                   description="Suspension lifted"),
        Transition("SUSPENDED", "DISSOLVED", "dissolve",
                   description="Society permanently dissolved"),

        # Direct dissolution from dormant states
        Transition("HIBERNATION", "DISSOLVED", "dissolve",
                   description="Dissolved from hibernation"),
    ]

    def phase_ordering(fsm: StateMachine) -> bool:
        """GENESIS → BOOTSTRAP → OPERATIONAL is irreversible."""
        if fsm.state in ("GENESIS", "BOOTSTRAP"):
            for event in fsm.history:
                if event.from_state in ("ACTIVE", "REST", "SLEEP", "HIBERNATION",
                                         "TORPOR", "ESTIVATION", "DREAMING", "MOLTING"):
                    return False  # Can't go back to early phases
        return True

    fsm = StateMachine(f"Society({society_id})", "GENESIS", transitions,
                        invariants=[phase_ordering])
    fsm.context["society_id"] = society_id
    fsm.context["atp_level"] = 100
    fsm.context["citizen_count"] = 0
    return fsm


# ═══════════════════════════════════════════════════════════════
# 3. ROLE LIFECYCLE FSM
# ═══════════════════════════════════════════════════════════════

def create_role_fsm(role_id: str = "role:analyst") -> StateMachine:
    transitions = [
        Transition("UNASSIGNED", "ASSIGNED", "agent_paired",
                   description="Agent paired with role"),
        Transition("ASSIGNED", "ACTIVE_PERFORMANCE", "first_action",
                   description="First R6 action executed"),
        Transition("ACTIVE_PERFORMANCE", "INACTIVE", "role_closed",
                   description="Agent departed, history preserved"),
        Transition("ACTIVE_PERFORMANCE", "REVOKED", "force_revoke",
                   description="Role forcibly terminated"),
        Transition("INACTIVE", "ASSIGNED", "agent_paired",
                   description="New agent takes the role"),
        Transition("ASSIGNED", "REVOKED", "force_revoke",
                   description="Role revoked before first action"),
    ]

    fsm = StateMachine(f"Role({role_id})", "UNASSIGNED", transitions)
    fsm.context["role_id"] = role_id
    fsm.context["agent_lct_id"] = ""
    fsm.context["actions_performed"] = 0
    return fsm


# ═══════════════════════════════════════════════════════════════
# 4. PAIRING LIFECYCLE FSM
# ═══════════════════════════════════════════════════════════════

def create_pairing_fsm(pair_id: str = "pair:001") -> StateMachine:
    transitions = [
        Transition("UNPAIRED", "NEGOTIATING", "handshake_initiated",
                   description="Pairing handshake started"),
        Transition("NEGOTIATING", "KEY_EXCHANGE", "terms_agreed",
                   description="Both parties agreed on terms"),
        Transition("NEGOTIATING", "UNPAIRED", "handshake_failed",
                   description="Negotiation failed"),
        Transition("KEY_EXCHANGE", "PAIRED", "keys_exchanged",
                   description="Symmetric keys established"),
        Transition("KEY_EXCHANGE", "UNPAIRED", "exchange_failed",
                   description="Key exchange failed"),
        Transition("PAIRED", "ACTIVE", "first_message",
                   description="First data/energy exchange"),
        Transition("ACTIVE", "CLOSED", "intentional_close",
                   description="Graceful termination"),
        Transition("ACTIVE", "REVOKED", "security_revoke",
                   description="Emergency security revocation"),
        Transition("PAIRED", "REVOKED", "security_revoke",
                   description="Revoked before first exchange"),
        Transition("PAIRED", "CLOSED", "intentional_close",
                   description="Closed before first exchange"),
    ]

    fsm = StateMachine(f"Pairing({pair_id})", "UNPAIRED", transitions)
    fsm.context["pair_id"] = pair_id
    return fsm


# ═══════════════════════════════════════════════════════════════
# 5. ATP ACCOUNT LIFECYCLE FSM
# ═══════════════════════════════════════════════════════════════

def create_atp_account_fsm(account_id: str = "atp:agent:001") -> StateMachine:
    transitions = [
        Transition("CREATED", "FUNDED", "initial_allocation",
                   description="Initial ATP allocated"),
        Transition("FUNDED", "ACTIVE", "first_deduction",
                   description="First ATP spent"),
        Transition("ACTIVE", "ACTIVE", "spend",
                   lambda ctx: ctx.get("balance", 0) > 0,
                   "Spend with positive balance"),
        Transition("ACTIVE", "DEPLETED", "limit_reached",
                   description="Daily spending limit exhausted"),
        Transition("DEPLETED", "ACTIVE", "daily_recharge",
                   description="New day recharge"),
        Transition("ACTIVE", "CLOSED", "close_account",
                   description="Account terminated normally"),
        Transition("ACTIVE", "SLASHED", "slash",
                   description="Penalty: balance zeroed"),
        Transition("FUNDED", "CLOSED", "close_account",
                   description="Closed before first use"),
        Transition("DEPLETED", "CLOSED", "close_account",
                   description="Closed while depleted"),
    ]

    fsm = StateMachine(f"ATP({account_id})", "CREATED", transitions)
    fsm.context["account_id"] = account_id
    fsm.context["balance"] = 0.0
    fsm.context["daily_spent"] = 0.0
    return fsm


# ═══════════════════════════════════════════════════════════════
# 6. KEY ROTATION LIFECYCLE FSM
# ═══════════════════════════════════════════════════════════════

def create_key_rotation_fsm(key_id: str = "key:ed25519:001") -> StateMachine:
    transitions = [
        Transition("PENDING", "ACTIVE", "activate",
                   description="Key activated for signing"),
        Transition("ACTIVE", "OVERLAPPING", "successor_activated",
                   description="New key activated, old enters overlap"),
        Transition("ACTIVE", "REVOKED", "compromise_detected",
                   description="Emergency revocation"),
        Transition("OVERLAPPING", "EXPIRED", "overlap_ended",
                   description="Overlap window closed"),
        Transition("OVERLAPPING", "REVOKED", "compromise_detected",
                   description="Compromised during overlap"),
    ]

    fsm = StateMachine(f"Key({key_id})", "PENDING", transitions)
    fsm.context["key_id"] = key_id
    fsm.context["can_sign"] = False
    fsm.context["can_verify"] = False
    return fsm


# ═══════════════════════════════════════════════════════════════
# 7. WITNESS ATTESTATION LIFECYCLE FSM
# ═══════════════════════════════════════════════════════════════

def create_witness_fsm(attestation_id: str = "wit:001") -> StateMachine:
    transitions = [
        Transition("OBSERVING", "ATTESTING", "begin_attestation",
                   description="Witness starts signing"),
        Transition("ATTESTING", "ATTESTED", "signature_complete",
                   description="Attestation signed"),
        Transition("ATTESTED", "VERIFIED", "verification_passed",
                   description="Third party verified signature"),
        Transition("ATTESTED", "EXPIRED", "freshness_exceeded",
                   description="Outside freshness window (>300s)"),
        Transition("ATTESTED", "REVOKED", "witness_revoke",
                   description="Witness revokes attestation"),
        Transition("VERIFIED", "EXPIRED", "freshness_exceeded",
                   description="Verified attestation expired"),
    ]

    fsm = StateMachine(f"Witness({attestation_id})", "OBSERVING", transitions)
    fsm.context["attestation_id"] = attestation_id
    return fsm


# ═══════════════════════════════════════════════════════════════
# INTEGRATED LIFECYCLE COORDINATOR
# ═══════════════════════════════════════════════════════════════

class EntityLifecycleCoordinator:
    """Coordinates multiple FSMs for a single entity's lifecycle.

    An entity has: LCT FSM, Role FSM, ATP FSM, Key FSM
    Events on one FSM can trigger events on others.
    """

    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        self.lct = create_lct_fsm(entity_id)
        self.role = create_role_fsm(f"role:{entity_id}")
        self.atp = create_atp_account_fsm(f"atp:{entity_id}")
        self.key = create_key_rotation_fsm(f"key:{entity_id}")
        self.event_log: list[dict] = []

    def birth(self, witness_count: int = 3):
        """Entity birth: activates LCT, creates key, allocates ATP."""
        self.lct.context["witness_count"] = witness_count
        self.lct.transition("birth_witnessed")
        self.key.transition("activate")
        self.atp.transition("initial_allocation", {"amount": 100.0})
        self.atp.context["balance"] = 100.0
        self._log("birth", f"Born with {witness_count} witnesses")

    def assign_role(self, agent_lct_id: str):
        """Assign an agent to this entity's role."""
        self.role.transition("agent_paired")
        self.role.context["agent_lct_id"] = agent_lct_id
        self._log("role_assigned", f"Agent {agent_lct_id} assigned")

    def perform_action(self, action_desc: str, atp_cost: float = 5.0):
        """Perform an R6 action (updates role, ATP)."""
        if self.role.state == "ASSIGNED":
            self.role.transition("first_action")

        if self.atp.state == "FUNDED":
            self.atp.transition("first_deduction")

        if self.atp.state == "ACTIVE" and self.atp.context["balance"] > 0:
            self.atp.context["balance"] -= atp_cost
            self.atp.context["daily_spent"] += atp_cost
            self.role.context["actions_performed"] += 1

        self._log("action", f"{action_desc} (cost: {atp_cost} ATP)")

    def rotate_key(self):
        """Initiate key rotation."""
        self.lct.transition("rotation_initiated")
        self.key.transition("successor_activated")
        self._log("key_rotation", "Key rotation initiated")

    def complete_rotation(self):
        """Complete key rotation."""
        self.lct.transition("rotation_complete")
        self.key.transition("overlap_ended")
        self._log("rotation_complete", "Key rotation finalized")

    def revoke(self, reason: str):
        """Revoke entity."""
        self.lct.transition("revoke")
        if self.role.state in ("ASSIGNED", "ACTIVE_PERFORMANCE"):
            self.role.transition("force_revoke")
        if self.atp.state in ("ACTIVE", "FUNDED", "DEPLETED"):
            self.atp.transition("close_account")
        self._log("revoked", reason)

    def _log(self, event: str, details: str):
        self.event_log.append({
            "event": event,
            "details": details,
            "states": {
                "lct": self.lct.state,
                "role": self.role.state,
                "atp": self.atp.state,
                "key": self.key.state,
            },
            "timestamp": datetime.utcnow().isoformat()
        })


# ═══════════════════════════════════════════════════════════════
# CHECKS
# ═══════════════════════════════════════════════════════════════

def run_checks():
    passed = 0
    failed = 0

    def check(condition: bool, description: str):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {description}")

    # ═══════════════════════════════════════════════════════════
    # SECTION 1: LCT LIFECYCLE
    # ═══════════════════════════════════════════════════════════

    print("Section 1: LCT Lifecycle")

    lct = create_lct_fsm("lct:web4:ai:test")
    check(lct.state == "GENESIS", "LCT starts in GENESIS")
    check(len(lct.all_states) == 5, f"LCT has {len(lct.all_states)} states")

    # Valid: GENESIS → ACTIVE
    lct.transition("birth_witnessed")
    check(lct.state == "ACTIVE", "GENESIS → ACTIVE on birth_witnessed")
    check(len(lct.history) == 1, "1 event in history")

    # Valid: ACTIVE → ROTATING
    lct.transition("rotation_initiated")
    check(lct.state == "ROTATING", "ACTIVE → ROTATING")

    # Valid: ROTATING → ACTIVE
    lct.transition("rotation_complete")
    check(lct.state == "ACTIVE", "ROTATING → ACTIVE on rotation_complete")

    # Valid: ACTIVE → SUSPENDED → ACTIVE
    lct.transition("suspend")
    check(lct.state == "SUSPENDED", "ACTIVE → SUSPENDED")
    lct.transition("reinstate")
    check(lct.state == "ACTIVE", "SUSPENDED → ACTIVE on reinstate")

    # Valid: ACTIVE → REVOKED
    lct.transition("revoke")
    check(lct.state == "REVOKED", "ACTIVE → REVOKED")

    # Invalid: REVOKED → anything
    try:
        lct.transition("reinstate")
        check(False, "REVOKED should not allow reinstate")
    except TransitionError:
        check(True, "REVOKED → reinstate raises TransitionError")

    # Invalid: GENESIS → ROTATING (must go through ACTIVE)
    lct2 = create_lct_fsm("lct:test:2")
    try:
        lct2.transition("rotation_initiated")
        check(False, "GENESIS should not allow rotation")
    except TransitionError:
        check(True, "GENESIS → rotation raises TransitionError")

    # Valid events from state
    lct3 = create_lct_fsm("lct:test:3")
    lct3.transition("birth_witnessed")
    valid = set(lct3.valid_events)
    check("rotation_initiated" in valid, "ACTIVE allows rotation_initiated")
    check("suspend" in valid, "ACTIVE allows suspend")
    check("revoke" in valid, "ACTIVE allows revoke")
    check("birth_witnessed" not in valid, "ACTIVE doesn't allow birth_witnessed")

    # Witness invariant
    lct4 = create_lct_fsm("lct:test:4")
    lct4.context["witness_count"] = 0
    try:
        lct4.transition("birth_witnessed")
        check(False, "Should fail with 0 witnesses")
    except TransitionError:
        check(True, "No-orphan invariant: 0 witnesses → blocked")

    # History tracking
    check(len(lct.history) == 6, f"LCT has {len(lct.history)} history events")
    check(lct.history[0].event == "birth_witnessed", "First event is birth")
    check(lct.history[-1].event == "revoke", "Last event is revoke")

    # ═══════════════════════════════════════════════════════════
    # SECTION 2: SOCIETY LIFECYCLE
    # ═══════════════════════════════════════════════════════════

    print("Section 2: Society Lifecycle")

    soc = create_society_fsm("soc:test")
    check(soc.state == "GENESIS", "Society starts in GENESIS")

    # Phase transitions
    soc.transition("laws_ratified")
    check(soc.state == "BOOTSTRAP", "GENESIS → BOOTSTRAP")

    soc.transition("quorum_reached")
    check(soc.state == "ACTIVE", "BOOTSTRAP → ACTIVE")

    # Metabolic transitions
    soc.transition("idle_1h")
    check(soc.state == "REST", "ACTIVE → REST on idle")

    soc.transition("transaction_received")
    check(soc.state == "ACTIVE", "REST → ACTIVE on transaction")

    # Sleep chain
    soc.transition("idle_1h")
    soc.transition("idle_6h")
    check(soc.state == "SLEEP", "REST → SLEEP on extended idle")

    soc.transition("idle_30d")
    check(soc.state == "HIBERNATION", "SLEEP → HIBERNATION on 30d")

    soc.transition("external_wake")
    check(soc.state == "ACTIVE", "HIBERNATION → ACTIVE on wake")

    # Torpor (ATP critical)
    soc.context["atp_level"] = 5
    soc.transition("atp_critical")
    check(soc.state == "TORPOR", "ACTIVE → TORPOR on ATP critical")

    # Can't leave torpor without enough ATP
    try:
        soc.transition("energy_recharged")
        check(False, "Should fail: ATP still < 20")
    except TransitionError:
        check(True, "Torpor guard: can't leave with ATP < 20")

    soc.context["atp_level"] = 25
    soc.transition("energy_recharged")
    check(soc.state == "ACTIVE", "TORPOR → ACTIVE with ATP ≥ 20")

    # Dreaming
    soc.transition("maintenance_window")
    check(soc.state == "DREAMING", "ACTIVE → DREAMING")
    soc.transition("consolidation_complete")
    check(soc.state == "ACTIVE", "DREAMING → ACTIVE")

    # Molting
    soc.transition("governance_change")
    check(soc.state == "MOLTING", "ACTIVE → MOLTING")
    soc.transition("renewal_complete")
    check(soc.state == "ACTIVE", "MOLTING → ACTIVE")

    # Estivation
    soc.transition("threat_detected")
    check(soc.state == "ESTIVATION", "ACTIVE → ESTIVATION")
    soc.transition("threat_resolved")
    check(soc.state == "ACTIVE", "ESTIVATION → ACTIVE")

    # Suspension and dissolution
    soc.transition("authority_suspend")
    check(soc.state == "SUSPENDED", "ACTIVE → SUSPENDED")
    soc.transition("dissolve")
    check(soc.state == "DISSOLVED", "SUSPENDED → DISSOLVED")

    # Invalid: can't go back from DISSOLVED
    try:
        soc.transition("reinstate")
        check(False, "DISSOLVED should not allow transitions")
    except TransitionError:
        check(True, "DISSOLVED is terminal")

    # ═══════════════════════════════════════════════════════════
    # SECTION 3: ROLE LIFECYCLE
    # ═══════════════════════════════════════════════════════════

    print("Section 3: Role Lifecycle")

    role = create_role_fsm("role:analyst")
    check(role.state == "UNASSIGNED", "Role starts UNASSIGNED")

    role.transition("agent_paired")
    check(role.state == "ASSIGNED", "UNASSIGNED → ASSIGNED")

    role.transition("first_action")
    check(role.state == "ACTIVE_PERFORMANCE", "ASSIGNED → ACTIVE_PERFORMANCE")

    role.transition("role_closed")
    check(role.state == "INACTIVE", "ACTIVE_PERFORMANCE → INACTIVE")

    # Re-assignment
    role.transition("agent_paired")
    check(role.state == "ASSIGNED", "INACTIVE → ASSIGNED (re-assignment)")

    role.transition("first_action")
    role.transition("force_revoke")
    check(role.state == "REVOKED", "ACTIVE_PERFORMANCE → REVOKED")

    # Terminal
    try:
        role.transition("agent_paired")
        check(False, "REVOKED should be terminal")
    except TransitionError:
        check(True, "REVOKED role is terminal")

    # ═══════════════════════════════════════════════════════════
    # SECTION 4: PAIRING LIFECYCLE
    # ═══════════════════════════════════════════════════════════

    print("Section 4: Pairing Lifecycle")

    pair = create_pairing_fsm("pair:alice-bob")
    check(pair.state == "UNPAIRED", "Pairing starts UNPAIRED")

    # Happy path
    pair.transition("handshake_initiated")
    check(pair.state == "NEGOTIATING", "UNPAIRED → NEGOTIATING")

    pair.transition("terms_agreed")
    check(pair.state == "KEY_EXCHANGE", "NEGOTIATING → KEY_EXCHANGE")

    pair.transition("keys_exchanged")
    check(pair.state == "PAIRED", "KEY_EXCHANGE → PAIRED")

    pair.transition("first_message")
    check(pair.state == "ACTIVE", "PAIRED → ACTIVE")

    pair.transition("intentional_close")
    check(pair.state == "CLOSED", "ACTIVE → CLOSED")

    # Failed negotiation
    pair2 = create_pairing_fsm("pair:fail")
    pair2.transition("handshake_initiated")
    pair2.transition("handshake_failed")
    check(pair2.state == "UNPAIRED", "Failed negotiation → UNPAIRED")

    # Security revocation
    pair3 = create_pairing_fsm("pair:revoke")
    pair3.transition("handshake_initiated")
    pair3.transition("terms_agreed")
    pair3.transition("keys_exchanged")
    pair3.transition("first_message")
    pair3.transition("security_revoke")
    check(pair3.state == "REVOKED", "ACTIVE → REVOKED on security event")

    # ═══════════════════════════════════════════════════════════
    # SECTION 5: ATP ACCOUNT LIFECYCLE
    # ═══════════════════════════════════════════════════════════

    print("Section 5: ATP Account Lifecycle")

    atp = create_atp_account_fsm("atp:agent")
    check(atp.state == "CREATED", "ATP starts CREATED")

    atp.transition("initial_allocation")
    check(atp.state == "FUNDED", "CREATED → FUNDED")

    atp.transition("first_deduction")
    check(atp.state == "ACTIVE", "FUNDED → ACTIVE")

    # Self-transition with balance
    atp.context["balance"] = 100.0
    atp.transition("spend")
    check(atp.state == "ACTIVE", "ACTIVE → ACTIVE on spend")

    # Spend with 0 balance fails guard
    atp.context["balance"] = 0
    try:
        atp.transition("spend")
        check(False, "Should fail: 0 balance")
    except TransitionError:
        check(True, "Spend guard: can't spend with 0 balance")

    # Depletion
    atp.transition("limit_reached")
    check(atp.state == "DEPLETED", "ACTIVE → DEPLETED")

    atp.transition("daily_recharge")
    check(atp.state == "ACTIVE", "DEPLETED → ACTIVE on recharge")

    # Slashing
    atp.transition("slash")
    check(atp.state == "SLASHED", "ACTIVE → SLASHED")

    # Terminal
    try:
        atp.transition("daily_recharge")
        check(False, "SLASHED should be terminal")
    except TransitionError:
        check(True, "SLASHED is terminal")

    # ═══════════════════════════════════════════════════════════
    # SECTION 6: KEY ROTATION LIFECYCLE
    # ═══════════════════════════════════════════════════════════

    print("Section 6: Key Rotation Lifecycle")

    key = create_key_rotation_fsm("key:ed25519:001")
    check(key.state == "PENDING", "Key starts PENDING")

    key.transition("activate")
    check(key.state == "ACTIVE", "PENDING → ACTIVE")

    key.transition("successor_activated")
    check(key.state == "OVERLAPPING", "ACTIVE → OVERLAPPING")

    key.transition("overlap_ended")
    check(key.state == "EXPIRED", "OVERLAPPING → EXPIRED")

    # Emergency revocation from ACTIVE
    key2 = create_key_rotation_fsm("key:002")
    key2.transition("activate")
    key2.transition("compromise_detected")
    check(key2.state == "REVOKED", "ACTIVE → REVOKED on compromise")

    # Revocation from OVERLAPPING
    key3 = create_key_rotation_fsm("key:003")
    key3.transition("activate")
    key3.transition("successor_activated")
    key3.transition("compromise_detected")
    check(key3.state == "REVOKED", "OVERLAPPING → REVOKED on compromise")

    # ═══════════════════════════════════════════════════════════
    # SECTION 7: WITNESS ATTESTATION LIFECYCLE
    # ═══════════════════════════════════════════════════════════

    print("Section 7: Witness Attestation Lifecycle")

    wit = create_witness_fsm("wit:time:001")
    check(wit.state == "OBSERVING", "Witness starts OBSERVING")

    wit.transition("begin_attestation")
    check(wit.state == "ATTESTING", "OBSERVING → ATTESTING")

    wit.transition("signature_complete")
    check(wit.state == "ATTESTED", "ATTESTING → ATTESTED")

    wit.transition("verification_passed")
    check(wit.state == "VERIFIED", "ATTESTED → VERIFIED")

    # Expiration from VERIFIED
    wit.transition("freshness_exceeded")
    check(wit.state == "EXPIRED", "VERIFIED → EXPIRED")

    # Revocation path
    wit2 = create_witness_fsm("wit:002")
    wit2.transition("begin_attestation")
    wit2.transition("signature_complete")
    wit2.transition("witness_revoke")
    check(wit2.state == "REVOKED", "ATTESTED → REVOKED")

    # Expiration from ATTESTED
    wit3 = create_witness_fsm("wit:003")
    wit3.transition("begin_attestation")
    wit3.transition("signature_complete")
    wit3.transition("freshness_exceeded")
    check(wit3.state == "EXPIRED", "ATTESTED → EXPIRED")

    # ═══════════════════════════════════════════════════════════
    # SECTION 8: INTEGRATED LIFECYCLE COORDINATOR
    # ═══════════════════════════════════════════════════════════

    print("Section 8: Integrated Lifecycle Coordinator")

    entity = EntityLifecycleCoordinator("lct:web4:ai:coordinator-test")

    # Birth
    entity.birth(witness_count=5)
    check(entity.lct.state == "ACTIVE", "After birth: LCT = ACTIVE")
    check(entity.key.state == "ACTIVE", "After birth: Key = ACTIVE")
    check(entity.atp.state == "FUNDED", "After birth: ATP = FUNDED")
    check(entity.atp.context["balance"] == 100.0, "ATP balance = 100")

    # Assign role
    entity.assign_role("lct:web4:human:alice")
    check(entity.role.state == "ASSIGNED", "Role assigned")

    # Perform actions
    entity.perform_action("analyze_data", atp_cost=10.0)
    check(entity.role.state == "ACTIVE_PERFORMANCE", "Role → ACTIVE_PERFORMANCE")
    check(entity.atp.state == "ACTIVE", "ATP → ACTIVE")
    check(entity.atp.context["balance"] == 90.0, "ATP = 90 after 10 cost")

    entity.perform_action("generate_report", atp_cost=15.0)
    check(entity.atp.context["balance"] == 75.0, "ATP = 75 after 15 cost")
    check(entity.role.context["actions_performed"] == 2, "2 actions performed")

    # Key rotation
    entity.rotate_key()
    check(entity.lct.state == "ROTATING", "LCT → ROTATING")
    check(entity.key.state == "OVERLAPPING", "Key → OVERLAPPING")

    entity.complete_rotation()
    check(entity.lct.state == "ACTIVE", "LCT → ACTIVE (rotation complete)")
    check(entity.key.state == "EXPIRED", "Old key → EXPIRED")

    # Event log
    check(len(entity.event_log) >= 5,
          f"Event log has {len(entity.event_log)} entries (≥5)")
    check(entity.event_log[0]["event"] == "birth", "First event = birth")

    # Revocation
    entity.revoke("Policy violation detected")
    check(entity.lct.state == "REVOKED", "After revoke: LCT = REVOKED")
    check(entity.role.state == "REVOKED", "After revoke: Role = REVOKED")
    check(entity.atp.state == "CLOSED", "After revoke: ATP = CLOSED")

    # ═══════════════════════════════════════════════════════════
    # SECTION 9: FSM FRAMEWORK PROPERTIES
    # ═══════════════════════════════════════════════════════════

    print("Section 9: FSM Framework Properties")

    # All states reachable
    fsm = create_lct_fsm("lct:test:reach")
    check(len(fsm.all_states) == 5,
          f"LCT has exactly 5 states: {fsm.all_states}")

    soc_fsm = create_society_fsm("soc:test:reach")
    check(len(soc_fsm.all_states) >= 11,
          f"Society has ≥11 states: {len(soc_fsm.all_states)}")

    # Metadata in transitions
    fsm2 = create_lct_fsm("lct:meta")
    fsm2.transition("birth_witnessed", {"witness_count": 3})
    check(fsm2.history[0].metadata.get("witness_count") == 3,
          "Metadata preserved in transition")

    # can_transition check
    fsm3 = create_lct_fsm("lct:can")
    check(fsm3.can_transition("birth_witnessed"), "GENESIS can birth_witnessed")
    check(not fsm3.can_transition("revoke"), "GENESIS cannot revoke")
    check(not fsm3.can_transition("nonexistent"), "No nonexistent event")

    # Transition descriptions
    desc_found = False
    for t in fsm.transitions:
        if t.description:
            desc_found = True
            break
    check(desc_found, "Transitions have descriptions")

    # ─── Summary ──────────────────────────────────────────────

    total = passed + failed
    print(f"\n{'='*60}")
    print(f"Entity Lifecycle State Machine: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  {failed} FAILED")
    else:
        print("  All checks passed!")
    print(f"{'='*60}")

    print(f"\nFSMs tested: LCT(5), Society(11+), Role(5), Pairing(7), "
          f"ATP(6), Key(5), Witness(6), Coordinator")

    return passed, failed


if __name__ == "__main__":
    run_checks()
