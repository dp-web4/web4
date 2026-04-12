"""
Trust Protocol Complexity Bounds for Web4
Session 32, Track 7

Fundamental complexity limits of trust protocols.
What are the minimum resources needed for trust operations?

- Communication complexity of trust consensus
- Round complexity of trust establishment
- Space complexity of trust state
- Time complexity of trust operations
- Lower bounds from information theory
- Amortized vs worst-case analysis
- Tradeoffs between complexity dimensions
"""

import math
import random
from dataclasses import dataclass
from typing import List, Dict, Tuple


# ─── Communication Complexity ─────────────────────────────────────

def consensus_message_complexity(n: int, protocol: str = "pbft") -> int:
    """
    Number of messages required for trust consensus.
    """
    if protocol == "pbft":
        return n * n  # O(n²) all-to-all
    elif protocol == "hotstuff":
        return 3 * n  # O(n) linear
    elif protocol == "raft":
        return 2 * n  # O(n) leader-based
    elif protocol == "tendermint":
        return 2 * n * n  # O(n²) two rounds
    else:
        return n * n


def gossip_rounds_to_converge(n: int, fanout: int = 3) -> int:
    """
    Rounds for gossip to reach all n nodes.
    Each round, each node sends to `fanout` random peers.
    Expected: O(log n / log fanout) rounds.
    """
    if n <= 1:
        return 0
    return math.ceil(math.log(n) / math.log(fanout))


def attestation_bandwidth(n_attestors: int, trust_dims: int = 3,
                           signature_bytes: int = 64) -> int:
    """
    Bytes needed to collect trust attestations.
    Each attestation: trust_dims * 8 bytes + signature.
    """
    per_attestation = trust_dims * 8 + signature_bytes
    return n_attestors * per_attestation


# ─── Round Complexity ─────────────────────────────────────────────

def trust_establishment_rounds(protocol: str = "interactive") -> int:
    """Minimum rounds for trust establishment."""
    if protocol == "interactive":
        return 3  # Challenge → Response → Verify
    elif protocol == "zero_knowledge":
        return 1  # Single proof
    elif protocol == "multisig":
        return 2  # Collect → Verify
    elif protocol == "delegated":
        return 1  # Delegation chain lookup
    else:
        return 3


def bft_round_lower_bound(f: int) -> int:
    """
    Lower bound on rounds for BFT consensus tolerating f faults.
    Fischer-Lynch-Paterson: asynchronous consensus impossible with 1 fault.
    Synchronous: f+1 rounds needed.
    """
    return f + 1


# ─── Space Complexity ─────────────────────────────────────────────

def trust_state_size(n_entities: int, trust_dims: int = 3,
                     bytes_per_dim: int = 8) -> int:
    """Bytes needed to store full trust state."""
    return n_entities * trust_dims * bytes_per_dim


def sparse_trust_state(n_entities: int, sparsity: float,
                       trust_dims: int = 3,
                       bytes_per_dim: int = 8,
                       id_bytes: int = 32) -> int:
    """
    Sparse representation: only store non-default trust values.
    Each entry: entity_id + trust_values.
    """
    n_nondefault = int(n_entities * (1 - sparsity))
    per_entry = id_bytes + trust_dims * bytes_per_dim
    return n_nondefault * per_entry


def log_state_size(n_attestations: int, entry_bytes: int = 128) -> int:
    """Size of attestation log (append-only)."""
    return n_attestations * entry_bytes


def merkle_proof_size(n_leaves: int, hash_bytes: int = 32) -> int:
    """Size of Merkle proof for attestation."""
    if n_leaves <= 1:
        return hash_bytes
    depth = math.ceil(math.log2(n_leaves))
    return depth * hash_bytes


# ─── Time Complexity ──────────────────────────────────────────────

def trust_lookup_time(n_entities: int, data_structure: str = "hashtable") -> str:
    """Time complexity for trust score lookup."""
    if data_structure == "hashtable":
        return "O(1)"
    elif data_structure == "btree":
        return f"O(log {n_entities})"
    elif data_structure == "sorted_array":
        return f"O(log {n_entities})"
    elif data_structure == "linear":
        return f"O({n_entities})"
    return "O(n)"


def trust_update_time(n_attestors: int, aggregation: str = "mean") -> str:
    """Time complexity for trust score update."""
    if aggregation == "mean":
        return f"O({n_attestors})"
    elif aggregation == "median":
        return f"O({n_attestors} log {n_attestors})"
    elif aggregation == "trimmed_mean":
        return f"O({n_attestors} log {n_attestors})"
    elif aggregation == "weighted":
        return f"O({n_attestors})"
    return f"O({n_attestors})"


# ─── Information-Theoretic Lower Bounds ───────────────────────────

def min_attestations_for_precision(target_error: float,
                                    confidence: float = 0.95) -> int:
    """
    Minimum attestations needed to estimate trust within target_error.
    From Hoeffding's inequality: n ≥ ln(2/α) / (2ε²).
    """
    alpha = 1 - confidence
    return math.ceil(math.log(2 / alpha) / (2 * target_error ** 2))


def min_bits_for_trust(levels: int) -> float:
    """Minimum bits needed to represent trust at given precision."""
    if levels <= 1:
        return 0.0
    return math.log2(levels)


def trust_verification_lower_bound(security_bits: int) -> int:
    """
    Minimum computation for trust verification with given security level.
    Adversary needs 2^security_bits work to forge.
    """
    return security_bits  # In terms of hash evaluations


# ─── Complexity Tradeoffs ─────────────────────────────────────────

@dataclass
class ComplexityProfile:
    communication: str
    rounds: int
    space: str
    time: str
    fault_tolerance: int


def analyze_protocol_complexity(n: int, f: int,
                                protocol: str) -> ComplexityProfile:
    """Analyze complexity profile of a trust protocol."""
    if protocol == "pbft":
        return ComplexityProfile(
            communication=f"O({n}²)",
            rounds=3,
            space=f"O({n})",
            time=f"O({n}²)",
            fault_tolerance=f,
        )
    elif protocol == "hotstuff":
        return ComplexityProfile(
            communication=f"O({n})",
            rounds=3,
            space=f"O({n})",
            time=f"O({n})",
            fault_tolerance=f,
        )
    elif protocol == "raft":
        return ComplexityProfile(
            communication=f"O({n})",
            rounds=2,
            space=f"O({n})",
            time=f"O({n})",
            fault_tolerance=f,
        )
    else:
        return ComplexityProfile(
            communication=f"O({n}²)",
            rounds=f + 1,
            space=f"O({n})",
            time=f"O({n}²)",
            fault_tolerance=f,
        )


def scalability_bottleneck(n: int, protocol: str) -> str:
    """Identify the primary scalability bottleneck."""
    msgs = consensus_message_complexity(n, protocol)

    if protocol in ["pbft", "tendermint"]:
        return f"communication: {msgs} messages (O(n²))"
    elif protocol in ["hotstuff", "raft"]:
        return f"leader bandwidth: {msgs} messages (O(n))"
    else:
        return f"unknown: {msgs} messages"


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
    print("Trust Protocol Complexity Bounds for Web4")
    print("Session 32, Track 7")
    print("=" * 70)

    # ── §1 Communication Complexity ─────────────────────────────
    print("\n§1 Communication Complexity\n")

    # PBFT is O(n²)
    pbft_100 = consensus_message_complexity(100, "pbft")
    pbft_1000 = consensus_message_complexity(1000, "pbft")
    check("pbft_quadratic", pbft_1000 / pbft_100 >= 90,
          f"ratio={pbft_1000/pbft_100:.1f}")

    # HotStuff is O(n)
    hs_100 = consensus_message_complexity(100, "hotstuff")
    hs_1000 = consensus_message_complexity(1000, "hotstuff")
    check("hotstuff_linear", abs(hs_1000 / hs_100 - 10) < 1,
          f"ratio={hs_1000/hs_100:.1f}")

    # HotStuff << PBFT at scale
    check("hotstuff_better_at_scale", hs_1000 < pbft_1000,
          f"hs={hs_1000} pbft={pbft_1000}")

    # Gossip convergence
    rounds = gossip_rounds_to_converge(1000, fanout=3)
    check("gossip_logarithmic", rounds < 20,
          f"rounds={rounds}")

    # ── §2 Round Complexity ─────────────────────────────────────
    print("\n§2 Round Complexity\n")

    check("interactive_3_rounds",
          trust_establishment_rounds("interactive") == 3)
    check("zk_1_round",
          trust_establishment_rounds("zero_knowledge") == 1)

    # BFT lower bound
    lb = bft_round_lower_bound(3)
    check("bft_lower_bound", lb == 4,
          f"lb={lb}")

    # ── §3 Space Complexity ─────────────────────────────────────
    print("\n§3 Space Complexity\n")

    # Full state for 10K entities
    full = trust_state_size(10000)
    check("full_state_240kb", abs(full - 240000) < 1000,
          f"size={full}")

    # Sparse saves space when most are default
    sparse = sparse_trust_state(10000, sparsity=0.9)
    check("sparse_smaller", sparse < full,
          f"sparse={sparse} full={full}")

    # Merkle proof size
    mp = merkle_proof_size(1_000_000)
    check("merkle_proof_small", mp < 1000,
          f"proof_size={mp} bytes")

    # ── §4 Time Complexity ──────────────────────────────────────
    print("\n§4 Time Complexity\n")

    check("hashtable_o1", trust_lookup_time(10000, "hashtable") == "O(1)")
    check("median_nlogn",
          "log" in trust_update_time(100, "median"))

    # ── §5 Information-Theoretic Bounds ─────────────────────────
    print("\n§5 Information-Theoretic Lower Bounds\n")

    # Attestations for ±0.05 error at 95% confidence
    n_attest = min_attestations_for_precision(0.05, 0.95)
    check("precision_005", n_attest > 500,
          f"n={n_attest}")

    # More precision → more attestations
    n_loose = min_attestations_for_precision(0.1, 0.95)
    check("tighter_needs_more", n_attest > n_loose,
          f"tight={n_attest} loose={n_loose}")

    # Bits for trust levels
    check("bits_256_levels", abs(min_bits_for_trust(256) - 8.0) < 0.01)
    check("bits_100_levels", min_bits_for_trust(100) < 7.0)

    # ── §6 Protocol Analysis ───────────────────────────────────
    print("\n§6 Protocol Complexity Analysis\n")

    pbft_profile = analyze_protocol_complexity(100, 33, "pbft")
    hs_profile = analyze_protocol_complexity(100, 33, "hotstuff")

    check("pbft_quadratic_comm", "²" in pbft_profile.communication)
    check("hotstuff_linear_comm", "²" not in hs_profile.communication)
    check("same_fault_tolerance",
          pbft_profile.fault_tolerance == hs_profile.fault_tolerance)

    # Bottleneck identification
    bottleneck = scalability_bottleneck(100, "pbft")
    check("pbft_bottleneck_comm", "n²" in bottleneck or "O(n²)" in bottleneck,
          bottleneck)

    # ── §7 Scalability Analysis ─────────────────────────────────
    print("\n§7 Scalability Tradeoffs\n")

    # At what n does PBFT become impractical? (>=1M messages)
    for n in [10, 100, 1000, 10000]:
        msgs = consensus_message_complexity(n, "pbft")
        if msgs >= 1_000_000:
            check("pbft_impractical_at_1000", n <= 1000,
                  f"n={n} msgs={msgs}")
            break

    # HotStuff stays practical
    hs_10k = consensus_message_complexity(10000, "hotstuff")
    check("hotstuff_practical_10k", hs_10k < 100_000,
          f"msgs={hs_10k}")

    # Bandwidth for 100 attestors
    bw = attestation_bandwidth(100, trust_dims=3)
    check("attestation_bandwidth", bw < 10000,
          f"bytes={bw}")

    # ── Summary ─────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
