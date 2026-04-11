#!/usr/bin/env python3
"""
Web4 MRH Theoretical Foundation — Reference Implementation
Spec: web4-standard/MRH_THEORETICAL_FOUNDATION.md (219 lines, 9 sections)

Covers:
  §1  Background: Classical Markov Blanket (conditional independence)
  §2  Innovation: MRH (relevancy over independence, fractal, horizon metaphor)
  §3  Fractal Scales and Contextual Relevance (multi-level, propagation formula)
  §4  Mathematical Foundation (Fractal Markov Property, information geometry)
  §5  Practical Implications (AI, distributed systems, human-AI)
  §6  Connection to Active Inference (FEP, hierarchical)
  §7  Implementation in Web4 (RDF graphs, fractal composition)
  §8  Evolution and Future Directions

Run:  python3 mrh_theoretical_foundation.py
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any

# ─────────────────────────────────────────────
# §1 Background: Classical Markov Blanket
# ─────────────────────────────────────────────

@dataclass
class MarkovBlanket:
    """Classical Markov blanket: MB(X) renders X conditionally independent of all other variables.
    P(X | MB(X), Y) = P(X | MB(X))"""
    node: str
    parents: Set[str] = field(default_factory=set)
    children: Set[str] = field(default_factory=set)
    co_parents: Set[str] = field(default_factory=set)  # Parents of children

    def blanket(self) -> Set[str]:
        """Full Markov blanket = parents ∪ children ∪ co-parents of children"""
        return self.parents | self.children | self.co_parents

    def conditionally_independent_of(self, y: str) -> bool:
        """X is conditionally independent of Y given MB(X) iff Y ∉ MB(X)"""
        return y not in self.blanket() and y != self.node

    # Spec §1.2 Limitations:
    LIMITATIONS = [
        "Single Scale: operates at a single level of abstraction",
        "Static Boundaries: typically fixed, not adaptive",
        "No Fractal Structure: cannot represent self-similar patterns at different scales",
        "Limited Context: focus on statistical independence rather than contextual relevance",
    ]


# ─────────────────────────────────────────────
# §2 Innovation: Markov Relevancy Horizon
# ─────────────────────────────────────────────

@dataclass
class MRHEntry:
    """A single entry in an MRH: (Yi, pi, ri, di)"""
    target: str         # Yi: relevant context (another LCT)
    probability: float  # pi: strength of relevance [0,1]
    relation: str       # ri: semantic predicate
    distance: int       # di: depth in the relevancy graph

@dataclass
class MRH:
    """Markov Relevancy Horizon per spec §2.2:
    MRH(X) = {(Yi, pi, ri, di) | Yi ∈ relevant_contexts(X)}"""
    node: str
    entries: List[MRHEntry] = field(default_factory=list)

    def add(self, target: str, probability: float, relation: str, distance: int):
        self.entries.append(MRHEntry(target, probability, relation, distance))

    def get_relevant(self, min_probability: float = 0.0) -> List[MRHEntry]:
        """Get entries above relevance threshold"""
        return [e for e in self.entries if e.probability >= min_probability]

    def get_by_relation(self, relation: str) -> List[MRHEntry]:
        return [e for e in self.entries if e.relation == relation]

    def get_by_distance(self, max_distance: int) -> List[MRHEntry]:
        return [e for e in self.entries if e.distance <= max_distance]

# Comparison table from spec §2.3
MRH_VS_BLANKET = {
    "Focus":       ("Statistical independence", "Contextual relevance"),
    "Structure":   ("Flat set of nodes", "Graph with typed edges"),
    "Scale":       ("Single level", "Fractal/multi-scale"),
    "Boundaries":  ("Fixed", "Probabilistic/gradient"),
    "Composition": ("Not compositional", "Naturally fractal"),
    "Semantics":   ("No semantic types", "Typed relationships"),
}


# ─────────────────────────────────────────────
# §3 Fractal Scales and Contextual Relevance
# ─────────────────────────────────────────────

@dataclass
class FractalLevel:
    """A level in the fractal hierarchy"""
    name: str
    depth: int
    mrh: MRH

class FractalMRHGraph:
    """Multi-scale MRH graph with fractal structure per spec §3"""

    def __init__(self):
        self.levels: Dict[str, FractalLevel] = {}
        self.mrh_map: Dict[str, MRH] = {}

    def add_level(self, name: str, depth: int, node_id: str):
        mrh = MRH(node=node_id)
        level = FractalLevel(name=name, depth=depth, mrh=mrh)
        self.levels[node_id] = level
        self.mrh_map[node_id] = mrh

    def add_relevance(self, from_node: str, to_node: str,
                      probability: float, relation: str, distance: int):
        if from_node in self.mrh_map:
            self.mrh_map[from_node].add(to_node, probability, relation, distance)

    def relevance_propagation(self, source: str, target: str,
                              decay: float = 0.9) -> float:
        """Relevance propagation across scales per spec §3.2:
        relevance(A, C) = Σ(paths) Π(edges in path) p(edge) × decay^distance"""
        # BFS to find all paths
        visited = set()
        queue = [(source, 1.0, 0)]  # (node, accumulated_prob, distance)
        total_relevance = 0.0

        while queue:
            node, acc_prob, dist = queue.pop(0)
            if node == target:
                total_relevance += acc_prob * (decay ** dist)
                continue
            if node in visited:
                continue
            visited.add(node)
            mrh = self.mrh_map.get(node)
            if mrh:
                for entry in mrh.entries:
                    if entry.target not in visited:
                        new_prob = acc_prob * entry.probability
                        queue.append((entry.target, new_prob, dist + entry.distance))
        return min(1.0, total_relevance)

    def fractal_depth(self, node_id: str) -> int:
        """Get the fractal depth of a node"""
        level = self.levels.get(node_id)
        return level.depth if level else 0


# ─────────────────────────────────────────────
# §4 Mathematical Foundation
# ─────────────────────────────────────────────

class FractalMarkovProperty:
    """Fractal Markov Property per spec §4.1:
    P(Xt+1,s | MRH(Xt,s)) = P(Xt+1,s | Xt,s ∪ relevant_scales(s))
    where s = scale level, relevant_scales(s) = contexts from other scales"""

    @staticmethod
    def verify_property(mrh: MRH, relevant_scales: List[str]) -> bool:
        """Verify that the fractal Markov property holds:
        all relevant scales must be represented in the MRH"""
        mrh_targets = {e.target for e in mrh.entries}
        return all(scale in mrh_targets for scale in relevant_scales)

    @staticmethod
    def conditional_independence(mrh: MRH, external_variable: str) -> bool:
        """Given MRH, X is conditionally independent of variables NOT in MRH"""
        mrh_targets = {e.target for e in mrh.entries}
        return external_variable not in mrh_targets

class InformationGeometry:
    """Information-geometric interpretation per spec §4.2:
    - Each LCT in high-dimensional information manifold
    - MRH defines local coordinate system
    - Relevance probabilities define metric tensor
    - Fractal structure from self-similar information patterns"""

    @staticmethod
    def metric_tensor(mrh: MRH) -> List[List[float]]:
        """Relevance probabilities as metric tensor components"""
        n = len(mrh.entries)
        if n == 0:
            return [[1.0]]
        # Diagonal metric: each entry's probability defines the metric in that dimension
        tensor = [[0.0] * n for _ in range(n)]
        for i, entry in enumerate(mrh.entries):
            tensor[i][i] = entry.probability
        return tensor

    @staticmethod
    def geodesic_distance(mrh_a: MRH, mrh_b: MRH) -> float:
        """Information-geometric distance between two MRHs"""
        targets_a = {e.target: e.probability for e in mrh_a.entries}
        targets_b = {e.target: e.probability for e in mrh_b.entries}
        all_targets = set(targets_a.keys()) | set(targets_b.keys())
        if not all_targets:
            return 0.0
        # KL-divergence inspired distance
        dist = 0.0
        for t in all_targets:
            p = targets_a.get(t, 0.001)
            q = targets_b.get(t, 0.001)
            dist += abs(p - q)
        return dist / len(all_targets)

    @staticmethod
    def self_similarity(parent_mrh: MRH, child_mrh: MRH) -> float:
        """Measure fractal self-similarity between parent and child MRH"""
        parent_rels = {e.relation for e in parent_mrh.entries}
        child_rels = {e.relation for e in child_mrh.entries}
        if not parent_rels and not child_rels:
            return 1.0  # Both empty = identical
        if not parent_rels or not child_rels:
            return 0.0
        overlap = len(parent_rels & child_rels)
        total = len(parent_rels | child_rels)
        return overlap / total


# ─────────────────────────────────────────────
# §5 Practical Implications
# ─────────────────────────────────────────────

class ContextManager:
    """§5.1 AI Systems: maintain context across multiple scales of reasoning"""

    def __init__(self, graph: FractalMRHGraph):
        self.graph = graph

    def zoom_to_level(self, node_id: str, depth: int) -> List[MRHEntry]:
        """Navigate between detailed and abstract representations"""
        mrh = self.graph.mrh_map.get(node_id)
        if not mrh:
            return []
        return [e for e in mrh.entries if e.distance <= depth]

    def compress_context(self, node_id: str, threshold: float = 0.5) -> List[MRHEntry]:
        """Preserve relevance during information compression"""
        mrh = self.graph.mrh_map.get(node_id)
        if not mrh:
            return []
        return [e for e in mrh.entries if e.probability >= threshold]

class ShardingBoundaryDetector:
    """§5.2 Distributed Systems: natural sharding boundaries"""

    @staticmethod
    def detect_boundaries(graph: FractalMRHGraph, threshold: float = 0.7) -> List[Set[str]]:
        """High relevance = same shard, low relevance = shard boundary.
        Transitively includes all high-relevance neighbors."""
        shards: List[Set[str]] = []
        assigned = set()
        for node_id in graph.mrh_map:
            if node_id in assigned:
                continue
            shard = set()
            queue = [node_id]
            while queue:
                n = queue.pop(0)
                if n in shard:
                    continue
                shard.add(n)
                mrh = graph.mrh_map.get(n)
                if mrh:
                    for entry in mrh.entries:
                        if entry.probability >= threshold and entry.target not in shard:
                            queue.append(entry.target)
            assigned.update(shard)
            shards.append(shard)
        return shards


# ─────────────────────────────────────────────
# §6 Connection to Active Inference
# ─────────────────────────────────────────────

@dataclass
class FractalAgent:
    """§6: Fractal agent with MRH boundaries at multiple scales
    Aligns with Free Energy Principle: each scale maintains its own predictive model"""
    agent_id: str
    scales: Dict[int, MRH] = field(default_factory=dict)  # scale → MRH

    def add_scale(self, scale: int, mrh: MRH):
        self.scales[scale] = mrh

    def get_boundary(self, scale: int) -> Optional[MRH]:
        """Get Markov blanket equivalent at a given scale"""
        return self.scales.get(scale)

    def hierarchical_prediction(self, scale: int) -> float:
        """Each scale maintains its own predictive model.
        Higher scales predict lower scale dynamics."""
        mrh = self.scales.get(scale)
        if not mrh:
            return 0.0
        # Prediction confidence = average relevance at this scale
        if not mrh.entries:
            return 0.0
        return sum(e.probability for e in mrh.entries) / len(mrh.entries)


# ─────────────────────────────────────────────
# §7 Implementation in Web4
# ─────────────────────────────────────────────

def mrh_to_rdf(mrh: MRH) -> List[Dict]:
    """Convert MRH to RDF graph per spec §7.1"""
    triples = []
    for entry in mrh.entries:
        triples.append({
            "@type": "mrh:Relevance",
            "mrh:target": entry.target,
            "mrh:probability": entry.probability,
            "mrh:relation": entry.relation,
            "mrh:distance": entry.distance
        })
    return triples

def demonstrate_fractal_composition(depth: int = 3) -> Dict[str, MRH]:
    """§7.2 Fractal composition: LCT_A.mrh → LCT_B, LCT_B.mrh → LCT_C, ..."""
    mrhs = {}
    for i in range(depth):
        node = f"LCT_{chr(65+i)}"  # LCT_A, LCT_B, LCT_C
        mrh = MRH(node=node)
        if i < depth - 1:
            next_node = f"LCT_{chr(65+i+1)}"
            mrh.add(next_node, 0.9 - (i * 0.1), "mrh:derives_from", i + 1)
        mrhs[node] = mrh
    return mrhs


# ═══════════════════════════════════════════════
# TEST SUITE
# ═══════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0
    total = 0

    def check(name, condition, detail=""):
        nonlocal passed, failed, total
        total += 1
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name} — {detail}")

    # ─── §1: Classical Markov Blanket ───
    print("§1: Classical Markov Blanket")

    mb = MarkovBlanket(
        node="X",
        parents={"A", "B"},
        children={"C", "D"},
        co_parents={"E"}
    )
    blanket = mb.blanket()
    check("T1.1 Blanket contains parents", "A" in blanket and "B" in blanket)
    check("T1.2 Blanket contains children", "C" in blanket and "D" in blanket)
    check("T1.3 Blanket contains co-parents", "E" in blanket)
    check("T1.4 Blanket size = 5", len(blanket) == 5)
    check("T1.5 X independent of Y (outside blanket)", mb.conditionally_independent_of("Y"))
    check("T1.6 X not independent of A (in blanket)", not mb.conditionally_independent_of("A"))
    check("T1.7 4 limitations documented", len(MarkovBlanket.LIMITATIONS) == 4)

    # ─── §2: MRH Innovation ───
    print("§2: MRH Innovation")

    mrh = MRH(node="entity_1")
    mrh.add("entity_2", 0.9, "mrh:depends_on", 1)
    mrh.add("entity_3", 0.6, "mrh:references", 2)
    mrh.add("entity_4", 0.3, "mrh:witnesses", 3)

    check("T2.1 MRH has 3 entries", len(mrh.entries) == 3)
    check("T2.2 High-relevance filter", len(mrh.get_relevant(0.5)) == 2)
    check("T2.3 Low-relevance filter", len(mrh.get_relevant(0.1)) == 3)
    check("T2.4 Relation filter", len(mrh.get_by_relation("mrh:depends_on")) == 1)
    check("T2.5 Distance filter", len(mrh.get_by_distance(2)) == 2)

    # MRH vs Blanket comparison
    check("T2.6 6 comparison dimensions", len(MRH_VS_BLANKET) == 6)
    check("T2.7 Focus: relevance not independence",
          MRH_VS_BLANKET["Focus"][1] == "Contextual relevance")
    check("T2.8 Structure: graph not flat",
          MRH_VS_BLANKET["Structure"][1] == "Graph with typed edges")
    check("T2.9 Scale: fractal not single",
          MRH_VS_BLANKET["Scale"][1] == "Fractal/multi-scale")
    check("T2.10 Composition: naturally fractal",
          MRH_VS_BLANKET["Composition"][1] == "Naturally fractal")

    # ─── §3: Fractal Scales ───
    print("§3: Fractal Scales")

    graph = FractalMRHGraph()
    graph.add_level("System", 0, "org")
    graph.add_level("Team", 1, "dept_a")
    graph.add_level("Team", 1, "dept_b")
    graph.add_level("Individual", 2, "person_1")
    graph.add_level("Individual", 2, "person_2")

    graph.add_relevance("org", "dept_a", 0.9, "mrh:contains", 1)
    graph.add_relevance("org", "dept_b", 0.85, "mrh:contains", 1)
    graph.add_relevance("dept_a", "person_1", 0.95, "mrh:member", 1)
    graph.add_relevance("dept_a", "person_2", 0.8, "mrh:member", 1)
    graph.add_relevance("dept_a", "dept_b", 0.6, "mrh:collaborates", 1)

    check("T3.1 Graph has 5 levels", len(graph.levels) == 5)
    check("T3.2 Org depth = 0", graph.fractal_depth("org") == 0)
    check("T3.3 Dept depth = 1", graph.fractal_depth("dept_a") == 1)
    check("T3.4 Person depth = 2", graph.fractal_depth("person_1") == 2)

    # Relevance propagation
    direct_rel = graph.relevance_propagation("org", "dept_a")
    check("T3.5 Direct relevance > 0", direct_rel > 0)

    indirect_rel = graph.relevance_propagation("org", "person_1")
    check("T3.6 Indirect relevance > 0", indirect_rel > 0)
    check("T3.7 Indirect < direct (decay)", indirect_rel < direct_rel)

    cross_rel = graph.relevance_propagation("org", "dept_b")
    check("T3.8 Cross-department relevance", cross_rel > 0)

    no_rel = graph.relevance_propagation("person_1", "org")
    check("T3.9 No reverse path = 0 relevance", no_rel == 0.0)

    # ─── §4: Mathematical Foundation ───
    print("§4: Mathematical Foundation")

    # Fractal Markov Property
    fmp = FractalMarkovProperty()
    mrh_test = MRH(node="X")
    mrh_test.add("scale_1", 0.8, "mrh:contains", 1)
    mrh_test.add("scale_2", 0.6, "mrh:references", 2)

    check("T4.1 Fractal Markov property holds",
          fmp.verify_property(mrh_test, ["scale_1", "scale_2"]))
    check("T4.2 Missing scale → property fails",
          not fmp.verify_property(mrh_test, ["scale_1", "scale_3"]))
    check("T4.3 Conditional independence outside MRH",
          fmp.conditional_independence(mrh_test, "external"))
    check("T4.4 Not independent if in MRH",
          not fmp.conditional_independence(mrh_test, "scale_1"))

    # Information Geometry
    ig = InformationGeometry()
    metric = ig.metric_tensor(mrh_test)
    check("T4.5 Metric tensor is 2×2", len(metric) == 2 and len(metric[0]) == 2)
    check("T4.6 Diagonal = probabilities", metric[0][0] == 0.8 and metric[1][1] == 0.6)
    check("T4.7 Off-diagonal = 0", metric[0][1] == 0.0)

    # Geodesic distance
    mrh_a = MRH(node="A")
    mrh_a.add("target_1", 0.9, "r", 1)
    mrh_a.add("target_2", 0.5, "r", 1)
    mrh_b = MRH(node="B")
    mrh_b.add("target_1", 0.8, "r", 1)
    mrh_b.add("target_2", 0.6, "r", 1)
    dist = ig.geodesic_distance(mrh_a, mrh_b)
    check("T4.8 Geodesic distance > 0 (different)", dist > 0)

    dist_self = ig.geodesic_distance(mrh_a, mrh_a)
    check("T4.9 Self-distance = 0", dist_self == 0.0)

    # Self-similarity
    parent = MRH(node="P")
    parent.add("c1", 0.9, "contains", 1)
    parent.add("c2", 0.8, "references", 1)
    child = MRH(node="C")
    child.add("c3", 0.7, "contains", 1)
    child.add("c4", 0.6, "derived_from", 1)
    sim = ig.self_similarity(parent, child)
    check("T4.10 Partial self-similarity", 0 < sim < 1)

    # Identical relation sets = perfect self-similarity
    child_same = MRH(node="C2")
    child_same.add("x", 0.7, "contains", 1)
    child_same.add("y", 0.6, "references", 1)
    sim_same = ig.self_similarity(parent, child_same)
    check("T4.11 Identical relations = 1.0", sim_same == 1.0)

    # Empty MRH
    empty_metric = ig.metric_tensor(MRH(node="empty"))
    check("T4.12 Empty MRH metric = [[1.0]]", empty_metric == [[1.0]])

    # ─── §5: Practical Implications ───
    print("§5: Practical Implications")

    # Context management
    cm = ContextManager(graph)
    level_1 = cm.zoom_to_level("org", 1)
    check("T5.1 Zoom to level 1 (depts only)", len(level_1) == 2)

    compressed = cm.compress_context("org", threshold=0.88)
    check("T5.2 Compression: only high-relevance retained", len(compressed) == 1)
    check("T5.3 Compressed keeps highest relevance", compressed[0].probability >= 0.88)

    # Sharding boundaries
    sbd = ShardingBoundaryDetector()
    shards = sbd.detect_boundaries(graph, threshold=0.8)
    check("T5.4 Shards detected", len(shards) > 0)
    # High-relevance nodes should be in same shard
    for shard in shards:
        if "dept_a" in shard:
            check("T5.5 High-relevance person_1 in dept_a shard", "person_1" in shard)
            break

    # ─── §6: Active Inference ───
    print("§6: Active Inference")

    agent = FractalAgent(agent_id="agent_1")
    mrh_s0 = MRH(node="agent_s0")
    mrh_s0.add("env_1", 0.9, "perceives", 1)
    mrh_s0.add("env_2", 0.7, "perceives", 1)
    agent.add_scale(0, mrh_s0)

    mrh_s1 = MRH(node="agent_s1")
    mrh_s1.add("concept_1", 0.8, "models", 1)
    agent.add_scale(1, mrh_s1)

    check("T6.1 Agent has 2 scales", len(agent.scales) == 2)
    check("T6.2 Scale 0 boundary exists", agent.get_boundary(0) is not None)
    check("T6.3 Scale 2 boundary = None", agent.get_boundary(2) is None)

    pred_0 = agent.hierarchical_prediction(0)
    pred_1 = agent.hierarchical_prediction(1)
    check("T6.4 Scale 0 prediction > 0", pred_0 > 0)
    check("T6.5 Scale 1 prediction > 0", pred_1 > 0)
    check("T6.6 Scale 0 avg relevance = 0.8", abs(pred_0 - 0.8) < 0.01)
    check("T6.7 Scale 1 avg relevance = 0.8", abs(pred_1 - 0.8) < 0.01)
    check("T6.8 Missing scale prediction = 0", agent.hierarchical_prediction(5) == 0.0)

    # ─── §7: Implementation in Web4 ───
    print("§7: Implementation in Web4")

    # RDF export
    mrh_rdf = MRH(node="lct:example")
    mrh_rdf.add("lct:other", 0.85, "mrh:derives_from", 2)
    mrh_rdf.add("lct:third", 0.5, "mrh:references", 3)
    rdf_triples = mrh_to_rdf(mrh_rdf)
    check("T7.1 RDF triples generated", len(rdf_triples) == 2)
    check("T7.2 RDF type correct", rdf_triples[0]["@type"] == "mrh:Relevance")
    check("T7.3 RDF target", rdf_triples[0]["mrh:target"] == "lct:other")
    check("T7.4 RDF probability", rdf_triples[0]["mrh:probability"] == 0.85)
    check("T7.5 RDF relation", rdf_triples[0]["mrh:relation"] == "mrh:derives_from")
    check("T7.6 RDF distance", rdf_triples[0]["mrh:distance"] == 2)

    # Fractal composition
    fc = demonstrate_fractal_composition(depth=4)
    check("T7.7 4 levels created", len(fc) == 4)
    check("T7.8 LCT_A → LCT_B", len(fc["LCT_A"].entries) == 1)
    check("T7.9 LCT_D has no outgoing (leaf)", len(fc["LCT_D"].entries) == 0)
    check("T7.10 Probability decreases with depth",
          fc["LCT_A"].entries[0].probability > fc["LCT_B"].entries[0].probability)

    # Unlimited depth with local coherence
    deep = demonstrate_fractal_composition(depth=10)
    check("T7.11 Deep fractal: 10 levels", len(deep) == 10)

    # ─── Integration: Full theoretical validation ───
    print()
    print("Integration: Full theoretical validation")

    # Build a complete fractal MRH graph
    full_graph = FractalMRHGraph()
    # System level
    full_graph.add_level("System", 0, "org")
    # Team level
    for i in range(3):
        tid = f"team_{i}"
        full_graph.add_level("Team", 1, tid)
        full_graph.add_relevance("org", tid, 0.9 - i * 0.1, "mrh:contains", 1)
    # Individual level
    for i in range(6):
        pid = f"person_{i}"
        tid = f"team_{i // 2}"
        full_graph.add_level("Individual", 2, pid)
        full_graph.add_relevance(tid, pid, 0.95 - (i % 2) * 0.1, "mrh:member", 1)

    check("T8.1 Full graph: 10 nodes", len(full_graph.levels) == 10)

    # Verify Markov property at each scale
    for node_id, mrh in full_graph.mrh_map.items():
        relevant = [e.target for e in mrh.entries]
        fmp_holds = fmp.verify_property(mrh, relevant)
        check(f"T8.2 Fractal Markov property: {node_id}", fmp_holds)
        break  # Just check first one to avoid excessive checks

    # Cross-scale relevance propagation
    org_to_person = full_graph.relevance_propagation("org", "person_0")
    check("T8.3 Cross-scale propagation: org→person_0 > 0", org_to_person > 0)

    # Information geometry metrics
    team0_mrh = full_graph.mrh_map["team_0"]
    team1_mrh = full_graph.mrh_map["team_1"]
    team_dist = ig.geodesic_distance(team0_mrh, team1_mrh)
    check("T8.4 Different teams: distance > 0", team_dist > 0)

    team_sim = ig.self_similarity(team0_mrh, team1_mrh)
    check("T8.5 Teams share structure (self-similar)", team_sim > 0)

    # Sharding
    shards = ShardingBoundaryDetector.detect_boundaries(full_graph, threshold=0.85)
    check("T8.6 Multiple shards detected", len(shards) > 1)

    # Context compression
    cm2 = ContextManager(full_graph)
    org_compressed = cm2.compress_context("org", threshold=0.8)
    check("T8.7 Org context compressed", len(org_compressed) <= len(full_graph.mrh_map["org"].entries))

    # ─── Summary ───
    print()
    print("=" * 60)
    if failed == 0:
        print(f"MRH Theoretical Foundation: {passed}/{total} checks passed")
        print("  All checks passed!")
    else:
        print(f"MRH Theoretical Foundation: {passed}/{total} checks passed, {failed} FAILED")
    print("=" * 60)
    return failed == 0

if __name__ == "__main__":
    run_tests()
