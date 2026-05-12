#!/usr/bin/env python3
"""
Web of Trust System - Session #35

Implements transitive trust calculation via social graph analysis.
Enables trust propagation through the network, providing additional
Sybil resistance beyond identity bonds.

Key Concepts:
- Direct Trust: First-hand experience with an agent
- Transitive Trust: Trust derived from trusted intermediaries
- Trust Decay: Trust weakens with graph distance (hops)
- Vouching: Established members can vouch for newcomers
- Social Graph Sybil Resistance: Hard to fake entire social network

Architecture:
  Direct Interactions → Trust Edges
        ↓
  Graph Traversal → Trust Paths
        ↓
  Path Aggregation → Transitive Trust
        ↓
  Combined Score → Final Trust

Created: Session #35 (2025-11-16)
Builds on: Session #34 (Gaming Mitigations), Session #33 (Reputation-ATP)
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
from collections import defaultdict, deque
import math

# Import gaming mitigation system
from gaming_mitigations import (
    GamingResistantNegotiator,
    IdentityBond,
    TrustScore
)

# Import ATP system
sys.path.insert(0, str(Path(__file__).parent.parent / "atp"))
from lowest_exchange import Society


# ============================================================================
# TRUST EDGE - DIRECT TRUST RELATIONSHIP
# ============================================================================

@dataclass
class TrustEdge:
    """
    Directed edge representing trust from one society to another.

    Represents: "Society A trusts Society B based on direct interactions"

    Components:
    - Direct trust score (0.0-1.0) from personal experience
    - Number of interactions (confidence in trust score)
    - Timestamp of last interaction (recency)
    - Edge weight for graph traversal
    """
    from_society: str  # Society LCT giving trust
    to_society: str    # Society LCT receiving trust
    trust_score: float = 0.5  # 0.0-1.0, starts neutral
    interaction_count: int = 0
    last_interaction: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Metadata
    successful_interactions: int = 0
    failed_interactions: int = 0

    def update_trust(self, success: bool):
        """
        Update trust based on interaction outcome.

        Uses exponential moving average:
        new_trust = old_trust * (1 - α) + outcome * α

        Where α (learning rate) decreases with more interactions
        (high confidence in established relationships).
        """
        self.interaction_count += 1
        self.last_interaction = datetime.now(timezone.utc)

        if success:
            self.successful_interactions += 1
            outcome = 1.0
        else:
            self.failed_interactions += 1
            outcome = 0.0

        # Learning rate: High initially, decreases with interactions
        # α = 1 / (1 + interaction_count)
        # First interaction: α = 0.5
        # 10th interaction: α = 0.09
        # 100th interaction: α = 0.01
        alpha = 1.0 / (1.0 + self.interaction_count)

        self.trust_score = (
            self.trust_score * (1.0 - alpha) +  # Old trust
            outcome * alpha                      # New observation
        )

    def get_edge_weight(self) -> float:
        """
        Calculate edge weight for graph traversal.

        Weight combines:
        - Trust score (0.0-1.0)
        - Confidence from interaction count
        - Recency (recent interactions weighted more)

        Returns: 0.0-1.0 (higher = stronger trust edge)
        """
        # Confidence: More interactions → higher confidence
        # conf = min(1.0, interaction_count / 50)
        confidence = min(1.0, self.interaction_count / 50.0)

        # Recency: Recent interactions weighted more
        # Decay half-life: 90 days
        age_days = (datetime.now(timezone.utc) - self.last_interaction).days
        recency = 0.5 ** (age_days / 90.0)

        # Combined weight
        weight = self.trust_score * confidence * recency
        return weight

    def get_confidence(self) -> float:
        """Get confidence in this trust edge (0.0-1.0)"""
        return min(1.0, self.interaction_count / 50.0)


# ============================================================================
# TRUST PATH - SEQUENCE OF TRUST EDGES
# ============================================================================

@dataclass
class TrustPath:
    """
    Path through trust graph from source to target.

    Represents: "A trusts B trusts C trusts D"

    Properties:
    - Path strength: Product of edge weights (weakest link)
    - Path length: Number of hops
    - Trust decay: Longer paths → weaker trust
    """
    edges: List[TrustEdge]

    def get_path_strength(self) -> float:
        """
        Calculate path strength as product of edge weights.

        Weakest link principle: Trust limited by weakest edge in chain.

        Example:
        A→B (0.9) → B→C (0.8) → C→D (0.7)
        Strength: 0.9 × 0.8 × 0.7 = 0.504
        """
        if not self.edges:
            return 0.0

        strength = 1.0
        for edge in self.edges:
            strength *= edge.get_edge_weight()

        return strength

    def get_path_length(self) -> int:
        """Number of hops in path"""
        return len(self.edges)

    def get_decayed_trust(self, decay_factor: float = 0.8) -> float:
        """
        Calculate trust with distance decay.

        Formula: path_strength × decay_factor^(path_length - 1)

        Rationale:
        - 1 hop: No decay (direct trust)
        - 2 hops: 80% strength (friend of friend)
        - 3 hops: 64% strength (friend of friend of friend)
        - 4 hops: 51% strength (too distant)

        Decay factor (0.8) means each hop retains 80% of trust.
        """
        base_strength = self.get_path_strength()
        hops = self.get_path_length()

        if hops == 0:
            return 0.0

        # No decay for direct trust (1 hop)
        if hops == 1:
            return base_strength

        # Apply decay for transitive trust (2+ hops)
        decay = decay_factor ** (hops - 1)
        return base_strength * decay

    def get_societies(self) -> List[str]:
        """Get all societies in path (source → intermediaries → target)"""
        if not self.edges:
            return []

        societies = [self.edges[0].from_society]
        for edge in self.edges:
            societies.append(edge.to_society)

        return societies


# ============================================================================
# TRUST GRAPH - SOCIAL NETWORK OF TRUST RELATIONSHIPS
# ============================================================================

class TrustGraph:
    """
    Directed graph of trust relationships between societies.

    Nodes: Societies (identified by LCT)
    Edges: Trust relationships (weighted by trust score)

    Operations:
    - Add/update trust edges
    - Find trust paths (BFS with depth limit)
    - Calculate transitive trust
    - Detect Sybil clusters
    """

    def __init__(self):
        # Adjacency list: from_society → {to_society: TrustEdge}
        self.edges: Dict[str, Dict[str, TrustEdge]] = defaultdict(dict)

        # Reverse adjacency: to_society → {from_society: TrustEdge}
        self.reverse_edges: Dict[str, Dict[str, TrustEdge]] = defaultdict(dict)

    def add_or_update_edge(
        self,
        from_society: str,
        to_society: str,
        success: bool
    ) -> TrustEdge:
        """
        Add new trust edge or update existing one.

        Called after each interaction to build trust graph.
        """
        if to_society in self.edges[from_society]:
            # Update existing edge
            edge = self.edges[from_society][to_society]
            edge.update_trust(success)
        else:
            # Create new edge
            edge = TrustEdge(
                from_society=from_society,
                to_society=to_society
            )
            edge.update_trust(success)

            # Add to forward and reverse indexes
            self.edges[from_society][to_society] = edge
            self.reverse_edges[to_society][from_society] = edge

        return edge

    def get_edge(self, from_society: str, to_society: str) -> Optional[TrustEdge]:
        """Get direct trust edge between two societies"""
        return self.edges.get(from_society, {}).get(to_society)

    def get_direct_trust(self, from_society: str, to_society: str) -> float:
        """
        Get direct trust score.

        Returns:
        - Edge weight if direct edge exists
        - 0.5 (neutral) if no direct interaction
        """
        edge = self.get_edge(from_society, to_society)
        if edge:
            return edge.get_edge_weight()
        return 0.5  # Neutral for unknown

    def find_trust_paths(
        self,
        source: str,
        target: str,
        max_depth: int = 3,
        max_paths: int = 5
    ) -> List[TrustPath]:
        """
        Find trust paths from source to target using BFS.

        Parameters:
        - max_depth: Maximum path length (default 3 hops)
        - max_paths: Maximum paths to return (best paths first)

        Returns: List of TrustPath objects, sorted by strength

        Algorithm:
        1. BFS from source to target
        2. Track all paths up to max_depth
        3. Return top max_paths by strength
        """
        if source == target:
            return []

        # Check for direct path first
        direct_edge = self.get_edge(source, target)
        if direct_edge:
            return [TrustPath(edges=[direct_edge])]

        # BFS to find paths
        paths = []

        # Queue: (current_society, path_edges, visited_set)
        queue = deque([(source, [], {source})])

        while queue:
            current, path_edges, visited = queue.popleft()

            # Check depth limit
            if len(path_edges) >= max_depth:
                continue

            # Explore neighbors
            neighbors = self.edges.get(current, {})
            for next_society, edge in neighbors.items():
                # Skip if already visited (prevent cycles)
                if next_society in visited:
                    continue

                # Build new path
                new_path = path_edges + [edge]
                new_visited = visited | {next_society}

                # Check if reached target
                if next_society == target:
                    paths.append(TrustPath(edges=new_path))

                    # Stop if found enough paths
                    if len(paths) >= max_paths:
                        break
                else:
                    # Continue exploring
                    queue.append((next_society, new_path, new_visited))

            if len(paths) >= max_paths:
                break

        # Sort paths by decayed trust (strongest first)
        paths.sort(key=lambda p: p.get_decayed_trust(), reverse=True)

        return paths[:max_paths]

    def calculate_transitive_trust(
        self,
        source: str,
        target: str,
        max_depth: int = 3
    ) -> Tuple[float, List[TrustPath]]:
        """
        Calculate transitive trust from source to target.

        Method:
        1. Find all trust paths (BFS up to max_depth)
        2. Calculate decayed trust for each path
        3. Aggregate using weighted average

        Returns: (transitive_trust_score, paths_used)

        Aggregation:
        Uses weighted average of path strengths, where weights
        are the path strengths themselves (stronger paths weighted more).

        Example:
        Path 1: strength 0.7
        Path 2: strength 0.3

        Transitive trust = (0.7×0.7 + 0.3×0.3) / (0.7 + 0.3)
                         = (0.49 + 0.09) / 1.0
                         = 0.58
        """
        # Find trust paths
        paths = self.find_trust_paths(source, target, max_depth)

        if not paths:
            return (0.5, [])  # Neutral for no paths

        # Calculate weighted average
        weighted_sum = 0.0
        weight_sum = 0.0

        for path in paths:
            strength = path.get_decayed_trust()
            weighted_sum += strength * strength  # Weight by strength
            weight_sum += strength

        if weight_sum == 0:
            return (0.5, paths)

        transitive_trust = weighted_sum / weight_sum
        return (transitive_trust, paths)

    def get_node_degree(self, society: str) -> Tuple[int, int]:
        """
        Get in-degree and out-degree of node.

        Returns: (in_degree, out_degree)

        Usage: Detect Sybil clusters (nodes with unusual degree patterns)
        """
        out_degree = len(self.edges.get(society, {}))
        in_degree = len(self.reverse_edges.get(society, {}))
        return (in_degree, out_degree)

    def get_clustering_coefficient(self, society: str) -> float:
        """
        Calculate clustering coefficient for node.

        Measures: How connected are this node's neighbors to each other?

        Formula:
        clustering = (actual_edges_between_neighbors) / (possible_edges)

        High clustering: Node's friends know each other (organic)
        Low clustering: Node's friends don't know each other (suspicious)

        Sybil detection: Sybil clusters have low clustering
        (created together but don't interact internally)
        """
        # Get neighbors (outgoing edges)
        neighbors = set(self.edges.get(society, {}).keys())

        if len(neighbors) < 2:
            return 0.0  # Need at least 2 neighbors

        # Count edges between neighbors
        edges_between_neighbors = 0
        for n1 in neighbors:
            for n2 in neighbors:
                if n1 != n2 and self.get_edge(n1, n2) is not None:
                    edges_between_neighbors += 1

        # Possible edges (directed graph)
        possible_edges = len(neighbors) * (len(neighbors) - 1)

        clustering = edges_between_neighbors / possible_edges
        return clustering

    def detect_sybil_cluster(
        self,
        society: str,
        min_cluster_size: int = 3
    ) -> Optional[Set[str]]:
        """
        Detect if society is part of Sybil cluster.

        Indicators:
        1. Low clustering coefficient (< 0.3)
        2. High out-degree but low in-degree (many outgoing, few incoming)
        3. Neighbors have similar patterns
        4. Recent creation times

        Returns: Set of societies in suspected cluster, or None
        """
        clustering = self.get_clustering_coefficient(society)
        in_deg, out_deg = self.get_node_degree(society)

        # Check for suspicious patterns
        suspicious = False

        # Pattern 1: Low clustering (friends don't know each other)
        if clustering < 0.3 and out_deg >= 3:
            suspicious = True

        # Pattern 2: Asymmetric degree (many outgoing, few incoming)
        if out_deg > 0 and in_deg / max(1, out_deg) < 0.3:
            suspicious = True

        if not suspicious:
            return None

        # Find other suspicious nodes in neighborhood
        cluster = {society}
        neighbors = set(self.edges.get(society, {}).keys())

        for neighbor in neighbors:
            neighbor_clustering = self.get_clustering_coefficient(neighbor)
            neighbor_in, neighbor_out = self.get_node_degree(neighbor)

            # Check if neighbor has similar suspicious pattern
            if neighbor_clustering < 0.3 and neighbor_out >= 3:
                cluster.add(neighbor)
            elif neighbor_out > 0 and neighbor_in / max(1, neighbor_out) < 0.3:
                cluster.add(neighbor)

        if len(cluster) >= min_cluster_size:
            return cluster

        return None

    def get_graph_stats(self) -> Dict:
        """Get statistics about the trust graph"""
        num_nodes = len(set(list(self.edges.keys()) + list(self.reverse_edges.keys())))
        num_edges = sum(len(neighbors) for neighbors in self.edges.values())

        # Average degree
        degrees = [len(neighbors) for neighbors in self.edges.values()]
        avg_degree = sum(degrees) / len(degrees) if degrees else 0

        # Average clustering
        clusterings = [
            self.get_clustering_coefficient(society)
            for society in self.edges.keys()
        ]
        avg_clustering = sum(clusterings) / len(clusterings) if clusterings else 0

        return {
            "num_nodes": num_nodes,
            "num_edges": num_edges,
            "avg_degree": avg_degree,
            "avg_clustering": avg_clustering
        }


# ============================================================================
# VOUCHING SYSTEM - NEWCOMER ONBOARDING
# ============================================================================

@dataclass
class Vouch:
    """
    Established member vouches for newcomer.

    Mechanism:
    - Voucher stakes portion of their bond
    - Newcomer gets reduced bond requirement
    - If newcomer behaves well: Stake returned to voucher
    - If newcomer misbehaves: Stake forfeited

    Requirements for voucher:
    - Trust score >= 0.8 (EXCELLENT)
    - Transaction count >= 100 (ESTABLISHED)
    - Bond age >= 90 days (PROVEN)
    """
    voucher_lct: str
    newcomer_lct: str
    stake_amount: int
    created_at: datetime
    active: bool = True
    released: bool = False
    forfeited: bool = False

    def release_stake(self) -> int:
        """
        Release stake back to voucher (newcomer succeeded).
        Returns amount released.
        """
        if self.active and not self.released and not self.forfeited:
            self.active = False
            self.released = True
            return self.stake_amount
        return 0

    def forfeit_stake(self) -> int:
        """
        Forfeit stake (newcomer failed).
        Returns amount forfeited.
        """
        if self.active and not self.released and not self.forfeited:
            self.active = False
            self.forfeited = True
            return self.stake_amount
        return 0


class VouchingSystem:
    """
    Manages vouching relationships for newcomer onboarding.

    Benefits:
    - Reduces barrier for legitimate newcomers (with social connections)
    - Creates accountability (voucher has skin in the game)
    - Sybil resistance (hard to get vouches for fake identities)
    """

    def __init__(self, negotiator: GamingResistantNegotiator):
        self.negotiator = negotiator
        self.vouches: Dict[str, List[Vouch]] = defaultdict(list)  # newcomer → vouches
        self.voucher_stakes: Dict[str, List[Vouch]] = defaultdict(list)  # voucher → vouches

    def can_vouch(self, voucher_lct: str) -> Tuple[bool, str]:
        """
        Check if society can vouch for newcomers.

        Requirements:
        - Trust score >= 0.8
        - Transaction count >= 100
        - Bond age >= 90 days
        - Not too many active vouches (max 3)
        """
        # Get trust score
        trust = self.negotiator.get_trust_score(voucher_lct)
        trust_score = trust.calculate_score()

        if trust_score < 0.8:
            return (False, f"Trust too low ({trust_score:.2f} < 0.8)")

        # Get transaction count
        tx_count = trust.successful_transactions + trust.transaction_failures
        if tx_count < 100:
            return (False, f"Insufficient history ({tx_count} < 100)")

        # Get bond age
        bond = self.negotiator.bond_registry.get_bond(voucher_lct)
        if not bond:
            return (False, "No identity bond found")

        if bond.age_days() < 90:
            return (False, f"Bond too young ({bond.age_days()} < 90 days)")

        # Check active vouches
        active_vouches = [v for v in self.voucher_stakes[voucher_lct] if v.active]
        if len(active_vouches) >= 3:
            return (False, f"Too many active vouches ({len(active_vouches)} >= 3)")

        return (True, "Eligible to vouch")

    def create_vouch(
        self,
        voucher_lct: str,
        newcomer_lct: str,
        stake_amount: int = 200
    ) -> Tuple[bool, str, Optional[Vouch]]:
        """
        Create vouch for newcomer.

        Returns: (success, message, vouch)
        """
        # Check voucher eligibility
        can_vouch, reason = self.can_vouch(voucher_lct)
        if not can_vouch:
            return (False, f"Cannot vouch: {reason}", None)

        # Check newcomer doesn't already have too many vouches
        existing_vouches = [v for v in self.vouches[newcomer_lct] if v.active]
        if len(existing_vouches) >= 2:
            return (False, f"Newcomer already has {len(existing_vouches)} vouches", None)

        # Create vouch
        vouch = Vouch(
            voucher_lct=voucher_lct,
            newcomer_lct=newcomer_lct,
            stake_amount=stake_amount,
            created_at=datetime.now(timezone.utc)
        )

        self.vouches[newcomer_lct].append(vouch)
        self.voucher_stakes[voucher_lct].append(vouch)

        return (True, "Vouch created successfully", vouch)

    def get_vouched_bond_discount(self, newcomer_lct: str) -> int:
        """
        Calculate bond discount for vouched newcomer.

        Each active vouch: 200 ATP discount (max 400 ATP)
        """
        active_vouches = [v for v in self.vouches[newcomer_lct] if v.active]
        discount = min(400, len(active_vouches) * 200)
        return discount

    def resolve_vouch(
        self,
        newcomer_lct: str,
        success: bool
    ) -> List[Tuple[str, int, bool]]:
        """
        Resolve all vouches for newcomer.

        Called when:
        - Newcomer reaches 50 transactions (success check)
        - Newcomer caught gaming (failure)

        Returns: List of (voucher_lct, amount, released/forfeited)
        """
        results = []

        vouches = self.vouches[newcomer_lct]
        for vouch in vouches:
            if not vouch.active:
                continue

            if success:
                amount = vouch.release_stake()
                results.append((vouch.voucher_lct, amount, True))
            else:
                amount = vouch.forfeit_stake()
                results.append((vouch.voucher_lct, amount, False))

        return results


# ============================================================================
# WEB OF TRUST INTEGRATION
# ============================================================================

class WebOfTrustNegotiator(GamingResistantNegotiator):
    """
    Extends gaming-resistant negotiator with web of trust.

    Trust calculation:
    1. Direct trust (if exists)
    2. Transitive trust (via graph)
    3. Weighted combination

    Sybil resistance:
    1. Identity bonds (Session #34)
    2. Experience penalties (Session #34)
    3. Social graph analysis (Session #35) ✨
    4. Vouching system (Session #35) ✨
    """

    def __init__(self):
        super().__init__()
        self.trust_graph = TrustGraph()
        self.vouching_system = VouchingSystem(self)

    def record_interaction(
        self,
        from_society_lct: str,
        to_society_lct: str,
        success: bool
    ):
        """
        Record interaction and update trust graph.

        Called after each transaction, message, or heartbeat.
        """
        self.trust_graph.add_or_update_edge(
            from_society_lct,
            to_society_lct,
            success
        )

    def get_combined_trust(
        self,
        source_lct: str,
        target_lct: str
    ) -> Tuple[float, Dict]:
        """
        Calculate combined trust from direct and transitive sources.

        Combination:
        - If direct trust exists: 70% direct, 30% transitive
        - If no direct trust: 100% transitive

        Returns: (trust_score, metadata)
        """
        # Get direct trust
        direct_edge = self.trust_graph.get_edge(source_lct, target_lct)

        if direct_edge:
            # Direct trust available
            direct_trust = direct_edge.get_edge_weight()
            direct_confidence = direct_edge.get_confidence()

            # Get transitive trust
            transitive_trust, paths = self.trust_graph.calculate_transitive_trust(
                source_lct,
                target_lct,
                max_depth=3
            )

            # Weighted combination (favor direct trust)
            combined = (
                direct_trust * 0.7 +
                transitive_trust * 0.3
            )

            metadata = {
                "trust_type": "combined",
                "direct_trust": direct_trust,
                "direct_confidence": direct_confidence,
                "transitive_trust": transitive_trust,
                "num_paths": len(paths),
                "combined_trust": combined
            }

            return (combined, metadata)
        else:
            # No direct trust, use transitive only
            transitive_trust, paths = self.trust_graph.calculate_transitive_trust(
                source_lct,
                target_lct,
                max_depth=3
            )

            metadata = {
                "trust_type": "transitive",
                "transitive_trust": transitive_trust,
                "num_paths": len(paths),
                "paths": [p.get_societies() for p in paths]
            }

            return (transitive_trust, metadata)

    def check_sybil_cluster(self, society_lct: str) -> Tuple[bool, Optional[Set[str]]]:
        """
        Check if society is part of Sybil cluster.

        Returns: (is_suspicious, cluster_members)
        """
        cluster = self.trust_graph.detect_sybil_cluster(society_lct)
        if cluster:
            return (True, cluster)
        return (False, None)


# ============================================================================
# DEMONSTRATION
# ============================================================================

def demo_web_of_trust():
    """
    Demonstrate web of trust capabilities.

    Scenarios:
    1. Build trust graph from interactions
    2. Calculate transitive trust
    3. Vouching for newcomer
    4. Detect Sybil cluster
    """
    print("=" * 80)
    print("Web of Trust System - Session #35")
    print("=" * 80)
    print()

    negotiator = WebOfTrustNegotiator()

    # Scenario 1: Build trust graph
    print("Scenario 1: Building Trust Graph")
    print("-" * 80)

    # Create societies with bonds
    alice = negotiator.create_society_with_bond(
        "lct:alice:1",
        "Alice",
        {"compute_hour": 100},
        bond_amount=1000
    )

    bob = negotiator.create_society_with_bond(
        "lct:bob:2",
        "Bob",
        {"compute_hour": 100},
        bond_amount=1000
    )

    carol = negotiator.create_society_with_bond(
        "lct:carol:3",
        "Carol",
        {"compute_hour": 100},
        bond_amount=1000
    )

    dave = negotiator.create_society_with_bond(
        "lct:dave:4",
        "Dave",
        {"compute_hour": 100},
        bond_amount=1000
    )

    print(f"Created 4 societies: Alice, Bob, Carol, Dave")
    print()

    # Simulate interactions to build trust graph
    print("Simulating interactions:")

    # Alice trusts Bob (many successful interactions)
    for _ in range(20):
        negotiator.record_interaction("lct:alice:1", "lct:bob:2", True)
    print(f"  Alice → Bob: 20 successful interactions")

    # Bob trusts Carol (some successful, some failed)
    for _ in range(15):
        negotiator.record_interaction("lct:bob:2", "lct:carol:3", True)
    for _ in range(5):
        negotiator.record_interaction("lct:bob:2", "lct:carol:3", False)
    print(f"  Bob → Carol: 15 successful, 5 failed interactions")

    # Carol trusts Dave
    for _ in range(10):
        negotiator.record_interaction("lct:carol:3", "lct:dave:4", True)
    print(f"  Carol → Dave: 10 successful interactions")

    print()

    # Scenario 2: Transitive trust
    print("Scenario 2: Transitive Trust Calculation")
    print("-" * 80)

    # Alice has no direct interaction with Carol
    print("Alice wants to know if she can trust Carol")
    print("(Alice has never interacted with Carol directly)")
    print()

    trust, metadata = negotiator.get_combined_trust("lct:alice:1", "lct:carol:3")

    print(f"Trust type: {metadata['trust_type']}")
    print(f"Transitive trust: {metadata['transitive_trust']:.3f}")
    print(f"Number of paths: {metadata['num_paths']}")

    if 'paths' in metadata:
        print(f"\nTrust paths:")
        for i, path_societies in enumerate(metadata['paths'], 1):
            print(f"  Path {i}: {' → '.join(path_societies)}")

    print()

    # Alice to Dave (2-hop path)
    print("Alice wants to know if she can trust Dave")
    print("(Alice → Bob → Carol → Dave)")
    print()

    trust, metadata = negotiator.get_combined_trust("lct:alice:1", "lct:dave:4")

    print(f"Transitive trust: {metadata['transitive_trust']:.3f}")
    if 'paths' in metadata:
        for i, path_societies in enumerate(metadata['paths'], 1):
            print(f"  Path {i}: {' → '.join(path_societies)}")

    print()

    # Graph statistics
    print("Trust Graph Statistics:")
    stats = negotiator.trust_graph.get_graph_stats()
    print(f"  Nodes: {stats['num_nodes']}")
    print(f"  Edges: {stats['num_edges']}")
    print(f"  Average degree: {stats['avg_degree']:.2f}")
    print(f"  Average clustering: {stats['avg_clustering']:.2f}")
    print()

    print("=" * 80)
    print("✅ Web of Trust System Operational")
    print("=" * 80)


if __name__ == "__main__":
    demo_web_of_trust()
