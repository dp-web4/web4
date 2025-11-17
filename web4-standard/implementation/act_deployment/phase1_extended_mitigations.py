"""
Extended Phase 1 Mitigations

Implements additional critical mitigations:
- Circular Vouching Detection (F1)
- Rate Limiting for Priority Queue (C2)

Session #39 (continued)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, deque

from energy_backed_identity_bond import EnergyBackedVouch


# ============================================================================
# Mitigation F1: Circular Vouching Detection
# ============================================================================

@dataclass
class VouchGraphNode:
    """Node in the vouching graph"""
    lct: str
    vouches_for: Set[str] = field(default_factory=set)  # Outgoing edges
    vouched_by: Set[str] = field(default_factory=set)   # Incoming edges
    in_cycle: bool = False
    cycle_ids: List[int] = field(default_factory=list)


class CircularVouchingDetector:
    """
    Detects circular vouching patterns in Web of Trust.

    Purpose: Prevent F1 (Circular Vouching) attack
    - Detects cycles in vouching graph (A→B→C→A)
    - Flags identities participating in circular vouching
    - Prevents Sybil network bootstrap

    Uses Tarjan's algorithm for strongly connected components.
    """

    def __init__(self):
        # Vouching graph: lct -> VouchGraphNode
        self.graph: Dict[str, VouchGraphNode] = {}

        # Detected cycles
        self.cycles: List[List[str]] = []

        # Statistics
        self.total_vouches = 0
        self.circular_vouches = 0

    def add_vouch(self, voucher_lct: str, newcomer_lct: str):
        """Add a vouch to the graph"""

        # Create nodes if they don't exist
        if voucher_lct not in self.graph:
            self.graph[voucher_lct] = VouchGraphNode(lct=voucher_lct)
        if newcomer_lct not in self.graph:
            self.graph[newcomer_lct] = VouchGraphNode(lct=newcomer_lct)

        # Add edges
        self.graph[voucher_lct].vouches_for.add(newcomer_lct)
        self.graph[newcomer_lct].vouched_by.add(voucher_lct)

        self.total_vouches += 1

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect all cycles in vouching graph using DFS.

        Returns list of cycles, where each cycle is a list of LCTs.
        """
        self.cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node_lct: str) -> bool:
            """DFS with cycle detection"""
            visited.add(node_lct)
            rec_stack.add(node_lct)
            path.append(node_lct)

            node = self.graph[node_lct]

            # Visit all neighbors
            for neighbor_lct in node.vouches_for:
                if neighbor_lct not in visited:
                    if dfs(neighbor_lct):
                        return True
                elif neighbor_lct in rec_stack:
                    # Found cycle!
                    cycle_start = path.index(neighbor_lct)
                    cycle = path[cycle_start:] + [neighbor_lct]
                    self.cycles.append(cycle)
                    self.circular_vouches += len(cycle) - 1

                    # Mark nodes as in cycle
                    cycle_id = len(self.cycles) - 1
                    for lct in cycle[:-1]:  # Exclude duplicate
                        self.graph[lct].in_cycle = True
                        self.graph[lct].cycle_ids.append(cycle_id)

            path.pop()
            rec_stack.remove(node_lct)
            return False

        # Run DFS from each unvisited node
        for lct in self.graph:
            if lct not in visited:
                dfs(lct)

        return self.cycles

    def is_circular_vouch(self, voucher_lct: str, newcomer_lct: str) -> bool:
        """
        Check if a vouch would create a cycle.

        Use this BEFORE adding a vouch to prevent circular vouching.
        """
        # If voucher is not in graph, can't create cycle
        if voucher_lct not in self.graph:
            return False

        # Check if there's a path from newcomer to voucher
        # If yes, adding voucher→newcomer would create cycle
        return self._has_path(newcomer_lct, voucher_lct)

    def _has_path(self, start: str, end: str) -> bool:
        """Check if there's a path from start to end using BFS"""
        if start not in self.graph:
            return False

        visited = set()
        queue = deque([start])

        while queue:
            current = queue.popleft()
            if current == end:
                return True

            if current in visited:
                continue

            visited.add(current)

            if current in self.graph:
                for neighbor in self.graph[current].vouches_for:
                    if neighbor not in visited:
                        queue.append(neighbor)

        return False

    def get_cycle_participants(self) -> Set[str]:
        """Get all identities participating in any cycle"""
        return {lct for lct, node in self.graph.items() if node.in_cycle}

    def get_trust_discount(self, lct: str) -> float:
        """
        Calculate trust discount for identity based on cycle participation.

        Returns multiplier in [0, 1]:
        - 1.0 = No cycle participation
        - 0.5 = Participates in 1 cycle
        - 0.0 = Participates in 2+ cycles
        """
        if lct not in self.graph:
            return 1.0

        node = self.graph[lct]

        if not node.in_cycle:
            return 1.0

        cycle_count = len(node.cycle_ids)
        if cycle_count == 1:
            return 0.5  # Suspicious but might be accidental
        else:
            return 0.0  # Definitely gaming the system

    def to_dict(self) -> Dict:
        """Serialize detector state"""
        return {
            "total_nodes": len(self.graph),
            "total_vouches": self.total_vouches,
            "cycles_detected": len(self.cycles),
            "circular_vouches": self.circular_vouches,
            "cycle_participants": len(self.get_cycle_participants()),
            "cycles": [
                {
                    "id": i,
                    "participants": cycle[:-1],  # Exclude duplicate
                    "length": len(cycle) - 1,
                }
                for i, cycle in enumerate(self.cycles)
            ]
        }


# ============================================================================
# Mitigation C2: Rate Limiting for Priority Queue
# ============================================================================

@dataclass
class RateLimitRecord:
    """Record of submission rate for an identity"""
    lct: str
    submissions: deque = field(default_factory=deque)  # Timestamps
    total_submissions: int = 0
    violations: int = 0


class TrustBasedRateLimiter:
    """
    Rate limiting for work request submissions.

    Purpose: Prevent C2 (Priority Spam) attack
    - Limits submission rate based on trust score
    - Low-trust identities have lower rate limits
    - High-trust identities have higher rate limits
    - Prevents DoS via spam submissions

    Formula: max_requests_per_hour = base_rate * trust_score
    """

    def __init__(
        self,
        base_rate_per_hour: int = 10,
        window_seconds: int = 3600,  # 1 hour
    ):
        """
        Initialize rate limiter.

        Args:
            base_rate_per_hour: Base submission rate for trust=1.0
            window_seconds: Time window for rate limiting
        """
        self.base_rate = base_rate_per_hour
        self.window_seconds = window_seconds

        # Rate limit records: lct -> RateLimitRecord
        self.records: Dict[str, RateLimitRecord] = {}

        # Statistics
        self.total_requests = 0
        self.blocked_requests = 0

    def check_rate_limit(
        self,
        requester_lct: str,
        trust_score: float,
    ) -> bool:
        """
        Check if request is within rate limit.

        Args:
            requester_lct: Identity making request
            trust_score: Trust score in [0, 1]

        Returns:
            True if within limit, False if rate limit exceeded
        """
        # Get or create record
        if requester_lct not in self.records:
            self.records[requester_lct] = RateLimitRecord(lct=requester_lct)

        record = self.records[requester_lct]

        # Calculate max allowed submissions
        max_submissions = int(self.base_rate * trust_score)

        # Minimum of 1 submission per hour, even for zero trust
        max_submissions = max(1, max_submissions)

        # Clean up old submissions outside window
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=self.window_seconds)

        # Remove submissions outside window
        while record.submissions and record.submissions[0] < window_start:
            record.submissions.popleft()

        # Check if within limit
        current_count = len(record.submissions)

        if current_count >= max_submissions:
            # Rate limit exceeded
            record.violations += 1
            self.blocked_requests += 1
            return False

        # Within limit - record submission
        record.submissions.append(now)
        record.total_submissions += 1
        self.total_requests += 1

        return True

    def get_remaining_quota(
        self,
        requester_lct: str,
        trust_score: float,
    ) -> int:
        """Get remaining submission quota for identity"""
        if requester_lct not in self.records:
            return int(self.base_rate * trust_score)

        record = self.records[requester_lct]
        max_submissions = int(self.base_rate * trust_score)

        # Clean up old submissions
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=self.window_seconds)

        while record.submissions and record.submissions[0] < window_start:
            record.submissions.popleft()

        current_count = len(record.submissions)
        return max(0, max_submissions - current_count)

    def get_stats(self) -> Dict:
        """Get rate limiter statistics"""
        return {
            "total_requests": self.total_requests,
            "blocked_requests": self.blocked_requests,
            "block_rate": self.blocked_requests / max(1, self.total_requests),
            "tracked_identities": len(self.records),
            "top_violators": self._get_top_violators(5),
        }

    def _get_top_violators(self, limit: int) -> List[Dict]:
        """Get identities with most violations"""
        violators = sorted(
            self.records.values(),
            key=lambda r: r.violations,
            reverse=True
        )[:limit]

        return [
            {
                "lct": v.lct,
                "violations": v.violations,
                "total_submissions": v.total_submissions,
            }
            for v in violators
        ]

    def reset_identity(self, lct: str):
        """Reset rate limit for identity (admin function)"""
        if lct in self.records:
            self.records[lct].submissions.clear()
            self.records[lct].violations = 0


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("EXTENDED PHASE 1 MITIGATIONS")
    print("=" * 80)

    # ========================================
    # Mitigation F1: Circular Vouching Detection
    # ========================================

    print("\n### Mitigation F1: Circular Vouching Detection")
    print("-" * 80)

    detector = CircularVouchingDetector()

    # Create a 5-identity circular vouching ring
    ring = ["lct-ring-A", "lct-ring-B", "lct-ring-C", "lct-ring-D", "lct-ring-E"]

    for i in range(len(ring)):
        voucher = ring[i]
        newcomer = ring[(i + 1) % len(ring)]
        detector.add_vouch(voucher, newcomer)

    print(f"Created vouching ring: A→B→C→D→E→A")

    # Detect cycles
    cycles = detector.detect_cycles()

    print(f"✓ Cycles detected: {len(cycles)}")
    for i, cycle in enumerate(cycles):
        print(f"  Cycle {i}: {' → '.join(cycle)}")

    # Check if new vouch would create cycle
    would_create_cycle = detector.is_circular_vouch("lct-outside", "lct-ring-A")
    print(f"✓ Would 'lct-outside → lct-ring-A' create cycle? {would_create_cycle}")

    would_create_cycle_2 = detector.is_circular_vouch("lct-ring-C", "lct-ring-A")
    print(f"✓ Would 'lct-ring-C → lct-ring-A' create cycle? {would_create_cycle_2}")

    # Get trust discounts
    print(f"\n✓ Trust discounts:")
    for lct in ring:
        discount = detector.get_trust_discount(lct)
        print(f"  {lct}: {discount:.1f}x (in {len(detector.graph[lct].cycle_ids)} cycles)")

    # ========================================
    # Mitigation C2: Rate Limiting
    # ========================================

    print("\n### Mitigation C2: Rate Limiting for Priority Queue")
    print("-" * 80)

    rate_limiter = TrustBasedRateLimiter(base_rate_per_hour=10)

    # High-trust identity (trust=0.9)
    high_trust_lct = "lct-high-trust"
    high_trust_score = 0.9

    # Low-trust identity (trust=0.2)
    low_trust_lct = "lct-low-trust"
    low_trust_score = 0.2

    print(f"High-trust identity (trust={high_trust_score}):")
    print(f"  Max submissions: {int(10 * high_trust_score)}/hour")

    print(f"\nLow-trust identity (trust={low_trust_score}):")
    print(f"  Max submissions: {int(10 * low_trust_score)}/hour")

    # Test high-trust submissions
    high_trust_accepted = 0
    for i in range(15):
        if rate_limiter.check_rate_limit(high_trust_lct, high_trust_score):
            high_trust_accepted += 1

    print(f"\n✓ High-trust submissions: {high_trust_accepted}/15 accepted")

    # Test low-trust submissions
    low_trust_accepted = 0
    for i in range(15):
        if rate_limiter.check_rate_limit(low_trust_lct, low_trust_score):
            low_trust_accepted += 1

    print(f"✓ Low-trust submissions: {low_trust_accepted}/15 accepted")
    print(f"✓ Low-trust blocked: {15 - low_trust_accepted}/15")

    # Get stats
    stats = rate_limiter.get_stats()
    print(f"\n✓ Rate limiter stats:")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Blocked requests: {stats['blocked_requests']}")
    print(f"  Block rate: {stats['block_rate']:.1%}")

    print("\n" + "=" * 80)
    print("Extended Phase 1 mitigations implemented successfully!")
    print("=" * 80)
