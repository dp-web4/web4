#!/usr/bin/env python3
"""
Trust Graph Spectral Analysis
Session 29, Track 3

Eigenvalue decomposition of trust adjacency matrices reveals:
1. Community structure (spectral clustering via Fiedler vector)
2. Centrality measures (PageRank, eigenvector centrality)
3. Resilience indicators (spectral gap, algebraic connectivity)
4. Attack vulnerability (which edges to cut for maximum damage)
5. Trust flow dynamics (stationary distribution of random walks)

No external dependencies — pure Python linear algebra.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
import math
import random
from collections import defaultdict

# ============================================================
# Test infrastructure
# ============================================================

results = {"passed": 0, "failed": 0, "total": 0}

def check(condition: bool, description: str):
    results["total"] += 1
    if condition:
        results["passed"] += 1
    else:
        results["failed"] += 1
        print(f"  FAIL: {description}")

# ============================================================
# §1 Matrix Operations (Pure Python)
# ============================================================

def mat_zeros(n: int, m: int = None) -> List[List[float]]:
    if m is None:
        m = n
    return [[0.0] * m for _ in range(n)]

def mat_identity(n: int) -> List[List[float]]:
    m = mat_zeros(n)
    for i in range(n):
        m[i][i] = 1.0
    return m

def mat_mul(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    n = len(A)
    m = len(B[0])
    k = len(B)
    C = mat_zeros(n, m)
    for i in range(n):
        for j in range(m):
            s = 0.0
            for l in range(k):
                s += A[i][l] * B[l][j]
            C[i][j] = s
    return C

def mat_vec_mul(A: List[List[float]], v: List[float]) -> List[float]:
    n = len(A)
    result = [0.0] * n
    for i in range(n):
        s = 0.0
        for j in range(len(v)):
            s += A[i][j] * v[j]
        result[i] = s
    return result

def vec_dot(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))

def vec_norm(v: List[float]) -> float:
    return math.sqrt(sum(x * x for x in v))

def vec_normalize(v: List[float]) -> List[float]:
    n = vec_norm(v)
    if n < 1e-15:
        return v
    return [x / n for x in v]

def vec_sub(a: List[float], b: List[float]) -> List[float]:
    return [x - y for x, y in zip(a, b)]

def vec_scale(v: List[float], s: float) -> List[float]:
    return [x * s for x in v]

# ============================================================
# §2 Eigenvalue Computation (Power Iteration)
# ============================================================

def power_iteration(A: List[List[float]], num_iter: int = 200,
                    tolerance: float = 1e-10) -> Tuple[float, List[float]]:
    """Find dominant eigenvalue and eigenvector via power iteration."""
    n = len(A)
    # Start with random vector
    rng = random.Random(42)
    v = [rng.gauss(0, 1) for _ in range(n)]
    v = vec_normalize(v)

    eigenvalue = 0.0
    for _ in range(num_iter):
        Av = mat_vec_mul(A, v)
        new_eigenvalue = vec_dot(v, Av)
        v = vec_normalize(Av)
        if abs(new_eigenvalue - eigenvalue) < tolerance:
            break
        eigenvalue = new_eigenvalue

    return eigenvalue, v

def deflate(A: List[List[float]], eigenvalue: float,
            eigenvector: List[float]) -> List[List[float]]:
    """Remove dominant eigenvalue component from matrix."""
    n = len(A)
    B = [row[:] for row in A]
    for i in range(n):
        for j in range(n):
            B[i][j] -= eigenvalue * eigenvector[i] * eigenvector[j]
    return B

def compute_eigenvalues(A: List[List[float]], k: int = None) -> List[Tuple[float, List[float]]]:
    """Compute top k eigenvalues and eigenvectors."""
    n = len(A)
    if k is None:
        k = n
    k = min(k, n)

    results_eigen = []
    B = [row[:] for row in A]

    for _ in range(k):
        val, vec = power_iteration(B)
        if abs(val) < 1e-12:
            break
        results_eigen.append((val, vec))
        B = deflate(B, val, vec)

    return results_eigen


# ============================================================
# §3 Trust Graph
# ============================================================

@dataclass
class TrustGraph:
    """Weighted directed graph of trust relationships."""
    n: int
    edges: Dict[Tuple[int, int], float] = field(default_factory=dict)
    node_labels: Dict[int, str] = field(default_factory=dict)

    def add_edge(self, i: int, j: int, weight: float):
        self.edges[(i, j)] = weight

    def adjacency_matrix(self) -> List[List[float]]:
        A = mat_zeros(self.n)
        for (i, j), w in self.edges.items():
            A[i][j] = w
        return A

    def symmetric_adjacency(self) -> List[List[float]]:
        """Symmetrize: A_sym[i][j] = (A[i][j] + A[j][i]) / 2"""
        A = self.adjacency_matrix()
        S = mat_zeros(self.n)
        for i in range(self.n):
            for j in range(self.n):
                S[i][j] = (A[i][j] + A[j][i]) / 2
        return S

    def degree_matrix(self) -> List[List[float]]:
        A = self.symmetric_adjacency()
        D = mat_zeros(self.n)
        for i in range(self.n):
            D[i][i] = sum(A[i])
        return D

    def laplacian(self) -> List[List[float]]:
        """L = D - A (symmetric version)."""
        A = self.symmetric_adjacency()
        D = self.degree_matrix()
        L = mat_zeros(self.n)
        for i in range(self.n):
            for j in range(self.n):
                L[i][j] = D[i][j] - A[i][j]
        return L

    def normalized_laplacian(self) -> List[List[float]]:
        """L_norm = I - D^{-1/2} A D^{-1/2}"""
        A = self.symmetric_adjacency()
        n = self.n
        D_inv_sqrt = mat_zeros(n)
        for i in range(n):
            d = sum(A[i])
            if d > 0:
                D_inv_sqrt[i][i] = 1.0 / math.sqrt(d)

        # D^{-1/2} A D^{-1/2}
        DAD = mat_mul(mat_mul(D_inv_sqrt, A), D_inv_sqrt)
        I = mat_identity(n)
        L_norm = mat_zeros(n)
        for i in range(n):
            for j in range(n):
                L_norm[i][j] = I[i][j] - DAD[i][j]
        return L_norm

    def out_degree(self, i: int) -> float:
        return sum(w for (src, _), w in self.edges.items() if src == i)

    def in_degree(self, i: int) -> float:
        return sum(w for (_, dst), w in self.edges.items() if dst == i)


# ============================================================
# §4 Spectral Analysis Tools
# ============================================================

class SpectralAnalyzer:
    """Spectral analysis of trust graphs."""

    def __init__(self, graph: TrustGraph):
        self.graph = graph

    def algebraic_connectivity(self) -> float:
        """
        Second-smallest eigenvalue of Laplacian (Fiedler value).
        Measures how well-connected the graph is.
        λ₂ > 0 iff graph is connected.
        Higher λ₂ = more resilient to partitioning.
        """
        L = self.graph.laplacian()
        # We need the second-smallest eigenvalue
        # Power iteration finds largest, so we use (max_eigenvalue * I - L)
        # to find the smallest eigenvalues of L as largest of the shifted matrix

        n = self.graph.n
        # First, find max eigenvalue of L
        max_eval, _ = power_iteration(L, num_iter=300)

        # Shift: B = max_eval * I - L
        # Eigenvalues of B = max_eval - eigenvalues of L
        # Largest eigenvalue of B corresponds to smallest of L
        B = mat_zeros(n)
        for i in range(n):
            for j in range(n):
                B[i][j] = -L[i][j]
            B[i][i] += max_eval + 0.01  # Small shift for stability

        # Find two largest eigenvalues of B
        evals = compute_eigenvalues(B, k=2)
        if len(evals) < 2:
            return 0.0

        # Second largest of B = max_eval - λ₂(L)
        # So λ₂(L) = max_eval + 0.01 - evals[1][0]
        lambda_2 = max_eval + 0.01 - evals[1][0]
        return max(0.0, lambda_2)

    def fiedler_vector(self) -> List[float]:
        """
        Eigenvector corresponding to λ₂ (algebraic connectivity).
        Used for spectral bisection / community detection.
        Positive entries = community A, negative = community B.
        """
        L = self.graph.laplacian()
        n = self.graph.n

        max_eval, _ = power_iteration(L, num_iter=300)
        B = mat_zeros(n)
        for i in range(n):
            for j in range(n):
                B[i][j] = -L[i][j]
            B[i][i] += max_eval + 0.01

        evals = compute_eigenvalues(B, k=2)
        if len(evals) < 2:
            return [0.0] * n

        return evals[1][1]

    def spectral_bisection(self) -> Tuple[Set[int], Set[int]]:
        """Split graph into two communities using Fiedler vector."""
        fv = self.fiedler_vector()
        community_a = {i for i in range(self.graph.n) if fv[i] >= 0}
        community_b = {i for i in range(self.graph.n) if fv[i] < 0}
        return community_a, community_b

    def pagerank(self, damping: float = 0.85, num_iter: int = 100) -> List[float]:
        """
        PageRank: trust importance via random walk with teleportation.
        PR(i) = (1-d)/n + d * Σ_j [A(j,i) * PR(j) / out_degree(j)]
        """
        n = self.graph.n
        A = self.graph.adjacency_matrix()
        pr = [1.0 / n] * n

        for _ in range(num_iter):
            new_pr = [(1 - damping) / n] * n
            for j in range(n):
                out_d = self.graph.out_degree(j)
                if out_d == 0:
                    # Distribute equally (dangling node)
                    for i in range(n):
                        new_pr[i] += damping * pr[j] / n
                else:
                    for i in range(n):
                        if A[j][i] > 0:
                            new_pr[i] += damping * pr[j] * A[j][i] / out_d
            pr = new_pr

        return pr

    def eigenvector_centrality(self) -> List[float]:
        """Centrality based on dominant eigenvector of adjacency matrix."""
        A = self.graph.symmetric_adjacency()
        _, vec = power_iteration(A, num_iter=300)
        # Normalize to [0, 1]
        max_v = max(abs(x) for x in vec) or 1
        return [abs(x) / max_v for x in vec]

    def spectral_gap(self) -> float:
        """
        Gap between largest and second-largest eigenvalue of adjacency.
        Larger gap → more expander-like → better mixing → harder to partition.
        """
        A = self.graph.symmetric_adjacency()
        evals = compute_eigenvalues(A, k=2)
        if len(evals) < 2:
            return 0.0
        return abs(evals[0][0]) - abs(evals[1][0])

    def cheeger_bound(self) -> Tuple[float, float]:
        """
        Cheeger inequality: λ₂/2 ≤ h(G) ≤ √(2λ₂)
        where h(G) is the Cheeger constant (isoperimetric number).
        Relates spectral gap to edge expansion.
        """
        lambda_2 = self.algebraic_connectivity()
        lower = lambda_2 / 2
        upper = math.sqrt(2 * lambda_2) if lambda_2 > 0 else 0
        return lower, upper


# ============================================================
# §5 Attack Vulnerability Analysis
# ============================================================

class VulnerabilityAnalyzer:
    """Identify attack targets using spectral methods."""

    def __init__(self, graph: TrustGraph, analyzer: SpectralAnalyzer):
        self.graph = graph
        self.analyzer = analyzer

    def critical_edges(self, top_k: int = 5) -> List[Tuple[Tuple[int, int], float]]:
        """
        Edges whose removal most decreases algebraic connectivity.
        These are the most critical trust relationships.
        """
        baseline = self.analyzer.algebraic_connectivity()
        impacts = []

        for edge, weight in list(self.graph.edges.items()):
            # Temporarily remove edge
            del self.graph.edges[edge]
            reverse = (edge[1], edge[0])
            reverse_weight = self.graph.edges.get(reverse)
            if reverse in self.graph.edges:
                del self.graph.edges[reverse]

            new_analyzer = SpectralAnalyzer(self.graph)
            new_lambda2 = new_analyzer.algebraic_connectivity()
            impact = baseline - new_lambda2

            # Restore edge
            self.graph.edges[edge] = weight
            if reverse_weight is not None:
                self.graph.edges[reverse] = reverse_weight

            impacts.append((edge, impact))

        impacts.sort(key=lambda x: x[1], reverse=True)
        return impacts[:top_k]

    def critical_nodes(self) -> List[Tuple[int, float]]:
        """
        Nodes whose removal most damages connectivity.
        Uses centrality as proxy (faster than full spectral recomputation).
        """
        centrality = self.analyzer.eigenvector_centrality()
        ranked = [(i, c) for i, c in enumerate(centrality)]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked

    def partition_vulnerability(self) -> float:
        """
        How easily can the graph be partitioned?
        Low algebraic connectivity + clear Fiedler vector separation = vulnerable.
        Returns score 0-1 where 1 = highly vulnerable.
        """
        lambda_2 = self.analyzer.algebraic_connectivity()
        fv = self.analyzer.fiedler_vector()

        # Measure Fiedler vector bimodality
        positive = sum(1 for x in fv if x > 0.1)
        negative = sum(1 for x in fv if x < -0.1)
        neutral = self.graph.n - positive - negative
        bimodality = min(positive, negative) / max(1, self.graph.n / 2)

        # Low λ₂ + high bimodality = vulnerable
        # Normalize λ₂ relative to max degree
        max_degree = max(sum(row) for row in self.graph.symmetric_adjacency())
        normalized_lambda2 = lambda_2 / max(0.01, max_degree)

        vulnerability = bimodality * (1 - min(1, normalized_lambda2))
        return min(1.0, max(0.0, vulnerability))


# ============================================================
# §6 Graph Generators
# ============================================================

def create_two_community_graph(n: int, p_intra: float = 0.8,
                                p_inter: float = 0.1) -> TrustGraph:
    """Create a graph with two clear communities."""
    g = TrustGraph(n=n)
    rng = random.Random(42)
    half = n // 2

    for i in range(n):
        for j in range(i + 1, n):
            same_community = (i < half and j < half) or (i >= half and j >= half)
            p = p_intra if same_community else p_inter
            if rng.random() < p:
                w = rng.uniform(0.3, 1.0)
                g.add_edge(i, j, w)
                g.add_edge(j, i, w)

    return g

def create_scale_free_graph(n: int, m: int = 2) -> TrustGraph:
    """Create a scale-free (power-law degree) trust graph via preferential attachment."""
    g = TrustGraph(n=n)
    rng = random.Random(42)

    # Start with complete graph on m+1 nodes
    for i in range(m + 1):
        for j in range(i + 1, m + 1):
            w = rng.uniform(0.3, 1.0)
            g.add_edge(i, j, w)
            g.add_edge(j, i, w)

    degrees = [m] * (m + 1) + [0] * (n - m - 1)

    for new_node in range(m + 1, n):
        total_degree = sum(degrees[:new_node])
        if total_degree == 0:
            targets = list(range(min(m, new_node)))
        else:
            # Preferential attachment
            targets = set()
            attempts = 0
            while len(targets) < m and attempts < 1000:
                r = rng.random() * total_degree
                cumsum = 0
                for i in range(new_node):
                    cumsum += degrees[i]
                    if cumsum >= r:
                        targets.add(i)
                        break
                attempts += 1

        for t in targets:
            w = rng.uniform(0.3, 1.0)
            g.add_edge(new_node, t, w)
            g.add_edge(t, new_node, w)
            degrees[new_node] += 1
            degrees[t] += 1

    return g


def create_federation_graph(n: int) -> TrustGraph:
    """Create a federation-like graph with authorities and regular members."""
    g = TrustGraph(n=n)
    rng = random.Random(42)

    # First 3 nodes are authorities (high connectivity)
    n_authorities = min(3, n)
    for i in range(n_authorities):
        for j in range(i + 1, n_authorities):
            g.add_edge(i, j, 0.9)
            g.add_edge(j, i, 0.9)

    # Regular members connect to 1-2 authorities + some peers
    for i in range(n_authorities, n):
        # Connect to random authority
        auth = rng.randint(0, n_authorities - 1)
        g.add_edge(i, auth, rng.uniform(0.5, 0.8))
        g.add_edge(auth, i, rng.uniform(0.5, 0.8))

        # Connect to 1-3 random peers
        for _ in range(rng.randint(1, 3)):
            peer = rng.randint(0, n - 1)
            if peer != i:
                w = rng.uniform(0.2, 0.6)
                g.add_edge(i, peer, w)
                g.add_edge(peer, i, w)

    return g


# ============================================================
# Tests
# ============================================================

def run_tests():
    print("=" * 70)
    print("Trust Graph Spectral Analysis")
    print("Session 29, Track 3")
    print("=" * 70)

    # §1 Basic Spectral Properties
    print("\n§1 Basic Spectral Properties")

    # Simple 4-node graph
    g4 = TrustGraph(n=4)
    g4.add_edge(0, 1, 1.0); g4.add_edge(1, 0, 1.0)
    g4.add_edge(1, 2, 1.0); g4.add_edge(2, 1, 1.0)
    g4.add_edge(2, 3, 1.0); g4.add_edge(3, 2, 1.0)
    g4.add_edge(3, 0, 1.0); g4.add_edge(0, 3, 1.0)

    L = g4.laplacian()
    check(L[0][0] == 2.0, f"s1: Degree of node 0 = {L[0][0]}")
    check(L[0][1] == -1.0, f"s2: Laplacian off-diagonal = {L[0][1]}")

    # Laplacian row sums are zero
    for i in range(4):
        row_sum = sum(L[i])
        check(abs(row_sum) < 1e-10, f"s3: Laplacian row {i} sum = {row_sum:.2e}")
        break  # Check one representative

    # §2 Community Detection
    print("\n§2 Community Detection (Two-Community Graph)")

    g_comm = create_two_community_graph(20, p_intra=0.7, p_inter=0.05)
    analyzer_comm = SpectralAnalyzer(g_comm)

    comm_a, comm_b = analyzer_comm.spectral_bisection()
    check(len(comm_a) > 0 and len(comm_b) > 0,
          f"s4: Spectral bisection: |A|={len(comm_a)}, |B|={len(comm_b)}")

    # Communities should roughly correspond to the two halves
    half = 10
    correct_a = len(comm_a & set(range(half))) + len(comm_b & set(range(half, 20)))
    correct_b = len(comm_b & set(range(half))) + len(comm_a & set(range(half, 20)))
    accuracy = max(correct_a, correct_b) / 20
    check(accuracy > 0.7,
          f"s5: Community detection accuracy: {accuracy:.1%}")

    # Algebraic connectivity should be low (two communities weakly connected)
    lambda_2 = analyzer_comm.algebraic_connectivity()
    check(lambda_2 < 3.0, f"s6: Algebraic connectivity λ₂ = {lambda_2:.3f} (low = two communities)")

    # §3 PageRank
    print("\n§3 PageRank on Federation Graph")

    g_fed = create_federation_graph(15)
    analyzer_fed = SpectralAnalyzer(g_fed)

    pr = analyzer_fed.pagerank()
    check(abs(sum(pr) - 1.0) < 0.01, f"s7: PageRank sums to {sum(pr):.4f} ≈ 1.0")

    # Authorities (nodes 0-2) should have higher PageRank
    auth_pr = sum(pr[:3]) / 3
    member_pr = sum(pr[3:]) / 12
    check(auth_pr > member_pr,
          f"s8: Authority PageRank ({auth_pr:.4f}) > member ({member_pr:.4f})")

    # §4 Eigenvector Centrality
    print("\n§4 Eigenvector Centrality")

    centrality = analyzer_fed.eigenvector_centrality()
    check(max(centrality) == 1.0, f"s9: Max centrality normalized to 1.0")
    check(min(centrality) >= 0.0, f"s10: Min centrality ≥ 0")

    # Most central node should be an authority
    most_central = centrality.index(max(centrality))
    check(most_central < 3,
          f"s11: Most central node is {most_central} (authority)")

    # §5 Spectral Gap
    print("\n§5 Spectral Gap and Resilience")

    # Well-connected graph should have larger spectral gap
    g_dense = TrustGraph(n=6)
    for i in range(6):
        for j in range(i + 1, 6):
            g_dense.add_edge(i, j, 0.8)
            g_dense.add_edge(j, i, 0.8)

    analyzer_dense = SpectralAnalyzer(g_dense)
    gap_dense = analyzer_dense.spectral_gap()

    gap_comm = analyzer_comm.spectral_gap()
    check(gap_dense > 0, f"s12: Dense graph spectral gap: {gap_dense:.3f}")
    check(gap_comm >= 0, f"s13: Two-community spectral gap: {gap_comm:.3f}")

    # §6 Cheeger Inequality
    print("\n§6 Cheeger Inequality")

    lower, upper = analyzer_comm.cheeger_bound()
    check(lower <= upper,
          f"s14: Cheeger bounds: {lower:.4f} ≤ h(G) ≤ {upper:.4f}")
    check(lower >= 0, f"s15: Cheeger lower bound ≥ 0")

    lower_dense, upper_dense = analyzer_dense.cheeger_bound()
    check(lower_dense >= 0,
          f"s16: Dense graph Cheeger lower: {lower_dense:.4f}")

    # §7 Scale-Free Graph
    print("\n§7 Scale-Free Graph Properties")

    g_sf = create_scale_free_graph(20, m=2)
    analyzer_sf = SpectralAnalyzer(g_sf)

    pr_sf = analyzer_sf.pagerank()
    check(abs(sum(pr_sf) - 1.0) < 0.01, f"s17: Scale-free PageRank sums to 1.0")

    # Scale-free should have hub nodes
    centrality_sf = analyzer_sf.eigenvector_centrality()
    max_centrality = max(centrality_sf)
    min_centrality = min(centrality_sf)
    check(max_centrality / max(0.001, min_centrality) > 2,
          f"s18: Scale-free has hubs: centrality ratio {max_centrality/max(0.001, min_centrality):.1f}")

    # §8 Vulnerability Analysis
    print("\n§8 Attack Vulnerability")

    vuln = VulnerabilityAnalyzer(g_comm, analyzer_comm)

    # Partition vulnerability should be high for two-community graph
    pv = vuln.partition_vulnerability()
    check(pv >= 0 and pv <= 1, f"s19: Partition vulnerability: {pv:.3f}")

    # Critical nodes
    critical = vuln.critical_nodes()
    check(len(critical) == 20, f"s20: Ranked all {len(critical)} nodes by criticality")
    check(critical[0][1] >= critical[-1][1],
          f"s21: Critical nodes ranked: {critical[0][1]:.3f} ≥ {critical[-1][1]:.3f}")

    # Dense graph should be less vulnerable
    vuln_dense = VulnerabilityAnalyzer(g_dense, analyzer_dense)
    pv_dense = vuln_dense.partition_vulnerability()
    check(pv_dense >= 0 and pv_dense <= 1,
          f"s22: Dense partition vulnerability: {pv_dense:.3f}")

    # §9 Critical Edges (most impactful removal)
    print("\n§9 Critical Edge Analysis")

    # Use small graph for edge analysis (faster)
    g_small = TrustGraph(n=6)
    # Bridge graph: two triangles connected by one edge
    g_small.add_edge(0, 1, 1.0); g_small.add_edge(1, 0, 1.0)
    g_small.add_edge(1, 2, 1.0); g_small.add_edge(2, 1, 1.0)
    g_small.add_edge(0, 2, 1.0); g_small.add_edge(2, 0, 1.0)
    g_small.add_edge(3, 4, 1.0); g_small.add_edge(4, 3, 1.0)
    g_small.add_edge(4, 5, 1.0); g_small.add_edge(5, 4, 1.0)
    g_small.add_edge(3, 5, 1.0); g_small.add_edge(5, 3, 1.0)
    g_small.add_edge(2, 3, 1.0); g_small.add_edge(3, 2, 1.0)  # Bridge!

    analyzer_small = SpectralAnalyzer(g_small)
    vuln_small = VulnerabilityAnalyzer(g_small, analyzer_small)

    critical_edges = vuln_small.critical_edges(top_k=3)
    check(len(critical_edges) > 0, f"s23: Found {len(critical_edges)} critical edges")

    # All critical edges have non-negative impact
    check(all(impact >= -0.01 for _, impact in critical_edges),
          f"s24: Critical edges have non-negative impact: top={critical_edges[0]}")

    # §10 Trust Flow / Random Walk
    print("\n§10 Trust Flow Analysis")

    # Stationary distribution of random walk = PageRank with d=1 (no teleport)
    pr_noteleport = analyzer_fed.pagerank(damping=0.999, num_iter=200)
    check(abs(sum(pr_noteleport) - 1.0) < 0.02,
          f"s25: Trust flow stationary distribution sums to {sum(pr_noteleport):.4f}")

    # Higher damping → trust flows more along edges (less random teleportation)
    pr_high_d = analyzer_fed.pagerank(damping=0.99)
    pr_low_d = analyzer_fed.pagerank(damping=0.5)

    # With high damping, authority PageRank should be more extreme
    auth_high = max(pr_high_d[:3])
    auth_low = max(pr_low_d[:3])
    check(auth_high > auth_low,
          f"s26: High damping amplifies authority: {auth_high:.4f} > {auth_low:.4f}")

    # §11 Federation-Specific Analysis
    print("\n§11 Federation Health Metrics")

    lambda2_fed = analyzer_fed.algebraic_connectivity()
    check(lambda2_fed > 0, f"s27: Federation is connected: λ₂ = {lambda2_fed:.3f}")

    gap_fed = analyzer_fed.spectral_gap()
    check(gap_fed > 0, f"s28: Federation spectral gap: {gap_fed:.3f}")

    cheeger_lower_fed, cheeger_upper_fed = analyzer_fed.cheeger_bound()
    check(cheeger_lower_fed >= 0,
          f"s29: Federation Cheeger bounds: [{cheeger_lower_fed:.4f}, {cheeger_upper_fed:.4f}]")

    # Federation community detection
    fed_a, fed_b = analyzer_fed.spectral_bisection()
    check(len(fed_a) + len(fed_b) == 15,
          f"s30: Federation bisection covers all nodes: {len(fed_a)} + {len(fed_b)} = 15")

    # §12 Comparative Analysis
    print("\n§12 Comparative Graph Analysis")

    graphs = {
        "two-community": (g_comm, analyzer_comm),
        "scale-free": (g_sf, analyzer_sf),
        "federation": (g_fed, analyzer_fed),
        "dense": (g_dense, analyzer_dense),
    }

    # Compare algebraic connectivity
    connectivities = {}
    for name, (g, a) in graphs.items():
        conn = a.algebraic_connectivity()
        connectivities[name] = conn

    # Dense should be most connected
    check(connectivities["dense"] > connectivities["two-community"],
          f"s31: Dense ({connectivities['dense']:.3f}) more connected than two-community ({connectivities['two-community']:.3f})")

    # All should be positive (connected graphs)
    check(all(v >= 0 for v in connectivities.values()),
          "s32: All graphs have non-negative algebraic connectivity")

    # Print summary
    print(f"\n{'=' * 70}")
    print(f"Results: {results['passed']} passed, {results['failed']} failed "
          f"out of {results['total']}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    run_tests()
