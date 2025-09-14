


# MRH (Markov Relevancy Horizon) Specification

This document provides the formal specification for the Markov Relevancy Horizon (MRH), a core concept in Web4 that defines the dynamic context of relationships surrounding each entity. Created by Dennis Palatov to extend the information-theoretic concept of Markov blankets to explicitly encompass fractal scales, MRH enables systems to maintain context across multiple levels of organization.

## Evolution: From Lists to RDF Graphs

The MRH has evolved from simple relationship lists to full RDF graphs, enabling:
- Semantic relationships with typed edges
- SPARQL queries for complex relationship patterns
- Trust propagation through graph algorithms
- Fractal composition across scales
- Integration with semantic web standards

## Core Concept: Context Through Relationships

The MRH is fundamentally different from traditional trust models. Rather than calculating trust scores or maintaining global reputation, each entity's MRH is simply the list of other entities it has relationships with. This creates emergent context - an entity's relevance and trustworthiness emerge from WHO it interacts with, not from abstract metrics.

### Key Principles

1. **MRH as RDF Graph**: The MRH is now an RDF graph structure with typed nodes and edges
2. **Semantic Relationships**: Each edge has a semantic type defining the relationship nature
3. **Context Emerges from Graph Structure**: An entity's context is defined by its position in the graph
4. **Dynamic and Self-Updating**: Every interaction updates the graph structure
5. **Horizon Limits Scope**: Graph traversal depth limits maintain Markov property
6. **Fractal Composition**: Graphs can compose across different scales of organization

## 1. MRH Implementation as RDF Graph

### 1.1 RDF Triple Structure

The MRH is implemented as an RDF graph where each relationship is a triple:

```turtle
@prefix web4: <https://web4.io/ontology#> .
@prefix lct: <https://web4.io/lct/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# Entity relationships as RDF triples
lct:alice web4:boundTo lct:hardware1 .
lct:alice web4:pairedWith lct:bob .
lct:alice web4:witnessedBy lct:timeserver .

# Relationship metadata using reification
_:binding1 a web4:Binding ;
    web4:subject lct:alice ;
    web4:predicate web4:boundTo ;
    web4:object lct:hardware1 ;
    web4:bindingType "permanent" ;
    web4:timestamp "2025-09-11T15:00:00Z"^^xsd:dateTime .
```

### 1.2 Graph Node Structure

```python
class MRHNode:
    lct_id: str              # Unique LCT identifier
    entity_type: str         # human, ai, device, role, etc.
    trust_scores: Dict       # Multi-dimensional trust metrics
    metadata: Dict           # Additional entity metadata
    
class MRHEdge:
    source: str              # Source LCT ID
    target: str              # Target LCT ID  
    relation: str            # Semantic relationship type
    probability: float       # Edge weight/probability
    distance: int            # Hop distance from origin
    timestamp: datetime      # When relationship established
    metadata: Dict           # Edge-specific metadata
```

## 2. Semantic Relationships in RDF

### 2.1 Relationship Ontology

The Web4 ontology defines semantic relationship types:

```turtle
# Binding relationships (permanent)
web4:boundTo rdfs:subPropertyOf web4:hasRelationship ;
    rdfs:comment "Permanent hardware or identity binding" .

web4:parentBinding rdfs:subPropertyOf web4:boundTo .
web4:childBinding rdfs:subPropertyOf web4:boundTo .
web4:siblingBinding rdfs:subPropertyOf web4:boundTo .

# Pairing relationships (session-based)
web4:pairedWith rdfs:subPropertyOf web4:hasRelationship ;
    rdfs:comment "Authorized operational pairing" .

web4:energyPairing rdfs:subPropertyOf web4:pairedWith .
web4:dataPairing rdfs:subPropertyOf web4:pairedWith .
web4:servicePairing rdfs:subPropertyOf web4:pairedWith .

# Witness relationships (trust-building)
web4:witnessedBy rdfs:subPropertyOf web4:hasRelationship ;
    rdfs:comment "Attestation and validation relationship" .

web4:timeWitness rdfs:subPropertyOf web4:witnessedBy .
web4:auditWitness rdfs:subPropertyOf web4:witnessedBy .
web4:oracleWitness rdfs:subPropertyOf web4:witnessedBy .
```

## 3. How MRH Creates Context

### 2.1 Relationship Types Define Context

Each relationship type creates different contextual meaning:

- **Bound Relationships**: Create hierarchical context (parent/child/sibling)
  - Parent binding: Entity inherits trust context from parent
  - Child binding: Entity extends parent's capabilities
  - Sibling binding: Entities share common parent context

- **Paired Relationships**: Create operational context
  - Energy management pairing: Entities can exchange energy credits
  - Data exchange pairing: Entities can share information
  - Service pairing: One entity provides services to another

- **Witness Relationships**: Create validation context
  - Time witnesses: Provide temporal ordering
  - Audit witnesses: Validate compliance
  - Oracle witnesses: Provide external data

### 2.2 Context Propagation

Context flows through the MRH via relationship chains:

1. **Direct Context** (Depth 1): Immediate relationships define primary context
2. **Inherited Context** (Depth 2): Context from relationships' relationships
3. **Network Context** (Depth 3+): Broader network effects, limited by horizon_depth

### 3.3 The Markov Property with Graph Traversal

The "Markov" in MRH means that beyond a certain graph traversal depth, relationships become irrelevant:

```sparql
# SPARQL query to find entities within horizon
PREFIX web4: <https://web4.io/ontology#>

SELECT ?entity ?distance WHERE {
    # Find all entities within 3 hops
    {
        <lct:origin> web4:hasRelationship ?entity .
        BIND(1 AS ?distance)
    } UNION {
        <lct:origin> web4:hasRelationship ?hop1 .
        ?hop1 web4:hasRelationship ?entity .
        BIND(2 AS ?distance)
    } UNION {
        <lct:origin> web4:hasRelationship ?hop1 .
        ?hop1 web4:hasRelationship ?hop2 .
        ?hop2 web4:hasRelationship ?entity .
        BIND(3 AS ?distance)
    }
    FILTER(?distance <= 3)  # Horizon depth
}
```

- Default horizon_depth = 3 (you, your connections, their connections)
- Graph algorithms prune traversal beyond horizon
- Maintains computational efficiency and local context focus
- Enables fractal composition at different scales

## 4. MRH Dynamics and Graph Updates

### 4.1 Automatic Graph Updates

The MRH graph updates automatically through entity interactions:

| Action | Graph Update | RDF Triple Added | Context Change |
|--------|--------------|------------------|----------------|
| Binding established | Add edge | `<A> web4:boundTo <B>` | Hierarchical context created |
| Pairing initiated | Add edge | `<A> web4:pairedWith <B>` | Operational context created |
| Witness attestation | Add/update edge | `<A> web4:witnessedBy <B>` | Validation context strengthened |
| Relationship revoked | Remove edge | Delete triple | Context removed |
| Trust propagation | Update weights | Modify edge metadata | Trust scores adjusted |

### 4.2 Trust Emergence and Propagation

Trust emerges from graph patterns and propagates through edges:

```python
# Trust propagation algorithms
class TrustPropagation:
    def multiplicative(self, path: List[MRHEdge]) -> float:
        """Trust decays multiplicatively along path"""
        trust = 1.0
        for edge in path:
            trust *= edge.probability * (self.decay_rate ** edge.distance)
        return trust
    
    def probabilistic(self, paths: List[List[MRHEdge]]) -> float:
        """Combine multiple paths probabilistically"""
        combined = 1.0
        for path in paths:
            path_trust = self.multiplicative(path)
            combined = 1 - ((1 - combined) * (1 - path_trust))
        return combined
    
    def maximal(self, paths: List[List[MRHEdge]]) -> float:
        """Take highest trust path"""
        return max(self.multiplicative(path) for path in paths)
```

Trust patterns in the graph:
- High in-degree of witness edges → Higher perceived reliability
- Stable long-term pairing edges → Established operational trust
- Strong binding subgraphs → Institutional trust
- Central position in trust graph → Network authority

## 5. Role-Contextual T3/V3 Tensors

### 5.1 Critical Principle: Trust is Role-Specific

**T3/V3 tensors are not absolute properties of entities - they only exist within the context of specific roles.** A person trusted as a surgeon has no inherent trust as a mechanic. RDF triples explicitly bind trust and value tensors to role pairings.

### 5.2 Role-Bound Trust Tensor (T3)

Trust tensors are always qualified by role context:

```turtle
# Trust is tied to entity-role pairs
lct:alice web4:hasRole web4:Surgeon .
lct:alice web4:hasRole web4:Researcher .

# T3 tensors exist only for entity-role combinations
_:trust1 a web4:T3Tensor ;
    web4:entity lct:alice ;
    web4:role web4:Surgeon ;
    web4:talent 0.95 ;       # High surgical skill
    web4:training 0.90 ;     # Extensive medical training
    web4:temperament 0.88 .  # Consistent surgical performance

_:trust2 a web4:T3Tensor ;
    web4:entity lct:alice ;
    web4:role web4:Mechanic ;
    web4:talent 0.20 ;       # Low mechanical skill
    web4:training 0.15 ;     # Minimal mechanical training
    web4:temperament 0.30 .  # Inconsistent mechanical work
```

### 5.3 Role-Contextual Value Tensor (V3)

Value creation is measured within role contexts:

```python
class RoleContextualT3V3:
    def __init__(self, entity_id: str, role: str):
        self.entity_id = entity_id
        self.role = role
        self.t3 = None  # Trust tensor for this role
        self.v3 = None  # Value tensor for this role
    
    def get_trust_in_role(self, graph: RDFGraph) -> T3Tensor:
        """Get T3 tensor for entity in specific role"""
        query = f"""
        SELECT ?talent ?training ?temperament WHERE {{
            ?tensor web4:entity <{self.entity_id}> ;
                    web4:role <{self.role}> ;
                    web4:talent ?talent ;
                    web4:training ?training ;
                    web4:temperament ?temperament .
        }}
        """
        return graph.query(query)
    
    def calculate_role_trust(self, interaction_type: str) -> float:
        """Trust depends on role-interaction alignment"""
        if not self.role_matches_interaction(interaction_type):
            return 0.0  # No trust outside of role context
        return self.t3.compute_trust_score()
```

### 5.4 Role Pairing in MRH

RDF enables precise role-based relationship modeling:

```turtle
# Pairing with role context
_:pairing1 a web4:RolePairing ;
    web4:subject lct:alice ;
    web4:subjectRole web4:Surgeon ;
    web4:object lct:hospital ;
    web4:objectRole web4:MedicalFacility ;
    web4:trustContext "surgical-procedures" ;
    web4:t3Score 0.92 .

_:pairing2 a web4:RolePairing ;
    web4:subject lct:alice ;
    web4:subjectRole web4:CarOwner ;  # Different role
    web4:object lct:garage ;
    web4:objectRole web4:AutoRepair ;
    web4:trustContext "vehicle-maintenance" ;
    web4:t3Score 0.15 .  # Low trust in mechanical context
```

### 5.5 SPARQL for Role-Based Trust Queries

```sparql
# Find entities trusted for specific role
PREFIX web4: <https://web4.io/ontology#>

SELECT ?entity ?trustScore WHERE {
    ?tensor a web4:T3Tensor ;
            web4:entity ?entity ;
            web4:role web4:Surgeon ;
            web4:talent ?talent ;
            web4:training ?training ;
            web4:temperament ?temperament .
    
    # Calculate composite trust score for role
    BIND((?talent * 0.4 + ?training * 0.3 + ?temperament * 0.3) AS ?trustScore)
    FILTER(?trustScore > 0.8)
}
ORDER BY DESC(?trustScore)

# Find best role match for interaction
SELECT ?entity ?role (MAX(?trust) AS ?maxTrust) WHERE {
    ?pairing web4:interactionType "medical-procedure" ;
             web4:subject ?entity ;
             web4:subjectRole ?role ;
             web4:t3Score ?trust .
} 
GROUP BY ?entity ?role
ORDER BY DESC(?maxTrust)
```

## 6. SPARQL Queries for MRH Analysis

Common SPARQL patterns for MRH queries:

```sparql
# Find trust paths between entities
SELECT ?path ?trust WHERE {
    <lct:alice> (web4:hasRelationship+) <lct:bob> .
    # Calculate trust along path
}

# Identify high-trust clusters
SELECT ?cluster (AVG(?trust) as ?avg_trust) WHERE {
    ?member web4:memberOf ?cluster .
    ?member web4:trustScore ?trust .
} GROUP BY ?cluster
HAVING (?avg_trust > 0.8)

# Find witness consensus
SELECT ?entity (COUNT(?witness) as ?witness_count) WHERE {
    ?entity web4:witnessedBy ?witness .
    ?witness web4:witnessRole web4:timeWitness .
} GROUP BY ?entity
ORDER BY DESC(?witness_count)
```

## 7. Implementation References

- [MRH RDF Specification](../MRH_RDF_SPECIFICATION.md) - Complete RDF implementation details
- [MRH RDF Implementation](../mrh_rdf_implementation.py) - Python reference implementation
- [SPARQL Query Examples](../mrh_sparql_queries.py) - Query patterns and examples
- [Trust Propagation](../mrh_trust_propagation.py) - Trust flow algorithms
- [MRH Visualizer](../mrh_visualizer.py) - Interactive graph visualization


