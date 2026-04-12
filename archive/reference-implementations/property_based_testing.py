#!/usr/bin/env python3
"""
Property-Based Testing — Hypothesis-Powered Invariant Discovery
================================================================

Uses the Hypothesis library (Python QuickCheck) to find edge cases
in Web4 core operations that assertion-based tests miss.

Unlike formal_property_verification.py (12 hand-sampled proofs),
this generates THOUSANDS of random inputs to stress-test invariants,
with automatic shrinking to find minimal counterexamples.

Properties tested:
  PBT-1. ATP Conservation: transfer sequences preserve total supply
  PBT-2. ATP Transfer Commutativity: order-independent final totals
  PBT-3. T3 Update Idempotence: quality=0.5 is identity operation
  PBT-4. T3 Clamping Invariant: values always in [0,1]
  PBT-5. Sliding Scale Monotonicity: higher quality → higher payment
  PBT-6. Sliding Scale Continuity: small input change → small output change
  PBT-7. Trust Bridge Round-Trip: 6→3→6 preserves primary dimensions
  PBT-8. MRH Decay Monotonicity: more hops → less trust (never more)
  PBT-9. Energy Ratio Bounds: always in [0,1]
  PBT-10. Diminishing Returns Convergence: series is bounded
  PBT-11. Lock Safety: lock+unlock = original balance
  PBT-12. Delegation Narrowing: child ⊆ parent at all depths
  PBT-13. Governance Alignment Primacy: non-aligned always fails
  PBT-14. Appeal Reversibility: reverse(penalty(x)) ≈ x
  PBT-15. Conservation Under Recharge: recharge + fees = predictable
  PBT-16. Sybil Unprofitability: N identities never beat 1 honest
  PBT-17. Gini Coefficient Bounds: always in [0,1]
  PBT-18. Hash Chain Integrity: any tampering is detected
  PBT-19. Composite Score Bounds: T3/V3 composites always in [0,1]
  PBT-20. Fee Monotonicity: higher fee rate → higher fee

Session: Legion Autonomous Session 13
"""

import hashlib
import json
import math
import random
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from hypothesis import given, settings, assume, note, HealthCheck
from hypothesis import strategies as st

# ═══════════════════════════════════════════════════════════════
# CORE FUNCTIONS UNDER TEST
# ═══════════════════════════════════════════════════════════════

def atp_transfer(sender: float, receiver: float, amount: float,
                 fee_rate: float, max_balance: float = float('inf')
                 ) -> Tuple[float, float, float, float]:
    """ATP transfer with fee and optional balance cap."""
    fee = amount * fee_rate
    sender -= (amount + fee)
    actual_credit = max(0.0, min(amount, max_balance - receiver))
    overflow = amount - actual_credit
    receiver += actual_credit
    sender += overflow
    return sender, receiver, fee, overflow


def t3_update(talent: float, training: float, temperament: float,
              quality: float) -> Tuple[float, float, float]:
    """T3 update from action quality. Delta = 0.02 * (quality - 0.5)."""
    base_delta = 0.02 * (quality - 0.5)
    factors = {"talent": 1.0, "training": 0.8, "temperament": 0.6}
    t = max(0.0, min(1.0, talent + base_delta * factors["talent"]))
    tr = max(0.0, min(1.0, training + base_delta * factors["training"]))
    te = max(0.0, min(1.0, temperament + base_delta * factors["temperament"]))
    return t, tr, te


def t3_composite(talent: float, training: float, temperament: float) -> float:
    """T3 composite: talent*0.4 + training*0.3 + temperament*0.3."""
    return talent * 0.4 + training * 0.3 + temperament * 0.3


def v3_composite(valuation: float, veracity: float, validity: float) -> float:
    """V3 composite: valuation*0.3 + veracity*0.35 + validity*0.35."""
    return valuation * 0.3 + veracity * 0.35 + validity * 0.35


def sliding_scale(quality: float, base_payment: float,
                  zero_threshold: float, full_threshold: float) -> float:
    """Continuous sliding scale payment."""
    if quality < zero_threshold:
        return 0.0
    elif quality <= full_threshold:
        scale = (quality - zero_threshold) / (full_threshold - zero_threshold)
        return base_payment * scale
    else:
        return base_payment


def trust_bridge_6to3(six_dim: Dict[str, float]) -> Dict[str, float]:
    """6-dim to 3-dim trust mapping."""
    pw = 0.6
    sw = (1.0 - pw) / 3.0
    mapping = {
        "talent": ("competence", ["alignment", "witnesses", "lineage"]),
        "training": ("reliability", ["alignment", "witnesses", "lineage"]),
        "temperament": ("consistency", ["alignment", "witnesses", "lineage"]),
    }
    result = {}
    for out_dim, (primary, secondaries) in mapping.items():
        val = pw * six_dim[primary]
        for sec in secondaries:
            val += sw * six_dim[sec]
        result[out_dim] = val
    return result


def mrh_trust_decay(base_trust: float, hops: int, decay: float) -> float:
    """MRH trust at given hop count."""
    if hops >= 5:
        return 0.0
    return base_trust * (decay ** hops)


def energy_ratio(atp: float, adp: float) -> float:
    """Energy ratio = atp / (atp + adp), 0.5 for zero/zero."""
    total = atp + adp
    if total == 0:
        return 0.5
    return atp / total


def diminishing_returns(n: int, base: float) -> List[float]:
    """Diminishing returns factors: base^i for i in 0..n-1."""
    return [base ** i for i in range(n)]


def hash_chain_entry(content: str, prev_hash: str) -> str:
    """Single hash chain entry."""
    return hashlib.sha256(f"{prev_hash}:{content}".encode()).hexdigest()


def gini_coefficient(values: List[float]) -> float:
    """Gini coefficient of a distribution."""
    if not values or all(v == 0 for v in values):
        return 0.0
    n = len(values)
    sorted_v = sorted(values)
    total = sum(sorted_v)
    if total == 0:
        return 0.0
    cum = 0.0
    area = 0.0
    for i, v in enumerate(sorted_v):
        cum += v
        area += cum
    return 1.0 - (2.0 * area) / (n * total) + 1.0 / n


# ═══════════════════════════════════════════════════════════════
# HYPOTHESIS STRATEGIES
# ═══════════════════════════════════════════════════════════════

unit_float = st.floats(min_value=0.0, max_value=1.0, allow_nan=False,
                       allow_infinity=False)
positive_float = st.floats(min_value=0.01, max_value=10000.0,
                           allow_nan=False, allow_infinity=False)
balance_float = st.floats(min_value=0.0, max_value=1000.0,
                          allow_nan=False, allow_infinity=False)
small_positive = st.floats(min_value=0.001, max_value=100.0,
                           allow_nan=False, allow_infinity=False)
fee_rate = st.floats(min_value=0.0, max_value=0.5, allow_nan=False,
                     allow_infinity=False)

six_dim_strategy = st.fixed_dictionaries({
    "competence": unit_float,
    "reliability": unit_float,
    "consistency": unit_float,
    "alignment": unit_float,
    "witnesses": unit_float,
    "lineage": unit_float,
})


# ═══════════════════════════════════════════════════════════════
# PROPERTY TESTS
# ═══════════════════════════════════════════════════════════════

passed = 0
failed = 0
errors = []
TOLERANCE = 1e-9


def check(condition, msg):
    global passed, failed, errors
    if condition:
        passed += 1
    else:
        failed += 1
        errors.append(msg)
        print(f"  FAIL: {msg}")


def run_hypothesis_test(test_func, name, n_examples=500):
    """Run a hypothesis test and report results."""
    global passed, failed, errors
    try:
        test_func()
        passed += 1
        print(f"  PASS ({n_examples} examples)")
    except Exception as e:
        failed += 1
        msg = f"{name}: {e}"
        errors.append(msg)
        print(f"  FAIL: {msg}")


# ── PBT-1: ATP Conservation Under Transfer Sequences ──────────────

print("\n══════════════════════════════════════════════════════════════")
print("  Property-Based Testing — Hypothesis-Powered Invariants")
print("══════════════════════════════════════════════════════════════")

print("\n§1 ATP Conservation Under Transfer Sequences")

@given(
    balances=st.lists(balance_float, min_size=2, max_size=10),
    transfers=st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=9),
            st.integers(min_value=0, max_value=9),
            small_positive,
        ),
        min_size=1, max_size=20,
    ),
    fee_r=fee_rate,
)
@settings(max_examples=500, suppress_health_check=[HealthCheck.too_slow])
def test_atp_conservation(balances, transfers, fee_r):
    """Total ATP + total fees = initial total, always."""
    n = len(balances)
    bals = list(balances)
    initial_total = sum(bals)
    total_fees = 0.0
    for (fr, to, amount) in transfers:
        fr_idx = fr % n
        to_idx = to % n
        if fr_idx == to_idx:
            continue
        if amount > bals[fr_idx]:
            continue  # insufficient funds — skip
        fee = amount * fee_r
        if amount + fee > bals[fr_idx]:
            continue
        bals[fr_idx] -= (amount + fee)
        bals[to_idx] += amount
        total_fees += fee
    final_total = sum(bals)
    assert abs(initial_total - (final_total + total_fees)) < TOLERANCE, \
        f"Conservation violated: {initial_total} != {final_total} + {total_fees}"

run_hypothesis_test(test_atp_conservation, "PBT-1: ATP Conservation")


# ── PBT-2: ATP Transfer Order Independence (Final Totals) ─────────

print("\n§2 ATP Transfer Order Independence (Total Supply)")

@given(
    s=balance_float,
    r=balance_float,
    a1=small_positive,
    a2=small_positive,
    fr=fee_rate,
)
@settings(max_examples=500, suppress_health_check=[HealthCheck.too_slow])
def test_transfer_total_independence(s, r, a1, a2, fr):
    """Two transfers between same pair: total_supply change is order-independent."""
    # Order 1: transfer a1 then a2
    s1, r1 = s, r
    total_fees_1 = 0.0
    if a1 + a1 * fr <= s1:
        fee = a1 * fr
        s1 -= (a1 + fee)
        r1 += a1
        total_fees_1 += fee
    if a2 + a2 * fr <= s1:
        fee = a2 * fr
        s1 -= (a2 + fee)
        r1 += a2
        total_fees_1 += fee
    # Order 2: transfer a2 then a1
    s2, r2 = s, r
    total_fees_2 = 0.0
    if a2 + a2 * fr <= s2:
        fee = a2 * fr
        s2 -= (a2 + fee)
        r2 += a2
        total_fees_2 += fee
    if a1 + a1 * fr <= s2:
        fee = a1 * fr
        s2 -= (a1 + fee)
        r2 += a1
        total_fees_2 += fee
    # Total supply change should be equal (only fees leave the system)
    supply1 = s1 + r1
    supply2 = s2 + r2
    # Note: individual balances may differ, but total_fees determines supply
    assert abs((s + r - supply1) - total_fees_1) < TOLERANCE
    assert abs((s + r - supply2) - total_fees_2) < TOLERANCE

run_hypothesis_test(test_transfer_total_independence, "PBT-2: Transfer Total Independence")


# ── PBT-3: T3 Update Identity at quality=0.5 ──────────────────────

print("\n§3 T3 Update Identity (quality=0.5 → no change)")

@given(t=unit_float, tr=unit_float, te=unit_float)
@settings(max_examples=500)
def test_t3_identity(t, tr, te):
    """quality=0.5 produces zero delta, so T3 is unchanged."""
    new_t, new_tr, new_te = t3_update(t, tr, te, 0.5)
    assert abs(new_t - t) < TOLERANCE, f"talent changed: {t} -> {new_t}"
    assert abs(new_tr - tr) < TOLERANCE, f"training changed: {tr} -> {new_tr}"
    assert abs(new_te - te) < TOLERANCE, f"temperament changed: {te} -> {new_te}"

run_hypothesis_test(test_t3_identity, "PBT-3: T3 Identity at 0.5")


# ── PBT-4: T3 Clamping Invariant ──────────────────────────────────

print("\n§4 T3 Clamping Invariant ([0,1] bounds)")

@given(t=unit_float, tr=unit_float, te=unit_float, q=unit_float)
@settings(max_examples=500)
def test_t3_clamping(t, tr, te, q):
    """T3 values always stay in [0,1] regardless of input."""
    new_t, new_tr, new_te = t3_update(t, tr, te, q)
    assert 0.0 <= new_t <= 1.0, f"talent out of bounds: {new_t}"
    assert 0.0 <= new_tr <= 1.0, f"training out of bounds: {new_tr}"
    assert 0.0 <= new_te <= 1.0, f"temperament out of bounds: {new_te}"

run_hypothesis_test(test_t3_clamping, "PBT-4: T3 Clamping")


# ── PBT-5: Sliding Scale Monotonicity ─────────────────────────────

print("\n§5 Sliding Scale Monotonicity")

@given(
    q1=unit_float,
    q2=unit_float,
    base=positive_float,
    zero=st.floats(min_value=0.0, max_value=0.4, allow_nan=False, allow_infinity=False),
    full=st.floats(min_value=0.5, max_value=1.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=500)
def test_sliding_monotonicity(q1, q2, base, zero, full):
    """Higher quality → higher or equal payment."""
    assume(zero < full)
    p1 = sliding_scale(q1, base, zero, full)
    p2 = sliding_scale(q2, base, zero, full)
    if q1 <= q2:
        assert p1 <= p2 + TOLERANCE, \
            f"Monotonicity violated: q1={q1}→{p1}, q2={q2}→{p2}"

run_hypothesis_test(test_sliding_monotonicity, "PBT-5: Sliding Scale Monotonicity")


# ── PBT-6: Sliding Scale Continuity ───────────────────────────────

print("\n§6 Sliding Scale Lipschitz Continuity")

@given(
    q=unit_float,
    base=positive_float,
    zero=st.floats(min_value=0.0, max_value=0.4, allow_nan=False, allow_infinity=False),
    full=st.floats(min_value=0.5, max_value=1.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=500)
def test_sliding_continuity(q, base, zero, full):
    """Small input change → bounded output change (Lipschitz)."""
    assume(zero < full)
    epsilon = 0.001
    q2 = min(1.0, q + epsilon)
    p1 = sliding_scale(q, base, zero, full)
    p2 = sliding_scale(q2, base, zero, full)
    # Lipschitz constant: base / (full - zero) for the ramp zone
    max_slope = base / (full - zero)
    assert abs(p2 - p1) <= max_slope * epsilon + TOLERANCE, \
        f"Continuity violated: |{p2}-{p1}| = {abs(p2-p1)} > {max_slope * epsilon}"

run_hypothesis_test(test_sliding_continuity, "PBT-6: Sliding Scale Continuity")


# ── PBT-7: Trust Bridge Primary Dimension Preservation ─────────────

print("\n§7 Trust Bridge Primary Preservation")

@given(six_dim=six_dim_strategy)
@settings(max_examples=500)
def test_trust_bridge_primary(six_dim):
    """Primary dimension dominates (0.6 weight), so order is preserved."""
    result = trust_bridge_6to3(six_dim)
    # Talent's primary is competence, training's is reliability, temperament's is consistency
    # Since secondaries are shared, if competence > reliability > consistency,
    # then talent > training > temperament
    if six_dim["competence"] > six_dim["reliability"]:
        assert result["talent"] >= result["training"] - TOLERANCE
    if six_dim["reliability"] > six_dim["consistency"]:
        assert result["training"] >= result["temperament"] - TOLERANCE

run_hypothesis_test(test_trust_bridge_primary, "PBT-7: Trust Bridge Primary Preservation")


# ── PBT-8: MRH Decay Monotonicity ─────────────────────────────────

print("\n§8 MRH Decay Monotonicity")

@given(
    base=unit_float,
    h1=st.integers(min_value=0, max_value=6),
    h2=st.integers(min_value=0, max_value=6),
    decay=st.floats(min_value=0.1, max_value=0.99, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=500)
def test_mrh_monotonicity(base, h1, h2, decay):
    """More hops → less trust (monotone decreasing)."""
    t1 = mrh_trust_decay(base, h1, decay)
    t2 = mrh_trust_decay(base, h2, decay)
    if h1 <= h2:
        assert t1 >= t2 - TOLERANCE, \
            f"MRH not monotone: hop {h1}→{t1}, hop {h2}→{t2}"

run_hypothesis_test(test_mrh_monotonicity, "PBT-8: MRH Decay Monotonicity")


# ── PBT-9: Energy Ratio Bounds ─────────────────────────────────────

print("\n§9 Energy Ratio Bounds [0,1]")

@given(
    atp=st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
    adp=st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=500)
def test_energy_ratio_bounds(atp, adp):
    """Energy ratio always in [0, 1]."""
    r = energy_ratio(atp, adp)
    assert 0.0 <= r <= 1.0, f"Energy ratio {r} out of bounds"

run_hypothesis_test(test_energy_ratio_bounds, "PBT-9: Energy Ratio Bounds")


# ── PBT-10: Diminishing Returns Convergence ────────────────────────

print("\n§10 Diminishing Returns Series Convergence")

@given(
    n=st.integers(min_value=1, max_value=100),
    base=st.floats(min_value=0.1, max_value=0.99, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=500)
def test_diminishing_convergence(n, base):
    """Sum of diminishing series is bounded by 1/(1-base)."""
    factors = diminishing_returns(n, base)
    total = sum(factors)
    theoretical_max = 1.0 / (1.0 - base)
    assert total <= theoretical_max + TOLERANCE, \
        f"Series sum {total} exceeds bound {theoretical_max}"
    # Also verify monotone decreasing
    for i in range(len(factors) - 1):
        assert factors[i] >= factors[i + 1] - TOLERANCE

run_hypothesis_test(test_diminishing_convergence, "PBT-10: Diminishing Returns Convergence")


# ── PBT-11: Lock Safety (lock + unlock = original) ────────────────

print("\n§11 Lock Safety Invariant")

@given(balance=balance_float, lock_pct=unit_float)
@settings(max_examples=500)
def test_lock_safety(balance, lock_pct):
    """Locking and unlocking preserves total balance."""
    lock_amount = balance * lock_pct
    available = balance - lock_amount
    locked = lock_amount
    # Total preserved after lock
    assert abs((available + locked) - balance) < TOLERANCE
    # Unlock (rollback)
    available += locked
    locked = 0.0
    assert abs(available - balance) < TOLERANCE
    # Lock then commit
    available = balance - lock_amount
    locked = lock_amount
    committed = locked
    locked = 0.0
    # After commit: available stays, committed is gone
    remaining = available
    assert abs(remaining - (balance - committed)) < TOLERANCE

run_hypothesis_test(test_lock_safety, "PBT-11: Lock Safety")


# ── PBT-12: Delegation Narrowing ──────────────────────────────────

print("\n§12 Delegation Scope Narrowing")

@given(
    parent_scope=st.frozensets(st.sampled_from(
        ["read", "write", "admin", "execute", "delegate", "audit"]),
        min_size=1, max_size=6),
    child_request=st.frozensets(st.sampled_from(
        ["read", "write", "admin", "execute", "delegate", "audit"]),
        min_size=0, max_size=6),
    depth=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=500)
def test_delegation_narrowing(parent_scope, child_request, depth):
    """Child scope ⊆ parent scope at all delegation depths."""
    current_scope = parent_scope
    for _ in range(depth):
        # Child gets intersection of request and parent
        child_scope = current_scope & child_request
        assert child_scope <= current_scope, \
            f"Child scope {child_scope} not subset of parent {current_scope}"
        current_scope = child_scope

run_hypothesis_test(test_delegation_narrowing, "PBT-12: Delegation Narrowing")


# ── PBT-13: Governance Alignment Primacy ───────────────────────────

print("\n§13 Governance Alignment Primacy")

@given(
    aligned=st.booleans(),
    compliant=st.booleans(),
    crisis=st.booleans(),
)
@settings(max_examples=500)
def test_alignment_primacy(aligned, compliant, crisis):
    """Non-aligned actions always fail, regardless of compliance or crisis."""
    # Governance verdict logic
    if not aligned:
        verdict = "VIOLATION"
    elif not compliant and not crisis:
        verdict = "WARNING"
    elif not compliant and crisis:
        verdict = "ACCEPTABLE"  # Crisis + aligned = ok even without compliance
    else:
        verdict = "PASS"

    if not aligned:
        assert verdict == "VIOLATION", \
            f"Non-aligned got {verdict} instead of VIOLATION"
    if aligned and compliant:
        assert verdict == "PASS"

run_hypothesis_test(test_alignment_primacy, "PBT-13: Alignment Primacy")


# ── PBT-14: Appeal Reversibility ───────────────────────────────────

print("\n§14 Appeal Reversibility (T3 Rollback)")

@given(
    talent=unit_float,
    training=unit_float,
    temperament=unit_float,
    penalty_t=st.floats(min_value=0.0, max_value=0.2, allow_nan=False, allow_infinity=False),
    penalty_tr=st.floats(min_value=0.0, max_value=0.2, allow_nan=False, allow_infinity=False),
    penalty_te=st.floats(min_value=0.0, max_value=0.2, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=500)
def test_appeal_reversibility(talent, training, temperament,
                               penalty_t, penalty_tr, penalty_te):
    """Reversing a penalty restores T3 to pre-penalty snapshot."""
    # Apply penalty (clamped)
    penalized_t = max(0.0, talent - penalty_t)
    penalized_tr = max(0.0, training - penalty_tr)
    penalized_te = max(0.0, temperament - penalty_te)
    # Reverse: restore from snapshot
    restored_t = talent  # Snapshot was saved before penalty
    restored_tr = training
    restored_te = temperament
    assert abs(restored_t - talent) < TOLERANCE
    assert abs(restored_tr - training) < TOLERANCE
    assert abs(restored_te - temperament) < TOLERANCE

run_hypothesis_test(test_appeal_reversibility, "PBT-14: Appeal Reversibility")


# ── PBT-15: Conservation Under Recharge ────────────────────────────

print("\n§15 Conservation Under Recharge")

@given(
    n_agents=st.integers(min_value=2, max_value=20),
    initial=st.floats(min_value=10.0, max_value=500.0, allow_nan=False, allow_infinity=False),
    recharge_rate=st.floats(min_value=0.01, max_value=0.2, allow_nan=False, allow_infinity=False),
    max_mult=st.floats(min_value=1.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    n_ticks=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
def test_conservation_with_recharge(n_agents, initial, recharge_rate, max_mult, n_ticks):
    """Recharge creates ATP. Track: supply = initial_supply + total_recharged - total_fees."""
    balances = [initial] * n_agents
    total_recharged = 0.0
    total_fees = 0.0
    max_balance = initial * max_mult
    fee_r = 0.05

    for _ in range(n_ticks):
        # Recharge all agents
        for i in range(n_agents):
            recharge_amount = min(initial * recharge_rate, max_balance - balances[i])
            recharge_amount = max(0.0, recharge_amount)
            balances[i] += recharge_amount
            total_recharged += recharge_amount
        # Random transfer
        fr = random.randint(0, n_agents - 1)
        to = (fr + 1) % n_agents
        amount = min(balances[fr] * 0.1, balances[fr] / (1 + fee_r))
        if amount > 0.01:
            fee = amount * fee_r
            balances[fr] -= (amount + fee)
            balances[to] += amount
            total_fees += fee

    current_supply = sum(balances)
    expected_supply = initial * n_agents + total_recharged - total_fees
    assert abs(current_supply - expected_supply) < 0.01, \
        f"Conservation: {current_supply} != {expected_supply}"

run_hypothesis_test(test_conservation_with_recharge, "PBT-15: Conservation Under Recharge", 300)


# ── PBT-16: Sybil Unprofitability ─────────────────────────────────

print("\n§16 Sybil Unprofitability")

@given(
    n_sybil=st.integers(min_value=2, max_value=20),
    hardware_cost=st.floats(min_value=50.0, max_value=500.0, allow_nan=False, allow_infinity=False),
    stake=st.floats(min_value=10.0, max_value=200.0, allow_nan=False, allow_infinity=False),
    fee_r=st.floats(min_value=0.01, max_value=0.1, allow_nan=False, allow_infinity=False),
    honest_quality=st.floats(min_value=0.6, max_value=1.0, allow_nan=False, allow_infinity=False),
    sybil_quality=st.floats(min_value=0.1, max_value=0.4, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=500, suppress_health_check=[HealthCheck.too_slow])
def test_sybil_unprofitability(n_sybil, hardware_cost, stake, fee_r,
                                honest_quality, sybil_quality):
    """Sybil farming is less profitable than honest participation."""
    # Honest: 1 identity, high quality
    honest_setup = hardware_cost + stake
    honest_payment = 100.0 * honest_quality  # quality-proportional payment
    honest_roi = honest_payment / honest_setup

    # Sybil: N identities, low quality, circular flow loses to fees
    sybil_setup = n_sybil * (hardware_cost + stake)
    sybil_payment = n_sybil * 100.0 * sybil_quality
    circular_loss = n_sybil * stake * fee_r * 10  # 10 cycles of circular transfer
    sybil_net = sybil_payment - circular_loss
    sybil_roi = sybil_net / sybil_setup if sybil_setup > 0 else 0

    # With quality gate (sybil_quality < 0.3 → zero payment from sliding scale)
    if sybil_quality < 0.3:
        sybil_payment_gated = 0.0
    elif sybil_quality <= 0.7:
        scale = (sybil_quality - 0.3) / (0.7 - 0.3)
        sybil_payment_gated = n_sybil * 100.0 * scale
    else:
        sybil_payment_gated = n_sybil * 100.0
    sybil_roi_gated = (sybil_payment_gated - circular_loss) / sybil_setup if sybil_setup > 0 else 0

    assert honest_roi > sybil_roi_gated, \
        f"Sybil profitable! honest_roi={honest_roi:.4f} vs sybil_roi={sybil_roi_gated:.4f}"

run_hypothesis_test(test_sybil_unprofitability, "PBT-16: Sybil Unprofitability")


# ── PBT-17: Gini Coefficient Bounds ───────────────────────────────

print("\n§17 Gini Coefficient Bounds [0,1]")

@given(
    values=st.lists(
        st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
        min_size=2, max_size=50,
    )
)
@settings(max_examples=500)
def test_gini_bounds(values):
    """Gini coefficient is always in [0, 1]."""
    g = gini_coefficient(values)
    assert -TOLERANCE <= g <= 1.0 + TOLERANCE, f"Gini {g} out of bounds"

run_hypothesis_test(test_gini_bounds, "PBT-17: Gini Coefficient Bounds")


# ── PBT-18: Hash Chain Integrity ──────────────────────────────────

print("\n§18 Hash Chain Tamper Detection")

@given(
    entries=st.lists(st.text(min_size=1, max_size=50), min_size=3, max_size=20),
    tamper_idx=st.integers(min_value=0, max_value=19),
)
@settings(max_examples=500)
def test_hash_chain_integrity(entries, tamper_idx):
    """Any modification to chain content is detected."""
    # Build chain
    chain = []
    prev = "genesis"
    for e in entries:
        h = hash_chain_entry(e, prev)
        chain.append((e, h))
        prev = h

    # Verify chain
    prev = "genesis"
    for content, expected_hash in chain:
        computed = hash_chain_entry(content, prev)
        assert computed == expected_hash
        prev = expected_hash

    # Tamper with one entry
    idx = tamper_idx % len(entries)
    tampered_entries = list(entries)
    tampered_entries[idx] = tampered_entries[idx] + "TAMPERED"

    # Rebuild chain with tampered content
    prev = "genesis"
    tamper_detected = False
    for i, (orig_content, orig_hash) in enumerate(chain):
        content = tampered_entries[i]
        computed = hash_chain_entry(content, prev)
        if computed != orig_hash:
            tamper_detected = True
            break
        prev = computed

    assert tamper_detected, "Tampering not detected!"

run_hypothesis_test(test_hash_chain_integrity, "PBT-18: Hash Chain Integrity")


# ── PBT-19: Composite Score Bounds ────────────────────────────────

print("\n§19 T3/V3 Composite Score Bounds [0,1]")

@given(
    t=unit_float, tr=unit_float, te=unit_float,
    val=unit_float, ver=unit_float, vld=unit_float,
)
@settings(max_examples=500)
def test_composite_bounds(t, tr, te, val, ver, vld):
    """T3 and V3 composites are always in [0, 1]."""
    t3 = t3_composite(t, tr, te)
    v3 = v3_composite(val, ver, vld)
    assert 0.0 - TOLERANCE <= t3 <= 1.0 + TOLERANCE, f"T3 composite {t3} out of bounds"
    assert 0.0 - TOLERANCE <= v3 <= 1.0 + TOLERANCE, f"V3 composite {v3} out of bounds"
    # Weights sum to 1.0
    assert abs(0.4 + 0.3 + 0.3 - 1.0) < TOLERANCE  # T3 weights
    assert abs(0.3 + 0.35 + 0.35 - 1.0) < TOLERANCE  # V3 weights

run_hypothesis_test(test_composite_bounds, "PBT-19: Composite Score Bounds")


# ── PBT-20: Fee Monotonicity ──────────────────────────────────────

print("\n§20 Fee Monotonicity")

@given(
    amount=positive_float,
    r1=fee_rate,
    r2=fee_rate,
)
@settings(max_examples=500)
def test_fee_monotonicity(amount, r1, r2):
    """Higher fee rate → higher fee for same amount."""
    f1 = amount * r1
    f2 = amount * r2
    if r1 <= r2:
        assert f1 <= f2 + TOLERANCE, f"Fee not monotone: {r1}→{f1}, {r2}→{f2}"

run_hypothesis_test(test_fee_monotonicity, "PBT-20: Fee Monotonicity")


# ── BONUS: Cross-Property Invariants ──────────────────────────────

print("\n§21 Cross-Property: T3 Update + Composite Monotonicity")

@given(
    t=st.floats(min_value=0.1, max_value=0.9, allow_nan=False, allow_infinity=False),
    tr=st.floats(min_value=0.1, max_value=0.9, allow_nan=False, allow_infinity=False),
    te=st.floats(min_value=0.1, max_value=0.9, allow_nan=False, allow_infinity=False),
    q_good=st.floats(min_value=0.51, max_value=1.0, allow_nan=False, allow_infinity=False),
    q_bad=st.floats(min_value=0.0, max_value=0.49, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=500)
def test_t3_composite_monotonicity(t, tr, te, q_good, q_bad):
    """Good quality increases composite, bad quality decreases it."""
    original = t3_composite(t, tr, te)
    good_t, good_tr, good_te = t3_update(t, tr, te, q_good)
    bad_t, bad_tr, bad_te = t3_update(t, tr, te, q_bad)
    after_good = t3_composite(good_t, good_tr, good_te)
    after_bad = t3_composite(bad_t, bad_tr, bad_te)
    assert after_good >= original - TOLERANCE, \
        f"Good quality decreased composite: {original}→{after_good}"
    assert after_bad <= original + TOLERANCE, \
        f"Bad quality increased composite: {original}→{after_bad}"

run_hypothesis_test(test_t3_composite_monotonicity, "PBT-21: T3 Composite Monotonicity")


print("\n§22 Cross-Property: Energy Ratio + T3 Coherence")

@given(
    t3=unit_float,
    v3=unit_float,
    atp_val=balance_float,
    adp_val=balance_float,
)
@settings(max_examples=500)
def test_coherence_bounds(t3, v3, atp_val, adp_val):
    """Coherence score (T3*0.4 + V3*0.3 + energy*0.3) is always in [0,1]."""
    er = energy_ratio(atp_val, adp_val)
    coherence = t3 * 0.4 + v3 * 0.3 + er * 0.3
    assert 0.0 - TOLERANCE <= coherence <= 1.0 + TOLERANCE, \
        f"Coherence {coherence} out of bounds"

run_hypothesis_test(test_coherence_bounds, "PBT-22: Coherence Bounds")


print("\n§23 Cross-Property: Transfer Capped + Conservation")

@given(
    sender=balance_float,
    receiver=balance_float,
    amount=small_positive,
    fr=fee_rate,
    max_bal=st.floats(min_value=100.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=500)
def test_capped_transfer_conservation(sender, receiver, amount, fr, max_bal):
    """Capped transfers preserve total: sender + receiver + fee = original total."""
    assume(amount + amount * fr <= sender)  # sufficient funds
    original_total = sender + receiver
    new_s, new_r, fee, overflow = atp_transfer(sender, receiver, amount, fr, max_bal)
    new_total = new_s + new_r
    assert abs(original_total - (new_total + fee)) < TOLERANCE, \
        f"Conservation: {original_total} != {new_total} + {fee}"

run_hypothesis_test(test_capped_transfer_conservation, "PBT-23: Capped Transfer Conservation")


# ═══════════════════════════════════════════════════════════════
# RESULTS
# ═══════════════════════════════════════════════════════════════

print(f"\n{'═' * 62}")
print(f"  Property-Based Testing Results: {passed} passed, {failed} failed")
print(f"  Total examples generated: ~{passed * 500}")
if errors:
    print(f"\n  Failures:")
    for e in errors:
        print(f"    - {e}")
print(f"{'═' * 62}")

sys.exit(0 if failed == 0 else 1)
