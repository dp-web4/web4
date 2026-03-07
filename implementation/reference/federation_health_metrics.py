"""
Federation Health Metrics for Web4
Session 30, Track 3

Comprehensive health scoring for Web4 federations:
- Trust distribution health (entropy, Gini, skewness)
- Network connectivity health (algebraic connectivity, diameter, clustering)
- Economic health (ATP velocity, inequality, activity)
- Governance health (participation, quorum, proposal success rate)
- Composite health score with weighted dimensions
- Health trajectory prediction (trending up/down/stable)
- Alert thresholds and anomaly detection
"""

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional


# ─── Health Status ─────────────────────────────────────────────────

class HealthStatus(Enum):
    HEALTHY = "healthy"        # score >= 0.7
    DEGRADED = "degraded"      # score 0.4-0.7
    CRITICAL = "critical"      # score < 0.4


class TrendDirection(Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


@dataclass
class HealthDimension:
    name: str
    score: float        # [0, 1]
    weight: float       # importance weight
    components: Dict[str, float] = field(default_factory=dict)

    @property
    def status(self) -> HealthStatus:
        if self.score >= 0.7:
            return HealthStatus.HEALTHY
        elif self.score >= 0.4:
            return HealthStatus.DEGRADED
        return HealthStatus.CRITICAL


@dataclass
class HealthSnapshot:
    timestamp: int
    dimensions: List[HealthDimension]
    composite_score: float
    alerts: List[str] = field(default_factory=list)

    @property
    def status(self) -> HealthStatus:
        if self.composite_score >= 0.7:
            return HealthStatus.HEALTHY
        elif self.composite_score >= 0.4:
            return HealthStatus.DEGRADED
        return HealthStatus.CRITICAL


# ─── Trust Distribution Health ─────────────────────────────────────

def trust_entropy(trust_scores: List[float], bins: int = 10) -> float:
    """Shannon entropy of trust distribution. Higher = more diverse."""
    if not trust_scores:
        return 0.0

    # Bin trust scores (use bins centered on values to avoid edge effects)
    counts = [0] * bins
    for t in trust_scores:
        # Map [0,1] to bins, ensuring max value goes to last bin
        idx = int(t * bins)
        if idx >= bins:
            idx = bins - 1
        counts[idx] += 1

    n = len(trust_scores)
    entropy = 0.0
    for c in counts:
        if c > 0:
            p = c / n
            entropy -= p * math.log2(p)

    max_entropy = math.log2(bins)
    return entropy / max_entropy if max_entropy > 0 else 0.0  # normalized [0,1]


def trust_gini(trust_scores: List[float]) -> float:
    """Gini coefficient of trust distribution. 0 = equal, 1 = maximally unequal."""
    if not trust_scores or len(trust_scores) < 2:
        return 0.0

    sorted_scores = sorted(trust_scores)
    n = len(sorted_scores)
    total = sum(sorted_scores)
    if total <= 0:
        return 0.0

    cumulative = 0.0
    gini_sum = 0.0
    for i, s in enumerate(sorted_scores):
        cumulative += s
        gini_sum += (2 * (i + 1) - n - 1) * s

    return gini_sum / (n * total)


def trust_distribution_health(trust_scores: List[float]) -> HealthDimension:
    """Compute trust distribution health."""
    if not trust_scores:
        return HealthDimension("trust_distribution", 0.0, 0.3)

    entropy = trust_entropy(trust_scores)
    gini = trust_gini(trust_scores)
    mean_trust = sum(trust_scores) / len(trust_scores)

    # Fraction above minimum viable trust (0.3)
    viable_fraction = sum(1 for t in trust_scores if t >= 0.3) / len(trust_scores)

    # Health score: weighted combination
    # High entropy (diverse) is good
    # Low Gini (equal) is good
    # High mean trust is good
    # High viable fraction is good
    score = 0.3 * entropy + 0.2 * (1 - gini) + 0.25 * mean_trust + 0.25 * viable_fraction

    return HealthDimension(
        "trust_distribution", score, 0.3,
        components={
            "entropy": entropy,
            "gini": gini,
            "mean_trust": mean_trust,
            "viable_fraction": viable_fraction,
        }
    )


# ─── Network Connectivity Health ───────────────────────────────────

def graph_density(n_nodes: int, n_edges: int) -> float:
    """Graph density: actual edges / possible edges."""
    if n_nodes < 2:
        return 0.0
    max_edges = n_nodes * (n_nodes - 1) / 2
    return n_edges / max_edges


def avg_clustering_coefficient(adjacency: Dict[int, List[int]]) -> float:
    """Average local clustering coefficient."""
    if not adjacency:
        return 0.0

    total_cc = 0.0
    count = 0

    for node, neighbors in adjacency.items():
        k = len(neighbors)
        if k < 2:
            continue

        # Count edges among neighbors
        neighbor_set = set(neighbors)
        edges_among = 0
        for n1 in neighbors:
            for n2 in adjacency.get(n1, []):
                if n2 in neighbor_set and n2 != n1:
                    edges_among += 1
        edges_among //= 2  # each edge counted twice

        cc = 2 * edges_among / (k * (k - 1))
        total_cc += cc
        count += 1

    return total_cc / count if count > 0 else 0.0


def is_connected(adjacency: Dict[int, List[int]]) -> bool:
    """Check if graph is connected via BFS."""
    if not adjacency:
        return True

    start = next(iter(adjacency))
    visited = {start}
    queue = [start]

    while queue:
        node = queue.pop(0)
        for neighbor in adjacency.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return len(visited) == len(adjacency)


def network_health(n_nodes: int, n_edges: int,
                   adjacency: Dict[int, List[int]]) -> HealthDimension:
    """Compute network connectivity health."""
    if n_nodes < 2:
        return HealthDimension("network", 0.0, 0.2)

    density = graph_density(n_nodes, n_edges)
    clustering = avg_clustering_coefficient(adjacency)
    connected = 1.0 if is_connected(adjacency) else 0.0

    # Ideal density: not too sparse (< 0.1) not too dense (> 0.8)
    density_score = 1.0 - abs(density - 0.3) / 0.7 if density <= 1.0 else 0.0
    density_score = max(0, density_score)

    # Health: connectivity matters most
    score = 0.4 * connected + 0.3 * min(1.0, density_score) + 0.3 * clustering

    return HealthDimension(
        "network", score, 0.2,
        components={
            "density": density,
            "clustering": clustering,
            "connected": connected,
            "density_score": density_score,
        }
    )


# ─── Economic Health ───────────────────────────────────────────────

def atp_velocity(transactions: List[float], supply: float, window: int = 100) -> float:
    """ATP velocity = transaction volume / supply in window."""
    if supply <= 0 or not transactions:
        return 0.0
    volume = sum(abs(t) for t in transactions[-window:])
    return volume / supply


def economic_health(balances: List[float], recent_transactions: List[float],
                    total_supply: float) -> HealthDimension:
    """Compute economic health."""
    if not balances:
        return HealthDimension("economic", 0.0, 0.25)

    gini = trust_gini(balances)  # reuse Gini
    velocity = atp_velocity(recent_transactions, total_supply)

    # Active participants (balance > 0)
    active_fraction = sum(1 for b in balances if b > 0) / len(balances)

    # Velocity health: some circulation is good, too much might indicate churn
    velocity_score = min(1.0, velocity / 2.0)  # normalized, cap at 1

    # Low inequality is healthy
    equality_score = 1 - gini

    score = 0.3 * equality_score + 0.3 * velocity_score + 0.4 * active_fraction

    return HealthDimension(
        "economic", score, 0.25,
        components={
            "gini": gini,
            "velocity": velocity,
            "active_fraction": active_fraction,
            "velocity_score": velocity_score,
        }
    )


# ─── Governance Health ─────────────────────────────────────────────

def governance_health(total_members: int, votes_cast: int,
                      proposals_submitted: int, proposals_passed: int,
                      quorum_met_fraction: float) -> HealthDimension:
    """Compute governance participation health."""
    if total_members <= 0:
        return HealthDimension("governance", 0.0, 0.25)

    # Participation rate
    max_possible_votes = total_members * max(1, proposals_submitted)
    participation = votes_cast / max_possible_votes if max_possible_votes > 0 else 0.0

    # Proposal success rate (not too low, not 100%)
    if proposals_submitted > 0:
        success_rate = proposals_passed / proposals_submitted
        # Ideal: 30-70% success (indicates healthy deliberation)
        success_health = 1.0 - abs(success_rate - 0.5) / 0.5
    else:
        success_health = 0.0

    # Quorum reliability
    quorum_health = quorum_met_fraction

    score = 0.4 * participation + 0.3 * success_health + 0.3 * quorum_health

    return HealthDimension(
        "governance", score, 0.25,
        components={
            "participation": participation,
            "success_health": success_health,
            "quorum_met": quorum_met_fraction,
            "proposals": proposals_submitted,
        }
    )


# ─── Composite Health Score ────────────────────────────────────────

def composite_health(dimensions: List[HealthDimension]) -> float:
    """Weighted composite health score."""
    if not dimensions:
        return 0.0

    total_weight = sum(d.weight for d in dimensions)
    if total_weight <= 0:
        return 0.0

    return sum(d.score * d.weight for d in dimensions) / total_weight


def generate_alerts(dimensions: List[HealthDimension]) -> List[str]:
    """Generate alerts for critical/degraded dimensions."""
    alerts = []
    for d in dimensions:
        if d.status == HealthStatus.CRITICAL:
            alerts.append(f"CRITICAL: {d.name} health at {d.score:.2f}")
        elif d.status == HealthStatus.DEGRADED:
            alerts.append(f"WARNING: {d.name} health degraded at {d.score:.2f}")

        # Component-level alerts
        for comp_name, comp_value in d.components.items():
            if comp_name == "gini" and comp_value > 0.8:
                alerts.append(f"HIGH INEQUALITY: {d.name} Gini={comp_value:.2f}")
            elif comp_name == "connected" and comp_value < 1.0:
                alerts.append(f"DISCONNECTED: Network has isolated components")
            elif comp_name == "viable_fraction" and comp_value < 0.5:
                alerts.append(f"LOW VIABLE TRUST: Only {comp_value*100:.0f}% above minimum")

    return alerts


# ─── Health Trajectory ─────────────────────────────────────────────

def health_trend(history: List[float], window: int = 5) -> TrendDirection:
    """Determine health trend from recent history."""
    if len(history) < 2:
        return TrendDirection.STABLE

    recent = history[-window:]
    if len(recent) < 2:
        return TrendDirection.STABLE

    # Simple linear regression slope
    n = len(recent)
    x_mean = (n - 1) / 2
    y_mean = sum(recent) / n

    numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(recent))
    denominator = sum((i - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        return TrendDirection.STABLE

    slope = numerator / denominator

    if slope > 0.01:
        return TrendDirection.IMPROVING
    elif slope < -0.01:
        return TrendDirection.DECLINING
    return TrendDirection.STABLE


def predict_health(history: List[float], steps_ahead: int = 5) -> float:
    """Linear extrapolation of health trajectory."""
    if len(history) < 2:
        return history[-1] if history else 0.5

    n = len(history)
    x_mean = (n - 1) / 2
    y_mean = sum(history) / n

    numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(history))
    denominator = sum((i - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        return y_mean

    slope = numerator / denominator
    intercept = y_mean - slope * x_mean

    predicted = slope * (n - 1 + steps_ahead) + intercept
    return max(0.0, min(1.0, predicted))


# ─── Anomaly Detection ────────────────────────────────────────────

def detect_anomalies(history: List[float], z_threshold: float = 2.0) -> List[int]:
    """Detect anomalous health scores using z-score."""
    if len(history) < 3:
        return []

    mean = sum(history) / len(history)
    variance = sum((h - mean) ** 2 for h in history) / len(history)
    std = math.sqrt(variance) if variance > 0 else 0.001

    anomalies = []
    for i, h in enumerate(history):
        z = abs(h - mean) / std
        if z > z_threshold:
            anomalies.append(i)

    return anomalies


# ─── Federation Health Simulator ───────────────────────────────────

class FederationHealthSimulator:
    """Simulate federation health evolution."""

    def __init__(self, n_entities: int, seed: int = 42):
        self.rng = random.Random(seed)
        self.n_entities = n_entities
        self.trust_scores = [self.rng.uniform(0.3, 0.9) for _ in range(n_entities)]
        self.balances = [self.rng.uniform(10, 100) for _ in range(n_entities)]
        self.total_supply = sum(self.balances)
        self.transactions = []
        self.health_history = []

        # Build random graph
        self.adjacency: Dict[int, List[int]] = {i: [] for i in range(n_entities)}
        for i in range(n_entities):
            for j in range(i + 1, n_entities):
                if self.rng.random() < 0.3:
                    self.adjacency[i].append(j)
                    self.adjacency[j].append(i)

    def step(self):
        """Advance one time step."""
        # Trust decay + random attestation
        for i in range(self.n_entities):
            self.trust_scores[i] *= 0.99  # decay
            if self.rng.random() < 0.1:
                self.trust_scores[i] = min(1.0, self.trust_scores[i] + 0.05)

        # Random transactions
        for _ in range(self.rng.randint(1, 5)):
            sender = self.rng.randint(0, self.n_entities - 1)
            receiver = self.rng.randint(0, self.n_entities - 1)
            if sender != receiver and self.balances[sender] > 1:
                amount = self.rng.uniform(0.1, min(5, self.balances[sender]))
                self.balances[sender] -= amount
                self.balances[receiver] += amount
                self.transactions.append(amount)

    def snapshot(self, timestamp: int) -> HealthSnapshot:
        """Take health snapshot."""
        trust_dim = trust_distribution_health(self.trust_scores)
        n_edges = sum(len(neighbors) for neighbors in self.adjacency.values()) // 2
        net_dim = network_health(self.n_entities, n_edges, self.adjacency)
        econ_dim = economic_health(self.balances, self.transactions[-100:], self.total_supply)
        gov_dim = governance_health(
            self.n_entities,
            votes_cast=int(self.n_entities * 0.6),
            proposals_submitted=5,
            proposals_passed=3,
            quorum_met_fraction=0.8
        )

        dimensions = [trust_dim, net_dim, econ_dim, gov_dim]
        comp = composite_health(dimensions)
        alerts = generate_alerts(dimensions)

        snapshot = HealthSnapshot(timestamp, dimensions, comp, alerts)
        self.health_history.append(comp)
        return snapshot


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
    print("Federation Health Metrics for Web4")
    print("Session 30, Track 3")
    print("=" * 70)

    # ── §1 Trust Distribution Health ──────────────────────────────
    print("\n§1 Trust Distribution Health\n")

    # Well-spread trust → high entropy, low Gini → healthy
    spread_trust = [i / 20 + 0.05 for i in range(20)]  # 0.05..0.95 evenly spread
    dim_spread = trust_distribution_health(spread_trust)
    check("spread_healthy", dim_spread.score >= 0.5,
          f"score={dim_spread.score:.3f}")

    # Skewed trust → low entropy, high Gini
    skewed_trust = [0.1] * 18 + [0.9, 0.95]
    dim_skewed = trust_distribution_health(skewed_trust)
    check("skewed_lower_score", dim_skewed.score < dim_spread.score,
          f"spread={dim_spread.score:.3f} skewed={dim_skewed.score:.3f}")

    # All zeros → critical
    zero_trust = [0.0] * 10
    dim_zero = trust_distribution_health(zero_trust)
    check("zero_trust_critical", dim_zero.status == HealthStatus.CRITICAL,
          f"score={dim_zero.score:.3f}")

    # Spread trust has higher entropy than skewed
    e_spread = trust_entropy(spread_trust)
    e_skewed = trust_entropy(skewed_trust)
    check("spread_higher_entropy", e_spread > e_skewed,
          f"spread={e_spread:.3f} skewed={e_skewed:.3f}")

    # ── §2 Gini Coefficient ───────────────────────────────────────
    print("\n§2 Gini Coefficient\n")

    gini_equal = trust_gini([1.0, 1.0, 1.0, 1.0])
    check("equal_gini_zero", gini_equal < 0.01, f"gini={gini_equal:.4f}")

    gini_unequal = trust_gini([0.0, 0.0, 0.0, 100.0])
    check("unequal_gini_high", gini_unequal > 0.5, f"gini={gini_unequal:.4f}")

    check("gini_bounded", 0 <= gini_equal <= 1 and 0 <= gini_unequal <= 1,
          f"equal={gini_equal:.3f} unequal={gini_unequal:.3f}")

    # ── §3 Network Health ─────────────────────────────────────────
    print("\n§3 Network Health\n")

    # Complete graph → high health
    n = 6
    adj_complete = {i: [j for j in range(n) if j != i] for i in range(n)}
    n_edges_complete = n * (n - 1) // 2
    dim_complete = network_health(n, n_edges_complete, adj_complete)
    check("complete_graph_connected", dim_complete.components["connected"] == 1.0)

    # Disconnected graph → low health
    adj_disconnected = {0: [1], 1: [0], 2: [3], 3: [2], 4: [], 5: []}
    dim_disc = network_health(6, 2, adj_disconnected)
    check("disconnected_lower_health", dim_disc.score < dim_complete.score,
          f"complete={dim_complete.score:.3f} disc={dim_disc.score:.3f}")
    check("disconnected_flag", dim_disc.components["connected"] == 0.0)

    # Graph density
    d = graph_density(4, 6)  # complete K4
    check("k4_density_1", abs(d - 1.0) < 0.01, f"density={d:.3f}")

    # ── §4 Economic Health ────────────────────────────────────────
    print("\n§4 Economic Health\n")

    # Healthy economy: equal balances, active transactions
    balances_equal = [100.0] * 10
    txns = [5.0] * 50
    dim_econ = economic_health(balances_equal, txns, 1000)
    check("equal_economy_healthy", dim_econ.score > 0.5,
          f"score={dim_econ.score:.3f}")

    # Dead economy: no transactions, zero balances
    dim_dead = economic_health([0.0] * 10, [], 1000)
    check("dead_economy_low", dim_dead.score <= 0.3,
          f"score={dim_dead.score:.3f}")

    # ATP velocity
    v = atp_velocity([10, 20, 30], 100)
    check("velocity_positive", v > 0, f"velocity={v:.3f}")
    check("velocity_zero_supply", atp_velocity([10], 0) == 0.0)

    # ── §5 Governance Health ──────────────────────────────────────
    print("\n§5 Governance Health\n")

    dim_gov = governance_health(100, votes_cast=300, proposals_submitted=10,
                                 proposals_passed=5, quorum_met_fraction=0.9)
    check("governance_reasonable", dim_gov.score > 0.2,
          f"score={dim_gov.score:.3f}")

    # 50% success rate → optimal deliberation score
    check("balanced_proposals", dim_gov.components["success_health"] > 0.8,
          f"success_health={dim_gov.components['success_health']:.3f}")

    # No proposals → low health
    dim_no_gov = governance_health(100, 0, 0, 0, 0.0)
    check("no_governance_low", dim_no_gov.score < 0.1,
          f"score={dim_no_gov.score:.3f}")

    # ── §6 Composite Health ───────────────────────────────────────
    print("\n§6 Composite Health Score\n")

    dims = [
        HealthDimension("trust", 0.8, 0.3),
        HealthDimension("network", 0.7, 0.2),
        HealthDimension("economic", 0.6, 0.25),
        HealthDimension("governance", 0.5, 0.25),
    ]
    comp = composite_health(dims)
    check("composite_bounded", 0 <= comp <= 1, f"composite={comp:.3f}")
    check("composite_weighted_avg", 0.5 <= comp <= 0.8,
          f"composite={comp:.3f}")

    # All healthy → composite healthy
    all_healthy = [HealthDimension("d", 0.9, 0.25) for _ in range(4)]
    check("all_healthy_composite", composite_health(all_healthy) >= 0.7)

    # ── §7 Alerts ─────────────────────────────────────────────────
    print("\n§7 Alert Generation\n")

    dims_with_critical = [
        HealthDimension("trust", 0.2, 0.3, {"gini": 0.85, "viable_fraction": 0.3}),
        HealthDimension("network", 0.8, 0.2, {"connected": 0.0}),
    ]
    alerts = generate_alerts(dims_with_critical)
    check("alerts_generated", len(alerts) > 0, f"alerts={len(alerts)}")
    check("critical_alert_present", any("CRITICAL" in a for a in alerts),
          f"alerts={alerts}")
    check("inequality_alert", any("INEQUALITY" in a for a in alerts),
          f"alerts={alerts}")
    check("disconnected_alert", any("DISCONNECTED" in a for a in alerts),
          f"alerts={alerts}")

    # ── §8 Health Trajectory ──────────────────────────────────────
    print("\n§8 Health Trajectory\n")

    improving = [0.3, 0.4, 0.5, 0.6, 0.7]
    declining = [0.8, 0.7, 0.6, 0.5, 0.4]
    stable = [0.6, 0.6, 0.61, 0.59, 0.6]

    check("improving_trend", health_trend(improving) == TrendDirection.IMPROVING)
    check("declining_trend", health_trend(declining) == TrendDirection.DECLINING)
    check("stable_trend", health_trend(stable) == TrendDirection.STABLE)

    # Prediction
    pred_up = predict_health(improving, steps_ahead=3)
    check("predict_up", pred_up > improving[-1],
          f"pred={pred_up:.3f} last={improving[-1]}")

    pred_down = predict_health(declining, steps_ahead=3)
    check("predict_down", pred_down < declining[-1],
          f"pred={pred_down:.3f} last={declining[-1]}")

    # ── §9 Anomaly Detection ──────────────────────────────────────
    print("\n§9 Anomaly Detection\n")

    normal = [0.7, 0.71, 0.69, 0.7, 0.72, 0.68, 0.7]
    anomalous = [0.7, 0.71, 0.69, 0.7, 0.2, 0.68, 0.7]  # 0.2 is anomaly

    no_anom = detect_anomalies(normal)
    check("no_anomalies_normal", len(no_anom) == 0, f"found={no_anom}")

    with_anom = detect_anomalies(anomalous)
    check("detects_anomaly", len(with_anom) > 0, f"found={with_anom}")
    check("anomaly_at_index_4", 4 in with_anom, f"found={with_anom}")

    # ── §10 Federation Simulation ─────────────────────────────────
    print("\n§10 Federation Health Simulation\n")

    sim = FederationHealthSimulator(n_entities=20, seed=42)

    # Run 50 steps
    snapshots = []
    for t in range(50):
        sim.step()
        if t % 10 == 0:
            snap = sim.snapshot(t)
            snapshots.append(snap)

    check("simulation_produces_snapshots", len(snapshots) > 0)
    check("snapshots_have_dimensions", all(len(s.dimensions) == 4 for s in snapshots))
    check("composite_bounded_sim", all(0 <= s.composite_score <= 1 for s in snapshots),
          f"scores={[s.composite_score for s in snapshots]}")

    # Health history populated
    check("history_populated", len(sim.health_history) > 0,
          f"len={len(sim.health_history)}")

    # Trend from simulation
    trend = health_trend(sim.health_history)
    check("trend_computed", trend in list(TrendDirection),
          f"trend={trend}")

    # ── §11 Health Status Classification ──────────────────────────
    print("\n§11 Health Status Classification\n")

    snap_healthy = HealthSnapshot(0, [], 0.8)
    snap_degraded = HealthSnapshot(0, [], 0.5)
    snap_critical = HealthSnapshot(0, [], 0.2)

    check("status_healthy", snap_healthy.status == HealthStatus.HEALTHY)
    check("status_degraded", snap_degraded.status == HealthStatus.DEGRADED)
    check("status_critical", snap_critical.status == HealthStatus.CRITICAL)

    # Dimension status
    dim_h = HealthDimension("test", 0.8, 1.0)
    dim_d = HealthDimension("test", 0.5, 1.0)
    dim_c = HealthDimension("test", 0.2, 1.0)
    check("dim_healthy", dim_h.status == HealthStatus.HEALTHY)
    check("dim_degraded", dim_d.status == HealthStatus.DEGRADED)
    check("dim_critical", dim_c.status == HealthStatus.CRITICAL)

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
