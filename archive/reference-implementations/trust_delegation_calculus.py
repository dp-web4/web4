"""
Trust Delegation Calculus for Web4
Session 33, Track 7

Formal algebra of trust delegation chains:
- Delegation as typed arrows with trust attenuation
- Sequential composition: A→B→C (serial delegation)
- Parallel composition: A→B | A→C (concurrent delegations)
- Delegation depth limits and trust decay
- Revocation propagation through chains
- Conditional delegation (capability-scoped)
- Delegation algebra laws (associativity, monotonicity)
- Circular delegation detection
- Effective authority computation
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set, FrozenSet
from collections import defaultdict
from enum import Enum, auto


# ─── Delegation Types ────────────────────────────────────────────

class DelegationType(Enum):
    FULL = auto()            # Complete authority transfer
    SCOPED = auto()          # Limited to specific capabilities
    CONDITIONAL = auto()     # Subject to conditions
    TEMPORARY = auto()       # Time-bounded


@dataclass(frozen=True)
class Capability:
    """A specific capability that can be delegated."""
    name: str
    scope: str = "global"    # e.g., "read", "write", "admin"

    def __repr__(self):
        return f"{self.name}:{self.scope}"


@dataclass
class Delegation:
    """A single delegation arrow from delegator to delegate."""
    delegator: str
    delegate: str
    trust_factor: float      # Trust attenuation factor [0, 1]
    delegation_type: DelegationType = DelegationType.FULL
    capabilities: FrozenSet[Capability] = field(default_factory=frozenset)
    max_depth: int = 5        # Maximum re-delegation depth
    revoked: bool = False
    conditions: List[str] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        return not self.revoked and self.trust_factor > 0

    def attenuated_trust(self, incoming_trust: float) -> float:
        """Apply trust attenuation to incoming trust."""
        if not self.is_active:
            return 0.0
        return incoming_trust * self.trust_factor


# ─── Delegation Chain ────────────────────────────────────────────

@dataclass
class DelegationChain:
    """A chain of delegations: A→B→C→D."""
    delegations: List[Delegation]

    @property
    def source(self) -> str:
        return self.delegations[0].delegator if self.delegations else ""

    @property
    def target(self) -> str:
        return self.delegations[-1].delegate if self.delegations else ""

    @property
    def depth(self) -> int:
        return len(self.delegations)

    @property
    def effective_trust(self) -> float:
        """Serial composition: product of trust factors."""
        if not self.delegations:
            return 0.0
        trust = 1.0
        for d in self.delegations:
            if not d.is_active:
                return 0.0
            trust *= d.trust_factor
        return trust

    @property
    def effective_capabilities(self) -> FrozenSet[Capability]:
        """Intersection of capabilities along chain (monotonically restricting)."""
        if not self.delegations:
            return frozenset()

        # Start with first delegation's capabilities
        # Full delegation means "all capabilities"
        caps: Optional[FrozenSet[Capability]] = None
        for d in self.delegations:
            if d.delegation_type == DelegationType.FULL:
                continue  # Full = pass through
            if caps is None:
                caps = d.capabilities
            else:
                caps = caps & d.capabilities  # Intersection
        return caps if caps is not None else frozenset()

    @property
    def is_valid(self) -> bool:
        """Check chain validity."""
        if not self.delegations:
            return False
        # Chain must be contiguous
        for i in range(1, len(self.delegations)):
            if self.delegations[i].delegator != self.delegations[i-1].delegate:
                return False
        # Check depth limits
        for i, d in enumerate(self.delegations):
            if i >= d.max_depth:
                return False
        # All must be active
        return all(d.is_active for d in self.delegations)

    @property
    def entities(self) -> List[str]:
        """All entities in the chain."""
        if not self.delegations:
            return []
        result = [self.delegations[0].delegator]
        for d in self.delegations:
            result.append(d.delegate)
        return result


# ─── Delegation Graph ────────────────────────────────────────────

class DelegationGraph:
    """Graph of all delegation relationships."""

    def __init__(self):
        self.delegations: List[Delegation] = []
        self.outgoing: Dict[str, List[int]] = defaultdict(list)  # entity -> delegation indices
        self.incoming: Dict[str, List[int]] = defaultdict(list)
        self.entities: Set[str] = set()

    def add_delegation(self, delegation: Delegation) -> int:
        """Add a delegation. Returns its index."""
        idx = len(self.delegations)
        self.delegations.append(delegation)
        self.outgoing[delegation.delegator].append(idx)
        self.incoming[delegation.delegate].append(idx)
        self.entities.add(delegation.delegator)
        self.entities.add(delegation.delegate)
        return idx

    def revoke(self, delegator: str, delegate: str) -> int:
        """Revoke all delegations from delegator to delegate. Returns count revoked."""
        count = 0
        for idx in self.outgoing.get(delegator, []):
            d = self.delegations[idx]
            if d.delegate == delegate and not d.revoked:
                d.revoked = True
                count += 1
        return count

    def revoke_cascade(self, delegator: str, delegate: str) -> Set[str]:
        """
        Revoke delegation and cascade to all downstream.
        If A→B is revoked, and B→C exists, C loses authority too.
        Returns set of all affected entities.
        """
        affected = set()
        stack = [(delegator, delegate)]

        while stack:
            src, dst = stack.pop()
            for idx in self.outgoing.get(src, []):
                d = self.delegations[idx]
                if d.delegate == dst and not d.revoked:
                    d.revoked = True
                    affected.add(dst)
                    # Cascade: revoke all outgoing from dst
                    for idx2 in self.outgoing.get(dst, []):
                        d2 = self.delegations[idx2]
                        if not d2.revoked:
                            stack.append((dst, d2.delegate))

        return affected

    def find_chains(self, source: str, target: str,
                     max_depth: int = 5) -> List[DelegationChain]:
        """Find all active delegation chains from source to target."""
        chains = []

        def dfs(current: str, chain: List[Delegation], visited: Set[str]):
            if current == target:
                chains.append(DelegationChain(list(chain)))
                return
            if len(chain) >= max_depth or current in visited:
                return

            for idx in self.outgoing.get(current, []):
                d = self.delegations[idx]
                if d.is_active and d.delegate not in visited:
                    chain.append(d)
                    dfs(d.delegate, chain, visited | {current})
                    chain.pop()

        dfs(source, [], set())
        return chains

    def effective_trust(self, source: str, target: str) -> float:
        """
        Compute effective trust from source to target.
        Takes the maximum trust over all valid chains (optimistic).
        """
        chains = self.find_chains(source, target)
        if not chains:
            return 0.0
        return max(c.effective_trust for c in chains if c.is_valid)

    def detect_cycles(self) -> List[List[str]]:
        """Detect circular delegation cycles."""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for idx in self.outgoing.get(node, []):
                d = self.delegations[idx]
                if not d.is_active:
                    continue
                neighbor = d.delegate
                if neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
                elif neighbor not in visited:
                    dfs(neighbor, path)

            path.pop()
            rec_stack.discard(node)

        for entity in list(self.entities):
            if entity not in visited:
                dfs(entity, [])

        return cycles

    def authority_set(self, entity: str) -> Dict[str, float]:
        """
        Compute effective authority of entity over all reachable targets.
        Returns {target: effective_trust}.
        """
        result = {}
        visited = set()
        stack = [(entity, 1.0, set())]

        while stack:
            current, trust, path_set = stack.pop()
            if current in path_set:
                continue

            for idx in self.outgoing.get(current, []):
                d = self.delegations[idx]
                if not d.is_active:
                    continue
                target = d.delegate
                new_trust = trust * d.trust_factor
                if target not in path_set:
                    if target not in result or result[target] < new_trust:
                        result[target] = new_trust
                    stack.append((target, new_trust, path_set | {current}))

        return result


# ─── Delegation Algebra Laws ─────────────────────────────────────

def verify_associativity(a_b_trust: float, b_c_trust: float,
                          c_d_trust: float) -> bool:
    """
    Verify: (A→B)→C→D ≡ A→(B→C)→D
    Sequential delegation is associative under multiplication.
    """
    left = (a_b_trust * b_c_trust) * c_d_trust
    right = a_b_trust * (b_c_trust * c_d_trust)
    return abs(left - right) < 1e-12


def verify_monotonicity(trust1: float, trust2: float,
                         attenuation: float) -> bool:
    """
    If trust1 >= trust2, then trust1 * att >= trust2 * att.
    Delegation preserves trust ordering.
    """
    if trust1 >= trust2:
        return trust1 * attenuation >= trust2 * attenuation - 1e-12
    return True


def parallel_composition(trusts: List[float], method: str = "max") -> float:
    """
    Compose parallel delegations.
    max: optimistic (take strongest path)
    min: pessimistic (take weakest)
    avg: balanced
    """
    if not trusts:
        return 0.0
    if method == "max":
        return max(trusts)
    elif method == "min":
        return min(trusts)
    elif method == "avg":
        return sum(trusts) / len(trusts)
    return max(trusts)


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
    print("Trust Delegation Calculus for Web4")
    print("Session 33, Track 7")
    print("=" * 70)

    # ── §1 Single Delegation ────────────────────────────────────
    print("\n§1 Single Delegation\n")

    d1 = Delegation("alice", "bob", 0.9)
    check("delegation_active", d1.is_active)
    check("trust_attenuation", abs(d1.attenuated_trust(1.0) - 0.9) < 1e-9)
    check("double_attenuation", abs(d1.attenuated_trust(0.8) - 0.72) < 1e-9)

    d_revoked = Delegation("alice", "bob", 0.9, revoked=True)
    check("revoked_inactive", not d_revoked.is_active)
    check("revoked_zero_trust", d_revoked.attenuated_trust(1.0) == 0.0)

    d_scoped = Delegation("alice", "bob", 0.9,
                           delegation_type=DelegationType.SCOPED,
                           capabilities=frozenset({Capability("read"), Capability("write")}))
    check("scoped_delegation", d_scoped.delegation_type == DelegationType.SCOPED)
    check("scoped_has_caps", len(d_scoped.capabilities) == 2)

    # ── §2 Delegation Chain ──────────────────────────────────────
    print("\n§2 Delegation Chain\n")

    chain = DelegationChain([
        Delegation("alice", "bob", 0.9),
        Delegation("bob", "carol", 0.8),
        Delegation("carol", "dave", 0.7),
    ])
    check("chain_source", chain.source == "alice")
    check("chain_target", chain.target == "dave")
    check("chain_depth", chain.depth == 3)

    # Effective trust: 0.9 × 0.8 × 0.7 = 0.504
    check("serial_trust", abs(chain.effective_trust - 0.504) < 1e-9,
          f"trust={chain.effective_trust}")
    check("chain_valid", chain.is_valid)
    check("chain_entities", chain.entities == ["alice", "bob", "carol", "dave"])

    # Broken chain
    bad_chain = DelegationChain([
        Delegation("alice", "bob", 0.9),
        Delegation("carol", "dave", 0.8),  # Not contiguous!
    ])
    check("broken_chain_invalid", not bad_chain.is_valid)

    # Chain with revoked link
    revoked_chain = DelegationChain([
        Delegation("alice", "bob", 0.9),
        Delegation("bob", "carol", 0.8, revoked=True),
    ])
    check("revoked_chain_zero_trust", revoked_chain.effective_trust == 0.0)

    # ── §3 Capability Restriction ────────────────────────────────
    print("\n§3 Capability Restriction Along Chain\n")

    cap_read = Capability("read")
    cap_write = Capability("write")
    cap_admin = Capability("admin")

    chain_scoped = DelegationChain([
        Delegation("alice", "bob", 0.9,
                   delegation_type=DelegationType.SCOPED,
                   capabilities=frozenset({cap_read, cap_write, cap_admin})),
        Delegation("bob", "carol", 0.8,
                   delegation_type=DelegationType.SCOPED,
                   capabilities=frozenset({cap_read, cap_write})),
    ])
    eff_caps = chain_scoped.effective_capabilities
    check("caps_intersection", eff_caps == frozenset({cap_read, cap_write}))
    check("admin_removed", cap_admin not in eff_caps)

    # Full delegation passes through
    chain_full = DelegationChain([
        Delegation("alice", "bob", 0.9, delegation_type=DelegationType.FULL),
        Delegation("bob", "carol", 0.8,
                   delegation_type=DelegationType.SCOPED,
                   capabilities=frozenset({cap_read})),
    ])
    check("full_then_scoped", chain_full.effective_capabilities == frozenset({cap_read}))

    # ── §4 Delegation Graph ──────────────────────────────────────
    print("\n§4 Delegation Graph\n")

    graph = DelegationGraph()
    graph.add_delegation(Delegation("alice", "bob", 0.9))
    graph.add_delegation(Delegation("bob", "carol", 0.8))
    graph.add_delegation(Delegation("alice", "carol", 0.7))  # parallel path
    graph.add_delegation(Delegation("carol", "dave", 0.85))

    chains = graph.find_chains("alice", "dave")
    check("chains_found", len(chains) >= 2, f"found {len(chains)}")

    eff = graph.effective_trust("alice", "dave")
    # Path 1: alice→bob→carol→dave = 0.9*0.8*0.85 = 0.612
    # Path 2: alice→carol→dave = 0.7*0.85 = 0.595
    check("effective_trust_max", abs(eff - 0.612) < 1e-3, f"eff={eff}")

    # No path
    eff_none = graph.effective_trust("dave", "alice")
    check("no_reverse_path", eff_none == 0.0)

    # ── §5 Revocation ────────────────────────────────────────────
    print("\n§5 Revocation\n")

    g2 = DelegationGraph()
    g2.add_delegation(Delegation("alice", "bob", 0.9))
    g2.add_delegation(Delegation("bob", "carol", 0.8))
    g2.add_delegation(Delegation("carol", "dave", 0.7))

    check("pre_revoke_trust", g2.effective_trust("alice", "dave") > 0)

    # Revoke bob→carol: should break chain to dave
    count = g2.revoke("bob", "carol")
    check("revocation_count", count == 1)
    check("post_revoke_no_trust", g2.effective_trust("alice", "dave") == 0.0)
    check("alice_bob_still_valid", g2.effective_trust("alice", "bob") > 0)

    # ── §6 Cascade Revocation ────────────────────────────────────
    print("\n§6 Cascade Revocation\n")

    g3 = DelegationGraph()
    g3.add_delegation(Delegation("root", "a", 0.9))
    g3.add_delegation(Delegation("a", "b", 0.8))
    g3.add_delegation(Delegation("b", "c", 0.7))
    g3.add_delegation(Delegation("b", "d", 0.6))

    # Revoke root→a: should cascade to b, c, d
    affected = g3.revoke_cascade("root", "a")
    check("cascade_affected_a", "a" in affected)
    check("cascade_affected_b", "b" in affected)
    check("cascade_affected_c", "c" in affected)
    check("cascade_affected_d", "d" in affected)
    check("cascade_all_revoked", g3.effective_trust("root", "c") == 0.0)

    # ── §7 Cycle Detection ───────────────────────────────────────
    print("\n§7 Cycle Detection\n")

    g4 = DelegationGraph()
    g4.add_delegation(Delegation("a", "b", 0.9))
    g4.add_delegation(Delegation("b", "c", 0.8))
    g4.add_delegation(Delegation("c", "a", 0.7))  # cycle!

    cycles = g4.detect_cycles()
    check("cycle_detected", len(cycles) > 0)
    # Cycle should contain a, b, c
    all_in_cycle = set()
    for cycle in cycles:
        all_in_cycle.update(cycle)
    check("cycle_contains_all", {"a", "b", "c"}.issubset(all_in_cycle))

    # No cycle
    g5 = DelegationGraph()
    g5.add_delegation(Delegation("x", "y", 0.9))
    g5.add_delegation(Delegation("y", "z", 0.8))
    check("no_cycle_in_dag", len(g5.detect_cycles()) == 0)

    # ── §8 Authority Set ─────────────────────────────────────────
    print("\n§8 Authority Set\n")

    g6 = DelegationGraph()
    g6.add_delegation(Delegation("ceo", "vp1", 0.95))
    g6.add_delegation(Delegation("ceo", "vp2", 0.90))
    g6.add_delegation(Delegation("vp1", "mgr1", 0.85))
    g6.add_delegation(Delegation("vp1", "mgr2", 0.80))
    g6.add_delegation(Delegation("vp2", "mgr3", 0.75))

    auth = g6.authority_set("ceo")
    check("auth_vp1", abs(auth.get("vp1", 0) - 0.95) < 1e-9)
    check("auth_mgr1", abs(auth.get("mgr1", 0) - 0.95 * 0.85) < 1e-9)
    check("auth_mgr3", abs(auth.get("mgr3", 0) - 0.90 * 0.75) < 1e-9)
    check("auth_covers_all", len(auth) == 5)

    # ── §9 Algebra Laws ─────────────────────────────────────────
    print("\n§9 Algebra Laws\n")

    # Associativity: (a*b)*c = a*(b*c)
    check("associativity_1", verify_associativity(0.9, 0.8, 0.7))
    check("associativity_2", verify_associativity(0.1, 0.5, 0.99))
    check("associativity_boundary", verify_associativity(1.0, 0.0, 0.5))

    # Monotonicity: higher trust → higher after attenuation
    check("monotonicity_1", verify_monotonicity(0.9, 0.5, 0.8))
    check("monotonicity_2", verify_monotonicity(1.0, 0.0, 0.5))

    # Parallel composition
    check("parallel_max", abs(parallel_composition([0.3, 0.7, 0.5], "max") - 0.7) < 1e-9)
    check("parallel_min", abs(parallel_composition([0.3, 0.7, 0.5], "min") - 0.3) < 1e-9)
    check("parallel_avg", abs(parallel_composition([0.3, 0.6, 0.9], "avg") - 0.6) < 1e-9)

    # Depth limit
    deep_chain = DelegationChain([
        Delegation("a", "b", 0.9, max_depth=2),
        Delegation("b", "c", 0.8, max_depth=2),
        Delegation("c", "d", 0.7, max_depth=2),  # idx 2 >= max_depth 2 → invalid
    ])
    check("depth_limit_enforced", not deep_chain.is_valid)

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
