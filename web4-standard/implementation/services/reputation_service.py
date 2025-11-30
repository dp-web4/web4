"""
Web4 Reputation Service - REST API Server
=========================================

Research prototype REST API server for the Web4 Reputation Service.

This service provides:
- T3/V3 reputation computation
- Outcome recording
- Gaming detection
- Reputation queries by entity and role
- Historical reputation tracking

Based on the Reputation Engine implementation from Session 01.

API Endpoints:
--------------
GET    /v1/reputation/{entity_id}      - Get reputation scores
POST   /v1/reputation/record           - Record action outcome
GET    /v1/reputation/{entity_id}/history - Get reputation history
GET    /v1/reputation/leaderboard      - Get top entities by reputation
GET    /health                         - Health check
GET    /ready                          - Readiness check
GET    /metrics                        - Prometheus metrics

Author: Web4 Infrastructure Team
License: MIT
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum

# Add reference implementation to path
sys.path.insert(0, str(Path(__file__).parent.parent / "reference"))

from reputation_engine import ReputationEngine, OutcomeType

try:
    from fastapi import FastAPI, HTTPException, Request, status, Query
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError:
    print("FastAPI not installed. Install with: pip install fastapi uvicorn")
    sys.exit(1)

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    from starlette.responses import Response
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    print("Warning: prometheus_client not installed. Metrics disabled.")


# =============================================================================
# Pydantic Models
# =============================================================================

class OutcomeEnum(str, Enum):
    """Outcome quality levels"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    EXCEPTIONAL_QUALITY = "exceptional_quality"
    POOR_QUALITY = "poor_quality"


class RecordOutcomeRequest(BaseModel):
    """Request to record action outcome"""
    entity: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    outcome: OutcomeEnum
    witnesses: List[str] = Field(default_factory=list)
    context: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "entity": "lct:web4:ai:society:001",
                "role": "researcher",
                "action": "compute",
                "outcome": "exceptional_quality",
                "witnesses": ["human:supervisor:alice"],
                "context": {"task_id": "task_001", "duration": 300}
            }
        }


class ReputationResponse(BaseModel):
    """Reputation scores response"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# =============================================================================
# Metrics
# =============================================================================

if METRICS_AVAILABLE:
    reputation_updates_counter = Counter(
        'web4_reputation_updates_total',
        'Total reputation updates',
        ['entity_type', 'role', 'outcome']
    )

    reputation_t3_gauge = Gauge(
        'web4_reputation_t3_score',
        'T3 (trustworthiness) score',
        ['entity', 'role']
    )

    reputation_v3_gauge = Gauge(
        'web4_reputation_v3_score',
        'V3 (value creation) score',
        ['entity', 'role']
    )

    gaming_detection_counter = Counter(
        'web4_reputation_gaming_detected_total',
        'Total gaming attempts detected',
        ['entity', 'severity']
    )


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Web4 Reputation Service",
    description="T3/V3 reputation tracking with gaming detection",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global state
reputation_engine: Optional[ReputationEngine] = None
SERVICE_VERSION = "1.0.0"
SERVICE_START_TIME = datetime.now(timezone.utc)


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    global reputation_engine

    reputation_engine = ReputationEngine()

    print(f"✅ Web4 Reputation Service started")
    print(f"   Version: {SERVICE_VERSION}")
    print(f"   Docs: http://localhost:8004/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Web4 Reputation Service shutting down")


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/v1/reputation/{entity_id}", response_model=ReputationResponse)
async def get_reputation(
    entity_id: str,
    role: Optional[str] = Query(None, description="Filter by role")
):
    """
    Get reputation scores for an entity.

    Returns T3 (trustworthiness) and V3 (value creation) scores:
    - **T3**: Measures reliability, consistency, honesty
    - **V3**: Measures quality, efficiency, impact

    Scores range from 0.0 to 1.0, with 0.5 as neutral starting point.

    **Query Parameters**:
    - `role`: Optional role filter (e.g., "researcher", "coordinator")

    **Returns**:
    - T3 score (trustworthiness)
    - V3 score (value creation)
    - Action count
    - Last updated timestamp
    - Gaming risk assessment
    """
    try:
        # Get reputation scores
        if role:
            reputation = reputation_engine.get_reputation(entity_id, role)
        else:
            # Get all roles for this entity
            reputation = reputation_engine.get_all_roles_reputation(entity_id)

        if not reputation:
            raise HTTPException(
                status_code=404,
                detail=f"No reputation found for entity: {entity_id}"
            )

        # Update Prometheus gauges
        if METRICS_AVAILABLE and role:
            reputation_t3_gauge.labels(entity=entity_id, role=role).set(
                reputation.get('t3_score', 0.5)
            )
            reputation_v3_gauge.labels(entity=entity_id, role=role).set(
                reputation.get('v3_score', 0.5)
            )

        return ReputationResponse(
            success=True,
            data={
                "entity_id": entity_id,
                "role": role if role else "all",
                "t3_score": reputation.get('t3_score', 0.5),
                "v3_score": reputation.get('v3_score', 0.5),
                "action_count": reputation.get('action_count', 0),
                "last_updated": reputation.get('last_updated', datetime.now(timezone.utc).isoformat()),
                "gaming_risk": reputation.get('gaming_risk', 'unknown')
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/v1/reputation/record", response_model=ReputationResponse, status_code=status.HTTP_201_CREATED)
async def record_outcome(request: RecordOutcomeRequest):
    """
    Record an action outcome to update reputation.

    This endpoint updates both T3 and V3 scores based on:
    - Action outcome (success, failure, quality)
    - Witness attestations
    - Historical behavior patterns
    - Gaming detection results

    **Gaming Detection**:
    The system automatically detects:
    - Self-dealing attempts
    - Reputation farming
    - Collusion patterns
    - Anomalous behavior

    **Returns**:
    - Updated T3/V3 scores
    - Score deltas (change from previous)
    - Gaming risk assessment
    - Action count
    """
    try:
        # Map string outcome to enum
        outcome_map = {
            "success": OutcomeType.SUCCESS,
            "partial_success": OutcomeType.PARTIAL_SUCCESS,
            "failure": OutcomeType.FAILURE,
            "exceptional_quality": OutcomeType.EXCEPTIONAL_QUALITY,
            "poor_quality": OutcomeType.POOR_QUALITY
        }

        outcome_type = outcome_map[request.outcome.value]

        # Record outcome
        previous_rep = reputation_engine.get_reputation(request.entity, request.role)
        previous_t3 = previous_rep.get('t3_score', 0.5) if previous_rep else 0.5
        previous_v3 = previous_rep.get('v3_score', 0.5) if previous_rep else 0.5

        reputation_engine.record_outcome(
            entity=request.entity,
            role=request.role,
            action=request.action,
            outcome=outcome_type,
            witnesses=request.witnesses,
            context=request.context or {}
        )

        # Get updated reputation
        updated_rep = reputation_engine.get_reputation(request.entity, request.role)

        t3_score = updated_rep.get('t3_score', 0.5)
        v3_score = updated_rep.get('v3_score', 0.5)
        gaming_risk = updated_rep.get('gaming_risk', 'low')

        # Update metrics
        if METRICS_AVAILABLE:
            entity_type = request.entity.split(':')[2] if ':' in request.entity else 'unknown'
            reputation_updates_counter.labels(
                entity_type=entity_type,
                role=request.role,
                outcome=request.outcome.value
            ).inc()

            reputation_t3_gauge.labels(entity=request.entity, role=request.role).set(t3_score)
            reputation_v3_gauge.labels(entity=request.entity, role=request.role).set(v3_score)

            if gaming_risk != 'low':
                gaming_detection_counter.labels(
                    entity=request.entity,
                    severity=gaming_risk
                ).inc()

        return ReputationResponse(
            success=True,
            data={
                "entity_id": request.entity,
                "role": request.role,
                "t3_score": t3_score,
                "v3_score": v3_score,
                "t3_delta": t3_score - previous_t3,
                "v3_delta": v3_score - previous_v3,
                "action_count": updated_rep.get('action_count', 1),
                "gaming_risk": gaming_risk,
                "witnesses": len(request.witnesses),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Invalid outcome type: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/v1/reputation/{entity_id}/history")
async def get_reputation_history(
    entity_id: str,
    role: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get reputation history for an entity.

    Returns time-series data of reputation changes.

    **Query Parameters**:
    - `role`: Optional role filter
    - `limit`: Maximum number of records (1-1000, default 100)

    **Returns**:
    - List of reputation snapshots with timestamps
    - T3/V3 scores over time
    - Action outcomes
    - Witness counts

    **TODO**: Implement historical tracking in reputation engine
    """
    # Stub implementation
    return {
        "success": True,
        "data": {
            "entity_id": entity_id,
            "role": role,
            "history": [
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "t3_score": 0.5,
                    "v3_score": 0.5,
                    "action": "initial",
                    "outcome": "success"
                }
            ],
            "note": "Historical tracking not yet implemented"
        }
    }


@app.get("/v1/reputation/leaderboard")
async def get_leaderboard(
    role: Optional[str] = Query(None),
    metric: str = Query("t3", regex="^(t3|v3|both)$"),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get reputation leaderboard.

    Returns top entities by reputation score.

    **Query Parameters**:
    - `role`: Optional role filter
    - `metric`: Ranking metric - "t3", "v3", or "both" (default: t3)
    - `limit`: Number of entities to return (1-100, default 10)

    **Returns**:
    - Ranked list of entities
    - Scores and ranks
    - Action counts

    **TODO**: Implement leaderboard in reputation engine
    """
    # Stub implementation
    return {
        "success": True,
        "data": {
            "metric": metric,
            "role": role,
            "leaderboard": [],
            "note": "Leaderboard not yet implemented"
        }
    }


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
    if reputation_engine is None:
        raise HTTPException(
            status_code=503,
            detail="Service not ready: Reputation engine not initialized"
        )

    return {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": (datetime.now(timezone.utc) - SERVICE_START_TIME).total_seconds()
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
    Run the Reputation Service.

    Configuration via environment variables:
    - WEB4_REPUTATION_HOST: Host to bind (default: 0.0.0.0)
    - WEB4_REPUTATION_PORT: Port to listen (default: 8004)
    - WEB4_REPUTATION_WORKERS: Number of workers (default: 1)
    - WEB4_REPUTATION_DEBUG: Debug mode (default: False)
    """
    import os

    host = os.getenv("WEB4_REPUTATION_HOST", "0.0.0.0")
    port = int(os.getenv("WEB4_REPUTATION_PORT", "8004"))
    workers = int(os.getenv("WEB4_REPUTATION_WORKERS", "1"))
    debug = os.getenv("WEB4_REPUTATION_DEBUG", "false").lower() == "true"

    print(f"\n🚀 Starting Web4 Reputation Service")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Workers: {workers}")
    print(f"   Debug: {debug}")
    print(f"   Docs: http://{host}:{port}/docs\n")

    uvicorn.run(
        "reputation_service:app",
        host=host,
        port=port,
        workers=workers,
        reload=debug,
        log_level="info" if not debug else "debug"
    )


if __name__ == "__main__":
    main()
