"""
Salience-Driven Resource Allocation for Web4
============================================

Applies Thor's salience distribution insights to Web4 ATP resource allocation.

Thor's Discovery (Session 7, 2025-12-07):
- Attention rate ceiling caused by salience distribution, not architecture
- r=0.907 correlation between mean salience and attention
- High-salience environment (0.5-1.0): 31% attention vs baseline 23%
- Architecture scales with input quality

Application to Web4:
- Current ATP allocation: Fixed costs per action type
- Problem: Treats all requests equally regardless of importance
- Solution: Salience-weighted ATP allocation prioritizes high-value actions

Key Insight: Just as consciousness attention scales with salience,
Web4 resource allocation should scale with request importance/urgency.

Author: Legion Autonomous Web4 Research
Date: 2025-12-07
Track: 30 (Salience-Driven Resource Allocation)
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
import random
import statistics


class RequestPriority(Enum):
    """Request priority levels (analog to SAGE salience)"""
    CRITICAL = "CRITICAL"       # 0.8-1.0 salience
    HIGH = "HIGH"               # 0.6-0.8 salience
    MEDIUM = "MEDIUM"           # 0.4-0.6 salience
    LOW = "LOW"                 # 0.2-0.4 salience
    BACKGROUND = "BACKGROUND"   # 0.0-0.2 salience


@dataclass
class ResourceRequest:
    """Request for ATP resources"""
    request_id: str
    action: str
    base_cost: float            # Base ATP cost
    salience: float             # 0-1 importance/urgency
    priority: RequestPriority
    timestamp: float
    requester_id: str


@dataclass
class AllocationResult:
    """Result of resource allocation"""
    request: ResourceRequest
    allocated_atp: float        # ATP actually allocated
    allocation_ratio: float     # allocated / requested
    queue_position: int         # Position in allocation queue
    allocation_time_ms: float   # Time to make decision


class SalienceDistributionAnalyzer:
    """
    Analyze salience distribution of incoming requests

    Thor's finding: Mean salience predicts attention (r=0.907)
    Applied here: Mean salience predicts resource availability
    """

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.recent_saliences: List[float] = []

    def add_request(self, salience: float) -> None:
        """Track request salience"""
        self.recent_saliences.append(salience)
        if len(self.recent_saliences) > self.window_size:
            self.recent_saliences.pop(0)

    def get_statistics(self) -> Dict[str, float]:
        """Calculate salience distribution statistics"""
        if not self.recent_saliences:
            return {
                'mean': 0.5,
                'median': 0.5,
                'std': 0.0,
                'min': 0.0,
                'max': 1.0,
                'p25': 0.25,
                'p75': 0.75
            }

        sorted_sal = sorted(self.recent_saliences)
        n = len(sorted_sal)

        return {
            'mean': statistics.mean(self.recent_saliences),
            'median': statistics.median(self.recent_saliences),
            'std': statistics.stdev(self.recent_saliences) if n > 1 else 0.0,
            'min': min(self.recent_saliences),
            'max': max(self.recent_saliences),
            'p25': sorted_sal[n // 4],
            'p75': sorted_sal[3 * n // 4]
        }

    def classify_environment(self) -> str:
        """
        Classify current salience environment

        Based on Thor's distributions:
        - High Priority: [0.5, 1.0], mean=0.75, attention=31%
        - Baseline: [0.2, 0.6], mean=0.40, attention=23%
        - Low Priority: [0.1, 0.5], mean=0.30, attention=15%
        """
        stats = self.get_statistics()
        mean_sal = stats['mean']

        if mean_sal >= 0.65:
            return "HIGH_SALIENCE"  # Like Thor's High Priority
        elif mean_sal >= 0.45:
            return "MEDIUM_SALIENCE"  # Like Thor's Baseline
        elif mean_sal >= 0.30:
            return "LOW_SALIENCE"
        else:
            return "VERY_LOW_SALIENCE"


class SalienceResourceAllocator:
    """
    ATP resource allocator with salience-based prioritization

    Inspired by Thor's attention allocation based on salience thresholds
    """

    def __init__(self, total_atp_budget: float = 1000.0):
        self.total_atp_budget = total_atp_budget
        self.available_atp = total_atp_budget
        self.analyzer = SalienceDistributionAnalyzer()
        self.allocated_requests: List[AllocationResult] = []

    def calculate_salience_multiplier(self, salience: float, environment: str) -> float:
        """
        Calculate ATP allocation multiplier based on salience

        Analog to Thor's attention decision:
        - High salience → more likely to attend → higher ATP allocation
        - Low salience → less likely to attend → lower ATP allocation

        Environment adaptation:
        - High-salience environment: Be more selective (raise bar)
        - Low-salience environment: Be less selective (lower bar)
        """

        # Environment-adaptive thresholds (like Thor's WAKE/FOCUS thresholds)
        if environment == "HIGH_SALIENCE":
            # In rich environment, only allocate to truly high-salience requests
            if salience >= 0.75:
                return 1.5  # Bonus for exceptional requests
            elif salience >= 0.60:
                return 1.0  # Full allocation
            elif salience >= 0.45:
                return 0.7  # Reduced allocation
            else:
                return 0.3  # Minimal allocation

        elif environment == "MEDIUM_SALIENCE":
            # Baseline (like Thor's v1.0.0 thresholds)
            if salience >= 0.60:
                return 1.2
            elif salience >= 0.45:
                return 1.0
            elif salience >= 0.30:
                return 0.6
            else:
                return 0.3

        elif environment == "LOW_SALIENCE":
            # In sparse environment, allocate more generously
            if salience >= 0.45:
                return 1.2
            elif salience >= 0.30:
                return 1.0
            elif salience >= 0.20:
                return 0.7
            else:
                return 0.4

        else:  # VERY_LOW_SALIENCE
            # Maximum generosity to not starve system
            if salience >= 0.30:
                return 1.2
            elif salience >= 0.20:
                return 1.0
            else:
                return 0.6

    def allocate_request(self, request: ResourceRequest) -> AllocationResult:
        """
        Allocate ATP resources to request based on salience

        Thor's principle: Higher salience → more attention
        Web4 application: Higher salience → more ATP
        """
        import time
        start_time = time.perf_counter()

        # Track salience for environment classification
        self.analyzer.add_request(request.salience)
        environment = self.analyzer.classify_environment()

        # Calculate salience-based multiplier
        multiplier = self.calculate_salience_multiplier(request.salience, environment)

        # Calculate target ATP allocation
        target_atp = request.base_cost * multiplier

        # Check available ATP
        if target_atp <= self.available_atp:
            # Full allocation
            allocated = target_atp
            self.available_atp -= allocated
        else:
            # Partial allocation (give what's available)
            allocated = self.available_atp
            self.available_atp = 0.0

        allocation_ratio = allocated / target_atp if target_atp > 0 else 0.0

        end_time = time.perf_counter()
        allocation_time = (end_time - start_time) * 1000  # ms

        result = AllocationResult(
            request=request,
            allocated_atp=allocated,
            allocation_ratio=allocation_ratio,
            queue_position=len(self.allocated_requests),
            allocation_time_ms=allocation_time
        )

        self.allocated_requests.append(result)
        return result

    def replenish_atp(self, amount: float) -> None:
        """Replenish ATP budget (e.g., from REST state recovery)"""
        self.available_atp = min(
            self.available_atp + amount,
            self.total_atp_budget
        )


def demonstrate_salience_allocation():
    """Demonstrate salience-driven resource allocation"""

    print("=" * 70)
    print("  Track 30: Salience-Driven Resource Allocation")
    print("  Applying Thor's Salience Discovery to Web4 ATP")
    print("=" * 70)

    print("\nThor's Discovery (Session 7):")
    print("  - Attention ceiling at ~17% with uniform[0.2, 0.6] salience")
    print("  - Achieved 31% attention with uniform[0.5, 1.0] salience")
    print("  - r=0.907 correlation: mean salience → attention rate")
    print("  - Conclusion: Architecture scales with input quality")

    print("\nWeb4 Application:")
    print("  - ATP allocation should prioritize high-salience requests")
    print("  - Environment-adaptive thresholds (like SAGE WAKE/FOCUS)")
    print("  - Higher mean salience → more selective allocation")
    print()

    allocator = SalienceResourceAllocator(total_atp_budget=1000.0)

    # Scenario 1: Mixed salience environment (baseline)
    print("=" * 70)
    print("  SCENARIO 1: Mixed Salience Environment (Baseline)")
    print("=" * 70)

    requests_mixed = [
        ResourceRequest("req1", "critical_transaction", 50.0, 0.95, RequestPriority.CRITICAL, 1.0, "agent1"),
        ResourceRequest("req2", "normal_query", 10.0, 0.45, RequestPriority.MEDIUM, 1.1, "agent2"),
        ResourceRequest("req3", "background_sync", 5.0, 0.15, RequestPriority.BACKGROUND, 1.2, "agent3"),
        ResourceRequest("req4", "high_priority_alert", 30.0, 0.85, RequestPriority.HIGH, 1.3, "agent4"),
        ResourceRequest("req5", "routine_update", 8.0, 0.35, RequestPriority.LOW, 1.4, "agent5"),
    ]

    print("\nRequests:")
    for req in requests_mixed:
        print(f"  {req.request_id}: {req.action}")
        print(f"    Base cost: {req.base_cost} ATP, Salience: {req.salience:.2f}, Priority: {req.priority.value}")

    print("\nAllocation Results:")
    for req in requests_mixed:
        result = allocator.allocate_request(req)
        print(f"  {req.request_id}:")
        print(f"    Allocated: {result.allocated_atp:.1f} ATP ({result.allocation_ratio:.1%} of target)")
        print(f"    Environment: {allocator.analyzer.classify_environment()}")

    # Check salience distribution
    stats = allocator.analyzer.get_statistics()
    print(f"\nSalience Distribution:")
    print(f"  Mean: {stats['mean']:.3f}")
    print(f"  Median: {stats['median']:.3f}")
    print(f"  Range: [{stats['min']:.2f}, {stats['max']:.2f}]")
    print(f"  Environment: {allocator.analyzer.classify_environment()}")

    # Scenario 2: High-salience environment
    print("\n" + "=" * 70)
    print("  SCENARIO 2: High-Salience Environment (Crisis Mode)")
    print("=" * 70)

    allocator2 = SalienceResourceAllocator(total_atp_budget=1000.0)

    requests_high = [
        ResourceRequest("req6", "emergency_response", 100.0, 0.98, RequestPriority.CRITICAL, 2.0, "agent1"),
        ResourceRequest("req7", "security_alert", 80.0, 0.92, RequestPriority.CRITICAL, 2.1, "agent2"),
        ResourceRequest("req8", "critical_repair", 60.0, 0.85, RequestPriority.HIGH, 2.2, "agent3"),
        ResourceRequest("req9", "urgent_notification", 40.0, 0.78, RequestPriority.HIGH, 2.3, "agent4"),
        ResourceRequest("req10", "high_priority_task", 30.0, 0.70, RequestPriority.HIGH, 2.4, "agent5"),
    ]

    print("\nRequests (All High Salience):")
    for req in requests_high:
        print(f"  {req.request_id}: salience={req.salience:.2f}, cost={req.base_cost}")

    print("\nAllocation Results:")
    for req in requests_high:
        result = allocator2.allocate_request(req)
        print(f"  {req.request_id}: {result.allocated_atp:.1f} ATP allocated ({result.allocation_ratio:.1%})")

    stats2 = allocator2.analyzer.get_statistics()
    print(f"\nSalience Distribution:")
    print(f"  Mean: {stats2['mean']:.3f} (HIGH - like Thor's High Priority)")
    print(f"  Environment: {allocator2.analyzer.classify_environment()}")

    # Scenario 3: Low-salience environment
    print("\n" + "=" * 70)
    print("  SCENARIO 3: Low-Salience Environment (Routine Operations)")
    print("=" * 70)

    allocator3 = SalienceResourceAllocator(total_atp_budget=1000.0)

    requests_low = [
        ResourceRequest("req11", "background_task1", 15.0, 0.35, RequestPriority.LOW, 3.0, "agent1"),
        ResourceRequest("req12", "maintenance", 20.0, 0.28, RequestPriority.LOW, 3.1, "agent2"),
        ResourceRequest("req13", "routine_check", 10.0, 0.42, RequestPriority.MEDIUM, 3.2, "agent3"),
        ResourceRequest("req14", "log_rotation", 8.0, 0.18, RequestPriority.BACKGROUND, 3.3, "agent4"),
        ResourceRequest("req15", "cache_cleanup", 12.0, 0.25, RequestPriority.LOW, 3.4, "agent5"),
    ]

    print("\nRequests (All Low Salience):")
    for req in requests_low:
        print(f"  {req.request_id}: salience={req.salience:.2f}, cost={req.base_cost}")

    print("\nAllocation Results:")
    for req in requests_low:
        result = allocator3.allocate_request(req)
        print(f"  {req.request_id}: {result.allocated_atp:.1f} ATP allocated ({result.allocation_ratio:.1%})")

    stats3 = allocator3.analyzer.get_statistics()
    print(f"\nSalience Distribution:")
    print(f"  Mean: {stats3['mean']:.3f} (LOW - like Thor's Lower Salience)")
    print(f"  Environment: {allocator3.analyzer.classify_environment()}")

    # Comparative Analysis
    print("\n" + "=" * 70)
    print("  COMPARATIVE ANALYSIS")
    print("=" * 70)

    print("\nEnvironment Adaptation (Like SAGE Threshold Adaptation):")
    print(f"  Mixed (mean={stats['mean']:.2f}): Standard allocation, balanced priorities")
    print(f"  High (mean={stats2['mean']:.2f}): Selective allocation, raise bar for resources")
    print(f"  Low (mean={stats3['mean']:.2f}): Generous allocation, lower bar to avoid starvation")

    print("\nConnection to Thor's Discovery:")
    print("  Thor: Salience distribution determines attention capacity")
    print("  Web4: Salience distribution determines resource allocation strategy")
    print("  Both: Architecture adapts to input quality (not fixed ceiling)")

    print("\nProduction Benefits:")
    print("  1. High-value requests get priority (critical transactions, security)")
    print("  2. Environment-adaptive (handles both crisis and routine gracefully)")
    print("  3. Prevents resource starvation in low-salience periods")
    print("  4. Grounded in SAGE empirical findings (r=0.907 salience-attention)")
    print("  5. Natural analog to consciousness attention allocation")

    print()


if __name__ == "__main__":
    demonstrate_salience_allocation()
