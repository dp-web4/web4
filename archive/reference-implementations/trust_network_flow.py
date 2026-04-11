"""
Trust Network Flow for Web4
Session 33, Track 2

Max-flow / min-cut analysis applied to trust networks:
- Trust capacity as edge weights in a directed graph
- Ford-Fulkerson / Edmonds-Karp for max-flow computation
- Min-cut identifies weakest trust bottleneck
- Trust path enumeration (all simple paths)
- Bottleneck path (max-min trust path)
- Trust flow conservation verification
- Augmenting path traces for transparency
- Multi-commodity trust flow (parallel trust types)
- Vulnerability detection via cut analysis
"""

from collections import defaultdict, deque
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
import heapq


# ─── Graph Representation ────────────────────────────────────────

@dataclass
class TrustEdge:
    src: str
    dst: str
    capacity: float       # max trust flow
    flow: float = 0.0     # current flow

    @property
    def residual(self) -> float:
        return self.capacity - self.flow


class TrustFlowGraph:
    """Directed trust flow graph with residual capacity tracking."""

    def __init__(self):
        self.edges: List[TrustEdge] = []
        self.graph: Dict[str, List[int]] = defaultdict(list)  # node -> edge indices
        self.nodes: Set[str] = set()

    def add_edge(self, src: str, dst: str, capacity: float) -> int:
        """Add a directed edge. Returns the index of the forward edge."""
        idx = len(self.edges)
        self.edges.append(TrustEdge(src, dst, capacity))
        self.edges.append(TrustEdge(dst, src, 0.0))  # reverse edge (residual)
        self.graph[src].append(idx)
        self.graph[dst].append(idx + 1)
        self.nodes.add(src)
        self.nodes.add(dst)
        return idx

    def reset_flow(self):
        """Reset all flows to 0."""
        for e in self.edges:
            e.flow = 0.0

    def total_capacity(self, src: str) -> float:
        return sum(self.edges[i].capacity for i in self.graph[src]
                   if self.edges[i].src == src)


# ─── Edmonds-Karp (BFS-based Ford-Fulkerson) ────────────────────

def bfs_find_path(g: TrustFlowGraph, source: str, sink: str) -> Optional[List[int]]:
    """BFS in residual graph to find augmenting path. Returns list of edge indices."""
    visited = {source}
    parent_edge: Dict[str, int] = {}
    queue = deque([source])

    while queue:
        node = queue.popleft()
        if node == sink:
            # Reconstruct path
            path = []
            cur = sink
            while cur != source:
                eidx = parent_edge[cur]
                path.append(eidx)
                cur = g.edges[eidx].src
            return path[::-1]

        for eidx in g.graph[node]:
            e = g.edges[eidx]
            if e.dst not in visited and e.residual > 1e-9:
                visited.add(e.dst)
                parent_edge[e.dst] = eidx
                queue.append(e.dst)

    return None


def max_flow_edmonds_karp(g: TrustFlowGraph, source: str, sink: str) -> float:
    """
    Compute maximum trust flow from source to sink using Edmonds-Karp.
    Modifies flow in-place. Returns total max flow.
    """
    g.reset_flow()
    total = 0.0

    while True:
        path = bfs_find_path(g, source, sink)
        if path is None:
            break

        # Find bottleneck capacity along path
        bottleneck = min(g.edges[i].residual for i in path)

        # Augment flow along path
        for i in path:
            g.edges[i].flow += bottleneck
            g.edges[i ^ 1].flow -= bottleneck  # reverse edge

        total += bottleneck

    return total


# ─── Min-Cut Detection ───────────────────────────────────────────

def find_min_cut(g: TrustFlowGraph, source: str, sink: str) -> Tuple[float, Set[str], List[Tuple[str, str, float]]]:
    """
    After running max flow, find the min cut.
    Returns (cut_value, reachable_from_source, cut_edges).
    """
    # Find nodes reachable from source in residual graph
    reachable = {source}
    queue = deque([source])
    while queue:
        node = queue.popleft()
        for eidx in g.graph[node]:
            e = g.edges[eidx]
            if e.dst not in reachable and e.residual > 1e-9:
                reachable.add(e.dst)
                queue.append(e.dst)

    # Cut edges: from reachable to non-reachable with saturated capacity
    cut_edges = []
    cut_value = 0.0
    for e in g.edges:
        if e.src in reachable and e.dst not in reachable and e.capacity > 0:
            cut_edges.append((e.src, e.dst, e.capacity))
            cut_value += e.capacity

    return cut_value, reachable, cut_edges


# ─── Bottleneck Path (Max-Min Trust) ────────────────────────────

def max_bottleneck_path(nodes: Set[str],
                         adj: Dict[str, List[Tuple[str, float]]],
                         source: str, sink: str) -> Tuple[float, List[str]]:
    """
    Find the path that maximizes the minimum edge trust.
    Uses a modified Dijkstra with max-min objective.
    Returns (bottleneck_value, path).
    """
    # dist[v] = max bottleneck trust to reach v from source
    dist: Dict[str, float] = {n: 0.0 for n in nodes}
    dist[source] = float('inf')
    prev: Dict[str, Optional[str]] = {n: None for n in nodes}

    # Max-heap: (-bottleneck, node)
    heap = [(-float('inf'), source)]
    visited = set()

    while heap:
        neg_b, u = heapq.heappop(heap)
        b = -neg_b
        if u in visited:
            continue
        visited.add(u)
        if u == sink:
            break

        for v, capacity in adj.get(u, []):
            new_b = min(b, capacity)
            if new_b > dist[v]:
                dist[v] = new_b
                prev[v] = u
                heapq.heappush(heap, (-new_b, v))

    # Reconstruct path
    if dist[sink] == 0.0:
        return 0.0, []

    path = []
    cur = sink
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()

    return dist[sink], path


# ─── All Simple Paths (for trust enumeration) ───────────────────

def all_simple_paths(adj: Dict[str, List[Tuple[str, float]]],
                      source: str, sink: str,
                      max_paths: int = 20) -> List[List[str]]:
    """Enumerate all simple trust paths (DFS, depth-limited)."""
    paths = []
    stack = [(source, [source], {source})]

    while stack and len(paths) < max_paths:
        node, path, visited = stack.pop()
        if node == sink:
            paths.append(path)
            continue
        for neighbor, _ in adj.get(node, []):
            if neighbor not in visited:
                stack.append((neighbor, path + [neighbor], visited | {neighbor}))

    return paths


def path_trust(adj: Dict[str, List[Tuple[str, float]]], path: List[str]) -> float:
    """Compute trust along a path (product of edge trusts)."""
    t = 1.0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        for neighbor, capacity in adj.get(u, []):
            if neighbor == v:
                t *= capacity
                break
        else:
            return 0.0
    return t


# ─── Multi-Commodity Trust Flow ──────────────────────────────────

@dataclass
class CommodityFlow:
    """A single trust commodity (e.g., a specific trust type)."""
    name: str
    source: str
    sink: str
    demand: float           # required flow
    achieved: float = 0.0

    @property
    def satisfied(self) -> bool:
        return self.achieved >= self.demand - 1e-9


def solve_multi_commodity(
    commodities: List[CommodityFlow],
    capacity: Dict[Tuple[str, str], float]
) -> Dict[str, float]:
    """
    Greedy multi-commodity flow: solve each commodity sequentially,
    sharing capacity. Returns achieved flow per commodity.
    """
    remaining_cap = dict(capacity)  # mutable copy

    for comm in commodities:
        # Build flow graph with remaining capacity
        g = TrustFlowGraph()
        nodes = set()
        for (u, v), cap in remaining_cap.items():
            nodes.add(u)
            nodes.add(v)
        for (u, v), cap in remaining_cap.items():
            if cap > 1e-9:
                g.add_edge(u, v, cap)

        # Solve single commodity
        flow = max_flow_edmonds_karp(g, comm.source, comm.sink)
        comm.achieved = min(flow, comm.demand)

        # Deduct used capacity
        for e in g.edges:
            if e.capacity > 0 and e.flow > 0:
                key = (e.src, e.dst)
                if key in remaining_cap:
                    remaining_cap[key] = max(0.0, remaining_cap[key] - e.flow)

    return {c.name: c.achieved for c in commodities}


# ─── Vulnerability Analysis ──────────────────────────────────────

@dataclass
class VulnerabilityReport:
    """Min-cut vulnerability analysis for a trust network."""
    min_cut_value: float
    cut_edges: List[Tuple[str, str, float]]
    choke_points: List[str]   # nodes appearing in multiple cut edges
    risk_level: str

    @property
    def num_cut_edges(self) -> int:
        return len(self.cut_edges)


def vulnerability_analysis(g: TrustFlowGraph,
                             source: str, sink: str) -> VulnerabilityReport:
    """
    Analyze trust network vulnerability via min-cut.
    """
    total = max_flow_edmonds_karp(g, source, sink)
    cut_value, reachable, cut_edges = find_min_cut(g, source, sink)

    # Identify choke points (nodes in multiple cut edges)
    node_count: Dict[str, int] = defaultdict(int)
    for u, v, _ in cut_edges:
        node_count[u] += 1
        node_count[v] += 1
    choke_points = [n for n, cnt in node_count.items() if cnt > 1]

    # Risk: based on number of cut edges (single point of failure)
    if len(cut_edges) == 1:
        risk = "CRITICAL"
    elif len(cut_edges) <= 2:
        risk = "HIGH"
    elif len(cut_edges) <= 4:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return VulnerabilityReport(cut_value, cut_edges, choke_points, risk)


# ─── Trust Flow Conservation ─────────────────────────────────────

def verify_flow_conservation(g: TrustFlowGraph, source: str, sink: str) -> Dict[str, bool]:
    """
    Verify Kirchhoff's flow conservation for all intermediate nodes.
    For each non-source/sink node: sum(inflow) == sum(outflow).
    """
    results = {}
    inflow: Dict[str, float] = defaultdict(float)
    outflow: Dict[str, float] = defaultdict(float)

    for e in g.edges:
        if e.flow > 0 and e.capacity > 0:  # forward edges only
            outflow[e.src] += e.flow
            inflow[e.dst] += e.flow

    for node in g.nodes:
        if node in (source, sink):
            continue
        results[node] = abs(inflow[node] - outflow[node]) < 1e-9

    return results


# ══════════════════════════════════════════════════════════════════
#  TESTS
# ══════════════════════════════════════════════════════════════════

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
    print("Trust Network Flow for Web4")
    print("Session 33, Track 2")
    print("=" * 70)

    # ── §1 Basic Max-Flow ────────────────────────────────────────
    print("\n§1 Basic Max-Flow\n")

    g1 = TrustFlowGraph()
    # Simple 2-path network
    # S -> A -> T (capacity 3)
    # S -> B -> T (capacity 2)
    g1.add_edge("S", "A", 3.0)
    g1.add_edge("A", "T", 3.0)
    g1.add_edge("S", "B", 2.0)
    g1.add_edge("B", "T", 2.0)

    flow = max_flow_edmonds_karp(g1, "S", "T")
    check("basic_max_flow", abs(flow - 5.0) < 1e-9, f"flow={flow}")

    # Single bottleneck
    g2 = TrustFlowGraph()
    g2.add_edge("S", "M", 10.0)
    g2.add_edge("M", "T", 4.0)  # bottleneck
    g2.add_edge("M", "T2", 6.0)
    g2.add_edge("S", "T2", 3.0)
    flow2 = max_flow_edmonds_karp(g2, "S", "T")
    check("bottleneck_flow", abs(flow2 - 4.0) < 1e-9, f"flow2={flow2}")

    # Diamond network
    g3 = TrustFlowGraph()
    g3.add_edge("S", "A", 0.8)
    g3.add_edge("S", "B", 0.7)
    g3.add_edge("A", "T", 0.6)
    g3.add_edge("B", "T", 0.9)
    g3.add_edge("A", "B", 0.5)
    flow3 = max_flow_edmonds_karp(g3, "S", "T")
    check("diamond_flow", flow3 <= 1.5 + 1e-9, f"flow3={flow3}")
    check("diamond_flow_positive", flow3 > 0.0)

    # ── §2 Min-Cut ───────────────────────────────────────────────
    print("\n§2 Min-Cut Analysis\n")

    g4 = TrustFlowGraph()
    g4.add_edge("S", "A", 3.0)
    g4.add_edge("S", "B", 2.0)
    g4.add_edge("A", "T", 1.5)  # bottleneck on A side
    g4.add_edge("B", "T", 2.5)
    g4.add_edge("A", "B", 1.0)

    mf = max_flow_edmonds_karp(g4, "S", "T")
    cut_val, reachable, cut_edges = find_min_cut(g4, "S", "T")

    check("max_flow_equals_min_cut", abs(mf - cut_val) < 1e-9,
          f"mf={mf}, cut={cut_val}")
    check("sink_not_reachable", "T" not in reachable)
    check("source_reachable", "S" in reachable)
    check("cut_edges_positive", len(cut_edges) > 0)

    # All cut edges go from reachable to non-reachable
    check("cut_edges_direction", all(u in reachable and v not in reachable
                                      for u, v, _ in cut_edges))

    # ── §3 Bottleneck Path ───────────────────────────────────────
    print("\n§3 Bottleneck Path (Max-Min Trust)\n")

    nodes = {"S", "A", "B", "C", "T"}
    adj = {
        "S": [("A", 0.9), ("B", 0.5)],
        "A": [("C", 0.8), ("T", 0.4)],
        "B": [("C", 0.6), ("T", 0.7)],
        "C": [("T", 0.95)],
    }

    bottleneck, path = max_bottleneck_path(nodes, adj, "S", "T")
    # Best path: S->A->C->T has bottleneck min(0.9, 0.8, 0.95) = 0.8
    # S->B->T has bottleneck min(0.5, 0.7) = 0.5
    check("bottleneck_path_found", len(path) > 0)
    check("bottleneck_value", abs(bottleneck - 0.8) < 1e-9, f"bottleneck={bottleneck}")
    check("path_starts_source", path[0] == "S" if path else False)
    check("path_ends_sink", path[-1] == "T" if path else False)

    # Direct high-trust path
    nodes2 = {"S", "T"}
    adj2 = {"S": [("T", 0.99)]}
    b2, p2 = max_bottleneck_path(nodes2, adj2, "S", "T")
    check("direct_path_bottleneck", abs(b2 - 0.99) < 1e-9)

    # No path
    nodes3 = {"S", "T"}
    adj3: Dict[str, List[Tuple[str, float]]] = {"S": []}
    b3, p3 = max_bottleneck_path(nodes3, adj3, "S", "T")
    check("no_path", b3 == 0.0 and p3 == [])

    # ── §4 All Simple Paths ──────────────────────────────────────
    print("\n§4 All Simple Paths\n")

    adj4 = {
        "S": [("A", 0.9), ("B", 0.8)],
        "A": [("T", 0.7)],
        "B": [("T", 0.6)],
    }
    paths = all_simple_paths(adj4, "S", "T")
    check("num_paths", len(paths) == 2, f"paths={paths}")
    check("path_lengths", all(len(p) == 3 for p in paths))

    # Path trust calculation
    pt1 = path_trust(adj4, ["S", "A", "T"])
    check("path_trust_1", abs(pt1 - 0.9 * 0.7) < 1e-9, f"pt1={pt1}")

    pt2 = path_trust(adj4, ["S", "B", "T"])
    check("path_trust_2", abs(pt2 - 0.8 * 0.6) < 1e-9, f"pt2={pt2}")

    # Best path is S->A->T
    trusts = [(p, path_trust(adj4, p)) for p in paths]
    best = max(trusts, key=lambda x: x[1])
    check("best_path", best[0] == ["S", "A", "T"])

    # ── §5 Flow Conservation ─────────────────────────────────────
    print("\n§5 Flow Conservation\n")

    g5 = TrustFlowGraph()
    g5.add_edge("S", "A", 5.0)
    g5.add_edge("S", "B", 3.0)
    g5.add_edge("A", "T", 4.0)
    g5.add_edge("B", "T", 3.0)
    g5.add_edge("A", "B", 2.0)
    max_flow_edmonds_karp(g5, "S", "T")

    conservation = verify_flow_conservation(g5, "S", "T")
    check("conservation_all_nodes", all(conservation.values()),
          f"violations={[n for n, ok in conservation.items() if not ok]}")
    check("conservation_a", conservation.get("A", True))
    check("conservation_b", conservation.get("B", True))

    # ── §6 Vulnerability Analysis ────────────────────────────────
    print("\n§6 Vulnerability Analysis\n")

    # Single-edge bottleneck = critical vulnerability
    g_crit = TrustFlowGraph()
    g_crit.add_edge("S", "M", 100.0)
    g_crit.add_edge("M", "T", 0.1)   # single choke point
    report = vulnerability_analysis(g_crit, "S", "T")
    check("critical_vulnerability", report.risk_level == "CRITICAL", f"risk={report.risk_level}")
    check("single_cut_edge", report.num_cut_edges == 1)

    # Well-connected network = lower risk
    g_robust = TrustFlowGraph()
    for i in range(5):
        g_robust.add_edge("S", f"M{i}", 1.0)
        g_robust.add_edge(f"M{i}", "T", 1.0)
    report2 = vulnerability_analysis(g_robust, "S", "T")
    check("low_risk", report2.risk_level in ("LOW", "MEDIUM"), f"risk2={report2.risk_level}")
    check("multiple_cut_edges", report2.num_cut_edges >= 5)

    # ── §7 Multi-Commodity Flow ──────────────────────────────────
    print("\n§7 Multi-Commodity Trust Flow\n")

    # Two trust types sharing capacity
    capacity = {
        ("S1", "M"): 3.0,
        ("S2", "M"): 3.0,
        ("M", "T1"): 2.0,
        ("M", "T2"): 2.0,
    }
    commodities = [
        CommodityFlow("talent_trust", "S1", "T1", demand=2.0),
        CommodityFlow("training_trust", "S2", "T2", demand=2.0),
    ]
    achieved = solve_multi_commodity(commodities, capacity)

    check("commodity_1_satisfied", commodities[0].satisfied,
          f"achieved={commodities[0].achieved}")
    check("commodity_2_attempted", achieved.get("training_trust", 0) >= 0)
    check("all_commodities_tracked", len(achieved) == 2)

    # Single commodity, simple case
    cap2 = {("A", "B"): 5.0, ("B", "C"): 3.0}
    comm2 = [CommodityFlow("flow", "A", "C", demand=3.0)]
    res2 = solve_multi_commodity(comm2, cap2)
    check("single_commodity_satisfied", comm2[0].satisfied, f"achieved={comm2[0].achieved}")

    # ── §8 Trust Capacity Scaling ────────────────────────────────
    print("\n§8 Trust Capacity Scaling\n")

    # Test that doubling capacity doubles max flow (linear scaling)
    g_base = TrustFlowGraph()
    g_base.add_edge("S", "A", 2.0)
    g_base.add_edge("A", "T", 2.0)
    f_base = max_flow_edmonds_karp(g_base, "S", "T")

    g_double = TrustFlowGraph()
    g_double.add_edge("S", "A", 4.0)
    g_double.add_edge("A", "T", 4.0)
    f_double = max_flow_edmonds_karp(g_double, "S", "T")

    check("capacity_scales_linearly", abs(f_double - 2 * f_base) < 1e-9,
          f"base={f_base}, double={f_double}")

    # Adding a parallel path increases max flow
    g_parallel = TrustFlowGraph()
    g_parallel.add_edge("S", "A", 2.0)
    g_parallel.add_edge("A", "T", 2.0)
    g_parallel.add_edge("S", "B", 3.0)
    g_parallel.add_edge("B", "T", 3.0)
    f_parallel = max_flow_edmonds_karp(g_parallel, "S", "T")
    check("parallel_increases_flow", f_parallel > f_base)
    check("parallel_additive", abs(f_parallel - 5.0) < 1e-9, f"parallel={f_parallel}")

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
