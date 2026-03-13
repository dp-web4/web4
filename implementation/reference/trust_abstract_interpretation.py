"""
Trust Abstract Interpretation for Web4
Session 34, Track 4

Abstract interpretation for static analysis of trust properties:
- Interval domain [lo, hi] for trust score ranges
- Sign domain {neg, zero, pos} for trust deltas
- Widening and narrowing operators for convergence
- Abstract transfer functions for trust operations
- Fixed-point computation on abstract domain
- Over-approximation soundness verification
- Trust property verification (boundedness, monotonicity)
- Abstract trust program analysis
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Set
from enum import Enum, auto


# ─── Interval Domain ────────────────────────────────────────────

@dataclass
class Interval:
    """Abstract interval [lo, hi] for trust scores."""
    lo: float
    hi: float

    @staticmethod
    def bottom() -> 'Interval':
        """Empty interval (unreachable)."""
        return Interval(float('inf'), float('-inf'))

    @staticmethod
    def top() -> 'Interval':
        """Full interval [-inf, inf]."""
        return Interval(float('-inf'), float('inf'))

    @staticmethod
    def point(v: float) -> 'Interval':
        return Interval(v, v)

    @staticmethod
    def trust_range() -> 'Interval':
        """Standard trust interval [0, 1]."""
        return Interval(0.0, 1.0)

    @property
    def is_bottom(self) -> bool:
        return self.lo > self.hi

    @property
    def is_point(self) -> bool:
        return not self.is_bottom and self.lo == self.hi

    @property
    def width(self) -> float:
        if self.is_bottom:
            return 0.0
        return self.hi - self.lo

    def contains(self, value: float) -> bool:
        return self.lo <= value <= self.hi

    def __repr__(self):
        if self.is_bottom:
            return "⊥"
        return f"[{self.lo:.3f}, {self.hi:.3f}]"


def interval_join(a: Interval, b: Interval) -> Interval:
    """Least upper bound: smallest interval containing both."""
    if a.is_bottom:
        return b
    if b.is_bottom:
        return a
    return Interval(min(a.lo, b.lo), max(a.hi, b.hi))


def interval_meet(a: Interval, b: Interval) -> Interval:
    """Greatest lower bound: intersection."""
    if a.is_bottom or b.is_bottom:
        return Interval.bottom()
    lo = max(a.lo, b.lo)
    hi = min(a.hi, b.hi)
    if lo > hi:
        return Interval.bottom()
    return Interval(lo, hi)


def interval_add(a: Interval, b: Interval) -> Interval:
    """Abstract addition."""
    if a.is_bottom or b.is_bottom:
        return Interval.bottom()
    return Interval(a.lo + b.lo, a.hi + b.hi)


def interval_mul(a: Interval, b: Interval) -> Interval:
    """Abstract multiplication (for trust composition)."""
    if a.is_bottom or b.is_bottom:
        return Interval.bottom()
    products = [a.lo * b.lo, a.lo * b.hi, a.hi * b.lo, a.hi * b.hi]
    return Interval(min(products), max(products))


def interval_widen(a: Interval, b: Interval) -> Interval:
    """
    Widening operator for convergence guarantee.
    If b exceeds a on any side, push to infinity.
    """
    if a.is_bottom:
        return b
    if b.is_bottom:
        return a
    lo = a.lo if b.lo >= a.lo else float('-inf')
    hi = a.hi if b.hi <= a.hi else float('inf')
    return Interval(lo, hi)


def interval_narrow(a: Interval, b: Interval) -> Interval:
    """
    Narrowing operator: refine an over-approximation.
    Replace infinities with finite bounds from b.
    """
    if a.is_bottom:
        return Interval.bottom()
    if b.is_bottom:
        return Interval.bottom()
    lo = b.lo if a.lo == float('-inf') else a.lo
    hi = b.hi if a.hi == float('inf') else a.hi
    return Interval(lo, hi)


def interval_clamp(a: Interval, lo: float, hi: float) -> Interval:
    """Clamp interval to [lo, hi] (trust bounds)."""
    if a.is_bottom:
        return Interval.bottom()
    return Interval(max(a.lo, lo), min(a.hi, hi))


# ─── Sign Domain ─────────────────────────────────────────────────

class Sign(Enum):
    BOTTOM = auto()    # unreachable
    NEG = auto()       # negative
    ZERO = auto()      # zero
    POS = auto()       # positive
    TOP = auto()       # unknown


def sign_of(v: float) -> Sign:
    if v < 0:
        return Sign.NEG
    elif v > 0:
        return Sign.POS
    else:
        return Sign.ZERO


def sign_join(a: Sign, b: Sign) -> Sign:
    if a == Sign.BOTTOM:
        return b
    if b == Sign.BOTTOM:
        return a
    if a == b:
        return a
    return Sign.TOP


def sign_add(a: Sign, b: Sign) -> Sign:
    if a == Sign.BOTTOM or b == Sign.BOTTOM:
        return Sign.BOTTOM
    if a == Sign.TOP or b == Sign.TOP:
        return Sign.TOP
    if a == Sign.ZERO:
        return b
    if b == Sign.ZERO:
        return a
    if a == b:
        return a  # pos+pos=pos, neg+neg=neg
    return Sign.TOP  # pos+neg = unknown


def sign_mul(a: Sign, b: Sign) -> Sign:
    if a == Sign.BOTTOM or b == Sign.BOTTOM:
        return Sign.BOTTOM
    if a == Sign.ZERO or b == Sign.ZERO:
        return Sign.ZERO
    if a == Sign.TOP or b == Sign.TOP:
        return Sign.TOP
    if a == b:
        return Sign.POS  # neg*neg=pos, pos*pos=pos
    return Sign.NEG  # pos*neg=neg


# ─── Abstract Trust Transfer Functions ──────────────────────────

def abstract_trust_attenuation(trust: Interval, factor: Interval) -> Interval:
    """Trust attenuation: new_trust = trust * factor, clamped to [0,1]."""
    result = interval_mul(trust, factor)
    return interval_clamp(result, 0.0, 1.0)


def abstract_trust_boost(trust: Interval, boost: Interval) -> Interval:
    """Trust boost: new_trust = trust + boost, clamped to [0,1]."""
    result = interval_add(trust, boost)
    return interval_clamp(result, 0.0, 1.0)


def abstract_trust_decay(trust: Interval, decay_rate: Interval) -> Interval:
    """Trust decay: new_trust = trust * (1 - decay_rate)."""
    one_minus = Interval(1.0 - decay_rate.hi, 1.0 - decay_rate.lo)
    result = interval_mul(trust, one_minus)
    return interval_clamp(result, 0.0, 1.0)


# ─── Abstract Program Analysis ──────────────────────────────────

@dataclass
class AbstractState:
    """Map from variable names to abstract intervals."""
    vars: Dict[str, Interval]

    def __getitem__(self, name: str) -> Interval:
        return self.vars.get(name, Interval.bottom())

    def __setitem__(self, name: str, val: Interval):
        self.vars[name] = val

    def copy(self) -> 'AbstractState':
        return AbstractState(dict(self.vars))

    def join(self, other: 'AbstractState') -> 'AbstractState':
        all_vars = set(self.vars.keys()) | set(other.vars.keys())
        result = {}
        for v in all_vars:
            result[v] = interval_join(
                self.vars.get(v, Interval.bottom()),
                other.vars.get(v, Interval.bottom())
            )
        return AbstractState(result)


def analyze_trust_program(statements: List[Tuple],
                           initial: AbstractState,
                           iterations: int = 10) -> AbstractState:
    """
    Simple abstract interpreter for trust programs.

    Statements:
    - ("assign", var, value_interval)
    - ("attenuate", var, factor_interval)
    - ("boost", var, boost_interval)
    - ("decay", var, rate_interval)
    - ("assert_bound", var, lo, hi)  — check property
    """
    state = initial.copy()

    for stmt in statements:
        if stmt[0] == "assign":
            _, var, val = stmt
            state[var] = val

        elif stmt[0] == "attenuate":
            _, var, factor = stmt
            state[var] = abstract_trust_attenuation(state[var], factor)

        elif stmt[0] == "boost":
            _, var, boost = stmt
            state[var] = abstract_trust_boost(state[var], boost)

        elif stmt[0] == "decay":
            _, var, rate = stmt
            state[var] = abstract_trust_decay(state[var], rate)

    return state


def verify_trust_property(state: AbstractState, var: str,
                           lo: float, hi: float) -> bool:
    """Verify that abstract value is within [lo, hi]."""
    val = state[var]
    if val.is_bottom:
        return True  # vacuously true
    return val.lo >= lo - 1e-9 and val.hi <= hi + 1e-9


# ─── Fixed-Point Computation ────────────────────────────────────

def fixed_point_widening(transfer_fn, initial: Interval,
                          max_iterations: int = 50) -> Interval:
    """
    Compute fixed point using widening for convergence.
    transfer_fn: Interval -> Interval
    """
    current = initial
    for _ in range(max_iterations):
        next_val = transfer_fn(current)
        widened = interval_widen(current, next_val)
        if widened.lo == current.lo and widened.hi == current.hi:
            break  # Converged
        current = widened
    return current


def fixed_point_with_narrowing(transfer_fn, initial: Interval,
                                 max_widen: int = 20,
                                 max_narrow: int = 20) -> Interval:
    """
    Compute fixed point with widening then narrowing for precision.
    """
    # Phase 1: Widen to convergence
    current = fixed_point_widening(transfer_fn, initial, max_widen)

    # Phase 2: Narrow for precision
    for _ in range(max_narrow):
        next_val = transfer_fn(current)
        narrowed = interval_narrow(current, next_val)
        if narrowed.lo == current.lo and narrowed.hi == current.hi:
            break
        current = narrowed

    return current


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
    print("Trust Abstract Interpretation for Web4")
    print("Session 34, Track 4")
    print("=" * 70)

    # ── §1 Interval Domain ──────────────────────────────────────
    print("\n§1 Interval Domain\n")

    a = Interval(0.2, 0.8)
    check("contains_mid", a.contains(0.5))
    check("contains_lo", a.contains(0.2))
    check("not_contains_below", not a.contains(0.1))
    check("width", abs(a.width - 0.6) < 1e-9)

    b = Interval.bottom()
    check("bottom_is_bottom", b.is_bottom)
    check("point_is_point", Interval.point(0.5).is_point)

    # ── §2 Interval Operations ───────────────────────────────────
    print("\n§2 Interval Operations\n")

    j = interval_join(Interval(0.2, 0.5), Interval(0.4, 0.8))
    check("join_lo", abs(j.lo - 0.2) < 1e-9)
    check("join_hi", abs(j.hi - 0.8) < 1e-9)

    m = interval_meet(Interval(0.2, 0.5), Interval(0.4, 0.8))
    check("meet_lo", abs(m.lo - 0.4) < 1e-9)
    check("meet_hi", abs(m.hi - 0.5) < 1e-9)

    empty = interval_meet(Interval(0.0, 0.3), Interval(0.5, 1.0))
    check("empty_meet", empty.is_bottom)

    s = interval_add(Interval(0.1, 0.3), Interval(0.2, 0.4))
    check("add_lo", abs(s.lo - 0.3) < 1e-9)
    check("add_hi", abs(s.hi - 0.7) < 1e-9)

    p = interval_mul(Interval(0.5, 0.8), Interval(0.6, 0.9))
    check("mul_lo", abs(p.lo - 0.3) < 1e-9)
    check("mul_hi", abs(p.hi - 0.72) < 1e-9)

    # ── §3 Widening ──────────────────────────────────────────────
    print("\n§3 Widening and Narrowing\n")

    w = interval_widen(Interval(0.0, 1.0), Interval(-0.1, 1.0))
    check("widen_lo_to_inf", w.lo == float('-inf'))
    check("widen_hi_stable", w.hi == 1.0)

    w2 = interval_widen(Interval(0.0, 1.0), Interval(0.0, 1.5))
    check("widen_hi_to_inf", w2.hi == float('inf'))
    check("widen_lo_stable", w2.lo == 0.0)

    # Narrowing: refine infinities
    n = interval_narrow(Interval(float('-inf'), float('inf')), Interval(0.0, 1.0))
    check("narrow_lo", abs(n.lo - 0.0) < 1e-9)
    check("narrow_hi", abs(n.hi - 1.0) < 1e-9)

    # ── §4 Sign Domain ──────────────────────────────────────────
    print("\n§4 Sign Domain\n")

    check("sign_pos", sign_of(0.5) == Sign.POS)
    check("sign_neg", sign_of(-0.3) == Sign.NEG)
    check("sign_zero", sign_of(0.0) == Sign.ZERO)

    check("sign_add_pp", sign_add(Sign.POS, Sign.POS) == Sign.POS)
    check("sign_add_nn", sign_add(Sign.NEG, Sign.NEG) == Sign.NEG)
    check("sign_add_pn", sign_add(Sign.POS, Sign.NEG) == Sign.TOP)

    check("sign_mul_pp", sign_mul(Sign.POS, Sign.POS) == Sign.POS)
    check("sign_mul_nn", sign_mul(Sign.NEG, Sign.NEG) == Sign.POS)
    check("sign_mul_pn", sign_mul(Sign.POS, Sign.NEG) == Sign.NEG)
    check("sign_mul_z", sign_mul(Sign.POS, Sign.ZERO) == Sign.ZERO)

    # ── §5 Trust Transfer Functions ──────────────────────────────
    print("\n§5 Trust Transfer Functions\n")

    trust = Interval(0.6, 0.9)
    factor = Interval(0.7, 0.8)
    attenuated = abstract_trust_attenuation(trust, factor)
    check("attenuate_bounded", attenuated.lo >= 0.0 and attenuated.hi <= 1.0)
    check("attenuate_lo", abs(attenuated.lo - 0.42) < 1e-9, f"lo={attenuated.lo}")
    check("attenuate_hi", abs(attenuated.hi - 0.72) < 1e-9, f"hi={attenuated.hi}")

    boosted = abstract_trust_boost(trust, Interval(0.1, 0.2))
    check("boost_bounded", boosted.lo >= 0.0 and boosted.hi <= 1.0)
    check("boost_hi_clamped", boosted.hi <= 1.0)

    decayed = abstract_trust_decay(trust, Interval(0.1, 0.2))
    check("decay_reduces", decayed.hi <= trust.hi)
    check("decay_bounded", decayed.lo >= 0.0)

    # ── §6 Abstract Program Analysis ────────────────────────────
    print("\n§6 Abstract Program Analysis\n")

    initial = AbstractState({"trust_a": Interval(0.5, 0.8)})
    program = [
        ("attenuate", "trust_a", Interval(0.9, 0.95)),
        ("boost", "trust_a", Interval(0.05, 0.1)),
    ]
    final = analyze_trust_program(program, initial)
    check("program_result_bounded", verify_trust_property(final, "trust_a", 0.0, 1.0))

    # Assign then decay
    initial2 = AbstractState({"score": Interval.trust_range()})
    program2 = [
        ("assign", "score", Interval(0.9, 1.0)),
        ("decay", "score", Interval(0.05, 0.1)),
    ]
    final2 = analyze_trust_program(program2, initial2)
    check("decay_from_high", final2["score"].hi < 1.0)
    check("decay_result", verify_trust_property(final2, "score", 0.0, 1.0))

    # ── §7 Fixed Point ───────────────────────────────────────────
    print("\n§7 Fixed-Point Computation\n")

    # Trust decay: x = x * 0.9 + 0.05  → fixed point = 0.5
    def transfer(x: Interval) -> Interval:
        decayed = interval_mul(x, Interval(0.9, 0.9))
        boosted = interval_add(decayed, Interval(0.05, 0.05))
        return interval_clamp(boosted, 0.0, 1.0)

    fp = fixed_point_widening(transfer, Interval(0.5, 0.5))
    check("fixed_point_converges", not fp.is_bottom)
    # Analytical fixed point: x = 0.9x + 0.05 → x = 0.5
    check("fixed_point_contains_analytical", fp.contains(0.5),
          f"fp={fp}")

    fp2 = fixed_point_with_narrowing(transfer, Interval(0.5, 0.5))
    check("narrowed_tighter", fp2.width <= fp.width + 1e-9,
          f"widened={fp.width:.3f}, narrowed={fp2.width:.3f}")

    # ── §8 Soundness ─────────────────────────────────────────────
    print("\n§8 Soundness Verification\n")

    # Over-approximation: concrete values always within abstract
    concrete_values = [0.3, 0.5, 0.7]
    abstract = Interval(0.2, 0.8)
    check("sound_all_contained", all(abstract.contains(v) for v in concrete_values))

    # Abstract multiplication is sound
    a_abs = Interval(0.4, 0.6)
    b_abs = Interval(0.7, 0.9)
    result_abs = interval_mul(a_abs, b_abs)

    # Check all corner products
    for av in [0.4, 0.5, 0.6]:
        for bv in [0.7, 0.8, 0.9]:
            check(f"mul_sound_{av}_{bv}",
                  result_abs.contains(av * bv),
                  f"{av}*{bv}={av*bv}, result={result_abs}")

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
