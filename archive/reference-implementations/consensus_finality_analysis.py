"""
Consensus Finality Analysis for Web4
Session 33, Track 4

Probabilistic vs deterministic finality in trust consensus:
- Probabilistic finality: P(reorg | depth d) models for PoW-style
- Deterministic finality: BFT-style single-round or two-round finality
- Finality gadgets: Casper FFG-like finality on top of PoW/PoS chains
- Trust-weighted finality: stronger trust → faster finality
- Safety/liveness tradeoff analysis under Byzantine faults
- Slashable conditions and accountability
- Finality time distribution models
- Fork choice rules with trust integration
"""

import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict


# ─── Probabilistic Finality (PoW/PoS style) ──────────────────────

def prob_reorg_poisson(depth: int, attacker_fraction: float) -> float:
    """
    Probability of a reorganization of depth >= d in PoW-style consensus.
    Nakamoto (1988) model: geometric decay.
    P(reorg | depth d) = (q/p)^d  where p = honest fraction, q = attacker fraction
    Valid when p > q (honest majority).
    """
    if attacker_fraction >= 0.5:
        return 1.0  # attacker always wins
    if attacker_fraction <= 0.0:
        return 0.0
    p = 1.0 - attacker_fraction
    q = attacker_fraction
    # Nakamoto's formula
    return (q / p) ** depth


def confirmations_for_safety(attacker_fraction: float,
                               target_prob: float = 1e-6) -> int:
    """
    Number of confirmation blocks needed to achieve target security level.
    Returns depth d such that P(reorg | d) <= target_prob.
    """
    if attacker_fraction >= 0.5:
        return float('inf')
    if attacker_fraction <= 0.0:
        return 1

    p = 1.0 - attacker_fraction
    q = attacker_fraction
    ratio = q / p
    if ratio >= 1.0:
        return float('inf')

    # Solve: (q/p)^d <= target_prob → d >= log(target_prob) / log(q/p)
    d = math.log(target_prob) / math.log(ratio)
    return math.ceil(d)


def finality_time_distribution(depth: int, block_time_s: float,
                                 attacker_fraction: float) -> Dict[str, float]:
    """
    Statistics about time-to-finality for probabilistic consensus.
    """
    confs = confirmations_for_safety(attacker_fraction)
    if confs == float('inf'):
        confs = 9999

    expected_time_s = confs * block_time_s
    prob_at_depth = prob_reorg_poisson(depth, attacker_fraction)

    return {
        "depth": depth,
        "block_time_s": block_time_s,
        "attacker_fraction": attacker_fraction,
        "p_reorg_at_depth": prob_at_depth,
        "confs_for_1e-6": confs,
        "expected_finality_s": expected_time_s,
    }


# ─── BFT Deterministic Finality ──────────────────────────────────

@dataclass
class BFTConfig:
    """Configuration for a BFT consensus protocol."""
    n: int                      # Total validators
    f: int                      # Byzantine fault tolerance bound
    protocol: str = "PBFT"      # "PBFT", "HotStuff", "Tendermint"

    @property
    def quorum(self) -> int:
        """Quorum size (2f+1 out of n)."""
        return 2 * self.f + 1

    @property
    def max_byzantine(self) -> int:
        """Maximum safe Byzantine nodes."""
        return (self.n - 1) // 3

    @property
    def is_safe(self) -> bool:
        return self.f <= self.max_byzantine

    @property
    def message_complexity(self) -> str:
        if self.protocol == "PBFT":
            return f"O(n²) = {self.n ** 2}"
        elif self.protocol in ("HotStuff", "Streamlet"):
            return f"O(n) = {self.n}"
        else:
            return f"O(n²)"

    @property
    def rounds_to_finality(self) -> int:
        """Number of rounds for deterministic finality."""
        if self.protocol == "PBFT":
            return 3
        elif self.protocol == "HotStuff":
            return 3  # Three-phase (Prepare/Pre-commit/Commit)
        elif self.protocol == "Tendermint":
            return 2  # Two-phase with locks
        else:
            return 3


def bft_safety_liveness_analysis(n: int, f: int) -> Dict[str, object]:
    """
    Analyze BFT safety and liveness for given n, f.
    Safety: f < n/3
    Liveness: f < n/3 (same condition, but under network synchrony assumption)
    """
    max_f = (n - 1) // 3
    safe = f <= max_f
    quorum = 2 * f + 1

    # CAP: cannot have consistency + availability + partition tolerance simultaneously
    # BFT trades: safety always preserved, liveness may fail under partition
    return {
        "n": n,
        "f": f,
        "max_safe_f": max_f,
        "quorum_size": quorum,
        "safety": safe,
        "liveness": safe,  # Liveness requires same f < n/3 bound
        "can_tolerate_split_brain": False,  # BFT cannot tolerate equal split
        "fraction_byzantine": f / n,
        "fraction_honest": (n - f) / n,
    }


# ─── Casper FFG-Style Finality Gadget ────────────────────────────

@dataclass
class Checkpoint:
    """A checkpoint in the finality gadget."""
    epoch: int
    block_hash: str
    justified: bool = False
    finalized: bool = False
    votes: Dict[str, float] = field(default_factory=dict)  # validator_id -> stake

    @property
    def total_votes(self) -> float:
        return sum(self.votes.values())

    def justify(self, total_stake: float, threshold: float = 2/3) -> bool:
        """Justify if votes > 2/3 of total stake."""
        if self.total_votes / total_stake >= threshold:
            self.justified = True
        return self.justified


@dataclass
class FinalityGadget:
    """Simplified Casper FFG-style finality gadget."""
    validators: Dict[str, float]  # validator_id -> stake
    checkpoints: List[Checkpoint] = field(default_factory=list)

    @property
    def total_stake(self) -> float:
        return sum(self.validators.values())

    def add_checkpoint(self, epoch: int, block_hash: str) -> Checkpoint:
        cp = Checkpoint(epoch=epoch, block_hash=block_hash)
        self.checkpoints.append(cp)
        return cp

    def cast_vote(self, checkpoint_epoch: int, validator_id: str) -> bool:
        """Cast a vote for a checkpoint."""
        cp = next((c for c in self.checkpoints if c.epoch == checkpoint_epoch), None)
        if cp is None or validator_id not in self.validators:
            return False
        cp.votes[validator_id] = self.validators[validator_id]
        cp.justify(self.total_stake)
        return True

    def try_finalize(self, epoch: int) -> bool:
        """
        Finalize epoch N if:
        1. Checkpoint N is justified
        2. Checkpoint N+1 is justified (Casper FFG rule)
        """
        cp = next((c for c in self.checkpoints if c.epoch == epoch), None)
        cp_next = next((c for c in self.checkpoints if c.epoch == epoch + 1), None)

        if cp and cp_next and cp.justified and cp_next.justified:
            cp.finalized = True
            return True
        return False

    def is_slashable(self, validator_id: str,
                      vote1: Tuple[int, int],
                      vote2: Tuple[int, int]) -> bool:
        """
        Check if a validator is slashable for double voting.
        vote = (source_epoch, target_epoch)
        Slashable if: same target OR votes surround each other.
        """
        s1, t1 = vote1
        s2, t2 = vote2
        if t1 == t2:
            return True  # Double vote on same target
        if s1 < s2 < t2 < t1 or s2 < s1 < t1 < t2:
            return True  # Surround vote
        return False


# ─── Trust-Weighted Finality ─────────────────────────────────────

@dataclass
class TrustWeightedConsensus:
    """
    Consensus where voting power is proportional to T3 trust scores.
    Finality threshold: trust-weighted supermajority.
    """
    validators: Dict[str, float]  # validator_id -> trust_score

    @property
    def total_trust(self) -> float:
        return sum(self.validators.values())

    def weighted_quorum(self, threshold: float = 2/3) -> float:
        """Required trust-weighted vote for threshold."""
        return self.total_trust * threshold

    def has_quorum(self, votes: Set[str], threshold: float = 2/3) -> bool:
        """Check if a set of validators has trust-weighted quorum."""
        vote_trust = sum(self.validators.get(v, 0.0) for v in votes)
        return vote_trust >= self.weighted_quorum(threshold)

    def minimum_quorum_set(self, threshold: float = 2/3) -> List[str]:
        """Find minimum set of validators to form quorum (greedy: highest trust first)."""
        required = self.weighted_quorum(threshold)
        # Sort by trust descending
        sorted_vals = sorted(self.validators.items(), key=lambda x: -x[1])
        quorum_set = []
        accumulated = 0.0
        for vid, trust in sorted_vals:
            quorum_set.append(vid)
            accumulated += trust
            if accumulated >= required:
                break
        return quorum_set

    def finality_latency(self, base_latency_ms: float,
                          trust_bonus_factor: float = 0.5) -> float:
        """
        Estimate finality latency.
        High trust → faster quorum formation → lower latency.
        avg_trust = total / n  scaled to [0.5, 1.0]
        """
        n = len(self.validators)
        if n == 0:
            return base_latency_ms
        avg_trust = self.total_trust / n
        # High trust = more likely to form quorum quickly
        speedup = 1.0 - trust_bonus_factor * (avg_trust - 0.5)
        return base_latency_ms * max(0.1, speedup)


# ─── Fork Choice Rule ────────────────────────────────────────────

@dataclass
class Block:
    """A block in the consensus chain."""
    hash: str
    parent: Optional[str]
    height: int
    trust_weight: float  # sum of validator trust for this block


def lmd_ghost_trust(blocks: Dict[str, Block],
                     votes: Dict[str, str],       # validator -> block_hash
                     validator_trust: Dict[str, float],
                     genesis: str) -> str:
    """
    LMD-GHOST fork choice with trust weighting.
    At each fork, choose the child with highest trust-weighted vote count.
    Returns the head block hash.
    """
    # Accumulate trust per block (and ancestors)
    block_trust: Dict[str, float] = defaultdict(float)
    for validator, block_hash in votes.items():
        trust = validator_trust.get(validator, 0.0)
        # Walk up to genesis, accumulating trust
        current = block_hash
        while current is not None:
            block_trust[current] += trust
            b = blocks.get(current)
            if b is None:
                break
            current = b.parent

    # Find head: start from genesis, always choose child with most trust
    current = genesis
    while True:
        children = [b for b in blocks.values() if b.parent == current]
        if not children:
            return current
        # Pick child with max accumulated trust
        best = max(children, key=lambda b: block_trust.get(b.hash, 0.0))
        current = best.hash


# ─── Safety/Liveness Partition Analysis ──────────────────────────

def partition_analysis(n: int, f: int,
                        partition_sizes: Tuple[int, int]) -> Dict[str, object]:
    """
    Analyze what happens when network partitions into two parts.
    BFT requires 2f+1 quorum; partition must not allow two conflicting quorums.
    """
    p1, p2 = partition_sizes
    # Note: p1+p2 can exceed n if Byzantine nodes appear in both partitions

    quorum = 2 * f + 1
    p1_has_quorum = p1 >= quorum
    p2_has_quorum = p2 >= quorum
    both_quorum = p1_has_quorum and p2_has_quorum  # safety violation possible!

    return {
        "n": n,
        "f": f,
        "quorum": quorum,
        "partition_p1": p1,
        "partition_p2": p2,
        "p1_has_quorum": p1_has_quorum,
        "p2_has_quorum": p2_has_quorum,
        "safety_risk": both_quorum,
        "liveness_preserved": p1_has_quorum or p2_has_quorum,
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
    print("Consensus Finality Analysis for Web4")
    print("Session 33, Track 4")
    print("=" * 70)

    # ── §1 Probabilistic Finality ────────────────────────────────
    print("\n§1 Probabilistic Finality\n")

    # With 0% attacker, reorg probability = 0
    check("zero_attacker", prob_reorg_poisson(6, 0.0) == 0.0)

    # With 50%+ attacker, always reorg
    check("majority_attacker", prob_reorg_poisson(6, 0.5) == 1.0)

    # Decay with depth
    p1 = prob_reorg_poisson(1, 0.3)
    p6 = prob_reorg_poisson(6, 0.3)
    p12 = prob_reorg_poisson(12, 0.3)
    check("prob_decreases_with_depth", p1 > p6 > p12)
    check("prob_positive", p1 > 0 and p6 > 0)

    # 33% attacker: 30% reorg at depth 1, (0.33/0.67)^6 at depth 6
    p33_d1 = prob_reorg_poisson(1, 1/3)
    expected = (1/3) / (2/3)
    check("prob_matches_formula", abs(p33_d1 - expected) < 1e-9)

    # ── §2 Confirmation Count ────────────────────────────────────
    print("\n§2 Confirmation Count\n")

    # 0% attacker needs 1 confirmation
    confs_0 = confirmations_for_safety(0.0, 1e-6)
    check("zero_attacker_confs", confs_0 == 1)

    # More attacker fraction → more confirmations needed
    confs_10 = confirmations_for_safety(0.10, 1e-6)
    confs_30 = confirmations_for_safety(0.30, 1e-6)
    confs_40 = confirmations_for_safety(0.40, 1e-6)
    check("more_attacker_more_confs", confs_10 < confs_30 < confs_40)

    # Verify: depth d achieves target safety
    for af in [0.1, 0.2, 0.3]:
        d = confirmations_for_safety(af, 1e-6)
        p = prob_reorg_poisson(d, af)
        check(f"confs_sufficient_{af:.1f}", p <= 1e-6, f"p={p:.2e}")

    # ── §3 BFT Configuration ─────────────────────────────────────
    print("\n§3 BFT Configuration\n")

    cfg4 = BFTConfig(n=4, f=1)
    check("bft_4_quorum", cfg4.quorum == 3)
    check("bft_4_safe", cfg4.is_safe)

    cfg7 = BFTConfig(n=7, f=2)
    check("bft_7_quorum", cfg7.quorum == 5)
    check("bft_7_safe", cfg7.is_safe)

    # f > n/3 → unsafe
    cfg_bad = BFTConfig(n=4, f=2)
    check("bft_unsafe", not cfg_bad.is_safe)

    # Protocol rounds
    check("pbft_3_rounds", BFTConfig(n=7, f=2, protocol="PBFT").rounds_to_finality == 3)
    check("hotstuff_3_rounds", BFTConfig(n=7, f=2, protocol="HotStuff").rounds_to_finality == 3)
    check("tendermint_2_rounds", BFTConfig(n=7, f=2, protocol="Tendermint").rounds_to_finality == 2)

    # ── §4 Safety/Liveness Analysis ──────────────────────────────
    print("\n§4 Safety/Liveness Analysis\n")

    analysis = bft_safety_liveness_analysis(10, 3)
    check("n10_f3_safe", analysis["safety"])
    check("n10_f3_quorum", analysis["quorum_size"] == 7)
    check("n10_f3_fraction", abs(analysis["fraction_byzantine"] - 0.3) < 1e-9)

    analysis_bad = bft_safety_liveness_analysis(10, 4)
    check("n10_f4_unsafe", not analysis_bad["safety"])

    check("no_split_brain", not analysis["can_tolerate_split_brain"])

    # ── §5 Finality Gadget (Casper FFG) ──────────────────────────
    print("\n§5 Finality Gadget (Casper FFG)\n")

    validators = {"v1": 40.0, "v2": 30.0, "v3": 20.0, "v4": 10.0}  # stake
    gadget = FinalityGadget(validators=validators)

    cp1 = gadget.add_checkpoint(1, "block_hash_1")
    cp2 = gadget.add_checkpoint(2, "block_hash_2")

    # Total stake = 100. Need 2/3 = 67 to justify.
    # v1(40) + v2(30) = 70 ≥ 67 → justified
    gadget.cast_vote(1, "v1")
    gadget.cast_vote(1, "v2")
    check("cp1_justified_threshold", cp1.justified, f"votes={cp1.total_votes}")

    gadget.cast_vote(2, "v1")
    gadget.cast_vote(2, "v2")
    check("cp2_justified", cp2.justified)

    # Finalize epoch 1: both 1 and 2 justified
    finalized = gadget.try_finalize(1)
    check("epoch1_finalized", finalized)
    check("cp1_is_finalized", cp1.finalized)

    # Without both justified, no finalization
    gadget2 = FinalityGadget(validators={"a": 60.0, "b": 40.0})
    cp_a = gadget2.add_checkpoint(1, "h1")
    cp_b = gadget2.add_checkpoint(2, "h2")
    gadget2.cast_vote(1, "a")  # 60% stake, but 60/100 < 2/3 → NOT justified
    check("cp_a_not_yet_justified", not cp_a.justified)
    # cp_b not justified → no finalization
    not_final = gadget2.try_finalize(1)
    check("no_finalize_without_both", not not_final)

    # ── §6 Slashable Conditions ──────────────────────────────────
    print("\n§6 Slashable Conditions\n")

    gadget3 = FinalityGadget(validators={})

    # Double vote: same target epoch
    check("double_vote_slashable", gadget3.is_slashable("v1", (1, 5), (2, 5)))

    # Surround vote
    check("surround_vote_slashable", gadget3.is_slashable("v1", (1, 10), (2, 8)))
    check("surround_vote_2", gadget3.is_slashable("v1", (2, 8), (1, 10)))

    # Non-slashable: consecutive non-overlapping
    check("non_slashable", not gadget3.is_slashable("v1", (1, 3), (4, 7)))

    # ── §7 Trust-Weighted Consensus ──────────────────────────────
    print("\n§7 Trust-Weighted Consensus\n")

    tw = TrustWeightedConsensus({
        "v1": 0.9,
        "v2": 0.8,
        "v3": 0.5,
        "v4": 0.3,
        "v5": 0.2,
    })
    total = tw.total_trust
    check("total_trust_correct", abs(total - 2.7) < 1e-9)

    # High-trust validators form quorum faster
    quorum = tw.minimum_quorum_set(2/3)
    # Need 2/3 * 2.7 = 1.8; v1(0.9) + v2(0.8) = 1.7 < 1.8; need v3 too
    vote_trust = sum(tw.validators[v] for v in quorum)
    check("quorum_sufficient", vote_trust >= tw.weighted_quorum(2/3))

    # Has quorum: top 3 validators
    check("has_quorum_top3", tw.has_quorum({"v1", "v2", "v3"}))

    # No quorum: bottom 3
    check("no_quorum_bottom3", not tw.has_quorum({"v3", "v4", "v5"}))

    # Latency: higher trust → lower latency
    tw_high = TrustWeightedConsensus({"a": 0.95, "b": 0.9, "c": 0.85})
    tw_low = TrustWeightedConsensus({"a": 0.4, "b": 0.3, "c": 0.35})
    lat_high = tw_high.finality_latency(1000.0)
    lat_low = tw_low.finality_latency(1000.0)
    check("high_trust_faster", lat_high < lat_low, f"high={lat_high:.0f}, low={lat_low:.0f}")

    # ── §8 Fork Choice Rule ──────────────────────────────────────
    print("\n§8 Fork Choice Rule (LMD-GHOST + Trust)\n")

    # Chain: genesis → A → B (main)
    #                 → C (fork, less trust)
    blocks = {
        "genesis": Block("genesis", None, 0, 0),
        "A": Block("A", "genesis", 1, 0),
        "B": Block("B", "A", 2, 0),
        "C": Block("C", "A", 2, 0),
    }
    validator_trust = {"v1": 0.9, "v2": 0.8, "v3": 0.3}
    votes = {"v1": "B", "v2": "B", "v3": "C"}  # Most trust on B

    head = lmd_ghost_trust(blocks, votes, validator_trust, "genesis")
    check("fork_choice_prefers_B", head == "B", f"head={head}")

    # Flip: most trust on C
    votes2 = {"v1": "C", "v2": "C", "v3": "B"}
    head2 = lmd_ghost_trust(blocks, votes2, validator_trust, "genesis")
    check("fork_choice_prefers_C", head2 == "C", f"head2={head2}")

    # ── §9 Partition Analysis ────────────────────────────────────
    print("\n§9 Partition Analysis\n")

    # n=7, f=2 → quorum=5. Split 4/3: p1 has quorum (4<5? no), p2 doesn't
    # quorum=5; p1=4 < 5 so neither has quorum
    part1 = partition_analysis(7, 2, (4, 3))
    check("equal_split_no_safety_risk", not part1["safety_risk"])
    check("equal_split_p1_no_quorum", not part1["p1_has_quorum"])
    check("equal_split_p2_no_quorum", not part1["p2_has_quorum"])

    # n=10, f=3 → quorum=7. Split 7/3: p1 has quorum, p2 doesn't
    part2 = partition_analysis(10, 3, (7, 3))
    check("7_3_split_safe", not part2["safety_risk"])
    check("7_3_split_liveness", part2["liveness_preserved"])

    # n=10, f=3 → quorum=7. Split 8/7: both partitions have quorum! Safety violation!
    part3 = partition_analysis(10, 3, (8, 7))
    check("8_7_split_safety_violation", part3["safety_risk"])

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
