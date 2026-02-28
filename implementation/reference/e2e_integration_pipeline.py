"""
Web4 End-to-End Integration Pipeline — Session 17, Track 5
==========================================================

Full system integration: entity lifecycle through all layers.
Tests complete flow: entity birth → trust accumulation → ATP earning →
governance participation → privacy-preserving queries → consensus →
cross-federation → audit.

This is the capstone — every prior module participates.

12 sections, ~75 checks expected.
"""

import hashlib
import math
import random
import time as time_module
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict


# ============================================================
# §1 — Entity Lifecycle
# ============================================================

class EntityState(Enum):
    NASCENT = "nascent"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


@dataclass
class Entity:
    entity_id: str
    entity_type: str
    state: EntityState = EntityState.NASCENT
    trust: Dict[str, float] = field(default_factory=lambda: {"talent": 0.5, "training": 0.5, "temperament": 0.5})
    atp_balance: float = 0.0
    lct_id: str = ""
    public_key: str = ""
    created_at: float = 0.0
    witnesses: List[str] = field(default_factory=list)
    society_id: str = ""
    roles: Set[str] = field(default_factory=set)
    reputation_history: List[float] = field(default_factory=list)

    def composite_trust(self) -> float:
        vals = [v for v in self.trust.values() if isinstance(v, (int, float))]
        return sum(vals) / len(vals) if vals else 0.0

    def activate(self) -> bool:
        if self.state == EntityState.NASCENT:
            self.state = EntityState.ACTIVE
            return True
        return False

    def suspend(self) -> bool:
        if self.state == EntityState.ACTIVE:
            self.state = EntityState.SUSPENDED
            return True
        return False

    def revoke(self) -> bool:
        if self.state in [EntityState.ACTIVE, EntityState.SUSPENDED]:
            self.state = EntityState.REVOKED
            return True
        return False

    def reactivate(self) -> bool:
        if self.state == EntityState.SUSPENDED:
            self.state = EntityState.ACTIVE
            return True
        return False


@dataclass
class EntityRegistry:
    entities: Dict[str, Entity] = field(default_factory=dict)
    lct_counter: int = 0

    def create_entity(self, entity_id: str, entity_type: str,
                      initial_atp: float = 100.0, time: float = 0.0) -> Entity:
        self.lct_counter += 1
        lct_id = f"lct:web4:{entity_id}:{self.lct_counter:08d}"
        pk = hashlib.sha256(f"pk:{entity_id}".encode()).hexdigest()[:32]
        entity = Entity(
            entity_id=entity_id, entity_type=entity_type,
            lct_id=lct_id, public_key=pk, created_at=time, atp_balance=initial_atp,
        )
        self.entities[entity_id] = entity
        return entity

    def get(self, entity_id: str) -> Optional[Entity]:
        return self.entities.get(entity_id)

    def active_count(self) -> int:
        return sum(1 for e in self.entities.values() if e.state == EntityState.ACTIVE)


def test_section_1():
    checks = []
    reg = EntityRegistry()
    alice = reg.create_entity("alice", "human", 200.0, time=1000.0)

    checks.append(("entity_created", alice is not None))
    checks.append(("nascent_state", alice.state == EntityState.NASCENT))
    checks.append(("has_lct", len(alice.lct_id) > 0))
    checks.append(("has_pk", len(alice.public_key) == 32))
    checks.append(("initial_trust", abs(alice.composite_trust() - 0.5) < 0.01))

    checks.append(("activate", alice.activate()))
    checks.append(("active_state", alice.state == EntityState.ACTIVE))
    checks.append(("cant_reactivate_active", not alice.reactivate()))
    checks.append(("suspend", alice.suspend()))
    checks.append(("suspended_state", alice.state == EntityState.SUSPENDED))
    checks.append(("reactivate", alice.reactivate()))
    checks.append(("active_again", alice.state == EntityState.ACTIVE))

    alice.suspend()
    checks.append(("revoke_suspended", alice.revoke()))
    checks.append(("revoked_state", alice.state == EntityState.REVOKED))
    checks.append(("cant_reactivate_revoked", not alice.reactivate()))

    return checks


# ============================================================
# §2 — Trust Accumulation Pipeline
# ============================================================

def accumulate_trust(entity: Entity, observations: List[Tuple[str, float]]) -> Dict:
    updates = []
    for dim, quality in observations:
        if dim not in entity.trust:
            continue
        delta = 0.02 * (quality - 0.5)
        old = entity.trust[dim]
        entity.trust[dim] = max(0.0, min(1.0, old + delta))
        updates.append({"dim": dim, "old": old, "new": entity.trust[dim], "delta": entity.trust[dim] - old})
    entity.reputation_history.append(entity.composite_trust())
    return {"updates": updates, "composite": entity.composite_trust(), "history_len": len(entity.reputation_history)}


def test_section_2():
    checks = []
    reg = EntityRegistry()
    bob = reg.create_entity("bob", "ai_agent", 100.0)
    bob.activate()

    result = accumulate_trust(bob, [("talent", 0.9), ("training", 0.8), ("temperament", 0.7)])
    checks.append(("trust_increased", bob.composite_trust() > 0.5))
    checks.append(("all_bounded", all(0 <= v <= 1 for v in bob.trust.values())))
    checks.append(("history_recorded", len(bob.reputation_history) == 1))

    for _ in range(50):
        accumulate_trust(bob, [("talent", 0.95), ("training", 0.9), ("temperament", 0.85)])
    checks.append(("trust_high_after_50", bob.composite_trust() > 0.7))
    checks.append(("trust_capped_at_1", all(v <= 1.0 for v in bob.trust.values())))

    carol = reg.create_entity("carol", "human", 100.0)
    carol.activate()
    for _ in range(30):
        accumulate_trust(carol, [("talent", 0.1), ("training", 0.2)])
    checks.append(("bad_decreases_trust", carol.composite_trust() < 0.5))
    checks.append(("trust_floor_0", all(v >= 0.0 for v in carol.trust.values())))

    return checks


# ============================================================
# §3 — ATP Earning and Spending
# ============================================================

@dataclass
class ATPLedger:
    balances: Dict[str, float] = field(default_factory=dict)
    total_minted: float = 0.0
    total_fees: float = 0.0
    total_staked: float = 0.0
    fee_rate: float = 0.05
    transactions: List[Dict] = field(default_factory=list)

    def mint(self, entity_id: str, amount: float):
        self.balances[entity_id] = self.balances.get(entity_id, 0) + amount
        self.total_minted += amount

    def transfer(self, sender: str, receiver: str, amount: float) -> Dict:
        if amount <= 0:
            return {"success": False, "reason": "non_positive"}
        fee = amount * self.fee_rate
        total = amount + fee
        if self.balances.get(sender, 0) < total:
            return {"success": False, "reason": "insufficient"}
        self.balances[sender] -= total
        self.balances[receiver] = self.balances.get(receiver, 0) + amount
        self.total_fees += fee
        tx = {"sender": sender, "receiver": receiver, "amount": amount, "fee": fee}
        self.transactions.append(tx)
        return {"success": True, **tx}

    def stake(self, entity_id: str, amount: float) -> bool:
        if self.balances.get(entity_id, 0) < amount:
            return False
        self.balances[entity_id] -= amount
        self.total_staked += amount
        return True

    def balance(self, entity_id: str) -> float:
        return self.balances.get(entity_id, 0)

    def conservation_check(self) -> bool:
        total_in_accounts = sum(self.balances.values())
        return abs(total_in_accounts + self.total_fees + self.total_staked - self.total_minted) < 0.01


def earn_atp(entity: Entity, ledger: ATPLedger, task_quality: float,
             base_reward: float = 10.0) -> Dict:
    if entity.state != EntityState.ACTIVE:
        return {"earned": 0, "reason": "not_active"}
    reward = base_reward * task_quality * entity.composite_trust()
    ledger.mint(entity.entity_id, reward)
    entity.atp_balance = ledger.balance(entity.entity_id)
    return {"earned": reward, "new_balance": entity.atp_balance}


def test_section_3():
    checks = []
    reg = EntityRegistry()
    ledger = ATPLedger()

    alice = reg.create_entity("alice", "human")
    alice.activate()
    ledger.mint("alice", 100.0)

    result = earn_atp(alice, ledger, 0.8, 10.0)
    checks.append(("earned_atp", result["earned"] > 0))
    checks.append(("balance_updated", alice.atp_balance > 100.0))

    alice.trust = {"talent": 0.9, "training": 0.9, "temperament": 0.9}
    result_high = earn_atp(alice, ledger, 0.8, 10.0)

    bob = reg.create_entity("bob", "ai_agent")
    bob.activate()
    bob.trust = {"talent": 0.3, "training": 0.3, "temperament": 0.3}
    ledger.mint("bob", 100.0)
    result_low = earn_atp(bob, ledger, 0.8, 10.0)
    checks.append(("trust_amplifies_earnings", result_high["earned"] > result_low["earned"]))

    tx = ledger.transfer("alice", "bob", 50.0)
    checks.append(("transfer_success", tx["success"]))
    checks.append(("fee_charged", tx["fee"] == 2.5))
    checks.append(("conservation", ledger.conservation_check()))

    carol = reg.create_entity("carol", "human")
    result_inactive = earn_atp(carol, ledger, 0.8)
    checks.append(("inactive_cant_earn", result_inactive["earned"] == 0))

    return checks


# ============================================================
# §4 — Governance Participation
# ============================================================

@dataclass
class Proposal:
    proposal_id: str
    proposer: str
    title: str
    votes: Dict[str, Tuple[bool, float]] = field(default_factory=dict)
    status: str = "open"
    atp_stake: float = 0.0

    def tally(self) -> Dict:
        approve = sum(w for _, (v, w) in self.votes.items() if v)
        reject = sum(w for _, (v, w) in self.votes.items() if not v)
        return {"approve": approve, "reject": reject, "total_votes": len(self.votes)}


@dataclass
class GovernanceSystem:
    proposals: Dict[str, Proposal] = field(default_factory=dict)
    min_trust_to_propose: float = 0.3
    min_trust_to_vote: float = 0.1
    proposal_stake: float = 10.0
    proposal_counter: int = 0

    def submit_proposal(self, entity: Entity, title: str, ledger: ATPLedger) -> Optional[Proposal]:
        if entity.state != EntityState.ACTIVE:
            return None
        if entity.composite_trust() < self.min_trust_to_propose:
            return None
        if not ledger.stake(entity.entity_id, self.proposal_stake):
            return None
        self.proposal_counter += 1
        prop = Proposal(
            proposal_id=f"prop_{self.proposal_counter}", proposer=entity.entity_id,
            title=title, atp_stake=self.proposal_stake,
        )
        self.proposals[prop.proposal_id] = prop
        return prop

    def vote(self, proposal_id: str, entity: Entity, approve: bool) -> bool:
        prop = self.proposals.get(proposal_id)
        if not prop or prop.status != "open":
            return False
        if entity.state != EntityState.ACTIVE or entity.composite_trust() < self.min_trust_to_vote:
            return False
        prop.votes[entity.entity_id] = (approve, entity.composite_trust())
        return True

    def resolve(self, proposal_id: str) -> str:
        prop = self.proposals.get(proposal_id)
        if not prop or prop.status != "open":
            return "invalid"
        tally = prop.tally()
        prop.status = "passed" if tally["approve"] > tally["reject"] and tally["total_votes"] >= 2 else "rejected"
        return prop.status


def test_section_4():
    checks = []
    reg = EntityRegistry()
    ledger = ATPLedger()
    gov = GovernanceSystem()

    alice = reg.create_entity("alice", "human")
    alice.activate()
    alice.trust = {"talent": 0.8, "training": 0.7, "temperament": 0.9}
    ledger.mint("alice", 500.0)

    bob = reg.create_entity("bob", "ai_agent")
    bob.activate()
    bob.trust = {"talent": 0.6, "training": 0.5, "temperament": 0.7}
    ledger.mint("bob", 300.0)

    carol = reg.create_entity("carol", "human")
    carol.activate()
    carol.trust = {"talent": 0.05, "training": 0.05, "temperament": 0.05}

    prop = gov.submit_proposal(alice, "Increase rewards", ledger)
    checks.append(("proposal_created", prop is not None))
    checks.append(("stake_deducted", ledger.balance("alice") == 490.0))

    checks.append(("alice_votes", gov.vote(prop.proposal_id, alice, True)))
    checks.append(("bob_votes", gov.vote(prop.proposal_id, bob, True)))
    checks.append(("carol_blocked", not gov.vote(prop.proposal_id, carol, False)))

    status = gov.resolve(prop.proposal_id)
    checks.append(("proposal_passed", status == "passed"))

    low_trust = reg.create_entity("low", "device")
    low_trust.activate()
    low_trust.trust = {"talent": 0.1, "training": 0.1, "temperament": 0.1}
    ledger.mint("low", 500.0)
    checks.append(("low_trust_cant_propose", gov.submit_proposal(low_trust, "Bad", ledger) is None))

    return checks


# ============================================================
# §5 — Privacy-Preserving Queries
# ============================================================

@dataclass
class PrivacyBudget:
    total_epsilon: float = 0.0
    max_epsilon: float = 10.0

    def can_spend(self, epsilon: float) -> bool:
        return self.total_epsilon + epsilon <= self.max_epsilon

    def spend(self, epsilon: float) -> bool:
        if not self.can_spend(epsilon):
            return False
        self.total_epsilon += epsilon
        return True


def private_trust_query(entity: Entity, epsilon: float,
                        budget: PrivacyBudget, rng: random.Random) -> Dict:
    if not budget.spend(epsilon):
        return {"trust": None, "exhausted": True}
    true_trust = entity.composite_trust()
    noise = rng.gauss(0, 1.0 / epsilon)
    noisy_trust = max(0.0, min(1.0, true_trust + noise))
    return {"trust": noisy_trust, "true_trust": true_trust, "error": abs(noisy_trust - true_trust), "exhausted": False}


def test_section_5():
    checks = []
    rng = random.Random(42)

    reg = EntityRegistry()
    alice = reg.create_entity("alice", "human")
    alice.activate()
    alice.trust = {"talent": 0.8, "training": 0.7, "temperament": 0.9}

    budget = PrivacyBudget(max_epsilon=5.0)
    result = private_trust_query(alice, 1.0, budget, rng)
    checks.append(("trust_returned", result["trust"] is not None))
    checks.append(("trust_bounded", 0.0 <= result["trust"] <= 1.0))
    checks.append(("budget_spent", abs(budget.total_epsilon - 1.0) < 0.01))

    budget2 = PrivacyBudget(max_epsilon=0.5)
    r3 = private_trust_query(alice, 1.0, budget2, rng)
    checks.append(("budget_exhausted", r3["exhausted"]))

    errors = []
    budget3 = PrivacyBudget(max_epsilon=200.0)
    for _ in range(50):
        r = private_trust_query(alice, 2.0, budget3, rng)
        if r["trust"] is not None:
            errors.append(r["error"])
    avg_error = sum(errors) / len(errors)
    checks.append(("reasonable_error", avg_error < 0.5))

    return checks


# ============================================================
# §6 — Consensus Integration
# ============================================================

@dataclass
class ConsensusRound:
    round_id: int
    participants: List[Entity] = field(default_factory=list)
    votes: Dict[str, bool] = field(default_factory=dict)
    decided: bool = False
    decision: Optional[bool] = None

    def vote(self, entity: Entity, value: bool) -> bool:
        if entity.state != EntityState.ACTIVE:
            return False
        self.votes[entity.entity_id] = value
        return True

    def decide(self) -> bool:
        if len(self.votes) < 2:
            return False
        approve_weight = sum(
            next((p.composite_trust() for p in self.participants if p.entity_id == eid), 0)
            for eid, v in self.votes.items() if v
        )
        reject_weight = sum(
            next((p.composite_trust() for p in self.participants if p.entity_id == eid), 0)
            for eid, v in self.votes.items() if not v
        )
        self.decided = True
        self.decision = approve_weight > reject_weight
        return True


def test_section_6():
    checks = []
    reg = EntityRegistry()
    entities = []
    for i in range(5):
        e = reg.create_entity(f"node_{i}", "ai_agent")
        e.activate()
        e.trust = {"talent": 0.5 + i * 0.1, "training": 0.5, "temperament": 0.5}
        entities.append(e)

    cr = ConsensusRound(round_id=1, participants=entities)
    for e in entities[:3]:
        cr.vote(e, True)
    for e in entities[3:]:
        cr.vote(e, False)
    checks.append(("consensus_decided", cr.decide()))
    checks.append(("has_decision", cr.decision is not None))

    cr2 = ConsensusRound(round_id=2, participants=entities)
    cr2.vote(entities[4], True)   # trust 0.633 (highest)
    cr2.vote(entities[3], True)   # trust 0.567
    cr2.vote(entities[0], False)  # trust 0.5 (lowest)
    cr2.decide()
    # approve_weight = 0.633+0.567 = 1.2, reject_weight = 0.5
    checks.append(("high_trust_wins", cr2.decision == True))

    inactive = reg.create_entity("inactive", "device")
    cr3 = ConsensusRound(round_id=3, participants=[inactive])
    checks.append(("inactive_cant_vote", not cr3.vote(inactive, True)))

    return checks


# ============================================================
# §7 — Cross-Federation Bridge
# ============================================================

@dataclass
class Federation:
    federation_id: str
    members: Dict[str, Entity] = field(default_factory=dict)
    trust_threshold: float = 0.3
    ledger: Optional[ATPLedger] = None

    def __post_init__(self):
        if self.ledger is None:
            self.ledger = ATPLedger()

    def admit(self, entity: Entity) -> bool:
        if entity.composite_trust() < self.trust_threshold or entity.state != EntityState.ACTIVE:
            return False
        self.members[entity.entity_id] = entity
        return True


def cross_federation_transfer(source_fed: Federation, target_fed: Federation,
                               entity_id: str, amount: float) -> Dict:
    source_entity = source_fed.members.get(entity_id)
    if not source_entity:
        return {"success": False, "reason": "not_member"}
    if source_entity.composite_trust() < 0.5:
        return {"success": False, "reason": "insufficient_trust"}
    if source_fed.ledger.balance(entity_id) < amount * 1.1:
        return {"success": False, "reason": "insufficient_balance"}
    cross_fee = amount * 0.1
    source_fed.ledger.balances[entity_id] -= amount + cross_fee
    source_fed.ledger.total_fees += cross_fee
    target_fed.ledger.balances[entity_id] = target_fed.ledger.balance(entity_id) + amount
    return {"success": True, "amount": amount, "cross_fee": cross_fee}


def test_section_7():
    checks = []
    reg = EntityRegistry()
    fed_a = Federation("federation_a", trust_threshold=0.3)
    fed_b = Federation("federation_b", trust_threshold=0.4)

    alice = reg.create_entity("alice", "human")
    alice.activate()
    alice.trust = {"talent": 0.8, "training": 0.7, "temperament": 0.9}
    fed_a.admit(alice)
    fed_a.ledger.mint("alice", 1000.0)

    bob = reg.create_entity("bob", "ai_agent")
    bob.activate()
    bob.trust = {"talent": 0.6, "training": 0.5, "temperament": 0.7}

    checks.append(("alice_admitted_a", "alice" in fed_a.members))
    checks.append(("bob_admitted_b", fed_b.admit(bob)))

    low = reg.create_entity("low", "device")
    low.activate()
    low.trust = {"talent": 0.1, "training": 0.1, "temperament": 0.1}
    checks.append(("low_rejected", not fed_b.admit(low)))

    result = cross_federation_transfer(fed_a, fed_b, "alice", 100.0)
    checks.append(("cross_fed_success", result["success"]))
    checks.append(("cross_fee_charged", result["cross_fee"] == 10.0))

    low_fed = reg.create_entity("low_fed", "human")
    low_fed.activate()
    low_fed.trust = {"talent": 0.3, "training": 0.3, "temperament": 0.3}
    fed_a.admit(low_fed)
    fed_a.ledger.mint("low_fed", 1000.0)
    result2 = cross_federation_transfer(fed_a, fed_b, "low_fed", 100.0)
    checks.append(("low_trust_cross_blocked", not result2["success"]))

    return checks


# ============================================================
# §8 — Audit Trail
# ============================================================

@dataclass
class AuditEntry:
    timestamp: float
    entity_id: str
    action: str
    details: Dict
    hash: str = ""
    prev_hash: str = ""

    def compute_hash(self):
        data = f"{self.timestamp}:{self.entity_id}:{self.action}:{self.prev_hash}"
        self.hash = hashlib.sha256(data.encode()).hexdigest()


@dataclass
class AuditTrail:
    entries: List[AuditEntry] = field(default_factory=list)
    last_hash: str = "genesis"

    def log(self, entity_id: str, action: str, details: Dict, time: float = 0.0):
        entry = AuditEntry(timestamp=time, entity_id=entity_id, action=action,
                          details=details, prev_hash=self.last_hash)
        entry.compute_hash()
        self.entries.append(entry)
        self.last_hash = entry.hash

    def verify_integrity(self) -> Tuple[bool, int]:
        prev_hash = "genesis"
        for i, entry in enumerate(self.entries):
            if entry.prev_hash != prev_hash:
                return False, i
            expected = hashlib.sha256(
                f"{entry.timestamp}:{entry.entity_id}:{entry.action}:{entry.prev_hash}".encode()
            ).hexdigest()
            if entry.hash != expected:
                return False, i
            prev_hash = entry.hash
        return True, -1

    def entries_for(self, entity_id: str) -> List[AuditEntry]:
        return [e for e in self.entries if e.entity_id == entity_id]


def test_section_8():
    checks = []
    trail = AuditTrail()
    trail.log("alice", "create", {"type": "human"}, 100.0)
    trail.log("alice", "activate", {}, 101.0)
    trail.log("bob", "create", {"type": "ai_agent"}, 102.0)
    trail.log("alice", "transfer", {"to": "bob", "amount": 50}, 103.0)

    checks.append(("entries_logged", len(trail.entries) == 4))
    valid, _ = trail.verify_integrity()
    checks.append(("integrity_valid", valid))

    # Tamper detection
    trail.entries[1].action = "TAMPERED"
    valid2, broken2 = trail.verify_integrity()
    checks.append(("tamper_detected", not valid2))
    checks.append(("tamper_at_1", broken2 == 1))

    # Entity query on fresh trail
    fresh = AuditTrail()
    fresh.log("alice", "create", {}, 1.0)
    fresh.log("bob", "create", {}, 2.0)
    fresh.log("alice", "earn", {"amount": 10}, 3.0)
    checks.append(("alice_entries_2", len(fresh.entries_for("alice")) == 2))

    return checks


# ============================================================
# §9 — Full System Simulation
# ============================================================

def simulate_full_system(num_entities: int, num_rounds: int, rng: random.Random) -> Dict:
    reg = EntityRegistry()
    ledger = ATPLedger()
    gov = GovernanceSystem()
    trail = AuditTrail()
    fed = Federation("main", trust_threshold=0.3)

    entities = []
    for i in range(num_entities):
        e = reg.create_entity(f"e{i}", "ai_agent" if i % 2 == 0 else "human",
                             initial_atp=100.0, time=float(i))
        e.activate()
        ledger.mint(e.entity_id, 100.0)
        fed.admit(e)
        trail.log(e.entity_id, "create", {"type": e.entity_type}, float(i))
        entities.append(e)

    proposals_created = 0
    consensus_decisions = 0
    total_earned = 0.0

    for round_num in range(num_rounds):
        for e in entities:
            q = rng.uniform(0.3, 0.9)
            accumulate_trust(e, [("talent", q), ("training", q*0.9), ("temperament", q*0.95)])

        for e in entities:
            result = earn_atp(e, ledger, rng.uniform(0.5, 1.0))
            total_earned += result.get("earned", 0)

        if round_num % 5 == 0:
            proposer = entities[round_num % num_entities]
            prop = gov.submit_proposal(proposer, f"Proposal {round_num}", ledger)
            if prop:
                proposals_created += 1
                for e in rng.sample(entities, min(5, len(entities))):
                    gov.vote(prop.proposal_id, e, rng.random() > 0.3)
                gov.resolve(prop.proposal_id)

        if round_num % 3 == 0:
            cr = ConsensusRound(round_id=round_num, participants=entities)
            for e in rng.sample(entities, min(5, len(entities))):
                cr.vote(e, rng.random() > 0.4)
            if cr.decide():
                consensus_decisions += 1

        if len(entities) >= 2:
            s = entities[rng.randint(0, len(entities)-1)]
            r = entities[rng.randint(0, len(entities)-1)]
            if s.entity_id != r.entity_id:
                ledger.transfer(s.entity_id, r.entity_id, rng.uniform(1, 20))

    audit_valid, _ = trail.verify_integrity()
    return {
        "entities": num_entities, "rounds": num_rounds,
        "proposals_created": proposals_created,
        "consensus_decisions": consensus_decisions,
        "total_earned": total_earned,
        "conservation": ledger.conservation_check(),
        "audit_valid": audit_valid,
        "federation_members": len(fed.members),
        "trust_mean": sum(e.composite_trust() for e in entities) / num_entities,
    }


def test_section_9():
    checks = []
    rng = random.Random(42)
    result = simulate_full_system(20, 50, rng)

    checks.append(("all_entities", result["entities"] == 20))
    checks.append(("rounds_done", result["rounds"] == 50))
    checks.append(("proposals", result["proposals_created"] > 0))
    checks.append(("consensus", result["consensus_decisions"] > 0))
    checks.append(("atp_earned", result["total_earned"] > 0))
    checks.append(("conservation", result["conservation"]))
    checks.append(("audit_valid", result["audit_valid"]))
    checks.append(("federation", result["federation_members"] > 0))
    checks.append(("trust_evolved", result["trust_mean"] != 0.5))

    return checks


# ============================================================
# §10 — Stress Test
# ============================================================

def test_section_10():
    checks = []
    rng = random.Random(42)

    reg = EntityRegistry()
    ledger = ATPLedger()
    entities = []
    for i in range(100):
        e = reg.create_entity(f"stress_{i}", "ai_agent")
        e.activate()
        ledger.mint(e.entity_id, 1000.0)
        entities.append(e)

    for _ in range(200):
        for e in entities:
            accumulate_trust(e, [("talent", rng.uniform(0.2, 0.8))])

    for _ in range(500):
        s = entities[rng.randint(0, 99)]
        r = entities[rng.randint(0, 99)]
        if s.entity_id != r.entity_id:
            ledger.transfer(s.entity_id, r.entity_id, rng.uniform(0.1, 5.0))

    checks.append(("stress_100", len(entities) == 100))
    checks.append(("trust_bounded", all(0 <= v <= 1 for e in entities for v in e.trust.values())))
    checks.append(("balances_positive", all(ledger.balance(e.entity_id) >= -0.01 for e in entities)))
    checks.append(("conservation", ledger.conservation_check()))
    checks.append(("transactions", len(ledger.transactions) > 100))

    return checks


# ============================================================
# §11 — Error Recovery
# ============================================================

def test_section_11():
    checks = []
    rng = random.Random(42)

    reg = EntityRegistry()
    ledger = ATPLedger()

    alice = reg.create_entity("alice", "human")
    alice.activate()
    checks.append(("double_activate_blocked", not alice.activate()))

    ledger.mint("alice", 100.0)
    result = ledger.transfer("alice", "nonexistent", 10.0)
    checks.append(("transfer_to_new", result["success"]))
    checks.append(("conservation_after", ledger.conservation_check()))

    bob = reg.create_entity("bob", "ai_agent")
    bob.activate()
    bob.revoke()
    checks.append(("revoked_cant_earn", earn_atp(bob, ledger, 0.8)["earned"] == 0))

    budget = PrivacyBudget(max_epsilon=1.0)
    budget.spend(1.0)
    checks.append(("budget_exhausted", not budget.can_spend(0.1)))

    carol = reg.create_entity("carol", "human")
    carol.activate()
    ledger.mint("carol", 100.0)
    checks.append(("continues_after_revoke", earn_atp(carol, ledger, 0.9)["earned"] > 0))

    return checks


# ============================================================
# §12 — Complete E2E Pipeline
# ============================================================

def run_complete_e2e_pipeline(rng: random.Random) -> List[Tuple[str, bool]]:
    checks = []

    reg = EntityRegistry()
    ledger = ATPLedger()
    gov = GovernanceSystem()
    trail = AuditTrail()
    budget = PrivacyBudget(max_epsilon=20.0)
    fed = Federation("main", ledger=ledger)

    # Phase 1: Create entities
    entities = []
    for i in range(10):
        e = reg.create_entity(f"e{i}", "human" if i < 5 else "ai_agent")
        e.activate()
        ledger.mint(e.entity_id, 200.0)
        fed.admit(e)
        trail.log(e.entity_id, "birth", {"type": e.entity_type})
        entities.append(e)
    checks.append(("phase1_entities", len(entities) == 10))

    # Phase 2: Trust
    for _ in range(30):
        for e in entities:
            q = rng.uniform(0.4, 0.9)
            accumulate_trust(e, [("talent", q), ("training", q*0.9), ("temperament", q*0.95)])
    checks.append(("phase2_trust_grown", sum(e.composite_trust() for e in entities) / 10 > 0.5))

    # Phase 3: ATP
    for _ in range(20):
        for e in entities:
            earn_atp(e, ledger, rng.uniform(0.5, 1.0))
    checks.append(("phase3_atp_earned", all(ledger.balance(e.entity_id) > 200 for e in entities)))

    # Phase 4: Governance
    prop = gov.submit_proposal(entities[0], "Upgrade protocol", ledger)
    checks.append(("phase4_proposal", prop is not None))
    for e in entities[1:6]:
        gov.vote(prop.proposal_id, e, True)
    for e in entities[6:]:
        gov.vote(prop.proposal_id, e, False)
    checks.append(("phase4_decided", gov.resolve(prop.proposal_id) in ["passed", "rejected"]))

    # Phase 5: Privacy
    for e in entities[:3]:
        r = private_trust_query(e, 1.0, budget, rng)
        checks.append((f"phase5_{e.entity_id}", r["trust"] is not None))

    # Phase 6: Consensus
    cr = ConsensusRound(round_id=1, participants=entities)
    for e in entities:
        cr.vote(e, rng.random() > 0.3)
    cr.decide()
    checks.append(("phase6_consensus", cr.decided))

    # Phase 7: Cross-federation
    fed_b = Federation("secondary", trust_threshold=0.5, ledger=ledger)
    for e in entities[5:]:
        fed_b.admit(e)
    result = cross_federation_transfer(fed, fed_b, entities[0].entity_id, 50.0)
    checks.append(("phase7_cross_fed", result["success"]))

    # Phase 8: Audit
    checks.append(("phase8_audit", trail.verify_integrity()[0]))

    # Phase 9: Conservation
    checks.append(("phase9_conservation", ledger.conservation_check()))

    # Phase 10: Trust bounded
    checks.append(("phase10_bounded", all(0 <= v <= 1 for e in entities for v in e.trust.values())))

    return checks


def test_section_12():
    return run_complete_e2e_pipeline(random.Random(42))


# ============================================================
# Main runner
# ============================================================

def run_all():
    sections = [
        ("§1 Entity Lifecycle", test_section_1),
        ("§2 Trust Accumulation", test_section_2),
        ("§3 ATP Earning/Spending", test_section_3),
        ("§4 Governance Participation", test_section_4),
        ("§5 Privacy Queries", test_section_5),
        ("§6 Consensus Integration", test_section_6),
        ("§7 Cross-Federation", test_section_7),
        ("§8 Audit Trail", test_section_8),
        ("§9 Full System Simulation", test_section_9),
        ("§10 Stress Test", test_section_10),
        ("§11 Error Recovery", test_section_11),
        ("§12 Complete E2E Pipeline", test_section_12),
    ]

    total = 0
    passed = 0
    failed_checks = []

    for name, fn in sections:
        checks = fn()
        section_pass = sum(1 for _, v in checks if v)
        section_total = len(checks)
        total += section_total
        passed += section_pass
        status = "✓" if section_pass == section_total else "✗"
        print(f"  {status} {name}: {section_pass}/{section_total}")
        for cname, cval in checks:
            if not cval:
                failed_checks.append(f"    FAIL: {name} → {cname}")

    print(f"\nTotal: {passed}/{total}")
    if failed_checks:
        print("\nFailed checks:")
        for f in failed_checks:
            print(f)

    return passed, total


if __name__ == "__main__":
    run_all()
