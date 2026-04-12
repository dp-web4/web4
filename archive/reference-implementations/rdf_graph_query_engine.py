"""
RDF Graph Query Engine
=======================

Implements a SPARQL-like query engine over Web4 trust graphs:
triple store with indexed lookups, pattern matching, property path
traversal, graph-level metrics (centrality, clustering, shortest
paths), incremental indexing, and MRH-based access control.

Sections:
  S1  — Triple Store & Indexing
  S2  — Pattern Matching (SELECT)
  S3  — Property Path Traversal
  S4  — Graph Metrics (centrality, clustering)
  S5  — Shortest Trust Paths
  S6  — Delegation Chain Queries
  S7  — MRH-Filtered Access Control
  S8  — Aggregate Queries
  S9  — Graph Diff & Change Detection
  S10 — Incremental Updates
  S11 — Performance & Scale
"""

from __future__ import annotations
import math
import random
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set, Any, FrozenSet
from collections import defaultdict, deque
from enum import Enum


# ============================================================
# S1 — Triple Store & Indexing
# ============================================================

@dataclass(frozen=True)
class Triple:
    subject: str
    predicate: str
    obj: str  # 'object' is a Python builtin


@dataclass
class TripleStore:
    """Indexed triple store for RDF-like data."""
    triples: List[Triple] = field(default_factory=list)
    # SPO, POS, OSP indexes for O(1) lookup
    _spo: Dict[str, Dict[str, Set[str]]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(set)))
    _pos: Dict[str, Dict[str, Set[str]]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(set)))
    _osp: Dict[str, Dict[str, Set[str]]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(set)))
    _triple_set: Set[Triple] = field(default_factory=set)

    def add(self, subject: str, predicate: str, obj: str) -> bool:
        t = Triple(subject, predicate, obj)
        if t in self._triple_set:
            return False
        self.triples.append(t)
        self._triple_set.add(t)
        self._spo[subject][predicate].add(obj)
        self._pos[predicate][obj].add(subject)
        self._osp[obj][subject].add(predicate)
        return True

    def remove(self, subject: str, predicate: str, obj: str) -> bool:
        t = Triple(subject, predicate, obj)
        if t not in self._triple_set:
            return False
        self._triple_set.remove(t)
        self.triples = [tr for tr in self.triples if tr != t]
        self._spo[subject][predicate].discard(obj)
        self._pos[predicate][obj].discard(subject)
        self._osp[obj][subject].discard(predicate)
        return True

    def query_spo(self, subject: Optional[str] = None,
                  predicate: Optional[str] = None,
                  obj: Optional[str] = None) -> List[Triple]:
        """Query triples by subject, predicate, object (any can be None = wildcard)."""
        if subject and predicate and obj:
            t = Triple(subject, predicate, obj)
            return [t] if t in self._triple_set else []

        if subject and predicate:
            return [Triple(subject, predicate, o)
                    for o in self._spo.get(subject, {}).get(predicate, set())]

        if predicate and obj:
            return [Triple(s, predicate, obj)
                    for s in self._pos.get(predicate, {}).get(obj, set())]

        if subject:
            results = []
            for pred, objs in self._spo.get(subject, {}).items():
                for o in objs:
                    results.append(Triple(subject, pred, o))
            return results

        if predicate:
            results = []
            for o, subjects in self._pos.get(predicate, {}).items():
                for s in subjects:
                    results.append(Triple(s, predicate, o))
            return results

        if obj:
            results = []
            for s, preds in self._osp.get(obj, {}).items():
                for p in preds:
                    results.append(Triple(s, p, obj))
            return results

        return list(self.triples)

    def subjects(self) -> Set[str]:
        return set(self._spo.keys())

    def objects(self) -> Set[str]:
        return set(self._osp.keys())

    def predicates(self) -> Set[str]:
        return set(self._pos.keys())

    def entities(self) -> Set[str]:
        return self.subjects() | self.objects()


def test_section_1():
    checks = []

    store = TripleStore()
    store.add("alice", "trusts", "bob")
    store.add("alice", "trusts", "charlie")
    store.add("bob", "trusts", "charlie")
    store.add("alice", "has_role", "admin")

    checks.append(("triple_count", len(store.triples) == 4))

    # Duplicate rejected
    added = store.add("alice", "trusts", "bob")
    checks.append(("no_duplicate", not added and len(store.triples) == 4))

    # SPO query
    alice_trusts = store.query_spo(subject="alice", predicate="trusts")
    checks.append(("alice_trusts_2", len(alice_trusts) == 2))

    # PO query (who trusts charlie?)
    trusted_by = store.query_spo(predicate="trusts", obj="charlie")
    checks.append(("charlie_trusted_by_2", len(trusted_by) == 2))

    # Subject-only query
    alice_all = store.query_spo(subject="alice")
    checks.append(("alice_all_3", len(alice_all) == 3))

    # Remove
    removed = store.remove("alice", "trusts", "bob")
    checks.append(("removed", removed and len(store.triples) == 3))

    # Entity set
    entities = store.entities()
    checks.append(("entities", "alice" in entities and "bob" in entities and "charlie" in entities))

    # Remove non-existent
    checks.append(("remove_nonexistent", not store.remove("x", "y", "z")))

    return checks


# ============================================================
# S2 — Pattern Matching (SELECT)
# ============================================================

@dataclass
class Binding:
    """Variable binding in a query result."""
    variables: Dict[str, str]


def pattern_match(store: TripleStore, patterns: List[Tuple[str, str, str]],
                  filters: Optional[List[callable]] = None) -> List[Binding]:
    """Match triple patterns against store. Variables start with '?'."""

    def match_single(pattern: Tuple[str, str, str],
                     bindings: List[Binding]) -> List[Binding]:
        s_pat, p_pat, o_pat = pattern
        new_bindings = []

        for binding in bindings:
            # Resolve variables
            s = binding.variables.get(s_pat, s_pat) if s_pat.startswith("?") else s_pat
            p = binding.variables.get(p_pat, p_pat) if p_pat.startswith("?") else p_pat
            o = binding.variables.get(o_pat, o_pat) if o_pat.startswith("?") else o_pat

            # Query with resolved values
            s_query = s if not s.startswith("?") else None
            p_query = p if not p.startswith("?") else None
            o_query = o if not o.startswith("?") else None

            results = store.query_spo(s_query, p_query, o_query)

            for triple in results:
                new_vars = dict(binding.variables)
                ok = True

                if s_pat.startswith("?"):
                    if s_pat in new_vars and new_vars[s_pat] != triple.subject:
                        ok = False
                    new_vars[s_pat] = triple.subject
                elif triple.subject != s:
                    ok = False

                if p_pat.startswith("?"):
                    if p_pat in new_vars and new_vars[p_pat] != triple.predicate:
                        ok = False
                    new_vars[p_pat] = triple.predicate
                elif triple.predicate != p:
                    ok = False

                if o_pat.startswith("?"):
                    if o_pat in new_vars and new_vars[o_pat] != triple.obj:
                        ok = False
                    new_vars[o_pat] = triple.obj
                elif triple.obj != o:
                    ok = False

                if ok:
                    new_bindings.append(Binding(new_vars))

        return new_bindings

    bindings = [Binding({})]
    for pattern in patterns:
        bindings = match_single(pattern, bindings)
        if not bindings:
            break

    if filters:
        for f in filters:
            bindings = [b for b in bindings if f(b.variables)]

    return bindings


def test_section_2():
    checks = []

    store = TripleStore()
    store.add("alice", "trusts", "bob")
    store.add("alice", "trusts", "charlie")
    store.add("bob", "trusts", "charlie")
    store.add("charlie", "trusts", "dave")
    store.add("alice", "has_trust", "0.8")
    store.add("bob", "has_trust", "0.6")
    store.add("charlie", "has_trust", "0.7")

    # Simple pattern: who does alice trust?
    results = pattern_match(store, [("alice", "trusts", "?target")])
    targets = {b.variables["?target"] for b in results}
    checks.append(("alice_targets", targets == {"bob", "charlie"}))

    # Join: who trusts someone who trusts charlie?
    results = pattern_match(store, [
        ("?a", "trusts", "?b"),
        ("?b", "trusts", "charlie"),
    ])
    # alice→bob→charlie
    checks.append(("transitive", len(results) >= 1))
    checks.append(("transitive_alice", any(b.variables.get("?a") == "alice" for b in results)))

    # All trusts
    all_trusts = pattern_match(store, [("?s", "trusts", "?o")])
    checks.append(("all_trusts_4", len(all_trusts) == 4))

    # With filter: only entities with trust > 0.65
    results = pattern_match(
        store,
        [("?entity", "has_trust", "?trust")],
        filters=[lambda v: float(v.get("?trust", "0")) > 0.65]
    )
    checks.append(("filtered", len(results) == 2))  # alice 0.8, charlie 0.7

    # No results
    empty = pattern_match(store, [("dave", "trusts", "?x")])
    checks.append(("empty_result", len(empty) == 0))

    return checks


# ============================================================
# S3 — Property Path Traversal
# ============================================================

def traverse_path(store: TripleStore, start: str, predicates: List[str],
                  max_depth: int = 10) -> List[List[str]]:
    """Traverse a chain of predicates from start node."""
    if not predicates:
        return [[start]]

    paths = []
    current_pred = predicates[0]
    remaining = predicates[1:]

    neighbors = store.query_spo(subject=start, predicate=current_pred)
    for triple in neighbors:
        if remaining:
            sub_paths = traverse_path(store, triple.obj, remaining, max_depth - 1)
            for sp in sub_paths:
                paths.append([start] + sp)
        else:
            paths.append([start, triple.obj])

    return paths


def reachable(store: TripleStore, start: str, predicate: str,
              max_hops: int = 10) -> Dict[str, int]:
    """Find all reachable nodes via transitive closure. Returns {node: min_hops}."""
    visited = {start: 0}
    queue = deque([(start, 0)])

    while queue:
        node, depth = queue.popleft()
        if depth >= max_hops:
            continue
        neighbors = store.query_spo(subject=node, predicate=predicate)
        for triple in neighbors:
            if triple.obj not in visited:
                visited[triple.obj] = depth + 1
                queue.append((triple.obj, depth + 1))

    return visited


def test_section_3():
    checks = []

    store = TripleStore()
    store.add("alice", "delegates_to", "bob")
    store.add("bob", "delegates_to", "charlie")
    store.add("charlie", "delegates_to", "dave")
    store.add("alice", "trusts", "charlie")
    store.add("bob", "trusts", "dave")

    # Single-hop path
    paths = traverse_path(store, "alice", ["delegates_to"])
    checks.append(("single_hop", len(paths) == 1 and paths[0] == ["alice", "bob"]))

    # Multi-hop path
    paths = traverse_path(store, "alice", ["delegates_to", "delegates_to"])
    checks.append(("two_hop", len(paths) == 1 and paths[0] == ["alice", "bob", "charlie"]))

    # Three-hop
    paths = traverse_path(store, "alice", ["delegates_to", "delegates_to", "delegates_to"])
    checks.append(("three_hop", len(paths) == 1 and paths[0] == ["alice", "bob", "charlie", "dave"]))

    # Reachable via delegation
    reach = reachable(store, "alice", "delegates_to")
    checks.append(("reach_all", len(reach) == 4))  # alice, bob, charlie, dave
    checks.append(("reach_distance", reach["dave"] == 3))

    # Reachable via trust (different graph)
    trust_reach = reachable(store, "alice", "trusts")
    checks.append(("trust_reach", "charlie" in trust_reach and "dave" not in trust_reach))

    # Dead end
    dead = reachable(store, "dave", "delegates_to")
    checks.append(("dead_end", len(dead) == 1))  # only dave itself

    return checks


# ============================================================
# S4 — Graph Metrics
# ============================================================

def degree_centrality(store: TripleStore, predicate: str) -> Dict[str, float]:
    """Compute degree centrality for a given predicate."""
    all_entities = store.entities()
    n = len(all_entities)
    if n <= 1:
        return {e: 0.0 for e in all_entities}

    centrality = {}
    for entity in all_entities:
        out_degree = len(store.query_spo(subject=entity, predicate=predicate))
        in_degree = len(store.query_spo(predicate=predicate, obj=entity))
        centrality[entity] = (out_degree + in_degree) / (2 * (n - 1))
    return centrality


def clustering_coefficient(store: TripleStore, entity: str,
                            predicate: str) -> float:
    """Local clustering coefficient: fraction of neighbor pairs that are connected."""
    neighbors = set()
    for t in store.query_spo(subject=entity, predicate=predicate):
        neighbors.add(t.obj)
    for t in store.query_spo(predicate=predicate, obj=entity):
        neighbors.add(t.subject)

    if len(neighbors) < 2:
        return 0.0

    connections = 0
    neighbor_list = list(neighbors)
    for i in range(len(neighbor_list)):
        for j in range(i + 1, len(neighbor_list)):
            a, b = neighbor_list[i], neighbor_list[j]
            if store.query_spo(a, predicate, b) or store.query_spo(b, predicate, a):
                connections += 1

    possible = len(neighbors) * (len(neighbors) - 1) / 2
    return connections / possible if possible > 0 else 0.0


def betweenness_centrality(store: TripleStore, predicate: str) -> Dict[str, float]:
    """Approximate betweenness centrality via BFS shortest paths."""
    all_entities = list(store.entities())
    n = len(all_entities)
    centrality = {e: 0.0 for e in all_entities}

    for source in all_entities:
        # BFS from source
        dist = {source: 0}
        paths = {source: 1}
        predecessors = defaultdict(list)
        queue = deque([source])
        order = []

        while queue:
            v = queue.popleft()
            order.append(v)
            for t in store.query_spo(subject=v, predicate=predicate):
                w = t.obj
                if w not in dist:
                    dist[w] = dist[v] + 1
                    queue.append(w)
                    paths[w] = 0
                if dist[w] == dist[v] + 1:
                    paths[w] += paths[v]
                    predecessors[w].append(v)

        # Accumulate
        dependency = {e: 0.0 for e in all_entities}
        for w in reversed(order):
            for v in predecessors[w]:
                if paths[w] > 0:
                    dependency[v] += (paths[v] / paths[w]) * (1 + dependency[w])
            if w != source:
                centrality[w] += dependency[w]

    # Normalize
    if n > 2:
        norm = 2.0 / ((n - 1) * (n - 2))
        centrality = {e: c * norm for e, c in centrality.items()}

    return centrality


def test_section_4():
    checks = []

    store = TripleStore()
    # Star topology: alice is hub
    for name in ["bob", "charlie", "dave", "eve"]:
        store.add("alice", "trusts", name)
        store.add(name, "trusts", "alice")
    # Some cross-links
    store.add("bob", "trusts", "charlie")
    store.add("charlie", "trusts", "bob")

    # Degree centrality
    dc = degree_centrality(store, "trusts")
    checks.append(("alice_central", dc["alice"] > dc["dave"]))
    checks.append(("degree_bounded", all(0 <= v <= 1 for v in dc.values())))

    # Clustering
    cc_alice = clustering_coefficient(store, "alice", "trusts")
    checks.append(("hub_low_clustering", cc_alice < 0.5))  # hub connects to many non-connected nodes

    cc_bob = clustering_coefficient(store, "bob", "trusts")
    checks.append(("bob_higher_clustering", cc_bob >= cc_alice))  # bob's neighbors (alice, charlie) ARE connected

    # Betweenness
    bc = betweenness_centrality(store, "trusts")
    checks.append(("alice_betweenness", bc["alice"] >= bc["dave"]))

    # Isolated node
    store.add("isolate", "has_name", "nobody")
    cc_isolate = clustering_coefficient(store, "isolate", "trusts")
    checks.append(("isolate_zero_clustering", cc_isolate == 0.0))

    return checks


# ============================================================
# S5 — Shortest Trust Paths
# ============================================================

def shortest_trust_path(store: TripleStore, source: str, target: str,
                        predicate: str = "trusts",
                        trust_weights: Optional[Dict[str, float]] = None) -> Optional[List[str]]:
    """Find shortest path using BFS (unweighted) or Dijkstra (weighted by trust)."""
    if trust_weights:
        # Dijkstra with edge weight = 1 / trust (higher trust = shorter path)
        import heapq
        dist = {source: 0.0}
        prev = {}
        heap = [(0.0, source)]
        visited = set()

        while heap:
            d, node = heapq.heappop(heap)
            if node in visited:
                continue
            visited.add(node)
            if node == target:
                break

            for t in store.query_spo(subject=node, predicate=predicate):
                neighbor = t.obj
                trust = trust_weights.get(neighbor, 0.5)
                if trust <= 0:
                    continue
                weight = 1.0 / trust
                new_dist = d + weight
                if new_dist < dist.get(neighbor, float('inf')):
                    dist[neighbor] = new_dist
                    prev[neighbor] = node
                    heapq.heappush(heap, (new_dist, neighbor))
    else:
        # BFS
        prev = {}
        visited = {source}
        queue = deque([source])

        while queue:
            node = queue.popleft()
            if node == target:
                break
            for t in store.query_spo(subject=node, predicate=predicate):
                if t.obj not in visited:
                    visited.add(t.obj)
                    prev[t.obj] = node
                    queue.append(t.obj)

    if target not in prev and target != source:
        return None

    # Reconstruct path
    path = [target]
    while path[-1] != source:
        path.append(prev[path[-1]])
    return list(reversed(path))


def test_section_5():
    checks = []

    store = TripleStore()
    store.add("alice", "trusts", "bob")
    store.add("bob", "trusts", "charlie")
    store.add("charlie", "trusts", "dave")
    store.add("alice", "trusts", "eve")
    store.add("eve", "trusts", "dave")

    # BFS shortest path
    path = shortest_trust_path(store, "alice", "dave")
    checks.append(("path_found", path is not None))
    checks.append(("path_short", len(path) == 3))  # alice→eve→dave (shorter than alice→bob→charlie→dave)

    # Same node
    self_path = shortest_trust_path(store, "alice", "alice")
    checks.append(("self_path", self_path == ["alice"]))

    # Unreachable
    store.add("frank", "trusts", "grace")
    no_path = shortest_trust_path(store, "alice", "grace")
    checks.append(("no_path", no_path is None))

    # Weighted path (higher trust = preferred)
    weights = {"bob": 0.9, "charlie": 0.9, "dave": 0.8, "eve": 0.3}
    w_path = shortest_trust_path(store, "alice", "dave", trust_weights=weights)
    checks.append(("weighted_path", w_path is not None))
    # With weights: eve has low trust (0.3), bob/charlie have high trust (0.9)
    # alice→bob→charlie→dave cost = 1/0.9 + 1/0.9 + 1/0.8 = 1.11+1.11+1.25 = 3.47
    # alice→eve→dave cost = 1/0.3 + 1/0.8 = 3.33+1.25 = 4.58
    # So high-trust path (via bob) should be preferred
    checks.append(("weighted_prefers_trust", w_path[1] == "bob"))

    return checks


# ============================================================
# S6 — Delegation Chain Queries
# ============================================================

def delegation_chain(store: TripleStore, entity: str) -> List[str]:
    """Find the delegation chain from entity to root (upward)."""
    chain = [entity]
    visited = {entity}
    current = entity

    while True:
        # Who delegates TO current? (current's delegator)
        delegators = store.query_spo(predicate="delegates_to", obj=current)
        if not delegators:
            break
        parent = delegators[0].subject
        if parent in visited:
            break  # cycle detection
        chain.append(parent)
        visited.add(parent)
        current = parent

    return list(reversed(chain))


def scope_narrowing_check(store: TripleStore, entity: str) -> bool:
    """Verify that delegation scopes narrow monotonically."""
    # Scopes stored as "has_scope" with numeric values
    chain = delegation_chain(store, entity)
    if len(chain) < 2:
        return True

    scopes = []
    for e in chain:
        scope_triples = store.query_spo(subject=e, predicate="has_scope")
        if scope_triples:
            scopes.append(float(scope_triples[0].obj))
        else:
            scopes.append(1.0)  # default full scope

    # Each scope ≤ previous (monotonically narrowing)
    return all(scopes[i] >= scopes[i + 1] for i in range(len(scopes) - 1))


def test_section_6():
    checks = []

    store = TripleStore()
    store.add("root", "delegates_to", "manager")
    store.add("manager", "delegates_to", "worker")
    store.add("root", "has_scope", "1.0")
    store.add("manager", "has_scope", "0.7")
    store.add("worker", "has_scope", "0.4")

    # Chain from worker up
    chain = delegation_chain(store, "worker")
    checks.append(("chain_complete", chain == ["root", "manager", "worker"]))

    # Chain from root
    root_chain = delegation_chain(store, "root")
    checks.append(("root_is_root", root_chain == ["root"]))

    # Scope narrowing
    checks.append(("scope_narrows", scope_narrowing_check(store, "worker")))

    # Violating scope narrowing
    store.add("rogue", "has_scope", "0.9")
    store.add("worker", "delegates_to", "rogue")
    checks.append(("scope_violation", not scope_narrowing_check(store, "rogue")))

    # Cycle detection
    store2 = TripleStore()
    store2.add("a", "delegates_to", "b")
    store2.add("b", "delegates_to", "a")
    chain_cycle = delegation_chain(store2, "b")
    checks.append(("cycle_safe", len(chain_cycle) <= 3))

    return checks


# ============================================================
# S7 — MRH-Filtered Access Control
# ============================================================

class MRHZone(Enum):
    SELF = 0
    DIRECT = 1
    INDIRECT = 2
    PERIPHERAL = 3
    BEYOND = 4


def compute_mrh_zone(store: TripleStore, viewer: str, target: str,
                     predicate: str = "trusts") -> MRHZone:
    """Compute MRH zone of target relative to viewer."""
    if viewer == target:
        return MRHZone.SELF

    reach = reachable(store, viewer, predicate, max_hops=4)
    hops = reach.get(target)

    if hops is None:
        return MRHZone.BEYOND
    if hops == 1:
        return MRHZone.DIRECT
    if hops == 2:
        return MRHZone.INDIRECT
    return MRHZone.PERIPHERAL


def filtered_query(store: TripleStore, viewer: str, patterns: List[Tuple[str, str, str]],
                   max_zone: MRHZone = MRHZone.INDIRECT,
                   trust_predicate: str = "trusts") -> List[Binding]:
    """Execute query with MRH access control — only return results within viewer's zone."""
    all_results = pattern_match(store, patterns)

    filtered = []
    for binding in all_results:
        # Check all entities in the binding are within the allowed zone
        all_ok = True
        for var_name, entity in binding.variables.items():
            zone = compute_mrh_zone(store, viewer, entity, trust_predicate)
            if zone.value > max_zone.value:
                all_ok = False
                break
        if all_ok:
            filtered.append(binding)

    return filtered


def test_section_7():
    checks = []

    store = TripleStore()
    store.add("alice", "trusts", "bob")
    store.add("bob", "trusts", "charlie")
    store.add("charlie", "trusts", "dave")
    store.add("dave", "trusts", "eve")
    store.add("frank", "trusts", "grace")  # disconnected

    # MRH zones
    checks.append(("self_zone", compute_mrh_zone(store, "alice", "alice") == MRHZone.SELF))
    checks.append(("direct_zone", compute_mrh_zone(store, "alice", "bob") == MRHZone.DIRECT))
    checks.append(("indirect_zone", compute_mrh_zone(store, "alice", "charlie") == MRHZone.INDIRECT))
    checks.append(("peripheral_zone", compute_mrh_zone(store, "alice", "dave") == MRHZone.PERIPHERAL))
    checks.append(("beyond_zone", compute_mrh_zone(store, "alice", "frank") == MRHZone.BEYOND))

    # Filtered query: alice can see DIRECT and INDIRECT
    results = filtered_query(store, "alice", [("?x", "trusts", "?y")],
                            max_zone=MRHZone.INDIRECT)
    entities_seen = set()
    for b in results:
        entities_seen.update(b.variables.values())
    checks.append(("filtered_no_dave", "dave" not in entities_seen))
    checks.append(("filtered_has_bob", "bob" in entities_seen))
    checks.append(("filtered_has_charlie", "charlie" in entities_seen))

    # Strict SELF-only
    self_results = filtered_query(store, "alice", [("?x", "trusts", "?y")],
                                  max_zone=MRHZone.SELF)
    checks.append(("self_only_empty", len(self_results) == 0))  # no trust triple has both S and O = alice

    return checks


# ============================================================
# S8 — Aggregate Queries
# ============================================================

def aggregate_query(store: TripleStore, pattern: Tuple[str, str, str],
                    group_by: str, agg: str = "count") -> Dict[str, float]:
    """Aggregate over matched triples."""
    results = pattern_match(store, [pattern])

    groups = defaultdict(list)
    for b in results:
        key = b.variables.get(group_by, "unknown")
        groups[key].append(b)

    aggregated = {}
    for key, bindings in groups.items():
        if agg == "count":
            aggregated[key] = float(len(bindings))
        elif agg.startswith("sum:"):
            var = agg.split(":")[1]
            aggregated[key] = sum(float(b.variables.get(var, 0)) for b in bindings)
        elif agg.startswith("avg:"):
            var = agg.split(":")[1]
            vals = [float(b.variables.get(var, 0)) for b in bindings]
            aggregated[key] = sum(vals) / len(vals) if vals else 0.0
    return aggregated


def test_section_8():
    checks = []

    store = TripleStore()
    for i in range(5):
        store.add(f"e{i}", "has_role", "worker")
    for i in range(3):
        store.add(f"e{i}", "has_role", "admin")
    store.add("e0", "has_trust", "0.8")
    store.add("e1", "has_trust", "0.6")
    store.add("e2", "has_trust", "0.7")

    # Count by role
    role_counts = aggregate_query(store, ("?entity", "has_role", "?role"),
                                  group_by="?role", agg="count")
    checks.append(("worker_count", role_counts.get("worker") == 5))
    checks.append(("admin_count", role_counts.get("admin") == 3))

    # Count by entity
    entity_roles = aggregate_query(store, ("?entity", "has_role", "?role"),
                                   group_by="?entity", agg="count")
    checks.append(("e0_two_roles", entity_roles.get("e0") == 2))
    checks.append(("e3_one_role", entity_roles.get("e3") == 1))

    # Average trust
    avg = aggregate_query(store, ("?entity", "has_trust", "?trust"),
                          group_by="?entity", agg="avg:?trust")
    checks.append(("avg_trust", abs(avg.get("e0", 0) - 0.8) < 0.01))

    return checks


# ============================================================
# S9 — Graph Diff & Change Detection
# ============================================================

def graph_diff(old_store: TripleStore, new_store: TripleStore) -> Dict[str, List[Triple]]:
    """Compute added and removed triples between two graph states."""
    old_set = old_store._triple_set
    new_set = new_store._triple_set

    added = [t for t in new_set if t not in old_set]
    removed = [t for t in old_set if t not in new_set]
    return {"added": added, "removed": removed}


def detect_structural_changes(diff: Dict[str, List[Triple]]) -> Dict[str, int]:
    """Classify changes by type."""
    changes = defaultdict(int)
    for t in diff["added"]:
        changes[f"added_{t.predicate}"] += 1
    for t in diff["removed"]:
        changes[f"removed_{t.predicate}"] += 1
    return dict(changes)


def test_section_9():
    checks = []

    old = TripleStore()
    old.add("alice", "trusts", "bob")
    old.add("alice", "trusts", "charlie")
    old.add("bob", "trusts", "charlie")

    new = TripleStore()
    new.add("alice", "trusts", "bob")
    new.add("alice", "trusts", "dave")
    new.add("bob", "trusts", "charlie")
    new.add("eve", "trusts", "alice")

    diff = graph_diff(old, new)
    checks.append(("added_count", len(diff["added"]) == 2))  # alice→dave, eve→alice
    checks.append(("removed_count", len(diff["removed"]) == 1))  # alice→charlie

    changes = detect_structural_changes(diff)
    checks.append(("added_trusts", changes.get("added_trusts", 0) == 2))
    checks.append(("removed_trusts", changes.get("removed_trusts", 0) == 1))

    # No changes
    same_diff = graph_diff(old, old)
    checks.append(("no_changes", len(same_diff["added"]) == 0 and len(same_diff["removed"]) == 0))

    return checks


# ============================================================
# S10 — Incremental Updates
# ============================================================

@dataclass
class IncrementalStore(TripleStore):
    """Triple store with change tracking for incremental updates."""
    _changelog: List[Tuple[str, Triple]] = field(default_factory=list)  # ("add"/"remove", triple)
    _version: int = 0

    def add(self, subject: str, predicate: str, obj: str) -> bool:
        result = super().add(subject, predicate, obj)
        if result:
            self._changelog.append(("add", Triple(subject, predicate, obj)))
            self._version += 1
        return result

    def remove(self, subject: str, predicate: str, obj: str) -> bool:
        result = super().remove(subject, predicate, obj)
        if result:
            self._changelog.append(("remove", Triple(subject, predicate, obj)))
            self._version += 1
        return result

    def changes_since(self, version: int) -> List[Tuple[str, Triple]]:
        return self._changelog[version:]

    @property
    def version(self) -> int:
        return self._version


def test_section_10():
    checks = []

    store = IncrementalStore()
    store.add("alice", "trusts", "bob")
    store.add("bob", "trusts", "charlie")

    checks.append(("version_2", store.version == 2))

    v1 = store.version
    store.add("charlie", "trusts", "dave")
    store.remove("alice", "trusts", "bob")

    changes = store.changes_since(v1)
    checks.append(("changes_2", len(changes) == 2))
    checks.append(("change_types", changes[0][0] == "add" and changes[1][0] == "remove"))

    # Version monotonically increases
    checks.append(("version_increases", store.version == 4))

    # Duplicate add doesn't create changelog entry
    store.add("bob", "trusts", "charlie")  # already exists
    checks.append(("no_dup_changelog", store.version == 4))

    return checks


# ============================================================
# S11 — Performance & Scale
# ============================================================

def test_section_11():
    checks = []

    import time as time_mod

    # Build large graph
    store = TripleStore()
    random.seed(42)
    n = 1000

    start = time_mod.perf_counter()
    for i in range(n):
        # Each entity trusts 3-5 random others
        for _ in range(random.randint(3, 5)):
            target = random.randint(0, n - 1)
            if target != i:
                store.add(f"e{i}", "trusts", f"e{target}")
        store.add(f"e{i}", "has_trust", f"{random.uniform(0.1, 0.95):.3f}")
    build_time = time_mod.perf_counter() - start
    checks.append(("build_1k_fast", build_time < 5.0))

    # Query performance
    start = time_mod.perf_counter()
    for _ in range(1000):
        i = random.randint(0, n - 1)
        store.query_spo(subject=f"e{i}", predicate="trusts")
    query_time = time_mod.perf_counter() - start
    checks.append(("1k_queries_fast", query_time < 2.0))

    # Pattern match performance
    start = time_mod.perf_counter()
    for _ in range(100):
        pattern_match(store, [(f"e{random.randint(0, n-1)}", "trusts", "?target")])
    pattern_time = time_mod.perf_counter() - start
    checks.append(("100_patterns_fast", pattern_time < 2.0))

    # Reachability
    start = time_mod.perf_counter()
    reach = reachable(store, "e0", "trusts", max_hops=3)
    reach_time = time_mod.perf_counter() - start
    checks.append(("reachability_fast", reach_time < 2.0))
    checks.append(("reach_many", len(reach) > 50))  # well-connected graph

    # Degree centrality
    start = time_mod.perf_counter()
    dc = degree_centrality(store, "trusts")
    dc_time = time_mod.perf_counter() - start
    checks.append(("centrality_computed", len(dc) > 0))
    checks.append(("centrality_fast", dc_time < 10.0))

    return checks


# ============================================================
# Main
# ============================================================

def main():
    random.seed(42)

    sections = [
        ("S1 Triple Store & Indexing", test_section_1),
        ("S2 Pattern Matching (SELECT)", test_section_2),
        ("S3 Property Path Traversal", test_section_3),
        ("S4 Graph Metrics", test_section_4),
        ("S5 Shortest Trust Paths", test_section_5),
        ("S6 Delegation Chain Queries", test_section_6),
        ("S7 MRH-Filtered Access Control", test_section_7),
        ("S8 Aggregate Queries", test_section_8),
        ("S9 Graph Diff & Change Detection", test_section_9),
        ("S10 Incremental Updates", test_section_10),
        ("S11 Performance & Scale", test_section_11),
    ]

    total_pass = 0
    total_fail = 0
    failures = []

    for name, test_fn in sections:
        checks = test_fn()
        passed = sum(1 for _, ok in checks if ok)
        failed = sum(1 for _, ok in checks if not ok)
        total_pass += passed
        total_fail += failed
        status = "✓" if failed == 0 else "✗"
        print(f"  {status} {name}: {passed}/{passed+failed}")
        for check_name, ok in checks:
            if not ok:
                failures.append(f"    FAIL: {check_name}")

    print(f"\nTotal: {total_pass}/{total_pass+total_fail}")
    if failures:
        print(f"\nFailed checks:")
        for f in failures:
            print(f)


if __name__ == "__main__":
    main()
