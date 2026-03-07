"""
Consensus Latency Analysis for Web4
Session 30, Track 7

Formal analysis of consensus protocol latency:
- Message delay models (fixed, uniform, exponential)
- Round-trip latency for different consensus protocols
- Network diameter impact on finality
- Pipelining effects (chained consensus)
- Latency vs throughput tradeoffs
- Geographic distribution effects
- Tail latency analysis (p99, p999)
- Optimistic fast path vs pessimistic slow path
"""

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional


# ─── Delay Models ──────────────────────────────────────────────────

class DelayModel(Enum):
    FIXED = "fixed"
    UNIFORM = "uniform"
    EXPONENTIAL = "exponential"
    LOGNORMAL = "lognormal"


def sample_delay(model: DelayModel, base_delay: float,
                 rng: random.Random) -> float:
    """Sample a network delay from the given model."""
    if model == DelayModel.FIXED:
        return base_delay
    elif model == DelayModel.UNIFORM:
        return rng.uniform(base_delay * 0.5, base_delay * 1.5)
    elif model == DelayModel.EXPONENTIAL:
        return rng.expovariate(1.0 / base_delay)
    elif model == DelayModel.LOGNORMAL:
        mu = math.log(base_delay) - 0.5 * 0.5 ** 2  # adjust for mean
        return rng.lognormvariate(mu, 0.5)
    return base_delay


# ─── Protocol Models ──────────────────────────────────────────────

@dataclass
class ProtocolLatency:
    """Latency characteristics of a consensus protocol."""
    name: str
    phases: int           # number of communication phases
    messages_per_phase: int  # messages per phase (for n nodes)
    optimistic_multiplier: float = 1.0  # fast path multiplier
    pessimistic_multiplier: float = 1.0  # slow path multiplier


def pbft_latency(n: int, base_delay: float) -> Dict:
    """
    PBFT: 3 phases (pre-prepare, prepare, commit).
    Each phase: O(n) messages, leader broadcasts.
    Latency: 3 * RTT + processing.
    """
    phases = 3
    messages_total = n + n * (n - 1) + n * (n - 1)  # 1-to-all + all-to-all + all-to-all
    latency = phases * base_delay * 2  # RTT per phase

    return {
        "name": "PBFT",
        "phases": phases,
        "total_messages": messages_total,
        "latency": latency,
        "message_complexity": f"O(n²) = {messages_total}",
    }


def hotstuff_latency(n: int, base_delay: float) -> Dict:
    """
    HotStuff: 3 phases (prepare, pre-commit, commit).
    Each phase: O(n) messages (leader-based).
    Latency: 3 * RTT.
    """
    phases = 3
    messages_total = 3 * (2 * n)  # leader sends n, receives n per phase
    latency = phases * base_delay * 2

    return {
        "name": "HotStuff",
        "phases": phases,
        "total_messages": messages_total,
        "latency": latency,
        "message_complexity": f"O(n) = {messages_total}",
    }


def raft_latency(n: int, base_delay: float) -> Dict:
    """
    Raft: 1 phase for normal operation (leader → followers → ack).
    Latency: 1 RTT (optimistic).
    Not BFT, but included for comparison.
    """
    messages_total = 2 * (n - 1)  # leader sends to all, receives acks
    latency = base_delay * 2  # 1 RTT

    return {
        "name": "Raft",
        "phases": 1,
        "total_messages": messages_total,
        "latency": latency,
        "message_complexity": f"O(n) = {messages_total}",
    }


def tendermint_latency(n: int, base_delay: float) -> Dict:
    """
    Tendermint: 3 phases (propose, prevote, precommit).
    All-to-all in prevote/precommit.
    Latency: 3 * RTT.
    """
    phases = 3
    messages_total = n + n * (n - 1) + n * (n - 1)
    latency = phases * base_delay * 2

    return {
        "name": "Tendermint",
        "phases": phases,
        "total_messages": messages_total,
        "latency": latency,
        "message_complexity": f"O(n²) = {messages_total}",
    }


# ─── Simulation ───────────────────────────────────────────────────

def simulate_consensus_latency(n: int, protocol_fn, delay_model: DelayModel,
                                base_delay: float, trials: int = 1000,
                                seed: int = 42) -> Dict:
    """
    Monte Carlo simulation of consensus latency.
    """
    rng = random.Random(seed)
    latencies = []

    for _ in range(trials):
        proto = protocol_fn(n, base_delay)
        total_latency = 0.0

        for phase in range(proto["phases"]):
            # Each phase: max delay among messages (parallel delivery)
            phase_delays = [sample_delay(delay_model, base_delay, rng)
                           for _ in range(min(n, 20))]  # cap for performance
            total_latency += max(phase_delays) if phase_delays else base_delay

        latencies.append(total_latency)

    latencies.sort()
    n_trials = len(latencies)

    return {
        "protocol": proto["name"],
        "n_nodes": n,
        "delay_model": delay_model.value,
        "mean": sum(latencies) / n_trials,
        "median": latencies[n_trials // 2],
        "p99": latencies[int(n_trials * 0.99)],
        "p999": latencies[min(int(n_trials * 0.999), n_trials - 1)],
        "min": latencies[0],
        "max": latencies[-1],
    }


# ─── Finality Analysis ────────────────────────────────────────────

def finality_time(protocol_phases: int, network_diameter: int,
                  base_delay: float) -> float:
    """
    Time to finality: phases * diameter * base_delay.
    In well-connected networks, diameter is small.
    """
    return protocol_phases * network_diameter * base_delay


def pipelining_throughput(base_latency: float, pipeline_depth: int) -> Dict:
    """
    With pipelining, throughput = pipeline_depth / base_latency.
    Each slot processes a different consensus instance.
    """
    if base_latency <= 0:
        return {"throughput": 0, "latency_per_decision": base_latency}

    throughput = pipeline_depth / base_latency
    effective_latency = base_latency  # latency doesn't change, throughput does

    return {
        "pipeline_depth": pipeline_depth,
        "base_latency": base_latency,
        "throughput_decisions_per_unit": throughput,
        "latency_per_decision": effective_latency,
        "speedup_vs_sequential": pipeline_depth,
    }


# ─── Geographic Distribution ──────────────────────────────────────

# Approximate one-way latencies (ms) between regions
REGION_LATENCIES = {
    ("us-east", "us-west"): 40,
    ("us-east", "eu-west"): 80,
    ("us-east", "asia-east"): 150,
    ("us-west", "eu-west"): 120,
    ("us-west", "asia-east"): 100,
    ("eu-west", "asia-east"): 130,
}


def get_inter_region_latency(r1: str, r2: str) -> float:
    """Get latency between two regions (symmetric)."""
    if r1 == r2:
        return 1.0  # intra-region
    key = tuple(sorted([r1, r2]))
    return REGION_LATENCIES.get(key, 100.0)


def geo_distributed_consensus_latency(node_regions: List[str],
                                       protocol_phases: int) -> Dict:
    """
    Consensus latency for geographically distributed nodes.
    Bottleneck is the slowest link needed for quorum.
    """
    n = len(node_regions)
    quorum = (2 * n) // 3 + 1  # BFT quorum

    # For each leader candidate, compute latency to reach quorum
    best_latency = float('inf')
    best_leader = 0

    for leader_idx in range(n):
        leader_region = node_regions[leader_idx]
        # Latency to each other node
        delays = sorted([
            get_inter_region_latency(leader_region, node_regions[j])
            for j in range(n) if j != leader_idx
        ])
        # Need quorum-1 responses (leader counts as 1)
        quorum_latency = delays[quorum - 2] if len(delays) >= quorum - 1 else delays[-1]
        total = protocol_phases * 2 * quorum_latency  # RTT per phase

        if total < best_latency:
            best_latency = total
            best_leader = leader_idx

    return {
        "n_nodes": n,
        "quorum": quorum,
        "best_leader_region": node_regions[best_leader],
        "best_latency_ms": best_latency,
        "worst_latency_ms": max(
            protocol_phases * 2 * max(
                get_inter_region_latency(node_regions[i], node_regions[j])
                for j in range(n) if j != i
            )
            for i in range(n)
        ),
    }


# ─── Optimistic vs Pessimistic Path ───────────────────────────────

def fast_path_probability(n: int, f: int, failure_prob: float) -> float:
    """
    Probability that fast path succeeds (all nodes respond on time).

    Fast path requires all n nodes.
    Slow path requires only n-f nodes.
    """
    # P(all respond) = (1 - failure_prob)^n
    return (1 - failure_prob) ** n


def expected_latency_with_fast_path(fast_latency: float, slow_latency: float,
                                     fast_prob: float) -> float:
    """Expected latency considering fast/slow path probabilities."""
    return fast_prob * fast_latency + (1 - fast_prob) * slow_latency


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
    print("Consensus Latency Analysis for Web4")
    print("Session 30, Track 7")
    print("=" * 70)

    # ── §1 Protocol Latency Comparison ────────────────────────────
    print("\n§1 Protocol Latency Comparison\n")

    n = 100
    base = 10.0  # ms

    pbft = pbft_latency(n, base)
    hs = hotstuff_latency(n, base)
    raft_l = raft_latency(n, base)
    tend = tendermint_latency(n, base)

    # HotStuff fewer messages than PBFT
    check("hotstuff_fewer_msgs", hs["total_messages"] < pbft["total_messages"],
          f"hs={hs['total_messages']} pbft={pbft['total_messages']}")

    # Raft has lowest latency (1 phase, not BFT)
    check("raft_lowest_latency", raft_l["latency"] < hs["latency"],
          f"raft={raft_l['latency']} hs={hs['latency']}")

    # PBFT and Tendermint same latency (same phase count)
    check("pbft_tendermint_same_latency",
          abs(pbft["latency"] - tend["latency"]) < 0.1)

    # HotStuff and PBFT same latency (3 phases each)
    check("hotstuff_pbft_same_latency",
          abs(hs["latency"] - pbft["latency"]) < 0.1)

    # ── §2 Delay Models ──────────────────────────────────────────
    print("\n§2 Delay Model Characteristics\n")

    rng = random.Random(42)
    n_samples = 1000

    fixed_delays = [sample_delay(DelayModel.FIXED, 10, rng) for _ in range(n_samples)]
    check("fixed_constant", all(d == 10.0 for d in fixed_delays))

    exp_delays = [sample_delay(DelayModel.EXPONENTIAL, 10, rng) for _ in range(n_samples)]
    exp_mean = sum(exp_delays) / len(exp_delays)
    check("exp_mean_near_base", abs(exp_mean - 10) < 3,
          f"mean={exp_mean:.1f}")

    # Exponential has high variance (heavy tail)
    exp_var = sum((d - exp_mean) ** 2 for d in exp_delays) / len(exp_delays)
    check("exp_high_variance", exp_var > 30, f"var={exp_var:.1f}")

    # Uniform bounded
    uni_delays = [sample_delay(DelayModel.UNIFORM, 10, rng) for _ in range(n_samples)]
    check("uniform_bounded", all(5 <= d <= 15 for d in uni_delays))

    # ── §3 Monte Carlo Simulation ─────────────────────────────────
    print("\n§3 Monte Carlo Consensus Simulation\n")

    sim_fixed = simulate_consensus_latency(10, hotstuff_latency, DelayModel.FIXED, 10)
    sim_exp = simulate_consensus_latency(10, hotstuff_latency, DelayModel.EXPONENTIAL, 10)

    # Fixed delay → no variance
    check("fixed_no_variance", sim_fixed["mean"] == sim_fixed["median"],
          f"mean={sim_fixed['mean']:.1f} median={sim_fixed['median']:.1f}")

    # Exponential has tail
    check("exp_p99_higher", sim_exp["p99"] > sim_exp["mean"],
          f"p99={sim_exp['p99']:.1f} mean={sim_exp['mean']:.1f}")

    # p999 > p99 > median
    check("exp_tail_ordering",
          sim_exp["p999"] >= sim_exp["p99"] >= sim_exp["median"],
          f"p999={sim_exp['p999']:.1f} p99={sim_exp['p99']:.1f} med={sim_exp['median']:.1f}")

    # ── §4 Finality Time ──────────────────────────────────────────
    print("\n§4 Finality Time\n")

    ft_small = finality_time(3, 2, 10)   # 3 phases, diameter 2
    ft_large = finality_time(3, 5, 10)   # 3 phases, diameter 5

    check("larger_diameter_slower", ft_large > ft_small,
          f"small={ft_small} large={ft_large}")

    # More phases → slower finality
    ft_1phase = finality_time(1, 3, 10)
    ft_3phase = finality_time(3, 3, 10)
    check("more_phases_slower", ft_3phase > ft_1phase)

    # ── §5 Pipelining ─────────────────────────────────────────────
    print("\n§5 Pipelining Effects\n")

    pipe = pipelining_throughput(60.0, 3)  # 60ms latency, 3-deep pipeline
    check("pipeline_3x_throughput", pipe["speedup_vs_sequential"] == 3)
    check("pipeline_throughput", abs(pipe["throughput_decisions_per_unit"] - 0.05) < 0.01,
          f"throughput={pipe['throughput_decisions_per_unit']:.4f}")

    # Deeper pipeline → higher throughput
    pipe_deep = pipelining_throughput(60.0, 5)
    check("deeper_pipeline_more_throughput",
          pipe_deep["throughput_decisions_per_unit"] > pipe["throughput_decisions_per_unit"])

    # Latency doesn't change with pipelining
    check("pipeline_same_latency",
          pipe["latency_per_decision"] == pipe_deep["latency_per_decision"])

    # ── §6 Geographic Distribution ────────────────────────────────
    print("\n§6 Geographic Consensus Latency\n")

    # All in same region → fast
    same_region = ["us-east"] * 4
    geo_same = geo_distributed_consensus_latency(same_region, 3)

    # Distributed across regions → slower
    distributed = ["us-east", "us-west", "eu-west", "asia-east"]
    geo_dist = geo_distributed_consensus_latency(distributed, 3)

    check("same_region_faster", geo_same["best_latency_ms"] < geo_dist["best_latency_ms"],
          f"same={geo_same['best_latency_ms']} dist={geo_dist['best_latency_ms']}")

    # Leader selection matters
    check("best_leader_chosen", geo_dist["best_leader_region"] in distributed)

    # Quorum is 3 for 4 nodes
    check("quorum_correct", geo_dist["quorum"] == 3)

    # ── §7 Fast Path Analysis ─────────────────────────────────────
    print("\n§7 Optimistic Fast Path\n")

    # No failures → fast path always succeeds
    fp_perfect = fast_path_probability(10, 3, 0.0)
    check("perfect_fast_path", fp_perfect == 1.0)

    # With failures → fast path less likely
    fp_5pct = fast_path_probability(10, 3, 0.05)
    check("failure_reduces_fast_path", fp_5pct < 1.0,
          f"prob={fp_5pct:.4f}")

    # More nodes → less likely fast path
    fp_100 = fast_path_probability(100, 33, 0.05)
    check("more_nodes_less_fast", fp_100 < fp_5pct,
          f"n10={fp_5pct:.4f} n100={fp_100:.4f}")

    # Expected latency
    exp_lat = expected_latency_with_fast_path(30, 90, fp_5pct)
    check("expected_between_fast_slow", 30 <= exp_lat <= 90,
          f"expected={exp_lat:.1f}")

    # ── §8 Scaling Analysis ───────────────────────────────────────
    print("\n§8 Latency Scaling with Network Size\n")

    sizes = [10, 50, 100, 500]
    pbft_msgs = [pbft_latency(n, 10)["total_messages"] for n in sizes]
    hs_msgs = [hotstuff_latency(n, 10)["total_messages"] for n in sizes]

    # PBFT O(n²): quadratic growth
    check("pbft_quadratic", pbft_msgs[-1] / pbft_msgs[0] > (sizes[-1] / sizes[0]),
          f"ratio={pbft_msgs[-1] / pbft_msgs[0]:.1f} expected>{sizes[-1]/sizes[0]}")

    # HotStuff O(n): linear growth
    hs_ratio = hs_msgs[-1] / hs_msgs[0]
    expected_ratio = sizes[-1] / sizes[0]
    check("hotstuff_linear", abs(hs_ratio - expected_ratio) / expected_ratio < 0.1,
          f"ratio={hs_ratio:.1f} expected={expected_ratio:.1f}")

    # Latency is constant (same number of phases regardless of n)
    lat_10 = hotstuff_latency(10, 10)["latency"]
    lat_500 = hotstuff_latency(500, 10)["latency"]
    check("hotstuff_constant_latency", lat_10 == lat_500,
          f"n10={lat_10} n500={lat_500}")

    # ── §9 Tail Latency ──────────────────────────────────────────
    print("\n§9 Tail Latency Analysis\n")

    sim_ln = simulate_consensus_latency(20, hotstuff_latency, DelayModel.LOGNORMAL, 10, trials=2000)

    # Lognormal has fat tail
    tail_ratio = sim_ln["p99"] / sim_ln["median"]
    check("lognormal_fat_tail", tail_ratio > 1.3,
          f"ratio={tail_ratio:.2f}")

    # p999 is even further
    check("p999_further", sim_ln["p999"] > sim_ln["p99"],
          f"p999={sim_ln['p999']:.1f} p99={sim_ln['p99']:.1f}")

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
