"""
Trust Protocol Automata for Web4
Session 32, Track 7

Formal state machines for trust protocol flows:
- Attestation protocol automaton (request → verify → attest → finalize)
- Trust negotiation protocol (offer → counter → accept/reject)
- Challenge-response trust verification
- Timed automata (deadlines for protocol steps)
- Protocol composition (sequential, parallel, choice)
- Safety verification (no deadlock, no invalid transitions)
- Protocol trace analysis
"""

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Tuple, Optional, Set, Callable


# ─── State Machine ────────────────────────────────────────────────

@dataclass
class Transition:
    source: str
    target: str
    action: str
    guard: Optional[Callable] = None  # condition that must hold
    timeout: Optional[int] = None     # max time for this transition


@dataclass
class ProtocolAutomaton:
    """Formal protocol state machine."""
    name: str
    states: Set[str] = field(default_factory=set)
    initial_state: str = ""
    final_states: Set[str] = field(default_factory=set)
    error_states: Set[str] = field(default_factory=set)
    transitions: List[Transition] = field(default_factory=list)
    current_state: str = ""
    clock: int = 0
    trace: List[Tuple[str, str, str]] = field(default_factory=list)

    def __post_init__(self):
        if self.current_state == "" and self.initial_state:
            self.current_state = self.initial_state

    def add_state(self, name: str, final: bool = False, error: bool = False):
        self.states.add(name)
        if final:
            self.final_states.add(name)
        if error:
            self.error_states.add(name)

    def add_transition(self, source: str, target: str, action: str,
                        guard: Optional[Callable] = None,
                        timeout: Optional[int] = None):
        self.transitions.append(Transition(
            source=source, target=target, action=action,
            guard=guard, timeout=timeout
        ))

    def available_actions(self) -> List[str]:
        """Return actions available from current state."""
        return [t.action for t in self.transitions
                if t.source == self.current_state]

    def step(self, action: str, context: Dict = None) -> bool:
        """Execute an action. Returns True if transition succeeded."""
        if context is None:
            context = {}

        for t in self.transitions:
            if t.source == self.current_state and t.action == action:
                if t.guard and not t.guard(context):
                    continue
                if t.timeout and self.clock > t.timeout:
                    # Timeout — transition to error state
                    self.trace.append((self.current_state, action + "_timeout", "timeout"))
                    if self.error_states:
                        self.current_state = next(iter(self.error_states))
                    return False

                old_state = self.current_state
                self.current_state = t.target
                self.trace.append((old_state, action, t.target))
                self.clock += 1
                return True

        return False  # No valid transition

    def is_final(self) -> bool:
        return self.current_state in self.final_states

    def is_error(self) -> bool:
        return self.current_state in self.error_states

    def reset(self):
        self.current_state = self.initial_state
        self.clock = 0
        self.trace = []


# ─── Attestation Protocol ────────────────────────────────────────

def build_attestation_protocol() -> ProtocolAutomaton:
    """
    Build attestation protocol automaton:
    idle → requested → verifying → attested → finalized
                    ↘ rejected
    """
    pa = ProtocolAutomaton(name="attestation", initial_state="idle")

    pa.add_state("idle")
    pa.add_state("requested")
    pa.add_state("verifying")
    pa.add_state("attested")
    pa.add_state("finalized", final=True)
    pa.add_state("rejected", final=True)
    pa.add_state("timeout_error", error=True)

    pa.add_transition("idle", "requested", "request")
    pa.add_transition("requested", "verifying", "begin_verify")
    pa.add_transition("verifying", "attested", "verify_pass",
                       guard=lambda ctx: ctx.get("trust", 0) >= ctx.get("threshold", 0.5))
    pa.add_transition("verifying", "rejected", "verify_fail",
                       guard=lambda ctx: ctx.get("trust", 0) < ctx.get("threshold", 0.5))
    pa.add_transition("attested", "finalized", "finalize")

    # Timeout transitions
    pa.add_transition("requested", "timeout_error", "timeout", timeout=10)
    pa.add_transition("verifying", "timeout_error", "timeout", timeout=20)

    pa.current_state = "idle"
    return pa


# ─── Trust Negotiation Protocol ──────────────────────────────────

def build_negotiation_protocol() -> ProtocolAutomaton:
    """
    Trust negotiation:
    idle → offered → [counter_offered ↔]* → accepted | rejected
    """
    pn = ProtocolAutomaton(name="negotiation", initial_state="idle")

    pn.add_state("idle")
    pn.add_state("offered")
    pn.add_state("counter_offered")
    pn.add_state("accepted", final=True)
    pn.add_state("rejected", final=True)
    pn.add_state("expired", error=True)

    pn.add_transition("idle", "offered", "make_offer")
    pn.add_transition("offered", "accepted", "accept")
    pn.add_transition("offered", "rejected", "reject")
    pn.add_transition("offered", "counter_offered", "counter")
    pn.add_transition("counter_offered", "accepted", "accept")
    pn.add_transition("counter_offered", "rejected", "reject")
    pn.add_transition("counter_offered", "counter_offered", "counter")

    pn.current_state = "idle"
    return pn


# ─── Challenge-Response Protocol ─────────────────────────────────

def build_challenge_response_protocol() -> ProtocolAutomaton:
    """
    Challenge-response trust verification:
    idle → challenged → responded → verified | failed
    """
    cr = ProtocolAutomaton(name="challenge_response", initial_state="idle")

    cr.add_state("idle")
    cr.add_state("challenged")
    cr.add_state("responded")
    cr.add_state("verified", final=True)
    cr.add_state("failed", final=True)

    cr.add_transition("idle", "challenged", "challenge")
    cr.add_transition("challenged", "responded", "respond")
    cr.add_transition("responded", "verified", "verify_ok",
                       guard=lambda ctx: ctx.get("response_valid", False))
    cr.add_transition("responded", "failed", "verify_fail",
                       guard=lambda ctx: not ctx.get("response_valid", False))

    cr.current_state = "idle"
    return cr


# ─── Protocol Composition ────────────────────────────────────────

def sequential_compose(p1: ProtocolAutomaton,
                        p2: ProtocolAutomaton) -> ProtocolAutomaton:
    """
    Sequential composition: p1 THEN p2.
    p1's final states connect to p2's initial state.
    """
    composed = ProtocolAutomaton(
        name=f"{p1.name}_then_{p2.name}",
        initial_state=f"p1_{p1.initial_state}"
    )

    # Add p1 states (non-final become intermediate)
    for s in p1.states:
        is_error = s in p1.error_states
        composed.add_state(f"p1_{s}", error=is_error)

    # Add p2 states
    for s in p2.states:
        is_final = s in p2.final_states
        is_error = s in p2.error_states
        composed.add_state(f"p2_{s}", final=is_final, error=is_error)

    # Add p1 transitions (non-final targets)
    for t in p1.transitions:
        if t.target not in p1.final_states:
            composed.add_transition(f"p1_{t.source}", f"p1_{t.target}", f"p1_{t.action}")

    # Connect p1 final states to p2 initial state
    for fs in p1.final_states:
        for t in p1.transitions:
            if t.target == fs:
                composed.add_transition(
                    f"p1_{t.source}", f"p2_{p2.initial_state}", f"p1_{t.action}_connect")

    # Add p2 transitions
    for t in p2.transitions:
        composed.add_transition(f"p2_{t.source}", f"p2_{t.target}", f"p2_{t.action}")

    composed.current_state = composed.initial_state
    return composed


# ─── Safety Verification ─────────────────────────────────────────

def verify_no_deadlock(protocol: ProtocolAutomaton) -> Tuple[bool, List[str]]:
    """
    Verify that no non-final, non-error state is a deadlock.
    Returns (is_safe, deadlocked_states).
    """
    deadlocked = []
    for state in protocol.states:
        if state in protocol.final_states or state in protocol.error_states:
            continue
        # Check if any transition leads out of this state
        has_outgoing = any(t.source == state for t in protocol.transitions)
        if not has_outgoing:
            deadlocked.append(state)

    return len(deadlocked) == 0, deadlocked


def verify_reachability(protocol: ProtocolAutomaton) -> Set[str]:
    """Return set of reachable states from initial state."""
    visited = set()
    stack = [protocol.initial_state]

    while stack:
        state = stack.pop()
        if state in visited:
            continue
        visited.add(state)
        for t in protocol.transitions:
            if t.source == state:
                stack.append(t.target)

    return visited


def verify_final_reachable(protocol: ProtocolAutomaton) -> bool:
    """Verify that at least one final state is reachable."""
    reachable = verify_reachability(protocol)
    return bool(reachable & protocol.final_states)


def count_paths(protocol: ProtocolAutomaton, max_depth: int = 20) -> int:
    """Count distinct paths from initial to any final state."""
    count = 0

    def dfs(state: str, depth: int, visited: Set[str]):
        nonlocal count
        if depth > max_depth:
            return
        if state in protocol.final_states:
            count += 1
            return

        for t in protocol.transitions:
            if t.source == state:
                if t.target not in visited or t.target in protocol.final_states:
                    visited.add(t.target)
                    dfs(t.target, depth + 1, visited)
                    visited.discard(t.target)

    dfs(protocol.initial_state, 0, {protocol.initial_state})
    return count


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
    print("Trust Protocol Automata for Web4")
    print("Session 32, Track 7")
    print("=" * 70)

    # ── §1 Attestation Protocol ─────────────────────────────────
    print("\n§1 Attestation Protocol\n")

    att = build_attestation_protocol()
    check("att_initial_idle", att.current_state == "idle")
    check("att_not_final", not att.is_final())

    # Happy path: request → verify → pass → finalize
    att.step("request")
    check("att_requested", att.current_state == "requested")

    att.step("begin_verify")
    check("att_verifying", att.current_state == "verifying")

    att.step("verify_pass", {"trust": 0.8, "threshold": 0.5})
    check("att_attested", att.current_state == "attested")

    att.step("finalize")
    check("att_finalized", att.is_final())

    # Trace
    check("att_trace_length", len(att.trace) == 4,
          f"trace={len(att.trace)}")

    # Rejection path
    att2 = build_attestation_protocol()
    att2.step("request")
    att2.step("begin_verify")
    att2.step("verify_fail", {"trust": 0.3, "threshold": 0.5})
    check("att_rejected", att2.current_state == "rejected")
    check("att_rejected_final", att2.is_final())

    # ── §2 Negotiation Protocol ─────────────────────────────────
    print("\n§2 Trust Negotiation Protocol\n")

    neg = build_negotiation_protocol()
    check("neg_initial", neg.current_state == "idle")

    neg.step("make_offer")
    check("neg_offered", neg.current_state == "offered")

    neg.step("counter")
    check("neg_countered", neg.current_state == "counter_offered")

    # Multiple counters allowed
    neg.step("counter")
    check("neg_counter_again", neg.current_state == "counter_offered")

    neg.step("accept")
    check("neg_accepted", neg.current_state == "accepted")
    check("neg_final", neg.is_final())

    # ── §3 Challenge-Response ───────────────────────────────────
    print("\n§3 Challenge-Response Protocol\n")

    cr = build_challenge_response_protocol()
    cr.step("challenge")
    cr.step("respond")
    cr.step("verify_ok", {"response_valid": True})
    check("cr_verified", cr.current_state == "verified")

    # Failed verification
    cr2 = build_challenge_response_protocol()
    cr2.step("challenge")
    cr2.step("respond")
    cr2.step("verify_fail", {"response_valid": False})
    check("cr_failed", cr2.current_state == "failed")

    # Invalid action
    cr3 = build_challenge_response_protocol()
    result = cr3.step("respond")  # can't respond before challenge
    check("cr_invalid_action", not result)
    check("cr_stays_idle", cr3.current_state == "idle")

    # ── §4 Safety Verification ──────────────────────────────────
    print("\n§4 Safety Verification\n")

    att = build_attestation_protocol()
    no_deadlock, deadlocked = verify_no_deadlock(att)
    check("att_no_deadlock", no_deadlock,
          f"deadlocked={deadlocked}")

    reachable = verify_reachability(att)
    check("att_all_reachable", len(reachable) >= 5,
          f"reachable={len(reachable)}")

    check("att_final_reachable", verify_final_reachable(att))

    neg = build_negotiation_protocol()
    no_dl_neg, dl_neg = verify_no_deadlock(neg)
    check("neg_no_deadlock", no_dl_neg, f"deadlocked={dl_neg}")

    # ── §5 Protocol Composition ─────────────────────────────────
    print("\n§5 Protocol Composition\n")

    cr = build_challenge_response_protocol()
    att = build_attestation_protocol()
    composed = sequential_compose(cr, att)

    check("composed_states", len(composed.states) > len(cr.states),
          f"composed={len(composed.states)}")
    check("composed_initial", composed.current_state.startswith("p1_"))

    # Verify composed protocol has final states
    check("composed_has_final", len(composed.final_states) > 0,
          f"finals={composed.final_states}")

    # ── §6 Path Analysis ───────────────────────────────────────
    print("\n§6 Path Analysis\n")

    att = build_attestation_protocol()
    paths = count_paths(att)
    check("att_multiple_paths", paths >= 2,
          f"paths={paths}")  # pass path + reject path

    cr = build_challenge_response_protocol()
    cr_paths = count_paths(cr)
    check("cr_paths", cr_paths >= 2,
          f"paths={cr_paths}")  # verified + failed

    # ── §7 Available Actions ────────────────────────────────────
    print("\n§7 Available Actions\n")

    att = build_attestation_protocol()
    idle_actions = att.available_actions()
    check("idle_can_request", "request" in idle_actions,
          f"actions={idle_actions}")

    att.step("request")
    req_actions = att.available_actions()
    check("requested_can_verify", "begin_verify" in req_actions,
          f"actions={req_actions}")

    # Reset
    att.reset()
    check("reset_to_idle", att.current_state == "idle")
    check("reset_clears_trace", len(att.trace) == 0)

    # ── Summary ─────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
