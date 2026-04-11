#!/usr/bin/env python3
"""
Web4 MRH RDF Graph — Reference Implementation
Spec: web4-standard/MRH_RDF_SPECIFICATION.md (356 lines)

MRH (Markov Relevancy Horizon) as RDF graph, not flat list.
Extends Markov blankets with fractal scales, typed edges, probabilities.

Covers:
  §1  Theoretical foundation (relevance, fractal, probabilistic, semantic)
  §2  Motivation for RDF over flat lists
  §3  Core spec: structure, ontology (4 classes, 13 properties), fractal
      composition, traversal (DFS Markov walk + BFS relevance expansion)
  §4  Use cases: context preservation, trust propagation, semantic search
  §5  Implementation: storage, optimization, compatibility
  §6  Examples: chain of reasoning, alternative paths, conditional deps
  §7  Benefits: precision, flexibility, scalability, Markov properties
  §8  Migration path: dual support → adoption → deprecation

Run: python mrh_rdf_graph.py
"""

from __future__ import annotations
import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ============================================================
# §3.2 Core Ontology — Classes
# ============================================================

class MRHClass(Enum):
    """Four MRH RDF classes from spec §3.2."""
    RELEVANCE = "mrh:Relevance"      # A relevancy relationship to another LCT
    TRANSITION = "mrh:Transition"    # A Markovian state transition
    CLUSTER = "mrh:Cluster"          # A group of related LCTs
    PATH = "mrh:Path"                # A traversal path through the graph


# ============================================================
# §3.2 Core Ontology — Relationship Types
# ============================================================

class MRHRelation(Enum):
    """Seven relationship properties from spec §3.2."""
    DERIVES_FROM = "mrh:derives_from"          # This LCT derives from target
    SPECIALIZES = "mrh:specializes"            # This LCT specializes target
    CONTRADICTS = "mrh:contradicts"            # This LCT contradicts target
    EXTENDS = "mrh:extends"                    # This LCT extends target
    REFERENCES = "mrh:references"              # Generic reference
    DEPENDS_ON = "mrh:depends_on"              # Functional dependency
    ALTERNATIVES_TO = "mrh:alternatives_to"    # Mutually exclusive alternatives


# ============================================================
# §3.1 Structure — Relevance Node
# ============================================================

@dataclass
class RelevanceNode:
    """A single relevancy relationship in the MRH graph (§3.1)."""
    node_id: str                                   # blank node ID e.g. "_:relevance1"
    rdf_type: MRHClass = MRHClass.RELEVANCE
    target: str = ""                               # LCT URI e.g. "lct:hash1"
    probability: float = 1.0                       # Markovian transition [0,1]
    relation: MRHRelation = MRHRelation.REFERENCES
    distance: int = 1                              # Markov distance (hops)
    trust: float = 1.0                             # Trust weight [0,1]
    decay_rate: float = 0.1                        # Temporal decay rate
    conditional_on: Optional[str] = None           # Node ID of dependency
    joint_probability: Optional[float] = None      # Joint prob with deps
    timestamp: str = ""

    def effective_probability(self, decay_factor: float = 0.9) -> float:
        """Probability adjusted by distance decay: P * decay^distance."""
        return self.probability * (decay_factor ** self.distance)

    def to_jsonld(self) -> dict:
        """Serialize to JSON-LD format per spec §3.1."""
        node: dict[str, Any] = {
            "@id": self.node_id,
            "@type": self.rdf_type.value,
            "mrh:target": {"@id": self.target},
            "mrh:probability": {"@value": str(self.probability), "@type": "xsd:decimal"},
            "mrh:relation": self.relation.value,
            "mrh:distance": {"@value": str(self.distance), "@type": "xsd:integer"},
        }
        if self.trust < 1.0:
            node["mrh:trust"] = {"@value": str(self.trust), "@type": "xsd:decimal"}
        if self.conditional_on:
            node["mrh:conditional_on"] = {"@id": self.conditional_on}
        if self.joint_probability is not None:
            node["mrh:joint_probability"] = {"@value": str(self.joint_probability), "@type": "xsd:decimal"}
        if self.timestamp:
            node["mrh:timestamp"] = self.timestamp
        if self.decay_rate != 0.1:
            node["mrh:decay_rate"] = {"@value": str(self.decay_rate), "@type": "xsd:decimal"}
        return node

    @staticmethod
    def from_jsonld(data: dict) -> 'RelevanceNode':
        """Deserialize from JSON-LD."""
        def extract_value(v):
            if isinstance(v, dict) and "@value" in v:
                return v["@value"]
            return v

        cond = data.get("mrh:conditional_on")
        if isinstance(cond, dict):
            cond = cond.get("@id")

        jp = data.get("mrh:joint_probability")
        if jp is not None:
            jp = float(extract_value(jp))

        return RelevanceNode(
            node_id=data.get("@id", ""),
            target=data.get("mrh:target", {}).get("@id", ""),
            probability=float(extract_value(data.get("mrh:probability", 1.0))),
            relation=MRHRelation(data.get("mrh:relation", "mrh:references")),
            distance=int(extract_value(data.get("mrh:distance", 1))),
            trust=float(extract_value(data.get("mrh:trust", {"@value": "1.0"}))),
            conditional_on=cond,
            joint_probability=jp,
        )


# ============================================================
# §3.1 Structure — MRH Graph
# ============================================================

MRH_CONTEXT = {
    "@vocab": "https://web4.foundation/mrh/v1#",
    "mrh": "https://web4.foundation/mrh/v1#",
    "lct": "https://web4.foundation/lct/",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}


@dataclass
class MRHGraph:
    """Complete MRH field as RDF graph (§3.1 graph form)."""
    nodes: list[RelevanceNode] = field(default_factory=list)

    def add_node(self, node: RelevanceNode):
        self.nodes.append(node)

    def get_node(self, node_id: str) -> Optional[RelevanceNode]:
        for n in self.nodes:
            if n.node_id == node_id:
                return n
        return None

    def get_by_target(self, target_lct: str) -> list[RelevanceNode]:
        return [n for n in self.nodes if n.target == target_lct]

    def get_by_relation(self, relation: MRHRelation) -> list[RelevanceNode]:
        return [n for n in self.nodes if n.relation == relation]

    def get_alternatives(self) -> list[list[RelevanceNode]]:
        """Find groups of mutually exclusive alternatives."""
        alt_nodes = self.get_by_relation(MRHRelation.ALTERNATIVES_TO)
        if not alt_nodes:
            return []
        # Group by target relationship (alternatives reference each other)
        groups: list[list[RelevanceNode]] = []
        seen = set()
        for node in alt_nodes:
            if node.node_id in seen:
                continue
            group = [node]
            seen.add(node.node_id)
            # Find all nodes that are alternatives to this one
            for other in alt_nodes:
                if other.node_id != node.node_id and other.node_id not in seen:
                    group.append(other)
                    seen.add(other.node_id)
            if len(group) >= 2:
                groups.append(group)
        return groups

    def to_jsonld(self) -> dict:
        """Serialize to JSON-LD format."""
        return {
            "@context": MRH_CONTEXT,
            "@graph": [n.to_jsonld() for n in self.nodes],
        }

    @staticmethod
    def from_jsonld(data: dict) -> 'MRHGraph':
        """Deserialize from JSON-LD."""
        graph = MRHGraph()
        for node_data in data.get("@graph", []):
            graph.add_node(RelevanceNode.from_jsonld(node_data))
        return graph

    def to_simple_form(self) -> list[str]:
        """Downgrade to simple array form (§3.1 backward compat)."""
        return list(set(n.target for n in self.nodes))


# ============================================================
# §3.1 + §5.3 Dual Format Support
# ============================================================

@dataclass
class LCT:
    """Simplified LCT with MRH field supporting both formats."""
    lct_version: str = "1.0"
    entity_id: str = ""
    mrh: Any = None  # MRHGraph or list[str]

    @property
    def mrh_format(self) -> str:
        """'graph' or 'simple'."""
        if isinstance(self.mrh, MRHGraph):
            return "graph"
        elif isinstance(self.mrh, list):
            return "simple"
        return "none"

    def upgrade_mrh(self):
        """Migrate from simple array to graph form (§8 Phase 1)."""
        if isinstance(self.mrh, list):
            graph = MRHGraph()
            for i, lct_uri in enumerate(self.mrh):
                graph.add_node(RelevanceNode(
                    node_id=f"_:migrated_{i}",
                    target=lct_uri,
                    probability=1.0,
                    relation=MRHRelation.REFERENCES,
                    distance=1,
                ))
            self.mrh = graph

    def downgrade_mrh(self):
        """Downgrade graph to simple form (§5.3 fallback)."""
        if isinstance(self.mrh, MRHGraph):
            self.mrh = self.mrh.to_simple_form()


# ============================================================
# §3.3 Fractal Composition
# ============================================================

class FractalMRH:
    """Navigate fractal MRH structures (§3.3)."""

    def __init__(self):
        self.lcts: dict[str, LCT] = {}

    def register_lct(self, lct: LCT):
        self.lcts[lct.entity_id] = lct

    def get_fractal_depth(self, entity_id: str, visited: set = None) -> int:
        """How deep the fractal nesting goes."""
        if visited is None:
            visited = set()
        if entity_id in visited:
            return 0
        visited.add(entity_id)

        lct = self.lcts.get(entity_id)
        if not lct or not isinstance(lct.mrh, MRHGraph):
            return 0

        max_depth = 0
        for node in lct.mrh.nodes:
            child_depth = self.get_fractal_depth(node.target, visited)
            max_depth = max(max_depth, child_depth)
        return 1 + max_depth

    def collect_all_targets(self, entity_id: str, depth: int = 3,
                            visited: set = None) -> set[str]:
        """Recursively collect all reachable targets up to depth."""
        if visited is None:
            visited = set()
        if depth <= 0 or entity_id in visited:
            return set()
        visited.add(entity_id)

        targets = set()
        lct = self.lcts.get(entity_id)
        if not lct or not isinstance(lct.mrh, MRHGraph):
            return targets

        for node in lct.mrh.nodes:
            targets.add(node.target)
            targets |= self.collect_all_targets(node.target, depth - 1, visited)
        return targets


# ============================================================
# §3.4 Traversal — DFS Markovian Walk
# ============================================================

@dataclass
class TraversalResult:
    """Result of MRH graph traversal."""
    target: str
    total_probability: float
    path: list[str]
    distance: int
    relation: MRHRelation


def dfs_markovian_walk(graph: MRHGraph, max_distance: int = 3,
                       decay: float = 0.9, min_prob: float = 0.01
                       ) -> list[TraversalResult]:
    """Depth-first Markovian walk (spec §3.4).

    total_prob = prob * decay^distance, filtered by max_distance.
    """
    results = []
    for node in graph.nodes:
        if node.distance <= max_distance:
            total_prob = node.probability * (decay ** node.distance)
            if total_prob >= min_prob:
                results.append(TraversalResult(
                    target=node.target,
                    total_probability=total_prob,
                    path=[node.node_id],
                    distance=node.distance,
                    relation=node.relation,
                ))
    results.sort(key=lambda r: r.total_probability, reverse=True)
    return results


# ============================================================
# §3.4 Traversal — BFS Relevance Expansion
# ============================================================

def bfs_relevance_expansion(fractal: FractalMRH, start_id: str,
                            depth: int = 3, threshold: float = 0.01
                            ) -> list[TraversalResult]:
    """Breadth-first relevance expansion across fractal MRH (spec §3.4).

    Traverses nested MRH graphs, multiplying probabilities along paths.
    """
    results = []
    queue = [(start_id, 1.0, 0, [start_id])]
    visited = set()

    while queue:
        current_id, current_prob, dist, path = queue.pop(0)
        if dist >= depth or current_id in visited:
            continue
        visited.add(current_id)

        lct = fractal.lcts.get(current_id)
        if not lct or not isinstance(lct.mrh, MRHGraph):
            continue

        for node in lct.mrh.nodes:
            new_prob = current_prob * node.probability
            if new_prob >= threshold:
                new_path = path + [node.target]
                results.append(TraversalResult(
                    target=node.target,
                    total_probability=new_prob,
                    path=new_path,
                    distance=dist + 1,
                    relation=node.relation,
                ))
                queue.append((node.target, new_prob, dist + 1, new_path))

    results.sort(key=lambda r: r.total_probability, reverse=True)
    return results


# ============================================================
# §4.2 Trust Propagation
# ============================================================

def propagate_trust(graph: MRHGraph, source_trust: float,
                    decay_factor: float = 0.9) -> dict[str, float]:
    """Trust flows through MRH graph (spec §4.2).

    trust(B) = Σ(trust(A) × P(A→B) × decay(distance))
    """
    trust_map: dict[str, float] = defaultdict(float)
    for node in graph.nodes:
        propagated = source_trust * node.probability * (decay_factor ** node.distance)
        trust_map[node.target] += propagated
    return dict(trust_map)


# ============================================================
# §5.2 Optimization — Edge Pruning
# ============================================================

def prune_low_probability(graph: MRHGraph, threshold: float = 0.1) -> MRHGraph:
    """Remove edges below probability threshold (§5.2)."""
    pruned = MRHGraph()
    for node in graph.nodes:
        if node.probability >= threshold:
            pruned.add_node(node)
    return pruned


# ============================================================
# §6.3 Conditional Dependencies
# ============================================================

def compute_conditional_probability(graph: MRHGraph, node_id: str) -> float:
    """Compute effective probability considering conditional dependencies."""
    node = graph.get_node(node_id)
    if not node:
        return 0.0

    if node.joint_probability is not None:
        return node.joint_probability

    if node.conditional_on is None:
        return node.probability

    parent = graph.get_node(node.conditional_on)
    if not parent:
        return node.probability
    return node.probability * parent.probability


# ============================================================
# §8 Migration Path
# ============================================================

class MigrationPhase(Enum):
    DUAL_SUPPORT = 1    # Accept both array and graph
    ADOPTION = 2        # Encourage graph for new LCTs
    DEPRECATION = 3     # Mark array as legacy


# ════════════════════════════════════════════════════════════════
#  TESTS
# ════════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name}")

    # ── T1: Core Ontology Classes ────────────────────────────────
    print("T1: Core Ontology Classes (§3.2)")
    check("T1.1 Four MRH classes",
          len(MRHClass) == 4)
    check("T1.2 Relevance class",
          MRHClass.RELEVANCE.value == "mrh:Relevance")
    check("T1.3 Transition class",
          MRHClass.TRANSITION.value == "mrh:Transition")
    check("T1.4 Cluster class",
          MRHClass.CLUSTER.value == "mrh:Cluster")
    check("T1.5 Path class",
          MRHClass.PATH.value == "mrh:Path")

    # ── T2: Relationship Types ───────────────────────────────────
    print("T2: Relationship Types (§3.2)")
    check("T2.1 Seven relationship types",
          len(MRHRelation) == 7)
    check("T2.2 derives_from",
          MRHRelation.DERIVES_FROM.value == "mrh:derives_from")
    check("T2.3 specializes",
          MRHRelation.SPECIALIZES.value == "mrh:specializes")
    check("T2.4 contradicts",
          MRHRelation.CONTRADICTS.value == "mrh:contradicts")
    check("T2.5 extends",
          MRHRelation.EXTENDS.value == "mrh:extends")
    check("T2.6 references",
          MRHRelation.REFERENCES.value == "mrh:references")
    check("T2.7 depends_on",
          MRHRelation.DEPENDS_ON.value == "mrh:depends_on")
    check("T2.8 alternatives_to",
          MRHRelation.ALTERNATIVES_TO.value == "mrh:alternatives_to")

    # ── T3: RelevanceNode ────────────────────────────────────────
    print("T3: RelevanceNode (§3.1)")
    node = RelevanceNode(
        node_id="_:r1",
        target="lct:hash1",
        probability=0.95,
        relation=MRHRelation.DERIVES_FROM,
        distance=1,
        trust=0.9,
        decay_rate=0.15,
        timestamp="2025-01-01T00:00:00Z",
    )
    check("T3.1 Node created",
          node.node_id == "_:r1")
    check("T3.2 Target set",
          node.target == "lct:hash1")
    check("T3.3 Probability in [0,1]",
          0 <= node.probability <= 1)
    check("T3.4 Distance is integer",
          isinstance(node.distance, int))
    check("T3.5 Trust weight",
          node.trust == 0.9)

    # Effective probability
    eff_prob = node.effective_probability(decay_factor=0.9)
    expected = 0.95 * (0.9 ** 1)
    check("T3.6 Effective probability = P * decay^distance",
          abs(eff_prob - expected) < 0.0001)

    # Distance 3 decays more
    node3 = RelevanceNode(node_id="_:r3", target="lct:far", probability=0.8, distance=3)
    eff3 = node3.effective_probability(0.9)
    check("T3.7 Higher distance → lower effective prob",
          eff3 < node.effective_probability(0.9))

    # ── T4: JSON-LD Serialization ────────────────────────────────
    print("T4: JSON-LD Serialization (§3.1)")
    jsonld = node.to_jsonld()
    check("T4.1 Has @id",
          jsonld["@id"] == "_:r1")
    check("T4.2 Has @type",
          jsonld["@type"] == "mrh:Relevance")
    check("T4.3 Target as @id object",
          jsonld["mrh:target"]["@id"] == "lct:hash1")
    check("T4.4 Probability as xsd:decimal",
          jsonld["mrh:probability"]["@type"] == "xsd:decimal")
    check("T4.5 Distance as xsd:integer",
          jsonld["mrh:distance"]["@type"] == "xsd:integer")
    check("T4.6 Has relation",
          jsonld["mrh:relation"] == "mrh:derives_from")
    check("T4.7 Trust included when < 1.0",
          "mrh:trust" in jsonld)
    check("T4.8 Timestamp included",
          jsonld.get("mrh:timestamp") == "2025-01-01T00:00:00Z")

    # Round-trip
    restored = RelevanceNode.from_jsonld(jsonld)
    check("T4.9 Round-trip preserves target",
          restored.target == node.target)
    check("T4.10 Round-trip preserves probability",
          abs(restored.probability - node.probability) < 0.0001)
    check("T4.11 Round-trip preserves relation",
          restored.relation == node.relation)
    check("T4.12 Round-trip preserves distance",
          restored.distance == node.distance)

    # ── T5: Conditional Dependencies (§6.3) ──────────────────────
    print("T5: Conditional Dependencies (§6.3)")
    cond_node = RelevanceNode(
        node_id="_:cond1",
        target="lct:ext1",
        probability=0.8,
        conditional_on="_:base",
    )
    jsonld_cond = cond_node.to_jsonld()
    check("T5.1 Conditional_on serialized",
          jsonld_cond["mrh:conditional_on"]["@id"] == "_:base")

    cond_restored = RelevanceNode.from_jsonld(jsonld_cond)
    check("T5.2 Conditional_on round-trips",
          cond_restored.conditional_on == "_:base")

    # Joint probability
    joint_node = RelevanceNode(
        node_id="_:cond2",
        target="lct:ext2",
        probability=0.7,
        conditional_on="_:base",
        joint_probability=0.56,
    )
    jl = joint_node.to_jsonld()
    check("T5.3 Joint probability serialized",
          "mrh:joint_probability" in jl)
    jr = RelevanceNode.from_jsonld(jl)
    check("T5.4 Joint probability round-trips",
          abs(jr.joint_probability - 0.56) < 0.001)

    # ── T6: MRH Graph ───────────────────────────────────────────
    print("T6: MRH Graph (§3.1)")
    graph = MRHGraph()
    n1 = RelevanceNode("_:r1", target="lct:A", probability=0.9,
                        relation=MRHRelation.DERIVES_FROM, distance=1)
    n2 = RelevanceNode("_:r2", target="lct:B", probability=0.7,
                        relation=MRHRelation.REFERENCES, distance=2,
                        conditional_on="_:r1")
    n3 = RelevanceNode("_:r3", target="lct:C", probability=0.5,
                        relation=MRHRelation.EXTENDS, distance=1)
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_node(n3)

    check("T6.1 Graph has 3 nodes",
          len(graph.nodes) == 3)
    check("T6.2 Get node by ID",
          graph.get_node("_:r1") is n1)
    check("T6.3 Get node returns None for missing",
          graph.get_node("_:missing") is None)
    check("T6.4 Get by target",
          len(graph.get_by_target("lct:A")) == 1)
    check("T6.5 Get by relation",
          len(graph.get_by_relation(MRHRelation.DERIVES_FROM)) == 1)

    # ── T7: Graph JSON-LD Serialization ──────────────────────────
    print("T7: Graph JSON-LD Serialization")
    graph_jl = graph.to_jsonld()
    check("T7.1 Has @context",
          "@context" in graph_jl)
    check("T7.2 Context has vocab",
          graph_jl["@context"]["@vocab"] == "https://web4.foundation/mrh/v1#")
    check("T7.3 Has @graph array",
          isinstance(graph_jl["@graph"], list))
    check("T7.4 Graph array has 3 items",
          len(graph_jl["@graph"]) == 3)

    # Round-trip graph
    restored_graph = MRHGraph.from_jsonld(graph_jl)
    check("T7.5 Round-trip preserves node count",
          len(restored_graph.nodes) == 3)
    check("T7.6 Round-trip preserves first target",
          restored_graph.nodes[0].target == "lct:A")

    # Simple form downgrade
    simple = graph.to_simple_form()
    check("T7.7 Simple form is list",
          isinstance(simple, list))
    check("T7.8 Simple form has unique targets",
          len(simple) == 3)
    check("T7.9 Simple form contains lct:A",
          "lct:A" in simple)

    # ── T8: Alternatives Detection ───────────────────────────────
    print("T8: Alternative Paths (§6.2)")
    alt_graph = MRHGraph()
    alt_graph.add_node(RelevanceNode(
        "_:path1", target="lct:sol_a", probability=0.6,
        relation=MRHRelation.ALTERNATIVES_TO))
    alt_graph.add_node(RelevanceNode(
        "_:path2", target="lct:sol_b", probability=0.4,
        relation=MRHRelation.ALTERNATIVES_TO))
    alt_graph.add_node(RelevanceNode(
        "_:other", target="lct:base", probability=0.9,
        relation=MRHRelation.DERIVES_FROM))

    alts = alt_graph.get_alternatives()
    check("T8.1 One alternative group found",
          len(alts) == 1)
    check("T8.2 Group has 2 alternatives",
          len(alts[0]) == 2)
    check("T8.3 Alt probabilities sum ≈ 1.0",
          abs(sum(n.probability for n in alts[0]) - 1.0) < 0.001)

    # No alternatives in regular graph
    check("T8.4 No alternatives in non-alt graph",
          len(graph.get_alternatives()) == 0)

    # ── T9: LCT Dual Format Support (§3.1 + §5.3) ───────────────
    print("T9: LCT Dual Format Support (§5.3)")
    # Simple form LCT
    lct_simple = LCT(entity_id="e1", mrh=["lct:A", "lct:B", "lct:C"])
    check("T9.1 Simple format detected",
          lct_simple.mrh_format == "simple")

    # Graph form LCT
    lct_graph = LCT(entity_id="e2", mrh=graph)
    check("T9.2 Graph format detected",
          lct_graph.mrh_format == "graph")

    # No MRH
    lct_none = LCT(entity_id="e3")
    check("T9.3 No MRH format detected",
          lct_none.mrh_format == "none")

    # Upgrade simple → graph (§8 Phase 1)
    lct_simple.upgrade_mrh()
    check("T9.4 Upgrade to graph format",
          lct_simple.mrh_format == "graph")
    check("T9.5 Upgraded graph has 3 nodes",
          len(lct_simple.mrh.nodes) == 3)
    check("T9.6 Upgraded nodes are REFERENCES",
          all(n.relation == MRHRelation.REFERENCES for n in lct_simple.mrh.nodes))
    check("T9.7 Upgraded nodes have prob 1.0",
          all(n.probability == 1.0 for n in lct_simple.mrh.nodes))

    # Downgrade graph → simple (§5.3 fallback)
    lct_simple.downgrade_mrh()
    check("T9.8 Downgrade to simple format",
          lct_simple.mrh_format == "simple")
    check("T9.9 Downgraded has 3 targets",
          len(lct_simple.mrh) == 3)

    # ── T10: Fractal Composition (§3.3) ──────────────────────────
    print("T10: Fractal Composition (§3.3)")
    fractal = FractalMRH()

    # LCT_A → {LCT_B(0.9), LCT_E(0.7)}
    mrh_a = MRHGraph()
    mrh_a.add_node(RelevanceNode("_:a1", target="lct:B", probability=0.9, distance=1))
    mrh_a.add_node(RelevanceNode("_:a2", target="lct:E", probability=0.7, distance=1))
    fractal.register_lct(LCT(entity_id="lct:A", mrh=mrh_a))

    # LCT_B → {LCT_C(0.8), LCT_D(0.6)}
    mrh_b = MRHGraph()
    mrh_b.add_node(RelevanceNode("_:b1", target="lct:C", probability=0.8, distance=1))
    mrh_b.add_node(RelevanceNode("_:b2", target="lct:D", probability=0.6, distance=1))
    fractal.register_lct(LCT(entity_id="lct:B", mrh=mrh_b))

    # LCT_E → {LCT_C(0.5)}
    mrh_e = MRHGraph()
    mrh_e.add_node(RelevanceNode("_:e1", target="lct:C", probability=0.5, distance=1))
    fractal.register_lct(LCT(entity_id="lct:E", mrh=mrh_e))

    # Leaf nodes (no MRH)
    fractal.register_lct(LCT(entity_id="lct:C"))
    fractal.register_lct(LCT(entity_id="lct:D"))

    # Depth: A→B→{C,D}, A→E→C. B has graph (depth 1+max child), leaves=0
    # A: 1 + max(B_depth=1, E_depth=1) = 2
    # B: 1 + max(C=0, D=0) = 1
    # E: 1 + max(C=0) = 1
    depth_a = fractal.get_fractal_depth("lct:A")
    depth_b = fractal.get_fractal_depth("lct:B")
    depth_e = fractal.get_fractal_depth("lct:E")
    check("T10.1 Fractal depth from A = 2 (A→B→leaf)",
          depth_a == 2)
    check("T10.2 Fractal depth from B = 1 (B→leaf)",
          depth_b == 1)
    check("T10.3 Fractal depth from E = 1 (E→leaf)",
          depth_e == 1)
    check("T10.4 Fractal depth from unknown is 0",
          fractal.get_fractal_depth("lct:unknown") == 0)

    # Collect all targets
    all_targets = fractal.collect_all_targets("lct:A", depth=3)
    check("T10.5 All reachable targets found",
          all_targets == {"lct:B", "lct:C", "lct:D", "lct:E"})
    check("T10.6 Depth-limited collection",
          "lct:C" not in fractal.collect_all_targets("lct:A", depth=1))

    # Circular reference handling
    mrh_circular = MRHGraph()
    mrh_circular.add_node(RelevanceNode("_:c1", target="lct:A", probability=0.5, distance=1))
    fractal.register_lct(LCT(entity_id="lct:D", mrh=mrh_circular))
    check("T10.7 Circular reference doesn't infinite loop",
          fractal.get_fractal_depth("lct:A") >= 1)  # terminates

    # ── T11: DFS Markovian Walk (§3.4) ───────────────────────────
    print("T11: DFS Markovian Walk (§3.4)")
    walk_graph = MRHGraph()
    walk_graph.add_node(RelevanceNode("_:w1", target="lct:near", probability=0.9,
                                       distance=1, relation=MRHRelation.DERIVES_FROM))
    walk_graph.add_node(RelevanceNode("_:w2", target="lct:mid", probability=0.7,
                                       distance=2, relation=MRHRelation.REFERENCES))
    walk_graph.add_node(RelevanceNode("_:w3", target="lct:far", probability=0.5,
                                       distance=3, relation=MRHRelation.EXTENDS))
    walk_graph.add_node(RelevanceNode("_:w4", target="lct:beyond", probability=0.3,
                                       distance=4, relation=MRHRelation.REFERENCES))

    results = dfs_markovian_walk(walk_graph, max_distance=3, decay=0.9)
    check("T11.1 DFS returns within max_distance",
          len(results) == 3)
    check("T11.2 Results sorted by total_probability desc",
          results[0].total_probability >= results[1].total_probability)
    check("T11.3 Nearest has highest total_prob",
          results[0].target == "lct:near")
    check("T11.4 Total prob = P * decay^dist",
          abs(results[0].total_probability - 0.9 * 0.9) < 0.0001)
    check("T11.5 Distance 2: 0.7 * 0.81",
          abs(results[1].total_probability - 0.7 * 0.81) < 0.0001)
    check("T11.6 Distance 3: 0.5 * 0.729",
          abs(results[2].total_probability - 0.5 * 0.729) < 0.0001)

    # Min probability threshold
    high_thresh = dfs_markovian_walk(walk_graph, max_distance=3, decay=0.9, min_prob=0.5)
    check("T11.7 Min prob filters low-prob results",
          len(high_thresh) == 2)

    # ── T12: BFS Relevance Expansion (§3.4) ──────────────────────
    print("T12: BFS Relevance Expansion (§3.4)")
    bfs_results = bfs_relevance_expansion(fractal, "lct:A", depth=3, threshold=0.01)
    check("T12.1 BFS returns results",
          len(bfs_results) > 0)
    check("T12.2 Sorted by probability desc",
          all(bfs_results[i].total_probability >= bfs_results[i+1].total_probability
              for i in range(len(bfs_results) - 1)))

    # Direct neighbors (depth 1)
    direct = [r for r in bfs_results if r.distance == 1]
    check("T12.3 A has 2 direct neighbors",
          len(direct) == 2)

    # lct:B via A→B: probability 0.9
    b_result = next((r for r in bfs_results if r.target == "lct:B"), None)
    check("T12.4 lct:B reachable",
          b_result is not None)
    check("T12.5 lct:B prob = 0.9",
          b_result and abs(b_result.total_probability - 0.9) < 0.001)

    # lct:C via A→B→C: probability 0.9*0.8 = 0.72
    c_via_b = [r for r in bfs_results if r.target == "lct:C"]
    check("T12.6 lct:C reachable via multiple paths",
          len(c_via_b) >= 1)
    check("T12.7 lct:C via B has prob 0.72",
          any(abs(r.total_probability - 0.72) < 0.001 for r in c_via_b))

    # High threshold filters
    high_bfs = bfs_relevance_expansion(fractal, "lct:A", depth=3, threshold=0.5)
    check("T12.8 High threshold reduces results",
          len(high_bfs) < len(bfs_results))

    # ── T13: Trust Propagation (§4.2) ────────────────────────────
    print("T13: Trust Propagation (§4.2)")
    trust_graph = MRHGraph()
    trust_graph.add_node(RelevanceNode("_:t1", target="lct:X", probability=0.9, distance=1))
    trust_graph.add_node(RelevanceNode("_:t2", target="lct:Y", probability=0.7, distance=2))
    trust_graph.add_node(RelevanceNode("_:t3", target="lct:X", probability=0.3, distance=2))

    trust_map = propagate_trust(trust_graph, source_trust=1.0, decay_factor=0.9)
    check("T13.1 Trust propagated to targets",
          len(trust_map) == 2)
    check("T13.2 Multiple paths to X aggregate",
          trust_map["lct:X"] > 0.9 * 0.9)  # Sum of two paths
    expected_x = 1.0 * 0.9 * 0.9 + 1.0 * 0.3 * 0.81
    check("T13.3 Trust X = sum of paths",
          abs(trust_map["lct:X"] - expected_x) < 0.001)
    expected_y = 1.0 * 0.7 * 0.81
    check("T13.4 Trust Y = single path",
          abs(trust_map["lct:Y"] - expected_y) < 0.001)

    # Zero source trust
    zero_trust = propagate_trust(trust_graph, source_trust=0.0)
    check("T13.5 Zero source → zero propagation",
          all(v == 0.0 for v in zero_trust.values()))

    # ── T14: Edge Pruning (§5.2) ─────────────────────────────────
    print("T14: Edge Pruning (§5.2)")
    prune_graph = MRHGraph()
    prune_graph.add_node(RelevanceNode("_:p1", target="lct:high", probability=0.9))
    prune_graph.add_node(RelevanceNode("_:p2", target="lct:mid", probability=0.5))
    prune_graph.add_node(RelevanceNode("_:p3", target="lct:low", probability=0.05))

    pruned = prune_low_probability(prune_graph, threshold=0.1)
    check("T14.1 Low-prob edge pruned",
          len(pruned.nodes) == 2)
    check("T14.2 High-prob edge kept",
          any(n.target == "lct:high" for n in pruned.nodes))
    check("T14.3 Mid-prob edge kept",
          any(n.target == "lct:mid" for n in pruned.nodes))

    # Aggressive pruning
    aggressive = prune_low_probability(prune_graph, threshold=0.6)
    check("T14.4 Aggressive prune keeps only high",
          len(aggressive.nodes) == 1)

    # ── T15: Conditional Probability (§6.3) ──────────────────────
    print("T15: Conditional Probability (§6.3)")
    cond_graph = MRHGraph()
    base = RelevanceNode("_:base", target="lct:foundation", probability=1.0)
    ext1 = RelevanceNode("_:cond1", target="lct:ext1", probability=0.8,
                          conditional_on="_:base")
    ext2 = RelevanceNode("_:cond2", target="lct:ext2", probability=0.7,
                          conditional_on="_:base", joint_probability=0.56)
    cond_graph.add_node(base)
    cond_graph.add_node(ext1)
    cond_graph.add_node(ext2)

    check("T15.1 Unconditional base prob = 1.0",
          abs(compute_conditional_probability(cond_graph, "_:base") - 1.0) < 0.001)
    check("T15.2 Conditional ext1 = 0.8 * 1.0",
          abs(compute_conditional_probability(cond_graph, "_:cond1") - 0.8) < 0.001)
    check("T15.3 Joint probability override (0.56)",
          abs(compute_conditional_probability(cond_graph, "_:cond2") - 0.56) < 0.001)
    check("T15.4 Missing node returns 0",
          compute_conditional_probability(cond_graph, "_:missing") == 0.0)

    # ── T16: Migration Path (§8) ─────────────────────────────────
    print("T16: Migration Path (§8)")
    check("T16.1 Three migration phases",
          len(MigrationPhase) == 3)
    check("T16.2 Phase 1: dual support",
          MigrationPhase.DUAL_SUPPORT.value == 1)
    check("T16.3 Phase 2: adoption",
          MigrationPhase.ADOPTION.value == 2)
    check("T16.4 Phase 3: deprecation",
          MigrationPhase.DEPRECATION.value == 3)

    # Migration workflow: simple → upgrade → use → (optional downgrade)
    migrating = LCT(entity_id="migrating", mrh=["lct:old1", "lct:old2"])
    check("T16.5 Starts as simple",
          migrating.mrh_format == "simple")
    migrating.upgrade_mrh()
    check("T16.6 After upgrade is graph",
          migrating.mrh_format == "graph")
    # Add richer data
    migrating.mrh.add_node(RelevanceNode(
        "_:new", target="lct:new1", probability=0.85,
        relation=MRHRelation.SPECIALIZES, distance=1))
    check("T16.7 Can add rich nodes after upgrade",
          len(migrating.mrh.nodes) == 3)
    migrating.downgrade_mrh()
    check("T16.8 Can downgrade back (lossy)",
          migrating.mrh_format == "simple")
    check("T16.9 Downgrade preserves targets",
          "lct:new1" in migrating.mrh)

    # ── T17: Example — Chain of Reasoning (§6.1) ────────────────
    print("T17: Chain of Reasoning Example (§6.1)")
    chain = MRHGraph()
    chain.add_node(RelevanceNode("_:p1", target="lct:premise1", probability=0.9,
                                  relation=MRHRelation.DERIVES_FROM))
    chain.add_node(RelevanceNode("_:p2", target="lct:premise2", probability=0.85,
                                  relation=MRHRelation.DERIVES_FROM))
    chain.add_node(RelevanceNode("_:c", target="lct:conclusion", probability=0.76,
                                  relation=MRHRelation.REFERENCES))  # produces → references

    jsonld_chain = chain.to_jsonld()
    check("T17.1 Chain serializes to JSON-LD",
          len(jsonld_chain["@graph"]) == 3)
    check("T17.2 All derive from premises",
          len(chain.get_by_relation(MRHRelation.DERIVES_FROM)) == 2)
    check("T17.3 Conclusion probability < premises",
          chain.nodes[2].probability < chain.nodes[0].probability)

    # ── T18: Example — Alternative Paths (§6.2) ─────────────────
    print("T18: Alternative Paths Example (§6.2)")
    alt_ex = MRHGraph()
    alt_ex.add_node(RelevanceNode("_:sol_a", target="lct:solution_a", probability=0.6,
                                    relation=MRHRelation.ALTERNATIVES_TO))
    alt_ex.add_node(RelevanceNode("_:sol_b", target="lct:solution_b", probability=0.4,
                                    relation=MRHRelation.ALTERNATIVES_TO))

    alts_ex = alt_ex.get_alternatives()
    check("T18.1 Alternatives detected",
          len(alts_ex) == 1)
    check("T18.2 Probabilities sum to 1.0",
          abs(sum(n.probability for n in alts_ex[0]) - 1.0) < 0.001)
    check("T18.3 Higher-prob alternative is solution_a",
          alts_ex[0][0].probability > alts_ex[0][1].probability)

    # ── T19: Example — Conditional Deps (§6.3) ──────────────────
    print("T19: Conditional Dependencies Example (§6.3)")
    cond_ex = MRHGraph()
    cond_ex.add_node(RelevanceNode("_:base", target="lct:foundation", probability=1.0))
    cond_ex.add_node(RelevanceNode("_:ext1", target="lct:extension1", probability=0.8,
                                    conditional_on="_:base"))
    cond_ex.add_node(RelevanceNode("_:ext2", target="lct:extension2", probability=0.7,
                                    conditional_on="_:base", joint_probability=0.56))

    check("T19.1 Base is unconditional",
          cond_ex.nodes[0].conditional_on is None)
    check("T19.2 ext1 depends on base",
          cond_ex.nodes[1].conditional_on == "_:base")
    check("T19.3 ext2 has joint probability",
          cond_ex.nodes[2].joint_probability == 0.56)
    check("T19.4 Joint prob = product of chain (0.8 × 0.7 = 0.56)",
          abs(cond_ex.nodes[2].joint_probability - 0.8 * 0.7) < 0.001)

    # ── T20: End-to-End Pipeline ─────────────────────────────────
    print("T20: End-to-End Pipeline")
    # Build a fractal MRH with reasoning chain
    e2e_fractal = FractalMRH()

    # Root context with two branches
    root_mrh = MRHGraph()
    root_mrh.add_node(RelevanceNode("_:r1", target="lct:research",
                                     probability=0.9, relation=MRHRelation.DERIVES_FROM))
    root_mrh.add_node(RelevanceNode("_:r2", target="lct:experiment",
                                     probability=0.8, relation=MRHRelation.EXTENDS))
    e2e_fractal.register_lct(LCT(entity_id="lct:root", mrh=root_mrh))

    # Research branch
    research_mrh = MRHGraph()
    research_mrh.add_node(RelevanceNode("_:d1", target="lct:paper_a",
                                         probability=0.95, relation=MRHRelation.REFERENCES))
    research_mrh.add_node(RelevanceNode("_:d2", target="lct:paper_b",
                                         probability=0.7, relation=MRHRelation.CONTRADICTS))
    e2e_fractal.register_lct(LCT(entity_id="lct:research", mrh=research_mrh))

    # Experiment branch
    exp_mrh = MRHGraph()
    exp_mrh.add_node(RelevanceNode("_:e1", target="lct:paper_a",
                                    probability=0.6, relation=MRHRelation.DEPENDS_ON))
    e2e_fractal.register_lct(LCT(entity_id="lct:experiment", mrh=exp_mrh))

    # Leaves
    e2e_fractal.register_lct(LCT(entity_id="lct:paper_a"))
    e2e_fractal.register_lct(LCT(entity_id="lct:paper_b"))

    # BFS from root
    e2e_results = bfs_relevance_expansion(e2e_fractal, "lct:root", depth=3, threshold=0.01)
    check("T20.1 BFS finds all reachable",
          len(set(r.target for r in e2e_results)) >= 4)

    # paper_a reachable via two paths
    paper_a_results = [r for r in e2e_results if r.target == "lct:paper_a"]
    check("T20.2 paper_a via multiple paths",
          len(paper_a_results) >= 2)

    # Trust propagation
    trust_root = propagate_trust(root_mrh, source_trust=0.85)
    check("T20.3 Trust propagated from root",
          "lct:research" in trust_root)

    # Serialize entire graph
    root_jl = root_mrh.to_jsonld()
    check("T20.4 Root serializable",
          len(root_jl["@graph"]) == 2)

    # Prune low-probability
    pruned = prune_low_probability(research_mrh, threshold=0.8)
    check("T20.5 Pruning removes low-prob paper_b",
          len(pruned.nodes) == 1 and pruned.nodes[0].target == "lct:paper_a")

    # Fractal depth
    # root→research→paper (2 levels), root→experiment→paper (2 levels)
    check("T20.6 Fractal depth from root = 2",
          e2e_fractal.get_fractal_depth("lct:root") == 2)

    # DFS on research branch
    dfs_research = dfs_markovian_walk(research_mrh, max_distance=3, decay=0.9)
    check("T20.7 DFS on research returns 2 results",
          len(dfs_research) == 2)
    check("T20.8 paper_a ranked first (higher total prob)",
          dfs_research[0].target == "lct:paper_a")

    # ── T21: Edge Cases ──────────────────────────────────────────
    print("T21: Edge Cases")
    empty_graph = MRHGraph()
    check("T21.1 Empty graph traversal returns empty",
          len(dfs_markovian_walk(empty_graph)) == 0)
    check("T21.2 Empty graph to_jsonld works",
          len(empty_graph.to_jsonld()["@graph"]) == 0)
    check("T21.3 Empty graph simple form is empty list",
          empty_graph.to_simple_form() == [])

    # Zero probability node
    zero_graph = MRHGraph()
    zero_graph.add_node(RelevanceNode("_:z", target="lct:zero", probability=0.0))
    zero_trust = propagate_trust(zero_graph, source_trust=1.0)
    check("T21.4 Zero-prob node propagates zero trust",
          zero_trust.get("lct:zero", 0) == 0.0)

    # Max distance
    max_dist_results = dfs_markovian_walk(walk_graph, max_distance=0)
    check("T21.5 Max distance 0 returns nothing",
          len(max_dist_results) == 0)

    # Single node graph
    single = MRHGraph()
    single.add_node(RelevanceNode("_:s", target="lct:only", probability=1.0, distance=1))
    single_results = dfs_markovian_walk(single)
    check("T21.6 Single node graph returns 1 result",
          len(single_results) == 1)

    # ═══════════════════════════════════════════════════════════
    print(f"\n{'='*60}")
    print(f"MRH RDF Graph: {passed}/{passed+failed} checks passed")
    if failed:
        print(f"  ({failed} FAILED)")
    else:
        print("  All checks passed!")
    print(f"{'='*60}")
    return passed, failed


if __name__ == "__main__":
    run_tests()
