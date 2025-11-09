"""
Web4 MRH (Markov Relevancy Horizon) Graph Implementation
=========================================================

Implements RDF-based knowledge graphs for Web4 entity relationships.

The MRH graph captures:
- Entity relationships (bound, paired, witnessed)
- Role-contextual trust (T3 tensors)
- Authorization decisions
- Law/society membership
- Delegation chains

Key Features:
- RDF triple storage
- SPARQL-like queries (simplified)
- Trust propagation through graph
- Automatic updates from events
- Role-contextual trust binding

Integration:
- LCT Registry → Identity triples
- Law Oracle → Authority/law triples
- Authorization → Decision triples
- Reputation → T3/V3 tensor triples
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple, Any
from enum import Enum
import time
import hashlib


class RelationType(Enum):
    """Web4 relationship types"""
    # Binding relationships (permanent)
    BOUND_TO = "web4:boundTo"
    PARENT_BINDING = "web4:parentBinding"
    CHILD_BINDING = "web4:childBinding"
    SIBLING_BINDING = "web4:siblingBinding"

    # Pairing relationships (session-based)
    PAIRED_WITH = "web4:pairedWith"
    ENERGY_PAIRING = "web4:energyPairing"
    DATA_PAIRING = "web4:dataPairing"
    SERVICE_PAIRING = "web4:servicePairing"

    # Witness relationships (trust-building)
    WITNESSED_BY = "web4:witnessedBy"
    TIME_WITNESS = "web4:timeWitness"
    AUDIT_WITNESS = "web4:auditWitness"
    ORACLE_WITNESS = "web4:oracleWitness"

    # Identity/Society relationships
    MEMBER_OF = "web4:memberOf"
    HAS_ROLE = "web4:hasRole"
    PAIRED_WITH_ROLE = "web4:pairedWithRole"

    # Authority/Law relationships
    HAS_AUTHORITY = "web4:hasAuthority"
    HAS_LAW_ORACLE = "web4:hasLawOracle"
    DELEGATES_TO = "web4:delegatesTo"

    # Trust/Reputation relationships
    HAS_T3_TENSOR = "web4:hasT3Tensor"
    HAS_V3_TENSOR = "web4:hasV3Tensor"
    AUTHORIZED_ACTION = "web4:authorizedAction"


@dataclass
class RDFTriple:
    """
    Basic RDF triple: subject-predicate-object

    Example:
      Triple(
        subject="lct:alice",
        predicate="web4:boundTo",
        object="lct:hardware1"
      )
    """
    subject: str
    predicate: str
    object: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.subject, self.predicate, self.object))

    def to_turtle(self) -> str:
        """Export as Turtle notation"""
        return f"<{self.subject}> <{self.predicate}> <{self.object}> ."

    def matches(self, subject: Optional[str] = None,
                predicate: Optional[str] = None,
                object_: Optional[str] = None) -> bool:
        """Check if triple matches pattern (None = wildcard)"""
        if subject and self.subject != subject:
            return False
        if predicate and self.predicate != predicate:
            return False
        if object_ and self.object != object_:
            return False
        return True


@dataclass
class MRHNode:
    """
    Entity node in MRH graph
    """
    lct_id: str
    entity_type: str  # HUMAN, AI, ORGANIZATION, etc.
    roles: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created: float = field(default_factory=time.time)


@dataclass
class MRHEdge:
    """
    Relationship edge in MRH graph

    Wraps RDF triple with additional MRH-specific metadata
    """
    triple: RDFTriple
    relation_type: RelationType
    weight: float = 1.0  # Edge weight for trust propagation
    distance: int = 1    # Hop distance from origin

    @property
    def source(self) -> str:
        return self.triple.subject

    @property
    def target(self) -> str:
        return self.triple.object


@dataclass
class T3Tensor:
    """
    Role-contextual Trust tensor

    CRITICAL: T3 is always bound to (entity, role) pair!
    """
    entity_lct: str
    role_lct: str
    talent: float = 0.5      # Natural capability
    training: float = 0.5    # Acquired skill
    temperament: float = 0.5 # Reliability/consistency

    def average(self) -> float:
        """Simple average trust score"""
        return (self.talent + self.training + self.temperament) / 3.0

    def weighted(self, talent_w=0.4, training_w=0.3, temperament_w=0.3) -> float:
        """Weighted trust score"""
        return (self.talent * talent_w +
                self.training * training_w +
                self.temperament * temperament_w)


class MRHGraph:
    """
    MRH Graph Manager

    Maintains RDF knowledge graph of Web4 entity relationships.
    Provides triple storage, query, and trust propagation.
    """

    def __init__(self):
        self.triples: Set[RDFTriple] = set()
        self.nodes: Dict[str, MRHNode] = {}
        self.edges_by_source: Dict[str, List[MRHEdge]] = {}
        self.edges_by_target: Dict[str, List[MRHEdge]] = {}

        # T3/V3 tensors (role-contextual)
        self.t3_tensors: Dict[Tuple[str, str], T3Tensor] = {}  # (entity, role) → T3

        # Index for fast queries
        self.predicate_index: Dict[str, Set[RDFTriple]] = {}
        self.subject_index: Dict[str, Set[RDFTriple]] = {}
        self.object_index: Dict[str, Set[RDFTriple]] = {}

    def add_node(self, lct_id: str, entity_type: str, metadata: Dict = None) -> MRHNode:
        """Add entity node to graph"""
        if lct_id in self.nodes:
            return self.nodes[lct_id]

        node = MRHNode(
            lct_id=lct_id,
            entity_type=entity_type,
            metadata=metadata or {}
        )
        self.nodes[lct_id] = node
        return node

    def add_triple(self, subject: str, predicate: str, object_: str,
                   metadata: Dict = None) -> RDFTriple:
        """Add RDF triple to graph"""
        triple = RDFTriple(
            subject=subject,
            predicate=predicate,
            object=object_,
            metadata=metadata or {}
        )

        if triple in self.triples:
            return triple

        self.triples.add(triple)

        # Update indices
        if predicate not in self.predicate_index:
            self.predicate_index[predicate] = set()
        self.predicate_index[predicate].add(triple)

        if subject not in self.subject_index:
            self.subject_index[subject] = set()
        self.subject_index[subject].add(triple)

        if object_ not in self.object_index:
            self.object_index[object_] = set()
        self.object_index[object_].add(triple)

        return triple

    def add_edge(self, source: str, target: str, relation: RelationType,
                 weight: float = 1.0, metadata: Dict = None) -> MRHEdge:
        """Add relationship edge to graph"""
        triple = self.add_triple(source, relation.value, target, metadata)

        edge = MRHEdge(
            triple=triple,
            relation_type=relation,
            weight=weight
        )

        # Update edge indices
        if source not in self.edges_by_source:
            self.edges_by_source[source] = []
        self.edges_by_source[source].append(edge)

        if target not in self.edges_by_target:
            self.edges_by_target[target] = []
        self.edges_by_target[target].append(edge)

        return edge

    def query_triples(self, subject: Optional[str] = None,
                     predicate: Optional[str] = None,
                     object_: Optional[str] = None) -> List[RDFTriple]:
        """
        Query triples matching pattern.

        None = wildcard.

        Examples:
          query(subject="lct:alice")  # All triples about alice
          query(predicate="web4:boundTo")  # All binding relationships
          query(subject="lct:alice", predicate="web4:hasRole")  # Alice's roles
        """
        # Use indices for efficiency
        if subject:
            candidates = self.subject_index.get(subject, set())
        elif predicate:
            candidates = self.predicate_index.get(predicate, set())
        elif object_:
            candidates = self.object_index.get(object_, set())
        else:
            candidates = self.triples

        return [t for t in candidates if t.matches(subject, predicate, object_)]

    def get_outgoing_edges(self, lct_id: str,
                          relation: Optional[RelationType] = None) -> List[MRHEdge]:
        """Get edges emanating from entity"""
        edges = self.edges_by_source.get(lct_id, [])
        if relation:
            edges = [e for e in edges if e.relation_type == relation]
        return edges

    def get_incoming_edges(self, lct_id: str,
                          relation: Optional[RelationType] = None) -> List[MRHEdge]:
        """Get edges pointing to entity"""
        edges = self.edges_by_target.get(lct_id, [])
        if relation:
            edges = [e for e in edges if e.relation_type == relation]
        return edges

    def get_neighbors(self, lct_id: str,
                     relation: Optional[RelationType] = None,
                     direction: str = "outgoing") -> List[str]:
        """Get neighboring entities"""
        if direction == "outgoing":
            edges = self.get_outgoing_edges(lct_id, relation)
            return [e.target for e in edges]
        elif direction == "incoming":
            edges = self.get_incoming_edges(lct_id, relation)
            return [e.source for e in edges]
        else:  # both
            out = self.get_neighbors(lct_id, relation, "outgoing")
            inc = self.get_neighbors(lct_id, relation, "incoming")
            return list(set(out + inc))

    def traverse(self, start: str, max_depth: int = 3,
                relation: Optional[RelationType] = None) -> Dict[int, Set[str]]:
        """
        Traverse graph from starting entity up to max_depth hops.

        Returns: {depth: {entities at that depth}}

        This implements the "Markov Relevancy Horizon" - entities
        beyond max_depth are outside the horizon and irrelevant.
        """
        result = {0: {start}}
        visited = {start}
        frontier = {start}

        for depth in range(1, max_depth + 1):
            next_frontier = set()

            for entity in frontier:
                neighbors = self.get_neighbors(entity, relation, "both")
                for neighbor in neighbors:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_frontier.add(neighbor)

            if not next_frontier:
                break

            result[depth] = next_frontier
            frontier = next_frontier

        return result

    def find_paths(self, start: str, end: str, max_depth: int = 3) -> List[List[str]]:
        """
        Find all paths from start to end within max_depth hops.

        Used for trust propagation calculations.
        """
        if start == end:
            return [[start]]

        paths = []

        def dfs(current: str, target: str, path: List[str], depth: int):
            if depth > max_depth:
                return

            if current == target:
                paths.append(path.copy())
                return

            for neighbor in self.get_neighbors(current):
                if neighbor not in path:  # Avoid cycles
                    path.append(neighbor)
                    dfs(neighbor, target, path, depth + 1)
                    path.pop()

        dfs(start, end, [start], 0)
        return paths

    def set_t3_tensor(self, entity_lct: str, role_lct: str, t3: T3Tensor):
        """
        Set T3 trust tensor for (entity, role) pair.

        CRITICAL: Trust is role-contextual!
        """
        key = (entity_lct, role_lct)
        self.t3_tensors[key] = t3

        # Also add as RDF triple
        tensor_id = f"tensor:t3:{entity_lct}:{role_lct}"
        self.add_triple(entity_lct, RelationType.HAS_T3_TENSOR.value, tensor_id)
        self.add_triple(tensor_id, "web4:role", role_lct)
        self.add_triple(tensor_id, "web4:talent", str(t3.talent))
        self.add_triple(tensor_id, "web4:training", str(t3.training))
        self.add_triple(tensor_id, "web4:temperament", str(t3.temperament))

    def get_t3_tensor(self, entity_lct: str, role_lct: str) -> Optional[T3Tensor]:
        """Get T3 trust tensor for (entity, role) pair"""
        key = (entity_lct, role_lct)
        return self.t3_tensors.get(key)

    def propagate_trust(self, start: str, end: str, role_lct: str,
                       decay_rate: float = 0.9) -> float:
        """
        Calculate trust from start to end entity in role context.

        Trust propagates through graph paths with decay.
        """
        paths = self.find_paths(start, end, max_depth=3)

        if not paths:
            return 0.0

        # Calculate trust for each path
        path_trusts = []

        for path in paths:
            trust = 1.0

            for i in range(len(path) - 1):
                # Get T3 for entity in role
                entity = path[i]
                t3 = self.get_t3_tensor(entity, role_lct)

                if t3:
                    # Multiply by entity trust and decay
                    trust *= t3.average() * (decay_rate ** i)
                else:
                    # No trust tensor = default low trust
                    trust *= 0.5 * (decay_rate ** i)

            path_trusts.append(trust)

        # Combine multiple paths (take max for now, could do probabilistic)
        return max(path_trusts) if path_trusts else 0.0

    def export_turtle(self) -> str:
        """Export graph as Turtle RDF"""
        lines = [
            "@prefix web4: <https://web4.io/ontology#> .",
            "@prefix lct: <https://web4.io/lct/> .",
            "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
            ""
        ]

        for triple in sorted(self.triples, key=lambda t: (t.subject, t.predicate)):
            lines.append(triple.to_turtle())

        return "\n".join(lines)

    def get_stats(self) -> Dict:
        """Get graph statistics"""
        return {
            "nodes": len(self.nodes),
            "triples": len(self.triples),
            "edges": sum(len(e) for e in self.edges_by_source.values()),
            "t3_tensors": len(self.t3_tensors),
            "predicates": len(self.predicate_index),
            "avg_outgoing_degree": (
                sum(len(e) for e in self.edges_by_source.values()) / len(self.nodes)
                if self.nodes else 0
            )
        }


class MRHEventIntegration:
    """
    Automatically updates MRH graph from Web4 events.

    Integration points:
    - LCT minting → Identity triples
    - Delegation creation → Authority triples
    - Authorization decision → Action triples
    - Reputation update → T3/V3 tensor triples
    """

    def __init__(self, graph: MRHGraph):
        self.graph = graph

    def on_lct_minted(self, lct_id: str, entity_type: str, society_id: str,
                     witnesses: List[str], birth_cert_hash: str):
        """Update graph when new LCT minted"""
        # Add entity node
        self.graph.add_node(lct_id, entity_type)

        # Add society membership
        self.graph.add_edge(lct_id, society_id, RelationType.MEMBER_OF)

        # Add witness relationships
        for witness in witnesses:
            self.graph.add_edge(lct_id, witness, RelationType.WITNESSED_BY,
                              metadata={"event": "birth", "cert_hash": birth_cert_hash})

        # Add birth certificate triple
        self.graph.add_triple(lct_id, "web4:birthCertificate", birth_cert_hash)

    def on_delegation_created(self, delegation_id: str, client_lct: str,
                             agent_lct: str, role_lct: str):
        """Update graph when delegation created"""
        # Add delegation edge
        self.graph.add_edge(client_lct, agent_lct, RelationType.DELEGATES_TO,
                          metadata={"delegation_id": delegation_id, "role": role_lct})

        # Add role pairing
        self.graph.add_edge(agent_lct, role_lct, RelationType.HAS_ROLE)
        self.graph.add_triple(agent_lct, RelationType.PAIRED_WITH_ROLE.value, role_lct,
                            metadata={"delegation_id": delegation_id})

        # Add agent to node roles
        if agent_lct in self.graph.nodes:
            self.graph.nodes[agent_lct].roles.add(role_lct)

    def on_authorization_granted(self, decision_id: str, agent_lct: str,
                                action: str, resource: str, atp_cost: int,
                                law_hash: str):
        """Update graph when authorization granted"""
        # Add authorization action triple
        action_id = f"action:{decision_id}"
        self.graph.add_triple(agent_lct, RelationType.AUTHORIZED_ACTION.value, action_id)
        self.graph.add_triple(action_id, "web4:actionType", action)
        self.graph.add_triple(action_id, "web4:resource", resource)
        self.graph.add_triple(action_id, "web4:atpCost", str(atp_cost))
        self.graph.add_triple(action_id, "web4:lawHash", law_hash)

    def on_reputation_update(self, entity_lct: str, role_lct: str, t3: T3Tensor):
        """Update graph when reputation changes"""
        self.graph.set_t3_tensor(entity_lct, role_lct, t3)


# Example usage and testing
if __name__ == "__main__":
    print("=" * 70)
    print("  Web4 MRH Graph - Implementation Test")
    print("=" * 70)

    # Create graph
    graph = MRHGraph()
    event_integration = MRHEventIntegration(graph)

    print("\n✅ MRH Graph created")

    # Simulate LCT minting events
    print("\n👤 Simulating Entity Creation:")

    event_integration.on_lct_minted(
        lct_id="lct:alice",
        entity_type="HUMAN",
        society_id="society:research_lab",
        witnesses=["witness:hr", "witness:security"],
        birth_cert_hash="abc123"
    )
    print("   ✅ Alice LCT minted")

    event_integration.on_lct_minted(
        lct_id="lct:ai_agent",
        entity_type="AI",
        society_id="society:research_lab",
        witnesses=["witness:supervisor"],
        birth_cert_hash="def456"
    )
    print("   ✅ AI Agent LCT minted")

    # Create delegation
    print("\n📋 Simulating Delegation:")

    event_integration.on_delegation_created(
        delegation_id="deleg:001",
        client_lct="lct:alice",
        agent_lct="lct:ai_agent",
        role_lct="role:researcher"
    )
    print("   ✅ Delegation created: alice → ai_agent (researcher)")

    # Set T3 tensors
    print("\n📊 Setting Trust Tensors:")

    event_integration.on_reputation_update(
        entity_lct="lct:ai_agent",
        role_lct="role:researcher",
        t3=T3Tensor(
            entity_lct="lct:ai_agent",
            role_lct="role:researcher",
            talent=0.8,
            training=0.7,
            temperament=0.9
        )
    )
    print("   ✅ T3 tensor set for ai_agent as researcher")

    # Query graph
    print("\n🔍 Querying Graph:")

    # Find Alice's relationships
    alice_triples = graph.query_triples(subject="lct:alice")
    print(f"\n   Alice has {len(alice_triples)} relationships:")
    for triple in alice_triples[:5]:  # Show first 5
        print(f"     {triple.predicate} → {triple.object}")

    # Find society members
    members = graph.query_triples(predicate="web4:memberOf",
                                  object_="society:research_lab")
    print(f"\n   Research lab has {len(members)} members:")
    for triple in members:
        print(f"     {triple.subject}")

    # Find delegations
    delegations = graph.query_triples(predicate="web4:delegatesTo")
    print(f"\n   {len(delegations)} delegations:")
    for triple in delegations:
        print(f"     {triple.subject} → {triple.object}")

    # Traverse from Alice
    print("\n🌐 Traversing from Alice (max depth 3):")

    horizon = graph.traverse("lct:alice", max_depth=3)
    for depth, entities in horizon.items():
        print(f"   Depth {depth}: {entities}")

    # Find paths
    print("\n🛤️  Paths from alice to ai_agent:")

    paths = graph.find_paths("lct:alice", "lct:ai_agent", max_depth=3)
    for i, path in enumerate(paths):
        print(f"   Path {i+1}: {' → '.join(path)}")

    # Trust propagation
    print("\n🔐 Trust Propagation:")

    trust = graph.propagate_trust("lct:alice", "lct:ai_agent", "role:researcher")
    print(f"   Trust from alice to ai_agent (researcher): {trust:.3f}")

    # Export Turtle
    print("\n📄 Turtle RDF Export (first 10 lines):")
    turtle = graph.export_turtle()
    for line in turtle.split("\n")[:10]:
        print(f"   {line}")

    # Statistics
    print("\n📊 Graph Statistics:")
    stats = graph.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print("\n✅ MRH Graph implementation complete and tested!")
    print("✅ Ready for integration with LCT/Law/Auth systems")
