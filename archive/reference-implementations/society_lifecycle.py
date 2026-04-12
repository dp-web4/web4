#!/usr/bin/env python3
"""
Web4 Society Lifecycle — Reference Implementation

Implements the Society Specification from:
  web4-standard/core-spec/SOCIETY_SPECIFICATION.md

Core concepts:
  - Society: self-governing collective with laws, ledger, treasury, LCT
  - Citizenship: witnessed relationship, multi-society, lifecycle management
  - Ledger: confined/witnessed/participatory with amendment chains
  - Treasury: ATP/ADP pool with law-governed allocation
  - Fractal: societies as citizens of other societies

Complements:
  - society_metabolic_states.py (metabolic state machine)
  - law_governance_integration.py (Law Oracle binding)
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ══════════════════════════════════════════════════════════════
# §1 — Society Core
# ══════════════════════════════════════════════════════════════

class SocietyPhase(Enum):
    GENESIS = "genesis"
    BOOTSTRAP = "bootstrap"
    OPERATIONAL = "operational"
    SUSPENDED = "suspended"
    DISSOLVED = "dissolved"


class CitizenStatus(Enum):
    PENDING = "pending"
    PROVISIONAL = "provisional"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class LedgerType(Enum):
    CONFINED = "confined"
    WITNESSED = "witnessed"
    PARTICIPATORY = "participatory"


@dataclass
class Law:
    law_id: str
    title: str
    content: str
    version: str = "v1.0.0"
    status: str = "ratified"
    effective_date: Optional[str] = None
    amendment_history: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {
            "law_id": self.law_id,
            "title": self.title,
            "content": self.content,
            "version": self.version,
            "status": self.status,
        }
        if self.effective_date:
            d["effective_date"] = self.effective_date
        if self.amendment_history:
            d["amendment_history"] = list(self.amendment_history)
        return d


# ══════════════════════════════════════════════════════════════
# §4 — Ledger (immutable record with amendment support)
# ══════════════════════════════════════════════════════════════

@dataclass
class LedgerEntry:
    entry_id: str
    entry_type: str  # citizenship_event, law_change, economic_event, amendment
    data: dict
    timestamp: str
    witnesses: list = field(default_factory=list)
    prev_hash: Optional[str] = None
    entry_hash: Optional[str] = None
    status: str = "active"  # active, superseded
    superseded_by: Optional[str] = None

    def compute_hash(self) -> str:
        payload = json.dumps({
            "entry_id": self.entry_id,
            "entry_type": self.entry_type,
            "data": self.data,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
        }, sort_keys=True)
        self.entry_hash = hashlib.sha256(payload.encode()).hexdigest()
        return self.entry_hash

    def to_dict(self) -> dict:
        d = {
            "entry_id": self.entry_id,
            "entry_type": self.entry_type,
            "data": self.data,
            "timestamp": self.timestamp,
            "witnesses": list(self.witnesses),
            "status": self.status,
        }
        if self.entry_hash:
            d["entry_hash"] = self.entry_hash
        if self.prev_hash:
            d["prev_hash"] = self.prev_hash
        if self.superseded_by:
            d["superseded_by"] = self.superseded_by
        return d


class SocietyLedger:
    """Append-only ledger with hash-chain integrity and amendment support."""

    def __init__(self, ledger_type: LedgerType = LedgerType.CONFINED):
        self.ledger_type = ledger_type
        self.entries: list[LedgerEntry] = []
        self.entry_index: dict[str, int] = {}
        self._counter = 0

    def append(self, entry_type: str, data: dict, witnesses: list = None, timestamp: str = None) -> LedgerEntry:
        self._counter += 1
        entry_id = f"entry-{self._counter:04d}"
        prev_hash = self.entries[-1].entry_hash if self.entries else None

        entry = LedgerEntry(
            entry_id=entry_id,
            entry_type=entry_type,
            data=data,
            timestamp=timestamp or _now(),
            witnesses=witnesses or [],
            prev_hash=prev_hash,
        )
        entry.compute_hash()
        self.entries.append(entry)
        self.entry_index[entry_id] = len(self.entries) - 1
        return entry

    def amend(self, original_id: str, amendment_type: str, new_data: dict,
              reason: str, law_auth: str, witnesses: list = None) -> Optional[LedgerEntry]:
        """Amend an existing entry while preserving original (§4.3)."""
        if original_id not in self.entry_index:
            return None

        idx = self.entry_index[original_id]
        original = self.entries[idx]

        # Record amendment
        amendment = self.append(
            entry_type="amendment",
            data={
                "amends": original_id,
                "amendment_type": amendment_type,
                "original_data": original.data,
                "new_data": new_data,
                "reason": reason,
                "law_authorization": law_auth,
            },
            witnesses=witnesses,
        )

        # Mark original as superseded
        original.status = "superseded"
        original.superseded_by = amendment.entry_id

        return amendment

    def query(self, entry_type: str = None, status: str = None) -> list[LedgerEntry]:
        results = self.entries
        if entry_type:
            results = [e for e in results if e.entry_type == entry_type]
        if status:
            results = [e for e in results if e.status == status]
        return results

    def verify_chain(self) -> bool:
        """Verify hash chain integrity."""
        for i, entry in enumerate(self.entries):
            expected_prev = self.entries[i - 1].entry_hash if i > 0 else None
            if entry.prev_hash != expected_prev:
                return False
            saved_hash = entry.entry_hash
            entry.compute_hash()
            if entry.entry_hash != saved_hash:
                return False
        return True

    @property
    def length(self) -> int:
        return len(self.entries)

    def to_dict(self) -> dict:
        return {
            "ledger_type": self.ledger_type.value,
            "entry_count": len(self.entries),
            "entries": [e.to_dict() for e in self.entries],
        }


# ══════════════════════════════════════════════════════════════
# §1.2.3 — Treasury (ATP/ADP pool)
# ══════════════════════════════════════════════════════════════

@dataclass
class TreasuryAllocation:
    recipient_lct: str
    amount: float
    purpose: str
    timestamp: str
    approved_by: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "recipient_lct": self.recipient_lct,
            "amount": self.amount,
            "purpose": self.purpose,
            "timestamp": self.timestamp,
            "approved_by": list(self.approved_by),
        }


class Treasury:
    """Society-managed ATP/ADP pool (§1.2.3)."""

    def __init__(self, initial_atp: float = 0.0):
        self.atp_balance: float = initial_atp
        self.adp_pool: float = 0.0
        self.allocations: list[TreasuryAllocation] = []
        self.total_minted: float = initial_atp
        self.total_allocated: float = 0.0

    def mint(self, amount: float):
        """Society mints new ATP."""
        self.atp_balance += amount
        self.total_minted += amount

    def allocate(self, recipient_lct: str, amount: float, purpose: str,
                 approved_by: list = None) -> Optional[TreasuryAllocation]:
        if amount > self.atp_balance:
            return None
        self.atp_balance -= amount
        self.total_allocated += amount
        alloc = TreasuryAllocation(
            recipient_lct=recipient_lct,
            amount=amount,
            purpose=purpose,
            timestamp=_now(),
            approved_by=approved_by or [],
        )
        self.allocations.append(alloc)
        return alloc

    def receive_adp(self, amount: float):
        """ADP returns after discharge."""
        self.adp_pool += amount

    def recharge(self, amount: float) -> float:
        """Recharge ADP back to ATP."""
        actual = min(amount, self.adp_pool)
        self.adp_pool -= actual
        self.atp_balance += actual
        return actual

    def to_dict(self) -> dict:
        return {
            "atp_balance": self.atp_balance,
            "adp_pool": self.adp_pool,
            "total_minted": self.total_minted,
            "total_allocated": self.total_allocated,
            "allocation_count": len(self.allocations),
        }


# ══════════════════════════════════════════════════════════════
# §2 — Citizenship
# ══════════════════════════════════════════════════════════════

@dataclass
class CitizenRecord:
    entity_lct: str
    status: CitizenStatus = CitizenStatus.PENDING
    rights: list = field(default_factory=list)
    obligations: list = field(default_factory=list)
    joined_at: Optional[str] = None
    suspended_at: Optional[str] = None
    terminated_at: Optional[str] = None
    witness_lcts: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {
            "entity_lct": self.entity_lct,
            "status": self.status.value,
            "rights": list(self.rights),
            "obligations": list(self.obligations),
        }
        if self.joined_at:
            d["joined_at"] = self.joined_at
        if self.suspended_at:
            d["suspended_at"] = self.suspended_at
        if self.terminated_at:
            d["terminated_at"] = self.terminated_at
        if self.witness_lcts:
            d["witness_lcts"] = list(self.witness_lcts)
        return d


# ══════════════════════════════════════════════════════════════
# Society — Main class
# ══════════════════════════════════════════════════════════════

class Society:
    """Self-governing collective of LCT-bearing entities (§1)."""

    def __init__(
        self,
        society_lct: str,
        name: str,
        founding_law: Law,
        initial_atp: float = 0.0,
        ledger_type: LedgerType = LedgerType.CONFINED,
        parent_society: Optional["Society"] = None,
    ):
        self.society_lct = society_lct
        self.name = name
        self.phase = SocietyPhase.GENESIS
        self.laws: dict[str, Law] = {founding_law.law_id: founding_law}
        self.ledger = SocietyLedger(ledger_type)
        self.treasury = Treasury(initial_atp)
        self.citizens: dict[str, CitizenRecord] = {}
        self.parent_society = parent_society
        self.child_societies: list[str] = []
        self.external_witnesses: list[str] = []
        self.created_at = _now()

        # Record genesis in ledger
        self.ledger.append("genesis", {
            "society_lct": society_lct,
            "name": name,
            "founding_law": founding_law.law_id,
            "initial_atp": initial_atp,
            "parent": parent_society.society_lct if parent_society else None,
        })

    # ── Phase Management ─────────────────────────────────────

    def bootstrap(self, founders: list[str], witness_lcts: list[str] = None) -> bool:
        """Bootstrap phase: register initial citizens (§1.3)."""
        if self.phase != SocietyPhase.GENESIS:
            return False

        for lct in founders:
            self._grant_citizenship(
                lct,
                rights=["vote", "propose", "allocate"],
                obligations=["witness", "contribute", "abide_law"],
                witnesses=witness_lcts or [],
            )

        self.phase = SocietyPhase.BOOTSTRAP

        self.ledger.append("phase_change", {
            "from": "genesis",
            "to": "bootstrap",
            "founders": founders,
        }, witnesses=witness_lcts)

        return True

    def go_operational(self) -> bool:
        """Transition to operational phase (§1.3)."""
        if self.phase != SocietyPhase.BOOTSTRAP:
            return False
        if len(self.citizens) < 2:
            return False

        self.phase = SocietyPhase.OPERATIONAL
        self.ledger.append("phase_change", {
            "from": "bootstrap",
            "to": "operational",
            "citizen_count": len(self.citizens),
        })
        return True

    def suspend(self, reason: str) -> bool:
        if self.phase not in (SocietyPhase.BOOTSTRAP, SocietyPhase.OPERATIONAL):
            return False
        self.phase = SocietyPhase.SUSPENDED
        self.ledger.append("phase_change", {"to": "suspended", "reason": reason})
        return True

    def dissolve(self, reason: str, witness_lcts: list = None) -> bool:
        if self.phase == SocietyPhase.DISSOLVED:
            return False
        self.phase = SocietyPhase.DISSOLVED
        # Terminate all citizenships
        for cr in self.citizens.values():
            if cr.status == CitizenStatus.ACTIVE:
                cr.status = CitizenStatus.TERMINATED
                cr.terminated_at = _now()
        self.ledger.append("dissolution", {
            "reason": reason,
            "final_citizen_count": len(self.citizens),
            "remaining_atp": self.treasury.atp_balance,
        }, witnesses=witness_lcts)
        return True

    # ── Citizenship Management ───────────────────────────────

    def _grant_citizenship(self, entity_lct: str, rights: list, obligations: list,
                            witnesses: list) -> CitizenRecord:
        record = CitizenRecord(
            entity_lct=entity_lct,
            status=CitizenStatus.ACTIVE,
            rights=rights,
            obligations=obligations,
            joined_at=_now(),
            witness_lcts=witnesses,
        )
        self.citizens[entity_lct] = record

        self.ledger.append("citizenship_event", {
            "action": "grant",
            "entity_lct": entity_lct,
            "rights": rights,
            "obligations": obligations,
        }, witnesses=witnesses)

        return record

    def apply_for_citizenship(self, entity_lct: str) -> Optional[CitizenRecord]:
        """Entity applies for citizenship (§2.3)."""
        if self.phase not in (SocietyPhase.BOOTSTRAP, SocietyPhase.OPERATIONAL):
            return None
        if entity_lct in self.citizens:
            return None  # Already a citizen

        record = CitizenRecord(
            entity_lct=entity_lct,
            status=CitizenStatus.PENDING,
        )
        self.citizens[entity_lct] = record

        self.ledger.append("citizenship_event", {
            "action": "apply",
            "entity_lct": entity_lct,
        })

        return record

    def accept_citizen(self, entity_lct: str, rights: list = None, obligations: list = None,
                        witnesses: list = None, provisional: bool = False) -> bool:
        """Accept a pending citizen (§2.3)."""
        if entity_lct not in self.citizens:
            return False
        record = self.citizens[entity_lct]
        if record.status != CitizenStatus.PENDING:
            return False

        record.status = CitizenStatus.PROVISIONAL if provisional else CitizenStatus.ACTIVE
        record.rights = rights or ["vote", "propose"]
        record.obligations = obligations or ["abide_law", "contribute"]
        record.joined_at = _now()
        record.witness_lcts = witnesses or []

        self.ledger.append("citizenship_event", {
            "action": "accept",
            "entity_lct": entity_lct,
            "status": record.status.value,
            "rights": record.rights,
            "obligations": record.obligations,
        }, witnesses=witnesses)

        return True

    def reject_citizen(self, entity_lct: str, reason: str = "") -> bool:
        if entity_lct not in self.citizens:
            return False
        record = self.citizens[entity_lct]
        if record.status != CitizenStatus.PENDING:
            return False

        record.status = CitizenStatus.TERMINATED
        record.terminated_at = _now()

        self.ledger.append("citizenship_event", {
            "action": "reject",
            "entity_lct": entity_lct,
            "reason": reason,
        })
        return True

    def suspend_citizen(self, entity_lct: str, reason: str, witnesses: list = None) -> bool:
        """Suspend an active citizen (§2.3)."""
        if entity_lct not in self.citizens:
            return False
        record = self.citizens[entity_lct]
        if record.status not in (CitizenStatus.ACTIVE, CitizenStatus.PROVISIONAL):
            return False

        record.status = CitizenStatus.SUSPENDED
        record.suspended_at = _now()

        self.ledger.append("citizenship_event", {
            "action": "suspend",
            "entity_lct": entity_lct,
            "reason": reason,
        }, witnesses=witnesses)
        return True

    def reinstate_citizen(self, entity_lct: str, witnesses: list = None) -> bool:
        """Reinstate a suspended citizen (§2.3)."""
        if entity_lct not in self.citizens:
            return False
        record = self.citizens[entity_lct]
        if record.status != CitizenStatus.SUSPENDED:
            return False

        record.status = CitizenStatus.ACTIVE
        record.suspended_at = None

        self.ledger.append("citizenship_event", {
            "action": "reinstate",
            "entity_lct": entity_lct,
        }, witnesses=witnesses)
        return True

    def terminate_citizen(self, entity_lct: str, reason: str, witnesses: list = None) -> bool:
        if entity_lct not in self.citizens:
            return False
        record = self.citizens[entity_lct]
        if record.status == CitizenStatus.TERMINATED:
            return False

        record.status = CitizenStatus.TERMINATED
        record.terminated_at = _now()

        self.ledger.append("citizenship_event", {
            "action": "terminate",
            "entity_lct": entity_lct,
            "reason": reason,
        }, witnesses=witnesses)
        return True

    # ── Law Management ───────────────────────────────────────

    def propose_law(self, law: Law, proposer_lct: str) -> bool:
        """Propose a new law (§4.2.1)."""
        if self.phase not in (SocietyPhase.BOOTSTRAP, SocietyPhase.OPERATIONAL):
            return False
        if proposer_lct not in self.citizens:
            return False
        if self.citizens[proposer_lct].status != CitizenStatus.ACTIVE:
            return False
        if "propose" not in self.citizens[proposer_lct].rights:
            return False

        law.status = "proposed"
        self.laws[law.law_id] = law

        self.ledger.append("law_change", {
            "action": "propose",
            "law_id": law.law_id,
            "title": law.title,
            "proposer": proposer_lct,
        })
        return True

    def ratify_law(self, law_id: str, voters: dict, witnesses: list = None) -> bool:
        """Ratify a proposed law with voting record (§4.2.1)."""
        if law_id not in self.laws:
            return False
        law = self.laws[law_id]
        if law.status != "proposed":
            return False

        # Simple majority
        yea = sum(1 for v in voters.values() if v == "yea")
        nay = sum(1 for v in voters.values() if v == "nay")
        if yea <= nay:
            law.status = "rejected"
            self.ledger.append("law_change", {
                "action": "reject",
                "law_id": law_id,
                "voting_record": voters,
            })
            return False

        law.status = "ratified"
        law.effective_date = _now()

        self.ledger.append("law_change", {
            "action": "ratify",
            "law_id": law_id,
            "voting_record": voters,
            "effective_date": law.effective_date,
        }, witnesses=witnesses)
        return True

    def amend_law(self, law_id: str, new_content: str, new_version: str,
                   reason: str, voters: dict, witnesses: list = None) -> bool:
        """Amend an existing ratified law (§4.2.2)."""
        if law_id not in self.laws:
            return False
        law = self.laws[law_id]
        if law.status != "ratified":
            return False

        yea = sum(1 for v in voters.values() if v == "yea")
        nay = sum(1 for v in voters.values() if v == "nay")
        if yea <= nay:
            return False

        old_version = law.version
        law.amendment_history.append({
            "from_version": old_version,
            "to_version": new_version,
            "reason": reason,
            "timestamp": _now(),
        })
        law.content = new_content
        law.version = new_version

        self.ledger.append("law_change", {
            "action": "amend",
            "law_id": law_id,
            "from_version": old_version,
            "to_version": new_version,
            "reason": reason,
            "voting_record": voters,
        }, witnesses=witnesses)
        return True

    # ── Treasury Operations ──────────────────────────────────

    def allocate_atp(self, recipient_lct: str, amount: float, purpose: str,
                      approved_by: list = None) -> Optional[TreasuryAllocation]:
        """Allocate ATP from treasury to a citizen (§1.2.3)."""
        if recipient_lct not in self.citizens:
            return None
        if self.citizens[recipient_lct].status != CitizenStatus.ACTIVE:
            return None

        alloc = self.treasury.allocate(recipient_lct, amount, purpose, approved_by)
        if alloc:
            self.ledger.append("economic_event", {
                "action": "allocate",
                "amount": amount,
                "token_type": "ATP",
                "recipient_lct": recipient_lct,
                "purpose": purpose,
            })
        return alloc

    # ── Fractal Membership (§3) ──────────────────────────────

    def incorporate_child(self, child_society: "Society") -> bool:
        """Register a child society as citizen (§3.1)."""
        if self.phase != SocietyPhase.OPERATIONAL:
            return False

        child_society.parent_society = self
        self.child_societies.append(child_society.society_lct)

        # Grant citizenship to child society
        self._grant_citizenship(
            child_society.society_lct,
            rights=["participate", "allocate"],
            obligations=["abide_law", "report"],
            witnesses=[],
        )

        self.ledger.append("fractal_event", {
            "action": "incorporate_child",
            "child_lct": child_society.society_lct,
            "child_name": child_society.name,
        })
        return True

    def get_fractal_tree(self, depth: int = 3) -> dict:
        """Get the fractal citizenship tree (§3.3)."""
        tree = {
            "society_lct": self.society_lct,
            "name": self.name,
            "phase": self.phase.value,
            "citizen_count": len([c for c in self.citizens.values() if c.status == CitizenStatus.ACTIVE]),
        }
        if depth > 0 and self.parent_society:
            tree["parent"] = {
                "society_lct": self.parent_society.society_lct,
                "name": self.parent_society.name,
            }
        if self.child_societies:
            tree["children"] = list(self.child_societies)
        return tree

    # ── Queries ──────────────────────────────────────────────

    def active_citizens(self) -> list[CitizenRecord]:
        return [c for c in self.citizens.values() if c.status == CitizenStatus.ACTIVE]

    def citizen_count(self) -> dict:
        counts = {}
        for c in self.citizens.values():
            s = c.status.value
            counts[s] = counts.get(s, 0) + 1
        return counts

    def to_dict(self) -> dict:
        return {
            "society_lct": self.society_lct,
            "name": self.name,
            "phase": self.phase.value,
            "laws": {k: v.to_dict() for k, v in self.laws.items()},
            "citizen_count": self.citizen_count(),
            "treasury": self.treasury.to_dict(),
            "ledger_type": self.ledger.ledger_type.value,
            "ledger_entries": self.ledger.length,
            "parent": self.parent_society.society_lct if self.parent_society else None,
            "children": list(self.child_societies),
        }


# ══════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════

def _now() -> str:
    return "2026-02-21T12:00:00Z"


# ══════════════════════════════════════════════════════════════
# Self-Tests
# ══════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            print(f"  [PASS] {name}")
            passed += 1
        else:
            print(f"  [FAIL] {name}")
            failed += 1

    # ── T1: Society Formation (§1.3) ────────────────────────
    print("\n═══ T1: Society Formation — Genesis ═══")
    founding_law = Law(
        law_id="LAW-001",
        title="Founding Charter",
        content="All decisions by unanimous consensus",
        version="v1.0.0",
        status="ratified",
        effective_date=_now(),
    )
    society = Society(
        society_lct="lct:web4:society:dev-team",
        name="Dev Team Alpha",
        founding_law=founding_law,
        initial_atp=1000.0,
    )
    check("T1: society created", society is not None)
    check("T1: phase is GENESIS", society.phase == SocietyPhase.GENESIS)
    check("T1: has founding law", "LAW-001" in society.laws)
    check("T1: treasury initialized", society.treasury.atp_balance == 1000.0)
    check("T1: ledger has genesis entry", society.ledger.length == 1)
    check("T1: genesis entry type", society.ledger.entries[0].entry_type == "genesis")

    # ── T2: Bootstrap Phase (§1.3) ──────────────────────────
    print("\n═══ T2: Bootstrap Phase ═══")
    founders = [
        "lct:web4:human:alice",
        "lct:web4:human:bob",
        "lct:web4:ai:claude",
    ]
    witnesses = ["lct:web4:witness:w1", "lct:web4:witness:w2"]
    ok = society.bootstrap(founders, witnesses)
    check("T2: bootstrap succeeded", ok)
    check("T2: phase is BOOTSTRAP", society.phase == SocietyPhase.BOOTSTRAP)
    check("T2: 3 citizens registered", len(society.citizens) == 3)
    check("T2: all active", all(c.status == CitizenStatus.ACTIVE for c in society.citizens.values()))
    check("T2: alice has vote right", "vote" in society.citizens["lct:web4:human:alice"].rights)
    check("T2: ledger has citizenship events", society.ledger.length >= 4)  # genesis + 3 citizens + phase change

    # ── T3: Operational Phase (§1.3) ────────────────────────
    print("\n═══ T3: Operational Phase ═══")
    ok = society.go_operational()
    check("T3: went operational", ok)
    check("T3: phase is OPERATIONAL", society.phase == SocietyPhase.OPERATIONAL)

    # Can't go operational again
    ok2 = society.go_operational()
    check("T3: can't go operational twice", not ok2)

    # ── T4: Citizenship Lifecycle (§2.3) ────────────────────
    print("\n═══ T4: Citizenship Lifecycle ═══")
    # Application
    dave_lct = "lct:web4:human:dave"
    app = society.apply_for_citizenship(dave_lct)
    check("T4: application created", app is not None)
    check("T4: status is PENDING", app.status == CitizenStatus.PENDING)

    # Acceptance
    ok = society.accept_citizen(dave_lct, rights=["vote", "propose"], obligations=["abide_law"])
    check("T4: acceptance succeeded", ok)
    check("T4: dave is ACTIVE", society.citizens[dave_lct].status == CitizenStatus.ACTIVE)

    # Suspension
    ok = society.suspend_citizen(dave_lct, "Violated code review policy")
    check("T4: suspension succeeded", ok)
    check("T4: dave is SUSPENDED", society.citizens[dave_lct].status == CitizenStatus.SUSPENDED)

    # Reinstatement
    ok = society.reinstate_citizen(dave_lct)
    check("T4: reinstatement succeeded", ok)
    check("T4: dave is ACTIVE again", society.citizens[dave_lct].status == CitizenStatus.ACTIVE)

    # Rejection of new applicant
    eve_lct = "lct:web4:human:eve"
    society.apply_for_citizenship(eve_lct)
    ok = society.reject_citizen(eve_lct, "Insufficient references")
    check("T4: rejection succeeded", ok)
    check("T4: eve is TERMINATED", society.citizens[eve_lct].status == CitizenStatus.TERMINATED)

    # Termination
    ok = society.terminate_citizen(dave_lct, "Left voluntarily")
    check("T4: termination succeeded", ok)
    check("T4: dave is TERMINATED", society.citizens[dave_lct].status == CitizenStatus.TERMINATED)

    # Can't suspend terminated
    ok = society.suspend_citizen(dave_lct, "try again")
    check("T4: can't suspend terminated", not ok)

    # Duplicate application blocked
    app2 = society.apply_for_citizenship("lct:web4:human:alice")
    check("T4: duplicate application blocked", app2 is None)

    # Provisional status
    frank_lct = "lct:web4:human:frank"
    society.apply_for_citizenship(frank_lct)
    ok = society.accept_citizen(frank_lct, provisional=True)
    check("T4: provisional acceptance", ok)
    check("T4: frank is PROVISIONAL", society.citizens[frank_lct].status == CitizenStatus.PROVISIONAL)

    # Can suspend provisional
    ok = society.suspend_citizen(frank_lct, "Probation violation")
    check("T4: can suspend provisional", ok)

    # ── T5: Law Management ──────────────────────────────────
    print("\n═══ T5: Law Management ═══")
    code_review_law = Law(
        law_id="LAW-002",
        title="Code Review Policy",
        content="All PRs require 2 approvals before merge",
    )
    ok = society.propose_law(code_review_law, "lct:web4:human:alice")
    check("T5: law proposed", ok)
    check("T5: law status is proposed", society.laws["LAW-002"].status == "proposed")

    # Ratify with voting
    voters = {
        "lct:web4:human:alice": "yea",
        "lct:web4:human:bob": "yea",
        "lct:web4:ai:claude": "nay",
    }
    ok = society.ratify_law("LAW-002", voters)
    check("T5: law ratified (2-1)", ok)
    check("T5: law status is ratified", society.laws["LAW-002"].status == "ratified")

    # Reject a law
    bad_law = Law(law_id="LAW-003", title="Bad Law", content="All code must be in COBOL")
    society.propose_law(bad_law, "lct:web4:human:bob")
    voters2 = {"lct:web4:human:alice": "nay", "lct:web4:human:bob": "yea", "lct:web4:ai:claude": "nay"}
    ok = society.ratify_law("LAW-003", voters2)
    check("T5: bad law rejected (1-2)", not ok)
    check("T5: law status is rejected", society.laws["LAW-003"].status == "rejected")

    # Non-citizen can't propose
    ok = society.propose_law(
        Law(law_id="LAW-004", title="X", content="Y"),
        "lct:web4:human:unknown",
    )
    check("T5: non-citizen can't propose", not ok)

    # Amend law
    ok = society.amend_law(
        "LAW-002",
        new_content="All PRs require 3 approvals before merge",
        new_version="v2.0.0",
        reason="Increased quality standards",
        voters={"lct:web4:human:alice": "yea", "lct:web4:human:bob": "yea", "lct:web4:ai:claude": "yea"},
    )
    check("T5: amendment succeeded", ok)
    check("T5: law version updated", society.laws["LAW-002"].version == "v2.0.0")
    check("T5: amendment history recorded", len(society.laws["LAW-002"].amendment_history) == 1)

    # ── T6: Treasury Operations (§1.2.3) ────────────────────
    print("\n═══ T6: Treasury Operations ═══")
    check("T6: initial balance", society.treasury.atp_balance == 1000.0)

    # Allocate to citizen
    alloc = society.allocate_atp("lct:web4:human:alice", 100.0, "Sprint bonus")
    check("T6: allocation succeeded", alloc is not None)
    check("T6: balance reduced", society.treasury.atp_balance == 900.0)
    check("T6: total allocated", society.treasury.total_allocated == 100.0)

    # Allocate to non-citizen blocked
    alloc2 = society.allocate_atp("lct:web4:human:unknown", 50.0, "Invalid")
    check("T6: non-citizen allocation blocked", alloc2 is None)

    # Over-allocation blocked
    alloc3 = society.allocate_atp("lct:web4:human:bob", 10000.0, "Too much")
    check("T6: over-allocation blocked", alloc3 is None)

    # ADP return and recharge
    society.treasury.receive_adp(50.0)
    check("T6: ADP received", society.treasury.adp_pool == 50.0)
    recharged = society.treasury.recharge(30.0)
    check("T6: recharge amount", recharged == 30.0)
    check("T6: ADP pool after recharge", society.treasury.adp_pool == 20.0)
    check("T6: ATP after recharge", society.treasury.atp_balance == 930.0)

    # Mint new ATP
    society.treasury.mint(500.0)
    check("T6: minting succeeded", society.treasury.atp_balance == 1430.0)
    check("T6: total minted tracked", society.treasury.total_minted == 1500.0)

    # ── T7: Ledger Integrity (§4) ───────────────────────────
    print("\n═══ T7: Ledger Integrity ═══")
    check("T7: ledger has entries", society.ledger.length > 0)
    check("T7: hash chain valid", society.ledger.verify_chain())

    # Query by type
    citizenship_events = society.ledger.query(entry_type="citizenship_event")
    check("T7: citizenship events found", len(citizenship_events) > 0)

    law_events = society.ledger.query(entry_type="law_change")
    check("T7: law events found", len(law_events) > 0)

    econ_events = society.ledger.query(entry_type="economic_event")
    check("T7: economic events found", len(econ_events) > 0)

    # Ledger amendment (§4.2.2)
    first_entry_id = society.ledger.entries[1].entry_id  # First citizenship entry
    amendment = society.ledger.amend(
        first_entry_id,
        amendment_type="correction",
        new_data={"note": "Rights updated after review"},
        reason="Initial rights were too broad",
        law_auth="LAW-001",
    )
    check("T7: amendment created", amendment is not None)
    check("T7: original marked superseded", society.ledger.entries[1].status == "superseded")
    check("T7: superseded_by set", society.ledger.entries[1].superseded_by == amendment.entry_id)
    check("T7: chain still valid after amendment", society.ledger.verify_chain())

    # Active-only query
    active_entries = society.ledger.query(status="active")
    superseded = society.ledger.query(status="superseded")
    check("T7: active + superseded = total", len(active_entries) + len(superseded) == society.ledger.length)

    # ── T8: Fractal Membership (§3) ─────────────────────────
    print("\n═══ T8: Fractal Membership ═══")
    # Create child society
    child_law = Law(law_id="CHILD-LAW-001", title="Child Charter", content="Delegate to parent")
    child = Society(
        society_lct="lct:web4:society:frontend-team",
        name="Frontend Team",
        founding_law=child_law,
        initial_atp=200.0,
    )
    child.bootstrap(["lct:web4:human:alice", "lct:web4:human:frank2"])
    child.go_operational()

    # Incorporate child into parent
    ok = society.incorporate_child(child)
    check("T8: incorporation succeeded", ok)
    check("T8: child in parent's children list", child.society_lct in society.child_societies)
    check("T8: child is citizen of parent", child.society_lct in society.citizens)
    check("T8: child's parent set", child.parent_society == society)

    # Fractal tree
    tree = society.get_fractal_tree()
    check("T8: tree has society_lct", tree["society_lct"] == society.society_lct)
    check("T8: tree has children", "children" in tree and len(tree["children"]) > 0)

    child_tree = child.get_fractal_tree()
    check("T8: child tree has parent", "parent" in child_tree)
    check("T8: child parent matches", child_tree["parent"]["society_lct"] == society.society_lct)

    # Create grandchild
    grandchild_law = Law(law_id="GC-LAW-001", title="Grandchild Charter", content="Minimal rules")
    grandchild = Society(
        society_lct="lct:web4:society:css-subteam",
        name="CSS Sub-Team",
        founding_law=grandchild_law,
        initial_atp=50.0,
    )
    grandchild.bootstrap(["lct:web4:human:alice"])
    grandchild.go_operational()
    ok = child.incorporate_child(grandchild)
    check("T8: grandchild incorporated", ok)
    check("T8: 3-level fractal", grandchild.parent_society == child)

    # ── T9: Ledger Types (§4.1) ─────────────────────────────
    print("\n═══ T9: Ledger Types ═══")
    # Confined
    confined_society = Society(
        society_lct="lct:web4:society:private",
        name="Private Team",
        founding_law=Law(law_id="P-001", title="Private Charter", content="Confined rules"),
        ledger_type=LedgerType.CONFINED,
    )
    check("T9: confined ledger", confined_society.ledger.ledger_type == LedgerType.CONFINED)

    # Witnessed
    witnessed_society = Society(
        society_lct="lct:web4:society:trade",
        name="Trade Guild",
        founding_law=Law(law_id="T-001", title="Trade Charter", content="Witnessed rules"),
        ledger_type=LedgerType.WITNESSED,
    )
    check("T9: witnessed ledger", witnessed_society.ledger.ledger_type == LedgerType.WITNESSED)

    # Participatory
    participatory_society = Society(
        society_lct="lct:web4:society:global",
        name="Global Web4",
        founding_law=Law(law_id="G-001", title="Global Charter", content="Participatory rules"),
        ledger_type=LedgerType.PARTICIPATORY,
    )
    check("T9: participatory ledger", participatory_society.ledger.ledger_type == LedgerType.PARTICIPATORY)

    # ── T10: Society Suspension & Dissolution ────────────────
    print("\n═══ T10: Society Suspension & Dissolution ═══")
    doomed = Society(
        society_lct="lct:web4:society:doomed",
        name="Doomed Society",
        founding_law=Law(law_id="D-001", title="Charter", content="Rules"),
        initial_atp=100.0,
    )
    doomed.bootstrap(["lct:web4:human:x", "lct:web4:human:y"])
    doomed.go_operational()

    ok = doomed.suspend("Budget crisis")
    check("T10: suspension succeeded", ok)
    check("T10: phase is SUSPENDED", doomed.phase == SocietyPhase.SUSPENDED)

    ok = doomed.dissolve("Irreconcilable differences", witness_lcts=["lct:web4:witness:w1"])
    check("T10: dissolution succeeded", ok)
    check("T10: phase is DISSOLVED", doomed.phase == SocietyPhase.DISSOLVED)
    check("T10: all citizens terminated",
          all(c.status == CitizenStatus.TERMINATED for c in doomed.citizens.values()))
    check("T10: dissolution in ledger",
          any(e.entry_type == "dissolution" for e in doomed.ledger.entries))

    # Can't dissolve twice
    ok = doomed.dissolve("Again")
    check("T10: can't dissolve twice", not ok)

    # ── T11: Serialization ──────────────────────────────────
    print("\n═══ T11: Serialization ═══")
    sd = society.to_dict()
    check("T11: has society_lct", sd["society_lct"] == society.society_lct)
    check("T11: has name", sd["name"] == "Dev Team Alpha")
    check("T11: has phase", sd["phase"] == "operational")
    check("T11: has laws", len(sd["laws"]) > 0)
    check("T11: has treasury", "treasury" in sd)
    check("T11: has citizen_count", "citizen_count" in sd)
    check("T11: has children", len(sd["children"]) > 0)

    # Treasury serialization
    td = society.treasury.to_dict()
    check("T11: treasury has atp_balance", "atp_balance" in td)
    check("T11: treasury has adp_pool", "adp_pool" in td)

    # Citizen serialization
    alice = society.citizens["lct:web4:human:alice"]
    cd = alice.to_dict()
    check("T11: citizen has entity_lct", cd["entity_lct"] == "lct:web4:human:alice")
    check("T11: citizen has status", "status" in cd)
    check("T11: citizen has rights", "rights" in cd)

    # Ledger serialization
    ld = society.ledger.to_dict()
    check("T11: ledger has entry_count", ld["entry_count"] == society.ledger.length)
    check("T11: ledger has type", ld["ledger_type"] == "confined")

    # JSON roundtrip
    j = json.dumps(sd)
    parsed = json.loads(j)
    check("T11: JSON roundtrip preserves lct", parsed["society_lct"] == society.society_lct)

    # ── T12: Edge Cases & Robustness ────────────────────────
    print("\n═══ T12: Edge Cases & Robustness ═══")
    # Bootstrap only in genesis
    ok = society.bootstrap(["lct:web4:human:z"])
    check("T12: can't bootstrap in operational", not ok)

    # Non-citizen has no propose rights
    terminated = society.citizens.get("lct:web4:human:dave")
    check("T12: terminated citizen exists", terminated is not None)
    ok = society.propose_law(
        Law(law_id="LAW-X", title="X", content="Y"),
        "lct:web4:human:dave",  # Terminated
    )
    check("T12: terminated citizen can't propose", not ok)

    # Suspended citizen can't receive allocation
    society.apply_for_citizenship("lct:web4:human:george")
    society.accept_citizen("lct:web4:human:george")
    society.suspend_citizen("lct:web4:human:george", "Testing")
    alloc = society.allocate_atp("lct:web4:human:george", 10.0, "Test")
    check("T12: suspended citizen can't receive ATP", alloc is None)

    # Citizen count
    counts = society.citizen_count()
    check("T12: citizen_count has active", "active" in counts)
    check("T12: active citizens exist", counts.get("active", 0) > 0)

    # Active citizens list
    active = society.active_citizens()
    check("T12: active_citizens returns list", len(active) > 0)
    check("T12: all returned are active", all(c.status == CitizenStatus.ACTIVE for c in active))

    # Amend nonexistent entry
    bad_amend = society.ledger.amend("nonexistent", "correction", {}, "test", "LAW-001")
    check("T12: amend nonexistent returns None", bad_amend is None)

    # ── T13: Multi-Society Citizenship (§2.2.1) ─────────────
    print("\n═══ T13: Multi-Society Citizenship ═══")
    other = Society(
        society_lct="lct:web4:society:other",
        name="Other Society",
        founding_law=Law(law_id="O-001", title="Other Charter", content="Rules"),
        initial_atp=500.0,
    )
    other.bootstrap(["lct:web4:human:alice", "lct:web4:human:newguy"])
    other.go_operational()

    # Alice is citizen of both societies
    alice_in_main = society.citizens.get("lct:web4:human:alice")
    alice_in_other = other.citizens.get("lct:web4:human:alice")
    check("T13: alice citizen of main", alice_in_main is not None and alice_in_main.status == CitizenStatus.ACTIVE)
    check("T13: alice citizen of other", alice_in_other is not None and alice_in_other.status == CitizenStatus.ACTIVE)
    check("T13: independent citizenships", alice_in_main is not alice_in_other)

    # Suspend in one doesn't affect other
    other.suspend_citizen("lct:web4:human:alice", "Testing independence")
    check("T13: alice suspended in other", other.citizens["lct:web4:human:alice"].status == CitizenStatus.SUSPENDED)
    check("T13: alice still active in main", society.citizens["lct:web4:human:alice"].status == CitizenStatus.ACTIVE)

    # ══════════════════════════════════════════════════════════
    print(f"""
{'='*60}
  Society Lifecycle — Track R Results
  {passed} passed, {failed} failed out of {passed + failed} checks
{'='*60}
""")

    if failed == 0:
        print("  All checks pass — Society lifecycle fully operational")
        print("  Formation: genesis → bootstrap → operational → dissolved")
        print("  Citizenship: apply → accept/reject → suspend → reinstate/terminate")
        print("  Ledger: hash-chained, 3 types, amendment support")
        print("  Treasury: ATP mint/allocate/recharge, ADP return")
        print("  Fractal: 3-level hierarchy (parent → child → grandchild)")
        print("  Multi-society: independent citizenships")
    else:
        print("  Some checks failed — review output above")

    return passed, failed


if __name__ == "__main__":
    run_tests()
