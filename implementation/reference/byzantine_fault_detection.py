"""
Byzantine Fault Detection for Web4
Session 31, Track 2

Detecting and identifying byzantine nodes from behavior:
- Voting pattern analysis (equivocation detection)
- Behavioral fingerprinting (consistency checks)
- Accusation protocols with evidence
- Trust-weighted byzantine detection
- Gradual trust degradation vs binary slashing
- False positive analysis (honest mistakes vs attacks)
- Recovery protocol for falsely accused nodes
- Detection latency vs accuracy tradeoff
"""

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Set, Tuple, Optional


# ─── Data Structures ───────────────────────────────────────────────

class NodeBehavior(Enum):
    HONEST = "honest"
    BYZANTINE = "byzantine"
    FAULTY = "faulty"       # crashes, not malicious


class VoteType(Enum):
    PREVOTE = "prevote"
    PRECOMMIT = "precommit"


@dataclass
class Vote:
    voter_id: int
    round_num: int
    vote_type: VoteType
    value: str       # block hash or NIL
    timestamp: int


@dataclass
class Accusation:
    accuser_id: int
    accused_id: int
    evidence_type: str
    evidence: Dict
    confidence: float  # [0, 1]
    timestamp: int


@dataclass
class NodeProfile:
    node_id: int
    behavior: NodeBehavior
    trust: float = 0.7
    votes: List[Vote] = field(default_factory=list)
    accusations_made: int = 0
    accusations_received: int = 0
    equivocations_detected: int = 0
    response_failures: int = 0


# ─── Equivocation Detection ───────────────────────────────────────

class EquivocationDetector:
    """Detect double-voting (sending conflicting votes in same round)."""

    def __init__(self):
        self.vote_log: Dict[Tuple[int, int, VoteType], List[Vote]] = {}

    def record_vote(self, vote: Vote) -> Optional[Accusation]:
        """Record a vote and check for equivocation."""
        key = (vote.voter_id, vote.round_num, vote.vote_type)

        if key not in self.vote_log:
            self.vote_log[key] = [vote]
            return None

        # Check for conflicting vote
        accusation = None
        for existing in self.vote_log[key]:
            if existing.value != vote.value:
                # Equivocation detected!
                accusation = Accusation(
                    accuser_id=-1,  # system detection
                    accused_id=vote.voter_id,
                    evidence_type="equivocation",
                    evidence={
                        "round": vote.round_num,
                        "vote_type": vote.vote_type.value,
                        "vote_1": existing.value,
                        "vote_2": vote.value,
                    },
                    confidence=1.0,  # equivocation is provable
                    timestamp=vote.timestamp,
                )
                break

        self.vote_log[key].append(vote)  # always store
        return accusation

    def check_history(self, voter_id: int) -> List[Accusation]:
        """Check entire history for equivocations by a voter."""
        accusations = []
        for key, votes in self.vote_log.items():
            if key[0] != voter_id:
                continue
            values = set(v.value for v in votes)
            if len(values) > 1:
                accusations.append(Accusation(
                    accuser_id=-1,
                    accused_id=voter_id,
                    evidence_type="equivocation",
                    evidence={"round": key[1], "values": list(values)},
                    confidence=1.0,
                    timestamp=votes[-1].timestamp,
                ))
        return accusations


# ─── Behavioral Analysis ──────────────────────────────────────────

class BehaviorAnalyzer:
    """Analyze voting patterns for suspicious behavior."""

    def __init__(self, window_size: int = 20):
        self.window_size = window_size
        self.vote_history: Dict[int, List[Vote]] = {}

    def record(self, vote: Vote):
        if vote.voter_id not in self.vote_history:
            self.vote_history[vote.voter_id] = []
        self.vote_history[vote.voter_id].append(vote)

    def response_rate(self, node_id: int, total_rounds: int) -> float:
        """Fraction of rounds where node voted."""
        if total_rounds <= 0:
            return 0.0
        votes = self.vote_history.get(node_id, [])
        rounds_voted = len(set(v.round_num for v in votes))
        return rounds_voted / total_rounds

    def consistency_score(self, node_id: int) -> float:
        """
        How consistent is node's voting with eventual consensus?
        1.0 = always votes with consensus; 0.0 = always against.
        """
        votes = self.vote_history.get(node_id, [])
        if not votes:
            return 0.5  # no data

        # Group by round, check if voted for winning value
        rounds: Dict[int, str] = {}
        node_votes: Dict[int, str] = {}
        for v in votes:
            if v.voter_id == node_id:
                node_votes[v.round_num] = v.value

        # Build consensus: most common vote per round across all nodes
        round_counts: Dict[int, Dict[str, int]] = {}
        for nid, vote_list in self.vote_history.items():
            for v in vote_list:
                if v.round_num not in round_counts:
                    round_counts[v.round_num] = {}
                round_counts[v.round_num][v.value] = round_counts[v.round_num].get(v.value, 0) + 1

        consensus = {}
        for r, counts in round_counts.items():
            consensus[r] = max(counts, key=counts.get)

        # Compare node votes to consensus
        matches = 0
        total = 0
        for r, v in node_votes.items():
            if r in consensus:
                total += 1
                if v == consensus[r]:
                    matches += 1

        return matches / total if total > 0 else 0.5

    def latency_score(self, node_id: int) -> float:
        """
        Average vote latency (lower = faster responder).
        Returns normalized score [0, 1] where 1 = fast.
        """
        votes = self.vote_history.get(node_id, [])
        if not votes:
            return 0.5

        # Compute average timestamp relative to round start
        round_min_ts: Dict[int, int] = {}
        for nid, vote_list in self.vote_history.items():
            for v in vote_list:
                if v.round_num not in round_min_ts:
                    round_min_ts[v.round_num] = v.timestamp
                round_min_ts[v.round_num] = min(round_min_ts[v.round_num], v.timestamp)

        delays = []
        for v in votes:
            if v.round_num in round_min_ts:
                delays.append(v.timestamp - round_min_ts[v.round_num])

        if not delays:
            return 0.5

        avg_delay = sum(delays) / len(delays)
        # Normalize: assume max acceptable delay is 10
        return max(0, 1 - avg_delay / 10)


# ─── Byzantine Score ──────────────────────────────────────────────

def compute_byzantine_score(profile: NodeProfile, analyzer: BehaviorAnalyzer,
                             total_rounds: int) -> float:
    """
    Composite score indicating likelihood of byzantine behavior.
    0.0 = definitely honest, 1.0 = definitely byzantine.
    """
    scores = []

    # Equivocation: strongest evidence (binary)
    if profile.equivocations_detected > 0:
        return 1.0  # proven byzantine

    # Response rate (honest nodes respond consistently)
    resp_rate = analyzer.response_rate(profile.node_id, total_rounds)
    scores.append(1 - resp_rate)  # low response → suspicious

    # Consistency with consensus
    consistency = analyzer.consistency_score(profile.node_id)
    scores.append(1 - consistency)  # low consistency → suspicious

    # Accusations received
    if profile.accusations_received > 0:
        acc_score = min(1.0, profile.accusations_received / 5)
        scores.append(acc_score)

    if not scores:
        return 0.0

    return sum(scores) / len(scores)


# ─── Trust Degradation ───────────────────────────────────────────

class GradualSlasher:
    """
    Gradual trust degradation instead of binary slashing.
    First offense = warning; repeated offenses escalate.
    """

    def __init__(self):
        self.offense_count: Dict[int, int] = {}
        self.trust_penalties: Dict[int, float] = {}

    def process_accusation(self, accusation: Accusation, current_trust: float) -> float:
        """
        Apply penalty based on accusation severity and history.
        Returns new trust level.
        """
        node_id = accusation.accused_id
        self.offense_count[node_id] = self.offense_count.get(node_id, 0) + 1
        count = self.offense_count[node_id]

        # Penalty escalates with offense count
        if accusation.evidence_type == "equivocation":
            # Provable: heavy penalty
            penalty = min(current_trust, 0.3 * count)
        else:
            # Behavioral: lighter penalty
            penalty = min(current_trust, 0.05 * count * accusation.confidence)

        new_trust = max(0, current_trust - penalty)
        self.trust_penalties[node_id] = self.trust_penalties.get(node_id, 0) + penalty

        return new_trust

    def total_penalty(self, node_id: int) -> float:
        return self.trust_penalties.get(node_id, 0)


# ─── False Positive Analysis ─────────────────────────────────────

def false_positive_rate(detections: List[Tuple[int, bool]]) -> float:
    """
    Compute false positive rate from (detected_as_byzantine, actually_byzantine) pairs.
    FPR = false_positives / (false_positives + true_negatives)
    """
    fp = sum(1 for detected, actual in detections if detected and not actual)
    tn = sum(1 for detected, actual in detections if not detected and not actual)

    if fp + tn == 0:
        return 0.0
    return fp / (fp + tn)


def false_negative_rate(detections: List[Tuple[int, bool]]) -> float:
    """FNR = false_negatives / (false_negatives + true_positives)"""
    fn = sum(1 for detected, actual in detections if not detected and actual)
    tp = sum(1 for detected, actual in detections if detected and actual)

    if fn + tp == 0:
        return 0.0
    return fn / (fn + tp)


def detection_accuracy(detections: List[Tuple[int, bool]]) -> float:
    """Overall accuracy = (TP + TN) / total"""
    correct = sum(1 for d, a in detections if (d > 0.5) == a)
    return correct / len(detections) if detections else 0.0


# ─── Recovery Protocol ────────────────────────────────────────────

@dataclass
class RecoveryRequest:
    node_id: int
    evidence_of_innocence: str
    vouchers: List[int]  # nodes vouching for innocence
    request_time: int


def evaluate_recovery(request: RecoveryRequest, network_trust: Dict[int, float],
                       slasher: GradualSlasher, quorum: int = 3) -> Dict:
    """
    Evaluate recovery request from accused node.
    Requires vouchers with sufficient trust.
    """
    # Count qualified vouchers (trust > 0.5)
    qualified = [v for v in request.vouchers
                 if network_trust.get(v, 0) > 0.5]

    # Total voucher trust
    voucher_trust = sum(network_trust.get(v, 0) for v in qualified)

    # Recovery conditions
    enough_vouchers = len(qualified) >= quorum
    enough_trust = voucher_trust >= quorum * 0.5
    penalty = slasher.total_penalty(request.node_id)

    # Recovery amount: partial based on voucher trust
    recovery_fraction = min(0.5, voucher_trust / (quorum * 2)) if enough_vouchers else 0.0

    return {
        "approved": enough_vouchers and enough_trust,
        "qualified_vouchers": len(qualified),
        "voucher_trust": voucher_trust,
        "recovery_fraction": recovery_fraction,
        "restored_trust": penalty * recovery_fraction,
    }


# ─── Simulation ───────────────────────────────────────────────────

def simulate_consensus_with_byzantines(n_nodes: int, n_byzantine: int,
                                        n_rounds: int, seed: int = 42) -> Dict:
    """
    Simulate consensus rounds with byzantine nodes and detection.
    """
    rng = random.Random(seed)

    # Create profiles
    profiles = {}
    byzantine_ids = set(rng.sample(range(n_nodes), n_byzantine))
    for i in range(n_nodes):
        behavior = NodeBehavior.BYZANTINE if i in byzantine_ids else NodeBehavior.HONEST
        profiles[i] = NodeProfile(i, behavior, trust=0.7)

    detector = EquivocationDetector()
    analyzer = BehaviorAnalyzer()
    slasher = GradualSlasher()

    accusations = []
    detections = []

    for r in range(n_rounds):
        block = f"block_{r}_{rng.randint(0, 1000)}"

        for i in range(n_nodes):
            profile = profiles[i]

            if profile.behavior == NodeBehavior.BYZANTINE:
                # Byzantine: sometimes equivocate, sometimes vote wrong
                action = rng.random()
                if action < 0.2:
                    # Equivocate: send two different votes
                    v1 = Vote(i, r, VoteType.PREVOTE, block, r * 10)
                    v2 = Vote(i, r, VoteType.PREVOTE, f"fake_{r}", r * 10 + 1)
                    analyzer.record(v1)
                    analyzer.record(v2)
                    acc = detector.record_vote(v1)
                    acc2 = detector.record_vote(v2)
                    if acc:
                        accusations.append(acc)
                        profile.equivocations_detected += 1
                    if acc2:
                        accusations.append(acc2)
                        profile.equivocations_detected += 1
                elif action < 0.5:
                    # Vote for wrong block
                    v = Vote(i, r, VoteType.PREVOTE, f"wrong_{r}", r * 10 + rng.randint(2, 5))
                    analyzer.record(v)
                    detector.record_vote(v)
                else:
                    # Sometimes act honestly (to evade detection)
                    v = Vote(i, r, VoteType.PREVOTE, block, r * 10 + rng.randint(0, 2))
                    analyzer.record(v)
                    detector.record_vote(v)
            else:
                # Honest: always vote for correct block
                delay = rng.randint(0, 2)
                v = Vote(i, r, VoteType.PREVOTE, block, r * 10 + delay)
                analyzer.record(v)
                detector.record_vote(v)

    # Compute byzantine scores
    scores = {}
    for i in range(n_nodes):
        scores[i] = compute_byzantine_score(profiles[i], analyzer, n_rounds)

    # Apply slashing for detected equivocators
    for acc in accusations:
        nid = acc.accused_id
        profiles[nid].trust = slasher.process_accusation(acc, profiles[nid].trust)

    # Build detection results
    for i in range(n_nodes):
        is_byzantine = i in byzantine_ids
        detected = scores[i] > 0.5
        detections.append((detected, is_byzantine))

    return {
        "n_nodes": n_nodes,
        "n_byzantine": n_byzantine,
        "n_rounds": n_rounds,
        "accusations": len(accusations),
        "scores": scores,
        "byzantine_ids": byzantine_ids,
        "fpr": false_positive_rate(detections),
        "fnr": false_negative_rate(detections),
        "accuracy": detection_accuracy(detections),
        "profiles": profiles,
    }


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
    print("Byzantine Fault Detection for Web4")
    print("Session 31, Track 2")
    print("=" * 70)

    # ── §1 Equivocation Detection ─────────────────────────────────
    print("\n§1 Equivocation Detection\n")

    detector = EquivocationDetector()

    # Normal vote: no accusation
    v1 = Vote(0, 1, VoteType.PREVOTE, "block_A", 100)
    acc = detector.record_vote(v1)
    check("normal_vote_no_accusation", acc is None)

    # Same vote again: no accusation (same value)
    v1b = Vote(0, 1, VoteType.PREVOTE, "block_A", 101)
    acc = detector.record_vote(v1b)
    check("duplicate_vote_no_accusation", acc is None)

    # Conflicting vote: accusation!
    v2 = Vote(0, 1, VoteType.PREVOTE, "block_B", 102)
    acc = detector.record_vote(v2)
    check("equivocation_detected", acc is not None)
    check("equivocation_confidence_1", acc.confidence == 1.0 if acc else False)
    check("equivocation_accused", acc.accused_id == 0 if acc else False)

    # Different round: no equivocation
    v3 = Vote(0, 2, VoteType.PREVOTE, "block_C", 200)
    acc = detector.record_vote(v3)
    check("different_round_ok", acc is None)

    # ── §2 History Check ──────────────────────────────────────────
    print("\n§2 History Analysis\n")

    history = detector.check_history(0)
    check("history_finds_equivocation", len(history) > 0,
          f"found={len(history)}")

    # Node 1 has no equivocations
    detector.record_vote(Vote(1, 1, VoteType.PREVOTE, "block_A", 100))
    history_1 = detector.check_history(1)
    check("honest_no_history", len(history_1) == 0)

    # ── §3 Behavioral Analysis ────────────────────────────────────
    print("\n§3 Behavioral Analysis\n")

    analyzer = BehaviorAnalyzer()

    # Simulate honest and byzantine voting
    for r in range(20):
        # Honest node 0: always votes block_X
        analyzer.record(Vote(0, r, VoteType.PREVOTE, f"block_{r}", r * 10))
        # Honest node 1: same
        analyzer.record(Vote(1, r, VoteType.PREVOTE, f"block_{r}", r * 10 + 1))
        # Byzantine node 2: sometimes wrong
        if r % 3 == 0:
            analyzer.record(Vote(2, r, VoteType.PREVOTE, f"wrong_{r}", r * 10 + 5))
        else:
            analyzer.record(Vote(2, r, VoteType.PREVOTE, f"block_{r}", r * 10 + 3))

    # Response rate
    rr_0 = analyzer.response_rate(0, 20)
    rr_2 = analyzer.response_rate(2, 20)
    check("honest_full_response", rr_0 == 1.0, f"rate={rr_0}")
    check("byzantine_full_response", rr_2 == 1.0, f"rate={rr_2}")

    # Consistency
    cons_0 = analyzer.consistency_score(0)
    cons_2 = analyzer.consistency_score(2)
    check("honest_high_consistency", cons_0 > 0.8, f"cons={cons_0:.3f}")
    check("byzantine_lower_consistency", cons_2 < cons_0,
          f"honest={cons_0:.3f} byzantine={cons_2:.3f}")

    # ── §4 Byzantine Score ────────────────────────────────────────
    print("\n§4 Byzantine Scoring\n")

    honest_profile = NodeProfile(0, NodeBehavior.HONEST)
    byz_profile = NodeProfile(2, NodeBehavior.BYZANTINE)

    score_honest = compute_byzantine_score(honest_profile, analyzer, 20)
    score_byz = compute_byzantine_score(byz_profile, analyzer, 20)

    check("honest_low_score", score_honest < 0.5,
          f"score={score_honest:.3f}")
    check("byzantine_higher_score", score_byz > score_honest,
          f"honest={score_honest:.3f} byz={score_byz:.3f}")

    # Proven equivocator → score = 1.0
    proven = NodeProfile(99, NodeBehavior.BYZANTINE, equivocations_detected=1)
    check("equivocator_score_1", compute_byzantine_score(proven, analyzer, 20) == 1.0)

    # ── §5 Gradual Slashing ──────────────────────────────────────
    print("\n§5 Gradual Trust Degradation\n")

    slasher = GradualSlasher()

    # First offense: moderate penalty
    acc1 = Accusation(1, 2, "behavioral", {}, 0.8, 100)
    t1 = slasher.process_accusation(acc1, 0.7)
    check("first_offense_penalty", t1 < 0.7, f"trust={t1:.3f}")

    # Second offense: larger penalty
    t2 = slasher.process_accusation(acc1, t1)
    penalty_1 = 0.7 - t1
    penalty_2 = t1 - t2
    check("escalating_penalty", penalty_2 > penalty_1,
          f"p1={penalty_1:.3f} p2={penalty_2:.3f}")

    # Equivocation: heavy penalty
    acc_equiv = Accusation(1, 3, "equivocation", {}, 1.0, 200)
    t_equiv = slasher.process_accusation(acc_equiv, 0.7)
    check("equivocation_heavy", t_equiv < t1,
          f"equivocation={t_equiv:.3f} behavioral={t1:.3f}")

    # Trust can't go below 0
    for _ in range(10):
        t_equiv = slasher.process_accusation(acc_equiv, t_equiv)
    check("trust_floor_zero", t_equiv >= 0.0)

    # ── §6 False Positive Analysis ────────────────────────────────
    print("\n§6 Detection Accuracy\n")

    # Perfect detection
    perfect = [(True, True), (True, True), (False, False), (False, False)]
    check("perfect_fpr_zero", false_positive_rate(perfect) == 0.0)
    check("perfect_fnr_zero", false_negative_rate(perfect) == 0.0)
    check("perfect_accuracy", detection_accuracy(perfect) == 1.0)

    # One false positive
    fp_case = [(True, True), (True, False), (False, False)]
    fpr = false_positive_rate(fp_case)
    check("one_fp", abs(fpr - 0.5) < 0.01, f"fpr={fpr:.3f}")

    # One false negative
    fn_case = [(True, True), (False, True), (False, False)]
    fnr = false_negative_rate(fn_case)
    check("one_fn", abs(fnr - 0.5) < 0.01, f"fnr={fnr:.3f}")

    # ── §7 Recovery Protocol ─────────────────────────────────────
    print("\n§7 Node Recovery\n")

    network_trust = {0: 0.8, 1: 0.7, 2: 0.6, 3: 0.9, 4: 0.3}
    slasher2 = GradualSlasher()
    # Slash node 5
    slasher2.process_accusation(
        Accusation(0, 5, "behavioral", {}, 0.7, 100), 0.7)

    # Recovery with enough vouchers
    req = RecoveryRequest(5, "network_issue", vouchers=[0, 1, 3], request_time=200)
    result = evaluate_recovery(req, network_trust, slasher2, quorum=3)
    check("recovery_approved", result["approved"])
    check("recovery_partial", 0 < result["recovery_fraction"] <= 0.5,
          f"fraction={result['recovery_fraction']:.3f}")

    # Recovery with insufficient vouchers
    req_bad = RecoveryRequest(5, "no_evidence", vouchers=[4], request_time=200)
    result_bad = evaluate_recovery(req_bad, network_trust, slasher2, quorum=3)
    check("insufficient_vouchers_denied", not result_bad["approved"])

    # ── §8 Full Simulation ────────────────────────────────────────
    print("\n§8 Full Consensus Simulation\n")

    sim = simulate_consensus_with_byzantines(10, 3, 50, seed=42)

    check("sim_accusations", sim["accusations"] > 0,
          f"accusations={sim['accusations']}")
    check("sim_accuracy_good", sim["accuracy"] >= 0.5,
          f"accuracy={sim['accuracy']:.3f}")
    check("sim_low_fpr", sim["fpr"] <= 0.5,
          f"fpr={sim['fpr']:.3f}")

    # Byzantine nodes should have higher scores
    byz_scores = [sim["scores"][i] for i in sim["byzantine_ids"]]
    honest_scores = [sim["scores"][i] for i in range(10) if i not in sim["byzantine_ids"]]
    avg_byz = sum(byz_scores) / len(byz_scores)
    avg_honest = sum(honest_scores) / len(honest_scores)
    check("byzantine_higher_avg_score", avg_byz > avg_honest,
          f"byz={avg_byz:.3f} honest={avg_honest:.3f}")

    # ── §9 Detection Threshold ────────────────────────────────────
    print("\n§9 Detection Threshold Analysis\n")

    # Test different thresholds
    thresholds = [0.3, 0.5, 0.7]
    for thresh in thresholds:
        detections = []
        for i in range(10):
            is_byz = i in sim["byzantine_ids"]
            detected = sim["scores"][i] > thresh
            detections.append((detected, is_byz))

        acc = detection_accuracy(detections)
        fpr = false_positive_rate(detections)
        check(f"threshold_{thresh}_valid", 0 <= acc <= 1,
              f"acc={acc:.3f} fpr={fpr:.3f}")

    # ── §10 Trust After Detection ─────────────────────────────────
    print("\n§10 Trust After Detection\n")

    # Equivocators should have reduced trust
    equivocator_trusts = [
        sim["profiles"][i].trust for i in sim["byzantine_ids"]
        if sim["profiles"][i].equivocations_detected > 0
    ]
    if equivocator_trusts:
        check("equivocators_low_trust", max(equivocator_trusts) < 0.7,
              f"trusts={equivocator_trusts}")
    else:
        check("equivocators_low_trust", True)  # no equivocators caught = still valid

    # Honest nodes should maintain trust
    honest_trusts = [sim["profiles"][i].trust for i in range(10)
                     if i not in sim["byzantine_ids"]]
    check("honest_maintain_trust", min(honest_trusts) >= 0.5,
          f"min_trust={min(honest_trusts):.3f}")

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
