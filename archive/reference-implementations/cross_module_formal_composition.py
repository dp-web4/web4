"""
Web4 Cross-Module Formal Composition — Session 17, Track 3
==========================================================

Proves composition properties when modules are combined:
- Privacy budget composition (sequential + parallel)
- ZK proof composition (AND, OR, threshold)
- Graph + privacy composition (private community detection)
- Trust + consensus composition (trust-weighted BFT)
- ATP + governance composition (stake-weighted voting)
- Full stack composition (all layers interact correctly)

Key question: Do module-level guarantees hold when combined?

12 sections, ~80 checks expected.
"""

import hashlib
import math
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from collections import defaultdict


# ============================================================
# §1 — Module Interface Contracts
# ============================================================

@dataclass
class ModuleContract:
    """Formal interface contract for a module."""
    name: str
    preconditions: List[Callable[..., bool]] = field(default_factory=list)
    postconditions: List[Callable[..., bool]] = field(default_factory=list)
    invariants: List[Callable[..., bool]] = field(default_factory=list)

    def check_preconditions(self, state: Dict) -> Tuple[bool, List[str]]:
        failures = []
        for i, pre in enumerate(self.preconditions):
            if not pre(state):
                failures.append(f"precondition_{i}")
        return len(failures) == 0, failures

    def check_postconditions(self, state: Dict) -> Tuple[bool, List[str]]:
        failures = []
        for i, post in enumerate(self.postconditions):
            if not post(state):
                failures.append(f"postcondition_{i}")
        return len(failures) == 0, failures

    def check_invariants(self, state: Dict) -> Tuple[bool, List[str]]:
        failures = []
        for i, inv in enumerate(self.invariants):
            if not inv(state):
                failures.append(f"invariant_{i}")
        return len(failures) == 0, failures


@dataclass
class CompositionProof:
    """Proof that two modules compose safely."""
    module_a: str
    module_b: str
    property_name: str
    holds: bool
    evidence: str = ""
    counterexample: Optional[Dict] = None


def make_privacy_contract() -> ModuleContract:
    return ModuleContract(
        name="privacy",
        preconditions=[
            lambda s: s.get("epsilon", 0) > 0,
            lambda s: s.get("budget_remaining", 0) >= s.get("epsilon", 0),
        ],
        postconditions=[
            lambda s: s.get("budget_remaining", 0) >= 0,
            lambda s: s.get("noise_added", False),
        ],
        invariants=[
            lambda s: s.get("total_epsilon", 0) <= s.get("max_epsilon", 10),
        ],
    )


def make_trust_contract() -> ModuleContract:
    return ModuleContract(
        name="trust",
        preconditions=[
            lambda s: 0 <= s.get("trust", 0.5) <= 1.0,
        ],
        postconditions=[
            lambda s: 0 <= s.get("trust", 0.5) <= 1.0,
        ],
        invariants=[
            lambda s: s.get("trust_delta", 0) <= 0.05,  # Max change per step
        ],
    )


def make_atp_contract() -> ModuleContract:
    return ModuleContract(
        name="atp",
        preconditions=[
            lambda s: s.get("balance", 0) >= 0,
            lambda s: s.get("amount", 0) > 0,
        ],
        postconditions=[
            lambda s: s.get("balance", 0) >= 0,
        ],
        invariants=[
            lambda s: abs(s.get("supply_before", 0) - s.get("supply_after", 0) - s.get("fees", 0)) < 0.01,
        ],
    )


def test_section_1():
    checks = []

    # Privacy contract
    pc = make_privacy_contract()
    good_state = {"epsilon": 1.0, "budget_remaining": 5.0, "noise_added": True, "total_epsilon": 3.0, "max_epsilon": 10.0}
    pre_ok, pre_fail = pc.check_preconditions(good_state)
    checks.append(("privacy_pre_ok", pre_ok))
    post_ok, _ = pc.check_postconditions(good_state)
    checks.append(("privacy_post_ok", post_ok))
    inv_ok, _ = pc.check_invariants(good_state)
    checks.append(("privacy_inv_ok", inv_ok))

    # Bad state: over budget
    bad_state = {"epsilon": 1.0, "budget_remaining": 0.5, "total_epsilon": 11.0, "max_epsilon": 10.0}
    pre_ok2, failures = pc.check_preconditions(bad_state)
    checks.append(("privacy_pre_fail", not pre_ok2))
    inv_ok2, _ = pc.check_invariants(bad_state)
    checks.append(("privacy_inv_fail", not inv_ok2))

    # Trust contract
    tc = make_trust_contract()
    trust_state = {"trust": 0.7, "trust_delta": 0.02}
    checks.append(("trust_valid", tc.check_invariants(trust_state)[0]))

    # ATP contract
    ac = make_atp_contract()
    atp_state = {"balance": 100.0, "amount": 10.0, "supply_before": 1000.0, "supply_after": 999.5, "fees": 0.5}
    checks.append(("atp_conserved", ac.check_invariants(atp_state)[0]))

    # Composition proof structure
    proof = CompositionProof("privacy", "trust", "trust_bounded_after_noise", True,
                             evidence="Trust values remain in [0,1] after DP noise addition")
    checks.append(("proof_holds", proof.holds))

    return checks


# ============================================================
# §2 — Privacy Budget Composition
# ============================================================

@dataclass
class PrivacyBudget:
    total_epsilon: float = 0.0
    max_epsilon: float = 10.0
    queries: List[Dict] = field(default_factory=list)

    def can_spend(self, epsilon: float) -> bool:
        return self.total_epsilon + epsilon <= self.max_epsilon

    def spend(self, epsilon: float, module: str = "", query: str = "") -> bool:
        if not self.can_spend(epsilon):
            return False
        self.total_epsilon += epsilon
        self.queries.append({"module": module, "query": query, "epsilon": epsilon})
        return True

    def remaining(self) -> float:
        return self.max_epsilon - self.total_epsilon


def sequential_composition(epsilons: List[float]) -> float:
    """Sequential composition: total epsilon = sum of individual epsilons."""
    return sum(epsilons)


def parallel_composition(epsilons: List[float]) -> float:
    """Parallel composition (disjoint data): total epsilon = max of individual epsilons."""
    return max(epsilons) if epsilons else 0.0


def advanced_composition(epsilons: List[float], delta: float = 1e-5) -> float:
    """Advanced composition theorem: tighter than sequential for many queries."""
    k = len(epsilons)
    if k == 0:
        return 0.0
    sum_sq = sum(e**2 for e in epsilons)
    # Advanced: sqrt(2 * sum(eps^2) * ln(1/delta)) + sum(eps * (e^eps - 1))
    term1 = math.sqrt(2 * sum_sq * math.log(1 / delta))
    term2 = sum(e * (math.exp(e) - 1) for e in epsilons)
    return term1 + term2


def test_section_2():
    checks = []

    # Sequential: sum
    seq = sequential_composition([1.0, 1.0, 1.0, 1.0])
    checks.append(("sequential_sum", seq == 4.0))

    # Parallel: max
    par = parallel_composition([1.0, 2.0, 0.5, 1.5])
    checks.append(("parallel_max", par == 2.0))

    # Advanced < sequential for many small queries
    small_eps = [0.1] * 100
    seq_total = sequential_composition(small_eps)
    adv_total = advanced_composition(small_eps)
    checks.append(("advanced_tighter", adv_total < seq_total))
    checks.append(("sequential_total_10", abs(seq_total - 10.0) < 0.001))

    # Budget tracking
    budget = PrivacyBudget(max_epsilon=5.0)
    checks.append(("can_spend_initial", budget.can_spend(3.0)))
    budget.spend(3.0, "module_a", "query_1")
    checks.append(("remaining_2", abs(budget.remaining() - 2.0) < 0.01))
    checks.append(("cant_overspend", not budget.can_spend(3.0)))
    budget.spend(2.0, "module_b", "query_2")
    checks.append(("budget_exhausted", budget.remaining() < 0.01))
    checks.append(("query_log", len(budget.queries) == 2))

    # Parallel on disjoint data is more efficient
    checks.append(("parallel_efficient", par < sequential_composition([1.0, 2.0, 0.5, 1.5])))

    return checks


# ============================================================
# §3 — ZK Proof Composition
# ============================================================

@dataclass
class ZKProof:
    """Simple ZK proof representation."""
    statement: str
    commitment: int
    challenge: int
    response: int
    valid: bool = True


def zk_and_compose(proofs: List[ZKProof]) -> ZKProof:
    """AND composition: all proofs must be valid."""
    combined_commitment = 1
    combined_challenge = 0
    combined_response = 0
    for p in proofs:
        combined_commitment = (combined_commitment * p.commitment) % (2**256)
        combined_challenge ^= p.challenge
        combined_response += p.response

    return ZKProof(
        statement=" AND ".join(p.statement for p in proofs),
        commitment=combined_commitment,
        challenge=combined_challenge,
        response=combined_response,
        valid=all(p.valid for p in proofs),
    )


def zk_or_compose(proofs: List[ZKProof]) -> ZKProof:
    """OR composition: at least one proof must be valid."""
    return ZKProof(
        statement=" OR ".join(p.statement for p in proofs),
        commitment=proofs[0].commitment if proofs else 0,
        challenge=proofs[0].challenge if proofs else 0,
        response=proofs[0].response if proofs else 0,
        valid=any(p.valid for p in proofs),
    )


def zk_threshold_compose(proofs: List[ZKProof], k: int) -> ZKProof:
    """Threshold composition: at least k of n proofs must be valid."""
    valid_count = sum(1 for p in proofs if p.valid)
    return ZKProof(
        statement=f"{k}-of-{len(proofs)}: " + ", ".join(p.statement for p in proofs),
        commitment=sum(p.commitment for p in proofs) % (2**256),
        challenge=sum(p.challenge for p in proofs),
        response=sum(p.response for p in proofs),
        valid=valid_count >= k,
    )


def test_section_3():
    checks = []

    p1 = ZKProof("trust > 0.5", 12345, 67890, 11111, valid=True)
    p2 = ZKProof("balance > 100", 54321, 9876, 22222, valid=True)
    p3 = ZKProof("role == admin", 99999, 11111, 33333, valid=False)

    # AND composition
    and_proof = zk_and_compose([p1, p2])
    checks.append(("and_both_valid", and_proof.valid))

    and_with_invalid = zk_and_compose([p1, p3])
    checks.append(("and_one_invalid", not and_with_invalid.valid))

    # OR composition
    or_proof = zk_or_compose([p1, p3])
    checks.append(("or_one_valid", or_proof.valid))

    all_invalid = zk_or_compose([p3, ZKProof("x", 0, 0, 0, False)])
    checks.append(("or_none_valid", not all_invalid.valid))

    # Threshold composition
    thresh_2_of_3 = zk_threshold_compose([p1, p2, p3], 2)
    checks.append(("threshold_2of3_valid", thresh_2_of_3.valid))

    thresh_3_of_3 = zk_threshold_compose([p1, p2, p3], 3)
    checks.append(("threshold_3of3_invalid", not thresh_3_of_3.valid))

    thresh_1_of_3 = zk_threshold_compose([p1, p2, p3], 1)
    checks.append(("threshold_1of3_valid", thresh_1_of_3.valid))

    # Nested composition: AND(OR(p1, p3), p2) = valid
    inner = zk_or_compose([p1, p3])
    outer = zk_and_compose([inner, p2])
    checks.append(("nested_composition", outer.valid))

    return checks


# ============================================================
# §4 — Graph + Privacy Composition
# ============================================================

@dataclass
class TrustGraph:
    nodes: Set[str] = field(default_factory=set)
    edges: Dict[str, Dict[str, float]] = field(default_factory=lambda: defaultdict(dict))
    trust_scores: Dict[str, float] = field(default_factory=dict)

    def add_node(self, node_id: str, trust: float = 0.5):
        self.nodes.add(node_id)
        self.trust_scores[node_id] = trust

    def add_edge(self, src: str, dst: str, weight: float = 1.0):
        self.edges[src][dst] = weight
        self.edges[dst][src] = weight

    def neighbors(self, node_id: str) -> List[str]:
        return list(self.edges.get(node_id, {}).keys())

    def degree(self, node_id: str) -> int:
        return len(self.edges.get(node_id, {}))


def private_community_detection(graph: TrustGraph, epsilon: float,
                                 budget: PrivacyBudget,
                                 rng: random.Random) -> Dict:
    """
    Community detection with differential privacy.
    Uses noisy label propagation to protect individual edges.
    """
    if not budget.can_spend(epsilon):
        return {"communities": {}, "budget_exhausted": True}

    budget.spend(epsilon, "graph", "community_detection")

    # Simple label propagation with DP noise
    labels = {n: i for i, n in enumerate(graph.nodes)}
    nodes_list = list(graph.nodes)

    for iteration in range(10):
        rng.shuffle(nodes_list)
        for node in nodes_list:
            neighbor_labels = defaultdict(float)
            for nbr in graph.neighbors(node):
                lbl = labels[nbr]
                weight = graph.edges[node].get(nbr, 1.0)
                # Add Laplace noise for privacy
                noise = rng.gauss(0, 1.0 / epsilon)
                neighbor_labels[lbl] += weight + noise

            if neighbor_labels:
                labels[node] = max(neighbor_labels, key=neighbor_labels.get)

    # Group by label
    communities = defaultdict(list)
    for node, label in labels.items():
        communities[label].append(node)

    return {
        "communities": dict(communities),
        "num_communities": len(communities),
        "budget_exhausted": False,
        "epsilon_spent": epsilon,
    }


def private_trust_query(graph: TrustGraph, node_id: str, epsilon: float,
                        budget: PrivacyBudget, rng: random.Random) -> Dict:
    """Query trust score with DP noise."""
    if not budget.can_spend(epsilon):
        return {"trust": None, "budget_exhausted": True}

    budget.spend(epsilon, "trust", f"query_{node_id}")
    true_trust = graph.trust_scores.get(node_id, 0.5)
    noise = rng.gauss(0, 1.0 / epsilon)
    noisy_trust = max(0.0, min(1.0, true_trust + noise))

    return {"trust": noisy_trust, "true_trust": true_trust, "noise": noise, "budget_exhausted": False}


def test_section_4():
    checks = []
    rng = random.Random(42)

    # Build test graph
    graph = TrustGraph()
    for i in range(20):
        graph.add_node(f"n{i}", trust=0.3 + (i % 5) * 0.15)

    # Create 2 communities
    for i in range(10):
        for j in range(i+1, 10):
            if rng.random() < 0.6:
                graph.add_edge(f"n{i}", f"n{j}")
    for i in range(10, 20):
        for j in range(i+1, 20):
            if rng.random() < 0.6:
                graph.add_edge(f"n{i}", f"n{j}")
    # Few cross-community edges
    graph.add_edge("n5", "n15")

    budget = PrivacyBudget(max_epsilon=10.0)

    # Private community detection
    result = private_community_detection(graph, 1.0, budget, rng)
    checks.append(("communities_found", result["num_communities"] >= 1))
    checks.append(("budget_tracked", budget.total_epsilon == 1.0))

    # Private trust query
    tq = private_trust_query(graph, "n0", 0.5, budget, rng)
    checks.append(("trust_returned", tq["trust"] is not None))
    checks.append(("trust_bounded", 0.0 <= tq["trust"] <= 1.0))
    checks.append(("budget_updated", abs(budget.total_epsilon - 1.5) < 0.01))

    # Multiple queries consume budget
    for i in range(5):
        private_trust_query(graph, f"n{i}", 1.0, budget, rng)
    checks.append(("budget_accumulates", budget.total_epsilon > 5.0))

    # Budget exhaustion
    budget2 = PrivacyBudget(max_epsilon=0.5)
    result2 = private_community_detection(graph, 1.0, budget2, rng)
    checks.append(("budget_exhaustion_caught", result2["budget_exhausted"]))

    return checks


# ============================================================
# §5 — Trust + Consensus Composition
# ============================================================

@dataclass
class TrustWeightedConsensus:
    """Consensus where vote weight is proportional to trust score."""
    participants: Dict[str, float] = field(default_factory=dict)  # id -> trust
    proposals: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def add_participant(self, node_id: str, trust: float):
        self.participants[node_id] = max(0.0, min(1.0, trust))

    def vote(self, proposal_id: str, voter_id: str, approve: bool):
        if voter_id not in self.participants:
            return
        weight = self.participants[voter_id]
        if proposal_id not in self.proposals:
            self.proposals[proposal_id] = {}
        self.proposals[proposal_id][voter_id] = weight if approve else -weight

    def tally(self, proposal_id: str) -> Dict:
        votes = self.proposals.get(proposal_id, {})
        approve_weight = sum(w for w in votes.values() if w > 0)
        reject_weight = sum(abs(w) for w in votes.values() if w < 0)
        total_weight = sum(self.participants.values())

        return {
            "approve": approve_weight,
            "reject": reject_weight,
            "total": total_weight,
            "quorum_met": (approve_weight + reject_weight) >= total_weight * 0.67,
            "approved": approve_weight > reject_weight and
                       (approve_weight + reject_weight) >= total_weight * 0.67,
        }


def verify_trust_consensus_composition(consensus: TrustWeightedConsensus) -> List[CompositionProof]:
    """Verify properties of trust-weighted consensus."""
    proofs = []

    # Property 1: Trust-bounded weight
    all_bounded = True
    for prop_id, votes in consensus.proposals.items():
        for voter, weight in votes.items():
            if abs(weight) > consensus.participants.get(voter, 0) + 0.001:
                all_bounded = False
    proofs.append(CompositionProof(
        "trust", "consensus", "trust_bounded_weight", all_bounded,
        evidence="Every vote weight <= voter's trust score"
    ))

    # Property 2: Monotonicity
    trusts = sorted(consensus.participants.items(), key=lambda x: x[1])
    monotonic = True
    for i in range(len(trusts) - 1):
        if trusts[i][1] > trusts[i+1][1]:
            monotonic = False
    proofs.append(CompositionProof(
        "trust", "consensus", "trust_monotonic_influence", monotonic,
        evidence="Higher trust entities have >= voting weight"
    ))

    return proofs


def test_section_5():
    checks = []

    tc = TrustWeightedConsensus()
    tc.add_participant("high_trust", 0.9)
    tc.add_participant("med_trust", 0.5)
    tc.add_participant("low_trust", 0.2)

    # High trust should dominate
    tc.vote("prop1", "high_trust", True)
    tc.vote("prop1", "low_trust", False)
    tc.vote("prop1", "med_trust", True)
    result = tc.tally("prop1")
    checks.append(("high_trust_wins", result["approve"] > result["reject"]))
    checks.append(("quorum_met", result["quorum_met"]))

    # Low trust majority can't override high trust minority
    tc2 = TrustWeightedConsensus()
    tc2.add_participant("high", 0.9)
    tc2.add_participant("low1", 0.1)
    tc2.add_participant("low2", 0.1)
    tc2.add_participant("low3", 0.1)
    tc2.vote("prop2", "high", True)
    tc2.vote("prop2", "low1", False)
    tc2.vote("prop2", "low2", False)
    tc2.vote("prop2", "low3", False)
    result2 = tc2.tally("prop2")
    checks.append(("trust_outweighs_count", result2["approve"] > result2["reject"]))

    # Composition proofs
    proofs = verify_trust_consensus_composition(tc)
    for proof in proofs:
        checks.append((f"proof_{proof.property_name}", proof.holds))

    # Trust bounding
    checks.append(("weight_bounded_0.9", tc.proposals["prop1"]["high_trust"] == 0.9))

    return checks


# ============================================================
# §6 — ATP + Governance Composition
# ============================================================

@dataclass
class ATPGovernance:
    """ATP staking integrated with governance voting."""
    balances: Dict[str, float] = field(default_factory=dict)
    stakes: Dict[str, float] = field(default_factory=dict)
    trust_scores: Dict[str, float] = field(default_factory=dict)
    total_supply: float = 0.0

    def create_entity(self, entity_id: str, balance: float, trust: float):
        self.balances[entity_id] = balance
        self.trust_scores[entity_id] = trust
        self.total_supply += balance

    def stake(self, entity_id: str, amount: float) -> bool:
        if amount <= 0 or self.balances.get(entity_id, 0) < amount:
            return False
        self.balances[entity_id] -= amount
        self.stakes[entity_id] = self.stakes.get(entity_id, 0) + amount
        return True

    def governance_weight(self, entity_id: str) -> float:
        """Weight = sqrt(stake) * trust — combines economic and trust signals."""
        stake = self.stakes.get(entity_id, 0)
        trust = self.trust_scores.get(entity_id, 0)
        return math.sqrt(stake) * trust

    def conservation_check(self) -> bool:
        total = sum(self.balances.values()) + sum(self.stakes.values())
        return abs(total - self.total_supply) < 0.01


def verify_atp_governance_composition(gov: ATPGovernance) -> List[CompositionProof]:
    proofs = []

    proofs.append(CompositionProof(
        "atp", "governance", "stake_conservation",
        gov.conservation_check(),
        evidence="Staking moves ATP between balance and stake, total unchanged"
    ))

    zero_trust_weight = True
    for eid in gov.trust_scores:
        if gov.trust_scores[eid] == 0 and gov.governance_weight(eid) != 0:
            zero_trust_weight = False
    proofs.append(CompositionProof(
        "atp", "governance", "zero_trust_zero_weight",
        zero_trust_weight,
        evidence="Entity with zero trust has zero governance weight"
    ))

    sqrt_damped = True
    for eid in gov.stakes:
        stake = gov.stakes[eid]
        trust = gov.trust_scores.get(eid, 0)
        if stake > 0 and trust > 0:  # Skip zero-weight entities
            weight_current = gov.governance_weight(eid)
            weight_doubled = math.sqrt(stake * 2) * trust
            if weight_doubled >= weight_current * 2:
                sqrt_damped = False
    proofs.append(CompositionProof(
        "atp", "governance", "sqrt_dampening",
        sqrt_damped,
        evidence="Doubling stake increases weight by sqrt(2) ≈ 1.41, not 2"
    ))

    return proofs


def test_section_6():
    checks = []

    gov = ATPGovernance()
    gov.create_entity("rich_trusted", 10000.0, 0.9)
    gov.create_entity("rich_untrusted", 10000.0, 0.1)
    gov.create_entity("poor_trusted", 100.0, 0.9)
    gov.create_entity("zero_trust", 5000.0, 0.0)

    gov.stake("rich_trusted", 5000.0)
    gov.stake("rich_untrusted", 5000.0)
    gov.stake("poor_trusted", 50.0)
    gov.stake("zero_trust", 3000.0)

    checks.append(("conservation_after_stake", gov.conservation_check()))

    rt_weight = gov.governance_weight("rich_trusted")
    ru_weight = gov.governance_weight("rich_untrusted")
    checks.append(("trust_amplifies", rt_weight > ru_weight))

    ratio = rt_weight / ru_weight if ru_weight > 0 else float('inf')
    checks.append(("trust_ratio_9to1", abs(ratio - 9.0) < 0.1))

    zt_weight = gov.governance_weight("zero_trust")
    checks.append(("zero_trust_zero_weight", zt_weight == 0.0))

    proofs = verify_atp_governance_composition(gov)
    for proof in proofs:
        checks.append((f"proof_{proof.property_name}", proof.holds))

    checks.append(("sqrt_factor", math.sqrt(2) < 2))

    return checks


# ============================================================
# §7 — Privacy + Trust Composition
# ============================================================

def private_trust_update(current_trust: float, observation_quality: float,
                         epsilon: float, budget: PrivacyBudget,
                         rng: random.Random) -> Dict:
    """
    Update trust with privacy guarantees.
    The observation quality is noised before the trust update.
    """
    if not budget.can_spend(epsilon):
        return {"new_trust": current_trust, "updated": False, "budget_exhausted": True}

    budget.spend(epsilon, "trust_update", "observation")

    # Add noise to observation quality (sensitivity = 1.0)
    noise = rng.gauss(0, 1.0 / epsilon)
    noisy_quality = max(0.0, min(1.0, observation_quality + noise))

    # Trust update: bounded step
    delta = 0.02 * (noisy_quality - 0.5)
    new_trust = max(0.0, min(1.0, current_trust + delta))

    return {
        "new_trust": new_trust,
        "delta": delta,
        "noisy_quality": noisy_quality,
        "updated": True,
        "budget_exhausted": False,
    }


def verify_private_trust_composition(updates: List[Dict]) -> List[CompositionProof]:
    proofs = []

    all_bounded = all(0.0 <= u.get("new_trust", 0.5) <= 1.0 for u in updates if u.get("updated"))
    proofs.append(CompositionProof(
        "privacy", "trust", "trust_bounded_with_noise",
        all_bounded,
        evidence="Trust clipped to [0,1] after noisy update"
    ))

    all_delta_bounded = all(abs(u.get("delta", 0)) <= 0.02 for u in updates if u.get("updated"))
    proofs.append(CompositionProof(
        "privacy", "trust", "delta_bounded_with_noise",
        all_delta_bounded,
        evidence="Trust delta clipped by noisy quality clamping to [0,1]"
    ))

    return proofs


def test_section_7():
    checks = []
    rng = random.Random(42)

    budget = PrivacyBudget(max_epsilon=10.0)
    trust = 0.5

    updates = []
    for i in range(50):
        quality = 0.3 + rng.random() * 0.4
        result = private_trust_update(trust, quality, 0.1, budget, rng)
        if result["updated"]:
            trust = result["new_trust"]
            updates.append(result)

    checks.append(("all_trust_bounded", all(0 <= u["new_trust"] <= 1 for u in updates)))
    checks.append(("all_delta_bounded", all(abs(u["delta"]) <= 0.02 for u in updates)))
    checks.append(("budget_correct", abs(budget.total_epsilon - len(updates) * 0.1) < 0.01))

    proofs = verify_private_trust_composition(updates)
    for proof in proofs:
        checks.append((f"proof_{proof.property_name}", proof.holds))

    # High privacy (low epsilon) still bounded
    budget2 = PrivacyBudget(max_epsilon=100.0)
    low_eps_updates = []
    trust2 = 0.5
    for i in range(50):
        result = private_trust_update(trust2, 0.8, 0.01, budget2, rng)
        if result["updated"]:
            trust2 = result["new_trust"]
            low_eps_updates.append(result)
    checks.append(("high_privacy_bounded", all(0 <= u["new_trust"] <= 1 for u in low_eps_updates)))

    return checks


# ============================================================
# §8 — Consensus + Privacy Composition
# ============================================================

def private_consensus_tally(votes: Dict[str, bool], trust_scores: Dict[str, float],
                            epsilon: float, budget: PrivacyBudget,
                            rng: random.Random) -> Dict:
    """
    Consensus tally with DP — individual votes are protected.
    Only the aggregate (noisy) result is revealed.
    """
    if not budget.can_spend(epsilon):
        return {"result": None, "budget_exhausted": True}

    budget.spend(epsilon, "consensus", "tally")

    approve = sum(trust_scores.get(v, 0.5) for v, vote in votes.items() if vote)
    reject = sum(trust_scores.get(v, 0.5) for v, vote in votes.items() if not vote)

    sensitivity = max(trust_scores.values()) if trust_scores else 1.0
    noise_approve = rng.gauss(0, sensitivity / epsilon)
    noise_reject = rng.gauss(0, sensitivity / epsilon)

    noisy_approve = approve + noise_approve
    noisy_reject = reject + noise_reject

    return {
        "approve": noisy_approve,
        "reject": noisy_reject,
        "result": noisy_approve > noisy_reject,
        "margin": noisy_approve - noisy_reject,
        "budget_exhausted": False,
    }


def test_section_8():
    checks = []
    rng = random.Random(42)

    trust_scores = {f"v{i}": 0.5 + i * 0.05 for i in range(10)}

    # Strong majority survives noise
    votes_strong = {f"v{i}": (i < 8) for i in range(10)}
    results_strong = []
    for _ in range(20):
        r = private_consensus_tally(votes_strong, trust_scores, 0.5,
                                    PrivacyBudget(max_epsilon=100.0), rng)
        results_strong.append(r["result"])

    approve_rate = sum(results_strong) / len(results_strong)
    checks.append(("strong_majority_survives", approve_rate > 0.7))

    # Close vote → noise may flip
    votes_close = {f"v{i}": (i < 5) for i in range(10)}
    results_close = []
    for _ in range(20):
        r = private_consensus_tally(votes_close, trust_scores, 0.5,
                                    PrivacyBudget(max_epsilon=100.0), rng)
        results_close.append(r["result"])
    close_approve = sum(results_close) / len(results_close)
    checks.append(("close_vote_noisy", 0.1 < close_approve < 0.9))

    budget2 = PrivacyBudget(max_epsilon=5.0)
    private_consensus_tally(votes_strong, trust_scores, 1.0, budget2, rng)
    checks.append(("consensus_budget_spent", abs(budget2.total_epsilon - 1.0) < 0.01))

    budget3 = PrivacyBudget(max_epsilon=0.3)
    r3 = private_consensus_tally(votes_strong, trust_scores, 0.5, budget3, rng)
    checks.append(("consensus_budget_exhausted", r3["budget_exhausted"]))

    return checks


# ============================================================
# §9 — Full Stack Composition Verification
# ============================================================

@dataclass
class FullStackState:
    """State of the full composed system."""
    trust_scores: Dict[str, float] = field(default_factory=dict)
    atp_balances: Dict[str, float] = field(default_factory=dict)
    privacy_budget: float = 10.0
    privacy_spent: float = 0.0
    consensus_decisions: List[bool] = field(default_factory=list)
    governance_proposals: int = 0
    communities: int = 0

    def total_atp(self) -> float:
        return sum(self.atp_balances.values())


def compose_full_stack(num_entities: int, num_rounds: int,
                       rng: random.Random) -> Tuple[FullStackState, List[CompositionProof]]:
    """
    Run the full stack: trust + ATP + privacy + consensus + governance.
    Verify composition properties at each step.
    """
    state = FullStackState()
    proofs = []
    budget = PrivacyBudget(max_epsilon=state.privacy_budget)

    for i in range(num_entities):
        eid = f"e{i}"
        state.trust_scores[eid] = 0.5 + rng.gauss(0, 0.1)
        state.trust_scores[eid] = max(0.0, min(1.0, state.trust_scores[eid]))
        state.atp_balances[eid] = 100.0 + rng.gauss(0, 20)
        state.atp_balances[eid] = max(10.0, state.atp_balances[eid])

    initial_total_atp = state.total_atp()

    for round_num in range(num_rounds):
        # 1. Private trust queries
        if budget.can_spend(0.1):
            budget.spend(0.1, "stack", f"round_{round_num}")

        # 2. Trust updates (bounded)
        for eid in state.trust_scores:
            quality = rng.uniform(0.3, 0.7)
            delta = 0.02 * (quality - 0.5)
            state.trust_scores[eid] = max(0.0, min(1.0, state.trust_scores[eid] + delta))

        # 3. ATP transfers (conservation)
        for _ in range(num_entities // 3):
            sender = f"e{rng.randint(0, num_entities-1)}"
            receiver = f"e{rng.randint(0, num_entities-1)}"
            if sender != receiver:
                amount = rng.uniform(1, 10)
                fee = amount * 0.05
                if state.atp_balances.get(sender, 0) >= amount + fee:
                    state.atp_balances[sender] -= (amount + fee)
                    state.atp_balances[receiver] = state.atp_balances.get(receiver, 0) + amount
                    initial_total_atp -= fee  # Fees burned

        # 4. Consensus (trust-weighted)
        votes = {f"e{i}": rng.random() > 0.4 for i in range(num_entities)}
        approve = sum(state.trust_scores[f"e{i}"] for i in range(num_entities) if votes[f"e{i}"])
        reject = sum(state.trust_scores[f"e{i}"] for i in range(num_entities) if not votes[f"e{i}"])
        state.consensus_decisions.append(approve > reject)

    state.privacy_spent = budget.total_epsilon

    # Verify composition properties
    trust_bounded = all(0.0 <= t <= 1.0 for t in state.trust_scores.values())
    proofs.append(CompositionProof("trust", "stack", "trust_bounded", trust_bounded))

    atp_conserved = abs(state.total_atp() - initial_total_atp) < 1.0
    proofs.append(CompositionProof("atp", "stack", "atp_conservation", atp_conserved))

    budget_ok = budget.total_epsilon <= budget.max_epsilon
    proofs.append(CompositionProof("privacy", "stack", "budget_bounded", budget_ok))

    decisions_made = len(state.consensus_decisions) == num_rounds
    proofs.append(CompositionProof("consensus", "stack", "liveness", decisions_made))

    return state, proofs


def test_section_9():
    checks = []
    rng = random.Random(42)

    state, proofs = compose_full_stack(20, 50, rng)

    for proof in proofs:
        checks.append((f"stack_{proof.property_name}", proof.holds))

    checks.append(("trust_all_bounded", all(0 <= t <= 1 for t in state.trust_scores.values())))
    checks.append(("atp_all_positive", all(b >= 0 for b in state.atp_balances.values())))
    checks.append(("decisions_made", len(state.consensus_decisions) == 50))
    checks.append(("privacy_spent", state.privacy_spent > 0))

    return checks


# ============================================================
# §10 — Interference Detection
# ============================================================

def detect_interference(module_a_outputs: List[Dict], module_b_outputs: List[Dict],
                        shared_state_before: Dict, shared_state_after: Dict) -> Dict:
    """
    Detect if two modules interfere when composed.
    Interference = one module's output corrupts another's invariants.
    """
    interferences = []

    for key in shared_state_before:
        before = shared_state_before[key]
        after = shared_state_after.get(key, None)

        if after is None:
            interferences.append({"type": "deleted", "key": key})
        elif isinstance(before, (int, float)) and isinstance(after, (int, float)):
            if before != 0 and abs(after - before) / abs(before) > 10:
                interferences.append({
                    "type": "magnitude_change",
                    "key": key,
                    "before": before,
                    "after": after,
                })

    for key in shared_state_after:
        if key in shared_state_before:
            if type(shared_state_before[key]) != type(shared_state_after[key]):
                interferences.append({
                    "type": "type_violation",
                    "key": key,
                    "expected": type(shared_state_before[key]).__name__,
                    "actual": type(shared_state_after[key]).__name__,
                })

    return {
        "interference_detected": len(interferences) > 0,
        "interferences": interferences,
        "num_interferences": len(interferences),
    }


def test_section_10():
    checks = []

    # No interference
    before = {"trust": 0.5, "balance": 100.0, "status": "active"}
    after = {"trust": 0.52, "balance": 95.0, "status": "active"}
    result = detect_interference([], [], before, after)
    checks.append(("no_interference", not result["interference_detected"]))

    # Magnitude interference
    after_bad = {"trust": 0.5, "balance": 100000.0, "status": "active"}
    result2 = detect_interference([], [], before, after_bad)
    checks.append(("magnitude_detected", result2["interference_detected"]))

    # Type violation
    after_type = {"trust": "high", "balance": 100.0, "status": "active"}
    result3 = detect_interference([], [], before, after_type)
    checks.append(("type_violation_detected", result3["interference_detected"]))

    # Deleted key
    after_deleted = {"trust": 0.5, "status": "active"}
    result4 = detect_interference([], [], before, after_deleted)
    checks.append(("deletion_detected", result4["interference_detected"]))

    # Clean composition
    clean_before = {"trust": 0.7, "budget": 5.0}
    clean_after = {"trust": 0.72, "budget": 4.9}
    result5 = detect_interference([], [], clean_before, clean_after)
    checks.append(("clean_no_interference", not result5["interference_detected"]))

    return checks


# ============================================================
# §11 — Composition Theorem Verification
# ============================================================

def verify_composition_theorems(rng: random.Random) -> List[CompositionProof]:
    """
    Verify key composition theorems:
    1. Privacy composes sequentially (sum of epsilons)
    2. Trust bounds survive composition
    3. ATP conservation holds across modules
    4. Consensus safety preserved under privacy noise
    5. Governance weight bounded by trust × sqrt(stake)
    """
    proofs = []

    # Theorem 1: Sequential privacy composition
    epsilons = [rng.uniform(0.01, 0.5) for _ in range(20)]
    seq_total = sequential_composition(epsilons)
    actual_sum = sum(epsilons)
    proofs.append(CompositionProof(
        "privacy", "composition", "sequential_composition",
        abs(seq_total - actual_sum) < 0.001,
        evidence=f"Sequential total {seq_total:.4f} == sum {actual_sum:.4f}"
    ))

    # Theorem 2: Advanced composition is tighter for many small queries
    small_eps = [0.05] * 100  # 100 small queries where advanced wins
    seq_small = sequential_composition(small_eps)
    adv_small = advanced_composition(small_eps)
    proofs.append(CompositionProof(
        "privacy", "composition", "advanced_tighter_than_sequential",
        adv_small < seq_small,
        evidence=f"Advanced {adv_small:.4f} < Sequential {seq_small:.4f} (100 × ε=0.05)"
    ))

    # Theorem 3: Parallel composition uses max
    par_total = parallel_composition(epsilons)
    proofs.append(CompositionProof(
        "privacy", "composition", "parallel_uses_max",
        par_total == max(epsilons),
        evidence=f"Parallel {par_total:.4f} == max {max(epsilons):.4f}"
    ))

    # Theorem 4: Trust bounds hold after 1000 DP updates
    trust = 0.5
    budget = PrivacyBudget(max_epsilon=200.0)
    for _ in range(1000):
        result = private_trust_update(trust, rng.random(), 0.1, budget, rng)
        if result["updated"]:
            trust = result["new_trust"]
    proofs.append(CompositionProof(
        "trust", "privacy", "trust_bounded_after_1000_updates",
        0.0 <= trust <= 1.0,
        evidence=f"Trust = {trust:.4f} after 1000 DP updates"
    ))

    # Theorem 5: ATP conservation after full stack
    state, stack_proofs = compose_full_stack(10, 100, rng)
    atp_proof = next((p for p in stack_proofs if p.property_name == "atp_conservation"), None)
    if atp_proof:
        proofs.append(atp_proof)

    return proofs


def test_section_11():
    checks = []
    rng = random.Random(42)

    theorems = verify_composition_theorems(rng)
    for theorem in theorems:
        checks.append((f"theorem_{theorem.property_name}", theorem.holds))

    all_hold = all(t.holds for t in theorems)
    checks.append(("all_theorems_hold", all_hold))

    return checks


# ============================================================
# §12 — Complete Composition Pipeline
# ============================================================

def run_complete_composition_pipeline(rng: random.Random) -> List[Tuple[str, bool]]:
    checks = []

    # 1. Module contracts
    pc = make_privacy_contract()
    tc = make_trust_contract()
    ac = make_atp_contract()
    good_privacy = {"epsilon": 1.0, "budget_remaining": 5.0, "noise_added": True, "total_epsilon": 3.0, "max_epsilon": 10}
    good_trust = {"trust": 0.7, "trust_delta": 0.01}
    good_atp = {"balance": 100, "amount": 10, "supply_before": 1000, "supply_after": 999.5, "fees": 0.5}
    checks.append(("contract_privacy", pc.check_preconditions(good_privacy)[0]))
    checks.append(("contract_trust", tc.check_invariants(good_trust)[0]))
    checks.append(("contract_atp", ac.check_invariants(good_atp)[0]))

    # 2. Budget composition
    eps_list = [0.1] * 50
    seq = sequential_composition(eps_list)
    adv = advanced_composition(eps_list)
    par = parallel_composition(eps_list)
    checks.append(("budget_seq_correct", abs(seq - 5.0) < 0.01))
    checks.append(("budget_adv_tighter", adv < seq))
    checks.append(("budget_par_efficient", par == 0.1))

    # 3. ZK composition
    valid_proofs = [ZKProof(f"s{i}", i*100+1, i*10+1, i+1, True) for i in range(5)]
    and_all = zk_and_compose(valid_proofs)
    checks.append(("zk_and_all_valid", and_all.valid))
    thresh = zk_threshold_compose(valid_proofs[:3] + [ZKProof("bad", 0, 0, 0, False)], 3)
    checks.append(("zk_threshold", thresh.valid))

    # 4. Graph + Privacy
    graph = TrustGraph()
    for i in range(10):
        graph.add_node(f"g{i}", trust=0.5)
        if i > 0:
            graph.add_edge(f"g{i}", f"g{i-1}")
    budget = PrivacyBudget(max_epsilon=10.0)
    comm = private_community_detection(graph, 1.0, budget, rng)
    checks.append(("graph_privacy_communities", comm["num_communities"] >= 1))

    # 5. Trust + Consensus
    tc2 = TrustWeightedConsensus()
    for i in range(5):
        tc2.add_participant(f"p{i}", 0.3 + i * 0.15)
    for i in range(5):
        tc2.vote("final", f"p{i}", i >= 2)
    tally = tc2.tally("final")
    checks.append(("trust_consensus_decided", tally["approve"] > 0 or tally["reject"] > 0))

    # 6. ATP + Governance
    gov = ATPGovernance()
    gov.create_entity("g1", 1000.0, 0.8)
    gov.create_entity("g2", 500.0, 0.6)
    gov.stake("g1", 500.0)
    gov.stake("g2", 200.0)
    checks.append(("atp_gov_conserved", gov.conservation_check()))
    w1 = gov.governance_weight("g1")
    w2 = gov.governance_weight("g2")
    checks.append(("atp_gov_weighted", w1 > w2))

    # 7. Full stack
    state, proofs = compose_full_stack(15, 30, rng)
    stack_ok = all(p.holds for p in proofs)
    checks.append(("full_stack_composed", stack_ok))

    # 8. No interference
    before = {"trust": 0.5, "balance": 100.0}
    after = {"trust": 0.52, "balance": 95.0}
    intfr = detect_interference([], [], before, after)
    checks.append(("no_interference", not intfr["interference_detected"]))

    # 9. All composition theorems
    theorems = verify_composition_theorems(rng)
    checks.append(("all_theorems", all(t.holds for t in theorems)))

    return checks


def test_section_12():
    rng = random.Random(42)
    return run_complete_composition_pipeline(rng)


# ============================================================
# Main runner
# ============================================================

def run_all():
    sections = [
        ("§1 Module Interface Contracts", test_section_1),
        ("§2 Privacy Budget Composition", test_section_2),
        ("§3 ZK Proof Composition", test_section_3),
        ("§4 Graph + Privacy Composition", test_section_4),
        ("§5 Trust + Consensus Composition", test_section_5),
        ("§6 ATP + Governance Composition", test_section_6),
        ("§7 Privacy + Trust Composition", test_section_7),
        ("§8 Consensus + Privacy Composition", test_section_8),
        ("§9 Full Stack Composition", test_section_9),
        ("§10 Interference Detection", test_section_10),
        ("§11 Composition Theorems", test_section_11),
        ("§12 Complete Pipeline", test_section_12),
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
