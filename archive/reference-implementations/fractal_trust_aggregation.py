"""
Fractal Trust Aggregation
==========================

Implements multi-scale trust hierarchies where trust at each level
is recursively composed from children. Supports zoom in/out,
level-appropriate resolution, cross-level consistency, and recursive
verification of trust invariants.

Sections:
  S1  — Trust Hierarchy Node
  S2  — Bottom-Up Aggregation
  S3  — Top-Down Decomposition
  S4  — Zoom Operations (in/out)
  S5  — Level-Appropriate Resolution
  S6  — Cross-Level Consistency
  S7  — Fractal Self-Similarity Metrics
  S8  — Dynamic Hierarchy Updates
  S9  — Trust Granularity Trade-offs
  S10 — Multi-Root Federation
  S11 — Performance & Scale
"""

from __future__ import annotations
import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any, Set
from collections import defaultdict


# ============================================================
# S1 — Trust Hierarchy Node
# ============================================================

@dataclass
class TrustNode:
    """A node in the fractal trust hierarchy."""
    node_id: str
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5
    weight: float = 1.0
    level: int = 0  # 0=leaf, higher=more aggregated
    children: List['TrustNode'] = field(default_factory=list)
    parent: Optional['TrustNode'] = None

    @property
    def composite(self) -> float:
        return (self.talent + self.training + self.temperament) / 3.0

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0

    @property
    def depth(self) -> int:
        if self.is_leaf:
            return 0
        return 1 + max(c.depth for c in self.children)

    @property
    def size(self) -> int:
        if self.is_leaf:
            return 1
        return 1 + sum(c.size for c in self.children)

    def add_child(self, child: 'TrustNode'):
        child.parent = self
        self.children.append(child)

    def leaves(self) -> List['TrustNode']:
        if self.is_leaf:
            return [self]
        result = []
        for c in self.children:
            result.extend(c.leaves())
        return result

    def ancestors(self) -> List['TrustNode']:
        result = []
        current = self.parent
        while current:
            result.append(current)
            current = current.parent
        return result


def test_section_1():
    checks = []

    root = TrustNode("root", level=2)
    team_a = TrustNode("team_a", level=1)
    team_b = TrustNode("team_b", level=1)
    alice = TrustNode("alice", talent=0.8, training=0.6, temperament=0.7)
    bob = TrustNode("bob", talent=0.6, training=0.7, temperament=0.5)
    charlie = TrustNode("charlie", talent=0.9, training=0.8, temperament=0.6)

    root.add_child(team_a)
    root.add_child(team_b)
    team_a.add_child(alice)
    team_a.add_child(bob)
    team_b.add_child(charlie)

    checks.append(("root_depth", root.depth == 2))
    checks.append(("root_size", root.size == 6))
    checks.append(("leaf_count", len(root.leaves()) == 3))
    checks.append(("alice_ancestors", len(alice.ancestors()) == 2))
    checks.append(("alice_composite", abs(alice.composite - 0.7) < 0.01))
    checks.append(("alice_is_leaf", alice.is_leaf))
    checks.append(("root_not_leaf", not root.is_leaf))

    return checks


# ============================================================
# S2 — Bottom-Up Aggregation
# ============================================================

def aggregate_bottom_up(node: TrustNode, method: str = "weighted_mean") -> TrustNode:
    """Recursively aggregate trust from leaves upward."""
    if node.is_leaf:
        return node

    # First aggregate all children
    for child in node.children:
        aggregate_bottom_up(child, method)

    if method == "weighted_mean":
        total_weight = sum(c.weight for c in node.children)
        if total_weight > 0:
            node.talent = sum(c.talent * c.weight for c in node.children) / total_weight
            node.training = sum(c.training * c.weight for c in node.children) / total_weight
            node.temperament = sum(c.temperament * c.weight for c in node.children) / total_weight

    elif method == "min":
        # Conservative: trust = weakest child
        node.talent = min(c.talent for c in node.children)
        node.training = min(c.training for c in node.children)
        node.temperament = min(c.temperament for c in node.children)

    elif method == "geometric_mean":
        n = len(node.children)
        node.talent = math.prod(c.talent for c in node.children) ** (1.0 / n)
        node.training = math.prod(c.training for c in node.children) ** (1.0 / n)
        node.temperament = math.prod(c.temperament for c in node.children) ** (1.0 / n)

    return node


def test_section_2():
    checks = []

    # Build hierarchy
    root = TrustNode("root", level=2)
    team = TrustNode("team", level=1)
    root.add_child(team)
    team.add_child(TrustNode("a", talent=0.8, training=0.6, temperament=0.7))
    team.add_child(TrustNode("b", talent=0.6, training=0.8, temperament=0.5))

    # Weighted mean
    aggregate_bottom_up(root, "weighted_mean")
    checks.append(("wm_talent", abs(team.talent - 0.7) < 0.01))
    checks.append(("wm_training", abs(team.training - 0.7) < 0.01))
    checks.append(("root_equals_team", abs(root.talent - team.talent) < 0.01))

    # Min (conservative)
    root2 = TrustNode("root2", level=2)
    team2 = TrustNode("team2", level=1)
    root2.add_child(team2)
    team2.add_child(TrustNode("c", talent=0.8, training=0.6, temperament=0.9))
    team2.add_child(TrustNode("d", talent=0.3, training=0.9, temperament=0.4))
    aggregate_bottom_up(root2, "min")
    checks.append(("min_talent", abs(team2.talent - 0.3) < 0.01))
    checks.append(("min_training", abs(team2.training - 0.6) < 0.01))

    # Geometric mean
    root3 = TrustNode("root3", level=2)
    team3 = TrustNode("team3", level=1)
    root3.add_child(team3)
    team3.add_child(TrustNode("e", talent=0.8, training=0.4, temperament=0.6))
    team3.add_child(TrustNode("f", talent=0.2, training=0.6, temperament=0.4))
    aggregate_bottom_up(root3, "geometric_mean")
    expected_gm = math.sqrt(0.8 * 0.2)  # ≈ 0.4
    checks.append(("gm_talent", abs(team3.talent - expected_gm) < 0.01))

    # Geometric < weighted mean (penalizes low values more)
    checks.append(("gm_lt_wm", team3.talent < 0.5))

    return checks


# ============================================================
# S3 — Top-Down Decomposition
# ============================================================

def decompose_top_down(node: TrustNode, target_trust: Dict[str, float],
                       dimension: str = "talent") -> Dict[str, float]:
    """Given a target aggregate trust, compute what each child needs."""
    if node.is_leaf:
        return {node.node_id: target_trust.get(dimension, 0.5)}

    current_agg = getattr(node, dimension)
    target_val = target_trust.get(dimension, current_agg)
    ratio = target_val / current_agg if current_agg > 0 else 1.0

    result = {}
    for child in node.children:
        child_target = min(0.95, max(0.0, getattr(child, dimension) * ratio))
        result[child.node_id] = child_target
        if not child.is_leaf:
            child_targets = decompose_top_down(child, {dimension: child_target}, dimension)
            result.update(child_targets)

    return result


def test_section_3():
    checks = []

    root = TrustNode("root", level=1)
    root.add_child(TrustNode("a", talent=0.6, weight=1.0))
    root.add_child(TrustNode("b", talent=0.4, weight=1.0))
    aggregate_bottom_up(root, "weighted_mean")

    # Current aggregate: 0.5. Target: 0.7
    targets = decompose_top_down(root, {"talent": 0.7}, "talent")
    checks.append(("a_increased", targets["a"] > 0.6))
    checks.append(("b_increased", targets["b"] > 0.4))

    # Ratio preserved: a/b should stay the same
    original_ratio = 0.6 / 0.4
    target_ratio = targets["a"] / targets["b"]
    checks.append(("ratio_preserved", abs(original_ratio - target_ratio) < 0.01))

    # Clamped to [0, 0.95]
    targets_high = decompose_top_down(root, {"talent": 0.99}, "talent")
    checks.append(("clamped_max", targets_high["a"] <= 0.95))

    return checks


# ============================================================
# S4 — Zoom Operations
# ============================================================

def zoom_out(node: TrustNode) -> Dict[str, float]:
    """Zoom out: return aggregated view at this node's level."""
    return {
        "node_id": node.node_id,
        "level": node.level,
        "talent": node.talent,
        "training": node.training,
        "temperament": node.temperament,
        "composite": node.composite,
        "child_count": len(node.children),
        "leaf_count": len(node.leaves()),
    }


def zoom_in(node: TrustNode) -> List[Dict[str, float]]:
    """Zoom in: return detailed view of children."""
    return [zoom_out(child) for child in node.children]


def zoom_to_level(root: TrustNode, target_level: int) -> List[Dict[str, float]]:
    """Get all nodes at a specific level."""
    result = []

    def collect(node: TrustNode):
        if node.level == target_level:
            result.append(zoom_out(node))
        else:
            for child in node.children:
                collect(child)

    collect(root)
    return result


def test_section_4():
    checks = []

    root = TrustNode("org", level=2)
    team_a = TrustNode("team_a", level=1)
    team_b = TrustNode("team_b", level=1)
    root.add_child(team_a)
    root.add_child(team_b)

    for i in range(3):
        team_a.add_child(TrustNode(f"a{i}", talent=0.6 + 0.1 * i,
                                   training=0.5, temperament=0.7))
    for i in range(2):
        team_b.add_child(TrustNode(f"b{i}", talent=0.4 + 0.2 * i,
                                   training=0.6, temperament=0.5))

    aggregate_bottom_up(root, "weighted_mean")

    # Zoom out at root
    overview = zoom_out(root)
    checks.append(("zoom_out_level", overview["level"] == 2))
    checks.append(("zoom_out_leaves", overview["leaf_count"] == 5))

    # Zoom in to teams
    teams = zoom_in(root)
    checks.append(("zoom_in_count", len(teams) == 2))
    checks.append(("zoom_in_names", teams[0]["node_id"] == "team_a"))

    # Zoom to specific level
    level_0 = zoom_to_level(root, 0)
    checks.append(("level_0_all_leaves", len(level_0) == 5))

    level_1 = zoom_to_level(root, 1)
    checks.append(("level_1_teams", len(level_1) == 2))

    level_2 = zoom_to_level(root, 2)
    checks.append(("level_2_root", len(level_2) == 1))

    return checks


# ============================================================
# S5 — Level-Appropriate Resolution
# ============================================================

def trust_at_resolution(node: TrustNode, resolution: int) -> Dict[str, Dict[str, float]]:
    """Get trust data at specified resolution level.
    Higher resolution = more detail, lower = more aggregated."""
    result = {}

    def collect(n: TrustNode, current_depth: int):
        if current_depth >= resolution or n.is_leaf:
            result[n.node_id] = {
                "talent": n.talent,
                "training": n.training,
                "temperament": n.temperament,
                "composite": n.composite,
                "level": n.level,
            }
        else:
            for child in n.children:
                collect(child, current_depth + 1)

    collect(node, 0)
    return result


def test_section_5():
    checks = []

    # Build 3-level hierarchy
    root = TrustNode("org", level=2)
    for t in range(3):
        team = TrustNode(f"team_{t}", level=1)
        root.add_child(team)
        for m in range(4):
            team.add_child(TrustNode(f"member_{t}_{m}",
                                     talent=0.3 + random.random() * 0.5,
                                     training=0.3 + random.random() * 0.5,
                                     temperament=0.3 + random.random() * 0.5))

    aggregate_bottom_up(root, "weighted_mean")

    # Resolution 0: just root
    r0 = trust_at_resolution(root, 0)
    checks.append(("r0_single", len(r0) == 1 and "org" in r0))

    # Resolution 1: root + teams
    r1 = trust_at_resolution(root, 1)
    checks.append(("r1_teams", len(r1) == 3))

    # Resolution 2: all leaves
    r2 = trust_at_resolution(root, 2)
    checks.append(("r2_leaves", len(r2) == 12))

    # Higher resolution = more data points
    checks.append(("resolution_monotone", len(r0) <= len(r1) <= len(r2)))

    return checks


# ============================================================
# S6 — Cross-Level Consistency
# ============================================================

def verify_cross_level_consistency(node: TrustNode,
                                    tolerance: float = 0.01) -> List[str]:
    """Verify that parent trust is consistent with children."""
    errors = []

    if node.is_leaf:
        return errors

    # Check this node's aggregation
    total_weight = sum(c.weight for c in node.children)
    if total_weight > 0:
        expected_talent = sum(c.talent * c.weight for c in node.children) / total_weight
        expected_training = sum(c.training * c.weight for c in node.children) / total_weight
        expected_temperament = sum(c.temperament * c.weight for c in node.children) / total_weight

        if abs(node.talent - expected_talent) > tolerance:
            errors.append(f"{node.node_id}: talent {node.talent:.3f} != expected {expected_talent:.3f}")
        if abs(node.training - expected_training) > tolerance:
            errors.append(f"{node.node_id}: training {node.training:.3f} != expected {expected_training:.3f}")
        if abs(node.temperament - expected_temperament) > tolerance:
            errors.append(f"{node.node_id}: temperament {node.temperament:.3f} != expected {expected_temperament:.3f}")

    # Recurse into children
    for child in node.children:
        errors.extend(verify_cross_level_consistency(child, tolerance))

    return errors


def test_section_6():
    checks = []

    # Consistent hierarchy
    root = TrustNode("root", level=1)
    root.add_child(TrustNode("a", talent=0.8, training=0.6, temperament=0.7))
    root.add_child(TrustNode("b", talent=0.6, training=0.4, temperament=0.5))
    aggregate_bottom_up(root, "weighted_mean")

    errors = verify_cross_level_consistency(root)
    checks.append(("consistent", len(errors) == 0))

    # Manually break consistency
    root.talent = 0.9  # Should be 0.7
    errors = verify_cross_level_consistency(root)
    checks.append(("inconsistency_detected", len(errors) > 0))

    # Fix it
    root.talent = 0.7
    errors = verify_cross_level_consistency(root)
    checks.append(("fixed", len(errors) == 0))

    # Deep hierarchy consistency
    deep = TrustNode("deep_root", level=3)
    l2 = TrustNode("l2", level=2)
    l1 = TrustNode("l1", level=1)
    deep.add_child(l2)
    l2.add_child(l1)
    l1.add_child(TrustNode("leaf1", talent=0.5, training=0.5, temperament=0.5))
    l1.add_child(TrustNode("leaf2", talent=0.7, training=0.7, temperament=0.7))
    aggregate_bottom_up(deep, "weighted_mean")
    errors = verify_cross_level_consistency(deep)
    checks.append(("deep_consistent", len(errors) == 0))

    return checks


# ============================================================
# S7 — Fractal Self-Similarity Metrics
# ============================================================

def self_similarity_score(node: TrustNode) -> float:
    """Measure how self-similar the trust structure is across levels.
    Returns a score [0, 1] where 1 = perfectly self-similar."""
    if node.is_leaf or len(node.children) == 0:
        return 1.0

    # Compare parent's trust profile to each child's
    parent_profile = (node.talent, node.training, node.temperament)
    deviations = []

    for child in node.children:
        child_profile = (child.talent, child.training, child.temperament)
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(parent_profile, child_profile)))
        deviations.append(dist)

    # Max possible distance in 3D unit cube = sqrt(3)
    avg_deviation = sum(deviations) / len(deviations)
    similarity = 1.0 - avg_deviation / math.sqrt(3)

    # Average with children's self-similarity (recursive)
    child_similarities = [self_similarity_score(c) for c in node.children]
    if child_similarities:
        return 0.5 * similarity + 0.5 * (sum(child_similarities) / len(child_similarities))
    return similarity


def trust_variance_across_levels(root: TrustNode) -> Dict[int, float]:
    """Compute trust variance at each level."""
    level_trusts = defaultdict(list)

    def collect(node: TrustNode):
        level_trusts[node.level].append(node.composite)
        for child in node.children:
            collect(child)

    collect(root)

    variances = {}
    for level, trusts in level_trusts.items():
        if len(trusts) < 2:
            variances[level] = 0.0
        else:
            mean = sum(trusts) / len(trusts)
            var = sum((t - mean) ** 2 for t in trusts) / len(trusts)
            variances[level] = var

    return variances


def test_section_7():
    checks = []
    random.seed(42)

    # Uniform hierarchy (high self-similarity)
    uniform_root = TrustNode("ur", level=1)
    for i in range(5):
        uniform_root.add_child(TrustNode(f"u{i}", talent=0.6, training=0.6, temperament=0.6))
    aggregate_bottom_up(uniform_root, "weighted_mean")
    ss_uniform = self_similarity_score(uniform_root)
    checks.append(("uniform_high_similarity", ss_uniform > 0.9))

    # Diverse hierarchy (low self-similarity)
    diverse_root = TrustNode("dr", level=1)
    for i in range(5):
        diverse_root.add_child(TrustNode(f"d{i}",
                                         talent=0.1 + 0.8 * (i / 4),
                                         training=0.9 - 0.8 * (i / 4),
                                         temperament=random.random()))
    aggregate_bottom_up(diverse_root, "weighted_mean")
    ss_diverse = self_similarity_score(diverse_root)
    checks.append(("diverse_lower_similarity", ss_diverse < ss_uniform))

    # Variance across levels
    root = TrustNode("org", level=2)
    for t in range(3):
        team = TrustNode(f"t{t}", level=1)
        root.add_child(team)
        for m in range(5):
            team.add_child(TrustNode(f"m{t}{m}",
                                     talent=0.3 + random.random() * 0.5,
                                     training=0.3 + random.random() * 0.5,
                                     temperament=0.3 + random.random() * 0.5))
    aggregate_bottom_up(root, "weighted_mean")

    variances = trust_variance_across_levels(root)
    checks.append(("leaf_variance", variances[0] > 0))
    # Aggregation reduces variance (central limit theorem)
    checks.append(("aggregation_reduces_variance",
                    variances.get(1, 0) <= variances.get(0, 0) + 0.01))

    return checks


# ============================================================
# S8 — Dynamic Hierarchy Updates
# ============================================================

def update_leaf_and_propagate(leaf: TrustNode, new_talent: float = None,
                               new_training: float = None,
                               new_temperament: float = None):
    """Update a leaf and propagate changes up."""
    if new_talent is not None:
        leaf.talent = new_talent
    if new_training is not None:
        leaf.training = new_training
    if new_temperament is not None:
        leaf.temperament = new_temperament

    # Propagate up
    current = leaf.parent
    while current:
        total_weight = sum(c.weight for c in current.children)
        if total_weight > 0:
            current.talent = sum(c.talent * c.weight for c in current.children) / total_weight
            current.training = sum(c.training * c.weight for c in current.children) / total_weight
            current.temperament = sum(c.temperament * c.weight for c in current.children) / total_weight
        current = current.parent


def rebalance_hierarchy(root: TrustNode, max_children: int = 4):
    """Split nodes with too many children into sub-groups."""
    if root.is_leaf:
        return

    while len(root.children) > max_children:
        # Split children into groups
        mid = len(root.children) // 2
        group_a = root.children[:mid]
        group_b = root.children[mid:]

        sub_a = TrustNode(f"{root.node_id}_sub_a", level=root.level - 1)
        sub_b = TrustNode(f"{root.node_id}_sub_b", level=root.level - 1)

        root.children = []
        for c in group_a:
            sub_a.add_child(c)
        for c in group_b:
            sub_b.add_child(c)

        root.add_child(sub_a)
        root.add_child(sub_b)
        root.level += 1

    for child in root.children:
        rebalance_hierarchy(child, max_children)

    aggregate_bottom_up(root, "weighted_mean")


def test_section_8():
    checks = []

    # Dynamic update
    root = TrustNode("root", level=1)
    alice = TrustNode("alice", talent=0.5, training=0.5, temperament=0.5)
    bob = TrustNode("bob", talent=0.5, training=0.5, temperament=0.5)
    root.add_child(alice)
    root.add_child(bob)
    aggregate_bottom_up(root, "weighted_mean")

    checks.append(("initial_root", abs(root.composite - 0.5) < 0.01))

    # Update alice and propagate
    update_leaf_and_propagate(alice, new_talent=0.9)
    checks.append(("alice_updated", abs(alice.talent - 0.9) < 0.01))
    checks.append(("root_propagated", abs(root.talent - 0.7) < 0.01))  # (0.9+0.5)/2

    # Consistency after update
    errors = verify_cross_level_consistency(root)
    checks.append(("consistent_after_update", len(errors) == 0))

    # Rebalance large hierarchy
    wide = TrustNode("wide", level=0)
    for i in range(10):
        wide.add_child(TrustNode(f"w{i}", talent=0.5, training=0.5, temperament=0.5))

    rebalance_hierarchy(wide, max_children=4)
    checks.append(("rebalanced_children", len(wide.children) <= 4))
    checks.append(("rebalanced_leaves", len(wide.leaves()) == 10))

    # Consistency after rebalance
    errors = verify_cross_level_consistency(wide)
    checks.append(("consistent_after_rebalance", len(errors) == 0))

    return checks


# ============================================================
# S9 — Trust Granularity Trade-offs
# ============================================================

def information_loss(fine: Dict[str, Dict[str, float]],
                     coarse: Dict[str, Dict[str, float]],
                     leaf_mapping: Dict[str, str]) -> float:
    """Measure information loss from coarsening trust resolution.
    leaf_mapping: {leaf_id: coarse_node_id}."""
    if not fine or not coarse:
        return 0.0

    total_loss = 0.0
    count = 0

    for leaf_id, fine_data in fine.items():
        coarse_id = leaf_mapping.get(leaf_id)
        if coarse_id and coarse_id in coarse:
            coarse_data = coarse[coarse_id]
            for dim in ["talent", "training", "temperament"]:
                diff = abs(fine_data[dim] - coarse_data[dim])
                total_loss += diff ** 2
            count += 3

    return math.sqrt(total_loss / count) if count > 0 else 0.0


def optimal_resolution(root: TrustNode, max_nodes: int) -> int:
    """Find the finest resolution that stays within node budget."""
    for resolution in range(root.depth + 1, -1, -1):
        nodes = trust_at_resolution(root, resolution)
        if len(nodes) <= max_nodes:
            return resolution
    return 0


def test_section_9():
    checks = []
    random.seed(42)

    root = TrustNode("org", level=2)
    for t in range(3):
        team = TrustNode(f"team_{t}", level=1)
        root.add_child(team)
        for m in range(4):
            team.add_child(TrustNode(f"m_{t}_{m}",
                                     talent=0.3 + random.random() * 0.5,
                                     training=0.3 + random.random() * 0.5,
                                     temperament=0.3 + random.random() * 0.5))
    aggregate_bottom_up(root, "weighted_mean")

    # Fine vs coarse resolution
    fine = trust_at_resolution(root, 10)  # all leaves
    coarse = trust_at_resolution(root, 1)  # teams only

    # Build leaf mapping
    leaf_mapping = {}
    for team in root.children:
        for member in team.children:
            leaf_mapping[member.node_id] = team.node_id

    loss = information_loss(fine, coarse, leaf_mapping)
    checks.append(("some_loss", loss > 0))
    checks.append(("bounded_loss", loss < 0.5))

    # Finer resolution = less loss
    mid = trust_at_resolution(root, 1)
    loss_mid = information_loss(fine, mid, leaf_mapping)
    checks.append(("finer_less_loss", loss_mid <= loss + 0.01))

    # Optimal resolution
    opt = optimal_resolution(root, max_nodes=5)
    nodes_at_opt = trust_at_resolution(root, opt)
    checks.append(("within_budget", len(nodes_at_opt) <= 5))

    opt_tight = optimal_resolution(root, max_nodes=2)
    checks.append(("tight_budget", len(trust_at_resolution(root, opt_tight)) <= 2))

    return checks


# ============================================================
# S10 — Multi-Root Federation
# ============================================================

@dataclass
class FederatedHierarchy:
    """Multiple trust hierarchies connected via federation."""
    roots: Dict[str, TrustNode] = field(default_factory=dict)
    cross_links: List[Tuple[str, str, float]] = field(default_factory=list)  # (node_a, node_b, trust)

    def add_root(self, root: TrustNode):
        self.roots[root.node_id] = root

    def add_cross_link(self, node_a: str, node_b: str, trust: float):
        self.cross_links.append((node_a, node_b, trust))

    def find_node(self, node_id: str) -> Optional[TrustNode]:
        for root in self.roots.values():
            result = self._find_in(root, node_id)
            if result:
                return result
        return None

    def _find_in(self, node: TrustNode, node_id: str) -> Optional[TrustNode]:
        if node.node_id == node_id:
            return node
        for child in node.children:
            result = self._find_in(child, node_id)
            if result:
                return result
        return None

    def _node_to_root(self) -> Dict[str, str]:
        """Build mapping from every node ID to its root ID."""
        mapping = {}
        for root_id, root in self.roots.items():
            self._map_subtree(root, root_id, mapping)
        return mapping

    def _map_subtree(self, node: TrustNode, root_id: str, mapping: Dict[str, str]):
        mapping[node.node_id] = root_id
        for child in node.children:
            self._map_subtree(child, root_id, mapping)

    def federated_trust(self, source_root: str, target_root: str) -> float:
        """Compute trust between two federation roots via cross-links."""
        node_root = self._node_to_root()
        relevant = [(a, b, t) for a, b, t in self.cross_links
                     if (node_root.get(a) == source_root and node_root.get(b) == target_root)
                     or (node_root.get(a) == target_root and node_root.get(b) == source_root)]
        if not relevant:
            return 0.0
        return sum(t for _, _, t in relevant) / len(relevant)

    def total_leaf_count(self) -> int:
        return sum(len(root.leaves()) for root in self.roots.values())


def test_section_10():
    checks = []
    random.seed(42)

    fed = FederatedHierarchy()

    # Federation A
    root_a = TrustNode("fed_a", level=1)
    for i in range(5):
        root_a.add_child(TrustNode(f"a_{i}", talent=0.6 + random.random() * 0.2,
                                   training=0.5, temperament=0.6))
    aggregate_bottom_up(root_a, "weighted_mean")
    fed.add_root(root_a)

    # Federation B
    root_b = TrustNode("fed_b", level=1)
    for i in range(4):
        root_b.add_child(TrustNode(f"b_{i}", talent=0.5 + random.random() * 0.3,
                                   training=0.6, temperament=0.5))
    aggregate_bottom_up(root_b, "weighted_mean")
    fed.add_root(root_b)

    checks.append(("two_roots", len(fed.roots) == 2))
    checks.append(("total_leaves", fed.total_leaf_count() == 9))

    # Cross-links
    fed.add_cross_link("a_0", "b_0", 0.7)
    fed.add_cross_link("a_1", "b_1", 0.5)

    cross_trust = fed.federated_trust("fed_a", "fed_b")
    checks.append(("cross_trust_positive", cross_trust > 0))

    # Find nodes across federation
    found = fed.find_node("a_0")
    checks.append(("find_cross_fed", found is not None and found.node_id == "a_0"))

    not_found = fed.find_node("nonexistent")
    checks.append(("not_found", not_found is None))

    return checks


# ============================================================
# S11 — Performance & Scale
# ============================================================

def build_balanced_tree(depth: int, branching: int, level: int = 0) -> TrustNode:
    """Build a balanced trust hierarchy."""
    node_id = f"n_{level}_{random.randint(0, 999999)}"
    node = TrustNode(node_id, level=depth - level,
                     talent=random.uniform(0.3, 0.9),
                     training=random.uniform(0.3, 0.9),
                     temperament=random.uniform(0.3, 0.9))
    if level < depth:
        for _ in range(branching):
            child = build_balanced_tree(depth, branching, level + 1)
            node.add_child(child)
    return node


def test_section_11():
    checks = []

    import time as time_mod
    random.seed(42)

    # Build large hierarchy: depth=4, branching=4 = 341 nodes
    start = time_mod.perf_counter()
    root = build_balanced_tree(4, 4)
    build_time = time_mod.perf_counter() - start
    checks.append(("build_fast", build_time < 2.0))
    checks.append(("node_count", root.size > 300))

    # Bottom-up aggregation
    start = time_mod.perf_counter()
    aggregate_bottom_up(root, "weighted_mean")
    agg_time = time_mod.perf_counter() - start
    checks.append(("aggregation_fast", agg_time < 2.0))

    # Cross-level consistency
    start = time_mod.perf_counter()
    errors = verify_cross_level_consistency(root)
    verify_time = time_mod.perf_counter() - start
    checks.append(("consistency_verified", len(errors) == 0))
    checks.append(("verify_fast", verify_time < 2.0))

    # Self-similarity
    start = time_mod.perf_counter()
    ss = self_similarity_score(root)
    ss_time = time_mod.perf_counter() - start
    checks.append(("self_similarity_computed", 0 <= ss <= 1))
    checks.append(("ss_fast", ss_time < 2.0))

    # Resolution queries
    r0 = trust_at_resolution(root, 0)
    r_max = trust_at_resolution(root, 10)
    checks.append(("resolution_0_minimal", len(r0) == 1))
    checks.append(("resolution_max_all", len(r_max) == len(root.leaves())))

    return checks


# ============================================================
# Main
# ============================================================

def main():
    random.seed(42)

    sections = [
        ("S1 Trust Hierarchy Node", test_section_1),
        ("S2 Bottom-Up Aggregation", test_section_2),
        ("S3 Top-Down Decomposition", test_section_3),
        ("S4 Zoom Operations", test_section_4),
        ("S5 Level-Appropriate Resolution", test_section_5),
        ("S6 Cross-Level Consistency", test_section_6),
        ("S7 Fractal Self-Similarity", test_section_7),
        ("S8 Dynamic Hierarchy Updates", test_section_8),
        ("S9 Trust Granularity Trade-offs", test_section_9),
        ("S10 Multi-Root Federation", test_section_10),
        ("S11 Performance & Scale", test_section_11),
    ]

    total_pass = 0
    total_fail = 0
    failures = []

    for name, test_fn in sections:
        checks = test_fn()
        passed = sum(1 for _, ok in checks if ok)
        failed = sum(1 for _, ok in checks if not ok)
        total_pass += passed
        total_fail += failed
        status = "✓" if failed == 0 else "✗"
        print(f"  {status} {name}: {passed}/{passed+failed}")
        for check_name, ok in checks:
            if not ok:
                failures.append(f"    FAIL: {check_name}")

    print(f"\nTotal: {total_pass}/{total_pass+total_fail}")
    if failures:
        print(f"\nFailed checks:")
        for f in failures:
            print(f)


if __name__ == "__main__":
    main()
