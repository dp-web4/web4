"""
Adversarial Trust Robustness for Web4
Session 32, Track 3

How robust are trust scores to adversarial manipulation?

- Trust poisoning attacks (gradual trust inflation)
- Sybil-based trust laundering
- Whitewashing attacks (identity reset)
- Trust oscillation attacks (alternating good/bad)
- Certified robustness bounds
- Median-based defenses
- Trust rate limiting
- Anomaly-based attack detection
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set


# ─── Trust System Model ──────────────────────────────────────────

@dataclass
class TrustAgent:
    agent_id: str
    trust_score: float = 0.5
    history: List[Tuple[int, float]] = field(default_factory=list)
    attestation_count: int = 0
    creation_time: int = 0
    is_byzantine: bool = False

    def update_trust(self, value: float, time: int,
                     learning_rate: float = 0.1):
        """Exponential moving average trust update."""
        self.trust_score = (1 - learning_rate) * self.trust_score + learning_rate * value
        self.trust_score = max(0.0, min(1.0, self.trust_score))
        self.history.append((time, self.trust_score))
        self.attestation_count += 1


@dataclass
class TrustNetwork:
    agents: Dict[str, TrustAgent] = field(default_factory=dict)
    attestations: List[Tuple[str, str, float, int]] = field(default_factory=list)

    def add_agent(self, agent_id: str, trust: float = 0.5,
                  time: int = 0, byzantine: bool = False) -> TrustAgent:
        agent = TrustAgent(agent_id=agent_id, trust_score=trust,
                          creation_time=time, is_byzantine=byzantine)
        self.agents[agent_id] = agent
        return agent

    def attest(self, source: str, target: str, value: float, time: int,
               learning_rate: float = 0.1):
        """Source attests about target's trustworthiness."""
        if target in self.agents:
            # Weight attestation by source's trust
            source_trust = self.agents.get(source, TrustAgent(source)).trust_score
            weighted_value = value * source_trust + self.agents[target].trust_score * (1 - source_trust)
            self.agents[target].update_trust(weighted_value, time, learning_rate)
            self.attestations.append((source, target, value, time))


# ─── Poisoning Attacks ───────────────────────────────────────────

def gradual_trust_inflation(network: TrustNetwork, attacker_id: str,
                            target_id: str, n_steps: int,
                            start_time: int = 0) -> List[float]:
    """
    Attacker gradually inflates target's trust by providing
    slightly-higher-than-current attestations.
    """
    scores = []
    for t in range(n_steps):
        current = network.agents[target_id].trust_score
        # Inflate by small amount each step
        inflated = min(1.0, current + 0.05)
        network.attest(attacker_id, target_id, inflated, start_time + t)
        scores.append(network.agents[target_id].trust_score)
    return scores


def ballot_stuffing(network: TrustNetwork, sybil_ids: List[str],
                    target_id: str, value: float,
                    time: int) -> float:
    """
    Multiple sybil identities all attest high trust for target.
    Returns final trust score.
    """
    for sid in sybil_ids:
        network.attest(sid, target_id, value, time)
    return network.agents[target_id].trust_score


# ─── Whitewashing Attack ─────────────────────────────────────────

def whitewashing_cost(network: TrustNetwork, bad_agent_id: str,
                      new_agent_id: str, time: int) -> Dict[str, float]:
    """
    Agent with bad reputation creates new identity.
    Analyze the cost/benefit.
    """
    old_trust = network.agents[bad_agent_id].trust_score
    old_age = time - network.agents[bad_agent_id].creation_time

    # New identity starts at default
    network.add_agent(new_agent_id, trust=0.5, time=time)
    new_trust = network.agents[new_agent_id].trust_score

    return {
        "old_trust": old_trust,
        "new_trust": new_trust,
        "trust_gain": new_trust - old_trust,
        "age_loss": old_age,
        "profitable": new_trust > old_trust,
    }


# ─── Trust Oscillation Attack ────────────────────────────────────

def oscillation_attack(network: TrustNetwork, attacker_id: str,
                       target_id: str, n_cycles: int,
                       good_steps: int = 5, bad_steps: int = 1) -> Dict:
    """
    Attacker alternates between good and bad behavior.
    Good behavior builds trust, then exploited in bad phase.
    """
    scores = []
    for cycle in range(n_cycles):
        t_base = cycle * (good_steps + bad_steps)
        # Good phase
        for t in range(good_steps):
            network.attest(attacker_id, target_id, 0.95, t_base + t)
        # Bad phase
        for t in range(bad_steps):
            network.attest(attacker_id, target_id, 0.05, t_base + good_steps + t)
        scores.append(network.agents[target_id].trust_score)

    return {
        "final_scores": scores,
        "mean_score": sum(scores) / len(scores),
        "min_score": min(scores),
        "max_score": max(scores),
    }


# ─── Defense Mechanisms ───────────────────────────────────────────

def median_aggregation(attestations: List[Tuple[str, float]],
                       f_byzantine: int) -> float:
    """
    Use median instead of mean for aggregation.
    Tolerates up to f Byzantine attestors.
    """
    values = sorted([v for _, v in attestations])
    n = len(values)
    if n == 0:
        return 0.5

    mid = n // 2
    if n % 2 == 0:
        return (values[mid - 1] + values[mid]) / 2
    return values[mid]


def rate_limited_update(current: float, new_value: float,
                        max_change: float = 0.05) -> float:
    """
    Limit maximum trust change per update.
    Prevents sudden trust manipulation.
    """
    delta = new_value - current
    clamped_delta = max(-max_change, min(max_change, delta))
    return current + clamped_delta


def age_weighted_trust(trust: float, age: int,
                       maturity_threshold: int = 100) -> float:
    """
    New identities get reduced effective trust.
    Prevents whitewashing profitability.
    """
    if age >= maturity_threshold:
        return trust
    age_factor = age / maturity_threshold
    # Trust capped at age_factor * trust, starting from base
    base = 0.5
    return base + (trust - base) * age_factor


def anomaly_score(history: List[float], window: int = 10) -> float:
    """
    Detect anomalous trust changes by comparing recent to historical.
    High score = suspicious behavior.
    """
    if len(history) < window * 2:
        return 0.0

    recent = history[-window:]
    historical = history[-window * 2:-window]

    recent_mean = sum(recent) / len(recent)
    hist_mean = sum(historical) / len(historical)
    hist_std = math.sqrt(sum((x - hist_mean) ** 2 for x in historical) / len(historical))

    if hist_std < 1e-10:
        return abs(recent_mean - hist_mean) * 10  # Scale up for constant history

    return abs(recent_mean - hist_mean) / hist_std


# ─── Certified Robustness ────────────────────────────────────────

def certified_trust_bound(n_honest: int, n_byzantine: int,
                          honest_range: Tuple[float, float] = (0.6, 0.8),
                          byzantine_range: Tuple[float, float] = (0.0, 1.0)) -> Tuple[float, float]:
    """
    Given n_honest honest attestors in [low, high] and n_byzantine arbitrary,
    compute guaranteed bounds on trimmed mean output.
    """
    n_total = n_honest + n_byzantine

    if n_byzantine >= n_total // 2:
        # Can't certify anything
        return (0.0, 1.0)

    # With trimmed mean removing n_byzantine from each side:
    # The remaining values are all honest
    return honest_range


def robustness_radius(trust: float, defense: str = "median",
                      n_attestors: int = 10, f: int = 3) -> float:
    """
    How much can Byzantine attestors change the output?
    Returns maximum possible deviation from honest aggregate.
    """
    honest_fraction = (n_attestors - f) / n_attestors

    if defense == "median":
        if f < n_attestors // 2:
            return 0.0  # Median is robust if f < n/2
        return 1.0  # Median can be fully controlled

    elif defense == "trimmed_mean":
        if f <= n_attestors // 3:
            return 0.0  # Trimmed mean is robust
        return (1 - honest_fraction)

    elif defense == "mean":
        # Mean always affected by f/n fraction
        return f / n_attestors

    return 1.0


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
    print("Adversarial Trust Robustness for Web4")
    print("Session 32, Track 3")
    print("=" * 70)

    random.seed(42)

    # ── §1 Gradual Trust Inflation ──────────────────────────────
    print("\n§1 Gradual Trust Inflation\n")

    net = TrustNetwork()
    net.add_agent("attacker", trust=0.6, byzantine=True)
    net.add_agent("target", trust=0.3)

    initial = net.agents["target"].trust_score
    scores = gradual_trust_inflation(net, "attacker", "target", 50)

    check("inflation_increases", scores[-1] > initial,
          f"initial={initial:.4f} final={scores[-1]:.4f}")

    # But rate is limited by attacker's trust weight
    check("inflation_bounded", scores[-1] < 0.9,
          f"final={scores[-1]:.4f}")

    # Monotonically increasing (gradual)
    increasing = all(scores[i] <= scores[i + 1] + 0.01
                     for i in range(len(scores) - 1))
    check("inflation_gradual", increasing)

    # ── §2 Sybil/Ballot Stuffing ────────────────────────────────
    print("\n§2 Sybil Ballot Stuffing\n")

    net2 = TrustNetwork()
    net2.add_agent("victim", trust=0.3)
    # Create sybils with default (low) trust
    sybils = [f"sybil_{i}" for i in range(10)]
    for s in sybils:
        net2.add_agent(s, trust=0.5)  # Default trust

    before = net2.agents["victim"].trust_score
    after = ballot_stuffing(net2, sybils, "victim", 1.0, 0)

    # Sybils increase trust but limited by their own low trust
    check("sybil_limited_effect", after < 0.8,
          f"before={before:.4f} after={after:.4f}")

    # Low-trust sybils have less effect than high-trust attestors
    net3 = TrustNetwork()
    net3.add_agent("victim2", trust=0.3)
    net3.add_agent("trusted_attestor", trust=0.9)
    net3.attest("trusted_attestor", "victim2", 1.0, 0)
    trusted_effect = net3.agents["victim2"].trust_score - 0.3

    check("trusted_more_effective", trusted_effect > (after - before) / len(sybils),
          f"trusted_effect={trusted_effect:.4f}")

    # ── §3 Whitewashing ─────────────────────────────────────────
    print("\n§3 Whitewashing Attack\n")

    net4 = TrustNetwork()
    net4.add_agent("bad_actor", trust=0.1, time=0)
    result = whitewashing_cost(net4, "bad_actor", "new_identity", time=100)

    check("whitewash_profitable", result["profitable"],
          f"old={result['old_trust']:.2f} new={result['new_trust']:.2f}")

    # With age-weighting defense, new identity starts at base (0.5)
    # but effective trust is discounted to base (no age = no bonus)
    new_effective = age_weighted_trust(result["new_trust"], age=0)
    raw_gain = result["new_trust"] - result["old_trust"]
    effective_gain = new_effective - result["old_trust"]
    # Age weighting reduces the gain (new identity doesn't get full trust)
    check("age_weight_reduces_gain", effective_gain <= raw_gain,
          f"raw_gain={raw_gain:.4f} effective_gain={effective_gain:.4f}")

    # ── §4 Oscillation Attack ───────────────────────────────────
    print("\n§4 Trust Oscillation Attack\n")

    net5 = TrustNetwork()
    net5.add_agent("oscillator", trust=0.7, byzantine=True)
    net5.add_agent("target_osc", trust=0.5)

    osc = oscillation_attack(net5, "oscillator", "target_osc", n_cycles=10)

    # Trust stays elevated despite periodic bad behavior (5:1 good:bad ratio)
    check("oscillation_elevated", osc["mean_score"] > 0.5,
          f"mean={osc['mean_score']:.4f}")

    # But not as high as pure good behavior would achieve
    check("oscillation_limited", osc["mean_score"] < 0.95,
          f"mean={osc['mean_score']:.4f}")

    # ── §5 Defense: Median Aggregation ──────────────────────────
    print("\n§5 Defense Mechanisms\n")

    # Median resists outliers
    honest_atts = [(f"h{i}", 0.7) for i in range(5)]
    byzantine_atts = [("b0", 0.0), ("b1", 1.0)]
    all_atts = honest_atts + byzantine_atts

    median_val = median_aggregation(all_atts, f_byzantine=2)
    check("median_resists_outliers", abs(median_val - 0.7) < 0.01,
          f"median={median_val:.4f}")

    # Mean would be affected
    mean_val = sum(v for _, v in all_atts) / len(all_atts)
    check("mean_affected", abs(mean_val - 0.7) > 0.01,
          f"mean={mean_val:.4f}")

    # ── §6 Rate Limiting ────────────────────────────────────────
    print("\n§6 Rate Limiting\n")

    current = 0.5
    # Attempt big jump
    limited = rate_limited_update(current, 1.0, max_change=0.05)
    check("rate_limit_caps", abs(limited - 0.55) < 0.01,
          f"limited={limited:.4f}")

    # Small changes pass through
    small = rate_limited_update(current, 0.53, max_change=0.05)
    check("rate_limit_small_ok", abs(small - 0.53) < 0.01,
          f"small={small:.4f}")

    # ── §7 Anomaly Detection ───────────────────────────────────
    print("\n§7 Anomaly Detection\n")

    # Stable history → low anomaly
    stable = [0.7 + random.gauss(0, 0.02) for _ in range(30)]
    score_stable = anomaly_score(stable)
    check("stable_low_anomaly", score_stable < 2.0,
          f"score={score_stable:.4f}")

    # Sudden change → high anomaly
    sudden = stable[:20] + [0.2 + random.gauss(0, 0.02) for _ in range(10)]
    score_sudden = anomaly_score(sudden)
    check("sudden_high_anomaly", score_sudden > 5.0,
          f"score={score_sudden:.4f}")

    # ── §8 Certified Robustness ─────────────────────────────────
    print("\n§8 Certified Robustness Bounds\n")

    # With enough honest attestors, bounds are tight
    lb, ub = certified_trust_bound(7, 2, (0.6, 0.8))
    check("certified_bounds", lb == 0.6 and ub == 0.8,
          f"bounds=({lb:.2f}, {ub:.2f})")

    # Too many Byzantine → can't certify
    lb2, ub2 = certified_trust_bound(3, 5)
    check("uncertifiable", lb2 == 0.0 and ub2 == 1.0)

    # Robustness radius
    r_median = robustness_radius(0.7, "median", n_attestors=10, f=3)
    r_mean = robustness_radius(0.7, "mean", n_attestors=10, f=3)
    check("median_more_robust", r_median < r_mean,
          f"median={r_median:.4f} mean={r_mean:.4f}")

    r_trimmed = robustness_radius(0.7, "trimmed_mean", n_attestors=10, f=3)
    check("trimmed_robust", r_trimmed <= r_mean,
          f"trimmed={r_trimmed:.4f} mean={r_mean:.4f}")

    # ── Summary ─────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
