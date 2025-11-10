"""
Web4 Knowledge Service - REST API Server
========================================

Production-ready REST API server for the Web4 Knowledge Service (MRH Graph).

Provides:
- RDF triple storage and queries
- SPARQL query interface
- Trust propagation computation
- Graph traversal operations
- Relationship discovery

Based on the MRH Graph implementation from Session 03.

API Endpoints:
--------------
POST   /v1/graph/triple         - Add RDF triple
POST   /v1/graph/query          - Execute SPARQL query
GET    /v1/graph/trust/{entity} - Get trust propagation
POST   /v1/graph/traverse       - Graph traversal
GET    /v1/graph/relationships/{entity} - Get entity relationships
GET    /v1/graph/stats          - Get graph statistics
GET    /health, /ready, /metrics

Author: Web4 Infrastructure Team
License: MIT
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent / "reference"))

from mrh_graph import MRHGraph, RelationType, T3Tensor

try:
    from fastapi import FastAPI, HTTPException, Request, status, Query
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError:
    print("FastAPI not installed. Install with: pip install fastapi uvicorn")
    sys.exit(1)

try:
    from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
    from starlette.responses import Response
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    print("Warning: prometheus_client not installed. Metrics disabled.")


# =============================================================================
# Pydantic Models
# =============================================================================

class AddTripleRequest(BaseModel):
    """Request to add RDF triple"""
    subject: str = Field(..., min_length=1)
    predicate: str = Field(..., min_length=1)
    object: str = Field(..., min_length=1)
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "subject": "lct:web4:ai:society:001",
                "predicate": "memberOf",
                "object": "society:ai_research_lab",
                "metadata": {"timestamp": "2025-11-10T12:00:00Z"}
            }
        }


class SPARQLQueryRequest(BaseModel):
    """SPARQL query request"""
    query: str = Field(..., min_length=1)
    limit: Optional[int] = Field(100, ge=1, le=10000)

    class Config:
        schema_extra = {
            "example": {
                "query": "SELECT ?action WHERE { <lct:web4:ai:society:001> performed ?action }",
                "limit": 100
            }
        }


class TraverseRequest(BaseModel):
    """Graph traversal request"""
    start_entity: str
    relationship_type: Optional[str] = None
    max_depth: int = Field(3, ge=1, le=10)
    direction: str = Field("outgoing", regex="^(outgoing|incoming|both)$")

    class Config:
        schema_extra = {
            "example": {
                "start_entity": "lct:web4:ai:society:001",
                "relationship_type": "delegates",
                "max_depth": 3,
                "direction": "outgoing"
            }
        }


# =============================================================================
# Metrics
# =============================================================================

if METRICS_AVAILABLE:
    triples_counter = Counter(
        'web4_knowledge_triples_total',
        'Total RDF triples stored',
        ['predicate_type']
    )

    graph_size_gauge = Gauge(
        'web4_knowledge_graph_size',
        'Total number of triples in graph'
    )

    sparql_queries_counter = Counter(
        'web4_knowledge_sparql_queries_total',
        'Total SPARQL queries executed',
        ['query_type']
    )

    query_duration = Histogram(
        'web4_knowledge_query_duration_seconds',
        'SPARQL query duration',
        ['query_type']
    )

    trust_propagation_counter = Counter(
        'web4_knowledge_trust_propagation_total',
        'Trust propagation computations'
    )


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Web4 Knowledge Service",
    description="MRH Graph with RDF storage and SPARQL queries",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global state
mrh_graph: Optional[MRHGraph] = None
SERVICE_VERSION = "1.0.0"
SERVICE_START_TIME = datetime.now(timezone.utc)


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    global mrh_graph

    mrh_graph = MRHGraph()

    print(f"✅ Web4 Knowledge Service started")
    print(f"   Version: {SERVICE_VERSION}")
    print(f"   Port: 8006")
    print(f"   Docs: http://localhost:8006/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Web4 Knowledge Service shutting down")


# =============================================================================
# API Endpoints
# =============================================================================

@app.post("/v1/graph/triple", status_code=status.HTTP_201_CREATED)
async def add_triple(req: AddTripleRequest):
    """
    Add an RDF triple to the knowledge graph.

    RDF triples represent relationships in subject-predicate-object form:
    - **Subject**: Entity performing action or having property
    - **Predicate**: Relationship or property type
    - **Object**: Target entity or value

    **Common Predicates**:
    - `memberOf`: Society membership
    - `delegates`: Delegation relationship
    - `witnesses`: Witness attestation
    - `performed`: Action execution
    - `hasTrust`: T3 reputation tensor
    - `hasValue`: V3 reputation tensor

    **Returns**:
    - Triple ID
    - Confirmation
    - Updated graph size
    """
    try:
        # Add triple to graph
        triple_id = mrh_graph.add_triple(
            subject=req.subject,
            predicate=req.predicate,
            object=req.object,
            metadata=req.metadata or {}
        )

        # Update metrics
        if METRICS_AVAILABLE:
            triples_counter.labels(predicate_type=req.predicate).inc()
            graph_size_gauge.set(len(mrh_graph.triples))

        return {
            "success": True,
            "data": {
                "triple_id": triple_id,
                "subject": req.subject,
                "predicate": req.predicate,
                "object": req.object,
                "graph_size": len(mrh_graph.triples),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add triple: {str(e)}")


@app.post("/v1/graph/query")
async def execute_sparql_query(req: SPARQLQueryRequest):
    """
    Execute SPARQL query on knowledge graph.

    SPARQL is a query language for RDF graphs, similar to SQL for databases.

    **Supported Query Types**:
    - SELECT: Retrieve specific variables
    - ASK: Boolean query (does pattern exist?)
    - CONSTRUCT: Build new graph from results
    - DESCRIBE: Get all info about entity

    **Example Queries**:
    ```sparql
    # Get all actions by entity
    SELECT ?action WHERE {
        <lct:web4:ai:society:001> performed ?action
    }

    # Find delegation chains
    SELECT ?delegate WHERE {
        <lct:web4:human:alice> delegates ?delegate
    }

    # Get trust network
    SELECT ?entity ?trust WHERE {
        ?entity hasTrust ?trust
    }
    ```

    **Query Complexity**:
    - Simple: < 10ms (direct lookup)
    - Medium: < 100ms (pattern matching)
    - Complex: < 1s (graph traversal)

    **Returns**:
    - Query results as list of bindings
    - Query metadata (execution time, result count)
    """
    try:
        # Parse query type from SPARQL
        query_upper = req.query.upper()
        if "SELECT" in query_upper:
            query_type = "SELECT"
        elif "ASK" in query_upper:
            query_type = "ASK"
        elif "CONSTRUCT" in query_upper:
            query_type = "CONSTRUCT"
        elif "DESCRIBE" in query_upper:
            query_type = "DESCRIBE"
        else:
            query_type = "UNKNOWN"

        # Execute query
        start_time = datetime.now(timezone.utc)
        results = mrh_graph.query(req.query, limit=req.limit)
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

        # Update metrics
        if METRICS_AVAILABLE:
            sparql_queries_counter.labels(query_type=query_type).inc()
            query_duration.labels(query_type=query_type).observe(duration)

        return {
            "success": True,
            "data": {
                "query_type": query_type,
                "results": results,
                "result_count": len(results) if isinstance(results, list) else 1,
                "execution_time_ms": duration * 1000,
                "graph_size": len(mrh_graph.triples)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")


@app.get("/v1/graph/trust/{entity_id}")
async def get_trust_propagation(
    entity_id: str,
    max_depth: int = Query(3, ge=1, le=10, description="Maximum propagation depth")
):
    """
    Compute trust propagation from an entity.

    Trust propagates through the relationship graph using the Markov
    Resonance Hypothesis (MRH). Trust decays with distance based on:
    - Relationship strength
    - Network topology
    - Markov horizon (max depth)

    **Algorithm**:
    1. Start with entity's direct T3 trust score
    2. Propagate through relationships (delegates, witnesses, etc.)
    3. Apply decay factor based on distance
    4. Aggregate trust from multiple paths
    5. Stop at Markov horizon

    **Parameters**:
    - `max_depth`: Maximum graph distance (1-10, default 3)

    **Returns**:
    - Direct connections with trust scores
    - Extended network (indirect connections)
    - Trust decay per hop
    - Network statistics
    """
    try:
        # Compute trust propagation
        trust_network = mrh_graph.propagate_trust(
            start_entity=entity_id,
            max_depth=max_depth
        )

        # Update metrics
        if METRICS_AVAILABLE:
            trust_propagation_counter.inc()

        return {
            "success": True,
            "data": {
                "entity_id": entity_id,
                "max_depth": max_depth,
                "direct_connections": trust_network.get("direct", []),
                "extended_network": trust_network.get("extended", []),
                "total_reachable": len(trust_network.get("direct", [])) + len(trust_network.get("extended", [])),
                "trust_decay_factor": trust_network.get("decay_factor", 0.8),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trust propagation failed: {str(e)}")


@app.post("/v1/graph/traverse")
async def traverse_graph(req: TraverseRequest):
    """
    Traverse the knowledge graph from a starting entity.

    Graph traversal explores the network of relationships:
    - **Outgoing**: Follow relationships from entity
    - **Incoming**: Follow relationships to entity
    - **Both**: Bidirectional traversal

    **Use Cases**:
    - Find all entities an agent delegates to
    - Discover who witnesses an entity
    - Map organizational hierarchies
    - Trace action chains
    - Identify communities

    **Parameters**:
    - `start_entity`: Starting point for traversal
    - `relationship_type`: Optional filter (e.g., "delegates", "witnesses")
    - `max_depth`: Maximum distance to traverse (1-10)
    - `direction`: "outgoing", "incoming", or "both"

    **Returns**:
    - Entities at each depth level
    - Relationship paths
    - Network diameter
    - Traversal statistics
    """
    try:
        # Traverse graph
        traversal_result = mrh_graph.traverse(
            start_entity=req.start_entity,
            relationship_type=req.relationship_type,
            max_depth=req.max_depth,
            direction=req.direction
        )

        return {
            "success": True,
            "data": {
                "start_entity": req.start_entity,
                "relationship_type": req.relationship_type,
                "max_depth": req.max_depth,
                "direction": req.direction,
                "nodes_visited": traversal_result.get("nodes", []),
                "edges_traversed": traversal_result.get("edges", []),
                "depth_distribution": traversal_result.get("depth_dist", {}),
                "total_nodes": len(traversal_result.get("nodes", [])),
                "total_edges": len(traversal_result.get("edges", []))
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph traversal failed: {str(e)}")


@app.get("/v1/graph/relationships/{entity_id}")
async def get_relationships(entity_id: str):
    """
    Get all relationships for an entity.

    Returns both outgoing and incoming relationships:
    - **Outgoing**: Relationships where entity is subject
    - **Incoming**: Relationships where entity is object

    **Relationship Types**:
    - Society membership (memberOf)
    - Delegations (delegates)
    - Witness attestations (witnesses)
    - Actions performed (performed)
    - Trust scores (hasTrust)
    - Value creation (hasValue)

    **Returns**:
    - Outgoing relationships
    - Incoming relationships
    - Relationship counts by type
    - Most common relationships
    """
    try:
        # Get relationships
        relationships = mrh_graph.get_relationships(entity_id)

        return {
            "success": True,
            "data": {
                "entity_id": entity_id,
                "outgoing": relationships.get("outgoing", []),
                "incoming": relationships.get("incoming", []),
                "outgoing_count": len(relationships.get("outgoing", [])),
                "incoming_count": len(relationships.get("incoming", [])),
                "total_count": len(relationships.get("outgoing", [])) + len(relationships.get("incoming", [])),
                "relationship_types": relationships.get("types", {})
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Relationship query failed: {str(e)}")


@app.get("/v1/graph/stats")
async def get_graph_stats():
    """
    Get knowledge graph statistics.

    Provides overview of graph structure and content:
    - Total triples (nodes + edges)
    - Unique entities
    - Relationship types and counts
    - Graph density
    - Largest connected components

    **Useful for**:
    - Monitoring graph growth
    - Understanding data distribution
    - Identifying bottlenecks
    - Planning queries
    - Capacity planning

    **Returns**:
    - Triple count
    - Entity count
    - Relationship distribution
    - Graph metrics
    """
    try:
        stats = mrh_graph.get_stats()

        return {
            "success": True,
            "data": {
                "total_triples": len(mrh_graph.triples),
                "unique_subjects": stats.get("unique_subjects", 0),
                "unique_objects": stats.get("unique_objects", 0),
                "unique_entities": stats.get("unique_entities", 0),
                "predicate_distribution": stats.get("predicates", {}),
                "most_connected_entities": stats.get("top_entities", []),
                "graph_density": stats.get("density", 0.0),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats query failed: {str(e)}")


# =============================================================================
# Health and Metrics Endpoints
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": SERVICE_VERSION
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    if mrh_graph is None:
        raise HTTPException(
            status_code=503,
            detail="Service not ready: MRH graph not initialized"
        )

    return {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": (datetime.now(timezone.utc) - SERVICE_START_TIME).total_seconds(),
        "graph_size": len(mrh_graph.triples)
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    if not METRICS_AVAILABLE:
        return JSONResponse(
            content={"error": "Metrics not available"},
            status_code=501
        )

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """
    Run the Knowledge Service.

    Configuration via environment variables:
    - WEB4_KNOWLEDGE_HOST: Host to bind (default: 0.0.0.0)
    - WEB4_KNOWLEDGE_PORT: Port to listen (default: 8006)
    - WEB4_KNOWLEDGE_WORKERS: Number of workers (default: 1)
    - WEB4_KNOWLEDGE_DEBUG: Debug mode (default: False)
    """
    import os

    host = os.getenv("WEB4_KNOWLEDGE_HOST", "0.0.0.0")
    port = int(os.getenv("WEB4_KNOWLEDGE_PORT", "8006"))
    workers = int(os.getenv("WEB4_KNOWLEDGE_WORKERS", "1"))
    debug = os.getenv("WEB4_KNOWLEDGE_DEBUG", "false").lower() == "true"

    print(f"\n🚀 Starting Web4 Knowledge Service")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Workers: {workers}")
    print(f"   Debug: {debug}")
    print(f"   Docs: http://{host}:{port}/docs\n")

    uvicorn.run(
        "knowledge_service:app",
        host=host,
        port=port,
        workers=workers,
        reload=debug,
        log_level="info" if not debug else "debug"
    )


if __name__ == "__main__":
    main()
