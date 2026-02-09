"""
Track FL: MRH Context Boundary Attacks (Attacks 323-328)

Attacks on Markov Relevancy Horizon (MRH) context boundaries.
MRH defines the dynamic context of relationships surrounding each entity,
determining what context is "in scope" for trust calculations, operations,
and access control.

Key insight: MRH gates context access across the entire Web4 system.
Violating or manipulating these boundaries undermines all trust guarantees.

Reference:
- web4-standard/core-spec/mrh-tensors.md
- Markov blanket concept: Beyond horizon depth, relationships become irrelevant

Default horizon_depth = 3 (entity, connections, their connections)

Added: 2026-02-09
"""

import hashlib
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Callable, Any
from enum import Enum


@dataclass
class AttackResult:
    """Result of an attack simulation."""
    attack_name: str
    success: bool
    setup_cost_atp: float
    gain_atp: float
    roi: float
    detection_probability: float
    time_to_detection_hours: float
    blocks_until_detected: int
    trust_damage: float
    description: str
    mitigation: str
    raw_data: Dict


# ============================================================================
# MRH INFRASTRUCTURE
# ============================================================================


class RelationType(Enum):
    """Types of MRH relationships."""
    BOUND_TO = "bound_to"           # Permanent binding
    PAIRED_WITH = "paired_with"     # Session-based pairing
    WITNESSED_BY = "witnessed_by"   # Trust attestation
    PARENT_BINDING = "parent"       # Hierarchical parent
    CHILD_BINDING = "child"         # Hierarchical child
    SIBLING_BINDING = "sibling"     # Shared parent


@dataclass
class MRHNode:
    """An entity in the MRH graph."""
    lct_id: str
    entity_type: str  # human, ai, device, role, service
    trust_scores: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MRHEdge:
    """A relationship edge in the MRH graph."""
    source: str
    target: str
    relation: RelationType
    probability: float  # Edge weight/strength
    distance: int       # Hop distance from query origin
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class MRHGraph:
    """Markov Relevancy Horizon graph implementation."""
    
    DEFAULT_HORIZON_DEPTH = 3
    
    def __init__(self, horizon_depth: int = DEFAULT_HORIZON_DEPTH):
        self.nodes: Dict[str, MRHNode] = {}
        self.edges: List[MRHEdge] = []
        self.horizon_depth = horizon_depth
        self.adjacency: Dict[str, List[str]] = {}  # For fast traversal
    
    def add_node(self, node: MRHNode):
        self.nodes[node.lct_id] = node
        if node.lct_id not in self.adjacency:
            self.adjacency[node.lct_id] = []
    
    def add_edge(self, edge: MRHEdge):
        self.edges.append(edge)
        if edge.source not in self.adjacency:
            self.adjacency[edge.source] = []
        if edge.target not in self.adjacency[edge.source]:
            self.adjacency[edge.source].append(edge.target)
        # Bidirectional for most relations
        if edge.relation != RelationType.WITNESSED_BY:
            if edge.target not in self.adjacency:
                self.adjacency[edge.target] = []
            if edge.source not in self.adjacency[edge.target]:
                self.adjacency[edge.target].append(edge.source)
    
    def get_entities_within_horizon(self, origin: str, 
                                      depth: Optional[int] = None) -> Set[str]:
        """Get all entities within MRH horizon of origin."""
        if depth is None:
            depth = self.horizon_depth
        
        within_horizon = {origin}
        current_frontier = {origin}
        
        for d in range(depth):
            next_frontier = set()
            for node in current_frontier:
                if node in self.adjacency:
                    for neighbor in self.adjacency[node]:
                        if neighbor not in within_horizon:
                            within_horizon.add(neighbor)
                            next_frontier.add(neighbor)
            current_frontier = next_frontier
        
        return within_horizon
    
    def is_in_context(self, origin: str, target: str) -> Tuple[bool, int]:
        """Check if target is within origin's MRH context."""
        # BFS to find shortest path
        if origin == target:
            return True, 0
        
        visited = {origin}
        queue = [(origin, 0)]
        
        while queue:
            current, dist = queue.pop(0)
            if dist >= self.horizon_depth:
                continue
            
            if current in self.adjacency:
                for neighbor in self.adjacency[current]:
                    if neighbor == target:
                        return True, dist + 1
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, dist + 1))
        
        return False, -1
    
    def get_path(self, origin: str, target: str) -> Optional[List[str]]:
        """Get shortest path from origin to target."""
        if origin == target:
            return [origin]
        
        visited = {origin}
        queue = [(origin, [origin])]
        
        while queue:
            current, path = queue.pop(0)
            if len(path) > self.horizon_depth + 1:
                continue
            
            if current in self.adjacency:
                for neighbor in self.adjacency[current]:
                    if neighbor == target:
                        return path + [neighbor]
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))
        
        return None


# ============================================================================
# ATTACK FL-1a: MRH BOUNDARY VIOLATION
# ============================================================================


def attack_mrh_boundary_violation() -> AttackResult:
    """
    ATTACK FL-1a: MRH Boundary Violation

    Attempt to access entities outside the permitted MRH horizon,
    bypassing context boundaries.

    Vectors:
    1. Direct out-of-context access
    2. Horizon depth override
    3. Context inheritance exploit
    4. Transitive access abuse
    5. Stale context reference
    6. Cross-graph context leak
    """

    defenses = {
        "boundary_enforcement": False,
        "depth_validation": False,
        "inheritance_check": False,
        "transitive_limit": False,
        "context_freshness": False,
        "graph_isolation": False,
    }

    now = time.time()
    
    # Build MRH graph
    graph = MRHGraph(horizon_depth=3)
    
    # Create network: A -> B -> C -> D -> E -> F (6 hops)
    for entity in ["A", "B", "C", "D", "E", "F"]:
        graph.add_node(MRHNode(lct_id=entity, entity_type="agent"))
    
    graph.add_edge(MRHEdge("A", "B", RelationType.PAIRED_WITH, 0.9, 1, now))
    graph.add_edge(MRHEdge("B", "C", RelationType.PAIRED_WITH, 0.9, 2, now))
    graph.add_edge(MRHEdge("C", "D", RelationType.PAIRED_WITH, 0.9, 3, now))
    graph.add_edge(MRHEdge("D", "E", RelationType.PAIRED_WITH, 0.9, 4, now))
    graph.add_edge(MRHEdge("E", "F", RelationType.PAIRED_WITH, 0.9, 5, now))

    # ========================================================================
    # Vector 1: Boundary Enforcement Defense
    # ========================================================================

    def enforce_boundary(graph: MRHGraph, origin: str, target: str) -> Tuple[bool, str]:
        """Enforce MRH boundary - deny access outside horizon."""
        in_context, distance = graph.is_in_context(origin, target)
        
        if not in_context:
            return False, f"target_outside_horizon"
        
        if distance > graph.horizon_depth:
            return False, f"distance_exceeds_horizon: {distance}/{graph.horizon_depth}"
        
        return True, "ok"

    # Attack: Try to access F from A (5 hops away, horizon is 3)
    allowed, reason = enforce_boundary(graph, "A", "F")
    
    if not allowed:
        defenses["boundary_enforcement"] = True

    # ========================================================================
    # Vector 2: Depth Validation Defense
    # ========================================================================

    def validate_depth_parameter(requested_depth: int,
                                   max_allowed: int = 3,
                                   min_allowed: int = 1) -> Tuple[bool, int]:
        """Validate requested horizon depth is within bounds."""
        if requested_depth < min_allowed:
            return False, min_allowed
        if requested_depth > max_allowed:
            return False, max_allowed
        return True, requested_depth

    # Attack: Request absurdly deep horizon
    valid, capped_depth = validate_depth_parameter(100)  # Try depth=100
    
    if not valid and capped_depth <= 3:
        defenses["depth_validation"] = True

    # ========================================================================
    # Vector 3: Inheritance Check Defense
    # ========================================================================

    @dataclass
    class ContextInheritance:
        child_lct: str
        parent_lct: str
        inherited_horizon: Set[str]
        granted_at: float

    def check_inheritance(inheritance: ContextInheritance,
                           graph: MRHGraph,
                           max_inheritance_age_seconds: float = 3600) -> Tuple[bool, List[str]]:
        """Check context inheritance is valid and fresh."""
        issues = []
        
        # Check parent-child relationship exists
        path = graph.get_path(inheritance.child_lct, inheritance.parent_lct)
        if path is None or len(path) > 2:  # Direct relationship only
            issues.append("no_direct_parent_relationship")
        
        # Check inheritance age
        age = time.time() - inheritance.granted_at
        if age > max_inheritance_age_seconds:
            issues.append(f"stale_inheritance: {age:.0f}s old")
        
        # Check inherited entities are actually in parent's horizon
        parent_horizon = graph.get_entities_within_horizon(inheritance.parent_lct)
        invalid_inherited = inheritance.inherited_horizon - parent_horizon
        if invalid_inherited:
            issues.append(f"invalid_inherited_entities: {invalid_inherited}")
        
        return len(issues) == 0, issues

    # Attack: Claim inheritance from non-parent with expanded context
    fake_inheritance = ContextInheritance(
        child_lct="A",
        parent_lct="F",  # Not a parent, 5 hops away
        inherited_horizon={"E", "F"},  # Claim access to distant entities
        granted_at=now - 7200  # 2 hours ago (stale)
    )
    
    valid, issues = check_inheritance(fake_inheritance, graph)
    
    if not valid:
        defenses["inheritance_check"] = True

    # ========================================================================
    # Vector 4: Transitive Limit Defense
    # ========================================================================

    @dataclass
    class ContextRequest:
        requester: str
        target: str
        via_intermediaries: List[str]
        
    def limit_transitive_access(request: ContextRequest,
                                  graph: MRHGraph,
                                  max_intermediaries: int = 2) -> Tuple[bool, str]:
        """Limit transitive context access through intermediaries."""
        # Direct access doesn't need intermediaries
        in_context, _ = graph.is_in_context(request.requester, request.target)
        if in_context:
            return True, "direct_access"
        
        # Too many intermediaries
        if len(request.via_intermediaries) > max_intermediaries:
            return False, f"too_many_intermediaries: {len(request.via_intermediaries)}/{max_intermediaries}"
        
        # Verify each intermediary is in requester's context
        for i, intermediary in enumerate(request.via_intermediaries):
            in_ctx, _ = graph.is_in_context(request.requester, intermediary)
            if not in_ctx:
                return False, f"intermediary_{i}_not_in_context"
        
        return True, "ok"

    # Attack: Chain through many intermediaries to reach distant entity
    chained_request = ContextRequest(
        requester="A",
        target="F",
        via_intermediaries=["B", "C", "D", "E"]  # 4 intermediaries
    )
    
    allowed, reason = limit_transitive_access(chained_request, graph)
    
    if not allowed:
        defenses["transitive_limit"] = True

    # ========================================================================
    # Vector 5: Context Freshness Defense
    # ========================================================================

    @dataclass
    class CachedContext:
        lct_id: str
        horizon_entities: Set[str]
        computed_at: float
        ttl_seconds: float

    def check_context_freshness(cached: CachedContext,
                                  max_age_seconds: float = 300) -> Tuple[bool, str]:
        """Ensure cached context is fresh enough."""
        age = time.time() - cached.computed_at
        
        if age > max_age_seconds:
            return False, f"context_stale: {age:.0f}s > {max_age_seconds}s"
        
        if age > cached.ttl_seconds:
            return False, f"ttl_exceeded: {age:.0f}s > {cached.ttl_seconds}s"
        
        return True, "ok"

    # Attack: Use very old cached context that included more entities
    stale_cache = CachedContext(
        lct_id="A",
        horizon_entities={"A", "B", "C", "D", "E", "F"},  # Overly broad
        computed_at=now - 86400,  # 24 hours ago
        ttl_seconds=60
    )
    
    fresh, reason = check_context_freshness(stale_cache)
    
    if not fresh:
        defenses["context_freshness"] = True

    # ========================================================================
    # Vector 6: Graph Isolation Defense
    # ========================================================================

    def check_graph_isolation(graph_a: MRHGraph, 
                                graph_b: MRHGraph,
                                query_origin: str,
                                query_target: str) -> Tuple[bool, str]:
        """Ensure contexts from different graphs don't leak."""
        # Origin must be in graph_a
        if query_origin not in graph_a.nodes:
            return False, "origin_not_in_source_graph"
        
        # Target must be in graph_a (not just in graph_b)
        if query_target not in graph_a.nodes:
            return False, "target_not_in_source_graph"
        
        # Even if target exists in both, must be reachable in same graph
        in_context, _ = graph_a.is_in_context(query_origin, query_target)
        if not in_context:
            return False, "not_reachable_in_same_graph"
        
        return True, "ok"

    # Create separate graph with entity F
    graph_b = MRHGraph(horizon_depth=3)
    graph_b.add_node(MRHNode(lct_id="F", entity_type="agent"))
    graph_b.add_node(MRHNode(lct_id="X", entity_type="agent"))
    graph_b.add_edge(MRHEdge("F", "X", RelationType.PAIRED_WITH, 0.9, 1, now))
    
    # Attack: Try to use graph_b context to access F from graph_a
    isolated, reason = check_graph_isolation(graph, graph_b, "A", "F")
    
    if not isolated:
        defenses["graph_isolation"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4
    
    within_a = graph.get_entities_within_horizon("A")

    return AttackResult(
        attack_name="MRH Boundary Violation (FL-1a)",
        success=attack_success,
        setup_cost_atp=20000.0,
        gain_atp=150000.0 if attack_success else 0.0,
        roi=(150000.0 / 20000.0) if attack_success else -1.0,
        detection_probability=0.85 if defenses_held >= 4 else 0.30,
        time_to_detection_hours=4.0,
        blocks_until_detected=40,
        trust_damage=0.90,
        description=f"""
MRH BOUNDARY VIOLATION ATTACK (Track FL-1a)

Attempt to access entities outside permitted MRH horizon.

Attack Pattern:
1. Direct access to entity 5 hops away (horizon=3)
2. Request horizon depth of 100 (vs max 3)
3. Claim false parent inheritance from distant entity
4. Chain through 4 intermediaries (vs max 2)
5. Use 24-hour-old cached context
6. Exploit cross-graph context leak

Graph Structure:
A -> B -> C -> D -> E -> F (5 hops)
A's horizon (depth=3): {within_a}
Target F in context: {graph.is_in_context("A", "F")[0]}

Defense Analysis:
- Boundary enforcement: {"HELD" if defenses["boundary_enforcement"] else "BYPASSED"}
- Depth validation: {"HELD" if defenses["depth_validation"] else "BYPASSED"}
- Inheritance check: {"HELD" if defenses["inheritance_check"] else "BYPASSED"}
- Transitive limit: {"HELD" if defenses["transitive_limit"] else "BYPASSED"}
- Context freshness: {"HELD" if defenses["context_freshness"] else "BYPASSED"}
- Graph isolation: {"HELD" if defenses["graph_isolation"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FL-1a: MRH Boundary Violation Defense:
1. Enforce strict horizon boundary checks
2. Validate and cap depth parameters
3. Verify inheritance relationships
4. Limit transitive intermediary chains
5. Require fresh context (short TTL)
6. Isolate separate graph contexts

MRH boundaries must be cryptographically enforced.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "horizon_depth": graph.horizon_depth,
            "a_context_size": len(within_a),
        }
    )


# ============================================================================
# ATTACK FL-1b: HORIZON MANIPULATION
# ============================================================================


def attack_horizon_manipulation() -> AttackResult:
    """
    ATTACK FL-1b: Horizon Manipulation

    Manipulate MRH horizon parameters to expand or contract
    context in unauthorized ways.

    Vectors:
    1. Dynamic horizon expansion
    2. Selective horizon contraction
    3. Per-relationship depth override
    4. Horizon flickering (rapid changes)
    5. Split horizon attack
    6. Horizon time travel
    """

    defenses = {
        "horizon_immutability": False,
        "contraction_audit": False,
        "depth_consistency": False,
        "change_rate_limit": False,
        "horizon_integrity": False,
        "temporal_consistency": False,
    }

    now = time.time()
    
    @dataclass
    class HorizonConfig:
        lct_id: str
        depth: int
        last_modified: float
        modification_count: int
        config_hash: str

    # ========================================================================
    # Vector 1: Horizon Immutability Defense
    # ========================================================================

    def check_horizon_immutability(config: HorizonConfig,
                                     allowed_modifiers: Set[str],
                                     modifier: str) -> Tuple[bool, str]:
        """Check if horizon modification is authorized."""
        if modifier not in allowed_modifiers:
            return False, f"unauthorized_modifier: {modifier}"
        
        # Standard horizons should not change
        if config.depth == 3:  # Standard depth
            return False, "cannot_modify_standard_horizon"
        
        return True, "ok"

    config = HorizonConfig("entity_A", 3, now - 3600, 0, "abc123")
    
    # Attack: Unauthorized modifier tries to change horizon
    allowed, reason = check_horizon_immutability(
        config, {"system_admin"}, "attacker"
    )
    
    if not allowed:
        defenses["horizon_immutability"] = True

    # ========================================================================
    # Vector 2: Contraction Audit Defense
    # ========================================================================

    @dataclass
    class HorizonChange:
        lct_id: str
        old_depth: int
        new_depth: int
        reason: str
        authorized_by: str
        timestamp: float

    def audit_contraction(change: HorizonChange,
                           min_notification_period: float = 86400) -> Tuple[bool, List[str]]:
        """Audit horizon contraction for compliance."""
        issues = []
        
        # Contraction should be rare and well-justified
        if change.new_depth < change.old_depth:
            if not change.reason:
                issues.append("contraction_without_reason")
            
            # Should have advance notice
            if change.timestamp < now + min_notification_period:
                issues.append("insufficient_notice_period")
            
            # Check authorization
            if "admin" not in change.authorized_by.lower():
                issues.append("unauthorized_contraction")
        
        return len(issues) == 0, issues

    # Attack: Contract horizon immediately without authorization
    malicious_contraction = HorizonChange(
        lct_id="victim",
        old_depth=3,
        new_depth=1,  # Severely restrict
        reason="",    # No reason
        authorized_by="attacker",
        timestamp=now  # Immediate
    )
    
    valid, issues = audit_contraction(malicious_contraction)
    
    if not valid:
        defenses["contraction_audit"] = True

    # ========================================================================
    # Vector 3: Depth Consistency Defense
    # ========================================================================

    def check_depth_consistency(configs: List[HorizonConfig],
                                  expected_depth: int = 3) -> List[str]:
        """Ensure depth is consistent across related entities."""
        inconsistencies = []
        
        depths = [c.depth for c in configs]
        
        # Check variance
        if len(set(depths)) > 1:
            inconsistencies.append(f"depth_variance: {set(depths)}")
        
        # Check against expected
        for config in configs:
            if config.depth != expected_depth:
                inconsistencies.append(f"{config.lct_id}: depth={config.depth}, expected={expected_depth}")
        
        return inconsistencies

    # Attack: Set inconsistent depths across related entities
    inconsistent_configs = [
        HorizonConfig("A", 3, now, 0, "hash_a"),
        HorizonConfig("B", 5, now, 1, "hash_b"),  # Expanded!
        HorizonConfig("C", 1, now, 2, "hash_c"),  # Contracted!
    ]
    
    inconsistencies = check_depth_consistency(inconsistent_configs)
    
    if inconsistencies:
        defenses["depth_consistency"] = True

    # ========================================================================
    # Vector 4: Change Rate Limit Defense
    # ========================================================================

    def limit_change_rate(config: HorizonConfig,
                           max_changes_per_day: int = 2) -> Tuple[bool, str]:
        """Limit how often horizon can change."""
        if config.modification_count >= max_changes_per_day:
            return False, f"rate_limit_exceeded: {config.modification_count}/{max_changes_per_day}"
        
        return True, "ok"

    # Attack: Rapidly flicker horizon depth
    flickering_config = HorizonConfig(
        lct_id="target",
        depth=3,
        last_modified=now,
        modification_count=50,  # Many changes!
        config_hash="hash"
    )
    
    allowed, reason = limit_change_rate(flickering_config)
    
    if not allowed:
        defenses["change_rate_limit"] = True

    # ========================================================================
    # Vector 5: Horizon Integrity Defense
    # ========================================================================

    def verify_horizon_integrity(config: HorizonConfig,
                                   stored_hash: str) -> Tuple[bool, str]:
        """Verify horizon config hasn't been tampered with."""
        # Compute expected hash
        data = f"{config.lct_id}:{config.depth}:{config.last_modified}"
        expected_hash = hashlib.sha256(data.encode()).hexdigest()[:8]
        
        if config.config_hash != expected_hash:
            return False, f"integrity_violation: hash_mismatch"
        
        if stored_hash != config.config_hash:
            return False, f"integrity_violation: stored_hash_mismatch"
        
        return True, "ok"

    # Attack: Modify config without updating hash
    tampered_config = HorizonConfig(
        lct_id="entity",
        depth=10,  # Tampered!
        last_modified=now,
        modification_count=0,
        config_hash="abc123"  # Old hash
    )
    
    valid, reason = verify_horizon_integrity(tampered_config, "abc123")
    
    if not valid:
        defenses["horizon_integrity"] = True

    # ========================================================================
    # Vector 6: Temporal Consistency Defense
    # ========================================================================

    @dataclass
    class HorizonSnapshot:
        lct_id: str
        depth: int
        as_of_time: float
        valid_until: float

    def check_temporal_consistency(snapshots: List[HorizonSnapshot],
                                     current_time: float) -> List[str]:
        """Check for temporal manipulation in horizon history."""
        issues = []
        
        # Sort by time
        sorted_snapshots = sorted(snapshots, key=lambda s: s.as_of_time)
        
        for i, snap in enumerate(sorted_snapshots):
            # Check for gaps or overlaps
            if i > 0:
                prev = sorted_snapshots[i-1]
                if snap.as_of_time < prev.valid_until:
                    issues.append(f"overlapping_periods: {prev.as_of_time}-{prev.valid_until} vs {snap.as_of_time}")
            
            # Check for future-dated snapshots
            if snap.as_of_time > current_time:
                issues.append(f"future_dated_snapshot: {snap.as_of_time}")
            
            # Check for impossible depth changes
            if i > 0:
                prev = sorted_snapshots[i-1]
                if abs(snap.depth - prev.depth) > 1:
                    issues.append(f"impossible_depth_jump: {prev.depth} -> {snap.depth}")
        
        return issues

    # Attack: Create future-dated snapshot with expanded horizon
    attack_snapshots = [
        HorizonSnapshot("entity", 3, now - 3600, now - 1800),
        HorizonSnapshot("entity", 3, now - 1800, now),
        HorizonSnapshot("entity", 10, now + 3600, now + 7200),  # Future!
    ]
    
    temporal_issues = check_temporal_consistency(attack_snapshots, now)
    
    if temporal_issues:
        defenses["temporal_consistency"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Horizon Manipulation (FL-1b)",
        success=attack_success,
        setup_cost_atp=18000.0,
        gain_atp=120000.0 if attack_success else 0.0,
        roi=(120000.0 / 18000.0) if attack_success else -1.0,
        detection_probability=0.80 if defenses_held >= 4 else 0.25,
        time_to_detection_hours=6.0,
        blocks_until_detected=60,
        trust_damage=0.85,
        description=f"""
HORIZON MANIPULATION ATTACK (Track FL-1b)

Manipulate MRH horizon parameters in unauthorized ways.

Attack Pattern:
1. Unauthorized modifier changes horizon
2. Contract horizon without notice/authorization
3. Create inconsistent depths (1, 3, 5)
4. Rapidly change horizon (50 changes)
5. Tamper with config without updating hash
6. Create future-dated snapshots

Manipulation Analysis:
- Unauthorized modification blocked: {not check_horizon_immutability(config, {"system_admin"}, "attacker")[0]}
- Contraction issues: {len(audit_contraction(malicious_contraction)[1])}
- Depth inconsistencies: {len(inconsistencies)}
- Change rate exceeded: {flickering_config.modification_count > 2}
- Temporal issues: {len(temporal_issues)}

Defense Analysis:
- Horizon immutability: {"HELD" if defenses["horizon_immutability"] else "BYPASSED"}
- Contraction audit: {"HELD" if defenses["contraction_audit"] else "BYPASSED"}
- Depth consistency: {"HELD" if defenses["depth_consistency"] else "BYPASSED"}
- Change rate limit: {"HELD" if defenses["change_rate_limit"] else "BYPASSED"}
- Horizon integrity: {"HELD" if defenses["horizon_integrity"] else "BYPASSED"}
- Temporal consistency: {"HELD" if defenses["temporal_consistency"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FL-1b: Horizon Manipulation Defense:
1. Restrict horizon modification to admins
2. Audit and require notice for contractions
3. Enforce consistent depth across entities
4. Rate limit horizon changes
5. Verify config integrity via hashing
6. Check temporal consistency

Horizon parameters must be immutable under normal operation.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "depth_inconsistencies": len(inconsistencies),
        }
    )


# ============================================================================
# ATTACK FL-2a: CONTEXT POISONING
# ============================================================================


def attack_context_poisoning() -> AttackResult:
    """
    ATTACK FL-2a: Context Poisoning

    Poison an entity's MRH context by injecting malicious
    relationships or corrupting existing ones.

    Vectors:
    1. Relationship injection
    2. Edge weight manipulation
    3. Node attribute corruption
    4. Trust score poisoning
    5. Metadata injection
    6. Graph structure corruption
    """

    defenses = {
        "relationship_validation": False,
        "weight_bounds_check": False,
        "attribute_verification": False,
        "trust_score_audit": False,
        "metadata_sanitization": False,
        "structure_integrity": False,
    }

    now = time.time()
    graph = MRHGraph(horizon_depth=3)
    
    # Setup legitimate graph
    for entity in ["victim", "friend_1", "friend_2"]:
        graph.add_node(MRHNode(lct_id=entity, entity_type="agent", 
                               trust_scores={"general": 0.8}))
    
    graph.add_edge(MRHEdge("victim", "friend_1", RelationType.PAIRED_WITH, 0.9, 1, now))
    graph.add_edge(MRHEdge("victim", "friend_2", RelationType.PAIRED_WITH, 0.8, 1, now))

    # ========================================================================
    # Vector 1: Relationship Validation Defense
    # ========================================================================

    def validate_new_relationship(edge: MRHEdge,
                                    graph: MRHGraph,
                                    allowed_sources: Set[str]) -> Tuple[bool, List[str]]:
        """Validate new relationship before adding to graph."""
        issues = []
        
        # Source must be known
        if edge.source not in graph.nodes:
            issues.append("unknown_source")
        
        # Source must be authorized to create relationships
        if edge.source not in allowed_sources:
            issues.append("unauthorized_source")
        
        # Target must be known
        if edge.target not in graph.nodes:
            issues.append("unknown_target")
        
        # Self-relationships suspicious
        if edge.source == edge.target:
            issues.append("self_relationship")
        
        # Check relationship type validity
        valid_types = [r for r in RelationType]
        if edge.relation not in valid_types:
            issues.append("invalid_relation_type")
        
        return len(issues) == 0, issues

    # Attack: Inject relationship from unknown attacker
    malicious_edge = MRHEdge(
        source="attacker",
        target="victim",
        relation=RelationType.PAIRED_WITH,
        probability=1.0,
        distance=1,
        timestamp=now
    )
    
    valid, issues = validate_new_relationship(
        malicious_edge, graph, {"victim", "friend_1", "friend_2"}
    )
    
    if not valid:
        defenses["relationship_validation"] = True

    # ========================================================================
    # Vector 2: Weight Bounds Check Defense
    # ========================================================================

    def check_weight_bounds(edge: MRHEdge,
                             min_weight: float = 0.0,
                             max_weight: float = 1.0) -> Tuple[bool, str]:
        """Check edge weight is within valid bounds."""
        if edge.probability < min_weight:
            return False, f"weight_below_minimum: {edge.probability} < {min_weight}"
        
        if edge.probability > max_weight:
            return False, f"weight_above_maximum: {edge.probability} > {max_weight}"
        
        return True, "ok"

    # Attack: Set impossibly high edge weight
    inflated_edge = MRHEdge(
        source="friend_1",
        target="victim",
        relation=RelationType.PAIRED_WITH,
        probability=100.0,  # Way above 1.0!
        distance=1,
        timestamp=now
    )
    
    valid, reason = check_weight_bounds(inflated_edge)
    
    if not valid:
        defenses["weight_bounds_check"] = True

    # ========================================================================
    # Vector 3: Attribute Verification Defense
    # ========================================================================

    def verify_node_attributes(node: MRHNode,
                                 valid_types: Set[str],
                                 max_metadata_size: int = 1024) -> Tuple[bool, List[str]]:
        """Verify node attributes are valid."""
        issues = []
        
        # Check entity type
        if node.entity_type not in valid_types:
            issues.append(f"invalid_entity_type: {node.entity_type}")
        
        # Check metadata size
        import json
        metadata_size = len(json.dumps(node.metadata))
        if metadata_size > max_metadata_size:
            issues.append(f"metadata_too_large: {metadata_size} > {max_metadata_size}")
        
        # Check for suspicious attributes
        if "admin" in str(node.metadata).lower():
            issues.append("suspicious_admin_reference")
        
        return len(issues) == 0, issues

    # Attack: Create node with invalid type and suspicious metadata
    malicious_node = MRHNode(
        lct_id="injected",
        entity_type="superadmin",  # Invalid type!
        metadata={"role": "admin", "bypass_all": True}  # Suspicious!
    )
    
    valid, issues = verify_node_attributes(
        malicious_node, {"human", "ai", "device", "agent", "service"}
    )
    
    if not valid:
        defenses["attribute_verification"] = True

    # ========================================================================
    # Vector 4: Trust Score Audit Defense
    # ========================================================================

    @dataclass
    class TrustScoreChange:
        lct_id: str
        dimension: str
        old_value: float
        new_value: float
        change_reason: str
        timestamp: float

    def audit_trust_score_change(change: TrustScoreChange,
                                   max_increase: float = 0.1,
                                   max_decrease: float = 0.2) -> Tuple[bool, str]:
        """Audit trust score changes for reasonableness."""
        delta = change.new_value - change.old_value
        
        if delta > max_increase:
            return False, f"excessive_increase: {delta:.2f} > {max_increase}"
        
        if delta < -max_decrease:
            return False, f"excessive_decrease: {delta:.2f} < -{max_decrease}"
        
        if not change.change_reason:
            return False, "missing_change_reason"
        
        return True, "ok"

    # Attack: Massively inflate trust score
    malicious_change = TrustScoreChange(
        lct_id="victim",
        dimension="general",
        old_value=0.3,
        new_value=1.0,  # +0.7, way above limit!
        change_reason="",  # No reason
        timestamp=now
    )
    
    valid, reason = audit_trust_score_change(malicious_change)
    
    if not valid:
        defenses["trust_score_audit"] = True

    # ========================================================================
    # Vector 5: Metadata Sanitization Defense
    # ========================================================================

    def sanitize_metadata(metadata: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """Sanitize metadata to remove malicious content."""
        sanitized = {}
        removed = []
        
        dangerous_keys = ["admin", "bypass", "override", "root", "sudo", "exec"]
        
        for key, value in metadata.items():
            # Check key
            if any(d in key.lower() for d in dangerous_keys):
                removed.append(f"key:{key}")
                continue
            
            # Check value for injection
            if isinstance(value, str):
                if any(d in value.lower() for d in dangerous_keys):
                    removed.append(f"value:{key}")
                    continue
                if "<script" in value.lower() or "javascript:" in value.lower():
                    removed.append(f"script_injection:{key}")
                    continue
            
            sanitized[key] = value
        
        return sanitized, removed

    # Attack: Inject malicious metadata
    malicious_metadata = {
        "description": "normal description",
        "admin_bypass": True,
        "exec_command": "rm -rf /",
        "xss_payload": "<script>alert('hacked')</script>"
    }
    
    sanitized, removed = sanitize_metadata(malicious_metadata)
    
    if removed:
        defenses["metadata_sanitization"] = True

    # ========================================================================
    # Vector 6: Structure Integrity Defense
    # ========================================================================

    def check_structure_integrity(graph: MRHGraph) -> List[str]:
        """Check graph structure for integrity issues."""
        issues = []
        
        # Check for orphaned nodes (no edges)
        connected = set()
        for edge in graph.edges:
            connected.add(edge.source)
            connected.add(edge.target)
        
        orphans = set(graph.nodes.keys()) - connected
        if orphans:
            issues.append(f"orphaned_nodes: {orphans}")
        
        # Check for duplicate edges
        edge_set = set()
        for edge in graph.edges:
            edge_key = (edge.source, edge.target, edge.relation)
            if edge_key in edge_set:
                issues.append(f"duplicate_edge: {edge_key}")
            edge_set.add(edge_key)
        
        # Check for inconsistent adjacency
        for node_id in graph.nodes:
            if node_id not in graph.adjacency:
                issues.append(f"missing_adjacency: {node_id}")
        
        return issues

    # Add orphaned node and duplicate edge
    graph.add_node(MRHNode(lct_id="orphan", entity_type="agent"))
    graph.edges.append(MRHEdge("victim", "friend_1", RelationType.PAIRED_WITH, 0.9, 1, now))
    
    structure_issues = check_structure_integrity(graph)
    
    if structure_issues:
        defenses["structure_integrity"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Context Poisoning (FL-2a)",
        success=attack_success,
        setup_cost_atp=25000.0,
        gain_atp=140000.0 if attack_success else 0.0,
        roi=(140000.0 / 25000.0) if attack_success else -1.0,
        detection_probability=0.75 if defenses_held >= 4 else 0.30,
        time_to_detection_hours=12.0,
        blocks_until_detected=120,
        trust_damage=0.88,
        description=f"""
CONTEXT POISONING ATTACK (Track FL-2a)

Poison MRH context by injecting malicious content.

Attack Pattern:
1. Inject relationship from unknown attacker
2. Set edge weight to 100.0 (max is 1.0)
3. Create node with invalid "superadmin" type
4. Inflate trust score by +0.7 (max +0.1)
5. Inject admin_bypass and script payload
6. Create orphan node and duplicate edge

Poisoning Analysis:
- Relationship validation issues: {len(validate_new_relationship(malicious_edge, graph, {"victim"})[1])}
- Edge weight out of bounds: {inflated_edge.probability > 1.0}
- Node attribute issues: {len(verify_node_attributes(malicious_node, {"agent"})[1])}
- Trust change excessive: {malicious_change.new_value - malicious_change.old_value > 0.1}
- Metadata items removed: {len(removed)}
- Structure issues: {len(structure_issues)}

Defense Analysis:
- Relationship validation: {"HELD" if defenses["relationship_validation"] else "BYPASSED"}
- Weight bounds check: {"HELD" if defenses["weight_bounds_check"] else "BYPASSED"}
- Attribute verification: {"HELD" if defenses["attribute_verification"] else "BYPASSED"}
- Trust score audit: {"HELD" if defenses["trust_score_audit"] else "BYPASSED"}
- Metadata sanitization: {"HELD" if defenses["metadata_sanitization"] else "BYPASSED"}
- Structure integrity: {"HELD" if defenses["structure_integrity"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FL-2a: Context Poisoning Defense:
1. Validate all new relationships
2. Enforce edge weight bounds [0, 1]
3. Verify node attributes against schema
4. Audit trust score changes
5. Sanitize all metadata input
6. Check structure integrity regularly

Context must be validated at every boundary.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "removed_metadata": removed,
        }
    )


# ============================================================================
# ATTACK FL-2b: CONTEXT AMPLIFICATION
# ============================================================================


def attack_context_amplification() -> AttackResult:
    """
    ATTACK FL-2b: Context Amplification

    Amplify influence within MRH context to gain disproportionate
    access or trust.

    Vectors:
    1. Hub formation exploit
    2. Clique amplification
    3. Bridge position abuse
    4. Trust cascade manipulation
    5. Echo chamber creation
    6. Centrality gaming
    """

    defenses = {
        "hub_detection": False,
        "clique_limit": False,
        "bridge_monitoring": False,
        "cascade_dampening": False,
        "diversity_requirement": False,
        "centrality_cap": False,
    }

    now = time.time()
    graph = MRHGraph(horizon_depth=3)
    
    # Create base network
    for i in range(20):
        graph.add_node(MRHNode(lct_id=f"agent_{i}", entity_type="agent"))
    
    # Normal connections
    for i in range(19):
        graph.add_edge(MRHEdge(f"agent_{i}", f"agent_{i+1}", 
                               RelationType.PAIRED_WITH, 0.7, 1, now))

    # ========================================================================
    # Vector 1: Hub Detection Defense
    # ========================================================================

    def detect_hub_formation(graph: MRHGraph,
                               max_connections: int = 10) -> List[str]:
        """Detect entities forming suspicious hubs."""
        hubs = []
        
        for node_id in graph.adjacency:
            connection_count = len(graph.adjacency[node_id])
            if connection_count > max_connections:
                hubs.append(f"{node_id}: {connection_count} connections")
        
        return hubs

    # Attack: Create hub with many connections
    graph.add_node(MRHNode(lct_id="hub_attacker", entity_type="agent"))
    for i in range(15):
        graph.add_edge(MRHEdge("hub_attacker", f"agent_{i}", 
                               RelationType.PAIRED_WITH, 0.9, 1, now))
    
    hubs = detect_hub_formation(graph)
    
    if hubs:
        defenses["hub_detection"] = True

    # ========================================================================
    # Vector 2: Clique Limit Defense
    # ========================================================================

    def check_clique_limit(graph: MRHGraph,
                            suspicious_nodes: Set[str],
                            max_clique_density: float = 0.5) -> Tuple[bool, str]:
        """Check if nodes form suspiciously dense clique."""
        if len(suspicious_nodes) < 3:
            return True, "ok"
        
        # Count edges among suspicious nodes
        internal_edges = 0
        possible_edges = len(suspicious_nodes) * (len(suspicious_nodes) - 1) / 2
        
        for edge in graph.edges:
            if edge.source in suspicious_nodes and edge.target in suspicious_nodes:
                internal_edges += 1
        
        density = internal_edges / possible_edges if possible_edges > 0 else 0
        
        if density > max_clique_density:
            return False, f"excessive_clique_density: {density:.2f} > {max_clique_density}"
        
        return True, "ok"

    # Create suspicious clique
    clique_nodes = {f"clique_{i}" for i in range(5)}
    for node_id in clique_nodes:
        graph.add_node(MRHNode(lct_id=node_id, entity_type="agent"))
    
    # Fully connect clique
    clique_list = list(clique_nodes)
    for i, a in enumerate(clique_list):
        for b in clique_list[i+1:]:
            graph.add_edge(MRHEdge(a, b, RelationType.PAIRED_WITH, 0.95, 1, now))
    
    clique_ok, reason = check_clique_limit(graph, clique_nodes)
    
    if not clique_ok:
        defenses["clique_limit"] = True

    # ========================================================================
    # Vector 3: Bridge Monitoring Defense
    # ========================================================================

    def monitor_bridge_positions(graph: MRHGraph,
                                   max_bridge_power: float = 0.3) -> List[str]:
        """Monitor entities in bridge positions."""
        warnings = []
        
        # Simplified: check nodes that connect otherwise disconnected groups
        for node_id in graph.adjacency:
            neighbors = set(graph.adjacency[node_id])
            
            # Check if removing this node would disconnect groups
            total_reachable_via_node = len(neighbors)
            total_nodes = len(graph.nodes)
            
            bridge_power = total_reachable_via_node / total_nodes if total_nodes > 0 else 0
            
            if bridge_power > max_bridge_power:
                warnings.append(f"{node_id}: bridge_power={bridge_power:.2f}")
        
        return warnings

    bridge_warnings = monitor_bridge_positions(graph)
    
    if bridge_warnings:
        defenses["bridge_monitoring"] = True

    # ========================================================================
    # Vector 4: Cascade Dampening Defense
    # ========================================================================

    @dataclass
    class TrustPropagation:
        source: str
        target: str
        trust_delta: float
        hop_count: int
        timestamp: float

    def dampen_cascade(propagations: List[TrustPropagation],
                        decay_per_hop: float = 0.3,
                        min_delta: float = 0.01) -> List[TrustPropagation]:
        """Apply dampening to trust propagation cascades."""
        dampened = []
        
        for prop in propagations:
            dampened_delta = prop.trust_delta * (1 - decay_per_hop) ** prop.hop_count
            
            if abs(dampened_delta) >= min_delta:
                dampened.append(TrustPropagation(
                    source=prop.source,
                    target=prop.target,
                    trust_delta=dampened_delta,
                    hop_count=prop.hop_count,
                    timestamp=prop.timestamp
                ))
        
        return dampened

    # Attack: Try to propagate large trust change through cascade
    attack_propagations = [
        TrustPropagation("attacker", "hop_1", 0.5, 1, now),
        TrustPropagation("hop_1", "hop_2", 0.5, 2, now),
        TrustPropagation("hop_2", "hop_3", 0.5, 3, now),
        TrustPropagation("hop_3", "target", 0.5, 4, now),
    ]
    
    dampened = dampen_cascade(attack_propagations)
    
    # After 4 hops with 0.3 decay, should be very small
    if len(dampened) < len(attack_propagations):
        defenses["cascade_dampening"] = True

    # ========================================================================
    # Vector 5: Diversity Requirement Defense
    # ========================================================================

    def check_connection_diversity(graph: MRHGraph,
                                     node_id: str,
                                     min_type_diversity: int = 2) -> Tuple[bool, str]:
        """Check if connections are diverse (not all same type)."""
        if node_id not in graph.adjacency:
            return True, "no_connections"
        
        neighbor_types = set()
        for neighbor in graph.adjacency[node_id]:
            if neighbor in graph.nodes:
                neighbor_types.add(graph.nodes[neighbor].entity_type)
        
        if len(neighbor_types) < min_type_diversity:
            return False, f"insufficient_diversity: {len(neighbor_types)} types"
        
        return True, "ok"

    # All hub_attacker's connections are same type (agent)
    diverse, reason = check_connection_diversity(graph, "hub_attacker")
    
    if not diverse:
        defenses["diversity_requirement"] = True

    # ========================================================================
    # Vector 6: Centrality Cap Defense
    # ========================================================================

    def calculate_centrality(graph: MRHGraph) -> Dict[str, float]:
        """Calculate degree centrality for all nodes."""
        centrality = {}
        max_possible = len(graph.nodes) - 1
        
        for node_id in graph.nodes:
            connections = len(graph.adjacency.get(node_id, []))
            centrality[node_id] = connections / max_possible if max_possible > 0 else 0
        
        return centrality

    def cap_centrality(centrality: Dict[str, float],
                        max_centrality: float = 0.3) -> List[str]:
        """Identify nodes exceeding centrality cap."""
        violations = []
        
        for node_id, cent in centrality.items():
            if cent > max_centrality:
                violations.append(f"{node_id}: centrality={cent:.2f}")
        
        return violations

    centrality = calculate_centrality(graph)
    centrality_violations = cap_centrality(centrality)
    
    if centrality_violations:
        defenses["centrality_cap"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Context Amplification (FL-2b)",
        success=attack_success,
        setup_cost_atp=22000.0,
        gain_atp=130000.0 if attack_success else 0.0,
        roi=(130000.0 / 22000.0) if attack_success else -1.0,
        detection_probability=0.70 if defenses_held >= 4 else 0.25,
        time_to_detection_hours=24.0,
        blocks_until_detected=200,
        trust_damage=0.80,
        description=f"""
CONTEXT AMPLIFICATION ATTACK (Track FL-2b)

Amplify influence within MRH context for disproportionate power.

Attack Pattern:
1. Form hub with 15 connections (max 10)
2. Create fully-connected 5-node clique
3. Position at bridge between groups
4. Propagate 0.5 trust delta through 4 hops
5. Create homogeneous connections (all agents)
6. Maximize centrality

Amplification Analysis:
- Hub detected: {len(hubs) > 0} ({hubs if hubs else "none"})
- Clique density excessive: {not clique_ok}
- Bridge positions: {len(bridge_warnings)}
- Cascade propagations after damping: {len(dampened)}/{len(attack_propagations)}
- Connection diversity ok: {check_connection_diversity(graph, "hub_attacker")[0]}
- Centrality violations: {len(centrality_violations)}

Defense Analysis:
- Hub detection: {"HELD" if defenses["hub_detection"] else "BYPASSED"}
- Clique limit: {"HELD" if defenses["clique_limit"] else "BYPASSED"}
- Bridge monitoring: {"HELD" if defenses["bridge_monitoring"] else "BYPASSED"}
- Cascade dampening: {"HELD" if defenses["cascade_dampening"] else "BYPASSED"}
- Diversity requirement: {"HELD" if defenses["diversity_requirement"] else "BYPASSED"}
- Centrality cap: {"HELD" if defenses["centrality_cap"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FL-2b: Context Amplification Defense:
1. Detect and limit hub formation
2. Cap clique density
3. Monitor bridge positions
4. Dampen trust cascades
5. Require connection diversity
6. Cap node centrality

Influence must be bounded and distributed.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "hub_count": len(hubs),
            "centrality_violations": len(centrality_violations),
        }
    )


# ============================================================================
# ATTACK FL-3a: CROSS-NETWORK MRH CONFLICT
# ============================================================================


def attack_cross_network_mrh_conflict() -> AttackResult:
    """
    ATTACK FL-3a: Cross-Network MRH Conflict

    Exploit conflicts between MRH contexts in different networks
    or federations.

    Vectors:
    1. Conflicting horizon depths
    2. Relationship type mismatch
    3. Trust score disagreement
    4. Temporal desynchronization
    5. Schema incompatibility
    6. Authority overlap
    """

    defenses = {
        "depth_reconciliation": False,
        "type_mapping": False,
        "trust_arbitration": False,
        "temporal_sync": False,
        "schema_validation": False,
        "authority_resolution": False,
    }

    now = time.time()
    
    # Create two networks with different configs
    network_a = MRHGraph(horizon_depth=3)
    network_b = MRHGraph(horizon_depth=5)  # Different depth!
    
    # Shared entity exists in both
    shared_entity = "shared_entity"
    network_a.add_node(MRHNode(lct_id=shared_entity, entity_type="agent",
                                trust_scores={"general": 0.8}))
    network_b.add_node(MRHNode(lct_id=shared_entity, entity_type="service",  # Different type!
                                trust_scores={"general": 0.3}))  # Different trust!

    # ========================================================================
    # Vector 1: Depth Reconciliation Defense
    # ========================================================================

    def reconcile_horizon_depth(depth_a: int, depth_b: int,
                                  strategy: str = "minimum") -> Tuple[int, str]:
        """Reconcile conflicting horizon depths."""
        if depth_a == depth_b:
            return depth_a, "match"
        
        if strategy == "minimum":
            return min(depth_a, depth_b), "took_minimum"
        elif strategy == "maximum":
            return max(depth_a, depth_b), "took_maximum"
        elif strategy == "average":
            return (depth_a + depth_b) // 2, "averaged"
        else:
            return 3, "default"  # Fall back to standard

    # Conflict: depths 3 vs 5
    reconciled, strategy = reconcile_horizon_depth(
        network_a.horizon_depth, network_b.horizon_depth
    )
    
    if reconciled != network_b.horizon_depth:  # Didn't just accept larger
        defenses["depth_reconciliation"] = True

    # ========================================================================
    # Vector 2: Type Mapping Defense
    # ========================================================================

    def map_entity_types(type_a: str, type_b: str,
                          mapping: Dict[Tuple[str, str], str]) -> Tuple[str, bool]:
        """Map conflicting entity types to canonical type."""
        if type_a == type_b:
            return type_a, True
        
        # Check mapping
        key = (type_a, type_b) if type_a < type_b else (type_b, type_a)
        if key in mapping:
            return mapping[key], True
        
        # Conflict unresolved
        return type_a, False

    type_mapping = {
        ("agent", "service"): "agent",  # Agent takes precedence
    }
    
    canonical_type, resolved = map_entity_types(
        network_a.nodes[shared_entity].entity_type,
        network_b.nodes[shared_entity].entity_type,
        type_mapping
    )
    
    if resolved:
        defenses["type_mapping"] = True

    # ========================================================================
    # Vector 3: Trust Arbitration Defense
    # ========================================================================

    def arbitrate_trust_scores(trust_a: float, trust_b: float,
                                 weight_a: float = 0.5,
                                 weight_b: float = 0.5) -> Tuple[float, str]:
        """Arbitrate conflicting trust scores."""
        if abs(trust_a - trust_b) < 0.1:
            return (trust_a + trust_b) / 2, "averaged_close"
        
        # Large discrepancy - investigate
        if abs(trust_a - trust_b) > 0.3:
            # Take conservative (lower) value
            return min(trust_a, trust_b), "took_conservative"
        
        # Weighted average
        weighted = trust_a * weight_a + trust_b * weight_b
        return weighted, "weighted_average"

    # Conflict: 0.8 vs 0.3 trust
    arbitrated, method = arbitrate_trust_scores(
        network_a.nodes[shared_entity].trust_scores.get("general", 0.5),
        network_b.nodes[shared_entity].trust_scores.get("general", 0.5)
    )
    
    if method == "took_conservative":
        defenses["trust_arbitration"] = True

    # ========================================================================
    # Vector 4: Temporal Sync Defense
    # ========================================================================

    @dataclass
    class NetworkTimestamp:
        network_id: str
        local_time: float
        last_sync: float
        clock_drift: float

    def check_temporal_sync(ts_a: NetworkTimestamp, ts_b: NetworkTimestamp,
                             max_drift_seconds: float = 60.0) -> Tuple[bool, str]:
        """Check temporal synchronization between networks."""
        # Check absolute drift
        time_diff = abs(ts_a.local_time - ts_b.local_time)
        if time_diff > max_drift_seconds:
            return False, f"time_difference: {time_diff:.0f}s"
        
        # Check clock drift rates
        if abs(ts_a.clock_drift) > 0.01 or abs(ts_b.clock_drift) > 0.01:
            return False, f"excessive_drift_rate: {max(ts_a.clock_drift, ts_b.clock_drift)}"
        
        return True, "ok"

    # Attack: Desynchronized clocks
    ts_a = NetworkTimestamp("net_a", now, now - 60, 0.001)
    ts_b = NetworkTimestamp("net_b", now + 120, now - 3600, 0.05)  # 2 min ahead, stale sync
    
    synced, reason = check_temporal_sync(ts_a, ts_b)
    
    if not synced:
        defenses["temporal_sync"] = True

    # ========================================================================
    # Vector 5: Schema Validation Defense
    # ========================================================================

    @dataclass
    class MRHSchema:
        version: str
        required_fields: Set[str]
        optional_fields: Set[str]
        relationship_types: Set[str]

    def validate_schema_compatibility(schema_a: MRHSchema, 
                                        schema_b: MRHSchema) -> Tuple[bool, List[str]]:
        """Validate schema compatibility between networks."""
        issues = []
        
        # Version check
        if schema_a.version.split('.')[0] != schema_b.version.split('.')[0]:
            issues.append(f"major_version_mismatch: {schema_a.version} vs {schema_b.version}")
        
        # Required field intersection
        common_required = schema_a.required_fields & schema_b.required_fields
        if len(common_required) < len(schema_a.required_fields) * 0.8:
            issues.append("insufficient_required_field_overlap")
        
        # Relationship type compatibility
        if not schema_a.relationship_types & schema_b.relationship_types:
            issues.append("no_common_relationship_types")
        
        return len(issues) == 0, issues

    # Incompatible schemas
    schema_a = MRHSchema("1.0", {"lct_id", "type", "trust"}, {"meta"}, {"paired", "bound"})
    schema_b = MRHSchema("2.0", {"id", "category"}, {"data"}, {"linked"})  # Different everything!
    
    compatible, issues = validate_schema_compatibility(schema_a, schema_b)
    
    if not compatible:
        defenses["schema_validation"] = True

    # ========================================================================
    # Vector 6: Authority Resolution Defense
    # ========================================================================

    @dataclass
    class AuthorityClaim:
        network_id: str
        entity_id: str
        claim_type: str  # "primary", "secondary", "mirror"
        established_at: float

    def resolve_authority(claims: List[AuthorityClaim]) -> Tuple[str, str]:
        """Resolve conflicting authority claims."""
        if not claims:
            return "", "no_claims"
        
        # Filter to primary claims only
        primary_claims = [c for c in claims if c.claim_type == "primary"]
        
        if len(primary_claims) == 0:
            # Use oldest claim
            oldest = min(claims, key=lambda c: c.established_at)
            return oldest.network_id, "oldest_secondary"
        
        if len(primary_claims) == 1:
            return primary_claims[0].network_id, "single_primary"
        
        # Multiple primary claims - conflict!
        # Resolve by oldest primary
        oldest_primary = min(primary_claims, key=lambda c: c.established_at)
        return oldest_primary.network_id, "oldest_primary_of_multiple"

    # Conflicting authority claims
    conflict_claims = [
        AuthorityClaim("net_a", shared_entity, "primary", now - 1000),
        AuthorityClaim("net_b", shared_entity, "primary", now - 500),  # Also claims primary!
    ]
    
    authority, resolution = resolve_authority(conflict_claims)
    
    if resolution == "oldest_primary_of_multiple":
        defenses["authority_resolution"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Cross-Network MRH Conflict (FL-3a)",
        success=attack_success,
        setup_cost_atp=30000.0,
        gain_atp=160000.0 if attack_success else 0.0,
        roi=(160000.0 / 30000.0) if attack_success else -1.0,
        detection_probability=0.75 if defenses_held >= 4 else 0.25,
        time_to_detection_hours=48.0,
        blocks_until_detected=400,
        trust_damage=0.85,
        description=f"""
CROSS-NETWORK MRH CONFLICT ATTACK (Track FL-3a)

Exploit conflicts between MRH contexts in different networks.

Attack Pattern:
1. Different horizon depths (3 vs 5)
2. Conflicting entity types (agent vs service)
3. Trust score disagreement (0.8 vs 0.3)
4. Temporal desynchronization (2 min drift)
5. Incompatible schemas (v1.0 vs v2.0)
6. Competing authority claims (both primary)

Conflict Resolution:
- Depth reconciled to: {reconciled} ({strategy})
- Type mapped to: {canonical_type} (resolved: {resolved})
- Trust arbitrated to: {arbitrated:.2f} ({method})
- Temporal sync: {synced} ({reason})
- Schema compatible: {compatible}
- Authority: {authority} ({resolution})

Defense Analysis:
- Depth reconciliation: {"HELD" if defenses["depth_reconciliation"] else "BYPASSED"}
- Type mapping: {"HELD" if defenses["type_mapping"] else "BYPASSED"}
- Trust arbitration: {"HELD" if defenses["trust_arbitration"] else "BYPASSED"}
- Temporal sync: {"HELD" if defenses["temporal_sync"] else "BYPASSED"}
- Schema validation: {"HELD" if defenses["schema_validation"] else "BYPASSED"}
- Authority resolution: {"HELD" if defenses["authority_resolution"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FL-3a: Cross-Network MRH Conflict Defense:
1. Reconcile horizon depths conservatively
2. Map entity types via canonical mapping
3. Arbitrate trust conservatively (lower wins)
4. Require temporal synchronization
5. Validate schema compatibility
6. Resolve authority by age

Cross-network conflicts require explicit resolution.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "reconciled_depth": reconciled,
            "arbitrated_trust": arbitrated,
        }
    )


# ============================================================================
# ATTACK FL-3b: STALE CONTEXT EXPLOITATION
# ============================================================================


def attack_stale_context_exploitation() -> AttackResult:
    """
    ATTACK FL-3b: Stale Context Exploitation

    Exploit outdated MRH context data to access resources
    or entities no longer in valid context.

    Vectors:
    1. Cached context replay
    2. Revocation lag exploitation
    3. TTL bypass
    4. Historical context abuse
    5. Snapshot manipulation
    6. Refresh race condition
    """

    defenses = {
        "cache_expiration": False,
        "revocation_propagation": False,
        "ttl_enforcement": False,
        "historical_lockout": False,
        "snapshot_validation": False,
        "refresh_atomicity": False,
    }

    now = time.time()

    # ========================================================================
    # Vector 1: Cache Expiration Defense
    # ========================================================================

    @dataclass
    class CachedMRH:
        lct_id: str
        context_entities: Set[str]
        cached_at: float
        expires_at: float

    def check_cache_expiration(cache: CachedMRH,
                                 current_time: float) -> Tuple[bool, str]:
        """Check if cached MRH has expired."""
        if current_time > cache.expires_at:
            return False, f"expired: {(current_time - cache.expires_at):.0f}s ago"
        
        # Also check maximum age
        max_age = 300  # 5 minutes
        age = current_time - cache.cached_at
        if age > max_age:
            return False, f"too_old: {age:.0f}s > {max_age}s"
        
        return True, "ok"

    # Attack: Use expired cache
    expired_cache = CachedMRH(
        lct_id="attacker",
        context_entities={"target_1", "target_2", "target_3"},
        cached_at=now - 3600,  # 1 hour ago
        expires_at=now - 3000  # Expired 50 min ago
    )
    
    valid, reason = check_cache_expiration(expired_cache, now)
    
    if not valid:
        defenses["cache_expiration"] = True

    # ========================================================================
    # Vector 2: Revocation Propagation Defense
    # ========================================================================

    @dataclass
    class RevocationEvent:
        revoked_entity: str
        revoked_at: float
        propagation_targets: Set[str]
        propagation_complete: bool

    def check_revocation_propagation(event: RevocationEvent,
                                       current_context: Set[str],
                                       max_propagation_delay: float = 60.0) -> Tuple[bool, str]:
        """Check if revocation has propagated."""
        if not event.propagation_complete:
            # Check if delay is excessive
            delay = time.time() - event.revoked_at
            if delay > max_propagation_delay:
                return False, f"propagation_stalled: {delay:.0f}s"
        
        # Check if revoked entity still in context
        if event.revoked_entity in current_context:
            return False, "revoked_entity_still_in_context"
        
        return True, "ok"

    # Attack: Use context before revocation propagates
    slow_revocation = RevocationEvent(
        revoked_entity="compromised_entity",
        revoked_at=now - 120,  # 2 min ago
        propagation_targets={"victim_1", "victim_2"},
        propagation_complete=False
    )
    
    attack_context = {"compromised_entity", "other_entity"}  # Still has revoked!
    
    propagated, reason = check_revocation_propagation(slow_revocation, attack_context)
    
    if not propagated:
        defenses["revocation_propagation"] = True

    # ========================================================================
    # Vector 3: TTL Enforcement Defense
    # ========================================================================

    @dataclass
    class TTLConfig:
        default_ttl: float
        min_ttl: float
        max_ttl: float
        relationship_ttls: Dict[str, float]

    def enforce_ttl(requested_ttl: float, 
                     config: TTLConfig,
                     relationship_type: str = "default") -> Tuple[float, str]:
        """Enforce TTL bounds."""
        # Check relationship-specific TTL
        if relationship_type in config.relationship_ttls:
            max_allowed = config.relationship_ttls[relationship_type]
            if requested_ttl > max_allowed:
                return max_allowed, "relationship_specific_cap"
        
        # Check bounds
        if requested_ttl < config.min_ttl:
            return config.min_ttl, "below_minimum"
        
        if requested_ttl > config.max_ttl:
            return config.max_ttl, "above_maximum"
        
        return requested_ttl, "ok"

    ttl_config = TTLConfig(
        default_ttl=300,
        min_ttl=60,
        max_ttl=3600,
        relationship_ttls={"paired_with": 1800}
    )
    
    # Attack: Request absurdly long TTL
    enforced, reason = enforce_ttl(86400 * 365, ttl_config)  # 1 year!
    
    if enforced <= ttl_config.max_ttl:
        defenses["ttl_enforcement"] = True

    # ========================================================================
    # Vector 4: Historical Lockout Defense
    # ========================================================================

    @dataclass
    class ContextHistoryEntry:
        lct_id: str
        context_at_time: Set[str]
        valid_from: float
        valid_until: float

    def check_historical_lockout(entry: ContextHistoryEntry,
                                   query_time: float,
                                   lockout_after: float = 3600) -> Tuple[bool, str]:
        """Prevent use of historical context after lockout."""
        # Check if entry is historical
        if query_time > entry.valid_until:
            age = query_time - entry.valid_until
            if age > lockout_after:
                return False, f"historical_lockout: {age:.0f}s > {lockout_after}s"
        
        return True, "ok"

    # Attack: Use very old historical context
    ancient_history = ContextHistoryEntry(
        lct_id="attacker",
        context_at_time={"privileged_1", "privileged_2"},
        valid_from=now - 86400 * 30,  # 30 days ago
        valid_until=now - 86400 * 29
    )
    
    allowed, reason = check_historical_lockout(ancient_history, now)
    
    if not allowed:
        defenses["historical_lockout"] = True

    # ========================================================================
    # Vector 5: Snapshot Validation Defense
    # ========================================================================

    @dataclass
    class MRHSnapshot:
        snapshot_id: str
        lct_id: str
        context_hash: str
        taken_at: float
        signature: str

    def validate_snapshot(snapshot: MRHSnapshot,
                           expected_signer: str) -> Tuple[bool, List[str]]:
        """Validate MRH snapshot integrity."""
        issues = []
        
        # Check signature format
        if not snapshot.signature or len(snapshot.signature) < 16:
            issues.append("invalid_signature_format")
        
        # Verify signature (simplified)
        expected_sig = hashlib.sha256(
            f"{snapshot.snapshot_id}:{snapshot.context_hash}:{expected_signer}".encode()
        ).hexdigest()[:32]
        
        if snapshot.signature != expected_sig:
            issues.append("signature_mismatch")
        
        # Check freshness
        if time.time() - snapshot.taken_at > 300:
            issues.append("snapshot_stale")
        
        return len(issues) == 0, issues

    # Attack: Use snapshot with forged signature
    forged_snapshot = MRHSnapshot(
        snapshot_id="snap_1",
        lct_id="attacker",
        context_hash="arbitrary_hash",
        taken_at=now,
        signature="forged_signature_here"
    )
    
    valid, issues = validate_snapshot(forged_snapshot, "legitimate_signer")
    
    if not valid:
        defenses["snapshot_validation"] = True

    # ========================================================================
    # Vector 6: Refresh Atomicity Defense
    # ========================================================================

    @dataclass
    class RefreshOperation:
        operation_id: str
        old_context: Set[str]
        new_context: Set[str]
        started_at: float
        completed_at: Optional[float]
        status: str  # "in_progress", "completed", "failed"

    def check_refresh_atomicity(operation: RefreshOperation,
                                  max_duration: float = 5.0) -> Tuple[bool, str]:
        """Ensure refresh operations are atomic."""
        if operation.status == "in_progress":
            duration = time.time() - operation.started_at
            if duration > max_duration:
                return False, f"refresh_timeout: {duration:.2f}s"
        
        if operation.status == "completed":
            if operation.completed_at is None:
                return False, "completed_without_timestamp"
            
            duration = operation.completed_at - operation.started_at
            if duration > max_duration:
                return False, f"slow_completion: {duration:.2f}s"
        
        return True, "ok"

    # Attack: Start refresh then use old context during window
    stalled_refresh = RefreshOperation(
        operation_id="refresh_1",
        old_context={"privileged_access"},
        new_context=set(),  # Would remove access
        started_at=now - 30,  # Started 30s ago
        completed_at=None,
        status="in_progress"
    )
    
    atomic, reason = check_refresh_atomicity(stalled_refresh)
    
    if not atomic:
        defenses["refresh_atomicity"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Stale Context Exploitation (FL-3b)",
        success=attack_success,
        setup_cost_atp=20000.0,
        gain_atp=120000.0 if attack_success else 0.0,
        roi=(120000.0 / 20000.0) if attack_success else -1.0,
        detection_probability=0.80 if defenses_held >= 4 else 0.30,
        time_to_detection_hours=6.0,
        blocks_until_detected=60,
        trust_damage=0.75,
        description=f"""
STALE CONTEXT EXPLOITATION ATTACK (Track FL-3b)

Exploit outdated MRH context to access revoked resources.

Attack Pattern:
1. Use cache from 1 hour ago (expired 50 min ago)
2. Access entity during revocation propagation delay
3. Request 1-year TTL (max is 1 hour)
4. Reference 30-day-old historical context
5. Use snapshot with forged signature
6. Exploit 30s refresh window

Staleness Analysis:
- Cache expired: {not check_cache_expiration(expired_cache, now)[0]}
- Revocation stalled: {not check_revocation_propagation(slow_revocation, attack_context)[0]}
- TTL capped from {86400*365}s to {enforced}s
- Historical locked out: {not check_historical_lockout(ancient_history, now)[0]}
- Snapshot valid: {validate_snapshot(forged_snapshot, "legitimate_signer")[0]}
- Refresh atomic: {check_refresh_atomicity(stalled_refresh)[0]}

Defense Analysis:
- Cache expiration: {"HELD" if defenses["cache_expiration"] else "BYPASSED"}
- Revocation propagation: {"HELD" if defenses["revocation_propagation"] else "BYPASSED"}
- TTL enforcement: {"HELD" if defenses["ttl_enforcement"] else "BYPASSED"}
- Historical lockout: {"HELD" if defenses["historical_lockout"] else "BYPASSED"}
- Snapshot validation: {"HELD" if defenses["snapshot_validation"] else "BYPASSED"}
- Refresh atomicity: {"HELD" if defenses["refresh_atomicity"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FL-3b: Stale Context Exploitation Defense:
1. Enforce strict cache expiration
2. Propagate revocations immediately
3. Enforce maximum TTL bounds
4. Lock out historical context
5. Validate snapshot signatures
6. Make refresh operations atomic

Freshness is a security property.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "enforced_ttl": enforced,
        }
    )


# ============================================================================
# RUN ALL ATTACKS
# ============================================================================


def run_all_track_fl_attacks() -> List[AttackResult]:
    """Run all Track FL attacks and return results."""
    attacks = [
        attack_mrh_boundary_violation,
        attack_horizon_manipulation,
        attack_context_poisoning,
        attack_context_amplification,
        attack_cross_network_mrh_conflict,
        attack_stale_context_exploitation,
    ]

    results = []
    for attack_fn in attacks:
        try:
            result = attack_fn()
            results.append(result)
        except Exception as e:
            print(f"Error running {attack_fn.__name__}: {e}")
            import traceback
            traceback.print_exc()

    return results


def print_track_fl_summary(results: List[AttackResult]):
    """Print summary of Track FL attack results."""
    print("\n" + "=" * 70)
    print("TRACK FL: MRH CONTEXT BOUNDARY ATTACKS - SUMMARY")
    print("Attacks 323-328")
    print("=" * 70)

    total_attacks = len(results)
    successful = sum(1 for r in results if r.success)
    defended = total_attacks - successful

    print(f"\nTotal Attacks: {total_attacks}")
    print(f"Defended: {defended}")
    print(f"Attack Success Rate: {(successful/total_attacks)*100:.1f}%")

    avg_detection = sum(r.detection_probability for r in results) / total_attacks
    print(f"Average Detection Probability: {avg_detection*100:.1f}%")

    print("\n" + "-" * 70)
    print("INDIVIDUAL RESULTS:")
    print("-" * 70)

    for i, result in enumerate(results, 323):
        status = "DEFENDED" if not result.success else "SUCCEEDED"
        print(f"\nAttack #{i}: {result.attack_name}")
        print(f"  Status: {status}")
        print(f"  Detection: {result.detection_probability*100:.0f}%")
        print(f"  Setup Cost: {result.setup_cost_atp:,.0f} ATP")
        print(f"  Trust Damage: {result.trust_damage:.0%}")


if __name__ == "__main__":
    results = run_all_track_fl_attacks()
    print_track_fl_summary(results)
