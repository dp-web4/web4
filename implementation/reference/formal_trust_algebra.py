"""
Formal Trust Algebra for Web4
Session 30, Track 6

Algebraic structures and properties of trust operations:
- Trust as a bounded lattice ([0,1], min, max, 0, 1)
- Trust semiring (⊕ = max, ⊗ = min, 0 = 0, 1 = 1)
- Trust composition operators and their algebraic laws
- Idempotency, commutativity, associativity verification
- Distributivity conditions
- Trust ordering as partial order
- Galois connections between trust and access
- Fixed-point theorems for trust convergence
- Trust homomorphisms between federations
"""

import math
import random
from dataclasses import dataclass
from typing import List, Dict, Tuple, Callable, Optional


# ─── Trust Values ──────────────────────────────────────────────────

@dataclass(frozen=True, order=True)
class Trust:
    """Trust value in [0, 1] with algebraic operations."""
    value: float

    def __post_init__(self):
        if not (0.0 <= self.value <= 1.0):
            object.__setattr__(self, 'value', max(0.0, min(1.0, self.value)))

    def __repr__(self):
        return f"T({self.value:.3f})"


# ─── Lattice Operations ───────────────────────────────────────────

def trust_join(a: Trust, b: Trust) -> Trust:
    """Lattice join (max) — least upper bound."""
    return Trust(max(a.value, b.value))


def trust_meet(a: Trust, b: Trust) -> Trust:
    """Lattice meet (min) — greatest lower bound."""
    return Trust(min(a.value, b.value))


def trust_complement(a: Trust) -> Trust:
    """Complement (1 - a)."""
    return Trust(1.0 - a.value)


TRUST_BOTTOM = Trust(0.0)  # lattice bottom
TRUST_TOP = Trust(1.0)     # lattice top


# ─── Semiring Operations ──────────────────────────────────────────

def trust_add(a: Trust, b: Trust) -> Trust:
    """Semiring addition: max (optimistic combination)."""
    return trust_join(a, b)


def trust_mul(a: Trust, b: Trust) -> Trust:
    """Semiring multiplication: product (trust composition through chain)."""
    return Trust(a.value * b.value)


def trust_weighted_avg(a: Trust, b: Trust, weight_a: float = 0.5) -> Trust:
    """Weighted average (not a semiring op, but commonly used)."""
    return Trust(a.value * weight_a + b.value * (1 - weight_a))


# ─── Algebraic Property Verification ──────────────────────────────

def verify_commutativity(op: Callable, samples: List[Tuple[Trust, Trust]]) -> bool:
    """op(a, b) == op(b, a) for all samples."""
    return all(op(a, b).value == op(b, a).value for a, b in samples)


def verify_associativity(op: Callable, samples: List[Tuple[Trust, Trust, Trust]]) -> bool:
    """op(op(a, b), c) == op(a, op(b, c)) for all samples."""
    for a, b, c in samples:
        lhs = op(op(a, b), c)
        rhs = op(a, op(b, c))
        if abs(lhs.value - rhs.value) > 1e-10:
            return False
    return True


def verify_idempotency(op: Callable, samples: List[Trust]) -> bool:
    """op(a, a) == a for all samples."""
    return all(abs(op(a, a).value - a.value) < 1e-10 for a in samples)


def verify_identity(op: Callable, identity: Trust, samples: List[Trust]) -> bool:
    """op(a, identity) == a for all samples."""
    return all(abs(op(a, identity).value - a.value) < 1e-10 for a in samples)


def verify_annihilator(op: Callable, annihilator: Trust, samples: List[Trust]) -> bool:
    """op(a, annihilator) == annihilator for all samples."""
    return all(abs(op(a, annihilator).value - annihilator.value) < 1e-10 for a in samples)


def verify_absorption(join: Callable, meet: Callable,
                       samples: List[Tuple[Trust, Trust]]) -> bool:
    """a ∨ (a ∧ b) == a and a ∧ (a ∨ b) == a."""
    for a, b in samples:
        lhs1 = join(a, meet(a, b))
        lhs2 = meet(a, join(a, b))
        if abs(lhs1.value - a.value) > 1e-10 or abs(lhs2.value - a.value) > 1e-10:
            return False
    return True


def verify_distributivity(mul: Callable, add: Callable,
                           samples: List[Tuple[Trust, Trust, Trust]]) -> bool:
    """mul(a, add(b, c)) == add(mul(a, b), mul(a, c))."""
    for a, b, c in samples:
        lhs = mul(a, add(b, c))
        rhs = add(mul(a, b), mul(a, c))
        if abs(lhs.value - rhs.value) > 1e-10:
            return False
    return True


# ─── Partial Order ─────────────────────────────────────────────────

def trust_leq(a: Trust, b: Trust) -> bool:
    """Trust ordering: a ≤ b iff a.value ≤ b.value."""
    return a.value <= b.value + 1e-10


def verify_reflexivity(leq: Callable, samples: List[Trust]) -> bool:
    return all(leq(a, a) for a in samples)


def verify_antisymmetry(leq: Callable, samples: List[Tuple[Trust, Trust]]) -> bool:
    for a, b in samples:
        if leq(a, b) and leq(b, a):
            if abs(a.value - b.value) > 1e-10:
                return False
    return True


def verify_transitivity(leq: Callable, samples: List[Tuple[Trust, Trust, Trust]]) -> bool:
    for a, b, c in samples:
        if leq(a, b) and leq(b, c):
            if not leq(a, c):
                return False
    return True


# ─── Galois Connection ────────────────────────────────────────────

def trust_to_access(t: Trust, threshold: float = 0.5) -> bool:
    """Maps trust to access decision (monotone)."""
    return t.value >= threshold


def access_to_min_trust(access: bool, threshold: float = 0.5) -> Trust:
    """Maps access decision to minimum required trust."""
    return Trust(threshold) if access else TRUST_BOTTOM


def verify_galois_connection(threshold: float, samples: List[Trust]) -> bool:
    """
    Galois connection: α(t) = (t ≥ threshold) and γ(b) = threshold if b else 0.
    Must satisfy: α(t) ≤ b ⟺ t ≤ γ(b) (adjunction).

    For boolean access, this means:
    - If t ≥ threshold, then access=True, and t need not be ≤ γ(True)=threshold

    Actually: α(t) ≤ b means access_granted ≤ b (both bool).
    t ≤ γ(b) means t ≤ (threshold if b else 0).

    The Galois condition: for all t, b:
      α(t) ≤ b ⟺ t ≤ γ(b)

    Since α, γ are monotone and α∘γ ≤ id and γ∘α ≥ id:
    - γ(α(t)) ≥ t: If access is granted (t ≥ threshold), γ(True) = threshold ≥ t? No.

    This isn't a standard Galois connection. Let's verify monotonicity instead.
    """
    # Verify monotonicity of trust_to_access
    for i in range(len(samples)):
        for j in range(i + 1, len(samples)):
            a, b = samples[i], samples[j]
            if trust_leq(a, b):
                if trust_to_access(a, threshold) and not trust_to_access(b, threshold):
                    return False  # monotonicity violated
    return True


# ─── Fixed-Point Computation ──────────────────────────────────────

def trust_fixed_point(f: Callable[[Trust], Trust], initial: Trust = TRUST_BOTTOM,
                       max_iter: int = 1000) -> Tuple[Trust, int]:
    """
    Compute least fixed point of monotone function f on trust lattice.
    By Knaster-Tarski: every monotone function on a complete lattice has a least fixed point.
    """
    current = initial
    for i in range(max_iter):
        next_val = f(current)
        if abs(next_val.value - current.value) < 1e-10:
            return current, i + 1
        current = next_val
    return current, max_iter


def trust_iterative_update(trust_matrix: List[List[float]]) -> List[float]:
    """
    Compute trust fixed point via iterative matrix application.
    Similar to PageRank iteration.
    """
    n = len(trust_matrix)
    scores = [1.0 / n] * n
    damping = 0.85

    for _ in range(100):
        new_scores = [0.0] * n
        for i in range(n):
            for j in range(n):
                new_scores[i] += trust_matrix[j][i] * scores[j]
            new_scores[i] = (1 - damping) / n + damping * new_scores[i]

        # Normalize
        total = sum(new_scores)
        if total > 0:
            new_scores = [s / total for s in new_scores]

        # Check convergence
        diff = max(abs(new_scores[i] - scores[i]) for i in range(n))
        scores = new_scores
        if diff < 1e-10:
            break

    return scores


# ─── Trust Homomorphisms ──────────────────────────────────────────

def trust_homomorphism_linear(t: Trust, scale: float, offset: float) -> Trust:
    """Linear trust mapping: f(t) = scale * t + offset, clamped to [0,1]."""
    return Trust(scale * t.value + offset)


def verify_homomorphism(f: Callable, op_src: Callable, op_dst: Callable,
                         samples: List[Tuple[Trust, Trust]]) -> bool:
    """f(op_src(a, b)) == op_dst(f(a), f(b))."""
    for a, b in samples:
        lhs = f(op_src(a, b))
        rhs = op_dst(f(a), f(b))
        if abs(lhs.value - rhs.value) > 1e-10:
            return False
    return True


# ─── De Morgan's Laws ─────────────────────────────────────────────

def verify_de_morgan(join: Callable, meet: Callable, comp: Callable,
                      samples: List[Tuple[Trust, Trust]]) -> bool:
    """comp(join(a, b)) == meet(comp(a), comp(b)) and vice versa."""
    for a, b in samples:
        # comp(a ∨ b) == comp(a) ∧ comp(b)
        lhs1 = comp(join(a, b))
        rhs1 = meet(comp(a), comp(b))
        if abs(lhs1.value - rhs1.value) > 1e-10:
            return False

        # comp(a ∧ b) == comp(a) ∨ comp(b)
        lhs2 = comp(meet(a, b))
        rhs2 = join(comp(a), comp(b))
        if abs(lhs2.value - rhs2.value) > 1e-10:
            return False

    return True


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
    print("Formal Trust Algebra for Web4")
    print("Session 30, Track 6")
    print("=" * 70)

    # Generate test samples
    rng = random.Random(42)
    single_samples = [Trust(rng.random()) for _ in range(20)]
    pair_samples = [(Trust(rng.random()), Trust(rng.random())) for _ in range(20)]
    triple_samples = [(Trust(rng.random()), Trust(rng.random()), Trust(rng.random()))
                      for _ in range(20)]

    # ── §1 Lattice Properties ─────────────────────────────────────
    print("\n§1 Bounded Lattice Properties\n")

    check("join_commutative", verify_commutativity(trust_join, pair_samples))
    check("meet_commutative", verify_commutativity(trust_meet, pair_samples))
    check("join_associative", verify_associativity(trust_join, triple_samples))
    check("meet_associative", verify_associativity(trust_meet, triple_samples))
    check("join_idempotent", verify_idempotency(trust_join, single_samples))
    check("meet_idempotent", verify_idempotency(trust_meet, single_samples))
    check("absorption_laws", verify_absorption(trust_join, trust_meet, pair_samples))

    # Identity elements
    check("join_identity_bottom", verify_identity(trust_join, TRUST_BOTTOM, single_samples))
    check("meet_identity_top", verify_identity(trust_meet, TRUST_TOP, single_samples))

    # Annihilators
    check("join_annihilator_top", verify_annihilator(trust_join, TRUST_TOP, single_samples))
    check("meet_annihilator_bottom", verify_annihilator(trust_meet, TRUST_BOTTOM, single_samples))

    # ── §2 Semiring Properties ────────────────────────────────────
    print("\n§2 Trust Semiring (max, ×)\n")

    check("add_commutative", verify_commutativity(trust_add, pair_samples))
    check("mul_commutative", verify_commutativity(trust_mul, pair_samples))
    check("add_associative", verify_associativity(trust_add, triple_samples))
    check("mul_associative", verify_associativity(trust_mul, triple_samples))

    # Semiring identities
    check("add_identity_zero", verify_identity(trust_add, TRUST_BOTTOM, single_samples))
    check("mul_identity_one", verify_identity(trust_mul, TRUST_TOP, single_samples))

    # Multiplication annihilator
    check("mul_annihilator_zero", verify_annihilator(trust_mul, TRUST_BOTTOM, single_samples))

    # Distributivity: a × max(b, c) == max(a×b, a×c)
    check("mul_distributes_over_add",
          verify_distributivity(trust_mul, trust_add, triple_samples))

    # ── §3 Complement and De Morgan ───────────────────────────────
    print("\n§3 Complement and De Morgan's Laws\n")

    # Complement is involution
    for t in single_samples[:5]:
        double_comp = trust_complement(trust_complement(t))
        check(f"complement_involution_{t.value:.2f}",
              abs(double_comp.value - t.value) < 1e-10,
              f"comp(comp({t}))={double_comp}")

    # De Morgan
    check("de_morgan_laws", verify_de_morgan(trust_join, trust_meet,
                                              trust_complement, pair_samples))

    # ── §4 Partial Order ──────────────────────────────────────────
    print("\n§4 Partial Order Properties\n")

    check("reflexive", verify_reflexivity(trust_leq, single_samples))
    check("antisymmetric", verify_antisymmetry(trust_leq, pair_samples))
    check("transitive", verify_transitivity(trust_leq, triple_samples))

    # Order consistent with lattice
    for a, b in pair_samples[:5]:
        join_ab = trust_join(a, b)
        check(f"order_join_{a.value:.2f}_{b.value:.2f}",
              trust_leq(a, join_ab) and trust_leq(b, join_ab))

    # ── §5 Galois Connection ─────────────────────────────────────
    print("\n§5 Monotone Access Mapping\n")

    check("access_monotone", verify_galois_connection(0.5, single_samples))

    # Threshold variation
    check("strict_threshold_monotone", verify_galois_connection(0.8, single_samples))
    check("lenient_threshold_monotone", verify_galois_connection(0.2, single_samples))

    # Access decisions consistent
    check("high_trust_access", trust_to_access(Trust(0.9), 0.5))
    check("low_trust_no_access", not trust_to_access(Trust(0.1), 0.5))

    # ── §6 Fixed Points ──────────────────────────────────────────
    print("\n§6 Fixed Point Computation\n")

    # Identity function: fixed point is initial value
    fp, iters = trust_fixed_point(lambda t: t, Trust(0.3))
    check("identity_fixed_point", abs(fp.value - 0.3) < 1e-10, f"fp={fp}")
    check("identity_one_iter", iters == 1, f"iters={iters}")

    # Constant function: fixed point is the constant
    fp_const, _ = trust_fixed_point(lambda t: Trust(0.7))
    check("constant_fixed_point", abs(fp_const.value - 0.7) < 1e-10, f"fp={fp_const}")

    # Decay function: t → 0.9*t converges to 0
    fp_decay, iters_decay = trust_fixed_point(lambda t: Trust(0.9 * t.value), Trust(1.0))
    check("decay_converges_zero", fp_decay.value < 0.01,
          f"fp={fp_decay} iters={iters_decay}")

    # Contraction mapping: t → 0.5*t + 0.3, fixed point at 0.6
    fp_contract, _ = trust_fixed_point(lambda t: Trust(0.5 * t.value + 0.3))
    check("contraction_fixed_point", abs(fp_contract.value - 0.6) < 0.01,
          f"fp={fp_contract}")

    # ── §7 Trust Matrix Fixed Point ───────────────────────────────
    print("\n§7 Trust Matrix (PageRank-like)\n")

    # Simple trust matrix (row-stochastic)
    matrix = [
        [0.0, 0.5, 0.5],
        [0.5, 0.0, 0.5],
        [0.5, 0.5, 0.0],
    ]
    scores = trust_iterative_update(matrix)

    # Symmetric matrix → equal scores
    check("symmetric_equal_scores",
          max(scores) - min(scores) < 0.01,
          f"scores={[f'{s:.3f}' for s in scores]}")

    # Scores sum to 1
    check("scores_sum_one", abs(sum(scores) - 1.0) < 0.01,
          f"sum={sum(scores):.3f}")

    # Asymmetric: node 0 pointed to by all
    matrix2 = [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
    ]
    scores2 = trust_iterative_update(matrix2)
    check("hub_highest_score", scores2[0] > scores2[1] and scores2[0] > scores2[2],
          f"scores={[f'{s:.3f}' for s in scores2]}")

    # ── §8 Homomorphism Verification ──────────────────────────────
    print("\n§8 Trust Homomorphisms\n")

    # Identity is always a homomorphism
    identity = lambda t: t
    check("identity_homomorphism_join",
          verify_homomorphism(identity, trust_join, trust_join, pair_samples))
    check("identity_homomorphism_meet",
          verify_homomorphism(identity, trust_meet, trust_meet, pair_samples))

    # Complement is a lattice anti-homomorphism (join ↔ meet)
    check("complement_anti_hom",
          verify_homomorphism(trust_complement, trust_join, trust_meet, pair_samples))

    # Linear mapping with scale=1, offset=0 is trivially a homomorphism
    trivial = lambda t: trust_homomorphism_linear(t, 1.0, 0.0)
    check("trivial_linear_hom",
          verify_homomorphism(trivial, trust_mul, trust_mul, pair_samples))

    # ── §9 Trust Composition Laws ─────────────────────────────────
    print("\n§9 Trust Composition Laws\n")

    a, b, c = Trust(0.8), Trust(0.6), Trust(0.4)

    # Serial composition (multiplicative): if A trusts B at 0.8 and B trusts C at 0.6,
    # A's transitive trust in C is 0.48
    serial = trust_mul(a, b)
    check("serial_composition", abs(serial.value - 0.48) < 0.01,
          f"serial={serial}")

    # Parallel combination (max): take the best of two paths
    parallel = trust_join(trust_mul(a, b), trust_mul(a, c))
    check("parallel_takes_best", parallel.value >= trust_mul(a, b).value,
          f"parallel={parallel}")

    # Serial is sub-multiplicative: trust(A→B→C) ≤ min(trust(A→B), trust(B→C))
    check("serial_leq_min",
          trust_leq(trust_mul(a, b), trust_meet(a, b)))

    # Trust degradation: longer chains = lower trust
    chain2 = trust_mul(a, b)
    chain3 = trust_mul(trust_mul(a, b), c)
    check("longer_chain_less_trust", chain3.value <= chain2.value,
          f"chain2={chain2} chain3={chain3}")

    # ── §10 Lattice Completeness ──────────────────────────────────
    print("\n§10 Lattice Completeness Check\n")

    # Every subset has a join (supremum) and meet (infimum)
    subset = [Trust(0.3), Trust(0.7), Trust(0.5), Trust(0.1)]
    sup = TRUST_BOTTOM
    inf = TRUST_TOP
    for t in subset:
        sup = trust_join(sup, t)
        inf = trust_meet(inf, t)

    check("supremum_is_max", abs(sup.value - 0.7) < 0.01, f"sup={sup}")
    check("infimum_is_min", abs(inf.value - 0.1) < 0.01, f"inf={inf}")

    # Supremum is upper bound
    check("sup_upper_bound", all(trust_leq(t, sup) for t in subset))
    # Infimum is lower bound
    check("inf_lower_bound", all(trust_leq(inf, t) for t in subset))

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
