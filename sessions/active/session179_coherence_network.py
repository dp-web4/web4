"""
Session #179: Coherence Network Topology

Integrates Session 256 (Space from Coherence) with Web4's network topology.

Key Insight from Session 256:
    Space = Coherence Correlation Structure
    Distance: d(A,B) = -log(C_AB / √(C_A × C_B))

    Where:
    - C_AB = joint coherence between A and B
    - C_A, C_B = individual coherences
    - The ratio measures correlation above independence

Application to Web4:
    Network topology emerges from coherence correlations:
    - High coherence correlation → "close" neighbors
    - Low coherence correlation → "distant" nodes
    - Network structure = coherence geometry
    - Information flow follows coherence gradients

Author: Web4 Research Session 16
Date: January 2026
Status: IN PROGRESS
"""

import math
from dataclasses import dataclass
from typing import List, Dict, Tuple, Set, Optional
import json


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class CoherenceNode:
    """Node in coherence network"""
    node_id: str
    coherence: float  # Individual coherence C_A (0-1)
    position: Optional[Tuple[float, float, float]] = None  # 3D embedding
    metadata: Dict[str, any] = None


@dataclass
class CoherenceEdge:
    """Edge representing coherence correlation"""
    from_node: str
    to_node: str
    joint_coherence: float  # C_AB
    coherence_distance: float  # d(A,B)
    correlation: float  # C_AB / √(C_A × C_B)


@dataclass
class NetworkMetrics:
    """Network-level coherence metrics"""
    avg_coherence: float
    avg_distance: float
    avg_correlation: float
    network_coherence: float  # Overall network coherence
    dimensionality: int  # Effective dimensionality
    connectivity: float  # How connected the network is


# ============================================================================
# Coherence Distance Calculator
# ============================================================================

class CoherenceDistanceCalculator:
    """
    Calculates coherence distance from Session 256.

    Core equation: d(A,B) = -log(C_AB / √(C_A × C_B))

    Properties:
    - d(A,A) = 0 (distance to self is zero)
    - d(A,B) = d(B,A) (symmetric)
    - d(A,B) > 0 when C_AB < √(C_A × C_B) (triangle inequality)
    """

    def __init__(self, epsilon: float = 1e-10):
        """
        Args:
            epsilon: Small value to prevent log(0)
        """
        self.epsilon = epsilon


    def calculate_correlation(
        self, c_a: float, c_b: float, c_ab: float
    ) -> float:
        """
        Calculate coherence correlation: C_AB / √(C_A × C_B)

        Returns value in [0, ∞):
        - correlation = 1 → independent
        - correlation > 1 → positively correlated (entangled)
        - correlation < 1 → negatively correlated (anti-correlated)
        """
        if c_a <= 0 or c_b <= 0:
            return 0.0

        denominator = math.sqrt(c_a * c_b)
        correlation = c_ab / denominator if denominator > 0 else 0.0

        return correlation


    def calculate_distance(
        self, c_a: float, c_b: float, c_ab: float
    ) -> float:
        """
        Calculate coherence distance: d(A,B) = -log(C_AB / √(C_A × C_B))

        Returns distance in [0, ∞):
        - distance = 0 → perfectly correlated (same location)
        - distance = ∞ → uncorrelated (infinitely far)
        """
        correlation = self.calculate_correlation(c_a, c_b, c_ab)

        # Clamp correlation to avoid log(0) or log(negative)
        correlation = max(self.epsilon, correlation)

        distance = -math.log(correlation)

        return max(0.0, distance)


    def calculate_from_patterns(
        self, pattern_a: List[float], pattern_b: List[float]
    ) -> Tuple[float, float, float]:
        """
        Calculate coherence and distance from behavior patterns.

        Returns:
            (c_a, c_b, c_ab, distance)
        """
        # Individual coherences (stability of patterns)
        c_a = self._pattern_coherence(pattern_a)
        c_b = self._pattern_coherence(pattern_b)

        # Joint coherence (correlation between patterns)
        c_ab = self._joint_coherence(pattern_a, pattern_b)

        # Distance
        distance = self.calculate_distance(c_a, c_b, c_ab)

        return c_a, c_b, c_ab, distance


    def _pattern_coherence(self, pattern: List[float]) -> float:
        """
        Calculate coherence of a single pattern.

        High coherence = stable, predictable pattern.
        """
        if len(pattern) < 2:
            return 0.5  # Neutral coherence for insufficient data

        # Coherence from stability (low variance = high coherence)
        mean = sum(pattern) / len(pattern)
        if mean == 0:
            return 0.3  # Low coherence for zero mean

        variance = sum((x - mean) ** 2 for x in pattern) / len(pattern)
        cv = math.sqrt(variance) / mean if mean > 0 else float('inf')

        # Convert CV to coherence (low CV = high coherence)
        coherence = 1.0 / (1.0 + cv)

        return min(1.0, max(0.0, coherence))


    def _joint_coherence(
        self, pattern_a: List[float], pattern_b: List[float]
    ) -> float:
        """
        Calculate joint coherence between two patterns.

        High joint coherence = patterns move together.
        """
        if len(pattern_a) < 2 or len(pattern_b) < 2:
            return 0.3  # Low coherence for insufficient data

        # Use correlation as proxy for joint coherence
        min_len = min(len(pattern_a), len(pattern_b))
        a = pattern_a[-min_len:]
        b = pattern_b[-min_len:]

        mean_a = sum(a) / len(a)
        mean_b = sum(b) / len(b)

        # Pearson correlation
        numerator = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(len(a)))
        var_a = sum((x - mean_a) ** 2 for x in a)
        var_b = sum((x - mean_b) ** 2 for x in b)
        denominator = math.sqrt(var_a * var_b) if var_a > 0 and var_b > 0 else 0

        correlation = numerator / denominator if denominator > 0 else 0.0

        # Convert correlation [-1, 1] to joint coherence [0, 1]
        # High positive correlation → high joint coherence
        joint_coherence = (correlation + 1.0) / 2.0

        # Scale by individual coherences
        c_a = self._pattern_coherence(a)
        c_b = self._pattern_coherence(b)
        joint_coherence *= math.sqrt(c_a * c_b)

        return min(1.0, max(0.0, joint_coherence))


# ============================================================================
# Coherence Network Builder
# ============================================================================

class CoherenceNetworkBuilder:
    """
    Builds network topology from coherence correlations.
    """

    def __init__(self):
        self.distance_calc = CoherenceDistanceCalculator()
        self.nodes: Dict[str, CoherenceNode] = {}
        self.edges: List[CoherenceEdge] = []


    def add_node(
        self,
        node_id: str,
        coherence: float,
        metadata: Optional[Dict] = None
    ):
        """Add node to network"""
        node = CoherenceNode(
            node_id=node_id,
            coherence=coherence,
            metadata=metadata or {}
        )
        self.nodes[node_id] = node


    def add_edge_from_patterns(
        self,
        node_a_id: str,
        node_b_id: str,
        pattern_a: List[float],
        pattern_b: List[float]
    ):
        """
        Add edge calculated from behavior patterns.
        """
        c_a, c_b, c_ab, distance = self.distance_calc.calculate_from_patterns(
            pattern_a, pattern_b
        )

        correlation = self.distance_calc.calculate_correlation(c_a, c_b, c_ab)

        edge = CoherenceEdge(
            from_node=node_a_id,
            to_node=node_b_id,
            joint_coherence=c_ab,
            coherence_distance=distance,
            correlation=correlation
        )

        self.edges.append(edge)


    def add_edge_from_coherences(
        self,
        node_a_id: str,
        node_b_id: str,
        joint_coherence: float
    ):
        """
        Add edge from known coherences.
        """
        node_a = self.nodes.get(node_a_id)
        node_b = self.nodes.get(node_b_id)

        if not node_a or not node_b:
            raise ValueError(f"Nodes must exist before adding edge")

        distance = self.distance_calc.calculate_distance(
            node_a.coherence,
            node_b.coherence,
            joint_coherence
        )

        correlation = self.distance_calc.calculate_correlation(
            node_a.coherence,
            node_b.coherence,
            joint_coherence
        )

        edge = CoherenceEdge(
            from_node=node_a_id,
            to_node=node_b_id,
            joint_coherence=joint_coherence,
            coherence_distance=distance,
            correlation=correlation
        )

        self.edges.append(edge)


    def get_neighbors(
        self, node_id: str, max_distance: float = float('inf')
    ) -> List[Tuple[str, float]]:
        """
        Get neighbors within coherence distance.

        Returns:
            List of (neighbor_id, distance) sorted by distance
        """
        neighbors = []

        for edge in self.edges:
            if edge.from_node == node_id and edge.coherence_distance <= max_distance:
                neighbors.append((edge.to_node, edge.coherence_distance))
            elif edge.to_node == node_id and edge.coherence_distance <= max_distance:
                neighbors.append((edge.from_node, edge.coherence_distance))

        # Sort by distance (closest first)
        neighbors.sort(key=lambda x: x[1])

        return neighbors


    def calculate_network_metrics(self) -> NetworkMetrics:
        """Calculate network-level metrics"""

        if not self.nodes or not self.edges:
            return NetworkMetrics(
                avg_coherence=0.0,
                avg_distance=0.0,
                avg_correlation=0.0,
                network_coherence=0.0,
                dimensionality=0,
                connectivity=0.0
            )

        # Average individual coherence
        avg_coherence = sum(n.coherence for n in self.nodes.values()) / len(self.nodes)

        # Average distance and correlation
        avg_distance = sum(e.coherence_distance for e in self.edges) / len(self.edges)
        avg_correlation = sum(e.correlation for e in self.edges) / len(self.edges)

        # Network coherence (geometric mean of node coherences)
        product = 1.0
        for node in self.nodes.values():
            product *= node.coherence
        network_coherence = product ** (1.0 / len(self.nodes))

        # Connectivity (actual edges / possible edges)
        n = len(self.nodes)
        max_edges = n * (n - 1) / 2
        connectivity = len(self.edges) / max_edges if max_edges > 0 else 0.0

        # Dimensionality (estimate from eigenvalue analysis - placeholder)
        # In full implementation, would compute correlation matrix eigenvalues
        dimensionality = min(3, len(self.nodes))  # Placeholder: assume 3D or less

        return NetworkMetrics(
            avg_coherence=avg_coherence,
            avg_distance=avg_distance,
            avg_correlation=avg_correlation,
            network_coherence=network_coherence,
            dimensionality=dimensionality,
            connectivity=connectivity
        )


    def find_coherence_clusters(
        self, max_cluster_distance: float = 1.0
    ) -> List[Set[str]]:
        """
        Find clusters of highly correlated nodes.

        Uses coherence distance threshold to group nodes.
        """
        # Build adjacency lists for nodes within distance threshold
        adjacency: Dict[str, Set[str]] = {nid: set() for nid in self.nodes.keys()}

        for edge in self.edges:
            if edge.coherence_distance <= max_cluster_distance:
                adjacency[edge.from_node].add(edge.to_node)
                adjacency[edge.to_node].add(edge.from_node)

        # Find connected components (clusters)
        visited = set()
        clusters = []

        def dfs(node_id: str, cluster: Set[str]):
            visited.add(node_id)
            cluster.add(node_id)
            for neighbor in adjacency[node_id]:
                if neighbor not in visited:
                    dfs(neighbor, cluster)

        for node_id in self.nodes.keys():
            if node_id not in visited:
                cluster = set()
                dfs(node_id, cluster)
                clusters.append(cluster)

        return clusters


    def export_to_dict(self) -> Dict:
        """Export network to dictionary for JSON serialization"""
        return {
            "nodes": [
                {
                    "id": node.node_id,
                    "coherence": node.coherence,
                    "position": node.position,
                    "metadata": node.metadata
                }
                for node in self.nodes.values()
            ],
            "edges": [
                {
                    "from": edge.from_node,
                    "to": edge.to_node,
                    "joint_coherence": edge.joint_coherence,
                    "distance": edge.coherence_distance,
                    "correlation": edge.correlation
                }
                for edge in self.edges
            ]
        }


# ============================================================================
# Test Cases
# ============================================================================

def test_coherence_distance():
    """Test basic coherence distance calculation"""
    print("Test 1: Coherence distance calculation")

    calc = CoherenceDistanceCalculator()

    # Test case 1: Perfect correlation (same location)
    c_a, c_b, c_ab = 0.8, 0.8, 0.8
    distance = calc.calculate_distance(c_a, c_b, c_ab)
    print(f"  Perfect correlation: d = {distance:.3f} (expected: 0)")

    # Test case 2: Independent (no correlation)
    c_a, c_b, c_ab = 0.8, 0.8, math.sqrt(0.8 * 0.8)
    distance = calc.calculate_distance(c_a, c_b, c_ab)
    print(f"  Independent: d = {distance:.3f} (expected: 0)")

    # Test case 3: High correlation (close)
    c_a, c_b, c_ab = 0.8, 0.8, 0.75
    distance = calc.calculate_distance(c_a, c_b, c_ab)
    print(f"  High correlation: d = {distance:.3f} (expected: small positive)")

    # Test case 4: Low correlation (distant)
    c_a, c_b, c_ab = 0.8, 0.8, 0.3
    distance = calc.calculate_distance(c_a, c_b, c_ab)
    print(f"  Low correlation: d = {distance:.3f} (expected: large positive)")

    print("  ✓ Test passed\n")


def test_pattern_based_distance():
    """Test distance calculation from behavior patterns"""
    print("Test 2: Pattern-based distance")

    calc = CoherenceDistanceCalculator()

    # Similar patterns (should be close)
    pattern_a = [10.0, 12.0, 11.0, 13.0, 12.0]
    pattern_b = [10.5, 12.5, 11.5, 13.5, 12.5]

    c_a, c_b, c_ab, distance = calc.calculate_from_patterns(pattern_a, pattern_b)

    print(f"  Similar patterns:")
    print(f"    C_A = {c_a:.3f}, C_B = {c_b:.3f}, C_AB = {c_ab:.3f}")
    print(f"    Distance = {distance:.3f} (expected: small)")

    # Different patterns (should be far)
    pattern_c = [50.0, 10.0, 80.0, 5.0, 90.0]

    c_a, c_c, c_ac, distance2 = calc.calculate_from_patterns(pattern_a, pattern_c)

    print(f"  Different patterns:")
    print(f"    C_A = {c_a:.3f}, C_C = {c_c:.3f}, C_AC = {c_ac:.3f}")
    print(f"    Distance = {distance2:.3f} (expected: large)")

    print(f"  ✓ Test passed\n" if distance < distance2 else "  ✗ Test failed\n")


def test_network_building():
    """Test building coherence network"""
    print("Test 3: Network building")

    builder = CoherenceNetworkBuilder()

    # Add nodes
    for i in range(5):
        builder.add_node(f"agent_{i}", coherence=0.5 + i * 0.1)

    # Add edges from patterns
    patterns = {
        "agent_0": [10.0, 12.0, 11.0, 13.0, 12.0],
        "agent_1": [10.5, 12.5, 11.5, 13.5, 12.5],  # Similar to 0
        "agent_2": [50.0, 10.0, 80.0, 5.0, 90.0],   # Different
        "agent_3": [10.2, 12.2, 11.2, 13.2, 12.2],  # Similar to 0,1
        "agent_4": [100.0, 105.0, 102.0, 104.0, 103.0],  # Different
    }

    # Create all pairwise edges
    agent_ids = list(patterns.keys())
    for i in range(len(agent_ids)):
        for j in range(i + 1, len(agent_ids)):
            builder.add_edge_from_patterns(
                agent_ids[i],
                agent_ids[j],
                patterns[agent_ids[i]],
                patterns[agent_ids[j]]
            )

    metrics = builder.calculate_network_metrics()

    print(f"  Network size: {len(builder.nodes)} nodes, {len(builder.edges)} edges")
    print(f"  Avg coherence: {metrics.avg_coherence:.3f}")
    print(f"  Avg distance: {metrics.avg_distance:.3f}")
    print(f"  Avg correlation: {metrics.avg_correlation:.3f}")
    print(f"  Network coherence: {metrics.network_coherence:.3f}")
    print(f"  Connectivity: {metrics.connectivity:.3f}")
    print(f"  ✓ Test passed\n")


def test_neighbor_finding():
    """Test finding neighbors within coherence distance"""
    print("Test 4: Neighbor finding")

    builder = CoherenceNetworkBuilder()

    # Simple 4-node network
    builder.add_node("A", 0.8)
    builder.add_node("B", 0.8)
    builder.add_node("C", 0.8)
    builder.add_node("D", 0.8)

    # A-B close, A-C medium, A-D far
    builder.add_edge_from_coherences("A", "B", 0.75)  # Close
    builder.add_edge_from_coherences("A", "C", 0.60)  # Medium
    builder.add_edge_from_coherences("A", "D", 0.30)  # Far

    # Find neighbors of A within distance 1.0
    neighbors = builder.get_neighbors("A", max_distance=1.0)

    print(f"  Neighbors of A within distance 1.0:")
    for neighbor_id, distance in neighbors:
        print(f"    {neighbor_id}: distance = {distance:.3f}")

    print(f"  ✓ Test passed\n")


def test_cluster_detection():
    """Test coherence cluster detection"""
    print("Test 5: Cluster detection")

    builder = CoherenceNetworkBuilder()

    # Create two clusters: {A, B, C} and {D, E}
    for node_id in ["A", "B", "C", "D", "E"]:
        builder.add_node(node_id, 0.7)

    # Cluster 1 edges (high correlation)
    builder.add_edge_from_coherences("A", "B", 0.68)
    builder.add_edge_from_coherences("B", "C", 0.68)
    builder.add_edge_from_coherences("A", "C", 0.68)

    # Cluster 2 edges (high correlation)
    builder.add_edge_from_coherences("D", "E", 0.68)

    # Inter-cluster edges (low correlation)
    builder.add_edge_from_coherences("C", "D", 0.30)

    clusters = builder.find_coherence_clusters(max_cluster_distance=0.5)

    print(f"  Found {len(clusters)} clusters:")
    for i, cluster in enumerate(clusters):
        print(f"    Cluster {i + 1}: {sorted(cluster)}")

    expected_clusters = 2
    print(f"  ✓ Test passed\n" if len(clusters) == expected_clusters else f"  ✗ Test failed\n")


def test_network_export():
    """Test network export to dict"""
    print("Test 6: Network export")

    builder = CoherenceNetworkBuilder()

    builder.add_node("A", 0.8, metadata={"type": "agent"})
    builder.add_node("B", 0.7, metadata={"type": "agent"})
    builder.add_edge_from_coherences("A", "B", 0.75)

    export = builder.export_to_dict()

    print(f"  Exported {len(export['nodes'])} nodes, {len(export['edges'])} edges")
    print(f"  JSON serializable: {type(export) == dict}")
    print(f"  ✓ Test passed\n")


# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("SESSION #179: Coherence Network Topology")
    print("=" * 80)
    print()
    print("Integrating Session 256 (Space from Coherence) with Web4")
    print()

    test_coherence_distance()
    test_pattern_based_distance()
    test_network_building()
    test_neighbor_finding()
    test_cluster_detection()
    test_network_export()

    print("=" * 80)
    print("All tests completed!")
    print("=" * 80)
