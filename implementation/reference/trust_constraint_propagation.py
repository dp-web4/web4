"""
Trust Constraint Propagation for Web4
Session 34, Track 7

Constraint satisfaction and propagation for trust bounds:
- Variables with domains (trust score ranges)
- Binary constraints between trust values
- Arc consistency (AC-3 algorithm)
- Node consistency
- Backtracking search with constraint propagation
- Trust-specific constraints (transitivity, monotonicity, conservation)
- Constraint network visualization
- Solution enumeration and counting
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set, Callable
from collections import defaultdict, deque


# ─── Domain ──────────────────────────────────────────────────────

@dataclass
class Domain:
    """Discrete domain of possible trust values."""
    values: Set[float]

    @staticmethod
    def trust_levels(n: int = 11) -> 'Domain':
        """Standard trust levels: 0.0, 0.1, ..., 1.0"""
        return Domain({round(i / (n - 1), 2) for i in range(n)})

    @staticmethod
    def binary() -> 'Domain':
        """Binary trust: 0 or 1."""
        return Domain({0.0, 1.0})

    @staticmethod
    def from_range(lo: float, hi: float, step: float = 0.1) -> 'Domain':
        vals = set()
        v = lo
        while v <= hi + 1e-9:
            vals.add(round(v, 4))
            v += step
        return Domain(vals)

    @property
    def size(self) -> int:
        return len(self.values)

    @property
    def is_empty(self) -> bool:
        return len(self.values) == 0

    @property
    def is_singleton(self) -> bool:
        return len(self.values) == 1

    @property
    def min_val(self) -> float:
        return min(self.values) if self.values else float('inf')

    @property
    def max_val(self) -> float:
        return max(self.values) if self.values else float('-inf')

    def copy(self) -> 'Domain':
        return Domain(set(self.values))


# ─── Constraint ──────────────────────────────────────────────────

@dataclass
class Constraint:
    """A constraint between variables."""
    variables: List[str]
    predicate: Callable[..., bool]
    name: str = ""

    def is_satisfied(self, assignment: Dict[str, float]) -> bool:
        """Check if constraint is satisfied by (partial) assignment."""
        vals = [assignment.get(v) for v in self.variables]
        if any(v is None for v in vals):
            return True  # Cannot check with missing values
        return self.predicate(*vals)


# ─── Constraint Network ─────────────────────────────────────────

class ConstraintNetwork:
    """A network of trust variables with constraints."""

    def __init__(self):
        self.variables: Dict[str, Domain] = {}
        self.constraints: List[Constraint] = []
        self._var_constraints: Dict[str, List[int]] = defaultdict(list)

    def add_variable(self, name: str, domain: Domain):
        self.variables[name] = domain.copy()

    def add_constraint(self, variables: List[str],
                        predicate: Callable[..., bool],
                        name: str = ""):
        idx = len(self.constraints)
        self.constraints.append(Constraint(variables, predicate, name))
        for v in variables:
            self._var_constraints[v].append(idx)

    def is_consistent(self, assignment: Dict[str, float]) -> bool:
        """Check if assignment satisfies all constraints."""
        return all(c.is_satisfied(assignment) for c in self.constraints)

    def get_constraints_for(self, var: str) -> List[Constraint]:
        return [self.constraints[i] for i in self._var_constraints.get(var, [])]

    def domain_product_size(self) -> int:
        """Total search space size."""
        size = 1
        for d in self.variables.values():
            size *= d.size
        return size


# ─── Node Consistency ────────────────────────────────────────────

def node_consistency(network: ConstraintNetwork) -> int:
    """
    Remove values that violate unary constraints.
    Returns number of values removed.
    """
    removed = 0
    for var_name, domain in network.variables.items():
        to_remove = set()
        for val in domain.values:
            assignment = {var_name: val}
            for c in network.get_constraints_for(var_name):
                if len(c.variables) == 1 and not c.predicate(val):
                    to_remove.add(val)
                    break
        domain.values -= to_remove
        removed += len(to_remove)
    return removed


# ─── Arc Consistency (AC-3) ──────────────────────────────────────

def arc_consistency_3(network: ConstraintNetwork) -> Tuple[bool, int]:
    """
    AC-3: enforce arc consistency on all binary constraints.
    Returns (consistent, values_removed).
    """
    total_removed = 0

    # Build arc queue
    queue = deque()
    for c in network.constraints:
        if len(c.variables) == 2:
            x, y = c.variables
            queue.append((x, y, c))
            queue.append((y, x, c))

    while queue:
        xi, xj, constraint = queue.popleft()
        removed = _revise(network, xi, xj, constraint)
        total_removed += removed

        if network.variables[xi].is_empty:
            return False, total_removed

        if removed > 0:
            # Re-enqueue arcs involving xi
            for c in network.get_constraints_for(xi):
                if len(c.variables) == 2:
                    for v in c.variables:
                        if v != xi:
                            queue.append((v, xi, c))

    return True, total_removed


def _revise(network: ConstraintNetwork, xi: str, xj: str,
            constraint: Constraint) -> int:
    """Remove values from domain of xi that have no support in xj."""
    removed = 0
    domain_xi = network.variables[xi]
    domain_xj = network.variables[xj]

    to_remove = set()
    for vi in domain_xi.values:
        has_support = False
        for vj in domain_xj.values:
            assignment = {xi: vi, xj: vj}
            if constraint.is_satisfied(assignment):
                has_support = True
                break
        if not has_support:
            to_remove.add(vi)

    domain_xi.values -= to_remove
    removed = len(to_remove)
    return removed


# ─── Backtracking Search ────────────────────────────────────────

def backtracking_search(network: ConstraintNetwork,
                         max_solutions: int = 100) -> List[Dict[str, float]]:
    """
    Find all solutions using backtracking with AC-3 preprocessing.
    """
    # Run AC-3 first
    consistent, _ = arc_consistency_3(network)
    if not consistent:
        return []

    solutions = []
    var_list = list(network.variables.keys())

    def backtrack(assignment: Dict[str, float], depth: int):
        if len(solutions) >= max_solutions:
            return
        if depth == len(var_list):
            if network.is_consistent(assignment):
                solutions.append(dict(assignment))
            return

        var = var_list[depth]
        for val in sorted(network.variables[var].values):
            assignment[var] = val
            if _forward_check(network, assignment, var):
                backtrack(assignment, depth + 1)
            del assignment[var]

    backtrack({}, 0)
    return solutions


def _forward_check(network: ConstraintNetwork,
                    assignment: Dict[str, float], var: str) -> bool:
    """Check if current assignment is consistent with all assigned constraints."""
    for c in network.get_constraints_for(var):
        if all(v in assignment for v in c.variables):
            if not c.is_satisfied(assignment):
                return False
    return True


# ─── Trust-Specific Constraints ──────────────────────────────────

def transitivity_constraint(a: str, b: str, c: str) -> Constraint:
    """Trust transitivity: trust(a,c) <= trust(a,b) * trust(b,c)"""
    return Constraint(
        [a, b, c],
        lambda va, vb, vc: vc <= va * vb + 1e-9,
        f"transitivity({a},{b},{c})"
    )


def monotonicity_constraint(before: str, after: str) -> Constraint:
    """Monotonicity: after >= before (trust doesn't decrease)."""
    return Constraint(
        [before, after],
        lambda vb, va: va >= vb - 1e-9,
        f"monotone({before},{after})"
    )


def conservation_constraint(inflow: str, outflow: str) -> Constraint:
    """Conservation: inflow == outflow (ATP conservation)."""
    return Constraint(
        [inflow, outflow],
        lambda vi, vo: abs(vi - vo) < 1e-9,
        f"conservation({inflow},{outflow})"
    )


def bounded_trust_constraint(var: str, lo: float = 0.0, hi: float = 1.0) -> Constraint:
    """Trust boundedness: lo <= var <= hi."""
    return Constraint(
        [var],
        lambda v: lo - 1e-9 <= v <= hi + 1e-9,
        f"bounded({var},[{lo},{hi}])"
    )


def dominance_constraint(stronger: str, weaker: str) -> Constraint:
    """Dominance: stronger >= weaker."""
    return Constraint(
        [stronger, weaker],
        lambda vs, vw: vs >= vw - 1e-9,
        f"dominance({stronger},{weaker})"
    )


# ═══════════════════════════════════════════════════════════════
#  TESTS
# ═══════════════════════════════════════════════════════════════

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
    print("Trust Constraint Propagation for Web4")
    print("Session 34, Track 7")
    print("=" * 70)

    # ── §1 Domain ────────────────────────────────────────────────
    print("\n§1 Domain\n")

    d = Domain.trust_levels()
    check("trust_levels_11", d.size == 11)
    check("trust_levels_range", d.min_val == 0.0 and d.max_val == 1.0)
    check("trust_levels_contains", 0.5 in d.values)

    d_bin = Domain.binary()
    check("binary_size", d_bin.size == 2)

    d_range = Domain.from_range(0.2, 0.8, 0.2)
    check("range_domain", 0.4 in d_range.values)

    # ── §2 Constraints ──────────────────────────────────────────
    print("\n§2 Constraints\n")

    c1 = bounded_trust_constraint("x")
    check("bounded_satisfied", c1.is_satisfied({"x": 0.5}))
    check("bounded_violated_hi", not c1.predicate(1.5))
    check("bounded_violated_lo", not c1.predicate(-0.1))

    c2 = dominance_constraint("a", "b")
    check("dominance_sat", c2.is_satisfied({"a": 0.8, "b": 0.5}))
    check("dominance_violated", not c2.is_satisfied({"a": 0.3, "b": 0.5}))

    c3 = conservation_constraint("in", "out")
    check("conservation_sat", c3.is_satisfied({"in": 0.5, "out": 0.5}))
    check("conservation_violated", not c3.is_satisfied({"in": 0.5, "out": 0.6}))

    # ── §3 Constraint Network ───────────────────────────────────
    print("\n§3 Constraint Network\n")

    net = ConstraintNetwork()
    net.add_variable("x", Domain.trust_levels())
    net.add_variable("y", Domain.trust_levels())
    net.add_constraint(["x", "y"], lambda x, y: x >= y, "x >= y")

    check("network_vars", len(net.variables) == 2)
    check("network_constraints", len(net.constraints) == 1)
    check("network_consistent", net.is_consistent({"x": 0.8, "y": 0.5}))
    check("network_inconsistent", not net.is_consistent({"x": 0.3, "y": 0.5}))

    # ── §4 Node Consistency ──────────────────────────────────────
    print("\n§4 Node Consistency\n")

    net2 = ConstraintNetwork()
    net2.add_variable("trust", Domain.from_range(0.0, 1.0, 0.1))
    net2.add_constraint(["trust"], lambda t: t >= 0.5, "trust >= 0.5")

    removed = node_consistency(net2)
    check("node_consistency_removed", removed > 0)
    check("only_high_trust", all(v >= 0.5 - 1e-9 for v in net2.variables["trust"].values))

    # ── §5 Arc Consistency ───────────────────────────────────────
    print("\n§5 Arc Consistency (AC-3)\n")

    net3 = ConstraintNetwork()
    net3.add_variable("a", Domain.from_range(0.0, 1.0, 0.1))
    net3.add_variable("b", Domain.from_range(0.0, 1.0, 0.1))
    net3.add_constraint(["a", "b"], lambda a, b: a > b, "a > b")

    consistent, ac_removed = arc_consistency_3(net3)
    check("ac3_consistent", consistent)
    check("ac3_removed_values", ac_removed > 0)
    # a can't be 0 (nothing less), b can't be 1 (nothing greater)
    check("a_cant_be_0", 0.0 not in net3.variables["a"].values)
    check("b_cant_be_1", 1.0 not in net3.variables["b"].values)

    # Inconsistent: a > 0.9 AND a < 0.1
    net4 = ConstraintNetwork()
    net4.add_variable("x", Domain.from_range(0.0, 1.0, 0.1))
    net4.add_constraint(["x"], lambda x: x > 0.9, "x > 0.9")
    node_consistency(net4)
    check("nc_leaves_1", net4.variables["x"].values == {1.0})

    # ── §6 Backtracking Search ───────────────────────────────────
    print("\n§6 Backtracking Search\n")

    net5 = ConstraintNetwork()
    net5.add_variable("x", Domain({0.0, 0.5, 1.0}))
    net5.add_variable("y", Domain({0.0, 0.5, 1.0}))
    net5.add_constraint(["x", "y"], lambda x, y: x + y == 1.0, "x+y=1")

    solutions = backtracking_search(net5)
    check("solutions_found", len(solutions) > 0)
    check("solutions_valid", all(
        abs(s["x"] + s["y"] - 1.0) < 1e-9 for s in solutions))
    # Solutions: (0, 1), (0.5, 0.5), (1, 0)
    check("solutions_count", len(solutions) == 3, f"found {len(solutions)}")

    # ── §7 Trust-Specific Constraints ────────────────────────────
    print("\n§7 Trust-Specific Constraints\n")

    # Transitivity: trust(a,c) <= trust(a,b) * trust(b,c)
    net6 = ConstraintNetwork()
    net6.add_variable("ab", Domain({0.5, 0.8, 1.0}))
    net6.add_variable("bc", Domain({0.5, 0.8, 1.0}))
    net6.add_variable("ac", Domain({0.0, 0.2, 0.4, 0.5, 0.8, 1.0}))
    # ac <= ab * bc
    net6.add_constraint(["ab", "bc", "ac"],
                         lambda ab, bc, ac: ac <= ab * bc + 1e-9,
                         "transitivity")

    sols6 = backtracking_search(net6, max_solutions=200)
    check("transitivity_solutions", len(sols6) > 0)
    check("transitivity_valid", all(
        s["ac"] <= s["ab"] * s["bc"] + 1e-9 for s in sols6))

    # Monotonicity: t1 <= t2
    net7 = ConstraintNetwork()
    net7.add_variable("t1", Domain({0.0, 0.3, 0.5, 0.7, 1.0}))
    net7.add_variable("t2", Domain({0.0, 0.3, 0.5, 0.7, 1.0}))
    net7.add_constraint(["t1", "t2"], lambda t1, t2: t2 >= t1, "monotone")

    sols7 = backtracking_search(net7)
    check("monotone_solutions", len(sols7) > 0)
    check("monotone_valid", all(s["t2"] >= s["t1"] - 1e-9 for s in sols7))
    # Count: all pairs where t2 >= t1 from 5 values
    check("monotone_count", len(sols7) == 15, f"count={len(sols7)}")

    # ── §8 Complex Network ──────────────────────────────────────
    print("\n§8 Complex Constraint Network\n")

    # Three entities with trust constraints forming a triangle
    net8 = ConstraintNetwork()
    for v in ["ab", "bc", "ac"]:
        net8.add_variable(v, Domain({0.0, 0.3, 0.5, 0.7, 1.0}))

    # Transitivity: ac <= ab * bc
    net8.add_constraint(["ab", "bc", "ac"],
                         lambda ab, bc, ac: ac <= ab * bc + 1e-9)
    # All must be positive
    for v in ["ab", "bc", "ac"]:
        net8.add_constraint([v], lambda x: x > 0)

    node_consistency(net8)
    check("complex_nc_pruned", 0.0 not in net8.variables["ab"].values)

    sols8 = backtracking_search(net8)
    check("complex_solutions", len(sols8) > 0)
    check("complex_all_positive", all(
        s["ab"] > 0 and s["bc"] > 0 and s["ac"] > 0 for s in sols8))
    check("complex_transitive", all(
        s["ac"] <= s["ab"] * s["bc"] + 1e-9 for s in sols8))

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
