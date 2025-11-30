"""
Web4 Authorization Service - REST API Server
============================================

Research prototype REST API server for the Web4 Authorization Service.

This service provides:
- Action authorization with LCT verification
- Law compliance checking
- Delegation chain validation
- ATP budget tracking
- Request authentication

Based on the Authorization Engine implementation from Session 01.

API Endpoints:
--------------
POST   /v1/auth/authorize    - Authorize an action
GET    /v1/delegation/{id}   - Get delegation details
POST   /v1/delegation/create - Create delegation (TODO)
GET    /health               - Health check
GET    /ready                - Readiness check
GET    /metrics              - Prometheus metrics

Authentication:
--------------
All requests require:
- Authorization: Bearer {lct_id}
- X-Signature: {ed25519_signature_hex}
- X-Nonce: {monotonic_nonce}

Author: Web4 Infrastructure Team
License: MIT
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json

# Add reference implementation to path
sys.path.insert(0, str(Path(__file__).parent.parent / "reference"))

from authorization_engine import (
    AuthorizationEngine,
    AuthorizationRequest,
    AgentDelegation
)
from lct_registry import LCTRegistry

try:
    from fastapi import FastAPI, HTTPException, Request, status, Depends, Header
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

class ActionEnum(str, Enum):
    """Standard Web4 actions"""
    READ = "read"
    WRITE = "write"
    COMPUTE = "compute"
    QUERY = "query"
    DELEGATE = "delegate"
    ALLOCATE = "allocate"


class AuthorizeRequest(BaseModel):
    """Request to authorize an action"""
    action: ActionEnum
    resource: str = Field(..., min_length=1)
    atp_cost: int = Field(..., ge=0)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        schema_extra = {
            "example": {
                "action": "compute",
                "resource": "model:training:gpt-5",
                "atp_cost": 500,
                "context": {
                    "delegation_id": "deleg:supervisor:001",
                    "witnesses": ["human:supervisor:alice"]
                }
            }
        }


class AuthorizeResponse(BaseModel):
    """Response from authorization"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# =============================================================================
# Metrics
# =============================================================================

if METRICS_AVAILABLE:
    auth_requests_counter = Counter(
        'web4_auth_requests_total',
        'Total authorization requests',
        ['decision', 'action']
    )

    auth_latency = Histogram(
        'web4_auth_latency_seconds',
        'Authorization request latency',
        ['action']
    )

    atp_budget_gauge = Gauge(
        'web4_auth_atp_budget_remaining',
        'ATP budget remaining',
        ['entity', 'role']
    )


# =============================================================================
# Authentication Helpers
# =============================================================================

class AuthenticationError(Exception):
    """Authentication failed"""
    pass


def verify_request_signature(
    lct_id: str,
    method: str,
    path: str,
    nonce: int,
    signature: str,
    body: Optional[Dict] = None
) -> bool:
    """
    Verify request signature.

    TODO: Integrate with LCT Registry to get public key and verify.
    For now, this is a stub that returns True.
    """
    # In production, this would:
    # 1. Get public key from LCT Registry
    # 2. Reconstruct signature payload
    # 3. Verify Ed25519 signature
    # 4. Check nonce monotonicity

    # Stub implementation
    return True


async def authenticate_request(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_signature: Optional[str] = Header(None),
    x_nonce: Optional[str] = Header(None)
) -> str:
    """
    Authenticate request and return LCT ID.

    Verifies:
    - Bearer token is present and valid LCT format
    - Signature is present and valid
    - Nonce is present and fresh

    Returns:
        LCT ID if authentication succeeds

    Raises:
        HTTPException: If authentication fails
    """
    # Check Authorization header
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format (expected: Bearer {lct_id})"
        )

    lct_id = authorization[7:]  # Remove "Bearer " prefix

    # Validate LCT ID format
    if not lct_id.startswith("lct:web4:"):
        raise HTTPException(
            status_code=401,
            detail="Invalid LCT ID format"
        )

    # Check signature
    if not x_signature:
        raise HTTPException(
            status_code=401,
            detail="Missing X-Signature header"
        )

    # Check nonce
    if not x_nonce:
        raise HTTPException(
            status_code=401,
            detail="Missing X-Nonce header"
        )

    try:
        nonce = int(x_nonce)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid nonce format (must be integer)"
        )

    # Verify signature
    # TODO: Get request body and verify signature
    # For now, we trust the signature
    is_valid = verify_request_signature(
        lct_id=lct_id,
        method=request.method,
        path=str(request.url.path),
        nonce=nonce,
        signature=x_signature,
        body=None  # TODO: Get body
    )

    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid signature"
        )

    return lct_id


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Web4 Authorization Service",
    description="Action authorization with LCT verification and law compliance",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global state
auth_engine: Optional[AuthorizationEngine] = None
lct_registry: Optional[LCTRegistry] = None
SERVICE_VERSION = "1.0.0"
SERVICE_START_TIME = datetime.now(timezone.utc)


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    global auth_engine, lct_registry

    # In production, these would come from config
    society_id = "society:web4_default"
    law_oracle_lct = "lct:web4:oracle:law:default:1"

    # Initialize components
    lct_registry = LCTRegistry(society_id)
    auth_engine = AuthorizationEngine(society_id, law_oracle_lct)

    print(f"✅ Web4 Authorization Service started")
    print(f"   Society: {society_id}")
    print(f"   Law Oracle: {law_oracle_lct}")
    print(f"   Version: {SERVICE_VERSION}")
    print(f"   Docs: http://localhost:8003/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Web4 Authorization Service shutting down")


# =============================================================================
# API Endpoints
# =============================================================================

@app.post("/v1/auth/authorize", response_model=AuthorizeResponse)
async def authorize_action(
    req: AuthorizeRequest,
    lct_id: str = Depends(authenticate_request)
):
    """
    Authorize an action for an entity.

    Verifies:
    1. LCT signature (via authentication)
    2. Law compliance (action is legal for role)
    3. Delegation chain (if applicable)
    4. ATP budget (sufficient budget remaining)

    Returns authorization decision with metadata:
    - decision: "granted" or "denied"
    - atp_remaining: ATP budget after this action
    - law_version: Law dataset version used
    - law_hash: Hash of law dataset
    - ledger_ref: Reference to ledger transaction (TODO)

    **Authentication Required**:
    - Authorization: Bearer {lct_id}
    - X-Signature: {ed25519_signature}
    - X-Nonce: {nonce}
    """
    try:
        # Create authorization request
        auth_request = AuthorizationRequest(
            requester_lct=lct_id,
            action=req.action.value,
            resource=req.resource,
            atp_cost=req.atp_cost,
            delegation_id=req.context.get("delegation_id"),
            witnesses=req.context.get("witnesses", []),
            request_id=f"req:{datetime.now(timezone.utc).timestamp()}",
            timestamp=datetime.now(timezone.utc)
        )

        # TODO: Add signature from request
        auth_request.signature = "stub_signature"

        # Authorize
        start_time = datetime.now(timezone.utc)
        decision = auth_engine.authorize(auth_request)
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

        # Update metrics
        if METRICS_AVAILABLE:
            auth_requests_counter.labels(
                decision=decision,
                action=req.action.value
            ).inc()

            auth_latency.labels(action=req.action.value).observe(duration)

        # Get ATP budget remaining (stub)
        atp_remaining = 5000 if decision == "granted" else 0

        return AuthorizeResponse(
            success=True,
            data={
                "decision": decision,
                "atp_remaining": atp_remaining,
                "resource_allocation": {
                    "cpu_cores": 2.0 if req.action == ActionEnum.COMPUTE else 0.0,
                    "memory_gb": 8.0 if req.action == ActionEnum.COMPUTE else 0.0,
                    "storage_gb": 50.0 if req.action == ActionEnum.WRITE else 0.0
                } if decision == "granted" else None
            },
            metadata={
                "law_version": "v1.0.0",
                "law_hash": "sha256:stub123...",
                "ledger_ref": None,  # TODO: Implement
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "duration_ms": duration * 1000
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/v1/delegation/{delegation_id}")
async def get_delegation(
    delegation_id: str,
    lct_id: str = Depends(authenticate_request)
):
    """
    Get delegation details.

    Returns information about a delegation including:
    - Delegator (human/org)
    - Delegate (AI agent)
    - Role and permissions
    - ATP budget
    - Expiry time
    - Status

    **TODO**: Implement delegation storage and retrieval
    """
    # Stub response
    return {
        "success": True,
        "data": {
            "delegation_id": delegation_id,
            "delegator": "lct:web4:human:research:alice",
            "delegate": lct_id,
            "role": "research_assistant",
            "permissions": ["read", "write", "compute"],
            "atp_budget": 5000,
            "atp_remaining": 4500,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": None,
            "status": "active"
        }
    }


@app.post("/v1/delegation/create")
async def create_delegation(lct_id: str = Depends(authenticate_request)):
    """
    Create a new delegation.

    **TODO**: Implement delegation creation with:
    - Role assignment
    - Permission specification
    - ATP budget allocation
    - Expiry time
    - Ledger recording
    """
    raise HTTPException(
        status_code=501,
        detail="Delegation creation not yet implemented"
    )


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
    if auth_engine is None or lct_registry is None:
        raise HTTPException(
            status_code=503,
            detail="Service not ready: Components not initialized"
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
# Error Handlers
# =============================================================================

@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc: HTTPException):
    """Custom 401 handler"""
    return JSONResponse(
        status_code=401,
        content={
            "success": False,
            "error": "Authentication failed",
            "details": exc.detail
        }
    )


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc: HTTPException):
    """Custom 403 handler"""
    return JSONResponse(
        status_code=403,
        content={
            "success": False,
            "error": "Authorization denied",
            "details": exc.detail
        }
    )


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """
    Run the Authorization Service.

    Configuration via environment variables:
    - WEB4_AUTH_HOST: Host to bind (default: 0.0.0.0)
    - WEB4_AUTH_PORT: Port to listen (default: 8003)
    - WEB4_AUTH_WORKERS: Number of workers (default: 1)
    - WEB4_AUTH_DEBUG: Debug mode (default: False)
    """
    import os

    host = os.getenv("WEB4_AUTH_HOST", "0.0.0.0")
    port = int(os.getenv("WEB4_AUTH_PORT", "8003"))
    workers = int(os.getenv("WEB4_AUTH_WORKERS", "1"))
    debug = os.getenv("WEB4_AUTH_DEBUG", "false").lower() == "true"

    print(f"\n🚀 Starting Web4 Authorization Service")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Workers: {workers}")
    print(f"   Debug: {debug}")
    print(f"   Docs: http://{host}:{port}/docs\n")

    uvicorn.run(
        "authorization_service:app",
        host=host,
        port=port,
        workers=workers,
        reload=debug,
        log_level="info" if not debug else "debug"
    )


if __name__ == "__main__":
    main()
