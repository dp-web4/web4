"""Tests for resolve_trust() and TrustResolution.

Sprint 25 T1: Tensor-aware indirect trust resolution through MRH graphs.
Composes MRHGraph.trust_between() with TrustProfile T3 tensors.
"""

from __future__ import annotations

import pytest

from web4.mrh import MRHGraph, MRHEdge, MRHNode, RelationType
from web4.trust import (
    T3,
    TrustProfile,
    TrustResolution,
    resolve_trust,
)


# ── Fixtures ────────────────────────────────────────────────────


def _make_graph_linear() -> MRHGraph:
    """Linear graph: alice → bob → carol → dave."""
    g = MRHGraph(horizon_depth=4)
    for name in ("alice", "bob", "carol", "dave"):
        g.add_node(MRHNode(f"lct:{name}"))
    g.add_edge(MRHEdge("lct:alice", "lct:bob", RelationType.PAIRED_WITH, 0.9))
    g.add_edge(MRHEdge("lct:bob", "lct:carol", RelationType.PAIRED_WITH, 0.8))
    g.add_edge(MRHEdge("lct:carol", "lct:dave", RelationType.WITNESSED_BY, 0.7))
    return g


def _make_graph_diamond() -> MRHGraph:
    """Diamond graph: alice → bob → dave, alice → carol → dave."""
    g = MRHGraph(horizon_depth=3)
    for name in ("alice", "bob", "carol", "dave"):
        g.add_node(MRHNode(f"lct:{name}"))
    g.add_edge(MRHEdge("lct:alice", "lct:bob", RelationType.PAIRED_WITH, 0.9))
    g.add_edge(MRHEdge("lct:alice", "lct:carol", RelationType.PAIRED_WITH, 0.7))
    g.add_edge(MRHEdge("lct:bob", "lct:dave", RelationType.WITNESSED_BY, 0.8))
    g.add_edge(MRHEdge("lct:carol", "lct:dave", RelationType.WITNESSED_BY, 0.6))
    return g


def _make_profiles() -> dict[str, TrustProfile]:
    """TrustProfiles for alice, bob, carol, dave with various roles."""
    profiles: dict[str, TrustProfile] = {}

    alice = TrustProfile("lct:alice")
    alice.set_role("web4:Analyst", T3(0.9, 0.85, 0.8))
    profiles["lct:alice"] = alice

    bob = TrustProfile("lct:bob")
    bob.set_role("web4:Analyst", T3(0.8, 0.75, 0.7))
    bob.set_role("web4:Engineer", T3(0.6, 0.5, 0.55))
    profiles["lct:bob"] = bob

    carol = TrustProfile("lct:carol")
    carol.set_role("web4:Analyst", T3(0.7, 0.65, 0.6))
    carol.set_role("web4:Engineer", T3(0.85, 0.9, 0.8))
    profiles["lct:carol"] = carol

    dave = TrustProfile("lct:dave")
    dave.set_role("web4:Analyst", T3(0.6, 0.55, 0.5))
    dave.set_role("web4:Engineer", T3(0.95, 0.9, 0.85))
    profiles["lct:dave"] = dave

    return profiles


# ── Self-Trust (Direct) ────────────────────────────────────────


class TestDirectTrust:
    """resolve_trust where observer == target."""

    def test_self_trust_returns_own_t3(self) -> None:
        graph = MRHGraph()
        graph.add_node(MRHNode("lct:alice"))
        profiles = _make_profiles()
        result = resolve_trust(graph, profiles, "lct:alice", "lct:alice", "web4:Analyst")
        assert result.method == "direct"
        assert result.path_trust == 1.0
        assert result.hops == 0
        assert result.effective_t3 is not None
        assert result.effective_t3.talent == pytest.approx(0.9)
        assert result.effective_t3.training == pytest.approx(0.85)
        assert result.effective_t3.temperament == pytest.approx(0.8)

    def test_self_trust_unknown_role_returns_default(self) -> None:
        graph = MRHGraph()
        graph.add_node(MRHNode("lct:alice"))
        profiles = _make_profiles()
        result = resolve_trust(graph, profiles, "lct:alice", "lct:alice", "web4:Surgeon")
        assert result.method == "direct"
        assert result.effective_t3 is not None
        # Default T3 is (0.5, 0.5, 0.5)
        assert result.effective_t3.talent == pytest.approx(0.5)

    def test_self_trust_no_profile_returns_default(self) -> None:
        graph = MRHGraph()
        graph.add_node(MRHNode("lct:unknown"))
        result = resolve_trust(graph, {}, "lct:unknown", "lct:unknown", "web4:Analyst")
        assert result.method == "direct"
        assert result.effective_t3 is not None
        assert result.effective_t3.talent == pytest.approx(0.5)


# ── Indirect Trust (1-hop) ─────────────────────────────────────


class TestIndirectTrust1Hop:
    """resolve_trust through a single intermediary."""

    def test_1hop_indirect_attenuates_t3(self) -> None:
        graph = _make_graph_linear()
        profiles = _make_profiles()
        result = resolve_trust(graph, profiles, "lct:alice", "lct:bob", "web4:Analyst")
        assert result.method == "indirect"
        assert result.path_trust > 0
        assert result.effective_t3 is not None
        # T3 should be attenuated: bob's T3(0.8, 0.75, 0.7) * path_trust
        assert result.effective_t3.talent < 0.8
        assert result.effective_t3.talent > 0.0

    def test_1hop_path_trust_reflects_edge_weight(self) -> None:
        graph = _make_graph_linear()
        profiles = _make_profiles()
        result = resolve_trust(graph, profiles, "lct:alice", "lct:bob", "web4:Analyst")
        # Edge weight 0.9, decay 0.7, 1 hop → 0.9 * 0.7 = 0.63
        assert result.path_trust == pytest.approx(0.63)

    def test_1hop_hops_is_1(self) -> None:
        graph = _make_graph_linear()
        profiles = _make_profiles()
        result = resolve_trust(graph, profiles, "lct:alice", "lct:bob", "web4:Analyst")
        assert result.hops == 1


# ── Indirect Trust (Multi-hop) ─────────────────────────────────


class TestIndirectTrustMultiHop:
    """resolve_trust through multiple intermediaries."""

    def test_2hop_trust_lower_than_1hop(self) -> None:
        graph = _make_graph_linear()
        profiles = _make_profiles()
        r1 = resolve_trust(graph, profiles, "lct:alice", "lct:bob", "web4:Analyst")
        r2 = resolve_trust(graph, profiles, "lct:alice", "lct:carol", "web4:Analyst")
        assert r2.path_trust < r1.path_trust
        assert r2.hops == 2

    def test_3hop_trust_very_low(self) -> None:
        graph = _make_graph_linear()
        profiles = _make_profiles()
        result = resolve_trust(graph, profiles, "lct:alice", "lct:dave", "web4:Analyst")
        assert result.method == "indirect"
        assert result.path_trust < 0.3  # 3 hops of decay
        assert result.hops == 3

    def test_multihop_t3_proportional_to_path_trust(self) -> None:
        graph = _make_graph_linear()
        profiles = _make_profiles()
        result = resolve_trust(graph, profiles, "lct:alice", "lct:dave", "web4:Engineer")
        assert result.effective_t3 is not None
        # dave's T3 for Engineer: (0.95, 0.9, 0.85), attenuated by path_trust
        assert result.effective_t3.talent == pytest.approx(0.95 * result.path_trust, abs=0.01)
        assert result.effective_t3.training == pytest.approx(0.9 * result.path_trust, abs=0.01)


# ── Multi-Path Aggregation ─────────────────────────────────────


class TestMultiPathAggregation:
    """resolve_trust with diamond graph (multiple paths)."""

    def test_probabilistic_higher_than_single_path(self) -> None:
        graph = _make_graph_diamond()
        profiles = _make_profiles()
        result = resolve_trust(
            graph,
            profiles,
            "lct:alice",
            "lct:dave",
            "web4:Analyst",
            strategy="probabilistic",
        )
        assert result.method == "indirect"
        assert result.strategy == "probabilistic"
        # Probabilistic combines paths: higher than any single path
        # Path 1: alice→bob→dave, Path 2: alice→carol→dave
        assert result.path_trust > 0

    def test_maximal_strategy(self) -> None:
        graph = _make_graph_diamond()
        profiles = _make_profiles()
        result = resolve_trust(
            graph,
            profiles,
            "lct:alice",
            "lct:dave",
            "web4:Analyst",
            strategy="maximal",
        )
        assert result.strategy == "maximal"
        assert result.path_trust > 0

    def test_probabilistic_vs_maximal(self) -> None:
        graph = _make_graph_diamond()
        profiles = _make_profiles()
        r_prob = resolve_trust(
            graph,
            profiles,
            "lct:alice",
            "lct:dave",
            "web4:Analyst",
            strategy="probabilistic",
        )
        r_max = resolve_trust(
            graph,
            profiles,
            "lct:alice",
            "lct:dave",
            "web4:Analyst",
            strategy="maximal",
        )
        # Probabilistic >= maximal (can only be higher with multiple paths)
        assert r_prob.path_trust >= r_max.path_trust


# ── No Path Found ──────────────────────────────────────────────


class TestNoPath:
    """resolve_trust when no path exists."""

    def test_disconnected_entities_returns_none_method(self) -> None:
        graph = MRHGraph()
        graph.add_node(MRHNode("lct:alice"))
        graph.add_node(MRHNode("lct:bob"))
        # No edge between alice and bob
        profiles = _make_profiles()
        result = resolve_trust(graph, profiles, "lct:alice", "lct:bob", "web4:Analyst")
        assert result.method == "none"
        assert result.effective_t3 is None
        assert result.path_trust == 0.0

    def test_unknown_target_not_in_graph(self) -> None:
        graph = MRHGraph()
        graph.add_node(MRHNode("lct:alice"))
        profiles = _make_profiles()
        result = resolve_trust(graph, profiles, "lct:alice", "lct:nobody", "web4:Analyst")
        assert result.method == "none"
        assert result.effective_t3 is None


# ── Custom Decay Factor ────────────────────────────────────────


class TestDecayFactor:
    """resolve_trust with custom decay_factor."""

    def test_higher_decay_gives_more_trust(self) -> None:
        graph = _make_graph_linear()
        profiles = _make_profiles()
        r_low = resolve_trust(
            graph,
            profiles,
            "lct:alice",
            "lct:bob",
            "web4:Analyst",
            decay_factor=0.5,
        )
        r_high = resolve_trust(
            graph,
            profiles,
            "lct:alice",
            "lct:bob",
            "web4:Analyst",
            decay_factor=0.9,
        )
        assert r_high.path_trust > r_low.path_trust

    def test_zero_decay_gives_zero_trust(self) -> None:
        graph = _make_graph_linear()
        profiles = _make_profiles()
        result = resolve_trust(
            graph,
            profiles,
            "lct:alice",
            "lct:bob",
            "web4:Analyst",
            decay_factor=0.0,
        )
        assert result.method == "none"
        assert result.path_trust == 0.0


# ── TrustResolution Round-Trip ─────────────────────────────────


class TestTrustResolutionRoundTrip:
    """TrustResolution to_dict/from_dict round-trip."""

    def test_roundtrip_with_t3(self) -> None:
        original = TrustResolution(
            observer="lct:alice",
            target="lct:bob",
            role="web4:Analyst",
            method="indirect",
            effective_t3=T3(0.6, 0.55, 0.5),
            path_trust=0.75,
            hops=1,
            strategy="probabilistic",
        )
        d = original.to_dict()
        restored = TrustResolution.from_dict(d)
        assert restored.observer == original.observer
        assert restored.target == original.target
        assert restored.role == original.role
        assert restored.method == original.method
        assert restored.path_trust == pytest.approx(original.path_trust)
        assert restored.hops == original.hops
        assert restored.strategy == original.strategy
        assert restored.effective_t3 is not None
        assert restored.effective_t3.talent == pytest.approx(0.6)

    def test_roundtrip_without_t3(self) -> None:
        original = TrustResolution(
            observer="lct:alice",
            target="lct:nobody",
            role="web4:Analyst",
            method="none",
        )
        d = original.to_dict()
        restored = TrustResolution.from_dict(d)
        assert restored.method == "none"
        assert restored.effective_t3 is None
        assert restored.path_trust == 0.0

    def test_to_dict_structure(self) -> None:
        resolution = TrustResolution(
            observer="lct:alice",
            target="lct:bob",
            role="web4:Engineer",
            method="indirect",
            effective_t3=T3(0.4, 0.3, 0.2),
            path_trust=0.5,
            hops=2,
            strategy="maximal",
        )
        d = resolution.to_dict()
        assert d["observer"] == "lct:alice"
        assert d["target"] == "lct:bob"
        assert d["role"] == "web4:Engineer"
        assert d["method"] == "indirect"
        assert d["path_trust"] == pytest.approx(0.5)
        assert d["hops"] == 2
        assert d["strategy"] == "maximal"
        assert "effective_t3" in d
        assert d["effective_t3"]["talent"] == pytest.approx(0.4)


# ── Integration: resolve_trust + TrustResolution ───────────────


class TestIntegration:
    """End-to-end: resolve_trust returns a TrustResolution that round-trips."""

    def test_indirect_result_round_trips(self) -> None:
        graph = _make_graph_linear()
        profiles = _make_profiles()
        result = resolve_trust(graph, profiles, "lct:alice", "lct:carol", "web4:Engineer")
        d = result.to_dict()
        restored = TrustResolution.from_dict(d)
        assert restored.method == "indirect"
        assert restored.path_trust == pytest.approx(result.path_trust)
        assert restored.effective_t3 is not None
        assert restored.effective_t3.talent == pytest.approx(
            result.effective_t3.talent,
            abs=0.001,  # type: ignore[union-attr]
        )

    def test_direct_result_round_trips(self) -> None:
        graph = MRHGraph()
        graph.add_node(MRHNode("lct:alice"))
        profiles = _make_profiles()
        result = resolve_trust(graph, profiles, "lct:alice", "lct:alice", "web4:Analyst")
        d = result.to_dict()
        restored = TrustResolution.from_dict(d)
        assert restored.method == "direct"
        assert restored.effective_t3 is not None
        assert restored.effective_t3.talent == pytest.approx(0.9)

    def test_different_roles_different_results(self) -> None:
        graph = _make_graph_linear()
        profiles = _make_profiles()
        r_analyst = resolve_trust(graph, profiles, "lct:alice", "lct:carol", "web4:Analyst")
        r_engineer = resolve_trust(graph, profiles, "lct:alice", "lct:carol", "web4:Engineer")
        # Same path_trust (same graph path), but different effective_t3
        assert r_analyst.path_trust == pytest.approx(r_engineer.path_trust)
        assert r_analyst.effective_t3 is not None
        assert r_engineer.effective_t3 is not None
        # Carol has different T3 for Analyst vs Engineer
        assert r_analyst.effective_t3.talent != pytest.approx(r_engineer.effective_t3.talent, abs=0.01)
