"""
Web4 Governance Service - REST API Server
=========================================

Research prototype REST API server for the Web4 Governance Service (Law Oracle).

Provides:
- Law dataset queries
- Action legality checks
- Role permission queries
- Governance version control

Based on the Law Oracle implementation from Session 03.

API Endpoints:
--------------
GET    /v1/law/version         - Get current law version
POST   /v1/law/check           - Check if action is legal
GET    /v1/law/permissions     - Get permissions for role
GET    /health, /ready, /metrics

Author: Web4 Infrastructure Team
License: MIT
"""

import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent / "reference"))

from law_oracle import LawOracle, create_default_law_dataset

try:
    from fastapi import FastAPI, HTTPException, Request, status, Query
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    print("FastAPI not installed")
    sys.exit(1)

try:
    from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
    from starlette.responses import Response
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False


class CheckLegalityRequest(BaseModel):
    action: str
    entity_type: str
    role: str

    class Config:
        schema_extra = {
            "example": {
                "action": "compute",
                "entity_type": "ai",
                "role": "researcher"
            }
        }


if METRICS_AVAILABLE:
    law_checks_counter = Counter(
        'web4_governance_law_checks_total',
        'Total law checks',
        ['action', 'entity_type', 'result']
    )


app = FastAPI(
    title="Web4 Governance Service",
    description="Law Oracle for machine-readable governance",
    version="1.0.0",
    docs_url="/docs"
)

law_oracle: Optional[LawOracle] = None
SERVICE_VERSION = "1.0.0"
SERVICE_START_TIME = datetime.now(timezone.utc)


@app.on_event("startup")
async def startup_event():
    global law_oracle
    society_id = "society:web4_default"
    law_oracle_lct = "lct:web4:oracle:law:default:1"

    law_oracle = LawOracle(society_id, law_oracle_lct)

    # Publish default law dataset
    law_dataset = create_default_law_dataset(society_id, law_oracle_lct, "1.0.0")
    law_oracle.publish_law_dataset(law_dataset)

    print(f"✅ Web4 Governance Service started")
    print(f"   Society: {society_id}")
    print(f"   Law Version: {law_dataset.version}")
    print(f"   Port: 8002")
    print(f"   Docs: http://localhost:8002/docs")


@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Web4 Governance Service shutting down")


@app.get("/v1/law/version")
async def get_law_version():
    """Get current law dataset version and metadata"""
    try:
        version_info = law_oracle.get_current_version()

        return {
            "success": True,
            "data": {
                "version": version_info.get("version", "1.0.0"),
                "hash": version_info.get("hash", "unknown"),
                "norm_count": version_info.get("norm_count", 0),
                "enacted_at": version_info.get("enacted_at", datetime.now(timezone.utc).isoformat())
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Version query failed: {str(e)}")


@app.post("/v1/law/check")
async def check_legality(req: CheckLegalityRequest):
    """
    Check if an action is legal for given entity type and role.

    Returns legality determination based on current law dataset.
    """
    try:
        is_legal = law_oracle.check_action_legal(
            action=req.action,
            entity_type=req.entity_type,
            role=req.role
        )

        # Update metrics
        if METRICS_AVAILABLE:
            law_checks_counter.labels(
                action=req.action,
                entity_type=req.entity_type,
                result="legal" if is_legal else "illegal"
            ).inc()

        return {
            "success": True,
            "data": {
                "action": req.action,
                "entity_type": req.entity_type,
                "role": req.role,
                "legal": is_legal,
                "law_version": "1.0.0"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Legality check failed: {str(e)}")


@app.get("/v1/law/permissions")
async def get_permissions(
    entity_type: str = Query(..., description="Entity type (human, ai, org, device)"),
    role: str = Query(..., description="Role (researcher, admin, etc)")
):
    """Get permissions for entity type and role"""
    try:
        permissions = law_oracle.get_permissions(entity_type, role)

        return {
            "success": True,
            "data": {
                "entity_type": entity_type,
                "role": role,
                "permissions": permissions,
                "law_version": "1.0.0"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Permissions query failed: {str(e)}")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": SERVICE_VERSION
    }


@app.get("/ready")
async def readiness_check():
    if law_oracle is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    return {
        "status": "ready",
        "uptime_seconds": (datetime.now(timezone.utc) - SERVICE_START_TIME).total_seconds()
    }


@app.get("/metrics")
async def metrics():
    if not METRICS_AVAILABLE:
        return JSONResponse(content={"error": "Metrics not available"}, status_code=501)
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def main():
    import os
    host = os.getenv("WEB4_GOVERNANCE_HOST", "0.0.0.0")
    port = int(os.getenv("WEB4_GOVERNANCE_PORT", "8002"))
    workers = int(os.getenv("WEB4_GOVERNANCE_WORKERS", "1"))
    debug = os.getenv("WEB4_GOVERNANCE_DEBUG", "false").lower() == "true"

    print(f"\n🚀 Starting Web4 Governance Service")
    print(f"   Host: {host}, Port: {port}")
    print(f"   Docs: http://{host}:{port}/docs\n")

    uvicorn.run(
        "governance_service:app",
        host=host,
        port=port,
        workers=workers,
        reload=debug,
        log_level="info" if not debug else "debug"
    )


if __name__ == "__main__":
    main()
