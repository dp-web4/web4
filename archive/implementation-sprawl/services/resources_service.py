"""
Web4 Resources Service - REST API Server
========================================

Research prototype REST API server for the Web4 Resources Service.

Provides ATP-based resource allocation and metering for:
- CPU cycles
- Memory (RAM)
- Storage (disk)
- Network bandwidth

Based on the Resource Allocator implementation from Session 02.

API Endpoints:
--------------
POST   /v1/resources/allocate       - Allocate resources
POST   /v1/resources/usage          - Report actual usage
GET    /v1/resources/pools          - Get resource pool status
GET    /v1/resources/{allocation_id} - Get allocation details
GET    /health, /ready, /metrics    - Health and metrics

Author: Web4 Infrastructure Team
License: MIT
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

sys.path.insert(0, str(Path(__file__).parent.parent / "reference"))

from resource_allocator import ResourceAllocator, ResourceType

try:
    from fastapi import FastAPI, HTTPException, Request, status
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


# =============================================================================
# Pydantic Models
# =============================================================================

class ResourceTypeEnum(str, Enum):
    CPU = "cpu"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"


class AllocateRequest(BaseModel):
    entity_id: str
    resource_type: ResourceTypeEnum
    amount: float = Field(..., gt=0)
    duration_seconds: Optional[int] = None

    class Config:
        schema_extra = {
            "example": {
                "entity_id": "lct:web4:ai:society:001",
                "resource_type": "cpu",
                "amount": 4.0,
                "duration_seconds": 3600
            }
        }


class UsageRequest(BaseModel):
    allocation_id: str
    actual_usage: float = Field(..., ge=0)


# =============================================================================
# Metrics
# =============================================================================

if METRICS_AVAILABLE:
    allocations_counter = Counter(
        'web4_resources_allocations_total',
        'Total resource allocations',
        ['resource_type', 'entity_type']
    )

    pool_utilization_gauge = Gauge(
        'web4_resources_pool_utilization',
        'Resource pool utilization',
        ['resource_type']
    )

    atp_consumed_counter = Counter(
        'web4_resources_atp_consumed_total',
        'Total ATP consumed',
        ['resource_type']
    )


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Web4 Resources Service",
    description="ATP-based resource allocation and metering",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

allocator: Optional[ResourceAllocator] = None
allocations_db: Dict[str, Dict[str, Any]] = {}
SERVICE_VERSION = "1.0.0"
SERVICE_START_TIME = datetime.now(timezone.utc)


@app.on_event("startup")
async def startup_event():
    global allocator
    society_id = "society:web4_default"
    allocator = ResourceAllocator(society_id)
    print(f"✅ Web4 Resources Service started")
    print(f"   Society: {society_id}")
    print(f"   Port: 8005")
    print(f"   Docs: http://localhost:8005/docs")


@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Web4 Resources Service shutting down")


# =============================================================================
# API Endpoints
# =============================================================================

@app.post("/v1/resources/allocate", status_code=status.HTTP_201_CREATED)
async def allocate_resources(req: AllocateRequest):
    """
    Allocate resources using ATP.

    Converts ATP to physical resources based on conversion rates:
    - 1 ATP = 100 CPU cycles
    - 1 ATP = 20 MB memory
    - 1 ATP = 100 MB storage
    - 1 ATP = 50 Kbps network

    Returns allocation ID for tracking actual usage.
    """
    try:
        # Map enum to ResourceType
        resource_map = {
            "cpu": ResourceType.CPU,
            "memory": ResourceType.MEMORY,
            "storage": ResourceType.STORAGE,
            "network": ResourceType.NETWORK
        }

        resource_type = resource_map[req.resource_type.value]

        # Allocate resources
        allocation = allocator.allocate_resources(
            entity=req.entity_id,
            resource_type=resource_type,
            amount=req.amount
        )

        # Generate allocation ID
        allocation_id = f"alloc:{uuid.uuid4().hex[:16]}"

        # Store allocation
        allocations_db[allocation_id] = {
            "allocation_id": allocation_id,
            "entity_id": req.entity_id,
            "resource_type": req.resource_type.value,
            "amount_requested": req.amount,
            "amount_allocated": allocation.get('allocated', req.amount),
            "atp_cost": allocation.get('atp_cost', 0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": req.duration_seconds,
            "actual_usage": None,
            "status": "active"
        }

        # Update metrics
        if METRICS_AVAILABLE:
            entity_type = req.entity_id.split(':')[2] if ':' in req.entity_id else 'unknown'
            allocations_counter.labels(
                resource_type=req.resource_type.value,
                entity_type=entity_type
            ).inc()

            atp_consumed_counter.labels(
                resource_type=req.resource_type.value
            ).inc(allocation.get('atp_cost', 0))

        return {
            "success": True,
            "data": allocations_db[allocation_id]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Allocation failed: {str(e)}")


@app.post("/v1/resources/usage")
async def report_usage(req: UsageRequest):
    """
    Report actual resource usage.

    Updates allocation record with actual usage for billing/refunds.
    """
    try:
        if req.allocation_id not in allocations_db:
            raise HTTPException(
                status_code=404,
                detail=f"Allocation not found: {req.allocation_id}"
            )

        allocation = allocations_db[req.allocation_id]
        allocation["actual_usage"] = req.actual_usage
        allocation["status"] = "completed"
        allocation["completed_at"] = datetime.now(timezone.utc).isoformat()

        # Calculate refund if under-utilized
        allocated = allocation["amount_allocated"]
        if req.actual_usage < allocated:
            refund_pct = (allocated - req.actual_usage) / allocated
            allocation["refund_percentage"] = refund_pct * 100

        return {
            "success": True,
            "data": allocation
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Usage report failed: {str(e)}")


@app.get("/v1/resources/pools")
async def get_pools():
    """Get resource pool status"""
    try:
        pools = allocator.get_pool_status()

        # Update metrics
        if METRICS_AVAILABLE:
            for resource_type, status in pools.items():
                utilization = status.get('utilization', 0)
                pool_utilization_gauge.labels(resource_type=resource_type).set(utilization)

        return {
            "success": True,
            "data": pools
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pool query failed: {str(e)}")


@app.get("/v1/resources/{allocation_id}")
async def get_allocation(allocation_id: str):
    """Get allocation details"""
    if allocation_id not in allocations_db:
        raise HTTPException(
            status_code=404,
            detail=f"Allocation not found: {allocation_id}"
        )

    return {
        "success": True,
        "data": allocations_db[allocation_id]
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": SERVICE_VERSION
    }


@app.get("/ready")
async def readiness_check():
    if allocator is None:
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
    host = os.getenv("WEB4_RESOURCES_HOST", "0.0.0.0")
    port = int(os.getenv("WEB4_RESOURCES_PORT", "8005"))
    workers = int(os.getenv("WEB4_RESOURCES_WORKERS", "1"))
    debug = os.getenv("WEB4_RESOURCES_DEBUG", "false").lower() == "true"

    print(f"\n🚀 Starting Web4 Resources Service")
    print(f"   Host: {host}, Port: {port}")
    print(f"   Docs: http://{host}:{port}/docs\n")

    uvicorn.run(
        "resources_service:app",
        host=host,
        port=port,
        workers=workers,
        reload=debug,
        log_level="info" if not debug else "debug"
    )


if __name__ == "__main__":
    main()
