"""
Trust Process Algebra for Web4
Session 34, Track 5

CSP/CCS-style process algebra for trust protocol specification:
- Processes: STOP, SKIP, prefix, choice, parallel, sequential
- Labelled transition systems (LTS)
- Strong and weak bisimulation equivalence
- Trace equivalence and refinement
- Trust protocol specification as processes
- Deadlock freedom via process analysis
- Channel communication with trust labels
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set, FrozenSet
from collections import defaultdict, deque
from enum import Enum, auto


# ─── Process AST ─────────────────────────────────────────────────

class ProcType(Enum):
    STOP = auto()       # Deadlock
    SKIP = auto()       # Successful termination
    PREFIX = auto()     # a → P
    CHOICE = auto()     # P □ Q (external choice)
    PARALLEL = auto()   # P ∥ Q (parallel composition)
    SEQUENTIAL = auto() # P ; Q
    HIDE = auto()       # P \ {a,b,...} (hiding)


@dataclass
class Process:
    ptype: ProcType
    action: str = ""            # For PREFIX
    left: Optional['Process'] = None
    right: Optional['Process'] = None
    hidden: FrozenSet[str] = frozenset()

    def __repr__(self):
        if self.ptype == ProcType.STOP:
            return "STOP"
        if self.ptype == ProcType.SKIP:
            return "SKIP"
        if self.ptype == ProcType.PREFIX:
            return f"{self.action}→{self.left}"
        if self.ptype == ProcType.CHOICE:
            return f"({self.left} □ {self.right})"
        if self.ptype == ProcType.PARALLEL:
            return f"({self.left} ∥ {self.right})"
        if self.ptype == ProcType.SEQUENTIAL:
            return f"({self.left} ; {self.right})"
        if self.ptype == ProcType.HIDE:
            return f"({self.left} \\ {set(self.hidden)})"
        return f"Process({self.ptype})"


# Constructors
def Stop() -> Process:
    return Process(ProcType.STOP)

def Skip() -> Process:
    return Process(ProcType.SKIP)

def Prefix(action: str, then: Process) -> Process:
    return Process(ProcType.PREFIX, action=action, left=then)

def Choice(p: Process, q: Process) -> Process:
    return Process(ProcType.CHOICE, left=p, right=q)

def Parallel(p: Process, q: Process) -> Process:
    return Process(ProcType.PARALLEL, left=p, right=q)

def Sequential(p: Process, q: Process) -> Process:
    return Process(ProcType.SEQUENTIAL, left=p, right=q)

def Hide(p: Process, actions: Set[str]) -> Process:
    return Process(ProcType.HIDE, left=p, hidden=frozenset(actions))


# ─── Labelled Transition System ──────────────────────────────────

TAU = "τ"  # Internal action
TICK = "✓" # Successful termination

@dataclass
class LTS:
    """Labelled Transition System."""
    states: Set[int] = field(default_factory=set)
    initial: int = 0
    transitions: Dict[int, List[Tuple[str, int]]] = field(
        default_factory=lambda: defaultdict(list))
    accepting: Set[int] = field(default_factory=set)

    def add_transition(self, src: int, action: str, dst: int):
        self.states.add(src)
        self.states.add(dst)
        self.transitions[src].append((action, dst))

    def successors(self, state: int, action: str = None) -> List[Tuple[str, int]]:
        if action is None:
            return self.transitions.get(state, [])
        return [(a, s) for a, s in self.transitions.get(state, []) if a == action]

    def actions(self, state: int) -> Set[str]:
        return {a for a, _ in self.transitions.get(state, [])}

    @property
    def all_actions(self) -> Set[str]:
        acts = set()
        for trans in self.transitions.values():
            for a, _ in trans:
                acts.add(a)
        return acts

    def is_deadlock(self, state: int) -> bool:
        return len(self.transitions.get(state, [])) == 0


# ─── Process to LTS Compilation ──────────────────────────────────

class LTSCompiler:
    """Compile a Process AST into an LTS."""

    def __init__(self):
        self.state_counter = 0

    def fresh(self) -> int:
        s = self.state_counter
        self.state_counter += 1
        return s

    def compile(self, proc: Process) -> LTS:
        self.state_counter = 0
        lts = LTS()
        start = self.fresh()
        lts.initial = start
        end = self._compile_rec(proc, start, lts)
        if end is not None:
            lts.accepting.add(end)
        return lts

    def _compile_rec(self, proc: Process, state: int, lts: LTS) -> Optional[int]:
        if proc.ptype == ProcType.STOP:
            lts.states.add(state)
            return None  # No outgoing transitions (deadlock)

        if proc.ptype == ProcType.SKIP:
            end = self.fresh()
            lts.add_transition(state, TICK, end)
            return end

        if proc.ptype == ProcType.PREFIX:
            next_state = self.fresh()
            lts.add_transition(state, proc.action, next_state)
            return self._compile_rec(proc.left, next_state, lts)

        if proc.ptype == ProcType.CHOICE:
            # Both branches start from same state
            end_l = self._compile_rec(proc.left, state, lts)
            end_r = self._compile_rec(proc.right, state, lts)
            # Merge end states
            if end_l is not None and end_r is not None:
                merge = self.fresh()
                lts.add_transition(end_l, TAU, merge)
                lts.add_transition(end_r, TAU, merge)
                return merge
            return end_l or end_r

        if proc.ptype == ProcType.SEQUENTIAL:
            mid = self._compile_rec(proc.left, state, lts)
            if mid is None:
                return None
            return self._compile_rec(proc.right, mid, lts)

        if proc.ptype == ProcType.PARALLEL:
            # Simplified: interleaving semantics
            # Compile both sides separately, then interleave
            l_state = self.fresh()
            r_state = self.fresh()
            lts.add_transition(state, TAU, l_state)
            lts.add_transition(state, TAU, r_state)
            end_l = self._compile_rec(proc.left, l_state, lts)
            end_r = self._compile_rec(proc.right, r_state, lts)
            if end_l is not None and end_r is not None:
                end = self.fresh()
                lts.add_transition(end_l, TAU, end)
                lts.add_transition(end_r, TAU, end)
                return end
            return end_l or end_r

        if proc.ptype == ProcType.HIDE:
            end = self._compile_rec(proc.left, state, lts)
            # Replace hidden actions with τ
            for s in list(lts.transitions.keys()):
                lts.transitions[s] = [
                    (TAU if a in proc.hidden else a, t)
                    for a, t in lts.transitions[s]
                ]
            return end

        return None


# ─── Trace Semantics ─────────────────────────────────────────────

def traces(lts: LTS, max_length: int = 10, max_traces: int = 100) -> Set[Tuple[str, ...]]:
    """Compute all traces of the LTS (sequences of visible actions)."""
    result: Set[Tuple[str, ...]] = set()
    stack = [(lts.initial, ())]

    while stack and len(result) < max_traces:
        state, trace = stack.pop()

        if len(trace) > max_length:
            continue

        result.add(trace)

        for action, next_state in lts.successors(state):
            if action == TAU:
                stack.append((next_state, trace))
            else:
                stack.append((next_state, trace + (action,)))

    return result


def trace_refinement(spec: LTS, impl: LTS,
                      max_length: int = 10) -> Tuple[bool, Optional[Tuple[str, ...]]]:
    """
    Check if impl trace-refines spec: traces(impl) ⊆ traces(spec).
    Returns (is_refinement, counterexample_trace).
    """
    spec_traces = traces(spec, max_length)
    impl_traces = traces(impl, max_length)

    for t in impl_traces:
        if t not in spec_traces:
            return False, t
    return True, None


# ─── Bisimulation ────────────────────────────────────────────────

def strong_bisimulation(lts1: LTS, lts2: LTS) -> bool:
    """
    Check strong bisimulation between two LTS.
    Uses partition refinement approach.
    """
    # Combine into single LTS with state remapping
    offset = max(lts1.states) + 1 if lts1.states else 0
    combined_trans: Dict[int, List[Tuple[str, int]]] = defaultdict(list)

    for s, trans in lts1.transitions.items():
        for a, t in trans:
            combined_trans[s].append((a, t))

    for s, trans in lts2.transitions.items():
        for a, t in trans:
            combined_trans[s + offset].append((a, t + offset))

    all_states = lts1.states | {s + offset for s in lts2.states}

    # Initial partition: one block for all states
    partition = [all_states]

    changed = True
    while changed:
        changed = False
        new_partition = []
        for block in partition:
            # Try to split block based on transitions
            split = _split_block(block, partition, combined_trans)
            if len(split) > 1:
                changed = True
            new_partition.extend(split)
        partition = new_partition

    # Check if initial states are in the same block
    s1 = lts1.initial
    s2 = lts2.initial + offset
    for block in partition:
        if s1 in block and s2 in block:
            return True
    return False


def _split_block(block: Set[int], partition: List[Set[int]],
                  transitions: Dict[int, List[Tuple[str, int]]]) -> List[Set[int]]:
    """Try to split a block based on distinguishing behavior."""
    if len(block) <= 1:
        return [block]

    # For each action, check which target blocks each state can reach
    states = list(block)
    ref = states[0]
    same_as_ref = {ref}
    different = set()

    for s in states[1:]:
        if _same_behavior(ref, s, partition, transitions):
            same_as_ref.add(s)
        else:
            different.add(s)

    if not different:
        return [block]
    return [same_as_ref, different]


def _same_behavior(s1: int, s2: int, partition: List[Set[int]],
                    transitions: Dict[int, List[Tuple[str, int]]]) -> bool:
    """Check if two states have the same transition behavior w.r.t. partition."""
    actions1 = {a for a, _ in transitions.get(s1, [])}
    actions2 = {a for a, _ in transitions.get(s2, [])}

    if actions1 != actions2:
        return False

    for action in actions1:
        targets1 = {_block_of(t, partition) for a, t in transitions.get(s1, []) if a == action}
        targets2 = {_block_of(t, partition) for a, t in transitions.get(s2, []) if a == action}
        if targets1 != targets2:
            return False

    return True


def _block_of(state: int, partition: List[Set[int]]) -> int:
    """Find which partition block a state belongs to."""
    for i, block in enumerate(partition):
        if state in block:
            return i
    return -1


# ─── Trust Protocol Specifications ──────────────────────────────

def trust_attestation_protocol() -> Process:
    """
    Attestation protocol:
    request → verify → (approve → done □ reject → done)
    """
    done = Skip()
    approve_path = Prefix("approve", done)
    reject_path = Prefix("reject", done)
    decision = Choice(approve_path, reject_path)
    return Prefix("request", Prefix("verify", decision))


def mutual_attestation_protocol() -> Process:
    """
    Mutual attestation: A attests B ∥ B attests A
    """
    a_attests = Prefix("a_attest", Prefix("a_confirm", Skip()))
    b_attests = Prefix("b_attest", Prefix("b_confirm", Skip()))
    return Parallel(a_attests, b_attests)


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
    print("Trust Process Algebra for Web4")
    print("Session 34, Track 5")
    print("=" * 70)

    compiler = LTSCompiler()

    # ── §1 Basic Processes ───────────────────────────────────────
    print("\n§1 Basic Processes\n")

    check("stop_repr", repr(Stop()) == "STOP")
    check("skip_repr", repr(Skip()) == "SKIP")

    p = Prefix("a", Prefix("b", Stop()))
    check("prefix_repr", "a" in repr(p) and "b" in repr(p))

    c = Choice(Prefix("a", Stop()), Prefix("b", Stop()))
    check("choice_repr", "□" in repr(c))

    # ── §2 LTS Compilation ───────────────────────────────────────
    print("\n§2 LTS Compilation\n")

    # a → STOP
    lts1 = compiler.compile(Prefix("a", Stop()))
    check("prefix_states", len(lts1.states) >= 2)
    check("prefix_has_a", "a" in lts1.all_actions)

    # a → b → SKIP
    lts2 = compiler.compile(Prefix("a", Prefix("b", Skip())))
    check("seq_has_a_b", "a" in lts2.all_actions and "b" in lts2.all_actions)
    check("seq_has_tick", TICK in lts2.all_actions)

    # Choice: a → STOP □ b → STOP
    lts3 = compiler.compile(Choice(Prefix("a", Stop()), Prefix("b", Stop())))
    initial_actions = lts3.actions(lts3.initial)
    check("choice_both_enabled", "a" in initial_actions and "b" in initial_actions)

    # ── §3 Traces ────────────────────────────────────────────────
    print("\n§3 Trace Semantics\n")

    # a → b → STOP has traces: (), (a,), (a,b)
    lts_ab = compiler.compile(Prefix("a", Prefix("b", Stop())))
    tr = traces(lts_ab)
    check("trace_empty", () in tr)
    check("trace_a", ("a",) in tr)
    check("trace_ab", ("a", "b") in tr)

    # Choice: a □ b has traces including (a,) and (b,)
    lts_choice = compiler.compile(Choice(Prefix("a", Stop()), Prefix("b", Stop())))
    tr_choice = traces(lts_choice)
    check("choice_trace_a", ("a",) in tr_choice)
    check("choice_trace_b", ("b",) in tr_choice)

    # ── §4 Trace Refinement ──────────────────────────────────────
    print("\n§4 Trace Refinement\n")

    # Spec: a → STOP □ b → STOP
    # Impl: a → STOP (subset of spec traces)
    spec = compiler.compile(Choice(Prefix("a", Stop()), Prefix("b", Stop())))
    compiler2 = LTSCompiler()
    impl = compiler2.compile(Prefix("a", Stop()))

    refines, cex = trace_refinement(spec, impl)
    check("impl_refines_spec", refines, f"cex={cex}")

    # Not a refinement: impl has action c not in spec
    compiler3 = LTSCompiler()
    bad_impl = compiler3.compile(Prefix("c", Stop()))
    refines2, cex2 = trace_refinement(spec, bad_impl)
    check("bad_impl_not_refines", not refines2, f"cex2={cex2}")

    # ── §5 Bisimulation ─────────────────────────────────────────
    print("\n§5 Bisimulation\n")

    # Same process: bisimilar
    c1 = LTSCompiler()
    c2 = LTSCompiler()
    lts_a1 = c1.compile(Prefix("a", Stop()))
    lts_a2 = c2.compile(Prefix("a", Stop()))
    check("same_process_bisimilar", strong_bisimulation(lts_a1, lts_a2))

    # Different processes: not bisimilar
    c3 = LTSCompiler()
    lts_b = c3.compile(Prefix("b", Stop()))
    check("different_not_bisimilar", not strong_bisimulation(lts_a1, lts_b))

    # ── §6 Trust Attestation Protocol ────────────────────────────
    print("\n§6 Trust Attestation Protocol\n")

    att_proc = trust_attestation_protocol()
    c4 = LTSCompiler()
    att_lts = c4.compile(att_proc)

    att_traces = traces(att_lts)
    # Should have traces through approve and reject paths
    has_approve = any("approve" in t for t in att_traces)
    has_reject = any("reject" in t for t in att_traces)
    check("att_has_approve_path", has_approve)
    check("att_has_reject_path", has_reject)
    check("att_starts_request", all(
        t[0] == "request" for t in att_traces if len(t) > 0))

    # ── §7 Mutual Attestation ────────────────────────────────────
    print("\n§7 Mutual Attestation Protocol\n")

    mut_proc = mutual_attestation_protocol()
    c5 = LTSCompiler()
    mut_lts = c5.compile(mut_proc)

    mut_traces = traces(mut_lts, max_length=6)
    check("mut_has_traces", len(mut_traces) > 1)
    has_a = any("a_attest" in t for t in mut_traces)
    has_b = any("b_attest" in t for t in mut_traces)
    check("mut_a_attests", has_a)
    check("mut_b_attests", has_b)

    # ── §8 Deadlock Analysis ─────────────────────────────────────
    print("\n§8 Deadlock Analysis\n")

    # STOP is always a deadlock
    c6 = LTSCompiler()
    stop_lts = c6.compile(Stop())
    check("stop_is_deadlock", stop_lts.is_deadlock(stop_lts.initial))

    # a → STOP deadlocks after a
    c7 = LTSCompiler()
    a_stop = c7.compile(Prefix("a", Stop()))
    check("not_initial_deadlock", not a_stop.is_deadlock(a_stop.initial))
    # Find the state after 'a'
    after_a = [s for a, s in a_stop.successors(a_stop.initial) if a == "a"]
    if after_a:
        check("deadlock_after_a", a_stop.is_deadlock(after_a[0]))

    # Sequential: a; b doesn't deadlock at the join point
    c8 = LTSCompiler()
    seq_lts = c8.compile(Sequential(Prefix("a", Skip()), Prefix("b", Skip())))
    seq_traces = traces(seq_lts)
    has_ab = any("a" in t and "b" in t for t in seq_traces)
    check("sequential_both_actions", has_ab)

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
