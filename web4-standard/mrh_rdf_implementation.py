#!/usr/bin/env python3
"""
MRH RDF Implementation - Practical example of Markov Relevancy Horizon as RDF graphs
"""

import json
import hashlib
import time
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import rdflib
from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import RDF, XSD
import networkx as nx
import matplotlib.pyplot as plt

# Define namespaces
MRH = Namespace("https://web4.foundation/mrh/v1#")
LCT_NS = Namespace("https://web4.foundation/lct/")  # Renamed to avoid collision with LCT class
WEB4 = Namespace("https://web4.foundation/web4/v1#")
GROUND = Namespace("https://web4.foundation/mrh/grounding#")  # Grounding-specific namespace

class MRHRelation(Enum):
    """Standard MRH relationship types"""
    # Semantic relationships (original)
    DERIVES_FROM = "derives_from"
    SPECIALIZES = "specializes"
    CONTRADICTS = "contradicts"
    EXTENDS = "extends"
    REFERENCES = "references"
    DEPENDS_ON = "depends_on"
    ALTERNATIVES_TO = "alternatives_to"
    PRODUCES = "produces"
    CONSUMES = "consumes"
    TRANSFORMS = "transforms"

    # Entity relationship mechanisms (December 2025)
    BINDING = "binding"           # Permanent identity attachment (hardware -> LCT)
    PAIRING = "pairing"           # Operational authorization (symmetric keys)
    WITNESSING = "witnessing"     # Trust building through observation
    BROADCAST = "broadcast"       # Public announcement for discovery
    GROUNDING = "grounding"       # Ephemeral operational presence

@dataclass
class MRHEdge:
    """Represents an edge in the MRH graph"""
    target_lct: str
    probability: float
    relation: MRHRelation
    distance: int = 1
    decay_rate: float = 0.9
    conditional_on: Optional[List[str]] = None
    metadata: Dict = field(default_factory=dict)

    def effective_probability(self, current_distance: int = 0) -> float:
        """Calculate effective probability with decay"""
        return self.probability * (self.decay_rate ** (current_distance + self.distance - 1))

@dataclass
class LocationContext:
    """Spatial grounding context"""
    type: str  # "physical" | "network" | "logical"
    value: str  # GPS coordinates, IP range, society ID, etc.
    precision: str  # "exact" | "city" | "region" | "country"
    verifiable: bool = False  # Can this be independently verified?

@dataclass
class ResourceState:
    """Resource availability state"""
    compute: float  # 0.0 to 1.0 (available capacity ratio)
    memory: float   # 0.0 to 1.0
    network: float  # 0.0 to 1.0
    sensors: List[str] = field(default_factory=list)  # Available sensor types

@dataclass
class CapabilitiesContext:
    """Capability grounding context"""
    advertised: List[str]  # Capability IDs entity claims it can do now
    hardware_class: str    # "edge-device" | "server" | "mobile" | "browser"
    resource_state: ResourceState = field(default_factory=lambda: ResourceState(1.0, 1.0, 1.0))

@dataclass
class SessionContext:
    """Temporal grounding context"""
    started: str  # ISO8601 timestamp
    activity_pattern: str  # Hash of recent activity timing
    continuity_token: str  # Links to previous grounding (hash of last grounding)

@dataclass
class GroundingContext:
    """
    Grounding context - ephemeral operational presence

    Captures where an entity currently IS and what it CAN do right now.
    This is the fifth MRH relationship type, complementing:
    - LCT (identity), T3/V3 (trust), ATP (resources), AGY/ACP (authorization)
    """
    location: LocationContext
    capabilities: CapabilitiesContext
    session: SessionContext
    active_contexts: List[str] = field(default_factory=list)  # LCTs currently engaged with

@dataclass
class GroundingEdge:
    """
    Grounding edge - ephemeral presence announcement

    Unlike semantic MRH edges (probability-weighted), grounding edges are:
    - Short-lived (minutes to hours TTL)
    - Frequently updated (heartbeat-driven)
    - Self-attested (signed by source LCT)
    - Optionally witnessed
    """
    source: str  # LCT doing the grounding
    target: GroundingContext  # Current operational context
    timestamp: str  # ISO8601 when this grounding was announced
    ttl: timedelta  # How long this grounding remains valid
    signature: str  # Signed by source LCT
    witness_set: List[str] = field(default_factory=list)  # Optional witnesses to this grounding

    def is_expired(self) -> bool:
        """Check if grounding has expired"""
        announced = datetime.fromisoformat(self.timestamp)
        expiry = announced + self.ttl
        return datetime.now() > expiry

    def time_remaining(self) -> timedelta:
        """Calculate time remaining before expiration"""
        announced = datetime.fromisoformat(self.timestamp)
        expiry = announced + self.ttl
        remaining = expiry - datetime.now()
        return max(remaining, timedelta(0))

class MRHGraph:
    """Markov Relevancy Horizon graph implementation"""

    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        self.graph = Graph()
        self.edges: List[MRHEdge] = []
        self.grounding_edges: List[GroundingEdge] = []  # Separate storage for grounding
        self._setup_namespaces()

    def _setup_namespaces(self):
        """Initialize RDF namespaces"""
        self.graph.bind("mrh", MRH)
        self.graph.bind("lct", LCT_NS)
        self.graph.bind("web4", WEB4)
        self.graph.bind("ground", GROUND)
        self.graph.bind("xsd", XSD)
        
    def add_relevance(self, edge: MRHEdge) -> BNode:
        """Add a relevance relationship to the graph"""
        relevance_node = BNode()
        
        # Add type
        self.graph.add((relevance_node, RDF.type, MRH.Relevance))
        
        # Add target
        target_uri = LCT_NS[edge.target_lct]
        self.graph.add((relevance_node, MRH.target, target_uri))
        
        # Add probability
        self.graph.add((relevance_node, MRH.probability, 
                       Literal(edge.probability, datatype=XSD.decimal)))
        
        # Add relation
        rel_uri = MRH[edge.relation.value]
        self.graph.add((relevance_node, MRH.relation, rel_uri))
        
        # Add distance
        self.graph.add((relevance_node, MRH.distance, 
                       Literal(edge.distance, datatype=XSD.integer)))
        
        # Add decay rate
        self.graph.add((relevance_node, MRH.decay_rate,
                       Literal(edge.decay_rate, datatype=XSD.decimal)))
        
        # Add conditional dependencies
        if edge.conditional_on:
            for condition in edge.conditional_on:
                self.graph.add((relevance_node, MRH.conditional_on, LCT_NS[condition]))
        
        # Store edge for traversal
        self.edges.append(edge)

        return relevance_node

    def add_grounding_edge(self, edge: GroundingEdge) -> BNode:
        """
        Add a grounding edge to the graph

        Grounding edges capture ephemeral operational presence:
        - Where the entity currently IS (location)
        - What it CAN do right now (capabilities)
        - When it started and how it connects to previous presence (session)
        - Who it's interacting with (active_contexts)
        """
        grounding_node = BNode()

        # Add type
        self.graph.add((grounding_node, RDF.type, GROUND.GroundingEdge))

        # Add source LCT
        source_uri = LCT_NS[edge.source]
        self.graph.add((grounding_node, GROUND.source, source_uri))

        # Add timestamp
        self.graph.add((grounding_node, GROUND.timestamp,
                       Literal(edge.timestamp, datatype=XSD.dateTime)))

        # Add TTL
        ttl_seconds = int(edge.ttl.total_seconds())
        self.graph.add((grounding_node, GROUND.ttl,
                       Literal(ttl_seconds, datatype=XSD.integer)))

        # Add signature
        self.graph.add((grounding_node, GROUND.signature,
                       Literal(edge.signature, datatype=XSD.string)))

        # Add witness set
        for witness in edge.witness_set:
            witness_uri = LCT_NS[witness]
            self.graph.add((grounding_node, GROUND.witness, witness_uri))

        # Add location context
        location_node = BNode()
        self.graph.add((grounding_node, GROUND.location, location_node))
        self.graph.add((location_node, GROUND.type,
                       Literal(edge.target.location.type, datatype=XSD.string)))
        self.graph.add((location_node, GROUND.value,
                       Literal(edge.target.location.value, datatype=XSD.string)))
        self.graph.add((location_node, GROUND.precision,
                       Literal(edge.target.location.precision, datatype=XSD.string)))
        self.graph.add((location_node, GROUND.verifiable,
                       Literal(edge.target.location.verifiable, datatype=XSD.boolean)))

        # Add capabilities context
        capabilities_node = BNode()
        self.graph.add((grounding_node, GROUND.capabilities, capabilities_node))
        self.graph.add((capabilities_node, GROUND.hardwareClass,
                       Literal(edge.target.capabilities.hardware_class, datatype=XSD.string)))

        # Add advertised capabilities
        for capability in edge.target.capabilities.advertised:
            self.graph.add((capabilities_node, GROUND.advertised,
                           Literal(capability, datatype=XSD.string)))

        # Add resource state
        resource_node = BNode()
        self.graph.add((capabilities_node, GROUND.resourceState, resource_node))
        self.graph.add((resource_node, GROUND.compute,
                       Literal(edge.target.capabilities.resource_state.compute, datatype=XSD.decimal)))
        self.graph.add((resource_node, GROUND.memory,
                       Literal(edge.target.capabilities.resource_state.memory, datatype=XSD.decimal)))
        self.graph.add((resource_node, GROUND.network,
                       Literal(edge.target.capabilities.resource_state.network, datatype=XSD.decimal)))

        for sensor in edge.target.capabilities.resource_state.sensors:
            self.graph.add((resource_node, GROUND.sensor,
                           Literal(sensor, datatype=XSD.string)))

        # Add session context
        session_node = BNode()
        self.graph.add((grounding_node, GROUND.session, session_node))
        self.graph.add((session_node, GROUND.started,
                       Literal(edge.target.session.started, datatype=XSD.dateTime)))
        self.graph.add((session_node, GROUND.activityPattern,
                       Literal(edge.target.session.activity_pattern, datatype=XSD.string)))
        self.graph.add((session_node, GROUND.continuityToken,
                       Literal(edge.target.session.continuity_token, datatype=XSD.string)))

        # Add active contexts
        for context_lct in edge.target.active_contexts:
            context_uri = LCT_NS[context_lct]
            self.graph.add((grounding_node, GROUND.activeContext, context_uri))

        # Store edge for traversal
        self.grounding_edges.append(edge)

        return grounding_node

    def get_current_grounding(self) -> Optional[GroundingEdge]:
        """Get the most recent non-expired grounding edge for this entity"""
        valid_groundings = [g for g in self.grounding_edges if not g.is_expired()]
        if not valid_groundings:
            return None
        # Return most recent
        return sorted(valid_groundings, key=lambda g: g.timestamp, reverse=True)[0]

    def get_grounding_history(self, window_hours: int = 24) -> List[GroundingEdge]:
        """Get grounding history within a time window"""
        cutoff = datetime.now() - timedelta(hours=window_hours)
        return [g for g in self.grounding_edges
                if datetime.fromisoformat(g.timestamp) > cutoff]

    def to_jsonld(self) -> Dict:
        """Convert to JSON-LD format for LCT embedding"""
        # Serialize to JSON-LD
        jsonld_str = self.graph.serialize(format='json-ld')
        jsonld_data = json.loads(jsonld_str)

        # Add context
        context = {
            "@vocab": "https://web4.foundation/mrh/v1#",
            "mrh": "https://web4.foundation/mrh/v1#",
            "lct": "https://web4.foundation/lct/",
            "ground": "https://web4.foundation/mrh/grounding#",
            "xsd": "http://www.w3.org/2001/XMLSchema#"
        }

        # Handle both dict and list responses from rdflib
        if isinstance(jsonld_data, dict):
            graph_data = jsonld_data.get("@graph", [])
        else:
            graph_data = jsonld_data

        return {
            "@context": context,
            "@graph": graph_data
        }
    
    def traverse_markov(self, max_depth: int = 3, 
                       min_probability: float = 0.1) -> List[Tuple[str, float, List[str]]]:
        """
        Traverse the MRH graph using Markovian walk
        Returns: List of (lct_id, cumulative_probability, path)
        """
        results = []
        visited = set()
        
        def _traverse(current_edges: List[MRHEdge], 
                     depth: int, 
                     cum_prob: float,
                     path: List[str]):
            
            if depth >= max_depth:
                return
            
            for edge in current_edges:
                # Calculate new probability
                new_prob = cum_prob * edge.effective_probability(depth)
                
                # Skip if below threshold
                if new_prob < min_probability:
                    continue
                
                # Skip if already visited with higher probability
                if edge.target_lct in visited:
                    continue
                
                visited.add(edge.target_lct)
                new_path = path + [edge.target_lct]
                results.append((edge.target_lct, new_prob, new_path))
                
                # Recursively traverse if we can fetch the target LCT
                target_mrh = self._fetch_lct_mrh(edge.target_lct)
                if target_mrh:
                    _traverse(target_mrh.edges, depth + 1, new_prob, new_path)
        
        # Start traversal from root edges
        _traverse(self.edges, 0, 1.0, [])
        
        # Sort by probability
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def _fetch_lct_mrh(self, lct_id: str) -> Optional['MRHGraph']:
        """Fetch MRH graph from another LCT (simulated)"""
        # In real implementation, this would fetch from network
        # For demo, we'll return None or generate synthetic data
        return None
    
    def find_paths(self, target_lct: str, max_paths: int = 5) -> List[List[MRHEdge]]:
        """Find multiple paths to a target LCT"""
        paths = []
        
        def _dfs(current_edges: List[MRHEdge], 
                target: str, 
                current_path: List[MRHEdge],
                visited: Set[str]):
            
            if len(paths) >= max_paths:
                return
            
            for edge in current_edges:
                if edge.target_lct == target:
                    paths.append(current_path + [edge])
                elif edge.target_lct not in visited:
                    visited.add(edge.target_lct)
                    # Would recursively search in real implementation
                    _dfs([], target, current_path + [edge], visited)
                    visited.remove(edge.target_lct)
        
        _dfs(self.edges, target_lct, [], set())
        return paths
    
    def merge_graphs(self, other: 'MRHGraph', 
                    merge_probability: float = 0.8) -> 'MRHGraph':
        """Merge another MRH graph with probability weighting"""
        merged = MRHGraph(f"{self.entity_id}_merged")
        
        # Add edges from self
        for edge in self.edges:
            merged.add_relevance(edge)
        
        # Add edges from other with probability adjustment
        for edge in other.edges:
            adjusted_edge = MRHEdge(
                target_lct=edge.target_lct,
                probability=edge.probability * merge_probability,
                relation=edge.relation,
                distance=edge.distance + 1,
                decay_rate=edge.decay_rate,
                conditional_on=edge.conditional_on,
                metadata={**edge.metadata, "merged_from": other.entity_id}
            )
            merged.add_relevance(adjusted_edge)
        
        return merged

class LCT:
    """Linked Context Token with RDF-based MRH"""
    
    def __init__(self, entity_id: str, content: Dict):
        self.entity_id = entity_id
        self.content = content
        self.mrh = MRHGraph(entity_id)
        self.timestamp = time.time()
        self.hash = self._compute_hash()
        
    def _compute_hash(self) -> str:
        """Compute LCT hash"""
        content_str = json.dumps(self.content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]
    
    def add_relevance(self, target_lct: 'LCT', 
                     probability: float,
                     relation: MRHRelation,
                     **kwargs) -> None:
        """Add a relevance relationship to another LCT"""
        edge = MRHEdge(
            target_lct=target_lct.hash,
            probability=probability,
            relation=relation,
            **kwargs
        )
        self.mrh.add_relevance(edge)
    
    def to_json(self) -> Dict:
        """Serialize LCT with RDF MRH"""
        return {
            "lct_version": "1.1",
            "entity_id": self.entity_id,
            "hash": self.hash,
            "timestamp": self.timestamp,
            "content": self.content,
            "mrh": self.mrh.to_jsonld()
        }
    
    def find_relevant_contexts(self, min_probability: float = 0.3) -> List[Tuple[str, float]]:
        """Find all relevant contexts above probability threshold"""
        traversal = self.mrh.traverse_markov(min_probability=min_probability)
        return [(lct_id, prob) for lct_id, prob, _ in traversal]

class FractalNavigator:
    """Navigate the fractal graph of graphs"""
    
    def __init__(self):
        self.lct_cache: Dict[str, LCT] = {}
        self.traversal_history: List[str] = []
        
    def register_lct(self, lct: LCT) -> None:
        """Register an LCT in the cache"""
        self.lct_cache[lct.hash] = lct
        
    def traverse_fractal(self, start_lct: LCT, 
                         depth: int = 3,
                         breadth: int = 5) -> nx.DiGraph:
        """
        Traverse the fractal MRH structure, building a NetworkX graph
        """
        G = nx.DiGraph()
        visited = set()
        
        def _traverse(lct: LCT, current_depth: int, parent_prob: float = 1.0):
            if current_depth >= depth or lct.hash in visited:
                return
            
            visited.add(lct.hash)
            self.traversal_history.append(lct.hash)
            
            # Add node
            G.add_node(lct.hash, 
                      entity_id=lct.entity_id,
                      depth=current_depth,
                      probability=parent_prob)
            
            # Get top relevances
            relevances = lct.mrh.traverse_markov(max_depth=1, min_probability=0.1)
            
            for i, (target_hash, prob, _) in enumerate(relevances[:breadth]):
                # Add edge
                G.add_edge(lct.hash, target_hash, 
                          weight=prob,
                          relation="relevance")
                
                # Recursively traverse if LCT is in cache
                if target_hash in self.lct_cache:
                    target_lct = self.lct_cache[target_hash]
                    _traverse(target_lct, current_depth + 1, parent_prob * prob)
        
        _traverse(start_lct, 0)
        return G
    
    def visualize_traversal(self, G: nx.DiGraph, filename: str = "mrh_fractal.png"):
        """Visualize the fractal MRH structure"""
        plt.figure(figsize=(12, 8))
        
        # Layout
        pos = nx.spring_layout(G, k=2, iterations=50)
        
        # Color by depth
        depths = [G.nodes[node].get('depth', 0) for node in G.nodes()]
        
        # Draw
        nx.draw_networkx_nodes(G, pos, 
                             node_color=depths,
                             cmap='viridis',
                             node_size=500,
                             alpha=0.8)
        
        nx.draw_networkx_labels(G, pos,
                               labels={n: n[:8] for n in G.nodes()},
                               font_size=8)
        
        # Draw edges with probability as width
        edges = G.edges()
        weights = [G[u][v]['weight'] for u, v in edges]
        nx.draw_networkx_edges(G, pos,
                              width=[w * 3 for w in weights],
                              alpha=0.5,
                              edge_color='gray')
        
        plt.title("Fractal MRH Graph Traversal")
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        plt.close()
        
        print(f"Visualization saved to {filename}")

def demo_mrh_rdf():
    """Demonstrate MRH RDF implementation"""
    
    print("=" * 60)
    print("MRH RDF Implementation Demo")
    print("=" * 60)
    
    # Create LCTs representing a reasoning chain
    premise1 = LCT("entity:premise1", {
        "type": "observation",
        "content": "Temperature is rising"
    })
    
    premise2 = LCT("entity:premise2", {
        "type": "observation", 
        "content": "Ice is melting"
    })
    
    hypothesis = LCT("entity:hypothesis", {
        "type": "inference",
        "content": "Climate change is accelerating"
    })
    
    conclusion = LCT("entity:conclusion", {
        "type": "conclusion",
        "content": "Immediate action required"
    })
    
    alternative = LCT("entity:alternative", {
        "type": "alternative",
        "content": "Natural cycle variation"
    })
    
    # Build MRH relationships
    premise1.add_relevance(
        premise2, 
        probability=0.85,
        relation=MRHRelation.REFERENCES,
        distance=1
    )
    
    premise2.add_relevance(
        hypothesis,
        probability=0.75,
        relation=MRHRelation.PRODUCES,
        distance=1
    )
    
    hypothesis.add_relevance(
        conclusion,
        probability=0.9,
        relation=MRHRelation.PRODUCES,
        distance=1
    )
    
    hypothesis.add_relevance(
        alternative,
        probability=0.1,
        relation=MRHRelation.ALTERNATIVES_TO,
        distance=1
    )
    
    # Add circular reference for fractal structure
    conclusion.add_relevance(
        premise1,
        probability=0.3,
        relation=MRHRelation.DEPENDS_ON,
        distance=3
    )
    
    # Print JSON-LD representation
    print("\n1. LCT with RDF MRH (JSON-LD format):")
    print("-" * 40)
    hypothesis_json = hypothesis.to_json()
    print(json.dumps(hypothesis_json, indent=2))
    
    # Traverse Markovian relevance
    print("\n2. Markovian Traversal from Hypothesis:")
    print("-" * 40)
    relevant = hypothesis.find_relevant_contexts(min_probability=0.05)
    for lct_id, prob in relevant:
        print(f"  {lct_id}: {prob:.3f}")
    
    # Demonstrate fractal navigation
    print("\n3. Fractal Graph Navigation:")
    print("-" * 40)
    
    navigator = FractalNavigator()
    navigator.register_lct(premise1)
    navigator.register_lct(premise2)
    navigator.register_lct(hypothesis)
    navigator.register_lct(conclusion)
    navigator.register_lct(alternative)
    
    # Traverse fractal structure
    G = navigator.traverse_fractal(hypothesis, depth=3, breadth=3)
    
    print(f"  Nodes discovered: {len(G.nodes())}")
    print(f"  Edges created: {len(G.edges())}")
    print(f"  Traversal order: {' -> '.join(navigator.traversal_history[:5])}")
    
    # Visualize (if matplotlib available)
    try:
        navigator.visualize_traversal(G, "mrh_fractal_demo.png")
    except:
        print("  (Visualization skipped - matplotlib not available)")
    
    # Demonstrate graph merging
    print("\n4. Graph Merging (Consensus Building):")
    print("-" * 40)
    
    # Create alternative perspective
    alt_perspective = LCT("entity:alt_perspective", {
        "type": "alternative_view",
        "content": "Different interpretation"
    })
    
    alt_perspective.add_relevance(
        premise1,
        probability=0.6,
        relation=MRHRelation.CONTRADICTS,
        distance=1
    )
    
    # Merge graphs
    merged = hypothesis.mrh.merge_graphs(alt_perspective.mrh, merge_probability=0.5)
    print(f"  Original edges: {len(hypothesis.mrh.edges)}")
    print(f"  Alternative edges: {len(alt_perspective.mrh.edges)}")
    print(f"  Merged edges: {len(merged.edges)}")
    
    # Show SPARQL-like query capability
    print("\n5. SPARQL-like Query on RDF Graph:")
    print("-" * 40)
    
    query = """
    SELECT ?target ?prob WHERE {
        ?relevance mrh:target ?target .
        ?relevance mrh:probability ?prob .
        ?relevance mrh:relation mrh:produces .
        FILTER(?prob > 0.5)
    }
    """
    
    print(f"  Query: Find all 'produces' relations with probability > 0.5")
    
    # Execute query (simplified)
    results = []
    for edge in hypothesis.mrh.edges:
        if edge.relation == MRHRelation.PRODUCES and edge.probability > 0.5:
            results.append((edge.target_lct, edge.probability))
    
    for target, prob in results:
        print(f"    -> {target}: {prob:.2f}")
    
    print("\n" + "=" * 60)
    print("Demo Complete")
    print("=" * 60)

def demo_grounding():
    """Demonstrate MRH Grounding functionality"""

    print("\n" + "=" * 60)
    print("MRH GROUNDING DEMONSTRATION - Phase 1 Implementation")
    print("=" * 60)

    # Create an LCT representing a SAGE instance
    sage_legion = LCT("sage:legion-pro-7", {
        "type": "sage_instance",
        "machine": "Legion Pro 7 16IRX8H",
        "os": "Ubuntu 22.04 LTS"
    })

    print("\n1. Creating Grounding Edge for SAGE Legion:")
    print("-" * 40)

    # Create grounding context
    location = LocationContext(
        type="physical",
        value="geo:45.5231,-122.6765",  # Portland, OR
        precision="city",
        verifiable=False
    )

    resource_state = ResourceState(
        compute=0.75,  # 75% compute available
        memory=0.82,   # 82% memory available
        network=0.95,  # 95% network available
        sensors=["gpu", "cpu_thermal", "battery"]
    )

    capabilities = CapabilitiesContext(
        advertised=["compute", "gpu_inference", "vector_db", "rdf_query"],
        hardware_class="server",
        resource_state=resource_state
    )

    session = SessionContext(
        started=datetime.now().isoformat(),
        activity_pattern=hashlib.sha256(b"pattern_data").hexdigest()[:16],
        continuity_token=hashlib.sha256(b"previous_grounding").hexdigest()[:16]
    )

    grounding_context = GroundingContext(
        location=location,
        capabilities=capabilities,
        session=session,
        active_contexts=["sage:thor", "sage:sprout"]
    )

    # Create grounding edge
    grounding_edge = GroundingEdge(
        source=sage_legion.hash,
        target=grounding_context,
        timestamp=datetime.now().isoformat(),
        ttl=timedelta(hours=1),  # 1 hour TTL
        signature=hashlib.sha256(f"{sage_legion.hash}{grounding_context}".encode()).hexdigest(),
        witness_set=["sage:thor", "sage:sprout"]
    )

    # Add to MRH graph
    sage_legion.mrh.add_grounding_edge(grounding_edge)

    print(f"  Source: {grounding_edge.source[:16]}...")
    print(f"  Location: {location.type} - {location.value}")
    print(f"  Hardware Class: {capabilities.hardware_class}")
    print(f"  Capabilities: {', '.join(capabilities.advertised)}")
    print(f"  Resource State: compute={resource_state.compute:.2f}, memory={resource_state.memory:.2f}")
    print(f"  Active Contexts: {', '.join(grounding_context.active_contexts)}")
    print(f"  TTL: {grounding_edge.ttl}")
    print(f"  Time Remaining: {grounding_edge.time_remaining()}")
    print(f"  Witnesses: {len(grounding_edge.witness_set)}")

    print("\n2. RDF Representation (Turtle Format):")
    print("-" * 40)

    # Serialize to Turtle for readability
    turtle_output = sage_legion.mrh.graph.serialize(format='turtle')
    # Show first 20 lines
    turtle_lines = turtle_output.split('\n')
    for line in turtle_lines[:25]:
        if line.strip():
            print(f"  {line}")
    print(f"  ... ({len(turtle_lines)} total lines)")

    print("\n3. Grounding History:")
    print("-" * 40)

    # Add a second grounding (simulating heartbeat update)
    grounding_edge_2 = GroundingEdge(
        source=sage_legion.hash,
        target=grounding_context,  # Same context, just refresh
        timestamp=datetime.now().isoformat(),
        ttl=timedelta(hours=1),
        signature=hashlib.sha256(f"{sage_legion.hash}{grounding_context}2".encode()).hexdigest(),
        witness_set=["sage:thor"]
    )
    sage_legion.mrh.add_grounding_edge(grounding_edge_2)

    history = sage_legion.mrh.get_grounding_history(window_hours=24)
    print(f"  Total groundings in last 24h: {len(history)}")
    for i, g in enumerate(history):
        print(f"  [{i+1}] {g.timestamp} - TTL: {g.ttl} - Witnesses: {len(g.witness_set)}")

    print("\n4. Current Grounding:")
    print("-" * 40)

    current = sage_legion.mrh.get_current_grounding()
    if current:
        print(f"  Timestamp: {current.timestamp}")
        print(f"  Location: {current.target.location.value}")
        print(f"  Hardware Class: {current.target.capabilities.hardware_class}")
        print(f"  Is Expired: {current.is_expired()}")
        print(f"  Time Remaining: {current.time_remaining()}")

    print("\n5. SPARQL Query Example:")
    print("-" * 40)

    query = """
    PREFIX ground: <https://web4.foundation/mrh/grounding#>
    PREFIX lct: <https://web4.foundation/lct/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    SELECT ?grounding ?timestamp ?hardware WHERE {
        ?grounding a ground:GroundingEdge .
        ?grounding ground:timestamp ?timestamp .
        ?grounding ground:capabilities ?caps .
        ?caps ground:hardwareClass ?hardware .
    }
    """

    print("  Query: Find all groundings with their timestamps and hardware class")
    print()

    # Execute SPARQL query on the RDF graph
    results = sage_legion.mrh.graph.query(query)
    for row in results:
        print(f"    -> Timestamp: {row.timestamp}, Hardware: {row.hardware}")

    print("\n6. JSON-LD Export:")
    print("-" * 40)

    lct_json = sage_legion.to_json()
    print(json.dumps(lct_json, indent=2)[:800])
    print("  ... (truncated)")

    print("\n" + "=" * 60)
    print("Phase 1 Implementation Complete!")
    print("Grounding edges successfully integrated into MRH")
    print("=" * 60)

if __name__ == "__main__":
    # Run original demo
    demo_mrh_rdf()

    # Run grounding demo
    demo_grounding()