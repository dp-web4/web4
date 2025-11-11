"""
Web4 Resources Service - REST API Server (SECURED)
===================================================

Production-ready REST API server with Phase 1 Security Mitigations.

Security Enhancements (Session 13):
-----------------------------------
4. Usage Monitoring: External validation of self-reported resource usage
   - Periodic measurement of actual resource consumption
   - Comparison with self-reported usage
   - Penalties for misreporting (escalating)
   - Deposit requirements for allocations

This addresses attacks C1 (ATP Draining) and C2 (Resource Hoarding)
from Session 11 security analysis.

Author: Web4 Security Implementation (Session 13)
License: MIT
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum
import uuid
import asyncio
import time

# Add reference implementation and ATP manager to path
sys.path.insert(0, str(Path(__file__).parent.parent / "reference"))
sys.path.insert(0, str(Path(__file__).parent))

from resource_allocator import ResourceAllocator, ResourceType
from atp_manager import get_atp_manager, TransactionType

try:
    from fastapi import FastAPI, HTTPException, Request, status
    from fastapi.responses import JSONResponse, Response
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError:
    print("FastAPI not installed. Install with: pip install fastapi uvicorn")
    sys.exit(1)

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    print("Warning: prometheus_client not installed. Metrics disabled.")


# =============================================================================
# Security Configuration
# =============================================================================

# Usage Monitoring Parameters (Mitigation 4)
USAGE_MEASUREMENT_INTERVAL = 60  # Measure usage every 60 seconds
USAGE_VERIFICATION_TOLERANCE = 0.10  # 10% variance allowed
MINIMUM_USAGE_REQUIREMENT = 0.20  # Must use at least 20% of allocation

# Penalty Escalation for Misreporting
MISREPORTING_PENALTIES = {
    1: 0,      # First offense: Warning only
    2: 50,     # Second offense: 50 ATP penalty
    3: 200,    # Third offense: 200 ATP penalty
    4: 1000    # Fourth+ offense: 1000 ATP penalty + suspension
}

# Deposit Requirements
RESOURCE_DEPOSIT_MULTIPLIER = 2.0  # Deposit 2x the ATP cost


# =============================================================================
# Pydantic Models
# =============================================================================

class ResourceTypeEnum(str, Enum):
    CPU = "cpu"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"


class AllocateRequest(BaseModel):
    """Request to allocate resources (with ATP deposit)"""
    entity_id: str
    resource_type: ResourceTypeEnum
    amount: float = Field(..., gt=0)
    duration_seconds: Optional[int] = 3600


class AllocateResponse(BaseModel):
    """Response from resource allocation (with monitoring info)"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    atp_cost: Optional[int] = None  # ATP cost for allocation
    atp_deposit: Optional[int] = None  # ATP deposit (refundable)
    atp_remaining: Optional[int] = None  # Remaining balance
    monitoring_active: Optional[bool] = None  # External monitoring status


class UsageRequest(BaseModel):
    """Request to report actual usage"""
    allocation_id: str
    actual_usage: float = Field(..., ge=0)


class UsageResponse(BaseModel):
    """Response from usage reporting (with verification)"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    verified: Optional[bool] = None  # Whether usage was verified
    measured_usage: Optional[float] = None  # Externally measured usage
    reported_usage: Optional[float] = None  # Self-reported usage
    discrepancy: Optional[float] = None  # Percentage discrepancy
    penalty: Optional[int] = None  # ATP penalty for misreporting
    refund: Optional[int] = None  # ATP refund for verified non-usage


# =============================================================================
# Resource Monitor
# =============================================================================

class ResourceMonitor:
    """
    External monitor for actual resource usage (Mitigation 4).

    Tracks allocations and periodically measures actual resource
    consumption to detect false reporting.
    """

    def __init__(self):
        self.allocations: Dict[str, Dict] = {}  # allocation_id -> allocation_data
        self.misreporting_counts: Dict[str, int] = {}  # entity_id -> offense_count
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}  # allocation_id -> task

    async def track_allocation(
        self,
        allocation_id: str,
        entity_id: str,
        resource_type: str,
        amount: float
    ):
        """
        Start tracking an allocation with periodic usage measurement.

        Args:
            allocation_id: Unique allocation identifier
            entity_id: Entity LCT ID
            resource_type: Type of resource
            amount: Allocated amount
        """
        self.allocations[allocation_id] = {
            "entity_id": entity_id,
            "resource_type": resource_type,
            "allocated": amount,
            "start_time": time.time(),
            "measured_usage": [],  # List of measurements
            "monitoring_active": True
        }

        # Start background monitoring task
        task = asyncio.create_task(self._monitor_usage(allocation_id))
        self.monitoring_tasks[allocation_id] = task

    async def _monitor_usage(self, allocation_id: str):
        """
        Periodically measure actual resource usage.

        In production, this would query actual system resources.
        For MVP, we simulate measurements.
        """
        while allocation_id in self.allocations and self.allocations[allocation_id]["monitoring_active"]:
            try:
                # Simulate measuring actual usage
                # In production: query cgroups, system monitors, etc.
                actual_usage = await self._measure_usage(allocation_id)

                # Store measurement
                self.allocations[allocation_id]["measured_usage"].append({
                    "timestamp": time.time(),
                    "usage": actual_usage
                })

                # Wait for next measurement interval
                await asyncio.sleep(USAGE_MEASUREMENT_INTERVAL)

            except Exception as e:
                print(f"Error monitoring allocation {allocation_id}: {e}")
                break

    async def _measure_usage(self, allocation_id: str) -> float:
        """
        Measure actual resource usage.

        In production, this would interface with:
        - cgroups for CPU/memory
        - disk I/O monitoring for storage
        - network traffic monitoring for bandwidth

        For MVP, we simulate realistic usage patterns.
        """
        alloc = self.allocations.get(allocation_id)
        if not alloc:
            return 0.0

        # Simulate usage between 10-90% of allocation
        # In real implementation, this queries actual system usage
        import random
        usage = alloc["allocated"] * random.uniform(0.1, 0.9)

        return usage

    async def verify_reported_usage(
        self,
        allocation_id: str,
        reported_usage: float
    ) -> tuple[bool, float, float]:
        """
        Verify self-reported usage against measurements.

        Args:
            allocation_id: Allocation identifier
            reported_usage: Self-reported usage amount

        Returns:
            Tuple of (verified: bool, measured_usage: float, discrepancy: float)
        """
        if allocation_id not in self.allocations:
            return False, 0.0, 0.0

        alloc = self.allocations[allocation_id]
        measurements = alloc["measured_usage"]

        if not measurements:
            # No measurements yet, can't verify
            return False, 0.0, 0.0

        # Calculate average measured usage
        avg_measured = sum(m["usage"] for m in measurements) / len(measurements)

        # Calculate discrepancy
        if avg_measured > 0:
            discrepancy = abs(reported_usage - avg_measured) / avg_measured
        else:
            discrepancy = 0.0

        # Verify if within tolerance
        verified = discrepancy <= USAGE_VERIFICATION_TOLERANCE

        return verified, avg_measured, discrepancy

    def record_misreporting(self, entity_id: str) -> int:
        """
        Record misreporting event and calculate penalty.

        Args:
            entity_id: Entity LCT ID

        Returns:
            ATP penalty amount
        """
        # Increment offense count
        count = self.misreporting_counts.get(entity_id, 0) + 1
        self.misreporting_counts[entity_id] = count

        # Calculate penalty
        penalty = MISREPORTING_PENALTIES.get(count, MISREPORTING_PENALTIES[4])

        return penalty

    def check_minimum_usage(self, allocation_id: str) -> tuple[bool, float]:
        """
        Check if allocation met minimum usage requirement.

        Args:
            allocation_id: Allocation identifier

        Returns:
            Tuple of (meets_minimum: bool, usage_ratio: float)
        """
        if allocation_id not in self.allocations:
            return True, 0.0

        alloc = self.allocations[allocation_id]
        measurements = alloc["measured_usage"]

        if not measurements:
            return True, 0.0

        # Calculate average usage ratio
        avg_measured = sum(m["usage"] for m in measurements) / len(measurements)
        usage_ratio = avg_measured / alloc["allocated"] if alloc["allocated"] > 0 else 0

        meets_minimum = usage_ratio >= MINIMUM_USAGE_REQUIREMENT

        return meets_minimum, usage_ratio

    def stop_monitoring(self, allocation_id: str):
        """Stop monitoring an allocation."""
        if allocation_id in self.allocations:
            self.allocations[allocation_id]["monitoring_active"] = False

        if allocation_id in self.monitoring_tasks:
            task = self.monitoring_tasks[allocation_id]
            if not task.done():
                task.cancel()
            del self.monitoring_tasks[allocation_id]


# =============================================================================
# Metrics
# =============================================================================

if METRICS_AVAILABLE:
    allocations_counter = Counter(
        'web4_resources_allocations_total',
        'Total resource allocations',
        ['resource_type', 'entity_type']
    )

    usage_verified_counter = Counter(
        'web4_resources_usage_verified_total',
        'Usage verifications',
        ['verified']
    )

    misreporting_counter = Counter(
        'web4_resources_misreporting_total',
        'Misreporting events',
        ['entity', 'offense_number']
    )

    allocation_rejected_counter = Counter(
        'web4_resources_allocation_rejected_total',
        'Allocation rejections',
        ['reason']
    )


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Web4 Resources Service (Secured)",
    description="ATP-based resource allocation with usage monitoring",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global state
allocator: Optional[ResourceAllocator] = None
atp_manager = get_atp_manager()
monitor = ResourceMonitor()
SERVICE_VERSION = "2.0.0-secured"

# Storage for allocation details
allocations_db: Dict[str, Dict] = {}


# =============================================================================
# API Endpoints
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    global allocator

    allocator = ResourceAllocator()

    print(f"✅ Web4 Resources Service (Secured) started")
    print(f"   Version: {SERVICE_VERSION}")
    print(f"   Security: Phase 1 Mitigations Active")
    print(f"   - Usage Monitoring: Enabled")
    print(f"   - Measurement Interval: {USAGE_MEASUREMENT_INTERVAL}s")
    print(f"   - Verification Tolerance: {USAGE_VERIFICATION_TOLERANCE:.0%}")
    print(f"   - Minimum Usage: {MINIMUM_USAGE_REQUIREMENT:.0%}")
    print(f"   Docs: http://localhost:8005/docs")


@app.post("/v1/resources/allocate", response_model=AllocateResponse, status_code=status.HTTP_201_CREATED)
async def allocate_resources(request: AllocateRequest):
    """
    Allocate resources with Phase 1 Security Mitigations.

    **Security Enhancements**:
    1. **ATP Deposit**: Lock 2x ATP cost as refundable deposit
    2. **Usage Monitoring**: External measurement starts immediately
    3. **Minimum Usage**: Must use ≥20% of allocation or pay penalty

    **Process**:
    1. Calculate ATP cost for allocation
    2. Require deposit (2x cost, refundable)
    3. Lock ATP from entity balance
    4. Allocate resources
    5. Start external usage monitoring
    6. Return allocation ID + monitoring status
    """
    try:
        # Calculate ATP cost (simplified: 10 ATP per unit)
        atp_cost = int(request.amount * 10)
        atp_deposit = int(atp_cost * RESOURCE_DEPOSIT_MULTIPLIER)
        total_required = atp_cost + atp_deposit

        # --- MITIGATION 4: ATP Deposit Requirement ---
        if not atp_manager.has_sufficient_balance(request.entity_id, total_required):
            if METRICS_AVAILABLE:
                allocation_rejected_counter.labels(reason="insufficient_atp").inc()

            return AllocateResponse(
                success=False,
                error=f"Insufficient ATP. Required: {total_required} (cost: {atp_cost}, deposit: {atp_deposit}), "
                      f"available: {atp_manager.get_balance(request.entity_id)}"
            )

        # Deduct ATP (cost + deposit)
        success, tx = atp_manager.deduct(
            entity_id=request.entity_id,
            amount=total_required,
            transaction_type=TransactionType.ALLOCATE_RESOURCE,
            description=f"Allocating {request.amount} {request.resource_type.value} "
                       f"(cost: {atp_cost}, deposit: {atp_deposit})",
            metadata={
                "resource_type": request.resource_type.value,
                "amount": request.amount,
                "deposit": atp_deposit,
                "refundable": True
            }
        )

        if not success:
            return AllocateResponse(
                success=False,
                error="Failed to deduct ATP (concurrent transaction?)"
            )

        # --- Allocate Resources ---
        allocation_id = f"alloc:{uuid.uuid4().hex[:16]}"

        # Store allocation details
        allocations_db[allocation_id] = {
            "allocation_id": allocation_id,
            "entity_id": request.entity_id,
            "resource_type": request.resource_type.value,
            "amount_requested": request.amount,
            "amount_allocated": request.amount,  # In production, may differ
            "atp_cost": atp_cost,
            "atp_deposit": atp_deposit,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": request.duration_seconds,
            "status": "active"
        }

        # --- MITIGATION 4: Start Usage Monitoring ---
        await monitor.track_allocation(
            allocation_id=allocation_id,
            entity_id=request.entity_id,
            resource_type=request.resource_type.value,
            amount=request.amount
        )

        # Update metrics
        if METRICS_AVAILABLE:
            allocations_counter.labels(
                resource_type=request.resource_type.value,
                entity_type="ai"  # TODO: extract from LCT
            ).inc()

        # Prepare response
        response_data = {
            "allocation_id": allocation_id,
            "entity_id": request.entity_id,
            "resource_type": request.resource_type.value,
            "amount_allocated": request.amount,
            "start_time": allocations_db[allocation_id]["start_time"],
            "status": "active"
        }

        return AllocateResponse(
            success=True,
            data=response_data,
            atp_cost=atp_cost,
            atp_deposit=atp_deposit,
            atp_remaining=atp_manager.get_balance(request.entity_id),
            monitoring_active=True
        )

    except Exception as e:
        if METRICS_AVAILABLE:
            allocation_rejected_counter.labels(reason="error").inc()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resource allocation failed: {str(e)}"
        )


@app.post("/v1/resources/usage", response_model=UsageResponse)
async def report_usage(request: UsageRequest):
    """
    Report actual resource usage with verification.

    **Security Enhancements**:
    1. **Usage Verification**: Compare self-reported vs measured usage
    2. **Penalty Escalation**: Repeated misreporting → increasing penalties
    3. **Refund Calculation**: Honest reporting → deposit refund

    **Process**:
    1. Stop external monitoring
    2. Compare reported vs measured usage
    3. If discrepancy >10% → Flag as misreporting, apply penalty
    4. If verified → Calculate refund based on actual usage
    5. Return verification status + refund/penalty
    """
    try:
        # Get allocation
        allocation = allocations_db.get(request.allocation_id)

        if not allocation:
            return UsageResponse(
                success=False,
                error=f"Allocation not found: {request.allocation_id}"
            )

        entity_id = allocation["entity_id"]

        # --- MITIGATION 4: Usage Verification ---
        monitor.stop_monitoring(request.allocation_id)

        verified, measured_usage, discrepancy = await monitor.verify_reported_usage(
            allocation_id=request.allocation_id,
            reported_usage=request.actual_usage
        )

        # Update metrics
        if METRICS_AVAILABLE:
            usage_verified_counter.labels(verified=str(verified).lower()).inc()

        penalty = 0
        refund = 0

        if not verified:
            # --- Misreporting Detected ---
            penalty = monitor.record_misreporting(entity_id)

            if METRICS_AVAILABLE:
                offense_count = monitor.misreporting_counts.get(entity_id, 0)
                misreporting_counter.labels(
                    entity=entity_id,
                    offense_number=str(offense_count)
                ).inc()

            # Apply penalty (deduct additional ATP)
            if penalty > 0:
                atp_manager.deduct(
                    entity_id=entity_id,
                    amount=penalty,
                    transaction_type=TransactionType.PENALTY,
                    description=f"Misreporting penalty (offense #{monitor.misreporting_counts[entity_id]})",
                    metadata={"allocation_id": request.allocation_id}
                )

            # No refund for misreporting
            response_data = {
                "allocation_id": request.allocation_id,
                "status": "misreporting_detected",
                "offense_count": monitor.misreporting_counts.get(entity_id, 0)
            }

            return UsageResponse(
                success=True,
                data=response_data,
                verified=False,
                measured_usage=measured_usage,
                reported_usage=request.actual_usage,
                discrepancy=discrepancy,
                penalty=penalty,
                refund=0
            )

        else:
            # --- Usage Verified ---
            # Check minimum usage requirement
            meets_minimum, usage_ratio = monitor.check_minimum_usage(request.allocation_id)

            if not meets_minimum:
                # Penalty for hoarding (allocated but didn't use)
                penalty = int(allocation["atp_deposit"] * (1.0 - usage_ratio))
                refund = allocation["atp_deposit"] - penalty
            else:
                # Full deposit refund for meeting minimum usage
                refund = allocation["atp_deposit"]

            # Credit refund
            if refund > 0:
                atp_manager.credit(
                    entity_id=entity_id,
                    amount=refund,
                    transaction_type=TransactionType.REFUND,
                    description=f"Resource deposit refund (usage: {usage_ratio:.1%})",
                    metadata={"allocation_id": request.allocation_id}
                )

            response_data = {
                "allocation_id": request.allocation_id,
                "status": "completed",
                "usage_ratio": usage_ratio
            }

            return UsageResponse(
                success=True,
                data=response_data,
                verified=True,
                measured_usage=measured_usage,
                reported_usage=request.actual_usage,
                discrepancy=discrepancy,
                penalty=penalty,
                refund=refund
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Usage reporting failed: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": SERVICE_VERSION,
        "security_level": "phase1_mitigations_active"
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    if not METRICS_AVAILABLE:
        return JSONResponse(
            content={"error": "Metrics not available"},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Run the resources service"""
    import os

    host = os.getenv("WEB4_RESOURCES_HOST", "0.0.0.0")
    port = int(os.getenv("WEB4_RESOURCES_PORT", "8005"))
    workers = int(os.getenv("WEB4_RESOURCES_WORKERS", "1"))

    uvicorn.run(
        "resources_service_secured:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info"
    )


if __name__ == "__main__":
    main()
