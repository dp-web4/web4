"""
Web4 Identity Service - REST API Server
=======================================

Research prototype REST API server for the Web4 Identity Service (LCT Registry).

This service provides:
- LCT minting (creating new identities)
- LCT lookup and verification
- Birth certificate retrieval
- Signature verification
- Entity status management

Based on the LCT Registry implementation from Session 03.

API Endpoints:
--------------
POST   /v1/lct/mint          - Mint new LCT
GET    /v1/lct/{lct_id}      - Get LCT information
POST   /v1/lct/{lct_id}/verify - Verify LCT signature
GET    /v1/lct/{lct_id}/birthcert - Get birth certificate
POST   /v1/lct/{lct_id}/revoke - Revoke LCT (admin only)
GET    /health               - Health check
GET    /ready                - Readiness check
GET    /metrics              - Prometheus metrics

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

from lct_registry import LCTRegistry, EntityType, LCTCredential

try:
    from fastapi import FastAPI, HTTPException, Request, status
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError:
    print("FastAPI not installed. Install with: pip install fastapi uvicorn")
    sys.exit(1)

try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    print("Warning: prometheus_client not installed. Metrics disabled.")


# =============================================================================
# Pydantic Models (Request/Response Schemas)
# =============================================================================

class EntityTypeEnum(str, Enum):
    """Entity types for LCT minting"""
    HUMAN = "human"
    AI = "ai"
    ORG = "org"
    DEVICE = "device"


class MintLCTRequest(BaseModel):
    """Request to mint a new LCT"""
    entity_type: EntityTypeEnum
    entity_identifier: str = Field(..., min_length=1, max_length=200)
    society: Optional[str] = None
    witnesses: List[str] = Field(default_factory=list)
    parent_org: Optional[str] = None  # For devices
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "entity_type": "ai",
                "entity_identifier": "research_agent_001",
                "society": "ai_research_lab",
                "witnesses": ["witness:hr_dept", "witness:ai_safety"],
                "metadata": {"version": "1.0", "model": "claude-3"}
            }
        }


class MintLCTResponse(BaseModel):
    """Response from minting LCT"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class LCTInfoResponse(BaseModel):
    """LCT information response"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class VerifySignatureRequest(BaseModel):
    """Request to verify signature"""
    message: str = Field(..., description="Hex-encoded message")
    signature: str = Field(..., description="Hex-encoded signature")

    class Config:
        schema_extra = {
            "example": {
                "message": "48656c6c6f20576f726c64",  # "Hello World" in hex
                "signature": "abcdef1234567890..."
            }
        }


class VerifySignatureResponse(BaseModel):
    """Signature verification response"""
    success: bool
    data: Optional[Dict[str, bool]] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str


# =============================================================================
# Metrics (Prometheus)
# =============================================================================

if METRICS_AVAILABLE:
    lct_minted_counter = Counter(
        'web4_identity_lct_minted_total',
        'Total LCTs minted',
        ['entity_type', 'society']
    )

    lct_lookup_counter = Counter(
        'web4_identity_lct_lookup_total',
        'Total LCT lookups',
        ['found']
    )

    signature_verify_counter = Counter(
        'web4_identity_signature_verify_total',
        'Total signature verifications',
        ['valid']
    )

    request_duration = Histogram(
        'web4_identity_request_duration_seconds',
        'Request duration in seconds',
        ['endpoint', 'method']
    )


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Web4 Identity Service",
    description="LCT Registry REST API for Web4 infrastructure",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global state
registry: Optional[LCTRegistry] = None
SERVICE_VERSION = "1.0.0"
SERVICE_START_TIME = datetime.now(timezone.utc)


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    global registry

    # In production, society_id would come from config
    society_id = "society:web4_default"

    registry = LCTRegistry(society_id)

    print(f"✅ Web4 Identity Service started")
    print(f"   Society: {society_id}")
    print(f"   Version: {SERVICE_VERSION}")
    print(f"   Docs: http://localhost:8001/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Web4 Identity Service shutting down")


# =============================================================================
# API Endpoints
# =============================================================================

@app.post("/v1/lct/mint", response_model=MintLCTResponse, status_code=status.HTTP_201_CREATED)
async def mint_lct(request: MintLCTRequest):
    """
    Mint a new LCT (Lightweight Coordination Token).

    Creates a new cryptographic identity with Ed25519 keypair,
    birth certificate, and witness attestations.

    **Entity Types**:
    - `human`: Human individuals (requires 3+ witnesses)
    - `ai`: AI agents and systems (requires 1+ witness)
    - `org`: Organizations and DAOs (requires 3+ witnesses)
    - `device`: IoT devices (requires parent_org)

    **Returns**:
    - LCT ID (format: lct:web4:{type}:{society}:{id})
    - Public key (hex)
    - Birth certificate hash
    - Private key (hex) - **SECURE THIS**
    """
    try:
        # Map string to EntityType enum
        entity_type_map = {
            "human": EntityType.HUMAN,
            "ai": EntityType.AI,
            "org": EntityType.ORG,
            "device": EntityType.DEVICE
        }

        entity_type = entity_type_map[request.entity_type.value]

        # Mint LCT
        lct, private_key = registry.mint_lct(
            entity_type=entity_type,
            entity_identifier=request.entity_identifier,
            witnesses=request.witnesses,
            parent_org=request.parent_org
        )

        # Update metrics
        if METRICS_AVAILABLE:
            society = request.society or "default"
            lct_minted_counter.labels(
                entity_type=request.entity_type.value,
                society=society
            ).inc()

        return MintLCTResponse(
            success=True,
            data={
                "lct_id": lct.lct_id,
                "entity_type": lct.entity_type,
                "entity_identifier": lct.entity_identifier,
                "society": lct.society,
                "public_key": lct.public_key.hex(),
                "private_key": private_key.hex(),  # ⚠️ Secure this!
                "birth_certificate": {
                    "certificate_hash": lct.birth_certificate.certificate_hash,
                    "witnesses": lct.birth_certificate.witnesses,
                    "creation_time": lct.birth_certificate.creation_time.isoformat()
                },
                "created_at": lct.created_at.isoformat(),
                "status": "active"
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/v1/lct/{lct_id}", response_model=LCTInfoResponse)
async def get_lct_info(lct_id: str):
    """
    Get LCT information.

    Retrieves the public information for an LCT including:
    - Entity type and identifier
    - Society membership
    - Public key
    - Birth certificate details
    - Current status

    **Note**: Private key is never returned by this endpoint.
    """
    try:
        # Lookup LCT
        lct = registry.get_lct(lct_id)

        if not lct:
            # Update metrics
            if METRICS_AVAILABLE:
                lct_lookup_counter.labels(found="false").inc()

            raise HTTPException(
                status_code=404,
                detail=f"LCT not found: {lct_id}"
            )

        # Update metrics
        if METRICS_AVAILABLE:
            lct_lookup_counter.labels(found="true").inc()

        return LCTInfoResponse(
            success=True,
            data={
                "lct_id": lct.lct_id,
                "entity_type": lct.entity_type,
                "entity_identifier": lct.entity_identifier,
                "society": lct.society,
                "public_key": lct.public_key.hex(),
                "birth_certificate": {
                    "certificate_hash": lct.birth_certificate.certificate_hash,
                    "witnesses": lct.birth_certificate.witnesses,
                    "creation_time": lct.birth_certificate.creation_time.isoformat()
                },
                "created_at": lct.created_at.isoformat(),
                "status": "active"  # TODO: Implement status tracking
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/v1/lct/{lct_id}/verify", response_model=VerifySignatureResponse)
async def verify_signature(lct_id: str, request: VerifySignatureRequest):
    """
    Verify a signature from an LCT.

    Verifies that a message was signed by the private key
    corresponding to the LCT's public key.

    **Parameters**:
    - `message`: Hex-encoded message bytes
    - `signature`: Hex-encoded signature bytes

    **Returns**:
    - `valid`: True if signature is valid, False otherwise
    """
    try:
        # Lookup LCT
        lct = registry.get_lct(lct_id)

        if not lct:
            raise HTTPException(
                status_code=404,
                detail=f"LCT not found: {lct_id}"
            )

        # Decode hex
        try:
            message_bytes = bytes.fromhex(request.message)
            signature_bytes = bytes.fromhex(request.signature)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid hex encoding: {str(e)}"
            )

        # Verify signature
        is_valid = registry.verify_signature(
            lct_id=lct_id,
            message=message_bytes,
            signature=signature_bytes
        )

        # Update metrics
        if METRICS_AVAILABLE:
            signature_verify_counter.labels(
                valid="true" if is_valid else "false"
            ).inc()

        return VerifySignatureResponse(
            success=True,
            data={"valid": is_valid}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/v1/lct/{lct_id}/birthcert")
async def get_birth_certificate(lct_id: str):
    """
    Get birth certificate for an LCT.

    Returns the complete birth certificate including:
    - Certificate hash
    - Witness attestations
    - Creation timestamp
    - Metadata
    """
    try:
        lct = registry.get_lct(lct_id)

        if not lct:
            raise HTTPException(
                status_code=404,
                detail=f"LCT not found: {lct_id}"
            )

        return {
            "success": True,
            "data": {
                "lct_id": lct.lct_id,
                "certificate_hash": lct.birth_certificate.certificate_hash,
                "witnesses": lct.birth_certificate.witnesses,
                "creation_time": lct.birth_certificate.creation_time.isoformat(),
                "entity_type": lct.entity_type,
                "entity_identifier": lct.entity_identifier,
                "society": lct.society
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/v1/lct/{lct_id}/revoke")
async def revoke_lct(lct_id: str):
    """
    Revoke an LCT.

    **⚠️ TODO**: Implement proper revocation with:
    - Authorization checks (admin only)
    - Ledger recording
    - Revocation propagation
    - Grace period handling

    Currently returns not implemented.
    """
    raise HTTPException(
        status_code=501,
        detail="LCT revocation not yet implemented"
    )


# =============================================================================
# Health and Metrics Endpoints
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns service health status. Used by load balancers
    and Kubernetes liveness probes.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=SERVICE_VERSION
    )


@app.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.

    Returns service readiness. Used by Kubernetes readiness probes.
    Service is ready when:
    - Registry is initialized
    - Can mint and lookup LCTs
    """
    if registry is None:
        raise HTTPException(
            status_code=503,
            detail="Service not ready: Registry not initialized"
        )

    return {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": (datetime.now(timezone.utc) - SERVICE_START_TIME).total_seconds()
    }


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.

    Exposes Prometheus-compatible metrics for monitoring:
    - LCT minting rate
    - Lookup rate
    - Signature verification rate
    - Request durations
    """
    if not METRICS_AVAILABLE:
        return JSONResponse(
            content={"error": "Metrics not available (prometheus_client not installed)"},
            status_code=501
        )

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# =============================================================================
# Error Handlers
# =============================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": exc.detail,
            "path": str(request.url)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Custom 500 handler"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "details": str(exc) if app.debug else None
        }
    )


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """
    Run the Identity Service.

    Configuration via environment variables:
    - WEB4_IDENTITY_HOST: Host to bind (default: 0.0.0.0)
    - WEB4_IDENTITY_PORT: Port to listen (default: 8001)
    - WEB4_IDENTITY_WORKERS: Number of workers (default: 1)
    - WEB4_IDENTITY_DEBUG: Debug mode (default: False)
    """
    import os

    host = os.getenv("WEB4_IDENTITY_HOST", "0.0.0.0")
    port = int(os.getenv("WEB4_IDENTITY_PORT", "8001"))
    workers = int(os.getenv("WEB4_IDENTITY_WORKERS", "1"))
    debug = os.getenv("WEB4_IDENTITY_DEBUG", "false").lower() == "true"

    print(f"\n🚀 Starting Web4 Identity Service")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Workers: {workers}")
    print(f"   Debug: {debug}")
    print(f"   Docs: http://{host}:{port}/docs\n")

    uvicorn.run(
        "identity_service:app",
        host=host,
        port=port,
        workers=workers,
        reload=debug,
        log_level="info" if not debug else "debug"
    )


if __name__ == "__main__":
    main()
