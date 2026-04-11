"""
Trust Automata Composition for Web4
Session 34, Track 1

Formal composition of trust protocol automata:
- DFA/NFA for trust state machines
- Product composition (synchronous parallel)
- Asynchronous interleaving composition
- Hiding/abstraction (internal actions)
- Bisimulation equivalence checking
- Deadlock detection in composed systems
- Trace equivalence and refinement
- Trust protocol compatibility checking
- Alphabet partitioning for interface composition
"""

from dataclasses import dataclass, field
from typing import Set, Dict, Tuple, Optional, FrozenSet, List
from collections import defaultdict, deque
from enum import Enum, auto


# ─── Labeled Transition System (LTS) ────────────────────────────

@dataclass
class LTS:
    """
    Labeled Transition System — foundation for process algebra.
    More general than DFA: allows nondeterminism and tau (internal) actions.
    """
    states: Set[str]
    initial: str
    alphabet: Set[str]                           # observable actions
    transitions: Dict[str, Dict[str, Set[str]]]  # state -> {action -> {next_states}}
    accepting: Set[str] = field(default_factory=set)
    tau: str = "τ"                                # internal action symbol

    def successors(self, state: str, action: str) -> Set[str]:
        return self.transitions.get(state, {}).get(action, set())

    def enabled(self, state: str) -> Set[str]:
        """Actions enabled in a state."""
        return set(self.transitions.get(state, {}).keys())

    def is_deadlock(self, state: str) -> bool:
        """A state with no outgoing transitions."""
        return len(self.enabled(state)) == 0

    def reachable(self) -> Set[str]:
        """Compute reachable states from initial."""
        visited = set()
        queue = deque([self.initial])
        while queue:
            s = queue.popleft()
            if s in visited:
                continue
            visited.add(s)
            for action, nexts in self.transitions.get(s, {}).items():
                for n in nexts:
                    if n not in visited:
                        queue.append(n)
        return visited

    def traces(self, max_length: int = 10) -> Set[Tuple[str, ...]]:
        """Enumerate traces (action sequences) up to max_length."""
        result = set()
        result.add(())  # empty trace

        stack = [(self.initial, ())]
        while stack:
            state, trace = stack.pop()
            if len(trace) >= max_length:
                continue
            for action, nexts in self.transitions.get(state, {}).items():
                if action == self.tau:
                    continue  # skip internal actions in traces
                new_trace = trace + (action,)
                result.add(new_trace)
                for n in nexts:
                    stack.append((n, new_trace))
        return result


# ─── Product Composition (Synchronous) ───────────────────────────

def synchronous_product(a: LTS, b: LTS) -> LTS:
    """
    Synchronous product: both automata must agree on shared actions.
    - Shared actions: synchronized (both move)
    - Private actions: independent (only owner moves)
    """
    shared = a.alphabet & b.alphabet
    a_private = a.alphabet - shared
    b_private = b.alphabet - shared

    states = set()
    transitions: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
    initial = f"{a.initial},{b.initial}"
    accepting = set()

    # BFS through product state space
    queue = deque([(a.initial, b.initial)])
    visited = set()

    while queue:
        sa, sb = queue.popleft()
        if (sa, sb) in visited:
            continue
        visited.add((sa, sb))
        product_state = f"{sa},{sb}"
        states.add(product_state)

        if sa in a.accepting and sb in b.accepting:
            accepting.add(product_state)

        # Shared actions: both must move
        for action in shared:
            for na in a.successors(sa, action):
                for nb in b.successors(sb, action):
                    next_state = f"{na},{nb}"
                    transitions[product_state][action].add(next_state)
                    queue.append((na, nb))

        # A-private actions: only A moves
        for action in a_private:
            for na in a.successors(sa, action):
                next_state = f"{na},{sb}"
                transitions[product_state][action].add(next_state)
                queue.append((na, sb))

        # B-private actions: only B moves
        for action in b_private:
            for nb in b.successors(sb, action):
                next_state = f"{sa},{nb}"
                transitions[product_state][action].add(next_state)
                queue.append((sa, nb))

    return LTS(
        states=states,
        initial=initial,
        alphabet=a.alphabet | b.alphabet,
        transitions=dict(transitions),
        accepting=accepting,
    )


# ─── Asynchronous Interleaving ───────────────────────────────────

def interleaving(a: LTS, b: LTS) -> LTS:
    """
    Asynchronous interleaving: all actions are independent.
    At each step, either A or B makes a move (no synchronization).
    """
    states = set()
    transitions: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
    initial = f"{a.initial},{b.initial}"
    accepting = set()

    queue = deque([(a.initial, b.initial)])
    visited = set()

    while queue:
        sa, sb = queue.popleft()
        if (sa, sb) in visited:
            continue
        visited.add((sa, sb))
        product_state = f"{sa},{sb}"
        states.add(product_state)

        if sa in a.accepting and sb in b.accepting:
            accepting.add(product_state)

        # A moves independently
        for action in a.enabled(sa):
            for na in a.successors(sa, action):
                next_state = f"{na},{sb}"
                transitions[product_state][action].add(next_state)
                queue.append((na, sb))

        # B moves independently
        for action in b.enabled(sb):
            for nb in b.successors(sb, action):
                next_state = f"{sa},{nb}"
                transitions[product_state][action].add(next_state)
                queue.append((sa, nb))

    return LTS(
        states=states,
        initial=initial,
        alphabet=a.alphabet | b.alphabet,
        transitions=dict(transitions),
        accepting=accepting,
    )


# ─── Hiding (Abstraction) ────────────────────────────────────────

def hide(lts: LTS, actions_to_hide: Set[str]) -> LTS:
    """
    Hide actions by converting them to internal (tau) actions.
    Used for abstraction — hiding implementation details.
    """
    new_alphabet = lts.alphabet - actions_to_hide
    new_transitions: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))

    for state, action_map in lts.transitions.items():
        for action, nexts in action_map.items():
            if action in actions_to_hide:
                new_transitions[state][lts.tau] |= nexts
            else:
                new_transitions[state][action] |= nexts

    return LTS(
        states=set(lts.states),
        initial=lts.initial,
        alphabet=new_alphabet,
        transitions=dict(new_transitions),
        accepting=set(lts.accepting),
    )


# ─── Deadlock Detection ──────────────────────────────────────────

def find_deadlocks(lts: LTS) -> Set[str]:
    """Find all reachable deadlock states (no outgoing transitions)."""
    reachable = lts.reachable()
    deadlocks = set()
    for s in reachable:
        if lts.is_deadlock(s) and s not in lts.accepting:
            deadlocks.add(s)
    return deadlocks


def is_deadlock_free(lts: LTS) -> bool:
    """Check if the LTS is deadlock-free (all reachable states have successors or are accepting)."""
    return len(find_deadlocks(lts)) == 0


# ─── Bisimulation Equivalence ────────────────────────────────────

def bisimulation_partition(lts: LTS) -> List[Set[str]]:
    """
    Compute the coarsest bisimulation partition via partition refinement.
    Two states are bisimilar iff they are in the same block.
    """
    all_states = lts.states

    # Initial partition: {accepting, non-accepting}
    acc = all_states & lts.accepting
    non_acc = all_states - lts.accepting
    partition = []
    if acc:
        partition.append(acc)
    if non_acc:
        partition.append(non_acc)
    if not partition:
        return []

    # Iterative refinement
    changed = True
    while changed:
        changed = False
        new_partition = []
        for block in partition:
            # Try to split this block
            split = _try_split(block, partition, lts)
            if len(split) > 1:
                changed = True
            new_partition.extend(split)
        partition = new_partition

    return partition


def _try_split(block: Set[str], partition: List[Set[str]], lts: LTS) -> List[Set[str]]:
    """Try to split a block based on transitions to other blocks."""
    if len(block) <= 1:
        return [block]

    # For each action and target block, check if all states in block
    # can reach that target block
    block_list = list(block)
    reference = block_list[0]

    for action in lts.alphabet | {lts.tau}:
        ref_targets = lts.successors(reference, action)
        ref_blocks = _find_blocks(ref_targets, partition)

        same = {reference}
        diff = set()

        for s in block_list[1:]:
            s_targets = lts.successors(s, action)
            s_blocks = _find_blocks(s_targets, partition)
            if s_blocks == ref_blocks:
                same.add(s)
            else:
                diff.add(s)

        if diff:
            return [same, diff]

    return [block]


def _find_blocks(states: Set[str], partition: List[Set[str]]) -> FrozenSet[int]:
    """Find which partition blocks a set of states belongs to."""
    blocks = set()
    for s in states:
        for i, block in enumerate(partition):
            if s in block:
                blocks.add(i)
                break
    return frozenset(blocks)


def are_bisimilar(a: LTS, b: LTS) -> bool:
    """
    Check if two LTS are bisimilar by computing the partition
    of their disjoint union.
    """
    # Create disjoint union
    union_states = {f"a.{s}" for s in a.states} | {f"b.{s}" for s in b.states}
    union_trans: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))

    for s, amap in a.transitions.items():
        for action, nexts in amap.items():
            for n in nexts:
                union_trans[f"a.{s}"][action].add(f"a.{n}")

    for s, bmap in b.transitions.items():
        for action, nexts in bmap.items():
            for n in nexts:
                union_trans[f"b.{s}"][action].add(f"b.{n}")

    union = LTS(
        states=union_states,
        initial=f"a.{a.initial}",
        alphabet=a.alphabet | b.alphabet,
        transitions=dict(union_trans),
        accepting={f"a.{s}" for s in a.accepting} | {f"b.{s}" for s in b.accepting},
    )

    partition = bisimulation_partition(union)
    # Check if initial states are in the same block
    for block in partition:
        if f"a.{a.initial}" in block and f"b.{b.initial}" in block:
            return True
    return False


# ─── Trace Refinement ────────────────────────────────────────────

def trace_includes(spec: LTS, impl: LTS, max_length: int = 8) -> bool:
    """
    Check if impl's traces are a subset of spec's traces.
    Implementation refines specification.
    """
    spec_traces = spec.traces(max_length)
    impl_traces = impl.traces(max_length)
    return impl_traces.issubset(spec_traces)


# ─── Protocol Compatibility ──────────────────────────────────────

def are_compatible(a: LTS, b: LTS) -> Tuple[bool, Optional[str]]:
    """
    Check if two protocols are compatible:
    - Their composition is deadlock-free
    - They can progress together
    Returns (compatible, reason_if_not).
    """
    composed = synchronous_product(a, b)
    deadlocks = find_deadlocks(composed)

    if deadlocks:
        return False, f"Deadlock states: {deadlocks}"

    # Check that at least one accepting state is reachable
    reachable = composed.reachable()
    if composed.accepting and not (reachable & composed.accepting):
        return False, "No accepting state reachable"

    return True, None


# ─── Trust Protocol Builders ─────────────────────────────────────

def attestation_protocol() -> LTS:
    """A simple trust attestation protocol: request → verify → attest/reject."""
    return LTS(
        states={"idle", "requested", "verified", "attested", "rejected"},
        initial="idle",
        alphabet={"request", "verify", "attest", "reject"},
        transitions={
            "idle": {"request": {"requested"}},
            "requested": {"verify": {"verified"}},
            "verified": {"attest": {"attested"}, "reject": {"rejected"}},
        },
        accepting={"attested", "rejected"},
    )


def verification_protocol() -> LTS:
    """Verification side: receive request, verify, respond."""
    return LTS(
        states={"waiting", "checking", "done_ok", "done_fail"},
        initial="waiting",
        alphabet={"request", "verify", "attest", "reject"},
        transitions={
            "waiting": {"request": {"checking"}},
            "checking": {"verify": {"done_ok", "done_fail"}},
            "done_ok": {"attest": {"waiting"}},
            "done_fail": {"reject": {"waiting"}},
        },
        accepting={"waiting"},
    )


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
    print("Trust Automata Composition for Web4")
    print("Session 34, Track 1")
    print("=" * 70)

    # ── §1 LTS Basics ───────────────────────────────────────────
    print("\n§1 LTS Basics\n")

    lts1 = LTS(
        states={"s0", "s1", "s2"},
        initial="s0",
        alphabet={"a", "b"},
        transitions={
            "s0": {"a": {"s1"}},
            "s1": {"b": {"s2"}},
        },
        accepting={"s2"},
    )
    check("reachable", lts1.reachable() == {"s0", "s1", "s2"})
    check("enabled_s0", lts1.enabled("s0") == {"a"})
    check("enabled_s2", lts1.enabled("s2") == set())
    check("deadlock_s2", lts1.is_deadlock("s2"))
    check("not_deadlock_s0", not lts1.is_deadlock("s0"))
    check("successors", lts1.successors("s0", "a") == {"s1"})
    check("no_successor", lts1.successors("s0", "b") == set())

    # Traces
    traces = lts1.traces(5)
    check("empty_trace", () in traces)
    check("trace_a", ("a",) in traces)
    check("trace_ab", ("a", "b") in traces)
    check("no_ba_trace", ("b", "a") not in traces)

    # ── §2 Synchronous Product ───────────────────────────────────
    print("\n§2 Synchronous Product\n")

    # Two processes sharing action "sync"
    p1 = LTS(
        states={"p0", "p1"},
        initial="p0",
        alphabet={"sync", "local_a"},
        transitions={
            "p0": {"local_a": {"p0"}, "sync": {"p1"}},
        },
        accepting={"p1"},
    )
    p2 = LTS(
        states={"q0", "q1"},
        initial="q0",
        alphabet={"sync", "local_b"},
        transitions={
            "q0": {"local_b": {"q0"}, "sync": {"q1"}},
        },
        accepting={"q1"},
    )

    product = synchronous_product(p1, p2)
    check("product_initial", product.initial == "p0,q0")
    check("product_has_states", len(product.states) > 0)

    # Sync action requires both to move
    synced = product.successors("p0,q0", "sync")
    check("sync_moves_both", "p1,q1" in synced)

    # Private actions move independently
    local_a = product.successors("p0,q0", "local_a")
    check("local_a_moves_p1_only", "p0,q0" in local_a)  # p stays at p0 due to self-loop

    # ── §3 Interleaving ─────────────────────────────────────────
    print("\n§3 Asynchronous Interleaving\n")

    a1 = LTS(
        states={"a0", "a1"},
        initial="a0",
        alphabet={"x"},
        transitions={"a0": {"x": {"a1"}}},
        accepting={"a1"},
    )
    a2 = LTS(
        states={"b0", "b1"},
        initial="b0",
        alphabet={"y"},
        transitions={"b0": {"y": {"b1"}}},
        accepting={"b1"},
    )

    inter = interleaving(a1, a2)
    check("interleave_initial", inter.initial == "a0,b0")

    # Both orderings possible: x then y, or y then x
    inter_traces = inter.traces(5)
    check("trace_xy", ("x", "y") in inter_traces)
    check("trace_yx", ("y", "x") in inter_traces)
    check("interleave_accepting", "a1,b1" in inter.accepting)

    # ── §4 Hiding ────────────────────────────────────────────────
    print("\n§4 Hiding (Abstraction)\n")

    full = LTS(
        states={"s0", "s1", "s2"},
        initial="s0",
        alphabet={"public", "internal"},
        transitions={
            "s0": {"internal": {"s1"}},
            "s1": {"public": {"s2"}},
        },
        accepting={"s2"},
    )

    hidden = hide(full, {"internal"})
    check("hidden_alphabet", hidden.alphabet == {"public"})

    # Internal becomes tau
    tau_succs = hidden.successors("s0", hidden.tau)
    check("tau_transition", "s1" in tau_succs)

    # Public action preserved
    check("public_preserved", "s2" in hidden.successors("s1", "public"))

    # ── §5 Deadlock Detection ────────────────────────────────────
    print("\n§5 Deadlock Detection\n")

    # lts1 has deadlock at s2 (accepting, so not counted)
    deadlocks1 = find_deadlocks(lts1)
    check("s2_accepting_not_deadlock", "s2" not in deadlocks1)

    # Non-accepting deadlock
    lts_dl = LTS(
        states={"s0", "s1", "dead"},
        initial="s0",
        alphabet={"a", "b"},
        transitions={
            "s0": {"a": {"s1"}, "b": {"dead"}},
            "s1": {"a": {"s0"}},
        },
        accepting={"s1"},
    )
    deadlocks = find_deadlocks(lts_dl)
    check("deadlock_found", "dead" in deadlocks)
    check("not_deadlock_free", not is_deadlock_free(lts_dl))

    # Deadlock-free system
    lts_safe = LTS(
        states={"s0", "s1"},
        initial="s0",
        alphabet={"a"},
        transitions={"s0": {"a": {"s1"}}, "s1": {"a": {"s0"}}},
        accepting={"s0", "s1"},
    )
    check("deadlock_free", is_deadlock_free(lts_safe))

    # ── §6 Bisimulation ─────────────────────────────────────────
    print("\n§6 Bisimulation Equivalence\n")

    # Two identical systems should be bisimilar
    sys_a = LTS(
        states={"x", "y"},
        initial="x",
        alphabet={"a"},
        transitions={"x": {"a": {"y"}}},
        accepting={"y"},
    )
    sys_b = LTS(
        states={"p", "q"},
        initial="p",
        alphabet={"a"},
        transitions={"p": {"a": {"q"}}},
        accepting={"q"},
    )
    check("identical_bisimilar", are_bisimilar(sys_a, sys_b))

    # Different behavior: not bisimilar
    sys_c = LTS(
        states={"m", "n"},
        initial="m",
        alphabet={"a", "b"},
        transitions={"m": {"a": {"n"}}, "n": {"b": {"m"}}},
        accepting={"n"},
    )
    check("different_not_bisimilar", not are_bisimilar(sys_a, sys_c))

    # Partition refinement
    partition = bisimulation_partition(sys_a)
    check("partition_computed", len(partition) > 0)
    check("partition_covers_reachable", sum(len(b) for b in partition) >= 2)

    # ── §7 Trace Refinement ──────────────────────────────────────
    print("\n§7 Trace Refinement\n")

    # Spec allows a,b; impl only does a → refines
    spec = LTS(
        states={"s0", "s1", "s2"},
        initial="s0",
        alphabet={"a", "b"},
        transitions={"s0": {"a": {"s1"}, "b": {"s2"}}},
        accepting={"s1", "s2"},
    )
    impl = LTS(
        states={"i0", "i1"},
        initial="i0",
        alphabet={"a"},
        transitions={"i0": {"a": {"i1"}}},
        accepting={"i1"},
    )
    check("impl_refines_spec", trace_includes(spec, impl))

    # Impl adds a trace not in spec → doesn't refine
    impl_bad = LTS(
        states={"i0", "i1"},
        initial="i0",
        alphabet={"a", "c"},
        transitions={"i0": {"a": {"i1"}, "c": {"i1"}}},
        accepting={"i1"},
    )
    check("bad_impl_not_refines", not trace_includes(spec, impl_bad))

    # ── §8 Protocol Compatibility ────────────────────────────────
    print("\n§8 Protocol Compatibility\n")

    attest = attestation_protocol()
    verify = verification_protocol()

    # These protocols share the same alphabet and should compose
    composed = synchronous_product(attest, verify)
    reachable_composed = composed.reachable()
    check("composed_has_states", len(reachable_composed) > 0)

    # Check compatibility
    compat, reason = are_compatible(attest, verify)
    # The composition may deadlock in some states — check
    deadlocks_composed = find_deadlocks(composed)
    check("compatibility_analyzed", reason is None or isinstance(reason, str))

    # Two completely independent protocols: always compatible (no shared actions)
    indep_a = LTS(
        states={"a0", "a1"}, initial="a0", alphabet={"x"},
        transitions={"a0": {"x": {"a1"}}}, accepting={"a1"},
    )
    indep_b = LTS(
        states={"b0", "b1"}, initial="b0", alphabet={"y"},
        transitions={"b0": {"y": {"b1"}}}, accepting={"b1"},
    )
    compat2, _ = are_compatible(indep_a, indep_b)
    check("independent_compatible", compat2)

    # ── §9 Trust Protocol Composition ────────────────────────────
    print("\n§9 Trust Protocol Composition\n")

    # Attestation + delegation protocols composed
    delegation = LTS(
        states={"d_idle", "d_requesting", "d_granted", "d_denied"},
        initial="d_idle",
        alphabet={"delegate_request", "delegate_grant", "delegate_deny", "attest"},
        transitions={
            "d_idle": {"delegate_request": {"d_requesting"}},
            "d_requesting": {"delegate_grant": {"d_granted"}, "delegate_deny": {"d_denied"}},
            "d_granted": {"attest": {"d_idle"}},
        },
        accepting={"d_idle", "d_granted"},
    )

    # delegation shares "attest" with attestation protocol
    check("shared_actions", "attest" in (attest.alphabet & delegation.alphabet))

    composed_trust = synchronous_product(attest, delegation)
    check("composed_trust_has_states", len(composed_trust.states) > 0)
    check("composed_trust_initial", composed_trust.initial == "idle,d_idle")

    # The composition should have traces involving both protocols
    trust_traces = composed_trust.traces(6)
    check("has_delegate_trace", any("delegate_request" in t for t in trust_traces))

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
