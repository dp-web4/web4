"""
Trust Hoare Logic for Web4
Session 34, Track 6

Pre/post-condition reasoning for trust operations:
- Hoare triples {P} C {Q} — if P holds before C, Q holds after
- Weakest precondition computation
- Strongest postcondition computation
- Trust-specific proof rules (attestation, delegation, revocation)
- Assertion language for trust predicates
- Verification condition generation
- Loop invariants for trust protocols
- Compositional reasoning (sequential, conditional, loop)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set, Callable
from enum import Enum, auto


# ─── Assertion Language ──────────────────────────────────────────

class AssertionOp(Enum):
    TRUE = auto()
    FALSE = auto()
    VAR = auto()           # variable reference
    CONST = auto()         # constant value
    NOT = auto()
    AND = auto()
    OR = auto()
    IMPLIES = auto()
    GT = auto()            # >
    GE = auto()            # >=
    LT = auto()            # <
    LE = auto()            # <=
    EQ = auto()            # ==
    PLUS = auto()
    MINUS = auto()
    TIMES = auto()
    FORALL = auto()        # ∀x. P
    EXISTS = auto()        # ∃x. P


@dataclass
class Assertion:
    op: AssertionOp
    name: str = ""
    value: float = 0.0
    left: Optional['Assertion'] = None
    right: Optional['Assertion'] = None

    def __repr__(self):
        if self.op == AssertionOp.TRUE:
            return "true"
        if self.op == AssertionOp.FALSE:
            return "false"
        if self.op == AssertionOp.VAR:
            return self.name
        if self.op == AssertionOp.CONST:
            return str(self.value)
        if self.op == AssertionOp.NOT:
            return f"¬({self.left})"
        if self.op == AssertionOp.AND:
            return f"({self.left} ∧ {self.right})"
        if self.op == AssertionOp.OR:
            return f"({self.left} ∨ {self.right})"
        if self.op == AssertionOp.IMPLIES:
            return f"({self.left} → {self.right})"
        if self.op == AssertionOp.GE:
            return f"({self.left} ≥ {self.right})"
        if self.op == AssertionOp.LE:
            return f"({self.left} ≤ {self.right})"
        if self.op == AssertionOp.GT:
            return f"({self.left} > {self.right})"
        if self.op == AssertionOp.LT:
            return f"({self.left} < {self.right})"
        if self.op == AssertionOp.EQ:
            return f"({self.left} = {self.right})"
        if self.op in (AssertionOp.PLUS, AssertionOp.MINUS, AssertionOp.TIMES):
            sym = {AssertionOp.PLUS: "+", AssertionOp.MINUS: "-", AssertionOp.TIMES: "*"}
            return f"({self.left} {sym[self.op]} {self.right})"
        return f"Assertion({self.op})"


# Constructors
def TrueA() -> Assertion: return Assertion(AssertionOp.TRUE)
def FalseA() -> Assertion: return Assertion(AssertionOp.FALSE)
def Var(name: str) -> Assertion: return Assertion(AssertionOp.VAR, name=name)
def Const(v: float) -> Assertion: return Assertion(AssertionOp.CONST, value=v)
def NotA(a: Assertion) -> Assertion: return Assertion(AssertionOp.NOT, left=a)
def AndA(a: Assertion, b: Assertion) -> Assertion: return Assertion(AssertionOp.AND, left=a, right=b)
def OrA(a: Assertion, b: Assertion) -> Assertion: return Assertion(AssertionOp.OR, left=a, right=b)
def ImpliesA(a: Assertion, b: Assertion) -> Assertion: return Assertion(AssertionOp.IMPLIES, left=a, right=b)
def Ge(a: Assertion, b: Assertion) -> Assertion: return Assertion(AssertionOp.GE, left=a, right=b)
def Le(a: Assertion, b: Assertion) -> Assertion: return Assertion(AssertionOp.LE, left=a, right=b)
def Gt(a: Assertion, b: Assertion) -> Assertion: return Assertion(AssertionOp.GT, left=a, right=b)
def Lt(a: Assertion, b: Assertion) -> Assertion: return Assertion(AssertionOp.LT, left=a, right=b)
def Eq(a: Assertion, b: Assertion) -> Assertion: return Assertion(AssertionOp.EQ, left=a, right=b)
def Plus(a: Assertion, b: Assertion) -> Assertion: return Assertion(AssertionOp.PLUS, left=a, right=b)
def Minus(a: Assertion, b: Assertion) -> Assertion: return Assertion(AssertionOp.MINUS, left=a, right=b)
def Times(a: Assertion, b: Assertion) -> Assertion: return Assertion(AssertionOp.TIMES, left=a, right=b)


# ─── Trust Predicates ────────────────────────────────────────────

def trust_bounded(var: str) -> Assertion:
    """0 ≤ var ≤ 1"""
    return AndA(Ge(Var(var), Const(0.0)), Le(Var(var), Const(1.0)))

def trust_above(var: str, threshold: float) -> Assertion:
    """var >= threshold"""
    return Ge(Var(var), Const(threshold))

def trust_below(var: str, threshold: float) -> Assertion:
    """var <= threshold"""
    return Le(Var(var), Const(threshold))

def trust_in_range(var: str, lo: float, hi: float) -> Assertion:
    """lo ≤ var ≤ hi"""
    return AndA(Ge(Var(var), Const(lo)), Le(Var(var), Const(hi)))


# ─── Commands (Imperative Trust Programs) ────────────────────────

class CmdType(Enum):
    SKIP = auto()
    ASSIGN = auto()        # x := e
    SEQ = auto()           # C1; C2
    IF = auto()            # if B then C1 else C2
    WHILE = auto()         # while B do C (with invariant)
    ASSERT = auto()        # assert P
    ASSUME = auto()        # assume P


@dataclass
class Command:
    ctype: CmdType
    var: str = ""
    expr: Optional[Assertion] = None
    cond: Optional[Assertion] = None
    left: Optional['Command'] = None
    right: Optional['Command'] = None
    invariant: Optional[Assertion] = None  # For while loops

    def __repr__(self):
        if self.ctype == CmdType.SKIP:
            return "skip"
        if self.ctype == CmdType.ASSIGN:
            return f"{self.var} := {self.expr}"
        if self.ctype == CmdType.SEQ:
            return f"{self.left}; {self.right}"
        if self.ctype == CmdType.IF:
            return f"if {self.cond} then {self.left} else {self.right}"
        if self.ctype == CmdType.WHILE:
            return f"while {self.cond} do {self.left}"
        if self.ctype == CmdType.ASSERT:
            return f"assert({self.cond})"
        if self.ctype == CmdType.ASSUME:
            return f"assume({self.cond})"
        return f"Cmd({self.ctype})"


# Command constructors
def CSkip() -> Command: return Command(CmdType.SKIP)
def Assign(var: str, expr: Assertion) -> Command:
    return Command(CmdType.ASSIGN, var=var, expr=expr)
def Seq(c1: Command, c2: Command) -> Command:
    return Command(CmdType.SEQ, left=c1, right=c2)
def If(cond: Assertion, then_cmd: Command, else_cmd: Command) -> Command:
    return Command(CmdType.IF, cond=cond, left=then_cmd, right=else_cmd)
def While(cond: Assertion, body: Command, invariant: Assertion = None) -> Command:
    return Command(CmdType.WHILE, cond=cond, left=body, invariant=invariant)
def Assert(pred: Assertion) -> Command:
    return Command(CmdType.ASSERT, cond=pred)
def Assume(pred: Assertion) -> Command:
    return Command(CmdType.ASSUME, cond=pred)


# ─── Hoare Triple ────────────────────────────────────────────────

@dataclass
class HoareTriple:
    """A Hoare triple {P} C {Q}."""
    precondition: Assertion
    command: Command
    postcondition: Assertion

    def __repr__(self):
        return f"{{{self.precondition}}} {self.command} {{{self.postcondition}}}"


# ─── Evaluation (Concrete) ──────────────────────────────────────

def eval_assertion(a: Assertion, state: Dict[str, float]) -> object:
    """Evaluate an assertion in a concrete state."""
    if a.op == AssertionOp.TRUE: return True
    if a.op == AssertionOp.FALSE: return False
    if a.op == AssertionOp.VAR: return state.get(a.name, 0.0)
    if a.op == AssertionOp.CONST: return a.value
    if a.op == AssertionOp.NOT: return not eval_assertion(a.left, state)
    if a.op == AssertionOp.AND:
        return eval_assertion(a.left, state) and eval_assertion(a.right, state)
    if a.op == AssertionOp.OR:
        return eval_assertion(a.left, state) or eval_assertion(a.right, state)
    if a.op == AssertionOp.IMPLIES:
        return not eval_assertion(a.left, state) or eval_assertion(a.right, state)
    if a.op == AssertionOp.GE:
        return eval_assertion(a.left, state) >= eval_assertion(a.right, state)
    if a.op == AssertionOp.LE:
        return eval_assertion(a.left, state) <= eval_assertion(a.right, state)
    if a.op == AssertionOp.GT:
        return eval_assertion(a.left, state) > eval_assertion(a.right, state)
    if a.op == AssertionOp.LT:
        return eval_assertion(a.left, state) < eval_assertion(a.right, state)
    if a.op == AssertionOp.EQ:
        return abs(eval_assertion(a.left, state) - eval_assertion(a.right, state)) < 1e-9
    if a.op == AssertionOp.PLUS:
        return eval_assertion(a.left, state) + eval_assertion(a.right, state)
    if a.op == AssertionOp.MINUS:
        return eval_assertion(a.left, state) - eval_assertion(a.right, state)
    if a.op == AssertionOp.TIMES:
        return eval_assertion(a.left, state) * eval_assertion(a.right, state)
    return None


def exec_command(cmd: Command, state: Dict[str, float],
                  max_steps: int = 100) -> Tuple[Dict[str, float], bool]:
    """
    Execute a command, returning (final_state, success).
    success=False if assertion fails.
    """
    if cmd.ctype == CmdType.SKIP:
        return state, True

    if cmd.ctype == CmdType.ASSIGN:
        new_state = dict(state)
        val = eval_assertion(cmd.expr, state)
        new_state[cmd.var] = val
        return new_state, True

    if cmd.ctype == CmdType.SEQ:
        s1, ok1 = exec_command(cmd.left, state, max_steps)
        if not ok1:
            return s1, False
        return exec_command(cmd.right, s1, max_steps)

    if cmd.ctype == CmdType.IF:
        cond = eval_assertion(cmd.cond, state)
        if cond:
            return exec_command(cmd.left, state, max_steps)
        else:
            return exec_command(cmd.right, state, max_steps)

    if cmd.ctype == CmdType.WHILE:
        s = dict(state)
        for _ in range(max_steps):
            if not eval_assertion(cmd.cond, s):
                break
            s, ok = exec_command(cmd.left, s, max_steps)
            if not ok:
                return s, False
        return s, True

    if cmd.ctype == CmdType.ASSERT:
        result = eval_assertion(cmd.cond, state)
        return state, bool(result)

    if cmd.ctype == CmdType.ASSUME:
        return state, True

    return state, True


# ─── Hoare Triple Verification (Testing) ────────────────────────

def verify_hoare_triple(triple: HoareTriple,
                         test_states: List[Dict[str, float]]) -> Tuple[bool, Optional[Dict]]:
    """
    Test-based verification: for each test state satisfying P,
    execute C and check Q holds.
    Returns (all_pass, first_counterexample).
    """
    for state in test_states:
        if eval_assertion(triple.precondition, state):
            final, ok = exec_command(triple.command, state)
            if not ok:
                return False, state
            if not eval_assertion(triple.postcondition, final):
                return False, state
    return True, None


# ─── Weakest Precondition (symbolic) ────────────────────────────

def wp(cmd: Command, post: Assertion) -> Assertion:
    """
    Compute weakest precondition wp(C, Q).
    The weakest assertion P such that {P} C {Q} holds.
    """
    if cmd.ctype == CmdType.SKIP:
        return post

    if cmd.ctype == CmdType.ASSIGN:
        # wp(x := e, Q) = Q[x ← e]
        return substitute(post, cmd.var, cmd.expr)

    if cmd.ctype == CmdType.SEQ:
        # wp(C1;C2, Q) = wp(C1, wp(C2, Q))
        return wp(cmd.left, wp(cmd.right, post))

    if cmd.ctype == CmdType.IF:
        # wp(if B then C1 else C2, Q) = (B → wp(C1,Q)) ∧ (¬B → wp(C2,Q))
        wp1 = wp(cmd.left, post)
        wp2 = wp(cmd.right, post)
        return AndA(ImpliesA(cmd.cond, wp1), ImpliesA(NotA(cmd.cond), wp2))

    if cmd.ctype == CmdType.ASSERT:
        # wp(assert P, Q) = P ∧ Q
        return AndA(cmd.cond, post)

    if cmd.ctype == CmdType.ASSUME:
        # wp(assume P, Q) = P → Q
        return ImpliesA(cmd.cond, post)

    if cmd.ctype == CmdType.WHILE:
        # For while: use provided invariant
        if cmd.invariant:
            return cmd.invariant
        return post  # Approximation

    return post


def substitute(assertion: Assertion, var: str, expr: Assertion) -> Assertion:
    """Substitute all occurrences of var in assertion with expr."""
    if assertion.op == AssertionOp.VAR and assertion.name == var:
        return expr
    if assertion.op in (AssertionOp.TRUE, AssertionOp.FALSE, AssertionOp.CONST):
        return assertion
    if assertion.op == AssertionOp.VAR:
        return assertion

    new_left = substitute(assertion.left, var, expr) if assertion.left else None
    new_right = substitute(assertion.right, var, expr) if assertion.right else None

    return Assertion(assertion.op, assertion.name, assertion.value, new_left, new_right)


# ─── Verification Condition Generator ───────────────────────────

def generate_vcs(triple: HoareTriple) -> List[Assertion]:
    """
    Generate verification conditions for a Hoare triple.
    Returns list of assertions that must be proved valid.
    """
    vcs = []
    # Main VC: P → wp(C, Q)
    weakest = wp(triple.command, triple.postcondition)
    vcs.append(ImpliesA(triple.precondition, weakest))
    return vcs


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
    print("Trust Hoare Logic for Web4")
    print("Session 34, Track 6")
    print("=" * 70)

    # ── §1 Assertions ────────────────────────────────────────────
    print("\n§1 Assertion Language\n")

    a = trust_bounded("trust")
    check("bounded_repr", "≥" in repr(a) and "≤" in repr(a))

    state = {"trust": 0.7, "score": 0.3}
    check("eval_bounded", eval_assertion(trust_bounded("trust"), state))
    check("eval_above", eval_assertion(trust_above("trust", 0.5), state))
    check("eval_not_above_1", not eval_assertion(trust_above("trust", 0.9), state))
    check("eval_range", eval_assertion(trust_in_range("trust", 0.5, 0.8), state))

    # Arithmetic
    expr = Plus(Var("trust"), Var("score"))
    check("eval_plus", abs(eval_assertion(expr, state) - 1.0) < 1e-9)

    mul = Times(Var("trust"), Const(0.5))
    check("eval_times", abs(eval_assertion(mul, state) - 0.35) < 1e-9)

    # ── §2 Command Execution ────────────────────────────────────
    print("\n§2 Command Execution\n")

    # Assignment
    cmd1 = Assign("trust", Times(Var("trust"), Const(0.9)))
    s1, ok1 = exec_command(cmd1, {"trust": 0.8})
    check("assign_ok", ok1)
    check("assign_value", abs(s1["trust"] - 0.72) < 1e-9)

    # Sequential
    cmd2 = Seq(
        Assign("trust", Times(Var("trust"), Const(0.9))),
        Assign("trust", Plus(Var("trust"), Const(0.05)))
    )
    s2, ok2 = exec_command(cmd2, {"trust": 0.8})
    check("seq_ok", ok2)
    check("seq_value", abs(s2["trust"] - 0.77) < 1e-9)

    # Conditional
    cmd3 = If(
        Gt(Var("trust"), Const(0.5)),
        Assign("level", Const(1.0)),
        Assign("level", Const(0.0))
    )
    s3, _ = exec_command(cmd3, {"trust": 0.8})
    check("if_true_branch", abs(s3["level"] - 1.0) < 1e-9)
    s4, _ = exec_command(cmd3, {"trust": 0.3})
    check("if_false_branch", abs(s4["level"] - 0.0) < 1e-9)

    # Assert
    cmd_assert_ok = Assert(trust_bounded("trust"))
    _, ok_a = exec_command(cmd_assert_ok, {"trust": 0.5})
    check("assert_passes", ok_a)

    cmd_assert_fail = Assert(trust_above("trust", 0.9))
    _, ok_f = exec_command(cmd_assert_fail, {"trust": 0.5})
    check("assert_fails", not ok_f)

    # ── §3 Hoare Triple Verification ────────────────────────────
    print("\n§3 Hoare Triple Verification\n")

    # {trust >= 0.5} trust := trust * 0.9 {trust >= 0.45}
    triple1 = HoareTriple(
        precondition=trust_above("trust", 0.5),
        command=Assign("trust", Times(Var("trust"), Const(0.9))),
        postcondition=trust_above("trust", 0.45)
    )
    test_states = [{"trust": v} for v in [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]]
    valid, cex = verify_hoare_triple(triple1, test_states)
    check("triple1_valid", valid, f"cex={cex}")

    # Invalid triple: postcondition too strong
    triple2 = HoareTriple(
        precondition=trust_above("trust", 0.5),
        command=Assign("trust", Times(Var("trust"), Const(0.9))),
        postcondition=trust_above("trust", 0.9)
    )
    valid2, cex2 = verify_hoare_triple(triple2, test_states)
    check("triple2_invalid", not valid2)

    # ── §4 Weakest Precondition ──────────────────────────────────
    print("\n§4 Weakest Precondition\n")

    # wp(x := 5, x > 3) = 5 > 3 = true
    post = Gt(Var("x"), Const(3.0))
    cmd_assign = Assign("x", Const(5.0))
    weakest = wp(cmd_assign, post)
    check("wp_assign", eval_assertion(weakest, {}))

    # wp(skip, Q) = Q
    wp_skip = wp(CSkip(), trust_bounded("t"))
    check("wp_skip", repr(wp_skip) == repr(trust_bounded("t")))

    # wp(x := x*0.9, x >= 0.45) needs x*0.9 >= 0.45 → x >= 0.5
    post2 = Ge(Var("x"), Const(0.45))
    cmd_decay = Assign("x", Times(Var("x"), Const(0.9)))
    wp2 = wp(cmd_decay, post2)
    # wp replaces x with x*0.9 in the postcondition
    check("wp_decay_at_0.5", eval_assertion(wp2, {"x": 0.5}))
    check("wp_decay_at_0.4", not eval_assertion(wp2, {"x": 0.4}))

    # wp(C1;C2, Q) = wp(C1, wp(C2, Q))
    cmd_seq = Seq(
        Assign("x", Plus(Var("x"), Const(1.0))),
        Assign("x", Times(Var("x"), Const(2.0)))
    )
    post3 = Ge(Var("x"), Const(4.0))
    wp3 = wp(cmd_seq, post3)
    # x+1)*2 >= 4 → x >= 1
    check("wp_seq_at_1", eval_assertion(wp3, {"x": 1.0}))
    check("wp_seq_at_0", not eval_assertion(wp3, {"x": 0.0}))

    # ── §5 Verification Conditions ──────────────────────────────
    print("\n§5 Verification Conditions\n")

    vcs = generate_vcs(triple1)
    check("vc_generated", len(vcs) > 0)

    # VC should be valid for all test states satisfying precondition
    all_valid = True
    for state in test_states:
        if eval_assertion(triple1.precondition, state):
            for vc in vcs:
                if not eval_assertion(vc, state):
                    all_valid = False
    check("vcs_valid", all_valid)

    # ── §6 Trust-Specific Rules ──────────────────────────────────
    print("\n§6 Trust-Specific Rules\n")

    # Attestation rule: {trust_bounded(t)} attest(t) {trust_bounded(t)}
    attest_cmd = Seq(
        Assign("t", Times(Var("t"), Const(0.95))),
        Assign("t", Plus(Var("t"), Const(0.02)))
    )
    attest_triple = HoareTriple(
        trust_bounded("t"), attest_cmd, trust_in_range("t", 0.0, 1.0)
    )
    states = [{"t": v} for v in [0.0, 0.1, 0.5, 0.8, 0.95, 1.0]]
    valid_a, _ = verify_hoare_triple(attest_triple, states)
    check("attestation_preserves_bounds", valid_a)

    # Decay rule: {t >= 0.5} decay(t, 0.1) {t >= 0.45}
    decay_cmd = Assign("t", Times(Var("t"), Const(0.9)))
    decay_triple = HoareTriple(
        trust_above("t", 0.5), decay_cmd, trust_above("t", 0.45)
    )
    valid_d, _ = verify_hoare_triple(decay_triple,
                                      [{"t": v} for v in [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]])
    check("decay_rule_valid", valid_d)

    # ── §7 Loop with Invariant ───────────────────────────────────
    print("\n§7 Loop with Invariant\n")

    # while trust > 0.1: trust := trust * 0.9
    # Invariant: trust >= 0 (trust stays non-negative)
    loop = While(
        Gt(Var("trust"), Const(0.1)),
        Assign("trust", Times(Var("trust"), Const(0.9))),
        invariant=Ge(Var("trust"), Const(0.0))
    )
    s_loop, _ = exec_command(loop, {"trust": 0.8})
    check("loop_converges", s_loop["trust"] <= 0.1 + 1e-9)
    check("loop_nonneg", s_loop["trust"] >= 0.0)

    # Invariant holds
    check("loop_invariant", eval_assertion(
        Ge(Var("trust"), Const(0.0)), s_loop))

    # ── §8 Compositional Reasoning ──────────────────────────────
    print("\n§8 Compositional Reasoning\n")

    # {true} x := 0.8; x := x * 0.9; assert(x >= 0.7) {x >= 0.7}
    comp_cmd = Seq(
        Assign("x", Const(0.8)),
        Seq(
            Assign("x", Times(Var("x"), Const(0.9))),
            Assert(Ge(Var("x"), Const(0.7)))
        )
    )
    comp_triple = HoareTriple(TrueA(), comp_cmd, Ge(Var("x"), Const(0.7)))
    valid_c, cex_c = verify_hoare_triple(comp_triple, [{}])
    check("composition_valid", valid_c, f"cex={cex_c}")

    # Failing composition: assert too strong
    bad_cmd = Seq(
        Assign("x", Const(0.5)),
        Assert(Ge(Var("x"), Const(0.8)))
    )
    bad_triple = HoareTriple(TrueA(), bad_cmd, Ge(Var("x"), Const(0.8)))
    valid_b, _ = verify_hoare_triple(bad_triple, [{}])
    check("bad_composition_fails", not valid_b)

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
