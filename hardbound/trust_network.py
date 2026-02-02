"""
Trust Network Analysis and Visualization

Track CG: Graph-based trust relationship analysis.

Key concepts:
1. Network Graph: Federations as nodes, trust as edges
2. Centrality Analysis: Identify influential federations
3. Cluster Detection: Find tightly-connected groups
4. Path Analysis: Trust paths between federations
5. Anomaly Detection: Unusual network patterns
6. Export Formats: Graph data for visualization tools

This provides the analytical layer for understanding the trust
network structure and identifying potential issues or opportunities.
"""

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from collections import defaultdict
import json
import math

from hardbound.multi_federation import MultiFederationRegistry, FederationRelationship


@dataclass
class NetworkNode:
    """A node in the trust network (federation)."""
    federation_id: str
    name: str
    in_degree: int = 0  # Number of incoming trust relationships
    out_degree: int = 0  # Number of outgoing trust relationships
    trust_sum_in: float = 0.0  # Sum of incoming trust scores
    trust_sum_out: float = 0.0  # Sum of outgoing trust scores
    betweenness_centrality: float = 0.0  # How often on shortest paths
    cluster_id: Optional[str] = None


@dataclass
class NetworkEdge:
    """An edge in the trust network (trust relationship)."""
    source_id: str
    target_id: str
    trust_score: float
    relationship_type: FederationRelationship
    bidirectional: bool = False
    reverse_trust: float = 0.0


@dataclass
class TrustPath:
    """A path of trust through the network."""
    path: List[str]  # Federation IDs in order
    total_trust: float  # Product of trust scores along path
    hops: int
    weakest_link: float  # Minimum trust on path


@dataclass
class NetworkCluster:
    """A cluster of tightly-connected federations."""
    cluster_id: str
    members: List[str]
    internal_edges: int
    external_edges: int
    avg_internal_trust: float
    cohesion: float  # internal_edges / possible_internal_edges


@dataclass
class NetworkAnomaly:
    """An unusual pattern detected in the network."""
    anomaly_type: str
    severity: float  # 0.0 to 1.0
    description: str
    affected_nodes: List[str]
    details: Dict = field(default_factory=dict)


class TrustNetworkAnalyzer:
    """
    Analyze trust network structure.

    Track CG: Graph-based trust relationship analysis.
    """

    def __init__(
        self,
        registry: MultiFederationRegistry,
    ):
        """
        Initialize analyzer.

        Args:
            registry: Multi-federation registry
        """
        self.registry = registry
        self._nodes: Dict[str, NetworkNode] = {}
        self._edges: List[NetworkEdge] = []
        self._adjacency: Dict[str, Set[str]] = defaultdict(set)  # Outgoing
        self._reverse_adjacency: Dict[str, Set[str]] = defaultdict(set)  # Incoming

    def build_network(self) -> Tuple[Dict[str, NetworkNode], List[NetworkEdge]]:
        """
        Build the trust network from registry data.

        Returns:
            Tuple of (nodes dict, edges list)
        """
        self._nodes = {}
        self._edges = []
        self._adjacency = defaultdict(set)
        self._reverse_adjacency = defaultdict(set)

        relationships = self.registry.get_all_relationships()

        # Create edge lookup for bidirectional check
        edge_lookup: Dict[Tuple[str, str], float] = {}

        # Build edges and collect node info
        for rel in relationships:
            edge_lookup[(rel.source_federation_id, rel.target_federation_id)] = rel.trust_score

            # Check if bidirectional
            reverse_key = (rel.target_federation_id, rel.source_federation_id)
            bidirectional = reverse_key in edge_lookup
            reverse_trust = edge_lookup.get(reverse_key, 0.0)

            edge = NetworkEdge(
                source_id=rel.source_federation_id,
                target_id=rel.target_federation_id,
                trust_score=rel.trust_score,
                relationship_type=rel.relationship,
                bidirectional=bidirectional,
                reverse_trust=reverse_trust,
            )
            self._edges.append(edge)

            # Build adjacency
            self._adjacency[rel.source_federation_id].add(rel.target_federation_id)
            self._reverse_adjacency[rel.target_federation_id].add(rel.source_federation_id)

            # Ensure nodes exist
            if rel.source_federation_id not in self._nodes:
                self._nodes[rel.source_federation_id] = NetworkNode(
                    federation_id=rel.source_federation_id,
                    name=rel.source_federation_id,  # Would get from registry
                )
            if rel.target_federation_id not in self._nodes:
                self._nodes[rel.target_federation_id] = NetworkNode(
                    federation_id=rel.target_federation_id,
                    name=rel.target_federation_id,
                )

        # Calculate node statistics
        for node_id, node in self._nodes.items():
            node.out_degree = len(self._adjacency[node_id])
            node.in_degree = len(self._reverse_adjacency[node_id])

            # Sum trust scores
            for edge in self._edges:
                if edge.source_id == node_id:
                    node.trust_sum_out += edge.trust_score
                if edge.target_id == node_id:
                    node.trust_sum_in += edge.trust_score

        return self._nodes, self._edges

    def find_trust_path(
        self,
        source_id: str,
        target_id: str,
        max_hops: int = 5,
    ) -> Optional[TrustPath]:
        """
        Find the best trust path between two federations.

        Uses BFS to find shortest path, then calculates trust product.

        Args:
            source_id: Starting federation
            target_id: Destination federation
            max_hops: Maximum path length

        Returns:
            TrustPath if path exists, None otherwise
        """
        if source_id == target_id:
            return TrustPath(path=[source_id], total_trust=1.0, hops=0, weakest_link=1.0)

        # BFS to find path
        visited = {source_id}
        queue = [(source_id, [source_id])]
        edge_trust: Dict[Tuple[str, str], float] = {
            (e.source_id, e.target_id): e.trust_score for e in self._edges
        }

        while queue:
            current, path = queue.pop(0)

            if len(path) > max_hops:
                continue

            for neighbor in self._adjacency[current]:
                if neighbor == target_id:
                    # Found path
                    full_path = path + [neighbor]
                    trusts = []
                    for i in range(len(full_path) - 1):
                        trust = edge_trust.get((full_path[i], full_path[i+1]), 0.0)
                        trusts.append(trust)

                    total_trust = 1.0
                    for t in trusts:
                        total_trust *= t

                    return TrustPath(
                        path=full_path,
                        total_trust=total_trust,
                        hops=len(trusts),
                        weakest_link=min(trusts) if trusts else 0.0,
                    )

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def find_all_paths(
        self,
        source_id: str,
        target_id: str,
        max_hops: int = 4,
    ) -> List[TrustPath]:
        """
        Find all trust paths between two federations.

        Args:
            source_id: Starting federation
            target_id: Destination federation
            max_hops: Maximum path length

        Returns:
            List of TrustPath objects
        """
        paths = []
        edge_trust: Dict[Tuple[str, str], float] = {
            (e.source_id, e.target_id): e.trust_score for e in self._edges
        }

        def dfs(current: str, path: List[str], visited: Set[str]):
            if len(path) > max_hops + 1:
                return

            if current == target_id:
                trusts = []
                for i in range(len(path) - 1):
                    trust = edge_trust.get((path[i], path[i+1]), 0.0)
                    trusts.append(trust)

                total_trust = 1.0
                for t in trusts:
                    total_trust *= t

                paths.append(TrustPath(
                    path=path.copy(),
                    total_trust=total_trust,
                    hops=len(trusts),
                    weakest_link=min(trusts) if trusts else 0.0,
                ))
                return

            for neighbor in self._adjacency[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    path.append(neighbor)
                    dfs(neighbor, path, visited)
                    path.pop()
                    visited.remove(neighbor)

        dfs(source_id, [source_id], {source_id})
        return sorted(paths, key=lambda p: -p.total_trust)

    def detect_clusters(self, min_cluster_size: int = 2) -> List[NetworkCluster]:
        """
        Detect clusters of tightly-connected federations.

        Uses connected components analysis.

        Args:
            min_cluster_size: Minimum members in a cluster

        Returns:
            List of NetworkCluster objects
        """
        # Find connected components (treating edges as undirected)
        visited = set()
        clusters = []

        def bfs_component(start: str) -> Set[str]:
            component = set()
            queue = [start]
            while queue:
                node = queue.pop(0)
                if node in component:
                    continue
                component.add(node)
                # Add both directions
                for neighbor in self._adjacency[node]:
                    if neighbor not in component:
                        queue.append(neighbor)
                for neighbor in self._reverse_adjacency[node]:
                    if neighbor not in component:
                        queue.append(neighbor)
            return component

        for node_id in self._nodes:
            if node_id not in visited:
                component = bfs_component(node_id)
                visited.update(component)

                if len(component) >= min_cluster_size:
                    # Calculate cluster metrics
                    members = list(component)
                    internal_edges = 0
                    external_edges = 0
                    trust_sum = 0.0

                    for edge in self._edges:
                        if edge.source_id in component:
                            if edge.target_id in component:
                                internal_edges += 1
                                trust_sum += edge.trust_score
                            else:
                                external_edges += 1

                    possible_internal = len(members) * (len(members) - 1)
                    cohesion = internal_edges / possible_internal if possible_internal > 0 else 0.0
                    avg_internal = trust_sum / internal_edges if internal_edges > 0 else 0.0

                    cluster = NetworkCluster(
                        cluster_id=f"cluster:{len(clusters)}",
                        members=members,
                        internal_edges=internal_edges,
                        external_edges=external_edges,
                        avg_internal_trust=avg_internal,
                        cohesion=cohesion,
                    )
                    clusters.append(cluster)

                    # Assign cluster to nodes
                    for member in members:
                        self._nodes[member].cluster_id = cluster.cluster_id

        return clusters

    def detect_anomalies(self) -> List[NetworkAnomaly]:
        """
        Detect unusual patterns in the network.

        Checks for:
        - Isolated nodes (no connections)
        - Trust asymmetry (A trusts B much more than B trusts A)
        - Cliques (fully connected small groups)
        - Star patterns (one node with many connections)

        Returns:
            List of NetworkAnomaly objects
        """
        anomalies = []

        # 1. Isolated nodes (only outgoing, no incoming)
        for node_id, node in self._nodes.items():
            if node.in_degree == 0 and node.out_degree > 0:
                anomalies.append(NetworkAnomaly(
                    anomaly_type="trust_giver_no_receiver",
                    severity=0.5,
                    description=f"Federation {node_id} gives trust but receives none",
                    affected_nodes=[node_id],
                ))
            elif node.in_degree > 0 and node.out_degree == 0:
                anomalies.append(NetworkAnomaly(
                    anomaly_type="trust_receiver_no_giver",
                    severity=0.3,
                    description=f"Federation {node_id} receives trust but gives none",
                    affected_nodes=[node_id],
                ))

        # 2. Trust asymmetry
        edge_lookup: Dict[Tuple[str, str], float] = {
            (e.source_id, e.target_id): e.trust_score for e in self._edges
        }

        checked_pairs = set()
        for edge in self._edges:
            pair = tuple(sorted([edge.source_id, edge.target_id]))
            if pair in checked_pairs:
                continue
            checked_pairs.add(pair)

            forward_trust = edge.trust_score
            reverse_trust = edge_lookup.get((edge.target_id, edge.source_id), 0.0)

            if reverse_trust > 0:
                ratio = max(forward_trust, reverse_trust) / min(forward_trust, reverse_trust)
                if ratio > 3.0:  # Significant asymmetry
                    anomalies.append(NetworkAnomaly(
                        anomaly_type="trust_asymmetry",
                        severity=min(1.0, (ratio - 3.0) / 7.0 + 0.3),
                        description=f"Trust asymmetry between {edge.source_id} and {edge.target_id}",
                        affected_nodes=[edge.source_id, edge.target_id],
                        details={"forward": forward_trust, "reverse": reverse_trust, "ratio": ratio},
                    ))

        # 3. Star patterns (high degree centrality)
        max_degree = max((n.in_degree + n.out_degree for n in self._nodes.values()), default=0)
        avg_degree = sum(n.in_degree + n.out_degree for n in self._nodes.values()) / max(1, len(self._nodes))

        for node_id, node in self._nodes.items():
            total_degree = node.in_degree + node.out_degree
            if total_degree > 2 * avg_degree and total_degree >= 5:
                anomalies.append(NetworkAnomaly(
                    anomaly_type="high_centrality",
                    severity=min(1.0, total_degree / max_degree),
                    description=f"Federation {node_id} has unusually high connectivity",
                    affected_nodes=[node_id],
                    details={"degree": total_degree, "avg_degree": avg_degree},
                ))

        return anomalies

    def calculate_centrality(self) -> Dict[str, float]:
        """
        Calculate degree centrality for all nodes.

        Returns:
            Dict mapping federation_id to centrality score
        """
        centrality = {}
        max_possible = max(1, 2 * (len(self._nodes) - 1))

        for node_id, node in self._nodes.items():
            centrality[node_id] = (node.in_degree + node.out_degree) / max_possible

        return centrality

    def get_most_trusted(self, limit: int = 10) -> List[Tuple[str, float]]:
        """
        Get the most trusted federations by incoming trust sum.

        Returns:
            List of (federation_id, trust_sum) tuples
        """
        sorted_nodes = sorted(
            self._nodes.items(),
            key=lambda x: x[1].trust_sum_in,
            reverse=True
        )
        return [(n[0], n[1].trust_sum_in) for n in sorted_nodes[:limit]]

    def get_most_trusting(self, limit: int = 10) -> List[Tuple[str, float]]:
        """
        Get federations that give the most trust.

        Returns:
            List of (federation_id, trust_sum) tuples
        """
        sorted_nodes = sorted(
            self._nodes.items(),
            key=lambda x: x[1].trust_sum_out,
            reverse=True
        )
        return [(n[0], n[1].trust_sum_out) for n in sorted_nodes[:limit]]

    def export_graph(self) -> Dict:
        """
        Export the network as a graph data structure.

        Returns:
            Dict with nodes and edges suitable for visualization
        """
        return {
            "nodes": [
                {
                    "id": node.federation_id,
                    "name": node.name,
                    "in_degree": node.in_degree,
                    "out_degree": node.out_degree,
                    "trust_sum_in": node.trust_sum_in,
                    "trust_sum_out": node.trust_sum_out,
                    "cluster_id": node.cluster_id,
                }
                for node in self._nodes.values()
            ],
            "edges": [
                {
                    "source": edge.source_id,
                    "target": edge.target_id,
                    "trust_score": edge.trust_score,
                    "relationship": edge.relationship_type.value,
                    "bidirectional": edge.bidirectional,
                }
                for edge in self._edges
            ],
            "metadata": {
                "node_count": len(self._nodes),
                "edge_count": len(self._edges),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }

    def get_network_summary(self) -> Dict:
        """
        Get a summary of network statistics.

        Returns:
            Dict with network statistics
        """
        if not self._nodes:
            return {
                "node_count": 0,
                "edge_count": 0,
                "avg_degree": 0,
                "density": 0,
            }

        total_degree = sum(n.in_degree + n.out_degree for n in self._nodes.values())
        avg_degree = total_degree / len(self._nodes)
        max_possible_edges = len(self._nodes) * (len(self._nodes) - 1)
        density = len(self._edges) / max_possible_edges if max_possible_edges > 0 else 0

        return {
            "node_count": len(self._nodes),
            "edge_count": len(self._edges),
            "avg_degree": avg_degree,
            "density": density,
            "total_trust": sum(e.trust_score for e in self._edges),
            "avg_trust": sum(e.trust_score for e in self._edges) / max(1, len(self._edges)),
        }


# Self-test
if __name__ == "__main__":
    print("=" * 60)
    print("Trust Network Analyzer - Self Test")
    print("=" * 60)

    import tempfile

    tmp_dir = Path(tempfile.mkdtemp())

    # Create registry
    registry = MultiFederationRegistry(db_path=tmp_dir / "registry.db")

    # Create test federations
    for name in ["alpha", "beta", "gamma", "delta", "epsilon"]:
        registry.register_federation(f"fed:{name}", name.title())

    # Create trust relationships
    registry.establish_trust("fed:alpha", "fed:beta", FederationRelationship.PEER, 0.7)
    registry.establish_trust("fed:beta", "fed:alpha", FederationRelationship.PEER, 0.6)
    registry.establish_trust("fed:beta", "fed:gamma", FederationRelationship.TRUSTED, 0.8)
    registry.establish_trust("fed:gamma", "fed:delta", FederationRelationship.PEER, 0.5)
    registry.establish_trust("fed:alpha", "fed:epsilon", FederationRelationship.TRUSTED, 0.9)

    # Analyze network
    analyzer = TrustNetworkAnalyzer(registry)
    nodes, edges = analyzer.build_network()

    print(f"\n1. Network built:")
    print(f"   Nodes: {len(nodes)}")
    print(f"   Edges: {len(edges)}")

    print("\n2. Find trust path alpha -> delta:")
    path = analyzer.find_trust_path("fed:alpha", "fed:delta")
    if path:
        print(f"   Path: {' -> '.join(path.path)}")
        print(f"   Total trust: {path.total_trust:.3f}")
        print(f"   Hops: {path.hops}")

    print("\n3. Detect clusters:")
    clusters = analyzer.detect_clusters()
    print(f"   Clusters found: {len(clusters)}")
    for cluster in clusters:
        print(f"   - {cluster.cluster_id}: {cluster.members}")

    print("\n4. Detect anomalies:")
    anomalies = analyzer.detect_anomalies()
    print(f"   Anomalies found: {len(anomalies)}")
    for anomaly in anomalies:
        print(f"   - {anomaly.anomaly_type}: {anomaly.description}")

    print("\n5. Most trusted federations:")
    most_trusted = analyzer.get_most_trusted(3)
    for fed_id, trust_sum in most_trusted:
        print(f"   - {fed_id}: {trust_sum:.2f}")

    print("\n6. Network summary:")
    summary = analyzer.get_network_summary()
    for key, value in summary.items():
        print(f"   {key}: {value:.2f}" if isinstance(value, float) else f"   {key}: {value}")

    print("\n✓ Self-test complete!")
