"""Tests for web4.mrh — Markov Relevancy Horizon graph."""

import json
import os
import pytest

from web4.mrh import (
    MRHEdge,
    MRHGraph,
    MRHNode,
    RelationType,
    propagate_maximal,
    propagate_multiplicative,
    propagate_probabilistic,
    relation_category,
)
from web4.trust import mrh_zone


# ── RelationType Tests ──────────────────────────────────────────

class TestRelationType:
    def test_binding_category(self):
        assert relation_category(RelationType.BOUND_TO) == "binding"
        assert relation_category(RelationType.PARENT_BINDING) == "binding"
        assert relation_category(RelationType.CHILD_BINDING) == "binding"
        assert relation_category(RelationType.SIBLING_BINDING) == "binding"

    def test_pairing_category(self):
        assert relation_category(RelationType.PAIRED_WITH) == "pairing"
        assert relation_category(RelationType.ENERGY_PAIRING) == "pairing"
        assert relation_category(RelationType.DATA_PAIRING) == "pairing"

    def test_witness_category(self):
        assert relation_category(RelationType.WITNESSED_BY) == "witness"
        assert relation_category(RelationType.TIME_WITNESS) == "witness"
        assert relation_category(RelationType.AUDIT_WITNESS) == "witness"
        assert relation_category(RelationType.ORACLE_WITNESS) == "witness"


# ── Node/Edge Tests ─────────────────────────────────────────────

class TestMRHNode:
    def test_basic_node(self):
        node = MRHNode("lct:alice", "human")
        assert node.lct_id == "lct:alice"
        assert node.entity_type == "human"
        assert node.trust_scores == {}

    def test_node_serialization(self):
        node = MRHNode("lct:alice", "human", {"composite": 0.85})
        d = node.as_dict()
        assert d["lctId"] == "lct:alice"
        assert d["entityType"] == "human"
        assert d["trustScores"]["composite"] == 0.85


class TestMRHEdge:
    def test_basic_edge(self):
        edge = MRHEdge("lct:alice", "lct:bob", RelationType.PAIRED_WITH, 0.9)
        assert edge.source == "lct:alice"
        assert edge.target == "lct:bob"
        assert edge.weight == 0.9
        assert edge.category == "pairing"

    def test_weight_clamping(self):
        edge = MRHEdge("a", "b", RelationType.BOUND_TO, 1.5)
        assert edge.weight == 1.0
        edge2 = MRHEdge("a", "b", RelationType.BOUND_TO, -0.5)
        assert edge2.weight == 0.0

    def test_string_relation(self):
        edge = MRHEdge("a", "b", "boundTo", 0.8)
        assert edge.relation == RelationType.BOUND_TO

    def test_edge_serialization(self):
        edge = MRHEdge("lct:alice", "lct:hw1", RelationType.BOUND_TO, 1.0,
                       timestamp="2026-01-01T00:00:00Z")
        d = edge.as_dict()
        assert d["relation"] == "boundTo"
        assert d["category"] == "binding"
        assert d["timestamp"] == "2026-01-01T00:00:00Z"


# ── Propagation Strategy Tests ──────────────────────────────────

class TestPropagation:
    def test_multiplicative_single_hop(self):
        # 1 hop: weight * decay^1 = 0.9 * 0.7 = 0.63
        result = propagate_multiplicative([0.9], 0.7)
        assert abs(result - 0.63) < 1e-10

    def test_multiplicative_two_hops(self):
        # hop1: 0.9 * 0.7 = 0.63, hop2: 0.63 * 0.8 * 0.49 = 0.24696
        result = propagate_multiplicative([0.9, 0.8], 0.7)
        expected = 0.9 * 0.7 * 0.8 * 0.49  # 0.7^1 * 0.7^2
        assert abs(result - expected) < 1e-10

    def test_multiplicative_empty(self):
        assert propagate_multiplicative([]) == 1.0

    def test_probabilistic_single(self):
        assert abs(propagate_probabilistic([0.5]) - 0.5) < 1e-10

    def test_probabilistic_two_paths(self):
        # 1 - (1-0.5)(1-0.3) = 1 - 0.35 = 0.65
        result = propagate_probabilistic([0.5, 0.3])
        assert abs(result - 0.65) < 1e-10

    def test_probabilistic_empty(self):
        assert propagate_probabilistic([]) == 0.0

    def test_maximal(self):
        assert propagate_maximal([0.3, 0.7, 0.5]) == 0.7

    def test_maximal_empty(self):
        assert propagate_maximal([]) == 0.0


# ── MRH Graph Tests ─────────────────────────────────────────────

def _build_sample_graph() -> MRHGraph:
    """
    Build a sample graph:
      alice --pairedWith(0.9)--> bob
      alice --boundTo(1.0)--> hw1
      bob --witnessedBy(0.8)--> timeserver
      bob --pairedWith(0.7)--> carol
    """
    g = MRHGraph(horizon_depth=3)
    g.add_node(MRHNode("lct:alice", "human"))
    g.add_node(MRHNode("lct:bob", "human"))
    g.add_node(MRHNode("lct:hw1", "device"))
    g.add_node(MRHNode("lct:timeserver", "oracle"))
    g.add_node(MRHNode("lct:carol", "human"))

    g.add_edge(MRHEdge("lct:alice", "lct:bob", RelationType.PAIRED_WITH, 0.9))
    g.add_edge(MRHEdge("lct:alice", "lct:hw1", RelationType.BOUND_TO, 1.0))
    g.add_edge(MRHEdge("lct:bob", "lct:timeserver", RelationType.WITNESSED_BY, 0.8))
    g.add_edge(MRHEdge("lct:bob", "lct:carol", RelationType.PAIRED_WITH, 0.7))
    return g


class TestMRHGraph:
    def test_add_node(self):
        g = MRHGraph()
        g.add_node(MRHNode("lct:alice", "human"))
        assert g.node_count == 1
        assert g.get_node("lct:alice").entity_type == "human"

    def test_add_edge_auto_creates_nodes(self):
        g = MRHGraph()
        g.add_edge(MRHEdge("a", "b", RelationType.PAIRED_WITH))
        assert g.node_count == 2
        assert g.edge_count == 1

    def test_get_edges_by_source(self):
        g = _build_sample_graph()
        edges = g.get_edges(source="lct:alice")
        assert len(edges) == 2

    def test_get_edges_by_relation(self):
        g = _build_sample_graph()
        edges = g.get_edges(relation=RelationType.PAIRED_WITH)
        assert len(edges) == 2

    def test_get_edges_by_target(self):
        g = _build_sample_graph()
        edges = g.get_edges(target="lct:bob")
        assert len(edges) == 1
        assert edges[0].source == "lct:alice"

    def test_in_out_degree(self):
        g = _build_sample_graph()
        assert g.out_degree("lct:alice") == 2
        assert g.in_degree("lct:bob") == 1

    def test_connected_entities(self):
        g = _build_sample_graph()
        connected = g.connected_entities("lct:bob")
        assert set(connected) == {"lct:alice", "lct:timeserver", "lct:carol"}


class TestHorizon:
    def test_horizon_depth_1(self):
        g = _build_sample_graph()
        h = g.horizon("lct:alice", depth=1)
        assert h["lct:alice"] == 0
        assert h["lct:bob"] == 1
        assert h["lct:hw1"] == 1
        assert "lct:carol" not in h

    def test_horizon_depth_2(self):
        g = _build_sample_graph()
        h = g.horizon("lct:alice", depth=2)
        assert h["lct:carol"] == 2
        assert h["lct:timeserver"] == 2

    def test_horizon_default_depth(self):
        g = _build_sample_graph()
        h = g.horizon("lct:alice")
        # Default depth=3, all 5 nodes reachable
        assert len(h) == 5

    def test_horizon_unknown_origin(self):
        g = _build_sample_graph()
        h = g.horizon("lct:unknown")
        assert h == {}

    def test_horizon_with_relation_filter(self):
        g = _build_sample_graph()
        h = g.horizon("lct:alice", relation_filter={RelationType.PAIRED_WITH})
        # Only follows pairing edges: alice->bob->carol
        assert "lct:bob" in h
        assert "lct:carol" in h
        assert "lct:hw1" not in h  # hw1 is binding, not pairing

    def test_horizon_zones(self):
        g = _build_sample_graph()
        zones = g.horizon_zones("lct:alice")
        assert "lct:alice" in zones["SELF"]
        assert "lct:bob" in zones["DIRECT"]
        assert "lct:hw1" in zones["DIRECT"]


class TestTrustPropagation:
    def test_trust_self(self):
        g = _build_sample_graph()
        assert g.trust_between("lct:alice", "lct:alice") == 1.0

    def test_trust_direct(self):
        g = _build_sample_graph()
        trust = g.trust_between("lct:alice", "lct:bob")
        # Direct: 0.9 * 0.7^1 = 0.63
        assert trust > 0.0

    def test_trust_two_hops(self):
        g = _build_sample_graph()
        trust = g.trust_between("lct:alice", "lct:carol")
        # Indirect through bob, lower than direct
        direct_trust = g.trust_between("lct:alice", "lct:bob")
        assert 0 < trust < direct_trust

    def test_trust_no_path(self):
        g = MRHGraph()
        g.add_node(MRHNode("a"))
        g.add_node(MRHNode("b"))
        assert g.trust_between("a", "b") == 0.0

    def test_trust_strategy_maximal(self):
        g = _build_sample_graph()
        trust = g.trust_between("lct:alice", "lct:bob", strategy="maximal")
        assert trust > 0.0

    def test_trust_multiplicative_strategy(self):
        g = _build_sample_graph()
        trust = g.trust_between("lct:alice", "lct:bob", strategy="multiplicative")
        assert trust > 0.0


class TestContextAnalysis:
    def test_relationship_summary(self):
        g = _build_sample_graph()
        summary = g.relationship_summary("lct:alice")
        assert summary["binding"] == 1   # boundTo hw1
        assert summary["pairing"] == 1   # pairedWith bob
        assert summary["witness"] == 0

    def test_relationship_summary_bob(self):
        g = _build_sample_graph()
        summary = g.relationship_summary("lct:bob")
        assert summary["pairing"] == 2   # from alice + to carol
        assert summary["witness"] == 1   # witnessedBy timeserver

    def test_witness_count(self):
        g = _build_sample_graph()
        assert g.witness_count("lct:timeserver") == 1
        assert g.witness_count("lct:alice") == 0

    def test_graph_serialization(self):
        g = _build_sample_graph()
        d = g.as_dict()
        assert d["nodeCount"] == 5
        assert d["edgeCount"] == 4
        assert d["horizonDepth"] == 3

    def test_graph_hash_deterministic(self):
        g1 = _build_sample_graph()
        g2 = _build_sample_graph()
        assert g1.graph_hash() == g2.graph_hash()


# ── Test Vectors ────────────────────────────────────────────────

class TestMRHVectors:
    @pytest.fixture
    def vectors(self):
        path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..",
            "test-vectors", "mrh", "graph-operations.json"
        )
        with open(path) as f:
            return json.load(f)

    def test_horizon_traversal(self, vectors):
        vec = next(v for v in vectors["vectors"] if v["id"] == "mrh-001")
        g = MRHGraph(horizon_depth=vec["input"]["horizonDepth"])
        for n in vec["input"]["nodes"]:
            g.add_node(MRHNode(n["lctId"], n.get("entityType", "unknown")))
        for e in vec["input"]["edges"]:
            g.add_edge(MRHEdge(e["source"], e["target"],
                               RelationType(e["relation"]), e["weight"]))
        h = g.horizon(vec["input"]["origin"], depth=vec["input"]["horizonDepth"])
        for entity_id, expected_dist in vec["expected"]["distances"].items():
            assert h[entity_id] == expected_dist

    def test_trust_propagation(self, vectors):
        vec = next(v for v in vectors["vectors"] if v["id"] == "mrh-002")
        g = MRHGraph()
        for n in vec["input"]["nodes"]:
            g.add_node(MRHNode(n["lctId"]))
        for e in vec["input"]["edges"]:
            g.add_edge(MRHEdge(e["source"], e["target"],
                               RelationType(e["relation"]), e["weight"]))
        trust = g.trust_between(
            vec["input"]["source"], vec["input"]["target"],
            strategy=vec["input"]["strategy"],
            decay_factor=vec["input"]["decayFactor"],
        )
        assert abs(trust - vec["expected"]["trust"]) < vec["expected"]["tolerance"]

    def test_relationship_summary(self, vectors):
        vec = next(v for v in vectors["vectors"] if v["id"] == "mrh-003")
        g = MRHGraph()
        for n in vec["input"]["nodes"]:
            g.add_node(MRHNode(n["lctId"]))
        for e in vec["input"]["edges"]:
            g.add_edge(MRHEdge(e["source"], e["target"],
                               RelationType(e["relation"]), e["weight"]))
        summary = g.relationship_summary(vec["input"]["entity"])
        assert summary == vec["expected"]["summary"]
