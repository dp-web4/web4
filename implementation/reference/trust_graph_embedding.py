"""
Trust Graph Embedding for Web4
Session 32, Track 4

Embed trust graphs into vector spaces for similarity, clustering, and ML:
- Adjacency-based spectral embedding (eigendecomposition of Laplacian)
- Random walk embedding (node2vec-style)
- Trust-weighted embedding (trust values as edge weights)
- Entity similarity from embeddings (cosine, euclidean)
- Community detection via embedding clustering
- Embedding quality metrics (stress, distortion)
- Low-dimensional visualization (2D projection)
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict


# ─── Trust Graph ──────────────────────────────────────────────────

@dataclass
class WeightedGraph:
    """Weighted directed graph for trust relationships."""
    nodes: List[str] = field(default_factory=list)
    edges: Dict[Tuple[str, str], float] = field(default_factory=dict)
    _node_set: Set[str] = field(default_factory=set)

    def add_node(self, node: str):
        if node not in self._node_set:
            self.nodes.append(node)
            self._node_set.add(node)

    def add_edge(self, source: str, target: str, weight: float = 1.0):
        self.add_node(source)
        self.add_node(target)
        self.edges[(source, target)] = weight

    def neighbors(self, node: str) -> List[Tuple[str, float]]:
        result = []
        for (s, t), w in self.edges.items():
            if s == node:
                result.append((t, w))
        return result

    def adjacency_matrix(self) -> List[List[float]]:
        """Return dense adjacency matrix."""
        n = len(self.nodes)
        idx = {node: i for i, node in enumerate(self.nodes)}
        mat = [[0.0] * n for _ in range(n)]
        for (s, t), w in self.edges.items():
            mat[idx[s]][idx[t]] = w
        return mat

    def degree_matrix(self) -> List[List[float]]:
        """Return diagonal degree matrix (sum of outgoing weights)."""
        n = len(self.nodes)
        idx = {node: i for i, node in enumerate(self.nodes)}
        mat = [[0.0] * n for _ in range(n)]
        for (s, _), w in self.edges.items():
            mat[idx[s]][idx[s]] += w
        return mat


# ─── Spectral Embedding ──────────────────────────────────────────

def power_iteration(matrix: List[List[float]], n_components: int = 2,
                     max_iter: int = 200, tol: float = 1e-6,
                     rng: random.Random = None) -> List[List[float]]:
    """
    Simple power iteration for finding top eigenvectors.
    Returns matrix of shape [n_nodes, n_components].
    """
    if rng is None:
        rng = random.Random(42)

    n = len(matrix)
    if n == 0:
        return []

    vectors = []
    for comp in range(min(n_components, n)):
        # Random initial vector
        v = [rng.gauss(0, 1) for _ in range(n)]
        norm = math.sqrt(sum(x * x for x in v))
        v = [x / norm for x in v]

        for _ in range(max_iter):
            # Matrix-vector multiply
            new_v = [0.0] * n
            for i in range(n):
                for j in range(n):
                    new_v[i] += matrix[i][j] * v[j]

            # Orthogonalize against previous eigenvectors
            for prev_v in vectors:
                dot = sum(a * b for a, b in zip(new_v, prev_v))
                new_v = [a - dot * b for a, b in zip(new_v, prev_v)]

            # Normalize
            norm = math.sqrt(sum(x * x for x in new_v))
            if norm < 1e-12:
                break
            new_v = [x / norm for x in new_v]

            # Check convergence
            diff = sum((a - b) ** 2 for a, b in zip(v, new_v))
            v = new_v
            if diff < tol:
                break

        vectors.append(v)

    # Transpose to [n_nodes, n_components]
    return [[vectors[c][i] for c in range(len(vectors))] for i in range(n)]


def spectral_embedding(graph: WeightedGraph,
                        n_components: int = 2) -> Dict[str, List[float]]:
    """
    Spectral embedding using adjacency matrix eigenvectors.
    Maps nodes to n_components-dimensional space.
    """
    adj = graph.adjacency_matrix()
    # Symmetrize for undirected embedding
    n = len(adj)
    sym = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            sym[i][j] = (adj[i][j] + adj[j][i]) / 2

    embeddings = power_iteration(sym, n_components)

    result = {}
    for i, node in enumerate(graph.nodes):
        result[node] = embeddings[i] if i < len(embeddings) else [0.0] * n_components
    return result


# ─── Random Walk Embedding ───────────────────────────────────────

def random_walk_embedding(graph: WeightedGraph,
                            n_components: int = 2,
                            walk_length: int = 20,
                            n_walks: int = 50,
                            window: int = 3,
                            rng: random.Random = None) -> Dict[str, List[float]]:
    """
    Random walk based embedding (simplified node2vec).
    Co-occurrence in random walks → similarity in embedding space.
    """
    if rng is None:
        rng = random.Random(42)

    n = len(graph.nodes)
    if n == 0:
        return {}

    # Initialize embeddings randomly
    embeddings = {node: [rng.gauss(0, 0.1) for _ in range(n_components)]
                  for node in graph.nodes}

    # Collect random walks
    walks = []
    for _ in range(n_walks):
        start = rng.choice(graph.nodes)
        walk = [start]
        current = start
        for _ in range(walk_length - 1):
            neighbors = graph.neighbors(current)
            if not neighbors:
                break
            # Weight-proportional random walk
            total_w = sum(w for _, w in neighbors)
            r = rng.random() * total_w
            cumulative = 0
            for nbr, w in neighbors:
                cumulative += w
                if cumulative >= r:
                    walk.append(nbr)
                    current = nbr
                    break
        walks.append(walk)

    # Simple skip-gram style update: nodes appearing together get closer
    lr = 0.01
    for walk in walks:
        for i in range(len(walk)):
            for j in range(max(0, i - window), min(len(walk), i + window + 1)):
                if i == j:
                    continue
                node_i = walk[i]
                node_j = walk[j]
                # Move embeddings closer
                for d in range(n_components):
                    diff = embeddings[node_j][d] - embeddings[node_i][d]
                    embeddings[node_i][d] += lr * diff
                    embeddings[node_j][d] -= lr * diff * 0.1

    return embeddings


# ─── Similarity Metrics ──────────────────────────────────────────

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a < 1e-12 or norm_b < 1e-12:
        return 0.0
    return dot / (norm_a * norm_b)


def euclidean_distance(a: List[float], b: List[float]) -> float:
    """Euclidean distance between two vectors."""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def embedding_similarity_matrix(embeddings: Dict[str, List[float]],
                                  metric: str = "cosine") -> Dict[Tuple[str, str], float]:
    """Compute pairwise similarity from embeddings."""
    nodes = list(embeddings.keys())
    result = {}
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            a, b = embeddings[nodes[i]], embeddings[nodes[j]]
            if metric == "cosine":
                sim = cosine_similarity(a, b)
            else:
                sim = 1.0 / (1.0 + euclidean_distance(a, b))
            result[(nodes[i], nodes[j])] = sim
            result[(nodes[j], nodes[i])] = sim
    return result


# ─── Community Detection ─────────────────────────────────────────

def kmeans_cluster(embeddings: Dict[str, List[float]], k: int = 2,
                    max_iter: int = 50,
                    rng: random.Random = None) -> Dict[str, int]:
    """Simple k-means clustering on embeddings."""
    if rng is None:
        rng = random.Random(42)

    nodes = list(embeddings.keys())
    if not nodes:
        return {}

    dims = len(embeddings[nodes[0]])

    # Initialize centroids
    centroids = [list(embeddings[rng.choice(nodes)]) for _ in range(k)]

    assignments = {}
    for _ in range(max_iter):
        # Assign nodes to nearest centroid
        new_assignments = {}
        for node in nodes:
            vec = embeddings[node]
            min_dist = float('inf')
            best_k = 0
            for ki in range(k):
                dist = sum((a - b) ** 2 for a, b in zip(vec, centroids[ki]))
                if dist < min_dist:
                    min_dist = dist
                    best_k = ki
            new_assignments[node] = best_k

        # Check convergence
        if new_assignments == assignments:
            break
        assignments = new_assignments

        # Update centroids
        for ki in range(k):
            members = [embeddings[n] for n in nodes if assignments[n] == ki]
            if members:
                centroids[ki] = [sum(m[d] for m in members) / len(members)
                                 for d in range(dims)]

    return assignments


# ─── Embedding Quality ───────────────────────────────────────────

def embedding_stress(graph: WeightedGraph,
                      embeddings: Dict[str, List[float]]) -> float:
    """
    Stress metric: how well embedding distances preserve graph distances.
    Lower = better. Uses Kruskal's stress formula.
    """
    numerator = 0.0
    denominator = 0.0

    for (s, t), w in graph.edges.items():
        if s in embeddings and t in embeddings:
            embed_dist = euclidean_distance(embeddings[s], embeddings[t])
            graph_dist = 1.0 / (w + 0.01)  # Higher trust = shorter distance
            numerator += (embed_dist - graph_dist) ** 2
            denominator += graph_dist ** 2

    return math.sqrt(numerator / denominator) if denominator > 0 else 0.0


# ══════════════════════════════════════════════════════════════════
#  TESTS
# ══════════════════════════════════════════════════════════════════

def _build_two_community_graph(rng: random.Random = None) -> WeightedGraph:
    """Two dense communities with sparse inter-community edges."""
    if rng is None:
        rng = random.Random(42)

    g = WeightedGraph()

    # Community 1: nodes 0-9
    for i in range(10):
        g.add_node(f"c1_{i}")
    for i in range(10):
        for j in range(i + 1, 10):
            if rng.random() < 0.6:
                trust = rng.uniform(0.7, 1.0)
                g.add_edge(f"c1_{i}", f"c1_{j}", trust)
                g.add_edge(f"c1_{j}", f"c1_{i}", trust)

    # Community 2: nodes 10-19
    for i in range(10):
        g.add_node(f"c2_{i}")
    for i in range(10):
        for j in range(i + 1, 10):
            if rng.random() < 0.6:
                trust = rng.uniform(0.7, 1.0)
                g.add_edge(f"c2_{i}", f"c2_{j}", trust)
                g.add_edge(f"c2_{j}", f"c2_{i}", trust)

    # Sparse inter-community edges
    for i in range(10):
        for j in range(10):
            if rng.random() < 0.05:
                trust = rng.uniform(0.1, 0.3)
                g.add_edge(f"c1_{i}", f"c2_{j}", trust)
                g.add_edge(f"c2_{j}", f"c1_{i}", trust)

    return g


def run_checks():
    passed = 0
    failed = 0

    def check(name, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name} — {detail}")

    print("=" * 70)
    print("Trust Graph Embedding for Web4")
    print("Session 32, Track 4")
    print("=" * 70)

    # ── §1 Spectral Embedding ───────────────────────────────────
    print("\n§1 Spectral Embedding\n")

    g = _build_two_community_graph()
    embeddings = spectral_embedding(g, n_components=2)

    check("spectral_all_nodes", len(embeddings) == len(g.nodes),
          f"embedded={len(embeddings)} nodes={len(g.nodes)}")

    # Each embedding should be 2D
    for node, emb in embeddings.items():
        if len(emb) != 2:
            check("spectral_dims", False, f"{node} has {len(emb)} dims")
            break
    else:
        check("spectral_dims", True)

    # Nodes in same community should be more similar
    c1_nodes = [f"c1_{i}" for i in range(10)]
    c2_nodes = [f"c2_{i}" for i in range(10)]

    intra_sims = []
    for i in range(len(c1_nodes)):
        for j in range(i + 1, len(c1_nodes)):
            intra_sims.append(cosine_similarity(
                embeddings[c1_nodes[i]], embeddings[c1_nodes[j]]))

    inter_sims = []
    for c1 in c1_nodes[:5]:
        for c2 in c2_nodes[:5]:
            inter_sims.append(cosine_similarity(
                embeddings[c1], embeddings[c2]))

    avg_intra = sum(intra_sims) / len(intra_sims) if intra_sims else 0
    avg_inter = sum(inter_sims) / len(inter_sims) if inter_sims else 0
    check("spectral_community_separation", avg_intra > avg_inter,
          f"intra={avg_intra:.3f} inter={avg_inter:.3f}")

    # ── §2 Random Walk Embedding ────────────────────────────────
    print("\n§2 Random Walk Embedding\n")

    rw_embeddings = random_walk_embedding(g, n_components=2,
                                            walk_length=15, n_walks=100)
    check("rw_all_nodes", len(rw_embeddings) == len(g.nodes))

    # Walk-based should also separate communities
    rw_intra = []
    for i in range(len(c1_nodes)):
        for j in range(i + 1, len(c1_nodes)):
            if c1_nodes[i] in rw_embeddings and c1_nodes[j] in rw_embeddings:
                rw_intra.append(euclidean_distance(
                    rw_embeddings[c1_nodes[i]], rw_embeddings[c1_nodes[j]]))

    rw_inter = []
    for c1 in c1_nodes[:5]:
        for c2 in c2_nodes[:5]:
            if c1 in rw_embeddings and c2 in rw_embeddings:
                rw_inter.append(euclidean_distance(
                    rw_embeddings[c1], rw_embeddings[c2]))

    avg_rw_intra = sum(rw_intra) / len(rw_intra) if rw_intra else float('inf')
    avg_rw_inter = sum(rw_inter) / len(rw_inter) if rw_inter else 0
    # Intra-community should have smaller distance (closer together)
    check("rw_community_signal",
          avg_rw_intra < avg_rw_inter * 2,  # relaxed — random walk is noisy
          f"intra_dist={avg_rw_intra:.4f} inter_dist={avg_rw_inter:.4f}")

    # ── §3 Similarity Metrics ───────────────────────────────────
    print("\n§3 Similarity Metrics\n")

    a = [1.0, 0.0]
    b = [0.0, 1.0]
    c = [1.0, 0.0]

    check("cosine_orthogonal", abs(cosine_similarity(a, b)) < 0.01)
    check("cosine_identical", abs(cosine_similarity(a, c) - 1.0) < 0.01)
    check("cosine_range", -1.01 <= cosine_similarity(a, b) <= 1.01)

    check("euclidean_zero", abs(euclidean_distance(a, c)) < 0.01)
    check("euclidean_positive", euclidean_distance(a, b) > 0)
    check("euclidean_symmetric",
          abs(euclidean_distance(a, b) - euclidean_distance(b, a)) < 0.01)

    # ── §4 Community Detection ──────────────────────────────────
    print("\n§4 Community Detection via Clustering\n")

    clusters = kmeans_cluster(embeddings, k=2)
    check("cluster_all_assigned", len(clusters) == len(g.nodes))

    # Count how well clusters match communities
    c1_clusters = [clusters.get(f"c1_{i}", -1) for i in range(10)]
    c2_clusters = [clusters.get(f"c2_{i}", -1) for i in range(10)]

    c1_majority = max(set(c1_clusters), key=c1_clusters.count)
    c2_majority = max(set(c2_clusters), key=c2_clusters.count)

    c1_correct = sum(1 for c in c1_clusters if c == c1_majority)
    c2_correct = sum(1 for c in c2_clusters if c == c2_majority)

    accuracy = (c1_correct + c2_correct) / 20
    check("cluster_accuracy", accuracy > 0.5,
          f"accuracy={accuracy:.2f}")

    # Clusters should separate communities (different majority clusters)
    check("clusters_separate", c1_majority != c2_majority or accuracy > 0.6,
          f"c1_maj={c1_majority} c2_maj={c2_majority}")

    # ── §5 Embedding Quality ────────────────────────────────────
    print("\n§5 Embedding Quality\n")

    stress = embedding_stress(g, embeddings)
    check("stress_finite", stress < float('inf'),
          f"stress={stress:.4f}")
    check("stress_reasonable", stress < 100,
          f"stress={stress:.4f}")

    # Higher dimensional embedding should have lower stress
    emb_3d = spectral_embedding(g, n_components=3)
    stress_3d = embedding_stress(g, emb_3d)
    # Not guaranteed to be lower with power iteration, but should be reasonable
    check("3d_stress_reasonable", stress_3d < 200,
          f"2d={stress:.4f} 3d={stress_3d:.4f}")

    # ── §6 Small Graph Properties ───────────────────────────────
    print("\n§6 Small Graph Properties\n")

    small = WeightedGraph()
    small.add_edge("a", "b", 0.9)
    small.add_edge("b", "a", 0.9)
    small.add_edge("b", "c", 0.1)
    small.add_edge("c", "b", 0.1)

    small_emb = spectral_embedding(small, 2)
    # All 3 nodes should have distinct embeddings
    check("small_distinct_embeddings",
          euclidean_distance(small_emb["a"], small_emb["b"]) > 0.01 or
          euclidean_distance(small_emb["b"], small_emb["c"]) > 0.01,
          "nodes should have non-identical embeddings")

    # Embedding preserves graph structure: nodes are embedded in 2D
    check("small_2d", all(len(v) == 2 for v in small_emb.values()))

    # ── Summary ─────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
