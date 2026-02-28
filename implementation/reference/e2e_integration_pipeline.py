"""
Web4 End-to-End Integration Pipeline — Session 17, Track 5
==========================================================

Full integration test: privacy + governance + consensus + economy + deployment.
This chains ALL major subsystems together and verifies end-to-end properties:

1. Entity registration with trust initialization
2. Privacy-preserving trust queries
3. Governance proposal submission and voting
4. Consensus on governance decisions
5. Economic settlement (ATP transfers)
6. Deployment across network regions
7. Cross-module invariant verification

12 sections, ~75 checks expected.
"""

import hashlib
import math
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict


# ============================================================
# §1 — Entity Registration Layer
# ============================================================

class EntityStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


@dataclass
class TrustTensor:
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    def composite(self) -> float:
        return (self.talent + self.training + self.temperament) / 3.0

    def bounded(self) -> bool:
        return all(0 <= v <= 1 for v in [self.talent, self.training, self.temperament])


@dataclass
class Entity:
    entity_id: str
    trust: TrustTensor = field(default_factory=TrustTensor)
    atp_balance: float = 100.0
    status: EntityStatus = EntityStatus.ACTIVE
    roles: Set[str] = field(default_factory=set)
    history: List[Dict] = field(default_factory=list)
    registered_at: float = 0.0

    def is_active(self) -> bool:
        return self.status == EntityStatus.ACTIVE

    def can_propose(self, min_trust: float = 0.3, min_atp: float = 10.0) -> bool:
        return (self.is_active() and
                self.trust.composite() >= min_trust and
                self.atp_balance >= min_atp)

    def can_vote(self, min_trust: float = 0.1) -> bool:
        return self.is_active() and self.trust.composite() >= min_trust


@dataclass
class EntityRegistry:
    entities: Dict[str, Entity] = field(default_factory=dict)
    next_id: int = 0

    def register(self, entity_id: str, initial_trust: TrustTensor = None,
                 initial_atp: float = 100.0, current_time: float = 0.0) -> Entity:
        if entity_id in self.entities:
            return self.entities[entity_id]
        trust = initial_trust or TrustTensor()
        entity = Entity(entity_id=entity_id, trust=trust, atp_balance=initial_atp,
                       registered_at=current_time)
        self.entities[entity_id] = entity
        return entity

    def get(self, entity_id: str) -> Optional[Entity]:
        return self.entities.get(entity_id)

    def active_count(self) -> int:
        return sum(1 for e in self.entities.values() if e.is_active())


def test_section_1():
    checks = []

    registry = EntityRegistry()
    alice = registry.register("alice", TrustTensor(0.8, 0.7, 0.75), 500.0)
    bob = registry.register("bob", TrustTensor(0.6, 0.5, 0.55), 200.0)

    checks.append(("alice_registered", alice.entity_id == "alice"))
    checks.append(("alice_active", alice.is_active()))
    checks.append(("alice_trust_bounded", alice.trust.bounded()))
    checks.append(("alice_can_propose", alice.can_propose()))
    checks.append(("bob_can_vote", bob.can_vote()))
    checks.append(("active_count", registry.active_count() == 2))

    # Low trust can't propose
    newbie = registry.register("newbie", TrustTensor(0.1, 0.1, 0.1), 5.0)
    checks.append(("newbie_cant_propose", not newbie.can_propose()))
    checks.append(("newbie_cant_vote_low", not newbie.can_vote(min_trust=0.2)))

    # Duplicate registration returns existing
    alice2 = registry.register("alice")
    checks.append(("no_duplicate", alice2.atp_balance == 500.0))

    return checks


# ============================================================
# §2 — Privacy-Preserving Trust Query Layer
# ============================================================

@dataclass
class PrivacyLayer:
    """DP-protected trust queries with budget tracking."""
    budget_max: float = 10.0
    budget_used: float = 0.0
    queries: List[Dict] = field(default_factory=list)

    def remaining(self) -> float:
        return self.budget_max - self.budget_used

    def query_mean_trust(self, entities: List[Entity], epsilon: float,
                         rng: random.Random) -> Dict:
        """DP-protected mean trust query."""
        if self.budget_used + epsilon > self.budget_max:
            return {"success": False, "reason": "budget_exceeded"}

        n = len(entities)
        if n == 0:
            return {"success": False, "reason": "no_entities"}

        true_mean = sum(e.trust.composite() for e in entities) / n
        sensitivity = 1.0 / n
        scale = sensitivity / epsilon
        noise = rng.gauss(0, scale * math.sqrt(2))  # Laplace approximation
        noisy_mean = max(0, min(1, true_mean + noise))

        self.budget_used += epsilon
        result = {
            "success": True,
            "noisy_mean": noisy_mean,
            "true_mean": true_mean,
            "epsilon": epsilon,
            "remaining": self.remaining(),
        }
        self.queries.append(result)
        return result

    def query_trust_histogram(self, entities: List[Entity], bins: int,
                              epsilon: float, rng: random.Random) -> Dict:
        """DP-protected trust histogram."""
        if self.budget_used + epsilon > self.budget_max:
            return {"success": False, "reason": "budget_exceeded"}

        composites = [e.trust.composite() for e in entities]
        bin_edges = [i / bins for i in range(bins + 1)]
        true_counts = [0] * bins
        for c in composites:
            idx = min(int(c * bins), bins - 1)
            true_counts[idx] += 1

        # Add Laplace noise to each bin
        sensitivity = 2.0 / len(entities) if entities else 1.0
        scale = sensitivity / epsilon
        noisy_counts = [max(0, round(c + rng.gauss(0, scale * math.sqrt(2))))
                       for c in true_counts]

        self.budget_used += epsilon
        result = {
            "success": True,
            "histogram": noisy_counts,
            "bins": bins,
            "epsilon": epsilon,
            "remaining": self.remaining(),
        }
        self.queries.append(result)
        return result


def test_section_2():
    checks = []
    rng = random.Random(42)

    registry = EntityRegistry()
    for i in range(20):
        trust = TrustTensor(0.4 + rng.random() * 0.4,
                           0.4 + rng.random() * 0.4,
                           0.4 + rng.random() * 0.4)
        registry.register(f"entity_{i}", trust)

    entities = list(registry.entities.values())
    privacy = PrivacyLayer(budget_max=5.0)

    # Mean trust query
    result = privacy.query_mean_trust(entities, 1.0, rng)
    checks.append(("mean_query_success", result["success"]))
    checks.append(("mean_reasonable", 0 <= result["noisy_mean"] <= 1))
    checks.append(("budget_consumed", privacy.budget_used == 1.0))

    # Histogram query
    hist = privacy.query_trust_histogram(entities, 5, 1.0, rng)
    checks.append(("histogram_success", hist["success"]))
    checks.append(("histogram_bins", len(hist["histogram"]) == 5))

    # Budget tracking
    checks.append(("budget_tracked", privacy.budget_used == 2.0))

    # Over-budget rejection
    over = privacy.query_mean_trust(entities, 5.0, rng)
    checks.append(("over_budget_rejected", not over["success"]))

    return checks


# ============================================================
# §3 — Governance Proposal Layer
# ============================================================

class ProposalStatus(Enum):
    OPEN = "open"
    PASSED = "passed"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class Proposal:
    proposal_id: str
    proposer: str
    title: str
    cost: float = 0.0
    status: ProposalStatus = ProposalStatus.OPEN
    votes: Dict[str, Tuple[bool, float]] = field(default_factory=dict)  # voter → (approve, weight)
    created_at: float = 0.0
    deadline: float = 0.0

    def total_weight(self) -> float:
        return sum(w for _, w in self.votes.values())

    def approval_weight(self) -> float:
        return sum(w for approve, w in self.votes.values() if approve)

    def approval_ratio(self) -> float:
        total = self.total_weight()
        return self.approval_weight() / total if total > 0 else 0


@dataclass
class GovernanceLayer:
    proposals: Dict[str, Proposal] = field(default_factory=dict)
    proposal_cost: float = 10.0
    quorum_ratio: float = 0.5
    approval_threshold: float = 0.6
    next_id: int = 0

    def submit_proposal(self, proposer: Entity, title: str, cost: float = 0.0,
                        current_time: float = 0.0,
                        economy: 'EconomyLayer' = None) -> Optional[Proposal]:
        if not proposer.can_propose(min_atp=self.proposal_cost):
            return None

        proposer.atp_balance -= self.proposal_cost
        # Track proposal cost as burned fees for conservation
        if economy is not None:
            economy.total_fees += self.proposal_cost
        prop_id = f"prop_{self.next_id}"
        self.next_id += 1

        proposal = Proposal(
            proposal_id=prop_id,
            proposer=proposer.entity_id,
            title=title,
            cost=cost,
            created_at=current_time,
            deadline=current_time + 100.0,
        )
        self.proposals[prop_id] = proposal
        return proposal

    def vote(self, voter: Entity, proposal_id: str, approve: bool) -> bool:
        if proposal_id not in self.proposals:
            return False
        if not voter.can_vote():
            return False
        proposal = self.proposals[proposal_id]
        if proposal.status != ProposalStatus.OPEN:
            return False
        if voter.entity_id in proposal.votes:
            return False  # Already voted

        weight = voter.trust.composite()
        proposal.votes[voter.entity_id] = (approve, weight)
        return True

    def resolve(self, proposal_id: str, total_weight: float) -> ProposalStatus:
        """Resolve proposal: check quorum and approval threshold."""
        proposal = self.proposals.get(proposal_id)
        if not proposal or proposal.status != ProposalStatus.OPEN:
            return proposal.status if proposal else ProposalStatus.EXPIRED

        if proposal.total_weight() < total_weight * self.quorum_ratio:
            proposal.status = ProposalStatus.EXPIRED
            return ProposalStatus.EXPIRED

        if proposal.approval_ratio() >= self.approval_threshold:
            proposal.status = ProposalStatus.PASSED
        else:
            proposal.status = ProposalStatus.REJECTED

        return proposal.status


def test_section_3():
    checks = []

    registry = EntityRegistry()
    alice = registry.register("alice", TrustTensor(0.8, 0.7, 0.75), 500.0)
    bob = registry.register("bob", TrustTensor(0.6, 0.5, 0.55), 200.0)
    carol = registry.register("carol", TrustTensor(0.7, 0.6, 0.65), 300.0)

    gov = GovernanceLayer()

    # Submit proposal
    prop = gov.submit_proposal(alice, "Upgrade consensus", cost=100.0)
    checks.append(("proposal_submitted", prop is not None))
    checks.append(("alice_charged", alice.atp_balance == 490.0))

    # Vote
    checks.append(("alice_votes", gov.vote(alice, prop.proposal_id, True)))
    checks.append(("bob_votes", gov.vote(bob, prop.proposal_id, True)))
    checks.append(("carol_votes", gov.vote(carol, prop.proposal_id, False)))

    # Duplicate vote blocked
    checks.append(("no_double_vote", not gov.vote(alice, prop.proposal_id, True)))

    # Resolve
    total_weight = sum(e.trust.composite() for e in registry.entities.values())
    status = gov.resolve(prop.proposal_id, total_weight)
    # Alice (0.75) + Bob (0.55) approve = 1.30 vs Carol (0.65) reject
    # Approval ratio = 1.30 / 1.95 ≈ 0.667 > 0.6 threshold
    checks.append(("proposal_passed", status == ProposalStatus.PASSED))

    return checks


# ============================================================
# §4 — Consensus Layer
# ============================================================

@dataclass
class ConsensusLayer:
    """Simplified BFT consensus for governance decisions."""
    node_count: int = 10
    faulty_max: int = 3
    decisions: Dict[str, Any] = field(default_factory=dict)

    def quorum(self) -> int:
        return 2 * self.faulty_max + 1

    def propose_decision(self, decision_id: str, value: Any,
                         supporters: int, rng: random.Random) -> Dict:
        """Propose and attempt to reach consensus."""
        if supporters < self.quorum():
            return {"decided": False, "reason": "insufficient_support"}

        # Simulate message delivery (with some loss)
        delivered = sum(1 for _ in range(supporters) if rng.random() > 0.05)

        if delivered >= self.quorum():
            self.decisions[decision_id] = value
            return {"decided": True, "value": value, "supporters": delivered}

        return {"decided": False, "reason": "delivery_failure", "delivered": delivered}


def test_section_4():
    checks = []
    rng = random.Random(42)

    consensus = ConsensusLayer(node_count=10)
    checks.append(("quorum_7", consensus.quorum() == 7))

    # Sufficient support → consensus
    result = consensus.propose_decision("gov_1", "approve", 9, rng)
    checks.append(("consensus_reached", result["decided"]))

    # Insufficient support → no consensus
    result2 = consensus.propose_decision("gov_2", "reject", 5, rng)
    checks.append(("insufficient_no_consensus", not result2["decided"]))

    # Decision recorded
    checks.append(("decision_recorded", "gov_1" in consensus.decisions))

    return checks


# ============================================================
# §5 — Economic Settlement Layer
# ============================================================

@dataclass
class EconomyLayer:
    """ATP economic settlement."""
    fee_rate: float = 0.05
    total_fees: float = 0.0
    initial_supply: float = 0.0
    transactions: List[Dict] = field(default_factory=list)

    def initialize(self, entities: Dict[str, Entity]):
        self.initial_supply = sum(e.atp_balance for e in entities.values())

    def transfer(self, sender: Entity, receiver: Entity, amount: float) -> Dict:
        fee = amount * self.fee_rate
        total_cost = amount + fee

        if sender.atp_balance < total_cost:
            return {"success": False, "reason": "insufficient_funds"}
        if amount <= 0:
            return {"success": False, "reason": "invalid_amount"}

        sender.atp_balance -= total_cost
        receiver.atp_balance += amount
        self.total_fees += fee

        tx = {
            "success": True,
            "sender": sender.entity_id,
            "receiver": receiver.entity_id,
            "amount": amount,
            "fee": fee,
        }
        self.transactions.append(tx)
        return tx

    def reward(self, entity: Entity, amount: float, source: str = "system"):
        """System reward (from pool, not from another entity)."""
        entity.atp_balance += amount
        self.initial_supply += amount  # System mint

    def conservation_check(self, entities: Dict[str, Entity]) -> Tuple[bool, float]:
        total = sum(e.atp_balance for e in entities.values())
        expected = self.initial_supply - self.total_fees
        diff = abs(total - expected)
        return diff < 0.01, diff


def test_section_5():
    checks = []

    registry = EntityRegistry()
    alice = registry.register("alice", initial_atp=1000.0)
    bob = registry.register("bob", initial_atp=500.0)

    economy = EconomyLayer()
    economy.initialize(registry.entities)

    # Transfer
    result = economy.transfer(alice, bob, 100.0)
    checks.append(("transfer_success", result["success"]))
    checks.append(("fee_charged", result["fee"] == 5.0))
    checks.append(("sender_debited", alice.atp_balance == 895.0))
    checks.append(("receiver_credited", bob.atp_balance == 600.0))

    # Conservation
    conserved, diff = economy.conservation_check(registry.entities)
    checks.append(("conservation_holds", conserved))

    # Insufficient funds
    result2 = economy.transfer(alice, bob, 10000.0)
    checks.append(("insufficient_blocked", not result2["success"]))

    return checks


# ============================================================
# §6 — Deployment Layer
# ============================================================

class Region(Enum):
    US_EAST = "us_east"
    US_WEST = "us_west"
    EU_WEST = "eu_west"
    ASIA_EAST = "asia_east"


@dataclass
class DeploymentLayer:
    """Multi-region deployment simulation."""
    regions: Dict[Region, List[str]] = field(default_factory=dict)
    latency_map: Dict[Tuple[Region, Region], float] = field(default_factory=dict)

    def __post_init__(self):
        self.latency_map = {
            (Region.US_EAST, Region.US_WEST): 35.0,
            (Region.US_EAST, Region.EU_WEST): 45.0,
            (Region.US_EAST, Region.ASIA_EAST): 100.0,
            (Region.US_WEST, Region.EU_WEST): 80.0,
            (Region.US_WEST, Region.ASIA_EAST): 70.0,
            (Region.EU_WEST, Region.ASIA_EAST): 120.0,
        }

    def deploy_entity(self, entity_id: str, region: Region):
        if region not in self.regions:
            self.regions[region] = []
        self.regions[region].append(entity_id)

    def latency(self, r1: Region, r2: Region) -> float:
        if r1 == r2:
            return 2.0  # Intra-region
        key = (min(r1, r2, key=lambda x: x.value),
               max(r1, r2, key=lambda x: x.value))
        return self.latency_map.get(key, self.latency_map.get((key[1], key[0]), 100.0))

    def global_consensus_latency(self) -> float:
        """Estimate global consensus latency (3 phases × max cross-region RTT)."""
        if not self.regions:
            return 0.0
        active_regions = [r for r in self.regions if self.regions[r]]
        if len(active_regions) <= 1:
            return 6.0  # 3 phases × 2ms intra-region

        max_lat = 0.0
        for i, r1 in enumerate(active_regions):
            for r2 in active_regions[i+1:]:
                lat = self.latency(r1, r2)
                max_lat = max(max_lat, lat)

        return max_lat * 3  # 3 phases of BFT


def test_section_6():
    checks = []

    deploy = DeploymentLayer()
    deploy.deploy_entity("alice", Region.US_EAST)
    deploy.deploy_entity("bob", Region.EU_WEST)
    deploy.deploy_entity("carol", Region.ASIA_EAST)

    checks.append(("entities_deployed", len(deploy.regions) == 3))
    checks.append(("intra_region_fast", deploy.latency(Region.US_EAST, Region.US_EAST) == 2.0))

    cross_lat = deploy.latency(Region.US_EAST, Region.ASIA_EAST)
    checks.append(("cross_region_slow", cross_lat > 50.0))

    global_lat = deploy.global_consensus_latency()
    checks.append(("global_consensus_latency", global_lat > 100.0))
    checks.append(("global_vs_local", global_lat > 6.0))

    return checks


# ============================================================
# §7 — Trust Update Pipeline
# ============================================================

def trust_update_pipeline(entity: Entity, action_quality: float,
                          action_type: str, observers: List[Entity]) -> Dict:
    """
    End-to-end trust update pipeline:
    1. Entity performs action
    2. Observers witness and rate
    3. Trust tensor updated
    4. History recorded
    """
    if not entity.is_active():
        return {"success": False, "reason": "entity_inactive"}

    # Determine which dimension to update
    dim_map = {
        "technical": "talent",
        "learning": "training",
        "social": "temperament",
    }
    dimension = dim_map.get(action_type, "temperament")

    # Calculate trust delta from quality and observer count
    base_delta = 0.02 * (action_quality - 0.5)  # Symmetric around 0.5
    observer_weight = min(1.0, len(observers) / 5.0)  # More observers = more impact
    delta = base_delta * observer_weight

    # Apply update
    old_value = getattr(entity.trust, dimension)
    new_value = max(0.0, min(1.0, old_value + delta))
    setattr(entity.trust, dimension, new_value)

    # Record history
    entry = {
        "action_type": action_type,
        "quality": action_quality,
        "dimension": dimension,
        "delta": delta,
        "old_value": old_value,
        "new_value": new_value,
        "observers": len(observers),
    }
    entity.history.append(entry)

    return {"success": True, "update": entry}


def test_section_7():
    checks = []

    registry = EntityRegistry()
    alice = registry.register("alice", TrustTensor(0.5, 0.5, 0.5))
    observers = [registry.register(f"obs_{i}") for i in range(5)]

    # Good technical action increases talent
    result = trust_update_pipeline(alice, 0.9, "technical", observers)
    checks.append(("update_success", result["success"]))
    checks.append(("talent_increased", alice.trust.talent > 0.5))

    # Bad social action decreases temperament
    result2 = trust_update_pipeline(alice, 0.1, "social", observers)
    checks.append(("temperament_decreased", alice.trust.temperament < 0.5))

    # History recorded
    checks.append(("history_recorded", len(alice.history) == 2))

    # Bounded updates
    high_trust = registry.register("high", TrustTensor(0.99, 0.99, 0.99))
    trust_update_pipeline(high_trust, 1.0, "technical", observers)
    checks.append(("trust_capped_at_1", high_trust.trust.talent <= 1.0))

    # No observers = no impact
    result3 = trust_update_pipeline(alice, 0.9, "technical", [])
    checks.append(("no_observers_no_delta", result3["update"]["delta"] == 0.0))

    return checks


# ============================================================
# §8 — Cross-Module State Verification
# ============================================================

def verify_system_state(registry: EntityRegistry,
                        privacy: PrivacyLayer,
                        governance: GovernanceLayer,
                        economy: EconomyLayer) -> Dict:
    """Verify cross-module invariants across the entire system."""
    invariants = {}

    # 1. All trust tensors bounded
    all_bounded = all(e.trust.bounded() for e in registry.entities.values())
    invariants["trust_bounded"] = all_bounded

    # 2. ATP conservation
    conserved, diff = economy.conservation_check(registry.entities)
    invariants["atp_conservation"] = conserved

    # 3. Privacy budget respected
    invariants["privacy_budget"] = privacy.budget_used <= privacy.budget_max

    # 4. No entity has negative ATP
    invariants["atp_non_negative"] = all(
        e.atp_balance >= 0 for e in registry.entities.values())

    # 5. Active entities can participate
    active = [e for e in registry.entities.values() if e.is_active()]
    invariants["active_entities_exist"] = len(active) > 0

    # 6. Governance proposals have valid proposers
    for prop in governance.proposals.values():
        proposer = registry.get(prop.proposer)
        if proposer is None:
            invariants["valid_proposers"] = False
            break
    else:
        invariants["valid_proposers"] = True

    all_hold = all(invariants.values())
    return {
        "invariants": invariants,
        "all_hold": all_hold,
    }


def test_section_8():
    checks = []
    rng = random.Random(42)

    # Set up full system
    registry = EntityRegistry()
    for i in range(10):
        trust = TrustTensor(0.4 + rng.random() * 0.4,
                           0.4 + rng.random() * 0.4,
                           0.4 + rng.random() * 0.4)
        registry.register(f"entity_{i}", trust, 500.0)

    privacy = PrivacyLayer(budget_max=10.0)
    governance = GovernanceLayer()
    economy = EconomyLayer()
    economy.initialize(registry.entities)

    # Run some operations
    entities = list(registry.entities.values())
    privacy.query_mean_trust(entities, 1.0, rng)
    prop = governance.submit_proposal(entities[0], "Test proposal", economy=economy)
    if prop:
        governance.vote(entities[1], prop.proposal_id, True)
    economy.transfer(entities[0], entities[1], 50.0)

    # Verify state
    result = verify_system_state(registry, privacy, governance, economy)
    checks.append(("all_invariants_hold", result["all_hold"]))
    checks.append(("trust_bounded", result["invariants"]["trust_bounded"]))
    checks.append(("atp_conservation", result["invariants"]["atp_conservation"]))
    checks.append(("privacy_budget", result["invariants"]["privacy_budget"]))
    checks.append(("atp_non_negative", result["invariants"]["atp_non_negative"]))
    checks.append(("valid_proposers", result["invariants"]["valid_proposers"]))

    return checks


# ============================================================
# §9 — Attack Simulation in E2E
# ============================================================

def simulate_e2e_attack(registry: EntityRegistry, governance: GovernanceLayer,
                        economy: EconomyLayer, rng: random.Random) -> Dict:
    """
    Simulate an attacker trying to exploit cross-module interactions:
    1. Register sybil identities
    2. Try to pass malicious governance proposal
    3. Try to drain treasury via proposal
    """
    # Create sybils
    sybils = []
    for i in range(5):
        sybil = registry.register(f"sybil_{i}", TrustTensor(0.15, 0.15, 0.15), 50.0)
        sybils.append(sybil)

    # Create honest entities
    honest = []
    for i in range(10):
        h = registry.register(f"honest_{i}", TrustTensor(0.7, 0.7, 0.7), 500.0)
        honest.append(h)

    economy.initialize(registry.entities)

    # Attack 1: Sybils try to propose (should fail — low trust)
    sybil_proposals = []
    for s in sybils:
        prop = governance.submit_proposal(s, "Malicious proposal", cost=100.0)
        sybil_proposals.append(prop)
    sybil_can_propose = any(p is not None for p in sybil_proposals)

    # Attack 2: Even if one sybil proposes, honest majority should reject
    # Manually create a proposal from a higher-trust sybil
    boosted_sybil = registry.register("boosted_sybil", TrustTensor(0.4, 0.4, 0.4), 100.0)
    prop = governance.submit_proposal(boosted_sybil, "Drain treasury", cost=500.0)

    if prop:
        # Sybils vote approve
        for s in sybils:
            governance.vote(s, prop.proposal_id, True)
        governance.vote(boosted_sybil, prop.proposal_id, True)

        # Honest entities vote reject
        for h in honest:
            governance.vote(h, prop.proposal_id, False)

        total_weight = sum(e.trust.composite() for e in registry.entities.values())
        status = governance.resolve(prop.proposal_id, total_weight)
        attack_passed = status == ProposalStatus.PASSED
    else:
        attack_passed = False

    return {
        "sybil_can_propose": sybil_can_propose,
        "attack_proposal_passed": attack_passed,
        "honest_majority_defended": not attack_passed,
        "sybil_count": len(sybils),
        "honest_count": len(honest),
    }


def test_section_9():
    checks = []
    rng = random.Random(42)

    registry = EntityRegistry()
    governance = GovernanceLayer()
    economy = EconomyLayer()

    result = simulate_e2e_attack(registry, governance, economy, rng)
    checks.append(("sybils_cant_propose", not result["sybil_can_propose"]))
    checks.append(("attack_blocked", not result["attack_proposal_passed"]))
    checks.append(("honest_majority_wins", result["honest_majority_defended"]))

    return checks


# ============================================================
# §10 — Multi-Round E2E Simulation
# ============================================================

def run_multi_round_simulation(rounds: int, rng: random.Random) -> Dict:
    """Run a multi-round E2E simulation with all layers interacting."""
    registry = EntityRegistry()
    privacy = PrivacyLayer(budget_max=100.0)
    governance = GovernanceLayer()
    economy = EconomyLayer()
    deploy = DeploymentLayer()

    # Initialize entities across regions
    regions = list(Region)
    for i in range(20):
        trust = TrustTensor(
            0.3 + rng.random() * 0.5,
            0.3 + rng.random() * 0.5,
            0.3 + rng.random() * 0.5,
        )
        entity = registry.register(f"node_{i}", trust, 500.0)
        deploy.deploy_entity(entity.entity_id, regions[i % len(regions)])

    economy.initialize(registry.entities)
    entities = list(registry.entities.values())

    round_results = []
    proposals_created = 0
    transfers_completed = 0

    for r in range(rounds):
        round_data = {"round": r}

        # 1. Privacy query (every 5 rounds)
        if r % 5 == 0 and privacy.remaining() >= 0.5:
            query = privacy.query_mean_trust(entities, 0.5, rng)
            round_data["privacy_query"] = query.get("success")

        # 2. Governance proposal (every 10 rounds)
        if r % 10 == 0:
            proposer = entities[r % len(entities)]
            prop = governance.submit_proposal(proposer, f"Proposal round {r}",
                                                economy=economy)
            if prop:
                proposals_created += 1
                # Random voting
                for e in entities:
                    if e.entity_id != proposer.entity_id and rng.random() > 0.3:
                        governance.vote(e, prop.proposal_id, rng.random() > 0.4)
                total_weight = sum(e.trust.composite() for e in entities)
                governance.resolve(prop.proposal_id, total_weight)

        # 3. Economic activity
        sender = entities[rng.randint(0, len(entities) - 1)]
        receiver = entities[rng.randint(0, len(entities) - 1)]
        if sender.entity_id != receiver.entity_id:
            amount = rng.uniform(1, 20)
            result = economy.transfer(sender, receiver, amount)
            if result["success"]:
                transfers_completed += 1

        # 4. Trust updates
        actor = entities[rng.randint(0, len(entities) - 1)]
        quality = rng.uniform(0.3, 0.8)
        action = rng.choice(["technical", "learning", "social"])
        observers = rng.sample(entities, min(3, len(entities)))
        trust_update_pipeline(actor, quality, action, observers)

        round_results.append(round_data)

    # Final verification
    state = verify_system_state(registry, privacy, governance, economy)

    return {
        "rounds": rounds,
        "entities": len(entities),
        "proposals_created": proposals_created,
        "transfers_completed": transfers_completed,
        "final_state_valid": state["all_hold"],
        "privacy_budget_used": privacy.budget_used,
        "total_fees": economy.total_fees,
        "invariants": state["invariants"],
    }


def test_section_10():
    checks = []
    rng = random.Random(42)

    result = run_multi_round_simulation(100, rng)
    checks.append(("simulation_completed", result["rounds"] == 100))
    checks.append(("proposals_created", result["proposals_created"] > 0))
    checks.append(("transfers_completed", result["transfers_completed"] > 0))
    checks.append(("final_state_valid", result["final_state_valid"]))
    checks.append(("trust_bounded", result["invariants"]["trust_bounded"]))
    checks.append(("atp_conservation", result["invariants"]["atp_conservation"]))
    checks.append(("fees_collected", result["total_fees"] > 0))

    return checks


# ============================================================
# §11 — Stress Test
# ============================================================

def stress_test(entity_count: int, rounds: int, rng: random.Random) -> Dict:
    """High-load stress test with many entities and rapid operations."""
    registry = EntityRegistry()
    economy = EconomyLayer()

    for i in range(entity_count):
        trust = TrustTensor(
            0.3 + rng.random() * 0.5,
            0.3 + rng.random() * 0.5,
            0.3 + rng.random() * 0.5,
        )
        registry.register(f"stress_{i}", trust, 1000.0)

    economy.initialize(registry.entities)
    entities = list(registry.entities.values())

    operations = 0
    for r in range(rounds):
        # Batch transfers
        for _ in range(10):
            s = entities[rng.randint(0, len(entities) - 1)]
            recv = entities[rng.randint(0, len(entities) - 1)]
            if s.entity_id != recv.entity_id:
                economy.transfer(s, recv, rng.uniform(0.1, 5.0))
                operations += 1

        # Batch trust updates
        for _ in range(5):
            actor = entities[rng.randint(0, len(entities) - 1)]
            quality = rng.uniform(0.2, 0.8)
            observers = rng.sample(entities, min(3, len(entities)))
            trust_update_pipeline(actor, quality, "technical", observers)
            operations += 1

    conserved, diff = economy.conservation_check(registry.entities)
    all_bounded = all(e.trust.bounded() for e in entities)
    all_positive = all(e.atp_balance >= -0.01 for e in entities)  # Small float tolerance

    return {
        "entity_count": entity_count,
        "rounds": rounds,
        "operations": operations,
        "conservation": conserved,
        "conservation_diff": diff,
        "trust_bounded": all_bounded,
        "atp_positive": all_positive,
    }


def test_section_11():
    checks = []
    rng = random.Random(42)

    result = stress_test(100, 50, rng)
    checks.append(("stress_conservation", result["conservation"]))
    checks.append(("stress_trust_bounded", result["trust_bounded"]))
    checks.append(("stress_atp_positive", result["atp_positive"]))
    checks.append(("stress_operations", result["operations"] > 500))

    # Larger stress
    result2 = stress_test(200, 20, rng)
    checks.append(("large_conservation", result2["conservation"]))
    checks.append(("large_trust_bounded", result2["trust_bounded"]))

    return checks


# ============================================================
# §12 — Complete E2E Integration Verification
# ============================================================

def run_complete_e2e_pipeline(rng: random.Random) -> List[Tuple[str, bool]]:
    checks = []

    # Phase 1: Entity registration
    registry = EntityRegistry()
    entities = []
    for i in range(15):
        trust = TrustTensor(
            0.4 + rng.random() * 0.4,
            0.4 + rng.random() * 0.4,
            0.4 + rng.random() * 0.4,
        )
        e = registry.register(f"e2e_{i}", trust, 500.0)
        entities.append(e)
    checks.append(("registration", registry.active_count() == 15))

    # Phase 2: Privacy queries
    privacy = PrivacyLayer(budget_max=10.0)
    mean_result = privacy.query_mean_trust(entities, 1.0, rng)
    checks.append(("privacy_query", mean_result["success"]))

    hist_result = privacy.query_trust_histogram(entities, 5, 1.0, rng)
    checks.append(("histogram_query", hist_result["success"]))

    # Phase 3: Governance (economy created early for conservation tracking)
    economy = EconomyLayer()
    economy.initialize(registry.entities)
    governance = GovernanceLayer()
    prop = governance.submit_proposal(entities[0], "Network upgrade", cost=200.0,
                                      economy=economy)
    checks.append(("proposal_created", prop is not None))

    for e in entities[1:]:
        governance.vote(e, prop.proposal_id, rng.random() > 0.3)
    total_weight = sum(e.trust.composite() for e in entities)
    status = governance.resolve(prop.proposal_id, total_weight)
    checks.append(("governance_resolved", status != ProposalStatus.OPEN))

    # Phase 4: Consensus
    consensus = ConsensusLayer(node_count=15)
    decision = consensus.propose_decision(
        "gov_decision_1", {"proposal": prop.proposal_id, "status": status.value},
        supporters=12, rng=rng,
    )
    checks.append(("consensus_reached", decision["decided"]))

    # Phase 5: Economic settlement
    if status == ProposalStatus.PASSED:
        economy.transfer(entities[0], entities[1], 50.0)
    economy.transfer(entities[2], entities[3], 30.0)
    checks.append(("economy_settled", len(economy.transactions) > 0))

    conserved, _ = economy.conservation_check(registry.entities)
    checks.append(("conservation_holds", conserved))

    # Phase 6: Deployment
    deploy = DeploymentLayer()
    regions = list(Region)
    for i, e in enumerate(entities):
        deploy.deploy_entity(e.entity_id, regions[i % len(regions)])
    global_lat = deploy.global_consensus_latency()
    checks.append(("deployment_latency", global_lat > 0))

    # Phase 7: Trust updates
    for e in entities[:5]:
        trust_update_pipeline(e, rng.uniform(0.5, 0.9), "technical",
                            entities[5:10])
    all_bounded = all(e.trust.bounded() for e in entities)
    checks.append(("trust_updates_bounded", all_bounded))

    # Phase 8: Cross-module verification
    state = verify_system_state(registry, privacy, governance, economy)
    checks.append(("cross_module_valid", state["all_hold"]))

    # Phase 9: Attack resistance
    attack = simulate_e2e_attack(EntityRegistry(), GovernanceLayer(), EconomyLayer(), rng)
    checks.append(("attack_defended", attack["honest_majority_defended"]))

    # Phase 10: Multi-round stability
    multi = run_multi_round_simulation(50, rng)
    checks.append(("multi_round_stable", multi["final_state_valid"]))

    return checks


def test_section_12():
    rng = random.Random(42)
    return run_complete_e2e_pipeline(rng)


# ============================================================
# Main runner
# ============================================================

def run_all():
    sections = [
        ("§1 Entity Registration", test_section_1),
        ("§2 Privacy Trust Queries", test_section_2),
        ("§3 Governance Proposals", test_section_3),
        ("§4 Consensus Layer", test_section_4),
        ("§5 Economic Settlement", test_section_5),
        ("§6 Deployment Layer", test_section_6),
        ("§7 Trust Update Pipeline", test_section_7),
        ("§8 Cross-Module Verification", test_section_8),
        ("§9 Attack Simulation", test_section_9),
        ("§10 Multi-Round Simulation", test_section_10),
        ("§11 Stress Test", test_section_11),
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
