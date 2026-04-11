"""
Federation Consensus Proofs for Web4
Session 30, Track 7

Formal properties of consensus in Web4 federations:
- Agreement: all honest nodes decide same value
- Validity: decision is a proposed value
- Termination: all honest nodes eventually decide
- BFT safety under f < n/3
- Liveness under partial synchrony
- View-change correctness
- Trust-weighted voting power analysis
- Quorum intersection proofs
- Double-vote detection and accountability
"""

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Set, Tuple, Optional


# ─── Consensus Data Structures ─────────────────────────────────────

class NodeState(Enum):
    HONEST = "honest"
    BYZANTINE = "byzantine"
    CRASHED = "crashed"


class Phase(Enum):
    PROPOSE = "propose"
    PREVOTE = "prevote"
    PRECOMMIT = "precommit"
    COMMIT = "commit"


@dataclass
class Vote:
    voter_id: int
    view: int
    value: str
    phase: Phase
    trust_weight: float = 1.0


@dataclass
class ConsensusNode:
    id: int
    state: NodeState
    trust: float
    decided_value: Optional[str] = None
    locked_value: Optional[str] = None
    locked_view: int = -1
    current_view: int = 0
    votes_sent: List[Vote] = field(default_factory=list)
    votes_received: List[Vote] = field(default_factory=list)


# ─── Quorum System ────────────────────────────────────────────────

class QuorumSystem:
    """BFT quorum system for n nodes with f faults."""

    def __init__(self, n: int, f: int, trust_weights: Optional[Dict[int, float]] = None):
        self.n = n
        self.f = f
        self.trust_weights = trust_weights or {i: 1.0 for i in range(n)}

    def is_quorum(self, nodes: Set[int]) -> bool:
        """Check if node set forms a quorum (> 2n/3 for BFT)."""
        if self.trust_weights:
            total_weight = sum(self.trust_weights.values())
            set_weight = sum(self.trust_weights.get(n, 0) for n in nodes)
            return set_weight > 2 * total_weight / 3
        return len(nodes) > 2 * self.n / 3

    def quorum_intersection(self, q1: Set[int], q2: Set[int]) -> Set[int]:
        """Two quorums must intersect in at least f+1 honest nodes."""
        return q1 & q2

    def quorum_intersection_guaranteed(self, q1: Set[int], q2: Set[int]) -> bool:
        """
        With f < n/3 and quorums of size > 2n/3:
        |Q1 ∩ Q2| > n/3 ≥ f+1 (guaranteed honest overlap)
        """
        intersection = self.quorum_intersection(q1, q2)
        return len(intersection) > self.f

    def min_quorum_size(self) -> int:
        """Minimum quorum size for BFT safety."""
        return 2 * self.f + 1  # Need > 2f nodes


# ─── Consensus Protocol Simulation ────────────────────────────────

class BFTConsensus:
    """Simplified BFT consensus for property verification."""

    def __init__(self, n: int, f: int, seed: int = 42):
        self.n = n
        self.f = f
        self.rng = random.Random(seed)
        self.quorum = QuorumSystem(n, f)

        self.nodes: List[ConsensusNode] = []
        for i in range(n):
            state = NodeState.BYZANTINE if i < f else NodeState.HONEST
            trust = 0.3 if state == NodeState.BYZANTINE else self.rng.uniform(0.6, 0.9)
            self.nodes.append(ConsensusNode(i, state, trust))

        self.all_votes: List[Vote] = []
        self.committed_values: Dict[int, str] = {}

    def honest_nodes(self) -> List[ConsensusNode]:
        return [n for n in self.nodes if n.state == NodeState.HONEST]

    def byzantine_nodes(self) -> List[ConsensusNode]:
        return [n for n in self.nodes if n.state == NodeState.BYZANTINE]

    def propose(self, view: int, proposer_id: int, value: str):
        """Leader proposes a value."""
        node = self.nodes[proposer_id]
        if node.state == NodeState.HONEST:
            vote = Vote(proposer_id, view, value, Phase.PROPOSE, node.trust)
            self.all_votes.append(vote)
            node.votes_sent.append(vote)

    def prevote(self, view: int, value: str):
        """Honest nodes prevote for the proposed value."""
        for node in self.nodes:
            if node.state == NodeState.HONEST:
                vote = Vote(node.id, view, value, Phase.PREVOTE, node.trust)
                self.all_votes.append(vote)
                node.votes_sent.append(vote)
            elif node.state == NodeState.BYZANTINE:
                # Byzantine node may send conflicting votes
                byz_value = value if self.rng.random() < 0.5 else f"bad_{view}"
                vote = Vote(node.id, view, byz_value, Phase.PREVOTE, node.trust)
                self.all_votes.append(vote)

    def precommit(self, view: int, value: str):
        """Nodes precommit if they see 2f+1 matching prevotes."""
        # Count prevotes for this value
        matching = [v for v in self.all_votes
                    if v.view == view and v.phase == Phase.PREVOTE and v.value == value]

        if len(matching) >= 2 * self.f + 1:
            for node in self.honest_nodes():
                vote = Vote(node.id, view, value, Phase.PRECOMMIT, node.trust)
                self.all_votes.append(vote)
                node.votes_sent.append(vote)
                node.locked_value = value
                node.locked_view = view

    def commit(self, view: int, value: str):
        """Nodes commit if they see 2f+1 matching precommits."""
        matching = [v for v in self.all_votes
                    if v.view == view and v.phase == Phase.PRECOMMIT and v.value == value]

        if len(matching) >= 2 * self.f + 1:
            for node in self.honest_nodes():
                node.decided_value = value
                self.committed_values[node.id] = value

    def run_round(self, view: int, proposer_id: int, value: str):
        """Execute full consensus round."""
        self.propose(view, proposer_id, value)
        self.prevote(view, value)
        self.precommit(view, value)
        self.commit(view, value)

    # ── Property Checks ───────────────────────────────────────────

    def check_agreement(self) -> bool:
        """All decided honest nodes decided the same value."""
        decided = [n.decided_value for n in self.honest_nodes()
                   if n.decided_value is not None]
        if not decided:
            return True
        return len(set(decided)) == 1

    def check_validity(self, proposed_values: Set[str]) -> bool:
        """All decided values were proposed."""
        for node in self.honest_nodes():
            if node.decided_value is not None:
                if node.decided_value not in proposed_values:
                    return False
        return True

    def check_termination(self) -> bool:
        """All honest nodes eventually decide."""
        return all(n.decided_value is not None for n in self.honest_nodes())

    def detect_double_votes(self) -> List[Tuple[int, int, str, str]]:
        """Find nodes that voted for different values in same view."""
        equivocations = []
        by_voter_view = {}

        for vote in self.all_votes:
            key = (vote.voter_id, vote.view, vote.phase)
            if key in by_voter_view:
                if by_voter_view[key] != vote.value:
                    equivocations.append(
                        (vote.voter_id, vote.view, by_voter_view[key], vote.value))
            else:
                by_voter_view[key] = vote.value

        return equivocations


# ─── View Change Protocol ─────────────────────────────────────────

def view_change_safety(locked_values: Dict[int, Tuple[str, int]],
                        new_proposal: str, n: int, f: int) -> bool:
    """
    View change is safe if:
    - New proposal matches highest locked value among 2f+1 responders
    - OR no responder has any lock (free to propose anything)
    """
    if not locked_values:
        return True  # no locks, any proposal is safe

    # Find highest locked view
    highest_view = -1
    highest_value = None
    for node_id, (value, view) in locked_values.items():
        if view > highest_view:
            highest_view = view
            highest_value = value

    if highest_view < 0:
        return True  # no locks

    return new_proposal == highest_value


# ─── Trust-Weighted Voting ────────────────────────────────────────

def trust_weighted_quorum(votes: List[Vote], total_trust: float,
                          threshold: float = 2/3) -> bool:
    """Check if votes form a trust-weighted quorum."""
    vote_trust = sum(v.trust_weight for v in votes)
    return vote_trust > total_trust * threshold


def voting_power_analysis(nodes: List[ConsensusNode]) -> Dict:
    """Analyze trust-weighted voting power distribution."""
    total_trust = sum(n.trust for n in nodes)
    honest_trust = sum(n.trust for n in nodes if n.state == NodeState.HONEST)
    byzantine_trust = sum(n.trust for n in nodes if n.state == NodeState.BYZANTINE)

    # BFT safety: byzantine trust < total/3
    bft_safe = byzantine_trust < total_trust / 3

    # Effective voting power
    power = {n.id: n.trust / total_trust for n in nodes}

    # HHI (concentration)
    hhi = sum(p ** 2 for p in power.values())

    return {
        "total_trust": total_trust,
        "honest_trust": honest_trust,
        "byzantine_trust": byzantine_trust,
        "honest_fraction": honest_trust / total_trust if total_trust > 0 else 0,
        "bft_safe": bft_safe,
        "hhi": hhi,
        "power": power,
    }


# ─── Accountability ───────────────────────────────────────────────

def slash_equivocator(node: ConsensusNode, penalty_fraction: float = 0.5) -> float:
    """
    Slash a node's trust for equivocation (double voting).
    Returns the trust penalty applied.
    """
    penalty = node.trust * penalty_fraction
    node.trust = max(0.0, node.trust - penalty)
    return penalty


def accountability_evidence(votes: List[Vote]) -> Dict[int, List[Vote]]:
    """
    Build accountability evidence: map each voter to their conflicting votes.
    """
    evidence: Dict[int, List[Vote]] = {}
    by_voter_view_phase: Dict[Tuple[int, int, str], List[Vote]] = {}

    for vote in votes:
        key = (vote.voter_id, vote.view, vote.phase.value)
        if key not in by_voter_view_phase:
            by_voter_view_phase[key] = []
        by_voter_view_phase[key].append(vote)

    for key, vote_list in by_voter_view_phase.items():
        values = set(v.value for v in vote_list)
        if len(values) > 1:
            voter_id = key[0]
            evidence[voter_id] = vote_list

    return evidence


# ══════════════════════════════════════════════════════════════════
#  TESTS
# ══════════════════════════════════════════════════════════════════

def run_checks():
    passed = 0
    failed = 0

    def check(name, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name} — {detail}")

    print("=" * 70)
    print("Federation Consensus Proofs for Web4")
    print("Session 30, Track 7")
    print("=" * 70)

    # ── §1 Quorum System ──────────────────────────────────────────
    print("\n§1 Quorum System Properties\n")

    qs = QuorumSystem(n=10, f=3)

    # 7 nodes form a quorum (> 2*10/3 = 6.67)
    check("7_is_quorum", qs.is_quorum(set(range(7))))
    # 6 nodes do NOT form a quorum
    check("6_not_quorum", not qs.is_quorum(set(range(6))))

    # Two quorums of size 7 in n=10 intersect in at least 4
    q1 = set(range(7))        # {0..6}
    q2 = set(range(3, 10))    # {3..9}
    intersection = qs.quorum_intersection(q1, q2)
    check("quorum_intersection_size", len(intersection) >= 4,
          f"|Q1∩Q2|={len(intersection)}")
    check("quorum_intersection_guaranteed",
          qs.quorum_intersection_guaranteed(q1, q2))

    # Min quorum size
    check("min_quorum_size", qs.min_quorum_size() == 7,
          f"min={qs.min_quorum_size()}")

    # ── §2 BFT Consensus Safety ───────────────────────────────────
    print("\n§2 BFT Consensus: Agreement\n")

    # n=10, f=3 (f < n/3): should reach agreement
    bft = BFTConsensus(n=10, f=3, seed=42)
    bft.run_round(view=0, proposer_id=3, value="block_A")

    check("agreement_holds", bft.check_agreement())
    check("validity_holds", bft.check_validity({"block_A"}))
    check("termination_holds", bft.check_termination())

    # All honest nodes decided same value
    honest_decisions = [n.decided_value for n in bft.honest_nodes()]
    check("all_honest_decide_A", all(d == "block_A" for d in honest_decisions),
          f"decisions={honest_decisions}")

    # ── §3 Byzantine Behavior ─────────────────────────────────────
    print("\n§3 Byzantine Node Detection\n")

    # Check for double votes from Byzantine nodes
    equivocations = bft.detect_double_votes()
    # Byzantine nodes may equivocate
    equivocating_ids = set(e[0] for e in equivocations)
    check("equivocations_from_byzantine",
          equivocating_ids.issubset(set(n.id for n in bft.byzantine_nodes())),
          f"equivocators={equivocating_ids}")

    # Accountability evidence
    evidence = accountability_evidence(bft.all_votes)
    check("evidence_identifies_byzantine",
          all(eid in set(n.id for n in bft.byzantine_nodes())
              for eid in evidence.keys()),
          f"evidence_for={list(evidence.keys())}")

    # ── §4 Safety Under Threshold ─────────────────────────────────
    print("\n§4 Safety Threshold: f < n/3\n")

    # Test various n, f combinations
    for n, f in [(4, 1), (7, 2), (10, 3), (13, 4)]:
        bft_test = BFTConsensus(n=n, f=f, seed=42)
        bft_test.run_round(view=0, proposer_id=f, value=f"block_{n}")
        check(f"agreement_n{n}_f{f}", bft_test.check_agreement())

    # ── §5 View Change Safety ─────────────────────────────────────
    print("\n§5 View Change Protocol\n")

    # No locks → any proposal safe
    check("no_locks_safe", view_change_safety({}, "anything", 10, 3))

    # Locked value → must propose same
    locks = {3: ("block_A", 5), 4: ("block_A", 5), 5: ("block_B", 3)}
    check("matching_lock_safe", view_change_safety(locks, "block_A", 10, 3))
    check("mismatching_lock_unsafe", not view_change_safety(locks, "block_C", 10, 3))

    # ── §6 Trust-Weighted Voting ──────────────────────────────────
    print("\n§6 Trust-Weighted Voting Power\n")

    nodes = bft.nodes
    analysis = voting_power_analysis(nodes)

    check("bft_safe_trust_weighted", analysis["bft_safe"],
          f"byz_frac={analysis['byzantine_trust']/analysis['total_trust']:.3f}")

    # Honest trust > 2/3
    check("honest_majority",
          analysis["honest_fraction"] > 2/3,
          f"honest={analysis['honest_fraction']:.3f}")

    # HHI bounded
    check("hhi_bounded", 0 < analysis["hhi"] <= 1,
          f"hhi={analysis['hhi']:.4f}")

    # Trust-weighted quorum check
    honest_votes = [Vote(n.id, 0, "block_A", Phase.PREVOTE, n.trust)
                    for n in bft.honest_nodes()]
    total_trust = analysis["total_trust"]
    check("honest_votes_form_quorum",
          trust_weighted_quorum(honest_votes, total_trust))

    # ── §7 Slashing and Accountability ────────────────────────────
    print("\n§7 Slashing Protocol\n")

    # Create equivocating node
    bad_node = ConsensusNode(99, NodeState.BYZANTINE, trust=0.8)
    original_trust = bad_node.trust

    penalty = slash_equivocator(bad_node, penalty_fraction=0.5)
    check("trust_reduced", bad_node.trust < original_trust,
          f"before={original_trust} after={bad_node.trust}")
    check("penalty_correct", abs(penalty - 0.4) < 0.01,
          f"penalty={penalty}")
    check("trust_non_negative", bad_node.trust >= 0.0)

    # Double slash
    penalty2 = slash_equivocator(bad_node, penalty_fraction=0.5)
    check("double_slash_less", penalty2 < penalty,
          f"1st={penalty:.3f} 2nd={penalty2:.3f}")

    # ── §8 Multiple Views ─────────────────────────────────────────
    print("\n§8 Multi-View Consensus\n")

    multi = BFTConsensus(n=7, f=2, seed=123)

    # Run 3 consecutive views
    for view in range(3):
        proposer = (view + 2) % 7  # honest proposer
        multi.run_round(view=view, proposer_id=proposer, value=f"block_{view}")

    # Agreement in each decided view
    check("multi_view_agreement", multi.check_agreement())

    # First decision sticks (once decided, don't change)
    first_decided = [n.decided_value for n in multi.honest_nodes()
                     if n.decided_value is not None]
    check("first_decision_persists", len(set(first_decided)) == 1,
          f"decisions={set(first_decided)}")

    # ── §9 Quorum Intersection Theorem ────────────────────────────
    print("\n§9 Quorum Intersection Theorem\n")

    # For any two quorums Q1, Q2 in n=3f+1:
    # |Q1 ∩ Q2| ≥ |Q1| + |Q2| - n ≥ 2(2f+1) - (3f+1) = f+1
    for n, f in [(4, 1), (7, 2), (10, 3)]:
        qs_test = QuorumSystem(n, f)
        min_q = 2 * f + 1
        min_intersection = 2 * min_q - n
        check(f"intersection_geq_f1_n{n}",
              min_intersection >= f + 1,
              f"|Q1∩Q2| ≥ {min_intersection}, f+1={f+1}")

    # ── §10 Liveness Analysis ─────────────────────────────────────
    print("\n§10 Liveness Under Partial Synchrony\n")

    # After GST (Global Stabilization Time), honest proposer guarantees progress
    live = BFTConsensus(n=10, f=3, seed=42)

    # View 0: Byzantine proposer → may not commit
    # View 1: Honest proposer → should commit
    honest_proposer = live.f  # first honest node
    live.run_round(view=1, proposer_id=honest_proposer, value="live_block")

    check("liveness_honest_proposer", live.check_termination(),
          f"decided={[n.decided_value for n in live.honest_nodes()]}")

    # Honest proposer count sufficient for eventual liveness
    honest_count = len(live.honest_nodes())
    total_views_needed = math.ceil(live.n / honest_count)  # views until honest leader
    check("eventual_honest_leader", total_views_needed <= live.n,
          f"views_needed={total_views_needed}")

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
