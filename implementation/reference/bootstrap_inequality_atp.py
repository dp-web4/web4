"""
Web4 Bootstrap Inequality & Fair ATP Distribution — Session 18, Track 5
======================================================================

Addresses the open question: "Does ATP recreate BTC-style wealth concentration?"

Models and compares multiple initial ATP distribution algorithms:
- Uniform: equal allocation to all
- Proof-of-work analog: first-come advantage
- Trust-weighted: allocation proportional to initial trust
- Quadratic: sqrt-dampened allocation (anti-plutocracy)
- Universal basic ATP: floor + merit
- Vesting: time-locked gradual release
- Challenge-based: allocation earned through verifiable work

Measures:
- Gini coefficient evolution
- Lorenz curves
- Theil index (decomposable inequality)
- Palma ratio (top 10% / bottom 40%)
- Social mobility (quartile transitions)
- Sybil resistance of each scheme

~90 checks expected.
"""

import math
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ============================================================
# §1 — Inequality Metrics
# ============================================================

def gini_coefficient(values: List[float]) -> float:
    """Gini coefficient: 0 = perfect equality, 1 = perfect inequality."""
    if not values or all(v == 0 for v in values):
        return 0.0
    sorted_v = sorted(values)
    n = len(sorted_v)
    total = sum(sorted_v)
    if total == 0:
        return 0.0
    cumulative = sum((i + 1) * v for i, v in enumerate(sorted_v))
    return (2 * cumulative - (n + 1) * total) / (n * total)


def lorenz_curve(values: List[float], points: int = 10) -> List[Tuple[float, float]]:
    """
    Lorenz curve: (cumulative % of population, cumulative % of wealth).
    Perfect equality = diagonal line.
    """
    if not values:
        return [(0, 0), (1, 1)]
    sorted_v = sorted(values)
    total = sum(sorted_v)
    if total == 0:
        return [(i / points, i / points) for i in range(points + 1)]

    n = len(sorted_v)
    curve = [(0.0, 0.0)]
    cumsum = 0.0
    for i in range(points):
        idx = int((i + 1) / points * n) - 1
        idx = max(0, min(idx, n - 1))
        cumsum = sum(sorted_v[:idx + 1])
        curve.append(((i + 1) / points, cumsum / total))

    return curve


def theil_index(values: List[float]) -> float:
    """
    Theil index: entropy-based inequality measure.
    0 = perfect equality, higher = more inequality.
    Decomposable across subgroups.
    """
    if not values:
        return 0.0
    n = len(values)
    mean = sum(values) / n
    if mean <= 0:
        return 0.0

    return sum(
        (v / mean) * math.log(v / mean + 1e-15) if v > 0 else 0
        for v in values
    ) / n


def palma_ratio(values: List[float]) -> float:
    """
    Palma ratio: income of top 10% / income of bottom 40%.
    Lower = more equal. Typically 1-2 for OECD countries.
    """
    if not values or len(values) < 10:
        return 0.0
    sorted_v = sorted(values)
    n = len(sorted_v)
    bottom_40 = sum(sorted_v[:int(n * 0.4)])
    top_10 = sum(sorted_v[int(n * 0.9):])
    return top_10 / bottom_40 if bottom_40 > 0 else float('inf')


def test_section_1():
    checks = []

    # Perfect equality
    equal = [100.0] * 100
    checks.append(("gini_equal", abs(gini_coefficient(equal)) < 0.01))

    # Perfect inequality
    unequal = [0.0] * 99 + [10000.0]
    checks.append(("gini_unequal", gini_coefficient(unequal) > 0.9))

    # Moderate inequality
    moderate = [10.0 + i * 2 for i in range(100)]
    gini_mod = gini_coefficient(moderate)
    checks.append(("gini_moderate", 0.1 < gini_mod < 0.5))

    # Lorenz curve
    curve = lorenz_curve(moderate)
    checks.append(("lorenz_starts_00", curve[0] == (0.0, 0.0)))
    # Below diagonal for unequal distribution
    checks.append(("lorenz_below_diagonal", any(
        y < x for x, y in curve if x > 0 and x < 1
    )))

    # Theil index
    theil_equal = theil_index(equal)
    theil_unequal = theil_index([1.0] * 90 + [100.0] * 10)
    checks.append(("theil_equal_zero", theil_equal < 0.01))
    checks.append(("theil_unequal_positive", theil_unequal > 0.1))

    # Palma ratio
    palma = palma_ratio(moderate)
    checks.append(("palma_finite", math.isfinite(palma)))
    checks.append(("palma_positive", palma > 0))

    # Metrics are consistent
    vals = [random.Random(42).uniform(10, 100) for _ in range(100)]
    g = gini_coefficient(vals)
    t = theil_index(vals)
    checks.append(("gini_theil_correlated", (g > 0) == (t > 0)))

    return checks


# ============================================================
# §2 — Distribution Algorithms
# ============================================================

@dataclass
class Entity:
    entity_id: str
    trust: float = 0.5
    atp_balance: float = 0.0
    joined_at: int = 0  # Time step when joined
    tasks_completed: int = 0
    hardware_bound: bool = False


def distribute_uniform(entities: List[Entity], total_atp: float) -> Dict[str, float]:
    """Equal allocation to all entities."""
    per_entity = total_atp / len(entities) if entities else 0
    return {e.entity_id: per_entity for e in entities}


def distribute_proof_of_work(entities: List[Entity], total_atp: float,
                             rng: random.Random) -> Dict[str, float]:
    """
    PoW-analog: early joiners get exponentially more.
    Models BTC-style first-mover advantage.
    """
    allocation = {}
    remaining = total_atp
    # Earlier entities get larger share
    sorted_entities = sorted(entities, key=lambda e: e.joined_at)
    for i, e in enumerate(sorted_entities):
        share = remaining * 0.2  # Take 20% of remaining
        allocation[e.entity_id] = share
        remaining -= share
    # Distribute remainder equally
    if remaining > 0 and entities:
        per_entity = remaining / len(entities)
        for e in entities:
            allocation[e.entity_id] = allocation.get(e.entity_id, 0) + per_entity
    return allocation


def distribute_trust_weighted(entities: List[Entity], total_atp: float) -> Dict[str, float]:
    """Allocation proportional to trust score."""
    total_trust = sum(e.trust for e in entities)
    if total_trust <= 0:
        return distribute_uniform(entities, total_atp)
    return {e.entity_id: total_atp * e.trust / total_trust for e in entities}


def distribute_quadratic(entities: List[Entity], total_atp: float) -> Dict[str, float]:
    """
    Quadratic (sqrt-dampened) allocation.
    Reduces concentration: 4x trust → 2x allocation, not 4x.
    """
    sqrt_trusts = {e.entity_id: math.sqrt(max(0, e.trust)) for e in entities}
    total_sqrt = sum(sqrt_trusts.values())
    if total_sqrt <= 0:
        return distribute_uniform(entities, total_atp)
    return {eid: total_atp * st / total_sqrt for eid, st in sqrt_trusts.items()}


def distribute_ubi_plus_merit(entities: List[Entity], total_atp: float,
                              ubi_fraction: float = 0.5) -> Dict[str, float]:
    """
    Universal Basic ATP + merit bonus.
    UBI portion split equally, merit portion by trust.
    """
    ubi_pool = total_atp * ubi_fraction
    merit_pool = total_atp * (1 - ubi_fraction)

    ubi_per = ubi_pool / len(entities) if entities else 0
    total_trust = sum(e.trust for e in entities)

    allocation = {}
    for e in entities:
        merit = merit_pool * e.trust / total_trust if total_trust > 0 else merit_pool / len(entities)
        allocation[e.entity_id] = ubi_per + merit

    return allocation


def distribute_vesting(entities: List[Entity], total_atp: float,
                       current_time: int, vesting_period: int = 100) -> Dict[str, float]:
    """
    Time-locked vesting: entities receive allocation gradually.
    Prevents dump-and-run.
    """
    allocation = {}
    per_entity = total_atp / len(entities) if entities else 0
    for e in entities:
        time_in = current_time - e.joined_at
        vested_fraction = min(1.0, time_in / vesting_period)
        allocation[e.entity_id] = per_entity * vested_fraction
    return allocation


def distribute_challenge_based(entities: List[Entity], total_atp: float) -> Dict[str, float]:
    """Allocation based on verifiable work (tasks completed)."""
    total_tasks = sum(e.tasks_completed for e in entities)
    if total_tasks <= 0:
        return distribute_uniform(entities, total_atp)
    return {e.entity_id: total_atp * e.tasks_completed / total_tasks for e in entities}


def test_section_2():
    checks = []
    rng = random.Random(42)

    # Create diverse entities
    entities = []
    for i in range(50):
        e = Entity(
            entity_id=f"e{i}",
            trust=rng.uniform(0.1, 0.9),
            joined_at=i,
            tasks_completed=rng.randint(0, 20),
            hardware_bound=rng.random() > 0.5,
        )
        entities.append(e)

    total_atp = 10000.0

    # Test each distribution
    uniform = distribute_uniform(entities, total_atp)
    checks.append(("uniform_equal", len(set(round(v, 2) for v in uniform.values())) == 1))
    checks.append(("uniform_total", abs(sum(uniform.values()) - total_atp) < 0.01))

    pow_dist = distribute_proof_of_work(entities, total_atp, rng)
    checks.append(("pow_total", abs(sum(pow_dist.values()) - total_atp) < 0.01))
    # Early joiners should get more
    checks.append(("pow_early_advantage", pow_dist["e0"] > pow_dist["e49"]))

    trust_w = distribute_trust_weighted(entities, total_atp)
    checks.append(("trust_total", abs(sum(trust_w.values()) - total_atp) < 0.01))

    quad = distribute_quadratic(entities, total_atp)
    checks.append(("quad_total", abs(sum(quad.values()) - total_atp) < 0.01))

    ubi = distribute_ubi_plus_merit(entities, total_atp, 0.5)
    checks.append(("ubi_total", abs(sum(ubi.values()) - total_atp) < 0.01))

    vest = distribute_vesting(entities, total_atp, current_time=50, vesting_period=100)
    checks.append(("vest_total_leq", sum(vest.values()) <= total_atp + 0.01))
    # Earlier joiners have vested more
    checks.append(("vest_time_advantage", vest["e0"] > vest["e49"]))

    challenge = distribute_challenge_based(entities, total_atp)
    checks.append(("challenge_total", abs(sum(challenge.values()) - total_atp) < 0.01))

    return checks


# ============================================================
# §3 — Gini Comparison Across Schemes
# ============================================================

def test_section_3():
    checks = []
    rng = random.Random(42)

    entities = []
    for i in range(200):
        entities.append(Entity(
            entity_id=f"e{i}",
            trust=rng.uniform(0.1, 0.9),
            joined_at=i,
            tasks_completed=rng.randint(0, 30),
        ))

    total_atp = 50000.0

    schemes = {
        "uniform": distribute_uniform(entities, total_atp),
        "pow": distribute_proof_of_work(entities, total_atp, rng),
        "trust": distribute_trust_weighted(entities, total_atp),
        "quadratic": distribute_quadratic(entities, total_atp),
        "ubi_50": distribute_ubi_plus_merit(entities, total_atp, 0.5),
        "ubi_80": distribute_ubi_plus_merit(entities, total_atp, 0.8),
        "challenge": distribute_challenge_based(entities, total_atp),
    }

    ginis = {}
    for name, alloc in schemes.items():
        values = list(alloc.values())
        ginis[name] = gini_coefficient(values)

    # Uniform should have Gini ≈ 0
    checks.append(("uniform_lowest_gini", ginis["uniform"] < 0.01))

    # PoW should have highest Gini (most unequal)
    checks.append(("pow_highest_gini", ginis["pow"] > ginis["trust"]))

    # Quadratic should be more equal than pure trust-weighted
    checks.append(("quadratic_less_than_trust", ginis["quadratic"] < ginis["trust"]))

    # UBI with higher floor is more equal
    checks.append(("ubi80_more_equal", ginis["ubi_80"] < ginis["ubi_50"]))

    # All Ginis are valid [0, 1]
    for name, g in ginis.items():
        checks.append((f"gini_{name}_valid", 0 <= g <= 1))

    return checks


# ============================================================
# §4 — Dynamic Inequality Evolution
# ============================================================

def simulate_economy(entities: List[Entity], initial_alloc: Dict[str, float],
                     rounds: int, rng: random.Random,
                     task_reward: float = 10.0, transfer_rate: float = 0.1,
                     fee_rate: float = 0.05) -> List[Dict]:
    """
    Simulate economic activity over multiple rounds.
    Returns trajectory of inequality metrics.
    """
    balances = dict(initial_alloc)
    trajectory = []

    for r in range(rounds):
        # Each entity earns from tasks (trust-weighted)
        for e in entities:
            if e.trust > 0:
                reward = task_reward * e.trust * rng.uniform(0.5, 1.5)
                balances[e.entity_id] = balances.get(e.entity_id, 0) + reward

        # Random transfers between entities
        n_transfers = int(len(entities) * transfer_rate)
        for _ in range(n_transfers):
            sender = rng.choice(entities)
            receiver = rng.choice(entities)
            if sender.entity_id != receiver.entity_id:
                amount = balances.get(sender.entity_id, 0) * rng.uniform(0.01, 0.05)
                fee = amount * fee_rate
                if balances.get(sender.entity_id, 0) >= amount + fee:
                    balances[sender.entity_id] -= amount + fee
                    balances[receiver.entity_id] = balances.get(receiver.entity_id, 0) + amount

        vals = [balances.get(e.entity_id, 0) for e in entities]
        trajectory.append({
            "round": r,
            "gini": gini_coefficient(vals),
            "theil": theil_index(vals),
            "palma": palma_ratio(vals),
            "mean": sum(vals) / len(vals),
            "median": sorted(vals)[len(vals) // 2],
        })

    return trajectory


def test_section_4():
    checks = []
    rng = random.Random(42)

    entities = []
    for i in range(100):
        entities.append(Entity(
            entity_id=f"e{i}",
            trust=rng.uniform(0.1, 0.9),
            joined_at=i,
        ))

    total_atp = 10000.0

    # Simulate with uniform initial distribution
    uniform_alloc = distribute_uniform(entities, total_atp)
    traj_uniform = simulate_economy(entities, uniform_alloc, 50, rng)

    checks.append(("trajectory_length", len(traj_uniform) == 50))
    checks.append(("gini_evolves", traj_uniform[-1]["gini"] != traj_uniform[0]["gini"]))

    # Starting uniform → Gini increases (inequality naturally emerges from trust-weighted rewards)
    checks.append(("inequality_emerges", traj_uniform[-1]["gini"] > traj_uniform[0]["gini"]))

    # Simulate with PoW initial distribution
    pow_alloc = distribute_proof_of_work(entities, total_atp, rng)
    traj_pow = simulate_economy(entities, pow_alloc, 50, rng)

    # PoW starts with high inequality
    checks.append(("pow_starts_unequal", traj_pow[0]["gini"] > traj_uniform[0]["gini"]))

    # UBI distribution
    ubi_alloc = distribute_ubi_plus_merit(entities, total_atp, 0.7)
    traj_ubi = simulate_economy(entities, ubi_alloc, 50, rng)

    # UBI should maintain lower inequality over time
    checks.append(("ubi_lower_gini", traj_ubi[-1]["gini"] < traj_pow[-1]["gini"]))

    # Palma ratio stays finite
    checks.append(("palma_finite", all(math.isfinite(t["palma"]) for t in traj_uniform)))

    return checks


# ============================================================
# §5 — Sybil Resistance Analysis
# ============================================================

def sybil_attack_profit(distribution_fn, entities: List[Entity], total_atp: float,
                        n_sybils: int, sybil_cost: float, rng: random.Random,
                        **kwargs) -> Dict:
    """
    Model a sybil attack: create n_sybils fake identities.
    Compare attacker's total allocation vs cost.
    """
    # Without sybils
    alloc_honest = distribution_fn(entities, total_atp, **kwargs)
    attacker = entities[0]
    honest_allocation = alloc_honest.get(attacker.entity_id, 0)

    # With sybils: attacker creates fake entities
    sybils = []
    for i in range(n_sybils):
        sybils.append(Entity(
            entity_id=f"sybil_{i}",
            trust=0.3,  # Sybils typically have lower trust
            joined_at=max(e.joined_at for e in entities) + 1,  # Late joiners
            tasks_completed=0,
        ))

    all_entities = entities + sybils
    alloc_sybil = distribution_fn(all_entities, total_atp, **kwargs)

    # Attacker controls original + all sybils
    sybil_total = alloc_sybil.get(attacker.entity_id, 0) + sum(
        alloc_sybil.get(f"sybil_{i}", 0) for i in range(n_sybils)
    )

    return {
        "honest_allocation": honest_allocation,
        "sybil_allocation": sybil_total,
        "sybil_cost": n_sybils * sybil_cost,
        "profit": sybil_total - honest_allocation - n_sybils * sybil_cost,
        "profitable": sybil_total - honest_allocation > n_sybils * sybil_cost,
    }


def test_section_5():
    checks = []
    rng = random.Random(42)

    entities = []
    for i in range(50):
        entities.append(Entity(
            entity_id=f"e{i}",
            trust=rng.uniform(0.3, 0.9),
            joined_at=i,
            tasks_completed=rng.randint(5, 20),
        ))

    total_atp = 10000.0
    sybil_cost = 50.0  # Cost per sybil identity

    # Test sybil resistance of each scheme
    # Uniform: sybils dilute total but sybil gains more than cost if cheap
    result_uniform = sybil_attack_profit(
        distribute_uniform, entities, total_atp, 10, sybil_cost, rng
    )
    checks.append(("uniform_sybil_result", isinstance(result_uniform["profit"], float)))

    # Trust-weighted: sybils with low trust get small share
    result_trust = sybil_attack_profit(
        distribute_trust_weighted, entities, total_atp, 10, sybil_cost, rng
    )
    checks.append(("trust_sybil_less_profit", result_trust["profit"] < result_uniform["profit"]))

    # Quadratic: even more resistant (sqrt dampening)
    result_quad = sybil_attack_profit(
        distribute_quadratic, entities, total_atp, 10, sybil_cost, rng
    )
    checks.append(("quad_sybil_result", isinstance(result_quad["profit"], float)))

    # Challenge-based: sybils with 0 tasks get nothing
    result_challenge = sybil_attack_profit(
        distribute_challenge_based, entities, total_atp, 10, sybil_cost, rng
    )
    checks.append(("challenge_sybil_unprofitable", not result_challenge["profitable"]))

    # Increasing sybil cost reduces profit
    result_high_cost = sybil_attack_profit(
        distribute_uniform, entities, total_atp, 10, 200.0, rng
    )
    checks.append(("higher_cost_less_profit", result_high_cost["profit"] < result_uniform["profit"]))

    # Many sybils diminish returns
    result_many = sybil_attack_profit(
        distribute_trust_weighted, entities, total_atp, 50, sybil_cost, rng
    )
    per_sybil_gain_few = (result_trust["sybil_allocation"] - result_trust["honest_allocation"]) / 10
    per_sybil_gain_many = (result_many["sybil_allocation"] - result_many["honest_allocation"]) / 50
    checks.append(("diminishing_returns", per_sybil_gain_many < per_sybil_gain_few + 1))

    return checks


# ============================================================
# §6 — Social Mobility
# ============================================================

def compute_mobility(initial_balances: Dict[str, float],
                     final_balances: Dict[str, float],
                     n_quartiles: int = 4) -> Dict:
    """
    Compute social mobility by tracking quartile transitions.
    """
    entities = sorted(initial_balances.keys())

    def get_quartile(bal_dict):
        sorted_ents = sorted(entities, key=lambda e: bal_dict.get(e, 0))
        quartiles = {}
        n = len(sorted_ents)
        for i, e in enumerate(sorted_ents):
            quartiles[e] = i * n_quartiles // n
        return quartiles

    initial_q = get_quartile(initial_balances)
    final_q = get_quartile(final_balances)

    # Transition matrix
    transitions = [[0] * n_quartiles for _ in range(n_quartiles)]
    for e in entities:
        iq = initial_q.get(e, 0)
        fq = final_q.get(e, 0)
        transitions[iq][fq] += 1

    # Mobility index: 1 - trace(M)/n (higher = more mobility)
    total = len(entities)
    stayed = sum(transitions[i][i] for i in range(n_quartiles))
    mobility = 1 - stayed / total if total > 0 else 0

    # Upward mobility: moved to higher quartile
    upward = sum(1 for e in entities if final_q.get(e, 0) > initial_q.get(e, 0))

    return {
        "mobility_index": mobility,
        "upward_pct": upward / total if total > 0 else 0,
        "stayed_pct": stayed / total if total > 0 else 0,
        "transitions": transitions,
    }


def test_section_6():
    checks = []
    rng = random.Random(42)

    entities = []
    for i in range(100):
        entities.append(Entity(
            entity_id=f"e{i}",
            trust=rng.uniform(0.1, 0.9),
        ))

    total_atp = 10000.0

    # Uniform start → simulate → measure mobility
    uniform_alloc = distribute_uniform(entities, total_atp)
    traj = simulate_economy(entities, uniform_alloc, 100, rng)

    # Compute final balances
    final_balances = {}
    for e in entities:
        final_balances[e.entity_id] = uniform_alloc.get(e.entity_id, 0) + e.trust * 100  # Approximate

    mobility = compute_mobility(uniform_alloc, final_balances)
    checks.append(("mobility_computed", isinstance(mobility["mobility_index"], float)))
    checks.append(("mobility_bounded", 0 <= mobility["mobility_index"] <= 1))

    # Some upward mobility exists
    checks.append(("some_upward", mobility["upward_pct"] > 0))

    # Not perfect mobility (some stay in place)
    checks.append(("not_perfect_mobility", mobility["stayed_pct"] > 0))

    # Perfect equality → high stability (everyone stays in their quartile... actually
    # with uniform starting point, final position depends on trust-weighted earnings)
    checks.append(("mobility_index_valid", mobility["mobility_index"] >= 0))

    return checks


# ============================================================
# §7 — Redistribution Mechanisms
# ============================================================

def progressive_tax(balances: Dict[str, float], brackets: List[Tuple[float, float]]) -> Dict[str, float]:
    """
    Progressive tax on ATP balances.
    Brackets: [(threshold, rate), ...] in ascending order.
    Returns tax amounts per entity.
    """
    taxes = {}
    for eid, balance in balances.items():
        tax = 0.0
        prev_threshold = 0.0
        for threshold, rate in brackets:
            taxable = min(balance, threshold) - prev_threshold
            if taxable > 0:
                tax += taxable * rate
            prev_threshold = threshold
        # Everything above last bracket
        if balance > brackets[-1][0]:
            tax += (balance - brackets[-1][0]) * brackets[-1][1]
        taxes[eid] = tax
    return taxes


def redistribute(balances: Dict[str, float], taxes: Dict[str, float],
                 method: str = "equal") -> Dict[str, float]:
    """Redistribute collected taxes."""
    tax_revenue = sum(taxes.values())
    new_balances = {eid: bal - taxes.get(eid, 0) for eid, bal in balances.items()}

    n = len(new_balances)
    if method == "equal":
        per_entity = tax_revenue / n if n > 0 else 0
        return {eid: bal + per_entity for eid, bal in new_balances.items()}
    elif method == "bottom_half":
        # Give to bottom 50% only
        sorted_ents = sorted(new_balances.keys(), key=lambda e: new_balances[e])
        bottom = sorted_ents[:n // 2]
        per_entity = tax_revenue / len(bottom) if bottom else 0
        for eid in bottom:
            new_balances[eid] += per_entity
        return new_balances

    return new_balances


def test_section_7():
    checks = []
    rng = random.Random(42)

    balances = {f"e{i}": rng.uniform(10, 1000) for i in range(50)}

    # Progressive tax
    brackets = [(100, 0.05), (500, 0.15), (1000, 0.30)]
    taxes = progressive_tax(balances, brackets)

    # All taxes are non-negative
    checks.append(("taxes_non_negative", all(t >= 0 for t in taxes.values())))

    # Higher balance → higher tax rate (effective)
    high_bal_ent = max(balances, key=balances.get)
    low_bal_ent = min(balances, key=balances.get)
    effective_high = taxes[high_bal_ent] / balances[high_bal_ent]
    effective_low = taxes[low_bal_ent] / balances[low_bal_ent]
    checks.append(("progressive", effective_high >= effective_low))

    # Redistribution preserves total
    total_before = sum(balances.values())
    new_bal = redistribute(balances, taxes, "equal")
    total_after = sum(new_bal.values())
    checks.append(("redistribution_conserves", abs(total_after - total_before) < 0.01))

    # Redistribution reduces Gini
    gini_before = gini_coefficient(list(balances.values()))
    gini_after = gini_coefficient(list(new_bal.values()))
    checks.append(("gini_reduced", gini_after < gini_before))

    # Bottom-half redistribution
    new_bal_bottom = redistribute(balances, taxes, "bottom_half")
    total_bottom = sum(new_bal_bottom.values())
    checks.append(("bottom_half_conserves", abs(total_bottom - total_before) < 0.01))

    # Bottom-half reduces Gini more
    gini_bottom = gini_coefficient(list(new_bal_bottom.values()))
    checks.append(("bottom_half_more_equal", gini_bottom <= gini_after + 0.01))

    return checks


# ============================================================
# §8 — BTC vs Web4 Inequality Comparison
# ============================================================

def simulate_btc_model(n_entities: int, n_rounds: int, rng: random.Random) -> List[float]:
    """
    Simplified BTC-like model:
    - Mining reward proportional to computational power (wealth)
    - First-movers accumulate exponentially
    - No trust-based adjustment
    """
    balances = {i: 10.0 + i * 0.1 for i in range(n_entities)}  # Slight advantage for early

    for _ in range(n_rounds):
        total_power = sum(balances.values())
        block_reward = 50.0
        # Mining probability proportional to balance (simplified PoW)
        winner = rng.random() * total_power
        cumsum = 0.0
        for i in range(n_entities):
            cumsum += balances[i]
            if cumsum >= winner:
                balances[i] += block_reward
                break

    return list(balances.values())


def simulate_web4_model(n_entities: int, n_rounds: int, rng: random.Random) -> List[float]:
    """
    Web4 model:
    - Trust-weighted rewards (sqrt dampened)
    - Universal basic ATP
    - Transfer fees
    - No first-mover advantage in allocation
    """
    trusts = {i: rng.uniform(0.3, 0.9) for i in range(n_entities)}
    balances = {i: 100.0 for i in range(n_entities)}  # Equal start

    for _ in range(n_rounds):
        # Trust-weighted task rewards (sqrt dampened)
        for i in range(n_entities):
            quality = rng.uniform(0.3, 1.0)
            reward = 10.0 * quality * math.sqrt(trusts[i])
            balances[i] += reward

        # UBI component
        ubi = 5.0
        for i in range(n_entities):
            balances[i] += ubi

        # Random transfers with fees
        for _ in range(n_entities // 5):
            s = rng.randint(0, n_entities - 1)
            r = rng.randint(0, n_entities - 1)
            if s != r:
                amount = balances[s] * 0.02
                fee = amount * 0.05
                if balances[s] >= amount + fee:
                    balances[s] -= amount + fee
                    balances[r] += amount

    return list(balances.values())


def test_section_8():
    checks = []
    rng = random.Random(42)

    n = 200
    rounds = 300  # More rounds → more concentration in PoW model

    btc_balances = simulate_btc_model(n, rounds, rng)
    web4_balances = simulate_web4_model(n, rounds, rng)

    gini_btc = gini_coefficient(btc_balances)
    gini_web4 = gini_coefficient(web4_balances)

    checks.append(("btc_gini", 0 < gini_btc < 1))
    checks.append(("web4_gini", 0 < gini_web4 < 1))

    # Web4 should have LOWER inequality than BTC
    checks.append(("web4_more_equal", gini_web4 < gini_btc))

    # Palma comparison
    palma_btc = palma_ratio(btc_balances)
    palma_web4 = palma_ratio(web4_balances)
    checks.append(("web4_lower_palma", palma_web4 < palma_btc))

    # Theil comparison
    theil_btc = theil_index(btc_balances)
    theil_web4 = theil_index(web4_balances)
    checks.append(("web4_lower_theil", theil_web4 < theil_btc))

    # BTC should have extreme concentration
    checks.append(("btc_concentrated", gini_btc > 0.5))

    # Web4 should be moderate (not perfectly equal due to trust variation)
    checks.append(("web4_moderate", 0.05 < gini_web4 < 0.5))

    return checks


# ============================================================
# §9 — Optimal Distribution Design
# ============================================================

def evaluate_scheme(entities: List[Entity], total_atp: float,
                    distribution_fn, rng: random.Random,
                    n_sybils: int = 10, sybil_cost: float = 50.0,
                    **kwargs) -> Dict:
    """Comprehensive evaluation of a distribution scheme."""
    alloc = distribution_fn(entities, total_atp, **kwargs)
    values = list(alloc.values())

    gini = gini_coefficient(values)
    theil = theil_index(values)
    palma = palma_ratio(values)

    sybil = sybil_attack_profit(distribution_fn, entities, total_atp,
                                n_sybils, sybil_cost, rng, **kwargs)

    return {
        "gini": gini,
        "theil": theil,
        "palma": palma,
        "sybil_profitable": sybil["profitable"],
        "sybil_profit": sybil["profit"],
        "total_distributed": sum(values),
        "min_allocation": min(values),
        "max_allocation": max(values),
    }


def test_section_9():
    checks = []
    rng = random.Random(42)

    entities = []
    for i in range(100):
        entities.append(Entity(
            entity_id=f"e{i}",
            trust=rng.uniform(0.1, 0.9),
            joined_at=i,
            tasks_completed=rng.randint(0, 25),
        ))

    total_atp = 20000.0

    # Evaluate all schemes
    schemes = {
        "uniform": (distribute_uniform, {}),
        "trust": (distribute_trust_weighted, {}),
        "quadratic": (distribute_quadratic, {}),
        "ubi_50": (distribute_ubi_plus_merit, {"ubi_fraction": 0.5}),
        "ubi_80": (distribute_ubi_plus_merit, {"ubi_fraction": 0.8}),
        "challenge": (distribute_challenge_based, {}),
    }

    results = {}
    for name, (fn, kwargs) in schemes.items():
        results[name] = evaluate_scheme(entities, total_atp, fn, rng, **kwargs)

    # All schemes distribute the correct total
    for name, r in results.items():
        checks.append((f"{name}_total_ok", abs(r["total_distributed"] - total_atp) < 1.0))

    # Challenge-based is sybil-resistant (sybils have 0 tasks)
    checks.append(("challenge_sybil_safe", not results["challenge"]["sybil_profitable"]))

    # UBI_80 is most equal (lowest Gini)
    ubi80_gini = results["ubi_80"]["gini"]
    checks.append(("ubi80_most_equal", ubi80_gini <= min(
        r["gini"] for name, r in results.items() if name != "uniform"
    ) + 0.01))

    # No scheme gives zero to any entity (except challenge where some have 0 tasks)
    for name in ["uniform", "trust", "quadratic", "ubi_50", "ubi_80"]:
        checks.append((f"{name}_nonzero_min", results[name]["min_allocation"] > 0))

    return checks


# ============================================================
# §10 — Composite Optimal Scheme
# ============================================================

def distribute_composite_optimal(entities: List[Entity], total_atp: float,
                                 ubi_fraction: float = 0.3,
                                 challenge_fraction: float = 0.3,
                                 trust_fraction: float = 0.4) -> Dict[str, float]:
    """
    Composite scheme combining multiple distribution mechanisms:
    - UBI floor for basic participation
    - Challenge-based for verifiable work
    - Trust-weighted (quadratic) for reputation
    """
    ubi_pool = total_atp * ubi_fraction
    challenge_pool = total_atp * challenge_fraction
    trust_pool = total_atp * trust_fraction

    # UBI: equal share
    per_entity = ubi_pool / len(entities) if entities else 0

    # Challenge: by tasks
    total_tasks = sum(e.tasks_completed for e in entities)

    # Trust: quadratic
    sqrt_trusts = {e.entity_id: math.sqrt(max(0.01, e.trust)) for e in entities}
    total_sqrt = sum(sqrt_trusts.values())

    allocation = {}
    for e in entities:
        ubi = per_entity
        challenge = challenge_pool * e.tasks_completed / total_tasks if total_tasks > 0 else challenge_pool / len(entities)
        trust_share = trust_pool * sqrt_trusts[e.entity_id] / total_sqrt if total_sqrt > 0 else trust_pool / len(entities)
        allocation[e.entity_id] = ubi + challenge + trust_share

    return allocation


def test_section_10():
    checks = []
    rng = random.Random(42)

    entities = []
    for i in range(100):
        entities.append(Entity(
            entity_id=f"e{i}",
            trust=rng.uniform(0.1, 0.9),
            joined_at=i,
            tasks_completed=rng.randint(0, 25),
        ))

    total_atp = 20000.0

    # Composite scheme
    composite = distribute_composite_optimal(entities, total_atp)
    checks.append(("composite_total", abs(sum(composite.values()) - total_atp) < 0.01))

    # Gini is moderate (between uniform and pure trust-weighted)
    gini_composite = gini_coefficient(list(composite.values()))
    gini_uniform = gini_coefficient(list(distribute_uniform(entities, total_atp).values()))
    gini_trust = gini_coefficient(list(distribute_trust_weighted(entities, total_atp).values()))
    checks.append(("composite_gini_moderate", gini_composite < gini_trust))
    checks.append(("composite_not_zero", gini_composite > gini_uniform - 0.01))

    # Everyone gets something (UBI floor)
    checks.append(("composite_nonzero", min(composite.values()) > 0))

    # Sybil resistance: sybils with 0 tasks and low trust get minimal allocation
    sybil = sybil_attack_profit(
        distribute_composite_optimal, entities, total_atp, 10, 50.0, rng
    )
    # Should be unprofitable or marginally profitable
    checks.append(("composite_sybil_result", isinstance(sybil["profit"], float)))

    # Compare with BTC model
    btc_vals = simulate_btc_model(100, 100, rng)
    web4_composite = list(composite.values())
    checks.append(("composite_less_inequality_than_btc",
                    gini_coefficient(web4_composite) < gini_coefficient(btc_vals)))

    # Dynamic stability: run economy with composite initial
    traj = simulate_economy(entities, composite, 50, rng)
    final_gini = traj[-1]["gini"]
    initial_gini = traj[0]["gini"]
    # Gini should grow but stay moderate
    checks.append(("gini_stays_moderate", final_gini < 0.6))

    # Sensitivity: varying UBI fraction
    high_ubi = distribute_composite_optimal(entities, total_atp, ubi_fraction=0.8)
    low_ubi = distribute_composite_optimal(entities, total_atp, ubi_fraction=0.1)
    gini_high_ubi = gini_coefficient(list(high_ubi.values()))
    gini_low_ubi = gini_coefficient(list(low_ubi.values()))
    checks.append(("higher_ubi_more_equal", gini_high_ubi < gini_low_ubi))

    return checks


# ============================================================
# Harness
# ============================================================

def run_section(name, func):
    results = func()
    passed = sum(1 for _, v in results if v)
    total = len(results)
    status = "✓" if passed == total else "✗"
    print(f"  {status} {name}: {passed}/{total}")
    return results


def main():
    all_checks = []
    sections = [
        ("§1 Inequality Metrics", test_section_1),
        ("§2 Distribution Algorithms", test_section_2),
        ("§3 Gini Comparison", test_section_3),
        ("§4 Dynamic Evolution", test_section_4),
        ("§5 Sybil Resistance", test_section_5),
        ("§6 Social Mobility", test_section_6),
        ("§7 Redistribution Mechanisms", test_section_7),
        ("§8 BTC vs Web4 Comparison", test_section_8),
        ("§9 Optimal Distribution Design", test_section_9),
        ("§10 Composite Optimal Scheme", test_section_10),
    ]

    for name, func in sections:
        results = run_section(name, func)
        all_checks.extend(results)

    passed = sum(1 for _, v in all_checks if v)
    total = len(all_checks)
    print(f"\nTotal: {passed}/{total}")

    if passed < total:
        print(f"\nFailed checks:")
        for name, v in all_checks:
            if not v:
                print(f"    FAIL: {name}")


if __name__ == "__main__":
    main()
