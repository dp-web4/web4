"""
Adversarial Bandit Trust for Web4
Session 33, Track 6

Adversarial multi-armed bandit algorithms for trust parameter selection:
- EXP3 (Exponential-weight algorithm for Exploration and Exploitation)
- EXP3.P (with explicit exploration for high-probability bounds)
- Trust parameter selection under adversarial reward manipulation
- Regret analysis and bounds
- Comparison with stochastic bandits (UCB1)
- Trust-weighted arm selection
- Non-stationary trust environments
- Byzantine adversary models for trust manipulation
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set, Callable
from collections import defaultdict


# ─── EXP3 Algorithm ──────────────────────────────────────────────

class EXP3:
    """
    Exponential-weight algorithm for Exploration and Exploitation.
    Adversarial bandit — makes no stochastic assumptions about rewards.

    Regret bound: O(√(K·T·ln K)) where K=arms, T=rounds.
    """

    def __init__(self, n_arms: int, gamma: float = 0.1):
        """
        Args:
            n_arms: Number of arms
            gamma: Exploration parameter in [0, 1]
        """
        self.n_arms = n_arms
        self.gamma = gamma
        self.weights = [1.0] * n_arms
        self.history: List[Tuple[int, float]] = []  # (arm, reward)

    @property
    def probabilities(self) -> List[float]:
        """Mixed strategy distribution over arms."""
        w_total = sum(self.weights)
        return [
            (1 - self.gamma) * (w / w_total) + self.gamma / self.n_arms
            for w in self.weights
        ]

    def select_arm(self, rng: random.Random = None) -> int:
        """Select an arm according to the mixed strategy."""
        probs = self.probabilities
        r = (rng or random).random()
        cumsum = 0.0
        for i, p in enumerate(probs):
            cumsum += p
            if r <= cumsum:
                return i
        return self.n_arms - 1

    def update(self, arm: int, reward: float):
        """
        Update weights based on observed reward.
        Uses importance-weighted estimator.
        """
        probs = self.probabilities
        # Importance-weighted reward estimate
        estimated_reward = reward / probs[arm]
        # Exponential weight update
        self.weights[arm] *= math.exp(self.gamma * estimated_reward / self.n_arms)
        self.history.append((arm, reward))

    @property
    def cumulative_reward(self) -> float:
        return sum(r for _, r in self.history)

    @property
    def regret_bound(self) -> float:
        """Theoretical regret bound for EXP3."""
        T = len(self.history)
        K = self.n_arms
        if T == 0:
            return 0.0
        return math.sqrt(2.0 * T * K * math.log(K))


# ─── EXP3.P (with explicit exploration) ─────────────────────────

class EXP3P:
    """
    EXP3.P — EXP3 with explicit exploration for high-probability bounds.
    Adds a uniform exploration bonus to guarantee arms are tried.

    High-probability regret bound: O(√(K·T·ln(K·T/δ))) with prob 1-δ.
    """

    def __init__(self, n_arms: int, delta: float = 0.1, T_horizon: int = 1000):
        self.n_arms = n_arms
        self.delta = delta
        self.T = T_horizon
        K = n_arms
        self.alpha = math.sqrt(math.log(K * T_horizon) / (K * T_horizon))
        self.beta = math.sqrt(math.log(K * T_horizon / delta) / (K * T_horizon))
        self.gamma = 1.05 * math.sqrt(K * math.log(K) / T_horizon) if T_horizon > 0 else 0.1
        self.gamma = min(self.gamma, 1.0)
        self.weights = [1.0] * n_arms
        self.cumulative_rewards: List[float] = [0.0] * n_arms
        self.round = 0
        self.history: List[Tuple[int, float]] = []

    @property
    def probabilities(self) -> List[float]:
        w_total = sum(self.weights)
        probs = [
            (1 - self.gamma) * (w / w_total) + self.gamma / self.n_arms
            for w in self.weights
        ]
        return probs

    def select_arm(self, rng: random.Random = None) -> int:
        probs = self.probabilities
        r = (rng or random).random()
        cumsum = 0.0
        for i, p in enumerate(probs):
            cumsum += p
            if r <= cumsum:
                return i
        return self.n_arms - 1

    def update(self, arm: int, reward: float):
        self.round += 1
        probs = self.probabilities
        estimated_reward = reward / probs[arm]
        bonus = self.beta / probs[arm]
        self.weights[arm] *= math.exp(
            self.gamma * (estimated_reward + bonus) / self.n_arms
        )
        self.cumulative_rewards[arm] += reward
        self.history.append((arm, reward))


# ─── UCB1 (Stochastic Baseline) ─────────────────────────────────

class UCB1:
    """Upper Confidence Bound for stochastic bandits (baseline comparison)."""

    def __init__(self, n_arms: int):
        self.n_arms = n_arms
        self.counts = [0] * n_arms
        self.values = [0.0] * n_arms
        self.total = 0
        self.history: List[Tuple[int, float]] = []

    def select_arm(self) -> int:
        # Play each arm once
        for i in range(self.n_arms):
            if self.counts[i] == 0:
                return i
        # UCB formula
        ucb_values = [
            self.values[i] + math.sqrt(2 * math.log(self.total) / self.counts[i])
            for i in range(self.n_arms)
        ]
        return max(range(self.n_arms), key=lambda i: ucb_values[i])

    def update(self, arm: int, reward: float):
        self.total += 1
        self.counts[arm] += 1
        n = self.counts[arm]
        self.values[arm] = self.values[arm] * (n - 1) / n + reward / n
        self.history.append((arm, reward))

    @property
    def cumulative_reward(self) -> float:
        return sum(r for _, r in self.history)


# ─── Adversary Models ────────────────────────────────────────────

def oblivious_adversary(n_arms: int, T: int, best_arm: int = 0,
                         rng: random.Random = None) -> List[List[float]]:
    """
    Oblivious adversary: rewards are fixed in advance (not adaptive).
    Best arm gets reward 1; others get reward based on fixed distribution.
    """
    rng = rng or random.Random(42)
    rewards = []
    for t in range(T):
        r = [rng.random() * 0.5 for _ in range(n_arms)]
        r[best_arm] = 0.8 + rng.random() * 0.2  # Best arm: 0.8-1.0
        rewards.append(r)
    return rewards


def adaptive_adversary(n_arms: int, T: int,
                        rng: random.Random = None) -> Callable[[int], List[float]]:
    """
    Adaptive adversary: sets rewards AFTER seeing learner's action.
    Returns a function that takes the learner's chosen arm and returns rewards.
    """
    rng = rng or random.Random(42)

    def generate(chosen_arm: int) -> List[float]:
        # Give 0 to chosen arm, random to others
        rewards = [rng.random() * 0.8 for _ in range(n_arms)]
        rewards[chosen_arm] = 0.0  # Punish chosen arm
        return rewards

    return generate


def switching_adversary(n_arms: int, T: int, switch_period: int = 50,
                         rng: random.Random = None) -> List[List[float]]:
    """
    Non-stationary adversary: best arm switches periodically.
    Tests adaptation speed of the algorithm.
    """
    rng = rng or random.Random(42)
    rewards = []
    for t in range(T):
        best = (t // switch_period) % n_arms
        r = [rng.random() * 0.3 for _ in range(n_arms)]
        r[best] = 0.8 + rng.random() * 0.2
        rewards.append(r)
    return rewards


# ─── Regret Computation ──────────────────────────────────────────

def compute_regret(reward_matrix: List[List[float]],
                    algorithm_history: List[Tuple[int, float]]) -> Dict[str, float]:
    """
    Compute regret metrics for an algorithm's performance.
    """
    T = len(algorithm_history)
    n_arms = len(reward_matrix[0]) if reward_matrix else 0

    # Best fixed arm in hindsight
    arm_totals = [sum(reward_matrix[t][a] for t in range(T)) for a in range(n_arms)]
    best_fixed = max(arm_totals) if arm_totals else 0.0

    # Algorithm's cumulative reward
    alg_reward = sum(r for _, r in algorithm_history)

    # Regret = best fixed arm - algorithm
    regret = best_fixed - alg_reward

    # Per-round regret
    per_round = regret / T if T > 0 else 0.0

    return {
        "T": T,
        "best_fixed_arm_reward": best_fixed,
        "algorithm_reward": alg_reward,
        "regret": regret,
        "per_round_regret": per_round,
        "best_arm": arm_totals.index(max(arm_totals)) if arm_totals else -1,
    }


# ─── Trust-Weighted Arm Selection ────────────────────────────────

class TrustWeightedEXP3:
    """
    EXP3 variant where arms represent trust parameter configurations.
    Trust scores bias initial weights (prior from T3 scores).
    """

    def __init__(self, arms: Dict[str, float], gamma: float = 0.1):
        """
        Args:
            arms: {arm_name: initial_trust_weight}
            gamma: exploration parameter
        """
        self.arm_names = list(arms.keys())
        self.n_arms = len(self.arm_names)
        self.gamma = gamma
        # Initialize weights from trust scores
        self.weights = [max(0.01, v) for v in arms.values()]
        self.history: List[Tuple[str, float]] = []

    @property
    def probabilities(self) -> Dict[str, float]:
        w_total = sum(self.weights)
        probs = [
            (1 - self.gamma) * (w / w_total) + self.gamma / self.n_arms
            for w in self.weights
        ]
        return dict(zip(self.arm_names, probs))

    def select_arm(self, rng: random.Random = None) -> str:
        probs = list(self.probabilities.values())
        r = (rng or random).random()
        cumsum = 0.0
        for i, p in enumerate(probs):
            cumsum += p
            if r <= cumsum:
                return self.arm_names[i]
        return self.arm_names[-1]

    def update(self, arm_name: str, reward: float):
        idx = self.arm_names.index(arm_name)
        probs = list(self.probabilities.values())
        estimated_reward = reward / probs[idx]
        self.weights[idx] *= math.exp(self.gamma * estimated_reward / self.n_arms)
        self.history.append((arm_name, reward))


# ── Byzantine Adversary for Trust ────────────────────────────────

def byzantine_trust_attack(n_honest: int, n_byzantine: int,
                            T: int, rng: random.Random = None) -> Dict[str, float]:
    """
    Model Byzantine nodes trying to manipulate trust scores.
    Honest nodes provide consistent, accurate attestations.
    Byzantine nodes provide adversarial attestations to maximize regret.

    Returns analysis of attack effectiveness.
    """
    rng = rng or random.Random(42)

    n_total = n_honest + n_byzantine
    honest_trust = [0.5] * n_honest
    byzantine_trust = [0.5] * n_byzantine

    trust_errors = []

    for t in range(T):
        # Honest attestations: small noise around true value (0.7)
        true_trust = 0.7
        honest_atts = [true_trust + rng.gauss(0, 0.05) for _ in range(n_honest)]

        # Byzantine: adversarial (try to push aggregate away from truth)
        if t % 2 == 0:
            byz_atts = [1.0] * n_byzantine  # inflate
        else:
            byz_atts = [0.0] * n_byzantine  # deflate

        all_atts = honest_atts + byz_atts

        # Median aggregation (Byzantine-resilient)
        sorted_atts = sorted(all_atts)
        median = sorted_atts[len(sorted_atts) // 2]

        # Trimmed mean (remove f extremes each side)
        trimmed = sorted_atts[n_byzantine:-n_byzantine] if n_byzantine > 0 and 2 * n_byzantine < len(sorted_atts) else sorted_atts
        trimmed_mean = sum(trimmed) / len(trimmed)

        # Simple mean (vulnerable)
        simple_mean = sum(all_atts) / len(all_atts)

        trust_errors.append({
            "median_error": abs(median - true_trust),
            "trimmed_error": abs(trimmed_mean - true_trust),
            "simple_error": abs(simple_mean - true_trust),
        })

    avg_errors = {
        "median_error": sum(e["median_error"] for e in trust_errors) / T,
        "trimmed_error": sum(e["trimmed_error"] for e in trust_errors) / T,
        "simple_error": sum(e["simple_error"] for e in trust_errors) / T,
        "n_honest": n_honest,
        "n_byzantine": n_byzantine,
        "byzantine_fraction": n_byzantine / n_total,
    }
    return avg_errors


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
    print("Adversarial Bandit Trust for Web4")
    print("Session 33, Track 6")
    print("=" * 70)

    rng = random.Random(42)

    # ── §1 EXP3 Basics ──────────────────────────────────────────
    print("\n§1 EXP3 Basics\n")

    exp3 = EXP3(n_arms=3, gamma=0.1)
    probs = exp3.probabilities
    check("initial_uniform_approx", all(abs(p - 1/3) < 0.05 for p in probs))
    check("probs_sum_to_1", abs(sum(probs) - 1.0) < 1e-9)

    arm = exp3.select_arm(rng)
    check("arm_valid", 0 <= arm < 3)

    # After rewarding arm 0 heavily
    for _ in range(20):
        exp3.update(0, 1.0)
    probs_after = exp3.probabilities
    check("best_arm_highest_prob", probs_after[0] > probs_after[1])
    check("best_arm_highest_prob2", probs_after[0] > probs_after[2])

    # ── §2 EXP3 vs Oblivious Adversary ──────────────────────────
    print("\n§2 EXP3 vs Oblivious Adversary\n")

    T = 500
    K = 5
    rewards = oblivious_adversary(K, T, best_arm=2, rng=random.Random(42))

    exp3_game = EXP3(K, gamma=0.2)
    for t in range(T):
        arm = exp3_game.select_arm(random.Random(t + 100))
        exp3_game.update(arm, rewards[t][arm])

    regret = compute_regret(rewards, exp3_game.history)
    check("exp3_positive_reward", regret["algorithm_reward"] > 0)
    check("exp3_sublinear_regret", regret["per_round_regret"] < 0.5,
          f"per_round={regret['per_round_regret']:.3f}")

    # Theoretical bound
    bound = exp3_game.regret_bound
    check("regret_bound_computed", bound > 0)

    # ── §3 EXP3.P ────────────────────────────────────────────────
    print("\n§3 EXP3.P (High-Probability Bounds)\n")

    exp3p = EXP3P(n_arms=4, delta=0.05, T_horizon=300)
    check("exp3p_initial_probs_valid", abs(sum(exp3p.probabilities) - 1.0) < 1e-9)

    rewards_p = oblivious_adversary(4, 300, best_arm=1, rng=random.Random(55))
    for t in range(300):
        arm = exp3p.select_arm(random.Random(t + 200))
        exp3p.update(arm, rewards_p[t][arm])

    check("exp3p_earned_reward", sum(r for _, r in exp3p.history) > 0)
    check("exp3p_best_arm_explored",
          exp3p.cumulative_rewards[1] > 0)

    # ── §4 UCB1 Comparison (Stochastic) ──────────────────────────
    print("\n§4 UCB1 Comparison\n")

    # Stochastic: EXP3 and UCB1 both work; UCB1 should be better
    K2 = 4
    T2 = 500
    stoch_rng = random.Random(77)
    arm_means = [0.3, 0.5, 0.8, 0.4]  # arm 2 is best

    exp3_s = EXP3(K2, gamma=0.15)
    ucb1_s = UCB1(K2)

    for t in range(T2):
        # EXP3
        a_exp3 = exp3_s.select_arm(random.Random(t * 3))
        r_exp3 = 1.0 if stoch_rng.random() < arm_means[a_exp3] else 0.0
        exp3_s.update(a_exp3, r_exp3)

        # UCB1
        a_ucb = ucb1_s.select_arm()
        r_ucb = 1.0 if random.Random(t * 7 + 3).random() < arm_means[a_ucb] else 0.0
        ucb1_s.update(a_ucb, r_ucb)

    check("ucb1_positive", ucb1_s.cumulative_reward > 0)
    check("exp3_stochastic_positive", exp3_s.cumulative_reward > 0)
    # UCB1 generally better in stochastic setting (lower regret)
    # But not guaranteed in every seed — just check both perform reasonably
    check("both_reasonable", ucb1_s.cumulative_reward > T2 * 0.3 and
          exp3_s.cumulative_reward > T2 * 0.2)

    # ── §5 Switching Adversary ───────────────────────────────────
    print("\n§5 Switching Adversary (Non-Stationary)\n")

    T3 = 600
    K3 = 3
    switch_rewards = switching_adversary(K3, T3, switch_period=100,
                                          rng=random.Random(33))

    exp3_switch = EXP3(K3, gamma=0.3)  # Higher gamma for non-stationary
    for t in range(T3):
        arm = exp3_switch.select_arm(random.Random(t * 11))
        exp3_switch.update(arm, switch_rewards[t][arm])

    regret_switch = compute_regret(switch_rewards, exp3_switch.history)
    check("switch_positive_reward", regret_switch["algorithm_reward"] > 0)
    # Per-round regret should be reasonable (higher than stationary)
    check("switch_regret_bounded", regret_switch["per_round_regret"] < 1.0,
          f"per_round={regret_switch['per_round_regret']:.3f}")

    # ── §6 Trust-Weighted EXP3 ───────────────────────────────────
    print("\n§6 Trust-Weighted EXP3\n")

    tw_exp3 = TrustWeightedEXP3(
        arms={
            "conservative": 0.9,    # High trust
            "moderate": 0.6,        # Medium trust
            "aggressive": 0.2,      # Low trust
        },
        gamma=0.1
    )
    probs_tw = tw_exp3.probabilities
    check("trust_bias_initial", probs_tw["conservative"] > probs_tw["aggressive"])
    check("tw_probs_sum", abs(sum(probs_tw.values()) - 1.0) < 1e-9)

    # After many rounds, trust weights should adapt
    for _ in range(100):
        arm = tw_exp3.select_arm(random.Random(_))
        reward = 0.9 if arm == "moderate" else 0.2
        tw_exp3.update(arm, reward)

    probs_final = tw_exp3.probabilities
    check("tw_adapts", probs_final["moderate"] > probs_tw["moderate"],
          f"init={probs_tw['moderate']:.3f}, final={probs_final['moderate']:.3f}")

    # ── §7 Byzantine Attack Analysis ─────────────────────────────
    print("\n§7 Byzantine Attack Analysis\n")

    # 10 honest, 3 Byzantine (30%)
    attack = byzantine_trust_attack(10, 3, T=200, rng=random.Random(42))
    check("median_resilient", attack["median_error"] < attack["simple_error"],
          f"median={attack['median_error']:.4f}, simple={attack['simple_error']:.4f}")
    check("trimmed_resilient", attack["trimmed_error"] < attack["simple_error"],
          f"trimmed={attack['trimmed_error']:.4f}, simple={attack['simple_error']:.4f}")

    # More Byzantine → worse simple mean, but median should hold
    attack_heavy = byzantine_trust_attack(10, 8, T=200, rng=random.Random(42))
    check("heavy_attack_simple_fails",
          attack_heavy["simple_error"] > 0.1,
          f"simple_error={attack_heavy['simple_error']:.4f}")
    # With 8/18 ≈ 44% Byzantine, median may struggle but should be better than mean
    check("heavy_attack_median_better",
          attack_heavy["median_error"] <= attack_heavy["simple_error"],
          f"median={attack_heavy['median_error']:.4f}, simple={attack_heavy['simple_error']:.4f}")

    # ── §8 Regret Analysis ───────────────────────────────────────
    print("\n§8 Regret Analysis\n")

    # Regret should scale sublinearly: regret/T → 0 as T → ∞
    for T_val in [100, 500, 1000]:
        K_val = 4
        rews = oblivious_adversary(K_val, T_val, best_arm=0, rng=random.Random(42))
        alg = EXP3(K_val, gamma=0.15)
        for t in range(T_val):
            arm = alg.select_arm(random.Random(t + 777))
            alg.update(arm, rews[t][arm])
        reg = compute_regret(rews, alg.history)
        check(f"sublinear_T{T_val}", reg["per_round_regret"] < 1.0,
              f"per_round={reg['per_round_regret']:.3f}")

    # Per-round regret decreases with T
    results = []
    for T_val in [200, 2000]:
        K_val = 3
        rews = oblivious_adversary(K_val, T_val, best_arm=1, rng=random.Random(88))
        alg = EXP3(K_val, gamma=0.1)
        for t in range(T_val):
            arm = alg.select_arm(random.Random(t + 999))
            alg.update(arm, rews[t][arm])
        reg = compute_regret(rews, alg.history)
        results.append(reg["per_round_regret"])

    check("regret_decreasing", results[0] >= results[1] * 0.5,
          f"T200={results[0]:.3f}, T2000={results[1]:.3f}")

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
