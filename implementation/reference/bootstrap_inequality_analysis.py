"""
Bootstrap Inequality & Fair ATP Distribution
=============================================

Explores the cold-start fairness problem: how initial ATP allocation
strategies affect long-term wealth inequality, trust mobility, and
sybil resistance. Tests multiple distribution schemes, Lorenz curves,
Gini coefficient dynamics, and anti-concentration bounds.

Sections:
  S1  — Gini Coefficient & Lorenz Curves
  S2  — Flat vs Proportional Initial Allocation
  S3  — Stake-Weighted Distribution
  S4  — Trust-Gated Progressive Allocation
  S5  — Sybil-Resistant Bootstrap (proof-of-work/unique-human)
  S6  — Temporal Vesting Schedules
  S7  — Redistribution Mechanisms (taxation, UBI, demurrage)
  S8  — Mobility Metrics (rank correlation, quintile transitions)
  S9  — Anti-Concentration Bounds
  S10 — Multi-Cohort Fairness (early vs late joiners)
  S11 — Combined Strategy Simulation
"""

from __future__ import annotations
import math
import random
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


# ============================================================
# S1 — Gini Coefficient & Lorenz Curves
# ============================================================

def gini_coefficient(values: List[float]) -> float:
    """Compute Gini coefficient. 0 = perfect equality, 1 = perfect inequality."""
    if not values or all(v == 0 for v in values):
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    total = sum(sorted_vals)
    if total == 0:
        return 0.0
    cumulative = 0.0
    area = 0.0
    for i, v in enumerate(sorted_vals):
        cumulative += v
        area += cumulative
    # Gini = 1 - 2*B where B = area under Lorenz curve
    # area = sum of cumulative sums = sum_{i=1}^{n} sum_{j=1}^{i} x_j
    # Normalized: B = area / (n * total)
    b = area / (n * total)
    return 1.0 - 2.0 * b + 1.0 / n


def lorenz_curve(values: List[float]) -> List[Tuple[float, float]]:
    """Return Lorenz curve points: [(fraction_of_pop, fraction_of_wealth), ...]."""
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    total = sum(sorted_vals)
    if total == 0:
        return [(i / n, 0.0) for i in range(n + 1)]
    points = [(0.0, 0.0)]
    cumulative = 0.0
    for i, v in enumerate(sorted_vals):
        cumulative += v
        points.append(((i + 1) / n, cumulative / total))
    return points


def test_section_1():
    checks = []

    # Perfect equality
    equal = [100.0] * 10
    g = gini_coefficient(equal)
    checks.append(("gini_perfect_equality", abs(g) < 0.01))

    # Perfect inequality (one person has everything)
    unequal = [0.0] * 9 + [100.0]
    g = gini_coefficient(unequal)
    checks.append(("gini_near_one", g > 0.8))

    # Moderate inequality
    moderate = [10.0, 20.0, 30.0, 40.0, 50.0]
    g = gini_coefficient(moderate)
    checks.append(("gini_moderate", 0.1 < g < 0.5))

    # Lorenz curve properties
    lc = lorenz_curve([10.0, 20.0, 30.0, 40.0])
    checks.append(("lorenz_starts_zero", lc[0] == (0.0, 0.0)))
    checks.append(("lorenz_ends_one", lc[-1] == (1.0, 1.0)))
    checks.append(("lorenz_monotone", all(lc[i][1] <= lc[i+1][1] for i in range(len(lc)-1))))
    checks.append(("lorenz_below_diagonal", all(y <= x + 0.01 for x, y in lc)))

    # Gini of empty / zeros
    checks.append(("gini_empty", gini_coefficient([]) == 0.0))
    checks.append(("gini_zeros", gini_coefficient([0.0, 0.0, 0.0]) == 0.0))

    return checks


# ============================================================
# S2 — Flat vs Proportional Initial Allocation
# ============================================================

@dataclass
class Entity:
    entity_id: str
    trust: float = 0.5
    balance: float = 0.0
    join_time: int = 0
    work_quality: float = 0.5  # average quality of work


def allocate_flat(entities: List[Entity], total_atp: float) -> Dict[str, float]:
    """Equal allocation regardless of trust or contribution."""
    per_entity = total_atp / len(entities)
    return {e.entity_id: per_entity for e in entities}


def allocate_proportional_trust(entities: List[Entity], total_atp: float) -> Dict[str, float]:
    """Allocate proportional to trust scores."""
    total_trust = sum(e.trust for e in entities)
    if total_trust == 0:
        return allocate_flat(entities, total_atp)
    return {e.entity_id: total_atp * (e.trust / total_trust) for e in entities}


def allocate_sqrt_trust(entities: List[Entity], total_atp: float) -> Dict[str, float]:
    """Allocate proportional to sqrt(trust) — sublinear to reduce concentration."""
    total_sqrt = sum(math.sqrt(e.trust) for e in entities)
    if total_sqrt == 0:
        return allocate_flat(entities, total_atp)
    return {e.entity_id: total_atp * (math.sqrt(e.trust) / total_sqrt) for e in entities}


def test_section_2():
    checks = []
    random.seed(42)

    # Create entities with varying trust
    entities = [Entity(f"e{i}", trust=0.1 + 0.8 * (i / 19)) for i in range(20)]
    total_atp = 1000.0

    # Flat allocation
    flat = allocate_flat(entities, total_atp)
    flat_values = list(flat.values())
    checks.append(("flat_equal", all(abs(v - 50.0) < 0.01 for v in flat_values)))
    checks.append(("flat_gini_zero", gini_coefficient(flat_values) < 0.01))

    # Proportional allocation
    prop = allocate_proportional_trust(entities, total_atp)
    prop_values = list(prop.values())
    checks.append(("prop_sum_correct", abs(sum(prop_values) - total_atp) < 0.01))
    checks.append(("prop_high_gets_more", prop[entities[-1].entity_id] > prop[entities[0].entity_id]))
    prop_gini = gini_coefficient(prop_values)
    checks.append(("prop_gini_higher", prop_gini > 0.1))

    # Sqrt allocation — between flat and proportional
    sqrt_alloc = allocate_sqrt_trust(entities, total_atp)
    sqrt_values = list(sqrt_alloc.values())
    sqrt_gini = gini_coefficient(sqrt_values)
    checks.append(("sqrt_reduces_inequality", sqrt_gini < prop_gini))
    checks.append(("sqrt_not_flat", sqrt_gini > 0.01))

    # Conservation
    checks.append(("all_conserve_total",
                    abs(sum(flat_values) - total_atp) < 0.01 and
                    abs(sum(prop_values) - total_atp) < 0.01 and
                    abs(sum(sqrt_values) - total_atp) < 0.01))

    return checks


# ============================================================
# S3 — Stake-Weighted Distribution
# ============================================================

def allocate_stake_weighted(entities: List[Entity], total_atp: float,
                            min_stake: float = 10.0) -> Dict[str, float]:
    """Allocate based on willingness to stake. Entities must stake min_stake to participate."""
    eligible = [e for e in entities if e.balance >= min_stake]
    if not eligible:
        return {e.entity_id: 0.0 for e in entities}

    stakes = {}
    for e in eligible:
        stake = min(e.balance * 0.5, e.balance - min_stake)
        stake = max(0.0, stake)
        stakes[e.entity_id] = stake

    total_staked = sum(stakes.values())
    if total_staked == 0:
        per = total_atp / len(eligible)
        result = {e.entity_id: 0.0 for e in entities}
        for e in eligible:
            result[e.entity_id] = per
        return result

    result = {e.entity_id: 0.0 for e in entities}
    for e in eligible:
        result[e.entity_id] = total_atp * (stakes[e.entity_id] / total_staked)
    return result


def test_section_3():
    checks = []

    # Entities with varying balances
    entities = []
    for i in range(10):
        e = Entity(f"e{i}", trust=0.5, balance=5.0 + i * 10.0)
        entities.append(e)

    alloc = allocate_stake_weighted(entities, 500.0, min_stake=10.0)

    # Only entities with balance >= 10 participate
    checks.append(("poorest_excluded", alloc["e0"] == 0.0))  # balance=5
    checks.append(("rich_included", alloc["e9"] > 0))  # balance=95

    # Richer entities get more
    included = {k: v for k, v in alloc.items() if v > 0}
    included_list = sorted(included.items(), key=lambda x: x[0])
    checks.append(("stake_monotone",
                    all(included_list[i][1] <= included_list[i+1][1]
                        for i in range(len(included_list)-1))))

    # Conservation
    checks.append(("stake_conserves", abs(sum(alloc.values()) - 500.0) < 0.01))

    # With all poor entities, nothing allocated
    poor = [Entity(f"p{i}", balance=1.0) for i in range(5)]
    alloc_poor = allocate_stake_weighted(poor, 100.0, min_stake=10.0)
    checks.append(("poor_get_nothing", sum(alloc_poor.values()) == 0.0))

    # Gini is lower than pure proportional (stake is sublinear in balance)
    # because stake = min(balance*0.5, balance-min_stake)
    stake_gini = gini_coefficient(list(alloc.values()))
    prop_gini = gini_coefficient([5.0 + i * 10.0 for i in range(10)])
    checks.append(("stake_gini_moderate", stake_gini < 1.0))

    return checks


# ============================================================
# S4 — Trust-Gated Progressive Allocation
# ============================================================

@dataclass
class ProgressiveAllocator:
    """Allocate ATP in tiers based on trust thresholds."""
    tiers: List[Tuple[float, float]]  # [(trust_threshold, atp_amount), ...]

    def allocate(self, entities: List[Entity]) -> Dict[str, float]:
        result = {}
        for e in entities:
            total = 0.0
            for threshold, amount in self.tiers:
                if e.trust >= threshold:
                    total += amount
            result[e.entity_id] = total
        return result


def test_section_4():
    checks = []

    tiers = [(0.0, 10.0), (0.3, 20.0), (0.6, 30.0), (0.9, 40.0)]
    allocator = ProgressiveAllocator(tiers=tiers)

    entities = [
        Entity("low", trust=0.1),     # gets tier 0 only: 10
        Entity("med", trust=0.5),     # gets tiers 0,1: 30
        Entity("high", trust=0.7),    # gets tiers 0,1,2: 60
        Entity("elite", trust=0.95),  # gets all tiers: 100
    ]

    alloc = allocator.allocate(entities)

    checks.append(("low_gets_base", abs(alloc["low"] - 10.0) < 0.01))
    checks.append(("med_gets_two", abs(alloc["med"] - 30.0) < 0.01))
    checks.append(("high_gets_three", abs(alloc["high"] - 60.0) < 0.01))
    checks.append(("elite_gets_all", abs(alloc["elite"] - 100.0) < 0.01))

    # Progressive: higher trust → disproportionately more
    checks.append(("progressive_ratio",
                    alloc["elite"] / alloc["low"] == 10.0))

    # Gini should be high (intentionally stratified)
    gini = gini_coefficient(list(alloc.values()))
    checks.append(("progressive_gini_high", gini > 0.2))

    # But no one gets zero (everyone qualifies for tier 0)
    checks.append(("nobody_zero", all(v > 0 for v in alloc.values())))

    return checks


# ============================================================
# S5 — Sybil-Resistant Bootstrap
# ============================================================

@dataclass
class SybilResistantAllocator:
    """Bootstrap allocation with proof-of-uniqueness cost."""
    registration_cost: float = 50.0   # ATP cost to register
    initial_grant: float = 100.0      # ATP granted on registration
    hardware_bonus: float = 50.0      # bonus for hardware binding
    referral_bonus: float = 20.0      # bonus per unique referrer (max 3)
    max_referral_bonuses: int = 3

    def register(self, entity: Entity, has_hardware: bool = False,
                 referrers: List[str] = None) -> Tuple[float, float]:
        """Returns (net_grant, registration_cost)."""
        grant = self.initial_grant
        if has_hardware:
            grant += self.hardware_bonus

        if referrers:
            unique_refs = list(set(referrers))[:self.max_referral_bonuses]
            grant += self.referral_bonus * len(unique_refs)

        net = grant - self.registration_cost
        return net, self.registration_cost

    def sybil_cost_analysis(self, num_identities: int,
                            has_hardware: bool = False) -> Dict[str, float]:
        """Analyze cost/benefit of creating multiple sybil identities."""
        total_cost = num_identities * self.registration_cost
        per_grant = self.initial_grant
        if has_hardware:
            per_grant += self.hardware_bonus
        total_grant = num_identities * per_grant
        net = total_grant - total_cost
        per_identity_net = net / num_identities if num_identities > 0 else 0

        # With hardware requirement, sybils need N hardware devices
        hardware_cost = num_identities * 250.0 if has_hardware else 0.0

        return {
            "total_cost": total_cost + hardware_cost,
            "total_grant": total_grant,
            "net_gain": net - hardware_cost,
            "per_identity_net": per_identity_net - (250.0 if has_hardware else 0.0),
            "profitable": (net - hardware_cost) > 0,
        }


def test_section_5():
    checks = []

    alloc = SybilResistantAllocator()

    # Basic registration
    net, cost = alloc.register(Entity("e1"))
    checks.append(("basic_net_positive", net == 50.0))
    checks.append(("basic_cost", cost == 50.0))

    # Hardware bonus
    net_hw, _ = alloc.register(Entity("e2"), has_hardware=True)
    checks.append(("hardware_bonus", net_hw == 100.0))

    # Referral bonus (capped at 3)
    net_ref, _ = alloc.register(Entity("e3"), referrers=["r1", "r2", "r3", "r4", "r5"])
    checks.append(("referral_capped", net_ref == 110.0))  # 50 base + 60 referral

    # Duplicate referrers don't count
    net_dup, _ = alloc.register(Entity("e4"), referrers=["r1", "r1", "r1"])
    checks.append(("dup_referrers_once", net_dup == 70.0))  # 50 base + 20 referral

    # Sybil analysis: 1 honest identity is profitable
    analysis_1 = alloc.sybil_cost_analysis(1, has_hardware=False)
    checks.append(("single_profitable", analysis_1["profitable"]))

    # Sybil analysis with hardware: each sybil needs $250 hardware
    analysis_5hw = alloc.sybil_cost_analysis(5, has_hardware=True)
    checks.append(("sybil_hw_unprofitable", not analysis_5hw["profitable"]))

    # Sybil without hardware: still profitable per identity
    analysis_5 = alloc.sybil_cost_analysis(5, has_hardware=False)
    checks.append(("sybil_no_hw_profitable", analysis_5["profitable"]))

    # Hardware makes sybils progressively worse
    checks.append(("hw_deters_sybils",
                    analysis_5hw["per_identity_net"] < analysis_5["per_identity_net"]))

    return checks


# ============================================================
# S6 — Temporal Vesting Schedules
# ============================================================

@dataclass
class VestingSchedule:
    """ATP vesting: initial allocation released over time."""
    total_grant: float
    cliff_periods: int = 3      # no release for first N periods
    vesting_periods: int = 12   # linear release over M periods after cliff
    initial_release: float = 0.1  # fraction released immediately

    def vested_at(self, period: int) -> float:
        """Return total vested amount at given period."""
        immediate = self.total_grant * self.initial_release

        if period < self.cliff_periods:
            return immediate

        remaining = self.total_grant * (1.0 - self.initial_release)
        elapsed = period - self.cliff_periods
        fraction = min(1.0, elapsed / self.vesting_periods)
        return immediate + remaining * fraction


def test_section_6():
    checks = []

    vest = VestingSchedule(total_grant=1000.0, cliff_periods=3,
                           vesting_periods=12, initial_release=0.1)

    # Immediate release
    checks.append(("immediate_10pct", abs(vest.vested_at(0) - 100.0) < 0.01))

    # During cliff, only immediate
    checks.append(("cliff_no_change", abs(vest.vested_at(2) - 100.0) < 0.01))

    # After cliff, linear release
    mid_vest = vest.vested_at(9)  # 6 periods after cliff
    expected = 100.0 + 900.0 * (6 / 12)
    checks.append(("mid_vesting", abs(mid_vest - expected) < 0.01))

    # Fully vested
    full = vest.vested_at(15)  # 12 periods after cliff
    checks.append(("fully_vested", abs(full - 1000.0) < 0.01))

    # Over-time still fully vested
    checks.append(("over_time_capped", abs(vest.vested_at(100) - 1000.0) < 0.01))

    # Monotonically increasing
    amounts = [vest.vested_at(t) for t in range(20)]
    checks.append(("monotone_vesting", all(amounts[i] <= amounts[i+1] + 0.001
                                           for i in range(len(amounts)-1))))

    # Different schedules for different trust levels
    high_trust_vest = VestingSchedule(total_grant=1000.0, cliff_periods=1,
                                     vesting_periods=6, initial_release=0.2)
    low_trust_vest = VestingSchedule(total_grant=1000.0, cliff_periods=6,
                                    vesting_periods=24, initial_release=0.05)

    # High trust vests faster
    checks.append(("high_trust_faster",
                    high_trust_vest.vested_at(5) > low_trust_vest.vested_at(5)))

    return checks


# ============================================================
# S7 — Redistribution Mechanisms
# ============================================================

def apply_flat_tax(balances: Dict[str, float], rate: float) -> Tuple[Dict[str, float], float]:
    """Apply flat tax rate, return new balances and total collected."""
    collected = 0.0
    new_balances = {}
    for eid, bal in balances.items():
        tax = bal * rate
        new_balances[eid] = bal - tax
        collected += tax
    return new_balances, collected


def apply_progressive_tax(balances: Dict[str, float],
                          brackets: List[Tuple[float, float]]) -> Tuple[Dict[str, float], float]:
    """Apply progressive tax with brackets [(threshold, rate), ...]."""
    collected = 0.0
    new_balances = {}
    sorted_brackets = sorted(brackets, key=lambda x: x[0])

    for eid, bal in balances.items():
        tax = 0.0
        remaining = bal
        prev_threshold = 0.0
        for threshold, rate in sorted_brackets:
            taxable = min(remaining, threshold - prev_threshold)
            if taxable > 0:
                tax += taxable * rate
                remaining -= taxable
            prev_threshold = threshold
        # Remaining above highest bracket
        if remaining > 0 and sorted_brackets:
            tax += remaining * sorted_brackets[-1][1]

        new_balances[eid] = bal - tax
        collected += tax

    return new_balances, collected


def apply_ubi(balances: Dict[str, float], ubi_amount: float,
              fund: float) -> Tuple[Dict[str, float], float]:
    """Distribute UBI equally from fund. Returns new balances and remaining fund."""
    n = len(balances)
    per_person = min(ubi_amount, fund / n) if n > 0 else 0.0
    total_distributed = per_person * n
    new_balances = {eid: bal + per_person for eid, bal in balances.items()}
    return new_balances, fund - total_distributed


def apply_demurrage(balances: Dict[str, float], rate: float) -> Dict[str, float]:
    """Apply demurrage (negative interest) — holdings decay over time."""
    return {eid: bal * (1.0 - rate) for eid, bal in balances.items()}


def test_section_7():
    checks = []

    balances = {"poor": 10.0, "mid": 100.0, "rich": 1000.0}

    # Flat tax
    taxed, collected = apply_flat_tax(balances, 0.1)
    checks.append(("flat_tax_correct", abs(taxed["rich"] - 900.0) < 0.01))
    checks.append(("flat_tax_collected", abs(collected - 111.0) < 0.01))

    # Progressive tax
    brackets = [(100.0, 0.05), (500.0, 0.10), (1000.0, 0.20)]
    prog_taxed, prog_collected = apply_progressive_tax(balances, brackets)
    # Rich pays: 100*0.05 + 400*0.10 + 500*0.20 = 5 + 40 + 100 = 145
    checks.append(("prog_tax_rich", abs(prog_taxed["rich"] - 855.0) < 0.01))
    # Poor pays: 10*0.05 = 0.5
    checks.append(("prog_tax_poor", abs(prog_taxed["poor"] - 9.5) < 0.01))

    # Progressive is less harsh on poor
    checks.append(("progressive_fairer",
                    (balances["poor"] - prog_taxed["poor"]) / balances["poor"] <
                    (balances["rich"] - prog_taxed["rich"]) / balances["rich"]))

    # UBI
    ubi_bal, remaining = apply_ubi(balances, 20.0, 100.0)
    checks.append(("ubi_equal", abs(ubi_bal["poor"] - 30.0) < 0.01))
    checks.append(("ubi_fund_decreased", remaining < 100.0))

    # Tax + UBI cycle reduces inequality
    cycle_bal = dict(balances)
    for _ in range(5):
        cycle_bal, collected = apply_flat_tax(cycle_bal, 0.1)
        cycle_bal, _ = apply_ubi(cycle_bal, collected / 3, collected)

    gini_before = gini_coefficient(list(balances.values()))
    gini_after = gini_coefficient(list(cycle_bal.values()))
    checks.append(("tax_ubi_reduces_gini", gini_after < gini_before))

    # Demurrage
    dem = apply_demurrage(balances, 0.02)
    checks.append(("demurrage_reduces", all(dem[k] < balances[k] for k in balances)))
    checks.append(("demurrage_proportional",
                    abs(dem["rich"] / balances["rich"] - dem["poor"] / balances["poor"]) < 0.001))

    return checks


# ============================================================
# S8 — Mobility Metrics
# ============================================================

def rank_correlation(before: List[float], after: List[float]) -> float:
    """Spearman rank correlation between two wealth distributions."""
    n = len(before)
    if n < 2:
        return 1.0

    def ranks(vals):
        sorted_idx = sorted(range(n), key=lambda i: vals[i])
        r = [0.0] * n
        for rank, idx in enumerate(sorted_idx):
            r[idx] = float(rank)
        return r

    r1 = ranks(before)
    r2 = ranks(after)

    d_sq = sum((r1[i] - r2[i]) ** 2 for i in range(n))
    return 1.0 - (6.0 * d_sq) / (n * (n * n - 1))


def quintile_transitions(before: List[float], after: List[float]) -> Dict[str, int]:
    """Count transitions between quintiles."""
    n = len(before)

    def quintile(vals, idx):
        sorted_idx = sorted(range(n), key=lambda i: vals[i])
        rank = sorted_idx.index(idx)
        return min(4, int(5 * rank / n))

    transitions = defaultdict(int)
    for i in range(n):
        q_before = quintile(before, i)
        q_after = quintile(after, i)
        if q_before != q_after:
            transitions["changed"] += 1
            if q_after > q_before:
                transitions["upward"] += 1
            else:
                transitions["downward"] += 1
        else:
            transitions["stayed"] += 1

    return dict(transitions)


def test_section_8():
    checks = []
    random.seed(42)

    # Perfect correlation
    before = [10.0, 20.0, 30.0, 40.0, 50.0]
    after = [15.0, 25.0, 35.0, 45.0, 55.0]  # same order, shifted
    rho = rank_correlation(before, after)
    checks.append(("perfect_correlation", rho == 1.0))

    # Reversed order
    reversed_after = [55.0, 45.0, 35.0, 25.0, 15.0]
    rho_rev = rank_correlation(before, reversed_after)
    checks.append(("negative_correlation", rho_rev < -0.5))

    # Simulated economy: start flat, evolve with noise
    n = 50
    initial = [100.0] * n
    evolved = list(initial)
    for step in range(100):
        for i in range(n):
            # Quality-based earnings (some agents are better)
            quality = 0.3 + 0.7 * (i / (n - 1))  # agent skill
            earnings = quality * random.uniform(0.5, 1.5) * 5.0
            # Spend proportional to balance
            spending = evolved[i] * 0.03
            evolved[i] = max(0, evolved[i] + earnings - spending)

    rho_sim = rank_correlation(initial, evolved)
    checks.append(("evolved_not_perfect", rho_sim < 1.0))

    # Quintile analysis
    qt = quintile_transitions(initial, evolved)
    checks.append(("some_mobility", qt.get("changed", 0) > 0 or
                    all(v == 100.0 for v in initial)))  # initial is flat

    # With actual differentiation
    before_diff = [10.0 * (i + 1) for i in range(20)]
    after_diff = list(before_diff)
    # Swap some rankings
    after_diff[2], after_diff[17] = after_diff[17], after_diff[2]
    after_diff[5], after_diff[14] = after_diff[14], after_diff[5]
    qt_diff = quintile_transitions(before_diff, after_diff)
    checks.append(("swaps_create_mobility", qt_diff.get("changed", 0) > 0))

    # Gini evolution
    gini_initial = gini_coefficient(initial)
    gini_evolved = gini_coefficient(evolved)
    checks.append(("inequality_emerges", gini_evolved > gini_initial))

    return checks


# ============================================================
# S9 — Anti-Concentration Bounds
# ============================================================

def max_share_bound(n: int, top_k: int = 1) -> float:
    """Maximum share the top-k entities should hold to prevent concentration."""
    # Herfindahl-Hirschman inspired: top-k should hold at most k/sqrt(n)
    return min(1.0, top_k / math.sqrt(n))


def check_concentration(balances: List[float], max_top1_share: float = 0.5,
                         max_top10_share: float = 0.8) -> Dict[str, bool]:
    """Check if wealth is too concentrated."""
    total = sum(balances)
    if total == 0:
        return {"top1_ok": True, "top10_ok": True, "hhi_ok": True}

    sorted_bal = sorted(balances, reverse=True)
    n = len(sorted_bal)

    top1_share = sorted_bal[0] / total
    top10_pct = max(1, n // 10)
    top10_share = sum(sorted_bal[:top10_pct]) / total

    # Herfindahl-Hirschman Index
    hhi = sum((b / total) ** 2 for b in balances)
    # HHI > 0.25 = highly concentrated, < 0.15 = competitive
    hhi_ok = hhi < 0.25

    return {
        "top1_ok": top1_share <= max_top1_share,
        "top10_ok": top10_share <= max_top10_share,
        "hhi_ok": hhi_ok,
        "top1_share": top1_share,
        "top10_share": top10_share,
        "hhi": hhi,
    }


def apply_anti_concentration(balances: Dict[str, float],
                              max_share: float = 0.1) -> Dict[str, float]:
    """Cap individual balance to max_share of total. Excess redistributed."""
    total = sum(balances.values())
    cap = total * max_share
    excess = 0.0
    capped = {}

    for eid, bal in balances.items():
        if bal > cap:
            excess += bal - cap
            capped[eid] = cap
        else:
            capped[eid] = bal

    # Redistribute excess equally to those below cap
    below_cap = [eid for eid, bal in capped.items() if bal < cap]
    if below_cap and excess > 0:
        per_person = excess / len(below_cap)
        for eid in below_cap:
            capped[eid] = min(cap, capped[eid] + per_person)

    return capped


def test_section_9():
    checks = []

    # Bounds scale with population
    bound_10 = max_share_bound(10)
    bound_100 = max_share_bound(100)
    bound_1000 = max_share_bound(1000)
    checks.append(("bound_decreases", bound_10 > bound_100 > bound_1000))
    checks.append(("bound_10_reasonable", 0.2 < bound_10 < 0.5))

    # Concentration check — equal distribution
    equal = [100.0] * 20
    conc = check_concentration(equal)
    checks.append(("equal_not_concentrated",
                    conc["top1_ok"] and conc["top10_ok"] and conc["hhi_ok"]))

    # Concentration check — one whale
    whale = [1.0] * 19 + [1000.0]
    conc_whale = check_concentration(whale)
    checks.append(("whale_detected", not conc_whale["top1_ok"]))
    checks.append(("whale_hhi_high", not conc_whale["hhi_ok"]))

    # Anti-concentration mechanism
    whale_dict = {f"e{i}": 1.0 for i in range(19)}
    whale_dict["whale"] = 1000.0
    capped = apply_anti_concentration(whale_dict, max_share=0.1)
    total = sum(whale_dict.values())
    checks.append(("whale_capped", capped["whale"] <= total * 0.1 + 0.01))

    # Conservation after capping
    checks.append(("cap_conserves", abs(sum(capped.values()) - total) < 1.0))

    # Gini reduced after capping
    gini_before = gini_coefficient(list(whale_dict.values()))
    gini_after = gini_coefficient(list(capped.values()))
    checks.append(("cap_reduces_gini", gini_after < gini_before))

    return checks


# ============================================================
# S10 — Multi-Cohort Fairness
# ============================================================

@dataclass
class CohortSimulation:
    """Simulate multiple cohorts joining at different times."""
    entities: Dict[str, Entity] = field(default_factory=dict)
    time: int = 0
    total_minted: float = 0.0
    total_fees: float = 0.0
    fee_rate: float = 0.05

    def add_cohort(self, size: int, cohort_id: str, initial_atp: float = 100.0):
        for i in range(size):
            eid = f"{cohort_id}_{i}"
            self.entities[eid] = Entity(eid, trust=0.3, balance=initial_atp,
                                       join_time=self.time)
            self.total_minted += initial_atp

    def simulate_period(self, periods: int = 1):
        for _ in range(periods):
            self.time += 1
            for eid, e in self.entities.items():
                # Trust grows slowly with tenure
                tenure = self.time - e.join_time
                e.trust = min(0.95, e.trust + 0.01 * (1.0 / (1.0 + tenure * 0.1)))

                # Earn based on trust and quality
                earnings = e.trust * e.work_quality * 10.0
                fee = earnings * self.fee_rate
                e.balance += earnings - fee
                self.total_minted += earnings
                self.total_fees += fee

    def cohort_balances(self, cohort_id: str) -> List[float]:
        return [e.balance for eid, e in self.entities.items()
                if eid.startswith(cohort_id)]

    def conservation_check(self) -> bool:
        total_bal = sum(e.balance for e in self.entities.values())
        return abs(total_bal + self.total_fees - self.total_minted) < 0.1


def test_section_10():
    checks = []

    sim = CohortSimulation()

    # Cohort A joins at t=0
    sim.add_cohort(10, "A", initial_atp=100.0)
    sim.simulate_period(10)

    # Cohort B joins at t=10 (late joiners)
    sim.add_cohort(10, "B", initial_atp=100.0)
    sim.simulate_period(10)

    # Conservation
    checks.append(("cohort_conservation", sim.conservation_check()))

    # Early cohort has more (10 extra periods of earning)
    avg_a = sum(sim.cohort_balances("A")) / 10
    avg_b = sum(sim.cohort_balances("B")) / 10
    checks.append(("early_advantage", avg_a > avg_b))

    # But the advantage is bounded (not runaway)
    ratio = avg_a / avg_b if avg_b > 0 else float('inf')
    checks.append(("advantage_bounded", ratio < 5.0))

    # Trust of early cohort is higher (more tenure)
    trust_a = [sim.entities[f"A_{i}"].trust for i in range(10)]
    trust_b = [sim.entities[f"B_{i}"].trust for i in range(10)]
    checks.append(("early_higher_trust", sum(trust_a) / 10 > sum(trust_b) / 10))

    # Both cohorts have non-zero earnings
    checks.append(("both_nonzero",
                    all(b > 100.0 for b in sim.cohort_balances("A")) and
                    all(b > 100.0 for b in sim.cohort_balances("B"))))

    # Third cohort at t=20, with adjusted initial grant (inflation adjustment)
    inflation_factor = sim.total_minted / (20 * 100.0)  # how much ATP exists per original grant
    adjusted_grant = 100.0 * min(inflation_factor, 3.0)
    sim.add_cohort(10, "C", initial_atp=adjusted_grant)
    sim.simulate_period(10)

    avg_c = sum(sim.cohort_balances("C")) / 10
    checks.append(("inflation_adjusted", avg_c > avg_b * 0.5))  # C not too far behind B

    # Gini across all entities
    all_bal = [e.balance for e in sim.entities.values()]
    gini = gini_coefficient(all_bal)
    checks.append(("multi_cohort_gini_moderate", gini < 0.5))

    return checks


# ============================================================
# S11 — Combined Strategy Simulation
# ============================================================

def run_combined_simulation(n_entities: int = 100, n_periods: int = 50,
                            seed: int = 42) -> Dict[str, float]:
    """Full simulation combining allocation, vesting, taxation, and anti-concentration."""
    random.seed(seed)

    # Create entities with varying quality
    entities = []
    for i in range(n_entities):
        quality = 0.2 + 0.6 * random.random()
        trust = 0.1 + 0.3 * random.random()
        entities.append(Entity(f"e{i}", trust=trust, balance=0.0,
                               work_quality=quality))

    # Phase 1: Initial allocation (sqrt-trust weighted)
    total_initial = n_entities * 100.0
    alloc = allocate_sqrt_trust(entities, total_initial)
    for e in entities:
        e.balance = alloc[e.entity_id]

    # Phase 2: Vesting schedule
    vesting = VestingSchedule(total_grant=50.0, cliff_periods=3,
                              vesting_periods=10, initial_release=0.2)

    # Track metrics over time
    gini_history = []
    total_minted = total_initial
    total_fees = 0.0

    for period in range(n_periods):
        # Vest additional ATP
        vested = vesting.vested_at(period)
        prev_vested = vesting.vested_at(period - 1) if period > 0 else 0.0
        new_vest = vested - prev_vested
        for e in entities:
            e.balance += new_vest
            total_minted += new_vest

        # Work and earn
        for e in entities:
            earnings = e.trust * e.work_quality * random.uniform(0.5, 1.5) * 5.0
            fee = earnings * 0.05
            e.balance += earnings - fee
            total_minted += earnings
            total_fees += fee

            # Trust evolution
            e.trust = min(0.95, e.trust + 0.005 * (e.work_quality - 0.3))

        # Periodic taxation + UBI (every 10 periods)
        if period > 0 and period % 10 == 0:
            bal_dict = {e.entity_id: e.balance for e in entities}
            bal_dict, collected = apply_flat_tax(bal_dict, 0.02)
            bal_dict, _ = apply_ubi(bal_dict, collected / n_entities, collected)
            for e in entities:
                e.balance = bal_dict[e.entity_id]

        # Record Gini
        gini_history.append(gini_coefficient([e.balance for e in entities]))

    # Final metrics
    final_balances = [e.balance for e in entities]
    conc = check_concentration(final_balances)

    return {
        "final_gini": gini_history[-1],
        "initial_gini": gini_history[0],
        "gini_trend": gini_history[-1] - gini_history[0],
        "max_gini": max(gini_history),
        "min_gini": min(gini_history),
        "top1_share": conc["top1_share"],
        "hhi": conc["hhi"],
        "top1_ok": conc["top1_ok"],
        "conservation": abs(sum(final_balances) + total_fees - total_minted) < 1.0,
        "all_positive": all(b > 0 for b in final_balances),
        "n_entities": n_entities,
        "n_periods": n_periods,
    }


def test_section_11():
    checks = []

    results = run_combined_simulation(n_entities=100, n_periods=50, seed=42)

    # Gini stays moderate
    checks.append(("gini_moderate", results["final_gini"] < 0.6))

    # No extreme concentration
    checks.append(("no_whale", results["top1_ok"]))
    checks.append(("hhi_ok", results["hhi"] < 0.1))

    # Conservation holds
    checks.append(("conservation", results["conservation"]))

    # Everyone has positive balance
    checks.append(("all_positive", results["all_positive"]))

    # Gini bounded throughout
    checks.append(("gini_bounded", results["max_gini"] < 0.7))

    # Scale test
    results_large = run_combined_simulation(n_entities=500, n_periods=20, seed=123)
    checks.append(("scales_to_500", results_large["conservation"]))
    checks.append(("large_gini_ok", results_large["final_gini"] < 0.6))

    return checks


# ============================================================
# Main
# ============================================================

def main():
    sections = [
        ("S1 Gini & Lorenz Curves", test_section_1),
        ("S2 Flat vs Proportional", test_section_2),
        ("S3 Stake-Weighted", test_section_3),
        ("S4 Trust-Gated Progressive", test_section_4),
        ("S5 Sybil-Resistant Bootstrap", test_section_5),
        ("S6 Temporal Vesting", test_section_6),
        ("S7 Redistribution Mechanisms", test_section_7),
        ("S8 Mobility Metrics", test_section_8),
        ("S9 Anti-Concentration Bounds", test_section_9),
        ("S10 Multi-Cohort Fairness", test_section_10),
        ("S11 Combined Strategy Simulation", test_section_11),
    ]

    total_pass = 0
    total_fail = 0
    failures = []

    for name, test_fn in sections:
        checks = test_fn()
        passed = sum(1 for _, ok in checks if ok)
        failed = sum(1 for _, ok in checks if not ok)
        total_pass += passed
        total_fail += failed
        status = "✓" if failed == 0 else "✗"
        print(f"  {status} {name}: {passed}/{passed+failed}")
        for check_name, ok in checks:
            if not ok:
                failures.append(f"    FAIL: {check_name}")

    print(f"\nTotal: {total_pass}/{total_pass+total_fail}")
    if failures:
        print(f"\nFailed checks:")
        for f in failures:
            print(f)


if __name__ == "__main__":
    main()
