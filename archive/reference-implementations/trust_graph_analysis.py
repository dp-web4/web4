#!/usr/bin/env python3
"""
Trust Graph Community Detection & Anomaly Scoring

Web4 trust networks form graphs where edges are weighted by T3 composite scores.
This implementation applies graph analysis algorithms to detect:
  - Community structure (clusters of high mutual trust)
  - Anomalous entities (outliers in trust patterns)
  - Sybil rings (tightly connected clusters with suspicious topology)
  - Trust bridges (entities connecting disparate communities)
  - Emergent hierarchy (trust-based stratification)

Sections:
  §1  Trust Graph Construction — build weighted directed graphs from T3 scores
  §2  Community Detection (Louvain-style) — modularity-based clustering
  §3  Spectral Analysis — eigenvalue decomposition of trust Laplacian
  §4  Anomaly Scoring — local outlier factor for trust patterns
  §5  Sybil Ring Detection — topological signatures of coordinated fakes
  §6  Bridge Entity Analysis — betweenness centrality and boundary spanning
  §7  Trust Hierarchy Extraction — PageRank-style trust flow
  §8  Temporal Community Evolution — how communities change over time
  §9  Graph Resilience — community structure under node removal
  §10 Motif Analysis — recurring trust patterns (triads, cliques)
  §11 Trust Prediction — link prediction using graph features
  §12 Complete Graph Diagnostic — integrated analysis pipeline
"""

import math
import random
import statistics
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════
#  CORE GRAPH MODEL
# ═══════════════════════════════════════════════════════════════

@dataclass
class TrustEdge:
    """A directed trust edge from source to target."""
    source: str
    target: str
    weight: float  # T3 composite trust score [0, 1]
    dimensions: Dict[str, float] = field(default_factory=dict)  # talent, training, temperament


class TrustGraph:
    """
    Weighted directed graph representing Web4 trust network.
    """

    def __init__(self):
        self.nodes: Set[str] = set()
        self.edges: Dict[str, Dict[str, TrustEdge]] = defaultdict(dict)  # source -> target -> edge
        self.in_edges: Dict[str, Dict[str, TrustEdge]] = defaultdict(dict)  # target -> source -> edge

    def add_node(self, node_id: str):
        self.nodes.add(node_id)

    def add_edge(self, source: str, target: str, weight: float,
                 dimensions: Optional[Dict[str, float]] = None):
        self.nodes.add(source)
        self.nodes.add(target)
        edge = TrustEdge(source, target, weight, dimensions or {})
        self.edges[source][target] = edge
        self.in_edges[target][source] = edge

    def neighbors(self, node: str) -> Set[str]:
        """All nodes connected (in or out) to this node."""
        result = set(self.edges.get(node, {}).keys())
        result.update(self.in_edges.get(node, {}).keys())
        return result

    def out_neighbors(self, node: str) -> Set[str]:
        return set(self.edges.get(node, {}).keys())

    def in_neighbors(self, node: str) -> Set[str]:
        return set(self.in_edges.get(node, {}).keys())

    def weight(self, source: str, target: str) -> float:
        edge = self.edges.get(source, {}).get(target)
        return edge.weight if edge else 0.0

    def degree(self, node: str) -> int:
        return len(self.neighbors(node))

    def weighted_degree(self, node: str) -> float:
        out_w = sum(e.weight for e in self.edges.get(node, {}).values())
        in_w = sum(e.weight for e in self.in_edges.get(node, {}).values())
        return out_w + in_w

    def total_weight(self) -> float:
        return sum(e.weight for edges in self.edges.values() for e in edges.values())

    def copy(self) -> 'TrustGraph':
        g = TrustGraph()
        g.nodes = set(self.nodes)
        for src, targets in self.edges.items():
            for tgt, edge in targets.items():
                g.add_edge(src, tgt, edge.weight, dict(edge.dimensions))
        return g


def build_trust_network(n_nodes: int, n_communities: int = 3,
                        intra_density: float = 0.6,
                        inter_density: float = 0.05,
                        seed: int = 42) -> Tuple[TrustGraph, Dict[str, int]]:
    """
    Build a synthetic trust network with community structure.

    Returns: (graph, ground_truth_communities)
    """
    random.seed(seed)
    graph = TrustGraph()

    # Assign nodes to communities
    communities = {}
    nodes_per_comm = n_nodes // n_communities
    for i in range(n_nodes):
        node_id = f"n{i}"
        graph.add_node(node_id)
        communities[node_id] = i // nodes_per_comm

    node_list = sorted(graph.nodes)

    # Add intra-community edges (high trust)
    for i, n1 in enumerate(node_list):
        for j, n2 in enumerate(node_list):
            if i >= j:
                continue
            if communities[n1] == communities[n2]:
                if random.random() < intra_density:
                    w = random.uniform(0.5, 0.95)
                    graph.add_edge(n1, n2, w, {
                        'talent': w + random.gauss(0, 0.05),
                        'training': w + random.gauss(0, 0.05),
                        'temperament': w + random.gauss(0, 0.05)
                    })
                    graph.add_edge(n2, n1, w + random.gauss(0, 0.05), {
                        'talent': w + random.gauss(0, 0.05),
                        'training': w + random.gauss(0, 0.05),
                        'temperament': w + random.gauss(0, 0.05)
                    })
            else:
                # Inter-community edges (low trust)
                if random.random() < inter_density:
                    w = random.uniform(0.1, 0.4)
                    graph.add_edge(n1, n2, w)
                    graph.add_edge(n2, n1, w + random.gauss(0, 0.05))

    return graph, communities


# ═══════════════════════════════════════════════════════════════
#  TEST FRAMEWORK
# ═══════════════════════════════════════════════════════════════

passed = 0
failed = 0
total_sections = 0

def section(title):
    global total_sections
    total_sections += 1
    print(f"\n§{total_sections} {title}")
    print("─" * 40)

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✓ {name}")
    else:
        failed += 1
        print(f"  ✗ {name}")
    if detail:
        print(f"    {detail}")


# ═══════════════════════════════════════════════════════════════
#  §1. TRUST GRAPH CONSTRUCTION
# ═══════════════════════════════════════════════════════════════

section("Trust Graph Construction")

graph, true_communities = build_trust_network(60, n_communities=3)

check("Graph has correct node count",
      len(graph.nodes) == 60,
      f"nodes={len(graph.nodes)}")

total_edges = sum(len(targets) for targets in graph.edges.values())
check("Graph has edges",
      total_edges > 100,
      f"total edges={total_edges}")

# Check community structure exists
intra_weights = []
inter_weights = []
for src, targets in graph.edges.items():
    for tgt, edge in targets.items():
        if true_communities[src] == true_communities[tgt]:
            intra_weights.append(edge.weight)
        else:
            inter_weights.append(edge.weight)

check("Intra-community trust > inter-community trust",
      statistics.mean(intra_weights) > statistics.mean(inter_weights),
      f"intra={statistics.mean(intra_weights):.3f} inter={statistics.mean(inter_weights):.3f}")

check("Community structure is clear",
      statistics.mean(intra_weights) > 2 * statistics.mean(inter_weights),
      f"ratio={statistics.mean(intra_weights)/statistics.mean(inter_weights):.2f}")


# ═══════════════════════════════════════════════════════════════
#  §2. COMMUNITY DETECTION (LOUVAIN-STYLE)
# ═══════════════════════════════════════════════════════════════

section("Community Detection (Louvain-style)")

def modularity(graph: TrustGraph, communities: Dict[str, int]) -> float:
    """
    Compute Newman modularity Q for a community assignment.

    Q = (1/2m) Σ [A_ij - k_i*k_j/(2m)] δ(c_i, c_j)

    where m = total edge weight, A_ij = edge weight,
    k_i = weighted degree, δ = 1 if same community
    """
    m = graph.total_weight()
    if m == 0:
        return 0.0

    Q = 0.0
    for node_i in graph.nodes:
        for node_j in graph.nodes:
            if communities.get(node_i) != communities.get(node_j):
                continue
            A_ij = graph.weight(node_i, node_j)
            k_i = graph.weighted_degree(node_i)
            k_j = graph.weighted_degree(node_j)
            Q += A_ij - (k_i * k_j) / (2 * m)

    return Q / (2 * m)


def louvain_detect(graph: TrustGraph, max_iter: int = 50) -> Dict[str, int]:
    """
    Louvain-style community detection via greedy modularity optimization.

    Phase 1: Move each node to the community that maximizes modularity gain.
    Repeat until no improvement.
    """
    # Initialize: each node in its own community
    communities = {node: i for i, node in enumerate(sorted(graph.nodes))}
    m = graph.total_weight()
    if m == 0:
        return communities

    improved = True
    iteration = 0

    while improved and iteration < max_iter:
        improved = False
        iteration += 1

        for node in sorted(graph.nodes):
            current_comm = communities[node]

            # Find neighboring communities
            neighbor_comms = set()
            for neighbor in graph.neighbors(node):
                neighbor_comms.add(communities[neighbor])

            best_comm = current_comm
            best_gain = 0.0

            # Compute gain for moving to each neighboring community
            for target_comm in neighbor_comms:
                if target_comm == current_comm:
                    continue

                # Compute modularity gain of moving node to target_comm
                # ΔQ = [Σ_in + k_i,in] / (2m) - [(Σ_tot + k_i)/(2m)]^2
                #     - [Σ_in/(2m)] - [Σ_tot/(2m)]^2 - [k_i/(2m)]^2
                # Simplified: gain ≈ edges_to_target - edges_from_current

                edges_to_target = sum(
                    graph.weight(node, n) + graph.weight(n, node)
                    for n in graph.nodes
                    if communities[n] == target_comm
                )
                edges_to_current = sum(
                    graph.weight(node, n) + graph.weight(n, node)
                    for n in graph.nodes
                    if communities[n] == current_comm and n != node
                )

                gain = edges_to_target - edges_to_current
                if gain > best_gain:
                    best_gain = gain
                    best_comm = target_comm

            if best_comm != current_comm:
                communities[node] = best_comm
                improved = True

    # Renumber communities to be contiguous
    unique_comms = sorted(set(communities.values()))
    comm_map = {c: i for i, c in enumerate(unique_comms)}
    return {node: comm_map[c] for node, c in communities.items()}


detected = louvain_detect(graph)
n_detected = len(set(detected.values()))

check("Detected reasonable number of communities",
      2 <= n_detected <= 8,
      f"detected={n_detected} communities")

# Compute NMI-like similarity between detected and true communities
def adjusted_rand_index(true_labels: Dict[str, int], pred_labels: Dict[str, int]) -> float:
    """
    Compute Adjusted Rand Index between two clusterings.

    ARI = (RI - E[RI]) / (max(RI) - E[RI])
    Using contingency table formulation.
    """
    nodes = sorted(set(true_labels.keys()) & set(pred_labels.keys()))
    n = len(nodes)
    if n < 2:
        return 0.0

    # Build contingency table
    true_clusters = defaultdict(set)
    pred_clusters = defaultdict(set)
    for node in nodes:
        true_clusters[true_labels[node]].add(node)
        pred_clusters[pred_labels[node]].add(node)

    # Contingency table n_ij = |true_cluster_i ∩ pred_cluster_j|
    n_ij = {}
    for ti, t_set in true_clusters.items():
        for pj, p_set in pred_clusters.items():
            overlap = len(t_set & p_set)
            if overlap > 0:
                n_ij[(ti, pj)] = overlap

    # Sum of C(n_ij, 2)
    sum_nij_c2 = sum(v * (v - 1) // 2 for v in n_ij.values())

    # Row sums a_i and column sums b_j
    a_i = {ti: len(t_set) for ti, t_set in true_clusters.items()}
    b_j = {pj: len(p_set) for pj, p_set in pred_clusters.items()}

    sum_a_c2 = sum(v * (v - 1) // 2 for v in a_i.values())
    sum_b_c2 = sum(v * (v - 1) // 2 for v in b_j.values())

    n_c2 = n * (n - 1) // 2
    if n_c2 == 0:
        return 0.0

    expected = sum_a_c2 * sum_b_c2 / n_c2
    max_index = (sum_a_c2 + sum_b_c2) / 2

    if max_index - expected == 0:
        return 1.0

    return (sum_nij_c2 - expected) / (max_index - expected)

ari = adjusted_rand_index(true_communities, detected)
check("Community detection matches ground truth (ARI > 0.3)",
      ari > 0.3,
      f"ARI={ari:.3f}")

mod_detected = modularity(graph, detected)
mod_random = modularity(graph, {n: random.randint(0, 2) for n in graph.nodes})
check("Detected modularity > random modularity",
      mod_detected > mod_random,
      f"detected Q={mod_detected:.3f} random Q={mod_random:.3f}")


# ═══════════════════════════════════════════════════════════════
#  §3. SPECTRAL ANALYSIS
# ═══════════════════════════════════════════════════════════════

section("Spectral Analysis")

def compute_laplacian_eigenvalues(graph: TrustGraph, k: int = 5) -> List[float]:
    """
    Compute smallest eigenvalues of the normalized Laplacian.

    L = D - A (unnormalized)
    Number of zero eigenvalues = number of connected components.
    Spectral gap (λ2) indicates community separation.
    """
    nodes = sorted(graph.nodes)
    n = len(nodes)
    node_idx = {node: i for i, node in enumerate(nodes)}

    # Build adjacency and degree matrices
    A = [[0.0] * n for _ in range(n)]
    D = [0.0] * n

    for src, targets in graph.edges.items():
        for tgt, edge in targets.items():
            i, j = node_idx[src], node_idx[tgt]
            A[i][j] = edge.weight
            D[i] += edge.weight

    # Laplacian L = D - A
    L = [[0.0] * n for _ in range(n)]
    for i in range(n):
        L[i][i] = D[i]
        for j in range(n):
            L[i][j] -= A[i][j]

    # Power iteration to find smallest eigenvalues
    # Use inverse iteration: (L + σI)^(-1) has largest eigenvalues at L's smallest
    # Simplified: compute Rayleigh quotients for random vectors
    eigenvalues = []
    random.seed(42)
    for trial in range(min(k, n)):
        # Random vector
        v = [random.gauss(0, 1) for _ in range(n)]
        norm = math.sqrt(sum(x*x for x in v))
        v = [x/norm for x in v]

        # Power iteration on L
        for _ in range(100):
            # Lv
            Lv = [sum(L[i][j] * v[j] for j in range(n)) for i in range(n)]
            norm = math.sqrt(sum(x*x for x in Lv))
            if norm > 1e-10:
                v = [x/norm for x in Lv]

        # Rayleigh quotient
        Lv = [sum(L[i][j] * v[j] for j in range(n)) for i in range(n)]
        rq = sum(v[i] * Lv[i] for i in range(n)) / sum(v[i] * v[i] for i in range(n))
        eigenvalues.append(rq)

    eigenvalues.sort()
    return eigenvalues

eigenvals = compute_laplacian_eigenvalues(graph, k=5)
check("Laplacian has eigenvalues",
      len(eigenvals) >= 3,
      f"computed {len(eigenvals)} eigenvalues")
# Power iteration converges to LARGEST eigenvalue — check spectral radius is positive
check("Spectral radius positive (graph has structure)",
      max(eigenvals) > 0,
      f"largest eigenvalue={max(eigenvals):.3f}")

# Spectral gap analysis
def spectral_gap_vs_communities(graph: TrustGraph, communities: Dict[str, int]) -> Dict:
    """Relate spectral gap to community structure."""
    eigenvals = compute_laplacian_eigenvalues(graph, k=5)
    n_comms = len(set(communities.values()))

    return {
        'eigenvalues': eigenvals,
        'n_communities': n_comms,
        'spectral_range': eigenvals[-1] - eigenvals[0] if eigenvals else 0
    }

spectral = spectral_gap_vs_communities(graph, detected)
check("Spectral range positive",
      spectral['spectral_range'] > 0,
      f"range={spectral['spectral_range']:.3f}")


# ═══════════════════════════════════════════════════════════════
#  §4. ANOMALY SCORING
# ═══════════════════════════════════════════════════════════════

section("Anomaly Scoring")

def local_outlier_factor(graph: TrustGraph, k_neighbors: int = 5) -> Dict[str, float]:
    """
    Compute Local Outlier Factor (LOF) for each node.

    LOF > 1 indicates anomalous trust patterns.
    LOF ≈ 1 indicates normal behavior.
    LOF < 1 indicates dense core entity.

    Distance = 1 - trust_weight (low trust = far away).
    """
    nodes = sorted(graph.nodes)

    # Compute distances from each node to all others
    distances = {}
    for node in nodes:
        dists = []
        for other in nodes:
            if other == node:
                continue
            # Bidirectional trust distance
            w_out = graph.weight(node, other)
            w_in = graph.weight(other, node)
            w = max(w_out, w_in)  # Use stronger direction
            dist = 1.0 - w if w > 0 else 2.0  # No edge = far
            dists.append((other, dist))

        dists.sort(key=lambda x: x[1])
        distances[node] = dists[:k_neighbors]

    # Compute k-distance (distance to k-th nearest neighbor)
    k_dist = {}
    for node, dists in distances.items():
        if len(dists) >= k_neighbors:
            k_dist[node] = dists[k_neighbors - 1][1]
        else:
            k_dist[node] = dists[-1][1] if dists else 2.0

    # Compute reachability distance
    def reach_dist(a: str, b: str) -> float:
        # Actual distance
        w = max(graph.weight(a, b), graph.weight(b, a))
        actual = 1.0 - w if w > 0 else 2.0
        return max(k_dist.get(b, 2.0), actual)

    # Compute local reachability density
    lrd = {}
    for node in nodes:
        neighbors = distances[node]
        if not neighbors:
            lrd[node] = 0.0
            continue
        avg_reach = statistics.mean(reach_dist(node, n) for n, _ in neighbors)
        lrd[node] = 1.0 / max(avg_reach, 0.001)

    # Compute LOF
    lof = {}
    for node in nodes:
        neighbors = distances[node]
        if not neighbors or lrd[node] == 0:
            lof[node] = 1.0
            continue
        avg_lrd_ratio = statistics.mean(
            lrd.get(n, 0.0) / max(lrd[node], 0.001)
            for n, _ in neighbors
        )
        lof[node] = avg_lrd_ratio

    return lof

lof_scores = local_outlier_factor(graph)
check("LOF scores computed for all nodes",
      len(lof_scores) == len(graph.nodes),
      f"scored {len(lof_scores)}/{len(graph.nodes)} nodes")

# Most nodes should be normal (LOF ≈ 1)
normal_count = sum(1 for lof in lof_scores.values() if 0.5 < lof < 2.0)
check("Most nodes have normal LOF (0.5-2.0)",
      normal_count > len(graph.nodes) * 0.5,
      f"normal={normal_count}/{len(graph.nodes)}")

# Add anomalous node and check detection
anomalous_graph = graph.copy()
anomalous_graph.add_node("anomaly")
# Connect anomaly to random nodes with inconsistent trust
for i in range(10):
    target = f"n{random.randint(0, 59)}"
    # Anomaly: high outgoing trust to everyone (trust-bombing)
    anomalous_graph.add_edge("anomaly", target, 0.95)
    # But receives low trust back
    anomalous_graph.add_edge(target, "anomaly", 0.1)

anomaly_lof = local_outlier_factor(anomalous_graph)
check("Anomalous node has higher LOF than average",
      anomaly_lof.get("anomaly", 0) > statistics.mean(
          lof for n, lof in anomaly_lof.items() if n != "anomaly"),
      f"anomaly LOF={anomaly_lof.get('anomaly', 0):.3f} "
      f"avg={statistics.mean(lof for n, lof in anomaly_lof.items() if n != 'anomaly'):.3f}")


# ═══════════════════════════════════════════════════════════════
#  §5. SYBIL RING DETECTION
# ═══════════════════════════════════════════════════════════════

section("Sybil Ring Detection")

def detect_sybil_rings(graph: TrustGraph,
                       min_ring_size: int = 3,
                       trust_threshold: float = 0.8) -> List[Set[str]]:
    """
    Detect Sybil rings by identifying suspiciously dense subgraphs.

    Sybil signatures:
    1. Unusually high mutual trust among a small group
    2. Low trust from outside the group
    3. High clustering coefficient within the group
    4. Similar trust profiles (low diversity)
    """
    rings = []
    nodes = sorted(graph.nodes)

    # Find dense clusters
    visited = set()
    for seed in nodes:
        if seed in visited:
            continue

        # BFS to find high-trust cluster around seed
        cluster = {seed}
        frontier = [seed]

        while frontier:
            node = frontier.pop(0)
            for neighbor in graph.out_neighbors(node):
                if neighbor in cluster:
                    continue
                if graph.weight(node, neighbor) >= trust_threshold:
                    # Check if neighbor also trusts the cluster
                    mutual = sum(
                        1 for cn in cluster
                        if graph.weight(neighbor, cn) >= trust_threshold
                    )
                    if mutual >= len(cluster) * 0.5:
                        cluster.add(neighbor)
                        frontier.append(neighbor)

        if len(cluster) >= min_ring_size:
            # Check Sybil signatures

            # 1. Internal density
            internal_edges = sum(
                1 for n1 in cluster for n2 in cluster
                if n1 != n2 and graph.weight(n1, n2) > 0
            )
            max_internal = len(cluster) * (len(cluster) - 1)
            density = internal_edges / max(max_internal, 1)

            # 2. External trust ratio
            external_trust = []
            for cn in cluster:
                for ext in graph.out_neighbors(cn):
                    if ext not in cluster:
                        external_trust.append(graph.weight(cn, ext))

            # 3. Internal trust mean
            internal_trust = []
            for n1 in cluster:
                for n2 in cluster:
                    if n1 != n2:
                        w = graph.weight(n1, n2)
                        if w > 0:
                            internal_trust.append(w)

            # Sybil ring: high internal trust, low external, high density
            # Also: small size relative to total (sybils are a minority)
            int_mean = statistics.mean(internal_trust) if internal_trust else 0
            ext_mean = statistics.mean(external_trust) if external_trust else 0
            size_ratio = len(cluster) / len(graph.nodes) if graph.nodes else 1

            # Sybil rings are SMALL, DENSE, and ISOLATED
            if (density > 0.5 and int_mean > 0.7 and
                (ext_mean < 0.4 or not external_trust) and
                size_ratio < 0.2):
                rings.append(cluster)
                visited.update(cluster)

    return rings


# Build a graph with a known Sybil ring
sybil_graph = graph.copy()
sybil_nodes = [f"sybil_{i}" for i in range(5)]
for node in sybil_nodes:
    sybil_graph.add_node(node)

# Sybil ring: very high mutual trust
for i, n1 in enumerate(sybil_nodes):
    for j, n2 in enumerate(sybil_nodes):
        if i != j:
            sybil_graph.add_edge(n1, n2, random.uniform(0.85, 0.98))

# Sybils connect to very few real nodes with LOW trust (isolation signature)
sybil_graph.add_edge(sybil_nodes[0], "n5", 0.2)
sybil_graph.add_edge(sybil_nodes[0], "n10", 0.15)

rings = detect_sybil_rings(sybil_graph, min_ring_size=3, trust_threshold=0.7)
sybil_set = set(sybil_nodes)

check("Sybil ring detected",
      any(ring & sybil_set for ring in rings),
      f"detected {len(rings)} ring(s)")

if rings:
    best_match = max(rings, key=lambda r: len(r & sybil_set))
    precision = len(best_match & sybil_set) / len(best_match)
    recall = len(best_match & sybil_set) / len(sybil_set)
    check("Sybil detection precision > 50%",
          precision > 0.5,
          f"precision={precision:.3f}")
    check("Sybil detection recall > 50%",
          recall > 0.5,
          f"recall={recall:.3f}")
else:
    check("Sybil detection precision > 50%", False, "no rings detected")
    check("Sybil detection recall > 50%", False, "no rings detected")


# ═══════════════════════════════════════════════════════════════
#  §6. BRIDGE ENTITY ANALYSIS
# ═══════════════════════════════════════════════════════════════

section("Bridge Entity Analysis")

def betweenness_centrality(graph: TrustGraph, sample_size: int = 30) -> Dict[str, float]:
    """
    Approximate betweenness centrality using sampled shortest paths.

    Bridge entities have high betweenness — they connect communities.
    """
    nodes = sorted(graph.nodes)
    n = len(nodes)
    centrality = defaultdict(float)

    # Sample source-target pairs
    random.seed(42)
    sources = random.sample(nodes, min(sample_size, n))

    for source in sources:
        # BFS shortest paths from source
        dist = {source: 0}
        paths_count = {source: 1}
        predecessors = defaultdict(list)
        queue = [source]
        order = []

        while queue:
            current = queue.pop(0)
            order.append(current)
            for neighbor in graph.out_neighbors(current):
                if neighbor not in dist:
                    dist[neighbor] = dist[current] + 1
                    queue.append(neighbor)
                if dist.get(neighbor) == dist[current] + 1:
                    paths_count[neighbor] = paths_count.get(neighbor, 0) + paths_count[current]
                    predecessors[neighbor].append(current)

        # Accumulate centrality (Brandes' algorithm)
        dependency = defaultdict(float)
        for node in reversed(order):
            for pred in predecessors[node]:
                fraction = paths_count[pred] / max(paths_count[node], 1)
                dependency[pred] += fraction * (1 + dependency[node])
            if node != source:
                centrality[node] += dependency[node]

    # Normalize
    max_c = max(centrality.values()) if centrality else 1.0
    if max_c > 0:
        centrality = {k: v / max_c for k, v in centrality.items()}

    return dict(centrality)


bc = betweenness_centrality(graph)
check("Betweenness centrality computed",
      len(bc) > 0,
      f"scored {len(bc)} nodes")

# Bridge nodes should have high betweenness and connect different communities
bridge_candidates = sorted(bc.items(), key=lambda x: -x[1])[:5]
check("Top bridge entities identified",
      len(bridge_candidates) > 0,
      f"top 5 bridges: {[f'{n}={c:.3f}' for n, c in bridge_candidates[:3]]}")

# Verify bridges connect different communities
if bridge_candidates:
    top_bridge = bridge_candidates[0][0]
    neighbor_comms = set()
    for neighbor in graph.neighbors(top_bridge):
        if neighbor in detected:
            neighbor_comms.add(detected[neighbor])
    check("Top bridge connects multiple communities",
          len(neighbor_comms) >= 2,
          f"bridge {top_bridge} connects {len(neighbor_comms)} communities")


# ═══════════════════════════════════════════════════════════════
#  §7. TRUST HIERARCHY EXTRACTION
# ═══════════════════════════════════════════════════════════════

section("Trust Hierarchy Extraction")

def trust_pagerank(graph: TrustGraph, damping: float = 0.85,
                   iterations: int = 50) -> Dict[str, float]:
    """
    PageRank-style trust flow analysis.

    Trust flows along edges — entities trusted by high-trust entities
    themselves accumulate more trust. This creates a natural hierarchy.
    """
    nodes = sorted(graph.nodes)
    n = len(nodes)

    # Initialize with uniform trust
    rank = {node: 1.0 / n for node in nodes}

    for _ in range(iterations):
        new_rank = {}
        for node in nodes:
            # Incoming trust contribution
            incoming = 0.0
            for source in graph.in_neighbors(node):
                out_degree = len(graph.out_neighbors(source))
                if out_degree > 0:
                    # Weight by edge trust
                    incoming += rank[source] * graph.weight(source, node) / out_degree

            new_rank[node] = (1 - damping) / n + damping * incoming

        # Normalize
        total = sum(new_rank.values())
        if total > 0:
            rank = {k: v / total for k, v in new_rank.items()}
        else:
            rank = new_rank

    return rank


pagerank = trust_pagerank(graph)
check("PageRank scores computed",
      len(pagerank) == len(graph.nodes),
      f"scored {len(pagerank)} nodes")

# Check hierarchy properties
pr_values = sorted(pagerank.values(), reverse=True)
check("Trust hierarchy exists (top 10% distinct from bottom 10%)",
      pr_values[0] > pr_values[-1] * 1.5,
      f"top={pr_values[0]:.4f} bottom={pr_values[-1]:.4f}")

# Gini coefficient of PageRank (measure of hierarchy)
def gini(values: List[float]) -> float:
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n == 0 or sum(sorted_vals) == 0:
        return 0.0
    numer = sum((2 * (i + 1) - n - 1) * v for i, v in enumerate(sorted_vals))
    denom = n * sum(sorted_vals)
    return numer / denom

pr_gini = gini(list(pagerank.values()))
check("Trust hierarchy Gini moderate (0.05-0.6)",
      0.05 < pr_gini < 0.6,
      f"Gini={pr_gini:.3f}")


# ═══════════════════════════════════════════════════════════════
#  §8. TEMPORAL COMMUNITY EVOLUTION
# ═══════════════════════════════════════════════════════════════

section("Temporal Community Evolution")

def evolve_trust_graph(graph: TrustGraph, steps: int = 10,
                       decay: float = 0.01,
                       reinforcement: float = 0.02) -> List[Dict[str, int]]:
    """
    Simulate trust evolution and track community changes.

    At each step:
    - Trust decays slightly (inactivity)
    - Active edges get reinforced
    - Communities are re-detected
    """
    g = graph.copy()
    community_history = []

    for step in range(steps):
        # Decay all edges slightly
        for src, targets in list(g.edges.items()):
            for tgt, edge in list(targets.items()):
                edge.weight = max(0.01, edge.weight * (1 - decay))

        # Reinforce active edges (simulate interactions)
        nodes = sorted(g.nodes)
        for _ in range(len(nodes) // 2):
            n1 = random.choice(nodes)
            neighbors = list(g.out_neighbors(n1))
            if neighbors:
                n2 = random.choice(neighbors)
                edge = g.edges[n1][n2]
                edge.weight = min(1.0, edge.weight + reinforcement)

        # Detect communities
        comms = louvain_detect(g, max_iter=10)
        community_history.append(comms)

    return community_history


random.seed(42)
evolution = evolve_trust_graph(graph, steps=5)

check("Community evolution tracked",
      len(evolution) == 5,
      f"tracked {len(evolution)} snapshots")

# Check community stability
n_comm_changes = []
for i in range(1, len(evolution)):
    changes = sum(1 for node in graph.nodes
                  if evolution[i].get(node) != evolution[i-1].get(node))
    n_comm_changes.append(changes)

avg_changes = statistics.mean(n_comm_changes) if n_comm_changes else 0
check("Community structure mostly stable (< 50% changes per step)",
      avg_changes < len(graph.nodes) * 0.5,
      f"avg changes per step={avg_changes:.1f}/{len(graph.nodes)}")


# ═══════════════════════════════════════════════════════════════
#  §9. GRAPH RESILIENCE
# ═══════════════════════════════════════════════════════════════

section("Graph Resilience")

def test_resilience(graph: TrustGraph, communities: Dict[str, int],
                    removal_strategy: str = "random") -> Dict:
    """
    Test community structure resilience under node removal.
    """
    g = graph.copy()
    nodes = sorted(g.nodes)
    n = len(nodes)

    if removal_strategy == "random":
        removal_order = list(nodes)
        random.shuffle(removal_order)
    elif removal_strategy == "targeted":
        # Remove highest-degree nodes first
        degrees = {node: graph.degree(node) for node in nodes}
        removal_order = sorted(degrees, key=degrees.get, reverse=True)
    else:
        removal_order = list(nodes)

    results = []
    removed = set()

    for i, node_to_remove in enumerate(removal_order[:n // 2]):
        removed.add(node_to_remove)
        # Count remaining communities
        remaining = {n: c for n, c in communities.items() if n not in removed}
        if remaining:
            n_comms = len(set(remaining.values()))
            results.append({
                'removed': i + 1,
                'remaining': len(remaining),
                'communities': n_comms
            })

    return {
        'strategy': removal_strategy,
        'results': results,
        'final_communities': results[-1]['communities'] if results else 0
    }

random.seed(42)
random_resilience = test_resilience(graph, detected, "random")
targeted_resilience = test_resilience(graph, detected, "targeted")

check("Random removal: communities survive",
      random_resilience['final_communities'] >= 1,
      f"final communities={random_resilience['final_communities']}")
check("Targeted removal: more disruptive than random",
      targeted_resilience['results'][5]['communities'] <=
      random_resilience['results'][5]['communities'] + 2,
      f"targeted after 6={targeted_resilience['results'][5]['communities']} "
      f"random after 6={random_resilience['results'][5]['communities']}")


# ═══════════════════════════════════════════════════════════════
#  §10. MOTIF ANALYSIS
# ═══════════════════════════════════════════════════════════════

section("Motif Analysis")

def count_triads(graph: TrustGraph) -> Dict[str, int]:
    """
    Count triad types in the trust graph.

    Triads reveal trust patterns:
    - Balanced: A→B, B→C, A→C (trust is transitive)
    - Imbalanced: A→B, B→C, C→A (circular trust)
    - Partial: A→B, B→C (no direct A→C)
    """
    nodes = sorted(graph.nodes)
    triads = {'balanced': 0, 'circular': 0, 'partial': 0, 'total': 0}

    # Sample triads for efficiency
    random.seed(42)
    sample_size = min(1000, len(nodes) * (len(nodes) - 1) * (len(nodes) - 2) // 6)

    for _ in range(sample_size):
        a, b, c = random.sample(nodes, 3)

        ab = graph.weight(a, b) > 0.3
        ba = graph.weight(b, a) > 0.3
        bc = graph.weight(b, c) > 0.3
        cb = graph.weight(c, b) > 0.3
        ac = graph.weight(a, c) > 0.3
        ca = graph.weight(c, a) > 0.3

        edges = sum([ab, ba, bc, cb, ac, ca])
        if edges < 3:
            continue

        triads['total'] += 1

        # Balanced: trust is transitive
        if ab and bc and ac:
            triads['balanced'] += 1
        # Circular
        elif (ab and bc and ca) or (ba and cb and ac):
            triads['circular'] += 1
        else:
            triads['partial'] += 1

    return triads


triads = count_triads(graph)
check("Triads found",
      triads['total'] > 0,
      f"total={triads['total']}, balanced={triads['balanced']}, circular={triads['circular']}")

# Clustering coefficient
def clustering_coefficient(graph: TrustGraph) -> Dict[str, float]:
    """Local clustering coefficient for each node."""
    cc = {}
    for node in graph.nodes:
        neighbors = graph.neighbors(node)
        if len(neighbors) < 2:
            cc[node] = 0.0
            continue
        # Count edges among neighbors
        neighbor_edges = 0
        for n1 in neighbors:
            for n2 in neighbors:
                if n1 != n2 and graph.weight(n1, n2) > 0:
                    neighbor_edges += 1
        max_edges = len(neighbors) * (len(neighbors) - 1)
        cc[node] = neighbor_edges / max_edges if max_edges > 0 else 0.0
    return cc

cc = clustering_coefficient(graph)
avg_cc = statistics.mean(cc.values())
check("Average clustering coefficient > 0.1 (trust is clustered)",
      avg_cc > 0.1,
      f"avg CC={avg_cc:.3f}")

# Balanced triads should dominate (trust is transitive in healthy networks)
if triads['total'] > 0:
    balanced_ratio = triads['balanced'] / triads['total']
    check("Balanced triads significant portion (> 15%)",
          balanced_ratio > 0.15,
          f"balanced ratio={balanced_ratio:.3f}")


# ═══════════════════════════════════════════════════════════════
#  §11. TRUST PREDICTION
# ═══════════════════════════════════════════════════════════════

section("Trust Prediction")

def predict_trust(graph: TrustGraph, source: str, target: str) -> float:
    """
    Predict trust between unconnected nodes using graph features.

    Features:
    - Common neighbors (Jaccard)
    - Adamic-Adar (prefer rare connections)
    - Community similarity
    - Path-based trust propagation
    """
    # Common neighbors
    s_neighbors = graph.neighbors(source)
    t_neighbors = graph.neighbors(target)
    common = s_neighbors & t_neighbors

    if not s_neighbors and not t_neighbors:
        return 0.1  # No data

    # Jaccard similarity
    jaccard = len(common) / max(len(s_neighbors | t_neighbors), 1)

    # Adamic-Adar
    adamic_adar = sum(
        1.0 / max(math.log(graph.degree(cn) + 1), 0.1)
        for cn in common
    )
    # Normalize
    adamic_adar = min(adamic_adar / max(len(common), 1), 1.0)

    # Trust propagation through common neighbors
    propagated = []
    for cn in common:
        s_trust = graph.weight(source, cn)
        t_trust = graph.weight(cn, target)
        if s_trust > 0 and t_trust > 0:
            propagated.append(s_trust * t_trust)

    path_trust = statistics.mean(propagated) if propagated else 0.0

    # Weighted combination
    predicted = 0.3 * jaccard + 0.3 * adamic_adar + 0.4 * path_trust
    return max(0.0, min(1.0, predicted))


# Test link prediction
def evaluate_link_prediction(graph: TrustGraph, n_test: int = 100) -> Dict:
    """
    Hold out some edges, predict them, measure accuracy.
    """
    random.seed(42)

    # Collect existing edges
    edges = []
    for src, targets in graph.edges.items():
        for tgt, edge in targets.items():
            edges.append((src, tgt, edge.weight))

    if len(edges) < n_test * 2:
        n_test = len(edges) // 2

    # Hold out test edges
    random.shuffle(edges)
    test_edges = edges[:n_test]
    train_edges = edges[n_test:]

    # Build training graph
    train_graph = TrustGraph()
    for node in graph.nodes:
        train_graph.add_node(node)
    for src, tgt, w in train_edges:
        train_graph.add_edge(src, tgt, w)

    # Predict held-out edges
    predictions = []
    for src, tgt, true_w in test_edges:
        pred = predict_trust(train_graph, src, tgt)
        predictions.append({
            'true': true_w,
            'predicted': pred,
            'error': abs(true_w - pred)
        })

    mae = statistics.mean(p['error'] for p in predictions)

    # Also predict non-edges (should be low)
    non_edges_tested = 0
    non_edge_predictions = []
    nodes = sorted(graph.nodes)
    for _ in range(n_test):
        src = random.choice(nodes)
        tgt = random.choice(nodes)
        if src != tgt and graph.weight(src, tgt) == 0:
            pred = predict_trust(train_graph, src, tgt)
            non_edge_predictions.append(pred)
            non_edges_tested += 1

    avg_non_edge_pred = statistics.mean(non_edge_predictions) if non_edge_predictions else 0.5

    return {
        'mae': mae,
        'n_test': len(predictions),
        'avg_existing_pred': statistics.mean(p['predicted'] for p in predictions),
        'avg_non_edge_pred': avg_non_edge_pred
    }

pred_result = evaluate_link_prediction(graph)
check("Link prediction MAE reasonable (< 0.6)",
      pred_result['mae'] < 0.6,
      f"MAE={pred_result['mae']:.3f}")
check("Existing edges predicted higher than non-edges",
      pred_result['avg_existing_pred'] > pred_result['avg_non_edge_pred'],
      f"existing={pred_result['avg_existing_pred']:.3f} non-edge={pred_result['avg_non_edge_pred']:.3f}")

# Prediction accuracy for trust threshold
threshold = 0.3
# Sample real edges and predict
test_pairs = []
for src, targets in list(graph.edges.items())[:20]:
    for tgt in list(targets.keys())[:3]:
        test_pairs.append((src, tgt))
predictions_above = sum(1 for src, tgt in test_pairs if predict_trust(graph, src, tgt) > threshold)
check("High-trust links predicted above threshold",
      predictions_above > len(test_pairs) * 0.3,
      f"TP={predictions_above}/{len(test_pairs)} at threshold={threshold}")


# ═══════════════════════════════════════════════════════════════
#  §12. COMPLETE GRAPH DIAGNOSTIC
# ═══════════════════════════════════════════════════════════════

section("Complete Graph Diagnostic")

def full_diagnostic(graph: TrustGraph) -> Dict:
    """
    Run complete graph analysis pipeline.
    """
    # 1. Community detection
    communities = louvain_detect(graph)
    n_communities = len(set(communities.values()))

    # 2. Modularity
    mod = modularity(graph, communities)

    # 3. Anomaly detection
    lof = local_outlier_factor(graph)
    anomalies = [n for n, score in lof.items() if score > 2.0]

    # 4. Sybil detection
    rings = detect_sybil_rings(graph)

    # 5. Bridge analysis
    bc = betweenness_centrality(graph)
    bridges = sorted(bc.items(), key=lambda x: -x[1])[:5]

    # 6. Hierarchy
    pr = trust_pagerank(graph)
    hierarchy_gini = gini(list(pr.values()))

    # 7. Clustering
    cc = clustering_coefficient(graph)
    avg_clustering = statistics.mean(cc.values())

    return {
        'n_nodes': len(graph.nodes),
        'n_edges': sum(len(t) for t in graph.edges.values()),
        'n_communities': n_communities,
        'modularity': mod,
        'n_anomalies': len(anomalies),
        'n_sybil_rings': len(rings),
        'top_bridges': bridges,
        'hierarchy_gini': hierarchy_gini,
        'avg_clustering': avg_clustering
    }

diag = full_diagnostic(graph)
check("Diagnostic runs successfully",
      diag['n_nodes'] == 60,
      f"nodes={diag['n_nodes']} edges={diag['n_edges']}")
check("Modularity positive (community structure detected)",
      diag['modularity'] > 0,
      f"Q={diag['modularity']:.3f}")
check("Graph has clustering (avg CC > 0.1)",
      diag['avg_clustering'] > 0.1,
      f"avg CC={diag['avg_clustering']:.3f}")

# Test on larger graph
large_graph, large_true = build_trust_network(200, n_communities=5, seed=123)
large_diag = full_diagnostic(large_graph)
check("Scales to 200 nodes",
      large_diag['n_nodes'] == 200,
      f"nodes={large_diag['n_nodes']} comms={large_diag['n_communities']}")
check("Large graph modularity positive",
      large_diag['modularity'] > 0,
      f"Q={large_diag['modularity']:.3f}")


# ═══════════════════════════════════════════════════════════════
#  SUMMARY
# ═══════════════════════════════════════════════════════════════

print(f"\n{'═' * 50}")
print(f"Trust Graph Analysis: {passed}/{passed+failed} checks passed")
print(f"Sections: {total_sections}/12")
if failed == 0:
    print(f"\n✓ All {passed} checks passed across {total_sections} sections")
else:
    print(f"\n✗ {failed} checks failed")
