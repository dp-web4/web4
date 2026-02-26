#!/usr/bin/env python3
"""
Web4 Society Specification — Reference Implementation
=======================================================
Implements the foundational society framework from:
  web4-standard/core-spec/SOCIETY_SPECIFICATION.md (392 lines)

Covers ALL 7 sections:
  §1 Definition — Core definition, minimum requirements, formation process
  §2 Citizenship — Multi-society, rights/obligations, lifecycle, record structure
  §3 Fractal Nature — Society fractals, inheritance, recursive citizenship, economic fractals
  §4 Ledger Types — Confined/Witnessed/Participatory, recording requirements, amendments
  §5 Implementation — Bootstrap, scaling patterns, trust building
  §6 Examples — Dev team, regional trade, global Web4
  §7 Future — Cross-society protocols, mergers/splits, dispute resolution
"""

from __future__ import annotations
import hashlib
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

# ══════════════════════════════════════════════════════════════
# §1 — Definition of Society
# ══════════════════════════════════════════════════════════════

@dataclass
class Law:
    """A society law — codified rule governing behavior."""
    law_id: str
    description: str
    amendment_mechanism: str = "consensus"
    enforcement: str = "voluntary"

    def is_valid(self) -> bool:
        return bool(self.law_id and self.description and self.amendment_mechanism)


class LedgerEventType(Enum):
    CITIZENSHIP = "citizenship_event"
    LAW_CHANGE = "law_change"
    ECONOMIC = "economic_event"
    WITNESS = "witness_attestation"


@dataclass
class LedgerEntry:
    """An immutable ledger entry."""
    entry_id: str
    event_type: LedgerEventType
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    status: str = "active"  # active, superseded
    superseded_by: Optional[str] = None


class LedgerType(Enum):
    CONFINED = "confined"         # Citizens only
    WITNESSED = "witnessed"       # Citizens + external witness
    PARTICIPATORY = "participatory"  # Participates in parent ledger


@dataclass
class Ledger:
    """Society ledger — immutable record of events."""
    ledger_type: LedgerType
    entries: List[LedgerEntry] = field(default_factory=list)
    validators: List[str] = field(default_factory=list)  # LCT IDs of validators
    parent_ledger_id: Optional[str] = None  # For participatory type

    def record(self, event_type: LedgerEventType, data: Dict[str, Any]) -> LedgerEntry:
        """Record an event (§4.2.1)."""
        entry = LedgerEntry(
            entry_id=f"entry-{uuid.uuid4().hex[:8]}",
            event_type=event_type,
            data=data,
        )
        self.entries.append(entry)
        return entry

    def amend(self, original_id: str, amendment_type: str,
              new_data: Dict[str, Any], reason: str, law_authorization: str) -> Optional[LedgerEntry]:
        """Amend an entry while preserving original (§4.2.2)."""
        original = next((e for e in self.entries if e.entry_id == original_id), None)
        if not original:
            return None
        if original.status == "superseded":
            return None  # Can't amend already-superseded entry

        amendment = LedgerEntry(
            entry_id=f"amendment-{uuid.uuid4().hex[:8]}",
            event_type=original.event_type,
            data={
                "amends": original_id,
                "amendment_type": amendment_type,
                "new_data": new_data,
                "reason": reason,
                "law_authorization": law_authorization,
            },
        )
        original.status = "superseded"
        original.superseded_by = amendment.entry_id
        self.entries.append(amendment)
        return amendment

    def query_active(self, event_type: Optional[LedgerEventType] = None) -> List[LedgerEntry]:
        """Query active (non-superseded) entries."""
        results = [e for e in self.entries if e.status == "active"]
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        return results

    def event_count(self) -> int:
        return len(self.entries)


@dataclass
class Treasury:
    """Society-managed ATP/ADP token pool (§1.2.3)."""
    atp_balance: float = 0.0
    adp_balance: float = 0.0
    allocation_law: str = ""

    def allocate_atp(self, amount: float, recipient: str) -> bool:
        if amount <= self.atp_balance:
            self.atp_balance -= amount
            return True
        return False

    def receive_atp(self, amount: float):
        self.atp_balance += amount


# ══════════════════════════════════════════════════════════════
# §2 — Citizenship
# ══════════════════════════════════════════════════════════════

class CitizenshipStatus(Enum):
    PENDING = "pending"
    PROVISIONAL = "provisional"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    REJECTED = "rejected"


@dataclass
class CitizenshipRecord:
    """Citizenship record structure (§2.4)."""
    entity_lct: str
    society_lct: str
    status: CitizenshipStatus = CitizenshipStatus.PENDING
    witness_lcts: List[str] = field(default_factory=list)
    rights: List[str] = field(default_factory=list)
    obligations: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def is_active(self) -> bool:
        return self.status == CitizenshipStatus.ACTIVE

    def can_vote(self) -> bool:
        return self.is_active() and "vote" in self.rights


# ══════════════════════════════════════════════════════════════
# §1.3 / §5 — Society Formation and Lifecycle
# ══════════════════════════════════════════════════════════════

class FormationPhase(Enum):
    PRE_GENESIS = "pre_genesis"
    GENESIS = "genesis"
    BOOTSTRAP = "bootstrap"
    OPERATIONAL = "operational"


@dataclass
class Society:
    """A Web4 Society — self-governing collective of LCT-bearing entities (§1.1)."""
    society_lct: str
    name: str
    laws: List[Law] = field(default_factory=list)
    ledger: Ledger = field(default_factory=lambda: Ledger(LedgerType.CONFINED))
    treasury: Treasury = field(default_factory=Treasury)
    citizens: Dict[str, CitizenshipRecord] = field(default_factory=dict)
    phase: FormationPhase = FormationPhase.PRE_GENESIS
    parent_society: Optional[str] = None  # For fractal nesting
    child_societies: List[str] = field(default_factory=list)
    t3_scores: Dict[str, float] = field(default_factory=lambda: {
        "talent": 0.5, "training": 0.5, "temperament": 0.5,
    })

    # --- §1.3 Formation ---

    def genesis(self, founders: List[str], initial_law: Law) -> bool:
        """Genesis Event (§1.3 step 1)."""
        if self.phase != FormationPhase.PRE_GENESIS:
            return False
        if len(founders) < 2:
            return False  # §5.1: minimum 2 entities
        if not initial_law.is_valid():
            return False

        self.laws.append(initial_law)
        self.phase = FormationPhase.GENESIS

        # Record genesis on ledger
        self.ledger.record(LedgerEventType.LAW_CHANGE, {
            "action": "ratify",
            "law_id": initial_law.law_id,
            "description": initial_law.description,
        })

        return True

    def bootstrap(self, founders: List[str], initial_atp: float = 0.0) -> bool:
        """Bootstrap Phase (§1.3 step 2)."""
        if self.phase != FormationPhase.GENESIS:
            return False

        # Record initial citizens
        for founder_lct in founders:
            record = CitizenshipRecord(
                entity_lct=founder_lct,
                society_lct=self.society_lct,
                status=CitizenshipStatus.ACTIVE,
                rights=["vote", "propose", "allocate"],
                obligations=["witness", "contribute"],
                witness_lcts=founders[:],  # all founders witness each other
            )
            self.citizens[founder_lct] = record
            self.ledger.record(LedgerEventType.CITIZENSHIP, {
                "event_type": "citizenship_granted",
                "entity_lct": founder_lct,
                "status": "active",
            })

        # Treasury
        self.treasury.atp_balance = initial_atp
        self.phase = FormationPhase.BOOTSTRAP
        return True

    def go_operational(self) -> bool:
        """Transition to operational phase (§1.3 step 3)."""
        if self.phase != FormationPhase.BOOTSTRAP:
            return False
        if not self.laws:
            return False
        if len(self.citizens) < 2:
            return False

        self.phase = FormationPhase.OPERATIONAL
        return True

    # --- §2 Citizenship ---

    def apply_citizenship(self, entity_lct: str) -> CitizenshipRecord:
        """Application → Review (§2.3)."""
        record = CitizenshipRecord(
            entity_lct=entity_lct,
            society_lct=self.society_lct,
        )
        self.citizens[entity_lct] = record
        return record

    def approve_citizenship(self, entity_lct: str, witnesses: List[str],
                            rights: List[str] = None, obligations: List[str] = None) -> bool:
        """Review → Acceptance (§2.3)."""
        record = self.citizens.get(entity_lct)
        if not record:
            return False
        if record.status not in (CitizenshipStatus.PENDING, CitizenshipStatus.PROVISIONAL):
            return False

        record.status = CitizenshipStatus.ACTIVE
        record.witness_lcts = witnesses
        record.rights = rights or ["vote", "propose"]
        record.obligations = obligations or ["witness"]

        self.ledger.record(LedgerEventType.CITIZENSHIP, {
            "event_type": "citizenship_granted",
            "entity_lct": entity_lct,
            "witnesses": witnesses,
            "rights": record.rights,
        })
        return True

    def suspend_citizen(self, entity_lct: str, reason: str) -> bool:
        """Active → Suspension (§2.3)."""
        record = self.citizens.get(entity_lct)
        if not record or record.status != CitizenshipStatus.ACTIVE:
            return False
        record.status = CitizenshipStatus.SUSPENDED
        self.ledger.record(LedgerEventType.CITIZENSHIP, {
            "action": "suspend",
            "entity_lct": entity_lct,
            "reason": reason,
        })
        return True

    def reinstate_citizen(self, entity_lct: str) -> bool:
        """Suspension → Reinstatement (§2.3)."""
        record = self.citizens.get(entity_lct)
        if not record or record.status != CitizenshipStatus.SUSPENDED:
            return False
        record.status = CitizenshipStatus.ACTIVE
        self.ledger.record(LedgerEventType.CITIZENSHIP, {
            "action": "reinstate",
            "entity_lct": entity_lct,
        })
        return True

    def terminate_citizen(self, entity_lct: str, reason: str) -> bool:
        """Suspend/Active → Termination (§2.3)."""
        record = self.citizens.get(entity_lct)
        if not record or record.status not in (CitizenshipStatus.ACTIVE, CitizenshipStatus.SUSPENDED):
            return False
        record.status = CitizenshipStatus.TERMINATED
        self.ledger.record(LedgerEventType.CITIZENSHIP, {
            "action": "terminate",
            "entity_lct": entity_lct,
            "reason": reason,
        })
        return True

    def active_citizens(self) -> List[str]:
        return [lct for lct, r in self.citizens.items() if r.is_active()]

    def citizen_count(self) -> int:
        return len([r for r in self.citizens.values() if r.is_active()])

    # --- §3 Fractal Nature ---

    def add_child_society(self, child_lct: str):
        """Register a child society (§3.1)."""
        self.child_societies.append(child_lct)

    def has_indirect_relationship(self, entity_lct: str, child_society: "Society") -> bool:
        """Check recursive citizenship (§3.2.2)."""
        # If entity is citizen of child, and child is citizen of self
        return (entity_lct in child_society.citizens and
                child_society.society_lct in self.citizens)

    # --- §5.2 Scaling ---

    def upgrade_ledger(self, new_type: LedgerType, **kwargs):
        """Scale ledger type as society grows (§5.2)."""
        self.ledger.ledger_type = new_type
        if new_type == LedgerType.PARTICIPATORY and "parent_ledger_id" in kwargs:
            self.ledger.parent_ledger_id = kwargs["parent_ledger_id"]

    # --- §5.3 Trust Building ---

    def calculate_t3(self) -> Dict[str, float]:
        """Calculate society-level T3 from citizen behavior (§5.3)."""
        if not self.citizens:
            return self.t3_scores

        active = [r for r in self.citizens.values() if r.is_active()]
        if not active:
            return self.t3_scores

        # Compliance rate as proxy for temperament
        total = len(self.citizens)
        active_count = len(active)
        compliance_rate = active_count / total if total > 0 else 0

        # Economic efficiency from treasury
        economic_score = min(1.0, self.treasury.atp_balance / 100) if self.treasury.atp_balance >= 0 else 0

        self.t3_scores["temperament"] = compliance_rate
        self.t3_scores["training"] = min(1.0, len(self.laws) * 0.1 + 0.3)
        self.t3_scores["talent"] = economic_score

        return self.t3_scores

    # --- §4.1 Law Changes ---

    def propose_law(self, law: Law, proposer: str) -> bool:
        """Propose a new law (§4.2.1)."""
        record = self.citizens.get(proposer)
        if not record or not record.is_active():
            return False
        if "propose" not in record.rights:
            return False

        self.ledger.record(LedgerEventType.LAW_CHANGE, {
            "action": "propose",
            "law_id": law.law_id,
            "description": law.description,
            "proposed_by": proposer,
        })
        return True

    def ratify_law(self, law: Law, voters: List[str]) -> bool:
        """Ratify a proposed law (§4.2.1)."""
        # Check quorum (simple majority of active citizens)
        active = self.active_citizens()
        voter_set = set(voters) & set(active)
        if len(voter_set) <= len(active) / 2:
            return False

        self.laws.append(law)
        self.ledger.record(LedgerEventType.LAW_CHANGE, {
            "action": "ratify",
            "law_id": law.law_id,
            "voting_record": {"for": list(voter_set), "total": len(active)},
        })
        return True


# ══════════════════════════════════════════════════════════════
# §3 — Fractal Society System
# ══════════════════════════════════════════════════════════════

class FractalSocietySystem:
    """Manages fractal hierarchy of societies (§3)."""

    def __init__(self):
        self.societies: Dict[str, Society] = {}

    def register(self, society: Society):
        self.societies[society.society_lct] = society

    def create_child(self, parent_lct: str, child: Society) -> bool:
        """Create child society with parent relationship (§3.1)."""
        parent = self.societies.get(parent_lct)
        if not parent:
            return False

        child.parent_society = parent_lct
        parent.add_child_society(child.society_lct)
        self.register(child)
        return True

    def get_citizenship_tree(self, entity_lct: str) -> Dict[str, List[str]]:
        """Get complete fractal citizenship portfolio (§3.3)."""
        tree: Dict[str, List[str]] = {"direct": [], "indirect": []}

        for soc_lct, society in self.societies.items():
            if entity_lct in society.citizens and society.citizens[entity_lct].is_active():
                tree["direct"].append(soc_lct)
                # Check parent chain for indirect
                current = society.parent_society
                while current:
                    if current not in tree["indirect"]:
                        tree["indirect"].append(current)
                    parent = self.societies.get(current)
                    current = parent.parent_society if parent else None

        return tree

    def atp_flow(self, parent_lct: str, child_lct: str, amount: float) -> bool:
        """Economic fractal: parent allocates ATP to child (§3.2.3)."""
        parent = self.societies.get(parent_lct)
        child = self.societies.get(child_lct)
        if not parent or not child:
            return False
        if child.parent_society != parent_lct:
            return False
        if not parent.treasury.allocate_atp(amount, child_lct):
            return False

        child.treasury.receive_atp(amount)
        parent.ledger.record(LedgerEventType.ECONOMIC, {
            "action": "allocate",
            "amount": amount,
            "token_type": "ATP",
            "recipient_lct": child_lct,
            "purpose": "child_society_allocation",
        })
        return True


# ══════════════════════════════════════════════════════════════
# §6 — Society Examples
# ══════════════════════════════════════════════════════════════

def create_dev_team_example() -> Society:
    """Development Team Society (§6.1)."""
    soc = Society(
        society_lct="lct:society:web4dev",
        name="Web4 Dev Team",
    )
    soc.ledger = Ledger(LedgerType.CONFINED)
    founders = [f"lct:dev:{i}" for i in range(5)]
    soc.genesis(founders, Law("law-code-review", "All code requires review", "consensus"))
    soc.bootstrap(founders, initial_atp=500)
    soc.go_operational()
    return soc


def create_trade_society_example() -> Society:
    """Regional Trade Society (§6.2)."""
    soc = Society(
        society_lct="lct:society:regional-trade",
        name="Regional Trade Society",
    )
    soc.ledger = Ledger(LedgerType.WITNESSED, validators=["lct:auditor:ext1"])
    founders = ["lct:business:1", "lct:business:2", "lct:logistics:1"]
    soc.genesis(founders, Law("law-trade-standards", "Trade standards apply", "majority_vote"))
    soc.bootstrap(founders, initial_atp=10000)
    soc.go_operational()
    return soc


# ══════════════════════════════════════════════════════════════
# §7 — Future: Cross-Society Protocols
# ══════════════════════════════════════════════════════════════

@dataclass
class Treaty:
    """Cross-society protocol (§7.1)."""
    treaty_id: str
    society_a: str
    society_b: str
    terms: List[str]
    resource_sharing: bool = False
    reputation_portability: bool = False


@dataclass
class MergerProposal:
    """Society merger proposal (§7.2)."""
    source_society: str
    target_society: str
    asset_division: Dict[str, float] = field(default_factory=dict)  # percentage splits
    citizen_migration: bool = True


@dataclass
class DisputeResolution:
    """Inter-society dispute (§7.3)."""
    dispute_id: str
    parties: List[str]
    arbitrator: Optional[str] = None
    resolution: Optional[str] = None
    enforcement: str = "voluntary"


# ══════════════════════════════════════════════════════════════
# TESTS
# ══════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(label, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {label} {detail}")

    # ── T1: Society Definition (§1) ──
    print("T1: Society Definition (§1)")

    soc = Society(society_lct="lct:society:test", name="Test Society")
    check("T1.1 Pre-genesis phase", soc.phase == FormationPhase.PRE_GENESIS)
    check("T1.2 No laws initially", len(soc.laws) == 0)
    check("T1.3 Empty treasury", soc.treasury.atp_balance == 0.0)

    # Minimum requirements (§1.2)
    law = Law("law-1", "All decisions unanimous", "consensus", "voluntary")
    check("T1.4 Law is valid", law.is_valid())

    invalid_law = Law("", "", "")
    check("T1.5 Empty law invalid", not invalid_law.is_valid())

    # ── T2: Formation Process (§1.3) ──
    print("T2: Formation Process (§1.3)")

    founders = ["lct:entity:alice", "lct:entity:bob"]

    # Genesis
    check("T2.1 Genesis succeeds", soc.genesis(founders, law))
    check("T2.2 Phase is genesis", soc.phase == FormationPhase.GENESIS)
    check("T2.3 Law recorded", len(soc.laws) == 1)
    check("T2.4 Ledger has entry", soc.ledger.event_count() > 0)

    # Can't genesis twice
    check("T2.5 Double genesis fails", not soc.genesis(founders, law))

    # Need minimum 2 founders
    solo_soc = Society(society_lct="lct:society:solo", name="Solo")
    check("T2.6 Solo founder fails", not solo_soc.genesis(["lct:entity:alone"], law))

    # Bootstrap
    check("T2.7 Bootstrap succeeds", soc.bootstrap(founders, initial_atp=1000))
    check("T2.8 Phase is bootstrap", soc.phase == FormationPhase.BOOTSTRAP)
    check("T2.9 Citizens recorded", len(soc.citizens) == 2)
    check("T2.10 Treasury funded", soc.treasury.atp_balance == 1000)

    # Operational
    check("T2.11 Go operational", soc.go_operational())
    check("T2.12 Phase is operational", soc.phase == FormationPhase.OPERATIONAL)

    # ── T3: Citizenship (§2) ──
    print("T3: Citizenship (§2)")

    # Existing citizens from bootstrap
    alice = soc.citizens["lct:entity:alice"]
    check("T3.1 Alice is active", alice.is_active())
    check("T3.2 Alice can vote", alice.can_vote())
    check("T3.3 Alice has rights", "vote" in alice.rights and "propose" in alice.rights)
    check("T3.4 Alice has obligations", "witness" in alice.obligations)

    # New application
    charlie = soc.apply_citizenship("lct:entity:charlie")
    check("T3.5 Charlie is pending", charlie.status == CitizenshipStatus.PENDING)
    check("T3.6 Charlie can't vote", not charlie.can_vote())

    # Approve
    check("T3.7 Approval succeeds",
          soc.approve_citizenship("lct:entity:charlie", ["lct:entity:alice", "lct:entity:bob"]))
    check("T3.8 Charlie now active", soc.citizens["lct:entity:charlie"].is_active())

    # Multi-society citizenship (§2.2.1)
    soc2 = Society(society_lct="lct:society:test2", name="Test 2")
    soc2.genesis(["lct:entity:alice", "lct:entity:dave"], Law("law-2", "Simple law"))
    soc2.bootstrap(["lct:entity:alice", "lct:entity:dave"])
    soc2.go_operational()
    check("T3.9 Alice in both societies",
          "lct:entity:alice" in soc.citizens and "lct:entity:alice" in soc2.citizens)

    # Suspension
    check("T3.10 Suspend succeeds", soc.suspend_citizen("lct:entity:charlie", "testing"))
    check("T3.11 Charlie suspended",
          soc.citizens["lct:entity:charlie"].status == CitizenshipStatus.SUSPENDED)

    # Reinstatement
    check("T3.12 Reinstate succeeds", soc.reinstate_citizen("lct:entity:charlie"))
    check("T3.13 Charlie active again", soc.citizens["lct:entity:charlie"].is_active())

    # Termination
    check("T3.14 Terminate succeeds", soc.terminate_citizen("lct:entity:charlie", "violation"))
    check("T3.15 Charlie terminated",
          soc.citizens["lct:entity:charlie"].status == CitizenshipStatus.TERMINATED)

    # Active citizen count
    check("T3.16 Two active citizens", soc.citizen_count() == 2)

    # ── T4: Fractal Nature (§3) ──
    print("T4: Fractal Nature (§3)")

    system = FractalSocietySystem()
    parent = Society(society_lct="lct:society:universe", name="Universe")
    parent.genesis(["lct:entity:a", "lct:entity:b"], Law("law-core", "Core principles"))
    parent.bootstrap(["lct:entity:a", "lct:entity:b"], initial_atp=10000)
    parent.go_operational()
    system.register(parent)

    child = Society(society_lct="lct:society:regional", name="Regional")
    child.genesis(["lct:entity:c", "lct:entity:d"], Law("law-local", "Local rules"))
    child.bootstrap(["lct:entity:c", "lct:entity:d"], initial_atp=0)
    child.go_operational()

    check("T4.1 Create child", system.create_child("lct:society:universe", child))
    check("T4.2 Child has parent", child.parent_society == "lct:society:universe")
    check("T4.3 Parent has child", "lct:society:regional" in parent.child_societies)

    # Make child a citizen of parent for recursive citizenship
    parent.apply_citizenship("lct:society:regional")
    parent.approve_citizenship("lct:society:regional", ["lct:entity:a"])

    # Recursive citizenship (§3.2.2)
    check("T4.4 Recursive relationship",
          parent.has_indirect_relationship("lct:entity:c", child))

    # Citizenship tree (§3.3)
    tree = system.get_citizenship_tree("lct:entity:c")
    check("T4.5 Direct in regional", "lct:society:regional" in tree["direct"])
    check("T4.6 Indirect in universe", "lct:society:universe" in tree["indirect"])

    # Economic fractals (§3.2.3)
    check("T4.7 ATP flow to child", system.atp_flow("lct:society:universe", "lct:society:regional", 500))
    check("T4.8 Parent balance reduced", parent.treasury.atp_balance == 9500)
    check("T4.9 Child balance increased", child.treasury.atp_balance == 500)

    # Can't flow to non-child
    check("T4.10 Non-child flow fails",
          not system.atp_flow("lct:society:universe", "lct:society:unknown", 100))

    # ── T5: Ledger Types (§4) ──
    print("T5: Ledger Types (§4)")

    # Confined ledger
    confined = Ledger(LedgerType.CONFINED, validators=["lct:citizen:1", "lct:citizen:2"])
    check("T5.1 Confined type", confined.ledger_type == LedgerType.CONFINED)

    # Witnessed ledger
    witnessed = Ledger(LedgerType.WITNESSED, validators=["lct:citizen:1", "lct:external:auditor"])
    check("T5.2 Witnessed type", witnessed.ledger_type == LedgerType.WITNESSED)

    # Participatory ledger
    participatory = Ledger(LedgerType.PARTICIPATORY, parent_ledger_id="parent-ledger-1")
    check("T5.3 Participatory type", participatory.ledger_type == LedgerType.PARTICIPATORY)
    check("T5.4 Has parent ledger", participatory.parent_ledger_id == "parent-ledger-1")

    # Recording requirements (§4.2.1)
    entry = confined.record(LedgerEventType.CITIZENSHIP, {
        "action": "grant",
        "entity_lct": "lct:entity:test",
    })
    check("T5.5 Entry recorded", confined.event_count() == 1)
    check("T5.6 Entry has ID", entry.entry_id.startswith("entry-"))
    check("T5.7 Entry is active", entry.status == "active")

    # Amendment (§4.2.2)
    amendment = confined.amend(
        entry.entry_id, "correction",
        {"action": "grant", "entity_lct": "lct:entity:test-corrected"},
        "Typo in entity LCT", "amendment_law_v1",
    )
    check("T5.8 Amendment created", amendment is not None)
    check("T5.9 Original superseded", entry.status == "superseded")
    check("T5.10 Original points to amendment", entry.superseded_by == amendment.entry_id)
    check("T5.11 Amendment has original ref", amendment.data["amends"] == entry.entry_id)
    check("T5.12 Two entries total", confined.event_count() == 2)

    # Can't amend superseded entry
    double_amend = confined.amend(entry.entry_id, "correction", {}, "nope", "law")
    check("T5.13 Can't amend superseded", double_amend is None)

    # Active query
    active = confined.query_active()
    check("T5.14 One active entry", len(active) == 1)
    check("T5.15 Active is amendment", active[0].entry_id == amendment.entry_id)

    # Ledger upgrade (§5.2)
    soc.upgrade_ledger(LedgerType.WITNESSED)
    check("T5.16 Ledger upgraded", soc.ledger.ledger_type == LedgerType.WITNESSED)

    # ── T6: Law Governance ──
    print("T6: Law Governance")

    law2 = Law("law-merge-policy", "Merge requires 2 approvals", "majority_vote")
    check("T6.1 Propose law", soc.propose_law(law2, "lct:entity:alice"))

    # Non-citizen can't propose
    check("T6.2 Non-citizen can't propose", not soc.propose_law(law2, "lct:entity:nobody"))

    # Ratify with majority
    check("T6.3 Ratify with majority",
          soc.ratify_law(law2, ["lct:entity:alice", "lct:entity:bob"]))
    check("T6.4 Law count increased", len(soc.laws) == 2)

    # Can't ratify without majority
    law3 = Law("law-trivial", "trivial")
    check("T6.5 No majority fails", not soc.ratify_law(law3, ["lct:entity:alice"]))

    # ── T7: Trust Building (§5.3) ──
    print("T7: Trust Building (§5.3)")

    t3 = soc.calculate_t3()
    check("T7.1 T3 has talent", "talent" in t3)
    check("T7.2 T3 has training", "training" in t3)
    check("T7.3 T3 has temperament", "temperament" in t3)
    check("T7.4 All in [0,1]", all(0 <= v <= 1 for v in t3.values()))

    # Temperament reflects compliance (2 active / 3 total)
    check("T7.5 Temperament < 1.0", t3["temperament"] < 1.0)
    check("T7.6 Training from law count", t3["training"] >= 0.3)

    # ── T8: Example Societies (§6) ──
    print("T8: Example Societies (§6)")

    dev = create_dev_team_example()
    check("T8.1 Dev team operational", dev.phase == FormationPhase.OPERATIONAL)
    check("T8.2 Dev team 5 citizens", dev.citizen_count() == 5)
    check("T8.3 Dev team confined ledger", dev.ledger.ledger_type == LedgerType.CONFINED)
    check("T8.4 Dev team has law", len(dev.laws) >= 1)
    check("T8.5 Dev team has ATP", dev.treasury.atp_balance == 500)

    trade = create_trade_society_example()
    check("T8.6 Trade society operational", trade.phase == FormationPhase.OPERATIONAL)
    check("T8.7 Trade witnessed ledger", trade.ledger.ledger_type == LedgerType.WITNESSED)
    check("T8.8 Trade has external validator", "lct:auditor:ext1" in trade.ledger.validators)

    # ── T9: Future Protocols (§7) ──
    print("T9: Future Protocols (§7)")

    treaty = Treaty(
        treaty_id="treaty-1",
        society_a="lct:society:dev",
        society_b="lct:society:trade",
        terms=["Mutual recognition", "Resource sharing"],
        resource_sharing=True,
        reputation_portability=True,
    )
    check("T9.1 Treaty has parties", treaty.society_a and treaty.society_b)
    check("T9.2 Treaty has terms", len(treaty.terms) == 2)
    check("T9.3 Resource sharing enabled", treaty.resource_sharing)
    check("T9.4 Reputation portable", treaty.reputation_portability)

    merger = MergerProposal(
        source_society="lct:society:small",
        target_society="lct:society:large",
        asset_division={"atp": 0.3, "laws": 1.0},
        citizen_migration=True,
    )
    check("T9.5 Merger proposal", merger.citizen_migration)

    dispute = DisputeResolution(
        dispute_id="dispute-1",
        parties=["lct:society:a", "lct:society:b"],
        arbitrator="lct:society:parent",
    )
    check("T9.6 Dispute has arbitrator", dispute.arbitrator is not None)

    # ── T10: Treasury Operations ──
    print("T10: Treasury Operations")

    t = Treasury(atp_balance=100, allocation_law="equal_share")
    check("T10.1 Initial balance", t.atp_balance == 100)
    check("T10.2 Allocate succeeds", t.allocate_atp(30, "recipient"))
    check("T10.3 Balance reduced", t.atp_balance == 70)
    check("T10.4 Over-allocate fails", not t.allocate_atp(100, "recipient"))
    t.receive_atp(50)
    check("T10.5 Receive increases balance", t.atp_balance == 120)

    # ══════════════════════════════════════════════════════════

    print(f"\n{'='*60}")
    print(f"Society Specification: {passed}/{passed+failed} checks passed")
    if failed:
        print(f"  {failed} FAILED")
    else:
        print(f"  All checks passed!")
    print(f"{'='*60}")
    return failed == 0


if __name__ == "__main__":
    run_tests()
