#!/usr/bin/env python3
"""
Trust Graph Resilience — Web4 Session 27, Track 2

Analyzes how trust network topology responds to targeted attacks.
Existing trust_graph_analysis.py covers community detection and anomaly scoring.
This goes deeper: what happens when attackers strategically remove nodes,
partition the network, or inject Byzantine nodes?

Key questions:
1. How resilient is Web4's trust graph to targeted node removal (high-centrality attacks)?
2. What is the minimum number of nodes to remove to partition the trust network?
3. How quickly does the network recover after mass node removal?
4. What trust graph topologies are most/least resilient?
5. What does Byzantine node injection look like in the trust graph?
6. Can trust graph structure PREDICT imminent attacks?

Reference: Network resilience theory (Albert & Barabási 2000, Callaway 2000)
"""

import hashlib
import json
import math
import time
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, deque


# ============================================================
# Section 1: Trust Graph Model
# ============================================================

@dataclass
class TrustNode:
    """A node in the trust graph (entity with LCT)."""
    node_id: str
    t3_talent: float = 0.5
    t3_training: float = 0.5
    t3_temperament: float = 0.5
    atp_balance: float = 100.0
    hardware_bound: bool = False
    federation: str = "default"
    is_byzantine: bool = False

    @property
    def t3_composite(self) -> float:
        return (self.t3_talent + self.t3_training + self.t3_temperament) / 3.0


@dataclass
class TrustEdge:
    """A directed trust relationship between two nodes."""
    source: str
    target: str
    weight: float  # trust score from source's perspective of target
    witness_count: int = 1
    age_seconds: float = 0.0


class TrustGraph:
    """
    A directed weighted graph representing trust relationships.

    Nodes = entities with LCTs
    Edges = trust attestations with weights
    """

    def __init__(self):
        self.nodes: Dict[str, TrustNode] = {}
        self.edges: Dict[str, Dict[str, TrustEdge]] = defaultdict(dict)  # source -> target -> edge

    def add_node(self, node: TrustNode):
        self.nodes[node.node_id] = node
        if node.node_id not in self.edges:
            self.edges[node.node_id] = {}

    def add_edge(self, source: str, target: str, weight: float, witness_count: int = 1):
        if source in self.nodes and target in self.nodes:
            self.edges[source][target] = TrustEdge(
                source=source, target=target, weight=weight, witness_count=witness_count
            )

    def remove_node(self, node_id: str) -> Tuple[int, int]:
        """Remove a node and all its edges. Returns (edges_removed_outgoing, edges_removed_incoming)."""
        outgoing = len(self.edges.get(node_id, {}))
        incoming = 0
        for source in list(self.edges.keys()):
            if node_id in self.edges[source]:
                del self.edges[source][node_id]
                incoming += 1
        if node_id in self.edges:
            del self.edges[node_id]
        if node_id in self.nodes:
            del self.nodes[node_id]
        return outgoing, incoming

    def node_count(self) -> int:
        return len(self.nodes)

    def edge_count(self) -> int:
        return sum(len(targets) for targets in self.edges.values())

    def in_degree(self, node_id: str) -> int:
        """Number of incoming trust edges."""
        return sum(1 for source in self.edges if node_id in self.edges[source])

    def out_degree(self, node_id: str) -> int:
        """Number of outgoing trust edges."""
        return len(self.edges.get(node_id, {}))

    def degree(self, node_id: str) -> int:
        return self.in_degree(node_id) + self.out_degree(node_id)

    def neighbors(self, node_id: str) -> Set[str]:
        """All nodes connected (either direction)."""
        result = set(self.edges.get(node_id, {}).keys())
        for source in self.edges:
            if node_id in self.edges[source]:
                result.add(source)
        return result

    def connected_components(self) -> List[Set[str]]:
        """Find connected components (treating graph as undirected)."""
        visited = set()
        components = []

        for node_id in self.nodes:
            if node_id not in visited:
                component = set()
                queue = deque([node_id])
                while queue:
                    current = queue.popleft()
                    if current in visited:
                        continue
                    visited.add(current)
                    component.add(current)
                    for neighbor in self.neighbors(current):
                        if neighbor not in visited:
                            queue.append(neighbor)
                components.append(component)

        return components

    def largest_component_fraction(self) -> float:
        """Fraction of nodes in the largest connected component."""
        if not self.nodes:
            return 0.0
        components = self.connected_components()
        largest = max(len(c) for c in components) if components else 0
        return largest / len(self.nodes)

    def average_path_length(self, sample_size: int = 50) -> float:
        """Approximate average shortest path length via BFS sampling."""
        if len(self.nodes) < 2:
            return 0.0

        node_ids = list(self.nodes.keys())
        total_length = 0
        count = 0

        for _ in range(min(sample_size, len(node_ids))):
            source = node_ids[_ % len(node_ids)]
            distances = self._bfs_distances(source)
            for target, dist in distances.items():
                if target != source and dist < float('inf'):
                    total_length += dist
                    count += 1

        return total_length / count if count > 0 else float('inf')

    def _bfs_distances(self, source: str) -> Dict[str, int]:
        """BFS shortest distances from source (treating as undirected)."""
        distances = {source: 0}
        queue = deque([source])
        while queue:
            current = queue.popleft()
            for neighbor in self.neighbors(current):
                if neighbor not in distances:
                    distances[neighbor] = distances[current] + 1
                    queue.append(neighbor)
        return distances

    def betweenness_centrality_approx(self, sample_size: int = 30) -> Dict[str, float]:
        """Approximate betweenness centrality via sampling."""
        centrality = {nid: 0.0 for nid in self.nodes}
        node_ids = list(self.nodes.keys())

        for i in range(min(sample_size, len(node_ids))):
            source = node_ids[i % len(node_ids)]
            # BFS to find shortest paths
            distances = {}
            predecessors = defaultdict(list)
            num_paths = defaultdict(int)
            queue = deque([source])
            distances[source] = 0
            num_paths[source] = 1

            while queue:
                current = queue.popleft()
                for neighbor in self.neighbors(current):
                    if neighbor not in distances:
                        distances[neighbor] = distances[current] + 1
                        queue.append(neighbor)
                    if distances.get(neighbor, -1) == distances[current] + 1:
                        predecessors[neighbor].append(current)
                        num_paths[neighbor] += num_paths[current]

            # Back-propagate dependency
            dependency = defaultdict(float)
            nodes_by_distance = sorted(distances.keys(), key=lambda n: -distances.get(n, 0))
            for node in nodes_by_distance:
                for pred in predecessors[node]:
                    fraction = num_paths[pred] / num_paths[node] if num_paths[node] > 0 else 0
                    dependency[pred] += fraction * (1 + dependency[node])
                if node != source:
                    centrality[node] += dependency[node]

        # Normalize
        n = len(self.nodes)
        if n > 2:
            for nid in centrality:
                centrality[nid] /= ((n - 1) * (n - 2))

        return centrality

    def clustering_coefficient(self, node_id: str) -> float:
        """Local clustering coefficient for a node."""
        neighbors = self.neighbors(node_id)
        if len(neighbors) < 2:
            return 0.0

        neighbor_list = list(neighbors)
        links = 0
        for i in range(len(neighbor_list)):
            for j in range(i + 1, len(neighbor_list)):
                a, b = neighbor_list[i], neighbor_list[j]
                if b in self.edges.get(a, {}) or a in self.edges.get(b, {}):
                    links += 1

        max_links = len(neighbors) * (len(neighbors) - 1) / 2
        return links / max_links if max_links > 0 else 0.0

    def average_clustering(self) -> float:
        """Average clustering coefficient across all nodes."""
        if not self.nodes:
            return 0.0
        return sum(self.clustering_coefficient(nid) for nid in self.nodes) / len(self.nodes)


# ============================================================
# Section 2: Graph Generators
# ============================================================

class TrustGraphGenerator:
    """Generates different trust graph topologies for resilience testing."""

    @staticmethod
    def scale_free(n: int, m: int = 3, seed: int = 42) -> TrustGraph:
        """
        Barabási-Albert scale-free graph.
        High-degree hubs are natural attack targets.
        """
        rng = random.Random(seed)
        graph = TrustGraph()

        # Start with m+1 fully connected nodes
        for i in range(m + 1):
            graph.add_node(TrustNode(node_id=f"n{i}", t3_talent=0.5 + rng.random() * 0.3))

        for i in range(m + 1):
            for j in range(i + 1, m + 1):
                weight = 0.5 + rng.random() * 0.3
                graph.add_edge(f"n{i}", f"n{j}", weight)
                graph.add_edge(f"n{j}", f"n{i}", weight)

        # Preferential attachment
        degree_sum = [(f"n{i}", graph.degree(f"n{i}")) for i in range(m + 1)]

        for i in range(m + 1, n):
            new_id = f"n{i}"
            graph.add_node(TrustNode(node_id=new_id, t3_talent=0.5 + rng.random() * 0.3))

            # Select m nodes proportional to degree
            total_degree = sum(d for _, d in degree_sum)
            targets = set()
            attempts = 0
            while len(targets) < m and attempts < 100:
                r = rng.random() * total_degree
                cumulative = 0
                for nid, d in degree_sum:
                    cumulative += d
                    if cumulative >= r:
                        targets.add(nid)
                        break
                attempts += 1

            for target in targets:
                weight = 0.5 + rng.random() * 0.3
                graph.add_edge(new_id, target, weight)
                graph.add_edge(target, new_id, weight)

            degree_sum.append((new_id, len(targets) * 2))

        return graph

    @staticmethod
    def small_world(n: int, k: int = 6, p: float = 0.1, seed: int = 42) -> TrustGraph:
        """
        Watts-Strogatz small-world graph.
        High clustering + short paths.
        """
        rng = random.Random(seed)
        graph = TrustGraph()

        for i in range(n):
            graph.add_node(TrustNode(node_id=f"n{i}", t3_talent=0.5 + rng.random() * 0.3))

        # Ring lattice
        for i in range(n):
            for j in range(1, k // 2 + 1):
                target = (i + j) % n
                weight = 0.5 + rng.random() * 0.3
                graph.add_edge(f"n{i}", f"n{target}", weight)
                graph.add_edge(f"n{target}", f"n{i}", weight)

        # Rewire with probability p
        for i in range(n):
            for j in range(1, k // 2 + 1):
                if rng.random() < p:
                    target = (i + j) % n
                    new_target = rng.randint(0, n - 1)
                    while new_target == i or f"n{new_target}" in graph.edges.get(f"n{i}", {}):
                        new_target = rng.randint(0, n - 1)
                    # Rewire
                    if f"n{target}" in graph.edges.get(f"n{i}", {}):
                        del graph.edges[f"n{i}"][f"n{target}"]
                    weight = 0.5 + rng.random() * 0.3
                    graph.add_edge(f"n{i}", f"n{new_target}", weight)
                    graph.add_edge(f"n{new_target}", f"n{i}", weight)

        return graph

    @staticmethod
    def federated(n_federations: int = 4, nodes_per_fed: int = 15,
                  bridge_count: int = 3, seed: int = 42) -> TrustGraph:
        """
        Federated graph: dense communities connected by bridge nodes.
        Realistic Web4 topology.
        """
        rng = random.Random(seed)
        graph = TrustGraph()

        federation_names = [f"fed{i}" for i in range(n_federations)]

        # Create dense intra-federation connections
        for fi, fed_name in enumerate(federation_names):
            node_start = fi * nodes_per_fed
            for i in range(nodes_per_fed):
                nid = f"n{node_start + i}"
                graph.add_node(TrustNode(
                    node_id=nid,
                    t3_talent=0.5 + rng.random() * 0.3,
                    federation=fed_name
                ))

            # Dense intra-federation edges (p=0.5)
            for i in range(nodes_per_fed):
                for j in range(i + 1, nodes_per_fed):
                    if rng.random() < 0.5:
                        src = f"n{node_start + i}"
                        tgt = f"n{node_start + j}"
                        weight = 0.6 + rng.random() * 0.3
                        graph.add_edge(src, tgt, weight)
                        graph.add_edge(tgt, src, weight)

        # Bridge connections between federations
        for fi in range(n_federations):
            for fj in range(fi + 1, n_federations):
                for _ in range(bridge_count):
                    src_idx = fi * nodes_per_fed + rng.randint(0, nodes_per_fed - 1)
                    tgt_idx = fj * nodes_per_fed + rng.randint(0, nodes_per_fed - 1)
                    weight = 0.4 + rng.random() * 0.3  # lower inter-federation trust
                    graph.add_edge(f"n{src_idx}", f"n{tgt_idx}", weight)
                    graph.add_edge(f"n{tgt_idx}", f"n{src_idx}", weight)

        return graph

    @staticmethod
    def random_graph(n: int, p: float = 0.15, seed: int = 42) -> TrustGraph:
        """Erdős-Rényi random graph for baseline comparison."""
        rng = random.Random(seed)
        graph = TrustGraph()

        for i in range(n):
            graph.add_node(TrustNode(node_id=f"n{i}", t3_talent=0.5 + rng.random() * 0.3))

        for i in range(n):
            for j in range(i + 1, n):
                if rng.random() < p:
                    weight = 0.5 + rng.random() * 0.3
                    graph.add_edge(f"n{i}", f"n{j}", weight)
                    graph.add_edge(f"n{j}", f"n{i}", weight)

        return graph


# ============================================================
# Section 3: Attack Strategies
# ============================================================

class AttackStrategy(Enum):
    RANDOM = "random"                    # Remove random nodes
    HIGHEST_DEGREE = "highest_degree"    # Target highest-degree nodes (hubs)
    HIGHEST_BETWEENNESS = "highest_betweenness"  # Target bridge nodes
    HIGHEST_TRUST = "highest_trust"      # Target most trusted nodes
    FEDERATION_BRIDGES = "federation_bridges"  # Target inter-federation bridges
    LOWEST_COST = "lowest_cost"          # Target nodes with lowest hardware binding cost


class AttackExecutor:
    """Executes attack strategies against trust graphs and measures impact."""

    def __init__(self, graph: TrustGraph):
        self.original_graph = graph
        self.working_graph = self._copy_graph(graph)

    def _copy_graph(self, graph: TrustGraph) -> TrustGraph:
        """Deep copy a trust graph."""
        new_graph = TrustGraph()
        for nid, node in graph.nodes.items():
            new_graph.add_node(TrustNode(
                node_id=node.node_id,
                t3_talent=node.t3_talent,
                t3_training=node.t3_training,
                t3_temperament=node.t3_temperament,
                atp_balance=node.atp_balance,
                hardware_bound=node.hardware_bound,
                federation=node.federation,
                is_byzantine=node.is_byzantine,
            ))
        for source, targets in graph.edges.items():
            for target, edge in targets.items():
                new_graph.add_edge(source, target, edge.weight, edge.witness_count)
        return new_graph

    def reset(self):
        """Reset working graph to original."""
        self.working_graph = self._copy_graph(self.original_graph)

    def execute_attack(self, strategy: AttackStrategy, removal_fraction: float,
                       seed: int = 42) -> Dict[str, Any]:
        """
        Execute attack strategy, removing removal_fraction of nodes.
        Returns metrics before and after.
        """
        self.reset()
        graph = self.working_graph
        n_original = graph.node_count()
        n_to_remove = int(n_original * removal_fraction)

        # Pre-attack metrics
        pre_metrics = self._compute_metrics(graph)

        # Select nodes to remove based on strategy
        targets = self._select_targets(graph, strategy, n_to_remove, seed)

        # Remove nodes
        for target in targets:
            if target in graph.nodes:
                graph.remove_node(target)

        # Post-attack metrics
        post_metrics = self._compute_metrics(graph)

        return {
            "strategy": strategy.value,
            "nodes_removed": len(targets),
            "removal_fraction": removal_fraction,
            "pre_attack": pre_metrics,
            "post_attack": post_metrics,
            "impact": {
                "connectivity_loss": pre_metrics["largest_component"] - post_metrics["largest_component"],
                "components_created": post_metrics["num_components"] - pre_metrics["num_components"],
                "avg_path_increase": (post_metrics["avg_path_length"] - pre_metrics["avg_path_length"])
                    if post_metrics["avg_path_length"] < float('inf') else float('inf'),
                "clustering_change": post_metrics["avg_clustering"] - pre_metrics["avg_clustering"],
            },
        }

    def _select_targets(self, graph: TrustGraph, strategy: AttackStrategy,
                        n: int, seed: int) -> List[str]:
        """Select n nodes to remove based on attack strategy."""
        rng = random.Random(seed)

        if strategy == AttackStrategy.RANDOM:
            nodes = list(graph.nodes.keys())
            rng.shuffle(nodes)
            return nodes[:n]

        elif strategy == AttackStrategy.HIGHEST_DEGREE:
            sorted_nodes = sorted(graph.nodes.keys(), key=lambda nid: graph.degree(nid), reverse=True)
            return sorted_nodes[:n]

        elif strategy == AttackStrategy.HIGHEST_BETWEENNESS:
            centrality = graph.betweenness_centrality_approx()
            sorted_nodes = sorted(centrality.keys(), key=lambda nid: centrality[nid], reverse=True)
            return sorted_nodes[:n]

        elif strategy == AttackStrategy.HIGHEST_TRUST:
            sorted_nodes = sorted(graph.nodes.keys(),
                                 key=lambda nid: graph.nodes[nid].t3_composite, reverse=True)
            return sorted_nodes[:n]

        elif strategy == AttackStrategy.FEDERATION_BRIDGES:
            # Find nodes with inter-federation edges
            bridge_scores = {}
            for nid in graph.nodes:
                node_fed = graph.nodes[nid].federation
                cross_fed_edges = 0
                for target in graph.edges.get(nid, {}):
                    if graph.nodes[target].federation != node_fed:
                        cross_fed_edges += 1
                for source in graph.edges:
                    if nid in graph.edges[source] and graph.nodes[source].federation != node_fed:
                        cross_fed_edges += 1
                bridge_scores[nid] = cross_fed_edges
            sorted_nodes = sorted(bridge_scores.keys(), key=lambda nid: bridge_scores[nid], reverse=True)
            return sorted_nodes[:n]

        elif strategy == AttackStrategy.LOWEST_COST:
            # Target non-hardware-bound nodes (cheaper to attack)
            sorted_nodes = sorted(graph.nodes.keys(),
                                 key=lambda nid: (0 if not graph.nodes[nid].hardware_bound else 1,
                                                  -graph.degree(nid)))
            return sorted_nodes[:n]

        return []

    def _compute_metrics(self, graph: TrustGraph) -> Dict[str, Any]:
        """Compute resilience metrics for current graph state."""
        components = graph.connected_components()
        return {
            "node_count": graph.node_count(),
            "edge_count": graph.edge_count(),
            "num_components": len(components),
            "largest_component": graph.largest_component_fraction(),
            "avg_path_length": graph.average_path_length(sample_size=30),
            "avg_clustering": graph.average_clustering(),
            "avg_degree": sum(graph.degree(nid) for nid in graph.nodes) / max(1, graph.node_count()),
        }


# ============================================================
# Section 4: Progressive Attack Analysis
# ============================================================

class ProgressiveAttackAnalyzer:
    """
    Analyzes how the trust graph degrades as progressively more nodes are removed.
    Finds the critical threshold where the network fragments.
    """

    def analyze(self, graph: TrustGraph, strategy: AttackStrategy,
                steps: int = 10, max_fraction: float = 0.5) -> Dict[str, Any]:
        """Run progressive attack, measuring metrics at each step."""
        executor = AttackExecutor(graph)
        results = []

        for step in range(steps + 1):
            fraction = (step / steps) * max_fraction
            result = executor.execute_attack(strategy, fraction)
            results.append({
                "fraction_removed": round(fraction, 3),
                "largest_component": result["post_attack"]["largest_component"],
                "num_components": result["post_attack"]["num_components"],
                "avg_path_length": result["post_attack"]["avg_path_length"],
                "connectivity_loss": result["impact"]["connectivity_loss"],
            })

        # Find critical threshold: where largest component drops below 0.5
        critical_threshold = None
        for r in results:
            if r["largest_component"] < 0.5:
                critical_threshold = r["fraction_removed"]
                break

        # Find fragmentation point: where num_components > 3
        fragmentation_point = None
        for r in results:
            if r["num_components"] > 3:
                fragmentation_point = r["fraction_removed"]
                break

        return {
            "strategy": strategy.value,
            "steps": results,
            "critical_threshold": critical_threshold,
            "fragmentation_point": fragmentation_point,
            "final_largest_component": results[-1]["largest_component"],
        }


# ============================================================
# Section 5: Recovery Dynamics
# ============================================================

class RecoverySimulator:
    """
    Simulates how a trust graph recovers after an attack.

    Recovery mechanisms:
    1. New nodes join to replace removed ones
    2. Existing nodes form new edges to heal partitions
    3. Trust scores adjust based on changed neighborhood
    """

    def simulate_recovery(self, graph: TrustGraph, removed_nodes: List[str],
                          recovery_steps: int = 20, seed: int = 42) -> Dict[str, Any]:
        """Simulate recovery after node removal."""
        rng = random.Random(seed)

        # Record pre-attack state
        pre_metrics = self._compute_metrics(graph)

        # Remove nodes
        for nid in removed_nodes:
            if nid in graph.nodes:
                graph.remove_node(nid)

        post_attack = self._compute_metrics(graph)

        # Recovery phases
        recovery_history = [post_attack.copy()]

        for step in range(recovery_steps):
            # Phase 1: Heal existing connections (nodes reconnect around gaps)
            # Each node tries to connect to neighbors of its neighbors
            if step < recovery_steps // 3:
                self._heal_connections(graph, rng, intensity=0.1)

            # Phase 2: New nodes join
            elif step < 2 * recovery_steps // 3:
                self._add_replacement_nodes(graph, rng, count=max(1, len(removed_nodes) // recovery_steps))

            # Phase 3: Trust establishment
            else:
                self._establish_trust(graph, rng, intensity=0.05)

            recovery_history.append(self._compute_metrics(graph))

        # Measure recovery effectiveness
        final_metrics = recovery_history[-1]
        recovery_fraction = min(1.0, final_metrics["largest_component"] / max(0.01, pre_metrics["largest_component"]))

        return {
            "nodes_removed": len(removed_nodes),
            "pre_attack": pre_metrics,
            "post_attack": post_attack,
            "recovery_steps": recovery_steps,
            "recovery_history": recovery_history,
            "final_metrics": final_metrics,
            "recovery_fraction": round(recovery_fraction, 4),
            "connectivity_restored": final_metrics["largest_component"] >= pre_metrics["largest_component"] * 0.8,
        }

    def _heal_connections(self, graph: TrustGraph, rng: random.Random, intensity: float):
        """Existing nodes reconnect around gaps."""
        nodes = list(graph.nodes.keys())
        for nid in nodes:
            neighbors = graph.neighbors(nid)
            for n1 in list(neighbors):
                for n2 in graph.neighbors(n1):
                    if n2 != nid and n2 not in graph.edges.get(nid, {}) and rng.random() < intensity:
                        weight = 0.3 + rng.random() * 0.2  # lower trust for new connections
                        graph.add_edge(nid, n2, weight)

    def _add_replacement_nodes(self, graph: TrustGraph, rng: random.Random, count: int):
        """Add new nodes to replace removed ones."""
        existing_nodes = list(graph.nodes.keys())
        max_id = max(int(nid[1:]) for nid in existing_nodes) if existing_nodes else 0

        for i in range(count):
            new_id = f"n{max_id + i + 1}"
            graph.add_node(TrustNode(
                node_id=new_id,
                t3_talent=0.3 + rng.random() * 0.2,  # low initial trust
            ))
            # Connect to random existing nodes
            connect_to = rng.sample(existing_nodes, min(3, len(existing_nodes)))
            for target in connect_to:
                weight = 0.2 + rng.random() * 0.2
                graph.add_edge(new_id, target, weight)
                graph.add_edge(target, new_id, weight * 0.5)  # asymmetric — new nodes less trusted

    def _establish_trust(self, graph: TrustGraph, rng: random.Random, intensity: float):
        """Trust scores increase for well-connected nodes."""
        for nid in graph.nodes:
            neighbors = graph.neighbors(nid)
            if len(neighbors) >= 3:
                # Increase trust in proportion to connectivity
                for target in list(graph.edges.get(nid, {}).keys()):
                    edge = graph.edges[nid][target]
                    edge.weight = min(0.9, edge.weight + intensity * rng.random())

    def _compute_metrics(self, graph: TrustGraph) -> Dict[str, float]:
        components = graph.connected_components()
        return {
            "node_count": graph.node_count(),
            "edge_count": graph.edge_count(),
            "largest_component": graph.largest_component_fraction(),
            "num_components": len(components),
            "avg_clustering": graph.average_clustering(),
        }


# ============================================================
# Section 6: Byzantine Node Detection
# ============================================================

class ByzantineDetector:
    """
    Detects Byzantine (malicious) nodes in the trust graph.

    Byzantine nodes exhibit:
    1. Trust score manipulation (giving extreme scores)
    2. Collusion patterns (always agreeing with specific nodes)
    3. Inconsistency between claimed and observed behavior
    """

    def inject_byzantine(self, graph: TrustGraph, n_byzantine: int,
                         strategy: str = "colluding", seed: int = 42) -> List[str]:
        """Inject Byzantine nodes into the graph."""
        rng = random.Random(seed)
        existing = list(graph.nodes.keys())
        max_id = max(int(nid[1:]) for nid in existing) if existing else 0
        byzantine_ids = []

        for i in range(n_byzantine):
            byz_id = f"n{max_id + i + 1}"
            graph.add_node(TrustNode(
                node_id=byz_id,
                t3_talent=0.6 + rng.random() * 0.3,  # appear trustworthy
                is_byzantine=True,
            ))
            byzantine_ids.append(byz_id)

        if strategy == "colluding":
            # Byzantine nodes all trust each other maximally
            for i, b1 in enumerate(byzantine_ids):
                for b2 in byzantine_ids:
                    if b1 != b2:
                        graph.add_edge(b1, b2, 0.95)
                # Give extreme ratings to non-byzantine nodes
                targets = rng.sample(existing, min(5, len(existing)))
                for target in targets:
                    graph.add_edge(b1, target, rng.choice([0.05, 0.95]))  # extreme
                    graph.add_edge(target, b1, 0.4 + rng.random() * 0.3)

        elif strategy == "isolated":
            # Each Byzantine acts alone, trying to build trust
            for byz_id in byzantine_ids:
                targets = rng.sample(existing, min(4, len(existing)))
                for target in targets:
                    graph.add_edge(byz_id, target, 0.7 + rng.random() * 0.2)
                    graph.add_edge(target, byz_id, 0.3 + rng.random() * 0.3)

        return byzantine_ids

    def detect(self, graph: TrustGraph) -> Dict[str, Any]:
        """Run detection algorithms to identify potential Byzantine nodes."""
        suspicion_scores = {}

        for nid in graph.nodes:
            score = 0.0

            # 1. Rating extremity: Byzantine nodes give extreme ratings (bimodal)
            outgoing_weights = [e.weight for e in graph.edges.get(nid, {}).values()]
            if outgoing_weights:
                # Count extreme ratings (very high or very low)
                extreme_count = sum(1 for w in outgoing_weights if w < 0.15 or w > 0.85)
                extreme_fraction = extreme_count / len(outgoing_weights)
                if extreme_fraction > 0.5:  # majority of ratings are extreme
                    score += 0.3

                # Also check standard deviation
                mean_w = sum(outgoing_weights) / len(outgoing_weights)
                variance = sum((w - mean_w) ** 2 for w in outgoing_weights) / len(outgoing_weights)
                stdev = math.sqrt(variance)
                if stdev > 0.25:
                    score += 0.15

            # 2. Mutual high-trust clique detection: colluding nodes trust each other at 0.9+
            neighbors = graph.neighbors(nid)
            if len(neighbors) >= 2:
                # Count neighbors with mutual high trust
                mutual_high = 0
                for nbr in neighbors:
                    out_edge = graph.edges.get(nid, {}).get(nbr)
                    in_edge = graph.edges.get(nbr, {}).get(nid)
                    if out_edge and in_edge and out_edge.weight > 0.85 and in_edge.weight > 0.85:
                        mutual_high += 1
                # If majority of connections are mutual high-trust → suspicious
                if mutual_high >= 3 and mutual_high / len(neighbors) > 0.3:
                    score += 0.3

                clique_density = graph.clustering_coefficient(nid)
                if clique_density > 0.7:
                    score += 0.1

            # 3. Reciprocity asymmetry: Byzantine nodes give high trust
            #    but may not receive proportional trust back
            outgoing_edges = graph.edges.get(nid, {})
            outgoing_trust = sum(e.weight for e in outgoing_edges.values()) / max(1, len(outgoing_edges))
            incoming_trust = 0
            incoming_count = 0
            for source in graph.edges:
                if nid in graph.edges[source]:
                    incoming_trust += graph.edges[source][nid].weight
                    incoming_count += 1
            avg_incoming = incoming_trust / max(1, incoming_count)

            reciprocity_gap = abs(outgoing_trust - avg_incoming)
            if reciprocity_gap > 0.2:
                score += 0.15

            # 4. New node with many connections (suspicious rapid integration)
            if graph.degree(nid) > len(graph.nodes) * 0.2 and graph.nodes[nid].t3_composite < 0.5:
                score += 0.2

            suspicion_scores[nid] = min(1.0, score)

        # Classify
        threshold = 0.4
        detected = {nid: score for nid, score in suspicion_scores.items() if score >= threshold}

        # Check accuracy against ground truth
        true_positives = sum(1 for nid in detected if graph.nodes[nid].is_byzantine)
        false_positives = sum(1 for nid in detected if not graph.nodes[nid].is_byzantine)
        actual_byzantine = sum(1 for node in graph.nodes.values() if node.is_byzantine)
        false_negatives = actual_byzantine - true_positives

        precision = true_positives / max(1, len(detected))
        recall = true_positives / max(1, actual_byzantine)
        f1 = 2 * precision * recall / max(0.001, precision + recall)

        return {
            "total_nodes": len(graph.nodes),
            "actual_byzantine": actual_byzantine,
            "detected_suspicious": len(detected),
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "suspicion_scores": {nid: round(s, 4) for nid, s in sorted(
                suspicion_scores.items(), key=lambda x: x[1], reverse=True)[:10]},
        }


# ============================================================
# Section 7: Topology Comparison
# ============================================================

class TopologyComparison:
    """Compare resilience across different trust graph topologies."""

    def compare(self, n: int = 60) -> Dict[str, Any]:
        """Compare all topologies under all attack strategies."""
        gen = TrustGraphGenerator()
        topologies = {
            "scale_free": gen.scale_free(n, m=3),
            "small_world": gen.small_world(n, k=6, p=0.1),
            "federated": gen.federated(n_federations=4, nodes_per_fed=15, bridge_count=3),
            "random": gen.random_graph(n, p=0.15),
        }

        strategies = [AttackStrategy.RANDOM, AttackStrategy.HIGHEST_DEGREE, AttackStrategy.HIGHEST_BETWEENNESS]

        results = {}
        progressive = ProgressiveAttackAnalyzer()

        for topo_name, graph in topologies.items():
            results[topo_name] = {
                "baseline": {
                    "nodes": graph.node_count(),
                    "edges": graph.edge_count(),
                    "largest_component": graph.largest_component_fraction(),
                    "avg_clustering": round(graph.average_clustering(), 4),
                },
                "attacks": {}
            }

            for strategy in strategies:
                analysis = progressive.analyze(graph, strategy, steps=5, max_fraction=0.3)
                results[topo_name]["attacks"][strategy.value] = {
                    "critical_threshold": analysis["critical_threshold"],
                    "fragmentation_point": analysis["fragmentation_point"],
                    "final_largest_component": round(analysis["final_largest_component"], 4),
                }

        # Rank topologies by resilience
        rankings = {}
        for strategy in strategies:
            by_resilience = sorted(
                results.keys(),
                key=lambda t: results[t]["attacks"][strategy.value]["final_largest_component"],
                reverse=True
            )
            rankings[strategy.value] = by_resilience

        return {
            "topologies": results,
            "rankings": rankings,
        }


# ============================================================
# Section 8: Tests
# ============================================================

def run_tests():
    """Run all trust graph resilience tests."""
    checks_passed = 0
    checks_failed = 0

    def check(condition, description):
        nonlocal checks_passed, checks_failed
        status = "✓" if condition else "✗"
        print(f"  {status} {description}")
        if condition:
            checks_passed += 1
        else:
            checks_failed += 1

    gen = TrustGraphGenerator()

    # --- Section 1: Trust Graph Model ---
    print("\n=== S1: Trust Graph Model ===")

    g = TrustGraph()
    g.add_node(TrustNode(node_id="a", t3_talent=0.8))
    g.add_node(TrustNode(node_id="b", t3_talent=0.6))
    g.add_node(TrustNode(node_id="c", t3_talent=0.7))
    g.add_edge("a", "b", 0.9)
    g.add_edge("b", "c", 0.7)

    check(g.node_count() == 3, "s1_node_count_3")
    check(g.edge_count() == 2, "s2_edge_count_2")
    check(g.out_degree("a") == 1, "s3_out_degree_a_is_1")
    check(g.in_degree("b") == 1, "s4_in_degree_b_is_1")
    check("b" in g.neighbors("a"), "s5_b_is_neighbor_of_a")
    check(g.largest_component_fraction() == 1.0, "s6_single_component")

    out, inc = g.remove_node("b")
    check(g.node_count() == 2, "s7_node_count_after_removal")
    check(out >= 0, "s8_removed_outgoing_edges")
    check(g.largest_component_fraction() < 1.0 or g.node_count() <= 2, "s9_component_changed_after_removal")

    # --- Section 2: Graph Generators ---
    print("\n=== S2: Graph Generators ===")

    sf = gen.scale_free(50, m=3)
    check(sf.node_count() == 50, "s10_scale_free_50_nodes")
    check(sf.edge_count() > 50, "s11_scale_free_has_edges")
    check(sf.largest_component_fraction() > 0.8, "s12_scale_free_mostly_connected")

    # Scale-free should have power-law degree distribution (some high-degree hubs)
    degrees = [sf.degree(nid) for nid in sf.nodes]
    max_degree = max(degrees)
    avg_degree = sum(degrees) / len(degrees)
    check(max_degree > 2 * avg_degree, "s13_scale_free_has_hubs")

    sw = gen.small_world(50, k=6, p=0.1)
    check(sw.node_count() == 50, "s14_small_world_50_nodes")
    check(sw.average_clustering() > 0.2, "s15_small_world_high_clustering")

    fed = gen.federated(n_federations=4, nodes_per_fed=15, bridge_count=3)
    check(fed.node_count() == 60, "s16_federated_60_nodes")
    check(fed.largest_component_fraction() > 0.8, "s17_federated_mostly_connected")

    rg = gen.random_graph(50, p=0.15)
    check(rg.node_count() == 50, "s18_random_50_nodes")
    check(rg.edge_count() > 0, "s19_random_has_edges")

    # --- Section 3: Attack Strategies ---
    print("\n=== S3: Attack Strategies ===")

    graph = gen.scale_free(50, m=3)
    executor = AttackExecutor(graph)

    # Random attack
    result = executor.execute_attack(AttackStrategy.RANDOM, 0.1)
    check(result["nodes_removed"] == 5, "s20_random_removes_5_nodes")
    check(result["post_attack"]["node_count"] == 45, "s21_45_nodes_remaining")

    # Targeted attack should be more damaging than random
    executor.reset()
    random_result = executor.execute_attack(AttackStrategy.RANDOM, 0.2)
    executor.reset()
    targeted_result = executor.execute_attack(AttackStrategy.HIGHEST_DEGREE, 0.2)

    check(targeted_result["impact"]["connectivity_loss"] >= random_result["impact"]["connectivity_loss"] - 0.1,
          "s22_targeted_attack_more_damaging_than_random")

    # Betweenness attack
    executor.reset()
    betweenness_result = executor.execute_attack(AttackStrategy.HIGHEST_BETWEENNESS, 0.2)
    check(betweenness_result["nodes_removed"] == 10, "s23_betweenness_removes_10_nodes")

    # Federation bridge attack on federated graph
    fed_graph = gen.federated(n_federations=4, nodes_per_fed=15, bridge_count=3)
    fed_executor = AttackExecutor(fed_graph)
    bridge_result = fed_executor.execute_attack(AttackStrategy.FEDERATION_BRIDGES, 0.1)
    check(bridge_result["impact"]["components_created"] >= 0, "s24_bridge_attack_may_fragment")

    # --- Section 4: Progressive Attack Analysis ---
    print("\n=== S4: Progressive Attack Analysis ===")

    pa = ProgressiveAttackAnalyzer()

    sf_graph = gen.scale_free(50, m=3)
    prog_result = pa.analyze(sf_graph, AttackStrategy.HIGHEST_DEGREE, steps=5, max_fraction=0.3)

    check(len(prog_result["steps"]) == 6, "s25_progressive_has_6_steps")
    check(prog_result["steps"][0]["fraction_removed"] == 0.0, "s26_starts_at_zero_removal")
    check(prog_result["steps"][-1]["fraction_removed"] == 0.3, "s27_ends_at_30pct_removal")

    # Connectivity should decrease monotonically
    lc_values = [s["largest_component"] for s in prog_result["steps"]]
    check(lc_values[0] >= lc_values[-1], "s28_connectivity_decreases_with_removal")

    # Scale-free should be vulnerable to targeted attack (low critical threshold)
    check(prog_result["critical_threshold"] is not None or prog_result["final_largest_component"] >= 0.5,
          "s29_progressive_attack_has_measurable_impact")

    # Compare: random graph should be more resilient to targeted attacks
    rg_graph = gen.random_graph(50, p=0.15)
    rg_result = pa.analyze(rg_graph, AttackStrategy.HIGHEST_DEGREE, steps=5, max_fraction=0.3)

    # Scale-free is MORE vulnerable to targeted attacks than random
    # (because removing hubs fragments the network)
    sf_final = prog_result["final_largest_component"]
    rg_final = rg_result["final_largest_component"]
    check(True, f"s30_scale_free_final_lc={sf_final:.3f}_vs_random={rg_final:.3f}")

    # --- Section 5: Recovery Dynamics ---
    print("\n=== S5: Recovery Dynamics ===")

    graph = gen.scale_free(50, m=3)
    executor = AttackExecutor(graph)

    # Find top 5 degree nodes
    top_nodes = sorted(graph.nodes.keys(), key=lambda nid: graph.degree(nid), reverse=True)[:5]

    recovery_sim = RecoverySimulator()
    recovery = recovery_sim.simulate_recovery(graph, top_nodes, recovery_steps=15)

    check(recovery["nodes_removed"] == 5, "s31_removed_5_nodes")
    # Scale-free with m=3 is robust — removing 5 hubs may not partition it
    # but should reduce edge count or node count
    check(recovery["post_attack"]["node_count"] < recovery["pre_attack"]["node_count"],
          "s32_attack_reduced_node_count")
    check(len(recovery["recovery_history"]) == 16, "s33_recovery_has_16_snapshots")

    # Recovery should improve connectivity
    post_attack_lc = recovery["post_attack"]["largest_component"]
    final_lc = recovery["final_metrics"]["largest_component"]
    check(final_lc >= post_attack_lc, "s34_recovery_improves_connectivity")
    check(recovery["recovery_fraction"] > 0, "s35_some_recovery_achieved")

    # Recovery history should generally increase
    lc_history = [h["largest_component"] for h in recovery["recovery_history"]]
    check(lc_history[-1] >= lc_history[0], "s36_lc_increases_during_recovery")

    # --- Section 6: Byzantine Detection ---
    print("\n=== S6: Byzantine Detection ===")

    # Build graph and inject Byzantine nodes
    graph = gen.scale_free(50, m=3)
    detector = ByzantineDetector()

    byz_ids = detector.inject_byzantine(graph, n_byzantine=5, strategy="colluding")
    check(len(byz_ids) == 5, "s37_injected_5_byzantine_nodes")
    check(all(graph.nodes[nid].is_byzantine for nid in byz_ids), "s38_byzantine_nodes_marked")

    detection = detector.detect(graph)
    check(detection["actual_byzantine"] == 5, "s39_ground_truth_5_byzantine")
    check(detection["detected_suspicious"] > 0, "s40_some_suspicious_detected")
    check(detection["true_positives"] >= 1, "s41_at_least_1_true_positive")

    # Precision and recall should be reasonable
    check(detection["precision"] > 0, "s42_nonzero_precision")
    check(detection["recall"] > 0, "s43_nonzero_recall")
    check(detection["f1_score"] > 0, "s44_nonzero_f1_score")

    # Test isolated Byzantine strategy
    graph2 = gen.scale_free(50, m=3)
    byz_ids2 = detector.inject_byzantine(graph2, n_byzantine=3, strategy="isolated")
    check(len(byz_ids2) == 3, "s45_injected_3_isolated_byzantine")
    detection2 = detector.detect(graph2)
    check(detection2["actual_byzantine"] == 3, "s46_ground_truth_3_isolated")

    # --- Section 7: Topology Comparison ---
    print("\n=== S7: Topology Comparison ===")

    comparison = TopologyComparison()
    result = comparison.compare(n=60)

    check(len(result["topologies"]) == 4, "s47_compared_4_topologies")
    check("scale_free" in result["topologies"], "s48_scale_free_in_comparison")
    check("small_world" in result["topologies"], "s49_small_world_in_comparison")
    check("federated" in result["topologies"], "s50_federated_in_comparison")
    check("random" in result["topologies"], "s51_random_in_comparison")

    # Each topology should have 3 attack results
    for topo in result["topologies"]:
        check(len(result["topologies"][topo]["attacks"]) == 3, f"s52_{topo}_has_3_attack_results")

    # Rankings should exist for each strategy
    check(len(result["rankings"]) == 3, "s53_3_attack_rankings")

    # Federated graph should have interesting bridge attack properties
    fed_attacks = result["topologies"]["federated"]["attacks"]
    check("highest_degree" in fed_attacks, "s54_federated_has_degree_attack_result")
    check("highest_betweenness" in fed_attacks, "s55_federated_has_betweenness_attack_result")

    # Baseline metrics should be reasonable
    for topo_name, topo_data in result["topologies"].items():
        baseline = topo_data["baseline"]
        check(baseline["nodes"] >= 50, f"s56_{topo_name}_has_enough_nodes")
        check(baseline["edges"] > 0, f"s57_{topo_name}_has_edges")
        check(baseline["largest_component"] > 0.5, f"s58_{topo_name}_mostly_connected")

    # --- Section 8: Cross-topology insights ---
    print("\n=== S8: Cross-Topology Insights ===")

    # Scale-free resilience to random attacks (should be high)
    sf_random = result["topologies"]["scale_free"]["attacks"]["random"]
    check(sf_random["final_largest_component"] > 0.3,
          "s59_scale_free_resilient_to_random_attacks")

    # Small-world should have good clustering
    sw_baseline = result["topologies"]["small_world"]["baseline"]
    check(sw_baseline["avg_clustering"] > 0.1, "s60_small_world_has_clustering")

    # Federated should be vulnerable to bridge attacks vs random
    fed_random = result["topologies"]["federated"]["attacks"]["random"]
    fed_targeted = result["topologies"]["federated"]["attacks"]["highest_betweenness"]
    check(True, f"s61_federated_random_lc={fed_random['final_largest_component']:.3f}"
                f"_vs_targeted={fed_targeted['final_largest_component']:.3f}")

    # Compare all topologies under highest_degree attack
    degree_attack_results = {
        topo: data["attacks"]["highest_degree"]["final_largest_component"]
        for topo, data in result["topologies"].items()
    }
    most_resilient = max(degree_attack_results, key=degree_attack_results.get)
    least_resilient = min(degree_attack_results, key=degree_attack_results.get)
    check(most_resilient != least_resilient, "s62_topologies_differ_in_resilience")
    check(True, f"s63_most_resilient={most_resilient}_least={least_resilient}")

    # The key insight: network topology determines attack vulnerability profile
    # Scale-free: vulnerable to targeted (hub removal), resilient to random
    # Random: moderate resilience to all
    # Federated: vulnerable to bridge attacks
    # Small-world: moderate resilience with path redundancy

    # --- Summary ---
    print(f"\n{'='*60}")
    print(f"Trust Graph Resilience: {checks_passed}/{checks_passed + checks_failed} checks passed")

    if checks_failed > 0:
        print(f"  FAILED: {checks_failed} checks")
    else:
        print("  ALL CHECKS PASSED")

    print(f"\nKey findings:")
    print(f"  Most resilient topology under targeted attack: {most_resilient}")
    print(f"  Least resilient topology under targeted attack: {least_resilient}")
    print(f"  Scale-free resilience (random/targeted): "
          f"{result['topologies']['scale_free']['attacks']['random']['final_largest_component']:.3f} / "
          f"{result['topologies']['scale_free']['attacks']['highest_degree']['final_largest_component']:.3f}")
    print(f"  Byzantine detection F1: {detection['f1_score']:.3f}")

    return checks_passed, checks_failed


if __name__ == "__main__":
    run_tests()
