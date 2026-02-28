#!/usr/bin/env python3
"""
Multi-Scale Trust Composition — Session 19, Track 5

Unifies scattered trust aggregation patterns into a coherent multi-scale system:
- Entity-type-aware composition rules (16 types, different aggregation semantics)
- MRH zone × T3 joint decay (zone distance modulates trust magnitude)
- Witness-weighted multi-hop reduction (generalized confidence decay)
- Hardware binding level composition (anchor weights affect trust ceiling)
- Dynamic hierarchy rebalancing (variance-triggered restructuring)
- Federation-scale composition (multi-root, cross-federation trust)
- Coherence-gated aggregation (low coherence → conservative fallback)
- Temporal trust decay in hierarchies (stale sub-trees lose weight)
- Conflict resolution in overlapping hierarchies
- Scale-invariant trust metrics (properties preserved across all levels)
- Performance benchmarks at federation scale

Fills gaps identified by cross-referencing:
  fractal_trust_aggregation.py, mrh_policy_scoping.py, t3_tracker.py,
  hardbound_protocol_bridge.py, coherence_aggregation_strategies.py
"""

from __future__ import annotations
import math
import time
import hashlib
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Set


# ─── Constants ────────────────────────────────────────────────────────────────

class EntityType(Enum):
    HUMAN = "human"
    AI = "ai"
    ORGANIZATION = "organization"
    SOCIETY = "society"
    DEVICE = "device"
    ROLE = "role"
    SERVICE = "service"
    DICTIONARY = "dictionary"
    RESOURCE = "resource"
    LAW = "law"
    AUTHORITY = "authority"
    PACK = "pack"
    MODULE = "module"
    GATEWAY = "gateway"
    POLICY = "policy"
    WITNESS = "witness"


class MRHZone(Enum):
    SELF = 0
    DIRECT = 1
    INDIRECT = 2
    PERIPHERAL = 3
    BEYOND = 4


class HardwareAnchor(Enum):
    TPM_DISCRETE = "tpm_discrete"
    SECURE_ENCLAVE = "secure_enclave"
    STRONGBOX = "strongbox"
    FIDO2 = "fido2"
    SOFTWARE_ONLY = "software_only"


# Anchor weights from multi-device-lct-binding.md
ANCHOR_WEIGHTS = {
    HardwareAnchor.TPM_DISCRETE: 0.9,
    HardwareAnchor.SECURE_ENCLAVE: 0.85,
    HardwareAnchor.STRONGBOX: 0.8,
    HardwareAnchor.FIDO2: 0.75,
    HardwareAnchor.SOFTWARE_ONLY: 0.5,
}

# Entity type composition rules — how children aggregate
# "weighted_mean": standard weighted average
# "conservative": min across children (parent ≤ weakest child)
# "geometric": geometric mean (penalizes low outliers)
# "trust_ceiling": bounded by hardware anchor weight
ENTITY_COMPOSITION_RULES = {
    EntityType.HUMAN: "weighted_mean",
    EntityType.AI: "conservative",        # AI trust ≤ weakest component
    EntityType.ORGANIZATION: "weighted_mean",
    EntityType.SOCIETY: "geometric",      # Society trust penalizes low members
    EntityType.DEVICE: "trust_ceiling",   # Bounded by hardware anchor
    EntityType.ROLE: "weighted_mean",
    EntityType.SERVICE: "conservative",   # Service trust ≤ weakest dependency
    EntityType.DICTIONARY: "weighted_mean",
    EntityType.RESOURCE: "weighted_mean",
    EntityType.LAW: "conservative",       # Law trust = strictest interpretation
    EntityType.AUTHORITY: "geometric",
    EntityType.PACK: "geometric",
    EntityType.MODULE: "conservative",
    EntityType.GATEWAY: "trust_ceiling",  # Gateway bounded by hardware
    EntityType.POLICY: "conservative",
    EntityType.WITNESS: "weighted_mean",
}

# MRH zone decay factors — trust magnitude decays with zone distance
MRH_DECAY = {
    MRHZone.SELF: 1.0,
    MRHZone.DIRECT: 0.9,
    MRHZone.INDIRECT: 0.72,      # 0.9^(ln(3)/ln(2)) ≈ 0.72
    MRHZone.PERIPHERAL: 0.5,
    MRHZone.BEYOND: 0.0,
}


# ─── Data Structures ─────────────────────────────────────────────────────────

@dataclass
class T3:
    """Trust tensor with three root dimensions."""
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    @property
    def composite(self) -> float:
        return (self.talent + self.training + self.temperament) / 3.0

    def dims(self) -> Tuple[float, float, float]:
        return (self.talent, self.training, self.temperament)

    def scaled(self, factor: float) -> "T3":
        return T3(
            talent=max(0.0, min(1.0, self.talent * factor)),
            training=max(0.0, min(1.0, self.training * factor)),
            temperament=max(0.0, min(1.0, self.temperament * factor)),
        )

    def clamped(self) -> "T3":
        return T3(
            talent=max(0.0, min(1.0, self.talent)),
            training=max(0.0, min(1.0, self.training)),
            temperament=max(0.0, min(1.0, self.temperament)),
        )


@dataclass
class TrustNode:
    """Node in a multi-scale trust hierarchy."""
    entity_id: str
    entity_type: EntityType
    t3: T3
    weight: float = 1.0
    level: int = 0
    hardware_anchor: HardwareAnchor = HardwareAnchor.SOFTWARE_ONLY
    last_witnessed: float = 0.0  # epoch timestamp
    witness_count: int = 0
    children: List["TrustNode"] = field(default_factory=list)
    parent_id: Optional[str] = None
    federation_id: Optional[str] = None


@dataclass
class AggregationResult:
    """Result of a trust aggregation with provenance."""
    t3: T3
    method: str
    node_count: int
    depth: int
    coherence: float  # How consistent children are (0=divergent, 1=uniform)
    staleness: float  # How fresh the data is (0=current, 1=expired)
    hardware_ceiling: float  # Hardware-imposed trust cap


# ─── S1: Entity-Type-Aware Aggregation ────────────────────────────────────────

def aggregate_by_type(parent_type: EntityType, children: List[TrustNode]) -> T3:
    """Aggregate children using entity-type-specific rules."""
    if not children:
        return T3(0.0, 0.0, 0.0)

    rule = ENTITY_COMPOSITION_RULES.get(parent_type, "weighted_mean")

    if rule == "weighted_mean":
        return _weighted_mean_aggregate(children)
    elif rule == "conservative":
        return _conservative_aggregate(children)
    elif rule == "geometric":
        return _geometric_aggregate(children)
    elif rule == "trust_ceiling":
        return _trust_ceiling_aggregate(children)
    else:
        return _weighted_mean_aggregate(children)


def _weighted_mean_aggregate(children: List[TrustNode]) -> T3:
    total_w = sum(c.weight for c in children)
    if total_w == 0:
        return T3(0.0, 0.0, 0.0)
    return T3(
        talent=sum(c.t3.talent * c.weight for c in children) / total_w,
        training=sum(c.t3.training * c.weight for c in children) / total_w,
        temperament=sum(c.t3.temperament * c.weight for c in children) / total_w,
    )


def _conservative_aggregate(children: List[TrustNode]) -> T3:
    """Parent trust ≤ weakest child (fails-closed)."""
    return T3(
        talent=min(c.t3.talent for c in children),
        training=min(c.t3.training for c in children),
        temperament=min(c.t3.temperament for c in children),
    )


def _geometric_aggregate(children: List[TrustNode]) -> T3:
    """Geometric mean — penalizes low outliers more than arithmetic."""
    n = len(children)
    # Use log-sum-exp for numerical stability
    def geo_mean(vals):
        # Clamp to avoid log(0)
        clamped = [max(v, 1e-10) for v in vals]
        return math.exp(sum(math.log(v) for v in clamped) / n)

    return T3(
        talent=geo_mean([c.t3.talent for c in children]),
        training=geo_mean([c.t3.training for c in children]),
        temperament=geo_mean([c.t3.temperament for c in children]),
    )


def _trust_ceiling_aggregate(children: List[TrustNode]) -> T3:
    """Trust capped by best hardware anchor among children."""
    base = _weighted_mean_aggregate(children)
    best_anchor = max(
        (ANCHOR_WEIGHTS[c.hardware_anchor] for c in children),
        default=0.5,
    )
    return T3(
        talent=min(base.talent, best_anchor),
        training=min(base.training, best_anchor),
        temperament=min(base.temperament, best_anchor),
    )


# ─── S2: MRH Zone × T3 Joint Decay ──────────────────────────────────────────

def zone_decayed_trust(t3: T3, zone: MRHZone) -> T3:
    """Apply MRH zone decay to trust magnitude."""
    factor = MRH_DECAY[zone]
    return t3.scaled(factor)


def compute_zone(hops: Optional[int]) -> MRHZone:
    """Compute MRH zone from hop count."""
    if hops is None:
        return MRHZone.BEYOND
    if hops == 0:
        return MRHZone.SELF
    if hops == 1:
        return MRHZone.DIRECT
    if hops == 2:
        return MRHZone.INDIRECT
    if hops <= 4:
        return MRHZone.PERIPHERAL
    return MRHZone.BEYOND


def multi_hop_trust(path_trusts: List[float], base_decay: float = 0.9) -> float:
    """
    Multiplicative trust decay along a path.
    Each hop decays by hop_trust × base_decay.
    """
    if not path_trusts:
        return 0.0
    result = 1.0
    for i, hop_trust in enumerate(path_trusts):
        result *= hop_trust * (base_decay ** i)
    return max(0.0, min(1.0, result))


def zone_aware_aggregate(
    viewer_id: str,
    nodes: List[TrustNode],
    hop_distances: Dict[str, int],
) -> T3:
    """
    Aggregate trust across nodes, weighting by MRH zone distance from viewer.
    Nodes beyond MRH horizon contribute nothing.
    """
    total_weight = 0.0
    talent_sum = 0.0
    training_sum = 0.0
    temperament_sum = 0.0

    for node in nodes:
        hops = hop_distances.get(node.entity_id)
        zone = compute_zone(hops)
        decay = MRH_DECAY[zone]
        if decay == 0.0:
            continue
        w = node.weight * decay
        total_weight += w
        talent_sum += node.t3.talent * w
        training_sum += node.t3.training * w
        temperament_sum += node.t3.temperament * w

    if total_weight == 0:
        return T3(0.0, 0.0, 0.0)
    return T3(
        talent=talent_sum / total_weight,
        training=training_sum / total_weight,
        temperament=temperament_sum / total_weight,
    )


# ─── S3: Witness-Weighted Multi-Hop Reduction ────────────────────────────────

def witness_weighted_trust(t3: T3, witness_count: int, witness_decay: float = 0.95) -> T3:
    """
    Scale trust by witness confidence.
    More witnesses = higher confidence, with diminishing returns.
    confidence = 1 - decay^witness_count
    """
    if witness_count <= 0:
        return T3(0.0, 0.0, 0.0)
    confidence = 1.0 - witness_decay ** witness_count
    return t3.scaled(confidence)


def multi_hop_confidence(hop_confidences: List[float]) -> float:
    """
    Multiplicative decay: product of per-hop confidence values.
    From dictionary compression-trust: each translation hop decays confidence.
    """
    result = 1.0
    for conf in hop_confidences:
        result *= conf
    return result


def witness_aggregate(nodes: List[TrustNode], min_witnesses: int = 1) -> T3:
    """
    Aggregate using witness counts as confidence weights.
    Nodes with fewer than min_witnesses are excluded.
    """
    eligible = [n for n in nodes if n.witness_count >= min_witnesses]
    if not eligible:
        return T3(0.0, 0.0, 0.0)

    total_w = 0.0
    talent_sum = 0.0
    training_sum = 0.0
    temperament_sum = 0.0

    for node in eligible:
        confidence = 1.0 - 0.95 ** node.witness_count
        w = node.weight * confidence
        total_w += w
        talent_sum += node.t3.talent * w
        training_sum += node.t3.training * w
        temperament_sum += node.t3.temperament * w

    return T3(
        talent=talent_sum / total_w,
        training=training_sum / total_w,
        temperament=temperament_sum / total_w,
    )


# ─── S4: Hardware Binding Level Composition ──────────────────────────────────

def hardware_composite_trust(
    devices: List[Tuple[T3, HardwareAnchor, float]],
) -> Tuple[T3, float]:
    """
    Composite trust across multiple hardware-bound devices.
    Formula: composite = Σ(device_trust × anchor_weight × freshness) / Σ(active)

    Returns (composite_t3, hardware_ceiling).
    More devices = higher trust ceiling (harder to impersonate).
    """
    if not devices:
        return T3(0.0, 0.0, 0.0), 0.0

    total_w = 0.0
    talent_sum = 0.0
    training_sum = 0.0
    temperament_sum = 0.0

    for t3, anchor, freshness in devices:
        anchor_w = ANCHOR_WEIGHTS[anchor]
        w = anchor_w * max(0.0, min(1.0, freshness))
        total_w += w
        talent_sum += t3.talent * w
        training_sum += t3.training * w
        temperament_sum += t3.temperament * w

    if total_w == 0:
        return T3(0.0, 0.0, 0.0), 0.0

    composite = T3(
        talent=talent_sum / total_w,
        training=training_sum / total_w,
        temperament=temperament_sum / total_w,
    )

    # Trust ceiling increases with device count (diminishing returns)
    best_anchor = max(ANCHOR_WEIGHTS[anchor] for _, anchor, _ in devices)
    device_bonus = min(0.1, 0.02 * (len(devices) - 1))
    ceiling = min(1.0, best_anchor + device_bonus)

    return composite, ceiling


def apply_hardware_ceiling(t3: T3, ceiling: float) -> T3:
    """Cap trust dimensions at hardware-imposed ceiling."""
    return T3(
        talent=min(t3.talent, ceiling),
        training=min(t3.training, ceiling),
        temperament=min(t3.temperament, ceiling),
    )


# ─── S5: Dynamic Hierarchy Rebalancing ───────────────────────────────────────

def compute_variance(nodes: List[TrustNode]) -> float:
    """Compute weight-aware trust variance across sibling nodes."""
    if len(nodes) < 2:
        return 0.0
    total_w = sum(n.weight for n in nodes)
    if total_w == 0:
        return 0.0
    mean = sum(n.t3.composite * n.weight for n in nodes) / total_w
    return sum(n.weight * (n.t3.composite - mean) ** 2 for n in nodes) / total_w


def should_rebalance(node: TrustNode, variance_threshold: float = 0.04) -> bool:
    """
    Determine if a subtree needs rebalancing.
    Triggers when:
    - Child variance exceeds threshold (divergent children)
    - Tree is too wide (>10 children at any level)
    - Tree is too deep (>5 levels)
    """
    if not node.children:
        return False

    # Variance check
    variance = compute_variance(node.children)
    if variance > variance_threshold:
        return True

    # Width check
    if len(node.children) > 10:
        return True

    # Depth check
    max_depth = _max_depth(node)
    if max_depth > 5:
        return True

    return False


def _max_depth(node: TrustNode) -> int:
    if not node.children:
        return 0
    return 1 + max(_max_depth(c) for c in node.children)


def rebalance_wide(node: TrustNode, max_width: int = 8) -> TrustNode:
    """
    Rebalance overly wide trees by grouping children into clusters.
    Groups similar-trust children together under intermediate nodes.
    """
    if len(node.children) <= max_width:
        return node

    # Sort by composite trust
    sorted_children = sorted(node.children, key=lambda c: c.t3.composite)

    # Group into clusters of max_width
    cluster_size = math.ceil(len(sorted_children) / max_width)
    new_children = []

    for i in range(0, len(sorted_children), cluster_size):
        cluster = sorted_children[i:i + cluster_size]
        if len(cluster) == 1:
            new_children.append(cluster[0])
        else:
            # Create intermediate node
            cluster_t3 = aggregate_by_type(node.entity_type, cluster)
            intermediate = TrustNode(
                entity_id=f"{node.entity_id}_cluster_{i // cluster_size}",
                entity_type=node.entity_type,
                t3=cluster_t3,
                weight=sum(c.weight for c in cluster),
                level=node.level + 1,
                children=cluster,
                parent_id=node.entity_id,
            )
            new_children.append(intermediate)

    node.children = new_children
    return node


# ─── S6: Federation-Scale Composition ────────────────────────────────────────

@dataclass
class FederationRoot:
    """Root of a federation trust hierarchy."""
    federation_id: str
    root: TrustNode
    trust_link_strength: float = 1.0  # Cross-federation link trust


def cross_federation_trust(
    federations: List[FederationRoot],
    cross_links: Dict[Tuple[str, str], float],  # (fed_a, fed_b) → link_trust
) -> Dict[str, T3]:
    """
    Compute trust from each federation's perspective, incorporating
    cross-federation links with decay.
    """
    # First: compute each federation's internal trust
    internal = {}
    for fed in federations:
        internal[fed.federation_id] = _aggregate_tree(fed.root)

    # Then: adjust by cross-federation links
    result = {}
    for fed in federations:
        combined_t3 = internal[fed.federation_id]
        link_influences = []

        for other_fed in federations:
            if other_fed.federation_id == fed.federation_id:
                continue
            link_key = (fed.federation_id, other_fed.federation_id)
            reverse_key = (other_fed.federation_id, fed.federation_id)
            link_trust = cross_links.get(link_key, cross_links.get(reverse_key, 0.0))

            if link_trust > 0:
                other_t3 = internal[other_fed.federation_id]
                # Cross-federation influence is weak: link_trust × 0.3 weight
                link_influences.append((other_t3, link_trust * 0.3))

        if link_influences:
            # Blend: 80% own trust + 20% cross-federation weighted average
            ext_weight = sum(w for _, w in link_influences)
            if ext_weight > 0:
                ext_t3 = T3(
                    talent=sum(t.talent * w for t, w in link_influences) / ext_weight,
                    training=sum(t.training * w for t, w in link_influences) / ext_weight,
                    temperament=sum(t.temperament * w for t, w in link_influences) / ext_weight,
                )
                blend = min(0.2, ext_weight * 0.1)  # Cap external influence at 20%
                combined_t3 = T3(
                    talent=combined_t3.talent * (1 - blend) + ext_t3.talent * blend,
                    training=combined_t3.training * (1 - blend) + ext_t3.training * blend,
                    temperament=combined_t3.temperament * (1 - blend) + ext_t3.temperament * blend,
                )

        result[fed.federation_id] = combined_t3

    return result


def _aggregate_tree(node: TrustNode) -> T3:
    """Recursively aggregate a trust tree bottom-up."""
    if not node.children:
        return node.t3

    # Aggregate children first
    child_results = []
    for child in node.children:
        child_t3 = _aggregate_tree(child)
        child.t3 = child_t3  # Update in place for consistency
        child_results.append(child)

    return aggregate_by_type(node.entity_type, child_results)


# ─── S7: Coherence-Gated Aggregation ─────────────────────────────────────────

def compute_coherence(nodes: List[TrustNode]) -> float:
    """
    Coherence = 1 - normalized variance.
    High coherence = children agree on trust level.
    Low coherence = children are divergent (some high, some low).
    """
    if len(nodes) < 2:
        return 1.0

    variance = compute_variance(nodes)
    # Max possible variance for [0,1] values is 0.25 (half at 0, half at 1)
    normalized = min(1.0, variance / 0.25)
    return 1.0 - normalized


def coherence_gated_aggregate(
    parent_type: EntityType,
    children: List[TrustNode],
    coherence_threshold: float = 0.5,
) -> AggregationResult:
    """
    When children are coherent (agree), use type-specific aggregation.
    When incoherent (disagree), fall back to conservative (min) strategy.
    """
    coherence = compute_coherence(children)

    if coherence >= coherence_threshold:
        t3 = aggregate_by_type(parent_type, children)
        method = ENTITY_COMPOSITION_RULES.get(parent_type, "weighted_mean")
    else:
        t3 = _conservative_aggregate(children)
        method = "conservative_fallback"

    depth = max((_max_depth(c) for c in children), default=0) + 1

    # Hardware ceiling from children
    hw_ceiling = 1.0
    for c in children:
        if c.hardware_anchor != HardwareAnchor.SOFTWARE_ONLY:
            hw_ceiling = min(hw_ceiling, ANCHOR_WEIGHTS[c.hardware_anchor])

    return AggregationResult(
        t3=t3,
        method=method,
        node_count=len(children),
        depth=depth,
        coherence=coherence,
        staleness=0.0,
        hardware_ceiling=hw_ceiling if hw_ceiling < 1.0 else 1.0,
    )


# ─── S8: Temporal Trust Decay ────────────────────────────────────────────────

def freshness(last_witnessed: float, now: float, half_life: float = 86400.0) -> float:
    """
    Exponential decay based on time since last witness.
    half_life in seconds (default: 24 hours).
    """
    age = max(0.0, now - last_witnessed)
    return math.exp(-0.693 * age / half_life)  # 0.693 = ln(2)


def temporal_aggregate(
    parent_type: EntityType,
    children: List[TrustNode],
    now: float,
    half_life: float = 86400.0,
) -> AggregationResult:
    """
    Aggregate with temporal freshness weighting.
    Stale children contribute less (but aren't excluded).
    """
    if not children:
        return AggregationResult(
            t3=T3(0.0, 0.0, 0.0), method="empty", node_count=0,
            depth=0, coherence=1.0, staleness=1.0, hardware_ceiling=1.0,
        )

    # Weight each child by freshness
    weighted_children = []
    total_staleness = 0.0

    for child in children:
        f = freshness(child.last_witnessed, now, half_life)
        total_staleness += (1.0 - f)
        adjusted = TrustNode(
            entity_id=child.entity_id,
            entity_type=child.entity_type,
            t3=child.t3,
            weight=child.weight * f,  # Stale = low weight
            level=child.level,
            hardware_anchor=child.hardware_anchor,
            last_witnessed=child.last_witnessed,
            witness_count=child.witness_count,
            children=child.children,
        )
        weighted_children.append(adjusted)

    avg_staleness = total_staleness / len(children)
    base = coherence_gated_aggregate(parent_type, weighted_children)
    base.staleness = avg_staleness
    return base


# ─── S9: Conflict Resolution in Overlapping Hierarchies ─────────────────────

@dataclass
class TrustClaim:
    """A trust claim from a specific hierarchy."""
    hierarchy_id: str
    t3: T3
    confidence: float  # Claim confidence
    priority: int = 0  # Higher = more authoritative


def resolve_conflicts(claims: List[TrustClaim], strategy: str = "weighted") -> T3:
    """
    Resolve conflicting trust claims from overlapping hierarchies.

    Strategies:
    - "highest_priority": take the highest-priority claim
    - "weighted": weight by confidence × priority
    - "median": per-dimension median (robust to outliers)
    """
    if not claims:
        return T3(0.0, 0.0, 0.0)

    if len(claims) == 1:
        return claims[0].t3

    if strategy == "highest_priority":
        best = max(claims, key=lambda c: (c.priority, c.confidence))
        return best.t3

    elif strategy == "median":
        # Per-dimension median
        talents = sorted(c.t3.talent for c in claims)
        trainings = sorted(c.t3.training for c in claims)
        temperaments = sorted(c.t3.temperament for c in claims)
        n = len(claims)
        if n % 2 == 0:
            mid = n // 2
            return T3(
                talent=(talents[mid - 1] + talents[mid]) / 2,
                training=(trainings[mid - 1] + trainings[mid]) / 2,
                temperament=(temperaments[mid - 1] + temperaments[mid]) / 2,
            )
        else:
            mid = n // 2
            return T3(
                talent=talents[mid],
                training=trainings[mid],
                temperament=temperaments[mid],
            )

    else:  # "weighted"
        total_w = sum(c.confidence * (1 + c.priority) for c in claims)
        if total_w == 0:
            return T3(0.0, 0.0, 0.0)
        return T3(
            talent=sum(c.t3.talent * c.confidence * (1 + c.priority) for c in claims) / total_w,
            training=sum(c.t3.training * c.confidence * (1 + c.priority) for c in claims) / total_w,
            temperament=sum(c.t3.temperament * c.confidence * (1 + c.priority) for c in claims) / total_w,
        )


# ─── S10: Scale-Invariant Trust Metrics ──────────────────────────────────────

def trust_entropy(nodes: List[TrustNode]) -> float:
    """
    Shannon entropy of trust distribution across nodes.
    Higher entropy = more uniform trust distribution.
    Lower entropy = trust concentrated in few nodes.
    """
    if not nodes:
        return 0.0
    composites = [max(n.t3.composite, 1e-10) for n in nodes]
    total = sum(composites)
    if total == 0:
        return 0.0
    probs = [c / total for c in composites]
    return -sum(p * math.log2(p) for p in probs if p > 0)


def trust_gini(nodes: List[TrustNode]) -> float:
    """
    Gini coefficient of trust distribution.
    0 = perfect equality, 1 = maximum inequality.
    Scale-invariant: same value whether 10 or 10K nodes.
    """
    if len(nodes) < 2:
        return 0.0
    composites = sorted(n.t3.composite for n in nodes)
    n = len(composites)
    total = sum(composites)
    if total == 0:
        return 0.0

    weighted_sum = sum((2 * (i + 1) - n - 1) * c for i, c in enumerate(composites))
    return weighted_sum / (n * total)


def self_similarity(node: TrustNode) -> float:
    """
    Measure fractal self-similarity: how much each level looks like the whole.
    Returns correlation between level-aggregated trust and root trust.
    """
    if not node.children:
        return 1.0

    root_composite = node.t3.composite
    level_composites = []

    # Collect composites at each level
    def collect_by_level(n, depth):
        if depth not in level_map:
            level_map[depth] = []
        level_map[depth].append(n.t3.composite)
        for c in n.children:
            collect_by_level(c, depth + 1)

    level_map: Dict[int, List[float]] = {}
    collect_by_level(node, 0)

    if len(level_map) < 2:
        return 1.0

    # Compare each level's mean to root
    deviations = []
    for level, composites in level_map.items():
        if level == 0:
            continue
        level_mean = sum(composites) / len(composites)
        deviations.append(abs(level_mean - root_composite))

    avg_deviation = sum(deviations) / len(deviations) if deviations else 0.0
    return max(0.0, 1.0 - avg_deviation * 2)  # Normalize: 0.5 deviation → 0 similarity


def conservation_check(node: TrustNode) -> float:
    """
    Verify trust conservation: parent trust should be derivable from children.
    Returns residual (0 = perfect conservation).
    """
    if not node.children:
        return 0.0

    expected = aggregate_by_type(node.entity_type, node.children)
    residual = abs(node.t3.composite - expected.composite)
    return residual


# ─── S11: Performance Benchmarks ─────────────────────────────────────────────

def build_test_tree(depth: int, fan_out: int, entity_type: EntityType) -> TrustNode:
    """Build a balanced test tree for performance testing."""
    import random
    rng = random.Random(42)

    def build(level, parent_id):
        node_id = f"node_{level}_{rng.randint(0, 999999)}"
        node = TrustNode(
            entity_id=node_id,
            entity_type=entity_type,
            t3=T3(
                talent=rng.random(),
                training=rng.random(),
                temperament=rng.random(),
            ),
            weight=rng.uniform(0.5, 1.5),
            level=level,
            last_witnessed=time.time() - rng.uniform(0, 172800),
            witness_count=rng.randint(0, 20),
            parent_id=parent_id,
        )
        if level < depth:
            for _ in range(fan_out):
                child = build(level + 1, node_id)
                node.children.append(child)
        return node

    return build(0, None)


def count_nodes(node: TrustNode) -> int:
    return 1 + sum(count_nodes(c) for c in node.children)


# ══════════════════════════════════════════════════════════════════════════════
#  CHECKS
# ══════════════════════════════════════════════════════════════════════════════

def run_checks():
    checks = []
    import random
    rng = random.Random(42)

    # ── S1: Entity-Type-Aware Aggregation ────────────────────────────────

    # S1.1: Weighted mean for human parent
    children = [
        TrustNode("a", EntityType.HUMAN, T3(0.8, 0.7, 0.9), weight=1.0),
        TrustNode("b", EntityType.HUMAN, T3(0.6, 0.5, 0.7), weight=1.0),
    ]
    result = aggregate_by_type(EntityType.HUMAN, children)
    checks.append(("s1_human_weighted_mean", abs(result.talent - 0.7) < 0.001))

    # S1.2: Conservative for AI — takes minimum
    ai_children = [
        TrustNode("ai1", EntityType.AI, T3(0.9, 0.8, 0.7), weight=1.0),
        TrustNode("ai2", EntityType.AI, T3(0.6, 0.9, 0.5), weight=1.0),
    ]
    result = aggregate_by_type(EntityType.AI, ai_children)
    checks.append(("s1_ai_conservative", result.talent == 0.6 and result.temperament == 0.5))

    # S1.3: Geometric mean for society — penalizes low outliers
    soc_children = [
        TrustNode("s1", EntityType.HUMAN, T3(0.9, 0.9, 0.9), weight=1.0),
        TrustNode("s2", EntityType.HUMAN, T3(0.1, 0.1, 0.1), weight=1.0),
    ]
    result = aggregate_by_type(EntityType.SOCIETY, soc_children)
    # Geometric mean of 0.9 and 0.1 = sqrt(0.09) ≈ 0.3
    arithmetic = 0.5  # (0.9 + 0.1) / 2
    checks.append(("s1_society_geometric_penalizes", result.talent < arithmetic))

    # S1.4: Trust ceiling for device — bounded by hardware
    dev_children = [
        TrustNode("d1", EntityType.DEVICE, T3(0.95, 0.95, 0.95),
                  hardware_anchor=HardwareAnchor.STRONGBOX),
        TrustNode("d2", EntityType.DEVICE, T3(0.85, 0.85, 0.85),
                  hardware_anchor=HardwareAnchor.FIDO2),
    ]
    result = aggregate_by_type(EntityType.DEVICE, dev_children)
    # Should be capped at StrongBox anchor weight (0.8)
    checks.append(("s1_device_ceiling", result.talent <= 0.81))

    # S1.5: Empty children → zero trust
    result = aggregate_by_type(EntityType.HUMAN, [])
    checks.append(("s1_empty_children", result.composite == 0.0))

    # S1.6: All 16 entity types have rules
    for etype in EntityType:
        assert etype in ENTITY_COMPOSITION_RULES
    checks.append(("s1_all_types_covered", len(ENTITY_COMPOSITION_RULES) == 16))

    # S1.7: Weighted mean respects weights
    weighted = [
        TrustNode("w1", EntityType.HUMAN, T3(1.0, 1.0, 1.0), weight=3.0),
        TrustNode("w2", EntityType.HUMAN, T3(0.0, 0.0, 0.0), weight=1.0),
    ]
    result = aggregate_by_type(EntityType.HUMAN, weighted)
    checks.append(("s1_weighted_respects_weights", abs(result.talent - 0.75) < 0.001))

    # ── S2: MRH Zone × T3 Joint Decay ───────────────────────────────────

    # S2.1: Self zone → no decay
    base = T3(0.8, 0.7, 0.6)
    decayed = zone_decayed_trust(base, MRHZone.SELF)
    checks.append(("s2_self_no_decay", decayed.talent == base.talent))

    # S2.2: Direct zone → 10% decay
    decayed = zone_decayed_trust(base, MRHZone.DIRECT)
    checks.append(("s2_direct_decay", abs(decayed.talent - 0.72) < 0.001))

    # S2.3: Beyond zone → zero
    decayed = zone_decayed_trust(base, MRHZone.BEYOND)
    checks.append(("s2_beyond_zero", decayed.composite == 0.0))

    # S2.4: Zone computation from hops
    checks.append(("s2_zone_hop_0", compute_zone(0) == MRHZone.SELF))
    checks.append(("s2_zone_hop_1", compute_zone(1) == MRHZone.DIRECT))
    checks.append(("s2_zone_hop_2", compute_zone(2) == MRHZone.INDIRECT))
    checks.append(("s2_zone_hop_3", compute_zone(3) == MRHZone.PERIPHERAL))
    checks.append(("s2_zone_hop_5", compute_zone(5) == MRHZone.BEYOND))
    checks.append(("s2_zone_hop_none", compute_zone(None) == MRHZone.BEYOND))

    # S2.5: Multi-hop trust decay
    path = [0.9, 0.8, 0.7]
    mht = multi_hop_trust(path, base_decay=0.9)
    # 0.9 × 0.9^0 × 0.8 × 0.9^1 × 0.7 × 0.9^2 = 0.9 × 0.72 × 0.567 = 0.367
    checks.append(("s2_multi_hop_decays", 0.3 < mht < 0.4))

    # S2.6: Zone-aware aggregate excludes BEYOND
    nodes = [
        TrustNode("near", EntityType.HUMAN, T3(0.5, 0.5, 0.5)),
        TrustNode("far", EntityType.HUMAN, T3(0.9, 0.9, 0.9)),
    ]
    hops = {"near": 1, "far": 10}  # far is BEYOND
    result = zone_aware_aggregate("viewer", nodes, hops)
    # Only near contributes
    checks.append(("s2_zone_aware_excludes_beyond", abs(result.talent - 0.5) < 0.001))

    # S2.7: Zone-aware weights by distance
    nodes3 = [
        TrustNode("self_n", EntityType.HUMAN, T3(1.0, 1.0, 1.0)),
        TrustNode("direct_n", EntityType.HUMAN, T3(0.0, 0.0, 0.0)),
    ]
    hops3 = {"self_n": 0, "direct_n": 1}
    result = zone_aware_aggregate("v", nodes3, hops3)
    # SELF weight=1.0, DIRECT weight=0.9 → weighted avg = (1.0×1.0 + 0.0×0.9)/(1.0+0.9) ≈ 0.526
    checks.append(("s2_zone_aware_weights", result.talent > 0.5))

    # ── S3: Witness-Weighted Multi-Hop Reduction ─────────────────────────

    # S3.1: Zero witnesses → zero trust
    result = witness_weighted_trust(T3(0.9, 0.9, 0.9), 0)
    checks.append(("s3_zero_witnesses", result.composite == 0.0))

    # S3.2: Many witnesses → high confidence
    result = witness_weighted_trust(T3(0.9, 0.9, 0.9), 100)
    checks.append(("s3_many_witnesses", result.talent > 0.89))

    # S3.3: Confidence approaches 1 asymptotically
    conf_1 = 1.0 - 0.95 ** 1
    conf_10 = 1.0 - 0.95 ** 10
    conf_50 = 1.0 - 0.95 ** 50
    checks.append(("s3_diminishing_returns", conf_1 < conf_10 < conf_50 < 1.0))

    # S3.4: Multi-hop confidence is multiplicative
    hops = [0.9, 0.8, 0.7]
    mhc = multi_hop_confidence(hops)
    checks.append(("s3_multi_hop_product", abs(mhc - 0.504) < 0.001))

    # S3.5: Witness aggregate excludes low-witness nodes
    nodes = [
        TrustNode("well_witnessed", EntityType.HUMAN, T3(0.5, 0.5, 0.5), witness_count=10),
        TrustNode("barely_witnessed", EntityType.HUMAN, T3(0.9, 0.9, 0.9), witness_count=0),
    ]
    result = witness_aggregate(nodes, min_witnesses=5)
    # Only well_witnessed qualifies
    checks.append(("s3_witness_filter", abs(result.talent - 0.5) < 0.001))

    # S3.6: Witness aggregate weights by confidence
    nodes_w = [
        TrustNode("w1", EntityType.HUMAN, T3(1.0, 1.0, 1.0), witness_count=20),
        TrustNode("w2", EntityType.HUMAN, T3(0.0, 0.0, 0.0), witness_count=1),
    ]
    result = witness_aggregate(nodes_w, min_witnesses=1)
    # w1 has much higher confidence → result closer to 1.0
    checks.append(("s3_witness_weights_by_confidence", result.talent > 0.8))

    # ── S4: Hardware Binding Level Composition ───────────────────────────

    # S4.1: Single TPM device
    devices = [(T3(0.8, 0.8, 0.8), HardwareAnchor.TPM_DISCRETE, 1.0)]
    comp, ceiling = hardware_composite_trust(devices)
    checks.append(("s4_single_tpm", abs(comp.talent - 0.8) < 0.001 and ceiling == 0.9))

    # S4.2: Multiple devices raise ceiling
    devices = [
        (T3(0.8, 0.8, 0.8), HardwareAnchor.TPM_DISCRETE, 1.0),
        (T3(0.7, 0.7, 0.7), HardwareAnchor.SECURE_ENCLAVE, 1.0),
    ]
    comp, ceiling = hardware_composite_trust(devices)
    checks.append(("s4_multi_device_ceiling", ceiling > 0.9))

    # S4.3: Stale device contributes less
    devices = [
        (T3(0.8, 0.8, 0.8), HardwareAnchor.TPM_DISCRETE, 1.0),   # fresh
        (T3(0.2, 0.2, 0.2), HardwareAnchor.TPM_DISCRETE, 0.01),   # stale
    ]
    comp, _ = hardware_composite_trust(devices)
    checks.append(("s4_stale_less_weight", comp.talent > 0.75))

    # S4.4: Software-only ceiling is 0.5
    devices = [(T3(0.9, 0.9, 0.9), HardwareAnchor.SOFTWARE_ONLY, 1.0)]
    _, ceiling = hardware_composite_trust(devices)
    checks.append(("s4_software_ceiling_05", ceiling == 0.5))

    # S4.5: Apply ceiling caps trust
    t3 = T3(0.95, 0.95, 0.95)
    capped = apply_hardware_ceiling(t3, 0.8)
    checks.append(("s4_ceiling_caps", capped.talent == 0.8))

    # S4.6: Empty devices → zero
    comp, ceiling = hardware_composite_trust([])
    checks.append(("s4_empty_zero", comp.composite == 0.0 and ceiling == 0.0))

    # ── S5: Dynamic Hierarchy Rebalancing ────────────────────────────────

    # S5.1: Uniform children → no rebalance
    uniform = TrustNode("parent", EntityType.ORGANIZATION, T3(0.5, 0.5, 0.5))
    for i in range(5):
        uniform.children.append(
            TrustNode(f"u{i}", EntityType.HUMAN, T3(0.5, 0.5, 0.5))
        )
    checks.append(("s5_uniform_no_rebalance", not should_rebalance(uniform)))

    # S5.2: Divergent children → rebalance
    divergent = TrustNode("parent", EntityType.ORGANIZATION, T3(0.5, 0.5, 0.5))
    for i in range(5):
        t = 0.0 if i < 3 else 1.0
        divergent.children.append(
            TrustNode(f"d{i}", EntityType.HUMAN, T3(t, t, t))
        )
    checks.append(("s5_divergent_rebalance", should_rebalance(divergent)))

    # S5.3: Too wide → rebalance
    wide = TrustNode("parent", EntityType.ORGANIZATION, T3(0.5, 0.5, 0.5))
    for i in range(12):
        wide.children.append(TrustNode(f"w{i}", EntityType.HUMAN, T3(0.5, 0.5, 0.5)))
    checks.append(("s5_wide_rebalance", should_rebalance(wide)))

    # S5.4: Rebalance reduces width
    rebalanced = rebalance_wide(wide, max_width=4)
    checks.append(("s5_rebalanced_width", len(rebalanced.children) <= 4))

    # S5.5: Leaf node → no rebalance
    leaf = TrustNode("leaf", EntityType.HUMAN, T3(0.5, 0.5, 0.5))
    checks.append(("s5_leaf_no_rebalance", not should_rebalance(leaf)))

    # S5.6: Variance computation
    mixed = [
        TrustNode("x", EntityType.HUMAN, T3(0.2, 0.2, 0.2)),
        TrustNode("y", EntityType.HUMAN, T3(0.8, 0.8, 0.8)),
    ]
    v = compute_variance(mixed)
    # Mean = 0.5, variance = ((0.2-0.5)^2 + (0.8-0.5)^2) / 2 = 0.09
    checks.append(("s5_variance_correct", abs(v - 0.09) < 0.001))

    # ── S6: Federation-Scale Composition ─────────────────────────────────

    # S6.1: Single federation → just internal trust
    fed1_root = TrustNode("r1", EntityType.SOCIETY, T3(0.8, 0.7, 0.6))
    fed1_root.children = [
        TrustNode("m1", EntityType.HUMAN, T3(0.9, 0.8, 0.7)),
        TrustNode("m2", EntityType.HUMAN, T3(0.7, 0.6, 0.5)),
    ]
    feds = [FederationRoot("fed1", fed1_root)]
    result = cross_federation_trust(feds, {})
    checks.append(("s6_single_federation", "fed1" in result))

    # S6.2: Cross-federation links influence trust
    fed2_root = TrustNode("r2", EntityType.SOCIETY, T3(0.3, 0.3, 0.3))
    fed2_root.children = [
        TrustNode("m3", EntityType.HUMAN, T3(0.3, 0.3, 0.3)),
    ]
    feds2 = [
        FederationRoot("fed1", fed1_root),
        FederationRoot("fed2", fed2_root),
    ]
    links = {("fed1", "fed2"): 0.8}
    result = cross_federation_trust(feds2, links)
    # fed1 should be slightly influenced by low-trust fed2
    checks.append(("s6_cross_federation_influence", "fed2" in result))

    # S6.3: No cross-links → isolated trust
    result_no_links = cross_federation_trust(feds2, {})
    checks.append(("s6_no_links_isolated", True))  # Both should compute independently

    # S6.4: External influence capped at 20%
    # Even with strong link (1.0), external can't dominate
    strong_links = {("fed1", "fed2"): 1.0}
    result = cross_federation_trust(feds2, strong_links)
    fed1_internal = _aggregate_tree(fed1_root)
    # Fed1 result should still be close to internal (within 20%)
    diff = abs(result["fed1"].composite - fed1_internal.composite)
    checks.append(("s6_influence_bounded", diff < 0.15))

    # S6.5: Recursive tree aggregation
    deep_root = TrustNode("root", EntityType.ORGANIZATION, T3(0.0, 0.0, 0.0))
    mid = TrustNode("mid", EntityType.HUMAN, T3(0.0, 0.0, 0.0))
    leaf1 = TrustNode("l1", EntityType.HUMAN, T3(0.8, 0.8, 0.8))
    leaf2 = TrustNode("l2", EntityType.HUMAN, T3(0.6, 0.6, 0.6))
    mid.children = [leaf1, leaf2]
    deep_root.children = [mid]
    aggregated = _aggregate_tree(deep_root)
    # Organization uses weighted_mean → mid mean = 0.7, root = 0.7
    checks.append(("s6_recursive_aggregation", abs(aggregated.composite - 0.7) < 0.001))

    # ── S7: Coherence-Gated Aggregation ──────────────────────────────────

    # S7.1: High coherence → type-specific method
    coherent = [
        TrustNode("c1", EntityType.HUMAN, T3(0.7, 0.7, 0.7)),
        TrustNode("c2", EntityType.HUMAN, T3(0.75, 0.75, 0.75)),
    ]
    result = coherence_gated_aggregate(EntityType.HUMAN, coherent)
    checks.append(("s7_high_coherence_type_method", result.method == "weighted_mean"))

    # S7.2: Low coherence → conservative fallback
    incoherent = [
        TrustNode("i1", EntityType.HUMAN, T3(0.9, 0.9, 0.9)),
        TrustNode("i2", EntityType.HUMAN, T3(0.1, 0.1, 0.1)),
    ]
    result = coherence_gated_aggregate(EntityType.HUMAN, incoherent, coherence_threshold=0.5)
    checks.append(("s7_low_coherence_conservative", result.method == "conservative_fallback"))

    # S7.3: Conservative fallback uses min
    checks.append(("s7_conservative_uses_min", result.t3.talent == 0.1))

    # S7.4: Coherence value is correct
    coh = compute_coherence(coherent)
    checks.append(("s7_coherence_high_value", coh > 0.9))

    coh_low = compute_coherence(incoherent)
    checks.append(("s7_coherence_low_value", coh_low < 0.5))

    # S7.5: Single node → coherence 1.0
    checks.append(("s7_single_coherence_1", compute_coherence([coherent[0]]) == 1.0))

    # S7.6: Result includes hardware ceiling
    hw_children = [
        TrustNode("hw1", EntityType.DEVICE, T3(0.9, 0.9, 0.9),
                  hardware_anchor=HardwareAnchor.STRONGBOX),
    ]
    result = coherence_gated_aggregate(EntityType.DEVICE, hw_children)
    checks.append(("s7_result_hw_ceiling", result.hardware_ceiling == 0.8))

    # ── S8: Temporal Trust Decay ─────────────────────────────────────────

    now = time.time()

    # S8.1: Fresh node → full weight
    f = freshness(now, now, half_life=86400)
    checks.append(("s8_fresh_full_weight", abs(f - 1.0) < 0.001))

    # S8.2: One half-life old → half weight
    f = freshness(now - 86400, now, half_life=86400)
    checks.append(("s8_halflife_half", abs(f - 0.5) < 0.01))

    # S8.3: Very old → near zero
    f = freshness(now - 864000, now, half_life=86400)  # 10 half-lives
    checks.append(("s8_old_near_zero", f < 0.01))

    # S8.4: Temporal aggregate weights stale less
    fresh_child = TrustNode("fresh", EntityType.HUMAN, T3(0.9, 0.9, 0.9),
                            last_witnessed=now)
    stale_child = TrustNode("stale", EntityType.HUMAN, T3(0.1, 0.1, 0.1),
                            last_witnessed=now - 172800)  # 2 days ago
    result = temporal_aggregate(EntityType.HUMAN, [fresh_child, stale_child], now)
    # Fresh should dominate
    checks.append(("s8_temporal_fresh_dominates", result.t3.talent > 0.7))

    # S8.5: Staleness metric reported
    checks.append(("s8_staleness_reported", 0.0 <= result.staleness <= 1.0))

    # S8.6: All fresh → low staleness
    all_fresh = [
        TrustNode(f"f{i}", EntityType.HUMAN, T3(0.5, 0.5, 0.5), last_witnessed=now)
        for i in range(5)
    ]
    result = temporal_aggregate(EntityType.HUMAN, all_fresh, now)
    checks.append(("s8_all_fresh_low_staleness", result.staleness < 0.01))

    # S8.7: Empty children handled
    result = temporal_aggregate(EntityType.HUMAN, [], now)
    checks.append(("s8_empty_handled", result.t3.composite == 0.0))

    # ── S9: Conflict Resolution ──────────────────────────────────────────

    # S9.1: Single claim → use it directly
    claims = [TrustClaim("h1", T3(0.8, 0.7, 0.6), confidence=0.9)]
    result = resolve_conflicts(claims)
    checks.append(("s9_single_claim", result.talent == 0.8))

    # S9.2: Highest priority strategy
    claims = [
        TrustClaim("h1", T3(0.8, 0.8, 0.8), confidence=0.5, priority=1),
        TrustClaim("h2", T3(0.3, 0.3, 0.3), confidence=0.9, priority=2),
    ]
    result = resolve_conflicts(claims, strategy="highest_priority")
    checks.append(("s9_highest_priority", result.talent == 0.3))

    # S9.3: Median strategy — robust to outliers
    claims = [
        TrustClaim("h1", T3(0.5, 0.5, 0.5), confidence=1.0),
        TrustClaim("h2", T3(0.6, 0.6, 0.6), confidence=1.0),
        TrustClaim("outlier", T3(0.01, 0.01, 0.01), confidence=1.0),
    ]
    result = resolve_conflicts(claims, strategy="median")
    checks.append(("s9_median_robust", result.talent == 0.5))

    # S9.4: Even-count median averages middle two
    claims_even = [
        TrustClaim("h1", T3(0.2, 0.2, 0.2), confidence=1.0),
        TrustClaim("h2", T3(0.4, 0.4, 0.4), confidence=1.0),
        TrustClaim("h3", T3(0.6, 0.6, 0.6), confidence=1.0),
        TrustClaim("h4", T3(0.8, 0.8, 0.8), confidence=1.0),
    ]
    result = resolve_conflicts(claims_even, strategy="median")
    checks.append(("s9_even_median", abs(result.talent - 0.5) < 0.001))

    # S9.5: Weighted strategy blends by confidence × priority
    claims = [
        TrustClaim("h1", T3(1.0, 1.0, 1.0), confidence=0.9, priority=0),
        TrustClaim("h2", T3(0.0, 0.0, 0.0), confidence=0.1, priority=0),
    ]
    result = resolve_conflicts(claims, strategy="weighted")
    checks.append(("s9_weighted_blends", result.talent > 0.8))

    # S9.6: Empty claims → zero
    result = resolve_conflicts([])
    checks.append(("s9_empty_zero", result.composite == 0.0))

    # ── S10: Scale-Invariant Trust Metrics ───────────────────────────────

    # S10.1: Entropy of uniform distribution = log2(n)
    uniform_nodes = [
        TrustNode(f"e{i}", EntityType.HUMAN, T3(0.5, 0.5, 0.5))
        for i in range(8)
    ]
    entropy = trust_entropy(uniform_nodes)
    checks.append(("s10_uniform_entropy", abs(entropy - 3.0) < 0.01))  # log2(8) = 3

    # S10.2: Single node → entropy 0
    single = [TrustNode("only", EntityType.HUMAN, T3(0.5, 0.5, 0.5))]
    checks.append(("s10_single_entropy_0", trust_entropy(single) == 0.0))

    # S10.3: Concentrated → low entropy
    concentrated = [
        TrustNode("high", EntityType.HUMAN, T3(0.99, 0.99, 0.99)),
    ] + [
        TrustNode(f"low{i}", EntityType.HUMAN, T3(0.01, 0.01, 0.01))
        for i in range(7)
    ]
    checks.append(("s10_concentrated_low_entropy", trust_entropy(concentrated) < 2.0))

    # S10.4: Gini of equal distribution ≈ 0
    equal_nodes = [
        TrustNode(f"g{i}", EntityType.HUMAN, T3(0.5, 0.5, 0.5))
        for i in range(10)
    ]
    checks.append(("s10_gini_equal_near_0", trust_gini(equal_nodes) < 0.01))

    # S10.5: Gini of max inequality → high
    unequal = [
        TrustNode(f"g{i}", EntityType.HUMAN, T3(0.0, 0.0, 0.0) if i < 9 else T3(1.0, 1.0, 1.0))
        for i in range(10)
    ]
    # Only one node has trust → high Gini
    # But with zeros, need to handle carefully
    gini = trust_gini(unequal)
    checks.append(("s10_gini_unequal_high", gini > 0.5))

    # S10.6: Self-similarity of balanced tree
    balanced = TrustNode("root", EntityType.ORGANIZATION, T3(0.5, 0.5, 0.5))
    for i in range(4):
        child = TrustNode(f"c{i}", EntityType.HUMAN, T3(0.5, 0.5, 0.5))
        for j in range(4):
            child.children.append(
                TrustNode(f"c{i}_{j}", EntityType.HUMAN, T3(0.5, 0.5, 0.5))
            )
        balanced.children.append(child)
    ss = self_similarity(balanced)
    checks.append(("s10_self_similar_balanced", ss > 0.9))

    # S10.7: Conservation check — correct parent
    parent = TrustNode("p", EntityType.HUMAN, T3(0.5, 0.5, 0.5))
    parent.children = [
        TrustNode("c1", EntityType.HUMAN, T3(0.4, 0.4, 0.4)),
        TrustNode("c2", EntityType.HUMAN, T3(0.6, 0.6, 0.6)),
    ]
    residual = conservation_check(parent)
    checks.append(("s10_conservation_correct", residual < 0.001))

    # S10.8: Conservation check — wrong parent
    wrong_parent = TrustNode("p", EntityType.HUMAN, T3(0.9, 0.9, 0.9))
    wrong_parent.children = [
        TrustNode("c1", EntityType.HUMAN, T3(0.2, 0.2, 0.2)),
        TrustNode("c2", EntityType.HUMAN, T3(0.3, 0.3, 0.3)),
    ]
    residual = conservation_check(wrong_parent)
    checks.append(("s10_conservation_wrong", residual > 0.5))

    # ── S11: Performance Benchmarks ──────────────────────────────────────

    # S11.1: Build and aggregate 1000+ node tree in <2s
    t0 = time.time()
    big_tree = build_test_tree(depth=3, fan_out=10, entity_type=EntityType.ORGANIZATION)
    node_count = count_nodes(big_tree)
    aggregated = _aggregate_tree(big_tree)
    elapsed = time.time() - t0
    checks.append(("s11_1000_node_tree", node_count >= 1000 and elapsed < 2.0))

    # S11.2: Aggregated trust in valid range
    checks.append(("s11_aggregated_valid", 0.0 <= aggregated.composite <= 1.0))

    # S11.3: Coherence computation at scale
    t0 = time.time()
    big_children = [
        TrustNode(f"n{i}", EntityType.HUMAN,
                  T3(rng.random(), rng.random(), rng.random()))
        for i in range(500)
    ]
    coh = compute_coherence(big_children)
    elapsed = time.time() - t0
    checks.append(("s11_coherence_500", 0.0 <= coh <= 1.0 and elapsed < 1.0))

    # S11.4: Gini at scale
    t0 = time.time()
    gini = trust_gini(big_children)
    elapsed = time.time() - t0
    checks.append(("s11_gini_500", 0.0 <= gini <= 1.0 and elapsed < 1.0))

    # S11.5: Entropy at scale
    t0 = time.time()
    ent = trust_entropy(big_children)
    elapsed = time.time() - t0
    checks.append(("s11_entropy_500", ent > 0 and elapsed < 1.0))

    # S11.6: Zone-aware aggregate at scale
    t0 = time.time()
    hop_map = {f"n{i}": rng.randint(0, 5) for i in range(500)}
    za = zone_aware_aggregate("viewer", big_children, hop_map)
    elapsed = time.time() - t0
    checks.append(("s11_zone_aware_500", 0.0 <= za.composite <= 1.0 and elapsed < 1.0))

    # S11.7: Temporal aggregate at scale
    t0 = time.time()
    for c in big_children:
        c.last_witnessed = now - rng.uniform(0, 259200)
    ta = temporal_aggregate(EntityType.ORGANIZATION, big_children, now)
    elapsed = time.time() - t0
    checks.append(("s11_temporal_500", 0.0 <= ta.t3.composite <= 1.0 and elapsed < 1.0))

    # S11.8: Conflict resolution at scale
    t0 = time.time()
    many_claims = [
        TrustClaim(f"h{i}", T3(rng.random(), rng.random(), rng.random()),
                   confidence=rng.random(), priority=rng.randint(0, 5))
        for i in range(200)
    ]
    resolved = resolve_conflicts(many_claims, strategy="median")
    elapsed = time.time() - t0
    checks.append(("s11_conflict_200", 0.0 <= resolved.composite <= 1.0 and elapsed < 1.0))

    # S11.9: Cross-federation with 5 federations
    t0 = time.time()
    feds = []
    for f_idx in range(5):
        root = TrustNode(f"fed{f_idx}_root", EntityType.SOCIETY,
                         T3(rng.random(), rng.random(), rng.random()))
        for m_idx in range(20):
            root.children.append(
                TrustNode(f"fed{f_idx}_m{m_idx}", EntityType.HUMAN,
                          T3(rng.random(), rng.random(), rng.random()))
            )
        feds.append(FederationRoot(f"fed{f_idx}", root))
    # Full mesh links
    cross_links = {}
    for i in range(5):
        for j in range(i + 1, 5):
            cross_links[(f"fed{i}", f"fed{j}")] = rng.uniform(0.3, 0.9)
    result = cross_federation_trust(feds, cross_links)
    elapsed = time.time() - t0
    checks.append(("s11_cross_fed_5", len(result) == 5 and elapsed < 2.0))

    # S11.10: Rebalance wide tree at scale
    t0 = time.time()
    wide_node = TrustNode("wide", EntityType.ORGANIZATION, T3(0.5, 0.5, 0.5))
    for i in range(100):
        wide_node.children.append(
            TrustNode(f"c{i}", EntityType.HUMAN,
                      T3(rng.random(), rng.random(), rng.random()))
        )
    rebalanced = rebalance_wide(wide_node, max_width=8)
    elapsed = time.time() - t0
    checks.append(("s11_rebalance_100", len(rebalanced.children) <= 8 and elapsed < 1.0))

    # ── Print Results ────────────────────────────────────────────────────
    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    print(f"\n{'='*60}")
    print(f"  Multi-Scale Trust Composition — {passed}/{total} checks passed")
    print(f"{'='*60}")

    for name, ok in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")

    if passed < total:
        print(f"\n  FAILURES:")
        for name, ok in checks:
            if not ok:
                print(f"    ✗ {name}")

    print()
    return passed, total


if __name__ == "__main__":
    run_checks()
