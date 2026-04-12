"""
Multi-Federation Bargaining for Web4
Session 32, Track 4

When federations interact, they need to negotiate terms.
Game-theoretic bargaining models for inter-federation cooperation.

- Nash bargaining solution
- Kalai-Smorodinsky solution
- Rubinstein alternating offers
- Coalition formation (Shapley value)
- Federation merger surplus division
- Trust-weighted voting power
- Pareto-optimal cooperation agreements
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from itertools import combinations


# ─── Bargaining Problems ──────────────────────────────────────────

@dataclass
class BargainingProblem:
    """Two-party bargaining over surplus from cooperation."""
    utility_a: float  # A's utility from cooperation
    utility_b: float  # B's utility from cooperation
    disagreement_a: float = 0.0  # A's utility if no deal
    disagreement_b: float = 0.0  # B's utility if no deal

    @property
    def surplus(self) -> float:
        """Total surplus from cooperation."""
        return (self.utility_a + self.utility_b -
                self.disagreement_a - self.disagreement_b)

    @property
    def feasible(self) -> bool:
        """Is cooperation beneficial for both parties?"""
        return (self.utility_a >= self.disagreement_a and
                self.utility_b >= self.disagreement_b and
                self.surplus > 0)


def nash_bargaining(problem: BargainingProblem,
                    power_a: float = 0.5) -> Tuple[float, float]:
    """
    Nash bargaining solution: maximize (ua - da)^α × (ub - db)^(1-α).
    power_a = bargaining power of party A.
    With equal power, splits surplus equally.
    """
    if not problem.feasible:
        return (problem.disagreement_a, problem.disagreement_b)

    surplus = problem.surplus
    share_a = power_a * surplus
    share_b = (1 - power_a) * surplus

    return (problem.disagreement_a + share_a,
            problem.disagreement_b + share_b)


def kalai_smorodinsky(problem: BargainingProblem) -> Tuple[float, float]:
    """
    Kalai-Smorodinsky solution: split surplus proportional to
    maximum possible gains (ideal point).
    Monotonic — increasing feasible set never hurts.
    """
    if not problem.feasible:
        return (problem.disagreement_a, problem.disagreement_b)

    gain_a = problem.utility_a - problem.disagreement_a
    gain_b = problem.utility_b - problem.disagreement_b
    total_gains = gain_a + gain_b

    if total_gains <= 0:
        return (problem.disagreement_a, problem.disagreement_b)

    # Proportion based on maximum possible gains
    prop_a = gain_a / total_gains
    prop_b = gain_b / total_gains

    surplus = problem.surplus
    return (problem.disagreement_a + prop_a * surplus,
            problem.disagreement_b + prop_b * surplus)


def rubinstein_alternating(discount_a: float, discount_b: float,
                           surplus: float = 1.0) -> Tuple[float, float]:
    """
    Rubinstein's alternating offers model.
    More patient party (higher discount factor) gets more.
    """
    if discount_a >= 1 or discount_b >= 1:
        # Infinite patience — equal split
        return (surplus / 2, surplus / 2)

    # SPE outcome: proposer gets (1 - δ_b)/(1 - δ_a * δ_b)
    share_a = (1 - discount_b) / (1 - discount_a * discount_b) * surplus
    share_b = surplus - share_a

    return (share_a, share_b)


# ─── Coalition Formation ─────────────────────────────────────────

def shapley_value(n_players: int,
                  value_function: Dict[frozenset, float]) -> List[float]:
    """
    Shapley value: fair division based on marginal contributions.
    Player i's share = average marginal contribution across all orderings.
    """
    values = [0.0] * n_players

    for i in range(n_players):
        # Consider all coalitions not containing i
        for size in range(n_players):
            coalitions_without_i = [
                s for s in combinations(
                    [j for j in range(n_players) if j != i], size)
            ]

            for coalition in coalitions_without_i:
                s = frozenset(coalition)
                s_with_i = frozenset(coalition + (i,))

                v_with = value_function.get(s_with_i, 0.0)
                v_without = value_function.get(s, 0.0)
                marginal = v_with - v_without

                # Weight by combinatorial factor
                weight = (math.factorial(size) *
                         math.factorial(n_players - size - 1) /
                         math.factorial(n_players))
                values[i] += weight * marginal

    return values


def is_core_allocation(allocation: List[float],
                       value_function: Dict[frozenset, float],
                       n_players: int) -> bool:
    """
    Check if allocation is in the core: no coalition can do better
    by defecting from the grand coalition.
    """
    grand = frozenset(range(n_players))
    grand_value = value_function.get(grand, 0.0)

    # Sum must equal grand coalition value
    if abs(sum(allocation) - grand_value) > 1e-6:
        return False

    # Every sub-coalition gets at least their standalone value
    for size in range(1, n_players):
        for coalition in combinations(range(n_players), size):
            s = frozenset(coalition)
            coalition_value = value_function.get(s, 0.0)
            coalition_allocation = sum(allocation[i] for i in coalition)
            if coalition_allocation < coalition_value - 1e-6:
                return False

    return True


# ─── Trust-Weighted Voting ────────────────────────────────────────

def trust_weighted_vote(votes: Dict[str, bool],
                        trust_scores: Dict[str, float],
                        threshold: float = 0.5) -> Tuple[bool, float]:
    """
    Decision by trust-weighted majority vote.
    Each voter's weight is their trust score.
    """
    yes_weight = sum(trust_scores.get(v, 0.5) for v, vote in votes.items() if vote)
    total_weight = sum(trust_scores.get(v, 0.5) for v in votes)

    if total_weight <= 0:
        return False, 0.0

    fraction = yes_weight / total_weight
    return (fraction >= threshold, fraction)


def banzhaf_power_index(weights: List[float],
                        threshold: float = 0.5) -> List[float]:
    """
    Banzhaf power index: fraction of coalitions where player is pivotal.
    Measures actual voting power (not just weight).
    """
    n = len(weights)
    total_weight = sum(weights)
    target = threshold * total_weight
    power = [0.0] * n
    total_swings = 0

    # Enumerate all coalitions
    for mask in range(1 << n):
        coalition_weight = sum(weights[i] for i in range(n) if mask & (1 << i))

        for i in range(n):
            if mask & (1 << i):
                # i is in coalition — is i pivotal?
                without_i = coalition_weight - weights[i]
                if coalition_weight >= target and without_i < target:
                    power[i] += 1
                    total_swings += 1

    if total_swings > 0:
        power = [p / total_swings for p in power]

    return power


# ─── Federation Merger Analysis ───────────────────────────────────

def merger_surplus(fed_a_size: int, fed_b_size: int,
                   fed_a_trust: float, fed_b_trust: float,
                   synergy: float = 0.1) -> Dict[str, float]:
    """
    Analyze surplus from federation merger.
    Larger federation = more witnesses = higher trust ceiling.
    """
    # Individual values (network effect: n²)
    value_a = fed_a_size ** 2 * fed_a_trust
    value_b = fed_b_size ** 2 * fed_b_trust

    # Merged value (synergy from cross-attestation)
    merged_size = fed_a_size + fed_b_size
    merged_trust = (fed_a_trust * fed_a_size + fed_b_trust * fed_b_size) / merged_size
    value_merged = merged_size ** 2 * merged_trust * (1 + synergy)

    surplus = value_merged - value_a - value_b

    return {
        "value_a": value_a,
        "value_b": value_b,
        "value_merged": value_merged,
        "surplus": surplus,
        "beneficial": surplus > 0,
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
    print("Multi-Federation Bargaining for Web4")
    print("Session 32, Track 4")
    print("=" * 70)

    # ── §1 Nash Bargaining ──────────────────────────────────────
    print("\n§1 Nash Bargaining\n")

    prob = BargainingProblem(utility_a=10.0, utility_b=10.0,
                             disagreement_a=2.0, disagreement_b=3.0)
    check("problem_feasible", prob.feasible)
    check("surplus_positive", prob.surplus == 15.0,
          f"surplus={prob.surplus}")

    # Equal power → equal surplus split
    ua, ub = nash_bargaining(prob, power_a=0.5)
    check("nash_equal_split", abs((ua - 2.0) - (ub - 3.0)) < 0.01,
          f"ua={ua:.2f} ub={ub:.2f}")

    # Individual rationality: both get >= disagreement
    check("nash_ir_a", ua >= prob.disagreement_a)
    check("nash_ir_b", ub >= prob.disagreement_b)

    # More power → more surplus
    ua_strong, _ = nash_bargaining(prob, power_a=0.8)
    ua_weak, _ = nash_bargaining(prob, power_a=0.2)
    check("nash_power_matters", ua_strong > ua_weak,
          f"strong={ua_strong:.2f} weak={ua_weak:.2f}")

    # ── §2 Kalai-Smorodinsky ────────────────────────────────────
    print("\n§2 Kalai-Smorodinsky Solution\n")

    # Asymmetric problem: A has more to gain
    asym = BargainingProblem(utility_a=20.0, utility_b=10.0,
                              disagreement_a=5.0, disagreement_b=5.0)
    ua_ks, ub_ks = kalai_smorodinsky(asym)

    # A should get proportionally more (15:5 gain ratio = 3:1)
    gain_a = ua_ks - asym.disagreement_a
    gain_b = ub_ks - asym.disagreement_b
    check("ks_proportional", abs(gain_a / max(0.01, gain_b) - 3.0) < 0.1,
          f"gain_a={gain_a:.2f} gain_b={gain_b:.2f} ratio={gain_a/max(0.01,gain_b):.2f}")

    # Individual rationality
    check("ks_ir_a", ua_ks >= asym.disagreement_a)
    check("ks_ir_b", ub_ks >= asym.disagreement_b)

    # ── §3 Rubinstein Alternating Offers ────────────────────────
    print("\n§3 Rubinstein Alternating Offers\n")

    # Equal patience → first-mover advantage (proposer gets slightly more)
    sa, sb = rubinstein_alternating(0.9, 0.9)
    check("rubinstein_first_mover", sa > sb,
          f"a={sa:.4f} b={sb:.4f}")
    # But difference shrinks as patience → 1
    sa2, sb2 = rubinstein_alternating(0.99, 0.99)
    check("rubinstein_converges_equal", abs(sa2 - sb2) < abs(sa - sb),
          f"gap@0.99={abs(sa2-sb2):.4f} gap@0.9={abs(sa-sb):.4f}")

    # More patient → more surplus (higher discount = more patient)
    sa_patient, sb_patient = rubinstein_alternating(0.95, 0.5)
    check("rubinstein_patience", sa_patient > sb_patient,
          f"patient_a={sa_patient:.4f} impatient_b={sb_patient:.4f}")

    # ── §4 Shapley Value ────────────────────────────────────────
    print("\n§4 Shapley Value & Coalition Formation\n")

    # 3-player game with super-additive value
    vf = {
        frozenset(): 0.0,
        frozenset([0]): 10.0,
        frozenset([1]): 20.0,
        frozenset([2]): 15.0,
        frozenset([0, 1]): 40.0,
        frozenset([0, 2]): 35.0,
        frozenset([1, 2]): 45.0,
        frozenset([0, 1, 2]): 60.0,
    }

    sv = shapley_value(3, vf)
    # Shapley values should sum to grand coalition value
    check("shapley_efficient", abs(sum(sv) - 60.0) < 0.01,
          f"sum={sum(sv):.2f}")

    # Player 1 (highest standalone) should get most
    check("shapley_player1_highest", sv[1] > sv[0] and sv[1] > sv[2],
          f"sv={[f'{v:.2f}' for v in sv]}")

    # Check if Shapley allocation is in the core
    check("shapley_in_core", is_core_allocation(sv, vf, 3),
          f"sv={[f'{v:.2f}' for v in sv]}")

    # ── §5 Trust-Weighted Voting ────────────────────────────────
    print("\n§5 Trust-Weighted Voting\n")

    votes = {"alice": True, "bob": False, "carol": True}
    trust = {"alice": 0.9, "bob": 0.3, "carol": 0.7}

    result, fraction = trust_weighted_vote(votes, trust)
    check("weighted_vote_yes", result,
          f"fraction={fraction:.4f}")

    # High-trust minority can outvote low-trust majority
    votes2 = {"alice": True, "bob": False, "carol": False, "dave": False}
    trust2 = {"alice": 0.9, "bob": 0.1, "carol": 0.1, "dave": 0.1}
    result2, frac2 = trust_weighted_vote(votes2, trust2)
    check("high_trust_minority_wins", result2,
          f"fraction={frac2:.4f}")

    # ── §6 Banzhaf Power Index ──────────────────────────────────
    print("\n§6 Banzhaf Power Index\n")

    # Equal weights → equal power
    equal_power = banzhaf_power_index([1.0, 1.0, 1.0])
    check("banzhaf_equal", all(abs(p - 1/3) < 0.01 for p in equal_power),
          f"power={[f'{p:.3f}' for p in equal_power]}")

    # Dictator (one player has majority weight alone)
    dict_power = banzhaf_power_index([6.0, 2.0, 2.0])
    check("banzhaf_dictator", dict_power[0] > dict_power[1],
          f"power={[f'{p:.3f}' for p in dict_power]}")

    # ── §7 Merger Surplus ───────────────────────────────────────
    print("\n§7 Federation Merger Analysis\n")

    # Equal federations
    merger = merger_surplus(100, 100, 0.7, 0.7, synergy=0.1)
    check("merger_beneficial", merger["beneficial"],
          f"surplus={merger['surplus']:.2f}")

    # Larger federation has more value (n² network effect)
    merger_asym = merger_surplus(200, 50, 0.7, 0.7)
    check("larger_more_value", merger_asym["value_a"] > merger_asym["value_b"])

    # Low-trust federation drags down merged trust
    merger_trust = merger_surplus(100, 100, 0.9, 0.3)
    check("low_trust_dilutes", merger_trust["value_merged"] <
          merger_surplus(100, 100, 0.9, 0.9)["value_merged"])

    # ── Summary ─────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
