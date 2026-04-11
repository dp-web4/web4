"""
Trust Contract DSL for Web4
Session 32, Track 3

A domain-specific language for expressing trust policies:
- Contract AST (abstract syntax tree)
- Policy expression types (threshold, range, composite)
- Logical operators (AND, OR, NOT, IMPLIES)
- Quantified policies (FORALL, EXISTS over entity sets)
- Contract type checking and validation
- Contract composition (sequential, parallel, conditional)
- Contract evaluation against trust context
- Contract normalization and optimization
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional, Union, Set
from abc import ABC, abstractmethod


# ─── AST Node Types ──────────────────────────────────────────────

class ExprType(Enum):
    BOOL = "bool"
    FLOAT = "float"
    ENTITY = "entity"
    ACTION = "action"
    VOID = "void"


@dataclass
class TypeInfo:
    expr_type: ExprType
    nullable: bool = False


# ─── AST Nodes ────────────────────────────────────────────────────

class Expr(ABC):
    @abstractmethod
    def evaluate(self, context: 'TrustContext') -> any:
        pass

    @abstractmethod
    def type_check(self) -> TypeInfo:
        pass


@dataclass
class TrustThreshold(Expr):
    """Check if entity's trust >= threshold."""
    entity: str
    dimension: str  # "talent", "training", "temperament", or "overall"
    threshold: float

    def evaluate(self, context: 'TrustContext') -> bool:
        trust = context.get_trust(self.entity, self.dimension)
        return trust >= self.threshold

    def type_check(self) -> TypeInfo:
        return TypeInfo(ExprType.BOOL)


@dataclass
class TrustRange(Expr):
    """Check if entity's trust is within [low, high]."""
    entity: str
    dimension: str
    low: float
    high: float

    def evaluate(self, context: 'TrustContext') -> bool:
        trust = context.get_trust(self.entity, self.dimension)
        return self.low <= trust <= self.high

    def type_check(self) -> TypeInfo:
        return TypeInfo(ExprType.BOOL)


@dataclass
class TrustValue(Expr):
    """Get entity's trust value."""
    entity: str
    dimension: str

    def evaluate(self, context: 'TrustContext') -> float:
        return context.get_trust(self.entity, self.dimension)

    def type_check(self) -> TypeInfo:
        return TypeInfo(ExprType.FLOAT)


@dataclass
class Literal(Expr):
    value: any
    lit_type: ExprType

    def evaluate(self, context: 'TrustContext') -> any:
        return self.value

    def type_check(self) -> TypeInfo:
        return TypeInfo(self.lit_type)


@dataclass
class And(Expr):
    left: Expr
    right: Expr

    def evaluate(self, context: 'TrustContext') -> bool:
        return self.left.evaluate(context) and self.right.evaluate(context)

    def type_check(self) -> TypeInfo:
        lt = self.left.type_check()
        rt = self.right.type_check()
        if lt.expr_type != ExprType.BOOL or rt.expr_type != ExprType.BOOL:
            raise TypeError(f"AND requires bool operands, got {lt.expr_type} and {rt.expr_type}")
        return TypeInfo(ExprType.BOOL)


@dataclass
class Or(Expr):
    left: Expr
    right: Expr

    def evaluate(self, context: 'TrustContext') -> bool:
        return self.left.evaluate(context) or self.right.evaluate(context)

    def type_check(self) -> TypeInfo:
        lt = self.left.type_check()
        rt = self.right.type_check()
        if lt.expr_type != ExprType.BOOL or rt.expr_type != ExprType.BOOL:
            raise TypeError(f"OR requires bool operands, got {lt.expr_type} and {rt.expr_type}")
        return TypeInfo(ExprType.BOOL)


@dataclass
class Not(Expr):
    operand: Expr

    def evaluate(self, context: 'TrustContext') -> bool:
        return not self.operand.evaluate(context)

    def type_check(self) -> TypeInfo:
        ot = self.operand.type_check()
        if ot.expr_type != ExprType.BOOL:
            raise TypeError(f"NOT requires bool operand, got {ot.expr_type}")
        return TypeInfo(ExprType.BOOL)


@dataclass
class Implies(Expr):
    """Logical implication: antecedent → consequent."""
    antecedent: Expr
    consequent: Expr

    def evaluate(self, context: 'TrustContext') -> bool:
        a = self.antecedent.evaluate(context)
        c = self.consequent.evaluate(context)
        return (not a) or c  # P → Q ≡ ¬P ∨ Q

    def type_check(self) -> TypeInfo:
        at = self.antecedent.type_check()
        ct = self.consequent.type_check()
        if at.expr_type != ExprType.BOOL or ct.expr_type != ExprType.BOOL:
            raise TypeError("IMPLIES requires bool operands")
        return TypeInfo(ExprType.BOOL)


@dataclass
class Compare(Expr):
    """Compare two float expressions."""
    left: Expr
    op: str  # ">", ">=", "<", "<=", "==", "!="
    right: Expr

    def evaluate(self, context: 'TrustContext') -> bool:
        lv = self.left.evaluate(context)
        rv = self.right.evaluate(context)
        ops = {
            ">": lambda a, b: a > b,
            ">=": lambda a, b: a >= b,
            "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b,
            "==": lambda a, b: abs(a - b) < 1e-10,
            "!=": lambda a, b: abs(a - b) >= 1e-10,
        }
        return ops[self.op](lv, rv)

    def type_check(self) -> TypeInfo:
        lt = self.left.type_check()
        rt = self.right.type_check()
        if lt.expr_type != ExprType.FLOAT or rt.expr_type != ExprType.FLOAT:
            raise TypeError(f"Compare requires float operands, got {lt.expr_type} and {rt.expr_type}")
        return TypeInfo(ExprType.BOOL)


@dataclass
class ForAll(Expr):
    """Universal quantifier over entity set."""
    entity_set: str  # name of entity set in context
    variable: str    # bound variable name
    body: Expr

    def evaluate(self, context: 'TrustContext') -> bool:
        entities = context.get_entity_set(self.entity_set)
        for entity in entities:
            sub_context = context.bind(self.variable, entity)
            if not self.body.evaluate(sub_context):
                return False
        return True

    def type_check(self) -> TypeInfo:
        bt = self.body.type_check()
        if bt.expr_type != ExprType.BOOL:
            raise TypeError("ForAll body must be bool")
        return TypeInfo(ExprType.BOOL)


@dataclass
class Exists(Expr):
    """Existential quantifier over entity set."""
    entity_set: str
    variable: str
    body: Expr

    def evaluate(self, context: 'TrustContext') -> bool:
        entities = context.get_entity_set(self.entity_set)
        for entity in entities:
            sub_context = context.bind(self.variable, entity)
            if self.body.evaluate(sub_context):
                return True
        return False

    def type_check(self) -> TypeInfo:
        bt = self.body.type_check()
        if bt.expr_type != ExprType.BOOL:
            raise TypeError("Exists body must be bool")
        return TypeInfo(ExprType.BOOL)


# ─── Trust Context ────────────────────────────────────────────────

@dataclass
class TrustContext:
    """Runtime context for evaluating trust contracts."""
    trust_scores: Dict[str, Dict[str, float]] = field(default_factory=dict)
    entity_sets: Dict[str, List[str]] = field(default_factory=dict)
    bindings: Dict[str, str] = field(default_factory=dict)

    def set_trust(self, entity: str, dimension: str, value: float):
        if entity not in self.trust_scores:
            self.trust_scores[entity] = {}
        self.trust_scores[entity][dimension] = value

    def get_trust(self, entity_or_var: str, dimension: str) -> float:
        # Resolve variable binding
        entity = self.bindings.get(entity_or_var, entity_or_var)
        return self.trust_scores.get(entity, {}).get(dimension, 0.0)

    def get_entity_set(self, name: str) -> List[str]:
        return self.entity_sets.get(name, [])

    def bind(self, variable: str, value: str) -> 'TrustContext':
        """Create new context with additional variable binding."""
        new_ctx = TrustContext(
            trust_scores=self.trust_scores,
            entity_sets=self.entity_sets,
            bindings={**self.bindings, variable: value}
        )
        return new_ctx


# ─── Contract ─────────────────────────────────────────────────────

@dataclass
class Contract:
    """A named, typed trust contract."""
    name: str
    description: str
    preconditions: List[Expr] = field(default_factory=list)
    body: Expr = None
    postconditions: List[Expr] = field(default_factory=list)

    def type_check(self) -> bool:
        """Validate all expressions are well-typed."""
        try:
            for pre in self.preconditions:
                t = pre.type_check()
                if t.expr_type != ExprType.BOOL:
                    return False
            if self.body:
                self.body.type_check()
            for post in self.postconditions:
                t = post.type_check()
                if t.expr_type != ExprType.BOOL:
                    return False
            return True
        except TypeError:
            return False

    def evaluate(self, context: TrustContext) -> Dict[str, any]:
        """Evaluate contract against context."""
        result = {
            "name": self.name,
            "preconditions_met": True,
            "body_result": None,
            "postconditions_met": True,
            "all_satisfied": True,
        }

        # Check preconditions
        for i, pre in enumerate(self.preconditions):
            if not pre.evaluate(context):
                result["preconditions_met"] = False
                result["all_satisfied"] = False
                result["failed_precondition"] = i
                return result

        # Evaluate body
        if self.body:
            result["body_result"] = self.body.evaluate(context)

        # Check postconditions
        for i, post in enumerate(self.postconditions):
            if not post.evaluate(context):
                result["postconditions_met"] = False
                result["all_satisfied"] = False
                result["failed_postcondition"] = i
                return result

        return result


# ─── Contract Composition ─────────────────────────────────────────

def sequential_compose(c1: Contract, c2: Contract) -> Contract:
    """c1 THEN c2: both must pass, c1's postconditions are c2's preconditions."""
    return Contract(
        name=f"{c1.name} >> {c2.name}",
        description=f"Sequential: {c1.description} then {c2.description}",
        preconditions=c1.preconditions,
        body=And(c1.body, c2.body) if c1.body and c2.body else (c1.body or c2.body),
        postconditions=c2.postconditions,
    )


def parallel_compose(c1: Contract, c2: Contract) -> Contract:
    """c1 AND c2: both must pass independently."""
    return Contract(
        name=f"{c1.name} & {c2.name}",
        description=f"Parallel: {c1.description} and {c2.description}",
        preconditions=c1.preconditions + c2.preconditions,
        body=And(c1.body, c2.body) if c1.body and c2.body else (c1.body or c2.body),
        postconditions=c1.postconditions + c2.postconditions,
    )


def conditional_compose(condition: Expr, c_true: Contract, c_false: Contract) -> Contract:
    """IF condition THEN c_true ELSE c_false."""
    body_expr = Or(
        And(condition, c_true.body) if c_true.body else condition,
        And(Not(condition), c_false.body) if c_false.body else Not(condition),
    )
    return Contract(
        name=f"if ? {c_true.name} : {c_false.name}",
        description=f"Conditional: {c_true.description} or {c_false.description}",
        preconditions=[],
        body=body_expr,
        postconditions=[],
    )


# ─── Expression Normalization ─────────────────────────────────────

def normalize(expr: Expr) -> Expr:
    """Simplify expression (constant folding, double negation elimination)."""
    if isinstance(expr, Not):
        inner = normalize(expr.operand)
        # ¬¬P = P
        if isinstance(inner, Not):
            return inner.operand
        # ¬True = False, ¬False = True
        if isinstance(inner, Literal) and inner.lit_type == ExprType.BOOL:
            return Literal(not inner.value, ExprType.BOOL)
        return Not(inner)

    if isinstance(expr, And):
        left = normalize(expr.left)
        right = normalize(expr.right)
        # P ∧ True = P
        if isinstance(left, Literal) and left.lit_type == ExprType.BOOL:
            return right if left.value else Literal(False, ExprType.BOOL)
        if isinstance(right, Literal) and right.lit_type == ExprType.BOOL:
            return left if right.value else Literal(False, ExprType.BOOL)
        return And(left, right)

    if isinstance(expr, Or):
        left = normalize(expr.left)
        right = normalize(expr.right)
        # P ∨ False = P
        if isinstance(left, Literal) and left.lit_type == ExprType.BOOL:
            return Literal(True, ExprType.BOOL) if left.value else right
        if isinstance(right, Literal) and right.lit_type == ExprType.BOOL:
            return Literal(True, ExprType.BOOL) if right.value else left
        return Or(left, right)

    return expr


# ─── Expression Size ─────────────────────────────────────────────

def expr_size(expr: Expr) -> int:
    """Count AST nodes."""
    if isinstance(expr, (TrustThreshold, TrustRange, TrustValue, Literal)):
        return 1
    if isinstance(expr, (Not,)):
        return 1 + expr_size(expr.operand)
    if isinstance(expr, (And, Or, Implies, Compare)):
        return 1 + expr_size(expr.left) + expr_size(expr.right)
    if isinstance(expr, (ForAll, Exists)):
        return 1 + expr_size(expr.body)
    return 1


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
    print("Trust Contract DSL for Web4")
    print("Session 32, Track 3")
    print("=" * 70)

    # ── §1 Basic Expressions ───────────────────────────────────
    print("\n§1 Basic Expressions\n")

    ctx = TrustContext()
    ctx.set_trust("alice", "overall", 0.8)
    ctx.set_trust("alice", "talent", 0.9)
    ctx.set_trust("bob", "overall", 0.4)

    # Threshold
    high = TrustThreshold("alice", "overall", 0.7)
    check("threshold_pass", high.evaluate(ctx))

    low = TrustThreshold("bob", "overall", 0.5)
    check("threshold_fail", not low.evaluate(ctx))

    # Range
    rng = TrustRange("alice", "overall", 0.5, 0.9)
    check("range_pass", rng.evaluate(ctx))

    # Value
    val = TrustValue("alice", "talent")
    check("value_correct", abs(val.evaluate(ctx) - 0.9) < 0.01)

    # ── §2 Logical Operators ───────────────────────────────────
    print("\n§2 Logical Operators\n")

    # AND
    both = And(
        TrustThreshold("alice", "overall", 0.7),
        TrustThreshold("bob", "overall", 0.3),
    )
    check("and_both_true", both.evaluate(ctx))

    both_fail = And(
        TrustThreshold("alice", "overall", 0.7),
        TrustThreshold("bob", "overall", 0.5),
    )
    check("and_one_false", not both_fail.evaluate(ctx))

    # OR
    either = Or(
        TrustThreshold("alice", "overall", 0.9),  # fail
        TrustThreshold("bob", "overall", 0.3),     # pass
    )
    check("or_one_true", either.evaluate(ctx))

    # NOT
    negated = Not(TrustThreshold("bob", "overall", 0.5))
    check("not_inverts", negated.evaluate(ctx))

    # IMPLIES
    impl = Implies(
        TrustThreshold("alice", "overall", 0.7),   # true
        TrustThreshold("alice", "talent", 0.8),     # true
    )
    check("implies_tt", impl.evaluate(ctx))

    impl_ft = Implies(
        TrustThreshold("alice", "overall", 0.95),   # false
        TrustThreshold("bob", "overall", 0.99),      # false
    )
    check("implies_false_antecedent", impl_ft.evaluate(ctx))  # F → F = T

    # ── §3 Type Checking ───────────────────────────────────────
    print("\n§3 Type Checking\n")

    # Well-typed
    check("threshold_type", TrustThreshold("a", "o", 0.5).type_check().expr_type == ExprType.BOOL)
    check("value_type", TrustValue("a", "o").type_check().expr_type == ExprType.FLOAT)

    # And requires bool operands
    good_and = And(TrustThreshold("a", "o", 0.5), TrustThreshold("b", "o", 0.5))
    check("and_well_typed", good_and.type_check().expr_type == ExprType.BOOL)

    bad_and = And(TrustValue("a", "o"), TrustThreshold("b", "o", 0.5))
    try:
        bad_and.type_check()
        check("and_bad_type_caught", False, "should have raised TypeError")
    except TypeError:
        check("and_bad_type_caught", True)

    # Compare requires float operands
    good_cmp = Compare(TrustValue("a", "o"), ">", TrustValue("b", "o"))
    check("compare_well_typed", good_cmp.type_check().expr_type == ExprType.BOOL)

    # ── §4 Quantifiers ─────────────────────────────────────────
    print("\n§4 Quantifiers\n")

    ctx.set_trust("carol", "overall", 0.6)
    ctx.entity_sets["team"] = ["alice", "bob", "carol"]

    # ForAll: all team members have trust > 0.3
    all_trusted = ForAll("team", "x",
                          TrustThreshold("x", "overall", 0.3))
    check("forall_pass", all_trusted.evaluate(ctx))

    # ForAll: all team members have trust > 0.5
    all_high = ForAll("team", "x",
                       TrustThreshold("x", "overall", 0.5))
    check("forall_fail", not all_high.evaluate(ctx))  # bob = 0.4

    # Exists: some team member has trust > 0.7
    some_high = Exists("team", "x",
                        TrustThreshold("x", "overall", 0.7))
    check("exists_pass", some_high.evaluate(ctx))

    # Exists: some team member has trust > 0.9
    some_very_high = Exists("team", "x",
                             TrustThreshold("x", "overall", 0.9))
    check("exists_fail", not some_very_high.evaluate(ctx))

    # ── §5 Contracts ───────────────────────────────────────────
    print("\n§5 Contract Evaluation\n")

    access_contract = Contract(
        name="data_access",
        description="Require minimum trust for data access",
        preconditions=[
            TrustThreshold("alice", "overall", 0.5),
        ],
        body=And(
            TrustThreshold("alice", "talent", 0.7),
            TrustRange("alice", "overall", 0.6, 1.0),
        ),
        postconditions=[],
    )

    result = access_contract.evaluate(ctx)
    check("contract_passes", result["all_satisfied"])
    check("contract_body_true", result["body_result"] is True)

    # Contract with failing precondition
    strict_contract = Contract(
        name="admin_access",
        description="Require admin-level trust",
        preconditions=[TrustThreshold("bob", "overall", 0.9)],
        body=Literal(True, ExprType.BOOL),
    )
    result_fail = strict_contract.evaluate(ctx)
    check("contract_precond_fails", not result_fail["preconditions_met"])

    # Type checking
    check("contract_type_valid", access_contract.type_check())

    # ── §6 Contract Composition ─────────────────────────────────
    print("\n§6 Contract Composition\n")

    c1 = Contract("auth", "Authentication",
                   body=TrustThreshold("alice", "overall", 0.5))
    c2 = Contract("access", "Authorization",
                   body=TrustThreshold("alice", "talent", 0.7))

    # Sequential
    seq = sequential_compose(c1, c2)
    check("seq_name", ">>" in seq.name)
    seq_result = seq.evaluate(ctx)
    check("seq_passes", seq_result["body_result"] is True)

    # Parallel
    par = parallel_compose(c1, c2)
    check("par_name", "&" in par.name)
    par_result = par.evaluate(ctx)
    check("par_passes", par_result["body_result"] is True)

    # Conditional
    cond = conditional_compose(
        TrustThreshold("alice", "overall", 0.7),
        c1, c2
    )
    cond_result = cond.evaluate(ctx)
    check("cond_evaluates", cond_result["body_result"] is not None)

    # ── §7 Normalization ───────────────────────────────────────
    print("\n§7 Expression Normalization\n")

    # Double negation elimination
    double_neg = Not(Not(TrustThreshold("alice", "overall", 0.5)))
    normalized = normalize(double_neg)
    check("double_neg_eliminated", isinstance(normalized, TrustThreshold))

    # AND with True
    and_true = And(Literal(True, ExprType.BOOL), TrustThreshold("alice", "overall", 0.5))
    norm_and = normalize(and_true)
    check("and_true_simplified", isinstance(norm_and, TrustThreshold))

    # OR with False
    or_false = Or(Literal(False, ExprType.BOOL), TrustThreshold("alice", "overall", 0.5))
    norm_or = normalize(or_false)
    check("or_false_simplified", isinstance(norm_or, TrustThreshold))

    # ── §8 Expression Size ─────────────────────────────────────
    print("\n§8 Expression Size\n")

    simple = TrustThreshold("a", "o", 0.5)
    check("size_leaf", expr_size(simple) == 1)

    compound = And(
        TrustThreshold("a", "o", 0.5),
        Or(TrustThreshold("b", "o", 0.3),
           Not(TrustThreshold("c", "o", 0.7)))
    )
    check("size_compound", expr_size(compound) == 6,
          f"size={expr_size(compound)}")

    # ── Summary ─────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
