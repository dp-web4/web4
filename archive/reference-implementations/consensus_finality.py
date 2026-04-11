"""
Consensus Finality Analysis for Web4
Session 33, Track 4

Probabilistic vs deterministic finality in trust consensus:
- Nakamoto-style probabilistic finality (Bitcoin-like)
- BFT-style deterministic finality (single-round confirmation)
- Tendermint/HotStuff finality gadget analysis
- Finality depth vs confidence curves
- Fork choice rules (longest chain, heaviest chain, GHOST)
- Reorg probability under adversarial stake
- Time-to-finality for different consensus variants
- Safety vs liveness tradeoffs
- Finality under partial synchrony (GST model)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum, auto
import math


# ─── Probabilistic Finality (Nakamoto) ──────────────────────────

def nakamoto_reorg_prob(depth: int, attacker_fraction: float) -> float:
    """
    Probability that an attacker with fraction q of hash/stake power
    can reorg a block at depth d.
    
    From Nakamoto (2008): uses Poisson distribution.
    q = attacker fraction, p = honest fraction = 1 - q.
    """
    q = attacker_fraction
    p = 1.0 - q

    if q >= p:
        return 1.0  # Attacker has majority — always wins

    # λ = expected number of blocks attacker mines while honest chain grows by d
    lam = depth * (q / p)

    # P(attack succeeds) = 1 - Σ_{k=0}^{d} [e^{-λ} λ^k / k!] * (1 - (q/p)^{d-k+1})
    # Simplified: P ≈ (q/p)^d for large d
    # More precise: sum over Poisson distribution
    total = 0.0
    for k in range(depth + 1):
        try:
            poisson = math.exp(-lam) * (lam ** k) / math.factorial(k)
        except (OverflowError, ValueError):
            poisson = 0.0
        if k <= depth:
            total += poisson * (1.0 - (q / p) ** (depth - k + 1))

    return max(0.0, 1.0 - total)


def finality_depth_for_confidence(confidence: float, attacker_fraction: float,
                                   max_depth: int = 100) -> int:
    """
    Find minimum depth d such that reorg probability < (1 - confidence).
    """
    target = 1.0 - confidence
    for d in range(1, max_depth + 1):
        if nakamoto_reorg_prob(d, attacker_fraction) < target:
            return d
    return max_depth


# ─── Deterministic BFT Finality ─────────────────────────────────

class BFTPhase(Enum):
    PROPOSE = auto()
    PREVOTE = auto()
    PRECOMMIT = auto()
    COMMIT = auto()


@dataclass
class BFTRound:
    """Single round of BFT consensus (Tendermint-style)."""
    round_num: int
    n: int              # total validators
    f: int              # max Byzantine faults (n = 3f+1 minimum)
    proposer: int
    votes: Dict[BFTPhase, List[int]] = field(default_factory=lambda: {
        BFTPhase.PREVOTE: [],
        BFTPhase.PRECOMMIT: [],
    })
    decided_value: Optional[str] = None

    @property
    def quorum(self) -> int:
        """2f+1 votes needed for quorum."""
        return 2 * self.f + 1

    def add_prevote(self, validator: int):
        self.votes[BFTPhase.PREVOTE].append(validator)

    def add_precommit(self, validator: int):
        self.votes[BFTPhase.PRECOMMIT].append(validator)

    def has_prevote_quorum(self) -> bool:
        return len(set(self.votes[BFTPhase.PREVOTE])) >= self.quorum

    def has_precommit_quorum(self) -> bool:
        return len(set(self.votes[BFTPhase.PRECOMMIT])) >= self.quorum

    def finalize(self, value: str) -> bool:
        """Finalize if we have precommit quorum."""
        if self.has_precommit_quorum():
            self.decided_value = value
            return True
        return False

    def is_bft_safe(self) -> bool:
        """Check n ≥ 3f+1 safety bound."""
        return self.n >= 3 * self.f + 1


@dataclass
class BFTFinality:
    """BFT consensus finality metrics."""
    n: int
    f: int
    rounds_to_finality: int = 1  # Tendermint: 1 round in happy path
    message_complexity: str = "O(n²)"
    finality_type: str = "deterministic"

    @property
    def safety_threshold(self) -> float:
        """Fraction of Byzantine nodes that can be tolerated."""
        return self.f / self.n

    @property
    def liveness_threshold(self) -> float:
        """Need > 2/3 honest for liveness."""
        return (self.n - self.f) / self.n

    def is_safe(self) -> bool:
        return self.n >= 3 * self.f + 1

    def finality_latency_rounds(self, network_delay_ms: float = 200) -> float:
        """Estimated finality latency in ms."""
        # 2 voting phases × n messages × network delay
        return self.rounds_to_finality * 2 * network_delay_ms


# ─── Fork Choice Rules ───────────────────────────────────────────

@dataclass
class Block:
    """A block in a blockchain fork."""
    hash: str
    parent: Optional[str]
    height: int
    weight: float = 1.0     # for heaviest-chain
    votes: int = 0          # for GHOST

    def __hash__(self):
        return hash(self.hash)


class BlockTree:
    """Tree of blocks for fork choice analysis."""

    def __init__(self):
        self.blocks: Dict[str, Block] = {}
        self.children: Dict[str, List[str]] = {}

    def add_block(self, block: Block):
        self.blocks[block.hash] = block
        if block.parent:
            self.children.setdefault(block.parent, []).append(block.hash)
        self.children.setdefault(block.hash, [])

    def longest_chain_tip(self) -> Optional[str]:
        """Return tip of the longest chain (highest block)."""
        if not self.blocks:
            return None
        return max(self.blocks.values(), key=lambda b: b.height).hash

    def heaviest_chain_tip(self) -> Optional[str]:
        """Return tip of heaviest chain (most cumulative weight)."""
        if not self.blocks:
            return None

        # BFS from genesis, accumulate weights
        cumulative: Dict[str, float] = {}
        for bh, block in self.blocks.items():
            if block.parent is None:
                cumulative[bh] = block.weight

        # Propagate weights down
        changed = True
        while changed:
            changed = False
            for bh, block in self.blocks.items():
                if bh not in cumulative and block.parent in cumulative:
                    cumulative[bh] = cumulative[block.parent] + block.weight
                    changed = True

        if not cumulative:
            return max(self.blocks.values(), key=lambda b: b.weight).hash

        return max(cumulative, key=lambda h: cumulative[h])

    def ghost_tip(self, genesis: str) -> str:
        """
        GHOST fork choice: at each fork, pick subtree with most blocks.
        """
        current = genesis
        while True:
            kids = self.children.get(current, [])
            if not kids:
                return current
            # Pick child with most descendants
            best = max(kids, key=lambda c: self._subtree_size(c))
            current = best

    def _subtree_size(self, root: str) -> int:
        """Count total blocks in subtree rooted at root."""
        size = 1
        for child in self.children.get(root, []):
            size += self._subtree_size(child)
        return size

    def chain_from(self, tip: str) -> List[str]:
        """Return chain from genesis to tip."""
        chain = []
        cur = tip
        while cur is not None:
            chain.append(cur)
            block = self.blocks.get(cur)
            cur = block.parent if block else None
        return list(reversed(chain))


# ─── HotStuff Linear Finality ────────────────────────────────────

@dataclass
class HotStuffRound:
    """
    HotStuff 3-phase linear consensus (O(n) message complexity).
    Phases: PREPARE → PRE-COMMIT → COMMIT → DECIDE
    """
    view: int
    n: int
    f: int
    leader: int
    qc: Optional[str] = None    # Quorum Certificate (aggregated signature)
    decided: bool = False

    @property
    def quorum(self) -> int:
        return 2 * self.f + 1

    def collect_votes(self, phase: str, votes: List[int]) -> Optional[str]:
        """
        Collect votes for a phase. Returns QC if quorum reached.
        In real HotStuff, this is a threshold signature.
        """
        if len(set(votes)) >= self.quorum:
            return f"QC-{phase}-{self.view}"
        return None

    def message_count(self) -> int:
        """HotStuff: O(n) per phase (leader broadcasts/collects)."""
        return 4 * self.n  # 4 phases × n messages each


def hotstuff_vs_pbft(n: int, f: int) -> Dict[str, int]:
    """Compare message complexity: HotStuff O(n) vs PBFT O(n²)."""
    return {
        "n": n,
        "f": f,
        "pbft_messages": n * n,  # O(n²)
        "hotstuff_messages": 4 * n,  # O(n)
        "ratio": n // 4,  # HotStuff is ~n/4 times more efficient
    }


# ─── Finality Under Partial Synchrony ───────────────────────────

class NetworkModel(Enum):
    SYNCHRONOUS = auto()      # known message delay bound
    PARTIAL_SYNC = auto()     # unknown delay, but eventually stabilizes (GST)
    ASYNCHRONOUS = auto()     # no delay bound (FLP impossibility applies)


def finality_under_model(model: NetworkModel, bft: BFTFinality) -> Dict[str, str]:
    """
    Analyze finality properties under different network models.
    FLP impossibility: cannot have safety + liveness in async networks.
    """
    if model == NetworkModel.SYNCHRONOUS:
        return {
            "safety": "guaranteed",
            "liveness": "guaranteed",
            "finality": "deterministic",
            "note": "Requires known Δ (message delay bound)"
        }
    elif model == NetworkModel.PARTIAL_SYNC:
        return {
            "safety": "always" if bft.is_safe() else "violated",
            "liveness": "after GST (Global Stabilization Time)",
            "finality": "deterministic after GST",
            "note": "Safety holds even before GST; liveness requires GST"
        }
    else:  # ASYNCHRONOUS
        return {
            "safety": "always (if BFT safe)",
            "liveness": "impossible (FLP impossibility)",
            "finality": "not guaranteed",
            "note": "FLP: no deterministic protocol achieves consensus in async model"
        }


# ─── Safety vs Liveness Tradeoff ────────────────────────────────

@dataclass
class FinalityConfig:
    """Configuration trading safety vs liveness."""
    name: str
    safety_threshold: float    # fraction of Byzantine nodes tolerated
    liveness_threshold: float  # fraction of honest nodes needed
    finality_time: str
    notes: str


FINALITY_CONFIGS = [
    FinalityConfig("Nakamoto (6 blocks)", 0.50, 0.50,
                   "~60 min (Bitcoin)", "Probabilistic; vulnerable to 51% attack"),
    FinalityConfig("Tendermint", 0.33, 0.67,
                   "~1-2 blocks", "Deterministic; halts if >1/3 Byzantine"),
    FinalityConfig("HotStuff", 0.33, 0.67,
                   "~1 block", "Deterministic; O(n) messages; used in Diem/LibraBFT"),
    FinalityConfig("PBFT", 0.33, 0.67,
                   "~1 block", "Deterministic; O(n²) messages; impractical at n>100"),
    FinalityConfig("Gasper (ETH2)", 0.33, 0.67,
                   "2 epochs ~13 min", "Finality gadget over LMD-GHOST"),
    FinalityConfig("Avalanche", 0.50, 0.80,
                   "~2 sec", "Probabilistic; metastability via repeated subsampling"),
]


# ─── Trust-Weighted Finality ─────────────────────────────────────

def trust_weighted_quorum(validators: Dict[str, float],
                           threshold: float = 0.67) -> Tuple[List[str], float]:
    """
    In trust-weighted BFT: weight votes by T3 trust score.
    Quorum = validators whose combined trust exceeds threshold × total.
    Returns (minimum quorum set, combined weight).
    """
    total_trust = sum(validators.values())
    target = threshold * total_trust

    # Sort by trust descending — greedy minimum quorum
    sorted_vals = sorted(validators.items(), key=lambda x: -x[1])
    quorum = []
    accumulated = 0.0
    for vid, trust in sorted_vals:
        quorum.append(vid)
        accumulated += trust
        if accumulated >= target:
            break

    return quorum, accumulated / total_trust


def finality_threshold_analysis(validators: Dict[str, float]) -> Dict[str, float]:
    """
    Analyze what fraction of trust is needed for various thresholds.
    """
    total = sum(validators.values())
    sorted_trusts = sorted(validators.values(), reverse=True)

    results = {}
    for threshold in [0.5, 0.67, 0.75, 0.90]:
        accumulated = 0.0
        count = 0
        for t in sorted_trusts:
            accumulated += t
            count += 1
            if accumulated >= threshold * total:
                break
        results[f"quorum_{int(threshold*100)}pct"] = count
        results[f"trust_weight_{int(threshold*100)}pct"] = accumulated / total

    return results


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

    # ── §1 Nakamoto Probabilistic Finality ───────────────────────
    print("\n§1 Nakamoto Probabilistic Finality\n")

    # 10% attacker: reorg probability should decrease with depth
    p10 = [nakamoto_reorg_prob(d, 0.10) for d in [1, 3, 6, 12]]
    check("reorg_decreases_with_depth", p10[0] > p10[1] > p10[2] > p10[3],
          f"probs={[f'{p:.4f}' for p in p10]}")
    check("6_blocks_is_low", p10[2] < 0.01, f"p={p10[2]:.6f}")

    # 33% attacker: harder to achieve finality
    p33 = nakamoto_reorg_prob(6, 0.33)
    check("33pct_higher_risk", p33 > p10[2], f"p33={p33:.4f}")

    # 50% attacker: guaranteed
    p50 = nakamoto_reorg_prob(1, 0.50)
    check("50pct_always_wins", p50 == 1.0, f"p50={p50}")

    # Finality depth for 99% confidence
    d1 = finality_depth_for_confidence(0.99, 0.10)
    d2 = finality_depth_for_confidence(0.99, 0.30)
    check("higher_attacker_needs_more_depth", d2 > d1,
          f"d1={d1}, d2={d2}")
    check("depth_is_positive", d1 >= 1)

    # ── §2 BFT Round ─────────────────────────────────────────────
    print("\n§2 BFT Round (Tendermint-style)\n")

    # n=10, f=3 → quorum=7
    rnd = BFTRound(1, n=10, f=3, proposer=0)
    check("bft_safe", rnd.is_bft_safe())
    check("quorum_is_7", rnd.quorum == 7)

    for v in range(7):
        rnd.add_prevote(v)
    check("prevote_quorum", rnd.has_prevote_quorum())
    check("no_precommit_yet", not rnd.has_precommit_quorum())

    for v in range(7):
        rnd.add_precommit(v)
    check("precommit_quorum", rnd.has_precommit_quorum())
    check("finalized", rnd.finalize("block-hash-abc"))
    check("decided_value_set", rnd.decided_value == "block-hash-abc")

    # Insufficient quorum
    rnd2 = BFTRound(1, n=10, f=3, proposer=0)
    for v in range(6):  # 6 < 7 = quorum
        rnd2.add_precommit(v)
    check("insufficient_quorum", not rnd2.has_precommit_quorum())
    check("not_finalized", not rnd2.finalize("value"))

    # Unsafe config: n=5, f=2 → need n≥7
    unsafe = BFTRound(1, n=5, f=2, proposer=0)
    check("unsafe_bft", not unsafe.is_bft_safe())

    # ── §3 BFT Finality Metrics ──────────────────────────────────
    print("\n§3 BFT Finality Metrics\n")

    bft10 = BFTFinality(n=10, f=3)
    check("safety_threshold", abs(bft10.safety_threshold - 0.3) < 1e-9)
    check("liveness_threshold", abs(bft10.liveness_threshold - 0.7) < 1e-9)
    check("is_safe_10_3", bft10.is_safe())

    bft4 = BFTFinality(n=4, f=2)
    check("unsafe_4_2", not bft4.is_safe())  # 4 < 3*2+1=7

    latency = bft10.finality_latency_rounds(200)
    check("latency_reasonable", latency > 0)

    # ── §4 Fork Choice ───────────────────────────────────────────
    print("\n§4 Fork Choice Rules\n")

    tree = BlockTree()
    # Genesis
    tree.add_block(Block("g", None, 0, weight=1.0))
    # Main chain: g → A → B → C
    tree.add_block(Block("A", "g", 1, weight=1.0))
    tree.add_block(Block("B", "A", 2, weight=1.0))
    tree.add_block(Block("C", "B", 3, weight=1.0))
    # Fork: g → A → D (shorter)
    tree.add_block(Block("D", "A", 2, weight=5.0))  # heavy but short

    # Longest chain picks C (height 3)
    longest = tree.longest_chain_tip()
    check("longest_chain", longest == "C", f"tip={longest}")

    # Heaviest chain: D has weight 5 on top of g(1)+A(1)+D(5)=7 vs C's g+A+B+C=4
    heaviest = tree.heaviest_chain_tip()
    check("heaviest_chain", heaviest == "D", f"tip={heaviest}")

    # GHOST: from genesis, pick subtree with most blocks
    # g has 2 children (A), A has 2 children (B,D), B has 1 (C), D has 0
    # At A: left subtree (B→C) has 2 blocks, right (D) has 1 → pick B side
    ghost = tree.ghost_tip("g")
    check("ghost_tip", ghost == "C", f"tip={ghost}")

    # Chain reconstruction
    chain = tree.chain_from("C")
    check("chain_from_C", chain == ["g", "A", "B", "C"], f"chain={chain}")

    # ── §5 HotStuff vs PBFT ─────────────────────────────────────
    print("\n§5 HotStuff vs PBFT Message Complexity\n")

    for n in [10, 100, 1000]:
        cmp = hotstuff_vs_pbft(n, f=n//3)
        check(f"hotstuff_less_messages_{n}",
              cmp["hotstuff_messages"] < cmp["pbft_messages"],
              f"hs={cmp['hotstuff_messages']}, pbft={cmp['pbft_messages']}")
        # At n=1000: PBFT has 1M messages, HotStuff has 4000
        if n == 1000:
            check("pbft_impractical_at_1000",
                  cmp["pbft_messages"] == 1000000)
            check("hotstuff_linear",
                  cmp["hotstuff_messages"] == 4000)

    # ── §6 Network Model Analysis ────────────────────────────────
    print("\n§6 Finality Under Network Models\n")

    bft = BFTFinality(n=10, f=3)

    sync_props = finality_under_model(NetworkModel.SYNCHRONOUS, bft)
    check("sync_safety", sync_props["safety"] == "guaranteed")
    check("sync_liveness", sync_props["liveness"] == "guaranteed")

    partial_props = finality_under_model(NetworkModel.PARTIAL_SYNC, bft)
    check("partial_safety", "always" in partial_props["safety"])
    check("partial_liveness", "GST" in partial_props["liveness"])

    async_props = finality_under_model(NetworkModel.ASYNCHRONOUS, bft)
    check("async_liveness_impossible", "impossible" in async_props["liveness"])
    check("flp_noted", "FLP" in async_props["note"])

    # ── §7 Trust-Weighted Quorum ─────────────────────────────────
    print("\n§7 Trust-Weighted Finality\n")

    # Unequal trust validators
    validators = {
        "alice": 0.95,
        "bob": 0.80,
        "carol": 0.70,
        "dave": 0.40,
        "eve": 0.20,
    }
    quorum, weight = trust_weighted_quorum(validators, 0.67)
    check("quorum_non_empty", len(quorum) > 0)
    check("quorum_reaches_threshold", weight >= 0.67, f"weight={weight:.3f}")
    # High-trust validators should be picked first
    check("alice_in_quorum", "alice" in quorum)
    check("minimum_quorum", len(quorum) <= len(validators))

    # Uniform trust = equal vote weight
    equal = {f"v{i}": 1.0 for i in range(10)}
    q_eq, w_eq = trust_weighted_quorum(equal, 0.67)
    check("uniform_quorum_7_of_10", len(q_eq) == 7, f"got={len(q_eq)}")

    # Threshold analysis
    analysis = finality_threshold_analysis(validators)
    check("50pct_quorum_exists", "quorum_50pct" in analysis)
    check("67pct_quorum_exists", "quorum_67pct" in analysis)
    check("larger_threshold_larger_quorum",
          analysis["quorum_90pct"] >= analysis["quorum_50pct"])

    # ── §8 Finality Config Catalog ───────────────────────────────
    print("\n§8 Finality Config Catalog\n")

    check("6_configs_cataloged", len(FINALITY_CONFIGS) == 6)
    check("bft_configs_have_33pct_threshold",
          all(abs(c.safety_threshold - 0.33) < 0.01
              for c in FINALITY_CONFIGS if "BFT" in c.notes or "Tendermint" in c.name))
    check("nakamoto_50pct_threshold",
          FINALITY_CONFIGS[0].safety_threshold == 0.50)
    # All BFT protocols need 67% honest
    bft_configs = [c for c in FINALITY_CONFIGS if c.liveness_threshold > 0.65]
    check("bft_all_67pct_liveness",
          all(abs(c.liveness_threshold - 0.67) < 0.01 for c in bft_configs))

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
