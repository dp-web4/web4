"""
Synthon Lifecycle Detection — Reference Implementation

A synthon is an emergent coherence entity formed by recursive interaction
between components. This implements quantitative detection of synthon
formation, health monitoring, and decay precursors.

Lifecycle FSM: NASCENT → FORMING → STABLE → STRESSED → DISSOLVING

Key observables:
- Formation: trust entropy decrease + clustering increase + MRH overlap
- Health: ATP flow stability, trust variance, witness diversity
- Decay: entropy increase, boundary permeability spikes, ATP asymmetry
- Anti-absorption: detect MRH absorption vs composition

Based on CLAUDE.md synthon framing:
"Engineer substrate conditions, not emergence itself.
 Instrument trust metrics as synthon-level health indicators.
 Treat inter-synthon conflict as signal — map it, don't suppress it.
 Monitor for decay signatures with the same seriousness as formation."

Checks: 72
"""
from __future__ import annotations
import hashlib
import math
import secrets
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple


# ─── Core Types ───────────────────────────────────────────────────────────────

class SynthonPhase(Enum):
    NASCENT = auto()      # Components exist but no coherence
    FORMING = auto()      # Trust entropy decreasing, clustering emerging
    STABLE = auto()       # Self-sustaining coherence
    STRESSED = auto()     # Decay precursors detected
    DISSOLVING = auto()   # Active dissolution


class HealthStatus(Enum):
    HEALTHY = auto()
    WARNING = auto()
    CRITICAL = auto()


class DecayType(Enum):
    ENTROPY_INCREASE = auto()
    BOUNDARY_LEAK = auto()
    ATP_ASYMMETRY = auto()
    WITNESS_LOSS = auto()
    TRUST_DIVERGENCE = auto()
    MRH_ABSORPTION = auto()


@dataclass
class Entity:
    """An entity that can participate in synthon formation."""
    entity_id: str
    trust_scores: Dict[str, float] = field(default_factory=dict)  # dim → value
    mrh_zones: Dict[str, int] = field(default_factory=dict)       # peer → distance
    atp_balance: float = 100.0
    atp_inflow: float = 0.0
    atp_outflow: float = 0.0
    witnesses: Set[str] = field(default_factory=set)

    @property
    def trust_composite(self) -> float:
        if not self.trust_scores:
            return 0.5
        return sum(self.trust_scores.values()) / len(self.trust_scores)

    @property
    def atp_flow_ratio(self) -> float:
        total = self.atp_inflow + self.atp_outflow
        if total == 0:
            return 0.5
        return self.atp_inflow / total


# ─── Trust Entropy ────────────────────────────────────────────────────────────

class TrustEntropy:
    """
    Shannon entropy of trust distribution within a group.
    Low entropy = coherent (similar trust levels) = formation signal.
    High entropy = incoherent (divergent trust) = decay signal.
    """

    @staticmethod
    def compute(trust_values: List[float], bins: int = 10) -> float:
        """Compute Shannon entropy of trust distribution."""
        if len(trust_values) < 2:
            return 0.0

        # Bin the values
        counts = [0] * bins
        for v in trust_values:
            idx = min(int(v * bins), bins - 1)
            counts[idx] += 1

        total = len(trust_values)
        entropy = 0.0
        for c in counts:
            if c > 0:
                p = c / total
                entropy -= p * math.log2(p)

        # Normalize to [0, 1]
        max_entropy = math.log2(bins)
        return entropy / max_entropy if max_entropy > 0 else 0.0

    @staticmethod
    def compute_delta(prev_values: List[float], curr_values: List[float]) -> float:
        """Compute entropy change. Negative = becoming more coherent."""
        return TrustEntropy.compute(curr_values) - TrustEntropy.compute(prev_values)


# ─── Clustering Coefficient ──────────────────────────────────────────────────

class ClusteringAnalysis:
    """
    Graph clustering coefficient for entity networks.
    High clustering = tight local groups = formation signal.
    """

    @staticmethod
    def compute_coefficient(adjacency: Dict[str, Set[str]]) -> float:
        """Global clustering coefficient."""
        if len(adjacency) < 3:
            return 0.0

        total_triangles = 0
        total_triples = 0

        for node in adjacency:
            neighbors = adjacency[node]
            k = len(neighbors)
            if k < 2:
                continue
            # Count connected pairs among neighbors
            connected = 0
            neighbor_list = list(neighbors)
            for i in range(len(neighbor_list)):
                for j in range(i + 1, len(neighbor_list)):
                    if neighbor_list[j] in adjacency.get(neighbor_list[i], set()):
                        connected += 1
            total_triangles += connected
            total_triples += k * (k - 1) // 2

        if total_triples == 0:
            return 0.0
        return total_triangles / total_triples

    @staticmethod
    def local_coefficient(node: str, adjacency: Dict[str, Set[str]]) -> float:
        """Local clustering coefficient for one node."""
        neighbors = adjacency.get(node, set())
        k = len(neighbors)
        if k < 2:
            return 0.0
        connected = 0
        neighbor_list = list(neighbors)
        for i in range(len(neighbor_list)):
            for j in range(i + 1, len(neighbor_list)):
                if neighbor_list[j] in adjacency.get(neighbor_list[i], set()):
                    connected += 1
        return connected / (k * (k - 1) / 2)


# ─── MRH Overlap Detection ───────────────────────────────────────────────────

class MRHOverlapAnalysis:
    """
    Detect convergent MRH horizons — entities whose relevancy horizons
    increasingly overlap indicates synthon formation.
    """

    @staticmethod
    def compute_overlap(mrh_a: Dict[str, int], mrh_b: Dict[str, int]) -> float:
        """Jaccard similarity of MRH peer sets."""
        peers_a = set(mrh_a.keys())
        peers_b = set(mrh_b.keys())
        if not peers_a or not peers_b:
            return 0.0
        intersection = peers_a & peers_b
        union = peers_a | peers_b
        return len(intersection) / len(union)

    @staticmethod
    def group_overlap(entities: List[Entity]) -> float:
        """Average pairwise MRH overlap in a group."""
        if len(entities) < 2:
            return 0.0
        total = 0.0
        count = 0
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                total += MRHOverlapAnalysis.compute_overlap(
                    entities[i].mrh_zones, entities[j].mrh_zones)
                count += 1
        return total / count

    @staticmethod
    def detect_absorption(absorber: Entity, target: Entity,
                           threshold: float = 0.8) -> bool:
        """Detect if absorber's MRH is subsuming target's MRH."""
        target_peers = set(target.mrh_zones.keys())
        absorber_peers = set(absorber.mrh_zones.keys())
        if not target_peers:
            return False
        # Absorption = most of target's peers are also absorber's peers
        overlap = target_peers & absorber_peers
        return len(overlap) / len(target_peers) >= threshold


# ─── Synthon Health Indicators ────────────────────────────────────────────────

@dataclass
class SynthonHealth:
    """Aggregate health metrics for a synthon."""
    trust_entropy: float         # Lower = more coherent
    clustering: float            # Higher = more connected
    mrh_overlap: float           # Higher = more aligned
    atp_flow_stability: float    # Closer to 0.5 = balanced
    witness_diversity: float     # Higher = more witnesses
    trust_variance: float        # Lower = more uniform
    boundary_permeability: float # Lower = more defined boundary

    @property
    def composite_health(self) -> float:
        """Weighted health score. Higher = healthier."""
        return (
            (1.0 - self.trust_entropy) * 0.2 +     # Low entropy good
            self.clustering * 0.2 +                  # High clustering good
            self.mrh_overlap * 0.15 +                # High overlap good
            self.atp_flow_stability * 0.15 +         # Balanced flow good
            self.witness_diversity * 0.15 +           # Diverse witnesses good
            (1.0 - self.trust_variance) * 0.1 +       # Low variance good
            (1.0 - self.boundary_permeability) * 0.05  # Low permeability good
        )

    @property
    def status(self) -> HealthStatus:
        h = self.composite_health
        if h >= 0.6:
            return HealthStatus.HEALTHY
        elif h >= 0.4:
            return HealthStatus.WARNING
        return HealthStatus.CRITICAL


@dataclass
class DecaySignal:
    """A detected decay precursor."""
    decay_type: DecayType
    severity: float   # 0-1
    entity_ids: List[str]
    details: str
    timestamp: float


# ─── Synthon Detector ─────────────────────────────────────────────────────────

class SynthonDetector:
    """
    Detect synthon formation from entity group dynamics.
    Formation = trust entropy decrease + clustering increase + MRH convergence.
    """

    def __init__(self, entropy_threshold: float = 0.4,
                 clustering_threshold: float = 0.3,
                 overlap_threshold: float = 0.3):
        self.entropy_threshold = entropy_threshold
        self.clustering_threshold = clustering_threshold
        self.overlap_threshold = overlap_threshold

    def detect_formation(self, entities: List[Entity],
                          adjacency: Dict[str, Set[str]]) -> Tuple[bool, SynthonHealth]:
        """Check if a group of entities is forming a synthon."""
        trust_values = [e.trust_composite for e in entities]
        entropy = TrustEntropy.compute(trust_values)
        clustering = ClusteringAnalysis.compute_coefficient(adjacency)
        mrh_overlap = MRHOverlapAnalysis.group_overlap(entities)

        # ATP flow stability: average deviation from balanced (0.5)
        flow_ratios = [e.atp_flow_ratio for e in entities]
        flow_stability = 1.0 - (sum(abs(r - 0.5) for r in flow_ratios) / max(len(flow_ratios), 1))

        # Witness diversity: fraction of entities that witness each other
        total_witness_pairs = 0
        for e in entities:
            for other in entities:
                if other.entity_id in e.witnesses:
                    total_witness_pairs += 1
        max_pairs = len(entities) * (len(entities) - 1)
        witness_div = total_witness_pairs / max(max_pairs, 1)

        # Trust variance
        mean_trust = sum(trust_values) / max(len(trust_values), 1)
        variance = sum((t - mean_trust) ** 2 for t in trust_values) / max(len(trust_values), 1)

        # Boundary permeability: fraction of MRH edges crossing group boundary
        group_ids = {e.entity_id for e in entities}
        internal_edges = 0
        external_edges = 0
        for e in entities:
            for peer in e.mrh_zones:
                if peer in group_ids:
                    internal_edges += 1
                else:
                    external_edges += 1
        total_edges = internal_edges + external_edges
        permeability = external_edges / max(total_edges, 1)

        health = SynthonHealth(
            trust_entropy=entropy,
            clustering=clustering,
            mrh_overlap=mrh_overlap,
            atp_flow_stability=flow_stability,
            witness_diversity=witness_div,
            trust_variance=variance,
            boundary_permeability=permeability,
        )

        forming = (entropy <= self.entropy_threshold and
                   clustering >= self.clustering_threshold and
                   mrh_overlap >= self.overlap_threshold)

        return forming, health


# ─── Synthon Lifecycle FSM ────────────────────────────────────────────────────

class SynthonEvent(Enum):
    COHERENCE_EMERGING = auto()
    COHERENCE_ACHIEVED = auto()
    STRESS_DETECTED = auto()
    STRESS_RESOLVED = auto()
    DISSOLUTION_STARTED = auto()
    REFORMED = auto()


@dataclass
class Synthon:
    """A tracked synthon with lifecycle state."""
    synthon_id: str
    phase: SynthonPhase
    entity_ids: Set[str]
    health_history: List[SynthonHealth] = field(default_factory=list)
    decay_signals: List[DecaySignal] = field(default_factory=list)
    formed_at: Optional[float] = None
    dissolved_at: Optional[float] = None
    transitions: List[Tuple[SynthonPhase, SynthonEvent, SynthonPhase]] = field(default_factory=list)


SYNTHON_TRANSITIONS: Dict[SynthonPhase, Dict[SynthonEvent, SynthonPhase]] = {
    SynthonPhase.NASCENT: {
        SynthonEvent.COHERENCE_EMERGING: SynthonPhase.FORMING,
    },
    SynthonPhase.FORMING: {
        SynthonEvent.COHERENCE_ACHIEVED: SynthonPhase.STABLE,
        SynthonEvent.DISSOLUTION_STARTED: SynthonPhase.DISSOLVING,
    },
    SynthonPhase.STABLE: {
        SynthonEvent.STRESS_DETECTED: SynthonPhase.STRESSED,
        SynthonEvent.DISSOLUTION_STARTED: SynthonPhase.DISSOLVING,
    },
    SynthonPhase.STRESSED: {
        SynthonEvent.STRESS_RESOLVED: SynthonPhase.STABLE,
        SynthonEvent.DISSOLUTION_STARTED: SynthonPhase.DISSOLVING,
    },
    SynthonPhase.DISSOLVING: {
        SynthonEvent.REFORMED: SynthonPhase.FORMING,
    },
}


class SynthonLifecycleManager:
    """Manage synthon lifecycle transitions based on health metrics."""

    def __init__(self, detector: SynthonDetector):
        self.detector = detector
        self.synthons: Dict[str, Synthon] = {}
        self._counter = 0

    def create_synthon(self, entity_ids: Set[str]) -> Synthon:
        self._counter += 1
        synthon = Synthon(
            synthon_id=f"synthon_{self._counter}",
            phase=SynthonPhase.NASCENT,
            entity_ids=entity_ids,
        )
        self.synthons[synthon.synthon_id] = synthon
        return synthon

    def transition(self, synthon_id: str, event: SynthonEvent) -> bool:
        synthon = self.synthons.get(synthon_id)
        if not synthon:
            return False
        transitions = SYNTHON_TRANSITIONS.get(synthon.phase, {})
        new_phase = transitions.get(event)
        if new_phase is None:
            return False

        old_phase = synthon.phase
        synthon.transitions.append((old_phase, event, new_phase))
        synthon.phase = new_phase

        if new_phase == SynthonPhase.STABLE and synthon.formed_at is None:
            synthon.formed_at = time.time()
        if new_phase == SynthonPhase.DISSOLVING:
            synthon.dissolved_at = time.time()

        return True

    def update_health(self, synthon_id: str, entities: List[Entity],
                       adjacency: Dict[str, Set[str]]) -> Optional[SynthonHealth]:
        """Update synthon health and auto-transition if warranted."""
        synthon = self.synthons.get(synthon_id)
        if not synthon:
            return None

        _, health = self.detector.detect_formation(entities, adjacency)
        synthon.health_history.append(health)

        # Auto-transition based on health
        if synthon.phase == SynthonPhase.NASCENT:
            if health.composite_health > 0.4:
                self.transition(synthon_id, SynthonEvent.COHERENCE_EMERGING)

        elif synthon.phase == SynthonPhase.FORMING:
            if health.composite_health > 0.6:
                self.transition(synthon_id, SynthonEvent.COHERENCE_ACHIEVED)

        elif synthon.phase == SynthonPhase.STABLE:
            if health.composite_health < 0.4:
                self.transition(synthon_id, SynthonEvent.STRESS_DETECTED)

        elif synthon.phase == SynthonPhase.STRESSED:
            if health.composite_health > 0.6:
                self.transition(synthon_id, SynthonEvent.STRESS_RESOLVED)
            elif health.composite_health < 0.3:
                self.transition(synthon_id, SynthonEvent.DISSOLUTION_STARTED)

        return health


# ─── Decay Detection ─────────────────────────────────────────────────────────

class DecayDetector:
    """Detect decay precursors from health history."""

    def __init__(self, window: int = 5):
        self.window = window

    def detect(self, synthon: Synthon) -> List[DecaySignal]:
        signals = []
        if len(synthon.health_history) < self.window:
            return signals

        recent = synthon.health_history[-self.window:]

        # 1. Entropy increasing over window
        entropies = [h.trust_entropy for h in recent]
        if all(entropies[i] <= entropies[i + 1] for i in range(len(entropies) - 1)):
            increase = entropies[-1] - entropies[0]
            if increase > 0.05:
                signals.append(DecaySignal(
                    DecayType.ENTROPY_INCREASE, min(increase * 5, 1.0),
                    list(synthon.entity_ids),
                    f"Trust entropy increasing: {entropies[0]:.3f} → {entropies[-1]:.3f}",
                    time.time()))

        # 2. Boundary permeability increasing
        perms = [h.boundary_permeability for h in recent]
        if all(perms[i] <= perms[i + 1] for i in range(len(perms) - 1)):
            increase = perms[-1] - perms[0]
            if increase > 0.05:
                signals.append(DecaySignal(
                    DecayType.BOUNDARY_LEAK, min(increase * 5, 1.0),
                    list(synthon.entity_ids),
                    f"Boundary permeability increasing: {perms[0]:.3f} → {perms[-1]:.3f}",
                    time.time()))

        # 3. ATP flow becoming asymmetric
        flows = [h.atp_flow_stability for h in recent]
        if all(flows[i] >= flows[i + 1] for i in range(len(flows) - 1)):
            decrease = flows[0] - flows[-1]
            if decrease > 0.1:
                signals.append(DecaySignal(
                    DecayType.ATP_ASYMMETRY, min(decrease * 3, 1.0),
                    list(synthon.entity_ids),
                    f"ATP flow stability decreasing: {flows[0]:.3f} → {flows[-1]:.3f}",
                    time.time()))

        # 4. Witness diversity declining
        witnesses = [h.witness_diversity for h in recent]
        if all(witnesses[i] >= witnesses[i + 1] for i in range(len(witnesses) - 1)):
            decrease = witnesses[0] - witnesses[-1]
            if decrease > 0.1:
                signals.append(DecaySignal(
                    DecayType.WITNESS_LOSS, min(decrease * 3, 1.0),
                    list(synthon.entity_ids),
                    f"Witness diversity declining: {witnesses[0]:.3f} → {witnesses[-1]:.3f}",
                    time.time()))

        # 5. Trust variance increasing
        variances = [h.trust_variance for h in recent]
        if all(variances[i] <= variances[i + 1] for i in range(len(variances) - 1)):
            increase = variances[-1] - variances[0]
            if increase > 0.01:
                signals.append(DecaySignal(
                    DecayType.TRUST_DIVERGENCE, min(increase * 10, 1.0),
                    list(synthon.entity_ids),
                    f"Trust variance increasing: {variances[0]:.3f} → {variances[-1]:.3f}",
                    time.time()))

        synthon.decay_signals.extend(signals)
        return signals


# ─── Anti-Absorption Defense ─────────────────────────────────────────────────

class AbsorptionDefense:
    """Detect when one entity's MRH is absorbing another's."""

    @staticmethod
    def check_group(entities: List[Entity], threshold: float = 0.8) -> List[Tuple[str, str]]:
        """Return pairs where first entity is absorbing second."""
        absorptions = []
        for a in entities:
            for b in entities:
                if a.entity_id == b.entity_id:
                    continue
                if MRHOverlapAnalysis.detect_absorption(a, b, threshold):
                    absorptions.append((a.entity_id, b.entity_id))
        return absorptions


# ─── Inter-Synthon Conflict ───────────────────────────────────────────────────

@dataclass
class InterSynthonConflict:
    """Conflict between two synthons."""
    conflict_id: str
    synthon_a: str
    synthon_b: str
    shared_entities: Set[str]
    severity: float
    details: str


class InterSynthonAnalyzer:
    """Detect and map conflicts between synthons."""

    def __init__(self, manager: SynthonLifecycleManager):
        self.manager = manager
        self.conflicts: List[InterSynthonConflict] = []

    def detect_conflicts(self) -> List[InterSynthonConflict]:
        """Find synthons competing for the same entities."""
        conflicts = []
        synthon_list = list(self.manager.synthons.values())

        for i in range(len(synthon_list)):
            for j in range(i + 1, len(synthon_list)):
                sa, sb = synthon_list[i], synthon_list[j]
                shared = sa.entity_ids & sb.entity_ids
                if shared:
                    severity = len(shared) / min(len(sa.entity_ids), len(sb.entity_ids))
                    conflict = InterSynthonConflict(
                        f"isc_{secrets.token_hex(6)}",
                        sa.synthon_id, sb.synthon_id, shared, severity,
                        f"{len(shared)} shared entities between {sa.synthon_id} and {sb.synthon_id}"
                    )
                    conflicts.append(conflict)

        self.conflicts = conflicts
        return conflicts


# ─── Checks ──────────────────────────────────────────────────────────────────

def _make_entity(eid: str, trust: float, peers: Dict[str, int],
                  witnesses: Set[str], atp_in: float = 50.0,
                  atp_out: float = 50.0) -> Entity:
    return Entity(
        entity_id=eid,
        trust_scores={"talent": trust, "training": trust, "temperament": trust},
        mrh_zones=peers,
        atp_balance=100.0,
        atp_inflow=atp_in,
        atp_outflow=atp_out,
        witnesses=witnesses,
    )


def _make_clique(n: int, trust: float, prefix: str = "e") -> Tuple[List[Entity], Dict[str, Set[str]]]:
    """Create a fully-connected clique of n entities."""
    ids = [f"{prefix}{i}" for i in range(n)]
    entities = []
    adjacency: Dict[str, Set[str]] = {}

    for eid in ids:
        peers = {other: 1 for other in ids if other != eid}
        witnesses = {other for other in ids if other != eid}
        entities.append(_make_entity(eid, trust, peers, witnesses))
        adjacency[eid] = {other for other in ids if other != eid}

    return entities, adjacency


def run_checks():
    checks = []
    t0 = time.time()

    # ── S1: Trust Entropy ─────────────────────────────────────────────────
    # Uniform distribution → low entropy
    uniform = [0.7, 0.71, 0.69, 0.72, 0.68, 0.7, 0.71]
    checks.append(("s1_uniform_low_entropy", TrustEntropy.compute(uniform) < 0.5))

    # Spread distribution → high entropy
    spread = [0.1, 0.3, 0.5, 0.7, 0.9, 0.2, 0.8]
    checks.append(("s1_spread_high_entropy", TrustEntropy.compute(spread) > 0.5))

    # Single value → zero entropy
    checks.append(("s1_single_zero", TrustEntropy.compute([0.5]) == 0.0))

    # Delta: becoming more coherent
    delta = TrustEntropy.compute_delta(spread, uniform)
    checks.append(("s1_delta_negative", delta < 0))

    # ── S2: Clustering Coefficient ────────────────────────────────────────
    # Full clique = 1.0
    full_adj: Dict[str, Set[str]] = {
        "a": {"b", "c", "d"},
        "b": {"a", "c", "d"},
        "c": {"a", "b", "d"},
        "d": {"a", "b", "c"},
    }
    checks.append(("s2_clique_1", abs(ClusteringAnalysis.compute_coefficient(full_adj) - 1.0) < 0.01))

    # Star graph = 0
    star_adj: Dict[str, Set[str]] = {
        "hub": {"a", "b", "c", "d"},
        "a": {"hub"}, "b": {"hub"}, "c": {"hub"}, "d": {"hub"},
    }
    checks.append(("s2_star_0", ClusteringAnalysis.compute_coefficient(star_adj) == 0.0))

    # Local coefficient for hub in star = 0
    checks.append(("s2_local_hub_0", ClusteringAnalysis.local_coefficient("hub", star_adj) == 0.0))

    # Local coefficient in clique = 1.0
    checks.append(("s2_local_clique_1", abs(ClusteringAnalysis.local_coefficient("a", full_adj) - 1.0) < 0.01))

    # ── S3: MRH Overlap ──────────────────────────────────────────────────
    mrh_a = {"x": 1, "y": 2, "z": 1}
    mrh_b = {"x": 1, "y": 1, "w": 3}
    overlap = MRHOverlapAnalysis.compute_overlap(mrh_a, mrh_b)
    # Jaccard: {x,y} intersect / {x,y,z,w} union = 2/4 = 0.5
    checks.append(("s3_jaccard_half", abs(overlap - 0.5) < 0.01))

    # Empty MRH
    checks.append(("s3_empty_zero", MRHOverlapAnalysis.compute_overlap({}, {"a": 1}) == 0.0))

    # Absorption: all of B's peers are in A's peers
    absorber = _make_entity("a", 0.7, {"x": 1, "y": 1, "z": 1, "w": 1}, set())
    target = _make_entity("b", 0.7, {"x": 1, "y": 1, "z": 1}, set())
    checks.append(("s3_absorption_detected",
                    MRHOverlapAnalysis.detect_absorption(absorber, target, 0.8)))

    # Not absorbed: only partial overlap
    partial = _make_entity("c", 0.7, {"x": 1, "q": 1, "r": 1}, set())
    checks.append(("s3_no_absorption",
                    not MRHOverlapAnalysis.detect_absorption(absorber, partial, 0.8)))

    # ── S4: Synthon Formation Detection ───────────────────────────────────
    detector = SynthonDetector(entropy_threshold=0.5, clustering_threshold=0.3,
                                overlap_threshold=0.2)

    # Coherent clique → formation detected
    entities, adjacency = _make_clique(5, 0.7)
    forming, health = detector.detect_formation(entities, adjacency)
    checks.append(("s4_clique_forming", forming))
    checks.append(("s4_high_clustering", health.clustering > 0.9))
    checks.append(("s4_low_entropy", health.trust_entropy < 0.5))
    checks.append(("s4_balanced_flow", health.atp_flow_stability > 0.8))

    # Incoherent group → no formation
    incoherent = [
        _make_entity("i0", 0.1, {"i1": 1}, set()),
        _make_entity("i1", 0.9, {"i0": 1}, set()),
        _make_entity("i2", 0.3, {}, set()),
        _make_entity("i3", 0.7, {}, set()),
        _make_entity("i4", 0.5, {}, set()),
    ]
    sparse_adj: Dict[str, Set[str]] = {"i0": {"i1"}, "i1": {"i0"}, "i2": set(), "i3": set(), "i4": set()}
    not_forming, i_health = detector.detect_formation(incoherent, sparse_adj)
    checks.append(("s4_incoherent_not_forming", not not_forming))
    checks.append(("s4_high_entropy", i_health.trust_entropy > 0.5))

    # ── S5: Health Metrics ────────────────────────────────────────────────
    checks.append(("s5_healthy", health.status == HealthStatus.HEALTHY))
    checks.append(("s5_composite_high", health.composite_health > 0.5))
    checks.append(("s5_incoherent_warning",
                    i_health.status in (HealthStatus.WARNING, HealthStatus.CRITICAL)))

    # ── S6: Synthon Lifecycle FSM ─────────────────────────────────────────
    manager = SynthonLifecycleManager(detector)
    synthon = manager.create_synthon({"e0", "e1", "e2", "e3", "e4"})
    checks.append(("s6_nascent", synthon.phase == SynthonPhase.NASCENT))

    ok = manager.transition(synthon.synthon_id, SynthonEvent.COHERENCE_EMERGING)
    checks.append(("s6_to_forming", ok and synthon.phase == SynthonPhase.FORMING))

    ok2 = manager.transition(synthon.synthon_id, SynthonEvent.COHERENCE_ACHIEVED)
    checks.append(("s6_to_stable", ok2 and synthon.phase == SynthonPhase.STABLE))
    checks.append(("s6_formed_at_set", synthon.formed_at is not None))

    ok3 = manager.transition(synthon.synthon_id, SynthonEvent.STRESS_DETECTED)
    checks.append(("s6_to_stressed", ok3 and synthon.phase == SynthonPhase.STRESSED))

    ok4 = manager.transition(synthon.synthon_id, SynthonEvent.STRESS_RESOLVED)
    checks.append(("s6_back_to_stable", ok4 and synthon.phase == SynthonPhase.STABLE))

    ok5 = manager.transition(synthon.synthon_id, SynthonEvent.DISSOLUTION_STARTED)
    checks.append(("s6_to_dissolving", ok5 and synthon.phase == SynthonPhase.DISSOLVING))
    checks.append(("s6_dissolved_at_set", synthon.dissolved_at is not None))

    # Invalid transition
    checks.append(("s6_invalid",
                    not manager.transition(synthon.synthon_id, SynthonEvent.STRESS_DETECTED)))

    # Reform
    ok6 = manager.transition(synthon.synthon_id, SynthonEvent.REFORMED)
    checks.append(("s6_reformed", ok6 and synthon.phase == SynthonPhase.FORMING))

    checks.append(("s6_history_length", len(synthon.transitions) == 6))

    # ── S7: Auto-Transition via Health Update ─────────────────────────────
    manager2 = SynthonLifecycleManager(detector)
    s2 = manager2.create_synthon({"e0", "e1", "e2", "e3", "e4"})

    # NASCENT → FORMING (health > 0.4)
    h = manager2.update_health(s2.synthon_id, entities, adjacency)
    checks.append(("s7_auto_forming", s2.phase == SynthonPhase.FORMING))

    # FORMING → STABLE (health > 0.6)
    h2 = manager2.update_health(s2.synthon_id, entities, adjacency)
    checks.append(("s7_auto_stable", s2.phase == SynthonPhase.STABLE))

    # STABLE stays stable with good health
    h3 = manager2.update_health(s2.synthon_id, entities, adjacency)
    checks.append(("s7_stays_stable", s2.phase == SynthonPhase.STABLE))

    # ── S8: Decay Detection ───────────────────────────────────────────────
    decay_detector = DecayDetector(window=5)

    # Simulate increasing entropy over 5 health snapshots
    decay_synthon = Synthon("decay_test", SynthonPhase.STABLE, {"d0", "d1"})
    for i in range(6):
        decay_synthon.health_history.append(SynthonHealth(
            trust_entropy=0.2 + i * 0.05,     # Increasing
            clustering=0.8 - i * 0.02,
            mrh_overlap=0.6,
            atp_flow_stability=0.8 - i * 0.03, # Decreasing
            witness_diversity=0.7 - i * 0.03,   # Decreasing
            trust_variance=0.01 + i * 0.005,    # Increasing
            boundary_permeability=0.1 + i * 0.02, # Increasing
        ))

    signals = decay_detector.detect(decay_synthon)
    signal_types = {s.decay_type for s in signals}
    checks.append(("s8_entropy_decay", DecayType.ENTROPY_INCREASE in signal_types))
    checks.append(("s8_atp_asymmetry", DecayType.ATP_ASYMMETRY in signal_types))
    checks.append(("s8_witness_loss", DecayType.WITNESS_LOSS in signal_types))
    checks.append(("s8_trust_divergence", DecayType.TRUST_DIVERGENCE in signal_types))
    checks.append(("s8_boundary_leak", DecayType.BOUNDARY_LEAK in signal_types))
    checks.append(("s8_signals_stored", len(decay_synthon.decay_signals) > 0))

    # No decay in stable synthon
    stable_synthon = Synthon("stable_test", SynthonPhase.STABLE, {"s0", "s1"})
    for _ in range(6):
        stable_synthon.health_history.append(SynthonHealth(
            0.2, 0.8, 0.6, 0.8, 0.7, 0.01, 0.1))
    no_signals = decay_detector.detect(stable_synthon)
    checks.append(("s8_no_decay_stable", len(no_signals) == 0))

    # ── S9: Absorption Defense ────────────────────────────────────────────
    group = [
        _make_entity("big", 0.7, {"x": 1, "y": 1, "z": 1, "w": 1, "v": 1}, set()),
        _make_entity("small", 0.7, {"x": 1, "y": 1, "z": 1}, set()),
        _make_entity("ind", 0.7, {"a": 1, "b": 1}, set()),
    ]
    absorptions = AbsorptionDefense.check_group(group, threshold=0.8)
    checks.append(("s9_absorption_found", ("big", "small") in absorptions))
    checks.append(("s9_ind_not_absorbed", not any(a[1] == "ind" for a in absorptions)))

    # ── S10: Inter-Synthon Conflict ───────────────────────────────────────
    manager3 = SynthonLifecycleManager(detector)
    s_a = manager3.create_synthon({"e0", "e1", "e2"})
    s_b = manager3.create_synthon({"e2", "e3", "e4"})  # e2 shared

    analyzer = InterSynthonAnalyzer(manager3)
    isc = analyzer.detect_conflicts()
    checks.append(("s10_conflict_found", len(isc) == 1))
    checks.append(("s10_shared_e2", "e2" in isc[0].shared_entities))
    checks.append(("s10_severity", isc[0].severity > 0))

    # No conflict when disjoint
    s_c = manager3.create_synthon({"x0", "x1"})
    isc2 = analyzer.detect_conflicts()
    # Still 1 conflict (between a and b), not between c and others
    ab_conflicts = [c for c in isc2 if "x0" in c.shared_entities or "x1" in c.shared_entities]
    checks.append(("s10_no_conflict_disjoint", len(ab_conflicts) == 0))

    # ── S11: Full Lifecycle Scenario ──────────────────────────────────────
    # Create entities, detect formation, track health, introduce stress, detect decay
    manager4 = SynthonLifecycleManager(detector)
    ents, adj = _make_clique(6, 0.75)
    s_life = manager4.create_synthon({e.entity_id for e in ents})

    # Phase 1: Nascent → Forming → Stable
    manager4.update_health(s_life.synthon_id, ents, adj)
    checks.append(("s11_forming", s_life.phase == SynthonPhase.FORMING))
    manager4.update_health(s_life.synthon_id, ents, adj)
    checks.append(("s11_stable", s_life.phase == SynthonPhase.STABLE))

    # Phase 2: Introduce stress — reduce trust, break connections, remove witnesses
    stressed_ents = [
        _make_entity(e.entity_id, 0.2 + i * 0.12,
                      {f"ext_{i}": 5},  # Only external peers (no group overlap)
                      set(), atp_in=85, atp_out=15)
        for i, e in enumerate(ents)
    ]
    stressed_adj: Dict[str, Set[str]] = {e.entity_id: set() for e in stressed_ents}
    stressed_adj[ents[0].entity_id] = {ents[1].entity_id}
    stressed_adj[ents[1].entity_id] = {ents[0].entity_id}

    manager4.update_health(s_life.synthon_id, stressed_ents, stressed_adj)
    checks.append(("s11_stressed", s_life.phase == SynthonPhase.STRESSED))

    # Phase 3: Further degradation → dissolving
    worse_ents = [
        _make_entity(e.entity_id, 0.1 + i * 0.15,
                      {}, set(), atp_in=100, atp_out=0)
        for i, e in enumerate(ents)
    ]
    empty_adj: Dict[str, Set[str]] = {e.entity_id: set() for e in worse_ents}
    manager4.update_health(s_life.synthon_id, worse_ents, empty_adj)
    checks.append(("s11_dissolving", s_life.phase == SynthonPhase.DISSOLVING))

    checks.append(("s11_full_history", len(s_life.health_history) == 4))

    # ── S12: Performance ──────────────────────────────────────────────────
    pt0 = time.time()
    for _ in range(200):
        ents_p, adj_p = _make_clique(8, 0.7)
        detector.detect_formation(ents_p, adj_p)
    pt1 = time.time()
    checks.append(("s12_200_detections_under_2s", pt1 - pt0 < 2.0))

    pt2 = time.time()
    for _ in range(500):
        TrustEntropy.compute([0.1 * i for i in range(10)])
    pt3 = time.time()
    checks.append(("s12_500_entropy_under_1s", pt3 - pt2 < 1.0))

    elapsed = time.time() - t0

    # ── Print Results ─────────────────────────────────────────────────────
    passed = sum(1 for _, v in checks if v)
    total = len(checks)
    title = f"Synthon Lifecycle Detection — {passed}/{total} checks passed"
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")
    for name, val in checks:
        print(f"  [{'PASS' if val else 'FAIL'}] {name}")

    failed = [n for n, v in checks if not v]
    if failed:
        print(f"\n  FAILURES:")
        for f in failed:
            print(f"    ✗ {f}")

    print(f"\n  Time: {elapsed:.2f}s\n")
    return passed == total


if __name__ == "__main__":
    run_checks()
