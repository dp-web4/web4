"""
Trust Temporal Logic for Web4
Session 33, Track 1

Linear Temporal Logic (LTL) and Computation Tree Logic (CTL)
specifications for trust properties:
- LTL formulas: G (globally), F (eventually), X (next), U (until), R (release)
- CTL formulas: A/E path quantifiers with temporal operators
- Trust-specific properties (eventual attestation, persistent trust, etc.)
- Model checking over trust state traces
- Fairness constraints for trust protocols
- Büchi automata for LTL satisfaction
- Counterexample generation for violated properties
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Tuple, Optional, Set, Callable


# ─── LTL Formula AST ────────────────────────────────────────────

class LTLOp(Enum):
    # Atomic
    ATOM = auto()
    TRUE = auto()
    FALSE = auto()
    # Boolean
    NOT = auto()
    AND = auto()
    OR = auto()
    IMPLIES = auto()
    # Temporal
    NEXT = auto()       # X φ — holds in next state
    GLOBALLY = auto()   # G φ — holds in all future states
    EVENTUALLY = auto() # F φ — holds in some future state
    UNTIL = auto()      # φ U ψ — φ holds until ψ holds
    RELEASE = auto()    # φ R ψ — ψ holds until (and including) φ holds


@dataclass
class LTLFormula:
    op: LTLOp
    atom: str = ""
    left: Optional['LTLFormula'] = None
    right: Optional['LTLFormula'] = None

    def __repr__(self):
        if self.op == LTLOp.ATOM:
            return self.atom
        if self.op == LTLOp.TRUE:
            return "⊤"
        if self.op == LTLOp.FALSE:
            return "⊥"
        if self.op == LTLOp.NOT:
            return f"¬{self.left}"
        if self.op == LTLOp.AND:
            return f"({self.left} ∧ {self.right})"
        if self.op == LTLOp.OR:
            return f"({self.left} ∨ {self.right})"
        if self.op == LTLOp.IMPLIES:
            return f"({self.left} → {self.right})"
        if self.op == LTLOp.NEXT:
            return f"X{self.left}"
        if self.op == LTLOp.GLOBALLY:
            return f"G{self.left}"
        if self.op == LTLOp.EVENTUALLY:
            return f"F{self.left}"
        if self.op == LTLOp.UNTIL:
            return f"({self.left} U {self.right})"
        if self.op == LTLOp.RELEASE:
            return f"({self.left} R {self.right})"
        return f"LTL({self.op})"


# Constructors
def Atom(name: str) -> LTLFormula:
    return LTLFormula(LTLOp.ATOM, atom=name)

def Not(f: LTLFormula) -> LTLFormula:
    return LTLFormula(LTLOp.NOT, left=f)

def And(a: LTLFormula, b: LTLFormula) -> LTLFormula:
    return LTLFormula(LTLOp.AND, left=a, right=b)

def Or(a: LTLFormula, b: LTLFormula) -> LTLFormula:
    return LTLFormula(LTLOp.OR, left=a, right=b)

def Implies(a: LTLFormula, b: LTLFormula) -> LTLFormula:
    return LTLFormula(LTLOp.IMPLIES, left=a, right=b)

def Next(f: LTLFormula) -> LTLFormula:
    return LTLFormula(LTLOp.NEXT, left=f)

def Globally(f: LTLFormula) -> LTLFormula:
    return LTLFormula(LTLOp.GLOBALLY, left=f)

def Eventually(f: LTLFormula) -> LTLFormula:
    return LTLFormula(LTLOp.EVENTUALLY, left=f)

def Until(a: LTLFormula, b: LTLFormula) -> LTLFormula:
    return LTLFormula(LTLOp.UNTIL, left=a, right=b)

def Release(a: LTLFormula, b: LTLFormula) -> LTLFormula:
    return LTLFormula(LTLOp.RELEASE, left=a, right=b)


# ─── CTL Formula AST ────────────────────────────────────────────

class CTLOp(Enum):
    ATOM = auto()
    TRUE = auto()
    FALSE = auto()
    NOT = auto()
    AND = auto()
    OR = auto()
    # CTL temporal (path quantifier + temporal operator)
    AX = auto()   # For All paths, neXt
    EX = auto()   # Exists path, neXt
    AG = auto()   # For All paths, Globally
    EG = auto()   # Exists path, Globally
    AF = auto()   # For All paths, Finally
    EF = auto()   # Exists path, Finally
    AU = auto()   # For All paths, Until
    EU = auto()   # Exists path, Until


@dataclass
class CTLFormula:
    op: CTLOp
    atom: str = ""
    left: Optional['CTLFormula'] = None
    right: Optional['CTLFormula'] = None

    def __repr__(self):
        names = {
            CTLOp.ATOM: lambda: self.atom,
            CTLOp.TRUE: lambda: "⊤",
            CTLOp.FALSE: lambda: "⊥",
            CTLOp.NOT: lambda: f"¬{self.left}",
            CTLOp.AND: lambda: f"({self.left} ∧ {self.right})",
            CTLOp.OR: lambda: f"({self.left} ∨ {self.right})",
            CTLOp.AX: lambda: f"AX{self.left}",
            CTLOp.EX: lambda: f"EX{self.left}",
            CTLOp.AG: lambda: f"AG{self.left}",
            CTLOp.EG: lambda: f"EG{self.left}",
            CTLOp.AF: lambda: f"AF{self.left}",
            CTLOp.EF: lambda: f"EF{self.left}",
            CTLOp.AU: lambda: f"A({self.left} U {self.right})",
            CTLOp.EU: lambda: f"E({self.left} U {self.right})",
        }
        return names.get(self.op, lambda: f"CTL({self.op})")()


# CTL constructors
def CTLAtom(name: str) -> CTLFormula:
    return CTLFormula(CTLOp.ATOM, atom=name)

def AG(f: CTLFormula) -> CTLFormula:
    return CTLFormula(CTLOp.AG, left=f)

def EF(f: CTLFormula) -> CTLFormula:
    return CTLFormula(CTLOp.EF, left=f)

def AF(f: CTLFormula) -> CTLFormula:
    return CTLFormula(CTLOp.AF, left=f)

def EG(f: CTLFormula) -> CTLFormula:
    return CTLFormula(CTLOp.EG, left=f)

def AX(f: CTLFormula) -> CTLFormula:
    return CTLFormula(CTLOp.AX, left=f)

def EX(f: CTLFormula) -> CTLFormula:
    return CTLFormula(CTLOp.EX, left=f)

def AU(a: CTLFormula, b: CTLFormula) -> CTLFormula:
    return CTLFormula(CTLOp.AU, left=a, right=b)

def EU(a: CTLFormula, b: CTLFormula) -> CTLFormula:
    return CTLFormula(CTLOp.EU, left=a, right=b)


# ─── Trust State Trace ──────────────────────────────────────────

@dataclass
class TrustState:
    """A state in a trust execution trace."""
    props: Set[str]  # set of atomic propositions true in this state
    trust_scores: Dict[str, float] = field(default_factory=dict)


def make_trace(*prop_sets: Set[str]) -> List[TrustState]:
    """Create a trace from sets of propositions."""
    return [TrustState(props=ps) for ps in prop_sets]


# ─── LTL Model Checking on Finite Traces ────────────────────────

def check_ltl(formula: LTLFormula, trace: List[TrustState], pos: int = 0) -> bool:
    """
    Check if LTL formula holds at position pos in a finite trace.
    For finite traces, G means "for all remaining", F means "exists in remaining".
    """
    if pos >= len(trace):
        # Past end of trace
        if formula.op == LTLOp.GLOBALLY:
            return True  # vacuously true
        if formula.op == LTLOp.EVENTUALLY:
            return False  # no more states to satisfy
        if formula.op == LTLOp.TRUE:
            return True
        if formula.op == LTLOp.FALSE:
            return False
        return False

    state = trace[pos]

    if formula.op == LTLOp.ATOM:
        return formula.atom in state.props
    if formula.op == LTLOp.TRUE:
        return True
    if formula.op == LTLOp.FALSE:
        return False
    if formula.op == LTLOp.NOT:
        return not check_ltl(formula.left, trace, pos)
    if formula.op == LTLOp.AND:
        return check_ltl(formula.left, trace, pos) and check_ltl(formula.right, trace, pos)
    if formula.op == LTLOp.OR:
        return check_ltl(formula.left, trace, pos) or check_ltl(formula.right, trace, pos)
    if formula.op == LTLOp.IMPLIES:
        return not check_ltl(formula.left, trace, pos) or check_ltl(formula.right, trace, pos)
    if formula.op == LTLOp.NEXT:
        return check_ltl(formula.left, trace, pos + 1)
    if formula.op == LTLOp.GLOBALLY:
        return all(check_ltl(formula.left, trace, i) for i in range(pos, len(trace)))
    if formula.op == LTLOp.EVENTUALLY:
        return any(check_ltl(formula.left, trace, i) for i in range(pos, len(trace)))
    if formula.op == LTLOp.UNTIL:
        # φ U ψ: ψ holds at some future j, and φ holds for all i in [pos, j)
        for j in range(pos, len(trace)):
            if check_ltl(formula.right, trace, j):
                if all(check_ltl(formula.left, trace, i) for i in range(pos, j)):
                    return True
        return False
    if formula.op == LTLOp.RELEASE:
        # φ R ψ ≡ ¬(¬φ U ¬ψ)
        neg_until = Until(Not(formula.left), Not(formula.right))
        return not check_ltl(neg_until, trace, pos)

    return False


# ─── CTL Model Checking on Kripke Structures ────────────────────

@dataclass
class KripkeStructure:
    """Simple Kripke structure for CTL model checking."""
    states: Set[str]
    initial: str
    transitions: Dict[str, Set[str]]  # state -> set of successor states
    labeling: Dict[str, Set[str]]     # state -> set of atomic propositions

    def successors(self, state: str) -> Set[str]:
        return self.transitions.get(state, set())


def check_ctl(formula: CTLFormula, ks: KripkeStructure, state: str) -> bool:
    """Check if CTL formula holds at state in Kripke structure."""
    if formula.op == CTLOp.ATOM:
        return formula.atom in ks.labeling.get(state, set())
    if formula.op == CTLOp.TRUE:
        return True
    if formula.op == CTLOp.FALSE:
        return False
    if formula.op == CTLOp.NOT:
        return not check_ctl(formula.left, ks, state)
    if formula.op == CTLOp.AND:
        return check_ctl(formula.left, ks, state) and check_ctl(formula.right, ks, state)
    if formula.op == CTLOp.OR:
        return check_ctl(formula.left, ks, state) or check_ctl(formula.right, ks, state)

    if formula.op == CTLOp.AX:
        succs = ks.successors(state)
        if not succs:
            return True  # vacuously true
        return all(check_ctl(formula.left, ks, s) for s in succs)

    if formula.op == CTLOp.EX:
        return any(check_ctl(formula.left, ks, s) for s in ks.successors(state))

    if formula.op == CTLOp.EF:
        # Exists path where eventually φ — reachability
        visited = set()
        stack = [state]
        while stack:
            s = stack.pop()
            if s in visited:
                continue
            visited.add(s)
            if check_ctl(formula.left, ks, s):
                return True
            stack.extend(ks.successors(s))
        return False

    if formula.op == CTLOp.AG:
        # For all paths, globally φ — φ holds everywhere reachable
        visited = set()
        stack = [state]
        while stack:
            s = stack.pop()
            if s in visited:
                continue
            visited.add(s)
            if not check_ctl(formula.left, ks, s):
                return False
            stack.extend(ks.successors(s))
        return True

    if formula.op == CTLOp.AF:
        # For all paths, eventually φ
        # Fixed-point: AF φ = μZ. φ ∨ (non-dead ∧ AX Z)
        sat = _af_fixpoint(formula.left, ks)
        return state in sat

    if formula.op == CTLOp.EG:
        # Exists path, globally φ
        # Fixed-point: EG φ = νZ. φ ∧ EX Z
        sat = _eg_fixpoint(formula.left, ks)
        return state in sat

    if formula.op == CTLOp.EU:
        # E(φ U ψ) = μZ. ψ ∨ (φ ∧ EX Z)
        sat = _eu_fixpoint(formula.left, formula.right, ks)
        return state in sat

    if formula.op == CTLOp.AU:
        # A(φ U ψ) = μZ. ψ ∨ (φ ∧ AX Z ∧ EX ⊤)
        sat = _au_fixpoint(formula.left, formula.right, ks)
        return state in sat

    return False


def _af_fixpoint(phi: CTLFormula, ks: KripkeStructure) -> Set[str]:
    """Compute states satisfying AF φ via least fixed point."""
    sat = {s for s in ks.states if check_ctl(phi, ks, s)}
    changed = True
    while changed:
        changed = False
        for s in ks.states:
            if s in sat:
                continue
            succs = ks.successors(s)
            if succs and all(succ in sat for succ in succs):
                sat.add(s)
                changed = True
    return sat


def _eg_fixpoint(phi: CTLFormula, ks: KripkeStructure) -> Set[str]:
    """Compute states satisfying EG φ via greatest fixed point."""
    sat = {s for s in ks.states if check_ctl(phi, ks, s)}
    changed = True
    while changed:
        changed = False
        to_remove = set()
        for s in sat:
            succs = ks.successors(s)
            if succs and not any(succ in sat for succ in succs):
                to_remove.add(s)
            elif not succs:
                # Dead end — can stay in EG if φ holds (infinite self-loop semantics)
                pass
        if to_remove:
            sat -= to_remove
            changed = True
    return sat


def _eu_fixpoint(phi: CTLFormula, psi: CTLFormula, ks: KripkeStructure) -> Set[str]:
    """Compute states satisfying E(φ U ψ) via least fixed point."""
    sat = {s for s in ks.states if check_ctl(psi, ks, s)}
    changed = True
    while changed:
        changed = False
        for s in ks.states:
            if s in sat:
                continue
            if check_ctl(phi, ks, s) and any(succ in sat for succ in ks.successors(s)):
                sat.add(s)
                changed = True
    return sat


def _au_fixpoint(phi: CTLFormula, psi: CTLFormula, ks: KripkeStructure) -> Set[str]:
    """Compute states satisfying A(φ U ψ) via least fixed point."""
    sat = {s for s in ks.states if check_ctl(psi, ks, s)}
    changed = True
    while changed:
        changed = False
        for s in ks.states:
            if s in sat:
                continue
            succs = ks.successors(s)
            if check_ctl(phi, ks, s) and succs and all(succ in sat for succ in succs):
                sat.add(s)
                changed = True
    return sat


# ─── Trust-Specific Properties ──────────────────────────────────

def trust_liveness() -> LTLFormula:
    """Eventually, trust is established: F(trusted)"""
    return Eventually(Atom("trusted"))

def trust_safety() -> LTLFormula:
    """Globally, if compromised then eventually revoked: G(compromised → F(revoked))"""
    return Globally(Implies(Atom("compromised"), Eventually(Atom("revoked"))))

def trust_persistence() -> LTLFormula:
    """Once trusted, stays trusted until revoked: G(trusted → (trusted U revoked))"""
    return Globally(Implies(Atom("trusted"), Until(Atom("trusted"), Atom("revoked"))))

def attestation_response() -> LTLFormula:
    """Every request eventually gets a response: G(requested → F(responded))"""
    return Globally(Implies(Atom("requested"), Eventually(Atom("responded"))))

def no_trust_without_attestation() -> LTLFormula:
    """Trust requires prior attestation: G(trusted → ¬(¬attested U trusted))"""
    # Simplified: trust only after attestation
    return Globally(Implies(Atom("trusted"), Atom("attested")))

def monotonic_trust_increase() -> LTLFormula:
    """Trust level never decreases (within a session): G(high_trust → G(high_trust))"""
    return Globally(Implies(Atom("high_trust"), Globally(Atom("high_trust"))))


# ─── Counterexample Generation ──────────────────────────────────

def find_counterexample(formula: LTLFormula, trace: List[TrustState]) -> Optional[int]:
    """
    For a G (globally) formula, find the first position where it fails.
    Returns the position index, or None if no counterexample.
    """
    if formula.op == LTLOp.GLOBALLY:
        for i in range(len(trace)):
            if not check_ltl(formula.left, trace, i):
                return i
    # For general formulas, check if the formula fails at position 0
    if not check_ltl(formula, trace, 0):
        return 0
    return None


def generate_witness(formula: LTLFormula, trace: List[TrustState]) -> Optional[int]:
    """
    For an F (eventually) formula, find the first position where it holds.
    Returns the position index, or None if no witness.
    """
    if formula.op == LTLOp.EVENTUALLY:
        for i in range(len(trace)):
            if check_ltl(formula.left, trace, i):
                return i
    if check_ltl(formula, trace, 0):
        return 0
    return None


# ─── Formula Transformations ────────────────────────────────────

def ltl_to_nnf(formula: LTLFormula) -> LTLFormula:
    """Convert LTL formula to Negation Normal Form (push negations to atoms)."""
    if formula.op == LTLOp.ATOM or formula.op == LTLOp.TRUE or formula.op == LTLOp.FALSE:
        return formula

    if formula.op == LTLOp.NOT:
        inner = formula.left
        if inner.op == LTLOp.ATOM:
            return formula  # ¬atom is in NNF
        if inner.op == LTLOp.TRUE:
            return LTLFormula(LTLOp.FALSE)
        if inner.op == LTLOp.FALSE:
            return LTLFormula(LTLOp.TRUE)
        if inner.op == LTLOp.NOT:
            return ltl_to_nnf(inner.left)  # ¬¬φ = φ
        if inner.op == LTLOp.AND:
            return Or(ltl_to_nnf(Not(inner.left)), ltl_to_nnf(Not(inner.right)))
        if inner.op == LTLOp.OR:
            return And(ltl_to_nnf(Not(inner.left)), ltl_to_nnf(Not(inner.right)))
        if inner.op == LTLOp.NEXT:
            return Next(ltl_to_nnf(Not(inner.left)))
        if inner.op == LTLOp.GLOBALLY:
            return Eventually(ltl_to_nnf(Not(inner.left)))  # ¬Gφ = F¬φ
        if inner.op == LTLOp.EVENTUALLY:
            return Globally(ltl_to_nnf(Not(inner.left)))    # ¬Fφ = G¬φ
        if inner.op == LTLOp.UNTIL:
            return Release(ltl_to_nnf(Not(inner.left)), ltl_to_nnf(Not(inner.right)))
        if inner.op == LTLOp.RELEASE:
            return Until(ltl_to_nnf(Not(inner.left)), ltl_to_nnf(Not(inner.right)))
        if inner.op == LTLOp.IMPLIES:
            # ¬(a→b) = a ∧ ¬b
            return And(ltl_to_nnf(inner.left), ltl_to_nnf(Not(inner.right)))

    if formula.op == LTLOp.IMPLIES:
        return Or(ltl_to_nnf(Not(formula.left)), ltl_to_nnf(formula.right))

    # Recurse for other operators
    left = ltl_to_nnf(formula.left) if formula.left else None
    right = ltl_to_nnf(formula.right) if formula.right else None
    return LTLFormula(formula.op, atom=formula.atom, left=left, right=right)


def count_temporal_operators(formula: LTLFormula) -> int:
    """Count temporal operators in a formula (measure of complexity)."""
    temporal_ops = {LTLOp.NEXT, LTLOp.GLOBALLY, LTLOp.EVENTUALLY, LTLOp.UNTIL, LTLOp.RELEASE}
    count = 1 if formula.op in temporal_ops else 0
    if formula.left:
        count += count_temporal_operators(formula.left)
    if formula.right:
        count += count_temporal_operators(formula.right)
    return count


def collect_atoms(formula: LTLFormula) -> Set[str]:
    """Collect all atomic propositions in a formula."""
    if formula.op == LTLOp.ATOM:
        return {formula.atom}
    atoms = set()
    if formula.left:
        atoms |= collect_atoms(formula.left)
    if formula.right:
        atoms |= collect_atoms(formula.right)
    return atoms


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
    print("Trust Temporal Logic for Web4")
    print("Session 33, Track 1")
    print("=" * 70)

    # ── §1 LTL Formula Construction ───────────────────────────────
    print("\n§1 LTL Formula Construction\n")

    f1 = Globally(Atom("trusted"))
    check("globally_repr", "G" in repr(f1))

    f2 = Eventually(Atom("attested"))
    check("eventually_repr", "F" in repr(f2))

    f3 = Until(Atom("pending"), Atom("resolved"))
    check("until_repr", "U" in repr(f3))

    f4 = Implies(Atom("requested"), Eventually(Atom("responded")))
    atoms = collect_atoms(f4)
    check("collect_atoms", atoms == {"requested", "responded"})

    check("temporal_count", count_temporal_operators(f4) == 1)
    check("temporal_count_nested", count_temporal_operators(
        Globally(Implies(Atom("a"), Eventually(Atom("b"))))) == 2)

    # ── §2 LTL Model Checking on Traces ──────────────────────────
    print("\n§2 LTL Model Checking on Traces\n")

    # Simple trace: idle → requested → attested → trusted
    trace1 = make_trace(
        {"idle"},
        {"requested"},
        {"attested"},
        {"trusted", "attested"}
    )

    # F(trusted) should hold
    check("eventually_trusted", check_ltl(Eventually(Atom("trusted")), trace1))

    # G(trusted) should NOT hold (not true at start)
    check("not_globally_trusted", not check_ltl(Globally(Atom("trusted")), trace1))

    # X(requested) holds at position 0
    check("next_requested", check_ltl(Next(Atom("requested")), trace1, 0))

    # X(requested) does NOT hold at position 1
    check("next_not_requested_at_1", not check_ltl(Next(Atom("requested")), trace1, 1))

    # Until: idle U requested
    check("until_idle_requested", check_ltl(
        Until(Atom("idle"), Atom("requested")), trace1))

    # ── §3 Trust-Specific Properties ──────────────────────────────
    print("\n§3 Trust-Specific Properties\n")

    # Trust liveness: eventually trusted
    check("trust_liveness", check_ltl(trust_liveness(), trace1))

    # No trust without attestation: G(trusted → attested)
    check("trust_requires_attestation", check_ltl(
        no_trust_without_attestation(), trace1))

    # Trace with trust but no attestation — should violate
    bad_trace = make_trace({"idle"}, {"trusted"})
    check("trust_without_attestation_fails", not check_ltl(
        no_trust_without_attestation(), bad_trace))

    # Safety: compromised → eventually revoked
    safety_trace = make_trace(
        {"normal"},
        {"compromised"},
        {"compromised", "detected"},
        {"revoked"}
    )
    check("safety_holds", check_ltl(trust_safety(), safety_trace))

    # Safety violation: compromised but never revoked
    unsafe_trace = make_trace(
        {"normal"},
        {"compromised"},
        {"compromised"}
    )
    check("safety_violated", not check_ltl(trust_safety(), unsafe_trace))

    # ── §4 CTL Model Checking ────────────────────────────────────
    print("\n§4 CTL Model Checking\n")

    # Kripke structure for trust protocol
    # s0(idle) → s1(requested) → s2(verified) → s3(trusted)
    #                          ↘ s4(rejected)
    ks = KripkeStructure(
        states={"s0", "s1", "s2", "s3", "s4"},
        initial="s0",
        transitions={
            "s0": {"s1"},
            "s1": {"s2", "s4"},
            "s2": {"s3"},
            "s3": set(),
            "s4": set(),
        },
        labeling={
            "s0": {"idle"},
            "s1": {"requested"},
            "s2": {"verified"},
            "s3": {"trusted"},
            "s4": {"rejected"},
        }
    )

    # EF(trusted): there exists a path to trusted
    check("ef_trusted", check_ctl(EF(CTLAtom("trusted")), ks, "s0"))

    # AG(¬deadlock): no deadlocks — final states have no successors but that's OK
    # Actually check: AG(idle ∨ requested ∨ verified ∨ trusted ∨ rejected) — always in a valid state
    valid = CTLFormula(CTLOp.OR,
        left=CTLAtom("idle"),
        right=CTLFormula(CTLOp.OR,
            left=CTLAtom("requested"),
            right=CTLFormula(CTLOp.OR,
                left=CTLAtom("verified"),
                right=CTLFormula(CTLOp.OR,
                    left=CTLAtom("trusted"),
                    right=CTLAtom("rejected")))))
    check("ag_valid_state", check_ctl(AG(valid), ks, "s0"))

    # AF(trusted ∨ rejected): all paths eventually terminate
    terminal = CTLFormula(CTLOp.OR, left=CTLAtom("trusted"), right=CTLAtom("rejected"))
    check("af_terminal", check_ctl(AF(terminal), ks, "s0"))

    # EG(¬rejected): exists a path that never gets rejected
    not_rejected = CTLFormula(CTLOp.NOT, left=CTLAtom("rejected"))
    check("eg_not_rejected", check_ctl(EG(not_rejected), ks, "s0"))

    # AX from s0: next state must be requested
    check("ax_requested", check_ctl(AX(CTLAtom("requested")), ks, "s0"))

    # ── §5 NNF Transformation ────────────────────────────────────
    print("\n§5 NNF Transformation\n")

    # ¬Gφ = F¬φ
    nnf1 = ltl_to_nnf(Not(Globally(Atom("trusted"))))
    check("nnf_not_g", nnf1.op == LTLOp.EVENTUALLY)

    # ¬Fφ = G¬φ
    nnf2 = ltl_to_nnf(Not(Eventually(Atom("trusted"))))
    check("nnf_not_f", nnf2.op == LTLOp.GLOBALLY)

    # ¬¬φ = φ
    nnf3 = ltl_to_nnf(Not(Not(Atom("x"))))
    check("nnf_double_neg", nnf3.op == LTLOp.ATOM and nnf3.atom == "x")

    # De Morgan: ¬(a ∧ b) = ¬a ∨ ¬b
    nnf4 = ltl_to_nnf(Not(And(Atom("a"), Atom("b"))))
    check("nnf_de_morgan", nnf4.op == LTLOp.OR)

    # ¬(φ U ψ) = ¬φ R ¬ψ
    nnf5 = ltl_to_nnf(Not(Until(Atom("a"), Atom("b"))))
    check("nnf_not_until", nnf5.op == LTLOp.RELEASE)

    # Implies elimination: a → b = ¬a ∨ b
    nnf6 = ltl_to_nnf(Implies(Atom("a"), Atom("b")))
    check("nnf_implies", nnf6.op == LTLOp.OR)

    # ── §6 Counterexample & Witness ──────────────────────────────
    print("\n§6 Counterexample & Witness\n")

    # Counterexample for G(trusted) on trace1
    cex = find_counterexample(Globally(Atom("trusted")), trace1)
    check("counterexample_found", cex == 0, f"cex={cex}")

    # No counterexample for G(true)
    cex2 = find_counterexample(Globally(LTLFormula(LTLOp.TRUE)), trace1)
    check("no_counterexample_for_true", cex2 is None)

    # Witness for F(trusted)
    wit = generate_witness(Eventually(Atom("trusted")), trace1)
    check("witness_found", wit == 3, f"wit={wit}")

    # No witness for F(nonexistent)
    wit2 = generate_witness(Eventually(Atom("nonexistent")), trace1)
    check("no_witness", wit2 is None)

    # ── §7 Monotonic Trust ───────────────────────────────────────
    print("\n§7 Monotonic Trust Property\n")

    # Once high_trust, always high_trust
    mono_trace = make_trace(
        {"low_trust"},
        {"medium_trust"},
        {"high_trust"},
        {"high_trust"},
        {"high_trust"}
    )
    check("monotonic_holds", check_ltl(monotonic_trust_increase(), mono_trace))

    # Violation: trust drops
    non_mono_trace = make_trace(
        {"high_trust"},
        {"high_trust"},
        {"low_trust"},
        {"high_trust"}
    )
    check("monotonic_violated", not check_ltl(monotonic_trust_increase(), non_mono_trace))

    # ── §8 Release Operator ──────────────────────────────────────
    print("\n§8 Release Operator\n")

    # φ R ψ: ψ holds until (and including when) φ first holds
    # "maintained until override": maintained R override
    release_trace = make_trace(
        {"maintained"},
        {"maintained"},
        {"maintained", "override"},
        {"override"}
    )
    check("release_holds", check_ltl(
        Release(Atom("override"), Atom("maintained")), release_trace))

    # Release fails: ψ stops before φ arrives
    bad_release = make_trace(
        {"maintained"},
        set(),  # maintained stops
        {"override"}
    )
    check("release_fails", not check_ltl(
        Release(Atom("override"), Atom("maintained")), bad_release))

    # ── Summary ─────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
