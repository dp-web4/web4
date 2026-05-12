"""
Web4 Resource Allocator
=======================

Maps ATP (energy tokens) to actual compute, storage, and network resources.
Integrates with authorization engine to enforce resource budgets and track consumption.

Key Concepts:
- ATP tokens represent abstract "energy" for work
- Resources are concrete: CPU cycles, memory bytes, storage bytes, network bandwidth
- Conversion rates map ATP to resources (dynamic or static)
- Metering tracks actual resource consumption
- Accounting reconciles ATP cost vs actual usage
- Anti-exhaustion protections prevent resource drain attacks

Design Philosophy:
- ATP is the universal currency, resources are specific goods
- Conversion rates reflect resource scarcity and demand
- Over-budget actions are denied (fail-safe)
- Under-budget actions charge actual cost (fair)
- Resource pools prevent single-entity exhaustion
- Metering is fine-grained but efficient
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import time
import math


class ResourceType(Enum):
    """Types of resources that can be allocated"""
    CPU_CYCLES = "cpu_cycles"  # Compute time
    MEMORY_BYTES = "memory_bytes"  # RAM allocation
    STORAGE_BYTES = "storage_bytes"  # Persistent storage
    NETWORK_BYTES = "network_bytes"  # Bandwidth
    GPU_SECONDS = "gpu_seconds"  # GPU compute time


@dataclass
class ResourceQuota:
    """Resource limits and consumption"""
    cpu_cycles: int = 0
    memory_bytes: int = 0
    storage_bytes: int = 0
    network_bytes: int = 0
    gpu_seconds: int = 0

    def __add__(self, other):
        """Add quotas"""
        return ResourceQuota(
            cpu_cycles=self.cpu_cycles + other.cpu_cycles,
            memory_bytes=self.memory_bytes + other.memory_bytes,
            storage_bytes=self.storage_bytes + other.storage_bytes,
            network_bytes=self.network_bytes + other.network_bytes,
            gpu_seconds=self.gpu_seconds + other.gpu_seconds
        )

    def __sub__(self, other):
        """Subtract quotas"""
        return ResourceQuota(
            cpu_cycles=self.cpu_cycles - other.cpu_cycles,
            memory_bytes=self.memory_bytes - other.memory_bytes,
            storage_bytes=self.storage_bytes - other.storage_bytes,
            network_bytes=self.network_bytes - other.network_bytes,
            gpu_seconds=self.gpu_seconds - other.gpu_seconds
        )

    def exceeds(self, limit: 'ResourceQuota') -> Tuple[bool, List[str]]:
        """Check if this quota exceeds a limit"""
        violations = []
        if self.cpu_cycles > limit.cpu_cycles:
            violations.append(f"CPU: {self.cpu_cycles} > {limit.cpu_cycles}")
        if self.memory_bytes > limit.memory_bytes:
            violations.append(f"Memory: {self.memory_bytes} > {limit.memory_bytes}")
        if self.storage_bytes > limit.storage_bytes:
            violations.append(f"Storage: {self.storage_bytes} > {limit.storage_bytes}")
        if self.network_bytes > limit.network_bytes:
            violations.append(f"Network: {self.network_bytes} > {limit.network_bytes}")
        if self.gpu_seconds > limit.gpu_seconds:
            violations.append(f"GPU: {self.gpu_seconds} > {limit.gpu_seconds}")
        return len(violations) > 0, violations

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "cpu_cycles": self.cpu_cycles,
            "memory_bytes": self.memory_bytes,
            "storage_bytes": self.storage_bytes,
            "network_bytes": self.network_bytes,
            "gpu_seconds": self.gpu_seconds
        }


@dataclass
class ConversionRates:
    """ATP to resource conversion rates"""
    # How much of each resource does 1 ATP buy?
    atp_to_cpu_cycles: int = 1_000_000  # 1M cycles per ATP
    atp_to_memory_bytes: int = 100_000_000  # 100MB per ATP
    atp_to_storage_bytes: int = 1_000_000_000  # 1GB per ATP
    atp_to_network_bytes: int = 10_000_000  # 10MB per ATP
    atp_to_gpu_seconds: float = 0.1  # 0.1 GPU-seconds per ATP

    # Inverse: How much ATP does each unit of resource cost?
    def cpu_to_atp(self, cycles: int) -> int:
        """Convert CPU cycles to ATP cost"""
        return math.ceil(cycles / self.atp_to_cpu_cycles)

    def memory_to_atp(self, bytes_amt: int) -> int:
        """Convert memory bytes to ATP cost"""
        return math.ceil(bytes_amt / self.atp_to_memory_bytes)

    def storage_to_atp(self, bytes_amt: int) -> int:
        """Convert storage bytes to ATP cost"""
        return math.ceil(bytes_amt / self.atp_to_storage_bytes)

    def network_to_atp(self, bytes_amt: int) -> int:
        """Convert network bytes to ATP cost"""
        return math.ceil(bytes_amt / self.atp_to_network_bytes)

    def gpu_to_atp(self, seconds: float) -> int:
        """Convert GPU seconds to ATP cost"""
        return math.ceil(seconds / self.atp_to_gpu_seconds)

    def quota_to_atp(self, quota: ResourceQuota) -> int:
        """Convert full quota to ATP cost"""
        return (
            self.cpu_to_atp(quota.cpu_cycles) +
            self.memory_to_atp(quota.memory_bytes) +
            self.storage_to_atp(quota.storage_bytes) +
            self.network_to_atp(quota.network_bytes) +
            self.gpu_to_atp(quota.gpu_seconds)
        )

    def atp_to_quota(self, atp: int) -> ResourceQuota:
        """Convert ATP to resource quota (equal split)"""
        # Divide ATP equally among resource types
        atp_per_type = atp // 5
        return ResourceQuota(
            cpu_cycles=atp_per_type * self.atp_to_cpu_cycles,
            memory_bytes=atp_per_type * self.atp_to_memory_bytes,
            storage_bytes=atp_per_type * self.atp_to_storage_bytes,
            network_bytes=atp_per_type * self.atp_to_network_bytes,
            gpu_seconds=int(atp_per_type * self.atp_to_gpu_seconds)
        )


@dataclass
class ResourceAllocation:
    """Active resource allocation for an entity"""
    allocation_id: str
    entity_lct: str
    atp_budget: int
    atp_consumed: int = 0
    quota_limit: ResourceQuota = field(default_factory=ResourceQuota)
    quota_consumed: ResourceQuota = field(default_factory=ResourceQuota)
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    metering_records: List[Dict] = field(default_factory=list)

    def is_valid(self) -> bool:
        """Check if allocation is still valid"""
        if self.expires_at and time.time() > self.expires_at:
            return False
        return self.atp_consumed < self.atp_budget

    def remaining_atp(self) -> int:
        """Get remaining ATP budget"""
        return self.atp_budget - self.atp_consumed

    def remaining_quota(self) -> ResourceQuota:
        """Get remaining resource quota"""
        return self.quota_limit - self.quota_consumed

    def can_allocate(self, requested: ResourceQuota, rates: ConversionRates) -> Tuple[bool, str]:
        """Check if requested resources can be allocated"""
        # Check quota limits
        would_consume = self.quota_consumed + requested
        exceeds, violations = would_consume.exceeds(self.quota_limit)
        if exceeds:
            return False, f"Quota exceeded: {', '.join(violations)}"

        # Check ATP budget
        atp_cost = rates.quota_to_atp(requested)
        if self.atp_consumed + atp_cost > self.atp_budget:
            return False, f"ATP budget exceeded: {self.atp_consumed + atp_cost} > {self.atp_budget}"

        return True, ""

    def consume(self, quota: ResourceQuota, atp_cost: int):
        """Consume resources and ATP"""
        self.quota_consumed = self.quota_consumed + quota
        self.atp_consumed += atp_cost

        # Record metering
        self.metering_records.append({
            "timestamp": time.time(),
            "quota": quota.to_dict(),
            "atp_cost": atp_cost,
            "quota_remaining": self.remaining_quota().to_dict(),
            "atp_remaining": self.remaining_atp()
        })

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "allocation_id": self.allocation_id,
            "entity_lct": self.entity_lct,
            "atp_budget": self.atp_budget,
            "atp_consumed": self.atp_consumed,
            "atp_remaining": self.remaining_atp(),
            "quota_limit": self.quota_limit.to_dict(),
            "quota_consumed": self.quota_consumed.to_dict(),
            "quota_remaining": self.remaining_quota().to_dict(),
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "is_valid": self.is_valid(),
            "metering_records_count": len(self.metering_records)
        }


class ResourcePool:
    """
    Society-level resource pool

    Resources belong to society, not individuals. Entities draw from pool
    based on ATP budget and reputation.
    """

    def __init__(self, pool_id: str, total_quota: ResourceQuota):
        self.pool_id = pool_id
        self.total_quota = total_quota
        self.available_quota = total_quota
        self.allocated_quota = ResourceQuota()
        self.allocations: Dict[str, ResourceAllocation] = {}

    def can_allocate(self, requested: ResourceQuota) -> Tuple[bool, str]:
        """Check if pool has resources available"""
        would_allocate = self.allocated_quota + requested
        exceeds, violations = would_allocate.exceeds(self.total_quota)
        if exceeds:
            return False, f"Pool exhausted: {', '.join(violations)}"
        return True, ""

    def reserve(self, allocation: ResourceAllocation) -> bool:
        """Reserve resources from pool"""
        can_allocate, reason = self.can_allocate(allocation.quota_limit)
        if not can_allocate:
            return False

        self.allocations[allocation.allocation_id] = allocation
        self.allocated_quota = self.allocated_quota + allocation.quota_limit
        self.available_quota = self.total_quota - self.allocated_quota
        return True

    def release(self, allocation_id: str) -> bool:
        """Release resources back to pool"""
        if allocation_id not in self.allocations:
            return False

        allocation = self.allocations[allocation_id]
        self.allocated_quota = self.allocated_quota - allocation.quota_limit
        self.available_quota = self.total_quota - self.allocated_quota
        del self.allocations[allocation_id]
        return True

    def get_stats(self) -> Dict:
        """Get pool statistics"""
        return {
            "pool_id": self.pool_id,
            "total_quota": self.total_quota.to_dict(),
            "available_quota": self.available_quota.to_dict(),
            "allocated_quota": self.allocated_quota.to_dict(),
            "active_allocations": len(self.allocations),
            "utilization": {
                "cpu": (self.allocated_quota.cpu_cycles / self.total_quota.cpu_cycles * 100) if self.total_quota.cpu_cycles > 0 else 0,
                "memory": (self.allocated_quota.memory_bytes / self.total_quota.memory_bytes * 100) if self.total_quota.memory_bytes > 0 else 0,
                "storage": (self.allocated_quota.storage_bytes / self.total_quota.storage_bytes * 100) if self.total_quota.storage_bytes > 0 else 0,
                "network": (self.allocated_quota.network_bytes / self.total_quota.network_bytes * 100) if self.total_quota.network_bytes > 0 else 0,
                "gpu": (self.allocated_quota.gpu_seconds / self.total_quota.gpu_seconds * 100) if self.total_quota.gpu_seconds > 0 else 0,
            }
        }


class ResourceAllocator:
    """
    Web4 Resource Allocation Engine

    Maps ATP tokens to actual compute resources, enforces quotas,
    meters consumption, and prevents resource exhaustion.
    """

    def __init__(self, society_id: str):
        self.society_id = society_id
        self.rates = ConversionRates()
        self.pools: Dict[str, ResourcePool] = {}
        self.allocations: Dict[str, ResourceAllocation] = {}
        self.allocation_counter = 0

    def create_pool(self, pool_id: str, total_quota: ResourceQuota) -> ResourcePool:
        """Create a new resource pool"""
        pool = ResourcePool(pool_id, total_quota)
        self.pools[pool_id] = pool
        return pool

    def create_allocation(
        self,
        entity_lct: str,
        atp_budget: int,
        pool_id: str = "default",
        duration_seconds: Optional[int] = None
    ) -> Tuple[Optional[ResourceAllocation], str]:
        """
        Create resource allocation from ATP budget

        Process:
        1. Convert ATP to resource quota
        2. Check pool availability
        3. Reserve from pool
        4. Create allocation record
        5. Return allocation ID
        """

        # Get pool
        if pool_id not in self.pools:
            return None, f"Pool {pool_id} not found"

        pool = self.pools[pool_id]

        # Convert ATP to quota
        quota = self.rates.atp_to_quota(atp_budget)

        # Create allocation
        self.allocation_counter += 1
        allocation_id = f"alloc:{self.society_id}:{self.allocation_counter}"

        expires_at = None
        if duration_seconds:
            expires_at = time.time() + duration_seconds

        allocation = ResourceAllocation(
            allocation_id=allocation_id,
            entity_lct=entity_lct,
            atp_budget=atp_budget,
            quota_limit=quota,
            expires_at=expires_at
        )

        # Reserve from pool
        if not pool.reserve(allocation):
            return None, "Pool resources exhausted"

        self.allocations[allocation_id] = allocation
        return allocation, ""

    def consume_resources(
        self,
        allocation_id: str,
        resources: ResourceQuota
    ) -> Tuple[bool, str]:
        """
        Consume resources from allocation

        Process:
        1. Verify allocation exists and is valid
        2. Check if consumption would exceed limits
        3. Calculate ATP cost
        4. Update consumption records
        5. Meter for accounting
        """

        if allocation_id not in self.allocations:
            return False, "Allocation not found"

        allocation = self.allocations[allocation_id]

        if not allocation.is_valid():
            return False, "Allocation expired or budget exhausted"

        # Check if can allocate
        can_allocate, reason = allocation.can_allocate(resources, self.rates)
        if not can_allocate:
            return False, reason

        # Calculate ATP cost
        atp_cost = self.rates.quota_to_atp(resources)

        # Consume
        allocation.consume(resources, atp_cost)

        return True, f"Consumed {atp_cost} ATP"

    def release_allocation(self, allocation_id: str) -> bool:
        """Release allocation and return resources to pool"""
        if allocation_id not in self.allocations:
            return False

        allocation = self.allocations[allocation_id]

        # Find which pool this came from
        for pool in self.pools.values():
            if allocation_id in pool.allocations:
                pool.release(allocation_id)
                break

        del self.allocations[allocation_id]
        return True

    def get_allocation(self, allocation_id: str) -> Optional[ResourceAllocation]:
        """Get allocation by ID"""
        return self.allocations.get(allocation_id)

    def get_entity_allocations(self, entity_lct: str) -> List[ResourceAllocation]:
        """Get all allocations for an entity"""
        return [a for a in self.allocations.values() if a.entity_lct == entity_lct]

    def get_stats(self) -> Dict:
        """Get allocator statistics"""
        return {
            "society_id": self.society_id,
            "pools": {pid: pool.get_stats() for pid, pool in self.pools.items()},
            "total_allocations": len(self.allocations),
            "active_allocations": sum(1 for a in self.allocations.values() if a.is_valid()),
            "expired_allocations": sum(1 for a in self.allocations.values() if not a.is_valid())
        }


# Example usage
if __name__ == "__main__":
    import json

    print("="*70)
    print("  Web4 Resource Allocator - Demonstration")
    print("="*70)

    # Create allocator
    allocator = ResourceAllocator("society:research_lab")

    # Create resource pool (society-owned)
    total_quota = ResourceQuota(
        cpu_cycles=1_000_000_000_000,  # 1 trillion cycles
        memory_bytes=100_000_000_000,  # 100GB
        storage_bytes=1_000_000_000_000,  # 1TB
        network_bytes=100_000_000_000,  # 100GB
        gpu_seconds=1000  # 1000 GPU-seconds
    )

    pool = allocator.create_pool("default", total_quota)
    print(f"\n✅ Created resource pool with:")
    print(f"   CPU: {total_quota.cpu_cycles:,} cycles")
    print(f"   Memory: {total_quota.memory_bytes:,} bytes")
    print(f"   Storage: {total_quota.storage_bytes:,} bytes")
    print(f"   Network: {total_quota.network_bytes:,} bytes")
    print(f"   GPU: {total_quota.gpu_seconds} seconds")

    # Create allocation from ATP budget
    entity_lct = "lct:ai:researcher"
    atp_budget = 100

    allocation, error = allocator.create_allocation(
        entity_lct=entity_lct,
        atp_budget=atp_budget,
        pool_id="default",
        duration_seconds=3600  # 1 hour
    )

    if allocation:
        print(f"\n✅ Created allocation for {entity_lct}")
        print(f"   ATP Budget: {atp_budget}")
        print(f"   Allocation ID: {allocation.allocation_id}")
        print(f"   Quota Limit:")
        print(json.dumps(allocation.quota_limit.to_dict(), indent=4))
    else:
        print(f"\n❌ Failed to create allocation: {error}")
        exit(1)

    # Consume resources
    print(f"\n📊 Simulating resource consumption...")

    consumptions = [
        ResourceQuota(cpu_cycles=10_000_000, memory_bytes=1_000_000, network_bytes=100_000),
        ResourceQuota(cpu_cycles=5_000_000, storage_bytes=10_000_000),
        ResourceQuota(gpu_seconds=1, network_bytes=500_000),
    ]

    for i, consumption in enumerate(consumptions, 1):
        success, msg = allocator.consume_resources(allocation.allocation_id, consumption)
        print(f"\n   Consumption {i}: {'✅' if success else '❌'} {msg}")
        if success:
            print(f"   ATP Remaining: {allocation.remaining_atp()}")

    # Get final stats
    print(f"\n" + "="*70)
    print("Final Statistics")
    print("="*70)
    print(json.dumps(allocator.get_stats(), indent=2))

    print(f"\n" + "="*70)
    print("Allocation Details")
    print("="*70)
    print(json.dumps(allocation.to_dict(), indent=2))
