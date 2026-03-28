"""
Web4 Markov Relevancy Horizon (MRH)

Canonical implementation per web4-standard/core-spec/mrh-tensors.md.

The MRH defines the dynamic context of relationships surrounding each entity.
It extends the information-theoretic concept of Markov blankets to explicitly
encompass fractal scales — an entity's relevance and trustworthiness emerge
from WHO it interacts with, not from abstract metrics.

Key concept: beyond a certain graph traversal depth (the "horizon"),
relationships become irrelevant. Default horizon_depth = 3.

Relationship types (from ontology):
- Binding: permanent presence attachment (parent/child/sibling)
- Pairing: authorized operational relationships (energy/data/service)
- Witnessing: trust-building through observation (time/audit/oracle)

Validated against: web4-standard/test-vectors/mrh/graph-operations.json
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from .trust import mrh_trust_decay, mrh_zone

__all__ = [
    # Classes
    "MRHGraph", "MRHNode", "MRHEdge", "RelationType",
    # Functions
    "relation_category",
    "mrh_trust_decay", "mrh_zone",
    "propagate_multiplicative", "propagate_probabilistic", "propagate_maximal",
]


# ── Relationship Types ──────────────────────────────────────────

class RelationType(str, Enum):
    """Semantic relationship types from the MRH ontology."""

    # Binding relationships (permanent)
    BOUND_TO = "boundTo"
    PARENT_BINDING = "parentBinding"
    CHILD_BINDING = "childBinding"
    SIBLING_BINDING = "siblingBinding"

    # Pairing relationships (session-based)
    PAIRED_WITH = "pairedWith"
    ENERGY_PAIRING = "energyPairing"
    DATA_PAIRING = "dataPairing"
    SERVICE_PAIRING = "servicePairing"

    # Witness relationships (trust-building)
    WITNESSED_BY = "witnessedBy"
    TIME_WITNESS = "timeWitness"
    AUDIT_WITNESS = "auditWitness"
    ORACLE_WITNESS = "oracleWitness"


# Classify relation types into categories
_BINDING_TYPES = {
    RelationType.BOUND_TO, RelationType.PARENT_BINDING,
    RelationType.CHILD_BINDING, RelationType.SIBLING_BINDING,
}
_PAIRING_TYPES = {
    RelationType.PAIRED_WITH, RelationType.ENERGY_PAIRING,
    RelationType.DATA_PAIRING, RelationType.SERVICE_PAIRING,
}
_WITNESS_TYPES = {
    RelationType.WITNESSED_BY, RelationType.TIME_WITNESS,
    RelationType.AUDIT_WITNESS, RelationType.ORACLE_WITNESS,
}


def relation_category(rel: RelationType) -> str:
    """Return 'binding', 'pairing', or 'witness' for a relation type."""
    if rel in _BINDING_TYPES:
        return "binding"
    elif rel in _PAIRING_TYPES:
        return "pairing"
    elif rel in _WITNESS_TYPES:
        return "witness"
    return "unknown"


# ── Graph Components ────────────────────────────────────────────

@dataclass
class MRHNode:
    """A node in the MRH graph — represents an entity with context."""

    lct_id: str
    entity_type: str = "unknown"
    trust_scores: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Serialize node to dict with camelCase keys for JSON-LD compatibility."""
        return {
            "lctId": self.lct_id,
            "entityType": self.entity_type,
            "trustScores": self.trust_scores,
            "metadata": self.metadata,
        }


@dataclass
class MRHEdge:
    """A directed edge in the MRH graph — a typed relationship."""

    source: str          # Source LCT ID
    target: str          # Target LCT ID
    relation: RelationType
    weight: float = 1.0  # Edge weight (trust probability)
    timestamp: Optional[str] = None  # ISO 8601
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.weight = max(0.0, min(1.0, self.weight))
        if isinstance(self.relation, str):
            self.relation = RelationType(self.relation)

    @property
    def category(self) -> str:
        """Relationship category: 'binding', 'pairing', or 'witness'."""
        return relation_category(self.relation)

    def as_dict(self) -> Dict[str, Any]:
        """Serialize edge to dict with source, target, relation type, weight, and category."""
        d: Dict[str, Any] = {
            "source": self.source,
            "target": self.target,
            "relation": self.relation.value,
            "weight": self.weight,
            "category": self.category,
        }
        if self.timestamp:
            d["timestamp"] = self.timestamp
        if self.metadata:
            d["metadata"] = self.metadata
        return d


# ── Trust Propagation Strategies ────────────────────────────────

def propagate_multiplicative(
    path_weights: List[float],
    decay_factor: float = 0.7,
) -> float:
    """
    Trust decays multiplicatively along a path.

    Each hop multiplies accumulated trust by edge weight and decay factor.
    Per spec: trust *= edge.weight * (decay_factor ** distance)
    """
    trust = 1.0
    for i, w in enumerate(path_weights):
        trust *= w * (decay_factor ** (i + 1))
    return trust


def propagate_probabilistic(path_trusts: List[float]) -> float:
    """
    Combine multiple path trusts probabilistically.

    P(at least one path) = 1 - product(1 - p_i)
    """
    if not path_trusts:
        return 0.0
    combined = 1.0
    for pt in path_trusts:
        combined *= (1.0 - pt)
    return 1.0 - combined


def propagate_maximal(path_trusts: List[float]) -> float:
    """Take the highest trust path."""
    if not path_trusts:
        return 0.0
    return max(path_trusts)


# ── MRH Graph ──────────────────────────────────────────────────

class MRHGraph:
    """
    Markov Relevancy Horizon graph.

    A directed graph of entities (nodes) connected by typed relationships
    (edges). Supports horizon-bounded traversal, trust propagation, and
    context extraction.

    Usage:
        g = MRHGraph()
        g.add_node(MRHNode("lct:alice", "human"))
        g.add_node(MRHNode("lct:bob", "human"))
        g.add_edge(MRHEdge("lct:alice", "lct:bob", RelationType.PAIRED_WITH, 0.9))

        # Entities within Alice's horizon
        context = g.horizon("lct:alice", depth=3)

        # Trust from Alice to Bob
        trust = g.trust_between("lct:alice", "lct:bob")
    """

    def __init__(self, horizon_depth: int = 3):
        self.horizon_depth = horizon_depth
        self._nodes: Dict[str, MRHNode] = {}
        self._edges: List[MRHEdge] = []
        # Adjacency: source -> [(target, edge_index)]
        self._adj: Dict[str, List[Tuple[str, int]]] = {}
        # Reverse adjacency: target -> [(source, edge_index)]
        self._rev: Dict[str, List[Tuple[str, int]]] = {}

    # ── Node/Edge management ────────────────────────────────────

    def add_node(self, node: MRHNode) -> None:
        """Add or update a node."""
        self._nodes[node.lct_id] = node
        if node.lct_id not in self._adj:
            self._adj[node.lct_id] = []
        if node.lct_id not in self._rev:
            self._rev[node.lct_id] = []

    def add_edge(self, edge: MRHEdge) -> None:
        """Add an edge. Auto-creates nodes if they don't exist."""
        if edge.source not in self._nodes:
            self.add_node(MRHNode(edge.source))
        if edge.target not in self._nodes:
            self.add_node(MRHNode(edge.target))

        idx = len(self._edges)
        self._edges.append(edge)
        self._adj[edge.source].append((edge.target, idx))
        self._rev[edge.target].append((edge.source, idx))

    def get_node(self, lct_id: str) -> Optional[MRHNode]:
        """Look up a node by LCT ID, or None if not in the graph."""
        return self._nodes.get(lct_id)

    def get_edges(
        self,
        source: Optional[str] = None,
        target: Optional[str] = None,
        relation: Optional[RelationType] = None,
    ) -> List[MRHEdge]:
        """Query edges by source, target, and/or relation type."""
        results = []
        if source is not None:
            candidates = [self._edges[i] for _, i in self._adj.get(source, [])]
        elif target is not None:
            candidates = [self._edges[i] for _, i in self._rev.get(target, [])]
        else:
            candidates = self._edges

        for e in candidates:
            if target is not None and e.target != target:
                continue
            if source is not None and e.source != source:
                continue
            if relation is not None and e.relation != relation:
                continue
            results.append(e)
        return results

    @property
    def node_count(self) -> int:
        """Total number of nodes in the graph."""
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        """Total number of edges in the graph."""
        return len(self._edges)

    @property
    def nodes(self) -> List[MRHNode]:
        """List of all nodes in the graph."""
        return list(self._nodes.values())

    # ── Horizon Traversal ───────────────────────────────────────

    def horizon(
        self,
        origin: str,
        depth: Optional[int] = None,
        relation_filter: Optional[Set[RelationType]] = None,
    ) -> Dict[str, int]:
        """
        BFS from origin up to horizon depth.

        Returns dict of {lct_id: hop_distance} for all reachable entities.
        The origin itself has distance 0.

        Args:
            origin: Starting entity LCT ID
            depth: Max traversal depth (defaults to self.horizon_depth)
            relation_filter: If set, only follow edges of these types
        """
        max_depth = depth if depth is not None else self.horizon_depth
        if origin not in self._nodes:
            return {}

        visited: Dict[str, int] = {origin: 0}
        frontier = [origin]

        for d in range(1, max_depth + 1):
            next_frontier = []
            for node_id in frontier:
                for neighbor, edge_idx in self._adj.get(node_id, []):
                    if neighbor in visited:
                        continue
                    edge = self._edges[edge_idx]
                    if relation_filter and edge.relation not in relation_filter:
                        continue
                    visited[neighbor] = d
                    next_frontier.append(neighbor)
                # Also follow reverse edges (MRH is about context, not direction)
                for neighbor, edge_idx in self._rev.get(node_id, []):
                    if neighbor in visited:
                        continue
                    edge = self._edges[edge_idx]
                    if relation_filter and edge.relation not in relation_filter:
                        continue
                    visited[neighbor] = d
                    next_frontier.append(neighbor)
            frontier = next_frontier

        return visited

    def horizon_zones(self, origin: str, depth: Optional[int] = None) -> Dict[str, List[str]]:
        """
        Classify entities within horizon by MRH zone.

        Returns dict with keys: SELF, DIRECT, INDIRECT, PERIPHERAL.
        """
        h = self.horizon(origin, depth)
        zones: Dict[str, List[str]] = {
            "SELF": [], "DIRECT": [], "INDIRECT": [], "PERIPHERAL": [],
        }
        for lct_id, hops in h.items():
            zone = mrh_zone(hops)
            if zone in zones:
                zones[zone].append(lct_id)
        return zones

    # ── Trust Propagation ───────────────────────────────────────

    def find_paths(
        self,
        source: str,
        target: str,
        max_depth: Optional[int] = None,
    ) -> List[List[MRHEdge]]:
        """
        Find all simple paths from source to target within horizon.

        Returns list of edge paths. Follows edges in both directions
        (since MRH context is bidirectional).
        """
        limit = max_depth if max_depth is not None else self.horizon_depth
        if source not in self._nodes or target not in self._nodes:
            return []

        paths: List[List[MRHEdge]] = []
        stack: List[Tuple[str, List[MRHEdge], Set[str]]] = [
            (source, [], {source})
        ]

        while stack:
            current, path, visited = stack.pop()
            if current == target and path:
                paths.append(path)
                continue
            if len(path) >= limit:
                continue

            # Forward edges
            for neighbor, edge_idx in self._adj.get(current, []):
                if neighbor not in visited:
                    edge = self._edges[edge_idx]
                    stack.append((
                        neighbor,
                        path + [edge],
                        visited | {neighbor},
                    ))
            # Reverse edges
            for neighbor, edge_idx in self._rev.get(current, []):
                if neighbor not in visited:
                    edge = self._edges[edge_idx]
                    stack.append((
                        neighbor,
                        path + [edge],
                        visited | {neighbor},
                    ))

        return paths

    def trust_between(
        self,
        source: str,
        target: str,
        strategy: str = "probabilistic",
        decay_factor: float = 0.7,
    ) -> float:
        """
        Compute trust from source to target using path-based propagation.

        Strategies:
        - "multiplicative": geometric decay along best path
        - "probabilistic": combine all paths (1 - prod(1 - p_i))
        - "maximal": highest single-path trust

        Direct neighbors use edge weight * decay. Multi-hop paths
        accumulate multiplicative decay.
        """
        if source == target:
            return 1.0

        paths = self.find_paths(source, target)
        if not paths:
            return 0.0

        path_trusts = []
        for path in paths:
            weights = [e.weight for e in path]
            pt = propagate_multiplicative(weights, decay_factor)
            path_trusts.append(pt)

        if strategy == "multiplicative":
            return propagate_maximal(path_trusts)  # best single path
        elif strategy == "maximal":
            return propagate_maximal(path_trusts)
        else:  # probabilistic (default)
            return propagate_probabilistic(path_trusts)

    # ── Context Analysis ────────────────────────────────────────

    def relationship_summary(self, lct_id: str) -> Dict[str, int]:
        """
        Count relationships by category for an entity.

        Returns {"binding": N, "pairing": M, "witness": K}.
        """
        counts: Dict[str, int] = {"binding": 0, "pairing": 0, "witness": 0}
        for _, edge_idx in self._adj.get(lct_id, []):
            cat = self._edges[edge_idx].category
            if cat in counts:
                counts[cat] += 1
        for _, edge_idx in self._rev.get(lct_id, []):
            cat = self._edges[edge_idx].category
            if cat in counts:
                counts[cat] += 1
        return counts

    def witness_count(self, lct_id: str) -> int:
        """Count how many entities witness this entity (in-degree of witness edges)."""
        count = 0
        for _, edge_idx in self._rev.get(lct_id, []):
            if self._edges[edge_idx].relation in _WITNESS_TYPES:
                count += 1
        # Also count outgoing witness edges (entity witnesses others)
        for _, edge_idx in self._adj.get(lct_id, []):
            if self._edges[edge_idx].relation in _WITNESS_TYPES:
                count += 1
        return count

    def in_degree(self, lct_id: str) -> int:
        """Number of edges pointing to this entity."""
        return len(self._rev.get(lct_id, []))

    def out_degree(self, lct_id: str) -> int:
        """Number of edges from this entity."""
        return len(self._adj.get(lct_id, []))

    def connected_entities(
        self,
        lct_id: str,
        relation: Optional[RelationType] = None,
    ) -> List[str]:
        """Get entities directly connected (both directions)."""
        result = set()
        for neighbor, edge_idx in self._adj.get(lct_id, []):
            if relation is None or self._edges[edge_idx].relation == relation:
                result.add(neighbor)
        for neighbor, edge_idx in self._rev.get(lct_id, []):
            if relation is None or self._edges[edge_idx].relation == relation:
                result.add(neighbor)
        return list(result)

    # ── Serialization ───────────────────────────────────────────

    def as_dict(self) -> dict[str, Any]:
        """Serialize entire graph to dict with nodes, edges, and counts."""
        return {
            "horizonDepth": self.horizon_depth,
            "nodes": [n.as_dict() for n in self._nodes.values()],
            "edges": [e.as_dict() for e in self._edges],
            "nodeCount": self.node_count,
            "edgeCount": self.edge_count,
        }

    def graph_hash(self) -> str:
        """Deterministic hash of graph structure."""
        canonical = json.dumps(self.as_dict(), sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]
